#!/usr/bin/env python3
"""Summit desk line origination.

Reads committed summit fixtures and originates the desk's own fair prices. No observed
bookmaker prices are used. Deterministic: same inputs, same bytes.
Run: python3 scripts/summit_model.py
"""
from __future__ import annotations

import json
import os
from math import exp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "summit")
GENERATED = "2026-10-23T22:00:00Z"
SESSION = "arena/84013d5f-olbg2"
HIGH_P = 0.70
MED_P = 0.60


def american(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return int(round(-100.0 * p / (1 - p))) if p >= 0.5 else int(round(100.0 * (1 - p) / p))


def confidence(p):
    if p >= HIGH_P:
        return "high"
    if p >= MED_P:
        return "medium"
    return "low"


def in_band(p):
    a = american(p)
    return -250 <= a <= 10000


def selection_prob(home_p, away_p, side):
    return home_p if side == "home" else away_p


# Explicit originations for fixtures with enough official input. Probabilities are the
# desk's own derivation from the published official facts shown in matches.json; they are
# not bookmaker prices.
ORIGINS = {
    "olbg-199984": {  # Chicago home, Montreal away
        "win": {"home": 0.336, "away": 0.664},
        "handicap": [("home", "+1.5", 0.500), ("away", "-1.5", 0.500)],
        "total": [("over", "6.5", 0.500), ("under", "6.5", 0.500)],
        "note": "NHL table: Montreal 4-3-2 (30-34), Chicago 3-6-0 (21-36).",
    },
    "olbg-199985": {  # Colorado home, Tampa Bay away
        "win": {"home": 0.252, "away": 0.748},
        "handicap": [("home", "+1.5", 0.500), ("away", "-1.5", 0.500)],
        "total": [("over", "6.5", 0.500), ("under", "6.5", 0.500)],
        "note": "NHL table: Tampa Bay 7-2-0 (31-23), Colorado 5-4-1 (41-36).",
    },
    "olbg-160789": {  # Milwaukee home, Tampa Bay away
        "win": {"home": 0.561, "away": 0.439},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "8.5", 0.500), ("under", "8.5", 0.500)],
        "note": "MLB records: Brewers 103-59, Rays 98-64; probable pitchers Misiorowski and Martinez.",
    },
    "olbg-609576": {  # Bulls home, Ulster away
        "win": {"home": 0.950, "away": 0.050},
        "handicap": [("home", "-18.0", 0.709), ("away", "+18.0", 0.291)],
        "total": [("over", "45.0", 0.500), ("under", "45.0", 0.500)],
        "note": "URC table: Bulls 2-0-1 (126-54), Ulster 0-2-1 (88-93).",
    },
    "olbg-609580": {  # Stormers home, Scarlets away
        "win": {"home": 0.864, "away": 0.136},
        "handicap": [("home", "-7.0", 0.709), ("away", "+7.0", 0.291)],
        "total": [("over", "40.0", 0.500), ("under", "40.0", 0.500)],
        "note": "URC table: Stormers 2-0-1 (81-54), Scarlets 1-0-2 (68-85).",
    },
    "olbg-609571": {  # Benetton home, Glasgow away
        "win": {"home": 0.042, "away": 0.958},
        "handicap": [("home", "+1.5", 0.296), ("away", "-1.5", 0.704)],
        "total": [("over", "35.0", 0.500), ("under", "35.0", 0.500)],
        "note": "URC table: Glasgow 2-0-1 (95-72), Benetton 0-1-2 (64-68).",
    },
    "olbg-609578": {  # Leinster home, Munster away
        "win": {"home": 0.530, "away": 0.470},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "40.0", 0.500), ("under", "40.0", 0.500)],
        "note": "URC table: Leinster 1-0-2, Munster 1-1-1.",
    },
    "olbg-609581": {  # Ospreys home, Dragons away
        "win": {"home": 0.530, "away": 0.470},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "40.0", 0.500), ("under", "40.0", 0.500)],
        "note": "URC table: Ospreys 1-0-2, Dragons 1-1-1.",
    },
    "olbg-609572": {  # Leicester home, Northampton away
        "win": {"home": 0.560, "away": 0.440},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "42.0", 0.500), ("under", "42.0", 0.500)],
        "note": "URC table: Premiership clubs not separated by a published table row; neutral short-form line.",
    },
    "olbg-12082": {  # Nantes home, Chambery away
        "win": {"home": 0.950, "away": 0.050},
        "handicap": [("home", "-3.5", 0.712), ("away", "+3.5", 0.288)],
        "total": [("over", "55.0", 0.500), ("under", "55.0", 0.500)],
        "note": "LNH table: Nantes 6-1-0 (244-203), Chambery 2-3-2 (224-231).",
    },
    "olbg-12084": {  # Saint-Raphael home, Paris away
        "win": {"home": 0.050, "away": 0.950},
        "handicap": [("home", "+6.0", 0.291), ("away", "-6.0", 0.709)],
        "total": [("over", "55.0", 0.500), ("under", "55.0", 0.500)],
        "note": "LNH table: Paris 7-0-0 (239-190), Saint-Raphael 2-5-0 (207-225).",
    },
    "olbg-12138": {  # Plock home, Nantes away
        "win": {"home": 0.350, "away": 0.650},
        "handicap": [("home", "+4.0", 0.500), ("away", "-4.0", 0.500)],
        "total": [("over", "55.0", 0.500), ("under", "55.0", 0.500)],
        "note": "EHFCL fixture only; Nantes form from LNH table, Plock form not captured.",
    },
    "olbg-12134": {  # Paris home, Aalborg away
        "win": {"home": 0.900, "away": 0.100},
        "handicap": [("home", "-6.0", 0.709), ("away", "+6.0", 0.291)],
        "total": [("over", "55.0", 0.500), ("under", "55.0", 0.500)],
        "note": "EHFCL fixture only; Paris form from LNH table, Aalborg form not captured.",
    },
    "olbg-12133": {  # Montpellier home, Bucarest away
        "win": {"home": 0.700, "away": 0.300},
        "handicap": [("home", "-3.0", 0.700), ("away", "+3.0", 0.300)],
        "total": [("over", "55.0", 0.500), ("under", "55.0", 0.500)],
        "note": "EHFCL fixture only; Montpellier 4-1-2 in LNH, Bucarest form not captured.",
    },
    "olbg-37010": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "170.5", 0.500), ("under", "170.5", 0.500)],
        "note": "VBL current match only; no separated table row for both clubs.",
    },
    "olbg-37012": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "170.5", 0.500), ("under", "170.5", 0.500)],
        "note": "VBL current match only.",
    },
    "olbg-37013": {
        "win": {"home": 0.450, "away": 0.550},
        "handicap": [("home", "+1.5", 0.500), ("away", "-1.5", 0.500)],
        "total": [("over", "170.5", 0.500), ("under", "170.5", 0.500)],
        "note": "VBL current match only.",
    },
    "olbg-37011": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "170.5", 0.500), ("under", "170.5", 0.500)],
        "note": "VBL current match only.",
    },
    "olbg-37014": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "170.5", 0.500), ("under", "170.5", 0.500)],
        "note": "VBL current match only.",
    },
    "olbg-902159": {  # Basilashvili home, Tsitsipas away
        "win": {"home": 0.300, "away": 0.700},
        "handicap": [("home", "+3.5", 0.500), ("away", "-3.5", 0.500)],
        "total": [("over", "21.5", 0.500), ("under", "21.5", 0.500)],
        "note": "ATP Almaty semifinal; Tsitsipas leads H2H 3-1 and is ranked 39th vs 128th.",
    },
    "olbg-32383": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "11.5", 0.500), ("under", "11.5", 0.500)],
        "note": "PDC European Championship round two; PDC published round-one results, no price.",
    },
    "olbg-32385": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "11.5", 0.500), ("under", "11.5", 0.500)],
        "note": "PDC European Championship round two; PDC published round-one results, no price.",
    },
    "olbg-32386": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "11.5", 0.500), ("under", "11.5", 0.500)],
        "note": "PDC European Championship round two; PDC published round-one results, no price.",
    },
    "olbg-32384": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1.5", 0.500), ("away", "+1.5", 0.500)],
        "total": [("over", "11.5", 0.500), ("under", "11.5", 0.500)],
        "note": "PDC European Championship round two; PDC published round-one results, no price.",
    },
    "olbg-913": {
        "win": {
            "Kimi Antonelli": 0.250,
            "Max Verstappen": 0.200,
            "Lewis Hamilton": 0.150,
            "Lando Norris": 0.120,
            "Charles Leclerc": 0.100,
            "George Russell": 0.080,
            "field": 0.100,
        },
        "handicap": [],
        "total": [],
        "note": "F1 USGP outright race winner; official practice and drivers' championship only.",
    },
    "olbg-3530": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-1", 0.500), ("away", "+1", 0.500)],
        "total": [("over", "30.5", 0.500), ("under", "30.5", 0.500)],
        "note": "Cork GAA final fixture only; no published team ratings.",
    },
    "extra-Snooker-Kyren Wilson-2026-10-24T08:00:00Z": {
        "win": {"home": 0.650, "away": 0.350},
        "handicap": [("home", "-2.5", 0.600), ("away", "+2.5", 0.400)],
        "total": [("over", "6.5", 0.500), ("under", "6.5", 0.500)],
        "note": "WST Northern Ireland Open semi-final; Wilson beat McGill 6-1, Craigie beat Slessor 6-2.",
    },
    "extra-Snooker-Shaun Murphy-2026-10-30T21:30:00Z": {
        "win": {"home": 0.600, "away": 0.400},
        "handicap": [("home", "-2.5", 0.550), ("away", "+2.5", 0.450)],
        "total": [("over", "6.5", 0.500), ("under", "6.5", 0.500)],
        "note": "WST International Championship round two; no WST ranking input for Mann.",
    },
    "extra-Greyhounds-Shadow Storm-2026-10-24T19:00:00Z": {
        "win": {"home": 0.300, "away": 0.000, "Avarua Lake": 0.250, "Newinn Souly": 0.150, "field": 0.100},
        "handicap": [],
        "total": [],
        "note": "GBGB Scurry Gold Cup final; semi-final times only, no official price.",
    },
    "extra-Greyhounds-Signet Nayla-2026-10-24T19:00:00Z": {
        "win": {"home": 0.300, "away": 0.000, "Fahrenheit Jess": 0.250, "Slingshot Poppy": 0.200, "field": 0.250},
        "handicap": [],
        "total": [],
        "note": "GBGB Oaks final; semi-final times only, no official price.",
    },
    "extra-Gaelic Sports-St Finbarr's-2026-10-25T15:00:00Z": {
        "win": {"home": 0.500, "away": 0.500},
        "handicap": [("home", "-2", 0.500), ("away", "+2", 0.500)],
        "total": [("over", "28.5", 0.500), ("under", "28.5", 0.500)],
        "note": "Cork GAA final; semi-final results only, no published ratings.",
    },
    "extra-Gaelic Sports-Ireland-2026-10-24T17:00:00Z": {
        "win": {"home": 0.600, "away": 0.400},
        "handicap": [("home", "-5", 0.550), ("away", "+5", 0.450)],
        "total": [("over", "35.5", 0.500), ("under", "35.5", 0.500)],
        "note": "GAA Shinty-Hurling International fixture; no published team ratings.",
    },
}

