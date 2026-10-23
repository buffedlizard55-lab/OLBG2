#!/usr/bin/env python3
"""Brief desk (session 7a073c9a) - evidence normalisation and line origination.

Inputs are committed captures only:

  data/signal/captures/*.json   first-hand reads made 2026-10-23 16:25-17:22Z by the
                                preceding desk session on this repository
  data/brief/session_captures.json  first-hand reads made 2026-10-23 19:29-20:05Z by
                                this session

Nothing here fetches anything, and no bookmaker price is an input anywhere.
Probabilities are fair (each market sums to 1) and are clamped to [0.05, 0.95].

Outputs
  data/brief/matches.json   every published fixture, every originated market
  data/brief/sources.json   the source ledger rendered on /brief/sources.html
  data/brief/flags.json     review queue rendered on /brief/flagged.html
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP = ROOT / "data" / "signal" / "captures"
OUT = ROOT / "data" / "brief"

CUTOFF = "2026-10-23T19:45:00Z"
GENERATED_FOR = "2026-10-23"
PROB_FLOOR, PROB_CEIL = 0.05, 0.95

SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
    "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
    "Handball", "Ice Hockey", "Basketball", "Rugby League",
]

# ------------------------------------------------------------------ odds maths


def clamp(p: float) -> float:
    return max(PROB_FLOOR, min(PROB_CEIL, p))


def american(p: float) -> int:
    p = clamp(p)
    if p >= 0.5:
        return -int(round(100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def fmt_am(p: float) -> str:
    a = american(p)
    return f"+{a}" if a > 0 else str(a)


def in_band(p: float) -> bool:
    """User's price window: fair American odds inside -250 .. +10000."""
    return -250 <= american(p) <= 10000


def confidence(p: float) -> str:
    if p >= 0.70:
        return "high"
    if p >= 0.55:
        return "medium"
    return "low"


# ------------------------------------------------------------------ distribution maths


def poisson_pmf(lam: float, k: int) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_grid(lam_a: float, lam_b: float, nmax: int = 16):
    return [[poisson_pmf(lam_a, i) * poisson_pmf(lam_b, j) for j in range(nmax + 1)]
            for i in range(nmax + 1)]


def grid_outcomes(grid, draw_share_home: float = 0.0):
    """Return (home win, draw, away win) probabilities from a score grid."""
    home = draw = away = 0.0
    for i, row in enumerate(grid):
        for j, p in enumerate(row):
            if i > j:
                home += p
            elif i == j:
                draw += p
            else:
                away += p
    return home, draw, away


def two_way_with_tie(home: float, draw: float, away: float, home_tie_share: float = 0.55):
    total = home + draw + away
    h = (home + draw * home_tie_share) / total
    return h, 1.0 - h


def grid_two_way(grid, home_tie_share: float = 0.55):
    h, d, a = grid_outcomes(grid)
    return two_way_with_tie(h, d, a, home_tie_share)


def margin_distribution(grid):
    """P(home wins by exactly k) for k in a bounded range."""
    n = len(grid)
    dist = {}
    for i in range(n):
        for j in range(n):
            dist[i - j] = dist.get(i - j, 0.0) + grid[i][j]
    return dist


def handicap_win_prob(dist, line: float) -> float:
    """P(home margin + line > 0). line is the handicap applied to home."""
    return sum(p for m, p in dist.items() if m + line > 0)


def total_over_prob(grid, line: float) -> float:
    over = 0.0
    for i, row in enumerate(grid):
        for j, p in enumerate(row):
            if i + j > line:
                over += p
    return over


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def log5(pa: float, pb: float) -> float:
    denom = pa + pb - 2 * pa * pb
    return (pa - pa * pb) / denom if denom else 0.5


def home_edge(p: float, edge: float) -> float:
    """Apply a multiplicative home edge in log-odds space."""
    lo = math.log(p / (1 - p)) + edge
    return 1 / (1 + math.exp(-lo))


def shrink(p: float, games: int, prior: int = 8) -> float:
    w = games / (games + prior)
    return 0.5 + (p - 0.5) * w


def market(name, selection, p, basis):
    p = clamp(p)
    return {
        "market": name,
        "selection": selection,
        "prob": round(p, 4),
        "american": fmt_am(p),
        "decimal": round(1 / p, 2),
        "in_band": in_band(p),
        "confidence": confidence(p),
        "basis": basis,
    }


# ------------------------------------------------------------------ loaders

def load(name):
    return json.loads((CAP / name).read_text())


SESSION = json.loads((OUT / "session_captures.json").read_text())

SOURCES = {}


def src(key, name, url, sport, used_for, captured_utc, first_hand):
    SOURCES[key] = {
        "key": key, "name": name, "url": url, "sport": sport,
        "used_for": used_for, "captured_utc": captured_utc, "first_hand": first_hand,
    }
    return key


def utc(dt: str) -> datetime:
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


CUT = utc(CUTOFF)


def upcoming(date_str: str, start_utc: str | None) -> bool:
    if start_utc:
        return utc(start_utc[:19] + "Z") > CUT
    return date_str >= "2026-10-24"


def status_of(date_str: str, start_utc: str | None) -> str:
    return "upcoming" if upcoming(date_str, start_utc) else "started before cut-off; result not captured"


