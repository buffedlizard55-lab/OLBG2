#!/usr/bin/env python3
"""Originate independent prices and select the five strongest picks per sport.

Only official inputs stored by today_seed.py are used.  A blank input stays blank;
there is no fallback to bookmaker prices or another dashboard.
"""
from __future__ import annotations

import json
import math
from itertools import permutations
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
SELECTION_CUTOFF = "2026-10-24T18:25:00Z"
HIGH = 0.70
MEDIUM = 0.55


def american(p):
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)


def record_parts(record):
    return [int(x) for x in record.split("-")]


def points_pct(record, sport):
    nums = record_parts(record)
    if sport in ("Ice Hockey", "Handball"):
        w, l, o = nums
        return (2 * w + o) / (2 * (w + l + o))
    w, l = nums[:2]
    return w / (w + l)


def moneyline_probability(fixture):
    sport = fixture["sport"]
    if sport == "Basketball":
        # The completed 2025-26 record supplies the prior.  Current 2026-27
        # results are added as played, with five wins and five losses of shrinkage
        # toward .500 so one or two games cannot dominate an 82-game prior.
        strengths = []
        for side in ("home", "away"):
            pw, pl = record_parts(fixture[f"prior_{side}_record"])[:2]
            cw, cl = record_parts(fixture[f"{side}_record"])[:2]
            strengths.append((pw + cw + 5) / (pw + pl + cw + cl + 10))
        p_home = 0.5 + 0.04 + 0.85 * (strengths[0] - strengths[1])
    elif sport == "Tennis":
        data = fixture["tennis"]
        strengths = []
        if data["basis"] == "season":
            for side in ("home", "away"):
                wins, losses = data[f"{side}_season"]
                strengths.append((wins + 5) / (wins + losses + 10))
        else:
            # Osaka has no comparable official season record for both players.
            # Use only the current tournament, with four matches and twelve sets
            # of .500 shrinkage; unfinished sets in retirements are excluded.
            for side in ("home", "away"):
                wins, losses = record_parts(fixture[f"{side}_record"])
                sets_for, sets_against = data[f"{side}_sets"]
                match_strength = (wins + 2) / (wins + losses + 4)
                set_strength = (sets_for + 6) / (sets_for + sets_against + 12)
                strengths.append(0.65 * match_strength + 0.35 * set_strength)
        p_home = 0.5 + 0.85 * (strengths[0] - strengths[1])
    elif sport == "Volleyball":
        strengths = []
        for side in ("home", "away"):
            row = fixture["volleyball"][side]
            games = row["wins"] + row["losses"]
            win_strength = (row["wins"] + 2) / (games + 4)
            set_strength = (row["sets_for"] + 6) / (row["sets_for"] + row["sets_against"] + 12)
            point_strength = (row["points_for"] + 300) / (row["points_for"] + row["points_against"] + 600)
            strengths.append(0.60 * win_strength + 0.25 * set_strength + 0.15 * point_strength)
        p_home = 0.5 + 0.035 + 0.85 * (strengths[0] - strengths[1])
    else:
        home = points_pct(fixture["home_record"], sport)
        away = points_pct(fixture["away_record"], sport)
        edge = 0.045 if sport == "Ice Hockey" else 0.04
        p_home = 0.5 + edge + 0.85 * (home - away)
    return max(0.12, min(0.88, p_home))


def market_probability(fixture):
    if fixture.get("market_decimal_home") and fixture.get("market_decimal_away"):
        h = 1 / fixture["market_decimal_home"]
        a = 1 / fixture["market_decimal_away"]
        return h / (h + a)
    return None


def poisson(rate, k):
    return math.exp(-rate) * rate ** k / math.factorial(k)


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def match_from_set_probability(set_probability, best_of):
    q, r = set_probability, 1 - set_probability
    if best_of == 3:
        return q ** 2 + 2 * q ** 2 * r
    return q ** 3 + 3 * q ** 3 * r + 6 * q ** 3 * r ** 2


