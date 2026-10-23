#!/usr/bin/env python3
"""Transcribe the 2026-10-23 OLBG research snapshot into deterministic inputs.

No network access is used. Agent-read official extracts are copied from their dated
workspace captures; facts read later in this session are explicit records below.
The build/pricing stages consume data/olbg/source.json, not the other desks.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "olbg"
OUT.mkdir(parents=True, exist_ok=True)
CUTOFF = "2026-10-23T21:32:48Z"
FRESH_WINDOW = "2026-10-23 19:27–19:40 UTC"
INVENTORY_TIME = "2026-10-23T16:20:00Z"

SPORTS = [
    {"slug": "golf", "name": "Golf", "hub": "https://www.olbg.com/betting-tips/Golf/5"},
    {"slug": "volleyball", "name": "Volleyball", "hub": "https://www.olbg.com/betting-tips/Volleyball/21"},
    {"slug": "rugby-union", "name": "Rugby Union", "hub": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"slug": "cricket", "name": "Cricket", "hub": "https://www.olbg.com/betting-tips/Cricket/7"},
    {"slug": "snooker", "name": "Snooker", "hub": "https://www.olbg.com/betting-tips/Snooker/8"},
    {"slug": "darts", "name": "Darts", "hub": "https://www.olbg.com/betting-tips/Darts/15"},
    {"slug": "baseball", "name": "Baseball", "hub": "https://www.olbg.com/betting-tips/Baseball/12"},
    {"slug": "gaelic-sports", "name": "Gaelic Sports", "hub": "https://www.olbg.com/betting-tips/Gaelic_Football/25"},
    {"slug": "greyhounds", "name": "Greyhounds", "hub": "https://www.olbg.com/betting-tips/Greyhounds/28"},
    {"slug": "tennis", "name": "Tennis", "hub": "https://www.olbg.com/betting-tips/Tennis/3"},
    {"slug": "motor-racing", "name": "Motor Racing", "hub": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
    {"slug": "handball", "name": "Handball", "hub": "https://www.olbg.com/betting-tips/Handball/20"},
    {"slug": "ice-hockey", "name": "Ice Hockey", "hub": "https://www.olbg.com/betting-tips/Ice_Hockey/13"},
    {"slug": "basketball", "name": "Basketball", "hub": "https://www.olbg.com/betting-tips/Basketball/4"},
    {"slug": "rugby-league", "name": "Rugby League", "hub": "https://www.olbg.com/betting-tips/Rugby_League/10"},
]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def source(label: str, url: str, captured: str, note: str, kind: str = "official"):
    return {"label": label, "url": url, "captured": captured, "note": note, "kind": kind}


def event(**kw):
    base = {
        "start_utc": None,
        "display_time": "",
        "timezone_note": "",
        "venue": "",
        "provenance": "official_context",
        "olbg_url": None,
        "olbg_event_id": None,
        "olbg_state": None,
        "official_status": "Upcoming on the cited official source",
        "pricing": None,
        "blank_reason": "No sufficiently complete official inputs were captured for an independent price.",
        "high_detail": False,
        "market_note": "Handicap and total markets were investigated; no supportable price was originated.",
        "note": "",
        "prose": None,
        "facts": [],
        "review_scope": None,
        "reviewed_at": None,
        "cap_reason": None,
    }
    base.update(kw)
    if base["provenance"] == "official_context":
        base["olbg_url"] = None
        base["olbg_event_id"] = None
        base["olbg_state"] = None
    return base


def olbg_inventory_fields(inventory):
    by_id = {}
    for row in inventory["rows"]:
        by_id[str(row[-1])] = {
            "competition": row[0], "name": row[1], "displayed_time": row[2],
            "market": row[3], "popular_selection": row[4],
            "numerator": row[5], "denominator": row[6], "displayed_percent": row[7],
        }
    return by_id


inventory = load("data/olbgdesk/olbg_inventory.json")
inv = olbg_inventory_fields(inventory)
review = load("data/olbg/review.json")
assert review["audit_cutoff"] == CUTOFF
events = []
inputs = {}

# NBA: official schedule and 2025-26 venue splits. Only the explicitly read
# game previews and dated injury report support the two detailed write-ups.
nba_seed = load("data/monitor/seed.json")
nba_team_data = load("data/inputs/nba_teams.json")
inputs["nba"] = {
    "season": "2025-26 (completed; dated prior, not current-season form)",
    "captured": nba_team_data["meta"]["snapshot_utc"],
    "source": source("NBA official 2025-26 standings", nba_team_data["meta"]["source_url"], nba_team_data["meta"]["snapshot_utc"], "Overall and home/road records; prior-season inputs."),
    "teams": nba_team_data["teams"],
}
nba_codes = {
    "nba-0022600099": ("CHI", "MIL"), "nba-0022600008": ("NYK", "BOS"),
    "nba-0022600097": ("TOR", "WAS"), "nba-0022600094": ("ATL", "CHA"),
    "nba-0022600096": ("MIN", "ORL"), "nba-0022600095": ("DAL", "IND"),
    "nba-0022600098": ("DET", "MIA"), "nba-0022600009": ("HOU", "SAS"),
    "nba-0022600100": ("NOP", "UTA"), "nba-0022600101": ("MEM", "GSW"),
    "nba-0022600102": ("LAC", "LAL"), "nba-0022600103": ("POR", "SAC"),
}
nba_names = {
    "nba-0022600099": "Chicago Bulls @ Milwaukee Bucks",
    "nba-0022600008": "New York Knicks @ Boston Celtics",
    "nba-0022600097": "Toronto Raptors @ Washington Wizards",
    "nba-0022600094": "Atlanta Hawks @ Charlotte Hornets",
    "nba-0022600096": "Minnesota Timberwolves @ Orlando Magic",
    "nba-0022600095": "Dallas Mavericks @ Indiana Pacers",
    "nba-0022600098": "Detroit Pistons @ Miami Heat",
    "nba-0022600009": "Houston Rockets @ San Antonio Spurs",
    "nba-0022600100": "New Orleans Pelicans @ Utah Jazz",
    "nba-0022600101": "Memphis Grizzlies @ Golden State Warriors",
    "nba-0022600102": "LA Clippers @ Los Angeles Lakers",
    "nba-0022600103": "Portland Trail Blazers @ Sacramento Kings",
}
nba_direct = {"nba-0022600099", "nba-0022600008", "nba-0022600102"}
nba_observed = {
    "nba-0022600008": "Expired OLBG page: moneyline; Boston −2.5 / New York +2.5; total 221.5. A comment instead says 223.5 and is flagged, not used.",
    "nba-0022600102": "Expired OLBG page: moneyline; Lakers −8.5 / Clippers +8.5; total 225.5. A comment instead says −9.5 and is flagged, not used.",
}
for old in nba_seed["events"]:
    if old.get("sport") != "basketball":
        continue
    eid = old["id"]
    away, home = nba_codes[eid]
    event_id = str(old["olbg_url"].split("event_id=")[-1])
    listed = event_id in inv
    direct = eid in nba_direct
    provenance = "last_seen" if listed or direct else "official_context"
    official = [
        source("NBA game page and preview", old["official_url"], FRESH_WINDOW, "Official participants, ET clock, venue and game information."),
        source("NBA official schedule", "https://www.nba.com/games?date=2026-10-23", "2026-10-23T16:19:00Z", "Twelve-game Friday slate; both rendered chunks read."),
        source("NBA official 2025-26 standings", "https://www.nba.com/standings?Season=2025-26", nba_team_data["meta"]["snapshot_utc"], "Prior-season overall and venue-split records."),
        source("NBA official injury report — 3:15 PM ET", "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf", FRESH_WINDOW, "Availability only as of the report timestamp; no numerical injury adjustment."),
    ]
    observed = nba_observed.get(eid, (f"16:20 OLBG snapshot popular market: {inv[event_id]['market']} — {inv[event_id]['popular_selection']}. Tipster share is not a probability." if listed else "No individual OLBG event was observed in the 16:20 inventory."))
    events.append(event(
        id=eid, sport="basketball", competition="NBA 2026-27 regular season",
        name=nba_names[eid], date="2026-10-23", start_utc=old["start_utc"],
        display_time=old["display_time"], timezone_note="NBA publishes ET; UTC is a calendar conversion of that explicit zone.",
        venue="", provenance=provenance,
        olbg_url=old["olbg_url"] if provenance == "last_seen" else None,
        olbg_event_id=int(event_id) if provenance == "last_seen" else None,
        olbg_state="Expired at direct check" if direct else ("16:20 discovery snapshot" if listed else None),
        official_status="Scheduled on NBA official schedule at the research cutoff",
        official_sources=official,
        pricing={"method": "nba_split_log5", "away": away, "home": home},
        high_detail=eid in {"nba-0022600008", "nba-0022600102"},
        market_note=observed + " Spread and total prices remain blank because an official scoring distribution was not captured.",
        note="Price uses only completed 2025-26 road/home records. Current opener details and the dated injury report are context, not numerical adjustments.",
        prose=None,
    ))

# EuroLeague Round 8: official schedule and standings after Round 7.
el = load("data/signal/captures/basketball_euroleague.json")
inputs["euroleague"] = {"teams": {r["team"]: r for r in el["standings_after_round7"]}}
for r in el["fixtures_round8"]:
    events.append(event(
        id="euroleague-" + r["game_code"].replace("_", "-"), sport="basketball",
        competition="EuroLeague 2026-27 — Round 8", name=f"{r['away']} @ {r['home']}",
        date=r["date"], display_time=r["time_as_served"], timezone_note="Clock reproduced as served; no timezone was certified.",
        venue=r["venue"], official_status="Official Round 8 schedule; official context only, not an observed OLBG row",
        official_sources=[
            source("EuroLeague official Round 8 schedule", el["source_urls"]["schedule_round8"], el["captured_utc"], "Ten fixtures and venues."),
            source("EuroLeague official standings after Round 7", el["source_urls"]["standings_after_round7"], el["captured_utc"], "Games, wins, losses, points for and against for all 20 teams."),
        ],
        pricing={"method": "euroleague_log5", "away": r["away"], "home": r["home"]},
        market_note="No individual OLBG Round 8 offer was observed. Moneyline is originated; score and total projections are arithmetic analysis, not spread/total bets.",
        note="Only 6–7 current-season games per club; detailed official availability review was not captured, so high-confidence eligibility is off.",
    ))

# NHL: reconcile the existing card with hash-checked official team/schedule captures,
# then add every FUT game on the official 25 October schedule. Five games receive
# fresh detailed reviews; the daily cap remains a cap, not a reason to invent rows.
nhl = load("data/signal/captures/nhl_fixtures.json")
capture_manifest = load("data/olbg/captures/manifest.json")
capture_dir = OUT / "captures"
raw_nhl = {}
capture_by_key = {}
for item in capture_manifest["captures"]:
    blob = (capture_dir / item["path"]).read_bytes()
    assert len(blob) == item["bytes"], item["key"]
    assert hashlib.sha256(blob).hexdigest() == item["sha256"], item["key"]
    raw_nhl[item["key"]] = json.loads(blob)
    capture_by_key[item["key"]] = item


def nhl_key(name):
    """Use ASCII keys while retaining Montréal in every public display field."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")


