# Daily Top-5 desk — capture & verification record (session `arena/b499dfe1-olbg2`, 2026-10-22)

## Scope claimed
New files only: `daily/**`, `data/daily/**`, `scripts/daily_{seed,model,build,verify}.py`,
`tests/test_daily_b499dfe1.py`, this note, one COORDINATION entry. No shared output edited.
Integration requests for the final integration session are logged in COORDINATION.md
(add `/daily/` to root nav, `scripts/integration_audit.py` folder list, and the CI drift paths).

## OLBG reverse engineering (fresh fetch, 2026-10-22)
- `https://www.olbg.com/betting-tips` — hub index; sport schema `/betting-tips/{Sport}/{sport_id}`,
  event schema `/betting-tips/{Sport}/{...}/{Home}_v_{Away}/{sport_id}?event_id={id}`.
  Markets observed on the front page: Money Line (MLB TB Rays @ MIL Brewers, event 160789, "Tomorrow 20:00"),
  NBA Money Line (CLE @ PHI 534845, DEN @ OKC 534843, "Today"), Win Match 2-way
  (Darts: Ryan Joyce vs Jermaine Wattimena, 32332, "Tomorrow 13:15"), Gaelic Football handicap
  (St Finbarrs v Nemo Rangers, 3530, 25 Oct). Excluded-sport events (Football, American Football,
  Horse Racing) were ignored per brief. OLBG tip percentages are community counts, never used as prices.
- The 17-sport eligible taxonomy and OLBG sport ids are taken from `data/verified/sports.json`
  (captured 2026-10-22 by prior sessions) and are consistent with the live hub above.

## Fresh official confirmations by this session (2026-10-22)
| Fetch | What it confirmed |
|---|---|
| `https://api-web.nhle.com/v1/score/2026-10-23` | 2 games FUT: MTL@CHI (2026020166, United Center, records 4-3-2 / 3-6-0; leaders Caufield 6G, Suzuki 7A, Fowler 3W; Nazar 3G), TBL@COL (2026020167, Ball Arena; Hagel 7G, Kucherov 9A). Matches `data/current/capture/nhl_score_2026-10-23.json`. |
| `https://api-web.nhle.com/v1/score/2026-10-24` | 12 games FUT incl. ANA@PHI 2026020168, LAK@NJD 2026020169 with leaders (Sennecke 5G, Michkov 6G, Carlsson 9A…). Matches repo capture. |
| `https://api-web.nhle.com/v1/standings/2026-10-22` | GP/W/L/OTL/GF/GA per club (e.g. CAR 11GP 42GF 27GA) agree with `nhl_team_summary_2026-10-22.json`. |
| `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-29` | World Series Games 1–5: gamePk 849805 (23 Oct, TB@MIL, American Family Field), 849802 (24th), 849804 (26th, MIL@TB, Tropicana Field), 849803 (27th), 849799 (28th, if-necessary). Game 5 was missing from the seeded verified fixtures and was added from this fetch. |
| `https://lolesports.com/en-US` | Worlds 2026 listed as global event; dated upcoming pairings not server-rendered → esports zero-row flag, nothing invented. |

All other fixtures/inputs come from official captures already in the repo dated 2026-10-22:
`data/verified/inputs.json` (NBA 2025-26 standings + opening-week fixtures, EuroLeague standings,
Top 14 / Pro D2 / URC tables incl. form strings, EHF 24-club standings, PDC Werner Rankings Ladder
prize money for 32 players, MLB 162-game records & runs) and `data/current/capture/*.json`
(NHL score/summary, EuroLeague R7, EHF fixtures incl. 28–29 Oct, URC table + R3 results,
WST NI Open, F1 calendar + 23-driver standings + race winners, MLB league run sample).

## Result (window 2026-10-23 → 2026-10-30)
- 132 originated fixtures: basketball 68 (65 NBA + 3 EuroLeague), rugby union 24, ice hockey 14,
  handball 12, darts 8, baseball 5, motor racing 1 (23-driver outright).
- Every originated match has a match-winner pick plus handicap and total markets investigated
  (NBA totals deliberately blank — no official PF/PA; darts adds leg handicap & total legs;
  F1 race-winner outright). All prices fair no-vig (decimal 1/p from the stored, rounded p).
- Confidence: 25 high (p ≥ 70% AND fair American in −250…+10000 AND sample gate), 70 medium, 37 low.
- Top-5 per sport: full fives for ice hockey, basketball, rugby union, handball, darts, baseball;
  motor-racing 1/5. 45 unique written predictions (76–149 words) covering every Top-5 pick and
  every high — each names the selection first and uses only seeded official facts
  (records, PF/PA rates, form strings such as SU Agen W-L-L-W-W, PDC ranks/prize money,
  NHL player leaders such as Michkov 6 goals).
- 9 unlined official fixtures carried with blank prices (gaelic 4, greyhounds 3, volleyball 1, darts outright 1)
  and 20 flags (DA-01…DA-20) on `daily/flagged.html`, including zero-row reasons for tennis,
  snooker, cricket, golf, rugby league, Aussie rules and esports — in each case the official
  capture did not server-render verifiable pairings/inputs, so nothing was invented.

## Irregularities flagged (see daily/flagged.html)
1. F1 race-day date: formula1.com capture renders the US weekend "23–25 Oct"; race day taken as
   25 Oct and disclosed on the row — needs manual confirmation against the official timetable.
2. NBA prices rest on 2025-26 records (0 games played in 2026-27 at capture) — capped at medium.
3. MLB Games 3–5 are the same two clubs; Games 5 is if-necessary per the MLB API.
4. Several Top-5 "high" selections sit at exactly −250 after 2-dp decimal rounding (p 0.7137–0.7167);
   the band rule is applied to the published rounded price and disclosed in the methodology.
5. Snooker/tennis/esports have live events this week but no server-rendered official pairings in
   capture — candidates for a future session with a rendered-page capture.

## Verification performed
- `python3 scripts/daily_verify.py` → OK (window, https official URL on every row/flag/prediction,
  price = 1/p within rounding, band gate, Top-5 ranking, ≥30-word & pairwise-Jaccard ≤ 0.88
  prediction uniqueness, internal-link existence, short-sport flag coverage).
- `python3 -m unittest tests.test_daily_b499dfe1` → 14 tests OK, including assertions on the
  *rendered* HTML (Top-5 selections present, local links resolve).
- Deterministic rebuild: seed → model → build re-run produces no diff.
- Line-by-line spot checks of predictions against seeded inputs (handball Veszprém 5-0, 37.0/29.2;
  darts Aspinall No.11 £579,500; baseball TB 98-64 4.54 rpg) all agree.
