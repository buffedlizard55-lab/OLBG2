# Coordination board

Session identifier: `arena/7043ea94-olbg2` (the Arena branch is fixed; no other session/worktree was available in this checkout).

| Task | Status | Owner session | File scope | Notes |
|---|---|---|---|---|
| Static dashboard foundation, OLBG workflow notes, and explicit verification/coverage flags | done | `arena/7043ea94-olbg2` | `index.html`, `sports.html`, `sports/*`, `markets.html`, `methodology.html`, `flagged.html`, `assets/*`, `scripts/*`, `README.md`, `COORDINATION.md`, `.github/workflows/*` | Complete as a transparent static research dashboard, not as a complete live fixture/lines/picks dataset. Five observed category examples have profile pages and scoped first-party schedule-source links. No match or betting claims are populated. |

## Handoff / activity log

- Request to integration owner/session `bfeb6335`: consider adding the official schedule entry-point links and scope caveats documented below to the published category/reference pages when integrating further sport coverage. This session did not edit the merged `site/**`, `data/**`, or main-branch Pages workflow.
- 2026-10-21 — Inspected the repository; it initially contained only `README.md`, with no prior coordination board or other claimed tasks. Created this board, claimed the dashboard/source-verification framework scope, committed the claim (`3dab71c`), and pushed it to `arena/7043ea94-olbg2`. `git pull --rebase origin arena/7043ea94-olbg2` initially could not find a remote ref because the branch had not yet been pushed; the immediate push created the remote branch successfully.
- 2026-10-21 — Built a responsive static dashboard with Overview, Sports Coverage, five sport-detail pages, Markets & Lines, Methodology, and Flagged for Review. Added a Pages Actions workflow and a dependency-free local-link/page check. No event/market tables were published because no match-level record was verified.
- 2026-10-21 — Ran `python3 scripts/check_site.py` and `git diff --check`; both passed. Link checker found all local page/assets links and required files; there are no data tables requiring row-level source audit. External first-party references below were opened directly during research.
- 2026-10-21 — After the dashboard branch was pushed, fetched `origin/main` and discovered another active session had already merged PR #1 (data pipeline/dashboard) and PR #3 (publication verification), with overlapping ownership of the shared site, Pages workflow, README, and coordination board. Their main-branch site includes source-verified NHL rows and a generated Pages architecture; the board records that legacy Pages deployment succeeded. Closed this session's duplicate PR #2 rather than overwrite the integrated site or invalidate its deployment. No changes from this session were merged to `main`. Optional official calendar entry-point research in this branch can be offered to the integration owner, but should not be added to their shared pages/data without coordination.

## Verification log

OLBG reference (first-party site, used only to describe OLBG's presentation and observe category/market labels):
- https://www.olbg.com/betting-tips — inspected 2026-10-21. The page describes 20+ sports and its rendered examples included darts, snooker, handball, basketball, and Gaelic football. Example market labels visible in that listing included Win Match 2-way and Money Line. This source does not verify an official event schedule, match facts, current form, original lines, or picks.

Official first-party schedule entry points opened on 2026-10-21 and linked from the matching sport-detail page:
- Darts / WDF only: https://dartswdf.com/calendar — WDF's official calendar page, with filters/categories and linked event details. It is not treated as exhaustive coverage of all darts organizers or match-level draws.
- Snooker / WPBSA group: https://www.wpbsa.com/events-list/ — WPBSA events calendar. It describes event dates/venues and explicitly marks dates provisional; tournament-level calendar text is not transcribed into match rows.
- Handball / IHF competitions: https://www.ihf.info/competitions — official IHF competition listings; not a full inventory of every domestic or club handball league.
- Basketball / NBA only: https://www.nba.com/schedule — NBA's official game schedule; not a full inventory of world basketball competitions.
- Gaelic football / GAA: https://www.gaa.ie/fixtures-results — official GAA fixtures/results page with football and hurling filters. Because hurling is excluded and the user's separate “football” exclusion makes Gaelic football classification ambiguous, this category remains flagged and contains no event records.

No event rows, prices, originated lines, odds, athlete form statements, confidence labels, picks, or generated predictions were verified or entered. Their blank/absent status is deliberate and documented on the site. The listed official schedule URLs are source entry points, not confirmation that the requested full event slate has been assembled.

## Irregularities / outstanding work

- Complete OLBG sport/competition taxonomy and the current match-level fixture slate remain unaudited. The five category examples are not exhaustive; the OLBG page itself says 20+ sports.
- Match-by-match verification against official organizer/league/team/athlete sources remains outstanding for every supported sport.
- No independently reproducible line-generation model, market availability/settlement audit, confidence calibration, or verified form/history research exists yet. Accordingly, no picks or high-confidence predictions are fabricated or published.
- Darts calendar scope must be broadened beyond WDF where appropriate; WPBSA, IHF, NBA, and GAA links have explicit sport/competition limitations. The GAA “football” scope ambiguity is flagged.
- Static site links are locally checked; external first-party pages were manually opened, but an automated external-link monitor or recurring data refresh is not configured.
- The GitHub Pages workflow in this duplicate dashboard branch was not deployed. Separately, the integration already present on `origin/main` has its own Pages configuration, merged PRs #1 and #3, a successful deployment recorded on the main coordination board, and live dashboard at https://buffedlizard55-lab.github.io/OLBG2/site/. This session's PR #2 was closed to protect that output; do not describe this branch as merged or deployed.
