#!/usr/bin/env python3
"""update_verify.py — verification gates for the /update/ layer (session arena/d69dc1c9-olbg2).

Checks, in order:
  1. every match row carries an official source URL (rows without one must be flagged);
  2. every rendered match/pick table row contains a source link;
  3. the high-confidence gate holds (prob >= 0.70 AND fair American in [-250, +10000]);
  4. in-band table only contains fair American inside the band;
  5. every high pick has a >= 30-word write-up;
  6. no originated line without a basis statement; never-originated rows must be flagged;
  7. all expected pages exist;
  8. dates of live rows inside the 22-28 Oct 2026 window.

Exit code 0 = all gates pass. Print PASS/FAIL per gate.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(ROOT, "data", "update")
OUT = os.path.join(ROOT, "update")
WIN_START, WIN_END = "2026-10-22", "2026-10-28"

EXPECTED_PAGES = ["index.html", "matches.html", "picks.html", "band.html", "sources.html",
                  "methodology.html", "flagged.html"] + [
    s + ".html" for s in ["tennis", "darts", "snooker", "golf", "cricket", "baseball", "basketball",
                          "ice-hockey", "rugby-union", "rugby-league", "handball", "volleyball",
                          "aussie-rules", "motor-racing", "esports", "greyhounds", "gaelic-football"]]


def load(name):
    return json.load(open(os.path.join(UPD, name)))


def main():
    failures = []
    matches = load("matches.json")["matches"]
    preds = load("predictions.json")["predictions"]
    band = load("band.json")["picks"]
    flags = load("flagged.json")["items"]
    flag_ids = {f.get("id") for f in flags}

    # 1 — source links on rows
    missing_src = [m["id"] for m in matches if not (m.get("official_url") or "").startswith("http")]
    ok1 = not missing_src
    print(("PASS" if ok1 else "FAIL") + f"  1. official source URL on every match row ({len(matches)} rows)"
          + (f" — missing: {missing_src[:5]}" if missing_src else ""))
    if not ok1:
        failures.append(1)

    # 2 — rendered tables carry source links
    bad_tables = []
    for path in sorted(glob.glob(os.path.join(OUT, "*.html"))):
        html = open(path).read()
        for row in re.findall(r"<tr>(.*?)</tr>", html, re.S):
            if "<th>" in row or "<td>" not in row:
                continue
            if "class=\"src\"" not in row and "class='src'" not in row and "official" not in row:
                bad_tables.append(os.path.basename(path))
                break
    ok2 = not bad_tables
    print(("PASS" if ok2 else "FAIL") + f"  2. every rendered table row has a source link"
          + (f" — offenders: {bad_tables[:5]}" if bad_tables else ""))
    if not ok2:
        failures.append(2)

    # 3 — high-confidence gate
    bad_high = []
    for p in preds:
        if p.get("confidence") == "high":
            if p.get("prob") is None or p["prob"] < 0.70 or not (-250 <= (p.get("american") or -99999) <= 10000):
                bad_high.append(p["id"])
    ok3 = not bad_high
    print(("PASS" if ok3 else "FAIL") + f"  3. high-confidence gate (>=70% and -250..+10000)"
          + (f" — violations: {bad_high[:5]}" if bad_high else ""))
    if not ok3:
        failures.append(3)

    # 4 — in-band table integrity
    bad_band = [p["id"] for p in band if not (-250 <= (p.get("american") or -99999) <= 10000)]
    ok4 = not bad_band
    print(("PASS" if ok4 else "FAIL") + f"  4. in-band table only fair American -250..+10000 ({len(band)} picks)"
          + (f" — violations: {bad_band[:5]}" if bad_band else ""))
    if not ok4:
        failures.append(4)

    # 5 — write-ups on high picks
    short = [p["id"] for p in preds
             if p.get("confidence") == "high" and len((p.get("writeup") or "").split()) < 30]
    ok5 = not short
    print(("PASS" if ok5 else "FAIL") + f"  5. high picks have >=30-word write-ups"
          + (f" — short: {short[:5]}" if short else ""))
    if not ok5:
        failures.append(5)

    # 6 — basis / flag discipline
    bad_basis = []
    for m in matches:
        if m.get("line_status", "").startswith("originated") and not m.get("basis"):
            bad_basis.append(m["id"])
        if m.get("line_status") == "not-originated" and m["id"] not in {f.get("id") for f in flags}:
            bad_basis.append(m["id"] + " (unflagged blank)")
    ok6 = not bad_basis
    print(("PASS" if ok6 else "FAIL") + f"  6. originated rows carry basis; blank rows are flagged"
          + (f" — violations: {bad_basis[:5]}" if bad_basis else ""))
    if not ok6:
        failures.append(6)

    # 7 — pages
    missing_pages = [p for p in EXPECTED_PAGES if not os.path.exists(os.path.join(OUT, p))]
    ok7 = not missing_pages
    print(("PASS" if ok7 else "FAIL") + f"  7. expected pages present ({len(EXPECTED_PAGES)} expected)"
          + (f" — missing: {missing_pages}" if missing_pages else ""))
    if not ok7:
        failures.append(7)

    # 8 — window discipline (in-window rows only; calendar notes excluded)
    bad_dates = [m["id"] for m in matches
                 if not (WIN_START <= (m.get("date") or "") <= WIN_END)]
    ok8 = not bad_dates
    print(("PASS" if ok8 else "FAIL") + f"  8. live rows inside 22-28 Oct window"
          + (f" — outside: {bad_dates[:5]}" if bad_dates else ""))
    if not ok8:
        failures.append(8)

    if failures:
        print("VERIFY FAIL on gates: " + ", ".join(map(str, failures)))
        return 1
    print(f"VERIFY PASS — {len(matches)} matches, {len(preds)} picks, {len(band)} in band, "
          f"{sum(1 for p in preds if p.get('confidence') == 'high')} high, {len(flags)} flagged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
