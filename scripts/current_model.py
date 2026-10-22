#!/usr/bin/env python3
"""Originate prices for every /current/ fixture from first-hand official captures.

Markets originated per fixture (where an official strength input exists):
  match winner (moneyline, 2- or 3-way), handicap, match total - and for the
  F1 round an outright race-winner market plus a championship head-to-head.

High-confidence gate (identical to METHODOLOGY.md, applied to EVERY originated
market and EVERY side of it, not just the two-way moneyline):
    model probability >= 0.7000  AND  fair American price inside -250 ... +10000
A fair no-vig price of -250 is p = 0.714286, so the band is a 1.43-point window.
Two-way moneylines almost never land in it; alternate handicap and total lines
do, which is the point of searching all of them.

Nothing here reads a bookmaker price. Nothing is inferred: a fixture with no
official strength input publishes a blank line and a written reason.

Stdlib only. Deterministic.
"""

from __future__ import annotations

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURE = os.path.join(ROOT, "data", "current", "capture")
DATA = os.path.join(ROOT, "data", "current")

BAND_MIN_P = 0.7000
BAND_MAX_P = 250.0 / 350.0          # fair -250
BAND_MAX_PRICE = 10000
MEDIUM_P = 0.6000


def load(name):
    with open(os.path.join(CAPTURE, name), encoding="utf-8") as handle:
        return json.load(handle)


def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def poisson_pmf(lam, n_max):
    """Iterative Poisson pmf: stable at the large lambdas handball needs (~32)."""
    out = [math.exp(-lam)]
    for k in range(1, n_max + 1):
        out.append(out[-1] * lam / k)
    return out


def price(p):
    """No-vig fair decimal + American from a model probability.

    The probability is rounded to four decimals FIRST and every published price
    is derived from that rounded number, so any reader can reproduce the decimal
    and American figures from the probability printed beside them.
    """
    if p <= 0.0:
        return {"p": 0.0, "fair_decimal": None, "fair_american": None, "american_exact": None}
    pr = round(p, 4)
    decimal = 1.0 / pr
    if decimal >= 2.0:
        american = 100.0 * (decimal - 1.0)
    else:
        american = -100.0 / (decimal - 1.0)
    return {"p": pr, "fair_decimal": round(decimal, 2),
            "fair_american": int(round(american)), "american_exact": american}


def in_band(p):
    return BAND_MIN_P <= p <= BAND_MAX_P and (1.0 / p) <= (BAND_MAX_PRICE + 100.0)


def label(p, band):
    if p >= BAND_MIN_P and band:
        return "high"
    if p >= BAND_MIN_P:
        return "medium"      # shorter than -250: capped, per METHODOLOGY.md
    if p >= MEDIUM_P:
        return "medium"
    return "low"


def half(x):
    """Nearest half-point, never exactly on a whole number (avoids a push)."""
    v = math.floor(x * 2.0 + 0.5) / 2.0
    if abs(v - round(v)) < 1e-9:
        v += 0.5 if x >= v else -0.5
    return round(v, 1)


# --------------------------------------------------------------------------- #
# Distribution helpers
# --------------------------------------------------------------------------- #
class PoissonGrid:
    """Joint independent-Poisson score distribution (hockey, handball, baseball)."""

    def __init__(self, lam_home, lam_away, n_max, settle_ties=False):
        ph = poisson_pmf(lam_home, n_max)
        pa = poisson_pmf(lam_away, n_max)
        self.p_home = self.p_draw = self.p_away = 0.0
        self.margin = {}      # margin -> probability
        self.total = {}       # total -> probability
        for i in range(n_max + 1):
            for j in range(n_max + 1):
                w = ph[i] * pa[j]
                if i > j:
                    self.p_home += w
                elif i == j:
                    self.p_draw += w
                else:
                    self.p_away += w
                self.margin[i - j] = self.margin.get(i - j, 0.0) + w
                self.total[i + j] = self.total.get(i + j, 0.0) + w
        if settle_ties:
            # Ice hockey and baseball settle a level score in overtime / extra
            # innings, so half the tie mass is a home win and half an away win.
            # It is parked on +/-0.5 sentinels, which keeps every deeper
            # handicap threshold arithmetically exact.
            tie = self.margin.pop(0, 0.0)
            self.margin[0.5] = self.margin.get(0.5, 0.0) + tie / 2.0
            self.margin[-0.5] = self.margin.get(-0.5, 0.0) + tie / 2.0
            self.p_home += tie / 2.0
            self.p_away += tie / 2.0
            self.p_draw = 0.0
        self.lam_home, self.lam_away = lam_home, lam_away

    def p_margin_gt(self, line):
        return sum(w for m, w in self.margin.items() if m > line)

    def p_total_gt(self, line):
        return sum(w for t, w in self.total.items() if t > line)

    def p_total_expected(self):
        return self.lam_home + self.lam_away


