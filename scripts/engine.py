"""Originated-line engine.

Every number this module produces is derived from the inputs in ``data/`` using the
parameters recorded in ``data/meta.json``. Nothing is read from a bookmaker.
The method is deliberately small enough to re-derive by hand; see ``site/methodology.html``.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------- probability helpers


def logistic(x: float, scale: float) -> float:
    """Logistic CDF with an explicit scale (in the units of x)."""
    if scale <= 0:
        raise ValueError("scale must be positive")
    z = x / scale
    if z > 60:
        return 1.0
    if z < -60:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


def normal_cdf(x: float, mean: float, sd: float) -> float:
    if sd <= 0:
        raise ValueError("sd must be positive")
    return 0.5 * (1.0 + math.erf((x - mean) / (sd * math.sqrt(2.0))))


def american(prob: float) -> int:
    """No-vig fair American price for a probability, rounded to the nearest 5."""
    if not 0.0 < prob < 1.0:
        raise ValueError(f"probability out of range: {prob}")
    if prob >= 0.5:
        price = -100.0 * prob / (1.0 - prob)
        price = max(price, -10000.0)
    else:
        price = 100.0 * (1.0 - prob) / prob
        price = min(price, 10000.0)
    rounded = int(round(price / 5.0) * 5)
    if -100 < rounded < 100:
        rounded = -100 if rounded < 0 else 100
    return rounded


def implied(price: int) -> float:
    if price < 0:
        return (-price) / (-price + 100.0)
    return 100.0 / (price + 100.0)


def decimal(price: int) -> float:
    if price < 0:
        return 1.0 + 100.0 / (-price)
    return 1.0 + price / 100.0


# ---------------------------------------------------------------- rating


def shrunk_goal_rate(gf: int, ga: int, gp: int, shrink: float) -> float:
    """Goal differential per game, pulled toward the league mean (0) by ``shrink`` games."""
    if gp <= 0:
        return 0.0
    return ((gf - ga) / gp) * (gp / (gp + shrink))


def nhl_rating(team: dict, params: dict) -> dict:
    gp = int(team["gp"])
    return {
        "abbr": team["abbr"],
        "gp": gp,
        "gf_pg": team["gf"] / gp if gp else None,
        "ga_pg": team["ga"] / gp if gp else None,
        "gd_pg": (team["gf"] - team["ga"]) / gp if gp else None,
        "rating": shrunk_goal_rate(team["gf"], team["ga"], gp, params["nhl_shrink_games"]),
    }


def nhl_market(home: dict, away: dict, params: dict) -> dict:
    """Originate money line, puck line and total for one NHL fixture."""
    shrink = params["nhl_shrink_games"]
    r_home = shrunk_goal_rate(home["gf"], home["ga"], home["gp"], shrink)
    r_away = shrunk_goal_rate(away["gf"], away["ga"], away["gp"], shrink)
    margin = r_home + params["nhl_home_goals"] - r_away
    p_home = logistic(margin, params["nhl_logistic_scale"])

    # Puck line is quoted at -1.5 / +1.5, i.e. P(margin > 1.5).
    p_home_cover = 1.0 - logistic(1.5 - margin, params["nhl_logistic_scale"])
    p_home_cover = min(max(p_home_cover, 0.01), 0.99)

    # Total: blend each side's goals for with the opponent's goals against.
    exp_home = (home["gf"] / home["gp"] + away["ga"] / away["gp"]) / 2.0
    exp_away = (away["gf"] / away["gp"] + home["ga"] / home["gp"]) / 2.0
    raw_total = exp_home + exp_away
    gp_weight = min(home["gp"], away["gp"])
    total = (raw_total * gp_weight + params["nhl_league_total"] * shrink) / (gp_weight + shrink)
    # Keep totals on a half-goal so the over/under cannot push.
    total_line = math.floor(total + 0.5) + 0.5
    p_over = 1.0 - normal_cdf(total_line, total, params["nhl_total_sd"])
    p_over = min(max(p_over, 0.01), 0.99)

    return {
        "engine": "nhl",
        "inputs": {
            "home": nhl_rating(home, params),
            "away": nhl_rating(away, params),
        },
        "expected_margin": round(margin, 3),
        "expected_total": round(total, 2),
        "money_line": {
            "home": american(p_home),
            "away": american(1.0 - p_home),
            "p_home": round(p_home, 4),
            "p_away": round(1.0 - p_home, 4),
            "home_team": home["name"],
            "away_team": away["name"],
            "favoured": home["name"] if p_home >= 0.5 else away["name"],
        },
        "handicap": {
            "line_home": -1.5,
            "line_away": 1.5,
            "home": american(p_home_cover),
            "away": american(1.0 - p_home_cover),
            "p_home_cover": round(p_home_cover, 4),
            "p_away_cover": round(1.0 - p_home_cover, 4),
        },
        "total": {
            "line": total_line,
            "over": american(p_over),
            "under": american(1.0 - p_over),
            "p_over": round(p_over, 4),
            "p_under": round(1.0 - p_over, 4),
        },
        "notes": [
            "Money line includes overtime and shootouts.",
            "Puck line is the standard 1.5-goal handicap.",
            "Prices are no-vig fair odds, not bookmaker prices.",
        ],
    }


def nba_market(home: dict, away: dict, params: dict) -> dict:
    """Baseline NBA market.

    No 2026-27 form exists for these teams at the snapshot, so every club carries the
    league-average rating and only home court separates the sides. The engine records
    that explicitly instead of inventing a prior-season strength.
    """
    margin = params["nba_home_points"]
    p_home = logistic(margin, params["nba_logistic_scale"])
    spread = -params["nba_home_points"]
    return {
        "engine": "nba-baseline",
        "inputs": {
            "home": {"abbr": home["abbr"], "name": home["name"], "gp": home["gp"], "rating": 0.0},
            "away": {"abbr": away["abbr"], "name": away["name"], "gp": away["gp"], "rating": 0.0},
        },
        "expected_margin": round(margin, 3),
        "expected_total": None,
        "money_line": {
            "home": american(p_home),
            "away": american(1.0 - p_home),
            "p_home": round(p_home, 4),
            "p_away": round(1.0 - p_home, 4),
            "home_team": home["name"],
            "away_team": away["name"],
            "favoured": home["name"] if p_home >= 0.5 else away["name"],
        },
        "handicap": {
            "line_home": spread,
            "line_away": -spread,
            "home": -100,
            "away": -100,
            "p_home_cover": 0.5,
            "p_away_cover": 0.5,
        },
        "total": None,
        "notes": [
            "Baseline line: no 2026-27 games played, so both teams are rated league-average.",
            "Home court is worth 2.5 points; the spread is therefore pick'em against the number.",
            "No total is originated because no verified league scoring baseline is loaded.",
            "Prices are no-vig fair odds, not bookmaker prices.",
        ],
    }


# ---------------------------------------------------------------- picks and confidence


# 2026-10-22 odds-window remediation, applied uniformly across all layers:
# HIGH additionally needs probability >= 70% and a fair no-vig American price
# inside the brief's [-250, +10000] window.
HIGH_PROB_FLOOR = 0.70
ODDS_WINDOW_MIN_AMERICAN = -250
ODDS_WINDOW_MAX_AMERICAN = 10000


def _fair_decimal(probability: float) -> float:
    return round(1.0 / max(probability, 1e-6), 2)


def _american(decimal_odds: float) -> int:
    if decimal_odds >= 2.0:
        return round((decimal_odds - 1.0) * 100.0)
    return round(-100.0 / (decimal_odds - 1.0))


def window_high_eligible(probability: float) -> tuple[bool, int]:
    american = _american(_fair_decimal(probability))
    return (probability >= HIGH_PROB_FLOOR
            and ODDS_WINDOW_MIN_AMERICAN <= american <= ODDS_WINDOW_MAX_AMERICAN), american


def confidence_label(edge: float, *, evidence: bool, sample_ok: bool, baseline: bool,
                     params: dict, probability: float | None = None) -> tuple[str, str]:
    """Return (label, reason). Labels are capped when the evidence pack is missing."""
    if baseline:
        return "low", "Baseline pricing: no current-season sample to separate the teams."
    if edge >= params["high_edge"]:
        if not evidence:
            return "medium", f"Model edge {edge:.3f} clears the high bar, but no evidence pack is attached."
        if not sample_ok:
            return "medium", "Model edge clears the high bar, but the games-played sample is below the minimum."
        eligible, american = window_high_eligible(probability or 0.0)
        if not eligible:
            return ("medium",
                    f"Model edge {edge:.3f} with an evidence pack, but probability "
                    f"{(probability or 0.0) * 100:.1f}% / fair American {american:+d} fails the "
                    "70% floor or the [-250, +10000] odds window; capped at medium on 2026-10-22.")
        return "high", f"Model edge {edge:.3f} with an official evidence pack, sufficient sample, and an in-window fair price ({american:+d})."
    if edge >= params["medium_edge"]:
        return "medium", f"Model edge {edge:.3f} clears the medium bar."
    return "low", f"Model edge {edge:.3f} is below the medium bar."


def choose_selection(market: dict) -> dict:
    """Pick the biggest edge in each market, and flag the primary match-winner pick."""
    ml = market["money_line"]
    home_side = {"market": "Money line", "selection": ml["home_team"], "probability": ml["p_home"], "price": ml["home"]}
    away_side = {"market": "Money line", "selection": ml["away_team"], "probability": ml["p_away"], "price": ml["away"]}
    primary = home_side if ml["p_home"] >= ml["p_away"] else away_side
    leans = []
    for side in (home_side, away_side):
        if side is not primary and side["probability"] >= 0.45:
            leans.append(side)
    hc = market.get("handicap")
    if hc:
        if hc["p_home_cover"] >= 0.55:
            leans.append({"market": f"Puck line {hc['line_home']:+g}" if market["engine"] == "nhl" else f"Spread {hc['line_home']:+g}",
                          "selection": ml["home_team"], "probability": hc["p_home_cover"], "price": hc["home"]})
        if hc["p_away_cover"] >= 0.55:
            leans.append({"market": f"Puck line {hc['line_away']:+g}" if market["engine"] == "nhl" else f"Spread {hc['line_away']:+g}",
                          "selection": ml["away_team"], "probability": hc["p_away_cover"], "price": hc["away"]})
    tot = market.get("total")
    if tot:
        if tot["p_over"] >= 0.55:
            leans.append({"market": f"Total {tot['line']:g}", "selection": "Over", "probability": tot["p_over"], "price": tot["over"]})
        if tot["p_under"] >= 0.55:
            leans.append({"market": f"Total {tot['line']:g}", "selection": "Under", "probability": tot["p_under"], "price": tot["under"]})
    return {"primary": primary, "leans": leans}
