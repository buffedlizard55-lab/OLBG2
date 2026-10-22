#!/usr/bin/env python3
"""Originate fair prices for every /atlas/ row that has a verified strength input.

Models (all constants are our own origination; every *input* is read from an
official governing-body capture stored under data/atlas/):

NHL  — multiplicative Poisson on NHL.com standings GF/GA
    w        = gp / (gp + 8)                      empirical-Bayes shrinkage
    attack_i = 1 + w * ((gf_i/gp_i) / L - 1)
    defence_i= 1 + w * ((ga_i/gp_i) / L - 1)
    L        = league goals per team-game from the same table
    lambda_home = L * attack_home * defence_away * H
    lambda_away = L * attack_away * defence_home / H      H = 1.044  (~9% goal ratio)
    moneyline   Poisson grid to 15 goals, tied games split 50/50
    puck line   1.5 goals
    total       the half-goal line whose P(over) is closest to 0.50

MLB  — Pythagorean win expectancy + log5 on official season runs
    pyth_i = RS^1.83 / (RS^1.83 + RA^1.83)        from the verified season totals
    p = log5(pyth_home, pyth_away) shifted by a logit home edge of 0.16
    run line 1.5 runs  Skellam grid on the two Poisson run rates
    total              the half-run line whose P(over) is closest to 0.50

Rows with no verified strength input are published with every price blank and a
written reason. Nothing is inferred, and no bookmaker price is read or compared.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "atlas"

BAND_MIN_DEC = 1.40
BAND_MAX_DEC = 101.00
BAND_MIN_AM = -250
BAND_MAX_AM = 10000

GENERATED_AT = "2026-10-22T13:05:00Z"
SESSION = "arena/ba48a907-olbg2"

# ---------------------------------------------------------------- helpers


def pois(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_grid(lam, n=20):
    return [pois(k, lam) for k in range(n + 1)]


def joint(la, lb, n=20):
    ga, gb = poisson_grid(la, n), poisson_grid(lb, n)
    return [[ga[i] * gb[j] for j in range(n + 1)] for i in range(n + 1)]


def p_win(la, lb, n=20):
    g = joint(la, lb, n)
    ph = sum(g[i][j] for i in range(n + 1) for j in range(n + 1) if i > j)
    pa = sum(g[i][j] for i in range(n + 1) for j in range(n + 1) if j > i)
    pt = 1.0 - ph - pa
    return ph + 0.5 * pt, pa + 0.5 * pt


def p_margin_ge(la, lb, k, n=20):
    g = joint(la, lb, n)
    return sum(g[i][j] for i in range(n + 1) for j in range(n + 1) if i - j >= k)


def p_over(la, lb, line, n=20):
    g = joint(la, lb, n)
    return sum(g[i][j] for i in range(n + 1) for j in range(n + 1) if i + j > line)


def fair_decimal(p):
    return 1.0 / p if p > 0 else None


def american(dec):
    if dec is None:
        return None
    if dec >= 2.0:
        return int(round((dec - 1) * 100))
    return int(round(-100.0 / (dec - 1)))


def in_band(dec):
    return dec is not None and BAND_MIN_DEC <= dec <= BAND_MAX_DEC


def grade(p, dec):
    if p >= 0.70 and in_band(dec):
        return "high", "model probability >= 70% and fair price inside -250..+10000"
    if p >= 0.60:
        return "medium", "model probability >= 60% but below the 70% high-confidence threshold"
    if p >= 0.70:
        return "medium", ">= 70% model probability but priced shorter than -250, so outside the brief's band"
    return "low", "under 60% model probability"


def outcome(label, p):
    dec = round(fair_decimal(p), 3)
    return {
        "label": label,
        "probability": round(p, 4),
        "fair_decimal": dec,
        "fair_american": american(dec),
        "in_band": in_band(dec),
    }


# ---------------------------------------------------------------- NHL

H_ICE = 1.044          # home-ice multiplier on goal expectation (our constant)
SHRINK = 8.0           # empirical-Bayes shrinkage games (our constant)


def nhl_rates():
    tbl = json.loads((ATLAS / "capture_nhl_table.json").read_text())
    teams = {t["abbrev"]: t for t in tbl["teams"]}
    total_gf = sum(t["gf"] for t in teams.values())
    total_gp = sum(t["gp"] for t in teams.values())
    L = total_gf / total_gp
    return tbl, teams, L


def nhl_lambdas(home, away, teams, L):
    h, a = teams[home], teams[away]

    def rate(t, key):
        w = t["gp"] / (t["gp"] + SHRINK)
        return 1 + w * ((t[key] / t["gp"]) / L - 1)

    att_h, def_h = rate(h, "gf"), rate(h, "ga")
    att_a, def_a = rate(a, "gf"), rate(a, "ga")
    lam_h = L * att_h * def_a * H_ICE
    lam_a = L * att_a * def_h / H_ICE
    return lam_h, lam_a


def nhl_markets(home, away, teams, L, home_name=None, away_name=None):
    home_name = home_name or home
    away_name = away_name or away
    lam_h, lam_a = nhl_lambdas(home, away, teams, L)
    ph, pa = p_win(lam_h, lam_a)
    out = []
    out.append({
        "market": "Moneyline",
        "line": None,
        "outcomes": [outcome(home_name, ph), outcome(away_name, pa)],
    })
    p_cover = p_margin_ge(lam_h, lam_a, 2)
    out.append({
        "market": "Puck Line",
        "line": 1.5,
        "outcomes": [outcome(f"{home_name} -1.5", p_cover), outcome(f"{away_name} +1.5", 1 - p_cover)],
    })
    total = lam_h + lam_a
    best, best_gap = None, 9e9
    for cand in [x / 2 for x in range(int(total * 2) - 4, int(total * 2) + 5)]:
        gap = abs(p_over(lam_h, lam_a, cand) - 0.5)
        if gap < best_gap:
            best, best_gap = cand, gap
    po = p_over(lam_h, lam_a, best)
    out.append({
        "market": "Total",
        "line": best,
        "outcomes": [outcome(f"Over {best}", po), outcome(f"Under {best}", 1 - po)],
    })
    params = {
        "lambda_home": round(lam_h, 4),
        "lambda_away": round(lam_a, 4),
        "league_goals_per_team_game": round(L, 4),
        "home_ice_multiplier": H_ICE,
        "shrinkage_games": SHRINK,
        "tie_policy": "tied regulation scores split 50/50",
    }
    return out, params


# ---------------------------------------------------------------- MLB

PYTH_EXP = 1.83
HOME_LOGIT = 0.16
RUN_HFA = 1.02


def mlb_rates():
    cap = json.loads((ATLAS / "capture_mlb.json").read_text())
    return {t["name"]: t for t in cap["teams"]}, cap


def mlb_markets(home, away, teams):
    h, a = teams[home], teams[away]

    def pyth(t):
        rs, ra = float(t["runsScored"]), float(t["runsAllowed"])
        return rs ** PYTH_EXP / (rs ** PYTH_EXP + ra ** PYTH_EXP)

    ph0, pa0 = pyth(h), pyth(a)
    denom = ph0 + pa0 - 2 * ph0 * pa0
    p = (ph0 - ph0 * pa0) / denom if denom else 0.5
    logit = math.log(p / (1 - p)) + HOME_LOGIT
    p_home = 1 / (1 + math.exp(-logit))

    g = 162.0
    lam_h = ((h["runsScored"] / g) + (a["runsAllowed"] / g)) / 2 * RUN_HFA
    lam_a = ((a["runsScored"] / g) + (h["runsAllowed"] / g)) / 2 / RUN_HFA

    out = []
    out.append({
        "market": "Moneyline",
        "line": None,
        "outcomes": [outcome(home, p_home), outcome(away, 1 - p_home)],
    })
    p_cover = p_margin_ge(lam_h, lam_a, 2, n=22)
    out.append({
        "market": "Run Line",
        "line": 1.5,
        "outcomes": [outcome(f"{home} -1.5", p_cover), outcome(f"{away} +1.5", 1 - p_cover)],
    })
    total = lam_h + lam_a
    best, best_gap = None, 9e9
    for cand in [x / 2 for x in range(int(total * 2) - 6, int(total * 2) + 7)]:
        gap = abs(p_over(lam_h, lam_a, cand, n=22) - 0.5)
        if gap < best_gap:
            best, best_gap = cand, gap
    po = p_over(lam_h, lam_a, best, n=22)
    out.append({
        "market": "Total",
        "line": best,
        "outcomes": [outcome(f"Over {best}", po), outcome(f"Under {best}", 1 - po)],
    })
    params = {
        "pythagorean_home": round(ph0, 4),
        "pythagorean_away": round(pa0, 4),
        "logit_home_edge": HOME_LOGIT,
        "lambda_runs_home": round(lam_h, 4),
        "lambda_runs_away": round(lam_a, 4),
        "pythagorean_exponent": PYTH_EXP,
    }
    return out, params


# ---------------------------------------------------------------- driver

BLANK = {
    "basketball": ("No verified team-strength input. For the NBA the 2026-27 season is one game old, "
                   "and stats.nba.com (the official carrier of prior-season team data) is not "
                   "reachable from this environment, so no rating is originated. For the EuroLeague "
                   "the official live API returned an empty standings payload "
                   "(api-live.euroleague.net/v2/competitions/E/seasons/E2026/standings), so no table "
                   "could be read."),
    "tennis": ("The official ATP singles rankings table could not be read from atptour.com in this "
               "session (the page returned only the ranking-date selector), so no rating is "
               "originated for these ties."),
}

INHERITED_BLANK = ("Not re-read in this session. The fixture is published with the official URL the "
                   "earlier desk cited, but no value on this row has been confirmed first-hand, so "
                   "every price is left blank.")


def main():
    fx = json.loads((ATLAS / "fixtures.json").read_text())
    nhl_tbl, nhl_teams, L = nhl_rates()
    mlb_teams, mlb_cap = mlb_rates()

    rows = []
    for f in fx["fixtures"]:
        row = dict(f)
        row["line_status"] = "blank"
        row["blank_reason"] = ""
        row["markets"] = []
        row["model_params"] = None
        row["pick"] = None
        row["pick_source"] = None
        row["inputs_url"] = None

        if row["status"] != "confirmed":
            row["blank_reason"] = INHERITED_BLANK
            row["match_band"] = {"favourite": None, "favourite_decimal": None,
                                 "favourite_american": None, "outsider_decimal": None,
                                 "outsider_american": None, "in_band": False}
            rows.append(row)
            continue

        league = None
        if row["id"].startswith("nhl-"):
            league = "nhl"
        elif row["id"].startswith("mlb-"):
            league = "mlb"

        if league == "nhl":
            markets, params = nhl_markets(row["home_abbrev"], row["away_abbrev"], nhl_teams, L,
                                          home_name=row["home"], away_name=row["away"])
            row["markets"] = markets
            row["model_params"] = params
            row["line_status"] = "originated"
            row["inputs_url"] = nhl_tbl["url"]
            row["official_source"] = row["official_source"] + " · inputs: " + nhl_tbl["source"]
        elif league == "mlb":
            markets, params = mlb_markets(row["home"], row["away"], mlb_teams)
            row["markets"] = markets
            row["model_params"] = params
            row["line_status"] = "originated"
            row["inputs_url"] = mlb_cap["standings_url"]
            row["official_source"] = row["official_source"] + " · inputs: " + mlb_cap["source"]
        else:
            row["blank_reason"] = BLANK.get(row["sport"], "No verified strength input for this competition.")
            row["match_band"] = {"favourite": None, "favourite_decimal": None,
                                 "favourite_american": None, "outsider_decimal": None,
                                 "outsider_american": None, "in_band": False}
            rows.append(row)
            continue

        # Match-level band: the brief asks for high-confidence picks on matches whose
        # prices sit between -250 and +10000, i.e. whose moneyline favourite is no
        # shorter than 1.40 and whose outsider is no longer than 101.00.
        ml = [m for m in row["markets"] if m["market"] == "Moneyline"][0]
        fav = max(ml["outcomes"], key=lambda o: o["probability"])
        outsider = min(ml["outcomes"], key=lambda o: o["probability"])
        row["match_band"] = {
            "favourite": fav["label"],
            "favourite_decimal": fav["fair_decimal"],
            "favourite_american": fav["fair_american"],
            "outsider_decimal": outsider["fair_decimal"],
            "outsider_american": outsider["fair_american"],
            "in_band": (BAND_MIN_DEC <= fav["fair_decimal"] <= BAND_MAX_DEC
                        and BAND_MIN_DEC <= outsider["fair_decimal"] <= BAND_MAX_DEC),
        }

        best = fav
        conf, reason = grade(best["probability"], best["fair_decimal"])
        row["pick"] = {
            "selection": best["label"],
            "market": "Moneyline",
            "probability": best["probability"],
            "fair_decimal": best["fair_decimal"],
            "fair_american": best["fair_american"],
            "confidence": conf,
            "grade_reason": reason,
        }
        row["pick_source"] = "moneyline favourite (match winner)"

        # strongest selection anywhere on the row that sits inside the brief's band
        cands = []
        for m in row["markets"]:
            for o in m["outcomes"]:
                if o["in_band"]:
                    cands.append(((o["probability"], -abs(o["fair_decimal"] - 2.0)), m["market"], o))
        if cands:
            cands.sort(key=lambda c: c[0], reverse=True)
            _, market, o = cands[0]
            conf, reason = grade(o["probability"], o["fair_decimal"])
            row["band_selection"] = {
                "selection": o["label"],
                "market": market,
                "probability": o["probability"],
                "fair_decimal": o["fair_decimal"],
                "fair_american": o["fair_american"],
                "confidence": conf,
                "grade_reason": reason,
            }
        else:
            row["band_selection"] = None

        for m in row["markets"]:
            for o in m["outcomes"]:
                o["confidence"] = grade(o["probability"], o["fair_decimal"])[0]

        rows.append(row)

    rows.sort(key=lambda r: (r["date"] or "", r["sport"], r["home"] or ""))

    counts = {
        "rows": len(rows),
        "confirmed": sum(1 for r in rows if r["status"] == "confirmed"),
        "inherited_unverified": sum(1 for r in rows if r["status"] == "inherited-unverified"),
        "originated": sum(1 for r in rows if r["line_status"] == "originated"),
        "blank": sum(1 for r in rows if r["line_status"] == "blank"),
        "high": sum(1 for r in rows if r.get("pick") and r["pick"]["confidence"] == "high"),
        "medium": sum(1 for r in rows if r.get("pick") and r["pick"]["confidence"] == "medium"),
        "low": sum(1 for r in rows if r.get("pick") and r["pick"]["confidence"] == "low"),
        "high_band_selections": sum(1 for r in rows
                                    if r.get("band_selection") and r["band_selection"]["confidence"] == "high"),
        "matches_in_band": sum(1 for r in rows if r.get("match_band") and r["match_band"]["in_band"]),
        "sports": len({r["sport"] for r in rows}),
    }

    payload = {
        "generated_at": GENERATED_AT,
        "session": SESSION,
        "rule": {
            "high": "model probability >= 0.70 AND fair decimal inside 1.40..101.00 (-250..+10000)",
            "medium": "model probability >= 0.60, or >= 0.70 priced shorter than -250",
            "low": "model probability < 0.60",
            "band": {"min_decimal": BAND_MIN_DEC, "max_decimal": BAND_MAX_DEC,
                     "min_american": BAND_MIN_AM, "max_american": BAND_MAX_AM},
        },
        "counts": counts,
        "matches": rows,
    }
    (ATLAS / "matches.json").write_text(json.dumps(payload, indent=1) + "\n")
    print(json.dumps(counts, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
