# /pulse/ desk — collection & reverse-engineering log (session arena/5fba1c42-olbg2)

Date of capture: **2026-10-22, ~09:30–12:55 UTC**. All fetches were first-hand, via the
platform page-fetcher (sandbox `curl` is blocked for most hosts). This document is the
permanent record of how OLBG's eligible-sport surface was mapped, what was verified,
what failed, and how the `/pulse/` layer was produced.

## 1. OLBG reverse engineering (target-site mechanics)

### 1.1 Sport taxonomy
- `olbg.com/betting-tips/` hub lists each sport with URL pattern `/betting-tips/<Slug>/<id>`
  (historic ids: Football/1, Horse_Racing/2, …, Darts/15, Ice_Hockey/19, Handball/20,
  Volleyball/21, Gaelic/25, Greyhounds/28). Eligible-sport list for this desk = the 17
  named in the brief; excluded sports (football/soccer incl. all leagues, American
  football, horse racing, boxing, UFC/MMA, cycling, hurling, specials) are never collected.
- Tips pages are community-tip listings — percentages are **not** market prices and were
  not used as probabilities anywhere in the model.

### 1.2 Event URL schema
Individual events expose URLs `/betting-tips/<Sport>/<slug>/tips/<event_id>` e.g. darts
event ids 32324/32330/32334/32325 observed for tonight's PDC European Championship R1.
Market shapes confirmed on those pages (darts): Win Match (2-way), Handsicap ±1.5 legs,
Total Legs 9.5 (best of 11). Handball/handicap and hockey puck-line shapes mirror the
same three-market pattern (win/handicap/total), which is what the desk originates.

### 1.3 Irregularities found on OLBG (recorded, not "fixed")
| Finding | Detail | Flag |
|---|---|---|
| Time labels drift vs official | Montauban v Oyonnax labelled 15:00 on OLBG while official LNR lists 21h00 local | PU-05 |
| Event naming | "USA Grand Prix" on OLBG vs official "United States Grand Prix" (R18, COTA, 23–25 Oct) | PU-17 |
| No integrity problem | tips % is community sentiment, presented prominently; treated as non-evidence | — |

## 2. Verification log per sport (first-hand captures)

| Sport | Official source | Result |
|---|---|---|
| Ice Hockey | `api-web.nhle.com/v1/score/2026-10-22` + `api.nhle.com/stats/rest/en/team/summary` | 12 games tonight; all 32 teams' GP/GF/GA cross-checked against score-feed records; league odds-partner prices recorded as context (PU-02) |
| Basketball | `nba.com/game/...` pages for 0022600006/7 | fixtures verified; season 1 game old → no team-strength inputs → **blank lines + PU-01** |
| Baseball | `statsapi.mlb.com` schedule + standings | World Series confirmed: Rays (98-64, RS 736/RA 650) at Brewers (103-59, 832/618), G1 23 Oct, G2 24 Oct, G3 26 Oct |
| Darts | pdc.tv 19 Oct schedule-confirmed + 21 Oct preview (rendering blocked by CookieYes → extracted via search-engine cache of the official articles) | 8 R1 matches 19:00 CEST, official 1–32 ET seeds, best of 11 + neutral venue; OLBG event pages 32324/5/30/34 match |
| Handball | `ehfcl.eurohandball.com/men/2026-27/{matches,standings}/` | 5 fixtures tonight + full group tables A–F with GF/GA |
| Snooker | `wst.tv/matches/b4533c9e-8d2c-4ecc-8dfd-c6b284705578` | NI Open R3 today; 2 matches live at capture excluded (PU-04); R1/R2 frame records for all 12 active players |
| Tennis | `atptour.com` current + Almaty daily-schedule | two schedulable R16 matches with official seeds; unseeded proxy documented (PU-14) |
| Rugby Union | `prod2.lnr.fr/calendrier-et-resultats` | full J8 card (1 tonight + 7 Friday), official positions 1e–16e per fixture |
| Cricket | ICC match 271646 + series news | 2nd T20I Sat 24 Oct registered; strengths blank + PU-03 |
| Motor Racing | `formula1.com/en/racing/2026` (chunks 0–1) | US GP 23–25 Oct; official R1–R16 winners/podiums captured; gaps R17 + R7 P3 flagged (PU-06) |
| Golf | europeantour.com | site banner confirms Genesis Championship in progress ("Round 2 Tee Times Available"); leaderboard pages 404/app-shell → blank + flag |
| Esports | lolesports Worlds 2026 primer | stage dates verified (Swiss from 23 Oct); Swiss R1 pairings not on the official page → blank + flag |
| Gaelic Football | gaa.ie/fixtures-results | October surface shows only Shinty–Hurling International (hurling = excluded) → no fixture, flag |
| Volleyball | en.volleyballworld.com | `/volleyball/` path 404s; no verifiable fixture list server-side → flag |
| Rugby League | nrl.com/draw | not captured first-hand this session → flag |
| Aussie Rules | afl.com.au/fixture | same → flag |
| Greyhounds | gbgb.org.uk results | JS-only page → flag |

