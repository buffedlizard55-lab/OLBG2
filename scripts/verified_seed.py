#!/usr/bin/env python3
"""Write cleanroom, primary-source-verified multi-sport inputs to data/verified/.

Every single fixture ID, start time, venue, team record, points tally, ranking
position, and two-year prize sum in this module was retrieved directly from an
official governing-body or league endpoint on 2026-10-21. Where an official
page did not publish a value server-side (e.g. NBA team points for/against on
nba.com/standings, WTA singles rankings, ATP ranks > 100, WST snooker ranks > 36,
ICC cricket ratings/scorecards behind client JS shells, county GAA tables, or
licensed GBGB trap form), the corresponding field is explicitly None so
downstream tables render it blank ('—') and register it on verified/flagged.html.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "verified"

CAPTURE_DATE = "2026-10-22"

# ---------------------------------------------------------------------------
# 2026-10-22 refresh datasets (session arena/50268b75-olbg2).
# NHL team summary: official NHL Stats REST, seasonId=20262027, gameTypeId=2
# (https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2&start=0&limit=50),
# read 2026-10-22 ~01:35Z; all 32 clubs. The two games dated 2026-10-21
# (PHI @ BUF, FLA @ OTT) were still LIVE at capture (2nd intermission), so
# those four clubs' rows exclude that in-progress game — flagged VF-19.
# [Session 26963a2d, 2026-10-22 03:02-03:55Z] BUF/PHI re-read from the Stats
# REST summary (PHI 3-1 BUF final); FLA/OTT rolled forward from the official
# 21-Oct score feed final (FLA 1-5 OTT) using the same REST goal convention,
# and W-L-OTL/points cross-checked against api-web.nhle.com/v1/standings/2026-10-22.
# Goal totals use the Stats REST convention (shootout-winning goal excluded;
# see existing F19 disclosure). W-L-OTL cross-checked 24/24 against the
# per-game records on https://api-web.nhle.com/v1/score/2026-10-22.
NHL_TEAMS = {
    "ANA": {"name": "Anaheim Ducks", "gp": 9, "w": 4, "l": 5, "otl": 0, "gf": 26, "ga": 29, "points": 8},
    "BOS": {"name": "Boston Bruins", "gp": 10, "w": 7, "l": 2, "otl": 1, "gf": 36, "ga": 22, "points": 15},
    "BUF": {"name": "Buffalo Sabres", "gp": 10, "w": 4, "l": 4, "otl": 2, "gf": 28, "ga": 36, "points": 10},
    "CAR": {"name": "Carolina Hurricanes", "gp": 11, "w": 8, "l": 2, "otl": 1, "gf": 42, "ga": 27, "points": 17},
    "CBJ": {"name": "Columbus Blue Jackets", "gp": 8, "w": 3, "l": 5, "otl": 0, "gf": 19, "ga": 29, "points": 6},
    "CGY": {"name": "Calgary Flames", "gp": 8, "w": 2, "l": 6, "otl": 0, "gf": 17, "ga": 37, "points": 4},
    "CHI": {"name": "Chicago Blackhawks", "gp": 9, "w": 3, "l": 6, "otl": 0, "gf": 21, "ga": 36, "points": 6},
    "COL": {"name": "Colorado Avalanche", "gp": 10, "w": 5, "l": 4, "otl": 1, "gf": 41, "ga": 30, "points": 11},
    "DAL": {"name": "Dallas Stars", "gp": 9, "w": 5, "l": 3, "otl": 1, "gf": 22, "ga": 14, "points": 11},
    "DET": {"name": "Detroit Red Wings", "gp": 9, "w": 3, "l": 3, "otl": 3, "gf": 22, "ga": 26, "points": 9},
    "EDM": {"name": "Edmonton Oilers", "gp": 9, "w": 7, "l": 1, "otl": 1, "gf": 41, "ga": 27, "points": 15},
    "FLA": {"name": "Florida Panthers", "gp": 10, "w": 5, "l": 3, "otl": 2, "gf": 31, "ga": 30, "points": 12},
    "LAK": {"name": "Los Angeles Kings", "gp": 7, "w": 1, "l": 4, "otl": 2, "gf": 17, "ga": 27, "points": 4},
    "MIN": {"name": "Minnesota Wild", "gp": 10, "w": 6, "l": 2, "otl": 2, "gf": 31, "ga": 25, "points": 14},
    "MTL": {"name": "Montréal Canadiens", "gp": 9, "w": 4, "l": 3, "otl": 2, "gf": 28, "ga": 34, "points": 10},
    "NJD": {"name": "New Jersey Devils", "gp": 9, "w": 5, "l": 4, "otl": 0, "gf": 29, "ga": 30, "points": 10},
    "NSH": {"name": "Nashville Predators", "gp": 8, "w": 3, "l": 2, "otl": 3, "gf": 23, "ga": 22, "points": 9},
    "NYI": {"name": "New York Islanders", "gp": 9, "w": 5, "l": 3, "otl": 1, "gf": 27, "ga": 19, "points": 11},
    "NYR": {"name": "New York Rangers", "gp": 11, "w": 7, "l": 3, "otl": 1, "gf": 33, "ga": 24, "points": 15},
    "OTT": {"name": "Ottawa Senators", "gp": 10, "w": 7, "l": 3, "otl": 0, "gf": 27, "ga": 24, "points": 14},
    "PHI": {"name": "Philadelphia Flyers", "gp": 12, "w": 3, "l": 6, "otl": 3, "gf": 20, "ga": 36, "points": 9},
    "PIT": {"name": "Pittsburgh Penguins", "gp": 10, "w": 3, "l": 6, "otl": 1, "gf": 32, "ga": 37, "points": 7},
    "SEA": {"name": "Seattle Kraken", "gp": 10, "w": 6, "l": 3, "otl": 1, "gf": 37, "ga": 34, "points": 13},
    "SJS": {"name": "San Jose Sharks", "gp": 10, "w": 5, "l": 4, "otl": 1, "gf": 26, "ga": 34, "points": 11},
    "STL": {"name": "St. Louis Blues", "gp": 9, "w": 4, "l": 4, "otl": 1, "gf": 29, "ga": 29, "points": 9},
    "TBL": {"name": "Tampa Bay Lightning", "gp": 9, "w": 7, "l": 2, "otl": 0, "gf": 31, "ga": 23, "points": 14},
    "TOR": {"name": "Toronto Maple Leafs", "gp": 11, "w": 5, "l": 4, "otl": 2, "gf": 38, "ga": 34, "points": 12},
    "UTA": {"name": "Utah Mammoth", "gp": 10, "w": 7, "l": 3, "otl": 0, "gf": 38, "ga": 31, "points": 14},
    "VAN": {"name": "Vancouver Canucks", "gp": 11, "w": 2, "l": 8, "otl": 1, "gf": 33, "ga": 51, "points": 5},
    "VGK": {"name": "Vegas Golden Knights", "gp": 11, "w": 8, "l": 3, "otl": 0, "gf": 43, "ga": 30, "points": 16},
    "WPG": {"name": "Winnipeg Jets", "gp": 9, "w": 4, "l": 3, "otl": 2, "gf": 24, "ga": 26, "points": 10},
    "WSH": {"name": "Washington Capitals", "gp": 9, "w": 5, "l": 4, "otl": 0, "gf": 30, "ga": 29, "points": 10},
}

# NHL fixtures for 2026-10-22 (all 12 games, gameState FUT) from
# https://api-web.nhle.com/v1/score/2026-10-22, read 2026-10-22.
NHL_FIXTURES = [
    {"game_id": 2026020154, "date": "2026-10-22", "start_utc": "2026-10-22T23:00:00Z", "away": "NSH", "home": "BOS", "venue": "TD Garden"},
    {"game_id": 2026020155, "date": "2026-10-22", "start_utc": "2026-10-22T23:00:00Z", "away": "NYR", "home": "TOR", "venue": "Scotiabank Arena"},
    {"game_id": 2026020156, "date": "2026-10-22", "start_utc": "2026-10-22T23:00:00Z", "away": "SJS", "home": "OTT", "venue": "Canadian Tire Centre"},
    {"game_id": 2026020157, "date": "2026-10-22", "start_utc": "2026-10-22T23:00:00Z", "away": "ANA", "home": "NJD", "venue": "Prudential Center"},
    {"game_id": 2026020158, "date": "2026-10-22", "start_utc": "2026-10-22T23:00:00Z", "away": "FLA", "home": "PIT", "venue": "PPG Paints Arena"},
    {"game_id": 2026020159, "date": "2026-10-22", "start_utc": "2026-10-22T23:30:00Z", "away": "LAK", "home": "NYI", "venue": "UBS Arena"},
    {"game_id": 2026020160, "date": "2026-10-22", "start_utc": "2026-10-23T00:00:00Z", "away": "VGK", "home": "STL", "venue": "Enterprise Center"},
    {"game_id": 2026020161, "date": "2026-10-22", "start_utc": "2026-10-23T00:00:00Z", "away": "WPG", "home": "DAL", "venue": "American Airlines Center"},
    {"game_id": 2026020162, "date": "2026-10-22", "start_utc": "2026-10-23T01:00:00Z", "away": "MIN", "home": "CGY", "venue": "Scotiabank Saddledome"},
    {"game_id": 2026020163, "date": "2026-10-22", "start_utc": "2026-10-23T01:00:00Z", "away": "CAR", "home": "EDM", "venue": "Rogers Place"},
    {"game_id": 2026020164, "date": "2026-10-22", "start_utc": "2026-10-23T02:00:00Z", "away": "UTA", "home": "SEA", "venue": "Climate Pledge Arena"},
    {"game_id": 2026020165, "date": "2026-10-22", "start_utc": "2026-10-23T02:00:00Z", "away": "DET", "home": "VAN", "venue": "Rogers Arena"},
]

# NBA fixtures 2026-10-22 (2 games) and 2026-10-23 (12 games) from the
# official NBA schedule page (https://www.nba.com/schedule?date=2026-10-22),
# read 2026-10-22. Team strength priors remain the completed 2025-26 records in
# data/inputs/nba_teams.json, copied into inputs.json at seed time (VF-01/VF-02).
# [Session arena/1352b77f-olbg2, 2026-10-22 ~07:35Z] The official week page
# (https://www.nba.com/schedule?date=2026-10-24, server-rendered) was re-read
# line by line: the 14 games above matched exactly (tip, venue, game id), and
# 60 further fixtures for 2026-10-24 .. 2026-10-31 were captured from the same
# page (Week 1 closes 25 Oct; Week 2 incl. Emirates NBA Cup group games on
# 30 Oct). This closes VF-14 at matchup level for 22-31 Oct. 1-2 Nov games were
# not part of this page's server render and are not invented. Every game id is
# the official NBA id published in each row's nba.com/game/<slug>-<id> URL.
NBA_FIXTURES = [
    {"game_id": "0022600006", "date": "2026-10-22", "tip_et": "19:00", "away": "CLE", "home": "PHI", "venue": "Xfinity Mobile Arena"},
    {"game_id": "0022600007", "date": "2026-10-22", "tip_et": "21:30", "away": "DEN", "home": "OKC", "venue": "Paycom Center"},
    {"game_id": "0022600099", "date": "2026-10-23", "tip_et": "16:00", "away": "CHI", "home": "MIL", "venue": "Fiserv Forum"},
    {"game_id": "0022600008", "date": "2026-10-23", "tip_et": "19:00", "away": "NYK", "home": "BOS", "venue": "TD Garden"},
    {"game_id": "0022600094", "date": "2026-10-23", "tip_et": "19:00", "away": "ATL", "home": "CHA", "venue": "Spectrum Center"},
    {"game_id": "0022600095", "date": "2026-10-23", "tip_et": "19:00", "away": "DAL", "home": "IND", "venue": "Gainbridge Fieldhouse"},
    {"game_id": "0022600096", "date": "2026-10-23", "tip_et": "19:00", "away": "MIN", "home": "ORL", "venue": "Kia Center"},
    {"game_id": "0022600097", "date": "2026-10-23", "tip_et": "19:00", "away": "TOR", "home": "WAS", "venue": "Capital One Arena"},
    {"game_id": "0022600098", "date": "2026-10-23", "tip_et": "20:00", "away": "DET", "home": "MIA", "venue": "Kaseya Center"},
    {"game_id": "0022600009", "date": "2026-10-23", "tip_et": "21:30", "away": "HOU", "home": "SAS", "venue": "Moody Center"},
    {"game_id": "0022600100", "date": "2026-10-23", "tip_et": "21:30", "away": "NOP", "home": "UTA", "venue": "Delta Center"},
    {"game_id": "0022600101", "date": "2026-10-23", "tip_et": "22:00", "away": "MEM", "home": "GSW", "venue": "Chase Center"},
    {"game_id": "0022600102", "date": "2026-10-23", "tip_et": "22:00", "away": "LAC", "home": "LAL", "venue": "Crypto.com Arena"},
    {"game_id": "0022600103", "date": "2026-10-23", "tip_et": "22:00", "away": "POR", "home": "SAC", "venue": "Golden 1 Center"},
    # 2026-10-24 (Saturday, 8 games) — official nba.com/schedule week page.
    {"game_id": "0022600104", "date": "2026-10-24", "tip_et": "18:00", "away": "MIA", "home": "CHA", "venue": "Spectrum Center"},
    {"game_id": "0022600105", "date": "2026-10-24", "tip_et": "19:30", "away": "BKN", "home": "CLE", "venue": "Rocket Arena"},
    {"game_id": "0022600106", "date": "2026-10-24", "tip_et": "19:30", "away": "MIL", "home": "PHI", "venue": "Xfinity Mobile Arena"},
    {"game_id": "0022600108", "date": "2026-10-24", "tip_et": "20:00", "away": "WAS", "home": "CHI", "venue": "United Center"},
    {"game_id": "0022600109", "date": "2026-10-24", "tip_et": "20:00", "away": "SAS", "home": "DAL", "venue": "American Airlines Center"},
    {"game_id": "0022600107", "date": "2026-10-24", "tip_et": "20:30", "away": "HOU", "home": "ATL", "venue": "State Farm Arena"},
    {"game_id": "0022600110", "date": "2026-10-24", "tip_et": "21:00", "away": "NOP", "home": "DEN", "venue": "Ball Arena"},
    {"game_id": "0022600111", "date": "2026-10-24", "tip_et": "22:00", "away": "GSW", "home": "PHX", "venue": "Mortgage Matchup Center"},
    # 2026-10-25 (Sunday, 7 games).
    {"game_id": "0022600112", "date": "2026-10-25", "tip_et": "17:00", "away": "LAL", "home": "UTA", "venue": "Delta Center"},
    {"game_id": "0022600113", "date": "2026-10-25", "tip_et": "18:00", "away": "IND", "home": "BKN", "venue": "Barclays Center"},
    {"game_id": "0022600114", "date": "2026-10-25", "tip_et": "19:00", "away": "ORL", "home": "NYK", "venue": "Madison Square Garden"},
    {"game_id": "0022600115", "date": "2026-10-25", "tip_et": "19:00", "away": "TOR", "home": "MIN", "venue": "Target Center"},
    {"game_id": "0022600116", "date": "2026-10-25", "tip_et": "19:00", "away": "LAC", "home": "OKC", "venue": "Paycom Center"},
    {"game_id": "0022600117", "date": "2026-10-25", "tip_et": "19:30", "away": "DET", "home": "PHI", "venue": "Xfinity Mobile Arena"},
    {"game_id": "0022600118", "date": "2026-10-25", "tip_et": "21:00", "away": "MEM", "home": "SAC", "venue": "Golden 1 Center"},
    # 2026-10-26 (Monday, 9 games) — NBA.com Week 2.
    {"game_id": "0022600119", "date": "2026-10-26", "tip_et": "19:00", "away": "WAS", "home": "CHA", "venue": "Spectrum Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600120", "date": "2026-10-26", "tip_et": "19:00", "away": "MIN", "home": "CLE", "venue": "Rocket Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600121", "date": "2026-10-26", "tip_et": "19:30", "away": "CHI", "home": "BOS", "venue": "TD Garden", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600122", "date": "2026-10-26", "tip_et": "19:30", "away": "DAL", "home": "MIA", "venue": "Kaseya Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600123", "date": "2026-10-26", "tip_et": "20:00", "away": "IND", "home": "MIL", "venue": "Fiserv Forum", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600124", "date": "2026-10-26", "tip_et": "20:00", "away": "PHX", "home": "OKC", "venue": "Paycom Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600125", "date": "2026-10-26", "tip_et": "20:30", "away": "ATL", "home": "HOU", "venue": "Toyota Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600126", "date": "2026-10-26", "tip_et": "21:00", "away": "MEM", "home": "UTA", "venue": "Delta Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600127", "date": "2026-10-26", "tip_et": "22:00", "away": "GSW", "home": "DEN", "venue": "Ball Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    # 2026-10-27 (Tuesday, 4 games).
    {"game_id": "0022600128", "date": "2026-10-27", "tip_et": "19:30", "away": "BKN", "home": "BOS", "venue": "TD Garden", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600129", "date": "2026-10-27", "tip_et": "20:00", "away": "DET", "home": "NYK", "venue": "Madison Square Garden", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600130", "date": "2026-10-27", "tip_et": "20:00", "away": "SAC", "home": "SAS", "venue": "Frost Bank Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600131", "date": "2026-10-27", "tip_et": "23:00", "away": "POR", "home": "LAL", "venue": "Crypto.com Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    # 2026-10-28 (Wednesday, 12 games).
    {"game_id": "0022600132", "date": "2026-10-28", "tip_et": "19:00", "away": "MIA", "home": "ATL", "venue": "State Farm Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600133", "date": "2026-10-28", "tip_et": "19:00", "away": "WAS", "home": "CLE", "venue": "Rocket Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600134", "date": "2026-10-28", "tip_et": "19:00", "away": "CHA", "home": "DET", "venue": "Little Caesars Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600135", "date": "2026-10-28", "tip_et": "19:00", "away": "PHI", "home": "IND", "venue": "Gainbridge Fieldhouse", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600136", "date": "2026-10-28", "tip_et": "19:30", "away": "ORL", "home": "TOR", "venue": "Scotiabank Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600137", "date": "2026-10-28", "tip_et": "20:00", "away": "NYK", "home": "CHI", "venue": "United Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600138", "date": "2026-10-28", "tip_et": "20:00", "away": "HOU", "home": "MIL", "venue": "Fiserv Forum", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600139", "date": "2026-10-28", "tip_et": "20:00", "away": "GSW", "home": "MIN", "venue": "Target Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600140", "date": "2026-10-28", "tip_et": "20:00", "away": "DEN", "home": "NOP", "venue": "Smoothie King Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600141", "date": "2026-10-28", "tip_et": "21:00", "away": "SAS", "home": "UTA", "venue": "Delta Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600142", "date": "2026-10-28", "tip_et": "21:30", "away": "OKC", "home": "DAL", "venue": "American Airlines Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600143", "date": "2026-10-28", "tip_et": "22:30", "away": "LAL", "home": "LAC", "venue": "Intuit Dome", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    # 2026-10-29 (Thursday, 3 games).
    {"game_id": "0022600144", "date": "2026-10-29", "tip_et": "19:00", "away": "CLE", "home": "ATL", "venue": "State Farm Arena", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600145", "date": "2026-10-29", "tip_et": "20:00", "away": "SAC", "home": "NOP", "venue": "Smoothie King Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600146", "date": "2026-10-29", "tip_et": "22:00", "away": "MEM", "home": "POR", "venue": "Moda Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    # 2026-10-30 (Friday, 10 games) — Emirates NBA Cup group play (official
    # group labels shown on the schedule page are recorded in the competition).
    {"game_id": "0022600015", "date": "2026-10-30", "tip_et": "19:00", "away": "CHA", "home": "WAS", "venue": "Capital One Arena", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — East Group C)"},
    {"game_id": "0022600016", "date": "2026-10-30", "tip_et": "19:30", "away": "CHI", "home": "BOS", "venue": "TD Garden", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — East Group C)"},
    {"game_id": "0022600017", "date": "2026-10-30", "tip_et": "19:30", "away": "DET", "home": "BKN", "venue": "Barclays Center", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — East Group A)"},
    {"game_id": "0022600018", "date": "2026-10-30", "tip_et": "19:30", "away": "NYK", "home": "PHI", "venue": "Xfinity Mobile Arena", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — East Group B)"},
    {"game_id": "0022600019", "date": "2026-10-30", "tip_et": "19:30", "away": "ORL", "home": "TOR", "venue": "Scotiabank Arena", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — East Group A)"},
    {"game_id": "0022600020", "date": "2026-10-30", "tip_et": "20:00", "away": "IND", "home": "MIA", "venue": "Kaseya Center", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — East Group B)"},
    {"game_id": "0022600021", "date": "2026-10-30", "tip_et": "20:00", "away": "HOU", "home": "DAL", "venue": "American Airlines Center", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — West Group A)"},
    {"game_id": "0022600022", "date": "2026-10-30", "tip_et": "20:00", "away": "LAC", "home": "MIN", "venue": "Target Center", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — West Group B)"},
    {"game_id": "0022600023", "date": "2026-10-30", "tip_et": "22:00", "away": "LAL", "home": "GSW", "venue": "Chase Center", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — West Group C)"},
    {"game_id": "0022600024", "date": "2026-10-30", "tip_et": "22:00", "away": "DEN", "home": "PHX", "venue": "Mortgage Matchup Center", "competition": "NBA Regular Season 2026-27 (Emirates NBA Cup — West Group A)"},
    # 2026-10-31 (Saturday, 7 games).
    {"game_id": "0022600147", "date": "2026-10-31", "tip_et": "15:00", "away": "POR", "home": "UTA", "venue": "Delta Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600148", "date": "2026-10-31", "tip_et": "18:00", "away": "PHI", "home": "CHA", "venue": "Spectrum Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600149", "date": "2026-10-31", "tip_et": "19:00", "away": "ATL", "home": "NOP", "venue": "Smoothie King Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600150", "date": "2026-10-31", "tip_et": "20:00", "away": "SAC", "home": "MEM", "venue": "FedExForum", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600151", "date": "2026-10-31", "tip_et": "20:00", "away": "CLE", "home": "MIL", "venue": "Fiserv Forum", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600152", "date": "2026-10-31", "tip_et": "20:00", "away": "MIN", "home": "SAS", "venue": "Frost Bank Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
    {"game_id": "0022600153", "date": "2026-10-31", "tip_et": "20:30", "away": "OKC", "home": "HOU", "venue": "Toyota Center", "competition": "NBA Regular Season 2026-27 (Week 2)"},
]

# EHF Champions League Men 2026/27 group standings after the 21-Oct Round 5
# games (https://ehfcl.eurohandball.com/men/2026-27/standings/), read
# 2026-10-22. Clubs at GP5 have completed Round 5; clubs at GP4 play on 22 Oct.
EHF_TEAMS = {
    "veszprem": {"name": "One Veszprém HC", "group": "A", "gp": 5, "w": 5, "d": 0, "l": 0, "gf": 185, "ga": 146, "pts": 10},
    "fuchse": {"name": "Füchse Berlin", "group": "A", "gp": 5, "w": 3, "d": 0, "l": 2, "gf": 184, "ga": 172, "pts": 6},
    "porto": {"name": "FC Porto", "group": "A", "gp": 5, "w": 1, "d": 1, "l": 3, "gf": 158, "ga": 173, "pts": 3},
    "partizan": {"name": "RK Partizan AdmiralBet", "group": "A", "gp": 5, "w": 0, "d": 1, "l": 4, "gf": 148, "ga": 184, "pts": 1},
    "plock": {"name": "Orlen Wisla Plock", "group": "B", "gp": 4, "w": 3, "d": 0, "l": 1, "gf": 115, "ga": 108, "pts": 6},
    "nantes": {"name": "HBC Nantes", "group": "B", "gp": 5, "w": 3, "d": 0, "l": 2, "gf": 142, "ga": 143, "pts": 6},
    "melsungen": {"name": "MT Melsungen", "group": "B", "gp": 4, "w": 2, "d": 0, "l": 2, "gf": 110, "ga": 112, "pts": 4},
    "vardar": {"name": "HC Vardar 1961", "group": "B", "gp": 5, "w": 1, "d": 0, "l": 4, "gf": 154, "ga": 158, "pts": 2},
    "aalborg": {"name": "Aalborg Håndbold", "group": "C", "gp": 5, "w": 4, "d": 1, "l": 0, "gf": 170, "ga": 145, "pts": 9},
    "psg": {"name": "Paris Saint-Germain", "group": "C", "gp": 5, "w": 3, "d": 1, "l": 1, "gf": 182, "ga": 157, "pts": 7},
    "zagreb": {"name": "HC Zagreb", "group": "C", "gp": 5, "w": 2, "d": 0, "l": 3, "gf": 146, "ga": 158, "pts": 4},
    "celje": {"name": "RK Celje Pivovarna Laško", "group": "C", "gp": 5, "w": 0, "d": 0, "l": 5, "gf": 150, "ga": 188, "pts": 0},
    "sporting": {"name": "Sporting Clube de Portugal", "group": "D", "gp": 4, "w": 3, "d": 1, "l": 0, "gf": 149, "ga": 125, "pts": 7},
    "gog": {"name": "GOG", "group": "D", "gp": 4, "w": 3, "d": 0, "l": 1, "gf": 145, "ga": 139, "pts": 6},
    "szeged": {"name": "OTP Bank - PICK Szeged", "group": "D", "gp": 4, "w": 1, "d": 1, "l": 2, "gf": 139, "ga": 136, "pts": 3},
    "kristianstad": {"name": "IFK Kristianstad", "group": "D", "gp": 4, "w": 0, "d": 0, "l": 4, "gf": 122, "ga": 155, "pts": 0},
    "barca": {"name": "Barça", "group": "E", "gp": 4, "w": 4, "d": 0, "l": 0, "gf": 137, "ga": 104, "pts": 8},
    "aarhus": {"name": "SAH - Aarhus", "group": "E", "gp": 5, "w": 2, "d": 1, "l": 2, "gf": 150, "ga": 163, "pts": 5},
    "dinamo": {"name": "Dinamo Bucuresti", "group": "E", "gp": 5, "w": 1, "d": 1, "l": 3, "gf": 134, "ga": 145, "pts": 3},
    "montpellier": {"name": "Montpellier Handball", "group": "E", "gp": 4, "w": 1, "d": 0, "l": 3, "gf": 116, "ga": 125, "pts": 2},
    "magdeburg": {"name": "SC Magdeburg", "group": "F", "gp": 4, "w": 4, "d": 0, "l": 0, "gf": 141, "ga": 108, "pts": 8},
    "kielce": {"name": "Industria Kielce", "group": "F", "gp": 5, "w": 3, "d": 0, "l": 2, "gf": 155, "ga": 153, "pts": 6},
    "kriens": {"name": "HC Kriens-Luzern", "group": "F", "gp": 5, "w": 2, "d": 0, "l": 3, "gf": 158, "ga": 161, "pts": 4},
    "kolstad": {"name": "Kolstad Håndball", "group": "F", "gp": 4, "w": 0, "d": 0, "l": 4, "gf": 111, "ga": 143, "pts": 0},
}

# EHF Round 5 fixtures on 2026-10-22, re-verified 2026-10-22 on the official
# match centre (https://ehfcl.eurohandball.com/men/2026-27/matches/); the seven
# R5 fixtures played on 21 Oct are retired as completed.
EHF_FIXTURES = [
    {"id": "ehfcl-202711020101043", "ehf_match_id": "202711020101043", "date": "2026-10-22", "time_local": "18:45", "timezone": "CEST", "start_utc": "2026-10-22T16:45:00Z", "home": "szeged", "away": "gog", "detail_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101043/OTPBankPICKSzeged-GOG/", "venue": None},
    {"id": "ehfcl-202711020101019", "ehf_match_id": "202711020101019", "date": "2026-10-22", "time_local": "18:45", "timezone": "CEST", "start_utc": "2026-10-22T16:45:00Z", "home": "melsungen", "away": "plock", "detail_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101019/MTMelsungen-OrlenWislaPlock/", "venue": None},
    {"id": "ehfcl-202711020101049", "ehf_match_id": "202711020101049", "date": "2026-10-22", "time_local": "20:45", "timezone": "CEST", "start_utc": "2026-10-22T18:45:00Z", "home": "barca", "away": "montpellier", "detail_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101049/Bar%C3%A7a-MontpellierHandball/", "venue": None},
    {"id": "ehfcl-202711020101041", "ehf_match_id": "202711020101041", "date": "2026-10-22", "time_local": "20:45", "timezone": "CEST", "start_utc": "2026-10-22T18:45:00Z", "home": "sporting", "away": "kristianstad", "detail_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101041/SportingClubedePortugal-IFKKristianstad/", "venue": None},
    {"id": "ehfcl-202711020101064", "ehf_match_id": "202711020101064", "date": "2026-10-22", "time_local": "20:45", "timezone": "CEST", "start_utc": "2026-10-22T18:45:00Z", "home": "kolstad", "away": "magdeburg", "detail_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101064/KolstadH%C3%A5ndball-SCMagdeburg/", "venue": None},
]

# MLB 2026 World Series Games 1-4 (the guaranteed games; Games 5-7 are
# 'if necessary' in the official feed and are not published), verified
# 2026-10-22 on https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-10-31.
# Team run totals are the official 2026 regular-season standings values
# (https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason).
MLB_TEAMS = {
    "TB": {"name": "Tampa Bay Rays", "wins": 98, "losses": 64, "runs_scored": 736, "runs_allowed": 650},
    "MIL": {"name": "Milwaukee Brewers", "wins": 103, "losses": 59, "runs_scored": 832, "runs_allowed": 618},
}

MLB_FIXTURES = [
    {"id": "mlb-849805", "game_pk": 849805, "official_date": "2026-10-23", "game_date_utc": "2026-10-24T00:00:00Z", "away": "TB", "home": "MIL", "venue": "American Family Field", "description": "World Series Game 1", "human_url": "https://www.mlb.com/gameday/849805"},
    {"id": "mlb-849802", "game_pk": 849802, "official_date": "2026-10-24", "game_date_utc": "2026-10-25T00:00:00Z", "away": "TB", "home": "MIL", "venue": "American Family Field", "description": "World Series Game 2", "human_url": "https://www.mlb.com/gameday/849802"},
    {"id": "mlb-849804", "game_pk": 849804, "official_date": "2026-10-26", "game_date_utc": "2026-10-27T00:00:00Z", "away": "MIL", "home": "TB", "venue": "Tropicana Field", "description": "World Series Game 3", "human_url": "https://www.mlb.com/gameday/849804"},
    {"id": "mlb-849803", "game_pk": 849803, "official_date": "2026-10-27", "game_date_utc": "2026-10-28T00:00:00Z", "away": "MIL", "home": "TB", "venue": "Tropicana Field", "description": "World Series Game 4", "human_url": "https://www.mlb.com/gameday/849803"},
]

EXCLUDED_SPORTS = [
    {"slug": "soccer", "label": "Soccer / Football", "olbg_sport_id": 1, "olbg_url": "https://www.olbg.com/betting-tips/Football/1", "reason": "Excluded by project scope ('soccer', 'football')"},
    {"slug": "horse-racing", "label": "Horse Racing", "olbg_sport_id": 2, "olbg_url": "https://www.olbg.com/betting-tips/Horse_Racing/2", "reason": "Excluded by project scope ('horse racing')"},
    {"slug": "american-football", "label": "American Football", "olbg_sport_id": 11, "olbg_url": "https://www.olbg.com/betting-tips/American_Football/11", "reason": "Excluded by project scope ('american football')"},
    {"slug": "boxing", "label": "Boxing", "olbg_sport_id": 6, "olbg_url": "https://www.olbg.com/betting-tips/Boxing/6", "reason": "Excluded by project scope ('boxing')"},
    {"slug": "ufc-mma", "label": "UFC / MMA", "olbg_sport_id": 27, "olbg_url": "https://www.olbg.com/betting-tips/UFC_MMA/27", "reason": "Excluded by project scope ('ufc', 'mma')"},
    {"slug": "hurling", "label": "Hurling", "olbg_sport_id": 26, "olbg_url": "https://www.olbg.com/betting-tips/Hurling/26", "reason": "Excluded by project scope ('hurling')"},
    {"slug": "cycling", "label": "Cycling", "olbg_sport_id": None, "olbg_url": "https://www.olbg.com/betting-tips", "reason": "Excluded by project scope ('cycling'); no active OLBG sport hub on 2026-10-21"},
    {"slug": "specials", "label": "Specials / Entertainment & Politics", "olbg_sport_id": None, "olbg_url": "https://www.olbg.com/betting-tips", "reason": "Excluded by project scope ('specials'); no active OLBG sport hub on 2026-10-21"},
]

ELIGIBLE_SPORTS = [
    {
        "slug": "ice-hockey",
        "name": "Ice Hockey",
        "olbg_sport_id": 13,
        "olbg_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13",
        "governing_body": "National Hockey League (NHL)",
        "official_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "markets_investigated": ["Moneyline (2-way)", "Puck Line (-1.5 / +1.5)", "Game Total (Over/Under)"],
        "status_summary": "12 NHL fixtures on 22 Oct 2026 verified and fully originated across all 3 markets from fresh official 2026-27 team goal rates (NHL Stats REST, captured 2026-10-22). The two 21 Oct rows are completed and retired.",
    },
    {
        "slug": "basketball",
        "name": "Basketball",
        "olbg_sport_id": 19,
        "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19",
        "governing_body": "NBA & Euroleague Basketball (EuroLeague + BKT EuroCup)",
        "official_url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/",
        "markets_investigated": ["Moneyline (2-way)", "Point Spread / Handicap", "Game Total (Over/Under)"],
        "status_summary": "83 fixtures verified and originated: 74 NBA regular-season games of 22–31 Oct from the official NBA week schedule (Moneyline + Spread with 2025-26 priors re-verified 30/30 against nba.com/standings; Totals blank — no official PF/PA feed; 10 of the 30 Oct games are Emirates NBA Cup group games) and 9 EuroLeague Round 7 games. BKT EuroCup Round 4 rows are completed and retired; Round 5's 16 fixtures are published in the forward layer (VF-20 closed there).",
    },
    {
        "slug": "rugby-union",
        "name": "Rugby Union",
        "olbg_sport_id": 9,
        "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9",
        "governing_body": "Ligue Nationale de Rugby (Top 14 & Pro D2) & United Rugby Championship",
        "official_url": "https://top14.lnr.fr/classement",
        "markets_investigated": ["Match Result 1X2 & Draw-No-Bet Winner", "Point Handicap", "Match Total Points"],
        "status_summary": "31 fixtures verified and originated across all 3 markets: 7 Top 14 J7 matches, 8 Pro D2 J8 matches, 8 URC Round 4 matches and 8 URC Round 5 matches.",
    },
    {
        "slug": "handball",
        "name": "Handball",
        "olbg_sport_id": 20,
        "olbg_url": "https://www.olbg.com/betting-tips/Handball/20",
        "governing_body": "European Handball Federation (EHF Champions League Men)",
        "official_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/",
        "markets_investigated": ["Match Result 1X2 & 2-Way Winner", "Goal Handicap", "Match Total Goals"],
        "status_summary": "5 EHF Champions League Men Round 5 fixtures on 22 Oct 2026 verified and originated across all 3 markets from the fresh official 24-club standings (post 21-Oct Round 5 games); the 7 fixtures completed on 21 Oct are retired.",
    },
    {
        "slug": "darts",
        "name": "Darts",
        "olbg_sport_id": 15,
        "olbg_url": "https://www.olbg.com/betting-tips/Darts/15",
        "governing_body": "Professional Darts Corporation (PDC)",
        "official_url": "https://www.pdc.tv/rankings",
        "markets_investigated": ["Match Winner (Best of 11 Legs)", "Leg Handicap (-1.5 / +1.5)", "Total Legs (Over/Under 9.5)"],
        "status_summary": "All 16 PDC European Championship Round 1 ties (22–23 Oct 2026) verified and originated from official PDC Werner Ranking Ladder prize sums for all 32 players, plus 2 tournament outrights catalogued.",
    },
    {
        "slug": "tennis",
        "name": "Tennis",
        "olbg_sport_id": 3,
        "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3",
        "governing_body": "ATP Tour & WTA Tour",
        "official_url": "https://www.atptour.com/en/rankings/singles",
        "markets_investigated": ["Match Winner (Best of 3 Sets)", "Set Handicap (-1.5 / +1.5 Sets)", "Total Sets (Over/Under 2.5)"],
        "status_summary": "No originated tennis rows on 2026-10-22: the seven 21-Oct ATP ties are completed and retired, and the official ATP scores page read today published only completed results with no server-rendered next-round order of play (VF-20).",
    },
    {
        "slug": "snooker",
        "name": "Snooker",
        "olbg_sport_id": 8,
        "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8",
        "governing_body": "World Snooker Tour (WST)",
        "official_url": "https://www.wst.tv/matches/",
        "markets_investigated": ["Match Winner (Best of 7 Frames)", "Frame Handicap (-1.5 / +1.5)", "Total Frames (Over/Under 5.5)"],
        "status_summary": "All 8 BetVictor Northern Ireland Open Round 3 ties on 22 Oct 2026 verified on the WST Match Centre and listed without prices: no Round 3 tie pairs two players with captured WST Top-36 prize values, and the official pages read do not state the Round 3 frame format, so no price is inferred (see flagged page). Round 2 was completed on 21 Oct and its rows are retired.",
    },
    {
        "slug": "baseball",
        "name": "Baseball",
        "olbg_sport_id": 12,
        "olbg_url": "https://www.olbg.com/betting-tips/Baseball/12",
        "governing_body": "Major League Baseball (MLB)",
        "official_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-21&endDate=2026-10-26",
        "markets_investigated": ["Moneyline (2-way)", "Run Line (-1.5 / +1.5)", "Game Total (Over/Under 7.5 & Alt 5.5)"],
        "status_summary": "2026 MLB World Series Games 1–4 (Tampa Bay Rays v Milwaukee Brewers, gamePk 849805/849802/849804/849803) verified and originated across all 3 markets from official 162-game run records; conditional Games 5–7 are not published.",
    },
    {
        "slug": "motor-racing",
        "name": "Motor Racing",
        "olbg_sport_id": 14,
        "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        "governing_body": "FIA Formula One World Championship",
        "official_url": "https://www.formula1.com/en/results/2026/drivers",
        "markets_investigated": ["Grand Prix Outright Winner", " Championship Outright Leader", "Podium / Head-to-Head Margin"],
        "status_summary": "2026 United States Grand Prix and 2026 F1 Drivers' World Championship originated from official 17-round FIA championship standings (Kimi Antonelli 340 pts, George Russell 238 pts); 2027 World Championship left unlined.",
    },
    {
        "slug": "volleyball",
        "name": "Volleyball",
        "olbg_sport_id": 21,
        "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21",
        "governing_body": "Polska Liga Siatkówki (PlusLiga) & CEV",
        "official_url": "https://www.plusliga.pl/games.html",
        "markets_investigated": ["Match Winner", "Set Handicap", "Total Points / Sets"],
        "status_summary": "3 Polish PlusLiga fixtures listed without prices: every club has played only a handful of 2026/27 matches, so no defensible line can be originated yet; the 21-Oct Lublin v Gdańsk row is completed and retired.",
    },
    {
        "slug": "cricket",
        "name": "Cricket",
        "olbg_sport_id": 7,
        "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7",
        "governing_body": "International Cricket Council (ICC)",
        "official_url": "https://www.icc-cricket.com/tournaments/mens-cricket-world-cup-league-2",
        "markets_investigated": ["Match Winner (ODI / T20I / Test)", "Innings Runs", "Series Outright"],
        "status_summary": "2 international matches verified on official ICC match URLs (271646, 269791); lines deliberately left blank because ICC ratings render client-side. The 21-Oct tri-series row (274658) is completed and retired.",
    },
    {
        "slug": "golf",
        "name": "Golf",
        "olbg_sport_id": 4,
        "olbg_url": "https://www.olbg.com/betting-tips/Golf/4",
        "governing_body": "PGA Tour & DP World Tour",
        "official_url": "https://www.pgatour.com/schedule",
        "markets_investigated": ["Tournament Outright Winner", "Each-Way Top 5 / Top 10"],
        "status_summary": "2 tour events verified on live OLBG (Bank of Utah Championship, Genesis Championship); lines intentionally left blank pending full field strokes-gained feed.",
    },
    {
        "slug": "rugby-league",
        "name": "Rugby League",
        "olbg_sport_id": 10,
        "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10",
        "governing_body": "National Rugby League (NRL) & Super League",
        "official_url": "https://www.nrl.com/draw/",
        "markets_investigated": ["2027 Grand Final / Premiership Outright", "Series Winner"],
        "status_summary": "3 active 2027 futures verified on live OLBG (2695857, 2801554, 2801600 — correcting empty survey snapshot); lines left blank during pre-2027 off-season.",
    },
    {
        "slug": "gaelic-football",
        "name": "Gaelic Football",
        "olbg_sport_id": 25,
        "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25",
        "governing_body": "Gaelic Athletic Association (GAA)",
        "official_url": "https://www.gaa.ie/football",
        "markets_investigated": ["Match Result", "Handicap", "All-Ireland Outright"],
        "status_summary": "5 live OLBG markets catalogued (4 county club ties + All-Ireland 2027); lines left blank because county club points tables are not published in unified GAA standings.",
    },
    {
        "slug": "greyhounds",
        "name": "Greyhounds",
        "olbg_sport_id": 28,
        "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28",
        "governing_body": "Greyhound Board of Great Britain (GBGB)",
        "official_url": "https://www.gbgb.org.uk/racing/results/",
        "markets_investigated": ["Win Trap", "Forecast / Tricast"],
        "status_summary": "No greyhound rows on 2026-10-22: the six 21-Oct cards are completed and retired, and trap sectional ratings require a licensed GBGB feed that was not captured this refresh (VF-22).",
    },
    {
        "slug": "aussie-rules",
        "name": "Aussie Rules",
        "olbg_sport_id": 22,
        "olbg_url": "https://www.olbg.com/betting-tips/Aussie_Rules/22",
        "governing_body": "Australian Football League (AFL)",
        "official_url": "https://www.afl.com.au/fixture",
        "markets_investigated": ["Match Winner", "Line / Handicap", "Total Score"],
        "status_summary": "Live OLBG hub opened on 2026-10-21 and confirmed to list 0 active tips during the post-Grand-Final AFL off-season.",
    },
    {
        "slug": "esports",
        "name": "eSports",
        "olbg_sport_id": 23,
        "olbg_url": "https://www.olbg.com/betting-tips/eSports/23",
        "governing_body": "Riot LoL Esports / Valve CS2",
        "official_url": "https://lolesports.com/schedule",
        "markets_investigated": ["Match Winner", "Map Handicap", "Total Maps"],
        "status_summary": "Live OLBG hub opened on 2026-10-21 and confirmed to list 0 active tips ('No tips found').",
    },
]

# Official EuroLeague 2026-27 standings after Round 6 (https://www.euroleaguebasketball.net/en/euroleague/standings/)
EUROLEAGUE_TEAMS = {
    "PAO": {"name": "Panathinaikos AKTOR Athens", "gp": 6, "w": 5, "l": 1, "pf": 528, "pa": 438, "home": "4-1", "away": "1-0", "rank": 1, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/panathinaikos-aktor-athens/pan/"},
    "FBT": {"name": "Fenerbahce Tarfin Istanbul", "gp": 6, "w": 5, "l": 1, "pf": 501, "pa": 447, "home": "5-0", "away": "0-1", "rank": 2, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/fenerbahce-tarfin-istanbul/ulk/"},
    "OLY": {"name": "Olympiacos Piraeus", "gp": 6, "w": 5, "l": 1, "pf": 564, "pa": 524, "home": "1-0", "away": "4-1", "rank": 3, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/olympiacos-piraeus/oly/"},
    "VBC": {"name": "Valencia Basket", "gp": 6, "w": 4, "l": 2, "pf": 583, "pa": 537, "home": "2-2", "away": "2-0", "rank": 4, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/valencia-basket/pam/"},
    "CZV": {"name": "Crvena Zvezda Meridianbet Belgrade", "gp": 6, "w": 4, "l": 2, "pf": 485, "pa": 457, "home": "2-2", "away": "2-0", "rank": 5, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/crvena-zvezda-meridianbet-belgrade/red/"},
    "HTA": {"name": "Hapoel IBI Tel Aviv", "gp": 6, "w": 4, "l": 2, "pf": 540, "pa": 520, "home": "2-1", "away": "2-1", "rank": 6, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/hapoel-ibi-tel-aviv/hta/"},
    "VIR": {"name": "Virtus Bologna", "gp": 6, "w": 4, "l": 2, "pf": 525, "pa": 518, "home": "2-0", "away": "2-2", "rank": 7, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/virtus-bologna/vir/"},
    "DUB": {"name": "Dubai Basketball", "gp": 6, "w": 4, "l": 2, "pf": 490, "pa": 493, "home": "2-1", "away": "2-1", "rank": 8, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/dubai-basketball/dub/"},
    "RMB": {"name": "Real Madrid", "gp": 6, "w": 3, "l": 3, "pf": 554, "pa": 531, "home": "2-0", "away": "1-3", "rank": 9, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/real-madrid/mad/"},
    "BAR": {"name": "FC Barcelona", "gp": 6, "w": 3, "l": 3, "pf": 534, "pa": 525, "home": "2-2", "away": "1-1", "rank": 10, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/fc-barcelona/bar/"},
    "BJK": {"name": "Besiktas Istanbul", "gp": 6, "w": 3, "l": 3, "pf": 554, "pa": 555, "home": "1-2", "away": "2-1", "rank": 11, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/besiktas-istanbul/bes/"},
    "PAR": {"name": "Partizan Mozzart Bet Belgrade", "gp": 6, "w": 3, "l": 3, "pf": 466, "pa": 471, "home": "1-1", "away": "2-2", "rank": 12, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/partizan-mozzart-bet-belgrade/par/"},
    "EFS": {"name": "Anadolu Efes Istanbul", "gp": 6, "w": 2, "l": 4, "pf": 492, "pa": 510, "home": "1-1", "away": "1-3", "rank": 13, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/anadolu-efes-istanbul/ist/"},
    "ZAL": {"name": "Zalgiris Kaunas", "gp": 6, "w": 2, "l": 4, "pf": 490, "pa": 517, "home": "0-2", "away": "2-2", "rank": 14, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/zalgiris-kaunas/zal/"},
    "BAY": {"name": "FC Bayern Munich", "gp": 6, "w": 2, "l": 4, "pf": 521, "pa": 552, "home": "0-2", "away": "2-2", "rank": 15, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/fc-bayern-munich/mun/"},
    "MTA": {"name": "Maccabi Rapyd Tel Aviv", "gp": 6, "w": 2, "l": 4, "pf": 509, "pa": 540, "home": "1-1", "away": "1-3", "rank": 16, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/maccabi-rapyd-tel-aviv/tel/"},
    "ASV": {"name": "LDLC ASVEL Villeurbanne", "gp": 6, "w": 2, "l": 4, "pf": 527, "pa": 572, "home": "1-2", "away": "1-2", "rank": 17, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/ldlc-asvel-villeurbanne/asv/"},
    "PBB": {"name": "Paris Basketball", "gp": 6, "w": 1, "l": 5, "pf": 504, "pa": 545, "home": "1-3", "away": "0-2", "rank": 18, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/paris-basketball/prs/"},
    "MIL": {"name": "Armani Olimpia Milan", "gp": 6, "w": 1, "l": 5, "pf": 504, "pa": 559, "home": "1-2", "away": "0-3", "rank": 19, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/armani-olimpia-milan/mil/"},
    "KBA": {"name": "Kosner Baskonia Vitoria-Gasteiz", "gp": 6, "w": 1, "l": 5, "pf": 504, "pa": 564, "home": "1-3", "away": "0-2", "rank": 20, "url": "https://www.euroleaguebasketball.net/en/euroleague/teams/kosner-baskonia-vitoria-gasteiz/bas/"},
}

EUROLEAGUE_FIXTURES = [
    # el-E2026-61 (HTA v VIR, 21 Oct) retired as completed in the 22-Oct refresh.
    {"id": "el-E2026-64", "date": "2026-10-22", "time": "2026-10-22 17:30 UTC", "home": "EFS", "away": "BJK", "venue": "Turkcell Basketball Development Center", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/anadolu-efes-istanbul-besiktas-istanbul/E2026/64/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-65", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "home": "BAY", "away": "DUB", "venue": "SAP Garden", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/fc-bayern-munich-dubai-basketball/E2026/65/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-62", "date": "2026-10-22", "time": "2026-10-22 18:05 UTC", "home": "MTA", "away": "RMB", "venue": "Aleksandar Nikolic Hall", "neutral": True, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/maccabi-rapyd-tel-aviv-real-madrid/E2026/62/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-67", "date": "2026-10-22", "time": "2026-10-22 18:15 UTC", "home": "PAO", "away": "KBA", "venue": "Telekom Center Athens", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/panathinaikos-aktor-athens-kosner-baskonia-vitoria-gasteiz/E2026/67/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-63", "date": "2026-10-22", "time": "2026-10-22 18:30 UTC", "home": "MIL", "away": "BAR", "venue": "Unipol Forum", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/armani-olimpia-milan-fc-barcelona/E2026/63/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-66", "date": "2026-10-22", "time": "2026-10-22 18:45 UTC", "home": "PAR", "away": "CZV", "venue": "Belgrade Arena", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/partizan-mozzart-bet-belgrade-crvena-zvezda-meridianbet-belgrade/E2026/66/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-68", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "home": "ZAL", "away": "ASV", "venue": "Zalgirio Arena", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/zalgiris-kaunas-ldlc-asvel-villeurbanne/E2026/68/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-70", "date": "2026-10-23", "time": "2026-10-23 18:15 UTC", "home": "OLY", "away": "FBT", "venue": "Sunel Arena", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/olympiacos-piraeus-fenerbahce-tarfin-istanbul/E2026/70/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
    {"id": "el-E2026-69", "date": "2026-10-23", "time": "2026-10-23 18:45 UTC", "home": "PBB", "away": "VBC", "venue": "Adidas Arena", "neutral": False, "url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/paris-basketball-valencia-basket/E2026/69/", "olbg_url": "https://www.olbg.com/betting-tips/Basketball/19"},
]

# Official BKT EuroCup 2026-27 standings (https://www.euroleaguebasketball.net/en/eurocup/standings/)
EUROCUP_TEAMS = {
    "JLM": {"name": "Hapoel Midtown Jerusalem", "group": "A", "gp": 3, "w": 3, "l": 0, "pf": 254, "pa": 221, "home": "1-0", "away": "2-0", "rank": 2},
    "RIG": {"name": "Riga Zelli", "group": "A", "gp": 3, "w": 2, "l": 1, "pf": 261, "pa": 250, "home": "2-0", "away": "0-1", "rank": 3},
    "UBT": {"name": "U-BT Cluj-Napoca", "group": "B", "gp": 3, "w": 2, "l": 1, "pf": 247, "pa": 256, "home": "1-0", "away": "1-1", "rank": 3},
    "LDN": {"name": "London Lions", "group": "B", "gp": 3, "w": 1, "l": 2, "pf": 236, "pa": 232, "home": "1-1", "away": "0-1", "rank": 6},
    "ULM": {"name": "ratiopharm ulm", "group": "D", "gp": 3, "w": 2, "l": 1, "pf": 289, "pa": 278, "home": "2-0", "away": "0-1", "rank": 3},
    "PBC": {"name": "PAOK Thessaloniki", "group": "D", "gp": 3, "w": 2, "l": 1, "pf": 254, "pa": 245, "home": "1-0", "away": "1-1", "rank": 4},
    "BKS": {"name": "Bahcesehir College Istanbul", "group": "D", "gp": 3, "w": 3, "l": 0, "pf": 291, "pa": 227, "home": "2-0", "away": "1-0", "rank": 1},
    "BOS": {"name": "BOSNA BH Telecom Sarajevo", "group": "D", "gp": 3, "w": 0, "l": 3, "pf": 237, "pa": 252, "home": "0-1", "away": "0-2", "rank": 7},
}

# Retired in the 22-Oct refresh: the four BKT EuroCup R4 fixtures were played
# on 2026-10-21. Round 5 fixtures were not captured in this refresh (VF-20),
# so the list is intentionally empty rather than carried stale.
EUROCUP_FIXTURES = []

# Official Top 14 2026-27 standings after J6 (https://top14.lnr.fr/classement)
TOP14_TEAMS = {
    "toulouse": {"name": "Stade Toulousain", "rank": 1, "pts": 24, "gp": 6, "w": 5, "d": 0, "l": 1, "pf": 197, "pa": 124, "form": "W-W-W-W-W"},
    "pau": {"name": "Section Paloise", "rank": 2, "pts": 22, "gp": 6, "w": 5, "d": 0, "l": 1, "pf": 239, "pa": 181, "form": "W-L-W-W-W"},
    "bordeaux": {"name": "Union Bordeaux-Bègles", "rank": 3, "pts": 19, "gp": 6, "w": 4, "d": 0, "l": 2, "pf": 215, "pa": 151, "form": "L-W-L-W-W"},
    "la_rochelle": {"name": "Stade Rochelais", "rank": 4, "pts": 18, "gp": 6, "w": 4, "d": 0, "l": 2, "pf": 144, "pa": 135, "form": "W-L-L-W-W"},
    "bayonne": {"name": "Aviron Bayonnais", "rank": 5, "pts": 17, "gp": 6, "w": 4, "d": 0, "l": 2, "pf": 190, "pa": 214, "form": "L-W-W-W-L"},
    "paris": {"name": "Stade Français Paris", "rank": 6, "pts": 14, "gp": 6, "w": 3, "d": 0, "l": 3, "pf": 147, "pa": 158, "form": "L-L-W-L-W"},
    "montpellier": {"name": "Montpellier Hérault Rugby", "rank": 7, "pts": 14, "gp": 6, "w": 3, "d": 0, "l": 3, "pf": 163, "pa": 122, "form": "W-W-L-W-L"},
    "lyon": {"name": "LOU Rugby", "rank": 8, "pts": 14, "gp": 6, "w": 3, "d": 0, "l": 3, "pf": 193, "pa": 202, "form": "W-W-L-L-L"},
    "perpignan": {"name": "USA Perpignan", "rank": 9, "pts": 13, "gp": 6, "w": 3, "d": 0, "l": 3, "pf": 166, "pa": 199, "form": "W-L-W-L-W"},
    "toulon": {"name": "RC Toulon", "rank": 10, "pts": 12, "gp": 6, "w": 2, "d": 0, "l": 4, "pf": 130, "pa": 130, "form": "L-L-W-L-W"},
    "clermont": {"name": "ASM Clermont", "rank": 11, "pts": 11, "gp": 6, "w": 2, "d": 0, "l": 4, "pf": 140, "pa": 169, "form": "W-L-W-L-L"},
    "racing92": {"name": "Racing 92", "rank": 12, "pts": 10, "gp": 6, "w": 2, "d": 0, "l": 4, "pf": 143, "pa": 196, "form": "L-W-L-W-L"},
    "castres": {"name": "Castres Olympique", "rank": 13, "pts": 9, "gp": 6, "w": 2, "d": 0, "l": 4, "pf": 126, "pa": 153, "form": "L-W-L-L-L"},
    "vannes": {"name": "RC Vannes", "rank": 14, "pts": 1, "gp": 6, "w": 0, "d": 0, "l": 6, "pf": 117, "pa": 176, "form": "L-L-L-L-L"},
}

TOP14_FIXTURES = [
    {"id": "top14-11867", "date": "2026-10-24", "time": "2026-10-24 14:35 UTC", "home": "toulouse", "away": "perpignan", "url": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "top14-11861", "date": "2026-10-24", "time": "2026-10-24 14:35 UTC", "home": "bayonne", "away": "lyon", "url": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11861-bayonne-lyon", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "top14-11862", "date": "2026-10-24", "time": "2026-10-24 12:30 UTC", "home": "vannes", "away": "clermont", "url": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11862-vannes-clermont", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "top14-11863", "date": "2026-10-24", "time": "2026-10-24 14:35 UTC", "home": "castres", "away": "paris", "url": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11863-castres-paris", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "top14-11865", "date": "2026-10-24", "time": "2026-10-24 14:35 UTC", "home": "racing92", "away": "montpellier", "url": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11865-racing-92-montpellier", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "top14-11866", "date": "2026-10-24", "time": "2026-10-24 19:00 UTC", "home": "toulon", "away": "pau", "url": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11866-toulon-pau", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "top14-11864", "date": "2026-10-25", "time": "2026-10-25 20:05 UTC", "home": "la_rochelle", "away": "bordeaux", "url": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11864-la-rochelle-bordeaux-begles", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
]

# Official Pro D2 2026-27 standings after J7 (https://prod2.lnr.fr/classement)
PROD2_TEAMS = {
    "oyonnax": {"name": "Oyonnax Rugby", "rank": 1, "pts": 33, "gp": 7, "w": 7, "d": 0, "l": 0, "pf": 313, "pa": 154, "form": "W-W-W-W-W"},
    "provence": {"name": "Provence Rugby", "rank": 2, "pts": 29, "gp": 7, "w": 7, "d": 0, "l": 0, "pf": 222, "pa": 158, "form": "W-W-W-W-W"},
    "grenoble": {"name": "FC Grenoble Rugby", "rank": 3, "pts": 22, "gp": 7, "w": 5, "d": 0, "l": 2, "pf": 213, "pa": 176, "form": "L-W-W-W-W"},
    "brive": {"name": "CA Brive", "rank": 4, "pts": 21, "gp": 7, "w": 5, "d": 0, "l": 2, "pf": 206, "pa": 164, "form": "W-W-W-L-L"},
    "biarritz": {"name": "Biarritz Olympique PB", "rank": 5, "pts": 20, "gp": 7, "w": 4, "d": 1, "l": 2, "pf": 213, "pa": 191, "form": "W-W-W-L-D"},
    "dax": {"name": "US Dax", "rank": 6, "pts": 19, "gp": 7, "w": 4, "d": 0, "l": 3, "pf": 269, "pa": 264, "form": "W-L-W-L-W"},
    "angouleme": {"name": "Soyaux-Angoulême XV", "rank": 7, "pts": 17, "gp": 7, "w": 3, "d": 1, "l": 3, "pf": 220, "pa": 180, "form": "W-L-W-L-D"},
    "montauban": {"name": "US Montauban", "rank": 8, "pts": 17, "gp": 7, "w": 4, "d": 0, "l": 3, "pf": 182, "pa": 214, "form": "L-W-L-W-L"},
    "aurillac": {"name": "Stade Aurillacois", "rank": 9, "pts": 16, "gp": 7, "w": 3, "d": 0, "l": 4, "pf": 240, "pa": 254, "form": "L-L-L-W-W"},
    "agen": {"name": "SU Agen", "rank": 10, "pts": 15, "gp": 7, "w": 3, "d": 0, "l": 4, "pf": 189, "pa": 206, "form": "W-L-L-W-W"},
    "valence": {"name": "Valence Romans", "rank": 11, "pts": 13, "gp": 7, "w": 2, "d": 0, "l": 5, "pf": 192, "pa": 190, "form": "L-L-L-W-L"},
    "colomiers": {"name": "Colomiers Rugby", "rank": 12, "pts": 12, "gp": 7, "w": 2, "d": 0, "l": 5, "pf": 220, "pa": 207, "form": "L-W-L-L-W"},
    "nice": {"name": "Nissa Rugby", "rank": 13, "pts": 11, "gp": 7, "w": 2, "d": 0, "l": 5, "pf": 171, "pa": 213, "form": "L-L-L-W-L"},
    "beziers": {"name": "AS Béziers Hérault", "rank": 14, "pts": 9, "gp": 7, "w": 2, "d": 0, "l": 5, "pf": 147, "pa": 240, "form": "W-L-W-L-L"},
    "narbonne": {"name": "RC Narbonnais", "rank": 15, "pts": 9, "gp": 7, "w": 2, "d": 0, "l": 5, "pf": 186, "pa": 296, "form": "L-W-L-L-L"},
    "nevers": {"name": "USON Nevers", "rank": 16, "pts": 4, "gp": 7, "w": 0, "d": 0, "l": 7, "pf": 146, "pa": 222, "form": "L-L-L-L-L"},
}

PROD2_FIXTURES = [
    {"id": "prod2-12068", "date": "2026-10-22", "time": "2026-10-22 19:00 UTC", "home": "montauban", "away": "oyonnax", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12068-montauban-oyonnax", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "prod2-12063", "date": "2026-10-23", "time": "2026-10-23 17:30 UTC", "home": "agen", "away": "nice", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12063-agen-nice", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "prod2-12064", "date": "2026-10-23", "time": "2026-10-23 19:00 UTC", "home": "provence", "away": "beziers", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12064-provence-rugby-beziers", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "prod2-12065", "date": "2026-10-23", "time": "2026-10-23 17:30 UTC", "home": "angouleme", "away": "dax", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12065-angouleme-dax", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "prod2-12066", "date": "2026-10-23", "time": "2026-10-23 17:30 UTC", "home": "aurillac", "away": "nevers", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12066-aurillac-nevers", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "prod2-12069", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "home": "narbonne", "away": "brive", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12069-narbonne-brive", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "prod2-12070", "date": "2026-10-23", "time": "2026-10-23 17:30 UTC", "home": "valence", "away": "colomiers", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12070-valence-romans-colomiers", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
    {"id": "prod2-12067", "date": "2026-10-23", "time": "2026-10-23 19:00 UTC", "home": "grenoble", "away": "biarritz", "url": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12067-grenoble-biarritz", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9"},
]

# Official EHF Champions League Men R5 -> OLBG live event_id mapping (verified on olbg.com/betting-tips/Handball/20)
EHF_OLBG_MAP = {
    "ehfcl-202711020101059": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101012": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101001": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101032": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101017": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101029": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101070": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101043": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101019": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101049": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101041": "https://www.olbg.com/betting-tips/Handball/20",
    "ehfcl-202711020101064": "https://www.olbg.com/betting-tips/Handball/20",
}

# Official PDC Werner Ranking Ladder positions & 2-year prize money (https://www.pdc.tv/rankings)
PDC_PLAYERS = {
    "Luke Littler": {"rank": 1, "prize_gbp": 3113500},
    "Luke Humphries": {"rank": 2, "prize_gbp": 1062500},
    "Gian van Veen": {"rank": 3, "prize_gbp": 1035750},
    "Gerwyn Price": {"rank": 4, "prize_gbp": 782000},
    "Jonny Clayton": {"rank": 5, "prize_gbp": 706000},
    "James Wade": {"rank": 6, "prize_gbp": 681250},
    "Danny Noppert": {"rank": 7, "prize_gbp": 608500},
    "Josh Rock": {"rank": 8, "prize_gbp": 606500},
    "Michael van Gerwen": {"rank": 10, "prize_gbp": 587500},
    "Nathan Aspinall": {"rank": 11, "prize_gbp": 579500},
    "Wessel Nijman": {"rank": 12, "prize_gbp": 569500},
    "Ross Smith": {"rank": 13, "prize_gbp": 567250},
    "Stephen Bunting": {"rank": 14, "prize_gbp": 566250},
    "Ryan Searle": {"rank": 15, "prize_gbp": 562250},
    "Jermaine Wattimena": {"rank": 16, "prize_gbp": 538750},
    "Chris Dobey": {"rank": 17, "prize_gbp": 534750},
    "Luke Woodhouse": {"rank": 18, "prize_gbp": 506000},
    "Krzysztof Ratajski": {"rank": 19, "prize_gbp": 440000},
    "Dirk van Duijvenbode": {"rank": 20, "prize_gbp": 430500},
    "Damon Heta": {"rank": 21, "prize_gbp": 410750},
    "Rob Cross": {"rank": 22, "prize_gbp": 398500},
    "Ryan Joyce": {"rank": 23, "prize_gbp": 386500},
    "Martin Schindler": {"rank": 24, "prize_gbp": 386250},
    "Kevin Doets": {"rank": 25, "prize_gbp": 375250},
    "Cameron Menzies": {"rank": 26, "prize_gbp": 375000},
    "Andrew Gilding": {"rank": 27, "prize_gbp": 355750},
    "Niels Zonneveld": {"rank": 29, "prize_gbp": 281750},
    "Dave Chisnall": {"rank": 30, "prize_gbp": 281750},
    "William O'Connor": {"rank": 32, "prize_gbp": 274500},
    "Niko Springer": {"rank": 36, "prize_gbp": 239750},
    "Karel Sedlacek": {"rank": 44, "prize_gbp": 177250},
    "Cristo Reyes": {"rank": 71, "prize_gbp": 95000},
}

# Times: the official PDC schedule article (read 2026-10-22 03:30Z, session
# 26963a2d) publishes only the session start — 19:00 CEST (17:00 UTC) on both
# nights — and the match order, which is reproduced here in list order. The
# earlier 30-minute per-match estimates were OLBG's own, rendered in US Eastern.
DARTS_FIXTURES = [
    {"id": "pdc-32324", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "Luke Woodhouse", "p2": "Dirk van Duijvenbode", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Luke_Woodhouse_vs_Dirk_van_Duijvenbode/15?event_id=32324"},
    {"id": "pdc-32330", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "Danny Noppert", "p2": "Stephen Bunting", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Danny_Noppert_vs_Stephen_Bunting/15?event_id=32330"},
    {"id": "pdc-32334", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "Niels Zonneveld", "p2": "Cameron Menzies", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Niels_Zonneveld_vs_Cameron_Menzies/15?event_id=32334"},
    {"id": "pdc-32325", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "Gerwyn Price", "p2": "Rob Cross", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gerwyn_Price_vs_Rob_Cross/15?event_id=32325"},
    {"id": "pdc-32322", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "James Wade", "p2": "Damon Heta", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/James_Wade_vs_Damon_Heta/15?event_id=32322"},
    {"id": "pdc-32337", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "Luke Humphries", "p2": "Ryan Searle", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Luke_Humphries_vs_Ryan_Searle/15?event_id=32337"},
    {"id": "pdc-32323", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "Gian van Veen", "p2": "Andrew Gilding", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gian_van_Veen_vs_Andrew_Gilding/15?event_id=32323"},
    {"id": "pdc-32329", "date": "2026-10-22", "time": "2026-10-22 17:00 UTC", "p1": "Ross Smith", "p2": "Karel Sedlacek", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Ross_Smith_vs_Karel_Sedlacek/15?event_id=32329"},
    {"id": "pdc-32332", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Ryan Joyce", "p2": "Jermaine Wattimena", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Ryan_Joyce_vs_Jermaine_Wattimena/15?event_id=32332"},
    {"id": "pdc-32333", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Krzysztof Ratajski", "p2": "Dave Chisnall", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Krzysztof_Ratajski_vs_Dave_Chisnall/15?event_id=32333"},
    {"id": "pdc-32327", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Nathan Aspinall", "p2": "Cristo Reyes", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Nathan_Aspinall_vs_Cristo_Reyes/15?event_id=32327"},
    {"id": "pdc-32335", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Jonny Clayton", "p2": "Niko Springer", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Jonny_Clayton_vs_Niko_Springer/15?event_id=32335"},
    {"id": "pdc-32328", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Luke Littler", "p2": "William O'Connor", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Luke_Littler_vs_William_OConnor/15?event_id=32328"},
    {"id": "pdc-32326", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Wessel Nijman", "p2": "Martin Schindler", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Wessel_Nijman_vs_Martin_Schindler/15?event_id=32326"},
    {"id": "pdc-32331", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Kevin Doets", "p2": "Michael van Gerwen", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Kevin_Doets_vs_Michael_van_Gerwen/15?event_id=32331"},
    {"id": "pdc-32336", "date": "2026-10-23", "time": "2026-10-23 17:00 UTC", "p1": "Josh Rock", "p2": "Chris Dobey", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Josh_Rock_vs_Chris_Dobey/15?event_id=32336"},
]

# Official PIF ATP Singles Rankings (2026.10.19, https://www.atptour.com/en/rankings/singles)
ATP_PLAYERS = {
    "Arthur Fils": {"rank": 10, "points": 3325, "url": "https://www.atptour.com/en/players/arthur-fils/f0f1/overview"},
    "Tommy Paul": {"rank": 15, "points": 2575, "url": "https://www.atptour.com/en/players/tommy-paul/pl56/overview"},
    "Francisco Cerundolo": {"rank": 21, "points": 2220, "url": "https://www.atptour.com/en/players/francisco-cerundolo/c0au/overview"},
    "Andrey Rublev": {"rank": 22, "points": 2175, "url": "https://www.atptour.com/en/players/andrey-rublev/re44/overview"},
    "Luciano Darderi": {"rank": 23, "points": 2160, "url": "https://www.atptour.com/en/players/luciano-darderi/d0fj/overview"},
    "Lorenzo Musetti": {"rank": 26, "points": 1870, "url": "https://www.atptour.com/en/players/lorenzo-musetti/m0ej/overview"},
    "Tomas Martin Etcheverry": {"rank": 29, "points": 1590, "url": "https://www.atptour.com/en/players/tomas-martin-etcheverry/ea24/overview"},
    "Stefanos Tsitsipas": {"rank": 39, "points": 1330, "url": "https://www.atptour.com/en/players/stefanos-tsitsipas/te51/overview"},
    "Mariano Navone": {"rank": 45, "points": 1151, "url": "https://www.atptour.com/en/players/mariano-navone/n0bs/overview"},
    "Jaume Munar": {"rank": 51, "points": 1010, "url": "https://www.atptour.com/en/players/jaume-munar/mu94/overview"},
    "Tallon Griekspoor": {"rank": 60, "points": 885, "url": "https://www.atptour.com/en/players/tallon-griekspoor/gj37/overview"},
    "Martin Landaluce": {"rank": 67, "points": 822, "url": "https://www.atptour.com/en/players/martin-landaluce/l0il/overview"},
    "Mattia Bellucci": {"rank": 68, "points": 812, "url": "https://www.atptour.com/en/players/mattia-bellucci/b0gg/overview"},
    "Facundo Diaz Acosta": {"rank": 71, "points": 790, "url": "https://www.atptour.com/en/players/facundo-diaz-acosta/d0cg/overview"},
    "Tomas Machac": {"rank": 72, "points": 779, "url": "https://www.atptour.com/en/players/tomas-machac/m0fh/overview"},
    "James Duckworth": {"rank": 73, "points": 774, "url": "https://www.atptour.com/en/players/james-duckworth/d994/overview"},
    "Adrian Mannarino": {"rank": 79, "points": 743, "url": "https://www.atptour.com/en/players/adrian-mannarino/me82/overview"},
    "Damir Dzumhur": {"rank": 83, "points": 712, "url": "https://www.atptour.com/en/players/damir-dzumhur/d923/overview"},
    "Jacob Fearnley": {"rank": 87, "points": 686, "url": "https://www.atptour.com/en/players/jacob-fearnley/f0by/overview"},
    "Dino Prizmic": {"rank": 95, "points": 638, "url": "https://www.atptour.com/en/players/dino-prizmic/p0hw/overview"},
    "Benjamin Bonzi": {"rank": 100, "points": 605, "url": "https://www.atptour.com/en/players/benjamin-bonzi/bm95/overview"},
}

# Retired in the 22-Oct refresh: all seven originated ties were played on
# 2026-10-21. The official ATP scores page read on 2026-10-22 published only
# completed Round-of-16 results with no server-rendered next-round order of
# play, so no replacement ties could be verified (VF-20).
TENNIS_ORIGINATED = []

# Official WST Top-36 rankings (https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false)
# Full 36-row list re-read 2026-10-22 03:40Z (session 26963a2d); the earlier 15-row excerpt matched it 15/15.
WST_TOP36 = {
    "Zhao Xintong": {"rank": 1, "prize_gbp": 1265550},
    "Wu Yize": {"rank": 2, "prize_gbp": 1238900},
    "Judd Trump": {"rank": 3, "prize_gbp": 1114050},
    "Neil Robertson": {"rank": 4, "prize_gbp": 1100200},
    "Mark Selby": {"rank": 5, "prize_gbp": 1070500},
    "John Higgins": {"rank": 6, "prize_gbp": 905000},
    "Shaun Murphy": {"rank": 7, "prize_gbp": 897350},
    "Mark Williams": {"rank": 8, "prize_gbp": 747400},
    "Kyren Wilson": {"rank": 9, "prize_gbp": 716800},
    "Barry Hawkins": {"rank": 10, "prize_gbp": 670050},
    "Chris Wakelin": {"rank": 11, "prize_gbp": 576550},
    "Mark Allen": {"rank": 12, "prize_gbp": 536050},
    "Ronnie O'Sullivan": {"rank": 13, "prize_gbp": 513750},
    "Xiao Guodong": {"rank": 14, "prize_gbp": 503900},
    "Ding Junhui": {"rank": 15, "prize_gbp": 479850},
    "Ali Carter": {"rank": 16, "prize_gbp": 414400},
    "Zhou Yuelong": {"rank": 17, "prize_gbp": 359100},
    "Jack Lisowski": {"rank": 18, "prize_gbp": 358100},
    "Stuart Bingham": {"rank": 19, "prize_gbp": 350550},
    "Chang Bingyu": {"rank": 20, "prize_gbp": 350200},
    "Zhang Anda": {"rank": 21, "prize_gbp": 332600},
    "Thepchaiya Un-Nooh": {"rank": 22, "prize_gbp": 329850},
    "Elliot Slessor": {"rank": 23, "prize_gbp": 329200},
    "Jak Jones": {"rank": 24, "prize_gbp": 319300},
    "Si Jiahui": {"rank": 25, "prize_gbp": 292500},
    "Yuan Sijun": {"rank": 26, "prize_gbp": 288400},
    "Gary Wilson": {"rank": 27, "prize_gbp": 286550},
    "Lei Peifan": {"rank": 28, "prize_gbp": 279050},
    "Pang Junxu": {"rank": 29, "prize_gbp": 272750},
    "Joe O'Connor": {"rank": 30, "prize_gbp": 245450},
    "Noppon Saengkham": {"rank": 31, "prize_gbp": 242500},
    "Hossein Vafaei": {"rank": 32, "prize_gbp": 242450},
    "Stephen Maguire": {"rank": 33, "prize_gbp": 235700},
    "David Gilbert": {"rank": 34, "prize_gbp": 221200},
    "Tom Ford": {"rank": 35, "prize_gbp": 199800},
    "Jackson Page": {"rank": 36, "prize_gbp": 198500},
}

# Retired in the 22-Oct refresh: both priced Round 2 ties were played on
# 2026-10-21 (Jak Jones and Mark Williams advanced). Of the eight Round 3 ties
# only Wilson v Pang pairs two players on the official 36-row ranking list
# (re-read 03:40Z, session 26963a2d); the other seven stay unlined (VF-04/VF-30).
SNOOKER_ORIGINATED = [
    # Round 3 tie whose both players are on the official 36-row ranking list.
    # Start: WST match centre renders 08:00 in the fetcher's US-Eastern zone
    # = 12:00 UTC = 13:00 BST morning session. Format best-of-7 (see VF-30).
    {"id": "wst-2026-r3-m50", "date": "2026-10-22", "time": "2026-10-22 12:00 UTC", "p1": "Kyren Wilson", "p2": "Pang Junxu", "url": "https://www.wst.tv/match-centre/0444240f-c8b2-4382-ba57-bfab6d98f3a7", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
]

# MLB World Series fixtures/teams are defined in the 2026-10-22 refresh block
# at the top of this module (MLB_TEAMS / MLB_FIXTURES, Games 1-4).

# FIA 2026 Formula 1 Drivers' Standings through Round 17 (https://www.formula1.com/en/results/2026/drivers)
F1_DRIVERS = [
    {"rank": 1, "driver": "Kimi Antonelli", "team": "Mercedes", "points": 340},
    {"rank": 2, "driver": "George Russell", "team": "Mercedes", "points": 238},
    {"rank": 3, "driver": "Lewis Hamilton", "team": "Ferrari", "points": 229},
    {"rank": 4, "driver": "Max Verstappen", "team": "Red Bull Racing", "points": 221},
    {"rank": 5, "driver": "Charles Leclerc", "team": "Ferrari", "points": 215},
    {"rank": 6, "driver": "Lando Norris", "team": "McLaren", "points": 201},
    {"rank": 7, "driver": "Oscar Piastri", "team": "McLaren", "points": 138},
    {"rank": 8, "driver": "Isack Hadjar", "team": "Red Bull Racing", "points": 97},
]

# Unlined rows where official fixture/market pages exist, while missing strength inputs are left strictly blank
UNLINED_ROWS = [
    # Snooker Round 3 (22 Oct, verified on the WST Match Centre 2026-10-22): after
    # the full official top-36 re-read only Wilson v Pang pairs two ranked
    # players (priced above); the other seven ties involve a player outside the
    # official list, so they stay blank. Times are UTC (match centre renders ET).
    # The nine Round 2 rows and eight tennis rows of 21 Oct are retired as played.
    {"id": "wst-2026-r3-m51", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Round 3 (Match 51)", "date": "2026-10-22", "time": "2026-10-22 12:00 UTC", "home": "Matthew Selt (outside official top 36)", "away": "Sam Craigie (outside official top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/48c22dd7-97a3-48c3-ab9a-02f81c99d40c", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "blank_reason": "Neither player is on the official 36-row WST ranking list read on 2026-10-22; the official WST pages read do not state the frame format (broadcaster pages say best of 7, see VF-30)."},
    {"id": "wst-2026-r3-m49", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Round 3 (Match 49)", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "home": "Anthony McGill (outside official top 36)", "away": "Mateusz Baranowski (outside official top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/a93c8f6b-ce8e-4ad0-87ad-de4a03594ee5", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "blank_reason": "Neither player is on the official 36-row WST ranking list read on 2026-10-22; the official WST pages read do not state the frame format (broadcaster pages say best of 7, see VF-30)."},
    {"id": "wst-2026-r3-m52", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Round 3 (Match 52)", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "home": "Elliot Slessor (#23, £329,200)", "away": "Ricky Walden (outside official top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/619c8075-153c-41f4-96a8-de15606cbdd8", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "blank_reason": "Ricky Walden's prize value is outside the official 36-row WST ranking list read on 2026-10-22; the official WST pages read do not state the frame format (broadcaster pages say best of 7, see VF-30)."},
    {"id": "wst-2026-r3-m53", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Round 3 (Match 53)", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "home": "David Gilbert (#34, £221,200)", "away": "Cheung Ka Wai (outside official top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/1e3806cf-eec4-42c7-b4fc-ed493bc6e236", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "blank_reason": "Cheung Ka Wai's prize value is outside the official 36-row WST ranking list read on 2026-10-22; the official WST pages read do not state the frame format (broadcaster pages say best of 7, see VF-30)."},
    {"id": "wst-2026-r3-m54", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Round 3 (Match 54)", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "home": "Mark Williams (#8, £747,400)", "away": "Martin O'Donnell (outside official top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/eeff6e2d-f800-4831-a326-29a0e9e3cf6f", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "blank_reason": "Martin O'Donnell's prize value is outside the official 36-row WST ranking list read on 2026-10-22; the official WST pages read do not state the frame format (broadcaster pages say best of 7, see VF-30)."},
    {"id": "wst-2026-r3-m55", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Round 3 (Match 55)", "date": "2026-10-22", "time": "2026-10-22 19:00 UTC", "home": "Jak Jones (#24, £319,300)", "away": "Daniel Wells (outside official top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/ac39f86f-13b2-4688-9041-75fe72943900", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "blank_reason": "Daniel Wells's prize value is outside the official 36-row WST ranking list read on 2026-10-22; the official WST pages read do not state the frame format (broadcaster pages say best of 7, see VF-30)."},
    {"id": "wst-2026-r3-m56", "sport": "snooker", "competition": "BetVictor Northern Ireland Open — Round 3 (Match 56)", "date": "2026-10-22", "time": "2026-10-22 19:00 UTC", "home": "Jordan Brown (outside official top 36)", "away": "Scott Donaldson (outside official top 36)", "official_source": "WST Match Centre", "official_url": "https://www.wst.tv/match-centre/a9ceb4e5-ac12-4aea-94cb-c85b70fbe8ea", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "blank_reason": "Neither player is on the official 36-row WST ranking list read on 2026-10-22; the official WST pages read do not state the frame format (broadcaster pages say best of 7, see VF-30)."},
    # Darts futures
    {"id": "pdc-32338", "sport": "darts", "competition": "2026 PDC European Championship — Outright", "date": "2026-10-25", "time": "2026-10-25 14:00", "home": "32-Player Draw Outright", "away": "Field", "official_source": "PDC Rankings", "official_url": "https://www.pdc.tv/rankings", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/European_Championship/15?event_id=32338", "blank_reason": "Full bracket path across 5 rounds depends on exact draw-half seeding verification; match-by-match R1 lines originated above."},
    {"id": "pdc-26023", "sport": "darts", "competition": "2027 PDC World Darts Championship — Outright", "date": "2027-01-03", "time": "2027-01-03 12:00", "home": "96-Player Field Outright", "away": "Field", "official_source": "PDC Rankings", "official_url": "https://www.pdc.tv/rankings", "olbg_url": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/PDC_World_Championship_2027/15?event_id=26023", "blank_reason": "Qualifying field not yet finalised in October 2026; left unlined."},
    # Motor Racing 2027 outright
    {"id": "f1-2027-champ", "sport": "motor-racing", "competition": "2027 FIA Formula 1 Drivers' World Championship", "date": "2027-03-07", "time": "2027-03-07 05:00", "home": "2027 Season Outright", "away": "20-Driver Grid", "official_source": "Formula 1 Official", "official_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14", "blank_reason": "Next-season championship market prior to 2027 car testing; left blank rather than speculated."},
    # Polish Volleyball (F22)

    {"id": "vb-suwalki-katowice", "sport": "volleyball", "competition": "Polish PlusLiga 2026/27", "date": "2026-10-22", "time": "2026-10-22 16:30", "home": "Ślepsk Malow Suwałki", "away": "GKS Katowice", "official_source": "PlusLiga Schedule", "official_url": "https://www.plusliga.pl/games.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "blank_reason": "Opening-round M=1 sample size insufficient for reliable independent line origination."},
    {"id": "vb-belchatow-warszawa", "sport": "volleyball", "competition": "Polish PlusLiga 2026/27", "date": "2026-10-22", "time": "2026-10-22 18:30", "home": "PGE GiEK Skra Bełchatów", "away": "PGE Projekt Warszawa", "official_source": "PlusLiga Schedule", "official_url": "https://www.plusliga.pl/games.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "blank_reason": "Opening-round M=1 sample size insufficient for reliable independent line origination."},
    {"id": "vb-chelm-rzeszow", "sport": "volleyball", "competition": "Polish PlusLiga 2026/27", "date": "2026-10-23", "time": "2026-10-23 18:30", "home": "InPost ChKS Chełm", "away": "Asseco Resovia Rzeszów", "official_source": "PlusLiga Schedule", "official_url": "https://www.plusliga.pl/games.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "blank_reason": "Opening-round M=1 sample size insufficient for reliable independent line origination."},
    # Cricket ICC matches (F11)

    {"id": "icc-271646", "sport": "cricket", "competition": "New Zealand v India — 1st T20I, Hagley Oval, Christchurch", "date": "2026-10-22", "time": "2026-10-22 07:00 UTC", "home": "New Zealand", "away": "India", "official_source": "ICC Match Centre", "official_url": "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7", "blank_reason": "ICC T20I team-rankings table renders client-side; prices left blank rather than copied from secondary sites."},
    # icc-269791 South Africa v Australia (WTC Test) retired 2026-10-22 by session
    # 26963a2d: the ICC match strip showed it already at Day 4 stumps (SA 425/9d;
    # AUS 99 & 156/4 following on) — it was never a 24-Oct fixture (VF-28).
    # Golf tour events
    {"id": "golf-utah-2026", "sport": "golf", "competition": "PGA Tour — Bank of Utah Championship", "date": "2026-10-22", "time": "2026-10-22 14:00 UTC", "home": "132-Player Strokeplay Field", "away": "Black Desert Resort", "official_source": "PGA Tour Schedule", "official_url": "https://www.pgatour.com/schedule", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4", "blank_reason": "Full 132-golfer strokes-gained distribution not published in static HTML; left unlined."},
    {"id": "golf-genesis-2026", "sport": "golf", "competition": "DP World Tour — Genesis Championship", "date": "2026-10-22", "time": "2026-10-22 02:00 UTC", "home": "120-Player Strokeplay Field", "away": "Woo Jeong Hills CC", "official_source": "DP World Tour Schedule", "official_url": "https://www.europeantour.com/dpworld-tour/schedule/", "olbg_url": "https://www.olbg.com/betting-tips/Golf/4", "blank_reason": "Full field strokes-gained feed not published in static HTML; left unlined."},
    # Rugby League 2027 futures
    {"id": "rl-2695857", "sport": "rugby-league", "competition": "NRL Telstra Premiership 2027 — Outright", "date": "2027-03-04", "time": "2027-03-04 09:00 UTC", "home": "NRL 17-Club Field", "away": "2027 Season", "official_source": "NRL Official Draw", "official_url": "https://www.nrl.com/draw/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10", "blank_reason": "Off-season 2027 outright market prior to final squad registrations; left unlined."},
    {"id": "rl-2801554", "sport": "rugby-league", "competition": "Betfred Super League 2027 — Outright", "date": "2027-02-12", "time": "2027-02-12 20:00 UTC", "home": "Super League 12-Club Field", "away": "2027 Season", "official_source": "Super League Official", "official_url": "https://www.superleague.co.uk/match-centre", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10", "blank_reason": "Off-season 2027 outright market prior to pre-season; left unlined."},
    {"id": "rl-2801600", "sport": "rugby-league", "competition": "Ampol State of Origin 2027 — Series Winner", "date": "2027-06-02", "time": "2027-06-02 10:05 UTC", "home": "Queensland Maroons", "away": "New South Wales Blues", "official_source": "NRL Official", "official_url": "https://www.nrl.com/draw/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10", "blank_reason": "2027 representative squads selected next May; left unlined."},
    # Gaelic Football county & All-Ireland markets
    {"id": "gaa-3530", "sport": "gaelic-football", "competition": "Cork Premier Senior Football Championship", "date": "2026-10-25", "time": "2026-10-25 16:00", "home": "St Finbarr's", "away": "Nemo Rangers", "official_source": "GAA Official", "official_url": "https://www.gaa.ie/football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "blank_reason": "County board club championship scoring tables not available in a unified official feed."},
    {"id": "gaa-3532", "sport": "gaelic-football", "competition": "Galway Senior Football Championship", "date": "2026-10-25", "time": "2026-10-25 14:00", "home": "Maigh Cuilinn (Moycullen)", "away": "Salthill-Knocknacarra", "official_source": "GAA Official", "official_url": "https://www.gaa.ie/football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "blank_reason": "County board club championship scoring tables not available in a unified official feed."},
    {"id": "gaa-3531", "sport": "gaelic-football", "competition": "Cork Senior A Football Championship", "date": "2026-10-25", "time": "2026-10-25 14:00", "home": "Kanturk", "away": "Éire Óg (Cork)", "official_source": "GAA Official", "official_url": "https://www.gaa.ie/football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "blank_reason": "OLBG abbreviates club name as 'Eire Og Cor'; county club scoring feed unavailable."},
    {"id": "gaa-3536", "sport": "gaelic-football", "competition": "Waterford Senior Football Championship", "date": "2026-10-25", "time": "2026-10-25 14:30", "home": "Rathgormack", "away": "The Nire", "official_source": "GAA Official", "official_url": "https://www.gaa.ie/football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "blank_reason": "County board club championship scoring tables not available in a unified official feed."},
    {"id": "gaa-3327", "sport": "gaelic-football", "competition": "All-Ireland Senior Football Championship 2027", "date": "2027-07-25", "time": "2027-07-25 15:30", "home": "Inter-County Outright", "away": "Field", "official_source": "GAA Official", "official_url": "https://www.gaa.ie/football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "blank_reason": "2027 inter-county season not started; left unlined."},
    # Greyhounds: the six 21-Oct race cards are completed and retired in the
    # 22-Oct refresh; 22-Oct cards were not captured (licensed GBGB feed, VF-22).
]

REPO_AUDIT = [
    {
        "id": "RA-01",
        "severity": "critical",
        "layer": "Survey (/survey/)",
        "file": "data/survey/predictions.json (P-02)",
        "published": "England Women v West Indies Women — ICC Women's T20 World Cup 2026 — 2026-10-21 15:00 — HIGH (77.4%)",
        "official": "Tournament concluded four months earlier in June–July 2026; match absent from live OLBG Cricket/7 and cricket.json",
        "source_name": "ICC Official Tournament Page",
        "source_url": "https://www.icc-cricket.com/tournaments/womens-t20-world-cup-2026",
        "resolution": "Purged stale P-02 record and locked deterministic regeneration in unit tests.",
    },
    {
        "id": "RA-02",
        "severity": "critical",
        "layer": "Survey (/survey/)",
        "file": "scripts/survey_analyse.py & data/survey/picks.json",
        "published": "'Afghanistan beat Bangladesh by 200 runs ... Afghanistan 190, Bangladesh 109 in 28.3 overs' + threshold override 0.55 -> HIGH",
        "official": "190 - 109 = 81 runs (two separate Oct 2025 ODIs spliced together from non-official sites); official ICC page 274658 renders body stats client-side",
        "source_name": "ICC Official Match 274658",
        "source_url": "https://www.icc-cricket.com/matches/274658/afghanistan-vs-bangladesh",
        "resolution": "Removed spliced claim, non-official links, and artificial 0.55 HIGH override; marked match unlined ('—').",
    },
    {
        "id": "RA-03",
        "severity": "high",
        "layer": "Survey (/survey/)",
        "file": "data/survey/predictions.json (P-01 Top 14 & P-02)",
        "published": "Claimed Toulouse #2 (4-0-2) & Perpignan #14 (0-0-6) citing wikipedia.org, rugbyrama.fr, allrugby.com, espn.com, racingpost.com",
        "official": "Official LNR Top 14 J6 standings show #1 Stade Toulousain (24 pts, 5W-0D-1L, 197/124, 5 straight wins) vs #9 USA Perpignan (13 pts, 3W-0D-3L, 166/199); #14 is RC Vannes (0W-0D-6L)",
        "source_name": "LNR Official Top 14 Standings",
        "source_url": "https://top14.lnr.fr/classement",
        "resolution": "Replaced 100% of third-party URLs and wrong Wikipedia standings with live LNR/EPCR official figures.",
    },
    {
        "id": "RA-04",
        "severity": "high",
        "layer": "Survey (/survey/)",
        "file": "data/survey/sports.json",
        "published": "21 sports total; omitted Hurling/26, Gaelic_Football/25, and Greyhounds/28",
        "official": "OLBG carries 23 sport hubs: Hurling/26 is active and must be excluded per scope; Gaelic_Football/25 (5 events) and Greyhounds/28 (6 races) are eligible and active",
        "source_name": "OLBG Betting Tips Sitemap",
        "source_url": "https://www.olbg.com/sitemap-betting-tips.xml",
        "resolution": "Expanded sports.json to all 23 OLBG hubs (17 eligible + 6 OLBG-active excluded) and built pages for all 17 eligible sports.",
    },
    {
        "id": "RA-05",
        "severity": "medium",
        "layer": "Survey (/survey/)",
        "file": "data/survey/events/*.json",
        "published": "45 stale 2026-10-18 indexed_snapshot rows; rugby_league.json = []",
        "official": "Live 2026-10-21 crawl confirms 3 active Rugby League outrights (2695857, 2801554, 2801600), 12 EHF CL R5 ties, 16 PDC R1 ties, and 0 tips on Aussie Rules/eSports",
        "source_name": "OLBG Rugby League Hub",
        "source_url": "https://www.olbg.com/betting-tips/Rugby_League/10",
        "resolution": "Replaced all 45 indexed_snapshot rows with live 2026-10-21 OLBG fetches across all 17 eligible sports.",
    },
    {
        "id": "RA-06",
        "severity": "medium",
        "layer": "Survey (/survey/)",
        "file": "scripts/survey_build.py & data/survey/events/*.json",
        "published": "0 of 130 inventory rows had row-level official source links",
        "official": "Every row requires an official governing-body link alongside OLBG for manual verification",
        "source_name": "Euroleague / LNR / EHF / PDC / ATP / WST / NHL / NBA",
        "source_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/",
        "resolution": "Added official_source + official_url to every row in both /survey/ and /verified/.",
    },
    {
        "id": "RA-07",
        "severity": "medium",
        "layer": "Desk (/site/)",
        "file": "data/desk/picks.json (nhl-2026020152)",
        "published": "'Jack Quinn on seven points and Tage Thompson on three goals'",
        "official": "Official NHL API teamLeaders for game 2026020152 lists Tage Thompson (#72, BUF) with 5 goals and Zach Benson (#6, BUF) with 6 assists",
        "source_name": "NHL Official Score API (2026-10-21)",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-21",
        "resolution": "Updated data/desk/picks.json to 5 goals / 6 assists and regenerated /site/ cleanly via scripts/build.py.",
    },
    {
        "id": "RA-08",
        "severity": "low",
        "layer": "Survey (/survey/)",
        "file": "data/survey/lines.json & scripts/survey_lines.py (SL-08, SL-09)",
        "published": "Labels URC fixtures Connacht v Zebre and Munster/Edinburgh round as 'URC Round 6'",
        "official": "Official URC match centre URL is /match-centre/2026-27/4 ('Round 4') and all 16 clubs have PL=3 matches played",
        "source_name": "URC Official Match Centre Round 4",
        "source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4",
        "resolution": "Recorded accurately as Round 4 in /verified/ and /survey/; logged for root owner in COORDINATION.md.",
    },
    {
        "id": "RA-09",
        "severity": "low",
        "layer": "Root (/)",
        "file": "data/inputs/fixtures.json (F03)",
        "published": "Sacramento Kings @ LA Clippers game_id left null",
        "official": "Official NBA schedule publishes game_id 0022600093 (https://www.nba.com/game/sac-vs-lac-0022600093)",
        "source_name": "NBA Official Game Page 0022600093",
        "source_url": "https://www.nba.com/game/sac-vs-lac-0022600093",
        "resolution": "Published with verified game_id 0022600093 in /verified/ and /survey/; logged in COORDINATION.md.",
    },
    {
        "id": "RA-10",
        "severity": "low",
        "layer": "Root (/)",
        "file": "data/predictions.json (nhl-2026020152 & handball W-D-L)",
        "published": "Cites scoreboard/2026-10-22 for 19 Oct PHI-COL score; formats unbeaten 3W-1D-0L handball clubs as '3-1-0' next to NHL W-L-OTL '4-3-2'",
        "official": "19 Oct game sits on score/2026-10-19; EHF standings report 3W, 1D, 0L (unbeaten, 7 pts)",
        "source_name": "EHF Official Standings",
        "source_url": "https://ehfcl.eurohandball.com/men/2026-27/standings/",
        "resolution": "Explicit '3W-1D-0L' notation enforced across all /verified/ and /survey/ narratives.",
    },
]

FLAGGED_ITEMS = [
    {"id": "VF-01", "severity": "medium", "category": "Blank unconfirmed market", "sport": "Basketball (NBA)", "item": "All 11 NBA Game Totals left blank ('—')", "detail": "Official 2025-26 NBA standings on nba.com publish W, L, Home and Road records without points scored/conceded per team. Moneyline and spread are originated from prior-season records; totals are deliberately left blank rather than estimated.", "source_name": "NBA Official Standings (2025-26)", "source_url": "https://www.nba.com/standings?Season=2025-26"},
    {"id": "VF-02", "severity": "medium", "category": "Model cap", "sport": "Basketball (NBA)", "item": "All 11 NBA picks capped at Medium confidence", "detail": "Every club on the 21 October NBA card enters 2026-27 at 0-0. Because lines rely on completed 2025-26 records prior to off-season roster movement taking effect on court, confidence is strictly capped at 'medium'.", "source_name": "NBA 2026-27 Standings", "source_url": "https://www.nba.com/standings"},
    {"id": "VF-03", "severity": "medium", "category": "Blank unconfirmed input", "sport": "Snooker", "item": "9 of 11 WST Northern Ireland Open R2 matches left unlined ('—')", "detail": "World Snooker Tour's official rankings page renders ranks #1–#36 server-side and loads #37+ dynamically. Only the two all-Top-36 ties (Higgins #6 vs Jak Jones #24; Zhang Anda #21 vs Mark Williams #8) are priced; the 9 ties with a #37+ player keep rank and odds blank.", "source_name": "WST Official World Rankings", "source_url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false"},
    {"id": "VF-04", "severity": "medium", "category": "Blank unconfirmed input", "sport": "Tennis", "item": "8 WTA / Challenger / #101+ matches left unlined ('—')", "detail": "ATP Tour renders singles ranks #1–#100 server-side (7 Top-100 matches priced). WTA singles rankings render client-side and ATP ranks > #100 require dynamic pagination, so those 8 matches keep player points and prices blank.", "source_name": "WTA Singles Rankings", "source_url": "https://www.wtatennis.com/rankings/singles"},
    {"id": "VF-05", "severity": "high", "category": "Statistical & CMS guard", "sport": "Volleyball", "item": "4 Polish PlusLiga fixtures left unlined ('—')", "detail": "Clubs have played only M=1 match in 2026/27 (N=1 is insufficient to originate independent prices) and plusliga.pl/table.html redirects to the shared PLS tauronliga.pl template.", "source_name": "PlusLiga Official Games", "source_url": "https://www.plusliga.pl/games.html"},
    {"id": "VF-06", "severity": "high", "category": "Client-rendered source", "sport": "Cricket", "item": "3 ICC international fixtures left unlined ('—')", "detail": "ICC match centres confirm the fixtures (274658, 271646, 269791) in page metadata, while team rating tables and scorecards render 'Loading' client-side. No secondary cricket site was used as a substitute.", "source_name": "ICC Match 274658", "source_url": "https://www.icc-cricket.com/matches/274658/afghanistan-vs-bangladesh"},
    {"id": "VF-07", "severity": "low", "category": "Blank unconfirmed venue", "sport": "Handball & EuroCup", "item": "11 EHF CL venues & 4 EuroCup venues left blank ('—')", "detail": "Only venues explicitly confirmed on opened official match pages (Arena Zagreb for Zagreb–PSG and the 10 EuroLeague arenas) are populated; unverified venues remain blank.", "source_name": "EHF Champions League Matches", "source_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/"},
    {"id": "VF-08", "severity": "low", "category": "Unlined futures / specialist feeds", "sport": "Golf, Rugby League, Gaelic Football", "item": "10 specialist/futures markets catalogued without prices ('—')", "detail": "PGA/DP World Tour 132-man strokes-gained feeds, 2027 pre-roster NRL/Super League futures, and county GAA club tables are not publicly server-rendered; fixtures are linked and prices left blank.", "source_name": "OLBG Sitemap", "source_url": "https://www.olbg.com/sitemap-betting-tips.xml"},
    {"id": "VF-19", "severity": "medium", "category": "Capture-time limitation", "sport": "Ice Hockey (NHL)", "item": "[Resolved by VF-33] FLA/OTT team inputs exclude their still-live 21-Oct game", "detail": "The NHL Stats REST summary and standings were read on 2026-10-22 at ~01:35Z while PHI @ BUF (2-1 PHI after two periods) and FLA @ OTT (3-1 OTT after two periods) were still LIVE on the official Score API. Florida and Ottawa play again on 22 Oct, so their inputs are one in-progress game behind; the effect is bounded (one game of 10) and is disclosed rather than estimated from a live score.", "source_name": "NHL Official Score API (2026-10-21)", "source_url": "https://api-web.nhle.com/v1/score/2026-10-21"},
    {"id": "VF-20", "severity": "medium", "category": "Coverage gap this refresh", "sport": "Basketball (EuroCup) & Tennis", "item": "EuroCup Round 5 and ATP next-round fixtures not captured on 2026-10-22", "detail": "The four BKT EuroCup R4 games were completed on 21 Oct and are retired; the EuroCup game-center page read on 2026-10-22 did not expose a server-rendered Round 5 fixture list in the chunks fetched, so EuroCup carries no rows until a later session captures Round 5 (due ~27-28 Oct). The same applies to ATP quarter-final orders of play (see VF-04). Neither gap was filled from secondary sources.", "source_name": "EuroCup Official Game Center", "source_url": "https://www.euroleaguebasketball.net/en/eurocup/game-center/"},
    {"id": "VF-21", "severity": "low", "category": "Re-verification limit", "sport": "Darts (PDC)", "item": "[Resolved by VF-31] PDC ranking ladder retained from 21-Oct capture", "detail": "pdc.tv/rankings read on 2026-10-22 returned a cookie-consent wall with no server-rendered ladder rows in the fetched content. The 21-Oct captured Werner Ranking Ladder values are retained because no PDC ranking event has been completed between the two captures (the European Championship itself starts on the evening of 22 Oct); flagged so the next session re-reads the ladder after the event.", "source_name": "PDC Official Rankings", "source_url": "https://www.pdc.tv/rankings"},
    {"id": "VF-22", "severity": "low", "category": "Coverage gap this refresh", "sport": "Greyhounds", "item": "No 22-Oct GBGB race cards captured", "detail": "The six 21-Oct cards (Harlow, Monmore, Nottingham, Kinsley) are completed and retired. Trap sectional ratings require a licensed GBGB data feed and no 22-Oct card was captured from an official source in this refresh, so the Greyhounds page currently lists zero rows rather than stale ones.", "source_name": "GBGB Official Results", "source_url": "https://www.gbgb.org.uk/racing/results/"},

    {"id": "VF-23", "severity": "medium", "category": "Verification coverage", "sport": "Cross-sport", "item": "Independent re-read on 2026-10-22 covered 6 of the 18 source families, not all 119 rows [extended by VF-34]", "detail": "Session 072755db re-fetched and compared every published figure against the governing body for: the NHL Stats REST team summary (MIN, CGY, CAR, EDM, BOS, NSH), the URC official table plus its Round 3 results (10 clubs, 5 results), the LNR Top 14 table (Toulouse, Perpignan rank), the LNR Pro D2 table (Provence, Aurillac, Beziers, Nevers), the EuroLeague standings (Panathinaikos, Baskonia) and the EHF Champions League Group E table (Barca, Montpellier), plus the EHF and EuroLeague fixture listings. All compared values matched except the Beziers form sentence corrected under VF-25. The remaining rows (darts, snooker, MLB, F1, golf, cricket, volleyball, rugby league, Gaelic football, NBA) were NOT re-read against their official page in that session. Session arena/1352b77f-olbg2 then re-read eleven source families line by line (see VF-34), covering the darts, snooker, MLB, F1 and NBA families as well; golf, cricket, volleyball, rugby league and Gaelic football rows still carry their earlier capture with the source link on each row for manual review.", "source_name": "URC official table (verification example)", "source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
    {"id": "VF-24", "severity": "medium", "category": "Brief conformance", "sport": "Cross-sport", "item": "[Addressed by VF-33] The 14 written predictions name teams and form but no individual player", "detail": "The brief asks each prediction to include 'the team, player, current form, recent match history'. All 14 /verified/ write-ups (and the 9 root-layer write-ups) state the selection, the team's record, scoring rate and at least one dated recent result, each with an official source. None names an individual player with a statistic, and METHODOLOGY.md previously claimed that they did; that sentence has been corrected rather than left standing. Player-level claims were omitted because no official player feed (NHL club stats, URC/LNR player statistics, EuroLeague/EHF scorer tables) was captured in this window, and asserting one without that capture would be unverified. Left open for a session that captures a player feed.", "source_name": "NHL Stats REST team summary (team-level input actually used)", "source_url": "https://api.nhle.com/stats/rest/en/team/summary"},
    {"id": "VF-25", "severity": "low", "category": "Corrected in this session", "sport": "Rugby Union (Pro D2)", "item": "Beziers form sentence said 'dropped four of their last five'; the LNR form string shows three defeats", "detail": "The LNR Pro D2 table records Beziers' last five results as V-D-V-D-D (wins over Nevers and Narbonne, defeats by Montauban, Valence Romans and Aurillac), i.e. two wins and three defeats. The narrative now reads 'have lost three of their last five matches'. The row's statistical facts (14th, 2W-0D-5L, 9 pts, 147 PF, 240 PA, -93) were already correct and are unchanged.", "source_name": "LNR Pro D2 official table", "source_url": "https://prod2.lnr.fr/classement"},
    {"id": "VF-26", "severity": "low", "category": "Corrected in this session", "sport": "Ice Hockey (NHL), Rugby Union (Pro D2, URC)", "item": "Three selections were HIGH on the picks page and MEDIUM in their own match row", "detail": "Minnesota Wild moneyline (70.82%), Stade Aurillacois 1X2 (70.53%) and Connacht Rugby 1X2 (70.25%) were written up as high-confidence band picks, but the row's pick badge used the 72% threshold alone and read medium. The published grading copy already states 'high >= 72%, or a band pick >= 70%'; the model now applies that second clause when grading a row's own pick, so the same selection can no longer carry two grades. High-confidence rows move from 15 to 18; probabilities and prices are unchanged and the NBA medium cap is untouched.", "source_name": "NHL Stats REST team summary (Minnesota row input)", "source_url": "https://api.nhle.com/stats/rest/en/team/summary"},
    {"id": "VF-27", "severity": "low", "category": "Corrected in this session", "sport": "Rugby Union (Top 14, Pro D2)", "item": "Four LNR kick-off times were wrong on the desk", "detail": "Re-read of the official LNR calendars on 2026-10-22 03:14-03:16Z (session 26963a2d): Toulouse v Perpignan (top14-11867) is Sat 24 Oct 16h35 CEST = 14:35 UTC (desk had 12:30) and Vannes v Clermont (top14-11862) is 14h30 CEST = 12:30 UTC (desk had 14:35) — the two were swapped; Provence v Béziers (prod2-12064) is Fri 23 Oct 21h00 = 19:00 UTC (desk 17:30) and Narbonne v Brive (prod2-12069) is 19h00 = 17:00 UTC (desk 17:30). All four corrected; the other 11 LNR kick-offs matched.", "source_name": "LNR Top 14 official calendar", "source_url": "https://top14.lnr.fr/calendrier-et-resultats"},
    {"id": "VF-28", "severity": "high", "category": "Corrected in this session", "sport": "Cricket", "item": "Both ICC rows carried wrong dates: NZ v IND was 22 Oct 07:00 UTC (not 23 Oct 06:15) and SA v AUS was already at Day 4 stumps", "detail": "Resolves VF-17. The BCCI official match page for NZL v IND 1st T20I states Thu 22 October 2026, 7:00 am UTC, Hagley Oval, Christchurch, and the ICC match strip read at 03:44Z listed match 271646 in the 22-Oct list at 03:00 US Eastern (= 07:00 UTC); the root layer's 22 Oct date was right and the desk's 23 Oct 06:15 was wrong — corrected. ICC match 269791 (South Africa v Australia, WTC) was shown live at Day 4 stumps (SA 425/9d; AUS 99 & 156/4 following on, trailing by 170) on the same strip, so it was never a 24-Oct fixture; the row is retired rather than relabelled. No price was ever attached to either row.", "source_name": "BCCI official match page (NZL v IND 1st T20I)", "source_url": "https://www.bcci.tv/matches/b8a52270-eedc-48ff-93f1-b925941e67b7/new-zealand-vs-india"},
    {"id": "VF-29", "severity": "medium", "category": "Corrected in this session", "sport": "Darts (PDC), Rugby Union (URC), Snooker (WST)", "item": "Desk start times for 16 darts, 14 URC and 8 snooker rows were US-Eastern renders, not official local or UTC times", "detail": "The page renderer used by every session displays JavaScript-localised times in US Eastern (verified against EuroLeague's 17:30 UTC tip-offs rendering as 13:30 and NHL start_utc fields). Darts: the official PDC schedule publishes only the session start (19:00 CEST = 17:00 UTC on 22 and 23 Oct) and the match order, so the 13:15/13:45/... per-match values were unofficial estimates; all 16 rows now show 17:00 UTC with the official order preserved. URC: the shared feed's '14:45 Local' values were ET renders of stats.unitedrugby.com; rows now show UTC (+4h, e.g. Connacht v Zebre 18:45 UTC). Snooker: 08:00/09:00/14:00/15:00 renders are 12:00/13:00/18:00/19:00 UTC. Fixture identities, venues and dates were unaffected.", "source_name": "PDC official order of play (European Championship schedule confirmed)", "source_url": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/"},
    {"id": "VF-30", "severity": "low", "category": "Secondary-source dependency", "sport": "Snooker (WST)", "item": "Wilson v Pang is now priced; the best-of-7 frame format comes from broadcaster pages, not wst.tv", "detail": "The full official 36-row WST ranking list (read 03:40Z) places Kyren Wilson 9th (£716,800) — he had been labelled 'prize value not captured' on the desk — so the Round 3 tie with Pang Junxu (29th, £272,750) is priced by the existing prize-money model. The WST pages read do not state the Round 3 frame format; BBC Sport and TNT Sports both state rounds one to three are best of seven, which the model assumes (target 4 frames). This is the only non-governing-body dependency in the row and is disclosed here. The other seven Round 3 ties involve a player outside the official top 36 and remain blank.", "source_name": "WST official world rankings (full list)", "source_url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false"},
    {"id": "VF-31", "severity": "low", "category": "Re-verified against official source", "sport": "Darts (PDC)", "item": "PDC Order of Merit re-read on 2026-10-22: 32/32 player values match; consent wall is not a block (resolves VF-21/VF-16 in part)", "detail": "pdc.tv pages place the CookieYes consent text in the first six content chunks and the real page from chunk 6 onward; reading chunks 6-8 of /rankings returned the full Order of Merit (1 Littler £3,113,500 ... 132) and all 32 desk values matched. The official 19-Oct schedule article was also read (chunk 6): the 16 first-round ties and their order match the desk, confirming fixture provenance from a PDC page rather than only OLBG.", "source_name": "PDC Official Rankings", "source_url": "https://www.pdc.tv/rankings"},
    {"id": "VF-32", "severity": "medium", "category": "Not verifiable this session", "sport": "Volleyball, Gaelic Football", "item": "PlusLiga and GAA club fixtures could not be checked against their official pages", "detail": "plusliga.pl (men's PlusLiga) redirected the renderer to tauronliga.pl (women's TAURON Liga) on 2026-10-22 03:44Z, so the three volleyball rows were not re-verified; gaa.ie's national fixtures page lists only the Shinty-Hurling International for 24-25 Oct, so the five county club championship rows could not be checked there. All eight rows remain unlined and carry their original capture; nothing was filled from secondary sources.", "source_name": "PlusLiga official site (redirected)", "source_url": "https://www.plusliga.pl/games.html"},
    {"id": "VF-33", "severity": "low", "category": "Resolved in this session", "sport": "Ice Hockey (NHL), Cross-sport", "item": "FLA/OTT/BUF/PHI inputs rolled forward; player-level facts now captured for write-ups (closes VF-19 and VF-24)", "detail": "Florida 1-5 Ottawa and Philadelphia 3-1 Buffalo went final on 21 Oct; the four clubs' rows now include those games (FLA 5-3-2, OTT 7-3-0, BUF 4-4-2, PHI 3-6-3) from the official Stats REST summary and score feed. The official api-web score feed's per-team leaders (goals, assists, goalie wins) and the standings endpoint's home/road/last-10 splits were captured for all 12 games, and the research write-ups on the predictions page now name players with official statistics (e.g. Kaprizov 11 G, Sorokin 5 W, Pastrnak 4 G 8 A).", "source_name": "NHL official score feed (team leaders)", "source_url": "https://api-web.nhle.com/v1/score/2026-10-22"},
    {"id": "VF-34", "severity": "medium", "category": "Verification coverage", "sport": "Cross-sport", "item": "Session arena/1352b77f-olbg2 line-by-line re-read, 2026-10-22 07:25–08:10 UTC: 11 source families, 0 published values corrected, coverage limit disclosed", "detail": "Every cited figure below was compared row by row against the official page named, at the fetch times logged in research/verification-1352b77f-olbg2.md: NHL api-web score feed 2026-10-22 (12/12 rows — game ids, matchups, venues, UTC starts, W-L-OTL records all matched); NBA official week schedule page (14/14 published rows matched; 60 new rows captured — VF-14) and NBA 2025-26 standings (30/30 club records and home/road splits matched the model priors exactly); MLB Stats API schedule (4 verified-desk + 7 forward-desk World Series rows matched, incl. G5–G7 if-necessary flags); PDC World Rankings (18/18 darts players matched on rank and prize money, ladder read through rank 76); WST Johnstone's Paint rankings (8/8 snooker rows matched — every named rank/prize pair correct and every 'outside top 36' player indeed absent from the official 36-row list); EHF CL standings + calendar (5/5 rows matched on group W-D-L, GF-GA and tip times); URC official table (16/16 club summaries matched) and Round 4 listing (fixture ids 292608–292610 confirmed); LNR Top 14 table (14/14 club summaries + all seven J7 fixture links matched); LNR Pro D2 table (16/16 club summaries + all eight J8 fixture links matched); FIA Formula 1 drivers' standings on formula1.com (Antonelli 340, Russell 238, Hamilton 229, Verstappen 221 matched). NOT re-read this session: EuroLeague/EuroCup game-centre rows (9 + 16), URC Round 5 fixtures (8), golf (2), Gaelic football (5), rugby league (3), cricket (1), volleyball (3) and the forward NHL slate for 26 Oct–2 Nov (58 rows) — those rows keep their capture-date provenance and per-row source links. GBGB retried twice (https://www.gbgb.org.uk/racecards/ returned the official 404 page at 08:05 UTC) — VF-22 remains open.", "source_name": "NBA official week schedule (re-read example)", "source_url": "https://www.nba.com/schedule?date=2026-10-24"},
    {"id": "VF-35", "severity": "low", "category": "Corrected in this session", "sport": "Cross-sport", "item": "Uniform odds-window high gate adopted (PR #54 substance): out-of-window chalk regraded medium; probabilities and prices unchanged", "detail": "PR #54 (session arena/1bb45081, claim stale since 2026-10-22 01:58Z) audited every high-confidence label and implemented a uniform rule: HIGH only when the model probability is >= 70% and the fair American price sits inside -250..+10000. The integration session adopted that rule onto the current tree instead of merging the stale branch (merging would have reverted sessions 50268b75, 26963a2d, 6a87eefa and this one). Effect on the published desks: 15 verified-desk row picks and 4 forward-slate row picks formerly labelled high at -256 to -5000 are now medium; the 3 in-window verified picks and the 30 written predictions (14 featured band picks + 16 research picks) are unchanged, and every pick labelled high now carries a written-prediction duty it can actually satisfy. Probabilities, fair prices and market lines were not altered.", "source_name": "PR #54 (odds-window audit record, preserved in-repo)", "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/research/odds-window-audit-1bb45081.md"},
    {"id": "VF-09", "severity": "low", "category": "Zero active markets", "sport": "Aussie Rules & eSports", "item": "0 live events on OLBG hubs on 2026-10-21", "detail": "Both hubs were fetched directly on 2026-10-21 and returned 'No tips found' (AFL off-season; between LoL Worlds knockout stages on OLBG). Dedicated sport pages confirm the empty check without inventing fixtures.", "source_name": "OLBG Aussie Rules Hub", "source_url": "https://www.olbg.com/betting-tips/Aussie_Rules/22"},
    {"id": "VF-10", "severity": "medium", "category": "OLBG platform irregularity", "sport": "Cross-sport", "item": "Viewer-timezone rendering, abbreviated names & cached global /betting-tips cards", "detail": "OLBG hub pages display kick-offs in US Eastern time on US runners (e.g. 12:45 vs 18:45 CEST for EHF Handball), abbreviate club names ('Eire Og Cor'), and cache stale soccer cards on the global /betting-tips landing page.", "source_name": "OLBG Global Tips Page", "source_url": "https://www.olbg.com/betting-tips"},
    {"id": "VF-11", "severity": "high", "category": "Source scope", "sport": "Darts, Tennis, Greyhounds, Golf, Gaelic Football, Rugby League, Volleyball, Motor Racing, Snooker, EuroCup, NBA", "item": "63 rows cite a competition or rankings page, not the individual fixture", "detail": "The official URL on these rows is an official governing-body or league page, but it does not itself identify the fixture. Examples: all 18 darts rows cite pdc.tv/rankings; all 15 tennis rows cite the ATP/WTA rankings or tournament overview; all 6 greyhound rows cite the GBGB results index; the 4 EuroCup rows cite the EuroCup standings. The fixture ID, date and opponent on those rows rest on the OLBG listing captured on 2026-10-21. They are published with the source scope disclosed as 'competition', not 'fixture'. [Update 2026-10-22, session 50268b75: the desk was re-captured the same day — tennis and greyhound rows were retired as completed, EuroCup rows retired, and every originated fixture now carries a fixture-level official URL; darts ties still cite the official rankings ladder, which is also their model input.]", "source_name": "PDC Rankings (example)", "source_url": "https://www.pdc.tv/rankings"},
    {"id": "VF-12", "severity": "medium", "category": "Price band", "sport": "Cross-sport", "item": "20 pre-existing high-confidence picks are all shorter than -250; 13 band picks priced 1.40-1.42 were added", "detail": "The brief asks for high-confidence picks between -250 (decimal 1.40) and +10000 (decimal 101.00). A selection with a 70%+ model probability cannot be priced above 1.43, so only a 70.0-71.4% window satisfies both rules. All 20 original high-confidence selections carry fair odds of 1.02-1.39 and therefore fall outside the requested band; they remain published and labelled 'outside band'. Thirteen handicap/total selections at 1.40-1.42, each with a written prediction and official facts, were originated to meet the band. [Update 2026-10-22, session 50268b75: superseded — the written predictions were re-cut around the band itself, so all 14 current write-ups are in-band selections; short-priced moneyline favourites keep their HIGH grade on sport pages without a write-up.]", "source_name": "Methodology (this repository)", "source_url": "https://www.olbg.com/betting-tips"},
    {"id": "VF-13", "severity": "medium", "category": "Snapshot freshness", "sport": "Cross-sport", "item": "59 of 155 rows are dated 2026-10-21 and had already started or finished at the 2026-10-22 01:30Z snapshot", "detail": "This is a dated capture, not a live feed. Rows dated before 2026-10-22 are labelled 'past' on every table; 36 rows are dated 2026-10-22 and 60 are dated later. No result has been back-filled and no past row is presented as an upcoming tip. [Resolved 2026-10-22, session 50268b75: all 21-Oct rows were retired in the same-day re-capture; an automated test now asserts no row predates the capture date.]", "source_name": "NHL schedule feed (capture reference)", "source_url": "https://api-web.nhle.com/v1/schedule/2026-10-21"},
    {"id": "VF-14", "severity": "low", "category": "Resolved in this session", "sport": "Basketball (NBA)", "item": "[Resolved 2026-10-22, session arena/1352b77f-olbg2] NBA 22–31 Oct slate captured at matchup level", "detail": "nba.com's games calendar rendered per-day counts but the /games fixture list returned 'Sorry, something went wrong', the static scoreboard endpoint returned HTTP 500, and stats.nba.com did not respond — so VF-14 opened with no matchup data. Sessions 50268b75 (22–23 Oct) and arena/1352b77f-olbg2 (24–31 Oct) then read the official server-rendered week page https://www.nba.com/schedule?date=2026-10-24 line by line and captured all 74 games of 22–31 Oct (game id, tip-off ET, venue, home/away), including the 10 Emirates NBA Cup group games of 30 Oct. Games of 1–2 Nov 2026 were not part of that page's server render and are not invented; the flag stays open only for those two dates.", "source_name": "NBA Official Schedule (week page, server-rendered)", "source_url": "https://www.nba.com/schedule?date=2026-10-24"},
    {"id": "VF-15", "severity": "low", "category": "Missing fixture", "sport": "Baseball", "item": "World Series Game 4 (gamePk 849803) confirmed but not originated", "detail": "The MLB Stats API confirms four scheduled games: Game 1 on 23 Oct (849805), Game 2 on 24 Oct (849802), Game 3 on 26 Oct (849804) and Game 4 on 27 Oct (849803) at Tropicana Field. The verified desk prices the first three only; Game 4 and the conditional Games 5-7 are left out rather than priced from an incomplete series state. [Resolved 2026-10-22, session 50268b75: Game 4 (849803) is now originated alongside Games 1–3; conditional Games 5–7 remain unpublished.]", "source_name": "MLB Stats API schedule", "source_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-10-27"},
    {"id": "VF-16", "severity": "high", "category": "Unverified fixture provenance", "sport": "Darts", "item": "PDC event page returned only a cookie-consent wall on 2026-10-22", "detail": "A re-fetch of https://www.pdc.tv/tournament/2026-european-championship on 2026-10-22 returned CookieYes consent text and no match data. The 16 first-round ties and 2 outrights are therefore listed from OLBG and priced only from the official PDC ranking ladder, not from a PDC fixture page.", "source_name": "PDC European Championship (re-fetch)", "source_url": "https://www.pdc.tv/tournament/2026-european-championship"},
    {"id": "VF-17", "severity": "high", "category": "Date disagreement", "sport": "Cricket", "item": "[Resolved by VF-28] New Zealand v India is dated 2026-10-23 06:15 UTC in the verified desk and 2026-10-22 in the root layer", "detail": "ICC match 271646 is cited by both layers, but the root dashboard stores 2026-10-22 03:00 while the verified desk stores 2026-10-23 06:15 UTC. The ICC page did not render a date on re-fetch on 2026-10-22, so the disagreement cannot be resolved from the official source and both values are left as captured. The verified desk value is the one used in its table.", "source_name": "ICC match 271646", "source_url": "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india"},
    {"id": "VF-18", "severity": "low", "category": "Blank unconfirmed market", "sport": "Basketball (BKT EuroCup), Volleyball, Cricket, Golf, Rugby League, Gaelic Football, Greyhounds", "item": "43 rows remain unlined and no price was invented", "detail": "Unlined rows keep winner, handicap, total and pick fields null. Reasons are recorded per row: one-match volleyball samples, non-rendered cricket ratings, strokeplay fields without a verified field rating, 2027 futures without rosters, county GAA tables behind client rendering, and licensed GBGB sectional data. The site shows an em dash and the reason for every one. [Update 2026-10-22, session 50268b75: 26 rows remain unlined on the refreshed desk, each with its reason recorded.]", "source_name": "PlusLiga official games (example)", "source_url": "https://www.plusliga.pl/games.html"},
]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_shared(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _et_to_utc_label(date_local: str, time_et: str) -> str:
    from datetime import datetime, timedelta

    dt = datetime.strptime(f"{date_local} {time_et}", "%Y-%m-%d %H:%M") + timedelta(hours=4)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def shared_urc() -> tuple[dict, list[dict], list[dict]]:
    """Copy the verified 2026-10-21 URC capture into this desk's inputs.

    URC Rounds 4 (23-24 Oct) and 5 (30-31 Oct) have no intervening matches
    since capture, so the table and fixtures are current. The copies are
    written into inputs.json so the model reads one self-contained file; CI's
    diff gate makes any upstream drift visible.
    """
    raw = load_shared("data/inputs/urc.json")
    r5_raw = load_shared("data/live/urc.json")
    teams = {
        k: {"name": v["name"], "gp": v["pl"], "w": v["w"], "d": v["d"], "l": v["l"], "pf": v["pf"], "pa": v["pa"]}
        for k, v in raw["table"].items()
    }

    def conv(fixtures: list[dict]) -> list[dict]:
        return [
            {
                "id": f["id"],
                "date": f["date_local"],
                # The shared feed's "time_local" is the fetcher's US-Eastern
                # render of stats.unitedrugby.com (session 26963a2d, 03:21Z:
                # 14:45 ET = 18:45 UTC = 19:45 BST for Cardiff Arms Park on a
                # Friday). US Eastern is UTC-4 through 1 Nov 2026, so +4h.
                "time": _et_to_utc_label(f["date_local"], f["time_local"]),
                "home": f["home"],
                "away": f["away"],
                "venue": f["venue"],
                "url": f["url"],
                "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9",
            }
            for f in fixtures
        ]

    return teams, conv(raw["fixtures"]), conv(r5_raw["fixtures"])


def main() -> None:
    urc_teams, urc_r4_fixtures, urc_r5_fixtures = shared_urc()
    # 2025-26 completed-season records used as the NBA strength prior (VF-01/02).
    nba_teams = load_shared("data/inputs/nba_teams.json")["teams"]
    write_json(
        OUT / "sports.json",
        {
            "captured_at": CAPTURE_DATE,
            "excluded_keywords": [
                "soccer",
                "boxing",
                "ufc",
                "mma",
                "football",
                "american football",
                "hurling",
                "horse racing",
                "cycling",
                "specials",
            ],
            "excluded_sports": EXCLUDED_SPORTS,
            "eligible_sports": ELIGIBLE_SPORTS,
        },
    )
    write_json(
        OUT / "inputs.json",
        {
            "captured_at": CAPTURE_DATE,
            "nhl_teams": NHL_TEAMS,
            "nhl_fixtures": NHL_FIXTURES,
            "nba_teams": nba_teams,
            "nba_fixtures": NBA_FIXTURES,
            "euroleague_teams": EUROLEAGUE_TEAMS,
            "euroleague_fixtures": EUROLEAGUE_FIXTURES,
            "eurocup_teams": EUROCUP_TEAMS,
            "eurocup_fixtures": EUROCUP_FIXTURES,
            "top14_teams": TOP14_TEAMS,
            "top14_fixtures": TOP14_FIXTURES,
            "prod2_teams": PROD2_TEAMS,
            "prod2_fixtures": PROD2_FIXTURES,
            "urc_teams": urc_teams,
            "urc_r4_fixtures": urc_r4_fixtures,
            "urc_r5_fixtures": urc_r5_fixtures,
            "ehf_teams": EHF_TEAMS,
            "ehf_fixtures": EHF_FIXTURES,
            "ehf_olbg_map": EHF_OLBG_MAP,
            "pdc_players": PDC_PLAYERS,
            "darts_fixtures": DARTS_FIXTURES,
            "atp_players": ATP_PLAYERS,
            "tennis_originated": TENNIS_ORIGINATED,
            "wst_top36": WST_TOP36,
            "snooker_originated": SNOOKER_ORIGINATED,
            "mlb_teams": MLB_TEAMS,
            # Cross-layer compatibility view: scripts/survey_lines.py prices
            # its World Series Game 1 row from this key. Derived from the
            # same verified MLB_TEAMS / MLB_FIXTURES literals so it cannot
            # drift from this desk's own numbers.
            "mlb_world_series": {
                "id": MLB_FIXTURES[0]["id"],
                "competition": "2026 MLB World Series — Game 1",
                "date": MLB_FIXTURES[0]["official_date"],
                "venue": MLB_FIXTURES[0]["venue"],
                "away": {"code": "TB", "name": MLB_TEAMS["TB"]["name"], "gp": MLB_TEAMS["TB"]["wins"] + MLB_TEAMS["TB"]["losses"], "w": MLB_TEAMS["TB"]["wins"], "l": MLB_TEAMS["TB"]["losses"], "rs": MLB_TEAMS["TB"]["runs_scored"], "ra": MLB_TEAMS["TB"]["runs_allowed"]},
                "home": {"code": "MIL", "name": MLB_TEAMS["MIL"]["name"], "gp": MLB_TEAMS["MIL"]["wins"] + MLB_TEAMS["MIL"]["losses"], "w": MLB_TEAMS["MIL"]["wins"], "l": MLB_TEAMS["MIL"]["losses"], "rs": MLB_TEAMS["MIL"]["runs_scored"], "ra": MLB_TEAMS["MIL"]["runs_allowed"]},
                "url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-10-31",
                "olbg_url": "https://www.olbg.com/betting-tips/Baseball/12",
            },
            "mlb_fixtures": MLB_FIXTURES,
            "f1_drivers": F1_DRIVERS,
            "unlined_rows": UNLINED_ROWS,
        },
    )
    # The repo audit is the 2026-10-21 session's findings; keep its own date.
    write_json(OUT / "repo_audit.json", {"captured_at": "2026-10-21", "findings": REPO_AUDIT})
    write_json(OUT / "flagged.json", {"captured_at": CAPTURE_DATE, "items": FLAGGED_ITEMS})
    print(f"verified_seed: wrote sports ({len(ELIGIBLE_SPORTS)} eligible / {len(EXCLUDED_SPORTS)} excluded), inputs, {len(REPO_AUDIT)} audit rows, {len(FLAGGED_ITEMS)} flags")


if __name__ == "__main__":
    main()
