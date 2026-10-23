# Quest desk — session record `693dbf40` (2026-10-23, cut-off 21:30 UTC)

## What was asked, what was built

Full upcoming-match list for 15 OLBG sports (Golf, Volleyball, Rugby Union, Cricket,
Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball,
Ice Hockey, Basketball, Rugby League), our own originated lines across every market
family, a graded pick per match (low/medium/high), focus on high-confidence picks inside
fair American −250…+10000, a top-five per sport, human written predictions (≥30 words,
facts only, no process words), executive summary, GitHub Pages dashboard, Flagged for
Review page, PR + merge without waiting.

**Result (`/quest/`, data in `data/quest/`):** 113 fixtures (99 priced, 14 blank with
reasons), 856 originated fair prices in 23 market families, 138 graded picks
(23 high, of which 9 inside the window), top-five shortlists for all 15 sports
(fewer than five only where priced matches are fewer), 34 written predictions
(minimum 51 words inherited, new piece 97 words; every in-window high pick covered),
75 registered official sources, 13 review flags (3 carried, 10 new).

## Repository review (line by line, findings)

The repo already contained 38 desk directories answering generations of this brief.
Rather than add a 39th disconnected capture, this session integrated the two freshest:

| Layer | Freshness | Contents used |
|---|---|---|
| `/cadence/` (`data/cadence/`, session `arena/a0c8b7f3-olbg2`) | captured 2026-10-23T20:05Z | 93 fixtures / 728 prices / 122 picks / 33 predictions / 59 sources — base layer, carried unchanged |
| `/brief/` (`data/brief/`, session 6b10ecda) | captured 2026-10-23T16:30Z | Saturday NHL slate (games 0168–0179) + stored 27-club NHL inputs; re-priced here |
| NHL.com first-hand read (this session) | 2026-10-23 ~21:30Z | games 0180–0187 (25–26 Oct), two published moneylines, week-strip counts |