def set_from_match_probability(match_probability, best_of):
    lo, hi = 0.001, 0.999
    for _ in range(80):
        mid = (lo + hi) / 2
        if match_from_set_probability(mid, best_of) < match_probability:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def handball_two_way_probability(fixture):
    strengths = []
    for side in ("home", "away"):
        row = fixture["handball"][side]
        points = 2 * row["wins"] + row["draws"]
        strengths.append((points + 5) / (2 * (row["gp"] + 5)))
    return max(0.12, min(0.88, 0.5 + 0.04 + 0.85 * (strengths[0] - strengths[1])))


def score_matrix(home_rate, away_rate, maximum=18):
    home = [poisson(home_rate, k) for k in range(maximum + 1)]
    away = [poisson(away_rate, k) for k in range(maximum + 1)]
    matrix = [(h, a, home[h] * away[a]) for h in range(maximum + 1) for a in range(maximum + 1)]
    total = sum(p for _, _, p in matrix)
    return [(h, a, p / total) for h, a, p in matrix]


def darts_outcomes(leg_probability):
    """Exact first-to-ten score distribution, including the winning final leg."""
    q, r = leg_probability, 1 - leg_probability
    outcomes = []
    for loser_legs in range(10):
        sequences = math.comb(9 + loser_legs, loser_legs)
        outcomes.append((10, loser_legs, sequences * q ** 10 * r ** loser_legs))
        outcomes.append((loser_legs, 10, sequences * r ** 10 * q ** loser_legs))
    return outcomes


def expand_fixtures():
    return json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))["fixtures"]


