# OLBG Match Research Dashboard

A GitHub Pages-ready, evidence-first dashboard scaffold for organizing match schedules, independently originated lines, market coverage, and confidence-rated picks.

## Current data status

There are **no match records, originated lines, picks, or official-source verifications** in this repository yet. The initial repository contained no data or application. This dashboard intentionally shows empty states instead of inventing fixtures, odds, form, or predictions. The user's exclusion list is recorded as a request, not represented as independently verified source data.

A live and complete fixture/market catalogue cannot be responsibly claimed without accessing OLBG and each relevant sport's governing-body/competition sources. The current environment/repository supplied no feed, credentials, source extracts, or official source documents. Do not label any event or pick verified until the cited official source has been checked directly and the verification date recorded.

## Run locally

This is a dependency-free static site. Open `index.html` in a browser, or run a static server from the repository root, for example:

```sh
python3 -m http.server 8000
```

## Data and verification contract

- Every future event, match fact, market line, form statistic, and prediction must have a source URL to the relevant official governing body, league, competition, or team/player source.
- Store facts only when directly confirmed. Leave unknown values blank and add the issue to **Flagged for Review**; never infer odds, results, form, or event status.
- Keep a `checkedAt` date and a source URL for each fact. The source must support the exact value, not merely the sport generally.
- Independently originated lines must be labeled as estimates, have a recorded method and timestamp, and must not be presented as official bookmaker odds.
- Picks require an explicit selection, low/medium/high confidence, a rationale, and supporting sources. High-confidence prose must be unique, at least 30 words, and grounded in verified current form and recent match history.
- The user-requested exclusions are: soccer, boxing, UFC, MMA, football, American football, hurling, horse racing, cycling, and specials. Their scope and interpretation have not been independently validated.

## Pages

- **Dashboard** — current record and verification counts.
- **Categories** — sports categories with confirmed records (currently none).
- **Markets** — market coverage with confirmed records (currently none).
- **Flagged for Review** — data and source gaps that need attention.
- **Methodology** — source, line, and confidence rules.

GitHub Pages is already configured for this repository to publish from the `main` branch root (GitHub reports the existing site as built). Merging these static files to `main` will update that existing Pages site; no duplicate Actions deployment workflow is added.
