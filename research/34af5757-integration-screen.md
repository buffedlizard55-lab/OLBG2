# Final-integration candidate screen — 24 October 2026

**Session:** `arena/34af5757-olbg2`  
**Purpose:** choose which merged or candidate layer can support each part of the release without adding overlapping counts or promoting unsupported picks.  
**Evidence boundary:** this is a first-hand review of committed repository data and code, not a second live capture of every OLBG or governing-body page. The official NHL/MLB reads and the earlier `/today/` field audit remain in [`34af5757-evidence-audit.md`](34af5757-evidence-audit.md).

## Decision summary

| Release need | Best current evidence | Integration decision |
| --- | --- | --- |
| Fresh OLBG inventory | `arena/03e61ed8-olbg2` live-desk capture at 17:57Z: 195 events, 181 matches and 14 outrights across 14 represented sports; Golf is explicitly empty | Useful as a **listing candidate only** until its confidence and blank-quote gates are corrected. Do not describe it as 195 officially confirmed fixtures. |
| Qualified high/in-band written selection | Merged `/vantage/`: Boston Bruins money line, 70.4%, fair −238, 86-word preview, official-input and sensitivity disclosure | Strongest current candidate. Keep the price-window and prior-sensitivity caveats beside it. |
| Honest multi-market/pricing coverage | Merged `/vantage/`: 15 priced matches, 95 fair outcomes, 15 previews; 41 official fixture/event records and 97 first-page OLBG entries | Use without adding counts from `/today/`, Clarity, Executive or live-desk. Its 115 review items and 74-pick shortfall must stay visible. |
| Root landing page | Neither the old cadence-heavy root nor an unfiltered live-desk banner | Lead with the qualified selection and explicit coverage limits; link fresh listings and evidence-checked previews separately. Do not call every stored layer “current.” |

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

## Other merged candidates

- **Clarity:** 50 fixtures, 239 lines, 41 picks and 31 previews, but all 12 rows labelled high are below 70%. It cannot supply a qualified high pick without changing the evidence or calculation.
- **Executive:** 71 fixtures/lines/previews and 12 highs, but only Houston–Atlanta is high and in-band. Its preview-generation timestamp is later than its stated capture, and its ranking-based prose needs separate source review before promotion.
- **`/today/`:** the earlier independent audit found five omitted official NHL games, a 65% high threshold, citation gaps and a contradicted Vegas superlative. Do not use its executive cards as the final root’s qualified-pick evidence.

## Integration acceptance gate

A final root may be published with visible shortfalls; it may not hide them. Before calling the release complete:

1. Show the exact 15-sport scope and separate listing counts from officially confirmed counts.
2. Put the Boston/Vantage selection ahead of unqualified quote-only or out-of-band highs, with its sensitivity and price provenance attached.
3. Link all picks, matches, lines, predictions, sport pages and Flagged for Review from the chosen desk.
4. If live-desk is merged, do not repeat its current 63-high or nine-value-row claims until LD-01 and LD-02 are fixed.
5. Rebuild every deterministic inventory after the final layer count is known; run the entire suite and link audit sequentially.
6. Merge only a green PR, wait for both validation and Pages deployment, and fetch the deployed root, pick, prediction, sport and review pages.
