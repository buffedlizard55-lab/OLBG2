# Horizon Desk (`arena/9c5af337-olbg2`) — 23 October 2026 (21:40 UTC) Research & Audit

## 1. Scope & Parallel-Session Discipline

Session `arena/9c5af337-olbg2` operates in the disjoint `/horizon/` namespace (`horizon/**`, `data/horizon/**`, `scripts/horizon_*.py`, `tests/test_horizon_9c5af337.py`, `research/horizon-9c5af337.md`, and append-only entries in `COORDINATION.md`). Concurrent sessions (`arena/f0ee1b4a-olbg2`, `arena/1b2c50af-olbg2`, `arena/deb1cb6e-olbg2`, `arena/181705f4-olbg2`, `arena/110cf432-olbg2`, `arena/84013d5f-olbg2`) hold claims over root pages, `README.md`, `scripts/build_site.py`, and their own respective namespaces; `/horizon/` touches none of their claimed files.

## 2. Live OLBG.com Reverse Engineering (`2026-10-23T21:33:00Z`)

Fetching `https://www.olbg.com/betting-tips` and sport/event routes directly from the US sandbox confirmed:

1. **15-Sport Taxonomy (16 OLBG `sportId` routes)**:
   - Golf (`/betting-tips/Golf/5`)
   - Volleyball (`/betting-tips/Volleyball/21`)
   - Rugby Union (`/betting-tips/Rugby_Union/9`)
   - Cricket (`/betting-tips/Cricket/7`)
   - Snooker (`/betting-tips/Snooker/8`)
   - Darts (`/betting-tips/Darts/15`)
   - Baseball (`/betting-tips/Baseball/12`)
   - Gaelic Sports (`/betting-tips/Gaelic_Football/25` and `/betting-tips/Hurling/26`)
   - Greyhounds (`/betting-tips/Greyhounds/28`)
   - Tennis (`/betting-tips/Tennis/3`)
   - Motor Racing (`/betting-tips/Motor_Racing/14`)
   - Handball (`/betting-tips/Handball/20`)
   - Ice Hockey (`/betting-tips/Ice_Hockey/13`)
   - Basketball (`/betting-tips/Basketball/4`)
   - Rugby League (`/betting-tips/Rugby_League/10`)
2. **Four Structural Defects on Live OLBG Pages**:
   - **US Egress Hub Suppression**: All `/betting-tips/{Sport}/{id}` hubs return `No tips found.` to a US egress IP while direct `?event_id=` routes resolve.
   - **Header Denominator String-Concatenation Bug**: Event headers concatenate the selection tip count onto the market total (`4 / 042` instead of `4 / 42` on `event_id=199984`; `6 / 062` on `event_id=160789`; `9 / 090` on `event_id=536036`; `2 / 021` on `event_id=902163`).
   - **Geo-Stripped Bookmaker Odds Cells**: Logged-out US visitors receive `WIN @` with empty price strings on event market rows.
   - **False `Expired` Badges & Unlabelled Timezone Shifts**: Unstarted Saturday 24 October fixtures display `Expired` badges alongside US-Eastern local times without a timezone suffix.

Consequently, OLBG is used strictly for sport/event taxonomy discovery; every fixture, statistic, injury designation, and probability input on `/horizon/` comes from an official governing-body, league, tour, or federation source.

## 3. Official Governing-Body Updates Captured at `2026-10-23T21:40:00Z`

Compared with earlier 2026-10-23 captures (`20:05Z`), live fetches at `21:33Z–21:40Z` established the following real-time official developments:

- **Snooker (`https://www.wst.tv/matches/` & `https://www.wst.tv/rankings/`)**:
  - BetVictor Northern Ireland Open Quarter-Final Match 59 (`David Gilbert v Mark Williams`) is now **Completed**: **Mark Williams defeated David Gilbert 6–4** (`match-centre/19048b0d-aaf4-4691-ad10-15b1b707f622`).
  - Quarter-Final Match 60 (`Jak Jones v Scott Donaldson`) is **Live Now** tied at `4–4` (29–0 in Frame 9 of 11). Saturday's Semi-Final Match 62 (`24 Oct, 14:00`) is therefore **Mark Williams vs Winner of Match 60 (Jak Jones / Scott Donaldson)** — left blank/unpriced until Match 60 concludes.
  - Semi-Final Match 61 (`Kyren Wilson vs Sam Craigie`, `24 Oct, 08:00`) is confirmed upcoming after Wilson beat Anthony McGill 6–1 and Craigie beat Elliot Slessor 6–2.
