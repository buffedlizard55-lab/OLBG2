# Evidence-gated integration audit — session 8226c94a

Date: 23 October 2026 (UTC). Baseline: `2999cc0cbe319451b6cd2a3737952e30a4da6208`.

## Result and limits

This is a **selected line/field audit**, not a claim that every historical repository line
or every sports fixture has been externally verified. At baseline there were 587 HTML
pages, multiple overlapping data layers, and 467 passing structural tests. Passing those
tests is not external factual verification.

The new, separate `/monitor/` has exactly the requested 15 categories. It stores 24
fixture rows with official pairing/date evidence, 19 associated OLBG participant-pair
listings, 35 source records and 12 selected unconfirmed OLBG discovery examples. Only
one match has an originated experimental moneyline, with two complementary outcomes.
No high-confidence recommendation qualifies. Five predictions per sport daily, complete
OLBG pagination, all market prices and supported injury coverage **remain unmet**.

The earlier desks are preserved, not counted as additional evidence. The repository
landing page now directs readers to the new desk and collapses the historical dashboard.

## Access and reproducibility

Direct sandbox Python HTTPS to OLBG, NHL and MLB failed with TLS EOF. The agent's
`fetch_page` tool could read selected pages. All 15 requested sport hubs were read,
plus the separate Hurling hub: Gaelic Sports now includes both Gaelic Football and
Hurling. The user did not exclude hurling in this request. Esports and Aussie Rules
are not new monitor categories.

Source reads occurred on 23 October around 16:16–16:19 UTC. The ledger uses the close
of that capture window; it does not claim per-request wall-clock precision. Stored
excerpts are **selected field transcriptions**, not raw response bytes. Their SHA-256
hashes detect local changes, not source authenticity. Runtime automation stores raw
successful HTTPS response bytes separately and records transport, soft-404 and parser
failures.

Reproduce the session extract and dashboard:

```sh
python scripts/monitor_seed.py
python scripts/monitor_build.py
python -m unittest discover -s tests
python scripts/integration_audit.py
```

Fresh automation is deliberately separate:

```sh
python scripts/monitor_collect.py
python scripts/monitor_build.py --runtime data/monitor/runtime/latest.json
```

No manual data input, credentials or paid feed is required to run the implemented
checks. This does **not** make unsupported official fixture parsers, odds feeds or
automatic evidence-backed prose complete.

## Field-level verification ledger