def nhl_display(name):
    return name.replace("Montreal", "Montréal")


nhl_summary_url = "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2"
nhl_team_capture = capture_by_key["nhl_team_summary"]
nhl_team_rows = raw_nhl["nhl_team_summary"]["data"]
assert len(nhl_team_rows) == 32
inputs["nhl"] = {
    "captured": nhl_team_capture["fetched_at"],
    "source": source("NHL official team summary API", nhl_team_capture["url"], nhl_team_capture["fetched_at"], "Hash-checked 32-team capture; exact integer inputs used."),
    "teams": {
        nhl_key(r["teamFullName"]): {
            "team_id": r["teamId"], "gp": r["gamesPlayed"], "gf": r["goalsFor"], "ga": r["goalsAgainst"],
            "w": r["wins"], "l": r["losses"], "otl": r["otLosses"], "points": r["points"],
        } for r in nhl_team_rows
    },
}
nhl_team_ids = {r["teamId"]: nhl_key(r["teamFullName"]) for r in nhl_team_rows}
nhl_rows = []
for r in nhl["games"]:
    row = dict(r)
    row["schedule_url"] = nhl["source_urls"].get(r["date"], nhl["source_urls"]["2026-10-24"])
    row["schedule_captured"] = nhl["captured_utc"]
    row["neutral_site"] = False
    nhl_rows.append(row)
