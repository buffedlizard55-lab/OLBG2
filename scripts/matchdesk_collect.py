#!/usr/bin/env python3
"""First-hand capture for the consolidated match desk.

The authoring sandbox reaches GitHub only, so every public read is taken by this
script inside a GitHub Actions job and committed back to the branch that asked for
it.  The script records responses and nothing else: it never interprets a body, picks
a fixture, prices a market or writes prose.  Parsing happens in
``scripts/matchdesk_facts.py``, which refuses a body that is missing, non-200 or
truncated.

For every request the manifest keeps the URL, the final URL after redirects, the UTC
time of the request, the HTTP status, the byte count, the sha256 of the stored body
and the file it was written to.  A failure is evidence too: it is written to the
manifest with its status and error, and published on the desk's review page.

Usage
-----
    python scripts/matchdesk_collect.py                     # full request list
    python scripts/matchdesk_collect.py --only olbg_hub_ice_hockey,nhle_standings
    python scripts/matchdesk_collect.py --request data/matchdesk/requests.json

Exit code is 0 even when individual reads fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "matchdesk"
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.json"
DEFAULT_REQUEST = DATA / "requests.json"

MAX_BYTES = 400_000
# A handful of ranking tables are server-rendered deep inside a very large page.  They
# declare their own cap in the request list; everything else is capped at MAX_BYTES.
DEFAULT_CAP = MAX_BYTES
TIMEOUT = 40
WORKERS = 6
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 OLBG2-matchdesk-capture/1.0 "
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
        "stored_as": "",
        "error": "",
        "content_type": "",
        "truncated": False,
    }
    cap_bytes = int(item.get("max_bytes") or DEFAULT_CAP)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json,text/html,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(cap_bytes + 1)
            rec["http_status"] = resp.status
            rec["final_url"] = resp.geturl()
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        body = exc.read(cap_bytes + 1)
        rec["http_status"] = exc.code
        ctype = (exc.headers.get("Content-Type", "") if exc.headers else "")
        rec["error"] = f"HTTPError {exc.code}"
    except Exception as exc:  # noqa: BLE001 - the failure itself is the evidence
        rec["error"] = f"{type(exc).__name__}: {exc}"
        return rec

    rec["content_type"] = ctype
    rec["bytes"] = len(body)
    rec["truncated"] = len(body) > cap_bytes
    body = body[:cap_bytes]
    rec["sha256"] = hashlib.sha256(body).hexdigest()
    suffix = ".json" if "json" in ctype else (".xml" if "xml" in ctype else ".txt")
    name = safe_name(key) + suffix
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / name).write_bytes(body)
    rec["stored_as"] = f"raw/{name}"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", default=str(DEFAULT_REQUEST))
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    spec = json.loads(pathlib.Path(args.request).read_text(encoding="utf-8"))
    requests = spec["requests"]
    if args.only:
        wanted = {k.strip() for k in args.only.split(",") if k.strip()}
        requests = [r for r in requests if r["key"] in wanted]
    if not requests:
        print("no requests selected")
        return 0

    started = now_utc()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        captures = list(pool.map(fetch, requests))
    captures.sort(key=lambda r: r["key"])

    ok = sum(1 for c in captures if c["http_status"] == 200)
    manifest = {
        "captured_at": now_utc(),
        "started_at": started,
        "request_file": pathlib.Path(args.request).name,
        "request_note": spec.get("note", ""),
        "count": len(captures),
        "ok": ok,
        "failed": len(captures) - ok,
        "captures": captures,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    for c in captures:
        flag = "ok " if c["http_status"] == 200 else "ERR"
        print(f"{flag} {c['http_status']} {c['bytes']:>8} {c['key']:<34} {c['error'][:60]}")
    print(f"{ok}/{len(captures)} reads returned HTTP 200; manifest at {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
