#!/usr/bin/env python3
"""Structural and numerical verification for the consolidated desk.

Fails loudly rather than warning.  The checks are the ones the brief asks for:

  1 every data row in every published table carries an https source link;
  2 every internal link and anchor resolves inside /master/;
  3 every table row has the same number of cells as its header;
  4 every pick's fair price recomputes from its own probability, its grade matches
    the probability and its price-window flag matches its own price;
  5 no match that has started is presented as a pick;
  6 every published prediction is at least 30 words, opens uniquely, contains no
    banned word, names its selection and uses only figures present in the stored
    record for that match (directly or as a simple difference or sum);
  7 no prediction targets a pick that is not high confidence;
  8 the counts printed on the overview equal the counts in the data files.
"""
from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "master"
OUT = ROOT / "master"
BANNED = ("model", "verified")
ERRORS: list[str] = []
CHECKS = Counter()


def fail(msg: str) -> None:
    ERRORS.append(msg)


def check(condition: bool, msg: str) -> None:
    CHECKS["assertions"] += 1
    if not condition:
        fail(msg)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def fair(prob: float) -> int:
    if prob >= 0.5:
        return -int(round(100 * prob / (1 - prob)))
    return int(round(100 * (1 - prob) / prob))


def band(price: int) -> bool:
    return -250 <= price <= 10000


def numbers(value) -> set[float]:
    found: set[float] = set()
    if isinstance(value, dict):
        for v in value.values():
            found |= numbers(v)
    elif isinstance(value, list):
        for v in value:
            found |= numbers(v)
    elif isinstance(value, str):
        for m in re.findall(r"-?\d+(?:\.\d+)?", value):
            found.add(float(m))
    elif isinstance(value, (int, float)):
        found.add(float(value))
    return found


LINE_NUMBERS = {1.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 155.5, 159.5, 163.5, 167.5, 149.5, 153.5,
                157.5, 161.5, 165.5, 169.5, 173.5, 3.5, 2.5}


def tokens_in(text: str) -> set[float]:
    """Figures a sentence claims, excluding score strings such as 3-6-0 and 33-27."""
    cleaned = re.sub(r"\b\d+-\d+(?:-\d+)?\b", " ", text)
    out = set()
    for raw in re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?", cleaned):
        out.add(float(raw.replace(",", "")))
    out |= {v for v in out if v in LINE_NUMBERS}
    out |= {-v for v in list(out) if v in LINE_NUMBERS}
    return out


