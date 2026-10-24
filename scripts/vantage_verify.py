#!/usr/bin/env python3
"""Strict local source/price/prose/link checks for Vantage.

This is a structural and transcription-consistency verifier. A URL is not proof
that the linked external page still reports the same value after the dated read.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vantage"
SITE = ROOT / "vantage"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        for key in (("href",) if tag in ("a", "link") else ("src",) if tag in ("script", "img") else ()):
            if attrs.get(key):
                self.urls.append(attrs[key])


def checks():
    m, l, p = read("matches.json"), read("lines.json"), read("picks.json")
    f, pred = read("fixtures.json"), read("predictions.json")
    flags, sources, taxonomy = read("flagged.json"), read("sources.json"), read("olbg_taxonomy.json")
    olbg = json.loads((DATA / "captures" / "olbg_first_page.json").read_text(encoding="utf-8"))
    discovery = read("discovery.json")
    hurling = json.loads((DATA / "captures" / "olbg_hurling_first_page.json").read_text(encoding="utf-8"))
    assert set(SPORTS) == {h["sport"] for h in taxonomy["hubs"]}
    assert len(olbg["listings"]) == discovery["imported_first_page_rows"]
    assert discovery["independently_checked_hurling_rows"] == 1
    assert discovery["listings"] == [*olbg["listings"], hurling["listing"]]
    assert len(discovery["listings"]) == len(m["matches"]) == m["listings"]
    assert len({r["event_id"] for r in discovery["listings"]}) == len(discovery["listings"])
    assert m["confirmed"] == len(f["fixtures"]) == sum(x["official_confirmed"] for x in m["matches"])
    assert m["priced"] == l["fixtures"] == len(l["detail"])
    assert l["count"] == len(l["lines"])
    assert p["count"] == len(p["picks"]) == pred["count"] == len(pred["predictions"])
    assert flags["count"] == len(flags["flags"])
    assert sources["count"] == len(sources["sources"])
    assert pred["high"] == p["high"] == p["focused"] == 1
    assert m["unknown"] == len(m["matches"]) - m["confirmed"]
    assert olbg["first_page_only"] if "first_page_only" in olbg else taxonomy["first_page_only"]
    assert re.fullmatch(r"[a-f0-9]{64}", olbg["source_sha256"])
    manifest = read("captures/manifest.json")
    assert not manifest["raw_http_bodies_archived"]
    for capture in manifest["captures"]:
        path = DATA / capture["path"]
        assert path.is_file() and path.resolve().is_relative_to(DATA.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == capture["sha256"]
    original = ROOT / olbg["source_committed_file"]
    if original.exists():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == olbg["source_sha256"], "original first-page extract drifted"
    n = 25

    official_urls = {x["url"] for x in sources["sources"]}
    assert len(official_urls) == sources["count"]
    for r in f["fixtures"]:
        assert r["official_url"] in official_urls, r["id"]
        assert r["sport"] in SPORTS
        assert r["olbg_event_id"] in {x["event_id"] for x in discovery["listings"]}
        assert (r["home"] and r["date"] and r["official_url"].startswith("https://"))
        for fact in r["facts"]:
            assert fact["claim"] and fact["url"] in official_urls, r["id"]
        for u in r["extra_official_urls"]:
            assert u in official_urls, (r["id"], u)
        if r["stats"]:
            assert r["stats"]["input_url"] in official_urls
            for side in ("home", "away"):
                x = r["stats"][side]
                assert x["gp"] > 0 and all(v >= 0 for k, v in x.items() if k not in ("gp",)), r["id"]
        n += 1 + len(r["facts"]) + len(r["extra_official_urls"])

    by_fixture = {r["id"]: r for r in f["fixtures"]}
    for row in m["matches"]:
        assert row["sport"] in SPORTS
        assert row["review_target_url"].startswith("https://")
        assert row["olbg_event_url"].startswith("https://www.olbg.com/betting-tips/")
        if row["official_confirmed"]:
            assert row["id"] in by_fixture
            assert row["fixture_source_url"] in official_urls
            assert row["official_date"] == by_fixture[row["id"]]["date"]
            assert row["official_home"] == by_fixture[row["id"]]["home"]
        else:
            for key in ("official_home", "official_away", "official_date", "official_start_utc",
                        "official_venue", "fixture_source_url", "primary_selection", "primary_probability"):
                assert row[key] is None, (row["id"], key)
        if row["primary_selection"]:
            start = datetime.fromisoformat(row["official_start_utc"].replace("Z", "+00:00"))
            asof = datetime.fromisoformat(m["as_of_utc"].replace("Z", "+00:00"))
            assert start > asof + timedelta(minutes=90), row["id"]
            assert row["official_confirmed"]
            assert by_fixture[row["id"]]["stats"]
        else:
            assert row["primary_confidence"] is None
        n += 5

    line_by_id = {x["id"]: x for x in l["lines"]}
    assert len(line_by_id) == l["count"]
    group = {}
    for item in l["lines"]:
        assert 0 < item["probability"] < 1
        assert 1.001 <= item["fair_decimal"] <= 100000
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from vantage_model import american
        expected = american(item["probability"])
        # If rounding lands on exactly 50%, the true pre-rounding sign decides
        # whether +100 or -100 was written. Both are the same even-money price.
        assert (abs(item["fair_american"]) == 100 if item["probability"] == .5 else
                abs(expected - item["fair_american"]) <= 1), (item["id"], expected, item["fair_american"])
        assert item["fair_in_band"] == (-250 <= item["fair_american"] <= 10000)
        assert item["official_source_url"] in official_urls and item["stats_source_url"] in official_urls
        assert item["olbg_offered_price"] is None
        if item["observed_american"] is not None:
            assert item["sport"] == "Ice Hockey"
            assert item["observed_source_url"] in official_urls
            assert item["observed_in_band"] == (-250 <= item["observed_american"] <= 10000)
        else:
            assert item["observed_in_band"] is None
        group.setdefault(item["fixture_id"], {}).setdefault(item["market"], []).append(item)
        n += 8
    for fid, mk in group.items():
        assert len(mk) == 3, (fid, mk.keys())
        for label, outcomes in mk.items():
            assert len(outcomes) in (2, 3), (fid, label, len(outcomes))
            assert abs(sum(v["probability"] for v in outcomes) - 1) < 2e-5, (fid, label)
            n += 2

    # Recompute every originated market, not just the stored American conversion.
    from vantage_model import market_rows
    for d in l["detail"]:
        frow = by_fixture[d["fixture_id"]]
        detail, recomputed = market_rows(frow)
        assert detail == d["estimate"], frow["id"]
        for x in recomputed:
            assert x == line_by_id[x["id"]], x["id"]
            n += 1

    preview_by_pick = {r["pick_id"]: r for r in pred["predictions"]}
    assert len(preview_by_pick) == p["count"]
    pick_ids = set()
    for pick in p["picks"]:
        assert pick["id"] not in pick_ids
        pick_ids.add(pick["id"])
        assert pick["fixture_id"] in group
        assert pick["official_url"] in official_urls
        assert pick["olbg_offered_price"] is None
        textrow = preview_by_pick[pick["id"]]
        assert textrow["fixture_id"] == pick["fixture_id"]
        assert textrow["confidence"] == pick["confidence"]
        assert len(textrow["text"].split()) == textrow["word_count"] >= 30
        assert pick["selection"].casefold() in textrow["text"].casefold()
        assert re.search(r"\b(model|verified)\b", textrow["text"], re.I) is None
        assert textrow["injury_status"] is None
        assert len(textrow["sources"]) >= 2 and all(u in official_urls for u in textrow["sources"])
        n += 9
    assert len({x["text"] for x in pred["predictions"]}) == p["count"]
    assert len({" ".join(x["text"].lower().split()[:6]) for x in pred["predictions"]}) == p["count"]
    featured = [x for x in p["picks"] if x["confidence"] == "high" and x["fair_in_band"] and x["observed_in_band"] is True]
    assert len(featured) == p["focused"] and featured[0]["fixture_id"] == "nhl-2026020170"
    assert featured[0]["observed_american"] == -178 and featured[0]["fair_american"] == -238

    shortfalls = [f for f in flags["flags"] if f["category"] == "five-per-sport shortfall"]
    assert len(shortfalls) == len(SPORTS)
    unverified = {f["id"] for f in flags["flags"] if f["category"] == "unverified listing"}
    assert unverified == {f"V-ROW-{x['olbg_event_id']}" for x in m["matches"] if not x["official_confirmed"]}
    for item in flags["flags"]:
        assert item["official_url"].startswith("https://") and item["olbg_url"].startswith("https://")
        assert item["missing_fields"] and item["detail"]
        n += 3
    # Per-row source links and navigable local target files/fragments.
    pages = sorted(SITE.rglob("*.html"))
    assert len(pages) == 27, len(pages)
    parsers = {}
    for page in pages:
        h = Anchors()
        text = page.read_text(encoding="utf-8")
        h.feed(text)
        assert len(h.ids) == len(set(h.ids)), f"duplicate id in {page}"
        parsers[page] = h
        assert "Flagged for Review" in text or page.name in ("methodology.html",)
        for tbody in re.findall(r"<tbody>(.*?)</tbody>", text, flags=re.S | re.I):
            for row in re.findall(r"<tr\b[^>]*>.*?</tr>", tbody, flags=re.S | re.I):
                assert 'href="https://' in row, (page.relative_to(ROOT), row[:200])
                n += 1
    for page, h in parsers.items():
        for raw in h.urls:
            u = urlsplit(raw)
            if u.scheme or u.netloc:
                assert u.scheme in ("https", "data"), raw
                continue
            if not u.path:
                if u.fragment:
                    assert u.fragment in h.ids, (page, raw)
                continue
            target = (page.parent / unquote(u.path)).resolve()
            if target.is_dir():
                target /= "index.html"
            assert target.is_relative_to(ROOT) and target.is_file(), (page.relative_to(ROOT), raw)
            if u.fragment and target in parsers:
                assert unquote(u.fragment) in parsers[target].ids, (page.relative_to(ROOT), raw)
            n += 1
    assert "Started / archived" in (SITE / "assets" / "app.js").read_text()
    return dict(assertions=n, pages=len(pages), links=sum(len(v.urls) for v in parsers.values()),
                official_matches=m["confirmed"], priced_matches=m["priced"],
                originated_selections=l["count"], previews=p["count"], review_items=flags["count"])


if __name__ == "__main__":
    result = checks()
    print("vantage_verify: " + json.dumps(result, sort_keys=True) + " · 0 errors (structural only)")
