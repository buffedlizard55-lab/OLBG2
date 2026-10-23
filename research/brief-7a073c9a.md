# Brief desk research note — session `arena/7a073c9a-olbg2`

Date: 2026-10-23 · desk: `/brief/` · cut-off: 19:45 UTC

This note records what was read, what was refused, and how the numbers on the desk were produced.
It is the companion to `data/brief/session_captures.json` (this session's first-hand reads),
`data/brief/sources.json` (the ledger) and `data/brief/flags.json` (the review queue).

## 1. OLBG reverse-engineering

### 1.1 Sport taxonomy

The `/betting-tips` index links to every sport page and therefore exposes the numeric id used in
OLBG's URL schema. All twenty-one ids were read in one request at 19:31Z:

| Category | id | Category | id | Category | id |
|---|---|---|---|---|---|
| Football | 1 | Cricket | 7 | Motor Racing | 14 |
| Horse Racing | 2 | Snooker | 8 | Darts | 15 |
| Tennis | 3 | Rugby Union | 9 | Boxing | 16 |
| Basketball | 4 | Rugby League | 10 | Cycling | 17 |
| Golf | 5 | American Football | 11 | Handball | 20 |
| | | Baseball | 12 | Volleyball | 21 |
| | | Ice Hockey | 13 | Gaelic Football | 25 |
| | | | | Hurling | 26 |
| | | | | Greyhounds | 28 |

The fifteen sports in the brief map to: Golf 5, Volleyball 21, Rugby Union 9, Cricket 7, Snooker 8,
Darts 15, Baseball 12, Gaelic Sports 25 and 26, Greyhounds 28, Tennis 3, Motor Racing 14,
Handball 20, Ice Hockey 13, Basketball 4, Rugby League 10.

The previous desk session could confirm only four of these ids. The full map is new.

### 1.2 URL schema

* sport index — `https://www.olbg.com/betting-tips/{Sport_With_Underscores}/{sportId}`
* event — `https://www.olbg.com/betting-tips/{Sport}/All_{Sport}/All_Events/{Event_Name}/{sportId}?event_id={eventId}`
* outright — same shape with a competition name in the event slot, e.g. `European_Championship` with `event_id=32338`.

### 1.3 The blocking behaviour

Three requests were made with a client that does not execute JavaScript:

| URL | Time (UTC) | Served marker |
|---|---|---|
| `/betting-tips/Tennis/3` | 19:29 | `No tips found.` |
| `/betting-tips/Ice_Hockey/13` | 19:30 | `No tips found.` |
| `/betting-tips/Darts/.../Luke_Littler_vs_William_OConnor/15?event_id=32328` | 19:44 | `No tips found for Luke Littler vs William OConnor but here is a list of current related events.` |

The editorial copy around the table arrives; the rows do not. This is the same behaviour the previous
session recorded at 17:02Z, so it is a property of the site rather than a transient failure.

**Consequence.** "The full list of matches listed on OLBG" cannot be produced from OLBG by a non-browser
client. The desk therefore:

1. reproduces OLBG's categories, ids, URL schema and market vocabulary (this note and `/brief/olbg.html`);
2. sources every fixture from the relevant governing body, with that body's link on the row;
3. records OLBG event ids where they were captured (twelve darts ids, including 32328 and the outright 32338);
4. never uses an OLBG tip share, consensus percentage or value rating as a pricing input.

### 1.4 Market vocabulary quoted from OLBG's own copy

* Ice Hockey — money line (two-way, includes OT/SO), puck line (±1.5), totals (commonly 5.5).
* Tennis — tournament winner, win match, set betting, total games, first-set winner, games won (games handicap).
* Darts — win match two-way, win tournament outright.
* Baseball — money line, run line, totals.

These names are mirrored on the desk. The prices are ours.

## 2. Capture log (this session)

| # | Source | Time (UTC) | Result |
|---|---|---|---|
| 1 | olbg.com/betting-tips | 19:31 | 21 sport ids read |
| 2 | olbg.com/betting-tips/Tennis/3 | 19:29 | no rows |
| 3 | olbg.com/betting-tips/Ice_Hockey/13 | 19:30 | no rows |
| 4 | atptour.com/en/scores/current | 19:34 | six quarter-finals, three completed; no semi-final line-up |
| 5 | wtatennis.com/scores | 19:36 | 0 tournaments live; notifications only |
| 6 | cev.eu/matches/ | 19:37 | 404 |
| 7 | en.volleyballworld.com/global-schedule | 19:40 | 10 fixtures (24 Oct) + 4 results (23 Oct) |
| 8 | olbg.com event page (darts) | 19:44 | no rows |
| 9 | en.volleyballworld.com/global-schedule (chunk 2) | 19:51 | Japanese and Polish fixtures |
| 10 | pdc.tv/rankings | 19:52 | cookie wall |
| 11 | svleague-women/standings | 20:04 | title only |

Same-day captures made by session `6b10ecda` between 16:25Z and 17:22Z were reused and are labelled with
their original timestamps: NHL schedule and team summary, MLB schedule and standings, EuroLeague schedule
and standings, WST fixtures and top-36 ranking, EHF calendar, NRL World Cup draw, Premiership fixtures,
OLBG darts list, DP World Tour leaderboard, F1 calendar and standings, GAA fixtures, GBGB open races,
Cricket Australia fixtures, ATP scores.

## 3. Origination

| Sport | Method | Input |
|---|---|---|
| Ice Hockey | Poisson on goals for/against per game, 4% home adjustment, tie split 55/45 | 32-club NHL team summary |
| Baseball | Log5 on win percentage, 16-point home adjustment; normal margin for run line and total | 2026 regular-season W-L, RS, RA |
| Basketball | Log5 on shrunk win rates, 22-point home adjustment, σ = 11 | EuroLeague standings after Round 7 |
| Snooker | Bradley-Terry on ranking prize money, exponent 0.35 | WST top-36 ranking |
| Handball | Poisson on a 30-goal baseline shifted by half the first-leg margin | EHF calendar and first-leg score |
| Rugby League | Poisson on Round 1 points for/against, shrunk 70% to the 28.2-point mean | NRL World Cup Round 1 |
| Rugby Union | Log5 on a last-three-win rate mapped to 35–65%, 18-point home adjustment | Official form strings |
| Volleyball | Even-chance prior moved 8 points per set of margin in the same pairing's verified result | Volleyball World schedule |
| Golf | Softmax over the 36-hole leaderboard, 22% residual | DP World Tour leaderboard |
| Motor Racing | Bradley-Terry on championship points, 15% residual | F1 standings after Round 17, top 8 |

Two-way markets are fair: they sum to 1.000 with no margin. All probabilities are clamped to 5–95%.

### The band problem, stated plainly

"High confidence" is a probability of at least 70%. "Inside the window" is a fair price of −250 or longer.
A 70% chance converts to −233, so a selection can only satisfy both between −250 and −233. That is why the
desk publishes tiers rather than forcing the label:

* Tier A — 1 selection (Boston Bruins −245, 71.0%)
* Tier B — 6 selections at 70%+ but shorter than −250
* Tier C — 32 of the 39 write-ups, inside the window but below 70%

## 4. Verification performed

* 1,547 structural checks (`scripts/brief_verify.py`), 0 failures.
* 18 new unit tests (`tests/test_brief.py`); repository total 594, all passing.
* `scripts/integration_audit.py`: 0 cross-layer link errors.
* Determinism: re-running the three build steps produces no diff.
* Two-way markets summed to 1 on every row; in-band flag recomputed from the American price on all 470
  market rows; no pick on a started fixture; no pick where the favourite is shorter than −250; no
  prediction names a market or selection that does not exist; "model" and "verified" absent from all 39
  write-ups; no repeated four-word openings; no repeated sentences of eight words or more.
* Every published fixture carries an https source from the ledger; every priced fixture records its input.

## 5. What could not be done, and why

| Sport | Fixtures | Priced | Reason |
|---|---|---|---|
| Tennis | 10 | 0 | No semi-final pairing published at 19:34Z; a pairing cannot be inferred from two results without the bracket |
| Cricket | 5 | 0 | No official ranking or form table was read for these teams in the window |
| Gaelic Sports | 1 | 0 | Single fixture; no scoring input |
| Greyhounds | 5 | 0 | GBGB publishes track, distance and grade but no runners |
| Darts | 12 | 0 | PDC rankings behind a cookie wall; no verified strength input |

These are published as fixtures with blank markets and explicit reasons, not dropped and not filled.

## 6. Repo review

* 576 pre-existing tests pass; `integration_audit.py` reports 0 link errors; 729 HTML pages pre-existed.
* Stray merge-closing lines remain in `COORDINATION.md` (3216, 3307, 3437, 3549, 3609, 3628) and
  `METHODOLOGY.md` (125). Both files are outside this session's write scope apart from the append, so they
  were left in place and logged.
* The repository carries more than twenty overlapping research desks; their counts are not additive. The
  brief desk is registered as one clearly-labelled entry in the root navigation.
* The repository's historical scope is 17 sports; the current brief is 15. This desk uses 15 only.
