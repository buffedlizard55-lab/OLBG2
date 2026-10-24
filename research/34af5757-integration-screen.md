# Final-integration candidate screen — 24 October 2026

**Session:** `arena/34af5757-olbg2`  
**Purpose:** choose which merged or candidate layer can support each part of the release without adding overlapping counts or promoting unsupported picks.  
**Evidence boundary:** this is a first-hand review of committed repository data and code, not a second live capture of every OLBG or governing-body page. The official NHL/MLB reads and the earlier `/today/` field audit remain in [`34af5757-evidence-audit.md`](34af5757-evidence-audit.md).

## Decision summary

| Release need | Best current evidence | Integration decision |
| --- | --- | --- |
| Fresh OLBG inventory | `arena/03e61ed8-olbg2` live-desk capture at 17:57Z: 195 events, 181 matches and 14 outrights across 14 represented sports; Golf is explicitly empty | Useful as a **listing candidate only** until its confidence and blank-quote gates are corrected. Do not describe it as 195 officially confirmed fixtures. |
| Qualified high/in-band written selection | Merged `/vantage/`: Boston Bruins money line, 70.4%, fair −238, 86-word preview, official-input and sensitivity disclosure. PR #207's `/now/` also has Boston ML and St. Louis +1.5 above 70% with previews | Vantage is the strongest **merged** selection evidence. `/now/` is a candidate only after its other seven sub-70% highs are regraded. Keep price-window and sensitivity caveats beside the pick. |
| Honest multi-market/pricing coverage | Merged `/vantage/`: 15 priced matches, 95 fair outcomes, 15 previews; 41 official fixture/event records and 97 first-page OLBG entries | Use without adding counts from `/today/`, Clarity, Executive, `/now/` or live-desk. Its 115 review items and 74-pick shortfall must stay visible. |
| Root landing page | PR #207's single front door and generated archive is the best layout candidate; the old root and unfiltered live-desk banner are not | Use `/now/` only after its 70% gate, temporal label, PR band claim and deleted disclosure test are corrected. Do not call every stored layer “current.” |

## Live-desk candidate: exact screen

