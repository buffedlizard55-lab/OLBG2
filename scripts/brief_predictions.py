#!/usr/bin/env python3
"""Brief desk - assemble and validate the written predictions.

Checks performed before anything is published:
  * every prediction points at a fixture that exists and is still upcoming;
  * the named selection exists as an originated market on that fixture;
  * at least 30 words;
  * the words "model" and "verified" never appear (the request forbids them in output);
  * no two write-ups share an opening four-word phrase, and no sentence of 8+ words is
    repeated verbatim between two write-ups;
  * a prediction is never attached to a fixture with no originated price.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "brief"
BANNED = ("model", "verified")
FIELD = {"golf-genesis": "Tournament winner", "f1-us-gp": "Race winner"}


def tier(p: float, in_band: bool) -> str:
    if p >= 0.70 and in_band:
        return "A"
    if p >= 0.70:
        return "B"
    if in_band:
        return "C"
    return "D"


def main():
    matches = json.loads((DATA / "matches.json").read_text())
    fixtures = {f["id"]: f for f in matches["fixtures"]}
    raw = []
    for name in ("prose_a.json", "prose_b.json"):
        raw += json.loads((DATA / name).read_text())["predictions"]

    out, errors = [], []
    seen_open, seen_sent = {}, {}
    for p in raw:
        fid = p.get("fixture_id")
        if not fid:
            for k in FIELD:
                if p["id"].startswith(k):
                    fid = k
        fid = fid or p["id"]
        f = fixtures.get(fid)
        if not f:
            errors.append(f"{p['id']}: no fixture {fid}")
            continue
        if not f["eligible"]:
            errors.append(f"{p['id']}: fixture is not upcoming")
            continue
        markets = [m for m in f["markets"] if m["selection"] == p["selection"] and m["market"] == p["market"]]
        if not markets:
            errors.append(f"{p['id']}: no such market/selection on the fixture")
            continue
        m = markets[0]
        text = p["text"].strip()
        words = re.findall(r"[A-Za-z0-9'’+-]+", text)
        if len(words) < 30:
            errors.append(f"{p['id']}: only {len(words)} words")
        low = text.lower()
        for b in BANNED:
            if b in low:
                errors.append(f"{p['id']}: banned word '{b}'")
        opening = " ".join(words[:4]).lower()
        if opening in seen_open:
            errors.append(f"{p['id']}: opening repeats {seen_open[opening]}")
        seen_open[opening] = p["id"]
        for sent in re.split(r"[.!?]", text):
            sw = re.findall(r"[A-Za-z0-9'’+-]+", sent)
            if len(sw) >= 8:
                key = " ".join(sw).lower()
                if key in seen_sent:
                    errors.append(f"{p['id']}: sentence repeats {seen_sent[key]}")
                seen_sent[key] = p["id"]
        out.append({
            "id": p["id"], "fixture_id": fid, "sport": f["sport"], "competition": f["competition"],
            "stage": f["stage"], "home": f["home"], "away": f["away"],
            "start": f.get("start_utc") or f.get("start_local"), "venue": f.get("venue", ""),
            "selection": p["selection"], "market": p["market"], "prob": m["prob"],
            "american": m["american"], "decimal": m["decimal"], "in_band": m["in_band"],
            "confidence": m["confidence"], "tier": tier(m["prob"], m["in_band"]),
            "source_key": p.get("fact_source", f["source_key"]),
            "source_url": f["source_url"], "text": text, "words": len(words),
        })

    if errors:
        raise SystemExit("prediction validation failed:\n  " + "\n  ".join(errors))

    by_sport = {}
    for r in out:
        by_sport.setdefault(r["sport"], []).append(r)
    payload = {
        "meta": {
            "count": len(out),
            "min_words": min(r["words"] for r in out),
            "max_words": max(r["words"] for r in out),
            "by_sport": {s: len(v) for s, v in sorted(by_sport.items())},
            "tiers": {t: sum(1 for r in out if r["tier"] == t) for t in "ABCD"},
            "banned_words_checked": list(BANNED),
        },
        "predictions": out,
    }
    (DATA / "predictions.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(payload["meta"], indent=1))


if __name__ == "__main__":
    main()
