"""Structural verifier for /canon/: link integrity + row-level source checks.

This checks internal consistency only (local links resolve, every table row
carries an https:// source link, every JSON invariant holds). It cannot and
does not verify an external fact; that verification is recorded by hand in
research/audit-3de6d2ed.md.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "canon"
SITE_DIR = ROOT / "canon"


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and ((tag in ("a", "link") and key == "href") or (tag in ("script", "img") and key == "src")):
                self.hrefs.append(value)


def check_local_links() -> list[str]:
    errors = []
    pages = list(SITE_DIR.rglob("*.html"))
    for page in pages:
        parser = LinkCollector()
        parser.feed(page.read_text())
        for href in parser.hrefs:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                if not href.startswith("https://"):
                    errors.append(f"{page.relative_to(ROOT)}: non-https external link {href}")
                continue
            if not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                errors.append(f"{page.relative_to(ROOT)}: broken local link {href}")
    return errors, len(pages)


def check_data() -> list[str]:
    errors = []
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
    preds = json.loads((DATA_DIR / "predictions.json").read_text())["predictions"]
    flags = json.loads((DATA_DIR / "flagged.json").read_text())["flags"]
    sources = json.loads((DATA_DIR / "sources.json").read_text())["sources"]

    excluded_terms = ["soccer", "football", "boxing", "ufc", "mma", "american football",
                       "hurling", "horse racing", "cycling", "special"]
    for m in matches:
        if not m["source_url"].startswith("https://"):
            errors.append(f"match {m['id']}: source_url is not https")
        sport_lower = m["sport_name"].lower()
        for term in excluded_terms:
            if term == "football" and "gaelic" in sport_lower:
                continue
            if term in sport_lower:
                errors.append(f"match {m['id']}: excluded sport leaked ({sport_lower})")
        for mk in m["markets"]:
            if not (0.0 < mk["probability"] < 1.0):
                errors.append(f"match {m['id']}: market probability out of range")
            if mk["confidence"] == "high":
                if not (mk["probability"] >= 0.70 and -250 <= mk["fair_american"] <= 10000):
                    errors.append(f"match {m['id']}: high confidence fails uniform odds-window gate")

    pred_texts = set()
    for p in preds:
        if len(p["prediction"].split()) < 30:
            errors.append(f"prediction {p['id']}: under 30 words")
        if p["prediction"] in pred_texts:
            errors.append(f"prediction {p['id']}: duplicate text")
        pred_texts.add(p["prediction"])
        if not (p["probability"] >= 0.70 and -250 <= p["fair_american"] <= 10000):
            errors.append(f"prediction {p['id']}: outside uniform odds-window gate")
        if not p["source_url"].startswith("https://"):
            errors.append(f"prediction {p['id']}: source_url not https")

    for f in flags:
        if not f["source_url"].startswith("https://"):
            errors.append(f"flag {f['id']}: source_url not https")

    unclassified = [s for s in sources if s["publisher"].startswith("UNCLASSIFIED")]
    if unclassified:
        errors.append(f"{len(unclassified)} unclassified source(s) in registry")

    return errors


def main():
    data_errors = check_data()
    link_errors, page_count = check_local_links()
    all_errors = data_errors + link_errors
    report = {
        "html_pages": page_count,
        "data_errors": len(data_errors),
        "local_link_errors": len(link_errors),
    }
    print("canon_verify.py:", json.dumps(report))
    for e in all_errors:
        print("ERROR:", e)
    if all_errors:
        sys.exit(1)
    print("canon_verify.py OK: 0 errors")


if __name__ == "__main__":
    main()
