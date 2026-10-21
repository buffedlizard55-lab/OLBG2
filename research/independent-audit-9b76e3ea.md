# Independent cross-layer audit — 2026-10-21

**Session:** `arena/9b76e3ea-olbg2`  
**Scope:** read-only audit of the merged root dashboard, `/site/` evidence desk and `/survey/` layer. No sports facts were re-verified against live external sources in this pass; findings below are based on the checked-in source, generated HTML, and reproducible build/test output. This report does not elevate an item to verified merely because a URL is present.

## Verification run

From the repository root:

```text
python3 -m unittest discover -s tests -v   -> 28 tests passed
python3 scripts/build.py                  -> Built 25 fixtures (4 high, 5 medium, 16 low)
python3 scripts/build_site.py              -> 9 pages, 35 fixtures, 4 predictions, no broken links
python3 scripts/survey_verify.py           -> PASS; 24 HTML pages, 130 events, 11 lines,
                                               2 predictions, 21 flags; all built-in checks green
python3 scripts/survey_build.py            -> regenerated survey pages
python3 scripts/survey_verify.py           -> PASS again; deterministic rebuild check green
```

The working tree remained clean after regeneration. These checks establish internal consistency and reproducibility under the repository's validators; they do **not** establish that every cited statement is true or that every URL is an official source.

## Findings requiring review

### R1 — Survey inventory citations are discovery citations, not row-level official fixture confirmation (high)

The 130 records under `data/survey/events/*.json` each have only a `source_url` field. Spot-checks show it points to an OLBG listing, for example `data/survey/events/rugby_union.json` (`Montauban v Oyonnax`) points to `https://www.olbg.com/betting-tips/Rugby_Union/9`. `scripts/survey_verify.py` checks that the records have an OLBG provenance URL, date and retrieval method; it does not require an official league/team URL for each event row. The report also reconciles 119 rows as flagged/unverified, which is appropriately cautious, but an OLBG link is not an official governing-body confirmation.

**Impact:** do not present all 130 as an officially verified fixture list. Where the official fixture source cannot be linked and checked per row, keep the field blank and mark the row unverified. To meet the requested standard, add a distinct official fixture-source field and a validator that checks it (or renders the row as explicitly unverified).

### R2 — Prediction citation validation checks URL presence, not official-source status (high)

`data/survey/predictions.json` P-01 and P-02 contain source URLs from third parties, not just governing bodies. Examples include All.Rugby, Planet Rugby, Rugbyrama, La Dépêche and L'Équipe for P-01; ESPNcricinfo, Cricinfo, The Sports Encounter and Wikipedia for P-02. P-02's venue field explicitly records a Wikipedia/ESPNcricinfo conflict. The text includes specific recent results, player performances, standings and availability details. `scripts/survey_verify.py` only asserts that each `facts_used` entry has a non-empty URL, so its “every prediction fact carries a source URL” pass is not equivalent to the user's official-source-only requirement.

Official references present in these records include the ICC team rankings (`https://www.icc-cricket.com/rankings/team-rankings`) and LNR standings/fixture page (`https://www.lnr.fr/rugby-top-14/classement`, `https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan`). They do not by themselves verify every narrative fact. Injury status, recent scorecards, and player details need official club/competition sources or must be removed/marked unverified. Do not characterize the existing predictions as fully official-source-verified until that gap is resolved.

### R3 — Scope and coverage counts conflict across layers (high)

- `README.md` describes 17 included sports, explicitly including Gaelic Football and Greyhounds. `data/survey/sports.json` has 15 included sports and marks Gaelic Football (id 25) and Greyhounds (id 28) excluded under the ambiguous broad wording in the brief. The survey's own `F-03` asks for a decision. These two layers therefore disagree on the in-scope universe.
- The root README's “Coverage gaps” section still says Handball, Volleyball, Golf, Motor Racing, Greyhounds, eSports, Aussie Rules and Rugby League could not be verified, while the later survey layer reports inventory rows for Handball, Volleyball, Golf, Motor Racing and Darts, and zero OLBG events for Rugby League, Aussie Rules and eSports. The old paragraph was not reconciled when the survey was appended.
- The survey build/verification output finds **24 HTML pages** (9 top-level + 15 sport pages); the coordination narrative describes 25 pages. “26 site files” in the build output counts the 24 HTML files plus two assets, not 26 pages.

**Impact:** readers cannot tell whether “17 sports” or “15 sports” is the agreed scope, and which coverage statement is current. Keep both interpretations visible as a flagged decision until resolved; update all counts from generated data in one integration pass.

### R4 — Survey navigation was missing at audit start; fixed upstream during this audit (resolved)

At the initial audit of commit `9852d0e`, `index.html` had no `survey/index.html` navigation link; this was also recorded as an integration request in `COORDINATION.md` under session `ca1d5677`. While this report was being prepared, session `arena/dd14fcfd-olbg2` added the survey link to the root navigation and footer in PR #27, merged into `main` (merge commit `e5ad112`). After rebasing onto the updated `main`, this audit confirmed the link is present in the root page and regenerated output. This finding is closed; no navigation change was made by this session.

### R5 — The “no duplicate fixtures” statement is false for two records (medium)

The survey section of `COORDINATION.md` and `README.md` says the layers cover different fixtures/no duplication. Comparing the 35 root fixture participants with survey event records finds at least these same fixtures in both:

- Afghanistan v Bangladesh — root `data/matches.json`; survey `data/survey/events/cricket.json` / P-02.
- New Zealand v India — root `data/matches.json`; survey `data/survey/events/cricket.json`.

The root and survey use separate datasets/models, but the inventory is not disjoint. State the overlap accurately and avoid double-counting a combined coverage total. The claim was found by exact team-pair comparison (team order ignored); no claim is made here about additional overlap outside the matching rows.

### R6 — This is a static snapshot, not an automatically refreshed live slate (high for “updated matches”)

Survey data records `as_of` dates from 2026-10-18, 2026-10-20 and 2026-10-21. A checked count finds 72/130 records retrieved via `indexed_snapshot` and marked `stale_flag: true`; the remaining 58 use `live_fetch`. `scripts/survey_build.py` hard-codes `RETRIEVED = "2026-10-21"`; the Pages workflow builds committed content but does not collect new schedules. Validators check provenance and determinism, not age/freshness.

**Impact:** as published, this is a point-in-time research snapshot. It should not be described as an up-to-date or continuously refreshed slate. Add a freshness threshold/expiry badge or a scheduled collector before making that claim. Events and especially completed fixtures must be rechecked before reuse.

## Scope boundary / non-changes

This session did not edit any generated page, sports data, prediction, source register or pipeline owned by earlier sessions. `COORDINATION.md` already contains unresolved integration requests about the survey navigation, scope ambiguity and combining flag registers. The findings above are recorded for the next integration owner rather than silently changing shared published outputs. R4 is resolved by PR #27: the root nav/footer now link to the survey and remained present after rebasing.
