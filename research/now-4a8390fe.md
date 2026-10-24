# /now/ — 24 October 2026 desk: record of work, sources and review findings

Session `arena/4a8390fe-olbg2` · snapshot `2026-10-24T18:10:00Z` · branch `arena/4a8390fe-olbg2`

This file records what was read, what was produced, what was checked, and what is still open. Nothing here
turns a link into proof: a link says where a value was read, and each fact carries the time it was read.

**Post-merge evidence correction (A5, 24 October):** PR #207 merged before its last CI/evidence fixes. The integrated desk now enforces 70% rather than 62%, regrading seven sub-70% highs to medium while retaining their previews. Three highs remain overall, but Dragons–Ospreys had started, so only Boston ML and St. Louis +1.5 are pregame highs. The root now says 50 fixture records / 45 still to start / 5 started, the unrelated reproducibility-disclosure test is restored, and V-09 flags the LA–New Jersey omission. The earlier 10-high and “upcoming” wording below is retained only where it describes the original build history.

---

## 1. The problem this session was asked to fix

The owner's words: the site is too confusing to understand what the matches are and where the picks are; it needs an
executive summary, obvious picks, and top-level organisation.

What was actually wrong, line by line:

| # | Finding | Evidence |
|---|---|---|
| R-01 | Forty-five published layers each claimed the current desk, with no single entry point | `git ls-files '*/index.html' \| wc -l` → 50 layer indexes |
| R-02 | The root landing page led with a 23 October cadence snapshot while newer desks existed, and its navigation listed 45 links | old `index.html` (commit `e0a6df4`) |
| R-03 | Neither the root nor the cadence page opened with an explicit statement of *where the picks are* | same |
| R-04 | Earlier desks stated that no OLBG listing was currently readable; on 24 October, 96 rows were readable across 14 sports | `now/olbg.html`, three hubs re-read live |
| R-05 | The inherited Gaelic record carried semi-final margins of 44 / −6 that disagree with the official scorelines (30 / 2) | `data/clarity/fixtures.json` vs the GAA scorelines on the record |
| R-06 | The inherited Rugby League margins (2 vs 28) were not opposition-adjusted yet were stored as if comparable | `data/clarity/fixtures.json` `rlwc-aus-fiji` |
| R-07 | At least six earlier desks grade started fixtures as actionable | recorded here and on `now/flagged.html` as V-08 for this desk's own four |
| R-08 | 95 reader-facing prediction texts in 12 other `data/**/predictions*.json` files use the brief's banned vocabulary | carried forward from the `/clarity/` audit, re-checked here: the new desk has zero |

## 2. What OLBG actually publishes (reverse-engineered today)

| Fact | Detail |
|---|---|
| Sport routes | `/betting-tips/<Sport>/<id>` with ids Golf 5, Volleyball 21, Rugby Union 9, Cricket 7, Snooker 8, Darts 15, Baseball 12, Gaelic Football 25, Hurling 26, Greyhounds 28, Tennis 3, Motor Racing 14, Handball 20, Ice Hockey 13, Basketball 4, Rugby League 10 |
| Event routes | `/betting-tips/<Sport>/<Group>/All_Events/<Home>_v_<Away>/<id>?event_id=<n>`; team sports use `@` for away-first names (e.g. `SJ_Sharks_@_BOS_Bruins`) |
| Content | one most-tipped selection per listed event, a tip count (`16/27`) and a share (`59%`). No odds are published |
| Time display | US Eastern strings such as `Today 14:05`, never UTC; stored verbatim, never converted here |
| Coverage today | 96 rows across 14 of the 15 sports; Golf hub returned “No tips found.” |
| Gaelic split | Gaelic Football (25) and Hurling (26) are separate routes; the Kilkenny hurling final is only on the hurling route |

Live re-reads in this session (all recorded in `data/now/olbg.json`):

| Hub | Checked | Result |
|---|---|---|
| Snooker `/Snooker/8` | 18:04Z | one event, `Mark Williams v Jak Jones`, event_id 9952, `Today 14:05`, Jak Jones 16/27 = 59% — matches the 17:15Z capture row |
| Golf `/Golf/5` | 18:06Z | HTTP 200, body renders “No tips found.” |
| Volleyball `/Volleyball/21` | 17:56Z | events listed including Giesen v Berlin (37013) and Trentino v Cisterna (36994) |
| NHL schedule `api-web.nhle.com/v1/schedule/2026-10-24` | 18:02Z | confirms SJS @ BOS 23:00Z at TD Garden (game 2026020170) and NYR @ OTT 23:00Z at Canadian Tire Centre (2026020171) |

## 3. What the desk produced

| Item | Count | Where |
|---|---|---|
| Fixture records | 50 across all 15 sports (45 still to start, 5 started at 18:10Z; 39 priced, 11 blank with a reason) | `data/now/fixtures.json`, `now/matches.html` |
| Originated prices | 866 (match winner, handicap ladder, total ladder) | `data/now/lines.json`, `now/lines.html` |
| Graded picks | 39 — 3 high, 33 medium, 3 low; all inside −250…+10000; only two highs are pregame | `data/now/picks.json`, `now/picks.html` |
| Picks still to start | 35 (4 had started by 18:10Z and are marked as under way) | `now/picks.html` |
| Written predictions | 36 across 11 sports, shortest 65 words, no repeated opening | `data/now/predictions.json`, `now/predictions.html` |
| OLBG rows | 96 | `data/now/olbg.json`, `now/olbg.html` |
| Sources | 66 registered, 50 official | `data/now/sources.json`, `now/sources.html` |
| Review items | 33 — 26 open, 2 corrected, 5 notes | `data/now/flagged.json`, `now/flagged.html` |
| Assertions | 8,069, zero failures | `scripts/now_verify.py` |

