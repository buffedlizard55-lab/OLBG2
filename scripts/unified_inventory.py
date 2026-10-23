#!/usr/bin/env python3
"""Independent inventory of the OLBG events captured verbatim at 2026-10-23T20:32Z.

Why this exists
---------------
The published desk needs a list of matches that OLBG itself lists, not a list inherited
from another layer.  This script re-reads the raw HTTP bodies stored under
`data/ledger/raw/` by the GitHub-hosted capture job and re-extracts every tip object.
It deliberately does **not** import `ledger_seed.py` or reuse `data/ledger/olbg.json`:
its numbers are an independent second reading, so a disagreement between the two is a
finding rather than a shared bug.

It records, for every event:
  * the OLBG event id and event URL exactly as published in the page payload,
  * the start time from `event_start_unix_timestamp` (never inferred),
  * the market aliases and decimal/american prices that appear in the captured payload,
  * the capture file, its sha256 and its fetch time, so a reader can audit the row.

Nothing is fetched here.  No value is filled in from memory or from another file.

Output: data/unified/olbg_events.json
Exit code 0 always unless the required raw evidence is missing.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "ledger"
RAW = LEDGER / "raw"
MANIFEST = LEDGER / "manifest.json"
OUT_DIR = ROOT / "data" / "unified"
OUT = OUT_DIR / "olbg_events.json"

# The fifteen sports in scope, mapped to the OLBG slug used in its URLs.
SPORTS = {
    "Golf": "Golf",
    "Volleyball": "Volleyball",
    "Rugby Union": "Rugby_Union",
    "Cricket": "Cricket",
    "Snooker": "Snooker",
    "Darts": "Darts",
    "Baseball": "Baseball",
    "Gaelic Sports": "Gaelic_Football",
    "Greyhounds": "Greyhounds",
    "Tennis": "Tennis",
    "Motor Racing": "Motor_Racing",
    "Handball": "Handball",
    "Ice Hockey": "Ice_Hockey",
    "Basketball": "Basketball",
    "Rugby League": "Rugby_League",
}

FIELD_RE = re.compile(
    r'(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*'
    r'(?P<val>"(?:[^"\\]|\\.)*"|null|true|false|void 0|-?\d+(?:\.\d+)?)'
)
TIP_START = re.compile(r'\{id:"([0-9a-f]{40})"')
ASSIGN_START = re.compile(r'c\.id="([0-9a-f]{40})"')


def unquote(v: str):
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if v in ("null", "void 0"):
        return None
    if v == "true":
        return True
    if v == "false":
        return False
    try:
        return json.loads(v)
    except ValueError:
        return v


def tip_objects(text: str) -> list[dict]:
    """Every flat tip object in a captured OLBG page, as key/value dictionaries."""
    out: list[dict] = []
    for m in TIP_START.finditer(text):
        chunk = text[m.start(): m.start() + 3000]
        fields: dict = {"id": m.group(1)}
        for f in FIELD_RE.finditer(chunk):
            fields.setdefault(f.group("key"), unquote(f.group("val")))
        if fields.get("event_name_alias"):
            out.append(fields)
    if not out:
        for m in ASSIGN_START.finditer(text):
            chunk = text[m.start(): m.start() + 3500]
            fields = {"id": m.group(1)}
            for a in re.finditer(r'c\.([A-Za-z_][A-Za-z0-9_]*)="?([^";]*)"?;', chunk):
                fields.setdefault(a.group(1), unquote(a.group(2)))
            fields.setdefault("event_name_alias", fields.get("eventname"))
            if fields.get("event_name_alias"):
                out.append(fields)
    return out


def iso_z(unix_ts) -> str | None:
    try:
        return dt.datetime.fromtimestamp(int(unix_ts), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError, OSError):
        return None


def main() -> int:
    if not MANIFEST.exists():
        print("unified_inventory: data/ledger/manifest.json missing", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    captures = manifest["captures"]

    pages: list[dict] = []
    non_200: list[dict] = []
    events: dict[tuple[str, str], dict] = {}
    parse_errors: list[dict] = []

    for cap in captures:
        url = cap.get("requested_url") or ""
        if "olbg.com" not in url:
            continue
        record = {
            "key": cap.get("key"),
            "url": cap.get("final_url") or url,
            "status": cap.get("status"),
            "fetched_at": cap.get("fetched_at"),
            "bytes": cap.get("bytes"),
            "sha256": cap.get("sha256"),
            "stored_as": cap.get("stored_as"),
            "sport": cap.get("sport"),
        }
        if cap.get("status") != 200 or not cap.get("stored_as"):
            non_200.append(record)
            continue
        path = ROOT / "data" / "ledger" / cap["stored_as"]
        if not path.exists():
            parse_errors.append({**record, "error": "stored body missing"})
            continue
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if cap.get("sha256") and sha != cap["sha256"]:
            parse_errors.append({**record, "error": "sha256 mismatch against manifest", "actual": sha})
            continue
        text = raw.decode("utf-8", "replace")
        objects = tip_objects(text)
        record["objects"] = len(objects)
        pages.append(record)
        if not objects:
            parse_errors.append({**record, "error": "no tip object found in body"})
            continue
        for f in objects:
            name = f.get("event_name_alias")
            event_url = f.get("eventUrl") or ""
            m = re.search(r"event_id=(\d+)", str(event_url))
            event_id = m.group(1) if m else ""
            if not event_id:  # outrights and tournament markets carry no event id
                event_id = "market:" + re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
            sport = cap.get("sport") or ""
            if sport in ("", "OLBG"):
                # The tips index and the per-event pages are filed under the publisher, so
                # recover the sport from the page's own category path.
                mm = re.search(r"/betting-tips/([A-Za-z_]+)/", str(f.get("categoryUrl") or "") + str(event_url))
                if mm:
                    sport = mm.group(1).replace("_", " ")
            if sport == "Gaelic Football":
                sport = "Gaelic Sports"
            if sport not in SPORTS:
                # The index pages list every OLBG sport; only the fifteen in scope are kept.
                continue
            if sport == "Hurling":
                sport = "Gaelic Sports"
            two_sided = bool(re.split(r"\s+@\s+|\s+vs\.?\s+|\s+v\s+", str(name), flags=re.I).__len__() == 2)
            if sport == "Gaelic Football":
                sport = "Gaelic Sports"
            if sport not in SPORTS:
                # The index pages list every OLBG sport; only the fifteen in scope are kept.
                continue
            key = (sport, event_id)
            ev = events.setdefault(key, {
                "sport": sport,
                "event": name,
                "event_id": event_id,
                "event_url": ("https://www.olbg.com" + event_url) if str(event_url).startswith("/") else event_url,
                "league": f.get("menu_league") or "",
                "kind": "match" if two_sided else "outright",
                "start_utc": iso_z(f.get("event_start_unix_timestamp")),
                "start_unix": f.get("event_start_unix_timestamp"),
                "markets": {},
                "tips": 0,
                "expired_values": set(),
                "captures": [],
            })
            market = f.get("market_alias") or ""
            ev["tips"] += 1
            slot = ev["markets"].setdefault(market, {"selections": [], "decimal_odds": [], "american_odds": []})
            sel = f.get("selection")
            if sel and sel not in slot["selections"]:
                slot["selections"].append(sel)
            if f.get("odds"):
                slot["decimal_odds"].append(f["odds"])
            if f.get("american_odds") not in (None, ""):
                slot["american_odds"].append(str(f.get("american_odds")))
            if str(f.get("expired")) not in ("0", "None", ""):
                ev["expired_values"].add(str(f.get("expired")))
            cap_ref = {"key": cap.get("key"), "fetched_at": cap.get("fetched_at"),
                       "sha256": cap.get("sha256"), "stored_as": cap.get("stored_as")}
            if cap_ref not in ev["captures"]:
                ev["captures"].append(cap_ref)
            # A later, richer page wins on the human-readable league label.
            if not ev["league"] and f.get("menu_league"):
                ev["league"] = f["menu_league"]

    capture_times = sorted({p["fetched_at"] for p in pages if p.get("fetched_at")})
    upcoming_cut = capture_times[-1] if capture_times else None

    rows = []
    for ev in events.values():
        ev["markets"] = {
            k: {
                "selections": v["selections"],
                "decimal_odds": v["decimal_odds"],
                "american_odds": v["american_odds"],
                "tip_count": len(v["decimal_odds"]),
            }
            for k, v in sorted(ev["markets"].items())
        }
        ev["expired_values"] = sorted(ev["expired_values"])
        ev["market_count"] = len(ev["markets"])
        # "upcoming" is a comparison of two recorded values, not an inference.
        if ev["start_utc"] and upcoming_cut:
            ev["upcoming_at_capture"] = ev["start_utc"] > upcoming_cut
        else:
            ev["upcoming_at_capture"] = None
        rows.append(ev)

    rows.sort(key=lambda r: (r["sport"], r["start_utc"] or "9999", r["event"]))
    by_sport: dict[str, dict] = {}
    for r in rows:
        s = by_sport.setdefault(r["sport"], {"events": 0, "upcoming": 0, "unknown_start": 0,
                                             "markets": set(), "tips": 0})
        s["events"] += 1
        s["tips"] += r["tips"]
        if r["upcoming_at_capture"] is True:
            s["upcoming"] += 1
        elif r["upcoming_at_capture"] is None:
            s["unknown_start"] += 1
        s["markets"].update(r["markets"].keys())
    for s in by_sport.values():
        s["markets"] = sorted(s["markets"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_from": {
            "manifest": "data/ledger/manifest.json",
            "capture_window": {"first": capture_times[0], "last": capture_times[-1]} if capture_times else {},
            "runner": "GitHub-hosted Actions runner (public internet); this desk does not refetch",
            "pages_read": len(pages),
            "olbg_pages_used": [p["key"] for p in pages],
        },
        "counts": {
            "events": len(rows),
            "upcoming": sum(1 for r in rows if r["upcoming_at_capture"] is True),
            "unknown_start": sum(1 for r in rows if r["upcoming_at_capture"] is None),
            "sports": len(by_sport),
            "by_sport": by_sport,
        },
        "pages": pages,
        "non_200": non_200,
        "parse_errors": parse_errors,
        "events": rows,
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    print(f"unified_inventory: {len(rows)} OLBG events from {len(pages)} verbatim pages "
          f"({payload['counts']['upcoming']} starting after the capture clock, "
          f"{payload['counts']['unknown_start']} without a recorded start)")
    for sport in SPORTS:
        s = by_sport.get(sport)
        print(f"  {sport:14} events={s['events'] if s else 0:3}  upcoming={s['upcoming'] if s else 0:3}  "
              f"no_start={s['unknown_start'] if s else 0:3}  markets={len(s['markets']) if s else 0}")
    if parse_errors:
        print(f"  {len(parse_errors)} page(s) could not be parsed - listed in the JSON", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
