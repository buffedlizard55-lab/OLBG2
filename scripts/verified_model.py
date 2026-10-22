#!/usr/bin/env python3
"""Independent multi-market line origination and human prediction builder for /verified/.

Reads cleanroom primary-official inputs from data/verified/inputs.json (plus the
verified shared tables in data/inputs/{nhl_teams,nba_teams,fixtures,urc,handball_ehf}.json)
and writes:
  - data/verified/matches.json
  - data/verified/predictions.json

Zero bookmaker odds or tipster consensus percentages enter any equation.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from verified_refresh_data import HUBS

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "data" / "verified"
SHARED = ROOT / "data" / "inputs"

HIGH_THRESHOLD = 0.70  # strictly greater than 70%, not >=
MEDIUM_THRESHOLD = 0.60
HIGH_AMERICAN_MIN = -250
HIGH_AMERICAN_MAX = 10000


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fair_decimal(prob: float) -> float:
    return round(max(1.02, 1.0 / max(prob, 1e-6)), 2)


def fair_american(prob: float) -> int:
    """No-vig American price derived from the same model probability."""
    if prob >= 0.5:
        return round(-100.0 * prob / (1.0 - prob))
    return round(100.0 * (1.0 - prob) / prob)


def american_in_high_band(american: int) -> bool:
    return HIGH_AMERICAN_MIN <= american <= HIGH_AMERICAN_MAX


def high_eligible(prob: float) -> bool:
    return prob > HIGH_THRESHOLD and american_in_high_band(fair_american(prob))


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def half_line(raw: float) -> float:
    """Nearest half-point market line to raw projection."""
    return math.floor(raw) + 0.5


def spread_line(expected_home_margin: float) -> float:
    """Standard half-point home handicap (negative when home is favoured)."""
    target = -expected_home_margin
    return math.floor(target) + 0.5


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


def grade(prob: float, cap: str | None = None) -> str:
    raw = "high" if high_eligible(prob) else ("medium" if prob >= MEDIUM_THRESHOLD else "low")
    order = ["low", "medium", "high"]
    if cap and order.index(raw) > order.index(cap):
        return cap
    return raw


def best_of_race(p: float, target: int) -> list[tuple[int, int, float]]:
    """Exact score distribution for first-to-`target` legs/frames/sets."""
    outcomes: list[tuple[int, int, float]] = []
    q = 1.0 - p
    for opp in range(target):
        ways = math.comb(target - 1 + opp, opp)
        outcomes.append((target, opp, ways * (p**target) * (q**opp)))
        outcomes.append((opp, target, ways * (q**target) * (p**opp)))
    return outcomes


# Hand-crafted, non-templated human analyses for every HIGH-confidence selection.
# Each entry uses verified official figures only and embeds {prob_pct} and {price}
# directly from the live model run so prose and table numbers can never diverge.
BESPOKE_HIGH_NARRATIVES: dict[str, dict] = {
    "nhl-2026020162": {
        "headline": "Minnesota's stronger season record earns a narrow High-grade away lean",
        "template": (
            "Moneyline: **Minnesota Wild**. Minnesota bring a 6–2–2 record into Calgary, while the Flames are 2–6–0. The Wild's latest game was a 4–3 overtime loss at Edmonton on 20 October, so this is not a winning-streak claim; the edge comes from the stronger season record. "
            "Calgary did beat Carolina 3–2 on 18 October, but the official figures still make Minnesota a narrow High-grade away selection at {prob_pct}% ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Official records for game 2026020162: Minnesota 6–2–2; Calgary 2–6–0", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
            {"claim": "Minnesota lost 4–3 in overtime at Edmonton on 20 October", "source": "https://api-web.nhle.com/v1/club-schedule/MIN/week/2026-10-19"},
            {"claim": "Calgary beat Carolina 3–2 on 18 October after earlier losses including 6–2 at Vegas", "source": "https://api-web.nhle.com/v1/club-schedule/CGY/week/2026-10-12"},
        ],
    },
    "prod2-12066": {
        "headline": "Aurillac's consecutive wins contrast with winless Nevers",
        "template": (
            "Match winner: **Stade Aurillacois**. Aurillac have climbed to ninth in Pro D2 with three wins from seven and arrive on back-to-back league victories. Nevers remain bottom and winless after seven rounds, with 146 points scored and 222 conceded. "
            "At Stade Jean Alric on 23 October, the official table supports Aurillac at {prob_pct}% ({price} fair decimal), although their own 240–254 points record argues against extending this to a handicap selection."
        ),
        "facts": [
            {"claim": "Aurillac are ninth at 3W–0D–4L, 240:254, with two straight wins; Nevers are 16th at 0W–0D–7L, 146:222", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Aurillac host Nevers on 23 October at Stade Jean Alric", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12066-aurillac-nevers"},
        ],
    },
    "urc-292609": {
        "headline": "Connacht's comparative edge comes against winless Zebre",
        "template": (
            "Match winner: **Connacht Rugby**. Connacht have one win from three URC rounds and are coming off a 36–19 defeat at Glasgow, so the case is comparative rather than a winning-streak claim. Zebre remain winless after three matches, conceding 116 points while scoring 52, and lost 29–12 to Edinburgh in their latest recorded outing. "
            "At Dexcom Stadium, those official figures give Connacht a narrow High-grade edge at {prob_pct}% ({price} fair decimal), rather than a stronger handicap position."
        ),
        "facts": [
            {"claim": "Connacht are 1W–0D–2L; Zebre are winless at 0W–0D–3L with 52:116 points", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Recent official results include Glasgow 36–19 Connacht and Zebre 12–29 Edinburgh", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Connacht host Zebre at Dexcom Stadium on 23 October", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/connacht-rugby-vs-zebre-parma-2026-10-23/292609"},
        ],
    },
}

def originate_nhl(nhl_teams: dict, fixtures: list[dict]) -> list[dict]:
    teams = {k: dict(v) for k, v in nhl_teams["teams"].items()}
    # Apply verified 2026-10-21T07:35Z NHL REST summary updates (including 20 Oct games; see L01)
    teams["TBL"].update({"gp": 9, "w": 7, "l": 2, "otl": 0, "gf": 31, "ga": 23, "points": 14})
    teams["VAN"].update({"gp": 11, "w": 2, "l": 8, "otl": 1, "gf": 33, "ga": 51, "points": 5})
    teams["VGK"].update({"gp": 11, "w": 8, "l": 3, "otl": 0, "gf": 43, "ga": 30, "points": 16})
    teams["CAR"].update({"gp": 11, "w": 8, "l": 2, "otl": 1, "gf": 42, "ga": 27, "points": 17})
    lg_gf = sum(t["gf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    rows: list[dict] = []
    for f in fixtures:
        h = teams[f["home"]]
        a = teams[f["away"]]
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
        reg_a = sum(p for (i, j), p in grid.items() if i < j)
        p_home = reg_h + 0.52 * reg_d
        p_away = 1.0 - p_home
        p_h_pl = sum(p for (i, j), p in grid.items() if i - j >= 2)
        p_a_pl = 1.0 - p_h_pl
        tot_line = 5.5 if (lh + la) < 6.0 else 6.5
        p_over = sum(p for (i, j), p in grid.items() if (i + j) > tot_line)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        conf = grade(win_prob)
        rows.append(
            {
                "id": f"nhl-{f['game_id']}",
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
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": -1.5, "label": f"{h['name']} -1.5 / {a['name']} +1.5", "fav_prob": round(p_h_pl, 4), "dog_prob": round(p_a_pl, 4), "fav_odds": fair_decimal(p_h_pl), "dog_odds": fair_decimal(p_a_pl)},
                "total_market": {"line": tot_line, "projected": round(lh + la, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Moneyline)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": conf},
                "official_source": "NHL GameCenter & Stats API",
                "official_url": f"https://www.nhl.com/gamecenter/{f['away'].lower()}-vs-{f['home'].lower()}/{f['date'].replace('-', '/')}/{f['game_id']}",
                "data_url": "https://api.nhle.com/stats/rest/en/team/summary",
                "olbg_url": f.get("olbg_event_url") or "https://www.olbg.com/betting-tips/Ice_Hockey/13",
            }
        )
    return rows


def originate_ice_league(
    teams: dict, fixtures: list[dict], competition: str,
    official_source: str, standings_url: str, schedule_url: str,
    *, default_date: str | None = None, default_time: str | None = None,
) -> list[dict]:
    """SHL/Liiga Poisson prices from official GF/GA, with eight-game shrinkage."""
    # With a full league table, GF/team-game is the natural scoring baseline.
    # For the single Liiga fixture, averaging GF and GA over the two clubs avoids
    # inventing a league-wide mean from unconfirmed teams.
    if len(teams) == 2:
        lg_gf = 0.5 * (sum(t["gf"] for t in teams.values()) + sum(t["ga"] for t in teams.values())) / sum(t["gp"] for t in teams.values())
    else:
        lg_gf = sum(t["gf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    rows: list[dict] = []
    for f in fixtures:
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
        total_line = 5.5 if lh + la < 6.0 else 6.5
        p_over = sum(p for (i, j), p in grid.items() if i + j > total_line)
        side = h["name"] if p_home >= p_away else a["name"]
        prob = max(p_home, p_away)
        rows.append({
            "id": f["id"], "sport": "ice-hockey", "sport_name": "Ice Hockey",
            "competition": competition, "date": f.get("date") or default_date,
            "time": f.get("time") or default_time,
            "home": h["name"], "away": a["name"], "venue": f.get("venue"),
            "line_status": "originated",
            "home_summary": f"{h['w']}W-{h['t']}T-{h['l']}L ({h['gf']} GF / {h['ga']} GA)",
            "away_summary": f"{a['w']}W-{a['t']}T-{a['l']}L ({a['gf']} GF / {a['ga']} GA)",
            "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
            "handicap_market": {"line": -1.5, "label": f"{h['name']} -1.5 / {a['name']} +1.5", "fav_prob": round(p_h_pl, 4), "dog_prob": round(1.0 - p_h_pl, 4), "fav_odds": fair_decimal(p_h_pl), "dog_odds": fair_decimal(1.0 - p_h_pl)},
            "total_market": {"line": total_line, "projected": round(lh + la, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
            "pick": {"selection": f"{side} (Moneyline)", "team": side, "probability": round(prob, 4), "fair_odds": fair_decimal(prob), "confidence": grade(prob)},
            "official_source": official_source, "official_url": f.get("url") or schedule_url,
            "data_url": standings_url, "olbg_url": HUBS["ice-hockey"],
            "model_note": (
                "Eight-game shrinkage toward the official league scoring baseline."
                if len(teams) > 2 else
                "Eight-game shrinkage toward a two-club GF/GA baseline; no complete current Liiga table was captured, so no other clubs' values are inferred."
            ),
        })
    return rows


def originate_nba(nba_teams: dict, fixtures: list[dict], extra_ids: dict) -> list[dict]:
    teams = nba_teams["teams"]
    rows: list[dict] = []
    k = 10.0
    for idx, f in enumerate(fixtures, 1):
        h = teams[f["home"]]
        a = teams[f["away"]]
        key = f"{f['away']}|{f['home']}|{f['date']}"
        gid = f.get("game_id") or extra_ids.get(key)
        slug_url = f"https://www.nba.com/game/{f['away'].lower()}-vs-{f['home'].lower()}-{gid}" if gid else f"https://www.nba.com/games?date={f['date']}"
        ph0 = (h["w"] + 0.5 * k) / (h["w"] + h["l"] + k)
        pa0 = (a["w"] + 0.5 * k) / (a["w"] + a["l"] + k)
        # Austin's Moody Center is a neutral venue, not a normal Spurs home floor.
        home_adjustment = 0.0 if f.get("neutral") else 0.28
        logit = math.log(ph0 / (1.0 - ph0)) - math.log(pa0 / (1.0 - pa0)) + home_adjustment
        p_home = logistic(logit)
        p_away = 1.0 - p_home
        exp_margin = logit * 6.8
        hcap = spread_line(exp_margin)
        p_cover = 1.0 - normal_cdf((-hcap - exp_margin) / 12.0)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        conf = grade(win_prob, cap="medium")
        rows.append(
            {
                "id": f"nba-{gid or idx}",
                "sport": "basketball",
                "sport_name": "Basketball",
                "competition": "NBA Regular Season 2026-27",
                "date": f["date"],
                "time": f"{f['date']} {f['tip_et']} ET",
                "home": h["name"],
                "away": a["name"],
                "venue": f.get("venue"),
                "neutral_site": bool(f.get("neutral")),
                "confidence_cap": "medium",
                "line_status": "originated",
                "home_summary": f"2025-26: {h['w']}-{h['l']} (Home {h['home_w']}-{h['home_l']})",
                "away_summary": f"2025-26: {a['w']}-{a['l']} (Road {a['road_w']}-{a['road_l']})",
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": None,  # Explicitly left blank: nba.com standings omit team points for/against
                "pick": {"selection": f"{win_side} (Moneyline)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": conf},
                "official_source": "NBA Official Game Page",
                "official_url": slug_url,
                "data_url": "https://www.nba.com/standings?Season=2025-26",
                "olbg_url": f.get("olbg_event_url") or "https://www.olbg.com/betting-tips/Basketball/19",
            }
        )
    return rows


def originate_euro_hoops(teams: dict, fixtures: list[dict], comp: str, standings_url: str) -> list[dict]:
    lg_ppg = sum(t["pf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    k = 3.0
    rows: list[dict] = []
    for f in fixtures:
        h = teams[f["home"]]
        a = teams[f["away"]]
        off_h = (h["pf"] + k * lg_ppg) / (h["gp"] + k)
        def_h = (h["pa"] + k * lg_ppg) / (h["gp"] + k)
        off_a = (a["pf"] + k * lg_ppg) / (a["gp"] + k)
        def_a = (a["pa"] + k * lg_ppg) / (a["gp"] + k)
        hca = 0.0 if f.get("neutral") else 3.4
        exp_h = 0.5 * (off_h + def_a) + 0.5 * hca
        exp_a = 0.5 * (off_a + def_h) - 0.5 * hca
        exp_margin = exp_h - exp_a
        exp_total = exp_h + exp_a
        p_home = normal_cdf(exp_margin / 10.8)
        p_away = 1.0 - p_home
        hcap = spread_line(exp_margin)
        p_cover = 1.0 - normal_cdf((-hcap - exp_margin) / 10.8)
        tline = half_line(exp_total)
        p_over = 1.0 - normal_cdf((tline - exp_total) / 13.5)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        rows.append(
            {
                "id": f["id"],
                "sport": "basketball",
                "sport_name": "Basketball",
                "competition": comp,
                "date": f["date"],
                "time": f["time"],
                "home": h["name"],
                "away": a["name"],
                "venue": f.get("venue"),
                "line_status": "originated",
                "home_summary": f"{h['w']}-{h['l']} ({h['pf']} PF / {h['pa']} PA)",
                "away_summary": f"{a['w']}-{a['l']} ({a['pf']} PF / {a['pa']} PA)",
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": tline, "projected": round(exp_total, 1), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Moneyline)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "Euroleague Basketball Official",
                "official_url": f["url"],
                "data_url": standings_url,
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_rugby(teams: dict, fixtures: list[dict], comp: str, standings_url: str, source_label: str) -> list[dict]:
    lg_ppg = sum(t["pf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    k = 3.0
    rows: list[dict] = []
    for f in fixtures:
        h = teams[f["home"]]
        a = teams[f["away"]]
        off_h = (h["pf"] + k * lg_ppg) / (h["gp"] + k)
        def_h = (h["pa"] + k * lg_ppg) / (h["gp"] + k)
        off_a = (a["pf"] + k * lg_ppg) / (a["gp"] + k)
        def_a = (a["pa"] + k * lg_ppg) / (a["gp"] + k)
        hca = 4.2
        exp_h = 0.5 * (off_h + def_a) + 0.5 * hca
        exp_a = 0.5 * (off_a + def_h) - 0.5 * hca
        exp_margin = exp_h - exp_a
        exp_total = exp_h + exp_a
        sigma = 12.6
        p_draw = normal_cdf((0.5 - exp_margin) / sigma) - normal_cdf((-0.5 - exp_margin) / sigma)
        p_home_1x2 = 1.0 - normal_cdf((0.5 - exp_margin) / sigma)
        p_away_1x2 = normal_cdf((-0.5 - exp_margin) / sigma)
        dnb_home = p_home_1x2 / (p_home_1x2 + p_away_1x2)
        hcap = spread_line(exp_margin)
        p_cover = 1.0 - normal_cdf((-hcap - exp_margin) / sigma)
        tline = half_line(exp_total)
        p_over = 1.0 - normal_cdf((tline - exp_total) / 14.2)
        win_side = h["name"] if p_home_1x2 >= p_away_1x2 else a["name"]
        win_prob = max(p_home_1x2, p_away_1x2)
        rows.append(
            {
                "id": f["id"],
                "sport": "rugby-union",
                "sport_name": "Rugby Union",
                "competition": comp,
                "date": f["date"],
                "time": f["time"],
                "home": h["name"],
                "away": a["name"],
                "venue": f.get("venue"),
                "line_status": "originated",
                "home_summary": f"{h['w']}W-{h['d']}D-{h['l']}L ({h['pf']} PF / {h['pa']} PA)",
                "away_summary": f"{a['w']}W-{a['d']}D-{a['l']}L ({a['pf']} PF / {a['pa']} PA)",
                "winner_market": {
                    "type": "1X2 Match Result",
                    "home_prob": round(p_home_1x2, 4),
                    "draw_prob": round(p_draw, 4),
                    "away_prob": round(p_away_1x2, 4),
                    "home_odds": fair_decimal(p_home_1x2),
                    "draw_odds": fair_decimal(p_draw),
                    "away_odds": fair_decimal(p_away_1x2),
                    "dnb_home_prob": round(dnb_home, 4),
                },
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": tline, "projected": round(exp_total, 1), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (1X2 Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": source_label,
                "official_url": f["url"],
                "data_url": standings_url,
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_handball(ehf_data: dict, olbg_map: dict) -> list[dict]:
    teams = ehf_data["teams"]
    lg_gf = sum(t["gf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    k = 3.0
    rows: list[dict] = []
    for f in ehf_data["fixtures"]:
        h = teams[f["home"]]
        a = teams[f["away"]]
        att_h = ((h["gf"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        def_h = ((h["ga"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        att_a = ((a["gf"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        def_a = ((a["ga"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        lh = lg_gf * att_h * def_a * 1.06
        la = lg_gf * att_a * def_h
        grid = poisson_grid(lh, la)
        p_home = sum(p for (i, j), p in grid.items() if i > j)
        p_draw = sum(p for (i, j), p in grid.items() if i == j)
        p_away = sum(p for (i, j), p in grid.items() if i < j)
        hcap = spread_line(lh - la)
        p_cover = sum(p for (i, j), p in grid.items() if (i - j) + hcap > 0)
        tline = half_line(lh + la)
        p_over = sum(p for (i, j), p in grid.items() if (i + j) > tline)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        rows.append(
            {
                "id": f["id"],
                "sport": "handball",
                "sport_name": "Handball",
                "competition": "EHF Champions League Men 2026/27 — Round 5",
                "date": f["date"],
                "time": f"{f['date']} {f['time_local']} {f['timezone']}",
                "home": h["name"],
                "away": a["name"],
                "venue": f["venue"],  # None where unconfirmed -> renders blank '—'
                "line_status": "originated",
                "home_summary": f"Grp {h['group']}: {h['w']}W-{h['d']}D-{h['l']}L ({h['gf']} GF / {h['ga']} GA)",
                "away_summary": f"Grp {a['group']}: {a['w']}W-{a['d']}D-{a['l']}L ({a['gf']} GF / {a['ga']} GA)",
                "winner_market": {"type": "1X2 Match Result", "home_prob": round(p_home, 4), "draw_prob": round(p_draw, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "draw_odds": fair_decimal(p_draw), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": tline, "projected": round(lh + la, 1), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (1X2 Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "EHF Official Match Details",
                "official_url": f["detail_url"],
                "data_url": "https://ehfcl.eurohandball.com/men/2026-27/standings/",
                "olbg_url": olbg_map.get(f["id"]),
            }
        )
    return rows


def originate_darts(players: dict, fixtures: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for f in fixtures:
        p1 = players[f["p1"]]
        p2 = players[f["p2"]]
        leg_p1 = logistic(0.24 * math.log(p1["prize_gbp"] / p2["prize_gbp"]))
        dist = best_of_race(leg_p1, target=6)
        m_p1 = sum(pr for a, b, pr in dist if a > b)
        m_p2 = 1.0 - m_p1
        hcap = -1.5 if m_p1 >= 0.5 else 1.5
        p_cover = sum(pr for a, b, pr in dist if (a - b) + hcap > 0)
        exp_legs = sum((a + b) * pr for a, b, pr in dist)
        p_over = sum(pr for a, b, pr in dist if (a + b) > 9.5)
        win_side = f["p1"] if m_p1 >= m_p2 else f["p2"]
        win_prob = max(m_p1, m_p2)
        rows.append(
            {
                "id": f["id"],
                "sport": "darts",
                "sport_name": "Darts",
                "competition": "2026 PDC European Championship — Round 1 (Best of 11 Legs)",
                "date": f["date"],
                "time": f["time"],
                "home": f["p1"],
                "away": f["p2"],
                "venue": "Westfalenhalle, Dortmund",
                "line_status": "originated",
                "home_summary": f"PDC #{p1['rank']} (£{p1['prize_gbp']:,})",
                "away_summary": f"PDC #{p2['rank']} (£{p2['prize_gbp']:,})",
                "winner_market": {"type": "2-way Match Winner", "home_prob": round(m_p1, 4), "away_prob": round(m_p2, 4), "home_odds": fair_decimal(m_p1), "away_odds": fair_decimal(m_p2)},
                "handicap_market": {"line": hcap, "label": f"{f['p1']} {hcap:+.1f} legs", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": 9.5, "projected": round(exp_legs, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "PDC Official Rankings",
                "official_url": "https://www.pdc.tv/rankings",
                "data_url": "https://www.pdc.tv/rankings",
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_tennis(players: dict, fixtures: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for f in fixtures:
        p1 = players[f["p1"]]
        p2 = players[f["p2"]]
        set_p1 = logistic(0.68 * math.log(p1["points"] / p2["points"]))
        dist = best_of_race(set_p1, target=2)
        m_p1 = sum(pr for a, b, pr in dist if a > b)
        m_p2 = 1.0 - m_p1
        hcap = -1.5 if m_p1 >= 0.5 else 1.5
        p_cover = sum(pr for a, b, pr in dist if (a - b) + hcap > 0)
        exp_sets = sum((a + b) * pr for a, b, pr in dist)
        p_over = sum(pr for a, b, pr in dist if (a + b) > 2.5)
        win_side = f["p1"] if m_p1 >= m_p2 else f["p2"]
        win_prob = max(m_p1, m_p2)
        rows.append(
            {
                "id": f["id"],
                "sport": "tennis",
                "sport_name": "Tennis",
                "competition": f["competition"],
                "date": f["date"],
                "time": f["time"],
                "home": f["p1"],
                "away": f["p2"],
                "venue": None,
                "line_status": "originated",
                "home_summary": f"ATP #{p1['rank']} ({p1['points']:,} pts)",
                "away_summary": f"ATP #{p2['rank']} ({p2['points']:,} pts)",
                "winner_market": {"type": "2-way Match Winner", "home_prob": round(m_p1, 4), "away_prob": round(m_p2, 4), "home_odds": fair_decimal(m_p1), "away_odds": fair_decimal(m_p2)},
                "handicap_market": {"line": hcap, "label": f"{f['p1']} {hcap:+.1f} sets", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": 2.5, "projected": round(exp_sets, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "ATP Tour Official",
                "official_url": f["url"],
                "data_url": "https://www.atptour.com/en/rankings/singles",
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_snooker(players: dict, fixtures: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for f in fixtures:
        p1 = players[f["p1"]]
        p2 = players[f["p2"]]
        frame_p1 = logistic(0.36 * math.log(p1["prize_gbp"] / p2["prize_gbp"]))
        dist = best_of_race(frame_p1, target=4)
        m_p1 = sum(pr for a, b, pr in dist if a > b)
        m_p2 = 1.0 - m_p1
        hcap = -1.5 if m_p1 >= 0.5 else 1.5
        p_cover = sum(pr for a, b, pr in dist if (a - b) + hcap > 0)
        exp_frames = sum((a + b) * pr for a, b, pr in dist)
        p_over = sum(pr for a, b, pr in dist if (a + b) > 5.5)
        win_side = f["p1"] if m_p1 >= m_p2 else f["p2"]
        win_prob = max(m_p1, m_p2)
        rows.append(
            {
                "id": f["id"],
                "sport": "snooker",
                "sport_name": "Snooker",
                "competition": "BetVictor Northern Ireland Open 2026 — Round 2 (Best of 7 Frames)",
                "date": f["date"],
                "time": f["time"],
                "home": f["p1"],
                "away": f["p2"],
                "venue": "Waterfront Hall, Belfast",
                "line_status": "originated",
                "home_summary": f"WST #{p1['rank']} (£{p1['prize_gbp']:,})",
                "away_summary": f"WST #{p2['rank']} (£{p2['prize_gbp']:,})",
                "winner_market": {"type": "2-way Match Winner", "home_prob": round(m_p1, 4), "away_prob": round(m_p2, 4), "home_odds": fair_decimal(m_p1), "away_odds": fair_decimal(m_p2)},
                "handicap_market": {"line": hcap, "label": f"{f['p1']} {hcap:+.1f} frames", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": 5.5, "projected": round(exp_frames, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "WST Official Match Centre",
                "official_url": f["url"],
                "data_url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false",
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_mlb(ws: dict, live_mlb: dict) -> list[dict]:
    teams = live_mlb["teams"]
    rows = []
    lg = 4.45
    for f in live_mlb["fixtures"]:
        h = teams[f["home"]]
        a = teams[f["away"]]
        lh = lg * ((h["runs_scored"] / 162.0) / lg) * ((a["runs_allowed"] / 162.0) / lg) * 1.04
        la = lg * ((a["runs_scored"] / 162.0) / lg) * ((h["runs_allowed"] / 162.0) / lg)
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
        rows.append(
            {
                "id": f["id"],
                "sport": "baseball",
                "sport_name": "Baseball",
                "competition": f"2026 MLB {f['description']}",
                "date": f["official_date"],
                "time": f["game_date_utc"],
                "home": h["name"],
                "away": a["name"],
                "venue": f["venue"],
                "line_status": "originated",
                "home_summary": f"{h['wins']}-{h['losses']} ({h['runs_scored']} RS / {h['runs_allowed']} RA)",
                "away_summary": f"{a['wins']}-{a['losses']} ({a['runs_scored']} RS / {a['runs_allowed']} RA)",
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": -1.5, "label": f"{fav_name} -1.5 / {dog_name} +1.5", "fav_prob": round(p_rl, 4), "dog_prob": round(1.0 - p_rl, 4), "fav_odds": fair_decimal(p_rl), "dog_odds": fair_decimal(1.0 - p_rl)},
                "total_market": {"line": 7.5, "projected": round(lh + la, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{fav_name} (Moneyline)", "team": fav_name, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "MLB Stats API Official",
                "official_url": f["human_url"],
                "data_url": live_mlb["meta"]["standings_source"]["url"],
                "olbg_url": ws["olbg_url"],
            }
        )
    return rows


def originate_f1(drivers: list[dict]) -> list[dict]:
    weights = [d["points"] ** 1.65 for d in drivers]
    total_w = sum(weights) * 1.08  # 8% residual share for P9–P20 grid
    p_usgp_win = weights[0] / total_w
    p_usgp_field = 1.0 - p_usgp_win
    p_podium = min(0.88, 1.0 - (1.0 - p_usgp_win) ** 3)
    # Championship title probability given +102 pt cushion over #2 Russell with 7 rounds left
    gap = drivers[0]["points"] - drivers[1]["points"]
    p_title = normal_cdf(gap / 46.0)
    # OLBG event 912 is the 2026 championship without Antonelli, not a 2027
    # future. Remove only his weight and retain the explicitly modelled residual.
    total_without = sum(weights[1:]) + 0.08 * sum(weights)
    p_without = weights[1] / total_without
    return [
        {
            "id": "f1-2026-usgp",
            "sport": "motor-racing",
            "sport_name": "Motor Racing",
            "competition": "2026 Formula 1 United States Grand Prix (Round 18, COTA)",
            "date": "2026-10-25",
            "time": "2026-10-25 16:00 track time",
            "home": "Kimi Antonelli (Mercedes)",
            "away": "19-Driver Field (led by Russell 238, Hamilton 229, Verstappen 221)",
            "venue": "Circuit of the Americas, Austin",
            "line_status": "originated",
            "home_summary": "FIA #1 — 340 pts (17 rounds)",
            "away_summary": "Russell 238 · Hamilton 229 · Verstappen 221",
            "winner_market": {"type": "Race Outright Winner", "home_prob": round(p_usgp_win, 4), "away_prob": round(p_usgp_field, 4), "home_odds": fair_decimal(p_usgp_win), "away_odds": fair_decimal(p_usgp_field)},
            "handicap_market": {"line": -0.5, "label": "Antonelli Top-3 Podium Yes / No", "fav_prob": round(p_podium, 4), "dog_prob": round(1.0 - p_podium, 4), "fav_odds": fair_decimal(p_podium), "dog_odds": fair_decimal(1.0 - p_podium)},
            "total_market": None,
            "pick": {"selection": "Kimi Antonelli — Race Winner (Outright)", "team": "Kimi Antonelli (Mercedes)", "probability": round(p_usgp_win, 4), "fair_odds": fair_decimal(p_usgp_win), "confidence": grade(p_usgp_win)},
            "official_source": "Formula 1 Official Race Page & Standings",
            "official_url": "https://www.formula1.com/en/racing/2026/united-states",
            "data_url": "https://www.formula1.com/en/results/2026/drivers",
            "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        },
        {
            "id": "f1-2026-drivers",
            "sport": "motor-racing",
            "sport_name": "Motor Racing",
            "competition": "2026 FIA Formula 1 Drivers' World Championship — Outright",
            "date": "2026-12-06",
            "time": "OLBG card label: 06 Dec 08:00; season outright (7 rounds left in stored capture)",
            "home": "Kimi Antonelli (Mercedes)",
            "away": "Chasing Pack (Russell 238, Hamilton 229, Verstappen 221)",
            "venue": None,
            "line_status": "originated",
            "home_summary": "FIA #1 — 340 pts (+102 lead)",
            "away_summary": "Russell #2 (238 pts) · Hamilton #3 (229 pts)",
            "winner_market": {"type": "Championship Outright", "home_prob": round(p_title, 4), "away_prob": round(1.0 - p_title, 4), "home_odds": fair_decimal(p_title), "away_odds": fair_decimal(1.0 - p_title)},
            "handicap_market": {"line": -65.5, "label": "Antonelli Season Margin -65.5 pts vs Russell", "fav_prob": round(normal_cdf((gap - 65.5) / 46.0), 4), "dog_prob": round(1.0 - normal_cdf((gap - 65.5) / 46.0), 4), "fav_odds": fair_decimal(normal_cdf((gap - 65.5) / 46.0)), "dog_odds": fair_decimal(1.0 - normal_cdf((gap - 65.5) / 46.0))},
            "total_market": None,
            "pick": {"selection": "Kimi Antonelli — 2026 World Champion", "team": "Kimi Antonelli (Mercedes)", "probability": round(p_title, 4), "fair_odds": fair_decimal(p_title), "confidence": grade(p_title)},
            "official_source": "Formula 1 Official Standings",
            "official_url": "https://www.formula1.com/en/results/2026/drivers",
            "data_url": "https://www.formula1.com/en/results/2026/drivers",
            "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        },
        {
            "id": "f1-2026-without-antonelli",
            "sport": "motor-racing", "sport_name": "Motor Racing",
            "competition": "2026 FIA Formula 1 Championship Without Kimi Antonelli — Outright",
            "date": "2026-12-06",
            "time": "OLBG card label: 06 Dec 08:00; season-outright market",
            "home": "George Russell (Mercedes)",
            "away": "Remaining field excluding Antonelli (led by Hamilton 229, Verstappen 221)",
            "venue": None, "line_status": "originated",
            "home_summary": "FIA #2 — 238 pts (stored official capture 2026-10-21)",
            "away_summary": "Hamilton #3 (229 pts) · Verstappen #4 (221 pts)",
            "winner_market": {"type": "Championship Outright Without Kimi Antonelli", "home_prob": round(p_without, 4), "away_prob": round(1.0 - p_without, 4), "home_odds": fair_decimal(p_without), "away_odds": fair_decimal(1.0 - p_without)},
            "handicap_market": None, "total_market": None,
            "pick": {"selection": "George Russell — 2026 Champion Without Kimi Antonelli", "team": "George Russell (Mercedes)", "probability": round(p_without, 4), "fair_odds": fair_decimal(p_without), "confidence": grade(p_without)},
            "official_source": "Formula 1 Official Standings",
            "official_url": "https://www.formula1.com/en/results/2026/drivers",
            "data_url": "https://www.formula1.com/en/results/2026/drivers",
            "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
            "model_note": "Antonelli's weight is removed; the explicit 8% residual for P9–P20 is retained and remaining official-standing weights are renormalized.",
        },
    ]


def finalise_originated_row(m: dict, provenance_by_id: dict) -> None:
    """Attach source scope and enforce the two-part High rule on every pick."""
    if m["id"] not in provenance_by_id:
        raise RuntimeError(f"Missing provenance register for originated row {m['id']}")
    prov = provenance_by_id[m["id"]]
    m["provenance"] = prov
    m["olbg_event_id"] = prov.get("olbg_event_id")
    if prov["discovery"] == "official supplementary":
        m["olbg_url"] = None
    elif m["sport"] == "darts" and m.get("olbg_url"):
        # Existing PDC rows carry direct event URLs.
        pass
    else:
        m["olbg_url"] = HUBS[m["sport"]]
    p = m["pick"]["probability"]
    american = fair_american(p)
    above = p > HIGH_THRESHOLD
    in_band = american_in_high_band(american)
    cap = m.get("confidence_cap")
    m["pick"]["fair_american"] = american
    m["pick"]["high_gate"] = {
        "probability_gt_70": above,
        "fair_american_in_band": in_band,
        "eligible": above and in_band,
        "rule": "p > 0.70 and -250 <= fair American <= +10000",
    }
    m["pick"]["confidence"] = grade(p, cap=cap)
    if above and not in_band:
        m["pick"]["confidence_note"] = f"Above 70%, but fair American {american:+d} is outside the High price band; confidence cannot be High."
    elif cap == "medium" and above and in_band:
        m["pick"]["confidence_note"] = "Medium cap retained because NBA prices use completed prior-season records."
    else:
        m["pick"]["confidence_note"] = "Confidence computed from model probability, strict High threshold and price band."


def main() -> None:
    inputs = read_json(VERIFIED / "inputs.json")
    nhl_teams = read_json(SHARED / "nhl_teams.json")
    nba_teams = read_json(SHARED / "nba_teams.json")
    shared_fx = read_json(SHARED / "fixtures.json")
    urc_raw = read_json(SHARED / "urc.json")
    ehf_raw = read_json(SHARED / "handball_ehf.json")
    sports_meta = {s["slug"]: s["name"] for s in read_json(VERIFIED / "sports.json")["eligible_sports"]}

    urc_teams = {
        k: {"name": v["name"], "gp": v["pl"], "w": v["w"], "d": v["d"], "l": v["l"], "pf": v["pf"], "pa": v["pa"]}
        for k, v in urc_raw["table"].items()
    }
    urc_fixtures = [
        {
            "id": f["id"],
            "date": f["date_local"],
            "time": f"{f['date_local']} {f['time_local']} Local",
            "home": f["home"],
            "away": f["away"],
            "venue": f["venue"],
            "url": f["url"],
            "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9",
        }
        for f in urc_raw["fixtures"]
    ]

    live_mlb_raw = json.loads((ROOT / "data" / "live" / "mlb.json").read_text())
    nhl_ids = set(inputs["nhl_fixture_ids"])
    nhl_fixtures = [f for f in shared_fx["nhl"]["fixtures"] if f"nhl-{f['game_id']}" in nhl_ids]
    if len(nhl_fixtures) != len(nhl_ids):
        raise RuntimeError(f"NHL official fixture filter mismatch: {len(nhl_fixtures)} != {len(nhl_ids)}")
    ehf_ids = set(inputs["ehf_fixture_ids"])
    ehf_current = dict(ehf_raw)
    ehf_current["fixtures"] = [f for f in ehf_raw["fixtures"] if f["id"] in ehf_ids]
    if len(ehf_current["fixtures"]) != len(ehf_ids):
        raise RuntimeError("EHF official fixture filter mismatch")

    originated: list[dict] = []
    originated.extend(originate_nhl(nhl_teams, nhl_fixtures))
    originated.extend(originate_ice_league(
        inputs["shl_teams"], inputs["shl_fixtures"], "SHL 2026-27 — Regular Season",
        "SweHockey Official Schedule & Standings", "https://stats.swehockey.se/ScheduleAndResults/Overview/20961",
        "https://stats.swehockey.se/ScheduleAndResults/Overview/20961",
        default_date="2026-10-22", default_time="2026-10-22 19:00 local",
    ))
    originated.extend(originate_ice_league(
        inputs["liiga_teams"], [inputs["liiga_fixture"]], "Liiga 2026-27 — Regular Season",
        "Liiga & JYP Official", "https://www.liiga.fi/en/stats/teamstats/season?sarja=runkosarja&tilasto=sarjataulukko&kaudesta=2027&kauteen=2027",
        "https://www.jypliiga.fi/ottelu/jyp-hpk-14/",
    ))
    originated.extend(originate_nba(nba_teams, inputs["nba_fixtures"], inputs.get("nba_extra_game_ids", {})))
    originated.extend(originate_euro_hoops(inputs["euroleague_teams"], inputs["euroleague_fixtures"], "EuroLeague 2026-27 — Round 7", "https://www.euroleaguebasketball.net/en/euroleague/standings/"))
    originated.extend(originate_rugby(inputs["top14_teams"], inputs["top14_fixtures"], "French Top 14 2026-27 — Journée 7", "https://top14.lnr.fr/classement", "LNR Official Top 14"))
    originated.extend(originate_rugby(inputs["prod2_teams"], inputs["prod2_fixtures"], "French Pro D2 2026-27 — Journée 8", "https://prod2.lnr.fr/classement", "LNR Official Pro D2"))
    originated.extend(originate_rugby(urc_teams, urc_fixtures, "United Rugby Championship 2026-27 — Round 4", "https://stats.unitedrugby.com/match-centre/table/2026-27", "URC Official Match Centre"))
    originated.extend(originate_handball(ehf_current, inputs["ehf_olbg_map"]))
    originated.extend(originate_darts(inputs["pdc_players"], inputs["darts_fixtures"]))
    originated.extend(originate_tennis(inputs["atp_players"], inputs["tennis_originated"]))
    originated.extend(originate_snooker(inputs["wst_top36"], inputs["snooker_originated"]))
    originated.extend(originate_mlb(inputs["mlb_world_series"], live_mlb_raw))
    originated.extend(originate_f1(inputs["f1_drivers"]))
    for row in originated:
        finalise_originated_row(row, inputs["provenance_by_id"])

    unlined: list[dict] = []
    for u in inputs["unlined_rows"]:
        unlined.append(
            {
                "id": u["id"],
                "sport": u["sport"],
                "sport_name": sports_meta[u["sport"]],
                "competition": u["competition"],
                "date": u["date"],
                "time": u["time"],
                "home": u["home"],
                "away": u["away"],
                "venue": u.get("venue"),
                "line_status": "unlined",
                "home_summary": None,
                "away_summary": None,
                "winner_market": None,
                "handicap_market": None,
                "total_market": None,
                "pick": None,
                "blank_reason": u["blank_reason"],
                "official_source": u["official_source"],
                "official_url": u["official_url"],
                "data_url": None,
                "olbg_url": u.get("olbg_url"),
                "olbg_event_id": u.get("olbg_event_id"),
                "provenance": u.get("provenance"),
            }
        )

    all_rows = originated + unlined
    high_rows = [m for m in originated if m["pick"]["confidence"] == "high"]

    predictions: list[dict] = []
    missing_ids = [m["id"] for m in high_rows if m["id"] not in BESPOKE_HIGH_NARRATIVES]
    if missing_ids:
        raise RuntimeError(f"Missing bespoke human narratives for HIGH picks: {missing_ids}")

    for m in high_rows:
        spec = BESPOKE_HIGH_NARRATIVES[m["id"]]
        prob_pct = f"{m['pick']['probability'] * 100:.1f}"
        price = f"{m['pick']['fair_odds']:.2f}"
        text = spec["template"].format(prob_pct=prob_pct, price=price).replace("**", "")
        plain_words = len(text.split())
        if plain_words < 30:
            raise AssertionError(f"Prediction {m['id']} has only {plain_words} words (< 30)")
        predictions.append(
            {
                "match_id": m["id"],
                "sport": m["sport"],
                "sport_name": m["sport_name"],
                "competition": m["competition"],
                "event": f"{m['away']} @ {m['home']}" if m["sport"] in {"ice-hockey", "baseball"} else f"{m['home']} v {m['away']}",
                "time": m["time"],
                "selection": m["pick"]["selection"],
                "probability": m["pick"]["probability"],
                "fair_odds": m["pick"]["fair_odds"],
                "fair_american": m["pick"]["fair_american"],
                "confidence": "high",
                "headline": spec["headline"],
                "text": text,
                "word_count": plain_words,
                "facts": spec["facts"],
                "official_url": m["official_url"],
                "olbg_url": m["olbg_url"],
            }
        )

    counts = {
        "total_rows": len(all_rows),
        "originated_rows": len(originated),
        "unlined_rows": len(unlined),
        "high_confidence": sum(1 for m in originated if m["pick"]["confidence"] == "high"),
        "medium_confidence": sum(1 for m in originated if m["pick"]["confidence"] == "medium"),
        "low_confidence": sum(1 for m in originated if m["pick"]["confidence"] == "low"),
    }
    write_json(VERIFIED / "matches.json", {"captured_at": inputs["captured_at"], "counts": counts, "matches": all_rows})
    write_json(VERIFIED / "predictions.json", {"captured_at": inputs["captured_at"], "min_words": 30, "count": len(predictions), "predictions": predictions})
    print(f"verified_model: {counts}")


if __name__ == "__main__":
    main()
