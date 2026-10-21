"""Independent line-origination model (olbg-desk-poisson-v1).

Every published number is derived from this module, from the official inputs stored in
data/events.json. Nothing here reads the network or a bookmaker feed: the model is ours
and the parameters are declared in data/events.json -> "model".

Method
------
1. Each team carries an official goals-for per game (GF/GP) and goals-against per game
   (GA/GP) from the NHL game-centre payload (api-web.nhle.com).
2. Expected goals blend each attack with the opposing defence:
       lambda_home = ((home.GF/GP + away.GA/GP) / 2) * home_multiplier
       lambda_away = ((away.GF/GP + home.GA/GP) / 2) * away_multiplier
3. The 60-minute score matrix is the product of two independent Poisson distributions.
4. Markets are read off that matrix:
       money line (two-way, OT/SO included) = P(home win) + tie_split * P(tie)
       puck line  -1.5 / +1.5            = P(margin >= 2)
       totals     5.5 and 6.5            = P(total >= line + 0.5)
5. Prices are no-margin fair odds, 1 / probability. No bookmaker margin is added or
   removed, and no bookmaker price is used as an input.

Limits are documented in the methodology page and repeated in the site footer.
"""
from __future__ import annotations

import math
from typing import Any

MAX_GOALS = 10


def poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def score_matrix(lh: float, la: float, max_goals: int = MAX_GOALS) -> list[list[float]]:
    ph = [poisson(i, lh) for i in range(max_goals + 1)]
    pa = [poisson(j, la) for j in range(max_goals + 1)]
    return [[ph[i] * pa[j] for j in range(max_goals + 1)] for i in range(max_goals + 1)]


def fair(prob: float) -> float:
    """Fair decimal odds for a probability, rounded to 2dp."""
    if prob <= 0:
        return float("inf")
    return round(1.0 / prob, 2)


def _pct(p: float) -> float:
    return round(100.0 * p, 1)


def markets(home: dict[str, Any], away: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    lh = (home["gf_pg"] + away["ga_pg"]) / 2.0 * params["home_multiplier"]
    la = (away["gf_pg"] + home["ga_pg"]) / 2.0 * params["away_multiplier"]
    m = score_matrix(lh, la, params.get("max_goals", MAX_GOALS))

    p_home = p_away = p_tie = 0.0
    p_home_by2 = p_away_by2 = 0.0
    total_dist: dict[int, float] = {}
    best = (0.0, 0, 0)  # probability, home goals, away goals

    for i, row in enumerate(m):
        for j, p in enumerate(row):
            total_dist[i + j] = total_dist.get(i + j, 0.0) + p
            if p > best[0]:
                best = (p, i, j)
            if i > j:
                p_home += p
                if i - j >= 2:
                    p_home_by2 += p
            elif i < j:
                p_away += p
                if j - i >= 2:
                    p_away_by2 += p
            else:
                p_tie += p

    split = params.get("tie_split_home", 0.5)
    ml_home = p_home + split * p_tie
    ml_away = p_away + (1.0 - split) * p_tie

    totals = {}
    for line in (5.5, 6.5):
        over = sum(p for t, p in total_dist.items() if t > line)
        totals[str(line)] = {
            "over": _pct(over),
            "under": _pct(1.0 - over),
            "over_odds": fair(over),
            "under_odds": fair(1.0 - over),
        }

    return {
        "lambda_home": round(lh, 2),
        "lambda_away": round(la, 2),
        "expected_total": round(lh + la, 2),
        "money_line": {
            "home": _pct(ml_home),
            "away": _pct(ml_away),
            "home_odds": fair(ml_home),
            "away_odds": fair(ml_away),
        },
        "puck_line": {
            "home_minus_1_5": _pct(p_home_by2),
            "away_plus_1_5": _pct(1.0 - p_home_by2),
            "home_minus_1_5_odds": fair(p_home_by2),
            "away_plus_1_5_odds": fair(1.0 - p_home_by2),
        },
        "regulation_three_way": {
            "home": _pct(p_home),
            "tie": _pct(p_tie),
            "away": _pct(p_away),
        },
        "totals": totals,
        "most_likely_score": f"{best[1]}-{best[2]}",
    }


def confidence(p_side: float, params: dict[str, Any]) -> str:
    """Confidence in the model's own selection, from the declared thresholds."""
    edge = abs(p_side / 100.0 - 0.5)
    if edge >= params["edge_high"]:
        return "high"
    if edge >= params["edge_medium"]:
        return "medium"
    return "low"


def evaluate(event: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    mk = markets(event["home"], event["away"], params)
    home_p = mk["money_line"]["home"]
    away_p = mk["money_line"]["away"]
    if home_p >= away_p:
        side, side_p, side_odds = "home", home_p, mk["money_line"]["home_odds"]
    else:
        side, side_p, side_odds = "away", away_p, mk["money_line"]["away_odds"]
    mk["selection"] = event[side]["name"]
    mk["selection_side"] = side
    mk["selection_prob"] = side_p
    mk["selection_odds"] = side_odds
    mk["confidence"] = confidence(side_p, params)
    return mk
