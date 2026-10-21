# Root dashboard verification-copy audit — 2026-10-21

**Session:** `arena/e3c5f898-olbg2`
**Scope:** Root dashboard text and generated pages only. No match rows, prices, source records, or predictions were changed.

## Why the copy changed

A live read of the published root page at `https://buffedlizard55-lab.github.io/OLBG2/` showed the headline “Verified fixtures,” a statement that every fixture had been re-checked against an official league or governing body, a “Fixtures verified” count, and the claim “official source on every row.” Its table introduction also said every row linked to an official fixture source. These assertions were stronger than the repository's own cross-layer evidence-status report.

`research/integration-audit.md` records only a limited NHL schedule spot-check on 2026-10-21 and explicitly says it does not verify standings inputs, prices, predictions, or other fixtures. `scripts/integration_audit.py` also identifies the site as a dated snapshot, not an exhaustive or continuously refreshed slate. The separate survey audit in `research/official-source-audit-18eca832.md` finds that its 130 inventory rows lack official fixture-source fields; this finding is about the survey layer, not the root dashboard.

A URL being present, pointing to a recognized official domain, or passing a local structural validator is not evidence that its page was fetched or that it supports each displayed value. The current automated tests establish internal structure and link behavior, not fresh verification of all external facts.

## Changes made

Updated the root dashboard builder and regenerated its root pages to:

- Describe the root dataset as a dated, partial snapshot; label counts as stored rows and model outputs, not as universally verified fixtures.
- Explain that source links are references and do not prove every field was independently checked.
- Link users to the existing evidence-status review and review queues.
- Remove similarly broad “verified inputs,” “verified fixtures,” and “verified official data” statements from sport, pick, methodology, source-register, and flag-page copy.
- State that model confidence is a classification, not verified certainty, and that cited prediction prose still needs factual content review.
- Preserve all existing rows, prices, predictions, and source URLs.

## External references and limits

- Live root dashboard observed: <https://buffedlizard55-lab.github.io/OLBG2/>
- Existing integration report and its limited official NHL check: [`integration-audit.md`](integration-audit.md)
- Survey-layer provenance audit: [`official-source-audit-18eca832.md`](official-source-audit-18eca832.md)
- Root evidence-status page: <https://buffedlizard55-lab.github.io/OLBG2/integration.html>

This was a copy/evidence review. No new sporting fact was marked verified, and the published fixture list is still not exhaustive or automatically refreshed.

## Follow-up after PR #39

A concurrent integration added Handball and expanded the root snapshot from 35 to 47 stored rows. The evidence-limit wording was reapplied to the merged builder, preserving the Handball data and its pages; current generated counts should be read from the dashboard, not the historical 35-row observation above. Subsequent PRs #41–#42 corrected Handball model probabilities and prediction wording; this copy audit preserves those merged updates and does not re-verify their sporting facts.
