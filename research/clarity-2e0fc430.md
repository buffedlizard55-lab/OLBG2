# /clarity/ — 2026-10-24 fifteen-sport desk

Session `arena/2e0fc430-olbg2`. Capture window 2026-10-24 17:10–17:40 UTC.
Live desk: <https://buffedlizard55-lab.github.io/OLBG2/clarity/>

## 1. What this session built

One dashboard that answers the question the brief keeps asking: *what are the matches, what are the picks,
and where is the analysis?*

| Item | Value |
|---|---:|
| Sports | 15 of 15, each with its own page |
| Fixtures captured from an official page | 50 |
| Fixtures with at least one originated line | 41 |
| Fixtures published without a line, with the reason | 9 |
| Originated selections (match winner, handicap, total) | 239 |
| Graded picks (one per priced fixture, all inside −250…+10000) | 41 |
| High-confidence picks | 12 across 5 sports |
| Written predictions (min 63 words, 2+ sourced facts each) | 31 across 11 sports |
| Official endpoints in the register | 52 |
| Per-fact citations | 245 |
| Review items published | 13 |
| Repository findings published | 7 |

## 2. OLBG reverse engineering (first-hand, 2026-10-24)

### Route schema

```
/betting-tips                                  → all-sport hub
/betting-tips/<Sport>/<sport_id>               → sport hub
/betting-tips/<Sport>/<Comp>/<Group>/<H>_v_<A>/<sport_id>?event_id=<id>
```

### Sport ids confirmed against the live sitemap

| Sport | id | Sport | id |
|---|---:|---|---:|
| Golf | 5 | Tennis | 3 |
| Volleyball | 21 | Motor Racing | 14 |
| Rugby Union | 9 | Handball | 20 |
| Cricket | 7 | Ice Hockey | 13 |
| Snooker | 8 | Basketball | 4 |
| Darts | 15 | Rugby League | 10 |
| Baseball | 12 | Gaelic Football | 25 |
| Greyhounds | 28 | Hurling | 26 |

Two traps found: **Ice Hockey is 13, not 11** (id 11 is American Football), and Gaelic sports are split
across **25 (football)** and **26 (hurling)**. Prior layers in this repo use both correctly; the point is
recorded so a new layer cannot get it wrong.

### Market vocabulary OLBG actually uses

Money Line, Puck Line, Game Totals, Run Line, Pointspread, Handicap, Win Match (2-way), Handicap 2-way,
Total 180s, Most 180s, Total Legs, Frame Betting, Top Team1 Batsman, Outright Winner, Win Tournament,
Grand Final Winner. This is the vocabulary the desk mirrors when it originates a market, rather than
inventing labels bookmakers do not use.

### Defects observed

1. **Times are displayed in US Eastern.** OLBG lists *HBW Balingen-Weilstetten v MT Melsungen* as
   "Today 14:00"; the HBL publishes 20:00 CEST. 14:00 ET = 20:00 CEST. Mixing the two without conversion
   puts a row six hours out.
2. **Blank prices.** The NHL event page for Carolina at St. Louis renders `WIN @` with no number, while tip
   counts render normally.
3. **"No tips found."** The golf hub returned that on a day the Butterfield Bermuda Championship was in
   progress. A listing-driven desk would report zero golf fixtures.
4. **Outright-only sports.** Rugby League returned three 2027 futures and no match market at all.
5. **Tip share is not a probability.** "15/26 Win Tips · 58%" is the share of OLBG tipsters, not a chance of
   winning. It is not used as a pricing input in this desk.

## 3. What was verified, and how

Every fact in `data/clarity/fixtures.json` carries a `source_url` and a `source_key` that resolves in
`data/clarity/sources.json`. Highlights of the capture:

