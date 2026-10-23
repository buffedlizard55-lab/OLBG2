# Final integration audit — 23 October 2026

- **Session:** `arena/f0ee1b4a-olbg2`
- **Stored snapshot:** `2026-10-23T20:10:00Z`
- **Integration external spot checks:** `2026-10-23T21:30:02Z`
- **Primary site:** https://buffedlizard55-lab.github.io/OLBG2/cadence/

> **Verification boundary.** Every one of the 93 fixture records was checked internally against the generated match, selection and source-register records. External pages were re-read only for the spot checks below. A 'pass' means internal consistency; it does not mean all 59 external sources were fetched again. Official links are provided for manual review.

## Executive result

| Check | Result |
|---|---:|
| Fixture rows internally consistent | 93 / 93 |
| Sourced fact entries checked | 245 |
| Registered official/OLBG sources | 59 |
| Priced / blank-price fixtures | 83 / 10 |
| Originated prices / graded selections | 728 / 122 |
| High / medium write-ups | 22 / 11 |
| Natural / alternate high selections in −250…+10000 | 0 / 8 |
| Blank venues retained | 48 |
| Publisher-local time strings retained without UTC inference | 61 |
| Active OLBG listings confirmed by integration | 0 |
| Internal errors after corrections | 0 |

The 93 rows are **not** represented as 93 currently listed OLBG events. The full OLBG schedule, every available market, current bookmaker prices and five qualifying high-confidence write-ups per sport remain incomplete and visible as review findings.

## Findings and corrections

