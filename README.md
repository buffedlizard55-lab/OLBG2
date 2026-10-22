# OLBG2 — multi-sport schedule research and line origination

OLBG2 records OLBG's published sports taxonomy, collects dated event listings, and independently models fair lines from stored inputs. It publishes static research dashboards and source links. It is **not** a live bookmaker feed, betting advice, or an exhaustive schedule of every event in the world. A linked official page records provenance; it is not, by itself, proof that the page supports every value beside it.

**Published landing page:** <https://buffedlizard55-lab.github.io/OLBG2/>

**Consolidated 17-sport desk:** <https://buffedlizard55-lab.github.io/OLBG2/final/index.html>

**Flagged for Review:** <https://buffedlizard55-lab.github.io/OLBG2/final/flagged.html> · <https://buffedlizard55-lab.github.io/OLBG2/publication.html> · <https://buffedlizard55-lab.github.io/OLBG2/review/reproducibility.html>

**Cross-layer integrity review:** <https://buffedlizard55-lab.github.io/OLBG2/integration.html>

## Start here

The repository contains several independently collected, overlapping snapshots. **Do not add their row counts together.** The root dashboard is the `/verified/` desk; `/final/` is a deterministic de-duplicated view of five input layers. Neither is a guarantee of full real-world fixture coverage or of current bookmaker prices.

| Desk | Entry point | Checked-in snapshot (2026-10-22) |
|---|---|---|
| **Daily picks desk** | [`daily/index.html`](daily/index.html) | This session's 23–25 October board: 38 fixtures across 7 sports, 224 originated prices, 28 picks (18 high confidence, 6 high **and** inside the −250/+10000 band), 28 hand-written predictions, and 10 sports named with the reason they carry no line. Built from pages read on 22 October; 19 conflicts with NHL team lines stored on `/final/` are published for review. |
| **Current capture desk** | [`current/index.html`](current/index.html) | Independent 22 October capture; fixture, price, prediction, source and review tables. Overlaps other desks; counts must not be added. Rebuilt and drift-checked in CI. These are stored captures, not a live feed. |
| **Root dashboard** | [`index.html`](index.html) | 188 rows across 14 of 17 eligible sports; 154 rows with originated lines, 34 unlined, and 14 price-band selections/writeups on the root dashboard. The separate `/verified/` research page has 16 additional research writeups. Price-band selections are a separate filter, not the count of rows labelled high confidence. |
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
final/                                                               consolidated 17-sport dashboard
portal/                                                              independent origination / audit portal
verified/, forward/, board/, hub/, slate/, live/, survey/, site/     overlapping evidence layers
integration.html, evidence/, audit65/, publication.html               integrity and review pages
sports/                                                               root desk's eligible-sport pages

data/                                                                 committed inputs, snapshots, predictions, sources, flags
scripts/                                                              deterministic builders, models, and structural verifiers
tests/                                                                repository unittest suite
research/                                                              capture notes and audit reports
COORDINATION.md                                                       shared task board and integration history
```

## Rebuild and verify locally

The pipelines use Python's standard library. From the repository root, the principal generation order is:

```bash
python3 scripts/daily_data.py && python3 scripts/daily_predictions.py && python3 scripts/daily_flags.py && python3 scripts/daily_build.py
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
