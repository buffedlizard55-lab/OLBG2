# OLBG2 — one desk: our own lines, confidence-graded picks, written predictions

**Live:** <https://buffedlizard55-lab.github.io/OLBG2/> · the current desk is <https://buffedlizard55-lab.github.io/OLBG2/compass/>
(24 October 2026, 22:45Z capture: 83 graded picks — 11 high / 32 medium / 40 low — across 13 sports, 56 written
previews, 321 originated prices of which 303 sit inside −250…+10000, 26 pages)

This repository publishes a daily research desk for the fifteen OLBG sports in scope: **Golf, Volleyball,
Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball,
Ice Hockey, Basketball, Rugby League**.

The root of the site is now a single front door. It opens with the executive summary, then the picks, then the
fixtures, then the fifteen sport categories. Nothing else competes with it: every earlier desk (including
/now/ and /latest/, the 18:10Z and 22:50Z captures) still exists, but it is reached through one generated index
on [archive.html](archive.html) and its counts are never added to the current desk's.

## Read this first

| Page | What is on it |
|---|---|
| [Executive summary](compass/index.html) | The strongest calls in large type, the counts, and a plain map of where everything lives |
| [Picks](compass/picks.html) | One row per pick: **selection**, market, our chance, a **0-10 score**, our price, the confidence grade and the official source |
| [Written predictions](compass/predictions.html) | One unique preview per high and medium pick, each ≥30 words, with the official facts and links beneath it |
| [All matches](compass/matches.html) | Every fixture, priced or blank, with the reason for any blank |
| [Our lines](compass/lines.html) | The full market book: match winner, handicap and total for each fixture we can price |
| [Odds band](compass/band.html) | The −250 to +10000 test, applied to every price we made |
| [By sport](compass/sports/index.html) | Fifteen category pages, same sections in the same order |
| [OLBG list](compass/olbg.html) | The 121 rows captured off OLBG's own event list at 22:25–22:45Z, with event ids and hub URLs |
| [Sources](compass/sources.html) | Every page a value was read from |
| [Method](compass/methodology.html) | The four pricing families, the confidence rules, the 0-10 score and what is never done |
| [Flagged for review](compass/flagged.html) | 20 items: OLBG data errors, time corrections, unverified events and coverage notes |
| [Independent re-check](recheck/index.html) | A separate audit desk that re-derives every price, grade, score and prose rule of the `/now/` desk from committed evidence: 1,246 checks, 0 failures, with the live-reread limits stated on every page |

## The 24 October 2026 snapshot (22:45Z capture)

| Item | Value |
|---|---|
| Upcoming fixtures on the desk | **122** across all 15 sports — 121 OLBG-listed plus the official World Series Game 3 |
| Prices originated here | **321** (match winner, handicap and total), 303 inside the band |
| Graded picks | **83** — 11 high, 32 medium, 40 low |
| Written predictions | **56** across 13 sports, shortest 81 words (high picks), no two openings alike |
| OLBG listing rows captured | **121** across 12 of the 15 sports (golf, snooker and motor racing showed no tips at capture) |
| Official sources linked | 36 |
| Review items | 20 — data errors, time corrections, unverified events and coverage notes |

Five written predictions per sport is the target, not a quota. On this desk it is met in 13 of the 15 sports;
Greyhounds, Rugby League and Darts publish every pickable fixture their OLBG lists carry at capture (1, 3 and 4),
and the remaining gaps (Golf, Snooker and Motor Racing showed no tips at capture) are named on the flagged page
rather than padded.

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
python scripts/compass_seed.py         # OLBG hub capture + official fixture records with provenance
python scripts/compass_model.py        # originate every market, grade it, apply the band test
python scripts/compass_predictions.py  # write the previews
python scripts/compass_build.py        # render the site (27 pages)
python scripts/compass_verify.py       # line-by-line assertions
python scripts/build_site.py           # regenerate the root front door and the archive index
python -m unittest discover -s tests
```

The pipeline is deterministic: `compass_verify.py` re-renders every page and fails if a single byte changes.

## Honesty rules

- A value that is not on an official page stays **blank**, and the blank is published with its reason.
- A source link records where a value was read; it does not prove the page still shows it, and each fact carries its
  own capture time.
- The fixture facts come from official captures made at 22:25–23:00Z on 24 October; the subset inherited from the
  17:35Z capture is marked as inherited on every row. All 15 OLBG hubs were re-read live during this session.
- Displayed times are never converted between timezones.
- The words "model" and "verified" do not appear in reader-facing copy; both are reserved for the internal method and
  are checked by the test suite.

## Earlier desks

Fifty-four earlier layers are preserved, unmodified and with their own counts, at their own URLs
(`/today/`, `/master/`, `/cadence/`, `/clarity/`, `/ledger/`, `/brief/`, `/olbg/`, `/atlas/`, and so on).
They are indexed, generated from the repository itself, on [archive.html](archive.html). Do not add their numbers to
the current desk's.
