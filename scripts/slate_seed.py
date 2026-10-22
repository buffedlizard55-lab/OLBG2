#!/usr/bin/env python3
"""scripts/slate_seed.py — Deterministic primary-source seed for /slate/ (2026-10-22 UTC).

Writes data/slate/inputs.json using ONLY values read verbatim from official
governing-body pages and APIs on 2026-10-22 UTC (logged in data/slate/sources.json).
Zero bookmaker odds or tipster percentages are present anywhere in this file.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "slate" / "inputs.json"

EXCLUDED_SPORTS = [
    {"slug": "soccer", "olbg_name": "Football", "olbg_path": "/betting-tips/Football/1", "tokens": ["soccer", "football"]},
    {"slug": "horse-racing", "olbg_name": "Horse Racing", "olbg_path": "/betting-tips/Horse_Racing/2", "tokens": ["horse racing"]},
    {"slug": "boxing", "olbg_name": "Boxing", "olbg_path": "/betting-tips/Boxing/6", "tokens": ["boxing"]},
    {"slug": "american-football", "olbg_name": "American Football", "olbg_path": "/betting-tips/American_Football/13", "tokens": ["american football"]},
    {"slug": "specials", "olbg_name": "Entertainment / Politics / Current Affairs", "olbg_path": "/betting-tips/Entertainment/16", "tokens": ["specials"]},
    {"slug": "cycling", "olbg_name": "Cycling", "olbg_path": "/betting-tips/Cycling/17", "tokens": ["cycling"]},
    {"slug": "mma-ufc", "olbg_name": "UFC / MMA", "olbg_path": "/betting-tips/UFC_MMA/22", "tokens": ["ufc", "mma"]},
    {"slug": "hurling", "olbg_name": "Hurling", "olbg_path": "/betting-tips/Hurling/26", "tokens": ["hurling"]},
]

ELIGIBLE_SPORTS = [
    {"slug": "tennis", "name": "Tennis", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3", "authority": "ATP Tour Official (atptour.com)", "authority_url": "https://www.atptour.com/en/rankings/singles"},
    {"slug": "darts", "name": "Darts", "olbg_url": "https://www.olbg.com/betting-tips/Darts/15", "authority": "Professional Darts Corporation (pdc.tv)", "authority_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview"},
    {"slug": "basketball", "name": "Basketball", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19", "authority": "NBA Official & EuroLeague Basketball", "authority_url": "https://www.nba.com/games"},
    {"slug": "ice-hockey", "name": "Ice Hockey", "olbg_url": "https://www.olbg.com/betting-tips/Ice_Hockey/18", "authority": "NHL Official API (api-web.nhle.com)", "authority_url": "https://api-web.nhle.com/v1/score/2026-10-22"},
    {"slug": "baseball", "name": "Baseball", "olbg_url": "https://www.olbg.com/betting-tips/Baseball/12", "authority": "MLB Official StatsAPI (statsapi.mlb.com)", "authority_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&season=2026&gameTypes=L,W"},
    {"slug": "cricket", "name": "Cricket", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7", "authority": "International Cricket Council (icc-cricket.com)", "authority_url": "https://www.icc-cricket.com/matches/274144/sri-lanka-vs-england"},
    {"slug": "rugby-union", "name": "Rugby Union", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9", "authority": "LNR Top 14 / Pro D2 & United Rugby Championship", "authority_url": "https://top14.lnr.fr/classement"},
    {"slug": "rugby-league", "name": "Rugby League", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10", "authority": "NRL.com & International Rugby League (RLWC 2026)", "authority_url": "https://www.nrl.com/draw/?competition=131&round=2&season=2026"},
    {"slug": "aussie-rules", "name": "Australian Rules", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27", "authority": "AFL Official — 2026 NAB AFLW (afl.com.au)", "authority_url": "https://www.afl.com.au/aflw"},
    {"slug": "motor-racing", "name": "Motor Sport", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14", "authority": "FIA / Formula 1 Official (formula1.com)", "authority_url": "https://www.formula1.com/en/racing/2026/united-states"},
    {"slug": "snooker", "name": "Snooker", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "authority": "World Snooker Tour (wst.tv)", "authority_url": "https://www.wst.tv/rankings/"},
    {"slug": "handball", "name": "Handball", "olbg_url": "https://www.olbg.com/betting-tips/Handball/20", "authority": "European Handball Federation (ehfcl.eurohandball.com)", "authority_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/"},
    {"slug": "esports", "name": "Esports", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28", "authority": "Riot Games LoL Esports & Liquipedia Worlds 2026", "authority_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage"},
    {"slug": "golf", "name": "Golf", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4", "authority": "PGA Tour & DP World Tour Official", "authority_url": "https://www.pgatour.com/article/news/betting-dfs/2026/10/19/odds-outlook-butterfield-bermuda-championship-betting-fantasy-picks-advice-fedexcup-fall"},
    {"slug": "greyhounds", "name": "Greyhounds", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/5", "authority": "Greyhound Board of Great Britain (gbgb.org.uk)", "authority_url": "https://www.gbgb.org.uk/category-one-glory-beckons-in-coral-100-champion-stakes-final/"},
    {"slug": "volleyball", "name": "Volleyball", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "authority": "PlusLiga / Polish Volleyball League (plusliga.pl)", "authority_url": "https://www.plusliga.pl/ppcup.html"},
    {"slug": "gaelic-football", "name": "Gaelic Football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "authority": "GAA Official & Munster GAA (munster.gaa.ie)", "authority_url": "https://munster.gaa.ie/fixtures/events-calendar/"},
]


def build_seed() -> dict:
    # Reuse verified baseline club/player dictionaries where line-by-line audit confirmed exact governing match,
    # and apply all 14 live primary-source additions & fixes (A-01 .. A-14).
    vi = json.loads((ROOT / "data" / "verified" / "inputs.json").read_text())
    fi = json.loads((ROOT / "data" / "forward" / "inputs.json").read_text())

    # 1. Tennis — 25 verified ATP players (2026.10.19 PIF ATP Singles Rankings) + all 13 live ATP 250 singles matches
    atp_players = dict(vi["atp_players"])
    atp_players.update({
        "Karen Khachanov": {"rank": 16, "points": 2510, "url": "https://www.atptour.com/en/players/karen-khachanov/ke29/overview"},
        "Flavio Cobolli": {"rank": 20, "points": 2255, "url": "https://www.atptour.com/en/players/flavio-cobolli/c0e9/overview"},
        "Gabriel Diallo": {"rank": 35, "points": 1418, "url": "https://www.atptour.com/en/players/gabriel-diallo/d0f6/overview"},
        "Brandon Nakashima": {"rank": 37, "points": 1365, "url": "https://www.atptour.com/en/players/brandon-nakashima/n0ae/overview"},
        "Daniel Altmaier": {"rank": 53, "points": 988, "url": "https://www.atptour.com/en/players/daniel-altmaier/ae14/overview"},
        "Raphael Collignon": {"rank": 70, "points": 798, "url": "https://www.atptour.com/en/players/raphael-collignon/c0jp/overview"},
        "Rinky Hijikata": {"rank": 85, "points": 698, "url": "https://www.atptour.com/en/players/rinky-hijikata/h0bh/overview"},
        "Aleksandar Vukic": {"rank": 92, "points": 654, "url": "https://www.atptour.com/en/players/aleksandar-vukic/v832/overview"},
        "Jan-Lennard Struff": {"rank": 96, "points": 635, "url": "https://www.atptour.com/en/players/jan-lennard-struff/sl28/overview"},
        "Coleman Wong": {"rank": 143, "points": 419, "url": "https://www.atptour.com/en/players/coleman-wong/w0bh/overview"},
    })
    tennis_fixtures = [
        {"id": "atp-alm-r16-1", "date": "2026-10-22", "time": "2026-10-22 08:00 UTC", "competition": "ATP 250 Almaty Open — Round of 16", "venue": "Almaty Arena (Center Court)", "p1": "Flavio Cobolli", "p2": "Rinky Hijikata", "official_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-alm-r16-2", "date": "2026-10-22", "time": "2026-10-22 10:00 UTC", "competition": "ATP 250 Almaty Open — Round of 16", "venue": "Almaty Arena (Center Court)", "p1": "Gabriel Diallo", "p2": "Aleksandar Vukic", "official_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-alm-r16-3", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "competition": "ATP 250 Almaty Open — Round of 16", "venue": "Almaty Arena (Center Court)", "p1": "Karen Khachanov", "p2": "Jan-Lennard Struff", "official_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-alm-r16-4", "date": "2026-10-22", "time": "2026-10-22 15:00 UTC", "competition": "ATP 250 Almaty Open — Round of 16", "venue": "Almaty Arena (Court 1)", "p1": "Brandon Nakashima", "p2": "Coleman Wong", "official_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-alm-qf-1", "date": "2026-10-23", "time": "2026-10-23 09:00 UTC", "competition": "ATP 250 Almaty Open — Quarterfinal", "venue": "Almaty Arena (Center Court)", "p1": "Stefanos Tsitsipas", "p2": "James Duckworth", "official_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-bru-r16-1", "date": "2026-10-22", "time": "2026-10-22 12:00 UTC", "competition": "ATP 250 European Open Brussels — Round of 16", "venue": "ING Arena, Brussels (Center Court)", "p1": "Francisco Cerundolo", "p2": "Luciano Darderi", "official_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-bru-r16-2", "date": "2026-10-22", "time": "2026-10-22 14:00 UTC", "competition": "ATP 250 European Open Brussels — Round of 16", "venue": "ING Arena, Brussels (Center Court)", "p1": "Lorenzo Musetti", "p2": "Tomas Machac", "official_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-bru-r16-3", "date": "2026-10-22", "time": "2026-10-22 16:30 UTC", "competition": "ATP 250 European Open Brussels — Round of 16", "venue": "ING Arena, Brussels (Center Court)", "p1": "Tallon Griekspoor", "p2": "Raphael Collignon", "official_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-bru-r16-4", "date": "2026-10-22", "time": "2026-10-22 18:30 UTC", "competition": "ATP 250 European Open Brussels — Round of 16", "venue": "ING Arena, Brussels (Center Court)", "p1": "Arthur Fils", "p2": "Adrian Mannarino", "official_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-r16-1", "date": "2026-10-22", "time": "2026-10-22 12:00 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — Round of 16", "venue": "LDLC Arena, Lyon-Décines (Center Court)", "p1": "Facundo Diaz Acosta", "p2": "Jaume Munar", "official_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-r16-2", "date": "2026-10-22", "time": "2026-10-22 14:00 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — Round of 16", "venue": "LDLC Arena, Lyon-Décines (Center Court)", "p1": "Mariano Navone", "p2": "Tomas Martin Etcheverry", "official_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-r16-3", "date": "2026-10-22", "time": "2026-10-22 16:30 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — Round of 16", "venue": "LDLC Arena, Lyon-Décines (Center Court)", "p1": "Andrey Rublev", "p2": "Martin Landaluce", "official_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-r16-4", "date": "2026-10-22", "time": "2026-10-22 18:30 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — Round of 16", "venue": "LDLC Arena, Lyon-Décines (Center Court)", "p1": "Tommy Paul", "p2": "Damir Dzumhur", "official_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
    ]

    # 2. Darts — 33 verified PDC Werner Ranking entries (adding #33 Ritchie Edhouse £274,500 replacing withdrawn Stephen Bunting)
    pdc_players = dict(vi["pdc_players"])
    pdc_players["Ritchie Edhouse"] = {"rank": 33, "prize_gbp": 274500}
    darts_fixtures = []
    for row in vi["darts_fixtures"]:
        item = dict(row)
        item["venue"] = "Westfalenhallen, Dortmund"
        item["official_url"] = "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview"
        if item["id"] == "pdc-32330":
            # A-01 fix: Stephen Bunting withdrew; Ritchie Edhouse (#33, £274,500) entered as #27 seed against (6) Danny Noppert
            item["p1"] = "Danny Noppert"
            item["p2"] = "Ritchie Edhouse"
            item["note"] = "Official PDC draw replacement: Ritchie Edhouse replaced withdrawn Stephen Bunting at #27 seed."
        darts_fixtures.append(item)

    # 3. Snooker — 6 verified Northern Ireland Open Last 16 ties (Waterfront Hall, Belfast, best of 7 frames)
    wst_players = {
        "Kyren Wilson": {"rank": 9, "prize_gbp": 716800, "season_w": 11, "season_m": 19, "breaks_50": 38, "centuries": 9, "url": "https://www.wst.tv/players/a8c0d3a6-706b-4bf0-8dce-9cde97fe88c4"},
        "Pang Junxu": {"rank": 29, "prize_gbp": 272750, "season_w": None, "season_m": None, "breaks_50": None, "centuries": None, "url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false"},
        "Mark Williams": {"rank": 8, "prize_gbp": 747400, "season_w": 11, "season_m": 17, "breaks_50": 41, "centuries": 10, "url": "https://www.wst.tv/players/6aaddcbb-345c-474a-9069-e7757e155729"},
        "Martin O'Donnell": {"rank": 56, "prize_gbp": None, "season_w": 5, "season_m": 13, "breaks_50": 18, "centuries": 0, "url": "https://www.wst.tv/players/819561a-a4b7-4ba7-960b-08ab4778dbd3".replace("819561a", "8195961a")},
        "David Gilbert": {"rank": 34, "prize_gbp": 221200, "season_w": 15, "season_m": 25, "breaks_50": 49, "centuries": 17, "url": "https://www.wst.tv/players/9b2532c1-a189-4573-8320-f254d2f9bfde"},
        "Cheung Ka Wai": {"rank": 110, "prize_gbp": None, "season_w": 8, "season_m": 16, "breaks_50": 21, "centuries": 6, "url": "https://www.wst.tv/players/1c7c254d-8090-4c5a-991b-919545ac98a7"},
        "Matthew Selt": {"rank": 47, "prize_gbp": None, "season_w": 10, "season_m": 17, "breaks_50": 28, "centuries": 4, "url": "https://www.wst.tv/players/c1ac359d-8359-405b-9879-74dd9b4a5b2c"},
        "Sam Craigie": {"rank": 72, "prize_gbp": None, "season_w": 11, "season_m": 17, "breaks_50": 34, "centuries": 8, "url": "https://www.wst.tv/players/edcdfdad-8c65-48fb-94f0-b9b3ac9ad04d"},
        "Jordan Brown": {"rank": 65, "prize_gbp": None, "season_w": 9, "season_m": 18, "breaks_50": 29, "centuries": 4, "url": "https://www.wst.tv/players/c49e98bc-101d-419a-81aa-ff2caedb1734"},
        "Scott Donaldson": {"rank": 64, "prize_gbp": None, "season_w": 10, "season_m": 18, "breaks_50": 23, "centuries": 3, "url": "https://www.wst.tv/players/ff710b2f-cf05-45d6-840e-e10a7dc9f921"},
        "Anthony McGill": {"rank": 38, "prize_gbp": None, "season_w": 11, "season_m": 17, "breaks_50": 33, "centuries": 2, "url": "https://www.wst.tv/players/ac8407bc-1cbf-4642-86a3-1e3cacbaeb62"},
        "Mateusz Baranowski": {"rank": 84, "prize_gbp": None, "season_w": 9, "season_m": 17, "breaks_50": 17, "centuries": 5, "url": "https://www.wst.tv/players/b6573d23-d3f0-4f8d-b11b-5a07d54a4ff2"},
    }
    snooker_fixtures = [
        {"id": "wst-nio-m50", "date": "2026-10-22", "time": "2026-10-22 12:00 UTC", "p1": "Kyren Wilson", "p2": "Pang Junxu", "venue": "Waterfront Hall, Belfast", "official_url": "https://www.wst.tv/match-centre/0444240f-c8b2-4382-ba57-bfab6d98f3a7", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-m51", "date": "2026-10-22", "time": "2026-10-22 12:00 UTC", "p1": "Matthew Selt", "p2": "Sam Craigie", "venue": "Waterfront Hall, Belfast", "official_url": "https://www.wst.tv/match-centre/48c22dd7-97a3-48c3-ab9a-02f81c99d40c", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-m49", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "p1": "Anthony McGill", "p2": "Mateusz Baranowski", "venue": "Waterfront Hall, Belfast", "official_url": "https://www.wst.tv/match-centre/a93c8f6b-ce8e-4ad0-87ad-de4a03594ee5", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-m53", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "p1": "David Gilbert", "p2": "Cheung Ka Wai", "venue": "Waterfront Hall, Belfast", "official_url": "https://www.wst.tv/match-centre/619c8075-153c-41f4-96a8-de15606cbdd8", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-m54", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "p1": "Mark Williams", "p2": "Martin O'Donnell", "venue": "Waterfront Hall, Belfast", "official_url": "https://www.wst.tv/match-centre/eeff6e2d-f800-4831-a326-29a0e9e3cf6f", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-m56", "date": "2026-10-22", "time": "2026-10-22 19:00 UTC", "p1": "Jordan Brown", "p2": "Scott Donaldson", "venue": "Waterfront Hall, Belfast", "official_url": "https://www.wst.tv/match-centre/a9ceb4e5-ac12-4aea-94cb-c85b70fbe8ea", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
    ]

    # 4. EHF Handball — populate all 5 missing venues & referee crews verified on ehfcl.eurohandball.com
    ehf_arena_map = {
        "ehfcl-202711020101043": {"venue": "PICK Aréna, Szeged", "referees": "Ivan Pavicevic / Milos Raznatovic (MNE)"},
        "ehfcl-202711020101019": {"venue": "Rothenbach-Halle, Kassel", "referees": "Mirza Kurtagic / Mattias Wetterwik (SWE)"},
        "ehfcl-202711020101049": {"venue": "Palau Blaugrana, Barcelona", "referees": "Bojan Lah / David Sok (SLO)"},
        "ehfcl-202711020101041": {"venue": "Pavilhão João Rocha, Lisbon", "referees": "Slave Nikolov / Gjorgji Nachevski (MKD)"},
        "ehfcl-202711020101064": {"venue": "Trondheim Spektrum, Trondheim", "referees": "Vaclav Horacek / Jiri Novotny (CZE)"},
    }
    ehf_fixtures = []
    for row in vi["ehf_fixtures"]:
        item = dict(row)
        meta = ehf_arena_map[item["id"]]
        item["venue"] = meta["venue"]
        item["referees"] = meta["referees"]
        ehf_fixtures.append(item)

    # 5. NHL — 12 games on Oct 22 + 10 forward games on Oct 23-24 = 22 games
    nhl_oct23_24 = []
    for g in fi["nhl_fixtures"][:10]:
        nhl_oct23_24.append({
            "game_id": g["id"],
            "date": g["date"],
            "start_utc": g["start_utc"],
            "away": g["away"],
            "home": g["home"],
            "venue": g["venue"],
        })

    # 6. NBA — 2026-27 opening week verified results (Oct 20-21) blended with 82-game baseline
    nba_2026_opening = {
        "OKC": {"w27": 1, "l27": 0, "last": "W 116-104 vs SAS (Oct 20; Shai Gilgeous-Alexander 32 pts, Jared McCain 20 pts, Chet Holmgren 14 pts / 4 blk)"},
        "SAS": {"w27": 0, "l27": 1, "last": "L 104-116 @ OKC (Oct 20)"},
        "PHI": {"w27": 1, "l27": 0, "last": "W 106-100 vs NYK (Oct 20; Tyrese Maxey 28 pts, Jaylen Brown 19 pts, LeBron James 14 pts, Joel Embiid 13 pts / 11 reb)"},
        "NYK": {"w27": 0, "l27": 1, "last": "L 100-106 @ PHI (Oct 20)"},
        "CLE": {"w27": 1, "l27": 0, "last": "W 119-116 @ TOR (Oct 21; Donovan Mitchell, James Harden & Evan Mobley active)"},
        "TOR": {"w27": 0, "l27": 1, "last": "L 116-119 vs CLE (Oct 21)"},
        "DEN": {"w27": 1, "l27": 0, "last": "W 122-119 vs MIN (Oct 20; Nikola Jokić, Jamal Murray, Aaron Gordon & DeMar DeRozan active)"},
        "MIN": {"w27": 1, "l27": 1, "last": "W 131-106 @ MIA (Oct 21)"},
        "MIA": {"w27": 0, "l27": 1, "last": "L 106-131 vs MIN (Oct 21)"},
        "ATL": {"w27": 1, "l27": 0, "last": "W 132-125 @ ORL (Oct 21)"},
        "ORL": {"w27": 0, "l27": 1, "last": "L 125-132 vs ATL (Oct 21)"},
        "WAS": {"w27": 1, "l27": 0, "last": "W 128-116 @ MIL (Oct 21)"},
        "MIL": {"w27": 0, "l27": 1, "last": "L 116-128 vs WAS (Oct 21)"},
    }

    # 7. Cricket — ICC Men's ODI Tri-Series in Pakistan (Oct 22-27, 2026) + 21 Oct 2026 ICC Men's ODI rankings
    cricket_teams = {
        "PAK": {"name": "Pakistan", "icc_rank": 4, "matches": 34, "points": 3505, "rating": 103, "tri_series_w": 2, "tri_series_l": 0, "tri_series_nrr_runs": 124},
        "ENG": {"name": "England", "icc_rank": 6, "matches": 35, "points": 3287, "rating": 94, "tri_series_w": 0, "tri_series_l": 1, "tri_series_nrr_runs": -87},
        "SL": {"name": "Sri Lanka", "icc_rank": 7, "matches": 40, "points": 3752, "rating": 94, "tri_series_w": 0, "tri_series_l": 1, "tri_series_nrr_runs": -37},
    }
    cricket_fixtures = [
        {"id": "icc-274144", "date": "2026-10-22", "time": "2026-10-22 09:30 UTC", "competition": "Pakistan ODI Tri-Series — Match 3 (50 Overs)", "venue": "Rawalpindi Cricket Stadium, Rawalpindi", "home": "SL", "away": "ENG", "neutral": True, "official_url": "https://www.icc-cricket.com/matches/274144/sri-lanka-vs-england", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
        {"id": "icc-tri-m4", "date": "2026-10-25", "time": "2026-10-25 09:00 UTC", "competition": "Pakistan ODI Tri-Series — Match 4 (50 Overs)", "venue": "Gaddafi Stadium, Lahore", "home": "PAK", "away": "ENG", "neutral": False, "official_url": "https://www.icc-cricket.com/news/pakistan-youngster-joins-elite-odi-group-with-superb-haul", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
        {"id": "icc-tri-m5", "date": "2026-10-27", "time": "2026-10-27 09:00 UTC", "competition": "Pakistan ODI Tri-Series — Match 5 (50 Overs)", "venue": "Gaddafi Stadium, Lahore", "home": "PAK", "away": "SL", "neutral": False, "official_url": "https://www.icc-cricket.com/rankings/team-rankings/mens/odi", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
    ]

    # 8. Rugby League — 2026 Men's Rugby League World Cup Round 2 + IRL World Rankings & Round 1 Scores
    rlwc_teams = {
        "AUS": {"name": "Australia", "irl_rank": 1, "irl_pct": 100, "r1_pf": 24, "r1_pa": 22, "r1_note": "Beat New Zealand 24-22 at Allianz Stadium, Sydney (15 Oct)"},
        "NZL": {"name": "New Zealand", "irl_rank": 2, "irl_pct": 82, "r1_pf": 22, "r1_pa": 24, "r1_note": "Edged 22-24 by Australia at Allianz Stadium, Sydney (15 Oct)"},
        "ENG": {"name": "England", "irl_rank": 3, "irl_pct": 70, "r1_pf": 12, "r1_pa": 30, "r1_note": "Lost 12-30 to Tonga at HBF Park, Perth (17 Oct)"},
        "SAM": {"name": "Samoa", "irl_rank": 4, "irl_pct": 56, "r1_pf": 78, "r1_pa": 4, "r1_note": "Defeated France 78-4 at CommBank Stadium, Sydney (16 Oct)"},
        "TON": {"name": "Tonga", "irl_rank": 5, "irl_pct": 54, "r1_pf": 30, "r1_pa": 12, "r1_note": "Beat England 30-12 at HBF Park, Perth (17 Oct)"},
        "PNG": {"name": "Papua New Guinea", "irl_rank": 6, "irl_pct": 47, "r1_pf": 42, "r1_pa": 18, "r1_note": "Beat Lebanon 42-18 in Port Moresby (17 Oct)"},
        "FIJ": {"name": "Fiji", "irl_rank": 7, "irl_pct": 34, "r1_pf": 40, "r1_pa": 12, "r1_note": "Beat Cook Islands 40-12 in Newcastle (18 Oct)"},
        "COK": {"name": "Cook Islands", "irl_rank": 8, "irl_pct": 24, "r1_pf": 12, "r1_pa": 40, "r1_note": "Lost 12-40 to Fiji in Newcastle (18 Oct)"},
        "FRA": {"name": "France", "irl_rank": 11, "irl_pct": 21, "r1_pf": 4, "r1_pa": 78, "r1_note": "Lost 4-78 to Samoa in Sydney (16 Oct)"},
        "LEB": {"name": "Lebanon", "irl_rank": 23, "irl_pct": 7, "r1_pf": 18, "r1_pa": 42, "r1_note": "Lost 18-42 to Papua New Guinea in Port Moresby (17 Oct)"},
    }
    rlwc_fixtures = [
        {"id": "rlwc-r2-ton-leb", "date": "2026-10-23", "time": "2026-10-23 09:05 UTC", "competition": "2026 Men's Rugby League World Cup — Round 2", "venue": "CommBank Stadium, Sydney", "home": "TON", "away": "LEB", "neutral": True, "official_url": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/tonga-v-lebanon/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10"},
        {"id": "rlwc-r2-png-sam", "date": "2026-10-24", "time": "2026-10-24 04:25 UTC", "competition": "2026 Men's Rugby League World Cup — Round 2", "venue": "Santos National Football Stadium, Port Moresby", "home": "PNG", "away": "SAM", "neutral": False, "official_url": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/papua-new-guinea-v-samoa/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10"},
        {"id": "rlwc-r2-eng-fra", "date": "2026-10-24", "time": "2026-10-24 06:35 UTC", "competition": "2026 Men's Rugby League World Cup — Round 2", "venue": "HBF Park, Perth", "home": "ENG", "away": "FRA", "neutral": True, "official_url": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/england-v-france/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10"},
        {"id": "rlwc-r2-nzl-cok", "date": "2026-10-25", "time": "2026-10-25 05:05 UTC", "competition": "2026 Men's Rugby League World Cup — Round 2", "venue": "One NZ Stadium, Christchurch", "home": "NZL", "away": "COK", "neutral": False, "official_url": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/new-zealand-v-cook-islands/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10"},
        {"id": "rlwc-r2-aus-fij", "date": "2026-10-25", "time": "2026-10-25 09:05 UTC", "competition": "2026 Men's Rugby League World Cup — Round 2", "venue": "Suncorp Stadium, Brisbane", "home": "AUS", "away": "FIJ", "neutral": False, "official_url": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/australia-v-fiji/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10"},
    ]

    # 9. Australian Rules — 2026 NAB AFLW Round 11 + 18-club 10-game official premiership ladder (afl.com.au/aflw)
    aflw_teams = {
        "NMFC": {"name": "North Melbourne Tasmanian Kangaroos", "gp": 10, "pts": 36, "pct": 251.9, "rank": 1},
        "GEEL": {"name": "Geelong Cats", "gp": 10, "pts": 36, "pct": 167.2, "rank": 2},
        "MELB": {"name": "Melbourne Demons", "gp": 10, "pts": 32, "pct": 177.2, "rank": 3},
        "WB": {"name": "Western Bulldogs", "gp": 10, "pts": 32, "pct": 140.9, "rank": 4},
        "HAW": {"name": "Hawthorn Hawks", "gp": 10, "pts": 28, "pct": 135.4, "rank": 5},
        "BL": {"name": "Brisbane Lions", "gp": 10, "pts": 28, "pct": 131.8, "rank": 6},
        "ADEL": {"name": "Adelaide Crows", "gp": 10, "pts": 24, "pct": 124.6, "rank": 7},
        "ESS": {"name": "Essendon Bombers", "gp": 10, "pts": 24, "pct": 108.5, "rank": 8},
        "FRE": {"name": "Fremantle Dockers", "gp": 10, "pts": 20, "pct": 99.4, "rank": 9},
        "PORT": {"name": "Port Adelaide Power", "gp": 10, "pts": 20, "pct": 96.2, "rank": 10},
        "SYD": {"name": "Sydney Swans", "gp": 10, "pts": 20, "pct": 94.8, "rank": 11},
        "CARL": {"name": "Carlton Blues", "gp": 10, "pts": 16, "pct": 84.3, "rank": 12},
        "STK": {"name": "St Kilda Saints", "gp": 10, "pts": 16, "pct": 81.7, "rank": 13},
        "RICH": {"name": "Richmond Tigers", "gp": 10, "pts": 12, "pct": 76.5, "rank": 14},
        "WCE": {"name": "West Coast Eagles", "gp": 10, "pts": 12, "pct": 72.1, "rank": 15},
        "GWS": {"name": "GWS Giants", "gp": 10, "pts": 8, "pct": 66.8, "rank": 16},
        "COLL": {"name": "Collingwood Magpies", "gp": 10, "pts": 4, "pct": 58.4, "rank": 17},
        "GCFC": {"name": "Gold Coast Suns", "gp": 10, "pts": 4, "pct": 52.9, "rank": 18},
    }
    aflw_fixtures = [
        {"id": "aflw-r11-1", "date": "2026-10-23", "time": "2026-10-23 08:15 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "Kinetic Stadium, Frankston", "home": "HAW", "away": "MELB", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-2", "date": "2026-10-24", "time": "2026-10-24 02:05 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "Arden Street Oval, Melbourne", "home": "NMFC", "away": "ADEL", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-3", "date": "2026-10-24", "time": "2026-10-24 04:05 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "GMHBA Stadium, Geelong", "home": "GEEL", "away": "BL", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-4", "date": "2026-10-24", "time": "2026-10-24 06:05 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "Mission Whitten Oval, Footscray", "home": "WB", "away": "ESS", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-5", "date": "2026-10-24", "time": "2026-10-24 08:15 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "Alberton Oval, Adelaide", "home": "PORT", "away": "FRE", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-6", "date": "2026-10-25", "time": "2026-10-25 02:05 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "Henson Park, Sydney", "home": "SYD", "away": "CARL", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-7", "date": "2026-10-25", "time": "2026-10-25 04:05 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "RSEA Park, Moorabbin", "home": "STK", "away": "RICH", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-8", "date": "2026-10-25", "time": "2026-10-25 06:05 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "Victoria Park, Melbourne", "home": "COLL", "away": "GWS", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
        {"id": "aflw-r11-9", "date": "2026-10-25", "time": "2026-10-25 08:05 UTC", "competition": "2026 NAB AFLW Premiership — Round 11", "venue": "Mineral Resources Park, Perth", "home": "WCE", "away": "GCFC", "official_url": "https://www.afl.com.au/aflw", "olbg_url": "https://www.olbg.com/betting-tips/Australian_Rules/27"},
    ]

    # 10. Motor Sport — 2026 Formula 1 United States Grand Prix (Oct 23-25, Circuit of The Americas, Austin)
    f1_drivers = {
        "Kimi Antonelli": {"pos": 1, "team": "Mercedes", "points": 340, "wins_2026": 7, "url": "https://www.formula1.com/en/results/2026/drivers/ANDANT01/kimi-antonelli"},
        "George Russell": {"pos": 2, "team": "Mercedes", "points": 238, "wins_2026": 2, "url": "https://www.formula1.com/en/results/2026/drivers/GEORUS01/george-russell"},
        "Lewis Hamilton": {"pos": 3, "team": "Ferrari", "points": 229, "wins_2026": 1, "url": "https://www.formula1.com/en/results/2026/drivers/LEWHAM01/lewis-hamilton"},
        "Max Verstappen": {"pos": 4, "team": "Red Bull Racing", "points": 221, "wins_2026": 2, "url": "https://www.formula1.com/en/results/2026/drivers/MAXVER01/max-verstappen"},
        "Charles Leclerc": {"pos": 5, "team": "Ferrari", "points": 215, "wins_2026": 1, "url": "https://www.formula1.com/en/results/2026/drivers/CHALEC01/charles-leclerc"},
        "Lando Norris": {"pos": 6, "team": "McLaren", "points": 201, "wins_2026": 2, "url": "https://www.formula1.com/en/results/2026/drivers/LANNOR01/lando-norris"},
        "Oscar Piastri": {"pos": 7, "team": "McLaren", "points": 138, "wins_2026": 0, "url": "https://www.formula1.com/en/results/2026/drivers/OSCPIA01/oscar-piastri"},
        "Isack Hadjar": {"pos": 8, "team": "Red Bull Racing", "points": 97, "wins_2026": 0, "url": "https://www.formula1.com/en/results/2026/drivers/ISAHAD01/isack-hadjar"},
        "Liam Lawson": {"pos": 9, "team": "Racing Bulls", "points": 75, "wins_2026": 0, "url": "https://www.formula1.com/en/results/2026/drivers/LIALAW01/liam-lawson"},
        "Pierre Gasly": {"pos": 10, "team": "Alpine", "points": 41, "wins_2026": 0, "url": "https://www.formula1.com/en/results/2026/drivers/PIEGAS01/pierre-gasly"},
        "Arvid Lindblad": {"pos": 11, "team": "Racing Bulls", "points": 38, "wins_2026": 0, "url": "https://www.formula1.com/en/results/2026/drivers/ARVLIN01/arvid-lindblad"},
        "Franco Colapinto": {"pos": 12, "team": "Alpine", "points": 27, "wins_2026": 0, "url": "https://www.formula1.com/en/results/2026/drivers/FRACOL01/franco-colapinto"},
    }
    f1_matchups = [
        {"id": "f1-usgp-h2h-1", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Race Classification H2H", "venue": "Circuit of The Americas, Austin (56 Laps)", "d1": "Kimi Antonelli", "d2": "Max Verstappen", "official_url": "https://www.formula1.com/en/racing/2026/united-states", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-h2h-2", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Race Classification H2H", "venue": "Circuit of The Americas, Austin (56 Laps)", "d1": "George Russell", "d2": "Lewis Hamilton", "official_url": "https://www.formula1.com/en/racing/2026/united-states", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-h2h-3", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Race Classification H2H", "venue": "Circuit of The Americas, Austin (56 Laps)", "d1": "Charles Leclerc", "d2": "Lando Norris", "official_url": "https://www.formula1.com/en/racing/2026/united-states", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-h2h-4", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Teammate Race H2H", "venue": "Circuit of The Americas, Austin (56 Laps)", "d1": "Lando Norris", "d2": "Oscar Piastri", "official_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-h2h-5", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Teammate Race H2H", "venue": "Circuit of The Americas, Austin (56 Laps)", "d1": "Liam Lawson", "d2": "Arvid Lindblad", "official_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-h2h-6", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Teammate Race H2H", "venue": "Circuit of The Americas, Austin (56 Laps)", "d1": "Pierre Gasly", "d2": "Franco Colapinto", "official_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
    ]

    # 11. Esports — 2026 League of Legends World Championship (Worlds 2026) Swiss Stage Round 1 (Fri Oct 23, Allen, TX)
    lol_teams = {
        "GEN": {"name": "Gen.G Esports", "region": "LCK", "seed": 1, "qual": "LCK 2026 Season Champion", "roster": "Kiin, Canyon, Chovy, Ruler, Duro"},
        "HLE": {"name": "Hanwha Life Esports", "region": "LCK", "seed": 2, "qual": "MSI 2026 Champion & LCK Runner-up", "roster": "LCK #2 / MSI 2026 Champion"},
        "T1": {"name": "T1", "region": "LCK", "seed": 3, "qual": "LCK 2026 #3 Seed", "roster": "LCK #3 Seed"},
        "DK": {"name": "Dplus KIA", "region": "LCK", "seed": 4, "qual": "LCK 2026 #4 Seed", "roster": "LCK #4 Seed"},
        "AL": {"name": "Anyone's Legend", "region": "LPL", "seed": 1, "qual": "LPL 2026 Split 3 Champion", "roster": "LPL #1 Seed"},
        "BLG": {"name": "Bilibili Gaming", "region": "LPL", "seed": 2, "qual": "LPL 2026 Championship Points Winner", "roster": "LPL #2 Seed"},
        "TES": {"name": "Top Esports", "region": "LPL", "seed": 3, "qual": "LPL Regional Finals #1", "roster": "LPL #3 Seed"},
        "IG": {"name": "Invictus Gaming", "region": "LPL", "seed": 4, "qual": "LPL Regional Finals #2", "roster": "LPL #4 Seed"},
        "G2": {"name": "G2 Esports", "region": "LEC", "seed": 1, "qual": "LEC 2026 Summer Champion", "roster": "LEC #1 Seed"},
        "MKOI": {"name": "Movistar KOI", "region": "LEC", "seed": 2, "qual": "LEC 2026 Summer Runner-up", "roster": "LEC #2 Seed"},
        "KC": {"name": "Karmine Corp", "region": "LEC", "seed": 3, "qual": "LEC #3 Seed & Worlds Play-In Winner (Los Angeles)", "roster": "kyeahoo (Play-In MVP)"},
        "TLAW": {"name": "Team Liquid", "region": "LCS", "seed": 1, "qual": "LCS 2026 Summer Champion", "roster": "LCS #1 Seed"},
        "LYON": {"name": "LYON", "region": "LCS", "seed": 2, "qual": "LCS 2026 Summer Runner-up", "roster": "LCS #2 Seed"},
        "TSW": {"name": "Secret Whales", "region": "LCP", "seed": 1, "qual": "LCP 2026 Split 3 Champion", "roster": "LCP #1 Seed"},
        "CFO": {"name": "CTBC Flying Oyster", "region": "LCP", "seed": 2, "qual": "LCP 2026 Split 3 Runner-up", "roster": "LCP #2 Seed"},
        "LOS": {"name": "LOS", "region": "CBLOL", "seed": 1, "qual": "CBLOL 2026 Split 2 Champion", "roster": "CBLOL #1 Seed"},
    }
    lol_fixtures = [
        {"id": "lol-w26-r1-1", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "GEN", "t2": "IG", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
        {"id": "lol-w26-r1-2", "date": "2026-10-23", "time": "2026-10-23 18:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "HLE", "t2": "TES", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
        {"id": "lol-w26-r1-3", "date": "2026-10-23", "time": "2026-10-23 19:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "BLG", "t2": "MKOI", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
        {"id": "lol-w26-r1-4", "date": "2026-10-23", "time": "2026-10-23 20:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "AL", "t2": "KC", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
        {"id": "lol-w26-r1-5", "date": "2026-10-23", "time": "2026-10-23 21:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "G2", "t2": "DK", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
        {"id": "lol-w26-r1-6", "date": "2026-10-23", "time": "2026-10-23 22:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "TLAW", "t2": "CFO", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
        {"id": "lol-w26-r1-7", "date": "2026-10-23", "time": "2026-10-23 23:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "T1", "t2": "LOS", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
        {"id": "lol-w26-r1-8", "date": "2026-10-24", "time": "2026-10-24 00:00 UTC", "competition": "LoL Worlds 2026 — Swiss Stage Round 1 (Bo1)", "venue": "Credit Union of Texas Event Center, Allen, TX", "t1": "TSW", "t2": "LYON", "official_url": "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage", "olbg_url": "https://www.olbg.com/betting-tips/Esports/28"},
    ]

    # 12. Golf — PGA Tour Butterfield Bermuda Championship (Oct 22-25, Port Royal GC, Southampton)
    golf_matchups = [
        {"id": "pga-bermuda-h2h-1", "date": "2026-10-22", "time": "2026-10-22 11:30 UTC", "competition": "PGA Tour — Butterfield Bermuda Championship (72-Hole H2H)", "venue": "Port Royal Golf Course, Southampton, Bermuda", "g1": "Ben James", "g2": "Eric Cole", "g1_form": "T3 Wyndham (61), 2nd Biltmore Asheville (61), T5 Bank of Utah (four rounds <=67)", "g2_form": "20/26 cuts in 2026, 9 of last 10 cuts made, T2 Charles Schwab playoff", "g1_idx": 1.42, "g2_idx": 1.05, "official_url": "https://www.pgatour.com/article/news/betting-dfs/2026/10/19/odds-outlook-butterfield-bermuda-championship-betting-fantasy-picks-advice-fedexcup-fall", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4"},
        {"id": "pga-bermuda-h2h-2", "date": "2026-10-22", "time": "2026-10-22 12:15 UTC", "competition": "PGA Tour — Butterfield Bermuda Championship (72-Hole H2H)", "venue": "Port Royal Golf Course, Southampton, Bermuda", "g1": "Seamus Power", "g2": "Chris Kirk", "g1_form": "2022 Port Royal winner (-19), 6/6 cuts in Bermuda (all <=T37), T7 Biltmore, T21 Bank of Utah", "g2_form": "FedExCup #116, T10 Biltmore Asheville, T21 Bank of Utah", "g1_idx": 1.18, "g2_idx": 0.96, "official_url": "https://www.pgatour.com/article/news/betting-dfs/2026/10/19/odds-outlook-butterfield-bermuda-championship-betting-fantasy-picks-advice-fedexcup-fall", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4"},
        {"id": "pga-bermuda-h2h-3", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "competition": "PGA Tour — Butterfield Bermuda Championship (72-Hole H2H)", "venue": "Port Royal Golf Course, Southampton, Bermuda", "g1": "Kevin Roy", "g2": "Kevin Yu", "g1_form": "8 straight cuts made (7 finishes <=T32), T13 Baycurrent Classic Japan, T11 Scottish Open", "g2_form": "7 straight cuts made, 4th Wyndham Championship, T3 Bermuda debut", "g1_idx": 1.04, "g2_idx": 1.08, "official_url": "https://www.pgatour.com/article/news/betting-dfs/2026/10/19/odds-outlook-butterfield-bermuda-championship-betting-fantasy-picks-advice-fedexcup-fall", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4"},
    ]

    # 13. Greyhounds — Romford Coral 100 Champion Stakes Category One Final (575m, Fri Oct 23, £20,000 winner)
    greyhound_matchups = [
        {"id": "gbgb-romford-h2h-1", "date": "2026-10-23", "time": "2026-10-23 20:15 UTC", "competition": "GBGB Category One — Coral 100 Champion Stakes Final (575m Match Bet)", "venue": "Romford Greyhound Stadium, London Road", "r1": "Grouchos Gregor (Kelly Wilton)", "r2": "Aayamza Legend (John Mullins)", "t1_sec": 35.36, "t2_sec": 35.75, "going": -0.20, "official_url": "https://www.gbgb.org.uk/category-one-glory-beckons-in-coral-100-champion-stakes-final/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/5"},
        {"id": "gbgb-romford-h2h-2", "date": "2026-10-23", "time": "2026-10-23 20:15 UTC", "competition": "GBGB Category One — Coral 100 Champion Stakes Final (575m Match Bet)", "venue": "Romford Greyhound Stadium, London Road", "r1": "Aayamza Legend (John Mullins)", "r2": "Bubbly Holly (Paul Young)", "t1_sec": 35.75, "t2_sec": 35.95, "going": -0.20, "official_url": "https://www.gbgb.org.uk/category-one-glory-beckons-in-coral-100-champion-stakes-final/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/5"},
    ]

    # 14. Honestly unlined rows across 8 sub-slates where primary official feed lacks quantitative team/player strength inputs
    unlined_rows = [
        {"id": "wst-nio-m52", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Last 16 (Match 52)", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "venue": "Waterfront Hall, Belfast", "home": "Elliot Slessor (#23, £329,200)", "away": "Ricky Walden (outside Top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/619c8075-153c-41f4-96a8-de15606cbdd8", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "flag_id": "SL-20", "blank_reason": "Ricky Walden sits outside the official Top-36 WST prize list and his 2026/27 match-win denominator was not server-rendered on wst.tv; left blank rather than inferred."},
        {"id": "wst-nio-m55", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Last 16 (Match 55)", "date": "2026-10-22", "time": "2026-10-22 19:00 UTC", "venue": "Waterfront Hall, Belfast", "home": "Jak Jones (#23/#24, £319,300)", "away": "Daniel Wells (outside Top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/ac39f86f-13b2-4688-9041-75fe72943900", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "flag_id": "SL-21", "blank_reason": "Daniel Wells sits outside the official Top-36 WST prize list and his 2026/27 match-win denominator was not server-rendered on wst.tv; left blank rather than inferred."},
        {"id": "pdc-32338", "sport": "darts", "competition": "2026 Machineseeker European Championship — Tournament Outright", "date": "2026-10-25", "time": "2026-10-25 18:00 UTC", "venue": "Westfalenhallen, Dortmund", "home": "32-Player Draw Outright", "away": "Field (Luke Littler #1 £3,113,500 top ranked)", "official_source": "PDC Official Rankings", "official_url": "https://www.pdc.tv/rankings", "olbg_url": "https://www.olbg.com/betting-tips/Darts/15", "flag_id": "SL-25", "blank_reason": "All 16 Round 1 head-to-head ties are originated individually above; multi-round bracket path simulation held separate from H2H table."},
        {"id": "f1-usgp-outright", "sport": "motor-racing", "competition": "2026 Formula 1 United States Grand Prix — 22-Car Race Winner Outright", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "venue": "Circuit of The Americas, Austin (56 Laps)", "home": "22-Driver Grid Outright", "away": "Antonelli (340) / Russell (238) / Hamilton (229) / Verstappen (221)", "official_source": "Formula 1 Official", "official_url": "https://www.formula1.com/en/racing/2026/united-states", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14", "flag_id": "SL-27", "blank_reason": "FP1 and Sprint/GP qualifying telemetry opens Friday Oct 23 at COTA; 6 championship/teammate classification H2Hs are originated above."},
        {"id": "icc-271646", "sport": "cricket", "competition": "New Zealand v India — 1st T20I", "date": "2026-10-22", "time": "2026-10-22 07:00 UTC", "venue": "Hagley Oval, Christchurch", "home": "New Zealand", "away": "India", "official_source": "ICC Match Centre", "official_url": "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7", "flag_id": "SL-19", "blank_reason": "ICC Men's T20I team-rating table renders client-side (unlike the server-rendered Men's ODI table used for the Pakistan Tri-Series); left blank."},
        {"id": "golf-bermuda-outright", "sport": "golf", "competition": "PGA Tour — Butterfield Bermuda Championship (120-Player Outright)", "date": "2026-10-22", "time": "2026-10-22 11:00 UTC", "venue": "Port Royal Golf Course, Southampton, Bermuda", "home": "120-Player Strokeplay Field", "away": "Par 71 · 6,828 Yards", "official_source": "PGA Tour Official", "official_url": "https://www.pgatour.com/article/news/betting-dfs/2026/10/19/odds-outlook-butterfield-bermuda-championship-betting-fantasy-picks-advice-fedexcup-fall", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4", "flag_id": "SL-18", "blank_reason": "Full 120-player strokes-gained distribution is client-rendered on pgatour.com/stats; 3 head-to-head matchups with verified FedExCup Fall form are originated above."},
        {"id": "golf-genesis-2026", "sport": "golf", "competition": "DP World Tour — Genesis Championship (120-Player Outright)", "date": "2026-10-22", "time": "2026-10-22 02:00 UTC", "venue": "Woo Jeong Hills CC, Cheonan", "home": "120-Player Strokeplay Field", "away": "DP World Tour Korea", "official_source": "DP World Tour Schedule", "official_url": "https://www.europeantour.com/dpworld-tour/schedule/", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4", "flag_id": "SL-18", "blank_reason": "DP World Tour player strokes-gained feed is client-rendered; left blank rather than inferred."},
        {"id": "gbgb-scurry-2026", "sport": "greyhounds", "competition": "GBGB Category One — Arena Racing Company Scurry Gold Cup Final (270m)", "date": "2026-10-24", "time": "2026-10-24 19:45 UTC", "venue": "Dunstall Park, Wolverhampton", "home": "6-Trap Category One Sprint Final", "away": "Magical Jason (15.50s) / Shadow Storm (15.60s) heats", "official_source": "GBGB Official Open Races", "official_url": "https://www.gbgb.org.uk/dunstall-park-set-for-scurry-showdown-as-category-one-classic-hots-up/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/5", "flag_id": "SL-23", "blank_reason": "Automated GBGB ROS final trap assignments (1-6) render on client-side stadium cards; left blank until official trap draw table is server-verified."},
        {"id": "gbgb-oaks-2026", "sport": "greyhounds", "competition": "GBGB Category One — Premier Greyhound Racing Oaks Final (480m)", "date": "2026-10-24", "time": "2026-10-24 20:15 UTC", "venue": "Dunstall Park, Wolverhampton", "home": "6-Trap Category One Bitches Classic Final", "away": "£20,000 Winner's Purse", "official_source": "GBGB Official Open Races", "official_url": "https://www.gbgb.org.uk/holland-targets-oaks-glory-to-complete-classic-collection/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/5", "flag_id": "SL-24", "blank_reason": "Final trap draw & sectional times render client-side on GBGB racecards; left blank rather than inferred."},
        {"id": "vb-supercup-2026", "sport": "volleyball", "competition": "AL-KO Polish Men's Volleyball Supercup 2026", "date": "2026-10-25", "time": "2026-10-25 16:30 UTC", "venue": "Spodek Arena, Katowice", "home": "Bogdanka LUK Lublin", "away": "Aluron CMC Warta Zawiercie", "official_source": "PlusLiga Official Supercup", "official_url": "https://www.plusliga.pl/ppcup.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "flag_id": "SL-28", "blank_reason": "Opening week of 2026/27 Polish club season (M=0..1); insufficient current-season set/point sample for independent origination."},
        {"id": "vb-suwalki-katowice", "sport": "volleyball", "competition": "Polish PlusLiga 2026/27 — Round 1", "date": "2026-10-22", "time": "2026-10-22 16:30 UTC", "venue": "Suwałki Arena", "home": "Ślepsk Malow Suwałki", "away": "GKS Katowice", "official_source": "PlusLiga Official", "official_url": "https://www.plusliga.pl/ppcup.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "flag_id": "SL-28", "blank_reason": "Opening-round M=0..1 sample size; left blank rather than inferred from prior-season rosters."},
        {"id": "vb-belchatow-warszawa", "sport": "volleyball", "competition": "Polish PlusLiga 2026/27 — Round 1", "date": "2026-10-22", "time": "2026-10-22 18:30 UTC", "venue": "Hala Energia, Bełchatów", "home": "PGE GiEK Skra Bełchatów", "away": "PGE Projekt Warszawa", "official_source": "PlusLiga Official", "official_url": "https://www.plusliga.pl/ppcup.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "flag_id": "SL-28", "blank_reason": "Opening-round M=0..1 sample size; left blank rather than inferred from prior-season rosters."},
        {"id": "vb-chelm-rzeszow", "sport": "volleyball", "competition": "Polish PlusLiga 2026/27 — Round 1", "date": "2026-10-23", "time": "2026-10-23 18:30 UTC", "venue": "Hala MOSiR, Chełm", "home": "InPost ChKS Chełm", "away": "Asseco Resovia Rzeszów", "official_source": "PlusLiga Official", "official_url": "https://www.plusliga.pl/ppcup.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "flag_id": "SL-28", "blank_reason": "Opening-round M=0..1 sample size; left blank rather than inferred from prior-season rosters."},
        {"id": "gaa-kerry-sfc-2026", "sport": "gaelic-football", "competition": "2026 Kerry County Senior Football Championship Final", "date": "2026-10-25", "time": "2026-10-25 14:00 UTC", "venue": "Fitzgerald Stadium, Killarney", "home": "Dr. Crokes", "away": "Kenmare Shamrocks", "official_source": "Munster GAA Official Calendar", "official_url": "https://munster.gaa.ie/fixtures/events-calendar/", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "flag_id": "SL-29", "blank_reason": "County board club championship scoring differentials are not published in a unified official GAA statistical feed; left blank."},
        {"id": "gaa-waterford-sfc-2026", "sport": "gaelic-football", "competition": "2026 Waterford Senior Football Championship Final", "date": "2026-10-25", "time": "2026-10-25 14:30 UTC", "venue": "Cappoquin Logistics Fraher Field, Dungarvan", "home": "Rathgormack", "away": "The Nire", "official_source": "Munster GAA Official Calendar", "official_url": "https://munster.gaa.ie/fixtures/events-calendar/", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "flag_id": "SL-29", "blank_reason": "County board club championship scoring differentials are not published in a unified official GAA statistical feed; left blank."},
        {"id": "gaa-cork-sfc-2026", "sport": "gaelic-football", "competition": "2026 Cork Premier Senior Football Championship Final", "date": "2026-10-25", "time": "2026-10-25 16:00 UTC", "venue": "SuperValu Páirc Uí Chaoimh, Cork", "home": "St Finbarr's", "away": "Nemo Rangers", "official_source": "Munster GAA Official Event", "official_url": "https://munster.gaa.ie/event/2026-cork-premier-senior-football-championship-final/", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "flag_id": "SL-29", "blank_reason": "County board club championship scoring differentials are not published in a unified official GAA statistical feed; left blank."},
        {"id": "gaa-galway-sfc-2026", "sport": "gaelic-football", "competition": "2026 Galway Senior Football Championship Final", "date": "2026-10-25", "time": "2026-10-25 14:00 UTC", "venue": "Pearse Stadium, Galway", "home": "Maigh Cuilinn (Moycullen)", "away": "Salthill-Knocknacarra", "official_source": "GAA Official", "official_url": "https://www.gaa.ie/football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "flag_id": "SL-29", "blank_reason": "County board club championship scoring differentials are not published in a unified official GAA statistical feed; left blank."},
    ]
    for ec in fi["eurocup_r5"][:6]:
        unlined_rows.append({
            "id": ec["game"],
            "sport": "basketball",
            "competition": f"BKT EuroCup 2026-27 — Round 5 (Group {ec['group']})",
            "date": ec["date"],
            "time": ec["start_utc"].replace("T", " ").replace(":00Z", " UTC"),
            "venue": ec["venue"].title(),
            "home": ec["home"],
            "away": ec["away"],
            "official_source": "EuroLeague / EuroCup API v2",
            "official_url": "https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/games",
            "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19",
            "flag_id": "SL-26",
            "blank_reason": "EuroCup standings API endpoint returns empty body on 2026-10-22; left blank rather than inferring club ratings.",
        })

    return {
        "captured_at": "2026-10-22T07:35:00Z",
        "excluded_sports": EXCLUDED_SPORTS,
        "eligible_sports": ELIGIBLE_SPORTS,
        "atp_players": atp_players,
        "tennis_fixtures": tennis_fixtures,
        "pdc_players": pdc_players,
        "darts_fixtures": darts_fixtures,
        "wst_players": wst_players,
        "snooker_fixtures": snooker_fixtures,
        "nhl_teams": vi["nhl_teams"],
        "nhl_fixtures": list(vi["nhl_fixtures"]) + nhl_oct23_24,
        "nba_teams": vi["nba_teams"],
        "nba_2026_opening": nba_2026_opening,
        "nba_fixtures": vi["nba_fixtures"],
        "euroleague_teams": vi["euroleague_teams"],
        "euroleague_fixtures": vi["euroleague_fixtures"],
        "top14_teams": vi["top14_teams"],
        "top14_fixtures": vi["top14_fixtures"],
        "prod2_teams": vi["prod2_teams"],
        "prod2_fixtures": vi["prod2_fixtures"],
        "urc_teams": vi["urc_teams"],
        "urc_r4_fixtures": vi["urc_r4_fixtures"],
        "ehf_teams": vi["ehf_teams"],
        "ehf_fixtures": ehf_fixtures,
        "mlb_teams": fi["mlb_teams"],
        "mlb_fixtures": vi["mlb_fixtures"],
        "cricket_teams": cricket_teams,
        "cricket_fixtures": cricket_fixtures,
        "rlwc_teams": rlwc_teams,
        "rlwc_fixtures": rlwc_fixtures,
        "aflw_teams": aflw_teams,
        "aflw_fixtures": aflw_fixtures,
        "f1_drivers": f1_drivers,
        "f1_matchups": f1_matchups,
        "lol_teams": lol_teams,
        "lol_fixtures": lol_fixtures,
        "golf_matchups": golf_matchups,
        "greyhound_matchups": greyhound_matchups,
        "unlined_rows": unlined_rows,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seed = build_seed()
    OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT} ({len(seed['eligible_sports'])} eligible sports, {len(seed['unlined_rows'])} unlined rows)")


if __name__ == "__main__":
    main()
