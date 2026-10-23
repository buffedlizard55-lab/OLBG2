# OLBG reverse-engineering refresh — 23 October 2026

Session `arena/b8a1ce4c-olbg2`, capture window 16:20–16:31 UTC. Every statement below was read
first-hand from the live site with the agent fetch tool in that window.

## 1. What one hub page gives you

`https://www.olbg.com/betting-tips/{Sport}/{id}` renders a server-side list. Each row carries:

| Field | Example (Darts) |
|---|---|
| Event | `Jonny Clayton vs Niko Springer` |
| Displayed start | `Today 14:45` |
| Most-tipped market | `Win Match 2-way` |
| Most-tipped selection | `Jonny Clayton` |
| Tip split | `26/31 Win Tips`, `84%` |
| Event id | `32335` |
| Event URL | `/betting-tips/Darts/All_Darts/All_Events/Jonny_Clayton_vs_Niko_Springer/15?event_id=32335` |

## 2. What it does not give you

- **No price.** The hub shows a percentage and a tip count, never odds. The event page was checked
  directly (`event_id=32335`): its price field renders as `WIN @` with nothing after it, and the
  handicap and total blocks carry only a line value, not a price.
- **No pagination-free list.** Both “Load More Tips” and “Show Expired Events” are client-side. The
  captured inventory is what OLBG rendered above the fold.
- **No reliable clock.** Displayed times are localised and inconsistent. The NHL row reads
  `Today 20:07` for a game the NHL feed schedules at `2026-10-24T00:00:00Z`.

Consequence for this repository: OLBG is a legitimate source for *which events exist and how the
crowd split*, and is not a source for fixtures, kick-off times or prices.

## 3. Sports present on 23 October 2026

| Sport | id | Events captured | Note |
|---|---|---|---|
| Golf | 5 | 0 | hub returned “No tips found.” |
| Volleyball | 21 | 14 | club and women's leagues |
| Rugby Union | 9 | 14 | URC R4, Premiership, Pro D2, Japan v Fiji |
| Cricket | 7 | 7 | Australian domestic, NZ v IND T20, PAK v ENG ODI |
| Snooker | 8 | 2 | Northern Ireland Open quarter-finals |
| Darts | 15 | 12 | Machineseeker European Championship |
| Baseball | 12 | 1 | World Series Game 1 |
| Gaelic Sports | 25 | 4 | club championships plus a 2027 outright |
| Greyhounds | 28 | 15 | UK graded cards |
| Tennis | 3 | 9 | ATP and WTA hard-court events |
| Motor Racing | 14 | 2 | USA Grand Prix plus championship outrights |
| Handball | 20 | 14 | French, German, Spanish, Danish, Balkan |
| Ice Hockey | 13 | 14 | one NHL game plus European leagues |
| Basketball | 4 | 14 | EuroLeague, NBA, Polish PLK |
| Rugby League | 10 | 3 | outrights only; no match listed |

125 events in total across 14 sports.

## 4. New irregularity worth recording

Draw markets are labelled inconsistently across sports. Handball publishes a three-way money line
including `Tie` (three of fourteen rows are tie picks), while Darts labels its two-way market
`Win Match 2-way` and Rugby Union uses `To Win`. Any downstream parser must key on the label rather
than assume a two-way market. Recorded as part of flag F-06.
