# Cross-layer integration audit — 2026-10-21

Session: `8103ccb6`. Baseline: `9852d0e`. This is an incremental audit of an already populated repository, not the initial empty-repository audit described in REPO_REVIEW.md.

## Reviewed scope

Read the shared coordination history, root configuration and builder, Pages workflow, survey verification code, survey prediction fact lists, and stored match metadata. Rebuilt all three layers and ran their structural gates. No sporting data or prices were changed, and no new high-confidence recommendation was created.

## Official-source check

Retrieved https://api-web.nhle.com/v1/score/2026-10-21 using fetch_page. The response identifies game 2026020152 PHI@BUF at KeyBank Center and game 2026020153 FLA@OTT at Canadian Tire Centre, both 2026-10-21T23:30:00Z. These match the two root NHL rows for that date. The check does not verify standings inputs, prices, injuries, predictions, or other fixtures. No raw response capture was persisted; this is a limited tool-response check, not a reproducible archived capture.

## Findings published at /integration.html

- Root and survey scope differs (17 versus 15 sports).
- Prior timezone interpretations conflict; no universal timezone established here.
- Root and survey both list Afghanistan–Bangladesh and New Zealand–India; previous claims of disjoint inventories cannot be relied on. No combined unique-match count is published.
- Hurling taxonomy claims conflict.
- Root `generated_at` precedes `inputs_captured_at`.
- Each survey prediction fact is exposed for review with its existing URL. Several are secondary publishers. Structural URL presence does not establish primary-source verification, even when the row cites an official URL.
- No continuous collector, expiry gate, exhaustive official fixture reconciliation, or all-market inventory exists. This session does not claim the full original brief is fulfilled.

## Changes

Added Survey and Evidence status navigation, a dated-research banner to root pages, a central cross-layer review table, cross-layer link checks including assets, five regression tests, and survey rebuild/validation in CI. Existing data and all earlier review queues remain unchanged. Every review table row links to evidence or the relevant review register; blank unknown sporting fields were not filled.

## Local verification

- `python3 scripts/build.py`: 25 desk fixtures.
- `python3 scripts/build_site.py`: 10 root pages, 35 fixtures, 4 existing narratives.
- `python3 scripts/survey_build.py`: 26 files (24 HTML pages plus two assets).
- `python3 scripts/survey_verify.py`: structural checks pass, 130 entries, 11 modelled lines, 2 existing narratives, 21 flags. Its label “verification” does not imply fresh external factual verification.
- `python3 -m unittest discover -s tests -q`: 33 tests pass.
- `python3 scripts/integration_audit.py`: zero broken local links across all published layers. External URL availability and fragment anchors are not validated.
- Repeated builds are byte-identical. Pages currently serves main at repository root, confirmed with GitHub API.
