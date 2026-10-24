# `/today/` evidence expansion — session `0d1eb9b5`

**Branch:** `arena/0d1eb9b5-olbg2`  
**Research capture:** 2026-10-24 17:15–18:25 UTC  
**Scope:** the exact 15 covered sports, with implementation isolated to `scripts/today_*.py`, `data/today/**`, `today/**`, `tests/test_today*.py`, this report, and the session's append-only coordination records. Shared root integration is deferred until the final pass.

## Validated board at this checkpoint

| Measure | Result |
|---|---:|
| Captured OLBG listing rows | 107 |
| Officially sourced fixtures | 39 |
| Originated fair-price rows | 387 |
| Published picks and unique written previews | 27 |
| High / Medium / Low picks | 10 / 10 / 7 |
| High picks inside the requested fair-price band | 3 |
| Source-register entries | 49 |
| Flagged review items | 27 |
| Rendered pages | 25 |
| Shortest preview | 87 words |
| Line-by-line verifier | 4,834 checks, zero errors |
| Focused regression suite | 31 tests, all passing |

Fixtures and picks by sport:

| Sport | Fixtures | Picks |
|---|---:|---:|
| Ice Hockey | 12 | 5 |
| Basketball | 8 | 5 |
| Baseball | 1 | 1 |
| Tennis | 3 | 3 |
| Volleyball | 6 | 4 |
| Handball | 5 | 5 |
| Motor Racing | 1 | 1 |
| Darts | 3 | 3 |
| Other seven covered sports | 0 | 0 |

The five-pick target is a ceiling and a target only where supportable events exist. It is not filled with outrights, started matches, official fixtures lacking a captured OLBG row, or unsupported events.

## OLBG reverse-engineering and event matching

- Event rows use OLBG's `?event_id=<id>` canonical query parameter. Every pick must join to a captured row; an official-only fixture may have research prices but cannot be promoted to the pick card.
- The hub's selection and tip share are community information, not bookmaker odds and not model inputs. Displayed times remain verbatim strings and are never silently treated as UTC.
- The current handball capture contains 20 rows and volleyball 11. Piacenza–Modena and Milano–Cuneo remain official-only volleyball fixtures because no corresponding OLBG row was exposed.
- The refreshed darts hub contains three match events and two outrights. Ratajski–Doets and Schindler–Wattimena were removed after their Saturday start times rather than retained as upcoming selections. PDC World Championship 2027 was added as an outright listing only.
- Golf has no listing; Rugby League has only 2027 outright futures. These are published gaps, not zero-value selections.

## Official-source and pricing increments

### NHL, NBA and MLB

- NHL schedule/score feeds and the official team-summary feed supply all 12 games, records, UTC starts, venues, scoring rates and player context. The started Anaheim–Philadelphia game stays in the match list without a pick.
- NBA's official games page, current and completed standings, traditional statistics and 1:30 PM ET injury report supply eight games. Unsubmitted reports remain pending, the ambiguous Dean Wade PDF page-break row is excluded, and missing arenas remain blank.
- MLB's official schedule and standings support the single World Series game and its probable pitchers.
- NHL/MLB use independent Poisson scoring matrices; NBA uses shrunken official scoring rates and a spread calibrated to the same moneyline favourite.

### Tennis, volleyball and handball

- ATP/WTA schedules, draws, player profiles, head-to-head pages and reports support three finals. Siniakova's unfinished third set in the Osaka retirement is excluded: her completed-set record is 7–1, not 8–0. The Ningbo article's Saturday label versus the official Sunday final date remains an explicit irregularity.
- Lega Volley's calendar and standings supply all six Sunday Italian fixtures. Prices use one-round match, set and point evidence with substantial shrinkage. Only the four with OLBG rows become picks.
- LNH and HBL calendars, standings, team pages and matchday preview support five Sunday handball selections. Three-way regular-time moneylines retain the tie; goal handicaps and totals come from the same Poisson score matrix. The direct HBL table's reCAPTCHA is disclosed and was not bypassed.

### Formula 1

Official inputs:

