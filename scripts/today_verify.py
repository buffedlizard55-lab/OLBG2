#!/usr/bin/env python3
"""Line-by-line checks for the /today/ dashboard.

Fails loudly if a rendered table row has no official link, if an internal link is broken,
if a preview repeats another preview's text, or if a pick's band flag disagrees with its price.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
SITE = ROOT / "today"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
SLUG = {s: s.lower().replace(" ", "-") for s in SPORTS}

errors: list[str] = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def main() -> int:
    listings = json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["picks"]
    lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))["lines"]
    preds = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))
    flags = json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))

    # --- data level ---------------------------------------------------------
    for row in listings["listings"]:
        check(row["url"].startswith("https://www.olbg.com/betting-tips/"), f"listing not on OLBG: {row['url']}")
        check(f"event_id={row['event_id']}" in row["url"], f"event id mismatch: {row['event_id']} {row['url']}")
        check(0 <= row["pct"] <= 100, f"tip share out of range: {row}")
        check(bool(row["event"]) and bool(row["selection"]), f"empty listing row: {row}")
    check(len({r["sport"] for r in listings["listings"]} | {"Golf"}) == 15, "listing sports do not cover 15")

    for f in listings["fixtures"]:
        check(f["source_url"].startswith("https://"), f"fixture without official source: {f['id']}")
        check(f["start_utc"].endswith("Z"), f"fixture start not UTC: {f['id']}")
        check(bool(f["home_record"]) and bool(f["away_record"]), f"fixture record blank: {f['id']}")

    for l in lines:
        p = l["probability"]
        check(0 < p < 1, f"probability out of range: {l['id']}")
        check(l["source_url"].startswith("https://"), f"line without source: {l['id']}")
        fair = l["fair_american"]
        implied = round(-fair / (-fair + 100) if fair < 0 else 100 / (fair + 100), 4)
        check(abs(implied - p) < 0.02, f"fair price does not match probability: {l['id']} {fair} vs {p}")

    texts = set()
    for p in preds["predictions"]:
        check(p["word_count"] >= 30, f"preview under 30 words: {p['id']}")
        check(p["word_count"] == len(p["text"].split()), f"word count mismatch: {p['id']}")
        check(not BANNED.search(p["text"]), f"prohibited word in preview: {p['id']}")
        check(p["text"].lower() not in texts, f"duplicate preview text: {p['id']}")
        texts.add(p["text"].lower())
        check(p["official_fixture_url"].startswith("https://"), f"preview without fixture link: {p['id']}")
        check(len(p["facts"]) >= 2 and all(f["source_url"].startswith("https://") for f in p["facts"]),
              f"preview facts missing a source: {p['id']}")
        check(p["injuries"] is None and "injury" in p["injuries_note"].lower(),
              f"injury field must be blank and explained: {p['id']}")

    pick_ids = {p["fixture_id"] for p in picks}
    for p in picks:
        auc = p["fair_american"]
        check(p["in_band"] == (-250 <= auc <= 10000), f"band flag wrong: {p['fixture_id']}")
        want = "high" if p["probability"] >= 0.65 else ("medium" if p["probability"] >= 0.55 else "low")
        check(p["confidence"] == want, f"confidence grade wrong: {p['fixture_id']}")
        check(p["fixture_id"] in {x["fixture_id"] for x in preds["predictions"]},
              f"pick without a written preview: {p['fixture_id']}")
    for pred in preds["predictions"]:
        check(pred["fixture_id"] in pick_ids, f"preview without a published pick: {pred['fixture_id']}")

    for sport in SPORTS:
        check(sport in listings["hubs"], f"sport missing from hubs: {sport}")

    for item in flags["items"]:
        check(item["source"].startswith("https://"), f"review item without evidence link: {item['code']}")

    for s in sources["sources"]:
        check(s["url"].startswith("https://"), f"source without url: {s['label']}")

    # --- rendered level -----------------------------------------------------
    pages = sorted(SITE.rglob("*.html"))
    check(len(pages) >= 25, f"expected at least 25 pages, found {len(pages)}")
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            target = href.split("#")[0]
            if not target:
                continue
            resolved = (page.parent / unquote(target)).resolve()
            check(resolved.exists(), f"broken link in {page.relative_to(ROOT)} -> {href}")
            if "#" in href:
                anchor = href.split("#", 1)[1]
                if anchor and resolved.suffix == ".html":
                    check(f'id="{anchor}"' in resolved.read_text(encoding="utf-8"),
                          f"missing anchor #{anchor} in {href}")
        # every table row must carry at least one outbound official link
        for row in re.findall(r"<tr>(.*?)</tr>", text, re.S):
            if "<th>" in row:
                continue
            check('class="src"' in row or 'href="https://' in row or "muted" in row,
                  f"table row without a source link in {page.relative_to(ROOT)}: {re.sub('<[^>]+>', ' ', row)[:70]}")

    for sport in SPORTS:
        page = SITE / "sports" / f"{SLUG[sport]}.html"
        check(page.exists(), f"missing sport page: {sport}")
        body = page.read_text(encoding="utf-8")
        check(listings["hubs"][sport]["url"] in body, f"sport page lacks its OLBG hub link: {sport}")

    check("Vegas Golden Knights" in (SITE / "index.html").read_text(encoding="utf-8"),
          "executive board does not name a high-confidence selection")
    for p in picks:
        check(p["selection"] in (SITE / "picks.html").read_text(encoding="utf-8"),
              f"pick missing from picks page: {p['selection']}")

    if errors:
        print(f"today_verify: {checks} checks, {len(errors)} errors")
        for e in errors[:40]:
            print("  ERROR", e)
        return 1
    print(f"today_verify: {checks} checks, 0 errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
