# Current Capture & Origination Layer — session 18792bd6

**Branch:** `arena/18792bd6-olbg2` · **Capture date:** 2026-10-22 · **Fixture window:** 2026-10-22 → 2026-10-29
**Published at:** `/current/` · **Data:** `data/current/` · **Raw captures:** `data/current/capture/`
**Pipeline:** `scripts/current_seed.py` → `scripts/current_model.py` → `scripts/current_build.py`
**Tests:** `tests/test_current.py` (37 tests, all passing; repository suite 186 tests passing)

---

## 1. What this layer is, and why it exists

The repository already carries fourteen overlapping research layers. This one is justified
only by genuinely fresh first-hand capture, so it publishes a single rule and obeys it
without exception:

> A value appears on `/current/` only if an official governing-body, league or tour endpoint
> returned it **during the 22 October 2026 session**, the raw response is stored verbatim under
> `data/current/capture/`, and the published row links the official page for that fixture.
> Anything an official source did not return is left **blank** with a written reason and a flag.

No bookmaker price was read at any point. Every price is originated here. No row is copied
from another layer of this repository and re-labelled as verified. Where a fixture could not
be confirmed, the sport publishes zero rows rather than a partial or reconstructed list.

Coverage: **57 fixture rows across 7 sports**, **1931 originated prices across 164 markets**,
**29 high-confidence in-band picks**, **29 written predictions**, **10 sports at zero rows each
with a first-hand reason**, **23 disclosure flags**.

---

## 2. Official sources read this session

Every URL below was fetched directly. The capture file named in the third column holds the
verbatim transcription; the published page links the per-fixture URL, not just the feed root.

| Sport / competition | Official source read | Capture file | What it returned |
|---|---|---|---|
| Rugby Union — URC | <https://stats.unitedrugby.com/match-centre/table/2026-27> | `urc_table_2026-10-22.json` | Full 16-club table (PTS PL W D L BP PF PA DIFF TF TA TB LB FO form) and all eight Round 3 results with scores and venues |
| Rugby Union — URC | <https://stats.unitedrugby.com/match-centre/2026-27/4> | `urc_round4_2026-10-22.json` | All eight Round 4 fixtures with official per-match URLs, venues and kickoff times as rendered |
| Ice Hockey — NHL | <https://api-web.nhle.com/v1/score/2026-10-23> | `nhl_score_2026-10-23.json` | Game-week counts 20–26 October plus the two 23 October games: ids, venue, `startTimeUTC`, records, named leaders |
| Ice Hockey — NHL | <https://api-web.nhle.com/v1/score/2026-10-24> | `nhl_score_2026-10-24.json` | All twelve 24 October games, ids `2026020168`–`2026020179`, venues, records, derived game-centre links, six named leaders each |
| Ice Hockey — NHL | <https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=gameTypeId%3D2%20and%20seasonId%3D20262027> | `nhl_team_summary_2026-10-22.json` | All 32 clubs: gp, w, l, otl, pts, pointPct, gf, ga, gfpg, gapg, pp%, pk% (snapshot through 2026-10-21) |
| Basketball — EuroLeague | <https://www.euroleaguebasketball.net/en/euroleague/game-center/> | `euroleague_round7_2026-10-22.json` | All nine Round 7 fixtures with official per-game URLs, venues, tip times, league positions; the completed 21 October result Hapoel IBI Tel Aviv 90–81 Virtus Bologna |
| Basketball — EuroLeague | <https://www.euroleaguebasketball.net/en/euroleague/standings/> | same file | Full 20-club standings: GP, W, L, win%, PTS+, PTS−, diff, home, away, last ten |
| Handball — EHF CL Men | <https://ehfcl.eurohandball.com/men/2026-27/standings/> | `ehf_standings_2026-10-22.json` | All 24 group-phase clubs across Groups A–F (GP W D L Goals DIFF PTS) plus the 28–29 October fixtures |
| Handball — EHF | <https://ehfcl.eurohandball.com/> | `ehf_2026-10-22.json` | Five EHF CL Men fixtures on 22 October, the 28 and 29 October fixtures with official match-detail URLs, nine EHF European Cup Men fixtures on 23–24 October, two IHF Women's World Championship 2027 qualifiers |
| Snooker — WST | <https://www.wst.tv/matches/> | `wst_ni_open_2026-10-22.json` | BetVictor Northern Ireland Open 2026 Round 3: six fixtures with `wst.tv/match-centre/{uuid}` URLs and verbatim times; the two "Live Now" fixtures held back; **21 completed Round 1 and Round 2 results with frame scores** |
| Baseball — MLB | <https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-10-25> | `mlb_world_series_2026-10-22.json` | World Series Game 1 `gamePk 849805` (2026-10-23) and Game 2 `849802` (2026-10-24), Rays at Brewers, American Family Field, series status |
| Baseball — MLB | <https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsType=regularSeason&fields=…> | `mlb_standings_sample_2026-10-22.json` | All 30 clubs with gamesPlayed, wins, losses, winningPercentage, runsScored, runsAllowed, runDifferential, divisionRank |
| Motor Racing — F1 | <https://www.formula1.com/en/racing/2026> | `f1_calendar_2026-10-22.json` | Round 18 United States, 23–25 OCT, official round URL; Round 17 Singapore completed; Round 1–7 winners, second and third |
| Motor Racing — F1 | <https://www.formula1.com/en/results/2026/drivers> | same file | Full 23-driver 2026 championship standings with points |
| Golf — DP World Tour | <https://www.europeantour.com/dpworld-tour/schedule/> | `dpworld_golf_2026-10-22.json` | "THIS WEEK: EVENT 40/42", Genesis Championship (Korea) at *Round 2 Tee Times Available* → in-play, `rows_originated: 0` |

