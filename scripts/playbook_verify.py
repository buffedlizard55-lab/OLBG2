#!/usr/bin/env python3
"""Playbook verifier: line-by-line checks on the desk and its data.

Fails loudly rather than publishing something that does not hold together. Checks:
  data      counts agree across files, every row carries a source, band arithmetic is right
  prose     >= 30 words, no banned vocabulary, no repeated 8-word run, selection named
  pages     every page exists, every internal link resolves, every pick row links to OLBG
  hygiene   no merge markers, no absolute local paths, no timestamps that would drift
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "playbook"
OUT = ROOT / "playbook"

FAILS: list[str] = []
CHECKS = 0


def ok(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def american(p: float) -> int:
    return int(round(-100.0 * p / (1.0 - p))) if p > 0.5 else int(round(100.0 * (1.0 - p) / p))


def main() -> int:
    fx_doc, picks_doc = load("fixtures.json"), load("picks.json")
    preds_doc, lines_doc = load("predictions.json"), load("lines.json")
    sources_doc, flags_doc = load("sources.json"), load("flagged.json")
    cap = json.loads((DATA / "olbg_capture.json").read_text())

    fixtures, picks = fx_doc["fixtures"], picks_doc["picks"]
    preds, lines = preds_doc["predictions"], lines_doc["lines"]
    source_urls = {s["url"] for s in sources_doc["sources"]}

    # ---------------------------------------------------------------- data basics
    ok(fx_doc["count"] == len(fixtures), "fixtures.json count does not match its list")
    ok(fx_doc["match_count"] == sum(1 for f in fixtures if f["olbg_event_id"]),
       "match_count does not match the rows that carry an OLBG id")
    ok(picks_doc["count"] == len(picks), "picks.json count does not match its list")
    ok(preds_doc["count"] == len(preds), "predictions.json count does not match its list")
    ok(lines_doc["count"] == len(lines), "lines.json count does not match its list")
    ok(fx_doc["tier_a"] + fx_doc["tier_b"] == len(fixtures), "tier counts do not add up")

    # every captured OLBG row must appear as a fixture
    ok(len(cap["rows"]) == sum(1 for f in fixtures if f["olbg_event_id"]),
       "the fixture set does not contain exactly the captured OLBG rows")
    ok(len(cap["outrights"]) == len(json.loads((DATA / "outrights.json").read_text())["outrights"]),
       "outright count drifted from the capture")

    # ------------------------------------------------------------------- sources
    for f in fixtures:
        if f["olbg_url"]:
            ok(f["olbg_url"] in source_urls, f"fixture {f['fid']} links to a URL missing from the register")
            ok(f["olbg_url"].startswith("https://www.olbg.com/betting-tips/"),
               f"fixture {f['fid']} OLBG link is not an OLBG event URL")
        ok(f.get("olbg_hub") in source_urls or f.get("olbg_hub") is None,
           f"fixture {f['fid']} hub missing from the register")
    for p in picks:
        ok(bool(p.get("source_url")), f"pick {p['pick_id']} carries no source link")
        ok(p.get("source_url") in source_urls, f"pick {p['pick_id']} source is not in the register")
    for p in preds:
        ok(bool(p["facts"]), f"prediction {p['pid']} carries no facts")
        for fact in p["facts"]:
            ok(fact["source"] in source_urls, f"prediction {p['pid']} cites {fact['source']} which is not registered")

    # ------------------------------------------------------------ price arithmetic
    for line in lines:
        for s in line["lines"]:
            pr, p = s["price"], s["probability"]
            ok(0 < p < 1, f"{line['event']}: probability out of range")
            if pr is not None:
                # the offered price must be no better than the fair price from the chance
                ok(pr <= american(p) + 1, f"{line['event']} {s['selection']}: offered price better than fair")
                ok(s["in_band"] == (-250 <= pr <= 10000), f"{line['event']} {s['selection']}: band flag wrong")
    for p in picks:
        ok(p["price"] is not None, f"pick {p['pick_id']} has no price")
        ok(p["in_band"] == (-250 <= p["price"] <= 10000), f"pick {p['pick_id']} band flag wrong")
        if p["confidence"] == "high":
            ok(p["in_band"], f"high pick {p['pick_id']} is outside the band")
            ok(p["tier"] == "A", f"high pick {p['pick_id']} has no official input")
            ok(p["probability"] >= 0.65, f"high pick {p['pick_id']} is under the 65% floor")
        ok(p["probability"] >= 0.5 or p["confidence"] == "low",
           f"pick {p['pick_id']} grades above low on a sub-50% chance")

    # --------------------------------------------------------------------- prose
    banned = ("model", "verified", "verification", "algorithm")
    words = {}
    for p in preds:
        text = p["text"]
        n = len(re.findall(r"[A-Za-z0-9'+.-]+", text))
        words[p["pid"]] = n
        ok(n >= 30, f"{p['pid']} is only {n} words")
        ok(n == p["words"], f"{p['pid']} stored word count is wrong")
        low = text.lower()
        for w in banned:
            ok(w not in low, f"{p['pid']} uses the banned word '{w}'")
        compact = re.sub(r"[^a-z0-9]", "", low)
        named = [tok for tok in re.findall(r"[A-Za-z0-9]+", p["selection"].lower()) if len(tok) >= 4]
        ok(any(tok in compact for tok in named), f"{p['pid']} never names its selection")
        ok(str(p["price"]) in text or f"{p['price']}" in text, f"{p['pid']} never states its price")

    def shingles(t: str) -> set[str]:
        w = re.findall(r"[a-z0-9']+", t.lower())
        return {" ".join(w[i:i + 8]) for i in range(max(0, len(w) - 7))}

    for i, a in enumerate(preds):
        for b in preds[i + 1:]:
            overlap = shingles(a["text"]) & shingles(b["text"])
            ok(not overlap, f"{a['pid']} and {b['pid']} share the run: {sorted(overlap)[:1]}")

    # every pick that has a preview must be the same selection as the preview
    by_fid = {}
    for p in preds:
        by_fid.setdefault(p["fid"], []).append(p["selection"])
    pick_sels = {}
    for p in picks:
        pick_sels.setdefault(p["fid"], set()).add(p["selection"])
    for p in preds:
        ok(p["selection"] in pick_sels.get(p["fid"], set()),
           f"preview {p['pid']} names a selection that is not one of the fixture's picks")

    # --------------------------------------------------------------------- pages
    expected = ["index.html", "picks.html", "predictions.html", "matches.html", "lines.html",
                "sources.html", "flagged.html", "methodology.html", "sports/index.html",
                "assets/style.css"]
    expected += [f"sports/{s}.html" for s in
                 ("ice-hockey", "basketball", "tennis", "cricket", "volleyball", "handball",
                  "rugby-union", "baseball", "gaelic-sports", "darts", "greyhounds", "golf",
                  "snooker", "motor-racing", "rugby-league")]
    for name in expected:
        ok((OUT / name).is_file(), f"missing page: playbook/{name}")

    for name in expected:
        path = OUT / name
        if not path.is_file() or path.suffix != ".html":
            continue
        text = path.read_text()
        base = path.parent
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            target = (base / href.split("#")[0]).resolve()
            ok(target.exists(), f"{name}: broken link to {href}")
        ok("<<<<<<<" not in text and ">>>>>>>" not in text, f"{name} contains merge markers")

    picks_html = (OUT / "picks.html").read_text()
    rows = re.findall(r"<tr><td>(.*?)</tr>", picks_html, re.S)
    ok(len(rows) >= len(picks), "picks.html has fewer rows than there are picks")
    ok(picks_html.count('class="src"') >= len(picks),
       "picks.html does not carry a source link on every pick row")

    pred_html = (OUT / "predictions.html").read_text()
    ok(pred_html.count('class="pred"') == len(preds), "predictions.html does not show every preview")

    for name in ("matches.html", "lines.html", "flagged.html", "sources.html"):
        ok('href="https://' in (OUT / name).read_text(), f"{name} carries no external source links")

    ok('href="playbook/picks.html"' in (ROOT / "index.html").read_text(),
       "the root front door does not link the picks page")
    ok('href="playbook/predictions.html"' in (ROOT / "index.html").read_text(),
       "the root front door does not link the predictions page")
    ok("archive.html" in (ROOT / "index.html").read_text(), "the root front door lost its archive link")
    ok("playbook/index.html" in (ROOT / "archive.html").read_text(),
       "the archive page does not list the playbook desk")

    # ------------------------------------------------------------------ grammar
    one_plural = re.compile(r"\b1 (matches|picks|previews|rows|fixtures|sources|prices|events|items|"
                            r"outrights|teams|games)\b", re.I)
    for name in expected:
        path = OUT / name
        if path.suffix != ".html" or not path.is_file():
            continue
        text = re.sub(r"<[^>]+>", " ", path.read_text())
        text = re.sub(r"\s+", " ", text)
        ok(not one_plural.search(text), f"{name} says '1 <plural>'")

    # ------------------------------------------------------------------- hygiene
    for name in expected:
        path = OUT / name
        if path.is_file():
            txt = path.read_text()
            ok("/home/" not in txt and "file://" not in txt, f"{name} leaks a local path")
            ok("2019-" not in txt, f"{name} contains a stray date that would drift")

    if FAILS:
        print(f"playbook_verify: {CHECKS} checks, {len(FAILS)} FAILURES")
        for f in FAILS[:40]:
            print("  FAIL:", f)
        return 1
    print(f"playbook_verify: {CHECKS} checks, 0 failures — {len(fixtures)} fixtures, {len(picks)} picks, "
          f"{len(preds)} previews, {len(expected)} pages, {sources_doc['count']} sources, {len(flags_doc['flags'])} flags")
    return 0


if __name__ == "__main__":
    sys.exit(main())