- [United States GP event](https://www.formula1.com/en/racing/2026/united-states) and official timetable: race `2026-10-25T20:00:00Z`, 15:00 Austin, five hours behind UTC.
- [Practice 2 results](https://www.formula1.com/en/results/2026/races/1297/united-states/practice/2): all 22 current starters. Leclerc 1:35.291; Antonelli +0.042, Verstappen +0.189, Hamilton +0.615, Russell +0.744.
- [Driver standings](https://www.formula1.com/en/results/2026/drivers): points for every current starter. Tsunoda has standings points but no current Practice 2 time and is excluded.
- [Season race results](https://www.formula1.com/en/results/2026/races): 17 completed races; Antonelli eight wins, Russell three, Verstappen two, Norris two, Hamilton one and Leclerc one.

The winner weight is `(0.15 + points/max points) × (1 + wins/max wins) × 1/(1 + Practice 2 gap seconds)`, normalized across 22 starters. Podium inclusion enumerates every ordered top-three outcome exactly. Winner probabilities sum to one and podium probabilities distribute exactly three places. Antonelli is the independent selection at 31.19%, fair +221, Low; no qualifying/grid advantage is claimed.

### Darts

Official inputs:

- [PDC Day Three schedule](https://www.pdc.tv/news/2026/october/24/2026-machineseeker-european-championship---day-three-latest): Saturday Round 2 order and best-of-19 format.
- [PDC Friday report](https://www.pdc.tv/news/2026/october/23/Littler-kickstarts-European-Championship-title-bid-in-style/): Aspinall 6–3, Littler 6–3, Clayton 6–3 and Rock 6–1; Littler's 105.05 average and Rock's six consecutive legs.
- [PDC opening-night report](https://www.pdc.tv/news/2026/october/22/nine-dart-star-woodhouse-sets-up-van-veen-clash-dortmund/): Price 6–2 with a 99.26 average and Bunting 6–5.
- [PDC rankings](https://www.pdc.tv/rankings) and [European Championship page](https://www.pdc.tv/tournaments/machineseeker-european-championship): separate two-year world-ranking and current European Tour earnings.
- [PDC Sunday schedule](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/): quarterfinal session starts 12:00 GMT after the clock change.

The leg-probability logit is `0.08 ln(world earnings ratio) + 0.06 ln(European Tour earnings ratio) + 0.035 × the difference in tournament leg differential`. Exact first-to-ten outcomes price match winner, both 2.5-leg handicaps and total legs 16.5. Current selections: Littler 60.93%/−156 Medium, Price 60.82%/−155 Medium, Rock 54.50%/−120 Low.

The PDC's directly readable Saturday report and indexed hub still exposed pre-match/TBC content for Sunday. [ESPN](https://www.espn.com/darts/story/_/id/49948004/pdc-european-championship-darts-2026-schedule-results-how-watch-prize-money-dates-more-dortmund) and [The Independent](https://www.independent.co.uk/sport/stephen-bunting-borussia-dortmund-gerwyn-price-bundesliga-eintracht-frankfurt-b3072710.html) independently confirm Price 10–4 Menzies, Bunting 10–3 Huybrechts and the resulting Sunday quarterfinal. That corroboration is disclosed; the pairing was not inferred from a live bracket. Saturday's exact match times are OLBG display values inside the official PDC session window.

## Verification commands

```bash
python3 scripts/today_seed.py
python3 scripts/today_model.py
python3 scripts/today_predictions.py
python3 scripts/today_flags.py
python3 scripts/today_build.py
python3 scripts/today_verify.py
python3 -m unittest tests.test_today_9f69ce85 tests.test_today_expansion tests.test_today_multi_sport -q
```

The verifier checks every listing/event ID, official link, probability and fair-price conversion, sport-specific market schema, complementary markets, F1 field/podium sums, pick-to-listing joins, confidence/band consistency, unique prose, repeated eight-word shingles, numeric claims against linked facts, local links/anchors and a source on every rendered table row.

## Open evidence gaps and integration state

- Cricket, Golf, Rugby Union, Snooker, Gaelic Sports, Greyhounds and Rugby League still require supported future events or comparable official inputs. Research continues without promoting unsupported events.
- F1 has no published qualifying grid; darts has the session-time and Sunday-corroboration limitations above; WTA Ningbo, HBL access, NBA report/venue/early-sample limitations and NHL started-game/shootout conventions remain flagged.
- PR #198 merged while this checkpoint was being prepared, and `origin/main` advanced through PR #207 to `59404ef`. Its changes do not touch the `/today/` implementation paths. Shared root navigation, README, CI inventory and deployment remain final-integration work; PR, autonomous merge and Pages confirmation are still pending for this branch.
