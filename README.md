# OLBG research desk

An evidence-first reverse-engineering of OLBG's sports coverage, plus a small independent line-origination desk.

The site publishes only fixtures that an **official competition source** confirms — teams, date and start time — and then
prices three markets per fixture using a model whose inputs and parameters are committed alongside the data.
Where an official source could not confirm something, the row is absent and the reason is written on the
**Flagged for review** page. Nothing is filled in to make the table look complete.

## What is in this snapshot

- **14 verified NHL fixtures** across the official 2026-10-21 and 2026-10-22 schedule days.
- **3 markets per fixture**: money line (two-way, OT/SO included), puck line 1.5, match total (5.5 and 6.5).
- **14 selections** with low / medium / high confidence, 6 of them high with a 30+ word sourced narrative.
- **16 eligible OLBG categories** tracked on a coverage board. Soccer, boxing, UFC/MMA, football (including American and
  Gaelic), hurling, horse racing, cycling and specials are excluded by the brief and never enter the pipeline.

Every row carries three links: the official NHL game page, the machine-readable official feed it was read from, and the
OLBG reference. The full list is on the site's **Sources** page.

## Build

Python 3.10+, no third-party dependencies.

```sh
python -m unittest discover -s tests -v   # 23 checks
python scripts/build.py                   # regenerates site/
python scripts/report.py                  # prints the model output table
python -m http.server 8000 -d site        # local preview
```

`data/events.json` is the single source of truth: official inputs, model parameters, selections, narratives, coverage
board and flags. `scripts/model.py` turns those inputs into prices; `scripts/build.py` validates the snapshot and writes
`site/`. Derived prices are **not** stored, so they can never drift from their inputs.

The build fails if a row uses an unapproved source host, if a selection disagrees with the model, if a high-confidence
narrative is under 30 words or fails to name its selection, or if the coverage board's row counts disagree with the
fixture list. Tests additionally crawl every generated page for broken local links.

## Evidence rules

- A fixture is published only when the competition's own feed returns both teams, the date and the start time.
- OLBG is the coverage reference the brief asked for, never an official match source. OLBG's tipster picks are not our picks.
- No bookmaker price is scraped, copied or used as an input. Prices are fair odds, `1 / probability`, with no margin.
- Model parameters (home/away multipliers, tie split, confidence edges) are **assumptions of this desk**, labelled as such,
  and editable in `data/events.json`.
- Anything that could not be confirmed is blank, flagged, and listed with the source that would settle it.

## Repository layout

```
data/events.json      official inputs, model params, picks, coverage board, flags
scripts/model.py      Poisson line-origination model
scripts/build.py      validation + static site generator
scripts/report.py     model output table for review
tests/test_build.py   23 checks (schema, exclusions, model agreement, links)
site/                 generated dashboard, category pages, methodology, sources, flagged
```

## Limitations

This is a dated snapshot, not a live feed. The model ignores rest, injuries, goaltenders, travel and score effects, and it
does not compare itself to market prices, so it cannot claim value. It is a transparent estimate, not betting advice.
