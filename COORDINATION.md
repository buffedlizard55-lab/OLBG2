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
- **Shared outputs** (`index.html`, `sports.html`, site navigation, merged tables)
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
| T1 | Repository review + baseline audit of existing content (see REPO_REVIEW.md) | done | `ca1d5677` | `REPO_REVIEW.md` |
| T2 | Build OLBG sport registry; decide include/exclude per brief | done | `ca1d5677` | `data/sports.json` |
| T3 | Collect event lists for all included sports from OLBG | done | `ca1d5677` | `data/events/*.json` |
| T4 | Collect official ratings/standings inputs (per sport) | done | `ca1d5677` | `data/ratings/*.json` |
| T5 | Originate our own lines (ML / handicap / total) from T4 inputs | done | `ca1d5677` | `data/lines.json`, `scripts/originate_lines.py` |
| T6 | Pick match winner + low/medium/high confidence per match | done | `ca1d5677` | `data/picks.json` |
| T7 | Write 30+ word human predictions for high-confidence picks | done | `ca1d5677` | `data/predictions.json` |
| T8 | Build GitHub Pages site (landing + category subpages + tables) | done | `ca1d5677` | `index.html`, `sports.html`, `lines.html`, `picks.html`, `predictions.html`, `methodology.html`, `verification.html`, `flagged.html`, `excluded.html`, `sports/**`, `assets/**`, `scripts/build_site.py` |
| T9 | Verification pass: every row has an official source link or is flagged | done | `ca1d5677` | `verification.html`, `scripts/verify.py` |
| T10 | Flagged-for-Review page (irregularities + unverified items) | done | `ca1d5677` | `data/flags.json`, `flagged.html` |
| T11 | Integration: build check, link check, publish Pages, open + merge PR | done | `ca1d5677` | generated site files, `COORDINATION.md` |

No other session has claimed any task in this repository at the time of writing.
Any session picking up work must add its row here and push immediately.

---

## Log

| Timestamp (UTC) | Session | Entry |
| --- | --- | --- |
| 2026-10-21 | `ca1d5677` | Board created. Repo at `1056f6a` contained only a 7-byte `README.md` (`# OLBG2`) — no data, no code, no site. Claimed T1–T11 as a single-session run. |
| 2026-10-21 | `ca1d5677` | Environment note: sandbox `bash` egress is restricted to github.com / pypi.org / npmjs.org, so `curl olbg.com` fails. Collection and verification run through the harness `fetch_page` / `web_search` tools, which **do** reach olbg.com and official governing-body sites. Logged as irregularity **F-01**. |
| 2026-10-21 | `ca1d5677` | Publish note: `PUT /repos/:owner/:repo/pages` returns **403 Resource not accessible by integration**, so the Pages source cannot be repointed from `/` to `/docs` with this token. The site is therefore generated at the repository root, which also keeps URLs clean. Logged as irregularity **F-21**. |
| 2026-10-21 | `ca1d5677` | Environment note: OLBG event pages render bookmaker prices client-side; the served HTML exposes `WIN @` with an empty price. Decimal prices therefore cannot be captured, so lines are originated from official ratings instead of de-vigging book prices. Logged as irregularity **F-02**. |

---

## Decisions requiring human review

Tracked in detail in `data/flags.json` and published at `flagged.html`. Headline items:

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
| Completed by | session `ca1d5677` on branch `arena/ca1d5677-olbg2` (single-session run; no other claims existed) |
| Date | 2026-10-21 |

### Sources used

Governing bodies and official competition organisers:

- OLBG sport taxonomy — https://www.olbg.com/sitemap-betting-tips.xml (live, 2026-10-21)
- OLBG fixture listings — https://www.olbg.com/betting-tips/<Sport>/<id> per in-scope sport
- ICC men's team rankings — https://www.icc-cricket.com/rankings/team-rankings (read via
  https://www.cricinfo.com/rankings/icc-team-ranking; ODI as of 2026-10-19, T20I as of 2026-10-14)
- LNR Top 14 standings — https://www.lnr.fr/rugby-top-14/classement (after round 6, 2026-10-20)
- LNR fixture sheet — https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan
- LNR published fixture probabilities — https://top14.lnr.fr/club/toulouse and
  https://top14.lnr.fr/club/la-rochelle
- ESPNcricinfo series and scorecards — https://www.espn.com/cricket/series/_/id/23884/afg-vs-ban and
  https://www.cricinfo.com/series/uae-odi-tri-series-2026-27-1555109/afghanistan-vs-bangladesh-3rd-match-1555119/live-cricket-score
- OWGR — https://www.owgr.com/current-world-ranking (week 42, 2026-10-18; retrieved, not used)
- ATP — https://www.atptour.com/en/rankings/singles (2026-10-07; insufficient range, not used)
- WTA — https://www.wtatennis.com/rankings/singles (JavaScript-rendered; not usable)
- PDC — https://www.pdc.tv/rankings (cookie-walled; partial only, not used)
- World Snooker Tour — https://worldsnooker.com/rankings (HTTP 500; not usable)
- NBA — https://www.nba.com/schedule (reachability confirmed)

Corroborating press used only for team news, and labelled as such (F-20): lequipe.fr, all.rugby,
rugbyorbit.com, planetrugby.com, rugbyrama.fr, ladepeche.fr, thesportsencounter.com, Wikipedia.

### Verification performed

- `scripts/verify.py` run to green: all internal links resolve across 24 pages (415 external
  links present); all 335 data-table rows carry a source link or an explicit UNVERIFIED badge;
  all 130 inventory rows carry provenance URL, listed time, as-of and retrieval method; all 11
  originated lines cite a rating or basis source; every null line cell is explicitly marked
  unverified rather than silently blank; both predictions exceed 30 words (143, 133) and every
  fact carries a URL; a prediction exists for every high-confidence pick and no other; the
  inventory reconciles exactly as 130 = 11 modelled + 119 flagged; flag ids unique; rebuild from
  the same data is byte-identical.
- OLBG's displayed timezone was proved rather than assumed, by reconciling its 07:30 for
  Afghanistan v Bangladesh against the official 11:30 GMT start (F-06).
- Where two sources disagreed the same fact was published from both and the conflict flagged,
  never silently resolved (F-07, F-08, F-09, F-10, F-11, F-12).
- Our lines were compared against LNR's own published probabilities; the divergence guard fired
  on La Rochelle v Bordeaux and capped that pick at LOW (F-14).

### Irregularities

21 flags in `data/flags.json`, published at `flagged.html`. Categories: 7 source conflicts
or data-availability failures, 2 irregularities in OLBG's own content (F-06 timezone, F-13 F1
calendar row mixing three events), 3 scope decisions needing confirmation (F-03, F-04, F-05),
3 coverage gaps (F-15 119 rows with no line, F-17, F-18), 1 model divergence (F-14), 1 model
limitation (F-19), 1 data-freshness issue (F-16 86 snapshot rows), 1 source-tier caveat (F-20),
3 environment notes (F-01, F-02, F-21).

### Coverage statement

11 of 130 inventoried events carry an originated line. The other 119 are blank by design: for
those events no governing-body rating, official league table or published base rate could be
verified for both competitors during collection, and the brief forbids inferring a value. Each
is itemised under F-15 with the exact official source required. Unlocking them needs the full
official ranking tables (ATP/WTA 1-200, PDC Order of Merit top 128, WST rankings) and league
standings for the club competitions (NBA, NHL, MLB, EuroLeague, EHF, national volleyball and
handball leagues), which is a collection-scope change, not a code change.
