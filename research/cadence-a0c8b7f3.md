# Cadence Desk Research & Line-by-Line Audit (`arena/a0c8b7f3-olbg2`)

- **Capture Date / Window**: `2026-10-23T19:00Z–19:50Z` (UTC)
- **Session / Branch**: `arena/a0c8b7f3-olbg2`
- **Published Dashboard Scope**: `/cadence/` (`https://buffedlizard55-lab.github.io/OLBG2/cadence/`)
- **Data & Pipeline Scope**: `data/cadence/`, `scripts/cadence_*.py`, `tests/test_cadence_a0c8b7f3.py`

---

## 1. OLBG.com Reverse-Engineering Findings

### 1.1 Canonical 15-Sport Taxonomy & `sportId` Routing

Direct inspection of `https://www.olbg.com/betting-tips` confirms that OLBG routes sport hubs via `/betting-tips/{Slug}/{sportId}` and exposes **16 canonical `sportId` routes covering all 15 mandated sports** (Gaelic Sports is split across Gaelic Football `25` and Hurling `26`):

| Mandated Sport | Cadence Slug | OLBG `sportId`(s) | Canonical OLBG Hub Route(s) | Primary Official Governing-Body Sources Used |
| --- | --- | --- | --- | --- |
| Golf | `golf` | `5` | `https://www.olbg.com/betting-tips/Golf/5` | `pgatour.com`, `europeantour.com` (DP World Tour) |
| Volleyball | `volleyball` | `21` | `https://www.olbg.com/betting-tips/Volleyball/21` | `legavolley.it`, `volleyball-bundesliga.de` |
| Rugby Union | `rugby-union` | `9` | `https://www.olbg.com/betting-tips/Rugby_Union/9` | `premrugby.com`, `stats.unitedrugby.com` |
| Cricket | `cricket` | `7` | `https://www.olbg.com/betting-tips/Cricket/7` | `cricket.com.au` (international & One-Day Cup) |
| Snooker | `snooker` | `8` | `https://www.olbg.com/betting-tips/Snooker/8` | `wst.tv` (World Snooker Tour) |
| Darts | `darts` | `15` | `https://www.olbg.com/betting-tips/Darts/15` | `pdc.tv` (Professional Darts Corporation) |
| Baseball | `baseball` | `12` | `https://www.olbg.com/betting-tips/Baseball/12` | `statsapi.mlb.com` (MLB Official StatsAPI) |
| Gaelic Sports | `gaelic-sports` | `25`, `26` | `https://www.olbg.com/betting-tips/Gaelic_Football/25`, `https://www.olbg.com/betting-tips/Hurling/26` | `gaa.ie`, `munster.gaa.ie`, `gaacork.ie`, `waterfordgaa.ie`, `limerickgaa.ie`, `kerrygaa.ie` |
| Greyhounds | `greyhounds` | `28` | `https://www.olbg.com/betting-tips/Greyhounds/28` | `gbgb.org.uk` (Greyhound Board of Great Britain) |
| Tennis | `tennis` | `3` | `https://www.olbg.com/betting-tips/Tennis/3` | `atptour.com`, `protennislive.com` |
| Motor Racing | `motor-racing` | `14` | `https://www.olbg.com/betting-tips/Motor_Racing/14` | `formula1.com` (FIA Formula One World Championship) |
| Handball | `handball` | `20` | `https://www.olbg.com/betting-tips/Handball/20` | `lnh.fr` (LNH Daikin StarLigue & EHF CL tracker) |
| Ice Hockey | `ice-hockey` | `13` | `https://www.olbg.com/betting-tips/Ice_Hockey/13` | `api-web.nhle.com` (NHL Official Web API) |
| Basketball | `basketball` | `4` | `https://www.olbg.com/betting-tips/Basketball/4` | `nba.com`, `ak-static.cms.nba.com` (Official Referee Injury PDF), `euroleaguebasketball.net` |
| Rugby League | `rugby-league` | `10` | `https://www.olbg.com/betting-tips/Rugby_League/10` | `nrl.com` (RLWC 2026 Official Draw & Results, `competition=131`) |

Out-of-scope OLBG hubs (`Football/1`, `Horse_Racing/2`, `Boxing/6`, `American_Football/11`, `Aussie_Rules/18`, `UFC/23`, `Esports/27`, etc.) are strictly excluded from all `/cadence/` tables, lines, and predictions.

### 1.2 Event-Page Architecture & Four Verified OLBG Frontend Defects

Inspecting direct OLBG `?event_id=` pages (`32335`, `902140`, `199984`, `536036`, `32384`, `902163`) revealed four concrete platform defects on `olbg.com`:

