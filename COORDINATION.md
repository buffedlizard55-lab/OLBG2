# COORDINATION.md — Shared Task Board (OLBG2)

This file is the single source of truth for multi-session coordination on this repository.
Any agent session working here must read this file first, claim a task by writing its
session ID and file scope, then commit and push that claim **before** editing anything.

## Conventions

- **Session ID**: short id taken from the working branch name.
- **Branch**: Arena-managed sessions are pinned to their own `arena/<id>-*` branch by the
  platform and cannot create `session-<id>/<task>` branches. Where that applies, the
  `arena/<id>-*` branch **is** that session's isolated worktree-equivalent, and the file
  scope below is what keeps sessions non-overlapping.
- **Claim rule**: never start a task another session has claimed.
- **Commit rule**: small, frequent commits; `git pull --rebase` before every push.
- **Verification rule**: nothing is marked `verified` without an official-source link.
  Values that cannot be confirmed are left blank and flagged `unverified`.
- **Shared outputs** (`docs/index.html`, `docs/_data/*`, site navigation, merged tables)
  are touched only by the final integration session.

## Status legend

| Status | Meaning |
| --- | --- |
| `unclaimed` | Nobody has started it. |
| `in progress` | An owning session is actively working it. |
| `needs review` | Published on the **Flagged for Review** page. Does **not** block anything. |
| `done` | Finished, sources + verification recorded below. |

---

## Task board

| # | Task | Status | Owner (session) | Files in scope |
| --- | --- | --- | --- | --- |
| T1 | Repository review + baseline audit of existing content | in progress | `ca1d5677` | `docs/audit/*`, `REPO_REVIEW.md` |
| T2 | Build OLBG sport registry; decide include/exclude per brief | in progress | `ca1d5677` | `data/sports.json` |
| T3 | Collect event lists for all included sports from OLBG | in progress | `ca1d5677` | `data/events/*.json` |
| T4 | Collect official ratings/standings inputs (per sport) | in progress | `ca1d5677` | `data/ratings/*.json` |
| T5 | Originate our own lines (ML / handicap / total) from T4 inputs | in progress | `ca1d5677` | `data/lines.json`, `scripts/originate_lines.py` |
| T6 | Pick match winner + low/medium/high confidence per match | in progress | `ca1d5677` | `data/picks.json` |
| T7 | Write 30+ word human predictions for high-confidence picks | in progress | `ca1d5677` | `data/predictions.json` |
| T8 | Build GitHub Pages site (landing + category subpages + tables) | in progress | `ca1d5677` | `docs/**`, `scripts/build_site.py` |
| T9 | Verification pass: every row has an official source link or is flagged | in progress | `ca1d5677` | `docs/verification.html`, `scripts/verify.py` |
| T10 | Flagged-for-Review page (irregularities + unverified items) | in progress | `ca1d5677` | `data/flags.json`, `docs/flagged.html` |
| T11 | Integration: build check, link check, publish Pages, open + merge PR | in progress | `ca1d5677` | `docs/**`, `COORDINATION.md` |

No other session has claimed any task in this repository at the time of writing.
Any session picking up work must add its row here and push immediately.

---

## Log

| Timestamp (UTC) | Session | Entry |
| --- | --- | --- |
| 2026-10-21 | `ca1d5677` | Board created. Repo at `1056f6a` contained only a 7-byte `README.md` (`# OLBG2`) — no data, no code, no site. Claimed T1–T11 as a single-session run. |
| 2026-10-21 | `ca1d5677` | Environment note: sandbox `bash` egress is restricted to github.com / pypi.org / npmjs.org, so `curl olbg.com` fails. Collection and verification run through the harness `fetch_page` / `web_search` tools, which **do** reach olbg.com and official governing-body sites. Logged as irregularity **F-01**. |
| 2026-10-21 | `ca1d5677` | Environment note: OLBG event pages render bookmaker prices client-side; the served HTML exposes `WIN @` with an empty price. Decimal prices therefore cannot be captured, so lines are originated from official ratings instead of de-vigging book prices. Logged as irregularity **F-02**. |

---

## Decisions requiring human review

Tracked in detail in `data/flags.json` and published at `docs/flagged.html`. Headline items:

- **F-03** Ambiguous exclusions: `Greyhounds` and `Gaelic_Football` are not named in the
  brief's exclusion list but are racing / football-code sports. Both excluded; review needed.
- **F-04** `Motor_Racing` is included (brief excludes `cycling`, not motorsport).
- **F-05** OLBG has no separate `UFC` / `MMA` / `Hurling` / `Specials` sport node in its
  sitemap, so those exclusions are vacuous.

---

## Completion record

Filled in by the integration session (T11) once all tasks are done.

| Field | Value |
| --- | --- |
| Sources used | _pending_ |
| Verification performed | _pending_ |
| Irregularities | _pending_ |
| PR link | _pending_ |
| Merge result | _pending_ |
| Pages deploy | _pending_ |
