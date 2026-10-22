# Relay layer — session `arena/103d996c-olbg2` (2026-10-22)

## 1. Why this layer exists

The two integration sessions that followed the completed `/current/` layer (PRs #123, #124)
could not reach official sports endpoints from their sandboxes and therefore published no new
sporting facts. This session's environment differs: the agent **web-fetch tool** reaches the
public internet (the sandbox shell itself does not — `curl` to `api.nhle.com` exits 35 through
the egress proxy). That made a new first-hand capture possible, which is what `/relay/` is.

## 2. What was read first-hand this session (evidence class A)

| UTC | Endpoint | Result |
|---|---|---|
| 20:56 | `https://api-web.nhle.com/v1/score/2026-10-23` | Both 23 Oct fixtures with records and team leaders (`data/relay/capture/nhl_score_2026-10-23.json`) |
| 20:57 | `https://api-web.nhle.com/v1/score/2026-10-24` (chunk 0-1 of 5) | 5 of the twelve-game 24 Oct slate (`data/relay/capture/nhl_score_2026-10-24.json`) |
| 20:56 | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-24` | World Series Games 1-2: Rays @ Brewers, American Family Field, gamePks 849805/849802 (`data/relay/capture/mlb_world_series_2026-10-22.json`) |
| 20:58 | `https://www.atptour.com/en/scores/current` (chunk 0 of 3) | 22 Oct Round-of-16 results, Vienna/Brussels/Lyon (Medvedev d. Shimabukuro 6-2 6-1; Bublik w/o v Marozsan; Lehecka d. Collignon 6-4 6-2; Michelsen d. Goffin 6-3 6-4; Cobolli d. Wawrinka 6-2 6-4; Fritz d. Herbert 6-2 7-5) |
| 21:01 | `https://www.pdc.tv/tournaments/` | 2026 European Championship live banner; tournament hub 10870; Premier/ProTour/World Series event list |
| 21:02 | `https://www.icc-cricket.com/en/matches` | HTTP 404 |
| 21:16 | `https://www.wst.tv/matches/` (chunk 0 of 4) | NI Open completed Round 1/2 results (Wang Xinbo d. Si Jiahui 4-2; Craigie d. Xiao Guodong 4-3; McGill d. Maguire 4-1; Un-Nooh d. Hill 4-2; Lisowski d. Huang Jiahao 4-1; Heathcote d. Selby 4-2; Selt d. Vafaei 4-3; Baranowski d. Gary Wilson 4-3; O'Connor d. Stevens 4-1; Xu Si d. Carter 4-0; Walden d. Robertson 4-1; Davies d. Murphy 4-2; Slessor d. He Guoqiang 4-0; Jones d. Wakelin 4-1; Pang Junxu d. Burden 4-2; Wells d. Hawkins 4-2; Donaldson d. Wu Yize 4-0; Brecel d. Lei Peifan 4-1; Gilbert d. Sykes 4-1) |

Search-index quotes of official pages (evidence class C, disclosure only — never priced):
`mlb.com/rays/roster/probable-pitchers` and `mlb.com/brewers/roster/probable-pitchers`
(Jacob Misiorowski named for Milwaukee, Tampa Bay TBD at capture), and Wikipedia/press schedule
summaries used only to cross-check the NI Open round structure (QF 23 Oct, best of 11).

## 3. Fetch-tool outage (the session's main constraint)

The fetch tool routes through a caching proxy that failed intermittently all session with
`SignatureDoesNotMatch` errors (~half of all calls, and nearly every request for a later chunk
of an already-fetched page). Endpoints that never returned through it:

- `api.nhle.com` (stats REST — the 32-club team summary), 5 attempts
- `stats.nba.com`, and `cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json` (HTTP 500)
- `icc-cricket.com/match-list`
- later chunks of `wst.tv/matches/`, `atptour.com/en/scores/current`, `pdc.tv/tournament-hub/10870`

Consequences, each published as a flag rather than papered over: 29 of 38 fixture rows carry
over verbatim from the `/current/` session's captures of the same day (class B); ten sports
publish zero rows with first-hand or carried reasons; NBA remains absent (basketball is
EuroLeague-only).

## 4. Fixture list (38 rows, window 23-29 Oct)

Ice Hockey 14 (NHL 23-24 Oct slates), Handball 10 (EHF CL 28-29 Oct), Rugby Union 8 (URC
Round 4), Basketball 3 (EuroLeague Round 7, 23 Oct), Baseball 2 (World Series G1-G2),
Motor Racing 1 (US GP, race day derived — flag RL-13).

In-play/finished fixtures were excluded: EHF 22 Oct games, EuroLeague 22 Oct games, snooker
Round 3 (22 Oct), Genesis Championship (in play).

## 5. Model and gate

Identical mathematics to `/current/` (attack/defence ratings with shrinkage; Poisson grids for
hockey/handball/baseball, normal margin/total for basketball/rugby; ties split for OT sports;
F1 outright as points share). The shared implementation is imported from
`scripts/current_model.py`. Gate: p ≥ 0.7000 AND fair American inside −250…+10000, searched
over every originated market and both sides. 1310 prices, 113 markets, 20 in-band picks,
20 hand-authored predictions (Rugby Union 6, Handball 6, Ice Hockey 5, Basketball 3; baseball
and F1 have none by arithmetic — flags RL-06/RL-07).

## 6. Five-picks-per-sport scorecard

| Sport | In-band picks | Quota |
|---|---|---|
| Rugby Union | 6 | met |
| Handball | 6 | met |
| Ice Hockey | 5 | met |
| Basketball | 3 | not met — only 3 upcoming fixtures; NBA unreadable (RL-05) |
| Baseball | 0 | not met — 2 near-level World Series games (RL-06) |
| Motor Racing | 0 | not met — points-share outrights cannot reach 70% (RL-07) |
| other 11 sports | — | zero rows, reasons on each sport page (RL-08…RL-12) |

## 7. Verification performed

- `tests/test_relay_103d996c.py` — 32 tests: standing-table arithmetic (NHL 32, URC 16, EL 20,
  EHF 24 with for-equals-against, MLB), capture agreement between the fresh and carried World
  Series captures, independent recomputation of BOS v SJS (Over 4.5, p to 3 dp) and Leinster v
  Munster (moneyline, p to 3 dp) from the raw captures, band-gate re-check over all 1310
  prices, price/probability consistency, half-point lines, prediction length/uniqueness/number
  checks, byte-identical rebuild, every local link and anchor, exact subpage chrome hrefs at
  depth 1, thead/tbody cell counts, official https-only links, no bookmaker domains.
- Full repository suite: 375 tests OK. `scripts/integration_audit.py`: 0 local link errors.

## 8. Irregularities

See `relay/flagged.html` — flags RL-01…RL-17, each with the affected rows named. The material
ones: RL-01 (proxy outage; class-B reliance), RL-02 (NHL GF/GA snapshot 21 Oct), RL-03 (EHF
tables predate tonight's round), RL-04 (three NHL games dated 25 Oct inside the 24 Oct slate),
RL-14 (no official Rays Game 1 starter; Misiorowski official for Milwaukee).
