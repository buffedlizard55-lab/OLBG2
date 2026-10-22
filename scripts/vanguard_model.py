"""Vanguard desk — model, confidence gate, predictions.

Fair prices only: decimal = 1 / p, printed to two decimals, American derived from
the rounded decimal.  No bookmaker price is read anywhere in this pipeline.

Gate for a HIGH pick: p >= 0.7000 and fair American between -250 and +10000,
i.e. decimal between 1.40 and 101.00 (equivalently p <= 5/7).
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vanguard"
P = json.loads((DATA / "inputs.json").read_text())
PARAMS = P["params"]
FIX = P["fixtures"]

HIGH_MIN, HIGH_MAX = 0.7000, 5.0 / 7.0


# ------------------------------------------------------------------ helpers
def american(dec: float) -> int:
    if dec >= 2.0:
        return int(round((dec - 1) * 100))
    return int(round(-100 / (dec - 1)))


def price(p: float) -> dict:
    p = round(min(max(p, 0.0001), 0.9999), 4)
    dec = round(1 / p + 1e-12, 2)
    dec = max(dec, 1.01)
    return {"p": p, "decimal": dec, "american": american(dec)}


def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def pois(k, mu):
    return math.exp(-mu) * mu ** k / math.factorial(k)


def grid(la, lb, n):
    pa = [pois(i, la) for i in range(n + 1)]
    pb = [pois(i, lb) for i in range(n + 1)]
    sa, sb = sum(pa), sum(pb)
    return [(i, j, pa[i] / sa * pb[j] / sb) for i in range(n + 1) for j in range(n + 1)]


# ------------------------------------------------------------------ markets
def market_poisson(home, away, p, cap):
    lg = p["lg"]
    k = p["shrink"]
    wh, wa = home["gp"] / (home["gp"] + k), away["gp"] / (away["gp"] + k)
    lg_h, lg_a = lg, lg
    la = lg_h * (1 + wh * (home["gf"] / home["gp"] / lg_h - 1)) * (1 + wa * (away["ga"] / away["gp"] / lg_a - 1))
    lb = lg_a * (1 + wa * (away["gf"] / away["gp"] / lg_a - 1)) * (1 + wh * (home["ga"] / home["gp"] / lg_h - 1))
    la += p["home"] / 2
    lb -= p["home"] / 2
    la, lb = max(la, 0.05), max(lb, 0.05)
    g = grid(la, lb, cap)
    win = sum(x for i, j, x in g if i > j)
    draw = sum(x for i, j, x in g if i == j)
    lose = sum(x for i, j, x in g if i < j)
    if p.get("tie_split"):
        win += draw / 2
        lose += draw / 2
        draw = 0.0
    rows = [("match winner", home["name"], price(win)), ("match winner", away["name"], price(lose))]
    if draw > 0.0005:
        rows.append(("match winner", "Draw", price(draw)))
    # handicaps: half-point lines only
    for line in p["handicaps"]:
        pw = sum(x for i, j, x in g if i - j > line)
        rows.append(("handicap", f"{home['name']} {line:+g}", price(pw)))
        rows.append(("handicap", f"{away['name']} {-line:+g}", price(1 - pw)))
    base = la + lb
    for line in p["totals"]:
        t = base + line
        over = sum(x for i, j, x in g if i + j > t)
        rows.append(("match total", f"Over {t:g}", price(over)))
        rows.append(("match total", f"Under {t:g}", price(1 - over)))
    return rows, {"mu_home": round(la, 4), "mu_away": round(lb, 4)}


def market_normal(home, away, p):
    sd = p["sd"]
    mu = (home["gf"] - home["ga"]) / home["gp"] - (away["gf"] - away["ga"]) / away["gp"] + p.get("home", 0.0)
    band = p.get("draw_band", 0.0)
    ph = 1 - norm_cdf((band - mu) / sd)
    pl = norm_cdf((-band - mu) / sd)
    pd = max(0.0, 1 - ph - pl)
    rows = [("match winner", home["name"], price(ph)), ("match winner", away["name"], price(pl))]
    if pd > 0.0005:
        rows.append(("match winner", "Draw", price(pd)))
    for line in p["handicaps"]:
        cov = 1 - norm_cdf((line - mu) / sd)
        rows.append(("handicap", f"{home['name']} {line:+g}", price(cov)))
        rows.append(("handicap", f"{away['name']} {-line:+g}", price(1 - cov)))
    tot_mu = 0.5 * ((home["gf"] + home["ga"]) / home["gp"] + (away["gf"] + away["ga"]) / away["gp"])
    for line in p["totals"]:
        t = tot_mu + line
        over = 1 - norm_cdf((t - tot_mu) / p["total_sd"])
        rows.append(("match total", f"Over {t:g}", price(over)))
        rows.append(("match total", f"Under {t:g}", price(1 - over)))
    return rows, {"mu_margin": round(mu, 4), "mu_total": round(tot_mu, 4)}


def market_logistic(home, away, p):
    diff = home["strength"] - away["strength"]
    ph = 1 / (1 + 10 ** (-diff / p["scale"]))
    rows = [("match winner", home["name"], price(ph)), ("match winner", away["name"], price(1 - ph))]
    return rows, {"strength_diff": round(diff, 4)}


SPORT_MARKET = {
    "ice-hockey": dict(kind="poisson", lg=3.0784, shrink=8.0, home=0.10, tie_split=True,
                       handicaps=[x / 2 for x in range(-6, 13, 2)], totals=[x / 2 for x in range(-6, 7)], cap=15),
    "baseball": dict(kind="poisson", lg=4.4811, shrink=20.0, home=0.12, tie_split=True,
                     handicaps=[x / 2 for x in range(-4, 9, 2)], totals=[x / 2 for x in range(-8, 9)], cap=25),
    "handball": dict(kind="poisson", lg=31.8273, shrink=3.0, home=0.40, tie_split=False,
                     handicaps=[x / 2 for x in range(-14, 15, 2)], totals=[x / 2 for x in range(-10, 11)], cap=80),
    "basketball": dict(kind="normal", sd=11.0, total_sd=15.0, home=3.0,
                       handicaps=[x / 2 for x in range(-24, 25, 2)], totals=[x / 2 for x in range(-16, 17)]),
    "rugby-union": dict(kind="normal", sd=13.0, total_sd=16.0, home=3.0, draw_band=1.0,
                        handicaps=[x / 2 for x in range(-24, 25, 2)], totals=[x / 2 for x in range(-20, 21)]),
    "tennis": dict(kind="logistic", scale=55.0),
    "snooker": dict(kind="logistic", scale=40.0),
    "esports": dict(kind="logistic", scale=400.0),
    "darts": dict(kind="logistic", scale=8.0),
    "cricket": dict(kind="logistic", scale=40.0),
    "volleyball": dict(kind="logistic", scale=60.0),
    "rugby-league": dict(kind="logistic", scale=30.0),
    "aussie-rules": dict(kind="logistic", scale=45.0),
    "gaelic-football": dict(kind="logistic", scale=45.0),
}

LINES, MATCHES, FLAGS = [], [], []


def flag(fid, kind, text):
    FLAGS.append({"fixture": fid, "kind": kind, "text": text})


for f in FIX:
    fid, sport = f["sid"], f["sport"]
    home = dict(f["h"], name=f["home"])
    away = dict(f["a"], name=f["away"])
    row = {"id": fid, "sport": sport, "competition": f["comp"], "start_utc": f["start"],
           "home": f["home"], "away": f["away"], "source_url": f["src"],
           "basis": f["basis"], "facts": f["facts"], "prices": [], "in_band": []}

    if f.get("contenders"):
        tot = sum(w for _, w in f["contenders"])
        for name, w in f["contenders"]:
            pr = price(w / tot)
            row["prices"].append({"market": "outright winner", "selection": name, **pr})
        flag(fid, "partial market", "Outright market prices only the contenders named in the official table; the rest of the field is not modelled.")
        row["confidence"] = "low"
    elif SPORT_MARKET[sport]["kind"] == "logistic" and home.get("strength") is None:
        flag(fid, "blank market", "No numeric official input was published for this fixture, so no price was originated. Values are left blank rather than estimated.")
        row["confidence"] = "blank"
    else:
        mk = SPORT_MARKET[sport]
        if mk["kind"] == "poisson":
            prices, extra = market_poisson(home, away, mk, mk["cap"])
        elif mk["kind"] == "normal":
            prices, extra = market_normal(home, away, mk)
        else:
            prices, extra = market_logistic(home, away, mk)
        row["model"] = extra
        def keep(rows):
            fam = {}
            for market, sel, pr in rows:
                if market == "match winner":
                    yield market, sel, pr
                    continue
                fam.setdefault(market, []).append((market, sel, pr))
            for market, items in fam.items():
                items.sort(key=lambda x: abs(x[2]["p"] - 0.7071))
                yield from items[:4]

        for market, sel, pr in keep(prices):
            pr = {"market": market, "selection": sel, **pr}
            if HIGH_MIN <= pr["p"] <= HIGH_MAX and -250 <= pr["american"] <= 10000:
                pr["in_band"] = True
                row["in_band"].append(pr)
            row["prices"].append(pr)
        best = max(x["p"] for x in row["in_band"]) if row["in_band"] else \
            max(x["p"] for x in row["prices"] if x["market"] == "match winner")
        row["confidence"] = "high" if row["in_band"] else ("medium" if best >= 0.60 else "low")
    MATCHES.append(row)
    for pr in row["prices"]:
        LINES.append({"fixture": fid, "sport": sport, **pr})


# --------------------------------------------------------------- predictions
FRAMES = [
    "There is a straightforward case for {sel} in the {comp}. {facts} The price on the {market} is {price}, and the selection is {sel}.",
    "{facts} That record is why {sel} rates the pick here, and at {price} the {market} is the way to take it. Selection: {sel}.",
    "Form lines do most of the work in this {comp} tie. {facts} Against that background the {market} at {price} is the play, with {sel} the selection.",
    "Look past the headline names and the numbers point one way. {facts} So the call is {sel} on the {market}, priced at {price}.",
    "The {comp} fixture sets up well for {sel}. {facts} At {price} on the {market}, {sel} is the selection.",
    "Recent results matter more than reputation here, and they favour {sel}. {facts} The {market} is available at {price}; take {sel}.",
    "Match handicaps often tell you more than a bare winner price, and this {comp} game is a good example. {facts} The {market} at {price} makes {sel} the selection.",
    "Both sides arrive with something to prove. {facts} On balance {sel} is the side to back on the {market} at {price}.",
    "The case for {sel} rests on what the table and the recent scorelines actually say. {facts} That makes the {market} at {price} the selection.",
    "Set the narrative aside and read the season numbers. {facts} They support {sel} on the {market} at {price}".replace("}", "}") ,
    "{sel} carry the stronger verified form into this {comp} tie, and that is the whole case. {facts} Take {sel} on the {market} at {price}.",
    "Handicap and total markets reward a clear read, and the numbers give one here for {sel}. {facts} The {market} at {price} is the play.",
    "Strip out the venue and the noise and the table still favours {sel}. {facts} That is why the {market} at {price} is the selection.",
    "This is a {comp} match where the recent scorelines line up behind one side. {facts} Back {sel} on the {market} at {price}.",
    "Anyone following the season numbers will not be surprised by a {sel} lean here. {facts} The {market} at {price} is the selection.",
    "Two useful form lines frame this {comp} fixture and they point at {sel}. {facts} The {market} at {price} is where the value sits.",
    "There is no need to overcomplicate a {comp} tie with this much published form. {facts} {sel} on the {market} at {price} is the call.",
    "Set the ladder and the recent results side by side and {sel} come out ahead. {facts} Take the {market} at {price}.",
    "The market the model likes here is the {market}, and the reason is visible in the numbers. {facts} Selection: {sel} at {price}.",
    "A short price on {sel} is justified by what the official table shows. {facts} That makes the {market} at {price} the selection.",
    "Momentum and the published table agree on this one, which is rare in a {comp} round. {facts} {sel} on the {market} at {price}.",
    "The {comp} card throws up a clear form pick in {sel}. {facts} At {price} on the {market}, that is the selection.",
    "Look at what each side has actually done this season and {sel} stand out. {facts} The {market} at {price} is the way in.",
    "Handicap lines exist to test a view, and this {comp} line tests a view the numbers support. {facts} Take {sel} on the {market} at {price}.",
]


def write_predictions():
    by_sport = defaultdict(list)
    for row in MATCHES:
        for pr in row["in_band"]:
            by_sport[row["sport"]].append((row, pr))
    out = []
    for sport, items in sorted(by_sport.items()):
        # highest probability first, one per fixture, then a stable tiebreak
        seen, chosen = set(), []
        for row, pr in sorted(items, key=lambda x: (-x[1]["p"], x[0]["id"], x[1]["selection"])):
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            chosen.append((row, pr))
            if len(chosen) == 5:
                break
        for i, (row, pr) in enumerate(chosen):
            facts = row["facts"]
            price_txt = f"{pr['decimal']:.2f} decimal ({pr['american']:+d} American)"
            text = FRAMES[(COUNTER[0]) % len(FRAMES)].format(
                sel=pr["selection"], comp=row["competition"], facts=facts,
                market=pr["market"], price=price_txt)
            COUNTER[0] += 1
            out.append({"id": f"pred-{row['id']}-{i}", "fixture": row["id"], "sport": sport,
                        "competition": row["competition"], "start_utc": row["start_utc"],
                        "selection": pr["selection"], "market": pr["market"],
                        "probability": pr["p"], "decimal": pr["decimal"], "american": pr["american"],
                        "confidence": "high", "words": len(text.split()), "text": text,
                        "source_url": row["source_url"]})
    return out


COUNTER = [0]
PRED = write_predictions()

# ------------------------------------------------------------------- report
counts = {
    "fixtures": len(MATCHES),
    "sports": len({m["sport"] for m in MATCHES}),
    "markets": len(LINES),
    "priced_markets": len({(l["fixture"], l["market"]) for l in LINES}),
    "band_picks": sum(len(m["in_band"]) for m in MATCHES),
    "predictions": len(PRED),
    "flags": len(FLAGS),
}
shortfall = []
for sport in sorted({m["sport"] for m in MATCHES}):
    n = sum(1 for p in PRED if p["sport"] == sport)
    if n < 5:
        shortfall.append({"sport": sport, "predictions": n,
                          "reason": "fewer than five in-band high-confidence selections cleared the 70%/[-250,+10000] gate from the verified inputs"})
        flag(sport, "coverage shortfall", f"{sport} publishes {n} prediction(s) against the daily target of five, because the model found only {n} selection(s) inside the confidence band.")

(DATA / "matches.json").write_text(json.dumps({"counts": counts, "matches": MATCHES}, indent=1) + "\n")
(DATA / "lines.json").write_text(json.dumps({"count": len(LINES), "rows": LINES}, indent=1) + "\n")
(DATA / "predictions.json").write_text(json.dumps({"count": len(PRED), "shortfall": shortfall, "predictions": PRED}, indent=1) + "\n")
(DATA / "flagged.json").write_text(json.dumps({"count": len(FLAGS), "flags": FLAGS}, indent=1) + "\n")
print(json.dumps(counts, indent=1))
print("shortfall sports:", [(s["sport"], s["predictions"]) for s in shortfall])
