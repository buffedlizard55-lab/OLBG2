#!/usr/bin/env python3
"""Executive desk — originate our own fair lines and grade one pick per fixture.

Rules (documented in executive/methodology.html):
  * Fair prices are *model-derived*, computed from the numeric strength inputs captured in
    data/executive/fixtures.json. They are not bookmaker quotes and are not calibrated to
    observed closing prices.
  * Two-way markets:  p(home) = sigmoid(K*(s_home - s_away) + home_edge), K = 3.0,
    home_edge = 0.15. The selection is the higher-probability side.
  * Outright markets: the selection is the named player; p = the captured outright
    probability where one exists, otherwise clamp(s_player, 0.15, 0.70).
  * Confidence: high if p >= 0.70, medium if p >= 0.60, otherwise low. A pick whose only
    strength input is an unverified default is forced to "low" so an unmodelled fixture can
    never masquerade as a conviction call.
  * The brief's price window is -250 .. +10000 (decimal 1.40 .. 101.00). A pick is
    "in band" when its fair American price falls inside that window. The priority list is
    the verified-input picks that are both in band and medium/high confidence.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "executive"
K = 3.0
HOME_EDGE = 0.15
BAND_MIN = -250
BAND_MAX = 10000


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + pow(2.718281828459045, -x))


def american(p: float) -> int:
    p = min(max(p, 0.0001), 0.9999)
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def decimal(p: float) -> float:
    return round(1.0 / min(max(p, 0.0001), 0.9999), 3)


def confidence(p: float, verified: bool = True) -> str:
    if not verified:
        return "low"
    if p >= 0.70:
        return "high"
    if p >= 0.60:
        return "medium"
    return "low"


def main() -> None:
    fixtures = json.loads((OUT / "fixtures.json").read_text())["fixtures"]
    lines: list[dict[str, Any]] = []
    picks: list[dict[str, Any]] = []
    for fx in fixtures:
        s_home = float(fx["home_strength"])
        s_away = float(fx["away_strength"])
        market = fx["market"]
        input_verified = "unverified" not in str(fx["home_strength_basis"]).lower()
        if "outright" in market:
            # Selection is the named player; p is a clamped estimate of an outright win.
            if "outright_probability" in fx:
                p_home = min(max(float(fx["outright_probability"]), 0.10), 0.72)
            else:
                p_home = min(max(s_home, 0.15), 0.70)
            p_sel, selection, sel_side = p_home, fx["home"], "home"
        else:
            p_home = sigmoid(K * (s_home - s_away) + HOME_EDGE)
            if p_home >= 0.5:
                p_sel, selection, sel_side = p_home, fx["home"], "home"
            else:
                p_sel, selection, sel_side = 1.0 - p_home, fx["away"], "away"
        p_away = 1.0 - p_home
        od = american(p_sel)
        in_band = BAND_MIN <= od <= BAND_MAX
        conf = confidence(p_sel, input_verified)
        lines.append({
            "fixture_id": fx["id"], "sport": fx["sport"], "competition": fx["competition"],
            "market": market,
            "home": fx["home"], "away": fx["away"],
            "home_strength": s_home, "away_strength": s_away,
            "home_strength_basis": fx["home_strength_basis"],
            "away_strength_basis": fx["away_strength_basis"],
            "input_verified": input_verified,
            "home_probability": round(p_home, 6), "away_probability": round(p_away, 6),
            "home_fair_odds": american(p_home), "away_fair_odds": american(p_away),
            "home_fair_decimal": decimal(p_home), "away_fair_decimal": decimal(p_away),
            "fair_probability": round(p_sel, 6),
            "fair_odds": od, "fair_decimal": decimal(p_sel),
            "confidence": conf,
            "selection": selection, "selection_side": sel_side,
        })
        picks.append({
            "fixture_id": fx["id"], "sport": fx["sport"], "competition": fx["competition"],
            "date": fx["date"], "start_utc": fx["start_utc"], "venue": fx["venue"],
            "match": f"{fx['home']} v {fx['away']}",
            "home": fx["home"], "away": fx["away"],
            "market": market, "selection": selection, "selection_side": sel_side,
            "fair_probability": round(p_sel, 6), "fair_odds": od, "fair_decimal": decimal(p_sel),
            "confidence": conf, "in_band": in_band, "input_verified": input_verified,
            "key_facts": fx["facts"],
            "source_keys": fx["source_keys"],
        })
    (OUT / "lines.json").write_text(json.dumps({"lines": lines}, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8")
    (OUT / "picks.json").write_text(json.dumps({"picks": picks}, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8")
    focus = [p for p in picks if p["in_band"] and p["confidence"] in ("high", "medium")
             and p["input_verified"]]
    print(f"fixtures={len(fixtures)} lines={len(lines)} picks={len(picks)}")
    print(f"high={sum(p['confidence']=='high' for p in picks)} "
          f"medium={sum(p['confidence']=='medium' for p in picks)} "
          f"low={sum(p['confidence']=='low' for p in picks)}")
    print(f"in_band={sum(p['in_band'] for p in picks)} focus(verified+in_band+med/high)={len(focus)}")


if __name__ == "__main__":
    main()
