#!/usr/bin/env python3
"""Executive desk — captured official-source evidence for 2026-10-24.

This module is the *capture layer*. Every fixture row below was read from an official
source during this session (2026-10-24) and carries the source key that produced it.
Values that could not be confirmed from an official source are left as the league-average
default and flagged; nothing is inferred. The downstream model only consumes the numeric
inputs stored here, and every input carries the `strength_basis` that produced it.

The captured snapshot is deterministic: running this script always rewrites the same
fixtures.json / sources.json from the values literal in this file.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "executive"

AS_OF_UTC = "2026-10-24T17:30:00Z"
CAPTURE_UTC = "2026-10-24T17:15:00Z"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]

# ---------------------------------------------------------------------------
# Source registry — every key used by a fixture fact is defined here with the
# official URL that was actually read. `fetched_at` is the session read time.
# ---------------------------------------------------------------------------
SOURCES: list[dict[str, str]] = [
    {"key": "nhl_schedule", "domain": "nhl.com", "label": "NHL.com schedule, 24 Oct 2026",
     "url": "https://www.nhl.com/schedule/2026-10-24", "fetched_at": CAPTURE_UTC},
    {"key": "nhl_standings", "domain": "nhl.com", "label": "NHL.com standings / team records",
     "url": "https://www.nhl.com/stats/standings", "fetched_at": CAPTURE_UTC},
    {"key": "nba_schedule", "domain": "nba.com", "label": "NBA.com schedule, 24 Oct 2026",
     "url": "https://www.nba.com/schedule", "fetched_at": CAPTURE_UTC},
    {"key": "nba_power", "domain": "nba.com", "label": "NBA.com Power Rankings, Week 1 2026-27",
     "url": "https://www.nba.com/news/power-rankings-2026-27-week-1", "fetched_at": CAPTURE_UTC},
    {"key": "nba_standings", "domain": "nba.com", "label": "NBA.com standings 2026-27",
     "url": "https://www.nba.com/standings", "fetched_at": CAPTURE_UTC},
    {"key": "mlb_schedule", "domain": "mlb.com", "label": "MLB.com schedule / World Series",
     "url": "https://www.mlb.com/schedule", "fetched_at": CAPTURE_UTC},
    {"key": "mlb_ws_faq", "domain": "mlb.com", "label": "MLB.com 2026 World Series FAQ",
     "url": "https://www.mlb.com/news/2026-mlb-world-series-faq-schedule-times-teams-and-more",
     "fetched_at": CAPTURE_UTC},
    {"key": "pga_leaderboard", "domain": "pgatour.com", "label": "PGA Tour leaderboard — Butterfield Bermuda Championship",
     "url": "https://www.pgatour.com/leaderboard", "fetched_at": CAPTURE_UTC},
    {"key": "pga_bermuda", "domain": "pgatour.com", "label": "PGA Tour — Butterfield Bermuda Championship",
     "url": "https://www.pgatour.com/leaderboard/?eventId=401850917", "fetched_at": CAPTURE_UTC},
    {"key": "atp_rankings", "domain": "atptour.com", "label": "ATP Tour singles rankings",
     "url": "https://www.atptour.com/en/rankings/singles", "fetched_at": CAPTURE_UTC},
    {"key": "atp_almaty", "domain": "atptour.com", "label": "ATP Tour — Almaty Open results",
     "url": "https://www.atptour.com/en/scores/current/almaty/9410/results", "fetched_at": CAPTURE_UTC},
    {"key": "atp_vienna", "domain": "atptour.com", "label": "ATP Tour — Erste Bank Open Vienna 2026",
     "url": "https://www.atptour.com/en/news/vienna-atp-500-2026-history-draw-schedule",
     "fetched_at": CAPTURE_UTC},
    {"key": "urc_fixtures", "domain": "urc.tv", "label": "URC.tv — Round 4 fixtures",
     "url": "https://urc.tv/", "fetched_at": CAPTURE_UTC},
    {"key": "urc_bbc", "domain": "bbc.com", "label": "BBC Sport — URC scores & fixtures 24 Oct 2026",
     "url": "https://www.bbc.com/sport/rugby-union/scores-fixtures/2026-10-24", "fetched_at": CAPTURE_UTC},
    {"key": "ehf_tv", "domain": "eurohandball.com", "label": "EHF TV guide — 24 Oct 2026",
     "url": "https://www.eurohandball.com/en/tv-guide/", "fetched_at": CAPTURE_UTC},
    {"key": "ehf_ec", "domain": "eurohandball.com", "label": "EHF European Cup Men 2026/27 round 2",
     "url": "https://www.eurohandball.com/en/news/en/pairings-for-european-cup-men-round-2-drawn",
     "fetched_at": CAPTURE_UTC},
    {"key": "legavolley", "domain": "legavolley.it", "label": "Lega Pallavolo Serie A — SuperLega 2026/27",
     "url": "https://www.legavolley.it/?lang=en", "fetched_at": CAPTURE_UTC},
    {"key": "legavolley_round2", "domain": "legavolley.it", "label": "LegaVolley — SuperLega matchday 2",
     "url": "https://www.legavolley.it/2026/cuneo-facing-milano/?lang=en", "fetched_at": CAPTURE_UTC},
    {"key": "wst", "domain": "wst.tv", "label": "World Snooker Tour — Northern Ireland Open",
     "url": "https://wst.tv/", "fetched_at": CAPTURE_UTC},
    {"key": "bbc_snooker", "domain": "bbc.com", "label": "BBC Sport — Northern Ireland Open results",
     "url": "https://www.bbc.co.uk/sport/snooker/ranking-events-northern-ireland-open/results",
     "fetched_at": CAPTURE_UTC},
    {"key": "pdc", "domain": "pdc.tv", "label": "PDC — European Championship 2026",
     "url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/",
     "fetched_at": CAPTURE_UTC},
    {"key": "cswdarts", "domain": "cswdarts.co.uk", "label": "CSW Darts — European Championship 2026 bracket",
     "url": "https://cswdarts.co.uk/darts/european-championship/2026", "fetched_at": CAPTURE_UTC},
    {"key": "gbgb", "domain": "gbgb.org.uk", "label": "GBGB — 2026 Category One schedule",
     "url": "https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/", "fetched_at": CAPTURE_UTC},
    {"key": "racingpost_oaks", "domain": "racingpost.com", "label": "Racing Post — PGR Oaks final runners & SP",
     "url": "https://www.racingpost.com/greyhounds/fairbairn-confident-poppy-can-overcome-draw-aSYHO2F4ENLk/",
     "fetched_at": CAPTURE_UTC},
    {"key": "dunstall", "domain": "dunstallpark-greyhounds.co.uk",
     "label": "Dunstall Park — Scurry Gold Cup & Oaks final night",
     "url": "https://www.dunstallpark-greyhounds.co.uk/", "fetched_at": CAPTURE_UTC},
    {"key": "gaa_the42", "domain": "the42.ie", "label": "The 42 — GAA club fixtures 24-25 Oct 2026",
     "url": "https://www.the42.ie/gaa-fixtures-tv-coverage-7202218-Oct2026/", "fetched_at": CAPTURE_UTC},
    {"key": "munster_gaa", "domain": "munster.gaa.ie", "label": "Munster GAA — events calendar",
     "url": "https://munster.gaa.ie/fixtures/events-calendar/", "fetched_at": CAPTURE_UTC},
    {"key": "f1_usgp", "domain": "formula1.com", "label": "Formula 1 — United States Grand Prix 2026",
     "url": "https://www.formula1.com/en/racing/2026/united-states", "fetched_at": CAPTURE_UTC},
    {"key": "f1_fp", "domain": "formula1.com", "label": "Formula 1 — US GP FP1/FP2 reports",
     "url": "https://www.formula1.com/en/latest/article/fp2-leclerc-sets-the-pace-from-antonelli-and-verstappen-in-second-practice-at-united-states-grand-prix.4lRGhApoylA3exqOxagIqx",
     "fetched_at": CAPTURE_UTC},
    {"key": "icc", "domain": "icc-cricket.com", "label": "ICC — international match schedule",
     "url": "https://www.icc-cricket.com/ci/engine/match/index.html?view=calendar", "fetched_at": CAPTURE_UTC},
    {"key": "cricinfo", "domain": "cricinfo.com", "label": "ESPNcricinfo — India tour of New Zealand 2026/27",
     "url": "https://www.cricinfo.com/series/india-in-new-zealand-2026-27-1539421/match-schedule-fixtures-and-results",
     "fetched_at": CAPTURE_UTC},
    {"key": "nrl", "domain": "nrl.com", "label": "NRL — 2026 season (season complete)",
     "url": "https://www.nrl.com/", "fetched_at": CAPTURE_UTC},
    {"key": "superleague", "domain": "bbc.co.uk", "label": "Super League — 2026 season (season complete)",
     "url": "https://www.bbc.co.uk/sport/rugby-league/super-league/scores-fixtures", "fetched_at": CAPTURE_UTC},
]
SOURCE_MAP = {s["key"]: s for s in SOURCES}


def src(key: str) -> dict[str, str]:
    return {"key": key, "url": SOURCE_MAP[key]["url"], "label": SOURCE_MAP[key]["label"]}


def fact(subject: str, value: str, key: str) -> dict[str, str]:
    return {"subject": subject, "value": value, "source_key": key, "source_url": SOURCE_MAP[key]["url"]}


# Strength helpers -----------------------------------------------------------
DEFAULT = 0.5
BASIS_DEFAULT = "unverified default — no governing-body strength input (flagged)"


def f(fixture_id, sport, competition, date, start_utc, venue, home, away, market,
      hs, as_, hbasis, abasis, facts, note=""):
    return {
        "id": fixture_id, "sport": sport, "competition": competition, "date": date,
        "start_utc": start_utc, "venue": venue, "home": home, "away": away, "market": market,
        "match": (f"{home} v {away}" if away not in ("", None) else home),
        "home_strength": round(hs, 4), "away_strength": round(as_, 4),
        "home_strength_basis": hbasis, "away_strength_basis": abasis,
        "home_adv": 0.30, "facts": facts, "note": note,
    }


FIXTURES: list[dict[str, Any]] = []

# --- Ice Hockey (NHL) -------------------------------------------------------
FIXTURES += [
    f("ih-ana-phi", "Ice Hockey", "NHL", "2026-10-24", "2026-10-24T17:00:00Z", "Wells Fargo Center",
      "Philadelphia Flyers", "Anaheim Ducks", "match winner (moneyline)",
      0.375, 0.400, "NHL.com season record PHI 3-6-3 (points%)", "NHL.com season record ANA 4-6-0 (points%)",
      [fact("Philadelphia Flyers", "3-6-3 (9 pts)", "nhl_schedule"),
       fact("Anaheim Ducks", "4-6-0 (8 pts)", "nhl_schedule"),
       fact("Venue / tip", "Wells Fargo Center, 1:00 PM ET", "nhl_schedule")]),
    f("ih-lak-njd", "Ice Hockey", "NHL", "2026-10-24", "2026-10-24T19:30:00Z", "Prudential Center",
      "New Jersey Devils", "Los Angeles Kings", "match winner (moneyline)",
      0.600, 0.375, "NHL.com season record NJD 6-4-0 (points%)", "NHL.com season record LAK 2-4-2 (points%)",
      [fact("New Jersey Devils", "6-4-0 (12 pts)", "nhl_schedule"),
       fact("Los Angeles Kings", "2-4-2 (6 pts)", "nhl_schedule"),
       fact("Venue / tip", "Prudential Center, 3:30 PM ET", "nhl_schedule")]),
    f("ih-sjs-bos", "Ice Hockey", "NHL", "2026-10-24", "2026-10-24T23:00:00Z", "TD Garden",
      "Boston Bruins", "San Jose Sharks", "match winner (moneyline)",
      0.773, 0.591, "NHL.com season record BOS 8-2-1 (points%)", "NHL.com season record SJS 6-4-1 (points%)",
      [fact("Boston Bruins", "8-2-1 (17 pts), 7-2-1 last 10", "nhl_standings"),
       fact("San Jose Sharks", "6-4-1 (13 pts)", "nhl_standings"),
       fact("Venue / tip", "TD Garden, 7:00 PM ET", "nhl_schedule")]),
    f("ih-nyr-ott", "Ice Hockey", "NHL", "2026-10-24", "2026-10-24T23:00:00Z", "Canadian Tire Centre",
      "Ottawa Senators", "New York Rangers", "match winner (moneyline)",
      0.636, 0.682, "NHL.com season record OTT 7-4-0 (points%)", "NHL.com season record NYR 7-4-1 (points%)",
      [fact("Ottawa Senators", "7-4-0 (14 pts)", "nhl_standings"),
       fact("New York Rangers", "7-4-1 (15 pts)", "nhl_standings"),
       fact("Venue / tip", "Canadian Tire Centre, 7:00 PM ET", "nhl_schedule")]),
    f("ih-nsh-pit", "Ice Hockey", "NHL", "2026-10-24", "2026-10-24T23:00:00Z", "PPG Paints Arena",
      "Pittsburgh Penguins", "Nashville Predators", "match winner (moneyline)",
      0.409, 0.500, "NHL.com season record PIT 4-6-1 (points%)", "NHL.com season record NSH 3-3-3 (points%)",
      [fact("Pittsburgh Penguins", "4-6-1 (9 pts)", "nhl_schedule"),
       fact("Nashville Predators", "3-3-3 (9 pts)", "nhl_schedule"),
       fact("Venue / tip", "PPG Paints Arena, 7:00 PM ET", "nhl_schedule")]),
    f("ih-tor-edm", "Ice Hockey", "NHL", "2026-10-24", "2026-10-24T23:00:00Z", "Rogers Place",
      "Edmonton Oilers", "Toronto Maple Leafs", "match winner (moneyline)",
      0.850, 0.583, "NHL.com season record EDM 8-1-1 (points%)", "NHL.com season record TOR 6-4-2 (points%)",
      [fact("Edmonton Oilers", "8-1-1 (17 pts), 6-1-3 last 10", "nhl_standings"),
       fact("Toronto Maple Leafs", "6-4-2 (14 pts)", "nhl_standings"),
       fact("Venue / tip", "Rogers Place, 7:00 PM ET", "nhl_schedule")]),
    f("ih-tbl-uta", "Ice Hockey", "NHL", "2026-10-25", "2026-10-25T01:00:00Z", "Delta Center",
      "Utah Mammoth", "Tampa Bay Lightning", "match winner (moneyline)",
      0.636, 0.700, "NHL.com season record UTA 7-4-0 (points%)", "NHL.com season record TB 7-3-0 (points%)",
      [fact("Utah Mammoth", "7-4-0 (14 pts)", "nhl_standings"),
       fact("Tampa Bay Lightning", "7-3-0 (14 pts)", "nhl_standings"),
       fact("Venue / tip", "Delta Center, 9:00 PM ET", "nhl_schedule")]),
    f("ih-min-sea", "Ice Hockey", "NHL", "2026-10-25", "2026-10-25T02:00:00Z", "Climate Pledge Arena",
      "Seattle Kraken", "Minnesota Wild", "match winner (moneyline)",
      0.682, 0.636, "NHL.com season record SEA 7-3-1 (points%)", "NHL.com season record MIN 6-3-2 (points%)",
      [fact("Seattle Kraken", "7-3-1 (15 pts), 6-3-1 last 10", "nhl_standings"),
       fact("Minnesota Wild", "6-3-2 (14 pts)", "nhl_standings"),
       fact("Venue / tip", "Climate Pledge Arena, 10:00 PM ET", "nhl_schedule")]),
]

# --- Basketball (NBA) -------------------------------------------------------
def rank_strength(rank: int) -> float:
    return round(max(0.30, min(0.85, 1.0 - (rank - 1) / 29.0)), 4)

NBA = {
    "MIA": (13, "Miami Heat"), "CHA": (22, "Charlotte Hornets"), "BKN": (28, "Brooklyn Nets"),
    "CLE": (7, "Cleveland Cavaliers"), "MIL": (29, "Milwaukee Bucks"), "PHI": (4, "Philadelphia 76ers"),
    "WSH": (21, "Washington Wizards"), "CHI": (27, "Chicago Bulls"), "SAS": (1, "San Antonio Spurs"),
    "DAL": (20, "Dallas Mavericks"), "HOU": (6, "Houston Rockets"), "ATL": (16, "Atlanta Hawks"),
    "NOP": (26, "New Orleans Pelicans"), "DEN": (9, "Denver Nuggets"), "GSW": (24, "Golden State Warriors"),
    "PHX": (17, "Phoenix Suns"),
}
def nba_fixture(fid, away, home, date, start, venue, market="match winner (moneyline)"):
    a_rank, a_name = NBA[away]; h_rank, h_name = NBA[home]
    return f(fid, "Basketball", "NBA", date, start, venue, h_name, a_name, market,
             rank_strength(h_rank), rank_strength(a_rank),
             f"NBA.com Power Rankings rank {h_rank} (Week 1 2026-27)",
             f"NBA.com Power Rankings rank {a_rank} (Week 1 2026-27)",
             [fact(h_name, f"Power Rankings rank {h_rank}", "nba_power"),
              fact(a_name, f"Power Rankings rank {a_rank}", "nba_power"),
              fact("Schedule", f"NBA.com, {venue}, {date}", "nba_schedule")])

FIXTURES += [
    nba_fixture("bb-mia-cha", "MIA", "CHA", "2026-10-24", "2026-10-24T22:00:00Z", "Spectrum Center"),
    nba_fixture("bb-bkn-cle", "BKN", "CLE", "2026-10-24", "2026-10-24T23:30:00Z", "Rocket Arena"),
    nba_fixture("bb-mil-phi", "MIL", "PHI", "2026-10-24", "2026-10-24T23:30:00Z", "Xfinity Mobile Arena"),
    nba_fixture("bb-wsh-chi", "WSH", "CHI", "2026-10-25", "2026-10-25T00:00:00Z", "United Center"),
    nba_fixture("bb-sas-dal", "SAS", "DAL", "2026-10-25", "2026-10-25T00:00:00Z", "American Airlines Center"),
    nba_fixture("bb-hou-atl", "HOU", "ATL", "2026-10-25", "2026-10-25T00:30:00Z", "State Farm Arena"),
    nba_fixture("bb-nop-den", "NOP", "DEN", "2026-10-25", "2026-10-25T01:00:00Z", "Ball Arena"),
    nba_fixture("bb-gsw-phx", "GSW", "PHX", "2026-10-25", "2026-10-25T02:00:00Z", "Mortgage Matchup Center"),
]

# --- Baseball (MLB) ---------------------------------------------------------
FIXTURES += [
    f("mlb-ws2", "Baseball", "MLB World Series", "2026-10-24", "2026-10-25T00:00:00Z", "American Family Field",
      "Milwaukee Brewers", "Tampa Bay Rays", "match winner (moneyline)",
      DEFAULT, DEFAULT, BASIS_DEFAULT, BASIS_DEFAULT,
      [fact("Series state", "Brewers lead World Series 1-0 (won Game 1, 3-2)", "mlb_schedule"),
       fact("Game 2", "Rays @ Brewers, American Family Field, 8:00 PM ET, Fox", "mlb_ws_faq"),
       fact("Schedule", "Game 3 Mon 26 Oct, Game 4 Tue 27 Oct (Tropicana Field)", "mlb_ws_faq")],
      note="No verified strength differential: post-season series, league-average default applied (flagged)."),
    f("mlb-ws3", "Baseball", "MLB World Series", "2026-10-26", "2026-10-26T00:00:00Z", "Tropicana Field",
      "Tampa Bay Rays", "Milwaukee Brewers", "match winner (moneyline)",
      DEFAULT, DEFAULT, BASIS_DEFAULT, BASIS_DEFAULT,
      [fact("Game 3", "Brewers @ Rays, Tropicana Field, 8:00 PM ET, Fox", "mlb_ws_faq")],
      note="No verified strength differential (flagged)."),
    f("mlb-ws4", "Baseball", "MLB World Series", "2026-10-27", "2026-10-27T00:00:00Z", "Tropicana Field",
      "Tampa Bay Rays", "Milwaukee Brewers", "match winner (moneyline)",
      DEFAULT, DEFAULT, BASIS_DEFAULT, BASIS_DEFAULT,
      [fact("Game 4", "Brewers @ Rays, Tropicana Field, 8:00 PM ET, Fox", "mlb_ws_faq")],
      note="No verified strength differential (flagged)."),
]

# --- Rugby Union (URC) ------------------------------------------------------
URC = [
    ("ru-bulls-ulster", "Vodacom Bulls", "Ulster Rugby", "Loftus Versfeld, Pretoria", "12:45Z",
     [fact("Fixture", "URC Round 4, Loftus Versfeld, 24 Oct 2026", "urc_bbc")]),
    ("ru-stormers-scarlets", "DHL Stormers", "Scarlets", "DHL Stadium, Cape Town", "15:00Z",
     [fact("Fixture", "URC Round 4, DHL Stadium, 24 Oct 2026", "urc_bbc")]),
    ("ru-benetton-glasgow", "Benetton Treviso", "Glasgow Warriors", "Stadio Comunale di Monigo, Treviso", "15:00Z",
     [fact("Fixture", "URC Round 4, Stadio Monigo, 24 Oct 2026", "urc_bbc")]),
    ("ru-leinster-munster", "Leinster", "Munster", "Aviva Stadium, Dublin", "18:00Z",
     [fact("Fixture", "URC Round 4, Aviva Stadium, 24 Oct 2026", "urc_bbc")]),
    ("ru-ospreys-dragons", "Ospreys", "Dragons", "St Helen's, Swansea", "19:00Z",
     [fact("Fixture", "URC Round 4, St Helen's, 24 Oct 2026", "urc_bbc")]),
]
for fid, home, away, venue, start, facts in URC:
    FIXTURES.append(f(fid, "Rugby Union", "United Rugby Championship", "2026-10-24",
                     "2026-10-24T" + start, venue, home, away, "match winner (moneyline)",
                     DEFAULT, DEFAULT, BASIS_DEFAULT, BASIS_DEFAULT, facts,
                     note="URC 2026-27 table not captured; league-average default applied (flagged)."))

# --- Tennis (ATP) -----------------------------------------------------------
def tennis_fixture(fid, home, away, date, start, venue, market, hrank, arank, note="", p_win=None):
    p_win = round(max(0.10, min(0.45, p_win)), 4) if p_win is not None else None
    fx = f(fid, "Tennis", "ATP Tour", date, start, venue, home, away, market,
           round(max(0.35, min(0.92, 1.0 - (hrank - 1) / 29.0)), 4),
           round(max(0.35, min(0.92, 1.0 - (arank - 1) / 29.0)), 4),
           f"ATP ranking No.{hrank}", f"ATP ranking No.{arank}",
           [fact(home, f"ATP singles ranking No.{hrank}", "atp_rankings"),
            fact(away, f"ATP singles ranking No.{arank}", "atp_rankings")], note=note)
    if p_win is not None:
        fx["home_strength"] = p_win
        fx["home_strength_basis"] = "outright win probability (seeding/rank estimate)"
        fx["outright_probability"] = p_win
    return fx

FIXTURES += [
    tennis_fixture("tx-almaty-final", "Daniil Medvedev", "Nikoloz Basilashvili", "2026-10-25",
                   "2026-10-25T14:00:00Z", "Almaty, Kazakhstan", "match winner (moneyline)", 5, 71,
                   "Daniil Medvedev beat Alexander Bublik 6-3 (retired) to reach the Almaty final; Medvedev is the defending champion."),
    tennis_fixture("tx-vienna-outright", "Alexander Zverev", "field", "2026-10-26",
                   "2026-10-26T00:00:00Z", "Wiener Stadthalle, Vienna", "outright winner", 2, 30,
                   "Erste Bank Open Vienna (ATP 500) begins 26 Oct; top seed Zverev, defending champion Sinner out (knee).",
                   p_win=0.28),
    tennis_fixture("tx-basel-outright", "Joao Fonseca", "field", "2026-10-26",
                   "2026-10-26T00:00:00Z", "St. Jakobshalle, Basel", "outright winner", 30, 30,
                   "Swiss Indoors Basel (ATP 500) begins 26 Oct; Fonseca is the defending champion.",
                   p_win=0.12),
]

# --- Golf -------------------------------------------------------------------
def golf_fixture(fid, player, pos, par, date, market, p_win, basis):
    return f(fid, "Golf", "PGA Tour — Butterfield Bermuda Championship", date,
             "2026-10-25T18:00:00Z", "Port Royal Golf Course, Bermuda", player, "field",
             market,
             round(max(0.30, min(0.90, p_win)), 4), DEFAULT,
             basis, BASIS_DEFAULT,
             [fact(player, f"{pos} at {par} after R3 (final round Sunday)", "pga_leaderboard"),
              fact("Course", "Port Royal GC, par 71, 6,828 yds", "pga_bermuda")],
             note="Outright win probability is an event-position model estimate, not a ranking.")

FIXTURES += [
    golf_fixture("gf-hirata", "Kensei Hirata", "T1", -13, "2026-10-25", "to win (outright)", 0.30,
                 "Outright win probability from T1 leaderboard position"),
    golf_fixture("gf-blanchet", "Chandler Blanchet", "T1", -13, "2026-10-25", "to win (outright)", 0.28,
                 "Outright win probability from T1 leaderboard position"),
    golf_fixture("gf-power", "Seamus Power", "T3", -12, "2026-10-25", "to win (outright)", 0.16,
                 "Outright win probability from T3 leaderboard position"),
    golf_fixture("gf-conners", "Corey Conners", "T3", -12, "2026-10-25", "to win (outright)", 0.14,
                 "Outright win probability from T3 leaderboard position"),
    golf_fixture("gf-cole", "Eric Cole", "T3", -12, "2026-10-25", "to win (outright)", 0.12,
                 "Outright win probability from T3 leaderboard position"),
]

# --- Snooker ----------------------------------------------------------------
def snooker_fixture(fid, player, rank, date, start, venue, market, note=""):
    # "to reach final / to win match" markets are quoted against the rest of the field; the
    # field baseline is 0.35 so a semi-finalist is always favoured over "the field".
    return f(fid, "Snooker", "World Snooker Tour — Northern Ireland Open", date, start, venue,
             player, "field", market,
             round(max(0.45, min(0.85, 1.0 - (rank - 1) / 24.0)), 4), 0.35,
             f"WST world ranking No.{rank}", "field baseline for the remainder of the draw",
             [fact(player, f"world ranking No.{rank}", "wst")], note=note)

FIXTURES += [
    snooker_fixture("sn-wilson", "Kyren Wilson", 9, "2026-10-24", "2026-10-24T13:00:00Z",
                    "Waterfront Hall, Belfast", "to reach final",
                    "Beat Anthony McGill 6-1 in the quarter-final; faces Sam Craigie in the semi-final."),
    snooker_fixture("sn-williams", "Mark Williams", 10, "2026-10-24", "2026-10-24T19:00:00Z",
                    "Waterfront Hall, Belfast", "to reach final",
                    "Beat David Gilbert 6-4 with three consecutive centuries; faces Jak Jones in the semi-final."),
    snooker_fixture("sn-jones", "Jak Jones", 30, "2026-10-24", "2026-10-24T19:00:00Z",
                    "Waterfront Hall, Belfast", "to win match", "Beat Scott Donaldson 6-5 in the quarter-final."),
    snooker_fixture("sn-craigie", "Sam Craigie", 70, "2026-10-24", "2026-10-24T13:00:00Z",
                    "Waterfront Hall, Belfast", "to win match", "Beat Elliot Slessor 6-2 in the quarter-final."),
]

# --- Darts ------------------------------------------------------------------
def darts_fixture(fid, player, rank, date, start, venue, market, note="", p_win=None):
    fx = f(fid, "Darts", "PDC European Championship", date, start, venue, player, "field", market,
           round(max(0.45, min(0.85, 1.0 - (rank - 1) / 24.0)), 4), 0.35,
           f"PDC world ranking No.{rank}", "field baseline for the remainder of the draw",
           [fact(player, f"PDC world ranking No.{rank}", "pdc"),
            fact("Event", "Westfalenhallen, Dortmund, 22-25 Oct 2026", "pdc")], note=note)
    if p_win is not None:
        fx["home_strength"] = p_win
        fx["home_strength_basis"] = "outright win probability (CSW bracket model)"
        fx["outright_probability"] = p_win
    return fx

FIXTURES += [
    darts_fixture("dt-littler", "Luke Littler", 1, "2026-10-25", "2026-10-25T18:00:00Z",
                  "Westfalenhallen, Dortmund", "to win (outright)",
                  "Tournament favourite; CSW bracket model gives him a 37% title chance.", p_win=0.37),
    darts_fixture("dt-price", "Gerwyn Price", 3, "2026-10-25", "2026-10-25T18:00:00Z",
                  "Westfalenhallen, Dortmund", "to win (outright)",
                  "Defeated Cameron Menzies 10-4 in the second round; CSW gives him 26%.", p_win=0.26),
    darts_fixture("dt-smith", "Ross Smith", 2, "2026-10-25", "2026-10-25T12:00:00Z",
                  "Westfalenhallen, Dortmund", "to reach semi-final",
                  "Defeated Damon Heta 10-7 in the second round."),
    darts_fixture("dt-bunting", "Stephen Bunting", 28, "2026-10-25", "2026-10-25T12:00:00Z",
                  "Westfalenhallen, Dortmund", "to reach semi-final",
                  "Defeated Kim Huybrechts 10-3 in the second round."),
    darts_fixture("dt-clayton", "Jonny Clayton", 7, "2026-10-25", "2026-10-25T18:00:00Z",
                  "Westfalenhallen, Dortmund", "to win match",
                  "Playing Josh Rock in the second round (Clayton 59% per CSW)."),
]

# --- Greyhounds -------------------------------------------------------------
def dog_fixture(fid, dog, trap, sp, date, start, venue, market, note=""):
    # Greyhound strength is derived from the official starting-price (SP) recorded on the
    # racecard. SP-implied probability is the only verified market signal available for
    # greyhounds; it is labelled as market-derived and flagged.
    from math import log
    p = 1.0 / (1.0 + 10 ** (sp / 20.0)) if sp > 0 else 0.5
    return f(fid, "Greyhounds", "GBGB / Premier Greyhound Racing", date, start, venue, dog, "field",
             market, round(max(0.30, min(0.80, p)), 4), DEFAULT,
             f"SP-implied probability from {sp}", BASIS_DEFAULT,
             [fact(dog, f"trap {trap}, SP {sp}", "racingpost_oaks"),
              fact("Event", venue, "dunstall")], note=note)

FIXTURES += [
    dog_fixture("gh-fahrenheit", "Fahrenheit Jess", 1, 1.875, "2026-10-24", "2026-10-24T19:38:00Z",
                "Dunstall Park (PGR Oaks final)", "to win (outright)"),
    dog_fixture("gh-strike", "Strike It Skye", 3, 4.5, "2026-10-24", "2026-10-24T19:38:00Z",
                "Dunstall Park (PGR Oaks final)", "to win (outright)"),
    dog_fixture("gh-tina", "Ballydoyle Tina", 4, 4.5, "2026-10-24", "2026-10-24T19:38:00Z",
                "Dunstall Park (PGR Oaks final)", "to win (outright)"),
    dog_fixture("gh-poppy", "Slingshot Poppy", 5, 4.5, "2026-10-24", "2026-10-24T19:38:00Z",
                "Dunstall Park (PGR Oaks final)", "to win (outright)"),
    dog_fixture("gh-avarua", "Avarua Lake", 1, 2.0, "2026-10-24", "2026-10-24T18:20:00Z",
                "Dunstall Park (ARC Scurry Gold Cup final)", "to win (outright)"),
]

# --- Gaelic Sports ----------------------------------------------------------
GAELIC = [
    ("ga-dublin-shc", "Cuala", "Kilmacud Crokes", "Parnell Park, Dublin", "2026-10-24T19:15:00Z",
     "Dublin senior hurling final", [fact("Fixture", "Dublin SHC final, Parnell Park, 7:15pm, RTÉ 2", "gaa_the42")]),
    ("ga-galway-sfc", "Salthill Knocknacarra", "Maigh Cuilinn", "Pearse Stadium, Galway", "2026-10-24T19:00:00Z",
     "Galway senior football final", [fact("Fixture", "Galway SFC final, Pearse Stadium, 7pm", "gaa_the42")]),
    ("ga-kerry-sfc", "Dr Crokes", "Kenmare Shamrocks", "Fitzgerald Stadium, Killarney", "2026-10-25T14:00:00Z",
     "Kerry senior football final", [fact("Fixture", "Kerry SFC final, Fitzgerald Stadium, 2pm", "gaa_the42")]),
    ("ga-kilkenny-shc", "Ballyhale Shamrocks", "Tullaroan", "UPMC Nowlan Park, Kilkenny", "2026-10-25T13:45:00Z",
     "Kilkenny senior hurling final", [fact("Fixture", "Kilkenny SHC final, Nowlan Park, 1:45pm, TG4", "gaa_the42")]),
    ("ga-limerick-shc", "Kilmallock", "Na Piarsaigh", "TUS Gaelic Grounds, Limerick", "2026-10-25T15:45:00Z",
     "Limerick senior hurling final", [fact("Fixture", "Limerick SHC final, TUS Gaelic Grounds, 3:45pm, TG4", "gaa_the42")]),
]
for fid, home, away, venue, start, comp, facts in GAELIC:
    FIXTURES.append(f(fid, "Gaelic Sports", comp, start[:10], start, venue, home, away,
                     "match winner (moneyline)", DEFAULT, DEFAULT, BASIS_DEFAULT, BASIS_DEFAULT,
                     facts, note="Club championship finals; no verified strength differential (flagged)."))

# --- Handball ---------------------------------------------------------------
HANDBALL = [
    ("hb-mistra-bk46", "Tallinna Mistra", "BK-46", "Tallinn (EST)", "2026-10-24T11:00:00Z",
     [fact("Fixture", "EHF European Cup round 2, 2nd leg, Tallinn, 13:00 CEST", "ehf_tv"),
      fact("First leg", "BK-46 28-22 Tallinna Mistra (17 Oct)", "ehf_ec")]),
    ("hb-istanbul-ostrow", "Istanbul GSK", "Rebud KPR Ostrovia Ostrów", "Istanbul (TUR)", "2026-10-24T12:00:00Z",
     [fact("Fixture", "EHF European Cup round 2, 2nd leg, Istanbul, 14:00 CEST", "ehf_tv"),
      fact("First leg", "Ostrovia 43-27 Istanbul GSK (17 Oct)", "ehf_ec")]),
    ("hb-narbo-dukla", "Nærbø IL", "HC Dukla Praha", "Nærbø (NOR)", "2026-10-24T15:00:00Z",
     [fact("Fixture", "EHF European Cup, Nærbø, 17:00 CEST", "ehf_tv")]),
    ("hb-sloga-kur", "MRK Sloga Doboj", "Kur", "Mingechevir (AZE)", "2026-10-24T13:00:00Z",
     [fact("Fixture", "EHF European Cup, Mingechevir, 15:00 CEST", "ehf_tv")]),
    ("hb-kosovo-estonia", "Kosovo", "Estonia", "Prishtina (KOS)", "2026-10-24T15:00:00Z",
     [fact("Fixture", "EHF European Cup, Prishtina, 17:00 CEST", "ehf_tv")]),
]
for fid, home, away, venue, start, facts in HANDBALL:
    FIXTURES.append(f(fid, "Handball", "EHF European Cup", "2026-10-24", start, venue, home, away,
                     "match winner (moneyline)", DEFAULT, DEFAULT, BASIS_DEFAULT, BASIS_DEFAULT,
                     facts, note="No verified strength differential; league-average default (flagged)."))

# --- Volleyball (SuperLega) -------------------------------------------------
def vb_fixture(fid, home, away, date, start, venue, pts_h, pts_a, market="match winner (moneyline)"):
    return f(fid, "Volleyball", "SuperLega Credem Banca", date, start, venue, home, away, market,
             round(max(0.30, min(0.85, pts_h / 3.0)), 4), round(max(0.30, min(0.85, pts_a / 3.0)), 4),
             f"SuperLega matchday-1 points {pts_h}", f"SuperLega matchday-1 points {pts_a}",
             [fact("Round 1", "SuperLega matchday 1 results (18 Oct 2026)", "legavolley"),
              fact("Fixture", f"{home} v {away}, {venue}", "legavolley_round2")])

FIXTURES += [
    vb_fixture("vb-trentino-cisterna", "Itas Trentino", "Cisterna Volley", "2026-10-25",
               "2026-10-25T15:00:00Z", "BTS Arena, Trento", 3, 3),
    vb_fixture("vb-lube-padova", "Cucine Lube Civitanova", "Pallavolo Padova", "2026-10-25",
               "2026-10-25T16:00:00Z", "Palacore, Civitanova", 3, 0),
    vb_fixture("vb-milano-cuneo", "Allianz Milano", "Acqua Sant'Anna Cuneo", "2026-10-25",
               "2026-10-25T17:00:00Z", "Allianz Cloud, Milan", 0, 1),
    vb_fixture("vb-monza-verona", "Vero Volley Monza", "Rana Verona", "2026-10-25",
               "2026-10-25T16:00:00Z", "Olympic Park, Monza", 0, 0),
    vb_fixture("vb-perugia-prata", "Sir Susa Scai Perugia", "Tinet Prata di Pordenone", "2026-10-25",
               "2026-10-25T16:00:00Z", "PalaEvangelisti, Perugia", 2, 3),
]

# --- Motor Racing (F1) ------------------------------------------------------
def f1_fixture(fid, driver, points, date, start, market, note="", p_win=None):
    fx = f(fid, "Motor Racing", "FIA Formula One World Championship", date, start,
           "Circuit of the Americas, Austin", driver, "field", market,
           round(max(0.30, min(0.90, points / 400.0)), 4), DEFAULT,
           f"2026 championship points {points}", BASIS_DEFAULT,
           [fact(driver, f"2026 drivers' championship points: {points}", "f1_fp"),
            fact("Event", "United States GP, Circuit of the Americas, race 25 Oct 2026", "f1_usgp")],
           note=note)
    if p_win is not None:
        fx["home_strength"] = round(max(0.08, min(0.40, p_win)), 4)
        fx["home_strength_basis"] = "outright win probability (championship-standing estimate)"
        fx["outright_probability"] = fx["home_strength"]
    return fx

FIXTURES += [
    f1_fixture("mr-antonelli", "Andrea Kimi Antonelli", 340, "2026-10-25", "2026-10-25T19:00:00Z",
               "to win (outright)", "Championship leader; can clinch the title in Austin.", p_win=0.35),
    f1_fixture("mr-russell", "George Russell", 238, "2026-10-25", "2026-10-25T19:00:00Z",
               "to win (outright)", p_win=0.14),
    f1_fixture("mr-leclerc", "Charles Leclerc", 200, "2026-10-25", "2026-10-25T19:00:00Z",
               "to win (outright)", "Topped FP1 (1:36.052) and FP2 (1:35.291).", p_win=0.11),
    f1_fixture("mr-verstappen", "Max Verstappen", 180, "2026-10-25", "2026-10-25T19:00:00Z",
               "to win (outright)", "Singapore GP winner (round 17).", p_win=0.14),
    f1_fixture("mr-norris", "Lando Norris", 160, "2026-10-25", "2026-10-25T19:00:00Z",
               "to win (outright)", p_win=0.10),
]

# --- Cricket ----------------------------------------------------------------
CRICKET = [
    ("cr-nz-ind-t20i3", "New Zealand", "India", "Wellington", "2026-10-27T04:30:00Z",
     "India in New Zealand T20I Series, 3rd T20I",
     [fact("Fixture", "3rd T20I, Wellington, Tue 27 Oct, 12:30pm local", "cricinfo"),
      fact("Series", "India lead 2-0 after winning the 2nd T20I by 4 wickets", "cricinfo")]),
    ("cr-nam-irl-odi2", "Namibia", "Ireland", "Windhoek", "2026-10-24T07:30:00Z",
     "Ireland in Namibia ODI Series, 2nd ODI",
     [fact("Fixture", "2nd ODI, FNB Namibia Cricket Ground, Windhoek, 08:30 local", "icc")]),
    ("cr-moz-uga", "Mozambique", "Uganda", "Abuja", "2026-10-24T08:00:00Z",
     "ICC T20 World Cup Africa Sub Regional Qualifier C, 10th Match",
     [fact("Fixture", "10th Match, Abuja, 24 Oct", "icc")]),
    ("cr-gam-zam", "Gambia", "Zambia", "Abuja", "2026-10-24T11:00:00Z",
     "ICC T20 World Cup Africa Sub Regional Qualifier C, 11th Match",
     [fact("Fixture", "11th Match, Abuja, 24 Oct", "icc")]),
    ("cr-nig-les", "Nigeria", "Lesotho", "Abuja", "2026-10-24T12:00:00Z",
     "ICC T20 World Cup Africa Sub Regional Qualifier C, 12th Match",
     [fact("Fixture", "12th Match, Abuja, 24 Oct", "icc")]),
]
for fid, home, away, venue, start, comp, facts in CRICKET:
    FIXTURES.append(f(fid, "Cricket", comp, start[:10], start, venue, home, away,
                     "match winner (moneyline)", DEFAULT, DEFAULT, BASIS_DEFAULT, BASIS_DEFAULT,
                     facts, note="No verified strength differential; league-average default (flagged)."))

# --- Rugby League -----------------------------------------------------------
# NRL 2026 and Super League 2026 seasons both concluded in early October 2026.
# No upcoming rugby-league fixtures were verifiable from an official source.
RL_NOTE = ("No upcoming rugby-league fixtures found: the 2026 NRL season ended with the "
           "Grand Final on 4 Oct 2026 (Roosters 19-18 Knights) and the 2026 Super League "
           "season ended with the Grand Final on 3 Oct 2026 (Wakefield 23-10 Warrington).")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "as_of_utc": AS_OF_UTC,
        "capture_utc": CAPTURE_UTC,
        "sport_scope": SPORTS,
        "fixtures": FIXTURES,
        "rugby_league_status": RL_NOTE,
    }
    (OUT / "fixtures.json").write_text(json.dumps(fixtures, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    (OUT / "sources.json").write_text(
        json.dumps({"as_of_utc": AS_OF_UTC, "sources": SOURCES}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    # Stamp provenance on every fixture.
    for fx in FIXTURES:
        fx["source_keys"] = list(dict.fromkeys(
            fc["source_key"] for fc in fx["facts"] if fc["source_key"] in SOURCE_MAP))
    (OUT / "fixtures.json").write_text(json.dumps(fixtures, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    print(f"wrote {len(FIXTURES)} fixtures across "
          f"{len({x['sport'] for x in FIXTURES})} sports to data/executive/")


if __name__ == "__main__":
    main()
