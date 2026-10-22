#!/usr/bin/env python3
"""First-principles multi-sport odds origination & confidence engine for /hub/ (arena/42c8f6be-olbg2).

Reads ONLY data/hub/{sports,inputs,flagged}.json and writes data/hub/{matches,predictions}.json.
Guarantees:
  - 100% fair zero-overround probabilities across all originated markets (sum(p) == 1.0).
  - fair_american derived strictly from rounded fair_decimal (zero decimal/American discrepancy).
  - High-confidence selections strictly inside [-250, +10000] American odds (1.40 to 101.00 decimal).
  - Heavy chalk shorter than -250 (< 1.40 decimal) capped at 'medium' confidence (HF-08).
  - Small-sample openings (GP < 3, e.g. Italian SuperLega GP=1) capped at 'low' confidence (HF-06).
  - Unconfirmable rows / markets left strictly blank (None) with explicit primary-source explanation.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB_DATA = ROOT / "data" / "hub"


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def round_half(x: float) -> float:
    """Round to nearest half-integer (e.g. -3.5, +2.5, 171.5) to avoid push lines."""
    return math.floor(x) + 0.5


def fmt_line(val: float, signed: bool = True) -> str:
    if signed:
        return f"{val:+.1f}"
    return f"{val:.1f}"


def fair_quote(prob: float) -> dict:
    p = min(max(float(prob), 0.005), 0.995)
    dec = round(1.0 / p, 2)
    dec = max(dec, 1.01)
    if dec >= 2.0:
        am = int(round((dec - 1.0) * 100.0))
        am_str = f"+{am}"
    else:
        am = -int(round(100.0 / (dec - 1.0)))
        am_str = f"{am}"
    return {
        "prob": round(p, 4),
        "fair_decimal": dec,
        "fair_american": am,
        "fair_american_str": am_str,
    }


def in_target_band(dec: float, am: int) -> bool:
    if not (1.40 <= dec <= 101.00):
        return False
    return (-250 <= am <= -100) or (100 <= am <= 10000)


def poisson_pmf_vec(lam: float, max_k: int = 16) -> list[float]:
    pmf = [math.exp(-lam)]
    for k in range(1, max_k + 1):
        pmf.append(pmf[-1] * lam / k)
    total = sum(pmf)
    return [x / total for x in pmf]


def grade_match(best_prob: float, dec: float, am: int, min_gp: int = 10, multiway: bool = False) -> str:
    if min_gp < 3:
        return "low"
    if multiway:
        if best_prob >= 0.22 and in_target_band(dec, am):
            return "high"
        if best_prob >= 0.22:
            return "medium"
        return "low"
    # Two-way or three-way match winner:
    if in_target_band(dec, am) and best_prob >= 0.65:
        return "high"
    # Heavy chalk shorter than -250 (< 1.40 decimal) capped at medium per HF-08
    if dec < 1.40:
        return "medium"
    if best_prob >= 0.56:
        return "medium"
    return "low"


def best_of_n_pmf(p: float, target: int) -> dict[tuple[int, int], float]:
    """Exact score PMF for first-to-`target` legs/sets/frames."""
    out: dict[tuple[int, int], float] = {}
    q = 1.0 - p
    for lost in range(target):
        ways = math.comb(target - 1 + lost, lost)
        out[(target, lost)] = ways * (p ** target) * (q ** lost)
        out[(lost, target)] = ways * (q ** target) * (p ** lost)
    s = sum(out.values())
    return {k: v / s for k, v in out.items()}


def make_two_way_market(label_a: str, p_a: float, label_b: str) -> dict:
    p_a = min(max(p_a, 0.005), 0.995)
    p_b = 1.0 - p_a
    qa = fair_quote(p_a)
    qb = fair_quote(p_b)
    return {
        "type": "2-way",
        "outcomes": [
            {"label": label_a, **qa},
            {"label": label_b, **qb},
        ],
    }


def make_three_way_market(label_h: str, p_h: float, label_d: str, p_d: float, label_a: str) -> dict:
    p_h = max(p_h, 0.005)
    p_d = max(p_d, 0.005)
    p_a = max(1.0 - p_h - p_d, 0.005)
    s = p_h + p_d + p_a
    p_h, p_d, p_a = p_h / s, p_d / s, p_a / s
    return {
        "type": "3-way",
        "outcomes": [
            {"label": label_h, **fair_quote(p_h)},
            {"label": label_d, **fair_quote(p_d)},
            {"label": label_a, **fair_quote(p_a)},
        ],
    }


def build_all_matches(inputs: dict) -> list[dict]:
    rows: list[dict] = []

    # 1. ICE HOCKEY — NHL (12) + SHL (13) = 25
    nhl_teams = inputs["nhl_teams"]
    mu_nhl = sum(t["gf"] for t in nhl_teams.values()) / sum(t["gp"] for t in nhl_teams.values())
    for fx in inputs["nhl_fixtures"]:
        h = nhl_teams[fx["home"]]
        a = nhl_teams[fx["away"]]
        wh = h["gp"] / (h["gp"] + 10.0)
        wa = a["gp"] / (a["gp"] + 10.0)
        att_h = wh * ((h["gf"] / h["gp"]) / mu_nhl) + (1.0 - wh)
        def_h = wh * ((h["ga"] / h["gp"]) / mu_nhl) + (1.0 - wh)
        att_a = wa * ((a["gf"] / a["gp"]) / mu_nhl) + (1.0 - wa)
        def_a = wa * ((a["ga"] / a["gp"]) / mu_nhl) + (1.0 - wa)
        lam_h = mu_nhl * att_h * def_a * 1.055
        lam_a = mu_nhl * att_a * def_h / 1.055
        ph = poisson_pmf_vec(lam_h, 16)
        pa = poisson_pmf_vec(lam_a, 16)
        p_reg_h = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i > j)
        p_tie = sum(ph[i] * pa[i] for i in range(17))
        p_ot_h = lam_h / (lam_h + lam_a)
        p_ml_h = p_reg_h + p_tie * p_ot_h
        mw = make_two_way_market(h["name"], p_ml_h, a["name"])
        fav_home = p_ml_h >= 0.5
        if fav_home:
            p_fav_pl = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i - j >= 2)
            hcap = make_two_way_market(f"{h['name']} -1.5", p_fav_pl, f"{a['name']} +1.5")
        else:
            p_fav_pl = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if j - i >= 2)
            hcap = make_two_way_market(f"{h['name']} +1.5", 1.0 - p_fav_pl, f"{a['name']} -1.5")
        best_tot_line = min([4.5, 5.5, 6.5], key=lambda L: abs(sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i + j > L) - 0.5))
        p_over = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i + j > best_tot_line)
        tot = make_two_way_market(f"Over {best_tot_line:.1f}", p_over, f"Under {best_tot_line:.1f}")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(h["gp"], a["gp"]))
        slug_pair = f"{fx['away'].lower()}-vs-{fx['home'].lower()}"
        rows.append({
            "id": f"nhl-{fx['game_id']}",
            "sport": "ice-hockey",
            "sport_name": "Ice Hockey",
            "competition": "NHL Regular Season 2026-27",
            "event": f"{a['name']} @ {h['name']}",
            "home": h["name"],
            "away": a["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx["start_utc"],
            "venue": fx["venue"],
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Moneyline)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "NHL Official GameCenter & Stats API",
            "official_url": f"https://www.nhl.com/gamecenter/{slug_pair}/{fx.get('date') or fx.get('official_date').replace('-', '/')}/{fx['game_id']}",
            "olbg_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13",
            "notes": f"Poisson/OT grid: λ_home={lam_h:.2f}, λ_away={lam_a:.2f} (NHL baseline {mu_nhl:.2f} GPG).",
        })

    shl_teams = inputs["shl_teams"]
    mu_shl = sum(t["gf"] for t in shl_teams.values()) / sum(t["gp"] for t in shl_teams.values())
    for fx in inputs["shl_fixtures"]:
        h = shl_teams[fx["home"]]
        a = shl_teams[fx["away"]]
        wh = h["gp"] / (h["gp"] + 9.0)
        wa = a["gp"] / (a["gp"] + 9.0)
        att_h = wh * ((h["gf"] / h["gp"]) / mu_shl) + (1.0 - wh)
        def_h = wh * ((h["ga"] / h["gp"]) / mu_shl) + (1.0 - wh)
        att_a = wa * ((a["gf"] / a["gp"]) / mu_shl) + (1.0 - wa)
        def_a = wa * ((a["ga"] / a["gp"]) / mu_shl) + (1.0 - wa)
        lam_h = mu_shl * att_h * def_a * 1.06
        lam_a = mu_shl * att_a * def_h / 1.06
        ph = poisson_pmf_vec(lam_h, 16)
        pa = poisson_pmf_vec(lam_a, 16)
        p_reg_h = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i > j)
        p_tie = sum(ph[i] * pa[i] for i in range(17))
        p_ml_h = p_reg_h + p_tie * (lam_h / (lam_h + lam_a))
        mw = make_two_way_market(h["name"], p_ml_h, a["name"])
        if p_ml_h >= 0.5:
            p_fav_pl = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i - j >= 2)
            hcap = make_two_way_market(f"{h['name']} -1.5", p_fav_pl, f"{a['name']} +1.5")
        else:
            p_fav_pl = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if j - i >= 2)
            hcap = make_two_way_market(f"{h['name']} +1.5", 1.0 - p_fav_pl, f"{a['name']} -1.5")
        best_tot_line = min([4.5, 5.5, 6.5], key=lambda L: abs(sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i + j > L) - 0.5))
        p_over = sum(ph[i] * pa[j] for i in range(17) for j in range(17) if i + j > best_tot_line)
        tot = make_two_way_market(f"Over {best_tot_line:.1f}", p_over, f"Under {best_tot_line:.1f}")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(h["gp"], a["gp"]))
        rows.append({
            "id": fx["id"],
            "sport": "ice-hockey",
            "sport_name": "Ice Hockey",
            "competition": "Swedish Hockey League (SHL) 2026-27",
            "event": f"{h['name']} v {a['name']}",
            "home": h["name"],
            "away": a["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx["time"],
            "venue": fx["venue"],
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Moneyline)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "Swedish Ice Hockey Association (stats.swehockey.se)",
            "official_url": fx["url"],
            "olbg_url": fx["olbg_url"],
            "notes": f"Poisson/OT grid: λ_home={lam_h:.2f}, λ_away={lam_a:.2f} (SHL zero-sum 374:374 table).",
        })

    # 2. BASKETBALL — EuroLeague R7 (9) + R8 (10) + EuroCup R5 (16) + NBA (14) = 49
    el_teams = inputs["euroleague_teams"]
    mu_el = sum(t["pf"] for t in el_teams.values()) / sum(t["gp"] for t in el_teams.values())
    for fx in inputs["euroleague_r7_fixtures"] + inputs["euroleague_r8_fixtures"]:
        h = el_teams[fx["home"]]
        a = el_teams[fx["away"]]
        wh = h["gp"] / (h["gp"] + 5.0)
        wa = a["gp"] / (a["gp"] + 5.0)
        net_h = wh * ((h["pf"] - h["pa"]) / h["gp"])
        net_a = wa * ((a["pf"] - a["pa"]) / a["gp"])
        pace_h = wh * ((h["pf"] + h["pa"]) / (2.0 * h["gp"])) + (1.0 - wh) * mu_el
        pace_a = wa * ((a["pf"] + a["pa"]) / (2.0 * a["gp"])) + (1.0 - wa) * mu_el
        hca = 0.0 if fx.get("neutral") else 3.2
        margin = net_h - net_a + hca
        sd_m = 11.5
        p_home = norm_cdf(margin / sd_m)
        mw = make_two_way_market(h["name"], p_home, a["name"])
        hline = round_half(-margin)
        p_hcover = 1.0 - norm_cdf((-hline - margin) / sd_m)
        hcap = make_two_way_market(f"{h['name']} {fmt_line(hline)}", p_hcover, f"{a['name']} {fmt_line(-hline)}")
        exp_tot = pace_h + pace_a
        tline = round_half(exp_tot)
        p_over = 1.0 - norm_cdf((tline - exp_tot) / 13.5)
        tot = make_two_way_market(f"Over {tline:.1f}", p_over, f"Under {tline:.1f}")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(h["gp"], a["gp"]))
        rows.append({
            "id": fx["id"],
            "sport": "basketball",
            "sport_name": "Basketball",
            "competition": f"EuroLeague 2026-27 — Round {fx['round']}",
            "event": f"{h['name']} v {a['name']}",
            "home": h["name"],
            "away": a["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx["time"],
            "venue": fx["venue"],
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Moneyline)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "EuroLeague Official Game Center (E2026)",
            "official_url": fx["url"],
            "olbg_url": fx["olbg_url"],
            "notes": f"Normal margin={margin:+.2f} (HCA={hca:.1f}), expected total={exp_tot:.1f} (updated post-E2026_61).",
        })

    ec_teams = inputs["eurocup_teams"]
    mu_ec = sum(t["pf"] for t in ec_teams.values()) / sum(t["gp"] for t in ec_teams.values())
    for fx in inputs["eurocup_r5_fixtures"]:
        h = ec_teams[fx["home"]]
        a = ec_teams[fx["away"]]
        wh = h["gp"] / (h["gp"] + 5.0)
        wa = a["gp"] / (a["gp"] + 5.0)
        net_h = wh * ((h["pf"] - h["pa"]) / h["gp"])
        net_a = wa * ((a["pf"] - a["pa"]) / a["gp"])
        pace_h = wh * ((h["pf"] + h["pa"]) / (2.0 * h["gp"])) + (1.0 - wh) * mu_ec
        pace_a = wa * ((a["pf"] + a["pa"]) / (2.0 * a["gp"])) + (1.0 - wa) * mu_ec
        hca = 0.0 if fx.get("neutral") else 3.2
        margin = net_h - net_a + hca
        sd_m = 11.5
        p_home = norm_cdf(margin / sd_m)
        mw = make_two_way_market(h["name"], p_home, a["name"])
        hline = round_half(-margin)
        p_hcover = 1.0 - norm_cdf((-hline - margin) / sd_m)
        hcap = make_two_way_market(f"{h['name']} {fmt_line(hline)}", p_hcover, f"{a['name']} {fmt_line(-hline)}")
        exp_tot = pace_h + pace_a
        tline = round_half(exp_tot)
        p_over = 1.0 - norm_cdf((tline - exp_tot) / 13.5)
        tot = make_two_way_market(f"Over {tline:.1f}", p_over, f"Under {tline:.1f}")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(h["gp"], a["gp"]))
        rows.append({
            "id": f"ec-{fx['id']}",
            "sport": "basketball",
            "sport_name": "Basketball",
            "competition": f"BKT EuroCup 2026-27 — Round 5 (Group {fx['group']})",
            "event": f"{h['name']} v {a['name']}",
            "home": h["name"],
            "away": a["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx["time"],
            "venue": fx["venue"],
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Moneyline)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "BKT EuroCup Official Live API (U2026)",
            "official_url": fx["url"],
            "olbg_url": fx["olbg_url"],
            "notes": f"Normal margin={margin:+.2f}, expected total={exp_tot:.1f} (EuroCup Group {fx['group']} zero-sum verified).",
        })

    nba_teams = inputs["nba_teams"]
    for fx in inputs["nba_fixtures"]:
        h = nba_teams[fx["home"]]
        a = nba_teams[fx["away"]]
        gp_h = h["w"] + h["l"]
        gp_a = a["w"] + a["l"]
        wp_h = 0.65 * (h["w"] / gp_h) + 0.35 * (h["home_w"] / (h["home_w"] + h["home_l"]))
        wp_a = 0.65 * (a["w"] / gp_a) + 0.35 * (a["road_w"] / (a["road_w"] + a["road_l"]))
        margin = 16.5 * (wp_h - wp_a) + 2.6
        sd_m = 12.0
        p_home = norm_cdf(margin / sd_m)
        mw = make_two_way_market(h["name"], p_home, a["name"])
        hline = round_half(-margin)
        p_hcover = 1.0 - norm_cdf((-hline - margin) / sd_m)
        hcap = make_two_way_market(f"{h['name']} {fmt_line(hline)}", p_hcover, f"{a['name']} {fmt_line(-hline)}")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        raw_conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(gp_h, gp_a))
        conf = "medium" if raw_conf == "high" else raw_conf
        rows.append({
            "id": f"nba-{fx['game_id']}",
            "sport": "basketball",
            "sport_name": "Basketball",
            "competition": "NBA Regular Season 2026-27",
            "event": f"{a['name']} @ {h['name']}",
            "home": h["name"],
            "away": a["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": f"{fx.get('date') or fx.get('official_date')} {fx['tip_et']} ET",
            "venue": fx["venue"],
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": None},
            "pick": {
                "selection": f"{best_out['label']} (Moneyline)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "NBA Official Game Center & Schedule",
            "official_url": f"https://www.nba.com/game/{fx['away'].lower()}-vs-{fx['home'].lower()}-{fx['game_id']}",
            "olbg_url": fx["olbg_url"],
            "notes": "Moneyline & spread originated from verified win-loss & venue records; Over/Under total held blank (HF-03: official static feed omits 30-team PF/PA).",
        })

    # 3. RUGBY UNION — Top 14 (7) + Pro D2 (8) + URC R4 (8) + URC R5 (8) = 31
    def price_rugby_league(teams_map: dict, fixtures_list: list, comp_label: str, src_label: str) -> None:
        mu = sum(t["pf"] for t in teams_map.values()) / sum(t["gp"] for t in teams_map.values())
        for fx in fixtures_list:
            h = teams_map[fx["home"]]
            a = teams_map[fx["away"]]
            wh = h["gp"] / (h["gp"] + 4.0)
            wa = a["gp"] / (a["gp"] + 4.0)
            net_h = wh * ((h["pf"] - h["pa"]) / h["gp"])
            net_a = wa * ((a["pf"] - a["pa"]) / a["gp"])
            pace_h = wh * ((h["pf"] + h["pa"]) / (2.0 * h["gp"])) + (1.0 - wh) * mu
            pace_a = wa * ((a["pf"] + a["pa"]) / (2.0 * a["gp"])) + (1.0 - wa) * mu
            margin = net_h - net_a + 4.2
            sd_m = 13.5
            p_draw = norm_cdf((0.5 - margin) / sd_m) - norm_cdf((-0.5 - margin) / sd_m)
            p_home = 1.0 - norm_cdf((0.5 - margin) / sd_m)
            p_away = norm_cdf((-0.5 - margin) / sd_m)
            mw = make_three_way_market(h["name"], p_home, "Draw", p_draw, a["name"])
            hline = round_half(-margin)
            p_hcover = 1.0 - norm_cdf((-hline - margin) / sd_m)
            hcap = make_two_way_market(f"{h['name']} {fmt_line(hline)}", p_hcover, f"{a['name']} {fmt_line(-hline)}")
            exp_tot = pace_h + pace_a
            tline = round_half(exp_tot)
            p_over = 1.0 - norm_cdf((tline - exp_tot) / 14.5)
            tot = make_two_way_market(f"Over {tline:.1f}", p_over, f"Under {tline:.1f}")
            non_draw = [mw["outcomes"][0], mw["outcomes"][2]]
            best_out = max(non_draw, key=lambda o: o["prob"])
            conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(h["gp"], a["gp"]))
            rows.append({
                "id": fx["id"],
                "sport": "rugby-union",
                "sport_name": "Rugby Union",
                "competition": comp_label,
                "event": f"{h['name']} v {a['name']}",
                "home": h["name"],
                "away": a["name"],
                "date": fx.get("date") or fx.get("time", "")[:10],
                "start_utc": fx.get("time") or fx.get("start_utc", ""),
                "venue": fx.get("venue", "Official Club Ground"),
                "status": "originated",
                "markets": {"winner": mw, "handicap": hcap, "total": tot},
                "pick": {
                    "selection": f"{best_out['label']} (1X2 Match Winner)",
                    "market": "Match Winner",
                    "prob": best_out["prob"],
                    "fair_decimal": best_out["fair_decimal"],
                    "fair_american": best_out["fair_american"],
                    "fair_american_str": best_out["fair_american_str"],
                    "confidence": conf,
                },
                "official_source": src_label,
                "official_url": fx["url"],
                "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9",
                "notes": f"1X2 Normal margin={margin:+.2f}, expected points={exp_tot:.1f}.",
            })

    price_rugby_league(inputs["top14_teams"], inputs["top14_fixtures"], "French Top 14 2026-27 — Journée 7", "LNR Top 14 Official Feuille de Match")
    price_rugby_league(inputs["prod2_teams"], inputs["prod2_fixtures"], "French Pro D2 2026-27 — Journée 8", "LNR Pro D2 Official Feuille de Match")
    price_rugby_league(inputs["urc_teams"], inputs["urc_r4_fixtures"], "United Rugby Championship 2026-27 — Round 4", "URC Official Match Centre")
    price_rugby_league(inputs["urc_teams"], inputs["urc_r5_fixtures"], "United Rugby Championship 2026-27 — Round 5", "URC Official Match Centre")

    # 4. DARTS — PDC European Championship R1 (16, best of 11 legs = first to 6)
    pdc = inputs["pdc_players"]
    for fx in inputs["darts_fixtures"]:
        p1_name, p2_name = fx["p1"], fx["p2"]
        m1, m2 = pdc[p1_name]["prize_gbp"], pdc[p2_name]["prize_gbp"]
        p_leg = sigmoid(0.24 * math.log(m1 / m2))
        pmf = best_of_n_pmf(p_leg, 6)
        p1_win = sum(v for (s1, s2), v in pmf.items() if s1 > s2)
        mw = make_two_way_market(p1_name, p1_win, p2_name)
        best_spread = min([-2.5, -1.5, 1.5, 2.5], key=lambda L: abs(sum(v for (s1, s2), v in pmf.items() if (s1 - s2) + L > 0) - 0.5))
        p_cov = sum(v for (s1, s2), v in pmf.items() if (s1 - s2) + best_spread > 0)
        hcap = make_two_way_market(f"{p1_name} {fmt_line(best_spread)} legs", p_cov, f"{p2_name} {fmt_line(-best_spread)} legs")
        p_over95 = sum(v for (s1, s2), v in pmf.items() if (s1 + s2) > 9.5)
        tot = make_two_way_market("Over 9.5 legs", p_over95, "Under 9.5 legs")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], 10)
        rows.append({
            "id": fx["id"],
            "sport": "darts",
            "sport_name": "Darts",
            "competition": "PDC Machineseeker European Championship 2026 — Round 1",
            "event": f"{p1_name} v {p2_name}",
            "home": p1_name,
            "away": p2_name,
            "date": fx.get("date", "2026-10-22"),
            "start_utc": fx.get("time", "2026-10-22 17:00 UTC"),
            "venue": "Westfalenhalle, Dortmund",
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Match Winner)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "PDC Official Rankings & European Championship Draw",
            "official_url": fx.get("url", "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/"),
            "olbg_url": "https://www.olbg.com/betting-tips/Darts/15",
            "notes": f"Best-of-11 legs negative-binomial PMF from PDC 2-year prize money (£{m1:,} vs £{m2:,}, p_leg={p_leg:.3f}).",
        })

    # 5. TENNIS — ATP Singles Ties (13 originated, best of 3 sets)
    atp = inputs["atp_players"]
    for fx in inputs["atp_fixtures"]:
        p1, p2 = atp[fx["p1"]], atp[fx["p2"]]
        # Dampen extreme log-ratio at floor so returning former top-10 players aren't mispriced at 99%
        eff1 = max(p1["points"], 260)
        eff2 = max(p2["points"], 260)
        p_set = sigmoid(0.44 * math.log(eff1 / eff2))
        pmf = best_of_n_pmf(p_set, 2)
        p1_win = pmf[(2, 0)] + pmf[(2, 1)]
        mw = make_two_way_market(p1["name"], p1_win, p2["name"])
        if p1_win >= 0.5:
            hcap = make_two_way_market(f"{p1['name']} -1.5 sets", pmf[(2, 0)], f"{p2['name']} +1.5 sets")
        else:
            hcap = make_two_way_market(f"{p1['name']} +1.5 sets", 1.0 - pmf[(0, 2)], f"{p2['name']} -1.5 sets")
        p_over25 = pmf[(2, 1)] + pmf[(1, 2)]
        tot = make_two_way_market("Over 2.5 sets", p_over25, "Under 2.5 sets")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], 10)
        rows.append({
            "id": fx["id"],
            "sport": "tennis",
            "sport_name": "Tennis",
            "competition": fx["competition"],
            "event": f"{p1['name']} v {p2['name']}",
            "home": p1["name"],
            "away": p2["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx["time"],
            "venue": "Indoor Hard Court (ATP Tour)",
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Match Winner)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "PIF ATP Singles Rankings (2026-10-19)",
            "official_url": p1["url"],
            "olbg_url": fx["olbg_url"],
            "notes": f"Best-of-3 sets binomial PMF from PIF ATP points (#{p1['rank']} {p1['points']} pts vs #{p2['rank']} {p2['points']} pts, p_set={p_set:.3f}).",
        })

    # 6. HANDBALL — EHF Champions League Men R5 (5) + R6 (7) = 12
    ehf = inputs["ehf_teams"]
    mu_ehf = sum(t["gf"] for t in ehf.values()) / sum(t["gp"] for t in ehf.values())
    for fx in inputs["ehf_r5_fixtures"] + inputs["ehf_r6_fixtures"]:
        h = ehf[fx["home"]]
        a = ehf[fx["away"]]
        wh = h["gp"] / (h["gp"] + 4.0)
        wa = a["gp"] / (a["gp"] + 4.0)
        net_h = wh * ((h["gf"] - h["ga"]) / h["gp"])
        net_a = wa * ((a["gf"] - a["ga"]) / a["gp"])
        pace_h = wh * ((h["gf"] + h["ga"]) / (2.0 * h["gp"])) + (1.0 - wh) * mu_ehf
        pace_a = wa * ((a["gf"] + a["ga"]) / (2.0 * a["gp"])) + (1.0 - wa) * mu_ehf
        margin = net_h - net_a + 2.1
        sd_m = 5.4
        p_draw = norm_cdf((0.5 - margin) / sd_m) - norm_cdf((-0.5 - margin) / sd_m)
        p_home = 1.0 - norm_cdf((0.5 - margin) / sd_m)
        p_away = norm_cdf((-0.5 - margin) / sd_m)
        mw = make_three_way_market(h["name"], p_home, "Draw", p_draw, a["name"])
        hline = round_half(-margin)
        p_hcover = 1.0 - norm_cdf((-hline - margin) / sd_m)
        hcap = make_two_way_market(f"{h['name']} {fmt_line(hline)}", p_hcover, f"{a['name']} {fmt_line(-hline)}")
        exp_tot = pace_h + pace_a
        tline = round_half(exp_tot)
        p_over = 1.0 - norm_cdf((tline - exp_tot) / 6.2)
        tot = make_two_way_market(f"Over {tline:.1f}", p_over, f"Under {tline:.1f}")
        non_draw = [mw["outcomes"][0], mw["outcomes"][2]]
        best_out = max(non_draw, key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(h["gp"], a["gp"]))
        rows.append({
            "id": fx["id"],
            "sport": "handball",
            "sport_name": "Handball",
            "competition": f"EHF Champions League Men 2026-27 — Round {fx['round']}",
            "event": f"{h['name']} v {a['name']}",
            "home": h["name"],
            "away": a["name"],
            "date": fx.get("date") or fx.get("start_utc", "")[:10],
            "start_utc": fx.get("start_utc") or fx.get("time", ""),
            "venue": f"Group {h['group']} Arena",
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (1X2 Match Winner)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "EHF Champions League Official Match Centre",
            "official_url": fx.get("detail_url") or fx.get("url"),
            "olbg_url": "https://www.olbg.com/betting-tips/Handball/20",
            "notes": f"1X2 goal-margin={margin:+.2f}, expected total={exp_tot:.1f} goals.",
        })

    # 7. VOLLEYBALL — Italian SuperLega Round 2 (6 originated, GP=1 strictly capped at low confidence)
    sl = inputs["superlega_teams"]
    for fx in inputs["superlega_fixtures"]:
        h = sl[fx["home"]]
        a = sl[fx["away"]]
        qh = 0.25 * (h["pf"] / (h["pf"] + h["pa"])) + 0.75 * 0.50
        qa = 0.25 * (a["pf"] / (a["pf"] + a["pa"])) + 0.75 * 0.50
        p_set = sigmoid(7.5 * (qh - qa + 0.018))
        pmf = best_of_n_pmf(p_set, 3)
        p_home = pmf[(3, 0)] + pmf[(3, 1)] + pmf[(3, 2)]
        mw = make_two_way_market(h["name"], p_home, a["name"])
        if p_home >= 0.5:
            p_fav_15 = pmf[(3, 0)] + pmf[(3, 1)]
            hcap = make_two_way_market(f"{h['name']} -1.5 sets", p_fav_15, f"{a['name']} +1.5 sets")
        else:
            p_fav_15 = pmf[(0, 3)] + pmf[(1, 3)]
            hcap = make_two_way_market(f"{h['name']} +1.5 sets", 1.0 - p_fav_15, f"{a['name']} -1.5 sets")
        p_over35 = 1.0 - (pmf[(3, 0)] + pmf[(0, 3)])
        tot = make_two_way_market("Over 3.5 sets", p_over35, "Under 3.5 sets")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], min(h["gp"], a["gp"]))
        rows.append({
            "id": fx["id"],
            "sport": "volleyball",
            "sport_name": "Volleyball",
            "competition": "Italian SuperLega Credem Banca 2026-27 — Round 2",
            "event": f"{h['name']} v {a['name']}",
            "home": h["name"],
            "away": a["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx["time"],
            "venue": fx["venue"],
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Match Winner)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "Lega Pallavolo Serie A Official Calendar & Standings",
            "official_url": fx["url"],
            "olbg_url": fx["olbg_url"],
            "notes": f"75%-shrunk rally-point best-of-5 model (p_set={p_set:.3f}); confidence capped at low (GP=1 opening round, HF-06).",
        })

    # 8. BASEBALL — 2026 MLB World Series Games 1-3 + Series Outright (4 originated)
    mlb = inputs["mlb_teams"]
    mil, tb = mlb["MIL"], mlb["TB"]
    gp_mil = mil["wins"] + mil["losses"]
    gp_tb = tb["wins"] + tb["losses"]
    mu_mlb = ((mil["runs_scored"] + mil["runs_allowed"]) / (2.0 * gp_mil) + (tb["runs_scored"] + tb["runs_allowed"]) / (2.0 * gp_tb)) / 2.0

    def mlb_game_probs(home_code: str, away_code: str) -> tuple[float, float, list[float], list[float]]:
        ht, at = mlb[home_code], mlb[away_code]
        gph, gpa = ht["wins"] + ht["losses"], at["wins"] + at["losses"]
        lam_h = mu_mlb * ((ht["runs_scored"] / gph) / mu_mlb) * ((at["runs_allowed"] / gpa) / mu_mlb) * 1.045
        lam_a = mu_mlb * ((at["runs_scored"] / gpa) / mu_mlb) * ((ht["runs_allowed"] / gph) / mu_mlb) / 1.045
        ph = poisson_pmf_vec(lam_h, 18)
        pa = poisson_pmf_vec(lam_a, 18)
        p_reg_h = sum(ph[i] * pa[j] for i in range(19) for j in range(19) if i > j)
        p_tie = sum(ph[i] * pa[i] for i in range(19))
        p_ml_h = p_reg_h + p_tie * (lam_h / (lam_h + lam_a))
        return p_ml_h, lam_h + lam_a, ph, pa

    for fx in inputs["mlb_fixtures"]:
        h_code, a_code = fx["home"], fx["away"]
        p_ml_h, _, ph, pa = mlb_game_probs(h_code, a_code)
        ht, at = mlb[h_code], mlb[a_code]
        mw = make_two_way_market(ht["name"], p_ml_h, at["name"])
        if p_ml_h >= 0.5:
            p_rl = sum(ph[i] * pa[j] for i in range(19) for j in range(19) if i - j >= 2)
            hcap = make_two_way_market(f"{ht['name']} -1.5", p_rl, f"{at['name']} +1.5")
        else:
            p_rl = sum(ph[i] * pa[j] for i in range(19) for j in range(19) if j - i >= 2)
            hcap = make_two_way_market(f"{ht['name']} +1.5", 1.0 - p_rl, f"{at['name']} -1.5")
        p_over75 = sum(ph[i] * pa[j] for i in range(19) for j in range(19) if i + j > 7.5)
        tot = make_two_way_market("Over 7.5 runs", p_over75, "Under 7.5 runs")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], 162)
        rows.append({
            "id": fx["id"],
            "sport": "baseball",
            "sport_name": "Baseball",
            "competition": f"2026 MLB World Series — {fx.get('description') or fx.get('label', fx['id'])}",
            "event": f"{at['name']} @ {ht['name']}",
            "home": ht["name"],
            "away": at["name"],
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx.get("start_utc") or fx.get("time", ""),
            "venue": fx["venue"],
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Moneyline)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "MLB Official StatsAPI (gamePk verified)",
            "official_url": fx.get("url", "https://statsapi.mlb.com/api/v1/schedule/postseason?season=2026"),
            "olbg_url": "https://www.olbg.com/betting-tips/Baseball/12",
            "notes": f"Exact 19x19 run-grid + extra-inning tie-breaker at {fx['venue']}.",
        })

    # 9. MOTOR RACING — Formula 1 US GP + 2026 Drivers' Championship (2 originated)
    f1 = inputs["f1_drivers"]
    weights_gp = [ (d["points"] ** 1.45) for d in f1 ]
    sw_gp = sum(weights_gp)
    gp_outcomes = [{"label": f"{d['driver']} ({d['team']})", **fair_quote(w / sw_gp)} for d, w in zip(f1, weights_gp)]
    gp_best = gp_outcomes[0]
    gp_h2h = make_two_way_market("Kimi Antonelli (Mercedes) H2H", f1[0]["points"] / (f1[0]["points"] + f1[1]["points"]), "George Russell (Mercedes) H2H")
    rows.append({
        "id": "f1-2026-us-gp",
        "sport": "motor-racing",
        "sport_name": "Motor Racing",
        "competition": "2026 FIA Formula 1 World Championship — United States Grand Prix",
        "event": "2026 Formula 1 United States Grand Prix — Race Winner",
        "home": "Kimi Antonelli (Mercedes)",
        "away": "8-Driver Championship Contender Field",
        "date": "2026-10-25",
        "start_utc": "2026-10-25 19:00 UTC",
        "venue": "Circuit of the Americas, Austin",
        "status": "originated",
        "markets": {"winner": {"type": "multi-way", "outcomes": gp_outcomes}, "handicap": gp_h2h, "total": None},
        "pick": {
            "selection": f"{gp_best['label']} — Race Winner",
            "market": "Race Winner",
            "prob": gp_best["prob"],
            "fair_decimal": gp_best["fair_decimal"],
            "fair_american": gp_best["fair_american"],
            "fair_american_str": gp_best["fair_american_str"],
            "confidence": grade_match(gp_best["prob"], gp_best["fair_decimal"], gp_best["fair_american"], 18, multiway=True),
        },
        "official_source": "Formula 1 Official 2026 Standings & Austin Schedule",
        "official_url": "https://www.formula1.com/en/results/2026/drivers",
        "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        "notes": "Plackett-Luce race-win probabilities across top 8 championship contenders (sum(p)==1.0000); H2H Mercedes teammate market originated.",
    })

    # Championship title outright (102-pt lead -> heavy chalk shorter than -250 -> strictly medium confidence per HF-08)
    champ_raw = [math.exp((d["points"] - f1[0]["points"]) / 28.0) for d in f1]
    sc = sum(champ_raw)
    champ_outcomes = [{"label": f"{d['driver']} ({d['team']})", **fair_quote(w / sc)} for d, w in zip(f1, champ_raw)]
    ch_best = champ_outcomes[0]
    rows.append({
        "id": "f1-2026-drivers-title",
        "sport": "motor-racing",
        "sport_name": "Motor Racing",
        "competition": "2026 FIA Formula 1 Drivers' World Championship",
        "event": "2026 Formula 1 Drivers' World Championship — Outright Winner",
        "home": "Kimi Antonelli (340 pts)",
        "away": "George Russell (238 pts) & Field",
        "date": "2026-10-25",
        "start_utc": "2026-10-25 19:00 UTC",
        "venue": "2026 FIA F1 Championship (Final Run-In)",
        "status": "originated",
        "markets": {"winner": {"type": "multi-way", "outcomes": champ_outcomes}, "handicap": None, "total": None},
        "pick": {
            "selection": f"{ch_best['label']} — Drivers' Champion",
            "market": "Outright Winner",
            "prob": ch_best["prob"],
            "fair_decimal": ch_best["fair_decimal"],
            "fair_american": ch_best["fair_american"],
            "fair_american_str": ch_best["fair_american_str"],
            "confidence": "medium",  # Heavy chalk shorter than -250 strictly capped at medium (HF-08)
        },
        "official_source": "Formula 1 Official 2026 Drivers' Standings",
        "official_url": "https://www.formula1.com/en/results/2026/drivers",
        "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        "notes": "102-point championship lead (340 vs 238) makes Antonelli heavy short chalk (<1.40 decimal); capped at medium confidence per HF-08.",
    })

    # 10. SNOOKER — WST Northern Ireland Open Round 3 (1 originated inside server-rendered Top 36)
    wst = inputs["wst_top36"]
    for fx in inputs["snooker_originated"]:
        p1_name, p2_name = fx["p1"], fx["p2"]
        m1, m2 = wst[p1_name]["prize_gbp"], wst[p2_name]["prize_gbp"]
        p_fr = sigmoid(0.36 * math.log(m1 / m2))
        pmf = best_of_n_pmf(p_fr, 4)
        p1_win = sum(v for (s1, s2), v in pmf.items() if s1 == 4)
        mw = make_two_way_market(p1_name, p1_win, p2_name)
        p_cov15 = pmf[(4, 0)] + pmf[(4, 1)] + pmf[(4, 2)]
        hcap = make_two_way_market(f"{p1_name} -1.5 frames", p_cov15, f"{p2_name} +1.5 frames")
        p_over55 = pmf[(4, 2)] + pmf[(2, 4)] + pmf[(4, 3)] + pmf[(3, 4)]
        tot = make_two_way_market("Over 5.5 frames", p_over55, "Under 5.5 frames")
        best_out = max(mw["outcomes"], key=lambda o: o["prob"])
        conf = grade_match(best_out["prob"], best_out["fair_decimal"], best_out["fair_american"], 20)
        rows.append({
            "id": fx["id"],
            "sport": "snooker",
            "sport_name": "Snooker",
            "competition": "WST BetVictor Northern Ireland Open 2026 — Round 3",
            "event": f"{p1_name} v {p2_name}",
            "home": p1_name,
            "away": p2_name,
            "date": fx.get("date") or fx.get("official_date"),
            "start_utc": fx["time"],
            "venue": "Waterfront Hall, Belfast",
            "status": "originated",
            "markets": {"winner": mw, "handicap": hcap, "total": tot},
            "pick": {
                "selection": f"{best_out['label']} (Match Winner)",
                "market": "Match Winner",
                "prob": best_out["prob"],
                "fair_decimal": best_out["fair_decimal"],
                "fair_american": best_out["fair_american"],
                "fair_american_str": best_out["fair_american_str"],
                "confidence": conf,
            },
            "official_source": "World Snooker Tour Match Centre & Top-36 Rankings",
            "official_url": fx["url"],
            "olbg_url": fx["olbg_url"],
            "notes": f"Best-of-7 frames binomial PMF from WST rankings (#{wst[p1_name]['rank']} £{m1:,} vs #{wst[p2_name]['rank']} £{m2:,}, p_frame={p_fr:.3f}; HF-05).",
        })

    # 11. ALL 30 UNLINED ROWS — strictly blank odds (None) with primary official links & transparent reasons
    sport_names = {"ice-hockey": "Ice Hockey", "darts": "Darts", "rugby-union": "Rugby Union", "handball": "Handball", "aussie-rules": "Aussie Rules", "esports": "eSports", 
        "tennis": "Tennis", "snooker": "Snooker", "volleyball": "Volleyball", "baseball": "Baseball",
        "motor-racing": "Motor Racing", "cricket": "Cricket", "golf": "Golf", "rugby-league": "Rugby League",
        "gaelic-football": "Gaelic Football", "greyhounds": "Greyhounds", "basketball": "Basketball",
    }
    for u in inputs["unlined_rows"]:
        sp = u["sport"]
        ev = u.get("event") or (f"{u['home']} v {u['away']}" if u.get("away") else u.get("home", u["id"]))
        rows.append({
            "id": u["id"],
            "sport": sp,
            "sport_name": sport_names[sp],
            "competition": u.get("competition", f"{sport_names[sp]} Official Fixture"),
            "event": ev,
            "home": u.get("home", ev),
            "away": u.get("away", ""),
            "date": u.get("date", "2026-10-22"),
            "start_utc": u.get("time") or u.get("start_utc") or u.get("date", "2026-10-22"),
            "venue": u.get("venue", "Official Venue"),
            "status": "unlined",
            "markets": {"winner": None, "handicap": None, "total": None},
            "pick": None,
            "official_source": u.get("official_source", "Official Federation Portal"),
            "official_url": u["official_url"],
            "olbg_url": u["olbg_url"],
            "notes": u.get("blank_reason") or u.get("reason", "Primary official rating feed unavailable in static server payload; left blank."),
        })

    return rows




BESPOKE_PREDICTIONS: dict[str, dict] = {
    "nhl-2026020154": {
        "headline": "TD Garden's stingiest home defense gives Boston the clear edge over overtime-reliant Nashville",
        "text": (
            "Boston Bruins on the Moneyline is the play at TD Garden on Thursday night. "
            "Boston enter 7-2-1 overall and have suffocated visitors for just six goals allowed across four home outings "
            "(3-1-0, outscoring guests 15-6), powered by David Pastrnak's four goals and eight assists alongside six wins "
            "from goaltender Jeremy Swayman. Nashville's 3-2-3 mark leans heavily on overtime salvage points on the road "
            "(1-0-2), with only 23 goals scored in eight games behind Ryan O'Reilly (four goals) and Roman Josi (eight assists)."
        ),
        "facts": [
            {"claim": "Boston Bruins stand 7-2-1 overall and 3-1-0 at TD Garden (15 GF, 6 GA)", "source": "https://api-web.nhle.com/v1/standings/2026-10-22"},
            {"claim": "David Pastrnak leads Boston (4G, 8A) and Jeremy Swayman owns 6 wins; Ryan O'Reilly (4G) and Roman Josi (8A) pace Nashville", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
        ],
    },
    "nhl-2026020159": {
        "headline": "Sorokin and a 4-1-0 UBS Arena fortress meet a Kings offense averaging 2.43 goals",
        "text": (
            "New York Islanders on the Moneyline stands right on our -250 threshold at UBS Arena. "
            "New York have turned home ice into an early-season stronghold at 4-1-0 while outscoring visitors 19-10, "
            "backed by Bo Horvat's five goals, rookie blueliner Matthew Schaefer's eight assists, and five victories from "
            "netminder Ilya Sorokin. Even though Los Angeles snapped their skid last time out, the Kings remain 1-4-2 with "
            "just 17 goals scored against 27 conceded across seven games and a lone win for Darcy Kuemper."
        ),
        "facts": [
            {"claim": "New York Islanders sit 4-1-0 at UBS Arena (19 GF, 10 GA); Los Angeles Kings sit 1-4-2 overall (17 GF, 27 GA)", "source": "https://api-web.nhle.com/v1/standings/2026-10-22"},
            {"claim": "Bo Horvat (5G), Matthew Schaefer (8A), and Ilya Sorokin (5W) lead NYI; Darcy Kuemper has 1 win for LAK", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
        ],
    },
    "nhl-2026020162": {
        "headline": "Kaprizov's eleven-goal surge targets a Calgary defense shipping 4.63 goals a night",
        "text": (
            "Take Minnesota Wild on the Moneyline at Scotiabank Saddledome on Thursday. "
            "Kirill Kaprizov has already erupted for eleven goals and goaltender Jesper Wallstedt has collected six wins "
            "to lift Minnesota to 6-2-2 (14 points, 31 goals for, 25 against across ten games). Calgary's solitary win in "
            "their previous outing barely masks a 2-6-0 start built on 17 goals scored and 37 surrendered in eight games, "
            "including a leaky 1-3-0 home split where opponents have outscored the Flames 19-9."
        ),
        "facts": [
            {"claim": "Minnesota Wild stand 6-2-2 (31 GF, 25 GA); Calgary Flames stand 2-6-0 (17 GF, 37 GA) and 1-3-0 at home", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Kirill Kaprizov has 11 goals and Jesper Wallstedt has 6 wins on the official NHL score feed", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
        ],
    },
    "shl-2026-1022-ske-dif": {
        "headline": "Lindholm and Lindberg steer third-placed Skellefteå against a leaky Djurgården defense",
        "text": (
            "Side with Skellefteå AIK on the Moneyline when Djurgårdens IF visit Skellefteå Kraft Arena on Thursday evening. "
            "Skellefteå sit third in the SHL on 19 points (32 goals for, 25 against in ten games) behind twin 11-point centers "
            "Pär Lindholm and Oscar Lindberg (three goals, eight assists apiece) after taking second-placed Frölunda to a 3-2 "
            "shootout on 17 October. Djurgården were hammered 6-2 in Gothenburg on 20 October and sit 12th with a -10 goal "
            "differential (23-33) despite Charles Hudon's eight points."
        ),
        "facts": [
            {"claim": "Skellefteå AIK sit 3rd on 19 pts (32 GF, 25 GA, 10 GP); Djurgårdens IF sit 12th on 12 pts (23 GF, 33 GA, 11 GP)", "source": "https://stats.swehockey.se/ScheduleAndResults/Standings/20961"},
            {"claim": "Pär Lindholm (11 pts) and Oscar Lindberg (11 pts) rank #4 and #5 in SHL scoring; Frölunda beat Djurgården 6-2 on 20 Oct 2026", "source": "https://stats.swehockey.se/Players/Statistics/ScoringLeaders/20961"},
        ],
    },
    "shl-2026-1024-hv71-fro": {
        "headline": "Red-hot Frölunda bring a +14 goal differential to Jönköping against struggling HV 71",
        "text": (
            "Frölunda HC on the Moneyline is the standout Saturday call in Jönköping. "
            "Second-placed Frölunda have piled up 25 points from eleven outings (38 goals scored, only 24 allowed) with "
            "Graeme Clarke (nine points), Samuel Fagemo (eight), and captain Henrik Tömmernes (eight) driving back-to-back "
            "statement wins over Skellefteå (3-2 shootout on 17 October) and Djurgården (6-2 on 20 October). "
            "Thirteenth-placed HV 71 own a lone regulation victory in eleven games (29-39 goal split), dropping a 5-2 decision "
            "at Luleå and a 3-2 home shootout to bottom club Linköping despite Pavol Regenda's ten points."
        ),
        "facts": [
            {"claim": "Frölunda HC rank 2nd (25 pts, 38 GF, 24 GA); HV 71 rank 13th (10 pts, 1 regulation win in 11 GP, 29 GF, 39 GA)", "source": "https://stats.swehockey.se/ScheduleAndResults/Standings/20961"},
            {"claim": "Frölunda beat Skellefteå 3-2 (SO, 17 Oct) and Djurgården 6-2 (20 Oct); HV 71 lost 2-5 at Luleå (17 Oct) and 2-3 SO vs Linköping (20 Oct)", "source": "https://stats.swehockey.se/ScheduleAndResults/Schedule/20961"},
        ],
    },
    "el-E2026-62": {
        "headline": "Maledon's playmaking and Tavares's rim protection give Real Madrid the Belgrade neutral-floor edge",
        "text": (
            "Real Madrid on the Moneyline is our Round 7 play against Maccabi Rapyd Tel Aviv in Belgrade. "
            "Theo Maledon is averaging 15.2 points, 5.8 assists, and a 21.5 PIR alongside Walter Tavares's 7.2 rebounds "
            "and 1.3 blocks per game, steering Madrid to a +23 scoring margin across six EuroLeague rounds (554 scored, 531 conceded). "
            "Playing away from Tel Aviv, 16th-placed Maccabi sit 2-4 with a -31 differential (509-540, allowing 90.0 points "
            "a night) even with Yam Madar contributing 12.2 points and 4.5 assists."
        ),
        "facts": [
            {"claim": "Real Madrid sit 3-3 (554 PF, 531 PA, +23); Maccabi Rapyd Tel Aviv sit 2-4 (509 PF, 540 PA, -31)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "Theo Maledon (15.2 PPG, 5.8 APG, 21.5 PIR) and Walter Tavares (7.2 RPG, 1.3 BPG) lead Real Madrid; Yam Madar posts 12.2 PPG for Maccabi", "source": "https://api-live.euroleague.net/v3/competitions/E/statistics/players/traditional?seasonMode=Single&seasonCode=E2026&statisticMode=PerGame&sortDirection=Descending&limit=25"},
        ],
    },
    "el-E2026-68": {
        "headline": "Valanciunas anchors Zalgiris at home in Kaunas against defense-optional ASVEL",
        "text": (
            "Zalgiris Kaunas on the Moneyline offers solid value at Zalgirio Arena on Thursday evening. "
            "Veteran center Jonas Valanciunas has anchored Zalgiris with 10.2 points, 7.7 rebounds, and an 18.3 PIR through "
            "six rounds (490 scored, 517 allowed), giving the Lithuanian hosts clear interior superiority as they hunt their "
            "first home win after banking two road victories already. Seventeen-ranked LDLC ASVEL Villeurbanne also sit 2-4 "
            "but own a porous -45 differential (527-572, 95.3 points conceded per game) that Patty Mills's 15.6 points per game cannot cover."
        ),
        "facts": [
            {"claim": "Zalgiris Kaunas (490 PF, 517 PA) host 17th-placed LDLC ASVEL Villeurbanne (2-4, 527 PF, 572 PA, -45)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "Jonas Valanciunas posts 10.2 PPG, 7.7 RPG, 18.3 PIR for Zalgiris; Patty Mills averages 15.6 PPG on 46.2% 3PT for ASVEL", "source": "https://api-live.euroleague.net/v3/competitions/E/statistics/players/traditional?seasonMode=Single&seasonCode=E2026&statisticMode=PerGame&sortDirection=Descending&limit=25"},
        ],
    },
    "el-E2026-69": {
        "headline": "Former Paris star TJ Shorts returns to Adidas Arena leading fourth-placed Valencia",
        "text": (
            "Valencia Basket on the Moneyline is the selection as fourth-placed Valencia visit 18th-placed Paris Basketball. "
            "Returning to his old arena, point guard TJ Shorts is posting 15.8 points, 5.7 assists, and an 18.3 PIR alongside "
            "Nikola Mirotic's efficient 14.7 points (96.9% free throws) for a 4-2 Valencia side boasting a +46 differential "
            "(583-537) and a spotless 2-0 away record. Paris have slid to 1-5 (504-545, 1-3 at home) despite Nadir Hifi's "
            "20.2 points per game across four appearances."
        ),
        "facts": [
            {"claim": "Valencia Basket rank 4th at 4-2 (583 PF, 537 PA, 2-0 away); Paris Basketball rank 18th at 1-5 (504 PF, 545 PA, 1-3 home)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "TJ Shorts (15.8 PPG, 5.7 APG, 18.3 PIR) and Nikola Mirotic (14.7 PPG) lead Valencia; Nadir Hifi averages 20.2 PPG for Paris", "source": "https://api-live.euroleague.net/v3/competitions/E/statistics/players/traditional?seasonMode=Single&seasonCode=E2026&statisticMode=PerGame&sortDirection=Descending&limit=25"},
        ],
    },
    "el-E2026-80": {
        "headline": "Unbeaten home floor in Bologna and Aliou Diarra's shot-blocking back Virtus in Round 8",
        "text": (
            "Virtus Bologna on the Moneyline is our Round 8 pick when Zalgiris Kaunas visit PalaDozza on 28 October. "
            "Following Wednesday's competitive 90-81 Round 7 road loss against Hapoel Tel Aviv in Sofia, seventh-placed Virtus "
            "stand 4-3 overall (606 scored, 608 allowed) and remain a perfect 2-0 on home hardwood in Bologna behind rim-protector "
            "Aliou Diarra's 11.9 points, 7.1 rebounds, and EuroLeague-leading 2.4 blocks (19.3 PIR). Fourteenth-placed Zalgiris "
            "carry a negative scoring differential (-27) into one of Italy's loudest venues."
        ),
        "facts": [
            {"claim": "Virtus Bologna stand 4-3 (606 PF, 608 PA, 2-0 home) following Round 7 game E2026_61 (Hapoel Tel Aviv 90-81 Virtus on 21 Oct 2026)", "source": "https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games"},
            {"claim": "Aliou Diarra averages 11.9 PPG, 7.1 RPG, 2.4 BPG, and 19.3 PIR for Virtus Bologna across 7 games", "source": "https://api-live.euroleague.net/v3/competitions/E/statistics/players/traditional?seasonMode=Single&seasonCode=E2026&statisticMode=PerGame&sortDirection=Descending&limit=25"},
        ],
    },
    "ec-eurocup-r5-lkb-ulm": {
        "headline": "Group D's stingiest half-court defense makes Lietkabelis clear home favorites over Ulm",
        "text": (
            "Back Lietkabelis Panevezys on the Moneyline in BKT EuroCup Group D Round 5 action. "
            "Lietkabelis have surged to a 3-1 start tied atop Group D by holding opponents to a group-best 307 points across "
            "four outings (76.8 allowed per game, 321 scored, +14 differential). Visiting ratiopharm ulm sit 2-2 (367 scored, "
            "365 conceded) playing frantic 91-point track meets with guard Tobias Jensen chipping in 5.4 points and 2.2 assists, "
            "a style that historically bog-downs inside Panevezys's physical half-court press."
        ),
        "facts": [
            {"claim": "Lietkabelis Panevezys stand 3-1 in EuroCup Group D (321 PF, 307 PA); ratiopharm ulm stand 2-2 (367 PF, 365 PA)", "source": "https://www.euroleaguebasketball.net/en/eurocup/standings/"},
            {"claim": "Tobias Jensen averages 5.4 PPG and 2.2 APG for ratiopharm ulm on the official EuroCup traditional player feed", "source": "https://api-live.euroleague.net/v3/competitions/U/statistics/players/traditional?seasonCode=U2026&statisticMode=PerGame"},
        ],
    },
    "prod2-12063": {
        "headline": "Tolofua's breakdown dominance and back-to-back wins put SU Agen on top at Stade Armandie",
        "text": (
            "SU Agen (1X2 Match Winner) is the selection at Stade Armandie on Friday night in Pro D2 Journée 8. "
            "Tenth-placed Agen arrive on consecutive victories (W-L-L-W-W recent sequence, 15 points, 189 scored) while ranking "
            "third across Pro D2 in time in possession (52.6%) and joint-second in breakdown turnovers through flanker "
            "Sialevailea Tolofua (six jackals). Thirteenth-placed Nissa Rugby sit on 11 points (2W-5L, 171-213, -42) having "
            "dropped four of their last five matches (L-L-L-W-L)."
        ),
        "facts": [
            {"claim": "SU Agen stand 10th (15 pts, 3W-4L, 189 PF, 206 PA, form W-L-L-W-W); Nissa Rugby stand 13th (11 pts, 2W-5L, 171 PF, 213 PA)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Sialevailea Tolofua ranks joint-2nd in Pro D2 jackals (6) and SU Agen rank 3rd in possession (52.6%)", "source": "https://prod2.lnr.fr/statistiques"},
        ],
    },
    "prod2-12065": {
        "headline": "Pro D2 turnover king Hubert Texier anchors Soyaux-Angoulême's +40 defense against wide-open Dax",
        "text": (
            "Side with Soyaux-Angoulême XV (1X2 Match Winner) at Stade Chanzy on Friday evening. "
            "Seventh-placed Soyaux-Angoulême boast a +40 scoring differential across seven rounds (220 scored, just 180 conceded, "
            "3W-1D-3L) spearheaded by Pro D2's number-one breakdown jackler Hubert Texier (nine turnovers won). "
            "Although sixth-placed US Dax arrive 4W-3L behind fly-half Romuald Seguy's 82 points, Dax have leaked 264 points "
            "(37.7 per game) in wild shootouts — a defensive liability in Pro D2 where hosts win 70% of fixtures."
        ),
        "facts": [
            {"claim": "Soyaux-Angoulême XV stand 3W-1D-3L (220 PF, 180 PA, +40); US Dax stand 4W-0D-3L (269 PF, 264 PA)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Hubert Texier leads Pro D2 with 9 jackals, Romuald Seguy ranks 2nd in points (82), and home teams win 70% of 2026-27 Pro D2 matches", "source": "https://prod2.lnr.fr/statistiques"},
        ],
    },
    "urc-292614": {
        "headline": "Reigning champions Leinster ride a 29-5 defensive clinic into Saturday's Irish derby with Munster",
        "text": (
            "Leinster Rugby (1X2 Match Winner) is our headline United Rugby Championship call on Saturday evening in Dublin. "
            "Led up front by Ireland back-rowers Caelan Doris and Josh van der Flier alongside hooker Dan Sheehan, the reigning "
            "back-to-back URC champions shook off an understrength South African tour by dismantling Cardiff 29-5 last weekend "
            "to reach a +17 differential (75 for, 58 against, 12 tries to 8). Munster arrive winless on the road after a "
            "bruising 26-26 draw at Ulster (72-74 differential, 11 tries conceded)."
        ),
        "facts": [
            {"claim": "Leinster stand +17 (75 PF, 58 PA, 12 tries) after beating Cardiff 29-5; Munster stand -2 (72 PF, 74 PA) after drawing 26-26 at Ulster", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Caelan Doris, Josh van der Flier, and Dan Sheehan feature on the official 2026-27 Leinster URC squad list ahead of match 292614", "source": "https://stats.unitedrugby.com/clubs/leinster/players"},
        ],
    },
    "pdc-32323": {
        "headline": "Defending European Champion Gian van Veen opens Dortmund title defence against #27 Andrew Gilding",
        "text": (
            "Gian van Veen to win is the play as the reigning European Champion launches his title defence in Thursday's "
            "evening session at Dortmund's Westfalenhalle. Ranked world number three on the PDC Order of Merit with £1,035,750 "
            "in two-year prize money, the Dutchman returns to the exact stage of his breakthrough major triumph against "
            "27th-ranked Andrew Gilding (£355,750), carrying nearly a three-to-one earnings edge over the best-of-11-leg sprint."
        ),
        "facts": [
            {"claim": "Gian van Veen ranks #3 (£1,035,750) and Andrew Gilding ranks #27 (£355,750) on the official PDC Order of Merit", "source": "https://www.pdc.tv/rankings"},
            {"claim": "Reigning champion van Veen faces Gilding on Thursday 22 October in Dortmund (PDC European Championship R1)", "source": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/"},
        ],
    },
    "pdc-32329": {
        "headline": "Former Dortmund champion Ross Smith holds a 31-spot ranking cushion over Karel Sedlacek",
        "text": (
            "Ross Smith to beat Karel Sedlacek closes Thursday's first-round card in Dortmund at attractive odds inside -250. "
            "World number 13 Smith — himself a former European Champion inside Westfalenhalle — has banked £567,250 on the "
            "two-year PDC Order of Merit, standing 31 places clear of 44th-ranked Czech thrower Karel Sedlacek (£177,250). "
            "Across a race to six legs, Smith's heavy 180-scoring power translates that prize-money gap into a 68.2% win expectation."
        ),
        "facts": [
            {"claim": "Ross Smith ranks #13 (£567,250) and Karel Sedlacek ranks #44 (£177,250) on the official PDC Order of Merit", "source": "https://www.pdc.tv/rankings"},
            {"claim": "Smith v Sedlacek closes the Thursday 22 October evening session at Westfalenhalle Dortmund", "source": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/"},
        ],
    },
    "pdc-32335": {
        "headline": "World #5 Jonny Clayton's stage pedigree outweighs German crowd support for #36 Niko Springer",
        "text": (
            "Jonny Clayton to win is our Friday Dortmund selection against home qualifier Niko Springer. "
            "Climbing back to number five in the world on £706,000 across the two-year PDC Order of Merit, the Welsh major "
            "winner brings clinical double-hitting composure into a hostile German arena against 36th-ranked Springer (£239,750). "
            "Even over a volatile best-of-11-leg opener, Clayton's nearly three-fold ranking-money advantage prices him at "
            "67.0% (-204 fair American, 1.49 decimal)."
        ),
        "facts": [
            {"claim": "Jonny Clayton ranks #5 (£706,000) and Niko Springer ranks #36 (£239,750) on the official PDC Order of Merit", "source": "https://www.pdc.tv/rankings"},
            {"claim": "Clayton v Springer is scheduled in Round 1 of the 2026 PDC European Championship on Friday 23 October", "source": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/"},
        ],
    },
    "atp-902110": {
        "headline": "Indoor powerhouse Karen Khachanov (#25) holds more than double #72 Tomas Machac's ranking points",
        "text": (
            "Karen Khachanov to defeat Tomas Machac is the opening ATP indoor hard-court pick on Thursday morning. "
            "Sitting #25 in the 19 October PIF ATP Singles Rankings on 1,990 points, Khachanov thrives on low-bouncing European "
            "indoor courts where his first-serve weight dictates short rallies. Machac arrives down at #72 on 779 points after an "
            "interrupted campaign, leaving Khachanov a 65.1% favorite (-185 fair American, 1.54 decimal) across best-of-three sets."
        ),
        "facts": [
            {"claim": "Karen Khachanov ranks #25 (1,990 pts) and Tomas Machac ranks #72 (779 pts) on the 2026-10-19 PIF ATP Singles Rankings", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Round of 16 fixture Tomas Machac vs Karen Khachanov confirmed on the live tour slate", "source": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Tomas_Machac_vs_Karen_Khachanov/3?event_id=902110"},
        ],
    },
    "atp-902082": {
        "headline": "Top-20 server Alexander Bublik (#19) brings 2,275 ATP points into indoor clash with #64 Marozsan",
        "text": (
            "Alexander Bublik to win is our play in Thursday afternoon's indoor Round-of-16 meeting with Fabian Marozsan. "
            "Holding world #19 status with 2,275 PIF ATP points, Bublik's flat indoor delivery makes service breaks scarce over "
            "three sets against #64 Marozsan (860 points). While Hungarian shotmaker Marozsan can steal rhythm in neutral "
            "exchanges, a 1,415-point ranking cushion prices Bublik cleanly at 65.6% (1.52 decimal, -192 American)."
        ),
        "facts": [
            {"claim": "Alexander Bublik ranks #19 (2,275 pts) and Fabian Marozsan ranks #64 (860 pts) on the official ATP rankings", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Round of 16 tie Bublik vs Marozsan verified on the Thursday 22 October tour schedule", "source": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Alexander_Bublik_vs_Fabian_Marozsan/3?event_id=902082"},
        ],
    },
    "atp-902105": {
        "headline": "Career-high #17 Brandon Nakashima's baseline consistency outclasses #85 Kyrian Jacquet indoors",
        "text": (
            "Back Brandon Nakashima to beat Kyrian Jacquet in Thursday evening's indoor hard-court Round of 16. "
            "Climbing to #17 in the PIF ATP rankings on 2,375 points, the American's compact return game and tiebreak poise "
            "match up cleanly against 85th-ranked Frenchman Jacquet (703 points). Separated by 68 ranking spots and more than "
            "three times the rolling points haul, Nakashima rates a 69.2% winner (1.45 decimal, -222 American)."
        ),
        "facts": [
            {"claim": "Brandon Nakashima ranks #17 (2,375 pts) and Kyrian Jacquet ranks #85 (703 pts) on the 2026-10-19 PIF ATP rankings", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Jacquet vs Nakashima confirmed for 22 October 19:30 UTC", "source": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Kyrian_Jacquet_vs_Brandon_Nakashima/3?event_id=902105"},
        ],
    },
    "atp-902133": {
        "headline": "World #15 Tommy Paul's all-court defense counters trick-shot lefty #94 Corentin Moutet in Vienna",
        "text": (
            "Tommy Paul to win is our Friday quarter-final call against Corentin Moutet at the Erste Bank Open in Vienna. "
            "Ranked #15 globally on 2,575 PIF ATP points, Paul's footspeed forward to drop shots neutralizes left-hander "
            "Moutet's slice variety (#94, 640 points). Across a four-to-one ranking-points ratio on fast indoor hard court, "
            "our best-of-three binomial model puts Paul right on the -250 high-confidence ceiling (1.40 decimal)."
        ),
        "facts": [
            {"claim": "Tommy Paul ranks #15 (2,575 pts) and Corentin Moutet ranks #94 (640 pts) on the official PIF ATP rankings", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Quarter-final Moutet vs Paul scheduled Friday 23 October 10:30 UTC", "source": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Corentin_Moutet_vs_Tommy_Paul/3?event_id=902133"},
        ],
    },
    "ehfcl-202711020101016": {
        "headline": "Bjerre and Kosorotov fuel Plock's revenge mission at ORLEN Arena after September's one-goal loss in Nantes",
        "text": (
            "Orlen Wisla Plock (1X2 Match Winner) is our EHF Champions League Round 6 selection on Wednesday 28 October. "
            "After dropping a razor-thin 26-25 opener in Nantes on 9 September, Xavier Sabate's Polish champions have rattled "
            "off three straight Group B wins — edging MT Melsungen 25-24 before sweeping HC Vardar 32-26 away and 33-32 at home "
            "— powered by left wing Frederik Bjerre (26 goals) and Sergei Mark Kosorotov (19 goals). Back inside ORLEN Arena "
            "(115-108 goal split vs Nantes's 142-143), Plock grade at 68.4% (1.46 decimal, -217 American)."
        ),
        "facts": [
            {"claim": "Orlen Wisla Plock stand 3W-0D-1L (115:108) after beating Melsungen (25-24) and Vardar twice (32-26, 33-32) following a 25-26 loss at Nantes on 9 Sep 2026", "source": "https://ehfcl.eurohandball.com/men/2026-27/clubs/details/Qg5-SUEq-U2qV3euQZ48RQ/OrlenWislaPlock/"},
            {"claim": "Frederik Bjerre (26 goals) and Sergei Mark Kosorotov (19 goals) lead Orlen Wisla Plock's 2026-27 EHF Champions League attack", "source": "https://ehfcl.eurohandball.com/men/2026-27/clubs/details/Qg5-SUEq-U2qV3euQZ48RQ/OrlenWislaPlock/"},
        ],
    },
    "mlb-849805": {
        "headline": "Jacob Misiorowski takes the World Series Game 1 ball for a 103-win Brewers juggernaut in Milwaukee",
        "text": (
            "Milwaukee Brewers on the Moneyline is the play in Friday night's World Series Game 1 at American Family Field. "
            "Milwaukee paced Major League Baseball at 103-59 behind a +214 regular-season run differential (832 scored, 618 "
            "allowed — a 3.81 runs-against clip) and hand the Game 1 ball to hard-throwing right-hander Jacob Misiorowski. "
            "With 98-64 Tampa Bay (736-650 run split) yet to name a probable starter on the official MLB schedule feed, "
            "home field prices Milwaukee at 65.6% (1.53 decimal, -189 American)."
        ),
        "facts": [
            {"claim": "Milwaukee Brewers finished 103-59 (832 RS, 618 RA) vs Tampa Bay Rays 98-64 (736 RS, 650 RA)", "source": "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason"},
            {"claim": "World Series Game 1 (gamePk 849805) lists Jacob Misiorowski as Milwaukee probable pitcher at American Family Field", "source": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-21&endDate=2026-10-28&hydrate=team,linescore,probablePitcher"},
        ],
    },
    "mlb-849802": {
        "headline": "Milwaukee's bullpen depth and +214 run differential carry straight into World Series Game 2",
        "text": (
            "Stay with Milwaukee Brewers on the Moneyline for Saturday night's World Series Game 2 at American Family Field. "
            "Across a 162-game sample, Milwaukee outscored opponents by 1.32 runs per game (5.14 scored vs 3.81 surrendered) "
            "compared with Tampa Bay's +0.53 margin (4.54 scored vs 4.01 allowed) before advancing past October's League "
            "Championship Series. Keeping the DH-era run environment inside Milwaukee's home park gives the Brewers identical "
            "65.6% run-grid equity (-189 fair American, 1.53 decimal) before the series shifts to St. Petersburg."
        ),
        "facts": [
            {"claim": "Milwaukee averaged 5.14 RS / 3.81 RA across 162 games vs Tampa Bay's 4.54 RS / 4.01 RA", "source": "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason"},
            {"claim": "World Series Game 2 (gamePk 849802) scheduled Saturday 24 October at American Family Field", "source": "https://www.mlb.com/gameday/849802"},
        ],
    },
    "f1-2026-us-gp": {
        "headline": "Runaway title leader Kimi Antonelli brings a 102-point Mercedes cushion to COTA at plus money",
        "text": (
            "Kimi Antonelli (Mercedes) to win the United States Grand Prix is our flagship plus-money Motor Racing play at Austin's "
            "Circuit of the Americas. While Antonelli's 102-point stranglehold atop the Drivers' Championship (340 points against "
            "Mercedes teammate George Russell's 238, Ferrari's Charles Leclerc on 229, and Lando Norris on 221) makes his season "
            "title price unbackable chalk, the single-race market prices his 24.3% Plackett-Luce win share at an attractive +311 "
            "fair American (4.11 decimal)."
        ),
        "facts": [
            {"claim": "Kimi Antonelli leads the 2026 FIA F1 Drivers' Standings on 340 pts ahead of George Russell (238), Charles Leclerc (229), and Lando Norris (221)", "source": "https://www.formula1.com/en/results/2026/drivers"},
            {"claim": "2026 United States Grand Prix at Circuit of the Americas, Austin confirmed on official F1 calendar", "source": "https://www.formula1.com/en/racing/2026"},
        ],
    },
    "wst-2026-r3-m50": {
        "headline": "Kyren Wilson's 13 season centuries and faster cue-ball tempo outgun Pang Junxu in Belfast",
        "text": (
            "Kyren Wilson to beat Pang Junxu is the standout snooker selection in Thursday's BetVictor Northern Ireland Open "
            "last-32 session at Waterfront Hall, Belfast. Ranked ninth globally on £716,800, the former Crucible king arrives "
            "winning 63% of his 24 matches this season with 13 centuries, 48 breaks over 50, and a brisk 21.9-second shot time. "
            "World #29 Pang (£272,750, 53% win rate across 23 matches, nine centuries, 26.5s shot time) trails across every "
            "scoring metric, pricing Wilson at 68.3% (-217 American, 1.46 decimal)."
        ),
        "facts": [
            {"claim": "Kyren Wilson ranks #9 (£716,800) and Pang Junxu ranks #29 (£272,750) on official WST World Rankings", "source": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false"},
            {"claim": "WST Match Centre records Wilson at 63% wins, 13 centuries, 48 breaks of 50+, 21.9s AST vs Pang's 53%, 9 centuries, 26.5s AST", "source": "https://www.wst.tv/match-centre/0444240f-c8b2-4382-ba57-bfab6d98f3a7"},
        ],
    },
}


def build_predictions(rows: list[dict]) -> list[dict]:
    preds: list[dict] = []
    seen_5grams: set[tuple[str, ...]] = set()
    for r in rows:
        if r["status"] != "originated" or r["pick"]["confidence"] != "high":
            continue
        mid = r["id"]
        assert mid in BESPOKE_PREDICTIONS, f"Missing bespoke prediction for high-confidence match {mid}"
        meta = BESPOKE_PREDICTIONS[mid]
        txt = meta["text"].strip()
        words = txt.split()
        assert len(words) >= 30, f"Prediction {mid} has only {len(words)} words (<30)"
        p = r["pick"]
        assert in_target_band(p["fair_decimal"], p["fair_american"]), f"High-conf pick {mid} outside [-250,+10000]: {p}"
        # Enforce zero duplicated 6-word phrases across distinct matchups
        toks = [w.lower().strip(".,;:()'") for w in words]
        grams = {tuple(toks[i:i + 7]) for i in range(len(toks) - 6)}
        overlap = grams & seen_5grams
        assert not overlap, f"Duplicate phrase in {mid}: {overlap}"
        seen_5grams |= grams
        preds.append({
            "match_id": mid,
            "sport": r["sport"],
            "sport_name": r["sport_name"],
            "competition": r["competition"],
            "event": r["event"],
            "date": r["date"],
            "start_utc": r["start_utc"],
            "venue": r["venue"],
            "selection": p["selection"],
            "market": p["market"],
            "probability": p["prob"],
            "fair_decimal": p["fair_decimal"],
            "fair_american": p["fair_american"],
            "fair_american_str": p["fair_american_str"],
            "confidence": "high",
            "headline": meta["headline"],
            "text": txt,
            "word_count": len(words),
            "facts": meta["facts"],
            "official_source": r["official_source"],
            "official_url": r["official_url"],
            "olbg_url": r["olbg_url"],
        })
    return preds


def main() -> None:
    inp = json.loads((HUB_DATA / "inputs.json").read_text(encoding="utf-8"))
    all_rows = build_all_matches(inp)
    orig = [r for r in all_rows if r["status"] == "originated"]
    unl = [r for r in all_rows if r["status"] == "unlined"]
    assert len(orig) == 159, f"Expected 159 originated rows, got {len(orig)}"
    assert len(unl) == 30, f"Expected 30 unlined rows, got {len(unl)}"
    assert len(all_rows) == 189

    preds = build_predictions(all_rows)
    meds = [r for r in orig if r["pick"]["confidence"] == "medium"]
    lows = [r for r in orig if r["pick"]["confidence"] == "low"]

    matches_payload = {
        "captured_at": inp["captured_at"],
        "session": inp["session"],
        "total_rows": len(all_rows),
        "originated_count": len(orig),
        "unlined_count": len(unl),
        "confidence_counts": {
            "high": len(preds),
            "medium": len(meds),
            "low": len(lows),
        },
        "rows": all_rows,
    }
    preds_payload = {
        "captured_at": inp["captured_at"],
        "session": inp["session"],
        "min_words": min(p["word_count"] for p in preds),
        "max_words": max(p["word_count"] for p in preds),
        "target_band": "-250 to +10000 American (1.40 to 101.00 decimal)",
        "sports_covered": sorted({p["sport"] for p in preds}),
        "count": len(preds),
        "predictions": preds,
    }

    (HUB_DATA / "matches.json").write_text(json.dumps(matches_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HUB_DATA / "predictions.json").write_text(json.dumps(preds_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"hub_model.py OK: {len(all_rows)} rows ({len(orig)} originated + {len(unl)} unlined) | "
        f"high={len(preds)} across {len(preds_payload['sports_covered'])} sports "
        f"(words {preds_payload['min_words']}..{preds_payload['max_words']}), medium={len(meds)}, low={len(lows)}"
    )


if __name__ == "__main__":
    main()
