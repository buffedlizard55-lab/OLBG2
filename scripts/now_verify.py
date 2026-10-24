#!/usr/bin/env python3
"""Line-by-line verifier for the /now/ desk.

Every assertion below is checkable from the committed data or from the rendered HTML, so a
reader can re-run this file and get the same answer. It fails closed: an unexpected blank,
a missing source link, a banned word in reader-facing copy or a drifted count is an error.

Checks
  1  schema and counts of the five data files
  2  every fixture carries an https official source, at least one sourced fact and a capture time
  3  every price equals the reciprocal of its probability, and the band test is applied exactly
  4  every published pick is inside the band, has a grade and names its source
  5  confidence rules are applied as documented (totals capped, evidence ladder capped at medium)
  6  every high and medium pick has a written prediction, >= 30 words, unique opening, no banned words
  7  every table row on every page carries a link
  8  every internal link and anchor resolves
  9  no reader-facing page contains the words model / verified
 10  deterministic rebuild (data files and pages are byte-identical on a second run)

Exit code 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "now"
OUT = ROOT / "now"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
checks = 0
errors: list[str] = []


def ok(cond, message):
    global checks
    checks += 1
    if not cond:
        errors.append(message)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def price_for(p: float) -> int:
    p = max(0.0005, min(0.9995, p))
    if p >= 0.5:
        return -max(100, round(100 * p / (1 - p)))
    return max(100, round(100 * (1 - p) / p))


def main() -> int:
    fixtures = load("fixtures.json")
    matches = load("matches.json")
    lines = load("lines.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    olbg = load("olbg.json")
    sources = load("sources.json")
    flagged = load("flagged.json")

    # 1 ------------------------------------------------------------------ schema
    ok(fixtures["count"] == len(fixtures["fixtures"]) == 50, "fixture count mismatch")
    ok(set(fixtures["sports"]) == set(SPORTS), "sport list is not the exact fifteen requested")
    ok({m["sport"] for m in matches["matches"]} <= set(SPORTS), "match sport outside the fifteen")
    ok(matches["count"] == len(matches["matches"]), "match count mismatch")
    ok(lines["count"] == len(lines["lines"]), "line count mismatch")
    ok(picks["count"] == len(picks["picks"]), "pick count mismatch")
    ok(preds["count"] == len(preds["predictions"]), "prediction count mismatch")
    ok(olbg["listings_count"] == len(olbg["listings"]), "OLBG row count mismatch")
    ok(sources["count"] == len(sources["sources"]), "source count mismatch")
    ok(flagged["count"] == len(flagged["flags"]), "flag count mismatch")
    omission = next((f for f in flagged["flags"] if f["id"] == "V-09"), None)
    ok(omission is not None, "LA-New Jersey omission is not flagged")
    if omission:
        ok(omission["source"] == "https://api-web.nhle.com/v1/schedule/2026-10-24",
           "NHL omission flag does not link the official schedule")
        ok("Los Angeles" in omission["item"] and "New Jersey" in omission["item"],
           "NHL omission flag does not name the fixture")

    # 2 ------------------------------------------------------------------ sources
    for f in fixtures["fixtures"]:
        ok(f["official_url"].startswith("https://"), f"{f['id']}: official_url is not https")
        ok(len(f["facts"]) >= 1, f"{f['id']}: no sourced fact")
        for fact in f["facts"]:
            ok(fact["source_url"].startswith("https://"), f"{f['id']}: fact source is not https")
            ok(fact.get("captured_utc", "").endswith("Z"), f"{f['id']}: fact has no capture time")
        ok(f["facts_inherited"] is True, f"{f['id']}: inheritance flag missing")
    for s in sources["sources"]:
        ok(s["url"].startswith("https://"), f"source not https: {s['url']}")

    # 3 ------------------------------------------------------------------ pricing
    for row in lines["lines"]:
        ok(row["american"] == price_for(row["probability"]),
           f"{row['fixture_id']} {row['selection']}: price is not 1/probability")
        ok(row["in_band"] == (-250 <= row["american"] <= 10000),
           f"{row['fixture_id']} {row['selection']}: band flag wrong")
        ok(row["basis"] in {"poisson", "normal_margin", "class_ladder"},
           f"{row['fixture_id']}: unknown basis {row['basis']}")
        ok(bool(row["assumption"]), f"{row['fixture_id']}: no stated assumption")

    # 4 ------------------------------------------------------------------ picks
    for p in picks["picks"]:
        ok(p["in_band"], f"{p['id']}: pick outside the band")
        ok(p["confidence"] in {"high", "medium", "low"}, f"{p['id']}: bad grade")
        ok(p["official_url"].startswith("https://"), f"{p['id']}: no official source")
        ok(p["american"] == price_for(p["probability"]), f"{p['id']}: price/price mismatch")
        ok(abs(p["decimal"] - round(1 / p["probability"], 3)) < 0.002,
           f"{p['id']}: decimal is not 1/probability")

    # 5 ------------------------------------------------------------------ grading
    graded = {(r["fixture_id"], r["market"], r["selection"]): r["confidence"]
              for r in lines["lines"]}
    for p in picks["picks"]:
        row = graded.get((p["fixture_id"], p["market"], p["selection"]))
        ok(row == p["confidence"], f"{p['id']}: pick grade differs from its line grade")
    for row in lines["lines"]:
        if row["kind"] == "total":
            ok(row["confidence"] != "high", f"{row['fixture_id']}: a total was graded high")
        if row["basis"] == "class_ladder":
            ok(row["confidence"] != "high",
               f"{row['fixture_id']}: an evidence-ladder price was graded high")
        if row["confidence"] == "high":
            ok(row["probability"] >= 0.70, f"{row['fixture_id']}: high under 70%")
        if row["confidence"] == "medium":
            ok(row["probability"] >= 0.55, f"{row['fixture_id']}: medium under 55%")

    # 5b ----------------------------------------------------------------- the 0-10 score
    shade = {"poisson": 1.0, "normal_margin": 1.0, "class_ladder": 0.8}
    picks_html = (OUT / "picks.html").read_text(encoding="utf-8")
    preds_html = (OUT / "predictions.html").read_text(encoding="utf-8")
    for p in picks["picks"]:
        score = p.get("score")
        ok(isinstance(score, (int, float)), f"{p['id']}: no 0-10 score")
        expect = round(min(10.0, 10.0 * p["probability"] * shade[p["basis"]]), 1)
        ok(abs(score - expect) < 1e-9, f"{p['id']}: score {score} is not 10 x chance x basis")
        ok(0.0 <= score <= 10.0, f"{p['id']}: score outside 0-10")
        ok(f'>{score:.1f}<span class="den">/10' in picks_html,
           f"{p['id']}: score missing from picks.html")
    for p in preds["predictions"]:
        ok(p.get("score") is not None, f"{p['id']}: preview carries no score")
        ok(f'>{p["score"]:.1f}<span class="den">/10' in preds_html,
           f"{p['id']}: score missing from predictions.html")
    for p in picks["picks"]:
        if p["confidence"] == "high":
            ok(p["score"] >= 6.0, f"{p['id']}: a high grade scores under 6.0")

    # 6 ------------------------------------------------------------------ prose
    ok(preds["min_words"] >= 30, "shortest prediction under 30 words")
    openings, texts = {}, set()
    for p in preds["predictions"]:
        words = len(p["text"].split())
        ok(p["words"] == words and words >= 30, f"{p['id']}: word count {words}")
        ok(not BANNED.search(p["text"]), f"{p['id']}: banned word in text")
        ok(not BANNED.search(p["headline"]), f"{p['id']}: banned word in headline")
        ok(p["text"] not in texts, f"{p['id']}: duplicated text")
        texts.add(p["text"])
        opening = " ".join(p["text"].split()[:5]).lower()
        ok(opening not in openings, f"{p['id']}: duplicated opening '{opening}'")
        openings[opening] = p["id"]
        ok(len(p["facts"]) >= 2, f"{p['id']}: fewer than two sourced facts")
        ok(p["official_url"].startswith("https://"), f"{p['id']}: no official source")
        sticky = [w for w in re.findall(r"[A-Za-z]{4,}", p["selection"])]
        ok(any(w.lower() in p["text"].lower() for w in sticky),
           f"{p['id']}: selection not named in the text")
    written = {p["fixture_id"] for p in preds["predictions"]}
    for p in picks["picks"]:
        if p["confidence"] in {"high", "medium"}:
            ok(p["fixture_id"] in written, f"{p['id']}: no written prediction")

    # 6b ----------------------------------------------------------------- temporal integrity
    started = {p["fixture_id"] for p in picks["picks"] if p["started"]}
    ok(len(started) == picks["started_count"], "started-pick count mismatch")
    ok(picks["pregame_count"] + picks["started_count"] == picks["count"],
       "pre-game and started picks do not add up")
    for p in picks["picks"]:
        m = next((x for x in matches["matches"] if x["id"] == p["fixture_id"]), None)
        ok(m is not None, f"{p['id']}: no matching fixture")
        ok(p["started"] == (bool(m["start_utc"]) and m["start_utc"] <= "2026-10-24T18:10:00Z"),
           f"{p['id']}: started flag disagrees with the start time")
    started_fixtures = sum(bool(m["started"]) for m in matches["matches"])
    ok(started_fixtures == 5, "expected five started fixture records at the pinned snapshot")
    ok(matches["count"] - started_fixtures == 45, "expected 45 fixture records still to start")
    index_html = (OUT / "index.html").read_text(encoding="utf-8")
    ok(">50</div><div class=\"k\">fixture records" in index_html,
       "desk index does not distinguish fixture records from upcoming matches")
    ok("45 still to start" in index_html and "5 started at snapshot" in index_html,
       "desk index temporal counts are missing")
    ok("50 upcoming matches" not in index_html, "desk index still calls every record upcoming")
    cards = re.findall(r'class="sel" href="predictions\.html#pred-([^"]+)"', index_html)
    ok(len(cards) >= 3, "executive summary shows too few calls")
    for fid in cards:
        ok(fid not in started, f"executive summary promotes a started fixture: {fid}")
    root_html = (ROOT / "index.html").read_text(encoding="utf-8")
    ok(">50</div><div class=\"k\">fixture records" in root_html,
       "root does not distinguish fixture records from upcoming matches")
    ok("45 still to start" in root_html and "5 started at snapshot" in root_html,
       "root temporal counts are missing")
    ok("50 upcoming matches" not in root_html, "root still calls every record upcoming")
    root_cards = re.findall(r'class="pickcard" href="now/predictions\.html#pred-([^"]+)"', root_html)
    ok(len(root_cards) >= 3, "root front door shows too few calls")
    for fid in root_cards:
        ok(fid not in started, f"root front door promotes a started fixture: {fid}")

    # 7 ------------------------------------------------------------------ links in tables
    for page in sorted(OUT.rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
            if "<th" in row:
                continue
            ok("https://" in row or "href=" in row,
               f"{page.relative_to(ROOT)}: table row without a link")

    # 8 ------------------------------------------------------------------ internal links
    ids = {p.resolve(): set(re.findall(r'id="([^"]+)"', p.read_text(encoding="utf-8")))
           for p in OUT.rglob("*.html")}
    for page in OUT.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        for href in re.findall(r'(?:href|src)="([^"]+)"', html):
            if href.startswith(("http://", "https://", "#", "data:", "mailto:")):
                continue
            target, _, anchor = href.partition("#")
            if not target:
                ok(anchor in ids[page.resolve()], f"{page}: missing anchor #{anchor}")
                continue
            path = (page.parent / target).resolve()
            ok(path.exists(), f"{page.relative_to(ROOT)}: broken link {href}")
            if anchor and path in ids:
                ok(anchor in ids[path],
                   f"{page.relative_to(ROOT)}: missing anchor {href}")
    root_index = (ROOT / "index.html").read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"]+)"', root_index):
        if href.startswith(("http", "#", "data:")):
            continue
        ok((ROOT / href.partition("#")[0]).exists(), f"root index: broken link {href}")

    # 9 ------------------------------------------------------------------ vocabulary
    for page in list(OUT.rglob("*.html")) + [ROOT / "index.html"]:
        html = page.read_text(encoding="utf-8")
        body = re.sub(r"<[^>]+>", " ", html)
        ok(not BANNED.search(body), f"{page.relative_to(ROOT)}: reader-facing 'model'/'verified'")

    # 10 ----------------------------------------------------------------- rebuild determinism
    before = {p: p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
    data_before = {p: p.read_bytes() for p in DATA.glob("*.json")}
    for script in ("now_seed.py", "now_model.py", "now_predictions.py", "now_build.py"):
        res = subprocess.run([sys.executable, str(ROOT / "scripts" / script)],
                             capture_output=True, text=True)
        ok(res.returncode == 0, f"{script} failed on rebuild: {res.stderr[-300:]}")
    after = {p: p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
    data_after = {p: p.read_bytes() for p in DATA.glob("*.json")}
    ok(before == after, "pages are not byte-identical after a rebuild")
    ok(data_before == data_after, "data is not byte-identical after a rebuild")

    print(f"now_verify: {checks} checks, {len(errors)} failures")
    for err in errors[:40]:
        print("  FAIL", err)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
