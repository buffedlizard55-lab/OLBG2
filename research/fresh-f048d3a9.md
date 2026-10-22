# Fresh audit — session arena/f048d3a9-olbg2 (2026-10-22)

Scope: read-only mechanical re-audit of the unified desk (`data/verified/`) + a first-hand
official-source sample. No upstream value was edited; discrepancies are flags with blank
corrected values in `data/fresh/audit.json` and on `fresh/flagged.html`.

## OLBG reverse engineering (re-confirmed first-hand, 2026-10-22)
- Tips hub: https://www.olbg.com/betting-tips — sport hubs at `/betting-tips/<Sport_Name>/<sport_id>`
  (e.g. Football/1, Horse_Racing/2, Darts/15, Ice_Hockey/13, Basketball/19 — matching `data/verified/sports.json`).
- Event pages: `/betting-tips/<Sport>/<League>/<Event_Name>/<sport_id>?event_id=<id>`
  (observed live: Gerwyn Price vs Rob Cross, Darts, event_id=32325 — the same fixture as desk row `pdc-32325`).
- Excluded by brief: soccer/football (1), horse racing (2), American football (11), boxing (6),
  UFC/MMA (27), hurling (26), cycling & specials (no active hub). 0 excluded rows leaked into the desk.

## Mechanical audit results (188 rows, 30 predictions)
Pass: 0 duplicate ids/fixtures; 188/188 rows carry HTTPS official + OLBG URLs; winner, handicap and
total probability sums = 1 (3-way markets include draw); fair odds = 1/probability within rounding;
all 30 predictions ≥30 words, unique, word-count fields exact, every fact sourced, every match_id resolves;
0 rows dated before capture; 14 of 17 eligible sports have rows.

## Flags raised (FR-01…FR-11, full detail in data/fresh/audit.json)
- **FR-01 (high):** 2 research predictions labelled `high` below 70% — NY Islanders 69.71% (-233),
  Gian van Veen 66.8% (-200). Same selections are `medium` in `matches.json` pick fields (FR-02, 3 same-selection label conflicts).
- **FR-03:** README still claims 178 rows / earlier counts; desk now has 188 rows, 35 upstream flags.
- **FR-04:** Tennis, Aussie Rules, eSports have 0 unified rows (reasons in sports.json; nothing invented).
- **FR-05:** 44/188 rows cite competition-level, not fixture-level, official pages.
- **FR-06:** 55 blank venues, 34 blank summaries, 34 unlined rows (published blank, not inferred).
- **FR-07:** 10 rows: local `date` ≠ UTC date in `time` (e.g. MIN@CGY 2026-10-22 / 2026-10-23T01:00Z) — convention unstated on the row.
- **FR-08:** First-hand re-verification is sample-only (below); the rest is mechanical audit, not re-verification.
- **FR-09:** EuroLeague page shows 18:15 (title) and 14:15 (stream line) for Panathinaikos v Baskonia; desk uses 18:15 UTC — corrected value blank.
- **FR-10:** 11 picks derive fair_american from 2dp-rounded odds rather than 4dp probability (rounding convention, e.g. -833 from 1.12).
- **FR-11:** Two Vodacom Bulls predictions share the 3-word opening "Back Vodacom Bulls".

## First-hand sample re-read (browser fetch; sandbox curl to sports hosts returns empty)
| Page | Result |
|---|---|
| https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154 | Title confirms Nashville @ Boston, Oct 22 2026 — matches row nhl-2026020154 (TD Garden, Boston 7-2-1 / Nashville 3-2-3 also matches ESPN schedule summary found in search) |
| https://www.nhl.com/gamecenter/min-vs-cgy/2026/10/22/2026020162 | Title confirms Minnesota @ Calgary, Oct 22 2026 — matches featured pick row |
| https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/panathinaikos-aktor-athens-kosner-baskonia-vitoria-gasteiz/E2026/67/ | Confirms fixture, 22 Oct 2026, Telekom Center Athens, PAO rank (1), Baskonia rank (20) as published; tip-time ambiguity → FR-09 |
| https://www.olbg.com/betting-tips | Live hub confirms taxonomy/URL schema above; Gerwyn Price vs Rob Cross darts event listed for today |

All other rows keep their upstream 2026-10-22 capture status. Nothing here is marked
first-hand verified beyond this table.

## Cross-scope requests (logged, not edited)
1. Upstream `/verified/` owner: regrade the 2 FR-01 research predictions (or publish the research-desk gate exception), fix FR-02 label conflicts, update README counts (FR-03), state date convention (FR-07) and American-rounding convention (FR-10).
2. Root navigation owner (`scripts/build_site.py`): add a `/fresh/` link ("Fresh Audit") at integration if desired; this session did not touch root HTML or the builder.
