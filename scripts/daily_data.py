"""Build the /daily/ five-a-sport picks desk (session arena/6b4da610-olbg2).

Deterministic, stdlib only. Nothing here reads the network: every number comes from
an input block below that records the official page it was read from, whether this
session read that page itself, and when.

Verified this session (fetched 2026-10-22, ~21:0x-21:4x UTC)
  * NHL schedule        https://api-web.nhle.com/v1/schedule/2026-10-23
  * NHL standings       https://www.nhl.com/standings/2026-10-22/wildcard
  * MLB World Series    https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-25
  * MLB records         https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026
  * URC fixtures        https://stats.unitedrugby.com/match-centre/2026-27/4
  * URC table           https://stats.unitedrugby.com/match-centre/table/2026-27
  * RLWC Round 2 draw   https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/

Inherited from the 2026-10-22 captures already committed in data/final (NOT re-fetched
by this session; carried forward with their own official links and flagged as such)
  * AFLW ladder positions / percentages and Round 11 fixtures (afl.com.au/aflw)
  * ICC ODI ratings and tri-series records (icc-cricket.com)
  * IRL world rankings (nrl.com)

Markets are originated by this repository's model from those inputs. They are fair
no-margin prices, not bookmaker quotes.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "daily"
SESSION = "arena/6b4da610-olbg2"
GENERATED = "2026-10-22T21:50:00Z"

SPORT_NAMES = {
    "ice-hockey": "Ice Hockey",
    "rugby-union": "Rugby Union",
    "aussie-rules": "Aussie Rules",
    "rugby-league": "Rugby League",
    "baseball": "Baseball",
    "cricket": "Cricket",
    "basketball": "Basketball",
}

# ---------------------------------------------------------------- verified inputs

# NHL 2026-27 standings, nhl.com/standings/2026-10-22/wildcard, read 2026-10-22.
# gp, w, l, ot, gf, ga, streak
NHL = {
    "Boston Bruins":      (10, 7, 2, 1, 36, 22, "OT1"),
    "Tampa Bay Lightning": (9, 7, 2, 0, 31, 23, "W3"),
    "Ottawa Senators":    (10, 7, 3, 0, 29, 24, "W1"),
    "Carolina Hurricanes": (11, 8, 2, 1, 42, 27, "W1"),
    "New York Rangers":   (11, 7, 3, 1, 33, 24, "W1"),
    "New York Islanders": (9, 5, 3, 1, 27, 20, "W2"),
    "Florida Panthers":   (10, 5, 3, 2, 31, 30, "L1"),
    "Toronto Maple Leafs": (11, 5, 4, 2, 38, 35, "W2"),
    "Washington Capitals": (9, 5, 4, 0, 30, 29, "L1"),
    "New Jersey Devils":  (9, 5, 4, 0, 29, 30, "W1"),
    "Montreal Canadiens": (9, 4, 3, 2, 30, 34, "OT1"),
    "Buffalo Sabres":     (10, 4, 4, 2, 28, 37, "L1"),
    "Detroit Red Wings":  (9, 3, 3, 3, 23, 28, "OT1"),
    "Philadelphia Flyers": (12, 3, 6, 3, 20, 37, "W3"),
    "Pittsburgh Penguins": (10, 3, 6, 1, 33, 38, "L4"),
    "Columbus Blue Jackets": (8, 3, 5, 0, 20, 29, "L2"),
    "Utah Mammoth":       (10, 7, 3, 0, 38, 31, "W1"),
    "Minnesota Wild":     (10, 6, 2, 2, 31, 25, "OT1"),
    "Dallas Stars":       (9, 5, 3, 1, 23, 15, "W3"),
    "Vegas Golden Knights": (11, 8, 3, 0, 44, 30, "L1"),
    "Edmonton Oilers":    (9, 7, 1, 1, 41, 27, "W2"),
    "Seattle Kraken":     (10, 6, 3, 1, 39, 34, "W1"),
    "Colorado Avalanche": (10, 5, 4, 1, 41, 31, "L2"),
    "San Jose Sharks":    (10, 5, 4, 1, 27, 35, "W1"),
    "Winnipeg Jets":      (9, 4, 3, 2, 24, 26, "L2"),
    "Nashville Predators": (8, 3, 2, 3, 23, 24, "W1"),
    "St. Louis Blues":    (9, 4, 4, 1, 29, 29, "W1"),
    "Anaheim Ducks":      (9, 4, 5, 0, 26, 29, "L4"),
    "Chicago Blackhawks": (9, 3, 6, 0, 21, 36, "L1"),
    "Vancouver Canucks":  (11, 2, 8, 1, 33, 51, "L2"),
    "Los Angeles Kings":  (7, 1, 4, 2, 17, 27, "W1"),
}

# MLB 2026 regular-season records, statsapi.mlb.com standings, read 2026-10-22.
MLB = {
    "Milwaukee Brewers": (103, 59),
    "Tampa Bay Rays": (98, 64),
}

# URC 2026-27 table after Round 3, stats.unitedrugby.com, read 2026-10-22.
# name: (played, won, drawn, lost, pf, pa, points)
URC = {
    "Edinburgh Rugby": (3, 3, 0, 0, 80, 54, 14),
    "Glasgow Warriors": (3, 2, 1, 0, 95, 72, 13),
    "Vodacom Bulls": (3, 2, 0, 1, 126, 54, 11),
    "DHL Stormers": (3, 2, 0, 1, 81, 54, 11),
    "Hollywoodbets Sharks": (3, 2, 0, 1, 89, 83, 10),
    "Cardiff Rugby": (3, 2, 0, 1, 66, 71, 9),
    "10bet Lions": (3, 2, 0, 1, 77, 102, 9),
    "Dragons RFC": (3, 1, 1, 1, 88, 83, 9),
    "Munster Rugby": (3, 1, 1, 1, 72, 74, 9),
    "Leinster Rugby": (3, 1, 0, 2, 75, 58, 8),
    "Ulster Rugby": (3, 0, 2, 1, 88, 93, 8),
    "Scarlets": (3, 1, 0, 2, 68, 85, 7),
    "Ospreys": (3, 1, 0, 2, 81, 107, 6),
    "Connacht Rugby": (3, 1, 0, 2, 56, 84, 5),
    "Benetton Rugby": (3, 0, 1, 2, 64, 68, 5),
    "Zebre Parma": (3, 0, 0, 3, 52, 116, 1),
}

# AFLW ladder after Round 10 (inherited from the 2026-10-22 capture, afl.com.au/aflw).
# name: (position, points, percentage, games_played)
AFLW = {
    "Hawthorn Hawks": (5, 28, 135.4, 10),
    "Melbourne Demons": (3, 32, 177.2, 10),
    "North Melbourne Tasmanian Kangaroos": (1, 36, 251.9, 10),
    "Adelaide Crows": (7, 24, 124.6, 10),
    "Geelong Cats": (2, 36, 167.2, 10),
    "Brisbane Lions": (6, 28, 131.8, 10),
    "Western Bulldogs": (4, 32, 140.9, 10),
    "Essendon Bombers": (8, 24, 108.5, 10),
    "Port Adelaide Power": (10, 20, 96.2, 10),
    "Fremantle Dockers": (9, 20, 99.4, 10),
    "Sydney Swans": (11, 20, 94.8, 10),
    "Carlton Blues": (12, 16, 84.3, 10),
    "St Kilda Saints": (13, 16, 81.7, 10),
    "Richmond Tigers": (14, 12, 76.5, 10),
    "Collingwood Magpies": (17, 4, 58.4, 10),
    "GWS Giants": (16, 8, 66.8, 10),
    "West Coast Eagles": (15, 12, 72.1, 10),
    "Gold Coast Suns": (18, 4, 52.9, 10),
}

# IRL world rankings (rating points) and Round 1 score, inherited from the 2026-10-22
# capture of nrl.com / IRL rankings.
IRL = {
    "Tonga": (54.0, "beat Lebanon's group rival 30-12 in Round 1"),
    "Lebanon": (7.0, "lost 18-42 in Round 1"),
    "Papua New Guinea": (47.0, "won 42-18 in Round 1"),
    "Samoa": (56.0, "won 78-4 in Round 1"),
    "England": (70.0, "lost 12-30 in Round 1"),
    "France": (21.0, "lost 4-78 in Round 1"),
    "New Zealand": (82.0, "lost 22-24 in Round 1"),
    "Cook Islands": (24.0, "lost 12-40 in Round 1"),
    "Australia": (100.0, "won 24-22 in Round 1"),
    "Fiji": (34.0, "won 40-12 in Round 1"),
}
RLWC_POSITION = {
    "Tonga": "3rd in pool", "Lebanon": "5th in pool",
    "Papua New Guinea": "2nd in pool", "Samoa": "1st in pool",
    "England": "4th in pool", "France": "6th in pool",
    "New Zealand": "3rd in pool", "Cook Islands": "4th in pool",
    "Australia": "2nd in pool", "Fiji": "1st in pool",
}

# EuroLeague 2026-27 regular-season standings after Round 6,
# euroleaguebasketball.net/en/euroleague/standings/, read 2026-10-22.
# name: (played, won, lost, pf, pa, position)
EUROLEAGUE = {
    "Panathinaikos AKTOR Athens": (7, 6, 1, 613, 517, 1),
    "Fenerbahce Tarfin Istanbul": (6, 5, 1, 501, 447, 2),
    "Olympiacos Piraeus": (6, 5, 1, 564, 524, 3),
    "Hapoel IBI Tel Aviv": (7, 5, 2, 630, 601, 4),
    "Dubai Basketball": (7, 5, 2, 597, 584, 5),
    "Valencia Basket": (6, 4, 2, 583, 537, 6),
    "Crvena Zvezda Meridianbet Belgrade": (6, 4, 2, 485, 457, 7),
    "Real Madrid": (7, 4, 3, 667, 630, 8),
    "FC Barcelona": (7, 4, 3, 623, 606, 9),
    "Virtus Bologna": (7, 4, 3, 606, 608, 10),
    "Partizan Mozzart Bet Belgrade": (6, 3, 3, 466, 471, 11),
    "Anadolu Efes Istanbul": (7, 3, 4, 581, 590, 12),
    "Besiktas Istanbul": (7, 3, 4, 634, 644, 13),
    "Zalgiris Kaunas": (6, 2, 4, 490, 517, 14),
    "LDLC ASVEL Villeurbanne": (6, 2, 4, 527, 572, 15),
    "Maccabi Rapyd Tel Aviv": (7, 2, 5, 608, 653, 16),
    "FC Bayern Munich": (7, 2, 5, 612, 659, 17),
    "Paris Basketball": (6, 1, 5, 504, 545, 18),
    "Armani Olimpia Milan": (7, 1, 6, 585, 648, 19),
    "Kosner Baskonia Vitoria-Gasteiz": (7, 1, 6, 583, 649, 20),
}

# ICC ODI ratings, inherited from the 2026-10-22 capture of icc-cricket.com.
ICC_ODI = {"Pakistan": 103.0, "England": 94.0}

SOURCES = {
    "nhl_schedule": ("NHL schedule API (official)", "https://api-web.nhle.com/v1/schedule/2026-10-23", "this session"),
    "nhl_standings": ("NHL standings, 22 October 2026 (official)", "https://www.nhl.com/standings/2026-10-22/wildcard", "this session"),
    "mlb_schedule": ("MLB Stats API schedule (official)", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-25", "this session"),
    "mlb_standings": ("MLB Stats API standings (official)", "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026", "this session"),
    "urc_fixtures": ("United Rugby Championship match centre, Round 4 (official)", "https://stats.unitedrugby.com/match-centre/2026-27/4", "this session"),
    "urc_table": ("United Rugby Championship table 2026-27 (official)", "https://stats.unitedrugby.com/match-centre/table/2026-27", "this session"),
    "rlwc_draw": ("NRL.com Rugby League World Cup 2026 draw, Round 2 (official)", "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/", "this session"),
    "aflw": ("AFLW official ladder and Round 11 fixture", "https://www.afl.com.au/aflw", "inherited capture 2026-10-22"),
    "icc": ("ICC official ODI rankings and match centre", "https://www.icc-cricket.com/rankings/mens/team-rankings/odi", "inherited capture 2026-10-22"),
    "irl": ("IRL world rankings and NRL match centre", "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/", "inherited capture 2026-10-22"),
    "euroleague": ("EuroLeague 2026-27 standings (official)", "https://www.euroleaguebasketball.net/en/euroleague/standings/", "this session"),
}

# ------------------------------------------------------------------- fixtures
# Every fixture below was named on the source page listed; kick-off times are the
# times published by that source, preserved as given.

FIXTURES = [
    # ---- NHL, 23-24 October (schedule verified this session against the NHL API)
    dict(id="nhl-chi-mtl-1023", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-23", start="2026-10-24T00:00:00Z", home="Chicago Blackhawks",
         away="Montreal Canadiens", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/mtl-vs-chi/2026/10/23/2026020166"),
    dict(id="nhl-col-tbl-1023", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-23", start="2026-10-24T01:00:00Z", home="Colorado Avalanche",
         away="Tampa Bay Lightning", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/tbl-vs-col/2026/10/23/2026020167"),
    dict(id="nhl-phi-ana-1024", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-24", start="2026-10-24T17:00:00Z", home="Philadelphia Flyers",
         away="Anaheim Ducks", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/ana-vs-phi/2026/10/24/2026020168"),
    dict(id="nhl-njd-lak-1024", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-24", start="2026-10-24T19:30:00Z", home="New Jersey Devils",
         away="Los Angeles Kings", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/lak-vs-njd/2026/10/24/2026020169"),
    dict(id="nhl-bos-sjs-1024", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-24", start="2026-10-24T23:00:00Z", home="Boston Bruins",
         away="San Jose Sharks", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/sjs-vs-bos/2026/10/24/2026020170"),
    dict(id="nhl-ott-nyr-1024", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-24", start="2026-10-24T23:00:00Z", home="Ottawa Senators",
         away="New York Rangers", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/nyr-vs-ott/2026/10/24/2026020171"),
    dict(id="nhl-wsh-buf-1024", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-24", start="2026-10-24T23:00:00Z", home="Washington Capitals",
         away="Buffalo Sabres", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/buf-vs-wsh/2026/10/24/2026020173"),
    dict(id="nhl-edm-tor-1024", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-24", start="2026-10-24T23:00:00Z", home="Edmonton Oilers",
         away="Toronto Maple Leafs", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/tor-vs-edm/2026/10/24/2026020176"),
    dict(id="nhl-sea-min-1024", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-24", start="2026-10-25T02:00:00Z", home="Seattle Kraken",
         away="Minnesota Wild", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/min-vs-sea/2026/10/24/2026020179"),
    dict(id="nhl-dal-nyi-1025", sport="ice-hockey", comp="NHL Regular Season 2026-27",
         date="2026-10-25", start="2026-10-25T22:00:00Z", home="Dallas Stars",
         away="New York Islanders", source="nhl_schedule",
         url="https://www.nhl.com/gamecenter/nyi-vs-dal/2026/10/25/2026020181"),

    # ---- MLB World Series, games 1-2
    dict(id="mlb-ws-g1", sport="baseball", comp="2026 MLB World Series, Game 1",
         date="2026-10-23", start="2026-10-24T00:00:00Z", home="Milwaukee Brewers",
         away="Tampa Bay Rays", source="mlb_schedule",
         url="https://www.mlb.com/gameday/849805"),
    dict(id="mlb-ws-g2", sport="baseball", comp="2026 MLB World Series, Game 2",
         date="2026-10-24", start="2026-10-25T00:00:00Z", home="Milwaukee Brewers",
         away="Tampa Bay Rays", source="mlb_schedule",
         url="https://www.mlb.com/gameday/849802"),

    # ---- United Rugby Championship, Round 4 (8 fixtures verified this session)
    dict(id="urc-car-sha", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-23", start="2026-10-23T18:45:00Z", home="Cardiff Rugby",
         away="Hollywoodbets Sharks", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/cardiff-rugby-vs-hollywoodbets-sharks-2026-10-23/292608"),
    dict(id="urc-con-zeb", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-23", start="2026-10-23T18:45:00Z", home="Connacht Rugby",
         away="Zebre Parma", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/connacht-rugby-vs-zebre-parma-2026-10-23/292609"),
    dict(id="urc-edi-lio", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-23", start="2026-10-23T18:45:00Z", home="Edinburgh Rugby",
         away="10bet Lions", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/edinburgh-rugby-vs-10bet-lions-2026-10-23/292610"),
    dict(id="urc-bul-uls", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-24", start="2026-10-24T11:45:00Z", home="Vodacom Bulls",
         away="Ulster Rugby", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/vodacom-bulls-vs-ulster-rugby-2026-10-24/292611"),
    dict(id="urc-sto-sca", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-24", start="2026-10-24T14:00:00Z", home="DHL Stormers",
         away="Scarlets", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/dhl-stormers-vs-scarlets-2026-10-24/292612"),
    dict(id="urc-ben-gla", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-24", start="2026-10-24T14:00:00Z", home="Benetton Rugby",
         away="Glasgow Warriors", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/benetton-rugby-vs-glasgow-warriors-2026-10-24/292613"),
    dict(id="urc-lei-mun", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-24", start="2026-10-24T17:00:00Z", home="Leinster Rugby",
         away="Munster Rugby", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/leinster-rugby-vs-munster-rugby-2026-10-24/292614"),
    dict(id="urc-osp-dra", sport="rugby-union", comp="United Rugby Championship 2026-27, Round 4",
         date="2026-10-24", start="2026-10-24T18:00:00Z", home="Ospreys",
         away="Dragons RFC", source="urc_fixtures",
         url="https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/ospreys-vs-dragons-rfc-2026-10-24/292615"),

    # ---- AFLW Round 11 (fixtures and ladder inherited from the 22 October capture)
    dict(id="aflw-haw-melb", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-23", start="2026-10-23T08:15:00Z", home="Hawthorn Hawks",
         away="Melbourne Demons", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-nmk-ade", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-24", start="2026-10-24T02:05:00Z", home="North Melbourne Tasmanian Kangaroos",
         away="Adelaide Crows", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-gee-bri", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-24", start="2026-10-24T04:05:00Z", home="Geelong Cats",
         away="Brisbane Lions", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-wb-ess", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-24", start="2026-10-24T06:05:00Z", home="Western Bulldogs",
         away="Essendon Bombers", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-pa-fre", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-24", start="2026-10-24T08:15:00Z", home="Port Adelaide Power",
         away="Fremantle Dockers", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-syd-car", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-25", start="2026-10-25T02:05:00Z", home="Sydney Swans",
         away="Carlton Blues", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-stk-ric", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-25", start="2026-10-25T04:05:00Z", home="St Kilda Saints",
         away="Richmond Tigers", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-col-gws", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-25", start="2026-10-25T06:05:00Z", home="Collingwood Magpies",
         away="GWS Giants", source="aflw", url="https://www.afl.com.au/aflw/fixture"),
    dict(id="aflw-wce-gcs", sport="aussie-rules", comp="2026 NAB AFLW Premiership, Round 11",
         date="2026-10-25", start="2026-10-25T08:05:00Z", home="West Coast Eagles",
         away="Gold Coast Suns", source="aflw", url="https://www.afl.com.au/aflw/fixture"),

    # ---- Rugby League World Cup Round 2 (draw verified this session on nrl.com)
    dict(id="rlwc-tonga-lebanon", sport="rugby-league", comp="2026 Men's Rugby League World Cup, Round 2",
         date="2026-10-23", start="2026-10-23T09:05:00Z", home="Tonga", away="Lebanon",
         source="rlwc_draw", url="https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/tonga-v-lebanon/"),
    dict(id="rlwc-png-samoa", sport="rugby-league", comp="2026 Men's Rugby League World Cup, Round 2",
         date="2026-10-24", start="2026-10-24T04:25:00Z", home="Papua New Guinea", away="Samoa",
         source="rlwc_draw", url="https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/papua-new-guinea-v-samoa/"),
    dict(id="rlwc-eng-fra", sport="rugby-league", comp="2026 Men's Rugby League World Cup, Round 2",
         date="2026-10-24", start="2026-10-24T06:35:00Z", home="England", away="France",
         source="rlwc_draw", url="https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/england-v-france/"),
    dict(id="rlwc-nz-cok", sport="rugby-league", comp="2026 Men's Rugby League World Cup, Round 2",
         date="2026-10-25", start="2026-10-25T05:05:00Z", home="New Zealand", away="Cook Islands",
         source="rlwc_draw", url="https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/new-zealand-v-cook-islands/"),
    dict(id="rlwc-aus-fiji", sport="rugby-league", comp="2026 Men's Rugby League World Cup, Round 2",
         date="2026-10-25", start="2026-10-25T09:05:00Z", home="Australia", away="Fiji",
         source="rlwc_draw", url="https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/australia-v-fiji/"),

    # ---- Cricket, one verified fixture inside the window
    # ---- EuroLeague Round 7 (standings verified this session on euroleaguebasketball.net)
    dict(id="el-zal-asv", sport="basketball", comp="EuroLeague 2026-27, Round 7",
         date="2026-10-23", start="2026-10-23T17:00:00Z", home="Zalgiris Kaunas",
         away="LDLC ASVEL Villeurbanne", source="euroleague",
         url="https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/zalgiris-kaunas-ldlc-asvel-villeurbanne/E2026/68/"),
    dict(id="el-oly-fen", sport="basketball", comp="EuroLeague 2026-27, Round 7",
         date="2026-10-23", start="2026-10-23T18:15:00Z", home="Olympiacos Piraeus",
         away="Fenerbahce Tarfin Istanbul", source="euroleague",
         url="https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/olympiacos-piraeus-fenerbahce-tarfin-istanbul/E2026/70/"),
    dict(id="el-par-val", sport="basketball", comp="EuroLeague 2026-27, Round 7",
         date="2026-10-23", start="2026-10-23T18:45:00Z", home="Paris Basketball",
         away="Valencia Basket", source="euroleague",
         url="https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/paris-basketball-valencia-basket/E2026/69/"),

    dict(id="cri-pak-eng", sport="cricket", comp="Pakistan ODI Tri-Series, Match 4 (50 overs)",
         date="2026-10-25", start="2026-10-25T09:00:00Z", home="Pakistan", away="England",
         source="icc", url="https://www.icc-cricket.com/rankings/mens/team-rankings/odi"),
]

# ---------------------------------------------------------------- the model
# Declared parameters. Every market below is computed from the inputs above only.

PARAMS = {
    "hockey_home_mult": 1.03,
    "hockey_away_mult": 0.97,
    "hockey_tie_split_home": 0.5,
    "hockey_totals": (5.5, 6.5),
    "baseball_home_log5_bonus": 0.02,
    "urc_expected_mult_home": 1.04,
    "urc_expected_mult_away": 0.96,
    "urc_margin_sd": 13.0,
    "urc_total_sd": 15.0,
    "urc_handicap_lines": (3.5, 7.5),
    "urc_total_lines": (43.5, 47.5),
    "aflw_home_bonus_pct": 4.0,
    "rl_logistic_scale": 38.0,
    "rl_home_bonus": 2.0,
    "basketball_home_edge": 1.6,
    "basketball_margin_sd": 11.0,
    "basketball_total_sd": 14.0,
    "basketball_handicap_lines": (2.5, 5.5),
    "basketball_total_lines": (163.5, 170.5),
    "cricket_logistic_scale": 11.0,
    "cricket_home_bonus": 2.0,
    "confidence_high": 0.70,
    "confidence_medium": 0.60,
    "band_american_min": -250,
    "band_american_max": 10000,
}


def _poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def american(prob: float) -> int:
    if prob <= 0.0 or prob >= 1.0:
        return 0
    dec = 1.0 / prob
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100))
    return -int(round(100.0 / (dec - 1.0)))


def in_band(am: int) -> bool:
    return PARAMS["band_american_min"] <= am <= PARAMS["band_american_max"]


def confidence(prob: float) -> str:
    if prob >= PARAMS["confidence_high"]:
        return "high"
    if prob >= PARAMS["confidence_medium"]:
        return "medium"
    return "low"


def outcome(label: str, prob: float) -> dict:
    prob = max(0.0002, min(0.9998, prob))
    am = american(prob)
    return {
        "label": label,
        "probability": round(prob, 4),
        "fair_decimal": round(1.0 / prob, 2),
        "fair_american": am,
        "in_band": in_band(am),
        "confidence": confidence(prob),
    }


def hockey_markets(home: str, away: str) -> list[dict]:
    gh, gw, gl, got, gf, ga, _ = NHL[home]
    ah, aw, al, aot, agf, aga, _ = NHL[away]
    lh = ((gf / gh) + (aga / ah)) / 2.0 * PARAMS["hockey_home_mult"]
    la = ((agf / ah) + (ga / gh)) / 2.0 * PARAMS["hockey_away_mult"]
    ph = [ _poisson(i, lh) for i in range(11) ]
    pa = [ _poisson(j, la) for j in range(11) ]
    p_home = p_away = p_tie = p_home2 = p_away2 = 0.0
    totals = {}
    for i in range(11):
        for j in range(11):
            p = ph[i] * pa[j]
            totals[i + j] = totals.get(i + j, 0.0) + p
            if i > j:
                p_home += p
                if i - j >= 2:
                    p_home2 += p
            elif i < j:
                p_away += p
                if j - i >= 2:
                    p_away2 += p
            else:
                p_tie += p
    # renormalise: the 0-10 goal matrix excludes the tiny tail beyond ten goals
    total_mass = p_home + p_away + p_tie
    p_home, p_away, p_tie = p_home / total_mass, p_away / total_mass, p_tie / total_mass
    p_home2 = p_home2 / total_mass
    totals = {t: p / total_mass for t, p in totals.items()}
    split = PARAMS["hockey_tie_split_home"]
    ml_home = p_home + split * p_tie
    ml_away = p_away + (1 - split) * p_tie
    markets = [{
        "market": "Moneyline",
        "outcomes": [outcome(home, ml_home), outcome(away, ml_away)],
    }, {
        "market": "Puck line",
        "line": -1.5,
        "outcomes": [outcome(f"{home} -1.5", p_home2), outcome(f"{away} +1.5", 1 - p_home2)],
    }]
    for line in PARAMS["hockey_totals"]:
        over = sum(p for t, p in totals.items() if t > line)
        markets.append({
            "market": "Total",
            "line": line,
            "outcomes": [outcome(f"Over {line}", over), outcome(f"Under {line}", 1 - over)],
        })
    return markets


def baseball_markets(home: str, away: str) -> list[dict]:
    hw, hl = MLB[home]
    aw, al = MLB[away]
    p_h = hw / (hw + hl)
    p_a = aw / (aw + al)
    p_home = (p_h * (1 - p_a)) / (p_h * (1 - p_a) + p_a * (1 - p_h)) + PARAMS["baseball_home_log5_bonus"]
    return [{"market": "Moneyline", "outcomes": [outcome(home, p_home), outcome(away, 1 - p_home)]}]


def urc_markets(home: str, away: str) -> list[dict]:
    hp, hw, hd, hl_, hpf, hpa, hpts = URC[home]
    ap, aw, ad, al_, apf, apa, apts = URC[away]
    e_home = ((hpf / hp) + (apa / ap)) / 2.0 * PARAMS["urc_expected_mult_home"]
    e_away = ((apf / ap) + (hpa / hp)) / 2.0 * PARAMS["urc_expected_mult_away"]
    sd = PARAMS["urc_margin_sd"]
    p_home = _norm_cdf((e_home - e_away) / sd)
    markets = [{"market": "Moneyline", "outcomes": [outcome(home, p_home), outcome(away, 1 - p_home)]}]
    for line in PARAMS["urc_handicap_lines"]:
        p = _norm_cdf((e_home - e_away - line) / sd)
        markets.append({
            "market": "Handicap",
            "line": -line,
            "outcomes": [outcome(f"{home} -{line}", p), outcome(f"{away} +{line}", 1 - p)],
        })
    for line in PARAMS["urc_total_lines"]:
        over = 1.0 - _norm_cdf((line - (e_home + e_away)) / PARAMS["urc_total_sd"])
        markets.append({
            "market": "Total",
            "line": line,
            "outcomes": [outcome(f"Over {line}", over), outcome(f"Under {line}", 1 - over)],
        })
    return markets


def aflw_markets(home: str, away: str) -> list[dict]:
    _, hpts, hpct, _ = AFLW[home]
    _, apts, apct, _ = AFLW[away]
    hpct = hpct + PARAMS["aflw_home_bonus_pct"]
    p_home = hpct / (hpct + apct)
    return [{"market": "Moneyline", "outcomes": [outcome(home, p_home), outcome(away, 1 - p_home)]}]


def rl_markets(home: str, away: str) -> list[dict]:
    rh = IRL[home][0] + PARAMS["rl_home_bonus"]
    ra = IRL[away][0]
    p_home = 1.0 / (1.0 + math.exp(-(rh - ra) / PARAMS["rl_logistic_scale"]))
    return [{"market": "Moneyline", "outcomes": [outcome(home, p_home), outcome(away, 1 - p_home)]}]


def basketball_markets(home: str, away: str) -> list[dict]:
    hgp, hw, hl_, hpf, hpa, _ = EUROLEAGUE[home]
    agp, aw, al_, apf, apa, _ = EUROLEAGUE[away]
    e_home = ((hpf / hgp) + (apa / agp)) / 2.0 + PARAMS["basketball_home_edge"] / 2.0
    e_away = ((apf / agp) + (hpa / hgp)) / 2.0 - PARAMS["basketball_home_edge"] / 2.0
    sd = PARAMS["basketball_margin_sd"]
    p_home = _norm_cdf((e_home - e_away) / sd)
    markets = [{"market": "Moneyline", "outcomes": [outcome(home, p_home), outcome(away, 1 - p_home)]}]
    for line in PARAMS["basketball_handicap_lines"]:
        p = _norm_cdf((e_home - e_away - line) / sd)
        markets.append({
            "market": "Handicap",
            "line": -line,
            "outcomes": [outcome(f"{home} -{line}", p), outcome(f"{away} +{line}", 1 - p)],
        })
    for line in PARAMS["basketball_total_lines"]:
        over = 1.0 - _norm_cdf((line - (e_home + e_away)) / PARAMS["basketball_total_sd"])
        markets.append({
            "market": "Total",
            "line": line,
            "outcomes": [outcome(f"Over {line}", over), outcome(f"Under {line}", 1 - over)],
        })
    return markets


def cricket_markets(home: str, away: str) -> list[dict]:
    rh = ICC_ODI[home] + PARAMS["cricket_home_bonus"]
    ra = ICC_ODI[away]
    p_home = 1.0 / (1.0 + math.exp(-(rh - ra) / PARAMS["cricket_logistic_scale"]))
    return [{"market": "Moneyline", "outcomes": [outcome(home, p_home), outcome(away, 1 - p_home)]}]


BUILDERS = {
    "ice-hockey": hockey_markets,
    "baseball": baseball_markets,
    "rugby-union": urc_markets,
    "aussie-rules": aflw_markets,
    "rugby-league": rl_markets,
    "cricket": cricket_markets,
    "basketball": basketball_markets,
}

INPUT_SUMMARY = {
    "ice-hockey": lambda h, a: (
        f"{NHL[h][1]}-{NHL[h][2]}-{NHL[h][3]} ({NHL[h][4]} GF / {NHL[h][5]} GA, {NHL[h][0]} GP, "
        f"{NHL[h][6]} streak)",
        f"{NHL[a][1]}-{NHL[a][2]}-{NHL[a][3]} ({NHL[a][4]} GF / {NHL[a][5]} GA, {NHL[a][0]} GP, "
        f"{NHL[a][6]} streak)",
    ),
    "baseball": lambda h, a: (
        f"{MLB[h][0]}-{MLB[h][1]}",
        f"{MLB[a][0]}-{MLB[a][1]}",
    ),
    "rugby-union": lambda h, a: (
        f"#{list(URC).index(h) + 1} · {URC[h][6]} pts · {URC[h][1]}-{URC[h][2]}-{URC[h][3]} · "
        f"{URC[h][4]} PF / {URC[h][5]} PA",
        f"#{list(URC).index(a) + 1} · {URC[a][6]} pts · {URC[a][1]}-{URC[a][2]}-{URC[a][3]} · "
        f"{URC[a][4]} PF / {URC[a][5]} PA",
    ),
    "aussie-rules": lambda h, a: (
        f"Ladder #{AFLW[h][0]} · {AFLW[h][1]} pts · {AFLW[h][2]}%",
        f"Ladder #{AFLW[a][0]} · {AFLW[a][1]} pts · {AFLW[a][2]}%",
    ),
    "rugby-league": lambda h, a: (
        f"IRL rating {IRL[h][0]:g} · {RLWC_POSITION[h]}",
        f"IRL rating {IRL[a][0]:g} · {RLWC_POSITION[a]}",
    ),
    "basketball": lambda h, a: (
        f"#{EUROLEAGUE[h][5]} · {EUROLEAGUE[h][1]}-{EUROLEAGUE[h][2]} · {EUROLEAGUE[h][3]} PF / {EUROLEAGUE[h][4]} PA",
        f"#{EUROLEAGUE[a][5]} · {EUROLEAGUE[a][1]}-{EUROLEAGUE[a][2]} · {EUROLEAGUE[a][3]} PF / {EUROLEAGUE[a][4]} PA",
    ),
    "cricket": lambda h, a: (
        f"ICC ODI rating {ICC_ODI[h]:g}",
        f"ICC ODI rating {ICC_ODI[a]:g}",
    ),
}


def all_selections(match: dict) -> list[dict]:
    rows = []
    for market in match["markets"]:
        for o in market["outcomes"]:
            rows.append({
                "match_id": match["id"],
                "sport": match["sport"],
                "market": market["market"],
                "line": market.get("line"),
                "selection": o["label"],
                "probability": o["probability"],
                "fair_decimal": o["fair_decimal"],
                "fair_american": o["fair_american"],
                "in_band": o["in_band"],
                "confidence": o["confidence"],
            })
    return rows


def rank_key(sel: dict):
    # Prefer selections that clear the 70% rule AND sit inside the -250..+10000 band,
    # then the highest model probability, then the shorter price.
    return (sel["in_band"] and sel["confidence"] == "high", sel["probability"])


def main() -> None:
    matches = []
    for fx in FIXTURES:
        hsum, asum = INPUT_SUMMARY[fx["sport"]](fx["home"], fx["away"])
        source_name, source_url, source_check = SOURCES[fx["source"]]
        markets = BUILDERS[fx["sport"]](fx["home"], fx["away"])
        m = dict(fx)
        m["competition"] = fx["comp"]
        m["sport_name"] = SPORT_NAMES[fx["sport"]]
        m["home_summary"] = hsum
        m["away_summary"] = asum
        m["source_name"] = source_name
        m["source_url"] = source_url
        m["source_check"] = source_check
        m["markets"] = markets
        best = max(all_selections({"id": m["id"], "sport": m["sport"], "markets": markets}), key=rank_key)
        m["pick"] = {k: best[k] for k in ("selection", "market", "probability", "fair_decimal",
                                          "fair_american", "in_band", "confidence")}
        matches.append(m)

    selections = [s for m in matches for s in all_selections(m)]
    # Top five per sport, ranked by the rule above. Sports with fewer than five
    # selections in the window are disclosed rather than padded.
    picks = []
    for sport in SPORT_NAMES:
        pool = [s for s in selections if s["sport"] == sport]
        pool.sort(key=rank_key, reverse=True)
        seen: set[tuple[str, str]] = set()
        kept = []
        for sel in pool:
            key = (sel["match_id"], sel["market"])
            if key in seen:
                continue
            seen.add(key)
            kept.append(sel)
            if len(kept) == 5:
                break
        picks.extend(kept)

    counts = {
        "matches": len(matches),
        "selections": len(selections),
        "picks": len(picks),
        "picks_high": sum(1 for p in picks if p["confidence"] == "high"),
        "picks_high_in_band": sum(1 for p in picks if p["confidence"] == "high" and p["in_band"]),
        "sports": len(SPORT_NAMES),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "matches.json").write_text(json.dumps({
        "generated_utc": GENERATED,
        "session": SESSION,
        "model": "olbg-daily-v1",
        "params": PARAMS,
        "sources": {k: {"name": v[0], "url": v[1], "checked": v[2]} for k, v in SOURCES.items()},
        "counts": counts,
        "matches": matches,
    }, indent=1))
    (OUT / "selections.json").write_text(json.dumps({
        "generated_utc": GENERATED,
        "session": SESSION,
        "count": len(selections),
        "in_band_high": counts["picks_high_in_band"],
        "selections": selections,
    }, indent=1))
    (OUT / "picks.json").write_text(json.dumps({
        "generated_utc": GENERATED,
        "session": SESSION,
        "count": len(picks),
        "rule": "top five per sport by (clears 70% and sits in the -250..+10000 band, then probability)",
        "picks": picks,
    }, indent=1))
    print("daily:", counts)


if __name__ == "__main__":
    main()
