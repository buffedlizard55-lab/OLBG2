#!/usr/bin/env python3
"""Originate betting lines from verified official data.

Nothing in here reads a bookmaker price. Every probability is derived from the
verified inputs in data/inputs/*.json, using the formulas documented in
METHODOLOGY.md. The output is data/matches.json.

Run:  python3 scripts/model.py
"""
from __future__ import annotations

import re

import json
import math
import os
from datetime import datetime, timezone

def dated_source_url(template: str, date: str) -> str:
    """Point a feed template at one fixture's date without mangling query strings.

    NHL-style feeds end in a date path segment; NBA-style feeds carry ?date=.
    Anything else is returned unchanged so a citation is never invented.
    """
    if "date=" in template:
        return re.sub(r"date=\d{4}-\d{2}-\d{2}", f"date={date}", template)
    if re.search(r"/\d{4}-\d{2}-\d{2}/?$", template):
        return re.sub(r"/\d{4}-\d{2}-\d{2}(/?)$", lambda m: "/" + date + m.group(1), template)
    return template


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUTS = os.path.join(ROOT, "data", "inputs")
OUT = os.path.join(ROOT, "data", "matches.json")

# ---------------------------------------------------------------- model knobs
# These are *our own* line-setting parameters, not sourced facts. Changing them
# changes the lines; they are recorded in every match row for auditability.
PARAMS = {
    "nhl_home_ice_factor": 1.05,     # multiplicative home-ice boost on expected goals
    "nhl_shrink_k": 8.0,             # empirical-Bayes shrinkage: weight = gp/(gp+k) on attack/defence
    "nhl_overround": 0.04,           # 4% theoretical margin applied to fair odds
    "nba_shrink_to_500": 0.25,       # 25% regression of last season's win% to .500
    "nba_points_per_logit": 11.0,    # expected NBA margin points per unit of logit rating
    "nba_margin_sigma": 11.0,        # logistic scale converting expected margin to P(win)
    "nba_home_logit_edge": 0.20,     # home court edge, in logit units (about 55% league home win rate)
    "nba_overround": 0.04,
    "urc_shrink_k": 6.0,             # same shrinkage idea; 6 because only 3 rounds are played
    "urc_home_points": 3.0,          # home advantage in points
    "urc_margin_sigma": 13.0,        # logistic scale for rugby margins
    "urc_overround": 0.04,
    "nhl_min_gp_high": 7,
    "nhl_min_gp_medium": 5,
}

CAPTURED_AT = "2026-10-21T05:45:00Z"


# ---------------------------------------------------------------- maths helpers
def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_grid(lam: float, nmax: int = 16) -> list[float]:
    return [poisson_pmf(k, lam) for k in range(nmax + 1)]


def nhl_moneyline(lam_home: float, lam_away: float) -> tuple[float, float, float]:
    """Return (p_home, p_away, p_tie) with the tie split evenly (OT/SO)."""
    ph, pa = poisson_grid(lam_home), poisson_grid(lam_away)
    p_home = p_away = p_tie = 0.0
    for i, ph_i in enumerate(ph):
        for j, pa_j in enumerate(pa):
            p = ph_i * pa_j
            if i > j:
                p_home += p
            elif j > i:
                p_away += p
            else:
                p_tie += p
    return p_home + p_tie / 2, p_away + p_tie / 2, p_tie


def nhl_puck_line(lam_home: float, lam_away: float, handicap: float = 1.5) -> tuple[float, float]:
    """P(home wins by more than handicap) and P(away loses by fewer than handicap)."""
    ph, pa = poisson_grid(lam_home), poisson_grid(lam_away)
    p_home = p_away = 0.0
    for i, ph_i in enumerate(ph):
        for j, pa_j in enumerate(pa):
            p = ph_i * pa_j
            if i - j > handicap:
                p_home += p
            else:
                p_away += p
    return p_home, p_away


def nhl_total(lam_home: float, lam_away: float, line: float) -> tuple[float, float]:
    ph, pa = poisson_grid(lam_home), poisson_grid(lam_away)
    over = under = 0.0
    for i, ph_i in enumerate(ph):
        for j, pa_j in enumerate(pa):
            p = ph_i * pa_j
            if i + j > line:
                over += p
            else:
                under += p
    return over, under


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def price(p: float, overround: float) -> float:
    """Fair odds 1/p with a margin applied, clamped to a publishable range."""
    return round(min(12.0, max(1.05, 1.0 / (p * (1.0 + overround)))), 2)


def half_line(value: float) -> float:
    """Nearest half-point line strictly away from the number (no pushes)."""
    return math.floor(value) + 0.5


