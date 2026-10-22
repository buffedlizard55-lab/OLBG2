# Forward Slate Capture — 2026-10-23 → 2026-11-02 (session arena/6a87eefa-olbg2)

Captured live on **2026-10-22** (all figures from official league endpoints; no
bookmaker odds or tipster material used anywhere). This file is the G2 research
log for the forward-window slate; the machine-readable capture lives in
`data/forward/capture_*.json(l)`, normalised inputs in `data/forward/inputs.json`.

## Sources read (fetch_page; bash egress is GitHub-only)

| Source | What it gave |
| --- | --- |
| `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-11-02` | All 7 World Series games (Rays @ Brewers 2-3-2), gamePks, venues, if-necessary flags → `capture_mlb.jsonl` |
| `https://statsapi.mlb.com/api/v1/schedule?teamId=158|139&startDate=2026-10-01&endDate=2026-10-22&fields=…` | Both clubs' full postseason paths: TB ALDS 3-0 NYY + ALCS 4-2 CLE; MIL NLDS 3-1 SD + NLCS 4-0 LAD |
| `https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&fields=…` + per-game `leagueRecord` | TB 98-64 (55-26 home, 43-38 away); MIL 103-59 (finale 2026-09-27) |
| `https://statsapi.mlb.com/api/v1/teams/{139,158}/stats?stats=season&group={hitting,pitching}&fields=stats,splits,stat,runs` | TB 736 RS / 650 RA; MIL 832 RS / 618 RA (each verified directly) |
| `https://statsapi.mlb.com/api/v1/teams/{139,158}/leaders?leaderCategories=homeRuns,battingAverage,earnedRunAverage&season=2026` | TB: Caminero 42 HR, Simpson .306, Rasmussen 2.67 ERA; MIL: Bauers 26 HR, Chourio .291/25 HR, Misiorowski 1.80 ERA |
| `https://api-web.nhle.com/v1/score/{date}` for 2026-10-23 … 2026-11-02 | The complete NHL game-week card: **70 fixtures** (game ids 2026020166–2026020235), with venue, `startTimeUTC`, per-game records, `gameCenterLink`, and per-game team leaders (goals/assists/wins) → `capture_nhl.jsonl`, `capture_nhl_leaders.jsonl` |
| `https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027 and gameTypeId=2` | All 32 clubs' GP/W/L/OTL + GF/GA (league model inputs) → `capture_nhl_teams.jsonl` |
| `https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/games` (full-season feed; round filter ignored) | **All 16 EuroCup Round 5 fixtures** (27–28 Oct, 4 groups × 8 teams) recovered from chunks 11–12 → `capture_eurocup_r5.jsonl` |
| `https://www.nba.com/games` | Server-rendered month calendar: official per-day NBA game counts (22 Oct: 2, 23: 12, 24: 8, 25: 7, 26: 9, 27: 4, 28: 12, 29: 3, 30: 10, 31: 7) → `capture_nba_slate.json` |

## Named gap closures (task-board items)

- **VF-15 (World Series Games 4–7 missing): CLOSED in this layer.** All seven
  games are originated in `data/forward/matches.json`, including
  `mlb-ws-g4` (2026-10-27, Tropicana Field, Brewers @ Rays) — the game the
  verified layer never lined. Games 5–7 carry the official if-necessary flag in
  their competition string.
- **VF-20 (EuroCup Round 5 card missing): CLOSED for the card.** All sixteen R5
  fixtures are captured from the official EuroLeague live API and published.
  They ship **unlined**: the same API's v1 and v2 `standings` endpoints return
  empty bodies and this desk never infers team strength, so no markets are
  fabricated.
- **VF-14 (NBA 22–24 Oct fixtures): PARTIAL.** The CDN schedule JSON endpoints
  return HTTP 500 and future-date game lists still fail to server-render
  ("Sorry, something went wrong" on `?date=2026-10-23`; `/schedule` renders only
  the client-side shell). The rendered month calendar does give official
  per-day game **counts** (captured above), but matchup-level rows cannot be
  verified, so no NBA rows are published — never inferred. Flag remains open.
- **VF-22 (GBGB cards): STILL BLOCKED.** `gbgb.org.uk`, `/racing/results/` and
  `/racing/race-cards/` all returned fetch failures or HTTP 500 on 2026-10-22.
  No greyhound rows published (a card capture would also lack the trap ratings
  this desk requires before lining). Flag remains open.

Attempt-by-attempt logs: `data/forward/capture_gap_notes.json`.

## Slate produced

- 93 rows: 70 NHL (originated), 7 MLB World Series (originated), 16 EuroCup R5
  (unlined with explicit blank reasons).
- 8 in-band high-confidence picks (model probability ≥ 0.70 AND fair American
  inside −250..+10000), each with a bespoke ≥30-word write-up naming the team, a
  player, current form and the explicit selection: SJS @ BOS (24 Oct),
  MIN @ UTA, BUF @ SJS (27 Oct), TOR @ SEA (28 Oct), WSH @ NSH (29 Oct),
  CHI @ BOS, PIT @ MTL (31 Oct), COL @ CHI (2 Nov).
- Model: shrunk-Poisson goal origination identical in method to the verified
  desk (k=8 toward league GF/game, 5% home-ice factor, Poisson grid for
  winner/handicap/total), plus alternate-line repricing so chalky favourites
  can be taken at in-band prices instead of being discarded.

## Pipeline

`scripts/forward_seed.py` → `data/forward/inputs.json` →
`scripts/forward_model.py` → `data/forward/{matches,predictions,flagged}.json` →
`scripts/forward_build.py` → `forward/{index,matches,picks,gaps}.html`.
Tests: `tests/test_forward.py` (determinism, market integrity, the uniform
high-confidence gate, prediction language rules, gap-flag coverage).
