# Final current-desk integration — 22 October 2026

## Scope and evidence

This pass checks repository integration, not fresh sports facts. It deliberately adds no fixtures, statistics, prices or narrative predictions. Official sports domains are outside this sandbox's outbound host allowlist. Existing captures cannot be labelled freshly verified by this session. Source links for manual review remain at [current sources](../current/sources.html), [fixture table](../current/matches.html), and [flagged items](../current/flagged.html).

Repository evidence reviewed: `COORDINATION.md` completion ledger for PRs #119–122; `scripts/current_{seed,model,build}.py`; generated `current/` pages; root builder; Pages validation/deployment workflows; integration link checker and tests. This is not a claim that every historical line in this large repository has been independently fact-checked.

## Resolved defects

1. Completed `/current/` desk was absent from root navigation. Add exact layer-relative links on root and category pages.
2. Current seed/model/build were absent from CI and generated-file drift checking. Add them before root generation and include `current data/current` in the drift gate.
3. Link checker used a seven-folder allowlist, silently omitting most desks. Discover all HTML recursively, excluding hidden, staging and dependency directories. Regression-test a newly named future desk.
4. Review page claimed fragment-anchor checking that the checker did not perform. Correct the disclosure and terminal output: checks establish file existence, not anchor validity, intended destinations, external availability, or factual truth.
5. README omitted current desk. Link it as an overlapping stored snapshot, not an additive or live feed.

## Verification and limits

- Replayed every rebuild command from `.github/workflows/pages.yml`: success.
- `python3 -m unittest discover -s tests`: 343 tests passed (5 new integration gates). Existing ResourceWarnings about unclosed test files remain non-fatal; no assertion failure.
- `python3 scripts/integration_audit.py`: zero broken local file references across discovered HTML pages.
- Current regeneration changes no committed current inputs or outputs.
- No new official sports-site reads occurred. Links alone are not verification.
- The current model reports 57 fixtures in 7 of 17 sports, 55 originated fixture rows, 2 blank rows, 1931 prices and 29 selected paragraphs. These are counts reproduced from repository data, not independently verified sporting facts. Ten zero-row sports remain visible for review.
- Five qualified daily match predictions per covered sport, exhaustive upcoming fixtures, live market availability, calibrated probabilities and independently refreshed official form inputs are **not established** by this integration. Do not fabricate picks to satisfy the quota.
- Alternate model handicaps/totals may not be offered by bookmakers. A 70% model label is not evidence of a 70% empirical win rate or a betting edge. The current desk's review/methodology pages disclose alternative-line selection and calibration limits.

## Manual review links

- [Dashboard](https://buffedlizard55-lab.github.io/OLBG2/current/index.html)
- [Official-source register](https://buffedlizard55-lab.github.io/OLBG2/current/sources.html)
- [Flagged for Review](https://buffedlizard55-lab.github.io/OLBG2/current/flagged.html)
- [Methodology](https://buffedlizard55-lab.github.io/OLBG2/current/methodology.html)
- [Integration review](https://buffedlizard55-lab.github.io/OLBG2/integration.html)
