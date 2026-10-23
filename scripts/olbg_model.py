#!/usr/bin/env python3
"""Independent, deterministic line origination for the /olbg/ desk.

All factual inputs come from data/olbg/source.json. Formulas are intentionally
simple and public; no OLBG tipster share or bookmaker price enters a calculation.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "olbg"
SOURCE = json.loads((DATA / "source.json").read_text(encoding="utf-8"))


def log5(a: Fraction, b: Fraction) -> Fraction:
    """Probability that A beats B in a two-way comparison."""
    return (a - a * b) / (a + b - 2 * a * b)


def american(p: Fraction) -> int:
    """Fair American price, rounded to the nearest whole unit."""
    if not 0 < p < 1:
        raise ValueError("probability outside (0,1)")
    if p > Fraction(1, 2):
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def confidence(p: Fraction, fair: int, high_detail: bool) -> str:
    # The brief says greater than 70%, so equality is not promoted.
    if high_detail and p > Fraction(70, 100) and -250 <= fair <= 10000:
        return "high"
    if p >= Fraction(60, 100):
        return "medium"
    return "low"


def as_float(p: Fraction) -> float:
    return float(p)


def base_line(event, method, formula, input_summary, away_p, home_p, away_name, home_name):
    if away_p >= home_p:
        selection, p = away_name, away_p
    else:
        selection, p = home_name, home_p
    fair = american(p)
    return {
        "id": event["id"] + "-winner", "event_id": event["id"], "sport": event["sport"],
        "market": "Match winner / two-way moneyline", "line": "", "primary": True,
        "selection": selection, "probability": as_float(p), "fair_american": fair,
        "fair_decimal": as_float(1 / p), "confidence": confidence(p, fair, event["high_detail"]),
        "away_selection": away_name, "home_selection": home_name,
        "away_probability": as_float(away_p), "home_probability": as_float(home_p),
        "method": method, "formula": formula, "inputs": input_summary,
        "market_price": None, "market_price_source": None,
    }


def price_nba(event):
    spec = event["pricing"]
    teams = SOURCE["inputs"]["nba"]["teams"]
    away, home = teams[spec["away"]], teams[spec["home"]]
    away_rate = Fraction(away["road_w"], away["road_w"] + away["road_l"])
    home_rate = Fraction(home["home_w"], home["home_w"] + home["home_l"])
    p = log5(away_rate, home_rate)
    summary = {
        "away": f"{away['name']} 2025-26 road {away['road_w']}–{away['road_l']}",
        "home": f"{home['name']} 2025-26 home {home['home_w']}–{home['home_l']}",
        "sample": "41 venue-split games per team; completed prior season",
    }
    return base_line(event, "NBA venue-split log5", "p(A road beats B home) = (a−ab)/(a+b−2ab), where a and b are the official 2025-26 venue win fractions.", summary, p, 1-p, away["name"], home["name"])


def price_record_log5(event, family):
    spec = event["pricing"]
    teams = SOURCE["inputs"][family]["teams"] if family == "euroleague" else SOURCE["inputs"][family]
    away, home = teams[spec["away"]], teams[spec["home"]]
    if family == "euroleague":
        away_rate = Fraction(away["w"], away["gp"])
        home_rate = Fraction(home["w"], home["gp"])
        away_record = f"{away['w']}–{away['l']} in {away['gp']} games"
        home_record = f"{home['w']}–{home['l']} in {home['gp']} games"
        method = "EuroLeague current-record log5"
    else:
        away_rate = Fraction(away["wins"], away["wins"] + away["losses"])
        home_rate = Fraction(home["wins"], home["wins"] + home["losses"])
        away_record = f"{away['wins']}–{away['losses']}, RS {away['runsScored']} / RA {away['runsAllowed']}"
        home_record = f"{home['wins']}–{home['losses']}, RS {home['runsScored']} / RA {home['runsAllowed']}"
        method = "MLB season-record log5"
    p = log5(away_rate, home_rate)
    line = base_line(event, method, "Two-way log5 from official win fractions; no home or injury adjustment.", {"away": away_record, "home": home_record}, p, 1-p, spec["away"], spec["home"])
    if family == "euroleague":
        # Arithmetic score context, deliberately not converted into a cover or over/under bet.
        expected_away = (Fraction(away["pf"], away["gp"]) + Fraction(home["pa"], home["gp"])) / 2
        expected_home = (Fraction(home["pf"], home["gp"]) + Fraction(away["pa"], away["gp"])) / 2
        line["score_context"] = {
            "expected_away_points": round(float(expected_away), 2),
            "expected_home_points": round(float(expected_home), 2),
            "expected_total": round(float(expected_away + expected_home), 2),
            "expected_home_margin": round(float(expected_home - expected_away), 2),
            "note": "Arithmetic mean of each offense and the opposing defense; analysis only, not a spread or total selection.",
        }
    return line


def price_nhl(event):
    spec = event["pricing"]
    teams = SOURCE["inputs"]["nhl"]["teams"]
    away, home = teams[spec["away"]], teams[spec["home"]]
    away_rate = Fraction(away["points"], 2 * away["gp"])
    home_rate = Fraction(home["points"], 2 * home["gp"])
    p = log5(away_rate, home_rate)
    summary = {
        "away": f"{spec['away']} {away['w']}–{away['l']}–{away['otl']}, {away['points']} points in {away['gp']} games, GF {away['gf']} / GA {away['ga']}",
        "home": f"{spec['home']} {home['w']}–{home['l']}–{home['otl']}, {home['points']} points in {home['gp']} games, GF {home['gf']} / GA {home['ga']}",
        "points_percentage": "points / (2 × games), using exact integers rather than rounded API percentages",
    }
    display_away = "Montréal Canadiens" if spec["away"] == "Montreal Canadiens" else spec["away"]
    return base_line(event, "NHL points-percentage log5", "Two-way log5 from exact current-season points percentages; no home or goalie adjustment.", summary, p, 1-p, display_away, spec["home"])


def price_ranking(event):
    spec = event["pricing"]
    ratings = SOURCE["inputs"][spec["input"]]
    if spec["p1"] not in ratings or spec["p2"] not in ratings:
        return None
    a, b = ratings[spec["p1"]], ratings[spec["p2"]]
    p1 = Fraction(a, a + b)
    p2 = 1 - p1
    label = "ICC ODI rating" if spec["input"] == "icc_odi" else ("PDC world-ranking pounds" if spec["input"] == "pdc_rankings" else "ATP singles ranking points")
    summary = {"p1": f"{spec['p1']}: {a:,} {label}", "p2": f"{spec['p2']}: {b:,} {label}", "capped": "No ranking-only estimate is eligible for high confidence."}
    return base_line(event, "Official ranking-value share", "p(player 1) = rating 1 / (rating 1 + rating 2); complementary two-way price, capped below high.", summary, p1, p2, spec["p1"], spec["p2"])


def poisson_mass(lam: float, max_goals: int = 40):
    values = [math.exp(-lam) * lam ** k / math.factorial(k) for k in range(max_goals + 1)]
    mass = sum(values)
    return [v / mass for v in values]


def nhl_additional_lines(event):
    """Originate the two expired OLBG non-moneyline markets with explicit assumptions."""
    if not event["pricing"].get("derive_markets"):
        return []
    spec = event["pricing"]
    teams = SOURCE["inputs"]["nhl"]["teams"]
    away, home = teams[spec["away"]], teams[spec["home"]]
    away_xg = (away["gf"] / away["gp"] + home["ga"] / home["gp"]) / 2
    home_xg = (home["gf"] / home["gp"] + away["ga"] / away["gp"]) / 2
    pa, ph = poisson_mass(away_xg), poisson_mass(home_xg)
    over = 0.0
    away_by_two = 0.0
    home_by_two = 0.0
    for a, va in enumerate(pa):
        for h, vh in enumerate(ph):
            joint = va * vh
            # A regulation tie is resolved by exactly one OT/shootout goal.
            final_total = 2 * a + 1 if a == h else a + h
            if final_total > 6.5:
                over += joint
            if a - h >= 2:
                away_by_two += joint
            if h - a >= 2:
                home_by_two += joint
    under = 1.0 - over
    total_sel, total_p = ("Over 6.5", over) if over >= under else ("Under 6.5", under)
    # libm can differ in the last bits across Python/platform versions. Normalize
    # only the serialized low-confidence Poisson outputs, not the exact-input gate.
    total_p = round(total_p, 12)
    inputs = {"expected_away_goals": round(away_xg, 4), "expected_home_goals": round(home_xg, 4), "distribution": "Independent Poisson through regulation; a tie adds exactly one goal; each marginal truncated at 40 and normalized."}
    common = {"event_id": event["id"], "sport": event["sport"], "primary": False, "confidence": "low", "market_price": None, "market_price_source": None, "inputs": inputs}
    total = dict(common, id=event["id"]+"-total-6-5", market="Game total", line="6.5", selection=total_sel, probability=total_p, fair_american=american(Fraction(total_p).limit_denominator(10**12)), fair_decimal=round(1/total_p, 12), method="NHL independent-Poisson total", formula=inputs["distribution"], observed_line="6.5 on expired OLBG event page")
    if event["id"] == "nhl-2026020166":
        away_cover, home_cover = away_by_two, 1-away_by_two
        away_text, home_text = "Montréal Canadiens −1.5", "Chicago Blackhawks +1.5"
    else:
        away_cover, home_cover = 1-home_by_two, home_by_two
        away_text, home_text = "Tampa Bay Lightning +1.5", "Colorado Avalanche −1.5"
    puck_sel, puck_p = (away_text, away_cover) if away_cover >= home_cover else (home_text, home_cover)
    puck_p = round(puck_p, 12)
    puck = dict(common, id=event["id"]+"-puck-line", market="Puck line", line="1.5", selection=puck_sel, probability=puck_p, fair_american=american(Fraction(puck_p).limit_denominator(10**12)), fair_decimal=round(1/puck_p, 12), method="NHL independent-Poisson puck line", formula=inputs["distribution"] + " A one-goal or tied-regulation decision does not cover −1.5.", observed_line="1.5 on expired OLBG event page")
    return [total, puck]


def collect_sources(events, flags):
    unique = {}
    for s in events:
        for item in s["official_sources"]:
            unique[(item["kind"], item["url"], item["label"])] = item
    for f in flags:
        for item in f["links"]:
            unique[(item["kind"], item["url"], item["label"])] = item
    for d in SOURCE["discovery"]:
        item = source = {"label": f"OLBG {d['sport']} hub", "url": d["url"], "captured": d["checked"], "note": d["result"], "kind": "olbg"}
        unique[(item["kind"], item["url"], item["label"])] = item
    return sorted(unique.values(), key=lambda s: (s["kind"], s["label"], s["url"]))


def main():
    matches, lines = [], []
    for original in SOURCE["events"]:
        event = dict(original)
        spec = event.get("pricing")
        line = None
        if spec:
            if spec["method"] == "nba_split_log5":
                line = price_nba(event)
            elif spec["method"] == "euroleague_log5":
                line = price_record_log5(event, "euroleague")
            elif spec["method"] == "mlb_log5":
                line = price_record_log5(event, "mlb")
            elif spec["method"] == "nhl_points_log5":
                line = price_nhl(event)
            elif spec["method"] == "ranking_share":
                line = price_ranking(event)
            else:
                raise ValueError(spec["method"])
        if line:
            lines.append(line)
            event["primary_line_id"] = line["id"]
            event["selection"] = line["selection"]
            event["probability"] = line["probability"]
            event["fair_american"] = line["fair_american"]
            event["confidence"] = line["confidence"]
            event["line"] = line
            extras = nhl_additional_lines(event) if spec["method"] == "nhl_points_log5" else []
            lines.extend(extras)
            event["additional_line_ids"] = [x["id"] for x in extras]
        else:
            event.update({"primary_line_id": None, "selection": None, "probability": None, "fair_american": None, "confidence": None, "line": None, "additional_line_ids": []})
        matches.append(event)

    by_sport = defaultdict(list)
    for line in lines:
        if line["primary"]:
            by_sport[line["sport"]].append(line)
    rank = {"high": 3, "medium": 2, "low": 1}
    shortlists = {}
    for sport in SOURCE["sports"]:
        slug = sport["slug"]
        chosen = sorted(by_sport[slug], key=lambda x: (-rank[x["confidence"]], -x["probability"], x["event_id"]))[:5]
        shortlists[slug] = {"count": len(chosen), "target": 5, "shortfall": 5-len(chosen), "lines": chosen}

    sources = collect_sources(matches, SOURCE["flags"])
    counts = {
        "events": len(matches), "sports": 15, "sports_with_rows": len({e["sport"] for e in matches}),
        "active": sum(e["provenance"] == "active" for e in matches),
        "last_seen": sum(e["provenance"] == "last_seen" for e in matches),
        "official_context": sum(e["provenance"] == "official_context" for e in matches),
        "priced_matches": sum(bool(e["line"]) for e in matches), "blank_matches": sum(not e["line"] for e in matches),
        "originated_markets": len(lines), "high": sum(x["confidence"] == "high" and x["primary"] for x in lines),
        "medium": sum(x["confidence"] == "medium" and x["primary"] for x in lines),
        "low": sum(x["confidence"] == "low" and x["primary"] for x in lines),
        "sources": len(sources), "manual_flags": len(SOURCE["flags"]),
    }
    (DATA / "matches.json").write_text(json.dumps({"research_cutoff": SOURCE["research_cutoff"], "matches": matches}, indent=2, ensure_ascii=False)+"\n")
    (DATA / "lines.json").write_text(json.dumps({"research_cutoff": SOURCE["research_cutoff"], "lines": lines}, indent=2, ensure_ascii=False)+"\n")
    (DATA / "picks.json").write_text(json.dumps({"research_cutoff": SOURCE["research_cutoff"], "shortlists": shortlists}, indent=2, ensure_ascii=False)+"\n")
    (DATA / "sources.json").write_text(json.dumps({"research_cutoff": SOURCE["research_cutoff"], "sources": sources}, indent=2, ensure_ascii=False)+"\n")
    (DATA / "summary.json").write_text(json.dumps({"research_cutoff": SOURCE["research_cutoff"], "counts": counts}, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(counts, indent=2))
    for line in lines:
        if line["confidence"] == "high":
            print("HIGH", line["event_id"], line["selection"], f"{line['probability']:.6%}", line["fair_american"])


if __name__ == "__main__":
    main()
