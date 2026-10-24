# OLBG2 — one desk: our own lines, confidence-graded picks, written predictions

**Live:** <https://buffedlizard55-lab.github.io/OLBG2/> · the current desk is <https://buffedlizard55-lab.github.io/OLBG2/now/>

This repository publishes a daily research desk for the fifteen OLBG sports in scope: **Golf, Volleyball,
Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball,
Ice Hockey, Basketball, Rugby League**.

The root of the site is now a single front door. It opens with the executive summary, then the picks, then the
fixtures, then the fifteen sport categories. Nothing else competes with it: every earlier desk still exists, but it
is reached through one generated index on [archive.html](archive.html) and its counts are never added to the current
desk's.

## Read this first

| Page | What is on it |
|---|---|
| [Executive summary](now/index.html) | The strongest calls in large type, the counts, and a plain map of where everything lives |
| [Picks](now/picks.html) | One row per pick: **selection**, market, our chance, a **0-10 score**, our price, the confidence grade and the official source |
| [Written predictions](now/predictions.html) | One unique preview per published pick, each ≥30 words, with the official facts and links beneath it |
| [Top 5 by sport](now/top5.html) | Up to five in-band originated lines for each of the fifteen sports, with shortfalls disclosed |
| [All matches](now/matches.html) | Every fixture, priced or blank, with the reason for any blank |
| [Our lines](now/lines.html) | The full market book: match winner, handicap and total for each fixture we can price |
| [Odds band](now/band.html) | The −250 to +10000 test, applied to every price we made |
| [By sport](now/sports/index.html) | Fifteen category pages, same sections in the same order |
| [OLBG list](now/olbg.html) | The 96 rows captured off OLBG's own event list, with event ids, URLs and 18 dated hub reads |
| [Source checks](now/checks.html) | The 22:32Z re-read of all fifteen OLBG hubs and nineteen official pages, with every exact link and change |
| [Sources](now/sources.html) | Every page a value was read from, with its capture time and role |
| [Method](now/methodology.html) | The four pricing families, the confidence rules, the 0-10 score and what is never done |
| [Flagged for review](now/flagged.html) | 39 items: what is blank, what was corrected, and where the five-a-day target was not met |

## The 24 October 2026 snapshot — refreshed 22:32Z

| Item | Value |
|---|---|
| Upcoming fixtures on the desk | **50** across all 15 sports — 39 priced, 11 blank with a stated reason |
| Prices originated here | **866** (match winner, handicap ladder and total ladder) |
| Graded picks | **39** — 10 high, 26 medium, 3 low, every one inside −250…+10000 |
| Picks still to start at 22:32Z | **33**, including 8 high-confidence calls; 6 started picks are kept for the record but excluded from the executive summary |
| Written predictions | **39** across 11 sports, shortest 65 words, no two openings alike — one for every pick |
| Top-five board | **55** in-band lines across 11 sports; 4 sports have no usable line and their blank reasons are published |
| OLBG listing rows captured | **96** across 14 of the 15 sports |
| First-hand rechecks | **15** OLBG hubs and **19** official pages at 22:32Z, plus three earlier hub reads |
| Official sources linked | 51 |
| Review items | 39 — 32 open, 2 corrected, 5 notes |

Five written predictions per sport is the target, not a quota. It is met in Basketball (8) and Ice Hockey (9) and
missed elsewhere, because a preview is only written when the official record carries the form, the recent results and
the statistics the preview talks about. The top-five page shows the strongest lines that can be originated from the
captured official inputs; shortfalls are named on the flagged page rather than padded.

## How the numbers are made

No bookmaker price is read anywhere. Each probability comes from an official rate on the fixture record, through one
of four documented families — Poisson scoring (ice hockey, baseball), a normal margin (rugby union, rugby league,
Gaelic games, basketball, tennis), a negative-binomial race to legs (darts), or a five-rung evidence ladder
(volleyball, handball, cricket and the two rugby league / Gaelic cards). A fair −250 is 71.43%, so a side we rate at
85% cannot be backed inside the requested band at all; the desk therefore publishes a handicap ladder and puts the
pick on the line where its number lands nearest 68%.

Confidence: **high** needs a numeric family, 62% or better and a price inside the band (match totals are capped at
medium because they carry more variance). **Medium** needs 55%. Everything else is **low** and is published only for
completeness.

The **0-10 score** puts that on one scale so sports can be compared without reading a price:
`score = 10 × our chance × basis shade`, with the shade at 1.0 for a goals or points rate and 0.8 for the evidence
ladder. 5.0 is a coin flip and no pick can score above 7.5 while the band stops at 71.4%. Every pick on the site
carries its score, and `scripts/now_verify.py` re-derives it from the probability.

```sh
python scripts/final_recheck.py   # validate the committed 22:32Z source dossier
python scripts/now_seed.py        # OLBG inventory + official fixture records with provenance
python scripts/now_model.py       # originate every market, grade it, apply the band test
python scripts/now_predictions.py # write the previews
python scripts/now_build.py       # render the /now/ site (28 pages)
python scripts/build_site.py      # regenerate the root front door and the archive index
python scripts/now_verify.py      # 8,564 line-by-line assertions
python -m unittest discover -s tests
```

The pipeline is deterministic: `now_verify.py` rebuilds every `/now/` artefact and fails if a single byte changes.
The root front door is regenerated before that strict check so its executive cards also exclude started fixtures.

## Honesty rules

- A value that is not on an official page stays **blank**, and the blank is published with its reason.
- A source link records where a value was read; it does not prove the page still shows it, and each fact carries its
  own capture time.
- The fixture facts come from an official capture made at 17:35Z on 24 October and are marked as inherited on every
  row. All fifteen OLBG hubs and nineteen official pages were re-read first-hand at 22:32Z. Changed values are
  flagged rather than silently blended into the dated price inputs; see [Source checks](now/checks.html) and
  [research/final-desk-1ecc0d92.md](research/final-desk-1ecc0d92.md).
- Displayed times are never converted between timezones.
- The words "model" and "verified" do not appear in reader-facing copy; both are reserved for the internal method and
  are checked by the test suite.

## Earlier desks

Forty-nine earlier layers are preserved, unmodified and with their own counts, at their own URLs
(`/today/`, `/master/`, `/cadence/`, `/clarity/`, `/ledger/`, `/brief/`, `/olbg/`, `/atlas/`, and so on).
They are indexed, generated from the repository itself, on [archive.html](archive.html). Do not add their numbers to
the current desk's.
