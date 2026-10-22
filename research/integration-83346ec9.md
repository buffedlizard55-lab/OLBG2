# Integration verification ledger — 2026-10-22

Session: `arena/83346ec9-olbg2`. Scope: shared publishing integration only.

## Source access and factual boundary

`curl -I --max-time 15 https://www.olbg.com/` failed with exit 35 (`OpenSSL SSL_connect: SSL_ERROR_SYSCALL`). The environment permits outbound access to GitHub and package registries, not general sports websites. No official sporting fact was freshly confirmed in this session. Prior captures were not relabelled as newly verified. Existing fixture values, prices and narrative text were not edited.

Official links retained for manual review:

| Subject | Official source | Session status |
|---|---|---|
| OLBG inventory | https://www.olbg.com/ | Access failed; live taxonomy and completeness unverified |
| NHL fixtures | https://api-web.nhle.com/v1/score/2026-10-23 | Prior capture only; not fetched here |
| EuroLeague games | https://www.euroleaguebasketball.net/en/euroleague/game-center/ | Prior capture only; not fetched here |
| URC table | https://stats.unitedrugby.com/match-centre/table/2026-27 | Prior capture only; not fetched here |
| EHF | https://ehfcl.eurohandball.com/ | Prior capture only; not fetched here |
| Snooker | https://www.wst.tv/matches/ | Prior capture only; not fetched here |
| MLB | https://statsapi.mlb.com/api/v1/schedule | Prior capture only; not fetched here |
| F1 | https://www.formula1.com/en/racing/2026 | Prior capture only; not fetched here |

The existing source register and raw captures are linked from `/current/sources.html`. A source link alone does not establish that every adjacent claim is supported.

## Repository findings and fixes

- Added `/current/` to root/category navigation and the integration table; values derived from committed JSON, not hand-summed across overlapping layers.
- Added current seed/model/build and generated data/page drift checks to CI.
- Changed local file link audit from a seven-folder allowlist to automatic HTML discovery across all published layers. It does **not** check remote URLs or fragment IDs, and its output now explicitly says structural only.
- Moved Atlas table row inside its table; it previously appeared after the closing table element.
- Added public integration review rows covering blocked source access, coverage gaps, alternate-line availability and model confidence limitations.
- Preserved every existing research layer; no active data owner's scope modified.

## Unmet requirements — do not interpret as completed

1. Full updated match inventory and every available market for every eligible sport.
2. Five independently justified, officially verified predictions for each sport daily; the current snapshot has 29 narratives in only four sports.
3. Bookmaker availability and odds within the requested band. Fair model odds alone cannot establish either.
4. Out-of-sample calibration of high-confidence probabilities; alternate handicaps can raise nominal probability without establishing predictive skill or betting value.
5. Fresh line-by-line verification of every stored fact and narrative. Offline reproducibility and source-domain tests are not factual verification.
6. Automated live source collection with freshness/started-event checks. Current CI is an offline regeneration pipeline, not a daily collection service.

The current snapshot records 57 fixtures, 55 originated rows, 2 blank rows, 1931 prices, 164 markets and 29 predictions; these are stored-data counts only. Ten of the 17 categories publish no rows. No missing factual values were filled by inference in this integration.

## Validation

Baseline: 338 unit tests passed. Final suite, rebuild, local file-link audit, pull request and deployment results are recorded in the append-only session entry in `COORDINATION.md`.
