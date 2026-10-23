# Signal desk research notes — session `6b10ecda`

Scope: `/signal/`, `data/signal/**`, `scripts/signal_*.py`, `tests/test_signal_6b10ecda.py`,
this file, and append-only entries in `COORDINATION.md`. Nothing else in the repository was
edited by this session.

Published at `https://buffedlizard55-lab.github.io/OLBG2/signal/index.html`.

---

## 1. What OLBG looks like from the outside

Observed first-hand on 23 October 2026 from `https://www.olbg.com/`,
`https://www.olbg.com/betting-tips` and `https://www.olbg.com/betting-tips/Darts/15`:

| Element | What the site does |
| --- | --- |
| Sport index URL | `/betting-tips/{Sport}/{sportId}` — e.g. `/betting-tips/Darts/15` |
| Event URL | `/betting-tips/{Sport}/{Region}/{Competition}/{Event_Name}/{sportId}?event_id={eventId}` |
| Sport ids read first-hand | Football `1`, Horse Racing `2`, Baseball `12`, Darts `15` |
| Markets seen on in-scope events | `Full Time Result`, `Win Match 2-way`, `Money Line`, `Win Tournament`, `Daily Racing` |
| Row contents | selection, market, tip count (`26/31 Win Tips`), tip share %, comment count, expert count, Value Rating |
| Ordering | default order is by number of community tips; the % is the share of tips on that selection |

The important structural point for this desk: **OLBG's percentage is a popularity measure, not a
price.** It is recorded in `data/signal/captures/olbg_taxonomy.json` as a description of the source
site and is never used as an input to any price published under `/signal/`.

Numeric ids for the other twelve in-scope sports were not exposed on any page read first-hand, so
they are left blank rather than guessed.

## 2. Sources that worked

| Sport | Official source | What it gave |
| --- | --- | --- |
| Ice Hockey | `api.nhle.com` team summary + `api-web.nhle.com` schedule/score | 32 teams' GF/GA/points%, 14 fixtures |
| Baseball | `statsapi.mlb.com` schedule + standings | World Series games 1–5, 2026 runs scored/allowed |
| Basketball | `api-live.euroleague.net` schedules + standings | Round 8 fixtures, full table after Round 7 |
| Rugby League | `nrl.com/draw` rounds 1 and 2 | five results, four upcoming World Cup fixtures |
| Rugby Union | `premrugby.com/fixtures-results` Round 4 | five fixtures with last-three form strings |
| Snooker | `wst.tv` fixtures + full world ranking | 12 matches, ranking money to 36th place |
| Handball | `eurohandball.com` calendar | 17 fixtures, one official first-leg result |
| Golf | `europeantour.com` schedule + leaderboard | Genesis Championship, 36-hole scores (top 25) |
| Motor Racing | `formula1.com` calendar + drivers' standings | round 18 dates, points to P8 |
| Cricket | `cricket.com.au` live & upcoming | one live final, five upcoming fixtures, three results |
| Gaelic Sports | `gaa.ie/fixtures-results` | one fixture (Shinty-Hurling International final) |
| Greyhounds | `gbgb.org.uk/racing/open-races` | five open-race heats, no runners |
| Tennis | `atptour.com/en/scores/current` + draw index | six quarter-finals, three events |
| Darts | `olbg.com/betting-tips/Darts/15` (operator, flagged) | twelve matches, one outright |
| Volleyball | `cev.eu` | competition state only, no fixture list |

## 3. Sources that failed (do not retry blind)

* `cdn.nba.com/.../todaysScoreboard_00.json` — HTTP 500 twice.
* `stats.nba.com/stats/scoreboardv3` and `core-api.nba.com/.../gamecardfeed` — refused / HTTP 500.
* `pdc.tv/tournaments`, `pdc.tv/live-scores` (redirects to `/calendar/`) — cookie-consent markup only
  across all chunks; no draw, no averages, no Order of Merit.
* `icc-cricket.com/fixtures-results` — client-side placeholder.
* `cricket.com.au/fixtures-results` — 404 (the working path is `/matches?isCompleted=0`).
* `premrugby.com/standings` — client-side table, no rows served.
* `unitedrugby.com/fixtures` — 404.
* `plusliga.pl/games.html` — redirects to another league's completed results.
* `championsleague.cev.eu/en/calendar/` — Page Not Found.
* `gbgb.org.uk` homepage — completed results only; the forward calendar lives at `/racing/open-races/`.

## 4. Interpretation decision published on the site

The brief sets two rules that overlap: a high-confidence pick implies roughly a 70%+ win
probability, and the focus band runs from −250 to +10000. A fair price of −250 *is* 71.43%, so the
strict intersection is the window 70.0%–71.43%. The dashboard publishes three tiers rather than
silently widening the rule:

* **Tier A** — inside the window (today: empty, stated explicitly);
* **Tier B** — above 70% but priced shorter than −250;
* **Tier C** — strongest selections that satisfy the price band.

Every table carries an `in band` / `outside band` marker.

## 5. Irregularities raised

* `CR-01` — three unresolved git conflict regions in `COORDINATION.md` on `main` (around lines
  3216–3307, 3437–3549, 3609–3628, last tagged `>>>>>>> 140baf3`). The file is append-only and
  shared by concurrent sessions, so this desk logged the defect instead of rewriting another
  session's text.
* `SG-TZ1` — premrugby.com, nrl.com and olbg.com all render kick-off times in the viewer's zone; the
  fetch proxy resolved to US Eastern, so every time was converted as UTC = served + 4h.
* `SG-RL1` — the Rugby League World Cup is two rounds old; on published differentials alone Fiji
  grade above Australia. The row is published as the data reads, with the flag attached.
* `SG-BK1`, `SG-DA1`, `SG-VB1`, `SG-GH1`, `SG-GA1`, `SG-CR3`, `SG-HB1`, `SG-SN2`, `SG-GO1`,
  `SG-MR1`, `SG-TE1` — each records a specific value that an official source did not publish, with
  the fixture left blank rather than filled in.
* `SG-INJ1` — no official source captured today publishes a machine-readable injury or availability
  list for these fixtures, so write-ups never assert an injury and say when nothing was published.

## 6. Rebuild

```bash
python3 scripts/signal_predictions.py   # captures -> matches/predictions/flagged/sources
python3 scripts/signal_build.py         # -> signal/*.html
python3 scripts/signal_verify.py        # 750 self-audit checks, exits non-zero on any problem
python3 -m unittest tests.test_signal_6b10ecda
```
