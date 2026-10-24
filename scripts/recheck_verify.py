#!/usr/bin/env python3
"""Strict verifier for the /recheck independent audit desk.

It rebuilds the data and the pages, fails on any byte of drift, then re-checks the published
structure: every entity table row carries an https source, internal links resolve, reader-facing
copy avoids the two internal-only reserved words, and the recorded verdict has zero failures.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "recheck"
OUT = ROOT / "recheck"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
fails: list[str] = []
checks = 0


def ok(cond: bool, msg: str):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


class Rows(HTMLParser):
    """Rows grouped per table, so summary tables can be told apart from entity tables."""

    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.row = None
        self.tables = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "table":
            self.tables.append([])
        elif tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.row = []
        elif tag == "a" and self.row is not None and d.get("href"):
            self.row.append(d["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.tables[-1].append(self.row)
            self.row = None
        elif tag == "tbody":
            self.in_tbody = False


def snapshot(root: Path):
    return {p.relative_to(ROOT): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def main() -> int:
    before = {**snapshot(DATA), **snapshot(OUT)} if DATA.exists() and OUT.exists() else {}

    for script in ("recheck_audit.py", "recheck_build.py"):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / script)],
                             cwd=ROOT, text=True, capture_output=True)
        ok(run.returncode == 0, f"{script} exited {run.returncode}: {run.stdout}{run.stderr}")

    if before:
        after = {**snapshot(DATA), **snapshot(OUT)}
        ok(before == after, "rebuild changed generated files (not deterministic)")

    doc = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    ok(doc["verdict"] == "pass", "recorded verdict is not pass")
    ok(doc["summary"]["checks_failed"] == 0, "results carry failed checks")
    ok(all(c["failed"] == 0 for c in doc["checks"]), "a check class reports failures")
    s = doc["summary"]
    ok(len(doc["pick_rows"]) == s["picks"] == 39, "pick row count drift")
    ok(len(doc["pred_rows"]) == s["predictions"] == 36, "prediction row count drift")
    ok(len(doc["fixture_rows"]) == s["fixtures"] == 50, "fixture row count drift")
    ok(s["lines"] == 866, "price count drift")
    ok(len(doc["hosts"]) == s["hosts"], "host census count drift")

    pages = sorted(OUT.rglob("*.html"))
    ok(len(pages) == 8, f"expected 8 pages, found {len(pages)}")
    ok((OUT / "assets" / "style.css").exists(), "stylesheet missing")
    expected = {"index.html", "picks.html", "predictions.html", "lines.html", "fixtures.html",
                "sources.html", "flagged.html", "methodology.html"}
    ok({p.name for p in pages} == expected, "page set drift")

    for page in pages:
        text = page.read_text(encoding="utf-8")
        ok("OLBG2" in text, f"{page.name}: missing brand")
        ok("../index.html" in text, f"{page.name}: no link home")
        ok(not BANNED.search(text), f"{page.name}: contains a reserved internal word")

    # every entity table row must cite an https source. On lines.html the small by-sport
    # summary table is statistics rather than records, so the rule targets the full price table.
    for name in ("picks.html", "predictions.html", "fixtures.html", "sources.html"):
        parser = Rows()
        parser.feed((OUT / name).read_text(encoding="utf-8"))
        rows = [r for table in parser.tables for r in table]
        ok(bool(rows), f"{name}: no table rows found")
        ok(all(any(h.startswith("https://") for h in row) for row in rows),
           f"{name}: a table row has no https source")
    parser = Rows()
    parser.feed((OUT / "lines.html").read_text(encoding="utf-8"))
    full_tables = [t for t in parser.tables if len(t) == s["lines"]]
    ok(len(full_tables) == 1, "lines.html: one full per-price table expected")
    ok(all(any(h.startswith("https://") for h in row) for row in full_tables[0]),
       "lines.html: a price row has no https source")
    summary = [t for t in parser.tables if t is not full_tables[0]]
    want_summary = len(doc["line_check"]["by_sport"])
    ok(sum(len(t) for t in summary) == want_summary,
       f"lines.html: by-sport summary should hold {want_summary} rows")

    # internal links resolve
    broken = []
    for page in pages:
        for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
            if href.startswith(("http", "mailto:", "#", "data:")):
                continue
            target = (page.parent / unquote(href.split("#")[0])).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append(f"{page.relative_to(ROOT)} -> {href}")
    ok(not broken, "broken local links: " + "; ".join(broken[:5]))

    # observations are the documented three
    obs = doc["observations"]
    ok(len(obs) == 3 and all(o["severity"] == "note" for o in obs),
        "observation set drift")
    ok(all(o["official_url"].startswith("https://") for o in obs),
        "an observation lacks an official link")

    print(f"recheck_verify: {checks} assertions, {len(fails)} failures, "
          f"{len(pages)} pages, {s['checks_total']} underlying checks, verdict {doc['verdict']}")
    if fails:
        for f in fails[:25]:
            print("  FAIL:", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
