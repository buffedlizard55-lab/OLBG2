# Independent First-Hand Official-Source Verification & Line-by-Line Repository Audit (`arena/d81930c3-olbg2`)

- **Session:** `arena/d81930c3-olbg2`
- **Audit Date (UTC):** `2026-10-22`
- **Deliverable Portal:** [`/portal/`](../portal/index.html) (`portal/flagged.html`, `portal/audit.html`, `data/portal/repo_audit.json`, `data/portal/flagged.json`)
- **Scope Rule:** Strictly read-only inspection of inherited layers (`root`, `/site/`, `/survey/`, `/live/`, `/verified/`, `/forward/`, `/board/`, `/slate/`, `/hub/`, `/evidence/`); all remediations and newly originated 17-sport lines live exclusively inside `portal/**`, `data/portal/**`, `scripts/portal_*.py`, `research/audit-d81930c3.md`, and `tests/test_portal_d81930c3.py`.

---

## 1. Live OLBG.com Reverse-Engineering Summary (`2026-10-22` UTC)

All four sitemap shards listed on `https://www.olbg.com/sitemap.xml` (`sitemap-betting-tips.xml` chunks `0..3`) and all live hub endpoints `https://www.olbg.com/betting-tips/<Slug>/<ID>` (`ID = 1..28`) were fetched directly on `2026-10-22`:

### 1.1 Exact Live OLBG Sport ID Map (`ID = 1..28`)

