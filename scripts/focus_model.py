"""Focus desk model. Fair prices only: decimal=1/p (2dp), American from rounded decimal.
High gate: p>=0.7000 AND fair American in [-250,+10000] (decimal 1.40..101.00).
No bookmaker price is read. Adapted from the vanguard Poisson/normal/logistic engine."""
import json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "focus"
INP = json.loads((DATA / "inputs.json").read_text())
HIGH_MIN, HIGH_MAX = 0.7000, 5.0 / 7.0

def american(dec):
    return int(round((dec - 1) * 100)) if dec >= 2.0 else int(round(-100 / (dec - 1)))

def price(p):
    p = round(min(max(p, 0.0001), 0.9999), 4)
    dec = max(round(1 / p + 1e-12, 2), 1.01)
    return {"p": p, "decimal": dec, "american": american(dec)}

def norm_cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def pois(k, mu): return math.exp(-mu) * mu ** k / math.factorial(k)
def grid(la, lb, n):
    pa = [pois(i, la) for i in range(n + 1)]; pb = [pois(i, lb) for i in range(n + 1)]
    sa, sb = sum(pa), sum(pb)
    return [(i, j, pa[i] / sa * pb[j] / sb) for i in range(n + 1) for j in range(n + 1)]

def market_poisson(home, away, p, cap):
    lg, k = p["lg"], p["shrink"]
    wh, wa = home["gp"] / (home["gp"] + k), away["gp"] / (away["gp"] + k)
    la = lg * (1 + wh * (home["gf"] / home["gp"] / lg - 1)) * (1 + wa * (away["ga"] / away["gp"] / lg - 1)) + p["home"] / 2
    lb = lg * (1 + wa * (away["gf"] / away["gp"] / lg - 1)) * (1 + wh * (home["ga"] / home["gp"] / lg - 1)) - p["home"] / 2
    la, lb = max(la, 0.05), max(lb, 0.05)
    g = grid(la, lb, cap)
    win = sum(x for i, j, x in g if i > j); draw = sum(x for i, j, x in g if i == j); lose = sum(x for i, j, x in g if i < j)
    if p.get("tie_split"): win += draw / 2; lose += draw / 2; draw = 0.0
    rows = [("match winner", home["name"], price(win)), ("match winner", away["name"], price(lose))]
    if draw > 0.0005: rows.append(("match winner", "Draw", price(draw)))
    for line in p["handicaps"]:
        pw = sum(x for i, j, x in g if i - j > line)
        rows.append(("handicap", f"{home['name']} {line:+g}", price(pw)))
        rows.append(("handicap", f"{away['name']} {-line:+g}", price(1 - pw)))
    base = la + lb
    for off in p["totals"]:
        t = round((base + off) * 2) / 2
        over = sum(x for i, j, x in g if i + j > t)
        rows.append(("match total", f"Over {t:g}", price(over)))
        rows.append(("match total", f"Under {t:g}", price(1 - over)))
    return rows, {"mu_home": round(la, 4), "mu_away": round(lb, 4)}

def market_normal(home, away, p):
    sd = p["sd"]
    mu = (home["gf"] - home["ga"]) / home["gp"] - (away["gf"] - away["ga"]) / away["gp"] + p.get("home", 0.0)
    band = p.get("draw_band", 0.0)
    ph = 1 - norm_cdf((band - mu) / sd); pl = norm_cdf((-band - mu) / sd); pd = max(0.0, 1 - ph - pl)
    rows = [("match winner", home["name"], price(ph)), ("match winner", away["name"], price(pl))]
    if pd > 0.0005: rows.append(("match winner", "Draw", price(pd)))
    for line in p["handicaps"]:
        cov = 1 - norm_cdf((line - mu) / sd)
        rows.append(("handicap", f"{home['name']} {line:+g}", price(cov)))
        rows.append(("handicap", f"{away['name']} {-line:+g}", price(1 - cov)))
    tot_mu = 0.5 * ((home["gf"] + home["ga"]) / home["gp"] + (away["gf"] + away["ga"]) / away["gp"])
    for off in p["totals"]:
        t = round((tot_mu + off) * 2) / 2
        over = 1 - norm_cdf((t - tot_mu) / p["total_sd"])
        rows.append(("match total", f"Over {t:g}", price(over)))
        rows.append(("match total", f"Under {t:g}", price(1 - over)))
    return rows, {"mu_margin": round(mu, 4), "mu_total": round(tot_mu, 4)}

def market_logistic(home, away, p):
    diff = home["strength"] - away["strength"]
    ph = 1 / (1 + 10 ** (-diff / p["scale"]))
    rows = [("match winner", home["name"], price(ph)), ("match winner", away["name"], price(1 - ph))]
    # handicap/total proxies for logistic sports: set handicap (volleyball/handball style) expressed as winner with adjusted scale
    return rows, {"strength_diff": round(diff, 4)}