Reviewed data: [`data/live_desk/model.json` at `3558a0f`](https://github.com/buffedlizard55-lab/OLBG2/blob/3558a0fadff88568ff8c36ab2504a222dd76fe73/data/live_desk/model.json), capture `2026-10-24T17:57:12Z`; [`predictions.json`](https://github.com/buffedlizard55-lab/OLBG2/blob/3558a0fadff88568ff8c36ab2504a222dd76fe73/data/live_desk/predictions.json); [`livedesk_model.py`](https://github.com/buffedlizard55-lab/OLBG2/blob/3558a0fadff88568ff8c36ab2504a222dd76fe73/scripts/livedesk_model.py); [`livedesk_ratings.py`](https://github.com/buffedlizard55-lab/OLBG2/blob/3558a0fadff88568ff8c36ab2504a222dd76fe73/scripts/livedesk_ratings.py); and [`livedesk_build.py`](https://github.com/buffedlizard55-lab/OLBG2/blob/3558a0fadff88568ff8c36ab2504a222dd76fe73/scripts/livedesk_build.py).

| Check | Stored result | Consequence |
| --- | ---: | --- |
| OLBG events / matches / outrights | 195 / 181 / 14 | Large fresh listing candidate; not an official-confirmation count. |
| Events with `official_verified=true` | 13 | The other 182 belong in review, not in a verified-fixture total. |
| Pricing tiers | 183 `quoted-market`; 12 `official-model` | Most prices are transformations of one OLBG quote, not independent official-stat estimates. |
| Rows labelled high | 63 | 58 are `quoted-market`; only five are `official-model`. |
| High rows also in the fair-price band | 1 | That row is quote-only and unconfirmed, not an official-input high selection. |
| Official-input high rows also in-band | 0 | No qualified high pick should be promoted from this capture as currently graded. |
| Written previews | 5 | All Ice Hockey: three medium and two low; none is a high-confidence write-up. |
| Top-five lists | 12 sports have at least one; Golf, Motor Racing and Rugby League have none | The five-per-sport target is not met and must not be padded. |

### LD-01 — confidence rule contradiction (high)

The metadata says: “high >= 70% and requires an official numeric input; consensus-only rows cap at medium.” The implementation of `grade()` caps only `crowd-consensus`; it permits `quoted-market` rows to become high.

The only high/in-band example is **Lugi HF vs IFK Skovde HK**, OLBG event [`12149`](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/Lugi_HF_vs_IFK_Skovde_HK/20?event_id=12149):

- `official_verified` is false and `facts` is empty.
- The only stored quote is 3.30 on Lugi. The script divides its implied probability by an assumed 1.04 margin, flips to the opponent, and publishes IFK Skovde at 70.86% / fair −243.
- The selected opponent has no stored quote and no written preview.

**Required resolution:** cap quote-only rows below high, or add real official numeric evidence and qualifying analysis. Do not merely change the methodology text to match the looser implementation.

### LD-02 — blank quote treated as a value quote (high)

`banner_html()` computes the comparison denominator as `quoted_decimal or 0 or 99`. A blank quote therefore becomes 99. Buffalo at Washington is counted among nine selections “worth backing at the quoted price right now” even though the selected Washington side has no quote.

**Required resolution:** require a nonempty finite decimal quote greater than 1.0 before making any at-that-price claim. Keep the fair price visible even when no offered comparison exists.

### LD-03 — official start and citation gaps (medium)

For confirmed NHL events, the builder prefers the OLBG-derived `event.start_utc` over `event.official.start_utc`. Examples in the stored capture:

| OLBG event | Listing-derived value displayed | [Official NHL schedule](https://api-web.nhle.com/v1/schedule/2026-10-24) |
| --- | --- | --- |
| 200002, Carolina at St. Louis | 2026-10-24T23:07:00Z | 2026-10-24T23:00:00Z |
| 200009, Tampa Bay at Utah | 2026-10-25T02:07:00Z | 2026-10-25T01:00:00Z |

The five previews cite OLBG and the schedule while using standings records, venue splits and goal totals. Add the captured [official NHL standings](https://api-web.nhle.com/v1/standings/now) source to those claims and use the official start for confirmed fixtures.

## Vantage: merged evidence-checked candidate

Reviewed on `main` at `80409d3` after PR [#205](https://github.com/buffedlizard55-lab/OLBG2/pull/205). The unmodified verifier reports **3,405 assertions, 2,085 links, 41 official matches, 95 originated selections, 27 pages, 15 previews and zero structural errors**.

| Area | Count / status | Integration note |
| --- | --- | --- |
| OLBG first-page entries | 97 | Explicitly partial because of “Load More Tips”; do not call it exhaustive. |
| Official fixture/event records | 41 | 56 OLBG-only rows retain blanks and non-confirming review links. |
| Priced matches / fair outcomes | 15 / 95 | Moneyline/1X2, handicaps and totals where supported. |
| Written previews | 15 | One for every published selection; no bare pick is presented as a full prediction. |
| High / in-band written selection | 1 | Boston Bruins ML, 70.4%, fair −238. |
| Review items | 115 | Keep the Flagged for Review page prominent. |
| Five-per-sport high-write-up shortfall | 74 | Explicitly disclosed; no unsupported padding. |

The [Boston preview’s official inputs](https://api-web.nhle.com/v1/score/2026-10-24) include Boston’s 6–0 win over Nashville and San Jose’s 6–2 win over Ottawa. The preview also discloses that the captured league-partner FanDuel price is not an OLBG bookmaker quote. Its sensitivity note says an eight-game shrink would produce 72.1% / −258 while a 12-game shrink would produce 69.0% / −223. That caveat must remain next to the high grade rather than being hidden by a root summary.

## `/now/` clean-root candidate (PR #207)

Reviewed an isolated archive of `arena/4a8390fe-olbg2` at `1e89cf5`; no branch files were edited. The unmodified `now_verify.py` completed **8,063 structural checks with zero failures**. Those checks reproduce the stored rules, including the incorrect 62% high threshold, so this pass is not acceptance evidence.

### What is strong

- A single root front door with the executive picks, fixture map, 15 sport links and a generated archive of earlier layers. This directly addresses the repository's largest usability problem.
- Fifty inherited official fixture records, 39 selected picks, 866 originated market rows and 36 previews. All 39 selected picks are in-band; all high/medium picks have a preview. The previews are at least 65 words and contain neither prohibited term.
- **Two pregame rows labelled high also clear 70% and have full previews:** Boston Bruins money line at 70.99% / fair −245, and St. Louis Blues +1.5 at 70.71% / fair −241. Perugia and Australia are exactly 70.0% but intentionally capped below high by their class-ladder evidence rule; do not promote them merely to increase the count.
- The build distinguishes 35 pregame picks from four started picks and honestly discloses that the 50 fixture records and 245 fact citations were inherited from Clarity's 17:35Z capture rather than re-read in this session.

### Corrections required before integration

| Finding | Stored evidence | Required resolution |
| --- | --- | --- |
| NW-01 · high threshold | `grade()` accepts high at 62%; seven of ten high picks are below 70% | Enforce 70% in the generator, verifier and tests. Regrade those seven to medium and regenerate all displayed counts; retain their analysis. |
| NW-02 · temporal label | Five of 50 fixture records have started at 18:10Z, while the root says “50 upcoming matches” | Publish 50 fixture records, 45 still to start and five started. Preserve the correct 35-pregame/four-started pick split. |
| NW-03 · PR band claim | 578 of 866 line rows are in-band; 288 are outside, with prices from −199900 to +199900 | Correct the PR body. The lines page already reports 578/866 and all 39 selected picks are in-band, so no price clamping is needed or acceptable. |
| NW-04 · removed disclosure test | PR deletes `test_reproducibility_review_page_discloses_pending_findings_and_links_sources` | Restore this unrelated review-page disclosure/link test. Root-specific tests may change; unrelated audit coverage must not be deleted. |
| NW-05 · NHL inventory | Ten late NHL games are present; LA–New Jersey at 19:30Z is absent although still upcoming at 18:10Z | Add the official/OLBG NJ row or flag the omission. Anaheim–Philadelphia had started and may be archived rather than called upcoming. |

The candidate's ten NHL rows are not a complete official 12-game index. Its 50 records must remain an inherited, bounded snapshot, not a claim of worldwide coverage. After NW-01 through NW-05, `/now/` can supply the clean root without adding its counts to Vantage or live-desk. Its generated inventory must account for the final number of top-level layers after rebasing: 48 if it follows Vantage alone, 49 if live-desk merges first.

## Other merged candidates

- **Clarity:** 50 fixtures, 239 lines, 41 picks and 31 previews, but all 12 rows labelled high are below 70%. It cannot supply a qualified high pick without changing the evidence or calculation.
- **Executive:** 71 fixtures/lines/previews and 12 highs, but only Houston–Atlanta is high and in-band. Its preview-generation timestamp is later than its stated capture, and its ranking-based prose needs separate source review before promotion.
- **`/today/`:** the earlier independent audit found five omitted official NHL games, a 65% high threshold, citation gaps and a contradicted Vegas superlative. Do not use its executive cards as the final root’s qualified-pick evidence.

## Integration acceptance gate

A final root may be published with visible shortfalls; it may not hide them. Before calling the release complete:

1. Show the exact 15-sport scope and separate listing counts from officially confirmed counts.
2. Put qualified high/in-band analysis ahead of unqualified quote-only, sub-70% or out-of-band highs. Use Vantage's Boston caveats or the corrected `/now/` Boston/St. Louis evidence; never present overlapping alternatives as additional independent picks.
3. Link all picks, matches, lines, predictions, sport pages and Flagged for Review from the chosen desk.
4. If live-desk is merged, do not repeat its current 63-high or nine-value-row claims until LD-01 and LD-02 are fixed. If `/now/` is merged, require NW-01 through NW-05 first.
5. Rebuild every deterministic inventory after the final layer count is known; run the entire suite and link audit sequentially.
6. Merge only a green PR, wait for both validation and Pages deployment, and fetch the deployed root, pick, prediction, sport and review pages.
