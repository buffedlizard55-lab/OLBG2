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
| [Picks](now/picks.html) | One row per pick: **selection**, market, our chance, our price, the confidence grade and the official source |
| [Written predictions](now/predictions.html) | One unique preview per high and medium pick, each ≥30 words, with the official facts and links beneath it |
| [All matches](now/matches.html) | Every fixture, priced or blank, with the reason for any blank |
| [Our lines](now/lines.html) | The full market book: match winner, handicap and total for each fixture we can price |
| [Odds band](now/band.html) | The −250 to +10000 test, applied to every price we made |
| [By sport](now/sports/index.html) | Fifteen category pages, same sections in the same order |
| [OLBG list](now/olbg.html) | The 96 rows captured off OLBG's own event list, with event ids, URLs and the hubs re-read live |
| [Sources](now/sources.html) | Every page a value was read from |
| [Method](now/methodology.html) | The four pricing families, the confidence rules and what is never done |
| [Flagged for review](now/flagged.html) | 32 items: what is blank, what was corrected, and where the five-a-day target was not met |

## The 24 October 2026 snapshot

| Item | Value |
|---|---|
| Upcoming fixtures on the desk | **50** across all 15 sports — 39 priced, 11 blank with a stated reason |
| Prices originated here | **866** (match winner, handicap ladder and total ladder) |
| Graded picks | **39** — 10 high, 26 medium, 3 low, every one inside −250…+10000 |
| Written predictions | **36** across 11 sports, shortest 65 words, no two openings alike |
| OLBG listing rows captured | **96** across 14 of the 15 sports |
| Official sources linked | 50 |
| Review items | 32 — 25 open, 2 corrected, 5 notes |

Five written predictions per sport is the target, not a quota. It is met in Basketball (8) and Ice Hockey (9) and
missed elsewhere, because a preview is only written when the official record carries the form, the recent results and
the statistics the preview talks about. Every shortfall is named on the flagged page rather than padded.

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

```sh
python scripts/now_seed.py         # OLBG inventory + official fixture records with provenance
python scripts/now_model.py        # originate every market, grade it, apply the band test
python scripts/now_predictions.py  # write the previews
python scripts/now_build.py        # render the site (27 pages)
python scripts/now_verify.py       # 7,809 line-by-line assertions
python scripts/build_site.py       # regenerate the root front door and the archive index
python -m unittest discover -s tests
```

The pipeline is deterministic: `now_verify.py` rebuilds every artefact and fails if a single byte changes.

## Honesty rules

- A value that is not on an official page stays **blank**, and the blank is published with its reason.
- A source link records where a value was read; it does not prove the page still shows it, and each fact carries its
  own capture time.
- The fixture facts come from an official capture made at 17:35Z on 24 October and are marked as inherited on every
  row. Three OLBG hubs were re-read live during this session and those results are recorded on the OLBG page.
- Displayed times are never converted between timezones.
- The words "model" and "verified" do not appear in reader-facing copy; both are reserved for the internal method and
  are checked by the test suite.

## Earlier desks

Forty-nine earlier layers are preserved, unmodified and with their own counts, at their own URLs
(`/today/`, `/master/`, `/cadence/`, `/clarity/`, `/ledger/`, `/brief/`, `/olbg/`, `/atlas/`, and so on).
They are indexed, generated from the repository itself, on [archive.html](archive.html). Do not add their numbers to
the current desk's.