Consulted but not usable for fixtures (documented on `current/flagged.html`):
<https://www.nba.com/games?date=2026-10-22>, <https://www.pdc.tv/tournaments/european-championship>,
<https://www.pdc.tv/live>, <https://www.pdc.tv/tournaments>, <https://www.atptour.com/en/scores/current>.

---

## 3. Dead ends — recorded so no future session repeats them

| Endpoint | Result |
|---|---|
| `cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json` | HTTP 500, twice |
| `data.nba.net/10s/prod/v1/2026-10-23/scoreboard.json` | Akamai "Invalid URL" |
| `www.nba.com/game?date=2026-10-23` | "Content Unavailable" |
| `stats.nba.com/stats/scoreboardv2` | fetch failed |
| `www.nba.com/games` | Calendar day counts render (22 Oct = 2, 23 = 12, 24 = 8, 25 = 7, 26 = 9); the fixture list itself does not |
| `www.nhl.com/standings` | HTTP 500 |
| `api.nhle.com/stats/rest/en/team/game` | HTTP 500 |
| `api.nhle.com/statsapi/v1/schedule` | 404 |
| `api-web.nhle.com/v1/standings/now` | works but costs eight chunks; superseded by the three-chunk REST team summary |
| `www.pdc.tv/tournaments`, `/live`, `/tournaments/european-championship` | cookie-consent wall and vendor inventory only, at every chunk depth |
| `www.atptour.com/en/scores/2026-10-23` | 404 |
| `www.atptour.com/en/tournaments/brussels/7485/2026/draw/results` | 404 |
| `www.unitedrugby.com/matches/` | 404 — use `stats.unitedrugby.com/match-centre/…` |
| `ehfcl.eurohandball.com/matches/` | 404 — use the standings page or `/matches/details/{id}/{slug}/` |
| `www.euroleaguebasketball.net/euroleague/results/` | 404 — use `/en/euroleague/game-center/` |
| `www.lnr.fr/rugby-top-14/calendrier-resultats` | 404 — Top 14 lives at `top14.lnr.fr` |

Consequence, honestly recorded: **the NBA is absent from this layer**. Nine EuroLeague fixtures
are the whole of its basketball coverage. Darts, tennis and golf publish zero rows for the
reasons on their sport pages, not because the sports have no fixtures.

---

## 4. Models

Full parameter list, including every constant that is ours rather than the sport's, is on
[`current/methodology.html`](../current/methodology.html). Summary:

| Sport | Model | Distribution |
|---|---|---|
| Ice Hockey | multiplicative Poisson attack/defence, shrinkage `gp/(gp+8)`, home ×1.05, league average **3.0784** goals per team game | exact score grid to 12; regulation ties split 50/50 for overtime and the shootout |
| Basketball | attack/defence on points for and against, shrinkage `gp/(gp+6)`, home +3.0, league average **86.4426** | normal margin, sd 11.0; total sd 15.0; no draws |
| Rugby Union | attack/defence on PF/PA, shrinkage `pl/(pl+6)`, home +3.0, league average **26.2083** | normal margin, sd 13.0, draw band ±1 point; total sd 16.0 |
| Handball | attack/defence Poisson on goals, shrinkage `gp/(gp+3)`, home ±0.4, league average **31.8273** over all 24 clubs | exact score grid to 70; draws stand |
| Baseball | attack/defence Poisson on runs, shrinkage `gp/(gp+20)`, home +0.25, league average **4.4811** over all 30 clubs | exact score grid to 20; ties split 50/50 for extra innings |
| Snooker | per-frame win rate from captured frames, shrunk `matches/(matches+6)` toward 0.500 | exact best-of-seven frame distribution |
| Motor Racing | share of championship points across 23 drivers (1933 points) | direct share; outrights only, capped at low confidence |

Ratings are `1 + w × (rate / league_average − 1)`, so a club with no games sits exactly at
league average. Prices are fair and vigourish-free: `decimal = 1 / probability`. The
probability is rounded to four decimals **first**, and the decimal and American prices are
derived from that rounded figure, so every number printed on the site can be reproduced from
the number printed beside it.

### The high-confidence gate

**high** = probability ≥ 0.7000 **and** a fair American price inside −250 … +10000.
Fair −250 is p = 0.714286, so the band is a 1.43-point-wide window. **medium** = probability
≥ 0.60, and also any probability above 0.70 whose fair price is shorter than −250, because
ultra-short chalk is capped. **low** = everything else.

The gate is searched across **every originated market on both sides** — moneyline, handicap
and match total — not just the two-way moneyline. That is the substantive difference between
this layer and its predecessors: a moneyline can only enter the window between 70.0 % and
71.43 %, which almost never happens, whereas an alternate handicap or total line can be chosen
so a genuinely strong opinion lands inside it. Of the 29 high-confidence picks, **28 come from
an alternate handicap or total line and 1 from a moneyline** (Leinster Rugby v Munster Rugby,
0.7063, −240).

Alternate-line grids are capped per sport so a published line is one a book would plausibly
post rather than an artefact of searching an enormous grid. Candidate selection is ranked:
moneyline first, then a handicap backing the model's own favourite, then a total, and only
last a heavy receiving handicap on the side the model does **not** favour — that last category
is arithmetically in band but says almost nothing.

### Two correctness points worth recording

* **Sign convention.** The threshold `T` is on the home margin; the home side is posted at
  `−T` and the away side at `+T`, which makes the two sides exact complements. Every line is a
  half-point, so no line can push. An earlier revision of this pipeline had the posted signs
  inverted relative to the probabilities; it was caught by re-reading the output and is fixed.
* **Settled ties.** In ice hockey and baseball a level score is resolved in overtime or extra
  innings. Half the tie mass is therefore parked on ±0.5 sentinels *before* any handicap
  probability is computed, and thresholds of 0 and ±0.5 are excluded from those sports' grids
  because they merely restate the moneyline. Without this, a "+0.5" hockey line silently
  double-counted the whole regulation tie.

---

## 5. Verification performed

1. **Independent recomputation.** Four fixtures — NHL Boston v San Jose, URC Leinster v
   Munster, EHF Barça v Montpellier, EuroLeague Panathinaikos v Baskonia — were recomputed
   straight from the raw capture JSON through a separate code path. League averages, expected
   scores, moneyline probabilities, draw probabilities and the band probabilities all agreed
   with the published values to four decimal places. Two of these recomputations are wired
   into `tests/test_current.py` so they re-run on every build.
