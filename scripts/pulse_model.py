#!/usr/bin/env python3
"""
pulse_model.py - deterministic line origination for the /pulse/ desk (session arena/5fba1c42-olbg2).

Every input comes from data/pulse/inputs.json, which was captured first-hand from official
governing-body sources on 2026-10-22 (URLs recorded per row). This script:
  1. originates win-match, handicap and match-total probabilities per fixture where the
     verified inputs support it,
  2. grades the favourite selection low / medium / high,
  3. writes data/pulse/matches.json and data/pulse/flagged.json.

Rules (uniform, documented):
  * HIGH  = model probability >= 0.70 AND fair American odds inside [-250, +10000]
            (decimal 1.40 - 101.00). -250 is decimal 1.40 = 71.43% implied, so the
            high-confidence band is the sliver 70.00% <= p <= 71.43% for heavy favourites,
            while plus-money selections are high as soon as p >= 0.70.
  * MEDIUM = 0.575 <= p < 0.70, or p >= 0.70 but fair price heavier than -250.
  * LOW    = p < 0.575.
  * Nothing is ever moved into the band by hand; the band is applied after origination.
"""
import json, math, os, itertools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INP = json.load(open(os.path.join(ROOT, "data/pulse/inputs.json")))

# ----------------------------------------------------------------- helpers
def fair_decimal(p):
    return round(1.0 / p, 3) if p > 0 else None

def fair_american(p):
    if p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return int(round(-100.0 * p / (1 - p)))
    return int(round(100.0 * (1 - p) / p))

def in_band(p):
    fa = fair_american(p)
    return fa is not None and -250 <= fa <= 10000

def grade(p):
    if p >= 0.70:
        return "high" if in_band(p) else "medium"
    if p >= 0.575:
        return "medium"
    return "low"

def pois(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

def logit(x):
    return 1.0 / (1.0 + math.exp(-x))

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))

def market(sel, p, note=""):
    return {
        "selection": sel,
        "probability": round(p, 4),
        "fair_decimal": fair_decimal(p),
        "fair_american": fair_american(p),
        "confidence": grade(p),
        "in_band": p >= 0.575 and in_band(p),
        "note": note,
    }

NHL_HOME_EDGE = 1.045      # documented constant: home scoring multiplier
NHL_OT_HOME_SHARE = 0.55   # documented constant: home share of OT/SO wins
EHF_HOME_EDGE = 1.03
DART_SEED_K = 1.15         # rating = seed^-k
TENNIS_SEED_K = 0.55
PROD2_HOME_PTS = 3.5       # documented home edge in points
PROD2_POS_PTS = 1.35       # documented points per table-position step
PROD2_MARGIN_SD = 13.0     # documented rugby margin dispersion

OUT = {"generated_at": INP["captured_at"], "matches": [], "flags": []}
FLAGS = []

def flag(code, item, detail, links, layer="/pulse/"):
    FLAGS.append({"code": code, "item": item, "detail": detail, "links": links, "layer": layer})

