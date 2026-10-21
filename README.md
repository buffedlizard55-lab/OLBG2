# OLBG2 — verified fixtures, originated lines, confidence-graded picks

A reverse-engineered view of [OLBG.com](https://www.olbg.com)'s sports coverage. The fixture list is rebuilt from
OLBG's sport hubs, then **every fixture is re-verified against the official league or governing body** before
anything is published. Betting lines are originated here from verified performance data — no bookmaker price is
used anywhere — and each selection is graded `high`, `medium` or `low` confidence.

**Live site:** https://buffedlizard55-lab.github.io/OLBG2/

The repository holds two published layers, both live:

| Layer | Entry point | What it is |
|---|---|---|
| **Slate dashboard** | `/index.html` | 33 verified fixtures · 30 originated lines · 4 high-confidence predictions · 19 flagged items. Built by `scripts/model.py` → `data/matches.json` → `scripts/build_site.py`. |
| **Evidence desk v2** | `/site/index.html` | 25 verified fixtures · 64 markets originated (money line, puck line, total) · 4 sourced high-confidence predictions · 8 flagged items. Built by `scripts/engine.py` + `scripts/build.py` from `data/desk/`. |

Both layers are live and independent. The root dashboard was contributed by the `42fb7792` session; the
`4a778bb7` session rebuilt the `site/` layer, which had previously been the two-fixture audit. Each layer states
its own snapshot and scope, and neither reuses a bookmaker price.

The two layers differ in breadth and depth and **do not share a fixture file**. Where they overlap (NHL, NBA) they
were verified against the same league sources but originate lines with different models, so their prices differ.
Treat each page's own numbers as the authoritative statement of that page's method; the method pages are the
contract.

> Integration note (2026-10-21): the merge that combined these layers preserved the root dashboard and its
> pipeline byte-for-byte apart from the navigation label (`Prior audit` → `Evidence desk v2`) and a footer link.
> `scripts/build.py`, `tests/**` and `site/**` now belong to the evidence desk; the older two-fixture audit data
> remains at `data/events.json` for provenance and is no longer built by either pipeline.

## What is in the dashboard release (capture window 2026-10-21 05:10–05:45 UTC)

| Sport | Fixtures | Lines originated | High confidence |
|---|---|---|---|
| Ice Hockey (NHL) | 12 | 11 | 4 |
| Basketball (NBA) | 11 | 11 | 0 |
| Rugby Union (URC) | 8 | 8 | 0 |
| Cricket (ICC) | 2 | 0 | 0 |
| **Total** | **33** | **30** | **4** |

Two of the 33 rows are deliberately blank: the Sharks' goal totals were never captured, and the ICC ranking
table did not render, so no cricket line could be originated without inventing an input. Both are on the
[Flagged for review](https://buffedlizard55-lab.github.io/OLBG2/flagged.html) page with source links.

## Evidence desk v2 (capture 2026-10-21 05:55 UTC)

| Sport | Window | Fixtures | Markets | High confidence |
|---|---|---|---|---|
| Ice hockey (NHL) | Oct 21–22 | 14 | Money line, puck line, total | 4 |
| Basketball (NBA) | Oct 21 | 11 | Money line, spread (baseline only) | 0 |

`scripts/engine.py` originates prices from official inputs only: NHL goal difference per game shrunk toward the
league mean by 12 games, plus a 0.25-goal home edge, logistic scale 1.2, no-vig American prices, half-goal totals
(σ = 1.7). NBA has no 2026-27 sample, so every club is league-average with a 2.5-point home edge and no total.
Confidence is computed: **high** needs ≥ 13 points of win-probability edge, ≥ 7 games per side and an evidence
pack (the fixture's own gamecenter cited in the prediction); a large edge without a pack is capped at medium.

`scripts/build.py` fails the build if any fixture, pick or flag cites a URL outside the allow-listed registry
(`data/desk/sources.json`), if an excluded sport appears, if a pick contradicts the model's favourite, if a
prediction is under 30 words or duplicated, or if a high-confidence row lacks a prediction.

```sh
python -m unittest discover -s tests -v   # 28 tests, including link resolution and all data rules
python scripts/build.py                   # regenerates site/ deterministically
```

## Scope

Included: Tennis, Basketball, Golf, Cricket, Snooker, Rugby Union, Rugby League, Baseball, Ice Hockey,
Motor Racing, Darts, Handball, Volleyball, Aussie Rules, eSports, Gaelic Football, Greyhounds.

Excluded by the brief: football (soccer), horse racing, American football, boxing, cycling, hurling and
"specials". UFC/MMA are filed under Boxing on OLBG, so that exclusion covers them. Enforced in
`scripts/config.py` and, for the prior pipeline, in `data/events.json` + `scripts/build.py`.

## Repository layout

```
index.html, picks.html, flagged.html, methodology.html, sources.html   dashboard (this release, generated)
sports/<sport>.html                                                    per-sport dashboard pages
assets/style.css                                                       dashboard styling
data/inputs/*.json                                                     verified inputs + fixtures
data/matches.json                                                      generated dataset (lines, picks)
data/predictions.json                                                  high-confidence write-ups + sources
data/flagged.json                                                      review queue (19 items)
data/sources.json                                                      source register (26 sources)
scripts/config.py, model.py, build_site.py                             dashboard pipeline
data/events.json, scripts/build.py, tests/test_build.py                original audit pipeline (kept green by CI)
site/**                                                                evidence desk v2 (own engine + build, CI-checked)
research/olbg-reverse-engineering.md, research/collection-log.md       OLBG schema + every fetch
COORDINATION.md                                                        shared task board and merge log
```

## Rebuild

Dashboard:

```bash
python3 scripts/model.py        # data/inputs -> data/matches.json
python3 scripts/build_site.py   # data/*.json -> HTML; fails on broken links or predictions under 30 words
```

Prior audit site (unchanged, and what CI validates):

```bash
python -m unittest discover -s tests -v
python scripts/build.py
```

Both pipelines use the Python standard library only. Pages is served from `main` at the repository root in
legacy mode, with `.nojekyll` committed.

## Data integrity rules used here

1. A fixture is published only if an official source confirms both teams, the competition and the date.
2. A value that cannot be confirmed is left blank and listed on the flagged page. Nothing is inferred.
3. OLBG supplies event discovery and market vocabulary only — never odds, never results.
4. Every published row links to the official fixture source and to its data source.
5. Predictions exist only for high-confidence picks, are at least 30 words, name the selection explicitly and
   cite a source for every factual claim.

See [METHODOLOGY.md](METHODOLOGY.md) for formulas and confidence thresholds.

## Coverage gaps

Tennis, darts, snooker, Gaelic football, Top 14 / Pro D2, and eight further sports (Handball, Volleyball, Golf,
Motor Racing, Greyhounds, eSports, Aussie Rules, Rugby League) could not be verified inside the capture window.
They are listed individually on the Flagged for Review page — absence from this site is **not** evidence that
OLBG lists no events for them.

18+ · This is an analytics and research project, not betting advice.
