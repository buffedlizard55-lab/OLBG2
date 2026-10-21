# COORDINATION — OLBG2 multi-session task board

**Session ID:** `arena/42fb7792-olbg2` (branch `arena/42fb7792-olbg2`)
**Last updated:** 2026-10-21 (UTC)

## Rules in force
- One owner per file scope. Claim here before you start, commit the claim, then work.
- Other sessions must not edit a claimed file. Log a request instead.
- `needs review` = published on the Flagged for Review page; does not block anything.
- Shared outputs (`index.html`, `sports/*`, `data/matches.json`) are regenerated only by the
  integration session from the per-sport data files.
- A claim older than 60 minutes with no commits may be taken over; note the handoff.

## Task board

| # | Task | Status | Owner session | File scope |
|---|------|--------|---------------|------------|
| 1 | Repo recon + coordination board | in progress | `arena/42fb7792-olbg2` | `COORDINATION.md`, `research/*` |
| 2 | OLBG reverse engineering: sport taxonomy, sport IDs, event URL schema | in progress | `arena/42fb7792-olbg2` | `research/olbg-reverse-engineering.md` |
| 3 | Data collection: fixtures per included sport | unclaimed | — | `data/raw/*.json` |
| 4 | Official-source verification of fixtures + form inputs | unclaimed | — | `data/verified/*.json` |
| 5 | Line origination model + confidence rules | unclaimed | — | `scripts/model.py` |
| 6 | High-confidence written predictions | unclaimed | — | `data/predictions.json` |
| 7 | Site build (landing, sport pages, flagged page, methodology) | unclaimed | — | `site/`, `*.html`, `assets/` |
| 8 | Integration: merge, verify, publish, PR | unclaimed | — | `index.html`, `sports/*`, `data/matches.json` |

## Claims log

| When (UTC) | Session | Action |
|---|---|---|
| 2026-10-21 05:10 | `arena/42fb7792-olbg2` | Board created. Investigating whether other sessions exist (repo was empty at start, single commit `1056f6a`). |

## Environment facts (recorded for other sessions)
- Sandbox HTTP egress is restricted to GitHub hosts. General web pages and league APIs are
  **not** reachable from `bash`. Use the agent `fetch_page` / `web_search` tools instead.
- GitHub Actions is not enabled for this repo (`/actions/permissions` → 403), so no scheduled
  collector workflow can run. Data must be captured interactively and committed with provenance.
- GitHub Pages is already enabled: source = branch `main`, path `/`, built (legacy).