# ----------------------------------------------------------------- NHL
def run_nhl():
    d = INP["nhl"]; teams = d["teams"]
    tot_gf = sum(t["gf"] for t in teams.values()); tot_gp = sum(t["gp"] for t in teams.values())
    L = tot_gf / tot_gp
    GRID = range(0, 15)
    for g in d["games"]:
        th, ta = teams[g["home"]], teams[g["away"]]
        gfh, gah = th["gf"]/th["gp"], th["ga"]/th["gp"]
        gfa, gaa = ta["gf"]/ta["gp"], ta["ga"]/ta["gp"]
        lam_h = gfh * gaa / L * NHL_HOME_EDGE
        lam_a = gfa * gah / L / NHL_HOME_EDGE
        ph = [[pois(i, lam_h) * pois(j, lam_a) for j in GRID] for i in GRID]
        p_home_reg = sum(ph[i][j] for i in GRID for j in GRID if i > j)
        p_tie = sum(ph[i][i] for i in GRID)
        p_away_reg = sum(ph[i][j] for i in GRID for j in GRID if i < j)
        p_home = p_home_reg + p_tie * NHL_OT_HOME_SHARE
        p_away = p_away_reg + p_tie * (1 - NHL_OT_HOME_SHARE)
        p_home_by2 = sum(ph[i][j] for i in GRID for j in GRID if i - j >= 2)
        p_away_by2 = sum(ph[i][j] for i in GRID for j in GRID if j - i >= 2)
        p_over = 1 - sum(pois(t, lam_h + lam_a) for t in range(0, 6))
        exp_tot = lam_h + lam_a
        win_markets = [
            market(f"{g['home']} win match (moneyline)", p_home),
            market(f"{g['away']} win match (moneyline)", p_away),
        ]
        cap_markets = [
            market(f"{g['home']} -1.5 (puck line)", p_home_by2),
            market(f"{g['away']} +1.5 (puck line)", 1 - p_home_by2),
            market(f"{g['away']} -1.5 (puck line)", p_away_by2),
            market(f"{g['home']} +1.5 (puck line)", 1 - p_away_by2),
        ]
        tot_markets = [
            market(f"Over 5.5 total goals", p_over),
            market(f"Under 5.5 total goals", 1 - p_over),
        ]
        allm = win_markets + cap_markets + tot_markets
        best = max(allm, key=lambda m: m["probability"])
        # pick = best selection on win market only (brief asks for a match winner)
        win_best = max(win_markets, key=lambda m: m["probability"])
        OUT["matches"].append({
            "id": g["id"], "sport": "ice-hockey", "competition": d["competition"],
            "date": g["start_utc"][:10], "start_utc": g["start_utc"],
            "home": g["home"], "away": g["away"], "venue": g["venue"],
            "home_form": f"{th['w']}-{th['l']}-{th['otl']} ({th['gf']} GF / {th['ga']} GA in {th['gp']} GP)",
            "away_form": f"{ta['w']}-{ta['l']}-{ta['otl']} ({ta['gf']} GF / {ta['ga']} GA in {ta['gp']} GP)",
            "leaders": g["leaders"], "market_context": g["market_context"],
            "expected": {"home_goals": round(lam_h, 2), "away_goals": round(lam_a, 2), "total": round(exp_tot, 2)},
            "winner_market": win_markets, "handicap_market": cap_markets[:2] if lam_h >= lam_a else cap_markets[2:],
            "total_market": tot_markets,
            "pick": win_best, "best_confident_market": best,
            "official_url": g["url"], "official_source": d["source_label"],
            "data_urls": [d["score_url"], d["stats_url"]],
        })
    return L

# ----------------------------------------------------------------- MLB
def run_mlb():
    d = INP["mlb"]; t = d["teams"]
    def strength(x):
        w = t[x]["w"] / (t[x]["w"] + t[x]["l"])
        rs, ra = t[x]["rs"], t[x]["ra"]
        pyth = rs**2 / (rs**2 + ra**2)
        return (w + pyth) / 2
    sb, st = strength("Milwaukee Brewers"), strength("Tampa Bay Rays")
    def log5(a, b):
        return (a - a * b) / (a + b - 2 * a * b)
    for g in d["games"]:
        home, away = g["home"], g["away"]
        sh, sa = (sb, st) if home.startswith("Milwaukee") else (st, sb)
        p = log5(sh, sa)
        if home.startswith("Milwaukee"):
            p = p * 1.13 / (p * 1.13 + (1 - p))   # documented home boost factor 1.13
        win_markets = [market(f"{home} win match (moneyline)", p),
                       market(f"{away} win match (moneyline)", 1 - p)]
        win_best = max(win_markets, key=lambda m: m["probability"])
        th, ta = t[home], t[away]
        OUT["matches"].append({
            "id": g["id"], "sport": "baseball", "competition": g["description"] + " - " + d["competition"],
            "date": g["official_date"], "start_utc": g["start_utc"],
            "home": home, "away": away, "venue": g["venue"],
            "home_form": f"{th['w']}-{th['l']} ({th['rs']} RS / {th['ra']} RA), home {th['home_record']}",
            "away_form": f"{ta['w']}-{ta['l']} ({ta['rs']} RS / {ta['ra']} RA), away {ta['away_record']}",
            "winner_market": win_markets,
            "handicap_market": "not originated - needs verified probable-pitcher data (blank, PU-19)",
            "total_market": "not originated - same reason (blank, PU-19)",
            "pick": win_best, "best_confident_market": win_best if win_best["probability"] >= 0.575 else win_best,
            "official_url": g["url"], "official_source": d["source_label"],
            "data_urls": [d["schedule_url"], d["standings_url_al"], d["standings_url_nl"]],
        })

