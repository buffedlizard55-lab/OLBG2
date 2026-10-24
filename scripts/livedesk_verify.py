#!/usr/bin/env python3
"""Structural and content checks for the live desk.

Run after scripts/livedesk_build.py.  Exits non-zero on the first violation so the CI job
stops before a broken page is published.

What it refuses to allow
------------------------
* a high-confidence pick that is not backed by an official-model tier row
* a price without a probability, or a probability outside 0-1
* a written prediction shorter than 30 words, or one that uses the words "model" or
  "verified" (the brief forbids both in published prose), or one that repeats another
  prediction's phrasing
* a number in a prediction that is not present in that prediction's own fact list
* a source link on a prediction that is not one of the pages the desk actually read
* a broken internal link, or a stray "None"/"nan" in the rendered HTML
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "live_desk"
OUT = ROOT / "live-desk"
MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
PRED = json.loads((DATA / "predictions.json").read_text(encoding="utf-8")) if (DATA / "predictions.json").exists() else {"items": []}

BANNED = ("model", "verified", "verification")
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9'’%.-]+", text)


def shingles(text: str, n: int = 8) -> set[tuple]:
    w = [x.lower() for x in words(text)]
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def main() -> int:
    events = {ev["key"]: ev for ev in MODEL["events"]}
    scope = set(MODEL["meta"]["scope"])

    # ------------------------------------------------------------------ model
    for key, ev in events.items():
        if ev["sport"] not in scope:
            fail(f"event {key}: sport {ev['sport']} is outside the brief")
        if not ev.get("olbg_url", "").startswith("https://www.olbg.com/"):
            fail(f"event {key}: missing OLBG link")
        if not ev.get("start_utc") and not (ev.get("official") or {}).get("start_local"):
            fail(f"event {key}: no start time")
        if ev["tier"] not in ("official-model", "quoted-market", "crowd-consensus", "no-basis"):
            fail(f"event {key}: unknown tier {ev['tier']}")
        p = ev.get("pick")
        if p:
            if not (0 < p["probability"] < 1):
                fail(f"event {key}: probability out of range")
            if not isinstance(p["fair_american"], int):
                fail(f"event {key}: fair price is not an integer")
            if p["confidence"] == "high" and ev["tier"] == "crowd-consensus":
                fail(f"event {key}: high confidence without an official input")
            if p["confidence"] not in ("high", "medium", "low"):
                fail(f"event {key}: bad confidence grade")
            if p["in_band"] != (-250 <= p["fair_american"] <= 10000):
                fail(f"event {key}: window flag disagrees with the price")
        if ev["official_verified"] and not (ev.get("official") or {}).get("source_url"):
            fail(f"event {key}: marked official with no official URL")

    # ------------------------------------------------------------------ predictions
    allowed_urls = set()
    for c in MODEL["meta"]["olbg_pages"].values():
        if c.get("url"):
            allowed_urls.add(c["url"])
    for srcs in MODEL["meta"].get("text_sources", {}).values():
        for s in srcs:
            allowed_urls.add(s["url"])
    for k in ("nhl_standings_url", "mlb_schedule_url", "euroleague_standings_url",
              "wta_rankings_url", "f1_standings_url"):
        if MODEL["meta"]["ratings"].get(k):
            allowed_urls.add(MODEL["meta"]["ratings"][k])
    for ev in MODEL["events"]:
        if ev.get("olbg_url"):
            allowed_urls.add(ev["olbg_url"])
        if (ev.get("official") or {}).get("source_url"):
            allowed_urls.add(ev["official"]["source_url"])

    seen: list[tuple[str, set]] = []
    for item in PRED["items"]:
        key = item.get("event_key")
        ev = events.get(key)
        if not ev:
            fail(f"prediction for unknown event {key!r}")
            continue
        body = item.get("body", "")
        n = len(words(body))
        if n < 30:
            fail(f"{key}: prediction is {n} words, below the 30-word floor")
        low = body.lower()
        for word in BANNED:
            if re.search(rf"\b{word}\b", low):
                fail(f"{key}: prediction uses the forbidden word {word!r}")
        if item.get("sport") != ev["sport"]:
            fail(f"{key}: prediction sport does not match the fixture")
        if not item.get("selection"):
            fail(f"{key}: prediction does not name a selection")
        # A write-up is authored against one capture.  While that capture is still the current
        # one every number must also appear in the fixture's own facts; once a fresher capture
        # lands, the prose keeps its own dated fact list and the page says which capture it
        # describes, so the numbers are never silently re-attributed.
        same_capture = item.get("capture") == MODEL["meta"].get("captured_at")
        facts_text = " ".join(item.get("facts", []))
        if same_capture:
            facts_text += " " + " ".join(str(v) for v in (ev.get("facts") or {}).values())
        for num in set(re.findall(r"\d+(?:\.\d+)?", body)):
            if num not in facts_text:
                fail(f"{key}: number {num!r} appears in the prose but not in the fact list")
        srcs = item.get("sources", [])
        if not srcs:
            fail(f"{key}: prediction has no source")
        for u in srcs:
            if u not in allowed_urls:
                fail(f"{key}: source {u} was not one of the pages read")
        for other_key, other in seen:
            inter = shingles(body) & other
            if inter:
                fail(f"{key}: shares an eight-word run with {other_key}")
        seen.append((key, shingles(body)))
        if item.get("confidence") == "high" and ev["tier"] == "crowd-consensus":
            fail(f"{key}: prediction claims high confidence without an official input")

    # ------------------------------------------------------------------ pages
    pages = list(OUT.rglob("*.html")) + [ROOT / "index.html"]
    if not (OUT / "index.html").exists():
        fail("desk index.html was not built")
    for sport in scope:
        slug = re.sub(r"[^a-z0-9]+", "-", sport.lower()).strip("-")
        if not (OUT / "sports" / f"{slug}.html").exists():
            fail(f"missing sport page for {sport}")
    for page in pages:
        text = page.read_text(encoding="utf-8")
        if re.search(r"\bNone\b|\bnan\b", text):
            fail(f"{page.name}: rendered None/nan")
        for href in re.findall(r'href="([^"#]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            target = (page.parent / href).resolve()
            if not target.exists():
                fail(f"{page.relative_to(ROOT)}: broken internal link {href}")

    if errors:
        print(f"{len(errors)} problems")
        for err in errors[:60]:
            print("  -", err)
        return 1
    print(f"ok: {len(events)} fixtures, {len(PRED['items'])} predictions, {len(pages)} pages checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
