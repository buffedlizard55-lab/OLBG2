#!/usr/bin/env python3
"""Rating inputs and probability rules for the live desk.

Everything in here is a published parameter, not a fitted secret.  The desk is a research
snapshot, so the point is that a reader can recompute any number on the site from the
official table it is built on plus the constants below.

Probability sources, strongest first
------------------------------------
``official-model``  a head-to-head probability computed from an official numeric table
                    (NHL club standings, MLB team rates, EuroLeague standings, WTA ranking
                    points, F1 championship points).  These are the only rows that can be
                    graded high.
``crowd-consensus`` OLBG publishes, for every tip it lists, the share of its tipsters who
                    backed that selection and the number of winning tips recorded.  That is
                    a real published number but it is a crowd, not a verified rating, so a
                    consensus-only row is capped at medium confidence and says so.
``no-basis``        neither is available; the row keeps the fixture and the OLBG link and
                    carries no price.

Formulae
--------
NHL    p_home = logistic(1.30 * (goal_diff_per_game_home - goal_diff_per_game_away) + 0.15)
       where goal_diff_per_game is (GF-GA)/GP from the official standings and +0.15 is the
       league home edge expressed in logit units.
MLB    p_home = logistic(0.28 * (run_diff_per_game_home - run_diff_per_game_away)
                         + 0.11 + 0.35 * (ERA_away - ERA_home) / 9)
       run_diff_per_game from the official team hitting and pitching splits.
EL     margin = 1.9 * (point_diff_home - point_diff_away) + 2.6 (home court)
       p_home = normal CDF(margin / 9.5)
Tennis p = logistic(0.55 * (log(points_player) - log(points_opponent)))
F1     p(driver wins) = softmax over the entered drivers of points / 55, restricted to the
       ten drivers the desk lists in its F1 note.  A race-winner market is not a
       two-horse market, so this is deliberately coarse and is never graded high.

Market anchor
-------------
A governing-body table describes the season; the quoted price describes this match.  Neither
is sufficient alone, so for the five official-model sports the two are combined in logit
space with MARKET_WEIGHT on the quote:

    logit(p) = (1 - MARKET_WEIGHT) * logit(p_official) + MARKET_WEIGHT * logit(p_quoted)

with MARKET_WEIGHT = 0.60.  Without the anchor, a five-game goal difference would make an
NHL club a 95% favourite, which no hockey market believes; without the official term the
desk would simply be copying a bookmaker's number.  The blended number is our line, and it
differs from the quote on every row where the two inputs disagree.

Where no official table exists but a quote does, the row is graded on the quote alone and
labelled ``quoted-market``.  Where neither exists, OLBG's published tip share is used and
labelled ``crowd-consensus``; a tip share is not a price, so that tier can never be high.

A price is "in band" when the fair American price lies inside [-250, +10000].
"""
from __future__ import annotations

import math
import re

HOME_EDGE_NHL = 0.15
NHL_SCALE = 1.30
MLB_SCALE = 0.28
MLB_HOME = 0.11
MLB_ERA_SCALE = 0.35
EL_SCALE = 1.9
EL_HOME = 2.6
EL_SIGMA = 9.5
TENNIS_SCALE = 0.55
F1_SCALE = 55.0
MARKET_WEIGHT = 0.60


def blend(official_p: float, quoted_decimal) -> float | None:
    """Combine the official-table probability with the quoted price in logit space."""
    try:
        dec = float(quoted_decimal)
    except (TypeError, ValueError):
        return round(official_p, 4)
    if dec <= 1.0:
        return round(official_p, 4)
    p_market = min(max((1.0 / dec) / QUOTE_MARGIN, 0.02), 0.95)
    o = min(max(official_p, 0.02), 0.95)
    z = (1 - MARKET_WEIGHT) * math.log(o / (1 - o)) + MARKET_WEIGHT * math.log(p_market / (1 - p_market))
    return round(1 / (1 + math.exp(-z)), 4)


QUOTE_MARGIN = 1.04


def quoted_probability(decimal) -> float | None:
    """A single quoted decimal, normalised for an assumed 4% margin on that quote.

    OLBG carries one price per tipped selection, not a two-sided board, so a true de-vig is
    impossible.  Dividing the implied probability by QUOTE_MARGIN is the smallest honest
    adjustment: it removes an assumed built-in margin without pretending to know the other
    side.  The assumption is printed on the method page.
    """
    try:
        dec = float(decimal)
    except (TypeError, ValueError):
        return None
    if dec <= 1.0:
        return None
    return round(min(max((1.0 / dec) / QUOTE_MARGIN, 0.02), 0.95), 4)


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))


def norm_sf(x: float) -> float:
    return 1.0 - norm_cdf(x)


# --------------------------------------------------------------------------- official tables
WTA_ROW = re.compile(
    r"(\d{1,3})\s*-\s*([A-Z][^0-9]{2,40}?)\s+([A-Z]{3})\s+(\d{1,2})\s+(\d{1,3})\s+([\d,]+)"
)


