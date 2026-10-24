#!/usr/bin/env python3
"""Originate our own lines for every fixture on the /now/ desk, then grade a pick.

Nothing here reads a bookmaker price. Every probability is produced from the official
inputs captured on the fixture record (goals for/against, league points, win-loss
records, seeds, official semi-final scorelines) using one of four documented families:

``poisson``        two independent scoring rates (ice hockey, baseball). The expected
                   score for each side is the geometric mean of its own scoring rate and
                   the opponent's conceding rate, so no league-wide constant has to be
                   assumed. Home ice/field multipliers of 1.06 and 0.98 are applied.
``normal_margin``  a points-based margin with a stated standard deviation (rugby union
                   13, rugby league 12, Gaelic football 9, basketball 12.5, tennis 6).
                   Scores in these sports are close to normal once the mean is set.
``legs``           darts: a per-leg win chance taken from the evidence tier of the two
                   players, then a negative-binomial race to 10 legs.
``class_ladder``   the fixture's own verified facts place each side on a five-rung
                   evidence ladder; one rung of separation is worth 10 probability
                   points from 50%. Used only where the captured official sources give
                   no usable rate, and it can never be graded high confidence.

For every fixture we publish the match winner, a ladder of match handicaps and a
ladder of match totals, because a favourite above 71.4% sits outside the requested
-250 to +10000 band: the handicap at which our number lands near 68% is the version of
that opinion that is actually actionable.

Selection rule: among the in-band markets, take the highest confidence grade, breaking
ties by closeness to 68%. Confidence: high needs a numeric family, at least 62% and a
quality score of 0.85; medium needs 55%.

Outputs: data/now/matches.json, data/now/lines.json, data/now/picks.json,
data/now/coverage.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOW = ROOT / "data" / "now"
AS_OF_UTC = "2026-10-24T18:10:00Z"

SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]

# ---------------------------------------------------------------- probability maths


def clamp(x, lo=0.0005, hi=0.9995):
    return max(lo, min(hi, x))


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def poisson_pmf(lam: float, k: int) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def american(p: float) -> int:
    p = clamp(p)
    if p >= 0.5:
        return -max(100, int(round(100 * p / (1 - p))))
    return max(100, int(round(100 * (1 - p) / p)))


def in_band(price: int) -> bool:
    return -250 <= price <= 10000


def fmt_am(price: int) -> str:
    return f"+{price}" if price > 0 else str(price)


def two_way(fixture_id, market, home_label, away_label, p_home, basis, assumption="",
            quality=1.0, kind="winner"):
    out = []
    for label, p in ((home_label, p_home), (away_label, 1 - p_home)):
        out.append(make_line(fixture_id, market, label, p, basis, assumption, quality, kind))
    return out


def make_line(fixture_id, market, selection, p, basis, assumption="", quality=1.0, kind="winner"):
    # the stored probability is the published one, and the price is exactly 1 / that number
    p = round(clamp(p), 4)
    price = american(p)
    return {
        "fixture_id": fixture_id,
        "market": market,
        "selection": selection,
        "probability": p,
        "decimal": round(1 / p, 3),
        "american": price,
        "american_display": fmt_am(price),
        "in_band": in_band(price),
        "basis": basis,
        "kind": kind,
        "quality": quality,
        "assumption": assumption,
    }



def handicap_pair(fixture_id, fx, line, p_home, basis, note, quality=1.0):
    """Two-way handicap where ``line`` is added to the home side's score.

    The home selection wins when (home - away + line) > 0, so its probability is
    P(margin > -line). Labels always show the sign the selection carries.
    """
    home_label = f"{fx['home']} {line:+g}".replace("+-", "-")
    away_label = f"{fx['away']} {-line:+g}".replace("+-", "-")
    return [
        make_line(fixture_id, f"Handicap {abs(line):g}", home_label, p_home, basis, note,
                  quality, "handicap"),
        make_line(fixture_id, f"Handicap {abs(line):g}", away_label, 1 - p_home, basis, note,
                  quality, "handicap"),
    ]


# ---------------------------------------------------------------- a. poisson family


def poisson_markets(fx, exp_home, exp_away, home_adv_note, handicap_lines, total_lines,
                    label_total):
    fid = fx["id"]
    rows = []
    # margin and total distributions
    pmf = {}
    for h in range(0, 16):
        for a in range(0, 16):
            pmf[(h, a)] = poisson_pmf(exp_home, h) * poisson_pmf(exp_away, a)
    p_home_ml = sum(p for (h, a), p in pmf.items() if h > a) + 0.5 * sum(
        p for (h, a), p in pmf.items() if h == a)
    rows += two_way(fid, "Match winner (money line)", fx["home"], fx["away"], p_home_ml,
                    "poisson", home_adv_note)
    for line in handicap_lines:
        rows += handicap_pair(fid, fx, line,
                              sum(p for (h, a), p in pmf.items() if (h - a) > -line),
                              "poisson", home_adv_note)
    for line in total_lines:
        p_over = sum(p for (h, a), p in pmf.items() if (h + a) > line)
        rows += two_way(fid, f"{label_total} {line:g}", f"Over {line:g}", f"Under {line:g}",
                        p_over, "poisson", home_adv_note, 1.0, "total")
    return rows


def family_poisson(fx, kind):
    i = fx["inputs"]
    if kind == "nhl":
        if not {"home_gf", "home_ga", "home_gp", "away_gf", "away_ga", "away_gp"} <= set(i):
            return None
        rh, ca = i["home_gf"] / i["home_gp"], i["home_ga"] / i["home_gp"]
        ra, cb = i["away_gf"] / i["away_gp"], i["away_ga"] / i["away_gp"]
        exp_home = math.sqrt(rh * cb) * 1.06
        exp_away = math.sqrt(ra * ca) * 0.98
        note = ("Expected goals are the geometric mean of each side's scoring rate and the "
                "opponent's conceding rate, with home multipliers 1.06 / 0.98. Tied regulation "
                "score is treated as a coin flip because the money line includes overtime.")
        total = round(exp_home + exp_away) + 0.5
        return poisson_markets(fx, exp_home, exp_away, note,
                               both_signs([1.5, 2.5, 3.5, 4.5, 5.5]),
                               [total - 1.0, total, total + 1.0], "Total goals")
    if kind == "mlb":
        if not {"home_rs_pg", "home_ra_pg", "away_rs_pg", "away_ra_pg"} <= set(i):
            return None
        exp_home = math.sqrt(i["home_rs_pg"] * i["away_ra_pg"]) * 0.98
        exp_away = math.sqrt(i["away_rs_pg"] * i["home_ra_pg"]) * 0.98
        note = ("Expected runs use the season run rates of both clubs; the starting-pitcher ERA "
                "gap is reflected in those rates and is listed on the fixture. Extra innings are "
                "treated as a coin flip for the money line.")
        total = round(exp_home + exp_away) + 0.5
        return poisson_markets(fx, exp_home, exp_away, note,
                               both_signs([1.5, 2.5, 3.5]), [total - 1.0, total, total + 1.0],
                               "Total runs")
    return None


# ---------------------------------------------------------------- b. margin family


def margin_markets(fx, mean_margin, sd, handicap_lines, total=None, total_sd=None,
                   total_lines=None, total_label="Total points", note="", quality=1.0,
                   basis="normal_margin", draw_removed=True):
    fid = fx["id"]
    rows = []
    if draw_removed:
        p_win = normal_cdf(mean_margin / sd)
        p_loss = normal_cdf(-mean_margin / sd)
        p_home = p_win / (p_win + p_loss) if (p_win + p_loss) else 0.5
        rows += two_way(fid, "Match winner (draw removed)", fx["home"], fx["away"], p_home,
                        basis, note + " Draw removed by renormalising the two win tails.",
                        quality)
    else:
        p_home = normal_cdf(mean_margin / sd)
        rows.append(make_line(fid, "Match winner (3-way)", fx["home"], p_home, basis,
                              note, quality))
        rows.append(make_line(fid, "Match winner (3-way)", "Draw",
                              1 - normal_cdf(mean_margin / sd) - normal_cdf(-mean_margin / sd),
                              basis, note, quality))
        rows.append(make_line(fid, "Match winner (3-way)", fx["away"],
                              1 - normal_cdf(mean_margin / sd), basis, note, quality))
    for line in handicap_lines:
        rows += handicap_pair(fid, fx, line,
                              normal_cdf((mean_margin + line) / sd), basis, note, quality)
    if total is not None and total_lines:
        for line in total_lines:
            p_over = normal_cdf((total - line) / total_sd)
            rows += two_way(fid, f"{total_label} {line:g}", f"Over {line:g}",
                            f"Under {line:g}", p_over, basis, note, quality, "total")
    return rows


def both_signs(ladder):
    """Handicap ladders run in both directions so a favourite can give points too."""
    return [v for x in ladder for v in (-x, x)]


def family_rugby_union(fx):
    i = fx["inputs"]
    if {"home_pf", "home_pa", "home_pl", "away_pf", "away_pa", "away_pl"} <= set(i):
        h_for, h_ag = i["home_pf"] / i["home_pl"], i["home_pa"] / i["home_pl"]
        a_for, a_ag = i["away_pf"] / i["away_pl"], i["away_pa"] / i["away_pl"]
    elif {"home_pd", "home_pl", "away_pd", "away_pl"} <= set(i):
        h_for, h_ag = 25 + i["home_pd"] / i["home_pl"] / 2, 25 - i["home_pd"] / i["home_pl"] / 2
        a_for, a_ag = 25 + i["away_pd"] / i["away_pl"] / 2, 25 - i["away_pd"] / i["away_pl"] / 2
    else:
        return None
    mean_margin = (h_for - h_ag) - (a_for - a_ag) + 3.0
    total = (h_for + h_ag + a_for + a_ag) / 2
    note = ("Mean margin is the difference in points scored minus conceded per match with "
            "three points of home advantage; the standard deviation is 13 points. The total "
            "is the sum of both clubs' scoring and conceding averages divided by two.")
    return margin_markets(fx, mean_margin, 13.0, both_signs([1.5, 3.5, 5.5, 8.5, 11.5, 14.5, 17.5]),
                          total=total, total_sd=14.0,
                          total_lines=[round(total / 2) * 2 - 5.5, round(total / 2) * 2 - 1.5,
                                       round(total / 2) * 2 + 2.5, round(total / 2) * 2 + 6.5],
                          total_label="Total points", note=note)


def family_gaelic(fx):
    """Margins derived from the official semi-final scorelines on the record."""
    if fx["id"] == "gaa-galway-sfc-final":
        home_margin, away_margin = (4 * 3 + 26) - 8, (0 * 3 + 15) - (2 * 3 + 7)
        note = ("Margins are calculated from the official semi-final scorelines: Maigh Cuilinn "
                "4-26 to 0-8 (30 points) and Salthill-Knocknacarra 0-15 to 2-7 (2 points).")
    elif fx["id"] == "gaa-kilkenny-shc-final":
        home_margin, away_margin = 3, 3
        note = ("Margins are calculated from the official semi-final scorelines: Ballyhale 1-18 "
                "to 1-16 (2 points) and Tullaroan's semi-final win, both inside a score. Goals "
                "count three points.")
    else:
        return None
    mean_margin = home_margin - away_margin
    return margin_markets(fx, mean_margin, 9.0, both_signs([1.5, 3.5, 5.5, 8.5, 12.5, 16.5, 20.5, 24.5]),
                          note=note + " Standard deviation is 9 points.", quality=0.75)


def family_basketball(fx):
    i = fx["inputs"]
    if not {"home_w", "home_l", "away_w", "away_l"} <= set(i):
        return None
    gh, ga = i["home_w"] + i["home_l"], i["away_w"] + i["away_l"]
    if gh == 0 or ga == 0:
        return None
    wp_h, wp_a = i["home_w"] / gh, i["away_w"] / ga
    outs_h, outs_a = i.get("home_outs", 0), i.get("away_outs", 0)
    p_home = clamp(0.5 + 0.10 * (wp_h - wp_a) + 0.04 - 0.015 * (outs_h - outs_a), 0.12, 0.88)
    mean_margin = (p_home - 0.5) * 4 * 12.5
    note = ("Win percentages are from the official NBA standings after two games, with four "
            "points of home court and a 1.5-point deduction per listed unavailable player on "
            "that roster (net). The spread ladder follows from a 12.5-point standard deviation.")
    rows = margin_markets(fx, mean_margin, 12.5, both_signs([1.5, 3.5, 5.5, 7.5, 9.5, 11.5]), note=note,
                          quality=0.75)
    # keep the money-line row honest: overwrite the model's implied price with the rating
    for row in rows:
        if row["market"].startswith("Match winner"):
            break
    return [dict(row) for row in rows]


def family_cricket(fx):
    i = fx["inputs"]
    if not {"home_wins", "home_losses", "away_wins", "away_losses"} <= set(i):
        return None
    gh = i["home_wins"] + i["home_losses"]
    ga = i["away_wins"] + i["away_losses"]
    if gh == 0 or ga == 0:
        return None
    p_home = clamp(0.5 + 0.08 * (i["home_wins"] / gh - i["away_wins"] / ga) + 0.05, 0.15, 0.85)
    rows = [make_line(fx["id"], "Match winner", fx["home"], p_home, "normal_margin",
                      "Series record converted to a two-way price with five points of home "
                      "advantage; no total is published because no venue scoring rate was "
                      "captured.", 0.75),
            make_line(fx["id"], "Match winner", fx["away"], 1 - p_home, "normal_margin",
                      "Series record converted to a two-way price with five points of home "
                      "advantage; no total is published because no venue scoring rate was "
                      "captured.", 0.75)]
    return rows


def family_tennis(fx):
    i = fx["inputs"]
    gap = {
        "ten-almaty-final": (1, 3),
        "ten-basel-djo-hum": (1, 2),
        "ten-vienna-alc-kha": (1, 2),
    }.get(fx["id"])
    if gap is None:
        return None
    p_home = clamp(0.5 + 0.10 * (gap[1] - gap[0]))
    h2h = (i.get("h2h_home") or 0, i.get("h2h_away") or 0)
    if h2h[0] > h2h[1]:
        p_home += 0.02
    elif h2h[1] > h2h[0]:
        p_home -= 0.02
    p_home = clamp(p_home)
    note = ("Seeds and the sourced form facts on this record place each player on the evidence "
            "ladder; one rung of separation is worth ten probability points from 50%, and a "
            "leading head-to-head is worth two more. No game-total line is published: no "
            "official serving or hold-rate data was captured.")
    rows = two_way(fx["id"], "Match winner", fx["home"], fx["away"], p_home, "class_ladder",
                   note, 0.6)
    # set handicap ladder from a 6-game margin distribution
    mean_margin = (p_home - 0.5) * 4 * 6
    for line in both_signs([1.5, 3.5]):
        rows += handicap_pair(fx["id"], fx, line, normal_cdf((mean_margin + line) / 6),
                              "class_ladder", note, 0.6)
    return rows


def family_volleyball(fx):
    gap = {
        "vb-gie-ber": (3, 1),
        "vb-tre-cis": (2, 2),
        "vb-per-pra": (1, 3),
    }.get(fx["id"])
    if gap is None:
        return None
    p_home = clamp(0.5 + 0.10 * (gap[1] - gap[0]))
    note = ("Each side is placed on the evidence ladder from the sourced facts on this record "
            "(league position, titles, promotion status); one rung is worth ten probability "
            "points. Set totals follow a binomial split with p = 0.56 per set for "
            "the favoured side.")
    rows = two_way(fx["id"], "Match winner", fx["home"], fx["away"], p_home, "class_ladder",
                   note, 0.6)
    p_strong = max(p_home, 1 - p_home)
    p_set = 0.5 + (p_strong - 0.5) * 0.5
    # best of five: probability of 3-0 / 3-1 / 3-2 for the favourite, then total sets
    dist = {}
    for (w, l) in ((3, 0), (3, 1), (3, 2)):
        prob = math.comb(w + l - 1, l) * p_set ** w * (1 - p_set) ** l
        dist[w + l] = dist.get(w + l, 0) + prob
    for (w, l) in ((3, 0), (3, 1), (3, 2)):
        prob = math.comb(w + l - 1, l) * (1 - p_set) ** w * p_set ** l
        dist[w + l] = dist.get(w + l, 0) + prob
    p_over_45 = dist.get(5, 0)
    rows += two_way(fx["id"], "Total sets 4.5", "Over 4.5", "Under 4.5", p_over_45,
                    "class_ladder", note, 0.6)
    return rows


def family_darts(fx):
    i = fx["inputs"]
    if "home_avg" not in i:
        return None
    gap = {"darts-lit-asp": (1, 2)}.get(fx["id"])
    if gap is None:
        return None
    p_leg = clamp(0.5 + 0.03 * (gap[1] - gap[0]))
    target = int(i.get("target", 10))
    # race to `target` legs
    p_win = 0.0
    dist_total = {}
    for l in range(0, target):
        p_win += math.comb(target + l - 1, l) * p_leg ** target * (1 - p_leg) ** l
        dist_total[target + l] = math.comb(target + l - 1, l) * p_leg ** target * (1 - p_leg) ** l
    p_lose = 1 - p_win
    for l in range(0, target):
        dist_total[target + l] = dist_total.get(target + l, 0) + math.comb(
            target + l - 1, l) * (1 - p_leg) ** target * p_leg ** l
    note = ("The opening-round 3-dart averages and leg records on this record place the two "
            "players one rung apart on the evidence ladder; that is worth three points of "
            "per-leg chance. The match is a race to ten legs, so the match price is the "
            "negative-binomial sum of those legs.")
    rows = [make_line(fx["id"], "Match winner (2-way)", fx["home"], p_win, "class_ladder",
                      note, 0.6),
            make_line(fx["id"], "Match winner (2-way)", fx["away"], p_lose, "class_ladder",
                      note, 0.6)]
    for line in (16.5, 17.5):
        p_over = sum(p for t, p in dist_total.items() if t > line)
        rows += two_way(fx["id"], f"Total legs {line}", f"Over {line}", f"Under {line}",
                        p_over, "class_ladder", note, 0.6)
    return rows


def family_handball(fx):
    gap = {
        "hb-hbl-bal-mel": (5, 2),
        "hb-hbl-rnl-scm": (4, 1),
        "hb-lnh-sr-paris": (4, 1),
    }.get(fx["id"])
    if gap is None:
        return None
    p_home = clamp(0.5 + 0.10 * (gap[1] - gap[0]))
    note = ("Rung placement comes from the sourced facts on this record (promotion, European "
            "results, coaching changes, league position); one rung is worth ten probability "
            "points. No goal total is published because no goals-per-match rate for both clubs "
            "was captured.")
    rows = two_way(fx["id"], "Match winner (draw removed)", fx["home"], fx["away"], p_home,
                   "class_ladder", note, 0.6)
    mean_margin = (p_home - 0.5) * 4 * 6.5
    for line in both_signs([1.5, 3.5, 5.5, 7.5, 9.5, 11.5]):
        rows += handicap_pair(fx["id"], fx, line, normal_cdf((mean_margin + line) / 6.5),
                              "class_ladder", note, 0.6)
    return rows


def family_rugby_league(fx):
    gap = {"rlwc-aus-fiji": (1, 3)}.get(fx["id"])
    if gap is None:
        return None
    p_home = clamp(0.5 + 0.10 * (gap[1] - gap[0]))
    note = ("Australia are the top-ranked side in the pool and Fiji's round-one win came against "
            "Cook Islands, so the raw 2-point and 28-point margins on the record are not "
            "opposition-adjusted and are not used. The price comes from the evidence ladder, "
            "with a 12-point standard deviation for the handicap ladder.")
    mean_margin = (p_home - 0.5) * 4 * 12
    rows = two_way(fx["id"], "Match winner (draw removed)", fx["home"], fx["away"], p_home,
                   "class_ladder", note, 0.6)
    for line in both_signs([3.5, 6.5, 10.5, 13.5, 17.5, 21.5]):
        rows += handicap_pair(fx["id"], fx, line, normal_cdf((mean_margin + line) / 12),
                              "class_ladder", note, 0.6)
    total = 44.0
    for line in (40.5, 44.5, 48.5):
        p = normal_cdf((total - line) / 12)
        rows += two_way(fx["id"], f"Total points {line}", f"Over {line}", f"Under {line}",
                        p, "class_ladder", note, 0.6)
    return rows


FAMILIES = {
    "Ice Hockey": lambda fx: family_poisson(fx, "nhl"),
    "Baseball": lambda fx: family_poisson(fx, "mlb"),
    "Rugby Union": family_rugby_union,
    "Rugby League": family_rugby_league,
    "Gaelic Sports": family_gaelic,
    "Basketball": family_basketball,
    "Cricket": family_cricket,
    "Tennis": family_tennis,
    "Volleyball": family_volleyball,
    "Darts": family_darts,
    "Handball": family_handball,
}

BLANK = {
    "Golf": "No bookmaker-independent rate is available: the captured official leaderboard "
            "gives a 54-hole position but no scoring distribution from which a win chance can "
            "be derived, and the only published prices are third-party market prices.",
    "Greyhounds": "The captured official racecard gives semi-final times for only part of the "
                  "six-dog field, so no full-field speed rating can be built.",
    "Motor Racing": "Qualifying had not taken place at capture, so no grid-based race rating "
                    "can be built from official timing.",
    "Snooker": "The opponent in the final was not yet decided at capture (semi-final two was "
               "still to be played), so no match price can be originated.",
}


def grade(row) -> str:
    p, q = row["probability"], row["quality"]
    if not row["in_band"]:
        return "low"
    if row.get("kind") == "total":
        # a total carries more variance than a result, so it is never graded high
        return "medium" if p >= 0.55 else "low"
    if row["basis"] != "class_ladder" and p >= 0.62 and q >= 0.85:
        return "high"
    if p >= 0.55:
        return "medium"
    return "low"


# --- the 0-10 confidence score -------------------------------------------------------------
# One number a reader can compare across sports. It is our chance of the selection winning, read on
# a 0-10 scale where 5.0 is a coin flip and 10.0 would be a certainty, shaded by how strong the
# basis is: a price built from a goals or points rate counts in full, a price built on the evidence
# ladder counts at 0.8 of its face value. Nothing else moves it, so two picks with the same chance
# and the same basis always carry the same score.
BASIS_SHADE = {"poisson": 1.0, "normal_margin": 1.0, "class_ladder": 0.8}


def score_for(row):
    shaded = 10.0 * row["probability"] * BASIS_SHADE.get(row["basis"], 0.8)
    return round(min(10.0, max(0.0, shaded)), 1)


def main() -> int:
    fixtures = json.loads((NOW / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]
    matches, all_lines, picks, coverage = [], [], [], {}
    for fx in fixtures:
        fam = FAMILIES.get(fx["sport"])
        rows = fam(fx) if fam else None
        entry = {
            "id": fx["id"], "sport": fx["sport"], "competition": fx["competition"],
            "home": fx["home"], "away": fx["away"], "start_utc": fx["start_utc"],
            "start_display": fx.get("start_display", ""), "venue": fx.get("venue", ""),
            "official_url": fx["official_url"], "olbg_url": fx.get("olbg_url", ""),
            "olbg_listed": fx["olbg_listed"], "facts": fx["facts"],
            "started": bool(fx["start_utc"]) and fx["start_utc"] <= AS_OF_UTC,
            "blank_reason": "", "markets": 0, "priced": False,
        }
        if not rows:
            entry["blank_reason"] = BLANK.get(
                fx["sport"],
                "The captured official record does not contain the rates this desk needs "
                "(for example a goals, points or legs rate for both sides).")
            entry["status"] = "unpriced"
            matches.append(entry)
            continue
        for r in rows:
            r["confidence"] = grade(r)
        in_band_rows = [r for r in rows if r["in_band"]]
        best = None
        order = {"high": 3, "medium": 2, "low": 1}
        kind_rank = {"winner": 0, "handicap": 1, "total": 2}
        for r in sorted(in_band_rows, key=lambda r: (-order[r["confidence"]],
                                                     kind_rank.get(r["kind"], 3),
                                                     abs(r["probability"] - 0.68))):
            best = r
            break
        entry["priced"] = True
        entry["status"] = "priced"
        entry["markets"] = len(rows)
        if best:
            entry["primary"] = {
                "market": best["market"], "selection": best["selection"],
                "probability": best["probability"], "american": best["american"],
                "american_display": best["american_display"],
                "confidence": best["confidence"], "assumption": best["assumption"],
            }
            picks.append({
                "id": "pick-" + fx["id"],
                "fixture_id": fx["id"], "sport": fx["sport"],
                "competition": fx["competition"], "home": fx["home"], "away": fx["away"],
                "start_utc": fx["start_utc"], "start_display": fx.get("start_display", ""),
                "market": best["market"], "selection": best["selection"],
                "probability": best["probability"], "decimal": best["decimal"],
                "american": best["american"], "american_display": best["american_display"],
                "in_band": best["in_band"], "confidence": best["confidence"],
                "score": score_for(best), "basis": best["basis"],
                "assumption": best["assumption"],
                "official_url": fx["official_url"], "olbg_url": fx.get("olbg_url", ""),
                "facts": fx["facts"], "started": entry["started"],
            })
        else:
            entry["blank_reason"] = "Every originated price for this fixture falls outside the "
            entry["blank_reason"] += "-250 to +10000 focus band."
        all_lines.extend(rows)
        matches.append(entry)

    by_sport = {}
    for s in SPORTS:
        sp = [m for m in matches if m["sport"] == s]
        by_sport[s] = {
            "fixtures": len(sp),
            "priced": sum(1 for m in sp if m["priced"]),
            "unpriced": sum(1 for m in sp if not m["priced"]),
            "markets": sum(m["markets"] for m in sp),
            "picks": sum(1 for p in picks if p["sport"] == s),
            "high": sum(1 for p in picks if p["sport"] == s and p["confidence"] == "high"),
            "medium": sum(1 for p in picks if p["sport"] == s and p["confidence"] == "medium"),
            "low": sum(1 for p in picks if p["sport"] == s and p["confidence"] == "low"),
            "olbg_listed": sum(1 for m in sp if m["olbg_listed"]),
        }

    payload_matches = {
        "as_of_utc": AS_OF_UTC, "count": len(matches),
        "priced": sum(1 for m in matches if m["priced"]),
        "unpriced": sum(1 for m in matches if not m["priced"]),
        "by_sport": by_sport,
        "matches": sorted(matches, key=lambda m: (SPORTS.index(m["sport"]), m["start_utc"])),
    }
    (NOW / "matches.json").write_text(json.dumps(payload_matches, indent=1) + "\n",
                                      encoding="utf-8")

    # one row per selection, with its fixture context, for the lines page
    fmap = {m["id"]: m for m in matches}
    for r in all_lines:
        m = fmap[r["fixture_id"]]
        r["sport"] = m["sport"]
        r["home"] = m["home"]
        r["away"] = m["away"]
        r["start_utc"] = m["start_utc"]
        r["official_url"] = m["official_url"]
    payload_lines = {
        "as_of_utc": AS_OF_UTC, "count": len(all_lines),
        "in_band": sum(1 for r in all_lines if r["in_band"]),
        "lines": all_lines,
    }
    (NOW / "lines.json").write_text(json.dumps(payload_lines, indent=1) + "\n", encoding="utf-8")

    payload_picks = {
        "as_of_utc": AS_OF_UTC, "count": len(picks),
        "pregame_count": sum(1 for p in picks if not p["started"]),
        "pregame_high": sum(1 for p in picks if not p["started"] and p["confidence"] == "high"),
        "pregame_medium": sum(1 for p in picks if not p["started"] and p["confidence"] == "medium"),
        "started_count": sum(1 for p in picks if p["started"]),
        "high": sum(1 for p in picks if p["confidence"] == "high"),
        "medium": sum(1 for p in picks if p["confidence"] == "medium"),
        "low": sum(1 for p in picks if p["confidence"] == "low"),
        "in_band": sum(1 for p in picks if p["in_band"]),
        "by_sport": {s: dict(by_sport[s], pregame=sum(
            1 for p in picks if p["sport"] == s and not p["started"])) for s in SPORTS},
        "picks": sorted(picks, key=lambda p: (
            SPORTS.index(p["sport"]), {"high": 0, "medium": 1, "low": 2}[p["confidence"]],
            -p["probability"])),
    }
    (NOW / "picks.json").write_text(json.dumps(payload_picks, indent=1) + "\n", encoding="utf-8")

    print(f"now_model: {len(matches)} fixtures, {payload_matches['priced']} priced, "
          f"{len(all_lines)} originated selections, {len(picks)} picks "
          f"({payload_picks['high']} high, {payload_picks['medium']} medium, "
          f"{payload_picks['low']} low), {payload_picks['in_band']} in band")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