# ----------------------------------------------------------------- darts
def race(p, n):
    q = 1 - p
    return sum(math.comb(n - 1 + j, j) * p**n * q**j for j in range(n))

def run_darts():
    d = INP["pdc"]
    for m in d["matches"]:
        r1, r2 = m["s1"] ** (-DART_SEED_K), m["s2"] ** (-DART_SEED_K)
        p_leg = r1 / (r1 + r2)
        p_leg = min(max(p_leg, 0.30), 0.70)   # documented cap: seed gaps exaggerate real leg-win edges
        p_match = race(p_leg, 6)
        p_m1 = 1 - p_match
        # handicap: -1.5 legs = win by 2+ legs (6-0..6-4)
        q = 1 - p_leg
        p1_by2 = sum(math.comb(5 + j, j) * p_leg**6 * q**j for j in range(5))
        p_over95 = sum(math.comb(5 + j, j) * (p_leg**6 * q**j + q**6 * p_leg**j) for j in (4, 5))
        win_markets = [market(f"{m['p1']} win match", p_match), market(f"{m['p2']} win match", p_m1)]
        cap = [market(f"{m['p1']} -1.5 legs", p1_by2), market(f"{m['p2']} +1.5 legs", 1 - p1_by2)]
        tot = [market("Over 9.5 total legs", p_over95), market("Under 9.5 total legs", 1 - p_over95)]
        win_best = max(win_markets, key=lambda x: x["probability"])
        best = max(win_markets + cap + tot, key=lambda x: x["probability"])
        OUT["matches"].append({
            "id": m["id"], "sport": "darts", "competition": d["competition"] + " - " + d["format"],
            "date": "2026-10-22", "start_utc": d.get("session_local", ""),
            "home": m["p1"], "away": m["p2"], "venue": "Westfalenhallen, Dortmund",
            "home_form": f"seed ({m['s1']})", "away_form": f"seed ({m['s2']})",
            "seed_model": f"leg-win p({m['p1']}) = {p_leg:.3f} from official ET one-year seeds, k={DART_SEED_K}",
            "winner_market": win_markets, "handicap_market": cap, "total_market": tot,
            "pick": win_best, "best_confident_market": best,
            "official_url": d["preview_url"], "official_source": d["source_label"],
            "data_urls": [d["schedule_url"], d["preview_url"]] + ([m["olbg_url"]] if m.get("olbg_url") else []),
        })