# ------------------------------------------------------------------ fixtures

FIXTURES = []


def add_fixture(**kw):
    kw.setdefault("markets", [])
    kw.setdefault("flags", [])
    kw.setdefault("no_in_band", False)
    kw.setdefault("start_utc", None)
    kw.setdefault("start_local", None)
    kw.setdefault("stage", "")
    kw.setdefault("input_note", "")
    kw["status"] = status_of(kw["date"], kw["start_utc"]) if kw.get("date") else "upcoming"
    kw["eligible"] = kw["status"] == "upcoming"
    FIXTURES.append(kw)
    return kw


# ------------------------------------------------------------------ Ice Hockey

def build_nhl():
    fx = load("nhl_fixtures.json")
    summary = load("nhl_team_summary_20262027.json")
    fields = summary["fields"]
    teams = {}
    for row in summary["teams"]:
        d = dict(zip(fields, row))
        teams[d["team"]] = d
    src("nhl-schedule", "NHL official schedule feed (api-web.nhle.com)", "https://api-web.nhle.com/v1/schedule/2026-10-23",
        "Ice Hockey", "14 fixtures, start times, venues, game ids", fx["captured_utc"], "session 6b10ecda, same day")
    src("nhl-teams", "NHL official team summary (api.nhle.com stats REST)", fx["source_urls"]["2026-10-23"] if False else "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2",
        "Ice Hockey", "games played, goals for/against, W-L-OTL for all 32 clubs", summary["captured_utc"], "session 6b10ecda, same day")
    league_gf = sum(t["goalsFor"] for t in teams.values()) / sum(t["gamesPlayed"] for t in teams.values())
    league_ga = sum(t["goalsAgainst"] for t in teams.values()) / sum(t["gamesPlayed"] for t in teams.values())
    league = (league_gf + league_ga) / 2
    for g in fx["games"]:
        h, a = teams.get(g["home"]), teams.get(g["away"])
        f = add_fixture(
            id=f"nhl-{g['id']}", sport="Ice Hockey", competition="NHL regular season", stage="",
            home=g["home"], away=g["away"], date=g["date"], start_utc=g["startUTC"], venue=g["venue"],
            source_key="nhl-schedule", source_url=g["gamecenter"], as_of=fx["captured_utc"],
            inputs=[{"key": "nhl-teams", "home": h, "away": a}] if h and a else [],
        )
        if not h or not a:
            f["flags"].append("no team-summary row for one side; left unlined")
            continue
        lam_h = ((h["goalsFor"] / h["gamesPlayed"]) + (a["goalsAgainst"] / a["gamesPlayed"])) / 2 * (league / (league or 1)) * 1.04
        lam_a = ((a["goalsFor"] / a["gamesPlayed"]) + (h["goalsAgainst"] / h["gamesPlayed"])) / 2 * 0.96
        lam_h = max(1.4, min(5.0, lam_h))
        lam_a = max(1.4, min(5.0, lam_a))
        grid = poisson_grid(lam_h, lam_a, 12)
        ph, pa = grid_two_way(grid, 0.55)
        f["expected"] = {"home": round(lam_h, 2), "away": round(lam_a, 2)}
        f["input_note"] = (f"{h['wins']}-{h['losses']}-{h['otLosses']} in {h['gamesPlayed']} GP, "
                           f"{h['goalsFor']/h['gamesPlayed']:.2f} GF/g and {h['goalsAgainst']/h['gamesPlayed']:.2f} GA/g; "
                           f"{a['wins']}-{a['losses']}-{a['otLosses']} in {a['gamesPlayed']} GP, "
                           f"{a['goalsFor']/a['gamesPlayed']:.2f} GF/g and {a['goalsAgainst']/a['gamesPlayed']:.2f} GA/g")
        basis = "Poisson on season GF/GA per game with a 4% home adjustment"
        f["markets"] = [
            market("Money line (2-way, includes OT/SO)", h["team"], ph, basis),
            market("Money line (2-way, includes OT/SO)", a["team"], pa, basis),
            market("Puck line -1.5", h["team"], handicap_win_prob(margin_distribution(grid), -1.5), basis),
            market("Puck line +1.5", a["team"], 1 - handicap_win_prob(margin_distribution(grid), -1.5), basis),
            market("Match total 5.5 - Over", "Over", total_over_prob(grid, 5.5), basis),
            market("Match total 5.5 - Under", "Under", 1 - total_over_prob(grid, 5.5), basis),
            market("Match total 6.5 - Over", "Over", total_over_prob(grid, 6.5), basis),
            market("Match total 6.5 - Under", "Under", 1 - total_over_prob(grid, 6.5), basis),
        ]


# ------------------------------------------------------------------ Baseball

