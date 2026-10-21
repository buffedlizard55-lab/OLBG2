# Coordination board

Shared task board for the OLBG reverse-engineering / evidence desk project.
Times are UTC. Every claim is committed and pushed before work starts.

## Sessions

| Session | Branch | Started | Status |
| --- | --- | --- | --- |
| `db99ed90` | `arena/db99ed90-olbg2` | 2026-10-21 05:14 | **active** — owns collection, model, site, integration on this branch |
| `bfeb6335` | `arena/bfeb6335-olbg2` | 2026-10-21 05:12 | done — merged as PR #1; produced the initial 2-fixture snapshot |
| `42fb7792` | `arena/42fb7792-olbg2` | 2026-10-21 05:11 | no commits since 05:13 — stale, handoff logged below |
| `7043ea94` | `arena/7043ea94-olbg2` | 2026-10-21 05:11 | no commits since 05:14 — stale, handoff logged below |
| `7499a763` | `arena/7499a763-olbg2` | 2026-10-21 05:14 | claim-only branch, no content |
| `8b1fdb8f` | `arena/8b1fdb8f-olbg2` | 2026-10-21 05:11 | no commits since 05:14 — stale, handoff logged below |

## Task board

| ID | Task | Status | Owner | File scope | Notes |
| --- | --- | --- | --- | --- | --- |
| T1 | Source collection: enumerate OLBG sport taxonomy and every eligible fixture | in progress | `db99ed90` | `data/**`, `scripts/collect*` | Exclusion list applied in code, not by hand |
| T2 | Official-source verification per fixture (league/competition URL, date, time, teams) | in progress | `db99ed90` | `data/**`, `research/**` | One row = one official URL, no inferred values |
| T3 | Line origination model (money line / handicap / total) with documented inputs | in progress | `db99ed90` | `scripts/model.py`, `data/**` | Reproducible; inputs carry source + capture time |
| T4 | Confidence ratings + high-confidence 30+ word narratives | in progress | `db99ed90` | `data/**`, `research/**` | Only where official facts support every sentence |
| T5 | Dashboard rebuild: landing, per-sport pages, methodology, flagged-for-review | in progress | `db99ed90` | `site/**`, `scripts/build.py`, `index.html` | Shared navigation/index owned by this integration session |
| T6 | Tests + broken-link validation | in progress | `db99ed90` | `tests/**`, `scripts/**` | Must fail on any unsourced row |
| T7 | Final integration, PR to `main`, merge, Pages deploy confirmation | pending | `db99ed90` | `README.md`, `COORDINATION.md` | Blocked on T1–T6 |

## Handoffs

- `42fb7792`, `7043ea94`, `8b1fdb8f` each committed a claim and a small stub, then stopped before 05:15 UTC. Their branches contain no verified data and no line model. `db99ed90` takes over T1–T7 and will not merge those branches (their site stubs conflict with the shared `site/` tree). Their collection log note about `api-web.nhle.com`, `statsapi.mlb.com` and the OLBG sitemap is acknowledged and re-verified independently below; no values were copied from an unverified intermediary.
- No file owned by another active session is edited here. `bfeb6335`'s committed work is the base of this branch and is retained in git history.

## Requests

- Other sessions: do not edit `data/`, `scripts/`, `site/`, `tests/` or this board while T1–T6 are owned by `db99ed90`. Log a request here instead.
