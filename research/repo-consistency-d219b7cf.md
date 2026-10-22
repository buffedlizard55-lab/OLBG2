# Repository snapshot consistency audit — 2026-10-22

## Scope and standard

This pass reconciled the root README's snapshot counts and descriptions against the checked-in `data/verified/`
JSON, the checked-in root dashboard, the builders, and the automated test suite. It is a **repository consistency
check only**: no sports fact or official web page was fetched during this task. It does not upgrade a row's
verification status or establish that any linked external source supports its stored values. Existing row-level
source links and open review findings remain the audit trail for that work.

## Findings and corrections

| Item | README before audit | Checked artifact | Correction |
|---|---:|---:|---|
| Unified / verified match rows | 119 | 118 (`data/verified/matches.json`, `counts.total_rows`; also root `index.html`) | 118 |
| Originated rows | 93 | 94 (`counts.originated_rows`) | 94 |
| Unlined rows | 26 | 24 (`counts.unlined_rows`) | 24 |
| Root fixture-scoped source URLs | 85 | 84 (`source_scope` values in all 118 rows) | 84 |
| Competition-scoped source URLs | 34 | 34 (`source_scope` values in all 118 rows) | 34 |
| Open review items | 26 | 33 (`data/verified/flagged.json`, `items`; root dashboard banner) | 33 |
| Automated tests | README had two conflicting figures, 61 and 63 | 80 tests pass in this checkout | 80 |
| Zero-row sport categories | README named two | 4 of 17 eligible categories have no row in this snapshot; dashboard sport pages record the individual reasons | State four, direct readers to the sport and flagged pages |
| Odds convention | “−250 to +10000 decimal” | `data/verified/band.json` stores decimal bounds 1.40–101.00; the model/report labels the requested limits as American odds | Clarify that −250…+10000 is American, with decimal equivalent 1.40…101.00 |

The checked data currently records 13 sports with rows (118 total), of which 94 are originated and 24 are unlined.
There are 14 featured price-band predictions plus 16 separately labeled research-desk write-ups in
`data/verified/predictions.json`; the README describes the 14 featured picks in the unified dashboard and separately
discloses the 16 research write-ups. The flagged JSON contains 33 items. These are checked-in snapshot counts,
not claims that the sporting data is current beyond its capture date (2026-10-22).

## Reproducible checks

- `python3 -m unittest discover -s tests -v` — **80 passed**.
- `python3 scripts/build_site.py` — `10 root pages + 17 sport pages`, 118 rows, 94 originated, 14 band picks,
  14 featured predictions, 33 review items.
- `python3 scripts/integration_audit.py` — **0 local link errors**.
- Dataset count cross-check: `data/verified/matches.json` counts (118/94/24); every row's `source_scope`
  (84 fixture / 34 competition); `data/verified/predictions.json` (14 featured / 16 research); and
  `data/verified/flagged.json` (33 items), compared with generated root `index.html` and `flagged.html`.
- `git diff --check` — clean.

## Source and coverage caveat

Every match row retains its own `official_url` and source-scope label in the data and the tables. This task did not
open those links, so this audit does not say that they were newly confirmed, that each is fixture-specific, or that
the cited page independently establishes all adjacent claims. Competition-level references remain competition-level;
unknown values and the extant VF flags remain for review. See [the verification ledger](../verification.html),
[flagged review page](../flagged.html), [source inventory](../sources.html), and the original source links attached
to each row. The 2026-10-22 snapshot is not a live or exhaustive worldwide sports schedule.
