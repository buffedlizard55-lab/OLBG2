# Coordination board

Shared task board for the OLBG reverse-engineering / evidence desk project.
Times are UTC. Every claim is committed and pushed before work starts.

## Sessions

| Session | Branch | Started | Status |
| --- | --- | --- | --- |
| `db99ed90` | `arena/db99ed90-olbg2` | 2026-10-21 05:14 | **active** — collection, model, site, integration |
| `bfeb6335` | `arena/bfeb6335-olbg2` | 2026-10-21 05:12 | done — merged as PR #1; produced the initial 2-fixture snapshot |
| `42fb7792` | `arena/42fb7792-olbg2` | 2026-10-21 05:11 | no commits since 05:13 — stale, handed off |
| `7043ea94` | `arena/7043ea94-olbg2` | 2026-10-21 05:11 | no commits since 05:14 — stale, handed off |
| `7499a763` | `arena/7499a763-olbg2` | 2026-10-21 05:14 | claim-only branch, no content |
| `8b1fdb8f` | `arena/8b1fdb8f-olbg2` | 2026-10-21 05:11 | no commits since 05:14 — stale, handed off |

## Task board

| ID | Task | Status | Owner | File scope | Notes |
| --- | --- | --- | --- | --- | --- |
| T1 | Source collection: OLBG taxonomy + every eligible fixture | done | `db99ed90` | `data/**` | 16 eligible categories identified from OLBG's betting-tips sitemap |
| T2 | Official verification per fixture | done | `db99ed90` | `data/**` | 14 NHL fixtures, each with official game page + official feed |
| T3 | Line-origination model | done | `db99ed90` | `scripts/model.py` | `olbg-desk-poisson-v1`, reproducible, parameters declared in data |
| T4 | Confidence ratings + high-confidence narratives | done | `db99ed90` | `data/**` | 6 high, 3 medium, 5 low; narratives 54–60 words, all unique |
| T5 | Dashboard + category pages + methodology + sources + flagged | done | `db99ed90` | `site/**`, `scripts/build.py`, `index.html` | 22 generated pages |
| T6 | Tests + broken-link validation | done | `db99ed90` | `tests/**` | 23 tests passing |
| T7 | Final integration, PR to `main`, merge, Pages deploy | in progress | `db99ed90` | `README.md`, `COORDINATION.md` | Recorded at the bottom of this file |

## Handoffs

- `42fb7792`, `7043ea94`, `8b1fdb8f` each committed a claim and a small stub, then stopped before 05:15 UTC. Their branches contain no verified data and no line model. `db99ed90` took over T1–T7 and did not merge those branches: their pages collide with the shared `site/` tree and contain no sourced rows. Their note that `api-web.nhle.com` and `statsapi.mlb.com` respond was re-verified independently; no values were copied from an unverified intermediary.
- No file owned by another active session was edited. `bfeb6335`'s committed work is in this branch's history.

## Requests

- Other sessions: `data/`, `scripts/`, `site/`, `tests/` and this board were owned by `db99ed90` for the duration of T1–T7. Log a request here rather than editing.

---

## Source and verification log — 2026-10-21

Every value in `data/events.json` was read from one of the URLs below during this session and copied without arithmetic.
Derived numbers (lambdas, probabilities, prices) are computed by `scripts/model.py` and are reproducible with `python scripts/build.py`.

