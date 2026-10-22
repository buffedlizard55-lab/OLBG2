# OLBG Reverse-Engineering & Line-by-Line Repository Forensic Audit (`arena/399eb9ae-olbg2`)

- **Audit Date:** `2026-10-22` (UTC)
- **Session / Branch:** `arena/399eb9ae-olbg2`
- **Exclusive Dashboard Namespace:** `/center/` (`data/center/**`, `scripts/center_{seed,model,build,verify}.py`, `center/**`, `tests/test_center_399eb9ae.py`)

---

## 1. OLBG.com Reverse-Engineering (`sitemap-betting-tips.xml` & `/betting-tips`)

First-hand inspection of `https://www.olbg.com/sitemap-betting-tips.xml` and `https://www.olbg.com/betting-tips` on `2026-10-22` establishes OLBG's complete 24-category taxonomy (`/betting-tips/{Sport_Slug}/{Category_ID}`):

### 1.1 Exact 17 Eligible OLBG Sport Categories

| Slug | Sport | OLBG ID | Verified OLBG Hub URL | Official Governing-Body Authority | Oct 22 Slate Status |
| --- | --- | ---: | --- | --- | --- |
| `tennis` | Tennis | `3` | `https://www.olbg.com/betting-tips/Tennis/3` | ATP Tour (`atptour.com`) & WTA (`wtatennis.com`) | **15 ATP originated** (`Almaty 9410`, `Brussels 7485`, `Lyon 496`) + **3 WTA unlined** (`Ningbo 2092`, `Osaka 405`) |
| `basketball` | Basketball | `4` | `https://www.olbg.com/betting-tips/Basketball/4` | NBA (`nba.com`) & EuroLeague (`euroleaguebasketball.net` / `api-live.euroleague.net`) | **11 originated** (2 NBA Oct 22 + 9 EuroLeague R7 Oct 22–23) |
| `golf` | Golf | `5` | `https://www.olbg.com/betting-tips/Golf/5` | PGA Tour (`pgatour.com`) | **1 unlined tournament row** (`Butterfield Bermuda Championship R2026528`; strokes-gained feed JS-gated) |
| `cricket` | Cricket | `7` | `https://www.olbg.com/betting-tips/Cricket/7` | International Cricket Council (`icc-cricket.com`) | **4 unlined rows** (`ODI Tri-Series in PAK`, `NAM v IRE`, `NZ v IND`, `SA v AUS`; ICC team ratings table JS-hydrated) |
| `snooker` | Snooker | `8` | `https://www.olbg.com/betting-tips/Snooker/8` | World Snooker Tour (`wst.tv`) | **8 originated** (all 8 BetVictor Northern Ireland Open Last 16 ties via server-rendered `wst.tv/players/{uuid}`) |
| `rugby-union` | Rugby Union | `9` | `https://www.olbg.com/betting-tips/Rugby_Union/9` | LNR (`top14.lnr.fr`, `prod2.lnr.fr`) & URC (`stats.unitedrugby.com`) | **23 originated** (7 Top 14 J7 + 8 Pro D2 J8 + 8 URC R4) |
| `rugby-league` | Rugby League | `10` | `https://www.olbg.com/betting-tips/Rugby_League/10` | International Rugby League (`intrl.sport`) & NRL (`nrl.com`) | **5 originated** (RLWC 2026 Round 2 Oct 23–25 from IRL world rankings + Round 1 results) |
| `baseball` | Baseball | `12` | `https://www.olbg.com/betting-tips/Baseball/12` | Major League Baseball (`mlb.com` / `statsapi.mlb.com`) | **2 originated** (2026 World Series Games 1–2: Tampa Bay Rays @ Milwaukee Brewers) |
| `ice-hockey` | Ice Hockey | `13` | `https://www.olbg.com/betting-tips/Ice_Hockey/13` | NHL (`nhl.com` / `api-web.nhle.com`) & SHL (`stats.swehockey.se`) | **25 originated** (12 NHL Oct 22 + 13 SHL Oct 22 & Oct 24 from `20961` 2026-27 table) |
| `motor-racing` | Motor Racing | `14` | `https://www.olbg.com/betting-tips/Motor_Racing/14` | Formula 1 (`formula1.com`) | **5 originated H2Hs + 1 race row** (2026 US GP at COTA Oct 23–25 from 18-round WDC standings) |
| `darts` | Darts | `15` | `https://www.olbg.com/betting-tips/Darts/15` | Professional Darts Corporation (`pdc.tv`) | **16 originated** (all 16 Machineseeker European Championship R1 ties in Dortmund Oct 22–23) |
| `handball` | Handball | `20` | `https://www.olbg.com/betting-tips/Handball/20` | European Handball Federation (`ehfcl.eurohandball.com`) | **16 originated** (5 EHF Champions League Men R5 Oct 22 + 11 R6 Oct 28–29 across Groups A–F) |
| `volleyball` | Volleyball | `21` | `https://www.olbg.com/betting-tips/Volleyball/21` | Lega Pallavolo Serie A (`legavolley.it`) & PlusLiga (`plusliga.pl`) | **6 SuperLega R2 originated** (`IdCampionato=999` Oct 25) + **3 PlusLiga unlined** (live 2026/27 table behind Cloudflare) |
| `aussie-rules` | Aussie Rules | `22` | `https://www.olbg.com/betting-tips/Aussie_Rules/22` | AFL / NAB AFLW (`afl.com.au/aflw`) | **9 originated** (all 9 official NAB AFLW Round 11 fixtures `8970`–`8979` Oct 23–25; Men's AFL concluded) |
| `esports` | Esports | `23` | `https://www.olbg.com/betting-tips/eSports/23` | Riot Games LoL Esports (`lolesports.com`) | **8 originated** (LoL Worlds 2026 Swiss Round 1 Bo1s from official `lolesports.com/en-US/gpr/2026/current` GPR) |
| `gaelic-football` | Gaelic Football | `25` | `https://www.olbg.com/betting-tips/Gaelic_Football/25` | Gaelic Athletic Association (`gaa.ie`) | **2 unlined provincial club fixtures** (`gaa.ie` publishes no numeric club ratings) |
| `greyhounds` | Greyhounds | `28` | `https://www.olbg.com/betting-tips/Greyhounds/28` | Greyhound Board of Great Britain (`gbgb.org.uk`) | **1 unlined Category One final** (Coral 100k Romford Champion Stakes Final Oct 23; single-heat clockings insufficient for calibrated 6-trap tissue) |

### 1.2 Excluded OLBG Categories Enforcement (0 Rows Emitted)

All 10 user-excluded terms map cleanly to 7 OLBG category hubs and are hard-blocked at seed, model, build, and test time (`0` rows):
- `Football/1` (soccer / football)
- `Horse_Racing/2` (horse racing)
- `Specials/6` (specials — Entertainment, Reality TV, Politics)
- `American_Football/11` (american football)
- `Boxing/16` (boxing)
- `Cycling/17` (cycling)
- `UFC_MMA/26` (ufc / mma)
- *Hurling* has no standalone OLBG category hub (occasionally surfaces under GAA specials) and is likewise blocked via regex guard.

### 1.3 OLBG Tip Card Schema & Empirical Calibration Benchmarks

1. **Zero Public Bookmaker Odds on OLBG Cards:** Public OLBG match rows render competition headers, UTC/BST timestamps, matchup links (`/betting-tips/{Sport}/{Comp}/{Slug}/{Pick}/{EventID}`), consensus tipster counts (`N/M Win Tips`, `%`), and expert tipster blurbs, **without** public sportsbook odds. Every fair line in `/center/` is independently originated from official governing-body statistics.
2. **OLBG 5-Season Empirical Benchmarks Used for Model Calibration:**
   - **Basketball (`Basketball/NBA/4`):** `68.61%` regular-season closing-favourite win rate (`4,104 / 5,982` games, 2020-21 to 2024-25).
   - **Ice Hockey (`Ice_Hockey/13`):** NHL regular-season favourite win rate `55.99%–64.55%`; SHL `62.26%`.
   - **Handball (`Handball/20`):** EHF Champions League Men favourite win rate `68.2%`, draw rate `9.8%` (`90.2%` non-draw), average total `60.82` goals, average winning margin `5.04` goals.
   - **Rugby Union (`Rugby_Union/9`):** Historical Premiership/European closing-favourite win rate `69.92%–75.45%`, draw rate `<2.5%`.
3. **Why Naive Tipster-Share Reading Concentrates >70% Outside `-250`:** On OLBG hubs, consensus tipster vote shares pile `78%–100%` onto heavy favourites (`>71.43%` implied probability = shorter than `-250` American), e.g., Veszprém `100% (14/14)`, Barça `100% (12/12)`, Magdeburg `92% (11/12)`, Medvedev `85%`, Cobolli `94%`, Littler `87%`. Our `/center/` origination layer prices independent fair probabilities across **Win / 1X2**, **Handicap / Spread / Puck / Run / Frame / Set / Leg Line**, and **Match Total Over/Under**, focusing all high-confidence selections strictly inside **`[-250, +10000]`** (`1.40` to `101.00` decimal) on natural standard increments (`0.5` points/goals/frames/sets/legs/runs) — never synthetic quarter-point handicaps tuned to skirt `-250`.

---

## 2. Line-by-Line Forensic Review of Existing Repository Layers

Every JSON dataset, Python script, and HTML board in the repository was audited line by line against live official governing-body pages fetched on `2026-10-22`:

### `CA-01` (Critical) — 12 of 13 Fabricated ATP R16 Matchups + Stale/Wrong Rankings + 6 Invalid High-Confidence Picks in `/slate/`
- **Files:** `data/slate/matches.json`, `data/slate/inputs.json`, `data/slate/predictions.json`
- **Official Sources:**
  - Almaty (`9410`): [daily-schedule](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule), [draws](https://www.atptour.com/en/scores/current/almaty/9410/draws)
  - Brussels (`7485`): [daily-schedule](https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule), [draws](https://www.atptour.com/en/scores/current/brussels/7485/draws)
  - Lyon (`496`): [daily-schedule](https://www.atptour.com/en/scores/current/lyon/496/daily-schedule), [draws](https://www.atptour.com/en/scores/current/lyon/496/draws)
  - Rankings (`2026-10-19`): [PIF ATP Singles Rankings](https://www.atptour.com/en/rankings/singles)
- **Line-by-Line Findings:**
  1. **Almaty (`atp-alm-r16-1..4`):** `/slate/` listed `Hijikata vs Cobolli`, `Struff vs Khachanov`, `Wong vs Nakashima`, and `Vukic vs Rublev`. Official `atptour.com` (`9410`) proves Cobolli (`#1` seed) and Nakashima (`#5` seed) are playing in **Lyon (`496`)**, Struff is in **Brussels (`7485`)**, Hijikata lost `6-7(5), 2-6` to Terence Atmane in Almaty R32, and Khachanov plays **Tomas Machac** in Almaty R16 (`Atmane vs Bellucci`, `Machac vs Khachanov`, `Medvedev vs Shimabukuro`, `Bublik vs Marozsan`, `Tsitsipas vs Duckworth`). Only `atp-alm-qf-1` (`Duckworth vs Tsitsipas`) matched reality.
  2. **Brussels (`atp-bru-r16-1..4`):** `/slate/` listed `Fearnley vs Cerundolo`, `Machac vs Musetti`, `Collignon vs Griekspoor`, and `Mannarino vs Fils`. Official `atptour.com` (`7485`) proves Machac & Mannarino are in **Almaty (`9410`)**, Musetti is in **Lyon (`496`)**, Collignon plays **#2 Jiri Lehecka**, Griekspoor played Mariano Navone, Cerundolo defeated Martin Damm, and #1 Arthur Fils plays **Jaume Munar** (`Dzumhur vs Bergs`, `Goffin vs Michelsen`, `Collignon vs Lehecka`, `Fils vs Munar`).
  3. **Lyon (`atp-lyo-r16-1..4`):** `/slate/` listed `Prizmic vs Diallo`, `Navone vs Etcheverry`, `Landaluce vs Rublev`, and `Dzumhur vs Paul`. Official `atptour.com` (`496`) proves `(WC) Stan Wawrinka` eliminated `Martin Landaluce` `6-3, 6-7(2), 7-6(5)` in Lyon R32, Rublev & Etcheverry are in **Almaty (`9410`)**, Navone & Dzumhur are in **Brussels (`7485`)**, and Tommy Paul defeated Benjamin Bonzi in Lyon R16 to face Corentin Moutet in the QF!
  4. **Stale/Wrong Rankings in `data/slate/inputs.json`:** `/slate/` cited `Karen Khachanov #16 (2,510 pts)` (official Oct 19 rank is `#25` on `1,990 pts`; `#16` is Jakub Mensik on `2,500`), `Flavio Cobolli #20 (2,255)` (official `#6` on `3,640`), `Brandon Nakashima #37 (1,365)` (official `#17` on `2,375`), `Raphael Collignon #70` (official `#55`), and `Coleman Wong #143` (official `#92`).
  5. **Impact on High-Confidence Predictions:** Six high-confidence picks in `data/slate/predictions.json` (`atp-alm-r16-3`, `atp-bru-r16-2`, `atp-bru-r16-3`, `atp-bru-r16-4`, `atp-lyo-r16-3`, `atp-lyo-r16-4`) recommend bets on non-existent tennis matches.

### `CA-02` (Critical) — Misattributed ATP & WTA Tournaments in `/hub/` (`Basel`, `Vienna`, `Guangzhou` Have Not Started)
- **Files:** `data/hub/matches.json`, `data/hub/predictions.json`, `data/hub/flagged.json`
- **Official Sources:** [ATP Basel `328`](https://www.atptour.com/en/scores/current/basel/328/daily-schedule), [ATP Vienna `337`](https://www.atptour.com/en/scores/current/vienna/337/daily-schedule), [ATP Lyon `496`](https://www.atptour.com/en/scores/current/lyon/496/daily-schedule), [WTA Ningbo `2092`](https://www.wtatennis.com/tournaments/2092/ningbo/2026), [WTA Osaka `405`](https://www.wtatennis.com/tournaments/405/osaka/2026)
- **Findings:**
  - `/hub/` labeled `atp-902116` (`Cobolli vs Wawrinka`) as `ATP Swiss Indoors Basel` and `atp-902133` (`Moutet vs Paul`) — including its high-confidence prediction prose (`"at the Erste Bank Open in Vienna"`) — as `ATP Erste Bank Open Vienna`. Both Basel (`328`) and Vienna (`337`) are Oct 26–Nov 1 tournaments whose official pages currently read `"There Is Currently No Daily Schedule"`; both matches are live at **ATP 250 Grand Prix Auvergne-Rhone-Alpes in Lyon (`496`)**.
  - `/hub/` labeled `wta-902135` (`Talia Gibson vs Ashlyn Krueger`) and `wta-902141` (`Alexandra Eala vs Diana Shnaider`) as `WTA Guangzhou Open` (`1023`, starts Oct 26). Official `wtatennis.com` confirms `#4 Talia Gibson vs Ashlyn Krueger` is the **Kinoshita Group Japan Open (Osaka `405`)** Quarter-Final, while `#1 Elena Rybakina vs Polina Kudermetova`, `Sara Bejlek vs Marie Bouzkova`, and `Alexandra Eala` are at **WTA 500 BNB Ningbo Open (`2092`)**.

### `CA-03` (Critical) — 8 of 9 Scrambled NAB AFLW Round 11 Pairings in `/slate/`
- **Files:** `data/slate/matches.json` (`aflw-r11-1..9`), `data/slate/predictions.json` (`aflw-r11-1`, `aflw-r11-2`, `aflw-r11-4`, `aflw-r11-9`)
- **Official Source:** [NAB AFLW Fixture & Match Centre](https://www.afl.com.au/aflw) (`matches/8970` through `8979`)
- **Findings:** Only `aflw-r11-6` (`North Melbourne vs Adelaide Crows`, match `8979`) matches the official AFLW Round 11 fixture list. The other 8 pairings in `/slate/` (`Melbourne vs Hawthorn`, `Brisbane Lions vs Geelong`, `Essendon vs Western Bulldogs`, `Fremantle vs Port Adelaide`, `Carlton vs Sydney`, `Richmond vs St Kilda`, `GWS vs Collingwood`, `Gold Coast vs West Coast`) are completely scrambled; the true official Round 11 draw is `Port Adelaide vs Collingwood (8970)`, `St Kilda vs Brisbane Lions (8974)`, `Geelong vs Fremantle (8975)`, `Gold Coast vs Richmond (8976)`, `Western Bulldogs vs Melbourne (8978)`, `Sydney vs West Coast (8973)`, `Hawthorn vs Essendon (8977)`, `North Melbourne vs Adelaide (8979)`, and `Carlton vs GWS Giants (8972)`. Four high-confidence predictions in `data/slate/predictions.json` are attached to those non-existent AFLW pairings.

### `CA-04` (Critical) — Fabricated PDC Darts Withdrawal & Replacement Claim (`Noppert vs Edhouse`) in `/slate/`
- **Files:** `data/slate/matches.json` (`pdc-32330`), `data/slate/predictions.json` (`pdc-32330`), `data/slate/flagged.json` (`SL-06`)
- **Official Sources:** [PDC Finalised Field & Draw](https://www.pdc.tv/news/2026/10/18/2026-machineseeker-european-championship-field-and-draw-confirmed), [PDC Event Preview](https://www.pdc.tv/news/2026/10/21/2026-machineseeker-european-championship-preview), [PDC World Rankings](https://www.pdc.tv/rankings)
- **Findings:** `/slate/` replaced `Danny Noppert vs Stephen Bunting` with `Danny Noppert vs Ritchie Edhouse`, claiming Bunting withdrew after Oct 18. Official `pdc.tv` Oct 19 schedule and Oct 21 preview explicitly confirm **`(5) Danny Noppert v (28) Stephen Bunting`** as Thursday's 7th Stage match in Dortmund, while `pdc.tv/rankings` shows William O'Connor took `#32` (`£274,500`) ahead of `#33 Ritchie Edhouse (£274,500)`.

### `CA-05` (High) — Wrong WST Match-Centre UUID & Incomplete/Stale Snooker Coverage Across `/slate/`, `/verified/`, `/board/`, and `/hub/`
- **Files:** `data/slate/matches.json` (`wst-nio-m53`), `data/verified/matches.json`, `data/board/matches.json`, `data/hub/matches.json`
- **Official Sources:** [WST Gilbert vs Cheung Match Centre](https://www.wst.tv/match-centre/1e3806cf-eec4-42c7-b4fc-ed493bc6e236), [WST Slessor vs Walden Match Centre](https://www.wst.tv/match-centre/619c8075-153c-41f4-96a8-de15606cbdd8), [WST Player Profiles](https://www.wst.tv/players/)
- **Findings:**
  - `/slate/` assigned Elliot Slessor vs Ricky Walden's match-centre UUID (`619c8075-153c-41f4-96a8-de15606cbdd8`) to `David Gilbert vs Cheung Ka Wai` (whose true UUID is `1e3806cf-eec4-42c7-b4fc-ed493bc6e236`) and omitted `Slessor vs Walden` and `Jak Jones vs Daniel Wells` from `wst_players`.
  - Meanwhile, `/verified/`, `/board/`, and `/hub/` left **6 of 8** Northern Ireland Open Last 16 matches unlined (`null`), asserting WST only renders Top 36 rankings. First-hand inspection of `https://www.wst.tv/players/{uuid}` proves WST server-renders current world rankings AND live 2026/27 season match/win/century/50+-break totals for **all 16 Last 16 players**, allowing `/center/` to originate all **8 of 8** Last 16 ties cleanly.

### `CA-06` (High) — Wrong SuperLega Round 2 Pairings & False Swap Accusation in `/hub/`
- **Files:** `data/hub/matches.json`, `data/hub/flagged.json`, `data/hub/repo_audit.json`
- **Official Source:** [LegaVolley Regular Season Calendar (`IdCampionato=999`)](https://www.legavolley.it/calendario/?IdCampionato=999)
- **Findings:** `/hub/` listed `Itas Trentino vs Rana Verona` and `Vero Volley Monza vs Cisterna Volley` for Round 2 (`2026-10-25`) and accused OLBG of swapping opponents. Official `legavolley.it` (`Giornata 2`, `25/10/2026 18:00`) confirms **`Itas Trentino vs Cisterna Volley`** (`39526`) and **`Vero Volley Monza vs Rana Verona`** (`39529`) — OLBG was right and `/hub/` swapped the two fixtures (`Trentino vs Verona` was Round 1 on Oct 18, won 3-2 by Verona).

### `CA-07` (High) — Fabricated OLBG Category IDs (`10` Wrong in `/slate/`, `4` Wrong in `/verified/` & `/board/`)
- **Files:** `data/slate/matches.json`, `data/verified/sports.json`, `data/board/sports.json`
- **Official Source:** `https://www.olbg.com/sitemap-betting-tips.xml`
- **Findings:** `/slate/` invented 10 non-existent OLBG sport IDs (`Golf=9`, `Baseball=14`, `Ice Hockey=15`, `Rugby Union=18`, `Rugby League=19`, `Handball=24`, `Aussie Rules=25`, `Motor Racing=27`, `Esports=31`, `Gaelic Football=33`), and `/verified/` + `/board/` misassigned 4 IDs (`Volleyball=19`, `Aussie Rules=21`, `Esports=28`, `Greyhounds=4`). True sitemap IDs are `Golf=5`, `Rugby_Union=9`, `Rugby_League=10`, `Baseball=12`, `Ice_Hockey=13`, `Motor_Racing=14`, `Darts=15`, `Handball=20`, `Volleyball=21`, `Aussie_Rules=22`, `eSports=23`, `Gaelic_Football=25`, `Greyhounds=28`.

### `CA-08` (High) — Stale PGA Tournament (`Bank of Utah`) & False Formula 1 Idle Claim (`VF-17`) in `/verified/`, `/board/`, and `/hub/`
- **Files:** `data/verified/sports.json`, `data/verified/flagged.json` (`VF-17`), `data/board/matches.json`, `data/hub/matches.json`
- **Official Sources:** [PGA Tour Schedule (`R2026528`)](https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528), [Formula 1 2026 United States GP](https://www.formula1.com/en/racing/2026/united-states), [F1 2026 Drivers Standings](https://www.formula1.com/en/results/2026/drivers)
- **Findings:**
  - `pgatour.com/schedule` shows the Oct 22–25 PGA Tour stop is the **Butterfield Bermuda Championship** (`R2026528`, Port Royal GC, `$6.0M` purse; Bank of Utah was a prior week).
  - `formula1.com/en/racing/2026/united-states` confirms the **2026 Formula 1 Pirelli United States Grand Prix** at Circuit of The Americas runs **23–25 Oct 2026** (Sprint weekend, Race Oct 25 20:00 UTC), refuting `VF-17`'s claim that no F1 Grand Prix takes place Oct 22–25.

### `CA-09` (High) — Non-Official Esports Wiki (`liquipedia.net`) & Unverifiable Client-Side JS ICC ODI Ratings in `/slate/`
- **Files:** `data/slate/sources.json`, `data/slate/inputs.json`, `data/slate/matches.json`
- **Official Sources:** [Riot LoL Global Power Rankings](https://lolesports.com/en-US/gpr/2026/current), [ICC Men's ODI Team Rankings](https://www.icc-cricket.com/rankings/team-rankings/mens/odi)
- **Findings:** `/slate/` cited community-edited `liquipedia.net` for LoL Worlds instead of `lolesports.com` (which publishes official Riot GPR scores: `Gen.G 1632`, `BLG 1529`, `HLE 1517`, `TES 1463`, `G2 1413`, `FLY 1397`, etc.), and priced Cricket ODIs from hardcoded ICC ratings (`118`, `108`, `101`) even though `icc-cricket.com/rankings/team-rankings/mens/odi` renders an empty JS shell (`| | | | | |`) in server HTML. Per the zero-inference mandate, `/center/` prices LoL Worlds from official `lolesports.com` GPR and leaves Cricket lines `null` (`unverified_input`) with an explicit flag.

### `CA-10` (Medium) — Synthetic Quarter-Point Handicaps & Duplicate Same-Match High-Confidence Picks in `/verified/` & `/board/`
- **Files:** `data/verified/matches.json`, `data/board/matches.json`, `data/board/predictions.json`
- **Findings:** `/verified/` and `/board/` used non-standard quarter-point handicaps in Rugby Union and Basketball (`-5.75`, `-3.25`, `-5.25`, `-1.75`, `-3.75`, `-0.75`, `-1.25`, `-4.75`) calibrated solely to land fair odds at `-238`/`-244`/`-250` just inside the `-250` boundary, and `data/board/predictions.json` emitted two separate high-confidence picks on the same NHL game (`nhl-2026020163` AND `nhl-2026020163-ml`: Carolina Hurricanes @ Edmonton Oilers). `/center/` uses only authentic half-unit sportsbook lines (`±0.5`, `±1.5`, `±2.5`, ...) and enforces at most **one** featured high-confidence pick per `match_id`.

### `CA-11` (Medium) — Legacy Root `data/matches.json`, `data/live/`, `data/forward/`, `data/desk/`, and `data/survey/` Gaps
- **Files:** `data/matches.json`, `data/predictions.json`, `data/live/`, `data/forward/`, `data/desk/`, `data/survey/`
- **Findings:**
  - Root `data/matches.json`: `47/47` rows have `source_url: null` and `olbg_url: null`, covering only 4 of 17 eligible sports (`ice_hockey`, `basketball`, `handball`, `rugby_union`) and missing start times on URC/EHF rows.
  - `data/forward/`: Covers only 4 of 17 sports (`93` matches, `8` high-confidence predictions) and omits Saturday Oct 24 URC Round 4 fixtures (`292611`–`292615`).
  - `data/live/` & `data/desk/`: Partial coverage (`26` lined rows in `live/`, `35` fixtures / `5` picks in `desk/`).
  - `data/survey/`: Used 2025-26 SHL season `18263` (which includes relegated Leksands IF instead of promoted IF Björklöven in 2026-27 `20961`) and included `Specials/6` in its taxonomy map without a dedicated 17-sport unified board.
  - `COORDINATION.md`: PR #77 accidentally overwrote `arena/42c8f6be-olbg2`'s completed session block (`SL1–SL6`); we restored it cleanly in commit `4b4d7f7`.

---

## 3. `/center/` Quantitative Origination Models & Confidence Band Discipline

Every originated row in `data/center/matches.json` computes zero-vig fair lines (`decimal`, `American`, `implied probability %`) across three standard markets (**Win / 1X2**, **Handicap / Spread**, **Match Total Over/Under**) exclusively from server-verified official governing-body statistics:

1. **Ice Hockey (NHL 12 + SHL 13 = 25 matches):** Bivariate/independent Skellam goal-expectancy model anchored to 2026-27 team `GF/GP` and `GA/GP` regressed toward league mean (`3.08` NHL, `2.82` SHL per team) with home-ice multiplier (`+5.5%` NHL, `+7.5%` SHL) and empirical OT/SO conversion (`60/40` split of regulation ties) producing Moneyline, `±1.5` Puck Line, and `5.5`/`6.5` Game Total O/U.
2. **Basketball (NBA 2 + EuroLeague 9 = 11 matches):** Possession-adjusted Normal margin & total model (`σ = 11.5` NBA, `σ = 10.2` EuroLeague) from official NBA 2025-26 82-game + Oct 21 opening-night ratings and exact 2026-27 EuroLeague R1–R6/R7 played-game point differentials (`61` official `E2026` boxscores), producing Moneyline, half-point Spread, and half-point Game Total O/U.
3. **Tennis (ATP Almaty 5 + Brussels 4 + Lyon 6 = 15 originated; 3 WTA unlined):** Log-points Elo/Bradley-Terry point/game/set Markov model from official `2026-10-19` PIF ATP Singles Rankings points on indoor hard court (`σ_sets`), producing Match Winner, `±1.5` Set Handicap, and `21.5`/`22.5`/`23.5` Total Games O/U.
4. **Darts (PDC European Championship R1 = 16 matches):** Leg-win logistic model from official 2-year PDC Werner Ranking Ladder prize money (`pdc.tv/rankings`) solved exactly via negative-binomial best-of-11 (`first to 6 legs`) combinatorics for Match Winner, `±1.5`/`±2.5` Leg Handicap, and `9.5` Total Legs O/U.
5. **Snooker (WST Northern Ireland Open Last 16 = 8 matches):** Frame-win logistic model blending official `wst.tv/players/{uuid}` world ranking + live 2026/27 season match win rate & century/50+-break rate solved exactly via best-of-7 (`first to 4 frames`) combinatorics for Match Winner, `±1.5` Frame Handicap, and `5.5` Total Frames O/U.
6. **Handball (EHF Champions League Men R5 + R6 = 16 matches):** Calibrated to OLBG's EHF CL Men empirical benchmarks (`60.82` avg goals, `9.8%` draw rate) using official 2026/27 Group A–F `GF/GP` and `GA/GP` (`σ = 5.4` goals, `+2.2` home court), producing 3-Way `1X2`, half-goal Handicap, and half-goal Total O/U.
7. **Rugby Union (Top 14 J7 7 + Pro D2 J8 8 + URC R4 8 = 23 matches):** Normal point-margin & total model (`σ = 12.5`, draw band `±0.5` pts, `+4.2` Top 14 / `+4.5` Pro D2 / `+3.8` URC + `+2.5` SA altitude home advantage) from official J6/J7/R3 standings (`PF/GP`, `PA/GP`, bonus-point table), producing `1X2`, half-point Handicap, and half-point Total O/U.
8. **Rugby League (RLWC Round 2 = 5 matches):** IRL World Ranking + Round 1 score-differential Normal margin model (`σ = 13.5`) producing `1X2`, half-point Handicap, and half-point Total O/U.
9. **Baseball (MLB World Series G1–G2 = 2 matches):** Pythagorean / Skellam run-environment model from official 162-game `statsapi.mlb.com` runs scored/allowed (`MIL 832-618`, `TB 736-650`, home DH park boost) producing Moneyline, `±1.5` Run Line, and `7.5`/`8.0` Total Runs O/U.
10. **Volleyball (SuperLega Credem Banca R2 = 6 originated; 3 PlusLiga unlined):** Point-ratio / set-win Markov model over best-of-5 sets from official `legavolley.it` Round 1 set & point ratios + reigning Serie A pedigree, producing Match Winner, `±1.5` Set Handicap, and `3.5`/`4.5` Total Sets O/U.
11. **Aussie Rules (NAB AFLW Round 11 = 9 matches):** Normal margin & low-scoring 4x15m AFLW total model (`σ = 18.5` pts, `+4.5` home ground) from official 10-round 2026 AFLW ladder (`PF`, `PA`, `%`, `pts`), producing Match Winner, half-point Line, and half-point Total Score O/U.
12. **Motor Racing (F1 US GP at COTA = 5 H2Hs + 1 race row):** Plackett-Luce / logistic paired-comparison model from official 18-round 2026 FIA Drivers' Championship points (`Antonelli 340`, `Russell 238`, `Hamilton 229`, `Verstappen 221`, `Leclerc 215`, `Norris 201`, `Piastri 138`) for 5 featured race classification H2Hs; 22-car outright winner left `null` without Friday FP1/Sprint telemetry.
13. **Esports (LoL Worlds 2026 Swiss R1 = 8 matches):** Official Riot Global Power Rankings (`lolesports.com/en-US/gpr/2026/current`) Elo logistic curve (`scale = 240` GPR pts for Bo1 Swiss variance), producing Match Winner and Bo1 Kill/Duration proxy flag (totals `null` where Riot publishes no kill-rate API).
14. **Strict Zero-Inference Unlined Sports (`Golf`, `Cricket`, `Gaelic Football`, `Greyhounds` + WTA & PlusLiga subsets):** Listed with verified fixtures, timestamps, venues, OLBG links, and official governing-body URLs, with all betting lines explicitly `null` (`—`) and logged in `data/center/flagged.json`.

### Confidence Tiering & `[-250, +10000]` Solution
- **`high` confidence:** Clear structural edge backed by multi-game official sample **and** primary recommended selection (Match Winner if `1.40 <= dec <= 101.00`, otherwise the natural `±1.5` Set/Frame/Puck/Leg/Run Line or standard half-point Spread/Total inside `[-250, +10000]`) priced strictly within **`-250` to `+10000`** (`1.40 <= fair_decimal <= 101.00`).
- **`medium` confidence:** Moderate edge (`55%–61%` win probability or early-season 1–2 game sample) or mismatches whose natural standard handicap still prices outside `[-250, +10000]`.
- **`low` confidence:** Near coin-flips (`<55%` win probability) or high-variance Bo1/early-season openers.
