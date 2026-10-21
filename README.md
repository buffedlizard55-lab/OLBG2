# OLBG2 — verified fixtures, originated lines, confidence-graded picks

A reverse-engineered view of [OLBG.com](https://www.olbg.com)'s sports coverage. The fixture list is rebuilt from
OLBG's sport hubs, then **every fixture is re-verified against the official league or governing body** before
anything is published. Betting lines are originated here from verified performance data — no bookmaker price is
used anywhere — and each selection is graded `high`, `medium` or `low` confidence.

**Live site:** https://buffedlizard55-lab.github.io/OLBG2/

The repository holds two published layers, both live:

| Layer | Entry point | What it is |
|---|---|---|
| **Dashboard** | `/index.html` | 33 verified fixtures · 30 originated lines · 4 high-confidence predictions · 18 flagged items. Covers NHL, NBA, URC and ICC cricket. |
| **NHL evidence desk** | `/site/index.html` | 14 NHL fixtures (the full 21–22 Oct slate) · 42 prices across three markets · 14 graded selections, 6 high-confidence · a 16-category coverage board · 8 flags. Ships its own Poisson model, 23 tests and a link crawl. |

The two layers were built by different sessions and are deliberately kept separate rather than blended: each has its
own generator, its own tests and its own audit trail. The dashboard links to the desk from its top navigation as
**NHL evidence desk**. The desk's NHL set is a stricter superset of the dashboard's 12 NHL rows — same fixtures, plus
the two the dashboard was missing, each carrying the official game-centre payload it was read from.

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

## What is in the NHL evidence desk (capture 2026-10-21 05:52 UTC)

All 14 NHL games on the official 21 and 22 October schedule days, read from
`api-web.nhle.com/v1/gamecenter/{id}/right-rail` and cross-checked against each game's NHL game page.

- **Markets:** money line (two-way, OT/SO included), puck line 1.5, match total at 5.5 and 6.5 — 42 prices.
- **Model:** `olbg-desk-poisson-v1`. Expected goals blend each attack with the opposing defence, then a 60-minute
  Poisson matrix produces every market. Parameters are declared in `data/events.json` and the build recomputes
  every price, so nothing can drift from its inputs.
- **Picks:** 6 high, 3 medium, 5 low. The six high-confidence selections each carry a 54–60 word narrative built
  only from fields in the official payload.
- **Coverage board:** all 16 eligible OLBG categories, each with a status and the exact reason it does or does not
  have a row. Eleven categories have no verified fixture; each is listed rather than omitted.

## Scope

Included: Tennis, Basketball, Golf, Cricket, Snooker, Rugby Union, Rugby League, Baseball, Ice Hockey,
Motor Racing, Darts, Handball, Volleyball, Aussie Rules, eSports, Gaelic Football, Greyhounds.

Excluded by the brief: football (soccer), horse racing, American football, boxing, cycling, hurling and
"specials". UFC/MMA are filed under Boxing on OLBG, so that exclusion covers them. Enforced in
`scripts/config.py` and, for the evidence desk, in `data/events.json` + `scripts/build.py`.

## Repository layout

```
index.html, picks.html, flagged.html, methodology.html, sources.html   dashboard (generated)
sports/<sport>.html                                                    dashboard per-sport pages
assets/style.css                                                       dashboard styling
data/inputs/*.json                                                     verified inputs + fixtures
data/matches.json                                                      generated dataset (lines, picks)
data/predictions.json                                                  high-confidence write-ups + sources
data/flagged.json                                                      dashboard review queue (18 items)
data/sources.json                                                      dashboard source register (24 sources)
scripts/config.py, model.py, build_site.py                             dashboard pipeline

site/**                                                                NHL evidence desk (generated)
data/events.json                                                       desk inputs, picks, coverage, flags
scripts/poisson.py, build.py, report.py                                desk model + generator
tests/test_build.py                                                    23 desk checks incl. link crawl
research/olbg-reverse-engineering.md, research/collection-log.md       OLBG schema + fetch provenance
COORDINATION.md                                                        shared task board and merge log
```

## Rebuild

Dashboard:

```bash
python3 scripts/model.py        # data/inputs -> data/matches.json
python3 scripts/build_site.py   # data/*.json -> HTML; fails on broken links or predictions under 30 words
```

NHL evidence desk (also what CI validates):

```bash
python -m unittest discover -s tests -v   # 23 checks
python scripts/build.py                   # data/events.json -> site/
python scripts/report.py                  # model output table for review
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
6. Model parameters that are desk assumptions rather than league measurements are labelled as such, in the data
   file and on the methodology page.

See [METHODOLOGY.md](METHODOLOGY.md) for the dashboard formulas and `/site/methodology.html` for the desk model.

## Coverage gaps

Tennis, darts, snooker, Gaelic football, Top 14 / Pro D2, and eight further sports (Handball, Volleyball, Golf,
Motor Racing, Greyhounds, eSports, Aussie Rules, Rugby League) could not be verified inside the capture window.
They are listed individually on the Flagged for Review page — absence from this site is **not** evidence that
OLBG lists no events for them.

18+ · This is an analytics and research project, not betting advice.
