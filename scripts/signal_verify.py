#!/usr/bin/env python3
"""Signal desk (session 6b10ecda) - self-audit before publication.

Checks, in order:
  1. every capture file parses and names the official source it came from;
  2. every published fixture carries a source link;
  3. every fixture without a price carries at least one flag explaining it;
  4. two-way markets are fair (the sides sum to 1.00);
  5. every written preview is at least 30 words, unique, and free of the two
     words that must never appear in published prediction text;
  6. every flag carries a source link;
  7. every generated HTML page exists and every local link inside /signal/
     resolves to a file on disk.

Exit code 0 means the desk is safe to publish.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "signal")
SITE = os.path.join(ROOT, "signal")
BANNED = re.compile(r"\bmodel(s|led|ling)?\b|\bverified\b", re.I)

problems = []
checks = 0


def check(cond, message):
    global checks
    checks += 1
    if not cond:
        problems.append(message)


def load(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag in ("a", "link"):
            for k, v in attrs:
                if k == "href":
                    self.hrefs.append(v)


def main():
    # 1 - captures
    caps = sorted(glob.glob(os.path.join(DATA, "captures", "*.json")))
    check(len(caps) >= 15, "expected at least 15 capture files, found %d" % len(caps))
    for c in caps:
        with open(c, "r", encoding="utf-8") as fh:
            blob = json.load(fh)
        name = os.path.basename(c)
        check("source_url" in blob or "source_urls" in blob,
              "%s does not name its official source" % name)
        check("captured_utc" in blob, "%s has no capture timestamp" % name)

    matches = load("matches.json")["matches"]
    preds = load("predictions.json")["predictions"]
    flags = load("flagged.json")["flags"]
    sources = load("sources.json")["sources"]

    # 2, 3, 4
    for m in matches:
        check(bool(m["source_url"]), "%s has no source link" % m["id"])
        if not m["pick"] and m["status"] != "result":
            check(bool(m["flags"]), "%s has no price and no flag" % m["id"])
        two_way = {}
        for mk in m["markets"]:
            two_way.setdefault(mk["market"], []).append(mk["prob"])
        for name, probs in two_way.items():
            if len(probs) == 2:
                check(abs(sum(probs) - 1.0) < 0.02,
                      "%s market '%s' sums to %.3f" % (m["id"], name, sum(probs)))

    # 5
    seen = {}
    for p in preds:
        if not p["write_up"]:
            continue
        check(p["words"] >= 30, "%s write-up is only %d words" % (p["id"], p["words"]))
        check(not BANNED.search(p["write_up"]),
              "%s write-up uses a word that must not appear in published text" % p["id"])
        key = p["write_up"][:80].lower()
        check(key not in seen, "%s repeats the opening of %s" % (p["id"], seen.get(key)))
        seen[key] = p["id"]
        check(bool(p["source_url"]), "%s write-up has no source link" % p["id"])

    # 6
    for f in flags:
        check(bool(f["source_url"]), "flag %s has no source link" % f["id"])
        check(bool(f["detail"]), "flag %s has no detail" % f["id"])
    check(len(sources) >= 15, "only %d sources recorded" % len(sources))

    # 7
    pages = glob.glob(os.path.join(SITE, "*.html")) + \
        glob.glob(os.path.join(SITE, "sports", "*.html"))
    check(len(pages) >= 23, "expected 23 generated pages, found %d" % len(pages))
    for pg in pages:
        with open(pg, "r", encoding="utf-8") as fh:
            text = fh.read()
        check(not BANNED.search(re.sub(r"<[^>]+>", " ", text).replace(
            "Method", "").replace("methodology", "")) or "methodology" in pg,
            "%s contains a banned word in visible text" % os.path.basename(pg))
        parser = Links()
        parser.feed(text)
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(pg), href))
            check(os.path.exists(target),
                  "%s links to missing %s" % (os.path.relpath(pg, ROOT), href))

    print("signal_verify: %d checks run, %d problems" % (checks, len(problems)))
    for p in problems:
        print("  - " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
