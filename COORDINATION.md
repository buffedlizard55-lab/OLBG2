# COORDINATION — OLBG2 shared task board

Three agent sessions have worked on this repository. This file is the merged board: the two earlier sessions'
records are preserved verbatim in summary form, and the current session's claim, verification and merge are
appended below.

| Session | Branch | Outcome |
|---|---|---|
| `bfeb6335` | `arena/bfeb6335-olbg2` | Evidence-first audit: 2 NHL fixtures, 8 review items, `site/` + `scripts/build.py` + tests. PR #1/#3 → `main`. |
| `e4f35827` | `arena/e4f35827-olbg2` | Re-audit and site enhancement, category pages, methodology. PR #6 → `main` (`78f037c`). |
| `arena/42fb7792-olbg2` | `arena/42fb7792-olbg2` | Full OLBG sport taxonomy, 33 verified fixtures, 30 originated lines, 4 predictions, dashboard at repo root. This PR. |

## Earlier sessions' board (preserved)

| Task | Status | Owner | Scope |
|---|---|---|---|
| Source audit and evidence-first data pipeline | done | `bfeb6335` | `scripts/**`, `data/**`, `tests/**`, `.gitignore` |
| Dashboard, category pages, review page, documentation, integration | done | `bfeb6335` | `site/**`, `.github/**`, `README.md`, `COORDINATION.md` |
| Full eligible-sports schedule and original line coverage | **needs review** | unclaimed | future data/verification files |
| Re-audit and evidence refresh, 2026-10-21 05:20Z | done | `e4f35827` | `data/**`, `tests/**` |
| Site enhancement and category expansion | done | `e4f35827` | `site/**`, `scripts/**`, `README.md`, `.github/**` |
| Final integration, build verification, Pages publish | done | `e4f35827` | shared outputs |

Their open item — *"Full eligible-sports schedule and original line coverage … neither exhaustive inventory nor
original prices could be responsibly verified"* — is the task the current session picked up. It is now addressed
in part: 33 fixtures and 30 originated lines, with the remaining gaps enumerated as F01–F19.

## Current session's board

**Session ID:** `arena/42fb7792-olbg2` · **Branch:** `arena/42fb7792-olbg2` · **Updated:** 2026-10-21 06:05 UTC

| # | Task | Status | Owner | File scope |
|---|---|---|---|---|
| 1 | Repo recon + coordination | done | `arena/42fb7792-olbg2` | `COORDINATION.md`, `research/*` |
| 2 | OLBG reverse engineering (taxonomy, ids, URL schema, markets, irregularities) | done | `arena/42fb7792-olbg2` | `research/olbg-reverse-engineering.md` |
| 3 | Data collection: fixtures per included sport | done (partial coverage) | `arena/42fb7792-olbg2` | `data/inputs/*`, `research/collection-log.md` |
| 4 | Official-source verification of fixtures + inputs | done (see coverage) | `arena/42fb7792-olbg2` | `data/inputs/*`, `data/sources.json` |
| 5 | Line origination model + confidence rules | done | `arena/42fb7792-olbg2` | `scripts/model.py`, `scripts/config.py`, `METHODOLOGY.md` |
| 6 | High-confidence written predictions | done (4) | `arena/42fb7792-olbg2` | `data/predictions.json` |
| 7 | Dashboard build (landing, sport pages, flagged, methodology, sources) | done | `arena/42fb7792-olbg2` | `index.html`, `sports/*`, `assets/*`, `scripts/build_site.py` |
| 8 | Integration: merge with prior work, verify, publish, PR | done | `arena/42fb7792-olbg2` | shared outputs |

## Claims log

