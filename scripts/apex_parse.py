#!/usr/bin/env python3
"""Parse the raw /apex/ captures into one compact digest committed to the repo.

Runs on the GitHub-hosted runner right after scripts/apex_collect.py, because the raw
bodies travel as an artifact only and the authoring sandbox cannot download artifacts.
This script interprets nothing about the sport: it records what each body contains.

Outputs data/apex/captures/parsed.json with four sections:
  listings  - every OLBG hub row (event, market, most-tipped selection, tip counts,
              OLBG decimal/American price, start timestamp, event id, urls, expired flag)
  official  - compact digest of the governing-body JSON feeds (NHL, MLB, NBA, ...)
  text      - tag-stripped text excerpts of official HTML pages (bounded per key)
  events    - what each captured OLBG event page and its __data.json route carries,
              including every market/selection/odds object found (the full market board
              check), bounded per key

Deterministic: same raw captures, byte-identical output.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAP_DIR = ROOT / "data" / "apex" / "captures"
RAW_DIR = CAP_DIR / "raw"
MANIFEST = CAP_DIR / "manifest.json"
OUT = CAP_DIR / "parsed.json"

TEXT_LIMIT = 14000        # per official HTML page
EVENT_TEXT_LIMIT = 5000   # per OLBG event page
EVENT_DATA_LIMIT = 400    # max market/odds objects kept per event page

OBJ_START = re.compile(r'\{id:"([0-9a-f]{40})"')
FIELD_RE = re.compile(r'(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<val>"(?:[^"\\]|\\.)*"|[^,}\]]+)')

OLBG_SPORT = {
    "Gaelic Football": "Gaelic Sports", "Gaelic Hurling": "Gaelic Sports",
    "Ice Hockey": "Ice Hockey", "Motor Racing": "Motor Racing",
}


def unquote(v: str):
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1].replace('\\"', '"')
    if v in ("null", "void 0", "undefined"):
        return None
    if v == "true":
        return True
    if v == "false":
        return False
    try:
        return json.loads(v)
    except ValueError:
        return v


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def body(caps: dict, key: str) -> str:
    rec = caps.get(key)
    if not rec or not rec.get("stored"):
        return ""
    p = RAW_DIR / rec["stored"]
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def as_json(caps: dict, key: str):
    try:
        return json.loads(body(caps, key))
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------- OLBG hub listings
def parse_listings(caps: dict):
    rows, pages = [], {}
    for key in sorted(caps):
        if not key.startswith("olbg_hub_"):
            continue
        rec = caps[key]
        text = body(caps, key)
        pages[key] = {"status": rec.get("http_status"), "bytes": rec.get("bytes"),
                      "sha256": rec.get("sha256"), "url": rec.get("url"),
                      "captured_at": rec.get("requested_at"), "objects": 0}
        count = 0
        for m in OBJ_START.finditer(text):
            chunk = text[m.start(): m.start() + 4000]
            fields: dict = {}
            for f in FIELD_RE.finditer(chunk):
                fields.setdefault(f.group("key"), unquote(f.group("val")))
            event = fields.get("event_name_alias")
            if not event:
                continue
            count += 1
            sport = (fields.get("sport") or "").replace("_", " ")
            if not sport:
                mm = re.search(r"/betting-tips/([A-Za-z_]+)/", (fields.get("eventUrl") or ""))
                sport = mm.group(1).replace("_", " ") if mm else ""
            sport = OLBG_SPORT.get(sport, sport)
            eid = ""
            mm = re.search(r"event_id=(\d+)", fields.get("eventUrl") or "")
            if mm:
                eid = mm.group(1)
            start = ""
            ts = fields.get("event_start_unix_timestamp")
            if ts:
                try:
                    start = dt.datetime.fromtimestamp(int(float(ts)), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, OSError):
                    start = ""
            url = fields.get("eventUrl") or ""
            if url.startswith("/"):
                url = "https://www.olbg.com" + url
            rows.append({
                "hub": key, "sport": sport,
                "competition": fields.get("menu_league") or fields.get("tournament") or "",
                "event": event, "event_id": eid, "start_utc": start,
                "selection": fields.get("selection") or "",
                "market": fields.get("market_alias") or fields.get("market_name") or "",
                "decimal": str(fields.get("odds") or ""),
                "american": str(fields.get("american_odds") or ""),
                "confidence": fields.get("confidence"),
                "win_tips": fields.get("win_tips"),
                "expired": str(fields.get("expired") or ""),
                "event_url": url,
            })
        pages[key]["objects"] = count
    return rows, pages


# --------------------------------------------------------------------- official JSON feeds
def nhl_schedule(digest: dict, caps: dict, key: str):
    d = as_json(caps, key)
    if not d:
        digest[key] = {"error": "unparseable or failed capture"}
        return
    games = []
    for day in (d.get("gameWeek") or []):
        for g in (day.get("games") or []):
            games.append({
                "id": g.get("id"), "date": g.get("startTimeUTC"),
                "venue": (g.get("venue") or {}).get("default"),
                "state": g.get("gameState"),
                "home": (g.get("homeTeam") or {}).get("abbrev"),
                "away": (g.get("awayTeam") or {}).get("abbrev"),
                "homeRecord": (g.get("homeTeam") or {}).get("record"),
                "awayRecord": (g.get("awayTeam") or {}).get("record"),
            })
    digest[key] = {"gameDay": d.get("gameDate"), "games": games}


def nhl_standings(digest: dict, caps: dict, key: str):
    d = as_json(caps, key)
    if not d:
        digest[key] = {"error": "unparseable or failed capture"}
        return
    teams = []
    for t in (d.get("standings") or []):
        teams.append({
            "abbrev": t.get("teamAbbrev", {}).get("default"),
            "gp": t.get("gamesPlayed"), "wins": t.get("wins"), "losses": t.get("losses"),
            "otl": t.get("otLosses"), "pts": t.get("points"),
            "gf": t.get("goalFor"), "ga": t.get("goalAgainst"),
            "home_w": t.get("homeWins"), "home_l": t.get("homeLosses"), "home_otl": t.get("homeOtLosses"),
            "road_w": t.get("roadWins"), "road_l": t.get("roadLosses"), "road_otl": t.get("roadOtLosses"),
            "streak": (t.get("streakCode") or "") + str(t.get("streakCount") or ""),
            "l10_w": t.get("l10Wins"), "l10_l": t.get("l10Losses"), "l10_otl": t.get("l10OtLosses"),
        })
    digest[key] = {"teams": teams}


def mlb_schedule(digest: dict, caps: dict, key: str):
    d = as_json(caps, key)
    if not d:
        digest[key] = {"error": "unparseable or failed capture"}
        return
    out = []
    for day in (d.get("dates") or []):
        for g in (day.get("games") or []):
            rec = {"date": day.get("date"), "id": g.get("gamePk"),
                   "doubleheader": g.get("doubleHeader"), "gametype": g.get("gameType"),
                   "series": g.get("seriesDescription"), "game_num": g.get("seriesGameNumber"),
                   "state": g.get("status", {}).get("detailedState"),
                   "time": g.get("gameDate"), "venue": (g.get("venue") or {}).get("name")}
            for side in ("home", "away"):
                t = g.get("teams", {}).get(side, {}) or {}
                team = (t.get("team") or {})
                rec[side] = {"name": team.get("name"), "id": team.get("id"),
                             "isWinner": t.get("isWinner"),
                             "score": (t.get("score") if g.get("status", {}).get("abstractGameState") == "Final" else None),
                             "probable": ((t.get("probablePitcher") or {}).get("fullName")),
                             "probable_id": ((t.get("probablePitcher") or {}).get("id"))}
            out.append(rec)
    digest[key] = {"games": out}


def mlb_standings(digest: dict, caps: dict, key: str):
    d = as_json(caps, key)
    if not d:
        digest[key] = {"error": "unparseable or failed capture"}
        return
    out = []
    for rec in (d.get("records") or []):
        for t in (rec.get("teamRecords") or []):
            out.append({"team": (t.get("team") or {}).get("name"),
                        "w": t.get("wins"), "l": t.get("losses"),
                        "pct": t.get("winningPercentage"),
                        "streak": (t.get("streak") or {}).get("streakCode"),
                        "l10": ((t.get("records", {}).get("splitRecords") or [{}])[0]),
                        "home": t.get("home", {}).get("wins"), "home_l": t.get("home", {}).get("losses"),
                        "away": t.get("away", {}).get("wins"), "away_l": t.get("away", {}).get("losses"),
                        "rs": t.get("runsScored"), "ra": t.get("runsAllowed")})
    digest[key] = {"teams": out}


def generic_json(digest: dict, caps: dict, key: str, limit: int = 60000):
    d = as_json(caps, key)
    if d is None:
        digest[key] = {"error": "unparseable or failed capture"}
        return
    s = json.dumps(d, separators=(",", ":"))
    digest[key] = {"truncated": len(s) > limit, "json": json.loads(s[:limit]) if len(s) <= limit else None,
                   "head": s[:limit] if len(s) > limit else None}


# --------------------------------------------------------------------- OLBG event pages
def walk_market_objects(obj, out: list, depth: int = 0):
    """Collect dicts that look like market rows (name + odds) from SvelteKit data."""
    if len(out) >= EVENT_DATA_LIMIT or depth > 25:
        return
    if isinstance(obj, dict):
        keys = {k.lower() for k in obj}
        if (("name" in keys or "runner" in keys or "selection" in keys) and
                any("odds" in k or "price" in k for k in keys)):
            compact = {}
            for k, v in obj.items():
                if isinstance(v, (str, int, float, bool)) or v is None:
                    compact[k] = v
            if compact:
                out.append(compact)
        for v in obj.values():
            walk_market_objects(v, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            walk_market_objects(v, out, depth + 1)


def parse_event_pages(caps: dict):
    pages = {}
    for key in sorted(caps):
        if not key.startswith("olbg_event_"):
            continue
        rec = caps[key]
        if key.endswith("_data"):
            d = as_json(caps, key)
            found = []
            if d is not None:
                walk_market_objects(d, found)
            pages[key] = {"status": rec.get("http_status"), "bytes": rec.get("bytes"),
                          "url": rec.get("url"), "market_objects": found[:EVENT_DATA_LIMIT]}
        else:
            text = strip_tags(body(caps, key))
            pages[key] = {"status": rec.get("http_status"), "bytes": rec.get("bytes"),
                          "url": rec.get("url"), "text": text[:EVENT_TEXT_LIMIT]}
    return pages


# --------------------------------------------------------------------- official HTML text
def parse_text(caps: dict):
    out = {}
    for key in sorted(caps):
        if key.startswith("olbg_") or key in OFFICIAL_JSON_KEYS:
            continue
        rec = caps[key]
        text = strip_tags(body(caps, key))
        out[key] = {"status": rec.get("http_status"), "bytes": rec.get("bytes"),
                    "url": rec.get("url"), "captured_at": rec.get("requested_at"),
                    "error": rec.get("error") or "",
                    "text": text[:TEXT_LIMIT]}
    return out


OFFICIAL_JSON_KEYS = {
    "nhl_sched_26": nhl_schedule, "nhl_sched_27": nhl_schedule,
    "nhl_standings_now": nhl_standings,
    "mlb_sched_ws": mlb_schedule, "mlb_al_standings": mlb_standings, "mlb_nl_standings": mlb_standings,
}
GENERIC_JSON_KEYS = {"nba_scoreboard", "nba_standings", "nba_schedule_v2"}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    caps = {r["key"]: r for r in manifest["captures"]}

    listings, hub_pages = parse_listings(caps)
    digest = {}
    for key, fn in sorted(OFFICIAL_JSON_KEYS.items()):
        if key in caps:
            fn(digest, caps, key)
    for key in sorted(GENERIC_JSON_KEYS):
        if key in caps:
            generic_json(digest, caps, key)
    events = parse_event_pages(caps)
    text = parse_text(caps)

    out = {
        "manifest_captured_at": manifest.get("captured_at"),
        "request_count": manifest.get("count"),
        "ok": manifest.get("ok"), "failed": manifest.get("failed"),
        "captures": {k: {"status": r.get("http_status"), "bytes": r.get("bytes"),
                         "sha256": r.get("sha256"), "url": r.get("url"),
                         "captured_at": r.get("requested_at"), "error": r.get("error") or ""}
                     for k, r in sorted(caps.items())},
        "hub_pages": hub_pages,
        "listings": listings,
        "official": digest,
        "events": events,
        "text": text,
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"parsed: {len(listings)} listing rows, {len(events)} event pages, "
          f"{len(text)} text pages, {len(digest)} json digests -> {OUT}")
    print(f"parsed.json bytes: {OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
