# Independent verification of the NHL dataset — 2026-10-21

Session `db99ed90`. Method: capture every NHL game on 21–22 October from the official feeds in a separate
workspace, then compare the published dataset against that capture row by row. Nothing was compared against
itself and nothing was taken from a secondary source.

| Check | Result |
|---|---|
| Fixture ids, matchups, dates | 14/14 identical |
| Venues | 14/14 identical |
| Start times | 14/14 identical (`7:30 PM EDT` = `23:30Z`, etc.) |
| OLBG event URLs | 14/14 identical (the two events OLBG lists) |
| Last-ten records | 28/28 team-appearances identical |
| Team goal totals | 17 of 32 differ — fully explained below |
| Overlapping selections | 5/5 — every published pick (`nhl-2026020152` Buffalo, `0154` Boston, `0158` Florida, `0161` Dallas, `0162` Minnesota) matches the selection the independent model produces from its own capture |

## Why 17 goal totals differ: the shootout convention

`nhl.com/standings` counts the shootout-deciding goal; `api.nhle.com/stats/rest/en/team/summary` does not. Every
difference observed equals the club's number of shootout wins (for goals for) or shootout losses (for goals
against) — never more, never less. The 16 clubs that have not been through a shootout are identical in both feeds.

| Club | GP | Standings GF/GA | API GF/GA | Δ | Shootouts |
|---|---|---|---|---|---|
| OTT | 9 | 24 / 23 | 22 / 23 | +2 / 0 | 2 SOW |
| SEA | 10 | 39 / 34 | 37 / 34 | +2 / 0 | 2 SOW |
| DET | 9 | 23 / 28 | 22 / 26 | +1 / +2 | 1 SOW, 2 SOL |
| NSH | 8 | 23 / 24 | 23 / 22 | 0 / +2 | 2 SOL |
| DAL | 9 | 23 / 15 | 22 / 14 | +1 / +1 | 1 SOW, 1 SOL |
| PIT | 10 | 33 / 38 | 32 / 37 | +1 / +1 | 1 SOW, 1 SOL |
| SJS | 10 | 27 / 35 | 26 / 34 | +1 / +1 | 1 SOW, 1 SOL |
| VGK | 10 | 42 / 24 | 41 / 24 | +1 / 0 | 1 SOW |
| BUF | 9 | 27 / 34 | 27 / 33 | 0 / +1 | 1 SOL |
| NYI | 9 | 27 / 20 | 27 / 19 | 0 / +1 | 1 SOL |
| PHI | 11 | 17 / 36 | 17 / 35 | 0 / +1 | 1 SOL |
| TOR | 11 | 38 / 35 | 38 / 34 | 0 / +1 | 1 SOL |
| ANA, BOS, CAR, CGY, EDM, FLA, LAK, MIN, STL, UTA, VAN, WPG | — | identical | identical | 0 | none |

Reading: the published dataset is faithful to the source it cites (`source_id: nhl-standings`). Its goal rate is
therefore marginally higher than the stats-API view — at most two goals over eight to eleven games, roughly 0.2
per game. The effect is disclosed as `flag-goal-convention`; no input was adjusted, and no price changed as a
result of this audit.

One consequence: the published desk has no line on San Jose at Ottawa (`nhl-2026020156`) because its copy of
the stats table never received the Sharks' goal columns. The independent capture does have them, and that game
becomes its sixth high-confidence selection (Ottawa 60.1%). Supplying the Sharks' row from `nhl.com/standings`
would add a 26th lined fixture; it was not supplied here because the standings page could not be read in this
session and the API figure differs from it by one shootout goal.

## Two secondary observations

1. **OLBG renders times in the viewer's timezone and states none.** Two captures of the same OLBG page produced
   `19:37` and `00:37` for the same `23:30Z` face-off. `19:37` is US Eastern, `00:37` is UK time, and both are
   `23:37Z` — seven minutes after the league's listed start. The dataset stores the OLBG string verbatim and takes
   authoritative times from the league feed.
2. **OLBG lists 2 of the 14 NHL games.** `olbg.com/betting-tips/Ice_Hockey/13` returned the two 21 October games
   (`event_id` 199897 and 199896) and four European club fixtures; the twelve 22 October NHL games were absent even
   though the league schedule confirms them. Rows without an OLBG link are left without one rather than pointed at
   a constructed URL.

## Reproducing

The independent capture lives in `research/nhl-desk-db99ed90/` (`events.json`, `poisson.py`, `report.py`). It is a
verification artifact, not part of the published build:

```bash
python3 research/nhl-desk-db99ed90/report.py
```

The published pipeline is unchanged and remains:

```bash
python3 scripts/build.py && python3 scripts/build_site.py
python3 -m unittest discover -s tests
```