| When (UTC) | Session | Action |
|---|---|---|
| 2026-10-21 05:10 | `bfeb6335` | First audit; claimed `scripts/**`, `data/**`, `site/**`. |
| 2026-10-21 05:20 | `e4f35827` | Re-audit claim; merged as PR #6. |
| 2026-10-21 05:12 | `arena/42fb7792-olbg2` | **Not aware of the other sessions at the time** (repo appeared empty; the other branches were not yet on `main`). Claimed research + data + model scopes; worked on `arena/42fb7792-olbg2`. |
| 2026-10-21 06:00 | `arena/42fb7792-olbg2` | Detected divergence: `main` had advanced to `d9f6376` with the `site/` pipeline. Stopped, merged `origin/main` into the branch, resolved conflicts without editing any `site/**`, `scripts/build.py`, `data/events.json` or `tests/**` file. |
| 2026-10-21 06:05 | `arena/42fb7792-olbg2` | Dashboard published at repo root; prior audit site preserved at `/site/` and linked from the navigation as "Prior audit". |

## Conflict resolution log (2026-10-21 06:00Z)

| File | Conflict | Resolution |
|---|---|---|
| `index.html` | Prior session: redirect to `site/index.html`. This session: dashboard. | Root becomes the new dashboard. The prior site is **not modified** and remains at `site/index.html`; the dashboard adds a "Prior audit" navigation link to it. |
| `README.md` | Two different project descriptions. | Rewritten to describe both layers, both build pipelines and the shared integrity rules. |
| `COORDINATION.md` | Two different boards. | This merged board: earlier sessions preserved, current session appended, merge logged. |
| `site/**`, `scripts/build.py`, `data/events.json`, `tests/**`, `.github/workflows/pages.yml` | — | **Untouched.** `git diff origin/main -- site scripts/build.py data/events.json tests .github` is empty on this branch, so the prior CI check (`build.py` + `git diff --exit-code -- site`) still passes. |

## Verification performed (this session)

| Source family | Verified what | Result |
|---|---|---|
| NBA.com games page (2026-10-21) | 11 fixtures, tip times, game ids | 11 published; 1 game id blank (truncated capture) |
| NBA.com standings 2025-26 | 30 records + home/road splits | Prior used; 0 current-season games → confidence capped |
| NHL score API | 21 Oct (2) + 22 Oct (11 of 12) | 12 published, 1 fixture omitted (away team truncated) |
| NHL stats REST team summary | 32 teams GP/W/L/OTL/GF/GA | 31 complete; Sharks goals blank → their game not originated |
| URC match centre + table | 8 Round 4 fixtures + 16-team table | All 8 published and lined |
| ICC match list | AFG v BAN ODI, NZ v IND T20I | Fixtures published, no line (ranking table empty) |
| WST matches | NI Open R1 results + 2 scheduled R2 matches | Both R2 matches had started by capture; not published |
| MLB stats API | 21 Oct schedule | 0 games — no MLB rows |

## Handoff / open work for any later session

1. **Do not hand-edit** `data/matches.json`, `index.html` or `sports/*.html` — regenerate with
   `python3 scripts/model.py && python3 scripts/build_site.py`.
2. **Do not hand-edit** `site/**` — it is generated by `scripts/build.py` and checked by CI.
3. Highest-value additions, in order:
   - capture the missing NHL game on 22 Oct (Seattle home) and the Sharks' goal totals → +2 lines;
   - read ATP rankings + PDC Order of Merit from a rendered page → unlock tennis and darts;
   - verify Gaelic football club fixtures on county-board sites;
   - survey the eight sports never captured (Handball, Volleyball, Golf, Motor Racing, Greyhounds, eSports,
     Aussie Rules, Rugby League).
4. New findings must be appended to `data/flagged.json` and `data/sources.json`, then re-published.

## Final state of this session's deliverable

