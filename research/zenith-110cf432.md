# Zenith 15-sport OLBG desk — research and verification log

**Session:** `arena/110cf432-olbg2` · **Branch:** `arena/110cf432-olbg2`  
**Snapshot cutoff used for fixture timing:** 2026-10-23 21:45 UTC  
**Published subsite:** `/zenith/` (dedicated Pages subdirectory; root navigation integration is requested from the active shared-root owner).

## Scope and honest state

The desk is limited to the fifteen sports requested: Golf, Volleyball, Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball and Rugby League. Gaelic Sports preserves OLBG's two routes (Gaelic Football id 25 and Hurling id 26) under one category. It does not silently include other OLBG sports.

This is **not** an exhaustive worldwide match schedule or a live betting feed. The OLBG tip-object source register in `/data/ledger/olbg.json` was captured at `2026-10-23T20:36:17Z`; the official fixture/fact bundle reused for the 93-row schedule came from the Cadence capture at `2026-10-23T19:00–19:50Z`. I re-read a broad set of official pages and event pages in this session, but did not re-fetch and independently reconcile every one of the 93 rows. The site preserves per-row source URLs, the original snapshot time and this limitation rather than claiming all rows are live at 21:45Z. Exact current start times not in the official capture remain blank or explicitly marked unconfirmed.

## Output counts (reproduced by the checked-in pipeline)

| Output | Count | Definition |
|---|---:|---|
| Covered OLBG event IDs | 218 | Unique event IDs grouped from stored OLBG tip objects; excludes non-covered sports. |
| Official-evidence fixtures | 93 | Fixture rows in the same-day official-source bundle across all 15 covered sports. |
| Originated selections | 728 | Captured official-input probability records with fair American/decimal prices recalculated by Zenith; no OLBG quote is used as a probability input. |
| Graded picks | 122 | One selected candidate for eligible priced fixtures; inherited evidence-tier grade is retained. |
| Human previews | 33 | Unique official-fact-linked writeups of at least 30 words; target is five per sport where support exists. |
| Review findings | 23 | 12 coverage/shortfall findings plus 11 generated repository/source-integrity findings (see `data/zenith/flagged.json` and `repo_audit.json`). |
| Static pages | 26 | Overview, evidence tables, review pages and 15 sport subpages. |

These totals describe this layer only. They are not additive to other overlapping repository snapshots.

## OLBG reverse-engineering

- Main sport route: `/betting-tips/{slug}/{sportId}`; all-events route: `/betting-tips/{slug}/All_{slug}/All_Events/{sportId}`; event detail: an event URL with `?event_id={id}`.
- OLBG hub tip objects provide the event ID/title, competition, UTC start, market alias, selection, tip count, comments, tipster confidence and (on the captured hub) a displayed quote. The inventory stores these separately from Zenith's fair-price lines.
- OLBG's region-specific event pages read during this session displayed false “Expired” headers for upcoming events to a US visitor, blank `WIN @` values and a percentage denominator string-concatenation defect. Examples and the literal displayed values are stored in `data/zenith/olbg_events.json` under `live_event_page_probes`.
- A second within-page inconsistency appeared on NBA event 534842: the totals selection showed 221.50 while its inline “hcap” pill showed 223.50. These are published as source irregularities, not silently reconciled.
- Capture counts by sport, each event ID, OLBG URL, raw quote fields and the distinction between historical capture time and the later status cutoff are in `data/zenith/olbg_events.json`.

## Official-source checks performed in this session

The following primary sources were directly read through the agent's web/fetch tools. A structured URL-and-field log is stored in `data/zenith/captures/source_read_log.json`. No raw HTTP response archive is claimed there; the source links are provided for manual review.

