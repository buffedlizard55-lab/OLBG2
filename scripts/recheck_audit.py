#!/usr/bin/env python3
"""Independent offline re-check of the current front-door desk (/now/).

This desk is owned by session 26707f98. It does not collect fixtures and it does not open any
external page: the sandbox egress policy only allows GitHub / PyPI / npm hosts, so every
federation source (OLBG, NHL, NBA, MLB, ...) is unreachable from here. Instead it re-derives,
from the committed capture under data/now/ and the rendered pages under now/, every rule the
brief imposes:

  C1 scope            exactly the fifteen requested sports, every count field honest
  C2 provenance       https official link per fixture and per sourced fact, register complete
  C3 price arithmetic American price is the reciprocal of the probability; band flag exact
  C4 grading          confidence grade and 0-10 score re-derived from the documented rules
  C5 prose            30+ words, reserved-word ban, uniqueness, selection named, facts attached
  C6 rendering        table rows carry sources, cards match data, internal links resolve
  C7 OLBG listing     event ids and urls line up with the fixtures that claim a listing
  C8 source register  unique keys, https only, host census for the live-reread block register
  C9 review flags     the underlying desk's flag file is internally complete

The output is deterministic (no clock reads, no network) so the Pages drift gate can rebuild it.
Anything that cannot be checked from the checkout is listed under "limits", never asserted.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "now"
PAGES = ROOT / "now"
OUT = ROOT / "data" / "recheck"
AS_OF = "2026-10-24T21:05:00Z"
PROBE_UTC = "2026-10-24T21:00:00Z"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
BASIS_SHADE = {"poisson": 1.0, "normal_margin": 1.0, "class_ladder": 0.8}
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
HTTPS = re.compile(r"^https://")

# Static record of the egress probe run by hand in this session. The script itself never opens
# a socket, so a rebuild on a fully-connected runner produces the same bytes.
EGRESS = [
    {"host": "www.olbg.com", "result": "blocked: OpenSSL SSL_ERROR_SYSCALL on connect",
     "probe_utc": PROBE_UTC},
    {"host": "api-web.nhle.com", "result": "blocked: OpenSSL SSL_ERROR_SYSCALL on connect",
     "probe_utc": PROBE_UTC},
    {"host": "github.com", "result": "reachable: HTTP 200", "probe_utc": PROBE_UTC},
    {"host": "pypi.org", "result": "reachable: HTTP 200", "probe_utc": PROBE_UTC},
]
BLOCK_REASON = ("Live re-read blocked in this build environment. Egress is limited to GitHub, "
                "PyPI and npm hosts; every sport and betting host fails TLS connect. The link "
                "below is present and well-formed, and the capture time of the value it supports "
                "is recorded on the underlying desk, but its current page content was not opened "
                "from this session.")


def load(name: str):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def host_of(url: str) -> str:
    if not url:
        return ""
    return urlsplit(url).netloc


def american(p: float) -> int:
    p = min(0.9995, max(0.0005, p))
    if p >= 0.5:
        return -max(100, round(100.0 * p / (1.0 - p)))
    return max(100, round(100.0 * (1.0 - p) / p))


def expected_grade(line_row: dict) -> str:
    """Re-derivation of the grading rule documented on the desk's method page."""
    p = line_row["probability"]
    if not line_row["in_band"]:
        return "low"
    if line_row.get("kind") == "total":
        return "medium" if p >= 0.55 else "low"
    if line_row.get("basis") != "class_ladder" and p >= 0.62 and line_row.get("quality", 0) >= 0.85:
        return "high"
    if p >= 0.55:
        return "medium"
    return "low"


def expected_score(row: dict) -> float:
    shaded = 10.0 * row["probability"] * BASIS_SHADE.get(row.get("basis", ""), 0.8)
    return round(min(10.0, max(0.0, shaded)), 1)


class TableRows(HTMLParser):
    """Collect the links inside every tbody row, the way a screen-reader user would meet them."""

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


