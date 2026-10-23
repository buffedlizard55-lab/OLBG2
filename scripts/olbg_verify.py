#!/usr/bin/env python3
"""Structural, arithmetic, provenance, prose and link verification for /olbg/."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from olbg_model import american, log5

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "olbg"
OUT = ROOT / "olbg"
EXPECTED_SPORTS = [
    ("golf", "Golf"), ("volleyball", "Volleyball"), ("rugby-union", "Rugby Union"),
    ("cricket", "Cricket"), ("snooker", "Snooker"), ("darts", "Darts"),
    ("baseball", "Baseball"), ("gaelic-sports", "Gaelic Sports"),
    ("greyhounds", "Greyhounds"), ("tennis", "Tennis"),
    ("motor-racing", "Motor Racing"), ("handball", "Handball"),
    ("ice-hockey", "Ice Hockey"), ("basketball", "Basketball"),
    ("rugby-league", "Rugby League"),
]

checks = 0

def ok(condition, message):
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.targets.append(attrs[key])


def verify_data():
    source = load("source.json")
    matches = load("matches.json")["matches"]
    lines = load("lines.json")["lines"]
    picks = load("picks.json")["shortlists"]
    predictions = load("predictions.json")["predictions"]
    flags = load("flagged.json")["items"]
    sources = load("sources.json")["sources"]
    counts = load("summary.json")["counts"]
    ok([(s["slug"], s["name"]) for s in source["sports"]] == EXPECTED_SPORTS, "exact sport taxonomy/order")
    ok(len(source["sports"]) == 15, "exactly 15 categories")
    ok(len({e["id"] for e in matches}) == len(matches), "unique event ids")
    ok(len({x["id"] for x in lines}) == len(lines), "unique line ids")
    by_event = {e["id"]: e for e in matches}
    by_line = {x["id"]: x for x in lines}
    ok(all(e["sport"] in dict(EXPECTED_SPORTS) for e in matches), "known sport on every row")
    ok(all(e["provenance"] in {"active", "last_seen", "official_context"} for e in matches), "three-state provenance")
    ok(not any(e["provenance"] == "active" for e in matches), "zero active rows in this capture")
    ok(all(e["official_sources"] for e in matches), "official source on every event")
    ok(all(s["kind"] == "official" and urlsplit(s["url"]).scheme == "https" for e in matches for s in e["official_sources"]), "HTTPS official sources on every row")
    ok(all(e["olbg_url"] for e in matches if e["provenance"] == "last_seen"), "OLBG discovery link on every last-seen row")
    ok(all(not e["olbg_url"] for e in matches if e["provenance"] == "official_context"), "no implied OLBG membership on official-context rows")
    ok(all(e["market_note"] for e in matches), "market investigation note on every event")
    for event in matches:
        datetime.strptime(event["date"], "%Y-%m-%d")
        if event.get("start_utc"):
            datetime.strptime(event["start_utc"], "%Y-%m-%dT%H:%M:%SZ")
        if event["line"]:
            ok(event["line"]["primary"], "embedded match line is primary")
            ok(event["line"]["id"] in by_line, "embedded line is in lines.json")
        else:
            ok(event["blank_reason"], f"blank reason missing: {event['id']}")
            ok(any(f["id"] == "BLANK-" + event["id"] for f in flags), f"blank flag missing: {event['id']}")
    ok(not any("Bertola" in e["name"] or "Player Competing" in e["name"] for e in matches), "incomplete ATP row excluded")
    ok(not any("India Women" in e["name"] for e in matches), "unclean women's cricket date excluded")
    ok(not any(e["sport"] == "gaelic-sports" for e in matches), "conflicting GAA row not promoted")
    ok(not any(e["id"] == "f1-828" for e in matches), "unsupported championship date excluded")

    primaries = [x for x in lines if x["primary"]]
    ok(len(primaries) == sum(bool(e["line"]) for e in matches), "one primary line per priced match")
    for line in lines:
        event = by_event[line["event_id"]]
        p = line["probability"]
        ok(math.isfinite(p) and 0 < p < 1, f"probability range: {line['id']}")
        fair = american(Fraction(p).limit_denominator(10**12))
        ok(abs(fair - line["fair_american"]) <= 1, f"fair American arithmetic: {line['id']}")
        ok(abs(line["fair_decimal"] - 1/p) < 1e-9, f"fair decimal arithmetic: {line['id']}")
        ok(line["selection"] and line["method"] and line["formula"] and line["inputs"], f"line disclosure: {line['id']}")
        ok(line["market_price"] is None and line["market_price_source"] is None, f"no bookmaker quote substitution: {line['id']}")
        if line["confidence"] == "high":
            ok(line["primary"] and p > .70 and -250 <= line["fair_american"] <= 10000, f"high numeric gate: {line['id']}")
            ok(event["high_detail"], f"high detailed-evidence gate: {line['id']}")
        if p > .70 and -250 <= line["fair_american"] <= 10000 and line["confidence"] != "high":
            ok(any(f["id"] == "CAP-" + line["id"] for f in flags), f"cap flag missing: {line['id']}")
        if line["primary"]:
            ok(abs(line["away_probability"] + line["home_probability"] - 1) < 1e-12, f"two-way complement: {line['id']}")

    # Spot-check exact formulas independently of the rendered values.
    nhl = next(e for e in matches if e["id"] == "nhl-2026020166")
    nhl_inputs = source["inputs"]["nhl"]["teams"]
    mtl, chi = nhl_inputs["Montreal Canadiens"], nhl_inputs["Chicago Blackhawks"]
    expected = log5(Fraction(mtl["points"], 2*mtl["gp"]), Fraction(chi["points"], 2*chi["gp"]))
    ok(expected == Fraction(5, 7), "Montréal exact probability is 5/7")
    ok(abs(nhl["line"]["probability"] - float(expected)) < 1e-12, "Montréal line uses exact points percentages")
    ok(nhl["line"]["fair_american"] == -250, "Montréal fair price stays on the -250 boundary")
    nba = next(e for e in matches if e["id"] == "nba-0022600008")
    nba_inputs = source["inputs"]["nba"]["teams"]
    nyk, bos = nba_inputs["NYK"], nba_inputs["BOS"]
    expected_nba = log5(Fraction(nyk["road_w"], nyk["road_w"]+nyk["road_l"]), Fraction(bos["home_w"], bos["home_w"]+bos["home_l"]))
    ok(abs(nba["line"]["home_probability"] - (1-float(expected_nba))) < 1e-12, "Boston venue-split arithmetic")
    ok(nba["line"]["confidence"] == "high" and nba["line"]["probability"] > .70, "Boston high gate")

    for sport in EXPECTED_SPORTS:
        slug = sport[0]
        short = picks[slug]
        ok(short["count"] == len(short["lines"]) and short["count"] <= 5, f"top-five cap: {slug}")
        ok(short["shortfall"] == 5-short["count"], f"shortfall arithmetic: {slug}")
        ok(all(x["primary"] and x["sport"] == slug for x in short["lines"]), f"shortlist rows: {slug}")
        ordered = sorted(short["lines"], key=lambda x: (-{"high":3,"medium":2,"low":1}[x["confidence"]], -x["probability"], x["event_id"]))
        ok(short["lines"] == ordered, f"shortlist ranking: {slug}")

    high_lines = [x for x in primaries if x["confidence"] == "high"]
    ok(len(predictions) == len(high_lines), "one prediction per high primary selection")
    normalized = set()
    for pred in predictions:
        text = pred["text"]
        words = text.split()
        norm = re.sub(r"\W+", " ", text.lower()).strip()
        ok(len(words) >= 30 and pred["word_count"] == len(words), f"prediction length: {pred['event_id']}")
        ok(norm not in normalized, f"unique prediction: {pred['event_id']}")
        normalized.add(norm)
        ok(not re.search(r"\b(model|verified)\b", text, re.I), f"prohibited prediction word: {pred['event_id']}")
        ok(text.startswith("Bet ") and pred["selection"].lower() in text.lower(), f"explicit selection: {pred['event_id']}")
        ok(pred["official_sources"] and all(s["kind"] == "official" for s in pred["official_sources"]), f"prediction official links: {pred['event_id']}")
        ok(pred["event_id"] in {x["event_id"] for x in high_lines}, f"prediction only for high: {pred['event_id']}")

    flag_ids = [f["id"] for f in flags]
    ok(len(flag_ids) == len(set(flag_ids)), "unique flag ids")
    ok(all(f["links"] and f["detail"] and f["title"] for f in flags), "source-linked, explained flags")
    ok(all(urlsplit(s["url"]).scheme in {"https", "http"} for f in flags for s in f["links"]), "flag links use HTTP(S)")
    source_keys = {(s["kind"], s["url"], s["label"]) for s in sources}
    ok(len(source_keys) == len(sources), "unique source register")
    for event in matches:
        for item in event["official_sources"]:
            ok((item["kind"], item["url"], item["label"]) in source_keys, f"source registered: {event['id']}")

    expected_counts = {
        "events": len(matches), "sports": 15, "sports_with_rows": len({e["sport"] for e in matches}),
        "active": 0, "last_seen": sum(e["provenance"]=="last_seen" for e in matches),
        "official_context": sum(e["provenance"]=="official_context" for e in matches),
        "priced_matches": len(primaries), "blank_matches": len(matches)-len(primaries),
        "originated_markets": len(lines), "high": len(high_lines),
        "medium": sum(x["confidence"]=="medium" for x in primaries), "low": sum(x["confidence"]=="low" for x in primaries),
        "sources": len(sources), "manual_flags": len(source["flags"]), "predictions": len(predictions), "flags": len(flags),
    }
    ok(counts == expected_counts, f"summary counts differ: {counts} != {expected_counts}")
    return source, matches, lines, predictions, flags


def verify_html(matches):
    pages = sorted(OUT.rglob("*.html"))
    ok(len(pages) == 22, f"22 HTML pages expected, got {len(pages)}")
    for slug, _ in EXPECTED_SPORTS:
        ok((OUT / "sports" / f"{slug}.html").is_file(), f"category page: {slug}")
    all_match_text = (OUT / "matches.html").read_text(encoding="utf-8")
    for event in matches:
        ok(f'id="{event["id"]}"' in all_match_text, f"rendered event row: {event['id']}")
    for page in pages:
        text = page.read_text(encoding="utf-8")
        parser = Links()
        parser.feed(text)
        ok("Snapshot 2026-10-23T19:40:38Z" in text, f"visible cutoff: {page.name}")
        ok("Flagged for Review" in text, f"review navigation: {page}")
        for href in parser.targets:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (page.parent / unquote(parsed.path)).resolve()
            if target.is_dir():
                target /= "index.html"
            ok(target.is_relative_to(ROOT.resolve()) and target.is_file(), f"broken local link {page.relative_to(ROOT)} -> {href}")
            if parsed.fragment and target.suffix == ".html":
                target_parser = Links()
                target_parser.feed(target.read_text(encoding="utf-8"))
                ok(parsed.fragment in target_parser.ids, f"broken fragment {page.relative_to(ROOT)} -> {href}")


def main():
    source, matches, lines, predictions, flags = verify_data()
    verify_html(matches)
    print(f"OLBG verification passed: {checks} checks; {len(matches)} matches; {len(lines)} markets; {len(predictions)} predictions; {len(flags)} flags; 22 pages")


if __name__ == "__main__":
    main()