| Source | What was taken | Rows |
| --- | --- | --- |
| `https://www.olbg.com/betting-tips` | Global event list, sport menu, taxonomy | coverage |
| `https://www.olbg.com/sitemap-betting-tips.xml` | OLBG sport ids (1–28) used for the exclusion list | coverage |
| `https://www.olbg.com/betting-tips/Ice_Hockey/13` | OLBG's NHL listing: 2 events (199897, 199896) plus Austria EHL and SHL fixtures | 2 |
| `https://www.olbg.com/betting-tips/Basketball/NBA/NBA/MIL_Bucks_@_WAS_Wizards/4?event_id=534889` | OLBG NBA listing used in the basketball gap | 0 |
| `https://api-web.nhle.com/v1/schedule/2026-10-21` | 2 games on 2026-10-21, 12 on 2026-10-22, start times in UTC | 14 |
| `https://api-web.nhle.com/v1/gamecenter/{id}/right-rail` | Goals for/against per game, PP/PK %, faceoff %, ranks, last-ten record, listed results, head coaches | 14 |
| `https://api.nhle.com/stats/rest/en/team` | Official full club names | 26 |
| `https://www.nhl.com/gamecenter/{slug}/{date}/{id}` | Human-readable official game page linked per row | 14 |
| `https://nba.com/games` | 11 games on 2026-10-21 and 2 on 2026-10-22, matchups not rendered | 0 |
| `https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-21` | `totalGames: 0` for 2026-10-21 | 0 |
| `https://www.icc-cricket.com/fixtures-results` and `/matches/271646/new-zealand-vs-india` | Upcoming cricket fixtures; no date field exposed | 0 |
| `https://www.atptour.com/en/scores/current` | In-progress/completed tennis matches; no dates | 0 |
| `https://www.premiershiprugby.com/fixtures` | HTTP 404 (site moved to `premrugby.com/fixtures-results`) | 0 |

### Checks performed

- 14/14 fixtures: teams, date and start time compared field by field against the official feed; `start_utc` cross-checked against the fixture date (allowing the next UTC day for evening face-offs).
- 26/26 club names matched against the official NHL team list, not written from memory.
- 14/14 picks recomputed from the model and asserted equal to the stored selection and confidence by `validate()`.
- 6/6 high-confidence narratives checked for ≥30 words (actual 54–60), uniqueness, and that the selection is named in the text.
- Coverage board row counts asserted equal to the fixture list at build time.
- `python -m unittest discover -s tests -v` → 23 passing.
- `python scripts/build.py` → 22 pages, every local link resolved by `test_generated_local_links_resolve`.

## Irregularities and limitations

- **OLBG times vs NHL times.** OLBG displayed both NHL fixtures at 00:37 the following day; the NHL feed gives 23:30Z. OLBG states no timezone in the retrieved text. The league time is published; the OLBG time is recorded unmodified on the Flagged page.
- **OLBG lists 2 of 14 NHL games.** The other 12 have no individual OLBG event page; they link to OLBG's NHL index and carry `olbg_listed: false`.
- **European ice hockey not covered.** OLBG listed Austria EHL and Swedish SHL fixtures. No official league feed was verified for them in this session, so they are named on the Flagged page with no row.
- **NBA blocked.** Four machine-readable NBA endpoints failed (HTTP 500 / AccessDenied / no response) and the official games page would not render matchups. No NBA row published.
- **Cricket and tennis have no dates in the retrievable text**, so no fixture could be dated. Recorded as a coverage gap, not as an absence of fixtures.
- **LAK last-ten record inconsistent** in the NHL payload (1-4-2 with seven listed results). Reproduced verbatim; flagged.
- **Model parameters are assumptions**, not league statistics: home 1.05 / away 0.95, 50/50 tie split, confidence edges 10 and 6 points. Documented on the methodology page and in `data/events.json`.
- **Model scope:** no rest/back-to-back, injury, goaltender, travel or score-effect adjustment; no market comparison, so no value claim.

## Integration and publication

- PR and merge result: recorded below once created.
- GitHub Pages is configured for legacy publication from the `main` branch root (`gh api repos/.../pages` → `build_type: legacy`, `source: main:/`). The root `index.html` redirects to `site/index.html`, so a merge to `main` publishes the desk without changing repository settings.
- CI (`.github/workflows/pages.yml`) validates the snapshot, rebuilds the site and fails if the committed `site/` is stale. Triggers widened to every branch so the work branch is checked before merge.