1. **US-IP Geo-Filtered Hub Lists (`No tips found.`)**: Requests from US egress IPs to `/betting-tips/{Sport}/{id}` render the navigation chrome and an empty `No tips found.` container once UK bookmaker affiliate feeds are suppressed, while direct `?event_id={id}` URLs continue to serve full tipster markets, comment bodies, and consensus counts.
2. **`Most Popular Tip` String-Concatenation Bug**: In the `Most Popular Tip` summary pill on `?event_id=` pages, OLBG's frontend template concatenates tip counts as strings instead of summing integers before computing `tips / total_tips`:
   - `event_id=902140` (`MTL Canadiens @ CHI Blackhawks`): `4` tips on Canadiens + `2` elsewhere -> renders `4 / 042 | 95%` (while the breakdown table directly below correctly states `4/42 tips`).
   - `event_id=199984` (`TB Rays @ MIL Brewers` World Series Game 1): renders `6 / 062 | 97%`.
   - `event_id=536036` (`IND Pacers @ ORL Magic`): renders `9 / 090 | 100%`.
   - `event_id=902163` (`PNG Kumuls v Samoa` RLWC): renders `2 / 021 | 95%`.
3. **Blank `WIN @` Odds Cells Under Geo-IP Bookmaker Suppression**: On `event_id=32384` (`Stephen Bunting v Kim Huybrechts`) and `event_id=902163` (`Papua New Guinea v Samoa`), selection rows render `WIN @` with an empty odds string because UK affiliate odds widgets return null to US visitors.
4. **False `Expired` Badges & US-Eastern Clock Drift**: Unstarted Saturday fixtures (`event_id=32384` Darts R2 on Oct 24 and `event_id=902163` RLWC R2 on Oct 24) display `Expired` badges alongside US-Eastern local timestamps (`03:00` EDT for `07:00 UTC`), creating false expiry states ahead of kickoff.

---

## 2. Official Governing-Body Verification Breakthroughs

Several earlier sessions marked sports or injury feeds unreachable due to testing legacy or client-rendered endpoints. During `CD2`/`CD3` we verified working first-hand official endpoints across **all 15 sports**:

- **NBA Schedule, Standings & Official Referee Injury Report**: While `cdn.nba.com` and `stats.nba.com` block/500, `https://www.nba.com/games?date=2026-10-23`, `https://www.nba.com/standings`, and the official NBA Referee Injury PDF `https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf` (linked from `official.nba.com/nba-injury-report-2026-27-season/`) return complete server-rendered records, stat leaders, and player-level `Out`/`Questionable`/`Probable` designations for tonight's 12 NBA games.
- **PDC Darts (`pdc.tv`)**: Direct `fetch_page` hits CookieYes vendor tables, whereas `pdc.tv/news/2026/october/...` indexed pages confirm Luke Humphries' official withdrawal from Dortmund with gastroenteritis (`2026-10-22`), Kim Huybrechts' `6-1` (`103.81` avg) replacement win over Ryan Searle, Luke Woodhouse's nine-darter in beating Dirk van Duijvenbode `6-3`, Gian van Veen's `120.24` European Tour record average and `6-4` R1 win over Andrew Gilding, and all Saturday Oct 24 Round 2 ties.
- **World Snooker Tour (`wst.tv`)**: Contrary to `REPO_REVIEW.md` `F-12` (which reported HTTP 500 on WST rankings), `https://www.wst.tv/rankings/` and `https://www.wst.tv/matches/` return HTTP 200 with full 2026/27 Johnstone's Paint World Rankings (`#1 Zhao Xintong £1,265,550`, `#2 Wu Yize £815,800`, `#3 Judd Trump £799,850`, `#4 Mark Selby £793,350`, `#8 Mark Williams £747,400`, `#9 Kyren Wilson £716,800`), Northern Ireland Open SF1 (`Kyren Wilson vs Sam Craigie`), and International Championship Nanjing Round 2 match centres (`87883228...`, `77ee26cc...`, `a7bc5bdd...`).
- **Premiership Rugby & RLWC Parameter Traps**: `premrugby.com/fixtures-results` returns an empty filter shell when `?competition=gallagher-prem&round=4` is appended directly, but bare `https://www.premrugby.com/fixtures-results` and `https://www.premrugby.com/standings` return all Round 4 fixtures (`Leicester v Northampton`, `Bristol v Exeter`, `Harlequins v Saracens`) and the full 10-club table. Similarly, `nrl.com/draw/?competition=116` is State of Origin, whereas `https://www.nrl.com/draw/?competition=131&round=2&season=2026` (and `round=3`) returns the official 2026 Men's Rugby League World Cup draw and results.
- **GBGB Greyhounds (`gbgb.org.uk`) & GAA County Boards**: `gbgb.org.uk` race reports and the 2026 Category One schedule confirm Saturday Oct 24's Category One double-header at Dunstall Park (`Arena Racing Company Scurry Gold Cup Final 270m` and `Premier Greyhound Racing Oaks Final 480m`) plus Trainer of the Year standings (`Maxine Locke 1,016 pts`, `Paul Young 850 pts`, `Mark Wallis 809 pts`) and `Newinn Jolly`'s welfare withdrawal (urine infection) at Romford. Official GAA portals (`gaa.ie`, `munster.gaa.ie`, `gaacork.ie`, `waterfordgaa.ie`, `limerickgaa.ie`, `kerrygaa.ie`) confirm Saturday's `Ireland v Scotland` Hurling-Shinty & Camogie-Shinty Internationals and Sunday's Cork, Kerry, Waterford, and Limerick County Finals.

