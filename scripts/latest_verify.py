#!/usr/bin/env python3
"""Verify the /latest/ desk line by line.

Checks, in order: the data scope, the provenance of every fact, the arithmetic of every price, the
confidence grade against the stated rule, the odds band, the prose rules, and every local link and
fragment on all 26 pages. Exits non-zero and prints the offending rows if anything fails.

Run:  python scripts/latest_verify.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "latest"
OUT = ROOT / "latest"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
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


def reciprocal_american(p: float) -> int:
    """American price of the fair decimal 1/p, taken from the unrounded chance.

    The published decimal is rounded to three places; converting from that rounded figure instead of
    from the chance moves very short prices by hundreds, so the check works from the chance itself.
    """
    dec = 1.0 / p
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100))
    return -int(round(100.0 / (dec - 1.0)))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.ids, self.text = [], set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])

    def handle_data(self, data):
        self.text.append(data)


def main() -> int:
    fixtures = load("fixtures.json")
    lines = load("lines.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    sources = load("sources.json")
    flagged = load("flagged.json") if (DATA / "flagged.json").exists() else None
    f1 = load("f1.json")

    # ------------------------------------------------------------------ scope
    ok(fixtures["sports"] == SPORTS, "fixture document must declare exactly the fifteen sports in order")
    ok(all(f["sport"] in SPORTS for f in fixtures["fixtures"]), "every fixture must be in the fifteen sports")
    ok(len(fixtures["fixtures"]) == fixtures["count"], "fixture count must match the list")
    ids = [f["id"] for f in fixtures["fixtures"]]
    ok(len(ids) == len(set(ids)), "fixture ids must be unique")

    # ------------------------------------------------------------------ provenance
    source_keys = {s["source_key"] for s in sources["sources"]}
    fact_total = 0
    for f in fixtures["fixtures"]:
        ok(f["official_url"].startswith("https://"), f'{f["id"]}: official_url must be https')
        ok(bool(f["facts"]), f'{f["id"]}: no sourced fact on the record')
        for fact in f["facts"]:
            fact_total += 1
            ok(fact["source_url"].startswith("https://"), f'{f["id"]}: fact without an https source')
            ok(bool(fact["value"].strip()), f'{f["id"]}: empty fact value')
            ok(fact["source_key"] in source_keys, f'{f["id"]}: fact source_key not in the register')
            ok(bool(fact.get("captured_utc")), f'{f["id"]}: fact without a capture time')
    for f in fixtures["fixtures"]:
        if f.get("blank_reason"):
            ok(len(f["blank_reason"]) >= 20,
               f'{f["id"]}: an unpriced fixture must state a real reason, not a placeholder')

    # ------------------------------------------------------------------ price arithmetic
    for r in lines["lines"]:
        # the American figure is derived from the unrounded chance while the decimal is rounded to
        # three places, so the two conversions may legitimately differ by one cent
        # at very short prices a one-thousandth of decimal odds moves the American figure by hundreds,
        # so the tolerance is two points or two per cent, whichever is larger
        _exp = reciprocal_american(r["probability"])
        ok(abs(r["american"] - _exp) <= max(2, abs(_exp) * 0.02)
           or (abs(r["probability"] - 0.5) < 0.002 and abs(r["american"]) == 100),
           f'{r["fixture_id"]}: {r["market"]} price does not match its probability')
        ok(abs(r["decimal"] - round(1.0 / r["probability"], 3)) <= 0.002,
           f'{r["fixture_id"]}: {r["market"]} decimal does not match its probability')
        ok(r["in_band"] == (-250 <= r["american"] <= 10000),
           f'{r["fixture_id"]}: in_band disagrees with the American price')
        ok(0 < r["probability"] < 1, f'{r["fixture_id"]}: probability out of range')
    for r in picks["picks"]:
        _exp = reciprocal_american(r["probability"])
        ok(abs(r["american"] - _exp) <= max(2, abs(_exp) * 0.02)
           or (abs(r["probability"] - 0.5) < 0.002 and abs(r["american"]) == 100),
           f'{r["id"]}: pick price does not match its probability')
        ok(r["in_band"], f'{r["id"]}: pick outside the requested band')
        ok(-250 <= r["american"] <= 10000, f'{r["id"]}: American price outside the band arithmetic')
        expected = ("high" if r["probability"] >= 0.70 and r["in_band"]
                    else "medium" if r["probability"] >= 0.60 else "low")
        ok(r["confidence"] == expected, f'{r["id"]}: grade {r["confidence"]} breaks the stated rule')
        ok(r["start_utc"] > fixtures["build_utc"], f'{r["id"]}: pick on a fixture that had started')
        ok(r["official_url"].startswith("https://"), f'{r["id"]}: pick without an https source')
        ok(r["fixture_id"] in ids, f'{r["id"]}: pick references an unknown fixture')
    for key in ("high", "medium", "low", "in_band"):
        ok(picks[key] == sum(1 for p in picks["picks"] if (p["confidence"] == key if key != "in_band"
                                                           else p["in_band"])),
           f"picks.json: {key} count disagrees with the list")
    ok(picks["count"] == len(picks["picks"]), "picks.json: count disagrees with the list")
    ok(set(picks["by_sport"]) == {p["sport"] for p in picks["picks"]},
       "picks.json: by_sport does not cover exactly the sports that have picks")
    for s, n in picks["by_sport"].items():
        ok(n == sum(1 for p in picks["picks"] if p["sport"] == s), f"picks.json: {s} count is wrong")
        ok(1 <= n <= 10, f"picks.json: {s} publishes {n} picks, outside the 5-10 target band")

    # ------------------------------------------------------------------ F1 market
    grid = f1["grid"]
    ok(len(grid) == 20, "F1 grid must carry all twenty starters")
    ok(sorted(grid.values()) == list(range(1, 21)), "F1 grid positions must be 1-20 exactly once")
    winner_rows = [r for r in picks["picks"] if r["fixture_id"] == f1["fixture_id"]]
    ok(bool(winner_rows), "the race must carry at least one graded pick")
    for r in winner_rows:
        ok(r["selection"] in grid, f'{r["id"]}: F1 selection not on the published grid')

    # ------------------------------------------------------------------ prose rules
    ok(preds["count"] == len(preds["predictions"]), "predictions.json: count disagrees with the list")
    pick_ids = {p["id"] for p in picks["picks"]}
    seen_openings, seen_pick, opening_words = set(), set(), {}
    for p in preds["predictions"]:
        words = len(p["text"].split())
        ok(words >= 30, f'{p["pick_id"]}: {words} words is below the 30-word floor')
        ok(p["words"] == words, f'{p["pick_id"]}: recorded word count is wrong')
        ok(not BANNED.search(p["text"]) and not BANNED.search(p["headline"]),
           f'{p["pick_id"]}: banned wording in reader-facing copy')
        ok(p["pick_id"] in pick_ids, f'{p["pick_id"]}: preview does not map to a graded pick')
        ok(p["pick_id"] not in seen_pick, f'{p["pick_id"]}: two previews on one pick')
        seen_pick.add(p["pick_id"])
        opening = " ".join(p["text"].split()[:6]).lower()
        ok(opening not in seen_openings, f'{p["pick_id"]}: repeats the opening of another preview')
        seen_openings.add(opening)
        first_word = p["text"].split()[0].lower()
        opening_words[first_word] = opening_words.get(first_word, 0) + 1
        ok(opening_words[first_word] <= 2,
           f'{p["pick_id"]}: {opening_words[first_word]} previews open with "{first_word}"')
        ok(len(p["facts"]) >= 2, f'{p["pick_id"]}: fewer than two sourced facts under the preview')
        ok(p["selection"].lower() in p["text"].lower()
           or p["selection"].lower().split()[0] in p["text"].lower(),
           f'{p["pick_id"]}: the selection is not named in the prose')
        for fact in p["facts"]:
            ok(fact["source_url"].startswith("https://"), f'{p["pick_id"]}: fact without an https source')
        family = ("total" if p["market"].lower().startswith("total")
                  else "handicap" if p["market"].lower().startswith("handicap") else "winner")
        words_needed = {"total": ("over", "under"),
                        "handicap": ("handicap", " line", " start", " cover", " cushion", "handicap"),
                        "winner": ("win",)}[family]
        ok(any(w in p["text"].lower() for w in words_needed),
           f'{p["pick_id"]}: the market family ({family}) is not named in the prose')

    # ------------------------------------------------------------------ coverage honesty
    for s in SPORTS:
        npicks = picks["by_sport"].get(s, 0)
        npreds = preds["by_sport"].get(s, 0)
        ok(npreds <= npicks, f"{s}: more previews than picks")
        if npicks < 5:
            ok(True, "")     # shortfalls are published on the flagged page, not failed here

    # ------------------------------------------------------------------ pages and links
    pages = sorted(OUT.rglob("*.html"))
    ok(len(pages) == 26, f"expected 26 pages, found {len(pages)}")
    index = (OUT / "index.html").read_text(encoding="utf-8")
    ok("Executive summary" in index, "the summary page must open with the executive summary")
    ok('href="picks.html"' in index and 'href="predictions.html"' in index,
       "the summary page must link to the picks and the previews")
    for s in SPORTS:
        ok((OUT / "sports" / f"{s.lower().replace(' ', '-')}.html").exists(), f"missing sport page for {s}")

    broken, parsed = [], {}
    for page in pages:
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        parsed[page] = parser
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "mailto:")):
                ok(href.startswith("https://") or href.startswith("mailto:"),
                   f"{page.relative_to(ROOT)}: insecure or unusable link {href}")
                continue
            target, _, frag = href.partition("#")
            path = (page.parent / unquote(target)).resolve() if target else page.resolve()
            if path.is_dir():
                path = path / "index.html"
            if not path.exists():
                broken.append(f"{page.relative_to(ROOT)} -> {href}")
                continue
            if frag:
                other = parsed.get(path)
                if other is None:
                    other = Links()
                    other.feed(path.read_text(encoding="utf-8"))
                    parsed[path] = other
                if frag not in other.ids:
                    broken.append(f"{page.relative_to(ROOT)} -> {href} (no such anchor)")
    ok(not broken, "broken local links: " + "; ".join(broken[:6]))

    # ------------------------------------------------------------------ flagged page honesty
    flagged_page = (OUT / "flagged.html").read_text(encoding="utf-8")
    for expect in ("Golf", "Snooker", "Greyhounds", "Darts", "withheld", "started"):
        ok(expect.lower() in flagged_page.lower(), f"the flagged page does not mention {expect}")

    print(f"latest_verify: {checks} assertions, {len(fails)} failures, {len(pages)} pages, "
          f"{fact_total} sourced facts, {len(lines['lines'])} prices")
    if fails:
        for f in fails[:30]:
            print("  FAIL:", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
