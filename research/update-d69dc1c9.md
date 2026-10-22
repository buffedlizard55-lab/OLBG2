# Research notes — /update/ layer, window 22–28 October 2026

Session `arena/d69dc1c9-olbg2` · branch `arena/d69dc1c9-olbg2` · claim in COORDINATION.md (D1–D6).

Goal: reverse-engineer the OLBG match list for the **17 eligible sports** (all except soccer,
boxing, UFC/MMA, football/American football, hurling, horse racing, cycling, specials), originate
our own lines (win/handicap/totals), pick winners with low/medium/high confidence under the
>70% + −250…+10000 gate, and publish at `/update/` with official source links on every row.
Policy: **never infer**; unconfirmable values stay blank and land on Flagged for Review.

## Fresh captures this session (official sources)

| Sport | Official source | What was captured |
|---|---|---|
| Ice hockey | `https://api-web.nhle.com/v1/score/2026-10-22` (+ further days) | 49 NHL fixtures 22–28 Oct with W-L-OT records, venues, team leaders (goals/assists/wins) |
| Baseball | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-10-28` | World Series 2026: Rays v Brewers, G1–G5 (23/24/26/27/28 Oct), venues + start times |
| Rugby union | `https://stats.unitedrugby.com/match-centre/202601/...` (8× per-match pages) | URC 2026-27 Round 4, eight fixtures incl. Cardiff–Sharks, Leinster–Munster (Aviva Stadium) |
| Snooker | `https://www.wst.tv/matches/` + `/match-centre/…` | BetVictor Northern Ireland Open 2026 Round 3, eight ties,22 Oct, Waterfront Hall |
| Tennis | `https://www.atptour.com/en/scores/stats/2026/9410/day/…` (Almaty), `7485/overview` (Brussels), `496/…` (Lyon) | ATP Almaty/Brussels/Lyon 22–24 Oct day schedules incl. Musetti–Atmane 6-1 6-2 result |
| Basketball | `https://www.euroleaguebasketball.net/en/euroleague/` (official widget) | EuroLeague R7 (6 games 22 Oct, 3 games 23 Oct incl. Olympiacos–Fenerbahce) + R8 (6 games 27 Oct); live standings positions beside each team |
| Darts | `https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship`, `…/19/2026-machineseeker-european-championship-schedule-confirmed/`, `…/22/Van-Veen-relishing-title-defence-in-Dortmund` | European Championship R1 Thursday x8 (Westfalenhalle, Dortmund), event structure, £750,000 prize fund, Humphries withdrawal |
| Motor racing | `https://www.formula1.com/en/results/2026/races`, `/races/1297/united-states/race-result`, `/races/1298/mexico/race-result`, `/results/2026/drivers` | 2026 winners table through Singapore (11 Oct), drivers' standings (Antonelli 340, Russell 238, Hamilton 229, Verstappen 221), **US GP 23–25 Oct COTA** (in window), Mexico GP 30 Oct–1 Nov (out of window) |
| Volleyball | `https://www.tauronliga.pl/games.html` (plusliga.pl redirects here), `/spcup/id/19/gid/236.html` | Polish men's league (TAURON Liga) 23–27 Oct fixtures incl. **AL-KO Superpuchar Polski** (Aluron CMC Warta Zawiercie v BOGDANKA LUK Lublin, 25 Oct) |

## Cross-references and inherited rows (never presented as fresh)

