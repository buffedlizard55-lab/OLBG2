# Canonical OLBG refresh and publication audit — 23 October 2026

**Session branch:** `arena/1b2c50af-olbg2`  
**Research cutoff:** `2026-10-23T21:32:48Z`  
**Canonical desk:** [`/olbg/`](../olbg/index.html)  
**Previous desk record:** [`research/olbg-758c0623.md`](olbg-758c0623.md)

## 1. Scope and outcome

This pass refreshed the existing canonical 15-sport desk rather than creating another overlapping dashboard. The taxonomy remains exactly: Golf, Volleyball, Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball and Rugby League.

The resulting snapshot contains:

- **94 upcoming fixture rows across 11 sports**; all 15 categories have a subpage and an explicit coverage decision.
- **0 active OLBG offers**, **24 last-seen rows**, and **70 official-context-only rows**. These states are never summed with the older Ledger, Cadence, Brief or Monitor desks.
- **59 priced matches**, **63 originated market rows**, **35 deliberately blank matches**, and **56 review items**.
- **Seven high-confidence predictions**: five Ice Hockey and two Basketball. Every prediction exceeds 70%, has a fair American price from −250 through +10000, contains at least 30 words, and carries fact-level official evidence.
- **22 static HTML pages**, including all 15 category pages and the Flagged for Review page.

All odds are independently originated fair prices. They are not bookmaker quotes, current offers, guarantees or betting advice. `last_seen` means an OLBG page or discovery row existed earlier; it does not mean a wager is active now.

## 2. Executive selection summary

