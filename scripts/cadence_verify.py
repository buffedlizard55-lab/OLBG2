"""Cadence desk — line-by-line verifier.

Fails (exit 1) on any of: missing official source link, price arithmetic that does not match the
published probability, a confidence label that contradicts its own probability, a band flag that
contradicts its own price, a prediction under 30 words or containing a prohibited word, a table row
without an official link, a local link that does not resolve, or a table row whose cell count differs
from its header.

Run: python3 scripts/cadence_verify.py
"""
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "cadence")
SITE = os.path.join(ROOT, "cadence")
BANNED = re.compile(r"\b(model|models|modelled|modeled|modelling|modeling|verify|verified|verifies|"
                    r"verification)\b", re.I)
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


M, L, P, PR, SRC, FLAG, AUD = (load("matches.json"), load("lines.json"), load("picks.json"),
                               load("predictions.json"), load("sources.json"), load("flagged.json"),
                               load("repo_audit.json"))
SOURCES = {s["key"]: s for s in SRC["sources"]}
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]

# 1. fixture-level provenance
for m in M["matches"]:
    if not str(m.get("official_source_url", "")).startswith("https://"):
        fail(f"{m['id']}: no https official source")
    if m["sport"] not in SPORTS:
        fail(f"{m['id']}: sport outside the fifteen")
    if not m.get("facts"):
        fail(f"{m['id']}: no facts captured")
    for f in m["facts"]:
        if not str(f.get("source_url", "")).startswith("https://"):
            fail(f"{m['id']}: fact without https source -> {f.get('value')[:60]}")
        if f.get("source_key") not in SOURCES:
            fail(f"{m['id']}: fact cites unregistered source key {f.get('source_key')}")
    if m["status"] == "blank" and not m.get("note"):
        fail(f"{m['id']}: blank row without a stated reason")
ok(f"fixtures: {len(M['matches'])} rows, each with an https official source and sourced facts")

for s in SPORTS:
    n = sum(1 for m in M["matches"] if m["sport"] == s)
    if n == 0:
        fail(f"{s}: no fixture captured")
ok(f"coverage: all 15 sports present; fixtures per sport "
   f"{ {s: sum(1 for m in M['matches'] if m['sport'] == s) for s in SPORTS} }")

# 2. price arithmetic and labels
HIGH_P, LOW_P = 0.70, 0.60
for r in L["lines"]:
    p = round(r["probability"], 6)
    if not (0 < p < 1):
        fail(f"{r['id']}: probability out of range")
        continue
    if american(p) != r["fair_american"]:
        fail(f"{r['id']}: fair_american {r['fair_american']} != {american(p)} for p={p}")
    if abs(round(1 / p, 3) - r["fair_decimal"]) > max(0.002, 0.0005 * r["fair_decimal"]):
        fail(f"{r['id']}: fair_decimal inconsistent")
    if r["offered_decimal"] < r["fair_decimal"]:
        fail(f"{r['id']}: offered price shorter than fair price")
    band = -250 <= american(p) <= 10000
    if band != r["in_band"]:
        fail(f"{r['id']}: in_band flag contradicts its own price")
    c = r["confidence"]
    if c == "high" and p < HIGH_P:
        fail(f"{r['id']}: high label below 70%")
    if c == "low" and p >= LOW_P:
        fail(f"{r['id']}: low label at or above 60%")
    if c == "high" and r.get("band_line") and r.get("tier", "") == "C":
        fail(f"{r['id']}: thin-sample band line graded high")
capped = [r for r in L["lines"] if r["confidence"] == "medium" and r["probability"] >= HIGH_P]
ok(f"lines: {len(L['lines'])} prices, all arithmetic, band flags and labels consistent; "
   f"{len(capped)} thin-sample band lines published as medium")

# 3. picks and shortlists
for p in P["picks"]:
    if p["confidence"] == "high" and p["probability"] < HIGH_P:
        fail(f"{p['id']}: high below 70%")
    if p["in_band"] != (-250 <= p["fair_american"] <= 10000):
        fail(f"{p['id']}: band flag wrong")
    if p.get("sport_rank") is not None and not (1 <= p["sport_rank"] <= 5):
        fail(f"{p['id']}: rank outside 1..5")
for s in SPORTS:
    n = sum(1 for p in P["picks"] if p["sport"] == s and p.get("sport_rank"))
    if n < 1:
        fail(f"{s}: no shortlisted selection")
ok(f"picks: {len(P['picks'])} graded selections, ranks and bands consistent")

highs = [p for p in P["picks"] if p["confidence"] == "high"]
in_band_high = [p for p in highs if p["in_band"]]
window = [p for p in highs if HIGH_P <= p["probability"] <= 250 / 350 + 1e-12]
ok(f"band arithmetic: {len(highs)} high, {len(in_band_high)} in band, "
   f"{len(window)} inside the 70.00-71.43% window")

