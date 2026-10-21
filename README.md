# OLBG Research Desk

A static, evidence-first research dashboard for organizing independently verified sports fixtures, markets, originated lines, and picks. The current site intentionally contains **no match rows, odds, line values, form claims, confidence ratings, or predictions**: none have been verified to the required standard yet.

## Browse locally

Open `index.html` directly, or run a local static server from the repository root, for example:

```sh
python -m http.server 8000
```

Then visit `http://localhost:8000`. The site has overview, sport category, market/line, methodology, and flagged-for-review pages. It is dependency-free and designed for GitHub Pages.

## Evidence policy

- Use official competition, governing-body, event, team, club, or athlete sources for event facts and recent results.
- Every future event row needs direct official-source links. Leave unsupported fields blank and flag them; never infer that an empty category means no events.
- OLBG links in the current snapshot document only observed public-page/category/market terminology. They do not verify event schedules, athlete form, original lines, or recommendations.
- Do not publish an independently originated line without a documented reproducible method and input provenance. Confidence and high-confidence prediction copy require verified facts and a defined calibration method.
- Exclude soccer, boxing, UFC, MMA, football, American football, hurling, horse racing, cycling, and specials. Ambiguities remain on the Flagged for Review page.

## Project status

The initial repository contained only this README. Five category examples (darts, snooker, handball, basketball, Gaelic football) were observed on OLBG's public tips page, but OLBG describes its directory as 20+ sports; the complete scope taxonomy and live event slate remain unverified. See [Flagged for Review](flagged.html), [Methodology](methodology.html), and [COORDINATION.md](COORDINATION.md) for gaps and work log.

## Sources

- [OLBG public betting tips listing](https://www.olbg.com/betting-tips) — first-party reference for OLBG's public category/market presentation only; not an official sporting-event source.
