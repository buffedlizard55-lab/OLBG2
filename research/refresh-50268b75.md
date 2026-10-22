# Verified Desk Refresh — Session 50268b75 (2026-10-22)

Scope: R1–R5 of the claim in `COORDINATION.md` — roll the `/verified/` desk from
the stale 2026-10-21 capture to a fresh 2026-10-22 official capture, retire all
completed 21-Oct fixtures, make the model read one self-contained inputs file,
add fair American prices, and re-cut the written predictions around a featured
band of **−250 to +10000 (American)**.

## Official captures used (all values transcribed into `scripts/verified_seed.py`)

| Competition | Endpoint | Captured |
|---|---|---|
| NHL fixtures + team rates | `api-web.nhle.com/v1/score/2026-10-22`, Stats REST `team/summary?seasonId=20262027&gameTypeId=2` | 12 fixtures, 32 teams |
| NBA fixtures | `nba.com/schedule?date=2026-10-22` | 2 games 22 Oct + 12 games 23 Oct (IDs, times, venues) |
| NBA strength priors | `data/inputs/nba_teams.json` (completed 2025-26, copied at seed time) | 30 teams |
| EuroLeague | `euroleaguebasketball.net/en/euroleague/standings/` | 20 teams, 9 live R7 fixtures |
| EHF Champions League | `ehfcl.eurohandball.com/men/2026-27/standings/` + matches | 24 clubs, 5 fixtures on 22 Oct |
| MLB World Series | `statsapi.mlb.com` schedule 2026-10-22–31 + standings | Games 1–4 (G5–G7 conditional, unpublished) |
| Top 14 / Pro D2 | `top14.lnr.fr/classement`, `prod2.lnr.fr/classement` | spot-checked unchanged, no intervening rounds |
| URC | copied at seed time from `data/inputs/urc.json` + `data/live/urc.json` | 16 teams, R4 + R5 fixtures |
| WST NI Open | `wst.tv` matches / match centre | 8 Round 3 ties (unlined, VF-04) |
| PDC rankings | `pdc.tv/rankings` — consent wall, no rows served | 21-Oct ladder retained (VF-13) |

## Decisions & irregularities

- **NHL goal convention.** Stats REST excludes shootout-deciding goals (the
  standings endpoint includes them); Stats REST is the model source, disclosed
  on the methodology page. Four clubs (PHI, BUF, FLA, OTT) had a game still
  live during capture on 21 Oct; their rows exclude that unfinished game.
  Florida/Ottawa play 22 Oct on one-game-stale inputs — flagged VF-11, not
  "corrected" from partial live scores.
- **NBA opening week.** No 2026-27 games played yet: 2025-26 records are the
  prior, confidence capped at medium, totals blank (nba.com standings publish
  no PF/PA), NBA excluded from featured written predictions.
- **Featured band.** Every match keeps a moneyline pick graded low/medium/high
  (≥0.72 / ≥0.60). The written predictions are now *featured* selections:
  probability ≥0.70 with fair American price in [−250, +10000]. Strong
  favourites whose moneyline prices shorter than −250 are repriced through
  alternate handicaps (Asian quarter lines on the continuous-margin sports)
  priced from the model's own distribution and gated on the same ≥0.70
  moneyline conviction — 14 featured write-ups, all −236…−250, 64–75 words,
  each naming its exact selection. Sporting/Magdeburg/Littler-class picks with
  no in-band half-line stay HIGH picks without a write-up rather than padding.
- **Retired without replacement (flagged):** EuroCup Round 5 and ATP orders of
  play were not server-rendered on the official pages read (VF-12); all
  completed 21-Oct rows removed desk-wide; tests now assert no row predates
  the capture date.
- **Cross-layer compatibility:** `scripts/survey_lines.py` consumes
  `inputs.json["mlb_world_series"]`; the seed now derives that key from the
  same verified `MLB_TEAMS`/`MLB_FIXTURES` literals (values identical to the
  prior capture: TB 98-64 736/650, MIL 103-59 832/618). Retiring snooker
  originated rows legitimately regenerated survey outputs (24 lines,
  115 flagged) — committed as the integration step; `survey_verify` green.
- **Repo hygiene:** `data/verified/inputs.json` is generated only by
  `scripts/verified_seed.py`; the model no longer reads `data/inputs/**` or
  `data/live/**` at run time. `repo_audit.json` keeps its historical
  2026-10-21 date.

## Verification performed

- Full CI pipeline run locally in order (verified seed→model→build, live,
  desk, survey incl. `survey_verify`, root `build_site.py`,
  `integration_audit.py`): all green, 0 broken cross-layer links.
- `python3 -m unittest discover -s tests`: 61 tests OK, including new
  featured-band, narrative-uniqueness/≥30-words, no-stale-fixture and
  NBA-exclusion assertions.
- Internal link scan of all 22 verified pages: 0 broken links/anchors.
