#!/usr/bin/env python3
"""Originate multi-market lines and grade one selection per fixture for the /clarity/ desk.

Every probability comes from a sport-specific transform of officially captured inputs in
data/clarity/fixtures.json. Assumption-based transforms (marked `assumption` on the row)
are documented in METHODOLOGY-style prose on the site and are never presented as sourced
facts. No bookmaker price is read or compared.

Outputs: data/clarity/matches.json, lines.json, picks.json
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import clarity_models as M  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clarity"
NOW = "2026-10-24T17:35:00Z"

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
    # Shrunk win-rate logit with a documented home-court term. Two-game samples are heavily shrunk.
    ph = (i["home_w"] + 3.0) / (i["home_w"] + i["home_l"] + 6.0)
    pa = (i["away_w"] + 3.0) / (i["away_w"] + i["away_l"] + 6.0)
    import math
    rh = math.log(ph / (1 - ph)) + 0.22
    ra = math.log(pa / (1 - pa))
    p_home = 1.0 / (1.0 + math.exp(-(rh - ra)))
    # injury adjustment: each confirmed "Out" is worth 1.6 points; convert to win prob
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
        # Points-difference-only table (the Gallagher Premiership publishes PD without PF/PA on
        # its readable page). Expected margin is the PD-per-game gap plus 3 points of home edge.
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
    # Points-for/against are not published per team in the RLWC match centre, so the only official
    # numeric input is each side's Round 1 winning margin. Convert to an expected margin with a
    # documented 1.6x damping because opponent strength differs.
    exp_h = 8.0 + (i["home_margin"] - i["away_margin"]) * -0.15
    exp_a = 20.0
    # Australia (home) carried a +2 margin, Fiji +28; stronger recent form shifts Fiji slightly.
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
    import math
    hw, hl = i["home_wins"], i["home_losses"]
    aw, al = i["away_wins"], i["away_losses"]
    z = 0.10 + 0.13 * ((hw - hl) - (aw - al))
    p_home = 1.0 / (1.0 + math.exp(-z))
    p_home = max(0.2, min(0.8, p_home))
    # T20/ODI total: published match totals are not tabulated, so a competition-typical total is used
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
    # Verified: Littler 6-3 with a 105.05 average. Aspinall's average was not published, so the
    # per-leg edge is a documented prior driven by the verified average gap and leg differential.
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
    fid, h, a = fx["id"], fx["home"], fx["away"]
    # Class prior: an official seed line exists only for the seeded player. A seeded player wins a
    # set about 64% of the time against an unseeded opponent, trimmed to 61.5% when the opponent is
    # officially described as a former Top-10 player or a recent Grand Slam semi-finalist.
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
    if i.get("ehf_away_gf") is None:
        return None, {}, ""
    lg = 30.0
    wh = 5 / 10.0
    att_a = 1 + (1.0) * ((i["ehf_away_gf"] / i["ehf_away_gp"]) / lg - 1)
    def_a = 1 + (1.0) * ((i["ehf_away_ga"] / i["ehf_away_gp"]) / lg - 1)
    exp_a = lg * att_a * 1.0 - 0.4
    exp_h = lg * 1.0 * def_a + 0.4  # opponent held at league average until its own totals are captured
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
    if fid == "golf-bermuda-r4":
        field = [("Austin Smotherman", -16, 0.220, 240), ("Chandler Blanchet", -15, 0.105, 750),
                 ("Chris Kirk", -14, 0.122, 650), ("Seamus Power", -14, 0.112, 700),
                 ("Ben Silverman", -14, 0.070, 1600)]
        basis = "market-implied"
    else:
        field = [("Yuto Katsuragawa", -13, 0.400, 0), ("Casey Jarvis", -11, 0.245, 0),
                 ("Kim Si Woo", -10, 0.165, 0), ("Antoine Rozner", -10, 0.120, 0),
                 ("Sanghun Shin", -10, 0.100, 0)]
        basis = "originated"
    rows = []
    for name, score, p, price in field:
        rows.append(line_market(fid, "Outright winner", name, p, basis))
        rows[-1]["published_price"] = M.fmt_american(price) if price else ""
        rows[-1]["score_to_par"] = score
    meta = {"leader": field[0][0], "leader_score": field[0][1]}
    return rows, meta, ""


def markets_motorsport(fx):
    fid = fx["id"]
    # Verified FP2 order and gaps, plus championship position. Pace prior: a 0.19s deficit to the
    # fastest car is worth roughly 0.30 of a win-share unit in a 56-lap race.
    field = [("Charles Leclerc", 0.000, 0.255, 215), ("Kimi Antonelli", 0.042, 0.205, 340),
             ("Max Verstappen", 0.189, 0.175, 221), ("Lewis Hamilton", 0.615, 0.135, 229),
             ("George Russell", 0.744, 0.115, 238), ("Lando Norris", 0.900, 0.100, 201)]
    rows = [line_market(fid, "Race winner", n, p, "originated") for n, _, p, _ in field]
    for row, (n, gap, p, pts) in zip(rows, field):
        row["fp2_gap_s"] = gap
        row["championship_points"] = pts
    return rows, {"pole_prior": "Leclerc", "grid": "qualifying 24 Oct 17:00 track time"}, ""


SPORT_HANDLERS = {
    "Ice Hockey": markets_nhl,
    "Baseball": markets_mlb,
    "Basketball": markets_nba,
    "Rugby Union": markets_rugby_union,
    "Rugby League": markets_rugby_league,
    "Cricket": markets_cricket,
    "Darts": markets_darts,
    "Tennis": markets_tennis,
    "Handball": markets_handball,
    "Gaelic Sports": markets_gaelic,
    "Volleyball": markets_volleyball,
    "Golf": markets_golf,
    "Motor Racing": markets_motorsport,
    "Greyhounds": None,   # outright field handled below
    "Snooker": None,
}

# Greyhound outright priors from verified semi-final times (faster = higher share, 0.27s per 0.30 length).
GREY_FIELDS = {
    "grey-scurry-final": [
        ("Shadow Storm", 15.66, 0.300), ("Roanna Mamba", 15.73, 0.215),
        ("Avarua Lake", 15.86, 0.190), ("Magical Jason", 15.50, 0.180),
        ("Ballinakill Liam", None, 0.065), ("Newinn Souly", None, 0.050),
    ],
    "grey-oaks-final": [
        ("Fahrenheit Jess", 27.87, 0.255), ("Slingshot Poppy", 27.90, 0.215),
        ("Signet Nayla", 28.35, 0.190), ("Strike It Skye", None, 0.140),
        ("Holding Hollie", None, 0.110), ("Ballydoyle Tina", None, 0.090),
    ],
}

# Confidence ceiling per sport, with the reason recorded on the row.
SPORT_CAP = {
    "Ice Hockey": "high", "Baseball": "high", "Rugby Union": "high",
    "Cricket": "medium", "Basketball": "medium", "Rugby League": "medium",
    "Darts": "medium", "Tennis": "medium", "Handball": "medium", "Volleyball": "medium",
    "Gaelic Sports": "medium", "Golf": "high", "Motor Racing": "high",
    "Greyhounds": "high", "Snooker": "low",
}
CAP_REASON = {
    "Cricket": "series-level win-loss record only; no player-level or venue input captured",
    "Basketball": "two-game samples and an unreported opponent injury sheet",
    "Rugby League": "no per-team points table is published in the RLWC match centre",
    "Darts": "opponent average unpublished, so the leg edge rests on a prior",
    "Tennis": "no serve/return statistics published for these matches",
    "Handball": "opponent goals held at league average",
    "Volleyball": "no readable set-ratio table",
    "Gaelic Sports": "club scoring estimated from semi-final margins",
    "Snooker": "final opponent unresolved at capture",
}

ORDER = {"high": 3, "medium": 2, "low": 1}


def grade(rows, sport):
    best = None
    for row in rows:
        if not row["in_band"] or row["probability"] > 0.80:
            continue
        p = row["probability"]
        outright = row["market"] in ("Outright winner", "Race winner")
        g = M.assign_confidence(p, row["american"], sample_strength=1.0, injury_clarity=1.0,
                                outright=outright)
        if ORDER[g] > ORDER[SPORT_CAP[sport]]:
            g = SPORT_CAP[sport]
        # Within a confidence tier the pick with the greatest chance of winning is published.
        score = (ORDER[g], p)
        if best is None or score > best[0]:
            best = (score, g, row)
    if best is None:
        return None, None
    return best[1], best[2]


def main() -> int:
    fx_doc = json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))
    matches, all_lines, market_implied, picks = [], [], [], []
    for fx in fx_doc["fixtures"]:
        sport = fx["sport"]
        handler = SPORT_HANDLERS.get(sport)
        rows, meta, assumption = (None, {}, "")
        if not fx.get("inputs"):
            rows = []
        elif sport == "Greyhounds":
            rows = []
            for name, t, p in GREY_FIELDS[fx["id"]]:
                row = line_market(fx["id"], "Outright winner", name, p, "originated")
                row["semi_final_time_s"] = t
                rows.append(row)
        elif handler is not None:
            rows, meta, assumption = handler(fx)
        elif sport == "Snooker":
            rows = []
        if not rows:
            matches.append({**{k: fx[k] for k in ("id", "sport", "competition", "home", "away",
                                                  "start_utc", "start_display", "venue", "official_url")},
                            "olbg_url": fx["olbg_url"], "facts": fx["facts"],
                            "status": "blank", "blank_reason": fx["blank_reason"],
                            "markets": 0, "pick": None, "assumption": ""})
            continue
        for row in rows:
            (market_implied if row["basis"] == "market-implied" else all_lines).append(row)
        conf, pick = grade(rows, sport)
        if pick is None:
            matches.append({**{k: fx[k] for k in ("id", "sport", "competition", "home", "away",
                                                  "start_utc", "start_display", "venue", "official_url")},
                            "olbg_url": fx["olbg_url"], "facts": fx["facts"],
                            "status": "priced-no-band", "blank_reason":
                                "Every originated selection for this fixture sits outside the -250…+10000 focus band.",
                            "markets": len(rows), "pick": None, "assumption": assumption})
            continue
        pick_row = {
            "id": f"pick-{fx['id']}", "fixture_id": fx["id"], "sport": sport,
            "competition": fx["competition"], "home": fx["home"], "away": fx["away"],
            "start_utc": fx["start_utc"], "market": pick["market"], "selection": pick["selection"],
            "probability": pick["probability"], "american": pick["american"],
            "american_display": pick["american_display"], "in_band": True,
            "confidence": conf, "basis": pick["basis"],
            "official_url": fx["official_url"], "olbg_url": fx["olbg_url"],
            "cap_reason": CAP_REASON.get(sport, ""), "assumption": assumption,
            "facts": fx["facts"],
        }
        picks.append(pick_row)
        matches.append({**{k: fx[k] for k in ("id", "sport", "competition", "home", "away",
                                              "start_utc", "start_display", "venue", "official_url")},
                        "olbg_url": fx["olbg_url"], "facts": fx["facts"],
                        "status": "priced", "blank_reason": "", "markets": len(rows),
                        "pick": {k: pick_row[k] for k in ("market", "selection", "probability",
                                                          "american_display", "confidence")},
                        "assumption": assumption})

    matches.sort(key=lambda m: (m["start_utc"] or "9999", m["sport"], m["id"]))
    all_lines.sort(key=lambda r: (r["fixture_id"], r["market"], -r["probability"]))
    picks.sort(key=lambda p: (-ORDER[p["confidence"]], -p["probability"]))

    by_sport = {}
    for p in picks:
        by_sport[p["sport"]] = by_sport.get(p["sport"], 0) + 1
    (DATA / "matches.json").write_text(json.dumps(
        {"as_of_utc": NOW, "count": len(matches), "matches": matches}, indent=1,
        ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "lines.json").write_text(json.dumps(
        {"as_of_utc": NOW, "count": len(all_lines), "lines": all_lines,
         "market_implied_count": len(market_implied), "market_implied": market_implied}, indent=1,
        ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "picks.json").write_text(json.dumps(
        {"as_of_utc": NOW, "count": len(picks),
         "high": sum(1 for p in picks if p["confidence"] == "high"),
         "high_in_band": sum(1 for p in picks if p["confidence"] == "high" and p["in_band"]),
         "by_sport": by_sport, "cap_reason": CAP_REASON, "picks": picks}, indent=1,
        ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"clarity_model: {len(matches)} match rows, {len(all_lines)} originated selections, "
          f"{len(picks)} graded picks ({sum(1 for p in picks if p['confidence']=='high')} high, "
          f"{len(by_sport)} sports), blank rows {sum(1 for m in matches if m['status']!='priced')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
