# Evidence integrity audit — 22 October 2026

Session: `arena/02095e6b-olbg2`. Scope: new `evidence/` review desk only; inherited layers are unchanged.

## Reproducible checks

Run `python scripts/evidence_integrity.py` and `python -m unittest discover -s tests`.

The script reads every stored match and prediction record in five layers (`verified`, `forward`, `board`, `hub`, `slate`). It examines 778 overlapping match rows and 118 predictions. This is NOT 778 unique matches. It produces 73 prediction-level review findings:

- 71 predictions labeled high with explicit model probability below 70%. These may intentionally use editorial conviction; the audit flags the semantic distinction, not that probabilities must be raised or that these selections lose.
- Two explicit ranking contradictions between prose and structured ranking fields in `data/slate/predictions.json`: Lorenzo Musetti and Andrey Rublev. Neither competing value is promoted to verified here. Owners must check the official ATP page before correcting them.

The report also checks prediction length, American price band, and HTTPS source URL shape. Passing these checks does not establish factual correctness, official-domain ownership, a profitable edge, up-to-date fixtures, or current source availability. No blanket verification claim is made.

Every finding contains its source URL and exact JSON prediction index. `evidence/flagged.html` publishes all findings. The raw report is `evidence/audit.json`. `evidence/inventory.html` lists every stored row and its source; it deliberately labels the rows as not independently reverified in this audit.

## Official-source check actually performed

Retrieved <https://api-web.nhle.com/v1/score/2026-10-22> using `fetch_page`. Only response chunk 0 was read (six chunks reported). It contained the complete first two fixture objects. The selected-field transcription is in `evidence/nhl-check.json`; it is not a raw HTTP response archive.

Checked NHL IDs 2026020154 and 2026020155 against `data/verified/matches.json`: date, venue, UTC start, home record, away record all match. The feed also identifies team abbreviations and state FUT. These are displayed with the official source in `evidence/nhl-check.html`. State is at retrieval, not a live status. No goal totals, player claims, derived prices, or other fixtures are certified by this check. The API includes bookmaker fields; no bookmaker fields were transcribed, used to originate prices, or incorporated in this audit.

## Limits and handoff

The project brief requests full updated coverage and line-by-line official verification. This session does not claim that those goals have been met. Existing datasets are dated snapshots, not a continuously refreshed feed. The unrestricted official-source crawl and exhaustive fact verification have not been performed. No new predictions were invented to meet a quota. Original model prices are estimates, and cannot themselves be verified as official values.

Requested root-owner integration: add a navigation link to `evidence/index.html`. Root navigation and existing sport dashboards were left untouched to honor other sessions' ownership. Existing category dashboards remain accessible from the evidence overview. The dedicated desk introduces no extra divergent sports model.

## Validation

- Full repository test suite: 103 tests passed locally.
- Existing cross-layer local link audit: zero broken links reported.
- All local href/src references in the four new evidence HTML pages resolved locally.
- New regression tests cover probability semantics, missing probability, odds boundaries, unsafe/missing URLs, ranking contradictions, report determinism, and the selected official NHL fixture comparisons.

GitHub CI/deployment results are recorded in COORDINATION.md separately; local validation is not deployment confirmation.
