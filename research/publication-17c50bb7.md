# Publication integrity audit — 2026-10-22

## Scope and limitations

Read the shared coordination board before claiming a disjoint workflow/test scope.
The repository already contains multiple dashboards and inherited data pipelines;
no additional fixture/model layer was created and no inherited sports data was altered.

Direct urllib HTTPS requests to the following official endpoints all raised
`URLError: TLS/SSL connection has been closed (EOF)` in this environment:

- https://www.olbg.com/betting-tips
- https://api-web.nhle.com/v1/schedule/2026-10-22
- https://www.nba.com/games?date=2026-10-22

These are failed access probes, not verified match facts. No response content was
available to archive. No claim is made about the websites' public availability.
Confirmed fixture values remain blank in the published report, `publication.html`.
Prior sessions' claims in COORDINATION.md were read as inherited claims, not new evidence.

## Confirmed repository irregularity

`.github/workflows/deploy-pages.yml` previously published every main push without
waiting for `.github/workflows/pages.yml` (content validation). The two independent
workflows had no dependency. A validation failure could therefore coexist with a
successful deployment of invalid generated pages.

Fix: expose the existing validation workflow with `workflow_call`, invoke it as
`validate` from the deployment workflow, and require `needs: validate` on deploy.
No `always()` override or failure suppression is used. The reusable workflow uses
the same caller commit, avoiding cross-run commit mismatches. Existing standalone
push/PR validation remains available.

## Verification

- All 145 Python unit tests passed locally, including two publication-gate regressions.
- `python scripts/integration_audit.py`: zero cross-layer local link errors.
- These are structural checks, not official factual verification or live external-link checks.
- The exact CI rebuild/drift check and remote workflow outcome are recorded in the coordination log.

## Outstanding

Fresh exhaustive collection, line-by-line official factual verification, reliable
ongoing refresh, calibrated independent prices, and fully verified narrative picks
are not completed by this audit. They must not be represented as completed merely
because links and software checks pass. The published review page preserves that distinction.