SPORT_MARKET = {
    "ice-hockey": dict(kind="poisson", lg=3.0784, shrink=8.0, home=0.10, tie_split=True, handicaps=[x/2 for x in range(-6,13,2)], totals=[x/2 for x in range(-6,7)], cap=15),
    "baseball": dict(kind="poisson", lg=4.4811, shrink=20.0, home=0.12, tie_split=True, handicaps=[x/2 for x in range(-4,9,2)], totals=[x/2 for x in range(-8,9)], cap=25),
    "handball": dict(kind="poisson", lg=31.8273, shrink=3.0, home=0.40, tie_split=False, handicaps=[x/2 for x in range(-14,15,2)], totals=[x/2 for x in range(-10,11)], cap=80),
    "basketball": dict(kind="normal", sd=11.0, total_sd=15.0, home=3.0, handicaps=[x/2 for x in range(-24,25,2)], totals=[x/2 for x in range(-16,17)]),
    "rugby-union": dict(kind="normal", sd=13.0, total_sd=16.0, home=3.0, draw_band=1.0, handicaps=[x/2 for x in range(-24,25,2)], totals=[x/2 for x in range(-20,21)]),
    "volleyball": dict(kind="logistic", scale=60.0),
    "rugby-league": dict(kind="logistic", scale=30.0),
    "cricket": dict(kind="logistic", scale=40.0), "tennis": dict(kind="logistic", scale=55.0),
    "snooker": dict(kind="logistic", scale=40.0), "darts": dict(kind="logistic", scale=25.0),
    "gaelic-football": dict(kind="logistic", scale=45.0),
}

def main():
    matches, lines, flags = [], [], []
    for f in INP["fixtures"]:
        fid, sport = f["sid"], f["sport"]
        home = dict(f["h"], name=f["home"]); away = dict(f["a"], name=f["away"])
        row = {"id": fid, "sport": sport, "competition": f["comp"], "start_utc": f["start"], "home": f["home"], "away": f["away"], "source_url": f["src"], "basis": f["basis"], "facts": f["facts"], "prices": [], "in_band": []}
        if f.get("contenders"):
            tot = sum(w for _, w in f["contenders"])
            for name, w in f["contenders"]: row["prices"].append({"market": "outright winner", "selection": name, **price(w / tot)})
            row["confidence"] = "low"
            flags.append({"id": f"FO-{fid}", "sport": sport, "kind": "partial outright", "text": "Outright prices only the contenders named in the official table; rest of field not priced.", "source": f["src"]})
        elif sport not in SPORT_MARKET or home.get("strength") is None and SPORT_MARKET.get(sport, {}).get("kind") == "logistic":
            row["confidence"] = "blank"
            flags.append({"id": f"FO-{fid}", "sport": sport, "kind": "blank — no official numeric input", "text": f["facts"], "source": f["src"]})
        else:
            mk = SPORT_MARKET[sport]
            if sport == "basketball" and "net" in home:
                # preseason net-rating proxy: winner only, no handicap/total originated
                ph = 1/(1+math.exp(-(((home["gf"]-home["ga"])/home["gp"])-((away["gf"]-away["ga"])/away["gp"])+3.0)/11.0))
                prices, extra = [("match winner", home["name"], price(ph)), ("match winner", away["name"], price(1-ph))], {"net_proxy": True}
                flags.append({"id": f"FO-net-{fid}", "sport": sport, "kind": "thin input", "text": "NBA priced from preseason net rating only; handicap and total left unoriginated for this fixture.", "source": f["src"]})
            elif mk["kind"] == "poisson": prices, extra = market_poisson(home, away, mk, mk["cap"])
            elif mk["kind"] == "normal": prices, extra = market_normal(home, away, mk)
            else: prices, extra = market_logistic(home, away, mk)
            row["model"] = extra
            # keep winner all + nearest-to-70.71% 4 per handicap/total family
            fam = {}
            kept = []
            for market, sel, pr in prices:
                if market == "match winner": kept.append((market, sel, pr))
                else: fam.setdefault(market, []).append((market, sel, pr))
            for market, items in fam.items():
                items.sort(key=lambda x: abs(x[2]["p"] - 0.7071)); kept.extend(items[:4])
            for market, sel, pr in kept:
                pr = {"market": market, "selection": sel, **pr}
                if HIGH_MIN <= pr["p"] <= HIGH_MAX:
                    pr["in_band"] = True; row["in_band"].append(pr)
                row["prices"].append(pr)
            best = max([x["p"] for x in row["in_band"]] or [x["p"] for x in row["prices"] if x["market"] == "match winner"] or [0])
            row["confidence"] = "high" if row["in_band"] else ("medium" if best >= 0.60 else "low")
        matches.append(row)
        for pr in row["prices"]: lines.append({"fixture": fid, "sport": sport, **pr})
    # sport shortfall flags
    labels = INP["labels"]
    for s in INP["sports"]:
        ms = [m for m in matches if m["sport"] == s]
        highs = [m for m in ms if m["in_band"]]
        if len(highs) < 5:
            flags.append({"id": f"FO-short-{s}", "sport": s, "kind": "top-5 shortfall", "text": f"{labels[s]}: {len(highs)} fixture(s) with an in-band high selection from captured official inputs — fewer than the five-per-sport aim. No price was invented to fill the gap.", "source": ms[0]["source_url"] if ms else "https://www.olbg.com/betting-tips"})
    (DATA / "matches.json").write_text(json.dumps({"counts": {"fixtures": len(matches), "lines": len(lines), "in_band": sum(len(m["in_band"]) for m in matches)}, "matches": matches}, indent=1))
    (DATA / "lines.json").write_text(json.dumps({"count": len(lines), "rows": lines}, indent=1))
    (DATA / "flagged.json").write_text(json.dumps({"count": len(flags), "flags": flags}, indent=1))
    print(f"focus_model: {len(matches)} fixtures, {len(lines)} lines, {sum(len(m['in_band']) for m in matches)} in-band, {len(flags)} flags")

if __name__ == "__main__": main()
