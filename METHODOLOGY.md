# METHODOLOGY.md

How a line is originated, how a pick is made, how confidence is labelled, and which parts are
verified facts versus disclosed modelling assumptions. The executable form of this document is
`scripts/originate_lines.py` and `scripts/analyse.py`; the published form is
<https://buffedlizard55-lab.github.io/OLBG2/methodology.html>.

## 1. Inventory

OLBG's sport taxonomy is taken from its own sitemap,
<https://www.olbg.com/sitemap-betting-tips.xml>, which lists 22 sports with numeric ids. For
each in-scope sport the `https://www.olbg.com/betting-tips/<Sport>/<id>` page is read and every
fixture recorded with:

- match or event name, competition, displayed time
- market name and OLBG's top community selection with its tip counts and percentage
- the event id, which yields a row-level OLBG URL
- `retrieved_via` — `live_fetch` (read from OLBG during collection on 2026-10-21) or
  `indexed_snapshot` (read from a dated search-index copy of the page)
- `as_of` — the date the underlying page content is dated

Live-fetched rows and snapshot rows are never merged, and the split is published (F-16).

OLBG displays times in **US Eastern**. This was established, not assumed: OLBG shows `07:30`
for Afghanistan v Bangladesh while the official start is `11:30 GMT` (F-06).

## 2. Evidence tiers

| Tier | Input | Requirement |
| --- | --- | --- |
| `tier1` | Governing-body rating — ICC team ratings, OWGR average points, PDC Order of Merit, WST rankings, ATP/WTA rankings | verified for **both** competitors |
| `tier2` | Official league table position, points and points difference | verified for **both** clubs |
| `tier3` | Published competition-level base rates with a stated sample size | verified for the competition |
| `none` | Nothing verifiable | **no line is published**; the row is flagged |

A tier is assigned only when the input is verified from the body that publishes it, or from a
mirror of that body's own table with the mirror named. OLBG pages are never labelled as
governing-body sources; source links on the site are tier-coloured so the distinction is
visible in every table.

## 3. Probability and price

A logistic function of the rating gap:

```
p = 1 / (1 + exp(-Δ / S))          Δ = rating(first side) - rating(second side)
fair decimal price = 1 / p          (no vig; this is our line, not a bookmaker's)
```

Half-point lines use `floor(x) + 0.5`, the convention that avoids a push. For a three-way
market the draw probability is held at the published competition base rate and the remaining
mass is split between the two sides by the logistic.

### Model constants — disclosed assumptions, not sourced facts

| Constant | Value | Note |
| --- | --- | --- |
| `cricket_odi_scale` | 25.0 | ICC ODI ratings span roughly 12–115 |
| `cricket_t20i_scale` | 50.0 | ICC T20I ratings span roughly 179–269, so the format needs its own scale |
| `cricket_home_advantage` | 0.0 | No official coefficient was verifiable, so the term is zero rather than guessed (F-19) |
| `rugby_points_per_logit` | 6.0 | League-points gap scale for Top 14 |
| `DIVERGENCE_CAP` | 15.0 pp | Official-divergence guard, see §5 |

Every constant is an assumption we own. Each line publishes a **sensitivity block** showing how
the pick probability moves if the scale constant is 20% tighter or looser, so a reviewer can see
how much of a result is driven by the assumption rather than the verified input.

## 4. What we deliberately do not use

- **Bookmaker prices.** OLBG renders them client-side and the served HTML has an empty `WIN @`
  placeholder, so no prices were capturable (F-02). De-vigging was therefore impossible. This is
  a better outcome for the brief anyway: a de-vigged book price is the market's line, not ours.
- **OLBG community tip percentages.** Using the crowd's split as a probability input would echo
  the market rather than originate a line. Tip counts are published as separate, clearly
  labelled community data and enter no calculation.
- **Any inferred value.** If a cell cannot be sourced it is blank and flagged.

## 5. Confidence rule

Deterministic, in this order:

1. **Official-divergence guard.** If a governing body publishes its own probability for the same
   fixture and it differs from ours by more than `DIVERGENCE_CAP` (15 pp), confidence is capped
   at **low** and the disagreement is flagged. We never silently override an official figure.
2. **high** — `p ≥ 0.70` on tier1/tier2 inputs *and* verified form for both competitors; **or**
   `p ≥ 0.55` on tier1 inputs corroborated by a verified same-series head-to-head win for the
   picked side within the last 14 days.
3. **medium** — `p ≥ 0.60` on tier1/tier2 inputs; or `p ≥ 0.70` on tier3 base rates.
4. **low** — any other published line.
5. **unverified** — no line could be originated.

The corroborated head-to-head path exists because a verified result between the same two sides
in the same series, in the same conditions, days earlier is stronger evidence than a rating gap
alone. It fired once: Afghanistan beat Bangladesh by 200 runs on 17 October 2026 in the same
tri-series (verified against ESPNcricinfo and cricinfo).

The divergence guard also fired once: our model gave Bordeaux 73.0% at La Rochelle, while LNR
publishes 53.18%. The pick stays on the site at our probability but is labelled **low** and
flagged (F-14) rather than presented as high confidence.

## 6. Predictions

Written only for high-confidence picks. Each must:

- be at least 30 words — asserted at build time by `scripts/verify.py`
- name the selection unambiguously (who wins, or over/under)
- include the team or player, current form and recent match history
- use only facts recorded in `data/lines.json`, each published under the prediction with its
  source link

No player, injury, score or date appears in a prediction unless it was verified during
collection. Where press-tier evidence is used instead of an official team sheet, that is stated
(F-20). Medium and low confidence picks carry no prediction, because for those we do not hold
enough verified player-level detail to write one without inventing it.

## 7. Build and gate

```bash
python3 scripts/load_inventory.py    # -> data/sports.json, data/events/*.json
python3 scripts/originate_lines.py   # -> data/lines.json
python3 scripts/analyse.py           # -> data/picks.json, data/predictions.json, data/flags.json
python3 scripts/build_site.py        # -> docs/
python3 scripts/verify.py            # gate; non-zero exit on any failure
```

`verify.py` checks: every internal link resolves; every data-table row carries a source link or
an explicit UNVERIFIED badge; every inventory row carries provenance, time, as-of and retrieval
method; every originated line cites a rating or basis source; every null line cell is explicitly
marked unverified rather than silently blank; every prediction is ≥30 words and every fact has a
URL; a prediction exists for every high-confidence pick and no other; the inventory reconciles
exactly as `modelled + flagged`; flag ids are unique; and rebuilding from the same data is
byte-identical.
