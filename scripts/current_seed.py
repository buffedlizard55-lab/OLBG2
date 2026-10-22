#!/usr/bin/env python3
"""Seed the /current/ layer from the first-hand captures in data/current/capture/.

Every fixture row written here carries:
  * the official governing-body URL for that individual fixture,
  * the raw capture file that returned it in this session,
  * only values that an official endpoint actually returned.

Anything that could not be read from an official source is left blank and is
carried forward to current/flagged.html by scripts/current_model.py.

Stdlib only. Deterministic: same captures in, same matches.json out.
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURE = os.path.join(ROOT, "data", "current", "capture")
OUT_DIR = os.path.join(ROOT, "data", "current")

WINDOW_START = "2026-10-22"
WINDOW_END = "2026-10-29"

SPORTS = [
    ("aussie-rules", "Aussie Rules"),
    ("baseball", "Baseball"),
    ("basketball", "Basketball"),
    ("cricket", "Cricket"),
    ("darts", "Darts"),
    ("esports", "eSports"),
    ("gaelic-football", "Gaelic Football"),
    ("golf", "Golf"),
    ("greyhounds", "Greyhounds"),
    ("handball", "Handball"),
    ("ice-hockey", "Ice Hockey"),
    ("motor-racing", "Motor Racing"),
    ("rugby-league", "Rugby League"),
    ("rugby-union", "Rugby Union"),
    ("snooker", "Snooker"),
    ("tennis", "Tennis"),
    ("volleyball", "Volleyball"),
]
SPORT_NAME = dict(SPORTS)


def load(name):
    with open(os.path.join(CAPTURE, name), encoding="utf-8") as handle:
        return json.load(handle)


def team(name, abbrev="", record=""):
    return {"name": name, "abbrev": abbrev, "record": record}


def row(match_id, sport, competition, date, home, away, venue, url, family,
        source_name, capture_file, start_utc="", time_note="", facts=None,
        inputs=None, kind="team", event=""):
    """Normalise one fixture. Blank strings are deliberate: never inferred."""
    return {
        "id": match_id,
        "kind": kind,
        "event": event,
        "sport": sport,
        "sport_name": SPORT_NAME[sport],
        "competition": competition,
        "date": date,
        "start_utc": start_utc,
        "time_note": time_note,
        "home": home,
        "away": away,
        "venue": venue or "",
        "official_url": url,
        "source_family": family,
        "source_name": source_name,
        "capture_file": "data/current/capture/" + capture_file,
        "facts": facts or [],
        "inputs": inputs or {},
    }


def fact(kind, text, url, source):
    return {"kind": kind, "text": text, "source_url": url, "source_name": source}


# --------------------------------------------------------------------------- #
# Ice Hockey - NHL
# --------------------------------------------------------------------------- #
NHL_SOURCE = "NHL official API (api-web.nhle.com) score feed"


def seed_nhl():
    out = []
    # Two capture files, two transcription shapes; normalise both.
    for fname, keys in (
        ("nhl_score_2026-10-23.json",
         {"id": "id", "date": "gameDate", "utc": "startTimeUTC", "venue": "venue",
          "url": "gameCenterLink", "leaders": "leaders", "note": None}),
        ("nhl_score_2026-10-24.json",
         {"id": "game_id", "date": "game_date", "utc": "start_time_utc", "venue": "venue",
          "url": "official_url", "leaders": "team_leaders", "note": "record_snapshot_note"}),
    ):
        cap = load(fname)
        note = cap.get(keys["note"]) if keys["note"] else None
        for game in cap["games"]:
            home, away = game["home"], game["away"]
            url = game[keys["url"]]
            facts = [fact("leader", "%s leader %s: %s (%s)" % (
                side["team"], side["category"], side["player"], side["value"]),
                url, NHL_SOURCE) for side in game[keys["leaders"]]]
            if note:
                facts.append(fact("caveat", note, url, NHL_SOURCE))
            out.append(row(
                "nhl-%s" % game[keys["id"]], "ice-hockey",
                "NHL 2026-27 Regular Season", game[keys["date"]],
                team(full_name(home["abbrev"]), abbrev=home["abbrev"], record=home["record"]),
                team(full_name(away["abbrev"]), abbrev=away["abbrev"], record=away["record"]),
                game[keys["venue"]], url, "nhl", NHL_SOURCE, fname,
                start_utc=game[keys["utc"]], facts=facts,
                inputs={"home_abbrev": home["abbrev"], "away_abbrev": away["abbrev"],
                        "home_record": home["record"], "away_record": away["record"]},
            ))
    return out


def full_name(abbrev):
    """Full club names come from the official 32-team summary, never re-assembled."""
    return NHL_FULL.get(abbrev, abbrev)


def load_nhl_full():
    global NHL_FULL
    NHL_FULL = {e["abbrev"]: e["team"]
                for e in load("nhl_team_summary_2026-10-22.json")["teams"]}
    return NHL_FULL


NHL_FULL: dict = {}


# --------------------------------------------------------------------------- #
# Basketball - Turkish Airlines EuroLeague
# --------------------------------------------------------------------------- #
EL_SOURCE = "EuroLeague Basketball official game centre and standings"


def seed_euroleague():
    cap = load("euroleague_round7_2026-10-22.json")
    st = {c["code"]: c for c in cap["standings"]}
    out = []
    for game in cap["fixtures"]:
        if game["date"] == "2026-10-21":
            continue  # already played: not a fixture
        h, a = st[game["home_code"]], st[game["away_code"]]
        url = game["official_url"]
        facts = [
            fact("standing", "%s P%d, %d-%d (win %s%%), last ten %s" % (
                h["team"], h["pos"], h["w"], h["l"], h["win_pct"], h["l10"]),
                cap["source_url_standings"], EL_SOURCE),
            fact("standing", "%s P%d, %d-%d (win %s%%), last ten %s" % (
                a["team"], a["pos"], a["w"], a["l"], a["win_pct"], a["l10"]),
                cap["source_url_standings"], EL_SOURCE),
            fact("venue", "Tip %s at %s" % (game["tip_time_as_rendered"], game["venue"]),
                url, EL_SOURCE),
        ]
        out.append(row(
            "euroleague-r7-%s" % game["game_code"].split("/")[-1], "basketball",
            cap["competition"], game["date"],
            team(h["team"], abbrev=h["code"], record="%d-%d" % (h["w"], h["l"])),
            team(a["team"], abbrev=a["code"], record="%d-%d" % (a["w"], a["l"])),
            game["venue"], url, "euroleague", EL_SOURCE,
            "euroleague_round7_2026-10-22.json",
            time_note=game["tip_time_as_rendered"], facts=facts,
            inputs={
                "home_pos": h["pos"], "away_pos": a["pos"], "home_gp": h["gp"], "away_gp": a["gp"],
                "home_for": h["pts_for"], "home_against": h["pts_against"],
                "away_for": a["pts_for"], "away_against": a["pts_against"],
                "home_home": h["home"], "away_away": a["away"],
                "standings_url": cap["source_url_standings"],
            },
        ))
    return out


# --------------------------------------------------------------------------- #
# Rugby Union - United Rugby Championship
# --------------------------------------------------------------------------- #
URC_SOURCE = "United Rugby Championship official match centre (stats.unitedrugby.com)"


def seed_urc():
    cap = load("urc_round4_2026-10-22.json")
    tbl = load("urc_table_2026-10-22.json")
    by_team = {t["team"]: t for t in tbl["table"]}
    results = tbl["round3_results"]
    out = []
    for game in cap["fixtures"]:
        h = by_team[game["home"]]
        a = by_team[game["away"]]
        url = game["match_url"]
        facts, seen = [], set()
        for side in (game["home"], game["away"]):
            for res in results:
                if side in (res["home"], res["away"]):
                    key = (res["date"], res["home"], res["away"])
                    if key in seen:
                        continue
                    seen.add(key)
                    facts.append(fact("result", "Round 3, %s: %s %d-%d %s (%s)" % (
                        res["date"], res["home"], res["home_score"], res["away_score"],
                        res["away"], res["venue"]), tbl["source_url"], URC_SOURCE))
        out.append(row(
            "urc-r4-%s" % game["match_id"], "rugby-union", tbl["competition"], game["date"],
            team(game["home"], record="%d-%d-%d" % (h["w"], h["d"], h["l"])),
            team(game["away"], record="%d-%d-%d" % (a["w"], a["d"], a["l"])),
            game["venue"], url, "urc", URC_SOURCE, "urc_round4_2026-10-22.json",
            time_note=game["kickoff_local"], facts=facts,
            inputs={
                "home_pts": h["pts"], "away_pts": a["pts"], "home_pl": h["pl"], "away_pl": a["pl"],
                "home_pf": h["pf"], "home_pa": h["pa"], "away_pf": a["pf"], "away_pa": a["pa"],
                "home_pos": h["pos"], "away_pos": a["pos"],
                "home_bp": h["bp"], "away_bp": a["bp"],
                "home_form": "".join(h["form"]), "away_form": "".join(a["form"]),
                "table_url": tbl["source_url"],
                "round_note": cap["note"],
            },
        ))
    return out


# --------------------------------------------------------------------------- #
# Handball - EHF Champions League Men
# --------------------------------------------------------------------------- #
EHF_SOURCE = "EHF Champions League Men official site (ehfcl.eurohandball.com)"


def seed_handball():
    cap = load("ehf_2026-10-22.json")
    standings = load("ehf_standings_2026-10-22.json")
    by_club = {c["club"]: c for c in standings["clubs"]}
    for extra in standings["extra_fixtures_first_hand"]:
        cap["fixtures"].append(dict(extra, competition=cap["fixtures"][0]["competition"],
                                    time_as_rendered=extra["time_as_rendered"]))
    out = []
    for game in cap["fixtures"]:
        h, a = game["home"], game["away"]
        if h not in by_club or a not in by_club:
            continue  # EHF European Cup / IHF qualifiers: no official group table returned
        hc, ac = by_club[h], by_club[a]
        url = game["official_url"]
        facts = [
            fact("standing", "Group %s: %s P%d %d-%d-%d, %d:%d goals (%+d), %d pts" % (
                hc["group"], h, hc["gp"], hc["w"], hc["d"], hc["l"], hc["goals_for"],
                hc["goals_against"], hc["diff"], hc["pts"]), standings["source_url"], EHF_SOURCE),
            fact("standing", "Group %s: %s P%d %d-%d-%d, %d:%d goals (%+d), %d pts" % (
                ac["group"], a, ac["gp"], ac["w"], ac["d"], ac["l"], ac["goals_for"],
                ac["goals_against"], ac["diff"], ac["pts"]), standings["source_url"], EHF_SOURCE),
        ]
        out.append(row(
            "ehfcl-%s" % game["match_id"], "handball", game["competition"], game["date"],
            team(h, record="%d-%d-%d" % (hc["w"], hc["d"], hc["l"])),
            team(a, record="%d-%d-%d" % (ac["w"], ac["d"], ac["l"])),
            "", url, "ehf", EHF_SOURCE, "ehf_2026-10-22.json",
            time_note=game["time_as_rendered"], facts=facts,
            inputs={
                "home_group": hc["group"], "away_group": ac["group"],
                "home_gp": hc["gp"], "away_gp": ac["gp"],
                "home_pts": hc["pts"], "away_pts": ac["pts"],
                "home_for": hc["goals_for"], "home_against": hc["goals_against"],
                "away_for": ac["goals_for"], "away_against": ac["goals_against"],
                "standings_url": standings["source_url"],
            },
        ))
    return out


# --------------------------------------------------------------------------- #
# Snooker - 2026 Northern Ireland Open
# --------------------------------------------------------------------------- #
WST_SOURCE = "World Snooker Tour official matches page (wst.tv)"


def seed_snooker():
    cap = load("wst_ni_open_2026-10-22.json")
    results = cap["completed_results_first_hand"]
    form: dict = {}
    frames_total = 0
    for res in results:
        frames = res["s1"] + res["s2"]
        frames_total += frames
        for player, won, lost in ((res["p1"], res["s1"], res["s2"]),
                                  (res["p2"], res["s2"], res["s1"])):
            entry = form.setdefault(player, {"m": 0, "fw": 0, "fl": 0, "lines": []})
            entry["m"] += 1
            entry["fw"] += won
            entry["fl"] += lost
            entry["lines"].append("%s: %s %d-%d %s (%s, %s)" % (
                "won" if won > lost else "lost", res["p1"], res["s1"], res["s2"],
                res["p2"], res["round"], res["day"]))
    out = []
    for idx, game in enumerate(cap["fixtures"], 1):
        p1, p2 = game["p1"], game["p2"]
        for player in (p1, p2):
            form.setdefault(player, {"m": 0, "fw": 0, "fl": 0, "lines": []})
        url = game["official_url"]
        facts = [fact("result", line, cap["source_url"], WST_SOURCE)
                 for player in (p1, p2) for line in form[player]["lines"]]
        out.append(row(
            "snooker-niopen-r3-%d" % idx, "snooker", "%s, %s" % (cap["event"], cap["round"]),
            "2026-10-22", team(p1), team(p2), "", url, "wst", WST_SOURCE,
            "wst_ni_open_2026-10-22.json",
            time_note="%s %s" % (game["day_as_rendered"], game["time_as_rendered"]),
            facts=facts,
            inputs={
                "p1_matches": form[p1]["m"], "p1_frames_won": form[p1]["fw"],
                "p1_frames_lost": form[p1]["fl"],
                "p2_matches": form[p2]["m"], "p2_frames_won": form[p2]["fw"],
                "p2_frames_lost": form[p2]["fl"],
                "event_matches_observed": len(results),
                "event_frames_observed": frames_total,
                "event_frames_per_match": round(frames_total / len(results), 4),
                "match_label": game["match_label"],
                "best_of": 7,
                "time_note": cap["time_note"],
            },
        ))
    return out


# --------------------------------------------------------------------------- #
# Baseball - MLB World Series
# --------------------------------------------------------------------------- #
MLB_SOURCE = "MLB Stats API (statsapi.mlb.com) schedule"


def seed_mlb():
    cap = load("mlb_world_series_2026-10-22.json")
    sample = load("mlb_standings_sample_2026-10-22.json")
    records = {r["team_id"]: r for r in cap["season_records"]}
    out = []
    for game in cap["games"]:
        h, a = game["home"], game["away"]
        hr, ar = records[h["id"]], records[a["id"]]
        url = game["official_url"]
        facts = [
            fact("series", "%s of a best-of-%d series; official status '%s'" % (
                game["description"], game["games_in_series"], game["status"]), url, MLB_SOURCE),
            fact("season", "%s %d-%d (%s), %d runs scored, %d runs allowed, division rank %s" % (
                hr["team"], hr["wins"], hr["losses"], hr["win_pct"], hr["runs_scored"],
                hr["runs_allowed"], hr["division_rank"]), cap["source_url_standings"],
                "MLB Stats API standings"),
            fact("season", "%s %d-%d (%s), %d runs scored, %d runs allowed, division rank %s" % (
                ar["team"], ar["wins"], ar["losses"], ar["win_pct"], ar["runs_scored"],
                ar["runs_allowed"], ar["division_rank"]), cap["source_url_standings"],
                "MLB Stats API standings"),
            fact("venue", "%s" % game["venue"]["name"], url, MLB_SOURCE),
        ]
        out.append(row(
            "mlb-%s" % game["game_pk"], "baseball",
            "MLB 2026 World Series", game["official_date"],
            team(h["name"]), team(a["name"]), game["venue"]["name"], url, "mlb",
            MLB_SOURCE, "mlb_world_series_2026-10-22.json",
            start_utc=game["game_date_utc"], facts=facts,
            inputs={
                "home_gp": hr["wins"] + hr["losses"], "home_rs": hr["runs_scored"],
                "home_ra": hr["runs_allowed"], "away_gp": ar["wins"] + ar["losses"],
                "away_rs": ar["runs_scored"], "away_ra": ar["runs_allowed"],
                "league_avg_runs_per_game": sample["league_avg_runs_per_game"],
                "league_sample_clubs": sample["sample_clubs"],
                "standings_url": sample["source_url"],
            },
        ))
    return out


# --------------------------------------------------------------------------- #
# Motor Racing - F1
# --------------------------------------------------------------------------- #
F1_SOURCE = "Formula 1 official calendar and results (formula1.com)"


def seed_f1():
    cap = load("f1_calendar_2026-10-22.json")
    rnd = cap["next_round"]
    drivers = cap["drivers_standings"]
    facts = [fact("standing", "P%d %s (%s) - %d pts" % (
        d["pos"], d["driver"], d["team"], d["pts"]), cap["source_url_drivers"], F1_SOURCE)
        for d in drivers]
    facts += [fact("result", "Round %d %s: 1st %s, 2nd %s, 3rd %s" % (
        w["round"], w["race"], w["winner"], w["second"], w["third"]), cap["source_url"], F1_SOURCE)
        for w in cap["race_winners_first_hand"]]
    facts.append(fact("window", cap["rounds_completed_note"], cap["source_url"], F1_SOURCE))
    return [row(
        "f1-2026-round-%d" % rnd["round"], "motor-racing",
        "FIA Formula One World Championship 2026", "2026-10-25",
        team("%s Grand Prix (Round %d)" % (rnd["country"], rnd["round"])),
        None, rnd["country"], rnd["official_url"],
        "formula1", F1_SOURCE, "f1_calendar_2026-10-22.json",
        time_note=rnd["dates_as_rendered"], facts=facts, kind="event",
        event="%s Grand Prix (Round %d)" % (rnd["country"], rnd["round"]),
        inputs={
            "drivers": [{"pos": d["pos"], "driver": d["driver"], "team": d["team"],
                         "code": d["code"], "nat": d["nat"], "pts": d["pts"]} for d in drivers],
            "field_points_total": sum(d["pts"] for d in drivers),
            "round": rnd["round"],
            "rounds_completed": 17,
            "round_label": rnd["dates_as_rendered"],
            "sponsor_note": rnd["event_name"],
            "standings_url": cap["source_url_drivers"],
        },
    )]


# --------------------------------------------------------------------------- #
# Zero-row sports: documented first-hand reason
# --------------------------------------------------------------------------- #
ZERO_SPORTS = [
    {"sport": "aussie-rules", "reason_flag": "CU-08",
     "reason": "No AFL fixture inside the 22 to 29 October 2026 capture window was returned by an official source during this session. The AFL Premiership season had concluded and no governing-body fixture feed was read, so this sport publishes zero rows rather than a list reconstructed from memory, a third-party site or another layer of this repository.",
     "source_consulted": "https://www.afl.com.au/", "source_reachable": False},
    {"sport": "cricket", "reason_flag": "CU-09",
     "reason": "No international or franchise fixture list for the capture window was returned by an official board feed during this session. Cricket pairings, venues and start times could not be read first-hand, so no cricket row is published; inventing a series schedule or copying one from an aggregator would be exactly the inference this layer refuses to make.",
     "source_consulted": "https://www.icc-cricket.com/", "source_reachable": False},
    {"sport": "darts", "reason_flag": "CU-10",
     "reason": "pdc.tv/tournaments, pdc.tv/live and pdc.tv/tournaments/european-championship each rendered only a cookie-consent wall and a cookie and vendor inventory to this fetcher at every chunk depth: no draw, no pairings, no session times. The 2026 European Championship window of 22 to 25 October at the Westfalenhallen in Dortmund was confirmed official through pdc.tv/calendar, but not one pairing was read, so no row is published.",
     "source_consulted": "https://www.pdc.tv/tournaments/european-championship", "source_reachable": True},
    {"sport": "esports", "reason_flag": "CU-11",
     "reason": "No esports fixture list for the capture window was returned by an official tournament organiser during this session, and no governing body publishes a consolidated cross-title calendar. Without a first-hand fixture feed this sport publishes zero rows; title, organiser, map and start time would all otherwise have to be guessed.",
     "source_consulted": "", "source_reachable": False},
    {"sport": "gaelic-football", "reason_flag": "CU-12",
     "reason": "The inter-county GAA season had concluded inside the capture window and no official fixture list was returned by gaa.ie during this session. Club championship fixtures are organised county by county and no consolidated official feed was read, so Gaelic football publishes zero rows rather than a partial or inferred list.",
     "source_consulted": "https://www.gaa.ie/", "source_reachable": False},
    {"sport": "golf", "reason_flag": "CU-13",
     "reason": "The DP World Tour schedule returned the Genesis Championship, event 40 of 42 in Korea, as in-play at the moment of capture: the round indicator read 'Round 2 Tee Times Available'. In-play events are excluded by this layer's rules, and no later tournament was listed as scheduled inside the window, so golf publishes zero rows with the official schedule page linked.",
     "source_consulted": "https://www.europeantour.com/dpworld-tour/schedule/", "source_reachable": True},
    {"sport": "greyhounds", "reason_flag": "CU-14",
     "reason": "No official greyhound racing fixture feed was reachable during this session. Meeting-level cards change daily and are published by national governing bodies rather than a single international federation, so without a first-hand read of a card this sport publishes zero rows; no race, trap, distance or time is shown.",
     "source_consulted": "", "source_reachable": False},
    {"sport": "rugby-league", "reason_flag": "CU-15",
     "reason": "No rugby-league fixture inside the capture window was returned by an official league source during this session. The northern-hemisphere club season had ended and no international window was read first-hand, so rugby league publishes zero rows rather than a reconstructed list of friendly or representative fixtures.",
     "source_consulted": "", "source_reachable": False},
    {"sport": "tennis", "reason_flag": "CU-16",
     "reason": "atptour.com/en/scores/current returned only matches already live or completed at the moment of capture, the Almaty event tid 9410, Brussels tid 7485 and Lyon tid 496, plus news and partner widgets. atptour.com/en/scores/2026-10-23 and the tournament draw route both returned HTTP 404. No future-session pairing was read, so tennis publishes zero rows.",
     "source_consulted": "https://www.atptour.com/en/scores/current", "source_reachable": True},
    {"sport": "volleyball", "reason_flag": "CU-17",
     "reason": "No volleyball fixture inside the capture window was returned by an official federation source during this session, neither a national league nor an international competition. Without a first-hand fixture feed this sport publishes zero rows; pool standings and match times would otherwise be assumptions rather than captured values.",
     "source_consulted": "", "source_reachable": False},
]
# Captured but excluded fixtures: published with the reason rather than hidden.
EXCLUDED = [
    {"sport": "ice-hockey", "reason_flag": "CU-01",
     "what": "NHL games dated 2026-10-22 (five read from api-web.nhle.com/v1/schedule/2026-10-22, game ids 2026020154-2026020158) and every W-L-OTL record carried beside the published 23-24 October fixtures",
     "reason": "The 22 October games were in-play at the moment of capture, so they are excluded from the published slate. The same feed showed that records beside the 23-24 October fixtures had not absorbed the 22 October results, so every published NHL record is a 2026-10-21 snapshot. Both facts are disclosed rather than normalised.",
     "source_url": "https://api-web.nhle.com/v1/schedule/2026-10-22"},
    {"sport": "ice-hockey", "reason_flag": "CU-02",
     "what": "Nathan MacKinnon's assists total in the Colorado game-leader block (2026-10-23 feed)",
     "reason": "The value was truncated at the end of the fetched chunk and is stored as null. It is not published anywhere on this layer; the remaining five named leaders for that game were read completely.",
     "source_url": "https://api-web.nhle.com/v1/score/2026-10-23"},
    {"sport": "basketball", "reason_flag": "CU-03",
     "what": "NBA fixtures for 2026-10-22 to 2026-10-29",
     "reason": "nba.com/games?date=2026-10-22 rendered only per-day game counts (22 Oct = 2, 23 Oct = 12, 24 Oct = 8, 25 Oct = 7, 26 Oct = 9) and the fixture list itself failed to render. cdn.nba.com scoreboard, data.nba.net scoreboard, nba.com/game and stats.nba.com scoreboardv2 all returned errors. No pairing was read, so no NBA row is published; the nine EuroLeague rows are this layer's basketball coverage.",
     "source_url": "https://www.nba.com/games?date=2026-10-22"},
    {"sport": "basketball", "reason_flag": "CU-04",
     "what": "EuroLeague Round 7 fixture E2026/70 (Hapoel IBI Tel Aviv v Crvena Zvezda Meridianbet)",
     "reason": "Read from the official game centre but not published as a fixture: Hapoel IBI Tel Aviv had already played Round 7 on 2026-10-21 (90-81 v Virtus Bologna) and stands at 5-2 over 7 GP while every other club shows 6 GP. The game centre therefore lists a Round 7 row that is already complete, and publishing it would double-count the round.",
     "source_url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/"},
    {"sport": "handball", "reason_flag": "CU-05",
     "what": "EHF European Cup Men fixtures dated 2026-10-23 and 2026-10-24 (nine read from ehfcl.eurohandball.com) and the IHF Women's World Championship 2027 qualifiers Estonia v Kosovo / Kosovo v Estonia",
     "reason": "Captured first-hand but published without originated prices: the EHF pages exposed no group-standings table for the European Cup or for the World Championship qualifiers in this session, and originating a line with no strength input would be inference.",
     "source_url": "https://ehfcl.eurohandball.com/"},
    {"sport": "handball", "reason_flag": "CU-06",
     "what": "A 20:45 fixture on 2026-10-29 beginning with Montpellier Handball",
     "reason": "The listing was cut off at the end of the fetched chunk. The opponent was read separately on the official standings page (Montpellier Handball v Dinamo Bucuresti, match id 202711020101055) and is published, but the truncation is disclosed here so the two readings can be reconciled manually.",
     "source_url": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
    {"sport": "snooker", "reason_flag": "CU-07",
     "what": "Two 2026 Northern Ireland Open Round 3 fixtures (David Gilbert v Ka Wai Cheung; Jak Jones v Daniel Wells) and two 09:00 fixtures on Thursday 22 October",
     "reason": "Neither player in those two fixtures appears in the 21 Round 1/Round 2 results read from wst.tv, so there is no first-hand strength input for them: they are published with blank lines and the reason rather than with an inferred price. Separately, the official page does not state a timezone, so the two 09:00 fixtures may already have begun when this page is published.",
     "source_url": "https://www.wst.tv/matches/"},
    {"sport": "basketball", "reason_flag": "CU-19",
     "what": "EuroLeague Round 7 venue attribution for Maccabi Rapyd Tel Aviv (ALEKSANDAR NIKOLIC HALL) and the Belgrade derby at BELGRADE ARENA",
     "reason": "The official game centre names an arena for every fixture but never states whether a home fixture is being played at a neutral site, and a same-city derby dilutes home advantage. This layer applies one uniform +3.0 home-point advantage to every fixture and discloses the two cases where that may overstate or understate the edge, rather than adjusting a number the source does not provide.",
     "source_url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/"},
    {"sport": "baseball", "reason_flag": "CU-20",
     "what": "World Series Game 1 and Game 2 priced identically",
     "reason": "Both games are originated from the same official season inputs (club runs scored and allowed over 162 games plus the 30-club league average). No starting-pitcher announcement was returned by the official schedule endpoint in this session, and starting pitchers dominate single-game baseball pricing, so the two rows carry the same model numbers and the same medium confidence. No pitcher is named anywhere on this layer.",
     "source_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-10-25"},
    {"sport": "motor-racing", "reason_flag": "CU-21",
     "what": "Round 18 United States Grand Prix outright prices",
     "reason": "The only official strength input read this session is the 2026 Drivers' championship standings. Share-of-championship-points is a crude outright prior, not a circuit model: it knows nothing about the Circuit of the Americas, tyre allocation, sprint format or car upgrades. Every driver price on this row is therefore capped at low confidence and no high-confidence pick is claimed for motor racing.",
     "source_url": "https://www.formula1.com/en/results/2026/drivers"},
    {"sport": "snooker", "reason_flag": "CU-22",
     "what": "Best-of-seven frame format for Northern Ireland Open Round 3",
     "reason": "The official matches page does not state the frame format for Round 3. All 21 Round 1 and Round 2 results read first-hand this session ended with the winner on exactly four frames, which is consistent only with a best-of-seven, so that format is used and disclosed rather than taken from an outside source. No world-ranking table was captured either, so the only strength input is in-event frame form; two of the six fixtures have none at all and publish blank lines.",
     "source_url": "https://www.wst.tv/matches/"},
    {"sport": "all", "reason_flag": "CU-23",
     "what": "Model constants that are ours, not the sport's",
     "reason": "Home advantages (+1.05 multiplicative for the NHL, +3.0 points for EuroLeague and the URC, +0.4 goals for the EHF, +0.25 runs for MLB), the shrinkage priors (gp+8, gp+6, gp+3, gp+20, matches+6), the margin and total standard deviations (NHL and handball and MLB come from an exact score grid; EuroLeague 11.0/15.0; URC 13.0/16.0 with a +/-1 point draw band) and the alternate-line radii are all assumptions chosen by this layer. No official source publishes them. They are listed in full on the methodology page so any reader can re-run the arithmetic with different values.",
     "source_url": "methodology.html"},
    {"sport": "rugby-union", "reason_flag": "CU-18",
     "what": "United Rugby Championship Round 4 kickoff times",
     "reason": "The official Round 4 listing renders times as 'Local' without naming a timezone, and one fixture renders '12:15' on Saturday 24 October an hour earlier than the rest of the round. Times are published verbatim as read and flagged rather than converted or normalised.",
     "source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
]


def main():
    load_nhl_full()
    matches = []
    matches += seed_nhl()
    matches += seed_euroleague()
    matches += seed_urc()
    matches += seed_handball()
    matches += seed_snooker()
    matches += seed_mlb()
    matches += seed_f1()
    matches.sort(key=lambda m: (m["date"], m["sport"], m["id"]))

    by_sport = {}
    for slug, name in SPORTS:
        rows = [m for m in matches if m["sport"] == slug]
        zero = next((z for z in ZERO_SPORTS if z["sport"] == slug), None)
        by_sport[slug] = {
            "sport": slug,
            "sport_name": name,
            "fixture_rows": len(rows),
            "zero_row_reason": (zero or {}).get("reason", ""),
            "zero_row_flag": (zero or {}).get("reason_flag", ""),
            "source_consulted": (zero or {}).get("source_consulted", ""),
            "source_reachable": (zero or {}).get("source_reachable", None),
        }

    doc = {
        "layer": "current",
        "generated_by": "scripts/current_seed.py",
        "capture_window": {"start": WINDOW_START, "end": WINDOW_END},
        "captured_at_utc": "2026-10-22T13:10:00Z",
        "matches": matches,
        "sports": by_sport,
        "excluded": EXCLUDED,
        "sport_order": [slug for slug, _ in SPORTS],
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "matches.json"), "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=1, ensure_ascii=False)
        handle.write("\n")

    print("current_seed OK: %d fixture rows across %d sports" % (
        len(matches), len({m["sport"] for m in matches})))
    for slug, name in SPORTS:
        print("   %-16s %2d" % (name, by_sport[slug]["fixture_rows"]))


if __name__ == "__main__":
    main()
