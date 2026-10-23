#!/usr/bin/env python3
"""Structural and factual checks for the /desk/ layer.

Fails loudly rather than publishing a board with a dangling link, a price that
does not follow from its probability, a row without a source, or a prediction
that breaks the writing rules.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "desk")
ERRORS = []
CHECKS = 0


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        ERRORS.append(msg)


def load(name):
    return json.load(open(os.path.join(ROOT, "data/olbgdesk", name)))


def main():
    inv = load("olbg_inventory.json")
    inputs = load("inputs.json")
    lines = load("lines.json")["lines"]
    preds = load("predictions.json")["predictions"]
    flags = load("flagged.json")["flags"]

    rows = [dict(zip(inv["header"], r)) for r in inv["rows"]]

    # --- data integrity ---
    check(len(rows) == 125, f"expected 125 OLBG rows, found {len(rows)}")
    check(len(inputs["fixtures"]) == 10, "expected 10 official fixtures")
    check(len(preds) == 6, "expected 6 predictions")
    check(len(flags) == 17, "expected 17 flags")
    for r in rows:
        check(r["event_id"] > 0, f"OLBG row without event id: {r['event']}")
        check(r["pct"] is not None and 0 <= r["pct"] <= 100, f"bad pct: {r}")
        check(r["tips"] <= r["total"], f"tips exceed total: {r['event']}")
    check(not any(r["sport"] == "Golf" for r in rows), "Golf must have no rows (OLBG: No tips found)")

    # --- price arithmetic ---
    for l in lines:
        dec = round(1.0 / l["p"], 2)
        check(abs(dec - l["fair_decimal"]) < 0.02,
              f"{l['fixture']}: fair decimal {l['fair_decimal']} does not equal 1/{l['p']}")
        expect_band = 1.40 <= l["fair_decimal"] <= 101.00
        check(l["in_band"] == expect_band, f"{l['fixture']}: band flag wrong")
        check(l["confidence"] in ("high", "medium", "low"), "bad confidence label")
        check((l["confidence"] == "high") == (l["p"] >= 0.70),
              f"{l['fixture']}: confidence does not follow the 70% rule")
        check(l["basis"] in ("official", "consensus"), "bad basis")
        if l["basis"] == "consensus":
            check(l.get("sample", 0) > 0, "consensus price without a tip sample")

    official = [l for l in lines if l["basis"] == "official"]
    check(len(official) == 48, f"expected 48 NHL markets, got {len(official)}")
    check(len(lines) == len(official) + len(rows),
          "market-count reconciliation failed")

    # --- every official fixture resolves to a governing-body URL ---
    for f in inputs["fixtures"]:
        check(f["src"].startswith("https://"), f"{f['sid']} missing https source")
        check("olbg.com" not in f["src"], f"{f['sid']} cites OLBG as a governing body")

    # --- predictions ---
    seen = set()
    for p in preds:
        words = len(re.findall(r"[A-Za-z0-9'\-]+", p["text"]))
        check(words >= 30, f"{p['selection']}: {words} words")
        check(p["words"] == words, f"{p['selection']}: stored word count wrong")
        low = p["text"].lower()
        for banned in ("model", "verified", "algorithm", "projection"):
            check(banned not in low, f"{p['selection']}: banned word '{banned}'")
        opening = p["text"].split()[0]
        check(opening not in seen, f"duplicate opening '{opening}'")
        seen.add(opening)
        check(p["sources"], f"{p['selection']}: no source")
        for u in p["sources"]:
            check(u.startswith("https://") and "olbg.com" not in u, f"{p['selection']}: bad source {u}")
        # every number quoted in prose must exist in the stored fact list
        for num in re.findall(r"\b\d+(?:\.\d+)?\b", p["text"]):
            check(any(num in fact for fact in p["facts"]),
                  f"{p['selection']}: number {num} is not in the stored facts")
        # the selection must be a real market on the board
        check(any(l["sid"] == p["sid"] and l["selection"] == p["selection"] and l["market"] == p["market"]
                  for l in lines), f"{p['selection']}: prediction not backed by a priced market")
        check(any(l["sid"] == p["sid"] and l["confidence"] == "high" for l in lines),
              f"{p['selection']}: prediction written for a non-high-confidence selection")

    # --- flags ---
    for f in flags:
        check(f["source"].startswith("https://"), f"{f['id']} missing https source")
        check(len(f["finding"]) > 40, f"{f['id']} finding too short to be useful")

    # --- pages and local links ---
    pages = []
    for base, _, files in os.walk(OUT):
        for fn in files:
            if fn.endswith(".html"):
                pages.append(os.path.join(base, fn))
    check(len(pages) == 25, f"expected 25 HTML pages, found {len(pages)}")

    for page in pages:
        body = open(page, encoding="utf-8").read()
        check("<h1>" in body and "</html>" in body, f"{page}: not a complete page")
        for href in re.findall(r'href="([^"]+)"', body):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            check(href not in ("",), f"{page}: empty href")
            target = os.path.normpath(os.path.join(os.path.dirname(page), href.split("#")[0]))
            check(os.path.exists(target), f"{page}: broken local link {href}")

    # --- every data table row carries a source ---
    for name in ("matches.html", "lines.html", "olbg.html"):
        body = open(os.path.join(OUT, name), encoding="utf-8").read()
        tbody = re.search(r"<tbody>(.*?)</tbody>", body, re.S)
        check(tbody is not None, f"{name}: no tbody")
        body_rows = re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.S)
        check(len(body_rows) > 0, f"{name}: no rows")
        for i, r in enumerate(body_rows):
            check("<a href=" in r, f"{name}: row {i+1} has no source link")

    # --- coverage claims on the landing page must match the data ---
    index = open(os.path.join(OUT, "index.html"), encoding="utf-8").read()
    check(f"<b>{len(rows)}</b><span>OLBG events listed</span>" in index, "landing KPI mismatch (rows)")
    check(f"<b>{len(lines)}</b><span>originated markets</span>" in index, "landing KPI mismatch (markets)")
    check(f"<b>{len([l for l in lines if l['confidence']=='high'])}</b><span>high-confidence picks</span>" in index,
          "landing KPI mismatch (high picks)")

    print(f"desk_verify: {CHECKS} checks, {len(ERRORS)} errors")
    for e in ERRORS:
        print("  FAIL:", e)
    if ERRORS:
        sys.exit(1)
    print("ALL CHECKS PASS")


if __name__ == "__main__":
    main()
