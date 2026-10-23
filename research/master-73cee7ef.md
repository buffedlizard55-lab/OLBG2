# Consolidated desk — session record (`arena/73cee7ef-olbg2`)

- **Session:** `arena/73cee7ef-olbg2` (final integration claim)
- **Branch:** `arena/73cee7ef-olbg2`
- **Desk clock:** 2026-10-23 22:00 UTC
- **Published at:** `/master/` (23 pages)
- **Pipeline:** `scripts/master_data.py` → `scripts/master_build.py` → `scripts/master_verify.py`
- **Tests:** `tests/test_master_73cee7ef.py` (20 tests) inside the repository suite (682 tests)

## 1. What was reviewed, line by line

| Layer | What was read | Verdict |
|---|---|---|
| `data/ledger/matches.json` | 142 OLBG events, one row per event | Used as the listing. Provenance is the embedded payload of OLBG's own pages, not the rendered DOM, and that is stated on every row. |
| `data/ledger/olbg.json` | 287 tip rows (in and out of scope) | Used for prices. Scope filter drops Football 26, Boxing 13, Horse Racing 4, American Football 2. |
| `data/ledger/official.json` | 93 fixtures + 82 club records (NHL 32, MLB 30, EuroLeague 20) | Used for originated prices and for every written prediction. |
| `data/ledger/manifest.json` | 181 captures with requested URL, status, bytes | Produced the capture audit: 60 failures, 32 truncations. |
| `data/ledger/raw/*` | Every stored body checked for error and challenge markers | Nine page families are error or challenge pages; no value here comes from them. |
| `data/ledger/predictions.json` | 19 earlier write-ups | Read. Not republished: five of them lean on tipster prose rather than an official record, and this desk writes its own. |
| `REPO_REVIEW.md` | Historical audit | Two of its statements are contradicted below (F-12, F-05). |
| `research/cadence-a0c8b7f3.md` | Prior research note | Its WST ranking figures disagree with today's live page (MR-01). |

## 2. Live re-reads made in this session

| ID | URL | Value seen | Verdict |
|---|---|---|---|
| LC-01 | `https://www.wst.tv/rankings/` | Zhao £1,265,550; Wu £1,238,900; Trump £1,114,050; Robertson £1,100,200; Selby £1,070,500 | conflicts with the 19:50Z note for #2–#5 |
| LC-02 | `https://api-web.nhle.com/v1/standings/now` | CAR 12 GP 8-2-2 18 pts 47/33; EDM 10 GP 8-1-1 17 pts 47/32; BOS 11 GP 8-2-1 17 pts 42/22; VGK 12 GP 8-4-0 16 pts 46/36 | agrees with the 20:32Z capture |
| LC-03 | `https://api-live.euroleague.net/v1/schedules?seasonCode=E2026&gameNumber=8` | E2026_79 Besiktas v Olympiacos 28 Oct 18:30; E2026_72 Dubai v Paris 27 Oct 17:00 | agrees with the stored fixtures |
| LC-04 | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-26` | WS Game 1 849805 TB @ MIL 2026-10-24T00:00Z; Game 2 849802; Game 3 on 10-26 | agrees |
| LC-05 | `https://www.nba.com/games?date=2026-10-24` | Eight games, MIA @ CHA 18:00 ET first | context only; the repository's own NBA capture is a 403 page |
| LC-06 | `https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Cameron_Menzies_vs_Gerwyn_Price/15?event_id=32383` | Price 3 of 4 tips (75%); pill prints "3 / 031 \| 97%"; every price blank; both selections badged Expired | agrees with the stored tip share; confirms four OLBG presentation defects |
| LC-07 | `https://www.olbg.com/betting-tips/Tennis/3` | Renders "No tips found." while the payload holds tips | confirms geo-filter behaviour |

## 3. Findings published on /master/flagged.html

Sixteen items. The ones that changed what could be published:

- **MR-07 / MR-16** — 60 of 181 official captures failed and 32 were truncated at 300,000 bytes. The OLBG board
  is therefore a floor: the 142 in-scope events are a minimum, not the complete board.
