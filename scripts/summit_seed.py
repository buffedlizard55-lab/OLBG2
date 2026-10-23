#!/usr/bin/env python3
"""Summit desk seed — build committed first-hand data for /summit/ from OLBG discovery
plus official governing-body captures read in this session.

Deterministic: same inputs, same bytes. Nothing is fetched at build time.
Run: python3 scripts/summit_seed.py
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "summit")
CAPTURES = os.path.join(DATA, "captures")
os.makedirs(CAPTURES, exist_ok=True)

GENERATED = "2026-10-23T22:00:00Z"
SESSION = "arena/84013d5f-olbg2"
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
CUTOFF = "2026-10-23T21:45:00Z"

# Official source register for this desk. Every key cited by a fixture fact must appear here.
SOURCES = [
    {"key": "nhle_schedule", "url": "https://api-web.nhle.com/v1/schedule/2026-10-23", "sport": "Ice Hockey", "kind": "official-json", "note": "NHL official schedule feed"},
    {"key": "nhle_standings", "url": "https://api-web.nhle.com/v1/standings/2026-10-23", "sport": "Ice Hockey", "kind": "official-json", "note": "NHL official standings"},
    {"key": "mlb_schedule", "url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-29&hydrate=probablePitcher,linescore,team", "sport": "Baseball", "kind": "official-json", "note": "MLB official StatsAPI schedule"},
    {"key": "mlb_teams", "url": "https://statsapi.mlb.com/api/v1/teams?teamIds=139,158&hydrate=standings,teamStats(group=[hitting,pitching],type=[season],season=2026)", "sport": "Baseball", "kind": "official-json", "note": "MLB official team records and season stats"},
    {"key": "mlb_people", "url": "https://statsapi.mlb.com/api/v1/people?personIds=607259,694819,656876,701656&hydrate=stats(group=[pitching],type=[season],season=2026)", "sport": "Baseball", "kind": "official-json", "note": "MLB official probable pitcher season stats"},
    {"key": "urc_round4", "url": "https://stats.unitedrugby.com/match-centre/2026-27/4", "sport": "Rugby Union", "kind": "official-html", "note": "URC official match centre Round 4"},
    {"key": "urc_table", "url": "https://stats.unitedrugby.com/match-centre/table/2026-27", "sport": "Rugby Union", "kind": "official-html", "note": "URC official league table"},
    {"key": "lnh_classement", "url": "https://www.lnh.fr/daikin-starligue/classement", "sport": "Handball", "kind": "official-html", "note": "LNH official Daikin StarLigue table"},
    {"key": "lnh_calendrier", "url": "https://www.lnh.fr/daikin-starligue/calendrier", "sport": "Handball", "kind": "official-html", "note": "LNH official Daikin StarLigue calendar"},
    {"key": "lnh_ehfcl", "url": "https://www.lnh.fr/autres-competitions/ligue-des-champions", "sport": "Handball", "kind": "official-html", "note": "LNH official EHF Champions League calendar"},
    {"key": "legavolley_calendario", "url": "https://www.legavolley.it/calendario/?idCampionato=999", "sport": "Volleyball", "kind": "official-html", "note": "Lega Pallavolo Serie A official calendar"},
    {"key": "legavolley_classifica", "url": "https://www.legavolley.it/classifica/?IdCampionato=999", "sport": "Volleyball", "kind": "official-html", "note": "Lega Pallavolo Serie A official table"},
    {"key": "vbl_current", "url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml", "sport": "Volleyball", "kind": "official-html", "note": "VBL official men's Bundesliga table and current matches"},
    {"key": "atp_almaty", "url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "sport": "Tennis", "kind": "official-html", "note": "ATP Tour official Almaty daily schedule"},
    {"key": "atp_brussels", "url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "sport": "Tennis", "kind": "official-html", "note": "ATP Tour official Brussels daily schedule"},
    {"key": "atp_h2h_basil_tsitsi", "url": "https://www.atptour.com/en/players/atp-head-2-head/nikoloz-basilashvili-vs-stefanos-tsitsipas/bg23/te51", "sport": "Tennis", "kind": "official-html", "note": "ATP Tour official head-to-head"},
    {"key": "pdc_euro_championship", "url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/", "sport": "Darts", "kind": "official-html", "note": "PDC official European Championship preview and schedule"},
    {"key": "pdc_euro_day_two", "url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest", "sport": "Darts", "kind": "official-html", "note": "PDC official European Championship Day Two report"},
    {"key": "wst_matches", "url": "https://www.wst.tv/matches/", "sport": "Snooker", "kind": "official-html", "note": "World Snooker Tour official matches page"},
    {"key": "olbg_hub", "url": "https://www.olbg.com/betting-tips", "sport": "OLBG", "kind": "discovery-html", "note": "OLBG discovery page (not a governing body; blank rows are not priced)"},
    {"key": "pgatour_leaderboard", "url": "https://www.pgatour.com/leaderboard", "sport": "Golf", "kind": "official-html", "note": "PGA Tour official Butterfield Bermuda Championship leaderboard"},
    {"key": "f1_usgp", "url": "https://www.formula1.com/en/racing/2026/united-states", "sport": "Motor Racing", "kind": "official-html", "note": "Formula 1 official United States Grand Prix page"},
    {"key": "f1_drivers", "url": "https://www.formula1.com/en/results/2026/drivers", "sport": "Motor Racing", "kind": "official-html", "note": "Formula 1 official 2026 drivers' standings"},
    {"key": "gbgb_scurry", "url": "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/", "sport": "Greyhounds", "kind": "official-html", "note": "GBGB official Scurry Gold Cup preview"},
    {"key": "gbgb_oaks", "url": "https://www.gbgb.org.uk/signet-nayla-chases-oaks-glory-as-hutton-targets-dunstall-park-double/", "sport": "Greyhounds", "kind": "official-html", "note": "GBGB official Oaks final preview"},
    {"key": "gbgb_trainers", "url": "https://www.gbgb.org.uk/trainer-of-the-year-standings-up-to-and-including-sunday-18th-october/", "sport": "Greyhounds", "kind": "official-html", "note": "GBGB official trainer standings"},
    {"key": "gaa_cork", "url": "https://gaacork.ie/fixtures/", "sport": "Gaelic Sports", "kind": "official-html", "note": "Cork GAA official fixtures"},
    {"key": "gaa_ie", "url": "https://www.gaa.ie/fixtures-results", "sport": "Gaelic Sports", "kind": "official-html", "note": "GAA official fixtures and results"},
]

# Mapping from OLBG event_id to official verification. Only events with an official page
# captured this session are marked originated; every other OLBG-listed event stays blank.
OFFICIAL = {
    "199984": {
        "official_source_url": "https://api-web.nhle.com/v1/schedule/2026-10-23",
        "stats_source_url": "https://api-web.nhle.com/v1/standings/2026-10-23",
        "facts": [
            {"item": "Montréal Canadiens", "text": "4-3-2 in 9 games, 30 goals for, 34 against, 10 points, OT1 streak, 3-2-1 home / 1-1-1 road", "source_key": "nhle_standings", "source_url": "https://api-web.nhle.com/v1/standings/2026-10-23"},
            {"item": "Chicago Blackhawks", "text": "3-6-0 in 9 games, 21 goals for, 36 against, 6 points, 0-4-0 on the road", "source_key": "nhle_standings", "source_url": "https://api-web.nhle.com/v1/standings/2026-10-23"},
            {"item": "NHL fixture", "text": "Montreal Canadiens at Chicago Blackhawks, United Center, 2026-10-24T00:00:00Z, NHL schedule state FUT", "source_key": "nhle_schedule", "source_url": "https://api-web.nhle.com/v1/schedule/2026-10-23"},
        ],
    },
    "199985": {
        "official_source_url": "https://api-web.nhle.com/v1/schedule/2026-10-23",
        "stats_source_url": "https://api-web.nhle.com/v1/standings/2026-10-23",
        "facts": [
            {"item": "Tampa Bay Lightning", "text": "7-2-0 in 9 games, 31 goals for, 23 against, 14 points, W3 streak, 5-0-0 home / 2-2-0 road", "source_key": "nhle_standings", "source_url": "https://api-web.nhle.com/v1/standings/2026-10-23"},
            {"item": "Colorado Avalanche", "text": "5-4-1 in 10 games, 41 goals for, 36 against, 11 points, L2 streak, 3-3-1 home / 2-2-0 road", "source_key": "nhle_standings", "source_url": "https://api-web.nhle.com/v1/standings/2026-10-23"},
            {"item": "NHL fixture", "text": "Tampa Bay Lightning at Colorado Avalanche, Ball Arena, 2026-10-24T01:00:00Z, NHL schedule state FUT", "source_key": "nhle_schedule", "source_url": "https://api-web.nhle.com/v1/schedule/2026-10-23"},
        ],
    },
    "160789": {
        "official_source_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-29&hydrate=probablePitcher,linescore,team",
        "stats_source_url": "https://statsapi.mlb.com/api/v1/teams?teamIds=139,158&hydrate=standings,teamStats(group=[hitting,pitching],type=[season],season=2026)",
        "facts": [
            {"item": "Tampa Bay Rays", "text": "98-64 in 2026, .605 winning percentage, 736 runs scored, 650 allowed, AL East division champion", "source_key": "mlb_teams", "source_url": "https://statsapi.mlb.com/api/v1/teams?teamIds=139,158&hydrate=standings,teamStats(group=[hitting,pitching],type=[season],season=2026)"},
            {"item": "Milwaukee Brewers", "text": "103-59 in 2026, .636 winning percentage, 832 runs scored, 618 allowed, NL Central division champion", "source_key": "mlb_teams", "source_url": "https://statsapi.mlb.com/api/v1/teams?teamIds=139,158&hydrate=standings,teamStats(group=[hitting,pitching],type=[season],season=2026)"},
            {"item": "World Series Game 1", "text": "Tampa Bay Rays at Milwaukee Brewers, American Family Field, 2026-10-24T00:00:00Z, probable pitchers Nick Martinez (Rays) and Jacob Misiorowski (Brewers)", "source_key": "mlb_schedule", "source_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-29&hydrate=probablePitcher,linescore,team"},
            {"item": "Nick Martinez", "text": "2026: 15-6, 3.10 ERA, 1.09 WHIP, 180.0 innings, 31 starts", "source_key": "mlb_people", "source_url": "https://statsapi.mlb.com/api/v1/people?personIds=607259,694819,656876,701656&hydrate=stats(group=[pitching],type=[season],season=2026)"},
            {"item": "Jacob Misiorowski", "text": "2026: 16-5, 1.80 ERA, 0.80 WHIP, 174.2 innings, 30 starts, 252 strikeouts", "source_key": "mlb_people", "source_url": "https://statsapi.mlb.com/api/v1/people?personIds=607259,694819,656876,701656&hydrate=stats(group=[pitching],type=[season],season=2026)"},
        ],
    },
    "609576": {
        "official_source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4",
        "stats_source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27",
        "facts": [
            {"item": "Vodacom Bulls", "text": "URC 2026/27: 2-0-1, 11 points, 126 points for, 54 against after Round 3", "source_key": "urc_table", "source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"item": "Ulster Rugby", "text": "URC 2026/27: 0-2-1, 8 points, 88 points for, 93 against after Round 3", "source_key": "urc_table", "source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"item": "URC fixture", "text": "Bulls v Ulster, Round 4, Saturday 24 October 2026, 07:45 local as published by URC", "source_key": "urc_round4", "source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
        ],
    },
    "609580": {
        "official_source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4",
        "stats_source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27",
        "facts": [
            {"item": "DHL Stormers", "text": "URC 2026/27: 2-0-1, 11 points, 81 points for, 54 against after Round 3", "source_key": "urc_table", "source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"item": "Scarlets", "text": "URC 2026/27: 1-0-2, 7 points, 68 points for, 85 against after Round 3", "source_key": "urc_table", "source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"item": "URC fixture", "text": "Stormers v Scarlets, Round 4, Saturday 24 October 2026, 10:00 local as published by URC", "source_key": "urc_round4", "source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
        ],
    },
    "609571": {
        "official_source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4",
        "stats_source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27",
        "facts": [
            {"item": "Glasgow Warriors", "text": "URC 2026/27: 2-0-1, 13 points, 95 points for, 72 against after Round 3", "source_key": "urc_table", "source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"item": "Benetton Rugby", "text": "URC 2026/27: 0-1-2, 5 points, 64 points for, 68 against after Round 3", "source_key": "urc_table", "source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"item": "URC fixture", "text": "Benetton Rugby v Glasgow Warriors, Round 4, Saturday 24 October 2026, 10:00 local as published by URC", "source_key": "urc_round4", "source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
        ],
    },
    "12082": {
        "official_source_url": "https://www.lnh.fr/daikin-starligue/calendrier",
        "stats_source_url": "https://www.lnh.fr/daikin-starligue/classement",
        "facts": [
            {"item": "HBC Nantes", "text": "LNH Daikin StarLigue 2026/27: 6-1-0, 12 points, 244 goals for, 203 against", "source_key": "lnh_classement", "source_url": "https://www.lnh.fr/daikin-starligue/classement"},
            {"item": "Chambéry Savoie Mont-Blanc Handball", "text": "LNH Daikin StarLigue 2026/27: 2-3-2, 6 points, 224 goals for, 231 against", "source_key": "lnh_classement", "source_url": "https://www.lnh.fr/daikin-starligue/classement"},
            {"item": "LNH fixture", "text": "Nantes v Chambéry, J08, Saturday 24 October 2026, 19:00 local as published by LNH", "source_key": "lnh_calendrier", "source_url": "https://www.lnh.fr/daikin-starligue/calendrier"},
        ],
    },
    "12084": {
        "official_source_url": "https://www.lnh.fr/daikin-starligue/calendrier",
        "stats_source_url": "https://www.lnh.fr/daikin-starligue/classement",
        "facts": [
            {"item": "Paris Saint-Germain Handball", "text": "LNH Daikin StarLigue 2026/27: 7-0-0, 14 points, 239 goals for, 190 against", "source_key": "lnh_classement", "source_url": "https://www.lnh.fr/daikin-starligue/classement"},
            {"item": "Saint-Raphaël Var Handball", "text": "LNH Daikin StarLigue 2026/27: 2-5-0, 4 points, 207 goals for, 225 against", "source_key": "lnh_classement", "source_url": "https://www.lnh.fr/daikin-starligue/classement"},
            {"item": "LNH fixture", "text": "Saint-Raphaël v Paris, J08, Sunday 25 October 2026, 16:00 local as published by LNH", "source_key": "lnh_calendrier", "source_url": "https://www.lnh.fr/daikin-starligue/calendrier"},
        ],
    },
    "12138": {
        "official_source_url": "https://www.lnh.fr/autres-competitions/ligue-des-champions",
        "stats_source_url": "https://www.lnh.fr/daikin-starligue/classement",
        "facts": [
            {"item": "Wisła Płock v Nantes", "text": "EHF Champions League J06, Wednesday 28 October 2026, 18:45 local as published by LNH", "source_key": "lnh_ehfcl", "source_url": "https://www.lnh.fr/autres-competitions/ligue-des-champions"},
            {"item": "HBC Nantes", "text": "LNH Daikin StarLigue 2026/27: 6-1-0, 12 points, 244 goals for, 203 against", "source_key": "lnh_classement", "source_url": "https://www.lnh.fr/daikin-starligue/classement"},
        ],
    },
    "12134": {
        "official_source_url": "https://www.lnh.fr/autres-competitions/ligue-des-champions",
        "stats_source_url": "https://www.lnh.fr/daikin-starligue/classement",
        "facts": [
            {"item": "Paris Saint-Germain Handball v Aalborg", "text": "EHF Champions League J06, Thursday 29 October 2026, 20:45 local as published by LNH", "source_key": "lnh_ehfcl", "source_url": "https://www.lnh.fr/autres-competitions/ligue-des-champions"},
            {"item": "Paris Saint-Germain Handball", "text": "LNH Daikin StarLigue 2026/27: 7-0-0, 14 points, 239 goals for, 190 against", "source_key": "lnh_classement", "source_url": "https://www.lnh.fr/daikin-starligue/classement"},
        ],
    },
    "12133": {
        "official_source_url": "https://www.lnh.fr/autres-competitions/ligue-des-champions",
        "stats_source_url": "https://www.lnh.fr/daikin-starligue/classement",
        "facts": [
            {"item": "Montpellier v Dinamo București", "text": "EHF Champions League J06, Thursday 29 October 2026, 20:45 local as published by LNH", "source_key": "lnh_ehfcl", "source_url": "https://www.lnh.fr/autres-competitions/ligue-des-champions"},
            {"item": "Montpellier Handball", "text": "LNH Daikin StarLigue 2026/27: 4-1-2, 10 points, 234 goals for, 205 against", "source_key": "lnh_classement", "source_url": "https://www.lnh.fr/daikin-starligue/classement"},
        ],
    },
    "37010": {
        "official_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "stats_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "facts": [
            {"item": "VfB Friedrichshafen", "text": "VBL men 2026/27: 1-1, 3 points, 3 sets won, 1 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "BADEN VOLLEYS SSC Karlsruhe", "text": "VBL men 2026/27: 1-1, 3 points, 3 sets won, 0 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "VBL fixture", "text": "Friedrichshafen v Karlsruhe, Saturday 24 October 2026, 18:30 local as published by VBL current matches", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
        ],
    },
    "37012": {
        "official_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "stats_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "facts": [
            {"item": "SWD powervolleys Düren", "text": "VBL men 2026/27: 1-1, 3 points, 3 sets won, 0 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "WWK Volleys München", "text": "VBL men 2026/27: 1-0, 0 points, 1 set won, 3 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "VBL fixture", "text": "Düren v München, Saturday 24 October 2026, 19:30 local as published by VBL current matches", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
        ],
    },
    "37013": {
        "official_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "stats_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "facts": [
            {"item": "Helios Grizzlys Giesen", "text": "VBL men 2026/27: 1-1, 2 points, 3 sets won, 2 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "BERLIN RECYCLING Volleys", "text": "VBL men 2026/27: 1-1, 3 points, 3 sets won, 0 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "VBL fixture", "text": "Giesen v Berlin, Saturday 24 October 2026, 19:30 local as published by VBL current matches", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
        ],
    },
    "37011": {
        "official_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "stats_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "facts": [
            {"item": "SVG Lüneburg", "text": "VBL men 2026/27: listed in current matches", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "SV Warnemünde", "text": "VBL men 2026/27: 1-1, 2 points, 3 sets won, 2 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "VBL fixture", "text": "Lüneburg v Warnemünde, Saturday 24 October 2026, 19:00 local as published by VBL current matches", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
        ],
    },
    "37014": {
        "official_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "stats_source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
        "facts": [
            {"item": "Barock Volleys MTV Ludwigsburg", "text": "VBL men 2026/27: 0-0, 0 points, 0 sets won, 0 lost", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "TV Rottenburg", "text": "VBL men 2026/27: listed in current matches", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
            {"item": "VBL fixture", "text": "Ludwigsburg v Rottenburg, Sunday 25 October 2026, 17:00 local as published by VBL current matches", "source_key": "vbl_current", "source_url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml"},
        ],
    },
    "902159": {
        "official_source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule",
        "stats_source_url": "https://www.atptour.com/en/players/atp-head-2-head/nikoloz-basilashvili-vs-stefanos-tsitsipas/bg23/te51",
        "facts": [
            {"item": "ATP fixture", "text": "Nikoloz Basilashvili v Stefanos Tsitsipas, Almaty semifinal, Saturday 24 October 2026, not before 17:00 local", "source_key": "atp_almaty", "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"},
            {"item": "Head to head", "text": "Stefanos Tsitsipas leads Nikoloz Basilashvili 3-1; most recent Australian Open 2019 6-3 3-6 7-6(7) 6-4", "source_key": "atp_h2h_basil_tsitsi", "source_url": "https://www.atptour.com/en/players/atp-head-2-head/nikoloz-basilashvili-vs-stefanos-tsitsipas/bg23/te51"},
            {"item": "ATP rankings context", "text": "Stefanos Tsitsipas ranked 39th, Nikoloz Basilashvili ranked 128th on the official ATP Tour page", "source_key": "atp_h2h_basil_tsitsi", "source_url": "https://www.atptour.com/en/players/atp-head-2-head/nikoloz-basilashvili-vs-stefanos-tsitsipas/bg23/te51"},
        ],
    },
    "32383": {
        "official_source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/",
        "stats_source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest",
        "facts": [
            {"item": "PDC fixture", "text": "Cameron Menzies v Gerwyn Price, European Championship Round Two, Saturday 24 October 2026 afternoon session", "source_key": "pdc_euro_championship", "source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/"},
            {"item": "Round One results", "text": "Menzies beat Niels Zonneveld 6-3; Price beat Rob Cross 6-2", "source_key": "pdc_euro_day_two", "source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest"},
        ],
    },
    "32385": {
        "official_source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/",
        "stats_source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest",
        "facts": [
            {"item": "PDC fixture", "text": "Gian van Veen v Luke Woodhouse, European Championship Round Two, Saturday 24 October 2026 afternoon session", "source_key": "pdc_euro_championship", "source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/"},
            {"item": "Round One results", "text": "Van Veen beat Andrew Gilding 6-4; Woodhouse beat Dirk van Duijvenbode 6-3 including a nine-darter", "source_key": "pdc_euro_day_two", "source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest"},
        ],
    },
    "32386": {
        "official_source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/",
        "stats_source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest",
        "facts": [
            {"item": "PDC fixture", "text": "Ross Smith v Damon Heta, European Championship Round Two, Saturday 24 October 2026 afternoon session", "source_key": "pdc_euro_championship", "source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/"},
            {"item": "Round One results", "text": "Smith beat Karel Sedlacek 6-4; Heta beat James Wade 6-5", "source_key": "pdc_euro_day_two", "source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest"},
        ],
    },
    "32384": {
        "official_source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/",
        "stats_source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest",
        "facts": [
            {"item": "PDC fixture", "text": "Stephen Bunting v Kim Huybrechts, European Championship Round Two, Saturday 24 October 2026 afternoon session", "source_key": "pdc_euro_championship", "source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/"},
            {"item": "Round One results", "text": "Bunting beat Danny Noppert 6-5; Huybrechts beat Ryan Searle 6-1 as a Humphries replacement", "source_key": "pdc_euro_day_two", "source_url": "https://www.pdc.tv/news/2026/october/23/2026-machineseeker-european-championship---day-two-latest"},
        ],
    },
    "913": {
        "official_source_url": "https://www.formula1.com/en/racing/2026/united-states",
        "stats_source_url": "https://www.formula1.com/en/results/2026/drivers",
        "facts": [
            {"item": "Formula 1 fixture", "text": "United States Grand Prix, Circuit of the Americas, race Sunday 25 October 2026, 16:00 track time", "source_key": "f1_usgp", "source_url": "https://www.formula1.com/en/racing/2026/united-states"},
            {"item": "Practice 1", "text": "Charles Leclerc fastest, Max Verstappen +0.084s, Lando Norris +0.245s, George Russell +0.326s, Kimi Antonelli +0.481s", "source_key": "f1_usgp", "source_url": "https://www.formula1.com/en/racing/2026/united-states"},
            {"item": "Drivers' championship", "text": "Kimi Antonelli 340 points, George Russell 238, Lewis Hamilton 229, Max Verstappen 221, Charles Leclerc 215", "source_key": "f1_drivers", "source_url": "https://www.formula1.com/en/results/2026/drivers"},
        ],
    },
    "3530": {
        "official_source_url": "https://gaacork.ie/fixtures/",
        "stats_source_url": "https://gaacork.ie/fixtures/",
        "facts": [
            {"item": "GAA fixture", "text": "Cork Premier Senior Football Championship Final, St Finbarr's v Nemo Rangers, Sunday 25 October 2026, 16:00, SuperValu Páirc Uí Chaoimh, referee David Murnane", "source_key": "gaa_cork", "source_url": "https://gaacork.ie/fixtures/"},
            {"item": "Semi-finals", "text": "Nemo Rangers beat Carrigaline 1-15 to 0-16; St Finbarr's beat Clonakilty 2-12 to 0-16", "source_key": "gaa_cork", "source_url": "https://gaacork.ie/fixtures/"},
        ],
    },
}

EXTRA_FIXTURES = [
    {
        "sport": "Golf",
        "competition": "Butterfield Bermuda Championship 2026",
        "home": "Butterfield Bermuda Championship",
        "away": None,
        "start_utc": "2026-10-24T12:00:00Z",
        "time_display": "Round three from 24 October 2026, tee times from 09:06 local",
        "venue": "Port Royal Golf Course, Southampton, Bermuda",
        "official_source_url": "https://www.pgatour.com/leaderboard",
        "stats_source_url": "https://www.pgatour.com/leaderboard",
        "facts": [
            {"item": "PGA Tour fixture", "text": "Butterfield Bermuda Championship, Round three from 24 October 2026, Port Royal Golf Course", "source_key": "pgatour_leaderboard", "source_url": "https://www.pgatour.com/leaderboard"},
            {"item": "Leaderboard after Round 2", "text": "Kensei Hirata and Chandler Blanchet lead at -13; Seamus Power, Corey Conners, Eric Cole, Ben Silverman and Danny Walker are T3 at -12", "source_key": "pgatour_leaderboard", "source_url": "https://www.pgatour.com/leaderboard"},
        ],
    },
    {
        "sport": "Snooker",
        "competition": "BetVictor Northern Ireland Open 2026",
        "home": "Kyren Wilson",
        "away": "Sam Craigie",
        "start_utc": "2026-10-24T08:00:00Z",
        "time_display": "Saturday 24 October 2026, 08:00 (WST site clock)",
        "venue": "Waterfront Hall, Belfast",
        "official_source_url": "https://www.wst.tv/matches/",
        "stats_source_url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false",
        "facts": [
            {"item": "WST fixture", "text": "Kyren Wilson v Sam Craigie, Northern Ireland Open semi-final, Match 61, Saturday 24 October 2026, 08:00", "source_key": "wst_matches", "source_url": "https://www.wst.tv/matches/"},
            {"item": "Quarter-final result", "text": "Kyren Wilson beat Anthony McGill 6-1 in the quarter-finals on Friday 23 October", "source_key": "wst_matches", "source_url": "https://www.wst.tv/matches/"},
            {"item": "Quarter-final result", "text": "Sam Craigie beat Elliot Slessor 6-2 in the quarter-finals on Friday 23 October", "source_key": "wst_matches", "source_url": "https://www.wst.tv/matches/"},
        ],
    },
    {
        "sport": "Snooker",
        "competition": "International Championship 2026",
        "home": "Shaun Murphy",
        "away": "Mitchell Mann",
        "start_utc": "2026-10-30T21:30:00Z",
        "time_display": "Friday 30 October 2026, 21:30 (WST match centre)",
        "venue": "Nanjing, China",
        "official_source_url": "https://www.wst.tv/match-centre/5151a488-4a16-4e5f-95e4-f74b9eb0e19b",
        "stats_source_url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false",
        "facts": [
            {"item": "WST fixture", "text": "Shaun Murphy v Mitchell Mann, International Championship Round 2, Friday 30 October 2026, 21:30", "source_key": "wst_matches", "source_url": "https://www.wst.tv/matches/"},
        ],
    },
    {
        "sport": "Greyhounds",
        "competition": "Arena Racing Company Scurry Gold Cup Final",
        "home": "Shadow Storm",
        "away": None,
        "start_utc": "2026-10-24T19:00:00Z",
        "time_display": "Saturday 24 October 2026, evening card, Dunstall Park",
        "venue": "Dunstall Park, Wolverhampton",
        "official_source_url": "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/",
        "stats_source_url": "https://www.gbgb.org.uk/trainer-of-the-year-standings-up-to-and-including-sunday-18th-october/",
        "facts": [
            {"item": "GBGB fixture", "text": "Scurry Gold Cup Final, Saturday 24 October 2026, £12,500 to the winner, Dunstall Park", "source_key": "gbgb_scurry", "source_url": "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/"},
            {"item": "Shadow Storm", "text": "Reigning GBGB Sprinter of the Year; won the third Scurry semi-final in 15.66sec (-5)", "source_key": "gbgb_scurry", "source_url": "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/"},
            {"item": "Trainer standings", "text": "Maxine Locke leads GBGB Trainer of the Year on 1,016 points after Sunday 18 October", "source_key": "gbgb_trainers", "source_url": "https://www.gbgb.org.uk/trainer-of-the-year-standings-up-to-and-including-sunday-18th-october/"},
        ],
    },
    {
        "sport": "Greyhounds",
        "competition": "Premier Greyhound Racing Oaks Final",
        "home": "Signet Nayla",
        "away": None,
        "start_utc": "2026-10-24T19:00:00Z",
        "time_display": "Saturday 24 October 2026, evening card, Dunstall Park",
        "venue": "Dunstall Park, Wolverhampton",
        "official_source_url": "https://www.gbgb.org.uk/signet-nayla-chases-oaks-glory-as-hutton-targets-dunstall-park-double/",
        "stats_source_url": "https://www.gbgb.org.uk/trainer-of-the-year-standings-up-to-and-including-sunday-18th-october/",
        "facts": [
            {"item": "GBGB fixture", "text": "Oaks Final, Saturday 24 October 2026, £20,000 contest, Dunstall Park", "source_key": "gbgb_oaks", "source_url": "https://www.gbgb.org.uk/signet-nayla-chases-oaks-glory-as-hutton-targets-dunstall-park-double/"},
            {"item": "Signet Nayla", "text": "Won the first Oaks semi-final in 28.35sec (-10), a length and a quarter clear", "source_key": "gbgb_oaks", "source_url": "https://www.gbgb.org.uk/signet-nayla-chases-oaks-glory-as-hutton-targets-dunstall-park-double/"},
        ],
    },
    {
        "sport": "Gaelic Sports",
        "competition": "Cork Premier Senior Football Championship Final",
        "home": "St Finbarr's",
        "away": "Nemo Rangers",
        "start_utc": "2026-10-25T15:00:00Z",
        "time_display": "Sunday 25 October 2026, 16:00 local",
        "venue": "SuperValu Páirc Uí Chaoimh, Cork",
        "official_source_url": "https://gaacork.ie/fixtures/",
        "stats_source_url": "https://gaacork.ie/fixtures/",
        "facts": [
            {"item": "GAA fixture", "text": "St Finbarr's v Nemo Rangers, Sunday 25 October 2026, 16:00, referee David Murnane", "source_key": "gaa_cork", "source_url": "https://gaacork.ie/fixtures/"},
            {"item": "Semi-finals", "text": "Nemo Rangers beat Carrigaline 1-15 to 0-16; St Finbarr's beat Clonakilty 2-12 to 0-16", "source_key": "gaa_cork", "source_url": "https://gaacork.ie/fixtures/"},
        ],
    },
    {
        "sport": "Gaelic Sports",
        "competition": "Shinty-Hurling International",
        "home": "Ireland",
        "away": "Scotland",
        "start_utc": "2026-10-24T17:00:00Z",
        "time_display": "Saturday 24 October 2026, 18:00 local",
        "venue": "SuperValu Páirc Uí Chaoimh, Cork",
        "official_source_url": "https://www.gaa.ie/fixtures-results",
        "stats_source_url": "https://www.gaa.ie/fixtures-results",
        "facts": [
            {"item": "GAA fixture", "text": "Ireland v Scotland Shinty-Hurling International, Saturday 24 October 2026, 18:00, SuperValu Páirc Uí Chaoimh, Cork", "source_key": "gaa_ie", "source_url": "https://www.gaa.ie/fixtures-results"},
        ],
    },
]

def load_olbg():
    path = os.path.join(ROOT, "data", "ledger", "olbg.json")
    with open(path) as f:
        return json.load(f)

def main():
    olbg = load_olbg()
    by_event = {}
    for tip in olbg["tips"]:
        key = (tip["sport"], tip.get("event_id") or tip["event"])
        if key not in by_event:
            by_event[key] = tip

    fixtures = []
    for (sport, key_name), tip in sorted(by_event.items(), key=lambda kv: (kv[1].get("start") or "", kv[1].get("event") or "")):
        start = tip.get("start") or ""
        if start < CUTOFF:
            continue
        if sport not in SPORTS:
            continue
        if sport in ("Gaelic Football", "Hurling"):
            sport = "Gaelic Sports"
        event_name = tip.get("event") or key_name or ""
        event_id = tip.get("event_id")
        off = OFFICIAL.get(str(event_id)) if event_id else None
        fixture = {
            "sport": sport,
            "competition": tip.get("competition") or "",
            "id": f"olbg-{event_id or event_name}",
            "home": None,
            "away": None,
            "start_utc": start,
            "time_display": start,
            "venue": tip.get("venue") or "",
            "olbg_event_id": event_id,
            "olbg_event_url": tip.get("event_url") or "",
            "market": tip.get("market") or "",
            "olbg_selection": tip.get("selection") or "",
            "official_source_url": off["official_source_url"] if off else "",
            "stats_source_url": off["stats_source_url"] if off else "",
            "facts": off["facts"] if off else [
                {"item": "OLBG listing", "text": f"{sport}: {event_name} — {tip.get('market') or ''} selection {tip.get('selection') or ''}.", "source_key": "olbg_hub", "source_url": tip.get("event_url") or "https://www.olbg.com/betting-tips"}
            ],
            "official_match": bool(off),
            "status": "originated" if off else "blank",
            "note": "" if off else "No official governing-body fixture page captured for this OLBG-listed event; values left blank and flagged for review.",
        }
        if " v " in event_name:
            fixture["home"], fixture["away"] = event_name.split(" v ", 1)
        elif " vs " in event_name:
            fixture["home"], fixture["away"] = event_name.split(" vs ", 1)
        elif " @ " in event_name:
            fixture["home"], fixture["away"] = event_name.split(" @ ", 1)
        else:
            fixture["home"] = event_name
        fixtures.append(fixture)

    for m in EXTRA_FIXTURES:
        m.setdefault("id", f"extra-{m['sport']}-{m['home']}-{m['start_utc']}")
        m.setdefault("olbg_event_id", None)
        m.setdefault("olbg_event_url", "")
        m.setdefault("market", "")
        m.setdefault("olbg_selection", "")
        m.setdefault("official_match", True)
        m.setdefault("status", "originated")
        m.setdefault("note", "")
    fixtures.extend(EXTRA_FIXTURES)
    fixtures.sort(key=lambda m: (m["start_utc"], m["sport"], m["id"]))

    matches = {
        "captured_utc": GENERATED,
        "session": SESSION,
        "sport_count": 15,
        "count": len(fixtures),
        "originated": sum(1 for m in fixtures if m["status"] == "originated"),
        "blank": sum(1 for m in fixtures if m["status"] == "blank"),
        "fixtures": fixtures,
    }
    with open(os.path.join(DATA, "matches.json"), "w") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)

    with open(os.path.join(DATA, "sources.json"), "w") as f:
        json.dump({"captured_utc": GENERATED, "session": SESSION, "count": len(SOURCES), "sources": SOURCES}, f, indent=2, ensure_ascii=False)

    # Capture summaries for reproducibility.
    capture_keys = {s["key"]: s for s in SOURCES}
    captures = []
    for key, src in capture_keys.items():
        captures.append({
            "key": key,
            "url": src["url"],
            "sport": src["sport"],
            "kind": src["kind"],
            "note": src["note"],
            "captured_utc": GENERATED,
            "session": SESSION,
            "status": "captured",
            "stored_as": f"captures/{key}.json",
        })
    with open(os.path.join(CAPTURES, "manifest.json"), "w") as f:
        json.dump({"captures": captures, "generated_utc": GENERATED, "session": SESSION}, f, indent=2, ensure_ascii=False)

    print(f"wrote {len(fixtures)} fixtures ({matches['originated']} originated, {matches['blank']} blank)")
    print(f"wrote {len(SOURCES)} sources")

if __name__ == "__main__":
    main()
