# OLBG2 — multi-sport schedule research and line origination

OLBG2 records OLBG's published sports taxonomy, collects dated event listings, and independently models fair lines from stored inputs. It publishes static research dashboards and source links. It is **not** a live bookmaker feed, betting advice, or an exhaustive schedule of every event in the world. A linked official page records provenance; it is not, by itself, proof that the page supports every value beside it.

## Current: final 15-sport integration — `/` + `/cadence/` (23 October 2026)

**Start here:** <https://buffedlizard55-lab.github.io/OLBG2/> ·
[all 93 fixture records](cadence/matches.html) · [top-five picks](cadence/picks.html) ·
[728 originated prices](cadence/lines.html) · [33 sourced write-ups](cadence/predictions.html) ·
[15 sport categories](cadence/sports/index.html) · [Flagged for Review](integration.html) ·
[93-row integration audit](research/integration-f0ee1b4a.md).

The root landing page now uses the latest corrected 23 October snapshot rather than presenting the older 22 October, 17-sport dashboard as current. It covers exactly the 15 requested sports and keeps historical desks separate; their counts are never added together.

| Current snapshot item | Result |
|---|---:|
| Official-source fixture records | 93 across 15 sports |
| Priced / deliberately blank-price fixtures | 83 / 10 |
| Originated prices / graded selections | 728 / 122 |
| High-confidence shortlisted selections | 22 |
| Natural / alternate-line high selections inside −250…+10000 | 0 / 8 |
| Written predictions | 33: 22 high, 11 medium |
| Sports with at least five high-confidence write-ups | 2 of 15 (Basketball, Rugby League) |
| Registered sources / sourced fact entries internally checked | 59 / 245 |
| Blank venue fields retained | 48 |
| Publisher-local/display times retained without UTC inference | 61 |
| Currently readable active OLBG listings established by the integration spot check | 0 |

**Coverage boundary:** the 93 rows are not represented as 93 current OLBG listings. One row retains a recorded OLBG event id with a matching registered event URL, but its integration re-read displayed “No tips found.” The other rows are official-context fixtures. The separate [OLBG discovery desk](olbg/index.html) and its review page preserve that distinct provenance. No complete OLBG inventory, every-market coverage, current bookmaker price feed, or five-high-write-ups-per-sport completion is claimed.

Final integration corrected two source/display defects before publication: Cork Gaelic semi-final margins now calculate as +2/+2 from the official scores, and outright/three-way fixture summaries now name the actual leading selection with the corresponding probability. The unsupported Gaelic `olbg_event_id` was removed. Corrections and five open review items are published with evidence links on [Flagged for Review](integration.html).

```sh
python scripts/cadence_seed.py
python scripts/cadence_model.py
python scripts/cadence_predictions.py
python scripts/cadence_build.py
python scripts/cadence_verify.py
python scripts/integration_f0ee1b4a_audit.py
python scripts/build_site.py
python scripts/integration_audit.py
python -m unittest tests.test_integration_f0ee1b4a -v
```

The internal audit passes all 93 fixture rows and 245 sourced fact entries. External official pages were re-read only for the documented NHL, OLBG and Cork GAA spot checks; the audit does not claim that every external source was freshly re-read during integration. CI rebuilds the same artifacts, checks local links, runs the full test suite and drift-checks the current desk, root and audit outputs.

## Earlier: OLBG daily desk — `/olbg/` (23 October 2026)

**Start here:** <https://buffedlizard55-lab.github.io/OLBG2/olbg/> ·
[all matches](olbg/matches.html) · [picks and predictions](olbg/picks.html) ·
[originated markets](olbg/markets.html) · [sources](olbg/sources.html) ·
[Flagged for Review](olbg/flagged.html) · [methodology](olbg/methodology.html) ·
[research record](research/olbg-758c0623.md).