| ID | Status | Item | Finding | Source | Manual review |
|---|---|---|---|---|---|
| FI-01 | corrected | Cork Gaelic football source-to-price inputs | The previous calculation used +8 v +2. The cited scores are Nemo 1-15 to 0-16 and St Finbarr's 2-12 to 0-16, both two-point wins. The basis and generated row now use +2 v +2; the selection remains low confidence. | [official/source](https://gaacork.ie/league/215999/) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/scripts/cadence_model.py) |
| FI-02 | corrected | Outright and three-way fixture summaries | Six outright summaries used an event name or a blank opponent instead of the leading golfer, runner or driver; four also inverted the leading probability. Summaries now equal their primary selection. Three-way summaries use draw-inclusive probabilities. | [official/source](https://www.pgatour.com/leaderboard) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/tests/test_integration_f0ee1b4a.py) |
| FI-03 | corrected | Unsupported Gaelic OLBG event id | The Gaelic row's numeric olbg_event_id=14 had no corresponding event URL in the stored capture or source register. It was removed. A live read of that constructed URL returned 'No tips found.' | [official/source](https://www.olbg.com/betting-tips/Gaelic_Football/25?event_id=14) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/fixtures.json) |
| FI-04 | needs review | Current OLBG listing coverage is not established | Only 1 of 93 rows retains a recorded OLBG event id with a matching registered URL, and its live re-read returned 'No tips found.' The integration therefore confirms zero currently readable active OLBG listings. The other rows are official-context fixtures, not claimed OLBG listings. | [official/source](https://www.olbg.com/betting-tips/Ice_Hockey/13?event_id=199984) | [review](https://buffedlizard55-lab.github.io/OLBG2/olbg/flagged.html) |
| FI-05 | needs review | Blank venue fields | 48 fixture rows have no confirmed venue and remain blank across 6 sports. No venue has been inferred. Each affected row and its official source is enumerated below. | [official/source](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/fixtures.json) | [review](https://buffedlizard55-lab.github.io/OLBG2/cadence/matches.html) |
| FI-06 | needs review | Five high-confidence write-ups per sport | The target is met for 2 of 15 sports (Basketball, Rugby League). There are 22 high-confidence and 11 medium-confidence write-ups in total; medium write-ups are not counted toward the high-confidence target. | [official/source](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/predictions.json) | [review](https://buffedlizard55-lab.github.io/OLBG2/cadence/predictions.html) |
| FI-07 | needs review | NHL published comparison prices moved after the stored capture | The live schedule still listed both NHL fixtures as FUT with the stored teams, starts and venues. Provider 8 showed Montréal -170 / Chicago +138 in the integration read, while the 20:05Z record stored -169 / +137. The desk's own probabilities were not changed; its historical comparison prose remains tied to the earlier capture. | [official/source](https://api-web.nhle.com/v1/schedule/2026-10-23) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/captures/nhle_schedule.json) |
| FI-08 | needs review | Historical desks are not consolidated into current counts | Older overlapping desks retain their own stale taxonomy, prose and source-link findings. They are preserved for audit, not added to the current 93-row snapshot. The existing 16-findings repository audit remains linked from the current desk. | [official/source](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/repo_audit.json) | [review](https://buffedlizard55-lab.github.io/OLBG2/cadence/audit.html) |
| FI-09 | needs review | Cork official participant ordering differs between sources | Cork GAA lists Nemo Rangers v St Finbarrs, while the stored Munster source string and generated row list St Finbarr's v Nemo Rangers. The final is at a neutral venue; no home/away designation is inferred and the underlying 48% low-confidence selection mapping is unchanged. The ordering discrepancy remains explicit for manual review. | [official/source](https://gaacork.ie/league/215999/) | [review](https://munster.gaa.ie/fixtures/events-calendar/) |

## External spot checks

These are page-reading-tool observations, not a substitute for a raw-response archive or a full refresh.

- **2026-10-23T21:30:02Z — [https://api-web.nhle.com/v1/schedule/2026-10-23](https://api-web.nhle.com/v1/schedule/2026-10-23):** NHL JSON retrieved. Games 2026020166 and 2026020167 were FUT with the stored participants, UTC starts and venues. Provider 8 prices had moved as described in FI-07.
- **2026-10-23T21:30:02Z — [https://www.olbg.com/betting-tips/Ice_Hockey/13?event_id=199984](https://www.olbg.com/betting-tips/Ice_Hockey/13?event_id=199984):** OLBG page retrieved; the event area displayed 'No tips found.' No active market or listing was inferred.
- **2026-10-23T21:30:02Z — [https://www.olbg.com/betting-tips/Gaelic_Football/25?event_id=14](https://www.olbg.com/betting-tips/Gaelic_Football/25?event_id=14):** OLBG page retrieved; it displayed 'No tips found.' and did not identify the Cork final.
- **2026-10-23T21:30:02Z — [https://gaacork.ie/league/215999/](https://gaacork.ie/league/215999/):** Cork GAA page retrieved; it listed Nemo Rangers v St Finbarrs on 25 October at 16:00 and the two semi-final scorelines used in FI-01. Its participant order differs from the stored Munster source string, as disclosed in FI-09.
- **2026-10-23T21:30:02Z — [https://gaacork.ie/fixtures/](https://gaacork.ie/fixtures/):** Cork GAA fixture page independently listed the same final, venue and referee David Murnane.

## Line-by-line fixture checks

Every row below was compared across `fixtures.json`, `matches.json`, its primary pick and the source register. 'Publisher time' means the official local/display string is retained and no UTC value was invented. Blank venue cells remain blank and are flagged here. 'OLBG listing unestablished' is not proof that an event is absent from OLBG; only the recorded NHL event URL was live-spot-checked in this integration.

| # | Sport | Fixture | Facts | Price | Start representation | Blank / OLBG state | Internal check | Official source |
|---:|---|---|---:|---|---|---|---|---|
| 1 | Ice Hockey | Chicago Blackhawks v Montréal Canadiens | 3 | originated | UTC | recorded OLBG id; active listing not confirmed | pass | [official](https://api-web.nhle.com/v1/schedule/2026-10-23) |
| 2 | Ice Hockey | Colorado Avalanche v Tampa Bay Lightning | 3 | originated | UTC | OLBG listing unestablished | pass | [official](https://api-web.nhle.com/v1/schedule/2026-10-23) |
| 3 | Basketball | Milwaukee Bucks v Chicago Bulls | 4 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 4 | Basketball | Boston Celtics v New York Knicks | 4 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 5 | Basketball | Washington Wizards v Toronto Raptors | 7 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 6 | Basketball | Charlotte Hornets v Atlanta Hawks | 9 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 7 | Basketball | Orlando Magic v Minnesota Timberwolves | 8 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 8 | Basketball | Indiana Pacers v Dallas Mavericks | 8 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 9 | Basketball | Miami Heat v Detroit Pistons | 5 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 10 | Basketball | San Antonio Spurs v Houston Rockets | 9 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 11 | Basketball | Utah Jazz v New Orleans Pelicans | 5 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 12 | Basketball | Golden State Warriors v Memphis Grizzlies | 8 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 13 | Basketball | Los Angeles Lakers v LA Clippers | 7 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 14 | Basketball | Sacramento Kings v Portland Trail Blazers | 9 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.nba.com/games?date=2026-10-23) |
| 15 | Basketball | Panathinaikos AKTOR Athens v Armani Olimpia Milan | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026) |
| 16 | Basketball | Valencia Basket v Fenerbahce Tarfin Istanbul | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026) |
| 17 | Basketball | Kosner Baskonia Vitoria-Gasteiz v Real Madrid | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026) |
| 18 | Basketball | Besiktas Istanbul v Olympiacos Piraeus | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026) |
| 19 | Basketball | Hapoel IBI Tel Aviv v Anadolu Efes Istanbul | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026) |
| 20 | Basketball | Virtus Bologna v Zalgiris Kaunas | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026) |
| 21 | Baseball | Milwaukee Brewers v Tampa Bay Rays | 5 | originated | UTC | OLBG listing unestablished | pass | [official](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-11-02) |
| 22 | Baseball | Milwaukee Brewers v Tampa Bay Rays | 4 | originated | UTC | OLBG listing unestablished | pass | [official](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-11-02) |
| 23 | Cricket | Tasmanian Tigers v Victoria | 1 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.cricket.com.au/matches?isCompleted=0&year=2026) |
| 24 | Cricket | Western Australia v New South Wales | 1 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.cricket.com.au/matches?isCompleted=0&year=2026) |
| 25 | Cricket | New Zealand v India | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.cricket.com.au/matches?isCompleted=0&year=2026) |
| 26 | Cricket | Pakistan v England | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.cricket.com.au/matches?isCompleted=0&year=2026) |
| 27 | Cricket | India Women v Zimbabwe Women | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.cricket.com.au/matches?isCompleted=0&year=2026) |
| 28 | Cricket | South Africa v Australia | 1 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.cricket.com.au/matches?isCompleted=0&year=2026) |
| 29 | Snooker | Kyren Wilson v Sam Craigie | 3 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/matches/) |
| 30 | Snooker | Shaun Murphy v Mitchell Mann | 3 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464) |
| 31 | Snooker | Zhou Yuelong v Liam Davies | 3 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464) |
| 32 | Snooker | Liu Hongyu v Louis Heathcote | 1 | blank | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464) |
| 33 | Snooker | Jimmy White v Mark Selby | 2 | blank | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464) |
| 34 | Snooker | Michal Szubarczyk v Wildcard 1 | 1 | blank | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464) |
| 35 | Snooker | Steven Hallworth v Wildcard 3 | 1 | blank | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464) |
| 36 | Snooker | Liu Wenwei v Wildcard 4 | 1 | blank | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464) |
| 37 | Darts | Ross Smith v Damon Heta | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 38 | Darts | Gian van Veen v Luke Woodhouse | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 39 | Darts | Cameron Menzies v Gerwyn Price | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 40 | Darts | Stephen Bunting v Kim Huybrechts | 2 | blank | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 41 | Darts | Wessel Nijman v Ryan Joyce | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 42 | Darts | Jonny Clayton v Josh Rock | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 43 | Darts | Krzysztof Ratajski v Michael van Gerwen | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 44 | Darts | Nathan Aspinall v Luke Littler | 2 | blank | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| 45 | Tennis | Daniil Medvedev v Alexander Bublik | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule) |
| 46 | Tennis | Nikoloz Basilashvili v Stefanos Tsitsipas | 2 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule) |
| 47 | Tennis | Vit Kopriva v Lukas Neumayer | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule) |
| 48 | Tennis | Joel Schwaerzler v Titouan Droguet | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule) |
| 49 | Tennis | Fabian Marozsan v Sebastian Sorger | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule) |
| 50 | Golf | Butterfield Bermuda Championship | 3 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.pgatour.com/leaderboard) |
| 51 | Golf | Genesis Championship | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.europeantour.com/dpworld-tour/genesis-championship-2026/leaderboard) |
| 52 | Greyhounds | Arena Racing Company Scurry Gold Cup Final | 4 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/) |
| 53 | Greyhounds | Premier Greyhound Racing Oaks Final | 4 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/) |
| 54 | Handball | Nantes v Chambéry | 2 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.lnh.fr/daikin-starligue/calendrier) |
| 55 | Handball | Saint-Raphaël v Paris | 2 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.lnh.fr/daikin-starligue/calendrier) |
| 56 | Handball | Montpellier v Saran | 2 | originated | UTC | venue, OLBG listing unestablished | pass | [official](https://www.lnh.fr/daikin-starligue/calendrier) |
| 57 | Handball | Paris v Aalborg | 1 | blank | UTC | venue, OLBG listing unestablished | pass | [official](https://www.lnh.fr/daikin-starligue/calendrier) |
| 58 | Handball | Montpellier v Bucarest | 1 | blank | UTC | venue, OLBG listing unestablished | pass | [official](https://www.lnh.fr/daikin-starligue/calendrier) |
| 59 | Handball | Plock v Nantes | 1 | blank | UTC | venue, OLBG listing unestablished | pass | [official](https://www.lnh.fr/daikin-starligue/calendrier) |
| 60 | Motor Racing | United States Grand Prix | 4 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.formula1.com/en/racing/2026/united-states) |
| 61 | Motor Racing | Formula 1 Drivers' Championship 2026 | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.formula1.com/en/results/2026/drivers) |
| 62 | Rugby League | Papua New Guinea v Samoa | 3 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 63 | Rugby League | England v France | 3 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 64 | Rugby League | New Zealand v Cook Islands | 3 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 65 | Rugby League | Australia v Fiji | 3 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 66 | Rugby League | England v Papua New Guinea | 1 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 67 | Rugby League | New Zealand v Fiji | 1 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 68 | Rugby League | Australia v Cook Islands | 1 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 69 | Rugby League | Lebanon v France | 1 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 70 | Rugby League | Tonga v Samoa | 1 | originated | UTC | OLBG listing unestablished | pass | [official](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |
| 71 | Rugby Union | Leicester Tigers v Northampton Saints | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.premrugby.com/fixtures-results) |
| 72 | Rugby Union | Bristol Bears v Exeter Chiefs | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.premrugby.com/fixtures-results) |
| 73 | Rugby Union | Harlequins v Saracens | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.premrugby.com/fixtures-results) |
| 74 | Rugby Union | Vodacom Bulls v Ulster | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://stats.unitedrugby.com/match-centre/2026-27/4) |
| 75 | Rugby Union | DHL Stormers v Scarlets | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://stats.unitedrugby.com/match-centre/2026-27/4) |
| 76 | Rugby Union | Benetton Rugby v Glasgow Warriors | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://stats.unitedrugby.com/match-centre/2026-27/4) |
| 77 | Rugby Union | Leinster v Munster | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://stats.unitedrugby.com/match-centre/2026-27/4) |
| 78 | Rugby Union | Ospreys v Dragons RFC | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://stats.unitedrugby.com/match-centre/2026-27/4) |
| 79 | Volleyball | Sir Susa Scai Perugia v Tinet Prata di Pordenone | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.legavolley.it/calendario/?idCampionato=999) |
| 80 | Volleyball | Itas Trentino v Cisterna Volley | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.legavolley.it/calendario/?idCampionato=999) |
| 81 | Volleyball | Gas Sales Bluenergy Piacenza v Valsa Group Modena | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.legavolley.it/calendario/?idCampionato=999) |
| 82 | Volleyball | Cucine Lube Civitanova v Pallavolo Padova | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.legavolley.it/calendario/?idCampionato=999) |
| 83 | Volleyball | Allianz Milano v Acqua Sant'Anna Cuneo | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.legavolley.it/calendario/?idCampionato=999) |
| 84 | Volleyball | Vero Volley Monza v Rana Verona | 3 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.legavolley.it/calendario/?idCampionato=999) |
| 85 | Volleyball | VfB Friedrichshafen v BADEN VOLLEYS Karlsruhe | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/hauptrunde.xhtml) |
| 86 | Volleyball | SVG Lüneburg v SV Warnemünde | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/hauptrunde.xhtml) |
| 87 | Volleyball | Helios GRIZZLYS Giesen v BERLIN RECYCLING Volleys | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/hauptrunde.xhtml) |
| 88 | Volleyball | SWD powervolleys Düren v WWK Volleys München | 1 | originated | publisher time string; no UTC inferred | venue, OLBG listing unestablished | pass | [official](https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/hauptrunde.xhtml) |
| 89 | Gaelic Sports | Ireland v Scotland | 1 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.gaa.ie/fixtures-results) |
| 90 | Gaelic Sports | St Finbarr's v Nemo Rangers | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished, official participant order differs: Cork GAA lists Nemo Rangers first | pass | [official](https://gaacork.ie/fixtures/) |
| 91 | Gaelic Sports | Dr Crokes v Kenmare Shamrocks | 1 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.kerrygaa.ie/clubs/kenmare-shamrocks/) |
| 92 | Gaelic Sports | Rathgormack v The Nire | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://www.waterfordgaa.ie/results/) |
| 93 | Gaelic Sports | Na Piarsaigh v Kilmallock | 2 | originated | publisher time string; no UTC inferred | OLBG listing unestablished | pass | [official](https://limerickgaa.ie/na-piarsaigh-gaa-club-notes-213/) |

## Reproduction

```sh
python3 scripts/cadence_seed.py
python3 scripts/cadence_model.py
python3 scripts/cadence_predictions.py
python3 scripts/cadence_build.py
python3 scripts/cadence_verify.py
python3 scripts/integration_f0ee1b4a_audit.py
python3 -m unittest tests.test_integration_f0ee1b4a -v
```

No probability was copied from OLBG. The integration corrections changed the Cork basis and fixture-summary presentation; they did not create a high-confidence pick or add prediction prose.
