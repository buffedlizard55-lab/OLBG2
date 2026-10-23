# /liveboard/ — capture, origination and verification ledger

**Session:** `arena/cfa67ee2-olbg2` · **Branch:** `arena/cfa67ee2-olbg2`
**Captured:** 2026-10-23 16:20–17:05 UTC · **Published desk:** `/liveboard/`
**Scope:** the fifteen sports named in the brief — Golf, Volleyball, Rugby Union, Cricket, Snooker,
Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball,
Rugby League.

---

## 1. What this session actually did

The fetch tool in this sandbox reaches both OLBG and a number of governing-body endpoints directly.
That allowed a first-hand capture rather than a re-use of another desk's snapshot:

| Step | Method | Result |
|---|---|---|
| Fixture discovery | OLBG sport hubs, one per sport | 128 event rows across 14 sports (Golf empty) |
| Market survey | OLBG hub labels plus one full event page | 12 distinct market types observed |
| Official inputs | MLB Stats API, NHL API, EuroLeague, WST, Formula 1, URC, GAA, EHF | 12 blocks stored in `data/liveboard/inputs.json` |
| Line origination | `scripts/liveboard_model.py` | 130 priced rows + 8 fair handicap/total lines |
| Predictions | hand-written against captured facts | 7, each ≥ 30 words |
| Publication | `scripts/liveboard_build.py` | 24 pages, 824 internal links, 0 broken |
| Tests | `tests/test_liveboard_cfa67ee2.py` | 36 tests, all passing |

---

## 2. Reverse-engineering notes (refreshed on the live site)

These confirm and extend what earlier sessions recorded in `research/olbg-reverse-engineering.md`.

1. **URL schema holds.** Sport hub is `/betting-tips/{Sport}/{id}`; event page is
   `/betting-tips/{Sport}/{Group}/{Competition}/{Event_Name}/{id}?event_id={event_id}`. The lower-case
   form (`/betting-tips/darts`) returns 404, so the sport name is case-sensitive in the path.
2. **Golf can genuinely be empty.** Both `/betting-tips/Golf/5` and `/betting-tips/Golf/All_Golf/5`
   rendered "No tips found" rather than an error, and the sport menu reset itself to "All Sports".
   An empty hub is therefore distinguishable from a broken one and is recorded as such.
3. **No odds for a logged-out visitor.** The Olympiacos v Fenerbahce event page lists Money Line,
   Pointspread and Game Totals, the tip split per selection, and tipster comments — but every
   `WIN @` field is blank. The only numeric prices on the page are inside individual tipster
   comments ("2.50 hcap", "169.50 hcap"), which are one person's taken line, not a consensus.
   The hub's help text still claims each pick "shows the odds"; it does not render them here.
4. **Tip counts are per-market, not per-event.** A hub row's `w/tw` is the split inside the single
   market OLBG has chosen to highlight, so a "100%" on a 1/1 row says almost nothing. This is why
   every tip-share price on this desk is Laplace-smoothed and why a row needs at least six tips
   before it can carry a high label.
