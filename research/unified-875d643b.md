# Consolidated desk — research and verification record (session arena/875d643b-olbg2)

## 1. The constraint that shaped the work

The authoring sandbox has no general internet access. Tested directly at the start of the session:

```
curl https://www.olbg.com/            -> 000 (no connection)
curl https://www.nba.com/             -> 000
curl https://api-web.nhle.com/v1/...  -> 000
curl https://www.bbc.co.uk/sport      -> 000
```

Only `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org` and
`files.pythonhosted.org` resolve. OLBG and every sports governing body are therefore unreachable from this
session, so **no page was fetched live here** and no row claims otherwise.

What the repository does hold, and what this desk is built on:

| Evidence set | What it is | When | Where |
|---|---|---|---|
| OLBG + official captures | 181 verbatim HTTP responses stored by `scripts/ledger_capture.py` on a GitHub-hosted runner, with status code, byte count, sha256 and fetch time | 2026-10-23T19:28:51Z → 20:32:10Z | `data/ledger/manifest.json`, `data/ledger/raw/` (179 bodies, 28 MB) |
| Fixture / price / prediction layer | Capture bundles transcribed by session `a0c8b7f3`, plus 728 originated prices and 33 write-ups | 2026-10-23T20:05Z | `data/cadence/` |

## 2. Reverse engineering of OLBG (what this session re-derived independently)

The captured OLBG pages are Nuxt-style server payloads with an embedded `tips:[...]` array of flat JS objects.
Each object carries: `event_name_alias`, `eventUrl` (containing `?event_id=`), `event_start_unix_timestamp`,
`market_alias`, `selection`, `odds`, `american_odds`, `fractional_odds`, `menu_league`, `categoryUrl`,
`confidence`, `win_tips_count`, `expired`.

Working URL shapes observed in the stored captures:

```
https://www.olbg.com/betting-tips                      # sport index (all sports)
https://www.olbg.com/betting-tips/<Sport>/<id>         # sport hub
https://www.olbg.com/betting-tips/<Sport>/All_<Sport>/All_Events/<id>
https://www.olbg.com/betting-tips/<Sport>/<Comp>/<Comp>/<Event_Slug>/<id>?event_id=<n>
```

Not working in the capture (recorded as evidence, not hidden): the `sports/<Sport>/top_tips?...` JSON endpoints
returned **404** for all fifteen sports under two URL variants, and hyphenated sport slugs
(`Gaelic-Sports`, `Ice-Hockey`, `Motor-Racing`, `Rugby-League`, `Rugby-Union`) returned 404 while underscore
slugs worked. Those 37 failures are published on `/sources.html`.

Market vocabulary actually present in the captures: Money Line, Pointspread, Game Totals, Win Match,
Win Match 2-way, Win Tournament, Handicap, Puck Line, Fastest Qualifier, Win Race, Grand Final Winner.

## 3. What was re-parsed, and the reconciliation

`scripts/unified_inventory.py` re-reads all 46 successful OLBG pages itself (it does not import the earlier
parser), verifies each body's sha256 against the manifest, and produces:

* **216 events** in the fifteen sports — 127 of them starting after the capture clock;
* per event: id, name, league, start, market names, tip count, listing URL, and the capture file + hash.

The earlier layer parsed one listing per sport, so it found fewer events (e.g. Ice Hockey 3 vs 39 here, Tennis 5
vs 21). Those deltas are published on `/verification.html` rather than quietly adopted.

Of the 93 fixtures in the priced layer, **44 match an OLBG event** on both sides; 49 do not, and say so
(`/matches.html`). The largest unmatched groups: all 9 Rugby League World Cup rows, all 8 snooker rows, all 2 golf
rows and 4 of 6 handball rows.

## 4. Official cross-checks that were possible

| Sport | Stored official body | Join key | Result |
|---|---|---|---|
| MLB | `statsapi.mlb.com` schedule (5 games, 23–31 Oct) | `gamePk` = fixture id suffix | game 849805 confirmed: Rays @ Brewers, 2026-10-24T00:00Z |
| NHL | `api-web.nhle.com/v1/schedule` (48 games) | game id = fixture id suffix | 2026020166 Blackhawks/Canadiens and 2026020167 Avalanche/Lightning confirmed with venue, start and both sides |
| EuroLeague | schedule XML, gameday 8 (10 games) | `gamecode` = fixture id suffix | E2026_79 Besiktas/Olympiacos confirmed |

No other sport has a machine-readable official body in this repository. Their rows are labelled
*“capture bundle”*, not “official”, on every page.

## 5. Arithmetic the audit re-derived

* Fair American ↔ probability ↔ fair decimal: 728/728 consistent.
* Offered decimal ↔ offered American: consistent within the rounding span (0.15 percentage points); 4 rows use
  the documented +999900 ceiling sentinel and are counted separately.
* Band flag: `-250 <= fair_american <= +10000`. 631 of 728 rows are inside; only 8 of the 22 high-confidence
  picks are, and **all 8 are alternate lines** — the natural price on those selections is shorter than −250.
* Confidence: high ≥ 70%, medium ≥ 60%. 37 alternate band lines on thin samples are capped at medium with the
  `band_line` flag set, and the audit verifies that every cap is flagged rather than silently applied.

## 6. Prose audit

33 write-ups: 51–88 words, 33 unique texts, 33 unique three-word openings, zero occurrences of the banned
`model`/`verified` families, selection named in every one, and every number in every write-up present in that
fixture's stored facts, inputs or prices (`A8`).

## 7. Open items

Published on `/flagged.html` with sources. The substantive ones are the five-a-sport shortfall (33 of 75), the
coverage gap (127 upcoming OLBG events vs 83 priced fixtures), the empty OLBG golf payload, the provenance
weakness of the fixture layer's capture bundles, the six unresolved conflict-marker lines in `COORDINATION.md`,
the 22 layers CI never rebuilds, and one MLB game carrying four different published probabilities.