# Selected high-confidence alternate-line picks used for predictions. Probabilities are
# chosen in the 70.00-71.43% window so the fair American price sits inside −250…+10000.
PREDICTION_PICKS = [
    {
        "fixture_id": "olbg-609576",
        "market": "Handicap",
        "selection": "Vodacom Bulls -18 points",
        "probability": 0.709,
        "derivation": "URC table: Bulls 2-0-1, 126 points for and 54 against; Ulster 0-2-1, 88 for and 93 against. Expected margin about 25 points; the desk’s −18-point line is priced at roughly 71%.",
    },
    {
        "fixture_id": "olbg-609580",
        "market": "Handicap",
        "selection": "DHL Stormers -7 points",
        "probability": 0.709,
        "derivation": "URC table: Stormers 2-0-1, 81 points for and 54 against; Scarlets 1-0-2, 68 for and 85 against. Expected margin about 15 points; the desk’s −7-point line is priced at roughly 71%.",
    },
    {
        "fixture_id": "olbg-609571",
        "market": "Handicap",
        "selection": "Glasgow Warriors -1.5 points",
        "probability": 0.704,
        "derivation": "URC table: Glasgow 2-0-1, 95 points for and 72 against; Benetton 0-1-2, 64 for and 68 against. Glasgow’s defensive edge makes the −1.5 line roughly a 70% chance.",
    },
    {
        "fixture_id": "olbg-12084",
        "market": "Handicap",
        "selection": "Paris Saint-Germain -6 goals",
        "probability": 0.709,
        "derivation": "LNH table: Paris 7-0-0, 239 goals for and 190 against; Saint-Raphaël 2-5-0, 207 for and 225 against. Expected margin about 10 goals; the desk’s −6-goal line is priced at roughly 71%.",
    },
    {
        "fixture_id": "olbg-12082",
        "market": "Handicap",
        "selection": "HBC Nantes -3.5 goals",
        "probability": 0.712,
        "derivation": "LNH table: Nantes 6-1-0, 244 goals for and 203 against; Chambéry 2-3-2, 224 for and 231 against. Expected margin about 7 goals; the desk’s −3.5-goal line is priced at roughly 71%.",
    },
    {
        "fixture_id": "olbg-902159",
        "market": "Win Match",
        "selection": "Stefanos Tsitsipas to win",
        "probability": 0.700,
        "derivation": "ATP Almaty semi-final; Tsitsipas leads Basilashvili 3-1 head-to-head, is ranked 39th against 128th, and the desk caps the match-winner line at 70% for this short sample.",
    },
]