5. **Time display is mixed.** North American events print US Eastern (MLB World Series Game 1 shows
   as "Today 20:00" against an official 2026-10-24T00:00:00Z first pitch, i.e. 20:00 EDT). European
   events print UK local (URC's own match centre gives 14:45 local for Cardiff v Sharks, matching
   OLBG's 14:45). The string is stored verbatim and never converted.
6. **Pagination exists and was not followed.** Every hub ends with "Load More Tips". These lists are
   first pages, not complete cards.
7. **Row truncation is real.** Six rows were cut mid-row at the bottom of a hub and were excluded
   rather than guessed at (flag F-15).

---

## 3. Official-source ledger

Every published number traces to one of these. Nothing else was used.

| Source | URL | What it gave | Used by |
|---|---|---|---|
| MLB Stats API (standings) | `statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason` | Rays 98-64, .605, 736/650, +86, L1, 5-5 L10, 25-14 one-run, 8-6 extras, 63-35 night | P01, P02, P03 |
| MLB Stats API (club) | `statsapi.mlb.com/api/v1/teams/158?hydrate=standings` | Brewers 103-59, .636, 832/618, +214, W5, 8-2 L10, 55-26 home, 68-35 night | P01, P02 |
| MLB Stats API (schedule) | `statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-30` | Six games, all World Series; venues and UTC starts | P01, F-20 |
| NHL API (schedule) | `api-web.nhle.com/v1/schedule/2026-10-23` | Two games; published moneylines MTL −170 / CHI +138, TBL +105 / COL −129 | NHL rows |
| NHL API (scoreboard) | `api-web.nhle.com/v1/scoreboard/2026-10-23` | SJS 4-3 MTL (OT, 20 Oct); COL 3-4 NJD (20 Oct) | context only |
| EuroLeague | `euroleaguebasketball.net/en/euroleague/standings/` | 20-club table, games/W/L/points for/against | 3 EuroLeague rows + 6 fair lines |
| World Snooker Tour | `wst.tv/rankings/` | World list (Williams 8th, £747,400) and one-year list (Jones 4th, £141,000; Gilbert 11th, £73,250) | 2 snooker rows, P06, P07 |
| Formula 1 | `formula1.com/en/results/2026/drivers` | Drivers' points: Antonelli 340 … Hadjar 97 | US GP row |
| URC match centre | `stats.unitedrugby.com/match-centre/2026-27/4` | Round 4 fixtures + eight Round 3 scorelines | 3 URC rows, P04, P05 |
| GAA | `gaa.ie/fixtures-results` | One October fixture (shinty-hurling); no club football | F-03 |
| EHF Champions League | `ehfcl.eurohandball.com/men/2026-27/standings/` | 28–29 Oct fixtures; none matching OLBG's card | F-04 |

**Blocked and recorded, not worked around:** PDC (cookie wall, twice), Opel HBL (JS + reCAPTCHA),
ATP rankings (table absent from the rendered chunks), `cdn.nba.com` (HTTP 500, twice),
PlusLiga (redirects to the women's TAURON Liga), ICC T20 World Cup schedule (404), URC table
(headers only). Each is listed with its URL and its failure on `/liveboard/sources.html`.

---

## 4. Origination method

Two provenance classes, never blended:

* **official-model** — probability from a governing-body number. Baseball uses log5 on season
  winning percentages with a home term, and a normal approximation (sd 4.2 runs) for the run line
  and total. The two NHL games use the mean implied probability of the NHL feed's three published
  moneylines, because that endpoint carries prices but not club records. EuroLeague uses point
  differential per game with a 0.12 home edge. Snooker uses the log of WST ranking money at scale
  0.45. Formula 1 uses championship points share discounted ×0.55 for single-race variance.
* **community-implied** — probability from OLBG's published tip split, Laplace-smoothed as
  `(tips + 1) / (total + 2)`. A 1-of-1 tip becomes 66.7%, never 100%.

Prices: fair decimal = 1 ÷ p; offered decimal = fair ÷ (1 − margin), with the margin per sport in
`scripts/liveboard_model.py`. Labels: **high** = p ≥ 0.70 (plus ≥ 6 tips when tip-share based);
**medium** = p ≥ 0.60; **low** otherwise. **In band** = offered American price between −250 and
+10000.

### The band, worked through
A fair 70% shot is −233. A fair 75% shot is −300. With a 5% margin the qualifying window is roughly
70–75%. Two consequences are visible in the published data and are not hidden:

* Gloucester at 89% and Mark Williams at 88% are **high confidence and outside the band**, because
  their prices are too short.
* Five single matches cleared both gates: Nemo Rangers +1.50 (75.0%), Mark Williams (74.0%),
  Aurillac (71.4%), Connacht (70.6%), Jak Jones (70.6%). One outright (State of Origin 2027, NSW)
  also cleared both and is shown separately.

---

## 5. Verification performed line by line

| Check | Method | Outcome |
|---|---|---|
| Every fixture row has an OLBG URL containing its event id | `test_every_event_has_a_stable_source_url` | pass |
| Every price row has an https source and a stated basis | `test_every_price_has_a_source_and_a_basis` | pass |
| High label never applied below 70% | `test_high_label_requires_seventy_percent` | pass |
| Tip-share "high" rows carry ≥ 6 tips | `test_tip_share_rows_need_a_real_sample_to_be_high` | pass |
| Band flag recomputes from the offered price | `test_band_flag_recomputes_from_the_offered_price` | pass |
| A 1-of-1 tip never reaches 70% | `test_one_of_one_tips_never_becomes_certainty` | pass |
| Every prediction ≥ 30 words, no banned vocabulary, ≥ 1 official fact link | three tests | pass |
| No prediction asserts an injury | `test_no_prediction_claims_an_injury` | pass |
| Zero broken internal links across 24 pages (824 links) | `test_no_internal_link_is_broken` + `integration_audit.py` | pass |
| Rebuild is byte-identical | `test_rebuild_is_byte_identical` | pass |
| Repository suite | `python3 -m unittest discover -s tests` | **503 tests OK** |

**What is *not* verified.** No claim on this desk is backed by a page that was not fetched in this
session. That cuts both ways: because no official injury list was obtained, no injury is asserted
anywhere; because ATP and PDC data could not be read, no tennis or darts ranking claim is made.

---

## 6. Coverage and shortfalls

| Sport | Fixtures | Priced markets | Official-input rows | High & in band | Predictions |
|---|---|---|---|---|---|
| Golf | 0 | 0 | 0 | 0 | 0 |
| Volleyball | 14 | 14 | 0 | 0 | 0 |
| Rugby Union | 14 | 14 | 0 | 2 | 2 |
| Cricket | 7 | 7 | 0 | 0 | 0 |
| Snooker | 2 | 2 | 2 | 2 | 2 |
| Darts | 14 | 14 | 0 | 0 | 0 |
| Baseball | 1 | 3 | 3 | 0 | 3 |
| Gaelic Sports | 5 | 5 | 0 | 1 | 0 |
| Greyhounds | 15 | 15 | 0 | 0 | 0 |
| Tennis | 9 | 9 | 0 | 0 | 0 |
| Motor Racing | 3 | 3 | 1 | 0 | 0 |
| Handball | 14 | 14 | 0 | 0 | 0 |
| Ice Hockey | 13 | 13 | 2 | 0 | 0 |
| Basketball | 14 | 14 | 3 | 0 | 0 |
| Rugby League | 3 | 3 | 0 | 0 | 0 |
| **Total** | **128** | **130** | **11** | **5** | **7** |

The brief asked for five predictions per sport. Seven were written, in three sports. In every other
case the missing ingredient is the same: an official current-form input. Without one, a thirty-word
prediction would have to invent form, recent results or statistics, which the brief forbids and this
desk does not do.

---

## 7. Irregularities (full text on `/liveboard/flagged.html`)

F-01 Golf empty · F-02 Rugby League outrights only · F-03 Gaelic club fixtures uncorroborated ·
F-04 handball EHF mismatch · F-05 PDC blocked · F-06 ATP table not rendered · F-07 NBA endpoints 500 ·
F-08 PlusLiga redirect · F-09 OLBG publishes no odds · F-10 mixed timezones · F-11 no injury data ·
F-12 prediction shortfall · F-13 narrow band window · F-14 pagination not followed · F-15 six rows
truncated · F-16 Donaldson not on WST lists · F-17 URC table empty · F-18 no F1 session time ·
F-19 NHL records not obtained · F-20 one baseball fixture only.

---

## 8. Reproducing this desk

```bash
python3 scripts/liveboard_model.py    # data/liveboard/lines.json  (deterministic)
python3 scripts/liveboard_build.py    # liveboard/**               (deterministic)
python3 -m unittest tests.test_liveboard_cfa67ee2 -v
```

The model and build scripts read only `data/liveboard/olbg.json`, `inputs.json`, `predictions.json`,
`flagged.json` and `sources.json`. None of them touches the network.
