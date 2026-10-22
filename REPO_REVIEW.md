# REPO_REVIEW.md — Baseline audit (task T1)

Session `ca1d5677`, 2026-10-21.

## What the repository contained

The review started from commit `1056f6a03d205807ad3f29620c24fdb0a696a52d` ("Initial commit")
on `main`. The entire repository was:

| Path | Size | Content |
| --- | --- | --- |
| `README.md` | 7 bytes | `# OLBG2` — no trailing newline |

That is the complete tree. There was no code, no data, no site, no `COORDINATION.md`, no CI
configuration, no `.gitignore`, no licence and no prior branch other than `main`.

## Audit findings

1. **No prior work to preserve.** Nothing in the brief's scope had been started, so no
   reconciliation with an existing implementation was needed and no other session's work was
   at risk. The task board was created from scratch.
2. **`README.md` had no trailing newline** (7 bytes, `# OLBG2`). Cosmetic. The file has been
   replaced with a full project README.
3. **No GitHub Pages configuration existed at the audited commit.** At `1056f6a` there was no site directory, no `gh-pages` branch, no `_config.yml` and no Actions workflow. A `.nojekyll` file is provided at the repository root (by the prior sessions' build) so
   GitHub Pages serves the static HTML directly instead of running a Jekyll build that would skip
   directories beginning with an underscore and add no value.
4. **No remote branch for this session existed.** The first `git pull --rebase origin
   arena/ca1d5677-olbg2` failed with `fatal: couldn't find remote ref` because the branch was
   local-only; the subsequent `git push` created it. Not a defect — recorded so the log entry
   is not mistaken for a conflict.
5. **Sandbox egress is restricted.** `curl https://www.olbg.com/` fails with
   `SSL_ERROR_SYSCALL`; only `github.com`, `api.github.com`, `pypi.org` and `registry.npmjs.org`
   are reachable from bash. Collection and verification therefore ran through the harness
   `fetch_page` / `web_search` tools, which do reach olbg.com and official governing-body sites.
   Logged as **F-01**. Consequence: the repository holds no cached HTML and no raw HTTP logs.
   Every claim is instead backed by a source URL a reviewer can open.
6. **No dependency manifest is required.** Every script is Python 3 standard library only, so
   there is no `requirements.txt`, no lockfile and no supply-chain surface to audit. Verified on
   Python 3.11.2.

## Irregularities found in the source data (not the repo)

These are irregularities in OLBG or in the official sources consulted, raised during the review
and published on the [Flagged for Review](https://buffedlizard55-lab.github.io/OLBG2/survey/flagged.html) page:

| Flag | Finding |
| --- | --- |
| F-06 | OLBG displays fixture times in US Eastern, not UK time. Established by reconciling OLBG's `07:30` for Afghanistan v Bangladesh against the official `11:30 GMT` start. |
| F-07 | Venue conflict for that same fixture: Sharjah Cricket Stadium (Wikipedia) versus Abu Dhabi (ESPNcricinfo). |
| F-08 | Series-naming conflict for the same fixtures: "Afghanistan v Bangladesh 2026-27" and "UAE ODI Tri-Series 2026-27" (ESPNcricinfo) versus "2026 Afghanistan Tri-Nation Series" (Wikipedia). |
| F-09 | ATP official ranking points disagree with third-party mirrors for the same publication date. |
| F-10 | ICC ODI points differ between mirrors while the rating agrees. |
| F-11 | PDC Order of Merit values differ across snapshots. |
| F-12 | Official World Snooker Tour rankings page returned HTTP 500; secondary sources disagree on the world number one. |
| F-13 | OLBG's own F1 calendar row mixes three events: "Round 16, 4 October, Bahrain Grand Prix, Sepang International Circuit, Malaysia". |
| F-14 | Our originated rugby union lines diverge from LNR's own published probabilities; one pick was capped at LOW as a result. |
| F-16 | 86 of 130 inventory rows come from dated search-index snapshots rather than a live fetch. |

## Scope decisions requiring human confirmation

| Flag | Decision |
| --- | --- |
| F-03 | Greyhounds (OLBG id 28) and Gaelic Football (id 25) are not named in the brief but were excluded — Greyhounds as a racing-family sport alongside horse racing, Gaelic Football as a football code alongside soccer. Both are a one-line change in `scripts/survey_inventory.py`. |
| F-04 | Motor Racing (id 14) was included; the brief excludes cycling, not motorsport. |
| F-05 | OLBG has no UFC, MMA, Hurling or Specials node, so four of the brief's exclusions are vacuous. |

## Verification performed for this task

- Repository tree enumerated with `find . -path ./.git -prune -o -type f -print`; count
  confirmed as 1 file.
- `README.md` byte length and content confirmed by direct read.
- Branch and commit state confirmed with `git log --oneline`, `git branch -a`, `git status`.
- OLBG sport taxonomy confirmed against
  <https://www.olbg.com/sitemap-betting-tips.xml> (retrieved live 2026-10-21): 22 sports.
- All source-conflict findings above were produced by comparing at least two independent
  sources for the same fact; both values are published rather than one being chosen silently.

## Line-by-line pass, 2026-10-22 (session `arena/36f79c71-olbg2`)

Every published row, prediction and flag was re-read; the table records what the pass changed and what it could
not settle.

| Area | Finding | Action |
|---|---|---|
| MLB World Series dates | StatsAPI `officialDate` is 2026-10-23 / 10-24 / 10-26 with `gameDate` 00:00Z the following day. The stored rows already matched this, so the suspected one-day drift was a `date`-bucket vs `gameDate` reading error, not a data error. | No change; documented here so the earlier note is not re-litigated. |
| MLB Games 4–7 | Game 4 (849803) is scheduled for 2026-10-27 at Tropicana Field; Game 5 (849799) is flagged `If Necessary`. Only Games 1–3 are priced. | Kept as VF-15 rather than pricing an incomplete series state. |
| EuroLeague facts | Re-fetched standings on 2026-10-22: Panathinaikos 5-1 / 528-438, Crvena Zvezda 4-2 / 485-457, Partizan 3-3 / 466-471, Efes 2-4 / 492-510, Besiktas 3-3 / 554-555, Baskonia 1-5 / 504-564. All match the stored inputs and the prediction text. | No change. |
| URC table | Re-fetched on 2026-10-22: Edinburgh 3-0 80/54, Glasgow 2-1 95/72, Bulls 2-1 126/54, Stormers 2-1 81/54, Ulster 0-2-1 88/93, Scarlets 1-2 68/85, Connacht 1-2 56/84, Zebre 0-3 52/116. | One sentence softened: “have not won away” became “are still without a win after three rounds”, which the table states directly. |
| Prediction superlatives | Three claims went beyond their cited table: “fewest goals allowed in EHF CL”, “competition-high 155 goals”, “widest ranking-position gap in the 16-match draw”. | Rewritten to the arithmetic the source supports (104 GA in four games; 155 conceded; a 60-place gap). |
| Band arithmetic | Efes headline said 177.9 while the same card's text said 174.9 and the line is 182.5. | Headline corrected to “sits 7.6 above a 174.9-point projection”. |
| All 13 band picks | Each re-checked against its own facts: probabilities 70.0–71.4%, prices the exact reciprocal rounded to 2 dp, ≥30 words, ≥2 sourced facts. | No change. |
| Retained flag | ICC 271646 renders client-side, so the 2026-10-22 (root) vs 2026-10-23 (verified) disagreement cannot be arbitrated from the official page. | Remains VF-17 with both values published. |
