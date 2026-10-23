#!/usr/bin/env python3
"""Signal desk (session 6b10ecda) - turn captured official data into rows.

Reads only data/signal/captures/*.json (first-hand captures of official
sources) and writes:

    data/signal/matches.json      every fixture we publish, with our prices
    data/signal/predictions.json  the written-up selections
    data/signal/flagged.json      every irregularity / unverifiable value
    data/signal/sources.json      one entry per official source used

Nothing is inferred: a fixture with no official numeric input is published
with a blank selection and a flag instead of a guessed price.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signal_model import (american_odds, apply_home_edge, bradley_terry,  # noqa: E402
                          clamp, conditional_field, confidence, decimal_odds,
                          fmt_american, handicap_cover, in_focus_band, log5,
                          margin_model, normal_handicap, normal_total_over,
                          poisson_match, pythagorean, round_line, shrink,
                          total_over)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = os.path.join(ROOT, "data", "signal", "captures")
OUT = os.path.join(ROOT, "data", "signal")
GENERATED_FOR = "2026-10-23"
DESK = "signal (session 6b10ecda)"

FLAGS = []
SOURCES = {}


def cap(name):
    with open(os.path.join(CAP, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def flag(fid, sport, subject, detail, source_url, severity="medium"):
    FLAGS.append({"id": fid, "sport": sport, "subject": subject,
                  "detail": detail, "source_url": source_url,
                  "severity": severity})


def source(key, name, url, sport, used_for):
    SOURCES[key] = {"key": key, "name": name, "url": url, "sport": sport,
                    "used_for": used_for}


def price(p):
    p = clamp(p)
    return {"prob": round(p, 4), "american": fmt_american(p),
            "decimal": decimal_odds(p), "in_band": in_focus_band(p),
            "confidence": confidence(p)}


def market(name, selection, p, note=""):
    d = {"market": name, "selection": selection, "note": note}
    d.update(price(p))
    return d


def make_match(mid, sport, competition, event, start, venue, source_url,
               inputs, markets, pick, flags=None, status="upcoming",
               extra=None):
    row = {"id": mid, "sport": sport, "competition": competition,
           "event": event, "start_utc": start, "venue": venue,
           "source_url": source_url, "inputs": inputs, "markets": markets,
           "pick": pick, "flags": flags or [], "status": status}
    if extra:
        row.update(extra)
    return row


MATCHES = []


# ---------------------------------------------------------------- ICE HOCKEY

def build_ice_hockey():
    summary = cap("nhl_team_summary_20262027.json")
    fixtures = cap("nhl_fixtures.json")
    source("nhl-summary", "NHL Stats API - team summary 2026-27",
           summary["source_url"], "Ice Hockey",
           "goals for / goals against / points% per team")
    for d, u in fixtures["source_urls"].items():
        source("nhl-sched-" + d, f"NHL Web API - schedule {d}", u, "Ice Hockey",
               "fixture list, start times, venues")

    teams = {t[0]: dict(zip(summary["fields"][1:], t[1:]))
             for t in summary["teams"]}
    gp = sum(t["gamesPlayed"] for t in teams.values())
    gf = sum(t["goalsFor"] for t in teams.values())
    league_gpg = gf / float(gp)

    for g in fixtures["games"]:
        home, away = g["home"], g["away"]
        th, ta = teams.get(home), teams.get(away)
        mid = "nhl-%s" % g["id"]
        if not th or not ta:
            flag("SG-NHL-%s" % g["id"], "Ice Hockey", f"{away} @ {home}",
                 "Team not present in the official season summary feed, so no "
                 "price is published.", g["gamecenter"])
            MATCHES.append(make_match(
                mid, "Ice Hockey", "NHL regular season",
                f"{away} @ {home}", g["startUTC"], g["venue"], g["gamecenter"],
                "", [], None, ["missing official team stats"]))
            continue
        ah = shrink(th["goalsFor"] / th["gamesPlayed"], league_gpg, th["gamesPlayed"])
        dh = shrink(th["goalsAgainst"] / th["gamesPlayed"], league_gpg, th["gamesPlayed"])
        aa = shrink(ta["goalsFor"] / ta["gamesPlayed"], league_gpg, ta["gamesPlayed"])
        da = shrink(ta["goalsAgainst"] / ta["gamesPlayed"], league_gpg, ta["gamesPlayed"])
        lam_h = (ah * da / league_gpg) * 1.05
        lam_a = (aa * dh / league_gpg) * 0.95
        m = poisson_match(lam_h, lam_a)
        exp_total = lam_h + lam_a
        tline = round_line(exp_total)
        if abs(tline - exp_total) < 1e-9:
            tline += 0.5
        p_over = total_over(m["total"], tline)
        mk = [
            market("Win match (money line)", home, m["p_home"]),
            market("Win match (money line)", away, m["p_away"]),
            market("Regulation result", f"{home} in 60 minutes", m["p_home_reg"]),
            market("Regulation result", f"{away} in 60 minutes", m["p_away_reg"]),
            market("Regulation result", "Tie after 60 minutes", m["p_tie_reg"]),
            market("Puck line -1.5", home, handicap_cover(m["margin"], -1.5)),
            market("Puck line +1.5", away, 1 - handicap_cover(m["margin"], -1.5)),
            market("Match total %.1f" % tline, "Over", p_over),
            market("Match total %.1f" % tline, "Under", 1 - p_over),
        ]
        best = max([(m["p_home"], home), (m["p_away"], away)])
        pick = price(best[0])
        pick["selection"] = best[1]
        pick["market"] = "Win match (money line)"
        inputs = ("%s %d-%d-%d, %.2f GF/game, %.2f GA/game; %s %d-%d-%d, "
                  "%.2f GF/game, %.2f GA/game (official season summary, %d and %d "
                  "games played)") % (
            home, th["wins"], th["losses"], th["otLosses"],
            th["goalsFor"] / th["gamesPlayed"], th["goalsAgainst"] / th["gamesPlayed"],
            away, ta["wins"], ta["losses"], ta["otLosses"],
            ta["goalsFor"] / ta["gamesPlayed"], ta["goalsAgainst"] / ta["gamesPlayed"],
            th["gamesPlayed"], ta["gamesPlayed"])
        MATCHES.append(make_match(
            mid, "Ice Hockey", "NHL regular season", f"{away} @ {home}",
            g["startUTC"], g["venue"], g["gamecenter"], inputs, mk, pick,
            extra={"home": home, "away": away,
                   "exp_score": "%.2f - %.2f" % (lam_h, lam_a)}))


# ------------------------------------------------------------------ BASEBALL

def build_baseball():
    mlb = cap("mlb.json")
    for k, u in mlb["source_urls"].items():
        source("mlb-" + k, "MLB Stats API - " + k, u, "Baseball",
               "World Series schedule and 2026 regular-season run totals")
    rs = mlb["regular_season_2026"]
    rays, brew = rs["Tampa Bay Rays"], rs["Milwaukee Brewers"]
    p_rays = pythagorean(rays["runsScored"], rays["runsAllowed"])
    p_brew = pythagorean(brew["runsScored"], brew["runsAllowed"])
    for g in mlb["games"]:
        home, away = g["home"], g["away"]
        ph = p_brew if home.startswith("Milwaukee") else p_rays
        pa = p_brew if away.startswith("Milwaukee") else p_rays
        base = log5(ph, pa)
        p_home = apply_home_edge(base, 1.08)
        hrs = brew if home.startswith("Milwaukee") else rays
        ars = brew if away.startswith("Milwaukee") else rays
        lam_h = ((hrs["runsScored"] + ars["runsAllowed"]) / 2.0) / 162.0 * 1.04
        lam_a = ((ars["runsScored"] + hrs["runsAllowed"]) / 2.0) / 162.0 * 0.96
        m = poisson_match(lam_h, lam_a, ot_split=True)
        exp_total = lam_h + lam_a
        tline = round_line(exp_total)
        if abs(tline - exp_total) < 1e-9:
            tline += 0.5
        p_over = total_over(m["total"], tline)
        mk = [
            market("Win match (money line)", home, p_home),
            market("Win match (money line)", away, 1 - p_home),
            market("Run line -1.5", home, handicap_cover(m["margin"], -1.5, ot_split=False)),
            market("Run line +1.5", away, 1 - handicap_cover(m["margin"], -1.5, ot_split=False)),
            market("Match total %.1f" % tline, "Over", p_over),
            market("Match total %.1f" % tline, "Under", 1 - p_over),
        ]
        pick = price(max(p_home, 1 - p_home))
        pick["selection"] = home if p_home >= 0.5 else away
        pick["market"] = "Win match (money line)"
        inputs = ("Milwaukee 103-59, 832 runs scored / 618 allowed; Tampa Bay "
                  "98-64, 736 scored / 650 allowed (official 2026 regular-season "
                  "standings). Pythagorean win rates %.3f and %.3f combined with "
                  "log5 and an 8%% home-odds edge." % (p_brew, p_rays))
        if g["ifNecessary"] == "Y":
            fl = ["Game is listed by MLB as 'if necessary' - it may never be played."]
        else:
            fl = []
        MATCHES.append(make_match(
            "mlb-%s" % g["gamePk"], "Baseball", "MLB World Series 2026",
            f"{away} @ {home} ({g['description']})", g["startUTC"], g["venue"],
            "https://www.mlb.com/scores/" + g["date"], inputs, mk, pick, fl,
            extra={"home": home, "away": away,
                   "exp_score": "%.2f - %.2f" % (lam_h, lam_a)}))
    flag("SG-MLB1", "Baseball", "Run distribution",
         "Run totals are priced from a Poisson distribution; real baseball run "
         "scoring is slightly over-dispersed, so totals and run-line prices are "
         "marginally conservative at the extremes.",
         mlb["source_urls"]["schedule"], "low")


# ---------------------------------------------------------------- BASKETBALL

def build_basketball():
    el = cap("basketball_euroleague.json")
    source("el-schedule", "EuroLeague official feed - Round 8 schedule",
           el["source_urls"]["schedule_round8"], "Basketball", "fixtures, venues")
    source("el-standings", "EuroLeague official feed - standings after Round 7",
           el["source_urls"]["standings_after_round7"], "Basketball",
           "games played, wins, points for, points against")
    st = {r["team"]: r for r in el["standings_after_round7"]}
    hca = 3.0
    for f in el["fixtures_round8"]:
        home, away = f["home"], f["away"]
        th, ta = st[home], st[away]
        off_h, def_h = th["pf"] / th["gp"], th["pa"] / th["gp"]
        off_a, def_a = ta["pf"] / ta["gp"], ta["pa"] / ta["gp"]
        exp_h = (off_h + def_a) / 2.0 + hca / 2.0
        exp_a = (off_a + def_h) / 2.0 - hca / 2.0
        mm = margin_model(exp_h - exp_a, 11.5)
        line = round_line(-(exp_h - exp_a))
        exp_total = exp_h + exp_a
        tline = round_line(exp_total)
        p_cover = normal_handicap(mm["exp_margin"], 11.5, line)
        p_over = normal_total_over(exp_total, 15.0, tline)
        mk = [
            market("Win match (2-way)", home, mm["p_home"]),
            market("Win match (2-way)", away, mm["p_away"]),
            market("Handicap %+0.1f" % line, home, p_cover),
            market("Handicap %+0.1f" % (-line), away, 1 - p_cover),
            market("Match total %.1f" % tline, "Over", p_over),
            market("Match total %.1f" % tline, "Under", 1 - p_over),
        ]
        pick = price(max(mm["p_home"], mm["p_away"]))
        pick["selection"] = home if mm["p_home"] >= mm["p_away"] else away
        pick["market"] = "Win match (2-way)"
        inputs = ("%s %d-%d after %d games, %.1f points for / %.1f against per "
                  "game; %s %d-%d after %d games, %.1f for / %.1f against "
                  "(official standings after Round 7). Home edge 3.0 points, "
                  "margin sigma 11.5.") % (
            home, th["w"], th["l"], th["gp"], off_h, def_h,
            away, ta["w"], ta["l"], ta["gp"], off_a, def_a)
        MATCHES.append(make_match(
            "el-%s" % f["game_code"], "Basketball", "EuroLeague Round 8",
            f"{home} v {away}", f["date"] + " (time as served: %s)" % f["time_as_served"],
            f["venue"], el["source_urls"]["schedule_round8"], inputs, mk, pick,
            extra={"home": home, "away": away,
                   "exp_score": "%.1f - %.1f" % (exp_h, exp_a)}))
    flag("SG-BK1", "Basketball", "NBA fixtures unavailable",
         "Three official NBA endpoints were attempted (cdn.nba.com todaysScoreboard, "
         "stats.nba.com scoreboardv3, core-api.nba.com gamecardfeed); all returned "
         "HTTP 500 or were refused through the fetch proxy, so no NBA fixture is "
         "published today. Basketball coverage is EuroLeague only.",
         "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json")
    flag("SG-BK2", "Basketball", "Round 8 kick-off times",
         "EuroLeague's feed serves two clock fields per fixture without a timezone "
         "label; the calendar date is published and the raw time is shown as served, "
         "not converted to UTC.", el["source_urls"]["schedule_round8"], "low")


# -------------------------------------------------------------- RUGBY LEAGUE

def build_rugby_league():
    rl = cap("rugby_league_rlwc.json")
    source("rlwc-r1", "NRL.com official RLWC 2026 draw - Round 1",
           rl["source_urls"]["round1"], "Rugby League", "Round 1 results")
    source("rlwc-r2", "NRL.com official RLWC 2026 draw - Round 2",
           rl["source_urls"]["round2"], "Rugby League", "Round 2 fixtures and results")

    pf, pa, games = {}, {}, {}
    def add(team, scored, conceded):
        pf[team] = pf.get(team, 0) + scored
        pa[team] = pa.get(team, 0) + conceded
        games[team] = games.get(team, 0) + 1
    for r in rl["round1_results"]:
        add(r["home"], r["home_score"], r["away_score"])
        add(r["away"], r["away_score"], r["home_score"])
    for r in rl["round2"]:
        if r.get("status") == "Full Time":
            add(r["home"], r["home_score"], r["away_score"])
            add(r["away"], r["away_score"], r["home_score"])

    # true home nations in this round (venue in the listed country)
    home_nation = {"Papua New Guinea": True, "New Zealand": True,
                   "Australia": True, "England": False}
    CAP_DIFF = 30.0
    PRIOR = 2.0  # shrink one- and two-game samples towards an even contest

    def diff(team):
        raw = max(-CAP_DIFF, min(CAP_DIFF, (pf[team] - pa[team]) / games[team]))
        return raw * games[team] / (games[team] + PRIOR)

    for r in rl["round2"]:
        if r.get("status") != "Upcoming":
            continue
        home, away = r["home"], r["away"]
        dh = diff(home)
        da = diff(away)
        hca = 4.0 if home_nation.get(home) else 0.0
        mm = margin_model(dh - da + hca, 16.0)
        line = round_line(-(dh - da + hca))
        exp_total = (pf[home] / games[home] + pa[away] / games[away]) / 2.0 + \
                    (pf[away] / games[away] + pa[home] / games[home]) / 2.0
        tline = round_line(exp_total)
        p_cover = normal_handicap(mm["exp_margin"], 16.0, line)
        p_over = normal_total_over(exp_total, 18.0, tline)
        mk = [
            market("Win match (2-way)", home, mm["p_home"]),
            market("Win match (2-way)", away, mm["p_away"]),
            market("Handicap %+0.1f" % line, home, p_cover),
            market("Handicap %+0.1f" % (-line), away, 1 - p_cover),
            market("Match total %.1f" % tline, "Over", p_over),
            market("Match total %.1f" % tline, "Under", 1 - p_over),
        ]
        pick = price(max(mm["p_home"], mm["p_away"]))
        pick["selection"] = home if mm["p_home"] >= mm["p_away"] else away
        pick["market"] = "Win match (2-way)"
        inputs = ("%s %d points for / %d against in %d World Cup match(es); %s "
                  "%d for / %d against in %d. Venue %s%s. Per-game differential "
                  "capped at +/-30 and shrunk by games/(games+2) because the "
                  "sample is one or two matches; margin sigma 16.") % (
            home, pf[home], pa[home], games[home], away, pf[away], pa[away],
            games[away], r["venue"],
            "" if hca else " (neutral for both nations, no home edge applied)")
        fl = []
        if home == "Australia" and away == "Fiji":
            fl.append("The only official inputs are one World Cup match each: "
                      "Australia beat New Zealand 24-22 while Fiji beat the Cook "
                      "Islands 40-12. On those two results alone the margin calculation "
                      "makes Fiji the side with the better published differential, "
                      "which runs against conventional expectation for this fixture. "
                      "The row is published as the data reads and flagged (SG-RL1).")
        if away == "France":
            fl.append("France's only data point is a 78-4 defeat to Samoa; the "
                      "per-game differential is capped at -30 so the price is "
                      "deliberately conservative.")
        MATCHES.append(make_match(
            "rlwc-%s" % r["url"].rstrip("/").split("/")[-1], "Rugby League",
            "Rugby League World Cup 2026, Round 2", f"{home} v {away}",
            r.get("kickoff_utc", r["date"]), r["venue"], r["url"], inputs, mk,
            pick, fl, extra={"home": home, "away": away,
                             "exp_score": "%.1f - %.1f" % (
                                 (exp_total + mm["exp_margin"]) / 2,
                                 (exp_total - mm["exp_margin"]) / 2)}))


# --------------------------------------------------------------- RUGBY UNION

def _rl_flags():
    flag("SG-RL1", "Rugby League", "One- and two-match samples drive every price",
         "The Rugby League World Cup is two rounds old, so each nation has one or "
         "two official results. Differentials are capped at +/-30 points and shrunk "
         "towards zero, but Australia v Fiji still prices Fiji as the side with the "
         "stronger published differential. No world ranking or squad list was "
         "readable to temper that, so the row carries this flag.",
         "https://www.nrl.com/draw/?competition=131&round=1&season=2026", "high")


def build_rugby_union():
    ru = cap("rugby_union_prem.json")
    source("prem-r4", "PREM Rugby official fixtures & results, Round 4",
           ru["source_url"], "Rugby Union", "fixtures, venues, last-three form")
    for m in ru["matches"]:
        fh = m["home_form_last3_as_shown"].count("W")
        fa = m["away_form_last3_as_shown"].count("W")
        exp_margin = 3.5 * (fh - fa) + 5.0
        mm = margin_model(exp_margin, 13.0)
        line = round_line(-exp_margin)
        p_cover = normal_handicap(exp_margin, 13.0, line)
        exp_total = 50.0
        p_over = normal_total_over(exp_total, 17.0, 50.5)
        mk = [
            market("Win match (2-way)", m["home"], mm["p_home"]),
            market("Win match (2-way)", m["away"], mm["p_away"]),
            market("Handicap %+0.1f" % line, m["home"], p_cover),
            market("Handicap %+0.1f" % (-line), m["away"], 1 - p_cover),
        ]
        pick = price(max(mm["p_home"], mm["p_away"]))
        pick["selection"] = m["home"] if mm["p_home"] >= mm["p_away"] else m["away"]
        pick["market"] = "Win match (2-way)"
        inputs = ("%s last three %s, %s last three %s (official PREM fixtures "
                  "page). Flat home edge 5.0 points, 3.5 points per win of form "
                  "difference, margin sigma 13.0.") % (
            m["home"], m["home_form_last3_as_shown"], m["away"],
            m["away_form_last3_as_shown"])
        MATCHES.append(make_match(
            "prem-%s" % m["match_centre"].rstrip("/").split("/")[-2],
            "Rugby Union", "Gallagher PREM Round 4",
            "%s v %s" % (m["home"], m["away"]), m["kickoff_utc"], m["venue"],
            m["match_centre"], inputs, mk, pick,
            ["No league table was readable (SG-RU1), so form and venue are the "
             "only inputs; no match total is published."],
            extra={"home": m["home"], "away": m["away"]}))
    flag("SG-RU1", "Rugby Union", "PREM standings not readable",
         "https://www.premrugby.com/standings renders its league table client-side "
         "and served no table rows, so league points, points for and points against "
         "could not be used. Rugby union prices rest on published last-three form "
         "plus a flat home edge and are deliberately close to even money.",
         "https://www.premrugby.com/standings")
    flag("SG-TZ1", "Rugby Union / Rugby League / Darts",
         "Kick-off times rendered in the viewer's timezone",
         "premrugby.com, nrl.com and olbg.com all render kick-off times in the "
         "viewer's local zone. The fetch proxy resolved to US Eastern (UTC-4), so "
         "every time on this desk was converted with UTC = served time + 4h. UK "
         "readers should treat the UTC column as authoritative.",
         "https://www.premrugby.com/fixtures-results?competition=gallagher-prem&round=4",
         "low")
    flag("SG-RU2", "Rugby Union", "Sixth Round 4 fixture",
         "The PREM Round 4 page listed six fixtures; five were captured first-hand "
         "with form strings. The sixth row was truncated in the captured chunk and "
         "is therefore not published rather than being reconstructed.",
         "https://www.premrugby.com/fixtures-results?competition=gallagher-prem&round=4",
         "low")


# -------------------------------------------------------------------- HANDBALL

def build_handball():
    hb = cap("handball_ehf.json")
    source("ehf-calendar", "European Handball Federation official calendar",
           hb["source_url"], "Handball", "fixtures, first-leg results")
    for m in hb["matches"]:
        if m.get("status", "").startswith("finished"):
            continue
        mid = "ehf-" + m["url"].rstrip("/").split("/")[-2]
        home, away = m["home"], m["away"]
        start = m["date"] + (" " + m.get("time_local", "") if m.get("time_local") else "")
        if home == "MRK Sloga Doboj" and away == "Kur":
            # official first leg: Kur 26-38 MRK Sloga Doboj (away win by 12)
            neutral = 12.0 + 3.0           # remove the away disadvantage
            exp_margin = neutral + 3.0      # add the home edge for leg two
            mm = margin_model(exp_margin, 7.0)
            line = round_line(-exp_margin)
            p_cover = normal_handicap(exp_margin, 7.0, line)
            exp_total = 64.0
            p_over = normal_total_over(exp_total, 9.0, 64.5)
            mk = [
                market("Win match (2-way)", home, mm["p_home"]),
                market("Win match (2-way)", away, mm["p_away"]),
                market("Handicap %+0.1f" % line, home, p_cover),
                market("Handicap %+0.1f" % (-line), away, 1 - p_cover),
                market("Match total 64.5", "Over", p_over),
                market("Match total 64.5", "Under", 1 - p_over),
                market("Tie winner (aggregate)", home,
                       normal_handicap(exp_margin + 12.0, 7.0, 0.0)),
            ]
            pick = price(mm["p_home"])
            pick["selection"] = home
            pick["market"] = "Win match (2-way)"
            inputs = ("Official first leg: Kur 26-38 MRK Sloga Doboj - a 12-goal "
                      "away win, 64 total goals. Leg two reverses venue: +3 goals "
                      "for losing the away disadvantage, +3 for the home edge, "
                      "margin sigma 7.0.")
            MATCHES.append(make_match(
                mid, "Handball", m["competition"], f"{home} v {away}", start,
                "", m["url"], inputs, mk, pick,
                extra={"home": home, "away": away,
                       "exp_score": "%.1f - %.1f" % ((exp_total + exp_margin) / 2,
                                                     (exp_total - exp_margin) / 2)}))
            continue
        MATCHES.append(make_match(
            mid, "Handball", m["competition"], f"{home} v {away}", start, "",
            m["url"], "", [], None,
            ["No official rating, table or previous result was published for "
             "either club on the EHF calendar, so no price is originated "
             "(SG-HB1)."]))
    flag("SG-HB1", "Handball", "No club ratings published",
         "The EHF match calendar lists fixtures but no club standings, ratings or "
         "head-to-head records. Only the one tie with an official first-leg result "
         "(Kur 26-38 MRK Sloga Doboj) carries a numeric input; the other sixteen "
         "fixtures are published with blank selections.", hb["source_url"])


# --------------------------------------------------------------------- SNOOKER

def build_snooker():
    wst = cap("snooker_wst.json")
    rank = cap("snooker_rankings_full.json")
    source("wst-fixtures", "World Snooker Tour official live & upcoming matches",
           wst["source_url"], "Snooker", "fixtures, rounds, match centres")
    source("wst-rankings", "World Snooker Tour official world ranking list",
           rank["source_url"], "Snooker", "ranking prize money per player")
    money = rank["world_ranking_gbp_top36"]
    bound = min(money.values())
    import math as _math
    for m in wst["matches"]:
        p1, p2 = m["p1"], m["p2"]
        mid = "wst-" + m["match_centre"].rstrip("/").split("/")[-1][:8]
        start = "%s %s" % (m["date"], m.get("time_local", ""))
        undetermined = any(x.lower().startswith(("winner of", "wildcard"))
                           for x in (p1, p2))
        if undetermined:
            MATCHES.append(make_match(
                mid, "Snooker", m["event"] + " - " + m["round"],
                f"{p1} v {p2}", start, "", m["match_centre"], "", [], None,
                ["At least one participant is undetermined, so no selection is "
                 "published (SG-SN1)."]))
            continue
        f1 = money.get(p1)
        f2 = money.get(p2)
        bounded = []
        if f1 is None:
            f1, _ = bound, bounded.append(p1)
        if f2 is None:
            f2, _ = bound, bounded.append(p2)
        if p1 not in money and p2 not in money:
            MATCHES.append(make_match(
                mid, "Snooker", m["event"] + " - " + m["round"],
                f"{p1} v {p2}", start, "", m["match_centre"], "", [], None,
                ["Neither player appears in the captured top-36 ranking table, so "
                 "there is no official numeric input and no selection is published "
                 "(SG-SN2)."]))
            continue
        p = bradley_terry(_math.log(f1), _math.log(f2), 1.1)
        mk = [market("Win match (2-way)", p1, p),
              market("Win match (2-way)", p2, 1 - p)]
        pick = price(max(p, 1 - p))
        pick["selection"] = p1 if p >= 0.5 else p2
        pick["market"] = "Win match (2-way)"
        inputs = ("Ranking prize money: %s GBP %s, %s GBP %s (official world "
                  "ranking list). Logistic comparison of the natural logarithms, "
                  "k = 1.1.") % (p1, format(f1, ","), p2, format(f2, ","))
        fl = []
        for b in bounded:
            fl.append("%s sits outside the captured top 36, so GBP %s - the 36th "
                      "placed figure - is used as an upper bound on their ranking "
                      "money; the favourite's probability is therefore a lower "
                      "bound (SG-SN2)." % (b, format(bound, ",")))
        MATCHES.append(make_match(
            mid, "Snooker", m["event"] + " - " + m["round"], f"{p1} v {p2}",
            start, "", m["match_centre"], inputs, mk, pick, fl,
            extra={"home": p1, "away": p2}))
    flag("SG-SN1", "Snooker", "Undetermined participants",
         "Several Northern Ireland Open and International Championship ties still "
         "list 'Winner of match n' or 'Wildcard n'. Those rows are published as "
         "fixtures with blank selections.", wst["source_url"], "low")
    flag("SG-SN2", "Snooker", "Ranking table truncated at 36th place",
         rank["cutoff_note"], rank["source_url"])
    flag("SG-SN3", "Snooker", "Ranking money as the only strength input",
         "Ranking prize money is a two-year rolling figure, not a form measure, and "
         "match length (best of 11 in the Belfast semi-finals) is not priced in "
         "separately. Snooker prices are therefore shaded towards the middle.",
         rank["source_url"], "low")


# ------------------------------------------------------------------- CRICKET

def build_cricket():
    cr = cap("cricket_ca.json")
    source("ca-matches", "Cricket Australia official live & upcoming matches",
           cr["source_url"], "Cricket", "fixture list, venues, official results")
    for m in cr["upcoming"]:
        mid = "cri-" + m["url"].rstrip("/").split("/")[-1][:26]
        if m["teams"] == "India Women v Zimbabwe Women":
            # official input: 1st ODI won by 9 wickets with 22.5 overs to spare
            overs_spare = 22.5
            runs_equiv = overs_spare * 5.3
            p = min(0.80, 0.5 + 0.0025 * runs_equiv)
            mk = [market("Win match (2-way)", "India Women", p),
                  market("Win match (2-way)", "Zimbabwe Women", 1 - p)]
            pick = price(p)
            pick["selection"] = "India Women"
            pick["market"] = "Win match (2-way)"
            inputs = ("Official 1st ODI: Zimbabwe Women 197 all out in 49.5 overs, "
                      "India Women 1-200 in 27.1 overs - a nine-wicket win with 22.5 "
                      "overs unused. Converted at 5.3 runs per unused over to %.0f "
                      "runs of dominance, scaled at 0.0025 per run and capped at "
                      "0.80." % runs_equiv)
            MATCHES.append(make_match(
                mid, "Cricket", m["series"] + " - " + m.get("stage", ""),
                m["teams"], m["date"], m.get("venue", ""), m["url"], inputs, mk,
                pick, ["Start time not published in a labelled timezone (SG-CR1).",
                       "Calendar date truncated in the captured chunk (SG-CR2)."],
                extra={"home": "India Women", "away": "Zimbabwe Women"}))
            continue
        MATCHES.append(make_match(
            mid, "Cricket", m["series"] + (" - " + m["stage"] if m.get("stage") else ""),
            m["teams"], m["date"], m.get("venue", ""), m["url"], "", [], None,
            ["No official team-strength figures (standings, net run rate or "
             "head-to-head) were published on the captured source for this "
             "fixture, so no selection is originated (SG-CR3)."]))
    flag("SG-CR1", "Cricket", "Unlabelled start times", cr["timezone_note"],
         cr["source_url"], "low")
    flag("SG-CR2", "Cricket", "Truncated date for India Women v Zimbabwe Women 2nd ODI",
         "The calendar date for the second women's ODI was cut off in the captured "
         "chunk; the fixture is published without a confirmed date rather than with "
         "an assumed one.", cr["upcoming"][-1]["url"], "low")
    flag("SG-CR3", "Cricket", "No published strength inputs for four fixtures",
         "Cricket Australia's match list publishes fixtures but no standings or net "
         "run rate, and the ICC fixtures page is client-side rendered. Only the "
         "women's ODI series, where an official first-match result exists, carries "
         "a price.", "https://www.icc-cricket.com/fixtures-results")


# ---------------------------------------------------------------------- GOLF

def build_golf():
    gf = cap("golf_dpworld.json")
    source("dpwt-leaderboard", "DP World Tour official leaderboard - Genesis Championship",
           gf["source_urls"]["leaderboard"], "Golf",
           "36-hole scores for the captured top 25")
    source("dpwt-schedule", "DP World Tour official schedule",
           gf["source_urls"]["schedule"], "Golf", "event status, week 40 of 42")
    import math as _math
    weights = {}
    best = min(p["to_par"] for p in gf["leaderboard_after_round2"])
    for p in gf["leaderboard_after_round2"]:
        weights[p["player"]] = _math.exp(-0.55 * (p["to_par"] - best))
    probs = conditional_field(weights)
    mk = [market("Outright winner (conditional on the captured top 25)", k, v)
          for k, v in sorted(probs.items(), key=lambda kv: -kv[1])]
    top = mk[0]
    pick = {k: top[k] for k in ("prob", "american", "decimal", "in_band", "confidence")}
    pick["selection"] = top["selection"]
    pick["market"] = "Outright winner (conditional)"
    inputs = ("36-hole scores from the official leaderboard; win weight = exp(-0.55 "
              "x strokes behind the lead) over the 25 captured players, normalised "
              "so the prices are conditional on the winner coming from that group.")
    MATCHES.append(make_match(
        "golf-genesis-2026", "Golf", "DP World Tour - Genesis Championship 2026",
        "Genesis Championship, Rounds 3-4", "2026-10-24", "Korea",
        gf["source_urls"]["leaderboard"], inputs, mk, pick,
        ["Prices are conditional on the winner coming from the captured top 25 "
         "after 36 holes; players outside that group are not priced (SG-GO1)."],
        extra={"kind": "outright"}))
    flag("SG-GO1", "Golf", "Conditional outright field",
         "Only the top 25 after 36 holes were captured from the official leaderboard. "
         "Rather than invent a probability for the rest of the field, golf prices are "
         "published as conditional on the winner coming from those 25 players and are "
         "labelled as such on every row.", gf["source_urls"]["leaderboard"])
    flag("SG-GO2", "Golf", "No two-way match market",
         "There is no head-to-head golf market this week on the official schedule, so "
         "golf contributes one outright market rather than five match previews.",
         gf["source_urls"]["schedule"], "low")


# -------------------------------------------------------------- MOTOR RACING

def build_motor_racing():
    f1 = cap("motor_racing_f1.json")
    source("f1-calendar", "Formula 1 official race calendar 2026",
           f1["source_urls"]["calendar"], "Motor Racing", "round order and dates")
    source("f1-standings", "Formula 1 official drivers' standings 2026",
           f1["source_urls"]["standings"], "Motor Racing",
           "championship points after round 17")
    weights = {d[0]: d[2] ** 1.6 for d in f1["drivers_standings_after_round_17"]}
    probs = conditional_field(weights)
    mk = [market("Race winner (conditional on the captured top 8)", k, v)
          for k, v in sorted(probs.items(), key=lambda kv: -kv[1])]
    top = mk[0]
    pick = {k: top[k] for k in ("prob", "american", "decimal", "in_band", "confidence")}
    pick["selection"] = top["selection"]
    pick["market"] = "Race winner (conditional)"
    inputs = ("Championship points after round 17 (Antonelli 340, Russell 238, "
              "Hamilton 229, Verstappen 221, Leclerc 215, Norris 201, Piastri 138, "
              "Hadjar 97). Win weight = points^1.6, normalised across the eight "
              "drivers published in the captured chunk.")
    MATCHES.append(make_match(
        "f1-usgp-2026", "Motor Racing", "Formula 1 - United States Grand Prix (round 18)",
        "United States Grand Prix", "2026-10-25", "Circuit of the Americas",
        f1["source_urls"]["standings"], inputs, mk, pick,
        ["Prices are conditional on a winner from the eight drivers whose points "
         "were captured; drivers from P9 down are not priced (SG-MR1).",
         "Qualifying had not taken place at capture time, so grid position is not "
         "an input (SG-MR2)."], extra={"kind": "outright"}))
    flag("SG-MR1", "Motor Racing", "Standings table truncated at P8",
         "The official drivers' standings chunk that was read first-hand ends at "
         "Isack Hadjar in eighth. Drivers below that have no captured points total, "
         "so the race-winner market is published as conditional on the top eight.",
         f1["source_urls"]["standings"])
    flag("SG-MR2", "Motor Racing", "No grid or practice data",
         "Free practice and qualifying results for round 18 were not published at "
         "capture time, so the price uses season-long championship points only and "
         "cannot react to weekend pace.", f1["source_urls"]["calendar"], "low")


# -------------------------------------------------------------- GAELIC SPORTS

def build_gaelic():
    ga = cap("gaelic_gaa.json")
    source("gaa-fixtures", "GAA official fixtures & results",
           ga["source_url"], "Gaelic Sports", "fixture list")
    for m in ga["matches"]:
        MATCHES.append(make_match(
            "gaa-" + m["match_url"].rstrip("/").split("/")[-1][:8], "Gaelic Sports",
            m["competition"] + " - " + m["stage"],
            "%s v %s" % (m["home"], m["away"]),
            "%s %s" % (m["date"], m.get("time_local", "")), m["venue"],
            m["match_url"], "", [], None,
            ["The GAA publishes no rating, table or previous result for this "
             "one-off international, so no price is originated (SG-GA1)."]))
    flag("SG-GA1", "Gaelic Sports", "Single fixture, no numeric inputs",
         "The GAA national fixtures page listed exactly one fixture in the window - "
         "the Shinty-Hurling International final - and publishes no form, table or "
         "head-to-head data for it. The fixture is listed with a blank selection.",
         ga["source_url"])


# --------------------------------------------------------------------- DARTS

def build_darts():
    dt = cap("darts_olbg.json")
    source("olbg-darts", "OLBG darts event index (operator source, not a "
           "governing body)", dt["source_url"], "Darts",
           "fixture list and event ids")
    for m in dt["matches"]:
        MATCHES.append(make_match(
            "darts-%s" % m["olbg_event_id"], "Darts",
            "PDC European Championship week (competition name not confirmed by the "
            "governing body)", "%s v %s" % (m["p1"], m["p2"]),
            m["kickoff_utc"], "", m["url"], "", [], None,
            ["No PDC-published draw, average or Order of Merit figure could be read, "
             "so this row has an operator source and no originated price (SG-DA1)."]))
    flag("SG-DA1", "Darts", "PDC site unreadable through the fetch proxy",
         dt["flag_text"], "https://www.pdc.tv/calendar/")


# ---------------------------------------------------------------- GREYHOUNDS

def build_greyhounds():
    gh = cap("greyhounds_gbgb.json")
    source("gbgb-open", "GBGB official open races calendar", gh["source_url"],
           "Greyhounds", "open race meetings for 23 October 2026")
    for i, r in enumerate(gh["open_races_listed"], 1):
        MATCHES.append(make_match(
            "gbgb-%d" % i, "Greyhounds", "GBGB open race - " + r["category"],
            "%s %dm (%s)" % (r["track"], r["distance_m"], r["grade"]),
            gh["date"], r["track"], gh["source_url"], "", [], None,
            ["GBGB publishes no runners, trap numbers or race time for this heat in "
             "the served page, so there is no field to price (SG-GH1)."]))
    flag("SG-GH1", "Greyhounds", "No runners published", gh["flag_text"],
         gh["source_url"])


# ----------------------------------------------------------------- VOLLEYBALL

def build_volleyball():
    vb = cap("volleyball_cev.json")
    source("cev-home", "European Volleyball Confederation official site",
           vb["source_urls"]["cev_home"], "Volleyball",
           "confirmation that CEV Champions League qualification is under way")
    flag("SG-VB1", "Volleyball", "No readable fixture list", vb["flag_text"],
         vb["source_urls"]["cev_home"], "high")


# --------------------------------------------------------------------- TENNIS

def build_tennis():
    tn = cap("tennis_atp.json")
    source("atp-scores", "ATP Tour official scoreboard", tn["source_url"],
           "Tennis", "quarter-final results and live states")
    source("atp-draw", "ATP Tour official tournament draw index",
           tn["draw_source_url"], "Tennis", "event list and draw structure")
    for i, q in enumerate(tn["quarter_finals"], 1):
        seeds = []
        if q["p1_seed"]:
            seeds.append("%s seeded %d" % (q["p1"], q["p1_seed"]))
        if q["p2_seed"]:
            seeds.append("%s seeded %d" % (q["p2"], q["p2_seed"]))
        MATCHES.append(make_match(
            "atp-qf-%d" % i, "Tennis", "ATP %s - %s" % (q["event"], q["round"]),
            "%s v %s" % (q["p1"], q["p2"]), "2026-10-23", q["event"],
            q["stats_url"], "; ".join(seeds), [], None,
            ["Published as an official result, not as a selection: the match was "
             "%s when the scoreboard was read (%s)." % (q["state"], q["result"])],
            status="result", extra={"result": q["result"]}))
    for i, sf in enumerate(tn["semi_finals"], 1):
        MATCHES.append(make_match(
            "atp-sf-%d" % i, "Tennis", "ATP %s - %s" % (sf["event"], sf["round"]),
            "%s v %s" % (sf["p1"], sf["p2"]), sf["date"], sf["event"],
            tn["source_url"], "", [], None,
            ["The opponent is not published on the official scoreboard yet, so no "
             "selection is originated (SG-TE1)."]))
    for f in tn.get("flags", []):
        flag(f["id"], "Tennis", f["subject"], f["detail"], f["source_url"],
             f.get("severity", "medium"))


# ----------------------------------------------------------------------- main

def main():
    build_ice_hockey()
    build_baseball()
    build_basketball()
    build_rugby_league()
    _rl_flags()
    build_rugby_union()
    build_handball()
    build_snooker()
    build_cricket()
    build_golf()
    build_motor_racing()
    build_gaelic()
    build_darts()
    build_greyhounds()
    build_volleyball()
    build_tennis()

    flag("SG-INJ1", "All sports", "No official injury feed was readable",
         "None of the official sources captured today publish a machine-readable "
         "injury or availability list for the fixtures covered here. Write-ups "
         "therefore state only what the official source published about "
         "availability, and never assert an injury that has not been read "
         "first-hand.", "https://www.olbg.com/", "medium")
    flag("CR-01", "Repository", "Unresolved merge-conflict markers in COORDINATION.md",
         "COORDINATION.md on main contains three unresolved conflict regions "
         "(around lines 3216-3307, 3437-3549 and 3609-3628, the last tagged "
         "'>>>>>>> 140baf3'). The file is append-only and shared by concurrent "
         "sessions, so this desk logged the defect rather than rewriting another "
         "session's text.",
         "https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md", "high")

    prose_path = os.path.join(OUT, "prose.json")
    prose = {}
    if os.path.exists(prose_path):
        with open(prose_path, "r", encoding="utf-8") as fh:
            prose = json.load(fh)

    predictions = []
    for m in MATCHES:
        if not m["pick"]:
            continue
        text = prose.get(m["id"], "")
        predictions.append({
            "id": m["id"], "sport": m["sport"], "competition": m["competition"],
            "event": m["event"], "start_utc": m["start_utc"],
            "selection": m["pick"]["selection"], "market": m["pick"]["market"],
            "prob": m["pick"]["prob"], "american": m["pick"]["american"],
            "decimal": m["pick"]["decimal"], "confidence": m["pick"]["confidence"],
            "in_band": m["pick"]["in_band"], "source_url": m["source_url"],
            "write_up": text, "words": len(text.split()),
        })

    meta = {"generated_for": GENERATED_FOR, "desk": DESK,
            "matches": len(MATCHES), "priced": len(predictions)}
    with open(os.path.join(OUT, "matches.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "matches": MATCHES}, fh, indent=1)
    with open(os.path.join(OUT, "predictions.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "predictions": predictions}, fh, indent=1)
    with open(os.path.join(OUT, "flagged.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "flags": FLAGS}, fh, indent=1)
    with open(os.path.join(OUT, "sources.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "sources": sorted(SOURCES.values(),
                                                   key=lambda s: (s["sport"], s["key"]))},
                  fh, indent=1)
    print("matches=%d priced=%d flags=%d sources=%d" %
          (len(MATCHES), len(predictions), len(FLAGS), len(SOURCES)))


if __name__ == "__main__":
    main()
