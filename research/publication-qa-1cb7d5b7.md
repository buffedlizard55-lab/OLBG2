# Publication QA — `/ledger/` and root integration

**Session:** `arena/1cb7d5b7-olbg2`

**Snapshot under review:** 23 October 2026, 20:36:17 UTC (`data/ledger/matches.json`)

**Status:** implementation, local QA, and deterministic rebuild check complete; PR, merge, and Pages deployment confirmation still pending.

## Scope and review method

This was a publication-quality review, not a fresh fixture-collection pass. Before claiming work, I checked the status/headings and recent ledger/cadence handoffs in `COORDINATION.md`, scanned remote branch heads, and reviewed the open PRs; the first full-file board display was truncated, so the older completed history was not read sequentially. That process correction is recorded append-only in the board. This pass stayed within the ledger renderer, its derived pages, the root landing/navigation, documentation, and regression tests. The complete repository test suite was run after the changes.

The source record is the committed snapshot under `data/ledger/`. No new official sports page was fetched during this pass. I reviewed the stored official NHL response, its capture-register entry, HTTP result, timestamp, and manifest hash before using it in the two new previews. No fixture, probability, fair price, market, or raw source capture was changed. Unsupported injury, player, and form information remains omitted.

## Findings and changes

1. **Malformed ledger tables.** The prior renderer could emit anchor/badge fragments directly under `<tr>`, rather than inside a cell. The table helper now wraps fragments in semantic `<td>` elements and uses `<th scope="col">` for headers. A parser-based regression test checks the header/cell count of every table across the 26 generated ledger pages.
2. **OLBG picks were mixed with supplementary schedule context.** The executive pick list and sport summaries now include only OLBG-listed events with an official fixture URL and an originated line. Supplementary NHL, MLB, and EuroLeague fixtures are separated, as are OLBG one-sided market-implied references. All originated recommendation rows link to their official game page.
3. **The “next 36 hours” cutoff was fixed.** The window is calculated from the latest captured timestamp rather than a hard-coded date; displayed starts retain their full UTC date and time.
4. **High-confidence preview shortfall was resolved from existing official evidence.** Two source-linked, unique previews were added for the high-confidence OLBG-linked Ice Hockey picks. Their fact source is the captured NHL standings response; each preview also links to its official game page. Both exceed the 30-word minimum, name the selected market, cite at least two facts, and contain neither prohibited term. No injury or player-status claim was added.
5. **Current-vs-archive hierarchy was clarified.** The root landing promotes the 15-sport ledger and links the separate Cadence snapshot as an earlier cross-check. The old root `/verified/` stripe is now explicitly marked historical and links back to the current ledger. The README distinguishes the overlapping snapshots and warns against adding their counts.
6. **Review copy is reproducible and current.** `scripts/ledger_report.py` regenerates the preview shortfall and repository-review output. Its root findings now reflect the current CTA and historical stripe rather than the former `/monitor/` promotion.

## Snapshot accounting

| Layer | Captured result | Publication treatment |
|---|---:|---|
| OLBG upcoming events | 142 across the 15 requested categories | Primary event list |
| Officially matched OLBG events | 12: 9 page-level pairings, 3 official schedule fixtures | Match state shown per event |
| OLBG events with originated lines | 3 | Only these can enter the originated OLBG recommendation list |
| OLBG events unmatched to an official source | 130 | Remain explicitly unmatched, with values blank and their OLBG listing available for review |
| Supplementary official schedules | 93 fixtures; 744 originated market selections | Separate context layer; only 3 fixtures overlap the captured OLBG slate, leaving 90 context-only fixtures |
| Market-implied OLBG references | 139 | Clearly distinguished from originated fair prices |
| Current written previews | 21 total: 7 joined to OLBG listings, 14 supplementary | The 7 OLBG-linked previews comprise 5 low- and 2 high-confidence previews |
| Carried previews | 26 | Clearly labelled as earlier work; their underlying facts were not reread in this capture |
| Review items | 15 | Published on `ledger/flagged.html` |

