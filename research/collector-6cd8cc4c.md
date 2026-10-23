# Production collector audit — 23 October 2026

## Scope and evidence boundary

This is a code/structural audit, **not** a new official-source verification of the stored fixtures. The environment permits outbound access only to GitHub and package registries, not OLBG or governing bodies. No new current fixture, injury, form, price, or prediction is asserted here. The requirement for a complete live list, every market and five defensible selections per sport remains unmet; missing facts stay blank.

## Findings and changes

| Item inspected | Finding / resolution | Source or manual review target |
|---|---|---|
| Existing landing/navigation | Root already links to the evidence-first monitor and 15 sport categories. Retained rather than creating another competing desk. | [Landing](../index.html), [monitor](../monitor/index.html) |
| NHL collection | Previously archived the response without parsing; now uses a strict fixture-only adapter. Corrected score host from `api.nhle.com` to `api-web.nhle.com`, consistent with the stored source URL. Endpoint accessibility has not been checked live in this session. | [Official NHL score endpoint](https://api-web.nhle.com/v1/score/2026-10-23), [prior repository transcription](../data/current/capture/nhl_score_2026-10-23.json) |
| Candidate eligibility | Accept only FUT/PRE with schedule state OK, explicit future UTC start, positive unique ID, valid official calendar date, and both official team names. Skip started/finished/postponed/uncertain games. Malformed candidates fail the response atomically. | [Adapter](../scripts/monitor_core.py), [official check target](https://api-web.nhle.com/v1/score/2026-10-23) |
| New fixture output | Preserve source date separately from UTC; attach source ID, capture timestamp and NHL gamecenter link. No name expansion, odds inference, ratings or injury claims. No automatic OLBG match asserted. | [Official NHL](https://www.nhl.com/), [collector](../scripts/monitor_collect.py) |
| Refresh reporting | Removed MLB-only wording now that two structured adapters exist. Failure states remain visible; an attempted refresh never changes historical source timestamps. | [Builder](../scripts/monitor_build.py), [source ledger](../monitor/sources.html) |
| Confidence / price band | Retained separate bookmaker quote and originated fair price fields. Market-implied probability is not independent forecasting evidence. No quota padding or new high-confidence claims. If the band applies to fair odds, ≥70% intersects it only at 70–71.43%; observed bookmaker odds and an independent probability need not have that relationship. | [Rules](../scripts/monitor_core.py), [review queue](../monitor/flagged.html) |
| Unattended deployment | Existing deployment workflow runs every six hours; successful runtime captures are deployed as artifacts rather than committed. No credentials or input are requested from the user. Collection errors are evidence, not empty-world schedules. | [Workflow](../.github/workflows/deploy-pages.yml) |

## Verification performed

Tests use deliberately synthetic names and IDs, not current NHL fixtures. They exercise response shape, future pregame acceptance, past/uncertain state rejection, explicit UTC, source-date preservation, missing names, duplicate IDs, invalid dates, absent betting facts, and the collector's NHL dispatch/body archive. Full repository tests and the local-link audit are also run. Passing these tests proves software behavior only, not real-world fixture correctness or forecast calibration.

## Still needs review

- Live endpoint/schema behavior and complete OLBG mapping/pagination are not confirmed here.
- The NHL adapter fetches the requested day's score feed only; it is not a full upcoming-season inventory.
- Thirteen other sport categories still lack structured automated fixture adapters in the monitor; MLB/NHL do not cover every league or market.
- Every-market independent pricing, current-form history, official injuries and 75 daily predictions are not delivered. No picks have been fabricated to meet the target.
- Prior desks and stored transcriptions are historical research, not automatically accepted as fresh primary-source evidence.
