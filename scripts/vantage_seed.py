#!/usr/bin/env python3
"""Rebuild Vantage's dated, conservative evidence ledger.

The OLBG first-page extract is copied with a SHA-256 pointer to the original merged
session's capture; we checked the fifteen hubs again in this session, but did *not*
claim a complete second line-by-line scrape.  Official fixture facts below were
read first-hand from the URLs recorded on each record on 24 October 2026.
This is an offline, repeatable snapshot, NOT a live collector or a bookmaker feed.
"""
from __future__ import annotations

import json
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vantage"
CAPTURE = DATA / "captures" / "olbg_first_page.json"
HURLING_CAPTURE = DATA / "captures" / "olbg_hurling_first_page.json"
STAMP = "2026-10-24T17:50:00Z"  # Freeze the first-hand 24 Oct research window, never runtime now().
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]

SCORE = "https://api-web.nhle.com/v1/score/2026-10-24"
SUMMARY = "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2"
STAND = "https://api-web.nhle.com/v1/standings/2026-10-24"
BOS_RECENT = "https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154"
SJS_RECENT = "https://www.nhl.com/gamecenter/sjs-vs-ott/2026/10/22/2026020156"
MLB_SCHEDULE = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-31&hydrate=team,linescore,probablePitcher,decisions"
MLB_STAND = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason"
MLB_PITCHERS = "https://statsapi.mlb.com/api/v1/people?personIds=656876,701656,688107,642547&hydrate=stats(group=%5Bpitching%5D,type=%5Bseason%5D,season=2026)"
NBA_INJURY = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_00PM.pdf"
NBA_TABLE = "https://www.nba.com/standings"
URC_TEAM = "https://www.unitedrugby.com/latest/news/round-4-team-announcements/"
URC_TABLE = "https://stats.unitedrugby.com/match-centre/table/2026-27"
TOP14_TABLE = "https://top14.lnr.fr/classement"
LEGAVOLLEY = "https://www.legavolley.it/2026/credem-banca-superleague-weekends-games-45/?lang=en"
PCB_FIXTURES = "https://www.pcb.com.pk/pakistan-england-and-sri-lanka-trination-odi-series-202627/tournament/1465.html"
PCB_TIMING = "https://www.pcb.com.pk/press-release-detail/pakistan-england-sri-lanka-set-to-begin-preparations-for-odi-world-cup-with-tri-series-from-18-to-31.html"
PCB_FORM = "https://www.pcb.com.pk/news-detail/arafat-minhas-6-40-and-59-sink-england-as-pakistan-win-consecutive-games-in-odi-tri-series.html"
NZC_FIXTURES = "https://scoring.nzc.nz/fixtures"
BCCI_FIXTURES = "https://www.bcci.tv/news/article/india-womens-squads-for-t20i-and-odi-series-against-zimbabwe-announced"
BCCI_MATCH2 = "https://www.bcci.tv/matches/88d47fe3-ead4-4b91-b0cc-4bda908fb8d7/india-women-vs-zimbabwe-women"
BCCI_INJURY = "https://www.bcci.tv/news/article/jintimani-kalita-replaces-renuka-singh-thakur-in-indias-odi-squad"
BCCI_FORM = "https://www.bcci.tv/matches/023cf7d3-6571-4932-997b-cac801ed0b4a/india-women-vs-zimbabwe-women"
WTA_NINGBO = "https://www.wtatennis.com/news/4598225/rybakina-survives-shnaider-test-sets-up-ningbo-final-with-fernandez"
WTA_OSAKA = "https://www.wtatennis.com/tournaments/405/osaka/2026/draws"
ATP_ALMATY = "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"
ATP_REPORT = "https://www.atptour.com/en/news/medvedev-bublik-almaty-2026-saturday"
PDC_SESSION = "https://www.pdc.tv/news/2026/october/24/2026-machineseeker-european-championship---day-three-latest"
MUNSTER = "https://munster.gaa.ie/fixtures/events-calendar/"
KILKENNY = "https://kilkennygaa.ie/2026/10/county-final-weekend-at-upmc-nowlan-park-senior-junior-titles-on-the-line/"
GBGB = "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/"
F1 = "https://www.formula1.com/en/latest/article/what-time-is-the-formula-1-2026-united-states-grand-prix-and-how-can-i-watch-it.5jZFEoK96n4tpbRzEJjRoH"
F1_RACE_HUB = "https://www.formula1.com/en/racing/2026/united-states"
NRL = "https://www.nrl.com/news/2026/10/20/world-cup-team-lists-mens-round-2/"
EHF_TABLE = "https://ehfcl.eurohandball.com/men/2026-27/standings/"
PGA = "https://www.pgatour.com/leaderboard"
WST = "https://www.wst.tv/match-centre/52c4eaec-9056-44dc-a984-e8bb6f8db3d2"

CHECK_TARGETS = {
    "Golf": PGA,
    "Volleyball": LEGAVOLLEY,
    "Rugby Union": URC_TEAM,
    "Cricket": PCB_FIXTURES,
    "Snooker": WST,
    "Darts": PDC_SESSION,
    "Baseball": MLB_SCHEDULE,
    "Gaelic Sports": MUNSTER,
    "Greyhounds": GBGB,
    "Tennis": WTA_NINGBO,
    "Motor Racing": F1,
    "Handball": EHF_TABLE,
    "Ice Hockey": SCORE,
    "Basketball": NBA_INJURY,
    "Rugby League": NRL,
}

