#!/usr/bin/env python3
"""Signal desk (session 6b10ecda) - price origination helpers.

Every function here turns OFFICIAL numeric inputs (captured under
data/signal/captures/) into our own prices. No bookmaker price is ever an
input: market prices are only ever stored alongside a row as a cross-check.

Conventions
-----------
* probabilities are "fair" probabilities (they sum to 1 across a market's
  outcomes - no overround is added anywhere on this desk);
* American odds are derived from the fair probability;
* published probabilities are clamped to [0.05, 0.95] because a single
  sporting fixture always keeps irreducible variance (documented cap).
"""
from __future__ import annotations

import math

PROB_FLOOR = 0.05
PROB_CEIL = 0.95

# ---------------------------------------------------------------- odds maths


def clamp(p: float) -> float:
    return max(PROB_FLOOR, min(PROB_CEIL, p))


def decimal_odds(p: float) -> float:
    return round(1.0 / p, 2)


def american_odds(p: float) -> int:
    """Fair American price for probability p."""
    if p >= 0.5:
        return -int(round(100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def fmt_american(p: float) -> str:
    a = american_odds(p)
    return f"+{a}" if a > 0 else str(a)


def in_focus_band(p: float) -> bool:
    """User band: fair American price between -250 and +10000 inclusive.

    -250 corresponds to p = 0.714285..., +10000 to p = 0.00990..., so the
    band is the probability interval [0.00990, 0.714285].
    """
    return -250 <= american_odds(p) <= 10000


def confidence(p: float) -> str:
    if p >= 0.70:
        return "high"
    if p >= 0.60:
        return "medium"
    return "low"


# ------------------------------------------------------------ distributions


def poisson_pmf(lam: float, k: int) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_grid(lam_a: float, lam_b: float, nmax: int = 15):
    pa = [poisson_pmf(lam_a, i) for i in range(nmax + 1)]
    pb = [poisson_pmf(lam_b, i) for i in range(nmax + 1)]
    return pa, pb


def poisson_match(lam_home: float, lam_away: float, nmax: int = 15,
                  ot_split: bool = True):
    """Return dict of win/tie probabilities and derived lines.

    ot_split=True means a regulation tie is resolved 50/50 (ice hockey).
    """
    pa, pb = poisson_grid(lam_home, lam_away, nmax)
    p_home = p_away = p_tie = 0.0
    margin = {}
    total = {}
    for i, phi in enumerate(pa):
        for j, paw in enumerate(pb):
            q = phi * paw
            if i > j:
                p_home += q
            elif j > i:
                p_away += q
            else:
                p_tie += q
            margin[i - j] = margin.get(i - j, 0.0) + q
            total[i + j] = total.get(i + j, 0.0) + q
    out = {"p_home_reg": p_home, "p_away_reg": p_away, "p_tie_reg": p_tie,
           "margin": margin, "total": total}
    if ot_split:
        out["p_home"] = p_home + p_tie / 2.0
        out["p_away"] = p_away + p_tie / 2.0
    else:
        out["p_home"] = p_home
        out["p_away"] = p_away
    return out


def total_over(total_dist: dict, line: float) -> float:
    return sum(q for k, q in total_dist.items() if k > line)


def handicap_cover(margin_dist: dict, line: float, ot_split: bool = True,
                   p_tie: float = 0.0) -> float:
    """P(home margin + line > 0). For ice hockey the OT goal is added to the
    winner of the coin-flip, so a regulation tie becomes +/-1."""
    p = 0.0
    for m, q in margin_dist.items():
        if m == 0 and ot_split:
            # OT: half the mass becomes +1, half becomes -1
            p += (q / 2.0) * (1.0 if 1 + line > 0 else 0.0)
            p += (q / 2.0) * (1.0 if -1 + line > 0 else 0.0)
        else:
            if m + line > 0:
                p += q
    return p


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def margin_model(exp_margin: float, sigma: float):
    """Normal margin model used for basketball / rugby / handball."""
    p_home = normal_cdf(exp_margin / sigma)
    return {"p_home": p_home, "p_away": 1.0 - p_home, "exp_margin": exp_margin,
            "sigma": sigma}


def normal_handicap(exp_margin: float, sigma: float, line: float) -> float:
    return normal_cdf((exp_margin + line) / sigma)


def normal_total_over(exp_total: float, sigma: float, line: float) -> float:
    return 1.0 - normal_cdf((line - exp_total) / sigma)


# ------------------------------------------------------------ sport helpers


def pythagorean(rs: float, ra: float, exponent: float = 1.83) -> float:
    return rs ** exponent / (rs ** exponent + ra ** exponent)


def log5(p_a: float, p_b: float) -> float:
    """Probability team A beats team B given their true win rates."""
    num = p_a - p_a * p_b
    den = p_a + p_b - 2 * p_a * p_b
    return num / den


def apply_home_edge(p: float, edge: float) -> float:
    """Multiply the home side's odds ratio by `edge` (1.08 == +8%)."""
    odds = p / (1 - p) * edge
    return odds / (1 + odds)


def bradley_terry(strength_a: float, strength_b: float, k: float = 1.1) -> float:
    """Logistic comparison of two log-scaled strengths (snooker money)."""
    return 1.0 / (1.0 + math.exp(-k * (strength_a - strength_b)))


def shrink(value: float, league_mean: float, games: int, prior_games: int = 10) -> float:
    w = games / float(games + prior_games)
    return w * value + (1 - w) * league_mean


def conditional_field(weights: dict) -> dict:
    """Normalise a dict of positive weights into conditional probabilities."""
    s = float(sum(weights.values()))
    return {k: v / s for k, v in weights.items()}


def round_line(x: float) -> float:
    """Nearest .5 line."""
    return round(x * 2) / 2.0
