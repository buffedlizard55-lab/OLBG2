# Coordination

Shared task board for the OLBG research desk. Read this before starting any work.

## Session log

| When (UTC) | Session | Branch | Note |
| --- | --- | --- | --- |
| 2026-10-21 ~05:12 | `bfeb6335` | `arena/bfeb6335-olbg2` | Built the first evidence-first snapshot (2 NHL fixtures, no lines). Merged in PR #1. |
| 2026-10-21 ~05:30 | `4a778bb7` | `arena/4a778bb7-olbg2` | **Active session.** Claimed the full multi-sport slate, an originated-lines model, sourced picks and a site rebuild. Claim committed and pushed before implementation. |

**Branch rule:** this hosting environment fixes one branch per session (`arena/4a778bb7-olbg2`). `session-<id>/<task>` branches cannot be used here; the branch name itself is the session id. All work below stays inside this branch and is integrated to `main` through a pull request.

## Task board

| Task | Status | Owner | File scope | Notes |
| --- | --- | --- | --- | --- |
| Source audit and evidence-first data pipeline (v1) | done | bfeb6335 | `scripts/**`, `data/**`, `tests/**` | 2 NHL fixtures, no originated prices. Superseded by v2 below. |
| Dashboard, category pages, review page (v1) | done | bfeb6335 | `site/**`, `.github/**` | Static Pages site, published from `main` root. |
| Full eligible-sports schedule and original line coverage | done (partial breadth, see flags) | 4a778bb7 | `data/**`, `scripts/**` | 25 fixtures verified (14 NHL, 11 NBA), 64 markets originated, 4 high-confidence predictions. Eleven eligible sports could not be verified and are listed as unverified on the Coverage page, not estimated. |
| Site v2 (sport pages, methodology, sources, flagged page) | done | 4a778bb7 | `site/**`, `tests/**`, `.github/**` | Dashboard, pick sheet, per-sport pages, methodology, source registry and flagged page. 28 tests passing. |
| Integration, re-verification, PR and Pages deploy | in progress | 4a778bb7 | `README.md`, `COORDINATION.md`, `index.html` | Single active session; integration performed here after the data and site tasks. PR link and deploy result recorded below once complete. |

## Requests and handoffs

- No other session is currently active. Any new session must add a claim row here, commit and push it before editing, and keep to a non-overlapping file scope. If a task needs a file another session owns, log the request here rather than editing it.

## Source and verification log — 2026-10-21 UTC

