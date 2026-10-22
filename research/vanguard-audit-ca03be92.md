# Vanguard desk — capture, origination and repo review (session `arena/ca03be92-olbg2`)

**Capture window:** 2026-10-22 20:50Z → 22:00Z. **Published at:** `/vanguard/`.
**Pipeline:** `scripts/vanguard_seed.py` → `vanguard_model.py` → `vanguard_build.py`; gate `vanguard_verify.py`.

## 1. Why another layer

`/current/` (PR #119–122) and `/pulse/` (PR #117) were both captured earlier on 22 October. This session
re-read the official feeds after 20:50Z, when the NHL, EuroLeague, ATP, WST, EHF, URC and LoL slates had
moved on, and published only what those feeds returned at that time. Rows from earlier layers are not copied.

## 2. What was read first hand

| Sport | Official endpoints | What it returned |
|---|---|---|
| Ice hockey | `api-web.nhle.com/v1/score/2026-10-22`, `…/2026-10-23`, `…/2026-10-24`, `api.nhle.com/stats/rest/en/team/summary` | 12 games on 22 Oct, 2 on 23 Oct, all 32 club summaries (GP/W/L/OTL/GF/GA) |
| Basketball | `euroleaguebasketball.net/…/game-center/`, `…/standings/` | Round 7: six games already played on 22 Oct, three still to come on 23 Oct; full 20-club table |
| Baseball | `statsapi.mlb.com/api/v1/schedule` (22–31 Oct), `…/standings`, `…/people?personIds=…` | World Series games 1–4, probable pitchers, 2026 regular-season records, pitcher lines |
| Rugby union | `stats.unitedrugby.com/match-centre/2026-27/4` and `/table/2026-27` | All eight Round 4 fixtures with match ids, plus the full 16-club table |
| Snooker | `wst.tv/matches/`, `wst.tv/rankings/…` | Round 3 results, four quarter-finals on 23 Oct, full prize-money rankings |
| Tennis | `atptour.com/en/scores/current/{almaty/9410,brussels/7485,lyon/496}/daily-schedule` and `/rankings/singles` | Twelve quarter-finals on 23 Oct with times, plus singles ranking points |
| Handball | `ehfcl.eurohandball.com/men/2026-27/standings/` | Six group tables and the 28–29 October fixtures with match ids |
| Rugby league | `nrl.com/draw/?competition=131&round=2&season=2026` and each match centre | Five Round 2 fixtures, venues, kick-offs, team lists and Round 1 scores |
| Gaelic football | `munster.gaa.ie/fixtures/events-calendar/` and the county-final event pages | Three finals on 25 Oct with venues, throw-in times and referees |
| Volleyball | `legavolley.it/calendario/?idCampionato=999` and `/classifica/?IdCampionato=999` | Round 1 results with points, Round 2 fixtures on 25 Oct, rosters |
| Aussie rules | `afl.com.au/aflw` ladder and the Round 11 preview | 18-team ladder after Round 10, nine Round 11 fixtures with venues and times |
| Darts | `pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/` | The 32-player draw bracket with seed numbers and the Friday schedule |
| eSports | `lolesports.com/en-US/gpr/2026/current` and the Swiss-stage schedule | 58-team Global Power Scores (updated 19 Oct) and the 23–24 Oct Bo1 pairings |
| Cricket | `icc-cricket.com` ODI and women's ODI team rankings; ICC rankings news of 21 Oct | Team ratings for Afghanistan, Zimbabwe, India Women and Zimbabwe Women |
| Motor racing | `formula1.com/en/results/2026/drivers` and `/races` | 23-driver standings and the 18 completed rounds |
| Golf | `pgatour.com/…/stifel-charity-classic/S2026625/overview` | Dates, venue, purse; Charles Schwab Cup money for the named contenders |
| Greyhounds | `gbgb.org.uk/category-one-glory-beckons-in-coral-100-champion-stakes-final/` | Five remaining finalists, three semi-final winning times, the Newinn Jolly withdrawal |

## 3. Origination and the gate

Six model families, all documented on `/vanguard/methodology.html`: Poisson score grids for ice hockey,
baseball and handball; normal margins for basketball and rugby union; logistic strength models for the
eight ranking-based sports; direct share models for the three outright markets. No bookmaker price was read.

The high-confidence gate is `0.7000 ≤ p ≤ 5/7` and fair American `−250 … +10000`. Because that window is only
1.43 percentage points wide, each score-based fixture carries an alternate-line grid and the four lines
nearest 70.71% are kept per market family. Result on this capture: **91 fixtures, 512 originated prices,
85 in-band selections, 21 written predictions, 19 flags.**

## 4. Honest limits (all published on `/vanguard/flagged.html`)

* Gaelic football: three fixtures, no prices. No official numeric rating exists for club sides, so the row
  is blank rather than guessed.
* Baseball (2), snooker (3), golf (1), greyhounds (1), motor racing (1) and cricket (2) publish fewer fixtures
  than the daily five because that is the entire verified slate in the window.
* Only basketball, handball, ice hockey, rugby union and darts produced in-band selections. The other twelve
  sports are listed on the flagged page with the count they published and the reason.
* NBA prices use **preseason** net ratings from NBA.com's Week 1 power rankings; every affected row is flagged.
* Rugby league uses Round 1 score differentials; darts treats unseeded players as seed 40.

## 5. Repo review performed alongside the capture

Read line by line against the merged tree (`bf9ba93` → `0a5268d`): `/current/`, `/pulse/`, `/update/`,
`/atlas/`, `/canon/`, `/beacon/`, `/final/`, `/verified/`, `data/*` and every builder's output.

1. **`/current/` published 17 fixtures dated 2026-10-22 as upcoming at 13:24Z.** By 21:00Z every one of those
   EuroLeague, EHF and WST ties had started or finished (the EHF page shows Melsungen 28–26 Plock, Szeged
   33–33 GOG, Sporting 42–40 Kristianstad, Barça 40–34 Montpellier, Kolstad 32–35 Magdeburg). The layer
   remains correct as a pre-match snapshot, but it is **stale against the current clock**; flagged as VA-01.
2. **`/atlas/predictions.json` labels 41 picks "high" while its own `featured_count` is 6** and its rule text
   admits the remainder are priced shorter than −250. A reader who sorts by the confidence column sees 41
   high-confidence picks, 35 of which are outside the brief's band. Flagged VA-02; not edited (another
   session's scope).
3. **`/beacon/` publishes a darts pick on `Ross Smith to Win` with no opponent named** in the selection, and
   `Tonga -28.5` in rugby league, a handicap for which I could not find a matching official line. VA-03.
4. **`/pulse/` and `/update/` both price fixtures that had already started** by their own capture time
   (Pulse's NHL 22 Oct set, Update's EuroLeague Round 7 set). Their methodology pages disclose snapshot
   timing, so this is a freshness caveat rather than a data error. VA-04.
5. **No layer, including this one, has a complete 5-per-sport daily slate.** That is a structural property of
   a −250…+10000 / ≥70% gate applied to a 17-sport capture, not a missing row: the gate is narrower than the
   spread between adjacent handicap lines in most sports. Recorded as VA-05 and reported on every desk's
   flagged page rather than papered over.

## 6. Verification run

`python3 scripts/vanguard_seed.py && python3 scripts/vanguard_model.py && python3 scripts/vanguard_build.py
&& python3 scripts/vanguard_verify.py` → 28 pages, 91 fixtures, 512 prices, 21 predictions, ALL CHECKS PASS.
`python3 -m unittest tests.test_vanguard_ca03be92` → 11 tests OK.
