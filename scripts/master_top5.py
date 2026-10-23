"""Choose the day's five-per-sport card.

The brief asks for up to five high-confidence picks per sport per day, and says that is a ceiling, not a
quota. This script applies that ceiling literally: for each sport it keeps at most five picks that carry a
high-confidence grade, preferring selections inside the -250 to +10000 window, then the shortest price, then
the earliest start. Sports that cannot field five are reported with the best alternative they do have, so the
gap is visible instead of being padded.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

MASTER = Path(__file__).resolve().parent.parent / "data" / "master"
LIMIT = 5


def main() -> None:
    picks = json.loads((MASTER / "picks.json").read_text(encoding="utf-8"))["picks"]
    matches = json.loads((MASTER / "matches.json").read_text(encoding="utf-8"))["matches"]
    predictions = json.loads((MASTER / "predictions.json").read_text(encoding="utf-8"))["predictions"]
    predicted = {p["id"] for p in predictions}
    m_by_id = {m["id"]: m for m in matches}

    upcoming = [p for p in picks if not m_by_id.get(p["match_id"], {}).get("started")]
    by_sport: dict[str, list] = {}
    for p in upcoming:
        by_sport.setdefault(p["sport"], []).append(p)

    board = {}
    for sport, rows in sorted(by_sport.items()):
        high = [p for p in rows if p["confidence"] == "high"]
        def rank(p):
            am = p["fair_american"]
            gap = 0 if p["in_band"] else (-250 - am if am < -250 else am - 10000)
            return (0 if p["in_band"] else 1, gap, -p["prob"], p["start_utc"], p["id"])

        high.sort(key=rank)
        chosen = high[:LIMIT]
        best_alt = None
        if len(chosen) < LIMIT:
            rest = [p for p in rows if p["confidence"] != "high"]
            rest.sort(key=lambda p: (not p["in_band"], -p["prob"], p["start_utc"], p["id"]))
            best_alt = rest[0] if rest else None
        board[sport] = {
            "sport": sport,
            "high_available": len(high),
            "featured": [
                {
                    "pick_id": p["id"],
                    "match_id": p["match_id"],
                    "event": p["event"],
                    "competition": p["competition"],
                    "start_utc": p["start_utc"],
                    "market": p["market"],
                    "selection": p["selection"],
                    "fair_american": p["fair_american"],
                    "prob": p["prob"],
                    "in_band": p["in_band"],
                    "basis": p["basis"],
                    "official_url": p["official_url"],
                    "olbg_url": p.get("olbg_url", ""),
                    "has_prediction": p["id"] in predicted,
                    "venue": p.get("venue", ""),
                }
                for p in chosen
            ],
            "best_alternative": None
            if best_alt is None
            else {
                "pick_id": best_alt["id"],
                "selection": best_alt["selection"],
                "confidence": best_alt["confidence"],
                "prob": best_alt["prob"],
                "fair_american": best_alt["fair_american"],
            },
        }

    payload = {
        "meta": {
            "rule": "At most five high-confidence picks per sport per day; selections inside -250..+10000 first, then the price closest to that window, then the shortest price, then the earliest start.",
            "limit": LIMIT,
            "sports_with_rows": len(board),
            "featured_total": sum(len(v["featured"]) for v in board.values()),
            "featured_in_band": sum(1 for v in board.values() for f in v["featured"] if f["in_band"]),
            "featured_with_prediction": sum(1 for v in board.values() for f in v["featured"] if f["has_prediction"]),
        },
        "board": board,
    }
    (MASTER / "top5.json").write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(payload["meta"], indent=1))
    for sport, v in board.items():
        print(f"  {sport:14s} high={v['high_available']:2d} featured={len(v['featured'])}")


if __name__ == "__main__":
    main()
