#!/usr/bin/env python3
"""Origination engine for the 15-sport live board.

Reads the first-hand OLBG capture and the official-input blocks, derives one
probability per fixture, converts it to a fair price and an offered price, and
grades confidence and band membership.  Deterministic: no wall clock, no
network, no randomness.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "liveboard"
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
    "Ice Hockey", "Basketball", "Rugby League",
]
# Sports book margin taken on the profit at the offered price.
MARGIN = {
    "Golf": 0.06, "Volleyball": 0.05, "Rugby Union": 0.05, "Cricket": 0.05,
    "Snooker": 0.05, "Darts": 0.04, "Baseball": 0.04, "Gaelic Sports": 0.06,
    "Greyhounds": 0.08, "Tennis": 0.05, "Motor Racing": 0.06, "Handball": 0.06,
    "Ice Hockey": 0.05, "Basketball": 0.04, "Rugby League": 0.06,
}
HIGH, MEDIUM = 0.70, 0.60
MIN_TIPS_FOR_HIGH = 6          # a tip-share row needs a real sample before it can be called high
BAND_LOW, BAND_HIGH = -250, 10000

EUROLEAGUE = {"Zalgiris", "Asvel", "Olympiacos", "Fenerbahce", "Paris", "Valencia"}


def europe(key: str) -> float:
    return 0.0


def american(dec: float) -> int:
    if dec >= 2.0:
        return int(round((dec - 1) * 100))
    return int(round(-100 / (dec - 1)))


def offered_price(p: float, sport: str) -> float:
    fair = 1.0 / p
    m = MARGIN[sport]
    return 1.0 + (fair - 1.0) * (1.0 - m)


def normal(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def parse_teams(event: str):
    if " @ " in event:
        return event.split(" @ ")[0].strip(), event.split(" @ ")[1].strip()
    for sep in (" vs ", " v "):
        if sep in event:
            a, b = event.split(sep, 1)
            return a.strip(), b.strip()
    return None, None


def load(name: str):
    return json.loads((DATA / name).read_text())


def block(inputs, bid):
    return next(b for b in inputs["blocks"] if b["id"] == bid)


# --------------------------------------------------------------------------- models
def mlb_win_prob(team_a, team_b, a_home, m_mil, m_tb):
    """log5 with a small home-field adjustment, from official season records."""
    pa = m_mil if team_a.startswith("MIL") else m_tb
    pb = m_tb if team_a.startswith("MIL") else m_mil
    p = (pa - pa * pb) / (pa + pb - 2 * pa * pb)
    if a_home:
        p += 0.04
    return round(min(max(p, 0.05), 0.95), 4)


def el_rating(row) -> float:
    return (row["pf"] - row["pa"]) / row["gp"]


def el_prob(home_key: str, away_key: str, table) -> float:
    diff = el_rating(table[home_key]) - el_rating(table[away_key]) + 3.0  # three-point home edge
    return round(normal(diff / 12.0), 4)


def snooker_prob(player: str, opponent: str, world, oneyear) -> float:
    money = {r["player"]: r["money"] for r in world}
    money.update({p: v for p, v in {r["player"]: r["money"] for r in oneyear}.items() if p not in money})
    floor = 25000
    a = math.log(max(money.get(player, floor), floor))
    b = math.log(max(money.get(opponent, floor), floor))
    return round(logistic(0.45 * (a - b)), 4)


def urc_prob(home: str, away: str, results) -> float:
    """Round-3 margin carried forward, plus a four-point home edge, over a 26-point scale."""
    margin: dict[str, int] = {}
    for r in results:
        h, a = map(int, r["score"].split("-"))
        margin[r["home"]] = h - a
        margin[r["away"]] = a - h
    alias = {"Zebre Parma": "Zebre Parma", "Lions": "Lions", "Sharks": "Sharks", "Cardiff": "Cardiff"}
    mh = margin.get(alias.get(home, home))
    ma = margin.get(alias.get(away, away))
    if mh is None or ma is None:
        return None
    # a single round is a thin sample, so the margin is shrunk hard towards the mean
    return round(normal(0.35 * (mh - ma + 4.0) / 26.0), 4)


def build():
    olbg = load("olbg.json")
    inputs = load("inputs.json")
    mil = block(inputs, "MLB-MIL-2026")["values"]
    tb = block(inputs, "MLB-TB-2026")["values"]
    el = block(inputs, "EUROLEAGUE-2026-27")["values"]
    world = block(inputs, "WST-WORLD-RANKING")["values"]
    oneyear = block(inputs, "WST-ONE-YEAR")["values"]
    centuries = {r["player"]: r["centuries"] for r in block(inputs, "WST-CENTURIES")["values"]}
    results = block(inputs, "URC-R3-RESULTS")["values"]

    rows, originated, unlined = [], [], []
    coverage = {}

    for sp in olbg["sports"]:
        sport = sp["sport"]
        keep = 0
        for ev in sp["events"]:
            home, away = parse_teams(ev["event"])
            sel = ev["selection"]
            basis, p, note = "tip-share", None, ""
            tips, total = ev["tips"], ev["total"]
            share = (100.0 * tips / total) if total else None

            # --- official-model fixtures -------------------------------------
            if sport == "Baseball":
                mil_p = mlb_win_prob("MIL Brewers", "TB Rays", True, mil["pct"], tb["pct"])
                p = mil_p if sel.startswith("MIL") else round(1 - mil_p, 4)
                basis = "official-model"
                note = "log5 on season records with a four-point home adjustment"
            elif sport == "Basketball" and ev.get("competition") == "Euroleague":
                key = {"Zalgiris": "ZAL", "Asvel Lyon Villeurbanne": "ASV", "Olympiacos": "OLY",
                       "Fenerbahce": "FBT", "Paris": "PBB", "Valencia": "VBC"}
                if home in key and away in key:
                    p = el_prob(key[home], key[away], el)
                    if sel not in (home,):
                        p = round(1 - p, 4)
                    basis = "official-model"
                    note = "point differential per game from the EuroLeague table, three-point home edge"
            elif sport == "Snooker":
                if away in ("Mark Williams", "Scott Donaldson"):
                    p = snooker_prob(away, home, world, oneyear)
                elif sel in ("Mark Williams", "Scott Donaldson"):
                    p = snooker_prob(sel, home, world, oneyear)
                else:
                    p = snooker_prob(sel, away if sel == home else home, world, oneyear)
                basis = "official-model"
                note = "world and one-year ranking money, log scale, 0.45 coefficient"
            elif sport == "Rugby Union" and ev.get("competition") == "URC" and home and away:
                pr = urc_prob(home, away, results)
                if pr is not None:
                    p = pr if sel == home else round(1 - pr, 4)
                    basis = "official-model"
                    note = "Round 3 winning margin carried forward with a four-point home edge"

            if p is None:
                if not total:
                    unlined.append({"sport": sport, "event": ev["event"], "reason": "no tip sample and no official input"})
                    continue
                p = round((tips + 1) / (total + 2), 4)     # Laplace smoothing
                note = f"OLBG tip share {tips}/{total}, Laplace-smoothed"

            fair = 1.0 / p
            offer = offered_price(p, sport)
            price = american(offer)
            if p >= HIGH and (basis == "official-model" or (total and total >= MIN_TIPS_FOR_HIGH)):
                conf = "high"
            elif p >= MEDIUM:
                conf = "medium"
            else:
                conf = "low"
            in_band = BAND_LOW <= american(fair) <= BAND_HIGH
            rows.append({
                "sport": sport, "event": ev["event"], "competition": ev.get("competition", ""),
                "start_display": ev["start_display"], "market": ev["market"] or "Handicap",
                "selection": sel, "opponent": away if sel == home else home,
                "basis": basis, "note": note,
                "tips": tips, "total": total, "share_pct": share,
                "probability": p, "fair_decimal": round(fair, 3),
                "fair_american": american(fair), "offered_decimal": round(offer, 3),
                "price": price, "confidence": conf, "in_band": in_band,
                "outright": bool(ev.get("outright")), "is_match": home is not None,
                "event_id": ev["id"], "source_url": "https://www.olbg.com" + ev["path"],
                "start_iso": None,
            })
            keep += 1
            originated.append((sport, ev, p, offer, basis))

        mine = [r for r in rows if r["sport"] == sport]
        coverage[sport] = {
            "events": len(sp["events"]), "priced": len(mine),
            "official_model_rows": sum(1 for r in mine if r["basis"] == "official-model"),
            "high": sum(1 for r in mine if r["confidence"] == "high"),
            "high_in_band": sum(1 for r in mine if r["confidence"] == "high" and r["in_band"] and r["is_match"]),
            "status": sp["status"],
        }

    # ---- derived lines where the official number supports a second market ----
    fair_lines = []
    pa, pb = mil["runs_scored"] / 162, mil["runs_allowed"] / 162
    qa, qb = tb["runs_scored"] / 162, tb["runs_allowed"] / 162
    total_runs = round((pa + qb + qa + pb) / 2, 2)
    fair_lines.append({
        "sport": "Baseball", "event": "TB Rays @ MIL Brewers", "market": "Game Totals",
        "line": 8.5, "model_total": total_runs,
        "read": "over" if total_runs > 8.5 else "under",
        "note": "both clubs' season runs scored and allowed, per game, averaged across the two attacks",
        "source_url": "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
    })
    diff = pa - qa
    fair_lines.append({
        "sport": "Baseball", "event": "TB Rays @ MIL Brewers", "market": "Run Line",
        "line": -1.5, "model_margin": round(diff, 2),
        "read": "MIL -1.5" if diff > 1.5 else "MIL +1.5",
        "note": "difference between the two clubs' runs scored and allowed per game",
        "source_url": "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
    })
    for h, a in [("ZAL", "ASV"), ("OLY", "FBT"), ("PBB", "VBC")]:
        gap = el_rating(el[h]) - el_rating(el[a]) + 3.0
        fair_lines.append({
            "sport": "Basketball", "event": f"{el[h]['club']} v {el[a]['club']}", "market": "Pointspread",
            "line": round(gap * 2, 1), "note": "point differential per game plus a three-point home edge",
            "source_url": "https://www.euroleaguebasketball.net/en/euroleague/standings/",
        })

    band_note = ("A fair 70% shot is -233; a fair 71.4% shot is -250. Once a 4-6% book margin is taken on "
                 "the profit, the two published gates - at least 70% and no shorter than -250 - intersect in "
                 "roughly a 70.0-71.4% window. That arithmetic is fixed by the brief, not chosen here, and it "
                 "is the reason the count of in-band high-confidence selections is small.")

    out = {
        "generated_utc": olbg["captured_utc"],
        "provenance": "OLBG fixture list plus governing-body inputs; prices originated by this project",
        "rows": rows,
        "originated_lines": fair_lines,
        "unlined": unlined,
        "coverage": coverage,
        "method": {
            "confidence": {"high": "p >= 0.70", "medium": "0.60 <= p < 0.70", "low": "p < 0.60"},
            "tip_share_gate": f"a tip-share row may only be graded high on {MIN_TIPS_FOR_HIGH}+ tips",
            "smoothing": "(tips + 1) / (total + 2) - a 1-of-1 tip becomes 66.7%, never 100%",
            "margins": MARGIN,
            "band": [BAND_LOW, BAND_HIGH],
            "band_note": band_note,
            "band_basis": "the band is applied to the fair price, not the offered price",
            "price_rule": "fair = 1/p; offered = 1 + (fair - 1) * (1 - margin); American from the offered decimal",
        },
    }
    (DATA / "lines.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"rows {len(rows)}  fair lines {len(fair_lines)}  unlined {len(unlined)}")
    print(f"high {sum(1 for r in rows if r['confidence']=='high')}  "
          f"high+in-band(matches) {sum(1 for r in rows if r['confidence']=='high' and r['in_band'] and r['is_match'])}")
    for s in SPORTS:
        c = coverage[s]
        print(f"  {s:15} events {c['events']:3} priced {c['priced']:3} official {c['official_model_rows']:2} "
              f"high {c['high']:2} high+band {c['high_in_band']}")


if __name__ == "__main__":
    build()
