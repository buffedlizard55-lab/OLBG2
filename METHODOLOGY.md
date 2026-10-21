# Methodology (repository version)

The published version of this document, with worked examples, is the site page
[methodology.html](methodology.html). This file is the same content in Markdown for reviewers reading the repo.

## 1. Verification chain

1. **Discovery** — the event list, event_id and market label come from OLBG's sport hub pages
   (`/betting-tips/{Sport}/{id}`). OLBG publishes no prices.
2. **Confirmation** — the fixture is checked against the official league or governing body (NBA.com, the NHL
   score API, the URC match centre, the ICC match list, the WST draw). If it cannot be confirmed, it is not
   published; the OLBG event goes to the flagged page instead.
3. **Inputs** — performance data is taken from the same official family of sources (NBA standings, NHL team
   summary, URC league table). Nothing else is used.
4. **Line origination** — see below. No bookmaker price is read, scraped or compared.
5. **Publication** — each row carries its fixture source, data source, model parameters and confidence.

## 2. Models

### NHL — multiplicative Poisson

```
w           = gp / (gp + 8)                       # empirical-Bayes shrinkage
attack_i    = 1 + w * ((gf_i/gp_i)/league_avg - 1)
defence_i   = 1 + w * ((ga_i/gp_i)/league_avg - 1)
lambda_home = league_avg * attack_home * defence_away * 1.05
lambda_away = league_avg * attack_away * defence_home / 1.05
P(home)     = Poisson grid, tie split 50/50 for OT/SO
puck line   = 1.5, P(home covers) = P(home margin >= 2)
total line  = nearest half point to lambda_home + lambda_away
```

`league_avg` is the mean goals-for per game across all 32 teams in the same snapshot.

**Goal convention.** Inputs come from `api.nhle.com/stats/rest/en/team/summary`, which excludes the
shootout-deciding goal from GF/GA. `nhl.com/standings` includes it, so the two differ for teams that have been
through a shootout (e.g. Ottawa 22 vs 24 GF, Buffalo 33 vs 34 GA). The model stays on the stats-API view and the
difference is disclosed as flag F19 rather than silently reconciled.

### NBA — prior-season logit model

```
shrunk  = 0.75 * (W/(W+L)) + 0.25 * 0.5        # 2025-26 season
rating  = logit(shrunk)
margin  = 11.0 * (rating_home + 0.20 - rating_away)
P(home) = logistic(margin / 11.0)
```

Current-season records are ignored because every team playing on 2026-10-21 was 0-0 before tip-off.
Game totals are **not** originated: no verified points-for/against input was captured.

### URC — league-table attack/defence

```
w = pl / (pl + 6)
attack_i  = 1 + w * ((pf_i/pl_i)/league_pf - 1)
defence_i = 1 + w * ((pa_i/pl_i)/league_pa - 1)
expected_home = league_pf * attack_home * defence_away + 3.0/2
expected_away = league_pa * attack_away * defence_home - 3.0/2
P(home) = logistic(expected_margin / 13.0)
```

### Prices

`price = round(1 / (p * 1.04), 2)`, clamped to 1.05–12.00. This is a fair price plus a 4% theoretical margin.
It is **not** a market price.

## 3. Confidence

| Sport | High | Medium | Low |
|---|---|---|---|
| NHL | p ≥ 65% and both teams ≥ 7 games | p ≥ 57% (≥ 7 games) or p ≥ 68% (≥ 5 games) | otherwise |
| NBA | not permitted (zero current-season games) | p ≥ 68% | p < 68% |
| URC | not permitted (three rounds) | p ≥ 62% | p < 62% |

## 4. Predictions

Only for high-confidence picks. Minimum 30 words (enforced by `scripts/build_site.py`), the selection stated in
the first sentence, the team's record and scoring rate, at least one named player with a verified statistic, and
the model probability. Every factual claim carries a source link on the Picks page. No injuries, line-ups,
transfers or travel claims are made, because none could be verified.

## 5. Known limitations

- Early-season samples (NHL 7–11 games, URC 3 rounds) are noisy; shrinkage is a guard, not a fix for roster change.
- NBA priors are a season old and do not account for trades or coaching changes.
- No market prices were available, so no value comparison against a bookmaker is possible.
- URC times are venue-local; no conversion was applied.
- Coverage is incomplete and every gap is listed on the flagged page.
- Team strength is assumed stationary within a season; no travel, back-to-back, injury or lineup adjustment is applied.
- The 4% margin is a theoretical overround, not an observed market price, so these are not "value" recommendations.
