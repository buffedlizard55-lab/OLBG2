# OLBG2 — sports schedule research, originated lines, and review flags

OLBG2 is a static research project that examines [OLBG.com](https://www.olbg.com)'s sports taxonomy and selected event listings, records source material, and demonstrates independent line-origination models. It is **not** a complete or continuously updated OLBG slate, and its stored event rows must not all be treated as officially verified fixtures. Model prices and confidence labels are estimates, not bookmaker odds or guarantees.

**Published dashboard:** <https://buffedlizard55-lab.github.io/OLBG2/>

**Evidence-status review:** <https://buffedlizard55-lab.github.io/OLBG2/integration.html>

**Sport survey:** <https://buffedlizard55-lab.github.io/OLBG2/survey/>

## Evidence status — read before using the counts

This repository contains multiple separately built snapshots. Their counts are **stored rows, not a verified count of unique upcoming matches**. The layers have known overlaps, different scopes, and different evidence limitations. Do not add their totals together.

The official-source provenance audit (`python3 scripts/official_source_audit.py`) reports that **all 145 survey inventory rows lack an explicit official fixture-source field**. The OLBG URLs on those records document OLBG listing provenance; they do not independently confirm that the fixture, date, or competition is correct. The 14 prediction-fact citations now live in `data/survey/archived_predictions.json` after the odds-window regrade (see below); 4 URLs are on candidate official domains and the rest are outside the audit's conservative allowlist. A domain match is not proof that a page supports a claim. See the [audit report](research/official-source-audit-18eca832.md), [cross-layer review](integration.html), and [Flagged for Review](flagged.html).

| Layer | Entry point | Snapshot contents (not an external verification claim) |
|---|---|---|
| **Root dashboard** | [`index.html`](index.html) | 47 stored match rows, 45 originated-line records, 2 active window-compliant high-confidence picks plus 7 archived narratives; 24 open and 4 closed review items. Built by `scripts/model.py` and `scripts/build_site.py`. |
| **Evidence desk** | [`site/index.html`](site/index.html) | Separate NHL/NBA layer with 25 stored fixture rows and 64 market records, 1 active high pick and 4 archived narratives, plus its own source register and 10 flags. Built by `scripts/engine.py` and `scripts/build.py`. |
| **Sport survey** | [`survey/index.html`](survey/index.html) | 145 OLBG-discovered inventory entries across its 15-sport taxonomy; 26 originated lines, 0 active high predictions and 5 narratives archived under the odds window, with 8 review flags. The inventory rows are not all officially fixture-verified. |
| **Live slate** | [`live/index.html`](live/index.html) | 11 fresh URC/MLB fixtures with three originated markets each; 0 active highs and 4 archived URC narratives, 12 flags. |
| **Verified desk** | [`verified/index.html`](verified/index.html) | 155 rows (112 originated, 43 unlined) across 17 eligible sports; 4 window-compliant high picks and 20 archived chalk narratives, 13 flagged items. |

## Odds-window confidence rule (2026-10-22)

A selection is labelled **high** in every layer only when its model probability is at least **70%** *and* its
fair no-vig American price sits inside **[-250, +10000]** (-250 = decimal 1.40 = 71.43% implied, so the practical
band is 70.0%–71.43%). Heavy chalk previously labelled high was regraded medium/low; its written prediction was
moved verbatim into a per-layer `archived_*.json` file with the regrade reason, fair price and sources, and each
site renders an archive section (or an explicit empty-state card where nothing qualifies). Full audit:
[`research/odds-window-audit-1bb45081.md`](research/odds-window-audit-1bb45081.md).

These are dated snapshots, not an automatically refreshed feed. Prior captures span 18–21 October 2026; the builders regenerate pages from checked-in data but do not retrieve new schedules. Recheck every event and source before treating it as upcoming or using its model output.

## Handball addition (2026-10-21 07:06–07:45 UTC)

The root dashboard now carries the twelve EHF Champions League Men round-5 fixtures of 21–22 October 2026.
Each pairing, date and published throw-off time was read from the official EHF match centre
(<https://ehfcl.eurohandball.com/men/2026-27/matches/>), and each club's group-phase wins, draws, losses, goals
for and goals against came from the official standings on the same site
(<https://ehfcl.eurohandball.com/men/2026-27/standings/>). All twelve were lined (three-way match winner,
handicap and match total; 84 prices). Of the five original high-confidence write-ups, only the Paris
Saint-Germain pick (70.2%, fair -238) survives the 2026-10-22 odds window; the four chalk narratives (Aalborg,
Barça, Sporting, Magdeburg, -370 to -588) are archived in `data/predictions_archived.json` with per-fact
source links. The line-by-line table and the irregularities found are in
[`research/handball-ehf-73620ec4.md`](research/handball-ehf-73620ec4.md).

Handball is therefore a fifth covered sport in the root layer (Ice Hockey, Basketball, Rugby Union, Cricket,
Handball). The other twelve in-scope sports remain uncovered there and are listed individually on the
[Flagged for Review](flagged.html) page; the dashboard's own coverage table shows this layer's rows, its lines
and the survey's event count for every one of the 17 sports. This addition does not change the survey layer,
the evidence desk or any earlier session's files.

## Cross-layer scope and overlap

The root scope configuration lists 17 included sports. The survey taxonomy lists 15 and excludes Greyhounds and Gaelic Football. This disagreement is unresolved and published for review; neither layer establishes the final interpretation of the brief. The original brief's use of “football” is also ambiguous alongside its separate mention of American football.

The layers are not deduplicated. At least Afghanistan v Bangladesh and New Zealand v India appear in both the root dashboard and survey; the root dashboard and evidence desk also share NHL/NBA coverage. Do not describe the datasets as disjoint or report a combined unique-match total.

The survey records inventory entries for sports beyond the root dashboard's original capture, but this does not establish exhaustive OLBG coverage. Its reported zero-entry results for Rugby League, Aussie Rules, and eSports are snapshot observations, not proof that OLBG has no listings outside the capture window. The [integration review](integration.html) and the survey's [Flagged for Review](survey/flagged.html) page list unresolved evidence and scope issues.

## Project scope

The brief excludes soccer, boxing, UFC/MMA, American football, hurling, horse racing, cycling, and specials. OLBG taxonomy, scope decisions, and data layers are documented separately; Greyhounds and Gaelic Football remain a flagged interpretation question rather than a settled exclusion.

## Repository layout

```text
index.html, picks.html, flagged.html, methodology.html, sources.html  root dashboard pages
sports/*.html                                                       root sport pages
integration.html                                                    cross-layer evidence-status review
site/**                                                             evidence desk snapshot and pages
survey/**                                                           sport survey pages

data/inputs/*.json                                                  root dashboard inputs
data/matches.json, data/predictions.json, data/flagged.json          root dashboard outputs and review queue
 data/desk/*.json                                                   evidence desk snapshot data
 data/survey/**                                                     survey inventory, line records and flags
 data/sources.json                                                  root dashboard source register

scripts/model.py, build_site.py                                      root dashboard model and builder
scripts/engine.py, build.py                                          evidence desk model and builder
scripts/survey_*.py                                                  survey pipeline and checks
scripts/official_source_audit.py                                     read-only survey provenance classification
scripts/integration_audit.py                                        cross-layer link and evidence disclosure checks
tests/                                                               automated structural tests
research/                                                            collection and audit notes
COORDINATION.md                                                      task board and session log
```

## Rebuild and verify

All scripts use the Python standard library. From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build_site.py
python3 scripts/survey_build.py
python3 scripts/survey_verify.py
python3 scripts/integration_audit.py
python3 scripts/official_source_audit.py
```

The builders and tests validate internal structure, model rules, and local links. The official-source audit classifies URL domains and reports missing provenance fields; it does **not** fetch pages or validate their contents. CI likewise does not collect live schedules. Passing these checks is not proof of factual accuracy, official-source support, freshness, complete market coverage, or an exhaustive sport inventory.

For model formulas and confidence thresholds, see [METHODOLOGY.md](METHODOLOGY.md) and [survey/METHODOLOGY.md](survey/METHODOLOGY.md). For current caveats, use the [evidence-status review](integration.html) and clearly labeled review pages. This project is research, not betting advice. 18+.
