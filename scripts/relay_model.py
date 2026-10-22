#!/usr/bin/env python3
"""Originate prices for every /relay/ fixture (session arena/103d996c-olbg2).

Markets per fixture: match winner (2- or 3-way), handicap grid, match-total
grid - plus, for the F1 round, an outright race-winner market and a
head-to-head between the top two in the championship.

High-confidence gate (identical to METHODOLOGY.md and to the /current/ layer):
    model probability >= 0.7000  AND  fair American price inside -250 ... +10000
searched across every originated market and both sides.

Strength tables come from the official standings/summary captures named on each
row of data/relay/matches.json (class A read this session, class B carried over
verbatim - see relay_seed.py). No bookmaker price is read anywhere.

The distribution and price helpers are imported from scripts/current_model.py
so both layers share one tested implementation. Stdlib only. Deterministic.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from current_model import (BAND_MAX_PRICE, BAND_MIN_P, MEDIUM_P, NormalMargin,
                           PoissonGrid, SnookerBo7, half, in_band, label,
                           markets_for as _markets_for, price, rating)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURCAP = os.path.join(ROOT, "data", "current", "capture")
DATA = os.path.join(ROOT, "data", "relay")


def load(directory, name):
    with open(os.path.join(directory, name), encoding="utf-8") as handle:
        return json.load(handle)


def build_inputs():
    inputs = {}

    # --- NHL: 32-club official team summary (class B, 2026-10-21 snapshot) - #
    summary = load(CURCAP, "nhl_team_summary_2026-10-22.json")
    teams = summary["teams"]
    league = sum(t["gf"] for t in teams) / sum(t["gp"] for t in teams)
    rows = []
    for t in teams:
        w, atk, dfn = rating(t["gp"], t["gf"], t["ga"], league, 8.0)
        rows.append({"code": t["abbrev"], "team": t["team"], "gp": t["gp"], "w": t["w"],
                     "l": t["l"], "otl": t["otl"], "pts": t["pts"], "point_pct": t["pointPct"],
                     "gf": t["gf"], "ga": t["ga"], "gfpg": t["gfpg"], "gapg": t["gapg"],
                     "shrink": round(w, 4), "attack": round(atk, 4), "defence": round(dfn, 4)})
    inputs["nhl"] = {
        "league_avg_goals_per_team_game": round(league, 4), "clubs": rows,
        "source_url": summary["source_url"], "source_name": summary["source_name"],
        "snapshot_note": summary["snapshot_note"], "prior": 8.0, "home": 1.05,
        "model": "multiplicative Poisson on goals for/against, shrinkage gp/(gp+8), "
                 "home factor 1.05, regulation ties split 50/50 for overtime",
    }

    # --- EuroLeague: 20-club official standings (class B) ------------------- #
    el = load(CURCAP, "euroleague_round7_2026-10-22.json")
    league = sum(c["pts_for"] for c in el["standings"]) / sum(c["gp"] for c in el["standings"])
    rows = []
    for c in el["standings"]:
        w, atk, dfn = rating(c["gp"], c["pts_for"], c["pts_against"], league, 6.0)
        rows.append({"code": c["code"], "team": c["team"], "pos": c["pos"], "gp": c["gp"],
                     "w": c["w"], "l": c["l"], "win_pct": c["win_pct"], "pts_for": c["pts_for"],
                     "pts_against": c["pts_against"], "diff": c["diff"], "home": c["home"],
                     "away": c["away"], "l10": c["l10"], "shrink": round(w, 4),
                     "attack": round(atk, 4), "defence": round(dfn, 4)})
    inputs["euroleague"] = {
        "league_avg_points_per_team_game": round(league, 4), "clubs": rows,
        "source_url": el["source_url_standings"], "source_name": el["source_name"],
        "prior": 6.0, "home": 3.0, "sd_margin": 11.0, "sd_total": 15.0,
        "model": "attack/defence points model, shrinkage gp/(gp+6), +3.0 home points, "
                 "normal margin sd 11.0",
    }

    # --- URC: 16-club official table (class B) ------------------------------ #
    urc = load(CURCAP, "urc_table_2026-10-22.json")
    league = sum(t["pf"] for t in urc["table"]) / sum(t["pl"] for t in urc["table"])
    rows = []
    for t in urc["table"]:
        w, atk, dfn = rating(t["pl"], t["pf"], t["pa"], league, 6.0)
        rows.append({"team": t["team"], "pos": t["pos"], "pts": t["pts"], "pl": t["pl"],
                     "w": t["w"], "d": t["d"], "l": t["l"], "bp": t["bp"], "pf": t["pf"],
                     "pa": t["pa"], "diff": t["diff"], "tf": t["tf"], "ta": t["ta"],
                     "form": "".join(t["form"]), "shrink": round(w, 4),
                     "attack": round(atk, 4), "defence": round(dfn, 4)})
    inputs["urc"] = {
        "league_avg_points_per_team_game": round(league, 4), "clubs": rows,
        "source_url": urc["source_url"], "source_name": urc["source_name"],
        "round3_results": urc["round3_results"],
        "prior": 6.0, "home": 3.0, "sd_margin": 13.0, "sd_total": 16.0, "draw_band": 1.0,
        "model": "attack/defence points model, shrinkage pl/(pl+6), +3.0 home points, "
                 "normal margin sd 13.0, draw band +/-1 point",
    }

    # --- EHF Champions League: 24-club official group tables (class B) ------ #
    ehf = load(CURCAP, "ehf_standings_2026-10-22.json")
    total_gf = sum(c["goals_for"] for c in ehf["clubs"])
    total_gp = sum(c["gp"] for c in ehf["clubs"])
    total_ga = sum(c["goals_against"] for c in ehf["clubs"])
    league = total_gf / total_gp
    rows = []
    for c in ehf["clubs"]:
        w, atk, dfn = rating(c["gp"], c["goals_for"], c["goals_against"], league, 3.0)
        rows.append({"club": c["club"], "group": c["group"], "pos": c["pos"], "gp": c["gp"],
                     "w": c["w"], "d": c["d"], "l": c["l"], "pts": c["pts"],
                     "goals_for": c["goals_for"], "goals_against": c["goals_against"],
                     "diff": c["diff"], "shrink": round(w, 4),
                     "attack": round(atk, 4), "defence": round(dfn, 4)})
    inputs["ehf"] = {
        "league_avg_goals_per_team_game": round(league, 4), "clubs": rows,
        "goals_for_total": total_gf, "goals_against_total": total_ga, "games_total": total_gp,
        "source_url": ehf["source_url"], "source_name": ehf["source_name"],
        "prior": 3.0, "home": 0.4,
        "model": "attack/defence Poisson on goals, shrinkage gp/(gp+3), +/-0.4 home goals, "
                 "full score grid",
        "consistency_check": "goals_for_total equals goals_against_total across the 24 clubs, "
                             "as it must: %d v %d" % (total_gf, total_ga),
    }

    # --- MLB: 30-club official standings sample (class B) ------------------- #
    mlb = load(CURCAP, "mlb_standings_sample_2026-10-22.json")
    league = mlb["league_avg_runs_per_game"]
    rows = []
    for t in mlb["teams"]:
        w, atk, dfn = rating(t["gp"], t["runs_scored"], t["runs_allowed"], league, 20.0)
        rows.append({"team": t["team"], "team_id": t["team_id"], "league": t["league"],
                     "division": t["division"], "gp": t["gp"], "w": t["wins"], "l": t["losses"],
                     "win_pct": t["win_pct"], "rs": t["runs_scored"], "ra": t["runs_allowed"],
                     "diff": t["run_differential"], "shrink": round(w, 4),
                     "attack": round(atk, 4), "defence": round(dfn, 4)})
    inputs["mlb"] = {
        "league_avg_runs_per_team_game": league, "clubs": rows,
        "source_url": mlb["source_url"], "source_name": mlb["source_name"],
        "note": mlb["note"], "prior": 20.0, "home": 0.25,
        "model": "attack/defence Poisson on runs, shrinkage gp/(gp+20), +0.25 home runs, "
                 "ties split 50/50 for extra innings",
    }

    # --- F1: 23-driver official championship standings (class B) ------------ #
    f1 = load(CURCAP, "f1_calendar_2026-10-22.json")
    drivers = f1["drivers_standings"]
    total_pts = sum(d["pts"] for d in drivers)
    inputs["f1"] = {
        "field_points_total": total_pts,
        "drivers": [{"pos": d["pos"], "driver": d["driver"], "code": d["code"],
                     "team": d["team"], "pts": d["pts"],
                     "share": round(d["pts"] / total_pts, 4)} for d in drivers],
        "race_winners": f1["race_winners_first_hand"],
        "source_url": f1["source_url_drivers"], "source_name": f1["drivers_standings_source"],
        "calendar_url": f1["source_url"], "rounds_completed_note": f1["rounds_completed_note"],
        "model": "share-of-championship-points outright; head-to-head between the top two "
                 "by points share",
    }
    return inputs


def dist_for(match, inputs):
    sport = match["sport"]
    i = match["inputs"]

    if sport == "ice-hockey":
        cfg = inputs["nhl"]
        tbl = {c["code"]: c for c in cfg["clubs"]}
        h, a = tbl[i["home_abbrev"]], tbl[i["away_abbrev"]]
        lam = cfg["league_avg_goals_per_team_game"]
        lam_h = lam * h["attack"] * a["defence"] * cfg["home"]
        lam_a = lam * a["attack"] * h["defence"] / cfg["home"]
        return PoissonGrid(lam_h, lam_a, 12, settle_ties=True), {
            "family": "nhl", "tie": "split", "hc_natural": 1.5, "hc_radius": 2.0,
            "total_radius": 2.0, "expected_h": lam_h, "expected_a": lam_a,
            "ratings": {"home": h, "away": a}, "league_avg": lam}

    if sport == "basketball":
        cfg = inputs["euroleague"]
        tbl = {c["code"]: c for c in cfg["clubs"]}
        h, a = tbl[match["home"]["abbrev"]], tbl[match["away"]["abbrev"]]
        lam = cfg["league_avg_points_per_team_game"]
        exp_h = lam * h["attack"] * a["defence"] + cfg["home"]
        exp_a = lam * a["attack"] * h["defence"] - cfg["home"]
        return NormalMargin(exp_h - exp_a, cfg["sd_margin"], exp_h + exp_a, cfg["sd_total"]), {
            "family": "euroleague", "tie": "none", "hc_natural": None, "hc_radius": 6.0,
            "total_radius": 4.0, "expected_h": exp_h, "expected_a": exp_a,
            "ratings": {"home": h, "away": a}, "league_avg": lam}

    if sport == "rugby-union":
        cfg = inputs["urc"]
        tbl = {c["team"]: c for c in cfg["clubs"]}
        h, a = tbl[match["home"]["name"]], tbl[match["away"]["name"]]
        lam = cfg["league_avg_points_per_team_game"]
        exp_h = lam * h["attack"] * a["defence"] + cfg["home"]
        exp_a = lam * a["attack"] * h["defence"] - cfg["home"]
        return NormalMargin(exp_h - exp_a, cfg["sd_margin"], exp_h + exp_a,
                            cfg["sd_total"], cfg["draw_band"]), {
            "family": "urc", "tie": "draw", "hc_natural": None, "hc_radius": 7.0,
            "total_radius": 6.0, "expected_h": exp_h, "expected_a": exp_a,
            "ratings": {"home": h, "away": a}, "league_avg": lam}

    if sport == "handball":
        cfg = inputs["ehf"]
        tbl = {c["club"]: c for c in cfg["clubs"]}
        h, a = tbl[match["home"]["name"]], tbl[match["away"]["name"]]
        lam = cfg["league_avg_goals_per_team_game"]
        exp_h = lam * h["attack"] * a["defence"] + cfg["home"]
        exp_a = lam * a["attack"] * h["defence"] - cfg["home"]
        return PoissonGrid(exp_h, exp_a, 70), {
            "family": "ehf", "tie": "draw", "hc_natural": None, "hc_radius": 4.0,
            "total_radius": 4.0, "expected_h": exp_h, "expected_a": exp_a,
            "ratings": {"home": h, "away": a}, "league_avg": lam}

    if sport == "baseball":
        cfg = inputs["mlb"]
        tbl = {c["team_id"]: c for c in cfg["clubs"]}
        ws = load(os.path.join(ROOT, "data", "relay", "capture"), "mlb_world_series_2026-10-22.json")
        id_by_name = {}
        for g in ws["games"]:
            id_by_name[g["home"]["name"]] = g["home"]["id"]
            id_by_name[g["away"]["name"]] = g["away"]["id"]
        h = tbl[id_by_name[match["home"]["name"]]]
        a = tbl[id_by_name[match["away"]["name"]]]
        lam = cfg["league_avg_runs_per_team_game"]
        exp_h = lam * h["attack"] * a["defence"] + cfg["home"]
        exp_a = lam * a["attack"] * h["defence"] - cfg["home"]
        return PoissonGrid(exp_h, exp_a, 20, settle_ties=True), {
            "family": "mlb", "tie": "split", "hc_natural": 1.5, "hc_radius": 1.5,
            "total_radius": 2.0, "expected_h": exp_h, "expected_a": exp_a,
            "ratings": {"home": h, "away": a}, "league_avg": lam}

    return None, {"blank_reason": "No official strength input captured for this sport."}


def best_band(markets, mu, mu_t):
    """Most natural in-band selection: moneyline, then favourite handicap, then
    totals, then underdog-receiving handicap (rank 3, published only when
    nothing better exists)."""
    favourite = max(markets[0]["outcomes"], key=lambda o: o["p"])["side"]
    cands = []
    for m in markets:
        for o in m["outcomes"]:
            if not o.get("in_band"):
                continue
            if m["market"] == "match winner":
                rank, nat = 0, None
            elif m["market"] == "handicap":
                rank = 1 if o["side"] == favourite else 3
                nat = mu
            else:
                rank, nat = 2, mu_t
            gap = 0.0 if nat is None else abs(o["line"] - nat)
            cands.append({"rank": rank, "gap": round(gap, 3), "p": o["p"],
                          "market": m["market"],
                          "selection": o.get("selection", o.get("name", "")),
                          "line": o.get("line", ""), "posted": o.get("posted", ""),
                          "side": o["side"]})
    if not cands:
        return None, []
    cands.sort(key=lambda c: (c["rank"], c["gap"], round(-c["p"], 6), c["selection"]))
    best = cands[0]
    pick = {"market": best["market"], "selection": best["selection"], "line": best["line"],
            "p": best["p"], "fair_decimal": price(best["p"])["fair_decimal"],
            "fair_american": price(best["p"])["fair_american"], "confidence": "high",
            "side": best["side"], "posted": best["posted"], "rank": best["rank"]}
    return pick, [{
        "market": c["market"], "selection": c["selection"], "p": round(c["p"], 4),
        "fair_decimal": price(c["p"])["fair_decimal"],
        "fair_american": price(c["p"])["fair_american"], "rank": c["rank"]} for c in cands]


def originate_f1(match, inputs):
    cfg = inputs["f1"]
    total = cfg["field_points_total"]
    outrights = []
    for d in cfg["drivers"]:
        p = d["pts"] / total
        if p <= 0:
            continue
        entry = {"side": "driver", "selection": d["driver"], "line": "", "p": p,
                 "points": d["pts"], "pos": d["pos"], "team": d["team"]}
        entry.update(price(p))
        entry["in_band"] = in_band(entry["p"])
        entry["confidence"] = label(entry["p"], entry["in_band"])
        entry.pop("american_exact", None)
        outrights.append(entry)
    outrights.sort(key=lambda o: -o["p"])
    a, b = cfg["drivers"][0], cfg["drivers"][1]
    pa = a["pts"] / (a["pts"] + b["pts"])
    h2h = []
    for name, p in ((a["driver"], pa), (b["driver"], 1.0 - pa)):
        entry = {"side": "driver", "selection": name, "line": "", "p": p}
        entry.update(price(p))
        entry["in_band"] = in_band(entry["p"])
        entry["confidence"] = label(entry["p"], entry["in_band"])
        entry.pop("american_exact", None)
        h2h.append(entry)
    markets = [
        {"market": "race winner (outright)", "line": "", "outcomes": outrights},
        {"market": "head-to-head, top two in the championship", "line": "", "outcomes": h2h},
    ]
    best = max(outrights, key=lambda o: o["p"])
    band = None
    cands = [{"market": m["market"], "selection": o["selection"], "p": round(o["p"], 4),
              "fair_decimal": o["fair_decimal"], "fair_american": o["fair_american"]}
             for m in markets for o in m["outcomes"] if o["in_band"]]
    if cands:
        cands.sort(key=lambda c: -c["p"])
        band = dict(cands[0], confidence="high")
    return markets, {"expected_h": best["p"], "expected_a": 0.0}, band, cands, best


NHL_RECORD_CAVEAT = ("Strength table (GF/GA) is the official 2026-10-21 team-summary snapshot "
                     "carried over from the /current/ capture; the twelve games of 22 October "
                     "are not in it. W-L-OTL records beside class-A rows are as printed by the "
                     "official feed at 2026-10-22 20:56 UTC. Disclosed, not adjusted.")


def main():
    with open(os.path.join(DATA, "matches.json"), encoding="utf-8") as handle:
        seeded = json.load(handle)
    inputs = build_inputs()
    matches = seeded["matches"]

    rows, band_picks = [], []
    for m in matches:
        if m["kind"] == "event":
            markets, mu, band, cands, best = originate_f1(m, inputs)
            primary = {"market": "race winner (outright)", "selection": best["selection"],
                       "p": round(best["p"], 4), "fair_decimal": best["fair_decimal"],
                       "fair_american": best["fair_american"], "confidence": best["confidence"],
                       "note": "Share-of-championship-points outright. Crude by design and "
                               "labelled low/medium; no per-circuit model is claimed."}
            rows.append({"match_id": m["id"], "sport": m["sport"], "originated": True,
                         "primary": primary, "markets": markets, "band_pick": band,
                         "band_candidates": cands, "blank_reason": "",
                         "model": inputs["f1"]["model"]})
            if band:
                band_picks.append({"match_id": m["id"], "sport": m["sport"],
                                   "sport_name": m["sport_name"], "date": m["date"],
                                   "fixture": m["event"], "official_url": m["official_url"],
                                   "capture_file": m["capture_file"],
                                   "evidence": m["evidence"], **band})
            continue

        dist, cfg = dist_for(m, inputs)
        if dist is None:
            rows.append({"match_id": m["id"], "sport": m["sport"], "originated": False,
                         "primary": None, "markets": [], "band_pick": None,
                         "band_candidates": [], "blank_reason": cfg["blank_reason"],
                         "model": ""})
            continue

        markets, mu, mu_t = _markets_for(m, dist, cfg)
        band, cands = best_band(markets, mu, mu_t)
        mw = markets[0]["outcomes"]
        best = max(mw, key=lambda o: o["p"])
        if band:
            primary = {"market": band["market"], "selection": band["selection"],
                       "p": band["p"], "fair_decimal": band["fair_decimal"],
                       "fair_american": band["fair_american"], "confidence": "high",
                       "note": "In-band selection found by searching every originated market."}
        else:
            level = abs(mw[0]["p"] - mw[-1]["p"]) < 0.0005
            primary = {"market": "match winner", "selection": best["name"],
                       "p": round(best["p"], 4), "fair_decimal": best["fair_decimal"],
                       "fair_american": best["fair_american"], "confidence": best["confidence"],
                       "level": level,
                       "note": (("The captured inputs rate both sides identically: true coin "
                                 "flip, no model edge. " if level else "")
                                + "No originated market on either side reaches probability "
                                "0.70 inside the -250 to +10000 fair-price band, so the "
                                "strongest two-way opinion is published instead and capped "
                                "at %s." % best["confidence"])}
        rows.append({
            "match_id": m["id"], "sport": m["sport"], "originated": True,
            "primary": primary, "markets": markets, "band_pick": band,
            "band_candidates": cands, "blank_reason": "",
            "model": cfg["family"], "expected_home": round(cfg["expected_h"], 3),
            "expected_away": round(cfg["expected_a"], 3),
            "expected_margin": round(mu, 3), "expected_total": round(mu_t, 3),
            "league_avg": round(cfg.get("league_avg", 0.0), 4),
            "caveat": NHL_RECORD_CAVEAT if m["sport"] == "ice-hockey" else "",
        })
        if band:
            band_picks.append({
                "match_id": m["id"], "sport": m["sport"], "sport_name": m["sport_name"],
                "date": m["date"], "home": m["home"]["name"], "away": m["away"]["name"],
                "fixture": "%s v %s" % (m["home"]["name"], m["away"]["name"]),
                "competition": m["competition"], "venue": m["venue"],
                "time_note": m["time_note"], "official_url": m["official_url"],
                "capture_file": m["capture_file"], "source_name": m["source_name"],
                "evidence": m["evidence"],
                "expected_margin": round(mu, 3), "expected_total": round(mu_t, 3),
                "caveat": NHL_RECORD_CAVEAT if m["sport"] == "ice-hockey" else "",
                **band})

    counts = {
        "fixture_rows": len(matches),
        "originated_rows": sum(1 for r in rows if r["originated"]),
        "blank_rows": sum(1 for r in rows if not r["originated"]),
        "sports_with_rows": len({r["sport"] for r in rows if r["originated"]}),
        "band_picks": len(band_picks),
        "markets_originated": sum(len(r["markets"]) for r in rows),
        "prices_originated": sum(len(m["outcomes"]) for r in rows for m in r["markets"]),
        "high_confidence": sum(1 for r in rows if r["primary"] and r["primary"]["confidence"] == "high"),
        "medium_confidence": sum(1 for r in rows if r["primary"] and r["primary"]["confidence"] == "medium"),
        "low_confidence": sum(1 for r in rows if r["primary"] and r["primary"]["confidence"] == "low"),
    }

    def write(name, doc):
        with open(os.path.join(DATA, name), "w", encoding="utf-8") as handle:
            json.dump(doc, handle, indent=1, ensure_ascii=False)
            handle.write("\n")

    write("model_inputs.json", {"generated_by": "scripts/relay_model.py", "inputs": inputs})
    write("lines.json", {"generated_by": "scripts/relay_model.py", "counts": counts,
                         "gate": {"min_probability": BAND_MIN_P,
                                  "max_fair_american": BAND_MAX_PRICE,
                                  "min_fair_american": -250,
                                  "note": "p >= 0.70 AND fair no-vig American price inside "
                                          "-250 ... +10000, searched across every originated "
                                          "market and both sides."},
                         "rows": rows})
    write("band.json", {"generated_by": "scripts/relay_model.py", "counts": counts,
                        "selections": band_picks})

    print("relay_model OK:", json.dumps(counts))
    for p in band_picks:
        print("   BAND %-13s %-44s | %-32s p=%.4f dec=%.2f am=%+d" % (
            p["sport"], p["fixture"][:44], p["selection"][:32], p["p"],
            p["fair_decimal"], p["fair_american"]))


if __name__ == "__main__":
    main()
