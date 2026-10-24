#!/usr/bin/env python3
"""First-hand capture of OLBG listings and governing-body pages for the consolidated desk.

This script records responses and nothing else.  It does not interpret a body, choose a
fixture, price a market or write prose: parsing happens later in ``livedesk_model.py`` and the
prose is authored separately.  The reason for the split is that the authoring sandbox
cannot reach most public hosts, so a GitHub-hosted runner takes the reads and commits a
manifest; the raw bodies travel as a workflow artifact, never as repository content.

Every record carries the URL, the UTC time of the request, the HTTP status, the final URL
after redirects, the byte count and a sha256 of the stored body, so any later claim built on
it can be traced back to this exact response.

Usage
-----
    python scripts/livedesk_collect.py                    # request list below
    python scripts/livedesk_collect.py --only olbg_hub_golf,ieh_sched_2026-10-25
    python scripts/livedesk_collect.py --request data/live_desk/requests.json

A failed request is written to the manifest with its status.  The script exits 0 even when
individual reads fail: an HTTP 403 is evidence and is published as such.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "live_desk" / "captures"
RAW_DIR = OUT_DIR / "raw"
MANIFEST = OUT_DIR / "manifest.json"
DEFAULT_REQUEST = ROOT / "data" / "live_desk" / "requests.json"

MAX_BYTES = 500_000
TIMEOUT = 30
WORKERS = 6
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 OLBG2-livedesk-capture/1.0 "
    "(+https://github.com/buffedlizard55-lab/OLBG2)"
)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_name(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", key)


def fetch(item: dict) -> dict:
    key = item["key"]
    url = item["url"]
    rec = {
        "key": key,
        "sport": item.get("sport", ""),
        "kind": item.get("kind", ""),
        "url": url,
        "note": item.get("note", ""),
        "requested_at": now_utc(),
        "http_status": None,
        "final_url": url,
        "bytes": 0,
        "sha256": None,
        "stored": "",
        "error": "",
        "excerpt": "",
    }
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(MAX_BYTES + 1)
            rec["http_status"] = resp.status
            rec["final_url"] = resp.geturl()
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_BYTES + 1)
        rec["http_status"] = exc.code
        ctype = exc.headers.get("Content-Type", "") if exc.headers else ""
        rec["error"] = f"HTTPError {exc.code}"
    except Exception as exc:  # noqa: BLE001 - the failure itself is the evidence
        rec["error"] = f"{type(exc).__name__}: {exc}"
        return rec

    rec["bytes"] = len(body)
    rec["content_type"] = ctype
    rec["truncated"] = len(body) > MAX_BYTES
    body = body[:MAX_BYTES]
    rec["sha256"] = hashlib.sha256(body).hexdigest()
    suffix = ".json" if "json" in ctype else ".txt"
    name = safe_name(key) + suffix
    (RAW_DIR / name).write_bytes(body)
    rec["stored"] = name
    text = body.decode("utf-8", "replace")
    rec["excerpt"] = re.sub(r"<[^>]*>", " ", text[:1500]).strip()[:240]
    return rec


def discover_events(records: list[dict], per_sport: int = 3) -> list[dict]:
    """From the OLBG hub captures, pick a few event pages per sport to fetch next.

    The point is to find out, from first-hand evidence, whether an event page carries a
    full market board (both sides of match winner, handicap, total) or only the community
    tips.  Three events per sport is enough to answer that and keeps the run small.
    """
    seen: dict[str, int] = {}
    extra: list[dict] = []
    for rec in records:
        if not rec.get("key", "").startswith("olbg_hub_") or rec.get("http_status") != 200:
            continue
        path = RAW_DIR / rec.get("stored", "")
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        sport = rec.get("sport", "")
        if seen.get(sport, 0) >= per_sport:
            continue
        for m in re.finditer(r'eventUrl:"(/betting-tips/[^"]+event_id=(\d+))"', text):
            if seen.get(sport, 0) >= per_sport:
                break
            rel, eid = m.group(1), m.group(2)
            key = f"olbg_event_{sport.lower().replace(' ', '_')}_{eid}"
            if any(e["key"] == key for e in extra):
                continue
            extra.append({"key": key, "url": "https://www.olbg.com" + rel,
                          "sport": sport, "kind": "olbg-event",
                          "note": "OLBG event page: checks for a full market board"})
            extra.append({"key": key + "_data",
                          "url": "https://www.olbg.com" + rel + "/__data.json",
                          "sport": sport, "kind": "olbg-event-data",
                          "note": "SvelteKit data route for the same event page"})
            seen[sport] = seen.get(sport, 0) + 1
    return extra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", default=str(DEFAULT_REQUEST))
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    request = json.loads(pathlib.Path(args.request).read_text(encoding="utf-8"))
    items = request["requests"]
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        items = [i for i in items if i["key"] in wanted]
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    started = now_utc()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        records = list(pool.map(fetch, items))
        if not args.only and request.get("discover_events", True):
            extra = discover_events(records)
            already = {i["key"] for i in items}
            extra = [e for e in extra if e["key"] not in already]
            if extra:
                print(f"discovered {len(extra)} event-page requests")
                records += list(pool.map(fetch, extra))

    manifest = {
        "captured_at": now_utc(),
        "started_at": started,
        "request_file": str(pathlib.Path(args.request).name),
        "request_note": request.get("note", ""),
        "count": len(records),
        "ok": sum(1 for r in records if (r["http_status"] or 0) == 200),
        "failed": sum(1 for r in records if (r["http_status"] or 0) != 200),
        "captures": records,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    print(f"captured {manifest['count']} requests at {manifest['captured_at']}")
    for r in records:
        flag = "ok " if r["http_status"] == 200 else "ERR"
        print(f"  {flag} {r['http_status']} {r['bytes']:>7} {r['key']} {r['error']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