## 3. What the numbers say (desk findings)

- **48 fixtures** across 10 sports: NHL 12, Pro D2 8, darts 8, snooker 6 (R3), EHF 5,
  MLB 3 (WS G1–G3), NBA 2 (blank), ATP 2, ICC 1 (blank), F1 1. 141 originated market rows.
- **Band geometry:** high = p ≥ 0.70 AND −250 ≤ fair ≤ +10000 ⇒ for favourites the window
  is only 70.00%–71.43%. Tonight exactly **one** selection qualifies: Ottawa ML 70.4%
  (fair −238) v San Jose. Boston (73.1%), Dallas (72.2%), Agen (71.9%) all clear 70% but
  price heavier than −250 → medium per the brief's own framing; Toronto +1.5 puck line at
  69.97% misses by 0.03% and is documented verbatim rather than rounded.
- **Market-implied check:** the NHL's official partner prices carry no favourite at −250 or
  shorter tonight (max: Dallas/Minnesota −205), so no "market 70%" pick exists — the single
  high pick is model-driven. PU-02 keeps partner prices out of the model.
- Toronto +1.5 at 69.97% is published as medium and cited on the band-audit table as the
  closest miss — an honesty artefact of deterministic rounding.

## 4. Model notes (matching METHODOLOGY page)

- NHL/EHF: independent Poisson, λ = GF×GA_opp/L × home edge (NHL 1.045, EHF 1.03), league
  averages computed live from the captured official tables (NHL L = 942/306 = 3.078).
- NHL OT share 0.55 documented; puck line uses the regulation grid only (OT/SO wins are
  one-goal margins), so −1.5 excludes OT wins by construction.
- Darts: rating = seed^(−1.15), leg p capped at [0.30, 0.70] after first run produced a
  degenerate p = 1.0000 for the 1 v 32 seed pairing (constant documented with cap, PU-16).
- MLB: log5 on blend(actual W%, Pythagorean ×2) → MIL 58.9% home (G1/G2), 55.9% on the
  G3 road flip; run line & total deliberately not originated (no verified probable
  pitchers → PU-19).
- Pro D2: margin ~ N(3.5 + 1.35×Δpos, 13) — Provence v Béziers is the biggest number
  (93.5%) while Szeged v GOG is tonight's tightest handball line (57%).
- Sensitivity on the featured pick is published on the methodology page (home edge and
  OT share swings move it across the band boundaries in both directions).

## 5. Failures and dead ends (do-not-retry list)

- NBA cdn JSON endpoints → HTTP 500; nba.com/games calendar broken — game pages render fully.
- pdc.tv blocks direct fetch (CookieYes JS wall) — official text recovered via search cache.
- icc-cricket.com/matches and /matches/upcoming → 404; find match pages via search.
- lnr.fr/prod2/... and prod2.lnr.fr/calendrier → 404; canonical is
  prod2.lnr.fr/calendrier-et-resultats.
- europeantour.com leaderboard paths → 404/app-shell.
- gbgb.org.uk results page renders zero rows server-side (JS-only).
- en.volleyballworld.com/volleyball/ → 404.
- unitedrugby.com/match-centre/2026-27/ → 404 (stats.unitedrugby.com is the live surface;
  URC is ineligible anyway — rugby league, not union, had no verified deadline-relevant
  fixture set captured first-hand; left flagged).

## 6. Layer inventory

- `data/pulse/inputs.json` — frozen first-hand inputs with per-row URLs.
- `data/pulse/matches.json`, `flagged.json`, `predictions.json` — generated by
  `scripts/pulse_model.py` (stdlib-only, deterministic — byte-identical on re-run;
  regression-tested) and the hand-verified predictions file.
- `pulse/` — 17 static pages (dashboard, all-matches, picks, sports/*, flagged, sources,
  methodology), zero external assets.
- `scripts/pulse_verify.py` + `tests/test_pulse_5fba1c42.py` (22 checks) — integrity gate.