def wta_rankings(text: str) -> dict[str, dict]:
    """Parse the official WTA singles ranking list.

    A row on wtatennis.com reads, after tag stripping:
        ``2 - Aryna Sabalenka BLR 28 20 7,550``
    rank - name country age events points.
    """
    out: dict[str, dict] = {}
    for m in WTA_ROW.finditer(text):
        rank, name, country, age, events, points = m.groups()
        key = re.sub(r"[^a-z ]+", "", name.lower()).strip()
        out[key] = {
            "rank": int(rank), "name": name.strip(), "country": country,
            "age": int(age), "events": int(events), "points": int(points.replace(",", "")),
        }
    return out


F1_ROW = re.compile(r"(\d{1,2})\s+([A-Z][A-Za-z'’.\-]+(?: [A-Z][A-Za-z'’.\-]+)+)\s+([A-Z]{3})\s+([A-Z]{3})\s+(.{1,40}?)\s+(\d{1,3})\b")


def f1_standings(text: str) -> dict[str, dict]:
    """Parse the official Formula 1 drivers' championship table.

    A row reads: ``1 Kimi Antonelli ANT ITA Mercedes 340``.
    """
    out: dict[str, dict] = {}
    for m in F1_ROW.finditer(text):
        pos, name, abbr, nat, team, pts = m.groups()
        key = re.sub(r"[^a-z ]+", "", name.lower()).strip()
        out[key] = {
            "pos": int(pos), "name": name.strip(), "abbr": abbr, "nat": nat,
            "team": team.strip(), "points": int(pts),
        }
    return out


# --------------------------------------------------------------------------- probabilities
def hockey_probability(home: dict, away: dict) -> float | None:
    for t in (home, away):
        if not t or not t.get("gp"):
            return None
    hd = (home["gf"] - home["ga"]) / home["gp"]
    ad = (away["gf"] - away["ga"]) / away["gp"]
    return round(logistic(NHL_SCALE * (hd - ad) + HOME_EDGE_NHL), 4)


def baseball_probability(home: dict, away: dict) -> float | None:
    try:
        hr = (home["runs"] - home["ra"]) / max(home["gp"], 1)
        ar = (away["runs"] - away["ra"]) / max(away["gp"], 1)
        era_h = float(home.get("era") or 4.20)
        era_a = float(away.get("era") or 4.20)
    except (KeyError, TypeError, ValueError):
        return None
    return round(logistic(MLB_SCALE * (hr - ar) + MLB_HOME + MLB_ERA_SCALE * (era_a - era_h) / 9), 4)


def euroleague_probability(home: dict, away: dict) -> float | None:
    try:
        hd = (home["pf"] - home["pa"]) / max(home.get("gp") or 1, 1)
        ad = (away["pf"] - away["pa"]) / max(away.get("gp") or 1, 1)
    except (KeyError, TypeError, ZeroDivisionError):
        return None
    margin = EL_SCALE * (hd - ad) + EL_HOME
    return round(norm_cdf(margin / EL_SIGMA), 4)


def tennis_probability(player_points: int, opponent_points: int) -> float:
    return round(logistic(TENNIS_SCALE * (math.log(player_points) - math.log(opponent_points))), 4)


def f1_winner_probability(points: int, field_points: list[int]) -> float:
    exps = [math.exp(p / F1_SCALE) for p in field_points]
    total = sum(exps) or 1.0
    return round(math.exp(points / F1_SCALE) / total, 4)


# --------------------------------------------------------------------------- grading
def american(p: float) -> int:
    p = min(max(p, 0.0002), 0.9998)
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def decimal_from_american(a: int) -> float:
    return round(1 + (100 / -a) if a < 0 else 1 + a / 100, 3)


def in_band(a: int) -> bool:
    return -250 <= a <= 10000


def grade(p: float, tier: str) -> str:
    """A tip share can never be high. A quote or an official table can."""
    if tier == "crowd-consensus":
        return "medium" if p >= 0.60 else "low"
    if p >= 0.70:
        return "high"
    if p >= 0.60:
        return "medium"
    return "low"


def consensus_probability(confidence, win_tips) -> tuple[float | None, str]:
    """OLBG's published tip share, shrunk toward an even split.

    The share is a percentage of the tipsters who backed that one selection; a share of 0
    or a missing value gives no estimate at all.
    """
    try:
        share = float(confidence)
    except (TypeError, ValueError):
        return None, "no published tip share"
    if share <= 0 or share > 100:
        return None, "no published tip share"
    shrunk = 0.5 + 0.5 * ((share / 100) - 0.5) * 2 * 0.5  # half-shrunk toward 0.5
    try:
        tips = int(float(win_tips))
    except (TypeError, ValueError):
        tips = 0
    return round(min(max(shrunk, 0.05), 0.95), 4), f"tip share {share:g}% over {tips} winning tips"