| OLBG ID | Canonical Live Hub Path | Eligibility Status | Live `2026-10-22` Hub State |
|---:|---|---|---|
| `1` | `/betting-tips/Football/1` | **EXCLUDED** (`soccer` / `football`) | Active tips — blocked by exclusion filter |
| `2` | `/betting-tips/Horse_Racing/2` | **EXCLUDED** (`horse racing`) | Active UK/IRE racecards — blocked by exclusion filter |
| `3` | `/betting-tips/Tennis/3` | **ELIGIBLE (1/17)** | Live ATP 250 (`Almaty`, `Brussels`, `Lyon`) & WTA (`Ningbo`, `Osaka`) ties (`902069..902133`) |
| `4` | `/betting-tips/Basketball/4` | **ELIGIBLE (2/17)** | Live NBA Opening Week + EuroLeague Round 7 + EuroCup + KBL/NBB |
| `5` | `/betting-tips/Golf/5` | **ELIGIBLE (3/17)** | Live `Butterfield Bermuda Championship` (`101904`) & `Stifel Charity Classic` (`101903`) |
| `6` | `/betting-tips/Specials/6` | **EXCLUDED** (`specials`) | HTTP 200 (`No tips found`) — blocked by exclusion filter |
| `7` | `/betting-tips/Cricket/7` | **ELIGIBLE (4/17)** | Live `Afghanistan v Zimbabwe` (`188831`), CSA Pro20 (`188811`, `188825`), + 5 futures |
| `8` | `/betting-tips/Snooker/8` | **ELIGIBLE (5/17)** | Live 8× WST BetVictor Northern Ireland Open Round 3 ties |
| `9` | `/betting-tips/Rugby_Union/9` | **ELIGIBLE (6/17)** | Live French Top 14 J7, Pro D2 J8, and URC Round 4 ties |
| `10` | `/betting-tips/Rugby_League/10` | **ELIGIBLE (7/17)** | Live 3× 2027 futures; active Oct 23–25 RLWC Round 2 verified via `rlwc2026.com` / `nrl.com` |
| `11` | `/betting-tips/American_Football/11` | **EXCLUDED** (`american football`) | Active NFL/NCAAF tips — blocked by exclusion filter |
| `12` | `/betting-tips/Baseball/12` | **ELIGIBLE (8/17)** | Live 2026 World Series Game 1 `Tampa Bay Rays @ Milwaukee Brewers` (`160789`) |
| `13` | `/betting-tips/Ice_Hockey/13` | **ELIGIBLE (9/17)** | Live 12× NHL games + 7× Swedish SHL (`199899..199906`) + Finnish Liiga (`199912`) |
| `14` | `/betting-tips/Motor_Racing/14` | **ELIGIBLE (10/17)** | Live `2026 United States Grand Prix` (`913`), `F1 Drivers Championship` (`828`), `2027 WDC` (`912`) |
| `15` | `/betting-tips/Darts/15` | **ELIGIBLE (11/17)** | Live 16× PDC European Championship R1 (`32322..32337`) + Euro/World outrights (`32338`, `26023`) |
| `16` | `/betting-tips/Boxing/16` | **EXCLUDED** (`boxing`) | Active fight tips — blocked by exclusion filter |
| `17` | `/betting-tips/Cycling/17` | **EXCLUDED** (`cycling`) | HTTP 200 — blocked by exclusion filter |
| `18` | `/betting-tips/Entertainment/18` | **EXCLUDED** (`specials`) | UK TV/entertainment novelty markets — blocked by exclusion filter |
| `19` | `/betting-tips/Politics/19` | **EXCLUDED** (`specials`) | Political novelty markets — blocked by exclusion filter |
| `20` | `/betting-tips/Handball/20` | **ELIGIBLE (12/17)** | Live 5× EHF Men's Champions League R5 + domestic HBL/Denmark/Sweden fixtures |
| `21` | `/betting-tips/Volleyball/21` | **ELIGIBLE (13/17)** | Live Polish PlusLiga (`36963..36965`), Tauron Liga (`36988`), Italian SuperLega (`36994`, `36996`), Czech Extraliga |
| `22` | `/betting-tips/Aussie_Rules/22` | **ELIGIBLE (14/17)** | `No tips found` on OLBG; active Oct 23–25 NAB AFLW Round 11 verified via `afl.com.au` |
| `23` | `/betting-tips/eSports/23` | **ELIGIBLE (15/17)** | `No tips found` on OLBG; active Oct 23–24 LoL Worlds Swiss R1 verified via `lolesports.com` |
| `24` | `/betting-tips/Specials/24` | **EXCLUDED** (`specials`) | HTTP 200 (`No tips found`) — blocked by exclusion filter |
| `25` | `/betting-tips/Gaelic_Football/25` | **ELIGIBLE (16/17)** | Live 5× Senior Club County Finals (`3530`, `3531`, `3532`, `3536`, `3537`) + `All-Ireland 2027` (`3327`) |
| `26` | `/betting-tips/Hurling/26` | **EXCLUDED** (`hurling`) | **LIVE** with `Ballyhale Shamrocks v Tullaroan` (`714`) & `All Ireland Hurling 2027` (`675`) — blocked |
| `27` | `/betting-tips/UFC_MMA/27` | **EXCLUDED** (`ufc` / `mma`) | HTTP 200 (`No tips found`) — blocked by exclusion filter |
| `28` | `/betting-tips/Greyhounds/28` | **ELIGIBLE (17/17)** | Live 4× UK BAGS cards (`689570..689584`); Cat-1 `Coral 100 Champion Stakes Final` verified via `gbgb.org.uk` |

---

## 2. Line-by-Line Forensic Findings Across Inherited Repository Layers (`PA-01` – `PA-12`)

Every data file (`data/matches.json`, `data/predictions.json`, `data/verified/*`, `data/forward/*`, `data/board/*`, `data/slate/*`, `data/hub/*`, `data/live/*`, `data/survey/*`, `data/desk/*`) and documentation file (`REPO_REVIEW.md`, `METHODOLOGY.md`) was audited line by line against live governing-body feeds fetched on `2026-10-22`:

