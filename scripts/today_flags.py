#!/usr/bin/env python3
"""Build the source register, per-sport status and transparent review queue."""
from __future__ import annotations

import json
from pathlib import Path

from today_official_data import NBA_GAMES, NBA_INJURY, NBA_PRIOR, NBA_STATS, NHLE_TEAM
from today_motor_data import F1_EVENT, F1_TIMETABLE, F1_STANDINGS, F1_RACES, F1_FP2
from today_darts_data import (
    PDC_HUB, PDC_EVENT, PDC_RANKINGS, PDC_DAY1, PDC_FRIDAY, PDC_DAY3,
    PDC_PREVIEW, ESPN_RESULTS, INDEPENDENT_QF,
)
from today_extra_data import (
    ATP_SCHEDULE, ATP_H2H, ATP_FINAL_REPORT, WTA_NINGBO, WTA_NINGBO_EVENT,
    WTA_ASIAN_SCHEDULE, WTA_OSAKA_DRAW, WTA_SINIAKOVA_SF, WTA_RYBAKINA,
    WTA_FERNANDEZ, WTA_KRUEGER, LEGA_CAL, LEGA_TABLE, LNH_CAL, LNH_TABLE,
    HBL_SCHEDULE, HBL_TABLE, HBL_PREVIEW,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
OLBG = "https://www.olbg.com/betting-tips"
NHLE_SCORE = "https://api-web.nhle.com/v1/score/2026-10-24"
NHLE_SCHED = "https://api-web.nhle.com/v1/schedule/2026-10-24"
MLB_SCHED = ("https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24"
             "&hydrate=probablePitcher,team")
MLB_MIL = "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings&season=2026"
MLB_STAND = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
ATP = "https://www.atptour.com/en/scores/current"
WTA = "https://www.wtatennis.com/scores"

SOURCES = [
    ("NHL scores feed, 2026-10-24", NHLE_SCORE,
     "Read in full: all 12 games, UTC starts, records, venues, team leaders and the league odds array.", "used"),
    ("NHL schedule feed, 2026-10-24", NHLE_SCHED,
     "Read for game states, startTimeUTC, venues and schedule confirmation.", "used"),
    ("NHL official team summary, 2026-27", NHLE_TEAM,
     "Read in full: 32 teams with games, wins, goals for/against, shots and special-teams rates. GF/GA inputs use this feed consistently.", "used"),
    ("MLB Stats API schedule, 2026-10-24", MLB_SCHED,
     "One game: Tampa Bay at Milwaukee at 2026-10-25T00:00:00Z; Drew Rasmussen and Logan Henderson listed as probable pitchers.", "used"),
    ("MLB Stats API team standings, Brewers", MLB_MIL,
     "Milwaukee 103-59, 832 runs scored, 618 allowed, 55-26 home, 8-2 last ten.", "used"),
    ("MLB Stats API league standings", MLB_STAND,
     "Tampa Bay 98-64, 736 scored, 650 allowed, 43-38 away, 5-5 last ten.", "partial"),
    ("NBA games page, 2026-10-24", NBA_GAMES,
     "Read: all eight games, official game IDs, UTC starts, current records and team leaders.", "used"),
    ("NBA current standings", "https://www.nba.com/standings",
     "Read: current 2026-27 records used alongside the completed-season prior.", "used"),
    ("NBA completed 2025-26 standings", NBA_PRIOR,
     "Read: 82-game records for all teams on today's schedule.", "used"),
    ("NBA traditional team statistics, 2026-27", NBA_STATS,
     "Read in full: games, records, points per game and average point differential. One- and two-game samples are shrunk, not described as established form.", "used"),
    ("NBA official injury report, 1:30 PM ET", NBA_INJURY,
     "Read in full. Official designations are attached to fixtures; NOT YET SUBMITTED remains pending and the ambiguous page-break row is excluded.", "used"),
    ("ATP current scores", ATP,
     "Read: semifinal results include Medvedev over Bublik and Basilashvili over Tsitsipas. A final start time was not established from the portion read.", "partial"),
    ("WTA scores", WTA,
     "Read: notifications and zero tournaments live; no usable upcoming-match schedule was returned.", "partial"),
    ("United Rugby Championship match centre", "https://www.unitedrugby.com/match-centre",
     "Read: Round 3 and Round 4 results with scores and venues; no upcoming fixture detail reached in the portion read.", "partial"),
    ("Handball-Bundesliga fixture page", "https://www.daikin-hbl.de/de/spielplan/",
     "HTTP 404; the site redirected to a not-found page.", "blocked"),
    ("World Snooker Tour match centre", "https://wst.tv/matches/",
     "Read: Wilson beat Craigie 6-5; Williams–Jones was live and the other finalist was not yet known, so no future final was priced.", "partial"),
    ("ATP Almaty daily schedule", ATP_SCHEDULE,
     "Read: Sunday singles final follows doubles and ceremonies, not before 15:00 local.", "used"),
    ("ATP official head-to-head", ATP_H2H,
     "Read: Medvedev 45-18 and rank 5, Basilashvili 7-10 and rank 128; Medvedev leads 1-0.", "used"),
    ("ATP Almaty semifinal report", ATP_FINAL_REPORT,
     "Read: 37 Medvedev hard-court wins, 10-1 Almaty record and Basilashvili's first tour final since Doha 2022.", "used"),
    ("WTA Ningbo tournament page", WTA_NINGBO_EVENT,
     "Read: the tournament runs 19-25 October and Day 7 is the final; used to resolve the preview's contradictory Saturday label.", "used"),
    ("WTA Ningbo final preview", WTA_NINGBO,
     "Read: not before 17:00 local/05:00 ET, Rybakina leads 3-2, both semifinals ended 6-3 7-5 and Fernandez is 11-2 in the Asian Swing. Its Saturday 24 October label conflicts with the tournament date.", "used"),
    ("WTA Asian Swing schedule", WTA_ASIAN_SCHEDULE,
     "Read: Osaka singles final on Sunday 25 October, not before 13:30 Japan time.", "used"),
    ("WTA Osaka main-draw PDF", WTA_OSAKA_DRAW,
     "Read in full: both finalists are 4-0; completed-set records exclude the unfinished third set in Siniakova's opening retirement win.", "used"),
    ("WTA Osaka semifinal report", WTA_SINIAKOVA_SF,
     "Read: Siniakova beat Boulter 6-1 6-4 to reach her first singles final since 2023.", "used"),
    ("WTA official player profiles", WTA_RYBAKINA,
     "Read with the linked Fernandez and Krueger profiles: current ranks, season records and titles used only where the profile supplied them.", "used"),
    ("WTA Fernandez player profile", WTA_FERNANDEZ,
     "Read: rank 30, 24-25 season record and one title.", "used"),
    ("WTA Krueger player profile", WTA_KRUEGER,
     "Read: current singles rank 55 and 2023 Osaka champion; conflicting search snippets for her season record were not used.", "partial"),
    ("Lega Volley official calendar", LEGA_CAL,
     "Read: six Sunday Serie A fixtures with local start times and venues.", "used"),
    ("Lega Volley official standings", LEGA_TABLE,
     "Read in full: one-round match, set and point records. These are treated as a tiny sample, not established form.", "used"),
    ("LNH official calendar", LNH_CAL,
     "Read: Saint-Raphaël–Paris at 16:00 and Montpellier–Saran at 17:00 local on Sunday.", "used"),
    ("LNH official standings", LNH_TABLE,
     "Read: seven-match W-L-D and goals records for Saint-Raphaël, Paris, Montpellier and Saran.", "used"),
    ("Opel HBL official homepage", HBL_SCHEDULE,
     "Read: three Sunday Bundesliga fixtures with local starts; official team pages supplied venues.", "used"),
    ("Opel HBL official standings", HBL_TABLE,
     "Officially indexed table rows supplied complete W-D-L and goals records for all six Sunday teams. The direct table route presented reCAPTCHA, which is disclosed rather than bypassed.", "partial"),
    ("Opel HBL matchday 10 preview", HBL_PREVIEW,
     "Read in full: Sunday recent results, scoring leaders and head-to-head records for Löwen–Magdeburg, Bergischer–Hamburg and Füchse–Wetzlar.", "used"),
    ("Formula 1 United States Grand Prix", F1_EVENT,
     "Read: weekend schedule, circuit detail and Practice 2 top five; structured event data gives 2026-10-25T20:00:00Z. Qualifying had not produced a grid.", "used"),
    ("Formula 1 official Austin timetable", F1_TIMETABLE,
     "Read: Sunday race 15:00-17:00 Austin over 56 laps or 120 minutes; the article states Austin is five hours behind UTC, reconciling to 20:00Z.", "used"),
    ("Formula 1 official driver standings", F1_STANDINGS,
     "Read in full: points for every current Practice 2 starter; Tsunoda has standings points but no current Practice 2 time and is excluded from this race field.", "used"),
    ("Formula 1 official race results", F1_RACES,
     "Read: 17 completed races and all winners; Antonelli eight, Russell three, Verstappen two, Norris two, Hamilton one and Leclerc one.", "used"),
    ("Formula 1 official Practice 2 results", F1_FP2,
     "Read in full: 22 current starters, all gaps and lap counts; Leclerc led in 1:35.291.", "used"),
    ("PDC European Championship Day Three", PDC_DAY3,
     "Read through official indexing: Saturday Round 2 order and best-of-19 format, including Aspinall–Littler and Clayton–Rock. The directly rendered route returned cookie-policy text before the article.", "used"),
    ("PDC Friday European Championship report", PDC_FRIDAY,
     "Read: Aspinall 6-3 Reyes, Littler 6-3 O'Connor, Clayton 6-3 Springer and Rock 6-1 Dobey; Littler averaged 105.05 and Rock won six straight legs.", "used"),
    ("PDC opening-night European Championship report", PDC_DAY1,
     "Read: Price beat Cross 6-2 with a 99.26 average and Bunting beat Noppert 6-5 after a 160 checkout.", "used"),
    ("PDC official world rankings", PDC_RANKINGS,
     "Read through official indexing: two-year ranking earnings for all six selected players; kept separate from current European Tour earnings.", "used"),
    ("PDC European Championship event page", PDC_EVENT,
     "Read through official indexing: current European Tour earnings for Aspinall, Littler, Clayton, Rock, Price and Bunting.", "used"),
    ("PDC European Championship tournament hub", PDC_HUB,
     "Read through official indexing for the event and bracket. Its exposed later-round index remained TBC, so it was not treated as confirmation of a completed result.", "partial"),
    ("PDC official Sunday schedule", PDC_PREVIEW,
     "Read: Sunday quarterfinal session begins 13:00 CET/12:00 GMT after the clock change; evening semifinals and final follow.", "used"),
    ("ESPN European Championship results", ESPN_RESULTS,
     "Trusted corroboration: Price 10-4 Menzies and Bunting 10-3 Huybrechts in Saturday Round 2. Used only for the Sunday fixture where the directly readable PDC report remained pre-match.", "used"),
    ("Independent Price–Bunting quarterfinal report", INDEPENDENT_QF,
     "Trusted corroboration: the two Saturday results created Sunday's Price–Bunting quarterfinal; Bunting fired four 100-plus checkouts.", "used"),
    ("PREM Rugby fixtures", "https://www.premrugby.com/fixtures-results?competition=gallagher-prem&round=4",
     "Read: current-round matches were full-time or live, so they were not promoted as upcoming selections.", "partial"),
]


def build():
    payload = json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))
    listings = payload["listings"]
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["picks"]
    preds = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]
    lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))["lines"]
    high_outside = [p for p in picks if p["confidence"] == "high" and not p["in_band"]]

    flags = [
        dict(code="NO-LISTING", sport="Golf",
             detail="The Golf hub returned 'No tips found.' OLBG listed no golf event to attach a pick to.",
             source=f"{OLBG}/Golf/5", needs="A golf event listed on OLBG."),
        dict(code="NO-MATCH-EVENTS", sport="Rugby League",
             detail="The hub listed only 2027 outright futures, not a Rugby League match event.",
             source=f"{OLBG}/Rugby_League/10", needs="A listed Rugby League match event."),
        dict(code="NO-OFFICIAL-FORM-SOURCE", sport="Greyhounds",
             detail="Nine race listings were captured, but no official racecard with per-dog form and trap data was read.",
             source="https://www.gbgb.org.uk/", needs="A reachable official racecard source."),
        dict(code="WTA-DATE-CONFLICT", sport="Tennis",
             detail="The WTA Ningbo final preview labels the start Saturday 24 October while also giving 17:00 local/05:00 ET; the official tournament page dates the final Sunday 25 October. The fixture uses Sunday and preserves the not-before time; the contradiction is not hidden.",
             source=WTA_NINGBO, needs="A corrected WTA article or order of play with an internally consistent day and date."),
        dict(code="TENNIS-QUOTA-AND-STARTS", sport="Tennis",
             detail="Three finals have comparable official evidence and OLBG rows, so only three picks qualify rather than five. All start labels are not-before times following doubles or ceremonies, not exact beginning times.",
             source=ATP_SCHEDULE, needs="Two more officially confirmed, OLBG-backed matches and final orders of play for exact starts."),
        dict(code="NOT-CONFIRMED", sport="Cricket",
             detail="Eleven cricket events were listed, but no governing-body fixture and form page was read for them.",
             source=f"{OLBG}/Cricket/7", needs="A board or ICC fixture page for each listed match."),
        dict(code="OFFICIAL-WITHOUT-OLBG", sport="Volleyball",
             detail="Piacenza–Modena and Milano–Cuneo are official Lega Volley fixtures but were absent from the captured OLBG board. Their research lines remain on the lines page without picks; the other four Italian fixtures supply four OLBG-backed selections, not a padded five.",
             source=LEGA_CAL, needs="Corresponding OLBG event rows before either official-only fixture can receive a pick; a fifth supported match for the target."),
        dict(code="PARTIAL-LEAGUE-COVERAGE", sport="Volleyball",
             detail="Italian fixtures now have official calendar and one-round standings support. Listings from other countries remain unpriced until their own league fixture and statistics pages are read.",
             source=f"{OLBG}/Volleyball/21", needs="Official sources for the remaining listed leagues."),
        dict(code="PARTIAL-LEAGUE-COVERAGE", sport="Handball",
             detail="Five Sunday fixtures across the LNH and HBL have official statistics and matching OLBG rows, meeting the five-pick target. The other captured handball listings remain unpriced until their own league or federation sources are read.",
             source=HBL_PREVIEW, needs="Official sources for ASOBAL, EHF, Swedish, Danish and international listings."),
        dict(code="HBL-TABLE-ACCESS", sport="Handball",
             detail="Complete current records for the six Sunday HBL teams came from officially indexed standings rows and the official matchday preview. The direct standings route presented reCAPTCHA; no challenge was bypassed and the official link remains available for manual review.",
             source=HBL_TABLE, needs="Nothing for these six teams; the access limitation is recorded for reviewers."),
        dict(code="QUOTA-SHORTFALL", sport="Darts",
             detail="Three current or upcoming PDC match listings have official schedule, ranking and tournament-leg support, producing three picks. The two outright listings are not matches, and the two Saturday evening matches already underway at the refreshed capture were removed rather than used to pad the target.",
             source=PDC_DAY3, needs="Two more supported, OLBG-backed match events for the five-match target."),
        dict(code="LISTED-MATCH-TIMES", sport="Darts",
             detail="PDC confirms the Saturday evening session and match order, while the exact 19:15Z and 20:15Z starts come from OLBG's display and are labelled as such. Sunday's 12:00Z value agrees with the official quarterfinal session start after the clock change.",
             source=PDC_DAY3, needs="Official per-match scheduled times if exact rather than session-level chronology is required."),
        dict(code="SUNDAY-RESULT-CORROBORATION", sport="Darts",
             detail="The official PDC bracket and Sunday session are linked, but its directly readable Saturday report and hub index still exposed pre-match/TBC content. ESPN and The Independent independently confirm Price 10-4 Menzies, Bunting 10-3 Huybrechts and the resulting Sunday quarterfinal. The pairing is not inferred from an unfinished bracket.",
             source=ESPN_RESULTS, needs="An updated PDC result report carrying the same afternoon scores for a single-source official audit."),
        dict(code="LIVE-OR-UNKNOWN-FINALIST", sport="Snooker",
             detail="Wilson beat Craigie 6-5, but Williams–Jones was live and the other finalist was unknown when read. No future final matchup or price is invented from a live bracket.",
             source="https://wst.tv/matches/", needs="A completed semifinal and an official final schedule."),
        dict(code="NOT-CONFIRMED", sport="Gaelic Sports",
             detail="Four club matches were listed, but no county-board fixture page was read.",
             source="https://www.gaa.ie/", needs="County-board fixture pages with throw-in times."),
        dict(code="NO-QUALIFYING-GRID", sport="Motor Racing",
             detail="Official timetable, 17 race results, season standings and all 22 Practice 2 starters support winner and podium prices. Qualifying had not produced a grid, so no starting-position advantage is used. One race supplies one pick, not a padded five.",
             source=F1_TIMETABLE, needs="The official qualifying result and grid before any grid-dependent claim; four more supported events for the five-event target."),
        dict(code="QUOTA-SHORTFALL", sport="Baseball",
             detail="One official baseball fixture exists. The five-per-sport target cannot be met from one scheduled game without inventing matches.",
             source=MLB_SCHED, needs="More officially scheduled games."),
        dict(code="STARTED-AT-CAPTURE", sport="Ice Hockey",
             detail="Anaheim at Philadelphia started at 17:00Z, before the 18:25Z selection cut-off. It remains in the match list without a pick; its live score is not used.",
             source=NHLE_SCORE, needs="Nothing; recorded for completeness."),
        dict(code="NBA-REPORT-PENDING", sport="Basketball",
             detail="The 1:30 PM ET report marked San Antonio, Dallas, Washington, New Orleans and Golden State NOT YET SUBMITTED. No availability claim is made for those teams.",
             source=NBA_INJURY, needs="A later official NBA injury report containing those teams."),
        dict(code="NBA-PDF-PAGEBREAK", sport="Basketball",
             detail="The Dean Wade row crosses a PDF page break with ambiguous team attribution. It is excluded from every preview and availability input.",
             source=NBA_INJURY, needs="A later report or cleanly aligned official row."),
        dict(code="NBA-VENUE-BLANK", sport="Basketball",
             detail="The official games-page portion used for the eight NBA fixtures did not supply arenas. Venue cells are blank rather than filled from team names or prior knowledge.",
             source=NBA_GAMES, needs="Official fixture pages with arena fields."),
        dict(code="NBA-SMALL-SAMPLE", sport="Basketball",
             detail="Current NBA scoring samples contain only one or two games per team. They receive ten league-average games of shrinkage and are not described as established scoring form.",
             source=NBA_STATS, needs="A larger current-season sample; the limitation remains explicit today."),
        dict(code="NHL-SHOOTOUT-COUNT", sport="Ice Hockey",
             detail="NHL standings and team-summary goal-against totals can differ because of shootout accounting. All scoring prices use the team-summary feed consistently instead of mixing conventions.",
             source=NHLE_TEAM, needs="Nothing; the convention is documented."),
        dict(code="OLBG-DISPLAY-TIME", sport="Ice Hockey",
             detail="OLBG displayed times are stored verbatim and never treated as UTC. Official league startTimeUTC controls the fixture chronology.",
             source=f"{OLBG}/Ice_Hockey/13", needs="Nothing; recorded so the column is not misread."),
        dict(code="INVENTORY-DEPTH", sport=None,
             detail=f"{len(listings)} listing rows are published across the 15 hubs. Hubs have a Load More Tips control, so this is not a complete inventory of every OLBG event.",
             source=OLBG, needs="Paged reads of every hub to complete the inventory."),
        dict(code="MARKET-COVERAGE", sport=None,
             detail=f"{len(lines)} prices cover moneylines plus NHL puck lines/totals, NBA spreads/totals, MLB run lines/totals, tennis and volleyball set markets, three-way handball result/handicap/total markets, darts match/leg-handicap/total-legs markets, and Formula 1 winner/podium markets. Official-only fixtures may be priced but are not picked without an OLBG row.",
             source=NHLE_TEAM, needs="Official inputs for the remaining sports; no blank is backfilled from OLBG consensus."),
    ]
    if high_outside:
        names = ", ".join(p["selection"] for p in high_outside)
        flags.append(dict(
            code="HIGH-OUTSIDE-BAND", sport=None,
            detail=f"High is 70% or better. −250 implies 71.43%, so the overlap is only 70.00–71.43%. {names} grade High but price outside the floor; their fair prices are unchanged.",
            source=OLBG, needs="No repricing; readers should use the band label alongside the grade."))

    by_sport = {}
    for row in listings:
        by_sport[row["sport"]] = by_sport.get(row["sport"], 0) + 1
    sports = []
    for sport in payload["hubs"]:
        confirmed = sum(1 for x in payload["fixtures"] if x["sport"] == sport)
        got_pick = sum(1 for x in picks if x["sport"] == sport)
        note = payload["sport_status"].get(sport, {}).get("note", "")
        if not note:
            if confirmed and got_pick:
                note = "Official fixtures, independent prices and written picks are linked on each row."
            elif confirmed:
                note = "Fixtures are confirmed, but none qualifies for the published five-pick card; see start times and review items."
            else:
                note = "No official fixture was confirmed in this capture. The reason and evidence link are in the review queue."
        sports.append(dict(
            sport=sport, hub_url=payload["hubs"][sport]["url"],
            sport_id=payload["hubs"][sport]["sport_id"], listings=by_sport.get(sport, 0),
            fixtures=confirmed, picks=got_pick,
            previews=sum(1 for p in preds if p["sport"] == sport), status=note,
        ))

    (DATA / "sources.json").write_text(json.dumps(dict(
        captured_utc=payload["capture_end_utc"],
        sources=[dict(label=l, url=u, read=r, outcome=o) for l, u, r, o in SOURCES],
        count=len(SOURCES)), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "flagged.json").write_text(json.dumps(dict(
        as_of_utc=payload["capture_end_utc"], count=len(flags), items=flags, sports=sports,
    ), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"today_flags: {len(SOURCES)} sources, {len(flags)} review items, {len(sports)} sport rows")


if __name__ == "__main__":
    build()
