# OLBG2 — one desk: our own lines, confidence-graded picks, written predictions

**Live:** <https://buffedlizard55-lab.github.io/OLBG2/> · the current desk is <https://buffedlizard55-lab.github.io/OLBG2/slate26/>
(26 October 2026, 05:05–05:45Z capture: 75 priced matches across ten sports, 9 high / 22 medium /
44 low, 11 written previews, 75 originated prices of which 64 sit inside
−250…+10000, 37 flagged items, 26 pages)

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
| [Executive summary](slate26/index.html) | The counts, the 9 high-confidence picks and a plain map of where everything lives |
| [Picks](slate26/picks.html) | Sport by sport, numbered 1 to 10: the **selection**, market, our price, our chance, the grade and the OLBG source |
| [Written predictions](slate26/predictions.html) | 11 previews, each ≥30 words, 2 with official statistics and links beneath |
| [All matches](slate26/matches.html) | Every OLBG fixture with its displayed time, official UTC start where read, and data grade |
| [Our lines](slate26/lines.html) | One originated price per fixture, the opposite side where two-way, and how each was built |
| [Odds band](slate26/band.html) | The −250 to +10000 test on every price, both sides of the window |
| [By sport](slate26/sports/index.html) | Fifteen category pages, one per covered sport |
| [Outrights](slate26/outrights.html) | 11 futures markets, kept out of the match count |
| [Sources](slate26/sources.html) | Every page a value was read from, 13 entries |
| [Method](slate26/methodology.html) | The two pricing routes, the grading rules, the time convention and what was not available |
| [Flagged for review](slate26/flagged.html) | 37 items: no-fixture sports, unverified start times and rows with no official statistic |
| [Independent re-check](recheck/index.html) | A separate audit desk that re-derives every price and grade of the `/now/` desk from committed evidence: 1,246 checks, 0 failures |

## Earlier desks

Every earlier capture stays published and unchanged; nothing is deleted when a newer desk takes the front door. The
24 October desk is at [compass/index.html](compass/index.html) — its [picks](compass/picks.html),
[previews](compass/predictions.html) and [flagged page](compass/flagged.html) still render — and the earlier layers
(`/now/`, `/latest/`, `/playbook/`, `/recheck/` …) are listed on [archive.html](archive.html).

## The 26 October 2026 snapshot (05:05–05:45Z capture)

| Item | Value |
|---|---|
| Upcoming fixtures on the desk | **75** across ten sports — every match OLBG's fifteen hubs listed |
| Prices originated here | **75**, 64 inside the band |
| Graded picks | **75** — 9 high, 22 medium, 44 low |
| Written predictions | **11** across five sports, shortest 62 words, no two openings alike |
| OLBG listing rows captured | **75** across ten of the fifteen sports (Golf and Snooker showed no tips; Darts, Rugby Union and Rugby League showed 2027 outrights only) |
| Official sources linked | 13 |
| Review items | 37 — blank start times, missing official statistics and data notes |

Five written predictions per sport is the target, not a quota, and this desk does not invent fixtures to reach it.
On 26 October OLBG priced matches in ten of the fifteen sports: Golf and Snooker returned "No tips found." and Darts,
Rugby Union and Rugby League showed 2027 outrights only, so five sports have no pick at all and say so on their own
page. Where a match was listed but no official fixture-level feed was readable, the row keeps its price and grade and
carries no prose; the market-only previews are labelled as such on every card.

## How the numbers are made

No bookmaker price is read anywhere. OLBG's hub pages publish no odds — only the share of tips — so each of the 75
prices is originated here by one of two documented routes:

- **OLBG tip share** (74 rows). The share is shrunk 15% toward a coin flip and capped at 78%, because a popularity poll
  is not a probability and a unanimous board is not a 92% winner. Rows with fewer than three tips are clamped to 65%.
- **Official season records** (1 row, Detroit at Edmonton). `logit = 3.6 × (points%home − points%away) + 0.22`, with both
  records read from the NHL feed that morning.

Confidence: **high** needs a 62% chance or better, at least four tips behind the row, and a price inside −250…+10000.
**Medium** needs 55% with three tips, or a stronger chance that falls outside the window. Everything else is **low**, and
every row where OLBG's most-tipped selection is the draw is low by rule.

Written previews come in two labelled tiers: **full** (statistics read from an official governing-body feed, listed with
links under the preview) and **market** (no official fixture-level feed was readable, so the preview is confined to the
fixture, the tip sample and our price, and makes no claim about form or availability).

```sh
python scripts/slate26_pipeline.py     # captured OLBG listings + official facts -> fixtures, lines, picks, flags
python scripts/slate26_predictions.py  # the written previews, with the word-count and wording checks
python scripts/slate26_build.py        # render slate26/ (26 pages) and the root front door
python scripts/slate26_verify.py       # 1,189 structural checks
python scripts/build_site.py           # regenerate the root page and the archive index
python -m unittest discover -s tests
```

The pipeline is deterministic: `slate26_verify.py` re-checks every page, link, grade and preview and fails on a broken
link, a high pick outside the window, a preview under 30 words, a repeated opening or a banned word.

## Honesty rules

- A value that is not on an official page stays **blank**, and the blank is published with its reason.
- A source link records where a value was read; it does not prove the page still shows it, and each fact carries its
  own capture time.
- The OLBG rows come from a single read of all fifteen hubs between 05:05 and 05:45Z on 26 October 2026; the official
  facts carry their own URL and, where relevant, their own snapshot time.
- Displayed times are never converted between timezones.
- The words "model" and "verified" do not appear in reader-facing copy; both are reserved for the internal method and
  are checked by the test suite.

## Earlier desks

Every earlier layer is preserved, unmodified and with its own counts, at its own URL
(`/today/`, `/master/`, `/cadence/`, `/clarity/`, `/ledger/`, `/brief/`, `/olbg/`, `/atlas/`, and so on).
They are indexed, generated from the repository itself, on [archive.html](archive.html). Do not add their numbers to
the current desk's.
