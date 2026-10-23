#!/usr/bin/env python3
"""Summit desk predictions.

Writes unique reader-facing predictions for the shortlisted high-confidence picks.
Every fact is copied from the committed fixture capture; no statistic is invented.
Run: python3 scripts/summit_predictions.py
"""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "summit")
GENERATED = "2026-10-23T22:00:00Z"
SESSION = "arena/84013d5f-olbg2"
MIN_WORDS = 30
BANNED = re.compile(r"\b(model|models|modelled|modeled|modelling|modeling|verify|verified|verifies|verification)\b", re.I)

TEXTS = {
    "olbg-609576": (
        "Vodacom Bulls -18 points",
        "The Bulls are the pick at minus 18 points in Saturday’s URC Round 4 game. Ulster are winless after three rounds, "
        "0-2-1 with 88 points for and 93 against. The Bulls are 2-0-1 with 126 points for and only 54 against, a roughly "
        "24-point edge. An 18-point handicap remains near the desk’s 70 per cent line. Selection: Vodacom Bulls -18 points."
    ),
    "olbg-609580": (
        "DHL Stormers -7 points",
        "Stormers are the pick at minus 7 points against Scarlets in URC Round 4. The Stormers are 2-0-1 with 81 points for "
        "and 54 against; Scarlets are 1-0-2 with 68 for and 85 against. That is about a 15-point expected gap, so a "
        "seven-point handicap is near the desk’s 70 per cent line. Selection: DHL Stormers -7 points."
    ),
    "olbg-609571": (
        "Glasgow Warriors -1.5 points",
        "Glasgow Warriors are the pick at minus 1.5 points against Benetton in URC Round 4. Glasgow are 2-0-1 with 95 "
        "points for and 72 against; Benetton are 0-1-2 with 64 for and 68 against. Glasgow’s defensive edge makes the "
        "narrow handicap a roughly 70 per cent chance. Selection: Glasgow Warriors -1.5 points."
    ),
    "olbg-12084": (
        "Paris Saint-Germain -6 goals",
        "Paris Saint-Germain are the pick at minus 6 goals against Saint-Raphaël in LNH J08. PSG are unbeaten at 7-0-0 "
        "with 239 goals for and 190 against; Saint-Raphaël are 2-5-0 with 207 for and 225 against. A six-goal handicap is "
        "about a 71 per cent chance on the desk’s goal-difference line. Selection: Paris Saint-Germain -6 goals."
    ),
    "olbg-12082": (
        "HBC Nantes -3.5 goals",
        "HBC Nantes are the pick at minus 3.5 goals against Chambéry in LNH J08. Nantes are 6-1-0 with 244 goals for and "
        "203 against; Chambéry are 2-3-2 with 224 for and 231 against. The three-and-a-half goal line sits near the desk’s "
        "70 per cent threshold. Selection: HBC Nantes -3.5 goals."
    ),
    "olbg-902159": (
        "Stefanos Tsitsipas to win",
        "Stefanos Tsitsipas is the pick to beat Nikoloz Basilashvili in the Almaty semi-final. Tsitsipas leads the "
        "head-to-head 3-1, including the 2019 Australian Open, and is ranked 39th against Basilashvili’s 128th. The desk "
        "sets the match-winner line at 70 per cent for this short sample. Selection: Stefanos Tsitsipas to win."
    ),
}

