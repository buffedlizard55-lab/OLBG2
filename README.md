# OLBG research desk

A small evidence-first, static GitHub Pages research dashboard. **This is not a complete or live OLBG feed, and it contains no originated odds or picks.** Two ice hockey fixtures were cross-checked against official NHL gamecenters at the snapshot timestamp. Other eligible sports, market availability, current form, and independent line estimates remain unverified. No high-confidence narratives have been published.

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
- Market labels are research categories, **not claims that odds were observed or priced**. No market is independently originated without a documented statistical method, inputs, timestamp, and reproducible calculation.
- The source links confirm the visible matchup and league time only. Predictions and confidence are blank until genuinely supported. High-confidence text requires at least 30 words and a documented official source for each factual claim.
- Exclusions include soccer, boxing, UFC/MMA, football (including Gaelic and American football), hurling, horse racing, cycling and specials. Unknown categories are not assumed to be covered.
- Source pages can change. Recheck against the official league before using any snapshot and never treat a 2026-10-21 capture as a live fixture feed.

See [COORDINATION.md](COORDINATION.md) for source checks, limitations and integration status.
