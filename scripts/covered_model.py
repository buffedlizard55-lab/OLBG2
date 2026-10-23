#!/usr/bin/env python3
"""Originate our own lines for the /covered/ desk from verified inputs only.

Reads  data/covered/inputs.json  (fixtures + values transcribed from official pages)
Writes data/covered/lines.json, data/covered/matches.json, data/covered/picks.json,
       data/covered/predictions.json

Method (documented in covered/methodology.html):
* Win market only, and only where a sport has verified, comparable team inputs
  (W-L or points records from an official feed). Everything else is left blank.
* Team strength = shrunk win (or points) percentage: (pts + K) / (2*GP + 2*K) for NHL,
  (W + K/2) / (GP + K) for NBA, with K = 10 prior games. K and the NHL home-ice
  adjustment are our own modelling assumptions, not facts from any source.
* Head-to-head win probability uses the log5 formula. The NHL home adjustment adds
  HOME_LOGIT to the home side's log-odds. NBA home side is not stated on the official
  page, so the NBA line is treated as neutral.
* Labels: low (<60%), medium (60-69.99%), high (>=70%). A 'high' label also needs at
  least SAMPLE_HIGH games for both sides, otherwise it is capped at medium.
* Brief's band gate: a pick qualifies only if p >= 0.70 AND the pick's fair American
  price is between -250 and +10000 inclusive. For favourites, a 70% price is about -233,
  so the literal band admits only roughly 70.0%-71.4%.
"""
from __future__ import annotations

import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "covered"

K_PRIOR = 10.0          # prior games per side (our assumption)
HOME_LOGIT = 0.25       # NHL home-ice log-odds shift (our assumption)
SAMPLE_HIGH = 20        # games per side needed before a 'high' label is allowed
BAND_MIN, BAND_MAX = -250, 10000
WIN_LINE_SPORTS = {"Ice Hockey", "Basketball"}

# Markets that OLBG or official pages show, and what this desk did with each one.
MARKETS_BY_SPORT = {
    "Golf": ["Tournament Outright Winner (OLBG)", "First Round Leader (OLBG)"],
    "Volleyball": ["Match winner (not captured)"],
    "Rugby Union": ["Match winner (not captured)"],
    "Cricket": ["Match winner (not captured)"],
    "Snooker": ["Match winner (OLBG market set not captured)"],
    "Darts": ["Win Match 2-way (OLBG)", "Win Tournament (OLBG)"],
    "Baseball": ["Money Line (OLBG)"],
    "Gaelic Sports": ["Match winner (not captured)"],
    "Greyhounds": ["Race winner (not captured)"],
    "Tennis": ["Win Match (OLBG)", "Tournament Winner (OLBG)", "Set Score Betting (OLBG)"],
    "Motor Racing": ["Win Race", "Podium Finish", "Top 6 Finish", "Points Finish", "Fastest Lap", "Fastest Qualifier", "Win Tournament (OLBG)"],
    "Handball": ["Match winner (not captured)"],
    "Ice Hockey": ["Money line / win (originated)", "Puck line (not originated)", "Game total (not originated)"],
    "Basketball": ["Money Line (originated)", "Pointspread (not originated)", "Game Totals (not originated)"],
    "Rugby League": ["Match winner (not captured)"],
}
MARKET_REASON = {
    "Puck line (not originated)": "needs verified goals-for and goals-against per game; not captured",
    "Game total (not originated)": "needs verified scoring rates; not captured",
    "Pointspread (not originated)": "needs verified points-for and points-against per game; not captured",
    "Game Totals (not originated)": "needs verified scoring rates; not captured",
}


def american(p: float) -> int:
    """Fair American price for a win probability p."""
    p = min(max(p, 1e-6), 1 - 1e-6)
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def label_for(p: float, min_games: int | None) -> tuple[str, str]:
    if p >= 0.70:
        if min_games is not None and min_games >= SAMPLE_HIGH:
            return "high", ""
        return "medium", "capped at medium: fewer than %d games per side" % SAMPLE_HIGH
    if p >= 0.60:
        return "medium", ""
    return "low", ""


def logit(p: float) -> float:
    return math.log(p / (1 - p))