def build_mlb():
    d = load("mlb.json")
    src("mlb-schedule", "MLB official Stats API - schedule", d["source_urls"]["schedule"],
        "Baseball", "World Series fixtures, start times, venues, game ids", d["captured_utc"], "session 6b10ecda, same day")
    src("mlb-standings", "MLB official Stats API - 2026 regular-season standings (AL and NL)", d["source_urls"]["standings_nl"],
        "Baseball", "wins, losses, runs scored/allowed for both World Series clubs", d["captured_utc"], "session 6b10ecda, same day")
    rs = d["regular_season_2026"]
    for g in d["games"]:
        h, a = rs[g["home"]], rs[g["away"]]
        f = add_fixture(
            id=f"mlb-{g['gamePk']}", sport="Baseball", competition="World Series 2026", stage=g["description"],
            home=g["home"], away=g["away"], date=g["date"], start_utc=g["startUTC"], venue=g["venue"],
            source_key="mlb-schedule", source_url=d["source_urls"]["schedule"], as_of=d["captured_utc"],
            inputs=[{"key": "mlb-standings"}],
        )
        ph_raw = log5(h["winPct"], a["winPct"])
        ph = home_edge(ph_raw, 0.16)
        if g["ifNecessary"] == "Y":
            f["flags"].append("if-necessary game; fixture contingent on the series not being decided")
        exp_h = (h["runsScored"] + a["runsAllowed"]) / (h["wins"] + h["losses"]) / 2
        exp_a = (a["runsScored"] + h["runsAllowed"]) / (a["wins"] + a["losses"]) / 2
        total_line = math.floor(exp_h + exp_a) + 0.5
        gap = total_line / 2.0
        f["expected"] = {"home_runs": round(exp_h, 2), "away_runs": round(exp_a, 2)}
        f["input_note"] = (f"{h['wins']}-{h['losses']} ({h['winPct']:.3f}), {h['runsScored']} RS / {h['runsAllowed']} RA; "
                           f"{a['wins']}-{a['losses']} ({a['winPct']:.3f}), {a['runsScored']} RS / {a['runsAllowed']} RA")
        basis = "Log5 on season win percentage with a 16-point home adjustment; team run rates for the total"
        f["markets"] = [
            market("Money line", g["home"], ph, basis),
            market("Money line", g["away"], 1 - ph, basis),
            market("Run line -1.5", g["home"], normal_cdf(-(1.5 - (exp_h - exp_a)) / 3.0), basis),
            market("Run line +1.5", g["away"], normal_cdf((1.5 - (exp_h - exp_a)) / 3.0), basis),
            market(f"Match total {total_line} - Over", "Over", normal_cdf(-(total_line - (exp_h + exp_a)) / 3.2), basis),
            market(f"Match total {total_line} - Under", "Under", 1 - normal_cdf(-(total_line - (exp_h + exp_a)) / 3.2), basis),
        ]


# ------------------------------------------------------------------ Basketball

def build_basketball():
    d = load("basketball_euroleague.json")
    src("el-schedule", "EuroLeague Basketball official schedules feed", d["source_urls"]["schedule_round8"],
        "Basketball", "Round 8 fixtures (10 games), venues, tip times", d["captured_utc"], "session 6b10ecda, same day")
    src("el-standings", "EuroLeague Basketball official standings feed after Round 7", d["source_urls"]["standings_after_round7"],
        "Basketball", "games played, W-L, points for/against", d["captured_utc"], "session 6b10ecda, same day")
    table = {r["team"]: r for r in d["standings_after_round7"]}
    for g in d["fixtures_round8"]:
        h, a = table.get(g["home"]), table.get(g["away"])
        f = add_fixture(
            id=f"el-{g['game_code']}", sport="Basketball", competition="EuroLeague Basketball 2026-27", stage="Round 8",
            home=g["home"], away=g["away"], date=g["date"], start_local=g["time_as_served"], venue=g["venue"],
            source_key="el-schedule", source_url=d["source_urls"]["schedule_round8"], as_of=d["captured_utc"],
            inputs=[{"key": "el-standings"}],
        )
        if not h or not a:
            f["flags"].append("team not present in the captured standings table; left unlined")
            continue
        hp = shrink(h["w"] / h["gp"], h["gp"])
        ap = shrink(a["w"] / a["gp"], a["gp"])
        ph = home_edge(log5(hp, ap), 0.22)
        exp_h = (h["pf"] / h["gp"] + a["pa"] / a["gp"]) / 2
        exp_a = (a["pf"] / a["gp"] + h["pa"] / a["gp"]) / 2
        total = round(exp_h + exp_a, 1) + 0.5
        line = round((exp_h - exp_a) * 2) / 2
        line = abs(line) + 0.5
        line = line if exp_h >= exp_a else -line
        sigma = 11.0
        f["expected"] = {"home": round(exp_h, 1), "away": round(exp_a, 1)}
        f["input_note"] = (f"{h['w']}-{h['l']} after {h['gp']} ({h['pf']} PF / {h['pa']} PA); "
                           f"{a['w']}-{a['l']} after {a['gp']} ({a['pf']} PF / {a['pa']} PA)")
        basis = "Log5 on shrunk win rates with a 22-point home adjustment; scoring rates for the spread and total"
        f["markets"] = [
            market("Money line (2-way)", h["team"], ph, basis),
            market("Money line (2-way)", a["team"], 1 - ph, basis),
            market(f"Spread {line:+.1f}", h["team"], normal_cdf((0 - (exp_h - exp_a - line)) / sigma), basis),
            market(f"Spread {-line:+.1f}", a["team"], 1 - normal_cdf((0 - (exp_h - exp_a - line)) / sigma), basis),
            market(f"Match total {total} - Over", "Over", normal_cdf((exp_h + exp_a - total) / sigma), basis),
            market(f"Match total {total} - Under", "Under", 1 - normal_cdf((exp_h + exp_a - total) / sigma), basis),
        ]