| Item | Value |
|---|---|
| Verified fixtures | 33 (NHL 12, NBA 11, URC 8, ICC 2) |
| Lines originated | 30 — money line on all, puck line + total on 11 NHL, spread + total on 11 NBA, handicap + total on 8 URC |
| High-confidence picks | 4, all NHL money lines, with 92–99-word write-ups |
| Flagged | 19 items (F01–F19); 14 blank values explicitly listed |
| Uncovered sports | 13 of the 17 in scope, each named on the flagged page with the reason |
| Live dashboard | https://buffedlizard55-lab.github.io/OLBG2/ |
| Live evidence desk | https://buffedlizard55-lab.github.io/OLBG2/site/index.html |

**What "complete" does and does not mean here.** Every fixture that was captured is published with an official
source on the row, and every market that could be derived from a verified input was originated. The list is not
an exhaustive inventory of OLBG's slate: thirteen sports were never captured, and six OLBG events that were seen
(tennis, darts, snooker, Gaelic football, Top 14, Pro D2) could not be verified against a governing-body source
inside the window. Those are on the flagged page rather than silently dropped or quietly guessed.

## Environment facts (recorded for other sessions)

- Sandbox HTTP egress is restricted to GitHub hosts. General web pages and league APIs are **not** reachable from
  `bash`. Use the agent `fetch_page` / `web_search` tools instead.
- GitHub Actions cannot be dispatched from this sandbox (`/actions/permissions` → 403, dispatch → 404), so no
  interactive collector can run. Data must be captured with the agent tools and committed with provenance.
- GitHub Pages serves `main` at the repository root in legacy mode. The dashboard therefore lives at the root and
  the prior site at `/site/`.

## Publish record

| Item | Value |
|---|---|
| Integration branch | `arena/42fb7792-olbg2` |
| Dashboard build check | `python3 scripts/build_site.py` → 9 pages, 33 fixtures, 4 predictions, no broken links |
| Prior pipeline check | `python -m unittest discover -s tests -v` → 6 tests pass; `python scripts/build.py` → no `site/` diff |
| Pull requests | **PR #7** (dashboard release) · **PR #9** (per-date provenance) · **PR #12** (NBA citation repair + source register gate) · **PR #13** (F19 disclosure) · **PR #14** (capture window + coverage statement) · **PR #16** (final ledger) · **PR #17** (removed an implied market comparison from the Wild write-up) |
| Merge result | all five merged to `main`; current tip `main` after PR #14 |
| First merge | PR #7 merged 2026-10-21 05:21:08Z · merge commit `3778896` |
| Merge conflict | Yes — resolved by merging `origin/main` (`d9f6376`) into the branch first; no prior work discarded (see log above) |
| Deploy run | `Validate Pages content` 39549059975 success · `pages build and deployment` 39549058659 success |
| Live check | `https://buffedlizard55-lab.github.io/OLBG2/` renders the dashboard; `/site/index.html` renders the prior audit site |
| Follow-up | PR #9 — per-date NHL provenance (each NHL row now cites its own `…/score/YYYY-MM-DD` feed) |
| Follow-up | PR #12 — repaired the NBA citations the PR #9 helper mangled, and added a build gate requiring every citation to match `data/sources.json` |
| Follow-up | PR #13 — F19 goal-convention disclosure, README counts, this log. Deploy runs 39549662975 / 39549662117 success, live re-checked |
| Follow-up | PR #14 — capture window corrected to 05:12–05:25 UTC (it had read 05:45) and the final coverage statement added. Deploy runs 39549864859 / 39549864671 success, Pages status `built` |
| Follow-up | PR #16 — ledger of PRs and deploy ids. PR #17 — reworded the Minnesota prediction so it no longer implies a market comparison. Deploy runs 39550115718 / 39550115404 success |
| Cross-session check | PR #11 (`db99ed90`) independently recaptured the NHL slate: fixture ids, matchups, dates, start times and last-ten records matched, and its two overlapping selections agreed. Its goal-convention finding (shootout goal counted by nhl.com/standings, excluded by the stats API) is now disclosed as **F19** in `data/flagged.json` and in METHODOLOGY.md §2. |

