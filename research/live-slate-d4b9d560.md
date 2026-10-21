# Live slate capture and verification - session `arena/d4b9d560-olbg2`

Captured 2026-10-21 between 07:05Z and 07:55Z. Sandbox `bash` has no external egress
(`curl https://api-web.nhle.com/...` returns `000`), so every value was read with the
agent's page-fetch tool from an official URL and written to `data/live/` with that URL
attached. Nothing below comes from memory or a secondary outlet.

## Sources read this session

| Source (official) | Returned | Used for |
|---|---|---|
| https://stats.unitedrugby.com/match-centre/2026-27/5 | 8 Round 5 fixtures (ids 292616-292623), venues, local kick-off times, broadcasters, per-match URLs; Round 3 results panel | `data/live/urc.json` fixtures + margin/total spreads |
| https://stats.unitedrugby.com/match-centre/table/2026-27 | 16-club table: P/W/D/L, BP, PF, PA, diff, TF/TA, form | `data/live/urc.json` table (line-model inputs) |
| https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-10-26&hydrate=team | 3 World Series games (849805, 849802, 849804), venues, UTC/local dates, `gameType: W` | `data/live/mlb.json` fixtures |
| https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason | Rays 98-64, 736 RS / 650 RA, AL East rank 1 | `data/live/mlb.json` inputs |
| https://statsapi.mlb.com/api/v1/standings?leagueId=104&season=2026&... | Brewers named explicitly: 103-59, 832 RS / 618 RA | `data/live/mlb.json` inputs |
| https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-21 | `totalGames: 0` | Evidence that there is no MLB fixture on 21 or 22 Oct |
| https://api-web.nhle.com/v1/score/2026-10-21 | PHI at BUF (2026020152), FLA at OTT (2026020153), 23:30Z, records, venues, team leaders | Cross-check of the root layer |
| https://api-web.nhle.com/v1/score/2026-10-22 | 2026020154 NSH at BOS, 2026020155 NYR at TOR, 2026020156 SJS at OTT, 2026020157 ANA at NJD, venues and start times | Cross-check of the root layer |
| https://api-web.nhle.com/v1/schedule/2026-10-22 | `numberOfGames: 12`; ids, venues, `startTimeUTC` | Cross-check |
| https://api.nhle.com/stats/rest/en/team/summary?...seasonId 20262027 | 30 of 32 clubs' GP/W/L/OTL/GF/GA | Freshness comparison -> flag L01 |
| https://api-web.nhle.com/v1/standings/now | CAR 11GP 8-2-1 42/27, VGK 11GP 8-3-0 44/30, EDM, BOS | Freshness comparison + flag L10 |
| https://www.nba.com/games?date=2026-10-22 | Month calendar (11/2/12/8/7 games for 21-25 Oct); fixture list failed to render | Flag L02 |
| https://www.atptour.com/en/scores/current | In-play and finished matches, serve-speed leaderboard; no upcoming fixture list | Flag L03 |

Sources attempted and **rejected** (recorded so the next session does not repeat them):
`https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json` (HTTP 500),
`https://stats.nba.com/stats/scoreboardv2?...` (unreachable),
`https://cricketapi-icc.pulselive.com/cricket/match/live` (unreachable),
`https://www.icc-cricket.com/en/matches` (404), `https://www.urc.rugby/matches` (unreachable),
`https://www.epcrugby.com/match-centre/` (404),
`https://www.eurohandball.com/en/competition(s)/mach-o-ehf-champions-league/` (404).

## Verification performed line by line

* Every one of the 11 published fixtures carries the official URL it was read from; the
  build fails if any row lacks one (`scripts/live_build.py` raises `SystemExit`).
* The 8 URC fixtures were checked against the per-match URLs on the match-centre page and
  against the 16-club table: all 16 clubs appearing in Round 5 exist in the table.
* The 3 MLB fixtures were checked against the standings capture: both finalists appear with
  the records used by the model, and the Brewers' name is read explicitly rather than
  inferred from division position.
* NHL fixture ids 2026020152-2026020157, matchups, venues and start times returned by the
  official feeds match the root dashboard's `data/matches.json` exactly, so that layer's
  fixtures are independently confirmed. Its team **inputs** are not (flag L01).

## Irregularities found

L01 - stale NHL inputs (4 clubs), L02 - NBA fixtures unretrievable, L03 - tennis fixtures
unretrievable, L04 - cricket sources down, L05 - handball 404, L06 - ten sports not
captured, L07 - no home-advantage term in the World Series model, L08 - rugby spreads from
8 matches, L09 - URC times are local, L10 - second confirmation of the shootout-goal
convention split (prior F19), L11 - the brief's "full list for every sport" is not met.
Full text and source links: `data/live/flags.json`, published at `live/flagged.html`.

## Reproduce

```
python3 scripts/live_model.py     # data/live/lines.json
python3 scripts/live_build.py     # live/** + link check
python3 -m unittest discover -s tests -q
```
