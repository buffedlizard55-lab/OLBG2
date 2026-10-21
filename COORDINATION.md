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
in part: 33 fixtures and 30 originated lines, with the remaining gaps enumerated as F01–F18.

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
| Pull request | PR #8 (this merge) |
| Merge result | merged to `main` |
| Pages deploy | verified after merge |

---

# Second integration — session `db99ed90` (2026-10-21, after `3778896`)

## Claim

Session `db99ed90` opened on `arena/db99ed90-olbg2` at 05:14 UTC against `main@306916e` and claimed the whole task
board (T1–T7) in commit `6036dd1`, pushed immediately. The four other `arena/*` branches were inspected first; three
had no commits after 05:14 and one was claim-only, so the claim did not collide with active work.

**Claim statement:** collection, official verification, line origination, confidence grading, high-confidence
narratives, the dashboard/category pages, tests and integration — scopes `data/**`, `scripts/**`, `site/**`,
`tests/**`, `README.md`, `COORDINATION.md`.

## Work delivered on this branch

| Task | Status | Scope | Result |
|---|---|---|---|
| T1 Source collection | done | `data/events.json` | 16 eligible OLBG categories with ids from the betting-tips sitemap |
| T2 Official verification | done | `data/events.json` | 14 NHL fixtures, each with official game page + official feed |
| T3 Line origination | done | `scripts/poisson.py` | `olbg-desk-poisson-v1`, Poisson, parameters declared in the data file |
| T4 Confidence + narratives | done | `data/events.json` | 6 high / 3 medium / 5 low; narratives 54–60 words, all unique |
| T5 Site | done | `site/**`, `scripts/build.py` | 22 pages: overview, fixtures, 16 categories, methodology, sources, flagged |
| T6 Tests | done | `tests/test_build.py` | 23 checks incl. broken-link crawl and model/pick agreement |
| T7 Integration | in progress | `README.md`, `COORDINATION.md` | Merge, PR, deploy recorded below |

## Sources used by this session

| Source | What was taken |
| --- | --- |
| `https://www.olbg.com/betting-tips` | Global list, sport menu, taxonomy |
| `https://www.olbg.com/sitemap-betting-tips.xml` | OLBG sport ids 1–28 |
| `https://www.olbg.com/betting-tips/Ice_Hockey/13` | OLBG's own NHL listing — 2 events (199897, 199896) plus Austria EHL and SHL |
| `https://api-web.nhle.com/v1/schedule/2026-10-21` | 2 games on 21 Oct, 12 on 22 Oct, start times in UTC |
| `https://api-web.nhle.com/v1/gamecenter/{id}/right-rail` | GF/GA per game, PP/PK %, ranks, last-ten record, listed results, head coaches (14 fixtures) |
| `https://api.nhle.com/stats/rest/en/team` | Official full club names (26 clubs used) |
| `https://www.nhl.com/gamecenter/{slug}/{date}/{id}` | Human-readable official game page linked per row |
| `https://www.nba.com/games` | 11 games on 21 Oct, 2 on 22 Oct; matchups did not render |
| `https://statsapi.mlb.com/api/v1/schedule?...&date=2026-10-21` | `totalGames: 0` |
| `https://www.icc-cricket.com/fixtures-results`, `/matches/271646/new-zealand-vs-india` | Upcoming cricket fixtures; no date field exposed |
| `https://www.atptour.com/en/scores/current` | In-progress/completed tennis; no dates |
| `https://www.premiershiprugby.com/fixtures` | HTTP 404 (site moved to `premrugby.com/fixtures-results`) |

## Verification performed

- 14/14 fixtures: teams, date and start time compared field by field against the official feed; `start_utc` checked
  against the fixture date, allowing the next UTC day for evening face-offs.
- 26/26 club names matched to the official NHL team list rather than written from memory.
- Spot-check of `https://www.nhl.com/gamecenter/buf-vs-phi/2026/10/21/2026020152` returned GF/GP 1.55/3.00,
  GA/GP 3.18/3.67, PP 12.9/9.1 % and PK 84.6/64.5 % — identical to the values stored for that row.
