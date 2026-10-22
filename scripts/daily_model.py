#!/usr/bin/env python3
"""Originate fair prices for every /daily/ fixture from first-hand official captures.

Markets originated:
  * match winner (moneyline) for every tennis fixture with a verified seed/form input
  * games handicap, alternate lines at half-game steps, both sides
  * total games, alternate lines at half-game steps, both sides

Nothing here reads a bookmaker price. A fixture with no official strength input
(the cricket rows) publishes a blank line and a written reason instead.

Confidence rule published on the site:
  high   = model probability >= 0.7000
  medium = 0.6000 .. 0.6999
  low    = below 0.6000
Price-window rule from the brief (''-250 to +10000''):
  in-band = fair American price numerically >= -250, i.e. 0.7000 <= p <= 0.714286
  A high-confidence pick can therefore sit outside the window (shorter than -250);
  that is labelled on every page rather than hidden.

Stdlib only. Deterministic.
"""

from __future__ import annotations

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "daily")

HIGH_P = 0.7000
MEDIUM_P = 0.6000
BAND_MAX_P = 250.0 / 350.0          # fair -250  (0.714286)
BAND_MIN_P = 0.7000
BAND_MAX_AMERICAN = 10000


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as handle:
        return json.load(handle)


def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def price(p):
    """Fair decimal and American from a probability rounded to four decimals first."""
    if p is None or p <= 0.0:
        return {"p": None, "fair_decimal": None, "fair_american": None}
    pr = round(p, 4)
    decimal = 1.0 / pr
    american = 100.0 * (decimal - 1.0) if decimal >= 2.0 else -100.0 / (decimal - 1.0)
    return {"p": pr, "fair_decimal": round(decimal, 2), "fair_american": int(round(american))}


def in_band(p):
    return p is not None and BAND_MIN_P <= p <= BAND_MAX_P


def label(p):
    if p is None:
        return ""
    if p >= HIGH_P:
        return "high"
    if p >= MEDIUM_P:
        return "medium"
    return "low"


def rating(side, constants):
    if side["status"] == "seeded":
        base = constants["seed_rating_base"] + constants["seed_rating_step"] * (
            constants["seed_rating_anchor"] - side["seed"]
        )
    elif side["status"] == "qualifier":
        base = constants["qualifier_rating"]
    else:
        base = constants["unseeded_rating"]
    return base + constants["form_per_set"] * (side["sets_won"] - side["sets_lost"])


def half_lines(centre, spread, step=0.5):
    """Half-point lines around a centre, never on a whole number (no push)."""
    out = []
    n = int(round(spread / step))
    for k in range(1, n + 1):
        v = round(centre + k * step, 1)
        if abs(v - round(v)) < 1e-9:            # snap a whole number to the half point
            v = round(v + (step if centre >= v else -step), 1)
        if v not in out:
            out.append(v)
    return out


def originate(fixture, inputs, constants):
    ra, rb = rating(inputs["a"], constants), rating(inputs["b"], constants)
    p_a = 1.0 / (1.0 + 10.0 ** (-(ra - rb) / constants["rating_scale"]))
    p_b = 1.0 - p_a
    mu = constants["margin_games_per_probability_unit"] * (p_a - 0.5)
    sd = constants["margin_sd_games"]

    rows = []
    for side, name, p in (("a", fixture["a"]["name"], p_a), ("b", fixture["b"]["name"], p_b)):
        row = {"fixture_id": fixture["id"], "market": "match_winner", "selection": name,
               "line": None, "side": side}
        row.update(price(p))
        row["confidence"] = label(row["p"])
        row["in_band"] = in_band(row["p"])
        rows.append(row)

    # Games handicap: a -L means a must win by more than L games.
    for side, sign, centre in (("a", 1, mu), ("b", -1, -mu)):
        name = fixture["a"]["name"] if side == "a" else fixture["b"]["name"]
        for line in half_lines(centre, 7.0):
            l = round(sign * line, 1)
            cover = 1.0 - phi((line - centre) / sd)
            row = {"fixture_id": fixture["id"], "market": "games_handicap",
                   "selection": f"{name} {'+' if l > 0 else ''}{l}", "line": l, "side": side}
            row.update(price(cover))
            row["confidence"] = label(row["p"])
            row["in_band"] = in_band(row["p"])
            rows.append(row)

    mean, tsd = constants["total_mean_games"], constants["total_sd_games"]
    for line in half_lines(mean, 3.0):
        over = 1.0 - phi((line - mean) / tsd)
        for selection, p in (("Over", over), ("Under", 1.0 - over)):
            row = {"fixture_id": fixture["id"], "market": "total_games",
                   "selection": f"{selection} {line}", "line": line, "side": selection.lower()}
            row.update(price(p))
            row["confidence"] = label(row["p"])
            row["in_band"] = in_band(row["p"])
            rows.append(row)
    return rows, {"rating_a": ra, "rating_b": rb, "p_a": round(p_a, 4), "p_b": round(p_b, 4),
                  "margin_mean": round(mu, 3), "margin_sd": sd,
                  "total_mean": mean, "total_sd": tsd}


