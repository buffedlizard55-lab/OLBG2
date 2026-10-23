# Ledger desk research notes — session `21a0c524`

Scope: `/ledger/**`, `data/ledger/**`, `scripts/ledger_*.py`, `tests/test_ledger_21a0c524.py`, this file, append-only `COORDINATION.md`. Nothing else edited. Captured 2026-10-23 (Friday).

## OLBG reverse engineering (first-hand today)

Read: `https://www.olbg.com/betting-tips`, `https://www.olbg.com/betting-tips/Darts/15`, `https://www.olbg.com/betting-tips/Ice_Hockey/13`, `https://www.olbg.com/sitemap-betting-tips.xml`.

- Sport hub: `/betting-tips/{Sport}/{sportId}`; event: `/betting-tips/{Sport}/{Group}/{Competition}/{Event_Name}/{sportId}?event_id={eventId}`.
- IDs for the 15 requested sports (sitemap, lastmod served as 2026-10-23): Tennis 3, Basketball 4, Golf 5, Cricket 7, Snooker 8, Rugby Union 9, Rugby League 10, Baseball 12, Ice Hockey 13, Motor Racing 14, Darts 15, Handball 20, Volleyball 21, Gaelic Football 25, Greyhounds 28.
- Both hubs fetched served "No tips found" with no event rows (event lists are not in server HTML through this fetch route today). OLBG's own text defines its percentages as tipster popularity and Value Rating vs theoretical probability from tip share — a popularity measure, never used here as a price input.
- Market names taken from OLBG's hub guides: Money Line (2-way incl. OT), Puck Line ±1.5, Totals (commonly 5.5); Darts Win Match / Handicap 2-Way / Total Legs / Total 180s / Tournament Winner.
- Scope irregularity: OLBG separates Gaelic Football (25) and Hurling (26); brief says "Gaelic Sports". Only GAA fixture served was the Shinty-Hurling International — published with flag LG-GA1.

## Sources that worked (all read first-hand today)

NHL Web API score (23+24 Oct) and NHL Stats team summary (31 teams complete GF/GA, Calgary truncated); MLB Stats API World Series schedule (Games 1–5) + AL/NL standings (Rays/Brewers runs); EuroLeague `api-live` Round 8 schedule + Round 7 standings; NRL.com RLWC draw R1/R2; WST homepage fixtures + world ranking to 36th; ATP current scores + Brussels draw; Cricket Australia `/matches?isCompleted=0`; DP World Tour Genesis leaderboard after R2; Formula1.com calendar + drivers' standings; eurohandball.com calendar strip; gaa.ie fixtures.

## Sources that failed (attempted today, logged, not retried blind)

NBA `todaysScoreboard_00.json` HTTP 500; premrugby.com fixtures served page chrome only; unitedrugby.com/fixtures-results 404; pdc.tv/calendar cookie markup only; gbgb.org.uk open races filter UI only; cev.eu news only.

## Maths interpretation

p > 70% with fair American odds ≥ −250 intersect only at 70.00–71.43% (−250 = 71.43%). Tier A = that window (4 selections today, all NHL +1.5 puck lines / one EuroLeague winner); Tier B = >70% shorter than −250; Tier C = strongest in-band below 70%. Rugby league and handball deliberately use wide Normal SDs (not Poisson) because 1-game samples under Poisson produced absurd 99.99% figures in the first run — the fix and SDs are documented in `scripts/ledger_model.py` and on `ledger/method.html`. An early MLB baseline bug (runs per team-game double-counted) was caught by inspecting the totals output and corrected before build.

## Numbers

80 fixtures (40 priced), 310 selections, 26 previews (min 78 words), 23 flags, 30 sources, 26 pages. `scripts/ledger_verify.py`: 2,008 checks, 0 errors. `scripts/integration_audit.py`: 0 cross-layer link errors.

## Rebuild

```bash
python3 scripts/ledger_model.py
python3 scripts/ledger_predictions.py
python3 scripts/ledger_build.py
python3 scripts/ledger_verify.py
python3 -m unittest tests.test_ledger_21a0c524
```