# ---------------------------------------------------------------- confidence
def confidence_for(sport: str, p: float, min_gp: int | None) -> str:
    """Deterministic confidence rule from METHODOLOGY.md."""
    if sport == "Basketball":
        # Current season sample is zero; only last season's prior exists.
        return "medium" if p >= 0.68 else "low"
    if sport == "Rugby Union":
        # Three rounds played -> never above medium.
        return "medium" if p >= 0.62 else "low"
    if min_gp is not None and min_gp >= PARAMS["nhl_min_gp_high"]:
        if p >= 0.65:
            return "high"
        if p >= 0.57:
            return "medium"
        return "low"
    if min_gp is not None and min_gp >= PARAMS["nhl_min_gp_medium"]:
        return "medium" if p >= 0.68 else "low"
    return "low"


# ---------------------------------------------------------------- builders
def build_nhl(teams: dict, fixtures: dict) -> list[dict]:
    rows = []
    valid = [t for t in teams.values() if t["gf"] is not None]
    league_gf = sum(t["gf"] / t["gp"] for t in valid) / len(valid)
    league_ga = sum(t["ga"] / t["gp"] for t in valid) / len(valid)
    league_avg = (league_gf + league_ga) / 2

    for fx in fixtures["fixtures"]:
        h, a = teams[fx["home"]], teams[fx["away"]]
        base = {
            "id": fx["id"],
            "sport": "Ice Hockey",
            "competition": "NHL",
            "home": {"code": fx["home"], "name": h["name"]},
            "away": {"code": fx["away"], "name": a["name"]},
            "start_display": fx["start_utc"].replace("T", " ").replace(":00Z", " UTC"),
            "start_utc": fx["start_utc"],
            "venue": fx["venue"],
            "fixture_source": {"name": fixtures["source_name"], "url": dated_source_url(fixtures["source_url"], fx["date"])},
            "data_source": {"name": "NHL official team summary", "url": INPUTS_URLS["nhl"], "captured_at": "2026-10-21T05:20:00Z"},
            "olbg_event_url": fx.get("olbg_event_url"),
            "params": {k: PARAMS[k] for k in ("nhl_home_ice_factor", "nhl_shrink_k", "nhl_overround")},
        }
        if h["gf"] is None or a["gf"] is None:
            base.update({
                "line_status": "not_originated",
                "reason": "Verified goals-for / goals-against for one or both teams were not captured.",
                "confidence": "unverified",
            })
            rows.append(base)
            continue

        k = PARAMS["nhl_shrink_k"]

        def shrink(ratio, gp):
            w = gp / (gp + k)
            return 1.0 + w * (ratio - 1.0)

        att_h = shrink((h["gf"] / h["gp"]) / league_avg, h["gp"])
        def_h = shrink((h["ga"] / h["gp"]) / league_avg, h["gp"])
        att_a = shrink((a["gf"] / a["gp"]) / league_avg, a["gp"])
        def_a = shrink((a["ga"] / a["gp"]) / league_avg, a["gp"])
        lam_h = league_avg * att_h * def_a * PARAMS["nhl_home_ice_factor"]
        lam_a = league_avg * att_a * def_h / PARAMS["nhl_home_ice_factor"]
        ph, pa, _ = nhl_moneyline(lam_h, lam_a)
        puck_h, puck_a = nhl_puck_line(lam_h, lam_a)
        total_line = half_line(lam_h + lam_a)
        over, under = nhl_total(lam_h, lam_a, total_line)

        p_pick = max(ph, pa)
        side = "home" if ph >= pa else "away"
        conf = confidence_for("Ice Hockey", p_pick, min(h["gp"], a["gp"]))

        base.update({
            "line_status": "originated",
            "model": {
                "league_avg_goals_per_game": round(league_avg, 3),
                "home_attack": round(att_h, 3), "home_defence": round(def_h, 3),
                "away_attack": round(att_a, 3), "away_defence": round(def_a, 3),
                "expected_home_goals": round(lam_h, 3),
                "expected_away_goals": round(lam_a, 3),
                "expected_margin": round(lam_h - lam_a, 3),
                "expected_total": round(lam_h + lam_a, 3),
            },
            "inputs": {
                "home": {"gp": h["gp"], "record": f'{h["w"]}-{h["l"]}-{h["otl"]}', "gf": h["gf"], "ga": h["ga"], "gf_pg": round(h["gf"] / h["gp"], 2), "ga_pg": round(h["ga"] / h["gp"], 2)},
                "away": {"gp": a["gp"], "record": f'{a["w"]}-{a["l"]}-{a["otl"]}', "gf": a["gf"], "ga": a["ga"], "gf_pg": round(a["gf"] / a["gp"], 2), "ga_pg": round(a["ga"] / a["gp"], 2)},
            },
            "markets": [
                {"market": "Moneyline", "selection": f'{h["name"]}', "line": None, "probability": round(ph, 4), "price": price(ph, PARAMS["nhl_overround"])},
                {"market": "Moneyline", "selection": f'{a["name"]}', "line": None, "probability": round(pa, 4), "price": price(pa, PARAMS["nhl_overround"])},
                {"market": "Puck line", "selection": f'{h["name"]} -1.5', "line": -1.5, "probability": round(puck_h, 4), "price": price(puck_h, PARAMS["nhl_overround"])},
                {"market": "Puck line", "selection": f'{a["name"]} +1.5', "line": 1.5, "probability": round(puck_a, 4), "price": price(puck_a, PARAMS["nhl_overround"])},
                {"market": "Total goals", "selection": f'Over {total_line}', "line": total_line, "probability": round(over, 4), "price": price(over, PARAMS["nhl_overround"])},
                {"market": "Total goals", "selection": f'Under {total_line}', "line": total_line, "probability": round(under, 4), "price": price(under, PARAMS["nhl_overround"])},
            ],
            "pick": {
                "market": "Moneyline",
                "selection": h["name"] if side == "home" else a["name"],
                "side": side,
                "probability": round(p_pick, 4),
                "price": price(p_pick, PARAMS["nhl_overround"]),
                "confidence": conf,
            },
            "confidence": conf,
        })
        rows.append(base)
    return rows


