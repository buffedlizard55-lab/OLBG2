# OLBG research desk

An evidence-first, static research dashboard published to GitHub Pages. It lists the eligible
fixtures on the OLBG slate that could be matched to an **official league page**, originates its own
fair prices for each one, publishes one selection per match with a computed confidence level, and
writes sourced predictions for the high-confidence picks. Open questions are published rather than
hidden.

**Live site:** https://buffedlizard55-lab.github.io/OLBG2/ (root redirects to `site/index.html`)

## What is covered in this snapshot (2026-10-21 05:55 UTC)

| Sport | Window | Fixtures | Lines | Status |
| --- | --- | --- | --- | --- |
| Ice hockey (NHL) | 2026-10-21 → 2026-10-22 | 14 | Money line, puck line, total | Full |
| Basketball (NBA) | 2026-10-21 | 11 | Money line, spread | Baseline only |
| Baseball (MLB) | 2026-10-21 | 0 | — | Official schedule returns no games |
| Tennis, cricket, rugby union, rugby league, snooker, darts, handball, volleyball, golf, motor racing, greyhounds | — | 0 | — | **Unverified**; no rows published |

Excluded by scope and listed as excluded: soccer/football, horse racing, boxing, UFC/MMA, American
football, Gaelic football, hurling, cycling, specials.

## How the lines are originated

Nothing is copied from a bookmaker. `scripts/model.py` computes every price from official league
inputs using the parameters in `data/meta.json`:

- **NHL** — goal difference per game, shrunk toward the league mean by 12 games, plus a 0.25-goal
  home edge, converted to a win probability with a logistic curve (scale 1.2). Puck line from the
  same margin distribution; total from blended goals for/against, shrunk toward 6.0 goals, priced
  with a normal curve (σ = 1.7). Prices are no-vig fair American odds.
- **NBA** — the 2026-27 season is one game old, so every club is rated league-average and only home
  court (2.5 points) separates the sides. No total is originated.

Confidence is computed, not chosen: **high** requires ≥ 13 points of win-probability edge, a sample
of at least 7 games per side, *and* an evidence pack (the fixture's own official page cited in the
prediction). A big edge without an evidence pack is capped at **medium**; everything else is **low**.

## Local build

Python 3.10+, no third-party dependencies.

```sh
python -m unittest discover -s tests -v
python scripts/build.py
python -m http.server 8000 -d site
```

- `data/meta.json` — snapshot, parameters, exclusions, stated limits.
- `data/sources.json` — the allow-listed source registry. The build **fails** if a fixture, pick or
  flag cites a URL that is not registered here.
- `data/team_inputs/nhl.json` — official standings inputs for all 32 clubs.
- `data/fixtures.json` — 25 fixtures, each with its own official page.
- `data/picks.json` — four written predictions with fact lists and sources.
- `data/flagged.json`, `data/coverage.json` — open items and per-sport verification state.
- `site/` — generated pages, committed so the snapshot is readable without a build.

## Evidence rules

1. A fixture is published only with an official league URL on an approved host
   (`nhl.com`, `nba.com`, `api.nhle.com`, `api-web.nhle.com`, `statsapi.mlb.com`). OLBG is a
   reference, never a fixture source.
2. Every high-confidence prediction is at least 30 words, unique, and names the team, a player,
   current form, recent results and the exact selection. Its fact list and sources sit next to it.
3. Unconfirmed values stay blank and are flagged. Blank is a finding.
4. Source pages change. Treat this as a timestamped snapshot, not a live feed.

See [COORDINATION.md](COORDINATION.md) for the session log, verification trail, open irregularities
and the integration record.