The 19:40:38 UTC snapshot contains **89 upcoming rows across 11 sports**, with all 15 requested categories represented. It keeps **0 active**, **24 last-seen on OLBG**, and **65 official-context-only** rows distinct. There are **54 priced matches**, **58 originated market rows**, and **3 high-confidence predictions**. No current bookmaker quote is claimed. The five-per-sport shortlist is a maximum, not a quota; 35 unpriced matches and the other limitations remain visible with official links.

```sh
python scripts/olbg_seed.py
python scripts/olbg_model.py
python scripts/olbg_predictions.py
python scripts/olbg_build.py
python scripts/olbg_verify.py
python -m unittest tests.test_olbg_758c0623 -v
```

The offline rebuild is deterministic. CI runs the same pipeline and drift-checks `olbg/` and `data/olbg/`; it does not refresh the snapshot.

## Earlier: 15-sport daily brief — `/brief/` (23 October 2026)

**Start here:** <https://buffedlizard55-lab.github.io/OLBG2/brief/> ·
[all matches](brief/matches.html) · [picks](brief/picks.html) · [39 predictions](brief/predictions.html) ·
[OLBG reverse-engineering](brief/olbg.html) · [source ledger](brief/sources.html) ·
[Flagged for review](brief/flagged.html) · [method](brief/methodology.html) · [repo review](brief/review.html).

This desk is built from first-hand reads of 22 official sources and is deterministic from committed captures:

| Item | Value |
|---|---|
| Sports | exactly the 15 named in the brief (Gaelic Football and Hurling under Gaelic Sports) |
| Fixtures published | 113 (87 still upcoming at the 19:45Z cut-off) |
| Fixtures with our own lines | 50, across 11 sports — money line / match winner, handicaps and totals per sport |
| In-band selections (−250…+10000) | 39, one per priced fixture |
| High-confidence picks | 1 inside the price window (Tier A), 6 inside 70% but shorter than −250 (Tier B) |
| Written predictions | 39, minimum 84 words, each fact traceable to its capture |
| Official sources | 22, every one linked on the row it supports |
| Review queue | 10 items, including four sports with fixtures but no price |

**What it will not do.** OLBG's public tips pages render their event tables client-side: three pages returned the literal
text "No tips found" at 19:29Z, 19:30Z and 19:44Z today, so no complete OLBG event inventory can be read by a
non-browser client. The desk reproduces OLBG's sport IDs, URL schema and market vocabulary (see
`/brief/olbg.html`) and takes fixtures from each governing body instead. No OLBG price or tip percentage is used as a
pricing input. Tennis, Cricket, Gaelic Sports, Greyhounds and Darts carry fixtures but no line today; each reason is on
the review page. No prediction asserts an injury, because no official injury feed was readable.

```sh
python scripts/brief_model.py        # captures -> fixtures, inputs, originated markets
python scripts/brief_predictions.py  # validates the 39 write-ups and assigns tiers
python scripts/brief_build.py        # writes /brief/
python scripts/brief_verify.py       # 1,547 structural checks
python -m unittest tests.test_brief   # 18 tests
```

## Previous: evidence-first 15-sport monitor (23 October 2026)

**Start here:** <https://buffedlizard55-lab.github.io/OLBG2/monitor/> ·
[Flagged for Review](monitor/flagged.html) · [source ledger](monitor/sources.html) ·
[field-audit notes](research/monitor-8226c94a.md).

The current request is **15 sports**, not the older 17-sport taxonomy. The new monitor
includes Gaelic Football and Hurling under Gaelic Sports; it does not include esports
or Aussie Rules. Older desks below remain **historical research**, not freshly checked data.

The selected session capture has **24 official-source fixture rows**, **19 OLBG participant
matches**, and **one experimental originated moneyline** (both outcomes). No high-confidence
selection clears the evidence gate. **Full OLBG inventory, exhaustive markets, and five
supported predictions per sport per day remain unmet** and are explicitly flagged.
Missing bookmaker prices, injury reports and unsupported probabilities remain null.

