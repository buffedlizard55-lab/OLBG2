# OLBG Playbook — reverse-engineering record (session 3ef9031e)

Captured 2026-10-24 between 22:35 and 23:05 UTC from this sandbox. Everything below was read
first-hand; nothing is carried over from another session's notes without being re-checked.

## 1. Sport routing

OLBG serves one hub per sport at `https://www.olbg.com/betting-tips/<Sport_Name>/<id>`.

| Sport | Path | id | Hub listing at capture |
|---|---|---|---|
| Golf | `Golf` | 5 | "No tips found." |
| Volleyball | `Volleyball` | 21 | 15 fixtures, BRA/ITA/GER/POL/TUR/FIN |
| Rugby Union | `Rugby_Union` | 9 | 3 fixtures + Six Nations 2027 outrights |
| Cricket | `Cricket` | 7 | 10 fixtures + 6 outrights |
| Snooker | `Snooker` | 8 | "No tips found." |
| Darts | `Darts` | 15 | 2 fixtures + PDC World Championship 2027 outright |
| Baseball | `Baseball` | 12 | 1 fixture (TB @ MIL) |
| Gaelic Sports | `Gaelic_Football` | 25 | 4 fixtures + All-Ireland 2027 outrights |
| (Hurling) | `Hurling` | 26 | 1 fixture — a different sport id behind the same hub family |
| Greyhounds | `Greyhounds` | 28 | 1 race (11:04 Doncaster) |
| Tennis | `Tennis` | 3 | 14 matches, tournament names absent from the card |
| Motor Racing | `Motor_Racing` | 14 | "No tips found." |
| Handball | `Handball` | 20 | 15 fixtures, all "Tie" on the modal selection |
| Ice Hockey | `Ice_Hockey` | 13 | 18 NHL fixtures (the flat hub hides 1 the NHL sub-hub shows) |
| Basketball | `Basketball` | 4 | 10 fixtures (7 NBA + 3 KBL) |
| Rugby League | `Rugby_League` | 10 | 0 fixtures; 3 outrights (SoO 2027, Super League GF, NRL 2027) |

`Gaelic Football` and `Hurling` share a family: hurling rows render on the football hub but carry
sport id 26 in their own event URLs. The seed keeps them apart by competition name (`Kilkenny SHC`).

## 2. What the hub actually is

**The hub is a tip feed, not a fixture list.** An event appears only once at least one OLBG user has
tipped it. That single fact explains the four empty sports and it is why this desk publishes four
sport pages with "Nothing to price" instead of importing fixtures from another source.

Consequences:

* An empty hub is not an empty slate. It means nobody has tipped that sport yet.
* Row order is popularity, not kick-off. Tomorrow's fixtures interleave with today's.
* The card prints `N/M Win Tips` — N is the number of tips on the *highlighted selection*, M the
  number on the whole market. It is a share of tips, **not** a strike rate.

## 3. Clock, timezone, drift

Every rendered time is a bare string — `Today 19:30`, `Tomorrow 14:00` — with no timezone suffix.
Against the official NHL feed the rendered clock runs **+7 minutes** ahead of the true UTC
conversion to US Eastern (checked on all twenty NHL rows). Two separate quirks, recorded as
`CLOCK-QUIRK`:

1. the clock is localised to the reader (US Eastern here, UTC−4 until 2026-11-01);
2. it carries a systematic +7 minute offset.

No OLBG clock string is used as a start time in this desk. Where an official feed exists, the
official start is used; elsewhere the string is shown verbatim beside an estimate and flagged.

Day labels resolve as: OLBG "Today" = Sat 2026-10-24, "Tomorrow" = Sun 2026-10-25. Because the US
evening of the 24th is the 25th in UTC, the desk is dated **Sunday 25 October 2026** and says so.

## 4. Prices

OLBG suppresses bookmaker prices for this sandbox's location: every card renders `WIN @` with an
empty slot, and every event page renders its market without a decimal or fractional price. Tip
counts, the tipped selection and the share all render normally.

Therefore **no OLBG price is quoted anywhere in this desk.** Every price published is originated
here, and every one is labelled as ours. Recorded as `PRICE-SUPPRESSION`.

## 5. Official counterpart data

| Feed | URL | What it gave |
|---|---|---|
| NHL schedule | `api-web.nhle.com/v1/schedule/2026-10-25` | 5 games, UTC start, venue, neutral-site flag |
| NHL score | `api-web.nhle.com/v1/score/2026-10-25` | same slate with game ids |
| NHL standings | `api-web.nhle.com/v1/standings/2026-10-25` | points snapshot 22:26:59Z |
| NHL team summary | `api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027…` | 32-team season totals (3 chunks; chunk 0 ends mid-record) |
| MLB schedule | `statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-25` | `totalGames: 0` |

Dead ends, not retried: ATP `scores/current/all/2026` (page chrome only), Lega Pallavolo
`classifica` (client-rendered), `liquimoly-hbl.de/de/statistiken/tabelle` (404; the live HBL
table is at `daikin-hbl.de/de/hbl/tabelle`), `nba.com/games?date=` (client-rendered calendar).

## 6. Data quirks that shaped the build

* OLBG event ids follow no arithmetic rule and must be carried verbatim.
* The NHL sub-hub lists a fixture the flat Ice Hockey hub does not (VAN @ ? hides one).
* FLA @ CHI (`2026020180`) is absent from OLBG entirely at capture: the fixture exists in the
  official feed only. It is kept, sourced to the NHL feed, and flagged.
* MIN @ VAN has no official start time in the schedule payload read; left blank, flagged.
* Handball's modal selection is "Tie" on nine rows, several at 100% of a 7-tip sample. A drawn
  handball match is rare; this reads as the draw leg of a three-way market, so those rows are
  published as listed but no price is originated from them (`HANDICAP-DEFAULT`).
* Tennis cards carry players and a clock but no tournament name (`TENNIS-DATES`).

## 7. What this means for the numbers

Only five fixtures have league-level scoring data (the NHL slate). For those, goals for/against per
game are regressed toward the league mean with a fifteen-game prior, adjusted for home ice, and run
through a bivariate Poisson to produce a win line, a puck line and two totals — with complementary
sides, so `P(away +1.5) = 1 − P(home −1.5)`.

For the other 83 priced fixtures the only published signal is OLBG's own tip share, shrunk with a
six-tip prior so a 1-tip board cannot price at certainty. That supports a win line only; a handicap
or a total cannot be invented from a tip share. Those rows are graded no higher than medium.

The arithmetic that decides the brief's targets: a −250 price **is** a 0.7143 chance, so "70%+
confidence" and "−250…+10000" overlap only between 0.70 and 0.7143. The build prints the live
counts on the method page rather than papering over the gap.