def build_nba(teams: dict, fixtures: dict) -> list[dict]:
    rows = []
    league_home_w = sum(t["home_w"] for t in teams.values())
    league_home_l = sum(t["home_l"] for t in teams.values())
    league_home_rate = league_home_w / (league_home_w + league_home_l)

    def rating(t):
        raw = t["w"] / (t["w"] + t["l"])
        shrunk = (1 - PARAMS["nba_shrink_to_500"]) * raw + PARAMS["nba_shrink_to_500"] * 0.5
        return math.log(shrunk / (1 - shrunk)), shrunk

    for fx in fixtures["fixtures"]:
        h, a = teams[fx["home"]], teams[fx["away"]]
        rh, sh = rating(h)
        ra, sa = rating(a)
        margin = PARAMS["nba_points_per_logit"] * (rh + PARAMS["nba_home_logit_edge"] - ra)
        p_home = logistic(margin / PARAMS["nba_margin_sigma"])
        p_away = 1 - p_home
        spread = -margin
        line = -(math.floor(abs(spread)) + 0.5) if spread < 0 else math.floor(spread) + 0.5
        # probability the home team covers its own line
        p_cover_home = logistic((margin + line) / PARAMS["nba_margin_sigma"])
        p_pick = max(p_home, p_away)
        side = "home" if p_home >= p_away else "away"
        conf = confidence_for("Basketball", p_pick, None)

        rows.append({
            "id": fx["id"],
            "sport": "Basketball",
            "competition": "NBA",
            "home": {"code": fx["home"], "name": h["name"]},
            "away": {"code": fx["away"], "name": a["name"]},
            "start_display": fx["date"] + " " + fx["tip_et"] + " ET",
            "start_utc": None,
            "start_note": "Tip time as published by NBA.com in US Eastern time.",
            "venue": None,
            "fixture_source": {"name": fixtures["source_name"], "url": dated_source_url(fixtures["source_url"], fx["date"])},
            "data_source": {"name": "NBA official standings 2025-26", "url": INPUTS_URLS["nba"], "captured_at": "2026-10-21T05:25:00Z"},
            "olbg_event_url": fx.get("olbg_event_url"),
            "line_status": "originated",
            "params": {k: PARAMS[k] for k in ("nba_shrink_to_500", "nba_points_per_logit", "nba_margin_sigma", "nba_home_logit_edge", "nba_overround")},
            "model": {
                "league_home_win_rate_2025_26": round(league_home_rate, 4),
                "home_shrunk_win_pct": round(sh, 4),
                "away_shrunk_win_pct": round(sa, 4),
                "expected_margin_home": round(margin, 2),
            },
            "inputs": {
                "home": {"season": "2025-26", "record": f'{h["w"]}-{h["l"]}', "home": f'{h["home_w"]}-{h["home_l"]}', "road": f'{h["road_w"]}-{h["road_l"]}'},
                "away": {"season": "2025-26", "record": f'{a["w"]}-{a["l"]}', "home": f'{a["home_w"]}-{a["home_l"]}', "road": f'{a["road_w"]}-{a["road_l"]}'},
                "note": "2026-27 record for both teams was 0-0 before tip-off; prior season used as the strength input.",
            },
            "markets": [
                {"market": "Moneyline", "selection": h["name"], "line": None, "probability": round(p_home, 4), "price": price(p_home, PARAMS["nba_overround"])},
                {"market": "Moneyline", "selection": a["name"], "line": None, "probability": round(p_away, 4), "price": price(p_away, PARAMS["nba_overround"])},
                {"market": "Handicap", "selection": f'{h["name"]} {line:+.1f}', "line": line, "probability": round(p_cover_home, 4), "price": price(p_cover_home, PARAMS["nba_overround"])},
                {"market": "Handicap", "selection": f'{a["name"]} {-line:+.1f}', "line": -line, "probability": round(1 - p_cover_home, 4), "price": price(1 - p_cover_home, PARAMS["nba_overround"])},
            ],
            "markets_not_originated": [
                {"market": "Game total", "reason": "No verified 2025-26 team points-for / points-against data was captured, so a total cannot be originated without inventing an input."}
            ],
            "pick": {
                "market": "Moneyline",
                "selection": h["name"] if side == "home" else a["name"],
                "side": side,
                "probability": round(p_pick, 4),
                "price": price(p_pick, PARAMS["nba_overround"]),
                "confidence": conf,
            },
            "confidence": conf,
        })
    return rows


