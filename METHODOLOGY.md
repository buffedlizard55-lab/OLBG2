# Methodology (repository version)

The published version of this document, with worked examples, is the site page
[methodology.html](methodology.html). This file is the same content in Markdown for reviewers reading the repo.

## 1. Verification chain

1. **Discovery** — the event list, event_id and market label come from OLBG's sport hub pages
   (`/betting-tips/{Sport}/{id}`). OLBG publishes no prices.
2. **Confirmation** — the fixture is checked against the official league or governing body (NBA.com, the NHL
   score API, the URC match centre, the ICC match list, the WST draw, the EHF Champions League match centre). If it cannot be confirmed, it is not
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

**Goal convention.** The captured inputs in `data/desk/nhl_teams.json` carry `source_id: nhl-standings` and were
read from `nhl.com/standings`, whose GF/GA **includes** the shootout-deciding goal. The stats API
(`api.nhle.com/stats/rest/en/team/summary`) excludes it, so the two views differ for clubs that have been through a
shootout (e.g. Ottawa 24 vs 22 GF, Buffalo 34 vs 33 GA, Seattle 39 vs 37 GF). Rates therefore sit up to ~0.2 goals per
game **above** the stats-API view, and the difference is disclosed as flag F19 rather than silently reconciled.

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

### Handball — group-phase attack/defence Poisson

```
league_gf   = sum(gf) / sum(gp) over all 24 clubs   # goals per team per game, both directions
w           = gp / (gp + 3)                         # four rounds played -> heavy shrinkage
attack_i    = 1 + w * ((gf_i/gp_i)/league_gf - 1)
defence_i   = 1 + w * ((ga_i/gp_i)/league_ga - 1)
exp_home    = league_gf * attack_home * defence_away + 0.4
exp_away    = league_gf * attack_away * defence_home - 0.4
P(result)   = sum of Poisson(i; exp_home) * Poisson(j; exp_away) over matching scores
```

The 0.4-goal split is our own home-court assumption (`handball_home_goals = 0.8`), not a sourced value. Match
winner is three-way; handicap uses a half-goal line just beyond the expected margin; match total uses a half-goal
line just below the expected total. The score grid is sized from the rates and renormalised, because a fixed
small grid truncates around 10% of the mass at handball scoring rates and shifts every probability.

Source: EHF Champions League Men official group standings and matches page (S33, S34), captured 2026-10-21
07:15 UTC. Verification record: `research/handball-ehf-73620ec4.md`.

### Prices

`price = round(1 / (p * 1.04), 2)`, clamped to 1.05–12.00. This is a fair price plus a 4% theoretical margin.
It is **not** a market price.

## 3. Confidence

### 3.1 Uniform odds-window gate (since 2026-10-22)

Across **every published layer** (root dashboard, desk `/site/`, survey `/survey/`, live `/live/`, verified
`/verified/`), a selection is labelled **high only when both conditions hold**:

1. model win probability `p ≥ 0.70`; and
2. its fair, no-vig American price lies inside **[-250, +10000]**, where the fair decimal is `1/p` and
   `American = round(-100 / (decimal − 1))` for prices below 2.00.

Boundary: **-250 American = decimal 1.40 = 71.43% implied**, so the effective high band is 70.0%–71.43%.
The gate is evaluated on fair no-vig prices so it is a deterministic function of the model probability and is
applied identically in all five layers; displayed market rows keep their documented model overround separately.
Selections failing the gate keep their probability and price but are capped at medium/low. Full remediation
record: `research/odds-window-audit-1bb45081.md`.

### 3.2 Layer-specific evidence gates (conjunctions with 3.1)

| Layer / sport | Additional high requirements | Medium | Low |
|---|---|---|---|
| Root NHL | both teams ≥ 7 games and the 3.1 window | p ≥ 57% (≥ 7 games) or p ≥ 68% (≥ 5 games) | otherwise |
| Root NBA | not permitted (zero current-season games) | p ≥ 68% | p < 68% |
| Root URC | not permitted (three rounds) | p ≥ 62% | p < 62% |
| Root Handball | both clubs ≥ 4 group games and the 3.1 window | p ≥ 58% (≥ 4 games) | otherwise |
| Desk `/site/` NHL/NBA | ≥ 13 pts model edge, evidence pack, min. games sample **and** the 3.1 window | ≥ 6 pts edge or capped edge-highs | otherwise |
| Survey `/survey/` | tier 1/2, form verified, old 72% bar **and** the 3.1 window | p ≥ 60% | otherwise |
| Live `/live/` | p ≥ 70% inside the 3.1 window | p ≥ 55% or out-of-window chalk | p < 55% |
| Verified `/verified/` | p ≥ 70% inside the 3.1 window | layer rules | layer rules |

## 4. Predictions

Only for high-confidence, window-compliant picks. Minimum 30 words (enforced by the build scripts), the
selection stated in the first sentence, the team's record and scoring rate, at least one named player with a
verified statistic, and the model probability. Every factual claim carries a source link on the picks page. No
injuries, line-ups, transfers or travel claims are made, because none could be verified.

Narratives displaced by the 2026-10-22 window rule are **archived, never deleted**, each with its original text,
facts, sources, fair decimal/American price, regraded label and reason:
`data/predictions_archived.json` (root), `data/desk/archived_picks.json`,
`data/survey/archived_predictions.json`, `data/live/archived_predictions.json`, and
`data/verified/archived_predictions.json`. Every layer renders an archive table or section and, where no
selection qualifies, an explicit empty-state notice instead of an invented pick.

## 5. Known limitations

- Early-season samples (NHL 7–11 games, URC 3 rounds) are noisy; shrinkage is a guard, not a fix for roster change.
- NBA priors are a season old and do not account for trades or coaching changes.
- No market prices were available, so no value comparison against a bookmaker is possible.
- URC times are venue-local; no conversion was applied.
- Coverage is incomplete and every gap is listed on the flagged page.
- Team strength is assumed stationary within a season; no travel, back-to-back, injury or lineup adjustment is applied.
- The 4% margin is a theoretical overround, not an observed market price, so these are not "value" recommendations.