# GP / GF / GA were each read directly from the NHL 2026-27 team-summary JSON.
# Deliberately keep CGY blank: its object straddled a reader chunk, so this pass did
# not recover an unambiguous goal total.  The CGY game remains unpriced and flagged.
NHL_INPUTS = {
    "LAK": (8, 20, 29), "NJD": (10, 33, 31), "SJS": (11, 32, 36),
    "BOS": (11, 42, 22), "NYR": (12, 37, 29), "OTT": (11, 29, 30),
    "NSH": (9, 23, 28), "PIT": (11, 36, 37), "BUF": (10, 28, 36),
    "WSH": (9, 30, 29), "VGK": (12, 45, 36), "CBJ": (8, 19, 29),
    "CAR": (12, 47, 32), "STL": (10, 35, 31), "TOR": (12, 43, 38),
    "EDM": (10, 46, 32), "TBL": (10, 34, 29), "UTA": (11, 41, 36),
    "DET": (10, 27, 28), "MIN": (11, 32, 27), "SEA": (11, 42, 37),
    "PHI": (12, 20, 36), "ANA": (10, 27, 33),
}
NHL_NAMES = {
    "LAK": "Los Angeles Kings", "NJD": "New Jersey Devils", "SJS": "San Jose Sharks",
    "BOS": "Boston Bruins", "NYR": "New York Rangers", "OTT": "Ottawa Senators",
    "NSH": "Nashville Predators", "PIT": "Pittsburgh Penguins", "BUF": "Buffalo Sabres",
    "WSH": "Washington Capitals", "VGK": "Vegas Golden Knights", "CBJ": "Columbus Blue Jackets",
    "CAR": "Carolina Hurricanes", "STL": "St. Louis Blues", "TOR": "Toronto Maple Leafs",
    "EDM": "Edmonton Oilers", "TBL": "Tampa Bay Lightning", "UTA": "Utah Mammoth",
    "DET": "Detroit Red Wings", "CGY": "Calgary Flames", "MIN": "Minnesota Wild",
    "SEA": "Seattle Kraken", "PHI": "Philadelphia Flyers", "ANA": "Anaheim Ducks",
}
# NHL daily JSON: game id; OLBG event_id; away/home abbreviations; official UTC start;
# venue; league-published away/home records; FanDuel partnerId=7 away/home quotes;
# named active-season leader statistics shown in *this game*'s official teamLeaders.
NHL_GAMES = [
    (2026020168, "199999", "ANA", "PHI", "2026-10-24T17:00:00Z", "Xfinity Mobile Arena", "4-6-0", "3-6-3", 100, -120, "Beckett Sennecke 5 goals; Leo Carlsson 9 assists", "Matvei Michkov 6 goals"),
    (2026020169, "200000", "LAK", "NJD", "2026-10-24T19:30:00Z", "Prudential Center", "2-4-2", "6-4-0", 162, -194, "Artemi Panarin 6 goals; Brandt Clarke 5 assists", "Arseny Gritsyuk 5 goals; Jack Hughes 8 assists"),
    (2026020170, "200007", "SJS", "BOS", "2026-10-24T23:00:00Z", "TD Garden", "6-4-1", "8-2-1", 146, -178, "Macklin Celebrini 5 goals, 9 assists", "David Pastrnak 6 goals, 10 assists"),
    (2026020171, "200008", "NYR", "OTT", "2026-10-24T23:00:00Z", "Canadian Tire Centre", "7-4-1", "7-4-0", 106, -128, "Alexis Lafrenière 8 goals; Adam Fox 14 assists", "Tim Stützle 7 goals, 8 assists; Linus Ullmark 7 wins"),
    (2026020172, "200006", "NSH", "PIT", "2026-10-24T23:00:00Z", "PPG Paints Arena", "3-3-3", "4-6-1", 106, -128, "Ryan O'Reilly 4 goals; Roman Josi 8 assists", "Evgeni Malkin 6 goals; Erik Karlsson 10 assists"),
    (2026020174, "200001", "VGK", "CBJ", "2026-10-24T23:00:00Z", "Nationwide Arena", "8-4-0", "3-5-0", -138, 116, "Mark Stone 8 goals; Jack Eichel 13 assists", "Kent Johnson 4 goals; Zach Werenski 6 assists"),
    (2026020175, "200002", "CAR", "STL", "2026-10-24T23:00:00Z", "Enterprise Center", "8-2-2", "5-4-1", -154, 128, "Sebastian Aho 7 goals; Jackson Blake 10 assists", "Mason McTavish 6 goals; Dylan Holloway 7 assists"),
    (2026020176, "200010", "TOR", "EDM", "2026-10-24T23:00:00Z", "Rogers Place", "6-4-2", "8-1-1", 150, -182, "Auston Matthews 8 goals, 10 assists", "Leon Draisaitl 10 goals; Connor McDavid 23 assists"),
    (2026020177, "200009", "TBL", "UTA", "2026-10-25T01:00:00Z", "Delta Center", "7-3-0", "7-4-0", 120, -144, "Brandon Hagel 7 goals; Nikita Kucherov 9 assists", "Nick Schmaltz 7 goals; Mikhail Sergachev 10 assists"),
    (2026020178, "200004", "DET", "CGY", "2026-10-25T02:00:00Z", "Scotiabank Saddledome", "4-3-3", "3-6-0", -130, 108, "Alex DeBrincat 6 goals, 6 assists", "Morgan Frost 3 goals; Joel Farabee 5 assists"),
    (2026020179, "200005", "MIN", "SEA", "2026-10-25T02:00:00Z", "Climate Pledge Arena", "6-3-2", "7-3-1", -160, 132, "Kirill Kaprizov 11 goals; Quinn Hughes 11 assists", "Frederick Gaudreau 6 goals; Chandler Stephenson 8 assists"),
]