`Deploy Pages` now attempts public-source collection every six hours and on main updates.
It deploys the attempt ledger and raw successful responses without committing bot changes.
A failed refresh never changes the age of stored evidence. The collector extracts OLBG
links and parses MLB schedules; other official fixture parsers, market-price feeds and
unattended evidence-backed prose are not complete. No claim of live full coverage is made.

```sh
python scripts/monitor_seed.py      # reproduce selected agent-read extracts (offline)
python scripts/monitor_build.py     # deterministic monitor from those extracts
python -m unittest discover -s tests
python scripts/integration_audit.py
# Optional diagnostic; the Pages workflow does this unattended:
python scripts/monitor_collect.py
python scripts/monitor_build.py --runtime data/monitor/runtime/latest.json
```

**Price rule:** observed bookmaker American odds must be in −250…+10000. Our fair odds
are separate estimates, never substituted for a missing quote. OLBG tip percentages
are not independently estimated win probabilities. An uncalibrated calculation remains
low confidence regardless of its numeric output.

---

## Historical desks and prior integration records

**15-sport Focus desk (23 October 2026, this brief only):** <https://buffedlizard55-lab.github.io/OLBG2/focus/index.html>

**Published landing page:** <https://buffedlizard55-lab.github.io/OLBG2/>

**Daily Top-5 desk (23 October 2026):** <https://buffedlizard55-lab.github.io/OLBG2/daily/index.html>

**Daily audit desk (23 October 2026, row-by-row official capture):** <https://buffedlizard55-lab.github.io/OLBG2/daily-audit/index.html>

**Consolidated 17-sport desk:** <https://buffedlizard55-lab.github.io/OLBG2/final/index.html>

**Flagged for Review:** <https://buffedlizard55-lab.github.io/OLBG2/daily/flagged.html> · <https://buffedlizard55-lab.github.io/OLBG2/daily-audit/flagged.html> · <https://buffedlizard55-lab.github.io/OLBG2/final/flagged.html> · <https://buffedlizard55-lab.github.io/OLBG2/publication.html> · <https://buffedlizard55-lab.github.io/OLBG2/review/reproducibility.html>

**Cross-layer integrity review:** <https://buffedlizard55-lab.github.io/OLBG2/integration.html>

## Latest integration (22 October 2026)

The [current capture desk](current/index.html) is now linked from root and category navigation and rebuilt in CI. It stores **57 fixture rows across 7 sports**, **55 originated rows**, **2 blank rows**, and **29 model-band predictions across 4 sports**. Ten categories have zero rows. These are counts from `data/current/band.json` and `predictions.json`, not additional unique matches to add to other desks.

**Not freshly externally verified in this integration session:** direct OLBG HTTPS access failed in this sandbox. Existing official captures remain dated evidence, not proof of current fixture status. See the [integration verification ledger](research/integration-83346ec9.md) and the published [Flagged for Review findings](integration.html). Five verified predictions per sport per day, exhaustive markets, observed bookmaker prices, independently calibrated confidence, and unattended fresh collection remain unmet. CI regenerates stored evidence; it does not fetch new fixtures.

## Start here

The repository contains several independently collected, overlapping snapshots. **Do not add their row counts together.** The current landing page is the final integration of `/cadence/`; historical root match pages use the `/verified/` dataset, and `/final/` is a deterministic de-duplicated view of five older input layers. None is a guarantee of full real-world fixture coverage or of current bookmaker prices.

