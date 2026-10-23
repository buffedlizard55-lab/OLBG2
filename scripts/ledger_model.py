#!/usr/bin/env python3
"""Originate our own prices for every fixture that has official numeric inputs.

Inputs (all from data/ledger/official.json, i.e. captured official responses):
  * season records: wins, losses, goals/points for and against, games played;
  * per-game scoring rates, used to build an expected score for each fixture.

The method is deliberately simple and stated in full on the methodology page:

  rating      = 1500 + 400 * (points_pct - 0.5) + 30 * (score_diff_per_game)
  home edge   = +45 rating points (a documented constant, not fitted to any market)
  p_home      = 1 / (1 + 10 ** (-(rating_home + 45 - rating_away) / 400))
  expected score = (attack_home * defence_away / league_average) per side
  totals      = Poisson with that expectation
  handicap    = Poisson margin, ties split 50/50 after the regulation draw

No bookmaker price is an input. OLBG's quoted price is carried alongside only as the
external quote it is, and never influences the number we publish.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ledger"

HOME_EDGE = 45.0


def american(p: float):
    if p <= 0 or p >= 1:
        return ""
    if p >= 0.5:
        return f"{round(-100 * p / (1 - p)):+d}" if abs(round(-100 * p / (1 - p))) >= 100 else f"{round(-100 * p / (1 - p)):+d}"
    return f"+{round(100 * (1 - p) / p):d}"


def fair(p: float):
    """Fair decimal and American, with the brief's band flag applied to the American."""
    dec = round(1 / p, 2) if p else None
    am = american(p)
    try:
        am_int = int(am) if am else None
    except ValueError:
        am_int = None
    in_band = am_int is not None and -250 <= am_int <= 10000
    return {"prob": round(p, 4), "decimal": dec, "american": am, "in_band": in_band}


def grade(p: float) -> str:
    if p >= 0.70:
        return "high"
    if p >= 0.60:
        return "medium"
    return "low"


def poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_probs(lam_home: float, lam_away: float, maxg: int = 15):
    ph = [poisson(i, lam_home) for i in range(maxg)]
    pa = [poisson(i, lam_away) for i in range(maxg)]
    win = draw = loss = 0.0
    margin2 = 0.0
    for i, a in enumerate(ph):
        for j, b in enumerate(pa):
            p = a * b
            if i > j:
                win += p
                if i - j >= 2:
                    margin2 += p
            elif i == j:
                draw += p
            else:
                loss += p
    return win, draw, loss, margin2, ph, pa


def total_dist(ph, pa):
    """Distribution of the combined score."""
    dist = [0.0] * (len(ph) + len(pa))
    for i, a in enumerate(ph):
        for j, b in enumerate(pa):
            dist[i + j] += a * b
    return dist


def over_prob(dist, line: float):
    # a half-point line: over means total > line
    return sum(p for k, p in enumerate(dist) if k > line)


def ratings_nhl(records: dict):
    out = {}
    for key, r in records.items():
        gp = r["gp"] or 1
        pts_pct = (r["pts"] or 0) / (2 * gp)
        diff = ((r["gf"] or 0) - (r["ga"] or 0)) / gp
        out[key] = {
            "rating": 1500 + 400 * (pts_pct - 0.5) + 30 * diff,
            "attack": (r["gf"] or 0) / gp,
            "defence": (r["ga"] or 0) / gp,
            "gp": gp, "record": r,
        }
    return out


def ratings_mlb(records: dict):
    out = {}
    for key, r in records.items():
        w, l = r.get("w") or 0, r.get("l") or 0
        gp = max(w + l, 1)
        diff = (r.get("rs") or 0) - (r.get("ra") or 0)
        out[key] = {
            "rating": 1500 + 400 * (w / gp - 0.5) + 8 * (diff / gp),
            "attack": (r.get("rs") or 0) / gp,
            "defence": (r.get("ra") or 0) / gp,
            "gp": gp, "record": r,
        }
    return out


def ratings_el(records: dict):
    out = {}
    for key, r in records.items():
        gp = r["gp"] or 1
        out[key] = {
            "rating": 1500 + 400 * ((r["w"] / gp) - 0.5) + 8 * ((r["pf"] - r["pa"]) / gp),
            "attack": r["pf"] / gp,
            "defence": r["pa"] / gp,
            "gp": gp, "record": r,
        }
    return out


