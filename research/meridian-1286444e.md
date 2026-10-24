# Meridian Desk (`arena/1286444e-olbg2`) — 2026-10-24 OLBG.com Reverse-Engineering, Official Verification & Line-by-Line Repository Audit

- **Capture date & window:** `2026-10-24 17:40–18:10 UTC`
- **Branch:** `arena/1286444e-olbg2`
- **Published dashboard:** `/meridian/` (`meridian/index.html` + 27 subpages)
- **Covered OLBG sports (strict 15-sport allowlist):** Golf, Volleyball, Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball, Rugby League.

---

## 1. Reverse Engineering OLBG.com (Live 2026-10-24 Inspection)

All **16 live OLBG hub endpoints** mapping to the 15 in-scope sports (including both `/betting-tips/Gaelic_Football/25` and `/betting-tips/Hurling/26` under **Gaelic Sports**), plus `/betting-tips` and representative event-detail endpoints (`?event_id=...`), were fetched first-hand on `2026-10-24`:

1. **Hub URL taxonomy & dual-code Gaelic mapping:**
   - OLBG assigns numeric sport IDs in `/betting-tips/<Sport_Slug>/<id>`: Tennis (`3`), Basketball (`4`), Golf (`5`), Cricket (`7`), Snooker (`8`), Rugby Union (`9`), Rugby League (`10`), Baseball (`12`), Ice Hockey (`13`), Motor Racing (`14`), Darts (`15`), Handball (`20`), Volleyball (`21`), Gaelic Football (`25`), Hurling (`26`), Greyhounds (`28`).
   - Out-of-scope OLBG hubs (`Football/1`, `Horse_Racing/2`, `American_Football/11`, `Boxing/16`, `Aussie_Rules/22`, `UFC_MMA/27`, `eSports/32`) were excluded completely (`0` rows).
2. **Geo-IP Viewer Timezone Localization (EDT `UTC-4` vs Venue/UTC):**
   - Server-rendered OLBG cards localize clock strings to the requester's geo-IP timezone without displaying a timezone suffix. From our San Francisco (`US`) environment, OLBG rendered `US/Eastern` (`EDT`, `UTC-4`) strings: e.g., `LA Kings @ NJ Devils` (`startTimeUTC: 2026-10-24T19:30:00Z`) rendered as `Today 15:37`; `TB Rays @ MIL Brewers` (`2026-10-25T00:00:00Z`) rendered as `Today 20:00`; `Ballyhale Shamrocks v Tullaroan` (`13:45 GMT` Sunday 25 Oct, after Ireland's 01:00 UTC DST fallback) rendered as `Tomorrow 09:45` (`09:45 EDT` = `13:45 UTC`).
   - Every fixture start time in `/meridian/` is taken from the official governing-body schedule and stored in ISO-8601 UTC (`Z`), while OLBG's raw display string is preserved separately for auditability.
3. **US-IP Bookmaker Quote Suppression & Market Handicap Preservation:**
   - On event-detail pages (`?event_id=160792`, `536115`, `32397`, `714`, `689892`, `689893`), OLBG suppresses UKGC-regulated bookmaker decimal/fractional odds for US visitors, rendering `WIN @` with an empty price slot while still rendering market handicaps (`WIN @ / -1.50 hcap`, `WIN @ / 227.50 hcap`, `WIN @ / 3.50 hcap`), tip counts (`Win Tips / Total`), expert counts, and tipster profit streaks (10-point stake basis).
4. **Denominator Mismatch Bug Observed Live on OLBG (`event_id=32397`):**
   - On `Nathan Aspinall vs Luke Littler` (`/betting-tips/Darts/All_Darts/All_Events/Nathan_Aspinall_vs_Luke_Littler/15?event_id=32397`), the top summary table displays `Luke Littler 14/20 (70%)` and `Nathan Aspinall 6/20 (30%)`, whereas the `Win Match 2-way` market card directly underneath displays `14/19 (74%)` and `6/19 (32%)` — summing to `20/19 (106%)` due to stale cached denominator state when a 20th tip arrived.
5. **Zero-Event & Outright-Only Hubs on 2026-10-24 (`18:10 UTC`):**
   - **Golf (`/betting-tips/Golf/5`):** Returned `"No tips found."` (`0` active events).
   - **Snooker (`/betting-tips/Snooker/8`):** Listed 1 match (`Mark Williams v Jak Jones`, `event_id=9952`), confirmed on `wst.tv/matches/` as `Live Now` at `18:00 UTC` (`Match 62`, BetVictor Northern Ireland Open SF2; Kyren Wilson already won SF1 `6-5` over Sam Craigie). Excluded from pre-match picks.
   - **Rugby League (`/betting-tips/Rugby_League/10`):** Listed `0` match events and `3` 2027 long-range outrights (`State of Origin 2027` `2695857`, `Super League 2027` `2801554`, `NRL 2027` `2801600`).

