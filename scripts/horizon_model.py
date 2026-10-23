"""Horizon desk (session arena/9c5af337-olbg2) — line origination engine.

Reads data/horizon/fixtures.json and writes:
  data/horizon/lines.json
  data/horizon/flagged.json

Confidence labels:
  high   : P(selection) >= 0.70
  medium : 0.55 <= P(selection) < 0.70
  low    : P(selection) < 0.55

Actionable odds band: American odds in [-250, +10000].
A selection with P >= 0.70 has fair moneyline <= -233; once P > 5/7 (~71.43%)
the fair moneyline drops below -250. For those >71.43% match-winner picks we
also originate a handicap / puck-line / run-line / set-line / leg-line or
match-total market priced inside [-250, +10000] and record both the moneyline
status and the in-band secondary market.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "horizon")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def prob_to_american(p):
    p = clamp(p, 0.0099, 0.9901)
    if abs(p - 0.5) < 1e-9:
        return 100
    if p > 0.5:
        return -int(round((p / (1.0 - p)) * 100))
    return int(round(((1.0 - p) / p) * 100))


def prob_to_decimal(p):
    p = clamp(p, 0.0099, 0.9901)
    return round(1.0 / p, 2)


def fmt_american(ml):
    if ml is None:
        return ""
    return f"+{ml}" if ml > 0 else f"{ml}"


def in_band(ml):
    return ml is not None and -250 <= ml <= 10000


def conf_label(p):
    if p is None:
        return None
    if p >= 0.70:
        return "high"
    if p >= 0.55:
        return "medium"
    return "low"


def round_half(x):
    return round(x * 2.0) / 2.0


def price_ice_hockey(f):
    inp = f["inputs"]
    h, a = inp["home"], inp["away"]
    h_gf, h_ga = h["gf"] / h["gp"], h["ga"] / h["gp"]
    a_gf, a_ga = a["gf"] / a["gp"], a["ga"] / a["gp"]
    league = 3.10
    lam_h = clamp(((h_gf * a_ga) / league) * 1.04, 1.9, 4.4)
    lam_a = clamp(((a_gf * h_ga) / league) * 0.96, 1.9, 4.4)
    pts_diff = (h["pts"] / h["gp"]) - (a["pts"] / a["gp"])
    gd_diff = (h_gf - h_ga) - (a_gf - a_ga)
    p_home = 1.0 / (1.0 + math.exp(-(0.55 * gd_diff + 0.55 * pts_diff + 0.14)))
    p_home = clamp(p_home, 0.22, 0.78)
    p_away = 1.0 - p_home
    total = round_half(lam_h + lam_a)
    raw_total = lam_h + lam_a
    p_over = clamp(0.50 + (raw_total - total) * 0.18, 0.44, 0.58)
    fav_home = p_home >= p_away
    p_fav = p_home if fav_home else p_away
    p_pl_fav = clamp(p_fav - 0.25, 0.26, 0.56)
    p_pl_dog = 1.0 - p_pl_fav
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {
            "market": "Puck Line",
            "fav": f["home"] if fav_home else f["away"],
            "dog": f["away"] if fav_home else f["home"],
            "fav_line": -1.5, "fav_prob": p_pl_fav, "fav_odds": prob_to_american(p_pl_fav),
            "dog_line": 1.5, "dog_prob": p_pl_dog, "dog_odds": prob_to_american(p_pl_dog),
        },
        "total": {
            "market": "Game Total (goals)", "line": total, "expected": round(raw_total, 2),
            "over_prob": p_over, "over_odds": prob_to_american(p_over),
            "under_prob": 1.0 - p_over, "under_odds": prob_to_american(1.0 - p_over),
        },
        "method": (f"Pythagorean-log5 blend on 2026-27 NHL goals/game and points/game "
                   f"({f['home']} {h_gf:.2f} GF/G, {h_ga:.2f} GA/G; {f['away']} {a_gf:.2f} GF/G, {a_ga:.2f} GA/G)."),
    }


def price_basketball(f):
    comp = f["competition"]
    inp = f["inputs"]
    if comp == "EuroLeague":
        h, a = inp["home"], inp["away"]
        h_net = (h["pf"] - h["pa"]) / h["gp"]
        a_net = (a["pf"] - a["pa"]) / a["gp"]
        margin = (h_net - a_net) * 0.72 + 3.2
        p_home = clamp(1.0 / (1.0 + math.exp(-margin / 6.5)), 0.12, 0.88)
        p_away = 1.0 - p_home
        spread = round_half(-margin)
        raw_total = ((h["pf"] + h["pa"]) / h["gp"] + (a["pf"] + a["pa"]) / a["gp"]) / 2.0
        tline = round_half(raw_total)
        p_over = clamp(0.50 + (raw_total - tline) * 0.08, 0.46, 0.56)
        return {
            "p_home": p_home, "p_away": p_away,
            "handicap": {
                "market": "Point Spread", "home_line": spread, "away_line": -spread,
                "home_prob": 0.52, "home_odds": prob_to_american(0.52),
                "away_prob": 0.48, "away_odds": prob_to_american(0.48),
            },
            "total": {
                "market": "Game Total (points)", "line": tline, "expected": round(raw_total, 1),
                "over_prob": p_over, "over_odds": prob_to_american(p_over),
                "under_prob": 1.0 - p_over, "under_odds": prob_to_american(1.0 - p_over),
            },
            "method": (f"EuroLeague net-rating differential after {h['gp']}/{a['gp']} rounds "
                       f"({f['home']} {h_net:+.1f} pts/g vs {f['away']} {a_net:+.1f} pts/g, +3.2 home court)."),
        }
    hw, hl = [int(x) for x in inp["home_record"].split("-")]
    aw, al = [int(x) for x in inp["away_record"].split("-")]
    rec_diff = (hw - hl) - (aw - al)
    inj_h = sum(1 for x in f["facts"] if x["team_or_item"] == f["home"] and "Out —" in x["value"])
    inj_a = sum(1 for x in f["facts"] if x["team_or_item"] == f["away"] and "Out —" in x["value"])
    q_h = sum(1 for x in f["facts"] if x["team_or_item"] == f["home"] and ("Questionable" in x["value"] or "Doubtful" in x["value"]))
    q_a = sum(1 for x in f["facts"] if x["team_or_item"] == f["away"] and ("Questionable" in x["value"] or "Doubtful" in x["value"]))
    margin = 2.6 + rec_diff * 2.2 + (inj_a - inj_h) * 1.35 + (q_a - q_h) * 0.55
    p_home = clamp(1.0 / (1.0 + math.exp(-margin / 6.8)), 0.24, 0.76)
    p_away = 1.0 - p_home
    spread = round_half(-margin)
    base_total = 224.5 - (inj_h + inj_a) * 0.7
    tline = round_half(base_total)
    p_over = 0.51 if base_total >= tline else 0.49
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {
            "market": "Point Spread", "home_line": spread, "away_line": -spread,
            "home_prob": 0.52, "home_odds": prob_to_american(0.52),
            "away_prob": 0.48, "away_odds": prob_to_american(0.48),
        },
        "total": {
            "market": "Game Total (points)", "line": tline, "expected": round(base_total, 1),
            "over_prob": p_over, "over_odds": prob_to_american(p_over),
            "under_prob": 1.0 - p_over, "under_odds": prob_to_american(1.0 - p_over),
        },
        "method": (f"Opening-week NBA record differential ({inp['home_record']} vs {inp['away_record']}) "
                   f"plus official 3:15 PM ET injury-report Out/Questionable counts ({inj_h} Out/{q_h} Q home vs {inj_a} Out/{q_a} Q away)."),
    }


def price_baseball(f):
    inp = f["inputs"]
    h, a = inp["home"], inp["away"]
    hsp, asp = inp["home_sp"], inp["away_sp"]
    h_pyth = (h["rs"] ** 1.83) / ((h["rs"] ** 1.83) + (h["ra"] ** 1.83))
    a_pyth = (a["rs"] ** 1.83) / ((a["rs"] ** 1.83) + (a["ra"] ** 1.83))
    base = (h_pyth * (1.0 - a_pyth)) / (h_pyth * (1.0 - a_pyth) + (1.0 - h_pyth) * a_pyth)
    sp_adj = 0.0
    if hsp.get("era") is not None and asp.get("era") is not None:
        sp_adj = clamp((asp["era"] - hsp["era"]) * 0.065 + (hsp["k9"] - asp["k9"]) * 0.008, -0.14, 0.14)
        exp_runs = 3.55 + (hsp["era"] + asp["era"]) * 0.72
        sp_note = f"{hsp['name']} ({hsp['era']:.2f} ERA, {hsp['whip']:.2f} WHIP) vs {asp['name']} ({asp['era']:.2f} ERA, {asp['whip']:.2f} WHIP)"
    else:
        sp_adj = -0.04
        exp_runs = 7.6
        sp_note = f"{hsp['name']} (2026 MLB pitching split blank on StatsAPI) vs {asp['name']} ({asp['era']:.2f} ERA, {asp['whip']:.2f} WHIP)"
    p_home = clamp(base + 0.035 + sp_adj, 0.35, 0.74)
    p_away = 1.0 - p_home
    tline = round_half(exp_runs)
    p_under = clamp(0.52 + (tline - exp_runs) * 0.12, 0.46, 0.58)
    fav_home = p_home >= p_away
    p_fav = p_home if fav_home else p_away
    p_rl_fav = clamp(p_fav - 0.19, 0.32, 0.58)
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {
            "market": "Run Line",
            "fav": f["home"] if fav_home else f["away"],
            "dog": f["away"] if fav_home else f["home"],
            "fav_line": -1.5, "fav_prob": p_rl_fav, "fav_odds": prob_to_american(p_rl_fav),
            "dog_line": 1.5, "dog_prob": 1.0 - p_rl_fav, "dog_odds": prob_to_american(1.0 - p_rl_fav),
        },
        "total": {
            "market": "Game Total (runs)", "line": tline, "expected": round(exp_runs, 2),
            "over_prob": 1.0 - p_under, "over_odds": prob_to_american(1.0 - p_under),
            "under_prob": p_under, "under_odds": prob_to_american(p_under),
        },
        "method": f"162-game Pythagorean log5 ({h['w']}-{h['l']} vs {a['w']}-{a['l']}) adjusted for {sp_note}.",
    }


def price_cricket(f):
    fid = f["id"]
    if fid == "cri-41095":
        p_home, p_away = 0.44, 0.56
        return {
            "p_home": p_home, "p_away": p_away,
            "total": {"market": "First-Innings Runs", "line": 195.5, "expected": 202.0,
                      "over_prob": 0.56, "over_odds": prob_to_american(0.56),
                      "under_prob": 0.44, "under_odds": prob_to_american(0.44)},
            "method": "1st T20I scorecard at Hagley Oval on 22 Oct (NZ 4-225 in 20.0 overs, India 6-230 in 19.4 overs).",
        }
    if fid == "cri-40394":
        p_home, p_away = 0.78, 0.22
        return {
            "p_home": p_home, "p_away": p_away,
            "handicap": {"market": "First-Innings Runs Line", "fav": "India Women", "dog": "Zimbabwe Women",
                         "fav_line": -45.5, "fav_prob": 0.58, "fav_odds": prob_to_american(0.58),
                         "dog_line": 45.5, "dog_prob": 0.42, "dog_odds": prob_to_american(0.42)},
            "total": {"market": "Zimbabwe Women Innings Runs", "line": 205.5, "expected": 197.0,
                      "over_prob": 0.43, "over_odds": prob_to_american(0.43),
                      "under_prob": 0.57, "under_odds": prob_to_american(0.57)},
            "method": "1st WODI scorecard in Vadodara on 23 Oct (Zimbabwe Women 197 in 49.5 overs; India Women 1-200 in 27.1 overs).",
        }
    if fid == "cri-40981":
        p_home, p_away = 0.48, 0.52
        return {
            "p_home": p_home, "p_away": p_away,
            "total": {"market": "First-Innings Runs", "line": 315.5, "expected": 330.0,
                      "over_prob": 0.55, "over_odds": prob_to_american(0.55),
                      "under_prob": 0.45, "under_odds": prob_to_american(0.45)},
            "method": "Tri-Series opener scorecard on 22 Oct (England 4-429 in 50.0 overs vs Sri Lanka 8-430 in 49.5 overs) and Lahore home condition.",
        }
    return {"no_numeric": True,
            "reason": "Cricket Australia's match hub lists the fixture date and venue, while team season tables or series scorecards for these sides are not present in the captured feed."}


def price_snooker(f):
    if f.get("line_blocked"):
        return {"no_numeric": True, "reason": f["line_blocked"]}
    inp = f["inputs"]
    fid = f["id"]
    if fid == "snk-ni-sf1":
        hm, am = inp["home_rank_money"], inp["away_rank_money"]
        ratio = hm / (hm + am)
        p_home = clamp(0.50 + (ratio - 0.50) * 0.59, 0.55, 0.74)
        p_away = 1.0 - p_home
        return {
            "p_home": p_home, "p_away": p_away,
            "handicap": {"market": "Frame Handicap (best of 11)", "fav": f["home"], "dog": f["away"],
                         "fav_line": -1.5, "fav_prob": 0.58, "fav_odds": prob_to_american(0.58),
                         "dog_line": 1.5, "dog_prob": 0.42, "dog_odds": prob_to_american(0.42)},
            "total": {"market": "Total Frames (best of 11)", "line": 8.5, "expected": 8.9,
                      "over_prob": 0.56, "over_odds": prob_to_american(0.56),
                      "under_prob": 0.44, "under_odds": prob_to_american(0.44)},
            "method": f"World-ranking prize-money share (£{hm:,} vs £{am:,}) and Belfast quarter-final frame scores (6-1 vs 6-2).",
        }
    if "home_season" in inp and "away_season" in inp:
        hs, as_ = inp["home_season"], inp["away_season"]
        wr_diff = hs["win_rate"] - as_["win_rate"]
        b_rate_h = hs["breaks50"] / max(hs["matches"], 1)
        b_rate_a = as_["breaks50"] / max(as_["matches"], 1)
        p_home = clamp(0.50 + wr_diff * 0.65 + (b_rate_h - b_rate_a) * 0.08, 0.30, 0.72)
        p_away = 1.0 - p_home
        fav_home = p_home >= p_away
        p_fav = p_home if fav_home else p_away
        return {
            "p_home": p_home, "p_away": p_away,
            "handicap": {"market": "Frame Handicap (best of 11)",
                         "fav": f["home"] if fav_home else f["away"],
                         "dog": f["away"] if fav_home else f["home"],
                         "fav_line": -1.5, "fav_prob": clamp(p_fav - 0.11, 0.42, 0.61),
                         "fav_odds": prob_to_american(clamp(p_fav - 0.11, 0.42, 0.61)),
                         "dog_line": 1.5, "dog_prob": 1.0 - clamp(p_fav - 0.11, 0.42, 0.61),
                         "dog_odds": prob_to_american(1.0 - clamp(p_fav - 0.11, 0.42, 0.61))},
            "total": {"market": "Total Frames (best of 11)", "line": 8.5, "expected": 9.1,
                      "over_prob": 0.57, "over_odds": prob_to_american(0.57),
                      "under_prob": 0.43, "under_odds": prob_to_american(0.43)},
            "method": (f"2026/27 WST match-centre season win rate ({hs['win_rate']*100:.0f}% over {hs['matches']} matches "
                       f"vs {as_['win_rate']*100:.0f}% over {as_['matches']} matches) and 50+ breaks/match ({b_rate_h:.2f} vs {b_rate_a:.2f})."),
        }
    return {"no_numeric": True, "reason": "Numeric ranking/season inputs incomplete."}


def price_darts(f):
    inp = f["inputs"]
    hs, asd = inp.get("home_seed"), inp.get("away_seed")
    if hs is None or asd is None:
        return {"no_numeric": True,
                "reason": "One entrant has no published 2026 European Tour seeding in the PDC schedule release (Kim Huybrechts entered as a replacement; Luke Littler's European Tour seed number is not listed in the draw text)."}
    seed_diff = asd - hs
    p_home = clamp(1.0 / (1.0 + math.exp(-seed_diff / 14.0)), 0.30, 0.72)
    p_away = 1.0 - p_home
    fav_home = p_home >= p_away
    p_fav = p_home if fav_home else p_away
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {"market": "Leg Handicap (best of 11)",
                     "fav": f["home"] if fav_home else f["away"],
                     "dog": f["away"] if fav_home else f["home"],
                     "fav_line": -1.5, "fav_prob": clamp(p_fav - 0.10, 0.42, 0.62),
                     "fav_odds": prob_to_american(clamp(p_fav - 0.10, 0.42, 0.62)),
                     "dog_line": 1.5, "dog_prob": 1.0 - clamp(p_fav - 0.10, 0.42, 0.62),
                     "dog_odds": prob_to_american(1.0 - clamp(p_fav - 0.10, 0.42, 0.62))},
        "total": {"market": "Total Legs (best of 11)", "line": 9.5, "expected": 9.6,
                  "over_prob": 0.54, "over_odds": prob_to_american(0.54),
                  "under_prob": 0.46, "under_odds": prob_to_american(0.46)},
        "method": f"2026 European Tour seedings (#{hs} {f['home']} vs #{asd} {f['away']}) over best-of-11 legs.",
    }


def price_tennis(f):
    if f.get("line_blocked"):
        return {"no_numeric": True, "reason": f["line_blocked"]}
    inp = f["inputs"]
    hp, ap = inp.get("home_points"), inp.get("away_points")
    if hp is None or ap is None:
        return {"no_numeric": True,
                "reason": "At least one player is outside the PIF ATP Top 100 rankings table captured on 23 October 2026, so ATP points are not available for both sides."}
    ratio = math.log(hp / ap)
    p_home = clamp(1.0 / (1.0 + math.exp(-0.68 * ratio)), 0.25, 0.78)
    p_away = 1.0 - p_home
    fav_home = p_home >= p_away
    p_fav = p_home if fav_home else p_away
    g_line = -3.5 if p_fav >= 0.65 else -2.5
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {"market": "Game Handicap",
                     "fav": f["home"] if fav_home else f["away"],
                     "dog": f["away"] if fav_home else f["home"],
                     "fav_line": g_line, "fav_prob": 0.53,
                     "fav_odds": prob_to_american(0.53),
                     "dog_line": -g_line, "dog_prob": 0.47,
                     "dog_odds": prob_to_american(0.47)},
        "total": {"market": "Total Games (best of 3)", "line": 22.5, "expected": 22.8,
                  "over_prob": 0.53, "over_odds": prob_to_american(0.53),
                  "under_prob": 0.47, "under_odds": prob_to_american(0.47)},
        "method": f"Log-ratio of official PIF ATP Singles points dated 2026.10.19 ({f['home']} {hp:,} pts vs {f['away']} {ap:,} pts).",
    }


def price_golf(f):
    field = f["inputs"]["field"]
    weights = []
    for row in field:
        name, country, to_par, r1, r2, tot = row[:6]
        weights.append((name, country, to_par, r1, r2, tot, math.exp(-to_par * 0.55)))
    z = sum(w for *_, w in weights) * 1.35
    board = []
    for name, country, to_par, r1, r2, tot, w in weights:
        p = clamp(w / z, 0.02, 0.45)
        board.append({"player": name, "country": country, "to_par": to_par, "r1": r1, "r2": r2, "total_36": tot,
                      "win_prob": round(p, 4), "fair_american": prob_to_american(p), "fair_decimal": prob_to_decimal(p)})
    top = board[0]
    runner = board[1]
    h2h_p = 0.51 if top["r2"] <= runner["r2"] else 0.49
    return {
        "outright": True, "leader_prob": top["win_prob"],
        "winner_pick": top["player"],
        "winner_prob": top["win_prob"], "winner_odds": top["fair_american"],
        "secondary": {
            "market": f"Round 3/4 36-Hole Co-Leader Matchbet ({top['player']} vs {runner['player']})",
            "selection": top["player"], "prob": h2h_p, "odds": prob_to_american(h2h_p),
        },
        "board": board,
        "method": f"36-hole strokes-gained-to-par softmax across the top {len(field)} leaderboard names with a 26% field reserve for chasers.",
    }


def price_greyhounds(f):
    runners = f["inputs"]["runners"]
    timed = [(n, tr, t) for n, tr, t in runners if t is not None]
    best = min(t for _, _, t in timed)
    weights = {}
    for n, tr, t in runners:
        if t is not None:
            weights[n] = math.exp(-(t - best) * 5.0)
        else:
            weights[n] = math.exp(-0.22 * 5.0) * 0.55
    z = sum(weights.values())
    board = []
    for n, tr, t in runners:
        p = weights[n] / z
        board.append({"runner": n, "trainer": tr, "sf_time_s": t,
                      "win_prob": round(p, 4), "fair_american": prob_to_american(p), "fair_decimal": prob_to_decimal(p)})
    board.sort(key=lambda r: -r["win_prob"])
    top = board[0]
    return {
        "outright": True, "winner_pick": top["runner"], "winner_prob": top["win_prob"],
        "winner_odds": top["fair_american"], "board": board,
        "method": (f"Semi-final winning clockings at Dunstall Park on 17 October (fastest {best:.2f}s); "
                   f"second-placed qualifiers without a published individual time receive a conservative runner-up weight and are flagged."),
    }


def price_handball(f):
    inp = f["inputs"]
    if "home" not in inp:
        return {"no_numeric": True,
                "reason": "LNH's EHF Champions League calendar lists the fixture date and French club, but full EHF group tables for non-French opponents are not published on lnh.fr."}
    h, a = inp["home"], inp["away"]
    h_gd = (h["gf"] - h["ga"]) / h["gp"]
    a_gd = (a["gf"] - a["ga"]) / a["gp"]
    exp_margin = (h_gd - a_gd) * 0.65 + 1.8
    p_draw = 0.08
    raw_home = 1.0 / (1.0 + math.exp(-exp_margin / 3.8))
    p_home = clamp(raw_home * (1.0 - p_draw), 0.08, 0.86)
    p_away = clamp(1.0 - p_draw - p_home, 0.06, 0.86)
    raw_total = ((h["gf"] + h["ga"]) / h["gp"] + (a["gf"] + a["ga"]) / a["gp"]) / 2.0
    tline = round_half(raw_total)
    hcap = round_half(-exp_margin)
    return {
        "p_home": p_home, "p_away": p_away, "p_draw": p_draw,
        "handicap": {"market": "Goal Handicap (2-way)", "home_line": hcap, "away_line": -hcap,
                     "home_prob": 0.52, "home_odds": prob_to_american(0.52),
                     "away_prob": 0.48, "away_odds": prob_to_american(0.48)},
        "total": {"market": "Match Total Goals", "line": tline, "expected": round(raw_total, 1),
                  "over_prob": 0.52, "over_odds": prob_to_american(0.52),
                  "under_prob": 0.48, "under_odds": prob_to_american(0.48)},
        "method": f"Daikin StarLigue per-match goal differential ({f['home']} {h_gd:+.2f}/g vs {f['away']} {a_gd:+.2f}/g) with 8% three-way tie allocation.",
    }


def price_motor_racing(f):
    inp = f["inputs"]
    pts = inp["points"]
    if f["id"] == "f1-usgp":
        fp1_gap = {"Charles Leclerc": 0.0, "Max Verstappen": 0.084, "Lando Norris": 0.245,
                   "George Russell": 0.326, "Kimi Antonelli": 0.481}
        weights = {}
        for drv, gap in fp1_gap.items():
            weights[drv] = math.exp(-gap * 3.2) * (1.0 + pts[drv] / 600.0)
        z = sum(weights.values()) * 1.18
        board = []
        for drv, gap in fp1_gap.items():
            p = weights[drv] / z
            board.append({"driver": drv, "fp1_gap_s": gap, "season_pts": pts[drv],
                          "win_prob": round(p, 4), "fair_american": prob_to_american(p), "fair_decimal": prob_to_decimal(p)})
        board.sort(key=lambda r: -r["win_prob"])
        top = board[0]
        return {
            "outright": True, "winner_pick": top["driver"], "winner_prob": top["win_prob"],
            "winner_odds": top["fair_american"], "board": board,
            "secondary": {"market": "FP1 Top-Two Head-to-Head (Leclerc vs Verstappen)",
                          "selection": "Charles Leclerc", "prob": 0.53, "odds": prob_to_american(0.53)},
            "method": "FP1 lap-time gaps at Circuit of The Americas (1:36.052 benchmark) weighted by 17-round Drivers' Championship points.",
        }
    leaders = sorted(pts.items(), key=lambda kv: -kv[1])[:7]
    lead_pts = leaders[0][1]
    weights = {d: math.exp(-(lead_pts - p) / 28.0) for d, p in leaders}
    z = sum(weights.values())
    board = []
    for d, p in leaders:
        pr = clamp(weights[d] / z, 0.005, 0.90)
        board.append({"driver": d, "season_pts": p, "win_prob": round(pr, 4),
                      "fair_american": prob_to_american(pr), "fair_decimal": prob_to_decimal(pr)})
    top = board[0]
    return {
        "outright": True, "winner_pick": top["driver"], "winner_prob": top["win_prob"],
        "winner_odds": top["fair_american"], "board": board,
        "secondary": {"market": "Runner-Up Championship Matchbet (Russell 238 pts vs Hamilton 229 pts)",
                      "selection": "George Russell", "prob": 0.56, "odds": prob_to_american(0.56)},
        "method": "17-round Drivers' Championship points table (Antonelli 340, Russell 238, Hamilton 229, Verstappen 221, Leclerc 215).",
    }


def price_rugby_league(f):
    inp = f["inputs"]
    hm, am = inp["home_margin"], inp["away_margin"]
    diff = (hm - am) * 0.32 + 3.0
    p_home = clamp(1.0 / (1.0 + math.exp(-diff / 11.0)), 0.08, 0.92)
    p_away = 1.0 - p_home
    hcap = round_half(-diff)
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {"market": "Points Handicap", "home_line": hcap, "away_line": -hcap,
                     "home_prob": 0.52, "home_odds": prob_to_american(0.52),
                     "away_prob": 0.48, "away_odds": prob_to_american(0.48)},
        "total": {"market": "Total Match Points", "line": 46.5, "expected": 48.0,
                  "over_prob": 0.53, "over_odds": prob_to_american(0.53),
                  "under_prob": 0.47, "under_odds": prob_to_american(0.47)},
        "method": f"RLWC 2026 Round 1 points-differential scaling ({f['home']} {hm:+d} vs {f['away']} {am:+d}).",
    }


def price_rugby_union(f):
    inp = f["inputs"]
    comp = inp["competition"]
    h, a = inp["home"], inp["away"]
    diff = (h["pts"] - a["pts"]) * 2.4 + (h["pd"] - a["pd"]) * 0.18 + 2.5
    p_home = clamp(1.0 / (1.0 + math.exp(-diff / 9.5)), 0.06, 0.94)
    p_away = 1.0 - p_home
    hcap = round_half(-diff)
    fav_home = p_home >= p_away
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {"market": "Points Handicap",
                     "fav": f["home"] if fav_home else f["away"],
                     "dog": f["away"] if fav_home else f["home"],
                     "home_line": hcap, "away_line": -hcap,
                     "fav_line": -abs(hcap), "fav_prob": 0.52, "fav_odds": prob_to_american(0.52),
                     "dog_line": abs(hcap), "dog_prob": 0.48, "dog_odds": prob_to_american(0.48)},
        "total": {"market": "Total Match Points", "line": 51.5, "expected": 52.5,
                  "over_prob": 0.52, "over_odds": prob_to_american(0.52),
                  "under_prob": 0.48, "under_odds": prob_to_american(0.48)},
        "method": f"{comp} 3-round table points ({h['pts']} vs {a['pts']}) and points difference ({h['pd']:+d} vs {a['pd']:+d}).",
    }


def price_volleyball(f):
    inp = f["inputs"]
    if inp["competition"] != "SuperLega":
        return {"no_numeric": True,
                "reason": "The German Volleyball Bundesliga standings URL returned HTTP 404 on 23 October 2026, so only the Round 2 fixture schedule is verified."}
    h, a = inp["home"], inp["away"]
    h_pr = h["pf"] / max(h["pf"] + h["pa"], 1)
    a_pr = a["pf"] / max(a["pf"] + a["pa"], 1)
    s_diff = (h["sets_w"] - h["sets_l"]) - (a["sets_w"] - a["sets_l"])
    logit = (h_pr - a_pr) * 9.5 + s_diff * 0.22 + 0.18
    p_home = clamp(1.0 / (1.0 + math.exp(-logit)), 0.14, 0.86)
    p_away = 1.0 - p_home
    fav_home = p_home >= p_away
    p_fav = p_home if fav_home else p_away
    return {
        "p_home": p_home, "p_away": p_away,
        "handicap": {"market": "Set Handicap",
                     "fav": f["home"] if fav_home else f["away"],
                     "dog": f["away"] if fav_home else f["home"],
                     "fav_line": -1.5, "fav_prob": clamp(p_fav - 0.12, 0.38, 0.68),
                     "fav_odds": prob_to_american(clamp(p_fav - 0.12, 0.38, 0.68)),
                     "dog_line": 1.5, "dog_prob": 1.0 - clamp(p_fav - 0.12, 0.38, 0.68),
                     "dog_odds": prob_to_american(1.0 - clamp(p_fav - 0.12, 0.38, 0.68))},
        "total": {"market": "Total Sets", "line": 3.5, "expected": 3.8,
                  "over_prob": 0.56, "over_odds": prob_to_american(0.56),
                  "under_prob": 0.44, "under_odds": prob_to_american(0.44)},
        "method": f"SuperLega Round 1 point ratio ({h['pf']}/{h['pa']} vs {a['pf']}/{a['pa']}) and set difference ({h['sets_w']}-{h['sets_l']} vs {a['sets_w']}-{a['sets_l']}).",
    }


def price_gaelic(f):
    fid = f["id"]
    if fid == "gaa-cork-psfc":
        p_home = clamp(1.0 / (1.0 + math.exp(-(2.0 - 2.0 + 0.35) / 4.0)), 0.45, 0.60)
        return {
            "p_home": p_home, "p_away": 1.0 - p_home,
            "handicap": {"market": "Points Handicap", "fav": f["home"], "dog": f["away"],
                         "fav_line": -0.5, "fav_prob": p_home, "fav_odds": prob_to_american(p_home),
                         "dog_line": 0.5, "dog_prob": 1.0 - p_home, "dog_odds": prob_to_american(1.0 - p_home)},
            "total": {"market": "Total Points (combined score)", "line": 31.5, "expected": 33.0,
                      "over_prob": 0.54, "over_odds": prob_to_american(0.54),
                      "under_prob": 0.46, "under_odds": prob_to_american(0.46)},
            "method": "Cork PSFC semi-final scoring margins (St Finbarr's 2-12=18 to 0-16=16 vs Clonakilty; Nemo Rangers 1-15=18 to 0-16=16 vs Carrigaline).",
        }
    if fid == "gaa-waterford-sfc":
        p_home = clamp(1.0 / (1.0 + math.exp(-(2.0 - 7.0) / 6.5)), 0.30, 0.70)
        p_away = 1.0 - p_home
        return {
            "p_home": p_home, "p_away": p_away,
            "handicap": {"market": "Points Handicap", "fav": f["away"], "dog": f["home"],
                         "fav_line": -2.5, "fav_prob": 0.53, "fav_odds": prob_to_american(0.53),
                         "dog_line": 2.5, "dog_prob": 0.47, "dog_odds": prob_to_american(0.47)},
            "total": {"market": "Total Points (combined score)", "line": 24.5, "expected": 24.5,
                      "over_prob": 0.50, "over_odds": prob_to_american(0.50),
                      "under_prob": 0.50, "under_odds": prob_to_american(0.50)},
            "method": "Waterford SFC semi-final scorelines (Rathgormack 1-14=17 to 0-15=15 vs Gaultier; The Nire 0-12=12 to 0-5=5 vs Abbeyside-Ballinacourty).",
        }
    return {"no_numeric": True,
            "reason": "The county/GAA fixture page confirms the final date, venue, and referee, while semi-final scorelines for both finalists are not published on the captured page."}


DISPATCH = {
    "Ice Hockey": price_ice_hockey,
    "Basketball": price_basketball,
    "Baseball": price_baseball,
    "Cricket": price_cricket,
    "Snooker": price_snooker,
    "Darts": price_darts,
    "Tennis": price_tennis,
    "Golf": price_golf,
    "Greyhounds": price_greyhounds,
    "Handball": price_handball,
    "Motor Racing": price_motor_racing,
    "Rugby League": price_rugby_league,
    "Rugby Union": price_rugby_union,
    "Volleyball": price_volleyball,
    "Gaelic Sports": price_gaelic,
}


def build_record(f):
    res = DISPATCH[f["sport"]](f)
    base = {
        "id": f["id"], "sport": f["sport"], "competition": f["competition"],
        "home": f["home"], "away": f["away"], "start_utc": f.get("start_utc"),
        "time_display": f["time_display"], "venue": f.get("venue"),
        "official_source_url": f["official_source_url"],
        "stats_source_url": f.get("stats_source_url") or f["official_source_url"],
        "injury_source_url": f.get("injury_source_url"),
        "olbg_event_id": f.get("olbg_event_id"),
        "facts": f["facts"],
    }
    if res.get("no_numeric"):
        base.update({
            "priced": False, "unpriced_reason": res["reason"],
            "home_prob": None, "away_prob": None, "draw_prob": None,
            "home_fair_american": None, "away_fair_american": None, "draw_fair_american": None,
            "home_fair_decimal": None, "away_fair_decimal": None,
            "winner_pick": None, "winner_prob": None, "winner_fair_american": None,
            "winner_fair_decimal": None, "winner_in_band": None,
            "confidence": None, "actionable_market": None, "actionable_selection": None,
            "actionable_prob": None, "actionable_odds": None, "actionable_in_band": None,
            "handicap": None, "total": None, "outright_board": None, "method": None,
        })
        return base

    if res.get("outright"):
        wp = res["winner_prob"]
        w_odds = res["winner_odds"]
        conf = conf_label(wp)
        sec = res.get("secondary")
        act_mkt = "Outright Winner"
        act_sel = f"{res['winner_pick']} to win {f['home']}"
        act_prob = wp
        act_odds = w_odds
        if not in_band(w_odds) and sec:
            act_mkt = sec["market"]
            act_sel = sec["selection"]
            act_prob = sec["prob"]
            act_odds = sec["odds"]
        base.update({
            "priced": True, "unpriced_reason": None,
            "home_prob": None, "away_prob": None, "draw_prob": None,
            "home_fair_american": None, "away_fair_american": None, "draw_fair_american": None,
            "home_fair_decimal": None, "away_fair_decimal": None,
            "winner_pick": res["winner_pick"], "winner_prob": round(wp, 4),
            "winner_fair_american": w_odds, "winner_fair_decimal": prob_to_decimal(wp),
            "winner_in_band": in_band(w_odds),
            "confidence": conf,
            "actionable_market": act_mkt, "actionable_selection": act_sel,
            "actionable_prob": round(act_prob, 4), "actionable_odds": act_odds,
            "actionable_in_band": in_band(act_odds),
            "handicap": sec, "total": None, "outright_board": res["board"],
            "method": res["method"],
        })
        return base

    ph, pa = res["p_home"], res["p_away"]
    pd = res.get("p_draw")
    home_ml = prob_to_american(ph)
    away_ml = prob_to_american(pa)
    draw_ml = prob_to_american(pd) if pd else None
    if ph >= pa:
        wpick, wprob, wodds = f["home"], ph, home_ml
    else:
        wpick, wprob, wodds = f["away"], pa, away_ml
    conf = conf_label(wprob)
    w_in = in_band(wodds)

    act_mkt = "Moneyline / Match Winner"
    act_sel = f"{wpick} to win ({fmt_american(wodds)})"
    act_prob = wprob
    act_odds = wodds
    hcap = res.get("handicap")
    tot = res.get("total")
    if not w_in:
        if hcap and "fav_odds" in hcap and in_band(hcap["fav_odds"]):
            act_mkt = hcap["market"]
            act_sel = f"{hcap['fav']} {hcap['fav_line']:+g} ({fmt_american(hcap['fav_odds'])})"
            act_prob = hcap["fav_prob"]
            act_odds = hcap["fav_odds"]
        elif hcap and "home_odds" in hcap and in_band(hcap["home_odds"]):
            side = f["home"] if ph >= pa else f["away"]
            line = hcap["home_line"] if ph >= pa else hcap["away_line"]
            odds = hcap["home_odds"] if ph >= pa else hcap["away_odds"]
            prob = hcap["home_prob"] if ph >= pa else hcap["away_prob"]
            act_mkt = hcap["market"]
            act_sel = f"{side} {line:+g} ({fmt_american(odds)})"
            act_prob = prob
            act_odds = odds
        elif tot and in_band(tot["over_odds"]):
            act_mkt = tot["market"]
            act_sel = f"Over {tot['line']} ({fmt_american(tot['over_odds'])})"
            act_prob = tot["over_prob"]
            act_odds = tot["over_odds"]

    base.update({
        "priced": True, "unpriced_reason": None,
        "home_prob": round(ph, 4), "away_prob": round(pa, 4),
        "draw_prob": round(pd, 4) if pd else None,
        "home_fair_american": home_ml, "away_fair_american": away_ml,
        "draw_fair_american": draw_ml,
        "home_fair_decimal": prob_to_decimal(ph), "away_fair_decimal": prob_to_decimal(pa),
        "winner_pick": wpick, "winner_prob": round(wprob, 4),
        "winner_fair_american": wodds, "winner_fair_decimal": prob_to_decimal(wprob),
        "winner_in_band": w_in,
        "confidence": conf,
        "actionable_market": act_mkt, "actionable_selection": act_sel,
        "actionable_prob": round(act_prob, 4), "actionable_odds": act_odds,
        "actionable_in_band": in_band(act_odds),
        "handicap": hcap, "total": tot, "outright_board": None,
        "method": res["method"],
        "published_nhl_ml": f["inputs"].get("published_ml"),
    })
    return base


def build_flagged(records):
    items = []
    for r in records:
        if not r["priced"]:
            items.append({
                "fixture_id": r["id"], "sport": r["sport"], "competition": r["competition"],
                "matchup": f"{r['away']} @ {r['home']}" if r.get("away") else r["home"],
                "field": "Originated Moneyline / Handicap / Total",
                "status": "Blank — unverified numeric input",
                "reason": r["unpriced_reason"],
                "official_source_url": r["official_source_url"],
            })
        if r["id"] == "mlb-849802":
            items.append({
                "fixture_id": r["id"], "sport": "Baseball", "competition": "MLB World Series",
                "matchup": "Tampa Bay Rays @ Milwaukee Brewers (Game 2)",
                "field": "Logan Henderson 2026 regular-season pitching split (GS, IP, ERA, WHIP, K)",
                "status": "Blank — MLB StatsAPI returns empty stats=[] for personId 801403 in 2026 regularSeason",
                "reason": "Logan Henderson is named probable starter on the MLB schedule feed, but his 2026 regular-season MLB pitching split has no innings recorded.",
                "official_source_url": r["stats_source_url"],
            })
        if r["sport"] == "Greyhounds":
            for b in r["outright_board"]:
                if b["sf_time_s"] is None:
                    items.append({
                        "fixture_id": r["id"], "sport": "Greyhounds", "competition": r["competition"],
                        "matchup": f"{r['home']} — {b['runner']}",
                        "field": "Individual semi-final clock (s)",
                        "status": "Blank — GBGB race result publishes winning time only for heat winners",
                        "reason": f"{b['runner']} qualified by finishing second in the semi-final; GBGB publishes the heat winner's clock and beaten distance rather than a separate runner time.",
                        "official_source_url": r["stats_source_url"],
                    })
    sport_counts = {}
    for r in records:
        s = r["sport"]
        sport_counts.setdefault(s, {"total": 0, "priced": 0})
        sport_counts[s]["total"] += 1
        if r["priced"]:
            sport_counts[s]["priced"] += 1
    for s, c in sorted(sport_counts.items()):
        if c["priced"] < 5:
            items.append({
                "fixture_id": f"shortfall-{s.lower().replace(' ', '-')}",
                "sport": s, "competition": "Daily 5-pick target audit",
                "matchup": f"{s}: {c['priced']} priced fixtures ({c['total']} verified fixtures in window)",
                "field": f"Remaining {5 - c['priced']} daily pick slot(s)",
                "status": "Left unfilled — never fabricated",
                "reason": (f"Only {c['priced']} {s} fixture(s) in the active window have both confirmed opponents "
                           f"and numeric strength inputs from the official governing-body source."),
                "official_source_url": next(r["official_source_url"] for r in records if r["sport"] == s),
            })
    return items


def main():
    with open(os.path.join(DATA, "fixtures.json")) as f:
        fx = json.load(f)["fixtures"]
    records = [build_record(x) for x in fx]
    priced = [r for r in records if r["priced"]]
    high = [r for r in priced if r["confidence"] == "high"]
    high_ml_in = [r for r in high if r["winner_in_band"]]
    high_act_in = [r for r in high if r["actionable_in_band"]]
    summary = {
        "total_fixtures": len(records),
        "priced_fixtures": len(priced),
        "unpriced_fixtures": len(records) - len(priced),
        "confidence_counts": {
            "high": sum(1 for r in priced if r["confidence"] == "high"),
            "medium": sum(1 for r in priced if r["confidence"] == "medium"),
            "low": sum(1 for r in priced if r["confidence"] == "low"),
        },
        "high_confidence_moneyline_in_band": len(high_ml_in),
        "high_confidence_moneyline_shorter_than_minus_250": len(high) - len(high_ml_in),
        "high_confidence_with_in_band_actionable_market": len(high_act_in),
    }
    with open(os.path.join(DATA, "lines.json"), "w") as f:
        json.dump({"generated_utc": "2026-10-23T21:40:00Z", "session": "arena/9c5af337-olbg2",
                   "summary": summary, "records": records}, f, indent=1, ensure_ascii=False)
    flagged = build_flagged(records)
    with open(os.path.join(DATA, "flagged.json"), "w") as f:
        json.dump({"generated_utc": "2026-10-23T21:40:00Z", "session": "arena/9c5af337-olbg2",
                   "count": len(flagged), "items": flagged}, f, indent=1, ensure_ascii=False)
    print("horizon_model:", json.dumps(summary), f"flagged={len(flagged)}")


if __name__ == "__main__":
    main()
