# OLBG2 — verified fixtures, originated lines, confidence-graded picks

A reverse-engineered view of [OLBG.com](https://www.olbg.com)'s sports coverage: the fixture list is rebuilt
from OLBG's sport hubs, then **every fixture is re-verified against the official league or governing body**
before anything is published. Betting lines are originated here from verified performance data — no bookmaker
price is used anywhere — and each selection is graded `high`, `medium` or `low` confidence.

**Live site:** https://buffedlizard55-lab.github.io/OLBG2/

## What is in this release (capture window 2026-10-21 05:10–05:45 UTC)

| Sport | Fixtures | Lines originated | High confidence |
|---|---|---|---|
| Ice Hockey (NHL) | 12 | 11 | 4 |
| Basketball (NBA) | 11 | 11 | 0 |
| Rugby Union (URC) | 8 | 8 | 0 |
| Cricket (ICC) | 2 | 0 | 0 |
| **Total** | **33** | **30** | **4** |

Two of the 33 rows are deliberately blank: the Sharks' goal totals were not captured, and the ICC ranking
table did not render, so a cricket line could not be originated without inventing an input. Both are on the
[Flagged for review](https://buffedlizard55-lab.github.io/OLBG2/flagged.html) page with the source link.

## Scope

Included: Tennis, Basketball, Golf, Cricket, Snooker, Rugby Union, Rugby League, Baseball, Ice Hockey,
Motor Racing, Darts, Handball, Volleyball, Aussie Rules, eSports, Gaelic Football, Greyhounds.

Excluded by the brief: football (soccer), horse racing, American football, boxing, cycling, hurling and
"specials". UFC/MMA are filed under Boxing on OLBG, so that exclusion covers them. See `scripts/config.py`.

## Repository layout

```
index.html, picks.html, flagged.html, methodology.html, sources.html   generated site
sports/<sport>.html                                                    generated per-sport pages
assets/style.css                                                       site styling
data/inputs/*.json                                                     verified inputs + fixtures
data/matches.json                                                      generated dataset (lines, picks)
data/predictions.json                                                  high-confidence write-ups + sources
data/flagged.json                                                      review queue
data/sources.json                                                      source register
scripts/config.py                                                      scope / exclusions
scripts/model.py                                                       line origination
scripts/build_site.py                                                  site build (+ link validation)
research/olbg-reverse-engineering.md                                   OLBG URL schema, sport IDs, irregularities
research/collection-log.md                                             every fetch and what it produced
COORDINATION.md                                                        shared task board
```

## Rebuild

```bash
python3 scripts/model.py        # data/inputs -> data/matches.json
python3 scripts/build_site.py   # data/*.json -> HTML; fails on broken links or short predictions
```

Both scripts use the Python standard library only. The site is plain HTML/CSS with one small inline filter
script, so it works on GitHub Pages without a build step (`.nojekyll` is committed).

## Data integrity rules used here

1. A fixture is published only if an official source confirms both teams, the competition and the date.
2. A value that cannot be confirmed is left blank and listed on the flagged page. Nothing is inferred.
3. OLBG supplies event discovery and market vocabulary only — never odds, never results.
4. Every published row links to the official fixture source and to its data source.
5. Predictions exist only for high-confidence picks, are at least 30 words, name the selection explicitly and
   cite a source for every factual claim.

See [METHODOLOGY.md](METHODOLOGY.md) for the formulas and confidence thresholds.

## Coverage gaps

Tennis, darts, snooker, Gaelic football, Top 14 / Pro D2, and eight further sports (Handball, Volleyball, Golf,
Motor Racing, Greyhounds, eSports, Aussie Rules, Rugby League) could not be verified inside the capture window.
They are listed individually on the site's Flagged for review page — absence from this site is **not** evidence
that OLBG lists no events for them.

18+ · This is an analytics and research project, not betting advice.