existing_nhl_ids = {r["id"] for r in nhl_rows}
schedule25 = capture_by_key["nhl_schedule_2026-10-25"]
new_nhl_rows = []
for day in raw_nhl["nhl_schedule_2026-10-25"]["gameWeek"]:
    if day["date"] != "2026-10-25":
        continue
    for g in day["games"]:
        if g["id"] in existing_nhl_ids:
            continue
        assert g["gameState"] == "FUT" and g["gameType"] == 2
        new_nhl_rows.append({
            "id": g["id"], "date": day["date"], "startUTC": g["startTimeUTC"],
            "away": nhl_team_ids[g["awayTeam"]["id"]], "home": nhl_team_ids[g["homeTeam"]["id"]],
            "venue": g["venue"]["default"], "state": g["gameState"],
            "gamecenter": "https://www.nhl.com" + g["gameCenterLink"],
            "schedule_url": schedule25["url"], "schedule_captured": schedule25["fetched_at"],
            "neutral_site": g["neutralSite"], "new_official_row": True,
        })
assert len(new_nhl_rows) == 5, [r["id"] for r in new_nhl_rows]
nhl_rows.extend(new_nhl_rows)
nhl_direct = {2026020166, 2026020167}
nhl_detailed = {2026020166, 2026020169, 2026020175, 2026020178, 2026020180}
for r in nhl_rows:
    direct = r["id"] in nhl_direct
    detailed = r["id"] in nhl_detailed
    away_key, home_key = nhl_key(r["away"]), nhl_key(r["home"])
    assert away_key in inputs["nhl"]["teams"] and home_key in inputs["nhl"]["teams"]
    display_name = f"{nhl_display(r['away'])} @ {nhl_display(r['home'])}"
    official = []
    if not r.get("new_official_row"):
        official.append(source("NHL official game centre", r["gamecenter"], nhl["captured_utc"], f"Game {r['id']}; FUT at capture."))
    official.extend([
        source("NHL official schedule", r["schedule_url"], r["schedule_captured"], "Official participants, UTC start, venue and FUT state in the hash-checked or dated capture."),
        source("NHL official team summary API", nhl_summary_url, nhl_team_capture["fetched_at"], "Games, goals, wins, losses, overtime losses and points; exact integer inputs used; capture SHA-256 checked."),
    ])
    if r.get("new_official_row"):
        official.append(source("NHL official 25 October score feed", "https://api-web.nhle.com/v1/score/2026-10-25", CUTOFF, "Fresh audit re-read: five FUT games on the official 25 October date; later UTC starts retain that official date."))
    if direct and not detailed:
        official.append(source("NHL official gamecenter landing feed", f"https://api-web.nhle.com/v1/gamecenter/{r['id']}/landing", FRESH_WINDOW, "Detailed matchup read retained from the prior review window."))
    if r["id"] == 2026020170:
        official.append(source("NHL Boston gamecenter landing feed — ranking review", "https://api-web.nhle.com/v1/gamecenter/2026020170/landing", CUTOFF, "Inspected during the fresh candidate review; sixth in-band estimate, retained below the five-game high-confidence daily card."))
    events.append(event(
        id=f"nhl-{r['id']}", sport="ice-hockey", competition="NHL 2026-27 regular season",
        name=display_name, date=r["date"], start_utc=r["startUTC"], display_time=r["startUTC"].replace("T", " ").replace(":00Z", " UTC"),
        timezone_note="UTC is published directly by the NHL API.", venue=r["venue"], neutral_site=r["neutral_site"],
        provenance="last_seen" if direct else "official_context",
        olbg_url=(f"https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/{'MTL_Canadiens_@_CHI_Blackhawks' if r['id']==2026020166 else 'TB_Lightning_@_COL_Avalanche'}/13?event_id={199984 if r['id']==2026020166 else 199985}" if direct else None),
        olbg_event_id=(199984 if r["id"] == 2026020166 else 199985) if direct else None,
        olbg_state="Expired at direct check" if direct else None,
        official_status="FUT on official NHL schedule at the research cutoff" + ("; neutral-site game" if r["neutral_site"] else ""),
        official_sources=official,
        pricing={"method": "nhl_points_log5", "away": away_key, "home": home_key, "derive_markets": direct},
        high_detail=detailed,
        market_note=("Expired OLBG page exposes moneyline, puck line 1.5 and total 6.5. Those two extra markets are originated with a disclosed independent-Poisson regulation calculation and a one-goal tie resolution." if direct else "No individual OLBG puck-line or total offer was observed; only the two-way moneyline is originated."),
        note=("Fresh detailed official matchup review is attached below. The early-season sample and absence of a game-specific availability bulletin remain explicit limitations." if detailed else "Early-season sample. This row did not receive one of the five fresh detailed NHL reviews, so arithmetic alone cannot promote it to high confidence."),
        cap_reason=("Boston’s estimate is the sixth in-band NHL candidate, behind the five promoted detailed reviews. The official preview was inspected, but this row remains medium so the daily card contains the five highest estimated in-band selections." if r["id"] == 2026020170 else None),
    ))

