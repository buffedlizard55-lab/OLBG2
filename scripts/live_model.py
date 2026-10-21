#!/usr/bin/env python3
"""Originate betting lines for the Layer-4 live slate (session arena/d4b9d560-olbg2).

Inputs : data/live/urc.json, data/live/mlb.json, data/live/predictions.json
Outputs: data/live/lines.json

Every input value comes from an official source captured in this session; the URLs
travel with the data. Nothing here reads the network and nothing is inferred from
memory. Two models are used, both parameterised only by numbers that appear in the
captured official data:

* Rugby union - normal model on the scoring margin. Expected points are built from
  the official league table (points for / against per game, scaled by the league
  average), shifted by the home advantage observed in the official Round 3 results.
  The margin and total spreads are the sample standard deviations of those same
  Round 3 results (n=8, disclosed as a small sample).
* Baseball - independent Poisson model on runs. Run rates come from the official
  regular-season standings (runs scored / allowed over 162 games) and are rescaled
  by the two finalists' own average run environment, so no league-wide constant that
  was not captured has to be assumed. Ties are split 50/50 as extra innings.

Odds are fair prices divided by (1 + overround); the overround is disclosed per row.
"""
from __future__ import annotations

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, "data", "live")
OVERROUND = 0.04
MAX_GOALS = 25


# ----------------------------------------------------------------------------- maths
def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


def sample_sd(values):
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(var), mean


def american(decimal: float) -> str:
    if decimal >= 2.0:
        return "+%d" % round((decimal - 1.0) * 100)
    return "%d" % round(-100.0 / (decimal - 1.0))


def price(prob: float) -> dict:
    decimal = 1.0 / (prob * (1.0 + OVERROUND))
    return {"probability": round(prob, 4), "decimal": round(decimal, 2), "american": american(decimal)}


# ----------------------------------------------------------------------------- rugby
def urc_rows():
    src = json.load(open(os.path.join(LIVE, "urc.json")))
    table, fixtures = src["table"], src["fixtures"]
    played = src["round3_results"]["played"]

    for_per_game = {c: t["pf"] / t["pl"] for c, t in table.items()}
    against_per_game = {c: t["pa"] / t["pl"] for c, t in table.items()}
    league_avg = sum(for_per_game.values()) / len(for_per_game)

    margins = [g["hs"] - g["as"] for g in played]
    totals = [g["hs"] + g["as"] for g in played]
    margin_sd, margin_mean = sample_sd(margins)
    total_sd, _ = sample_sd(totals)
    home_adv = (sum(g["hs"] for g in played) - sum(g["as"] for g in played)) / len(played)
    draws_played = sum(t["d"] for t in table.values()) / 2.0
    games_played = sum(t["pl"] for t in table.values()) / 2.0
    draw_rate = draws_played / games_played

    rows = []
    for fx in fixtures:
        home, away = fx["home"], fx["away"]
        # The observed home advantage is split evenly so that it moves the margin by the
        # full measured amount without inflating the expected total.
        exp_home = for_per_game[home] * (against_per_game[away] / league_avg) + home_adv / 2.0
        exp_away = for_per_game[away] * (against_per_game[home] / league_avg) - home_adv / 2.0
        margin = exp_home - exp_away

        # Draw probability is the season rate observed in the official table; the rest
        # of the mass is split by the normal model on the margin.
        p_home_raw = norm_cdf(margin / margin_sd)
        p_away_raw = 1.0 - p_home_raw
        p_draw = draw_rate
        p_home = (1.0 - p_draw) * p_home_raw
        p_away = (1.0 - p_draw) * p_away_raw

        exp_total = exp_home + exp_away
        total_line = math.floor(exp_total) + 0.5
        p_over = 1.0 - norm_cdf((total_line - exp_total) / total_sd)

        spread = math.floor(abs(margin)) + 0.5
        if margin >= 0:
            fav, dog, fav_line, dog_line = home, away, -spread, spread
            p_fav_cover = 1.0 - norm_cdf((spread - margin) / margin_sd)
        else:
            fav, dog, fav_line, dog_line = away, home, -spread, spread
            p_fav_cover = 1.0 - norm_cdf((-margin - spread) / margin_sd)

        rows.append(
            {
                "id": fx["id"],
                "sport": "Rugby Union",
                "competition": src["meta"]["competition"],
                "date": fx["date_local"],
                "time": fx["time_local"] + " local",
                "home": home,
                "away": away,
                "home_name": table[home]["name"],
                "away_name": table[away]["name"],
                "venue": fx["venue"],
                "source_url": fx["url"],
                "inputs": {
                    "home": {k: table[home][k] for k in ("pl", "w", "d", "l", "pf", "pa", "pts", "form", "pos")},
                    "away": {k: table[away][k] for k in ("pl", "w", "d", "l", "pf", "pa", "pts", "form", "pos")},
                    "source_url": src["meta"]["table_source"]["url"],
                },
                "model": {
                    "name": "normal margin model",
                    "expected_home_points": round(exp_home, 1),
                    "expected_away_points": round(exp_away, 1),
                    "expected_margin": round(margin, 1),
                    "expected_total": round(exp_total, 1),
                    "margin_sd": round(margin_sd, 2),
                    "total_sd": round(total_sd, 2),
                    "home_advantage_points": round(home_adv, 2),
                    "home_advantage_applied": "+/- half of the measured margin to home/away, so the total is unchanged",
                    "draw_rate": round(draw_rate, 4),
                    "sample": "URC Round 3 results, 8 matches, official match centre",
                },
                "markets": {
                    "match_winner": {
                        "type": "3-way",
                        "options": {
                            home: price(p_home),
                            "draw": price(p_draw),
                            away: price(p_away),
                        },
                    },
                    "handicap": {
                        "type": "handicap",
                        "line": {fav: fav_line, dog: dog_line},
                        "options": {fav: price(p_fav_cover), dog: price(1.0 - p_fav_cover)},
                    },
                    "total": {
                        "type": "total",
                        "line": total_line,
                        "options": {"over": price(p_over), "under": price(1.0 - p_over)},
                    },
                },
            }
        )
    return rows


