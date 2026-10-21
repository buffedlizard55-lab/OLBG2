# Collection log (raw provenance)

Every fetch used to build this dataset, with the UTC capture window, the URL and what was taken from it.
Nothing enters `data/` without a line here. All captures fall inside 2026-10-21 05:10–05:45 UTC.

| # | URL | What was taken | Outcome |
|---|-----|----------------|---------|
| 1 | https://www.olbg.com/betting-tips | Global tips page; sport taxonomy in hrefs | Cached/stale football fixtures present — not used for data |
| 2 | https://www.olbg.com/sitemap-betting-tips.xml | Sport names + numeric ids | OK (23 sports) |
| 3 | https://www.olbg.com/sitemap.xml | Sitemap index | OK |
| 4 | https://www.olbg.com/betting-tips/Basketball/NBA/NBA/4 | NBA event list, markets, event_ids | OK (7 of 11 official games listed) |
| 5 | https://www.olbg.com/betting-tips/Ice_Hockey/13 | NHL + European hockey events | OK |
| 6 | https://www.olbg.com/betting-tips/Tennis/3 | Tennis events | OK (tournament not labelled) |
| 7 | https://www.olbg.com/betting-tips/Cricket/7 | Cricket events | OK |
| 8 | https://www.olbg.com/betting-tips/Rugby_Union/9 | URC / Top 14 / Pro D2 events | OK |
| 9 | https://www.olbg.com/betting-tips/Darts/15 | PDC match list | OK |
| 10 | https://www.olbg.com/betting-tips/Snooker/8 | Northern Ireland Open matches | OK |
| 11 | https://www.olbg.com/betting-tips/Gaelic_Football/25 | Club fixtures | OK |
| 12 | https://www.nba.com/games?date=2026-10-21 | 11 fixtures, ET tip times, game ids | OK |
| 13 | https://www.nba.com/standings | 2026-27 records (season opening) | OK |
| 14 | https://www.nba.com/standings?Season=2025-26 | Full 2025-26 W-L, home/road splits (30 teams) | OK |
| 15 | https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json | Attempted live scoreboard | HTTP 500 — abandoned |
| 16 | https://stats.nba.com/stats/leaguestandingsv3?... | Attempted standings API | Blocked — abandoned |
| 17 | https://api-web.nhle.com/v1/schedule/2026-10-21 | NHL schedule 21 Oct (2 games) | OK |
| 18 | https://api-web.nhle.com/v1/standings/2026-10-20 | NHL standings snapshot (verbose) | OK but superseded by #20 |
| 19 | https://api-web.nhle.com/v1/score/2026-10-21 | 2 games, UTC starts, venues, team leaders | OK |
| 20 | https://api.nhle.com/stats/rest/en/team/summary (3 pages) | All 32 teams: GP, W-L-OTL, GF, GA, GF/GP, GA/GP | OK (Sharks GF/GA truncated) |
| 21 | https://api-web.nhle.com/v1/score/2026-10-22 (4 pages) | 11 of 12 games, UTC starts, venues, leaders | Partial — 12th game truncated |
| 22 | https://api-web.nhle.com/v1/schedule/2026-10-22 | Cross-check of 22 Oct fixtures | OK |
| 23 | https://api-web.nhle.com/v1/scoreboard/2026-10-22 | Recent results (e.g. COL 2 @ PHI 3, 19 Oct) | OK |
| 24 | https://stats.unitedrugby.com/match-centre/2026-27/4 | All 8 Round 4 fixtures, venues, local times | OK |
| 25 | https://www.unitedrugby.com/match-centre (2 pages) | Fixture confirmation + Saturday 24 Oct list | OK |
| 26 | https://stats.unitedrugby.com/match-centre/table/2026-27 | 16-team table: P, W, D, L, PF, PA, PTS, form | OK |
| 27 | https://www.unitedrugby.com/standings | Attempted standings page | 404 — used #26 instead |
| 28 | https://www.icc-cricket.com/rankings/team-rankings/mens/odi | ICC fixture list (AFG v BAN ODI, NZ v IND T20I) | OK for fixtures; ranking table rendered empty |
| 29 | https://www.wst.tv/matches/ (2 pages) | Northern Ireland Open draw, R1 results, R2 schedule | OK |
| 30 | https://www.wst.tv/rankings/ | World rankings top 11 + One Year List | Partial (top 11 only) |
| 31 | https://www.atptour.com/en/rankings/singles | Attempted ATP rankings | Client-side table, no data captured |
| 32 | https://www.pdc.tv/rankings | Attempted PDC Order of Merit | Cookie consent shell only |
| 33 | https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-21 | MLB schedule | OK — 0 games (rest day) |

## Derived files

| File | Built from | Notes |
|------|------------|-------|
| `data/inputs/nhl_teams.json` | #20 | 31 of 32 teams complete; SJS goals blank |
| `data/inputs/nba_teams.json` | #14 | 30 teams, prior season, used as a prior |
| `data/inputs/urc.json` | #24, #26 | Table + Round 4 fixtures + Round 3 results |
| `data/inputs/fixtures.json` | #12, #19, #21, #28 | Fixtures with official source URLs |
| `data/matches.json` | `scripts/model.py` | 33 fixtures, 30 originated lines |
| `data/predictions.json` | model output + #19/#20/#21 | 4 high-confidence write-ups, all facts sourced |
| `data/flagged.json` | review pass | 18 items |
| `data/sources.json` | all of the above | 24 registered sources |

## Time discrepancy note

OLBG's displayed start times could not be reconciled to a single timezone (NBA rows sit ~10 minutes after the
official ET tip time; NHL rows sit ~7 minutes after the equivalent UK time). Official league times are used in
`start_utc`; OLBG strings are preserved in the research notes only. See flagged item F12.