def main():
    fixtures = load("fixtures.json")["fixtures"]
    inputs = load("inputs.json")
    constants = inputs["constants"]
    input_by_id = {row["id"]: row for row in inputs["fixtures"]}

    lines, model_rows = [], []
    for fixture in fixtures:
        if fixture["id"] not in input_by_id:
            lines.append({
                "fixture_id": fixture["id"], "market": "match_winner", "selection": "",
                "line": None, "side": "", "p": None, "fair_decimal": None,
                "fair_american": None, "confidence": "", "in_band": False,
                "blank_reason": "No official strength input was read for this fixture. The ICC team-rankings table "
                                "rendered an empty body in this session, so originating a price would be inference."
            })
            continue
        rows, model = originate(fixture, input_by_id[fixture["id"]], constants)
        lines.extend(rows)
        model_rows.append(dict(model, fixture_id=fixture["id"], sport=fixture["sport"]))

    # Winner pick per fixture, plus the best in-band pick per fixture.
    winner_picks, band_picks = [], []
    for fixture in fixtures:
        rows = [r for r in lines if r["fixture_id"] == fixture["id"] and r["p"] is not None]
        if not rows:
            continue
        ml = [r for r in rows if r["market"] == "match_winner"]
        best = max(ml, key=lambda r: r["p"])
        winner_picks.append({
            "fixture_id": fixture["id"], "sport": fixture["sport"],
            "selection": best["selection"], "p": best["p"],
            "fair_decimal": best["fair_decimal"], "fair_american": best["fair_american"],
            "confidence": best["confidence"], "in_band": best["in_band"],
        })

    counts = {
        "fixtures": len(fixtures),
        "lined_fixtures": len({r["fixture_id"] for r in lines if r["p"] is not None}),
        "unlined_fixtures": len({r["fixture_id"] for r in lines if r["p"] is None}),
        "prices": sum(1 for r in lines if r["p"] is not None),
        "markets": len({(r["fixture_id"], r["market"]) for r in lines if r["p"] is not None}),
        "high_confidence_prices": sum(1 for r in lines if r["confidence"] == "high"),
        "in_band_prices": sum(1 for r in lines if r["in_band"]),
        "high_confidence_winners": sum(1 for w in winner_picks if w["confidence"] == "high"),
    }
    # How close could any originated price get to the brief's -250 window?
    priced = [r for r in lines if r["p"] is not None and r["market"] != "match_winner"]
    window_probe = None
    if priced:
        nearest = min(priced, key=lambda r: abs(r["p"] - BAND_MAX_P))
        window_probe = {"selection": nearest["selection"], "market": nearest["market"],
                        "fixture_id": nearest["fixture_id"], "p": nearest["p"],
                        "fair_american": nearest["fair_american"],
                        "gap_points": round(abs(nearest["p"] - BAND_MAX_P) * 100, 2),
                        "in_window": in_band(nearest["p"])}

    top = {}
    for pick in winner_picks:
        top.setdefault(pick["sport"], [])
    for sport in top:
        ranked = sorted([w for w in winner_picks if w["sport"] == sport],
                        key=lambda w: -w["p"])
        top[sport] = ranked[:5]

    payload = {
        "layer": "daily",
        "gate": {"high_p": HIGH_P, "medium_p": MEDIUM_P, "band_min_p": BAND_MIN_P,
                 "band_max_p": round(BAND_MAX_P, 6), "band_max_american": BAND_MAX_AMERICAN,
                 "note": "high = p >= 0.7000. in_band = 0.7000 <= p <= 0.714286, which is the fair-price "
                         "window -250 to +10000 in the brief. A 'high' pick shorter than -250 is labelled "
                         "out-of-window rather than reclassified."},
        "counts": counts,
        "model": model_rows,
        "rows": lines,
        "winner_picks": winner_picks,
        "top_picks": top,
        "window_probe": window_probe,
    }
    with open(os.path.join(DATA, "lines.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"counts": counts,
                      "winner_picks": [(w["fixture_id"], w["selection"], w["p"], w["confidence"], w["in_band"]) for w in winner_picks],
                      "window_probe": window_probe},
                     indent=1))


if __name__ == "__main__":
    main()
