# Independent OLBG repository audit — 2026-10-23

**Scope.** Offline structural review of the merged 15-sport `/cadence/` publication, its underlying checked-in captures, and the root landing-page integration. This is not a fresh OLBG or governing-body source verification. Official domains are outside the current sandbox's outbound allowlist, so links below are supplied for manual review and no new external page content is claimed as checked.

## Summary

The repository already contains a built, multi-page desk for the exact requested sports at [`/cadence/`](../cadence/index.html), including a sport index, match and line tables, prediction cards, OLBG notes, methodology, sources and a Flagged for Review page. This audit independently ran its offline verifier and the repository suite. It found two actionable gaps and published them in the root [`Flagged for Review`](../flagged.html) page as `AUDIT-GREY-01` and `AUDIT-ODDS-02`:

1. **Greyhound source/year mismatch:** two records describe 2026 finals but cite a GBGB URL whose path says `2025-category-one-schedule`; the checked-in file is a summary of readings, not the official response. Dates and details remain unverified pending a current official schedule.
2. **Odds availability:** the cadence generator computes its `offered_*` columns from its own probabilities and code-defined margins. The checked-in capture set has no saved OLBG odds response for those lines. These values must not be interpreted as current bookmaker quotes or confirmation of OLBG availability.

The root dashboard now links directly to the exact-15-sport desk, both in the research navigation and its landing-page call-to-action. This does not make the snapshot live or independently verify its facts.

## Coverage snapshot from committed data

The desk verifier reports **93 fixtures across all 15 requested sports**, **728 originated prices**, **83 of 93 fixtures with prices**, **122 graded selections**, **33 written predictions**, **59 registered source URLs**, and **19 combined review items** (three desk flags plus 16 repository-audit findings). These are counts in the 2026-10-23 snapshot, not newly observed live counts.

| Sport | Fixtures | Ranked picks | Written predictions | Official source recorded in capture (not freshly fetched here) |
|---|---:|---:|---:|---|
| Golf | 2 | 5 | 0 | [PGA TOUR leaderboard](https://www.pgatour.com/leaderboard) |
| Volleyball | 10 | 5 | 3 | [Lega Pallavolo calendar](https://www.legavolley.it/calendario/?idCampionato=999) |
| Rugby Union | 8 | 5 | 1 | [Premiership Rugby fixtures](https://www.premrugby.com/fixtures-results) |
| Cricket | 6 | 5 | 5 | [Cricket Australia matches](https://www.cricket.com.au/matches?isCompleted=0&year=2026) |
| Snooker | 8 | 3 | 1 | [World Snooker Tour matches](https://www.wst.tv/matches/) |
| Darts | 8 | 5 | 3 | [PDC event preview](https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/) |
| Baseball | 2 | 2 | 1 | [MLB schedule API](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-11-02) |
| Gaelic Sports | 5 | 5 | 0 | [GAA fixtures and results](https://www.gaa.ie/fixtures-results) |
| Greyhounds | 2 | 5 | 0 | [GBGB page cited by capture — year mismatch flagged](https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/) |
| Tennis | 5 | 5 | 1 | [ATP Tour Almaty schedule](https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule) |
| Motor Racing | 2 | 5 | 1 | [Formula 1 United States Grand Prix](https://www.formula1.com/en/racing/2026/united-states) |
| Handball | 6 | 5 | 4 | [LNH calendar](https://www.lnh.fr/daikin-starligue/calendrier) |
| Ice Hockey | 2 | 3 | 3 | [NHL schedule API](https://api-web.nhle.com/v1/schedule/2026-10-23) |
| Basketball | 18 | 5 | 5 | [NBA games](https://www.nba.com/games?date=2026-10-23) |
| Rugby League | 9 | 5 | 5 | [NRL draw](https://www.nrl.com/draw/?competition=131&round=2&season=2026) |

**Prediction-target shortfalls:** only Basketball, Cricket and Rugby League have five written predictions. Three sports (Golf, Greyhounds, Gaelic Sports) have none; the other nine sports have one to four. The desk explains that it did not generate prose where it considered evidence insufficient, but this does not meet the requested five-predictions-per-sport target. Ranked-pick count is distinct from prediction count.

The desk also documents that its ≥70% confidence and fair-odds −250…+10000 constraints overlap only from 70.00% to about 71.43%. Its odds-band flag is computed from the desk's **fair** price; this must not be conflated with actual bookmaker or OLBG offered odds. See [`band board`](../cadence/band.html) and the `AUDIT-ODDS-02` review row.

## Validation performed

- `python3 scripts/cadence_verify.py` — **11 check groups passed, 0 errors**. Checks include the exact sport set, row/source-link presence, sourced facts, line arithmetic, confidence and band consistency, prediction length/uniqueness/prohibited terms, table structure, and local links. This is a deterministic check of committed files; it does **not** fetch or validate the live content of the linked pages.
- `python3 scripts/integration_audit.py` — **0 cross-layer local-link errors** (explicitly structural only).
- `python3 -m unittest discover -s tests -v` before this audit's additions — **662 tests passed**; after adding the two root integration tests — **664 tests passed**.
- `python3 scripts/build_site.py` — generated the root pages deterministically; the new landing-page links resolve to the existing cadence index.
- Latest GitHub `main` Pages deployment at the time of audit — succeeded for merge `8b4435f` ([Deploy Pages run 40026534146](https://github.com/buffedlizard55-lab/OLBG2/actions/runs/40026534146)). This confirms deployment status, not the accuracy or freshness of external sports facts.

## Source links for manual review

Each sport table row above links to the URL recorded as its official fixture source in the capture. The full source register, fixture-specific source links, raw summary captures, methodology, predictions and unresolved issues are available from the [`Cadence sources page`](../cadence/sources.html), [`all matches`](../cadence/matches.html), [`predictions`](../cadence/predictions.html), [`repository audit`](../cadence/audit.html), and [`Cadence Flagged for Review`](../cadence/flagged.html). The two independent findings from this audit are also published on the root [`Flagged for Review`](../flagged.html) page.

## Limits and integrity notes

- No match date, result, ranking, injury, market price or prediction in this report was newly confirmed against a live official page. The report relies on committed data and validators; source links are for manual review.
- A URL being HTTPS, registered, or rendered in a row does not prove it supports every adjacent claim. The verifier establishes link and data structure, not source semantics.
- The repository has numerous overlapping desk layers. Their row counts are not additive; use `/cadence/` for this exact 15-sport snapshot and read its capture date and flags.
- The snapshot is dated 23 October 2026 and must not be treated as a live feed. Later fixtures, postponements, injuries, prices or results can invalidate it.
