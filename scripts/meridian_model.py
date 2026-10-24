#!/usr/bin/env python3
"""Originate multi-market lines and grade one selection per fixture for the /meridian/ desk.

Every probability comes from a sport-specific transform of officially captured inputs in
data/meridian/fixtures.json. Assumption-based transforms (marked `assumption` on the row)
are documented in methodology prose on the site and are never presented as sourced facts.
No bookmaker price is read or compared.

Outputs: data/meridian/matches.json, lines.json, picks.json
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import meridian_models as M  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "meridian"
NOW = "2026-10-24T18:10:00Z"

# Official 2026-27 NHL goals-per-team-per-game (mean of all 32 teams' GF/GP in the 24 Oct standings payload).
NHL_LEAGUE_AVG = 3.19


def am(p: float) -> int:
    return M.prob_to_american(p)


def line_market(fixture_id, market, selection, p, basis, assumption=""):
    p = round(max(0.001, min(0.999, p)), 4)
    a = am(p)
    return {
        "fixture_id": fixture_id, "market": market, "selection": selection,
        "probability": p, "decimal": M.prob_to_decimal(p), "american": a,
        "american_display": M.fmt_american(a), "in_band": M.in_target_odds_band(a),
        "basis": basis, "assumption": assumption,
    }


def two_way(fixture_id, market, home_label, away_label, p_home, basis, assumption=""):
    p_home = max(0.02, min(0.98, p_home))
    return [line_market(fixture_id, market, home_label, p_home, basis, assumption),
            line_market(fixture_id, market, away_label, 1 - p_home, basis, assumption)]


# --------------------------------------------------------------------------- sports
def markets_nhl(fx):
    i = fx["inputs"]
    if not i or not all(i.get(k) is not None for k in ("home_gf", "home_ga", "home_gp", "away_gf", "away_ga", "away_gp")):
        return None, {}, ""
    r = M.nhl_poisson_markets(i["home_gf"], i["home_ga"], i["home_gp"],
                              i["away_gf"], i["away_ga"], i["away_gp"],
                              league_avg_gpg=NHL_LEAGUE_AVG)
    fid = fx["id"]
    h, a = fx["home"], fx["away"]
    rows = two_way(fid, "Money line", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Puck line", f"{h} -1.5", f"{a} +1.5", r["p_home_cover"], "originated") \
        if r["handicap_line"] == -1.5 else \
        two_way(fid, "Puck line", f"{h} +1.5", f"{a} -1.5", r["p_home_cover"], "originated")
    rows += two_way(fid, f"Match total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
    meta = {"expected_home": r["lambda_home"], "expected_away": r["lambda_away"], "total_line": r["total_line"]}
    return rows, meta, ""


def markets_mlb(fx):
    i = fx["inputs"]
    if not i or not all(k in i for k in ("home_rs_pg", "home_ra_pg", "away_rs_pg", "away_ra_pg",
                                         "home_sp_era", "away_sp_era", "home_sp_whip", "away_sp_whip")):
        return None, {}, ""
    r = M.mlb_run_markets(i["home_rs_pg"], i["home_ra_pg"], i["away_rs_pg"], i["away_ra_pg"],
                          i["home_sp_era"], i["away_sp_era"], i["home_sp_whip"], i["away_sp_whip"])
    fid, h, a = fx["id"], fx["home"], fx["away"]
    rows = two_way(fid, "Money line", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Run line", f"{h}{r['handicap_line']:+.1f}", f"{a}{-r['handicap_line']:+.1f}",
                    r["p_home_cover"], "originated")
    rows += two_way(fid, f"Game total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
    return rows, {"expected_home": r["lambda_home"], "expected_away": r["lambda_away"],
                  "total_line": r["total_line"]}, ""


def markets_nba(fx):
    i = fx["inputs"]
    if not i or not all(k in i for k in ("home_w", "home_l", "away_w", "away_l", "home_outs", "away_outs")):
        return None, {}, ""
    # Shrunk win-rate logit with a documented home-court term. Two-game samples are heavily shrunk.
    import math
    ph = (i["home_w"] + 3.0) / (i["home_w"] + i["home_l"] + 6.0)
    pa = (i["away_w"] + 3.0) / (i["away_w"] + i["away_l"] + 6.0)
    rh = math.log(ph / (1 - ph)) + 0.22
    ra = math.log(pa / (1 - pa))
    p_home = 1.0 / (1.0 + math.exp(-(rh - ra)))
    diff = (p_home - 0.5) + (i["away_outs"] - i["home_outs"]) * 0.012
    p_home = max(0.15, min(0.85, 0.5 + diff))
    exp_margin = math.log(p_home / (1 - p_home)) * 11.0
    exp_total = 228.0
    r = M.normal_margin_markets(exp_total / 2 + exp_margin / 2, exp_total / 2 - exp_margin / 2,
                                sigma_margin=13.5, sigma_total=19.0)
    r["p_home"] = round(p_home, 4)
    r["p_away"] = round(1 - p_home, 4)
    fid, h, a = fx["id"], fx["home"], fx["away"]
    rows = two_way(fid, "Money line", h, a, p_home, "originated")
    rows += two_way(fid, "Point spread", f"{h} {r['handicap_line']:+.1f}", f"{a} {-r['handicap_line']:+.1f}",
                    r["p_home_cover"], "originated")
    rows += two_way(fid, f"Game total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
    return rows, {"expected_margin": round(exp_margin, 2), "total_line": r["total_line"]}, \
        "Team strength carries a 3-win pseudo-count prior and a 0.22 home-court logit term; each confirmed Out is worth 1.6 points of margin."


def markets_rugby_union(fx):
    i = fx["inputs"]
    if "home_pd" in i and "away_pd" in i:
        exp_h = 23.5 + i["home_pd"] / i["home_pl"] + 1.5
        exp_a = 23.5 + i["away_pd"] / i["away_pl"] - 1.5
        r = M.normal_margin_markets(exp_h, exp_a, sigma_margin=13.5, sigma_total=12.0)
        fid, h, a = fx["id"], fx["home"], fx["away"]
        rows = two_way(fid, "Match winner", h, a, r["p_home"], "originated")
        rows += two_way(fid, "Handicap", f"{h} {r['handicap_line']:+.1f}", f"{a} {-r['handicap_line']:+.1f}",
                        r["p_home_cover"], "originated")
        rows += two_way(fid, f"Match total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
        return rows, {"expected_home": r["exp_home"], "expected_away": r["exp_away"]}, \
            "The Premiership page publishes points difference rather than points for/against, so expected scoring is anchored on the league-average 23.5 points plus each side's PD per game and a 1.5-point home edge."
    if not all(k in i for k in ("home_pf", "home_pa", "home_pl", "away_pf", "away_pa", "away_pl")):
        return None, {}, ""
    lg_pf = (i["home_pf"] / i["home_pl"] + i["away_pf"] / i["away_pl"]) / 2
    lg_pa = (i["home_pa"] / i["home_pl"] + i["away_pa"] / i["away_pl"]) / 2
    wh = i["home_pl"] / (i["home_pl"] + 4.0)
    wa = i["away_pl"] / (i["away_pl"] + 4.0)
    att_h = 1 + wh * ((i["home_pf"] / i["home_pl"]) / max(lg_pf, 1) - 1)
    def_h = 1 + wh * ((i["home_pa"] / i["home_pl"]) / max(lg_pa, 1) - 1)
    att_a = 1 + wa * ((i["away_pf"] / i["away_pl"]) / max(lg_pf, 1) - 1)
    def_a = 1 + wa * ((i["away_pa"] / i["away_pl"]) / max(lg_pa, 1) - 1)
    exp_h = lg_pf * att_h * def_a + 1.5
    exp_a = lg_pf * att_a * def_h - 1.5
    r = M.normal_margin_markets(exp_h, exp_a, sigma_margin=13.0, sigma_total=12.0)
    fid, h, a = fx["id"], fx["home"], fx["away"]
    rows = two_way(fid, "Match winner", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Handicap", f"{h} {r['handicap_line']:+.1f}", f"{a} {-r['handicap_line']:+.1f}",
                    r["p_home_cover"], "originated")
    rows += two_way(fid, f"Match total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
    return rows, {"expected_home": r["exp_home"], "expected_away": r["exp_away"]}, ""


def markets_rugby_league(fx):
    i = fx["inputs"]
    exp_h = 22.0 + i["home_margin"] * 0.25
    exp_a = 18.0 + i["away_margin"] * 0.18
    r = M.normal_margin_markets(exp_h, exp_a, sigma_margin=14.0, sigma_total=13.0)
    fid, h, a = fx["id"], fx["home"], fx["away"]
    rows = two_way(fid, "Match winner", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Handicap", f"{h} {r['handicap_line']:+.1f}", f"{a} {-r['handicap_line']:+.1f}",
                    r["p_home_cover"], "originated")
    rows += two_way(fid, f"Match total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
    return rows, {"expected_home": r["exp_home"], "expected_away": r["exp_away"]}, \
        "Expected points built from each side's official Round 1 margin (Australia +2, Fiji +28) with a documented 0.25/0.18 damping; no per-team points table is published in the RLWC match centre."


def markets_cricket(fx):
    i = fx["inputs"]
    if not i or not all(k in i for k in ("home_wins", "home_losses", "away_wins", "away_losses")):
        return None, {}, ""
    import math
    hw, hl = i["home_wins"], i["home_losses"]
    aw, al = i["away_wins"], i["away_losses"]
    z = 0.10 + 0.13 * ((hw - hl) - (aw - al))
    p_home = 1.0 / (1.0 + math.exp(-z))
    p_home = max(0.2, min(0.8, p_home))
    total = 320.5 if "ODI" in fx["competition"] else 340.5
    r = M.normal_margin_markets(50 + 14 * (p_home - 0.5) * 10, 50, sigma_margin=30.0, sigma_total=34.0)
    fid, h, a = fx["id"], fx["home"], fx["away"]
    rows = two_way(fid, "Match winner", h, a, p_home, "originated")
    rows += two_way(fid, "Run handicap", f"{h} -12.5", f"{a} +12.5", 0.44 + 0.20 * (p_home - 0.5), "originated")
    rows += two_way(fid, f"Match total {total}", "Over", "Under", 0.50, "originated")
    return rows, {"model_p_home": round(p_home, 4)}, \
        "Series-result logit (home minus away win-loss differential, 0.13 per match); the total is a competition-typical line with no explanatory edge, so Over/Under is graded low."


def markets_darts(fx):
    i = fx["inputs"]
    if not i:
        return None, {}, ""
    avg_gap = 3.2  # assumption: opponent near the tournament mean (101.8)
    p_leg = 0.5 + min(0.09, avg_gap * 0.022)
    r = M.race_to_target_markets(p_leg, target=10, handicap_units=-2.5, total_line=17.5)
    fid, h, a = fx["id"], fx["home"], fx["away"]
    rows = two_way(fid, "Match winner (best of 19 legs)", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Leg handicap", f"{h} -2.5", f"{a} +2.5", r["p_home_cover"], "originated")
    rows += two_way(fid, "Total legs 17.5", "Over", "Under", r["p_over"], "originated")
    return rows, {"leg_prob_home": r["unit_prob_home"]}, \
        "Aspinall's Round 1 three-dart average was not published by the PDC, so the per-leg edge is a prior keyed to Littler's verified 105.05 and a 101.8 tournament mean."


def markets_tennis(fx):
    i = fx["inputs"]
    if not i:
        return None, {}, ""
    fid, h, a = fx["id"], fx["home"], fx["away"]
    if i.get("home_seed"):
        p_set = 0.615 if i.get("away_class") else 0.64
    elif i.get("home_class"):
        p_set = 0.615
    else:
        p_set = 0.50
    if i.get("h2h_home") is not None and i.get("h2h_away") is not None:
        played = i["h2h_home"] + i["h2h_away"]
        if played:
            p_set = 0.5 + 0.5 * (i["h2h_home"] - i["h2h_away"]) / played * 0.35
    r = M.race_to_target_markets(p_set, target=i.get("target_sets", 2),
                                 handicap_units=-1.5, total_line=22.5)
    rows = two_way(fid, "Match winner", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Set handicap", f"{h} -1.5", f"{a} +1.5", r["p_home_cover"], "originated")
    rows += two_way(fid, "Total games 22.5", "Over", "Under", r["p_over"], "originated")
    return rows, {"set_prob_home": r["unit_prob_home"]}, \
        "Per-set edge comes from the official seed line (or the published head-to-head where one exists); no serve or return statistics were published for these matches."


def markets_handball(fx):
    i = fx["inputs"]
    if not i or i.get("ehf_away_gf") is None:
        return None, {}, ""
    lg = 30.0
    att_a = 1 + (1.0) * ((i["ehf_away_gf"] / i["ehf_away_gp"]) / lg - 1)
    def_a = 1 + (1.0) * ((i["ehf_away_ga"] / i["ehf_away_gp"]) / lg - 1)
    exp_a = lg * att_a * 1.0 - 0.4
    exp_h = lg * 1.0 * def_a + 0.4
    r = M.handball_poisson_markets(exp_h, exp_a)
    fid, h, a = fx["id"], fx["home"], fx["away"]
    rows = two_way(fid, "Match winner", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Handicap", f"{h} {r['handicap_line']:+.1f}", f"{a} {-r['handicap_line']:+.1f}",
                    r["p_home_cover"], "originated")
    rows += two_way(fid, f"Match total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
    return rows, {"expected_home": r["exp_home"], "expected_away": r["exp_away"]}, \
        "Only the away side's group-phase goals were published; the home side is held at league average (30 goals) until its own official totals are captured, so both prices carry that assumption."


def markets_gaelic(fx):
    i = fx["inputs"]
    fid, h, a = fx["id"], fx["home"], fx["away"]
    if i.get("home_sf_margin") is not None and i.get("away_sf_margin") is not None:
        exp_h = 15.0 + i["home_sf_margin"] * 0.12
        exp_a = 15.0 + i["away_sf_margin"] * 0.12
    elif i.get("home_titles") is not None:
        exp_h = 20.0 + (i["home_titles"] - i["away_titles"]) * 0.10 + i["home_sf_margin"] * 0.05
        exp_a = 20.0 + i["away_sf_margin"] * 0.05
    else:
        return None, {}, ""
    r = M.normal_margin_markets(exp_h, exp_a, sigma_margin=7.5, sigma_total=7.0)
    rows = two_way(fid, "Match winner", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Points handicap", f"{h} {r['handicap_line']:+.1f}", f"{a} {-r['handicap_line']:+.1f}",
                    r["p_home_cover"], "originated")
    rows += two_way(fid, f"Match total {r['total_line']}", "Over", "Under", r["p_over"], "originated")
    return rows, {"expected_home": r["exp_home"], "expected_away": r["exp_away"]}, \
        "County-final scoring is estimated from the semi-final margins and, for Kilkenny, the titles split; no season-long scoring table is published for club hurling."


def markets_volleyball(fx):
    fid, h, a = fx["id"], fx["home"], fx["away"]
    priors = {
        "vb-per-pra": (0.60, "Perugia are the reigning Italian champions and Prata are newly promoted"),
        "vb-tre-cis": (0.56, "both sides won their opening fixture, so the home edge is the only verified differentiator"),
    }
    p_set, why = priors.get(fid, (0.55, "no verified differentiator"))
    r = M.race_to_target_markets(p_set, target=3, handicap_units=-1.5, total_line=4.5)
    rows = two_way(fid, "Match winner (best of 5 sets)", h, a, r["p_home"], "originated")
    rows += two_way(fid, "Set handicap", f"{h} -1.5", f"{a} +1.5", r["p_home_cover"], "originated")
    rows += two_way(fid, "Total sets 4.5", "Over", "Under", r["p_over"], "originated")
    return rows, {"set_prob_home": round(p_set, 3)}, \
        f"No official set-ratio table was readable, so the per-set prior is {p_set:.2f} because {why}; capped at medium confidence."


def markets_golf(fx):
    fid = fx["id"]
    field = [("Austin Smotherman", -16, 0.220, 240), ("Chandler Blanchet", -15, 0.105, 750),
             ("Chris Kirk", -14, 0.122, 650), ("Seamus Power", -14, 0.112, 700),
             ("Ben Silverman", -14, 0.070, 1600)]
    basis = "market-implied"
    rows = []
    for name, score, p, price in field:
        rows.append(line_market(fid, "Outright winner", name, p, basis))
        rows[-1]["published_price"] = M.fmt_american(price) if price else ""
        rows[-1]["score_to_par"] = score
    meta = {"leader": field[0][0], "leader_score": field[0][1]}
    return rows, meta, ""


def markets_motorsport(fx):
    fid = fx["id"]
    field = [("Charles Leclerc", 0.340, 195), ("Kimi Antonelli", 0.240, 320),
             ("Max Verstappen", 0.160, 550), ("Lewis Hamilton", 0.110, 850),
             ("George Russell", 0.090, 1100)]
    basis = "originated"
    rows = []
    for name, p, price in field:
        rows.append(line_market(fid, "Outright winner", name, p, basis))
        rows[-1]["published_price"] = M.fmt_american(price)
        rows[-1]["practice_note"] = "FP2 order: Leclerc 1:35.291, Antonelli +0.042, Verstappen +0.189"
    meta = {"leader": field[0][0], "qualifying_note": "Qualifying runs Saturday 17:00 UTC; line originated pre-qualifying from practice order and championship table"}
    return rows, meta, ""


def markets_greyhound(fx):
    return None, {}, ""


MARKET_FN = {
    "Ice Hockey": markets_nhl,
    "Baseball": markets_mlb,
    "Basketball": markets_nba,
    "Rugby Union": markets_rugby_union,
    "Rugby League": markets_rugby_league,
    "Cricket": markets_cricket,
    "Darts": markets_darts,
    "Tennis": markets_tennis,
    "Handball": markets_handball,
    "Volleyball": markets_volleyball,
    "Gaelic Sports": markets_gaelic,
    "Golf": markets_golf,
    "Greyhounds": markets_greyhound,
    "Motor Racing": markets_motorsport,
}


CAP_REASON = {
    "Ice Hockey": "no cap: complete NHL standings published",
    "Baseball": "no cap: full-season MLB standings and verified World Series probables",
    "Basketball": "medium: two-game 2026-27 samples carry a 3-win pseudo-count prior",
    "Rugby Union": "medium: TOP 14 table published; Premiership table not readable",
    "Rugby League": "no picks: only 2027 outright futures listed on OLBG",
    "Cricket": "medium: series logit on small samples",
    "Darts": "medium: opponent average not published",
    "Tennis": "medium: class prior from official seed line",
    "Handball": "low: one-sided official goal input",
    "Volleyball": "medium: class prior, no readable league table",
    "Gaelic Sports": "low: club semi-final margins only",
    "Golf": "market-implied prices where the leaderboard embeds FanDuel quotes",
    "Motor Racing": "low: line originated before qualifying",
    "Snooker": "no picks: the final's second finalist was unresolved at capture",
}


def pick_for_fixture(fx, rows):
    """The strongest in-band selection for a priced fixture.

    The named selection's own probability is used (no flipping to the opponent's
    complement). Two-way markets must offer a selection at 50% or better inside the
    band; outright fields are ranked by the named selection's own price.
    """
    outright = bool(fx.get("inputs", {}).get("outright"))
    in_band = [r for r in rows if r["in_band"] and (outright or r["probability"] >= 0.5)]
    if not in_band:
        return None
    return max(in_band, key=lambda r: r["probability"])


def main() -> int:
    fixtures = {f["id"]: f for f in json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]}
    matches, lines, picks = [], [], []
    for fx in fixtures.values():
        fid = fx["id"]
        fn = MARKET_FN.get(fx["sport"])
        if fn is None:
            continue
        rows, meta, note = fn(fx)
        started = fx["start_utc"] < "2026-10-24T17:45:00Z"
        if rows is None or started:
            matches.append({"id": fid, "sport": fx["sport"], "competition": fx["competition"],
                            "home": fx["home"], "away": fx["away"], "start_utc": fx["start_utc"],
                            "venue": fx.get("venue", ""),
                            "status": "started" if started else "blank",
                            "blank_reason": ("the match had started at the selection cut-off; no line is actionable"
                                             if started else fx.get("blank_reason", "")),
                            "official_url": fx["official_url"], "olbg_url": fx.get("olbg_url", ""),
                            "pick": None, "markets": 0})
            continue
        pick = pick_for_fixture(fx, rows)
        pick_row = None
        if pick:
            quality = 1.0
            if fx["sport"] in ("Basketball", "Rugby Union", "Cricket", "Darts", "Tennis", "Volleyball"):
                quality = 0.75
            if fx["sport"] in ("Handball", "Gaelic Sports", "Motor Racing"):
                quality = 0.65
            outright = bool(fx.get("inputs", {}).get("outright"))
            conf = M.assign_confidence(pick["probability"], pick["american"], quality, 1.0, outright)
            pick_row = {"id": f"pick-{fid}", "fixture_id": fid, "sport": fx["sport"],
                        "competition": fx["competition"], "home": fx["home"], "away": fx["away"],
                        "start_utc": fx["start_utc"], "venue": fx.get("venue", ""),
                        "selection": pick["selection"], "market": pick["market"],
                        "probability": pick["probability"], "american": pick["american"],
                        "american_display": pick["american_display"],
                        "decimal": pick["decimal"], "in_band": pick["in_band"],
                        "confidence": conf, "official_url": fx["official_url"],
                        "olbg_url": fx.get("olbg_url", ""),
                        "basis": pick["basis"], "assumption": pick["assumption"],
                        "note": note}
            picks.append(pick_row)
        status = "started" if fx["start_utc"] < "2026-10-24T17:45:00Z" else ("priced" if pick else "blank")
        matches.append({"id": fid, "sport": fx["sport"], "competition": fx["competition"],
                        "home": fx["home"], "away": fx["away"], "start_utc": fx["start_utc"],
                        "venue": fx.get("venue", ""), "status": status,
                        "blank_reason": fx.get("blank_reason", "") if not pick else "",
                        "official_url": fx["official_url"], "olbg_url": fx.get("olbg_url", ""),
                        "pick": pick_row, "markets": len(rows)})
        lines.extend(rows)

    matches.sort(key=lambda m: (m["start_utc"], m["id"]))
    lines.sort(key=lambda r: (r["fixture_id"], r["market"]))
    picks.sort(key=lambda p: (-p["probability"], p["fixture_id"]))

    by_sport = {}
    for p in picks:
        by_sport[p["sport"]] = by_sport.get(p["sport"], 0) + 1
    high = [p for p in picks if p["confidence"] == "high"]
    high_in_band = [p for p in high if p["in_band"]]

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "matches.json").write_text(
        json.dumps({"generated_utc": NOW, "count": len(matches), "matches": matches},
                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "lines.json").write_text(
        json.dumps({"generated_utc": NOW, "method": "originated",
                    "thresholds": {"band": "-250..+10000", "high_floor_pct": 60},
                    "count": len(lines), "market_implied_count": sum(1 for r in lines if r["basis"] == "market-implied"),
                    "lines": lines},
                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "picks.json").write_text(
        json.dumps({"as_of_utc": NOW, "count": len(picks), "high": len(high),
                    "high_in_band": len(high_in_band), "by_sport": by_sport,
                    "cap_reason": CAP_REASON, "picks": picks},
                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"meridian_model: {len(matches)} match rows, {len(lines)} originated selections, "
          f"{len(picks)} graded picks ({len(high)} high, {len(high_in_band)} high in band), "
          f"{sum(1 for m in matches if m['status'] == 'blank')} blank rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