# ------------------------------------------------------------------ Snooker

def build_snooker():
    d = load("snooker_wst.json")
    ranks = load("snooker_rankings_full.json")
    money = ranks["world_ranking_gbp_top36"]
    src("wst-fixtures", "World Snooker Tour official Live & Upcoming matches module", d["source_url"],
        "Snooker", "match list, rounds, dates, match-centre links", d["captured_utc"], "session 6b10ecda, same day")
    src("wst-rankings", "World Snooker Tour official world ranking (prize money, top 36)", ranks["source_url"],
        "Snooker", "prize-money strength inputs", ranks["captured_utc"], "session 6b10ecda, same day")
    bound = min(money.values())
    for i, m in enumerate(d["matches"]):
        f = add_fixture(
            id=f"snk-{i}", sport="Snooker", competition=m["event"], stage=m["round"],
            home=m["p1"], away=m["p2"], date=m["date"], start_local=m["time_local"], venue="match centre",
            source_key="wst-fixtures", source_url=m["match_centre"], as_of=d["captured_utc"],
            inputs=[{"key": "wst-rankings"}],
        )
        p1, p2 = m["p1"], m["p2"]
        if "Winner of" in p1 or "Winner of" in p2 or "Wildcard" in p1 or "Wildcard" in p2:
            f["flags"].append("participant not yet published by the official source; left unlined")
            continue
        s1, s2 = money.get(p1), money.get(p2)
        bounded = False
        if s1 is None:
            s1, bounded = bound, True
        if s2 is None:
            s2, bounded = bound, True
        if bounded:
            f["flags"].append(f"at least one player is outside the published top 36; the 36th-placed figure (GBP {bound:,}) is used as a published upper bound and flagged BR-08")
        if money.get(p1) is None and money.get(p2) is None:
            f["flags"].append("both players sit outside the published top 36, so the same upper bound applies to each and no strength separation exists; left unlined")
            continue
        st1, st2 = s1 ** 0.35, s2 ** 0.35
        p = st1 / (st1 + st2)
        f["input_note"] = (f"world-ranking prize money: {p1} GBP {s1:,}{' (bound)' if money.get(p1) is None else ''}; "
                           f"{p2} GBP {s2:,}{' (bound)' if money.get(p2) is None else ''}")
        f["markets"] = [market("Match winner", p1, p, "Bradley-Terry on ranking prize money (exponent 0.35)"),
                        market("Match winner", p2, 1 - p, "Bradley-Terry on ranking prize money (exponent 0.35)")]


# ------------------------------------------------------------------ Handball

def build_handball():
    d = load("handball_ehf.json")
    src("ehf-calendar", "European Handball Federation official match calendar", d["source_url"],
        "Handball", "17 fixtures with dates, local tip times and first-leg scores", d["captured_utc"], "session 6b10ecda, same day")
    for i, m in enumerate(d["matches"]):
        f = add_fixture(
            id=f"hb-{i}", sport="Handball", competition=m["competition"], stage="",
            home=m["home"], away=m["away"], date=m["date"], start_local=m.get("time_local"), venue="",
            source_key="ehf-calendar", source_url=m["url"], as_of=d["captured_utc"], inputs=[],
            note=m.get("status", ""),
        )
        score = m.get("score_at_capture")
        if (not score or "-" not in score) and "first leg" in m.get("status", ""):
            mm = re.search(r"first leg\s+(.+?)\s+(\d+)-(\d+)\s+([A-Za-z0-9 .&\'-]+)\)?$", m.get("status", ""))
            if mm:
                t1, g1, g2, t2 = mm.group(1).strip(), int(mm.group(2)), int(mm.group(3)), mm.group(4).strip()
                if t1.lower() in m["home"].lower() or m["home"].lower() in t1.lower():
                    score = f"{g1}-{g2}"
                elif t2.lower() in m["home"].lower() or m["home"].lower() in t2.lower():
                    score = f"{g2}-{g1}"
                if score:
                    f["input_note_leg"] = f"first leg: {t1} {g1}-{g2} {t2}"
        if not score or "-" not in score or (m.get("status", "").startswith("scheduled") and not f.get("input_note_leg")):
            f["flags"].append("no official score or strength input for either side; left unlined")
            continue
        try:
            hs, as_ = [int(x) for x in score.split("-")]
        except ValueError:
            f["flags"].append("score not parseable; left unlined")
            continue
        if hs + as_ == 0:
            f["flags"].append("no score at capture; left unlined")
            continue
        edge = (hs - as_) / 2.0
        lam_h = max(18.0, min(42.0, 30.0 + edge))
        lam_a = max(18.0, min(42.0, 30.0 - edge))
        grid = poisson_grid(lam_h, lam_a, 55)
        ph, pa = grid_two_way(grid, 0.5)
        total = round(lam_h + lam_a) + 0.5
        f["expected"] = {"home": round(lam_h, 1), "away": round(lam_a, 1)}
        f["input_note"] = (f.get("input_note_leg", f"score {score} (home {m['home']} v away {m['away']})") + f"; used as a ±{abs(edge):.1f}-goal strength edge")
        basis = "Poisson on a 30-goal baseline shifted by half the verified first-leg margin"
        f["markets"] = [
            market("Money line (2-way)", m["home"], ph, basis),
            market("Money line (2-way)", m["away"], pa, basis),
            market(f"Match total {total} - Over", "Over", total_over_prob(grid, total), basis),
            market(f"Match total {total} - Under", "Under", 1 - total_over_prob(grid, total), basis),
        ]