class NormalMargin:
    """Normal margin + normal total (basketball, rugby union)."""

    def __init__(self, mu_margin, sd_margin, mu_total, sd_total, draw_band=0.0):
        self.mu, self.sd = mu_margin, sd_margin
        self.mut, self.sdt = mu_total, sd_total
        self.band = draw_band
        self.p_home = 1.0 - phi((self.band - self.mu) / self.sd)
        if self.band > 0:
            self.p_draw = phi((self.band - self.mu) / self.sd) - phi((-self.band - self.mu) / self.sd)
            self.p_away = phi((-self.band - self.mu) / self.sd)
        else:
            self.p_draw = 0.0
            self.p_away = phi(-self.mu / self.sd)

    def p_margin_gt(self, line):
        return 1.0 - phi((line - self.mu) / self.sd)

    def p_total_gt(self, line):
        return 1.0 - phi((line - self.mut) / self.sdt)

    def p_total_expected(self):
        return self.mut


class SnookerBo7:
    """Exact best-of-seven frame distribution from a per-frame win probability."""

    def __init__(self, q):
        self.q = q
        self.p_home = self.p_away = 0.0
        self.p_draw = 0.0
        self.margin = {}
        self.total = {}
        for k in range(4):
            c = math.comb(3 + k, k)
            w1 = c * (q ** 4) * ((1 - q) ** k)
            w2 = c * ((1 - q) ** 4) * (q ** k)
            self.p_home += w1
            self.p_away += w2
            self.margin[4 - k] = self.margin.get(4 - k, 0.0) + w1
            self.margin[k - 4] = self.margin.get(k - 4, 0.0) + w2
            self.total[4 + k] = self.total.get(4 + k, 0.0) + w1 + w2

    def p_margin_gt(self, line):
        return sum(w for m, w in self.margin.items() if m > line)

    def p_total_gt(self, line):
        return sum(w for t, w in self.total.items() if t > line)

    def p_total_expected(self):
        return sum(t * w for t, w in self.total.items())

    def expected_frames(self):
        """Expected frames won by player one and by player two."""
        one = two = 0.0
        for k in range(4):
            c = math.comb(3 + k, k)
            one += c * (self.q ** 4) * ((1 - self.q) ** k) * 4 + c * ((1 - self.q) ** 4) * (self.q ** k) * k
            two += c * (self.q ** 4) * ((1 - self.q) ** k) * k + c * ((1 - self.q) ** 4) * (self.q ** k) * 4
        return one, two


# --------------------------------------------------------------------------- #
# Strength tables, built only from captured official numbers
# --------------------------------------------------------------------------- #
def rating(gp, gf, ga, league, prior):
    w = gp / (gp + prior)
    attack = 1.0 + w * ((gf / gp) / league - 1.0)
    defence = 1.0 + w * ((ga / gp) / league - 1.0)
    return w, attack, defence


