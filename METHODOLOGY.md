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

The multi-sport `/verified/` layer (the unified dashboard's source dataset) prices **no-vig**: `fair_decimal =
round(1 / p, 2)` and the American figure is derived from that same rounded decimal, so the two prices printed on a
row always agree. Neither convention is a bookmaker quote.

## 3. Confidence

| Sport | High | Medium | Low |
|---|---|---|---|
| NHL | uniform window rule and both teams ≥ 7 games | p ≥ 57% (≥ 7 games) or p ≥ 68% (≥ 5 games) | otherwise |
| NBA | not permitted (zero current-season games) | p ≥ 68% | p < 68% |
| URC | not permitted (three rounds) | p ≥ 62% | p < 62% |
| Handball | uniform window rule and both clubs ≥ 4 group games | p ≥ 58% (≥ 4 games) | otherwise |


**Uniform high-confidence window (applied to the four earlier layers — root archive, `/site/`, `/survey/`, `/live/` — on 2026-10-22 by session `arena/c12bdcd7`).** The brief defines high-confidence
picks as greater-than-70% selections and asks generation to focus on matches priced between **−250 and +10000**.
Every layer therefore applies one shared clause on top of its own evidence/sample gates: **high** requires
model probability **≥ 72%**, **or ≥ 70% with the fair no-vig price (1/p) inside [−250, +10000]** — and never
below the 70% floor. Boundary arithmetic: −250 American = decimal 1.40 = 71.43% implied, so a two-way fair
price qualifies between 70.0% and 71.43% outright; alternate handicap/total lines are used to express stronger
opinions inside the window (as the `/verified/` featured set does). Written predictions accompany every
high-confidence pick and every featured write-up sits inside the window; chalk-favourite write-ups outside it
are retained but labelled "outside the focus band" on their pages rather than passed off as compliant.

Selections regraded below high by this rule keep their narratives verbatim in per-layer archive files
(`data/predictions_archived.json`, `data/desk/archived_picks.json`) with the regrade reason — nothing is
deleted. The earlier root rule (NHL high at p ≥ 65%) and the live-slate rule (high at p ≥ 62%) were superseded
because both could label sub-70% picks high, which the brief's definition forbids. This closed the odds-window
compliance task opened as PR #54 (session `1bb45081`); see `research/pr54-takeover-c12bdcd7.md`.

The `/verified/` and `/forward/` published desks apply the strict form of the same window (session
`arena/1352b77f-olbg2`, VF-35): **high** only when the model probability is ≥ 70% **and** the fair American price
sits inside −250..+10000 — ultra-short chalk is capped at **medium**, so every HIGH label carries a written
prediction (14 featured band + 16 research write-ups) and the picks page never presents unbackable −5000
favourites as high-confidence tips. Unifying the four earlier layers onto this strict form is the one open
cross-layer item (recorded in COORDINATION.md for the legacy-layer owner). **medium** ≥ 60%; **low**
below 60%. NBA picks are capped at medium because only prior-season records exist. Handicap and total picks are
graded by the same rule; alternate lines only become featured when the moneyline pick already clears 70%.

## 4. Predictions

Only for high-confidence picks. Minimum 30 words (enforced by `scripts/build_site.py`), the selection stated in
the first sentence, the team's record and scoring rate, at least one dated recent result, and the model
probability. Every factual claim carries a source link on the Picks page. No injuries, line-ups, transfers or
travel claims are made, because none could be verified.

**Player-level detail.** The brief asks each prediction to name a player. The 14 root/featured write-ups do
**not** assert an individual player statistic (no official player feed had been captured when they were
written — **VF-24**). On 2026-10-22 session 26963a2d captured the NHL official score feed's per-team leaders
(goals, assists, goalie wins), the standings endpoint's home/road/last-10 splits, the PDC Order of Merit and the
WST match-centre season statistics, and published **16 research-desk selections** on `/verified/predictions.html#research`
that name players with those official figures (e.g. Kaprizov 11 G, Sorokin 5 W, Wilson 63% season win rate),
each fact carrying its endpoint URL and fetch time. Those write-ups are graded by a stated research rule
(HIGH only when every official indicator agrees), sit inside the −250…+10000 band, include one plus-money
underdog, and are re-validated against the live desk row on every build so prose and table prices cannot drift.
Sports without a server-rendered official player feed (rugby, darts form) still cite only team/ranking facts.

## 5. Known limitations

- Early-season samples (NHL 7–11 games, URC 3 rounds) are noisy; shrinkage is a guard, not a fix for roster change.
- NBA priors are a season old and do not account for trades or coaching changes.
- No market prices were available, so no value comparison against a bookmaker is possible.
- URC times are venue-local; no conversion was applied.
- Coverage is incomplete and every gap is listed on the flagged page.
- Team strength is assumed stationary within a season; no travel, back-to-back, injury or lineup adjustment is applied.
- The 4% margin is a theoretical overround, not an observed market price, so these are not "value" recommendations.
