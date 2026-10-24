#!/usr/bin/env python3
"""Originated lines for the /compass/ desk.

Every price is ours: derived from official captured statistics (Poisson goal/run
models, normal-margin families, binomial leg model) or, where no official
fixture-level statistic exists, from the OLBG community tip share with shrinkage
(basis 'olbg_community', shade 0.8). No bookmaker price is read, scraped or
compared (the bookmaker odds that appear on nhl.com schedule rows are ignored).

Confidence (METHODOLOGY.md):
  high   = numeric family + p >= 0.62 + our price inside the -250..+10000 band
  medium = numeric p >= 0.55, or community/ladder p >= 0.70
  low    = otherwise
Totals are capped at medium. Score = 10 * p * shade (1.0 numeric, 0.8 community),
capped at 7.5 when in band.
"""
from __future__ import annotations

import json
import math
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "compass"

AS_OF = "2026-10-24T22:45:00Z"
BAND_MIN, BAND_MAX = -250, 10000
HIGH_P, MED_P, COMM_MED = 0.62, 0.55, 0.70

NHL_TEAM = {
    "BOS": (42, 22, 11), "TBL": (34, 29, 10), "OTT": (31, 30, 11), "CAR": (47, 33, 12),
    "NYR": (37, 29, 12), "NJD": (36, 32, 11), "TOR": (43, 39, 12), "NYI": (29, 23, 10),
    "MTL": (34, 35, 10), "FLA": (31, 34, 11), "DET": (28, 30, 10), "WSH": (30, 29, 9),
    "BUF": (28, 37, 10), "PIT": (37, 38, 11), "PHI": (24, 42, 13), "CBJ": (20, 29, 8),
    "UTA": (41, 36, 11), "MIN": (32, 27, 11), "DAL": (26, 17, 10), "EDM": (47, 32, 10),
    "VGK": (46, 36, 12), "SEA": (44, 37, 11), "COL": (47, 34, 11), "SJS": (33, 37, 11),
    "STL": (35, 31, 10), "WPG": (26, 29, 10), "ANA": (32, 37, 11), "NSH": (23, 30, 9),
    "CGY": (19, 38, 9), "LAK": (21, 32, 9),
}
NBA_REC = {  # (w, l, home_w, home_l, road_w, road_l)
    "PHI": (2, 0, 1, 0, 1, 0), "MIL": (0, 2, 0, 1, 0, 1), "DEN": (0, 1, 0, 0, 0, 1),
    "NO": (0, 2, 0, 1, 0, 1), "CLE": (0, 1, 0, 0, 0, 1), "BKN": (0, 1, 0, 1, 0, 0),
    "DAL": (1, 1, 0, 0, 1, 1), "SA": (0, 2, 0, 0, 0, 2), "ATL": (2, 0, 0, 0, 2, 0),
    "HOU": (2, 0, 1, 0, 1, 0), "WAS": (1, 1, 1, 1, 0, 0), "CHI": (1, 1, 0, 0, 1, 1),
    "GS": (0, 2, 0, 1, 0, 1), "PHX": (0, 1, 0, 0, 0, 1),
}


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_probs(lam_home: float, lam_away: float, max_goals: int = 14):
    ph = pw = pd_ = 0.0
    for a in range(max_goals + 1):
        for b in range(max_goals + 1):
            p = poisson_pmf(a, lam_home) * poisson_pmf(b, lam_away)
            if a > b:
                ph += p
            elif a == b:
                pd_ += p
            else:
                pw += p
    return ph, pw, pd_


def nhl_lambda(abb_home: str, abb_away: str):
    gf, ga, gp = NHL_TEAM[abb_home]
    gf_a, ga_a, gp_a = NHL_TEAM[abb_away]
    league = sum(v[0] for v in NHL_TEAM.values()) / sum(v[2] for v in NHL_TEAM.values())
    att_h, df_h = gf / gp / league, ga / gp / league
    att_a, df_a = gf_a / gp_a / league, ga_a / gp_a / league
    lam_h = league * att_h * df_a * 1.06
    lam_a = league * att_a * df_h * 0.98
    return lam_h, lam_a, league


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def american(p: float) -> int:
    if p >= 0.999:
        return -990
    if p <= 0.001:
        return 10000
    v = -100.0 * p / (1.0 - p) if p > 0.5 else 100.0 * (1.0 - p) / p
    return int(math.floor(v + 0.5))