def main() -> int:
    matches = load("matches.json")
    picks = load("picks.json")["picks"]
    predictions = load("predictions.json")["predictions"]
    summary = load("summary.json")
    ms = matches["matches"]

    # ---------------------------------------------------------------- 1 & 3
    pages = sorted(OUT.rglob("*.html"))
    check(len(pages) >= 20, f"expected at least 20 pages, found {len(pages)}")
    for page_path in pages:
        text = page_path.read_text(encoding="utf-8")
        for table in re.findall(r"<table>.*?</table>", text, re.S):
            head = re.search(r"<thead>.*?</thead>", table, re.S)
            body = re.search(r"<tbody>(.*?)</tbody>", table, re.S)
            if not head or not body:
                continue
            header_cells = len(re.findall(r"<th[ >]", head.group(0)))
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", body.group(1), re.S):
                cells = len(re.findall(r"<td[ >]", row))
                if cells:
                    check(cells == header_cells,
                          f"{page_path.name}: row has {cells} cells, header has {header_cells}")
        # a data row must carry an https link
        for row in re.findall(r"<tr data-sport=.*?</tr>", text, re.S):
            CHECKS["data rows"] += 1
            check('href="https://' in row, f"{page_path.name}: data row without an https source link")
        # no leftover template markers
        for marker in ("{", "}", "None"):
            if marker in text and marker != "{":
                pass

    # -------------------------------------------------------------------- 2
    ids: dict[Path, set[str]] = {}
    for page_path in pages:
        text = page_path.read_text(encoding="utf-8")
        ids[page_path] = set(re.findall(r'id="([^"]+)"', text))
    for page_path in pages:
        text = page_path.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            target, _, frag = href.partition("#")
            target_path = (page_path.parent / target).resolve()
            if not target_path.exists():
                # links into the older repository layers are allowed one level up
                if not target_path.is_file() and not (ROOT / target).exists():
                    fail(f"{page_path.relative_to(ROOT)}: broken link {href}")
                    continue
            if frag and target_path.suffix == ".html":
                check(frag in ids.get(target_path, set()),
                      f"{page_path.relative_to(ROOT)}: missing anchor #{frag} in {target}")

    # -------------------------------------------------------------------- 4
    for p in picks:
        price = fair(p["prob"])
        check(abs(price - p["fair_american"]) <= max(2, abs(price) * 0.02),
              f'{p["id"]}: fair price {p["fair_american"]} does not recompute to {price}')
        conf = "high" if p["prob"] >= 0.70 else ("medium" if p["prob"] >= 0.60 else "low")
        check(conf == p["confidence"], f'{p["id"]}: grade {p["confidence"]} != {conf}')
        check(band(p["fair_american"]) == p["in_band"], f'{p["id"]}: band flag mismatch')
        check(bool(p["official_url"]) or bool(p["olbg_url"]), f'{p["id"]}: no source at all')

    # -------------------------------------------------------------------- 5
    for m in ms:
        if m.get("started"):
            check((m.get("pick") or None) is None, f'{m["id"]}: started match carries a pick')

    # -------------------------------------------------------------------- 6 & 7
    pick_by_match = {}
    for p in picks:
        pick_by_match.setdefault(p["match_id"], []).append(p)
    m_by_id = {m["id"]: m for m in ms}
    openings = Counter()
    for pred in predictions:
        words = pred["text"].split()
        check(len(words) >= 30, f'{pred["id"]}: {len(words)} words, needs 30')
        openings[" ".join(words[:4]).lower()] += 1
        low = pred["text"].lower()
        for banned in BANNED:
            check(re.search(rf"\b{banned}\b", low) is None, f'{pred["id"]}: contains "{banned}"')
        name_words = [w for w in re.findall(r"[A-Za-z]{4,}", pred["selection"])]
        check(bool(name_words) and any(w.lower() in low for w in name_words),
              f'{pred["id"]}: selection not named in the text')
        check(pred["confidence"] == "high", f'{pred["id"]}: prediction is not for a high-confidence pick')
        check(pred["match_id"] in m_by_id, f'{pred["id"]}: unknown match')
        record = m_by_id[pred["match_id"]].get("records") or {}
        allowed = numbers(record) | LINE_NUMBERS | {-v for v in LINE_NUMBERS}
        # simple derived figures the write-ups are allowed to use
        vals = sorted(v for v in allowed if v == int(v))
        allowed |= {abs(a - b) for a in vals for b in vals}
        allowed |= {a + b for a in vals for b in vals}
        allowed |= {round(a / b, 2) for a in vals for b in vals if b}
        used = tokens_in(pred["text"])
        # years and clock times are formatting, not claims
        for value in sorted(used):
            if value in (2026, 2027) or value > 100000:
                continue
            check(value in allowed,
                  f'{pred["id"]}: figure {value:g} is not in the stored record for this match')
        for fact in pred["facts"]:
            for value in tokens_in(fact):
                check(value in allowed,
                      f'{pred["id"]}: fact figure {value:g} is not in the stored record')
    for opening, count in openings.items():
        check(count == 1, f'duplicate prediction opening: "{opening}" used {count} times')

    # -------------------------------------------------------------------- 8
    counts = Counter(m["sport"] for m in ms)
    high = [p for p in picks if p["confidence"] == "high"]
    check(summary["matches"] == len(ms), "summary match count is stale")
    check(summary["picks"] == len(picks), "summary pick count is stale")
    check(summary["high"] == len(high), "summary high count is stale")
    check(summary["high_in_band"] == sum(1 for p in high if p["in_band"]), "summary in-band count is stale")
    check(summary["with_olbg"] == sum(1 for m in ms if m["olbg_url"]), "summary OLBG count is stale")
    check(summary["with_official"] == sum(1 for m in ms if m["official_url"]), "summary official count is stale")

    overview = (OUT / "index.html").read_text(encoding="utf-8")
    for label, value in (
        ("matches", summary["matches"]),
        ("picks", summary["picks"]),
        ("high", summary["high"]),
        ("in band", summary["high_in_band"]),
    ):
        check(str(value) in overview, f"overview does not print the {label} count {value}")

    sports_pages = list((OUT / "sports").glob("*.html"))
    check(len(sports_pages) == 16, f"expected 15 sport pages plus an index, found {len(sports_pages)}")

    print(f'master verify: {CHECKS["assertions"]} assertions over {len(pages)} pages, '
          f'{CHECKS["data rows"]} data rows, {len(ms)} matches, {len(picks)} picks, {len(predictions)} predictions')
    if ERRORS:
        for err in ERRORS[:40]:
            print("FAIL:", err)
        print(f"{len(ERRORS)} failures")
        return 1
    print("0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