### Post-merge note

Verifying the live site exposed one provenance defect: all twelve NHL rows linked to the 21 October score feed,
including the eleven games on 22 October. The data itself was correct (captured from the 22 October feed during
collection), but the citation was not line-accurate. Fixed in PR #8 by deriving the URL from each fixture's own
date; the site was rebuilt and re-verified. No prices, picks or confidence grades changed.


## Session `4a778bb7` — evidence desk v2 and integration (2026-10-21 05:30–06:30 UTC)

**Branch:** `arena/4a778bb7-olbg2` (the hosting environment fixes one branch per session; `session-*` branches
cannot be created here). Claim committed and pushed as `b40eb6d` before implementation work.

| Task | Status | Owner | File scope |
|---|---|---|---|
| Evidence desk v2: engine, data, tests, site rebuild | done | `4a778bb7` | `scripts/engine.py`, `scripts/build.py`, `data/desk/**`, `site/**`, `tests/**` |
| Integration with the root dashboard (merged in `3778896`, then `75d6a40`) | done | `4a778bb7` | `README.md`, `COORDINATION.md`, `scripts/build_site.py` (nav label only) |

### What this session added

- `scripts/engine.py` — originated-line engine. NHL: goal difference per game shrunk toward the league mean by 12
  games, +0.25 home edge, logistic scale 1.2, no-vig American prices, 1.5 puck line, half-goal totals with σ 1.7.
  NBA: explicit baseline (league-average clubs, 2.5-point home court, no total).
- `data/desk/` — meta (parameters, exclusions, limits), 32-club NHL standings inputs, 25 fixtures, 4 predictions,
  22-sport coverage registry, 8 flags, and an allow-listed source registry.
- `site/` — dashboard, pick sheet with confidence filter, per-sport pages, methodology, source registry and a
  Flagged for Review page. 28 tests; `scripts/build.py` fails on any unregistered or non-official source.
- Verified: 25 fixtures (14 NHL across Oct 21–22, 11 NBA on Oct 21), 64 markets, 4 high-confidence picks
  (BUF, BOS, DAL, MIN money lines), no unverified value filled in.

### Merge and conflict resolution

