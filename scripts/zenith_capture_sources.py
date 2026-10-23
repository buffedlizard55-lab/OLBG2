#!/usr/bin/env python3
"""Carry forward source metadata and log this session's direct official-site rereads."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'zenith'

def main():
    base=json.loads((ROOT/'data/cadence/sources.json').read_text())
    # Explicit manual reads performed in this session through the agent web/fetch tools.
    # These are URLs and field-level notes, not claims that a raw HTTP archive is stored.
    checked=[
      ('NHL schedule','https://api-web.nhle.com/v1/schedule/2026-10-23','Two listed Oct 23 games and startTimeUTC/gameState fields; also 12 Oct 24 games. NHL official API.'),
      ('NHL standings','https://api-web.nhle.com/v1/standings/2026-10-23','Team games-played, W/L/OTL, goals-for/against, home/road splits and streaks.'),
      ('NBA schedule','https://www.nba.com/schedule?date=2026-10-23','Official 12-game Oct 23 slate, pairings, arena and ET tip-time labels.'),
      ('NBA standings','https://www.nba.com/standings','Official 2026-27 opening-week standings, W-L and last-ten fields.'),
      ('NBA injury report','https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_05_15PM.pdf','Official report read; row alignment in parsed content is not wholly dependable, so individual injury claims withheld unless visibly unambiguous.'),
      ('MLB World Series schedule','https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-31&hydrate=team,probablePitcher,decisions,linescore','World Series games and scheduled starters; response exposed a live-linescore/Preview-state inconsistency, flagged.'),
      ('MLB pitching stats','https://statsapi.mlb.com/api/v1/people?personIds=607259,694819,656876,701656&hydrate=stats(group=[pitching],type=[season],season=2026)','2026 pitcher season statistics for official player ids.'),
      ('MLB standings','https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason','Official regular-season team standings and splits.'),
      ('WST matches','https://www.wst.tv/matches/','Northern Ireland Open completed and scheduled rounds, including Oct 24 semifinal schedule.'),
      ('WST rankings','https://www.wst.tv/rankings/','Rendered official Johnstone’s Paint rankings and one-year/centuries tables; older repo report claiming unavailable is stale.'),
      ('PDC day-two','https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest','Official draw schedule for Friday Oct 23 R1, after Luke Humphries withdrawal.'),
      ('PDC withdrawal','https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship','Official illness/withdrawal confirmation; Kim Huybrechts replacement.'),
      ('DP World Tour event','https://www.europeantour.com/dpworld-tour/genesis-championship-2026/','Official event dates, venue and live championship facts; accessed through official search result/page.'),
      ('PGA Tour leaderboard','https://www.pgatour.com/leaderboard','Official Butterfield Bermuda Championship live leaderboard, field, scores and quoted tournament odds.'),
      ('GAA fixture calendar','https://munster.gaa.ie/fixtures/events-calendar/','Official Munster GAA double-header and Cork final dates/times/venue.'),
      ('GBGB category-one schedule','https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/','Official schedule lists Oct 24 2026 Dunstall Park Scurry Gold Cup and Oaks; URL path retains 2025 label, flagged.'),
      ('ATP Almaty results','https://www.atptour.com/en/scores/current/almaty/9410/results','Official live ATP results page; October 24 quarter-final results were already present at reread time.'),
      ('ATP Medvedev report','https://www.atptour.com/en/news/medvedev-almaty-2026-report-friday','Official report confirms Friday semi-finalist progression, meaning earlier Saturday semifinals in source snapshot are stale/completed.'),
      ('WTA Ningbo semis','https://www.wtatennis.com/news/4597893/ningbo-semifinals-preview-leylah-fernandez-vs-marie-bouzkova-diana-shnaider-vs-elena-rybakina','Official semifinal preview and form/H2H/stats.'),
      ('Prem Rugby match centre','https://premrugby.com/match-centre/294925/news','Official Leicester Tigers–Northampton Saints fixture pairing and date.'),
      ('URC lineups','https://www.unitedrugby.com/latest/news/round-4-team-announcements/','Official Oct 23–24 team announcements and lineups for URC Round 4.'),
      ('LegaVolley SuperLega weekend','https://www.legavolley.it/2026/credem-banca-superleague-weekends-games-45/?lang=en','Official Oct 25 SuperLega fixtures and Round 1 numeric results/standings.'),
      ('EHF standings/schedule','https://ehfcl.eurohandball.com/men/2026-27/standings/','Official EHF group standings and calendar; specific EHF dates may differ from OLBG event time.'),
      ('NRL RLWC draw','https://www.nrl.com/draw/?competition=131&round=2&season=2026','Official 2026 RLWC Round 2/3 pairings, date, venue, standings places and team lists.'),
    ]
    payload={"generated_utc":"2026-10-23T22:27:00Z","session":"arena/110cf432-olbg2","capture_scope":"Official source URLs directly reread through agent fetch/search tools during this session; no raw HTTP bodies are claimed in this file.","prior_same_day_source_capture":{"captured_utc":base.get('captured_utc'),"session":base.get('session'),"count":base.get('count'),"sources":base.get('sources',[])},"current_session_reads":[{"key":k,"url":u,"what_was_checked":w,"verification":"read in session; see limitations on the desk"} for k,u,w in checked]}
    (OUT/'captures').mkdir(parents=True,exist_ok=True)
    (OUT/'captures'/'source_read_log.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
    print(f"zenith_capture_sources: preserved {len(base.get('sources',[]))} same-day source records and logged {len(checked)} session reads")
if __name__=='__main__':main()
