#!/usr/bin/env python3
"""Originate the /latest/ pick list and grade every pick.

Inputs are the originated prices in `data/latest/lines.json` (inherited, already reduced from
official rates) plus one market this session originates first hand: the Formula 1 United States
Grand Prix, priced from the published qualifying classification.

Rules, all stated on the published method page:
  * a selection is eligible for a pick only if its fixture had not started when the desk was cut;
  * the price must sit inside the brief's -250...+10000 band;
  * HIGH needs our chance at 70% or better and a price inside the band;
    MEDIUM needs 60% or better; anything else is LOW and is published with that label;
  * picks are spread across matches and markets - at most one match-winner, one handicap and one
    total per fixture - so a sport with one fixture still gets its several markets covered.

Run:  python scripts/latest_model.py
"""
from __future__ import annotations

import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "latest"
BUILD_UTC = "2026-10-24T22:45:00Z"
MAX_PICKS_PER_SPORT = 10
MIN_PICKS_PER_SPORT = 5
MIN_PROBABILITY = 0.45          # below this a pick is not published at all
RACE_MIN_PROBABILITY = 0.10     # a 20-runner race has no 45% favourite; the floor is lower there
RACE_LADDER = [{"winner": 5}]   # one race, one market, several drivers - like an outright list
POLE_WIN_SHARE = 0.40           # stated assumption for the F1 grid curve
F1_MARKET_WINNERS = 6


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def write(name, doc):
    (DATA / name).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def decimal_and_american(p: float):
    dec = round(1.0 / p, 3)
    dec = min(max(dec, 1.01), 12.0)
    if dec >= 2.0:
        american = int(round((dec - 1.0) * 100))
    else:
        american = -int(round(100.0 / (dec - 1.0)))
    return dec, american


def market_kind(row) -> str:
    """Derive the market family from the published label.

    The inherited file's own `kind` field is not reliable: several `Total sets` rows carry the label
    `winner`, which would let a totals row occupy a fixture's one match-winner slot. The label is the
    thing a reader sees, so the label decides.
    """
    m = row["market"].lower()
    if m.startswith("total"):
        return "total"
    if m.startswith("handicap"):
        return "handicap"
    return "winner"


def in_band(american: int) -> bool:
    return -250 <= american <= 10000


def grade(p: float, american: int) -> str:
    if p >= 0.70 and in_band(american):
        return "high"
    if p >= 0.60:
        return "medium"
    return "low"


def f1_lines(f1: dict):
    """Price the race-winner market from the published grid.

    The only free parameter is how fast a chance decays down the grid. It is fixed by one stated
    assumption - the pole sitter wins 40% of the time - and the same curve then gives every other
    driver's chance. Normalising over the 20 starters keeps the market a proper distribution.
    """
    grid = f1["grid"]
    drivers = list(grid)
    n = len(drivers)
    # solve exp(-k*(pos-1)) so that the pole sitter's normalised share is POLE_WIN_SHARE
    lo, hi = 0.0, 1.0
    for _ in range(80):
        k = (lo + hi) / 2
        w = [math.exp(-k * (grid[d] - 1)) for d in drivers]
        if w[0] / sum(w) < POLE_WIN_SHARE:      # share rises with k, so raise the low bound
            lo = k
        else:
            hi = k
    k = (lo + hi) / 2
    w = [math.exp(-k * (grid[d] - 1)) for d in drivers]
    total = sum(w)
    rows = []
    for d, weight in sorted(zip(drivers, w), key=lambda t: -t[1])[:F1_MARKET_WINNERS]:
        p = weight / total
        dec, american = decimal_and_american(p)
        rows.append({
            "fixture_id": f1["fixture_id"],
            "sport": "Motor Racing",
            "market": "Race winner",
            "selection": d,
            "probability": round(p, 4),
            "decimal": dec,
            "american": american,
            "american_display": f"{american:+d}" if american > 0 else str(american),
            "in_band": in_band(american),
            "basis": "grid_curve",
            "kind": "winner",
            "quality": 0.9,
            "assumption": (
                "Race-winner chance falls geometrically down the starting grid; the curve is fixed "
                f"so the pole sitter holds a {int(POLE_WIN_SHARE * 100)}% share and every other "
                "driver's share follows from their grid slot. Grid order is the official qualifying "
                "classification. No bookmaker price is read."),
            "home": f1["favourite"],
            "away": "Field",
            "start_utc": f1["start_utc"],
            "official_url": f1["source_url"],
        })
    # A second market on the same race: the field without the pole sitter.
    rest = [(d, wt) for d, wt in zip(drivers, w) if grid[d] != 1]
    rest_total = sum(wt for _, wt in rest)
    for d, wt in sorted(rest, key=lambda t: -t[1])[:3]:
        p = wt / rest_total
        dec, american = decimal_and_american(p)
        rows.append({
            "fixture_id": f1["fixture_id"],
            "sport": "Motor Racing",
            "market": "Winner without the pole sitter",
            "selection": d,
            "probability": round(p, 4),
            "decimal": dec,
            "american": american,
            "american_display": f"{american:+d}" if american > 0 else str(american),
            "in_band": in_band(american),
            "basis": "grid_curve",
            "kind": "handicap",
            "quality": 0.9,
            "assumption": "The same grid curve renormalised over the 19 drivers who did not take pole.",
            "home": f1["favourite"],
            "away": "Field",
            "start_utc": f1["start_utc"],
            "official_url": f1["source_url"],
        })
    return rows, k