def build_inputs():
    inputs = {}

    # --- NHL: 32-club official team summary ------------------------------- #
    summary = load("nhl_team_summary_2026-10-22.json")
    teams = summary["teams"]
    league = sum(t["gf"] for t in teams) / sum(t["gp"] for t in teams)
    rows = []
    for t in teams:
        w, atk, dfn = rating(t["gp"], t["gf"], t["ga"], league, 8.0)
        rows.append({"code": t["abbrev"], "team": t["team"], "gp": t["gp"], "w": t["w"],
                     "l": t["l"], "otl": t["otl"], "pts": t["pts"], "point_pct": t["pointPct"],
                     "gf": t["gf"], "ga": t["ga"], "gfpg": t["gfpg"], "gapg": t["gapg"],
                     "pp": t["pp"], "pk": t["pk"], "shrink": round(w, 4),
                     "attack": round(atk, 4), "defence": round(dfn, 4)})
    inputs["nhl"] = {
        "league_avg_goals_per_team_game": round(league, 4), "clubs": rows,
        "source_url": summary["source_url"], "source_name": summary["source_name"],
        "snapshot_note": summary["snapshot_note"], "prior": 8.0, "home": 1.05,
        "model": "multiplicative Poisson on goals for/against, shrinkage gp/(gp+8), home factor 1.05",
    }

    # --- EuroLeague: 20-club official standings --------------------------- #
    el = load("euroleague_round7_2026-10-22.json")
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
        "model": "attack/defence points model, shrinkage gp/(gp+6), +3.0 home points, normal margin sd 11.0",
    }

    # --- URC: 16-club official table -------------------------------------- #
    urc = load("urc_table_2026-10-22.json")
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
        "model": "attack/defence points model, shrinkage pl/(pl+6), +3.0 home points, normal margin sd 13.0, draw band +/-1 point (a draw needs level scores)",
    }

    # --- EHF Champions League: 24-club official group tables -------------- #
    ehf = load("ehf_standings_2026-10-22.json")
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
        "model": "attack/defence Poisson on goals, shrinkage gp/(gp+3), +/-0.4 home goals, full score grid",
        "consistency_check": "goals_for_total equals goals_against_total across the 24 clubs, as it must: %d v %d"
                             % (total_gf, total_ga),
    }

    # --- MLB: 30-club official standings sample --------------------------- #
    mlb = load("mlb_standings_sample_2026-10-22.json")
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
        "model": "attack/defence Poisson on runs, shrinkage gp/(gp+20), +0.25 home runs, ties split 50/50 for extra innings",
    }

    # --- F1: 23-driver official championship standings ------------------- #
    f1 = load("f1_calendar_2026-10-22.json")
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
        "model": "share-of-championship-points outright; head-to-head between the top two by points share",
    }

    # --- Snooker: event form read first-hand ------------------------------ #
    wst = load("wst_ni_open_2026-10-22.json")
    form = {}
    frames = matches = 0
    for res in wst["completed_results_first_hand"]:
        matches += 1
        frames += res["s1"] + res["s2"]
        for player, won, lost in ((res["p1"], res["s1"], res["s2"]), (res["p2"], res["s2"], res["s1"])):
            e = form.setdefault(player, {"matches": 0, "frames_won": 0, "frames_lost": 0, "lines": []})
            e["matches"] += 1
            e["frames_won"] += won
            e["frames_lost"] += lost
            e["lines"].append("%s %d-%d %s (%s, %s)" % (res["p1"], res["s1"], res["s2"],
                                                        res["p2"], res["round"], res["day"]))
    for e in form.values():
        e["frame_rate"] = round(e["frames_won"] / (e["frames_won"] + e["frames_lost"]), 4)
        e["shrink"] = round(e["matches"] / (e["matches"] + 6.0), 4)
    inputs["wst"] = {
        "event": wst["event"], "round": wst["round"], "form": form,
        "matches_observed": matches, "frames_observed": frames,
        "frames_per_match": round(frames / matches, 4),
        "source_url": wst["source_url"], "source_name": wst["source_name"],
        "time_note": wst["time_note"], "prior": 6.0,
        "model": "exact best-of-seven frame distribution; per-frame win rate from captured frames, shrunk matches/(matches+6) toward 0.5",
    }
    return inputs


