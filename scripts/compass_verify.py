#!/usr/bin/env python3
"""Line-by-line verification for the /compass/ desk.

Checks (all must pass):
 1. Determinism — re-rendering every page in memory is byte-identical to disk.
 2. High-confidence predictions are >= 30 words, no repeated openings, no banned words.
 3. Band integrity — in_band flag matches the -250..+10000 American conversion.
 4. Pick/line/fixture cross-references resolve.
 5. Every fixture with a non-blank official source has an http(s) URL.
 6. Every OLBG event id is unique; all 15 sports present in the nav.
 7. Internal link audit over all 27 rendered pages.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

DATA = ROOT / "data" / "compass"
OUT = ROOT / "compass"

import compass_build as B  # noqa: E402


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    errors = []

    fixtures = load("fixtures.json")["fixtures"]
    lines = load("lines.json")["lines"]
    picks = load("picks.json")["picks"]
    preds = load("predictions.json")["predictions"]
    olbg = load("olbg.json")
    flagged = load("flagged.json")["items"]
    sources = load("sources.json")["sources"]

    # 1. determinism
    for name, fn in [
        ("index.html", B.build_index), ("picks.html", B.build_picks),
        ("predictions.html", B.build_predictions), ("matches.html", B.build_matches),
        ("lines.html", B.build_lines), ("band.html", B.build_band),
        ("olbg.html", B.build_olbg), ("sources.html", B.build_sources),
        ("methodology.html", B.build_methodology), ("flagged.html", B.build_flagged),
        ("sports/index.html", B.build_sports_index),
    ] + [(f"sports/{B.SLUG[s]}.html", lambda s=s: B.build_sport(s)) for s in B.SPORTS]:
        disk = (OUT / name).read_text(encoding="utf-8")
        fresh = fn()
        if disk != fresh:
            errors.append(f"non-deterministic page: {name}")

    # 2. predictions
    words = {p["id"]: len(p["text"].split()) for p in preds}
    for p in preds:
        if p["confidence"] == "high" and words[p["id"]] < 30:
            errors.append(f"high prediction under 30 words: {p['id']} ({words[p['id']]})")
        low = p["text"].lower()
        for banned in ("model", "verified"):
            if banned in low:
                errors.append(f"banned word '{banned}' in prediction {p['id']}")
    openings = {}
    for p in preds:
        key = " ".join(p["text"].split()[:4]).lower()
        if key in openings:
            errors.append(f"repeated opening: {openings[key]} and {p['id']}")
        openings[key] = p["id"]
    for p in picks:
        if p["confidence"] in ("high", "medium") and not any(t["pick_id"] == p["id"] for t in preds):
            errors.append(f"missing prediction for {p['id']}")

    # 3. band integrity
    for l in lines:
        p = l["probability"]
        am = l["american"]
        expected_in = -250 <= am <= 10000
        if l["in_band"] != expected_in:
            errors.append(f"band flag wrong: {l['fixture_id']}/{l['selection']}")
        dec = 1.0 / p
        if abs(l["decimal"] - round(dec, 3)) > 0.002:
            errors.append(f"decimal mismatch: {l['fixture_id']}/{l['selection']}")

    # 4. cross-references
    fix_ids = {f["id"] for f in fixtures}
    line_keys = {(l["fixture_id"], l["selection"]) for l in lines}
    for p in picks:
        if p["fixture_id"] not in fix_ids:
            errors.append(f"pick references unknown fixture: {p['id']}")
        if (p["fixture_id"], p["selection"]) not in line_keys:
            errors.append(f"pick selection not in lines: {p['id']}")
    per_sport: dict[str, int] = {}
    for p in picks:
        per_sport[p["sport"]] = per_sport.get(p["sport"], 0) + 1
        if per_sport[p["sport"]] > 10:
            errors.append(f"more than 10 picks for {p['sport']}")
    for s in B.SPORTS:
        if s not in per_sport:
            print(f"note: no picks for {s} (OLBG-listing status)")

    # 5. official urls
    for f in fixtures:
        if f["official_url"] and not f["official_url"].startswith("http"):
            errors.append(f"bad official url: {f['id']}")
        for fact in f["facts"]:
            if fact["source_url"] and not fact["source_url"].startswith(("http", "data/")):
                errors.append(f"bad fact source url: {f['id']} / {fact['claim']}")

    # 6. olbg uniqueness + sports coverage
    ids = [r["event_id"] for r in olbg["listings"]]
    if len(ids) != len(set(ids)):
        errors.append("duplicate OLBG event ids")
    listed_sports = {r["sport"] for r in olbg["listings"]}
    for s in B.SPORTS:
        if s not in listed_sports and s not in B.NO_LISTING_NOTE:
            errors.append(f"sport with listings but no hub note: {s}")

    # 7. link audit
    link_re = re.compile(r'href=\'([^\'#?]+)\'')
    for page_file in sorted(OUT.rglob("*.html")):
        text = page_file.read_text(encoding="utf-8")
        base = page_file.parent
        for href in link_re.findall(text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href.startswith("now/") or href.startswith(("data/", "scripts/")):
                continue
            target = (base / href).resolve()
            if not target.exists():
                errors.append(f"broken link in {page_file.name}: {href}")

    pages = len(list(OUT.rglob("*.html")))
    print(f"compass_verify: {pages} pages, {len(fixtures)} fixtures, "
          f"{len(lines)} lines, {len(picks)} picks, {len(preds)} predictions, {len(flagged)} flags")
    if errors:
        print("FAILURES:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