### `PA-01` (CRITICAL — Hallucinated Fixtures & Predictions): 12 of 13 Tennis Matches & 6 of 7 Tennis High-Confidence Picks in `/slate/` Do Not Exist on Official ATP Draws
- **Files affected:** `data/slate/matches.json` (`atp-alm-r16-1..4`, `atp-bru-r16-1..4`, `atp-lyo-r16-1..4`), `data/slate/predictions.json` (Predictions `[0]..[5]`).
- **Evidence:** Direct fetches of `https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule`, `https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule`, and `https://www.atptour.com/en/scores/current/lyon/496/daily-schedule` on `2026-10-22` prove that 12 of `/slate/`'s 13 ATP fixtures are non-existent pairings:
  - `Rinky Hijikata vs Flavio Cobolli` (`Almaty R16`): Hijikata lost in Almaty R32 on Oct 20 to Terence Atmane (`7-6(5), 6-2`), while Flavio Cobolli is top seed in **Lyon** playing `(WC) Stan Wawrinka`.
  - `Jan-Lennard Struff vs Karen Khachanov` (`Almaty R16`, featured Prediction `#1`): `(5) Karen Khachanov` actually plays `Tomas Machac` on Center Court in Almaty on Thu Oct 22.
  - `Tomas Machac vs Lorenzo Musetti` (`Brussels R16`, featured Prediction `#2`): Tomas Machac is in **Almaty** playing Khachanov, while Lorenzo Musetti is in **Lyon** quarter-finals (having beaten Moise Kouame on Oct 21).
  - `Raphael Collignon vs Tallon Griekspoor` (`Brussels R16`, featured Prediction `#3`): Collignon actually plays `#2 seed Jiri Lehecka` on Centre Court in Brussels on Thu Oct 22.
  - `Martin Landaluce vs Andrey Rublev` (`Lyon R16`, featured Prediction `#5`): Landaluce was eliminated in Lyon R32 on Oct 21 by Stan Wawrinka (`6-3, 6-7(2), 7-6(5)`).
  - `Damir Dzumhur vs Tommy Paul` (`Lyon R16`, featured Prediction `#6`): Dzumhur is in **Brussels** playing `(6) Zizou Bergs`, while Tommy Paul is in **Lyon** quarter-finals playing `Corentin Moutet`.
- **Portal remediation:** `/portal/` originates lines exclusively for the 16 live ATP & WTA ties verified directly against `atptour.com` (`Almaty`, `Brussels`, `Lyon`) and `wtatennis.com` (`Ningbo`, `Osaka`).

### `PA-02` (CRITICAL — Hallucinated Withdrawal & Replacement): `/slate/` Fabricated a Stephen Bunting Withdrawal in PDC European Championship Round 1
- **Files affected:** `data/slate/matches.json` (`pdc-32330`), `data/slate/predictions.json` (Prediction `#9`), `data/slate/repo_audit.json` (`A-01`).
- **Evidence:** `/slate/` replaced `Stephen Bunting` with `Ritchie Edhouse` against `Danny Noppert` and asserted in Prediction `#9`: *"Official PDC preview confirmation on October 21 replaced withdrawn Stephen Bunting with #33 Ritchie Edhouse"*. Official PDC articles (`https://www.pdc.tv/news/2026/october/18/2026-machineseeker-european-championship-draw`, `https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-of-play`, and `https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview`) plus live `olbg.com/betting-tips/Darts/15` (`event_id=32330`) confirm `(5) Danny Noppert v (28) Stephen Bunting` on Thursday Oct 22 in Dortmund, with zero withdrawal.
- **Portal remediation:** `/portal/` restores `(5) Danny Noppert v (28) Stephen Bunting` with direct `pdc.tv` draw/schedule links and flags `/slate/` `pdc-32330` on `portal/flagged.html`.

### `PA-03` (CRITICAL — Completed Tournament Listed as Active): `/verified/`, `/board/`, and `/hub/` List PGA Tour `Bank of Utah Championship` (`Oct 1–4`) on `2026-10-22`
- **Files affected:** `data/verified/matches.json` (`golf-utah-2026`), `data/board/matches.json` (`golf-utah-2026`), `data/hub/matches.json` (`golf-utah-2026`).
- **Evidence:** Direct fetch of `https://www.pgatour.com/tournaments/2026/bank-of-utah-championship/R2026554` confirms the tournament was completed **October 1–4, 2026** at Black Desert Resort and won by **Austin Smotherman (-26, $1,080,000)**. All three layers simultaneously missed OLBG's actual live Oct 22–25 Golf events: PGA Tour `Butterfield Bermuda Championship` (`R2026528`, OLBG `101904`) and PGA Tour Champions `Stifel Charity Classic` (`S2026625`, OLBG `101903`), and misstated DP World Tour `Genesis Championship` as a `120-Player Strokeplay Field` instead of `126` (`90 DPWT + 36 KPGA` per `europeantour.com`).
- **Portal remediation:** `/portal/` removes the completed Utah event, originates tournament matchups across live `Butterfield Bermuda Championship` and `Genesis Championship`, and flags full-field strokeplay outrights honestly.

