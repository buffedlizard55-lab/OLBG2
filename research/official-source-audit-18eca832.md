# Survey official-source provenance audit — 2026-10-21

Run `python3 scripts/official_source_audit.py` for a row-by-row JSON report. This is a **read-only structural audit**, not a claim that linked pages were fetched or that their contents were verified. Classification is a deliberately narrow domain allowlist, not an endorsement of any individual claim.

| Check | Result | Review action |
|---|---:|---|
| Survey inventory rows | 130 | All lack `official_fixture_source`; OLBG listing URLs are provenance of OLBG's listing, **not** an official fixture confirmation. Do not present these rows as officially verified. |
| Prediction facts | 15 | 4 point to candidate official domains; 11 point to domains outside the allowlist. Even the 4 require checking the actual page and the specific claim. |
| Tests | 36 pass | Includes URL host confusion cases and count reconciliation. |

Official domain candidates: `icc-cricket.com`, `nba.com`, `nhl.com`, `mlb.com`, `atptour.com`, `wtatennis.com`, `itftennis.com`, `worldsnooker.com`, `wst.tv`, `pdc.tv`, `lnr.fr`, `top14.lnr.fr`, `unitedrugby.com`, `thepwr.com`, `gaa.ie`, `fiba.basketball` and their true subdomains. This list is intentionally incomplete and can give false negatives. An allowlisted domain is **not** proof that a given URL exists or supports the fact. The report links each non-allowlisted narrative source and lists every inventory row requiring official confirmation.

Examples for manual review: [OLBG cricket listing](https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/Afghanistan_vs_Bangladesh_One_Day_Match/7?event_id=188824) proves only listing provenance; [LNR fixture](https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan) is an official-domain candidate but its content must still be checked; [Planet Rugby round-up](https://www.planetrugby.com/news/top-14-round-up-antoine-dupont-brace-keeps-toulouse-at-the-top-while-newly-promoted-side-remain-winless) is a secondary source used for a prediction fact. No values have been inferred or silently filled in.

**Flagged for integration:** the existing survey UI and validator do not require an official fixture URL for every inventory row, and the published prediction text includes claims backed only by secondary sources. These are review items, not a reason to hide existing clearly labeled unverified records. The next integration owner should add an official-source field only after checking each underlying official page and should revise unsupported predictions rather than treating the host classifier as verification. Static snapshots should also be refreshed before treating any match as upcoming.
