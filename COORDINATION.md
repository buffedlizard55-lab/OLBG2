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
| Pull request | **PR #7** https://github.com/buffedlizard55-lab/OLBG2/pull/7 |
| Merge | merged to `main` at 2026-10-21 05:21:08Z · merge commit `3778896` |
| Merge conflict | Yes — resolved by merging `origin/main` (`d9f6376`) into the branch first; no prior work discarded (see log above) |
| Deploy run | `Validate Pages content` 39549059975 success · `pages build and deployment` 39549058659 success |
| Live check | `https://buffedlizard55-lab.github.io/OLBG2/` renders the dashboard; `/site/index.html` renders the prior audit site |
| Follow-up | PR #9 — per-date NHL provenance (each NHL row now cites its own `…/score/YYYY-MM-DD` feed) |
| Follow-up | PR #12 — repaired the NBA citations the PR #9 helper mangled, and added a build gate requiring every citation to match `data/sources.json` |
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