- **NHL schedule** — [nhl.com/schedule/2026-10-21](https://www.nhl.com/schedule/2026-10-21) and [nhl.com/schedule/2026-10-22](https://www.nhl.com/schedule/2026-10-22): 2 games on Oct 21 (PHI @ BUF, FLA @ OTT, both 7:30 PM EDT) and 12 games on Oct 22, each with its own gamecenter link. Every fixture row links its own gamecenter.
- **NHL team inputs** — [api.nhle.com team summary, season 20262027, gameTypeId 2](https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2) (official NHL statistics API) for GP, W, L, OTL, GF, GA, point %, PP%, PK%, shots and faceoff %. [api-web.nhle.com/v1/standings/2026-10-20](https://api-web.nhle.com/v1/standings/2026-10-20) for the standings snapshot timestamp (`2026-10-21T05:14:45Z`) and L10/streak/home-away splits.
- **NBA** — [nba.com/games?date=2026-10-21](https://www.nba.com/games?date=2026-10-21) lists 11 games with tip times and individual game URLs; each fixture row links its own game page. [nba.com/standings](https://www.nba.com/standings) shows the 2026-27 season is 0-1 games old for the four teams that have played, so no meaningful current-season form exists. Individual game pages carry the league's own preview text (e.g. [MIL @ WAS](https://www.nba.com/game/mil-vs-was-0022600086)), which is quoted only where it is explicitly attributed.
- **MLB** — [statsapi.mlb.com schedule for 2026-10-21](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-21) returns `totalGames: 0`; no MLB fixture is published and baseball is recorded as having no scheduled matches on the snapshot date rather than being silently dropped.
- **OLBG** — [olbg.com/betting-tips](https://www.olbg.com/betting-tips) was read for the eligible-sport slate. Only one eligible-sport event appeared on the default page (MIL @ WAS, NBA, "Today 19:10", Money Line). OLBG tip percentages are recorded as OLBG's community data, never as our picks or as official fixtures.
- **OLBG time-zone discrepancy (carried forward)** — OLBG shows 19:37 for both Oct 21 NHL games while the NHL shows 7:30 PM EDT. League time is published; OLBG's unlabelled time is not interpreted. See Flagged for Review.

## Irregularities and limits

- **Needs review:** OLBG start times for the two Oct 21 NHL games do not match the league's published times.
- **Needs review:** OLBG's default tips page surfaces only one eligible-sport event, so the "full slate" cannot be reconstructed from that page alone. League schedules are used as the inventory of matches, and OLBG links are attached only where an OLBG event page was actually found.
- **Limits:** ratings use a small 2026-27 sample (7-11 games per NHL club); NBA has essentially no 2026-27 sample. Prices are model fair odds, not market prices, and no vig is applied. Nothing here is betting advice.

## v2 verification log — 2026-10-21 UTC

- **NHL fixture inventory.** `nhl.com/schedule/2026-10-21` shows 2 games and `nhl.com/schedule/2026-10-22` shows 12 (NBA-style week view: 12 in the Oct 22 table). The 12th Oct 22 game, DET @ VAN (id 2026020165), was missing from the truncated first read of that page and was confirmed separately on the Vancouver club schedule (`api-web.nhle.com/v1/club-schedule/VAN/week/2026-10-19`). All 14 rows carry their own gamecenter URL.
- **NHL inputs.** All 32 clubs taken from `nhl.com/standings`, which states it is current as of Oct 21, 1:13 AM EDT. Every row was checked for GP = W + L + OT; the build enforces that identity.
- **NHL evidence packs.** Gamecenter pages read individually for PHI @ BUF, NSH @ BOS, WPG @ DAL and MIN @ CGY. Each prediction's facts were transcribed from those pages: team rates, players to watch, goalie lines, last-10 results and venue.
- **NBA.** All 11 games on Oct 21 with tip times from `nba.com/games?date=2026-10-21`; MIL @ WAS also opened individually to confirm date, time and arena. `nba.com/standings` shows the season is 0-1 games old, which is why NBA lines are baseline.
- **Baseball.** `statsapi.mlb.com` schedule for the date returns `totalGames: 0`; no row published.
- **Build checks.** `python -m unittest discover -s tests` (28 tests) and `python scripts/build.py`. Tests cover the model invariants, every validation rule, local link resolution, insecure-link rejection, and that every published fixture carries its official link.
- **Limits.** Ratings rest on a 7-11 game NHL sample; NBA has none. Prices are no-vig fair odds, not market prices, and no rated value has been back-tested.

### Irregularities logged this session

- NHL's own properties disagree on games played and records for some clubs; the standings table (timestamped, internally consistent with the published rates) is used. Detail in `data/flagged.json` (`flag-nhl-gp`).
- OLBG's default tips page surfaces only one eligible-sport event, so OLBG cannot be used as the slate inventory.
- OLBG times for the two Oct 21 NHL games remain 19:37 against the league's 7:30 PM EDT.

## Integration and publication

- v1 PR: https://github.com/buffedlizard55-lab/OLBG2/pull/1 (merged).
- v2 branch: `arena/4a778bb7-olbg2`. v2 PR and merge result recorded here when complete.
- GitHub Pages publishes the `main` branch root in legacy mode; the root `index.html` redirects to `site/index.html`. CI validates the source data, the tests and the generated HTML.
