#!/usr/bin/env python3
"""Quest desk verifier. Returns a list of errors; empty means pass."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "quest"
OUT = ROOT / "quest"
CUTOFF = "2026-10-23T21:30:00Z"
SPORTS15 = {"Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
            "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
            "Handball", "Ice Hockey", "Basketball", "Rugby League"}
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)


def american(p):
    return -int(round(100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))


def selection_identifiable(selection, text):
    t = text.lower()
    if selection.startswith(("Over ", "Under ")):
        word, num = selection.split()[0], selection.split()[1]
        return word.lower() in t and num in text
    probe = selection.split(" -")[0].split(" +")[0]
    return probe.lower() in t


def load(name):
    return json.loads((DATA / name).read_text())


def run():
    errs = []
    fixtures = load("fixtures.json")["fixtures"]
    lines = load("lines.json")["lines"]
    picks = load("picks.json")["picks"]
    top5 = load("top5.json")["top5"]
    preds = load("predictions.json")["predictions"]
    sources = load("sources.json")["sources"]
    flags = load("flagged.json")["flags"]
    fx = {f["id"]: f for f in fixtures}

    # 1. Scope + official link on every fixture; no started fixture.
    if {f["sport"] for f in fixtures} != SPORTS15:
        errs.append("sport set is not exactly the mandated 15")
    for f in fixtures:
        if not str(f.get("official_source_url", "")).startswith("https://"):
            errs.append(f"{f['id']}: missing/non-https official source")
        if f.get("start_utc") and f["start_utc"] < CUTOFF:
            errs.append(f"{f['id']}: start {f['start_utc']} precedes cut-off")
        if f["status"] == "blank" and not f.get("blank_reason"):
            errs.append(f"{f['id']}: blank without reason")
        for fl in f.get("facts", []):
            if not str(fl.get("source_url", "")).startswith("https://"):
                errs.append(f"{f['id']}: fact without https source")

    # 2. Lines recompute from probability; window + label ceilings hold.
    line_keys = set()
    for l in lines:
        if l["fixture_id"] not in fx:
            errs.append(f"line {l['id']}: unknown fixture")
            continue
        if fx[l["fixture_id"]]["status"] != "priced":
            errs.append(f"line {l['id']}: on blank fixture")
        if american(l["probability"]) != l["fair_american"]:
            errs.append(f"line {l['id']}: fair American {l['fair_american']} != recomputed "
                        f"{american(l['probability'])} (p={l['probability']})")
        if abs(1 / l["probability"] - l["fair_decimal"]) > 0.002:
            errs.append(f"line {l['id']}: fair decimal mismatch")
        if l["in_band"] != (-250 <= l["fair_american"] <= 10000):
            errs.append(f"line {l['id']}: window flag mismatch")
        if l["confidence"] == "high" and l["probability"] < 0.70:
            errs.append(f"line {l['id']}: high label below 0.70")
        if l["confidence"] == "medium" and l["probability"] < 0.60:
            errs.append(f"line {l['id']}: medium label below 0.60")
        line_keys.add((l["fixture_id"], l["market"], l["selection"]))
    for f in fixtures:
        if f["status"] == "priced" and not [l for l in lines if l["fixture_id"] == f["id"]]:
            errs.append(f"{f['id']}: priced but no lines")

    # 3. Picks resolve to fixtures and to a published line.
    for p in picks:
        if p["fixture_id"] not in fx:
            errs.append(f"pick {p['id']}: unknown fixture")
            continue
        if (p["fixture_id"], p["market"], p["selection"]) not in line_keys:
            errs.append(f"pick {p['id']}: no matching line ({p['market']} / {p['selection']})")
        if american(p["probability"]) != p["fair_american"]:
            errs.append(f"pick {p['id']}: fair American mismatch")
        if p["confidence"] == "high" and p["probability"] < 0.70:
            errs.append(f"pick {p['id']}: high label below 0.70")

    # 4. Every in-window high pick has prose; prose rules hold.
    pred_by_pick = {x["pick_id"]: x for x in preds}
    for p in picks:
        if p["confidence"] == "high" and p["in_band"] and p["id"] not in pred_by_pick:
            errs.append(f"pick {p['id']}: in-window high without written prediction")
    seen_texts = set()
    for x in preds:
        words = len(x["text"].split())
        if words < 30:
            errs.append(f"prediction {x['id']}: only {words} words")
        if BANNED.search(x["text"]) or BANNED.search(x["headline"]):
            errs.append(f"prediction {x['id']}: banned word in prose")
        if x["text"] in seen_texts:
            errs.append(f"prediction {x['id']}: duplicate text")
        seen_texts.add(x["text"])
        if not selection_identifiable(x["selection"], x["text"]):
            errs.append(f"prediction {x['id']}: selection not identifiable in text")
        if not x.get("facts"):
            errs.append(f"prediction {x['id']}: no facts")
        for fl in x.get("facts", []):
            if not str(fl.get("source_url", "")).startswith("https://"):
                errs.append(f"prediction {x['id']}: fact without https source")

    # 5. Top5 integrity.
    pick_ids = {p["id"] for p in picks}
    for sport, rows in top5.items():
        if len(rows) > 5:
            errs.append(f"top5 {sport}: more than 5 rows")
        probs = [r["probability"] for r in rows]
        if probs != sorted(probs, reverse=True):
            errs.append(f"top5 {sport}: not in probability order")
        for r in rows:
            if r["pick_id"] not in pick_ids:
                errs.append(f"top5 {sport}: unknown pick {r['pick_id']}")
            if not str(r.get("official_source_url", "")).startswith("https://"):
                errs.append(f"top5 {sport} #{r['rank']}: no official link")

    # 6. Sources/flags carry links.
    for s in sources:
        if not str(s.get("url", "")).startswith("https://"):
            errs.append(f"source {s.get('key')}: non-https url")
    for fl in flags:
        if not str(fl.get("source_url", "")).startswith("https://"):
            errs.append(f"flag {fl.get('id')}: no https source")

    # 7. Generated pages: exist, carry the cut-off, local links resolve,
    #    and data pages link out on at least as many rows as they print.
    pages = sorted(OUT.rglob("*.html")) if OUT.exists() else []
    if len(pages) < 25:
        errs.append(f"expected >=25 quest pages, found {len(pages)}")
    for pg in pages:
        html_text = pg.read_text()
        if "2026-10-23T21:30:00Z" not in html_text:
            errs.append(f"{pg.name}: cut-off not printed")
        for href in re.findall(r'href="([^"#]+)', html_text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = (pg.parent / href.split("#")[0]).resolve()
            if href.split("#")[0] and not target.exists():
                errs.append(f"{pg.name}: broken local link {href}")
    for name in ("matches.html", "picks.html", "top5.html", "sources.html", "flagged.html"):
        p = OUT / name
        if not p.exists():
            continue
        t = p.read_text()
        rows = t.count("<tr>") - t.count("<thead>")
        links = len(re.findall(r'href="https://', t))
        if links < max(0, rows):
            errs.append(f"{name}: {links} outgoing links for ~{rows} data rows")
    return errs


if __name__ == "__main__":
    errors = run()
    if errors:
        print(f"QUEST VERIFY: {len(errors)} error(s)")
        for e_ in errors[:60]:
            print(" -", e_)
        raise SystemExit(1)
    print("QUEST VERIFY: 0 errors")