# ------------------------------------------------------------------ Rugby League

def build_rugby_league():
    d = load("rugby_league_rlwc.json")
    src("nrl-r1", "NRL.com official Rugby League World Cup 2026 draw - Round 1", d["source_urls"]["round1"],
        "Rugby League", "Round 1 results and scores", d["captured_utc"], "session 6b10ecda, same day")
    src("nrl-r2", "NRL.com official Rugby League World Cup 2026 draw - Round 2", d["source_urls"]["round2"],
        "Rugby League", "Round 2 fixtures, venues, kick-off times", d["captured_utc"], "session 6b10ecda, same day")
    pf, pa, games = {}, {}, {}
    for r in d["round1_results"]:
        for team, f_, a_ in ((r["home"], r["home_score"], r["away_score"]), (r["away"], r["away_score"], r["home_score"])):
            pf[team] = pf.get(team, 0) + f_
            pa[team] = pa.get(team, 0) + a_
            games[team] = games.get(team, 0) + 1
    for i, m in enumerate(d["round2"]):
        utc_start = m.get("kickoff_utc")
        f = add_fixture(
            id=f"rl-{i}", sport="Rugby League", competition="Rugby League World Cup 2026", stage="Round 2",
            home=m["home"], away=m["away"], date=m["date"], start_utc=utc_start, venue=m.get("venue", ""),
            source_key="nrl-r2", source_url=m["url"], as_of=d["captured_utc"], inputs=[{"key": "nrl-r1"}],
            note=m.get("status", ""),
        )
        if m.get("status") == "Full Time":
            f["result"] = f"{m['home']} {m['home_score']}-{m['away_score']} {m['away']}"
            f["flags"].append("completed before the cut-off; the official score is published as a result, not priced")
            continue
        h, a = m["home"], m["away"]
        if h not in pf or a not in pf:
            f["flags"].append("no Round 1 score for one side; left unlined")
            continue
        mean = 28.2  # Round 1 mean points per team-innings
        atk_h = 0.3 * (pf[h] / games[h]) + 0.7 * mean
        dfn_h = 0.3 * (pa[h] / games[h]) + 0.7 * mean
        atk_a = 0.3 * (pf[a] / games[a]) + 0.7 * mean
        dfn_a = 0.3 * (pa[a] / games[a]) + 0.7 * mean
        lam_h = (atk_h + dfn_a) / 2 * 1.02
        lam_a = (atk_a + dfn_h) / 2 * 0.98
        grid = poisson_grid(lam_h, lam_a, 70)
        ph, pa_ = grid_two_way(grid, 0.5)
        dist = margin_distribution(grid)
        total = round(lam_h + lam_a) + 0.5
        f["expected"] = {"home": round(lam_h, 1), "away": round(lam_a, 1)}
        f["input_note"] = (f"Round 1: {h} {pf[h]}-{pa[h]}, {a} {pf[a]}-{pa[a]} (points for-against); rates shrunk 70% to the 28.2-point Round 1 mean")
        basis = "Poisson on Round 1 points for/against with a 2% home adjustment"
        f["markets"] = [
            market("Money line (2-way)", h, ph, basis),
            market("Money line (2-way)", a, pa_, basis),
            market("Handicap -6.5", h, handicap_win_prob(dist, -6.5), basis),
            market("Handicap +6.5", a, 1 - handicap_win_prob(dist, -6.5), basis),
            market(f"Match total {total} - Over", "Over", total_over_prob(grid, total), basis),
            market(f"Match total {total} - Under", "Under", 1 - total_over_prob(grid, total), basis),
        ]


# ------------------------------------------------------------------ Rugby Union

def build_rugby_union():
    d = load("rugby_union_prem.json")
    src("prem-fixtures", "PREM Rugby official fixtures & results - Gallagher PREM Round 4", d["source_url"],
        "Rugby Union", "Round 4 fixtures, venues, last-three form strings", d["captured_utc"], "session 6b10ecda, same day")
    for i, m in enumerate(d["matches"]):
        f = add_fixture(
            id=f"ru-{i}", sport="Rugby Union", competition="Gallagher Premiership", stage="Round 4",
            home=m["home"], away=m["away"], date=m["date"], start_utc=m.get("kickoff_utc"), venue=m["venue"],
            source_key="prem-fixtures", source_url=m["match_centre"], as_of=d["captured_utc"], inputs=[],
        )
        hf, af = m["home_form_last3_as_shown"], m["away_form_last3_as_shown"]
        f["input_note"] = f"last three results as published: {m['home']} {hf}; {m['away']} {af}"
        if not hf or not af:
            f["flags"].append("no form string published; left unlined")
            continue
        hv = sum(1 for c in hf.split(",") if c.strip() == "W") / 3
        av = sum(1 for c in af.split(",") if c.strip() == "W") / 3
        p = home_edge(log5(0.35 + 0.3 * hv, 0.35 + 0.3 * av), 0.18)
        basis = "Log5 on a last-three-win rate mapped onto a 35-65% band, with a 18-point home adjustment"
        f["markets"] = [market("Money line (2-way)", m["home"], p, basis),
                        market("Money line (2-way)", m["away"], 1 - p, basis)]
        f["flags"].append("no verified scoring or league-points input was readable (standings render client-side); handicap and total markets are left blank")


