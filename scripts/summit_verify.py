#!/usr/bin/env python3
"""Summit desk line-by-line verifier.

Fails on: missing official source for an originated fixture, price arithmetic that does not match the
published probability, a confidence label that contradicts its own probability, a band flag that
contradicts its own price, a prediction under 30 words or containing a prohibited word, a prediction
fact that is not present in the fixture capture, or a broken local link.
Run: python3 scripts/summit_verify.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "summit")
SITE = os.path.join(ROOT, "summit")
BANNED = re.compile(r"\b(model|models|modelled|modeled|modelling|modeling|verify|verified|verifies|\bverification)\b", re.I)
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
checks = []
errors = []


def ok(msg):
    checks.append(msg)


def fail(msg):
    errors.append(msg)


def american(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return int(round(-100.0 * p / (1 - p))) if p >= 0.5 else int(round(100.0 * (1 - p) / p))


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def fixture_value(f):
    return f.get("value") or f.get("text") or ""


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.cur, self.row, self.cell, self.in_cell = [], None, None, None, False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.cur = {"head": [], "rows": []}
        elif tag == "tr" and self.cur is not None:
            self.row = {"cells": [], "links": 0}
        elif tag in ("td", "th") and self.row is not None:
            self.in_cell = True
            self.cell = {"text": "", "links": 0, "head": tag == "th"}
        elif tag == "a" and self.cell is not None:
            self.cell["links"] += 1
            self.row["links"] += 1

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            target = self.cur["head"] if self.cell["head"] else self.row["cells"]
            target.append({"text": self.cell["text"].strip(), "links": self.cell["links"]})
            self.cell, self.in_cell = None, False
        elif tag == "tr" and self.row is not None:
            if self.row["cells"]:
                self.cur["rows"].append(self.row)
            self.row = None
        elif tag == "table" and self.cur is not None:
            self.tables.append(self.cur)
            self.cur = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if v and ((tag in ("a", "link") and k == "href") or (tag in ("script", "img") and k == "src")):
                self.targets.append(v)


def local_link_errors(root=SITE):
    errors = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            if not fn.endswith(".html"):
                continue
            path = Path(os.path.join(dirpath, fn))
            text = open(path, encoding="utf-8").read()
            rel = os.path.relpath(path, root)
            parser = Links()
            parser.feed(text)
            for href in parser.targets:
                url = urlsplit(href)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (path.parent / unquote(url.path)).resolve()
                if target.is_dir():
                    target /= "index.html"
                if not target.is_relative_to(root) or not target.is_file():
                    errors.append(f"{rel}: {href}")
    return errors


def main():
    M, L, P, PR, SRC, FLAG, AUD = (
        load("matches.json"), load("lines.json"), load("picks.json"),
        load("predictions.json"), load("sources.json"), load("flagged.json"), load("repo_audit.json"),
    )
    SOURCES = {s["key"]: s for s in SRC["sources"]}
    FIX = {m["id"]: m for m in M["fixtures"]}

    # 1. fixtures
    for m in M["fixtures"]:
        if m["sport"] not in SPORTS:
            fail(f"{m['id']}: sport outside the fifteen")
        if m["status"] == "originated":
            if not str(m.get("official_source_url", "")).startswith("https://"):
                fail(f"{m['id']}: originated fixture without https official source")
            if not m.get("facts"):
                fail(f"{m['id']}: originated fixture without facts")
            for f in m["facts"]:
                v = fixture_value(f)
                if not str(f.get("source_url", "")).startswith("https://"):
                    fail(f"{m['id']}: fact without https source -> {v[:60]}")
                if f.get("source_key") not in SOURCES:
                    fail(f"{m['id']}: fact cites unregistered source key {f.get('source_key')}")
        if m["status"] == "blank" and not m.get("note"):
            fail(f"{m['id']}: blank row without a stated reason")
    for s in SPORTS:
        if not any(m["sport"] == s for m in M["fixtures"]):
            fail(f"{s}: no fixture captured")
    ok(f"fixtures: {len(M['fixtures'])} rows; {sum(1 for m in M['fixtures'] if m['status']=='originated')} originated")

    # 2. lines
    HIGH_P, LOW_P = 0.70, 0.60
    for r in L["lines"]:
        p = round(r["probability"], 6)
        if not 0 < p < 1:
            fail(f"{r['id']}: probability out of range")
            continue
        if american(p) != r["fair_american"]:
            fail(f"{r['id']}: fair_american {r['fair_american']} != {american(p)} for p={p}")
        if abs(round(1 / p, 3) - r["fair_decimal"]) > max(0.002, 0.0005 * r["fair_decimal"]):
            fail(f"{r['id']}: fair_decimal inconsistent")
        if r["offered_decimal"] < r["fair_decimal"]:
            fail(f"{r['id']}: offered price shorter than fair price")
        band = -250 <= r["fair_american"] <= 10000
        if band != r["in_band"]:
            fail(f"{r['id']}: in_band flag contradicts its own price")
        c = r["confidence"]
        if c == "high" and p < HIGH_P:
            fail(f"{r['id']}: high label below 70%")
        if c == "low" and p >= LOW_P:
            fail(f"{r['id']}: low label at or above 60%")
        if r.get("band_line") and not (HIGH_P <= p <= 0.7144):
            fail(f"{r['id']}: band line outside 70.00-71.44%")
    ok(f"lines: {len(L['lines'])} prices; arithmetic, band flags and labels consistent")

    # 3. picks
    for p_ in P["picks"]:
        p = p_["probability"]
        if p_["confidence"] == "high" and p < HIGH_P:
            fail(f"{p_['id']}: high below 70%")
        if p_["in_band"] != (-250 <= p_["fair_american"] <= 10000):
            fail(f"{p_['id']}: band flag wrong")
        if p_.get("sport_rank") is not None and not (1 <= p_["sport_rank"] <= 5):
            fail(f"{p_['id']}: rank outside 1..5")
    ok(f"picks: {len(P['picks'])} selections")

    # 4. predictions
    openings = set()
    bodies = set()
    for pr in PR["predictions"]:
        if pr["word_count"] < 30:
            fail(f"{pr['id']}: {pr['word_count']} words")
        if len(pr["text"].split()) != pr["word_count"]:
            fail(f"{pr['id']}: word_count does not match text")
        if BANNED.search(pr["text"]) or BANNED.search(pr["headline"]):
            fail(f"{pr['id']}: prohibited word in reader-facing prose")
        if not pr["facts"]:
            fail(f"{pr['id']}: no linked facts")
        for f in pr["facts"]:
            if not f["source_url"].startswith("https://"):
                fail(f"{pr['id']}: fact without https source")
        fixture = FIX[pr["fixture_id"]]
        values = {fixture_value(f) for f in fixture["facts"]}
        for f in pr["facts"]:
            if f["claim"] not in values:
                fail(f"{pr['id']}: quoted fact not present in fixture capture -> {f['claim'][:60]}")
        op = " ".join(pr["text"].split()[:3]).lower()
        if op in openings:
            fail(f"{pr['id']}: duplicate opening")
        openings.add(op)
        if pr["text"] in bodies:
            fail(f"{pr['id']}: duplicate body")
        bodies.add(pr["text"])
        pick = next((x for x in P["picks"] if x["id"] == pr["pick_id"]), None)
        if pick is None:
            fail(f"{pr['id']}: prediction not attached to a pick")
        elif pick["selection"] != pr["selection"]:
            fail(f"{pr['id']}: selection drift")
        elif pick["probability"] != pr["probability"]:
            fail(f"{pr['id']}: probability drift")
        elif pick["fair_american"] != pr["fair_american"]:
            fail(f"{pr['id']}: price drift")
    ok(f"predictions: {len(PR['predictions'])}, min {PR['min_words']} words, unique openings/bodies")

    short = [p_ for p_ in P["picks"] if p_["confidence"] in ("high", "medium") and p_.get("sport_rank")]
    have = {pr["pick_id"] for pr in PR["predictions"]}
    missing = [p_["id"] for p_ in short if p_["id"] not in have]
    if missing:
        fail(f"shortlisted picks without prediction: {missing}")
    ok(f"prediction coverage: {len(short)} shortlisted picks, {len(have)} predictions")

    # 5. HTML
    errs = local_link_errors()
    for e in errs:
        fail(f"broken local link: {e}")
    ok(f"local links: {len(errs)} errors across {sum(1 for _,_,fs in os.walk(SITE) for f in fs if f.endswith('.html'))} HTML pages")

    if errors:
        for e in errors:
            print("FAIL", e)
        print(f"Summit verify: {len(errors)} errors, {len(checks)} checks")
        sys.exit(1)
    print(f"Summit verify: {len(checks)} checks, 0 errors")
    sys.exit(0)


if __name__ == "__main__":
    main()
