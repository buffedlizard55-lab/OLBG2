#!/usr/bin/env python3
"""Pure-Python multi-market line origination models for the /clarity/ desk (2026-10-24).

All lines are originated from official governing-body statistics with zero bookmaker odds input.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def prob_to_decimal(p: float) -> float:
    p = clamp(p, 0.0005, 0.9995)
    return round(1.0 / p, 3)


def prob_to_american(p: float) -> int:
    p = clamp(p, 0.0005, 0.9995)
    if p >= 0.5:
        return -max(100, int(round(100.0 * p / (1.0 - p))))
    return max(100, int(round(100.0 * (1.0 - p) / p)))


def fmt_american(am: int) -> str:
    return f"+{am}" if am > 0 else str(am)


def in_target_odds_band(american_odds: int) -> bool:
    """True when selection sits inside [-250, +10000] inclusive (decimal 1.40..101.00)."""
    return -250 <= american_odds <= 10000


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def poisson_pmf(lam: float, k: int) -> float:
    if lam <= 0.0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def round_half(x: float) -> float:
    """Round to nearest .5 line so two-way handicaps/totals avoid pushes."""
    return math.floor(x) + 0.5


def assign_confidence(
    win_prob: float,
    american_odds: int,
    sample_strength: float = 1.0,
    injury_clarity: float = 1.0,
    outright: bool = False,
) -> str:
    """Assign low / medium / high confidence inside the [-250, +10000] focus band.

    Two-way markets: high needs a 60%+ chance at an actionable price. Multi-runner
    outright markets (golf, F1, greyhounds) are graded on their own scale because a
    field of 30+ entrants can never produce a 60% favourite.
    """
    quality = sample_strength * injury_clarity
    if not in_target_odds_band(american_odds):
        if win_prob > 0.7143 and not outright:
            return "medium" if quality >= 0.75 else "low"
        return "low"
    if outright:
        if win_prob >= 0.24 and quality >= 0.85:
            return "high"
        if win_prob >= 0.12 and quality >= 0.70:
            return "medium"
        return "low"
    if win_prob >= 0.60 and quality >= 0.85:
        return "high"
    if win_prob >= 0.535 and quality >= 0.70:
        return "medium"
    return "low"


def nhl_poisson_markets(
    home_gf: int,
    home_ga: int,
    home_gp: int,
    away_gf: int,
    away_ga: int,
    away_gp: int,
    league_avg_gpg: float = 3.16,
    home_ice_boost: float = 1.045,
    b2b_home_penalty: float = 1.0,
    b2b_away_penalty: float = 1.0,
) -> Dict[str, object]:
    """Empirical-Bayes shrunk multiplicative Poisson over a 0..16 goal grid."""
    wh = home_gp / (home_gp + 8.0)
    wa = away_gp / (away_gp + 8.0)
    att_h = 1.0 + wh * (((home_gf / max(1, home_gp)) / league_avg_gpg) - 1.0)
    def_h = 1.0 + wh * (((home_ga / max(1, home_gp)) / league_avg_gpg) - 1.0)
    att_a = 1.0 + wa * (((away_gf / max(1, away_gp)) / league_avg_gpg) - 1.0)
    def_a = 1.0 + wa * (((away_ga / max(1, away_gp)) / league_avg_gpg) - 1.0)

    lam_h = clamp(league_avg_gpg * att_h * def_a * home_ice_boost * b2b_home_penalty, 1.85, 4.75)
    lam_a = clamp((league_avg_gpg * att_a * def_h / home_ice_boost) * b2b_away_penalty, 1.75, 4.65)

    max_g = 16
    ph = [poisson_pmf(lam_h, g) for g in range(max_g + 1)]
    pa = [poisson_pmf(lam_a, g) for g in range(max_g + 1)]
    # Normalize tail
    sh, sa = sum(ph), sum(pa)
    ph = [x / sh for x in ph]
    pa = [x / sa for x in pa]

    p_reg_h = 0.0
    p_reg_a = 0.0
    p_tie = 0.0
    p_h_minus_1_5 = 0.0
    p_a_minus_1_5 = 0.0

    total_line = 6.5 if (lam_h + lam_a) >= 6.0 else 5.5
    p_over_reg = 0.0

    for gh in range(max_g + 1):
        for ga in range(max_g + 1):
            joint = ph[gh] * pa[ga]
            if gh > ga:
                p_reg_h += joint
            elif ga > gh:
                p_reg_a += joint
            else:
                p_tie += joint
            if gh - ga >= 2:
                p_h_minus_1_5 += joint
            if ga - gh >= 2:
                p_a_minus_1_5 += joint
            if gh + ga > total_line:
                p_over_reg += joint
            elif gh + ga == int(total_line - 0.5) and gh == ga:
                # Tied regulation at 3-3 (total_line 6.5) always goes over in OT/SO!
                p_over_reg += joint

    # OT/SO win share slightly tilted toward higher-scoring team (52/48 max)
    ot_share_h = clamp(0.5 + 0.06 * (lam_h - lam_a), 0.45, 0.55)
    p_home_ml = clamp(p_reg_h + p_tie * ot_share_h, 0.05, 0.95)
    p_away_ml = 1.0 - p_home_ml

    fav_is_home = p_home_ml >= 0.5
    if fav_is_home:
        puck_fav_prob = clamp(p_h_minus_1_5, 0.12, 0.78)
        puck_dog_prob = 1.0 - puck_fav_prob
        puck_label_fav = "Home -1.5"
        puck_label_dog = "Away +1.5"
    else:
        puck_fav_prob = clamp(p_a_minus_1_5, 0.12, 0.78)
        puck_dog_prob = 1.0 - puck_fav_prob
        puck_label_fav = "Away -1.5"
        puck_label_dog = "Home +1.5"

    p_over = clamp(p_over_reg, 0.18, 0.82)
    p_under = 1.0 - p_over

    return {
        "lambda_home": round(lam_h, 3),
        "lambda_away": round(lam_a, 3),
        "p_home": round(p_home_ml, 4),
        "p_away": round(p_away_ml, 4),
        "handicap_line": -1.5 if fav_is_home else 1.5,
        "p_home_cover": round(puck_fav_prob if fav_is_home else puck_dog_prob, 4),
        "p_away_cover": round(puck_dog_prob if fav_is_home else puck_fav_prob, 4),
        "total_line": total_line,
        "p_over": round(p_over, 4),
        "p_under": round(p_under, 4),
    }


def normal_margin_markets(
    exp_home_pts: float,
    exp_away_pts: float,
    sigma_margin: float,
    sigma_total: float,
) -> Dict[str, object]:
    """Two-way normal margin & total origination (Basketball, Rugby Union, Rugby League, Gaelic)."""
    mu_margin = exp_home_pts - exp_away_pts  # positive => home favoured
    mu_total = exp_home_pts + exp_away_pts

    p_home = clamp(1.0 - normal_cdf((0.0 - mu_margin) / sigma_margin), 0.02, 0.98)
    p_away = 1.0 - p_home

    # Spread from home perspective (negative means home gives points)
    if abs(mu_margin) < 0.5:
        spread_home = -0.5 if mu_margin >= 0 else 0.5
    elif mu_margin > 0:
        spread_home = -round_half(mu_margin)
    else:
        spread_home = round_half(abs(mu_margin))

    # Home covers if HomeMargin + spread_home > 0 => HomeMargin > -spread_home
    threshold = -spread_home
    p_home_cover = clamp(1.0 - normal_cdf((threshold - mu_margin) / sigma_margin), 0.15, 0.85)
    p_away_cover = 1.0 - p_home_cover

    total_line = round_half(mu_total)
    p_over = clamp(1.0 - normal_cdf((total_line - mu_total) / sigma_total), 0.18, 0.82)
    p_under = 1.0 - p_over

    return {
        "exp_home": round(exp_home_pts, 2),
        "exp_away": round(exp_away_pts, 2),
        "p_home": round(p_home, 4),
        "p_away": round(p_away, 4),
        "handicap_line": spread_home,
        "p_home_cover": round(p_home_cover, 4),
        "p_away_cover": round(p_away_cover, 4),
        "total_line": total_line,
        "p_over": round(p_over, 4),
        "p_under": round(p_under, 4),
    }


def race_to_target_markets(
    p_unit_home: float,
    target: int,
    handicap_units: float,
    total_line: float,
) -> Dict[str, object]:
    """Exact negative-binomial / DP race-to-`target` legs or frames (Darts, Snooker, Tennis, Volleyball)."""
    p = clamp(p_unit_home, 0.15, 0.85)
    q = 1.0 - p

    # DP over (h, a) states up to target
    dp = [[0.0] * (target + 1) for _ in range(target + 1)]
    dp[0][0] = 1.0
    terminal: List[Tuple[int, int, float]] = []

    for h in range(target):
        for a in range(target):
            cur = dp[h][a]
            if cur == 0.0:
                continue
            if h + 1 == target:
                terminal.append((target, a, cur * p))
            else:
                dp[h + 1][a] += cur * p
            if a + 1 == target:
                terminal.append((h, target, cur * q))
            else:
                dp[h][a + 1] += cur * q

    p_home = sum(prob for h, a, prob in terminal if h == target)
    p_away = 1.0 - p_home

    # Home covers if (h - a) + handicap_units > 0
    p_home_cover = sum(prob for h, a, prob in terminal if (h - a) + handicap_units > 0)
    p_away_cover = 1.0 - p_home_cover

    p_over = sum(prob for h, a, prob in terminal if (h + a) > total_line)
    p_under = 1.0 - p_over

    return {
        "unit_prob_home": round(p, 4),
        "p_home": round(p_home, 4),
        "p_away": round(p_away, 4),
        "handicap_line": handicap_units,
        "p_home_cover": round(clamp(p_home_cover, 0.08, 0.92), 4),
        "p_away_cover": round(1.0 - clamp(p_home_cover, 0.08, 0.92), 4),
        "total_line": total_line,
        "p_over": round(clamp(p_over, 0.08, 0.92), 4),
        "p_under": round(1.0 - clamp(p_over, 0.08, 0.92), 4),
    }


def mlb_run_markets(
    home_rs_pg: float,
    home_ra_pg: float,
    away_rs_pg: float,
    away_ra_pg: float,
    home_sp_era: float,
    away_sp_era: float,
    home_sp_whip: float,
    away_sp_whip: float,
    league_rpg: float = 4.42,
) -> Dict[str, object]:
    """MLB run-expectancy Poisson + extra-inning tie split for Moneyline, Run Line (+/-1.5), Total."""
    # Blend team run prevention (40%) with starting pitcher ERA/WHIP (60% for 5.5 IP + 40% bullpen)
    sp_factor_against_away = 0.58 * (home_sp_era / 4.05) * (0.7 + 0.3 * (home_sp_whip / 1.24)) + 0.42 * (home_ra_pg / league_rpg)
    sp_factor_against_home = 0.58 * (away_sp_era / 4.05) * (0.7 + 0.3 * (away_sp_whip / 1.24)) + 0.42 * (away_ra_pg / league_rpg)

    lam_h = clamp(league_rpg * (home_rs_pg / league_rpg) * sp_factor_against_home * 1.035, 2.4, 5.8)
    lam_a = clamp(league_rpg * (away_rs_pg / league_rpg) * sp_factor_against_away / 1.035, 2.3, 5.7)

    max_r = 18
    ph = [poisson_pmf(lam_h, r) for r in range(max_r + 1)]
    pa = [poisson_pmf(lam_a, r) for r in range(max_r + 1)]
    sh, sa = sum(ph), sum(pa)
    ph = [x / sh for x in ph]
    pa = [x / sa for x in pa]

    p_reg_h = 0.0
    p_tie = 0.0
    p_h_minus_1_5 = 0.0
    p_a_minus_1_5 = 0.0
    total_line = round_half(lam_h + lam_a)
    p_over = 0.0

    for rh in range(max_r + 1):
        for ra in range(max_r + 1):
            j = ph[rh] * pa[ra]
            if rh > ra:
                p_reg_h += j
            elif rh == ra:
                p_tie += j
            if rh - ra >= 2:
                p_h_minus_1_5 += j
            if ra - rh >= 2:
                p_a_minus_1_5 += j
            if rh + ra > total_line:
                p_over += j
            elif rh == ra and (rh + ra + 1) > total_line:
                p_over += j

    p_home = clamp(p_reg_h + p_tie * 0.52, 0.15, 0.85)
    p_away = 1.0 - p_home
    fav_home = p_home >= 0.5
    handicap_line = -1.5 if fav_home else 1.5
    # In MLB, home -1.5 also wins ~38% of extra-inning walk-off HR scenarios slightly, keep regulation + small extra share
    p_home_cover = clamp(p_h_minus_1_5 + p_tie * 0.18, 0.18, 0.75) if fav_home else clamp(1.0 - (p_a_minus_1_5 + p_tie * 0.24), 0.25, 0.82)

    return {
        "lambda_home": round(lam_h, 3),
        "lambda_away": round(lam_a, 3),
        "p_home": round(p_home, 4),
        "p_away": round(p_away, 4),
        "handicap_line": handicap_line,
        "p_home_cover": round(p_home_cover, 4),
        "p_away_cover": round(1.0 - p_home_cover, 4),
        "total_line": total_line,
        "p_over": round(clamp(p_over, 0.18, 0.82), 4),
        "p_under": round(1.0 - clamp(p_over, 0.18, 0.82), 4),
    }


def handball_poisson_markets(
    exp_home_goals: float,
    exp_away_goals: float,
) -> Dict[str, object]:
    """Handball normal-approximated high-scoring goal grid (60-minute match)."""
    # At 28-34 goals per team, over-dispersed goal margin has sigma ~= 4.35, total sigma ~= 5.10
    return normal_margin_markets(exp_home_goals, exp_away_goals, sigma_margin=4.35, sigma_total=5.10)