### `PA-04` (HIGH — Next-Week Tournament Misattribution): `/hub/` Labels Live Oct 22–23 Lyon, Ningbo & Osaka Tennis Matches as `Basel`, `Vienna`, and `Guangzhou`
- **Files affected:** `data/hub/matches.json` (`atp-902126`, `atp-902133`, `wta-902072`, `wta-902107`), `data/hub/predictions.json` (`Corentin Moutet v Tommy Paul`).
- **Evidence:** Official `https://www.atptour.com/en/tournaments/basel/328/overview` and `https://www.atptour.com/en/tournaments/vienna-2/337/overview` confirm both `Swiss Indoors Basel` and `Erste Bank Open Vienna` run **26 October – 1 November 2026** (`There is no draw available for this tournament`). `Cobolli vs Wawrinka` and `Moutet vs Paul` are live at `ATP 250 Grand Prix Auvergne-Rhône-Alpes (Lyon)`; `Shnaider vs Eala` is at `WTA 500 BNB Ningbo Open` (`wtafiles.wtatennis.com/pdf/draws/2026/2092/MDS.pdf`); and `Gibson vs Krueger` is at `WTA 250 Kinoshita Group Japan Open (Osaka)`.

### `PA-05` (HIGH — Incomplete 17-Sport Origination Across Every Prior Layer): Zero Existing Repo Layers Originate Lines Across All 17 Eligible OLBG Sports
- **Files affected:** `data/verified/matches.json` (`13/17` sports), `data/board/matches.json` (`13/17` sports), `data/hub/matches.json` (`15/17` present, `11/17` lined), `data/slate/matches.json` (`15/17` lined; `gaelic-football` & `volleyball` `0` lined), `data/matches.json` (`5/17` sports).
- **Portal remediation:** `/portal/` is the first layer in the repository to publish verified fixtures and originated multi-market lines across **all 17 eligible OLBG sports** while leaving unconfirmed sub-slates blank (`—`) and flagged.

### `PA-06` (HIGH — Non-Standard Quarter-Point Asian Handicaps Engineered for `-250` Band): `/verified/` & `/board/` Use Synthetic `.25`/`.75` Spreads in Rugby Union & Basketball
- **Files affected:** `data/verified/predictions.json` (`11/14` picks), `data/board/predictions.json` (`11/35` picks), `data/verified/band.json`.
- **Evidence:** Picks such as `DHL Stormers -0.75 @ -250`, `Glasgow Warriors -1.25 @ -244`, `Edinburgh Rugby -1.75 @ -238`, `Stade Toulousain -3.25 @ -238`, and `Panathinaikos -5.75 @ -244` solve normal CDFs for synthetic quarter-point lines not dealt in standard basketball or rugby handicap markets.
- **Portal remediation:** `/portal/` originates strictly standard half-point (`.5`) spreads, set/frame/leg handicaps (`±1.5`, `±2.5`), and puck/run lines (`±1.5`), never synthetic `.25`/`.75` lines.

### `PA-07` (HIGH — Root Layer Null Sources & Completed Oct 21 Matches Still `scheduled`): `data/matches.json` Has 47/47 `source_url: null`
- **Files affected:** `data/matches.json` (all 47 rows).
- **Evidence:** Every row in `data/matches.json` carries `"source_url": null`, `19` rows carry `"date": null`, and completed `2026-10-21` NBA/NHL/EHF fixtures (`Timberwolves 131-106 Heat`, `Lakers 127-105 Warriors`, `Rockets 128-110 Mavericks`, etc.) remain `"status": "scheduled"`.

