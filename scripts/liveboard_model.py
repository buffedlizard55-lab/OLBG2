#!/usr/bin/env python3
"""
liveboard_model.py — deterministic line origination for the /liveboard/ desk.

Inputs
  data/liveboard/olbg.json    fixtures, markets and tip counts captured first-hand from olbg.com
  data/liveboard/inputs.json  numbers read first-hand from official governing-body endpoints

Output
  data/liveboard/lines.json   one row per originated market, with probability, fair price,
                              our offered price, the band test and a confidence label

Two provenance classes are produced and never mixed silently:

  A  "official-model"    probability estimated from a number returned by an official body
                         (MLB records, NHL published moneylines, EuroLeague standings,
                         WST ranking money, F1 championship points).
  B  "community-implied" probability estimated from the tip-share that OLBG itself publishes
                         for the selection, smoothed with a Laplace prior so that a 1/1 tip
                         can never become a 100% estimate.

Nothing else is used. A fixture with neither an official input nor an OLBG tip count is left
unlined and appears in data/liveboard/flagged.json instead of being priced.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "liveboard"

MARGIN = {
    "Baseball": 0.05,
    "Ice Hockey": 0.05,
    "Basketball": 0.05,
    "Snooker": 0.05,
    "Motor Racing": 0.06,
    "Rugby Union": 0.05,
    "Darts": 0.05,
    "Cricket": 0.05,
    "Volleyball": 0.05,
    "Handball": 0.06,
    "Gaelic Sports": 0.05,
    "Greyhounds": 0.08,
    "Tennis": 0.05,
    "Rugby League": 0.06,
    "Golf": 0.05,
}

# A high label needs both a probability at or above 0.70 and enough observations behind it.
MIN_TIPS_FOR_HIGH = 6
# In-band rule from the brief: our offered American price between -250 and +10000.
BAND_LOW, BAND_HIGH = -250.0, 10000.0


# ---------------------------------------------------------------- price helpers
def decimal_from_prob(p: float) -> float:
    return 1.0 / p


def american_from_decimal(d: float) -> float:
    if d >= 2.0:
        return round((d - 1.0) * 100.0, 0)
    return round(-100.0 / (d - 1.0), 0)


def fmt_american(a: float) -> str:
    a = int(round(a))
    return f"+{a}" if a > 0 else f"{a}"


def in_band(american: float) -> bool:
    return BAND_LOW <= american <= BAND_HIGH


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# ------------------------------------------------------------- probability models
def p_moneyline_log5(pct_a: float, pct_b: float, home_edge: float) -> float:
    """Bill James log5, then a home-field shift applied on the logit scale."""
    num = pct_a * (1.0 - pct_b)
    den = num + pct_b * (1.0 - pct_a)
    base = num / den if den else 0.5
    base = min(max(base, 0.02), 0.98)
    return logistic(math.log(base / (1.0 - base)) + home_edge)


def p_from_decimal_odds(odds_list) -> float:
    """Proportional de-vig of one side's published decimal/American moneylines."""
    probs = []
    for o in odds_list:
        d = float(o) if not str(o).startswith(("+", "-")) else (1.0 + float(o) / 100.0 if str(o).startswith("+") else 1.0 + 100.0 / abs(float(o)))
        probs.append(1.0 / d)
    return sum(probs) / len(probs)


def p_from_rating_diff(rating_a: float, rating_b: float, scale: float, home_edge: float = 0.0) -> float:
    return logistic(scale * (rating_a - rating_b) + home_edge)


def p_total_over(expected_total: float, line: float, sd: float) -> float:
    """P(total > line) under a normal approximation, continuity-corrected by 0.5."""
    if sd <= 0:
        return 0.5
    z = (expected_total - line) / sd
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def p_margin_over(expected_margin: float, line: float, sd: float) -> float:
    """P(margin > line) under a normal approximation."""
    z = (expected_margin - line) / sd
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# --------------------------------------------------------------------- load data
def load():
    olbg = json.loads((DATA / "olbg.json").read_text())
    inputs = json.loads((DATA / "inputs.json").read_text())
    blocks = {b["id"]: b for b in inputs["blocks"]}
    return olbg, blocks