# MLB World Series schedule and regular-season records.
mlb = load("data/signal/captures/mlb.json")
inputs["mlb"] = mlb["regular_season_2026"]
for r in mlb["games"]:
    first = r["gamePk"] == 849805
    events.append(event(
        id=f"mlb-{r['gamePk']}", sport="baseball", competition="MLB World Series 2026",
        name=f"{r['away']} @ {r['home']} — {r['description']}", date=r["date"], start_utc=r["startUTC"],
        display_time=r["startUTC"].replace("T", " ").replace(":00Z", " UTC"), timezone_note="UTC is published directly by the MLB Stats API.",
        venue=r["venue"], provenance="last_seen" if first else "official_context",
        olbg_url="https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789" if first else None,
        olbg_event_id=160789 if first else None, olbg_state="Expired at direct check" if first else None,
        official_status=("Scheduled; if necessary" if r["ifNecessary"] == "Y" else "Scheduled on official MLB API"),
        official_sources=[
            source("MLB official schedule API", mlb["source_urls"]["schedule"], mlb["captured_utc"], "Five World Series entries, UTC starts, venues and scheduling status."),
            source("MLB official 2026 standings API", mlb["source_urls"]["standings_al"], mlb["captured_utc"], "Rays 98–64, 736 runs for and 650 against; Brewers 103–59, 832 for and 618 against in the paired league feeds."),
        ] + ([source("MLB official Game 1 live feed", "https://statsapi.mlb.com/api/v1.1/game/849805/feed/live", FRESH_WINDOW, "Preview/Scheduled at 2026-10-24T00:00:00Z. Probable-pitcher values were not promoted without explicit extraction.")] if first else []),
        pricing={"method": "mlb_log5", "away": r["away"], "home": r["home"]},
        high_detail=first,
        market_note=("Expired OLBG Game 1 page exposes moneyline, run line ±1.5 and total 6.5. Run line and total stay blank because probable pitchers and a complete extra-inning run distribution were not captured." if first else "Only the match winner is originated from season records. No individual OLBG offer was observed for this game."),
        note="Overall 162-game records only; no home/away, starter or bullpen adjustment. Game 5 remains conditional on the official schedule.",
    ))

# PDC European Championship last 16, freshly corroborated on the official hub.
pdc_hub = "https://www.pdc.tv/tournament-hub/10870"
pdc_rankings = "https://www.pdc.tv/rankings"
inputs["pdc_rankings"] = {"Gian van Veen": 1045750, "Gerwyn Price": 787000, "Stephen Bunting": 576250, "Ross Smith": 572250, "Luke Woodhouse": 514000, "Damon Heta": 418750, "Cameron Menzies": 378500, "Kim Huybrechts": 152000}
pdc_rows = [
    ("32383", "Cameron Menzies", "Gerwyn Price", "07:15", "Menzies beat Zonneveld 6–3; Price beat Cross 6–2."),
    ("32384", "Stephen Bunting", "Kim Huybrechts", "08:15", "Bunting beat Noppert 6–5; Huybrechts beat Searle 6–1."),
    ("32385", "Gian van Veen", "Luke Woodhouse", "10:15", "Van Veen beat Gilding 6–4; Woodhouse beat Van Duijvenbode 6–3."),
    ("32386", "Ross Smith", "Damon Heta", "09:15", "Smith beat Sedlacek 6–4; Heta beat Wade 6–5."),
]
darts_capture = load("data/signal/captures/darts_olbg.json")
darts_urls = {str(r["olbg_event_id"]): r["url"] for r in darts_capture["matches"]}
for oid, p1, p2, clock, recent in pdc_rows:
    events.append(event(
        id=f"pdc-{oid}", sport="darts", competition="PDC European Championship — Last 16",
        name=f"{p1} v {p2}", date="2026-10-24", display_time=clock,
        timezone_note="PDC hub clock has no certified timezone; the OLBG snapshot instead showed 13:15 for all four, which is flagged.",
        provenance="last_seen", olbg_url=darts_urls[oid], olbg_event_id=int(oid), olbg_state="Expired at direct check",
        official_status="Confirmed last-16 pairing on official PDC tournament hub; upcoming there while expired on OLBG",
        official_sources=[
            source("PDC official tournament hub", pdc_hub, FRESH_WINDOW, f"Last-16 pairing and displayed {clock} clock. {recent}"),
            source("PDC official world rankings", pdc_rankings, FRESH_WINDOW, "Current world-ranking prize money for both players; distinct from European Tour rankings."),
        ],
        pricing={"method": "ranking_share", "input": "pdc_rankings", "p1": p1, "p2": p2},
        market_note="Expired OLBG pages expose match winner, leg handicap and totals. Only match winner is priced: no official leg-distribution input was captured.",
        note=recent + " Ranking-value share is an uncalibrated two-way estimate and is capped below high.",
    ))

# ATP Basel and Vienna qualifying on 24 October, from the official daily OP PDFs.
inputs["atp_rankings"] = {
    "Baez": 1044, "Tirante": 1032, "J.M. Cerundolo": 1000, "Vallejo": 997,
    "Faria": 941, "Kecmanovic": 930, "Hanfmann": 923, "Marozsan": 860,
    "Altmaier": 849, "Kopriva": 844, "Droguet": 801, "Machac": 779,
    "Duckworth": 774, "Carreno Busta": 773, "Medjedovic": 764, "Svajda": 759,
    "Mannarino": 743, "Molcan": 734, "Kovacevic": 715, "Hijikata": 689,
    "Fearnley": 686, "Giron": 676, "Sonego": 658,
}
atp_rank_url = "https://www.atptour.com/en/rankings/singles?rankRange=0-100"
atp_events = [
    ("basel", "Giron", "Hanfmann"), ("basel", "Faria", "Brunold"),
    ("basel", "Bernet", "Altmaier"), ("basel", "Kecmanovic", "Hijikata"),
    ("basel", "J.M. Cerundolo", "Svajda"), ("basel", "Baez", "Mpetshi Perricard"),
    ("basel", "Kovacevic", "Duckworth"), ("vienna", "Kopriva", "Neumayer"),
    ("vienna", "Schwaerzler", "Droguet"), ("vienna", "Marozsan", "Sorger"),
    ("vienna", "Tirante", "Mannarino"), ("vienna", "Fearnley", "Carreno Busta"),
    ("vienna", "Vallejo", "Sonego"), ("vienna", "Molcan", "Medjedovic"),
    ("vienna", "Moutet", "Machac"),
]
for tournament, p1, p2 in atp_events:
    number = "328" if tournament == "basel" else "337"
    op = f"https://www.protennislive.com/posting/2026/{number}/op.pdf"
    ranking_inputs = inputs["atp_rankings"]
    blank = None if p1 in ranking_inputs and p2 in ranking_inputs else "At least one player’s official singles ranking points were not captured; no price is filled from a name, wildcard or secondary ranking."
    events.append(event(
        id=f"atp-{tournament}-{p1.lower().replace(' ', '-').replace('.', '')}-{p2.lower().replace(' ', '-').replace('.', '')}",
        sport="tennis", competition=f"ATP {tournament.title()} 2026 — qualifying",
        name=f"{p1} v {p2}", date="2026-10-24", display_time="",
        timezone_note="Official order of play confirms the date and match list; no per-match clock is transcribed here.",
        official_status="Named on the official 24 October qualifying order of play; official context only",
        official_sources=[
            source(f"ATP {tournament.title()} official order of play PDF", op, FRESH_WINDOW, "24 October 2026 qualifying match list. The separate incomplete Bertola–Player Competing row is excluded and flagged."),
            source("ATP official singles rankings — 19 October", atp_rank_url, FRESH_WINDOW, "Ranking points used only where both exact player values were captured."),
        ],
        pricing={"method": "ranking_share", "input": "atp_rankings", "p1": p1, "p2": p2},
        blank_reason=blank or "No sufficiently complete official inputs were captured for an independent price.",
        market_note="These qualifiers were not individually observed on OLBG. Match winner is priced only where both rankings are present; set/game handicaps and totals remain blank.",
        note="Ranking-value share does not incorporate surface, draw format or availability and is capped below high.",
    ))

