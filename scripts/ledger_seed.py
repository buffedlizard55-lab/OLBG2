#!/usr/bin/env python3
"""Parse the captured OLBG pages into a structured tip/event inventory.

OLBG renders its sport hubs server-side and embeds each tip as a flat JavaScript object
literal inside the page payload, for example:

    {id:"c1866…",selection:"Wessel Nijman",market_alias:"Win Match 2-way",odds:"1.53",
     american_odds:"-189",event_start_unix_timestamp:"1792784700",
     eventUrl:"/betting-tips/Darts/All_Darts/All_Events/Wessel_Nijman_vs_Martin_Schindler/15?event_id=32326",
     event_name_alias:"Wessel Nijman vs Martin Schindler",…,tournament:"European Championship"}

This script does not invent anything: it only reads fields that literally appear in the
stored response, records the capture key and timestamp they came from, and keeps the
verbatim fragment so every derived row can be audited against the raw file.

Output: data/ledger/olbg.json
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402
DATA = ROOT / "data" / "ledger"
ANCHOR = anchor()
import datetime as _dtmod
ANCHOR_DT = _dtmod.datetime.strptime(ANCHOR, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dtmod.timezone.utc)
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.json"

FIELD_RE = re.compile(
    r'(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*'
    r'(?P<val>"(?:[^"\\]|\\.)*"|null|true|false|void 0|-?\d+(?:\.\d+)?)'
)
OBJ_START = re.compile(r'\{id:"([0-9a-f]{40})"')


def norm_event(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


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


def parse_objects(text: str) -> list[dict]:
    """Return every flat tip object found in a captured page."""
    out = []
    for m in OBJ_START.finditer(text):
        chunk = text[m.start(): m.start() + 3000]
        fields = {}
        for f in FIELD_RE.finditer(chunk):
            key, val = f.group("key"), f.group("val")
            if key in fields:      # first occurrence wins; later ones belong to the next object
                continue
            fields[key] = unquote(val)
        if not fields.get("event_name_alias"):
            continue
        out.append({"fragment": chunk[:600], "fields": fields})
    return out


def parse_assignments(text: str) -> list[dict]:
    """Event pages use `c.field=value;` assignments; recover them too."""
    blocks = []
    for m in re.finditer(r'c\.id="([0-9a-f]{40})"', text):
        chunk = text[m.start(): m.start() + 3500]
        fields = {}
        for a in re.finditer(r'c\.([A-Za-z_][A-Za-z0-9_]*)="?([^";]*)"?;', chunk):
            fields.setdefault(a.group(1), unquote(a.group(2)))
        if fields.get("event_name_alias") or fields.get("eventname"):
            fields.setdefault("event_name_alias", fields.get("eventname"))
            blocks.append({"fragment": chunk[:600], "fields": fields})
    return blocks


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    caps = {c["key"]: c for c in manifest["captures"]}
    tips: dict[tuple, dict] = {}
    pages = []

    for key, cap in sorted(caps.items()):
        if not key.startswith("olbg_"):
            continue
        path = ROOT / "data" / "ledger" / cap.get("stored_as", "")
        if not path.exists() or cap.get("status") != 200:
            continue
        sport_guess = None
        m = re.search(r"/betting-tips/([A-Za-z_]+)/", cap.get("final_url", ""))
        if m:
            sport_guess = m.group(1).replace("_", " ")
        text = path.read_text(encoding="utf-8", errors="replace")
        objs = parse_objects(text)
        if not objs:
            objs = parse_assignments(text)
        pages.append({"key": key, "url": cap.get("final_url"), "fetched_at": cap.get("fetched_at"),
                      "objects": len(objs), "bytes": cap.get("bytes")})
        for o in objs:
            f = o["fields"]
            sport = (f.get("sport") or f.get("sport_alias") or "").replace("_", " ")
            if not sport:
                mm = re.search(r"/betting-tips/([A-Za-z_]+)/", (f.get("categoryUrl") or "") + (f.get("eventUrl") or ""))
                sport = mm.group(1).replace("_", " ") if mm else (sport_guess or "")
            comp = f.get("tournament") or f.get("menu_league") or ""
            if not comp:
                mm = re.search(r"/betting-tips/[A-Za-z_]+/([A-Za-z0-9_%\-]+)/", f.get("leagueUrl") or f.get("categoryUrl") or "")
                if mm and not mm.group(1).lower().startswith(("all_",)):
                    comp = mm.group(1).replace("_", " ")
            event = f.get("event_name_alias") or f.get("eventname")
            if not event:
                continue
            eid = f.get("vc_event_id") or f.get("event_id")
            if not eid:
                mm = re.search(r"event_id=(\d+)", f.get("eventUrl") or "")
                eid = mm.group(1) if mm else ""
            start = f.get("event_start_unix_timestamp")
            start_utc = ""
            if start:
                try:
                    start_utc = _dt.datetime.fromtimestamp(int(float(start)), _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, OSError):
                    start_utc = ""
            if not start_utc and f.get("event_start"):
                start_utc = str(f["event_start"]).replace(" ", "T")
            row = {
                "sport": sport,
                "event": event,
                "event_id": str(eid or ""),
                "competition": comp,
                "start": start_utc,
                "venue": f.get("venue") or "",
                "selection": f.get("selection") or f.get("outcome_name") or "",
                "market": f.get("market_alias") or f.get("market_name") or "",
                "olbg_decimal": f.get("odds") or "",
                "olbg_american": f.get("american_odds") or "",
                "olbg_fractional": f.get("fractional_odds") or "",
                "olbg_confidence": f.get("confidence"),
                "olbg_win_tips": f.get("win_tips"),
                "olbg_comments": f.get("comments_count"),
                "olbg_expired": str(f.get("expired") or ""),
                "event_url": ("https://www.olbg.com" + f["eventUrl"]) if str(f.get("eventUrl", "")).startswith("/") else (f.get("eventUrl") or (cap.get("final_url") if str(key).startswith("olbg_event") else "")),
                "capture_key": key,
                "captured_at": cap.get("fetched_at"),
                "page_url": cap.get("final_url"),
                "verbatim": (o.get("fragment") or "")[:300],
            }
            rowkey = (row["sport"], row["event_id"] or row["event"], row["market"], row["selection"])
            if rowkey not in tips or (row["captured_at"] or "") > (tips[rowkey]["captured_at"] or ""):
                tips[rowkey] = row
    # collapse duplicate objects for the same tip; keep whichever copy carries the event link
    collapsed: dict[tuple, dict] = {}
    for r in tips.values():
        k = (r["sport"], norm_event(r["event"]), r["market"], r["selection"])
        cur = collapsed.get(k)
        if cur is None or (not cur.get("event_url") and r.get("event_url")):
            collapsed[k] = r
    rows = sorted(collapsed.values(), key=lambda r: (r["start"], r["sport"], r["event"]))
    out = {
        "meta": {
            "generated_at": ANCHOR,
            "source": "OLBG.com sport hub pages captured by scripts/ledger_capture.py",
            "note": "One row per OLBG tip. The tip is OLBG's published selection; the price is OLBG's quoted bookmaker price and is NOT our line.",
            "pages": pages,
            "tip_rows": len(rows),
            "events": len({(r["sport"], r["event_id"] or r["event"]) for r in rows}),
            "sports": sorted({r["sport"] for r in rows}),
        },
        "tips": rows,
    }
    (DATA / "olbg.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows)} tips, {out['meta']['events']} events, {len(pages)} pages")
    for p in pages:
        print(f"  {p['objects']:>3}  {p['key']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