# ----------------------------------------------------------------------------- baseball
def mlb_rows():
    src = json.load(open(os.path.join(LIVE, "mlb.json")))
    teams, rows = src["teams"], []
    games = sum(t["wins"] + t["losses"] for t in teams.values()) / len(teams)
    # The run environment is the two finalists' own average, so no uncaptured
    # league-wide constant enters the model.
    env = sum(t["runs_scored"] for t in teams.values()) / len(teams) / games

    for fx in src["fixtures"]:
        home, away = teams[fx["home"]], teams[fx["away"]]
        lam_home = (home["runs_scored"] / games) * ((away["runs_allowed"] / games) / env)
        lam_away = (away["runs_scored"] / games) * ((home["runs_allowed"] / games) / env)

        p_home = p_away = p_tie = 0.0
        p_over = {}
        total_line = math.floor(lam_home + lam_away) + 0.5
        for i in range(MAX_GOALS):
            for j in range(MAX_GOALS):
                p = poisson_pmf(i, lam_home) * poisson_pmf(j, lam_away)
                if i > j:
                    p_home += p
                elif j > i:
                    p_away += p
                else:
                    p_tie += p
                if i + j > total_line:
                    p_over[total_line] = p_over.get(total_line, 0.0) + p
        # A tied scoreline goes to extra innings: split it evenly.
        p_home += p_tie / 2.0
        p_away += p_tie / 2.0
        p_over_total = p_over.get(total_line, 0.0)

        run_line = 1.5
        p_home_cover = 0.0
        for i in range(MAX_GOALS):
            for j in range(MAX_GOALS):
                if i - j >= 2:
                    p_home_cover += poisson_pmf(i, lam_home) * poisson_pmf(j, lam_away)
        p_away_cover = 1.0 - p_home_cover
        if p_home >= p_away:
            fav, dog, fav_line, dog_line = fx["home"], fx["away"], -run_line, run_line
            p_fav_cover = p_home_cover
        else:
            fav, dog, fav_line, dog_line = fx["away"], fx["home"], -run_line, run_line
            p_fav_cover = p_away_cover

        rows.append(
            {
                "id": fx["id"],
                "sport": "Baseball",
                "competition": src["meta"]["competition"],
                "date": fx["official_date"],
                "time": fx["game_date_utc"],
                "home": fx["home"],
                "away": fx["away"],
                "home_name": home["name"],
                "away_name": away["name"],
                "venue": fx["venue"],
                "source_url": fx["url"],
                "detail": fx["description"],
                "inputs": {
                    "home": {k: home[k] for k in ("wins", "losses", "runs_scored", "runs_allowed", "division_rank") if k in home},
                    "away": {k: away[k] for k in ("wins", "losses", "runs_scored", "runs_allowed", "division_rank") if k in away},
                    "source_url": src["meta"]["standings_source"]["url"],
                },
                "model": {
                    "name": "independent Poisson runs model",
                    "expected_home_runs": round(lam_home, 3),
                    "expected_away_runs": round(lam_away, 3),
                    "expected_total": round(lam_home + lam_away, 3),
                    "run_environment": round(env, 3),
                    "games": int(games),
                    "tie_handling": "scoreline ties split 50/50 as extra innings",
                    "home_advantage": "not applied - no official MLB home/away split was captured this session",
                },
                "markets": {
                    "match_winner": {
                        "type": "2-way",
                        "options": {fx["home"]: price(p_home), fx["away"]: price(p_away)},
                    },
                    "handicap": {
                        "type": "run line",
                        "line": {fav: fav_line, dog: dog_line},
                        "options": {fav: price(p_fav_cover), dog: price(1.0 - p_fav_cover)},
                    },
                    "total": {
                        "type": "total",
                        "line": total_line,
                        "options": {"over": price(p_over_total), "under": price(1.0 - p_over_total)},
                    },
                },
            }
        )
    return rows