# --------------------------------------------------------------------------- #
# Per-fixture origination
# --------------------------------------------------------------------------- #
def dist_for(match, inputs):
    """Return (distribution, market config) or None when no official input exists."""
    sport = match["sport"]
    i = match["inputs"]

    if sport == "ice-hockey":
        tbl = {c["code"]: c for c in inputs["nhl"]["clubs"]}
        cfg = inputs["nhl"]
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
        ws = load("mlb_world_series_2026-10-22.json")
        cap_ids = {g["home"]["id"]: g["home"]["name"] for g in ws["games"]}
        cap_ids.update({g["away"]["id"]: g["away"]["name"] for g in ws["games"]})
        home_id = next(k for k, v in cap_ids.items() if v == match["home"]["name"])
        away_id = next(k for k, v in cap_ids.items() if v == match["away"]["name"])
        h, a = tbl[home_id], tbl[away_id]
        lam = cfg["league_avg_runs_per_team_game"]
        exp_h = lam * h["attack"] * a["defence"] + cfg["home"]
        exp_a = lam * a["attack"] * h["defence"] - cfg["home"]
        return PoissonGrid(exp_h, exp_a, 20, settle_ties=True), {
            "family": "mlb", "tie": "split", "hc_natural": 1.5, "hc_radius": 1.5,
            "total_radius": 2.0, "expected_h": exp_h, "expected_a": exp_a,
            "ratings": {"home": h, "away": a}, "league_avg": lam}

    if sport == "snooker":
        cfg = inputs["wst"]
        f1_, f2_ = cfg["form"].get(match["home"]["name"]), cfg["form"].get(match["away"]["name"])
        if not f1_ or not f2_:
            return None, {"family": "wst", "blank_reason":
                          "Neither player appears in the %d Round 1/Round 2 results read from wst.tv, so this "
                          "layer holds no first-hand strength input for either side of the fixture."
                          % cfg["matches_observed"]}
        d1 = f1_["shrink"] * (f1_["frame_rate"] - 0.5)
        d2 = f2_["shrink"] * (f2_["frame_rate"] - 0.5)
        q = min(0.95, max(0.05, 0.5 + d1 - d2))
        dist = SnookerBo7(q)
        return dist, {
            "family": "wst", "tie": "none", "hc_natural": None, "hc_radius": 1.5,
            "total_radius": 1.0, "expected_h": dist.expected_frames()[0],
            "expected_a": dist.expected_frames()[1],
            "frame_q": round(q, 4), "ratings": {"home": f1_, "away": f2_},
            "frames_per_match": cfg["frames_per_match"]}

    return None, {"blank_reason": "No official strength input captured for this sport."}


VENUE_CAVEATS = {
    "euroleague-r7-62": ("The official game centre lists ALEKSANDAR NIKOLIC HALL as the venue for Maccabi Rapyd "
                         "Tel Aviv's home fixture. The feed does not state whether that is a neutral site, and this "
                         "layer applies its uniform +3.0 home-point advantage regardless, so the home advantage in "
                         "this row may be overstated. Disclosed, not adjusted."),
    "euroleague-r7-66": ("The official game centre lists BELGRADE ARENA for Partizan Mozzart Bet Belgrade's home "
                         "fixture against Crvena Zvezda Meridianbet Belgrade, a same-city derby. A shared-city derby "
                         "dilutes home advantage; the uniform +3.0 is still applied and disclosed."),
}


NHL_RECORD_CAVEAT = ("W-L-OTL records beside these fixtures are a 2026-10-21 snapshot: the official feed had not "
                     "absorbed the twelve games played on 2026-10-22 when it was read. Published exactly as returned "
                     "and disclosed as flag CU-01 rather than adjusted.")


