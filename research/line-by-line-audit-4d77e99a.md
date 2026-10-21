# Line-by-Line Repository & Official-Source Forensic Audit (`arena/4d77e99a-olbg2`)

**Audit date:** `2026-10-21` (UTC)  
**Baseline inspected:** `origin/main` commit `04204a0` (post-PR #42, encompassing root `data/**`, `data/desk/**`, `data/survey/**`, `scripts/*.py`, and all published HTML pages across `/`, `/site/`, `/survey/`, and `/integration.html`).  
**Companion machine-readable ledger:** [`data/verified/repo_audit.json`](../data/verified/repo_audit.json) · **Interactive review pages:** [`verified/audit.html`](../verified/audit.html) and [`verified/flagged.html`](../verified/flagged.html).

---

## 1. Executive Summary

Every data file, generator script, model equation, and published narrative across all three repository layers was audited line by line against **primary official governing-body and league endpoints retrieved live on `2026-10-21`**. No secondary media site, odds aggregator, encyclopedia, or unverified cache was accepted as proof.

| Repository Layer | Scope Audited | Line-by-Line Verdict | Action Taken in Session `4d77e99a` |
|---|---|---|---|
| **Layer 3 — `/survey/` (`data/survey/**`, `scripts/survey_*.py`)** | 21 sports in `sports.json`, 15 event files (130 rows), 11 originated lines, 11 picks, 2 `HIGH` predictions, 21 flags | **Critical defects found** (`RA-01`–`RA-06`): `predictions.json` `P-02` published a completed June 2026 tournament (`England Women v West Indies Women`, `ICC Women's T20 World Cup 2026`) dated `2026-10-21`; `scripts/survey_analyse.py` & `picks.json` spliced two separate cricket scorecards into `"won by 200 runs (190 vs 109)"` (`190 - 109 = 81`); 11/15 prediction-fact URLs cited non-official sites (`wikipedia.org`, `espn.com`, `cricinfo.com`, `thesportsencounter.com`, `rugbyrama.fr`, `allrugby.com`, `racingpost.com`); 45 inventory rows used `indexed_snapshot` from `2026-10-18` instead of live `2026-10-21` OLBG hubs; `rugby_league.json` was `[]` despite 3 live OLBG markets; `Hurling/26`, `Gaelic_Football/25`, and `Greyhounds/28` were missing from `sports.json`. | **100% remediated directly in `/survey/` (`V3`)** and superseded with full multi-market coverage in `/verified/` (`V2`). |
| **Layer 2 — `/site/` (`data/desk/**`, `scripts/engine.py`, `scripts/build.py`)** | 25 NHL + NBA fixtures, 62 team records, 5 high/medium picks | **1 factual player-stat discrepancy found** (`RA-07`): `data/desk/picks.json` (`nhl-2026020152`, `PHI @ BUF`) reported `"Tage Thompson on three goals"`, whereas official NHL API (`https://api-web.nhle.com/v1/score/2026-10-21`) confirms `Tage Thompson` (`id: 8479420`, `#72`, `BUF`) has **`5` goals** (`"value": 5`). All 25 game IDs, venues, start times, 32 NHL records, and 30 NBA records matched official feeds; `nhl-2026020158` (`Brady Tkachuk`, `id: 8480801`, `teamAbbrev: "FLA"`, `6` goals; `Matthew Tkachuk`, `id: 8479314`, `11` assists) verified 100% accurate for `season: 20262027`. | **100% remediated directly in `data/desk/picks.json` + regenerated `/site/` (`V3b`)**. |
| **Layer 1 — Root Dashboard (`data/**`, `scripts/model.py`, `scripts/build_site.py`)** | 47 fixtures (16 NHL, 11 NBA, 8 URC, 12 EHF Handball, 2 Cricket unlined), 9 `HIGH` predictions, 23 flags | **Core numerical tables verified accurate; metadata/attribution notes & 7 previously uncaptured official slates documented**: (1) `data/inputs/fixtures.json` leaves `SAC @ LAC` `game_id` `null` (`F03`), whereas `https://www.nba.com/games?date=2026-10-21` publishes `0022600093` (`https://www.nba.com/game/sac-vs-lac-0022600093`); (2) `data/predictions.json` `nhl-2026020152` cites `https://api-web.nhle.com/v1/scoreboard/2026-10-22` for a 19 October game score; (3) `data/predictions.json` Handball prose formats unbeaten `3W-1D-0L` records as `"3-1-0"` right beside NHL `W-L-OTL` records (`"4-3-2"`). All 24 EHF club `gp/w/d/l/gf/ga/pts` values, all 16 NHL team totals, all 30 NBA records, and all 16 URC Round 4 table rows matched official feeds digit for digit. | Root files left untouched in deference to active session `arena/e3c5f898-olbg2`; **logged in `COORDINATION.md` and fully expanded with clean primary data in `/verified/` (`V2`)**. |

---

## 2. Detailed Line-by-Line Findings Register (`RA-01` – `RA-14`)

### `RA-01` · CRITICAL · Committed `data/survey/predictions.json` (`P-02`) out of sync with `scripts/survey_analyse.py` and published a completed June 2026 tournament as a `2026-10-21` `HIGH` pick
- **Location:** `data/survey/predictions.json` lines 53–89 (`id: "P-02"`), rendered live on `survey/predictions.html` and `survey/index.html`.
- **Published value:** `event: "England Women v West Indies Women"`, `competition: "ICC Women's T20 World Cup 2026"`, `start_time: "2026-10-21 15:00"`, `selection: "England Women"`, `confidence: "high"`, `model_prob: 0.774`, citing `espn.com`, `wikipedia.org`, and `icc-cricket.com`.
- **Official verification (`https://www.icc-cricket.com/tournaments/womens-t20-world-cup-2026`, `https://www.olbg.com/betting-tips/Cricket/7`):** The ICC Women's T20 World Cup 2026 in England took place in **June–July 2026** (four months before `2026-10-21`). Neither `olbg.com/betting-tips/Cricket/7` nor `data/survey/events/cricket.json` contains `England Women v West Indies Women`. A prior edit updated `scripts/survey_analyse.py` without running it to regenerate `data/survey/predictions.json`.
- **Resolution:** Purged completely. `scripts/survey_analyse.py`, `data/survey/picks.json`, and `data/survey/predictions.json` are now generated deterministically in lockstep and enforced by unit tests.

### `RA-02` · CRITICAL · Mathematically impossible spliced cricket score (`190 vs 109 = "won by 200 runs"`) and fabricated `HIGH` override in `scripts/survey_analyse.py` / `data/survey/picks.json`
- **Location:** `scripts/survey_analyse.py` lines 52–108 (`VERIFIED_H2H["afghanistan vs bangladesh one day match"]`) and `data/survey/picks.json` lines 16–39.
- **Published value:**
  - `copy`: *"Afghanistan beat Bangladesh by 200 runs in the second ODI, bowling them out for 109 in pursuit of 191"*
  - `facts`: *"2nd ODI, 11 Oct 2025: Afghanistan won by 200 runs (Afghanistan 190, Bangladesh 109 in 28.3 overs)"*
  - Lowered `HIGH` probability threshold from `0.63` to `0.55` specifically to force `p = 0.5987` into `confidence = "high"`.
- **Forensic mathematical proof & official verification (`https://www.icc-cricket.com/matches/274658/afghanistan-vs-bangladesh`):** A team defending `190` cannot win by `200 runs` (`190 - 109 = 81 runs` — in the Oct 2025 Abu Dhabi series, Afghanistan won the 2nd ODI `190 vs 109` by **81 runs** and the 3rd ODI `293 vs 93` by **200 runs**; the author spliced two separate matches into one impossible sentence and cited `thesportsencounter.com`, `wikipedia.org`, `espn.com`, and `cricinfo.com`). Furthermore, `icc-cricket.com/matches/274658/afghanistan-vs-bangladesh` renders `"Loading"` for body statistics and `icc-cricket.com/rankings/team-rankings/mens/odi` renders client-side.
- **Resolution:** Spliced claim, non-official links, and artificial `0.55` confidence override completely deleted. `Afghanistan v Bangladesh` (`274658`) is catalogued with its official ICC match link and left **unlined (`—`)** rather than backed by unverified ratings.

### `RA-03` · HIGH · 11 of 15 fact citations in `data/survey/predictions.json` pointed to non-official domains even where primary governing-body pages exist
- **Location:** `data/survey/predictions.json` (`P-01` `Toulouse v Perpignan` and `P-02`).
- **Published value:** Cited `wikipedia.org` (×3), `rugbyrama.fr` (×2), `espn.com` (×2), `allrugby.com` (×1), `racingpost.com` (×1), plus `cricinfo.com` and `thesportsencounter.com` in `survey_analyse.py`.
- **Official verification:**
  - Ligue Nationale de Rugby official Top 14 standings (`https://top14.lnr.fr/classement`) directly confirms `Stade Toulousain` `#2` (`4W-0D-2L, 217 PF, 128 PA, +89, 19 pts`) and `USA Perpignan` `#14` (`0W-0D-6L, 88 PF, 200 PA, -112, 0 pts`), plus official J7 match sheet `https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan`.
  - EPCR official Champions Cup results (`https://www.epcrugby.com/champions-cup/matches`) directly confirms `Stade Toulousain 60 - 14 Sale Sharks` (`11 Oct 2026`, Stade Ernest Wallon).
- **Resolution:** Replaced 100% of third-party URLs across `data/survey/` with verified primary governing-body URLs (`top14.lnr.fr`, `prod2.lnr.fr`, `stats.unitedrugby.com`, `epcrugby.com`, `ehfcl.eurohandball.com`, `euroleaguebasketball.net`, `pdc.tv`, `wst.tv`, `atptour.com`, `formula1.com`, `api.nhle.com`, `nba.com`, `statsapi.mlb.com`). `scripts/official_source_audit.py` now verifies **0 non-official fact URLs**.

### `RA-04` · HIGH · Incomplete OLBG sport taxonomy in `data/survey/sports.json` (`Hurling/26`, `Gaelic_Football/25`, `Greyhounds/28` omitted; only 15 of 17 eligible sports surveyed)
- **Location:** `data/survey/sports.json`, `scripts/survey_inventory.py`.
- **Official verification (`https://www.olbg.com/sitemap-betting-tips.xml` & live OLBG hub crawls on `2026-10-21`):**
  - `Hurling` (`https://www.olbg.com/betting-tips/Hurling/26`) exists on OLBG (`sport_id = 26`, 5 club championship events live) and must be **explicitly listed and excluded** per prompt instructions.
  - `Gaelic Football` (`https://www.olbg.com/betting-tips/Gaelic_Football/25`, `sport_id = 25`) has **5 live OLBG markets** (`3530`, `3531`, `3532`, `3536`, `3327`).
  - `Greyhounds` (`https://www.olbg.com/betting-tips/Greyhounds/28`, `sport_id = 28`) has **6 live 21 October race cards** (`689383`–`689387`, `689390`).
  - `Aussie Rules` (`https://www.olbg.com/betting-tips/Aussie_Rules/22`, `sport_id = 22`) and `eSports` (`https://www.olbg.com/betting-tips/eSports/23`, `sport_id = 23`) were fetched live on `2026-10-21` and confirmed to have **0 active tip markets (`"No tips found"`)**.
- **Resolution:** `data/survey/sports.json` now catalogs all **23 OLBG sports** (`17` eligible + `6` OLBG-active excluded categories, alongside the complete 10-sport exclusion gate).

### `RA-05` · MEDIUM · Stale `indexed_snapshot` rows (`2026-10-18`) and empty `rugby_league.json` across `data/survey/events/*.json`
- **Location:** `data/survey/events/ice_hockey.json`, `handball.json`, `volleyball.json`, `darts.json`, `baseball.json`, `motor_racing.json`, `rugby_league.json`, `rugby_union.json`.
- **Official verification (`2026-10-21` live `olbg.com` crawl):**
  - `rugby_league.json` was `[]`, whereas `https://www.olbg.com/betting-tips/Rugby_League/10` lists **3 active 2027 outrights**: `NRL Premiership 2027` (`2695857`, `Penrith Panthers` `3/5` `60%`), `Super League 2027` (`2801554`, `Wigan Warriors` `3/7` `43%`), and `State of Origin 2027` (`2801600`, `Queensland` `2/2` `100%`).
  - `ice_hockey.json` listed completed `2026-10-18` NHL games instead of live `2026-10-21+` events (`199876`–`199914`); `handball.json` missed 5 of 12 live EHF CL Round 5 events (`12044`–`12055`) and kept finished Oct 18 games; `darts.json` missed `Danny Noppert v Stephen Bunting` (`32330`) and `Kevin Doets v Michael van Gerwen` (`32331`) and lacked event URLs; `baseball.json` lacked event ID `160789` (`TB Rays @ MIL Brewers`, `Over 5.50`, `4/4` `100%`).
- **Resolution:** All **17 `data/survey/events/<sport>.json` files** refreshed from live `2026-10-21` OLBG fetches (`0` `indexed_snapshot` rows remaining) with live OLBG URLs AND verified governing-body URLs per row.

### `RA-06` · MEDIUM · Missing row-level official source links across `/survey/` sport tables
- **Location:** `scripts/survey_build.py` (`sport_page`) and `data/survey/events/*.json`.
- **Defect:** Previously flagged by audits `9b76e3ea`, `8f07248b`, and `18eca832`: none of the 130 rows in `data/survey/events/*.json` carried an `official_url` field, so sport tables rendered only `OLBG` links.
- **Resolution:** Every row across all 17 `/survey/` sport files now carries explicit `official_source`, `official_url`, and `official_status` (`verified_fixture` vs `competition_hub_only`), rendered directly as clickable links on every row of `survey/sports/<slug>.html` AND `verified/sports/<slug>.html`.

### `RA-07` · MEDIUM · Stale player goal tally in `data/desk/picks.json` (`nhl-2026020152`, `PHI @ BUF`)
- **Location:** `data/desk/picks.json` lines 6–9 (`nhl-2026020152`).
- **Published value:** `"Jack Quinn on seven points and Tage Thompson on three goals"`.
- **Official verification (`https://api-web.nhle.com/v1/score/2026-10-21`):** `teamLeaders` for game `2026020152` reports `Tage Thompson` (`id: 8479420`, `#72`, `BUF`) `"category": "goals", "value": 5` and `Zach Benson` (`id: 8484145`, `#6`, `BUF`) `"category": "assists", "value": 6`.
- **Resolution:** Fixed directly in `data/desk/picks.json` and rebuilt `/site/` deterministically via `python3 scripts/build.py`.

### `RA-08` · LOW · `data/survey/lines.json` & `scripts/survey_lines.py` mislabel 2026-27 URC **Round 4** as `"Round 6"`
- **Location:** `data/survey/lines.json` (`SL-08`, `SL-09`).
- **Official verification (`https://stats.unitedrugby.com/match-centre/2026-27/4` & `https://stats.unitedrugby.com/match-centre/table/2026-27`):** Every URC club has played **`PL = 3`** matches entering `23–24 October 2026`, and fixtures `292608`–`292615` sit on official endpoint `/match-centre/2026-27/4` (**Round 4**). Fixed directly in `scripts/survey_lines.py` and `/verified/`.

### `RA-09` · LOW · Root `data/inputs/fixtures.json` missing `SAC @ LAC` NBA `game_id` (`F03`)
- **Location:** `data/inputs/fixtures.json` (`Sacramento Kings @ LA Clippers`, `game_id: null`).
- **Official verification (`https://www.nba.com/games?date=2026-10-21`):** Official game ID is **`0022600093`** (`https://www.nba.com/game/sac-vs-lac-0022600093`). Published with its verified game ID and URL in `/verified/` and `data/survey/events/basketball.json`.

### `RA-10` · LOW · Root `data/predictions.json` (`nhl-2026020152`) cites `scoreboard/2026-10-22` for a `2026-10-19` game result
- **Location:** `data/predictions.json` line 23 (`"Philadelphia beat Colorado 3-2 on 19 October"` -> `"source": "https://api-web.nhle.com/v1/scoreboard/2026-10-22"`).
- **Official verification:** The 19 October game appears on `https://api-web.nhle.com/v1/score/2026-10-19` (and weekly window endpoints), not as a `2026-10-22` game card. Documented in `COORDINATION.md` and avoided in `/verified/`.

### `RA-11` · LOW · Root `data/predictions.json` mixes NHL `W-L-OTL` (`4-3-2`) with EHF Handball `W-D-L` (`3-1-0`) notation on the same page
- **Location:** `data/predictions.json` (`ehfcl-202711020101029`, `ehfcl-202711020101032`, `ehfcl-202711020101041`).
- **Detail:** `Aalborg`, `PSG`, and `Sporting` are unbeaten (`3 wins, 1 draw, 0 losses = 7 pts`), written `"3-1-0"` directly beneath NHL records where `"4-3-2"` means `4 wins, 3 regulation losses, 2 OT losses`. In `/verified/` and `/survey/`, drawn-sport records explicitly spell out `"3W-1D-0L"` so readers never misread draws as losses.

### `RA-12` · RESOLVED IN `/verified/` · Previously unoriginated official slates recovered from live governing-body feeds
- **Darts (`F05`):** Recovered all **32/32 PDC European Championship players' official ranks and two-year prize money (`£`)** directly from `https://www.pdc.tv/rankings` -> **16 matches originated** across Moneyline, Leg Handicap, and Total Legs.
- **Tennis (`F04`):** Recovered official `2026.10.19` PIF ATP Top 100 rankings (`https://www.atptour.com/en/rankings/singles`) + live draws -> **5 Top-100 ATP matches originated** across Moneyline, Set Handicap (`±1.5`), and Total Sets (`O/U 2.5`); **9 WTA/Challenger matches kept explicitly unlined (`—`)** rather than guessing unrendered ranks.
- **Rugby Union (`F08`):** Recovered official LNR Top 14 J7 (`7` matches, 14-club table at `https://top14.lnr.fr/classement`) and Pro D2 J8 (`8` matches, 16-club table at `https://prod2.lnr.fr/classement`) alongside URC Round 4 (`8` matches) -> **23 Rugby Union matches originated**.
- **European Basketball:** Recovered official EuroLeague Round 7 (`10` matches, 20-club table at `https://www.euroleaguebasketball.net/en/euroleague/standings/`) and BKT EuroCup Round 4 (`4` matches, 32-club table at `https://www.euroleaguebasketball.net/en/eurocup/standings/`) -> **14 European Basketball matches originated across all 3 markets (including Totals)**.
- **Snooker (`F06`):** Recovered all **11 Wed Oct 21 BetVictor Northern Ireland Open Round 2 matches** (`https://www.wst.tv/matches/`) + Top-36 Johnstone's Paint World Rankings (`https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false`) -> **2 Top-36 matches originated**; **9 matches involving `#37+` players kept strictly unlined (`—`)**.
- **Baseball & Formula 1:** Originated **2026 MLB World Series Game 1 (`TB @ MIL`, `gamePk=849805`)** from official 162-game `statsapi.mlb.com` stats and **2026 F1 US GP + Drivers' World Championship** from official `formula1.com/en/results/2026/drivers` points.

### `RA-13` · INTENTIONALLY KEPT BLANK (`—`) · Unconfirmed inputs left strictly blank and flagged rather than inferred
1. **NBA Game Totals (`11` games):** `nba.com/standings?Season=2025-26` omits team `PTS+ / PTS-`; total column left `—` on every NBA row.
2. **WTA & ATP `#101+` Tennis Rankings (`9` matches):** `wtatennis.com/rankings/singles` renders via client JS and ATP ranks beyond `#100` require JS pagination; rankings and odds left `—`.
3. **WST Snooker Rankings `#37+` (`9` matches):** `wst.tv/rankings/...` renders `#1–#36` server-side only; `#37+` ranks and match prices left `—`.
4. **Polish Volleyball (`4` matches, `F22`):** `plusliga.pl/table.html` redirects to shared PLS `tauronliga.pl/table.html` and every team has played only `M = 1` match (`N = 1` is statistically insufficient for independent origination); prices left `—`.
5. **ICC Cricket (`3` matches, `F11`):** `icc-cricket.com` rankings and match scorecards render client-side (`"Loading"`); prices left `—`.
6. **Golf (`2`), Rugby League (`3`), Gaelic Football (`5`), Greyhounds (`6`), Aussie Rules (`0` active), eSports (`0` active):** Official event/governing-body pages linked on every row; unverified player strokes-gained, 2027 pre-roster ratings, county club tables, and licensed trap ratings left strictly `—`.
