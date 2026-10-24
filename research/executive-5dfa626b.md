# Executive desk — research and verification notes

Session: `arena/5dfa626b-olbg2` · captured 2026-10-24 · desk at `executive/`

## Scope

The standing brief asks for the exact 15 OLBG sport categories, priced with our own
originated lines, one pick per fixture, a low/medium/high conviction label, unique
written previews, high-conviction selections concentrated on matches priced between
−250 and +10000, and an official source link on every table row. This session builds a
new, non-overlapping desk at `/executive/` that does not touch the existing
`zenith/` or `omega/` desks.

## What was captured

`scripts/executive_seed.py` reads official governing-body pages live in this session and
stores a deterministic fixture bundle in `data/executive/fixtures.json` (71 fixtures
across 14 sports) plus a 33-entry official source registry in
`data/executive/sources.json`. Every fixture row carries per-side strength inputs, the
basis for each, and a list of facts each with its own source URL. No value is inferred.

| Sport | Fixtures | Strength basis |
|---|---|---|
| Ice Hockey (NHL) | 8 | NHL.com points percentage `(2W+OTL)/(2GP)` |
| Basketball (NBA) | 8 | NBA.com power-rankings slot |
| Motor Racing (F1) | 5 | Championship points → outright win estimate |
| Tennis (ATP) | 3 | ATP ranking / event seeding |
| Golf (PGA) | 5 | Leaderboard position after R3 |
| Cricket | 5 | Default (no comparable strength table) — flagged |
| Darts (PDC) | 5 | PDC ranking / CSW bracket win probability |
| Snooker (WST) | 4 | WST world ranking |
| Volleyball (SuperLega) | 5 | Round-1 points / 3 |
| Rugby Union (URC) | 5 | Default (no published strength table) — flagged |
| Handball (EHF) | 5 | Default — flagged |
| Gaelic Sports (GAA) | 5 | Default — flagged |
| Greyhounds | 5 | Starting-price-implied probability — flagged market-derived |
| Baseball (MLB) | 3 | Default (post-season series) — flagged |
| Rugby League | 0 | No live fixture on 24 Oct 2026 |

## Own lines

`scripts/executive_model.py` originates fair prices from the stored inputs rather than
quoting any bookmaker. Two-way probabilities use `p(home) = sigmoid(K·(s_home − s_away) +
home_edge)` with `K = 3.0` and `home_edge = 0.15`; outright probabilities are the event
position estimates recorded in the fixture. Fair American and decimal prices are
reciprocals. A fixture whose only strength input is a league-average default is forced to
low conviction, so an unmodelled matchup cannot masquerade as a conviction call.

## The −250 to +10000 window

The band maps to probability 0.714 down to ~0.0099. High conviction is p ≥ 0.70, so the
intersection is only the narrow p ∈ [0.70, 0.714] slice. In this snapshot 1 of the 12
high-conviction picks (Houston Rockets, fair −242) prices inside the window; the other 11
are stronger favourites priced below −250. Those are published separately rather than
dropped. The eight verified medium/high picks that price inside the window are surfaced as
the executive-summary priority list.

## Known limitations

- 5 sports (cricket, rugby union, handball, Gaelic sports, baseball) have no comparable
  governing-body strength table for this date, so their inputs are defaults and their
  conviction is capped at low. These are flagged on `executive/flagged.html`.
- Greyhound strength is derived from the overnight starting price, i.e. a market-derived
  input, and is flagged as such.
- Rugby league has no live fixture: both 2026 professional seasons (NRL and Super League)
  had ended before 24 October 2026, so the category page documents the season-end status
  with official sources and carries no priced pick.
- Five previews per sport is a target. Baseball (3), Snooker (4) and Tennis (3) fall short
  and the shortfall is flagged rather than padded with invented selections.

## Reproduce

```
python3 scripts/executive_seed.py
python3 scripts/executive_model.py
python3 scripts/executive_predictions.py
python3 scripts/executive_verify.py
python3 scripts/executive_build.py
python3 -m unittest tests.test_executive_5dfa626b
```