# ----------------------------------------------------------------- EHF
def run_ehf():
    d = INP["ehf"]; st = d["standings"]
    tot_gf = sum(v["gf"] for v in st.values()); tot_gp = sum(v["gp"] for v in st.values())
    L = tot_gf / tot_gp
    GRID = range(0, 75)
    for m in d["matches"]:
        th, ta = st[m["home"]], st[m["away"]]
        gfh, gah = th["gf"]/th["gp"], th["ga"]/th["gp"]
        gfa, gaa = ta["gf"]/ta["gp"], ta["ga"]/ta["gp"]
        lam_h = gfh * gaa / L * EHF_HOME_EDGE
        lam_a = gfa * gah / L / EHF_HOME_EDGE
        ph = [[pois(i, lam_h) * pois(j, lam_a) for j in GRID] for i in GRID]
        p_home_reg = sum(ph[i][j] for i in GRID for j in GRID if i > j)
        p_tie = sum(ph[i][i] for i in GRID)
        p_away_reg = sum(ph[i][j] for i in GRID for j in GRID if i < j)
        h_ph = p_home_reg / (p_home_reg + p_away_reg)     # draw-no-bet normalisation
        margin = lam_h - lam_a
        line = math.floor(abs(margin)) + 0.5
        if lam_h >= lam_a:
            p_cover = sum(ph[i][j] for i in GRID for j in GRID if i - j > line - 1)
            cap = [market(f"{m['home']} -{line} (handicap)", p_cover),
                   market(f"{m['away']} +{line} (handicap)", 1 - p_cover)]
        else:
            p_cover = sum(ph[i][j] for i in GRID for j in GRID if j - i > line - 1)
            cap = [market(f"{m['away']} -{line} (handicap)", p_cover),
                   market(f"{m['home']} +{line} (handicap)", 1 - p_cover)]
        exp_tot = lam_h + lam_a
        tline = math.floor(exp_tot) + 0.5
        p_over = 1 - sum(pois(t, exp_tot) for t in range(0, int(tline) + 1))
        win_markets = [market(f"{m['home']} win match (draw no bet)", h_ph),
                       market(f"{m['away']} win match (draw no bet)", 1 - h_ph)]
        tot = [market(f"Over {tline} total goals", p_over), market(f"Under {tline} total goals", 1 - p_over)]
        win_best = max(win_markets, key=lambda x: x["probability"])
        best = max(win_markets + cap + tot, key=lambda x: x["probability"])
        OUT["matches"].append({
            "id": m["id"], "sport": "handball", "competition": d["competition"],
            "date": m["start_utc"][:10], "start_utc": m["start_utc"],
            "home": m["home"], "away": m["away"], "venue": "home venue per EHF match page",
            "home_form": f"Group {th['grp']}: {th['w']}-{th['d']}-{th['l']} ({th['gf']}:{th['ga']}, {th['pts']} pts in {th['gp']} GP)",
            "away_form": f"Group {ta['grp']}: {ta['w']}-{ta['d']}-{ta['l']} ({ta['gf']}:{ta['ga']}, {ta['pts']} pts in {ta['gp']} GP)",
            "expected": {"home_goals": round(lam_h, 1), "away_goals": round(lam_a, 1), "total": round(exp_tot, 1), "tie_probability": round(p_tie, 3)},
            "winner_market": win_markets, "handicap_market": cap, "total_market": tot,
            "pick": win_best, "best_confident_market": best,
            "official_url": m["url"], "official_source": d["source_label"],
            "data_urls": [d["matches_url"], d["standings_url"]],
        })

# ----------------------------------------------------------------- WST
def run_wst():
    d = INP["wst"]
    def shrink(f):
        return (f[0] + 2) / (f[0] + f[1] + 4)
    for m in d["scheduled"]:
        pa_r, pb_r = shrink(m["f1"]), shrink(m["f2"])
        p_frame = pa_r / (pa_r + pb_r)
        p_match = race(p_frame, 4)
        q = 1 - p_frame
        p1_by2 = sum(math.comb(3 + j, j) * p_frame**4 * q**j for j in range(3))
        p7 = sum(math.comb(3 + j, j) * (p_frame**4 * q**j + q**4 * p_frame**j) for j in (2, 3))
        win_markets = [market(f"{m['p1']} win match", p_match), market(f"{m['p2']} win match", 1 - p_match)]
        cap = [market(f"{m['p1']} -1.5 frames", p1_by2), market(f"{m['p2']} +1.5 frames", 1 - p1_by2)]
        tot = [market("Match goes to 6.5+ frames (over 6.5)", p7), market("Under 6.5 frames", 1 - p7)]
        win_best = max(win_markets, key=lambda x: x["probability"])
        best = max(win_markets + cap + tot, key=lambda x: x["probability"])
        OUT["matches"].append({
            "id": m["id"], "sport": "snooker", "competition": d["competition"] + " - " + d["format"],
            "date": "2026-10-22", "start_utc": "2026-10-22 " + m["time"] + " (session time per WST)",
            "home": m["p1"], "away": m["p2"], "venue": "Belfast (Titanic Exhibition Centre per WST tournament page area)",
            "home_form": f"this event {m['f1'][0]}-{m['f1'][1]} frames ({m['r1']}; {m['r2']})",
            "away_form": f"this event {m['f2'][0]}-{m['f2'][1]} frames ({m['r1b']}; {m['r2b']})",
            "winner_market": win_markets, "handicap_market": cap, "total_market": tot,
            "pick": win_best, "best_confident_market": best,
            "official_url": m["url"], "official_source": d["source_label"],
            "data_urls": [d["tournament_url"]],
        })

