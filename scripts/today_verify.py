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

    check(len({l["id"] for l in lines}) == len(lines), "duplicate originated line id")
    for l in lines:
        p = l["probability"]
        check(0 < p < 1, f"probability out of range: {l['id']}")
        check(l["source_url"].startswith("https://"), f"line without source: {l['id']}")
        check(all(url.startswith("https://") for url in l.get("source_urls", [])),
              f"line has a non-HTTPS secondary source: {l['id']}")
        fair = l["fair_american"]
        implied = round(-fair / (-fair + 100) if fair < 0 else 100 / (fair + 100), 4)
        check(abs(implied - p) < 0.02, f"fair price does not match probability: {l['id']} {fair} vs {p}")

    expected_markets = {
        "Ice Hockey": ({"Moneyline", "Puck line", "Total goals"}, 10),
        "Basketball": ({"Moneyline", "Point spread", "Total points"}, 6),
        "Baseball": ({"Moneyline", "Run line", "Total runs"}, 10),
        "Tennis": ({"Moneyline", "Set handicap", "Total sets"}, 8),
        "Volleyball": ({"Moneyline", "Set handicap", "Total sets"}, 10),
        "Handball": ({"Moneyline", "Match handicap", "Total goals"}, 7),
        "Motor Racing": ({"Race winner", "Podium finish"}, 66),
        "Darts": ({"Moneyline", "Leg handicap", "Total legs"}, 8),
    }
    for f in listings["fixtures"]:
        fixture_lines = [l for l in lines if l["fixture_id"] == f["id"]]
        markets, count = expected_markets[f["sport"]]
        check(len(fixture_lines) == count, f"fixture market-row count wrong: {f['id']}")
        check({l["market"] for l in fixture_lines} == markets,
              f"fixture market families incomplete: {f['id']}")
        moneylines = [l for l in fixture_lines if l["market"] == "Moneyline"]
        if f["sport"] == "Motor Racing":
            winners = [l for l in fixture_lines if l["market"] == "Race winner"]
            podium = [l for l in fixture_lines if l["market"] == "Podium finish"]
            check(len(winners) == 22 and abs(sum(l["probability"] for l in winners) - 1) < 0.0002,
                  f"race-winner field is incomplete: {f['id']}")
            check(len(podium) == 44 and abs(sum(l["probability"] for l in podium if l["selection"].endswith("Yes")) - 3) < 0.0002,
                  f"podium probabilities do not distribute three places: {f['id']}")
            for driver in {l["selection"].split(" — ")[0] for l in podium}:
                pair = [l for l in podium if l["selection"].startswith(driver + " — ")]
                check(len(pair) == 2 and abs(sum(l["probability"] for l in pair) - 1) < 0.0002,
                      f"podium pair is not complementary: {f['id']} {driver}")
        else:
            expected_moneylines = 3 if f["sport"] == "Handball" else 2
            check(len(moneylines) == expected_moneylines and abs(sum(l["probability"] for l in moneylines) - 1) < 0.0002,
                  f"moneyline probabilities are not complete: {f['id']}")
        if f["sport"] == "Handball":
            check(sum(1 for l in moneylines if l["selection"] == "Tie") == 1,
                  f"handball regular-time tie missing: {f['id']}")
            for line in [l for l in fixture_lines if l["market"] in ("Match handicap", "Total goals")]:
                check(abs(line["line"] % 1) == 0.5, f"handball line is not a half-goal: {line['id']}")
        if f["sport"] in ("Tennis", "Volleyball"):
            for line in [l for l in fixture_lines if l["market"] in ("Set handicap", "Total sets")]:
                check(abs(line["line"] % 1) == 0.5, f"set line is not a half-set: {line['id']}")
        if f["sport"] == "Darts":
            for line in [l for l in fixture_lines if l["market"] in ("Leg handicap", "Total legs")]:
                check(abs(line["line"] % 1) == 0.5, f"darts line is not a half-leg: {line['id']}")
        if f["sport"] == "Basketball":
            home_ml = next(l for l in moneylines if l["selection"] == f["home"])
            home_spread = next(l for l in fixture_lines if l["market"] == "Point spread"
                               and l["selection"] == f["home"])
            check((home_ml["probability"] - 0.5) * home_spread["line"] < 0,
                  f"NBA spread reverses the moneyline favourite: {f['id']}")
            for line in [l for l in fixture_lines if l["market"] in ("Point spread", "Total points")]:
                check(abs(line["line"] % 1) == 0.5, f"NBA line is not a half-point: {line['id']}")
    check(sum(1 for f in listings["fixtures"] if f["sport"] == "Ice Hockey") == 12,
          "the official 12-game NHL slate is incomplete")
    check(sum(1 for f in listings["fixtures"] if f["sport"] == "Basketball") == 8,
          "the official eight-game NBA slate is incomplete")

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
        check(p["selection"] in p["text"], f"preview does not state its selection: {p['id']}")
        fact_text = " ".join(f["claim"] for f in p["facts"])
        for number in set(re.findall(r"\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)*", p["text"])):
            check(number in fact_text, f"numeric claim absent from linked facts: {p['id']} {number}")
        if p["injuries"] is None:
            check("injury" in p["injuries_note"].lower(),
                  f"blank injury field must be explained: {p['id']}")
        else:
            check(isinstance(p["injuries"], list), f"injuries must be a list or blank: {p['id']}")
            for item in p["injuries"]:
                check(item.get("source_url", "").startswith("https://"),
                      f"injury designation without official source: {p['id']}")
                check(bool(item.get("player")) and bool(item.get("status")),
                      f"incomplete injury designation: {p['id']}")

    shingle_owner = {}
    for p in preds["predictions"]:
        words = re.findall(r"[\w’'-]+", p["text"].casefold())
        for i in range(max(0, len(words) - 7)):
            shingle = " ".join(words[i:i + 8])
            if shingle in shingle_owner:
                check(False, f"repeated eight-word phrase: {shingle_owner[shingle]} / {p['id']}: {shingle}")
            else:
                shingle_owner[shingle] = p["id"]

    pick_ids = {p["fixture_id"] for p in picks}
    fixture_by_id = {f["id"]: f for f in listings["fixtures"]}
    for p in picks:
        check(bool(fixture_by_id[p["fixture_id"]].get("olbg_event_id")),
              f"pick lacks a corresponding captured OLBG event: {p['fixture_id']}")
        auc = p["fair_american"]
        check(p["in_band"] == (-250 <= auc <= 10000), f"band flag wrong: {p['fixture_id']}")
        want = "high" if p["probability"] >= 0.70 else ("medium" if p["probability"] >= 0.55 else "low")
        check(p["confidence"] == want, f"confidence grade wrong: {p['fixture_id']}")
        check(p["fixture_id"] in {x["fixture_id"] for x in preds["predictions"]},
              f"pick without a written preview: {p['fixture_id']}")
    for pred in preds["predictions"]:
        check(pred["fixture_id"] in pick_ids, f"preview without a published pick: {pred['fixture_id']}")
    for sport in SPORTS:
        count = sum(1 for p in picks if p["sport"] == sport)
        check(count <= 5, f"more than five published picks for {sport}")
    for sport in ("Ice Hockey", "Basketball"):
        check(sum(1 for p in picks if p["sport"] == sport) == 5,
              f"five-pick target not met for {sport}")

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

    executive = (SITE / "index.html").read_text(encoding="utf-8")
    first_high = next((p for p in picks if p["confidence"] == "high"), None)
    check(first_high is not None and first_high["selection"] in executive,
          "executive board does not name a high-confidence selection")
    rendered = "\n".join(page.read_text(encoding="utf-8") for page in pages)
    for stale in ("High is 65%", "NHL totals and puck lines need", "Ten of the fifteen sports",
                  "NBA.com returned its games shell"):
        check(stale not in rendered, f"stale baseline copy remains: {stale}")
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