def build():
    fixtures = expand_fixtures()
    olbg = json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))
    event_urls = {r["event_id"]: r["url"] for r in olbg["listings"]}
    lines = []
    candidates = []

    def add_line(fixture, market, selection, probability, source_url, method,
                 line=None, market_home=None):
        probability = round(max(0.001, min(0.999, probability)), 4)
        fair = american(probability)
        lines.append(dict(
            id=f"{fixture['id']}:{market}:{selection}:{line}",
            fixture_id=fixture["id"], sport=fixture["sport"], market=market,
            selection=selection, line=line, probability=probability,
            fair_american=fair, fair_decimal=round(1 / probability, 3),
            source_url=source_url,
            source_urls=fixture.get("pricing_source_urls", [source_url]), method=method,
            market_implied_home=market_home,
        ))
        return lines[-1]

    for fixture in fixtures:
        sport = fixture["sport"]
        if sport not in ("Ice Hockey", "Baseball", "Basketball", "Tennis", "Volleyball", "Handball", "Motor Racing", "Darts"):
            continue
        implied = market_probability(fixture)
        input_source = fixture.get("stats_source_url", fixture["source_url"])
        moneyline_choices = []
        if sport == "Darts":
            data = fixture["darts"]
            home, away = data["home"], data["away"]
            logit = (0.08 * math.log(home["world_money"] / away["world_money"])
                     + 0.06 * math.log(home["et_money"] / away["et_money"])
                     + 0.035 * ((home["legs_won"] - home["legs_lost"])
                                - (away["legs_won"] - away["legs_lost"])))
            q = 1 / (1 + math.exp(-logit))
            outcomes = darts_outcomes(q)
            method = "official ranking-earning log ratios and tournament leg differential; exact best-of-19 distribution"
            home_line = add_line(fixture, "Moneyline", fixture["home"],
                                 sum(p for h, a, p in outcomes if h == 10), input_source, method,
                                 market_home=implied)
            moneyline_choices.append(home_line)
            moneyline_choices.append(add_line(
                fixture, "Moneyline", fixture["away"],
                sum(p for h, a, p in outcomes if a == 10), input_source,
                "complement within exact best-of-19 distribution"))
            home_minus = sum(p for h, a, p in outcomes if h - a >= 3)
            away_minus = sum(p for h, a, p in outcomes if a - h >= 3)
            add_line(fixture, "Leg handicap", fixture["home"], home_minus, input_source,
                     "exact best-of-19 margin; home -2.5 legs", line=-2.5)
            add_line(fixture, "Leg handicap", fixture["away"], 1 - home_minus, input_source,
                     "complement of home -2.5; away +2.5", line=2.5)
            add_line(fixture, "Leg handicap", fixture["away"], away_minus, input_source,
                     "exact best-of-19 margin; away -2.5 legs", line=-2.5)
            add_line(fixture, "Leg handicap", fixture["home"], 1 - away_minus, input_source,
                     "complement of away -2.5; home +2.5", line=2.5)
            under = sum(p for h, a, p in outcomes if h + a <= 16)
            add_line(fixture, "Total legs", "Under", under, input_source,
                     "exact best-of-19 score distribution", line=16.5)
            add_line(fixture, "Total legs", "Over", 1 - under, input_source,
                     "complement of under 16.5 legs", line=16.5)
            fixture["leg_probability_home"] = round(q, 6)
            fixture["expected_legs"] = round(sum((h + a) * p for h, a, p in outcomes), 4)
            fixture["darts_weight_method"] = "logit = 0.08 ln(world earnings ratio) + 0.06 ln(European Tour earnings ratio) + 0.035 leg-differential difference"
        elif sport == "Motor Racing":
            drivers = fixture["motor"]["drivers"]
            maximum_points = max(row["points"] for row in drivers)
            maximum_wins = max(row["wins"] for row in drivers)
            weights = []
            for row in drivers:
                points_base = 0.15 + row["points"] / maximum_points
                win_factor = 1 + row["wins"] / maximum_wins
                practice_factor = 1 / (1 + row["fp2_gap"])
                weights.append(points_base * win_factor * practice_factor)
            total_weight = sum(weights)
            winner_probabilities = [weight / total_weight for weight in weights]
            for row, probability in zip(drivers, winner_probabilities):
                moneyline_choices.append(add_line(
                    fixture, "Race winner", row["name"], probability, input_source,
                    "normalized points base × season-win factor × Practice 2 gap factor; no qualifying input"))

            # Exact Plackett-Luce top-three inclusion. Enumerating 22×21×20
            # ordered podiums is small and avoids a simulated or approximate price.
            podium = [0.0] * len(drivers)
            for first, second, third in permutations(range(len(drivers)), 3):
                probability = (weights[first] / total_weight
                               * weights[second] / (total_weight - weights[first])
                               * weights[third] / (total_weight - weights[first] - weights[second]))
                podium[first] += probability
                podium[second] += probability
                podium[third] += probability
            for row, probability in zip(drivers, podium):
                add_line(fixture, "Podium finish", f"{row['name']} — Yes", probability,
                         input_source, "exact enumeration of every ordered top-three outcome")
                add_line(fixture, "Podium finish", f"{row['name']} — No", 1 - probability,
                         input_source, "complement of exact podium probability")
            fixture["race_weight_method"] = "0.15 + points/max points; × (1 + wins/max wins); × 1/(1 + FP2 gap seconds)"
        elif sport == "Handball":
            # Scoring supplies the total; official W-L-D records calibrate the
            # margin. Independent Poisson goals then produce all three regular-
            # time outcomes, including the tie, without discarding draw mass.
            p_two_way = handball_two_way_probability(fixture)
            rates = {}
            for side in ("home", "away"):
                row = fixture["handball"][side]
                rates[side] = dict(
                    attack=(row["goals_for"] + 150) / (row["gp"] + 5),
                    defence=(row["goals_against"] + 150) / (row["gp"] + 5),
                )
            expected_total = ((rates["home"]["attack"] + rates["away"]["defence"]) / 2
                              + (rates["away"]["attack"] + rates["home"]["defence"]) / 2)
            margin = 7.0 * NormalDist().inv_cdf(p_two_way)
            home_rate = max(1.0, (expected_total + margin) / 2)
            away_rate = max(1.0, (expected_total - margin) / 2)
            matrix = score_matrix(home_rate, away_rate, maximum=60)
            p_home = sum(p for h, a, p in matrix if h > a)
            p_draw = sum(p for h, a, p in matrix if h == a)
            p_away = sum(p for h, a, p in matrix if h < a)
            home_line = add_line(fixture, "Moneyline", fixture["home"], p_home,
                                 input_source, "W-L-D calibrated Poisson regular-time result",
                                 market_home=implied)
            moneyline_choices.append(home_line)
            moneyline_choices.append(add_line(fixture, "Moneyline", fixture["away"], p_away,
                                              input_source, "W-L-D calibrated Poisson regular-time result"))
            moneyline_choices.append(add_line(fixture, "Moneyline", "Tie", p_draw,
                                              input_source, "Poisson probability of equal regular-time goals"))
            spread_magnitude = math.floor(abs(margin)) + 0.5
            home_spread = -spread_magnitude if margin >= 0 else spread_magnitude
            home_cover = sum(p for h, a, p in matrix if h + home_spread > a)
            add_line(fixture, "Match handicap", fixture["home"], home_cover, input_source,
                     "Poisson goal-difference matrix; half-goal handicap", line=home_spread)
            add_line(fixture, "Match handicap", fixture["away"], 1 - home_cover, input_source,
                     "complement of home handicap", line=-home_spread)
            total_line = math.floor(expected_total) + 0.5
            under = sum(poisson(expected_total, k) for k in range(math.floor(total_line) + 1))
            add_line(fixture, "Total goals", "Under", under, input_source,
                     "Poisson total from official GF/GA rates", line=total_line)
            add_line(fixture, "Total goals", "Over", 1 - under, input_source,
                     "complement of under probability", line=total_line)
            fixture["expected_goals"] = dict(home=round(home_rate, 3), away=round(away_rate, 3))
        else:
            p_home = round(moneyline_probability(fixture), 4)
            p_away = round(1 - p_home, 4)
            home_line = add_line(fixture, "Moneyline", fixture["home"], p_home,
                                 input_source, "official record strength plus fixed home edge where applicable",
                                 market_home=implied)
            moneyline_choices.append(home_line)
            moneyline_choices.append(add_line(fixture, "Moneyline", fixture["away"], p_away,
                                              input_source, "complement of home moneyline probability"))

        if sport == "Ice Hockey":
            stats = fixture["nhl"]
            # Five league-average games of shrinkage temper the early-season
            # scoring rates.  A 0.15-goal home adjustment is applied once.
            shrunk = {}
            for side in ("home", "away"):
                row = stats[side]
                shrunk[side] = dict(
                    attack=(row["goals_for"] + 15) / (row["gp"] + 5),
                    defence=(row["goals_against"] + 15) / (row["gp"] + 5),
                )
            home_rate = (shrunk["home"]["attack"] + shrunk["away"]["defence"]) / 2 + 0.15
            away_rate = (shrunk["away"]["attack"] + shrunk["home"]["defence"]) / 2
            matrix = score_matrix(home_rate, away_rate)
            source = stats["source_url"]
            home_minus = sum(p for h, a, p in matrix if h - a >= 2)
            away_minus = sum(p for h, a, p in matrix if a - h >= 2)
            add_line(fixture, "Puck line", fixture["home"], home_minus, source,
                     "independent Poisson goal matrix; home -1.5", line=-1.5)
            add_line(fixture, "Puck line", fixture["away"], 1 - home_minus, source,
                     "complement of home -1.5; away +1.5", line=1.5)
            add_line(fixture, "Puck line", fixture["away"], away_minus, source,
                     "independent Poisson goal matrix; away -1.5", line=-1.5)
            add_line(fixture, "Puck line", fixture["home"], 1 - away_minus, source,
                     "complement of away -1.5; home +1.5", line=1.5)
            total_rate = home_rate + away_rate
            for total in (5.5, 6.5):
                under = sum(poisson(total_rate, k) for k in range(math.floor(total) + 1))
                add_line(fixture, "Total goals", "Under", under, source,
                         "Poisson total from official GF/GA rates", line=total)
                add_line(fixture, "Total goals", "Over", 1 - under, source,
                         "complement of under probability", line=total)
            fixture["expected_goals"] = dict(home=round(home_rate, 3), away=round(away_rate, 3))

        elif sport == "Baseball":
            runs = fixture["runs"]
            games = runs["games"]
            home_rate = ((runs["home_scored"] + runs["away_allowed"]) / games / 2) + 0.15
            away_rate = ((runs["away_scored"] + runs["home_allowed"]) / games / 2) - 0.15
            matrix = score_matrix(home_rate, away_rate)
            home_minus = sum(p for h, a, p in matrix if h - a >= 2)
            away_minus = sum(p for h, a, p in matrix if a - h >= 2)
            add_line(fixture, "Run line", fixture["home"], home_minus, fixture["source_url"],
                     "independent Poisson run matrix; home -1.5", line=-1.5)
            add_line(fixture, "Run line", fixture["away"], 1 - home_minus, fixture["source_url"],
                     "complement of home -1.5; away +1.5", line=1.5)
            add_line(fixture, "Run line", fixture["away"], away_minus, fixture["source_url"],
                     "independent Poisson run matrix; away -1.5", line=-1.5)
            add_line(fixture, "Run line", fixture["home"], 1 - away_minus, fixture["source_url"],
                     "complement of away -1.5; home +1.5", line=1.5)
            total_rate = home_rate + away_rate
            for total in (7.5, 8.5):
                under = sum(poisson(total_rate, k) for k in range(math.floor(total) + 1))
                add_line(fixture, "Total runs", "Under", under, fixture["source_url"],
                         "Poisson total from official season runs", line=total)
                add_line(fixture, "Total runs", "Over", 1 - under, fixture["source_url"],
                         "complement of under probability", line=total)
            fixture["expected_runs"] = dict(home=round(home_rate, 3), away=round(away_rate, 3))

        elif sport == "Basketball":
            nba = fixture["nba"]
            rates = {}
            for side in ("home", "away"):
                row = nba[side]
                gp = row["gp"]
                # Ten league-average games of scoring shrinkage.  Allowed points
                # are derived only from the two official columns PTS and +/-.
                attack = (gp * row["points_per_game"] + 10 * 114.0) / (gp + 10)
                differential = gp * row["point_differential"] / (gp + 10)
                rates[side] = dict(attack=attack, allowed=attack - differential)
            scoring_home = (rates["home"]["attack"] + rates["away"]["allowed"]) / 2 + 1.5
            scoring_away = (rates["away"]["attack"] + rates["home"]["allowed"]) / 2 - 1.5
            expected_total = scoring_home + scoring_away
            # Keep the spread coherent with the official-record moneyline instead
            # of allowing a two-game scoring differential to reverse the favourite.
            margin = 12.0 * NormalDist().inv_cdf(p_home)
            home_points = (expected_total + margin) / 2
            away_points = (expected_total - margin) / 2
            spread_magnitude = math.floor(abs(margin)) + 0.5
            home_spread = -spread_magnitude if margin >= 0 else spread_magnitude
            # Every spread is a half-point line, so there is no push branch.
            z = (-home_spread - margin) / 12.0
            home_cover = 1 - normal_cdf(z)
            add_line(fixture, "Point spread", fixture["home"], home_cover, fixture["source_url"],
                     "moneyline-calibrated normal margin distribution (SD 12)", line=home_spread)
            add_line(fixture, "Point spread", fixture["away"], 1 - home_cover, fixture["source_url"],
                     "complement of home spread cover", line=-home_spread)
            total_line = math.floor(expected_total) + 0.5
            over = 1 - normal_cdf((total_line - expected_total) / 18.0)
            add_line(fixture, "Total points", "Over", over, nba["source_url"],
                     "normal total distribution (SD 18); official PTS and +/-", line=total_line)
            add_line(fixture, "Total points", "Under", 1 - over, nba["source_url"],
                     "complement of over probability", line=total_line)
            fixture["expected_points"] = dict(home=round(home_points, 2), away=round(away_points, 2))

        elif sport in ("Tennis", "Volleyball"):
            best_of = 3 if sport == "Tennis" else 5
            q = set_from_match_probability(p_home, best_of)
            r = 1 - q
            market_name = "Set handicap"
            if best_of == 3:
                home_minus = q ** 2
                away_minus = r ** 2
            else:
                home_minus = q ** 3 * (4 - 3 * q)
                away_minus = r ** 3 * (4 - 3 * r)
            add_line(fixture, market_name, fixture["home"], home_minus, input_source,
                     f"best-of-{best_of} independent set distribution; home -1.5 sets", line=-1.5)
            add_line(fixture, market_name, fixture["away"], 1 - home_minus, input_source,
                     "complement of home -1.5 sets; away +1.5", line=1.5)
            add_line(fixture, market_name, fixture["away"], away_minus, input_source,
                     f"best-of-{best_of} independent set distribution; away -1.5 sets", line=-1.5)
            add_line(fixture, market_name, fixture["home"], 1 - away_minus, input_source,
                     "complement of away -1.5 sets; home +1.5", line=1.5)
            totals = (2.5,) if best_of == 3 else (3.5, 4.5)
            for total in totals:
                if total == 2.5:
                    over = 2 * q * r
                elif total == 3.5:
                    over = 1 - q ** 3 - r ** 3
                else:
                    over = 6 * q ** 2 * r ** 2
                add_line(fixture, "Total sets", "Over", over, input_source,
                         f"exact best-of-{best_of} set-score distribution", line=total)
                add_line(fixture, "Total sets", "Under", 1 - over, input_source,
                         "complement of over probability", line=total)

        if fixture["start_utc"] > SELECTION_CUTOFF and fixture.get("olbg_event_id"):
            chosen = max(moneyline_choices, key=lambda line: line["probability"])
            candidates.append(dict(
                fixture_id=fixture["id"], line_id=chosen["id"], sport=sport,
                competition=fixture["competition"], event_name=fixture.get("event_name"),
                home=fixture["home"], away=fixture["away"],
                start_utc=fixture["start_utc"], start_display=fixture.get("start_display"),
                selection=chosen["selection"],
                market=chosen["market"], line=chosen["line"], probability=chosen["probability"],
                fair_american=chosen["fair_american"], fair_decimal=chosen["fair_decimal"],
                confidence="high" if chosen["probability"] >= HIGH else
                           ("medium" if chosen["probability"] >= MEDIUM else "low"),
                in_band=-250 <= chosen["fair_american"] <= 10000,
                source_url=fixture["source_url"], stats_source_url=fixture.get("stats_source_url"),
                olbg_event_id=fixture.get("olbg_event_id"),
                olbg_event_url=event_urls.get(fixture.get("olbg_event_id")),
                olbg_listed_selection=fixture.get("olbg_listed_selection"),
                olbg_market=fixture.get("olbg_market"),
                home_record=fixture["home_record"], away_record=fixture["away_record"],
                fact_home=fixture["fact_home"], fact_away=fixture["fact_away"],
            ))

    def rank(pick):
        grade = {"high": 0, "medium": 1, "low": 2}[pick["confidence"]]
        return grade, not pick["in_band"], -pick["probability"], pick["start_utc"]

    picks = []
    for sport in sorted({p["sport"] for p in candidates}):
        sport_picks = sorted((p for p in candidates if p["sport"] == sport), key=rank)
        picks.extend(sport_picks[:5])
    picks.sort(key=rank)

    (DATA / "lines.json").write_text(json.dumps(dict(
        generated_utc=olbg["capture_end_utc"], selection_cutoff_utc=SELECTION_CUTOFF,
        high_threshold=HIGH, medium_threshold=MEDIUM,
        method="official-record moneylines; Poisson NHL/MLB/handball scoring; shrunk NBA scoring; exact tennis/volleyball set and darts leg distributions; normalized F1 winner and exact podium markets",
        lines=lines, count=len(lines),
    ), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "picks.json").write_text(json.dumps(dict(
        generated_utc=olbg["capture_end_utc"], selection_cutoff_utc=SELECTION_CUTOFF,
        picks=picks, count=len(picks),
    ), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"today_model: {len(lines)} prices, {len(picks)} picks; High >= {HIGH:.0%}")


if __name__ == "__main__":
    build()
