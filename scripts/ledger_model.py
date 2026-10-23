#!/usr/bin/env python3
"""Ledger desk (session 21a0c524): originate own fair prices from data/ledger/inputs.json.

Inputs are first-hand transcriptions of official pages read 2026-10-23 (see sources.json).
OLBG tip percentages are never used. Where an input is missing the fixture is published
unpriced and flagged in data/ledger/flagged.json (built by ledger_predictions.py).

Methods (documented on ledger/method.html):
- NHL / MLB / RLWC: independent Poisson scoring rates from goals/runs/points for-against.
- EuroLeague: Normal approximation on expected points from PF/PA per game.
- Snooker: log-strength from world-ranking prize money; below-top-36 opponents use the
  36th-place figure (£198,500) as a ceiling, so a favourite's price is a floor (flagged).
- Golf outright / F1 outright: transparent share models on 36-hole deficit / championship
  points. Low confidence by construction.
Confidence: High >=0.70, Medium >=0.60, Low below, with caps for tiny samples.
Band: fair American odds in [-250, +10000]. p>=0.70 inside the band means 0.7000-0.7143.
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN = json.loads((ROOT / "data/ledger/inputs.json").read_text())

def american(p):
    if p <= 0 or p >= 1: return None
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)

def conf(p, cap=None):
    c = "High" if p >= 0.70 else ("Medium" if p >= 0.60 else "Low")
    order = {"Low": 0, "Medium": 1, "High": 2}
    if cap and order[c] > order[cap]: c = cap
    return c

def tier(p, am):
    if am is None: return ""
    in_band = am >= -250  # American odds are >= -10000.. ; band is -250..+10000 (all + odds here < +10000 unless p tiny)
    if p >= 0.70 and in_band and am <= 10000: return "A"
    if p >= 0.70: return "B"
    return "C" if in_band else ""

def sel(fixture, market, selection, p, cap=None, note=""):
    am = american(p)
    return {"fixture": fixture, "market": market, "selection": selection,
            "prob": round(p, 4), "american": am, "decimal": round(1 / p, 3) if p else None,
            "confidence": conf(p, cap), "tier": tier(p, am),
            "in_band": (am is not None and -250 <= am <= 10000), "note": note}

def phi(z): return 0.5 * (1 + math.erf(z / math.sqrt(2)))

def pois(k, lam): return math.exp(-lam) * lam ** k / math.factorial(k)

def poisson_markets(fid, a_name, h_name, lam_a, lam_h, totals, cap=None, unit="goals", handicap=1.5, maxn=None):
    if maxn is None:
        mx = max(lam_a, lam_h); maxn = int(mx + 8 * mx ** 0.5) + 12
    """Returns selections: match winner (2-way, draw split), handicap -1.5/+1.5, totals O/U."""
    pa = [pois(i, lam_a) for i in range(maxn + 1)]
    ph = [pois(i, lam_h) for i in range(maxn + 1)]
    pa = [x / sum(pa) for x in pa]; ph = [x / sum(ph) for x in ph]
    p_aw = p_hw = p_dr = 0.0; p_hcap_h = p_hcap_a = 0.0; tot = {t: 0.0 for t in totals}
    for i, x in enumerate(pa):
        for j, y in enumerate(ph):
            q = x * y
            if i > j: p_aw += q
            elif j > i: p_hw += q
            else: p_dr += q
            if j - i > handicap: p_hcap_h += q
            if i - j > handicap: p_hcap_a += q
            for t in totals:
                if i + j > t: tot[t] += q
    out = []
    # 2-way winner: drawn regulation split evenly (OT/extra-innings proxy, documented)
    out.append(sel(fid, "Match winner (2-way)", h_name, p_hw + p_dr / 2, cap))
    out.append(sel(fid, "Match winner (2-way)", a_name, p_aw + p_dr / 2, cap))
    out.append(sel(fid, f"Handicap -{handicap}", h_name, p_hcap_h, cap))
    out.append(sel(fid, f"Handicap +{handicap}", a_name, 1 - p_hcap_h, cap))
    out.append(sel(fid, f"Handicap -{handicap}", a_name, p_hcap_a, cap))
    out.append(sel(fid, f"Handicap +{handicap}", h_name, 1 - p_hcap_a, cap))
    for t in totals:
        out.append(sel(fid, f"Total {unit} {t}", f"Over {t}", tot[t], cap))
        out.append(sel(fid, f"Total {unit} {t}", f"Under {t}", 1 - tot[t], cap))
    return out, {"lam_away": round(lam_a, 3), "lam_home": round(lam_h, 3), "p_draw_reg": round(p_dr, 4)}

matches, selections = [], []

# ---------- NHL ----------
teams = IN["nhl_teams"]
complete = {k: v for k, v in teams.items() if v[0] and v[1] is not None}
league_gpg = sum(v[1] for v in complete.values()) / sum(v[0] for v in complete.values())
HOME = 1.06  # documented home-ice scoring uplift assumption (not an official statistic)
for (date, utc, aa, ha, an, hn, venue, ra, rh, gid, leaders) in IN["nhl_fixtures"]:
    fid = f"NHL-{gid}"
    m = {"id": fid, "sport": "Ice Hockey", "competition": "NHL 2026-27 regular season", "date": date,
         "start": utc, "away": an, "home": hn, "venue": venue, "status": "Upcoming",
         "source_keys": ["nhl-score23" if date == "2026-10-23" else "nhl-score24", "nhl-summary"],
         "context": f"Away record {ra}; home record {rh} (NHL score feed). Leaders: {leaders}.",
         "priced": False}
    A, H = teams[aa], teams[ha]
    if A[1] is None or H[1] is None:
        m["blank_reason"] = "Calgary goals for/against truncated in the stats chunk read — no price originated."
    else:
        lam_a = (A[1] / A[0]) * (H[2] / H[0]) / league_gpg / HOME
        lam_h = (H[1] / H[0]) * (A[2] / A[0]) / league_gpg * HOME
        s, extra = poisson_markets(fid, an, hn, lam_a, lam_h, [5.5, 6.5], unit="goals")
        selections += s; m["priced"] = True; m["rates"] = extra
        m["inputs"] = f"{aa}: {A[1]} GF / {A[2]} GA in {A[0]} GP; {ha}: {H[1]} GF / {H[2]} GA in {H[0]} GP; league baseline {league_gpg:.3f} goals/team/game (31 complete teams)."
    matches.append(m)

# ---------- MLB ----------
T = IN["mlb"]["teams"]
base = (T["Tampa Bay Rays"]["RS"] + T["Milwaukee Brewers"]["RS"]) / (2 * 162)  # runs scored per team-game
for (date, utc, label, away, home, venue, pk, note) in IN["mlb"]["games"]:
    fid = f"MLB-{pk}"
    A, H = T[away], T[home]
    lam_a = (A["RS"] / A["GP"]) * (H["RA"] / H["GP"]) / base
    lam_h = (H["RS"] / H["GP"]) * (A["RA"] / A["GP"]) / base * 1.03
    s, extra = poisson_markets(fid, away, home, lam_a, lam_h, [7.5, 8.5], unit="runs")
    selections += s
    matches.append({"id": fid, "sport": "Baseball", "competition": f"MLB World Series {label} ({note})",
                    "date": date, "start": utc, "away": away, "home": home, "venue": venue, "status": "Upcoming",
                    "source_keys": ["mlb-sched", "mlb-al", "mlb-nl"], "priced": True, "rates": extra,
                    "context": f"Rays 98-64 (.605), 736 RS / 650 RA, last ten 5-5; Brewers 103-59 (.636), 832 RS / 618 RA, last ten 8-2, streak W5 (2026 regular season, MLB standings feeds). Probable pitchers were not in the feeds read — see flags.",
                    "inputs": f"Two-team run baseline {base:.3f} runs/team/game from the finalists' own RS/RA (documented limitation)."})

# ---------- EuroLeague (Normal) ----------
S = IN["euroleague"]["standings"]
lg = sum(v[3] for v in S.values()) / sum(v[0] for v in S.values())
SD_MARGIN = 13.0; SD_TOTAL = 18.0  # documented assumptions, not official statistics
for i, (date, t, home, away, venue) in enumerate(IN["euroleague"]["fixtures"], 1):
    fid = f"EL-R8-{i:02d}"; H, A = S[home], S[away]
    eh = (H[3] / H[0]) * (A[4] / A[0]) / lg * 1.02
    ea = (A[3] / A[0]) * (H[4] / H[0]) / lg
    margin, total = eh - ea, eh + ea
    ph = phi(margin / SD_MARGIN)
    line = round(abs(margin) * 2) / 2
    fav = home if margin >= 0 else away
    p_fav_cover = phi((abs(margin) - line) / SD_MARGIN) if line else ph if margin >= 0 else 1 - ph
    tline = round(total * 2) / 2
    p_over = 1 - phi((tline - total) / SD_TOTAL)
    selections += [sel(fid, "Match winner", home, ph), sel(fid, "Match winner", away, 1 - ph),
                   sel(fid, f"Handicap {fav} -{line}", fav, p_fav_cover),
                   sel(fid, f"Handicap {fav} -{line}", (away if fav == home else home) + f" +{line}", 1 - p_fav_cover),
                   sel(fid, f"Total points {tline}", f"Over {tline}", p_over),
                   sel(fid, f"Total points {tline}", f"Under {tline}", 1 - p_over)]
    matches.append({"id": fid, "sport": "Basketball", "competition": "EuroLeague Regular Season Round 8",
                    "date": date, "start": t, "away": away, "home": home, "venue": venue, "status": "Upcoming",
                    "source_keys": ["el-sched", "el-stand"], "priced": True,
                    "rates": {"exp_home": round(eh, 2), "exp_away": round(ea, 2)},
                    "context": f"{home}: {H[1]}-{H[2]} in {H[0]} GP, {H[3]} PF / {H[4]} PA; {away}: {A[1]}-{A[2]} in {A[0]} GP, {A[3]} PF / {A[4]} PA (standings after Round 7).",
                    "inputs": f"League baseline {lg:.2f} pts/team/game; margin SD {SD_MARGIN} and total SD {SD_TOTAL} are stated assumptions."})

# ---------- Rugby League ----------
pf = {}; pa_ = {}; gp = {}
for (_, h, hs, a, as_, v) in IN["rlwc"]["results_r1"] + IN["rlwc"]["results_r2"]:
    for tm, f, ag in ((h, hs, as_), (a, as_, hs)):
        pf[tm] = pf.get(tm, 0) + f; pa_[tm] = pa_.get(tm, 0) + ag; gp[tm] = gp.get(tm, 0) + 1
mean_pts = sum(pf.values()) / sum(gp.values())
for i, (date, t, home, away, venue, ph_, pa) in enumerate(IN["rlwc"]["fixtures_r2"], 1):
    fid = f"RLWC-R2-{i}"
    # heavy shrinkage: 2 phantom games at tournament mean (1-2 real games per team)
    def rate(tm):
        return ((pf[tm] + 2 * mean_pts) / (gp[tm] + 2), (pa_[tm] + 2 * mean_pts) / (gp[tm] + 2))
    hf, ha_ = rate(home); af, aa_ = rate(away)
    eh = hf * aa_ / mean_pts; ea = af * ha_ / mean_pts
    # Rugby league points are heavily over-dispersed vs Poisson on 1-2 game samples;
    # use a Normal margin/total with wide stated SDs (margin 16, total 19) instead.
    margin, total = eh - ea, eh + ea
    ph = phi(margin / 16.0)
    fav = home if margin >= 0 else away
    p_cover = phi((abs(margin) - 12.5) / 16.0)
    p_over = 1 - phi((44.5 - total) / 19.0)
    s = [sel(fid, "Match winner (2-way)", home, ph, "Medium"), sel(fid, "Match winner (2-way)", away, 1 - ph, "Medium"),
         sel(fid, "Handicap -12.5", fav, p_cover, "Medium"), sel(fid, "Handicap +12.5", away if fav == home else home, 1 - p_cover, "Medium"),
         sel(fid, "Total points 44.5", "Over 44.5", p_over, "Medium"), sel(fid, "Total points 44.5", "Under 44.5", 1 - p_over, "Medium")]
    extra = {"exp_home": round(eh, 2), "exp_away": round(ea, 2), "sd_margin": 16.0, "sd_total": 19.0}
    selections += s
    matches.append({"id": fid, "sport": "Rugby League", "competition": "Rugby League World Cup 2026 Round 2",
                    "date": date, "start": t, "away": away, "home": home, "venue": venue, "status": "Upcoming",
                    "source_keys": ["rlwc-r1", "rlwc-r2"], "priced": True, "rates": extra,
                    "context": f"{home} ({ph_} as served): {pf[home]} scored / {pa_[home]} conceded in {gp[home]} game(s); {away} ({pa} as served): {pf[away]} / {pa_[away]} in {gp[away]}. One/two-game samples — confidence capped at Medium and flagged.",
                    "inputs": "Tournament mean points/team/game with 2 phantom games of shrinkage per team (stated method)."})
matches.append({"id": "RLWC-R2-FT", "sport": "Rugby League", "competition": "Rugby League World Cup 2026 Round 2",
                "date": "2026-10-23", "start": "Full Time", "away": "Lebanon", "home": "Tonga",
                "venue": "CommBank Stadium, Sydney", "status": "Completed: Tonga 36-0 Lebanon",
                "source_keys": ["rlwc-r2"], "priced": False, "blank_reason": "Already completed at capture — listed for completeness, never priced."})

# ---------- Snooker ----------
R = IN["snooker"]["rankings_gbp"]; BOUND = 198500
for (date, t, comp, rnd, p1, p2, mid) in IN["snooker"]["fixtures"]:
    fid = f"SN-{mid[:8]}"
    m = {"id": fid, "sport": "Snooker", "competition": f"{comp}, {rnd}", "date": date, "start": t,
         "away": p2, "home": p1, "venue": "", "status": "Upcoming", "source_keys": ["wst-home", "wst-rank"], "priced": False}
    if "Winner of" in p1 or "Winner of" in p2:
        m["blank_reason"] = "Participants not yet known on the official page — no price originated."
    else:
        v1 = R.get(p1, [None, None])[1]; v2 = R.get(p2, [None, None])[1]
        bounded = (v1 is None) ^ (v2 is None)
        if v1 is None and v2 is None:
            m["blank_reason"] = "Neither player's ranking money is in the top-36 table read — no price originated."
        else:
            e1 = math.log(v1 or BOUND); e2 = math.log(v2 or BOUND)
            p = 1 / (1 + math.exp(-(e1 - e2) * 1.4))
            note = "Bounded: opponent below top 36, £198,500 (36th) used as ceiling — favourite price is a floor." if bounded else ""
            cap = "Medium" if bounded else None
            selections += [sel(fid, "Match winner", p1, p, cap, note), sel(fid, "Match winner", p2, 1 - p, cap, note)]
            m["priced"] = True
            m["context"] = f"World ranking money: {p1} {'£{:,}'.format(v1) if v1 else 'below top 36 (not served)'}; {p2} {'£{:,}'.format(v2) if v2 else 'below top 36 (not served)'}."
            m["inputs"] = "Log-strength on ranking money (stated method). Match format (best-of) was not on the pages read, so no frame handicap or total is offered."
    matches.append(m)
for (date, rnd, p1, s1, p2, s2, st) in IN["snooker"]["live_qf"]:
    matches.append({"id": f"SN-QF-{p1.split()[-1]}", "sport": "Snooker",
                    "competition": f"BetVictor Northern Ireland Open 2026, {rnd}", "date": date, "start": "Live at capture",
                    "away": p2, "home": p1, "venue": "", "status": f"{st}: {p1} {s1}-{s2} {p2}",
                    "source_keys": ["wst-home"], "priced": False, "blank_reason": "In play at capture — never priced in-play on this desk."})

# ---------- Cricket (fixtures only) ----------
for i, (date, series, home, away, venue, t) in enumerate(IN["cricket"], 1):
    matches.append({"id": f"CR-{i:02d}", "sport": "Cricket", "competition": series, "date": date, "start": t,
                    "away": away, "home": home, "venue": venue, "status": "Upcoming", "source_keys": ["ca-matches"],
                    "priced": False, "blank_reason": "No official table, ranking or recent-result feed was read for these teams — fixture published, no price originated (flag LG-CR1)."})

# ---------- Golf outright ----------
leaders = IN["golf"]["leaders"]
# win weights: exp(-(shots behind leader)/2.2), normalised over listed players (stated method, 36 holes left)
w = [(n, math.exp(-((-10 - s) * -1) / 2.2) if False else math.exp(-(s - (-10)) / 2.2), s, r1, r2) for (n, s, r1, r2) in leaders]
tot_w = sum(x[1] for x in w)
for (n, wt, s, r1, r2) in w:
    p = wt / tot_w
    selections.append(sel("GO-GENESIS", "Outright winner (36 holes completed)", n, p, "Low",
                          "Share model on strokes deficit only; field beyond -4 not listed, so shares are upper bounds."))
matches.append({"id": "GO-GENESIS", "sport": "Golf", "competition": IN["golf"]["event"], "date": "2026-10-23 (after R2)",
                "start": "Rounds 3-4 to follow", "away": "", "home": "Genesis Championship field (leaders listed)", "venue": "",
                "status": "In progress — outright only", "source_keys": ["dpwt-lb"], "priced": True,
                "context": "Co-leaders at -10: Antoine Rozner (67, 65) and Casey Jarvis (65, 67); four players at -7; three at -6 (official leaderboard).",
                "inputs": "Strokes-deficit share weights; players worse than -4 are not in the chunk read and are excluded — flagged LG-GO1."})

# ---------- F1 outright ----------
pts = IN["f1"]["standings"]; tot_p = sum(x[2] for x in pts)
for (n, tm, p_) in pts:
    selections.append(sel("MR-USGP", "Race winner — United States GP (R18)", f"{n} ({tm})", p_ / tot_p, "Low",
                          "Championship-points share only; no practice/qualifying data read."))
matches.append({"id": "MR-USGP", "sport": "Motor Racing", "competition": "Formula 1 Round 18, United States", "date": "23-25 Oct 2026",
                "start": "LIVE weekend at capture", "away": "", "home": "United States Grand Prix", "venue": "",
                "status": "Race weekend under way — outright only", "source_keys": ["f1-cal", "f1-stand"], "priced": True,
                "context": "Standings: Antonelli 340, Russell 238, Hamilton 229, Verstappen 221, Leclerc 215, Norris 201. Winners read for R1-R7: Russell (Australia), Antonelli (China, Japan, Miami, Canada, Monaco), Hamilton (Barcelona-Catalunya).",
                "inputs": "Points-share outright weights for the top 10 only — flagged LG-MR1."})
for (rnd, name, dates, st) in IN["f1"]["events"][1:]:
    matches.append({"id": f"MR-{name.upper()[:6]}", "sport": "Motor Racing", "competition": f"Formula 1 {rnd}, {name}",
                    "date": dates, "start": "", "away": "", "home": f"{name} Grand Prix", "venue": "", "status": st,
                    "source_keys": ["f1-cal"], "priced": False, "blank_reason": "Future round listed from the official calendar; no separate price originated this far out."})

# ---------- Handball ----------
hb_priced = {"MRK Sloga Doboj|Kur": (38, 26), "Kosovo|Estonia": (39, 22)}
for i, (t, comp, home, away) in enumerate(IN["handball"]["fixtures_24oct"], 1):
    fid = f"HB-{i:02d}"
    m = {"id": fid, "sport": "Handball", "competition": comp, "date": "2026-10-24", "start": t, "away": away,
         "home": home, "venue": "", "status": "Upcoming", "source_keys": ["ehf"], "priced": False}
    key = f"{home}|{away}"
    if key in hb_priced:
        f_, a_ = hb_priced[key]
        # regress the single result 50% toward 28-28, wide stated SDs (margin 6.5, total 8.5)
        eh = (f_ + 28) / 2; ea = (a_ + 28) / 2
        margin, total = eh - ea, eh + ea
        ph = phi(margin / 6.5); p_cover = phi((abs(margin) - 4.5) / 6.5); p_over = 1 - phi((54.5 - total) / 8.5)
        fav = home if margin >= 0 else away
        s = [sel(fid, "Match winner (2-way)", home, ph, "Low"), sel(fid, "Match winner (2-way)", away, 1 - ph, "Low"),
             sel(fid, "Handicap -4.5", fav, p_cover, "Low"), sel(fid, "Handicap +4.5", away if fav == home else home, 1 - p_cover, "Low"),
             sel(fid, "Total goals 54.5", "Over 54.5", p_over, "Low"), sel(fid, "Total goals 54.5", "Under 54.5", 1 - p_over, "Low")]
        extra = {"exp_home": eh, "exp_away": ea, "sd_margin": 6.5, "sd_total": 8.5}
        selections += s; m["priced"] = True; m["rates"] = extra
        m["context"] = f"Same pairing played 23 Oct: {home} won {f_}-{a_} per the EHF feed (listed with {away} first that day). Single-result sample — Low confidence, flagged."
        m["inputs"] = "Expected goals = single result regressed 50% toward 28-28; margin SD 6.5 / total SD 8.5 are stated assumptions."
    else:
        m["blank_reason"] = "No official form/table feed read for these clubs — fixture published, no price originated (flag LG-HB1)."
    matches.append(m)

# ---------- Gaelic / Tennis context / empty sports ----------
for (date, t, comp, home, away, venue, note) in IN["gaelic"]:
    matches.append({"id": "GA-01", "sport": "Gaelic Sports", "competition": comp, "date": date, "start": t,
                    "away": away, "home": home, "venue": venue, "status": "Upcoming", "source_keys": ["gaa"], "priced": False,
                    "context": note, "blank_reason": "No official form data read; also an OLBG scope note — OLBG lists 'Gaelic Football' (25) and 'Hurling' (26) separately while this is the Shinty-Hurling International (flag LG-GA1)."})
for i, (ev, w_, l_, sc) in enumerate(IN["tennis"]["qf_results"], 1):
    matches.append({"id": f"TE-QF{i}", "sport": "Tennis", "competition": f"ATP {ev} quarter-final", "date": "2026-10-23",
                    "start": "Completed", "away": l_, "home": w_, "venue": "", "status": f"Completed: {w_} won {sc}",
                    "source_keys": ["atp-scores"], "priced": False, "blank_reason": "Completed before capture — semi-final pairings were not confirmable in the readable draw chunks (flag LG-TE1)."})
for (ev, p1, p2, st) in IN["tennis"]["live"]:
    matches.append({"id": "TE-LIVE", "sport": "Tennis", "competition": f"ATP {ev} quarter-final", "date": "2026-10-23",
                    "start": "Live at capture", "away": p2, "home": p1, "venue": "", "status": st,
                    "source_keys": ["atp-scores"], "priced": False, "blank_reason": "In play at capture — never priced in-play on this desk."})

out = {"meta": {"desk": "ledger", "session": "21a0c524", "generated_for": "2026-10-23",
               "matches": len(matches), "selections": len(selections),
               "league_baselines": {"nhl_gpg": round(league_gpg, 3), "mlb_runs_two_team": round(base, 3), "euroleague_ppg": round(lg, 2), "rlwc_mean_pts": round(mean_pts, 2)}},
       "matches": matches, "selections": selections}
(ROOT / "data/ledger/lines.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f"matches={len(matches)} selections={len(selections)} priced_fixtures={sum(m['priced'] for m in matches)}")
best = {}
for s in selections:
    sp = next(m["sport"] for m in matches if m["id"] == s["fixture"])
    best.setdefault(sp, []).append(s)
for sp, ss in best.items():
    top = sorted(ss, key=lambda x: -x["prob"])[:6]
    print(sp, [(x["fixture"], x["market"], x["selection"], x["prob"], x["american"], x["tier"]) for x in top])
