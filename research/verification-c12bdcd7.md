# Line-by-line verification pass — session `arena/c12bdcd7-olbg2` (2026-10-22)

Method: every published row must carry an official source URL (enforced by tests and the two audit scripts);
this pass re-read the cited official pages **live on 2026-10-22** for each source family behind the highest-value
rows (the 14 featured in-band predictions, the new greyhound rows, the MLB World Series card and a forward-NHL
sample) and compared the published values against what the official page returned in this session. A value that
could not be confirmed stays blank and flagged; nothing was inferred.

## 1. Row-by-row results (re-read in this session)

| Row / claim | Official source re-read | Published value | What the official page returned | Result |
|---|---|---|---|---|
| `nhl-2026020162` MIN @ CGY | `api-web.nhle.com/v1/score/2026-10-22` (gameCenterLink `min-vs-cgy/2026/10/22/2026020162`) | 2026-10-23T01:00:00Z, Scotiabank Saddledome, MIN 6-2-2, CGY 2-6-0 | identical id, venue, startTimeUTC; MIN record `6-2-2`, CGY `2-6-0` | **PASS** |
| `nhl-2026020162` facts | same feed (teamLeaders) | Kaprizov 11 goals; Wallstedt 6 wins | Kaprizov goals 11; Wallstedt wins 6 | **PASS** |
| `nhl-2026020154` NSH @ BOS | same feed | TD Garden, 23:00Z | identical | **PASS** |
| `nhl-2026020159` NYI v LAK | same feed | UBS Arena, 23:30Z, NYI 5-3-1 | identical; NYI `5-3-1` | **PASS** |
| `nhl-2026020161` WPG @ DAL | same feed | American Airlines Center, DAL 5-3-1, Oettinger 4 wins | identical; DAL `5-3-1`, Oettinger wins 4 | **PASS** |
| `nhl-2026020162/163` day count | same feed `gameWeek` | 22 Oct: 12 NHL games | `numberOfGames: 12` for 2026-10-22 | **PASS** |
| `urc-292609` Connacht v Zebre | `stats.unitedrugby.com/match-centre/.../292609` | 2026-10-23 18:45 UTC, Dexcom Stadium, Connacht 56 PF, Zebre 52 PF | "Fri, 23 Oct 2026", Dexcom Stadium, Connacht v ZebreParma; countdown 1d 10h ≈ 18:45 UTC; Season Stats: Connacht Points 56, Zebre Points 52 | **PASS** (page's "2:45 pm" is a US-Eastern JS render — see irregularities) |
| `top14-11867` Toulouse v Perpignan | `top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan` | 2026-10-24 14:35 UTC, Stade Ernest-Wallon | "24 Octobre 2026, 16h35, Stade Ernest Wallon" (16h35 CEST = 14:35 UTC ✓) | **PASS** |
| `ehfcl-202711020101049` Barça v Montpellier | `ehfcl.eurohandball.com/.../202711020101049/Barça-MontpellierHandball/` | 2026-10-22 20:45 CEST | fixture page title "Barça 0:0 Montpellier Handball - Group Phase"; sidebar "M20:45 Barça v Montpellier Handball" | **PASS** |
| `ehfcl-…1041` Sporting v Kristianstad, `ehfcl-…1064` Kolstad v Magdeburg | same EHF sidebar (Oct 22) | published rows | both fixtures and 20:45 CEST slots present | **PASS** |
| `el-E2026-67` Panathinaikos v Baskonia | `euroleaguebasketball.net/.../E2026/67/` | 2026-10-22 18:15 UTC, Telekom Center Athens, PAO 5-1 (528 PF), KBA 1-5 (504 PF) | title "… 2026-10-22 18:15"; "TELEKOM CENTER ATHENS"; table ranks (1) and (20); PPG 88.0 = 528/6 and 84.0 = 504/6 | **PASS** (facts reproduce exactly) |
| MLB WS G1–G7 (`mlb-ws-g1..g7`, live `mlb-849805/02/04`) | `statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-11-05&gameType=W` | 7 games: G1 10-23 TB@MIL, G2 10-24, G3 10-26 MIL@TB, G4 10-27, G5 10-28 (if-nec), G6 10-30, G7 10-31 | all 7 gamePks (849805/02/04/03/799/01/00), dates, venues and `ifNecessary` flags identical | **PASS — closes the "G5–G7 listing" open item** |
| Forward NHL sample `nhl-2026020166/167` | `api-web.nhle.com/v1/score/2026-10-23` | MTL @ CHI United Center 2026-10-24T00:00Z; TBL @ COL Ball Arena 01:00Z | identical id, venue, startTimeUTC | **PASS** |
| 10 greyhound rows `gbgb-cat1-*` | `gbgb.org.uk/racing/open-races/2025-category-one-schedule/` (re-read twice today) | 23 Oct Romford Champion Stakes 575m … 26 Dec Newcastle All England Cup 480m | all ten (date, track, event, distance) identical to the verbatim capture in `data/verified/capture_gbgb_cat1_c12bdcd7.json` | **PASS** |
| NBA per-day counts (VF-14) | `nba.com/games?date=2026-10-23` (re-read today) | 22:2, 23:12, 24:8, 25:7, 26:9, 27:4, 28:12, 29:3, 30:10, 31:7 | identical month calendar counts; fixture lists still fail server-render ("Sorry, something went wrong"); CDN JSON still HTTP 500 | **PASS (counts) / gap stays open (matchups)** |

## 2. Automated gates (all green after this session's changes)

| Gate | Result |
|---|---|
| `python -m unittest discover -s tests` | **88/88 OK** (incl. new window-rule, archive and band-annotation gates in `test_dashboard`, `test_live`, `test_build`, `test_forward`, `test_verified_pipeline`) |
| `scripts/integration_audit.py` | 0 cross-layer local link errors |
| `scripts/survey_verify.py` | VERIFICATION PASSED, deterministic rebuild |
| `scripts/live_build.py` | 0 broken local links; every fixture row carries an official source URL |
| CI chain (all five layers rebuilt, `git diff --exit-code` on generated paths) | byte-identical — committed outputs match generator output |
| Every table row has a source link | enforced per layer (unregistered citations fail the build; blank cells must carry a reason) |

## 3. Irregularities observed in this pass

1. **URC match-centre pages render kick-off times in US-Eastern regardless of viewer** ("2:45 pm" for an 18:45
   UTC kick-off; the countdown widget confirms the UTC instant). This is the same class of issue as VF-29;
   our published UTC times are correct and no conversion is needed. No data change.
2. **GBGB's own schedule contains a typo** — "Arena Racng Company Scurry Gold Cup". Our row reproduces the
   official text verbatim (never silently "fix" a source) and the capture file notes it.
3. **EuroLeague game 61 (Hapoel 90–81 Virtus, 21 Oct)** — carried as an open informational item by session
   `26963a2d`. Not re-read in this pass (the season feed is large and the row is not featured); remains
   informational-only and blocks nothing.
4. **VF-14 (NBA matchup lists)** and **VF-22's per-race-card gap** remain open and are published on the Flagged
   pages. VF-22's *fixture listing* gap is closed (ten Category One rows live).

## 4. Coverage limit of this pass (disclosed, like VF-23)

The 128-row verified desk was not re-read row-by-row against every one of its ~47 source families in this
session; this pass covered all 14 featured prediction rows' families (NHL, URC, Top 14, Pro D2 team pages were
already re-read by `26963a2d`, EHF, EuroLeague), the MLB WS card, the greyhound capture, and a forward-NHL
sample. Remaining rows carry their capture-dated source links for manual review, exactly as VF-23 describes.