| Sport | Official inputs captured |
|---|---|
| Ice Hockey | 12-game NHL score feed for 24 Oct plus the 24 Oct standings: games played, goals for/against, home and road splits, team leaders |
| Basketball | NBA 2026-27 standings plus the 1:00 PM ET official injury report, read fixture by fixture |
| Baseball | MLB StatsAPI World Series schedule, probable pitchers, 2026 season pitching lines, both league standings |
| Rugby Union | URC table and Round 4 team announcements; Gallagher Premiership standings and Round 4 results; TOP 14 standings and journée 7 calendar |
| Rugby League | RLWC Round 2 match centre (both team lists, ins and outs), Round 1 wrap with scorelines, Round 3 draw |
| Cricket | ECB tri-series schedule, ICC match reports for all three completed games, CSA Pro20 fixtures and results |
| Golf | PGA TOUR leaderboard with embedded FanDuel prices; DP World Tour leaderboard |
| Motor Racing | formula1.com race hub: FP1/FP2 order, gaps, session times, circuit data; drivers' standings |
| Greyhounds | GBGB final fields with semi-final times and prize money for both Category One finals |
| Tennis | ATP Almaty final report and order of play; Basel and Vienna draw reports |
| Darts | PDC Round 1 results and averages; Day Three schedule |
| Gaelic Sports | Kilkenny GAA county final page and club results; Munster GAA final page; Galway GAA revised fixture notice |
| Snooker | WST matches page: semi-final result and the final's identity |
| Volleyball | Lega Pallavolo Round 2 fixture announcements; VBL fixture list |
| Handball | EHF Champions League group standings; HBL and LNH fixture lists |

## 4. Line origination

Full method on `/clarity/methodology.html`. In one line: shrunk attack/defence or margin models per sport
family, a race-to-target state model for set/leg sports, and outright fields priced from the leaderboard,
practice order or semi-final clock. Prices are `1/p` with no margin and no bookmaker input.

The −250…+10000 window is applied literally. Because −250 implies 71.43%, a two-way selection can only be
both "above 70%" and "longer than −250" between 70.0% and 71.43%. Rather than publish 78% favourites as
"high confidence" at −355, every market is originated and the strongest **in-band** selection is the pick.

## 5. Assumptions, stated plainly

| Sport | Assumption | Why |
|---|---|---|
| Volleyball | per-set prior from verified status (champions, promoted, both won openers) | both league tables render client-side |
| Handball | none — the three fixtures are published blank | only one side per fixture had published goal totals |
| Darts | tournament-mean prior for Aspinall's average | PDC published Littler's 105.05 only |
| Tennis | class prior from the seed line / published head-to-head | no serve or return statistics published |
| Basketball | 3-win pseudo-count, 0.22 home term, 1.6 pts per confirmed absence | 1–2 game samples |
| Rugby league | margins damped from Round 1 | no per-team points table in the RLWC match centre |
| Gaelic | scoring from semi-final margins and title split | no club scoring table |
| Cricket totals | 50/50, graded low | no venue par published |
| F1 | practice-order prior | grid not set at capture |

Each assumption is repeated on the row it affects and in `data/clarity/picks.json`.

## 6. Repository review (line by line, scripted)

`scripts/clarity_audit.py` produces seven findings with file names, line numbers and counts. The three that
matter:

1. **CR-01 — 95 published prediction texts across 12 data files use `model` / `verified` vocabulary.**
   The brief bans those words from reader-facing prose. This session's 31 write-ups are clean; the others
   belong to merged sessions and are reported, not edited.
2. **CR-02 — Aussie Rules and eSports rows live inside desks that advertise an exact-15-sport scope**
   (`data/atlas`, `data/beacon`, `data/canon`, `data/command`, `data/portal`, `data/slate`, `data/vanguard`).
3. **CR-03 — the "future-only" desk still prices started fixtures.** PR #194 announced that only fixtures
   with a confirmed future start receive an actionable market. Re-scanning `data/zenith` at 17:35 UTC finds
   17 fixtures whose published start has passed, carrying 212 originated selections and 20 picks.

Also recorded: 4 merge-conflict marker lines in `COORDINATION.md`, and a stale RR-03 claim in
`data/ledger/repo_review.json` that describes a root page timestamp which no longer exists.

## 7. CI and the ledger drift gate

`scripts/ledger_report.py` counts top-level directories that contain an `index.html`, so adding
`/clarity/` changes `data/ledger/repo_review.json` and `ledger/repo-review.html`. Both were regenerated with
the ledger owner's scripts, unmodified, and committed with this layer: layer count 43 → 44, with `clarity`
appearing in the evidence list. No ledger prose was hand-edited.

## 8. Reproduce

```sh
python3 scripts/clarity_seed.py        # official captures -> fixtures + source register
python3 scripts/clarity_model.py       # originate markets, grade picks
python3 scripts/clarity_predictions.py # validate and publish the write-ups
python3 scripts/clarity_audit.py       # repo audit + flag list
python3 scripts/clarity_build.py       # write /clarity/
python3 scripts/clarity_verify.py      # 2,828 structural assertions
python3 -m unittest tests.test_clarity_2e0fc430 -v   # 20 tests incl. byte-identical rebuild
```