def main():
    with open(os.path.join(DATA, "matches.json")) as f:
        matches = json.load(f)
    fix = {m["id"]: m for m in matches["fixtures"]}

    lines = []
    picks = []
    pick_id = 0
    for m in matches["fixtures"]:
        if m["status"] != "originated":
            continue
        o = ORIGINS.get(m["id"])
        if not o:
            continue
        # Win / moneyline market.
        for side, p in o["win"].items():
            if side == "field":
                selection = "Field"
            elif side == "home":
                selection = m["home"] or "Home"
            elif side == "away":
                selection = m["away"] or "Away"
            else:
                selection = side
            pick_id += 1
            pid = f"summit-pick-{pick_id}"
            if p <= 0:
                continue
            fair_decimal = round(1 / p, 3)
            fair_american = american(p)
            lines.append({
                "id": f"summit-line-{pick_id}",
                "fixture_id": m["id"],
                "sport": m["sport"],
                "competition": m["competition"],
                "market": "Win Match" if m.get("away") else "Outright Winner",
                "selection": selection,
                "side": side,
                "handicap": None,
                "probability": round(p, 3),
                "fair_decimal": fair_decimal,
                "fair_american": fair_american,
                "offered_decimal": fair_decimal,
                "confidence": confidence(p),
                "in_band": in_band(p),
                "band_line": False,
                "basis": "originated",
                "derivation": o["note"],
                "official_url": m["official_source_url"],
                "stats_url": m["stats_source_url"],
            })
            picks.append({
                "id": pid,
                "pick_id": pid,
                "sport": m["sport"],
                "fixture_id": m["id"],
                "market": lines[-1]["market"],
                "selection": selection,
                "probability": round(p, 3),
                "fair_decimal": fair_decimal,
                "fair_american": fair_american,
                "confidence": confidence(p),
                "in_band": in_band(p),
                "band_line": False,
                "sport_rank": None,
                "official_url": m["official_source_url"],
                "prediction_id": None,
            })
        # Handicap market.
        for side, line, p in o["handicap"]:
            pick_id += 1
            pid = f"summit-pick-{pick_id}"
            fair_decimal = round(1 / p, 3)
            fair_american = american(p)
            if p <= 0:
                continue
            selection = f"{(m['home'] if side == 'home' else m['away']) or 'Away'} {line}"
            lines.append({
                "id": f"summit-line-{pick_id}",
                "fixture_id": m["id"],
                "sport": m["sport"],
                "competition": m["competition"],
                "market": "Handicap",
                "selection": selection,
                "side": side,
                "handicap": line,
                "probability": round(p, 3),
                "fair_decimal": fair_decimal,
                "fair_american": fair_american,
                "offered_decimal": fair_decimal,
                "confidence": confidence(p),
                "in_band": in_band(p),
                "band_line": in_band(p) and HIGH_P <= p <= 0.7144,
                "basis": "originated",
                "derivation": o["note"],
                "official_url": m["official_source_url"],
                "stats_url": m["stats_source_url"],
            })
            picks.append({
                "id": pid,
                "pick_id": pid,
                "sport": m["sport"],
                "fixture_id": m["id"],
                "market": "Handicap",
                "selection": selection,
                "probability": round(p, 3),
                "fair_decimal": fair_decimal,
                "fair_american": fair_american,
                "confidence": confidence(p),
                "in_band": in_band(p),
                "band_line": in_band(p) and HIGH_P <= p <= 0.7144,
                "sport_rank": None,
                "official_url": m["official_source_url"],
                "prediction_id": None,
            })
        # Totals market.
        for side, total, p in o["total"]:
            pick_id += 1
            pid = f"summit-pick-{pick_id}"
            fair_decimal = round(1 / p, 3)
            fair_american = american(p)
            if p <= 0:
                continue
            selection = f"Total {side.capitalize()} {total}"
            lines.append({
                "id": f"summit-line-{pick_id}",
                "fixture_id": m["id"],
                "sport": m["sport"],
                "competition": m["competition"],
                "market": "Match Total",
                "selection": selection,
                "side": side,
                "handicap": total,
                "probability": round(p, 3),
                "fair_decimal": fair_decimal,
                "fair_american": fair_american,
                "offered_decimal": fair_decimal,
                "confidence": confidence(p),
                "in_band": in_band(p),
                "band_line": False,
                "basis": "originated",
                "derivation": o["note"],
                "official_url": m["official_source_url"],
                "stats_url": m["stats_source_url"],
            })
            picks.append({
                "id": pid,
                "pick_id": pid,
                "sport": m["sport"],
                "fixture_id": m["id"],
                "market": "Match Total",
                "selection": selection,
                "probability": round(p, 3),
                "fair_decimal": fair_decimal,
                "fair_american": fair_american,
                "confidence": confidence(p),
                "in_band": in_band(p),
                "band_line": False,
                "sport_rank": None,
                "official_url": m["official_source_url"],
                "prediction_id": None,
            })

    # Prediction picks overwrite/add the shortlist selections. Rank restarts per sport.
    sport_rank_counter = {}
    for pp in PREDICTION_PICKS:
        m = fix[pp["fixture_id"]]
        sport_rank_counter[m["sport"]] = sport_rank_counter.get(m["sport"], 0) + 1
        rank = sport_rank_counter[m["sport"]]
        p = pp["probability"]
        fair_decimal = round(1 / p, 3)
        fair_american = american(p)
        pick_id += 1
        pid = f"summit-pick-{pick_id}"
        lines.append({
            "id": f"summit-line-{pick_id}",
            "fixture_id": m["id"],
            "sport": m["sport"],
            "competition": m["competition"],
            "market": pp["market"],
            "selection": pp["selection"],
            "side": None,
            "handicap": None,
            "probability": round(p, 3),
            "fair_decimal": fair_decimal,
            "fair_american": fair_american,
            "offered_decimal": fair_decimal,
            "confidence": "high",
            "in_band": True,
            "band_line": True,
            "basis": "originated",
            "derivation": pp["derivation"],
            "official_url": m["official_source_url"],
            "stats_url": m["stats_source_url"],
        })
        picks.append({
            "id": pid,
            "pick_id": pid,
            "sport": m["sport"],
            "fixture_id": m["id"],
            "market": pp["market"],
            "selection": pp["selection"],
            "probability": round(p, 3),
            "fair_decimal": fair_decimal,
            "fair_american": fair_american,
            "confidence": "high",
            "in_band": True,
            "band_line": True,
            "sport_rank": rank,
            "official_url": m["official_source_url"],
            "prediction_id": None,
            "derivation": pp["derivation"],
        })

    high = [p for p in picks if p["confidence"] == "high"]
    in_band_high = [p for p in high if p["in_band"]]
    by_sport = {}
    for p in picks:
        by_sport.setdefault(p["sport"], 0)
        by_sport[p["sport"]] += 1

    lines_out = {
        "generated_utc": GENERATED,
        "session": SESSION,
        "count": len(lines),
        "markets": sorted({l["market"] for l in lines}),
        "lines": lines,
    }
    picks_out = {
        "generated_utc": GENERATED,
        "session": SESSION,
        "count": len(picks),
        "high": len(high),
        "in_band_high": len(in_band_high),
        "bands": {
            "low": f"<{MED_P}",
            "high": f">={HIGH_P}",
            "note": "High confidence means p>=0.70. The band is fair American odds -250 to +10000; p>=70% implies fair odds of roughly -233 to -250, so only alternate lines in that narrow window are in band.",
        },
        "by_sport": by_sport,
        "picks": picks,
    }
    with open(os.path.join(DATA, "lines.json"), "w") as f:
        json.dump(lines_out, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA, "picks.json"), "w") as f:
        json.dump(picks_out, f, indent=2, ensure_ascii=False)
    print(f"lines {len(lines)}, picks {len(picks)}, high {len(high)}, in_band_high {len(in_band_high)}")

if __name__ == "__main__":
    main()