Irregularities found while reviewing (all published, none silently fixed in other
sessions' scopes):

1. `COORDINATION.md` is 516 KB append-only and still contains committed merge-conflict
   markers from concurrent rebases (cadence audit RA-01). This session appended only.
2. 43 legacy HTML pages cover out-of-mandate sports (Aussie Rules, Esports; RA-02).
   `/quest/` publishes exactly 15 sports.
3. 204 older prediction entries leak the banned process words into reader prose
   (RA-03/RA-04). Quest prose passes a zero-match regex gate.
4. Root datasets (`data/matches.json`, `site/data/lines.json`) cover 5 and 2 sports
   respectively (RA-05). Quest does not build on them.
5. Two source desks price NHL from two different official goal conventions
   (standings incl. shootout goal vs stats-API excl.; e.g. Montréal 30 vs 28 GF in
   9 games). Disclosed as quest flag **Q-DQ1**; each row links its own feed.
6. One inherited OLBG event id (`gaa-cork-psfc` = 14) read like a sport id
   (Motor Racing), not an event id — flagged in **Q-OLBG1**; the final-integration
   session removed the unsupported value upstream (PR #178) and this desk was
   regenerated from the corrected layer before merge.
7. Open PRs #161/#167 from other sessions touch coordination records only.
8. Cadence's `offered_*` price columns (fair probability scaled by a margin factor,
   producing longer-than-fair decimals) are not carried over; Quest publishes fair
   prices only, defined on the methodology page.

## OLBG reverse engineering (read live 2026-10-23 ~21:30Z)

Pages read first-hand: `https://www.olbg.com/betting-tips` and
`https://www.olbg.com/betting-tips/Basketball/4`.

- **Taxonomy (mandated 15):** Tennis 3, Basketball 4, Golf 5, Cricket 7, Snooker 8,
  Rugby Union 9, Rugby League 10, Baseball 12, Ice Hockey 13, Motor Racing 14,
  Darts 15, Handball 20, Volleyball 21, Gaelic Football 25, Hurling 26,
  Greyhounds 28. Gaelic Sports = 25 + 26 on OLBG.
- **URLs:** `/betting-tips/{Sport}/{id}`; competitions insert segments
  (`/Basketball/NBA/4`, `/Basketball/European/Euroleague/4`,
  `/Basketball/NBA/NBA_Championship/4`); event pages via the rendered tables
  (stored example `?event_id=199984`); tipsters at `/best-tipsters/{Sport}/{id}`.
- **Mechanics:** community tipster competitions since 2002; selections show tip
  counts, tip-share %, expert counts and a Value Rating vs tip-share-implied
  probability; event pages show Most Popular Tip and Best Tipsters Tip.
- **Markets named by OLBG (Basketball page):** Money Line, Pointspread, Game Totals
  (+ outrights). This board originates the same families per sport — match winner /
  money line, handicaps (puck/point/goal/set/game/leg/frame/run), totals
  (points/goals/runs/games/sets/legs/frames), outrights and race winner.
- **Hard limit:** both pages returned the literal text “No tips found.” where the
  event table renders client-side. No server-side OLBG event inventory is
  capturable; fixtures come from governing bodies and join OLBG at sport level
  (flag **Q-OLBG1**). No OLBG price or tip percentage is used as an input anywhere.

## Origination added this session (NHL, 20 fixtures)

Engine (`scripts/quest_seed.py::nhl_price`): expected goals = average of scoring and
conceding rates from stored inputs, +4% home lift (none at the neutral-site game);
Poisson matrix 0–12; regulation tie → OT/SO share by expected goals, one-goal margin,
+1 total goal; markets ML, puck ∓1.5, totals 5.5/6.5, plus cadence-convention
band-ceiling alternate where the favourite is shorter than −250. League mean
3.155 goals from the 27 stored club lines (asserted internally consistent).

Cross-validation vs the brief desk's own money-line favourite probabilities on the
same twelve Saturday games: differences −0.026…+0.039 (mean |Δ| ≈ 0.024), same
favourite in 12/12. New in-window high produced: **Boston Bruins ML, 70.2%, fair −236**
(game 2026020170) — the one new written prediction, built only from the stored
11-game lines (BOS 8-2-1, 42 GF, 22 GA, 17 pts; SJS 6-4-1, 32 GF, 36 GA, 13 pts)
and the TD Garden fixture record.

Four added fixtures stay blank (no stored inputs for Florida / NY Islanders /
Dallas / Winnipeg / Vancouver): 0180, 0181, 0182 (neutral site), 0184.

## Start-time normalisation (the five classes)

| Class | n | Rule |
|---|---|---|
| published UTC/offset | 52 | stored instant shown in UTC (handball +01/+02 offsets normalised, same instant) |
| venue-local converted | 18 | domestic/order-of-play clocks via IANA zones; 25 Oct Europe DST change handled by tz database (e.g. SuperLega 18:00 CET = 17:00Z; German Bundesliga 24 Oct still CEST) |
| session-window start | 8 | PDC published CEST windows 13:00/19:00; not an exact throw time |
| viewer-zone inferred | 9 | “viewer-local” clocks read as America/New_York — triangulated (Newlands 10:30 SAST, Hagley 20:00 NZDT, Leicester 15:05 BST, plus six more orthodox starts; implausible otherwise). Flag **Q-TZ1** |
| date-only | 26 | `start_utc` stays null; only the date asserted. Flag **Q-TZ2** |

All 87 timed fixtures start after the 21:30Z cut-off (asserted in seed and verifier).

## Confidence, window, top five, prose — rules as published

- High ≥70%, medium ≥60% (inherited tier caps can only lower). Window:
  −250 ≤ fair American ≤ +10000; high ∩ window = 70.00–71.43% (a fair −250 is 71.43%).
  Today: 9 in-window highs, 14 highs outside, all shown at honest prices.
- Top 5 per sport: matches ranked by display-selection probability (strongest
  in-window pick preferred), best in-window line from the full market set shown
  alongside. Shortfalls printed (e.g. Baseball 2 priced matches → top 2).
- Prose: ≥30 words, unique, selection in plain words, every number traceable to a
  stored fact with an official link under the piece; zero matches for
  `\b(model\w*|verif\w*)\b`; no injury asserted (NBA's league report is linked on
  NBA rows instead — flag Q-INJ). Golf/Greyhounds/Gaelic carry no prose because no
  selection reached medium (carried flag CD-PR1); prices still published.

## Verification performed

- `python3 scripts/quest_verify.py` → 0 errors: all prices recompute from
  probabilities; window flags re-derived; high labels ≥0.70 without exception;
  blank fixtures carry reasons and no lines; every pick resolves to a published
  line; every in-window high has prose; prose length/uniqueness/banned-word gates;
  no start before cut-off; 25 generated pages crawled, no broken local link;
  data pages link out on every row band.
- `python3 -m unittest tests.test_quest` → 10 tests.
- Live cross-checks first-hand tonight: OLBG (2 pages), NHL.com schedule (23–26 Oct,
  incl. DraftKings MTL −170/+142 and TBL +105/COL −125 for 23 Oct — disagreement
  with our Tampa pick disclosed as **Q-MKT1**), NBA.com calendar (8 games 24 Oct,
  list unrenderable — **Q-COV1**), NHL week strip (11 games 27 Oct — **Q-COV2**).

## Limitations (also on /quest/flagged.html)

Q-OLBG1 no server-side OLBG inventory · Q-MKT1 one market disagreement · Q-TZ1/Q-TZ2
time provenance · Q-COV1 Saturday NBA omitted · Q-COV2 NHL stops 26 Oct ·
Q-DQ1 dual NHL goal conventions · Q-BLANK 14 unpriced fixtures · Q-INJ no official
availability feed beyond NBA · Q-CONF labels uncalibrated (no backtest in repo) ·
carried CD-PR1/2/3. The desk is a dated snapshot, not a live feed; the next refresh
needs a browser-grade OLBG capture, the Saturday NBA slate and post-weekend standings.

## Publication record

(Appended after merge/deploy below this line by the same session.)

| Item | Value |
|---|---|
| Pull request | [#181](https://github.com/buffedlizard55-lab/OLBG2/pull/181) — merged 2026-10-23T21:55:22Z as `b8368d1` (no approval wait) |
| CI | `Validate Pages content` **success** on the PR head and on `main` (run 40030186477) |
| Pages deploy | Several deploys cancelled each other while parallel sessions merged (#179/#182/#185); `pages-build-deployment` run [40031040503](https://github.com/buffedlizard55-lab/OLBG2/actions/runs/40031040503) completed build+deploy **success** on a `main` containing this desk |
| Live check | `/quest/today.html`, `/quest/top5.html`, `/quest/flagged.html`, `/quest/sports/ice-hockey.html` fetched after deploy and read: KPIs 113 fixtures / 99 priced / 856 prices / 23 high / 9 in-window / 34 predictions / 13 flags; Boston −236 write-up live. (`/quest/index.html` returned a stale cached 404 to the fetching tool immediately after deploy; the file is on `main` and sibling pages serve — re-check on next visit.) |
| Live entry | https://buffedlizard55-lab.github.io/OLBG2/quest/ |

Open flags remain published at `/quest/flagged.html` and do not block anything. Root navigation and
CI drift-wiring requests for `/quest/` stand in COORDINATION.md for the integrator.
