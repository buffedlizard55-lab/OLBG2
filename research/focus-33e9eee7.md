# Focus desk research note — session 33e9eee7 (2026-10-23)

## OLBG reverse-engineering (re-read 2026-10-23)
- `https://www.olbg.com/betting-tips` lists events across 20+ sports with market labels and tipster counts (e.g. Darts "Win Match 2-way", Baseball "Money Line"). OLBG publishes tipster selections, **not prices** — every price on /focus/ is originated here.
- Sport hub pattern: `https://www.olbg.com/betting-tips/{Sport}/{id}` — confirmed live for Ice Hockey (`/Ice_Hockey/13`, NHL + Danish Metal Ligaen + Germany Eishockey Liga + Finland SM Liiga + Austria EHL + Switzerland NLA, markets Money Line / Puck Line / Game Totals), Darts (event_id 32335 etc. from the tips feed), Baseball (`/Baseball/MLB/MLB/.../12?event_id=160789`, TB Rays @ MIL Brewers, Money Line).
- Scope applied: exactly the 15 brief sports. Aussie Rules and Esports (in older 17-sport layers) are excluded here.

## Fresh official captures (2026-10-23, this session)
| Sport | Official source read | What was taken |
|---|---|---|
| Ice Hockey | https://api-web.nhle.com/v1/score/2026-10-25 and /v1/standings/2026-10-23 | 5 NHL fixtures on 25–26 Oct, records, team leaders (goals/assists/wins) |
| Baseball | https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-24&endDate=2026-10-30 and /v1/standings?leagueId=103,104&season=2026 | World Series Games 2–6 (TB vs MIL, venues, if-necessary flags); Tampa Bay 98-64, RS 736 / RA 650 re-read |
| Tennis | https://www.atptour.com/en/scores/current | Quarter-finals live on 23 Oct — semi pairings not yet set, so tennis is blank/flagged |
| Cricket | https://www.icc-cricket.com/fixtures | Returned 404 on 2026-10-23 — cricket blank/flagged, not invented |

Other priced rows (Rugby Union URC, Handball EHF, Volleyball SuperLega, Rugby League RLWC, Basketball NBA/EuroLeague proxy, Gaelic finals, F1 outright) use the 2026-10-22 official capture stored in `data/vanguard/inputs.json`; each row's `basis` and `source_url` state this and link the governing body (URC, eurohandball.com, legavolley.it, nrl.com, nba.com, munster.gaa.ie, formula1.com).

## Verification performed
- `python3 scripts/focus_verify.py` → ALL CHECKS PASS (price recompute, high gate, ≥30-word unique predictions, banned public-prose words absent, https source per row, internal links, KPI vs data).
- `python3 -m unittest tests.test_focus_33e9eee7` → 7 tests OK.
- Full repo suite run at integration (see COORDINATION.md).

## Irregularities (all on /focus/flagged.html)
1. Five-per-sport prediction aim met in **no** sport: the −250…+10000 band only admits 70.0–71.4% straight prices, so only 11 high predictions (Handball 4, Rugby Union 5, Ice Hockey 2) cleared it. Flagged per sport (FO-short-*).
2. Tennis, Darts, Snooker, Golf, Greyhounds, Cricket: no priced fixture — official pairing/field/timed data not captured on 2026-10-23. Blank, flagged.
3. Gaelic Sports (3 finals): official fixture confirmed, no numeric club strength published — blank.
4. Basketball NBA rows use preseason net rating only; handicap/total not originated for them (FO-net-*).
5. MLB Games 5–6 are "if necessary" per MLB — they may not be played.
6. NHL strength inputs (GF/GA) are the 2026-10-22 capture; fixtures/records/leaders are 2026-10-23. Disclosed in each row's basis.
7. No injury information is claimed: no governing-body page read for these rows stated an injury, so predictions make no injury claim rather than inventing one.