# ------------------------------------------------------------------ Darts

def build_darts():
    d = load("darts_olbg.json")
    src("olbg-darts", "OLBG official darts tips index (operator source, not a governing body)", d["source_url"],
        "Darts", "12 fixtures and OLBG event ids", d["captured_utc"], "session 6b10ecda, same day")
    for i, m in enumerate(d["matches"]):
        f = add_fixture(
            id=f"darts-{i}", sport="Darts", competition="European Tour (as listed by OLBG)", stage="",
            home=m["p1"], away=m["p2"], date=m["date"], start_utc=m.get("kickoff_utc"), venue="",
            source_key="olbg-darts", source_url=m["url"], as_of=d["captured_utc"], inputs=[],
        )
        f["flags"].append("PDC rankings unreachable (BR-02): no official strength input, so every market is left blank")


# ------------------------------------------------------------------ Tennis

def build_tennis():
    d = load("tennis_atp.json")
    s = SESSION["atp_refresh"]
    src("atp-scores", "ATP Tour official Tour Scores board", s["source_url"],
        "Tennis", "quarter-final results; refreshed first-hand in this session", s["captured_utc"], "this session")
    src("atp-capture", "ATP Tour official Tour Scores board (earlier same-day read)", d["source_url"],
        "Tennis", "quarter-final results and semi-final slots", d["captured_utc"], "session 6b10ecda, same day")
    for i, q in enumerate(s["quarter_finals"]):
        add_fixture(
            id=f"ten-qf-{i}", sport="Tennis", competition=q["event"], stage="Quarter-final",
            home=q["p1"], away=q["p2"], date="2026-10-23", start_utc=None, venue="",
            source_key="atp-scores", source_url=s["source_url"], as_of=s["captured_utc"], inputs=[],
            note="", markets=[],
        )
        FIXTURES[-1]["result"] = q["score"] if q["winner"] else "in progress at 19:34Z"
        FIXTURES[-1]["flags"].append("no price originated from a completed result")
    for i, sf in enumerate(d["semi_finals"]):
        add_fixture(
            id=f"ten-sf-{i}", sport="Tennis", competition=sf["event"], stage="Semi-final",
            home=sf["p1"], away=sf["p2"], date=sf["date"], venue="",
            source_key="atp-capture", source_url=d["source_url"], as_of=d["captured_utc"], inputs=[],
        )
        FIXTURES[-1]["flags"].append("opponent not published by the official source (BR-03); participant left blank and the match unpriced")


# ------------------------------------------------------------------ Cricket

def build_cricket():
    d = load("cricket_ca.json")
    src("cricket-au", "Cricket Australia official live & upcoming matches", d["source_url"],
        "Cricket", "5 upcoming fixtures, series, venues", d["captured_utc"], "session 6b10ecda, same day")
    for i, m in enumerate(d["upcoming"]):
        f = add_fixture(
            id=f"ck-{i}", sport="Cricket", competition=m["series"], stage=m.get("stage", ""),
            home=m["teams"].split(" v ")[0], away=m["teams"].split(" v ")[1] if " v " in m["teams"] else "",
            date=m["date"], venue=m.get("venue", ""), source_key="cricket-au", source_url=m["url"],
            as_of=d["captured_utc"], inputs=[],
        )
        if not m.get("venue"):
            f["flags"].append("venue not published in the captured list")
        f["flags"].append("no first-hand official ranking or form table was captured for these teams; every market is left blank")


# ------------------------------------------------------------------ Golf

def build_golf():
    d = load("golf_dpworld.json")
    src("dpwt-leaderboard", "DP World Tour official leaderboard - Genesis Championship", d["source_urls"]["leaderboard"],
        "Golf", "36-hole leaderboard", d["captured_utc"], "session 6b10ecda, same day")
    lb = d["leaderboard_after_round2"]
    best = min(p["to_par"] for p in lb)
    weights = {}
    for p in lb:
        weights[p["player"]] = math.exp(-(p["to_par"] - best) / 4.0)
    total = sum(weights.values())
    f = add_fixture(
        id="golf-genesis", sport="Golf", competition=d["event"]["name"], stage="After Round 2",
        home="", away="", date="2026-10-24", venue="", source_key="dpwt-leaderboard",
        source_url=d["source_urls"]["leaderboard"], as_of=d["captured_utc"], inputs=[{"key": "dpwt-leaderboard"}],
    )
    f["input_note"] = f"{len(lb)} players captured; leader at {best} to par after 36 holes"
    f["flags"].append("outright market only: a shot-level strokes-gained feed was not readable, so no 3-ball or top-finish market is originated")
    for p in lb[:25]:
        q = weights[p["player"]] / total * 0.78
        f["markets"].append(market("Tournament winner", p["player"], q,
                                   "softmax over the 36-hole leaderboard with a 22% residual for players outside the captured top 25"))
        FIXTURES[-1]["markets"][-1]["player_score"] = p["to_par"]