### `PA-08` (MEDIUM — Non-Governing-Body Community Wiki Citations): `/slate/` Cites `liquipedia.net` Across All 8 Esports Rows
- **Files affected:** `data/slate/matches.json` (`lol-w26-r1-1..8`), `data/slate/sources.json`.
- **Evidence:** All 8 LoL Worlds 2026 Swiss Stage Round 1 rows in `/slate/` link to fan-edited `https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage`. Official Riot Esports URLs (`https://lolesports.com/en-US/live/worlds/111215067738057254` and `https://lolesports.com/en-US/news/worlds-2026-primer`) confirm the exact same 8 Bo1 matchups in Allen, Texas.

### `PA-09` (MEDIUM — Contradictory F1 Gap Flag & Round-Count Off-by-One): `VF-17` Claims No F1 Race Until Las Vegas; `/slate/` Misstates Completed Rounds as `18`
- **Files affected:** `data/verified/flagged.json` (`VF-17`), `data/board/flagged.json` (`VF-17`), `data/slate/predictions.json` (Prediction `#34`).
- **Evidence:** `https://www.formula1.com/en/results/2026/races` confirms **17 Grands Prix** have been completed through Singapore (Oct 11, won by Max Verstappen), and **Round 18 is the United States Grand Prix in Austin on Sunday Oct 25, 2026** (`races/1297/united-states`, OLBG `913`). `VF-17` falsely asserts a 4-week gap to Las Vegas, while `/slate/` Prediction `#34` writes *"Oscar Piastri (138 points, zero wins across 18 rounds)"* (17 rounds completed, not 18).

### `PA-10` (MEDIUM — Taxonomy & OLBG Sport-ID Mis-Mappings): `REPO_REVIEW.md` Denies Live `/Hurling/26` Hub; Multiple Layers Swap OLBG IDs
- **Files affected:** `REPO_REVIEW.md`, `data/survey/sports.json`, `data/verified/sports.json`, `data/board/sports.json`.
- **Evidence:** Live fetch of `https://www.olbg.com/betting-tips/Hurling/26` on `2026-10-22` returned active tips (`Ballyhale Shamrocks v Tullaroan` `714`, `All Ireland Hurling Championship 2027` `675`), and `/UFC_MMA/27`, `/Specials/6`, `/Specials/24` returned HTTP 200 (all excluded per user rules). Upstream sport files also misstated IDs (`Basketball=4` not `19`, `Golf=5` not `4`, `Ice_Hockey=13` not `18`, `Aussie_Rules=22` not `27`, `eSports=23` not `28`, `Greyhounds=28` not `5`).

### `PA-11` (MEDIUM — Stale EuroLeague `GP=6` Records & Stale NBA Opening-Week Records): `HTA` & `VIR` Completed Round 7 on Oct 21 (`90–81`)
- **Files affected:** `data/verified/inputs.json`, `data/board/inputs.json`, `data/slate/inputs.json`.
- **Evidence:** Live fetch of `https://www.euroleaguebasketball.net/en/euroleague/standings/` (`2026-10-22`) shows `Hapoel IBI Tel Aviv` at `7 GP, 5-2, 630 PF / 601 PA (+29)` and `Virtus Bologna` at `7 GP, 4-3, 606 PF / 608 PA (-2)` after Wednesday Oct 21's Round 7 opener, while all other 18 EuroLeague clubs stand at `6 GP`. Similarly, NBA Oct 21 results (`Rockets 128-110 Mavericks`, `Timberwolves 131-106 Heat`, `Lakers 127-105 Warriors`, `Trail Blazers 124-83 Suns`, `Clippers 121-96 Kings`) updated those 10 teams to `1-0` / `0-1` entering Oct 22–23.

### `PA-12` (LOW — ATP Ranking Prose vs Structured Field Contradictions & NHL Shootout-Goal Convention): Documented & Reconciled
- **Files affected:** `data/slate/predictions.json` (`Lorenzo Musetti` / `Andrey Rublev` rank fields), `data/desk/nhl_teams.json` (`nhl.com/standings` shootout-goal GF/GA vs `api.nhle.com/stats/rest/en/team/summary` regulation+OT GF/GA).
- **Portal remediation:** `/portal/` uses `api.nhle.com/stats/rest/en/team/summary` regulation+OT `goalsFor`/`goalsAgainst` uniformly across all 32 NHL clubs and programmatically cross-checks every number in prediction prose against structured match/input records on build.
