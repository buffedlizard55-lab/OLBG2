# Reproducibility and publication-integrity audit

**Session:** `arena/dc72bac4-olbg2`  
**Audit date:** 2026-10-22 UTC  
**Base observed after rebase:** `238c157` (PR #91)  
**Purpose:** check deterministic builds, internal publication checks, count accuracy, and CI coverage. This is not a sports-fact audit and does not certify that an official source supports each adjacent claim.

## Findings

### RPA-01 — stale counts in the root builder and README — corrected here

The committed verified dataset reports **188 rows, 154 originated, 34 unlined, and rows in 14 of 17 eligible sports** (`data/verified/matches.json`). Its `source_scope` counts are 144 fixture-scoped and 44 competition-scoped. Before this correction, user-facing copy still said 178 rows, 13 sports, 63 competition-scoped rows, and the root index banner said 118 rows. The archive also claimed 15 sports. README's expected output said 178 rows and 80 tests although the checked-in test suite had 145 tests after PR #91.

The hard-coded stale counts in `scripts/build_site.py` now derive from the loaded dataset or have been removed. The sport index reports the row-bearing and zero-row category counts dynamically and clarifies that zero rows in this snapshot do not establish that a sport has no fixtures. README now identifies `/final/` as the consolidated 17-sport view, documents overlapping layer snapshots, and avoids freezing the test count. A regression suite checks those count disclosures.

The current `/verified/` dataset count is a structural observation, not an assertion that all 188 fixtures were freshly re-verified by this audit.

### RPA-02 — board dataset and its tests disagree after a deterministic rebuild — needs review

A diagnostic run of the board generation sequence, after rebuilding the forward capture from checked-in inputs, produced **277 rows (227 originated, 50 unlined)**. The checked-in `data/board/matches.json` and rendered `/board/` pages are **207 rows (167 originated, 40 unlined)**. Two existing tests in `tests/test_board_ddcbf63c.py` hard-code the earlier counts and fail against the regenerated output:

- `test_matches_deduplication_and_counts`: expected 207, observed 277.
- `test_originated_vs_unlined_integrity_and_american_odds_math`: expected 167 originated, observed 227.

This work did not edit that file or commit the diagnostic generated files: the board test is in the completed board owner's declared scope, and the coordination rule requires a cross-scope request rather than silently taking it over. All generated board, evidence, audit65, and final changes from the diagnostic run were reverted. The request and exact scope are in [`COORDINATION.md`](../COORDINATION.md).

The `final` consolidation remained at 382 deduplicated rows in the diagnostic rebuild because the added NBA schedule rows are also present in the verified input layer. This is a repeatable deduplication result, not independent verification of those NBA events. The root `/final/` snapshot remains 382 rows until an owner refreshes the board scope and dependent audit outputs.

For manual review, the affected row records retain their source URLs in the board/forward inputs. Examples of official links recorded by those rows include [NBA's official Oct. 24 schedule](https://www.nba.com/schedule?date=2026-10-24) and the [NBA game page referenced for MIA–CHA, game 0022600104](https://www.nba.com/game/mia-vs-cha-0022600104). **This audit did not fetch either URL**, so it makes no claim that the page currently confirms the stored fixture fields.

### RPA-03 — CI's drift gate does not cover every generated desk — needs review / cross-scope request

`.github/workflows/pages.yml` rebuilds `/verified/`, `/live/`, the desk site, `/survey/`, `/final/`, and root pages. Its `git diff --exit-code` path list does not include `/board/`, `/hub/`, `/slate/`, `/portal/`, `/forward/`, `/evidence/`, or `/audit65/`. Some of these layers have local structural/unit tests and dedicated verifiers, but that is not the same as checking every committed generated output for drift.

PR #91 (`arena/17c50bb7-olbg2`) explicitly claimed the workflow file and is merged. This session therefore did not edit `.github/workflows/pages.yml`; the request to add the remaining deterministic build/drift checks is logged in [`COORDINATION.md`](../COORDINATION.md). The separate deploy workflow now depends on the reusable validation workflow, as added by PR #91.

### RPA-04 — local structure checks pass; external facts remain outside their guarantee

The checks run here validate schemas, model invariants, source host/URL presence, word counts, local links, and deterministic generation. They do not fetch every official page or prove each source page supports each fixture, statistic, form statement, price, or prediction. PR #91's source-access report records TLS EOF failures when official endpoints were attempted in that session: [`publication.html`](../publication.html) · [`research/publication-17c50bb7.md`](publication-17c50bb7.md). Those factual and exhaustive-coverage gaps remain flagged.

## Verification performed

| Check | Result |
|---|---|
| `python3 scripts/verified_seed.py && python3 scripts/verified_model.py && python3 scripts/verified_build.py` | Passed; 188 rows, 154 originated, 34 unlined |
| `python3 scripts/live_model.py && python3 scripts/live_build.py` | Passed; 11 fixtures, 33 markets, 0 broken links in the live builder's check |
| `python3 scripts/survey_sync_inventory.py && python3 scripts/survey_lines.py && python3 scripts/survey_analyse.py && python3 scripts/survey_build.py && python3 scripts/survey_verify.py` | Passed; verifier scanned 26 pages / 368 table rows, checked row-source-or-unverified status, and reported 0 internal-link errors |
| `python3 scripts/portal_seed.py && python3 scripts/portal_model.py && python3 scripts/portal_build.py && python3 scripts/portal_verify.py` | Passed; 26 pages, 707 table rows with HTTPS source links, 1,536 internal links/fragments, 244 rows; these are structural counts, not external content checks |
| `python3 scripts/hub_verify.py` | Passed; 22 pages, 524 table rows with HTTPS source links, 707 internal links/fragments |
| `python3 scripts/build_site.py && python3 scripts/integration_audit.py` | Passed after copy corrections; 10 root pages + 17 category pages, 188 rows, 0 local link errors |
| `python3 -m unittest discover -s tests -q` against the checked-in board snapshot | **149 tests passed** (145 existing + 4 new publication-copy/review-page tests) |
| Board diagnostic `forward_seed → forward_model → board_seed → board_model → board_build` | Exposed RPA-02; updated outputs were not retained because the board owner's tests are out of scope |
| Cross-layer external factual verification | **Not performed in this audit.** Source links are provenance/manual-review links only. |

The GitHub Pages CI drift command was not claimed green after this branch's changes at audit time; it was not edited because of the merged PR #91 scope. The exact workflow must be rerun by Actions after publication.