# ----------------------------------------------------------------- ATP
def run_atp():
    d = INP["atp"]
    for m in d["upcoming"]:
        r1, r2 = m["s1"] ** (-TENNIS_SEED_K), m["s2"] ** (-TENNIS_SEED_K)
        p_set = r1 / (r1 + r2)
        p_match = p_set**2 * (3 - 2 * p_set)  # race to 2 sets
        win_markets = [market(f"{m['p1']} win match", p_match), market(f"{m['p2']} win match", 1 - p_match)]
        q = 1 - p_set
        p_straight = p_set**2
        tot = [market("Over 2.5 sets", 1 - (p_set**2 + q**2)), market("Under 2.5 sets", p_set**2 + q**2)]
        cap = [market(f"{m['p1']} -1.5 sets", p_straight), market(f"{m['p2']} +1.5 sets", 1 - p_straight)]
        win_best = max(win_markets, key=lambda x: x["probability"])
        best = max(win_markets + cap + tot, key=lambda x: x["probability"])
        OUT["matches"].append({
            "id": m["id"], "sport": "tennis", "competition": d["competition"],
            "date": "2026-10-22", "start_utc": m["slot"],
            "home": m["p1"], "away": m["p2"], "venue": "Almaty Arena, Center Court (per ATP daily schedule)",
            "home_form": m["p1_seed"], "away_form": m["p2_seed"],
            "seed_model": f"set-win p({m['p1']}) = {p_set:.3f} from official draw seeds, k={TENNIS_SEED_K}; PU-14 unseeded proxy",
            "winner_market": win_markets, "handicap_market": cap, "total_market": tot,
            "pick": win_best, "best_confident_market": best,
            "official_url": m["url"], "official_source": d["source_label"],
            "data_urls": [d["schedule_url"], d["current_url"]],
        })

# ----------------------------------------------------------------- Pro D2
def run_prod2():
    d = INP["prod2"]
    for m in d["matches"]:
        mu = PROD2_HOME_PTS + PROD2_POS_PTS * (m["pa"] - m["ph"])
        p_home = norm_cdf(mu / PROD2_MARGIN_SD)
        mu_a = -mu
        line = math.floor(abs(mu)) + 0.5
        if mu >= 0:
            cap = [market(f"{m['home']} -{line} (handicap)", norm_cdf((mu - line) / PROD2_MARGIN_SD)),
                   market(f"{m['away']} +{line} (handicap)", 1 - norm_cdf((mu - line) / PROD2_MARGIN_SD))]
        else:
            cap = [market(f"{m['away']} -{line} (handicap)", norm_cdf((mu_a - line) / PROD2_MARGIN_SD)),
                   market(f"{m['home']} +{line} (handicap)", 1 - norm_cdf((mu_a - line) / PROD2_MARGIN_SD))]
        win_markets = [market(f"{m['home']} win match", p_home), market(f"{m['away']} win match", 1 - p_home)]
        win_best = max(win_markets, key=lambda x: x["probability"])
        best = max(win_markets + cap, key=lambda x: x["probability"])
        OUT["matches"].append({
            "id": m["id"], "sport": "rugby-union", "competition": d["competition"],
            "date": m["start_utc"][:10], "start_utc": m["start_utc"],
            "home": m["home"], "away": m["away"], "venue": f"{m['day']} {m['time_local']} local, per LNR",
            "home_form": f"{m['ph']}e of 16 (official LNR J8 fixture list)", "away_form": f"{m['pa']}e of 16",
            "expected": {"margin_model": f"home margin ~ N({mu:+.1f}, {PROD2_MARGIN_SD})"},
            "winner_market": win_markets, "handicap_market": cap,
            "total_market": "not originated - LNR J8 page lists positions only, no verified points data (blank, PU-20)",
            "pick": win_best, "best_confident_market": best,
            "official_url": m["url"], "official_source": d["source_label"],
            "data_urls": [d["calendar_url"]],
        })