| Desk | Entry point | Checked-in snapshot (2026-10-22) |
|---|---|---|
| **Daily Top-5 desk** | [`daily/index.html`](daily/index.html) | 132 originated upcoming fixtures (2026-10-23–30) across 7 sports, a top-five selection per sport, 25 high-confidence picks and 45 written predictions. Sources and limits in `research/daily-b499dfe1.md`. |
| **Daily audit desk** | [`daily-audit/index.html`](daily-audit/index.html) | Narrower, row-by-row capture fetched 2026-10-22 21:30 UTC: 8 ATP quarter-finals verified against the ATP Tour's own order of play and draws, 9 ICC fixtures verified against the ICC, 288 originated prices, 5 written picks (≥30 words, each fact linked), 15 review items. Two sports have rows; the other 15 of the 17 eligible sports are each accounted for, with the reason, on the landing page and the flagged page. Rebuilt and drift-checked in CI. |
| **Daily picks desk** | [`daily-picks/index.html`](daily-picks/index.html) | This session's 23–25 October board: 38 fixtures across 7 sports, 224 originated prices, 28 picks, 28 written predictions, 19 NHL conflict rows for review. |
| **Current capture desk** | [`current/index.html`](current/index.html) | Independent 22 October capture; fixture, price, prediction, source and review tables. Overlaps other desks; counts must not be added. Rebuilt and drift-checked in CI. These are stored captures, not a live feed. |
| **Historical root match pages** | [`matches.html`](matches.html) | Historical 22 October data: 188 rows across 14 of 17 eligible sports; 154 rows with originated lines, 34 unlined, and 14 price-band selections/writeups on the root dashboard archive. The separate `/verified/` research page has 16 additional research writeups. These pages are not the current landing snapshot. |
| **Consolidated desk** | [`final/index.html`](final/index.html) | 382 deduplicated rows across all 17 eligible sports; 339 originated and 43 unlined. The union uses `/verified/`, `/hub/`, `/board/`, `/slate/`, and `/forward/`. It contains 19 featured model picks. |
| **Forensic origination portal** | [`portal/index.html`](portal/index.html) | Separate 244-row audit snapshot: 220 originated, 24 explicitly unlined; includes its own sport pages, predictions, sources, and review queue. |
| **Board** | [`board/index.html`](board/index.html) | Checked-in 207-row snapshot. A deterministic rebuild using the current forward-window capture produces 277 rows; the generated update is held for review because two tests in the board owner's scope still assert the older 207/167 counts. See `research/reproducibility-audit-dc72bac4.md`. |
| **Verified desk** | [`verified/index.html`](verified/index.html) | Root dashboard's source dataset and 17 category pages; 188 rows, 154 originated. |
| **Forward window** | [`forward/index.html`](forward/index.html) | 93 scheduled rows from the checked-in NHL, MLB, and EuroCup capture files. |
| **Other research layers** | [`hub/index.html`](hub/index.html), [`slate/index.html`](slate/index.html), [`evidence/index.html`](evidence/index.html), [`audit65/index.html`](audit65/index.html), [`live/index.html`](live/index.html), [`survey/index.html`](survey/index.html), [`site/index.html`](site/index.html) | Separate snapshots and audits with their own scopes, capture dates, evidence limits, and flagged items. They overlap with other desks. |

The root verified desk has 144 fixture-scoped URLs and 44 competition-scoped URLs. The latter are explicitly identified in its review/methodology pages; an official competition link does not independently prove a particular fixture detail. Every unlined value is intentionally blank with a reason rather than inferred. The consolidated desk retains row-level provenance and publishes a separate review page.

## Sport scope

The working taxonomy contains 17 eligible sports. Excluded categories include soccer/football, boxing, UFC/MMA, American football, hurling, horse racing, cycling, and specials. The precise interpretation of the brief's separate use of “football” and “American football” is disclosed as an open scope issue; the project does not silently treat that wording as settled. Zero rows in a category mean only that the particular snapshot contains no row for it, not that the sport has no fixtures.

## Prices and predictions

Prices are model-derived fair prices, not bookmaker quotes. The `high` label is a model confidence category, not a guarantee. For the stricter focus selection, the relevant condition is model probability of at least 70% **and** fair American odds from −250 to +10000 (decimal 1.40–101.00). Each published desk states its own model and selection rules; do not compare labels across separate snapshots without reading their methodology.