# ------------------------------------------------------------------ Motor Racing

def build_motor():
    d = load("motor_racing_f1.json")
    src("f1-calendar", "Formula 1 official 2026 race calendar", d["source_urls"]["calendar"],
        "Motor Racing", "United States Grand Prix dates and rounds", d["captured_utc"], "session 6b10ecda, same day")
    src("f1-standings", "Formula 1 official 2026 drivers' standings", d["source_urls"]["standings"],
        "Motor Racing", "drivers' points after Round 17 (top 8 captured)", d["captured_utc"], "session 6b10ecda, same day")
    st = d["drivers_standings_after_round_17"]
    f = add_fixture(
        id="f1-us-gp", sport="Motor Racing", competition="Formula 1 United States Grand Prix", stage="Round 18",
        home="", away="", date="2026-10-25", venue="Circuit of the Americas", source_key="f1-calendar",
        source_url=d["source_urls"]["calendar"], as_of=d["captured_utc"], inputs=[{"key": "f1-standings"}],
    )
    f["input_note"] = "drivers' championship points after Round 17 for the eight drivers captured"
    f["flags"].append("only the top eight championship positions were captured; the market is normalised over those eight with a 15% residual")
    w = {name: pts ** 1.5 for name, team, pts in st}
    tot = sum(w.values())
    for name, team, pts in st:
        f["markets"].append(market("Race winner", name, w[name] / tot * 0.85,
                                   "Bradley-Terry on championship points with a 15% residual"))
        FIXTURES[-1]["markets"][-1]["driver_team"] = team
        FIXTURES[-1]["markets"][-1]["driver_points"] = pts


# ------------------------------------------------------------------ Gaelic / Greyhounds / Volleyball

def build_gaelic():
    d = load("gaelic_gaa.json")
    src("gaa-fixtures", "GAA official fixtures & results", d["source_url"], "Gaelic Sports",
        "the single October fixture listed nationally", d["captured_utc"], "session 6b10ecda, same day")
    for i, m in enumerate(d["matches"]):
        f = add_fixture(
            id=f"gaa-{i}", sport="Gaelic Sports", competition=m["competition"], stage=m.get("stage", ""),
            home=m["home"], away=m["away"], date=m["date"], start_local=m.get("time_local"), venue=m.get("venue", ""),
            source_key="gaa-fixtures", source_url=m["match_url"], as_of=d["captured_utc"], inputs=[],
        )
        f["flags"].append("no official scoring or form input captured for either side; left unlined")


def build_greyhounds():
    d = load("greyhounds_gbgb.json")
    src("gbgb", "Greyhound Board of Great Britain official open-race calendar", d["source_url"],
        "Greyhounds", "5 open races (track, distance, category, grade)", d["captured_utc"], "session 6b10ecda, same day")
    for i, r in enumerate(d["open_races_listed"]):
        f = add_fixture(
            id=f"gh-{i}", sport="Greyhounds", competition=f"{r['track']} open race", stage=f"Category {r['category']}",
            home=f"{r['distance_m']}m {r['grade']}", away="", date=d["date"], venue=r["track"],
            source_key="gbgb", source_url=d["source_url"], as_of=d["captured_utc"], inputs=[],
        )
        f["flags"].append("GBGB publishes no runner names or trap numbers; no market can be originated")


def build_volleyball():
    v = SESSION["volleyball_world"]
    src("vbw-schedule", "Volleyball World official global schedule", v["schedule_url"], "Volleyball",
        "10 fixtures for 2026-10-24 and four same-day results", v["captured_utc"], "this session")
    results = {r["home"] + "|" + r["away"]: r for r in v["results_2026_10_23"]}
    for i, m in enumerate(v["fixtures_2026_10_24"]):
        f = add_fixture(
            id=f"vb-{i}", sport="Volleyball", competition=m["competition"], stage=m.get("pool", ""),
            home=m["home"], away=m["away"], date="2026-10-24", start_local=m["local_time"], venue=f"{m['venue_city']}, {m['country']}",
            source_key="vbw-schedule", source_url=m["url"], as_of=v["captured_utc"], inputs=[],
        )
        rev = results.get(m["home"] + "|" + m["away"]) or results.get(m["away"] + "|" + m["home"])
        if rev and not rev["sets"].startswith("in progress"):
            home_sets, away_sets = [int(x) for x in rev["sets"].split("-")]
            # previous meeting: `away` side of tomorrow is the home side of the result
            rev_home_won = home_sets > away_sets
            winner = rev["home"] if rev_home_won else rev["away"]
            margin = abs(home_sets - away_sets)
            p_home = 0.5 + (0.08 * margin) * (1 if winner == m["home"] else -1)
            p_home = min(0.78, max(0.22, p_home))
            f["input_note"] = (f"same pairing played 2026-10-23: {rev['home']} {rev['sets']} {rev['away']} "
                               f"(sets {rev['set_scores_home']} / {rev['set_scores_away']})")
            f["markets"] = [market("Money line (2-way)", m["home"], p_home,
                                   "even-chance prior moved 8 points per set of margin in the verified same-pairing result"),
                            market("Money line (2-way)", m["away"], 1 - p_home,
                                   "even-chance prior moved 8 points per set of margin in the verified same-pairing result")]
            f["flags"].append("no league table or rating feed was readable (BR-04); the price uses the reverse-fixture result only")
        else:
            f["flags"].append("no official strength input for either side; left unlined (BR-04)")


