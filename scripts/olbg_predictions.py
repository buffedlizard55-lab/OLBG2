#!/usr/bin/env python3
"""Publish high-selection prose and the complete review queue."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "olbg"
source = json.loads((DATA / "source.json").read_text(encoding="utf-8"))
matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))["matches"]
lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))["lines"]
by_event = {e["id"]: e for e in matches}

predictions = []
seen = set()
for line in lines:
    if not line["primary"] or line["confidence"] != "high":
        continue
    event = by_event[line["event_id"]]
    text = event.get("prose") or ""
    words = text.split()
    normalized = re.sub(r"\W+", " ", text.lower()).strip()
    assert len(words) >= 30, f"short prediction: {event['id']}"
    assert normalized and normalized not in seen, f"duplicate/empty prediction: {event['id']}"
    assert not re.search(r"\b(model|verified)\b", text, re.I), f"banned prediction word: {event['id']}"
    assert re.match(r"^Bet\s", text), f"selection is not explicit: {event['id']}"
    assert line["selection"].lower() in text.lower(), f"selection absent from prose: {event['id']}"
    assert line["probability"] > 0.70 and -250 <= line["fair_american"] <= 10000
    seen.add(normalized)
    predictions.append({
        "event_id": event["id"], "sport": event["sport"], "match": event["name"],
        "selection": line["selection"], "probability": line["probability"],
        "fair_american": line["fair_american"], "confidence": "high", "text": text,
        "word_count": len(words), "provenance": event["provenance"],
        "official_sources": event["official_sources"], "olbg_url": event["olbg_url"],
    })

flags = list(source["flags"])
for event in matches:
    if not event["line"]:
        flags.append({
            "id": "BLANK-" + event["id"], "severity": "blank",
            "title": "No supportable price: " + event["name"],
            "detail": event["blank_reason"] + " The row remains in the fixture table with official links; no value is inferred.",
            "links": event["official_sources"],
        })
for line in lines:
    if line["probability"] > 0.70 and -250 <= line["fair_american"] <= 10000 and line["confidence"] != "high":
        event = by_event[line["event_id"]]
        reason = ("The independent-Poisson market is deliberately low confidence because the early-season scoring sample and distribution assumptions do not pass the detailed high-confidence evidence gate."
                  if not line["primary"] else
                  "The number falls inside the requested window, but this row lacks the detailed official matchup/availability review required for high-confidence publication. It remains capped rather than being promoted by arithmetic alone.")
        flags.append({
            "id": "CAP-" + line["id"], "severity": "limitation",
            "title": "High-confidence cap: " + line["selection"], "detail": reason,
            "links": event["official_sources"],
        })

(DATA / "predictions.json").write_text(json.dumps({"research_cutoff": source["research_cutoff"], "predictions": predictions}, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
(DATA / "flagged.json").write_text(json.dumps({"research_cutoff": source["research_cutoff"], "items": flags}, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
summary_path = DATA / "summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary["counts"]["predictions"] = len(predictions)
summary["counts"]["flags"] = len(flags)
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
print(f"Wrote {len(predictions)} unique high-confidence predictions and {len(flags)} review items")