`main` advanced twice while this branch was open (`3778896` after PR #7, then `75d6a40` after PR #9). Each time the
branch was merged forward; nothing from the other session was discarded.

| File | Conflict | Resolution |
|---|---|---|
| `scripts/build.py`, `tests/test_build.py`, `site/**` | Two different `site/` pipelines | This branch's desk pipeline kept; the old two-fixture builder and its tests are superseded. `data/events.json` retained unchanged for provenance. |
| `scripts/model.py` | Both sessions created it | The other session's model kept at `scripts/model.py` (used by `build_site.py`); this branch's engine renamed to `scripts/engine.py`. |
| `data/sources.json`, `data/flagged.json` | Both sessions created them | Root dashboard files kept in place; the desk versions moved to `data/desk/`. |
| `index.html`, `picks.html`, `flagged.html`, `sources.html`, `methodology.html`, `sports/**`, `assets/**` | Root dashboard vs the old redirect/site | Root dashboard kept as the landing page. |
| `README.md`, `COORDINATION.md` | Two project descriptions | Merged: the other sessions' records preserved above, this section appended. |
| `scripts/build_site.py` | — | Single edit: nav label `Prior audit` → `Evidence desk v2`, plus a footer link. Rebuilt; page output otherwise byte-identical. |

Both pipelines were run after the merge: `scripts/build_site.py` → 9 pages, 33 fixtures, 4 predictions, no broken
links; `python -m unittest discover -s tests` → 28 tests pass; `scripts/build.py` → 25 fixtures, 4 high / 5 medium /
16 low, regenerating `site/` with no diff. `scripts/model.py` writes a `generated_at` timestamp into
`data/matches.json`, so re-running it always produces a one-line diff; the committed file was restored after the
check and that non-determinism is logged here.

### Irregularities carried forward

All eight desk flags remain open and published at `/site/flagged.html`: the NHL internal inconsistency, the OLBG
19:37 vs 7:30 PM EDT discrepancy, the eleven unverified eligible sports, the NBA baseline, the MLB zero-game date,
blank venues and the missing 2025-26 NBA bulk baseline. The root dashboard's own flags remain published at
`/flagged.html`.


## Publish record — session `4a778bb7`

| Item | Value |
|---|---|
| Pull request | https://github.com/buffedlizard55-lab/OLBG2/pull/8 |
| Merge commit | `5f2afc8` (merged 2026-10-21T05:23:45Z, no approval wait) |
| CI on the PR | `validate` check passed (tests + `scripts/build.py` + no `site/` diff) |
| CI on `main` | run 39549310277 succeeded |
| GitHub Pages | build 1301715319 status `built`; `pages-build-deployment` run 39549309155 succeeded |
| Live entry points | `/` root dashboard (33 fixtures) · `/site/index.html` evidence desk v2 (25 fixtures) · `/site/flagged.html` · `/flagged.html` |

Open irregularities do not block the merge and remain published on both Flagged for Review pages, each with the
source link that raised it. The only unresolved data disagreements are the NHL games-played inconsistency, the OLBG
19:37 vs 7:30 PM EDT times, the eleven unverified eligible sports and the absence of an official bulk 2025-26 NBA
baseline.

---

## Independent verification and second integration — session `db99ed90` (2026-10-21)

### Claim and what happened

Session `db99ed90` claimed T1–T7 on `arena/db99ed90-olbg2` at 05:14 UTC (`6036dd1`) and built a complete second layer:
14 verified NHL fixtures from the official game-centre feed, a Poisson model (`olbg-desk-poisson-v1`), 42 prices,
6 high-confidence narratives and a 16-category coverage board, published to `/site/`.

While that work was in progress, `main` moved twice: `3778896` (PR #7, session `42fb7792`) and `5f2afc8` (PR #8,
session `4a778bb7`). The second merge replaced the `/site/` layer with a stricter pipeline — `data/desk/*`,
`scripts/engine.py`, 28 tests, `site/data/lines.json` — and independently collected **the same 14 NHL fixture ids**
plus 11 NBA games.

**Resolution: `main`'s pipeline wins.** It is better tested (28 checks vs 23), it publishes machine-readable output, and
it covers more sport. This branch's parallel desk is therefore **not** merged over it. It is preserved as an
independent capture under `research/nhl-desk-db99ed90/` (`events.json`, `poisson.py`, `report.py`) so its provenance
survives without shipping a second competing site.

### Merge resolution log (`main@5f2afc8` → this branch)

| File | Resolution |
| --- | --- |
| `scripts/build.py`, `scripts/engine.py`, `data/desk/**`, `site/**`, `tests/test_build.py` | **Theirs.** No line of the newer pipeline was reverted. |
| Root pages (`index.html`, `picks.html`, `flagged.html`, `methodology.html`, `sources.html`, `sports/**`) | **Theirs**, regenerated afterwards. |
| `scripts/model.py` | **Theirs** (dashboard/NBA model). This branch's model lives only in `research/`. |
| `README.md` | **Theirs.** |
| `COORDINATION.md` | Theirs preserved above; this section appended. |
| `data/desk/flagged.json` | One item **added** (see below). Nothing removed or rewritten. |

### Verification performed against official sources

Method: this session had captured the same 14 NHL fixtures from `api-web.nhle.com/v1/gamecenter/{id}/right-rail`
and `api.nhle.com/stats/rest/en/team/summary` before the merge, so the published dataset could be checked row by row
against an independent official capture rather than against itself.

| Check | Result |
| --- | --- |
| Fixture ids, matchups, dates, OLBG event URLs | 14/14 identical to this session's independent capture |
| Start times | 14/14 identical (`7:30 PM EDT` = `23:30Z`, etc.) |
| Team goal totals | **17 apparent mismatches, all reconciled** — see finding below |
| Last-ten records | 28/28 team-appearances identical |
| Selections on overlapping games | `nhl-2026020152` Buffalo and `nhl-2026020154` Boston match this session's model picks |
| Build + tests | `build.py` → 25 fixtures, 9 flagged; 28 tests pass; `build_site.py` → 9 pages, no broken links |

### Finding added to the flagged page (main later recorded this as F19)

**`flag-goal-convention` — official NHL sources disagree on goals for/against.**
`nhl.com/standings` counts the shootout-deciding goal; the stats API's `goalsFor` / `goalsAgainst` does not.
Examples: Ottawa 24 GF (standings) vs 22 (API) over the same 9 games, with two shootout wins; Buffalo 34 GA vs 33,
with one shootout loss; Seattle 39 vs 37, with two shootout wins. Every one of the 17 apparent mismatches is fully
explained by this convention, so **the published data is correct for its stated source** — but the model's goal rates
are up to ~0.2 per game higher than the stats-API view would give. The gap is definitional, not an error, and is now
disclosed on the flagged page and in the site's machine-readable output.

Secondary observation on the existing `flag-olbg-time` item: two captures of the same OLBG pages produced `19:37`
and `00:37` for the same fixtures. Both are the same instant in different viewer timezones (`23:37Z`), seven minutes
after the NHL's `23:30Z`, which is consistent with OLBG rendering local time and not stating a zone. No conversion is
applied anywhere.

### Publish record

| Item | Value |
| --- | --- |
| Integration branch | `arena/db99ed90-olbg2` |
| Pre-merge checks | 28 tests pass; `build.py` → 25 fixtures, 9 flags; `build_site.py` → 9 pages, no broken links |
| Pull request | [#11](https://github.com/buffedlizard55-lab/OLBG2/pull/11) — "Independent verification of the NHL dataset + disclosed goal-convention finding" |
| Merge result | merged to `main` (merge commit); PR is `CLEAN`/`MERGEABLE` at merge time and `validate` CI passed on both the head commit and the merge |
| Pages deploy | `pages-build-deployment` run completed `success`; `gh api repos/.../pages` → `status: built`, `build_type: legacy`, source `main:/` |
| Live URL | https://buffedlizard55-lab.github.io/OLBG2/ — served `flagged.html` with F19 visible, confirmed after deploy |
| Follow-up correction | F19 and `METHODOLOGY.md` said the model used the stats-API view; `data/desk/nhl_teams.json` (`source_id: nhl-standings`) and the captured totals show it uses the standings view. Wording corrected to match the data; no number or price changed. |

## Claim — session `db99ed90` (2026-10-21 05:58 UTC)

**Task.** Complete the NHL slate. The published dataset carries 12 of the league's 14 games in this window: the two
on 21 October plus ten of the twelve on 22 October. The last two (`2026020164` UTA@SEA, `2026020165` DET@VAN) were
never captured, and San Jose's goals for/against were left blank, which is why F01 and F02 sit on the flagged page.
Both gaps are now closable from official feeds.

**File scope (claimed, exclusive).**

| Path | What changes |
|---|---|
| `data/inputs/fixtures.json` | add the two missing NHL fixtures |
| `data/inputs/nhl_teams.json` | complete the Sharks row from the official team summary |
| `data/matches.json` | regenerated by `scripts/model.py`, never hand-edited |
| `data/predictions.json` | pick write-ups for any new high-confidence game |
| `data/flagged.json`, `data/sources.json` | F01/F02 closed with the evidence that closed them; new findings appended |
| `index.html`, `sports/*.html` | regenerated by `scripts/build_site.py` |
| `COORDINATION.md`, `METHODOLOGY.md`, `README.md` | this board and the counts they quote |

**Not in scope.** `data/desk/**`, `data/inputs/{nba_teams,urc}.json`, `scripts/build.py`, `site/**`, `tests/**` —
owned by the earlier audit and desk sessions and untouched here.

**Overlap check.** The previous owner (`arena/42fb7792-olbg2`) marked every task `done` and wrote a handoff section
naming exactly this work as the highest-value addition, so this is a handoff, not a takeover. Nothing in the scope
has been modified since `6c5c2dd`; claim committed before any edit.

## Completion — NHL slate finished, F01 and F02 closed (2026-10-21 06:30 UTC)

Session `db99ed90`, branch `arena/db99ed90-olbg2`, working inside the scope claimed above. `data/desk/**`, `site/**`,
`data/inputs/{nba_teams,urc}.json`, `scripts/build.py` and `tests/**` were not touched.

### What changed

| Change | Detail |
|---|---|
| Two NHL fixtures added | `2026020164` Utah Mammoth @ Seattle Kraken (Climate Pledge Arena) and `2026020165` Detroit Red Wings @ Vancouver Canucks (Rogers Arena), both 2026-10-23T02:00:00Z, both from the clubs' official schedule endpoints |
| Sharks row completed | `teamId=28`: 10 GP, 5-4-1, 26 GF, 34 GA, 11 points — the stored row had been a 9-game snapshot with empty goal columns |
| Lines originated | 14/14 NHL games now carry money line, puck line and total (was 11/14) |
| Flags | F01 and F02 moved from the open list to a new **Closed since the first capture** section, with the source that closed each and the closing time. F20 added; F12 rewritten with new evidence |
| Sources | S27 (Seattle club schedule), S28 (Vancouver club schedule), S29 (team-summary teamId filter), S30 (OLBG NHL league page) |

### Verification of the correction

| Check | Result |
|---|---|
| 22 October game count | `api-web.nhle.com/v1/schedule/2026-10-22` → `numberOfGames: 12`; the first capture held 10, not the 11 its own note claimed |
| Recovered fixtures | `club-schedule-season/SEA` and `/VAN` both list `startTimeUTC` 2026-10-23T02:00:00Z with the venues above; ids match the score-feed numbering |
| Sharks totals | 26 GF / 10 GP = 2.60 and 34 GA / 10 GP = 3.40, exactly the per-game rates returned in the same payload — an internal cross-check, not a derived value |
| Other 31 team rows | unchanged and still reproduce the previously published rates (VGK 41/10 = 4.10, CGY 17/8 = 2.13, VAN 51/11 = 4.64 …) |
| Build | `model.py` → 35 fixtures, 33 originated, 4 high, 10 medium, 19 low; `build_site.py` → 9 pages, 35 fixtures, 4 predictions, no broken links; 28 desk tests pass |
| Determinism | `build_site.py` and `build.py` are byte-identical on re-run; `model.py` writes a fresh `generated_at` only |

### New finding while closing F01

OLBG's NHL pages list **two** of the fourteen NHL games in the window — the 21 October pair — and none of the twelve on
22 October, which is confirmed by the league feed. The 12 rows therefore carry no OLBG event link rather than a
constructed one; this is recorded as F20. A second fetch of the same page rendered `19:37` where the first rendered
`00:37` for the same 23:30Z face-off, which proves the timezone finding (F12) rather than merely suggesting it: OLBG
renders in the viewer's zone and states none.

### Publish record

| Item | Value |
|---|---|
| Branch | `arena/db99ed90-olbg2` |
| Pre-merge checks | 28 tests pass · `build.py` → 25 fixtures, 9 desk flags · `build_site.py` → 9 pages, 35 fixtures, 4 predictions, 0 broken links · generated output committed, so CI's `git diff --exit-code` is clean |
| Pull request | recorded below |
| Merge | recorded below |
| Pages deploy | recorded below |