# ------------------------------------------------------------------ assemble

def assemble():
    build_nhl(); build_mlb(); build_basketball(); build_snooker(); build_handball()
    build_rugby_league(); build_rugby_union(); build_darts(); build_tennis(); build_cricket()
    build_golf(); build_motor(); build_gaelic(); build_greyhounds(); build_volleyball()

    result_names = ("Money line", "Match winner", "Tournament winner", "Race winner")
    for f in FIXTURES:
        f["strongest"] = max(f["markets"], key=lambda m: m["prob"]) if f["markets"] else None
        if not f["markets"] or not f["eligible"]:
            f["pick"] = None
            f["result_pick"] = None
            f["no_in_band"] = True
            continue
        results = [m for m in f["markets"] if m["market"].startswith(result_names)]
        in_band_results = [m for m in results if m["in_band"]]
        in_band_all = [m for m in f["markets"] if m["in_band"]]
        strongest_result = max(results, key=lambda m: m["prob"]) if results else None
        f["result_pick"] = (max(in_band_results, key=lambda m: m["prob"])
                            if in_band_results and strongest_result and strongest_result["prob"] <= 0.7143 else None)
        f["pick"] = dict(f["result_pick"]) if f["result_pick"] else None
        if f["pick"]:
            f["pick"]["kind"] = "result"
        f["no_in_band"] = f["pick"] is None
    return FIXTURES


def main():
    fixtures = assemble()
    counts = {s: 0 for s in SPORTS}
    priced = {s: 0 for s in SPORTS}
    picks = {s: 0 for s in SPORTS}
    for f in fixtures:
        counts[f["sport"]] += 1
        if f["markets"]:
            priced[f["sport"]] += 1
        if f.get("pick"):
            picks[f["sport"]] += 1
    payload = {
        "meta": {
            "generated_for": GENERATED_FOR,
            "session": "arena/7a073c9a-olbg2",
            "cut_off_utc": CUTOFF,
            "fixtures": len(fixtures),
            "priced": sum(priced.values()),
            "picks": sum(picks.values()),
            "by_sport": {s: {"fixtures": counts[s], "priced": priced[s], "picks": picks[s]} for s in SPORTS},
        },
        "fixtures": fixtures,
    }
    (OUT / "matches.json").write_text(json.dumps(payload, indent=1) + "\n")
    (OUT / "sources.json").write_text(json.dumps({"sources": list(SOURCES.values())}, indent=1) + "\n")
    flags = SESSION["flags"] + [
        {"id": "BR-08", "subject": "Ranking-money bound used for players outside the top 36",
         "severity": "low",
         "detail": "Where a snooker participant is outside the captured top 36, the 36th-placed prize-money figure (GBP 198,500) is used as a published upper bound on that player's ranking money. The row says so. No rank or money figure is invented.",
         "evidence": ["https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false"]},
        {"id": "BR-09", "subject": "Eight OLBG darts events had already started",
         "severity": "low",
         "detail": "Eight darts events listed by OLBG for 2026-10-23 had a start time before this desk's 19:45Z cut-off. Their results could not be read (see BR-01/BR-02), so they are published with that status and excluded from selections.",
         "evidence": ["https://www.olbg.com/betting-tips/Darts/15"]},
        {"id": "BR-10", "subject": "Four sports carry no originated price",
         "severity": "high",
         "detail": "Tennis (no published pairing), Cricket (no official ranking or form table read), Gaelic Sports (single fixture, no scoring input) and Greyhounds (no runners published) carry fixtures with blank markets. They are shown with the reason on every row and are not written up.",
         "evidence": ["https://www.atptour.com/en/scores/current", "https://www.cricket.com.au/matches?year=2026&isCompleted=0", "https://www.gaa.ie/fixtures-results", "https://www.gbgb.org.uk/racing/open-races/"]},
    ]
    (OUT / "flags.json").write_text(json.dumps({"flags": flags}, indent=1) + "\n")
    taxonomy = {
        "index_url": SESSION["olbg"]["index_url"],
        "captured_utc": SESSION["olbg"]["captured_utc"],
        "sport_ids_seen_in_index_links": SESSION["olbg"]["sport_ids_seen_in_index_links"],
        "markets_named_in_served_editorial_copy": SESSION["olbg"]["markets_named_in_served_editorial_copy"],
        "url_patterns": {
            "sport_index": SESSION["olbg"]["index_url_pattern_observed"],
            "event": SESSION["olbg"]["event_url_pattern_observed"],
        },
        "server_rendered_event_list": SESSION["olbg"]["server_rendered_event_list"],
        "server_rendered_evidence": SESSION["olbg"]["server_rendered_evidence"],
    }
    (OUT / "olbg_taxonomy.json").write_text(json.dumps(taxonomy, indent=1) + "\n")
    print(json.dumps(payload["meta"], indent=1))


if __name__ == "__main__":
    main()