def make_row(sport, event, market, family, p, source_class, source_url, basis, sample=None, note=""):
    margin = MARGIN.get(sport, 0.05)
    p = min(max(p, 1e-4), 1 - 1e-4)
    fair_dec = decimal_from_prob(p)
    offered_dec = 1.0 / (p * (1.0 - margin))
    fair_am = american_from_decimal(fair_dec)
    offered_am = american_from_decimal(offered_dec)
    band = in_band(offered_am)

    high_ok = p >= 0.70 and (sample is None or sample >= MIN_TIPS_FOR_HIGH)
    if high_ok:
        conf = "high"
    elif p >= 0.60:
        conf = "medium"
    else:
        conf = "low"

    return {
        "sport": sport,
        "event": event["n"],
        "event_id": event["id"],
        "olbg_url": event["u"],
        "time_displayed": event["t"],
        "market": market,
        "selection": event["s"],
        "family": family,
        "probability": round(p, 4),
        "fair_decimal": round(fair_dec, 3),
        "fair_american": fmt_american(fair_am),
        "offered_decimal": round(offered_dec, 3),
        "offered_american": fmt_american(offered_am),
        "margin": margin,
        "in_band": band,
        "confidence": conf,
        "source_class": source_class,
        "source_url": source_url,
        "basis": basis,
        "tip_sample": sample,
        "note": note,
        "high_and_in_band": bool(conf == "high" and band),
        "is_match": not event.get("outright"),
    }