---

## 2. Line-by-Line Repository Review Findings

Every active and historical desk in the repository was audited line by line against official governing-body feeds on `2026-10-24`:

1. **`MR-AUD-01` (High — Hosted CI Failure on `main`):** Merging `/executive/` (PR #201/`2d2420b`) broke `Validate Pages content` (`run 40118214103`) and `Deploy Pages` (`run 40118214146`) because `tests/test_clarity_2e0fc430.py` rebuilds `scripts/clarity_audit.py` in place, which counts top-level `*/index.html` directories (`45` -> `46`). Running unmodified `clarity_audit.py` + `clarity_build.py` alongside `ledger_report.py` + `ledger_build.py` restores byte-identical determinism and green CI.
2. **`MR-AUD-02` (High — `clarity/` Wrong Greyhound Race & Wrong Start Times):** `data/clarity/predictions.json` attached Premier Greyhound Racing Oaks finalist `Fahrenheit Jess` to `10:14 Dunstall Park` (`event_id=690035`), which OLBG actually lists as a graded race (`Greenwell Gypsy 2/3` vs `Innfield Fifi 1/3`), instead of the true Oaks Final at `9:38 Dunstall Park` (`event_id=689893`). It also recorded `18:00Z` and `18:15Z` instead of `20:18Z` (`9:18 PM BST`) and `20:38Z` (`9:38 PM BST`).
3. **`MR-AUD-03` (High — `clarity/` Golf Picks Published Against an Empty OLBG Hub & Non-OLBG ATP Draws):** `data/clarity/predictions.json` published two Golf predictions (`Yuto Katsuragawa`, `Austin Smotherman`) linking to `https://www.olbg.com/betting-tips/Golf/5` even though that hub returned `"No tips found."` on `2026-10-24`, and published two ATP R1 previews (`Djokovic vs Humbert`, `Alcaraz vs Khachanov`) with blank `olbg_url` while omitting five live WTA matches that ARE listed on `/betting-tips/Tennis/3` (`902207`, `902171`, `902175`, `902173`, `902172`).
4. **`MR-AUD-04` (Medium — `clarity/` European DST Fallback Error on Sunday 25 Oct 2026):** `data/clarity/predictions.json` stored `Stade Rochelais vs Union Bordeaux-Bègles` (`21h05` local on Sunday 25 Oct 2026, `top14.lnr.fr`) as `2026-10-25T19:05:00Z` (`UTC+2` CEST) instead of `2026-10-25T20:05:00Z` (`UTC+1` CET after Europe's 01:00 UTC clock change on 25 Oct 2026).
5. **`MR-AUD-05` (High — `executive/` Eliminated Snooker Player & Single-Event Padding):** `data/executive/predictions.json` published a `medium`-confidence tournament pick on `Sam Craigie v field` after `wst.tv/matches/` already recorded `Kyren Wilson 6-5 Sam Craigie` (eliminated in SF1), split the single United States Grand Prix into 5 separate `"v field"` rows, and carried `0/71` OLBG event URLs and `0/71` injury checks.
6. **`MR-AUD-06` (High — `executive/` Third-Party Media Citations):** `data/executive/predictions.json` cited `racingpost.com` for Greyhounds and `the42.ie` for Gaelic Sports rather than official `gbgb.org.uk` and `gaa.ie` / provincial / county GAA boards.
7. **`MR-AUD-07` (High — `today/` Self-Contradiction on `BUF @ WSH`, Missing 5 NHL Games & Missing `Hurling/26`):** `data/today/flagged.json` stated `Buffalo at Washington` had no OLBG event ID while `data/today/predictions.json` still published `pred-nhl-2026020173` on it; in fact OLBG lists `BUF Sabres @ WAS Capitals` at `event_id=200003`. `today/` also stopped after chunk 2 of the NHL score feed (omitting `CAR@STL`, `TOR@EDM`, `TBL@UTA`, `DET@CGY`, `MIN@SEA`), omitted `/betting-tips/Hurling/26` (`Ballyhale Shamrocks v Tullaroan` `714`), misread EDT Darts times as UTC, originated `0` NHL spreads/totals, and left `13/15` sports with `0` verified fixtures.
8. **`MR-AUD-08` (High — `cadence/` & `zenith/` Non-OLBG Rugby League Fixtures & Null Timestamps):** Both `data/cadence/predictions.json` (`33/33` lacking `olbg_event_url`, `20/33` `start_utc: null`) and `data/zenith/predictions.json` (`13/13` `start_utc: null`) published 5 Rugby League international fixtures absent from `/betting-tips/Rugby_League/10`.
9. **`MR-AUD-09` (High — Legacy Banned Words & Out-of-Scope Sports in Historical `data/**`):** Twelve historical `data/**/predictions*.json` files contain `model*`/`verif*` vocabulary in reader-facing prose, and seven early `data/**` folders retain `aussie-rules` / `esports` rows from pre-15-sport captures (preserved untouched per non-destructive scope rules and audited here).
10. **`MR-AUD-10` (Medium — Root `flagged.html` Missing Source Links on 38 Legacy Rows):** Root `flagged.html` (`2026-10-22` snapshot) contains 38 legacy rows rendering `"no source link recorded"`. In `/meridian/flagged.html` and `/meridian/audit.html`, 100% of rows link directly to official `https://` sources.

---

## 3. First-Hand Official Governing-Body Verification Summary (All 15 Covered Sports)

| Sport | OLBG Hub(s) | OLBG Events | Upcoming Lined | Written Picks | Official Governing-Body Sources Read Live on 2026-10-24 |
|---|---|---:|---:|---:|---|
| Ice Hockey | `Ice_Hockey/13`, `NHL/13` | 17 | 11 | 5 | `api-web.nhle.com/v1/score/2026-10-24`, `api-web.nhle.com/v1/standings/2026-10-24`, `nhl.com/news/nhl-status-report-*` |
| Basketball | `Basketball/4` | 9 | 8 | 5 | `nba.com/games?date=2026-10-24`, `nba.com/standings`, `ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_30PM.pdf` |
| Handball | `Handball/20` | 10 | 8 | 5 | `ehfcl.eurohandball.com/men/2026-27/standings/`, `lnh.fr/daikin-starligue/classement`, `daikin-hbl.de` / `opel-hbl.de` |
| Tennis | `Tennis/3` | 6 | 6 | 5 | `atptour.com/en/scores/current`, `atptour.com/en/news/medvedev-bublik-almaty-2026-saturday`, `wtafiles.wtatennis.com/pdf/draws/2026/{405,1056,2092}/MDS.pdf` |
| Volleyball | `Volleyball/21` | 9 | 5 | 5 | `legavolley.it` (2026/27 SuperLega R1/R2), `plusliga.pl` / `tauronliga.pl/games.html` |
| Gaelic Sports | `Gaelic_Football/25`, `Hurling/26` | 7 | 4 | 4 | `kilkennygaa.ie`, `munster.gaa.ie`, `gaacork.ie`, `galwaygaa.ie`, `maighcuilinn.com`, `limerickgaa.ie` |
| Cricket | `Cricket/7` | 9 | 3 | 3 | `icc-cricket.com`, `bcci.tv`, `nzc.nz`, `cricket.co.za` |
| Darts | `Darts/15` | 6 | 3 | 3 | `pdc.tv/news/2026/october/23/Littler-kickstarts-European-Championship-title-bid-in-style/`, `pdc.tv/news/2026/october/24/2026-machineseeker-european-championship---day-three-latest` |
| Rugby Union | `Rugby_Union/9` | 6 | 2 | 2 | `top14.lnr.fr/calendrier-et-resultats`, `top14.lnr.fr/classement`, `stats.unitedrugby.com`, `quins.co.uk`, `saracens.com`, `wallabies.rugby` |
| Greyhounds | `Greyhounds/28` | 6 | 2 | 2 | `gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/`, `gbgb.org.uk/signet-nayla-chases-oaks-glory-as-hutton-targets-dunstall-park-double/` |
| Baseball | `Baseball/12` | 1 | 1 | 1 | `statsapi.mlb.com/api/v1/schedule`, `statsapi.mlb.com/api/v1/standings`, `statsapi.mlb.com/api/v1/people`, `statsapi.mlb.com/api/v1/teams/{139,158}/roster/40Man` |
| Motor Racing | `Motor_Racing/14` | 1 | 1 | 1 | `formula1.com/en/racing/2026/united-states`, `formula1.com/en/results/2026/drivers` |
| Snooker | `Snooker/8` | 1 | 0 | 0 | `wst.tv/matches/` (`Mark Williams v Jak Jones` live in progress at `18:00 UTC`) |
| Rugby League | `Rugby_League/10` | 3 | 0 | 0 | `superleague.co.uk`, `nrl.com` (only 2027 futures on OLBG; 0 match events) |
| Golf | `Golf/5` | 0 | 0 | 0 | `pgatour.com`, `europeantour.com` (`"No tips found."` on OLBG Golf hub) |
| **Total** | **16 hubs (15 sports)** | **91** | **54** | **41** | **100% first-hand official governing-body provenance** |
