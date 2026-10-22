# PR #54 takeover and odds-window remediation on current `main`

- Session: `arena/c12bdcd7-olbg2`
- Date: 2026-10-22
- Closes the task opened by session `1bb45081` (PR #54, "Odds-window confidence gate (−250..+10000) across
  all five layers; 36 chalk narratives archived")
- Status: implemented on current `main`; PR #54 closed as superseded

## 1. Why this session took the task over

COORDINATION.md's takeover rule: a claim more than 60 minutes old with no commits may be taken over by any
session, with the handoff recorded. PR #54's last commit was 2026-10-22 01:57Z; at this session's start
(2026-10-22, after PR #69 merged at 04:04Z) it was still open, `CONFLICTING`, and had been left alone twice
(`26963a2d`, `6a87eefa`) as stale. Fifteen pull requests landed after it, and its diff (7,940 lines across
all five layers) was written against data states that later sessions replaced — the `/verified/` desk in
particular now has 118 rows and 30 write-ups where PR #54 expected 155 rows and 24. Merging it as-is would
have clobbered verified work that had itself been independently re-verified (PR #62).

## 2. The two readings of the brief, and the decision

> "A lot of the high confidence picks are just picks that have a greater than 70% chance to win based on
> market prices. We need to focus on generating high confidence picks for matches that sit between -250 and
> +10000 odds."

| Reading | High label | Consequence |
|---|---|---|
| A (PR #54): the window defines the high tier | high ⇔ p ≥ 70% **and** price in [−250, +10000] | effective label window 70.0–71.43% on two-way fair prices; an 84% favourite is graded "medium" |
| B (published and tested on `/verified/` and `/forward/` since sessions 50268b75 / 36f79c71): the window scopes **generation** | high ⇔ p ≥ 72% **or** (p ≥ 70% and in window); **written predictions and featured picks** are generated inside the window (alternate lines used when the moneyline is shorter than −250) | confidence stays monotonic in win probability; the write-ups the brief asks for sit in the window |

**Decision: reading B**, applied uniformly to the four legacy layers that had not yet adopted it. Reasons:

1. It is the rule the two newest layers already publish, test (60+ assertions), and document; three
   verification sessions re-verified the data under it and it survived PR-by-PR review of the brief's
   "generate predictions as above" sentence.
2. Under reading A the confidence scale stops ordering outcomes: Toulouse at 95% would read "medium" while a
   71% pick reads "high". The brief separately says "label each with a confidence level of low, medium, or
   high" — the label should track confidence in the outcome, and the **window** should track where we
   generate write-ups.
3. Every sentence of the brief is still satisfied: high-confidence picks are >70% selections (floor
   enforced), each high pick carries a ≥30-word sourced write-up, featured write-ups sit in the −250…+10000
   band, and out-of-band chalk write-ups are retained but explicitly labelled "outside the focus band"
   instead of being passed off as compliant.

PR #54's boundary arithmetic (−250 = decimal 1.40 = 71.43% implied) is adopted verbatim and documented in
METHODOLOGY.md §3. Its non-destructive archiving principle is adopted too — **nothing is deleted**.

## 3. What changed, layer by layer

| Layer | Label change | Narrative change | Disclosure |
|---|---|---|---|
| root (`data/matches.json`, `scripts/model.py`) | NHL high threshold 0.65 → the uniform rule; BUF (65.4%), BOS (65.3%), MIN (68.9%) regraded to medium | their 3 narratives moved verbatim to `data/predictions_archived.json` with `regraded_to` + reason; 6 active narratives annotated `price_band` (NYI −247 and Paris SG −235 in band; 4 EHF chalk outside) | tests `test_dashboard.py` (window rule, archive, annotations) |
| live (`/live/`) | `confidence()` 0.62 → the uniform rule (no current row moved: all four highs ≥ 76%) | all 4 write-ups annotated `price_band` = outside-band (fair −320…−607) | picks page splits "inside the −250…+10000 focus band" from "outside the focus band (chalk favourites)"; `test_live.py` gates |
| survey (`/survey/`) | high clause gains the in-band alternative (no current row moved) | 5 write-ups annotated `price_band` = outside-band (fair −332…−1941) | predictions page split + honest empty-state note; `survey_verify.py` gates (PASS) |
| desk (`/site/`, `scripts/engine.py`) | `confidence_label` gains the probability floor + window on top of edge/evidence gates; BUF (65.0%), BOS (68.6%), DAL (64.7%) → medium, FLA (54.5%) stays low | their 4 narratives moved verbatim to `data/desk/archived_picks.json`; MIN @ CGY (70.5%, fair −233, in band) keeps the sole active narrative | pick sheet gains band tags, the rule statement and a "Regraded narratives" section; `test_build.py` gates (31 tests) |

## 4. Verification performed

| Check | Result |
|---|---|
| Full test suite after each layer | 88/88 unittest green (was 80; +8 new gates) |
| Deterministic rebuild (the exact CI chain in `.github/workflows/pages.yml`) | all generators green; every generated path byte-identical afterwards (`git status` clean apart from the intended source/data edits) |
| `survey_verify.py` | VERIFICATION PASSED, byte-identical rebuild |
| `live_build.py` | 0 broken local links, every fixture row carries an official source URL |
| `integration_audit.py` | 0 cross-layer local link errors |
| Archive integrity | every archived narrative ≥ 30 words, facts and source URLs preserved, `regraded_to` matches the row's new label, no id both active and archived |

## 5. What this session deliberately did **not** do

- Did not regrade `/verified/` or `/forward/` labels (they already follow the published rule; their featured
  sets are in-band and test-enforced).
- Did not delete or rewrite a single narrative text, fact or source link.
- Did not touch PR #54's branch; the PR is closed with a pointer here.