2. **Table arithmetic re-checked.** Goals/points/runs for minus against equals the published
   difference, and wins plus draws plus losses equals games played, for all 24 EHF clubs, all
   30 MLB clubs, all 20 EuroLeague clubs and all 16 URC clubs. Also: total goals for equals
   total goals against across the 24 EHF clubs (3501 v 3501) and across the 30 MLB clubs
   (21769 v 21769), as it must.
3. **Cross-validation between independent official pages.** EuroLeague standings positions
   1–20 match the club codes printed beside each fixture in the official game centre. NHL
   records beside the 23 and 24 October fixtures match the 21 October team-summary snapshot
   for six clubs (BOS 7-2-1, NYR 7-3-1, CAR 8-2-1, VGK 8-3-0, TBL 7-2-0, CHI 3-6-0).
4. **Irregularity found and disclosed rather than smoothed.** The EuroLeague game centre lists
   a Round 7 fixture for Hapoel IBI Tel Aviv against Crvena Zvezda Meridianbet, but the same
   club had already played Round 7 on 2026-10-21 (90–81 v Virtus Bologna) and stands at 5–2
   over seven games while every other club shows six. The fixture is excluded and flagged
   (CU-04) instead of being published as a duplicate.
5. **Structural checks in CI.** Rebuild byte-identity, every local link and anchor resolving,
   every official link being `https`, every table's header and body cell counts matching,
   every fixture appearing on `matches.html` with its own official URL, every zero-row sport
   page carrying its flag id, and no bookmaker name appearing anywhere on the layer.
6. **No hallucinated pairings.** Two defects in earlier layers of this repository — invented
   ATP pairings (flag PA-01) and a PDC row that substituted Ritchie Edhouse for Stephen
   Bunting (flag PA-02) — were specifically guarded against: no tennis or darts row is
   published at all, because no official pairing was read.

---

## 6. Flag register

All 23 flags are published on [`current/flagged.html`](../current/flagged.html) with the
official source consulted beside each. None blocks publication.

| Flag | Sport | Substance |
|---|---|---|
| CU-01 | Ice Hockey | 22 October games excluded as in-play; every published W-L-OTL record is a 2026-10-21 snapshot that does not include them |
| CU-02 | Ice Hockey | Nathan MacKinnon's assists value was truncated at the end of a fetched chunk and is stored as `null`, never published |
| CU-03 | Basketball | NBA fixtures unreadable: four official endpoints failed and `nba.com/games` renders only per-day counts |
| CU-04 | Basketball | EuroLeague Round 7 fixture for Hapoel IBI Tel Aviv excluded — that round was already played on 2026-10-21 |
| CU-05 | Handball | Nine EHF European Cup Men fixtures and two IHF World Championship qualifiers captured but not priced: no official group table exists for them |
| CU-06 | Handball | A 29 October fixture was truncated mid-listing; the opponent was recovered from the official standings page and both readings disclosed |
| CU-07 | Snooker | Two Round 3 fixtures have no first-hand strength input for either player and publish blank lines; the page states no timezone, so two 09:00 fixtures may already be under way |
| CU-08 | Aussie Rules | Zero rows — no official fixture returned |
| CU-09 | Cricket | Zero rows — no official fixture returned |
| CU-10 | Darts | Zero rows — `pdc.tv` served only a cookie wall at every depth |
| CU-11 | eSports | Zero rows — no official organiser feed returned |
| CU-12 | Gaelic Football | Zero rows — season concluded, no official fixture returned |
| CU-13 | Golf | Zero rows — the only event in the window was in play at Round 2 |
| CU-14 | Greyhounds | Zero rows — no official feed reachable |
| CU-15 | Rugby League | Zero rows — no official fixture returned |
| CU-16 | Tennis | Zero rows — only live and completed matches returned; two routes 404 |
| CU-17 | Volleyball | Zero rows — no official fixture returned |
| CU-18 | Rugby Union | Round 4 times render as "Local" with no timezone named, and one fixture renders an hour earlier than the rest; published verbatim |
| CU-19 | Basketball | The official feed names an arena but never says whether a home fixture is at a neutral site; one uniform home advantage is applied and the two affected fixtures disclosed |
| CU-20 | Baseball | World Series Games 1 and 2 price identically because no starting-pitcher announcement was returned; no pitcher is named anywhere |
| CU-21 | Motor Racing | The outright is a share-of-championship-points prior, not a circuit model; every driver price is capped at low confidence |
| CU-22 | Snooker | The best-of-seven format is inferred from the 21 captured results (every winner finished on exactly four frames), not stated on the page |
| CU-23 | All | Home advantages, shrinkage priors, standard deviations, draw bands and alternate-line radii are this layer's assumptions; no official source publishes them |