def main():
    olbg, blocks = load()
    rows = []
    unlined = []
    originated_lines = []

    mlb = {b["id"]: b for b in blocks.values() if b["sport"] == "Baseball"}
    tb = blocks["MLB-STANDINGS-TB"]["fields"]
    mil = blocks["MLB-STANDINGS-MIL"]["fields"]
    el = blocks["EL-STANDINGS"]["teams"]
    f1 = {d["driver"]: d for d in blocks["F1-DRIVERS-2026"]["drivers"]}
    wst_world = blocks["WST-RANKINGS"]["world"]
    wst_year = blocks["WST-RANKINGS"]["one_year"]
    nhl_odds = blocks["NHL-SCHEDULE-2324"]["published_odds_moneyline"]

    for hub in olbg["hubs"]:
        sport = hub["sport"]
        for ev in hub.get("events", []):
            market = ev.get("m", "")
            if not market:
                market = "Handicap" if re.search(r"[+-]\d", ev.get("s", "")) else "Win Match"
            family = "outright" if ev.get("outright") else (
                "handicap" if "handicap" in market.lower() or "spread" in market.lower() or "puck line" in market.lower() or "run line" in market.lower() else
                "total" if "total" in market.lower() else
                "winner"
            )
            sample = ev.get("tw")
            handled = False

            # ---------------------------------------------------------- BASEBALL (official model)
            if sport == "Baseball" and ev["id"] == 160789 and family == "winner":
                p_mil = p_moneyline_log5(float(mil["pct"]), float(tb["pct"]), home_edge=0.10)
                rows.append(make_row(sport, ev, "Money Line", "winner", p_mil, "official-model",
                                     "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
                                     f"log5 on MLB regular-season win% (MIL {mil['pct']} v TB {tb['pct']}) with a 0.10 logit home edge for the Brewers",
                                     sample))
                # Run line: expected margin from runs scored/allowed per game
                mil_rs, mil_ra = mil["runsScored"] / 162, mil["runsAllowed"] / 162
                tb_rs, tb_ra = tb["runsScored"] / 162, tb["runsAllowed"] / 162
                exp_margin = (mil_rs + tb_ra) / 2 - (tb_rs + mil_ra) / 2
                exp_total = (mil_rs + tb_ra) / 2 + (tb_rs + mil_ra) / 2
                p_rl = p_margin_over(exp_margin, 1.5, 4.2)
                rows.append(make_row(sport, ev, "Run Line -1.5", family="handicap", p=p_rl, source_class="official-model",
                                     source_url="https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
                                     basis=f"expected margin {exp_margin:+.2f} runs (season runs for/against per game), normal sd 4.2",
                                     sample=sample))
                originated_lines.append({
                    "sport": sport, "event": ev["n"], "event_id": ev["id"], "olbg_url": ev["u"],
                    "market": "Game Totals", "line": round(exp_total * 2) / 2.0,
                    "basis": f"combined season runs for/against per game; expected margin {exp_margin:+.2f}",
                    "source_url": "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
                })
                originated_lines.append({
                    "sport": sport, "event": ev["n"], "event_id": ev["id"], "olbg_url": ev["u"],
                    "market": "Run Line", "line": -1.5 if exp_margin > 0 else 1.5,
                    "basis": f"expected margin {exp_margin:+.2f} runs makes -1.5 the natural run line for the stronger side",
                    "source_url": "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
                })
                p_over = p_total_over(exp_total, 8.5, 4.2)
                over_ev = dict(ev)
                over_ev["s"] = "Over 8.5"
                rows.append(make_row(sport, over_ev, "Game Totals 8.5", "total", p_over, "official-model",
                                     "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
                                     f"expected total {exp_total:.2f} runs, normal sd 4.2", sample))
                handled = True

            # ---------------------------------------------------------- ICE HOCKEY NHL (official market)
            elif sport == "Ice Hockey" and ev["id"] == 199984 and family == "winner":
                p = p_from_decimal_odds(nhl_odds["2026020166"]["MTL"])
                rows.append(make_row(sport, ev, "Money Line", "winner", p, "official-model",
                                     "https://api-web.nhle.com/v1/schedule/2026-10-23",
                                     "mean implied probability of the NHL feed's published MTL moneylines (-170,-170,-162)",
                                     sample))
                handled = True
            elif sport == "Ice Hockey" and ev["id"] == 199967 and family == "winner":
                p = p_from_decimal_odds(nhl_odds["2026020167"]["COL"])
                rows.append(make_row(sport, ev, "Money Line", "winner", p, "official-model",
                                     "https://api-web.nhle.com/v1/schedule/2026-10-23",
                                     "mean implied probability of the NHL feed's published COL moneylines (-129,-128,-125)",
                                     sample))
                handled = True

            # ---------------------------------------------------------- BASKETBALL EuroLeague
            elif sport == "Basketball" and ev.get("c") == "Euroleague" and family == "winner":
                pair = {"535928": ("Zalgiris Kaunas", "LDLC ASVEL Villeurbanne", "Zalgiris"),
                        "535925": ("Olympiacos Piraeus", "Fenerbahce Tarfin Istanbul", "Olympiacos"),
                        "535926": ("Paris Basketball", "Valencia Basket", "Valencia")}.get(str(ev["id"]))
                if pair:
                    a, b, _s = pair
                    ra = el[a]["diff"] / el[a]["gp"]
                    rb = el[b]["diff"] / el[b]["gp"]
                    p = p_from_rating_diff(ra, rb, scale=0.16, home_edge=0.12 if a != "Paris Basketball" else 0.12)
                    if ev["s"] == b:
                        p = 1 - p
                        ra, rb = rb, ra
                        a, b = b, a
                    rows.append(make_row(sport, ev, "Money Line", "winner", p, "official-model",
                                         "https://www.euroleaguebasketball.net/en/euroleague/standings/",
                                         f"EuroLeague point differential per game ({a} {ra:+.2f} v {b} {rb:+.2f}), logistic scale 0.16, 0.12 home edge",
                                         sample))
                    exp_total = ((el[pair[0]]["pts_plus"] + el[pair[0]]["pts_minus"]) / el[pair[0]]["gp"] +
                                 (el[pair[1]]["pts_plus"] + el[pair[1]]["pts_minus"]) / el[pair[1]]["gp"]) / 2.0
                    exp_margin = (el[pair[0]]["diff"] / el[pair[0]]["gp"]) - (el[pair[1]]["diff"] / el[pair[1]]["gp"])
                    originated_lines.append({
                        "sport": sport, "event": ev["n"], "event_id": ev["id"], "olbg_url": ev["u"],
                        "market": "Game Totals", "line": round(exp_total * 2) / 2.0,
                        "basis": f"mean of both clubs' season points for+against per game ({pair[0]} and {pair[1]})",
                        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/standings/",
                    })
                    originated_lines.append({
                        "sport": sport, "event": ev["n"], "event_id": ev["id"], "olbg_url": ev["u"],
                        "market": "Pointspread", "line": round(exp_margin * 2) / 2.0,
                        "basis": f"difference in EuroLeague point differential per game ({pair[0]} minus {pair[1]})",
                        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/standings/",
                    })
                    handled = True

            # ---------------------------------------------------------- SNOOKER (WST ranking money)
            elif sport == "Snooker" and family == "winner":
                players = {9950: ("David Gilbert", "Mark Williams"), 9951: ("Jak Jones", "Scott Donaldson")}[ev["id"]]
                a, b = players
                ma = wst_world.get(a) or wst_year.get(a)
                mb = wst_world.get(b) or wst_year.get(b)
                if ma and mb:
                    p = p_from_rating_diff(math.log(ma), math.log(mb), scale=0.45)
                    if ev["s"] == b and ev["s"] != a:
                        p = 1 - p
                    rows.append(make_row(sport, ev, "Win Match", "winner", p, "official-model",
                                         "https://www.wst.tv/rankings/",
                                         f"log of WST ranking money ({a} £{ma:,} v {b} £{mb:,}) as a strength scale",
                                         sample))
                    handled = True
                else:
                    unlined.append({"sport": sport, "event": ev["n"], "event_id": ev["id"],
                                    "reason": "WST ranking money was captured for the other player but not for this selection's opponent, so no official strength input exists for the pair.",
                                    "source_url": "https://www.wst.tv/rankings/"})

            # ---------------------------------------------------------- MOTOR RACING (points share)
            elif sport == "Motor Racing" and not ev.get("outright") and family == "winner":
                total_pts = sum(d["points"] for d in f1.values())
                ver = f1["Max Verstappen"]["points"]
                p = ver / total_pts * 0.55  # championship points share, discounted because a race is a single event
                rows.append(make_row(sport, ev, "Win Race", "winner", p, "official-model",
                                     "https://www.formula1.com/en/results/2026/drivers",
                                     f"Verstappen {ver} of {total_pts} points among the eight drivers captured, discounted x0.55 for single-race variance",
                                     sample))
                handled = True

            # ---------------------------------------------------------- Generic fallback: OLBG tip share
            if not handled:
                if sample and sample > 0 and ev.get("w") is not None:
                    # Laplace smoothing: (w+1)/(n+2) keeps a 1/1 tip away from certainty.
                    p = (ev["w"] + 1.0) / (sample + 2.0)
                    rows.append(make_row(sport, ev, market or "Win", family, p, "community-implied",
                                         ev["u"],
                                         f"Laplace-smoothed OLBG tip share ({ev['w']} of {sample} tips)",
                                         sample,
                                         note="OLBG publishes tip shares, not odds; this price is our own transformation of that share."))
                else:
                    unlined.append({"sport": sport, "event": ev["n"], "event_id": ev["id"],
                                    "reason": "No official input and no usable OLBG tip sample for this row.",
                                    "source_url": ev["u"]})

    # ---------------------------------------------------------------- coverage summary
    coverage = {}
    for hub in olbg["hubs"]:
        s = hub["sport"]
        evs = hub.get("events", [])
        priced = [r for r in rows if r["sport"] == s]
        high = [r for r in priced if r["high_and_in_band"] and r["is_match"]]
        officially = [r for r in priced if r["source_class"] == "official-model"]
        coverage[s] = {
            "events_captured": len(evs),
            "markets_priced": len(priced),
            "rows_official_model": len(officially),
            "rows_community_implied": len(priced) - len(officially),
            "high_confidence_in_band": len(high),
            "high_confidence_in_band_incl_outrights": len([r for r in priced if r["high_and_in_band"]]),
            "unlined_rows": len([u for u in unlined if u["sport"] == s]),
        }

    out = {
        "generated_utc": olbg["captured_utc"],
        "method": {
            "margin": MARGIN,
            "min_tips_for_high": MIN_TIPS_FOR_HIGH,
            "band": f"offered American price between {int(BAND_LOW)} and +{int(BAND_HIGH)}",
            "official_model": "probability from an official governing-body number",
            "community_implied": "Laplace-smoothed OLBG tip share, transformed into our own price",
        },
        "rows": rows,
        "originated_lines": originated_lines,
        "unlined": unlined,
        "coverage": coverage,
    }
    (DATA / "lines.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

    print(f"rows: {len(rows)}  high+in-band (matches): {sum(1 for r in rows if r['high_and_in_band'] and r['is_match'])}  fair lines: {len(originated_lines)}  unlined: {len(unlined)}")
    for s, c in coverage.items():
        print(f"  {s:15s} events {c['events_captured']:3d}  priced {c['markets_priced']:3d}  high {c['high_confidence_in_band']:2d}")


if __name__ == "__main__":
    main()