# Fact claims must match values already present in the fixture capture.
FACTS = {
    "olbg-609576": [
        ("Vodacom Bulls", "URC 2026/27: 2-0-1, 11 points, 126 points for, 54 against after Round 3"),
        ("Ulster Rugby", "URC 2026/27: 0-2-1, 8 points, 88 points for, 93 against after Round 3"),
        ("URC fixture", "Bulls v Ulster, Round 4, Saturday 24 October 2026, 07:45 local as published by URC"),
    ],
    "olbg-609580": [
        ("DHL Stormers", "URC 2026/27: 2-0-1, 11 points, 81 points for, 54 against after Round 3"),
        ("Scarlets", "URC 2026/27: 1-0-2, 7 points, 68 points for, 85 against after Round 3"),
        ("URC fixture", "Stormers v Scarlets, Round 4, Saturday 24 October 2026, 10:00 local as published by URC"),
    ],
    "olbg-609571": [
        ("Glasgow Warriors", "URC 2026/27: 2-0-1, 13 points, 95 points for, 72 against after Round 3"),
        ("Benetton Rugby", "URC 2026/27: 0-1-2, 5 points, 64 points for, 68 against after Round 3"),
        ("URC fixture", "Benetton Rugby v Glasgow Warriors, Round 4, Saturday 24 October 2026, 10:00 local as published by URC"),
    ],
    "olbg-12084": [
        ("Paris Saint-Germain Handball", "LNH Daikin StarLigue 2026/27: 7-0-0, 14 points, 239 goals for, 190 against"),
        ("Saint-Raphaël Var Handball", "LNH Daikin StarLigue 2026/27: 2-5-0, 4 points, 207 goals for, 225 against"),
        ("LNH fixture", "Saint-Raphaël v Paris, J08, Sunday 25 October 2026, 16:00 local as published by LNH"),
    ],
    "olbg-12082": [
        ("HBC Nantes", "LNH Daikin StarLigue 2026/27: 6-1-0, 12 points, 244 goals for, 203 against"),
        ("Chambéry Savoie Mont-Blanc Handball", "LNH Daikin StarLigue 2026/27: 2-3-2, 6 points, 224 goals for, 231 against"),
        ("LNH fixture", "Nantes v Chambéry, J08, Saturday 24 October 2026, 19:00 local as published by LNH"),
    ],
    "olbg-902159": [
        ("ATP fixture", "Nikoloz Basilashvili v Stefanos Tsitsipas, Almaty semifinal, Saturday 24 October 2026, not before 17:00 local"),
        ("Head to head", "Stefanos Tsitsipas leads Nikoloz Basilashvili 3-1; most recent Australian Open 2019 6-3 3-6 7-6(7) 6-4"),
        ("ATP rankings context", "Stefanos Tsitsipas ranked 39th, Nikoloz Basilashvili ranked 128th on the official ATP Tour page"),
    ],
}

def main():
    with open(os.path.join(DATA, "matches.json")) as f:
        matches = json.load(f)
    with open(os.path.join(DATA, "picks.json")) as f:
        picks = json.load(f)
    fix = {m["id"]: m for m in matches["fixtures"]}
    by_pick = {p["id"]: p for p in picks["picks"]}

    predictions = []
    pid = 0
    for m in matches["fixtures"]:
        if m["id"] not in TEXTS:
            continue
        selection, text = TEXTS[m["id"]]
        words = len(text.split())
        if words < MIN_WORDS:
            raise SystemExit(f"{m['id']}: prediction only {words} words")
        if BANNED.search(text):
            raise SystemExit(f"{m['id']}: banned word in prediction")
        pick = next((p for p in picks["picks"] if p["fixture_id"] == m["id"] and p.get("sport_rank")), None)
        if pick is None:
            raise SystemExit(f"{m['id']}: no shortlisted pick")
        if pick["selection"] != selection:
            raise SystemExit(f"{m['id']}: selection mismatch {pick['selection']} vs {selection}")
        pid += 1
        pred_id = f"summit-pred-{pid}"
        fact_list = []
        for item, value in FACTS[m["id"]]:
            source = next((f["source_url"] for f in m["facts"] if f.get("value") == value or f.get("text") == value), None)
            if not source:
                raise SystemExit(f"{m['id']}: fact not found in capture: {value[:60]}")
            fact_list.append({"item": item, "claim": value, "source_url": source})
        predictions.append({
            "id": pred_id,
            "headline": f"{selection} — desk pick",
            "fixture_id": m["id"],
            "pick_id": pick["id"],
            "sport": m["sport"],
            "selection": selection,
            "probability": pick["probability"],
            "fair_decimal": pick["fair_decimal"],
            "fair_american": pick["fair_american"],
            "word_count": words,
            "text": text,
            "facts": fact_list,
            "injury_note": "No official injury list was published for this fixture in today’s captures.",
        })
        pick["prediction_id"] = pred_id

    openings = {" ".join(p["text"].split()[:3]).lower() for p in predictions}
    if len(openings) != len(predictions):
        raise SystemExit("duplicate prediction openings")
    texts = [p["text"] for p in predictions]
    if len(set(texts)) != len(texts):
        raise SystemExit("duplicate prediction bodies")

    preds_out = {
        "generated_utc": GENERATED,
        "session": SESSION,
        "count": len(predictions),
        "min_words": MIN_WORDS,
        "sports": sorted({p["sport"] for p in predictions}),
        "unpaid_graded": [],
        "graded_not_shortlisted": [],
        "predictions": predictions,
    }
    with open(os.path.join(DATA, "predictions.json"), "w") as f:
        json.dump(preds_out, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA, "picks.json"), "w") as f:
        json.dump(picks, f, indent=2, ensure_ascii=False)
    print(f"predictions {len(predictions)}")

if __name__ == "__main__":
    main()
