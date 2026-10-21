#!/usr/bin/env python3
"""Small dependency-free GitHub Pages link and page smoke check."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "index.html", "sports.html", "markets.html", "methodology.html", "flagged.html",
    "sports/darts.html", "sports/snooker.html", "sports/handball.html",
    "sports/basketball.html", "sports/gaelic-football.html", "assets/styles.css",
]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.tables = 0
        self.rows = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "script" and attrs.get("src"):
            self.links.append(attrs["src"])
        if tag == "table":
            self.tables += 1
        if tag == "tr":
            self.rows += 1

errors = []
for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        errors.append(f"required file missing: {rel}")

pages = sorted(ROOT.rglob("*.html"))
parsed = {}
for page in pages:
    parser = PageParser()
    parser.feed(page.read_text(encoding="utf-8"))
    parsed[page] = parser

for page, parser in parsed.items():
    for link in parser.links:
        parts = urlsplit(link)
        if parts.scheme or parts.netloc:
            continue
        if not parts.path and not parts.fragment:
            continue
        dest = (page.parent / unquote(parts.path)).resolve() if parts.path else page.resolve()
        try:
            dest.relative_to(ROOT)
        except ValueError:
            errors.append(f"{page.relative_to(ROOT)}: local link escapes site: {link}")
            continue
        if not dest.is_file():
            errors.append(f"{page.relative_to(ROOT)}: broken local link: {link}")
            continue
        if parts.fragment and dest.suffix.lower() == ".html" and dest in parsed:
            if unquote(parts.fragment) not in parsed[dest].ids:
                errors.append(f"{page.relative_to(ROOT)}: missing fragment target: {link}")

# Event/line data tables must not be added with empty/missing provenance. At present
# there are deliberately no tables or event rows; actual records require review.
if any(p.tables for p in parsed.values()):
    errors.append("data tables need manual source-link/provenance verification before publication")

if errors:
    print("Site validation failed:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)
print(f"Site validation passed: {len(pages)} HTML pages, required assets present, local links resolve, no unreviewed data tables.")
