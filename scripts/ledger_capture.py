#!/usr/bin/env python3
"""First-hand capture of public pages, run on a GitHub-hosted runner.

The sandbox that authors this repository cannot reach the public internet, so every
capture is taken by this script inside a GitHub Actions job and committed back to the
branch that requested it.  Each response is stored verbatim (bounded), together with
the HTTP status, the final URL after redirects, the byte count, a sha256 of the stored
body and the UTC time of the request.

Nothing in this script interprets a response: it only records it.  Parsing happens in
`ledger_seed.py`, which refuses to use a body that is missing, truncated or non-200.

Usage:  python scripts/ledger_capture.py [request.json] [--only key1,key2]
Exit code is 0 even when individual requests fail, so the manifest is always committed:
a failure is evidence too, and it is published on the flagged page.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ledger"
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.json"
DEFAULT_REQUEST = DATA / "request.json"

MAX_BYTES = 300_000          # stored body cap per response
TIMEOUT = 40
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 OLBG2-research-capture/1.0 "
    "(+https://github.com/buffedlizard55-lab/OLBG2)"
)


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: pathlib.Path, default):
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def fetch(url: str) -> dict:
    """Return a capture record and (optionally) the stored body text."""
    started = now_utc()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    rec = {"requested_url": url, "requested_at": started}
    body = b""
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read(MAX_BYTES + 1)
            rec.update(
                status=int(resp.status),
                final_url=resp.geturl(),
                content_type=resp.headers.get("Content-Type", ""),
                server=resp.headers.get("Server", ""),
                last_modified=resp.headers.get("Last-Modified", ""),
            )
            truncated = len(raw) > MAX_BYTES
            body = raw[:MAX_BYTES]
            rec["truncated"] = truncated
    except urllib.error.HTTPError as exc:  # a documented 403/404 is still evidence
        rec.update(status=int(exc.code), final_url=url, error=f"HTTPError {exc.code}")
        try:
            body = exc.read(MAX_BYTES)
        except Exception:  # noqa: BLE001 - the status alone is the finding
            body = b""
    except Exception as exc:  # noqa: BLE001 - DNS, TLS, timeout, sandbox egress
        rec.update(status=0, final_url=url, error=f"{type(exc).__name__}: {exc}"[:400])
    rec["fetched_at"] = now_utc()
    rec["bytes"] = len(body)
    rec["sha256"] = hashlib.sha256(body).hexdigest() if body else ""
    rec["_body"] = body
    return rec


def guess_ext(rec: dict) -> str:
    ctype = (rec.get("content_type") or "").lower()
    url = (rec.get("final_url") or "").lower()
    if "json" in ctype or url.endswith(".json"):
        return "json"
    if "xml" in ctype or url.endswith(".xml"):
        return "xml"
    if "text/plain" in ctype:
        return "txt"
    return "html"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = ""
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = a.split("=", 1)[1]
    req_path = pathlib.Path(args[0]) if args else DEFAULT_REQUEST
    spec = load_json(req_path, {})
    requests = spec.get("requests", [])
    if only:
        wanted = {k.strip() for k in only.split(",") if k.strip()}
        requests = [r for r in requests if r["key"] in wanted]
    if not requests:
        print("no requests to perform", file=sys.stderr)
        return 0

    RAW.mkdir(parents=True, exist_ok=True)
    manifest = load_json(MANIFEST, {"captures": []})
    history = {c["key"]: c for c in manifest.get("captures", []) if c.get("key")}
    run = {"run_at": now_utc(), "request_file": str(req_path.relative_to(ROOT)), "results": []}

    for item in requests:
        key = item["key"]
        url = item["url"]
        rec = fetch(url)
        body = rec.pop("_body", b"")
        ext = guess_ext(rec)
        stored = f"raw/{key}.{ext}"
        if body:
            (DATA / stored).write_bytes(body)
            rec["stored_as"] = stored
        rec.update(
            key=key,
            sport=item.get("sport", ""),
            kind=item.get("kind", ""),
            label=item.get("label", ""),
            note=item.get("note", ""),
        )
        # Keep the newest capture per key in `captures`, and every attempt in `history`.
        history[key] = rec
        run["results"].append({k: rec[k] for k in ("key", "status", "bytes", "truncated", "error") if k in rec})
        print(f"{rec.get('status', 0):>4} {rec.get('bytes', 0):>7}B {key:<28} {url}")
        time.sleep(1.0)  # be polite to the public endpoints

    manifest["captures"] = sorted(history.values(), key=lambda c: c["key"])
    manifest["last_run"] = run
    manifest.setdefault("history", []).append({k: v for k, v in run.items() if k != "results"})
    manifest["history"] = manifest["history"][-40:]
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=False) + "\n", encoding="utf-8")

    ok = sum(1 for r in run["results"] if r.get("status") == 200)
    print(f"\n{ok}/{len(run['results'])} requests returned HTTP 200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