# Cricket Australia official match centres and ICC men's ODI ratings.
ca = load("data/signal/captures/cricket_ca.json")
inputs["icc_odi"] = {"Pakistan": 103, "England": 93}
cricket_meta = {
    "Tasmanian Tigers v Victoria": (188839, "direct"),
    "New Zealand v India": (188832, "direct"),
    "Western Australia v New South Wales": (188840, "inventory"),
    "Pakistan v England": (188838, "inventory"),
}
for r in ca["upcoming"]:
    if r["teams"] not in cricket_meta:
        continue
    oid, state = cricket_meta[r["teams"]]
    pricing = None
    blank = "No compatible official team rating was captured for this fixture/format; no price is inferred."
    if r["teams"] == "Pakistan v England":
        pricing = {"method": "ranking_share", "input": "icc_odi", "p1": "Pakistan", "p2": "England"}
        blank = ""
    official = [source("Cricket Australia official match centre", r["url"], FRESH_WINDOW, f"Upcoming; {r['series']}; {r['venue']}. Clock labels say ‘your time’, so no UTC conversion is published.")]
    if pricing:
        official.append(source("ICC official men’s ODI team rankings", "https://www.icc-cricket.com/rankings/mens/team-rankings/odi", FRESH_WINDOW, "Ratings dated 23 October: Pakistan 103, England 93. ODI ratings are not substituted for T20I ratings."))
    events.append(event(
        id=f"cricket-{oid}", sport="cricket", competition=r["series"] + (f" — {r['stage']}" if r.get("stage") else ""),
        name=r["teams"], date=r["date"], display_time="", timezone_note="Only the calendar date is published; the match centre’s ‘your time’ clock cannot be certified as UTC.",
        venue=r["venue"], provenance="last_seen", olbg_url=f"https://www.olbg.com/betting-tips/Cricket/7", olbg_event_id=oid,
        olbg_state="Expired at direct check" if state == "direct" else "16:20 discovery snapshot",
        official_status="Upcoming on Cricket Australia match centre", official_sources=official,
        pricing=pricing, blank_reason=blank,
        market_note="Match winner is priced only for Pakistan–England from same-format ODI ratings. Domestic, T20I, totals and player markets remain blank without compatible inputs.",
        note="The separately captured India Women–Zimbabwe Women second ODI is excluded because its date was not cleanly confirmed; the first-ODI result is not used as a price.",
    ))

# URC Bulls–Ulster: official fixture and Round 3 context, but no 1X2 distribution.
events.append(event(
    id="urc-bulls-ulster-2026-10-24", sport="rugby-union", competition="United Rugby Championship 2026-27 — Round 4",
    name="Bulls v Ulster", date="2026-10-24", display_time="07:45", timezone_note="URC page displays a local clock without a certified timezone; no UTC conversion.",
    venue="Loftus Versfeld", provenance="last_seen", olbg_url="https://www.olbg.com/betting-tips/Rugby_Union/9", olbg_event_id=609576,
    olbg_state="16:20 discovery snapshot", official_status="Saturday fixture on official URC match centre",
    official_sources=[source("URC official match centre", "https://stats.unitedrugby.com/match-centre/2026-27/4", FRESH_WINDOW, "Bulls–Ulster on Saturday at displayed 07:45, Loftus Versfeld. Round 3 context: Bulls 2-0-1, 126/54 PF/PA; Ulster 0-2-1, 88/93.")],
    blank_reason="The official page supports the fixture and three-match context but not a draw-inclusive win distribution; no 1X2 price is invented.",
    market_note="OLBG’s To Win market was reviewed. Match winner, handicap and total all remain blank because the draw and scoring distributions are unsupported.",
    note="Official context only three matches into the season; no injury or availability claim added.",
))

# WST: fully named future fixtures only; undetermined finalists/wildcards are excluded.
wst = load("data/signal/captures/snooker_wst.json")
wst_rank = load("data/signal/captures/snooker_rankings_full.json")
for r in wst["matches"]:
    if r["date"] <= "2026-10-23" or "Winner of" in r["p1"] or "Winner of" in r["p2"] or "Wildcard" in r["p2"]:
        continue
    events.append(event(
        id="wst-" + r["match_centre"].rstrip("/").split("/")[-1], sport="snooker",
        competition=r["event"] + " — " + r["round"], name=f"{r['p1']} v {r['p2']}", date=r["date"],
        display_time=r["time_local"], timezone_note="WST clock reproduced without a certified timezone.",
        official_status="Scheduled with both players named on WST match centre; official context only",
        official_sources=[
            source("WST official match centre", r["match_centre"], wst["captured_utc"], f"{r['round']}; {r['status_at_capture']}."),
            source("WST official world rankings", wst_rank["source_url"], wst_rank["captured_utc"], "Captured table ends at 36th place, Jackson Page £198,500. No missing value is treated as exact."),
        ],
        blank_reason="At least one player lacks an exact captured WST ranking value; using the top-36 cutoff as an exact rating would be an inferred value, so the price is blank.",
        market_note="Match winner, frame handicap and frame total are not priced without two exact player inputs and confirmed format/distribution evidence.",
    ))

