# OLBG2 — sports schedule research, originated lines, and review flags

OLBG2 is a static research project that examines [OLBG.com](https://www.olbg.com)'s sports taxonomy and selected event listings, records source material, and demonstrates independent line-origination models. It is **not** a complete or continuously updated OLBG slate, and stored rows must not all be treated as officially verified fixtures. Model prices and confidence labels are estimates, not bookmaker odds or guarantees.

**Current verified multi-sport desk:** <https://buffedlizard55-lab.github.io/OLBG2/verified/>

**Root dashboard:** <https://buffedlizard55-lab.github.io/OLBG2/>

**Evidence-status review:** <https://buffedlizard55-lab.github.io/OLBG2/integration.html>

## Evidence status — read before using the counts

This repository contains five separately built snapshots. Their counts are **stored rows, not a verified count of unique upcoming matches**. The layers overlap, use different taxonomies and capture windows, and have different evidence limitations. **Do not add their totals together.**

| Layer | Entry point | Stored snapshot contents — not a blanket external-verification claim |
|---|---|---|
| **Verified multi-sport desk** | [`verified/index.html`](verified/index.html) | **22 October 2026:** 166 catalogued rows — 126 static OLBG-discovered cards and 40 clearly labelled official supplements. 92 originated lines across seven sports, 74 deliberately unlined rows, and three High picks with unique official-fact narratives. Built by `scripts/verified_seed.py`, `scripts/verified_refresh_data.py`, `scripts/verified_model.py`, and `scripts/verified_build.py`. |
| **Live slate** | [`live/index.html`](live/index.html) | **21 October 2026:** 11 URC/MLB fixture rows, 33 market-line records, and four written High picks. This is a separate historical capture, not part of the verified desk's 166-row total. |
| **Root dashboard** | [`index.html`](index.html) | 47 stored match rows, 45 originated-line records, and nine written High picks at its recorded snapshot. Built by `scripts/model.py` and `scripts/build_site.py`. |
| **Evidence desk** | [`site/index.html`](site/index.html) | Separate NHL/NBA snapshot with 25 fixture rows and 64 market records, plus its own source register and flags. Built by `scripts/engine.py` and `scripts/build.py`. |
| **Sport survey** | [`survey/index.html`](survey/index.html) | 145 inventoried entries, 26 line records, and a separate review queue. Its rows are not all independently fixture-verified. |

These are dated snapshots, not an automatically refreshed feed. Captures span 18–22 October 2026; builders regenerate pages from checked-in data but do not retrieve new schedules. Recheck every event and official source before treating a row as upcoming or using its model output.

The read-only provenance classifier (`python3 scripts/official_source_audit.py`) currently reports **145/145 survey inventory rows** and **14/14 survey prediction-fact citations** on official-domain candidates. A domain match is not proof that a page supports a claim. See the [audit report](research/official-source-audit-18eca832.md), [cross-layer review](integration.html), and each layer's Flagged for Review page.

## Current verified-desk scope and limits

The verified desk checks all 17 eligible OLBG sport hubs and blocks the eight requested exclusions: soccer/football, horse racing, American football, boxing, UFC/MMA, hurling, cycling, and specials. Gaelic Football and Greyhounds are eligible; Greyhounds currently has a zero-row page because its hub displayed “No tips found.”

The 166-row desk is the fullest supportable **static rendered** capture, plus official supplements. It is not exhaustive dynamic OLBG coverage: unresolved **Load More Tips** controls remain flagged. Official supplements never carry an OLBG link or imply that a current OLBG card was observed.

Every row has an official source or explicitly labelled official review URL, a discovery state, an official-confirmation state, and a time basis. Relative OLBG Today/Tomorrow labels remain raw text unless an official page independently establishes the date/time. Missing inputs stay blank; a URL alone is not treated as factual verification.

High confidence requires both:

- published model probability **strictly greater than 70%**; and
- fair American price from **-250 through +10000 inclusive**.

Each High pick also has a unique narrative of at least 30 words, an explicit selection, and relevant official form or recent-match evidence. Strong favourites shorter than -250 remain Medium. See [`verified/methodology.html`](verified/methodology.html) for the exact formulas and model-specific caveats.

## Cross-layer scope and overlap

The current verified taxonomy contains 17 eligible sports. The older survey was remediated to the same 17-sport scope; historical documentation may describe its earlier 15-sport state. Those records are retained as history, not as the current interpretation.

The layers are not deduplicated. NHL, NBA, rugby, handball, baseball, tennis, darts, cricket, and other events can appear in multiple snapshots. The root dashboard and evidence desk also share NHL/NBA coverage. Never report a combined unique-match total by summing layer rows.

The historical root-handball addition used the official EHF match centre and standings for twelve 21–22 October fixtures. Its record remains in [`research/handball-ehf-73620ec4.md`](research/handball-ehf-73620ec4.md). The current verified handball page is a separate 22 October capture with five originated EHF rows and 15 unlined domestic/international cards.

## Repository layout

```text
verified/**, data/verified/**                                      current verified desk pages and data
live/**, data/live/**                                              separate 21 October live-slate snapshot
index.html, picks.html, flagged.html, methodology.html, sources.html
sports/*.html, assets/**                                           root dashboard pages
integration.html                                                   cross-layer evidence-status review
site/**, data/desk/**                                              evidence-desk snapshot and data
survey/**, data/survey/**                                          sport survey pages and data

data/inputs/*.json                                                 root/shared official inputs
data/matches.json, data/predictions.json, data/flagged.json         root outputs and review queue
data/sources.json                                                  root source register

scripts/verified_*.py                                              verified source register, model and builder
scripts/live_*.py                                                  live-slate model and builder
scripts/model.py, build_site.py                                    root model and builder
scripts/engine.py, build.py                                        evidence-desk model and builder
scripts/survey_*.py                                                survey pipeline and checks
scripts/official_source_audit.py                                   read-only survey provenance classifier
scripts/integration_audit.py                                      cross-layer links and evidence disclosures
tests/                                                             automated structural/mathematical tests
research/                                                          collection and audit notes
COORDINATION.md                                                    task board and publish ledger
```

## Rebuild and verify

All scripts use the Python standard library. From the repository root, the CI-equivalent sequence is:

```bash
python3 scripts/verified_seed.py
python3 scripts/verified_model.py
python3 scripts/verified_build.py
python3 scripts/live_model.py
python3 scripts/live_build.py
python3 scripts/build.py
python3 scripts/survey_sync_inventory.py
python3 scripts/survey_lines.py
python3 scripts/survey_analyse.py
python3 scripts/survey_build.py
python3 scripts/survey_verify.py
python3 scripts/build_site.py
python3 scripts/integration_audit.py
python3 -m unittest discover -s tests -v
python3 scripts/official_source_audit.py
```

The builders and tests validate internal structure, model rules, provenance states, and local links. The official-source audit classifies URL domains and reports missing provenance fields; it does **not** fetch pages or validate their contents. CI does not collect live schedules. Passing these checks is not proof of factual accuracy, official-source support, freshness, complete market coverage, or exhaustive sport inventory.

For older root-model formulas see [METHODOLOGY.md](METHODOLOGY.md); for the current verified models use [verified/methodology.html](verified/methodology.html). This project is research, not betting advice. 18+.
