"""Hand-written predictions for the /daily-picks/ desk (session arena/6b4da610-olbg2).

One paragraph per published pick, keyed by (match id, selection). Every factual claim
is drawn from the input block in daily_picks_data.py: NHL records and point streaks from
nhl.com/standings/2026-10-22, URC table rows from stats.unitedrugby.com, EuroLeague
standings from euroleaguebasketball.net, MLB records from statsapi.mlb.com, RLWC pool
positions from the NRL draw, AFLW ladder positions from the 22 October capture.

No player-level claim (injury, lineup, scoring run) is made unless this session read it
on an official page. Where it was not read, the paragraph stays at team level.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "daily-picks"

TEXT_FILE = OUT / "prediction_texts.json"


def load_texts() -> dict:
    """Hand-written paragraphs, keyed 'match_id|selection'."""
    doc = json.loads(TEXT_FILE.read_text())
    return {tuple(k.split("|", 1)): v for k, v in doc["texts"].items()}


def main() -> None:
    picks = json.loads((OUT / "picks.json").read_text())["picks"]
    matches = {m["id"]: m for m in json.loads((OUT / "matches.json").read_text())["matches"]}
    rows = []
    missing = []
    texts = load_texts()
    for p in picks:
        key = (p["match_id"], p["selection"])
        text = texts.get(key)
        m = matches[p["match_id"]]
        if text is None:
            missing.append(key)
            continue
        if p["selection"].lower() not in text.lower():
            raise SystemExit(f"prediction for {key} never names the selection")
        # Any price quoted in the prose must equal the published fair price.
        price = f"+{p['fair_american']}" if p["fair_american"] > 0 else str(p["fair_american"])
        text = re.sub(r"at a fair [-+]?\d+", f"at a fair {price}", text)
        rows.append({
            "match_id": p["match_id"],
            "sport": p["sport"],
            "sport_name": m["sport_name"],
            "competition": m["competition"],
            "date": m["date"],
            "start_utc": m["start"],
            "matchup": f"{m['home']} vs {m['away']}",
            "market": p["market"],
            "selection": p["selection"],
            "probability": p["probability"],
            "fair_decimal": p["fair_decimal"],
            "fair_american": p["fair_american"],
            "confidence": p["confidence"],
            "in_band": p["in_band"],
            "word_count": len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'./-]*", text)),
            "prediction": text,
            "source_name": m["source_name"],
            "source_url": m["url"],
        })
    unused = [k for k in texts if k not in {(p["match_id"], p["selection"]) for p in picks}]
    payload = {
        "generated_utc": "2026-10-22T21:50:00Z",
        "session": "arena/6b4da610-olbg2",
        "count": len(rows),
        "min_words": min(r["word_count"] for r in rows) if rows else 0,
        "missing": missing,
        "unused_texts": unused,
        "predictions": rows,
    }
    (OUT / "predictions.json").write_text(json.dumps(payload, indent=1))
    print("predictions:", len(rows), "missing:", missing, "unused:", unused,
          "min words:", payload["min_words"])


if __name__ == "__main__":
    main()
