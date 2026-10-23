#!/usr/bin/env python3
"""Carry the earlier `/ledger/` previews (session 21a0c524) into this desk.

That session published 26 previews against its own fixture ids before this desk was
merged over the top of it. The ids do not line up with ours, so nothing is silently
re-pointed: each preview keeps the event, market and selection it was written for, keeps
a link to the page it was written from, and is marked as carried rather than re-checked.

Prose rules are re-run here, not trusted. Anything that fails is dropped and reported.
Output: data/ledger/inherited.json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402

DATA = ROOT / "data" / "ledger"
SOURCE_LAYER = "21a0c524"
BANNED = ("model", "verified", "verification")


def main() -> int:
    previews = json.loads((DATA / "inherited" / f"previews_{SOURCE_LAYER}.json").read_text(encoding="utf-8"))
    sources = {s["key"]: s for s in json.loads(
        (DATA / "inherited" / f"sources_{SOURCE_LAYER}.json").read_text(encoding="utf-8"))["sources"]}

    kept, dropped = [], []
    openings = {}
    for item in previews["predictions"]:
        text = re.sub(r"\s+", " ", item["text"]).strip()
        words = len(text.split())
        low = text.lower()
        problems = []
        if words < 30:
            problems.append(f"only {words} words")
        for bad in BANNED:
            if re.search(rf"\b{bad}\b", low):
                problems.append(f"contains the forbidden word '{bad}'")
        opening = " ".join(text.split()[:6]).lower()
        if opening in openings:
            problems.append("duplicate opening")
        if not item.get("source_keys"):
            problems.append("no source attached")
        cited = []
        for key in item.get("source_keys", []):
            src = sources.get(key)
            if not src or not src.get("url", "").startswith("https://"):
                problems.append(f"source '{key}' missing or not https")
                continue
            cited.append({"key": key, "name": src.get("name", ""), "url": src["url"],
                          "used_for": src.get("used_for", "")})
        if problems:
            dropped.append({"sport": item.get("sport", ""), "event": item.get("event", ""),
                            "selection": item.get("selection", ""), "problems": problems})
            continue
        openings[opening] = item.get("fixture", "")
        kept.append({
            "sport": item["sport"],
            "event": item["event"],
            "competition": item.get("competition", ""),
            "date": item.get("date", ""),
            "carried_fixture_id": item.get("fixture", ""),
            "market": item.get("market", ""),
            "selection": item["selection"],
            "confidence": item.get("confidence", ""),
            "prob": item.get("prob"),
            "american": item.get("american"),
            "decimal": item.get("decimal"),
            "text": text,
            "words": words,
            "sources": cited,
            "provenance": f"carried from the {SOURCE_LAYER} ledger; prose rules re-checked here, facts not re-read",
        })

    by_sport: dict[str, int] = {}
    for p in kept:
        by_sport[p["sport"]] = by_sport.get(p["sport"], 0) + 1

    out = {
        "meta": {
            "generated_at": anchor(),
            "source_layer": SOURCE_LAYER,
            "archived_from": "data/ledger/inherited/",
            "published": len(kept),
            "dropped": len(dropped),
            "by_sport": dict(sorted(by_sport.items())),
            "min_words": min((p["words"] for p in kept), default=0),
            "max_words": max((p["words"] for p in kept), default=0),
            "rule": "at least 30 words, unique opening, selection named, no forbidden words, https source linked",
        },
        "previews": kept,
        "dropped": dropped,
    }
    (DATA / "inherited.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["meta"], indent=1))
    for d in dropped:
        print("DROPPED", d["sport"], d["selection"], d["problems"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