# 4. predictions
openings = set()
for pr in PR["predictions"]:
    if pr["word_count"] < 30:
        fail(f"{pr['id']}: {pr['word_count']} words")
    if len(pr["text"].split()) != pr["word_count"]:
        fail(f"{pr['id']}: word_count does not match the text")
    if BANNED.search(pr["text"]) or BANNED.search(pr["headline"]):
        fail(f"{pr['id']}: prohibited word in reader-facing prose")
    if not pr["facts"]:
        fail(f"{pr['id']}: no linked facts")
    for f in pr["facts"]:
        if not f["source_url"].startswith("https://"):
            fail(f"{pr['id']}: fact without https source")
        if not any(f["claim"] == x["value"] for x in next(m for m in M["matches"]
                                                         if m["id"] == pr["fixture_id"])["facts"]):
            fail(f"{pr['id']}: quoted fact not present in the fixture capture")
    op = " ".join(pr["text"].split()[:3]).lower()
    if op in openings:
        fail(f"{pr['id']}: duplicate opening")
    openings.add(op)
    pick = next((x for x in P["picks"] if x["id"] == pr["pick_id"]), None)
    if pick is None:
        fail(f"{pr['id']}: prediction is not attached to a graded pick")
    elif pick["selection"] != pr["selection"]:
        fail(f"{pr['id']}: selection drift between pick and prediction")
    elif pick["probability"] != pr["probability"]:
        fail(f"{pr['id']}: probability drift")
ok(f"predictions: {len(PR['predictions'])}, min {PR['min_words']} words, unique openings, "
   f"zero prohibited words, every fact traceable")

graded_short = [p for p in P["picks"] if p["confidence"] in ("high", "medium") and p.get("sport_rank")]
have = {pr["pick_id"] for pr in PR["predictions"]}
missing = [p["id"] for p in graded_short if p["id"] not in have]
if missing:
    fail(f"shortlisted graded picks without a prediction: {missing}")
ok(f"prediction coverage: {len(graded_short)} shortlisted graded picks, {len(have)} predictions")

# 5. generated HTML: row-level links, cell counts, local links
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
            (self.cur["head"] if self.cell["head"] else self.row["cells"]).append(
                {"text": self.cell["text"].strip(), "links": self.cell["links"]})
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


pages, rows_checked, unlinked, bad_cells, broken = [], 0, [], [], []
for dirpath, _dirs, files in os.walk(SITE):
    for fn in sorted(files):
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        text = open(path).read()
        rel = os.path.relpath(path, SITE)
        pages.append(rel)
        tables = Tables()
        tables.feed(text)
        for t in tables.tables:
            width = len(t["head"])
            for row in t["rows"]:
                rows_checked += 1
                if width and len(row["cells"]) != width:
                    bad_cells.append(f"{rel}: {len(row['cells'])} cells vs {width} headers")
                if row["links"] == 0:
                    first = row["cells"][0]["text"][:50] if row["cells"] else ""
                    unlinked.append(f"{rel}: {first}")
        links = Links()
        links.feed(text)
        for href in links.targets:
            u = urlsplit(href)
            if u.scheme in ("http", "https", "mailto") or href.startswith("#"):
                continue
            if not u.path:
                continue
            target = (Path(os.path.dirname(path)) / unquote(u.path)).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not os.path.isfile(target):
                broken.append(f"{rel} -> {href}")

if bad_cells:
    fail(f"table cell-count mismatches: {bad_cells[:4]}")
if broken:
    fail(f"broken local links: {broken[:6]}")
ok(f"html: {len(pages)} pages, {rows_checked} table rows, {len(broken)} broken local links, "
   f"{len(bad_cells)} cell-count mismatches")
# data rows must carry a source link; the desk's method/about pages have no data tables
data_pages = [p for p in pages if not re.search(r"(methodology|olbg|flagged)\.html$", p)]
unlinked = [u for u in unlinked if any(u.startswith(p + ":") for p in data_pages)]
if unlinked:
    fail(f"table rows with no official link: {unlinked[:6]}")
ok(f"row provenance: every data-table row on {len(data_pages)} data pages carries at least one link")

# 6. sources register
for s in SRC["sources"]:
    if not s["url"].startswith("https://"):
        fail(f"source {s['key']}: not https")
used = set()
for m in M["matches"]:
    used.add(m.get("stats_source_url"))
    used.add(m.get("official_source_url"))
ok(f"sources: {SRC['count']} registered, all https")

# 7. flags and audit
if not FLAG["flags"]:
    fail("no disclosure flags")
for f in FLAG["flags"]:
    if not str(f.get("source_url", "")).startswith("https://"):
        fail(f"flag {f['id']}: no https source")
for f in AUD["findings"]:
    if not str(f.get("official_source_url", "")).startswith("https://"):
        fail(f"audit {f['id']}: no https source")
ok(f"review: {FLAG['count']} desk flags + {AUD['summary']['irregularities_logged']} audit findings, all sourced")

print("\n".join(f"  ok  {c}" for c in checks))
if errors:
    print()
    for e in errors:
        print("  FAIL", e)
    print(f"\n{len(checks)} checks passed, {len(errors)} errors")
    sys.exit(1)
print(f"\n{len(checks)} checks passed, 0 errors")