# ----------------------------------------------------------------- F1
def run_f1():
    d = INP["f1"]; tal = d["driver_tally_verified"]
    scores = {k: v["wins"] + 0.5 * v["p2"] + 0.25 * v["p3"] for k, v in tal.items()}
    total_named = sum(scores.values())
    total_pool = 28.0  # 16 races x (1 win + 0.5 P2 + 0.25 P3)
    mkts = []
    for name in sorted(scores, key=scores.get, reverse=True):
        p = scores[name] / total_pool
        mkts.append(market(f"{name} wins the United States GP", p,
                           f"{tal[name]['wins']}W {tal[name]['p2']}xP2 {tal[name]['p3']}xP3 in R1-R16"))
    mkts.append(market("Any other driver wins", (total_pool - total_named) / total_pool,
                       "remainder incl. unverified R7 third place - PU-06"))
    named = sorted(mkts, key=lambda x: -x["probability"])  # all named drivers + remainder
    best = max(mkts, key=lambda x: x["probability"])
    OUT["matches"].append({
        "id": "f1-usgp-2026", "sport": "motor-racing", "competition": d["competition"],
        "date": "2026-10-25", "start_utc": "2026-10-25 (race day; weekend 23-25 Oct)",
        "home": "Field (Austin, COTA)", "away": "-", "venue": "Circuit of The Americas, Austin",
        "home_form": "R18 of the 2026 FIA F1 season; previous round R17 Singapore (09-11 Oct)",
        "winner_market": named, "handicap_market": "n/a (outright market)", "total_market": "n/a",
        "pick": best, "best_confident_market": best,
        "official_url": d["calendar_url"], "official_source": d["source_label"],
        "data_urls": [d["calendar_url"], d["olbg_url"]],
    })

# ----------------------------------------------------------------- blank fixtures (NBA, cricket)
def run_blanks():
    nba = INP["nba"]
    for g in nba["games"]:
        OUT["matches"].append({
            "id": g["id"], "sport": "basketball", "competition": nba["competition"],
            "date": "2026-10-22", "start_utc": g["start_utc"],
            "home": g["home"], "away": g["away"], "venue": g["venue"],
            "home_form": g["record_home"], "away_form": g["record_away"],
            "line_status": "blank - waiting for official 2026-27 data (PU-01)",
            "pick": None, "winner_market": None, "handicap_market": None, "total_market": None,
            "official_url": g["url"], "official_source": nba["source_label"],
            "data_urls": [nba["calendar_url"]],
        })
    icc = INP["icc"]
    for m in icc["matches"]:
        OUT["matches"].append({
            "id": m["id"], "sport": "cricket", "competition": icc["competition"],
            "date": m["date"], "start_utc": m["date"],
            "home": m["home"], "away": m["away"], "venue": m["venue"],
            "line_status": "blank - team-strength inputs not captured from official source (PU-03)",
            "pick": None, "winner_market": None, "handicap_market": None, "total_market": None,
            "official_url": m["url"], "official_source": icc["source_label"],
            "data_urls": [icc["match1_url"], icc["series_news_url"]],
        })