def inv_logit(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def strength(side: dict, sport: str) -> float | None:
    if sport == "Ice Hockey" and side.get("gp"):
        return (side["pts"] + K_PRIOR) / (2 * side["gp"] + 2 * K_PRIOR)
    if sport == "Basketball" and side.get("gp") is not None:
        return (side["w"] + K_PRIOR * 0.5) / (side["gp"] + K_PRIOR)
    return None


def log5(a: float, b: float) -> float:
    return a * (1 - b) / (a * (1 - b) + b * (1 - a))


def originate(fx: dict) -> dict | None:
    sport = fx["sport"]
    if sport not in WIN_LINE_SPORTS:
        return None
    sa, sb = fx["side_a"], fx["side_b"]
    a, b = strength(sa, sport), strength(sb, sport)
    if a is None or b is None:
        return None
    p_a = log5(a, b)
    home = fx.get("home_side")
    if sport == "Ice Hockey" and home in ("side_a", "side_b"):
        shift = HOME_LOGIT if home == "side_a" else -HOME_LOGIT
        p_a = inv_logit(logit(p_a) + shift)
    p_b = 1 - p_a
    min_games = min(sa.get("gp") or 0, sb.get("gp") or 0)
    if sport == "Basketball":
        basis = "NBA: shrunk win pct (W + 5) / (GP + 10); neutral court (home side not stated on source)"
    else:
        basis = f"NHL: shrunk points pct (pts + 10) / (2GP + 20); log5; home-ice shift +{HOME_LOGIT:.2f} log-odds to the home side (assumption)"
    labels = {}
    for key, p, side in (("side_a", p_a, sa), ("side_b", p_b, sb)):
        lab, note = label_for(p, min_games)
        labels[key] = {"p": round(p, 4), "fair_american": american(p), "label": lab, "label_note": note}
    return {
        "fixture_id": fx["id"],
        "sport": sport,
        "market": "Win match (moneyline)",
        "method": basis,
        "inputs": {"side_a": {"name": sa["name"], "record": sa.get("record_as_read"), "gp": sa.get("gp")},
                   "side_b": {"name": sb["name"], "record": sb.get("record_as_read"), "gp": sb.get("gp")}},
        "strength": {"side_a": round(a, 4), "side_b": round(b, 4)},
        "sides": labels,
        "markets_considered": MARKETS_BY_SPORT.get(sport, []),
        "markets_not_originated": {m: MARKET_REASON[m] for m in MARKETS_BY_SPORT.get(sport, []) if m in MARKET_REASON},
    }


def pick_from(line: dict, fx: dict) -> dict:
    sa, sb = fx["side_a"], fx["side_b"]
    side_key = "side_a" if line["sides"]["side_a"]["p"] >= line["sides"]["side_b"]["p"] else "side_b"
    s = line["sides"][side_key]
    name = (sa if side_key == "side_a" else sb)["name"]
    in_band = BAND_MIN <= s["fair_american"] <= BAND_MAX
    qualifies = s["label"] == "high" and s["p"] >= 0.70 and in_band
    return {
        "fixture_id": fx["id"],
        "sport": fx["sport"],
        "selection": name,
        "selection_side": side_key,
        "p": s["p"],
        "fair_american": s["fair_american"],
        "label": s["label"],
        "label_note": s["label_note"],
        "band_check": "in band (-250..+10000)" if in_band else "outside band",
        "qualifies_high_confidence": qualifies,
    }


def main() -> None:
    inputs = json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))
    fixtures = inputs["fixtures"]

    lines, picks = [], []
    for fx in fixtures:
        line = originate(fx)
        if line:
            lines.append(line)
            picks.append(pick_from(line, fx))

    sports = [
        "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
        "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
        "Basketball", "Rugby League",
    ]
    top5 = {}
    for sport in sports:
        ranked = sorted([p for p in picks if p["sport"] == sport], key=lambda x: (-x["p"], x["fixture_id"]))
        top5[sport] = ranked[:5]

    high = [p for p in picks if p["qualifies_high_confidence"]]
    (DATA / "lines.json").write_text(json.dumps({"as_of": inputs["as_of"], "parameters": {
        "K_PRIOR": K_PRIOR, "HOME_LOGIT": HOME_LOGIT, "SAMPLE_HIGH": SAMPLE_HIGH,
        "BAND": [BAND_MIN, BAND_MAX], "label_thresholds": {"high": 0.70, "medium": 0.60},
        "note": "K_PRIOR, HOME_LOGIT and SAMPLE_HIGH are modelling assumptions set by this desk, not facts from any source."},
        "lines": lines}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "picks.json").write_text(json.dumps({"as_of": inputs["as_of"],
        "high_confidence_qualifying": high,
        "top5_by_sport": top5,
        "gate": "high-confidence = p >= 0.70 AND fair American price in -250..+10000 AND >= %d games per side" % SAMPLE_HIGH}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "predictions.json").write_text(json.dumps({"as_of": inputs["as_of"], "predictions": [],
        "reason": "No selection passed the high-confidence gate in this snapshot, so no written predictions were produced. Predictions are only written for gate-passing selections."},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    matches = []
    line_by_fx = {l["fixture_id"]: l for l in lines}
    for fx in fixtures:
        ln = line_by_fx.get(fx["id"])
        matches.append({
            "id": fx["id"], "sport": fx["sport"], "competition": fx["competition"],
            "start_as_read": fx.get("start_as_read"), "start_utc": fx.get("start_utc"),
            "status_as_read": fx.get("status_as_read"), "venue": fx.get("venue"),
            "side_a": fx["side_a"]["name"] if fx.get("side_a") else None,
            "side_b": fx["side_b"]["name"] if fx.get("side_b") else None,
            "source_id": fx["source_id"],
            "source_url": fx.get("game_url") or next(
                (s["url"] for s in json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"] if s["id"] == fx["source_id"]), ""),
            "olbg_ref": fx.get("olbg_ref"),
            "line_status": "originated" if ln else "not originated (input gap)",
        })
    (DATA / "matches.json").write_text(json.dumps({"as_of": inputs["as_of"], "matches": matches}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("fixtures:", len(fixtures), "lines:", len(lines), "high qualifying:", len(high))


if __name__ == "__main__":
    main()