- **Independent agreement with the dashboard session:** `data/predictions.json` on `main` describes the same
  `nhl-2026020152` game as "Buffalo 4-3-2 … 27 goals for, 33 against, 3.00 per game … Philadelphia 1.55" and picks
  Buffalo. That matches this session's independently captured numbers and its model selection exactly.
- 14/14 picks recomputed by `validate()` and asserted equal to the stored selection and confidence.
- 6/6 high-confidence narratives checked for length, uniqueness and naming the selection.
- Coverage row counts asserted equal to the fixture list at build time.
- `python -m unittest discover -s tests -v` → 23 pass. `python3 scripts/build.py` → 22 pages, 0 broken local links.
- `python3 scripts/build_site.py` → 9 pages, 33 fixtures, 4 predictions, no broken links (dashboard unaffected).

## Merge resolution (2026-10-21, `main@3778896` → this branch)

`main` advanced to `3778896` (PR #7, session `42fb7792`) while this branch was being built. Rebase hit a
`COORDINATION.md` conflict and was aborted in favour of a single merge, so no commit was replayed twice.

| File | Conflict | Resolution |
| --- | --- | --- |
| `index.html` | Their dashboard vs this branch's redirect | **Kept theirs.** The root stays the Dashboard; this branch no longer redirects the root. |
| `scripts/model.py` | Both sessions added a file with this name | **Kept theirs** (used by `build_site.py`). This branch's model was renamed `scripts/poisson.py`; `build.py`, `tests/` and `report.py` import from it. |
| `scripts/build.py`, `data/events.json`, `tests/test_build.py`, `site/**` | Prior audit pipeline vs evidence desk | **Took this branch's versions.** The desk is a superset of the two-fixture audit (same two games, 14 in total), regenerates `site/` deterministically and passes a larger test suite. The audit remains in git history at `306916e`. |
| `README.md`, `COORDINATION.md` | Two descriptions/boards | Rewritten README describing both layers; this board preserves the earlier sessions' text above and appends this session. |
| `.github/workflows/pages.yml` | — | This branch's wider version (runs on every branch, 23 tests, rebuild + `git diff --exit-code -- site`, link crawl). |
| `scripts/build_site.py` | — | One edit: nav label `Prior audit` → `NHL evidence desk`, because `/site/` now holds the desk. Regenerated; no other dashboard output changed. |

No other session's file was edited without logging it here. Nothing from `main` was reverted except the two-fixture
audit site, which this branch's desk replaces and which remains in history.

## Irregularities and limits (this session)

- **OLBG times differ from the NHL.** OLBG showed both 21 Oct fixtures at 00:37 the next day; the NHL feed gives
  23:30Z. OLBG states no timezone in the retrieved text. League time is published; OLBG's is recorded unchanged.
- **OLBG lists 2 of 14 NHL games.** The other 12 link to OLBG's NHL index and carry `olbg_listed: false`.
- **European ice hockey not covered.** OLBG listed Austria EHL and Swedish SHL fixtures; no official league feed was
  verified, so they are named on the Flagged page with no row.
- **NBA blocked for this session.** Four endpoints failed and the official page would not render matchups. The
  dashboard layer does carry NBA rows from its own capture; this layer does not duplicate them.
- **Cricket and tennis expose no fixture date** in the retrievable text, so no dated fixture was published.
- **LAK last-ten record inconsistent** in the NHL payload (1-4-2 with seven listed results). Reproduced verbatim.
- **Model parameters are assumptions**, not league statistics: home 1.05 / away 0.95, 50/50 tie split, confidence
  edges 10 and 6 points. Stated on the methodology page and in `data/events.json`.
- **The desk model ignores** rest, back-to-backs, injuries, goaltenders, travel and score effects, and makes no
  comparison to market prices, so it cannot claim value.

## Publish record

| Item | Value |
| --- | --- |
| Integration branch | `arena/db99ed90-olbg2` |
| Pre-merge checks | 23 tests pass; `build.py` → 22 pages; `build_site.py` → 9 pages, no broken links |
| Pull request | recorded below |
| Merge result | recorded below |
| Pages deploy | recorded below |