| Row scope | Official source actually read | Supported fields | Blank / not certified |
|---|---|---|---|
| MLB `849805` | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-23) | Teams, game ID, scheduled status, officialDate 2026-10-23, UTC 2026-10-24T00:00:00Z, venue, World Series Game 1 | Actual bookmaker price, pitchers, recent individual results, injuries |
| MLB moneyline inputs | [MLB standings](https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason&fields=records,teamRecords,team,id,name,wins,losses,runsScored,runsAllowed) | Rays 98–64, 736 runs scored / 650 allowed; Brewers 103–59, 832 / 618; all 3 chunks read | Unlabelled record splits not interpreted; no postseason form inferred |
| 12 NBA rows | [NBA games, both chunks](https://www.nba.com/games?date=2026-10-23) | Exact participant pair, game-link ID, Oct 23 date, explicitly labelled ET clocks | No odds, injury report, sufficient prediction inputs; UTC conversion is labelled normalization, not independently sourced UTC |
| 3 URC rows | [URC round 4](https://stats.unitedrugby.com/match-centre/2026-27/4) | Cardiff–Sharks, Connacht–Zebre, Edinburgh–Lions; Oct 23; displayed 14:45; fixture IDs | Page says Local but zone unresolved; UTC and pre-match eligibility blank |
| 2 WST rows | [WST matches, chunks 0 and 2](https://www.wst.tv/matches/) | Jones–Donaldson and Gilbert–Williams, scheduled quarter-finals, Oct 23; displayed 14:00; exact match-centre URLs | UTC timezone, betting inputs and injuries; completed McGill–Wilson and Craigie–Slessor not promoted |
| US Grand Prix | [F1 race page](https://www.formula1.com/en/racing/2026/united-states) | Race Oct 25, displayed 16:00; calendar also checked | Display timezone, full field, price distribution and offered odds |
| 4 RLWC rows | [NRL round 2](https://www.nrl.com/draw/?competition=131&round=2&season=2026) | PNG–Samoa / England–France on Oct 24; NZ–Cook Islands / Australia–Fiji on Oct 25 | Timezone and OLBG membership; Tonga–Lebanon already Full Time and excluded |
| Ireland–Scotland | [GAA fixtures](https://www.gaa.ie/fixtures-results) | Shinty-Hurling International, Oct 24, displayed 18:00, pairing | OLBG membership, timezone; not evidence for county football/hurling matchups |

Each row above links an official source. The dashboard links each individual fixture
and the read source separately where those URLs differ. A link observed in a read
listing is not a claim that its target page was separately fetched.

## Source gaps — not proof of no fixtures

| Category | Official check | Observed result |
|---|---|---|
| Golf | [PGA schedule](https://www.pgatour.com/schedule) | First chunk has 2026 schedule; no upcoming tournament transcribed. OLBG Golf hub said No tips found. |
| Volleyball | [Volleyball World schedule](https://en.volleyballworld.com/volleyball/competitions/superlega/2026-2027/schedule/) | Fetch failure; endpoint covers only one competition. |
| Cricket | [ICC match-list](https://www.icc-cricket.com/match-list) | 404 body, also on /matches. |
| Darts | [PDC tournament route](https://www.pdc.tv/tournament/european-championship-1) | Cookie text followed by 404 in final chunk; calendar final chunk contained controls, not pairings. |
| Greyhounds | [GBGB racing](https://www.gbgb.org.uk/racing/) | Controls without racecard runners; /racing/race-cards/ returned 404. |
| Tennis | [ATP Basel schedule](https://www.atptour.com/en/scores/current/basel/328/daily-schedule) | There Is Currently No Daily Schedule. No old Basel rows carried into the new monitor. |
| Handball | [EHF matches](https://www.eurohandball.com/en/matches/) | Page-not-found body; alternate 2026–27 Champions League matches URL also failed. |
| Ice Hockey | [NHL score](https://api.nhle.com/v1/score/2026-10-23) | 404 body, also on /v1/schedule/2026-10-23. |

## OLBG reverse engineering, limited to observed public output

- [Sitemap](https://www.olbg.com/sitemap-betting-tips.xml): sport hubs have a name
  path and numeric sport ID. The new parser validates both domain and allowed sport ID.
- Event pages have an `event_id` query parameter. The collector deduplicates within
  sport; it does not interpret a selection link as a second fixture.
- [MLB event](https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789): Money Line, Run Line ±1.50 and Game Totals 6.50 observed.
  `WIN @` had no numeric offered price in returned text. Tipster paragraphs were not
  used as official statistical evidence or copied into original prose.
- [Basketball hub](https://www.olbg.com/betting-tips/Basketball/4): participant pairs
  matched the 12 NBA listings. Displayed OLBG clocks differ from official ET clocks
  by ten minutes if compared as ET, but the OLBG zone itself is not certified.
- [Greyhound hub](https://www.olbg.com/betting-tips/Greyhounds/28): an Expired entry
  remains in the returned list. Presence on a hub never certifies future status.
- Load More Tips appears on hubs. This session did not certify exhaustive pagination
  or a private API. No full-list claim is made. Market-family checklists are research
  tasks, not assertions that each event offers every market.

## Independent lines and selection safety

The only originated line uses official season wins and losses in the explicitly
published log5 formula. Both outcomes sum to 1. There is no bookmaker input, so this
is an independent **descriptive baseline**, not a calibrated forecast. The confidence
is low. Neither market odds nor injuries are fabricated. The original exploratory
paragraph is over 30 words, avoids the prohibited words, cites the official season
totals, and explicitly declines to assert missing recent form/pitching/availability.
It is **not** represented as satisfying the high-confidence prediction brief.

An actual quoted price in −250…+10000 is required for the high-confidence gate.
Applying the band to fair odds would artificially narrow ≥70% estimates to roughly
70–71.43%; that historical convention is not used as a substitute for a real quote.

## Repository findings

| Finding | Checked location | Disposition |
|---|---|---|
| Frozen today / snapshot constants | [baseline build_site.py](https://github.com/buffedlizard55-lab/OLBG2/blob/2999cc0cbe319451b6cd2a3737952e30a4da6208/scripts/build_site.py) | Historical display clearly marked; monitor uses capture/runtime clocks and browser expiry. |
| Legacy 17-sport scope | [baseline README](https://github.com/buffedlizard55-lab/OLBG2/blob/2999cc0cbe319451b6cd2a3737952e30a4da6208/README.md) | Preserved as historical records; exact 15-sport monitor added. |
| Literal conflict-marker remnants | [baseline board](https://github.com/buffedlizard55-lab/OLBG2/blob/2999cc0cbe319451b6cd2a3737952e30a4da6208/COORDINATION.md) | Lines 3216, 3307, 3437, 3549, 3609, 3628; flagged, not silently removed. |
| Rebuild without collection | [baseline workflows](https://github.com/buffedlizard55-lab/OLBG2/tree/2999cc0cbe319451b6cd2a3737952e30a4da6208/.github/workflows) | Scheduled attempted collection before artifact publication; failures visible. |
| Fact claims broader than source availability | [baseline README](https://github.com/buffedlizard55-lab/OLBG2/blob/2999cc0cbe319451b6cd2a3737952e30a4da6208/README.md) | No older row, prediction or claimed verification imported into monitor. |

All remaining irregularities are published at [Flagged for Review](../monitor/flagged.html).
Publication status, PR link and deployment result are recorded in `COORDINATION.md`.