def utc_local(date: str, clock: str, zone: str) -> str:
    """Explicit time-zone conversion, never infer an unlabelled OLBG display time."""
    return datetime.fromisoformat(f"{date}T{clock}").replace(tzinfo=ZoneInfo(zone)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fixture(fid, sport, olbg_id, home, away, date, source, *, competition="", local=None,
            utc=None, zone=None, venue=None, facts=(), stats=None, extra_sources=(),
            timing_note=None, status_note=None, category="match"):
    if local and zone:
        derived_utc = utc_local(date, local, zone)
        if utc is not None:
            assert derived_utc == utc, (fid, utc, derived_utc)
        utc = derived_utc
    return dict(id=fid, sport=sport, olbg_event_id=olbg_id,
                home=home, away=away, date=date, start_utc=utc,
                published_start=f"{date} {local} ({zone})" if local else (utc or None),
                start_rule=timing_note or ("calculated from explicitly zoned league time" if local else ("league UTC time" if utc else "not published by source")),
                venue=venue, official_url=source, extra_official_urls=list(extra_sources),
                competition=competition, kind=category, status_note=status_note,
                facts=[dict(claim=c, url=u) for c, u in facts], stats=stats)


def assemble() -> tuple[list[dict], list[dict]]:
    official = []
    sources = {}

    def add_source(url, scope, description):
        assert url.startswith("https://"), url
        if url not in sources:
            method = ("Official-site indexed excerpt only; direct page body was blocked by a cookie wall; manual re-read needed"
                      if url == PDC_SESSION else
                      "Official-site indexed draw excerpt only; direct WTA page rendered notifications, not draw cells"
                      if url == WTA_OSAKA else
                      "First-hand official page/API read by web tool; structured fact transcription only, full raw body not persisted")
            sources[url] = dict(url=url, scope=scope, checked_on="2026-10-24",
                                what_checked=description, capture=method)

    for url, scope, desc in [
        (SCORE, "NHL", "24 Oct schedule IDs, states, time, venue, records, leaders; FanDuel partnerId 7 odds"),
        (SUMMARY, "NHL", "2026-27 team summary GP, goals for/against (API excludes shootout deciding goals)"),
        (BOS_RECENT, "NHL", "22 Oct Bruins 6-0 Predators; DiPietro 28 saves and Pastrnak two goals, two assists"),
        (SJS_RECENT, "NHL", "22 Oct Sharks 6-2 Senators; Askarov 41 saves"),
        (MLB_SCHEDULE, "MLB", "World Series Game 2 gamePk, teams, pitchers, date, time, status"),
        (MLB_STAND, "MLB", "Rays and Brewers regular-season W/L, scored/allowed, home/road splits"),
        (MLB_PITCHERS, "MLB", "Rasmussen and Henderson 2026 season pitching ERA and innings"),
        (NBA_INJURY, "NBA", "24 Oct 1:00 pm ET report: matchup, scheduled time, teams, listed absences"),
        (NBA_TABLE, "NBA", "2026-27 standings W/L; sample size one or two games"),
        (URC_TEAM, "URC", "24 Oct Ospreys–Dragons pairing, 19:00 UK kickoff, named squads"),
        (URC_TABLE, "URC", "Ospreys and Dragons 2026-27 GP/W/PF/PA, pre-match"),
        (TOP14_TABLE, "Top 14", "2026-27 teams' GP, W, PF and PA"),
        (LEGAVOLLEY, "Volleyball", "25 Oct SuperLega pairings and local starts; round-one context"),
        (PCB_FIXTURES, "Cricket", "ODI tri-series 25/27/29 Oct pairings and venues"),
        (PCB_TIMING, "Cricket", "PCB press release explicitly says all tri-series matches begin at 1pm PKT"),
        (PCB_FORM, "Cricket", "Pakistan 87-run win against England on 20 Oct; Arafat Minhas 6-40 and 59"),
        (NZC_FIXTURES, "Cricket", "India vs New Zealand 3rd T20I date and pairing; displayed clock varies by reader timezone, so no UTC start transcribed"),
        (BCCI_FIXTURES, "Cricket", "25 Oct India W vs Zimbabwe W second ODI, 14:00 IST, Vadodara"),
        (BCCI_MATCH2, "Cricket", "25 Oct second ODI match page: 04:30 EDT start and BCA Stadium, Vadodara; matches 14:00 IST"),
        (BCCI_FORM, "Cricket", "India W won first ODI by nine wickets on 23 Oct"),
        (BCCI_INJURY, "Cricket", "Renuka Singh Thakur replaced by Jintimani Kalita for ODI squad"),
        (WTA_NINGBO, "Tennis", "Rybakina vs Fernandez final on Sunday, semi-final results and H2H 3-2"),
        (WTA_OSAKA, "Tennis", "24 Oct Osaka draw still displayed semi-final slots; cannot confirm Krueger–Siniakova final"),
        (ATP_ALMATY, "Tennis", "Sunday final: Medvedev vs Basilashvili, not before 15:00 local"),
        (ATP_REPORT, "Tennis", "Saturday results, Medvedev 37 hard-court wins, Basilashvili over Tsitsipas"),
        (PDC_SESSION, "Darts", "24 Oct evening session pairings; exact match starts not published"),
        (MUNSTER, "Gaelic Football", "25 Oct St Finbarrs–Nemo Rangers Cork final, 16:00 local"),
        (KILKENNY, "Hurling", "25 Oct Ballyhale Shamrocks–Tullaroan Kilkenny senior final, venue; no official throw-in time on this article"),
        (GBGB, "Greyhounds", "24 Oct Scurry Gold Cup final and Shadow Storm 15.66sec semi; not a race-card source"),
        (F1, "Formula 1", "Austin race 25 Oct 15:00 track local, 24 Oct qualifying 16:00 local"),
        (F1_RACE_HUB, "Formula 1", "Official USA Grand Prix hub: Charles Leclerc topped FP2 in 1:35.291; circuit and lap count"),
        (NRL, "Rugby League", "2026 RLWC fixtures, but no matching OLBG match tips in the captured first page"),
        (EHF_TABLE, "Handball", "EHF 2026-27 group standings and Oct 28–29 upcoming fixture links"),
        (PGA, "Golf", "Bermuda event underway 22–25 Oct, while OLBG golf hub shows no tips"),
        (WST, "Snooker", "24 Oct Mark Williams v Jak Jones Northern Ireland Open semifinal; WST labels it Live Now"),
    ]:
        add_source(url, scope, desc)

    for row in NHL_GAMES:
        game_id, eid, away, home, start, venue, ar, hr, ao, ho, af, hf = row
        stats = None
        if home in NHL_INPUTS and away in NHL_INPUTS:
            stats = dict(kind="nhl", away=dict(zip(("gp", "gf", "ga"), NHL_INPUTS[away])),
                         home=dict(zip(("gp", "gf", "ga"), NHL_INPUTS[home])),
                         input_url=SUMMARY)
        official.append(fixture(f"nhl-{game_id}", "Ice Hockey", eid, NHL_NAMES[home], NHL_NAMES[away],
                                "2026-10-24", SCORE, competition="NHL 2026-27",
                                utc=start, venue=venue, stats=stats, extra_sources=(SUMMARY,),
                                facts=[(f"{NHL_NAMES[away]}: {ar}; {af}", SCORE),
                                       (f"{NHL_NAMES[home]}: {hr}; {hf}", SCORE),
                                       *(([(f"{NHL_NAMES[away]} GP/GF/GA {NHL_INPUTS[away]}; {NHL_NAMES[home]} GP/GF/GA {NHL_INPUTS[home]}", SUMMARY)]
                                          if stats else []))],
                                status_note="PRE on league feed at collection" if game_id == 2026020168 else None))
        if game_id == 2026020170:
            official[-1]["facts"].extend([
                dict(claim="Boston defeated Nashville 6-0 on 22 October; Michael DiPietro stopped 28 shots and David Pastrnak scored twice with two assists", url=BOS_RECENT),
                dict(claim="San Jose defeated Ottawa 6-2 on 22 October; Yaroslav Askarov made 41 saves", url=SJS_RECENT),
            ])
            official[-1]["extra_official_urls"].extend([BOS_RECENT, SJS_RECENT])
        official[-1]["official_game_id"] = game_id
        official[-1]["nhl_abbrevs"] = dict(away=away, home=home)
        official[-1]["team_records"] = dict(away=ar, home=hr)
        official[-1]["leaders"] = dict(away=af, home=hf)
        official[-1]["offered_quote"] = dict(provider="FanDuel via NHL score feed", source_url=SCORE,
                                               away_american=ao, home_american=ho,
                                               note="league-served quote at capture, not an OLBG or currently available price")

    official.append(fixture("mlb-849802", "Baseball", "160792", "Milwaukee Brewers", "Tampa Bay Rays",
                            "2026-10-24", MLB_SCHEDULE, competition="MLB World Series Game 2",
                            utc="2026-10-25T00:00:00Z", venue="American Family Field",
                            extra_sources=(MLB_STAND, MLB_PITCHERS),
                            facts=[("MLB gamePk 849802 is listed as scheduled, 2026-10-25T00:00Z; Rays at Brewers; Drew Rasmussen and Logan Henderson are probable starters", MLB_SCHEDULE),
                                   ("Milwaukee 103-59, 832 RS, 618 RA; Tampa Bay 98-64, 736 RS, 650 RA over 162 regular-season games", MLB_STAND),
                                   ("Rasmussen 2.67 ERA in 172.0 IP; Henderson 2.47 ERA in 98.1 IP", MLB_PITCHERS)],
                            stats=dict(kind="mlb", home=dict(gp=162, rs=832, ra=618, w=103),
                                       away=dict(gp=162, rs=736, ra=650, w=98), input_url=MLB_STAND)))

    # Rugby union: official calendar + standings.  Actual team sheets do not establish injury status.
    official.append(fixture("urc-osp-dra", "Rugby Union", "609581", "Ospreys", "Dragons RFC",
                            "2026-10-24", URC_TEAM, competition="United Rugby Championship R4",
                            local="19:00", zone="Europe/London", venue="St. Helen's, Swansea",
                            extra_sources=(URC_TABLE,),
                            facts=[("URC lists Ospreys–Dragons on 24 Oct, 19:00 UK, and names Tom Rogers and Rio Dyer in the starting sides", URC_TEAM),
                                   ("Ospreys PL3 W1 PF81 PA107; Dragons PL3 W1 D1 PF88 PA83", URC_TABLE)],
                            stats=dict(kind="rugby", home=dict(gp=3, pf=81, pa=107),
                                       away=dict(gp=3, pf=88, pa=83), input_url=URC_TABLE)))
    for fid, eid, home, away, date, clock, url, gp_h, pf_h, pa_h, gp_a, pf_a, pa_a, home_fact, away_fact in [
        ("top14-toulon-pau", "609555", "RC Toulon", "Section Paloise", "2026-10-24", "21:00",
         "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11866-toulon-pau", 6, 130, 130, 6, 239, 181,
         "Toulon 2 wins in 6, 130 scored/130 allowed", "Pau 5 wins in 6, 239 scored/181 allowed"),
        ("top14-rochelle-bordeaux", "609554", "Stade Rochelais", "Union Bordeaux-Bègles", "2026-10-25", "21:05",
         "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11864-la-rochelle-bordeaux-begles", 6, 144, 135, 6, 215, 151,
         "La Rochelle 4 wins in 6, 144 scored/135 allowed", "Bordeaux 4 wins in 6, 215 scored/151 allowed"),
    ]:
        add_source(url, "Top 14", "named 2026-27 fixture, local kickoff, team sheets, venue")
        official.append(fixture(fid, "Rugby Union", eid, home, away, date, url,
                                competition="Top 14 J7", local=clock, zone="Europe/Paris",
                                extra_sources=(TOP14_TABLE,),
                                facts=[(home_fact, TOP14_TABLE), (away_fact, TOP14_TABLE),
                                       (f"{home} vs {away}, {date} at {clock} France local", url)],
                                stats=dict(kind="rugby", home=dict(gp=gp_h, pf=pf_h, pa=pa_h),
                                           away=dict(gp=gp_a, pf=pf_a, pa=pa_a), input_url=TOP14_TABLE)))

    official.append(fixture("cricket-pak-eng-odi4", "Cricket", "188838", "Pakistan", "England",
                            "2026-10-25", PCB_FIXTURES, competition="Pakistan ODI tri-series",
                            local="13:00", zone="Asia/Karachi", venue="Gaddafi Stadium, Lahore",
                            timing_note="PCB confirms all tri-series matches at 1pm PKT", extra_sources=(PCB_FORM, PCB_TIMING),
                            facts=[("Pakistan beat England by 87 runs on 20 Oct; Arafat Minhas took 6-40 and scored 59", PCB_FORM),
                                   ("Pakistan vs England fourth ODI is in Lahore on 25 Oct", PCB_FIXTURES),
                                   ("PCB announces all matches begin at 13:00 PKT", PCB_TIMING)]))
    official.append(fixture("cricket-nz-ind-t20i3", "Cricket", "188852", "New Zealand", "India",
                            "2026-10-27", NZC_FIXTURES, competition="India in New Zealand T20I",
                            venue="Hnry Stadium, Wellington",
                            facts=[("BLACKCAPS vs India 3rd T20I shown on 27 Oct at Hnry Stadium, Wellington", NZC_FIXTURES)],
                            status_note="NZC page shows a reader-local time with no zone and changes with the capture locale. UTC start withheld"))
    official.append(fixture("cricket-ind-zim-w-odi2", "Cricket", "188847", "India Women", "Zimbabwe Women",
                            "2026-10-25", BCCI_FIXTURES, competition="Women's ODI 2nd", local="14:00", zone="Asia/Kolkata",
                            venue="BCA Stadium, Vadodara", extra_sources=(BCCI_MATCH2, BCCI_FORM, BCCI_INJURY),
                            facts=[("Second ODI scheduled 25 October at 14:00 IST, Vadodara", BCCI_FIXTURES),
                                   ("BCCI second ODI match page shows BCA Stadium, Vadodara, and 04:30 EDT (the same instant as 14:00 IST)", BCCI_MATCH2),
                                   ("India Women won the first ODI by nine wickets", BCCI_FORM),
                                   ("Renuka Singh Thakur ruled out of ODI series and replaced by Jintimani Kalita", BCCI_INJURY)],
                            status_note="OLBG lists a top-batsman prop, not a match-winner; no batter-specific rate captured"))
    # This is a *conflict*, not a 31 October start: the official 3rd Test begins 27 October.
    csa = "https://cricket.co.za/csa-announces-unmissable-2026-27-home-season-for-the-proteas-men/"
    add_source(csa, "Cricket", "3rd South Africa–Australia Test begins 27 Oct and runs to 31 Oct")
    aus_preview = "https://www.cricket.com.au/news/4597818/south-africa-v-australia-third-test-match-preview-guide-cape-town-newlands-broadcast-details-how-to-watch-team-news-session-start-times-2026"
    add_source(aus_preview, "Cricket", "24 Oct Cricket Australia preview reports 10:30 South Africa local for the 27 Oct start, conflicting with earlier CSA 10:00")
    official.append(fixture("cricket-sa-aus-3rd-test", "Cricket", "188835", "South Africa", "Australia",
                            "2026-10-27", csa, competition="3rd Test", zone="Africa/Johannesburg",
                            venue="Newlands Cricket Ground, Cape Town", extra_sources=(aus_preview,),
                            facts=[("CSA puts the third Test at 27–31 October in Cape Town, 10:00 local", csa),
                                   ("Cricket Australia newer preview says 10:30 local", aus_preview)],
                            status_note="Two official sources disagree on start time and OLBG displays 31 October (last scheduled day). Leave time and price blank"))

    for fid, eid, home, away, clock in [
        ("volley-trentino-cisterna", "36994", "Itas Trentino", "Cisterna Volley", "17:00"),
        ("volley-perugia-prata", "36997", "Sir Susa Scai Perugia", "Tinet Prata di Pordenone", "18:00"),
    ]:
        official.append(fixture(fid, "Volleyball", eid, home, away, "2026-10-25", LEGAVOLLEY,
                                competition="SuperLega R2", local=clock, zone="Europe/Rome",
                                facts=[(f"{home} vs {away} scheduled Sunday 25 Oct {clock} Italy local", LEGAVOLLEY)],
                                status_note="OLBG shortens 'Tinet Prata di Pordenone' to 'Pordenone'; alias requires review" if eid == "36997" else None))

    official.append(fixture("wst-williams-jones", "Snooker", "9952", "Mark Williams", "Jak Jones",
                            "2026-10-24", WST, competition="Northern Ireland Open semifinal",
                            venue="Belfast, Northern Ireland",
                            facts=[("WST match centre lists semifinal No. 62, Williams v Jones, 24 October and labels it 'Live Now'", WST)],
                            status_note="WST marked Live Now at read time; do not publish a pre-match selection"))

    # The WTA Osaka draw still had semifinal slots when read. Do not treat an OLBG final pairing as confirmed.
    official.append(fixture("tennis-ningbo-final", "Tennis", "902207", "Elena Rybakina", "Leylah Fernandez",
                            "2026-10-25", WTA_NINGBO, competition="BNB Ningbo Open Final",
                            facts=[("Rybakina beat Shnaider 6-3, 7-5; Fernandez beat Bouzkova 6-3, 7-5; Rybakina leads their H2H 3-2", WTA_NINGBO)],
                            status_note="Sunday date confirmed; official start time not recovered; no priced pick"))
    official.append(fixture("tennis-almaty-final", "Tennis", "902251", "Daniil Medvedev", "Nikoloz Basilashvili",
                            "2026-10-25", ATP_ALMATY, competition="ATP Almaty Open Final",
                            timing_note="not before 15:00 Almaty local; lower bound only; UTC start deliberately blank",
                            extra_sources=(ATP_REPORT,),
                            facts=[("ATP order of play names Medvedev and Basilashvili in Sunday's singles final, not before 15:00 local", ATP_ALMATY),
                                   ("Medvedev led Bublik 6-3 when Bublik retired; Basilashvili beat Tsitsipas 6-4, 6-7(5), 6-3", ATP_REPORT)],
                            status_note="ATP player overview records are not current to this semifinal; no strength price"))

    # PDC names opponents and session, but does not provide exact match starts; keep time blank.
    for fid, eid, a, b in [
        ("darts-aspinall-littler", "32397", "Nathan Aspinall", "Luke Littler"),
        ("darts-clayton-rock", "32400", "Jonny Clayton", "Josh Rock"),
    ]:
        official.append(fixture(fid, "Darts", eid, a, b, "2026-10-24", PDC_SESSION,
                                competition="PDC European Championship R2",
                                facts=[(f"{a} vs {b} in Saturday evening session 19:00–23:00 CEST; best of 19 legs", PDC_SESSION)],
                                status_note="Official-site indexed excerpt only; direct PDC page returned cookie wall. Exact start missing and match may be underway. No price"))

    official.append(fixture("gaa-cork-final", "Gaelic Sports", "3530", "St Finbarrs", "Nemo Rangers",
                            "2026-10-25", MUNSTER, competition="Cork Premier SFC Final",
                            local="16:00", zone="Europe/Dublin", venue="SuperValu Páirc Uí Chaoimh",
                            facts=[("Munster GAA calendar names St Finbarrs vs Nemo Rangers on 25 Oct at 16:00 in Cork", MUNSTER)],
                            status_note="OLBG handicap +1.5 has no independent current-form margin input; no price"))
    official.append(fixture("gaa-kilkenny-hurling-final", "Gaelic Sports", "714", "Shamrocks Ballyhale", "Tullaroan",
                            "2026-10-25", KILKENNY, competition="Kilkenny Senior Hurling Final",
                            venue="UPMC Nowlan Park",
                            facts=[("Kilkenny GAA confirms Shamrocks Ballyhale v Tullaroan on Sunday 25 October at Nowlan Park", KILKENNY)],
                            status_note="OLBG says Ballyhale Shamrocks, Kilkenny GAA says Shamrocks Ballyhale (name order not independently reconciled). Official article gives no throw-in time; start and fair line remain blank"))

    official.append(fixture("f1-usa-gp", "Motor Racing", "913", "United States Grand Prix", None,
                            "2026-10-25", F1, category="race", competition="Formula 1",
                            local="15:00", zone="America/Chicago", venue="Circuit of The Americas",
                            extra_sources=(F1_RACE_HUB,),
                            facts=[("The Grand Prix is on 25 Oct at 15:00 Austin local", F1),
                                   ("The Formula 1 United States GP hub lists Charles Leclerc fastest in FP2 at 1:35.291", F1_RACE_HUB)],
                            status_note="Race winner is an outright, not a team-versus-team match; no probabilistic price"))

    # NBA injury PDF *does* contain matchup/date/tip; games shell by itself failed.
    # One incident: OLBG's NOP and GSW listed hour disagrees with this official report.
    for eid, home, away, abbrevs, et, season_records in [
        ("536117", "Charlotte Hornets", "Miami Heat", "MIA@CHA", "18:00", "1-1 / 0-2"),
        ("536112", "Cleveland Cavaliers", "Brooklyn Nets", "BKN@CLE", "19:30", "0-1 / 0-1"),
        ("536111", "Philadelphia 76ers", "Milwaukee Bucks", "MIL@PHI", "19:30", "2-0 / 0-2"),
        ("536114", "Dallas Mavericks", "San Antonio Spurs", "SAS@DAL", "20:00", "1-1 / 0-2"),
        ("536113", "Chicago Bulls", "Washington Wizards", "WAS@CHI", "20:00", "1-1 / 1-1"),
        ("536115", "Atlanta Hawks", "Houston Rockets", "HOU@ATL", "20:30", "2-0 / 2-0"),
        ("536116", "Denver Nuggets", "New Orleans Pelicans", "NOP@DEN", "21:00", "0-1 / 0-2"),
        ("536118", "Phoenix Suns", "Golden State Warriors", "GSW@PHX", "22:00", "0-1 / 0-2"),
    ]:
        fact = [(f"NBA 1:00pm ET injury report lists {abbrevs} on 24 Oct at {et} ET", NBA_INJURY),
                (f"NBA standings: {home} / {away} {season_records} after one or two games", NBA_TABLE)]
        if eid == "536115":
            fact.append(("Houston: Steven Adams Out (ankle management), Fred VanVleet Out (knee management), Reed Sheppard Questionable (knee contusion); Atlanta: Mouhamed Gueye Out (foot fracture)", NBA_INJURY))
        official.append(fixture(f"nba-{eid}", "Basketball", eid, home, away, "2026-10-24",
                                NBA_INJURY, competition="NBA 2026-27", local=et, zone="America/New_York",
                                extra_sources=(NBA_TABLE,), facts=fact,
                                status_note="OLBG hour differs from official ET report; use report time" if eid in ("536116", "536118") else
                                ("Milwaukee report NOT YET SUBMITTED at 1:00pm ET" if eid == "536111" else "Only 1–2 official season games; price withheld")))

    for fid, eid, date, clock, a, b, ag, bg, ul in [
        ("ehf-magdeburg-kriens", "12136", "2026-10-28", "20:45", "SC Magdeburg", "HC Kriens-Luzern", (5, 176, 140), (5, 158, 161),
         "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101065/SCMagdeburg-HCKriensLuzern/"),
        ("ehf-vardar-melsungen", "12130", "2026-10-28", "18:45", "HC Vardar 1961", "MT Melsungen", (5, 154, 158), (5, 138, 138),
         "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101022/HCVardar1961-MTMelsungen/"),
        ("ehf-kielce-kolstad", "12132", "2026-10-28", "20:45", "Industria Kielce", "Kolstad Håndball", (5, 155, 153), (5, 143, 178),
         "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101067/IndustriaKielce-KolstadH%C3%A5ndball/"),
        ("ehf-gog-sporting", "12129", "2026-10-29", "18:45", "GOG", "Sporting Clube de Portugal", (5, 178, 172), (5, 191, 165),
         "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101040/GOG-SportingClubedePortugal/"),
    ]:
        add_source(ul, "EHF", f"{a} vs {b} in group-phase Round 6 at {clock} league local")
        official.append(fixture(fid, "Handball", eid, a, b, date, ul,
                                competition="EHF Champions League Men", local=clock, zone="Europe/Berlin",
                                extra_sources=(EHF_TABLE,),
                                facts=[(f"{a} GP {ag[0]} GF {ag[1]} GA {ag[2]}; {b} GP {bg[0]} GF {bg[1]} GA {bg[2]}", EHF_TABLE),
                                       (f"{a} vs {b}, {date} {clock} European local", ul)],
                                stats=dict(kind="handball", home=dict(gp=ag[0], pf=ag[1], pa=ag[2]),
                                           away=dict(gp=bg[0], pf=bg[1], pa=bg[2]), input_url=EHF_TABLE),
                                status_note="OLBG's top pick is Tie; its tip share is not a win probability. Only the three-way Money Line was observed on the event page" if eid == "12136" else None))

    return official, list(sources.values())


def write(name, obj):
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    first_page = json.loads(CAPTURE.read_text(encoding="utf-8"))
    hurling = json.loads(HURLING_CAPTURE.read_text(encoding="utf-8"))
    write("captures/manifest.json", dict(
        evidence_date="2026-10-24", raw_http_bodies_archived=False,
        note="Hashes cover structured extracts only. The 96-row input traces to a pinned repository commit; the extra Hurling record is first-hand.",
        captures=[dict(path=str(path.relative_to(DATA)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                       record_type="structured extract (not raw HTTP)") for path in (CAPTURE, HURLING_CAPTURE)]))
    assert {s for s in SPORTS} == set(first_page["hubs"])
    assert hurling["listing"]["subsport"] == "Hurling"
    discovery = [*first_page["listings"], hurling["listing"]]
    olbg_ids = {r["event_id"] for r in discovery}
    assert len(olbg_ids) == len(discovery), "single first-page row per event id"
    fixtures, sources = assemble()
    ids = [f["olbg_event_id"] for f in fixtures]
    assert len(ids) == len(set(ids)), "each OLBG event can match at most one official record"
    assert set(ids) <= olbg_ids, "never invent an OLBG event"
    assert {f["sport"] for f in fixtures} <= set(SPORTS)
    official_ids = set(ids)
    for r in discovery:
        if r["event_id"] not in official_ids:
            assert r.get("url", "").startswith("https://www.olbg.com/")
    listing_counts = Counter(r["sport"] for r in discovery)
    confirmed_counts = Counter(f["sport"] for f in fixtures)
    write("discovery.json", dict(as_of_utc=STAMP, imported_first_page_rows=len(first_page["listings"]),
                                  independently_checked_hurling_rows=1, first_page_only=True,
                                  source_sha256=first_page["source_sha256"], listings=discovery))
    write("olbg_taxonomy.json", dict(as_of_utc=STAMP, first_page_source=first_page["source_committed_file"],
                                     first_page_source_sha256=first_page["source_sha256"],
                                     added_hurling_source=HURLING_CAPTURE.name,
                                     first_page_only=True, hubs=[dict(sport=s, **first_page["hubs"][s],
                                                                     **({"subhub_url": hurling["hub"], "sport_ids": [25, 26]}
                                                                        if s == "Gaelic Sports" else {}),
                                                                     official_check_target=CHECK_TARGETS[s],
                                                                     listings=listing_counts[s], official_matches=confirmed_counts[s])
                                                                 for s in SPORTS],
                                     reverse_engineering=[
                                         "Hub route: /betting-tips/{Sport_Slug}/{numericSportId}; event route: /betting-tips/{Sport}/{group}/{competition}/{event}/{sportId}?event_id={id}.",
                                         "Hub surfaces only the most-tipped selection per event. Event pages can show more markets, but neither a full active inventory nor offered odds were recovered from hub HTML.",
                                         "Ice Hockey event pages expose Money Line, Puck Line and Game Totals; Handball Magdeburg–Kriens page exposed Money Line only. Market coverage is not implied for uninspected events.",
                                         "Promotional cards interrupt tip rows; 'Load More Tips' means the 96 imported listings and one separately checked Hurling match are first-page records only. Gaelic Sports includes Gaelic Football id 25 plus Hurling id 26; Golf hub returned 'No tips found' and Rugby League displayed 2027 outrights rather than matches.",
                                         "The listed time string is copied verbatim and not used as a UTC start. It disagrees with the NBA injury report for NOP@DEN and GSW@PHX, and with the CSA third Test start for South Africa v Australia.",
                                     ]))
    write("fixtures.json", dict(as_of_utc=STAMP, count=len(fixtures),
                                capture_note="24 Oct official reads transcribed; PDC/WTA Osaka comparisons use indexed excerpts where page body was unavailable. Full raw HTTP bodies not archived", 
                                fixtures=fixtures))
    write("sources.json", dict(as_of_utc=STAMP, count=len(sources), sources=sources))
    # A pragmatic line-by-line audit of the *latest merged repository at claim time*.
    # Do not hand-wave structural consistency into fresh external verification.
    write("repo_audit.json", dict(as_of_utc=STAMP, reviewed_main_sha="6926afe", findings=[
        dict(code="VR-01", severity="high", path="index.html:10-35; scripts/build_site.py:443-530", status="open",
             finding="The root nav opens /today/ as the new 24 October board but still labels /cadence/ 'Current' and keeps a 23 October stripe and a 23 October hero. Readers can mistake the older picks for today's. The two scopes should be clearly labelled without editing an active integration owner's files.",
             source_url="https://api-web.nhle.com/v1/score/2026-10-24"),
        dict(code="VR-02", severity="high", path="data/today/olbg_listings.json:1-14; data/vantage/captures/olbg_hurling_first_page.json", status="open",
             finding="The 96 imported OLBG records plus one first-hand Hurling record are first-page extracts, not a complete sport inventory. Interleaved promo cards and Load More Tips prevent an exhaustive list without pagination capture.",
             source_url="https://www.olbg.com/betting-tips/Volleyball/21"),
        dict(code="VR-03", severity="high", path="data/today/olbg_listings.json:90-150; scripts/today_seed.py:119-150", status="open",
             finding="NBA games page failed but the 1pm ET official injury report names eight NBA matchups and tip times. Treat its player-status extract cautiously: row spans and NOT YET SUBMITTED are not a clean injury feed.",
             source_url=NBA_INJURY),
        dict(code="VR-04", severity="high", path="data/today/lines.json:1-60; scripts/today_model.py", status="open",
             finding="A fair -250…+10000 calculation is not an observed OLBG price. The NHL league feed does supply a distinct FanDuel partnerId=7 quote for some moneylines; show both separately and never substitute tip support percentages for a probability.",
             source_url=SCORE),
        dict(code="VR-05", severity="high", path="data/cadence/matches.json:1-8; index.html", status="open",
             finding="A dated desk stays on GitHub Pages after events start. A clean root needs a visible as-of timestamp and browser-time expiry warning; a successful build or deploy does not refresh the evidence.",
             source_url=STAND),
        dict(code="VR-06", severity="medium", path="COORDINATION.md:3216-3628,4895-4896", status="open",
             finding="Historical merge separators and conflict markers remain in the shared task board; they are prior records, not introduced by this session.",
             source_url="https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md"),
        dict(code="VR-07", severity="medium", path="REPO_REVIEW.md:51-56", status="open",
             finding="Legacy scope note says Greyhounds and Gaelic Football are excluded despite the current explicit 15-sport request including both. Older 17-sport desks additionally show eSports/Aussie Rules; keep them historical and out of the current shortlist.",
             source_url="https://www.olbg.com/betting-tips/Gaelic_Football/25"),
        dict(code="VR-08", severity="high", path="data/today/olbg_listings.json: first-page NBA & cricket rows", status="open",
             finding="OLBG NOP@DEN and GSW@PHX displayed times are one hour later than the NBA's 1pm ET report; its South Africa v Australia row is dated the third Test's final day, not the CSA-confirmed 27 Oct start. Times cannot be silently used as official UTC.",
             source_url=NBA_INJURY),
        dict(code="VR-09", severity="medium", path="scripts/today_seed.py:169; data/today/olbg_listings.json:1239", status="open",
             finding="The separate /today/ source transcript spells Flyers leader 'Michael Michkov'. The NHL 24 Oct game leader object identifies Matvei Michkov with six goals. Vantage uses Matvei and records the older transcript as a typo, without changing another session's files.",
             source_url=SCORE),
    ]))
    print(f"vantage_seed: {len(discovery)} dated first-page OLBG rows (96 imported + 1 first-hand Hurling), {len(fixtures)} official match/race records, {len(sources)} official URLs; {len(SPORTS)} exact sports")


if __name__ == "__main__":
    main()
