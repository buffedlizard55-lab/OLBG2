#!/usr/bin/env python3
"""Build the source register and the review queue for the 2026-10-24 snapshot."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
OLBG = "https://www.olbg.com/betting-tips"

SOURCES = [
    ("NHL scores feed, 2026-10-24", "https://api-web.nhle.com/v1/score/2026-10-24",
     "Read in full across the paged response: 12 games, start times, 2026-27 records, per-team leaders, league odds array.",
     "used"),
    ("NHL schedule feed, 2026-10-24", "https://api-web.nhle.com/v1/schedule/2026-10-24",
     "Read: game states, startTimeUTC, venues, broadcast lists, odds arrays. Used to confirm starts for the two games whose score-feed chunk was truncated.",
     "used"),
    ("NHL standings, 2026-10-24", "https://api-web.nhle.com/v1/standings/2026-10-24",
     "Partially read (first page). Standings timestamp 2026-10-24T17:06:30Z confirmed; goal totals seen for Carolina, Edmonton, Boston and Vegas.",
     "partial"),
    ("MLB Stats API schedule, 2026-10-24", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team",
     "One game returned: Tampa Bay Rays at Milwaukee Brewers, first pitch 2026-10-25T00:00:00Z, probable pitchers Drew Rasmussen and Logan Henderson.",
     "used"),
    ("MLB Stats API team standings, Brewers", "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings&season=2026",
     "Milwaukee 103-59, 832 runs scored, 618 allowed, 55-26 home, 8-2 last ten.",
     "used"),
    ("MLB Stats API league standings", "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026",
     "First page read: Tampa Bay 98-64, 736 scored, 650 allowed, 43-38 away, 5-5 last ten.",
     "partial"),
    ("NBA games page, 2026-10-24", "https://www.nba.com/games?date=2026-10-24",
     "Calendar rendered (8 games on 24 October) but the game payload failed with \"Sorry, something went wrong\"; no per-game data.",
     "blocked"),
    ("NBA CDN today's scoreboard", "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
     "HTTP 500 on two attempts.", "blocked"),
    ("NBA stats scoreboard v3", "https://stats.nba.com/stats/scoreboardv3?GameDate=2026-10-24&LeagueID=00",
     "Request failed (no response body).", "blocked"),
    ("United Rugby Championship match centre", "https://www.unitedrugby.com/match-centre",
     "Read: Round 3 and Round 4 results with scores and venues; Round 4 games dated 23 October. No 24 October fixture detail reached within the page portion read.",
     "partial"),
    ("Handball-Bundesliga fixture page", "https://www.daikin-hbl.de/de/spielplan/",
     "HTTP 404; the site redirected to a not-found page that links to https://www.opel-hbl.de/de/hbl/spielplan.",
     "blocked"),
    ("World Snooker Tour match centre", "https://wst.tv/matches/",
     "Read: BetVictor Northern Ireland Open 2026 match list from Round 1 (18-19 October). Today's match not reached within the page portion read.",
     "partial"),
]

FLAGS = [
    dict(code="NO-LISTING", sport="Golf",
         detail="The Golf hub returned \"No tips found.\" at 17:16 UTC. OLBG listed no golf event, so there was nothing to attach a pick to.",
         source=f"{OLBG}/Golf/5", needs="A golf event to be listed on OLBG before a golf pick can exist."),
    dict(code="NO-MATCH-EVENTS", sport="Rugby League",
         detail="The Rugby League hub listed only 2027 outright futures (State of Origin, Super League, NRL). No Rugby League match event was listed.",
         source=f"{OLBG}/Rugby_League/10", needs="A listed Rugby League match event."),
    dict(code="OFFICIAL-FEED-BLOCKED", sport="Basketball",
         detail="Ten basketball events were listed, including nine NBA games, but no official NBA fixture data could be read: the games page returned its shell with an error message, and the scoreboard endpoints returned HTTP 500 or failed.",
         source="https://www.nba.com/games?date=2026-10-24", needs="An NBA fixture feed that returns per-game data."),
    dict(code="NO-OFFICIAL-FORM-SOURCE", sport="Greyhounds",
         detail="Nine race listings were captured, but GBGB does not publish per-race dog form or trap data at a URL reachable here, so no greyhound pick is published.",
         source="https://www.gbgb.org.uk/", needs="A reachable official racecard source."),
    dict(code="NOT-CONFIRMED", sport="Tennis",
         detail="Six tennis matches were listed for 25-26 October. No ATP or WTA page was read in this capture window, so no fixture, ranking or form fact is asserted.",
         source=f"{OLBG}/Tennis/3", needs="An ATP/WTA match page for each listed match."),
    dict(code="NOT-CONFIRMED", sport="Cricket",
         detail="Eleven cricket events were listed, including a Pakistan v England ODI and four CSA T20 games. No governing-body page was read in this capture, so no cricket pick is published.",
         source=f"{OLBG}/Cricket/7", needs="A board or ICC fixture page for each listed match."),
    dict(code="NOT-CONFIRMED", sport="Volleyball",
         detail="Twelve volleyball matches were listed across Austrian, German, Polish, French, Dutch, Brazilian and Italian leagues. No league page was read in this capture.",
         source=f"{OLBG}/Volleyball/21", needs="A league fixture/standings page per competition."),
    dict(code="OFFICIAL-FEED-BLOCKED", sport="Handball",
         detail="Ten handball matches were listed. The Bundesliga fixture URL tried returned HTTP 404, so no handball fixture could be confirmed.",
         source="https://www.daikin-hbl.de/de/spielplan/", needs="A working HBL and ASOBAL fixture/standings page."),
    dict(code="NOT-CONFIRMED", sport="Darts",
         detail="Five PDC matches were listed. Four of them had displayed start times before the capture window and no PDC page was read, so none is published.",
         source=f"{OLBG}/Darts/15", needs="A PDC match schedule page."),
    dict(code="NOT-CONFIRMED", sport="Snooker",
         detail="One snooker match was listed (Mark Williams v Jak Jones). The WST match centre was read only as far as the Round 1 results, so the match could not be confirmed from the governing body.",
         source="https://wst.tv/matches/", needs="The WST page section covering 24 October."),
    dict(code="NOT-CONFIRMED", sport="Gaelic Sports",
         detail="Four club matches were listed (Galway, Cork and Limerick championships). No county-board page was read, so no Gaelic pick is published.",
         source="https://www.gaa.ie/", needs="County board fixture pages with throw-in times."),
    dict(code="NOT-CONFIRMED", sport="Motor Racing",
         detail="The United States Grand Prix was listed for 25 October with Max Verstappen the most-tipped driver. No Formula 1 page was read in this capture, so no motor-racing pick is published.",
         source=f"{OLBG}/Motor_Racing/14", needs="The Formula 1 event page and grid/qualifying result."),
    dict(code="QUOTA-SHORTFALL", sport="Baseball",
         detail="One officially sourced baseball fixture exists (the World Series game). The five-per-sport target cannot be met from a single scheduled game.",
         source="https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24", needs="More than one scheduled game."),
    dict(code="STARTED-AT-CAPTURE", sport="Ice Hockey",
         detail="Anaheim at Philadelphia was scheduled for 17:00Z, before the 17:45Z selection cut-off, so it is shown as a fixture but carries no pick.",
         source="https://api-web.nhle.com/v1/score/2026-10-24", needs="Nothing; recorded for completeness."),
    dict(code="NO-OLBG-LISTING", sport="Ice Hockey",
         detail="Buffalo at Washington was confirmed by the NHL feed but no OLBG event id for it appeared on the Ice Hockey hub page read, so a bet could not be placed on it from the listing we captured.",
         source=f"{OLBG}/Ice_Hockey/13", needs="The OLBG listing to appear on a later page of the hub."),
    dict(code="REQUIREMENT-CONFLICT", sport=None,
         detail="\"High confidence means 70% or better\" and \"the price must sit between -250 and +10000\" can only both hold between 70.00% and 71.43%, because -250 is 71.43%. The New Jersey pick is a 73.6% (-279) call and is therefore published as high confidence but marked outside the band rather than repriced to fit.",
         source="https://www.olbg.com/betting-tips", needs="A decision on which rule wins."),
    dict(code="OLBG-DISPLAY-TIME", sport="Ice Hockey",
         detail="OLBG's displayed times for NHL games are US Eastern clock times plus about seven minutes (for example \"Today 19:07\" for a 23:00Z start). They are stored verbatim and never used as kick-off times.",
         source=f"{OLBG}/Ice_Hockey/13", needs="Nothing; recorded so the column is not misread."),
    dict(code="INVENTORY-DEPTH", sport=None,
         detail="96 listing rows were read from the first page of each of the 15 sport hubs. Each hub is paginated with a \"Load More Tips\" control, so this is not a complete OLBG inventory.",
         source=f"{OLBG}", needs="Paged reads of every hub to complete the inventory."),
]

payload = json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))
listings = payload["listings"]
by_sport = {}
for row in listings:
    by_sport.setdefault(row["sport"], 0)
    by_sport[row["sport"]] += 1

sports = []
fixtures = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["picks"]
preds = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]
for sport in payload["hubs"]:
    confirmed = sum(1 for x in payload["fixtures"] if x["sport"] == sport)
    got_pick = sum(1 for x in fixtures if x["sport"] == sport)
    note = payload["sport_status"].get(sport, {}).get("note", "")
    if not note:
        if confirmed and got_pick:
            note = "Fixtures and picks for this sport come from the official league feed linked on each row."
        elif confirmed and not got_pick:
            note = "Fixtures were confirmed, but every one of them had started before the selection cut-off, so no pick is published."
        else:
            note = ("No officially confirmed fixture in this capture: the official source for this sport was blocked or was "
                    "not reached in the capture window. See the review items for this sport.")
    sports.append(dict(
        sport=sport, hub_url=payload["hubs"][sport]["url"], sport_id=payload["hubs"][sport]["sport_id"],
        listings=by_sport.get(sport, 0),
        fixtures=sum(1 for f in payload["fixtures"] if f["sport"] == sport),
        picks=sum(1 for p in fixtures if p["sport"] == sport),
        previews=sum(1 for p in preds if p["sport"] == sport),
        status=note,
    ))

(DATA / "sources.json").write_text(json.dumps(dict(
    captured_utc=payload["capture_end_utc"],
    sources=[dict(label=l, url=u, read=r, outcome=o) for l, u, r, o in SOURCES],
    count=len(SOURCES),
), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

(DATA / "flagged.json").write_text(json.dumps(dict(
    as_of_utc=payload["capture_end_utc"], count=len(FLAGS), items=FLAGS, sports=sports,
), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"today_flags: {len(SOURCES)} sources, {len(FLAGS)} review items, {len(sports)} sport rows")
