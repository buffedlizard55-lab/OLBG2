#!/usr/bin/env python3
"""Strict structural verifier for the /clarity/ desk.

Checks every published row, price, prediction and local link. Exits non-zero on the first
class of failure it finds, printing the offending identifiers.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clarity"
OUT = ROOT / "clarity"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
SLUG = {
    "Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union", "Cricket": "cricket",
    "Snooker": "snooker", "Darts": "darts", "Baseball": "baseball", "Gaelic Sports": "gaelic-sports",
    "Greyhounds": "greyhounds", "Tennis": "tennis", "Motor Racing": "motor-racing",
    "Handball": "handball", "Ice Hockey": "ice-hockey", "Basketball": "basketball",
    "Rugby League": "rugby-league",
}
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
fails: list[str] = []
checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.row = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.row = []
        elif tag == "a" and self.row is not None and d.get("href"):
            self.row.append(d["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "tbody":
            self.in_tbody = False


def reciprocal_american(p: float) -> int:
    if p >= 0.5:
        return -max(100, int(round(100.0 * p / (1.0 - p))))
    return max(100, int(round(100.0 * (1.0 - p) / p)))


def main() -> int:
    fx = load("fixtures.json")
    matches = load("matches.json")
    lines = load("lines.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    flags = load("flagged.json")
    sources = load("sources.json")
    audit = load("repo_audit.json")

    # ---------------------------------------------------------------- data scope
    ok(set(fx["sports"]) == set(SPORTS), "fixture document must declare exactly the fifteen sports")
    ok(all(m["sport"] in SPORTS for m in matches["matches"]), "every match row must be in the fifteen sports")
    ok(len(fx["fixtures"]) == matches["count"], "fixture and match counts must agree")
    ok(all(f["official_url"].startswith("https://") for f in fx["fixtures"]),
       "every fixture needs an https official_url")
    ok(all(f["facts"] for f in fx["fixtures"]), "every fixture needs at least one sourced fact")
    fact_total = sum(len(f["facts"]) for f in fx["fixtures"])
    for f in fx["fixtures"]:
        for fact in f["facts"]:
            ok(fact["source_url"].startswith("https://"), f"{f['id']}: fact without https source")
            ok(fact["source_key"] in {s["key"] for s in sources["sources"]},
               f"{f['id']}: fact source_key not in the register")
            ok(bool(fact["value"]), f"{f['id']}: empty fact value")

    # ---------------------------------------------------------------- pricing math
    for row in lines["lines"]:
        ok(row["american"] == reciprocal_american(row["probability"]),
           f"{row['fixture_id']}: price does not match probability for {row['selection']}")
        ok(row["in_band"] == (-250 <= row["american"] <= 10000),
           f"{row['fixture_id']}: in_band flag disagrees with the American price")
        ok(0 < row["probability"] < 1, f"{row['fixture_id']}: probability out of range")
        ok(row["basis"] == "originated", f"{row['fixture_id']}: non-originated basis inside the lines file")
    for row in picks["picks"]:
        ok(row["confidence"] in ("low", "medium", "high"), f"{row['id']}: bad confidence")
        ok(row["in_band"], f"{row['id']}: published pick outside the focus band")
        ok(row["american"] == reciprocal_american(row["probability"]),
           f"{row['id']}: pick price does not match its probability")
        ok(row["official_url"].startswith("https://"), f"{row['id']}: pick without official source")
        ok(row["sport"] in SPORTS, f"{row['id']}: pick outside the fifteen sports")
    ok(picks["high"] == sum(1 for p in picks["picks"] if p["confidence"] == "high"),
       "high-confidence count does not match the pick list")
    ok(picks["high_in_band"] == sum(1 for p in picks["picks"]
                                    if p["confidence"] == "high" and p["in_band"]),
       "high_in_band count does not match the pick list")

    # ---------------------------------------------------------------- prose rules
    openings, texts = set(), set()
    for p in preds["predictions"]:
        ok(p["words"] >= 30, f"{p['id']}: under 30 words")
        ok(p["words"] == len(p["text"].split()), f"{p['id']}: word count does not match the text")
        ok(not BANNED.search(p["text"]), f"{p['id']}: contains model/verified vocabulary")
        ok(not BANNED.search(p["headline"]), f"{p['id']}: headline contains banned vocabulary")
        ok(p["text"] not in texts, f"{p['id']}: duplicate prose")
        texts.add(p["text"])
        opening = " ".join(p["text"].split()[:5]).lower()
        ok(opening not in openings, f"{p['id']}: duplicate opening")
        openings.add(opening)
        ok(len(p["facts"]) >= 2, f"{p['id']}: fewer than two sourced facts")
        sticky = [w for w in re.findall(r"[A-Za-z]+", p["selection"]) if len(w) >= 4]
        ok(any(w.lower() in p["text"].lower() for w in sticky),
           f"{p['id']}: the selection is not named in the prose")
        ok(p["official_url"].startswith("https://"), f"{p['id']}: no official fixture link")
        ok(p["id"] == f"pred-{p['fixture_id']}", f"{p['id']}: id does not derive from the fixture")
    for sport in SPORTS:
        n = preds["by_sport"].get(sport, 0)
        ok(n <= max(5, sum(1 for p in preds["predictions"]
                           if p["sport"] == sport and p["confidence"] == "high")),
           f"{sport}: write-up count above the five-per-sport ceiling")

    # ---------------------------------------------------------------- pages and links
    pages = sorted(OUT.rglob("*.html"))
    ok(len(pages) >= 27, "expected at least 27 published pages")
    for page in pages:
        text = page.read_text(encoding="utf-8")
        ok("OLBG2" in text, f"{page.relative_to(ROOT)}: missing brand")
        ok("index.html" in text, f"{page.relative_to(ROOT)}: no link home")
    for sport in SPORTS:
        path = OUT / "sports" / f"{SLUG[sport]}.html"
        ok(path.exists(), f"missing sport page for {sport}")
        if path.exists():
            ok(sport in path.read_text(encoding="utf-8"), f"{sport} page does not name the sport")

    for name in ("index.html", "picks.html", "matches.html", "lines.html",
                 "flagged.html", "sources.html", "band.html"):
        parser = Rows()
        parser.feed((OUT / name).read_text(encoding="utf-8"))
        ok(parser.rows, f"{name}: no table rows found")
        for row in parser.rows:
            ok(any(h.startswith("https://") for h in row), f"{name}: a table row has no external source")

    phtml = (OUT / "predictions.html").read_text(encoding="utf-8")
    ok(phtml.count('class="pred"') == preds["count"], "predictions page must render every write-up")
    ok(phtml.count("https://") >= preds["count"] * 2, "predictions page must link sources per write-up")
    broken = []
    for page in pages:
        for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
            if href.startswith(("http", "mailto:", "#")):
                continue
            target = (page.parent / unquote(href.split("#")[0])).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append(f"{page.relative_to(ROOT)} -> {href}")
    ok(not broken, "broken local links: " + "; ".join(broken[:5]))

    # ---------------------------------------------------------------- flags and audit
    ok(flags["count"] >= 8, "flag list is implausibly short")
    ok(audit["count"] >= 5, "repo audit is implausibly short")
    blank = [m for m in matches["matches"] if m["status"] != "priced"]
    for m in blank:
        ok(m["blank_reason"], f"{m['id']}: blank row without a stated reason")

    print(f"clarity_verify: {checks} assertions, {len(fails)} failures, "
          f"{len(pages)} pages, {fact_total} sourced facts")
    if fails:
        for f in fails[:25]:
            print("  FAIL:", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