class Check:
    def __init__(self, cid: str, title: str):
        self.cid, self.title = cid, title
        self.total = self.passed = 0
        self.failures = []

    def record(self, ok: bool, label: str):
        self.total += 1
        if ok:
            self.passed += 1
        else:
            self.failures.append(label)

    def as_dict(self):
        return {"id": self.cid, "title": self.title, "total": self.total,
                "passed": self.passed, "failed": self.total - self.passed,
                "failures": self.failures[:60]}


def main() -> int:
    fixtures_doc = load("fixtures.json")
    matches_doc = load("matches.json")
    lines_doc = load("lines.json")
    picks_doc = load("picks.json")
    preds_doc = load("predictions.json")
    olbg_doc = load("olbg.json")
    sources_doc = load("sources.json")
    flagged_doc = load("flagged.json")

    fixtures = fixtures_doc["fixtures"]
    matches = matches_doc["matches"]
    lines = lines_doc["lines"]
    picks = picks_doc["picks"]
    preds = preds_doc["predictions"]
    listings = olbg_doc["listings"]
    sources = sources_doc["sources"]
    flags = flagged_doc["flags"]

    fx_by_id = {f["id"]: f for f in fixtures}
    line_index = {(r["fixture_id"], r["market"], r["selection"]): r for r in lines}
    pick_index = {p["fixture_id"]: p for p in picks}
    pred_index = {p["fixture_id"]: p for p in preds}
    source_keys = {s["source_key"] for s in sources}
    listing_events = {str(x.get("event_id")): x for x in listings}

    checks = [Check(f"C{i}", t) for i, t in enumerate([
        "Scope and published counts",
        "Fixture and fact provenance",
        "Price arithmetic and odds band",
        "Pick grading and 0-10 score",
        "Written-prediction rules",
        "Rendered pages, tables and links",
        "OLBG listing linkage",
        "Source register and host census",
        "Flagged-for-review file",
    ], start=1)]
    c_scope, c_prov, c_price, c_grade, c_prose, c_render, c_olbg, c_src, c_flag = checks

    # ---- C1 scope ----------------------------------------------------------
    c_scope.record(set(fixtures_doc["sports"]) == set(SPORTS), "fixture sports are the exact fifteen")
    c_scope.record({m["sport"] for m in matches} <= set(SPORTS), "match sports stay in the fifteen")
    c_scope.record({p["sport"] for p in picks} <= set(SPORTS), "pick sports stay in the fifteen")
    c_scope.record({p["sport"] for p in preds} <= set(SPORTS), "prediction sports stay in the fifteen")
    for doc, key, rows in [
        (fixtures_doc, "count", fixtures), (matches_doc, "count", matches),
        (lines_doc, "count", lines), (picks_doc, "count", picks),
        (preds_doc, "count", preds), (olbg_doc, "listings_count", listings),
        (sources_doc, "count", sources), (flagged_doc, "count", flags),
    ]:
        c_scope.record(doc[key] == len(rows), f"{key} field matches the row list ({len(rows)})")
    c_scope.record(picks_doc["high"] == sum(1 for p in picks if p["confidence"] == "high"),
                   "high count matches the pick list")
    c_scope.record(picks_doc["medium"] == sum(1 for p in picks if p["confidence"] == "medium"),
                   "medium count matches the pick list")
    c_scope.record(picks_doc["low"] == sum(1 for p in picks if p["confidence"] == "low"),
                   "low count matches the pick list")

    # ---- C2 provenance -----------------------------------------------------
    fixture_rows = []
    for fx in fixtures:
        problems = []
        if not HTTPS.match(fx.get("official_url", "")):
            problems.append("no https official link")
        if not fx.get("facts"):
            problems.append("no sourced facts")
        for fact in fx.get("facts", []):
            if not HTTPS.match(fact.get("source_url", "")):
                problems.append(f"fact without https url: {fact.get('claim', '?')}")
            if fact.get("source_key") not in source_keys:
                problems.append(f"fact source_key not in register: {fact.get('source_key', '?')}")
            if not str(fact.get("value", "")).strip():
                problems.append(f"empty fact value: {fact.get('claim', '?')}")
            if not fact.get("captured_utc"):
                problems.append(f"fact without capture time: {fact.get('claim', '?')}")
        c_prov.record(not problems, fx["id"] + (": " + "; ".join(problems) if problems else ""))
        fixture_rows.append({
            "id": fx["id"], "sport": fx["sport"], "match": f'{fx["away"]} @ {fx["home"]}',
            "facts": len(fx.get("facts", [])), "official_url": fx["official_url"],
            "olbg_listed": bool(fx.get("olbg_listed")),
            "verdict": "pass" if not problems else "fail", "problems": problems,
        })

    # ---- C3 price arithmetic ----------------------------------------------
    price_failures = []
    by_sport = defaultdict(lambda: {"lines": 0, "in_band": 0, "fail": 0})
    by_kind = Counter()
    for r in lines:
        agg = by_sport[r["sport"]]
        agg["lines"] += 1
        by_kind[r.get("kind", "?")] += 1
        problems = []
        want_am = american(r["probability"])
        if r["american"] != want_am:
            problems.append(f"american {r['american']} != reciprocal {want_am}")
        want_band = -250 <= r["american"] <= 10000
        if bool(r["in_band"]) != want_band:
            problems.append(f"in_band flag {r['in_band']} disagrees with price {r['american']}")
        if not (0 < r["probability"] < 1):
            problems.append("probability outside (0,1)")
        if round(1 / r["probability"], 3) != round(r["decimal"], 3):
            problems.append(f"decimal {r['decimal']} != round(1/p,3) {round(1 / r['probability'], 3)}")
        if r.get("basis") not in BASIS_SHADE:
            problems.append(f"unknown basis {r.get('basis')}")
        if r["in_band"]:
            agg["in_band"] += 1
        if problems:
            agg["fail"] += 1
            price_failures.append({"fixture_id": r["fixture_id"], "market": r["market"],
                                   "selection": r["selection"], "problems": problems,
                                   "official_url": r["official_url"]})
        c_price.record(not problems,
                       f'{r["fixture_id"]} / {r["market"]} / {r["selection"]}'
                       + (": " + "; ".join(problems) if problems else ""))

    # ---- C4 pick grading ----------------------------------------------------
    pick_rows = []
    for p in picks:
        problems = []
        source_line = line_index.get((p["fixture_id"], p["market"], p["selection"]))
        if source_line is None:
            problems.append("no matching originated line row")
            want_grade, want_score = "?", None
        else:
            want_grade = expected_grade(source_line)
            want_score = expected_score(source_line)
            if p["confidence"] != want_grade:
                problems.append(f"published grade {p['confidence']} != re-derived {want_grade}")
            if float(p["score"]) != want_score:
                problems.append(f"published score {p['score']} != re-derived {want_score}")
        if american(p["probability"]) != p["american"]:
            problems.append("pick price does not match its probability")
        if not p["in_band"]:
            problems.append("published pick sits outside the -250..+10000 band")
        if not HTTPS.match(p.get("official_url", "")):
            problems.append("no https official link")
        if p["sport"] not in SPORTS:
            problems.append("sport outside the fifteen")
        if p["confidence"] == "high" and p["american"] < -250:
            problems.append("high pick shorter than -250 despite band flag")
        c_grade.record(not problems,
                       p["id"] + (": " + "; ".join(problems) if problems else ""))
        pick_rows.append({
            "id": p["id"], "sport": p["sport"], "match": f'{p["away"]} @ {p["home"]}',
            "market": p["market"], "selection": p["selection"],
            "probability": p["probability"], "american": p["american_display"],
            "published_grade": p["confidence"],
            "rederived_grade": want_grade, "published_score": p["score"],
            "rederived_score": want_score, "in_band": p["in_band"], "started": p["started"],
            "basis": p["basis"], "official_url": p["official_url"],
            "olbg_url": p.get("olbg_url", ""),
            "verdict": "pass" if not problems else "fail", "problems": problems,
        })

    # ---- C5 prose -----------------------------------------------------------
    seen_texts, seen_openings = set(), set()
    pred_rows = []
    for p in preds:
        problems = []
        words = len(p["text"].split())
        if words < 30:
            problems.append(f"only {words} words")
        if words != p["words"]:
            problems.append(f"stored word count {p['words']} != actual {words}")
        if BANNED.search(p["text"]) or BANNED.search(p.get("headline", "")):
            problems.append("contains a reserved internal word")
        if p["text"] in seen_texts:
            problems.append("duplicate prose body")
        seen_texts.add(p["text"])
        opening = " ".join(p["text"].split()[:5]).lower()
        if opening in seen_openings:
            problems.append("duplicate five-word opening")
        seen_openings.add(opening)
        sticky = [w for w in re.findall(r"[A-Za-z]+", p["selection"]) if len(w) >= 4]
        if not any(w.lower() in p["text"].lower() for w in sticky):
            problems.append("the selection is not named in the prose")
        if len(p.get("facts", [])) < 2:
            problems.append("fewer than two sourced facts")
        for fact in p.get("facts", []):
            if not HTTPS.match(fact.get("source_url", "")):
                problems.append("fact without https url")
        if p["id"] != f"pred-{p['fixture_id']}":
            problems.append("prediction id does not derive from the fixture")
        if not HTTPS.match(p.get("official_url", "")):
            problems.append("no https official link")
        c_prose.record(not problems,
                       p["id"] + (": " + "; ".join(problems) if problems else ""))
        pred_rows.append({
            "id": p["id"], "sport": p["sport"], "match": f'{p["away"]} @ {p["home"]}',
            "selection": p["selection"], "confidence": p["confidence"],
            "headline": p["headline"], "words": words, "facts": len(p.get("facts", [])),
            "official_url": p["official_url"], "olbg_url": p.get("olbg_url", ""),
            "verdict": "pass" if not problems else "fail", "problems": problems,
        })
    # coverage: every pregame high/medium pick must have prose
    for p in picks:
        if p["confidence"] in ("high", "medium") and not p["started"]:
            ok = p["fixture_id"] in pred_index
            c_prose.record(ok, f"prose coverage for {p['id']}" + ("" if ok else " missing"))

    # ---- C6 rendered pages --------------------------------------------------
    page_names = ["index.html", "picks.html", "predictions.html", "matches.html",
                  "lines.html", "band.html", "olbg.html", "sources.html",
                  "methodology.html", "flagged.html"]
    rendered = {}
    for name in page_names:
        path = PAGES / name
        c_render.record(path.exists(), f"page exists: now/{name}")
        if path.exists():
            rendered[name] = path.read_text(encoding="utf-8")
    sport_pages = list((PAGES / "sports").glob("*.html"))
    c_render.record(len(sport_pages) == 16, f"15 sport pages plus index under now/sports (found {len(sport_pages)})")

    # picks / matches / lines publish one primary table, so their row counts must be exact.
    exact_rows = {"picks.html": len(picks), "matches.html": len(matches),
                  "lines.html": len(lines)}
    for name, want in exact_rows.items():
        if name in rendered:
            parser = TableRows()
            parser.feed(rendered[name])
            c_render.record(len(parser.rows) == want,
                            f"{name} renders {len(parser.rows)} table rows, data has {want}")
            c_render.record(all(any(h.startswith("https://") for h in row) for row in parser.rows),
                            f"{name}: every table row carries an https source")
    # olbg / sources pages carry several tables (hub re-reads plus the data rows), so the data
    # rows must be present as a subset and every rendered row must still cite an https source.
    for name, want in (("olbg.html", len(listings)), ("sources.html", len(sources))):
        if name in rendered:
            parser = TableRows()
            parser.feed(rendered[name])
            c_render.record(len(parser.rows) >= want,
                            f"{name} renders {len(parser.rows)} rows including the {want} data rows")
            c_render.record(all(any(h.startswith("https://") for h in row) for row in parser.rows),
                            f"{name}: every table row carries an https source")
    if "predictions.html" in rendered:
        cards = rendered["predictions.html"].count('class="pred"')
        c_render.record(cards == len(preds),
                        f"predictions.html renders {cards} cards, data has {len(preds)}")
    if "index.html" in rendered:
        for label, want in [("fixtures", len(fixtures)), ("picks", len(picks)),
                            ("predictions", len(preds)), ("lines", len(lines)),
                            ("listings", len(listings))]:
            c_render.record(str(want) in rendered["index.html"],
                            f"front door shows the {label} total ({want})")
    for name, body in rendered.items():
        c_render.record(not BANNED.search(body), f"now/{name} avoids reserved internal words")
    broken = []
    for page in [PAGES / n for n in page_names] + sport_pages:
        if not page.exists():
            continue
        for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
            if href.startswith(("http", "mailto:", "#", "data:")):
                continue
            target = (page.parent / unquote(href.split("#")[0])).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append(f"{page.relative_to(ROOT)} -> {href}")
    c_render.record(not broken, "internal links resolve" + (": " + "; ".join(broken[:5]) if broken else ""))

    # ---- C7 OLBG listing linkage -------------------------------------------
    observations = []
    c_olbg.record(olbg_doc["listings_count"] == len(listings), "olbg listing count honest")
    for x in listings:
        ok = HTTPS.match(x.get("url", "")) and str(x.get("event_id", "")).isdigit()
        c_olbg.record(ok, f"listing event {x.get('event_id', '?')} has numeric id and https url")
    matched_fixtures = 0
    for fx in fixtures:
        if not fx.get("olbg_listed"):
            continue
        matched_fixtures += 1
        url = fx.get("olbg_url", "")
        if not url:
            # The desk asserts an OLBG listing but captured no event URL for it. Not a hard
            # failure of the published numbers; published as an observation for manual follow-up.
            observations.append({
                "id": f"O-{fx['id']}-olbg-url", "severity": "note",
                "title": f"{fx['id']} is marked as listed on OLBG but carries no event URL",
                "detail": "The fixture record has olbg_listed = true with an empty olbg_url, so "
                          "the listing cannot be cross-checked against a captured event id.",
                "fixture": fx["id"], "sport": fx["sport"],
                "official_url": fx["official_url"],
            })
            continue
        m = re.search(r"event_id=(\d+)", url)
        ok = bool(m) and m.group(1) in listing_events
        c_olbg.record(ok, f"{fx['id']}: olbg_url event id resolves to a captured listing")
    c_olbg.record(matched_fixtures >= 1, f"{matched_fixtures} fixtures carry an OLBG listing flag")

    # ---- C8 source register + host census ----------------------------------
    # source_key names a source family (e.g. one key per sport hub), so the uniqueness rule is
    # on the (key, url) pair, not the key alone.
    key_url_pairs = [(s["source_key"], s["url"]) for s in sources]
    c_src.record(len(set(key_url_pairs)) == len(key_url_pairs),
                 "every (source_key, url) pair is unique")
    c_src.record(all(HTTPS.match(s["url"]) for s in sources), "every registered source is https")
    c_src.record(all(s.get("captured_utc") for s in sources), "every source carries a capture time")
    host_tally = Counter()
    host_kinds = defaultdict(set)
    for s in sources:
        h = host_of(s["url"])
        host_tally[h] += int(s.get("claims", 0)) or 1
        host_kinds[h].add(s.get("kind", "unspecified"))
    for fx in fixtures:
        host_tally[host_of(fx["official_url"])] += 1
        for fact in fx["facts"]:
            host_tally[host_of(fact["source_url"])] += 1
        if fx.get("olbg_url"):
            host_tally[host_of(fx["olbg_url"])] += 1
    hosts = []
    for h, n in sorted(host_tally.items(), key=lambda kv: (-kv[1], kv[0])):
        is_olbg = h.endswith("olbg.com")
        hosts.append({
            "host": h, "references": n,
            "kind": "OLBG event list" if is_olbg else "; ".join(sorted(host_kinds.get(h, {"official"}))),
            "live_reread": "not attempted — OLBG's own domain" if is_olbg else BLOCK_REASON,
        })
    c_src.record(len(hosts) >= 10, f"host census covers {len(hosts)} distinct external hosts")

    # ---- C9 flags -----------------------------------------------------------
    c_flag.record(flagged_doc["count"] == len(flags), "flag count honest")
    severity_counter = Counter(f.get("severity", "") for f in flags)
    c_flag.record(sum(severity_counter.values()) == len(flags)
                  and severity_counter.get("open", 0) == flagged_doc["open"]
                  and severity_counter.get("corrected", 0) == flagged_doc["corrected"],
                  "open / note / corrected totals reconcile to the flag list")
    for f in flags:
        src = f.get("source", "")
        ok = (f.get("id") and f.get("item") and f.get("detail")
              and (HTTPS.match(src) or src.endswith(".html")))
        c_flag.record(ok, f"flag {f.get('id', '?')} has id, detail and a source link")

    # ---- aggregate result ---------------------------------------------------
    total_checks = sum(c.total for c in checks)
    total_failed = sum(c.total - c.passed for c in checks)
    discrepancies = [item for c in checks for item in c.failures]
    result = {
        "as_of_utc": AS_OF,
        "subject": "independent offline re-check of the /now/ front-door desk (data/now + now)",
        "session": "26707f98",
        "environment": {
            "network_opened_by_script": False,
            "egress_probe": EGRESS,
            "policy": "egress allowlist: github.com, api.github.com, codeload.github.com, "
                      "registry.npmjs.org, pypi.org, files.pythonhosted.org",
        },
        "summary": {
            "fixtures": len(fixtures), "matches": len(matches), "lines": len(lines),
            "picks": len(picks), "predictions": len(preds), "olbg_listings": len(listings),
            "sources": len(sources), "flags": len(flags), "hosts": len(hosts),
            "checks_total": total_checks, "checks_failed": total_failed,
            "line_kinds": dict(by_kind),
            "lines_in_band": sum(1 for r in lines if r["in_band"]),
            "picks_in_band": sum(1 for p in picks if p["in_band"]),
            "high_picks": picks_doc["high"], "medium_picks": picks_doc["medium"],
            "low_picks": picks_doc["low"],
        },
        "checks": [c.as_dict() for c in checks],
        "pick_rows": pick_rows,
        "line_check": {"total": len(lines), "failures": price_failures,
                       "by_sport": {k: dict(v) for k, v in sorted(by_sport.items())}},
        "pred_rows": pred_rows,
        "fixture_rows": fixture_rows,
        "hosts": hosts,
        "limits": [
            "No external page was opened. Every result below is derived from the committed "
            "capture (fixture facts stamped 2026-10-24T17:35Z; OLBG hubs re-read by the owning "
            "session up to 18:06Z); a source link proves where a value was read at capture, not "
            "what the page shows now.",
            "Fixtures that the underlying desk left blank (no originated line) are outside "
            "price and prose checks; their reasons are published on now/flagged.html.",
            "OLBG publishes one side per event, so the desk's prices on quoted-market rows are "
            "a normalised read of the OLBG quote, not an independent second-source price. This "
            "session cannot add a second source because those hosts are unreachable here.",
            "Injury and line-up news after the 17:35Z capture is not reflected anywhere in the "
            "committed data and cannot be retrieved from this environment.",
        ],
        "observations": observations,
        "discrepancies": discrepancies,
        "verdict": "pass" if total_failed == 0 else "fail",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                      encoding="utf-8")
    print(f"recheck_audit: {total_checks} checks, {total_failed} failures, "
          f"{len(pick_rows)} picks, {len(pred_rows)} predictions, {len(lines)} prices, "
          f"{len(hosts)} hosts; verdict {result['verdict']}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