# Formula 1 race and championship outright context.
f1 = load("data/signal/captures/motor_racing_f1.json")
for oid, name, date, clock, blank in [
    (913, "United States Grand Prix 2026 — race", "2026-10-25", "16:00", "Qualifying had not supplied a final grid and a complete official field-performance distribution was not captured; no race-winner probability is invented."),
]:
    events.append(event(
        id=f"f1-{oid}", sport="motor-racing", competition="Formula 1", name=name, date=date, display_time=clock,
        timezone_note="Clock reproduced as displayed; timezone not certified.", provenance="last_seen",
        olbg_url=("https://www.olbg.com/betting-tips/Motor_Racing/All_Motor_Racing/All_Events/USA_Grand_Prix/14?event_id=913" if oid == 913 else "https://www.olbg.com/betting-tips/Motor_Racing/14"),
        olbg_event_id=oid, olbg_state="Expired at direct check" if oid == 913 else "16:20 discovery snapshot",
        official_status="Official F1 calendar/standings context; race weekend in progress" if oid == 913 else "Official F1 standings and remaining-calendar context",
        official_sources=[
            source("Formula 1 official United States event page", "https://www.formula1.com/en/racing/2026/united-states", FRESH_WINDOW, "Practice 3 and qualifying Saturday; race Sunday 25 October at displayed 16:00."),
            source("Formula 1 official drivers’ standings", f1["source_urls"]["standings"], FRESH_WINDOW, "Antonelli 340, Russell 238, Hamilton 229, Verstappen 221, Leclerc 215, Norris 201, Piastri 138, Hadjar 97; full table read but no outcome distribution inferred."),
        ],
        blank_reason=blank,
        market_note="OLBG lists win race and editorially describes fastest lap, podium and points markets. No full-field price is published without a supported distribution.",
    ))

# EHF official 24 October calendar. No unsupported three-way prices.
ehf = load("data/signal/captures/handball_ehf.json")
for r in ehf["matches"]:
    if r["date"] != "2026-10-24":
        continue
    events.append(event(
        id="ehf-" + r["url"].split("/matches/")[-1].split("/")[0], sport="handball", competition=r["competition"],
        name=f"{r['home']} v {r['away']}", date=r["date"], display_time=r.get("time_local", ""),
        timezone_note="EHF clock reproduced as displayed; timezone not certified.", official_status="Scheduled on official EHF match centre; official context only",
        official_sources=[source("EHF official match centre", r["url"], FRESH_WINDOW, r["status"] + "; 24 October calendar corroborated in the detailed review window.")],
        blank_reason="No compatible club rating and draw-inclusive scoring distribution were captured; the match-winner price remains blank.",
        market_note="Money line, handicap and totals were investigated. No price is originated from a single first-leg score or an incomplete three-way input set.",
        note=("First-leg context: Kur 26–38 MRK Sloga Doboj. That result is not treated as a second-leg probability." if r["home"] == "MRK Sloga Doboj" else ""),
    ))

# NRL Rugby League World Cup official context, with one-match samples disclosed.
nrl = load("data/signal/captures/rugby_league_rlwc.json")
for r in nrl["round2"]:
    if r["status"] != "Upcoming":
        continue
    events.append(event(
        id="nrl-" + r["url"].rstrip("/").split("/")[-1], sport="rugby-league", competition="Rugby League World Cup 2026 — Round 2",
        name=f"{r['home']} v {r['away']}", date=r["date"], display_time=r["time_et"],
        timezone_note="Clock is shown as served in the dated capture; the viewer-zone interpretation is not certified here, so kickoff_utc is deliberately blank.",
        venue=r["venue"], official_status="Upcoming on official NRL draw; not individually observed in the OLBG inventory",
        official_sources=[source("NRL official World Cup match page", r["url"], nrl["captured_utc"], "Upcoming fixture and venue; earlier Round 1 results are context only.")],
        blank_reason="Only one recent official match per team was captured, with no ratings or availability table; no independent price is manufactured from that sample.",
        market_note="Match winner, handicap and totals remain blank. These are official-context fixtures, not asserted OLBG offers.",
    ))

# Manual findings: source-linked, specific, and separate from automatic blank rows.
# Attach fact-level evidence to each freshly reviewed high-confidence candidate.
# A fact can only cite an official HTTPS URL registered on the same event.
reviewed_event_ids = set()
for e in events:
    detail = review["event_reviews"].get(e["id"])
    if not detail:
        continue
    reviewed_event_ids.add(e["id"])
    e["prose"] = detail["prose"]
    e["facts"] = detail["facts"]
    e["review_scope"] = detail["review_scope"]
    e["reviewed_at"] = CUTOFF
    assert e["high_detail"], e["id"]
    assert {f["kind"] for f in e["facts"]} >= {"team_form", "availability"}, e["id"]
    assert any(f["kind"] in {"recent_form", "recent_history"} for f in e["facts"]), e["id"]
    assert any(f["kind"] in {"player", "goalie"} for f in e["facts"]), e["id"]
    registered = {s["url"] for s in e["official_sources"]}
    for fact in e["facts"]:
        url = fact["source_url"]
        assert url.startswith("https://"), (e["id"], url)
        if url not in registered:
            label = "NHL official gamecenter landing feed — fresh detail review" if "nhle.com" in url else "Official detail review"
            e["official_sources"].append(source(label, url, CUTOFF, "Freshly inspected evidence attached to the prediction facts."))
            registered.add(url)
    assert all(f["source_url"] in registered for f in e["facts"])
assert reviewed_event_ids == set(review["event_reviews"]), reviewed_event_ids ^ set(review["event_reviews"])