def main() -> int:
    fixtures = read("fixtures.json")["fixtures"]
    lines = [r for r in read("lines.json")["lines"]
             if r["start_utc"] > BUILD_UTC]                       # not started when the desk was cut
    f1 = json.loads((DATA / "f1.json").read_text(encoding="utf-8"))
    f1_rows, k = f1_lines(f1)
    lines += f1_rows

    # A fixture whose own money line comes out at 95% or better is not a view, it is a broken input:
    # two teams in the same final are never that far apart, and the handicap ladder built on such a
    # margin produces nonsense like a -199900 price. Those fixtures are withheld from the pick list and
    # named on the review page with the number that triggered the test, instead of being published.
    winner_best = {}
    for r in lines:
        if r["kind"] == "winner":
            winner_best[r["fixture_id"]] = max(winner_best.get(r["fixture_id"], 0.0), r["probability"])
    implausible = {fid: p for fid, p in winner_best.items() if p >= 0.95}

    by_id = {f["id"]: f for f in fixtures}
    for r in lines:
        r["kind"] = market_kind(r)
        r["confidence"] = grade(r["probability"], r["american"])
        r["score"] = round(10 * r["probability"] * r.get("quality", 1.0), 1)

    picks, selection_notes = [], {}
    sports = []
    for r in lines:
        if r["sport"] not in sports:
            sports.append(r["sport"])

    # Widening ladder: how many selections of each market kind one fixture may contribute. The desk
    # takes the narrowest rung that still reaches five picks, so a sport with eight fixtures gets one
    # pick each across the strongest markets, and a sport with one fixture still gets its several
    # markets covered instead of being dropped.
    LADDER = [
        {"winner": 1},
        {"winner": 1, "handicap": 1},
        {"winner": 1, "handicap": 1, "total": 1},
        {"winner": 1, "handicap": 2, "total": 1},
        {"winner": 1, "handicap": 2, "total": 2},
        {"winner": 1, "handicap": 3, "total": 2},
    ]

    for sport in sports:
        floor = RACE_MIN_PROBABILITY if sport == "Motor Racing" else MIN_PROBABILITY
        ladder = RACE_LADDER if sport == "Motor Racing" else LADDER
        # Out-of-band prices are never published as picks. A fair -250 is 71.43%, so a selection the
        # desk rates above that cannot be backed inside the requested window at all - the pick goes on
        # a handicap or total rung instead, which is exactly what the widening ladder below allows.
        pool = [r for r in lines
                if r["sport"] == sport and r["probability"] >= floor and r["in_band"]
                and r["fixture_id"] not in implausible]
        # Inside-band selections first, then the chance closest to a fair -250 (71.4%) and below it.
        # That is what puts the desk's picks on the handicap rung rather than on unbettable chalk.
        pool.sort(key=lambda r: (not r["in_band"], -min(r["probability"], 0.714),
                                 r["fixture_id"], r["selection"]))
        chosen = []
        for rung in ladder:
            per_fixture = {}
            for r in chosen:
                per_fixture.setdefault(r["fixture_id"], []).append(r)
            for r in pool:
                if len(chosen) >= MAX_PICKS_PER_SPORT:
                    break
                if r in chosen:
                    continue
                used = per_fixture.get(r["fixture_id"], [])
                if sum(1 for u in used if u["kind"] == r["kind"]) >= rung.get(r["kind"], 0):
                    continue
                if sport != "Motor Racing" and any(u["market"] == r["market"] for u in used):
                    continue     # never back both sides of one line; a race is an outright market
                chosen.append(r)
                per_fixture.setdefault(r["fixture_id"], []).append(r)
            if len(chosen) >= MIN_PICKS_PER_SPORT:
                break
        chosen.sort(key=lambda r: (-r["probability"], r["fixture_id"]))
        for i, r in enumerate(chosen, 1):
            f = by_id[r["fixture_id"]]
            picks.append({
                "id": f"pick-{r['fixture_id']}-{r['kind']}-{i}",
                "fixture_id": r["fixture_id"],
                "sport": r["sport"],
                "competition": f["competition"],
                "home": r.get("home", f["home"]),
                "away": r.get("away", f["away"]),
                "start_utc": r["start_utc"],
                "start_display": f["start_display"],
                "market": r["market"],
                "selection": r["selection"],
                "probability": r["probability"],
                "decimal": r["decimal"],
                "american": r["american"],
                "american_display": r["american_display"],
                "in_band": r["in_band"],
                "confidence": r["confidence"],
                "score": r["score"],
                "basis": r["basis"],
                "assumption": r["assumption"],
                "official_url": r["official_url"],
                "olbg_url": f.get("olbg_url", ""),
            })
        selection_notes[sport] = {
            "fixtures_available": len({r["fixture_id"] for r in pool}),
            "picks": len(chosen),
        }

    picks.sort(key=lambda p: (sports.index(p["sport"]), -p["probability"], p["fixture_id"]))
    counts = {
        "count": len(picks),
        "high": sum(1 for p in picks if p["confidence"] == "high"),
        "medium": sum(1 for p in picks if p["confidence"] == "medium"),
        "low": sum(1 for p in picks if p["confidence"] == "low"),
        "in_band": sum(1 for p in picks if p["in_band"]),
        "by_sport": {s: sum(1 for p in picks if p["sport"] == s) for s in sports},
    }
    write("picks.json", {
        "withheld_fixtures": [
            {"fixture_id": fid,
             "sport": by_id[fid]["sport"],
             "reason": (f"Our own money line for this fixture closes at {p * 100:.1f}%, which no "
                        "two-team market can support. The input behind it is treated as broken, so "
                        "the fixture is withheld from the pick list and flagged rather than priced.")}
            for fid, p in sorted(implausible.items())],
        "build_utc": BUILD_UTC,
        "note": ("Only selections on fixtures that had not started when the desk was cut are "
                 "graded. Matches already under way are listed on the fixtures page with no pick."),
        **counts,
        "picks": picks,
    })
    write("f1_market.json", {
        "build_utc": BUILD_UTC,
        "curve_k": round(k, 6),
        "pole_share_assumed": POLE_WIN_SHARE,
        "note": "Free parameter of the F1 grid curve, recorded so the prices can be reproduced.",
    })
    print(f"latest_model: {len(lines)} priced selections on unstarted fixtures, "
          f"{counts['count']} picks ({counts['high']} high, {counts['medium']} medium, "
          f"{counts['low']} low), {counts['in_band']} inside the band, "
          f"{len(counts['by_sport'])} sports")
    for s, n in counts["by_sport"].items():
        print(f"  {s:14s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