- **Tennis (`https://www.atptour.com/en/scores/current`, `daily-schedule`, and `rankings/singles?rankRange=0-100`)**:
  - In **Brussels (`7485`)**, Arthur Fils (#10, 3,325 pts) defeated Alex Michelsen (#37, 1,370 pts) `6-4, 7-6(12)` on his sixth match point, and Jan-Lennard Struff (#58, 929 pts) defeated Zizou Bergs (#41, 1,220 pts). The official Saturday 24 October Semifinal schedule is now published:
    - `Francisco Cerundolo (#21, 2,220 pts) vs Tallon Griekspoor (#60, 885 pts)` (Not Before 16:00 local)
    - `Arthur Fils (#10, 3,325 pts) vs Jan-Lennard Struff (#58, 929 pts)` (Not Before 18:30 local)
  - In **Lyon (`496`)**, top seed Flavio Cobolli (#6, 3,640 pts) defeated Brandon Nakashima (#17, 2,375 pts) `4-6, 6-4, 6-4`, Tommy Paul (#15, 2,575 pts) defeated Corentin Moutet `6-4, 3-6, 6-3`, and Taylor Fritz (#14, 2,880 pts) defeated Daniel Altmaier (#65, 849 pts) `7-6(5), 6-2`. That locks in Saturday's `Tommy Paul vs Taylor Fritz` semifinal, while Cobolli awaits the winner of `Luca Van Assche vs Lorenzo Musetti` (live at `0-6, 7-6(5), 3-2` in Set 3).
  - In **Almaty (`9410`)**, Daniil Medvedev (#5, 3,660 pts) defeated Terence Atmane `6-4, 6-4` and Alexander Bublik (#19, 2,275 pts) defeated Karen Khachanov (#25, 1,990 pts) `4-6, 7-6(5), 7-6(5)` to set up Saturday's `Daniil Medvedev vs Alexander Bublik` semifinal alongside `Nikoloz Basilashvili (Q) vs Stefanos Tsitsipas (#39, 1,330 pts)`.
  - In **Basel (`328`)** and **Vienna (`337`)**, Saturday 24 October Qualifying Round 1 schedules pit Top-100 ranked players against each other (`Marcos Giron #88 vs Yannick Hanfmann #59`, `Miomir Kecmanovic #57 vs Rinky Hijikata #86`, `Juan Manuel Cerundolo #53 vs Zachary Svajda #77`, `Thiago Agustin Tirante #50 vs Adrian Mannarino #79`, `Jacob Fearnley #87 vs Pablo Carreno Busta #74`, `Adolfo Daniel Vallejo #54 vs Lorenzo Sonego #89`, `Alex Molcan #80 vs Hamad Medjedovic #76`).
- **Rugby Union (`https://stats.unitedrugby.com/match-centre/2026-27/4` & `https://stats.unitedrugby.com/match-centre/table/2026-27`)**:
  - All three Friday 23 October URC Round 4 fixtures are now **Full Time**: `Cardiff Rugby 21–36 Hollywoodbets Sharks`, `Connacht 48–27 Zebre Parma`, and `Edinburgh 31–10 10bet Lions`.
  - Crucially, fetching the official 2026/27 URC League Table (`https://stats.unitedrugby.com/match-centre/table/2026-27`) provided official 3-match records, points for/against, point differentials, tries for/against, and league points for all ten clubs competing in Saturday's five URC Round 4 fixtures (`Vodacom Bulls vs Ulster`, `DHL Stormers vs Scarlets`, `Benetton Rugby vs Glasgow Warriors`, `Leinster vs Munster`, `Ospreys vs Dragons RFC`), alongside the three Gallagher PREM Round 4 fixtures (`Leicester Tigers vs Northampton Saints`, `Bristol Bears vs Exeter Chiefs`, `Harlequins vs Saracens`).
- **Handball (`https://www.lnh.fr/daikin-starligue/calendrier` & `classement`)**:
  - All five Friday 23 October Daikin StarLigue Round 8 matches are now completed (`Aix 32–26 Toulouse`, `Chartres 32–33 Nîmes`, `Limoges 32–24 Dunkerque`, `Sélestat 24–26 Caen`, `Tremblay 34–29 Cesson-Rennes`), leaving three upcoming Round 8 matches (`Nantes vs Chambéry` Sat 24 Oct, `Saint-Raphaël vs Paris` Sun 25 Oct, `Montpellier vs Saran` Sun 25 Oct) plus three EHF Champions League Round 6 fixtures (`Paris vs Aalborg`, `Plock vs Nantes`, `Montpellier vs Bucarest`).
- **Golf (`https://www.pgatour.com/leaderboard`)**:
  - At the Butterfield Bermuda Championship (Port Royal Golf Course), Round 2 completed for the leading wave with the projected cut moving to `-5`: Kensei Hirata (65–64) and Chandler Blanchet (62–67) share T1 at `-13` (129), one shot ahead of five players tied T3 at `-12` (130): Seamus Power (66–64), Corey Conners (63–67), Eric Cole (65–65), Ben Silverman (63–67), and Danny Walker (63–67).

## 4. Odds-Band Arithmetic (`-250` to `+10000`) & Confidence Grading

- Fair American odds of `-250` correspond to implied probability $p = \frac{250}{350} = 71.4286\%$, while `+10000` corresponds to $p = \frac{100}{10100} = 0.9901\%$.
- High confidence requires $p \ge 70.00\%$ supported by full-season (`Tier A`) or multi-round (`Tier B`, 4–9 games) official numeric evidence (or a natural outright/moneyline selection on a 1–3 game `Tier C` sample, with alternate band-ceiling lines on `Tier C` samples capped at `medium`).
- Consequently, `high` confidence and the `-250` to `+10000` fair-odds band intersect strictly inside $[70.00\%, 71.43\%]$. `/horizon/` never fabricates or shifts a moneyline probability to force a heavy favourite into the band; instead, it reports each selection's true fair price, marks whether that price sits in band, and quotes the exact alternate handicap or total line from the fixture's continuous distribution that sits inside $[70.00\%, 71.43\%]$ (`-233` to `-250` fair).