### Coverage against the five-per-sport target

| Sport | Predictions | Why not five |
|---|---:|---|
| Ice Hockey | 9 | target met |
| Basketball | 8 | target met |
| Rugby Union | 4 | five fixtures only, one without a usable official rate |
| Volleyball | 3 | three fixtures on the card |
| Tennis | 3 | three fixtures; two are 26 October first-round matches |
| Handball | 3 | three fixtures; all priced from the evidence ladder |
| Gaelic Sports | 2 | Cork final has no published scoring rates; Kilkenny final priced, Cork blank |
| Cricket | 1 | three of four fixtures price within five points of a coin flip |
| Baseball | 1 | game three has no announced starters at capture |
| Darts | 1 | one fixture; the pick is under way |
| Rugby League | 1 | England v Papua New Guinea is 30 October with no team news at capture |
| Golf, Snooker, Greyhounds, Motor Racing | 0 | no defensible numeric basis from the captured official inputs (see V-05 and the blank reasons) |

## 4. How the numbers were made

Four families, each documented on the method page and in `scripts/now_model.py`:

1. **Poisson scoring** — ice hockey and baseball. Expected score = geometric mean of a club's scoring rate and the
   opponent's conceding rate (no invented league constant), home multipliers 1.06 / 0.98, ties split 50/50 for the
   money line because it includes overtime.
2. **Normal margin** — rugby union (sd 13), rugby league (12), Gaelic (9), basketball (12.5), tennis (6 games).
   Draws removed by renormalising the two win tails. Basketball uses win percentage plus four points of home court
   and a 1.5-point deduction per listed unavailable player.
3. **Race to legs** — darts: a per-leg chance from the evidence tier, then a negative-binomial race to ten legs, which
   also gives the total-legs distribution.
4. **Evidence ladder** — volleyball, handball, cricket and the two rugby league / Gaelic cards: five rungs from the
   verified facts on the record, one rung = ten probability points from 50%. Never graded higher than medium.

Every price is 1 / probability. High confidence requires a numeric family, ≥70%, quality ≥0.85 and a price inside the
band; match totals are capped at medium; the evidence ladder is capped at medium.

## 5. Verification performed

- 8,069 assertions in `scripts/now_verify.py`, including: every price equals 1/probability; the band test matches
  −250…+10000 exactly; no total or evidence-ladder price is graded high; every high and medium pick has a ≥30-word
  preview that names its selection, does not repeat another opening and contains neither “model” nor “verified”;
  every table row on every page carries a link; every internal link and anchor resolves; the pipeline reproduces byte
  for byte.
- 794 unit tests pass (`python -m unittest discover -s tests`), including 16 new tests for this desk.
- `scripts/integration_audit.py` reports 0 cross-layer local link errors.
- Live OLBG re-reads and one live NHL schedule read are recorded in §2 with timestamps.

**What was not re-read:** the 50 official fixture records and their 245 per-fact citations come from the 17:35Z
capture and are marked `facts_inherited` on every row. This session did not re-open those pages; it re-used the
committed capture and says so on the site.

## 5b. The 0-10 score (added after the first build)

The owner asked for a 0-10 confidence number on every pick so sports can be compared without reading a price. The rule is `score_for()` in `scripts/now_model.py`:

```
score = round(min(10, 10 × probability × shade), 1)
shade = 1.0 for poisson / normal_margin, 0.8 for class_ladder
```

Consequences, all of them checked: 5.0 is a coin flip, 7.1 is the highest score on the desk (a 71.4% rugby union
handicap, the strongest chance the band allows), the evidence ladder can never exceed 8.0 and in practice tops out at
5.6 because those prices are capped near 70%. The score is published on the dashboard cards, on every row of
`now/picks.html`, on each sport page and on each preview in `now/predictions.html`, and it is re-derived line by line
by `scripts/now_verify.py` (8,069 assertions after the 70% and temporal corrections). Three cricket fixtures at 50–55% appear on the picks page under
"priced but not backed" — they are shown so the book is complete, and their score of 4.8–5.5 is the reason they are
not offered.

## 6. Open items handed back

| ID | Item |
|---|---|
| V-08 | Four picks are for matches already under way at 18:10Z; kept for the record, excluded from the executive summary |
| V-09 | The inherited ten-NHL-record set omits Los Angeles at New Jersey (19:30Z) from the official 12-game schedule; flagged with the official schedule link rather than filled with unconfirmed data |
| COV-* | Twelve sports carry fewer than five written predictions; each is named on the flagged page |
| F-* | Eleven fixtures carry no price, each with its stated reason |
| V-05 | OLBG's golf hub lists no events today |
| V-07 | Some inherited fixture links point at a round preview or squad announcement rather than a per-fixture permalink |

## 7. Reproduce

```sh
python scripts/now_seed.py
python scripts/now_model.py
python scripts/now_predictions.py
python scripts/now_build.py
python scripts/build_site.py            # root front door + archive index
python scripts/now_verify.py            # verifies the fresh root as well as /now/
python -m unittest discover -s tests
```