def markets_for(match, dist, cfg):
    """Originate every market and every side; return the market list + band search."""
    markets = []
    p_home, p_draw, p_away = dist.p_home, dist.p_draw, dist.p_away
    outcomes = [{"name": match["home"]["name"], "side": "home", "p": p_home}]
    if p_draw > 0:
        outcomes.append({"name": "Draw", "side": "draw", "p": p_draw})
    outcomes.append({"name": match["away"]["name"], "side": "away", "p": p_away})
    total_p = sum(o["p"] for o in outcomes)
    for o in outcomes:
        o["p"] = o["p"] / total_p
        o.update(price(o["p"]))
        o["in_band"] = in_band(o["p"])
        o["confidence"] = label(o["p"], o["in_band"])
        o.pop("american_exact", None)
    markets.append({"market": "match winner", "line": "", "outcomes": outcomes})

    mu = cfg["expected_h"] - cfg["expected_a"]
    nat = cfg.get("hc_natural")
    if nat:
        # T is the threshold on the home margin; the home side is posted at -T,
        # so a home favourite carries T = +nat (the standard puck / run line).
        nat_line = nat if mu >= 0 else -nat
    else:
        nat_line = half(mu)
    steps = int(round(cfg["hc_radius"]))
    hc = []
    for k in range(-steps, steps + 1):
        line = round(nat_line + 1.0 * k, 1)
        if cfg.get("tie") == "split" and abs(line) < 1.0:
            continue   # +/-0.5 restates the moneyline once overtime settles ties
        p_cover = dist.p_margin_gt(line)
        if p_cover <= 0.0005 or p_cover >= 0.9995:
            continue
        for side, p, who, posted in (("home", p_cover, match["home"]["name"], -line),
                                     ("away", 1.0 - p_cover, match["away"]["name"], line)):
            entry = {"side": side, "selection": "%s %+.1f" % (who, posted),
                     "line": line, "posted": posted, "p": p}
            entry.update(price(p))
            entry["in_band"] = in_band(entry["p"])
            entry["confidence"] = label(entry["p"], entry["in_band"])
            entry.pop("american_exact", None)
            hc.append(entry)
    markets.append({"market": "handicap", "line": nat_line, "outcomes": hc})

    mu_t = cfg["expected_h"] + cfg["expected_a"]
    nat_t = half(mu_t)
    steps = int(round(cfg["total_radius"]))
    tot = []
    for k in range(-steps, steps + 1):
        line = round(nat_t + 1.0 * k, 1)
        p_over = dist.p_total_gt(line)
        if p_over <= 0.0005 or p_over >= 0.9995:
            continue
        for side, p in (("over", p_over), ("under", 1.0 - p_over)):
            entry = {"side": side, "selection": "%s %.1f" % (side.title(), line), "line": line, "p": p}
            entry.update(price(p))
            entry["in_band"] = in_band(entry["p"])
            entry["confidence"] = label(entry["p"], entry["in_band"])
            entry.pop("american_exact", None)
            tot.append(entry)
    markets.append({"market": "match total", "line": nat_t, "outcomes": tot})
    return markets, mu, mu_t


def best_band(markets, mu, mu_t):
    """The most natural in-band selection, searched across every market and side.

    Ranking (then closest to the model's own number, then highest probability):
      0  the moneyline itself
      1  a handicap line backing the model's favourite
      2  a total (over/under) line
      3  a handicap line backing the model's underdog
    Ranking 3 last matters: a heavy receiving handicap on a side the model does
    not favour is arithmetically in band but says almost nothing, so it is only
    published when the fixture offers no better in-band expression.
    """
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
    return pick, [{"market": c["market"], "selection": c["selection"],
                   "p": round(c["p"], 4),
                   "fair_decimal": price(c["p"])["fair_decimal"],
                   "fair_american": price(c["p"])["fair_american"], "rank": c["rank"]}
                  for c in cands]



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
    top2 = cfg["drivers"][:2]
    a, b = top2[0], top2[1]
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
    cands = [{"market": m["market"], "selection": o["selection"], "p": o["p"],
              "fair_decimal": o["fair_decimal"], "fair_american": o["fair_american"]}
             for m in markets for o in m["outcomes"] if o["in_band"]]
    if cands:
        cands.sort(key=lambda c: -c["p"])
        band = dict(cands[0], market=cands[0]["market"], confidence="high")
    return markets, {"expected_h": best["p"], "expected_a": 0.0}, band, cands, best


