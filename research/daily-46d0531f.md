# Daily slate, 23 October 2026 — capture and verification note

Session `arena/46d0531f-olbg2`. Captures made **2026-10-22, 20:56–21:32 UTC** with the agent `fetch_page`
tool. Every fetched page's rendered text is stored verbatim in `data/daily/capture/`.

## 1. What this session found that the earlier sessions did not

Three earlier sessions recorded that official sports hosts are unreachable and therefore that no source could be
re-certified. That is true of the sandbox **shell** (egress is allowlisted to GitHub hosts) but not of the agent
fetch tool: `olbg.com`, `atptour.com`, `icc-cricket.com`, `wtatennis.com`, `pdc.tv` and `gaa.ie` all responded to
`fetch_page` from this session. That is the single change in method that made fresh, first-hand verification
possible.

The pattern that decides whether a page can be used is server-side rendering:

| Host | Rendered server-side? | What could be read |
|---|---|---|
| `olbg.com` | yes | event list, market labels, tip counts — **no odds anywhere** |
| `atptour.com` scores/draws/schedule | yes | order of play, seeds, byes, qualifiers, completed scorelines |
| `atptour.com` rankings | partly | top-12 table rendered; deeper ranks are behind the date widget |
| `icc-cricket.com` fixtures list | yes | nine upcoming fixtures, format, start time, match links |
| `icc-cricket.com` rankings and scorecards | **no** | empty table body / no panel content |
| `wtatennis.com` draws | **no** | site chrome and notifications only |
| `pdc.tv` | **no** | cookie-consent wall |
| `gaa.ie` fixtures | yes | but only one inter-county fixture in October; no club football |

Consequence: tennis has a full official input set and is priced; cricket has official fixtures and **no** input,
so it is published with blank prices. Darts, WTA tennis, eSports and Gaelic football cannot be published at all
without inventing something, so they are named on the flagged page instead.

## 2. Fixtures published (17)

Eight ATP quarter-finals, verified against the ATP **Day 7 order of play** (`almaty/9410`, `brussels/7485`) and
the corresponding singles draws. Seeds read from the draws: Medvedev (1), Bublik (3), Khachanov (5), Tsitsipas (7)
at Almaty; Fils (1), Lehecka (2), F. Cerundolo (3), Michelsen (5), Bergs (6) at Brussels.

Nine ICC fixtures, verified against `icc-cricket.com/fixtures-results`: AFG v ZIM (ODI, Tri-Series in UAE),
NZ v IND (T20), IND v ZIM (ODI), NGR v MOZ, ZAM v LES, GAM v UGA, DEN v KUW and QAT v KEN (CWC Challenge
League), AFG-U19 v BAN-U19 (Youth ODI). The completed AUS v BAN T20 is excluded as not upcoming.

Dates: the ATP prints a date, so the eight tennis rows carry 2026-10-23. The ICC prints a start time and
"(Your time)" but **no date**, so seven cricket rows carry a blank date and the eighth (NZ v IND) carries the date
only because OLBG printed "24 Oct" — attributed to OLBG on the row.

## 3. Line origination

Markets per tennis fixture: match winner, games handicap (14 alternate lines per side at half-game steps) and
total games (12 alternate lines). 288 prices across 24 fixture-markets. The model is documented in full on
`daily/methodology.html` and reproducible with `python3 scripts/daily_model.py`.

Rating = 1500 + 25 × (9 − seed) for a seeded player, 1480 unseeded, 1455 for a qualifier, plus 6 per verified set
won and minus 6 per verified set lost. Win probability is a logistic function of the rating gap (scale 200); the
games margin is Normal(8 × (p − 0.5), 4.5); the total is Normal(22, 4.2). Lines are snapped off whole numbers so
no price can push.

**Zero prices land inside the brief's −250…+10000 window.** The window is p ∈ [0.7000, 0.714286] — 1.43
probability points — and half-point lines step by roughly four points, so the window is stepped over. The nearest
originated price is Under 24.5 games at p = 0.7242 (fair −263), 0.99 points above it. Rather than post a
quarter-game line invented for the purpose, the five published picks are the highest-confidence match winners and
each is labelled *outside −250 window*. Recorded as DL-05.

## 4. The five written picks

| # | Match | Selection | p | Fair | Words |
|---|---|---|---|---|---|
| 1 | Medvedev v Atmane (Almaty QF) | Medvedev | 0.9216 | −1176 | 57 |
| 2 | Griekspoor v Lehecka (Brussels QF) | Lehecka | 0.9100 | −1011 | 54 |
| 3 | Chidekh v F. Cerundolo (Brussels QF) | Cerundolo | 0.8916 | −823 | 61 |
| 4 | Struff v Bergs (Brussels QF) | Bergs | 0.7359 | −279 | 60 |
| 5 | Fils v Michelsen (Brussels QF) | Fils | 0.7336 | −275 | 62 |

Every paragraph names the player, the exact selection and price, the tournament form and at least one completed
scoreline, and every fact is listed beneath the paragraph with its official URL. Where a player entered on a bye
(F. Cerundolo, Fils) the paragraph says the price rests on seeding rather than inventing form.

## 5. Five picks a day, per sport

Met for tennis (five). **Not met for cricket** (zero), because cricket has no official strength input in this
session; a pick there would be a guess dressed as a model output. The other fifteen eligible sports are accounted
for one by one on the landing page: seven are covered by the `/current/` desk, four were not surveyed this session,
two have no fixture on OLBG, and two (darts, Gaelic football) have fixtures on OLBG whose official confirmation
failed. DW-13 records the shortfall.

## 6. Verification performed

* Every fixture row links the official page it was read from; a test asserts the href is present in the rendered
  table, not only in the JSON.
* Every model input is a count from the ATP draw (seeds, byes, sets) or a declared constant.
* 288 prices are re-derived from their own printed probability in the test suite.
* Confidence labels are recomputed from the stated thresholds; the in-window flag is recomputed from the stated
  window; no line may sit on a whole number.
* Every internal link and every `#anchor` in all 26 pages is resolved on disk by a test.
* The build is re-run inside a test and compared byte for byte.
* `python3 scripts/integration_audit.py` reports 0 local link errors across every layer.

## 7. Irregularities carried forward

Fifteen items, DL-01…DL-15, are published on `daily/flagged.html` with their sources. The ones a reviewer should
look at first:

1. **DL-05** — the brief's confidence bar and price window are mutually exclusive at half-point lines. If the
   intent is "high-confidence picks, with the price window as a soft preference", the five published picks are
   correct. If the intent is "no pick unless it is inside −250", this layer has no picks at all and the model needs
   a finer line grid.
2. **DL-03** — eight WTA fixtures were listed by OLBG but could not be verified because the WTA draws page does not
   render server-side. If WTA coverage matters, that is the one fetch to retry in a browser session.
3. **DL-04 / DL-13** — cricket fixtures with no prices. The ICC rankings table is the missing input; one successful
   read of it would unlock nine cricket rows.
4. **DL-10** — darts is entirely blocked by the PDC consent wall, not by a lack of fixtures.