Prediction paragraphs are generated only where the selected data layer supplies relevant sourced inputs. The links and review ledgers let readers inspect those inputs. Passing structural tests does not establish that every linked official page was freshly fetched or that every narrative claim is accurate. The [`publication review`](publication.html) records source-access attempts that failed in this environment; those values remain unverified rather than being presented as newly checked facts.

## Repository map

```text
index.html, matches.html, picks.html, flagged.html, verification.html  root research desk
daily/                                                               daily top-five desk: 132 fixtures, 25 picks, 45 predictions
daily-audit/                                                         daily audit: ATP + ICC rows re-read from the governing body
final/                                                               consolidated 17-sport dashboard
portal/                                                              independent origination / audit portal
verified/, forward/, board/, hub/, slate/, live/, survey/, site/     overlapping evidence layers
integration.html, evidence/, audit65/, publication.html               integrity and review pages
sports/                                                               root desk's eligible-sport pages

data/                                                                 committed inputs, snapshots, predictions, sources, flags
data/daily-audit/capture/                                             verbatim rendered text of every page fetched for the daily audit
scripts/                                                              deterministic builders, models, and structural verifiers
tests/                                                                repository unittest suite
research/                                                              capture notes and audit reports
COORDINATION.md                                                       shared task board and integration history
```

## Rebuild and verify locally

The pipelines use Python's standard library. From the repository root, the principal generation order is:

```bash
python3 scripts/daily_seed.py && python3 scripts/daily_model.py && python3 scripts/daily_verify.py && python3 scripts/daily_build.py
python3 scripts/daily_audit_model.py && python3 scripts/daily_audit_build.py
python3 scripts/daily_seed.py && python3 scripts/daily_model.py && python3 scripts/daily_build.py && python3 scripts/daily_verify.py
python3 scripts/daily_picks_data.py && python3 scripts/daily_picks_predictions.py && python3 scripts/daily_picks_flags.py && python3 scripts/daily_picks_build.py
python3 scripts/current_seed.py && python3 scripts/current_model.py && python3 scripts/current_build.py
python3 scripts/verified_seed.py && python3 scripts/verified_model.py && python3 scripts/verified_build.py
python3 scripts/forward_seed.py && python3 scripts/forward_model.py && python3 scripts/forward_build.py
python3 scripts/live_model.py && python3 scripts/live_build.py
python3 scripts/board_seed.py && python3 scripts/board_model.py && python3 scripts/board_build.py
python3 scripts/hub_seed.py && python3 scripts/hub_model.py && python3 scripts/hub_build.py && python3 scripts/hub_verify.py
python3 scripts/slate_seed.py && python3 scripts/slate_model.py && python3 scripts/slate_build.py
python3 scripts/portal_seed.py && python3 scripts/portal_model.py && python3 scripts/portal_build.py && python3 scripts/portal_verify.py
python3 scripts/evidence_integrity.py && python3 scripts/audit65.py
python3 scripts/final_consolidate.py && python3 scripts/final_predictions.py && python3 scripts/final_flags.py && python3 scripts/final_build.py
python3 scripts/survey_sync_inventory.py && python3 scripts/survey_lines.py && python3 scripts/survey_analyse.py && python3 scripts/survey_build.py && python3 scripts/survey_verify.py
python3 scripts/build.py && python3 scripts/build_site.py && python3 scripts/integration_audit.py
python3 -m unittest discover -s tests -v
```

Generation is deterministic from the committed captures; it does not fetch OLBG or governing-body pages. The current CI workflow validates selected pipelines, local links, and tests before Pages deployment. Its drift gate does not cover every independently generated sub-site, so local rebuild success should not be mistaken for a factual source audit. That CI coverage limitation is logged in [`COORDINATION.md`](COORDINATION.md).

For model rules and limitations see [`METHODOLOGY.md`](METHODOLOGY.md), each desk's methodology page, and the appropriately labeled **Flagged for Review** pages. Research, not betting advice. 18+.