def main():
    with open(os.path.join(DATA, "matches.json"), encoding="utf-8") as handle:
        seeded = json.load(handle)
    inputs = build_inputs()
    matches = seeded["matches"]

    rows, band_picks, blanks = [], [], []
    for m in matches:
        if m["kind"] == "event":
            markets, mu, band, cands, best = originate_f1(m, inputs)
            primary = {"market": "race winner (outright)", "selection": best["selection"],
                       "p": best["p"], "fair_decimal": best["fair_decimal"],
                       "fair_american": best["fair_american"], "confidence": best["confidence"],
                       "note": "Share-of-championship-points outright. Crude by design and labelled low/medium; "
                               "no per-circuit model is claimed."}
            rows.append({"match_id": m["id"], "sport": m["sport"], "originated": True,
                         "primary": primary, "markets": markets, "band_pick": band,
                         "band_candidates": cands, "blank_reason": "", "model": inputs["f1"]["model"]})
            if band:
                band_picks.append({"match_id": m["id"], "sport": m["sport"],
                                   "sport_name": m["sport_name"], "date": m["date"],
                                   "fixture": m["event"], "official_url": m["official_url"],
                                   "capture_file": m["capture_file"], **band})
            continue

        dist, cfg = dist_for(m, inputs)
        if dist is None:
            reason = cfg["blank_reason"]
            blanks.append({"match_id": m["id"], "sport": m["sport"], "sport_name": m["sport_name"],
                           "date": m["date"],
                           "fixture": "%s v %s" % (m["home"]["name"], m["away"]["name"]),
                           "reason": reason, "official_url": m["official_url"],
                           "capture_file": m["capture_file"], "flag": "CU-07"})
            rows.append({"match_id": m["id"], "sport": m["sport"], "originated": False,
                         "primary": None, "markets": [], "band_pick": None,
                         "band_candidates": [], "blank_reason": reason, "model": ""})
            continue

        markets, mu, mu_t = markets_for(m, dist, cfg)
        band, cands = best_band(markets, mu, mu_t)
        mw = markets[0]["outcomes"]
        two_way = [o for o in mw if o["side"] in ("home", "away")]
        best = max(mw, key=lambda o: o["p"])
        if band:
            primary = {"market": band["market"], "selection": band["selection"], "p": band["p"],
                       "fair_decimal": band["fair_decimal"], "fair_american": band["fair_american"],
                       "confidence": "high", "note": "In-band selection found by searching every originated market."}
        else:
            level = abs(mw[0]["p"] - mw[-1]["p"]) < 0.0005
            primary = {"market": "match winner", "selection": best["name"], "p": best["p"],
                       "fair_decimal": best["fair_decimal"], "fair_american": best["fair_american"],
                       "confidence": best["confidence"],
                       "level": level,
                       "note": (("The captured inputs rate both sides identically, so this is a true coin flip: "
                                  "the published selection follows the official listing order and carries "
                                  "no model edge. " if level else "")
                                + "No originated market on either side reaches probability 0.70 inside the "
                                "-250 to +10000 fair-price band, so the strongest two-way opinion is "
                                "published instead and capped at %s." % best["confidence"])}
        rows.append({
            "match_id": m["id"], "sport": m["sport"], "originated": True,
            "primary": primary, "markets": markets, "band_pick": band,
            "band_candidates": cands, "blank_reason": "",
            "model": cfg["family"], "expected_home": round(cfg["expected_h"], 3),
            "expected_away": round(cfg["expected_a"], 3),
            "expected_margin": round(mu, 3), "expected_total": round(mu_t, 3),
            "league_avg": round(cfg.get("league_avg", 0.0), 4),
            "caveat": VENUE_CAVEATS.get(m["id"], "") or (
                NHL_RECORD_CAVEAT if m["sport"] == "ice-hockey" else ""),
        })
        if band:
            band_picks.append({
                "match_id": m["id"], "sport": m["sport"], "sport_name": m["sport_name"],
                "date": m["date"], "home": m["home"]["name"], "away": m["away"]["name"],
                "fixture": "%s v %s" % (m["home"]["name"], m["away"]["name"]),
                "competition": m["competition"], "venue": m["venue"],
                "time_note": m["time_note"], "official_url": m["official_url"],
                "capture_file": m["capture_file"], "source_name": m["source_name"],
                "expected_margin": round(mu, 3), "expected_total": round(mu_t, 3),
                "caveat": VENUE_CAVEATS.get(m["id"], "") or (
                    NHL_RECORD_CAVEAT if m["sport"] == "ice-hockey" else ""),
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

    write("model_inputs.json", {"generated_by": "scripts/current_model.py", "inputs": inputs})
    write("lines.json", {"generated_by": "scripts/current_model.py", "counts": counts,
                         "gate": {"min_probability": BAND_MIN_P,
                                  "max_fair_american": BAND_MAX_PRICE,
                                  "min_fair_american": -250,
                                  "note": "p >= 0.70 AND fair no-vig American price inside -250 ... +10000, "
                                          "searched across every originated market and both sides."},
                         "rows": rows})
    write("band.json", {"generated_by": "scripts/current_model.py", "counts": counts,
                        "selections": band_picks})
    write("blanks.json", {"generated_by": "scripts/current_model.py", "rows": blanks})

    print("current_model OK:", json.dumps(counts))
    for p in band_picks[:80]:
        print("   BAND %-13s %-44s | %-32s p=%.4f dec=%.2f am=%+d" % (
            p["sport"], p["fixture"][:44], p["selection"][:32], p["p"], p["fair_decimal"], p["fair_american"]))


if __name__ == "__main__":
    main()
