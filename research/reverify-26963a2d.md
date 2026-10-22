# Line-by-line re-verification & research desk — session `arena/26963a2d-olbg2` (2026-10-22, 02:46–04:45 UTC)

Scope: every row of the `/verified/` desk (119 rows at start) re-read against the governing body that
publishes it, plus a research capture (form, splits, leaders, rankings) used to write 16 research-grade
selections. Raw captures with per-fetch UTC timestamps: `data/verified/research_26963a2d.json`;
the written selections: `data/verified/research_picks_26963a2d.json`.

Rules applied: official endpoints only; no bookmaker odds; nothing inferred — anything not returned by an
official page stays blank and is flagged; the −250…+10000 band is applied to the desk's own fair prices.

## 1. What was re-verified (official URL · fetched UTC · result)

| Family | Rows | Source | Fetched | Result |
|---|---|---|---|---|
| NHL fixtures/venues/start times | 12 | `api-web.nhle.com/v1/score/2026-10-22` | 02:58 | 12/12 match (ids 2026020154–165) |
| NHL team records | 32 clubs | `api.nhle.com/stats/rest/en/team/summary` + `api-web.nhle.com/v1/standings/2026-10-22` | 03:02 / 03:55 | 28/32 match; BUF, PHI, FLA, OTT one game stale → **corrected** |
| NHL 21-Oct finals | 2 | `api-web.nhle.com/v1/score/2026-10-21` | 03:00 | PHI 3-1 BUF; FLA 1-5 OTT (shots 30-19) |
| EuroLeague R7 + standings | 9 | euroleaguebasketball.net standings / game-center round 7 | 03:06 | 9/9 fixtures match; HTA/VIR rows exclude game 61 (played 21 Oct) — noted |
| NBA Week 1 | 14 | `nba.com/schedule?date=2026-10-23` | 03:10 | 14/14 match |
| LNR Top 14 J7 / Pro D2 J8 | 7 + 8 | `top14.lnr.fr`, `prod2.lnr.fr` calendrier + classement | 03:14–03:16 | tables match; **4 kick-off times wrong → corrected (VF-27)** |
| URC R4/R5 | 14 | `stats.unitedrugby.com` table / round-4 / round-5 | 03:20–03:22 | table + fixtures match; **"Local" times were US-Eastern renders → UTC (VF-29)** |
| EHF CL round 5 | 5 (+24 table rows) | `ehfcl.eurohandball.com/men/2026-27/matches/`, `/standings/` | 03:36–03:38 | 5/5 fixtures, 24/24 table rows match |
| PDC European Championship R1 | 16 (+32 ranks) | `pdc.tv/rankings` (chunks 6–8), schedule article 19 Oct (chunk 6) | 03:30–03:31 | 32/32 Order-of-Merit values match; order of play matches; **per-match times unofficial → session start (VF-29, VF-31)** |
| MLB World Series | 4 | `statsapi.mlb.com/api/v1/schedule?…hydrate=probablePitcher` | 03:28 | 4/4 match; G1 MIL probable Misiorowski; G5 if-necessary not on desk (informational) |
| WST NI Open R3 | 8 | `wst.tv/match-centre/0444240f-…`, `wst.tv/rankings/abfba8fe-…?showLive=false` | 03:38–03:40 | 8/8 fixtures; full top 36 read; **Kyren Wilson #9 £716,800 was missing → row priced (VF-30)**; times were ET renders → UTC |
| Cricket | 2 | ICC strip; BCCI match page | 03:44–03:48 | **both rows wrong (VF-28)**: NZ v IND is 22 Oct 07:00 UTC; SA v AUS already at Day 4 stumps → retired |
| Volleyball (PlusLiga) | 3 | `plusliga.pl/games.html` | 03:44 | redirected to tauronliga.pl → **not verifiable (VF-32)** |
| Gaelic football | 5 | `gaa.ie/fixtures-results` | 03:44 | club fixtures not listed nationally → **not verifiable (VF-32)** |
| Golf, F1, rugby league outrights | 2 + 3 + 3 | — | — | not re-read this session (unlined; prior capture retained; disclosed) |

## 2. Irregularities found (all published on the Flagged for Review page)