def build_urc(data: dict) -> list[dict]:
    rows = []
    table = data["table"]
    league_pf = sum(t["pf"] for t in table.values()) / sum(t["pl"] for t in table.values())
    league_pa = sum(t["pa"] for t in table.values()) / sum(t["pl"] for t in table.values())

    for fx in data["fixtures"]:
        h, a = table[fx["home"]], table[fx["away"]]
        k = PARAMS["urc_shrink_k"]

        def shrink(ratio, pl):
            w = pl / (pl + k)
            return 1.0 + w * (ratio - 1.0)

        h_pf = league_pf * shrink((h["pf"] / h["pl"]) / league_pf, h["pl"])
        h_pa = league_pa * shrink((h["pa"] / h["pl"]) / league_pa, h["pl"])
        a_pf = league_pf * shrink((a["pf"] / a["pl"]) / league_pf, a["pl"])
        a_pa = league_pa * shrink((a["pa"] / a["pl"]) / league_pa, a["pl"])
        exp_h = league_pf * (h_pf / league_pf) * (a_pa / league_pa) + PARAMS["urc_home_points"] / 2
        exp_a = league_pa * (a_pf / league_pa) * (h_pa / league_pa) - PARAMS["urc_home_points"] / 2
        margin = exp_h - exp_a
        p_home = logistic(margin / PARAMS["urc_margin_sigma"])
        p_away = 1 - p_home
        total = exp_h + exp_a
        line = half_line(total)
        p_over = logistic((total - line) / (PARAMS["urc_margin_sigma"] * 0.9))
        hcap = half_line(abs(margin))
        home_line = -hcap if margin > 0 else hcap
        p_cover_home = logistic((margin + home_line) / PARAMS["urc_margin_sigma"])

        p_pick = max(p_home, p_away)
        side = "home" if p_home >= p_away else "away"
        conf = confidence_for("Rugby Union", p_pick, None)

        rows.append({
            "id": fx["id"],
            "sport": "Rugby Union",
            "competition": "United Rugby Championship",
            "home": {"code": fx["home"], "name": h["name"]},
            "away": {"code": fx["away"], "name": a["name"]},
            "start_display": f'{fx["date_local"]} {fx["time_local"]} local',
            "start_utc": None,
            "start_note": "URC publishes venue-local times only; the string is stored exactly as published.",
            "venue": fx["venue"],
            "fixture_source": {"name": "URC official match centre", "url": data["meta"]["source_url"]},
            "data_source": {"name": "URC official league table", "url": data["meta"]["table_url"], "captured_at": "2026-10-21T05:35:00Z"},
            "olbg_event_url": None,
            "line_status": "originated",
            "params": {k: PARAMS[k] for k in ("urc_shrink_k", "urc_home_points", "urc_margin_sigma", "urc_overround")},
            "model": {
                "league_pf_per_game": round(league_pf, 2),
                "league_pa_per_game": round(league_pa, 2),
                "expected_home_points": round(exp_h, 2),
                "expected_away_points": round(exp_a, 2),
                "expected_margin_home": round(margin, 2),
                "expected_total": round(total, 2),
            },
            "inputs": {
                "home": {"pl": h["pl"], "record": f'{h["w"]}-{h["d"]}-{h["l"]}', "pf": h["pf"], "pa": h["pa"], "pts": h["pts"], "form": h["form"]},
                "away": {"pl": a["pl"], "record": f'{a["w"]}-{a["d"]}-{a["l"]}', "pf": a["pf"], "pa": a["pa"], "pts": a["pts"], "form": a["form"]},
            },
            "markets": [
                {"market": "Match winner", "selection": h["name"], "line": None, "probability": round(p_home, 4), "price": price(p_home, PARAMS["urc_overround"])},
                {"market": "Match winner", "selection": a["name"], "line": None, "probability": round(p_away, 4), "price": price(p_away, PARAMS["urc_overround"])},
                {"market": "Handicap", "selection": f'{h["name"]} {home_line:+.1f}', "line": home_line, "probability": round(p_cover_home, 4), "price": price(p_cover_home, PARAMS["urc_overround"])},
                {"market": "Handicap", "selection": f'{a["name"]} {-home_line:+.1f}', "line": -home_line, "probability": round(1 - p_cover_home, 4), "price": price(1 - p_cover_home, PARAMS["urc_overround"])},
                {"market": "Match total", "selection": f"Over {line}", "line": line, "probability": round(p_over, 4), "price": price(p_over, PARAMS["urc_overround"])},
                {"market": "Match total", "selection": f"Under {line}", "line": line, "probability": round(1 - p_over, 4), "price": price(1 - p_over, PARAMS["urc_overround"])},
            ],
            "pick": {
                "market": "Match winner",
                "selection": h["name"] if side == "home" else a["name"],
                "side": side,
                "probability": round(p_pick, 4),
                "price": price(p_pick, PARAMS["urc_overround"]),
                "confidence": conf,
            },
            "confidence": conf,
        })
    return rows