---

## 3. Summary of Line-by-Line Repository Irregularities

Full structured entries with line citations and manual-review links are stored in `data/cadence/repo_audit.json` and rendered on `/cadence/audit.html` and `/cadence/flagged.html`. Key repo-wide findings:

1. **Unresolved Git Merge Conflict Markers in `COORDINATION.md`**: Lines `3216`, `3307`, `3437`, `3549`, `3609`, and `3628` contain stray `=======` and `>>>>>>>` markers left by earlier concurrent sessions.
2. **43 Out-of-Scope Sport Pages Across 22 Desk Trees**: Prior desks (`atlas`, `beacon`, `board`, `canon`, `command`, `current`, `daily`, `daily-audit`, `daily-picks`, `portal`, `site`, `slate`, `sports`, `survey`, `update`, `vanguard`, `verified`) published `aussie-rules.html` and `esports.html` despite neither sport being in the 15-sport scope.
3. **204+ Prediction Items Violating the Forbidden-Word Constraint (`model` / `verified`)**: Across 15 `data/**/predictions*.json` files — including `100%` of `data/predictions.json` (`6/6`, e.g. line 13) and `100%` of `data/portal/predictions.json` (`34/34`, e.g. line 36), `70/165` in `data/update/predictions.json` (e.g. line 18), `26/41` in `data/atlas/predictions.json`, and `24/45` in `data/daily/predictions.json` — prose uses forbidden words `model` or `verified`.
4. **163 HTML Files With Table Rows Missing Official `https://` Source Links**: Across root and prior sub-desks, 163 HTML files contain `<tbody><tr>` data rows without an external official source URL, violating the row-level verification requirement.
5. **Stale & Already-Started Matches Published as Upcoming Picks**:
   - Root `data/matches.json` (`2026-10-22T07:41:28Z`, 5 sports) and `data/predictions.json` (`2026-10-22`, 6 completed Oct 21–22 NHL/EHF matches; e.g. `Barça v Montpellier` at line 78 already finished `40-34`).
   - `site/data/lines.json` (`2026-10-21T05:55:00Z`) covers only 2 of 15 sports (`Ice hockey`, `Basketball`).
   - `data/signal/matches.json` (`2026-10-23`) retains 23 pre-`19:30Z` live/completed matches marked `"upcoming"` (e.g. `prem-294923` `Gloucester v Bath` line 3274, `wst-19048b0d` `Gilbert v M.Williams` line 3945) and leaves 5 of 15 sports with zero predictions (`Volleyball`, `Darts`, `Gaelic Sports`, `Greyhounds`, plus `0` Volleyball rows).
   - `data/covered/matches.json` covers only 7 of 15 sports (`23` rows) and `data/covered/predictions.json` contains `0` predictions.
6. **Outdated Factual Claims in `REPO_REVIEW.md`**:
   - `REPO_REVIEW.md:54` (`F-12`) states WST rankings returned HTTP 500; `wst.tv/rankings/` is live (HTTP 200) and confirms `#1 Zhao Xintong (£1,265,550)`.
   - `REPO_REVIEW.md:63` (`F-03`) excluded `Greyhounds (id 28)` and `Gaelic Football (id 25)` despite both being explicitly required.
   - `REPO_REVIEW.md:65` (`F-05`) claimed OLBG has no `Hurling` node despite `https://www.olbg.com/betting-tips/Hurling/26` being live in OLBG's main sports navigation.
