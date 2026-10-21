# OLBG research desk

A small evidence-first, static GitHub Pages research dashboard. **This is not a complete or live OLBG feed, and it contains no originated odds or picks.** Two NHL fixtures for 2026-10-21 were cross-checked against official NHL gamecenters at 05:20Z (Flyers @ Sabres, Panthers @ Senators). All other eligible sports were inventoried from OLBG indexes but remain unverified against official schedules. No high-confidence narratives have been published.

Snapshot: `2026-10-21T05:20:00Z` · Verified fixtures: 02 · Open checks: 08

## Local build

Python 3.10+; no third-party dependencies.

```sh
python -m unittest discover -s tests -v
python scripts/build.py
python -m http.server 8000 -d site
```

`data/events.json` contains evidence links and explicit nulls for unknowns. `scripts/build.py` validates and escapes all displayed fields. `site/` contains the generated static pages, committed to make the evidence snapshot readable without running a server. GitHub Actions validates the generated site on PRs and pushes to `main`. The repository’s existing GitHub Pages configuration publishes the `main` branch root; the root `index.html` redirects to `site/index.html`. GitHub Pages settings cannot be changed with this session’s integration permissions, so no Actions deployment is attempted.

## Evidence rules

- Each published fixture requires an official league gamecenter URL and an OLBG reference; OLBG is not treated as an official match source.
- Market labels (Money line, Puck line / handicap, Game total / Over-Under) are research categories **not claims that odds were observed or priced**. No market is independently originated without a documented statistical method, inputs, timestamp, and reproducible calculation (see `site/methodology.html`).
- The source links confirm the visible matchup and league time only. Predictions and confidence are blank until genuinely supported. High-confidence text requires at least 30 words and a documented official source for each factual claim (teams, players, form, recent history, explicit selection).
- Exclusions include soccer, boxing, UFC/MMA, football (including Gaelic and American football), hurling, horse racing, cycling and specials. Unknown categories are not assumed to be covered.
- Source pages can change. Recheck against the official league before using any snapshot and never treat a 2026-10-21 capture as a live fixture feed.

## What was verified 05:20Z

- **NHL schedule Oct 21** — [NHL schedule 2026-10-21](https://www.nhl.com/schedule/2026-10-21) still 2 games: PHI@BUF and FLA@OTT at 7:30 PM EDT. Gamecenters: [PHI at BUF 2026020152](https://www.nhl.com/gamecenter/phi-vs-buf/2026/10/21/2026020152) (PHI 2-6-3, BUF 4-3-2, Zegras 7pts, Michkov 6G, Woll .917) and [FLA at OTT 2026020153](https://www.nhl.com/gamecenter/fla-vs-ott/2026/10/21/2026020153) (FLA 5-2-2, OTT 6-3-0, M.Tkachuk 14pts, Ullmark 6-1-0 1.33).
- **OLBG ice hockey index** — [OLBG Ice Hockey](https://www.olbg.com/betting-tips/Ice_Hockey/13) lists both NHL games at 00:37 (no timezone) with Over 5.50, plus Austria EHL and SHL entries — only NHL pair verified.
- **Basketball** — [OLBG Basketball](https://www.olbg.com/betting-tips/Basketball/4) lists 6 NBA games (MIL@WAS 19:10 etc.) plus Euroleague/EuroCup/KBL; official [NBA games](https://www.nba.com/games) shows 11 games Oct 21 but errors on expand, so not verified.
- **Tennis** — [OLBG Tennis](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Aliaksandra_Sasnovich/3?event_id=902039) ~15 matches with Win Match/Set Betting; no ATP/WTA cross-check.
- **Baseball** — [MLB schedule 2026-10-21](https://www.mlb.com/schedule/2026-10-21) shows no games.

See [COORDINATION.md](COORDINATION.md) for source checks, limitations and integration status. Category pages: Ice hockey (verified), Basketball/Tennis/Baseball (inventoried but unverified), Methodology, Flagged for review.
