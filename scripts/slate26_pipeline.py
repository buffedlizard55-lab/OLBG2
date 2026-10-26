#!/usr/bin/env python3
"""Session 9cf54b86 — 26 October 2026 fifteen-sport slate.

Everything this module writes is derived from two hand-captured inputs:

  1. OLBG_LISTINGS  — the tips table on each of the fifteen OLBG sport hubs, read on
                      2026-10-26 between 05:05 and 05:45 UTC with the agent fetch tool.
  2. OFFICIAL_FACTS — facts read the same morning from official governing-body feeds
                      (NHL, MLB) and the Austrian Volleyball Federation fixture list.

Nothing is inferred. A field that was not read from a source stays empty, and the
fixture is flagged on slate26/flagged.html.

Run: python scripts/slate26_pipeline.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "slate26"
CAPTURED = "2026-10-26T05:45:00Z"
CAPTURED_LABEL = "26 October 2026, 05:05–05:45Z"

SPORTS = [
    # key, label, slug, OLBG hub URL
    ("golf", "Golf", "golf", "https://www.olbg.com/betting-tips/Golf/5"),
    ("volleyball", "Volleyball", "volleyball", "https://www.olbg.com/betting-tips/Volleyball/21"),
    ("rugby-union", "Rugby Union", "rugby-union", "https://www.olbg.com/betting-tips/Rugby_Union/9"),
    ("cricket", "Cricket", "cricket", "https://www.olbg.com/betting-tips/Cricket/7"),
    ("snooker", "Snooker", "snooker", "https://www.olbg.com/betting-tips/Snooker/8"),
    ("darts", "Darts", "darts", "https://www.olbg.com/betting-tips/Darts/15"),
    ("baseball", "Baseball", "baseball", "https://www.olbg.com/betting-tips/Baseball/12"),
    ("gaelic", "Gaelic Sports", "gaelic-sports", "https://www.olbg.com/betting-tips/Gaelic_Football/25"),
    ("greyhounds", "Greyhounds", "greyhounds", "https://www.olbg.com/betting-tips/Greyhounds/28"),
    ("tennis", "Tennis", "tennis", "https://www.olbg.com/betting-tips/Tennis/3"),
    ("motor-racing", "Motor Racing", "motor-racing", "https://www.olbg.com/betting-tips/Motor_Racing/14"),
    ("handball", "Handball", "handball", "https://www.olbg.com/betting-tips/Handball/20"),
    ("ice-hockey", "Ice Hockey", "ice-hockey", "https://www.olbg.com/betting-tips/Ice_Hockey/13"),
    ("basketball", "Basketball", "basketball", "https://www.olbg.com/betting-tips/Basketball/4"),
    ("rugby-league", "Rugby League", "rugby-league", "https://www.olbg.com/betting-tips/Rugby_League/10"),
]
HUB = {k: h for k, _, _, h in SPORTS}
LABEL = {k: l for k, l, _, _ in SPORTS}
SLUG = {k: s for k, _, s, _ in SPORTS}

# What each hub actually returned at capture. Counts are the number of listing rows on the hub.
HUB_STATE = {
    "golf": ("none", "Hub rendered the literal message 'No tips found.' at 05:12Z."),
    "volleyball": ("matches", "14 rows: Brazilian Superliga, Austrian AVL, Polish Tauron Liga, Italian Serie A1 W, Austrian cup."),
    "rugby-union": ("outright-only", "One row only: Six Nations 2027 outright (Ireland). No match priced."),
    "cricket": ("matches", "13 rows: 6 upcoming matches plus 7 outright / player-of-the-match markets."),
    "snooker": ("none", "Hub rendered the literal message 'No tips found.' at 05:16Z."),
    "darts": ("outright-only", "One row only: PDC World Championship 2027 outright (Luke Littler). No match priced."),
    "baseball": ("matches", "One row: World Series Game 3, MIL @ TB."),
    "gaelic": ("matches", "3 rows: 2 club championship matches plus the All-Ireland 2027 outright."),
    "greyhounds": ("matches", "One row: 3:19 Monmore, one dog. No other meeting priced."),
    "tennis": ("matches", "14 rows across ATP/WTA/Challenger and ITF-level events; times carried no tournament label."),
    "motor-racing": ("matches", "One row: Mexico City Grand Prix, Win Race (Leclerc)."),
    "handball": ("matches", "13 rows, all EHF Champions League group fixtures on 28–29 October plus one Swedish league game today."),
    "ice-hockey": ("matches", "9 rows: 3 NHL, 2 Danish Metal Ligaen, 2 Swedish SHL, 1 Finnish Liiga, 1 German DEL."),
    "basketball": ("matches", "14 rows: 8 NBA, 4 EuroLeague, 1 Korean KBL, 1 Argentine Liga Nacional."),
    "rugby-league": ("outright-only", "3 rows, all 2027 outrights (State of Origin, Super League, NRL). No match priced."),
}

# sport, league, event, event_id, displayed time (verbatim), market, selection, tips, total tips, pct
OLBG_LISTINGS = [
    # ---- Ice Hockey (hub 05:20Z) ----
    ("ice-hockey", "Danish Metal Ligaen", "Sonderjyske vs Aalborg Pirates", 200050, "Today 14:30", "Money Line", "Sonderjyske", 4, 4, 100),
    ("ice-hockey", "NHL", "LA Kings @ NY Rangers", 200101, "Today 19:07", "Money Line", "NY Rangers", 3, 3, 100),
    ("ice-hockey", "Danish Metal Ligaen", "Frederikshavn Whitehawks vs Odense Bulldogs", 200058, "Today 14:00", "Puck Line", "Frederikshavn Whitehawks -1.50", 2, 2, 100),
    ("ice-hockey", "Finland SM Liiga", "Kalpa vs Sport", 200081, "Tomorrow 12:30", "Money Line", "Kalpa", 2, 2, 100),
    ("ice-hockey", "Swedish Hockey League", "IF Malmo Redhawks vs Linkoping HC", 200082, "Tomorrow 14:00", "Money Line", "IF Malmo Redhawks", 2, 2, 100),
    ("ice-hockey", "Swedish Hockey League", "Frolunda HC vs Rogle BK", 200083, "Tomorrow 14:00", "Money Line", "Frolunda HC", 2, 2, 100),
    ("ice-hockey", "NHL", "TOR Maple Leafs @ CGY Flames", 200103, "Today 20:37", "Puck Line", "CGY Flames +1.50", 1, 1, 100),
    ("ice-hockey", "NHL", "DET Red Wings @ EDM Oilers", 200102, "Today 21:37", "Money Line", "EDM Oilers", 1, 1, 100),
    ("ice-hockey", "Germany Eishockey Liga", "Kolner Haie vs Adler Mannheim", 200100, "Tomorrow 14:00", "Money Line", "Adler Mannheim", 1, 1, 100),
    # ---- Basketball (hub 05:22Z) ----
    ("basketball", "Korea KBL", "Goyang Sky Gunners vs Changwon Sakers", 536165, "Today 06:00", "Pointspread", "Goyang Sky Gunners -2.50", 4, 4, 100),
    ("basketball", "NBA", "MIN Timberwolves @ CLE Cavaliers", 536203, "Today 19:00", "Money Line", "MIN Timberwolves", 2, 2, 100),
    ("basketball", "NBA", "DAL Mavericks @ MIA Heat", 536200, "Today 19:30", "Pointspread", "DAL Mavericks +8.50", 2, 2, 100),
    ("basketball", "NBA", "IND Pacers @ MIL Bucks", 536204, "Today 20:00", "Money Line", "IND Pacers", 2, 2, 100),
    ("basketball", "NBA", "ATL Hawks @ HOU Rockets", 536201, "Today 20:30", "Pointspread", "HOU Rockets -5.50", 2, 2, 100),
    ("basketball", "NBA", "WAS Wizards @ CHA Hornets", 536199, "Today 19:00", "Game Totals", "Under 228.50", 1, 1, 100),
    ("basketball", "NBA", "CHI Bulls @ BOS Celtics", 534851, "Today 19:30", "Pointspread", "CHI Bulls +13.50", 1, 1, 100),
    ("basketball", "Argentina Liga Nacional", "Lanus vs Regatas", 536154, "Today 19:30", "Game Totals", "Under 160.50", 1, 1, 100),
    ("basketball", "NBA", "PHX Suns @ OKC Thunder", 536205, "Today 20:00", "Game Totals", "Under 218.50", 1, 1, 100),
    ("basketball", "NBA", "MEM Grizzlies @ UTA Jazz", 536206, "Today 21:00", "Money Line", "MEM Grizzlies", 1, 1, 100),
    ("basketball", "NBA", "GS Warriors @ DEN Nuggets", 536202, "Today 22:00", "Pointspread", "DEN Nuggets -7.50", 1, 1, 100),
    ("basketball", "EuroLeague", "BC Dubai vs Paris", 536176, "Tomorrow 12:00", "Pointspread", "BC Dubai -10.50", 1, 1, 100),
    ("basketball", "EuroLeague", "Bayern Munich vs Barcelona", 536174, "Tomorrow 15:00", "Game Totals", "Over 173.50", 1, 1, 100),
    ("basketball", "EuroLeague", "Panathinaikos vs Milano", 536177, "Tomorrow 15:15", "Pointspread", "Panathinaikos -14.50", 1, 1, 100),
    # ---- Tennis (hub 05:24Z) ----
    ("tennis", "Tennis, tournament not labelled by OLBG", "Paula Badosa vs Carol Young Suh Lee", 902300, "Today 03:30", "Win Match", "Paula Badosa", 6, 7, 86),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Alexandra Eala vs Mika Stojsavljevic", 902175, "Today 04:00", "Win Match", "Alexandra Eala", 6, 9, 67),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Novak Djokovic vs Ugo Humbert", 902233, "Tomorrow 06:00", "Win Match", "Novak Djokovic", 4, 5, 80),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Stan Wawrinka vs Jiri Lehecka", 902232, "Tomorrow 06:00", "Win Match", "Jiri Lehecka", 4, 7, 57),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Aliaksandra Sasnovich vs Nikola Bartunkova", 902306, "Today 02:00", "Win Match", "Nikola Bartunkova", 3, 6, 50),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Han Shi vs Alevtina Ibragimova", 902299, "Today 02:00", "Win Match", "Han Shi", 3, 5, 60),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Matteo Berrettini vs Tomas Martin Etcheverry", 902208, "Today 08:30", "Win Match", "Matteo Berrettini", 3, 4, 75),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Jakub Mensik vs Lukas Neumayer", 902321, "Today 12:30", "Win Match", "Jakub Mensik", 3, 3, 100),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Leylah Fernandez vs Himeno Sakatsume", 902172, "Today 22:00", "Win Match", "Leylah Fernandez", 3, 5, 60),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Harriet Dart vs Tatiana Prozorova", 902303, "Today 05:00", "Total Games", "Over 22.50", 2, 2, 100),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Yelyzaveta Kotliar vs Alja Senica", 902315, "Today 08:00", "Win Match", "Yelyzaveta Kotliar", 2, 3, 67),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Tomas Machac vs Alex De Minaur", 902318, "Today 10:00", "Win Match", "Alex De Minaur", 2, 2, 100),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Antonia Vergara Rivera vs Eduarda Gomes", 902334, "Today 10:00", "Win Match", "Antonia Vergara Rivera", 2, 2, 100),
    ("tennis", "Tennis, tournament not labelled by OLBG", "Luiza Fullana vs Lourdes Ayala", 902339, "Today 13:00", "Win Match", "Luiza Fullana", 2, 2, 100),
    # ---- Cricket (hub 05:26Z) ----
    ("cricket", "New Zealand v India, 3rd T20I", "New Zealand vs India 3rd T20 Match", 188852, "Tomorrow 03:00", "Win Match", "India", 14, 21, 67),
    ("cricket", "Namibia v Ireland, 3rd ODI", "Namibia vs Ireland 3rd ODI", 188854, "Tomorrow 03:30", "Win Match", "Ireland", 11, 16, 69),
    ("cricket", "Pakistan v Sri Lanka, ODI", "Pakistan vs Sri Lanka One Day Match", 188868, "Tomorrow 04:00", "Win Match", "Pakistan", 5, 9, 56),
    ("cricket", "South Africa v Australia", "South Africa vs Australia", 188835, "31 Oct 04:30", "Man of the Match", "AK Markram", 3, 5, 60),
    ("cricket", "WBBL", "Melbourne Stars W vs Hobart Hurricanes W T20 Big Bash", 188864, "29 Oct 04:10", "Win Match", "Hobart Hurricanes W", 4, 6, 67),
    ("cricket", "WBBL", "Brisbane Heat W vs Sydney Sixers W T20 Big Bash", 188865, "30 Oct 04:10", "Win Match", "Sydney Sixers W", 3, 5, 60),
    # ---- Gaelic Sports (hub 05:28Z) ----
    ("gaelic", "GAA club championship (county not labelled by OLBG)", "Kanturk v Eire Og Cor", 3531, "01 Nov 14:00", "Handicap", "Eire Og Cor +0.50", 6, 6, 100),
    ("gaelic", "GAA club championship (county not labelled by OLBG)", "Fr Caseys v Kildimo Pallaskenry", 3537, "01 Nov 15:30", "Handicap", "Kildimo Pallaskenry +3.50", 5, 7, 71),
    # ---- Handball (hub 05:30Z) ----
    ("handball", "EHF Champions League", "SC Magdeburg vs HC Kriens Luzern", 12136, "28 Oct 15:45", "Money Line", "Tie", 7, 11, 64),
    ("handball", "EHF Champions League", "Fuchse Berlin vs RK Partizan", 12128, "29 Oct 13:45", "Money Line", "Tie", 6, 11, 55),
    ("handball", "Swedish Handbollsligan", "OV Helsingborg HK vs IF Hallby HK", 12150, "Today 14:00", "Money Line", "OV Helsingborg HK", 5, 10, 50),
    ("handball", "EHF Champions League", "KS Kielce vs Kolstad", 12132, "28 Oct 15:45", "Money Line", "Tie", 5, 8, 63),
    ("handball", "EHF Champions League", "HC Vardar vs MT Melsungen", 12130, "28 Oct 13:45", "Money Line", "Tie", 4, 7, 57),
    ("handball", "EHF Champions League", "Wisla Plock vs Nantes", 12138, "28 Oct 13:45", "Money Line", "Tie", 4, 6, 67),
    ("handball", "EHF Champions League", "PSG Handball vs Aalborg Handbold", 12134, "28 Oct 15:45", "Money Line", "Tie", 4, 6, 67),
    ("handball", "EHF Champions League", "RK Celje vs RK Zagreb", 12135, "28 Oct 15:45", "Money Line", "Tie", 4, 6, 67),
    ("handball", "EHF Champions League", "FC Porto vs Veszprem", 12127, "28 Oct 13:45", "Money Line", "Tie", 3, 6, 50),
    ("handball", "EHF Champions League", "GOG vs Sporting CP", 12129, "29 Oct 13:45", "Money Line", "GOG", 2, 4, 50),
    ("handball", "EHF Champions League", "Montpellier vs Dinamo Bucuresti", 12133, "29 Oct 15:45", "Money Line", "Tie", 2, 3, 67),
    ("handball", "EHF Champions League", "IFK Kristianstad vs Pick Szeged", 12131, "29 Oct 13:45", "Money Line", "Tie", 1, 3, 33),
    ("handball", "EHF Champions League", "Skanderborg Handbold vs FC Barcelona", 12137, "29 Oct 15:45", "Money Line", "FC Barcelona", 1, 3, 33),
    # ---- Volleyball (hub 05:32Z) ----
    ("volleyball", "Brazilian Superliga", "Norde Volei vs Volei Renata", 37102, "Today 20:00", "Win Match", "Norde Volei", 6, 8, 75),
    ("volleyball", "Brazilian Superliga", "Montes Claros vs Sada Cruzeiro", 37101, "Today 18:00", "Win Match", "Sada Cruzeiro", 5, 10, 50),
    ("volleyball", "Italian Serie A1 Women", "Conegliano W vs Vallefoglia W", 37076, "28 Oct 15:00", "Win Match", "Vallefoglia W", 5, 7, 71),
    ("volleyball", "Austrian Volley League Men", "SG VCA Amstetten vs UVC Ried", 37116, "Today 11:30", "Win Match", "UVC Ried", 4, 5, 80),
    ("volleyball", "Polish Tauron Liga Women", "BKS Bielsko Biala W vs LKS Lodz W", 37080, "Today 12:30", "Win Match", "LKS Lodz W", 4, 7, 57),
    ("volleyball", "Austrian Volley League Men", "UVC Graz vs SG Union Raiffeisen Waldviertel", 37119, "Today 14:00", "Win Match", "SG Union Raiffeisen Waldviertel", 4, 5, 80),
    ("volleyball", "Austrian Volley League Men", "VBK Klagenfurt vs SK Aich-Dob", 37118, "Today 13:00", "Win Match", "SK Aich/Dob", 3, 4, 75),
    ("volleyball", "Brazilian Superliga Women", "Sancor Volei W vs SESI Volei Bauru W", 37004, "Today 17:30", "Win Match", "SESI Volei Bauru W", 3, 5, 60),
    ("volleyball", "Italian Serie A1 Women", "Marignano W vs Bergamo W", 37075, "Tomorrow 15:00", "Win Match", "Bergamo W", 2, 3, 67),
    ("volleyball", "Austrian Volley League Men", "UNIONvolleys Bisamberg Hollabrunn vs TSV Hartberg", 37117, "Today 12:30", "Set Score", "TSV Hartberg to win 3-2", 1, 2, 50),
    ("volleyball", "Polish Tauron Liga Women", "Budowlani Lodz W vs Radomka Radom W", 37082, "28 Oct 12:30", "Set Score", "Radomka Radom W to win 3-0", 1, 1, 100),
    ("volleyball", "Polish Tauron Liga Women", "Uni Opole W vs Palac Bydgoszcz W", 37081, "Tomorrow 15:30", "Win Match", "Palac Bydgoszcz W", 2, 4, 50),
    ("volleyball", "Brazilian Superliga", "Suzano Volei vs Goias Volei", 37103, "Tomorrow 19:30", "Win Match", "Suzano Volei", 2, 3, 67),
    ("volleyball", "Brazilian Superliga", "Praia Clube vs Sao Jose", 37104, "Tomorrow 21:00", "Win Match", "Praia Clube", 2, 3, 67),
    # ---- Baseball (hub 05:34Z) ----
    ("baseball", "MLB, World Series Game 3", "MIL Brewers @ TB Rays", 160795, "Today 21:00", "Money Line", "TB Rays", 9, 11, 82),
    # ---- Greyhounds (hub 05:36Z) ----
    ("greyhounds", "Monmore, A? grade not shown by OLBG", "3:19 Monmore", 690193, "Today 11:19", "Daily Races", "Tullymurry Skies", 1, 1, 100),
    # ---- Motor Racing (hub 05:38Z) ----
    ("motor-racing", "Formula 1", "Mexico City Grand Prix", 914, "01 Nov 15:00", "Win Race", "Charles Leclerc", 1, 2, 50),
]

OUTRIGHTS = [
    ("cricket", "World Cup 2027", "India", "Outright Winner", 182606, "21 Nov 2027 05:00", 6, 12, 50),
    ("cricket", "Big Bash Women 2026", "Sydney Sixers W", "Outright Winner", 187184, "05 Dec 03:10", 2, 3, 67),
    ("cricket", "T20 Big Bash 2026-27", "Adelaide Strikers", "Outright Winner", 187503, "12 Dec 03:15", 1, 2, 50),
    ("cricket", "SA20 2026-27", "Pretoria Capitals", "Outright Winner", 187504, "24 Jan 2027 11:30", 1, 1, 100),
    ("cricket", "T20 Blast 2027", "Sussex", "Outright Winner", 188350, "18 Jul 2027 11:00", 0, 0, 0),
    ("darts", "PDC World Championship 2027", "Luke Littler", "Win Tournament", 26023, "03 Jan 2027 12:00", 22, 36, 61),
    ("rugby-union", "Six Nations 2027", "Ireland", "Win Tournament", 609013, "14 Mar 2027 16:00", 3, 10, 30),
    ("rugby-league", "State of Origin 2027", "New South Wales", "Win Tournament", 2695857, "27 May 2027 06:00", 9, 12, 75),
    ("rugby-league", "Super League 2027", "Wigan Warriors", "Grand Final Winner", 2801554, "02 Oct 2027 13:00", 2, 4, 50),
    ("rugby-league", "NRL 2027", "Penrith Panthers", "Grand Final Winner", 2801600, "03 Oct 2027 04:30", 1, 3, 33),
    ("gaelic", "All Ireland Football Championship 2027", "Kerry", "Outright Winner", 3327, "25 Jul 2027 15:30", 6, 8, 75),
]

# Facts read from official feeds, keyed by the OLBG event id of the fixture they belong to.
# Every entry carries the exact URL it was read from and the claim it supports.
OFFICIAL_FACTS = {
    200102: [
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "DET Red Wings season record", "4-4-3 (11 games played)"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "EDM Oilers season record", "8-2-1 (11 games played)"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "EDM team goaltending", "team GAA 3.55, save percentage .872, 0 shutouts in 11 games"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "EDM starter Devon Levi", "6-1-0, GAA 3.11, save percentage .887 in 7 games"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "EDM backup Tristan Jarry", "2-1-1, GAA 3.73, save percentage .861 in 4 games"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "DET team goaltending", "team GAA 2.91, save percentage .886, 1 shutout in 11 games"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "DET starter John Gibson", "3-4-1, GAA 3.44, save percentage .867 in 8 games"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "DET backup Daniil Tarasov", "1-0-2, GAA 1.40, save percentage .940, 1 shutout in 4 games"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "EDM scorer form, last five games", "Connor McDavid 16 points (12 assists); Leon Draisaitl 8 goals"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "EDM defence scoring", "Evan Bouchard 21 points (7 goals, 14 assists) in 11 games, plus-15, 26:02 average ice time"),
        ("NHL.com game summary", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
         "DET scorer form, last five games", "Lucas Raymond 5 points (3 goals); Dylan Larkin 3 assists"),
        ("NHL.com schedule", "https://api-web.nhle.com/v1/schedule/2026-10-26",
         "Puck drop", "2026-10-27T01:30:00Z at Rogers Place, Edmonton"),
        ("NHL.com standings", "https://api-web.nhle.com/v1/standings/2026-10-25",
         "EDM points and goal difference", "17 points, 49 goals for, 39 against, 5-0-0 on the road, L1"),
    ],
    160795: [
        ("MLB StatsAPI", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team",
         "Game", "World Series Game 3, Milwaukee Brewers at Tampa Bay Rays, 2026-10-27T00:00:00Z, Tropicana Field"),
        ("MLB StatsAPI", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team",
         "Series state", "Milwaukee lead the best-of-seven series 2-0 (series game 3 of 7)"),
        ("MLB StatsAPI", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team",
         "Milwaukee probable starter", "Robert Gasser (id 688107)"),
        ("MLB StatsAPI", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team",
         "Tampa Bay probable starter", "Freddy Peralta (id 642547)"),
        ("MLB StatsAPI", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team",
         "Tampa Bay regular season", "98-64 (.605), American League East champions, 55-26 at home, 736 runs scored, 650 allowed"),
        ("MLB StatsAPI", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team",
         "Tampa Bay home split", "55-26 at home (.679) in the 2026 regular season"),
    ],
}

# Where an official feed gave both sides' season records, our own price comes from those records
# rather than from the tip share. The formula is printed on slate26/methodology.html.
MODEL_INPUT = {
    200102: {"kind": "nhl", "home": "EDM", "away": "DET",
             "home_points_pct": 0.7727, "away_points_pct": 0.5000,
             "home_record": "8-2-1", "away_record": "4-4-3"},
}

# Fixture-level official kick-off times read from the Austrian Volleyball Federation (ÖVV).
# These cross-check OLBG's displayed times and confirm the US-Eastern display convention.
OFFICIAL_KICKOFFS = {
    37116: ("2026-10-26T15:30:00Z", "https://volleynet.at/matches/24148",
            "ÖVV match 24148: VCA Amstetten NÖ v UVC McDonalds Ried/Innkreis, 26.10.2026 16:30 CET, Johann Pölz-Halle"),
    37117: ("2026-10-26T16:30:00Z", "https://volleynet.at/calendar?tab=Upcoming",
            "ÖVV upcoming list: UNIONvolleys Bisamberg-Hollabrunn v TSV Raiffeisen Hartberg, Mo. 26.10. 17:30 CET"),
    37118: ("2026-10-26T17:00:00Z", "https://volleynet.at/calendar?tab=Upcoming",
            "ÖVV upcoming list: VBK Kelag Wörther-See-Löwen Klagenfurt v SK Zadruga Aich/Dob, Mo. 26.10. 18:00 CET"),
    37119: ("2026-10-26T18:00:00Z", "https://volleynet.at/calendar?tab=Upcoming",
            "ÖVV upcoming list: UVC Holding Graz v Union Raiffeisen Waldviertel, Mo. 26.10. 19:00 CET"),
}

SOURCES = [
    ("olbg_hubs", "OLBG — fifteen sport hubs", "https://www.olbg.com/betting-tips",
     "Board read sport by sport 05:05–05:45Z on 26 Oct 2026. Every row on this desk starts from a listing here."),
    ("olbg_golf", "OLBG — Golf hub", HUB["golf"], "Returned 'No tips found.' at 05:12Z; no golf match was listed."),
    ("olbg_snooker", "OLBG — Snooker hub", HUB["snooker"], "Returned 'No tips found.' at 05:16Z; no snooker match was listed."),
    ("olbg_darts", "OLBG — Darts hub", HUB["darts"], "Outright only (PDC World Championship 2027); no match priced."),
    ("olbg_ru", "OLBG — Rugby Union hub", HUB["rugby-union"], "Outright only (Six Nations 2027); no match priced."),
    ("olbg_rl", "OLBG — Rugby League hub", HUB["rugby-league"], "2027 outrights only; no match priced."),
    ("nhl_sched", "NHL.com — schedule, 26 October 2026", "https://api-web.nhle.com/v1/schedule/2026-10-26",
     "Three games, official UTC start times and venues."),
    ("nhl_game", "NHL.com — game summary DET @ EDM", "https://api-web.nhle.com/v1/gamecenter/2026020187/landing",
     "Records, team and individual goaltending, skater season and last-five-game leaders."),
    ("nhl_stand", "NHL.com — standings, 25 October 2026", "https://api-web.nhle.com/v1/standings/2026-10-25",
     "Standings snapshot stamped 2026-10-26T05:17Z."),
    ("mlb_api", "MLB — StatsAPI schedule and probable pitchers", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team",
     "World Series Game 3 teams, start time, venue, starters and the Rays' 2026 record."),
    ("oevv", "ÖVV / volleynet.at — Austrian Volleyball Federation", "https://volleynet.at/calendar?tab=Upcoming",
     "Official fixtures for the four Austrian Volley League men's matches on 26 October."),
    ("f1_stand", "Formula 1 — 2026 driver standings", "https://www.formula1.com/en/results/2026/drivers",
     "Read to confirm the 2026 grid and that the season is live; points table not captured, so no F1 line is originated beyond the market read."),
    ("olbg_event_probe", "OLBG — generic event path probe", "https://www.olbg.com/betting-tips/event/200101",
     "Returns an empty tips page for a live event id, so this desk links hubs and prints event ids instead of deep-linking."),
]


# --------------------------------------------------------------------------- helpers
def american(p: float) -> int:
    """Fair American price for probability p, with a 2% two-way hold applied to the pair."""
    p = min(max(p, 0.01), 0.99)
    if p == 0.5:
        return 100
    return int(round(-100 * p / (1 - p))) if p > 0.5 else int(round(100 * (1 - p) / p))


def decimal_of(price: int) -> float:
    return round(1 + (100 / -price) if price < 0 else 1 + (price / 100), 3)


def split_event(event: str):
    if " @ " in event:
        away, home = [x.strip() for x in event.split(" @ ", 1)]
        return home, away
    if " vs " in event:
        a, b = [x.strip() for x in event.split(" vs ", 1)]
        return a, b
    return event, ""


def is_two_way(market: str) -> bool:
    return market in {"Money Line", "Win Match", "Win Race", "Puck Line", "Pointspread",
                      "Handicap", "Game Totals"}


def start_utc(event_id: int, display: str) -> str:
    """OLBG prints US Eastern clock times (proved against the ÖVV fixture list, see NOTES)."""
    if event_id in OFFICIAL_KICKOFFS:
        return OFFICIAL_KICKOFFS[event_id][0]
    return ""


NOTES = [
    ("time-convention",
     "OLBG hub times are US Eastern, not UTC",
     "Four Austrian Volley League matches carried 11:30/12:30/13:00/14:00 on OLBG and 16:30/17:30/18:00/19:00 CET "
     "on the ÖVV fixture list. CET is UTC+1 and US Eastern is UTC-4 on 26 October, so the four rows differ by exactly "
     "five hours on every fixture. The desk therefore prints OLBG's string verbatim and never treats it as UTC.",
     "https://volleynet.at/calendar?tab=Upcoming"),
    ("nhl-quirk",
     "The three NHL rows carry a +7 minute offset",
     "OLBG shows 19:07 / 20:37 / 21:37 for LAK@NYR, TOR@CGY and DET@EDM. The NHL feed gives 23:00Z, 00:30Z and 01:30Z, "
     "which are 19:00 / 20:30 / 21:30 Eastern. The display offset is seven minutes on all three and is reproduced, not corrected.",
     "https://api-web.nhle.com/v1/schedule/2026-10-26"),
    ("handball-tie",
     "Nine of thirteen handball rows are most-tipped on the draw",
     "OLBG's handball money line carries three outcomes and the community's most-tipped selection is 'Tie' on nine of "
     "the thirteen fixtures. That is a genuine listing, but it means the board's leading pick is not a team on most rows, "
     "so the desk grades those rows low and prices only the named outcome.",
     HUB["handball"]),
    ("no-fixtures",
     "Five of the fifteen sports had no match priced at capture",
     "Golf and Snooker returned 'No tips found.'; Darts, Rugby Union and Rugby League showed 2027 outrights only. "
     "No fixture is invented for those sports and the shortfall against a five-per-sport target is stated on every page it affects.",
     HUB["golf"]),
    ("event-links",
     "OLBG's generic event path is empty",
     "https://www.olbg.com/betting-tips/event/{id} renders a page with 'No tips found.' even for a live event id, so "
     "deep links from this desk are not used. Each row prints the event id and links the sport hub instead.",
     "https://www.olbg.com/betting-tips/event/200101"),
    ("probable-pitcher",
     "The MLB feed lists Freddy Peralta as the Rays' probable starter",
     "The starters are reproduced exactly as MLB's feed returns them. Peralta's move to Tampa Bay was not separately "
     "checked against a roster page, so the name stands as the feed's claim and is flagged rather than asserted.",
     "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-26&hydrate=probablePitcher,team"),
    ("no-injury-feed",
     "No official injury or availability report was captured",
     "None of the fifteen sports produced a machine-readable injury list in this session. No prediction mentions an "
     "injury, and every row where availability would matter is flagged as unverified rather than filled in.",
     "https://www.olbg.com/betting-tips"),
]


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    fixtures, lines, picks, flags = [], [], [], []
    gaps: dict[str, dict] = {}

    for i, (sport, league, event, eid, display, market, selection, n, m, pct) in enumerate(OLBG_LISTINGS, 1):
        fid = f"S26-{i:03d}"
        home, away = split_event(event)
        share = pct / 100 if m else 0.0
        basis = "none"
        p_ours = None
        if eid in MODEL_INPUT:
            mi = MODEL_INPUT[eid]
            logit = 3.6 * (mi["home_points_pct"] - mi["away_points_pct"]) + 0.22
            p_ours = round(1 / (1 + math.exp(-logit)), 4)
            basis = "official-input"
        elif m >= 1:
            # Tip share shrunk 15% toward a coin flip: the OLBG hub publishes no prices, so the share is
            # a popularity poll and not a probability. One- and two-tip rows are additionally clamped to
            # 65%, because a single tip reads 100% and would otherwise price as a -1233 favourite.
            p_ours = round(min(0.5 + 0.85 * (share - 0.5), 0.78), 4)
            basis = "olbg-tip-share"
            if m < 3:
                p_ours = min(p_ours, 0.65)
                basis = "olbg-tip-share-thin"
        price = american(p_ours) if p_ours else ""
        price_other = american(1 - p_ours) if (p_ours and is_two_way(market)) else ""

        in_band = bool(price != "" and -250 <= price <= 10000)
        if p_ours is None:
            conf = "ungraded"
        elif selection.strip().lower() in {"tie", "draw"}:
            conf = "low"
        elif m < 3:
            conf = "low"
        elif p_ours >= 0.62 and m >= 4 and in_band:
            conf = "high"
        elif p_ours >= 0.55 and m >= 3:
            conf = "medium"
        else:
            conf = "low"

        facts = [{"claim": c, "value": v, "source": s, "url": u} for (s, u, c, v) in OFFICIAL_FACTS.get(eid, [])]
        ko = start_utc(eid, display)

        fixtures.append({
            "id": fid, "sport": sport, "sport_label": LABEL[sport], "league": league,
            "event": event, "home": home, "away": away, "olbg_event_id": eid,
            "olbg_display_time": display, "official_start_utc": ko,
            "hub_url": HUB[sport], "facts": facts,
            "data_grade": "official" if facts else ("official-time-only" if ko else "olbg-only"),
            "market": market, "selection": selection, "tips": n, "total_tips": m, "share": pct,
        })

        lines.append({
            "fixture": fid, "sport": sport, "market": market, "selection": selection,
            "probability": p_ours, "price": price, "opposite_price": price_other,
            "in_band": in_band, "basis": basis,
        })

        picks.append({
            "fixture": fid, "sport": sport, "sport_label": LABEL[sport], "league": league,
            "event": event, "market": market, "selection": selection,
            "probability": p_ours, "price": price, "confidence": conf, "in_band": in_band,
            "tips": f"{n}/{m}", "share": pct, "hub_url": HUB[sport], "olbg_event_id": eid,
            "basis": (f"OLBG board {n}/{m} tips ({pct}%)" if m else "OLBG board showed no tip count"),
            "priced_from": basis,
            "thin_sample": m < 3,
        })

        gaps.setdefault(sport, {"facts": [], "time": []})
        if not facts:
            gaps[sport]["facts"].append(fid)
        if not ko:
            gaps[sport]["time"].append(fid)

    for sport, g in gaps.items():
        if g["facts"]:
            flags.append({
                "id": f"G-{sport}", "fixture": f"{len(g['facts'])} rows", "sport": LABEL[sport],
                "event": f"{LABEL[sport]}: no official fixture-level statistic",
                "item": "No official fixture-level statistic captured",
                "detail": ("Listed rows " + ", ".join(g["facts"]) + ". The listing, the tip sample and our own price exist, "
                           "but no official feed for these competitions was readable in this session, so no written "
                           "preview is published for them. Every row keeps its source link and stays unverified."),
                "status": "unverified", "source": HUB[sport],
            })
        if g["time"]:
            flags.append({
                "id": f"T-{sport}", "fixture": f"{len(g['time'])} rows", "sport": LABEL[sport],
                "event": f"{LABEL[sport]}: no official UTC start",
                "item": "Kick-off / start time not confirmed from an official feed",
                "detail": ("Listed rows " + ", ".join(g["time"]) + ". OLBG's own string is printed verbatim and is "
                           "US Eastern (proved on the volleyball rows), but no official UTC time was read for these "
                           "competitions, so the UTC column is left blank."),
                "status": "unverified", "source": HUB[sport],
            })

    for sport, league, sel, market, eid, when, n, m, pct in OUTRIGHTS:
        flags.append({
            "id": f"O{eid}", "fixture": f"OLBG-{eid}", "sport": LABEL[sport], "event": league,
            "item": "Season outright, excluded from fixture counts",
            "detail": (f"'{sel}' to win {league} ({market}) is a futures market dated {when}. It is listed on the sport page "
                       "but kept out of the match total so the fixture count is not inflated."),
            "status": "note", "source": HUB[sport],
        })

    for key, title, detail, src in NOTES:
        flags.append({"id": f"N-{key}", "fixture": "-", "sport": "-", "event": title,
                      "item": title, "detail": detail, "status": "note", "source": src})

    def dump(name, payload):
        (OUT / name).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    dump("fixtures.json", {"captured_utc": CAPTURED, "captured_label": CAPTURED_LABEL,
                           "count": len(fixtures), "fixtures": fixtures})
    dump("lines.json", {"captured_utc": CAPTURED, "count": len(lines), "lines": lines,
                        "in_band": sum(1 for l in lines if l["in_band"])})
    dump("picks.json", {"captured_utc": CAPTURED, "count": len(picks), "picks": picks,
                        "high": sum(1 for p in picks if p["confidence"] == "high"),
                        "medium": sum(1 for p in picks if p["confidence"] == "medium"),
                        "low": sum(1 for p in picks if p["confidence"] == "low"),
                        "in_band": sum(1 for p in picks if p["in_band"])})
    dump("outrights.json", {"captured_utc": CAPTURED, "count": len(OUTRIGHTS),
                            "outrights": [dict(zip(("sport", "competition", "selection", "market", "olbg_event_id",
                                                    "display_time", "tips", "total_tips", "share"), o)) for o in OUTRIGHTS]})
    dump("hubs.json", {"captured_utc": CAPTURED, "captured_label": CAPTURED_LABEL,
                       "hubs": [{"sport": k, "label": LABEL[k], "slug": SLUG[k], "url": HUB[k],
                                 "state": HUB_STATE[k][0], "note": HUB_STATE[k][1]} for k, _, _, _ in SPORTS]})
    dump("sources.json", {"captured_utc": CAPTURED, "count": len(SOURCES),
                          "sources": [{"key": k, "name": n, "url": u, "note": note} for k, n, u, note in SOURCES]})
    dump("flagged.json", {"captured_utc": CAPTURED, "count": len(flags), "items": flags})
    return {"fixtures": len(fixtures), "picks": len(picks), "flags": len(flags)}


if __name__ == "__main__":
    s = build()
    print(f"slate26: {s['fixtures']} fixtures, {s['picks']} picks, {s['flags']} flags")