- **MR-06** — every NBA capture returned 403, so no NBA row is priced from official data anywhere in the repository.
- **MR-09 / MR-10** — only three sports have numeric inputs; two covered sports (Golf, Snooker) have no OLBG event
  in the captured board at all, so five picks each is arithmetically impossible today.
- **MR-01** — two sets of World Snooker ranking figures, both linked, neither deleted.
- **MR-11** — no injury feed captured, so no write-up asserts one.
- **MR-15** — EuroLeague tip times are venue-local. The desk now prints "(venue time)" on every such row rather
  than labelling it UTC.

## 4. Corrected arithmetic found during the build

Three defects were found and fixed **before** publication, and are recorded because they would otherwise have
produced confidently wrong picks:

1. **Reversed puck-line pairing.** The first build paired `home -1.5` with `away -1.5`, so a 70% cover was
   labelled with its 30% opposite. The pairing is now written out: `home -1.5` ↔ `away +1.5`, `home +1.5` ↔
   `away -1.5`, and the verifier recomputes every price from its own probability.
2. **Unbounded estimates.** An 8-1-1 start produced a −3800 money line. Estimates are now held inside the range
   each sport trades in (NHL 24–76%, EuroLeague 12–88%, MLB 30–70%), and the bounds are published.
3. **Poisson overflow on basketball totals.** A 160-point total cannot be summed as a Poisson. Totals above 40
   points now use a normal approximation with variance equal to the mean.

## 5. What the desk contains

| Item | Count |
|---|---|
| Matches | 232 (142 OLBG-listed, 93 with an official fixture link, 3 with both) |
| Markets published | every money line, puck line/handicap and totals line for the 93 official fixtures, plus every OLBG quote |
| Graded picks | 207 (23 matches had already started and are never picks) |
| High confidence | 87 |
| High confidence **and** in the −250…+10000 window | 8 |
| Written predictions | 11 (Ice Hockey 6, Basketball 5) |
| Review items | 16 |
| Failed captures listed with URL and status | 60 |

## 6. Honest limits

- Five predictions per sport is not reached. Two sports have no event in the captured board and twelve have no
  official per-match statistics, so a write-up there would have no facts to stand on. The coverage table on
  `/master/predictions.html` gives the reason sport by sport.
- The in-band high-confidence list is eight rows because 70.00% and −250 are the same price to within 1.43
  points. Stretching estimates to fill the window was rejected.
- OLBG prices carry the bookmaker margin. A market-implied probability is therefore not our estimate and is
  labelled as such on every row.
- No injury, suspension or line-up information is asserted anywhere on the desk.

## 7. Late additions (22:00Z–22:40Z)

Two sports had no row at all in the 22:00Z build. Both were closed with first-hand reads rather than by copying
another layer:

| Capture | URL | What was read | Used for |
|---|---|---|---|
| LC-08 | `https://www.wst.tv/matches/` | Northern Ireland Open 2026: every completed round result, the first semi-final pairing (Kyren Wilson v Sam Craigie, 24 Oct 08:00) and the unfinished quarter-final (Jak Jones 4-4 Scott Donaldson) | two snooker fixtures, our own frame-based price, MR-18, MR-19 |
| LC-09 | `https://www.pgatour.com/leaderboard` | Butterfield Bermuda Championship, Port Royal: cut line &minus;5, second-round leaderboard with both round scores, positions, and the tour page's FanDuel odds module | one golf outright event with nine priced selections, MR-17 |

Consequences recorded rather than glossed over:

- The snooker price is ours, built from frames won and lost in the rounds captured (Wilson 10-4, Craigie 18-10).
  It gives Wilson 66%, which is **below** the 70% floor, so snooker contributes a medium-confidence pick and no
  prediction. It is not inflated to reach the grade.
- The golf prices are FanDuel's, embedded in the official tour page. They are labelled market-implied and kept
  apart from tour data on the same row.
- The second semi-final has no opponent (MR-19), so it is published unpriced.

## 8. The five-per-sport ceiling

The brief calls five high-confidence picks per sport per day a maximum, not a quota. `scripts/master_top5.py`
applies that ceiling literally and `master/top5.html` prints the result sport by sport: 28 selections across 14
sports, 7 inside the price window, and a printed shortfall wherever five were not available. Nothing below high
confidence is promoted to fill a slot, and the verifier fails if any sport shows six.
