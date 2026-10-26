#!/usr/bin/env python3
"""Written previews for session 9cf54b86 (26 October 2026 slate).

Two tiers, printed on every card so a reader always knows the footing:

  full   — the preview quotes statistics read from an official governing-body feed.
  market — no official fixture-level feed was readable for that competition, so the preview
           is confined to the fixture, the OLBG tip sample and our own price. It makes no
           claim about form, recent results or availability.

Run: python scripts/slate26_predictions.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slate26"

TEXTS = {
    "S26-008": (
        "full",
        "Edmonton carry an 8-2-1 record into this one against Detroit's 4-4-3, and the gap shows in the scoring "
        "numbers: the Oilers have 49 goals for and 39 against in 11 games, while Devon Levi has gone 6-1-0 with a "
        "3.11 goals-against average. Connor McDavid has 16 points across his last five games and Leon Draisaitl has "
        "eight goals in the same span. The pick is Edmonton on the money line and our price is -333."
    ),
    "S26-073": (
        "full",
        "Tampa Bay won 98 games and went 55-26 at home in the 2026 regular season, yet they arrive at World Series "
        "Game 3 trailing Milwaukee 2-0. The official feed lists Robert Gasser for the Brewers and Freddy Peralta for "
        "the Rays, with first pitch at Tropicana Field, and nine of the eleven tips on OLBG's board are on Tampa Bay. "
        "The pick is the Rays on the money line at our price of -339."
    ),
    "S26-025": (
        "market",
        "Alexandra Eala is the side of this match the OLBG board leans to, holding six of the nine tips logged on "
        "the fixture, and our own line makes her -181 to win it. The market is a straight Win Match, so the bet "
        "needs nothing beyond a victory in whatever number of sets it takes; the board's 67% share is a popularity "
        "read rather than a price, which is why our figure sits a little lower."
    ),
    "S26-030": (
        "market",
        "Matteo Berrettini holds three of the four tips on this match and our price on him is -248, close to the "
        "shortest line this desk will publish before a selection drops out of the -250 to +10000 window. The "
        "selection is the Win Match market only: Berrettini needs the match, not a set score or a handicap, and the "
        "four-tip sample is printed here rather than smoothed over."
    ),
    "S26-038": (
        "market",
        "This is the third T20 international of New Zealand's series against India, and fourteen of the twenty-one "
        "tips OLBG has logged on the fixture are on the tourists, which our line turns into -181. The selection is "
        "the Win Match market, so the pick is settled by the result and not by a series scoreline. Twenty-one tips "
        "is the deepest sample on the cricket hub at capture."
    ),
    "S26-039": (
        "market",
        "Ireland take eleven of the sixteen tips on the closing one-day international in Namibia, and our price on "
        "them is -195. The fixture is billed as the third ODI, so the pick is Ireland to win a 50-over match rather "
        "than any innings or top-batter market. At 69% the board's support is broad but not unanimous, and the grade "
        "carries that sample with it."
    ),
    "S26-042": (
        "market",
        "OLBG's Women's Big Bash card has four of six tips on Hobart Hurricanes for the 29 October meeting with "
        "Melbourne Stars, and our line makes them -181. It is a two-way Win Match market with no draw to complicate "
        "the result, so the pick stands or falls on who wins. Six tips is a small sample and the desk says so "
        "instead of hiding it behind the grade."
    ),
    "S26-045": (
        "market",
        "The selection here is the handicap rather than the result: Kildimo Pallaskenry are handed a 3.5-point "
        "start against Fr Caseys, so the bet lands if they win, draw, or lose by three points or fewer. Five of the "
        "seven tips on the OLBG board take that side of the line, and our price on it is -211. Because it is a "
        "handicap, a narrow defeat still pays."
    ),
    "S26-059": (
        "market",
        "Norde Volei hold six of the eight tips on this Brazilian Superliga fixture and our price on them is -248, "
        "the shortest line on the volleyball hub at capture. The pick is the Win Match market, which needs the match "
        "and not a set score, so a five-set grind pays exactly the same as a straight-sets sweep. Eight tips is the "
        "second-deepest sample among the fourteen volleyball rows."
    ),
    "S26-061": (
        "market",
        "Vallefoglia are the visiting side in this Serie A1 women's match and the OLBG board has five of seven tips "
        "with them, which our line prices at -211. The market is a straight Win Match, so the selection does not "
        "depend on a set score or a handicap. Seven tips is a workable sample and the row is graded high with that "
        "share and count printed alongside it."
    ),
    "S26-065": (
        "market",
        "SK Aich/Dob take three of the four tips for the Klagenfurt meeting and our price on them is -248. Only four "
        "tips sit behind the row, which is the minimum this desk will grade high, and the pick is confined to the "
        "Win Match market. The Austrian Volley League fixture list separately confirms the match, its venue and an "
        "18:00 local start."
    ),
}

BANNED = ("model", "verified", "algorithm", "machine learning")


def main() -> None:
    fixtures = json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["picks"]
    by_id = {f["id"]: f for f in fixtures}
    pick_by_id = {p["fixture"]: p for p in picks}

    rows, errors, openings = [], [], set()
    for fid, (tier, text) in TEXTS.items():
        f, p = by_id[fid], pick_by_id[fid]
        words = len(text.split())
        opening = " ".join(text.split()[:5]).lower()
        if words < 30:
            errors.append(f"{fid}: only {words} words")
        if opening in openings:
            errors.append(f"{fid}: opening repeats another preview")
        openings.add(opening)
        for word in BANNED:
            if re.search(rf"\b{word}", text, re.I):
                errors.append(f"{fid}: banned word '{word}'")
        tokens = [t for t in re.split(r"[^A-Za-z]+", f["selection"]) if len(t) > 3]
        if not any(re.search(rf"\b{t}", text, re.I) for t in tokens):
            errors.append(f"{fid}: selection not named")
        if tier == "full" and not f["facts"]:
            errors.append(f"{fid}: full tier without official facts")
        if tier == "market" and f["facts"]:
            errors.append(f"{fid}: market tier on a row that has official facts")
        rows.append({
            "fixture": fid, "tier": tier, "sport": f["sport"], "sport_label": f["sport_label"],
            "league": f["league"], "event": f["event"], "selection": f["selection"],
            "market": p["market"], "price": p["price"], "probability": p["probability"],
            "confidence": p["confidence"], "in_band": p["in_band"],
            "tips": p["tips"], "share": p["share"], "words": words, "text": text,
            "facts": f["facts"], "hub_url": f["hub_url"], "olbg_event_id": f["olbg_event_id"],
        })

    if errors:
        raise SystemExit("slate26_predictions: " + "; ".join(errors))

    rows.sort(key=lambda r: (r["tier"] != "full", -r["share"], r["fixture"]))
    payload = {
        "captured_utc": "2026-10-26T05:45:00Z",
        "count": len(rows),
        "full": sum(1 for r in rows if r["tier"] == "full"),
        "market": sum(1 for r in rows if r["tier"] == "market"),
        "on_high_picks": sum(1 for r in rows if r["confidence"] == "high"),
        "shortest_words": min(r["words"] for r in rows),
        "predictions": rows,
    }
    (DATA / "predictions.json").write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"slate26_predictions: {payload['count']} previews ({payload['full']} full, {payload['market']} market), "
          f"shortest {payload['shortest_words']} words")


if __name__ == "__main__":
    main()
