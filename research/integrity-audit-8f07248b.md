# Independent evidence-integrity audit — `arena/8f07248b-olbg2`

**Date:** 2026-10-21 UTC  
**Status:** structural audit complete; no sporting facts newly verified.  
**Scope:** read-only review of the committed JSON inventories and reproducible validation commands. No shared data, generated pages, prediction text, or pipeline code was changed. This report does not claim a fresh live fetch of every linked source.

## Checks run

- `python3 scripts/survey_verify.py` — passed: 24 generated pages scanned; 335 table rows have a source link or explicit `UNVERIFIED` marker; 130 inventory entries reconcile to 11 modelled and 119 flagged entries; 2 survey predictions meet the word-count and URL-presence checks; deterministic rebuild passed.
- `python3 -m unittest discover -s tests -v` — 33 tests passed.
- Parsed all 15 `data/survey/events/*.json` files, `data/matches.json`, and both prediction stores to independently check whether inventory rows carry official-source fields and inspect source representation.

## Findings

| ID | Finding | Evidence / impact | Review disposition |
|---|---|---|---|
| A1 | The 130 survey inventory records have OLBG `source_url` provenance, but **0/130** contain a per-event `official_source_url` field. | Event schemas in all populated `data/survey/events/*.json` contain OLBG event URLs and capture metadata; the survey verifier's “source” gate accepts this OLBG URL. This proves discovery/provenance, not the fixture itself against a governing-body source. | Do not describe those 130 rows as officially fixture-verified. Existing review flags and the evidence disclosures should remain visible until row-level official references are supplied. |
| A2 | Narrative fact links are not equivalent to official-source verification. | The survey verifier checks that each prediction fact has a URL and sufficient words; it does not classify the publisher. In `data/survey/predictions.json`, Toulouse's factual list includes `all.rugby`, `planetrugby.com`, `ladepeche.fr`, `rugbyrama.fr`, and `lequipe.fr` alongside LNR; Afghanistan–Bangladesh includes a mix of source types. These can be useful leads but are not all governing-body sources. | Keep those narratives marked for source review; either replace each non-official factual claim with an official corroboration or explicitly qualify the claim and avoid calling it officially verified. |
| A3 | Main fixture dataset count includes two not-originated entries. | `data/matches.json` reports total 35, originated 33, not originated 2; direct recount agrees. Confidence counts are high 4, medium 10, low 19, plus 2 entries with confidence `unverified`. | A UI or summary that says “35 originated lines” would be false; retain the separate 33/2 and confidence breakdown. |
| A4 | Existing line/inventory gates establish structure and cited-basis presence, not exhaustive market coverage or truth of each external value. | `survey_verify.py` passes the inventory-to-modelled/flagged reconciliation and checks citations/URL presence. The main unit suite likewise validates registered source references and data invariants, not that every external source page was fetched successfully in this audit. | Phrase the result as documented partial capture, not a complete current list or independently fact-verified market catalogue. |

## Conclusions

The validation suite is useful and all executed checks passed. Those passes certify structural integrity, link presence/local resolution, counts, and deterministic generation; they do **not** establish that every listed event is current or independently confirmed by an official sports body. No fresh sport facts are promoted by this audit, and no values were inferred or filled in.

Official primary-source entry points already present in repository materials include the NBA (`https://www.nba.com/games?date=2026-10-21`), NHL (`https://api-web.nhle.com/v1/score/2026-10-21`), ICC (`https://www.icc-cricket.com/rankings/team-rankings`), and LNR (`https://www.lnr.fr/rugby-top-14/classement`). Their presence in the source register is not a claim that every linked value was re-fetched during this audit. See also `research/independent-audit-9b76e3ea.md` and `research/integration-audit.md` for earlier, complementary findings.