def build_other(fixtures: dict) -> list[dict]:
    rows = []
    for fx in fixtures["other_verified"]["cricket"]:
        rows.append({
            "id": fx["id"],
            "sport": "Cricket",
            "competition": "International (" + fx["format"] + ")",
            "home": {"code": None, "name": fx["home"]},
            "away": {"code": None, "name": fx["away"]},
            "start_display": fx["date"] + " " + fx["start_display"],
            "start_utc": None,
            "start_note": "ICC displays start time in the viewer's local time; no UTC value was published.",
            "venue": None,
            "fixture_source": {"name": "ICC official match list", "url": fx["url"]},
            "data_source": None,
            "olbg_event_url": fx.get("olbg_event_url"),
            "line_status": "not_originated",
            "reason": "No official team-strength input was available: the ICC team-ranking table did not render in the captured page and no other governing-body rating was verified. A line would require inventing an input.",
            "confidence": "unverified",
        })
    return rows


INPUTS_URLS = {
    "nhl": json.load(open(os.path.join(INPUTS, "nhl_teams.json")))["meta"]["source_url"],
    "nba": json.load(open(os.path.join(INPUTS, "nba_teams.json")))["meta"]["source_url"],
}


def main() -> None:
    nhl_in = json.load(open(os.path.join(INPUTS, "nhl_teams.json")))
    nba_in = json.load(open(os.path.join(INPUTS, "nba_teams.json")))
    urc_in = json.load(open(os.path.join(INPUTS, "urc.json")))
    fixtures = json.load(open(os.path.join(INPUTS, "fixtures.json")))

    matches = []
    matches += build_nhl(nhl_in["teams"], fixtures["nhl"])
    matches += build_nba(nba_in["teams"], fixtures["nba"])
    matches += build_urc(urc_in)
    matches += build_other(fixtures)
    matches.sort(key=lambda m: (m["sport"], m["start_display"] or ""))

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs_captured_at": CAPTURED_AT,
        "params": PARAMS,
        "counts": {
            "total": len(matches),
            "originated": sum(1 for m in matches if m["line_status"] == "originated"),
            "not_originated": sum(1 for m in matches if m["line_status"] != "originated"),
            "high": sum(1 for m in matches if m.get("confidence") == "high"),
            "medium": sum(1 for m in matches if m.get("confidence") == "medium"),
            "low": sum(1 for m in matches if m.get("confidence") == "low"),
        },
        "matches": matches,
    }
    with open(OUT, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload["counts"], indent=2))
    for m in matches:
        if m.get("confidence") == "high":
            print("HIGH:", m["id"], m["pick"]["selection"], m["pick"]["probability"])


if __name__ == "__main__":
    main()