def in_band(am: int) -> bool:
    return BAND_MIN <= am <= BAND_MAX


def conf(p: float, basis: str, kind: str) -> str:
    numeric = basis in ("poisson", "poisson_runs", "normal_margin", "binomial_legs")
    if numeric and p >= HIGH_P and in_band(american(p)) and kind != "total":
        return "high"
    if numeric and p >= MED_P:
        return "medium"
    if p >= COMM_MED:
        return "medium"
    return "low"


def community_p(tips, total) -> float:
    if not tips or not total:
        return 0.5
    share = tips / total
    w = 0.85 if total >= 10 else (0.7 if total >= 6 else 0.5)
    p = 0.5 + w * (share - 0.5)
    cap = 0.60 if total <= 3 else 0.72
    return min(max(p, 0.30), cap)


def base_row(f, market, selection, p, basis, kind, assumption, quality=1.0):
    p = min(max(p, 0.01), 0.99)
    p_r = round(p, 4)
    am = american(p_r)
    return {
        "fixture_id": f["id"], "market": market, "selection": selection,
        "probability": p_r, "decimal": round(1.0 / p_r, 3), "american": am,
        "american_display": str(am), "in_band": in_band(am), "basis": basis,
        "kind": kind, "quality": quality, "assumption": assumption,
        "confidence": conf(p, basis, kind), "sport": f["sport"], "home": f["home"],
        "away": f["away"], "start_utc": f["start_utc"], "official_url": f["official_url"],
    }


def half_line(tot: float) -> float:
    return math.floor(tot + 0.25) + 0.5


