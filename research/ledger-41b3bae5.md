# Ledger desk research note — session `arena/41b3bae5-olbg2`

Date: 2026-10-23 · desk: `/ledger/` · capture window 19:28:51Z – 19:55:42Z · snapshot anchor 19:55:42Z

This note records how the OLBG site was reverse-engineered, what was captured first hand, how the
prices were originated, and what the desk refuses to publish. It is the companion to
`data/ledger/manifest.json` (every capture with status, timestamp and sha256),
`data/ledger/sources.json` (the source register), `data/ledger/verify.json` (the 18-check audit)
and `ledger/flagged.html` (the review queue).

---

## 1. Reverse-engineering OLBG

### 1.1 Sport taxonomy

`https://www.olbg.com/betting-tips` is the index. It links every sport page, so the numeric id
inside OLBG's URL schema is public:

| Sport | id | Sport | id | Sport | id |
|---|---|---|---|---|---|
| Football | 1 | Cricket | 7 | Motor Racing | 14 |
| Horse Racing | 2 | Snooker | 8 | Darts | 15 |
| Tennis | 3 | Rugby Union | 9 | Boxing | 16 |
| Basketball | 4 | Rugby League | 10 | Cycling | 17 |
| Golf | 5 | American Football | 11 | Handball | 20 |
| | | Baseball | 12 | Volleyball | 21 |
| | | Ice Hockey | 13 | Gaelic Football | 25 |
| | | | | Hurling | 26 |
| | | | | Greyhounds | 28 |

The brief's fifteen sports map to Golf 5, Volleyball 21, Rugby Union 9, Cricket 7, Snooker 8,
Darts 15, Baseball 12, Gaelic Sports 25 + 26, Greyhounds 28, Tennis 3, Motor Racing 14,
Handball 20, Ice Hockey 13, Basketball 4, Rugby League 10.

Two URL shapes matter, and they are not equivalent:

```
https://www.olbg.com/betting-tips/<Sport>/<id>                                  (hub, tip-driven)
https://www.olbg.com/betting-tips/<Sport>/All_<Sport>/All_Events/<id>            (all-events listing)
https://www.olbg.com/betting-tips/<Sport>/All_<Sport>/All_Events/<Slug>/<id>?event_id=<n>   (one event)
```

### 1.2 The tip object

Every hub page serialises its tips as a flat payload before hydration. The fields that matter:

```
id, selection, market_alias, odds, american_odds, fractional_odds,
event_start_unix_timestamp, eventUrl (?event_id=<n>), event_name_alias,
tournament, venue, address, event_is_match, has_live_scores, confidence, expired
```

`scripts/ledger_seed.py` parses that literal form with a tolerant field regex — it never evaluates
the payload — then collapses duplicate tips for the same event with
`(sport, normalised event, market, selection)`, keeping the copy that carries an `event_url`.

### 1.3 What the pages do not give

* The hub lists **only events OLBG has tips for**. It is not a full slate. Golf and Snooker had
  zero live tip objects at capture time.
* `/sports/<Sport>/top_tips?paginate=1-100&…` is referenced inside the payload but returns 404
  when requested directly (it is XHR-gated), so pagination cannot be reproduced.
* OLBG mixes out-of-scope sports (Football, Horse Racing, Boxing, American Football) into the same
  tip stream; those rows are dropped at seed time rather than published.
