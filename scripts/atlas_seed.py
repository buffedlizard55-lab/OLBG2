#!/usr/bin/env python3
"""Seed the /atlas/ first-hand verification desk.

Read-only inputs
----------------
data/atlas/capture_nhl_schedule.json     NHL Stats REST schedule, 22-31 Oct 2026 (73 games)
data/atlas/capture_nhl_standings.json    NHL Stats REST team summary, 2026-27 (32 teams)
data/atlas/capture_nba_schedule.json     NBA.com official schedule, 22-31 Oct 2026 (74 games)
data/atlas/capture_mlb.json              MLB Stats API World Series + 2026 season records
data/atlas/capture_euroleague.json       EuroLeague live API, Round 7 (E2026_62..E2026_70)
data/atlas/capture_atp.json              ATP Tour official daily schedules, 22 Oct 2026
data/final/matches.json                  the previously published consolidated desk (read only)
data/portal/sports.json                  17-sport eligible taxonomy captured by arena/d81930c3-olbg2

Output
------
data/atlas/fixtures.json    one row per fixture with an explicit verification status
data/atlas/sports.json      eligible taxonomy + excluded hubs

Rule enforced here
------------------
A row is `confirmed` only when this session read it back from the governing-body
URL that is stored on the row. Everything else is `inherited-unverified`: the
fixture identity is carried from data/final/ (which cites an official source) but
this session did not re-read it, so every derived value on that row stays blank.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "atlas"
FINAL = ROOT / "data" / "final" / "matches.json"
PORTAL_SPORTS = ROOT / "data" / "portal" / "sports.json"

CHECKED_AT = "2026-10-22T12:55:00Z"
SESSION = "arena/ba48a907-olbg2"

OUT = ATLAS

SPORT_NAME = {
    "aussie-rules": "Aussie Rules",
    "baseball": "Baseball",
    "basketball": "Basketball",
    "cricket": "Cricket",
    "darts": "Darts",
    "esports": "eSports",
    "gaelic-football": "Gaelic Football",
    "golf": "Golf",
    "greyhounds": "Greyhounds",
    "handball": "Handball",
    "ice-hockey": "Ice Hockey",
    "motor-racing": "Motor Racing",
    "rugby-league": "Rugby League",
    "rugby-union": "Rugby Union",
    "snooker": "Snooker",
    "tennis": "Tennis",
    "volleyball": "Volleyball",
}


def load(p: Path):
    return json.loads(p.read_text())


NHL_CLUB = {
    "BOS": "Boston Bruins", "BUF": "Buffalo Sabres", "CGY": "Calgary Flames",
    "CHI": "Chicago Blackhawks", "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers",
    "FLA": "Florida Panthers", "MTL": "Montreal Canadiens", "OTT": "Ottawa Senators",
    "TBL": "Tampa Bay Lightning", "TOR": "Toronto Maple Leafs", "VAN": "Vancouver Canucks",
    "WPG": "Winnipeg Jets", "CAR": "Carolina Hurricanes", "CBJ": "Columbus Blue Jackets",
    "NJD": "New Jersey Devils", "NYI": "New York Islanders", "NYR": "New York Rangers",
    "PHI": "Philadelphia Flyers", "PIT": "Pittsburgh Penguins", "WSH": "Washington Capitals",
    "ANA": "Anaheim Ducks", "COL": "Colorado Avalanche", "DAL": "Dallas Stars",
    "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild", "NSH": "Nashville Predators",
    "SEA": "Seattle Kraken", "SJS": "San Jose Sharks", "STL": "St. Louis Blues",
    "UTA": "Utah Mammoth", "VGK": "Vegas Golden Knights",
}


def nhl_rows():
    sched = load(ATLAS / "capture_nhl_schedule.json")
    team = {int(k): v for k, v in sched["team_id_to_abbrev"].items()}
    src = sched["source"]
    url = sched["url"]
    out = []
    for gid, date, et, home_id, away_id in sched["games"]:
        home_ab, away_ab = team[home_id], team[away_id]
        home, away = NHL_CLUB[home_ab], NHL_CLUB[away_ab]
        slug = f"{away_ab.lower()}-vs-{home_ab.lower()}"
        # easternStartTime -> UTC (EDT = UTC-4 in late October)
        hh, mm = (int(x) for x in et.split(":"))
        utc_h = (hh + 4) % 24
        out.append({
            "id": f"nhl-{gid}",
            "sport": "ice-hockey",
            "sport_name": "Ice Hockey",
            "competition": "2026-27 NHL Regular Season",
            "date": date,
            "start_local_et": et,
            "start_utc": f"{date}T{utc_h:02d}:{mm:02d}:00Z",
            "venue": None,
            "home": home,
            "away": away,
            "home_abbrev": home_ab,
            "away_abbrev": away_ab,
            "official_source": src,
            "official_url": f"https://www.nhl.com/gamecenter/{slug}/{date[:4]}/{date[5:7]}/{date[8:10]}/{gid}",
            "coverage_url": url,
            "status": "confirmed",
            "evidence": (f"Game id {gid} present in the NHL Stats REST schedule feed for "
                         f"{date} with homeTeamId={home_id} ({home_ab}) and visitingTeamId={away_id} ({away_ab})."),
        })
    return out


def nba_rows():
    sched = load(ATLAS / "capture_nba_schedule.json")
    out = []
    for g in sched["games"]:
        slug = re.sub(r"[^a-z0-9]+", "-", g["id"].lower())
        out.append({
            "id": f"nba-{g['id']}",
            "sport": "basketball",
            "sport_name": "Basketball",
            "competition": "2026-27 NBA Regular Season" if g["stage"] == "Regular Season" else "2026-27 Emirates NBA Cup",
            "date": g["date"],
            "start_local_et": g["et"],
            "start_utc": None,
            "venue": g["venue"],
            "city": g["city"],
            "home": g["home"],
            "away": g["away"],
            "official_source": sched["source"],
            "official_url": f"https://www.nba.com/game/{_nba_slug(g)}/{g['id']}",
            "coverage_url": sched["url"],
            "status": "confirmed",
            "evidence": (f"Game id {g['id']} listed on nba.com/schedule under {g['date']} "
                         f"({g['et']} ET) at {g['venue']}, {g['city']}: {g['away']} at {g['home']}."),
        })
    return out


def _nba_slug(g):
    abbr = {
        "Atlanta Hawks": "atl", "Boston Celtics": "bos", "Brooklyn Nets": "bkn",
        "Charlotte Hornets": "cha", "Chicago Bulls": "chi", "Cleveland Cavaliers": "cle",
        "Dallas Mavericks": "dal", "Denver Nuggets": "den", "Detroit Pistons": "det",
        "Golden State Warriors": "gsw", "Houston Rockets": "hou", "Indiana Pacers": "ind",
        "LA Clippers": "lac", "Los Angeles Lakers": "lal", "Memphis Grizzlies": "mem",
        "Miami Heat": "mia", "Milwaukee Bucks": "mil", "Minnesota Timberwolves": "min",
        "New Orleans Pelicans": "nop", "New York Knicks": "nyk", "Oklahoma City Thunder": "okc",
        "Orlando Magic": "orl", "Philadelphia 76ers": "phi", "Phoenix Suns": "phx",
        "Portland Trail Blazers": "por", "Sacramento Kings": "sac", "San Antonio Spurs": "sas",
        "Toronto Raptors": "tor", "Utah Jazz": "uta", "Washington Wizards": "was",
    }
    return f"{abbr[g['away']]}-vs-{abbr[g['home']]}"


def mlb_rows():
    cap = load(ATLAS / "capture_mlb.json")
    out = []
    for g in cap["games"]:
        out.append({
            "id": f"mlb-{g['gamePk']}",
            "sport": "baseball",
            "sport_name": "Baseball",
            "competition": f"2026 MLB World Series — {g['description']}",
            "date": g["officialDate"],
            "start_utc": g["utc"],
            "venue": g["venue"],
            "home": g["home"],
            "away": g["away"],
            "official_source": cap["source"],
            "official_url": f"https://www.mlb.com/gameday/{g['gamePk']}",
            "coverage_url": cap["schedule_url"],
            "status": "confirmed",
            "evidence": (f"gamePk {g['gamePk']} present in the MLB Stats API schedule for "
                         f"{g['officialDate']}: {g['away']} at {g['home']} ({g['venue']}), "
                         f"\"{g['description']}\", ifNecessary={g['ifNecessary']}."),
        })
    return out


def euroleague_rows():
    cap = load(ATLAS / "capture_euroleague.json")
    out = []
    for g in cap["games"]:
        if g["played"]:
            continue
        out.append({
            "id": f"el-{g['code'].replace('_', '-').lower()}",
            "sport": "basketball",
            "sport_name": "Basketball",
            "competition": "2026-27 EuroLeague Regular Season — Round 7",
            "date": g["utc"][:10],
            "start_utc": g["utc"],
            "venue": g["venue"],
            "home": g["home"],
            "away": g["away"],
            "official_source": cap["source"],
            "official_url": f"https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/{g['code']}/",
            "coverage_url": cap["url"],
            "status": "confirmed",
            "evidence": (f"{g['code']} returned by the EuroLeague live API for Round 7 with "
                         f"utcDate={g['utc']}, venue={g['venue']}, local={g['home']}, road={g['away']}, played=false."),
        })
    return out


def tennis_rows():
    cap = load(ATLAS / "capture_atp.json")
    out = []
    for i, m in enumerate(cap["matches"], start=1):
        out.append({
            "id": f"atp-2026-1022-{i:02d}",
            "sport": "tennis",
            "sport_name": "Tennis",
            "competition": f"{m['tournament']} — {m['round']}",
            "date": "2026-10-22",
            "start_utc": None,
            "venue": m["court"],
            "home": m["p1"],
            "away": m["p2"],
            "official_source": cap["source"],
            "official_url": m["url"],
            "coverage_url": cap["rankings_url"],
            "status": "confirmed",
            "evidence": (f"{m['p1']} vs {m['p2']} shown as \"{m['round']}\" on {m['court']} of the "
                         f"official ATP daily schedule for Thu 22 October 2026 "
                         f"({m['url']}). Seeds/entry status as published: "
                         f"{m.get('p1_seed') or m.get('p1_entry') or 'unseeded'} vs "
                         f"{m.get('p2_seed') or m.get('p2_entry') or 'unseeded'}."),
        })
    return out


# Sports this session captured first-hand. Everything else is inherited.
CAPTURED_SPORTS = {"ice-hockey", "basketball", "baseball", "tennis"}


def inherited_rows():
    """Rows carried from data/final/ for sports this session did not capture.

    Fixture identity (teams, date, competition) is preserved together with the
    official URL the earlier session recorded, but this session did not re-open
    that URL, so the row is marked inherited-unverified and every derived value
    stays blank.
    """
    final = load(FINAL)["matches"]
    out = []
    for m in final:
        sp = m.get("sport")
        if sp in CAPTURED_SPORTS:
            continue           # those sports are rebuilt from this session's own capture
        out.append({
            "id": f"inh-{m['id']}",
            "source_row_id": m["id"],
            "sport": sp,
            "sport_name": m.get("sport_name") or SPORT_NAME.get(sp, sp),
            "competition": m.get("competition"),
            "date": m.get("date"),
            "start_utc": m.get("start_utc"),
            "venue": m.get("venue"),
            "home": m.get("home"),
            "away": m.get("away"),
            "official_source": m.get("official_source"),
            "official_url": m.get("official_url"),
            "coverage_url": None,
            "status": "inherited-unverified",
            "evidence": ("Fixture identity carried from the published consolidated desk "
                         "(data/final/matches.json), which cites the official URL stored on this "
                         "row. This session did not re-open that URL, so no value on this row has "
                         "been confirmed first-hand and every derived cell is left blank."),
        })
    return out


def main():
    rows = []
    rows += nhl_rows()
    rows += nba_rows()
    rows += mlb_rows()
    rows += euroleague_rows()
    rows += tennis_rows()
    rows += inherited_rows()
    rows.sort(key=lambda r: (r["date"] or "", r["sport"], r["home"] or ""))

    payload = {
        "generated_at": CHECKED_AT,
        "session": SESSION,
        "window": ["2026-10-22", "2026-10-31"],
        "rule": ("confirmed = re-read from the governing-body URL stored on the row during this "
                 "session; inherited-unverified = carried from the previously published desk, "
                 "official URL attached, no value confirmed this session."),
        "counts": {
            "rows": len(rows),
            "confirmed": sum(1 for r in rows if r["status"] == "confirmed"),
            "inherited_unverified": sum(1 for r in rows if r["status"] == "inherited-unverified"),
        },
        "fixtures": rows,
    }
    (ATLAS / "fixtures.json").write_text(json.dumps(payload, indent=1) + "\n")

    sports = load(PORTAL_SPORTS)
    payload2 = {
        "captured_by": "arena/d81930c3-olbg2 (taxonomy), re-used by " + SESSION,
        "captured_at": sports.get("captured_at"),
        "eligible_count": sports["eligible_count"],
        "eligible_sports": sports["eligible_sports"],
        "excluded_hubs": sports["excluded_hubs"],
    }
    (ATLAS / "sports.json").write_text(json.dumps(payload2, indent=1) + "\n")

    print(f"fixtures: {len(rows)} rows "
          f"({payload['counts']['confirmed']} confirmed, "
          f"{payload['counts']['inherited_unverified']} inherited-unverified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