The three source-matched OLBG matches are two NHL fixtures and one MLB fixture. The executive pick table shows one strongest originated selection per match: the two NHL selections are high confidence and in the requested price band; the Rays–Brewers selection is medium confidence. Five picks per sport remains a maximum target, not a fabricated quota. The other thirteen listed sports have no originated OLBG selection in this snapshot, and that shortfall is stated on the picks page.

### High-confidence selections and supporting NHL facts

- **Canadiens at Blackhawks — Over 5.5**, 71.41%, fair American price **−250**. Captured NHL standings report Montréal at 9 GP, 4–3–2, 30 goals for and 34 against; Chicago at 9 GP, 3–6–0, 21 for and 36 against, with a 3–2–0 home record (15 for, 17 against).
- **Lightning at Avalanche — Avalanche +1.5**, 71.38%, fair American price **−249**. The standings report Colorado at 10 GP, 5–4–1, 41 goals for and 31 against, including a 3–1–1 home record (24 for, 16 against); Tampa Bay at 9 GP, 7–2–0, 31 for and 23 against, 2–2–0 on the road, and a three-game winning streak.

These are dated source captures, not live standings. The official response is `https://api-web.nhle.com/v1/standings/2026-10-23`, captured at 20:32:14 UTC with HTTP 200; the stored body’s manifest SHA-256 is `42230dc3c244380ddd58276e2a76a1c23aff4593c237b56d08e479fec10f50b3`. Official game pages: [Canadiens–Blackhawks](https://www.nhl.com/gamecenter/mtl-vs-chi/2026/10/24/2026020166) and [Lightning–Avalanche](https://www.nhl.com/gamecenter/tbl-vs-col/2026/10/24/2026020167).

## Source-link exception and unresolved coverage

The 130 unmatched OLBG listings have **no captured official fixture source**. They remain labelled unmatched, with an empty official-source value and a separate OLBG listing link for manual review; assigning a governing-body URL without evidence would be misleading. Likewise, sports with no official match source or no readable statistical input remain blank and flagged. This is an explicit source-coverage limitation, not a claim that those listings have been officially confirmed. The official source register and per-row status are available on `ledger/sources.html` and `ledger/verification.html`.

The separate `/cadence/` dashboard is a 23 October capture from 20:10 UTC (93 fixtures, 728 originated selections, 33 write-ups). It is an independent, overlapping snapshot—not a live update and not an additional count to add to the ledger.

## Validation run

- `python3 -m py_compile scripts/ledger_build.py scripts/ledger_report.py scripts/build_site.py scripts/ledger_predictions.py tests/test_publication_1cb7d5b7.py` — passed.
- `python3 scripts/ledger_predictions.py` — 21 previews published, 0 rejected; 47–69 words.
- `python3 scripts/ledger_report.py` — regenerated 15 review items and 7 repository findings.
- `python3 scripts/ledger_build.py` — 26 ledger pages written.
- `python3 scripts/ledger_verify.py` — 18/18 checks passed.
- Deterministic root/ledger rebuild sequence was rerun; the working diff hash remained identical (`ae146dc9f62ba2669837e8cc6effc876237e891aac4027c9a9eccead3b738698`).
- `python3 scripts/integration_audit.py` — 0 local link errors; structural only, external claims not freshly fetched.
- `python3 -m unittest tests.test_publication_1cb7d5b7 -v` — 8 tests passed, including table shape, OLBG-only recommendation joins, the dynamic 36-hour cutoff, and NHL fact-to-capture checks.
- `python3 -m unittest discover -s tests -v` — 670 tests passed. The run emits existing `ResourceWarning` notices from `tests/test_update_d69dc1c9.py` for unclosed JSON input files; they do not fail the suite.

**Next:** commit and push the integration, open and merge its PR, confirm the Pages deployment, then append the PR/deployment result here and to `COORDINATION.md`.