def build():
    fx = json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))
    lines = []
    for f in fx["fixtures"]:
        kind = f["inputs"]["kind"]
        o = f.get("olbg_listing") or {}
        _DARTS_OUT = False
        if kind == "nhl":
            lam_h, lam_a, league = nhl_lambda(f["inputs"]["home"], f["inputs"]["away"])
            ph, pw, pd_ = poisson_probs(lam_h, lam_a)
            p_home = ph + 0.5 * pd_
            assume = (f"Expected goals are the geometric mean of each side's scoring rate and the "
                      f"opponent's conceding rate (league average {league:.2f} goals/game from the 30 "
                      f"captured teams, flag cmp-15) with home multipliers 1.06/0.98; a tied "
                      f"regulation score is split evenly because the money line settles with overtime.")
            lines.append(base_row(f, "Match winner (money line, incl. OT)", f["home"], p_home, "poisson", "winner", assume))
            lines.append(base_row(f, "Match winner (money line, incl. OT)", f["away"], 1 - p_home, "poisson", "winner", assume))
            p_h15 = sum(poisson_pmf(a, lam_h) * poisson_pmf(b, lam_a)
                        for a in range(15) for b in range(15) if a >= b + 2)
            lines.append(base_row(f, "Puck line (handicap)", f"{f['home']} -1.5", p_h15, "poisson", "handicap", assume))
            lines.append(base_row(f, "Puck line (handicap)", f"{f['away']} +1.5", 1 - p_h15, "poisson", "handicap", assume))
            lv = half_line(lam_h + lam_a)
            p_over = 1 - sum(poisson_pmf(a, lam_h) * poisson_pmf(b, lam_a)
                             for a in range(15) for b in range(15) if a + b <= math.floor(lv))
            lines.append(base_row(f, f"Game total {lv}", f"Over {lv}", p_over, "poisson", "total", assume))
            lines.append(base_row(f, f"Game total {lv}", f"Under {lv}", 1 - p_over, "poisson", "total", assume))
        elif kind == "mlb":
            i = f["inputs"]
            base = 4.5
            sp_h = 0.92 if i["home_sp_era"] < 2.8 else (0.97 if i["home_sp_era"] < 4.0 else 1.0)
            sp_a = 0.92 if i["away_sp_era"] < 2.8 else (0.97 if i["away_sp_era"] < 4.0 else 1.0)
            lam_h = base * (i["home_rs_pg"] / base) * (i["away_ra_pg"] / base) * sp_h * 1.03
            lam_a = base * (i["away_rs_pg"] / base) * (i["home_ra_pg"] / base) * sp_a
            ph, pw, pd_ = poisson_probs(lam_h, lam_a, 20)
            p_home = ph + 0.5 * pd_
            assume = (f"Expected runs combine each club's 2026 run rate with the opponent's run "
                      f"conceded rate (baseline {base} runs/team/game), scaled for both starters "
                      f"(home SP {i['home_sp_era']} ERA / {i['home_sp_whip']} WHIP; away SP "
                      f"{i['away_sp_era']} ERA / {i['away_sp_whip']} WHIP, official StatsAPI); a tie "
                      f"is split evenly because extra innings decide the money line. No official "
                      f"league-average runs source was captured, so the baseline is a fixed constant.")
            lines.append(base_row(f, "Match winner (money line)", f["home"], p_home, "poisson_runs", "winner", assume))
            lines.append(base_row(f, "Match winner (money line)", f["away"], 1 - p_home, "poisson_runs", "winner", assume))
            p_h15 = sum(poisson_pmf(a, lam_h) * poisson_pmf(b, lam_a)
                        for a in range(21) for b in range(21) if a >= b + 2)
            lines.append(base_row(f, "Run line (handicap)", f"{f['home']} -1.5", p_h15, "poisson_runs", "handicap", assume))
            lines.append(base_row(f, "Run line (handicap)", f"{f['away']} +1.5", 1 - p_h15, "poisson_runs", "handicap", assume))
            lv = half_line(lam_h + lam_a)
            p_over = 1 - sum(poisson_pmf(a, lam_h) * poisson_pmf(b, lam_a)
                             for a in range(21) for b in range(21) if a + b <= math.floor(lv))
            lines.append(base_row(f, f"Game total {lv}", f"Over {lv}", p_over, "poisson_runs", "total", assume))
            lines.append(base_row(f, f"Game total {lv}", f"Under {lv}", 1 - p_over, "poisson_runs", "total", assume))
        elif kind == "nba":
            h, a = f["inputs"]["home"], f["inputs"]["away"]
            hw, hl = NBA_REC[h][0], NBA_REC[h][1]
            ar, al = NBA_REC[a][4], NBA_REC[a][5]
            p_home = min(max(0.5 + 0.04 + 0.10 * (hw - hl) - 0.08 * (ar - al), 0.35), 0.65)
            assume = ("Two-game season: probability is a 0.5 prior plus 4 points of home edge, 10 "
                      "points per point of the home win/loss record and 8 points per point of the "
                      "visitor's road record, capped at 35-65%. 2025-26 priors unavailable (flag "
                      "cmp-16); confidence capped at medium.")
            lines.append(base_row(f, "Match winner (money line)", f["home"], p_home, "normal_margin", "winner", assume, 0.9))
            lines.append(base_row(f, "Match winner (money line)", f["away"], 1 - p_home, "normal_margin", "winner", assume, 0.9))
            m = (p_home - 0.5) * 2 * 9.0
            p_cover_home = normal_cdf((m - 5.5) / 8.0)
            lines.append(base_row(f, "Point spread (handicap)", f"{f['home']} -5.5", p_cover_home,
                                  "normal_margin", "handicap",
                                  "Standard 5.5-point line: expected margin is the model win gap "
                                  "scaled to a 9-point spread, against an 8-point margin standard "
                                  "deviation (two-game sample — illustrative, flag cmp-16).", 0.7))
            lines.append(base_row(f, "Point spread (handicap)", f"{f['away']} +5.5", 1 - p_cover_home,
                                  "normal_margin", "handicap",
                                  "Visitor covering +5.5: the home margin is 5 points or fewer.", 0.7))
        elif kind in ("rugby", "gaelic", "cricket"):
            home_edge = f["inputs"].get("home_edge", 0.0)
            away_edge = f["inputs"].get("away_edge", 0.0)
            sigma = {"rugby": 12.0, "gaelic": 8.0, "cricket": 25.0}[kind]
            home_adv = {"rugby": 2.5, "gaelic": 1.5, "cricket": 2.0}[kind]
            m = (home_edge - away_edge) * sigma * 2 + home_adv
            p_home = normal_cdf(m / sigma)
            assume = (f"Normal margin distribution (sigma {sigma:g}) with the home edge set from the sourced "
                      f"facts on this record (form, series position, venue, squad quality).")
            lines.append(base_row(f, "Match winner (2-way)", f["home"], p_home, "normal_margin", "winner", assume))
            lines.append(base_row(f, "Match winner (2-way)", f["away"], 1 - p_home, "normal_margin", "winner", assume))
            if kind == "gaelic" and f["inputs"].get("handicap") is not None:
                x = f["inputs"]["handicap"]
                underdog = f["inputs"]["underdog_side"]
                p_cover = normal_cdf((x - m) / sigma)
                lines.append(base_row(f, "3-way handicap", f"{underdog} +{x:g}", p_cover,
                                      "normal_margin", "handicap",
                                      f"Underdog covering +{x:g}: the home margin is {x:g} or fewer "
                                      f"(3-way handicap, as listed on OLBG)."))
                lines.append(base_row(f, "3-way handicap", f"{f['home']} -{x:g}", 1 - p_cover,
                                      "normal_margin", "handicap",
                                      f"Home side winning by more than {x:g} (3-way handicap)."))
            elif kind in ("rugby", "cricket") and abs(m) >= 3:
                line = max(5.5, round(abs(m) + 2) if kind == "rugby" else round(abs(m) / 5) * 5)
                if m > 0:
                    p_fav = normal_cdf((m - line) / sigma)
                    lines.append(base_row(f, "Match handicap", f"{f['home']} -{line:g}", p_fav,
                                          "normal_margin", "handicap",
                                          f"Home side winning by more than {line:g} (normal margin, sigma {sigma:g})."))
                    lines.append(base_row(f, "Match handicap", f"{f['away']} +{line:g}", 1 - p_fav,
                                          "normal_margin", "handicap",
                                          f"Away side covering +{line:g}: home margin {line:g} or fewer."))
                else:
                    line_a = max(5.5, round(-m + 2))
                    p_fav = normal_cdf((-line_a - m) / sigma)
                    lines.append(base_row(f, "Match handicap", f"{f['away']} -{line_a:g}", p_fav,
                                          "normal_margin", "handicap",
                                          f"Away side winning by more than {line_a:g} (normal margin, sigma {sigma:g})."))
                    lines.append(base_row(f, "Match handicap", f"{f['home']} +{line_a:g}", 1 - p_fav,
                                          "normal_margin", "handicap",
                                          f"Home side covering +{line_a:g}: away margin {line_a:g} or fewer."))
        elif kind == "handball":
            home_edge = f["inputs"].get("home_edge", 0.0)
            away_edge = f["inputs"].get("away_edge", 0.0)
            sigma = 6.5
            m = (home_edge - away_edge) * sigma * 2 + 1.5
            p_draw = normal_cdf(1 / sigma) - normal_cdf(-1 / sigma)
            p_home = normal_cdf(m / sigma) - 0.5 * p_draw
            p_away = 1 - p_home - p_draw
            assume = (f"Normal margin distribution (sigma {sigma:g} goals) with a 1.5-goal home edge; the "
                      f"draw is the mass inside +/-1 goal (3-way money line, regulation time only). "
                      f"Edge terms come from the sourced facts on this record.")
            lines.append(base_row(f, "Money line (3-way, regulation)", f["home"], p_home, "normal_margin", "winner", assume))
            lines.append(base_row(f, "Money line (3-way, regulation)", "Tie", p_draw, "normal_margin", "winner", assume))
            lines.append(base_row(f, "Money line (3-way, regulation)", f["away"], p_away, "normal_margin", "winner", assume))
            if m > 4:
                p_c = normal_cdf((m - 4.5) / sigma)
                lines.append(base_row(f, "Match handicap (half-goal line)", f"{f['home']} -4.5", p_c,
                                      "normal_margin", "handicap", "Home side winning by 5 or more goals."))
                lines.append(base_row(f, "Match handicap (half-goal line)", f"{f['away']} +4.5", 1 - p_c,
                                      "normal_margin", "handicap", "Away side covering +4.5: home margin 4 goals or fewer."))
        elif kind == "volleyball":
            p_home = 0.70 if f["inputs"].get("elite") else 0.62
            assume = ("Class ladder: the better-established club of the pairing is priced at 62% (70% when the pairing is a top-two club against a clearly weaker or newly promoted side, per the captured league context) "
                      "(top-tier European club fixtures are heavily one-sided; set outcomes are not "
                      "priced because no official set-level statistics were captured). Where the "
                      "OLBG community favours the other side the share is recorded on the OLBG "
                      "list and the divergence is flagged (cmp-08).")
            lines.append(base_row(f, "Match winner (best of 5)", f["home"], p_home, "class_ladder", "winner", assume))
            lines.append(base_row(f, "Match winner (best of 5)", f["away"], 1 - p_home, "class_ladder", "winner", assume))
        elif kind == "tennis":
            home_edge = f["inputs"].get("home_edge", 0.0)
            away_edge = f["inputs"].get("away_edge", 0.0)
            p_home = min(max(0.5 + 0.5 * (home_edge - away_edge), 0.30), 0.75)
            assume = ("Match-winner probability from the sourced form facts on this record (rounds "
                      "survived, quality of beaten opponents, seeding where official).")
            lines.append(base_row(f, "Match winner", f["home"], p_home, "normal_margin", "winner", assume))
            lines.append(base_row(f, "Match winner", f["away"], 1 - p_home, "normal_margin", "winner", assume))
        elif kind == "darts":
            home_edge = f["inputs"].get("home_edge", 0.0)
            away_edge = f["inputs"].get("away_edge", 0.0)
            p_leg = min(max(0.5 + 0.5 * (away_edge - home_edge), 0.30), 0.70)
            p_win = sum(comb(19, k) * p_leg ** k * (1 - p_leg) ** (19 - k) for k in range(10, 20))
            assume = ("Binomial leg calculation over the best-of-19 format: the leg win rate is set from "
                      "the sourced facts (rounds won, match averages, finish quality); the match "
                      "probability is the binomial tail to 10 legs.")
            lines.append(base_row(f, "Match winner (best of 19 legs)", f["away"], p_win, "binomial_legs", "winner", assume))
            lines.append(base_row(f, "Match winner (best of 19 legs)", f["home"], 1 - p_win, "binomial_legs", "winner", assume))
        elif kind == "darts_outright":
            p = community_p(f["inputs"].get("tips"), f["inputs"].get("total_tips"))
            # same-day event; community basis only
            _DARTS_OUT = True
            lines.append(base_row(f, "Win tournament (Finals Day)", f["inputs"]["selection"], p,
                                  "olbg_community", "outright",
                                  "Community tip share on the OLBG event (Littler 13/21) with 15% "
                                  "shrinkage to 0.5; corroborated by the official PDC result line "
                                  "(averages 105.05 in round 1 then 114.47 in round 2).", 0.8))
        elif kind == "outright":
            p = community_p(f["inputs"].get("tips"), f["inputs"].get("total_tips"))
            _DARTS_OUT = True
            lines.append(base_row(f, "Win tournament (ante-post)", f["inputs"]["selection"], p,
                                  "olbg_community", "outright",
                                  "Community tip share on the OLBG ante-post event with 15% "
                                  "shrinkage to 0.5; no official market page captured (flagged).", 0.8))
        elif kind == "olbg_only":
            if f["inputs"].get("prop_market"):
                continue
            tips = total = None
            if o.get("tips") and "/" in str(o["tips"]):
                tips, total = (int(x) for x in o["tips"].split("/"))
            p = community_p(tips, total)
            lines.append(base_row(f, "Win (OLBG community line)", o.get("selection") or f["away"], p,
                                  "olbg_community", "winner",
                                  "No official fixture-level statistics were captured; the price is "
                                  "the OLBG community tip share with 15% shrinkage to 0.5 and is "
                                  "flagged as unverified.", 0.8))
    order = {"low": 0, "medium": 1, "high": 2}
    by_fix = {}
    for l in lines:
        by_fix.setdefault(l["fixture_id"], []).append(l)
    for fid, rows in by_fix.items():
        f = next(x for x in fx["fixtures"] if x["id"] == fid)
        capped = bool(f["blank_reason"]) or f["inputs"]["kind"] == "nba"
        if capped:
            for l in rows:
                if order[l["confidence"]] > 1:
                    l["confidence"] = "medium"
        if f["inputs"]["kind"] in ("outright", "darts_outright"):
            for l in rows:
                if order[l["confidence"]] > 0:
                    l["confidence"] = "low"
    payload = {"as_of_utc": AS_OF, "count": len(lines),
               "in_band": sum(1 for l in lines if l["in_band"]), "lines": lines}
    (DATA / "lines.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"compass_model: {len(lines)} originated lines ({payload['in_band']} in band)")


if __name__ == "__main__":
    build()