| Sport | Official source(s) re-read | Example confirmed fields / issue |
|---|---|---|
| Golf | [PGA Tour leaderboard](https://www.pgatour.com/leaderboard), [DP World Tour Genesis Championship](https://www.europeantour.com/dpworld-tour/genesis-championship-2026/) | Bermuda event dates, field/round/score leaders; DP World Tour event dates/location. No golf fixture row was present in the captured OLBG inventory. |
| Volleyball | [Lega Volley weekend schedule](https://www.legavolley.it/2026/credem-banca-superleague-weekends-games-45/?lang=en), [current SuperLega table](https://www.legavolley.it/classifica/?IdCampionato=999&lang=en), [VBL fixtures/table](https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/hauptrunde.xhtml) | Italian matchday fixtures, opening-round results and table. VBL fixture search result exposed Oct 24 Friedrichshafen–Karlsruhe, but not every volleyball tie was separately re-read. |
| Rugby Union | [URC Round 4 team announcements](https://www.unitedrugby.com/latest/news/round-4-team-announcements/), [Premiership official match centre](https://premrugby.com/match-centre/294925/news), [Premiership standings](https://www.premrugby.com/competitions/gallagher-prem/standings) | URC fixtures/lineups and official PREM matchup/date. |
| Cricket | [Cricket Australia upcoming fixtures](https://www.cricket.com.au/matches?year=2026&isCompleted=0), [Tasmania–Victoria match centre](https://www.cricket.com.au/matches/CA:40681/tasmanian-tigers-men-victoria-men-one-day-cup-2026-27), [WA–NSW match centre](https://www.cricket.com.au/matches/CA:40683/western-australia-men-nsw-men-one-day-cup-2026-27), [NZ–India T20I](https://www.cricket.com.au/matches/CA:41095/new-zealand-men-india-men-new-zealand-v-india-t20is-2026-men), [Pakistan–England ODI](https://www.cricket.com.au/matches/CA:40981/pakistan-men-england-men-pakistan-odi-tri-series-2026-men) | Confirmed pairings, match date, venue and event status. Match centres showed team announcements and scorecard unavailable at read time; player selections were therefore not filled. |
| Snooker | [WST matches](https://www.wst.tv/matches/), [rankings](https://www.wst.tv/rankings/) | The WST page displayed Oct 24 semi-final pairing Kyren Wilson–Sam Craigie and official current rankings. A separate session with WST match-centre ids did not always render opponent details; wildcard names remain unfilled. |
| Darts | [PDC Round 1/2 report](https://www.pdc.tv/news/2026/october/22/nine-dart-star-woodhouse-sets-up-van-veen-clash-dortmund/), [Humphries withdrawal](https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship), [Day Two schedule](https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest) | Current draw and Humphries illness/replacement; previously listed Oct 23 round-one matches had started or finished by the later read. |
| Baseball | [MLB StatsAPI schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-31&hydrate=team,probablePitcher,decisions,linescore), [MLB standings](https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason), [official pitcher stats](https://statsapi.mlb.com/api/v1/people?personIds=607259,694819,656876,701656&hydrate=stats(group=[pitching],type=[season],season=2026)) | World Series teams, series metadata and probable starters. The schedule JSON combined a Preview state with in-progress linescore data for one game; this inconsistency is explicitly flagged, and the desk does not assert live status. |
| Gaelic Sports | [Munster GAA event calendar](https://munster.gaa.ie/fixtures/events-calendar/), [GAA panels](https://www.gaa.ie/article/ireland-panels-announced-ahead-of-shinty-hurling-camogie-internationals), [Cork final](https://munster.gaa.ie/event/2026-cork-premier-senior-hurling-championship-final/) | Ireland–Scotland shinty double-header and Cork final date, venue and teams. Other county finals are not all independently audited in this pass. |
| Greyhounds | [GBGB Scurry/Oaks report](https://www.gbgb.org.uk/dunstall-park-set-for-scurry-showdown-as-category-one-classic-hots-up/), [GBGB finals report](https://www.gbgb.org.uk/signet-nayla-chases-oaks-glory-as-hutton-targets-dunstall-park-double/), [Category One schedule](https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/) | Official event schedule states Oct 24 Dunstall Park Scurry Gold Cup and Oaks. The schedule URL retains a `2025` path component; source-year mismatch is flagged. |
| Tennis | [ATP Almaty results](https://www.atptour.com/en/scores/current/almaty/9410/results), [ATP report](https://www.atptour.com/en/news/medvedev-almaty-2026-report-friday), [WTA Ningbo semi-final preview](https://www.wtatennis.com/news/4597893/ningbo-semifinals-preview-leylah-fernandez-vs-marie-bouzkova-diana-shnaider-vs-elena-rybakina) | ATP results showed the Almaty semi-final progression had already occurred at read time. WTA preview provided pairings, head-to-head and recent form. Later official result status supersedes an earlier fixture snapshot. |
| Motor Racing | [F1 United States GP](https://www.formula1.com/en/racing/2026/united-states), [2026 drivers standings](https://www.formula1.com/en/results/2026/drivers) | Official COTA session schedule/results and drivers points. |
| Handball | [EHF Champions League standings/calendar](https://ehfcl.eurohandball.com/men/2026-27/standings/), [EHF results/news](https://www.eurohandball.com/en/news/en/magdeburg-aalborg-and-paris-in-main-round-four-clubs-out) | Group standings and Oct 28/29 EHF fixtures were visible. Not every domestic handball pairing had a numeric official source checked. |
| Ice Hockey | [NHL schedule](https://api-web.nhle.com/v1/schedule/2026-10-23), [NHL standings](https://api-web.nhle.com/v1/standings/2026-10-23) | Oct 23/24 game ids, start times, venue and club form/stat lines. |
| Basketball | [NBA schedule](https://www.nba.com/schedule?date=2026-10-23), [NBA standings](https://www.nba.com/standings), [official injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/), [5:15 p.m. ET report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_05_15PM.pdf) | 12-game official slate, venue/tip times, opening-week records, report timestamp and listed designations. One extracted row’s team/player alignment was suspect, so inherited player injury claims are withheld pending review. |
| Rugby League | [NRL Round 2 draw](https://www.nrl.com/draw/?competition=131&round=2&season=2026), [Round 1](https://www.nrl.com/draw/?competition=131&round=1&season=2026), [Round 3](https://www.nrl.com/draw/?competition=131&round=3&season=2026), [Australia–Fiji match centre](https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/australia-v-fiji/) | Official RLWC rounds, date, team lists and venue. OLBG's captured Rugby League events were 2027 outright futures, not these 2026 fixtures; this mismatch is flagged and no invented OLBG event id is assigned. |

## Repository audit / irregularities

`data/zenith/repo_audit.json` is generated with a structural scan and curated fact/source limitations. The review identified inherited prediction prose containing internal words, conflict-marker-like lines in the append-only coordination history, old or overlapping snapshots, OLBG regional rendering defects, gaps between OLBG's captured schedule and governing-body fixtures, and fair odds that must not be mistaken for live bookmaker offers. Each item has a source or artifact URL.

No historical source files belonging to other sessions were edited. A root navigation request to the active integration owner is recorded in `COORDINATION.md`.

## Reproduction and checks

```sh
python3 scripts/zenith_capture_sources.py
python3 scripts/zenith_seed.py
python3 scripts/zenith_olbg.py
python3 scripts/zenith_model.py
python3 scripts/zenith_predictions.py
python3 scripts/zenith_audit.py
python3 scripts/zenith_build.py
python3 scripts/zenith_verify.py
python3 -m unittest tests.test_zenith_110cf432 -v
```

The Zenith verifier checks fixture scope and source links, fair-price arithmetic and the band predicate, confidence and prediction constraints, OLBG quote separation, every rendered data row's external source link, and local links. It is structural/provenance validation; it cannot prove an external page will remain unchanged after capture.