flags = [
    {"id": "OLBG-ACTIVE-01", "severity": "review", "title": "No active tips were visible on the checked OLBG hubs", "detail": "All 16 main hub renders checked in this session showed no active tip set, and league-specific NHL/NBA/MLB/EuroLeague/cricket/ATP pages said ‘No tips found.’ This is a checked-page result, not proof that every OLBG market is empty. Zero rows are labelled active.", "links": [source("OLBG tips index", "https://www.olbg.com/betting-tips", FRESH_WINDOW, "Checked hub family.", "olbg")]},
    {"id": "OLBG-EXPIRED-02", "severity": "review", "title": "Expired OLBG pages can still describe officially upcoming events", "detail": "Direct event pages for Boston–New York, Lakers–Clippers, Montréal–Chicago, Tampa Bay–Colorado, Rays–Brewers, the US Grand Prix and four PDC matches showed Expired while official schedules still listed the events ahead. Both states are preserved; no Expired page is called an active offer.", "links": [source("Expired OLBG Celtics event", "https://www.olbg.com/betting-tips/Basketball/NBA/NBA/NY_Knicks_@_BOS_Celtics/4?event_id=534842", FRESH_WINDOW, "Expired.", "olbg"), source("NBA official Celtics game page", "https://www.nba.com/game/nyk-vs-bos-0022600008", FRESH_WINDOW, "Friday 7:00 PM ET.")]},
    {"id": "OLBG-NBA-03", "severity": "irregularity", "title": "Celtics total differs between the OLBG selection and comment", "detail": "The expired page displays Under/Over 221.5 while a comment beside the selection quotes 223.5. Neither is used as an official statistic or an originated line.", "links": [source("OLBG Celtics event — inspect total", "https://www.olbg.com/betting-tips/Basketball/NBA/NBA/NY_Knicks_@_BOS_Celtics/4?event_id=534842", FRESH_WINDOW, "221.5 selection versus 223.5 comment.", "olbg")]},
    {"id": "OLBG-NBA-04", "severity": "irregularity", "title": "Lakers spread differs between the OLBG selection and comment", "detail": "The expired page displays Lakers −8.5 / Clippers +8.5 while the quoted comment says −9.5. The comment is not evidence for the originated price.", "links": [source("OLBG Lakers event — inspect spread", "https://www.olbg.com/betting-tips/Basketball/NBA/NBA/LA_Clippers_@_LA_Lakers/4?event_id=536042", FRESH_WINDOW, "8.5 selection versus 9.5 comment.", "olbg")]},
    {"id": "OLBG-F1-05", "severity": "irregularity", "title": "Malformed OLBG tip-count rendering on the Formula 1 page", "detail": "The expired US Grand Prix render concatenates counts into strings such as ‘14 / 014644…’. Those fields are not parsed as meaningful totals, and tipster shares are never used as probabilities.", "links": [source("OLBG US Grand Prix event", "https://www.olbg.com/betting-tips/Motor_Racing/All_Motor_Racing/All_Events/USA_Grand_Prix/14?event_id=913", FRESH_WINDOW, "Malformed count rendering.", "olbg")]},
    {"id": "NBA-INJ-06", "severity": "limitation", "title": "NBA availability is timestamped and one rendered Lakers row is garbled", "detail": "The official injury report is valid only as of 3:15 PM ET on 23 October. Clearly parsed Celtics and Clippers absences are quoted in prose; the malformed Lakers row is not interpreted. Later updates can change availability.", "links": [source("NBA official injury report", "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf", FRESH_WINDOW, "10/23/26 03:15 PM.")]},
    {"id": "NHL-INJ-07", "severity": "limitation", "title": "No game-specific official NHL availability bulletin was captured", "detail": "The five freshly reviewed official gamecentre previews support fixtures, records, last-five skater leaders and goaltending statistics but did not supply a dated game-specific availability report in the inspected content. No NHL injury claim or injury adjustment is made; this limitation remains attached to all five high-confidence NHL rows.", "links": [source(f"NHL game {gid} landing feed", f"https://api-web.nhle.com/v1/gamecenter/{gid}/landing", CUTOFF, "Fresh detailed matchup read; no availability bulletin promoted.") for gid in sorted(nhl_detailed)]},
    {"id": "PDC-TIME-08", "severity": "irregularity", "title": "PDC and OLBG darts clocks do not agree", "detail": "The official PDC hub displays staggered 07:15, 08:15, 09:15 and 10:15 clocks, while the 16:20 OLBG inventory showed 13:15 for all four. Neither zone is silently inferred; official pairings and ranking inputs remain usable.", "links": [source("PDC official tournament hub", pdc_hub, FRESH_WINDOW, "Staggered last-16 clocks.")]},
    {"id": "ATP-RANK-09", "severity": "limitation", "title": "Incomplete ATP ranking fields stay blank", "detail": "Seven of the 15 named qualifiers lack an exact captured ranking value for at least one participant. The Bertola–‘Player Competing’ row is incomplete and excluded. No wildcard ranking or secondary-site figure is substituted.", "links": [source("ATP Basel official order of play", "https://www.protennislive.com/posting/2026/328/op.pdf", FRESH_WINDOW, "Qualifying list."), source("ATP official rankings", atp_rank_url, FRESH_WINDOW, "19 October rankings.")]},
    {"id": "CRICKET-TZ-10", "severity": "limitation", "title": "Cricket clocks and one women’s fixture date are not promoted", "detail": "Cricket Australia labels clocks ‘your time’; only calendar dates are published. The India Women–Zimbabwe Women second ODI is excluded because its captured date was not clean. ICC women’s ODI ratings rendered empty, and men’s ODI ratings are not used for T20Is.", "links": [source("Cricket Australia upcoming list", ca["source_url"], ca["captured_utc"], ca["timezone_note"])]},
    {"id": "GAA-CONFLICT-11", "severity": "irregularity", "title": "GAA Ireland–Scotland status conflicts between captures", "detail": "A dated capture listed Ireland–Scotland as a future 24 October final, but the fresher official fixtures-results render placed it under Previous results with ambiguous Final text. It is not presented as certainly upcoming and no selection is published.", "links": [source("GAA official fixtures and results", "https://www.gaa.ie/fixtures-results", FRESH_WINDOW, "Fresh placement under Previous results."), source("GAA match page", "https://www.gaa.ie/hurling/shinty-hurling-international/ireland-scotland/9abfb6e4-6223-44b7-8d25-57510681e49e", "2026-10-23T16:45:00Z", "Earlier future-listing capture.")]},
    {"id": "VOLLEYBALL-12", "severity": "limitation", "title": "No readable official forward volleyball card", "detail": "The checked Volleyball World schedule returned Page Not Found, PlusLiga redirected to a different league, and CEV exposed news rather than a usable forward list. Volleyball therefore has zero published matches and zero selections rather than an inferred schedule.", "links": [source("CEV official site", "https://www.cev.eu/", "2026-10-23T17:20:00Z", "Official context and access limitation.")]},
    {"id": "GREYHOUNDS-13", "severity": "limitation", "title": "GBGB open-race data lacks runners, traps and race times", "detail": "Track, distance, category and grade alone cannot identify a betting field. The GBGB homepage showed results rather than a readable future card, so no greyhound race or selection is published.", "links": [source("GBGB official open-race calendar", "https://www.gbgb.org.uk/racing/open-races/", "2026-10-23T17:20:00Z", "No runner-level card in served HTML.")]},
    {"id": "GOLF-14", "severity": "limitation", "title": "Golf tournament is in progress, not an upcoming match", "detail": "The checked PGA Tour schedule showed the Butterfield Bermuda Championship in Round 2, while the dated DP World Tour capture had completed two rounds. In-progress leaderboards are not converted into upcoming match prices; golf has zero upcoming rows in this snapshot.", "links": [source("PGA Tour official schedule", "https://www.pgatour.com/schedule", FRESH_WINDOW, "R2 In Progress at check."), source("DP World Tour official leaderboard", "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/leaderboard", "2026-10-23T17:10:00Z", "Post-round-two context.")]},
    {"id": "MLB-MARKETS-15", "severity": "limitation", "title": "MLB run line and total are not priced without explicit pitching inputs", "detail": "The expired Game 1 page exposes run line ±1.5 and total 6.5, but probable pitchers were not explicitly extracted and extra innings complicate a regulation-only calculation. Only match winner from official season records is published.", "links": [source("MLB official Game 1 feed", "https://statsapi.mlb.com/api/v1.1/game/849805/feed/live", FRESH_WINDOW, "Preview/Scheduled; no probable-pitcher claim promoted."), source("Expired OLBG Game 1 page", "https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789", FRESH_WINDOW, "Market inventory only.", "olbg")]},
    {"id": "REPO-16", "severity": "repository", "title": "Historical repository contains conflict-marker text and overlapping desks", "detail": "Review found leftover conflict-marker lines in COORDINATION.md and METHODOLOGY.md plus many overlapping dashboards with different dates and counts. Shared historical content is preserved; this desk has a separate /olbg/ namespace and does not add counts across layers.", "links": [source("Repository methodology at main", "https://github.com/buffedlizard55-lab/OLBG2/blob/main/METHODOLOGY.md#L125", CUTOFF, "Manual repository review link.", "repository"), source("Repository coordination ledger at main", "https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md", CUTOFF, "Append-only shared ledger; marker text retained for owner review.", "repository")]},
    {"id": "PRICE-17", "severity": "limitation", "title": "No current bookmaker odds were captured", "detail": "All odds on this desk are originated fair American prices derived from the displayed estimate, not bookmaker offers. A selection is not a claim that a current wager is available at that price.", "links": [source("Expired OLBG moneyline example", "https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/MTL_Canadiens_@_CHI_Blackhawks/13?event_id=199984", FRESH_WINDOW, "Expired; no current quote used.", "olbg")]},
]

