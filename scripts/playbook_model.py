#!/usr/bin/env python3
"""Playbook model: originate our own prices, grade confidence, test the odds band.

Two documented inputs, never mixed silently:

  tier A  the five NHL fixtures. Expected goals come from each club's goals for and
          goals against per game on the official NHL season summary, run through a
          bivariate Poisson, with a home-ice multiplier (and none for the neutral-site
          Heritage Classic). Prices are originated on the win market, the puck line
          and the match total.

  tier B  every other fixture. OLBG publishes, for each event, the share of its own
          tips on the highlighted selection. That share is already normalised across
          the market's outcomes, so it is read as the market-implied probability of
          that selection. Only the win market can be originated from it: a handicap or
          a total needs scoring data that this capture does not contain.

Price convention: fair price from the probability, then a 4% margin applied to the
decimal odds (the offered decimal is 1 + (fair - 1) x 0.96). Every offered price is
therefore slightly worse than fair, which is what a book would do.

Band: the brief asks for selections between -250 and +10000. A probability of 0.7143
is exactly -250, so in-band means p <= 0.7143 on the favourite side.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "playbook"

MARGIN = 0.96
SHRINK_K = 6.0      # pseudo-tips pulling a small tip sample back toward 50%
BAND_LOW, BAND_HIGH = -250.0, 10000.0
HIGH_P, MED_P = 0.70, 0.60
HOME_MULT, AWAY_MULT = 1.06, 0.94

CONF_RANK = {"high": 3, "medium": 2, "low": 1}


def american(p: float) -> int | None:
    if p is None or p <= 0 or p >= 1:
        return None
    if p > 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def offered_price(p: float) -> int | None:
    """Fair decimal from p, 4% margin, back to an American price."""
    if p is None or p <= 0 or p >= 1:
        return None
    fair_dec = 1.0 / p
    off_dec = 1.0 + (fair_dec - 1.0) * MARGIN
    off_p = 1.0 / off_dec
    return american(off_p)


def in_band(price: int | None) -> bool:
    return price is not None and BAND_LOW <= price <= BAND_HIGH


def poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_matrix(lam_h: float, lam_a: float, maxg: int = 14):
    return {(i, j): poisson(i, lam_h) * poisson(j, lam_a)
            for i in range(maxg) for j in range(maxg)}


def nhl_market(fx) -> dict:
    o = fx["official"]
    h, a = o["home"], o["away"]
    lg = 2.920  # mean of (mean GF/GP, mean GA/GP) across the ten clubs captured, documented
    # ten games of goals for/against is a small sample, so each rate is regressed
    # toward the league mean with fifteen prior games before it is used.
    prior = 15.0
    att_h = (h["gf"] + lg * prior) / (h["gp"] + prior)
    def_h = (h["ga"] + lg * prior) / (h["gp"] + prior)
    att_a = (a["gf"] + lg * prior) / (a["gp"] + prior)
    def_a = (a["ga"] + lg * prior) / (a["gp"] + prior)
    lam_h = att_h * def_a / lg
    lam_a = att_a * def_h / lg
    mult_h, mult_a = (1.0, 1.0) if o["neutral_site"] else (HOME_MULT, AWAY_MULT)
    lam_h *= mult_h
    lam_a *= mult_a
    lam_h = max(0.6, min(6.5, lam_h))
    lam_a = max(0.6, min(6.5, lam_a))

    m = poisson_matrix(lam_h, lam_a)
    p_home = sum(p for (i, j), p in m.items() if i > j)
    p_tie = sum(p for (i, j), p in m.items() if i == j)
    p_away = sum(p for (i, j), p in m.items() if i < j)
    # NHL regular season always resolves: half of the 60-minute ties go to each side
    p_home += p_tie / 2
    p_away += p_tie / 2

    p_home_ml = min(0.85, max(0.15, p_home / (p_home + p_away)))
    p_away_ml = 1.0 - p_home_ml

    # puck lines settled on the 60-minute-plus-overtime scoreline
    p_home_win_by2 = min(0.85, sum(p for (i, j), p in m.items() if i - j >= 2))
    p_away_win_by2 = min(0.85, sum(p for (i, j), p in m.items() if j - i >= 2))
    p_home_m15 = 1.0 - p_away_win_by2
    p_away_p15 = 1.0 - p_home_win_by2

    total = {(i + j): sum(p for (a1, b1), p in m.items() if a1 + b1 == i + j) for i, j in [(0, 0)]}
    dist = {}
    for (i, j), p in m.items():
        dist[i + j] = dist.get(i + j, 0.0) + p
    p_over55 = min(0.85, max(0.15, sum(p for t, p in dist.items() if t >= 6)))
    p_over65 = min(0.85, max(0.15, sum(p for t, p in dist.items() if t >= 7)))

    fav_home = p_home_ml >= 0.5
    pl_market = [
        {"market": "Puck line 1.5 (favourite -1.5)", "selection": f"{fx['home']} -1.5",
         "p": round(p_home_win_by2 if fav_home else p_away_win_by2, 4)},
        {"market": "Puck line 1.5 (favourite -1.5)", "selection": f"{fx['away']} +1.5",
         "p": round(p_away_p15 if fav_home else p_home_m15, 4)},
    ]
    # make sure the two sides of the puck line are the same bet from both ends
    if fav_home:
        pl_market[1]["selection"] = f"{fx['away']} +1.5"
        pl_market[1]["p"] = round(1 - pl_market[0]["p"], 4)
    else:
        pl_market[1]["selection"] = f"{fx['home']} +1.5"
        pl_market[1]["p"] = round(1 - pl_market[0]["p"], 4)

    return {
        "lambda_home": round(lam_h, 2), "lambda_away": round(lam_a, 2),
        "att_home": round(att_h, 2), "def_home": round(def_h, 2),
        "att_away": round(att_a, 2), "def_away": round(def_a, 2),
        "observed_gf_home": round(h["gf"] / h["gp"], 2), "observed_gf_away": round(a["gf"] / a["gp"], 2),
        "markets": [
            {"market": "Match winner", "selection": fx["home"], "p": round(p_home_ml, 4)},
            {"market": "Match winner", "selection": fx["away"], "p": round(p_away_ml, 4)},
        ] + pl_market + [
            {"market": "Match total 5.5", "selection": "Over 5.5", "p": round(p_over55, 4)},
            {"market": "Match total 5.5", "selection": "Under 5.5", "p": round(1 - p_over55, 4)},
            {"market": "Match total 6.5", "selection": "Over 6.5", "p": round(p_over65, 4)},
            {"market": "Match total 6.5", "selection": "Under 6.5", "p": round(1 - p_over65, 4)},
        ],
    }


WIN_MARKETS = {"Money Line", "Win Match", "To Win", "Win Match 2-way", "Win Tournament"}


def shrunk(won: int, total: int) -> float | None:
    """A tip share on a handful of tips is not a probability, so it is pulled
    toward 50% with SHRINK_K pseudo-tips before it is priced."""
    if not total:
        return None
    return (won + SHRINK_K * 0.5) / (total + SHRINK_K)


def market_label(raw: str) -> str:
    return {
        "Money Line": "Match winner",
        "Win Match": "Match winner",
        "To Win": "Match winner",
        "Win Match 2-way": "Match winner",
        "Pointspread": "Handicap (points spread)",
        "Handicap": "Handicap",
        "Total 180s": "Total 180s",
        "Daily Races": "Race winner",
        "Top Team1 Batsman": "Top team-1 batsman",
    }.get(raw, raw)


def tier_b_market(fx) -> dict | None:
    p = shrunk(fx.get("tips_won") or 0, fx.get("tips_total") or 0)
    if p is None:
        return None
    if fx["tipped_selection"] in ("Tie", "Draw"):
        return None
    label = market_label(fx["market"])
    markets = [{"market": label, "selection": fx["tipped_selection"], "p": round(p, 4)}]
    if fx["market"] in WIN_MARKETS and fx.get("_other_side"):
        markets.append({"market": label, "selection": fx["_other_side"], "p": round(1 - p, 4)})
    return {
        "lambda_home": None, "lambda_away": None,
        "observed_gf_home": None, "observed_gf_away": None,
        "sample": {"won": fx.get("tips_won"), "total": fx.get("tips_total"), "shrunk_from": fx.get("tip_share")},
        "markets": markets,
    }


def confidence(p: float, tier: str, band_ok: bool) -> str:
    """The rubric printed on /playbook/methodology.html.

    A price of -250 is a 71.43% chance, so a pure ">70% is high" rule and a
    "-250 to +10000" rule can only ever meet in a 1.4-point window. Confidence here
    therefore requires all three of: a governing-body input, a modelled probability
    of 65% or better, and a price inside the requested band. Selections at 70%+ whose
    price falls outside the band are still listed, as medium, with the shortfall shown.
    """
    if tier == "A" and band_ok and p >= 0.65:
        return "high"
    if band_ok and p >= 0.50:
        return "medium"
    if p >= HIGH_P:
        return "medium"
    return "low"


def main() -> None:
    fx_doc = json.loads((DATA / "fixtures.json").read_text())
    lines, picks = [], []

    for fx in fx_doc["fixtures"]:
        model = None
        if fx["tier"] == "A" and fx.get("official"):
            model = nhl_market(fx)
        else:
            # the other side of a two-horse market, used only for the complement price
            home, away = fx["home"], fx["away"]
            sel = fx["tipped_selection"]
            if sel and home and away:
                fx["_other_side"] = away if sel.startswith(home.split()[0]) else home
            model = tier_b_market(fx)

        if not model:
            continue

        row_lines = []
        for mk in model["markets"]:
            price = offered_price(mk["p"])
            row_lines.append({
                "market": mk["market"], "selection": mk["selection"],
                "probability": mk["p"], "price": price, "in_band": in_band(price),
            })
        lines.append({
            "fid": fx["fid"], "sport": fx["sport"], "competition": fx["competition"], "event": fx["event"],
            "tier": fx["tier"], "input": ("official NHL season totals + bivariate Poisson"
                                          if fx["tier"] == "A" else "OLBG published tip share"),
            "lambda_home": model["lambda_home"], "lambda_away": model["lambda_away"],
            "tip_sample": model.get("sample"),
            "observed_gf_home": model["observed_gf_home"], "observed_gf_away": model["observed_gf_away"],
            "lines": row_lines,
            "olbg_url": fx["olbg_url"], "source_url": fx.get("source_url") or fx["olbg_url"],
            "source_label": fx.get("source_label") or "OLBG",
            "start_utc": fx.get("start_utc_official") or fx["start_utc_estimate"],
            "day": fx["olbg_day"],
        })

        # one pick per market, always the side the price favours
        if fx["tier"] == "B":
            candidates = model["markets"][:1]
        else:
            # for each market take the strongest side whose price sits inside the
            # requested band; only if neither side qualifies do we take the strongest
            # side overall and mark it out of band.
            buckets: dict[str, list] = {}
            for mk in model["markets"]:
                buckets.setdefault(mk["market"], []).append(mk)
            candidates = []
            for market, options in buckets.items():
                banded = [o for o in options if in_band(offered_price(o["p"]))]
                pool = banded or options
                candidates.append(max(pool, key=lambda o: o["p"]))

        for mk in candidates:
            p = mk["p"]
            price = offered_price(p)
            picks.append({
                "pick_id": f"{fx['fid']}-{mk['market'].lower().replace(' ', '-').replace('.', '').replace('%', '')}",
                "fid": fx["fid"], "sport": fx["sport"], "sport_slug": fx["sport_slug"],
                "competition": fx["competition"], "event": fx["event"],
                "market": mk["market"], "selection": mk["selection"],
                "probability": round(p, 4), "price": price,
                "confidence": confidence(p, fx["tier"], in_band(price)),
                "tier": fx["tier"],
                "input": ("official NHL season totals" if fx["tier"] == "A" else "OLBG published tip share"),
                "in_band": in_band(price),
                "day": fx["olbg_day"],
                "start_utc": fx.get("start_utc_official") or fx["start_utc_estimate"],
                "started_at_capture": fx["status_at_capture"] != "not_started",
                "olbg_url": fx["olbg_url"],
                "source_url": fx.get("source_url") or fx["olbg_url"],
                "source_label": fx.get("source_label") or "OLBG",
            })

    # keep the strongest picks per sport, capped at ten, and only those not already under way
    by_sport = {}
    for p in picks:
        if p["started_at_capture"] or (p["start_utc"] or "") < "2026-10-25T00:00:00Z" or p["price"] is None:
            continue
        by_sport.setdefault(p["sport"], []).append(p)

    kept = []
    for sport, rows in by_sport.items():
        rows.sort(key=lambda r: (r["tier"] == "A", CONF_RANK[r["confidence"]], r["probability"]), reverse=True)
        kept.extend(rows[:10])

    kept.sort(key=lambda r: (r["day"], -CONF_RANK[r["confidence"]], -r["probability"]))

    summary = {
        "generated_utc": fx_doc["generated_utc"],
        "count": len(kept),
        "price_count": sum(len(l["lines"]) for l in lines),
        "by_sport": {s: sum(1 for p in kept if p["sport"] == s) for s in sorted({p["sport"] for p in kept})},
        "by_confidence": {c: sum(1 for p in kept if p["confidence"] == c) for c in ("high", "medium", "low")},
        "by_tier": {t: sum(1 for p in kept if p["tier"] == t) for t in ("A", "B")},
        "in_band": sum(1 for p in kept if p["in_band"]),
        "high_in_band": sum(1 for p in kept if p["confidence"] == "high" and p["in_band"]),
        "band": [BAND_LOW, BAND_HIGH],
        "shrink_pseudo_tips": SHRINK_K,
        "picks": kept,
    }
    (DATA / "lines.json").write_text(json.dumps({
        "generated_utc": fx_doc["generated_utc"], "count": len(lines),
        "margin": "4% of the win part of the fair decimal price",
        "lines": lines,
    }, indent=1) + "\n")
    (DATA / "picks.json").write_text(json.dumps(summary, indent=1) + "\n")

    print(f"playbook_model: {len(lines)} fixtures priced ({summary['price_count']} selections), "
          f"{len(kept)} picks {summary['by_confidence']}, in band {summary['in_band']}, "
          f"high+in-band {summary['high_in_band']}")
    print("  by sport:", summary["by_sport"])


if __name__ == "__main__":
    main()