# ----------------------------------------------------------------------------- picks
def confidence(prob: float) -> str:
    if prob >= 0.62:
        return "high"
    if prob >= 0.55:
        return "medium"
    return "low"


def add_picks(rows):
    preds = {}
    path = os.path.join(LIVE, "predictions.json")
    if os.path.exists(path):
        preds = {p["fixture_id"]: p for p in json.load(open(path))["predictions"]}

    for row in rows:
        # The brief asks for a match-winner pick, so the pick is always taken from the
        # match-winner market. Handicap and total prices are published alongside it.
        best_sel, best_prob = None, -1.0
        for sel, priced in row["markets"]["match_winner"]["options"].items():
            if priced["probability"] > best_prob:
                best_sel, best_prob = sel, priced["probability"]
        label = best_sel if best_sel != "draw" else "Draw"
        if best_sel in (row["home"], row["away"]) or best_sel == "draw":
            names = {row["home"]: row["home_name"], row["away"]: row["away_name"], "draw": "Draw"}
            label = names[best_sel] + " to win the match"
        row["pick"] = {
            "market": "match_winner",
            "selection": best_sel,
            "label": label,
            "probability": round(best_prob, 4),
            "decimal": row["markets"]["match_winner"]["options"][best_sel]["decimal"],
            "american": row["markets"]["match_winner"]["options"][best_sel]["american"],
            "confidence": confidence(best_prob),
            "rule": "high >= 0.62, medium 0.55-0.62, low < 0.55 on the model probability of the selection",
        }
        pred = preds.get(row["id"])
        if pred:
            pred = dict(pred)
            pred["words"] = len(pred["text"].split())
        row["prediction"] = pred
    return rows


def main():
    rows = add_picks(urc_rows() + mlb_rows())
    out = {
        "meta": {
            "generated_by": "scripts/live_model.py",
            "session": "arena/d4b9d560-olbg2",
            "overround": OVERROUND,
            "fixtures": len(rows),
            "lines_originated": sum(len(r["markets"]) for r in rows),
            "picks": len([r for r in rows if r.get("pick")]),
            "high_confidence": len([r for r in rows if r["pick"]["confidence"] == "high"]),
        },
        "rows": rows,
    }
    with open(os.path.join(LIVE, "lines.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    m = out["meta"]
    print(
        "live_model: %(fixtures)d fixtures, %(lines_originated)d market lines, "
        "%(picks)d picks (%(high_confidence)d high confidence)" % m
    )
    for row in rows:
        p = row["pick"]
        print(
            "  %-14s %-28s %-14s %-6s p=%.3f %s"
            % (row["id"], (row["away_name"] + " @ " + row["home_name"])[:28], p["label"], p["confidence"], p["probability"], "(no prediction)" if not row["prediction"] else "")
        )


if __name__ == "__main__":
    main()
