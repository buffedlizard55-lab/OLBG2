#!/usr/bin/env python3
"""Structural verification for the 26 October 2026 desk (session 9cf54b86).

Checks, in order: every page exists, every internal link resolves to a file on disk, every
fixture row carries an http source link, every pick is graded and every high pick is inside
the requested band, every preview is 30+ words with a unique opening and no banned wording,
every flagged item is published, and the root front door quotes the desk's own counts.

Run: python scripts/slate26_verify.py   (exit 0 = pass)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slate26"
OUT = ROOT / "slate26"

PAGES = ["index.html", "picks.html", "predictions.html", "matches.html", "lines.html", "band.html",
         "sources.html", "flagged.html", "outrights.html", "methodology.html", "sports/index.html"]
SPORTS = ["ice-hockey", "basketball", "tennis", "cricket", "handball", "volleyball", "gaelic",
          "baseball", "greyhounds", "motor-racing", "golf", "snooker", "darts", "rugby-union", "rugby-league"]
BANNED = ("model", "verified")

problems: list[str] = []
checks = 0


def check(cond: bool, message: str) -> None:
    global checks
    checks += 1
    if not cond:
        problems.append(message)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    fx, picks, preds, lines, flags = (load("fixtures.json"), load("picks.json"), load("predictions.json"),
                                      load("lines.json"), load("flagged.json"))

    # 1. pages exist
    all_pages = PAGES + [f"sports/{s}.html" for s in SPORTS]
    for name in all_pages:
        check((OUT / name).is_file(), f"missing page slate26/{name}")

    # 2. internal links resolve
    for name in all_pages:
        path = OUT / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        base = path.parent
        for href in re.findall(r'href="([^"#]+)(?:#[^"]*)?"', text):
            if href.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            target = (base / href).resolve()
            check(target.exists(), f"{name}: broken link {href}")

    # 3. every fixture row links a source
    for f in fx["fixtures"]:
        check(f["hub_url"].startswith("https://www.olbg.com/"), f'{f["id"]}: no OLBG source link')
        check(f["sport"] in SPORTS, f'{f["id"]}: unknown sport {f["sport"]}')

    # 4. picks
    check(picks["count"] == len(picks["picks"]), "pick count does not match the list")
    check(picks["count"] == fx["count"], "not every fixture has a pick")
    for p in picks["picks"]:
        check(p["confidence"] in {"high", "medium", "low"}, f'{p["fixture"]}: bad grade')
        check(p["price"] not in ("", None), f'{p["fixture"]}: no originated price')
        if p["confidence"] == "high":
            check(p["in_band"], f'{p["fixture"]}: high pick outside -250..+10000')
            check(p["tips"].split("/")[1].isdigit() and int(p["tips"].split("/")[1]) >= 4,
                  f'{p["fixture"]}: high pick on fewer than four tips')
        if p["selection"].strip().lower() in {"tie", "draw"}:
            check(p["confidence"] != "high", f'{p["fixture"]}: draw graded high')
    check(sum(1 for p in picks["picks"] if p["confidence"] == "high") == picks["high"], "high count mismatch")
    check(picks["in_band"] == sum(1 for p in picks["picks"] if p["in_band"]), "in-band count mismatch")

    # 5. lines
    check(lines["count"] == len(lines["lines"]), "line count mismatch")
    for l in lines["lines"]:
        check(l["probability"] is not None, f'{l["fixture"]}: line without probability')
        check(l["basis"] in {"official-input", "olbg-tip-share", "olbg-tip-share-thin"}, f'{l["fixture"]}: bad basis')
        check(-1400 <= int(l["price"]) <= 10000, f'{l["fixture"]}: implausible price {l["price"]}')

    # 6. predictions
    openings = set()
    pred_page = (OUT / "predictions.html").read_text(encoding="utf-8")
    for r in preds["predictions"]:
        check(len(r["text"].split()) >= 30, f'{r["fixture"]}: preview under 30 words')
        opening = " ".join(r["text"].split()[:5]).lower()
        check(opening not in openings, f'{r["fixture"]}: repeated opening')
        openings.add(opening)
        for word in BANNED:
            check(not re.search(rf"\b{word}", r["text"], re.I), f'{r["fixture"]}: banned word {word}')
        check(f'id="{r["fixture"]}"' in pred_page, f'{r["fixture"]}: no anchor on the predictions page')
        if r["tier"] == "full":
            check(bool(r["facts"]), f'{r["fixture"]}: full preview without facts')
            for fact in r["facts"]:
                check(fact["url"].startswith("http"), f'{r["fixture"]}: fact without a source link')
        else:
            check(not r["facts"], f'{r["fixture"]}: market preview carrying official facts')
    check(preds["count"] == len(preds["predictions"]), "prediction count mismatch")

    # 7. flagged items are published
    flag_page = (OUT / "flagged.html").read_text(encoding="utf-8")
    for item in flags["items"]:
        check(item["id"] in flag_page, f'{item["id"]}: not on the flagged page')
        check(item["source"].startswith("http"), f'{item["id"]}: flagged item without a source link')

    # 8. root front door
    root = (ROOT / "index.html").read_text(encoding="utf-8")
    check(f">{fx['count']}</div><div class=\"l\">upcoming matches" in root, "root: fixture count missing")
    check(f">{picks['count']}</div><div class=\"l\">picks still to start" in root, "root: pick count missing")
    check('href="slate26/picks.html"' in root, "root: no link to the picks page")
    check('href="slate26/predictions.html"' in root, "root: no link to the predictions page")
    check('href="slate26/flagged.html"' in root, "root: no link to the flagged page")

    if problems:
        print(f"slate26_verify: FAIL — {len(problems)} problem(s) over {checks} checks")
        for p in problems[:40]:
            print("  -", p)
        return 1
    print(f"slate26_verify: ok — {checks} checks over {len(all_pages)} pages, "
          f"{fx['count']} fixtures, {picks['count']} picks, {preds['count']} previews, {flags['count']} flags")
    return 0


if __name__ == "__main__":
    sys.exit(main())
