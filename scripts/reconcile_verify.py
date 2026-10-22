#!/usr/bin/env python3
"""Structural verifier for the /reconcile/ console.

Gates:
  1. every internal link and #fragment resolves to a file/anchor that exists;
  2. every data row on the reconciliation tables carries a source cell (a link or an
     explicit em dash, never an empty cell);
  3. the published counts on the landing page match data/reconcile/report.json;
  4. no upstream dataset outside data/reconcile/ is touched by the build.

Exit code 0 = clean. Any failure prints the offending items and exits 1.
"""

from __future__ import annotations

import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "reconcile")
DATA = os.path.join(ROOT, "data", "reconcile")

# Files the audit reads but must never write.
UPSTREAM = [
    "data/matches.json", "data/verified/matches.json", "data/board/matches.json",
    "data/forward/matches.json", "data/hub/matches.json", "data/slate/matches.json",
    "data/portal/matches.json", "data/final/matches.json", "data/desk/fixtures.json",
    "data/live/lines.json", "data/survey/lines.json",
]


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.tables = []          # list of list-of-cells for tbody rows
        self._in_tbody = False
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "tbody":
            self._in_tbody = True
        elif tag == "tr" and self._in_tbody:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        if tag == "a" and self._cell is not None and a.get("href"):
            self._cell.append("LINK:" + a["href"])

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.tables.append(self._row)
            self._row = None
        elif tag == "tbody":
            self._in_tbody = False


def load(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main() -> int:
    errors = []
    pages = []
    for base, _, files in os.walk(SITE):
        for name in files:
            if name.endswith(".html"):
                pages.append(os.path.join(base, name))

    anchor_index = {}
    parsed = {}
    for path in pages:
        c = Collector()
        c.feed(load(path))
        parsed[path] = c
        anchor_index[os.path.relpath(path, SITE)] = c.ids

    # 1. internal links + fragments
    for path, c in parsed.items():
        rel_dir = os.path.dirname(os.path.relpath(path, SITE))
        for href in c.links:
            if re.match(r"^(https?:)?//", href) or href.startswith("mailto:"):
                continue
            target, _, frag = href.partition("#")
            if not target:
                if frag and frag not in c.ids:
                    errors.append(f"{os.path.relpath(path, ROOT)}: missing anchor #{frag}")
                continue
            resolved = os.path.normpath(os.path.join(rel_dir, target))
            abs_target = os.path.normpath(os.path.join(SITE, resolved))
            if not os.path.exists(abs_target):
                errors.append(f"{os.path.relpath(path, ROOT)}: broken link {href}")
                continue
            if frag and abs_target in parsed and frag not in parsed[abs_target].ids:
                errors.append(f"{os.path.relpath(path, ROOT)}: missing anchor {href}")

    # 2. every data row carries a source cell on the audit tables
    must_cite = ["flagged.html", "non-fixtures.html", "spot-checks.html", "sources.html"]
    for name in must_cite:
        path = os.path.join(SITE, name)
        if path not in parsed:
            errors.append(f"missing page {name}")
            continue
        for i, row in enumerate(parsed[path].tables):
            if not row:
                continue
            last = row[-1]
            if not last:
                errors.append(f"{name}: table row {i + 1} has an empty source cell")

    # 3. published counts match the report
    report = json.load(open(os.path.join(DATA, "report.json"), encoding="utf-8"))
    rows_doc = json.load(open(os.path.join(DATA, "rows.json"), encoding="utf-8"))
    index_html = load(os.path.join(SITE, "index.html"))
    checks = {
        "rows": f"{report['totals']['rows']:,}",
        "distinct fixtures": f"{report['totals']['distinct_fixtures']:,}",
        "non-fixtures": str(report["totals"]["non_fixtures"]),
        "price conflicts": str(report["totals"]["price_conflicts"]),
        "grade conflicts": str(report["totals"]["confidence_conflicts"]),
    }
    for label, value in checks.items():
        if value not in index_html:
            errors.append(f"index.html does not publish {label} = {value}")
    if rows_doc["count"] != report["totals"]["rows"]:
        errors.append("rows.json count disagrees with report totals")

    # 4. upstream guard (informational unless a git ref is present)
    git = os.path.join(ROOT, ".git")
    if os.path.isdir(git):
        import subprocess
        out = subprocess.run(["git", "status", "--porcelain", "--"] + UPSTREAM,
                             cwd=ROOT, capture_output=True, text=True)
        dirty = [ln for ln in out.stdout.splitlines() if ln.strip() and "data/reconcile" not in ln]
        if dirty:
            errors.append("upstream dataset modified: " + "; ".join(dirty))

    if errors:
        print(f"FAILED — {len(errors)} structural error(s)")
        for e in errors[:50]:
            print("  -", e)
        return 1
    print(f"OK — {len(pages)} pages, {sum(len(c.tables) for c in parsed.values())} table rows, "
          f"all links resolve, all sources present, counts match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
