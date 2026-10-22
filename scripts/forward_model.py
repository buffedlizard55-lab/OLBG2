#!/usr/bin/env python3
"""Forward-window line origination and prediction builder (2026-10-23 .. 2026-11-02).

Reads the self-contained capture in data/forward/inputs.json (written by
scripts/forward_seed.py) and writes:
  - data/forward/matches.json     (fixture + originated markets + picks)
  - data/forward/predictions.json (>=30-word written predictions for picks that
                                   clear the uniform high-confidence gate)
  - data/forward/flagged.json     (forward-window gap and status flags)

Methodology is deliberately identical to the /verified desk so the two layers
stay splice-compatible: shrunk Poisson goal models for ice hockey and baseball,
no bookmaker odds or tipster percentages anywhere, and the uniform
high-confidence gate from the live coordination board —

    high  <=>  model probability >= 0.70  AND  fair American in [-250, +10000]

so a "high" pick is always a >70% shot whose fair price is no shorter than
-250. Featured selections additionally scan handicap/total and alternate lines
originated from the same score distribution so a chalky moneyline can be
repriced inside the band instead of being discarded.
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FWD = ROOT / "data" / "forward"

HIGH_THRESHOLD = 0.72
MEDIUM_THRESHOLD = 0.60
FEATURED_MIN_PROB = 0.70
AMERICAN_MIN = -250
AMERICAN_MAX = 10000
MIN_WORDS = 30

NHL_OLBG = "https://www.olbg.com/betting-tips/Ice_Hockey/13"
MLB_OLBG = "https://www.olbg.com/betting-tips/Baseball/12"
BASKET_OLBG = "https://www.olbg.com/betting-tips/Basketball/19"

# Bespoke written predictions, keyed by match id, for every featured selection.
# Each entry is factual (official capture figures only), >= 30 words, names the
# selection, a player, current form and recent match history, and is written by
# hand — the {selection}/{prob_pct}/{price}/{american} slots only restate the
# model's own numbers, never outside information.
NARRATIVES: dict[str, dict] = {
    "nhl-2026020170": {
        "headline": "Boston's 2.20 goals-against wall hosts a Celebrini side shipping 3.40 per night",
        "template": (
            "Take {selection} when the Sharks visit TD Garden on Saturday night. "
            "Boston have opened 2026-27 at 7-2-1 with 36 scored and only 22 conceded across ten games, "
            "and David Pastrnak paces the club with four goals and eight assists in front of Jeremy Swayman's six wins. "
            "San Jose sit 5-4-1 having leaked 34 goals in ten, their bright spot Macklin Celebrini (five goals, nine assists), "
            "and this matchup prices the Bruins at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Boston Bruins stand 7-2-1 with 36 GF and 22 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "San Jose Sharks stand 5-4-1 with 26 GF and 34 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "David Pastrnak leads Boston with 4 goals and 8 assists; Jeremy Swayman has 6 wins; Macklin Celebrini leads San Jose with 5 goals and 9 assists", "source": "https://www.nhl.com/gamecenter/sjs-vs-bos/2026/10/24/2026020170"},
        ],
    },
    "nhl-2026020195": {
        "headline": "Kaprizov's 11-goal Wild carry a two-goal cushion into Delta Center",
        "template": (
            "Back {selection} at Delta Center on Tuesday evening instead of touching the near-even moneyline. "
            "Minnesota arrive 6-2-2 with 31 goals scored and 25 allowed over ten games, Kirill Kaprizov leading the club with eleven goals "
            "and Quinn Hughes quarterbacking with eleven assists, while Jesper Wallstedt has six wins in net. "
            "Utah's 7-3-0 start is real (38 scored), but two of the Wild's ten games have needed extra time (two overtime losses) and the +1.5 cushion grades at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Minnesota Wild stand 6-2-2 with 31 GF and 25 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Utah Mammoth stand 7-3-0 with 38 GF and 31 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Kirill Kaprizov leads Minnesota with 11 goals; Quinn Hughes has 11 assists; Jesper Wallstedt has 6 wins; Nick Schmaltz leads Utah with 7 goals", "source": "https://www.nhl.com/gamecenter/min-vs-uta/2026/10/27/2026020195"},
        ],
    },
    "nhl-2026020198": {
        "headline": "Evenly matched Sabres and Sharks split by the half-goal line in San Jose",
        "template": (
            "Take {selection} at SAP Center on Tuesday night in a game the model can barely separate. "
            "Buffalo's 4-4-2 start (28 scored, 36 conceded) and San Jose's 5-4-1 (26 scored, 34 conceded) both profile as mid-table form, "
            "with Tage Thompson's five goals and Zach Benson's six assists carrying the Sabres while Macklin Celebrini leads the Sharks with five goals and nine assists. "
            "Neither side has found a consistent run — Buffalo sit at .500 through ten games (4-4-2) — so the half-goal cushion prices at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Buffalo Sabres stand 4-4-2 with 28 GF and 36 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "San Jose Sharks stand 5-4-1 with 26 GF and 34 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Tage Thompson leads Buffalo with 5 goals; Zach Benson has 6 assists; Macklin Celebrini leads San Jose with 5 goals and 9 assists", "source": "https://www.nhl.com/gamecenter/buf-vs-sjs/2026/10/27/2026020198"},
        ],
    },
    "nhl-2026020202": {
        "headline": "Matthews' Leafs land in Seattle with the safest angle on the night's 7.09-goal projection",
        "template": (
            "Back {selection} at Climate Pledge Arena on Wednesday night in one of the slate's higher-projected games (7.09 combined goals). "
            "Toronto's 5-4-2 start has been all-event hockey — 38 scored and 34 conceded in eleven games — with Auston Matthews leading the club in both goals (eight) and assists (ten). "
            "Seattle counter through Chandler Stephenson's eight assists and Frederick Gaudreau's five goals on a 6-3-1 record, "
            "and with the model projecting 7.09 combined goals the Leafs' half-goal cushion grades at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Toronto Maple Leafs stand 5-4-2 with 38 GF and 34 GA through eleven games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Seattle Kraken stand 6-3-1 with 37 GF and 34 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Auston Matthews leads Toronto with 8 goals and 10 assists; Frederick Gaudreau leads Seattle with 5 goals; Chandler Stephenson has 8 assists", "source": "https://www.nhl.com/gamecenter/tor-vs-sea/2026/10/28/2026020202"},
        ],
    },
    "nhl-2026020208": {
        "headline": "Overtime-soaked Predators host a Capitals side that rarely loses big",
        "template": (
            "Take {selection} at Bridgestone Arena on Thursday night. "
            "Washington's 5-4-0 start has been tight — 30 scored and 29 conceded in nine games, Alex Tuch's five goals and Dylan Strome's five assists leading the way — "
            "and Nashville have gone to extra time in three of eight contests (3-2-3, 23 scored, 22 conceded) behind Roman Josi's eight assists and Juuse Saros. "
            "Games between these profiles almost always land within a goal, making the Capitals +1.5 the sharp side at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Washington Capitals stand 5-4-0 with 30 GF and 29 GA through nine games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Nashville Predators stand 3-2-3 with 23 GF and 22 GA through eight games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Alex Tuch leads Washington with 5 goals; Roman Josi leads Nashville with 8 assists; Juuse Saros has 3 wins", "source": "https://www.nhl.com/gamecenter/wsh-vs-nsh/2026/10/29/2026020208"},
        ],
    },
    "nhl-2026020217": {
        "headline": "Swayman's Bruins get the win-or-share line against a Chicago defence allowing 4.00 per night",
        "template": (
            "Back {selection} at TD Garden on Saturday afternoon — the in-band way to side with a Bruins team whose moneyline has drifted shorter than the -250 floor. "
            "Boston's 7-2-1 record is built on 36 goals scored and just 22 conceded, with David Pastrnak contributing four goals and eight assists and Jeremy Swayman backstopping six wins. "
            "Chicago arrive 3-6-0 having conceded 36 in nine games (4.00 per night) despite rookie Anton Frondell's five assists, "
            "and the model's margin distribution gives Boston at least a share of regulation in {prob_pct}% of simulations ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Boston Bruins stand 7-2-1 with 36 GF and 22 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Chicago Blackhawks stand 3-6-0 with 21 GF and 36 GA through nine games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "David Pastrnak leads Boston with 4 goals and 8 assists; Jeremy Swayman has 6 wins; Anton Frondell has 5 assists for Chicago", "source": "https://www.nhl.com/gamecenter/chi-vs-bos/2026/10/31/2026020217"},
        ],
    },
    "nhl-2026020223": {
        "headline": "Karlsson's Penguins take the half-goal cushion into a Bell Centre shootout",
        "template": (
            "Take {selection} at the Bell Centre on Saturday night between two sides that trade in chaos. "
            "Pittsburgh's 3-6-1 start has produced 32 goals scored and 37 conceded in ten games — Evgeni Malkin has five goals and Erik Karlsson ten assists — "
            "while Montreal are 4-3-2 on the back of Cole Caufield's six goals and Nick Suzuki's seven assists. "
            "Neither defence has settled, so the Penguins losing by anything more than a goal is the outlier: +1.5 grades at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Pittsburgh Penguins stand 3-6-1 with 32 GF and 37 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Montreal Canadiens stand 4-3-2 with 28 GF and 34 GA through nine games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Erik Karlsson has 10 assists for Pittsburgh; Cole Caufield leads Montreal with 6 goals; Nick Suzuki has 7 assists", "source": "https://www.nhl.com/gamecenter/pit-vs-mtl/2026/10/31/2026020223"},
        ],
    },
    "nhl-2026020234": {
        "headline": "MacKinnon's 41-goal Avalanche offence lands on the United Center",
        "template": (
            "Back {selection} at the United Center on Monday night. "
            "Colorado's attack is averaging 4.10 goals per game — 41 in ten contests — with Artturi Lehkonen's eight goals and Nathan MacKinnon's ten assists driving a 5-4-1 record, "
            "and Mackenzie Blackwood has four wins behind them. "
            "Chicago are 3-6-0 with 36 conceded and only 21 scored, leaning on rookie Anton Frondell's five assists, "
            "and the model likes the visitors at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Colorado Avalanche stand 5-4-1 with 41 GF and 30 GA through ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Chicago Blackhawks stand 3-6-0 with 21 GF and 36 GA through nine games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Artturi Lehkonen leads Colorado with 8 goals; Nathan MacKinnon has 10 assists; Anton Frondell has 5 assists for Chicago", "source": "https://www.nhl.com/gamecenter/col-vs-chi/2026/11/02/2026020234"},
        ],
    },
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write via a temp sibling + os.replace: some overlay filesystems
    # otherwise leave a stale directory entry behind for this file name.
    tmp = path.parent / (path.name + ".tmpwrite")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def fair_decimal(prob: float) -> float:
    return round(max(1.02, 1.0 / max(prob, 1e-6)), 2)


def fair_american(prob: float) -> int:
    dec = 1.0 / min(max(prob, 1e-6), 1.0 - 1e-9)
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100))
    return int(round(-100.0 / (dec - 1.0)))


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def half_line(raw: float) -> float:
    return math.floor(raw) + 0.5


def poisson_grid(lh: float, la: float) -> dict[tuple[int, int], float]:
    max_k = max(35, int(math.ceil(max(lh, la) + 7.5 * math.sqrt(max(lh, la, 1.0)))))
    ph = [math.exp(-lh) * (lh**k) / math.factorial(k) for k in range(max_k + 1)]
    pa = [math.exp(-la) * (la**k) / math.factorial(k) for k in range(max_k + 1)]
    grid: dict[tuple[int, int], float] = {}
    total_mass = 0.0
    for i in range(max_k + 1):
        for j in range(max_k + 1):
            p = ph[i] * pa[j]
            grid[(i, j)] = p
            total_mass += p
    return {k: v / total_mass for k, v in grid.items()}


def _grid_margin_total_probs(grid: dict) -> tuple[dict, dict]:
    margin_probs: dict[int, float] = {}
    total_probs: dict[int, float] = {}
    for (i, j), p in grid.items():
        margin_probs[i - j] = margin_probs.get(i - j, 0.0) + p
        total_probs[i + j] = total_probs.get(i + j, 0.0) + p
    return margin_probs, total_probs


def grade(prob: float, cap: str | None = None) -> str:
    raw = "high" if prob >= HIGH_THRESHOLD else ("medium" if prob >= MEDIUM_THRESHOLD else "low")
    order = ["low", "medium", "high"]
    if cap and order.index(raw) > order.index(cap):
        return cap
    return raw


def _in_band(prob: float) -> bool:
    return prob >= FEATURED_MIN_PROB and AMERICAN_MIN <= fair_american(prob) <= AMERICAN_MAX


def _best_alt_line(prob_gt, lo: float, hi: float) -> tuple[float, float] | None:
    """Half-point alternate line whose P(value > line) lands nearest band middle."""
    best: tuple[float, float] | None = None
    x = math.floor(lo) + 0.5
    while x <= hi:
        p = prob_gt(x)
        if _in_band(p) and (best is None or abs(p - 0.7071) < abs(best[1] - 0.7071)):
            best = (x, p)
        x += 1.0
    return best


def _fmt_line(v: float) -> str:
    s = f"{v:+.2f}".rstrip("0").rstrip(".")
    return s if s not in {"+", "-"} else f"{v:+.1f}"


def _alternate_candidates(row: dict) -> list[dict]:
    dist = row.get("_dist")
    if not dist or "margin_probs" not in dist:
        return []
    home, away, unit = row["home"], row["away"], dist.get("unit", "goals")
    mp = {int(k): v for k, v in dist["margin_probs"].items()}
    tp = {int(k): v for k, v in dist["total_probs"].items()}
    neg = {-k: v for k, v in mp.items()}
    out: list[dict] = []

    def add_handicaps(prob_gt_home, prob_gt_away, lo, hi):
        alt = _best_alt_line(prob_gt_home, lo, hi)
        if alt:
            line, p = alt
            out.append({"selection": f"{home} {_fmt_line(-line)} (Alternate Handicap)", "market": "Alternate Handicap", "probability": round(p, 4)})
        alt = _best_alt_line(prob_gt_away, lo, hi)
        if alt:
            line, p = alt
            out.append({"selection": f"{away} {_fmt_line(-line)} (Alternate Handicap)", "market": "Alternate Handicap", "probability": round(p, 4)})

    def add_totals(prob_gt_total, lo, hi):
        alt = _best_alt_line(prob_gt_total, lo, hi)
        if alt:
            line, p = alt
            out.append({"selection": f"Over {line:.1f} {unit} (Alternate Total)", "market": "Alternate Total", "probability": round(p, 4)})
        alt = _best_alt_line(lambda x: 1.0 - prob_gt_total(x), lo, hi)
        if alt:
            line, p = alt
            out.append({"selection": f"Under {line:.1f} {unit} (Alternate Total)", "market": "Alternate Total", "probability": round(p, 4)})

    add_handicaps(
        lambda x: sum(p for v, p in mp.items() if v > x),
        lambda x: sum(p for v, p in neg.items() if v > x),
        min(mp),
        max(mp),
    )
    add_totals(lambda x: sum(p for v, p in tp.items() if v > x), min(tp), max(tp))
    return out


def featured_selection(row: dict) -> dict | None:
    """Strongest in-band selection across moneyline, handicap, totals and
    alternates repriced from the originator's own score distribution."""
    candidates: list[dict] = [
        {"selection": row["pick"]["selection"], "market": "Match Winner", "probability": row["pick"]["probability"]}
    ]
    hm = row.get("handicap_market")
    if hm:
        label = hm["label"]
        if " / " in label:
            fav_label, dog_label = label.split(" / ", 1)
            candidates.append({"selection": f"{fav_label} (Handicap)", "market": "Handicap", "probability": hm["fav_prob"]})
            candidates.append({"selection": f"{dog_label} (Handicap)", "market": "Handicap", "probability": hm["dog_prob"]})
        else:
            candidates.append({"selection": f"{label} (Handicap)", "market": "Handicap", "probability": hm["fav_prob"]})
    tm = row.get("total_market")
    if tm:
        candidates.append({"selection": f"Over {tm['line']} (Match Total)", "market": "Match Total", "probability": tm["over_prob"]})
        candidates.append({"selection": f"Under {tm['line']} (Match Total)", "market": "Match Total", "probability": tm["under_prob"]})
    pick_prob = row["pick"]["probability"]
    pick_team = row["pick"].get("team") or ""
    for cand in _alternate_candidates(row):
        if cand["market"] == "Alternate Handicap":
            if pick_prob >= FEATURED_MIN_PROB and pick_team and cand["selection"].startswith(pick_team):
                candidates.append(cand)
        elif cand["market"] == "Alternate Total" and tm:
            if cand["selection"].startswith("Over") and tm["over_prob"] >= MEDIUM_THRESHOLD:
                candidates.append(cand)
            elif cand["selection"].startswith("Under") and tm["under_prob"] >= MEDIUM_THRESHOLD:
                candidates.append(cand)
    in_band = [
        {
            **c,
            "fair_odds": fair_decimal(c["probability"]),
            "fair_american": fair_american(c["probability"]),
            "confidence": "high",
        }
        for c in candidates
        if _in_band(c["probability"])
    ]
    if not in_band:
        return None
    return max(in_band, key=lambda c: (c["market"] == "Match Winner", c["probability"]))


