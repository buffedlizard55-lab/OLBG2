# Gap re-check — session `arena/1619553b-olbg2` (2026-10-22 UTC)

Scope: re-test the two blocked gaps left open by `arena/6a87eefa-olbg2` (VF-14, VF-22) against the official
sources, using each site's real navigation. No values were published from this check; nothing was inferred.

## VF-22 — GBGB greyhound cards (gbgb.org.uk)

| Step | URL fetched (official) | Result (fetched 2026-10-22) |
|---|---|---|
| Guessed path (earlier session's assumption, now known wrong) | https://www.gbgb.org.uk/racing/fixtures/ | HTTP-level 404 page ("PAGE NOT FOUND") — this path does not exist |
| Official homepage | https://www.gbgb.org.uk/ | Reachable. Links to "View Open Races" and "See all results". |
| Open races | https://www.gbgb.org.uk/racing/open-races/ | Reachable. Calendar (October 2026) and filters render; **no race list in the server-rendered HTML**. Links to a "2026 Category One Schedule" (`/racing/open-races/2025-category-one-schedule/`) and "2026 Category Two Schedule" (`/2025-category-two-schedule/`). |
| Racecourses | https://www.gbgb.org.uk/racing/race-courses/ | Reachable. Lists track names, contact details and race-day patterns (weekly), **not** dated race cards. |
| Results | https://www.gbgb.org.uk/racing/results/ | Reachable. Shows "0 items in 0 pages" in the captured HTML; results are loaded by script. |

**Outcome: VF-22 remains OPEN (blocked).** GBGB is reachable and its track list and race-day patterns are
official, but dated card entries are loaded client-side and were not returned in the captured HTML.
No greyhound row is published. The Category One/Two schedule documents were not opened in this pass and
are a candidate for a later session.

## VF-14 — NBA 22–24 Oct fixture list (nba.com)

| Step | URL fetched (official) | Result (fetched 2026-10-22) |
|---|---|---|
| Games page for 23 Oct | https://www.nba.com/games?date=2026-10-23 | Calendar counts only (22 Oct: 2 games, 23 Oct: 12, 24 Oct: 8). Body: "Sorry, something went wrong. Please refresh the page." — **no fixture list**. |
| Season schedule | https://www.nba.com/schedule?season=2026 | Page shell and filters only; **no game rows** in the captured HTML. |

**Outcome: VF-14 remains OPEN (blocked).** Per-day counts are official and consistent with the earlier capture,
but no team pairing, tip time or game id can be read from the server-rendered page. No NBA row is published.

## Irregularities noticed in this pass (for review, not corrected here)

- The earlier flag text for VF-22 described the GBGB site as returning 500 on all pages. This pass shows the
  homepage and track/results pages return normally; the earlier failure is therefore **not reproducible** and
  the flag should be reworded to "dated cards not server-rendered" (logged for the flag owner, not edited here).
- The NBA calendar's "Sorry, something went wrong" message appears on the official page itself.
