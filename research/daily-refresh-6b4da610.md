# Daily five-a-sport picks desk — session `arena/6b4da610-olbg2`

Captured 2026-10-22 between roughly 21:00 and 21:45 UTC. Builds `/daily/` from
`data/daily/`. Baseline: `main` at `9068101` (merge of PR #123).

## Why this layer exists

The standing brief asks for updated fixtures for every covered sport, our own lines, a
winner per match with a confidence label, and five high-confidence picks per sport priced
between −250 and +10000. The repository already held fifteen overlapping desks, so this
pass did not add another sweep of the same ground: it priced the **next three days**
(23–25 October) from a small number of pages read live in this session, and it recorded
every sport it could not price.

## What was fetched, and from where

| Source | Read for | When | Result |
|---|---|---|---|
| `api-web.nhle.com/v1/schedule/2026-10-23` | NHL fixtures and start times, 23–25 Oct | 21:0x UTC | 2 games on 23 Oct, 12 on 24 Oct, fixture ids and UTC start times |
| `nhl.com/standings/2026-10-22/wildcard` | NHL records, goals for/against, streaks | 21:2x UTC | All 32 clubs, "current as of Oct 22, 4:59 PM EDT" |
| `statsapi.mlb.com/api/v1/schedule` | World Series games 1–2 | 21:0x UTC | Two fixtures, both at American Family Field |
| `statsapi.mlb.com/api/v1/standings` | Brewers and Rays records | 21:1x UTC | 103-59 and 98-64 |
| `stats.unitedrugby.com/match-centre/2026-27/4` | URC Round 4 fixtures | 21:1x UTC | 8 fixtures, 23–24 Oct |
| `stats.unitedrugby.com/match-centre/table/2026-27` | URC table | 21:1x UTC | 16 clubs, points, PF/PA, form |
| `nrl.com/draw/rugby-league-world-cup/2026/round-2/` | RLWC Round 2 draw | 21:2x UTC | 5 fixtures, venues, pool positions |
| `euroleaguebasketball.net/en/euroleague/standings/` | EuroLeague table | 21:3x UTC | 20 clubs, records, PF/PA |

Two pages returned no usable data and are recorded as such: `afl.com.au/aflw/ladder`
(JavaScript shell, no rows) and `pdc.tv` (cookie-consent wall). `api-live.euroleague.net`
returned an empty body. EuroLeague standings were then read from the rendered page.

## What was inherited rather than re-verified

* AFLW ladder positions, points and percentages — carried from the committed 22 October
  capture in `data/final`, with `afl.com.au/aflw` as the source link.
* ICC ODI ratings (Pakistan 103, England 94) — carried from the same capture.
* IRL ranking points and Round 1 scorelines — the Round 2 draw, venues and pool positions
  were re-read; the rating numbers were not.

These three are named on `/daily/flagged.html` under "Inputs carried over rather than
re-verified". Everything else on the desk was read in this session.

## The finding worth reading

Comparing the freshly read NHL standings with the team lines already stored in
`data/final/matches.json` for the same fixtures produced **19 conflicts** (IR-NHL-01 to
IR-NHL-19). Most are single-goal drift, consistent with captures taken at different points
on 22 October, but one is a full result: Florida are stored as 5-2-2 (30 GF / 25 GA) and
are 5-3-2 (31 GF / 30 GA) on the standings page — a loss and five goals of difference.
Ottawa moved from 6-3-0 to 7-3-0. Detroit is two goals against out. The model on this desk
uses the fresh figure; the older values are left untouched because `data/final` belongs to
another session's scope, and the conflict is published for review instead.

The second finding is arithmetic, not sporting. A 70% chance prices at −233. The brief asks
for ≥70% picks priced no shorter than −250, so the compliant window is 70.0%–71.4%
exactly. This desk publishes that window and marks band membership, instead of nudging
handicaps to manufacture compliant prices.

## Outputs

* 38 fixtures, 7 sports, 224 originated prices, 28 picks, 18 high confidence, 6 high **and**
  in band.
* 28 hand-written predictions, 48–82 words, every one naming its selection and its source.
* 10 sports with no line and a written reason for each.
* 16 pages under `/daily/`, 20 tests in `tests/test_daily.py`, wired into the CI drift gate.

## Honest limits

Four of seven sports reach five picks. Basketball reaches five by using three markets on
three fixtures. Baseball (two World Series games) and cricket (one tri-series match) cannot
reach five distinct fixtures in this window. Ten sports were not captured at all. No
bookmaker price was read, so nothing here is a value comparison. No player-level fact was
verified, so no prediction mentions a player.