* OLBG's quoted price is a bookmaker price. It is published in its own column, labelled `OLBG
  quote`, and is never presented as our line.

Counts at capture: 295 tip rows over 44 OLBG pages, collapsing to 260 distinct events, of which
**143 are upcoming in the fifteen requested sports**.

---

## 2. Capture and provenance

`scripts/ledger_capture.py` fetches a request list on a GitHub Actions runner (the sandbox has no
outbound access to these hosts) and writes each response verbatim. Each manifest entry records
`key, url, sport, kind, status, fetched_at, bytes, sha256, stored_as`.

* 181 capture attempts, 124 returned 200 with a body stored under `data/ledger/raw/`
* Bodies are stored as `.txt` even when they are HTML: the repository link checker reads every
  `.html` as UTF-8, and two vendor pages were not valid UTF-8
* `scripts/ledger_verify.py` re-hashes every stored body against the manifest, so a silent edit to
  a capture is caught before publication

Official inputs that parsed into numbers:

| Source | Shape | Used for |
|---|---|---|
| `api-web.nhle.com/v1/schedule/<date>`, `/v1/standings/now`, `api.nhle.com/stats/rest/en/team/summary` | JSON | 32 NHL team records, 32 fixtures |
| `statsapi.mlb.com` schedule (`hydrate=probablePitcher`), `standings?leagueId=103|104`, `teams/stats` | JSON | 30 MLB team records, probable pitchers, fixtures |
| `api-live.euroleague.net/v1/{schedules,standings}?seasonCode=E2026` | XML | 20 EuroLeague teams, fixtures (venue-local times, published as served) |

Everything else (cricket.com.au, WTA, WST, PDC, DP World Tour, F1, GAA, GBGB, EHF, Premiership,
RLWC) was captured as HTML and read for the prose only; where the page was a JavaScript shell the
numbers were not there to read, which is why those sports carry no originated price.

---

## 3. Matching OLBG rows to official fixtures

A row is only marked verified when an official capture says the same two sides meet within a day of
the OLBG start time. North-American feeds are matched on the team nickname (`Oilers`, `Brewers`),
EuroLeague on the full club name. Result at capture: **10 of 143** rows matched (3 against a
fixture feed, 7 against an official page); 133 remain `unmatched` and are published as OLBG
listings only, with no line and no preview.

The low match rate is a property of the slate, not of the parser: OLBG's upcoming list is dominated
by domestic handball, volleyball and greyhound meetings whose governing bodies publish no machine
readable schedule that this session could reach.

---

## 4. Originating our own lines

`scripts/ledger_model.py` prices only fixtures whose season records were captured as numbers: NHL,
MLB and EuroLeague, 93 fixtures in total, 744 selections.

* **Ratings.** `r = 1500 + 600·(win% − 0.5) + 25·(goal difference per game)`, with a 45-point home
  edge (about six percentage points of win probability).
* **Totals.** Team attack and defence rates combined against the league average, then a Poisson
  total; the published total is the half-line nearest the expected total.
* **Handicaps.** Puck line and run line at ±1.5 from the same Poisson pair; NBA-style spreads from
  a normal approximation on expected points for EuroLeague.
* **Ties.** Hockey ties after regulation are split 50/50, which is the standard shootout
  approximation, not a claim about the shootout.
* **No margin.** Prices are fair prices: decimal = 1/p. Two-way markets sum to 1.000, and
  `ledger_verify.py` checks it.

Confidence: high ≥ 70%, medium 60–69.9%, low below 60%. The brief's price band (−250 to +10000)
is applied to the fair American price and shown as its own column.

**A structural note the desk makes explicit:** a 70% chance is about −233, which is *shorter* than
the band's −250 floor. High confidence and the band can therefore only overlap between 70.0% and
71.4%. At capture, 155 selections were high confidence and **10** of those fell inside the band.
The desk lists the intersection first, then the rest of the high-confidence rows, rather than
quietly widening either rule.

Across the whole table: 884 selections, 744 originated, 140 market-implied (OLBG's price converted,
labelled as such), 155 high, 10 high-and-in-band.

---

## 5. Written previews

Rules enforced by `scripts/ledger_predictions.py` and re-checked by both the verifier and the tests:
at least 30 words, unique opening, the selection named, at least two cited facts, an official
source link, and no use of the words *model* or *verified*.

19 previews were written from this session's captures (Baseball 5, Basketball 5, Cricket 4, Ice
Hockey 5), 59–69 words each. Injuries are not asserted anywhere: no official team-news feed was
readable, so an injury claim could only have been invented.

26 further previews are **carried** from the superseded `21a0c524` ledger that had already shipped
in the same `/ledger/` path (see §7). They are archived under `data/ledger/inherited/`, their prose
rules were re-run here, and each card states that its facts were not re-read today. They add Golf,
Handball, Motor Racing, Rugby League and Snooker coverage.

Total: 45 previews across 9 of 15 sports. The six without one are named on the flagged page.

---

## 6. The published site

`scripts/ledger_build.py` writes 26 pages: overview, matches (OLBG listing), fixtures (official
slates with our markets), picks, predictions, flagged, sources, verification, methodology,
repository review, a sports index and fifteen sport pages. Everything is plain HTML with inline
SVG and one local stylesheet; there are no external assets, so the desk works offline and under a
strict CSP.

`scripts/ledger_verify.py` runs 18 checks and exits non-zero on failure: body hashes, OLBG row
links, official URL plus capture time on every verified row, pick sources and basis, the prose
rules for both preview sets, internal links and fragments, published counts against data,
the carried-preview provenance, the source register against the manifest, fifteen sport pages,
and a minimum page length.

Reproducibility: every generator takes its clock from `ledger_common.anchor()`, the newest capture
timestamp, so a rebuild is byte-identical. Two consecutive full rebuilds produce an empty
`git diff`.

---

## 7. Consolidation with the other `/ledger/` desk

While this branch was open, session `21a0c524` shipped its own desk on the same path (its commit
`6504035` is on `main`): different scripts, different data files under `data/ledger/`, four pages
that this desk does not generate, and its own test module. Shipping both would have meant two
contradictory desks under one URL and a failing suite, since `data/ledger/lines.json` alone cannot
satisfy two schemas.

The merge therefore consolidates:

* this desk's capture-backed pipeline and fifteen sport pages stay at `/ledger/`
* the earlier desk's 26 previews are preserved and carried, with provenance and live source links
* its archived page copies live under `data/ledger/inherited/pages/` (as `.txt`, for the link
  checker), and its `inputs.json`, `sources.json` and `predictions.json` under `data/ledger/inherited/`
* its four superseded pages, its stylesheet, its `inputs.json` and its now-unmaintainable test
  module are removed, which is recorded here and in `COORDINATION.md`

## 8. What is missing, and where it is published

Fifteen review items (`L-01` … `L-15`) are on `ledger/flagged.html`, each with the failing source
and the effect on the desk:

1. Six sports have no preview and most have no originated line, because their official pages were
   JavaScript shells or did not carry the fixtures.
2. 133 of 143 OLBG rows matched no official source, so they are listings without a price.
3. No injury data anywhere; no readable official team-news feed.
4. OLBG lists only tipped events, so the desk is not a complete slate.
5. Golf and Snooker had no live OLBG tip objects at capture time; their futures markets are shown
   without a line.
6. Greyhound races are published without runner names or form, because GBGB's card did not carry
   them in readable form.

Five sports carry five or more high-confidence picks (Ice Hockey 78, Basketball 48, Volleyball 10,
Handball 6, Rugby Union 5); Baseball carries three. Six sports carry none, and each of those pages
states the shortfall rather than filling it.
