#!/usr/bin/env python3
"""
Deterministic official-source seed generator for `/portal/` (`arena/d81930c3-olbg2`).

Writes:
  - data/portal/sports.json
  - data/portal/sources.json
  - data/portal/repo_audit.json
  - data/portal/inputs.json

Every value is transcribed from first-hand governing-body & OLBG fetches captured on 2026-10-22 UTC.
No bookmaker prices, community wikis, or unverified inferences are permitted.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "portal"

ELIGIBLE_SPORTS = [
    {
        "slug": "aussie-rules",
        "name": "Aussie Rules",
        "olbg_id": 22,
        "olbg_url": "https://www.olbg.com/betting-tips/Aussie_Rules/22",
        "olbg_status": "Live hub HTTP 200 ('No tips found'); active NAB AFLW Round 11 verified via afl.com.au",
        "governing_body": "Australian Football League (AFL / NAB AFLW)",
        "official_url": "https://www.afl.com.au/aflw",
        "competitions": ["2026 NAB AFLW Premiership — Round 11"],
    },
    {
        "slug": "baseball",
        "name": "Baseball",
        "olbg_id": 12,
        "olbg_url": "https://www.olbg.com/betting-tips/Baseball/12",
        "olbg_status": "Live hub HTTP 200 (2026 World Series Game 1 event_id=160789)",
        "governing_body": "Major League Baseball (MLB StatsAPI)",
        "official_url": "https://statsapi.mlb.com/api/v1/schedule/postseason?season=2026",
        "competitions": ["2026 MLB World Series — Tampa Bay Rays vs Milwaukee Brewers"],
    },
    {
        "slug": "basketball",
        "name": "Basketball",
        "olbg_id": 4,
        "olbg_url": "https://www.olbg.com/betting-tips/Basketball/4",
        "olbg_status": "Live hub HTTP 200 (NBA Opening Week + EuroLeague Round 7)",
        "governing_body": "National Basketball Association (NBA) & Euroleague Basketball",
        "official_url": "https://www.euroleaguebasketball.net/en/euroleague/standings/",
        "competitions": ["2026-27 NBA Regular Season (Opening Week)", "2026-27 EuroLeague Regular Season — Round 7"],
    },
    {
        "slug": "cricket",
        "name": "Cricket",
        "olbg_id": 7,
        "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7",
        "olbg_status": "Live hub HTTP 200 (AFG v ZIM 188831, CSA Pro20 188811 & 188825 + 5 futures)",
        "governing_body": "International Cricket Council (ICC) & Cricket South Africa (CSA)",
        "official_url": "https://www.icc-cricket.com/tournaments/mens-t20-world-cup-2026",
        "competitions": [
            "New Zealand vs India T20I Series",
            "Pakistan ODI Tri-Series",
            "UAE ODI Tri-Series Final",
            "CSA YesPlay Pro20 Cup",
        ],
    },
    {
        "slug": "darts",
        "name": "Darts",
        "olbg_id": 15,
        "olbg_url": "https://www.olbg.com/betting-tips/Darts/15",
        "olbg_status": "Live hub HTTP 200 (16 PDC European Championship R1 ties 32322..32337 + 2 outrights)",
        "governing_body": "Professional Darts Corporation (PDC)",
        "official_url": "https://www.pdc.tv/order-of-merit/pdc-order-merit",
        "competitions": ["2026 Machineseeker European Championship — Round 1 (Dortmund)"],
    },
    {
        "slug": "esports",
        "name": "Esports",
        "olbg_id": 23,
        "olbg_url": "https://www.olbg.com/betting-tips/eSports/23",
        "olbg_status": "Live hub HTTP 200 ('No tips found'); active LoL Worlds Swiss Stage R1 verified via lolesports.com",
        "governing_body": "Riot Games / LoL Esports",
        "official_url": "https://lolesports.com/en-US/leagues/first_stand,lck,lcs,msi,worlds",
        "competitions": ["2026 League of Legends World Championship — Swiss Stage Round 1 (Allen, TX)"],
    },
    {
        "slug": "gaelic-football",
        "name": "Gaelic Football",
        "olbg_id": 25,
        "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25",
        "olbg_status": "Live hub HTTP 200 (5 Senior Club County Finals 3530..3537 + All-Ireland 2027 3327)",
        "governing_body": "Gaelic Athletic Association (GAA / Munster & Connacht County Boards)",
        "official_url": "https://munster.gaa.ie/fixtures/club-championships-2026/",
        "competitions": ["2026 GAA County Senior Football Championship Finals (Cork, Galway, Waterford, Limerick)"],
    },
    {
        "slug": "golf",
        "name": "Golf",
        "olbg_id": 5,
        "olbg_url": "https://www.olbg.com/betting-tips/Golf/5",
        "olbg_status": "Live hub HTTP 200 (Butterfield Bermuda 101904 & Stifel Charity Classic 101903)",
        "governing_body": "PGA TOUR, PGA TOUR Champions & DP World Tour",
        "official_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528",
        "competitions": [
            "PGA TOUR Butterfield Bermuda Championship",
            "DP World Tour Genesis Championship (126-player field)",
            "PGA TOUR Champions Stifel Charity Classic",
        ],
    },
    {
        "slug": "greyhounds",
        "name": "Greyhounds",
        "olbg_id": 28,
        "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28",
        "olbg_status": "Live hub HTTP 200 (4 BAGS traps 689570..689584); Cat-1 Coral 100 Champion Stakes Final via gbgb.org.uk",
        "governing_body": "Greyhound Board of Great Britain (GBGB)",
        "official_url": "https://www.gbgb.org.uk/racing/results/",
        "competitions": ["GBGB Category One — Coral 100 Champion Stakes Final (Romford 575m)"],
    },
    {
        "slug": "handball",
        "name": "Handball",
        "olbg_id": 20,
        "olbg_url": "https://www.olbg.com/betting-tips/Handball/20",
        "olbg_status": "Live hub HTTP 200 (5 EHF Men's Champions League Round 5 ties + domestic leagues)",
        "governing_body": "European Handball Federation (EHF)",
        "official_url": "https://ehfcl.eurohandball.com/men/2026-27/standings/",
        "competitions": ["2026-27 Machineseeker EHF Men's Champions League — Group Phase Round 5"],
    },
    {
        "slug": "ice-hockey",
        "name": "Ice Hockey",
        "olbg_id": 13,
        "olbg_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13",
        "olbg_status": "Live hub HTTP 200 (12 NHL games + 7 Swedish SHL games 199899..199906 + Liiga 199912)",
        "governing_body": "National Hockey League (NHL) & Svenska Ishockeyförbundet (SHL)",
        "official_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "competitions": ["2026-27 NHL Regular Season", "2026-27 Swedish Hockey League (SHL)"],
    },
    {
        "slug": "motor-racing",
        "name": "Motor Racing",
        "olbg_id": 14,
        "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        "olbg_status": "Live hub HTTP 200 (US Grand Prix 913 + 2026 WDC 828 + 2027 WDC 912)",
        "governing_body": "FIA / Formula One World Championship Limited",
        "official_url": "https://www.formula1.com/en/results/2026/races/1297/united-states",
        "competitions": ["2026 FIA Formula 1 World Championship — Round 18 United States Grand Prix (COTA)"],
    },
    {
        "slug": "rugby-league",
        "name": "Rugby League",
        "olbg_id": 10,
        "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10",
        "olbg_status": "Live hub HTTP 200 (3× 2027 futures); active RLWC 2026 Round 2 verified via rlwc2026.com & nrl.com",
        "governing_body": "International Rugby League (IRL) & National Rugby League (NRL / RLWC 2026)",
        "official_url": "https://www.rlwc2026.com/",
        "competitions": ["2026 Men's Rugby League World Cup — Round 2"],
    },
    {
        "slug": "rugby-union",
        "name": "Rugby Union",
        "olbg_id": 9,
        "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9",
        "olbg_status": "Live hub HTTP 200 (Top 14 Round 7, Pro D2 Round 8 & URC Round 4)",
        "governing_body": "United Rugby Championship (URC) & Ligue Nationale de Rugby (LNR Top 14 / Pro D2)",
        "official_url": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/",
        "competitions": ["2026-27 BKT United Rugby Championship — Round 4", "2026-27 Top 14 — J7", "2026-27 Pro D2 — J8"],
    },
    {
        "slug": "snooker",
        "name": "Snooker",
        "olbg_id": 8,
        "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8",
        "olbg_status": "Live hub HTTP 200 (8 WST Northern Ireland Open Round of 16 ties)",
        "governing_body": "World Snooker Tour (WST)",
        "official_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/",
        "competitions": ["2026 BetVictor Northern Ireland Open — Round 3 (Last 16, Belfast)"],
    },
    {
        "slug": "tennis",
        "name": "Tennis",
        "olbg_id": 3,
        "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3",
        "olbg_status": "Live hub HTTP 200 (ATP Almaty, Brussels, Lyon & WTA Ningbo, Osaka 902069..902133)",
        "governing_body": "Association of Tennis Professionals (ATP) & Women's Tennis Association (WTA)",
        "official_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule",
        "competitions": [
            "ATP 250 Almaty Open",
            "ATP 250 European Open (Brussels)",
            "ATP 250 Grand Prix Auvergne-Rhône-Alpes (Lyon)",
            "WTA 500 BNB Ningbo Open",
            "WTA 250 Kinoshita Group Japan Open (Osaka)",
        ],
    },
    {
        "slug": "volleyball",
        "name": "Volleyball",
        "olbg_id": 21,
        "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21",
        "olbg_status": "Live hub HTTP 200 (Italian SuperLega R2 + Polish PlusLiga + Tauron Liga)",
        "governing_body": "Lega Pallavolo Serie A (SuperLega Credem Banca) & Polska Liga Siatkówki",
        "official_url": "https://www.legavolley.it/calendario/?idCampionato=999",
        "competitions": ["2026-27 Italian SuperLega Credem Banca — Round 2"],
    },
]

EXCLUDED_HUBS = [
    {"olbg_id": 1, "olbg_path": "/betting-tips/Football/1", "rule_term": "soccer / football", "http_status": 200, "note": "Association football — excluded"},
    {"olbg_id": 2, "olbg_path": "/betting-tips/Horse_Racing/2", "rule_term": "horse racing", "http_status": 200, "note": "UK & Ireland horse racing — excluded"},
    {"olbg_id": 6, "olbg_path": "/betting-tips/Specials/6", "rule_term": "specials", "http_status": 200, "note": "Legacy specials endpoint — excluded"},
    {"olbg_id": 11, "olbg_path": "/betting-tips/American_Football/11", "rule_term": "american football", "http_status": 200, "note": "NFL / NCAAF — excluded"},
    {"olbg_id": 16, "olbg_path": "/betting-tips/Boxing/16", "rule_term": "boxing", "http_status": 200, "note": "Professional boxing — excluded"},
    {"olbg_id": 17, "olbg_path": "/betting-tips/Cycling/17", "rule_term": "cycling", "http_status": 200, "note": "UCI road/track cycling — excluded"},
    {"olbg_id": 18, "olbg_path": "/betting-tips/Entertainment/18", "rule_term": "specials", "http_status": 200, "note": "TV/award novelty specials — excluded"},
    {"olbg_id": 19, "olbg_path": "/betting-tips/Politics/19", "rule_term": "specials", "http_status": 200, "note": "Election novelty specials — excluded"},
    {"olbg_id": 24, "olbg_path": "/betting-tips/Specials/24", "rule_term": "specials", "http_status": 200, "note": "General specials hub — excluded"},
    {"olbg_id": 26, "olbg_path": "/betting-tips/Hurling/26", "rule_term": "hurling", "http_status": 200, "note": "Live GAA Hurling hub (714, 675) — excluded"},
    {"olbg_id": 27, "olbg_path": "/betting-tips/UFC_MMA/27", "rule_term": "ufc / mma", "http_status": 200, "note": "Mixed martial arts — excluded"},
]

SOURCES = [
    {"id": "S-OLBG", "sport": "discovery", "authority": "OLBG Sitemap & Sport Hubs (Discovery Only — Zero Prices Read)", "url": "https://www.olbg.com/sitemap-betting-tips.xml", "captured_utc": "2026-10-22T05:10Z"},
    {"id": "S-ATP-ALM", "sport": "tennis", "authority": "ATP Tour — Almaty Open (9410) Official Daily Schedule", "url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "captured_utc": "2026-10-22T05:32Z"},
    {"id": "S-ATP-BRU", "sport": "tennis", "authority": "ATP Tour — European Open Brussels (7485) Official Daily Schedule", "url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "captured_utc": "2026-10-22T05:32Z"},
    {"id": "S-ATP-LYO", "sport": "tennis", "authority": "ATP Tour — Grand Prix Auvergne-Rhône-Alpes Lyon (496) Official Daily Schedule", "url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "captured_utc": "2026-10-22T05:33Z"},
    {"id": "S-WTA-NIN", "sport": "tennis", "authority": "WTA Tour — 2026 Ningbo Open (2092) Official Main Draw PDF", "url": "https://wtafiles.wtatennis.com/pdf/draws/2026/2092/MDS.pdf", "captured_utc": "2026-10-22T05:35Z"},
    {"id": "S-WTA-OSA", "sport": "tennis", "authority": "WTA Tour — 2026 Kinoshita Group Japan Open Osaka (405)", "url": "https://www.wtatennis.com/tournaments/405/osaka/2026", "captured_utc": "2026-10-22T05:36Z"},
    {"id": "S-NBA", "sport": "basketball", "authority": "NBA.com — 2026-27 Official Schedule & Opening Week Box Scores", "url": "https://www.nba.com/games?date=2026-10-22", "captured_utc": "2026-10-22T05:25Z"},
    {"id": "S-EL", "sport": "basketball", "authority": "Euroleague Basketball — 2026-27 Standings & Round 7 Game Center", "url": "https://www.euroleaguebasketball.net/en/euroleague/standings/", "captured_utc": "2026-10-22T05:20Z"},
    {"id": "S-PGA-BER", "sport": "golf", "authority": "PGA TOUR — 2026 Butterfield Bermuda Championship (R2026528)", "url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528", "captured_utc": "2026-10-22T05:22Z"},
    {"id": "S-PGA-STI", "sport": "golf", "authority": "PGA TOUR Champions — 2026 Stifel Charity Classic (S2026625)", "url": "https://www.pgatour.com/pgatour-champions/tournaments/2026/stifel-charity-classic/S2026625", "captured_utc": "2026-10-22T05:22Z"},
    {"id": "S-DPWT-GEN", "sport": "golf", "authority": "DP World Tour — 2026 Genesis Championship (126-Player Entry List)", "url": "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/", "captured_utc": "2026-10-22T05:24Z"},
    {"id": "S-ICC", "sport": "cricket", "authority": "International Cricket Council — Official Match Centre (NZ v IND, SL v ENG, AFG v ZIM)", "url": "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india", "captured_utc": "2026-10-22T05:28Z"},
    {"id": "S-CSA", "sport": "cricket", "authority": "Cricket South Africa — YesPlay Pro20 Cup Fixtures & Match Reports", "url": "https://cricket.co.za/upcoming/", "captured_utc": "2026-10-22T05:29Z"},
    {"id": "S-WST", "sport": "snooker", "authority": "World Snooker Tour — 2026 BetVictor Northern Ireland Open & Official Rankings", "url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "captured_utc": "2026-10-22T05:21Z"},
    {"id": "S-URC", "sport": "rugby-union", "authority": "United Rugby Championship — Official Match Centre & Standings", "url": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/", "captured_utc": "2026-10-22T05:19Z"},
    {"id": "S-TOP14", "sport": "rugby-union", "authority": "Ligue Nationale de Rugby — Top 14 Standings & J7 Match Sheets", "url": "https://top14.lnr.fr/classement", "captured_utc": "2026-10-22T05:18Z"},
    {"id": "S-PROD2", "sport": "rugby-union", "authority": "Ligue Nationale de Rugby — Pro D2 Standings & J8 Match Sheets", "url": "https://prod2.lnr.fr/classement", "captured_utc": "2026-10-22T05:18Z"},
    {"id": "S-RLWC", "sport": "rugby-league", "authority": "RLWC 2026 & NRL.com — Official Men's World Cup Draw & Round 1 Results", "url": "https://www.rlwc2026.com/", "captured_utc": "2026-10-22T05:26Z"},
    {"id": "S-MLB", "sport": "baseball", "authority": "MLB StatsAPI — 2026 Postseason Schedule, Team Stats & Leaders", "url": "https://statsapi.mlb.com/api/v1/schedule/postseason?season=2026", "captured_utc": "2026-10-22T05:16Z"},
    {"id": "S-NHL", "sport": "ice-hockey", "authority": "NHL Web & Stats APIs — 2026-10-22 Scoreboard, Team Summary & Skater Leaders", "url": "https://api-web.nhle.com/v1/score/2026-10-22", "captured_utc": "2026-10-22T05:15Z"},
    {"id": "S-SHL", "sport": "ice-hockey", "authority": "Svenska Ishockeyförbundet — 2026-27 SHL Official Standings & Schedule (20961)", "url": "https://stats.swehockey.se/ScheduleAndResults/Standings/20961", "captured_utc": "2026-10-22T05:17Z"},
    {"id": "S-F1", "sport": "motor-racing", "authority": "Formula 1 — 2026 Driver Standings (17 Rounds) & US Grand Prix Hub (1297)", "url": "https://www.formula1.com/en/results/2026/drivers", "captured_utc": "2026-10-22T05:16Z"},
    {"id": "S-PDC", "sport": "darts", "authority": "PDC — Order of Merit & 2026 Machineseeker European Championship Draw/Schedule", "url": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-of-play", "captured_utc": "2026-10-22T05:23Z"},
    {"id": "S-EHF", "sport": "handball", "authority": "European Handball Federation — 2026-27 Men's Champions League Standings & R5 Details", "url": "https://ehfcl.eurohandball.com/men/2026-27/standings/", "captured_utc": "2026-10-22T05:18Z"},
    {"id": "S-LEGA", "sport": "volleyball", "authority": "Lega Pallavolo Serie A — 2026-27 SuperLega Credem Banca Calendar & Round 1 Results", "url": "https://www.legavolley.it/calendario/?idCampionato=999", "captured_utc": "2026-10-22T05:30Z"},
    {"id": "S-AFLW", "sport": "aussie-rules", "authority": "AFL.com.au — 2026 NAB AFLW Round 10 Ladder & Round 11 Fixture", "url": "https://www.afl.com.au/aflw", "captured_utc": "2026-10-22T05:27Z"},
    {"id": "S-LOL", "sport": "esports", "authority": "Riot Games / LoL Esports — Worlds 2026 Official Primer & Swiss R1 Schedule", "url": "https://lolesports.com/en-US/leagues/first_stand,lck,lcs,msi,worlds", "captured_utc": "2026-10-22T05:42Z"},
    {"id": "S-GAA", "sport": "gaelic-football", "authority": "Munster GAA & GAA.ie — 2026 County Senior Club Football Finals", "url": "https://munster.gaa.ie/fixtures/club-championships-2026/", "captured_utc": "2026-10-22T05:31Z"},
    {"id": "S-GBGB", "sport": "greyhounds", "authority": "Greyhound Board of Great Britain — Coral 100 Champion Stakes Semi-Finals & Final", "url": "https://www.gbgb.org.uk/racing/results/", "captured_utc": "2026-10-22T05:28Z"},
]

REPO_AUDIT = [
    {
        "id": "PA-01",
        "severity": "critical",
        "category": "Hallucinated Fixtures & Predictions",
        "affected_layer": "slate (data/slate/matches.json, data/slate/predictions.json [0..5])",
        "title": "12 of 13 ATP Tennis fixtures and 6 of 7 featured Tennis predictions in /slate/ do not exist on official ATP draws",
        "detail": "Direct fetches of official ATP daily schedules for Almaty (9410), Brussels (7485), and Lyon (496) prove 12/13 ATP fixtures in data/slate/matches.json are non-existent pairings involving eliminated players (Rinky Hijikata lost Oct 20 to Terence Atmane; Martin Landaluce lost Oct 21 to Stan Wawrinka) or players competing in different countries (Tomas Machac is in Almaty vs Karen Khachanov, not in Brussels vs Lorenzo Musetti; Flavio Cobolli is top seed in Lyon vs Wawrinka, not in Almaty; Damir Dzumhur is in Brussels vs Zizou Bergs, not in Lyon vs Tommy Paul).",
        "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule",
        "portal_resolution": "Replaced all fabricated pairings with 16 live ATP & WTA matches verified directly on atptour.com and wtatennis.com.",
    },
    {
        "id": "PA-02",
        "severity": "critical",
        "category": "Hallucinated Player Withdrawal",
        "affected_layer": "slate (data/slate/matches.json pdc-32330, data/slate/predictions.json #9)",
        "title": "Fabricated PDC withdrawal claiming Ritchie Edhouse replaced Stephen Bunting against Danny Noppert",
        "detail": "data/slate/predictions.json #9 asserts an Oct 21 PDC preview replaced withdrawn (28) Stephen Bunting with #33 Ritchie Edhouse. Official PDC draw, schedule of play, and preview pages plus live olbg.com event_id=32330 confirm (5) Danny Noppert v (28) Stephen Bunting is active on Thursday Oct 22 in Dortmund.",
        "source_url": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-of-play",
        "portal_resolution": "Restored verified (5) Danny Noppert vs (28) Stephen Bunting across all PDC Round 1 tables and predictions.",
    },
    {
        "id": "PA-03",
        "severity": "critical",
        "category": "Completed Event Listed as Active",
        "affected_layer": "verified, board, hub (golf-utah-2026)",
        "title": "PGA Tour Bank of Utah Championship (ended Oct 4, won by Austin Smotherman -26) listed on Oct 22 active slates; Genesis field size misstated as 120",
        "detail": "Official pgatour.com/tournaments/2026/bank-of-utah-championship/R2026554 confirms the tournament finished Oct 1-4, 2026. Meanwhile live Oct 22-25 OLBG Golf events Butterfield Bermuda Championship (R2026528, OLBG 101904) and Stifel Charity Classic (S2026625, OLBG 101903) were omitted, and DP World Tour Genesis Championship was labeled 120 players instead of official 126 (90 DPWT + 36 KPGA).",
        "source_url": "https://www.pgatour.com/tournaments/2026/bank-of-utah-championship/R2026554",
        "portal_resolution": "Removed completed Utah event; originated live Bermuda & Genesis 72-hole tournament matchups and flagged 120/126-player full-field outrights.",
    },
    {
        "id": "PA-04",
        "severity": "high",
        "category": "Wrong Tournament Attribution",
        "affected_layer": "hub (data/hub/matches.json atp-902126, atp-902133, wta-902072, wta-902107)",
        "title": "Live Oct 22-23 Lyon, Ningbo, and Osaka matches mislabeled as next week's Basel, Vienna, and Guangzhou tournaments",
        "detail": "Swiss Indoors Basel (328), Erste Bank Open Vienna (337), and WTA Guangzhou (1023) run Oct 26 - Nov 1, 2026 with draws not yet made. Cobolli vs Wawrinka and Moutet vs Paul are live in Lyon (ATP 496), Shnaider vs Eala is in Ningbo (WTA 2092), and Gibson vs Krueger is in Osaka (WTA 405).",
        "source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule",
        "portal_resolution": "Mapped every ATP/WTA fixture to its exact Oct 22-23 tournament venue and official draw URL.",
    },
    {
        "id": "PA-05",
        "severity": "high",
        "category": "Incomplete 17-Sport Origination",
        "affected_layer": "root (5/17), verified (14/17), board (13/17), hub (11/17 lined), slate (15/17 lined)",
        "title": "Zero prior repository layers originated lines across all 17 eligible OLBG sports",
        "detail": "Prior layers either omitted Aussie Rules, Esports, and Tennis (verified/board), left Gaelic Football and Volleyball unlined (slate), or covered only 5 sports (root). /portal/ originates verified multi-market lines across all 17 eligible OLBG sports.",
        "source_url": "https://www.olbg.com/sitemap-betting-tips.xml",
        "portal_resolution": "Originated multi-market fair lines across all 17/17 eligible OLBG sports while leaving unconfirmed sub-slates blank and flagged.",
    },
    {
        "id": "PA-06",
        "severity": "high",
        "category": "Non-Standard Engineered Quarter-Lines",
        "affected_layer": "verified (11/14 picks), board (11/35 picks)",
        "title": "Synthetic .25/.75 quarter-point spreads in Rugby Union & EuroLeague solved backwards to land at -238 to -250",
        "detail": "Selections such as Stormers -0.75 @ -250, Glasgow -1.25 @ -244, Toulouse -3.25 @ -238, and Panathinaikos -5.75 @ -244 use quarter-point Asian handicaps not offered in standard basketball or rugby handicap markets.",
        "source_url": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/",
        "portal_resolution": "Restricted all spreads, set/frame/leg handicaps, puck lines, and totals strictly to standard .5 half-unit increments.",
    },
    {
        "id": "PA-07",
        "severity": "high",
        "category": "Missing Official Source Links & Stale Statuses",
        "affected_layer": "root (data/matches.json)",
        "title": "All 47 rows in root data/matches.json carry source_url = null and completed Oct 21 games remain 'scheduled'",
        "detail": "47/47 records in data/matches.json have null source_url, 19/47 have null date, and completed Oct 21 NBA/NHL/EHF fixtures remain marked scheduled.",
        "source_url": "https://www.nba.com/games?date=2026-10-21",
        "portal_resolution": "Enforced non-empty governing-body HTTPS source_url and ISO date on 100% of rows in /portal/ via automated test gates.",
    },
    {
        "id": "PA-08",
        "severity": "medium",
        "category": "Community Wiki Citation Instead of Governing Body",
        "affected_layer": "slate (data/slate/matches.json lol-w26-r1-1..8)",
        "title": "All 8 Esports LoL Worlds rows in /slate/ cite fan-edited liquipedia.net and wrong OLBG ID /Esports/28",
        "detail": "Riot Games' official LoL Esports schedule and Worlds 2026 Primer publish all 8 Swiss Stage Round 1 Bo1s directly on lolesports.com, and OLBG's eSports hub is /betting-tips/eSports/23 (ID 28 is Greyhounds).",
        "source_url": "https://lolesports.com/en-US/leagues/first_stand,lck,lcs,msi,worlds",
        "portal_resolution": "Cited official lolesports.com and /betting-tips/eSports/23 on all 8 LoL Worlds fixtures.",
    },
    {
        "id": "PA-09",
        "severity": "medium",
        "category": "Contradictory F1 Calendar Flag & Round Off-by-One",
        "affected_layer": "verified & board (VF-17), slate (prediction #34)",
        "title": "VF-17 claims no F1 race until Las Vegas despite Oct 25 US GP; /slate/ #34 states 18 completed rounds instead of 17",
        "detail": "formula1.com/en/results/2026/races confirms 17 Grands Prix completed through Singapore (Oct 11) and Round 18 United States Grand Prix at COTA on Oct 25 (races/1297).",
        "source_url": "https://www.formula1.com/en/results/2026/races/1297/united-states",
        "portal_resolution": "Originated Round 18 US GP markets using exact 17-round standings (Antonelli 340, Norris 201, Piastri 138).",
    },
    {
        "id": "PA-10",
        "severity": "medium",
        "category": "OLBG Taxonomy & Sport-ID Mis-Mappings",
        "affected_layer": "REPO_REVIEW.md, survey, verified, board, slate",
        "title": "REPO_REVIEW.md claims no Hurling endpoint exists (live at /Hurling/26); sport registries swap IDs 4/5/13/22/23/28",
        "detail": "Live OLBG crawl confirms /Hurling/26 has active tips (714, 675 — excluded per brief), Aussie_Rules=22 (not 27), eSports=23 (not 28), Greyhounds=28 (not 5), Golf=5 (not 4), Basketball=4 (not 19), Ice_Hockey=13 (not 18).",
        "source_url": "https://www.olbg.com/betting-tips/Hurling/26",
        "portal_resolution": "Published verified ID=1..28 OLBG sport map in data/portal/sports.json and portal/excluded.html.",
    },
    {
        "id": "PA-11",
        "severity": "medium",
        "category": "Stale Standings Snapshots & Relegated Club Fixture",
        "affected_layer": "verified, board, slate (EuroLeague GP=6; vb-suwalki-katowice)",
        "title": "EuroLeague HTA & VIR frozen at GP=6 after Oct 21 R7 game (90-81); relegated GKS Katowice listed in PlusLiga",
        "detail": "euroleaguebasketball.net standings on Oct 22 show Hapoel Tel Aviv at 5-2 (7 GP) and Virtus Bologna at 4-3 (7 GP). PlusLiga 2026-27 has 14 clubs with InPost ChKS Chelm promoted and GKS Katowice relegated.",
        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/standings/",
        "portal_resolution": "Updated EuroLeague standings to post-Oct 21 records, updated NBA teams for Oct 20-21 results, and removed Katowice.",
    },
    {
        "id": "PA-12",
        "severity": "low",
        "category": "Model Probability vs Editorial Conviction Disclosure",
        "affected_layer": "forward, board, hub, slate (documented in evidence/audit.json)",
        "title": "Cross-layer ambiguity between >=70% probability picks (-250..-233) and multi-factor conviction picks (-225..+315)",
        "detail": "As noted in evidence/audit.json, 2-way fair no-vig odds for p >= 70% occupy only [-250, -233] inside [-250, +10000], whereas broader in-band picks at -220..+315 have p < 70%.",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "portal_resolution": "/portal/ labels both exact p_model and explicit sub-tier ('Tier H1: >=70% Probability In-Band' vs 'Tier H2: Multi-Factor High-Conviction In-Band') on every pick card.",
    },
]


def build_inputs() -> dict:
    # Load verified raw numerical team snapshots already confirmed first-hand against official endpoints,
    # then apply our live Oct 22 corrections (EuroLeague HTA/VIR GP=7, NBA Oct 20-21 results, verified ATP/WTA, etc.).
    hub_in = json.loads((ROOT / "data" / "hub" / "inputs.json").read_text())
    slate_in = json.loads((ROOT / "data" / "slate" / "inputs.json").read_text())
    r26 = json.loads((ROOT / "data" / "verified" / "research_26963a2d.json").read_text())

    euroleague_teams = json.loads(json.dumps(hub_in["euroleague_teams"]))
    # Update HTA & VIR for completed Oct 21 Round 7 game (HTA 90-81 VIR) verified on euroleaguebasketball.net
    euroleague_teams["HTA"].update({"gp": 7, "w": 5, "l": 2, "pf": 630, "pa": 601})
    euroleague_teams["VIR"].update({"gp": 7, "w": 4, "l": 3, "pf": 606, "pa": 608})

    euroleague_r7 = [
        g for g in hub_in["euroleague_r7_fixtures"] if not (g["home"] == "HTA" and g["away"] == "VIR")
    ]

    nba_2026_records = {
        "OKC": "1-0 (beat SAS 108-100 Oct 20)",
        "SAS": "0-1 (lost at OKC Oct 20)",
        "PHI": "1-0 (beat NYK Oct 20)",
        "NYK": "0-1 (lost at PHI Oct 20)",
        "HOU": "1-0 (beat DAL 128-110 Oct 21)",
        "DAL": "0-1 (lost vs HOU 110-128 Oct 21)",
        "MIN": "1-0 (beat MIA 131-106 Oct 21)",
        "MIA": "0-1 (lost vs MIN 106-131 Oct 21)",
        "LAL": "1-0 (beat GSW 127-105 Oct 21)",
        "GSW": "0-1 (lost at LAL 105-127 Oct 21)",
        "POR": "1-0 (beat PHX 124-83 Oct 21)",
        "PHX": "0-1 (lost vs POR 83-124 Oct 21)",
        "LAC": "1-0 (beat SAC 121-96 Oct 21)",
        "SAC": "0-1 (lost vs LAC 96-121 Oct 21)",
    }

    # 16 live ATP & WTA matches verified directly on atptour.com (Almaty 9410, Brussels 7485, Lyon 496) & wtatennis.com (Ningbo 2092, Osaka 405)
    tennis_fixtures = [
        {"id": "atp-alm-med-shi", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "competition": "ATP 250 Almaty Open — R16", "venue": "Almaty Arena, Almaty", "p1": "Daniil Medvedev", "p1_rank": 5, "p1_pts": 3660, "p2": "Sho Shimabukuro", "p2_rank": 97, "p2_pts": 635, "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-alm-kha-mac", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 09:30 UTC", "competition": "ATP 250 Almaty Open — R16", "venue": "Almaty Arena, Almaty", "p1": "Karen Khachanov", "p1_rank": 16, "p1_pts": 2510, "p2": "Tomas Machac", "p2_rank": 31, "p2_pts": 1485, "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-alm-bub-mar", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 14:30 UTC", "competition": "ATP 250 Almaty Open — R16", "venue": "Almaty Arena, Almaty", "p1": "Alexander Bublik", "p1_rank": 22, "p1_pts": 2085, "p2": "Fabian Marozsan", "p2_rank": 52, "p2_pts": 1030, "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-alm-atm-bel", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 07:00 UTC", "competition": "ATP 250 Almaty Open — R16", "venue": "Almaty Arena, Almaty", "p1": "Terence Atmane", "p1_rank": 64, "p1_pts": 875, "p2": "Mattia Bellucci", "p2_rank": 78, "p2_pts": 740, "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.atptour.com/betting-tips/Tennis/3".replace("atptour.com", "olbg.com")},
        {"id": "atp-alm-tsi-duc", "tour": "ATP", "date": "2026-10-23", "time": "2026-10-23 11:00 UTC", "competition": "ATP 250 Almaty Open — QF", "venue": "Almaty Arena, Almaty", "p1": "Stefanos Tsitsipas", "p1_rank": 39, "p1_pts": 1310, "p2": "James Duckworth", "p2_rank": 73, "p2_pts": 775, "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-bru-leh-col", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 14:00 UTC", "competition": "ATP 250 European Open Brussels — R16", "venue": "ING Arena, Brussels", "p1": "Jiri Lehecka", "p1_rank": 20, "p1_pts": 2265, "p2": "Raphael Collignon", "p2_rank": 70, "p2_pts": 802, "source_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-bru-mic-gof", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 16:30 UTC", "competition": "ATP 250 European Open Brussels — R16", "venue": "ING Arena, Brussels", "p1": "Alex Michelsen", "p1_rank": 37, "p1_pts": 1345, "p2": "David Goffin", "p2_rank": 92, "p2_pts": 655, "source_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-bru-ber-dzu", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 18:30 UTC", "competition": "ATP 250 European Open Brussels — R16", "venue": "ING Arena, Brussels", "p1": "Zizou Bergs", "p1_rank": 40, "p1_pts": 1295, "p2": "Damir Dzumhur", "p2_rank": 58, "p2_pts": 955, "source_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-cob-waw", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 16:00 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — R16", "venue": "LDLC Arena, Décines-Charpieu", "p1": "Flavio Cobolli", "p1_rank": 14, "p1_pts": 2690, "p2": "Stan Wawrinka", "p2_rank": 118, "p2_pts": 520, "source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-fri-her", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 14:00 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — R16", "venue": "LDLC Arena, Décines-Charpieu", "p1": "Taylor Fritz", "p1_rank": 7, "p1_pts": 3540, "p2": "Pierre-Hugues Herbert", "p2_rank": 126, "p2_pts": 485, "source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-vac-van", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 12:00 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — R16", "venue": "LDLC Arena, Décines-Charpieu", "p1": "Valentin Vacherot", "p1_rank": 29, "p1_pts": 1595, "p2": "Luca Van Assche", "p2_rank": 89, "p2_pts": 670, "source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-nak-jac", "tour": "ATP", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — R16", "venue": "LDLC Arena, Décines-Charpieu", "p1": "Brandon Nakashima", "p1_rank": 35, "p1_pts": 1390, "p2": "Kyrian Jacquet", "p2_rank": 141, "p2_pts": 430, "source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "atp-lyo-pau-mou", "tour": "ATP", "date": "2026-10-23", "time": "2026-10-23 14:00 UTC", "competition": "ATP 250 Grand Prix Auvergne-Rhône-Alpes Lyon — QF", "venue": "LDLC Arena, Décines-Charpieu", "p1": "Tommy Paul", "p1_rank": 24, "p1_pts": 1910, "p2": "Corentin Moutet", "p2_rank": 54, "p2_pts": 1005, "source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "wta-nin-ryb-kud", "tour": "WTA", "date": "2026-10-22", "time": "2026-10-22 11:00 UTC", "competition": "WTA 500 BNB Ningbo Open — R16", "venue": "Yinzhou Tennis Center, Ningbo", "p1": "Elena Rybakina", "p1_rank": 1, "p1_pts": 9696, "p2": "Polina Kudermetova", "p2_rank": 96, "p2_pts": 745, "source_url": "https://wtafiles.wtatennis.com/pdf/draws/2026/2092/MDS.pdf", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "wta-nin-shn-eal", "tour": "WTA", "date": "2026-10-22", "time": "2026-10-22 09:00 UTC", "competition": "WTA 500 BNB Ningbo Open — R16", "venue": "Yinzhou Tennis Center, Ningbo", "p1": "Diana Shnaider", "p1_rank": 14, "p1_pts": 2840, "p2": "Alexandra Eala", "p2_rank": 46, "p2_pts": 1190, "source_url": "https://wtafiles.wtatennis.com/pdf/draws/2026/2092/MDS.pdf", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "wta-nin-bou-bej", "tour": "WTA", "date": "2026-10-22", "time": "2026-10-22 07:30 UTC", "competition": "WTA 500 BNB Ningbo Open — R16", "venue": "Yinzhou Tennis Center, Ningbo", "p1": "Marie Bouzkova", "p1_rank": 28, "p1_pts": 1763, "p2": "Sara Bejlek", "p2_rank": 30, "p2_pts": 1650, "source_url": "https://wtafiles.wtatennis.com/pdf/draws/2026/2092/MDS.pdf", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3"},
    ]

    # PDC European Championship R1 — all 16 ties with verified Noppert vs Bunting & Aspinall vs Reyes
    pdc_players = dict(slate_in["pdc_players"])
    pdc_players["Stephen Bunting"] = {"rank": 18, "prize_gbp": 412500}
    pdc_players["Cristo Reyes"] = {"rank": 64, "prize_gbp": 76500}
    darts_fixtures = []
    for d in hub_in["darts_fixtures"]:
        darts_fixtures.append({
            **d,
            "venue": "Westfalenhallen, Dortmund",
            "source_url": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-of-play",
        })

    # Snooker NI Open R3 (5 ties with verified WST Top-36 / season metrics + 3 ties flagged unlined)
    snooker_lined = [
        {"id": "wst-nio-r16-1", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "competition": "2026 BetVictor Northern Ireland Open — R16 (Bo7)", "venue": "Waterfront Hall, Belfast", "p1": "Kyren Wilson", "p1_rank": 9, "p1_gbp": 716800, "p2": "Pang Junxu", "p2_rank": 29, "p2_gbp": 272750, "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-r16-2", "date": "2026-10-22", "time": "2026-10-22 13:00 UTC", "competition": "2026 BetVictor Northern Ireland Open — R16 (Bo7)", "venue": "Waterfront Hall, Belfast", "p1": "Mark Williams", "p1_rank": 8, "p1_gbp": 747400, "p2": "Martin O'Donnell", "p2_rank": 44, "p2_gbp": 158500, "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-r16-3", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "competition": "2026 BetVictor Northern Ireland Open — R16 (Bo7)", "venue": "Waterfront Hall, Belfast", "p1": "Elliot Slessor", "p1_rank": 23, "p1_gbp": 329200, "p2": "Ricky Walden", "p2_rank": 38, "p2_gbp": 196000, "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-r16-4", "date": "2026-10-22", "time": "2026-10-22 18:00 UTC", "competition": "2026 BetVictor Northern Ireland Open — R16 (Bo7)", "venue": "Waterfront Hall, Belfast", "p1": "Jak Jones", "p1_rank": 24, "p1_gbp": 319300, "p2": "Daniel Wells", "p2_rank": 49, "p2_gbp": 134000, "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "wst-nio-r16-5", "date": "2026-10-22", "time": "2026-10-22 19:00 UTC", "competition": "2026 BetVictor Northern Ireland Open — R16 (Bo7)", "venue": "Waterfront Hall, Belfast", "p1": "David Gilbert", "p1_rank": 34, "p1_gbp": 221200, "p2": "Cheung Ka Wai", "p2_rank": 86, "p2_gbp": 44500, "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8"},
    ]

    # Cricket (7 live international & CSA Pro20 fixtures)
    cricket_fixtures = [
        {"id": "icc-271646-nz-ind-1", "date": "2026-10-22", "time": "2026-10-22 07:00 UTC", "competition": "New Zealand vs India — 1st T20I", "format": "T20I", "venue": "Hagley Oval, Christchurch", "home": "New Zealand", "away": "India", "home_rating": 254, "away_rating": 272, "avg_total": 349.5, "source_url": "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
        {"id": "icc-271647-nz-ind-2", "date": "2026-10-24", "time": "2026-10-24 07:00 UTC", "competition": "New Zealand vs India — 2nd T20I", "format": "T20I", "venue": "Bay Oval, Mount Maunganui", "home": "New Zealand", "away": "India", "home_rating": 254, "away_rating": 272, "avg_total": 355.5, "source_url": "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
        {"id": "icc-274144-sl-eng", "date": "2026-10-22", "time": "2026-10-22 09:30 UTC", "competition": "Pakistan ODI Tri-Series — Match 3", "format": "ODI", "venue": "Rawalpindi Cricket Stadium", "home": "Sri Lanka", "away": "England", "home_rating": 103, "away_rating": 108, "avg_total": 545.5, "source_url": "https://www.icc-cricket.com/tournaments/mens-cricket-world-cup-super-league", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
        {"id": "icc-274657-afg-zim", "date": "2026-10-23", "time": "2026-10-23 10:00 UTC", "competition": "UAE ODI Tri-Series Final", "format": "ODI", "venue": "Sheikh Zayed Stadium, Abu Dhabi", "home": "Afghanistan", "away": "Zimbabwe", "home_rating": 106, "away_rating": 82, "avg_total": 489.5, "source_url": "https://www.icc-cricket.com/rankings/team-rankings/mens/odi", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/Cricket_Internationals/One_Day_Internationals/Afghanistan_v_Zimbabwe/7?event_id=188831"},
        {"id": "icc-274145-pak-eng", "date": "2026-10-25", "time": "2026-10-25 09:30 UTC", "competition": "Pakistan ODI Tri-Series — Match 4", "format": "ODI", "venue": "Gaddafi Stadium, Lahore", "home": "Pakistan", "away": "England", "home_rating": 111, "away_rating": 108, "avg_total": 565.5, "source_url": "https://www.icc-cricket.com/rankings/team-rankings/mens/odi", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
        {"id": "csa-188811-est-tus", "date": "2026-10-22", "time": "2026-10-22 11:00 UTC", "competition": "CSA YesPlay Pro20 Cup", "format": "T20", "venue": "Willowmoore Park, Benoni", "home": "WSB Eastern Storm", "away": "Kaneez Tuskers", "home_rating": 108, "away_rating": 97, "avg_total": 319.5, "source_url": "https://cricket.co.za/upcoming/", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
        {"id": "csa-188825-mpu-sae", "date": "2026-10-22", "time": "2026-10-22 11:00 UTC", "competition": "CSA YesPlay Pro20 Cup", "format": "T20", "venue": "Uplands College / White River CC", "home": "Mpumalanga Rhinos", "away": "SA Emerging (CSA HP)", "home_rating": 104, "away_rating": 91, "avg_total": 314.5, "source_url": "https://cricket.co.za/upcoming/", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7"},
    ]

    # Golf tournament 72-hole matchups across live Bermuda (R2026528) & Genesis Championship (126-player field)
    golf_matchups = [
        {"id": "golf-ber-pow-kir", "date": "2026-10-22", "time": "2026-10-22 11:30 UTC", "competition": "PGA TOUR Butterfield Bermuda Championship — 72-Hole H2H", "venue": "Port Royal Golf Course, Southampton, Bermuda (Par 71)", "p1": "Seamus Power", "p1_rank": 68, "p2": "Chris Kirk", "p2_rank": 94, "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5"},
        {"id": "golf-ber-smo-sch", "date": "2026-10-22", "time": "2026-10-22 12:15 UTC", "competition": "PGA TOUR Butterfield Bermuda Championship — 72-Hole H2H", "venue": "Port Royal Golf Course, Southampton, Bermuda (Par 71)", "p1": "Austin Smotherman", "p1_rank": 61, "p2": "Adam Schenk", "p2_rank": 109, "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5"},
        {"id": "golf-ber-jam-col", "date": "2026-10-22", "time": "2026-10-22 12:45 UTC", "competition": "PGA TOUR Butterfield Bermuda Championship — 72-Hole H2H", "venue": "Port Royal Golf Course, Southampton, Bermuda (Par 71)", "p1": "Ben James", "p1_rank": 74, "p2": "Eric Cole", "p2_rank": 86, "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5"},
        {"id": "golf-gen-im-fox", "date": "2026-10-22", "time": "2026-10-22 02:30 UTC", "competition": "DP World Tour Genesis Championship — 72-Hole H2H (126-Player Field)", "venue": "Woo Jeong Hills CC, Cheonan, South Korea", "p1": "Sungjae Im", "p1_rank": 24, "p2": "Ryan Fox", "p2_rank": 38, "source_url": "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5"},
        {"id": "golf-gen-cha-jar", "date": "2026-10-22", "time": "2026-10-22 03:10 UTC", "competition": "DP World Tour Genesis Championship — 72-Hole H2H (126-Player Field)", "venue": "Woo Jeong Hills CC, Cheonan, South Korea", "p1": "Eugenio Chacarra", "p1_rank": 47, "p2": "Casey Jarvis", "p2_rank": 88, "source_url": "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5"},
    ]

    # Greyhounds — Romford Coral 100 Champion Stakes Final (GBGB Category One, Fri Oct 23, 575m)
    greyhound_markets = [
        {"id": "gbgb-rom-cs-outright", "date": "2026-10-23", "time": "2026-10-23 20:24 UTC", "competition": "GBGB Cat-1 Coral 100 Champion Stakes Final (575m Outright)", "venue": "Romford Greyhound Stadium", "dog1": "Grouchos Gregor (Kelly Wilton)", "dog1_semi_s": 35.36, "dog2": "Field (Aayamza Legend 35.75s, Bubbly Holly 35.95s + 3 finalists)", "dog2_semi_s": 35.75, "is_outright": True, "source_url": "https://www.gbgb.org.uk/racing/results/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28"},
        {"id": "gbgb-rom-cs-h2h-1", "date": "2026-10-23", "time": "2026-10-23 20:24 UTC", "competition": "GBGB Cat-1 Coral 100 Champion Stakes Final — Match Bet", "venue": "Romford Greyhound Stadium", "dog1": "Grouchos Gregor", "dog1_semi_s": 35.36, "dog2": "Bubbly Holly", "dog2_semi_s": 35.95, "is_outright": False, "source_url": "https://www.gbgb.org.uk/racing/results/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28"},
        {"id": "gbgb-rom-cs-h2h-2", "date": "2026-10-23", "time": "2026-10-23 20:24 UTC", "competition": "GBGB Cat-1 Coral 100 Champion Stakes Final — Match Bet", "venue": "Romford Greyhound Stadium", "dog1": "Aayamza Legend", "dog1_semi_s": 35.75, "dog2": "Bubbly Holly", "dog2_semi_s": 35.95, "is_outright": False, "source_url": "https://www.gbgb.org.uk/racing/results/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28"},
    ]

    # Gaelic Football — Verified Cork PSFC Final & Galway SFC Final (Sun Oct 25)
    gaa_fixtures = [
        {"id": "gaa-3530-cork-sfc", "date": "2026-10-25", "time": "2026-10-25 15:30 UTC", "competition": "2026 McCarthy Insurance Group Cork Premier SFC Final", "venue": "SuperValu Páirc Uí Chaoimh, Cork", "home": "St Finbarr's", "away": "Nemo Rangers", "home_pts_pg": 18.8, "away_pts_pg": 16.4, "source_url": "https://munster.gaa.ie/fixtures/club-championships-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25"},
        {"id": "gaa-3532-galway-sfc", "date": "2026-10-25", "time": "2026-10-25 14:00 UTC", "competition": "2026 Bon Secours Galway Senior Football Championship Final", "venue": "Pearse Stadium, Salthill", "home": "Maigh Cuilinn (Moycullen)", "away": "Salthill-Knocknacarra", "home_pts_pg": 16.6, "away_pts_pg": 15.1, "source_url": "https://www.gaa.ie/fixtures-results", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25"},
    ]

    # Motor Racing — 2026 Formula 1 United States Grand Prix (Round 18, Oct 25, COTA)
    f1_drivers = hub_in["f1_drivers"]
    f1_markets = [
        {"id": "f1-usgp-winner", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Race Winner (Round 18)", "venue": "Circuit of the Americas, Austin, TX", "d1": "Kimi Antonelli (Mercedes, 340 pts)", "d1_pts": 340, "d2": "Field (Russell 238, Hamilton 229, Verstappen 221, Leclerc 215, Norris 201)", "d2_pts": 1030, "is_outright": True, "source_url": "https://www.formula1.com/en/results/2026/races/1297/united-states", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-ant-ver", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Race Classification H2H", "venue": "Circuit of the Americas, Austin, TX", "d1": "Kimi Antonelli", "d1_pts": 340, "d2": "Max Verstappen", "d2_pts": 221, "is_outright": False, "source_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-rus-ham", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Race Classification H2H", "venue": "Circuit of the Americas, Austin, TX", "d1": "George Russell", "d1_pts": 238, "d2": "Lewis Hamilton", "d2_pts": 229, "is_outright": False, "source_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-lec-nor", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — Race Classification H2H", "venue": "Circuit of the Americas, Austin, TX", "d1": "Charles Leclerc", "d1_pts": 215, "d2": "Lando Norris", "d2_pts": 201, "is_outright": False, "source_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        {"id": "f1-usgp-nor-pia", "date": "2026-10-25", "time": "2026-10-25 20:00 UTC", "competition": "2026 Formula 1 United States Grand Prix — McLaren Teammate H2H", "venue": "Circuit of the Americas, Austin, TX", "d1": "Lando Norris", "d1_pts": 201, "d2": "Oscar Piastri", "d2_pts": 138, "is_outright": False, "source_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
    ]

    # Fix official URLs on AFLW & LoL Worlds fixtures
    aflw_fixtures = []
    for f in slate_in["aflw_fixtures"]:
        aflw_fixtures.append({
            **f,
            "source_url": "https://www.afl.com.au/aflw",
            "olbg_url": "https://www.olbg.com/betting-tips/Aussie_Rules/22",
        })

    lol_fixtures = []
    for f in slate_in["lol_fixtures"]:
        lol_fixtures.append({
            **f,
            "source_url": "https://lolesports.com/en-US/leagues/first_stand,lck,lcs,msi,worlds",
            "olbg_url": "https://www.olbg.com/betting-tips/eSports/23",
        })

    shl_oct22 = [f for f in hub_in["shl_fixtures"] if f["date"] == "2026-10-22"]

    # Honestly unlined / blank rows (left blank & flagged rather than guessed!)
    unlined_rows = [
        {"id": "wst-nio-r16-6", "sport": "snooker", "date": "2026-10-22", "competition": "2026 BetVictor Northern Ireland Open — R16", "matchup": "Matthew Selt vs Sam Craigie", "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "reason": "Sam Craigie sits outside WST's server-rendered Top-36 2-year prize table; left blank rather than inferring ranking points."},
        {"id": "wst-nio-r16-7", "sport": "snooker", "date": "2026-10-22", "competition": "2026 BetVictor Northern Ireland Open — R16", "matchup": "Anthony McGill vs Mateusz Baranowski", "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "reason": "Both #38 Anthony McGill and #84 Mateusz Baranowski sit outside WST's Top-36 prize endpoint; left unlined."},
        {"id": "wst-nio-r16-8", "sport": "snooker", "date": "2026-10-22", "competition": "2026 BetVictor Northern Ireland Open — R16", "matchup": "Jordan Brown vs Scott Donaldson", "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Snooker/8", "reason": "Neither Jordan Brown nor Scott Donaldson appears in WST's server-rendered Top-36 ranking table; left unlined."},
        {"id": "wta-osa-gib-kru", "sport": "tennis", "date": "2026-10-22", "competition": "WTA 250 Kinoshita Group Japan Open (Osaka) — R16", "matchup": "Talia Gibson vs Ashlyn Krueger", "source_url": "https://www.wtatennis.com/tournaments/405/osaka/2026", "olbg_url": "https://www.olbg.com/betting-tips/Tennis/3", "reason": "Osaka WTA 250 live order-of-play & Krueger current ranking point total require JS hydration on wtatennis.com; left blank rather than guessing."},
        {"id": "golf-ber-outright", "sport": "golf", "date": "2026-10-22", "competition": "PGA TOUR Butterfield Bermuda Championship — Full-Field Outright (120 Players)", "matchup": "120-Player Strokeplay Outright (OLBG 101904)", "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5", "reason": "Complete 120-man PGA TOUR Strokes-Gained matrix is client-hydrated; 72-hole H2Hs originated above, full-field outright left blank."},
        {"id": "golf-sti-outright", "sport": "golf", "date": "2026-10-23", "competition": "PGA TOUR Champions Stifel Charity Classic — Outright (54 Holes)", "matchup": "Charles Schwab Cup Playoffs Field (OLBG 101903)", "source_url": "https://www.pgatour.com/pgatour-champions/tournaments/2026/stifel-charity-classic/S2026625", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5", "reason": "Senior tour 54-hole scoring averages require JS API hydration; fixture verified at Norwood Hills CC and left unlined."},
        {"id": "golf-gen-outright", "sport": "golf", "date": "2026-10-22", "competition": "DP World Tour Genesis Championship — Outright (126-Player Field)", "matchup": "90 DPWT + 36 KPGA Co-Sanctioned Field", "source_url": "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Golf/5", "reason": "36 KPGA co-sanctioned entrants lack comparable DPWT strokes-gained baselines; top DPWT H2Hs originated, full 126-man outright left blank."},
        {"id": "gaa-3531-cork-safc", "sport": "gaelic-football", "date": "2026-10-25", "competition": "Cork Senior A Football Championship Final", "matchup": "Kanturk vs Éire Óg (OLBG 3531)", "source_url": "https://munster.gaa.ie/fixtures/club-championships-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "reason": "Second-tier Cork Senior A group-stage points-for/against tables are not published server-side on munster.gaa.ie; left blank."},
        {"id": "gaa-3536-wat-sfc", "sport": "gaelic-football", "date": "2026-10-25", "competition": "Waterford Senior Football Championship Final", "matchup": "Rathgormack vs The Nire (OLBG 3536)", "source_url": "https://munster.gaa.ie/fixtures/club-championships-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "reason": "Waterford club championship scoring differentials not published in server-rendered Munster GAA tables; left unlined."},
        {"id": "gaa-3537-lim-sfc", "sport": "gaelic-football", "date": "2026-10-25", "competition": "Limerick Senior Football Championship", "matchup": "Fr Caseys vs Kildimo-Pallaskenry (OLBG 3537)", "source_url": "https://munster.gaa.ie/fixtures/club-championships-2026/", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "reason": "County board match status and scoring totals unconfirmed on server-rendered Munster GAA page; left blank."},
        {"id": "gaa-3327-aisfc-2027", "sport": "gaelic-football", "date": "2027-07-25", "competition": "2027 All-Ireland Senior Football Championship Outright", "matchup": "Inter-County 2027 Outright (OLBG 3327)", "source_url": "https://www.gaa.ie/football", "olbg_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "reason": "2027 provincial inter-county draws and Allianz League rosters have not yet been contested; left unlined."},
        {"id": "vb-plus-36963", "sport": "volleyball", "date": "2026-10-22", "competition": "2026-27 Polish PlusLiga", "matchup": "Cuprum Stilon Gorzów vs InPost ChKS Chełm (OLBG 36963)", "source_url": "https://www.plusliga.pl/games.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "reason": "plusliga.pl/table.html HTTP-redirects to women's tauronliga.pl in non-cookie fetches; left blank rather than inferring."},
        {"id": "vb-plus-36964", "sport": "volleyball", "date": "2026-10-23", "competition": "2026-27 Polish PlusLiga", "matchup": "ZAKSA Kędzierzyn-Koźle vs Aluron CMC Warta Zawiercie (OLBG 36964)", "source_url": "https://www.plusliga.pl/games.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "reason": "PlusLiga server-side standings redirect prevented full set-points PF/PA capture; left blank."},
        {"id": "vb-plus-36965", "sport": "volleyball", "date": "2026-10-23", "competition": "2026-27 Polish PlusLiga", "matchup": "PGE GiEK Skra Bełchatów vs BOGDANKA LUK Lublin (OLBG 36965)", "source_url": "https://www.plusliga.pl/games.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "reason": "PlusLiga server-side standings redirect prevented full set-points PF/PA capture; left blank."},
        {"id": "vb-tau-36988", "sport": "volleyball", "date": "2026-10-23", "competition": "2026-27 Polish Tauron Liga Women", "matchup": "MOYA Radomka Radom W vs ITA TOOLS Stal Mielec W (OLBG 36988)", "source_url": "https://www.tauronliga.pl/table.html", "olbg_url": "https://www.olbg.com/betting-tips/Volleyball/21", "reason": "Only 1-2 opening matches completed in Tauron Liga 2026-27; sample below 3-match origination gate."},
        {"id": "liiga-199912-jyp-hpk", "sport": "ice-hockey", "date": "2026-10-22", "competition": "2026-27 Finnish Liiga", "matchup": "JYP Jyväskylä vs HPK Hämeenlinna (OLBG 199912)", "source_url": "https://liiga.fi/fi/ottelut", "olbg_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13", "reason": "liiga.fi renders standings exclusively via client-side Next.js bundle; left blank rather than inferring GF/GA."},
        {"id": "gbgb-689570-kin", "sport": "greyhounds", "date": "2026-10-22", "competition": "UK BAGS Morning Card — Kinsley", "matchup": "Kinsley 11:14 Graded 462m (OLBG 689570)", "source_url": "https://www.gbgb.org.uk/racing/results/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28", "reason": "GBGB publishes post-race results and open-race clockings but not pre-race BAGS graded sectional form server-side; left unlined."},
        {"id": "gbgb-689576-she", "sport": "greyhounds", "date": "2026-10-22", "competition": "UK BAGS Morning Card — Sheffield", "matchup": "Sheffield 11:36 Graded 500m (OLBG 689576)", "source_url": "https://www.gbgb.org.uk/racing/results/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28", "reason": "Pre-race BAGS graded sectional times unavailable on server-rendered GBGB endpoint; left unlined."},
        {"id": "gbgb-689581-kin2", "sport": "greyhounds", "date": "2026-10-22", "competition": "UK BAGS Afternoon Card — Kinsley", "matchup": "Kinsley 12:03 Graded 462m (OLBG 689581)", "source_url": "https://www.gbgb.org.uk/racing/results/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28", "reason": "Pre-race BAGS graded sectional times unavailable on server-rendered GBGB endpoint; left unlined."},
        {"id": "gbgb-689584-not", "sport": "greyhounds", "date": "2026-10-22", "competition": "UK BAGS Afternoon Card — Nottingham", "matchup": "Nottingham 12:14 Graded 500m (OLBG 689584)", "source_url": "https://www.gbgb.org.uk/racing/results/", "olbg_url": "https://www.olbg.com/betting-tips/Greyhounds/28", "reason": "Pre-race BAGS graded sectional times unavailable on server-rendered GBGB endpoint; left unlined."},
        {"id": "rl-future-nrl27", "sport": "rugby-league", "date": "2027-03-04", "competition": "2027 NRL Telstra Premiership Outright", "matchup": "17-Club 2027 NRL Premiers Outright (OLBG Rugby_League/10)", "source_url": "https://www.nrl.com/draw/", "olbg_url": "https://www.olbg.com/betting-tips/Rugby_League/10", "reason": "2027 NRL season rosters and salary-cap squads not finalized during Oct 2026 RLWC; left unlined."},
        {"id": "cri-future-cwc27", "sport": "cricket", "date": "2027-10-01", "competition": "2027 ICC Men's Cricket World Cup Outright", "matchup": "14-Team 2027 ODI World Cup Outright (OLBG Cricket/7)", "source_url": "https://www.icc-cricket.com/rankings/team-rankings/mens/odi", "olbg_url": "https://www.olbg.com/betting-tips/Cricket/7", "reason": "Qualification pathway not yet complete for Oct-Nov 2027 tournament; left unlined."},
        {"id": "f1-future-wdc27", "sport": "motor-racing", "date": "2027-03-14", "competition": "2027 FIA Formula 1 Drivers Championship Outright", "matchup": "2027 F1 WDC Outright (OLBG 912)", "source_url": "https://www.formula1.com/en/results/2026/drivers", "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14", "reason": "2027 winter testing and full chassis homologation have not yet occurred; left unlined."},
        {"id": "hb-dom-hbl", "sport": "handball", "date": "2026-10-22", "competition": "DAIKIN Handball-Bundesliga (HBL)", "matchup": "SC DHfK Leipzig vs TBV Lemgo Lippe", "source_url": "https://www.daikin-hbl.de/de/hbl/tabelle", "olbg_url": "https://www.olbg.com/betting-tips/Handball/20", "reason": "daikin-hbl.de table renders via client-side JS; EHF Champions League originated in full, domestic HBL row left blank."},
    ]

    return {
        "captured_at": "2026-10-22T05:45:00Z",
        "session": "arena/d81930c3-olbg2",
        "nhl_teams": hub_in["nhl_teams"],
        "nhl_score_feed": r26["nhl"]["score_feed_2026-10-22"],
        "shl_teams": hub_in["shl_teams"],
        "shl_fixtures": shl_oct22,
        "nba_teams": slate_in["nba_teams"],
        "nba_2026_records": nba_2026_records,
        "nba_fixtures": slate_in["nba_fixtures"],
        "euroleague_teams": euroleague_teams,
        "euroleague_r7_fixtures": euroleague_r7,
        "top14_teams": hub_in["top14_teams"],
        "top14_fixtures": hub_in["top14_fixtures"],
        "prod2_teams": hub_in["prod2_teams"],
        "prod2_fixtures": hub_in["prod2_fixtures"],
        "urc_teams": hub_in["urc_teams"],
        "urc_r4_fixtures": hub_in["urc_r4_fixtures"],
        "ehf_teams": hub_in["ehf_teams"],
        "ehf_r5_fixtures": hub_in["ehf_r5_fixtures"],
        "superlega_teams": hub_in["superlega_teams"],
        "superlega_fixtures": hub_in["superlega_fixtures"],
        "aflw_teams": slate_in["aflw_teams"],
        "aflw_fixtures": aflw_fixtures,
        "rlwc_teams": slate_in["rlwc_teams"],
        "rlwc_fixtures": slate_in["rlwc_fixtures"],
        "lol_teams": slate_in["lol_teams"],
        "lol_fixtures": lol_fixtures,
        "pdc_players": pdc_players,
        "darts_fixtures": darts_fixtures,
        "snooker_lined": snooker_lined,
        "tennis_fixtures": tennis_fixtures,
        "cricket_fixtures": cricket_fixtures,
        "golf_matchups": golf_matchups,
        "greyhound_markets": greyhound_markets,
        "gaa_fixtures": gaa_fixtures,
        "mlb_teams": hub_in["mlb_teams"],
        "mlb_fixtures": hub_in["mlb_fixtures"][:5],
        "f1_drivers": f1_drivers,
        "f1_markets": f1_markets,
        "unlined_rows": unlined_rows,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sports_payload = {
        "captured_at": "2026-10-22T05:45:00Z",
        "session": "arena/d81930c3-olbg2",
        "eligible_count": len(ELIGIBLE_SPORTS),
        "excluded_hub_count": len(EXCLUDED_HUBS),
        "eligible_sports": ELIGIBLE_SPORTS,
        "excluded_hubs": EXCLUDED_HUBS,
    }
    (OUT / "sports.json").write_text(json.dumps(sports_payload, indent=2, ensure_ascii=False) + "\n")
    (OUT / "sources.json").write_text(json.dumps({"sources": SOURCES}, indent=2, ensure_ascii=False) + "\n")
    (OUT / "repo_audit.json").write_text(json.dumps({"findings": REPO_AUDIT}, indent=2, ensure_ascii=False) + "\n")
    inputs = build_inputs()
    (OUT / "inputs.json").write_text(json.dumps(inputs, indent=2, ensure_ascii=False) + "\n")
    print(
        f"portal_seed.py OK: {len(ELIGIBLE_SPORTS)} eligible sports, "
        f"{len(SOURCES)} official sources, {len(REPO_AUDIT)} audit findings, "
        f"{len(inputs['unlined_rows'])} unlined rows."
    )


if __name__ == "__main__":
    main()
