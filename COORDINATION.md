# COORDINATION — OLBG2 multi-session task board

**Session ID:** `arena/42fb7792-olbg2` (branch `arena/42fb7792-olbg2`)
**Last updated:** 2026-10-21 05:55 UTC

## Rules in force
- One owner per file scope. Claim here before you start, commit the claim, then work.
- Other sessions must not edit a claimed file. Log a request instead.
- `needs review` = published on the Flagged for Review page; does not block anything.
- Shared outputs (`index.html`, `sports/*`, `data/matches.json`) are regenerated only by the integration
  session from the per-sport data files.
- A claim older than 60 minutes with no commits may be taken over; note the handoff.

## Task board

| # | Task | Status | Owner session | File scope |
|---|------|--------|---------------|------------|
| 1 | Repo recon + coordination board | done | `arena/42fb7792-olbg2` | `COORDINATION.md`, `research/*` |
| 2 | OLBG reverse engineering (taxonomy, ids, URL schema, markets, irregularities) | done | `arena/42fb7792-olbg2` | `research/olbg-reverse-engineering.md` |
| 3 | Data collection: fixtures per included sport | done (partial coverage) | `arena/42fb7792-olbg2` | `data/inputs/*`, `research/collection-log.md` |
| 4 | Official-source verification of fixtures + inputs | done (see coverage note) | `arena/42fb7792-olbg2` | `data/inputs/*`, `data/sources.json` |
| 5 | Line origination model + confidence rules | done | `arena/42fb7792-olbg2` | `scripts/model.py`, `scripts/config.py`, `METHODOLOGY.md` |
| 6 | High-confidence written predictions | done (4) | `arena/42fb7792-olbg2` | `data/predictions.json` |
| 7 | Site build (dashboard, sport pages, flagged, methodology, sources) | done | `arena/42fb7792-olbg2` | `index.html`, `sports/*`, `assets/*`, `scripts/build_site.py` |
| 8 | Integration: verify, publish, PR | in progress | `arena/42fb7792-olbg2` | shared outputs |

**No competing session was detected.** The repository was empty at session start (single commit `1056f6a`,
one `README.md`), and no other branch, worktree or claim appeared during the session. Every task above was
therefore self-claimed and completed by `arena/42fb7792-olbg2`.

## Claims log

| When (UTC) | Session | Action |
|---|---|---|
| 2026-10-21 05:12 | `arena/42fb7792-olbg2` | Board created; repo empty, no rival claims. |
| 2026-10-21 05:15 | `arena/42fb7792-olbg2` | Claimed tasks 1–2 (research scope). |
| 2026-10-21 05:18 | `arena/42fb7792-olbg2` | Claimed tasks 3–8 (this session is working solo; scopes are disjoint from any future session's). |
| 2026-10-21 05:55 | `arena/42fb7792-olbg2` | Tasks 1–7 complete, task 8 integration under way. Published site, flagged page populated. |

## Verification performed

| Source family | Verified what | Result |
|---|---|---|
| NBA.com games page (2026-10-21) | 11 fixtures, tip times, game ids | All 11 published; 1 game id blank (truncated capture) |
| NBA.com standings 2025-26 | 30 team records + home/road splits | Used as prior; 0 current-season games, so confidence capped |
| NHL score API | 21 Oct (2 games) + 22 Oct (11 of 12) | 12 published, 1 fixture omitted (away team truncated) |
| NHL stats REST team summary | 32 teams GP/W/L/OTL/GF/GA | 31 complete, Sharks goals blank → their game not originated |
| URC match centre + table | 8 Round 4 fixtures + 16-team table | All 8 published and lined |
| ICC match list | AFG v BAN ODI, NZ v IND T20I | Fixtures published, no line (ranking table empty) |
| WST matches | NI Open R1 results + 2 scheduled R2 matches | Both R2 matches had started by capture; not published |
| MLB stats API | 21 Oct schedule | 0 games — no MLB rows |

## Handoff / open work for any later session

1. **Do not edit** `data/matches.json`, `index.html` or `sports/*.html` by hand — regenerate with
   `python3 scripts/model.py && python3 scripts/build_site.py`.
2. Highest-value additions, in order:
   - capture the missing NHL game on 22 Oct (Seattle home) and Sharks goal totals → +2 lines;
   - read ATP rankings + PDC Order of Merit from a rendered page → unlock tennis and darts;
   - verify Gaelic football club fixtures on county-board sites;
   - survey the eight sports never captured (Handball, Volleyball, Golf, Motor Racing, Greyhounds, eSports,
     Aussie Rules, Rugby League).
3. Anything new must be appended to `data/flagged.json` and `data/sources.json` and re-published.

## Environment facts (recorded for other sessions)
- Sandbox HTTP egress is restricted to GitHub hosts. General web pages and league APIs are **not** reachable
  from `bash`. Use the agent `fetch_page` / `web_search` tools instead.
- GitHub Actions is not enabled for this repo (`/actions/permissions` → 403, dispatch → 404), so no scheduled
  collector can run. Data must be captured interactively and committed with provenance.
- GitHub Pages is enabled: source = branch `main`, path `/`, legacy build. The site must stay at the repo root.

## Publish record

| Item | Value |
|---|---|
| Integration branch | `arena/42fb7792-olbg2` |
| Build check | `python3 scripts/build_site.py` → 9 pages, 33 fixtures, 4 predictions, no broken links |
| Pull request | _to be recorded after merge_ |
| Merge result | _to be recorded after merge_ |
| Pages deploy | _to be recorded after deploy_ |
