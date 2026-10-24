#!/usr/bin/env python3
"""Playbook seed: normalise the first-hand OLBG capture + official capture into fixtures.

Inputs (committed, first-hand):
  data/playbook/olbg_capture.json   rows read off OLBG's rendered hubs on 2026-10-24
  data/playbook/official.json       values read off governing-body feeds the same evening

Outputs:
  data/playbook/fixtures.json       one row per event, with its OLBG link and provenance
  data/playbook/sources.json        the source register (every URL used anywhere)
  data/playbook/flagged.json        things that could not be confirmed, and why

Nothing here calls the network. Every value traces to a URL in sources.json.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "playbook"

CAPTURE_UTC = "2026-10-24T22:50:00Z"
CAPTURE_END_UTC = "2026-10-24T23:05:00Z"
SESSION = "arena/3ef9031e-olbg2"

# ---------------------------------------------------------------- sport register
# Hub URL, numeric OLBG sport id, and the league path segment seen on the rendered
# page for each competition. Every entry below was read off the live hub.
SPORTS = [
    ("Golf", "golf", 5, "https://www.olbg.com/betting-tips/Golf/5", "All_Golf/All_Events"),
    ("Volleyball", "volleyball", 21, "https://www.olbg.com/betting-tips/Volleyball/21", "All_Volleyball/All_Events"),
    ("Rugby Union", "rugby-union", 9, "https://www.olbg.com/betting-tips/Rugby_Union/9", "All_Rugby_Union/All_Events"),
    ("Cricket", "cricket", 7, "https://www.olbg.com/betting-tips/Cricket/7", "All_Cricket/All_Events"),
    ("Snooker", "snooker", 8, "https://www.olbg.com/betting-tips/Snooker/8", "All_Snooker/All_Events"),
    ("Darts", "darts", 15, "https://www.olbg.com/betting-tips/Darts/15", "All_Darts/All_Events"),
    ("Baseball", "baseball", 12, "https://www.olbg.com/betting-tips/Baseball/12", "MLB/MLB"),
    ("Gaelic Sports", "gaelic-sports", 25, "https://www.olbg.com/betting-tips/Gaelic_Football/25", "All_Gaelic_Football/All_Events"),
    ("Greyhounds", "greyhounds", 28, "https://www.olbg.com/betting-tips/Greyhounds/28", "All_Greyhounds/All_Events"),
    ("Tennis", "tennis", 3, "https://www.olbg.com/betting-tips/Tennis/3", "All_Tennis/All_Events"),
    ("Motor Racing", "motor-racing", 14, "https://www.olbg.com/betting-tips/Motor_Racing/14", "All_Motor_Racing/All_Events"),
    ("Handball", "handball", 20, "https://www.olbg.com/betting-tips/Handball/20", "All_Handball/All_Events"),
    ("Ice Hockey", "ice-hockey", 13, "https://www.olbg.com/betting-tips/Ice_Hockey/13", "NHL/NHL"),
    ("Basketball", "basketball", 4, "https://www.olbg.com/betting-tips/Basketball/4", "NBA/NBA"),
    ("Rugby League", "rugby-league", 10, "https://www.olbg.com/betting-tips/Rugby_League/10", "All_Rugby_League/All_Events"),
]
SPORT_BY_NAME = {s[0]: s for s in SPORTS}

# competitions whose rendered path differs from the sport default (read off the page)
COMP_PATH = {
    ("Ice Hockey", "Switzerland NLA"): "Other/Switzerland_NLA",
    ("Ice Hockey", "Germany Eishockey Liga"): "Other/Germany_Eishockey_Liga",
    ("Basketball", "Korea KBL"): "Other/Korea_KBL",
    ("Gaelic Sports", "Kilkenny SHC"): None,          # hurling sits on its own sport hub
}

HURLING = ("Hurling", "hurling", 26, "https://www.olbg.com/betting-tips/Hurling/26", "All_Hurling/All_Events")

# Hub results, transcribed from the rendered pages. `match_rows` counts the events
# with at least one tip that the hub actually listed at capture time.
HUB_RESULTS = {
    "Golf": "No tips found.",
    "Snooker": "No tips found.",
    "Motor Racing": "No tips found.",
    "Rugby League": "0 match events; 3 season outrights only",
}

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


def slugify_event(name: str) -> str:
    out = name.replace(" @ ", "_@_").replace(" vs ", "_vs_").replace(" v ", "_v_")
    out = re.sub(r"[^A-Za-z0-9_@.\-:]", "_", out)
    out = re.sub(r"_+", "_", out).strip("_")
    return out


def parse_display(display: str) -> tuple[str, str, str | None]:
    """Return (iso_date, kind, utc_estimate).

    OLBG prints clock times in the viewer's timezone with no suffix. From this
    environment that is US Eastern (UTC-4 until 2026-11-01), so the estimate below
    adds four hours. It is an ESTIMATE derived from a rendered string, never an
    official start time, and is labelled as such everywhere it is used.
    """
    display = display.strip()
    m = re.match(r"^Today\s+(\d{1,2}:\d{2})$", display)
    if m:
        return "2026-10-24", "today", _plus4("2026-10-24", m.group(1))
    m = re.match(r"^Tomorrow\s+(\d{1,2}:\d{2})$", display)
    if m:
        return "2026-10-25", "tomorrow", _plus4("2026-10-25", m.group(1))
    m = re.match(r"^(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{1,2}:\d{2})$", display)
    if m:
        day, mon, hm = int(m.group(1)), MONTHS[m.group(2)], m.group(3)
        iso = f"2026-{mon:02d}-{day:02d}"
        return iso, "dated", _plus4(iso, hm)
    return "", "unknown", None


def _plus4(iso_date: str, hm: str) -> str:
    h, mi = (int(x) for x in hm.split(":"))
    dt = datetime.fromisoformat(iso_date).replace(hour=h, minute=mi, tzinfo=timezone.utc)
    return (dt + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ")


def split_sides(event: str, competition: str) -> tuple[str | None, str | None, str]:
    """Return (home, away, shape). shape is one of @ / v / race."""
    if " @ " in event:
        away, home = event.split(" @ ", 1)
        return home.strip(), away.strip(), "at"
    for sep in (" vs ", " v "):
        if sep in event:
            home, away = event.split(sep, 1)
            return home.strip(), away.strip(), "v"
    return None, None, "race"


def event_url(sport: str, competition: str, event: str, eid: str) -> str | None:
    if sport == "Gaelic Sports" and competition == "Kilkenny SHC":
        _, _, sid, hub, path = HURLING
    else:
        _, _, sid, hub, path = SPORT_BY_NAME[sport]
        if (sport, competition) in COMP_PATH and COMP_PATH[(sport, competition)]:
            path = COMP_PATH[(sport, competition)]
    if not eid:
        return None
    return f"https://www.olbg.com/betting-tips/{sport.replace(' ', '_')}/{path}/{slugify_event(event)}/{sid}?event_id={eid}"


def fid_for(sport_slug: str, eid: str, event: str) -> str:
    raw = f"{sport_slug}|{eid or event}"
    return "pb-" + hashlib.sha1(raw.encode()).hexdigest()[:10]


def main() -> None:
    cap = json.loads((DATA / "olbg_capture.json").read_text())
    off = json.loads((DATA / "official.json").read_text())

    # ---- official NHL lookup keyed by the two abbreviations
    nhl_games = {}
    for g in off["nhl"]["games"]:
        nhl_games[(g["home"], g["away"])] = g
    abbr_by_nick = {v["name"].split()[-1]: k for k, v in off["nhl"]["teams"].items()}

    def nhl_abbrev(side):
        if not side:
            return None
        for nick, ab in abbr_by_nick.items():
            if nick in side:
                return ab
        return None

    fixtures = []
    sources = {}

    def add_source(url: str, label: str, kind: str) -> None:
        if not url:
            return
        sources.setdefault(url, {"url": url, "label": label, "kind": kind, "rows": []})

    for sport, slug, sid, hub, _path in SPORTS + [HURLING]:
        add_source(hub, f"OLBG {sport} hub", "olbg-hub")

    for row in cap["rows"]:
        sport = row["s"]
        comp = row["c"]
        event = row["e"]
        eid = row["id"]
        # hurling rows are listed under the Gaelic Football hub but are a different sport id
        hurling = sport == "Gaelic Sports" and comp == "Kilkenny SHC"
        slug = HURLING[1] if hurling else SPORT_BY_NAME[sport][1]
        sid = HURLING[2] if hurling else SPORT_BY_NAME[sport][2]
        home, away, shape = split_sides(event, comp)
        iso, kind, est = parse_display(row["t"])
        url = event_url(sport, comp, event, eid)
        add_source(url, f"OLBG event {event}", "olbg-event")
        if url:
            sources[url]["rows"].append(eid)

        official = None
        if sport == "Ice Hockey" and comp == "NHL":
            ha, aa = nhl_abbrev(home), nhl_abbrev(away)
        else:
            ha, aa = None, None
        if ha and aa:
            g = nhl_games.get((ha, aa))
            if g:
                official = {
                    "tier": "A",
                    "league": "NHL",
                    "nhl_game_id": g["nhl_id"],
                    "start_utc_official": g["utc"],
                    "venue": g["venue"],
                    "neutral_site": g["neutral"],
                    "home_abbrev": ha,
                    "away_abbrev": aa,
                    "home": off["nhl"]["teams"][ha],
                    "away": off["nhl"]["teams"][aa],
                    "leaders": {ha: off["nhl"]["leaders"].get(ha, []), aa: off["nhl"]["leaders"].get(aa, [])},
                    "sources": off["nhl"]["sources"],
                }
                for u, lab in (("schedule", "NHL schedule feed"), ("score", "NHL score feed"),
                               ("team_summary", "NHL team summary (season totals)")):
                    add_source(off["nhl"]["sources"][u], lab, "official")

        fixtures.append({
            "fid": fid_for(slug, eid, event),
            "sport": sport,
            "sport_slug": slug,
            "sport_id": sid,
            "competition": comp,
            "event": event,
            "home": home,
            "away": away,
            "shape": shape,
            "olbg_event_id": eid,
            "olbg_url": url,
            "olbg_hub": HURLING[3] if hurling else SPORT_BY_NAME[sport][3],
            "source_url": url,
            "source_label": "OLBG",
            "olbg_display": row["t"],
            "olbg_day": iso,
            "olbg_day_kind": kind,
            "start_utc_estimate": est,
            "start_utc_basis": "derived from OLBG's rendered clock (no timezone suffix; US Eastern assumed)",
            "market": row["m"],
            "tipped_selection": row["sel"],
            "tips_won": row["w"],
            "tips_total": row["n"],
            "tip_share": (row["w"] / row["n"]) if row["n"] else None,
            "status_at_capture": ("not_started" if (est and est > CAPTURE_UTC) else "started_or_unknown"),
            "official": official,
            "tier": "A" if official else "B",
        })

    # the fifth NHL game on the same night has no OLBG row at capture time
    g = next(g for g in off["nhl"]["games"] if g["nhl_id"] == "2026020180")
    fixtures.append({
        "fid": "pb-nhl-2026020180",
        "sport": "Ice Hockey", "sport_slug": "ice-hockey", "sport_id": 13,
        "competition": "NHL",
        "event": "FLA Panthers @ CHI Blackhawks",
        "home": "CHI Blackhawks", "away": "FLA Panthers", "shape": "at",
        "olbg_event_id": None, "olbg_url": None,
        "source_url": off["nhl"]["sources"]["schedule"], "source_label": "NHL schedule feed",
        "olbg_hub": SPORT_BY_NAME["Ice Hockey"][3],
        "olbg_display": None, "olbg_day": "2026-10-25", "olbg_day_kind": "official-only",
        "start_utc_estimate": g["utc"],
        "start_utc_basis": "official NHL schedule feed",
        "market": None, "tipped_selection": None, "tips_won": 0, "tips_total": 0,
        "tip_share": None, "status_at_capture": "not_started", "tier": "A",
        "official": {
            "tier": "A", "league": "NHL", "nhl_game_id": "2026020180",
            "start_utc_official": g["utc"], "venue": g["venue"], "neutral_site": False,
            "home_abbrev": "CHI", "away_abbrev": "FLA",
            "home": off["nhl"]["teams"]["CHI"], "away": off["nhl"]["teams"]["FLA"],
            "leaders": {"CHI": off["nhl"]["leaders"]["CHI"], "FLA": off["nhl"]["leaders"]["FLA"]},
            "sources": off["nhl"]["sources"],
        },
    })

    for key, lab in (("schedule", "NHL schedule feed"), ("score", "NHL score feed"),
                     ("standings", "NHL standings (25 Oct snapshot)"),
                     ("team_summary", "NHL team summary (season totals)")):
        if off["nhl"]["sources"].get(key):
            add_source(off["nhl"]["sources"][key], lab, "official")
    add_source("https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-25",
               "MLB schedule feed (25 Oct probe: no games)", "official")

    # ---- outrights (kept apart so they never inflate the match count)
    outrights = []
    for row in cap["outrights"]:
        sport = row["s"]
        sid, hub, path = (HURLING[2], HURLING[3], HURLING[4]) if sport == "Gaelic Sports" and "Hurling" in row["e"] \
            else (SPORT_BY_NAME[sport][2], SPORT_BY_NAME[sport][3], SPORT_BY_NAME[sport][4])
        url = f"https://www.olbg.com/betting-tips/{sport.replace(' ', '_')}/{path}/{slugify_event(row['e'])}/{sid}?event_id={row['id']}"
        add_source(url, f"OLBG outright {row['e']}", "olbg-event")
        outrights.append({
            "sport": sport, "sport_slug": SPORT_BY_NAME[sport][1],
            "event": row["e"], "olbg_event_id": row["id"], "olbg_url": url,
            "olbg_display": row["t"], "market": row["m"], "tipped_selection": row["sel"],
            "tips_won": row["w"], "tips_total": row["n"],
            "tip_share": (row["w"] / row["n"]) if row["n"] else None,
        })

    by_sport = {}
    for f in fixtures:
        by_sport.setdefault(f["sport"], []).append(f)

    # ---- flags: everything that could not be confirmed first-hand
    flags = []
    for sport in [s[0] for s in SPORTS]:
        rows = [f for f in fixtures if f["sport"] == sport]
        if not rows:
            flags.append({
                "id": f"NO-EVENTS-{SPORT_BY_NAME[sport][1]}",
                "sport": sport, "severity": "open",
                "title": f"{sport}: no match event on OLBG at capture time",
                "detail": HUB_RESULTS.get(sport, "The hub listed no event with at least one tip."),
                "source": SPORT_BY_NAME[sport][3],
            })
    flags.append({
        "id": "PRICE-SUPPRESSION", "sport": "All", "severity": "open",
        "title": "OLBG does not show bookmaker prices to this location",
        "detail": ("Every event card rendered 'WIN @' with an empty price slot and every event page rendered the market "
                   "without a decimal or fractional price. Tip counts, the tipped selection and the tip share did "
                   "render. No OLBG price is therefore quoted anywhere on this desk; every price published here is "
                   "one this desk originated and is labelled as such."),
        "source": "https://www.olbg.com/betting-tips/Ice_Hockey/13",
    })
    flags.append({
        "id": "CLOCK-QUIRK", "sport": "All", "severity": "open",
        "title": "OLBG's rendered clock runs seven minutes ahead of the official UTC conversion",
        "detail": ("NHL game 2026020182 starts 2026-10-25T23:00:00Z, which is 19:00 US Eastern, and OLBG printed "
                   "'Tomorrow 19:07'. The same +7 minute offset appears on all twenty NHL rows checked. No OLBG clock "
                   "string is used as a start time; the official feed is used where one was read."),
        "source": "https://api-web.nhle.com/v1/schedule/2026-10-25",
    })
    flags.append({
        "id": "HANDICAP-DEFAULT", "sport": "Handball", "severity": "open",
        "title": "Nine handball rows show 'Tie' as the most-tipped selection",
        "detail": ("On the handball hub the modal selection is 'Tie' on nine rows, several at 100% of a small sample "
                   "(7/7, 4/4, 3/3). A drawn handball match is uncommon, so a 'Tie' row carrying every tip is more "
                   "likely a rendering of the draw leg of a three-way market than a genuine crowd position. Those rows "
                   "are published as listed but are not used to originate a price."),
        "source": "https://www.olbg.com/betting-tips/Handball/20",
    })
    flags.append({
        "id": "TENNIS-DATES", "sport": "Tennis", "severity": "open",
        "title": "Fourteen tennis rows carry an OLBG start time but no official confirmation",
        "detail": ("The ATP scores page returned only page chrome and no draw, and the WTA draw pages were not read. "
                   "Fixture, players and OLBG's clock are recorded; the official start time and the tournament name are "
                   "left blank on every tennis row rather than guessed."),
        "source": "https://www.olbg.com/betting-tips/Tennis/3",
    })
    flags.append({
        "id": "TIER-B-PRICING", "sport": "All", "severity": "note",
        "title": "Thirteen sports carry no governing-body statistics in this capture",
        "detail": ("Only the five NHL fixtures have league totals read from an official feed. For every other fixture "
                   "the win price is a normalised read of the tip share OLBG itself publishes, and only the win market "
                   "is originated, because a handicap or a total cannot be derived without scoring data. Those rows are "
                   "graded no higher than medium however short the price."),
        "source": "https://www.olbg.com/betting-tips",
    })
    flags.append({
        "id": "UNVERIFIED-FEEDS", "sport": "All", "severity": "open",
        "title": "League sites that returned no table to this reader",
        "detail": ("Lega Pallavolo's classifica page returned navigation only (the table is rendered client-side), and "
                   "the Handball-Bundesliga table URL redirected to a 404 page. Volleyball and handball therefore stay "
                   "on tier B."),
        "source": "https://www.legavolley.it/classifica/?IdCampionato=999",
    })
    flags.append({
        "id": "MLB-NO-GAME", "sport": "Baseball", "severity": "note",
        "title": "MLB lists no game on 25 October 2026",
        "detail": ("The MLB schedule feed returns totalGames 0 for 2026-10-25. The only baseball row OLBG lists is "
                   "TB @ MIL, which starts 2026-10-25T00:00:00Z."),
        "source": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-25",
    })

    out_fixtures = {
        "generated_utc": CAPTURE_END_UTC,
        "session": SESSION,
        "capture_utc": CAPTURE_UTC,
        "count": len(fixtures),
        "match_count": sum(1 for f in fixtures if f["olbg_event_id"]),
        "tier_a": sum(1 for f in fixtures if f["tier"] == "A"),
        "tier_b": sum(1 for f in fixtures if f["tier"] == "B"),
        "by_sport": {s: sum(1 for f in fixtures if f["sport"] == s) for s in [x[0] for x in SPORTS]},
        "fixtures": sorted(fixtures, key=lambda f: (f["olbg_day"], f["sport"], f["event"])),
    }
    (DATA / "fixtures.json").write_text(json.dumps(out_fixtures, indent=1) + "\n")
    (DATA / "outrights.json").write_text(json.dumps({"count": len(outrights), "outrights": outrights}, indent=1) + "\n")
    (DATA / "sources.json").write_text(json.dumps({
        "captured_utc": CAPTURE_UTC,
        "count": len(sources),
        "sources": sorted(sources.values(), key=lambda s: (s["kind"], s["url"])),
    }, indent=1) + "\n")
    (DATA / "flagged.json").write_text(json.dumps({
        "generated_utc": CAPTURE_END_UTC, "count": len(flags), "flags": flags,
    }, indent=1) + "\n")

    print(f"playbook_seed: {len(fixtures)} fixtures ({out_fixtures['match_count']} with an OLBG event id), "
          f"{out_fixtures['tier_a']} tier A, {len(outrights)} outrights, {len(sources)} sources, {len(flags)} flags")


if __name__ == "__main__":
    main()
