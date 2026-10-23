#!/usr/bin/env python3
"""Validate and join the hand-written previews onto the selection table.

Checks performed here (and repeated by tests/test_ledger_41b3bae5.py):
  * every preview is at least 30 words;
  * no two previews share more than a short opening phrase (uniqueness);
  * the words "model" and "verified" do not appear, per the brief;
  * every preview names its selection and links the official source it was written from;
  * the pick id exists in data/ledger/picks.json.

Anything that fails is not published as a preview: it is written to the flagged list with
the exact reason, so a shortfall is visible instead of hidden.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402
DATA = ROOT / "data" / "ledger"
ANCHOR = anchor()
import datetime as _dtmod
ANCHOR_DT = _dtmod.datetime.strptime(ANCHOR, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dtmod.timezone.utc)
BANNED = ("model", "verified", "verification")


def main() -> int:
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    prose = json.loads((DATA / "prose.json").read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in picks["picks"]}

    accepted, rejected = [], []
    seen_openings = {}
    for item in prose["predictions"]:
        pid = item["pick_id"]
        text = re.sub(r"\s+", " ", item["text"]).strip()
        words = len(text.split())
        problems = []
        pick = by_id.get(pid)
        if not pick:
            problems.append("pick id not present in the selection table")
        if words < 30:
            problems.append(f"only {words} words")
        low = text.lower()
        for bad in BANNED:
            if re.search(rf"\b{bad}\b", low):
                problems.append(f"contains the forbidden word '{bad}'")
        if pick:
            sticky = [t for t in re.findall(r"[a-z]+", pick["selection"].lower()) if len(t) >= 4]
            if sticky and not any(t in low for t in sticky):
                problems.append("does not name the selection")
        opening = " ".join(text.split()[:6]).lower()
        if opening in seen_openings:
            problems.append("duplicate opening")
        if not item.get("source_url"):
            problems.append("no source url")
        if not item.get("facts") or len(item["facts"]) < 2:
            problems.append("fewer than two cited facts")
        if problems:
            rejected.append({"pick_id": pid, "sport": pick["sport"] if pick else "", "text": text,
                             "words": words, "problems": problems})
            continue
        seen_openings[opening] = pid
        accepted.append({
            **pick,
            "text": text, "words": words,
            "facts": item["facts"],
            "prediction_source": item["source_url"],
        })

    by_sport = {}
    for p in accepted:
        by_sport.setdefault(p["sport"], []).append(p)

    out = {
        "meta": {
            "generated_at": ANCHOR,
            "published": len(accepted), "rejected": len(rejected),
            "by_sport": {k: len(v) for k, v in sorted(by_sport.items())},
            "min_words": min((p["words"] for p in accepted), default=0),
            "max_words": max((p["words"] for p in accepted), default=0),
            "rule": "at least 30 words, unique, selection named, two cited facts, official source linked",
        },
        "predictions": accepted,
        "rejected": rejected,
    }
    (DATA / "predictions.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["meta"], indent=1))
    for r in rejected:
        print("REJECTED", r["pick_id"], r["problems"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