def norm(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def lookup(records: dict, name: str):
    """Find a record by exact normalised name, then by the last distinctive word."""
    n = norm(name)
    if n in records:
        return records[n]
    words = [w for w in n.split() if len(w) >= 5]
    for w in reversed(words):
        for k in records:
            if w in k.split():
                return records[k]
    return None


def build_market_block(sport: str, home: str, away: str, rh: dict, ra: dict, league_avg: float, lines: list[float]):
    """Return win/handicap/total selections with probabilities."""
    p_home = 1 / (1 + 10 ** (-((rh["rating"] + HOME_EDGE) - ra["rating"]) / 400))
    out = {"win": [], "handicap": [], "total": []}
    out["win"].append({"selection": home, "market": "Win match (2-way)", **fair(p_home)})
    out["win"].append({"selection": away, "market": "Win match (2-way)", **fair(1 - p_home)})

    lam_h = (rh["attack"] * ra["defence"] / league_avg) if league_avg else 0
    lam_a = (ra["attack"] * rh["defence"] / league_avg) if league_avg else 0
    if lam_h and lam_a:
        win, draw, loss, margin2, ph, pa = poisson_probs(lam_h, lam_a)
        p_reg_home = win + 0.5 * draw
        # handicap -1.5 for the favourite side, +1.5 for the other
        p_home_minus = margin2
        p_away_plus = 1 - margin2
        out["handicap"].append({"selection": f"{home} -1.5", "market": "Handicap", **fair(p_home_minus)})
        out["handicap"].append({"selection": f"{away} +1.5", "market": "Handicap", **fair(p_away_plus)})
        dist = total_dist(ph, pa)
        for line in lines:
            p_over = over_prob(dist, line)
            out["total"].append({"selection": f"Over {line}", "market": "Match total", **fair(p_over)})
            out["total"].append({"selection": f"Under {line}", "market": "Match total", **fair(1 - p_over)})
        out["_expected"] = {"home": round(lam_h, 2), "away": round(lam_a, 2), "total": round(lam_h + lam_a, 2)}
        out["_regulation"] = {"home": round(win, 4), "draw": round(draw, 4), "away": round(loss, 4)}
    return out


def main() -> int:
    official = json.loads((DATA / "official.json").read_text(encoding="utf-8"))
    matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))
    recs = official["records"]

    nhl_r = ratings_nhl(recs["nhl"])
    mlb_r = ratings_mlb(recs["mlb"])
    el_r = ratings_el(recs["euroleague"])
    avg_goals = sum(v["attack"] for v in nhl_r.values()) / max(len(nhl_r), 1)
    avg_runs = sum(v["attack"] for v in mlb_r.values()) / max(len(mlb_r), 1)
    avg_pts = sum(v["attack"] for v in el_r.values()) / max(len(el_r), 1)

    fixtures = []
    for f in official["fixtures"]:
        comp = f["competition"]
        if comp == "NHL":
            rh, ra, avg, lines = lookup(nhl_r, f["home"]), lookup(nhl_r, f["away"]), avg_goals, [5.5, 6.5]
        elif comp == "MLB":
            rh, ra, avg, lines = lookup(mlb_r, f["home"]), lookup(mlb_r, f["away"]), avg_runs, [7.5, 8.5]
        elif comp == "EuroLeague":
            rh, ra, avg, lines = lookup(el_r, f["home"]), lookup(el_r, f["away"]), avg_pts, [159.5, 163.5]
        else:
            continue
        if not rh or not ra:
            fixtures.append({**f, "markets": None, "note": "official record not found for one side: no line originated"})
            continue
        block = build_market_block(f["sport"], f["home"], f["away"], rh, ra, avg, lines)
        fixtures.append({
            **f,
            "markets": block,
            "inputs": {
                "home": {"record": rh["record"].get("name") or f["home"], "rating": round(rh["rating"], 1)},
                "away": {"record": ra["record"].get("name") or f["away"], "rating": round(ra["rating"], 1)},
                "league_average": round(avg, 2),
                "home_edge": HOME_EDGE,
            },
        })

    # attach our market block to the OLBG rows that matched an official fixture
    by_fixture = {x["fixture_id"]: x for x in fixtures if x.get("markets")}
    attached = 0
    for ev in matches["events"]:
        fid = ev.get("verify", {}).get("fixture_id")
        if fid and fid in by_fixture:
            ev["our_markets"] = by_fixture[fid]["markets"]
            ev["our_inputs"] = by_fixture[fid]["inputs"]
            attached += 1

    priced = [x for x in fixtures if x.get("markets")]
    selections = 0
    for x in priced:
        for group in ("win", "handicap", "total"):
            selections += len(x["markets"].get(group, []))

    out = {
        "meta": {
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "method": "see scripts/ledger_model.py header and the methodology page",
            "official_fixtures": len(official["fixtures"]),
            "fixtures_with_lines": len(priced),
            "fixtures_without_lines": len(official["fixtures"]) - len(priced),
            "selections": selections,
            "olbg_rows_with_our_lines": attached,
            "constants": {"home_edge_rating": HOME_EDGE},
        },
        "fixtures": fixtures,
    }
    (DATA / "lines.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    (DATA / "matches.json").write_text(json.dumps(matches, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["meta"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