---

## 7. What is deliberately *not* here

* **No bookmaker odds.** Nothing on this layer was read from a sportsbook, an aggregator or a
  comparison site. Every price is originated from official statistics.
* **No third-party statistics.** No Wikipedia, ESPN, Cricinfo, Flashscore or similar citation
  appears anywhere on `/current/`. One web search was run this session, to establish that the
  PDC European Championship window is official; the pairings it surfaced were **not**
  published, because they came from non-official sites.
* **No inferred values.** Where a source did not return a number, the cell is empty.
* **No claim of completeness.** The layer covers the fixtures its captures returned inside the
  window. It is not a live feed and does not refresh itself.

---

## 8. Coordination record

* Claim written to `COORDINATION.md` and pushed as commit `a116e81` before any file was edited.
* The requested branch name `session-<id>/<task>` is impossible here: the environment fixes
  this session to `arena/18792bd6-olbg2`. The deviation is logged in the claim block.
* Exclusive scope respected: only `current/**`, `data/current/**`, `scripts/current_*.py`,
  `tests/test_current.py`, `research/current-capture-18792bd6.md` and append-only entries in
  `COORDINATION.md`. Shared outputs — `index.html`, root navigation, `data/matches.json`,
  `scripts/integration_audit.py`, `.github/workflows/pages.yml` — were **not** edited. Because
  the workflow's drift check does not cover `current/`, byte-identical-rebuild enforcement is
  implemented inside `tests/test_current.py` instead, which keeps the guarantee without
  touching a file other sessions own.
* `scripts/integration_audit.py` reports zero cross-layer local link errors with this layer
  present.

---

## 9. Post-publication accuracy pass (same session, after PR #119 merged)

Reading the deployed pages rather than the build log surfaced four headline numbers that were
derived from the wrong field. None affected a price, a probability, a prediction or a flag, but
each was a false statement on the landing page, so all four were fixed and then pinned by tests.

| Rendered | Was | Should be | Cause |
|---|---|---|---|
| Index KPI "Disclosure flags" | 13 | **23** | counted only `matches.json["excluded"]`; the ten zero-row flags live in `sports[slug]["zero_row_flag"]` |
| Index sentence "28 of the **57** picks" | 57 | **29** | denominator took `counts["fixture_rows"]` instead of `counts["band_picks"]` |
| Index sport card "Snooker … **6** originated lines" | 6 | **4** | reused the fixture-row count for both halves of the sentence |
| Sport page lede "6 fixtures … **6** originated lines" | 6 | **4** | same reuse, in `build_sport` |

Fixes: two new helpers in `scripts/current_build.py` — `originated_by_sport()` and
`total_flag_ids()` — so both figures are derived from `lines.json` and `matches.json` rather
than restated. The flagged page lede now spells the accounting out ("23 distinct flag ids in
total: 13 capture disclosures listed below, plus one zero-row flag for each of the 10 sports
that publish no rows"), and the index KPI carries the same breakdown as its sub-label.

Six tests were added as `TestHeadlineCounts` (`tests/test_current.py`, now **43 tests**): every
index KPI equals its data field; the index flag count equals the set of distinct `CU-` ids
published on the flagged page; the alternate-line sentence uses band picks as its denominator;
every sport card and every sport page lede separates fixtures from originated lines and both
sum to `counts["originated_rows"]`; and the flagged lede's arithmetic adds up. Repository suite
**330 tests OK**, `integration_audit.py` reports 0 link errors, and the workflow's drift check
is clean.

**Lesson recorded for future sessions:** a deterministic rebuild and a green link audit both
passed while four rendered numbers were wrong, because every test asserted on the data rather
than on the rendered page. Assert on the HTML.