flags.append({
    "id": "NBA-ROAD-COLUMN-18", "severity": "irregularity",
    "title": "NBA home/road columns were explicitly reconciled",
    "detail": "A manual review note briefly conflated the Clippers’ home and away splits. A direct re-read of the official standings resolved it before publication: HOME is 23–18 and ROAD is 19–22. The canonical pricing input remains 19–22 away; no probability change was hidden.",
    "links": [source("NBA official 2025-26 standings", "https://www.nba.com/standings?Season=2025-26", CUTOFF, "Complete standings table re-read; Clippers HOME 23–18, ROAD 19–22.")],
})

# Per-sport narrative shown even when the event table is empty.
category_notes = {
    "golf": "No upcoming golf rows: the checked events were already in progress and a complete forward field was not captured. See GOLF-14.",
    "volleyball": "No supportable forward volleyball card was readable from official sources. The 16:20 OLBG inventory is discovery evidence only, not enough to publish fixture facts. See VOLLEYBALL-12.",
    "gaelic-sports": "No upcoming Gaelic Sports row is promoted because the official Ireland–Scotland status conflicts between captures. Gaelic Football and Hurling are intentionally one requested category. See GAA-CONFLICT-11.",
    "greyhounds": "No runner-level future card was available from GBGB, so no race names, traps or selections are invented. See GREYHOUNDS-13.",
}

payload = {
    "schema_version": 1,
    "research_cutoff": CUTOFF,
    "fresh_read_window": FRESH_WINDOW,
    "latest_access_audit": CUTOFF,
    "inventory_captured": INVENTORY_TIME,
    "sports": SPORTS,
    "events": events,
    "inputs": inputs,
    "flags": flags,
    "category_notes": category_notes,
    "review": review,
    "capture_manifest": capture_manifest,
    "discovery": [
        {"sport": c["sport"], "url": c["url"], "checked": CUTOFF,
         "result": c["observed_text"] + ". Inspected hub render only; not a global empty-market claim."}
        for c in review["olbg_checks"]
    ],
}
(OUT / "source.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
shutil.copyfile(ROOT / "data" / "olbgdesk" / "olbg_inventory.json", OUT / "olbg_inventory_2026-10-23.json")
print(f"Wrote {len(events)} events across {len({e['sport'] for e in events})} sports; {len(flags)} manual flags; cutoff {CUTOFF}")