# ----------------------------------------------------------------- flags
def run_flags():
    flag("PU-01", "NBA 2026-27 lines", INP["nba"]["blank_reason"],
         ["https://www.nba.com/games?date=2026-10-22"])
    flag("PU-02", "NHL market context", "Odds next to NHL games are league-published odds-partner prices inside the NHL's own score API; recorded as market context only, never used by the model.",
         [INP["nhl"]["score_url"]])
    flag("PU-03", "Cricket team strengths", INP["icc"]["blank_reason"],
         ["https://www.icc-cricket.com/matches/271646/new-zealand-vs-india"])
    flag("PU-04", "WST in-play rows", "Two Round-3 matches (Selt v Craigie, Wilson v Pang Junxu) were already in play at capture; they are listed on sport pages as in-play and receive no pre-match lines.",
         ["https://www.wst.tv/matches/b4533c9e-8d2c-4ecc-8dfd-c6b284705578"])
    flag("PU-05", "Montauban v Oyonnax kick-off", INP["prod2"]["olbg_note"],
         ["https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12068-montauban-oyonnax"])
    flag("PU-06", "F1 result gaps", "; ".join(INP["f1"]["gaps"]),
         ["https://www.formula1.com/en/racing/2026"])
    flag("PU-07", "Esports pairings", INP["esports_status"]["status"],
         [INP["esports_status"]["official_url"]])
    for i, u in enumerate(INP["unresolved_sports"], start=8):
        code = f"PU-{i:02d}"
        flag(code, u["sport"] + " coverage", u["status"], [u["url"]])
    flag("PU-14", "ATP unseeded proxy", INP["atp"]["unseeded_proxy_note"],
         ["https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"])
    flag("PU-15", "Model constants", "Home-edge multipliers (NHL 1.045, EHF 1.03), NHL OT home share 0.55, seed exponents (darts 1.15, tennis 0.55) and Pro D2 constants (3.5 home points, 1.35 pts/place, sd 13) are documented model assumptions, not official data; sensitivity is shown on the methodology page.",
         ["https://api.nhle.com/stats/rest/en/team/summary"])
    flag("PU-16", "Darts seed basis", "European Championship seeds are the PDC's one-year European Tour ranking seeds, not the PDC Order of Merit; leg model uses seeds only.",
         ["https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview"])
    flag("PU-17", "US GP name", "OLBG lists the event as 'USA Grand Prix'; the official FIA title is 'United States Grand Prix' (Round 18, COTA, 23-25 Oct). Reconciled as the same event.",
         ["https://www.formula1.com/en/racing/2026/united-states"])
    flag("PU-19", "MLB run-line/total", "World Series run-line and total were not originated: no verified probable-pitcher or bullpen workload data was captured from official MLB pages in this session. Money lines only.",
         ["https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-21&endDate=2026-10-28"])
    flag("PU-20", "Pro D2 totals", "Match-total markets for Pro D2 were not originated: the official J8 page lists table positions but no verified points-scored data in the captured region.",
         ["https://prod2.lnr.fr/calendrier-et-resultats"])
    flag("PU-21", "OLBG check", "All OLBG-listed eligible-sport events at capture were reconciled against official fixtures; see OLBG crosscheck in inputs.json. No excluded-sport row is originated anywhere on /pulse/.",
         ["https://www.olbg.com/betting-tips/"])

def main():
    run_nhl(); run_mlb(); run_darts(); run_ehf(); run_wst(); run_atp(); run_prod2(); run_f1(); run_blanks()
    run_flags()
    sports = {"ice-hockey":0,"basketball":0,"baseball":0,"darts":0,"handball":0,"snooker":0,"tennis":0,
              "rugby-union":0,"cricket":0,"motor-racing":0}
    for m in OUT["matches"]:
        sports[m["sport"]] = sports.get(m["sport"], 0) + 1
    OUT["sports_covered"] = sports
    OUT["rules"] = {
        "high": "p >= 0.70 AND fair American in [-250, +10000]",
        "medium": "0.575 <= p < 0.70, or p >= 0.70 but heavier than -250",
        "low": "p < 0.575",
        "excluded_sports": ["football (soccer)", "american football", "horse racing", "boxing", "ufc/mma", "cycling", "hurling", "specials"],
    }
    json.dump(OUT["matches"], open(os.path.join(ROOT, "data/pulse/matches.json"), "w"), indent=1, ensure_ascii=False)
    json.dump({"generated_at": INP["captured_at"], "flags": FLAGS},
              open(os.path.join(ROOT, "data/pulse/flagged.json"), "w"), indent=1, ensure_ascii=False)
    high = [m for m in OUT["matches"] if m.get("best_confident_market") and m["best_confident_market"]["confidence"] == "high"]
    print(f"matches: {len(OUT['matches'])}  flags: {len(FLAGS)}  high-picks: {len(high)}")
    for m in OUT["matches"]:
        if m.get("pick"):
            pm = m["pick"]
            print(f"  {m['id']:<26} {m['sport']:<13} {pm['selection'][:52]:<54} p={pm['probability']:<7} {pm['fair_american']} ({pm['confidence']})")

if __name__ == "__main__":
    main()
