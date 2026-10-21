# OLBG2

Reverse-engineering of [OLBG.com](https://www.olbg.com/): a full inventory of upcoming
fixtures across every sport OLBG covers **except** the ten the brief excludes, with our own
originated betting lines, a winner pick and a confidence label per match, written predictions
for the high-confidence picks, and a GitHub Pages dashboard publishing all of it.

**Live site:** <https://buffedlizard55-lab.github.io/OLBG2/>

## Headline numbers (retrieved 2026-10-21)

| Metric | Value |
| --- | --- |
| OLBG sports in its taxonomy | 22 |
| In scope | 15 |
| Excluded by the brief | 7 |
| Events inventoried | 130 |
| Lines originated | 11 |
| Picks: high / medium / low | 2 / 1 / 8 |
| Written predictions (≥30 words) | 2 |
| Flags raised | 21 |
| Event rows with no originated line | 119 (each itemised with a reason) |

## The one rule that shaped everything

> Every table row must have a source link to an official site. If a value can't be confirmed
> from an official source, leave it blank and flag it as unverified. Never infer or fill in values.

119 of 130 events therefore carry **no** line. That is the rule working as intended, not a
failure: for those events no governing-body rating, official league table or published base
rate could be verified for both competitors during collection. Each one is itemised under
[F-15](https://buffedlizard55-lab.github.io/OLBG2/flagged.html#F-15) with the exact official
source that would be needed to originate a line.

## Layout

```
COORDINATION.md          shared multi-session task board
REPO_REVIEW.md           baseline audit of the repo as found
METHODOLOGY.md           how lines are originated, confidence rule, disclosed assumptions
data/
  sports.json            OLBG's 22-sport taxonomy with include/exclude decisions
  events/<sport>.json    fixture inventory, one file per in-scope sport
  lines.json             originated lines + every verified input used
  picks.json             winner pick + confidence per originated line
  predictions.json       written predictions for high-confidence picks
  flags.json             irregularities, source conflicts, unverified rows
scripts/
  load_inventory.py      materialises the collected OLBG inventory into data/events/
  originate_lines.py     verified inputs + model -> data/lines.json
  analyse.py             picks, confidence, predictions, flags
  build_site.py          data/*.json -> site at repo root (stdlib, deterministic)
  verify.py              gates the build: links, per-row sources, data integrity
index.html, sports.html,   the published GitHub Pages site, built at the
  lines.html, picks.html,    repository root because Pages on this repo is pinned
  predictions.html,          to "/" of main and the token cannot repoint it
  methodology.html,
  verification.html,
  flagged.html,
  excluded.html
  sports/<sport>.html        one subpage per in-scope sport
  assets/style.css, app.js
```

## Reproduce

```bash
python3 scripts/load_inventory.py    # data/sports.json + data/events/*.json
python3 scripts/originate_lines.py   # data/lines.json
python3 scripts/analyse.py           # data/picks.json, data/predictions.json, data/flags.json
python3 scripts/build_site.py        # site files at the repo root
python3 scripts/verify.py            # exits non-zero on any failed check
```

`verify.py` re-runs `build_site.py` and asserts the output is byte-identical, so the site is
reproducible from the data.

## Verification discipline

- **Tier 1** — governing-body rating for both competitors (ICC, OWGR, PDC, WST, ATP/WTA).
- **Tier 2** — official league table position for both clubs (LNR Top 14).
- **Tier 3** — published competition base rates with a stated sample size (OLBG's own database).
- **None** — no line published, row flagged.

Source links are tier-labelled on every page, so an OLBG page is never presented as an official
governing-body source. Where two official sources disagree, both values are published and the
conflict is flagged rather than silently resolved.

An **official-divergence guard** caps confidence at LOW when our line disagrees with a
governing body's own published probability by more than 15 percentage points. That guard fired
on La Rochelle v Bordeaux: our model said 73.0% Bordeaux, LNR publishes 53.18%. See
[F-14](https://buffedlizard55-lab.github.io/OLBG2/flagged.html#F-14).

## Notable findings about OLBG itself

- OLBG displays fixture times in **US Eastern**, not UK time — established by reconciling its
  `07:30` for Afghanistan v Bangladesh against the official `11:30 GMT` start ([F-06](https://buffedlizard55-lab.github.io/OLBG2/flagged.html#F-06)).
- Bookmaker prices are rendered client-side; the served HTML has an empty `WIN @`
  placeholder, so no decimal prices were capturable ([F-02](https://buffedlizard55-lab.github.io/OLBG2/flagged.html#F-02)).
- OLBG's own F1 calendar lists "Round 16, 4 October, Bahrain Grand Prix, Sepang International
  Circuit, Malaysia" — three different events in one row ([F-13](https://buffedlizard55-lab.github.io/OLBG2/flagged.html#F-13)).
- OLBG has no `UFC`, `MMA`, `Hurling` or `Specials` sport node, so four of the brief's ten
  exclusions are vacuous against OLBG's taxonomy ([F-05](https://buffedlizard55-lab.github.io/OLBG2/flagged.html#F-05)).

## Multi-session coordination

See [COORDINATION.md](COORDINATION.md). This repository was built by a single session
(`ca1d5677`) which claimed and completed T1–T11.

## Disclaimer

Research and data-engineering output. Not betting advice. Nothing here guarantees any result.
18+. If gambling is becoming a problem, free support is available from
[GamCare](https://www.gamcare.org.uk/) and [GambleAware](https://www.gambleaware.org/).