_BAND_MARKET_MAP = {
    "Match Winner": "moneyline",
    "Handicap": "handicap",
    "Alternate Handicap": "handicap",
    "Match Total": "total",
    "Alternate Total": "total",
}


def _band_pick(feat: dict) -> dict:
    m = re.search(r"([+-]?\d+\.\d+)", feat["selection"])
    return {
        "selection": feat["selection"],
        "market": _BAND_MARKET_MAP.get(feat["market"], feat["market"]),
        "line": float(m.group(1)) if m else None,
        "probability": feat["probability"],
        "fair_odds": feat["fair_odds"],
        "fair_american": feat["fair_american"],
        "confidence": "high",
        "price_band": "in-band",
    }


def originate_nhl(inputs: dict) -> list[dict]:
    teams = inputs["nhl_teams"]
    lg_gf = sum(t["gf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    rows: list[dict] = []
    for f in inputs["nhl_fixtures"]:
        h, a = teams[f["home"]], teams[f["away"]]
        k = 8.0
        att_h = ((h["gf"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        def_h = ((h["ga"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        att_a = ((a["gf"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        def_a = ((a["ga"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        lh = lg_gf * att_h * def_a * 1.05
        la = lg_gf * att_a * def_h
        grid = poisson_grid(lh, la)
        reg_h = sum(p for (i, j), p in grid.items() if i > j)
        reg_d = sum(p for (i, j), p in grid.items() if i == j)
        p_home = reg_h + 0.52 * reg_d
        p_away = 1.0 - p_home
        p_h_pl = sum(p for (i, j), p in grid.items() if i - j >= 2)
        p_a_pl = 1.0 - p_h_pl
        tot_line = 5.5 if (lh + la) < 6.0 else 6.5
        p_over = sum(p for (i, j), p in grid.items() if (i + j) > tot_line)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        margin_probs, total_probs = _grid_margin_total_probs(grid)
        rows.append(
            {
                "id": f"nhl-{f['id']}",
                "sport": "ice-hockey",
                "sport_name": "Ice Hockey",
                "competition": "NHL Regular Season 2026-27",
                "date": f["date"],
                "time": f["start_utc"],
                "home": h["name"],
                "away": a["name"],
                "venue": f["venue"],
                "line_status": "originated",
                "home_summary": f"{h['w']}-{h['l']}-{h['otl']} ({h['gf']} GF / {h['ga']} GA)",
                "away_summary": f"{a['w']}-{a['l']}-{a['otl']} ({a['gf']} GF / {a['ga']} GA)",
                "winner_market": {
                    "type": "2-way Moneyline",
                    "home_prob": round(p_home, 4),
                    "away_prob": round(p_away, 4),
                    "home_odds": fair_decimal(p_home),
                    "away_odds": fair_decimal(p_away),
                },
                "handicap_market": {
                    "line": -1.5,
                    "label": f"{h['name']} -1.5 / {a['name']} +1.5",
                    "fav_prob": round(p_h_pl, 4),
                    "dog_prob": round(p_a_pl, 4),
                    "fav_odds": fair_decimal(p_h_pl),
                    "dog_odds": fair_decimal(p_a_pl),
                },
                "total_market": {
                    "line": tot_line,
                    "projected": round(lh + la, 2),
                    "over_prob": round(p_over, 4),
                    "under_prob": round(1.0 - p_over, 4),
                    "over_odds": fair_decimal(p_over),
                    "under_odds": fair_decimal(1.0 - p_over),
                },
                "pick": {
                    "selection": f"{win_side} (Moneyline)",
                    "team": win_side,
                    "probability": round(win_prob, 4),
                    "fair_odds": fair_decimal(win_prob),
                    "confidence": grade(win_prob),
                    "fair_american": fair_american(win_prob),
                },
                "_dist": {"margin_probs": margin_probs, "total_probs": total_probs, "unit": "goals"},
                "official_source": "NHL GameCenter & Stats API",
                "official_url": f"https://www.nhl.com{f['gc']}",
                "data_url": "https://api.nhle.com/stats/rest/en/team/summary",
                "olbg_url": NHL_OLBG,
            }
        )
    return rows


def originate_mlb(inputs: dict) -> list[dict]:
    teams = inputs["mlb_teams"]
    tb, mil = teams["TB"], teams["MIL"]
    gp_total = (tb["wins"] + tb["losses"]) + (mil["wins"] + mil["losses"])
    rs_pg = (tb["runs_scored"] + mil["runs_scored"]) / gp_total
    ra_pg = (tb["runs_allowed"] + mil["runs_allowed"]) / gp_total
    lg = 0.5 * (rs_pg + ra_pg)
    rows: list[dict] = []
    for f in inputs["mlb_fixtures"]:
        is_home_brewers = f["home"] == "Milwaukee Brewers"
        h = mil if is_home_brewers else tb
        a = tb if is_home_brewers else mil
        gp_h = h["wins"] + h["losses"]
        gp_a = a["wins"] + a["losses"]
        lh = lg * ((h["runs_scored"] / gp_h) / lg) * ((a["runs_allowed"] / gp_a) / lg) * 1.04
        la = lg * ((a["runs_scored"] / gp_a) / lg) * ((h["runs_allowed"] / gp_h) / lg)
        grid = poisson_grid(lh, la)
        reg_h = sum(p for (i, j), p in grid.items() if i > j)
        reg_d = sum(p for (i, j), p in grid.items() if i == j)
        p_home = reg_h + 0.51 * reg_d
        p_away = 1.0 - p_home
        fav_is_home = p_home >= p_away
        fav_name = h["name"] if fav_is_home else a["name"]
        dog_name = a["name"] if fav_is_home else h["name"]
        win_prob = max(p_home, p_away)
        if fav_is_home:
            p_rl = sum(p for (i, j), p in grid.items() if i - j >= 2)
        else:
            p_rl = sum(p for (i, j), p in grid.items() if j - i >= 2)
        p_over = sum(p for (i, j), p in grid.items() if (i + j) > 7.5)
        margin_probs, total_probs = _grid_margin_total_probs(grid)
        game_no = f["description"].replace("World Series Game ", "")
        comp = f"2026 MLB World Series — Game {game_no}"
        if f.get("if_necessary") == "Y":
            comp += " (if necessary)"
        rows.append(
            {
                "id": f["id"].replace("mlb-ws-", "mlb-ws-"),
                "sport": "baseball",
                "sport_name": "Baseball",
                "competition": comp,
                "date": f["date"],
                "time": f["game_date_utc"],
                "home": h["name"],
                "away": a["name"],
                "venue": f["venue"],
                "line_status": "originated",
                "home_summary": f"{h['wins']}-{h['losses']} ({h['runs_scored']} RS / {h['runs_allowed']} RA)",
                "away_summary": f"{a['wins']}-{a['losses']} ({a['runs_scored']} RS / {a['runs_allowed']} RA)",
                "winner_market": {
                    "type": "2-way Moneyline",
                    "home_prob": round(p_home, 4),
                    "away_prob": round(p_away, 4),
                    "home_odds": fair_decimal(p_home),
                    "away_odds": fair_decimal(p_away),
                },
                "handicap_market": {
                    "line": -1.5,
                    "label": f"{fav_name} -1.5 / {dog_name} +1.5",
                    "fav_prob": round(p_rl, 4),
                    "dog_prob": round(1.0 - p_rl, 4),
                    "fav_odds": fair_decimal(p_rl),
                    "dog_odds": fair_decimal(1.0 - p_rl),
                },
                "total_market": {
                    "line": 7.5,
                    "projected": round(lh + la, 2),
                    "over_prob": round(p_over, 4),
                    "under_prob": round(1.0 - p_over, 4),
                    "over_odds": fair_decimal(p_over),
                    "under_odds": fair_decimal(1.0 - p_over),
                },
                "pick": {
                    "selection": f"{fav_name} (Moneyline)",
                    "team": fav_name,
                    "probability": round(win_prob, 4),
                    "fair_odds": fair_decimal(win_prob),
                    "confidence": grade(win_prob),
                    "fair_american": fair_american(win_prob),
                },
                "_dist": {"margin_probs": margin_probs, "total_probs": total_probs, "unit": "runs"},
                "official_source": "MLB Stats API Official",
                "official_url": f["human_url"],
                "data_url": "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026",
                "olbg_url": MLB_OLBG,
            }
        )
    return rows


def eurocup_unlined(inputs: dict) -> list[dict]:
    blank = (
        "Official EuroCup standings and form tables return empty bodies on both the v1 and v2 "
        "api-live.euroleague.net standings endpoints as of 2026-10-22, and this desk never infers "
        "team strength from results it has not captured; the Round 5 card is recorded in full and "
        "every market is intentionally left blank."
    )
    rows: list[dict] = []
    for f in inputs["eurocup_r5"]:
        rows.append(
            {
                "id": f["game"],
                "sport": "basketball",
                "sport_name": "Basketball",
                "competition": f"EuroCup 2026-27 — Regular Season Round 5 (Group {f['group']})",
                "date": f["date"],
                "time": f["start_utc"],
                "home": f["home"],
                "away": f["away"],
                "venue": f["venue"],
                "line_status": "unlined",
                "home_summary": None,
                "away_summary": None,
                "winner_market": None,
                "handicap_market": None,
                "total_market": None,
                "pick": None,
                "featured": None,
                "band_pick": None,
                "blank_reason": blank,
                "official_source": "EuroLeague Basketball Live API (EuroCup)",
                "official_url": "https://www.euroleaguebasketball.net/en/eurocup/game-center/",
                "data_url": "https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/games",
                "olbg_url": BASKET_OLBG,
            }
        )
    return rows


def build_flagged(inputs: dict, rows: list[dict]) -> dict:
    gaps = inputs["gap_notes"]
    items = [
        {
            "id": "VF-15",
            "title": "MLB World Series Games 4-7 missing from the verified slate",
            "status": "closed-in-forward",
            "summary": (
                "Forward slate originates all seven World Series games from the official schedule, "
                "including Game 4 (mlb-ws-g4, 2026-10-27, Tropicana Field) which the verified layer "
                "never lined. Games 5-7 carry official if-necessary flags and are priced for the "
                "window but may not be played."
            ),
            "sources": ["https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-11-02"],
        },
        {
            "id": "VF-14",
            "title": "NBA 2026-10-22..24 fixtures not verified",
            "status": gaps["vf-14-nba"]["outcome"],
            "summary": (
                "nba.com now server-renders its month calendar, giving official per-day game counts "
                "(22 Oct: 2, 23 Oct: 12, 24 Oct: 8, ... 31 Oct: 7), but fixture lists for future dates "
                "still fail to server-render ('Sorry, something went wrong'), and the CDN schedule JSON "
                "returns HTTP 500. No NBA rows are added to the forward slate: the desk never publishes "
                "matchups it cannot verify. Attempt log kept in data/forward/capture_gap_notes.json."
            ),
            "sources": ["https://www.nba.com/games"],
        },
        {
            "id": "VF-20",
            "title": "EuroCup Round 5 card missing",
            "status": "closed-in-forward",
            "summary": (
                "All sixteen EuroCup Round 5 fixtures (27-28 October) are captured from the official "
                "EuroLeague live API (competition U, season U2026) and appear in the forward slate. "
                "They ship unlined because the same API's standings endpoints return empty bodies and "
                "the desk never infers team strength."
            ),
            "sources": ["https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/games"],
        },
        {
            "id": "VF-22",
            "title": "GBGB race cards unreachable",
            "status": gaps["vf-22-gbgb"]["outcome"],
            "summary": (
                "gbgb.org.uk returned fetch failures or HTTP 500 on the homepage, the results page and "
                "the race-cards page on 2026-10-22. No greyhound rows are added: there is no verified "
                "card to publish and no trap ratings to price from. Attempt log kept in "
                "data/forward/capture_gap_notes.json."
            ),
            "sources": ["https://www.gbgb.org.uk/"],
        },
        {
            "id": "VF-WINDOW",
            "title": "Forward window coverage",
            "status": "complete-for-verified-sports",
            "summary": (
                f"Slate covers 2026-10-23 .. 2026-11-02: {sum(1 for r in rows if r['sport'] == 'ice-hockey')} "
                f"NHL fixtures (the complete official gameWeek card), "
                f"{sum(1 for r in rows if r['sport'] == 'baseball')} MLB World Series games and "
                f"{sum(1 for r in rows if r['sport'] == 'basketball')} EuroCup Round 5 matches. "
                "NBA and greyhound coverage remain blocked as recorded above; tennis/WST/PDC/volleyball/"
                "handball are explicitly out of scope for this layer."
            ),
            "sources": [],
        },
    ]
    return {"captured_at": inputs["captured_at"], "items": items}


def main() -> None:
    inputs = read_json(FWD / "inputs.json")
    rows = originate_nhl(inputs) + originate_mlb(inputs) + eurocup_unlined(inputs)

    featured_ids: list[str] = []
    for row in rows:
        if row["line_status"] != "originated":
            continue
        feat = featured_selection(row)
        if feat:
            row["featured"] = feat
            row["band_pick"] = _band_pick(feat)
            featured_ids.append(row["id"])
        else:
            row["featured"] = None
            row["band_pick"] = None

    missing = [mid for mid in featured_ids if mid not in NARRATIVES]
    if missing:
        raise SystemExit(
            "featured selections need hand-written narratives before publication: "
            + ", ".join(missing)
        )

    predictions = []
    for row in rows:
        if row["id"] not in NARRATIVES:
            continue
        feat = row["featured"]
        entry = NARRATIVES[row["id"]]
        text = entry["template"].format(
            selection=feat["selection"],
            prob_pct=f"{feat['probability'] * 100:.1f}",
            price=f"{feat['fair_odds']:.2f}",
            american=f"{feat['fair_american']:+d}",
        )
        words = len(text.split())
        if words < MIN_WORDS:
            raise SystemExit(f"{row['id']}: narrative is {words} words, needs {MIN_WORDS}")
        predictions.append(
            {
                "match_id": row["id"],
                "sport": row["sport"],
                "sport_name": row["sport_name"],
                "competition": row["competition"],
                "event": f"{row['away']} @ {row['home']}" if row["sport"] in {"ice-hockey", "baseball"} else f"{row['home']} v {row['away']}",
                "time": row["time"],
                "selection": feat["selection"],
                "market": feat["market"],
                "match_type": "band",
                "probability": feat["probability"],
                "fair_odds": feat["fair_odds"],
                "fair_american": feat["fair_american"],
                "confidence": "high",
                "headline": entry["headline"],
                "text": text,
                "word_count": words,
                "facts": entry["facts"],
                "official_url": row["official_url"],
                "olbg_url": row["olbg_url"],
            }
        )

    counts: dict[str, int] = {
        "total": len(rows),
        "originated": sum(1 for r in rows if r["line_status"] == "originated"),
        "unlined": sum(1 for r in rows if r["line_status"] == "unlined"),
        "band_picks": len(featured_ids),
        "nhl": sum(1 for r in rows if r["sport"] == "ice-hockey"),
        "mlb": sum(1 for r in rows if r["sport"] == "baseball"),
        "eurocup": sum(1 for r in rows if r["sport"] == "basketball"),
    }

    public_rows = [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]
    write_json(FWD / "matches.json", {"captured_at": inputs["captured_at"], "counts": counts, "matches": public_rows})
    write_json(
        FWD / "predictations.json",
        {"captured_at": inputs["captured_at"], "min_words": MIN_WORDS, "count": len(predictions), "predictions": predictions},
    )
    write_json(FWD / "flagged.json", build_flagged(inputs, rows))
    print(f"matches: {counts}")
    print(f"predictions: {len(predictions)}")
    if featured_ids:
        print("featured: " + ", ".join(featured_ids))


if __name__ == "__main__":
    main()
