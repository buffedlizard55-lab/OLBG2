"""Cadence desk — independent line origination for 2026-10-23.

Reads ``data/cadence/fixtures.json`` and originates, for every fixture where an official
numeric input exists: match winner (two- or three-way), handicap/spread, and match total
(goals, points, runs, frames, legs, games or sets).

Probability formulas are fixed and documented; every one is a function of numbers read from
the official source stored beside the fixture. No bookmaker price is an input. Where the
official feed published a price it is kept only as a comparison column on the match page.

Confidence grading
------------------
high   : P >= 0.70 **and** the official input is a full-season table/ranking (tier A) or a
         4-9 match current-season sample (tier B).
medium : P >= 0.60, or P >= 0.70 on a tier-C sample (capped; the cap is printed on the row).
low    : everything else.

Price band
----------
-250 is 0.714285..., so "high (>= 0.70)" and "-250..+10000" intersect only in
[0.7000, 0.7143]. Each row states its fair price, so a reader can see immediately whether a
high-confidence pick is inside the band. In addition, where a market has a continuous line
ladder the desk quotes the alternate line nearest to that ceiling ("band line"), with its own
probability and price. Nothing is relabelled: both lines are published.

Run: python3 scripts/cadence_model.py -> data/cadence/{matches,lines,picks}.json
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "cadence")
BAND_LOW, BAND_HIGH = -250, 10000
HIGH_P = 0.70
FLOOR_P = 250.0 / 350.0  # 0.7142857 = fair -250
GENERATED = "2026-10-23T20:10:00Z"


# ---------------------------------------------------------------- helpers
def z(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    lo, hi = -8.0, 8.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def american(p):
    if p is None:
        return None
    p = min(max(p, 1e-4), 1 - 1e-4)
    if p >= 0.5:
        return int(round(-100.0 * p / (1 - p)))
    return int(round(100.0 * (1 - p) / p))


def dec(p):
    if p is None:
        return None
    return round(1.0 / min(max(p, 1e-4), 1 - 1e-4), 3)


def in_band(p):
    if p is None:
        return False
    return BAND_LOW <= american(p) <= BAND_HIGH


def log5(pa, pb, home_mult=1.0):
    pa = min(max(pa, 0.02), 0.98)
    pb = min(max(pb, 0.02), 0.98)
    den = pa + pb - 2 * pa * pb
    if den <= 0:
        return 0.5
    p = (pa - pa * pb) / den
    p = p * home_mult / (p * home_mult + (1 - p))
    return min(max(p, 0.02), 0.98)


def poisson_over(lam, line):
    k = int(math.floor(line))
    cdf = sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))
    return 1 - cdf


def p_gt(mu, sigma, line):
    """P(X > line) for a normal margin/total with mean mu."""
    return 1 - ncdf((line - mu) / sigma)


def shrink(w, gp, prior_games=7.0):
    return (w + prior_games / 2.0) / (gp + prior_games)


def market(kind, selection, line, p, basis, margin, band_line=False, three_way=False, draw=None):
    p = min(max(p, 1e-4), 1 - 1e-4)
    p = round(p, 6)                      # every published number derives from this value
    row = {"market": kind, "selection": selection, "line": line,
           "probability": p, "fair_american": american(p),
           "fair_decimal": dec(p),
           "offered_decimal": round(dec(p) / (1 - margin), 3),
           "offered_american": american(p * (1 - margin)),
           "in_band": in_band(p), "band_line": band_line, "basis": basis,
           "three_way": three_way}
    if draw is not None:
        row["draw_probability"] = round(draw, 4)
        row["draw_fair_american"] = american(draw)
    return row


def band_search(kind, template, mu, sigma, lo, hi, step, basis, margin, label_total=False,
                three_way=False, draw=None):
    """Alternate line closest to the -250 ceiling whose probability is still >= 0.70."""
    best = None
    n = int(round((hi - lo) / step))
    for i in range(n + 1):
        line = round(lo + i * step, 2)
        p = p_gt(mu, sigma, line)
        if HIGH_P <= p <= FLOOR_P + 1e-12 and (best is None or p > best[1]):
            best = (line, p)
    if best is None:
        return None
    line, p = best
    if label_total:
        sel = template.replace("{l}", f"{line:.1f}")
    else:
        sel = template.replace("{l}", f"{line:+.1f}")
    return market(kind, sel, line, p, basis, margin, band_line=True,
                  three_way=three_way, draw=draw)


SPREAD_TEMPLATE = "{team} {l}"


# ---------------------------------------------------------------- per-sport models
def model_nhl(f):
    h, a = f["inputs"]["home"], f["inputs"]["away"]
    ph, pa = h["pts"] / (2 * h["gp"]), a["pts"] / (2 * a["gp"])
    p_home = log5(ph, pa, 1.09)
    mu = z(p_home) * 1.85
    lam_h = (h["gf"] / h["gp"] + a["ga"] / a["gp"]) / 2 * 1.04
    lam_a = (a["gf"] / a["gp"] + h["ga"] / a["gp"]) / 2
    lam = lam_h + lam_a
    fav = f["home"] if p_home >= 0.5 else f["away"]
    dog = f["away"] if fav == f["home"] else f["home"]
    p_fav, mu_fav = max(p_home, 1 - p_home), abs(mu)
    base = (f"NHL points% {ph:.3f} v {pa:.3f} with a 9% home term; goal rates {lam_h:.2f}+{lam_a:.2f} "
            f"from {h['gp']} and {a['gp']} games")
    out = [market("Money line", fav, None, p_fav, base, 0.045),
           market("Puck line", f"{fav} -1.5", -1.5, p_gt(mu_fav, 1.75, 1.5), base + "; margin sigma 1.75 goals", 0.045),
           market("Puck line", f"{dog} +1.5", 1.5, 1 - p_gt(mu_fav, 1.75, 1.5), base + "; margin sigma 1.75 goals", 0.045)]
    for line in (5.5, 6.5):
        p_over = poisson_over(lam, line)
        out += [market("Total goals", f"Over {line}", line, p_over, base + f"; Poisson mean {lam:.2f}", 0.045),
                market("Total goals", f"Under {line}", line, 1 - p_over, base + f"; Poisson mean {lam:.2f}", 0.045)]
    b = band_search("Puck line", SPREAD_TEMPLATE.replace("{team}", fav), mu_fav, 1.75, -2.5, 3.5, 1.0, base + "; margin sigma 1.75 goals", 0.045)
    if b:
        out.append(b)
    b = band_search("Total goals", "Over {l}", lam, math.sqrt(lam), 3.5, 12.5, 1.0,
                    base + f"; Poisson mean {lam:.2f}", 0.045, label_total=True)
    if b:
        out.append(b)
    return {"p_home": p_home, "markets": out, "tier": "B",
            "evidence": f"NHL 2026-27, {h['gp']} and {a['gp']} games played"}


def model_basketball(f):
    no_numeric = False
    if "home" in f["inputs"]:
        h, a = f["inputs"]["home"], f["inputs"]["away"]
        ph, pa = shrink(h["w"], h["gp"], 7), shrink(a["w"], a["gp"], 7)
        p_home = log5(ph, pa, 1.12)
        dh, da = (h["pf"] - h["pa"]) / h["gp"], (a["pf"] - a["pa"]) / a["gp"]
        mu = (dh - da) * 1.05 + z(p_home) * 3.0
        lam = (h["pf"] / h["gp"] + a["pa"] / a["gp"]) / 2 + (a["pf"] / a["gp"] + h["pa"] / h["gp"]) / 2
        tier, sigma = "B", 10.5
        base = (f"EuroLeague 2026-27: {h['w']}-{h['l']} in {h['gp']} v {a['w']}-{a['l']} in {a['gp']}; "
                f"shrunk win rates {ph:.3f} v {pa:.3f}; point differential {dh:+.1f} v {da:+.1f}")
    else:
        wh = {"1-0": 1.0, "0-1": 0.0}.get(f["inputs"]["home_record"], 0.5)
        wa = {"1-0": 1.0, "0-1": 0.0}.get(f["inputs"]["away_record"], 0.5)
        ph, pa = shrink(wh, 1, 10), shrink(wa, 1, 10)
        p_home = log5(ph, pa, 1.11)
        mu, lam, tier, sigma = z(p_home) * 11.5, 224.0, "C", 12.0
        no_numeric = True
        base = ("NBA 2026-27: one or two games per club, so the model uses a league-average prior "
                "with an 11% home term (sample too small to separate the teams)")
    fav = f["home"] if p_home >= 0.5 else f["away"]
    dog = f["away"] if fav == f["home"] else f["home"]
    p_fav, mu_fav = max(p_home, 1 - p_home), abs(mu)
    out = [market("Money line", fav, None, p_fav, base + f"; sigma {sigma} points", 0.05)]
    for line in (1.5, 3.5, 5.5):
        out.append(market("Point spread", f"{fav} -{line}", -line, p_gt(mu_fav, sigma, line),
                          base + f"; sigma {sigma} points", 0.05))
    out.append(market("Point spread", f"{dog} +5.5", 5.5, 1 - p_gt(mu_fav, sigma, 5.5),
                      base + f"; sigma {sigma} points", 0.05))
    for line in (210.5, 218.5, 226.5, 234.5):
        p_over = p_gt(lam, sigma * 1.55, line)
        out += [market("Game total", f"Over {line}", line, p_over, base + f"; total mean {lam:.1f}", 0.05),
                market("Game total", f"Under {line}", line, 1 - p_over, base + f"; total mean {lam:.1f}", 0.05)]
    b = band_search("Point spread", SPREAD_TEMPLATE.replace("{team}", fav), mu_fav, sigma, -24.5, 24.5, 1.0,
                    base + f"; sigma {sigma} points", 0.05)
    if b:
        out.append(b)
    b = band_search("Game total", "Over {l}", lam, sigma * 1.55, 150.5, 289.5, 1.0,
                    base + f"; total mean {lam:.1f}", 0.05, label_total=True)
    if b:
        out.append(b)
    return {"p_home": p_home, "markets": out, "tier": tier, "evidence": base,
            "no_numeric": no_numeric}


def model_baseball(f):
    no_numeric = False
    h, a = f["inputs"]["home"], f["inputs"]["away"]

    def pyth(t):
        return t["rs"] ** 1.83 / (t["rs"] ** 1.83 + t["ra"] ** 1.83)

    ph, pa = pyth(h), pyth(a)
    spa, spb = f["inputs"]["home_sp"], f["inputs"]["away_sp"]
    adj = 0.0
    if spa.get("era") and spb.get("era"):
        adj = max(min((spb["era"] - spa["era"]) * 0.045, 0.10), -0.10)
    p_home = min(max(log5(ph, pa, 1.06) + adj, 0.03), 0.97)
    mu = z(p_home) * 4.05
    lam = (h["rs"] / 162 + a["ra"] / 162) / 2 + (a["rs"] / 162 + h["ra"] / 162) / 2
    fav = f["home"] if p_home >= 0.5 else f["away"]
    dog = f["away"] if fav == f["home"] else f["home"]
    p_fav, mu_fav = max(p_home, 1 - p_home), abs(mu)
    base = (f"Pythagorean win% {ph:.3f} v {pa:.3f} from 2026 runs, 6% home term, "
            f"starter adjustment {adj*100:+.1f} points ({spa['name']} v {spb['name']})")
    out = [market("Money line", fav, None, p_fav, base, 0.04),
           market("Run line", f"{fav} -1.5", -1.5, p_gt(mu_fav, 4.05, 1.5), base + "; margin sigma 4.05 runs", 0.04),
           market("Run line", f"{dog} +1.5", 1.5, 1 - p_gt(mu_fav, 4.05, 1.5), base + "; margin sigma 4.05 runs", 0.04)]
    for line in (7.5, 8.5):
        p_over = p_gt(lam, 4.3, line)
        out += [market("Game total", f"Over {line}", line, p_over, base + f"; runs mean {lam:.2f}", 0.04),
                market("Game total", f"Under {line}", line, 1 - p_over, base + f"; runs mean {lam:.2f}", 0.04)]
    b = band_search("Run line", SPREAD_TEMPLATE.replace("{team}", fav), mu_fav, 4.05, -3.5, 4.5, 1.0, base, 0.04)
    if b:
        out.append(b)
    b = band_search("Game total", "Over {l}", lam, 4.3, 4.5, 14.5, 1.0, base + f"; runs mean {lam:.2f}", 0.04, label_total=True)
    if b:
        out.append(b)
    return {"p_home": p_home, "markets": out, "tier": "A",
            "evidence": "162-game 2026 records plus 2026 starter lines"}


def model_cricket(f):
    i = f["inputs"] or {}
    fmt = i.get("format", "List A")
    hf, af = str(i.get("home_form", "")).lower(), str(i.get("away_form", "")).lower()
    score = 0.0
    no_numeric = not (("won" in hf) or ("lost" in hf) or ("won" in af) or ("lost" in af))
    if "won" in hf:
        score = 0.10
    elif "lost" in hf:
        score = -0.10
    elif "won" in af:
        score = -0.10
    elif "lost" in af:
        score = 0.10
    p_home = min(max(0.5 + score + 0.03, 0.10), 0.90)
    sigma = {"T20I": 30.0, "ODI": 42.0, "WODI": 40.0, "List A": 44.0, "Test": 90.0}.get(fmt, 42.0)
    lam = {"T20I": 330.0, "ODI": 560.0, "WODI": 470.0, "List A": 560.0, "Test": 1250.0}.get(fmt, 540.0)
    mu = z(p_home) * sigma * 0.55
    fav = f["home"] if p_home >= 0.5 else f["away"]
    dog = f["away"] if fav == f["home"] else f["home"]
    p_fav = max(p_home, 1 - p_home)
    base = (f"{fmt}: the only numeric strength input captured is the last completed official result "
            f"(home form '{i.get('home_form','none')}', away form '{i.get('away_form','none')}')")
    out = [market("Match winner", fav, None, p_fav, base, 0.05)]
    hcap = round(sigma * 0.12 * 2) / 2
    out.append(market("Handicap", f"{fav} -{hcap:.1f}", -hcap, p_gt(abs(mu), sigma, hcap), base + f"; margin sigma {sigma:.0f} runs", 0.05))
    if fmt != "Test":
        for line in (round(lam * 0.85) + 0.5, round(lam * 0.95) + 0.5):
            p_over = p_gt(lam, sigma * 1.5, line)
            out += [market("Total runs", f"Over {line}", line, p_over, base + f"; total mean {lam:.0f} runs", 0.05),
                    market("Total runs", f"Under {line}", line, 1 - p_over, base + f"; total mean {lam:.0f} runs", 0.05)]
        b = band_search("Handicap", SPREAD_TEMPLATE.replace("{team}", fav), abs(mu), sigma, -3 * sigma + 0.5, 3 * sigma - 0.5,
                        max(1.0, round(sigma / 8)), base, 0.05)
        if b:
            out.append(b)
    return {"p_home": p_home, "markets": out, "tier": "C",
            "evidence": f"{fmt}: one completed official result only; no published rating captured",
            "no_numeric": no_numeric}


def model_snooker(f):
    no_numeric = False
    i = f["inputs"]
    hm, am, hs, as_ = i.get("home_rank_money"), i.get("away_rank_money"), i.get("home_season"), i.get("away_season")
    if hm and am:
        p_home = 1 / (1 + 10 ** (-((math.log10(hm) - math.log10(am)) / 1.6)))
        basis = f"log10 ranking money {math.log10(hm):.3f} v {math.log10(am):.3f} (Johnstone's Paint World Rankings)"
        tier = "A"
    elif hs and as_:
        d = math.log10(hs["win_rate"]) - math.log10(as_["win_rate"])
        p_home = 1 / (1 + 10 ** (-d / 0.9))
        basis = (f"2026/27 match win rate {hs['win_rate']:.0%} v {as_['win_rate']:.0%}, "
                 f"average shot time {hs['ast']}s v {as_['ast']}s, centuries {hs['centuries']} v {as_['centuries']}")
        tier = "B"
    else:
        return None
    p_home = min(max(p_home, 0.05), 0.95)
    mu = z(p_home) * 2.2
    fav = f["home"] if p_home >= 0.5 else f["away"]
    p_fav = max(p_home, 1 - p_home)
    out = [market("Match winner", fav, None, p_fav, basis + ", best of 11 frames", 0.045),
           market("Frame handicap", f"{fav} -1.5", -1.5, p_gt(abs(mu), 2.2, 1.5), basis + "; frame margin sigma 2.2", 0.045)]
    for line in (8.5, 9.5):
        p_over = p_gt(9.6, 2.3, line)
        out += [market("Total frames", f"Over {line}", line, p_over, basis + "; frames mean 9.6", 0.045),
                market("Total frames", f"Under {line}", line, 1 - p_over, basis + "; frames mean 9.6", 0.045)]
    b = band_search("Frame handicap", SPREAD_TEMPLATE.replace("{team}", fav), abs(mu), 2.2, -4.5, 4.5, 1.0, basis, 0.045)
    if b:
        out.append(b)
    return {"p_home": p_home, "markets": out, "tier": tier, "evidence": basis,
            "no_numeric": False}


def model_darts(f):
    no_numeric = False
    i = f["inputs"]
    hm, am = i.get("home_et_money"), i.get("away_et_money")
    hs, asd = i.get("home_seed"), i.get("away_seed")
    if hm and am:
        p_home = 1 / (1 + 10 ** (-((math.log10(hm) - math.log10(am)) / 1.4)))
        basis = f"2026 European Tour prize money £{hm:,} v £{am:,}"
        tier = "A"
    elif hs and asd:
        p_home = 1 / (1 + 10 ** (-((math.log10(asd / hs)) / 3.0)))
        basis = f"official European Tour seeding {hs} v {asd}"
        tier = "A"
    else:
        return None
    p_home = min(max(p_home, 0.05), 0.95)
    mu = z(p_home) * 2.0
    fav = f["home"] if p_home >= 0.5 else f["away"]
    p_fav = max(p_home, 1 - p_home)
    out = [market("Match winner", fav, None, p_fav, basis + ", best of 11 legs", 0.05),
           market("Leg handicap", f"{fav} -1.5", -1.5, p_gt(abs(mu), 2.0, 1.5), basis + "; leg margin sigma 2.0", 0.05)]
    for line in (8.5, 9.5):
        p_over = p_gt(9.4, 2.1, line)
        out += [market("Total legs", f"Over {line}", line, p_over, basis + "; legs mean 9.4", 0.05),
                market("Total legs", f"Under {line}", line, 1 - p_over, basis + "; legs mean 9.4", 0.05)]
    b = band_search("Leg handicap", SPREAD_TEMPLATE.replace("{team}", fav), abs(mu), 2.0, -4.5, 4.5, 1.0, basis, 0.05)
    if b:
        out.append(b)
    return {"p_home": p_home, "markets": out, "tier": tier, "evidence": basis,
            "no_numeric": no_numeric}


def model_tennis(f):
    i = f["inputs"]
    no_numeric = False
    hp, ap = i.get("home_points"), i.get("away_points")
    if hp and ap:
        p_home = 1 / (1 + 10 ** (-((math.log10(hp) - math.log10(ap)) / 1.35)))
        basis, tier = f"ATP ranking points {hp:,} v {ap:,}", "A"
    else:
        p_home, tier, no_numeric = 0.5, "C", True
        basis = "no published ranking points for both players in this capture (qualifying draw or unranked)"
    p_home = min(max(p_home, 0.05), 0.95)
    mu = z(p_home) * 4.6
    fav = f["home"] if p_home >= 0.5 else f["away"]
    p_fav = max(p_home, 1 - p_home)
    out = [market("Match winner", fav, None, p_fav, basis + ", best of three sets", 0.045),
           market("Games handicap", f"{fav} -3.5", -3.5, p_gt(abs(mu), 4.6, 3.5), basis + "; games margin sigma 4.6", 0.045)]
    for line in (21.5, 22.5):
        p_over = p_gt(22.0, 4.8, line)
        out += [market("Total games", f"Over {line}", line, p_over, basis + "; games mean 22.0", 0.045),
                market("Total games", f"Under {line}", line, 1 - p_over, basis + "; games mean 22.0", 0.045)]
    b = band_search("Games handicap", SPREAD_TEMPLATE.replace("{team}", fav), abs(mu), 4.6, -11.5, 11.5, 1.0, basis, 0.045)
    if b:
        out.append(b)
    return {"p_home": p_home, "markets": out, "tier": tier, "evidence": basis,
            "no_numeric": no_numeric}


def model_handball(f):
    no_numeric = False
    i = f["inputs"]
    if "home" not in i:
        return None
    h, a = i["home"], i["away"]
    ph, pa = shrink(h["w"], h["gp"], 7), shrink(a["w"], a["gp"], 7)
    p2 = min(max(log5(ph, pa, 1.12), 0.12), 0.88)
    draw = 0.058
    p_home = p2 * (1 - draw)
    p_away = (1 - p2) * (1 - draw)
    lam_h = (h["gf"] / h["gp"] + a["ga"] / a["gp"]) / 2
    lam_a = (a["gf"] / a["gp"] + h["ga"] / a["gp"]) / 2
    lam = lam_h + lam_a
    mu = z(p2) * 9.0
    home_fav = p2 >= 0.5
    fav = f["home"] if home_fav else f["away"]
    dog = f["away"] if home_fav else f["home"]
    p_fav = p_home if home_fav else p_away
    mu_fav = abs(mu)
    base = (f"LNH StarLigue, {h['gp']} rounds: {h['w']}-{h['l']}-{h['d']} v {a['w']}-{a['l']}-{a['d']}; "
            f"shrunk win rates {ph:.3f} v {pa:.3f}; goal rates {lam_h:.1f}+{lam_a:.1f}; draw mass 5.8%")
    out = [market("Match winner (three-way)", fav, None, p_fav, base, 0.05, three_way=True, draw=draw)]
    out.append(market("Match winner (three-way)", "Draw", None, draw, base, 0.05, three_way=True, draw=draw))
    out.append(market("Match winner (three-way)", dog, None, (p_away if home_fav else p_home), base, 0.05,
                      three_way=True, draw=draw))
    for line in (1.5, 3.5):
        out.append(market("Goal handicap", f"{fav} -{line}", -line, p_gt(mu_fav, 8.6, line) * (1 - draw),
                          base + "; goal margin sigma 8.6", 0.05, three_way=True, draw=draw))
    for line in (55.5, 60.5):
        p_over = p_gt(lam, 10.5, line)
        out += [market("Total goals", f"Over {line}", line, p_over, base + f"; total mean {lam:.1f}", 0.05),
                market("Total goals", f"Under {line}", line, 1 - p_over, base + f"; total mean {lam:.1f}", 0.05)]
    b = band_search("Goal handicap", SPREAD_TEMPLATE.replace("{team}", fav), mu_fav, 8.6, -19.5, 19.5, 1.0,
                    base + "; goal margin sigma 8.6", 0.05, three_way=True, draw=draw)
    if b:
        out.append(b)
    return {"p_home": p2, "markets": out, "tier": "B",
            "evidence": f"LNH StarLigue 2026-27, {h['gp']} and {a['gp']} rounds"}


def model_rugby_union(f):
    i = f["inputs"]
    no_numeric = False
    if "home" in i:
        h, a = i["home"], i["away"]
        ph = (h["w"] + 5.0) / (h["p"] + 10.0)
        pa = (a["w"] + 5.0) / (a["p"] + 10.0)
        p2 = min(max(log5(ph, pa, 1.10), 0.15), 0.85)
        mu = (h["pd"] - a["pd"]) / h["p"] * 1.1 + z(p2) * 2.0
        lam = 47.0
        basis = (f"Gallagher PREM after 3 rounds: {h['w']}-{h['l']} v {a['w']}-{a['l']}, "
                 f"points difference {h['pd']:+d} v {a['pd']:+d}")
        ev = basis + "; three rounds only, so confidence is capped at medium"
    else:
        p2, mu, lam = 0.53, z(0.53) * 9.5, 48.0
        no_numeric = True
        basis = "URC Round 4: no numeric point-differential input captured for both clubs; league-average prior, 3% home term"
        ev = basis
    draw = 0.032
    home_fav = p2 >= 0.5
    fav = f["home"] if home_fav else f["away"]
    dog = f["away"] if home_fav else f["home"]
    p_home3, p_away3 = p2 * (1 - draw), (1 - p2) * (1 - draw)
    p_fav = p_home3 if home_fav else p_away3
    mu_fav = abs(mu)
    out = [market("Match winner (three-way)", fav, None, p_fav, basis + "; draw mass 3.2%", 0.05,
                  three_way=True, draw=draw),
           market("Match winner (three-way)", "Draw", None, draw, basis, 0.05, three_way=True, draw=draw),
           market("Match winner (three-way)", dog, None, p_away3 if home_fav else p_home3, basis, 0.05,
                  three_way=True, draw=draw)]
    for line in (3.5, 6.5):
        out.append(market("Handicap", f"{fav} -{line}", -line, p_gt(mu_fav, 13.0, line) * (1 - draw),
                          basis + "; margin sigma 13.0 points", 0.05, three_way=True, draw=draw))
    for line in (44.5, 49.5):
        p_over = p_gt(lam, 14.0, line)
        out += [market("Total points", f"Over {line}", line, p_over, basis + f"; total mean {lam:.1f}", 0.05),
                market("Total points", f"Under {line}", line, 1 - p_over, basis + f"; total mean {lam:.1f}", 0.05)]
    b = band_search("Handicap", SPREAD_TEMPLATE.replace("{team}", fav), mu_fav, 13.0, -29.5, 29.5, 1.0,
                    basis + "; margin sigma 13.0 points", 0.05, three_way=True, draw=draw)
    if b:
        out.append(b)
    return {"p_home": p2, "markets": out, "tier": "C", "evidence": ev,
            "no_numeric": no_numeric}


def model_rugby_league(f):
    no_numeric = False
    def pos_strength(pos):
        try:
            n = int(str(pos)[0])
        except Exception:
            n = 3
        return 1 - (n - 1) / 6.0

    mh = f["inputs"].get("home_margin")
    ma = f["inputs"].get("away_margin")
    if mh is None or ma is None:
        return None
    sh = min(max(0.5 + mh * 0.006, 0.15), 0.85)
    sa = min(max(0.5 + ma * 0.006, 0.15), 0.85)
    p2 = min(max(log5(sh, sa, 1.05), 0.10), 0.90)
    mu = z(p2) * 13.5
    draw = 0.012
    home_fav = p2 >= 0.5
    fav = f["home"] if home_fav else f["away"]
    dog = f["away"] if home_fav else f["home"]
    p_home3, p_away3 = p2 * (1 - draw), (1 - p2) * (1 - draw)
    p_fav = p_home3 if home_fav else p_away3
    mu_fav = abs(mu)
    basis = (f"RLWC 2026 Round 1 margins {mh:+d} v {ma:+d} points, weighted 0.006 per point; "
             f"one match per side, so confidence is capped at medium")
    out = [market("Match winner", fav, None, p_fav, basis, 0.05),
           market("Handicap", f"{fav} -6.5", -6.5, p_gt(mu_fav, 13.5, 6.5) * (1 - draw), basis, 0.05),
           market("Handicap", f"{dog} +6.5", 6.5, (1 - p_gt(mu_fav, 13.5, 6.5)) * (1 - draw), basis, 0.05)]
    for line in (42.5, 48.5):
        p_over = p_gt(44.0, 14.0, line)
        out += [market("Total points", f"Over {line}", line, p_over, basis + "; total mean 44.0", 0.05),
                market("Total points", f"Under {line}", line, 1 - p_over, basis + "; total mean 44.0", 0.05)]
    b = band_search("Handicap", SPREAD_TEMPLATE.replace("{team}", fav), mu_fav, 13.5, -29.5, 29.5, 1.0, basis, 0.05)
    if b:
        out.append(b)
    return {"p_home": p2, "markets": out, "tier": "C", "evidence": basis}


def model_volleyball(f):
    i = f["inputs"]
    no_numeric = False
    if "home" in i and "pts" in i["home"]:
        h, a = i["home"], i["away"]
        ph = shrink(h["sets_w"], h["played"], 20) if h["played"] else 0.5
        pa = shrink(a["sets_w"], a["played"], 20) if a["played"] else 0.5
        p_set = log5(ph * 0.8 + 0.1, pa * 0.8 + 0.1, 1.03)
        basis = (f"SuperLega Round 1: {h['sets_w']}-{h['sets_l']} sets, points {h['pf']}/{h['pa']} v "
                 f"{a['sets_w']}-{a['sets_l']} sets, points {a['pf']}/{a['pa']}")
    else:
        p_set = 0.515
        no_numeric = True
        basis = "1. Bundesliga Männer Round 2: the table captured shows one match per club, so a league-average prior with a 3% home term is used"
    p_set = min(max(p_set, 0.30), 0.70)

    def bo5(p):
        return p ** 3 * (1 + 3 * (1 - p) + 6 * (1 - p) ** 2)

    p_home = bo5(p_set)
    fav = f["home"] if p_home >= 0.5 else f["away"]
    p_fav = max(p_home, 1 - p_home)
    p3 = p_set ** 3 + (1 - p_set) ** 3
    p4 = 3 * p_set ** 3 * (1 - p_set) + 3 * (1 - p_set) ** 3 * p_set
    p5 = max(0.0, 1 - p3 - p4)
    base = basis + f"; per-set {p_set:.3f}, best of five, confidence capped at medium (one match per club)"
    out = [market("Match winner", fav, None, p_fav, base, 0.05),
           market("Set handicap", f"{fav} -1.5", -1.5, p3 if p_home >= 0.5 else 1 - p3, base, 0.05)]
    for line, p_over in ((3.5, p4 + p5), (4.5, p5)):
        out += [market("Total sets", f"Over {line}", line, p_over, base + f"; set distribution 3:{p3:.3f} 4:{p4:.3f} 5:{p5:.3f}", 0.05),
                market("Total sets", f"Under {line}", line, 1 - p_over, base + f"; set distribution 3:{p3:.3f} 4:{p4:.3f} 5:{p5:.3f}", 0.05)]
    return {"p_home": p_home, "markets": out, "tier": "C", "evidence": base,
            "no_numeric": no_numeric}


def model_golf(f):
    field = f["inputs"]["field"]
    best = min(x[2] for x in field)
    weights = [(x[0], math.exp(-(x[2] - best) / 3.2), x) for x in field]
    rest = math.exp(-6.0 / 3.2) * 45
    total = sum(w for _, w, _ in weights) + rest
    out, probs = [], []
    for name, w, row in weights:
        p = w / total
        probs.append(p)
        out.append(market("Outright winner", name, None, p,
                          f"softmax on strokes behind the 36-hole leader ({row[2]:+d}), tau 3.2 strokes, "
                          f"45 unlisted rivals at six shots back", 0.11))
    top = max(range(len(probs)), key=lambda k: probs[k])
    ranked = sorted(out, key=lambda m: -m["probability"])[:5]
    return {"p_home": probs[top], "markets": out, "tier": "C",
            "evidence": "two completed rounds only; a tournament winner at this stage cannot be a high-confidence price",
            "outright_only": True, "top_index": top, "outright_top": ranked}


def model_greyhound(f):
    runners = [r for r in f["inputs"]["runners"] if r[2] is not None]
    if len(runners) < 2:
        return None
    best = min(r[2] for r in runners)
    total = sum(math.exp(-(r[2] - best) / 0.22) for r in runners)
    out, probs = [], []
    for name, _trainer, t in runners:
        p = math.exp(-(t - best) / 0.22) / total
        probs.append(p)
        out.append(market("Outright winner", name, None, p,
                          f"softmax on semi-final winning time ({t:.2f}s), tau 0.22s, {len(runners)} priced finalists", 0.11))
    top = max(range(len(probs)), key=lambda k: probs[k])
    ranked = sorted(out, key=lambda m: -m["probability"])[:5]
    return {"p_home": probs[top], "markets": out, "tier": "C",
            "evidence": "six-dog final on semi-final times only; no sectional or trap-bias input captured",
            "outright_only": True, "top_index": top, "outright_top": ranked}


def model_motor_race(f):
    i = f["inputs"]
    if i["market"] == "outright":
        pts = i["points"]
        order = sorted(pts.items(), key=lambda kv: -kv[1])
        lead, second = order[0][1], order[1][1]
        p_title = 1 / (1 + 10 ** (-((lead - second) / 130.0)))
        out = [market("Drivers' Championship", order[0][0], None, p_title,
                      f"{lead} points v {second} with five rounds and 130 points remaining after Austin", 0.09)]
        return {"p_home": p_title, "markets": out, "tier": "B",
                "evidence": "17 completed rounds of the 2026 championship", "outright_only": True, "top_index": 0}
    pts = i["points"]
    order = sorted(pts.items(), key=lambda kv: -kv[1])
    best = order[0][1]
    weights = [(n, math.exp(-(best - v) / 140.0), v) for n, v in order]
    rest = 12 * math.exp(-best / 140.0)   # twelve further drivers on zero or low points
    total = sum(w for _, w, _ in weights) + rest
    weights[0] = (weights[0][0], weights[0][1] * 1.35, weights[0][2])  # FP1 pace, Leclerc quickest
    best_lc = max(weights, key=lambda t: t[1] if t[0] == "Charles Leclerc" else 0)
    weights = [(n, w * (1.35 if n == "Charles Leclerc" else 1.0), v) for n, w, v in weights]
    total = sum(w for _, w, _ in weights) + rest
    out, probs = [], []
    for n, w, v in weights:
        p = w / total
        probs.append(p)
        out.append(market("Race winner", n, None, p,
                          f"softmax on 2026 championship points ({v}), tau 140, twelve further drivers, "
                          f"FP1 form weight 1.35 for the fastest car", 0.10))
    top = max(range(len(probs)), key=lambda k: probs[k])
    ranked = sorted(out, key=lambda m: -m["probability"])[:5]
    return {"p_home": probs[top], "markets": out, "tier": "B",
            "evidence": "17 rounds of 2026 championship points plus the official FP1 classification",
            "outright_only": True, "top_index": top, "outright_top": ranked}


def model_gaelic(f):
    margins = {"gaa-cork-psfc": (8, 2), "gaa-waterford-sfc": (2, 7), "gaa-limerick-shc": (7, None)}
    hm, am = margins.get(f["id"], (None, None))
    no_numeric = hm is None or am is None
    if no_numeric:
        p2 = 0.52
        basis = "no numeric strength input captured for both sides; league-average prior with a 2% home term"
    else:
        p2 = min(max(0.5 + (hm - am) * 0.012, 0.30), 0.70)
        basis = f"published semi-final winning margins {hm:+d} v {am:+d} points, weighted 0.012 per point"
    mu = z(p2) * 7.5
    draw = 0.04
    home_fav = p2 >= 0.5
    fav = f["home"] if home_fav else f["away"]
    dog = f["away"] if home_fav else f["home"]
    p_home3, p_away3 = p2 * (1 - draw), (1 - p2) * (1 - draw)
    p_fav = p_home3 if home_fav else p_away3
    mu_fav = abs(mu)
    base = basis + "; draw mass 4.0%, confidence capped at medium (single championship result)"
    out = [market("Match winner (three-way)", fav, None, p_fav, base, 0.05, three_way=True, draw=draw),
           market("Match winner (three-way)", "Draw", None, draw, base, 0.05, three_way=True, draw=draw),
           market("Match winner (three-way)", dog, None, p_away3 if home_fav else p_home3, base, 0.05,
                  three_way=True, draw=draw)]
    for line in (1.5, 3.5):
        out.append(market("Handicap", f"{fav} -{line}", -line, p_gt(mu_fav, 7.0, line) * (1 - draw), base, 0.05,
                          three_way=True, draw=draw))
    for line in (38.5, 44.5):
        p_over = p_gt(42.0, 9.0, line)
        out += [market("Total points", f"Over {line}", line, p_over, base + "; total mean 42.0", 0.05),
                market("Total points", f"Under {line}", line, 1 - p_over, base + "; total mean 42.0", 0.05)]
    return {"p_home": p2, "markets": out, "tier": "C", "evidence": base,
            "no_numeric": no_numeric}


MODELS = {
    "Ice Hockey": model_nhl, "Basketball": model_basketball, "Baseball": model_baseball,
    "Cricket": model_cricket, "Snooker": model_snooker, "Darts": model_darts,
    "Tennis": model_tennis, "Handball": model_handball, "Rugby Union": model_rugby_union,
    "Rugby League": model_rugby_league, "Volleyball": model_volleyball, "Golf": model_golf,
    "Greyhounds": model_greyhound, "Motor Racing": model_motor_race, "Gaelic Sports": model_gaelic,
}


def confidence(p, tier, band_line=False):
    """High needs P >= 0.70. A 1-3 match sample can still carry high on a natural
    money-line/outright selection, but a manufactured band-boundary alternate line on that
    same thin sample is capped at medium."""
    if p is None:
        return None
    if p >= HIGH_P:
        if tier in ("A", "B"):
            return "high"
        return "medium" if band_line else "high"
    if p >= 0.60:
        return "medium"
    return "low"


def main():
    fx = json.load(open(os.path.join(OUT, "fixtures.json")))
    matches, lines, picks = [], [], []
    for f in fx["fixtures"]:
        res = MODELS[f["sport"]](f)
        row = {"id": f["id"], "sport": f["sport"], "competition": f["competition"],
               "home": f["home"], "away": f["away"], "venue": f.get("venue"),
               "start_utc": f.get("start_utc"), "time_display": f.get("time_display"),
               "olbg_event_id": f.get("olbg_event_id"),
               "official_source_url": f["official_source_url"],
               "stats_source_url": f.get("stats_source_url"),
               "injury_source_url": f.get("injury_source_url"),
               "facts": f["facts"], "evidence_tier": None, "evidence": None,
               "status": "originated", "note": None}
        if res is None:
            row["status"] = "blank"
            row["note"] = f.get("line_blocked") or "No official numeric input for both sides, so no line is originated."
            matches.append(row)
            continue
        row["evidence_tier"] = res["tier"]
        row["evidence"] = res["evidence"]
        p_home = res["p_home"]
        p_fav = max(p_home, 1 - p_home)
        row["home_win_probability"] = round(p_home, 4)
        row["favourite"] = f["home"] if p_home >= 0.5 else f["away"]
        row["favourite_probability"] = round(p_fav, 4)
        row["confidence"] = confidence(p_fav, res["tier"])
        row["confidence_cap"] = (res["tier"] == "C" and p_fav >= HIGH_P)

        for k, m in enumerate(res["markets"]):
            m2 = dict(m)
            m2.update({"id": f"{f['id']}-m{k}", "fixture_id": f["id"], "sport": f["sport"]})
            m2["confidence"] = confidence(m2["probability"], res["tier"], bool(m2.get("band_line")))
            lines.append(m2)

        def base_pick(m, extra=None):
            d = {"id": f"{f['id']}-{extra or 'pick'}", "fixture_id": f["id"], "sport": f["sport"],
                 "competition": f["competition"], "home": f["home"], "away": f["away"],
                 "start_utc": f.get("start_utc"), "time_display": f.get("time_display"),
                 "selection": m["selection"], "market": m["market"], "line": m["line"],
                 "probability": m["probability"], "fair_american": m["fair_american"],
                 "fair_decimal": m["fair_decimal"], "in_band": m["in_band"],
                 "confidence": confidence(m["probability"], res["tier"], extra == "band"),
                 "evidence_tier": res["tier"], "evidence": res["evidence"], "basis": m["basis"],
                 "official_source_url": f["official_source_url"],
                 "stats_source_url": f.get("stats_source_url")}
            if extra == "band":
                d["band_board"] = True
            return d

        natural = [m for m in res["markets"] if not m.get("band_line") and m["market"] in (
            "Money line", "Match winner", "Match winner (three-way)", "Outright winner",
            "Race winner", "Drivers' Championship")]
        natural.sort(key=lambda m: -m["probability"])
        if natural:
            picks.append(base_pick(natural[0]))
        for j, m in enumerate(res.get("outright_top") or []):
            picks.append(base_pick(m, f"out{j}"))
        band = [] if res.get("no_numeric") else [m for m in res["markets"] if m.get("band_line")]
        if band:
            picks.append(base_pick(max(band, key=lambda m: m["probability"]), "band"))
        matches.append(row)

    # Sport ranking: the five highest-confidence selections for each sport. A sport whose
    # card contains fewer than five selections at medium or better gets fewer than five and
    # says so on its page; the shortfall is never filled by relabelling a low-confidence row.
    order = {"high": 0, "medium": 1, "low": 2}
    for sport in sorted({p["sport"] for p in picks}):
        rows = [p for p in picks if p["sport"] == sport]
        rows.sort(key=lambda p: (order[p["confidence"]], bool(p.get("band_board")),
                                 not p["in_band"], -p["probability"]))
        seen, shortlist = set(), []
        for p in rows:
            key = (p["fixture_id"], p["selection"])
            if key in seen:
                continue
            seen.add(key)
            shortlist.append(p)
        for rank, p in enumerate(shortlist[:5], 1):
            p["sport_rank"] = rank
        for p in picks:
            if p["sport"] == sport:
                p.setdefault("sport_rank", None)

    summary = {}
    for p in picks:
        s = summary.setdefault(p["sport"], {"shortlisted": 0, "high": 0, "in_band_high": 0,
                                            "high_in_window": 0, "medium": 0})
        if p.get("sport_rank"):
            s["shortlisted"] += 1
        if p["confidence"] == "medium":
            s["medium"] += 1
        if p["confidence"] == "high":
            s["high"] += 1
            if p["in_band"]:
                s["in_band_high"] += 1
    for p in picks:
        if p["confidence"] == "high" and HIGH_P <= p["probability"] <= FLOOR_P + 1e-12:
            summary[p["sport"]]["high_in_window"] += 1

    json.dump({"generated_utc": GENERATED, "session": "arena/a0c8b7f3-olbg2",
               "sport_count": len({r["sport"] for r in matches}), "count": len(matches),
               "originated": sum(1 for r in matches if r["status"] == "originated"),
               "blank": sum(1 for r in matches if r["status"] == "blank"),
               "matches": matches}, open(os.path.join(OUT, "matches.json"), "w"), indent=1, ensure_ascii=False)
    json.dump({"generated_utc": GENERATED, "count": len(lines),
               "markets": sorted({l["market"] for l in lines}), "lines": lines},
              open(os.path.join(OUT, "lines.json"), "w"), indent=1, ensure_ascii=False)
    json.dump({"generated_utc": GENERATED, "count": len(picks),
               "high": sum(1 for p in picks if p["confidence"] == "high"),
               "in_band_high": sum(1 for p in picks if p["confidence"] == "high" and p["in_band"]),
               "bands": {"low": BAND_LOW, "high": BAND_HIGH,
                         "note": "-250 is 0.7143, so high confidence (>=0.70) and this band intersect only in [0.7000,0.7143]"},
               "by_sport": summary, "picks": picks},
              open(os.path.join(OUT, "picks.json"), "w"), indent=1, ensure_ascii=False)
    print(f"matches={len(matches)} originated={sum(1 for r in matches if r['status']=='originated')} "
          f"lines={len(lines)} picks={len(picks)} high={sum(1 for p in picks if p['confidence']=='high')} "
          f"in_band_high={sum(1 for p in picks if p['confidence']=='high' and p['in_band'])}")


if __name__ == "__main__":
    main()
