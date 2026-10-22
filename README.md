# OLBG2 — eligible-sports schedule, originated lines, and sourced predictions

OLBG2 is a static research project that reverse-engineers [OLBG.com](https://www.olbg.com)'s sports taxonomy,
records fixtures for every eligible sport, originates its own prices from official governing-body statistics, and
publishes every value next to the official page it came from. It is **not** a live bookmaker feed, not betting
advice, and not a complete snapshot of world sport: it is a dated capture with its gaps disclosed.

**Published dashboard:** <https://buffedlizard55-lab.github.io/OLBG2/>

**Flagged for review:** <https://buffedlizard55-lab.github.io/OLBG2/flagged.html>

**Cross-layer evidence review:** <https://buffedlizard55-lab.github.io/OLBG2/integration.html>

## What the root site is

The dashboard at the repository root is the unified, deduplicated view over the multi-sport desk in
[`verified/`](verified/index.html). It carries **155 fixtures across 15 of the 17 eligible sports**, each row with
its official source link, a verification badge, and — where the model could be supported — moneyline, handicap and
total prices. 112 rows are fully originated; 43 are blank with a written reason.

| Layer | Entry point | Snapshot contents (not an external verification claim) |
|---|---|---|
| **Unified dashboard** | [`index.html`](index.html) | 155 fixtures, 15 sports, 112 originated rows, 13 price-band picks, 33 written predictions, 18 open review items. Built by `scripts/build_site.py` from `data/verified/**`. |
| **Verified multi-sport desk** | [`verified/index.html`](verified/index.html) | The same 155 rows in their original layout, plus audit and methodology pages. Built by `scripts/verified_seed.py` → `verified_model.py` → `verified_build.py`. |
| **Root-layer archive** | [`archive.html`](archive.html) | The earlier 47-row root capture, preserved with its own source links. Superseded for NHL, NBA, URC, cricket and handball, but not deleted. |
| **Evidence desk v2** | [`site/index.html`](site/index.html) | Independent NHL/NBA layer with 25 stored fixture rows and 64 market records. Built by `scripts/engine.py` and `scripts/build.py`. |
| **Sport survey** | [`survey/index.html`](survey/index.html) | 130 OLBG-discovered inventory entries across its 15-sport taxonomy; 11 originated lines, 2 predictions. Inventory rows are not all fixture-verified. |

The layers are **not** disjoint and must not be added together. They represent separate audit passes over
overlapping windows; use the unified dashboard for the published dataset and the archive page for provenance.

## Scope

The brief excludes soccer/football, boxing, UFC/MMA, American football, hurling, horse racing, cycling and
specials. The remaining 17 sports form the eligible taxonomy. Aussie Rules (AFL off-season) and eSports returned
no active fixtures in this window; they are listed with zero rows rather than silently skipped. Greyhounds and
Gaelic Football are **not** on the exclusion list, so they are in scope; the survey layer's older 15-sport taxonomy
that omitted them is disclosed and superseded.

The brief's use of “football” next to a separate “American football” entry remains the one unresolved scope
question. It is recorded as an interpretation flag rather than resolved by assumption.

## Verification, blanks and freshness

- Every published row carries a link to an official governing-body, league or tour page.
- 92 of the 155 rows cite a URL that identifies the individual fixture; the other 63 cite a competition or
  rankings page. That difference is shown on every table and disclosed as **VF-11** on the flagged page.
- Where an official input was missing (client-rendered rankings, one-match samples, unconfirmed venues, 2027
  futures without rosters), the value is **blank** and the reason is published. Nothing was inferred.
- 15 rows (12 NHL fixtures, 3 MLB World Series games) were re-read on **2026-10-22**; the other 140 retain their
  **2026-10-21** capture stamp. The snapshot is dated, not continuously refreshed.
- 59 rows are dated 2026-10-21 and are labelled **past** everywhere; they stay visible for audit and are never
  presented as upcoming tips.

## Prices and confidence

Model prices are fair decimals derived from the models in [METHODOLOGY.md](METHODOLOGY.md), not bookmaker quotes.

- Confidence: **high** ≥72% model probability, **medium** ≥60%, **low** below 60%.
- Price band from the brief: **−250 to +10000** decimal (1.40–101.00). A 70%+ probability cannot be priced above
  1.43, so the only window satisfying both a ≥70% probability and the −250 floor is 70.0–71.4%.
- The 20 original high-confidence picks are priced 1.02–1.39 and are labelled **outside band**.
- 13 additional handicap/total picks at **1.40–1.42** carry their own ≥30-word predictions and official facts;
  these are the **price-band** picks the brief asked for.

## Repository layout

```text
index.html, matches.html, picks.html, verification.html      unified dashboard pages
flagged.html, methodology.html, sources.html, archive.html   review, method, sources, provenance
sports/index.html, sports/<slug>.html                        17 eligible sport pages
integration.html                                             cross-layer evidence-status review
verified/**                                                  multi-sport desk pages (source dataset)
site/**                                                      evidence desk snapshot and pages
survey/**                                                    sport survey pages

data/verified/*.json                                         unified dataset, predictions, band, flags
data/matches.json, data/predictions.json, data/flagged.json  archived root-layer outputs
data/desk/*.json                                             evidence desk snapshot data
data/survey/**                                               survey inventory, line records and flags

scripts/verified_seed.py, verified_model.py, verified_build.py   verified desk pipeline
scripts/build_site.py                                        unified dashboard builder
scripts/model.py, build.py                                   archived root layer and evidence desk
scripts/survey_*.py                                          survey pipeline and checks
scripts/official_source_audit.py                             read-only survey provenance classification
scripts/integration_audit.py                                 cross-layer link and disclosure checks

tests/                                                       automated structural tests (61)
research/                                                    collection and audit notes
COORDINATION.md                                              task board and session log
```

## Rebuild and verify

All scripts use the Python standard library. From the repository root:

```bash
python3 scripts/verified_seed.py && python3 scripts/verified_model.py && python3 scripts/verified_build.py
python3 scripts/build_site.py
python3 scripts/build.py
python3 scripts/survey_build.py && python3 scripts/survey_verify.py
python3 scripts/integration_audit.py
python3 -m unittest discover -s tests
```

Expected: the builder reports `10 root pages + 17 sport pages / 155 rows, 112 originated, 13 band picks / 33
predictions (13 band) / 18 verified review items`; the integration audit reports zero local link errors; the suite
reports 61 tests passing.

The builders and tests validate internal structure, model rules, source allowlists and local links. They do not
fetch pages, and a passing check is not proof that every external page supports every adjacent claim. CI rebuilds
the static layers and fails if the generated HTML drifts from the checked-in files.

For the formulas, thresholds and known limitations see [METHODOLOGY.md](METHODOLOGY.md) and the
[methodology page](methodology.html). For open questions use [Flagged for Review](flagged.html) and the
[cross-layer review](integration.html). Research, not betting advice. 18+.
