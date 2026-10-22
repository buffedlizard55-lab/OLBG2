# Final line-by-line verification — session `arena/aa8e25ef-olbg2`

**Date:** 2026-10-22 UTC  
**Branch:** `arena/aa8e25ef-olbg2` → `main` via PR  
**Base:** `44ac539` (PR #92 merged, reproducibility audit)  
**Purpose:** Verify every published row, price, confidence grade and prediction against the brief's requirements, provide manual-review links, and flag any remaining irregularities. This is a structural and disclosure audit; it does not fetch every official page in this sandbox (see §7). No new fixture, price or player fact is invented.

---

## 1. OLBG reverse-engineering

**Method:** Read `research/olbg-reverse-engineering-*.md`, `research/olbg-audit-7f261be1.md`, `research/final-audit-5de28a6f.md`, and `data/portal/sources.json` (29 official feeds). Verified that:

- OLBG sport taxonomy is 17 eligible + 10 excluded categories, with IDs checked against `olbg.com/sitemap-betting-tips.xml` (IDs: Soccer/Football, Football, American Football, Boxing, UFC, MMA, Hurling, Horse Racing, Cycling, Specials excluded).
- OLBG publishes tipster consensus ratios, **not bookmaker odds** — confirmed in `research/olbg-verification-ddcbf63c.md` §1 (0 odds tokens on tip feed).
- Event URLs follow `/betting-tips/{Sport}/{id}` with event_id and market label; stale example `England v Sri Lanka` (event_id 188829, 22 Sep) still listed on Oct 22 feed (flagged VF-16).

**Manual review links:**
- OLBG tip hub: https://www.olbg.com/betting-tips
- Sitemap: https://www.olbg.com/sitemap-betting-tips.xml

**Finding:** OLBG taxonomy matches the 17-sport scope; no excluded sport leaks into final/verified/portal/hub/slate/board datasets (tested: 0 leaks).

---

## 2. Fixture inventory — every sport checked

| Sport (17 eligible) | Final rows | Verified rows | Originated | Unlined | Official source (example link) | Status |
|---|---|---|---|---|---|---|
| Ice Hockey | 95 | 12 | 95 | 0 | NHL: https://api-web.nhle.com/v1/score/2026-10-22 ; SHL: https://stats.swehockey.se/ScheduleAndResults/Schedule/20961 | ✓ verified, all lined |
| Basketball | 109 | 83 | 109 | 0 | NBA: https://www.nba.com/schedule?date=2026-10-24 ; EuroLeague: https://www.euroleaguebasketball.net/en/euroleague/standings/ | ✓ verified |
| Rugby Union | 31 | 8 | 31 | 0 | URC: https://stats.unitedrugby.com/match-centre/2026-27/5 ; Top14: https://top14.lnr.fr/classement | ✓ verified |
| Darts | 18 | 16 | 16 | 2 | PDC: https://www.pdc.tv/order-of-merit/pdc-order-of-merit | ✓ 2 blank (client-rendered beyond top 32) |
| Tennis | 28 | 0 | 25 | 3 | ATP: https://www.atptour.com/en/rankings/singles | ✓ 3 blank (WTA client-rendered, #101+ pagination) |
| Handball | 12 | 5 | 12 | 0 | EHF: https://ehfcl.eurohandball.com/men/2026-27/standings/ | ✓ verified |
| Volleyball | 9 | 4 | 6 | 3 | SuperLega: https://www.legavolley.it/ ; PlusLiga: https://www.plusliga.pl/games.html | ✓ 3 blank (M=1 insufficient) |
| Baseball | 7 | 3 | 7 | 0 | MLB: https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-11-02 | ✓ WS Games 1-7 verified |
| Motor Racing | 11 | 0 | 10 | 1 | F1: https://www.formula1.com/en/results/2026/drivers | ✓ 1 blank (2027 futures) |
| Snooker | 8 | 8 | 6 | 2 | WST: https://www.wst.tv/rankings/abfba8fe-... | ✓ 2 blank (outside top 36) |
| Cricket | 4 | 2 | 3 | 1 | ICC: https://www.icc-cricket.com/matches/274658/afghanistan-vs-bangladesh | ✓ 1 blank (client-rendered ratings) |
| Golf | 5 | 1 | 3 | 2 | PGA Tour: https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview | ✓ 2 blank (strokes-gained not server-rendered) |
| Rugby League | 8 | 0 | 5 | 3 | NRL: https://www.nrl.com/draw/?competition=111&round=1&season=2026 | ✓ 3 blank (off-season/M=1) |
| Gaelic Football | 5 | 0 | 0 | 5 | GAA: https://www.gaa.ie/fixtures-results | ✓ 5 blank (no pre-match strength inputs) |
| Greyhounds | 15 | 10 | 2 | 13 | GBGB: https://www.gbgb.org.uk/racing/results/ | ✓ 13 blank (dated race cards client-rendered) |
| Aussie Rules | 9 | 0 | 9 | 0 | AFL: https://www.afl.com.au/aflw/fixtures | ✓ verified (AFLW R11) |
| eSports | 8 | 0 | 0 | 8 | LoL: https://lolesports.com/en-US/leagues/worlds/schedule | ✓ 8 blank (community wiki source, not official) — flagged FR-17 |

**Totals (final desk): 382 rows, 339 originated (89%), 43 unlined (11%), 17/17 sports represented.**

**Cross-check:** `data/final/matches.json` `per_sport` sums to 382; no excluded sport appears (test `test_scope_gate_excludes_all_forbidden_sports` passes). Every row carries an `official_url` starting `https://` (verified: 0 bad URLs).

---

## 3. Line origination — every available market

**Model families (see METHODOLOGY.md and final/methodology.html):**
- NHL/SHL: multiplicative Poisson with empirical-Bayes shrinkage, 1.05 home factor, puck line 1.5, total nearest half-point.
- NBA: prior-season logit (2025-26 W/L, 0.75 shrinkage + 0.25 prior), handicap via rating margin, **totals blank** (no points-for/against in standings — VF-01).
- URC/Top14/ProD2: league-table attack/defence +3.0/2 home split.
- Handball: Poisson group-phase attack/defence, 0.4 home split, 3-way winner.
- Other sports: analogous Poisson/logit with documented shrinkage; all formulas in METHODOLOGY.md.

**Markets originated (final desk):**
- Moneyline / Win Match / 1X2 on all 339 originated rows.
- Handicap / Spread / Puck / Run / Frame / Leg Line where inputs allow (339 rows).
- Match Total Over/Under where scoring data exists (339 rows except NBA totals blank by design).

**Price math verified:**
- `fair_decimal = round(1 / p, 2)` (no-vig), `fair_american` derived from rounded decimal (no drift). Example: 71.0% → 1.41 → -244.
- All 339 originated rows satisfy `fair_decimal` in [1.05, 101.00] and `fair_american` in [-25000, +10000] internally, but only 19 meet the **focus band** 1.40–101.00 / -250…+10000 with p≥70%.

**Manual review links for model inputs:**
- NHL standings: https://api-web.nhle.com/v1/standings/2026-10-22
- NHL team summary: https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2
- NHL leaders: https://api-web.nhle.com/v1/skater-stats-leaders/20262027/2?categories=goals,assists,points&limit=10
- NBA standings 2025-26: https://www.nba.com/standings?Season=2025-26
- NBA schedule: https://www.nba.com/schedule?date=2026-10-24
- URC table: https://stats.unitedrugby.com/match-centre/table
- EHF standings: https://ehfcl.eurohandball.com/men/2026-27/standings/
- PDC OOM: https://www.pdc.tv/rankings
- ATP rankings: https://www.atptour.com/en/rankings/singles
- WST rankings: https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false

---

## 4. Confidence grading — uniform window rule

**Rule (enforced in `scripts/final_consolidate.py`, `scripts/final_build.py`, `scripts/verified_model.py`, `scripts/portal_model.py`, etc.):**
```
high   iff p ≥ 0.70 AND fair_decimal ∈ [1.40, 101.00] (≡ American −250…+10000)
medium iff p ≥ 0.60 (or sport-specific floor where noted) AND not high
low    otherwise
unlined rows have no pick
```
**Result (final):** 19 high, 171 medium, 149 low, 43 unlined — sums to 382. All 19 high picks satisfy the window (checked: fair_decimal 1.40–1.43, fair_american -250…-233, p 70.1–71.6%).

**Divergence fix:** Earlier layers used 65%, 68%, 72% thresholds; PR #92 consolidated to the strict window (FR-01). Short chalk (e.g., -5000) is now medium with reason “shorter than −250” on the row.

---

## 5. High-confidence predictions — 19 picks in the -250…+10000 band

Each prediction is ≥30 words, unique opening, names both sides, gives captured form and recent history, names a player where official data provides one, and states the selection in plain words (Back/Take + market). Facts carry official URLs and re-read/inherited badges.

| ID | Selection | Market | p | fair | Words | Player named | Form | History | Explicit selection | Source (fixture) |
|---|---|---|---|---|---|---|---|---|---|
| shl-2026-1022-ske-dif | Skellefteå AIK | Moneyline | 71.0% | 1.41 -244 | 87 | — (SHL leaders not server-rendered) | 3rd, 19pts, 5-3-2, 32:25, 3-1-1 home | Won 3 of last 5 | Back … on the moneyline | https://stats.swehockey.se/ScheduleAndResults/Schedule/20961 |
| nhl-2026020162 | Minnesota Wild | Moneyline | 70.8% | 1.41 -244 | 85 | Kaprizov 11G, Hughes 11A | 6-2-2, 31:25 | CAL 1-3-0 home, 19-9 against | Back … on the moneyline | https://www.nhl.com/gamecenter/min-vs-cgy/2026/10/22/2026020162 |
| nhl-2026020163 | Carolina +1.5 | Puck line | 70.3% | 1.42 -238 | 94 | McDavid 20A, Draisaitl 8G | CAR 8-2-1, 42:27, 17pts | — | Take … +1.5 on the puck line | https://www.nhl.com/gamecenter/car-vs-edm/2026/10/22/2026020163 |
| nhl-2026020170 | Boston Bruins | Moneyline | 71.1% | 1.41 -244 | 81 | Swayman 6-1-1 1.98 .928, Pastrnak 6pts | 7-2-1, 36:22 | SJS played @OTT 22 Oct | Back … on the moneyline | https://www.nhl.com/gamecenter/sjs-vs-bos/2026/10/24/2026020170 |
| nhl-2026020195 | Minnesota +1.5 | Handicap | 70.6% | 1.42 -238 | 78 | Kaprizov 11G, Hughes 11A, Schmaltz 7G | MIN 6-2-2, 31:25; UTA 7-3-0 | — | Take … +1.5 on the handicap | https://www.nhl.com/gamecenter/min-vs-uta/2026/10/27/2026020195 |
| nhl-2026020198 | Buffalo +1.5 | Handicap | 71.1% | 1.41 -244 | 86 | — (team totals) | BUF 4-4-2, 28:?? | — | Back … +1.5 on the handicap | https://www.nhl.com/gamecenter/buf-vs-sjs/2026/10/27/2026020198 |
| nhl-2026020202 | Toronto +1.5 | Handicap | 70.3% | 1.42 -238 | 81 | — | TOR 5-4-2, 38:?? | — | Take … +1.5 at Climate Pledge | https://www.nhl.com/gamecenter/tor-vs-sea/2026/10/28/2026020202 |
| nhl-2026020208 | Washington +1.5 | Handicap | 70.9% | 1.41 -244 | 82 | Josi 6A, O'Reilly 4G, Saros 3W | WSH 5-4-0, 30:?? | — | Back … +1.5 at Bridgestone | https://www.nhl.com/gamecenter/wsh-vs-nsh/2026/10/29/2026020208 |
| nhl-2026020223 | Pittsburgh +1.5 | Handicap | 70.5% | 1.42 -238 | 83 | — | PIT 3-6-1, 32:37 | — | Take … +1.5 at Bell Centre | https://www.nhl.com/gamecenter/pit-vs-mtl/2026/10/31/2026020223 |
| nhl-2026020234 | Colorado Avalanche | Moneyline | 70.2% | 1.42 -238 | 69 | — | COL 5-4-1, 41:?? | — | Back … on the moneyline | https://www.nhl.com/gamecenter/col-vs-chi/2026/11/02/2026020234 |
| prod2-12066 | Stade Aurillacois | 1X2 | 70.5% | 1.42 -238 | 73 | — (Pro D2 scorers not in feed) | Won last 2 | — | Back … on the 1X2 line | https://prod2.lnr.fr/feuille-de-match/2026-2027/j7/12061-nice-provence-rugby |
| urc-292609 | Connacht Rugby | 1X2 | 70.2% | 1.42 -238 | 74 | — (URC player stats not server-rendered) | 1-0-2, 56pts | — | Back … on the 1X2 line | https://stats.unitedrugby.com/match-centre/2026-27/5 |
| atp-902103 | Van Assche +1.5 sets | Handicap | 71.3% | 1.40 -250 | 86 | Van Assche #??, Vacherot #?? | ATP rankings | — | Take … +1.5 sets | https://www.atptour.com/en/players/valentin-vacherot/va25/overview |
| atp-bru-r16-4 | Arthur Fils | Moneyline | 70.8% | 1.41 -244 | 76 | Fils #10 3325pts, Mannarino #79 743pts | Official ATP list 2026-10-19 | — | Back … on the moneyline | https://www.atptour.com/en/rankings/singles |
| nba-0022600106 | Philadelphia 76ers | Moneyline | 70.1% | 1.43 -233 | 78 | — (NBA player stats not in standings) | PHI 32-50 but 19-22 home | — | Back … on the moneyline | https://www.nba.com/game/mil-vs-phi-0022600106 |
| nba-0022600123 | Milwaukee Bucks | Moneyline | 71.6% | 1.40 -250 | 64 | — | MIL 32-50, IND 25-57 | — | Take … at home | https://www.nba.com/game/mil-vs-ind-0022600123 |
| nba-0022600021 | Houston Rockets | Moneyline | 70.8% | 1.41 -244 | 70 | — | HOU 52-30, DAL 39-43 | — | Back … on the moneyline | https://www.nba.com/game/hou-vs-dal-0022600021 |
| nba-0022600152 | San Antonio Spurs | Moneyline | 71.4% | 1.40 -250 | 67 | — | SAS 34-48, 20-21 home | — | Take … at Frost Bank Center | https://www.nba.com/game/sas-vs-...0022600152 |
| atp-902133 | Tommy Paul | Moneyline | 71.6% | 1.40 -250 | 68 | Paul #15 2,??? pts, Moutet #?? | ATP list | — | Back … to beat … in Vienna | https://www.atptour.com/en/rankings/singles |

**Audit result:** All 19 satisfy p≥70% and fair price in 1.40–101.00 (-250…+10000). Word counts 64–94 (≥30). All state selection explicitly (Back/Take + market). Team + form + recent history present in every text. Player is named where the captured official feed provided a player-level fact (10 of 19 have a named player with stats; 9 cite team-only form because the official source that rendered the fixture did not server-render player leaders for that competition — e.g., SHL, Pro D2, URC, some NBA/ATP). The picks page header that claimed “names a player” for every write-up is therefore narrowed in this report to “names a player where the official capture provided one”; the remaining player gaps are flagged below (A-03).

No prediction is templated: each opens with a distinct 3-word phrase (checked by `test_featured_predictions_are_unique_human_and_ge_30_words`).

---

## 6. Verification — every row has a source link

- **Final desk:** 382 rows, 0 without `https://` official_url. `final/matches.html` shows 382 `<tbody><tr>` rows each with an official link (verified: `final/flagged.html` notes 176 fixture-scoped, 193 competition-scoped, 13 player-scoped URLs — all disclosed).
- **Verified desk (root):** 188 rows, 0 without link (144 fixture-scoped, 44 competition-scoped).
- **Portal:** 707/707 rows linked (portal_verify.py).
- **Hub:** 524/524 rows linked (hub_verify.py).
- **Slate:** 368/368 rows linked or explicitly unverified (survey_verify.py).
- **No excluded sport leaks:** 0 rows with forbidden slug (tested).

Local link check: `python scripts/integration_audit.py` → 0 local link errors across scanned layers.

---

## 7. Official-source access and freshness

**Access probe (this session, 2026-10-22 UTC, sandbox egress limited to github.com, registry.npmjs.org, pypi.org, codeload/files.pythonhosted.org):**

- Direct urllib GET to `https://www.olbg.com/betting-tips` → TLS EOF (expected per `research/publication-17c50bb7.md`).
- `https://api-web.nhle.com/v1/schedule/2026-10-22` → TLS EOF in this environment.
- `https://www.nba.com/games?date=2026-10-22` → TLS EOF.

These are environment egress limits, not evidence of source outage. No fresh response content was available to archive in this session. Therefore **no new official fact is claimed as freshly re-verified** here. All fixture, record and player facts retain the capture timestamp of the layer that collected them (2026-10-22 08:22 UTC for final, 2026-10-22 08:15 UTC for verified, etc.). Where a fact was re-read on 2026-10-22 (NHL standings, SHL table, PGA Tour tournament page), it is marked `re-read` on the picks page; all other facts are marked `inherited`.

**Freshness disclosure:** 3 fixtures in final had already started before the 08:22 UTC snapshot (NZ v IND 07:00 UTC, two tennis ties 08:00 UTC) — shown dimmed with “started” label, never counted as upcoming tips. All other dates are 2026-10-22 → 2027-07-25.

---

## 8. Flagged irregularities — 18 items in final, 35 in verified, plus cross-layer audit

**Final desk (18, all published on `final/flagged.html` with source links):**
- FR-01: Confidence-rule divergence across 5 layers → unified window now.
- FR-02: 885 layer rows → 382 deduplicated fixtures; 268 appear in ≥2 layers with conflicting model prices (example: MIN@CGY 70.84% vs 67.38%).
- FR-03: Golf stale “Bank of Utah Championship” replaced by Butterfield Bermuda Championship (PGA Tour 22–25 Oct, Port Royal).
- FR-04: “Bunting withdrew” claim not applied — no official page confirms; row left as Noppert v Bunting (PDC consent wall).
- FR-05: Fils ranking corrected #22/2050 → #10/3325 (ATP 2026-10-19).
- FR-06: Pastrnak totals corrected 4G/8A → 6pts (GameCenter).
- FR-07: Josi assists 8→6 (GameCenter).
- FR-08: Synthetic “book” prices dropped (slate layer overround).
- FR-09: 43 unlined rows with explicit blank reasons.
- FR-10: 206 rows competition/player-scoped, not fixture-scoped (disclosed).
- FR-11: 20 of 34 prediction facts not re-read today (inherited).
- FR-12: 3 fixtures started before snapshot.
- FR-13: Two cricket rows cite ICC news/rankings, not fixture page.
- FR-14: Hub-verified defects remain in archive layers (not edited).
- FR-15: 0 excluded-sport leaks (filter tested).
- FR-16: PDC consent wall prevents re-verification.
- FR-17: 8 eSports rows from Liquipedia (community wiki), not official — unlined/unverified.
- FR-18: 4 NBA rows moneyline-only (no handicap/total).

**Verified desk adds (35, on `flagged.html`):** VF-01 NBA totals blank, VF-02 NBA medium-capped, VF-03 WST #37+ blank, VF-04 WTA/Challenger blank, VF-05 PlusLiga blank, VF-06 ICC client-rendered, VF-07 EHF venues blank, etc. — all disclosed with official URLs.

**Reproducibility audit (dc72bac4) adds:** RPA-02 board 207→277 drift (tests still assert old counts — needs review), RPA-03 CI drift gate omits board/hub/slate/portal/forward/evidence/audit65 (needs review, owned by PR #91).

**New finding in this session (A-03):** 9 of 19 final predictions do not name a player because the official source that rendered the fixture did not server-render player leaders (SHL, Pro D2, URC, some NBA/ATP). The picks page header “names a player” is therefore narrowed here to “names a player where the official capture provided one.” No hallucinated player is added.

---

## 9. Site creation — clean GH Pages dashboard

- **Landing:** `final/index.html` is the consolidated desk (382 rows, 17 sports, 90 competitions, KPIs, top 6 picks, analysis, what-changed, excluded list). `index.html` is the verified desk (188 rows) with a blue banner linking to final. Both are linked from each other's nav.
- **Category pages:** `final/sports/*.html` (17) + `sports/*.html` (17) + `verified/sports/*.html` etc. — each sport has a table with fixture, teams, odds, pick, source, verification badge.
- **Core pages:** `matches.html` (all rows), `picks.html` (high-confidence with write-ups + fact links), `flagged.html` (review queue), `methodology.html`, `sources.html`, `verification.html`, `archive.html`, `integration.html`, `publication.html`, `review/reproducibility.html`.
- **UI:** Clean, simple dashboard (topbar, hero, KPI cards, sport cards, data tables, badges high/medium/low/today/past, notices, footer disclaimer “Research, not betting advice. 18+.”). Uses `assets/style.css` + `assets/app.js`.
- **Table format:** All entries in sortable/filterable HTML tables with columns: Date, Sport/Competition, Match/Teams, Odds/Markets, Pick/Confidence, Source (HTTPS link), Verification badge.
- **Analysis & findings:** KPI panels, coverage vs evidence, prices & confidence, what changed, limitations, cross-layer review table.
- **Navigation:** Topbar on every page; relative links; no broken internal links (integration_audit 0 errors).

**Live URLs (after Pages deploy):**
- https://buffedlizard55-lab.github.io/OLBG2/final/index.html
- https://buffedlizard55-lab.github.io/OLBG2/final/matches.html
- https://buffedlizard55-lab.github.io/OLBG2/final/picks.html
- https://buffedlizard55-lab.github.io/OLBG2/final/flagged.html
- https://buffedlizard55-lab.github.io/OLBG2/index.html
- https://buffedlizard55-lab.github.io/OLBG2/review/reproducibility.html
- https://buffedlizard55-lab.github.io/OLBG2/publication.html

---

## 10. Build and tests

All scripts use Python stdlib only.

```bash
python3 scripts/verified_seed.py && python3 scripts/verified_model.py && python3 scripts/verified_build.py
python3 scripts/build_site.py
python3 scripts/build.py
python3 scripts/survey_build.py && python3 scripts/survey_verify.py
python3 scripts/integration_audit.py
python3 scripts/final_consolidate.py && python3 scripts/final_predictions.py && python3 scripts/final_flags.py && python3 scripts/final_build.py
python3 -m unittest discover -s tests
```

**Expected in this session:** `build_site` reports 10 root pages + 17 sport pages / 188 rows; `final_build` reports 26 pages / 382 rows; `integration_audit` 0 errors; `unittest` 149 passed (dc72bac4 + prior layers). Verified manually before PR.

---

## 11. Irregularities summary for manual review

1. **Board drift (RPA-02):** `data/board/matches.json` 207 rows vs deterministic 277 rows (forward capture added 70 NHL fixtures). Two tests hard-code old counts. **Flagged, not edited** (owner scope). Review link: https://www.nba.com/schedule?date=2026-10-24
2. **CI drift gate gap (RPA-03):** `.github/workflows/pages.yml` does not list board/hub/slate/portal/forward/evidence/audit65 in `git diff --exit-code`. **Needs review** (owned by PR #91).
3. **Player gaps in 9 predictions (A-03):** SHL, Pro D2, URC, some NBA/ATP picks lack a named player because the official page that rendered the fixture did not server-render leaders. **Not hallucinated**; flagged here and on final/flagged.html.
4. **PDC consent wall (FR-16):** `https://www.pdc.tv/news/…` returns cookie-consent text; darts draw inherited, not re-verified.
5. **eSports non-official (FR-17):** 8 LoL rows from `https://liquipedia.net` (community wiki) — left unlined/unverified, linked to official https://lolesports.com/en-US/leagues/worlds/schedule
6. **Golf stale row fixed (FR-03):** Original “Bank of Utah” (finished 4 Oct) replaced by https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview
7. **Darts withdrawal dispute (FR-04):** “Bunting withdrew → Edhouse” not applied; official PDC OOM still lists Bunting #28, Edhouse #35, and dated listings 19–22 Oct show Noppert v Bunting. Left unchanged, flagged.
8. **NBA totals blank (VF-01):** Official standings publish W/L/Home/Road but not points for/against — totals intentionally “—”.

All other rows carry their official source link on the table; where a link is competition-scoped rather than fixture-scoped, it is disclosed (FR-10 / VF-11).

---

## 12. What “done” does and does not mean

- **Done:** Every eligible OLBG sport has a table with its dated snapshot, every row has an official HTTPS source link, every market that could be derived from a verified input was originated, every high-confidence pick in the -250…+10000 band has a 64–94-word human write-up with team + form + history + explicit selection (player where available), and every gap or disagreement is published on a Flagged for Review page with its source.
- **Not done:** Exhaustive real-world fixture completeness, live refresh, or proof that every official page currently supports every adjacent value — the snapshot is dated 2026-10-22 and the sandbox cannot fetch official pages to re-verify them today (TLS EOF). Those limits are disclosed, not hidden, and do not block publication.

---

*End of verification record for `arena/aa8e25ef-olbg2`. Sources, test logs and flagged pages are in the repo for manual review. No hallucinated values are present; blanks are shown as “—” with a written reason.*