| Event | Selection | Estimate | Fair American | OLBG provenance | Official detail evidence |
|---|---|---:|---:|---|---|
| New York Knicks @ Boston Celtics | Boston Celtics moneyline | 70.20% | −236 | Last seen; event page expired | [NBA game preview](https://www.nba.com/game/nyk-vs-bos-0022600008) · [standings](https://www.nba.com/standings?Season=2025-26) · [3:15 PM ET injury report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf) |
| LA Clippers @ Los Angeles Lakers | Los Angeles Lakers moneyline | 71.38% | −249 | Last seen; event page expired | [NBA game preview](https://www.nba.com/game/lac-vs-lal-0022600102) · [standings](https://www.nba.com/standings?Season=2025-26) · [3:15 PM ET injury report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf) |
| Montréal Canadiens @ Chicago Blackhawks | Montréal Canadiens two-way moneyline | 71.43% | −250 | Last seen; event page expired | [NHL gamecentre landing](https://api-web.nhle.com/v1/gamecenter/2026020166/landing) · [team summary](https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2) |
| Los Angeles Kings @ New Jersey Devils | New Jersey Devils two-way moneyline | 71.43% | −250 | Official context only | [NHL gamecentre landing](https://api-web.nhle.com/v1/gamecenter/2026020169/landing) · [team summary](https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2) |
| Carolina Hurricanes @ St. Louis Blues | Carolina Hurricanes two-way moneyline | 71.05% | −245 | Official context only | [NHL gamecentre landing](https://api-web.nhle.com/v1/gamecenter/2026020175/landing) · [team summary](https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2) |
| Detroit Red Wings @ Calgary Flames | Detroit Red Wings two-way moneyline | 70.97% | −244 | Official context only | [NHL gamecentre landing](https://api-web.nhle.com/v1/gamecenter/2026020178/landing) · [team summary](https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2) |
| Florida Panthers @ Chicago Blackhawks | Florida Panthers two-way moneyline | 70.59% | −240 | Official context only | [NHL gamecentre landing](https://api-web.nhle.com/v1/gamecenter/2026020180/landing) · [25 October score feed](https://api-web.nhle.com/v1/score/2026-10-25) |

The complete prose and the exact fact-to-source mapping are in [`data/olbg/predictions.json`](../data/olbg/predictions.json) and [`data/olbg/review.json`](../data/olbg/review.json). Each card on the site exposes the same evidence in a disclosure drawer.

### Evidence corrections made before publication

- The NBA standings were re-read in full. The Clippers’ **home** split is 23–18; their **road** split is 19–22. The pricing input correctly remains 19–22 away. The potential column confusion is logged as `NBA-ROAD-COLUMN-18`.
- The Montréal preview lists Caufield with six season goals and eight points, and Suzuki with 12 points. Caufield alone is the listed Montréal last-five points leader with six; the prose does not attribute that last-five mark to Suzuki.
- New Jersey’s last-five comparison uses Jack Hughes’ six points and four assists against Artemi Panarin’s six points and four goals.
- Carolina’s write-up uses Ehlers’ six last-five points, Aho’s four last-five assists and Kochetkov’s 6–0–0 / 1.98 GAA / .899 save-percentage line. It does not use an uncorroborated season skater total.
- Detroit’s Tarasov line is 1.40 GAA and .940 save percentage. Florida’s last-five comparison uses Brady Tkachuk’s ten points and seven goals, Matthew Tkachuk’s ten assists and Patrick Kane’s four points.
- Boston’s NHL estimate is the sixth in-band candidate. Its [official preview](https://api-web.nhle.com/v1/gamecenter/2026020170/landing) was inspected, but the row remains medium under `CAP-nhl-2026020170-winner` so the daily high-confidence card contains the five highest estimated in-band selections rather than six.
- No NHL gamecentre preview inspected in this batch supplied a dated game-specific availability bulletin. Every NHL prediction says so in distinct language; no injury or confirmed-lineup claim was invented. The NBA injury report remains valid only at its stated timestamp, and its malformed Lakers row was not interpreted.

## 3. Official 25 October NHL schedule reconciliation

The committed official schedule capture adds five FUT games that were absent from the previous 14-row NHL inventory. Two have UTC starts on 26 October while retaining the NHL’s official 25 October game date.

| Game | Official date | UTC start | Venue | Neutral site | Official sources |
|---|---|---|---|---|---|
| Florida Panthers @ Chicago Blackhawks (`2026020180`) | 25 Oct | 25 Oct 19:00 | United Center | No | [schedule](https://api-web.nhle.com/v1/schedule/2026-10-25) · [score](https://api-web.nhle.com/v1/score/2026-10-25) |
| New York Islanders @ Dallas Stars (`2026020181`) | 25 Oct | 25 Oct 22:00 | American Airlines Center | No | [schedule](https://api-web.nhle.com/v1/schedule/2026-10-25) · [score](https://api-web.nhle.com/v1/score/2026-10-25) |
| Montréal Canadiens @ Winnipeg Jets (`2026020182`) | 25 Oct | 25 Oct 23:00 | Princess Auto Stadium | **Yes** | [schedule](https://api-web.nhle.com/v1/schedule/2026-10-25) · [score](https://api-web.nhle.com/v1/score/2026-10-25) |
| Colorado Avalanche @ Nashville Predators (`2026020183`) | 25 Oct | 26 Oct 00:00 | Bridgestone Arena | No | [schedule](https://api-web.nhle.com/v1/schedule/2026-10-25) · [score](https://api-web.nhle.com/v1/score/2026-10-25) |
| Minnesota Wild @ Vancouver Canucks (`2026020184`) | 25 Oct | 26 Oct 02:00 | Rogers Arena | No | [schedule](https://api-web.nhle.com/v1/schedule/2026-10-25) · [score](https://api-web.nhle.com/v1/score/2026-10-25) |

The NHL inventory is now 19 officially upcoming games: two on the official 23 October date, 12 on 24 October and five on 25 October. It is not represented as an exhaustive list beyond that evidenced window.

## 4. Raw evidence integrity

`scripts/olbg_seed.py` reads the committed copies under `data/olbg/captures/`, checks exact byte counts and SHA-256 hashes, and only then constructs team inputs and fixtures.

| Capture | Official fetch time (UTC) | SHA-256 | Stored evidence |
|---|---|---|---|
| NHL team summary | 2026-10-23 20:32:15 | `a3293d5f2d9859255fc8c0564f28b190ff85e29c5a6044ced9730eaa9a372e8e` | [`nhl_team_summary_2026-10-23.json`](../data/olbg/captures/nhl_team_summary_2026-10-23.json) |
| NHL schedule, 24 October | 2026-10-23 20:32:11 | `4d7ef26a4ab4f15bd24f3bdd461cdb7192b2007ce10b40bf2c1e77a2fe999e00` | [`nhl_schedule_2026-10-24.json`](../data/olbg/captures/nhl_schedule_2026-10-24.json) |
| NHL schedule, 25 October | 2026-10-23 20:32:12 | `9b020d7fa6ca042414737bfdfcff2bf76a079ff42030425204e4f8bbf859c03b` | [`nhl_schedule_2026-10-25.json`](../data/olbg/captures/nhl_schedule_2026-10-25.json) |

All 32 current team-summary rows are mapped by official team ID and normalized name. This avoids the earlier exploratory `Montreal` / `Montréal` key mismatch. Public display retains the accented Montréal name.

## 5. Checked-page OLBG access audit

Each URL below returned inspected content displaying **“No tips found”** in this review batch. Motor Racing and Rugby League also displayed no tournament tips. This is a checked-page result only; it is not proof that every OLBG event, tournament or market is globally empty.

| Requested category | Inspected OLBG hub |
|---|---|
| Golf | [Golf/5](https://www.olbg.com/betting-tips/Golf/5) |
| Volleyball | [Volleyball/21](https://www.olbg.com/betting-tips/Volleyball/21) |
| Rugby Union | [Rugby_Union/9](https://www.olbg.com/betting-tips/Rugby_Union/9) |
| Cricket | [Cricket/7](https://www.olbg.com/betting-tips/Cricket/7) |
| Snooker | [Snooker/8](https://www.olbg.com/betting-tips/Snooker/8) |
| Darts | [Darts/15](https://www.olbg.com/betting-tips/Darts/15) |
| Baseball | [Baseball/12](https://www.olbg.com/betting-tips/Baseball/12) |
| Gaelic Sports | [Gaelic_Football/25](https://www.olbg.com/betting-tips/Gaelic_Football/25) · [Hurling/26](https://www.olbg.com/betting-tips/Hurling/26) |
| Greyhounds | [Greyhounds/28](https://www.olbg.com/betting-tips/Greyhounds/28) |
| Tennis | [Tennis/3](https://www.olbg.com/betting-tips/Tennis/3) |
| Motor Racing | [Motor_Racing/14](https://www.olbg.com/betting-tips/Motor_Racing/14) |
| Handball | [Handball/20](https://www.olbg.com/betting-tips/Handball/20) |
| Ice Hockey | [Ice_Hockey/13](https://www.olbg.com/betting-tips/Ice_Hockey/13) |
| Basketball | [Basketball/4](https://www.olbg.com/betting-tips/Basketball/4) |
| Rugby League | [Rugby_League/10](https://www.olbg.com/betting-tips/Rugby_League/10) |

The earlier 16:20 OLBG inventory remains separately labeled as discovery history. No tipster share was used as an independent probability.

## 6. Coverage and abstention

| Sport | Fixture rows | Priced | High-confidence | Daily shortlist |
|---|---:|---:|---:|---:|
| Golf | 0 | 0 | 0 | 0/5 |
| Volleyball | 0 | 0 | 0 | 0/5 |
| Rugby Union | 1 | 0 | 0 | 0/5 |
| Cricket | 4 | 1 | 0 | 1/5 |
| Snooker | 5 | 0 | 0 | 0/5 |
| Darts | 4 | 4 | 0 | 4/5 |
| Baseball | 5 | 5 | 0 | 5/5 |
| Gaelic Sports | 0 | 0 | 0 | 0/5 |
| Greyhounds | 0 | 0 | 0 | 0/5 |
| Tennis | 15 | 8 | 0 | 5/5 |
| Motor Racing | 1 | 0 | 0 | 0/5 |
| Handball | 14 | 0 | 0 | 0/5 |
| Ice Hockey | 19 | 19 | 5 | 5/5 |
| Basketball | 22 | 22 | 2 | 5/5 |
| Rugby League | 4 | 0 | 0 | 0/5 |

“5/5” is a priced shortlist count, not five high-confidence predictions. The daily target remains evidence-limited. Ranking-only Tennis, Darts and Cricket estimates are capped below high; incomplete participant fields stay blank. Baseball’s five season-record prices do not pass the detailed high-confidence gate. Golf, Volleyball, Gaelic Sports and Greyhounds have no supportable upcoming row in this snapshot. Motor Racing, Handball, Rugby Union and Rugby League retain official-context rows without invented prices.

## 7. Market and pricing rules

- NBA prices use official completed 2025–26 venue splits in a two-way log5 comparison. Current opener facts and timestamped availability provide written context, not hidden numerical adjustments.
- NHL prices use exact current-season points divided by twice games played in the same public log5 formula. There is no undisclosed home, goalie or injury adjustment.
- Only the two expired OLBG-linked NHL events have originated puck-line and 6.5-total rows. Those four additional markets use a disclosed independent-Poisson calculation and remain low confidence.
- MLB uses overall 162-game records. Run lines and totals stay blank without explicit pitching and extra-inning inputs.
- EuroLeague, ATP, PDC and ICC rows retain their existing public formulas and caps. Unsupported handicaps, totals, player fields, dates and clocks remain blank.
- No current bookmaker price was captured or substituted for a fair price.

## 8. Repository review and retained irregularities

- The repository contains multiple historical dashboards with different dates and counts. This pass updates only canonical `/olbg/`; counts from `/cadence/`, `/ledger/`, `/brief/` and `/monitor/` are not added together.
- Historical conflict-marker text remains in shared `COORDINATION.md` and `METHODOLOGY.md`. It is logged as `REPO-16`; unrelated historical content was not silently rewritten.
- Existing OLBG line/comment mismatches, PDC clock disagreement, GAA status conflict, incomplete ATP rankings, uncertified clocks and unavailable runner/field data remain in Flagged for Review with source links.
- Open stale coordination-only PRs #167 and #161 were left untouched.
- The fixed Arena branch was used as required; no alternate session branch was created.

## 9. Reproduce and inspect

```sh
python scripts/olbg_seed.py
python scripts/olbg_model.py
python scripts/olbg_predictions.py
python scripts/olbg_build.py
python scripts/olbg_verify.py
python -m unittest discover -s tests -q
python scripts/integration_audit.py
```

The offline build performs no network request. CI rebuilds committed evidence and drift-checks generated outputs; it does not refresh fixtures, availability or OLBG status. The [`Sources & audit page`](../olbg/sources.html) contains the 16 hub checks, raw hashes, reconciliation record, complete source register and a row-by-row review state for all 94 events.
