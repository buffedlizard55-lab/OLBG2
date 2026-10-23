#!/usr/bin/env python3
"""Structural audit for the /brief/ desk.

This is an audit of the *published artefacts*, not of the world. It cannot prove that
an external page said what a capture claims; it proves that every published row is
internally consistent, carries a source, and that no blank was silently filled.

Exit code 1 on any failure.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "brief"
BRIEF = ROOT / "brief"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
          "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
          "Handball", "Ice Hockey", "Basketball", "Rugby League"]

failures = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


def main():
    matches = json.loads((DATA / "matches.json").read_text())
    preds = json.loads((DATA / "predictions.json").read_text())
    sources = {s["key"]: s for s in json.loads((DATA / "sources.json").read_text())["sources"]}
    flags = json.loads((DATA / "flags.json").read_text())["flags"]
    fixtures = matches["fixtures"]

    # scope
    check({f["sport"] for f in fixtures} == set(SPORTS), "fixture sports do not match the 15 in scope")
    for s in SPORTS:
        check((BRIEF / "sports" / (s.lower().replace(" ", "-") + ".html")).exists(), f"missing sport page: {s}")

    # rows
    for f in fixtures:
        check(f["source_url"].startswith("https://"), f"{f['id']}: source is not https")
        check(f["source_key"] in sources, f"{f['id']}: source key not on the ledger")
        check(f["sport"] in SPORTS, f"{f['id']}: sport out of scope")
        check(bool(f["status"]), f"{f['id']}: no status")
        for m in f["markets"]:
            check(0.05 <= m["prob"] <= 0.95, f"{f['id']}: probability out of clamp range")
            check(m["in_band"] == (-250 <= int(m["american"].replace("+", "")) <= 10000),
                  f"{f['id']}: in_band flag disagrees with the American price")
            if m["prob"] >= 0.70:
                check(m["confidence"] == "high", f"{f['id']}: high-confidence label missing")
        if f["markets"]:
            check(bool(f.get("input_note")), f"{f['id']}: priced without a recorded input note")
        # two-way markets must sum to 1
        by_market = {}
        for m in f["markets"]:
            by_market.setdefault(m["market"], []).append(m)
        for name, group in by_market.items():
            if len(group) == 2 and ("Money line" in name):
                check(abs(sum(g["prob"] for g in group) - 1.0) < 1e-3,
                      f"{f['id']}: two-way market {name} does not sum to 1")
        if f["eligible"] and f["markets"]:
            for m in f["markets"]:
                if m["prob"] > 0.7143:
                    check(not f.get("pick") or f["pick"]["prob"] <= m["prob"], f"{f['id']}: pick exceeds the strongest")

    # predictions
    ids = {f["id"] for f in fixtures}
    seen = set()
    for p in preds["predictions"]:
        check(p["fixture_id"] in ids, f"{p['id']}: unknown fixture")
        check(p["words"] >= 30, f"{p['id']}: fewer than 30 words")
        for bad in ("model", "verified"):
            check(bad not in p["text"].lower(), f"{p['id']}: banned word {bad}")
        check(p["id"] not in seen, f"{p['id']}: duplicate id")
        seen.add(p["id"])
        check(not p["text"].strip().endswith(",") and len(p["text"]) > 200, f"{p['id']}: prose too short in characters")
        check(p["tier"] in "ABCD", f"{p['id']}: bad tier")

    # no prediction for an unpriced fixture
    priced_ids = {f["id"] for f in fixtures if f["markets"] and f["eligible"]}
    for p in preds["predictions"]:
        check(p["fixture_id"] in priced_ids, f"{p['id']}: fixture is not priced/upcoming")

    # flags
    ids_flag = {f["id"] for f in flags}
    for required in ("BR-01", "BR-02", "BR-03", "BR-04", "BR-08", "BR-09", "BR-10"):
        check(required in ids_flag, f"missing flag {required}")

    # html links
    broken = 0
    pages = list(BRIEF.rglob("*.html"))
    for page in pages:
        text = page.read_text()
        check('assets/style.css' in text or '../assets/style.css' in text, f"{page.name}: no stylesheet")
        for href in re.findall(r'href="([^"#]+)(?:#[^"]*)?"', text):
            if href.startswith(("http", "mailto")):
                continue
            if not (page.parent / href.split("#")[0]).resolve().exists():
                broken += 1
                failures.append(f"{page.relative_to(BRIEF)}: broken link {href}")
    check(broken == 0, "broken internal links")

    # every fixture row appears on its sport page
    for s in SPORTS:
        page = (BRIEF / "sports" / (s.lower().replace(" ", "-") + ".html")).read_text()
        n = sum(1 for f in fixtures if f["sport"] == s)
        check(f"<div class=\"k\">Fixtures</div><div class=\"v\">{n}</div>" in page,
              f"{s}: sport page fixture count does not match the data")

    print(f"brief verify: {checks} checks, {len(pages)} pages, {len(fixtures)} fixtures, "
          f"{len(preds['predictions'])} predictions, {len(failures)} failures")
    if failures:
        for f in failures[:40]:
            print("  FAIL", f)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
