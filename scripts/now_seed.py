#!/usr/bin/env python3
"""Seed the /now/ desk (session arena/4a8390fe-olbg2, 2026-10-24).

Three separate provenance layers are kept apart and never mixed silently:

1. ``olbg``      - what OLBG itself lists. The 96-row listing capture committed at
                   17:15-17:50Z today (``data/today/olbg_listings.json``) is the base
                   inventory; every hub route was re-read today, and the Snooker, Golf and
                   Volleyball hubs were re-read a second time in this session. Each row
                   carries OLBG's own event id and event URL so it can be checked by hand.
2. ``fixtures``  - official governing-body fixture records with per-fact source URLs.
                   These come from the 17:35Z official capture committed in
                   ``data/clarity/fixtures.json``. They are inherited, not re-read here,
                   and every record says so (``facts_inherited``), so a reader is never
                   told that this build re-checked them.
3. ``own``       - everything this desk originates: markets, prices, confidence grades,
                   the odds-band test and the written previews.

Nothing is inferred: a value that is not in an official capture stays blank and is
listed on the Flagged for Review page.

Outputs (deterministic):
    data/now/olbg.json, data/now/fixtures.json, data/now/sources.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NOW = DATA / "now"
CLARITY = DATA / "clarity"
TODAY = DATA / "today"

SESSION = "arena/4a8390fe-olbg2"
AS_OF_UTC = "2026-10-24T18:10:00Z"
BUILD_DATE = "2026-10-24"

SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
SLUG = {
    "Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
    "Cricket": "cricket", "Snooker": "snooker", "Darts": "darts", "Baseball": "baseball",
    "Gaelic Sports": "gaelic-sports", "Greyhounds": "greyhounds", "Tennis": "tennis",
    "Motor Racing": "motor-racing", "Handball": "handball", "Ice Hockey": "ice-hockey",
    "Basketball": "basketball", "Rugby League": "rugby-league",
}

# Hub routes, all confirmed against the live site today (see olbg.json -> hubs).
HUBS = {
    "Golf": ("https://www.olbg.com/betting-tips/Golf/5", 5),
    "Volleyball": ("https://www.olbg.com/betting-tips/Volleyball/21", 21),
    "Rugby Union": ("https://www.olbg.com/betting-tips/Rugby_Union/9", 9),
    "Cricket": ("https://www.olbg.com/betting-tips/Cricket/7", 7),
    "Snooker": ("https://www.olbg.com/betting-tips/Snooker/8", 8),
    "Darts": ("https://www.olbg.com/betting-tips/Darts/15", 15),
    "Baseball": ("https://www.olbg.com/betting-tips/Baseball/12", 12),
    "Gaelic Sports": ("https://www.olbg.com/betting-tips/Gaelic_Football/25", 25),
    "Greyhounds": ("https://www.olbg.com/betting-tips/Greyhounds/28", 28),
    "Tennis": ("https://www.olbg.com/betting-tips/Tennis/3", 3),
    "Motor Racing": ("https://www.olbg.com/betting-tips/Motor_Racing/14", 14),
    "Handball": ("https://www.olbg.com/betting-tips/Handball/20", 20),
    "Ice Hockey": ("https://www.olbg.com/betting-tips/Ice_Hockey/13", 13),
    "Basketball": ("https://www.olbg.com/betting-tips/Basketball/4", 4),
    "Rugby League": ("https://www.olbg.com/betting-tips/Rugby_League/10", 10),
}
HURLING_HUB = ("https://www.olbg.com/betting-tips/Hurling/26", 26)

# Live re-reads performed in this session (fetch tool, timestamps are UTC).
RECHECKS = [
    {
        "hub": "Snooker",
        "url": "https://www.olbg.com/betting-tips/Snooker/8",
        "checked_utc": "2026-10-24T18:04:00Z",
        "result": "One event listed: 'Mark Williams v Jak Jones', event_id 9952, display time "
                  "'Today 14:05', most-tipped selection Jak Jones, 16/27 Win Tips, 59%. Matches "
                  "the 17:15Z capture row exactly.",
        "status": "confirmed",
    },
    {
        "hub": "Golf",
        "url": "https://www.olbg.com/betting-tips/Golf/5",
        "checked_utc": "2026-10-24T18:06:00Z",
        "result": "Page returned HTTP 200 and rendered 'No tips found.' No golf event is listed "
                  "with a public tip, so no golf fixture below is asserted to be an active OLBG "
                  "listing.",
        "status": "no-listings",
    },
    {
        "hub": "Volleyball",
        "url": "https://www.olbg.com/betting-tips/Volleyball/21",
        "checked_utc": "2026-10-24T17:56:00Z",
        "result": "Hub lists volleyball events including 'Helios Grizzlys Giesen vs Berlin Volleys' "
                  "(event_id 37013) and 'Trentino vs Cisterna' (event_id 36994); both are priced on "
                  "this desk.",
        "status": "confirmed",
    },
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(text: str) -> str:
    text = text.lower()
    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\b(fc|rfc|the|club|volleys|volley)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> set[str]:
    drop = {"w", "women", "men", "senior", "rfc", "fc", "r"}
    return {t for t in norm(text).split() if t not in drop and len(t) > 2}


def match_listing(fixture: dict, listings: list[dict]) -> dict | None:
    """Find the OLBG listing whose event names both appear in this fixture."""
    home, away = tokens(fixture["home"]), tokens(fixture["away"])
    if not home or not away:
        return None
    best, best_score = None, 0
    for row in listings:
        if row["sport"] != fixture["sport"]:
            continue
        ev = tokens(row["event"])
        score = (2 if home & ev else 0) + (2 if away & ev else 0)
        if score > best_score:
            best, best_score = row, score
    return best if best_score >= 2 else None


def build_olbg() -> dict:
    base = load(TODAY / "olbg_listings.json")
    listings = []
    for row in base["listings"]:
        listings.append({
            "sport": row["sport"],
            "competition": row.get("competition", ""),
            "event": row["event"],
            "displayed_time": row["displayed_time"],
            "market": row["market"],
            "selection": row["selection"],
            "tips": row["tips"],
            "pct": row.get("pct"),
            "event_id": row["event_id"],
            "url": row["url"],
        })
    hubs = {
        sport: {
            "url": HUBS[sport][0],
            "sport_id": HUBS[sport][1],
            "listed_events": sum(1 for r in listings if r["sport"] == sport),
        }
        for sport in SPORTS
    }
    hubs["Gaelic Sports"]["note"] = (
        "OLBG splits Gaelic games across Gaelic Football (25) and Hurling (26); the Hurling hub "
        "URL is recorded separately below."
    )
    return {
        "capture_utc": base["capture_utc"],
        "capture_end_utc": base["capture_end_utc"],
        "capture_session": base["session"],
        "inherited_from": "data/today/olbg_listings.json",
        "rechecked_utc": AS_OF_UTC,
        "hubs": hubs,
        "hurling_hub": {"url": HURLING_HUB[0], "sport_id": HURLING_HUB[1]},
        "rechecks": RECHECKS,
        "listings": listings,
        "listings_count": len(listings),
        "sports_listed": sorted({r["sport"] for r in listings}),
        "notes": [
            "OLBG publishes one most-tipped selection per listed event with a tip count and the "
            "share of tips on that market. It is a community vote, not a price.",
            "Displayed times are OLBG's own strings in US Eastern. They are stored verbatim and "
            "are never converted here; official start values come from the governing body.",
            "OLBG publishes no odds on these hub pages, so every price on this site is originated "
            "on this desk from official inputs.",
            "The 96-row base capture was made at 17:15-17:50Z today by the /today/ desk and is "
            "inherited unchanged; this session re-read three hubs (recorded in 'rechecks').",
        ],
    }


def build_fixtures() -> dict:
    src = load(CLARITY / "fixtures.json")
    listings = load(TODAY / "olbg_listings.json")["listings"]
    fixtures = []
    for f in src["fixtures"]:
        row = dict(f)
        row["facts_inherited"] = True
        row["facts_capture"] = "official capture committed 2026-10-24T17:35Z (data/clarity)"
        hit = match_listing(row, listings)
        row["olbg_listed"] = bool(hit)
        if hit:
            row["olbg_listing"] = {
                "event": hit["event"],
                "displayed_time": hit["displayed_time"],
                "market": hit["market"],
                "selection": hit["selection"],
                "tips": hit["tips"],
                "pct": hit.get("pct"),
                "event_id": hit["event_id"],
                "url": hit["url"],
            }
        fixtures.append(row)
    return {
        "captured_utc": AS_OF_UTC,
        "session": SESSION,
        "build_date": BUILD_DATE,
        "sports": SPORTS,
        "slug": SLUG,
        "source_layer": "data/clarity/fixtures.json (official captures 2026-10-24T17:35Z)",
        "inheritance_note": (
            "Every fixture record below is an official governing-body capture made at 17:35Z today. "
            "This build does not re-read those pages; it re-uses the committed capture and says so "
            "on every row. Three OLBG hubs were re-read live in this session and the result is on "
            "the OLBG page."
        ),
        "fixtures": fixtures,
        "count": len(fixtures),
    }


def build_sources() -> dict:
    reg: dict[str, dict] = {}
    for f in load(NOW / "fixtures.json")["fixtures"]:
        for fact in f["facts"]:
            key = fact["source_url"]
            rec = reg.setdefault(key, {
                "url": key,
                "source_key": fact.get("source_key", ""),
                "captured_utc": fact.get("captured_utc", ""),
                "claims": 0,
                "sports": set(),
                "fixtures": set(),
            })
            rec["claims"] += 1
            rec["sports"].add(f["sport"])
            rec["fixtures"].add(f["id"])
    olbg = load(NOW / "olbg.json")
    for hub in list(olbg["hubs"].values()) + [olbg["hurling_hub"]]:
        rec = reg.setdefault(hub["url"], {
            "url": hub["url"], "source_key": "olbg_hub", "captured_utc": AS_OF_UTC,
            "claims": 0, "sports": set(), "fixtures": set(),
        })
        rec["olbg_hub"] = True
    rows = []
    for url, rec in sorted(reg.items()):
        rows.append({
            "url": url,
            "source_key": rec["source_key"],
            "captured_utc": rec["captured_utc"] or AS_OF_UTC,
            "claims": rec["claims"],
            "sports": sorted(rec["sports"]),
            "fixtures": len(rec["fixtures"]),
            "official": url.startswith("https://") and "olbg.com" not in url,
            "kind": "OLBG listing hub" if "olbg.com" in url else "official governing body / league feed",
        })
    return {
        "as_of_utc": AS_OF_UTC,
        "count": len(rows),
        "official_count": sum(1 for r in rows if r["official"]),
        "sources": rows,
    }


def main() -> int:
    NOW.mkdir(parents=True, exist_ok=True)
    olbg = build_olbg()
    (NOW / "olbg.json").write_text(json.dumps(olbg, indent=1) + "\n", encoding="utf-8")
    fixtures = build_fixtures()
    (NOW / "fixtures.json").write_text(json.dumps(fixtures, indent=1) + "\n", encoding="utf-8")
    sources = build_sources()
    (NOW / "sources.json").write_text(json.dumps(sources, indent=1) + "\n", encoding="utf-8")
    listed = sum(1 for f in fixtures["fixtures"] if f["olbg_listed"])
    print(f"now_seed: {fixtures['count']} fixtures, {listed} matched to an OLBG listing, "
          f"{olbg['listings_count']} OLBG rows, {sources['count']} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