- **NBA**: `nba.com/schedule` rendered filter shell only; `cdn.nba.com/static/json/…`
  (scheduleLeagueV2_1.json, scheduleLeagueV2.json, todaysScoreboard_00.json) returned HTTP 500
  during the session. NBA rows for 22–28 Oct are **inherited** from `data/verified/matches.json`
  (PR #82, official sources captured by an earlier session) and labelled as such.
- **URC form labels**: fresh URC fixtures lacked records on the match-centre pages; form
  summaries were cross-referenced from `data/verified` same-window rows (labelled `cross-ref`).
- **Handball (EHFCL), Pro D2/Top 14 rugby, gaelic football, greyhounds, golf, cricket**:
  no working fresh capture path within the session's fetch budget → rows inherited from
  `data/verified/matches.json`, each with the prior layer's official URL, flagged.
- Prior-layer rows that clash with fresh captures (same pairing, different date/older sponsor
  naming — the Polish volleyball rows) are suppressed in favour of the official game centre
  render, and the clash is flagged (`date-clash-*`).
- **Australian rules (AFLW) and esports**: no verified rows anywhere for this window —
  recorded as gaps on the Flagged page; nothing invented.

## Irregularities (all on the Flagged page)

1. **PDC consent wall** — pdc.tv serves every page a consent interstitial to fetchers. Schedule
   and news text was obtained via search-engine rendering of the *official pdc.tv URLs*; rows
   keep those URLs and are flagged "indirect render of official page" for manual review.
2. **Luke Humphries withdrawal** — official PDC statement (22 Oct): Humphries withdrew with
   gastroenteritis; Kim Huybrechts takes his place v Ryan Searle. The superseded draw row is
   removed; the substitution is flagged for review.
3. **Timezones** — URC ("Local"), EuroLeague, TAURON Liga, ATP and MLB local times are published
   exactly as the official pages rendered them; no timezone inferred or converted.
4. **EuroLeague R8 28 Oct** — the widget rendered six R8 games (27 Oct) only; games 77–80, if
   any, never appeared. Left out, flagged as a known gap.
5. **WST venue** — matches page did not render venue per match; cell left blank (Belfast
   Waterfront Hall appears only as an event note).
6. **MLB player-level form** — the schedule API gave records and venues but no player stats;
   the Game 1 write-up names no players rather than inventing them.

## Line origination (scripts/update_model.py)

- Win match (team sports): Bill James **log5** on Laplace-smoothed W% = (W+1)/(GP+2), home
  advantage as a probability bump (NHL +0.035, URC +0.055, MLB +0.03).
- Handicap: expected margin from captured PF/PA differentials blended with win probability
  (NHL 6-goal scale, URC 14-point scale); ~1.91 two-way pricing. Totals: mean combined scoring.
- EuroLeague: logistic on captured standings positions (slope 0.12/rank, +0.35 home log-odds).
- PDC: logistic on official draw seedings where rendered (Ross Smith (1) v Sedlacek (32)).
- F1 race winner: 60% season win share + 40% last-five share over the official 2026 winners
  table; multi-outcome field shares normalised with a 6% field floor.
- Tennis: a line is originated only when both players have a captured result this week.
- Snooker, volleyball, unseded darts: **no form captured → no line, blank + flagged**.

## Confidence gate (unchanged from project policy)

- **high** = model probability ≥ 70% **and** fair American in [−250, +10000] (70.0–71.4% ⇒
  ≈ −250…−233). Higher-probability shorter-priced favourites are labelled
  "high (out of band)" and excluded from the in-band tables.
- **medium** ≥ 60%; **low** < 60%.

## Results (as built)

- 208 match rows (106 fresh, 8 form-cross-ref, 94 inherited), 165 picks, 114 in-band,
  11 high-confidence, 143 flagged items.
- Verification: `python3 scripts/update_verify.py` (8 gates) and
  `python3 -m unittest discover -s tests` (164 tests) pass at publish time.

## Errors and dead ends (do not retry)

- `cdn.nba.com` static JSON → HTTP 500 (all three endpoints); `nba.com/schedule` → filter shell.
- `icc-cricket.com/fixtures` → 404.
- `pdc.tv` (calendar, news, tournaments) → consent wall in every fetch chunk.
- `euroleaguebasketball.net/en/euroleague/schedule/` and `/games/` → 404 (the homepage widget works).
- GBGB cards, gaa.ie, afl.com.au, esl/a-sports client-rendered (historical dead ends, unchanged).
- plusliga.pl/games.html redirects to tauronliga.pl/games.html (works; season page is 16 chunks —
  fixtures for 23–25 Oct sit at chunks 2–3).
