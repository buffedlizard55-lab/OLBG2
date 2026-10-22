"""Generate data/canon/predictions.json: one written prediction per high-confidence pick.

Every prediction:
- Is >= 30 words (verified programmatically).
- Is unique prose (no two predictions share an opening sentence).
- Names the competing teams/players, a verified current-form/stat fact, a
  dated recent result, and an explicit betting selection with the model's
  fair American/decimal price.
- The fair price quoted in the text is generated from the SAME probability
  used to build data/canon/matches.json, so prose and data can never drift.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "canon"

sys.path.insert(0, str(ROOT / "scripts"))
from canon_prose import PROSE_BY_ID  # noqa: E402


def main():
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
    by_id = {m["id"]: m for m in matches}

    predictions = []
    seen_openers = set()
    for match_id, template in PROSE_BY_ID.items():
        match = by_id.get(match_id)
        if match is None:
            raise SystemExit(f"canon_predictions.py: {match_id} missing from matches.json")
        top = match["top_market"]
        if top is None:
            raise SystemExit(f"canon_predictions.py: {match_id} has no market to predict")
        prob = top["probability"]
        if not (0.70 <= prob and -250 <= top["fair_american"] <= 10000):
            raise SystemExit(f"canon_predictions.py: {match_id} fails the uniform odds-window gate")
        american_str = f"+{top['fair_american']}" if top["fair_american"] > 0 else str(top["fair_american"])
        text = template.format(
            selection=top["selection"],
            fair_american=american_str,
            fair_decimal=f"{top['fair_decimal']:.2f}",
        )
        words = text.split()
        if len(words) < 30:
            raise SystemExit(f"canon_predictions.py: {match_id} prediction is only {len(words)} words")
        opener = " ".join(words[:4])
        if opener in seen_openers:
            raise SystemExit(f"canon_predictions.py: {match_id} repeats opener '{opener}'")
        seen_openers.add(opener)
        predictions.append({
            "id": match_id,
            "match_id": match_id,
            "sport": match["sport"],
            "sport_name": match["sport_name"],
            "competition": match["competition"],
            "date": match["date"],
            "matchup": f"{match['home']} vs {match['away']}",
            "selection": top["selection"],
            "market": top["market"],
            "probability": prob,
            "fair_decimal": top["fair_decimal"],
            "fair_american": top["fair_american"],
            "word_count": len(words),
            "prediction": text,
            "source_url": match["source_url"],
        })

    predictions.sort(key=lambda p: (p["sport"], p["date"] or "", p["id"]))
    out = {
        "generated_utc": "2026-10-22T12:20:00Z",
        "session": "arena/3de6d2ed-olbg2",
        "min_words": 30,
        "focus_band_american": [-250, 10000],
        "focus_band_decimal": [1.40, 101.00],
        "count": len(predictions),
        "sports_covered": len({p["sport"] for p in predictions}),
        "predictions": predictions,
    }
    (DATA_DIR / "predictions.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"canon_predictions.py OK: {len(predictions)} predictions across {out['sports_covered']} sports, "
          f"min {min(p['word_count'] for p in predictions)} words, max {max(p['word_count'] for p in predictions)} words")


if __name__ == "__main__":
    main()
