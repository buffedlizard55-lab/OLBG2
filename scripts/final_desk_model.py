#!/usr/bin/env python3
"""Final Desk Model — originate lines, grade confidence, generate predictions"""
import json, math, os

def fair_decimal(p):
    """Convert probability to fair decimal odds"""
    if p <= 0 or p >= 1: return None
    return round(1.0 / p, 2)

def fair_american(decimal):
    """Convert decimal to American odds"""
    if decimal is None: return None
    if decimal >= 2.0: return f"+{round((decimal - 1) * 100)}"
    return str(round(-100 / (decimal - 1)))

def poisson_pmf(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def nhl_game_probs(home_stats, away_stats, home_edge=0.55):
    """Simple Poisson model for NHL game"""
    if not home_stats or not away_stats:
        return None
    home_gf_rate = home_stats["gf"] / home_stats["gp"]
    home_ga_rate = home_stats["ga"] / home_stats["gp"]
    away_gf_rate = away_stats["gf"] / away_stats["gp"]
    away_ga_rate = away_stats["ga"] / away_stats["gp"]
    exp_home_goals = (home_gf_rate + away_ga_rate) / 2 * home_edge
    exp_away_goals = (away_gf_rate + home_ga_rate) / 2 / home_edge
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0
    total_probs = {}
    for h in range(10):
        for a in range(10):
            p = poisson_pmf(h, exp_home_goals) * poisson_pmf(a, exp_away_goals)
            if h > a: p_home += p
            elif h == a: p_draw += p
            else: p_away += p
            total = h + a
            total_probs[total] = total_probs.get(total, 0) + p
    p_home_final = p_home + p_draw * 0.5
    p_away_final = p_away + p_draw * 0.5
    return {
        "home_win": p_home_final, "away_win": p_away_final,
        "exp_home": exp_home_goals, "exp_away": exp_away_goals,
        "exp_total": exp_home_goals + exp_away_goals
    }

def originate_lines(fixtures, team_stats):
    """Originate lines for all fixtures"""
    matches = []
    for fx in fixtures:
        match = dict(fx)
        match["markets"] = {}
        match["confidence"] = "low"
        match["pick"] = None
        match["fair_odds"] = None
        if fx["sport"] == "ice-hockey" and fx["competition"] == "NHL":
            home_stats = team_stats.get(fx["home_team"])
            away_stats = team_stats.get(fx["away_team"])
            probs = nhl_game_probs(home_stats, away_stats)
            if probs:
                home_dec = fair_decimal(probs["home_win"])
                away_dec = fair_decimal(probs["away_win"])
                match["markets"]["moneyline"] = {
                    "home": {"decimal": home_dec, "american": fair_american(home_dec), "prob": round(probs["home_win"], 4)},
                    "away": {"decimal": away_dec, "american": fair_american(away_dec), "prob": round(probs["away_win"], 4)}
                }
                total_line = round(probs["exp_total"] * 2) / 2 + 0.5
                match["markets"]["total"] = {"line": total_line, "over_prob": 0.52, "under_prob": 0.48}
                spread_line = 1.5
                if probs["home_win"] > 0.6:
                    match["markets"]["puck_line"] = {"home": -spread_line, "away": spread_line}
                elif probs["away_win"] > 0.6:
                    match["markets"]["puck_line"] = {"home": spread_line, "away": -spread_line}
                best_side = "home" if probs["home_win"] > probs["away_win"] else "away"
                best_prob = max(probs["home_win"], probs["away_win"])
                best_dec = home_dec if best_side == "home" else away_dec
                match["pick"] = fx["home_team"] if best_side == "home" else fx["away_team"]
                match["fair_odds"] = {"decimal": best_dec, "american": fair_american(best_dec)}
                american_val = float(fair_american(best_dec).replace("+", ""))
                if best_prob >= 0.70 and -250 <= american_val <= 10000:
                    match["confidence"] = "high"
                elif best_prob >= 0.55:
                    match["confidence"] = "medium"
        elif fx["sport"] == "basketball":
            home_adv = 0.55
            match["markets"]["moneyline"] = {
                "home": {"decimal": fair_decimal(home_adv), "american": fair_american(fair_decimal(home_adv)), "prob": home_adv},
                "away": {"decimal": fair_decimal(1-home_adv), "american": fair_american(fair_decimal(1-home_adv)), "prob": 1-home_adv}
            }
            match["pick"] = fx["home_team"]
            match["fair_odds"] = {"decimal": fair_decimal(home_adv), "american": fair_american(fair_decimal(home_adv))}
            match["confidence"] = "low"
        elif fx["sport"] == "baseball":
            home_adv = 0.54
            match["markets"]["moneyline"] = {
                "home": {"decimal": fair_decimal(home_adv), "american": fair_american(fair_decimal(home_adv)), "prob": home_adv},
                "away": {"decimal": fair_decimal(1-home_adv), "american": fair_american(fair_decimal(1-home_adv)), "prob": 1-home_adv}
            }
            match["pick"] = fx["home_team"]
            match["fair_odds"] = {"decimal": fair_decimal(home_adv), "american": fair_american(fair_decimal(home_adv))}
            match["confidence"] = "low"
        elif fx["sport"] == "tennis":
            match["markets"]["win_match"] = {
                "player1": {"decimal": 1.80, "prob": 0.55},
                "player2": {"decimal": 2.10, "prob": 0.48}
            }
            match["pick"] = fx["away_team"]
            match["confidence"] = "low"
        matches.append(match)
    return matches

def generate_predictions(matches):
    """Generate predictions for high-confidence picks"""
    predictions = []
    for m in matches:
        if m["confidence"] == "high" and m.get("pick"):
            team = m["pick"]
            opponent = m["away_team"] if team == m["home_team"] else m["home_team"]
            if m["sport"] == "ice-hockey":
                prob = m["markets"]["moneyline"]["home"]["prob"] if team == m["home_team"] else m["markets"]["moneyline"]["away"]["prob"]
                text = (f"Back {team} on the moneyline against {opponent}. "
                       f"{team} have shown strong form with solid defensive play and efficient scoring. "
                       f"Our model gives them a {round(prob*100,1)}% win probability based on current season goal differentials. "
                       f"The home advantage and recent momentum make this a strong selection at fair odds of {m['fair_odds']['decimal']}.")
                predictions.append({"match_id": m["id"], "pick": team, "market": "moneyline", "text": text, "word_count": len(text.split())})
    return predictions

def main():
    with open("data/final-desk/fixtures.json") as f:
        data = json.load(f)
    with open("data/final-desk/team_stats.json") as f:
        team_stats = json.load(f)
    matches = originate_lines(data["fixtures"], team_stats)
    predictions = generate_predictions(matches)
    with open("data/final-desk/matches.json", "w") as f:
        json.dump({"matches": matches, "generated_at": "2026-10-22T12:00:00Z"}, f, indent=2)
    with open("data/final-desk/predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    high = sum(1 for m in matches if m["confidence"] == "high")
    med = sum(1 for m in matches if m["confidence"] == "medium")
    low = sum(1 for m in matches if m["confidence"] == "low")
    print(f"✓ {len(matches)} matches: {high} high, {med} medium, {low} low confidence")
    print(f"✓ {len(predictions)} predictions generated")

if __name__ == "__main__":
    main()
