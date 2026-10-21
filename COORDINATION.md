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

### Publish record — PR #19 (NHL slate)

| Item | Value |
|---|---|
| Pull request | [#19](https://github.com/buffedlizard55-lab/OLBG2/pull/19) — "Complete the NHL slate: 14/14 games, F01 and F02 closed" |
| Merge | merged to `main`, merge commit `c828e53`, after one sync merge (`5bcb0ee`) because PRs #16–#18 landed while CI ran. Only `picks.html` conflicted, and it was resolved by regenerating from the merged data rather than hand-editing |
| Deploy | `Validate Pages content` 39550395204 success · `pages build and deployment` success · `gh api .../pages` → `built` |
| Live check | `sports/ice-hockey.html` renders Utah @ Seattle with all six prices and the three Sharks markets; `flagged.html` renders the closed-items section |

### Coverage survey — handball and volleyball (2026-10-21 06:45 UTC)

`F09` said eight sports "were not surveyed". Two of them now have been, and the result is a finding rather than a
silence:

| Sport | What OLBG lists | Why nothing is published |
|---|---|---|
| Handball | ≥15 events on the first page segment, mostly EHF Champions League on 21–22 Oct (Zagreb v PSG 12053, Veszprem v Fuchse Berlin 12055, Nantes v Vardar 12050, Kolstad v Magdeburg 12048), plus Swedish and Danish league games | Hub groups everything under `All Handball / All Events`, names no competition, and no official EHF fixture list or table could be read in the capture |
| Volleyball | ≥15 events: Polish PlusLiga, German Bundesliga, Italian women's Serie A1, Dutch and Finnish women's fixtures; markets are match winner and set score | Same: no competition label, no official league table captured |

Both are recorded as F21 and F22 with the hub URL as their source. `F09` now names the six sports that genuinely were
not opened: Golf, Motor Racing, Greyhounds, eSports, Aussie Rules, Rugby League. The client-side table counts events
"at least fifteen" rather than a total, because the hubs are paged and the full list was not enumerated — a number we
did not verify is not a number we publish.

### Current state of the deliverable

| Item | Value |
|---|---|
| Fixtures | 35 verified (NHL 14, NBA 11, URC 8, ICC 2) |
| Lines originated | 33 — all NHL games now carry money line, puck line and total |
| High-confidence picks | 4, each with a sourced write-up of 92–110 words |
| Review queue | 20 open + 2 closed, every row with a source link |
| Sports covered | 4 of 17 with published fixtures; handball and volleyball surveyed without publication; 6 not opened |
| Build | 9 pages, 0 broken links, 28 desk tests green, generated output byte-stable |

## Sync merge — documentation correction (2026-10-21 06:55 UTC)

Session `db99ed90`. **No code, data or generated page changed in this merge.** `git diff origin/main --stat` after
resolution is `COORDINATION.md` and `README.md` only.

| File | Conflict | Resolution |
|---|---|---|
| `COORDINATION.md` | Theirs had accumulated the full board while this branch carried its own appended sections | Theirs kept verbatim; this section appended |
| `README.md` | Both sides described the `site/` layer, and both had a stale sentence about `data/events.json` | Theirs kept, two corrections applied (see below) |
| `data/events.json`, `scripts/poisson.py`, `scripts/report.py`, `site/**`, `data/desk/**` | No real conflict — both sides already carried the same 14-game capture from PR #11 | Taken unchanged; nothing deleted or reverted |

**Corrections applied to the README.**

1. The desk layer's flag count was eight; `data/desk/flagged.json` holds **nine** (the eighth plus
   `flag-goal-convention` added in PR #11).
2. The integration note claimed `data/events.json` was "the older two-fixture audit". It is in fact the 14-game NHL
   capture with the per-team form, the last-ten results and the 16-category coverage board. The audit data is in
   git history, not in that file. The paragraph now says what the file actually is and how it relates to
   `data/desk/*.json`.

**State verified after the merge (all four gates).**

| Gate | Result |
|---|---|
| `python3 scripts/model.py` | 35 fixtures, 33 originated, 4 high / 10 medium / 19 low |
| `python3 scripts/build_site.py` | 9 pages, 35 fixtures, 4 predictions, 0 broken links |
| `python3 scripts/build.py` | 25 desk fixtures, 9 flags, no `site/` diff |
| `python3 -m unittest discover -s tests` | 28 pass |

### Publish record

| Item | Value |
|---|---|
| Pull request | recorded below |
| Merge | recorded below |
| Deploy | recorded below |

## Session `db99ed90` — independent verification and second integration (2026-10-21 ~05:30–07:10 UTC)

**Claim (written to this board and pushed before any edit).** `data/events.json`, `scripts/poisson.py`,
`scripts/report.py`, `data/desk/flagged.json` (corrections only), `README.md`, `METHODOLOGY.md`, this file.

### What was done

| # | Task | Result |
|---|---|---|
| 1 | Capture all 14 NHL games on 21–22 October from official feeds, independently of the published dataset | `research/nhl-desk-db99ed90/` |
| 2 | Poisson goal model over that capture | 14 fixtures, 6 high / 3 medium / 5 low |
| 3 | Row-by-row comparison with the published desk | 14/14 ids, venues, times, OLBG URLs; 28/28 last-ten records; 5/5 selections |
| 4 | Explain the goal-total differences | Shootout convention — every delta equals the club's SOW/SOL count (table in `research/verification-2026-10-21.md`) |
| 5 | Disclose the finding on the live site | `flag-goal-convention` in `data/desk/flagged.json`, now carrying the 17-of-32 measurement |
| 6 | Integration | Merged `origin/main`, kept the desk pipeline, rebuilt, tested, published |

### Verification table

| Check | Result |
|---|---|
| Fixture ids, matchups, dates, venues | 14/14 identical |
| Start times | 14/14 identical (`7:30 PM EDT` = `23:30Z`) |
| OLBG event URLs | 14/14 identical |
| Last-ten records | 28/28 identical |
| Team goal totals | 17/32 differ, all explained by shootouts; 16 clubs without a shootout identical |
| Overlapping selections | 5/5 agree on side |
| Build | 25 fixtures, 9 desk flags, no `site/` diff; 28 desk tests pass |

### Irregularity recorded, not silently corrected

`flag-goal-convention` — `nhl.com/standings` counts the shootout-deciding goal in GF/GA; the stats API does not.
The desk cites the standings view, so its rates sit up to ~0.2 goals per game above the API view. The flag now
quotes the measured effect (17 of 32 clubs, maximum 2 goals) instead of two examples.

### Cross-scope request left open

`nhl-2026020156` (San Jose at Ottawa) has no line because the stats table has no Sharks goal columns. The
independent capture has them (2.60 GF/GP, 3.40 GA/GP over 10 games, which is 26/34 in the API and 27/35 on
`nhl.com/standings`). Whoever next reads a rendered standings page can supply the row and gain a 26th lined fixture.

### Publish record

| Item | Value |
|---|---|
| Pull request | recorded below |
| Merge | recorded below |
| Deploy | recorded below |

## Publish ledger — all four PRs from session `db99ed90` (closes the "recorded below" rows)

| PR | Title | Merge commit | Validate run | Pages run | Live check |
|---|---|---|---|---|---|
| [#19](https://github.com/buffedlizard55-lab/OLBG2/pull/19) | Complete the NHL slate: 14/14 games, F01 and F02 closed | `c828e53` | 39550395204 | 39550393822 | `sports/ice-hockey.html` shows Utah @ Seattle with six prices; `flagged.html` shows the closed-items section |
| [#20](https://github.com/buffedlizard55-lab/OLBG2/pull/20) | Survey handball and volleyball on OLBG | `42e16f7` | 39550663818 | 39550663101 | `flagged.html` shows F21/F22 and "20 open items · 2 closed" |
| [#21](https://github.com/buffedlizard55-lab/OLBG2/pull/21) | Correct two stale README statements | `9616757` | 39550881881 | 39550881480 | root pages unchanged; README corrected |
| [#22](https://github.com/buffedlizard55-lab/OLBG2/pull/22) | Independent audit of the NHL dataset; shootout effect measured | `e3cfb1f` | 39551094468 | 39551093843 | `site/flagged.html` shows the 17-of-32 measurement in `flag-goal-convention` |

Every merge was made with `gh pr merge --merge` after `mergeStateStatus` reached `CLEAN`; three of the four needed a
sync merge first because `main` advanced while CI ran. In each sync the other sessions' files were taken as-is and only
generated pages were regenerated — `git diff origin/main` before each merge touched nothing outside this session's
scope.

### Final state

| Layer | Fixtures | Lines | Predictions | Review queue |
|---|---|---|---|---|
| Root dashboard (`/`) | 35 (NHL 14, NBA 11, URC 8, ICC 2) | 33 | 4 | 20 open + 2 closed |
| Evidence desk (`/site/`) | 25 (NHL 14, NBA 11) | 64 markets | 4 | 9 open |



---

# Session `ca1d5677` — sport-coverage survey layer (appended)

**Session ID:** `ca1d5677` · **Branch:** `arena/ca1d5677-olbg2` · **PR:** #25 · **Updated:** 2026-10-21 06:40 UTC

This session started from `1056f6a` while `main` still looked empty, built a full survey layer,
and only discovered the three merged sessions when its own PR reported *not mergeable*. It then
stopped, read this board, and relocated every one of its files into a namespace that does not
overlap any file the prior sessions own. **No file owned by `bfeb6335`, `e4f35827` or
`arena/42fb7792-olbg2` was modified**, with the single documented exception of appending the
sections you are reading now to this shared board and an append-only pointer section at the end
of `README.md`.

## Claim

| # | Task | Status | Owner | File scope (non-overlapping) |
|---|---|---|---|---|
| S1 | Repo baseline audit at `1056f6a` | done | `ca1d5677` | `REPO_REVIEW.md` |
| S2 | OLBG sport taxonomy + include/exclude decisions | done | `ca1d5677` | `data/survey/sports.json` |
| S3 | **Survey the sports never captured** (prior board's open handoff item 3, fourth bullet) | done | `ca1d5677` | `data/survey/events/*.json`, `scripts/survey_inventory.py` |
| S4 | Originate lines from verified official inputs | done (11 of 130) | `ca1d5677` | `data/survey/lines.json`, `scripts/survey_lines.py` |
| S5 | Picks + confidence with an official-divergence guard | done | `ca1d5677` | `data/survey/picks.json`, `scripts/survey_analyse.py` |
| S6 | High-confidence written predictions | done (2) | `ca1d5677` | `data/survey/predictions.json` |
| S7 | Survey sub-site (10 pages + 15 sport pages) | done | `ca1d5677` | `survey/**`, `scripts/survey_build.py` |
| S8 | Verification gate | done, all green | `ca1d5677` | `scripts/survey_verify.py` |
| S9 | Integration with the three merged sessions | done | `ca1d5677` | this file, `README.md` (append-only) |

## What this layer adds to what is already published

The prior board's open item was that *"neither exhaustive inventory nor original prices could be
responsibly verified"*, and its handoff asked a later session to *"survey the eight sports never
captured (Handball, Volleyball, Golf, Motor Racing, Greyhounds, eSports, Aussie Rules, Rugby
League)"*. That is exactly what S3 did, and it went further:

| | Prior sessions (root dashboard) | This layer (`/survey/`) |
|---|---|---|
| Fixtures inventoried | 33 (NHL 12, NBA 11, URC 8, ICC 2) | **130** across all 15 in-scope sports |
| Sports with events | 4 | 12 (plus 3 confirmed to have zero OLBG events) |
| Handball / Volleyball / Golf / Motor Racing / Rugby League / eSports / Aussie Rules / Darts / Snooker / Tennis / Cricket / Baseball | never captured | **surveyed**, with per-event provenance |
| Lines originated | 30 | 11 (different fixtures; no duplication) |
| High-confidence predictions | 4 (NHL money lines) | 2 (Top 14, ICC ODI) |
| Flags | 19 (F01–F19) | 21 (F-01–F-21) |

The two layers cover **different fixtures**, so nothing is duplicated.

## New findings contributed by this layer

- **F-06** OLBG displays fixture times in **US Eastern**, not UK time. Proved by reconciling
  OLBG's `07:30` for Afghanistan v Bangladesh against the official `11:30 GMT` start. This
  affects how any session reads OLBG `listed_time` values, including the prior board's
  "tip times" captured from NBA.com.
- **F-13** OLBG's own F1 calendar row mixes three events: *"Round 16, 4 October, Bahrain Grand
  Prix, Sepang International Circuit, Malaysia"*.
- **F-02** OLBG event pages render bookmaker prices client-side; the served HTML has an empty
  `WIN @` placeholder. Confirms the prior board's note that prices must come from elsewhere.
- **F-05** OLBG has **no** UFC, MMA, Hurling or Specials sport node, so four of the brief's ten
  exclusions are vacuous. Its taxonomy is exactly 22 sports.
- **F-03 / F-04** Greyhounds and Gaelic Football are not named in the brief; both excluded here
  (racing family / football code). Motor Racing included. Needs confirmation — and note the prior
  board lists Greyhounds and Gaelic football among sports to survey, so the two layers currently
  take opposite positions on whether Gaelic football is in scope.
- **F-21** `PUT /repos/:owner/:repo/pages` returns **403 Resource not accessible by integration**
  for this token, so the Pages source cannot be repointed from `/` to `/docs`. Independently
  confirms the prior board's environment note that *"GitHub Pages serves `main` at the repository
  root in legacy mode"*.
- **F-12** `https://worldsnooker.com/rankings` returns **HTTP 500**; secondary sources disagree on
  the world number one (Trump 1st in September, 3rd by 4 October). Relevant to the prior board's
  "read ATP rankings + PDC Order of Merit from a rendered page" handoff item: **the PDC page is
  cookie-walled and the ATP page is JavaScript-rendered**, which is why neither unlocked here.

## Conflict resolution log (2026-10-21 06:35 UTC)

| File | Conflict | Resolution |
|---|---|---|
| `COORDINATION.md` | add/add — two different boards | **Theirs taken verbatim**; this session appended below the existing content. Nothing removed. |
| `README.md` | modify/delete — this session had renamed it to `SURVEY_README.md`, prior session modified it | **Theirs restored intact**, then a clearly delimited append-only section added at the end pointing to `/survey/`. Their original text is unmodified above it. |
| `index.html`, `flagged.html`, `picks.html`, `methodology.html`, `sports/*`, `assets/*`, `scripts/build_site.py`, `data/matches.json`, `data/predictions.json`, `data/flagged.json`, `data/sources.json`, `tests/**`, `site/**`, `.github/**`, `research/**`, `.gitignore`, `.nojekyll` | — | **Untouched.** This session relocated its own colliding files into `survey/`, `data/survey/` and `scripts/survey_*.py` *before* merging, so these never conflicted. |

## Verification performed (this layer)

`scripts/survey_verify.py` gates the build and is green: all internal links resolve across 25
pages; all 335 data-table rows carry a source link or an explicit UNVERIFIED badge; all 130
inventory rows carry a provenance URL, listed time, as-of date and retrieval method; all 11
originated lines cite a rating or basis source; every null line cell is explicitly marked
unverified rather than silently blank; both predictions exceed 30 words (143, 133) and every
fact carries a URL; a prediction exists for every high-confidence pick and no other; the
inventory reconciles exactly as 130 = 11 modelled + 119 flagged; flag ids unique; and rebuilding
from the same data is byte-identical.

Official sources used: OLBG sitemap and per-sport listings; ICC team rankings (icc-cricket.com
via cricinfo.com); LNR Top 14 standings, fixture sheet and published fixture probabilities
(lnr.fr / top14.lnr.fr); ESPNcricinfo series pages and scorecards. Retrieved but not usable:
OWGR (retrieved, week 42), ATP (JavaScript-rendered, top 18 only), WTA (JavaScript-rendered),
PDC (cookie-walled), World Snooker Tour (HTTP 500). Full per-source status is on
`survey/verification.html`.

## Request logged for the integration owner (not done here, per the ownership rule)

1. Add a `Survey` link to the root dashboard navigation pointing at `survey/index.html`, so the
   130-event layer is discoverable from `/`. The survey pages already link back to `../index.html`.
2. Decide **F-03**: are Greyhounds and Gaelic Football in scope? The two layers currently differ.
3. Consider merging the two flag registers (`data/flagged.json` F01–F19 and
   `data/survey/flags.json` F-01–F-21) into one numbering scheme on the flagged page.

## Publish record (this layer)

| Item | Value |
|---|---|
| Integration branch | `arena/ca1d5677-olbg2` |
| PR | #25 |
| Build check | `python3 scripts/survey_build.py` → 25 pages, 130 events, 11 lines, 2 predictions, 21 flags |
| Verification gate | `python3 scripts/survey_verify.py` → all checks green |
| Survey URL | https://buffedlizard55-lab.github.io/OLBG2/survey/ |
| Flagged for review | https://buffedlizard55-lab.github.io/OLBG2/survey/flagged.html |

## Merge and deploy ledger (session `ca1d5677`)

| Item | Value |
|---|---|
| PR | <https://github.com/buffedlizard55-lab/OLBG2/pull/25> |
| State | **MERGED** at 2026-10-21T05:57:00Z |
| Merge commit | `6f66d28d1e00c46da81d604a274ed27a710b2e03` |
| Base / head | `main` ← `arena/ca1d5677-olbg2` |
| Pages build | commit `6f66d28`, status **built** at 2026-10-21T05:57:24Z, `error.message: null` |
| Pages source | `build_type: legacy`, `source {branch: main, path: "/"}` — unchanged |
| Dashboard | https://buffedlizard55-lab.github.io/OLBG2/ (prior sessions, untouched) |
| Survey layer | https://buffedlizard55-lab.github.io/OLBG2/survey/ |
| Flagged for review | https://buffedlizard55-lab.github.io/OLBG2/survey/flagged.html |
| Files added to `main` | 58 (all new paths); 2 modified append-only (`COORDINATION.md`, `README.md`) |
| Prior-session artifacts changed | **none** — `git diff origin/main -- site scripts/build.py scripts/model.py scripts/config.py scripts/engine.py tests .github data/matches.json data/flagged.json data/sources.json data/inputs data/desk research index.html flagged.html picks.html methodology.html sports assets .gitignore` is empty |

### Divergence, as required by the conflict protocol

The first `gh pr merge 25 --merge` failed with *"not mergeable: the merge commit cannot be cleanly
created"*. Cause: this session branched from `1056f6a` while `main` had since advanced through PRs
#19–#24. Rather than resolve textual conflicts on generated files, the branch **relocated its own
files first** into `survey/`, `data/survey/` and `scripts/survey_*.py`, then merged `origin/main`
with `-X` untouched. Only two conflicts remained and both were resolved additively:
`COORDINATION.md` (theirs taken verbatim, this session appended) and `README.md` (theirs restored
intact, an append-only pointer section added at the end).

A second hazard was hit and recorded for other sessions: **`git pull --rebase` on this branch
replays the other sessions' 41 commits** because the branch contains a merge commit from `main`.
It was aborted (`git rebase --abort`) with no loss — the correct push had already landed. Prefer
`git merge origin/main` over `git pull --rebase` on any branch that has merged `main`.

Before merging, the prior sessions' CI gate was reproduced locally and passed:
`python3 scripts/build_site.py` regenerates their `index.html`, `sports/*`, `assets/*`, `site/**`
byte-identically (`git diff --exit-code` clean), so the root dashboard is not broken by this merge.

## Claim — session `8103ccb6` (2026-10-21)

| Task | Status | Owner | File scope |
|---|---|---|---|
| Final cross-layer discoverability, evidence-status audit and CI integration | in progress | `8103ccb6` | `scripts/build_site.py`, `scripts/integration_audit.py`, `integration.html`, generated root pages, `tests/test_integration.py`, `.github/workflows/pages.yml`, `research/integration-audit.md`, `COORDINATION.md` |

All earlier claims are complete; no active conflicting claim or open PR was found. Work stays on the Arena-assigned branch `arena/8103ccb6-olbg2` (branch naming is fixed by this environment). Preserve all three data layers; do not claim that structural validation verifies external facts. Integrate the previously requested Survey navigation and expose contradictions/coverage gaps centrally. Official-source spot check: https://api-web.nhle.com/v1/score/2026-10-21 retrieved with fetch_page this turn; two fixtures, PHI@BUF and FLA@OTT at 23:30Z. This is not a re-verification of the full inventory.

### Completion — session `8103ccb6`

Task status: **done** (integration code); external evidence gaps: **needs review**, published on `integration.html`. Detailed scope, source, findings and reproducible commands: `research/integration-audit.md`. Root, desk and survey data were preserved without alteration. Added survey discoverability, cross-layer evidence disclosures, secondary-source narrative review rows, freshness notices, cross-layer local-link checks and survey CI gates. All 33 unit tests pass, all three builds pass, survey structural checks pass, zero broken local links. These are not claims of exhaustive official factual verification. Full automatic current coverage and all-market origination remain unfulfilled and explicitly flagged.

Initial pre-push `git pull --rebase origin arena/8103ccb6-olbg2` reported no remote ref (new branch). Claim was then pushed successfully. No conflict or work loss. Only the fixed Arena branch is used.
## Current session `arena/dd14fcfd-olbg2` (2026-10-21)

| Task | Status | Owner | File scope |
|---|---|---|---|
| Make the existing 130-event survey discoverable from the root dashboard | in progress | `arena/dd14fcfd-olbg2` | `scripts/build_site.py`, generated root HTML, `COORDINATION.md` |

Claim is limited to root-dashboard navigation; the survey dataset and its generated pages remain owned by their prior contribution. Validation will run the survey integrity gate, both site builds, and unit tests.

### Completion — `arena/dd14fcfd-olbg2`

The root dashboard now links directly to `survey/index.html` in both the primary navigation and footer; the link is emitted by `scripts/build_site.py` and appears on all generated root pages. This makes the existing 130-event inventory and its sport/category pages discoverable without changing survey data or prior sources.

Verification: `python3 scripts/build_site.py` passed (9 pages, 35 fixtures, no broken links); `python3 scripts/survey_verify.py` passed (all 130 inventory entries and 335 rows integrity checks, 24 scanned content pages, all internal links resolve); `python3 -m unittest discover -s tests -v` passed (28 tests). No new factual claims or sports data were introduced.

| Task | Status | Owner | Files |
|---|---|---|---|
| Root-dashboard Survey navigation | done | `arena/dd14fcfd-olbg2` | `scripts/build_site.py`, root generated HTML, `COORDINATION.md` |

| Item | Value |
|---|---|
| Follow-up PR | [#27](https://github.com/buffedlizard55-lab/OLBG2/pull/27) |
| Merge result | Merged 2026-10-21 06:41:09 UTC; merge commit `e5ad112b41d4df167026fd9429310d2335dc4727` |
| Validate Pages content | Run `39556956109` success |
| GitHub Pages deployment | Run `39556955856` success, including deploy job |


### Integration conflict log — 8103ccb6
PR #29 initially could not merge because main advanced to 8457c79 (another session added Survey navigation). Stopped and merged origin/main. Preserved both coordination sections, kept their Survey footer, consolidated duplicate Survey nav items, and regenerated all conflicting HTML from the combined builder. No data was changed or discarded. Re-ran all three builds and 33 tests.

Pre-push pull/rebase after the sync merge attempted to replay already merged concurrent-session commits and conflicted in the board. Aborted rebase without discarding work; the explicit merge commit preserves both histories. Push follows the safe abort, rather than rewriting prior sessions' commits.
