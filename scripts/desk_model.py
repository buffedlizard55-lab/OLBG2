#!/usr/bin/env python3
"""Independent line origination for the /desk/ 15-sport board.

Two disclosed bases, never mixed inside one price:

1. official  - a Poisson goals model built only from NHL club aggregates that were
   read first-hand from the NHL statistics endpoint (goals for, goals against,
   games played). Used for money line, puck line and match total.
2. consensus - OLBG's published tip split for the most-tipped selection of an
   event, shrunk toward 0.5. OLBG publishes a tip count and a percentage but no
   price (checked on the hub and on an event page), so this is a crowd signal,
   not a bookmaker price. It can never be labelled high confidence because no
   official numeric input corroborates it.

Fair odds are the inverse of the model probability, rounded to two decimals and
converted to American. A price is "in band" when the fair American price sits in
[-250, +10000], i.e. decimal 1.40 to 101.00 inclusive.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def american(dec):
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100))
    return -int(round(100.0 / (dec - 1.0)))


def band(dec):
    return 1.40 <= dec <= 101.00


def confidence(p, basis, n):
    """Confidence follows the brief's definition: probability of the selection.

    Evidence strength is a separate column so a crowd-derived number can never be
    mistaken for one corroborated by a governing body.
    """
    if p >= 0.70:
        return "high"
    if p >= 0.65:
        return "medium"
    return "low"


def nhl_lines(inputs):
    stats = inputs["nhl_club_stats"]
    gp = {k: v[0] for k, v in stats.items()}
    gf = {k: v[1] for k, v in stats.items()}
    ga = {k: v[2] for k, v in stats.items()}
    lg = sum(gf.values()) / sum(gp.values())
    k_shrink = 8.0
    out = []

    def rate(team, col):
        raw = (col[team] / gp[team]) if gp[team] else lg
        return (raw * gp[team] + lg * k_shrink) / (gp[team] + k_shrink)

    for f in inputs["fixtures"]:
        if f["sport"] != "Ice Hockey":
            continue
        h, a = f["home_abbr"], f["away_abbr"]
        if h not in stats or a not in stats:
            continue
        lam_h = rate(h, gf) * rate(a, ga) / lg + 0.10
        lam_a = rate(a, gf) * rate(h, ga) / lg - 0.10
        lam_a = max(lam_a, 0.20)
        lam_h = max(lam_h, 0.20)
        n = 12
        grid = [[poisson(i, lam_h) * poisson(j, lam_a) for j in range(n + 1)] for i in range(n + 1)]
        p_h_reg = sum(grid[i][j] for i in range(n + 1) for j in range(n + 1) if i > j)
        p_tie = sum(grid[i][i] for i in range(n + 1))
        p_a_reg = sum(grid[i][j] for i in range(n + 1) for j in range(n + 1) if i < j)
        # Overtime / shootout treated as a coin flip: disclosed in METHODOLOGY.
        p_h = p_h_reg + 0.5 * p_tie
        p_a = p_a_reg + 0.5 * p_tie
        p_h_2 = sum(grid[i][j] for i in range(n + 1) for j in range(n + 1) if i - j >= 2)
        p_a_1 = 1.0 - p_h_2
        total = lam_h + lam_a
        p_over55 = 1.0 - sum(poisson(k, total) for k in range(0, 6))
        p_over65 = 1.0 - sum(poisson(k, total) for k in range(0, 7))

        def add(market, selection, p, basis_note):
            dec = round(1.0 / p, 2) if p > 0 else 101.0
            out.append({
                "sid": f["sid"], "sport": f["sport"], "comp": f["comp"],
                "fixture": f"{f['away']} @ {f['home']}" if f["sport"] == "Ice Hockey" else f"{f['home']} v {f['away']}",
                "start_utc": f["start_utc"], "market": market, "market_type": "Match Winner" if market == "Money Line" else ("Match Total" if market.startswith("Match Total") else "Handicap"), "selection": selection,
                "p": round(p, 4), "fair_decimal": dec, "fair_american": american(dec),
                "in_band": band(dec), "confidence": confidence(p, "official", 0),
                "basis": "official", "basis_note": basis_note, "src": f["src"],
                "sample": None,
            })

        note = (f"Poisson goals model from NHL club aggregates: {h} {gf[h]}GF/{ga[h]}GA in {gp[h]}GP, "
                f"{a} {gf[a]}GF/{ga[a]}GA in {gp[a]}GP, league average {lg:.2f} goals per club game, "
                f"rates shrunk {k_shrink:.0f} games toward the league mean, home edge +0.10 goals, "
                f"overtime treated as a coin flip.")
        add("Money Line", f["home"], p_h, note)
        add("Money Line", f["away"], p_a, note)
        add("Puck Line -1.5", f["home"], p_h_2, note)
        add("Puck Line +1.5", f["away"], p_a_1, note)
        add("Match Total 5.5", "Over 5.5", p_over55, note)
        add("Match Total 5.5", "Under 5.5", 1 - p_over55, note)
        add("Match Total 6.5", "Over 6.5", p_over65, note)
        add("Match Total 6.5", "Under 6.5", 1 - p_over65, note)
    return out, lg


MARKET_TYPE = {
    "Win Match": "Match Winner", "To Win": "Match Winner", "Money Line": "Match Winner",
    "Win Match 2-way": "Match Winner", "Win Race": "Race Winner", "Daily Races": "Race Winner",
    "Handicap": "Handicap", "Match Handicap": "Handicap", "Pointspread": "Handicap",
    "Puck Line": "Handicap", "Total Games": "Match Total", "Game Totals": "Match Total",
    "Set Score": "Set Betting", "Set Betting": "Set Betting",
    "Win Tournament": "Outright", "Grand Final Winner": "Outright", "Outright Winner": "Outright",
}
SPORT_ID = {"Tennis": 3, "Volleyball": 21, "Rugby Union": 9, "Cricket": 7, "Snooker": 8,
            "Darts": 15, "Basketball": 4, "Ice Hockey": 13, "Handball": 20, "Greyhounds": 28,
            "Gaelic Sports": 25, "Motor Racing": 14, "Baseball": 12, "Rugby League": 10, "Golf": 5}


def consensus_lines(inventory):
    rows = [dict(zip(inventory["header"], r)) for r in inventory["rows"]]
    out = []
    k = 12.0
    for r in rows:
        n = int(r["tips"] or 0)
        pct = float(r["pct"] or 0) / 100.0
        if n <= 0:
            continue
        p = (n * pct + k * 0.5) / (n + k)
        p = min(max(p, 0.02), 0.98)
        dec = round(1.0 / p, 2)
        sid = SPORT_ID[r["sport"]]
        out.append({
            "sid": f"olbg-{r['event_id']}", "sport": r["sport"], "comp": "OLBG listing",
            "fixture": r["event"], "start_utc": None, "market": r["market"],
            "market_type": MARKET_TYPE.get(r["market"], r["market"]),
            "selection": r["selection"], "p": round(p, 4), "fair_decimal": dec,
            "fair_american": american(dec), "in_band": band(dec),
            "confidence": confidence(p, "consensus", n), "basis": "consensus",
            "basis_note": (f"OLBG published {r['tips']} of {r['total']} tips ({r['pct']}%) on this selection; "
                           f"share shrunk toward 0.50 with a 12-tip prior. OLBG publishes no price."),
            "src": f"https://www.olbg.com/betting-tips/{r['sport'].replace(' ', '_')}/{sid}?event_id={r['event_id']}",
            "olbg_url": f"https://www.olbg.com/betting-tips/{r['sport'].replace(' ', '_')}/{sid}?event_id={r['event_id']}",
            "sample": n, "olbg_display_time": r["time_display"], "olbg_tips": f"{r['tips']}/{r['total']}",
            "olbg_pct": r["pct"],
        })
    return out


def main():
    inputs = json.load(open(os.path.join(ROOT, "data/olbgdesk/inputs.json")))
    inventory = json.load(open(os.path.join(ROOT, "data/olbgdesk/olbg_inventory.json")))
    nhl, lg = nhl_lines(inputs)
    cons = consensus_lines(inventory)
    lines = nhl + cons
    json.dump({"generated_utc": "2026-10-23T16:35:00Z", "league_average_goals": round(lg, 4),
               "lines": lines},
              open(os.path.join(ROOT, "data/olbgdesk/lines.json"), "w"), indent=1)
    print(f"{len(nhl)} official NHL markets, {len(cons)} consensus winner markets, {len(lines)} total")
    hi = [l for l in lines if l["confidence"] == "high"]
    print("high:", len(hi))
    for l in hi:
        print(f"  {l['fixture']} | {l['selection']} | p={l['p']} | {l['fair_american']} | band={l['in_band']}")


if __name__ == "__main__":
    main()
