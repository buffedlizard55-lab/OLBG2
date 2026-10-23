"""Cadence desk — captured official-source inputs for 2026-10-23.

Every value below was read first-hand from the official governing-body page named in
``source`` during the capture window 2026-10-23T19:00Z-20:05Z. Nothing is inferred:
where an official page did not publish a value it is left as ``None`` and is listed on
``/cadence/flagged.html``.

Run: python3 scripts/cadence_seed.py  ->  data/cadence/{sources,fixtures,captures}.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "cadence")
CAP = os.path.join(OUT, "captures")
CAPTURED_UTC = "2026-10-23T20:05:00Z"
SESSION = "arena/a0c8b7f3-olbg2"

# ---------------------------------------------------------------------------
# Official sources actually read this session
# ---------------------------------------------------------------------------
SOURCES = [
    ("olbg_tips", "OLBG", "https://www.olbg.com/betting-tips",
     "Full sport index confirming the 16 canonical OLBG sportIds used by the desk"),
    ("olbg_darts", "OLBG", "https://www.olbg.com/betting-tips/Darts/15",
     "Darts hub route /betting-tips/Darts/15 and market vocabulary"),
    ("olbg_nhl_event", "OLBG", "https://www.olbg.com/betting-tips/Ice_Hockey/13?event_id=199984",
     "Event-page structure, Most Popular Tip string-concatenation defect"),
    ("olbg_nba_event", "OLBG", "https://www.olbg.com/betting-tips/Basketball/4?event_id=536036",
     "Event-page markets (Money Line, Pointspread, Game Totals) and tie display"),
    ("olbg_tennis_event", "OLBG", "https://www.olbg.com/betting-tips/Tennis/3?event_id=902163",
     "Blank WIN @ odds cells, false Expired badge, 2/021 denominator defect"),
    ("nhle_schedule", "NHL", "https://api-web.nhle.com/v1/schedule/2026-10-23",
     "Two NHL fixtures on 2026-10-23 with UTC start, venue and published moneylines"),
    ("nhle_standings", "NHL", "https://api-web.nhle.com/v1/standings/2026-10-23",
     "2026-27 club records, goal totals, home/road splits, L10 and streaks"),
    ("nba_games", "NBA", "https://www.nba.com/games?date=2026-10-23",
     "Twelve NBA fixtures, tip times (ET), records and season leaders"),
    ("nba_standings", "NBA", "https://www.nba.com/standings",
     "2026-27 conference standings after 1-2 games"),
    ("nba_injury", "NBA Office of the Commissioner",
     "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf",
     "Official game-day injury report 10/23/26 03:15 PM ET with player statuses"),
    ("nba_injury_index", "NBA", "https://official.nba.com/nba-injury-report-2026-27-season/",
     "Index page linking the 2026-10-23 injury-report PDFs"),
    ("mlb_schedule", "MLB", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-11-02",
     "World Series Games 1-7 with official date, venue and probable pitchers"),
    ("mlb_standings", "MLB", "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026",
     "Final 2026 regular-season records and splits for both World Series clubs"),
    ("mlb_brewers", "MLB", "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings",
     "Milwaukee 103-59, 832/618, 55-26 home, 68-35 night, W5, 8-2 L10"),
    ("mlb_pitchers", "MLB", "https://statsapi.mlb.com/api/v1/people?personIds=607259,694819,656876,701656&hydrate=stats(group=[pitching],type=[season],season=2026)",
     "2026 season pitching lines for Martinez, Misiorowski, Rasmussen and Henderson"),
    ("cricket_au", "Cricket Australia", "https://www.cricket.com.au/matches?isCompleted=0&year=2026",
     "Upcoming Australian and international fixtures with venues and local start times"),
    ("cricket_au_done", "Cricket Australia", "https://www.cricket.com.au/matches?isCompleted=1&year=2026",
     "Completed 2026 fixtures with full scorecards (Afghanistan v Zimbabwe, SL v England, NZ v India)"),
    ("wst_matches", "World Snooker Tour", "https://www.wst.tv/matches/",
     "Northern Ireland Open quarter-final, semi-final and final schedule with frame scores"),
    ("wst_rankings", "World Snooker Tour", "https://www.wst.tv/rankings/",
     "Johnstone's Paint World Rankings and One Year List with prize money"),
    ("wst_ic", "World Snooker Tour", "https://www.wst.tv/match-centre/77ee26cc-bb1d-417e-a522-c716cd390464",
     "International Championship 2026 Nanjing Round 2 match centres and dates"),
    ("wst_ni_qf", "World Snooker Tour", "https://www.wst.tv/match-centre/19048b0d-aaf4-4691-ad10-15b1b707f622",
     "Live Northern Ireland Open quarter-final frame scores (Gilbert v Williams)"),
    ("pdc_withdrawal", "PDC", "https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship",
     "Official withdrawal of Luke Humphries (gastroenteritis) and Kim Huybrechts replacement"),
    ("pdc_day_one", "PDC", "https://www.pdc.tv/news/2026/october/22/nine-dart-star-woodhouse-sets-up-van-veen-clash-dortmund",
     "Round One results, Woodhouse nine-darter, Bunting 6-5 Noppert, Huybrechts 6-1 Searle"),
    ("pdc_schedule", "PDC", "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/",
     "Saturday 24 October Round Two bracket and 2026 European Tour ranking order"),
    ("pdc_rules", "PDC", "https://www.pdc.tv/rankings/pdc-rankings-rules",
     "2026 European Championship format, prize fund and cut-off"),
    ("atp_scores", "ATP Tour", "https://www.atptour.com/en/scores/current",
     "Live and completed ATP quarter-final scores across Almaty, Brussels and Lyon"),
    ("atp_almaty", "ATP Tour", "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule",
     "Almaty Open semi-final order of play for 24 October 2026"),
    ("atp_rankings", "ATP Tour", "https://www.atptour.com/en/rankings/singles",
     "PIF ATP Rankings singles, week of 2026-10-19, official points"),
    ("atp_vienna", "ATP Tour", "https://www.atptour.com/en/scores/current/vienna/337/daily-schedule",
     "Vienna qualifying order of play for 24 October 2026"),
    ("pgatour", "PGA TOUR", "https://www.pgatour.com/leaderboard",
     "Butterfield Bermuda Championship R2 leaderboard, scores, cut line -4"),
    ("dpwt", "DP World Tour", "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/leaderboard",
     "Genesis Championship R2 scores and round-three tee times"),
    ("gbgb_schedule", "GBGB", "https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/",
     "2026 Category One schedule: Scurry Gold Cup and PGR Oaks finals, Dunstall Park, 24 Oct"),
    ("gbgb_scurry", "GBGB", "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/",
     "Scurry Gold Cup semi-final winners and winning times"),
    ("gbgb_oaks", "GBGB", "https://www.gbgb.org.uk/signet-nayla-chases-oaks-glory-as-hutton-targets-dunstall-park-double/",
     "PGR Oaks semi-final winners and winning times"),
    ("gbgb_toty", "GBGB", "https://www.gbgb.org.uk/trainer-of-the-year-standings-up-to-and-including-sunday-18th-october/",
     "Trainer of the Year standings to 18 October 2026"),
    ("lnh_table", "LNH", "https://www.lnh.fr/daikin-starligue/classement",
     "Daikin StarLigue 2026-27 table after seven rounds with goals for/against"),
    ("lnh_cal", "LNH", "https://www.lnh.fr/daikin-starligue/calendrier",
     "StarLigue Round 8 fixtures and results"),
    ("lnh_ehf", "LNH", "https://www.lnh.fr/autres-competitions/ligue-des-champions",
     "EHF Champions League Round 6 fixtures involving French clubs"),
    ("legavolley_cal", "Lega Pallavolo Serie A", "https://www.legavolley.it/calendario/?idCampionato=999",
     "SuperLega 2026-27 Round 1 results and Round 2 fixtures with venues and officials"),
    ("legavolley_table", "Lega Pallavolo Serie A", "https://www.legavolley.it/classifica/?IdCampionato=999",
     "SuperLega table updated 18/10/2026 with sets and points ratios"),
    ("vbl_schedule", "Volleyball Bundesliga", "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/hauptrunde.xhtml",
     "1. Bundesliga Männer match schedule for 22-25 October 2026"),
    ("vbl_table", "Volleyball Bundesliga", "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/statistik/tabelle/tabelle_hauptrunde.xhtml",
     "1. Bundesliga Männer table after Round 1"),
    ("prem_fixtures", "Premiership Rugby", "https://www.premrugby.com/fixtures-results",
     "Gallagher PREM Round 4 fixtures with venues and form strings"),
    ("prem_table", "Premiership Rugby", "https://www.premrugby.com/standings",
     "Gallagher PREM table after three rounds with points difference"),
    ("urc_round4", "United Rugby Championship", "https://stats.unitedrugby.com/match-centre/2026-27/4",
     "URC Round 4 fixtures, Round 3 results and venues"),
    ("nrl_r2", "NRL", "https://www.nrl.com/draw/?competition=131&round=2&season=2026",
     "Rugby League World Cup 2026 Round 2 fixtures, venues and ladder positions"),
    ("nrl_r1", "NRL", "https://www.nrl.com/draw/?competition=131&round=1&season=2026",
     "Rugby League World Cup 2026 Round 1 results"),
    ("nrl_r3", "NRL", "https://www.nrl.com/draw/?competition=131&round=3&season=2026",
     "Rugby League World Cup 2026 Round 3 fixtures"),
    ("f1_calendar", "Formula 1", "https://www.formula1.com/en/racing/2026",
     "2026 FIA Formula One calendar; Round 18 United States 23-25 October"),
    ("f1_usgp", "Formula 1", "https://www.formula1.com/en/racing/2026/united-states",
     "COTA session schedule, circuit length, laps and FP1 classification"),
    ("f1_drivers", "Formula 1", "https://www.formula1.com/en/results/2026/drivers",
     "2026 Drivers' Championship points after Round 17"),
    ("gaa_fixtures", "GAA", "https://www.gaa.ie/fixtures-results",
     "Hurling-Shinty International Ireland v Scotland, 24 October, Páirc Uí Chaoimh"),
    ("munster_gaa", "Munster GAA", "https://munster.gaa.ie/fixtures/events-calendar/",
     "Cork, Kerry, Waterford and Limerick county finals 25 October with venues and referees"),
    ("gaacork", "Cork GAA", "https://gaacork.ie/fixtures/",
     "Cork Premier SFC final St Finbarr's v Nemo Rangers and semi-final scorelines"),
    ("kerrygaa", "Kerry GAA", "https://www.kerrygaa.ie/clubs/kenmare-shamrocks/",
     "Kerry SFC final Dr Crokes v Kenmare Shamrocks, Fitzgerald Stadium"),
    ("waterfordgaa", "Waterford GAA", "https://www.waterfordgaa.ie/results/",
     "Waterford SFC semi-final results: Rathgormack 1-14 Gaultier 0-15; The Nire 0-12 Abbeyside 0-5"),
    ("limerickgaa", "Limerick GAA", "https://limerickgaa.ie/na-piarsaigh-gaa-club-notes-213/",
     "Limerick SHC semi-final Na Piarsaigh 2-24 Doon 3-16; final v Kilmallock"),
]

SOURCE_URL = {key: url for key, _pub, url, _what in SOURCES}


def ref(key):
    return SOURCE_URL[key]


# ---------------------------------------------------------------------------
# Fixtures.  Each row carries its own official source keys and verified facts.
# ``time_display`` is the string the official page published; ``start_utc`` is
# filled only where the publisher stated a UTC or ET basis explicitly.
# ---------------------------------------------------------------------------
FIXTURES = []


def fx(**kw):
    kw.setdefault("olbg_event_id", None)
    kw.setdefault("start_utc", None)
    kw.setdefault("time_display", None)
    kw.setdefault("venue", None)
    kw.setdefault("facts", [])
    kw.setdefault("inputs", {})
    kw.setdefault("lineup_note", None)
    FIXTURES.append(kw)


# --- Ice Hockey: NHL -------------------------------------------------------
fx(sport="Ice Hockey", competition="NHL", id="nhl-2026020166",
   home="Chicago Blackhawks", away="Montréal Canadiens",
   start_utc="2026-10-24T00:00:00Z", time_display="2026-10-24T00:00:00Z (NHL feed)",
   venue="United Center", olbg_event_id=199984,
   source="nhle_schedule", stats_source="nhle_standings",
   inputs={"home": {"gp": 9, "w": 3, "l": 6, "otl": 0, "pts": 6, "gf": 21, "ga": 36,
                    "l10": "3-6-0", "streak": "L1", "home": "3-2-0", "road": "0-4-0"},
           "away": {"gp": 9, "w": 4, "l": 3, "otl": 2, "pts": 10, "gf": 30, "ga": 34,
                    "l10": "4-3-2", "streak": "OT1", "home": "3-2-1", "road": "1-1-1"},
           "published_ml": {"away": -169, "home": 137}},
   facts=[("Montréal", "4-3-2 in 9 games, 30 goals for, 34 against, 10 points, OT1 streak", "nhle_standings"),
          ("Chicago", "3-6-0 in 9 games, 21 goals for, 36 against, 6 points, 0-4-0 on the road", "nhle_standings"),
          ("NHL feed price", "Montréal -169 / Chicago +137 published by the NHL schedule feed", "nhle_schedule")])

fx(sport="Ice Hockey", competition="NHL", id="nhl-2026020167",
   home="Colorado Avalanche", away="Tampa Bay Lightning",
   start_utc="2026-10-24T01:00:00Z", time_display="2026-10-24T01:00:00Z (NHL feed)",
   venue="Ball Arena",
   source="nhle_schedule", stats_source="nhle_standings",
   inputs={"home": {"gp": 10, "w": 5, "l": 4, "otl": 1, "pts": 11, "gf": 41, "ga": 31,
                    "l10": "5-4-1", "streak": "L2", "home": "3-1-1", "road": "2-3-0"},
           "away": {"gp": 9, "w": 7, "l": 2, "otl": 0, "pts": 14, "gf": 31, "ga": 23,
                    "l10": "7-2-0", "streak": "W3", "home": "5-0-0", "road": "2-2-0"},
           "published_ml": {"away": 105, "home": -129}},
   facts=[("Tampa Bay", "7-2-0 in 9 games, 31 goals for, 23 against, 14 points, W3", "nhle_standings"),
          ("Colorado", "5-4-1 in 10 games, 41 goals for, 31 against, 11 points, L2", "nhle_standings"),
          ("NHL feed price", "Tampa Bay +105 / Colorado -129 published by the NHL schedule feed", "nhle_schedule")])

# --- Basketball: NBA -------------------------------------------------------
NBA = [
    ("nba-0022600099", "Milwaukee Bucks", "Chicago Bulls", "2026-10-24T00:00:00Z", "8:00 PM ET", "00-1", "0-1"),
    ("nba-0022600008", "Boston Celtics", "New York Knicks", "2026-10-23T23:00:00Z", "7:00 PM ET", "0-1", "0-1"),
    ("nba-0022600097", "Washington Wizards", "Toronto Raptors", "2026-10-23T23:00:00Z", "7:00 PM ET", "1-0", "1-0"),
    ("nba-0022600094", "Charlotte Hornets", "Atlanta Hawks", "2026-10-23T23:00:00Z", "7:00 PM ET", "1-0", "1-0"),
    ("nba-0022600096", "Orlando Magic", "Minnesota Timberwolves", "2026-10-23T23:00:00Z", "7:00 PM ET", "0-1", "1-0"),
    ("nba-0022600095", "Indiana Pacers", "Dallas Mavericks", "2026-10-23T23:00:00Z", "7:00 PM ET", "1-0", "0-1"),
    ("nba-0022600098", "Miami Heat", "Detroit Pistons", "2026-10-24T00:00:00Z", "8:00 PM ET", "0-1", "1-0"),
    ("nba-0022600009", "San Antonio Spurs", "Houston Rockets", "2026-10-24T01:30:00Z", "9:30 PM ET", "0-1", "1-0"),
    ("nba-0022600100", "Utah Jazz", "New Orleans Pelicans", "2026-10-24T01:30:00Z", "9:30 PM ET", "0-1", "0-1"),
    ("nba-0022600101", "Golden State Warriors", "Memphis Grizzlies", "2026-10-24T02:00:00Z", "10:00 PM ET", "0-1", "1-0"),
    ("nba-0022600102", "Los Angeles Lakers", "LA Clippers", "2026-10-24T02:00:00Z", "10:00 PM ET", "1-0", "1-0"),
    ("nba-0022600103", "Sacramento Kings", "Portland Trail Blazers", "2026-10-24T02:00:00Z", "10:00 PM ET", "0-1", "1-0"),
]
NBA_INJ = {
    "nba-0022600099": [("Chicago Bulls", "Nic Claxton", "Out", "Left hamstring strain")],
    "nba-0022600008": [("Boston Celtics", "Devin Carter", "Out", "Illness")],
    "nba-0022600097": [("Toronto Raptors", "Nate Bittle", "Out", "Right foot avulsion fracture"),
                       ("Washington Wizards", "AJ Dybantsa", "Out", "Left ankle sprain"),
                       ("Washington Wizards", "Tristan Vukcevic", "Out", "Left hip impingement"),
                       ("Washington Wizards", "Jamir Watkins", "Out", "Left ACL repair/surgery")],
    "nba-0022600094": [("Atlanta Hawks", "Mouhamed Gueye", "Out", "Left foot fracture"),
                       ("Atlanta Hawks", "Henri Veesaar", "Out", "Right ACL tear"),
                       ("Charlotte Hornets", "Kon Knueppel", "Out", "Left hamstring strain"),
                       ("Charlotte Hornets", "Coby White", "Out", "Left calf strain"),
                       ("Charlotte Hornets", "Grant Williams", "Out", "Right hamstring strain"),
                       ("Charlotte Hornets", "Kylan Boswell", "Out", "Right knee surgery")],
    "nba-0022600096": [("Minnesota Timberwolves", "Donte DiVincenzo", "Out", "Right Achilles repair/surgery"),
                       ("Orlando Magic", "Anthony Black", "Out", "Right ankle sprain"),
                       ("Orlando Magic", "Jonathan Isaac", "Out", "Left knee injury management"),
                       ("Orlando Magic", "Izaiyah Nelson", "Out", "Left ankle injury recovery"),
                       ("Orlando Magic", "Noah Penda", "Out", "Right partially torn hamstring")],
    "nba-0022600095": [("Dallas Mavericks", "Santi Aldama", "Out", "Right knee surgery"),
                       ("Dallas Mavericks", "Dereck Lively II", "Out", "Right foot surgery"),
                       ("Dallas Mavericks", "Caleb Martin", "Out", "Right thumb sprain"),
                       ("Indiana Pacers", "T.J. McConnell", "Out", "Right hamstring strain"),
                       ("Indiana Pacers", "Johnny Furphy", "Out", "Right ACL repair/surgery")],
    "nba-0022600098": [("Detroit Pistons", "Taurean Prince", "Available", "Personal reasons"),
                       ("Miami Heat", "Vladislav Goldin", "Available", "Right ankle sprain")],
    "nba-0022600009": [("Houston Rockets", "Steven Adams", "Questionable", "Right calf tightness"),
                       ("Houston Rockets", "Reed Sheppard", "Questionable", "Left knee contusion"),
                       ("San Antonio Spurs", "De'Aaron Fox", "Questionable", "Right wrist sprain"),
                       ("San Antonio Spurs", "Tobias Harris", "Out", "Left calf strain"),
                       ("San Antonio Spurs", "Keldon Johnson", "Questionable", "Mouth laceration"),
                       ("San Antonio Spurs", "Jayden Quaintance", "Out", "Right knee surgery")],
    "nba-0022600100": [("Utah Jazz", "Jusuf Nurkic", "Out", "Right 2nd plantar plate tear"),
                       ("Utah Jazz", "Tony Bradley", "Available", "Left quadriceps strain")],
    "nba-0022600101": [("Memphis Grizzlies", "Cedric Coward", "Doubtful", "Left wrist sprain"),
                       ("Golden State Warriors", "Jimmy Butler III", "Out", "Right ACL repair/surgery"),
                       ("Golden State Warriors", "Moses Moody", "Out", "Left patellar tendon repair/surgery"),
                       ("Golden State Warriors", "Kristaps Porzingis", "Out", "Not with team"),
                       ("Golden State Warriors", "Brandin Podziemski", "Questionable", "Bilateral low back soreness")],
    "nba-0022600102": [("LA Clippers", "Bradley Beal", "Out", "Right knee injury management"),
                       ("LA Clippers", "Brandon Ingram", "Out", "Right heel surgery"),
                       ("LA Clippers", "Jordan Miller", "Out", "Left rotator cuff surgery"),
                       ("LA Clippers", "Max Strus", "Out", "Right plantar fascia")],
    "nba-0022600103": [("Portland Trail Blazers", "Shaedon Sharpe", "Out", "Right meniscus surgery"),
                       ("Portland Trail Blazers", "Chris Youngblood", "Out", "Left ankle soreness"),
                       ("Sacramento Kings", "Dylan Cardwell", "Out", "Left calf strain"),
                       ("Sacramento Kings", "Malik Monk", "Probable", "Left ankle soreness"),
                       ("Sacramento Kings", "Maxime Raynaud", "Out", "Right patella subluxation"),
                       ("Sacramento Kings", "Ben Simmons", "Out", "Right Achilles repair/surgery")],
}
for fid, home, away, start, disp, hrec, arec in NBA:
    fx(sport="Basketball", competition="NBA", id=fid, home=home, away=away,
       start_utc=start, time_display=disp, venue=None, source="nba_games",
       stats_source="nba_standings", injury_source="nba_injury",
       inputs={"home_record": hrec, "away_record": arec},
       facts=[(home, f"{hrec} after the opening games", "nba_standings"),
              (away, f"{arec} after the opening games", "nba_standings"),
              ("Tip time", disp, "nba_games")] +
             [(t, f"{p} {st} — {r}", "nba_injury") for t, p, st, r in NBA_INJ.get(fid, [])])

# --- Basketball: EuroLeague Round 8 ---------------------------------------
EL = {
    "Panathinaikos AKTOR Athens": (7, 6, 1, 613, 517),
    "Fenerbahce Tarfin Istanbul": (6, 5, 1, 501, 447),
    "Olympiacos Piraeus": (6, 5, 1, 564, 524),
    "Hapoel IBI Tel Aviv": (7, 5, 2, 630, 601),
    "Dubai Basketball": (7, 5, 2, 597, 584),
    "Valencia Basket": (6, 4, 2, 583, 537),
    "Real Madrid": (7, 4, 3, 667, 630),
    "Crvena Zvezda Meridianbet Belgrade": (7, 4, 3, 560, 532),
    "FC Barcelona": (7, 4, 3, 623, 606),
    "Virtus Bologna": (7, 4, 3, 606, 608),
    "Partizan Mozzart Bet Belgrade": (7, 4, 3, 541, 546),
    "Zalgiris Kaunas": (7, 3, 4, 595, 602),
    "Anadolu Efes Istanbul": (7, 3, 4, 581, 590),
    "Besiktas Istanbul": (7, 3, 4, 634, 644),
    "Maccabi Rapyd Tel Aviv": (7, 2, 5, 608, 653),
    "FC Bayern Munich": (7, 2, 5, 612, 659),
    "LDLC ASVEL Villeurbanne": (7, 2, 5, 612, 677),
    "Paris Basketball": (6, 1, 5, 504, 545),
    "Armani Olimpia Milan": (7, 1, 6, 585, 648),
    "Kosner Baskonia Vitoria-Gasteiz": (7, 1, 6, 583, 649),
}
EL_FIX = [
    ("el-E2026_76", "Panathinaikos AKTOR Athens", "Armani Olimpia Milan", "2026-10-27", "15:15 local"),
    ("el-E2026_75", "Valencia Basket", "Fenerbahce Tarfin Istanbul", "2026-10-27", "15:30 local"),
    ("el-E2026_73", "Kosner Baskonia Vitoria-Gasteiz", "Real Madrid", "2026-10-27", "16:00 local"),
    ("el-E2026_79", "Besiktas Istanbul", "Olympiacos Piraeus", "2026-10-28", "13:30 local"),
    ("el-E2026_77", "Hapoel IBI Tel Aviv", "Anadolu Efes Istanbul", "2026-10-28", "14:00 local"),
    ("el-E2026_80", "Virtus Bologna", "Zalgiris Kaunas", "2026-10-28", "local TBC"),
]
for fid, home, away, day, disp in EL_FIX:
    hg, hw, hl, hf, ha = EL[home]
    ag, aw, al, af, aa = EL[away]
    fx(sport="Basketball", competition="EuroLeague", id=fid, home=home, away=away,
       start_utc=None, time_display=f"{day} {disp}", source="el_game_center",
       venue=None, stats_source="el_standings",
       inputs={"home": {"gp": hg, "w": hw, "l": hl, "pf": hf, "pa": ha},
               "away": {"gp": ag, "w": aw, "l": al, "pf": af, "pa": aa}},
       facts=[(home, f"{hw}-{hl} in {hg} EuroLeague games, {hf} points for, {ha} against", "el_standings"),
              (away, f"{aw}-{al} in {ag} EuroLeague games, {af} points for, {aa} against", "el_standings")])

# --- Baseball: World Series Games 1-2 -------------------------------------
fx(sport="Baseball", competition="MLB World Series", id="mlb-849805",
   home="Milwaukee Brewers", away="Tampa Bay Rays",
   start_utc="2026-10-24T00:00:00Z", time_display="World Series Game 1, 2026-10-24T00:00Z",
   venue="American Family Field", source="mlb_schedule", stats_source="mlb_brewers",
   inputs={"home": {"w": 103, "l": 59, "pct": 0.636, "rs": 832, "ra": 618, "home": "55-26",
                    "night": "68-35", "l10": "8-2", "streak": "W5"},
           "away": {"w": 98, "l": 64, "pct": 0.605, "rs": 736, "ra": 650, "away": "43-38",
                    "night": "63-35", "l10": "5-5", "streak": "L1"},
           "home_sp": {"name": "Jacob Misiorowski", "gs": 30, "ip": 174.2, "era": 1.80,
                       "k": 252, "bb": 44, "whip": 0.80, "k9": 12.98, "avg": 0.157},
           "away_sp": {"name": "Nick Martinez", "gs": 31, "ip": 180.0, "era": 3.10,
                       "k": 109, "bb": 26, "whip": 1.09, "k9": 5.45, "avg": 0.249}},
   facts=[("Milwaukee", "103-59, .636, 832 scored, 618 allowed, 55-26 at home, 68-35 at night, W5, 8-2 in ten", "mlb_brewers"),
          ("Tampa Bay", "98-64, .605, 736 scored, 650 allowed, 43-38 on the road, 63-35 at night, L1, 5-5 in ten", "mlb_standings"),
          ("Jacob Misiorowski", "2026: 30 starts, 16-5, 1.80 ERA, 174.2 IP, 252 K, 44 BB, 0.80 WHIP, .157 opponents average", "mlb_pitchers"),
          ("Nick Martinez", "2026: 31 starts, 15-6, 3.10 ERA, 180.0 IP, 109 K, 26 BB, 1.09 WHIP, .249 opponents average", "mlb_pitchers"),
          ("Fixture", "World Series Game 1 at American Family Field, first pitch 2026-10-24T00:00Z", "mlb_schedule")])

fx(sport="Baseball", competition="MLB World Series", id="mlb-849802",
   home="Milwaukee Brewers", away="Tampa Bay Rays",
   start_utc="2026-10-25T00:00:00Z", time_display="World Series Game 2, 2026-10-25T00:00Z",
   venue="American Family Field", source="mlb_schedule", stats_source="mlb_brewers",
   inputs={"home": {"w": 103, "l": 59, "pct": 0.636, "rs": 832, "ra": 618, "home": "55-26",
                    "night": "68-35", "l10": "8-2", "streak": "W5"},
           "away": {"w": 98, "l": 64, "pct": 0.605, "rs": 736, "ra": 650, "away": "43-38",
                    "night": "63-35", "l10": "5-5", "streak": "L1"},
           "home_sp": {"name": "Logan Henderson", "gs": None, "ip": None, "era": None,
                       "k": None, "bb": None, "whip": None, "k9": None, "avg": None},
           "away_sp": {"name": "Drew Rasmussen", "gs": 30, "ip": 172.0, "era": 2.67,
                       "k": 174, "bb": 32, "whip": 0.91, "k9": 9.10, "avg": 0.199}},
   facts=[("Milwaukee", "103-59, .636, 832 scored, 618 allowed, 55-26 at home, W5, 8-2 in ten", "mlb_brewers"),
          ("Tampa Bay", "98-64, .605, 736 scored, 650 allowed, 43-38 on the road, L1", "mlb_standings"),
          ("Drew Rasmussen", "2026: 30 starts, 16-5, 2.67 ERA, 172.0 IP, 174 K, 32 BB, 0.91 WHIP, .199 opponents average", "mlb_pitchers"),
          ("Fixture", "World Series Game 2 at American Family Field, first pitch 2026-10-25T00:00Z", "mlb_schedule")])

# --- Cricket --------------------------------------------------------------
fx(sport="Cricket", competition="One-Day Cup 2026-27", id="cri-40681",
   home="Tasmanian Tigers", away="Victoria",
   time_display="23 October 2026, 7:30 pm viewer-local", venue="Bellerive Oval, Hobart",
   source="cricket_au", stats_source="cricket_au_done",
   inputs={"format": "List A", "home_note": "Tasmania", "away_note": "Victoria"},
   facts=[("Fixture", "One-Day Cup 2026-27, Tasmanian Tigers v Victoria, Bellerive Oval, Hobart, 23 October 2026", "cricket_au")])

fx(sport="Cricket", competition="One-Day Cup 2026-27", id="cri-40683",
   home="Western Australia", away="New South Wales",
   time_display="24 October 2026, 2:00 am viewer-local", venue="WACA Ground, Perth",
   source="cricket_au", stats_source="cricket_au_done",
   inputs={"format": "List A"},
   facts=[("Fixture", "One-Day Cup 2026-27, Western Australia v New South Wales, WACA Ground, Perth, 24 October 2026", "cricket_au")])

fx(sport="Cricket", competition="New Zealand v India T20Is 2026", id="cri-41095",
   home="New Zealand", away="India",
   time_display="24 October 2026, 3:00 am viewer-local", venue="Hagley Oval, Christchurch",
   source="cricket_au", stats_source="cricket_au_done",
   inputs={"format": "T20I", "home_form": "lost 1st T20I by 4 wickets", "away_form": "won 1st T20I by 4 wickets"},
   facts=[("1st T20I", "India won by 4 wickets: New Zealand 4-225 (20.0), India 6-230 (19.4), Hagley Oval, 22 October 2026", "cricket_au_done"),
          ("Fixture", "2nd T20I, Hagley Oval, Christchurch, 24 October 2026", "cricket_au")])

fx(sport="Cricket", competition="Pakistan ODI Tri-Series 2026", id="cri-40981",
   home="Pakistan", away="England",
   time_display="25 October 2026, 4:00 am viewer-local", venue="Gaddafi Stadium, Lahore",
   source="cricket_au", stats_source="cricket_au_done",
   inputs={"format": "ODI", "home_form": "not captured in this series", "away_form": "lost to Sri Lanka by 2 wickets"},
   facts=[("Sri Lanka v England", "Sri Lanka won by 2 wickets: England 4-429 (50.0), Sri Lanka 8-430 (49.5), Rawalpindi, 22 October 2026", "cricket_au_done"),
          ("Fixture", "Pakistan v England, Pakistan ODI Tri-Series, Gaddafi Stadium, Lahore, 25 October 2026", "cricket_au")])

fx(sport="Cricket", competition="India v Zimbabwe ODIs 2026 (Women)", id="cri-40394",
   home="India Women", away="Zimbabwe Women",
   time_display="25 October 2026, 4:30 am viewer-local", venue="Vadodara International Cricket Stadium",
   source="cricket_au", stats_source="cricket_au_done",
   inputs={"format": "WODI", "home_form": "won 1st ODI by 9 wickets", "away_form": "lost 1st ODI by 9 wickets"},
   facts=[("1st ODI", "India Women won by 9 wickets: Zimbabwe Women 197 (49.5), India Women 1-200 (27.1), Vadodara, 23 October 2026", "cricket_au_done"),
          ("Fixture", "2nd ODI, Vadodara International Cricket Stadium, 25 October 2026", "cricket_au")])

fx(sport="Cricket", competition="South Africa v Australia Tests 2026", id="cri-39992",
   home="South Africa", away="Australia",
   time_display="27-31 October 2026, 4:30 am viewer-local", venue="Newlands, Cape Town",
   source="cricket_au", stats_source="cricket_au_done",
   inputs={"format": "Test"},
   facts=[("Fixture", "3rd Test, South Africa v Australia, Newlands, Cape Town, 27-31 October 2026", "cricket_au")])

# --- Snooker --------------------------------------------------------------
fx(sport="Snooker", competition="BetVictor Northern Ireland Open 2026", id="snk-ni-sf1",
   home="Kyren Wilson", away="Sam Craigie",
   time_display="24 October 2026, 08:00 (WST site clock)", venue="Waterfront Hall, Belfast",
   source="wst_matches", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": 716800, "away_rank_money": 132000,
           "home_note": "world no.9, £716,800", "away_note": "Northern Ireland Open quarter-finalist, beat Elliot Slessor 6-2"},
   facts=[("Kyren Wilson", "world no.9 with £716,800 on the Johnstone's Paint World Rankings; beat Anthony McGill 6-1 in the quarter-final", "wst_rankings"),
          ("Sam Craigie", "beat Elliot Slessor 6-2 in the quarter-final to reach the semi-final", "wst_matches"),
          ("Fixture", "Northern Ireland Open semi-final, 24 October 2026, first match on the WST schedule", "wst_matches")])

fx(sport="Snooker", competition="International Championship 2026", id="snk-ic-murphy",
   home="Shaun Murphy", away="Mitchell Mann",
   time_display="30 October 2026, 21:30 (WST match centre)", venue="Nanjing, China",
   source="wst_ic", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": 897350, "away_rank_money": None,
           "home_season": {"matches": 20, "win_rate": 0.65, "ast": 21.0, "breaks50": 46, "centuries": 15},
           "away_season": {"matches": 17, "win_rate": 0.48, "ast": 31.5, "breaks50": 23, "centuries": 4}},
   facts=[("Shaun Murphy", "world no.7 with £897,350; 2026/27 season 20 matches, 65% win rate, 21.0s average shot time, 46 breaks of 50+, 15 centuries", "wst_rankings"),
          ("Mitchell Mann", "2026/27 season 17 matches, 48% match win rate, 31.5s average shot time, 23 breaks of 50+, 4 centuries", "wst_ic"),
          ("Fixture", "International Championship Round 2, Nanjing, 30 October 2026, 21:30 per the match centre", "wst_ic")])

fx(sport="Snooker", competition="International Championship 2026", id="snk-ic-zhou",
   home="Zhou Yuelong", away="Liam Davies",
   time_display="30 October 2026, 21:30 (WST match centre)", venue="Nanjing, China",
   source="wst_ic", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": 359100, "away_rank_money": None,
           "home_season": {"matches": 23, "win_rate": 0.57, "ast": 26.4, "breaks50": 51, "centuries": 14},
           "away_season": {"matches": 28, "win_rate": 0.75, "ast": 24.9, "breaks50": 57, "centuries": 11}},
   facts=[("Zhou Yuelong", "world no.17 with £359,100; 2026/27 season 23 matches, 57% win rate, 26.4s average shot time, 51 breaks of 50+, 14 centuries", "wst_rankings"),
          ("Liam Davies", "2026/27 season 28 matches, 75% match win rate, 24.9s average shot time, 57 breaks of 50+, 11 centuries", "wst_ic"),
          ("Fixture", "International Championship Round 2, Nanjing, 30 October 2026", "wst_ic")])

fx(sport="Snooker", competition="International Championship 2026", id="snk-ic-liu",
   home="Liu Hongyu", away="Louis Heathcote",
   time_display="30 October 2026, 21:30 (WST match centre)", venue="Nanjing, China",
   source="wst_ic", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": None, "away_rank_money": None},
   line_blocked="Both players are outside the published ranking-money list held here; no strength input, so no line is originated.",
   facts=[("Fixture", "International Championship Round 2, Nanjing, Liu Hongyu v Louis Heathcote", "wst_ic")])

fx(sport="Snooker", competition="International Championship 2026", id="snk-ic-white",
   home="Jimmy White", away="Mark Selby",
   time_display="30 October 2026, 21:30 (WST match centre)", venue="Nanjing, China",
   source="wst_ic", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": None, "away_rank_money": 1070500,
           "away_note": "world no.5, £1,070,500; one-year list leader £348,350"},
   facts=[("Mark Selby", "world no.5 with £1,070,500 and top of the 2026/27 One Year List on £348,350", "wst_rankings"),
          ("Fixture", "International Championship Round 2, Nanjing, Jimmy White v Mark Selby", "wst_ic")])

for fid, h, a in [("snk-ic-szubarczyk", "Michal Szubarczyk", "Wildcard 1"),
                  ("snk-ic-hallworth", "Steven Hallworth", "Wildcard 3"),
                  ("snk-ic-liuwenwei", "Liu Wenwei", "Wildcard 4")]:
    fx(sport="Snooker", competition="International Championship 2026", id=fid, home=h, away=a,
       time_display="30 October 2026, 21:30 (WST match centre)", venue="Nanjing, China",
       source="wst_ic", stats_source="wst_rankings", inputs={"format": "pre-qualifier"},
       line_blocked="Opponent is published only as a wildcard slot, so identity is unconfirmed; no line is originated.",
       facts=[("Fixture", f"International Championship pre-qualifier, {h} v {a} (opponent identity not published)", "wst_ic")])

# --- Darts: European Championship Round Two -------------------------------
DARTS = [
    # (id, home, away, home European Tour money, away money, home seed, away seed, session)
    ("drt-r2-1", "Ross Smith", "Damon Heta", 158000, 0, 1, 17, "Saturday afternoon"),
    ("drt-r2-2", "Gian van Veen", "Luke Woodhouse", 0, 0, 8, 9, "Saturday afternoon"),
    ("drt-r2-3", "Cameron Menzies", "Gerwyn Price", 0, 0, 29, 13, "Saturday afternoon"),
    ("drt-r2-4", "Stephen Bunting", "Kim Huybrechts", 0, 0, 28, None, "Saturday afternoon"),
    ("drt-r2-5", "Wessel Nijman", "Ryan Joyce", 124000, 0, 2, 15, "Saturday evening"),
    ("drt-r2-6", "Jonny Clayton", "Josh Rock", 0, 0, 7, 10, "Saturday evening"),
    ("drt-r2-7", "Krzysztof Ratajski", "Michael van Gerwen", 89500, 0, 3, 19, "Saturday evening"),
    ("drt-r2-8", "Nathan Aspinall", "Luke Littler", 0, 0, 6, None, "Saturday evening"),
]
DARTS_FACTS = {
    "drt-r2-1": [("Ross Smith", "top seed on the 2026 European Tour Rankings with £158,000; beat Karel Sedlacek 6-4 in Round One", "pdc_schedule"),
                 ("Damon Heta", "17th seed; beat James Wade 6-5 in Round One", "pdc_day_one")],
    "drt-r2-2": [("Gian van Veen", "eighth seed and reigning champion; beat Andrew Gilding 6-4; set a 120.24 European Tour record average in Maastricht", "pdc_day_one"),
                 ("Luke Woodhouse", "ninth seed; hit a nine-dart finish in a 6-3 Round One win over Dirk van Duijvenbode", "pdc_day_one")],
    "drt-r2-3": [("Cameron Menzies", "29th seed; beat fourth seed Niels Zonneveld 6-3 in Round One", "pdc_day_one"),
                 ("Gerwyn Price", "13th seed; beat Rob Cross 6-2 in Round One", "pdc_day_one")],
    "drt-r2-4": [("Stephen Bunting", "28th seed; beat fifth seed Danny Noppert 6-5 with a 160 checkout in the deciding leg", "pdc_day_one"),
                 ("Kim Huybrechts", "late replacement for the withdrawn Luke Humphries; holds no 2026 European Tour seeding; beat Ryan Searle 6-1 at a 103.81 average", "pdc_day_one")],
    "drt-r2-5": [("Wessel Nijman", "second seed with £124,000 on the 2026 European Tour Rankings", "pdc_schedule"),
                 ("Ryan Joyce", "15th seed", "pdc_schedule")],
    "drt-r2-6": [("Jonny Clayton", "seventh seed for the event", "pdc_schedule"),
                 ("Josh Rock", "tenth seed for the event", "pdc_schedule")],
    "drt-r2-7": [("Krzysztof Ratajski", "third seed with £89,500 on the 2026 European Tour Rankings", "pdc_schedule"),
                 ("Michael van Gerwen", "four-time European Championship winner; 19th seed", "pdc_schedule")],
    "drt-r2-8": [("Nathan Aspinall", "sixth seed for the event", "pdc_schedule"),
                 ("Luke Littler", "world number one and reigning World Champion; his 2026 European Tour seeding is not published in the draw bracket captured here", "pdc_schedule")],
}
for fid, h, a, hm, am, hs, asd, session in DARTS:
    fx(sport="Darts", competition="Machineseker European Championship".replace("Machineseker", "Machineseeker"),
       id=fid, home=h, away=a,
       time_display=f"24 October 2026, Round Two {session} (13:00-17:00 / 19:00-23:00 CEST)",
       venue="Westfalenhalle, Dortmund", source="pdc_schedule", stats_source="pdc_rules",
       inputs={"format": "best of 11 legs", "home_et_money": hm or None, "away_et_money": am or None,
               "home_seed": hs, "away_seed": asd, "session": session},
       facts=DARTS_FACTS[fid])

# --- Tennis ---------------------------------------------------------------
TN = [
    ("ten-almaty-sf1", "Daniil Medvedev", "Alexander Bublik", "2026-10-24", "Not before 18:00 local", 3660, 2275,
     [("Daniil Medvedev", "world no.5 with 3,660 ATP points; beat Terence Atmane 6-4 6-4 in the quarter-final", "atp_rankings"),
      ("Alexander Bublik", "world no.19 with 2,275 ATP points; beat Karen Khachanov 4-6 7-6(5) 7-6(5)", "atp_rankings")]),
    ("ten-almaty-sf2", "Nikoloz Basilashvili", "Stefanos Tsitsipas", "2026-10-24", "Not before 15:00 local", None, 1330,
     [("Stefanos Tsitsipas", "world no.39 with 1,330 ATP points, seeded seventh in Almaty", "atp_rankings"),
      ("Nikoloz Basilashvili", "qualified for the Almaty main draw; not inside the published top 100 held here", "atp_almaty")]),
    ("ten-vienna-q1a", "Vit Kopriva", "Lukas Neumayer", "2026-10-24", "Starts 11:30 local", None, None,
     [("Fixture", "Vienna Open qualifying round one, Centre Court, 24 October 2026, from 11:30 local", "atp_vienna")]),
    ("ten-vienna-q1b", "Joel Schwaerzler", "Titouan Droguet", "2026-10-24", "Followed by", None, None,
     [("Fixture", "Vienna Open qualifying round one, Centre Court, 24 October 2026", "atp_vienna")]),
    ("ten-vienna-q1c", "Fabian Marozsan", "Sebastian Sorger", "2026-10-24", "Followed by", None, None,
     [("Fixture", "Vienna Open qualifying round one, Centre Court, 24 October 2026", "atp_vienna")]),
]
for fid, h, a, day, disp, hp, ap, facts in TN:
    fx(sport="Tennis", competition="ATP Tour", id=fid, home=h, away=a,
       time_display=f"{day} {disp}", source="atp_almaty", stats_source="atp_rankings",
       inputs={"format": "best of three sets", "home_points": hp, "away_points": ap},
       facts=facts)

# --- Golf -----------------------------------------------------------------
fx(sport="Golf", competition="PGA TOUR", id="golf-bermuda",
   home="Butterfield Bermuda Championship", away=None,
   time_display="22-25 October 2026, round three from 24 October", venue="Port Royal Golf Course, Southampton, Bermuda",
   source="pgatour", stats_source="pgatour",
   inputs={"market": "outright", "after_round": 2, "cut_line": -4, "field": [
       ("Kensei Hirata", "JPN", -13, 65, 64, 129, "F"), ("Chandler Blanchet", "USA", -13, 62, 67, 129, "F"),
       ("Seamus Power", "IRL", -12, 66, 64, 130, "F*"), ("Corey Conners", "CAN", -12, 63, 67, 130, "F*"),
       ("Eric Cole", "USA", -12, 65, None, 65, "17"), ("David Skinns", "ENG", -11, 68, 63, 131, "F"),
       ("Denny McCarthy", "USA", -11, 67, 64, 131, "F"), ("Greyson Sigg", "USA", -11, 67, 64, 131, "F")]},
   facts=[("Leaderboard", "After 36 holes: Hirata and Blanchet -13 (129), Power and Conners -12 (130), Cole -12 through 17 holes", "pgatour"),
          ("Cut line", "-4 at Port Royal Golf Course", "pgatour"),
          ("Schedule", "Butterfield Bermuda Championship, Port Royal Golf Course, 22-25 October 2026", "pgatour")])

fx(sport="Golf", competition="DP World Tour", id="golf-genesis",
   home="Genesis Championship", away=None,
   time_display="Round three from 24 October 2026, tee times from 09:06 local", venue="Korea",
   source="dpwt", stats_source="dpwt",
   inputs={"market": "outright", "after_round": 2, "field": [
       ("Antoine Rozner", "FRA", -10, 67, 65, 132), ("Casey Jarvis", "RSA", -10, 65, 67, 132),
       ("Martin Couvra", "FRA", -7, 69, 66, 135), ("Filippo Celli", "ITA", -7, 69, 66, 135),
       ("Ryan Fox", "NZL", -7, 68, 67, 135), ("Sanghun Shin", "KOR", -7, 66, 69, 135),
       ("Si Woo Kim", "KOR", -6, 67, 69, 136), ("Daihan Lee", "KOR", -6, 69, 67, 136)]},
   facts=[("Leaderboard", "After two rounds: Rozner and Jarvis -10 (132), Couvra, Celli, Fox and Shin -7 (135)", "dpwt"),
          ("Schedule", "Genesis Championship, DP World Tour, round three from 24 October 2026", "dpwt")])

# --- Greyhounds ----------------------------------------------------------
fx(sport="Greyhounds", competition="GBGB Category One", id="grey-scurry",
   home="Arena Racing Company Scurry Gold Cup Final", away=None,
   time_display="24 October 2026 (evening card)", venue="Dunstall Park, Wolverhampton",
   source="gbgb_schedule", stats_source="gbgb_scurry",
   inputs={"market": "outright", "distance_m": 270, "purse_gbp": 12500, "runners": [
       ("Shadow Storm", "R P Rees", 15.66), ("Avarua Lake", "R P Rees", 15.86),
       ("Roanna Mamba", "M P Brown", 15.73), ("Ballinakill Liam", "M A Wallis", None),
       ("Magical Jason", "K R Hutton", None), ("Newinn Souly", "unknown", None)]},
   facts=[("Final", "Arena Racing Company Scurry Gold Cup Final, 270m, Dunstall Park, 24 October 2026, £12,500 to the winner", "gbgb_schedule"),
          ("Semi-final 3", "Shadow Storm won in 15.66s (-5), a length and a quarter clear of Newinn Souly", "gbgb_scurry"),
          ("Semi-final 1", "Avarua Lake won in 15.86s (-5) from Ballinakill Liam", "gbgb_scurry"),
          ("Semi-final 2", "Roanna Mamba won in 15.73s (-5) from Magical Jason", "gbgb_scurry")])

fx(sport="Greyhounds", competition="GBGB Category One", id="grey-oaks",
   home="Premier Greyhound Racing Oaks Final", away=None,
   time_display="24 October 2026 (evening card)", venue="Dunstall Park, Wolverhampton",
   source="gbgb_schedule", stats_source="gbgb_oaks",
   inputs={"market": "outright", "distance_m": 480, "purse_gbp": 20000, "runners": [
       ("Fahrenheit Jess", "G D Holland", 27.87), ("Slingshot Poppy", "B Fairbairn", 27.90),
       ("Signet Nayla", "K R Hutton", 28.35), ("Strike It Skye", "M A Wallis", None),
       ("Holding Hollie", "R Taberner", None), ("Ballydoyle Tina", "G D Holland", None)]},
   facts=[("Final", "Premier Greyhound Racing Oaks Final, 480m, Dunstall Park, 24 October 2026, £20,000 to the winner", "gbgb_schedule"),
          ("Semi-final 2", "Fahrenheit Jess made all in a fastest-of-the-round 27.87s (-10) from Holding Hollie", "gbgb_oaks"),
          ("Semi-final 3", "Slingshot Poppy won in 27.90s (-10) from Ballydoyle Tina", "gbgb_oaks"),
          ("Semi-final 1", "Signet Nayla won in 28.35s (-10) from Strike It Skye", "gbgb_oaks")])

# --- Handball ------------------------------------------------------------
LNH = {"Paris": (7, 7, 0, 0, 239, 190), "Nantes": (7, 6, 1, 0, 244, 203), "Montpellier": (7, 4, 1, 2, 234, 205),
       "Nîmes": (7, 5, 2, 0, 228, 228), "Limoges": (7, 4, 3, 0, 234, 214), "Chartres": (7, 3, 3, 1, 204, 224),
       "Tremblay": (7, 3, 3, 1, 231, 227), "Aix": (7, 3, 4, 0, 227, 223), "Sélestat": (7, 3, 4, 0, 208, 217),
       "Chambéry": (7, 2, 3, 2, 224, 231), "Saran": (7, 3, 4, 0, 202, 216), "Caen": (7, 3, 4, 0, 198, 235),
       "Toulouse": (7, 3, 4, 0, 198, 201), "Saint-Raphaël": (7, 2, 5, 0, 207, 225),
       "Cesson-Rennes": (7, 1, 6, 0, 209, 227), "Dunkerque": (7, 1, 6, 0, 175, 196)}
HB = [("hb-nantes-chambery", "Nantes", "Chambéry", "2026-10-24T19:00:00+02:00", "Sat 24 October, 19:00 local"),
      ("hb-sr-paris", "Saint-Raphaël", "Paris", "2026-10-25T16:00:00+01:00", "Sun 25 October, 16:00 local"),
      ("hb-montpellier-saran", "Montpellier", "Saran", "2026-10-25T17:00:00+01:00", "Sun 25 October, 17:00 local"),
      ("hb-paris-aalborg", "Paris", "Aalborg", "2026-10-28T20:45:00+01:00", "Wed 28 October, 20:45 local (EHF CL R6)"),
      ("hb-montpellier-bucarest", "Montpellier", "Bucarest", "2026-10-29T20:45:00+01:00", "Thu 29 October, 20:45 local (EHF CL R6)"),
      ("hb-plock-nantes", "Plock", "Nantes", "2026-10-28T18:45:00+01:00", "Wed 28 October, 18:45 local (EHF CL R6)")]
for fid, home, away, start, disp in HB:
    if home in LNH and away in LNH:
        inputs = {"home": dict(zip(("gp", "w", "l", "d", "gf", "ga"), LNH[home])),
                  "away": dict(zip(("gp", "w", "l", "d", "gf", "ga"), LNH[away])),
                  "competition": "Daikin StarLigue"}
        facts = [(home, f"{LNH[home][1]}-{LNH[home][2]}-{LNH[home][3]} after 7 rounds, {LNH[home][4]} goals for, {LNH[home][5]} against", "lnh_table"),
                 (away, f"{LNH[away][1]}-{LNH[away][2]}-{LNH[away][3]} after 7 rounds, {LNH[away][4]} goals for, {LNH[away][5]} against", "lnh_table")]
    else:
        inputs = {"competition": "EHF Champions League"}
        facts = [("Fixture", f"EHF Champions League Round 6, {home} v {away}, 2026", "lnh_ehf")]
    fx(sport="Handball", competition=inputs["competition"], id=fid, home=home, away=away,
       start_utc=start, time_display=disp, venue=None, source="lnh_cal", stats_source="lnh_table",
       inputs=inputs, facts=facts)

# --- Motor Racing --------------------------------------------------------
fx(sport="Motor Racing", competition="Formula 1", id="f1-usgp",
   home="United States Grand Prix", away=None,
   start_utc="2026-10-25T20:00:00Z", time_display="25 October 2026, 16:00 track time (UTC-5, per F1 schedule)",
   venue="Circuit of The Americas, Austin",
   source="f1_usgp", stats_source="f1_drivers",
   inputs={"market": "race winner", "circuit_km": 5.513, "laps": 56, "distance_km": 308.432,
           "fp1": [("Charles Leclerc", "1:36.052"), ("Max Verstappen", "+0.084s"), ("Lando Norris", "+0.245s"),
                   ("George Russell", "+0.326s"), ("Kimi Antonelli", "+0.481s")],
           "points": {"Kimi Antonelli": 340, "George Russell": 238, "Lewis Hamilton": 229, "Max Verstappen": 221,
                      "Charles Leclerc": 215, "Lando Norris": 201, "Oscar Piastri": 138, "Isack Hadjar": 97,
                      "Liam Lawson": 75, "Pierre Gasly": 41, "Arvid Lindblad": 38, "Franco Colapinto": 27,
                      "Oliver Bearman": 23, "Nico Hulkenberg": 13, "Gabriel Bortoleto": 10}},
   facts=[("Circuit", "Circuit of The Americas: 5.513 km, 56 laps, 308.432 km race distance", "f1_usgp"),
          ("FP1", "Leclerc 1:36.052 from Verstappen +0.084s, Norris +0.245s, Russell +0.326s, Antonelli +0.481s", "f1_usgp"),
          ("Standings", "Antonelli 340, Russell 238, Hamilton 229, Verstappen 221, Leclerc 215, Norris 201 after Round 17", "f1_drivers"),
          ("Session", "Qualifying 24 October 17:00 track time; race 25 October 16:00 track time", "f1_usgp")])

fx(sport="Motor Racing", competition="Formula 1", id="f1-wdc",
   home="Formula 1 Drivers' Championship 2026", away=None,
   time_display="Season ends 6 December 2026", venue=None,
   source="f1_drivers", stats_source="f1_drivers",
   inputs={"market": "outright", "rounds_completed": 17, "points": {"Kimi Antonelli": 340, "George Russell": 238,
           "Lewis Hamilton": 229, "Max Verstappen": 221, "Charles Leclerc": 215, "Lando Norris": 201,
           "Oscar Piastri": 138}},
   facts=[("Drivers' Championship", "After 17 rounds: Antonelli 340, Russell 238, Hamilton 229, Verstappen 221, Leclerc 215, Norris 201, Piastri 138", "f1_drivers")])

# --- Rugby League --------------------------------------------------------
RL = [("rlwc-png-samoa", "Papua New Guinea", "Samoa", "2026-10-24T04:25:00Z", "24 October, 12:25am ET (NRL display)",
       "3rd", "2nd", "Port Moresby"),
      ("rlwc-eng-fra", "England", "France", "2026-10-24T06:35:00Z", "24 October, 2:35am ET (NRL display)",
       "4th", "6th", "HBF Park, Perth"),
      ("rlwc-nz-cook", "New Zealand", "Cook Islands", "2026-10-25T05:05:00Z", "25 October, 1:05am ET (NRL display)",
       "3rd", "4th", "One NZ Stadium, Christchurch"),
      ("rlwc-aus-fiji", "Australia", "Fiji", "2026-10-25T09:05:00Z", "25 October, 5:05am ET (NRL display)",
       "2nd", "1st", "Suncorp Stadium, Brisbane"),
      ("rlwc-r3-eng-png", "England", "Papua New Guinea", "2026-10-30T09:05:00Z", "30 October, 5:05am ET (NRL display)",
       "4th", "3rd", "WIN Stadium, Wollongong"),
      ("rlwc-r3-nz-fiji", "New Zealand", "Fiji", "2026-10-31T04:30:00Z", "31 October, 12:30am ET (NRL display)",
       "3rd", "1st", "Cbus Super Stadium, Gold Coast"),
      ("rlwc-r3-aus-cook", "Australia", "Cook Islands", "2026-10-31T09:05:00Z", "31 October, 5:05am ET (NRL display)",
       "2nd", "4th", "Queensland Country Bank Stadium, Townsville"),
      ("rlwc-r3-leb-fra", "Lebanon", "France", "2026-11-01T05:40:00Z", "1 November, 1:40am ET (NRL display)",
       "5th", "6th", "CommBank Stadium, Sydney"),
      ("rlwc-r3-ton-sam", "Tonga", "Samoa", "2026-11-01T08:05:00Z", "1 November, 4:05am ET (NRL display)",
       "1st", "2nd", "CommBank Stadium, Sydney")]
RL_MARGINS = {"rlwc-png-samoa": (24, 74), "rlwc-eng-fra": (-18, -74), "rlwc-nz-cook": (-2, -28),
              "rlwc-aus-fiji": (2, 28), "rlwc-r3-eng-png": (-18, 24), "rlwc-r3-nz-fiji": (-2, 28),
              "rlwc-r3-aus-cook": (2, -28), "rlwc-r3-leb-fra": (-24, -74), "rlwc-r3-ton-sam": (18, 74)}
RL_FACTS = {
    "rlwc-png-samoa": [("Round 1", "Papua New Guinea beat Lebanon 42-18 in Port Moresby", "nrl_r1"),
                       ("Round 1", "Samoa beat France 78-4 at CommBank Stadium", "nrl_r1"),
                       ("Ladder", "Samoa are 2nd and Papua New Guinea 3rd after Round 1", "nrl_r2")],
    "rlwc-eng-fra": [("Round 1", "England lost 12-30 to Tonga at HBF Park", "nrl_r1"),
                     ("Round 1", "France lost 4-78 to Samoa", "nrl_r1"),
                     ("Ladder", "England 4th, France 6th", "nrl_r2")],
    "rlwc-nz-cook": [("Round 1", "New Zealand lost 22-24 to Australia", "nrl_r1"),
                     ("Round 1", "Cook Islands lost 12-40 to Fiji", "nrl_r1"),
                     ("Ladder", "New Zealand 3rd, Cook Islands 4th", "nrl_r2")],
    "rlwc-aus-fiji": [("Round 1", "Australia beat New Zealand 24-22", "nrl_r1"),
                      ("Round 1", "Fiji beat Cook Islands 40-12", "nrl_r1"),
                      ("Ladder", "Fiji are 1st and Australia 2nd on points difference after Round 1", "nrl_r2")],
    "rlwc-r3-eng-png": [("Round 1", "England lost 12-30 to Tonga; Papua New Guinea beat Lebanon 42-18", "nrl_r1")],
    "rlwc-r3-nz-fiji": [("Round 1", "New Zealand lost 22-24 to Australia; Fiji beat Cook Islands 40-12", "nrl_r1")],
    "rlwc-r3-aus-cook": [("Round 1", "Australia beat New Zealand 24-22; Cook Islands lost 12-40 to Fiji", "nrl_r1")],
    "rlwc-r3-leb-fra": [("Round 1", "Lebanon lost 18-42 to Papua New Guinea; France lost 4-78 to Samoa", "nrl_r1")],
    "rlwc-r3-ton-sam": [("Round 1", "Tonga beat England 30-12; Samoa beat France 78-4", "nrl_r1")],
}
for fid, home, away, start, disp, hpos, apos, venue in RL:
    fx(sport="Rugby League", competition="Rugby League World Cup 2026", id=fid, home=home, away=away,
       start_utc=start, time_display=disp, venue=venue, source="nrl_r2", stats_source="nrl_r1",
       inputs={"home_ladder": hpos, "away_ladder": apos,
               "home_margin": RL_MARGINS[fid][0], "away_margin": RL_MARGINS[fid][1]},
       facts=RL_FACTS[fid])

# --- Rugby Union ---------------------------------------------------------
PREM = {"Gloucester Rugby": (3, 2, 0, 1, 62, 12), "Northampton Saints": (3, 2, 0, 1, 41, 11),
        "Saracens": (3, 2, 0, 1, 21, 11), "Leicester Tigers": (3, 2, 0, 1, 10, 11),
        "Bath Rugby": (3, 2, 0, 1, -1, 11), "Bristol Bears": (3, 2, 0, 1, 2, 10),
        "Sale Sharks": (3, 2, 0, 1, -2, 9), "Exeter Chiefs": (3, 1, 0, 2, -21, 8),
        "Newcastle Red Bulls": (3, 0, 0, 3, -44, 4), "Harlequins": (3, 0, 0, 3, -68, 2)}
RU = [("ru-leicester-northampton", "Leicester Tigers", "Northampton Saints", "Sat 24 Oct, 10:05 viewer-local"),
      ("ru-bristol-exeter", "Bristol Bears", "Exeter Chiefs", "Sat 24 Oct, 12:30 viewer-local"),
      ("ru-quins-saracens", "Harlequins", "Saracens", "Sun 25 Oct, 11:00 viewer-local"),
      ("ru-bulls-ulster", "Vodacom Bulls", "Ulster", "Sat 24 Oct, 07:45 (URC local)"),
      ("ru-stormers-scarlets", "DHL Stormers", "Scarlets", "Sat 24 Oct, 10:00 (URC local)"),
      ("ru-benetton-glasgow", "Benetton Rugby", "Glasgow Warriors", "Sat 24 Oct, 10:00 (URC local)"),
      ("ru-leinster-munster", "Leinster", "Munster", "Sat 24 Oct, 13:00 (URC local)"),
      ("ru-ospreys-dragons", "Ospreys", "Dragons RFC", "Sat 24 Oct, 14:00 (URC local)")]
for fid, home, away, disp in RU:
    if home in PREM and away in PREM:
        h = PREM[home]; a = PREM[away]
        inputs = {"competition": "Gallagher PREM", "home": {"p": h[0], "w": h[1], "d": h[2], "l": h[3], "pd": h[4], "pts": h[5]},
                  "away": {"p": a[0], "w": a[1], "d": a[2], "l": a[3], "pd": a[4], "pts": a[5]}}
        facts = [(home, f"{h[1]}-{h[2]}-{h[3]} after three rounds, points difference {h[4]:+d}, {h[5]} league points", "prem_table"),
                 (away, f"{a[1]}-{a[2]}-{a[3]} after three rounds, points difference {a[4]:+d}, {a[5]} league points", "prem_table"),
                 ("Round 4", f"{home} v {away}, Gallagher PREM Round 4, {disp}", "prem_fixtures")]
        src, st = "prem_fixtures", "prem_table"
    else:
        inputs = {"competition": "United Rugby Championship"}
        facts = [("Round 4", f"{home} v {away}, URC Round 4, {disp}", "urc_round4")]
        src, st = "urc_round4", "urc_round4"
    fx(sport="Rugby Union", competition=inputs["competition"], id=fid, home=home, away=away,
       time_display=disp, source=src, stats_source=st, inputs=inputs, facts=facts)

# --- Volleyball ----------------------------------------------------------
SL = {"Cisterna Volley": (3, 1, 1, 0, 3, 0, 79, 56), "Gas Sales Bluenergy Piacenza": (3, 1, 1, 0, 3, 0, 75, 56),
      "Itas Trentino": (3, 1, 1, 0, 3, 0, 75, 61), "Cucine Lube Civitanova": (3, 1, 1, 0, 3, 0, 78, 65),
      "Tinet Prata di Pordenone": (3, 1, 1, 0, 3, 1, 94, 91), "Sir Susa Scai Perugia": (2, 1, 1, 0, 3, 2, 114, 95),
      "Acqua Sant'Anna Cuneo": (1, 1, 0, 1, 2, 3, 95, 114), "Vero Volley Monza": (0, 1, 0, 1, 1, 3, 91, 94),
      "Rana Verona": (0, 1, 0, 1, 0, 3, 65, 78), "Valsa Group Modena": (0, 1, 0, 1, 0, 3, 61, 75),
      "Pallavolo Padova": (0, 1, 0, 1, 0, 3, 56, 75), "Allianz Milano": (0, 1, 0, 1, 0, 3, 56, 79)}
VB = [("vb-perugia-prata", "Sir Susa Scai Perugia", "Tinet Prata di Pordenone", "Sun 25 Oct, 18:00 local"),
      ("vb-trentino-cisterna", "Itas Trentino", "Cisterna Volley", "Sun 25 Oct, 17:00 local"),
      ("vb-piacenza-modena", "Gas Sales Bluenergy Piacenza", "Valsa Group Modena", "Sun 25 Oct, 18:00 local"),
      ("vb-civitanova-padova", "Cucine Lube Civitanova", "Pallavolo Padova", "Sun 25 Oct, 18:00 local"),
      ("vb-milano-cuneo", "Allianz Milano", "Acqua Sant'Anna Cuneo", "Sun 25 Oct, 19:00 local"),
      ("vb-monza-verona", "Vero Volley Monza", "Rana Verona", "Sun 25 Oct, 18:00 local"),
      ("vb-friedrichshafen-karlsruhe", "VfB Friedrichshafen", "BADEN VOLLEYS Karlsruhe", "Sat 24 Oct, 6:30 PM (VBL schedule)"),
      ("vb-lueneburg-warnemuende", "SVG Lüneburg", "SV Warnemünde", "Sat 24 Oct, 7:00 PM (VBL schedule)"),
      ("vb-giesen-berlin", "Helios GRIZZLYS Giesen", "BERLIN RECYCLING Volleys", "Sat 24 Oct, 7:30 PM (VBL schedule)"),
      ("vb-dueren-muenchen", "SWD powervolleys Düren", "WWK Volleys München", "Sat 24 Oct, 7:30 PM (VBL schedule)")]
for fid, home, away, disp in VB:
    if home in SL and away in SL:
        h, a = SL[home], SL[away]
        inputs = {"competition": "SuperLega", "home": {"pts": h[0], "played": h[1], "sets_w": h[4], "sets_l": h[5], "pf": h[6], "pa": h[7]},
                  "away": {"pts": a[0], "played": a[1], "sets_w": a[4], "sets_l": a[5], "pf": a[6], "pa": a[7]}}
        facts = [(home, f"{h[1]} match played, {h[4]}-{h[5]} sets, {h[6]} points for and {h[7]} against in Round 1", "legavolley_table"),
                 (away, f"{a[1]} match played, {a[4]}-{a[5]} sets, {a[6]} points for and {a[7]} against in Round 1", "legavolley_table"),
                 ("Round 2", f"{home} v {away}, {disp}", "legavolley_cal")]
        src, st = "legavolley_cal", "legavolley_table"
    else:
        inputs = {"competition": "1. Bundesliga Männer"}
        facts = [("Round 2", f"{home} v {away}, {disp}", "vbl_schedule")]
        src, st = "vbl_schedule", "vbl_table"
    fx(sport="Volleyball", competition=inputs["competition"], id=fid, home=home, away=away,
       time_display=disp, source=src, stats_source=st, inputs=inputs, facts=facts)

# --- Gaelic Sports -------------------------------------------------------
GAA = [
    ("gaa-shinty-hurling", "Ireland", "Scotland", "Hurling-Shinty International", "24 October 2026, 18:00",
     "SuperValu Páirc Uí Chaoimh, Cork", "gaa_fixtures", None,
     [("Fixture", "Hurling-Shinty International, Ireland v Scotland, SuperValu Páirc Uí Chaoimh, 24 October 2026, 18:00, referee Eamonn Furlong", "gaa_fixtures")]),
    ("gaa-cork-psfc", "St Finbarr's", "Nemo Rangers", "Cork Premier Senior Football Championship Final", "25 October 2026, 16:00",
     "SuperValu Páirc Uí Chaoimh", "gaacork", None,
     [("Semi-finals", "Nemo Rangers beat Carrigaline 1-15 to 0-16; St Finbarr's beat Clonakilty 2-12 to 0-16", "gaacork"),
      ("Fixture", "Cork Premier Senior Football Championship Final, St Finbarr's v Nemo Rangers, 25 October 2026, 16:00, referee David Murnane", "munster_gaa")]),
    ("gaa-kerry-sfc", "Dr Crokes", "Kenmare Shamrocks", "Kerry Senior Football Championship Final", "25 October 2026, 14:00",
     "Fitzgerald Stadium, Killarney", "kerrygaa", None,
     [("Fixture", "Kerry Senior Football Championship Final, Dr Crokes v Kenmare Shamrocks, Fitzgerald Stadium, 25 October 2026, 14:00, referee Sean Joy", "kerrygaa")]),
    ("gaa-waterford-sfc", "Rathgormack", "The Nire", "Waterford Senior Football Championship Final", "25 October 2026, 14:30",
     "Cappoquin Logistics Fraher Field, Dungarvan", "waterfordgaa", None,
     [("Semi-finals", "Rathgormack beat Gaultier 1-14 to 0-15; The Nire beat Abbeyside-Ballinacourty 0-12 to 0-5", "waterfordgaa"),
      ("Fixture", "Waterford Senior Football Championship Final, Rathgormack v The Nire, Fraher Field, 25 October 2026, 14:30, referee Killian O'Sullivan", "munster_gaa")]),
    ("gaa-limerick-shc", "Na Piarsaigh", "Kilmallock", "Limerick Senior Hurling Championship Final", "25 October 2026, 15:45",
     "TUS Gaelic Grounds, Limerick", "limerickgaa", None,
     [("Semi-final", "Na Piarsaigh beat Doon 2-24 to 3-16 to reach the final", "limerickgaa"),
      ("Fixture", "Limerick Senior Hurling Championship Final, Na Piarsaigh v Kilmallock, TUS Gaelic Grounds, 25 October 2026, 15:45, referee John O'Halloran", "munster_gaa")]),
]
for fid, home, away, comp, disp, venue, src, olbg, facts in GAA:
    fx(sport="Gaelic Sports", competition=comp, id=fid, home=home, away=away, time_display=disp,
       venue=venue, source=src, stats_source="munster_gaa", olbg_event_id=olbg, inputs={"format": "championship"},
       facts=facts)

# ---------------------------------------------------------------------------
# Extra official sources referenced by facts
# ---------------------------------------------------------------------------
SOURCES.extend([
    ("el_standings", "EuroLeague Basketball", "https://www.euroleaguebasketball.net/en/euroleague/standings/",
     "EuroLeague 2026-27 regular-season table after seven rounds with points for/against"),
    ("el_game_center", "EuroLeague Basketball", "https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026",
     "EuroLeague Round 8 fixtures, dates and venues"),
])
SOURCE_URL.update({key: url for key, _pub, url, _what in SOURCES if key not in SOURCE_URL})


def main():
    os.makedirs(CAP, exist_ok=True)
    for key, pub, url, what in SOURCES:
        SOURCE_URL.setdefault(key, url)
    sources = [{"key": k, "publisher": p, "url": u, "what": w, "fetched_utc": CAPTURED_UTC, "session": SESSION}
               for k, p, u, w in SOURCES]
    with open(os.path.join(OUT, "sources.json"), "w") as f:
        json.dump({"captured_utc": CAPTURED_UTC, "session": SESSION, "count": len(sources),
                   "sources": sources}, f, indent=1, ensure_ascii=False)

    rows = []
    for f in FIXTURES:
        row = dict(f)
        row["official_source_url"] = SOURCE_URL[f["source"]]
        row["stats_source_url"] = SOURCE_URL.get(f.get("stats_source") or "", f.get("stats_source") or "")
        if f.get("injury_source"):
            row["injury_source_url"] = SOURCE_URL[f["injury_source"]]
        row["facts"] = [{"team_or_item": t, "value": v, "source_key": k, "source_url": SOURCE_URL[k]}
                        for t, v, k in f["facts"]]
        rows.append(row)
    with open(os.path.join(OUT, "fixtures.json"), "w") as f:
        json.dump({"captured_utc": CAPTURED_UTC, "session": SESSION,
                   "sport_count": len({r["sport"] for r in rows}), "count": len(rows), "fixtures": rows},
                  f, indent=1, ensure_ascii=False)

    # Verbatim-style capture bundles, one per source family, for audit.
    bundles = {}
    for r in rows:
        bundles.setdefault(r["source"], []).append({
            "fixture_id": r["id"], "sport": r["sport"], "home": r["home"], "away": r["away"],
            "time_display": r["time_display"], "venue": r.get("venue"),
            "facts": [{"item": x["team_or_item"], "text": x["value"]} for x in r["facts"]]})
    for key, items in bundles.items():
        with open(os.path.join(CAP, f"{key}.json"), "w") as f:
            json.dump({"source_key": key, "url": SOURCE_URL[key], "captured_utc": CAPTURED_UTC,
                       "session": SESSION, "readings": items}, f, indent=1, ensure_ascii=False)
    print(f"fixtures={len(rows)} sports={len({r['sport'] for r in rows})} sources={len(sources)} captures={len(bundles)}")


if __name__ == "__main__":
    main()
