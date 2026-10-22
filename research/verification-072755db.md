# Independent verification pass — session `arena/072755db-olbg2` (2026-10-22 02:50–03:40 UTC)

Purpose: re-read the official governing-body pages behind the published `/verified/` desk and check the desk's
figures line by line, rather than trusting the previous session's capture. Everything below was fetched **in this
session** with the agent's page-reading tool; the sandbox has no direct HTTP egress, so the URLs are the same ones
printed on the site rows.

## 1. What was re-read, and what matched

| Source family | Official URL fetched | Values compared | Result |
|---|---|---|---|
| NHL team rates | `https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027 and gameTypeId=2` | MIN 6-2-2, 14 pts, 31 GF, 25 GA; CGY 2-6-0, 4 pts, 17 GF, 37 GA; CAR 8-2-1, 17 pts, 42 GF, 27 GA; EDM 7-1-1, 15 pts, 41 GF, 27 GA | **All four match exactly** |
| NHL fixtures | `https://api-web.nhle.com/v1/score/2026-10-22` | BOS 7-2-1 vs NSH 3-2-3 at TD Garden 23:00Z; TOR 5-4-2 vs NYR 7-3-1; 12 games on the date | Match |
| URC table | `https://stats.unitedrugby.com/match-centre/table/2026-27` | Edinburgh 14 pts (3-0-0, 80/54); Glasgow 13 (2-1-0, 95/72); Bulls 11 (2-0-1, 126/54, +72); Stormers 11 (2-0-1, 81/54); Lions 9 (2-0-1, 77/102); Dragons 9 (1-1-1, 88/83); Ulster 8 (0-2-1, 88/93); Scarlets 7 (1-0-2, 68/85); Connacht 5 (1-0-2, 56/84); Zebre 1 (0-0-3, 52/116, −64) | **All 10 match exactly** |
| URC results (Round 3) | same page, results panel | Glasgow 36-19 Connacht; Bulls 57-15 Lions; Stormers 39-22 Sharks; Dragons 31-38 Ospreys; Edinburgh 29-12 Zebre | Match |
| Top 14 table | `https://top14.lnr.fr/classement` | Toulouse 24 pts, 6 GP, 5-0-1, 197/124, +73, form V-V-V-V-V; Perpignan 9th | Match (Perpignan's row detail was cut off in the fetched chunk — rank only, see §4) |
| Pro D2 table | `https://prod2.lnr.fr/classement` | Provence 2nd, 29 pts, 7-0-0, 222/158, +64; Aurillac 9th, 16 pts, 3-0-4, 240/254, wins v Biarritz (J6) and Béziers (J7); Béziers 14th, 9 pts, 2-0-5, 147/240, −93; Nevers 16th, 4 pts, 0-0-7, 146/222, −76 | Match, except one prose sentence (defect 1) |
| EuroLeague standings | `https://www.euroleaguebasketball.net/en/euroleague/standings/` | Panathinaikos 1st, 6 GP, 5-1, 528/438, +90, home 4-1; Baskonia 20th, 6 GP, 1-5, 504/564, −60, home 1-3, away 0-2 | **Both match exactly** |
| EHF Champions League | `https://ehfcl.eurohandball.com/men/2026-27/standings/` + `/matches/` | Group E: Barça 4 GP, 4-0-0, 137:104, 8 pts; Montpellier 4 GP, 1-0-3, 116:125, 2 pts; Barça–Montpellier fixture 202711020101049 on 22 Oct 20:45 | Match |
| WST rankings | `https://www.wst.tv/rankings/` and the full-table link | Top 36 prize values (Zhao £1,265,550 … Jackson Page £198,500); Kyren Wilson £716,800 (#9); Pang Junxu £272,750 (#29) | Match; the table still stops at #36, so 9 of the 16 named Round 3 players remain unpriced |

Market-level arithmetic was also checked programmatically over all 119 rows: each two-way/three-way market sums to
1.0, each quoted price equals `round(1/p, 2)`, every pick's American price equals the American equivalent of its
published decimal, and every row carries an `https://` official URL.

## 2. Defects found and fixed in this session

1. **Pro D2 form sentence (VF-25).** The Provence–Béziers narrative said Béziers "have dropped four of their last
   five". The LNR table's form string is V-D-V-D-D: two wins, **three** defeats. Corrected to "have lost three of
   their last five matches". The row's numbers were already right.
2. **Confidence labelling (VF-26).** Minnesota (70.82%), Aurillac (70.53%) and Connacht (70.25%) were written up as
   high-confidence band picks but their own match row read `medium`, because the row grading used the 72% rule
   only. The published copy already promises "high ≥72%, or a band pick ≥70%", so the model now applies that
   clause. High rises 15 → 18; probabilities and prices are untouched; the NBA medium cap still holds.
3. **Price rounding.** `fair_american()` derived the American price from the unrounded probability while the
   decimal price was rounded first, so three rows printed two different prices for one selection (1.43 beside
   −230, 1.33 beside −299). The American figure is now derived from the published decimal, and the test asserts
   exactly that relationship.
4. **Documentation drift.** `README.md` still described the previous 155-row snapshot (112 originated, 13 band
   picks, 33 predictions, 18 review items, 92 fixture-scoped URLs) and `METHODOLOGY.md` claimed every write-up
   names a player with a verified statistic. Both are corrected to the live figures (119 / 93 / 14 / 14 / 26;
   85 fixture-scoped / 34 competition-scoped) and to what the write-ups actually contain.
5. **Root methodology lede** was hardcoded to "112 originated lines … 33 predictions"; it now reads from the data
   (93 … 14).
6. **Fixture-scope counter printed 0.** The dashboard's "N of M rows cite a URL that identifies the individual
   fixture" line read `0 of 119` because `build_site.py` expected a `source_scope` field the model never emitted.
   The model now derives it from each row's URL (fixture paths: `/gamecenter/`, `feuille-de-match/`,
   `/matches/details/`, `/match-centre/<id>/`, `/game/`, `/gameday`, ICC match ids). Result: **85 fixture-scoped,
   34 competition-scoped**, matching the README and VF-11.
7. **Capture badge said 21 Oct on every row.** `verified_cell()` hardcoded "captured 21 Oct" while the dataset is a
   2026-10-22 capture; it now reads `captured_at` from `matches.json` and renders "captured 22 Oct".

## 3. What this pass did **not** verify

The pass covered six source families, not all 119 rows. The following were **not** re-read against their official
page in this session and keep the previous session's 2026-10-22 capture: all 16 PDC darts ties (ranking ladder
behind a consent wall, VF-21), all 8 WST snooker ties (missing prize values for 9 of 16 players, VF-03), the 14
NBA rows, the 4 MLB World Series rows, the 3 F1 rows, the 2 golf rows, the 2 cricket rows, the 3 volleyball rows,
the 3 rugby-league futures and the 5 Gaelic football rows. This is published as **VF-23**; it is a limit of the
verification, not a finding that those values are wrong.

Also still open: Top 14 Perpignan's points/PF/PA detail (the fetched chunk cut off before the row), the Toulouse
"60-14 v Sale Sharks" line (EPCR page not fetched), and the Round 3 frame format that blocks the snooker rows.

## 4. How to reproduce

```bash
python3 scripts/verified_seed.py && python3 scripts/verified_model.py && python3 scripts/verified_build.py
python3 scripts/build_site.py && python3 scripts/integration_audit.py && python3 -m unittest discover -s tests
```

Expected: 119 rows / 93 originated / 26 unlined / 18 high / 26 medium / 49 low / 14 featured / 26 flags;
integration audit 0 link errors; 63 tests pass; `git diff --exit-code` clean after a rebuild.
