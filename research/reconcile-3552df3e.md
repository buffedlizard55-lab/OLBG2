# /reconcile/ — cross-layer reconciliation audit

Session `arena/3552df3e-olbg2` · audit date 2026-10-22 · branch `arena/3552df3e-olbg2`

## Why this scope

At claim time (12:15 UTC) seven live sessions were each building a further fixture/prediction layer
(`/pulse/`, `/canon/`, `/command/`, `/atlas/`, `/update/`, plus deployment and reproducibility audits).
The repository already published **eleven** overlapping datasets, and nothing anywhere compared them.
Two specific defects were visible before any audit ran:

- the same fixture is published by up to seven layers at different prices and grades;
- rows that are not head-to-head fixtures (season outrights, tournament fields, “field v venue”,
  greyhound race cards) are formatted as matches with their own moneylines.

Adding a twelfth dataset would have deepened both. This session therefore audits what is already
published, from outside every other session's file scope.

## Method

`scripts/reconcile_audit.py` reads eleven layers read-only:

| Layer | File | Rows |
|---|---|---|
| root | `data/matches.json` | 47 |
| verified | `data/verified/matches.json` | 188 |
| board | `data/board/matches.json` | 207 |
| forward | `data/forward/matches.json` | 93 |
| hub | `data/hub/matches.json` | 189 |
| slate | `data/slate/matches.json` | 208 |
| portal | `data/portal/matches.json` | 244 |
| final | `data/final/matches.json` | 382 |
| desk | `data/desk/fixtures.json` | 25 |
| live | `data/live/lines.json` | 11 |
| survey | `data/survey/lines.json` | 25 |

Each row is normalised into one record: sport slug, date, home/away (club codes expanded only from the
repository's own captured team tables), moneyline decimals and probabilities **mapped by team name**,
pick, grade, source URL and the layer's own capture stamp. Fixture identity is
`(sport, date, sorted team names)` after accent stripping, alias resolution and parenthetical removal.

Ten checks run: overlap (C1), price conflict (C2), grade conflict (C3), non-fixture classification (C4),
staleness (C5), citations (C6), prediction quality (C7), one fixture-scoped URL describing incompatible
pairings (C8), within-layer duplicates (C9), and scope/coverage (C10).

## Results

**1,619 published rows resolve to 433 distinct fixtures.** 1,466 rows sit inside 369 fixtures that two
or more layers publish. The catalogue is ~91% duplication.

| Result | Count |
|---|---|
| Rows audited | 1,619 |
| Distinct fixtures | 433 |
| Overlapping fixtures | 369 (1,466 rows) |
| Rows that are not head-to-head fixtures | 64 |
| Team-level price conflicts | 341 |
| Selection-level grade conflicts | 161 |
| High grades that break the project's own rule | 116 |
| Stale rows (fixture before capture stamp) | 34 |
| Rows with no fixture date | 25 |
| Rows under the brief's excluded sports | 0 |

Largest price disagreement on one club on one date: **16.05 decimal points**
(Kosner Baskonia Vitoria-Gasteiz, 2026-10-22 — 7.21 in `/verified/` and `/board/`, 13.97 in `/final/`,
19.19 in `/portal/`, 23.26 in `/slate/`). The disagreement is not a bug in any one model; it is the
absence of a reconciliation step between them.

Confidence grading deviates from the rule the repository publishes (`high` only when p ≥ 0.70 **and**
the fair price is inside 1.40–101.00) in 116 rows: 57 in `/slate/`, 40 in `/hub/`, 37 in `/board/`.
Examples read straight from the committed data: `/slate/` grades Flavio Cobolli at p=0.6625 as `high`;
`/hub/` grades Boston Bruins at p=0.6601 as `high`; `/board/` grades Panathinaikos at 1.16 as `high`.

## First-hand spot checks (9)

Only nine claims were re-read from an official page in this session. Everything else is mechanically
audited, which can prove inconsistency between layers but not agreement with the outside world.

| ID | Claim | Official page | Verdict |
|---|---|---|---|
| SC-01 | NHL 2026-10-22 slate (12 games, three named pairings, 23:00Z) | <https://api-web.nhle.com/v1/schedule/2026-10-22> | confirmed |
| SC-02 | Boston Bruins v San Jose Sharks, 2026-10-24, TD Garden | <https://api-web.nhle.com/v1/club-schedule/BOS/week/2026-10-24> | confirmed |
| SC-03 | Carolina Hurricanes v Boston Bruins, 2026-10-27 | same club feed | partially confirmed (UTC puck drop is 28 Oct 00:00Z) |
| SC-04 | ATP Almaty R16 pairings on 2026-10-22 | <https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule> | **contradicted** |
| SC-05 | GBGB Cat-1 dates/tracks/distances (23–24 Oct, 8 Nov, 20 Nov…) | <https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/> | confirmed (as race meetings, not fixtures) |
| SC-06 | PDC European Championship R1 pairings | <https://www.pdc.tv/tournaments/machineseeker-european-championship> | unreadable (cookie wall); rows cite a rankings page |
| SC-07 | Antonelli (Mercedes) in the 2026 standings, 340 points | <https://www.formula1.com/en/results/2026/drivers> | partially confirmed (driver/team yes, points not rendered) |
| SC-08 | Polish PlusLiga fixtures on the cited page | <https://www.plusliga.pl/games.html> | unreadable (redirects to TAURON Liga, women's list) |
| SC-09 | EuroLeague round-7 fixtures on 22–23 Oct | <https://api-live.euroleague.net/v1/results?seasonCode=E2026&round=7> | partially confirmed (teams yes; future pairings not in a results feed) |

SC-04 is the material result. The official Almaty day-6 order of play for 22 October 2026 is
Atmane–Bellucci, Machac–Khachanov, Medvedev–Shimabukuro, Bublik–Marozsan plus two doubles matches.
The `/slate/` layer publishes Almaty round-of-16 pairings that include Flavio Cobolli v Rinky Hijikata.
Neither player appears on the official card. That row — and the other `/slate/` tennis rows — cannot be
presented as verified under the brief's “no hallucinations” rule.

## What this session changed

Only new files. No other session's data, builder, page or test was edited:

- `scripts/reconcile_audit.py`, `scripts/reconcile_build.py`, `scripts/reconcile_verify.py`
- `data/reconcile/report.json`, `rows.json`, `spot_checks.json`
- `reconcile/**` (28 pages: overview, conflicts, non-fixtures, freshness, provenance, predictions,
  spot checks, flagged for review, method, sources, sports index + 17 sport pages)
- `tests/test_reconcile.py` (30 tests)
- this file, and an append-only entry in `COORDINATION.md`

## Limits, stated plainly

- Nine spot checks, not 1,619. The mechanical checks prove disagreement between layers; they do not
  prove any layer matches the world.
- “Non-fixture” is a classification from the row's own text and structure — a defect report, not a deletion.
- Price and grade conflicts are expected when layers run independent models. The finding is the missing
  reconciliation, not that a particular model is wrong.
- The audit date is fixed at 2026-10-22 so rebuilds are byte-identical; it is never read from the clock.
- CI wiring for `/reconcile/` (a rebuild + drift gate in `.github/workflows/pages.yml`) is logged as a
  cross-scope request: that workflow is claimed by session `arena/17c50bb7-olbg2` / `arena/dc72bac4-olbg2`.