- **VF-27** LNR kick-offs: `top14-11867` Toulouse v Perpignan is 16h35 CEST (desk 12:30 UTC → 14:35 UTC); `top14-11862` Vannes v Clermont 14h30 (→ 12:30 UTC) — swapped on the desk; `prod2-12064` Provence v Béziers 21h00 (→ 19:00 UTC); `prod2-12069` Narbonne v Brive 19h00 (→ 17:00 UTC).
- **VF-28** Cricket: `icc-271646` NZ v IND was 23 Oct 06:15 UTC on the desk; BCCI official page says Thu 22 Oct 07:00 UTC, Hagley Oval (resolves VF-17 — the root layer's 22 Oct was right). `icc-269791` SA v AUS was listed as a 24 Oct fixture while already at Day 4 stumps → retired.
- **VF-29** Timezone: the renderer shows JS-localised times in US Eastern. Desk darts (13:15…), URC ("14:45 Local") and snooker (08:00…) times were ET renders. Darts now carry the official session start 17:00 UTC with PDC match order; URC and snooker converted to UTC (+4h).
- **VF-30** Snooker: Wilson v Pang priced from the full official ranking list; frame format (best of 7) is from BBC Sport/TNT Sports, not wst.tv — disclosed. Seven other R3 ties stay blank (a player outside the top 36).
- **VF-31** PDC consent wall is not a block: content starts at chunk 6. Rankings 32/32 match; official order of play confirms the 16 ties.
- **VF-32** PlusLiga redirect and gaa.ie coverage — 8 rows not verifiable; left as captured, nothing filled.
- **VF-33** NHL FLA/OTT/BUF/PHI inputs rolled forward; player-level official facts captured and used (closes VF-19, addresses VF-24).
- Informational: EuroLeague HTA/VIR standings rows on the desk exclude game 61 (Hapoel 90-81 Virtus, 21 Oct); MLB Game 5 (849799, 28 Oct, if necessary) not on the desk.

## 3. Research desk selections (16) — `data/verified/research_picks_26963a2d.json`

Confidence rule: **HIGH** = desk probability ≥ 0.66, price in band, and every official indicator captured
(record, home/away split, last-10/form string, leader, ranking) points the same way, ≥3 official facts;
**MEDIUM** = ≥ 0.58 in band or one indicator against (stated as a caveat); LOW picks get no write-up.
Prices below are the live desk prices after the input corrections above.

| Match | Selection | Price | Grade |
|---|---|---|---|
| MIN @ CGY | Minnesota Wild ML | −244 | high |
| LAK @ NYI | NY Islanders ML | −233 | high |
| Aurillac v Nevers | Aurillac 1X2 | −238 | high |
| van Veen v Gilding | van Veen | −200 | high |
| NSH @ BOS | Boston ML | −175 | medium |
| WPG @ DAL | Dallas ML | −164 | medium |
| CAR @ EDM | **Carolina ML (+109, underdog)** | +109 | medium |
| SJS @ OTT | Ottawa ML | −164 | medium (back-to-back caveat) |
| Montauban v Oyonnax | Oyonnax 1X2 | −185 | medium |
| Connacht v Zebre | Connacht 1X2 | −238 | medium |
| Leinster v Munster | Leinster 1X2 | −196 | medium |
| Humphries v Searle | Humphries | −152 | medium |
| Price v Cross | Price | −156 | medium |
| R. Smith v Sedlacek | Smith | −213 | medium |
| WS Game 1 TB @ MIL | Brewers ML | −167 | medium |
| Wilson v Pang | Kyren Wilson | −217 | medium |

Declined (with reasons in the JSON): Zalgiris (0-2 at home), Detroit @ Vancouver (DET 3 road goals), Florida @
Pittsburgh (stale inputs now fixed but FLA on a 1-5 loss), Barça / Aspinall / Littler / Toulouse (outside band).

## 4. Pipeline changes (T5)

- `scripts/verified_seed.py`: NHL BUF/PHI/FLA/OTT rows; 4 LNR kick-offs; URC ET→UTC conversion in `shared_urc()`;
  darts session-start times; full WST top 36; `SNOOKER_ORIGINATED` m50; cricket row fix + retirement; VF-27…VF-33;
  VF-17/19/21/24 annotated as resolved/addressed.
- `scripts/verified_model.py`: snooker label Round 3; research picks loaded, validated (≥30 words, named
  selection, ≥3 facts, price/probability equal to the live row) and written to `predictions.json["research"]`;
  `research_pick` on rows; counts.research.
- `scripts/verified_build.py`: research section on `predictions.html`, confidence-aware cards with caveats and
  fetch times, row links; index link.
- `tests/test_verified_pipeline.py`: counts 94/24; new research-desk test (band, drift, facts, player names,
  plus-money presence).
- `METHODOLOGY.md`, `README.md`: player-level paragraph updated.
- Desk now 118 rows (94 originated, 24 unlined), 14 featured + 16 research write-ups, 33 flags.

## 5. Not done / handed over

- EuroCup R5 and ATP orders of play still not server-rendered (VF-12/VF-20).
- PlusLiga, GAA club, golf, F1 and rugby-league rows not re-verified this session (VF-32 and prior flags).
- PDC Round 2 (24 Oct) order of play "TBC" on the official article at capture time — nothing added.
