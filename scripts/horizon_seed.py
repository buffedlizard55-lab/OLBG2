"""Horizon desk (session arena/9c5af337-olbg2) — official fixture & source capture.

Writes:
  data/horizon/sources.json
  data/horizon/fixtures.json
  data/horizon/olbg_taxonomy.json
  data/horizon/repo_audit.json
  data/horizon/captures/<source_key>.json

Run: python3 scripts/horizon_seed.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "horizon")
CAP = os.path.join(OUT, "captures")
CAPTURED_UTC = "2026-10-23T21:40:00Z"
SESSION = "arena/9c5af337-olbg2"

SOURCES = [
    ("olbg_hub", "OLBG", "https://www.olbg.com/betting-tips",
     "OLBG 15-sport taxonomy and US-egress hub/event route verification"),
    ("nhle_schedule", "National Hockey League", "https://api-web.nhle.com/v1/schedule/2026-10-23",
     "Official NHL schedule feed for 2026-10-23 through 2026-10-25 with startTimeUTC, venues, and provider moneylines"),
    ("nhle_standings", "National Hockey League", "https://api-web.nhle.com/v1/standings/2026-10-23",
     "Official NHL standings feed as of 2026-10-23T21:27:30Z with games played, points, goals for/against, L10, and streaks"),
    ("nba_games", "National Basketball Association", "https://www.nba.com/games?date=2026-10-23",
     "Official NBA slate for Friday 23 October 2026 with tip times and opening records"),
    ("nba_standings", "National Basketball Association", "https://www.nba.com/standings",
     "Official 2026-27 NBA standings after opening-night games"),
    ("nba_injury", "National Basketball Association",
     "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf",
     "Official NBA Referee Injury Report dated 10/23/2026 03:15 PM ET"),
    ("el_standings", "EuroLeague Basketball", "https://www.euroleaguebasketball.net/en/euroleague/standings/",
     "Official 2026-27 EuroLeague regular-season table after seven rounds with points for and against"),
    ("el_game_center", "EuroLeague Basketball",
     "https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=8&season=E2026",
     "Official EuroLeague Round 8 schedule for 27-28 October 2026"),
    ("mlb_schedule", "Major League Baseball",
     "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-11-02",
     "Official MLB StatsAPI 2026 World Series schedule (Tampa Bay Rays vs Milwaukee Brewers)"),
    ("mlb_brewers", "Major League Baseball",
     "https://statsapi.mlb.com/api/v1/Schedule?sportId=1&teamId=158&startDate=2026-10-22&endDate=2026-11-02&hydrate=team,probablePitcher,linescore,decisions",
     "Official MLB StatsAPI hydrated World Series schedule with probable pitchers and season records"),
    ("mlb_standings", "Major League Baseball",
     "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason",
     "Official 2026 MLB 162-game regular-season standings, run totals, and home/road splits"),
    ("mlb_pitchers", "Major League Baseball",
     "https://statsapi.mlb.com/api/v1/people?personIds=694813,608379,801403,656876&hydrate=stats(group=%5Bpitching%5D,type=%5Bseason%5D,season=2026)",
     "Official 2026 MLB pitching statistics for Jacob Misiorowski, Nick Martinez, Logan Henderson, and Drew Rasmussen"),
    ("cricket_au", "Cricket Australia", "https://www.cricket.com.au/matches",
     "Official Cricket Australia match centre listing upcoming domestic One-Day Cup and international fixtures"),
    ("cricket_au_done", "Cricket Australia", "https://www.cricket.com.au/matches?tab=completed",
     "Official Cricket Australia completed match results through 23 October 2026"),
    ("wst_matches", "World Snooker Tour", "https://www.wst.tv/matches/",
     "Official WST BetVictor Northern Ireland Open 2026 quarter-final results and semi-final schedule"),
    ("wst_rankings", "World Snooker Tour", "https://www.wst.tv/rankings/",
     "Official Johnstone's Paint World Rankings and 2026/27 One Year List"),
    ("wst_ic", "World Snooker Tour",
     "https://www.wst.tv/match-centre/ee54f470-4821-4fd6-a5f4-db32dc475890",
     "Official WST International Championship 2026 match-centre draw and player season statistics"),
    ("pdc_schedule", "Professional Darts Corporation",
     "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-schedule-play",
     "Official 2026 Machineseeker European Championship draw, seedings, and Dortmund session schedule"),
    ("pdc_day_one", "Professional Darts Corporation",
     "https://www.pdc.tv/news/2026/october/22/nine-dart-star-woodhouse-sets-up-van-veen-clash-dortmund",
     "Official PDC European Championship Day One Round One results and averages"),
    ("pdc_rules", "Professional Darts Corporation", "https://www.pdc.tv/order-of-merit-rules",
     "Official PDC European Tour Order of Merit ranking rules and format regulations"),
    ("atp_almaty", "ATP Tour", "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule",
     "Official ATP 250 Almaty Open Day 8 (Saturday 24 October 2026) semifinal schedule and QF results"),
    ("atp_brussels", "ATP Tour", "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule",
     "Official ATP 250 Brussels Day 8 (Saturday 24 October 2026) semifinal schedule and QF results"),
    ("atp_lyon", "ATP Tour", "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule",
     "Official ATP 250 Grand Prix Auvergne-Rhone-Alpes (Lyon) QF results and semifinal draw"),
    ("atp_basel", "ATP Tour", "https://www.atptour.com/en/scores/current/basel/328/daily-schedule",
     "Official ATP 500 Swiss Indoors Basel Day 1 (Saturday 24 October 2026) qualifying schedule"),
    ("atp_vienna", "ATP Tour", "https://www.atptour.com/en/scores/current/vienna/337/daily-schedule",
     "Official ATP 500 Erste Bank Open Vienna Day 1 (Saturday 24 October 2026) qualifying schedule"),
    ("atp_rankings", "ATP Tour", "https://www.atptour.com/en/rankings/singles?rankRange=0-100",
     "Official PIF ATP Singles Rankings Top 100 dated 2026.10.19"),
    ("pgatour", "PGA TOUR", "https://www.pgatour.com/leaderboard",
     "Official 2026 Butterfield Bermuda Championship 36-hole leaderboard at Port Royal Golf Course"),
    ("dpwt", "DP World Tour",
     "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/leaderboard?round=2",
     "Official 2026 Genesis Championship 36-hole leaderboard on the DP World Tour"),
    ("gbgb_schedule", "Greyhound Board of Great Britain", "https://www.gbgb.org.uk/open-race-schedule/",
     "Official GBGB Category One open-race schedule for Dunstall Park (24 October 2026)"),
    ("gbgb_scurry", "Greyhound Board of Great Britain",
     "https://www.gbgb.org.uk/racing-results/?meetingId=435688&raceId=1198332",
     "Official GBGB Dunstall Park Scurry Gold Cup semi-final results and winning times"),
    ("gbgb_oaks", "Greyhound Board of Great Britain",
     "https://www.gbgb.org.uk/racing-results/?meetingId=435688&raceId=1198335",
     "Official GBGB Dunstall Park Premier Greyhound Racing Oaks semi-final results and winning times"),
    ("lnh_cal", "Ligue Nationale de Handball", "https://www.lnh.fr/daikin-starligue/calendrier",
     "Official LNH Daikin StarLigue 2026/27 Journée 08 results (23 Oct) and weekend fixtures (24-25 Oct)"),
    ("lnh_table", "Ligue Nationale de Handball", "https://www.lnh.fr/daikin-starligue/classement",
     "Official LNH Daikin StarLigue 2026/27 standings table"),
    ("lnh_ehf", "Ligue Nationale de Handball", "https://www.lnh.fr/autres-competitions/ligue-des-champions",
     "Official LNH EHF Champions League Round 6 schedule for French clubs"),
    ("f1_usgp", "Formula 1", "https://www.formula1.com/en/racing/2026/united-states",
     "Official 2026 Formula 1 United States Grand Prix hub, circuit specs, and FP1 classification"),
    ("f1_drivers", "Formula 1", "https://www.formula1.com/en/results/2026/drivers",
     "Official 2026 FIA Formula One World Championship Drivers' Standings after 17 rounds"),
    ("nrl_r2", "National Rugby League", "https://www.nrl.com/draw/?competition=131&round=2&season=2026",
     "Official RLWC 2026 Round 2 draw and results (including Tonga 36-0 Lebanon)"),
    ("nrl_r1", "National Rugby League", "https://www.nrl.com/draw/?competition=131&round=1&season=2026",
     "Official RLWC 2026 Round 1 completed results and margins"),
    ("prem_fixtures", "Premiership Rugby", "https://www.premrugby.com/fixtures-results",
     "Official Gallagher PREM 2026/27 Round 4 fixtures"),
    ("prem_table", "Premiership Rugby", "https://www.premrugby.com/standings",
     "Official Gallagher PREM 2026/27 standings after Round 3"),
    ("urc_round4", "United Rugby Championship", "https://stats.unitedrugby.com/match-centre/2026-27/4",
     "Official URC 2026/27 Round 4 Friday full-time results and Saturday fixtures"),
    ("urc_table", "United Rugby Championship", "https://stats.unitedrugby.com/match-centre/table/2026-27",
     "Official URC 2026/27 league table with W-D-L, PF, PA, DIFF, TF, TA, and league points"),
    ("legavolley_cal", "Lega Pallavolo Serie A", "https://www.legavolley.it/calendario/?idCampionato=999",
     "Official Italian SuperLega Credem Banca 2026/27 Round 2 schedule (25 October 2026)"),
    ("legavolley_table", "Lega Pallavolo Serie A", "https://www.legavolley.it/classifica/?IdCampionato=999",
     "Official Italian SuperLega Credem Banca 2026/27 standings and Round 1 set/point records"),
    ("vbl_schedule", "Volleyball Bundesliga",
     "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/spielplan.xhtml",
     "Official German 1. Bundesliga Männer Round 2 schedule (24 October 2026)"),
    ("vbl_table", "Volleyball Bundesliga",
     "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_maenner/spielplan.xhtml",
     "Official German 1. Bundesliga Männer opener context"),
    ("gaa_fixtures", "Gaelic Athletic Association", "https://www.gaa.ie/fixtures-results",
     "Official GAA fixtures hub for the 2026 Hurling-Shinty International in Cork"),
    ("munster_gaa", "Munster GAA", "https://munster.gaa.ie/fixtures-results/",
     "Official Munster GAA county final schedule and referee appointments"),
    ("gaacork", "Cork GAA", "https://gaacork.ie/fixtures-results/",
     "Official Cork GAA Premier Senior Football Championship semi-final results and final fixture"),
    ("kerrygaa", "Kerry GAA", "https://www.kerrygaa.ie/fixtures-results/",
     "Official Kerry GAA Senior Football Championship Final fixture"),
    ("waterfordgaa", "Waterford GAA", "https://www.waterfordgaa.ie/fixtures-results/",
     "Official Waterford GAA Senior Football Championship semi-final results and final fixture"),
    ("limerickgaa", "Limerick GAA", "https://limerickgaa.ie/fixtures-results/",
     "Official Limerick GAA Senior Hurling Championship semi-final result and final fixture"),
]
SOURCE_URL = {key: url for key, _pub, url, _what in SOURCES}

FIXTURES = []


def fx(**kw):
    FIXTURES.append(kw)


# --- 1. Ice Hockey: NHL (2 Friday + 12 Saturday) ---------------------------
NHL_STANDINGS = {
    "Carolina Hurricanes": (12, 8, 2, 2, 18, 43, 30, "6-2-2", "W1", "4-1-0", "4-1-2"),
    "Edmonton Oilers": (10, 8, 1, 1, 17, 41, 29, "8-1-1", "W5", "4-0-1", "4-1-0"),
    "Boston Bruins": (11, 8, 2, 1, 17, 41, 29, "7-2-1", "W1", "5-1-0", "3-1-1"),
    "Vegas Golden Knights": (12, 8, 4, 0, 16, 40, 35, "6-4-0", "W1", "5-2-0", "3-2-0"),
    "Washington Capitals": (10, 7, 2, 1, 15, 34, 23, "7-2-1", "W2", "5-1-0", "2-1-1"),
    "Detroit Red Wings": (10, 7, 2, 1, 15, 35, 25, "7-2-1", "W3", "4-1-1", "3-1-0"),
    "Tampa Bay Lightning": (9, 7, 2, 0, 14, 31, 23, "7-2-0", "W3", "5-0-0", "2-2-0"),
    "Minnesota Wild": (10, 6, 2, 2, 14, 36, 30, "6-2-2", "W2", "3-1-1", "3-1-1"),
    "Montreal Canadiens": (9, 6, 2, 1, 13, 33, 27, "6-2-1", "W2", "4-1-0", "2-1-1"),
    "Ottawa Senators": (9, 6, 2, 1, 13, 32, 26, "6-2-1", "W1", "4-1-0", "2-1-1"),
    "Pittsburgh Penguins": (10, 6, 3, 1, 13, 33, 29, "6-3-1", "W1", "3-1-1", "3-2-0"),
    "New Jersey Devils": (10, 6, 4, 0, 12, 33, 29, "6-4-0", "L1", "3-2-0", "3-2-0"),
    "Colorado Avalanche": (10, 5, 4, 1, 11, 41, 31, "5-4-1", "L2", "3-1-1", "2-3-0"),
    "Seattle Kraken": (10, 4, 3, 3, 11, 28, 29, "4-3-3", "OT1", "2-1-2", "2-2-1"),
    "Calgary Flames": (10, 5, 4, 1, 11, 29, 31, "5-4-1", "L1", "3-2-0", "2-2-1"),
    "Toronto Maple Leafs": (10, 4, 4, 2, 10, 31, 33, "4-4-2", "L1", "3-2-1", "1-2-1"),
    "Los Angeles Kings": (10, 4, 4, 2, 10, 28, 31, "4-4-2", "L1", "2-1-1", "2-3-1"),
    "Buffalo Sabres": (10, 4, 5, 1, 9, 29, 32, "4-5-1", "L1", "2-2-1", "2-3-0"),
    "Utah Mammoth": (10, 4, 5, 1, 9, 28, 33, "4-5-1", "L2", "2-2-1", "2-3-0"),
    "St. Louis Blues": (9, 4, 5, 0, 8, 25, 29, "4-5-0", "L2", "2-2-0", "2-3-0"),
    "New York Rangers": (10, 3, 5, 2, 8, 27, 33, "3-5-2", "L2", "1-3-1", "2-2-1"),
    "Chicago Blackhawks": (10, 3, 5, 2, 8, 26, 32, "3-5-2", "L1", "1-2-1", "2-3-1"),
    "Anaheim Ducks": (9, 3, 5, 1, 7, 23, 31, "3-5-1", "L2", "2-2-0", "1-3-1"),
    "Columbus Blue Jackets": (9, 3, 5, 1, 7, 26, 33, "3-5-1", "L2", "2-3-0", "1-2-1"),
    "Philadelphia Flyers": (9, 2, 5, 2, 6, 23, 34, "2-5-2", "L3", "1-2-1", "1-3-1"),
    "Nashville Predators": (9, 2, 6, 1, 5, 21, 33, "2-6-1", "L3", "1-3-1", "1-3-0"),
    "San Jose Sharks": (10, 1, 7, 2, 4, 20, 40, "1-7-2", "L4", "1-3-1", "0-4-1"),
}

NHL_GAMES = [
    ("nhl-2026020166", "Chicago Blackhawks", "Montreal Canadiens", "2026-10-24T00:00:00Z", "United Center", {"away": -170, "home": 138}),
    ("nhl-2026020167", "Colorado Avalanche", "Tampa Bay Lightning", "2026-10-24T01:00:00Z", "Ball Arena", {"away": 104, "home": -126}),
    ("nhl-2026020168", "Philadelphia Flyers", "Anaheim Ducks", "2026-10-24T17:00:00Z", "Xfinity Mobile Arena", None),
    ("nhl-2026020169", "New Jersey Devils", "Los Angeles Kings", "2026-10-24T17:00:00Z", "Prudential Center", None),
    ("nhl-2026020170", "Boston Bruins", "San Jose Sharks", "2026-10-24T23:00:00Z", "TD Garden", None),
    ("nhl-2026020171", "Ottawa Senators", "New York Rangers", "2026-10-24T23:00:00Z", "Canadian Tire Centre", None),
    ("nhl-2026020172", "Pittsburgh Penguins", "Nashville Predators", "2026-10-24T23:00:00Z", "PPG Paints Arena", None),
    ("nhl-2026020173", "Washington Capitals", "Buffalo Sabres", "2026-10-24T23:00:00Z", "Capital One Arena", None),
    ("nhl-2026020174", "Columbus Blue Jackets", "Vegas Golden Knights", "2026-10-24T23:00:00Z", "Nationwide Arena", None),
    ("nhl-2026020175", "St. Louis Blues", "Carolina Hurricanes", "2026-10-24T23:00:00Z", "Enterprise Center", None),
    ("nhl-2026020176", "Edmonton Oilers", "Toronto Maple Leafs", "2026-10-24T23:00:00Z", "Rogers Place", None),
    ("nhl-2026020177", "Utah Mammoth", "Tampa Bay Lightning", "2026-10-25T01:00:00Z", "Delta Center", None),
    ("nhl-2026020178", "Calgary Flames", "Detroit Red Wings", "2026-10-25T02:00:00Z", "Scotiabank Saddledome", None),
    ("nhl-2026020179", "Seattle Kraken", "Minnesota Wild", "2026-10-25T02:00:00Z", "Climate Pledge Arena", None),
]

for fid, home, away, start_utc, venue, pub_ml in NHL_GAMES:
    hs = NHL_STANDINGS[home]
    as_ = NHL_STANDINGS[away]
    keys = ("gp", "w", "l", "otl", "pts", "gf", "ga", "l10", "streak", "home", "road")
    inp = {"home": dict(zip(keys, hs)), "away": dict(zip(keys, as_))}
    if pub_ml:
        inp["published_ml"] = pub_ml
    facts = [
        (home, f"{hs[1]}-{hs[2]}-{hs[3]} in {hs[0]} games, {hs[5]} GF / {hs[6]} GA, {hs[4]} pts, streak {hs[8]}", "nhle_standings"),
        (away, f"{as_[1]}-{as_[2]}-{as_[3]} in {as_[0]} games, {as_[5]} GF / {as_[6]} GA, {as_[4]} pts, streak {as_[8]}", "nhle_standings"),
        ("Schedule", f"{away} at {home}, {venue}, {start_utc}", "nhle_schedule"),
    ]
    if pub_ml:
        facts.append(("NHL feed price", f"{away} {pub_ml['away']:+d} / {home} {pub_ml['home']:+d} published on NHL schedule feed", "nhle_schedule"))
    fx(sport="Ice Hockey", competition="NHL", id=fid, home=home, away=away,
       start_utc=start_utc, time_display=f"{start_utc} (NHL schedule feed)", venue=venue,
       source="nhle_schedule", stats_source="nhle_standings", inputs=inp, facts=facts)

# --- 2. Basketball: NBA (12 Friday) + EuroLeague Round 8 (6) ---------------
NBA = [
    ("nba-0022600099", "Milwaukee Bucks", "Chicago Bulls", "2026-10-24T00:00:00Z", "8:00 PM ET", "0-1", "0-1"),
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
       facts=[(home, f"{hrec} after opening games", "nba_standings"),
              (away, f"{arec} after opening games", "nba_standings"),
              ("Tip time", disp, "nba_games")] +
             [(t, f"{p} {st} — {r}", "nba_injury") for t, p, st, r in NBA_INJ.get(fid, [])])

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
    ("el-E2026_76", "Panathinaikos AKTOR Athens", "Armani Olimpia Milan", "2026-10-27", "20:15 local (Telekom Center Athens)"),
    ("el-E2026_75", "Valencia Basket", "Fenerbahce Tarfin Istanbul", "2026-10-27", "20:30 local (Roig Arena)"),
    ("el-E2026_73", "Kosner Baskonia Vitoria-Gasteiz", "Real Madrid", "2026-10-27", "21:00 local (Buesa Arena)"),
    ("el-E2026_79", "Besiktas Istanbul", "Olympiacos Piraeus", "2026-10-28", "18:30 local (Turkcell Basketball Development Center)"),
    ("el-E2026_77", "Hapoel IBI Tel Aviv", "Anadolu Efes Istanbul", "2026-10-28", "19:00 local (Arena Botevgrad)"),
    ("el-E2026_80", "Virtus Bologna", "Zalgiris Kaunas", "2026-10-28", "20:30 local (PalaDozza)"),
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

# --- 3. Baseball: World Series Games 1-2 ----------------------------------
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
          ("Logan Henderson", "Named Game 2 starter on MLB schedule feed; 2026 regular-season MLB pitching split is empty and left blank", "mlb_pitchers"),
          ("Fixture", "World Series Game 2 at American Family Field, first pitch 2026-10-25T00:00Z", "mlb_schedule")])

# --- 4. Cricket (6 fixtures) ----------------------------------------------
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

# --- 5. Snooker (Northern Ireland Open SFs + International Championship) ---
fx(sport="Snooker", competition="BetVictor Northern Ireland Open 2026", id="snk-ni-sf1",
   home="Kyren Wilson", away="Sam Craigie",
   time_display="24 October 2026, 08:00 (WST site clock)", venue="Waterfront Hall, Belfast",
   source="wst_matches", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": 716800, "away_rank_money": 132000,
           "home_note": "world no.9, £716,800", "away_note": "Northern Ireland Open semi-finalist, beat Elliot Slessor 6-2"},
   facts=[("Kyren Wilson", "world no.9 with £716,800 on the Johnstone's Paint World Rankings; beat Anthony McGill 6-1 in the quarter-final", "wst_rankings"),
          ("Sam Craigie", "beat Elliot Slessor 6-2 in the quarter-final and Matthew Selt 4-2 in Round 3", "wst_matches"),
          ("Fixture", "Northern Ireland Open Semi-Final 1 (Match 61), 24 October 2026, 08:00 WST clock", "wst_matches")])

fx(sport="Snooker", competition="BetVictor Northern Ireland Open 2026", id="snk-ni-sf2",
   home="Mark Williams", away="Winner of Match 60 (Jak Jones / Scott Donaldson)",
   time_display="24 October 2026, 14:00 (WST site clock)", venue="Waterfront Hall, Belfast",
   source="wst_matches", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": 747400, "away_rank_money": None},
   line_blocked="Mark Williams beat David Gilbert 6-4 in QF Match 59, but QF Match 60 (Jak Jones 4-4 Scott Donaldson) was still live in Frame 9 at capture time; no line is originated until the opponent is confirmed.",
   facts=[("Mark Williams", "world no.8 with £747,400; defeated David Gilbert 6-4 in Quarter-Final Match 59 on 23 October 2026", "wst_matches"),
          ("Quarter-Final Match 60", "Jak Jones tied 4-4 with Scott Donaldson (29-0 in Frame 9 of 11) at 21:40 UTC", "wst_matches"),
          ("Fixture", "Northern Ireland Open Semi-Final 2 (Match 62), 24 October 2026, 14:00 WST clock", "wst_matches")])

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
   line_blocked="Both players are outside the published top-36 ranking-money list captured here; no numeric strength input, so no line is originated.",
   facts=[("Fixture", "International Championship Round 2, Nanjing, Liu Hongyu v Louis Heathcote", "wst_ic")])

fx(sport="Snooker", competition="International Championship 2026", id="snk-ic-white",
   home="Jimmy White", away="Mark Selby",
   time_display="30 October 2026, 21:30 (WST match centre)", venue="Nanjing, China",
   source="wst_ic", stats_source="wst_rankings",
   inputs={"format": "best of 11 frames", "home_rank_money": None, "away_rank_money": 1070500,
           "away_note": "world no.5, £1,070,500; one-year list leader £348,350"},
   line_blocked="Jimmy White's ranking-money figure is not on the top-36 WST rankings page captured here; no line is originated.",
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

# --- 6. Darts: European Championship Round Two ----------------------------
DARTS = [
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
    fx(sport="Darts", competition="Machineseeker European Championship",
       id=fid, home=h, away=a,
       time_display=f"24 October 2026, Round Two {session} (13:00-17:00 / 19:00-23:00 CEST)",
       venue="Westfalenhalle, Dortmund", source="pdc_schedule", stats_source="pdc_rules",
       inputs={"format": "best of 11 legs", "home_et_money": hm or None, "away_et_money": am or None,
               "home_seed": hs, "away_seed": asd, "session": session},
       facts=DARTS_FACTS[fid])

# --- 7. Tennis: ATP Tour Saturday 24 October (SFs + ATP 500 Q1s) ----------
TN = [
    ("ten-brussels-sf2", "Arthur Fils", "Jan-Lennard Struff", "ATP 250 Brussels", "2026-10-24",
     "Not before 18:30 local (Centre Court)", "atp_brussels", 3325, 929, None,
     [("Arthur Fils", "world no.10 with 3,325 ATP points, top seed in Brussels; defeated fifth seed Alex Michelsen 6-4 7-6(12) in the quarter-final", "atp_rankings"),
      ("Jan-Lennard Struff", "world no.58 with 929 ATP points; defeated Zizou Bergs in the Brussels quarter-final", "atp_rankings"),
      ("Fixture", "Brussels Semifinal 2, Centre Court, Saturday 24 October 2026 Not Before 18:30 local", "atp_brussels")]),
    ("ten-brussels-sf1", "Francisco Cerundolo", "Tallon Griekspoor", "ATP 250 Brussels", "2026-10-24",
     "Not before 16:00 local (Centre Court)", "atp_brussels", 2220, 885, None,
     [("Francisco Cerundolo", "world no.21 with 2,220 ATP points, seeded third in Brussels", "atp_rankings"),
      ("Tallon Griekspoor", "world no.60 with 885 ATP points; reached the Brussels semi-finals", "atp_rankings"),
      ("Fixture", "Brussels Semifinal 1, Centre Court, Saturday 24 October 2026 Not Before 16:00 local", "atp_brussels")]),
    ("ten-almaty-sf1", "Daniil Medvedev", "Alexander Bublik", "ATP 250 Almaty", "2026-10-24",
     "Not before 18:00 local (Center Court)", "atp_almaty", 3660, 2275, None,
     [("Daniil Medvedev", "world no.5 with 3,660 ATP points; beat Terence Atmane 6-4 6-4 in the quarter-final", "atp_rankings"),
      ("Alexander Bublik", "world no.19 with 2,275 ATP points; beat Karen Khachanov 4-6 7-6(5) 7-6(5)", "atp_rankings"),
      ("Fixture", "Almaty Semifinal 2, Center Court, Saturday 24 October 2026 Not Before 18:00 local", "atp_almaty")]),
    ("ten-lyon-sf2", "Tommy Paul", "Taylor Fritz", "ATP 250 Lyon", "2026-10-24",
     "Saturday Semifinal (Court Central Auvergne-Rhone-Alpes)", "atp_lyon", 2575, 2880, None,
     [("Taylor Fritz", "world no.14 with 2,880 ATP points, second seed; beat Daniel Altmaier 7-6(5) 6-2 in the Lyon quarter-final", "atp_rankings"),
      ("Tommy Paul", "world no.15 with 2,575 ATP points, fourth seed; beat Corentin Moutet 6-4 3-6 6-3 in the Lyon quarter-final", "atp_rankings"),
      ("Fixture", "Grand Prix Auvergne-Rhone-Alpes (Lyon) Semifinal, Tommy Paul (4) v Taylor Fritz (2)", "atp_lyon")]),
    ("ten-vienna-q1f", "Adolfo Daniel Vallejo", "Lorenzo Sonego", "ATP 500 Vienna Qualifying", "2026-10-24",
     "Followed by on Glaubandich Court", "atp_vienna", 997, 658, None,
     [("Adolfo Daniel Vallejo", "world no.54 with 997 ATP points, seeded second in Vienna qualifying", "atp_rankings"),
      ("Lorenzo Sonego", "world no.89 with 658 ATP points", "atp_rankings"),
      ("Fixture", "Erste Bank Open Vienna Qualifying Round 1, Glaubandich Court, 24 October 2026", "atp_vienna")]),
    ("ten-vienna-q1d", "Thiago Agustin Tirante", "Adrian Mannarino", "ATP 500 Vienna Qualifying", "2026-10-24",
     "Not before 18:00 local (Centre Court)", "atp_vienna", 1032, 743, None,
     [("Thiago Agustin Tirante", "world no.50 with 1,032 ATP points, top seed in Vienna qualifying", "atp_rankings"),
      ("Adrian Mannarino", "world no.79 with 743 ATP points", "atp_rankings"),
      ("Fixture", "Erste Bank Open Vienna Qualifying Round 1, Centre Court, 24 October 2026 Not Before 18:00 local", "atp_vienna")]),
    ("ten-basel-q1a", "Marcos Giron", "Yannick Hanfmann", "ATP 500 Basel Qualifying", "2026-10-24",
     "Starts at 11:00 local (Center Court)", "atp_basel", 676, 923, None,
     [("Yannick Hanfmann", "world no.59 with 923 ATP points, sixth seed in Basel qualifying", "atp_rankings"),
      ("Marcos Giron", "world no.88 with 676 ATP points", "atp_rankings"),
      ("Fixture", "Swiss Indoors Basel Qualifying Round 1, Center Court, 24 October 2026 at 11:00 local", "atp_basel")]),
    ("ten-basel-q1e", "Miomir Kecmanovic", "Rinky Hijikata", "ATP 500 Basel Qualifying", "2026-10-24",
     "Starts at 11:00 local (IWB Court 1)", "atp_basel", 930, 689, None,
     [("Miomir Kecmanovic", "world no.57 with 930 ATP points, fourth seed in Basel qualifying", "atp_rankings"),
      ("Rinky Hijikata", "world no.86 with 689 ATP points", "atp_rankings"),
      ("Fixture", "Swiss Indoors Basel Qualifying Round 1, IWB Court 1, 24 October 2026 at 11:00 local", "atp_basel")]),
    ("ten-basel-q1f", "Juan Manuel Cerundolo", "Zachary Svajda", "ATP 500 Basel Qualifying", "2026-10-24",
     "Followed by on IWB Court 1", "atp_basel", 1000, 759, None,
     [("Juan Manuel Cerundolo", "world no.53 with 1,000 ATP points, second seed in Basel qualifying", "atp_rankings"),
      ("Zachary Svajda", "world no.77 with 759 ATP points", "atp_rankings"),
      ("Fixture", "Swiss Indoors Basel Qualifying Round 1, IWB Court 1, 24 October 2026", "atp_basel")]),
    ("ten-almaty-sf2", "Nikoloz Basilashvili", "Stefanos Tsitsipas", "ATP 250 Almaty", "2026-10-24",
     "Not before 15:00 local (Center Court)", "atp_almaty", None, 1330, None,
     [("Stefanos Tsitsipas", "world no.39 with 1,330 ATP points, seeded seventh in Almaty", "atp_rankings"),
      ("Nikoloz Basilashvili", "qualified for the Almaty main draw; outside the published Top 100 rankings table captured here", "atp_almaty")]),
    ("ten-lyon-sf1", "Flavio Cobolli", "Winner of Van Assche / Musetti", "ATP 250 Lyon", "2026-10-24",
     "Saturday Semifinal (Court Central Auvergne-Rhone-Alpes)", "atp_lyon", 3640, None,
     "Flavio Cobolli beat Brandon Nakashima 4-6 6-4 6-4 in the quarter-final, but Luca Van Assche v Lorenzo Musetti was still live in Set 3 (0-6, 7-6(5), 3-2) at capture time; no line is originated.",
     [("Flavio Cobolli", "world no.6 with 3,640 ATP points, top seed in Lyon; defeated Brandon Nakashima 4-6 6-4 6-4 in QF", "atp_lyon"),
      ("Quarter-final in play", "Luca Van Assche (#48, 1,065 pts) led Lorenzo Musetti (#26, 1,870 pts) 0-6 7-6(5) 3-2 in Set 3 at 21:40 UTC", "atp_lyon")]),
]
for fid, h, a, comp, day, disp, src, hp, ap, blocked, facts in TN:
    fx(sport="Tennis", competition=comp, id=fid, home=h, away=a,
       time_display=f"{day} {disp}", source=src, stats_source="atp_rankings",
       line_blocked=blocked,
       inputs={"format": "best of three sets", "home_points": hp, "away_points": ap},
       facts=facts)

# --- 8. Golf (PGA TOUR Bermuda + DP World Tour Genesis) -------------------
fx(sport="Golf", competition="PGA TOUR", id="golf-bermuda",
   home="Butterfield Bermuda Championship", away=None,
   time_display="22-25 October 2026, Round 3 tee times Saturday 24 October", venue="Port Royal Golf Course, Southampton, Bermuda",
   source="pgatour", stats_source="pgatour",
   inputs={"market": "outright", "after_round": 2, "cut_line": -5, "field": [
       ("Kensei Hirata", "JPN", -13, 65, 64, 129, "F"),
       ("Chandler Blanchet", "USA", -13, 62, 67, 129, "F"),
       ("Seamus Power", "IRL", -12, 66, 64, 130, "F*"),
       ("Corey Conners", "CAN", -12, 63, 67, 130, "F*"),
       ("Eric Cole", "USA", -12, 65, 65, 130, "F"),
       ("Ben Silverman", "CAN", -12, 63, 67, 130, "F"),
       ("Danny Walker", "USA", -12, 63, 67, 130, "F"),
       ("David Skinns", "ENG", -11, 68, 63, 131, "F"),
       ("Denny McCarthy", "USA", -11, 67, 64, 131, "F")]},
   facts=[("Leaderboard", "After 36 holes: Hirata (65-64) and Blanchet (62-67) T1 at -13 (129); Power, Conners, Cole, Silverman, and Walker T3 at -12 (130)", "pgatour"),
          ("Cut line", "-5 projected 36-hole cut at Port Royal Golf Course", "pgatour"),
          ("Schedule", "Butterfield Bermuda Championship, Port Royal Golf Course, 22-25 October 2026", "pgatour")])

fx(sport="Golf", competition="DP World Tour", id="golf-genesis",
   home="Genesis Championship", away=None,
   time_display="Round 3 from 24 October 2026, tee times from 09:06 local", venue="Korea",
   source="dpwt", stats_source="dpwt",
   inputs={"market": "outright", "after_round": 2, "field": [
       ("Antoine Rozner", "FRA", -10, 67, 65, 132), ("Casey Jarvis", "RSA", -10, 65, 67, 132),
       ("Martin Couvra", "FRA", -7, 69, 66, 135), ("Filippo Celli", "ITA", -7, 69, 66, 135),
       ("Ryan Fox", "NZL", -7, 68, 67, 135), ("Sanghun Shin", "KOR", -7, 66, 69, 135),
       ("Si Woo Kim", "KOR", -6, 67, 69, 136), ("Daihan Lee", "KOR", -6, 69, 67, 136)]},
   facts=[("Leaderboard", "After two rounds: Rozner and Jarvis -10 (132), Couvra, Celli, Fox and Shin -7 (135)", "dpwt"),
          ("Schedule", "Genesis Championship, DP World Tour, round three from 24 October 2026", "dpwt")])

# --- 9. Greyhounds (GBGB Category One Finals) -----------------------------
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

# --- 10. Handball (Daikin StarLigue R8 + EHF Champions League R6) ---------
LNH = {
    "Paris": (7, 7, 0, 0, 239, 190),
    "Nantes": (7, 6, 1, 0, 244, 203),
    "Nîmes": (8, 6, 2, 0, 261, 260),
    "Montpellier": (7, 4, 1, 2, 234, 205),
    "Limoges": (8, 5, 3, 0, 266, 238),
    "Tremblay": (8, 4, 3, 1, 265, 256),
    "Aix": (8, 4, 4, 0, 259, 249),
    "Caen": (8, 4, 4, 0, 224, 259),
    "Chartres": (8, 3, 4, 1, 236, 257),
    "Sélestat": (8, 3, 5, 0, 232, 243),
    "Saran": (7, 3, 4, 0, 202, 216),
    "Chambéry": (7, 2, 3, 2, 224, 231),
    "Toulouse": (8, 3, 5, 0, 224, 233),
    "Saint-Raphaël": (7, 2, 5, 0, 207, 225),
    "Cesson-Rennes": (8, 1, 7, 0, 238, 261),
    "Dunkerque": (8, 1, 7, 0, 199, 228),
}
HB = [
    ("hb-nantes-chambery", "Nantes", "Chambéry", "2026-10-24T19:00:00+02:00", "Sat 24 October, 19:00 local"),
    ("hb-sr-paris", "Saint-Raphaël", "Paris", "2026-10-25T16:00:00+01:00", "Sun 25 October, 16:00 local"),
    ("hb-montpellier-saran", "Montpellier", "Saran", "2026-10-25T17:00:00+01:00", "Sun 25 October, 17:00 local"),
    ("hb-paris-aalborg", "Paris", "Aalborg", "2026-10-28T20:45:00+01:00", "Wed 28 October, 20:45 local (EHF CL R6)"),
    ("hb-montpellier-bucarest", "Montpellier", "Bucarest", "2026-10-29T20:45:00+01:00", "Thu 29 October, 20:45 local (EHF CL R6)"),
    ("hb-plock-nantes", "Plock", "Nantes", "2026-10-28T18:45:00+01:00", "Wed 28 October, 18:45 local (EHF CL R6)"),
]
for fid, home, away, start, disp in HB:
    if home in LNH and away in LNH:
        inputs = {"home": dict(zip(("gp", "w", "l", "d", "gf", "ga"), LNH[home])),
                  "away": dict(zip(("gp", "w", "l", "d", "gf", "ga"), LNH[away])),
                  "competition": "Daikin StarLigue"}
        facts = [(home, f"{LNH[home][1]}-{LNH[home][2]}-{LNH[home][3]} in {LNH[home][0]} games, {LNH[home][4]} goals for, {LNH[home][5]} against", "lnh_table"),
                 (away, f"{LNH[away][1]}-{LNH[away][2]}-{LNH[away][3]} in {LNH[away][0]} games, {LNH[away][4]} goals for, {LNH[away][5]} against", "lnh_table"),
                 ("Journée 08", f"{home} v {away}, {disp} (following Friday's five completed J08 games)", "lnh_cal")]
    else:
        inputs = {"competition": "EHF Champions League"}
        facts = [("Fixture", f"EHF Champions League Round 6, {home} v {away}, 2026", "lnh_ehf")]
    fx(sport="Handball", competition=inputs["competition"], id=fid, home=home, away=away,
       start_utc=start, time_display=disp, venue=None, source="lnh_cal", stats_source="lnh_table",
       inputs=inputs, facts=facts)

# --- 11. Motor Racing (Formula 1 USGP + Drivers' Championship) ------------
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

# --- 12. Rugby League (RLWC 2026 Round 2 + Round 3) -----------------------
RL = [
    ("rlwc-png-samoa", "Papua New Guinea", "Samoa", "2026-10-24T04:25:00Z", "24 October, 12:25am ET (NRL display)",
     "3rd", "2nd", "Santos National Football Stadium, Port Moresby"),
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
     "1st", "2nd", "CommBank Stadium, Sydney"),
]
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
    "rlwc-r3-leb-fra": [("Round 1", "Lebanon lost 18-42 to Papua New Guinea (and 0-36 to Tonga in R2); France lost 4-78 to Samoa", "nrl_r1")],
    "rlwc-r3-ton-sam": [("Round 1", "Tonga beat England 30-12 (and Lebanon 36-0 in R2); Samoa beat France 78-4", "nrl_r1")],
}
for fid, home, away, start, disp, hpos, apos, venue in RL:
    fx(sport="Rugby League", competition="Rugby League World Cup 2026", id=fid, home=home, away=away,
       start_utc=start, time_display=disp, venue=venue, source="nrl_r2", stats_source="nrl_r1",
       inputs={"home_ladder": hpos, "away_ladder": apos,
               "home_margin": RL_MARGINS[fid][0], "away_margin": RL_MARGINS[fid][1]},
       facts=RL_FACTS[fid])

# --- 13. Rugby Union (Gallagher PREM R4 + URC R4 with full URC table) -----
PREM = {
    "Gloucester Rugby": (3, 2, 0, 1, 62, 12),
    "Northampton Saints": (3, 2, 0, 1, 41, 11),
    "Saracens": (3, 2, 0, 1, 21, 11),
    "Leicester Tigers": (3, 2, 0, 1, 10, 11),
    "Bath Rugby": (3, 2, 0, 1, -1, 11),
    "Bristol Bears": (3, 2, 0, 1, 2, 10),
    "Sale Sharks": (3, 2, 0, 1, -2, 9),
    "Exeter Chiefs": (3, 1, 0, 2, -21, 8),
    "Newcastle Red Bulls": (3, 0, 0, 3, -44, 4),
    "Harlequins": (3, 0, 0, 3, -68, 2),
}
URC_TABLE = {
    "Glasgow Warriors": (3, 2, 1, 0, 23, 13, 95, 72),
    "Vodacom Bulls": (3, 2, 0, 1, 72, 11, 126, 54),
    "DHL Stormers": (3, 2, 0, 1, 27, 11, 81, 54),
    "Dragons RFC": (3, 1, 1, 1, 5, 9, 88, 83),
    "Munster": (3, 1, 1, 1, -2, 9, 72, 74),
    "Leinster": (3, 1, 0, 2, 17, 8, 75, 58),
    "Ulster": (3, 0, 2, 1, -5, 8, 88, 93),
    "Scarlets": (3, 1, 0, 2, -17, 7, 68, 85),
    "Ospreys": (3, 1, 0, 2, -26, 6, 81, 107),
    "Benetton Rugby": (3, 0, 1, 2, -4, 5, 64, 68),
}
RU = [
    ("ru-leicester-northampton", "Leicester Tigers", "Northampton Saints", "Sat 24 Oct, 10:05 viewer-local", "Mattioli Woods Welford Road"),
    ("ru-bristol-exeter", "Bristol Bears", "Exeter Chiefs", "Sat 24 Oct, 12:30 viewer-local", "Ashton Gate"),
    ("ru-quins-saracens", "Harlequins", "Saracens", "Sun 25 Oct, 11:00 viewer-local", "Twickenham Stoop"),
    ("ru-bulls-ulster", "Vodacom Bulls", "Ulster", "Sat 24 Oct, 07:45 (URC local)", "Loftus Versfeld"),
    ("ru-stormers-scarlets", "DHL Stormers", "Scarlets", "Sat 24 Oct, 10:00 (URC local)", "DHL Stadium"),
    ("ru-benetton-glasgow", "Benetton Rugby", "Glasgow Warriors", "Sat 24 Oct, 10:00 (URC local)", "Stadio Monigo"),
    ("ru-leinster-munster", "Leinster", "Munster", "Sat 24 Oct, 13:00 (URC local)", "Aviva Stadium"),
    ("ru-ospreys-dragons", "Ospreys", "Dragons RFC", "Sat 24 Oct, 14:00 (URC local)", "St Helen's"),
]
for fid, home, away, disp, venue in RU:
    if home in PREM and away in PREM:
        h = PREM[home]
        a = PREM[away]
        inputs = {"competition": "Gallagher PREM",
                  "home": {"p": h[0], "w": h[1], "d": h[2], "l": h[3], "pd": h[4], "pts": h[5]},
                  "away": {"p": a[0], "w": a[1], "d": a[2], "l": a[3], "pd": a[4], "pts": a[5]}}
        facts = [(home, f"{h[1]}-{h[2]}-{h[3]} after three rounds, points difference {h[4]:+d}, {h[5]} league points", "prem_table"),
                 (away, f"{a[1]}-{a[2]}-{a[3]} after three rounds, points difference {a[4]:+d}, {a[5]} league points", "prem_table"),
                 ("Round 4", f"{home} v {away}, Gallagher PREM Round 4, {disp}", "prem_fixtures")]
        src, st = "prem_fixtures", "prem_table"
    else:
        h = URC_TABLE[home]
        a = URC_TABLE[away]
        inputs = {"competition": "United Rugby Championship",
                  "home": {"p": h[0], "w": h[1], "d": h[2], "l": h[3], "pd": h[4], "pts": h[5], "pf": h[6], "pa": h[7]},
                  "away": {"p": a[0], "w": a[1], "d": a[2], "l": a[3], "pd": a[4], "pts": a[5], "pf": a[6], "pa": a[7]}}
        facts = [(home, f"{h[1]}-{h[2]}-{h[3]} after three rounds ({h[6]} PF / {h[7]} PA), points difference {h[4]:+d}, {h[5]} league points", "urc_table"),
                 (away, f"{a[1]}-{a[2]}-{a[3]} after three rounds ({a[6]} PF / {a[7]} PA), points difference {a[4]:+d}, {a[5]} league points", "urc_table"),
                 ("Round 4", f"{home} v {away}, URC Round 4, {disp} at {venue}", "urc_round4")]
        src, st = "urc_round4", "urc_table"
    fx(sport="Rugby Union", competition=inputs["competition"], id=fid, home=home, away=away,
       time_display=disp, venue=venue, source=src, stats_source=st, inputs=inputs, facts=facts)

# --- 14. Volleyball (SuperLega R2 + 1. Bundesliga Männer R2) --------------
SL = {
    "Cisterna Volley": (3, 1, 1, 0, 3, 0, 79, 56),
    "Gas Sales Bluenergy Piacenza": (3, 1, 1, 0, 3, 0, 75, 56),
    "Itas Trentino": (3, 1, 1, 0, 3, 0, 75, 61),
    "Cucine Lube Civitanova": (3, 1, 1, 0, 3, 0, 78, 65),
    "Tinet Prata di Pordenone": (3, 1, 1, 0, 3, 1, 94, 91),
    "Sir Susa Scai Perugia": (2, 1, 1, 0, 3, 2, 114, 95),
    "Acqua Sant'Anna Cuneo": (1, 1, 0, 1, 2, 3, 95, 114),
    "Vero Volley Monza": (0, 1, 0, 1, 1, 3, 91, 94),
    "Rana Verona": (0, 1, 0, 1, 0, 3, 65, 78),
    "Valsa Group Modena": (0, 1, 0, 1, 0, 3, 61, 75),
    "Pallavolo Padova": (0, 1, 0, 1, 0, 3, 56, 75),
    "Allianz Milano": (0, 1, 0, 1, 0, 3, 56, 79),
}
VB = [
    ("vb-perugia-prata", "Sir Susa Scai Perugia", "Tinet Prata di Pordenone", "Sun 25 Oct, 18:00 local"),
    ("vb-trentino-cisterna", "Itas Trentino", "Cisterna Volley", "Sun 25 Oct, 17:00 local"),
    ("vb-piacenza-modena", "Gas Sales Bluenergy Piacenza", "Valsa Group Modena", "Sun 25 Oct, 18:00 local"),
    ("vb-civitanova-padova", "Cucine Lube Civitanova", "Pallavolo Padova", "Sun 25 Oct, 18:00 local"),
    ("vb-milano-cuneo", "Allianz Milano", "Acqua Sant'Anna Cuneo", "Sun 25 Oct, 19:00 local"),
    ("vb-monza-verona", "Vero Volley Monza", "Rana Verona", "Sun 25 Oct, 18:00 local"),
    ("vb-friedrichshafen-karlsruhe", "VfB Friedrichshafen", "BADEN VOLLEYS Karlsruhe", "Sat 24 Oct, 6:30 PM (VBL schedule)"),
    ("vb-lueneburg-warnemuende", "SVG Lüneburg", "SV Warnemünde", "Sat 24 Oct, 7:00 PM (VBL schedule)"),
    ("vb-giesen-berlin", "Helios GRIZZLYS Giesen", "BERLIN RECYCLING Volleys", "Sat 24 Oct, 7:30 PM (VBL schedule)"),
    ("vb-dueren-muenchen", "SWD powervolleys Düren", "WWK Volleys München", "Sat 24 Oct, 7:30 PM (VBL schedule)"),
]
for fid, home, away, disp in VB:
    if home in SL and away in SL:
        h, a = SL[home], SL[away]
        inputs = {"competition": "SuperLega",
                  "home": {"pts": h[0], "played": h[1], "sets_w": h[4], "sets_l": h[5], "pf": h[6], "pa": h[7]},
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

# --- 15. Gaelic Sports (5 weekend championship fixtures) ------------------
GAA = [
    ("gaa-shinty-hurling", "Ireland", "Scotland", "Hurling-Shinty International", "24 October 2026, 18:00",
     "SuperValu Páirc Uí Chaoimh, Cork", "gaa_fixtures", None,
     [("Fixture", "Hurling-Shinty International, Ireland v Scotland, SuperValu Páirc Uí Chaoimh, 24 October 2026, 18:00, referee Eamonn Furlong", "gaa_fixtures")]),
    ("gaa-cork-psfc", "St Finbarr's", "Nemo Rangers", "Cork Premier Senior Football Championship Final", "25 October 2026, 16:00",
     "SuperValu Páirc Uí Chaoimh", "gaacork", 14,
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
# OLBG taxonomy + live defects
# ---------------------------------------------------------------------------
OLBG_TAXONOMY = {
    "captured_utc": CAPTURED_UTC,
    "session": SESSION,
    "source_url": "https://www.olbg.com/betting-tips",
    "sports": [
        {"sport": "Golf", "olbg_ids": ["5"], "hub_url": "https://www.olbg.com/betting-tips/Golf/5", "markets": "Win Tournament"},
        {"sport": "Volleyball", "olbg_ids": ["21"], "hub_url": "https://www.olbg.com/betting-tips/Volleyball/21", "markets": "Win Match, Set Score"},
        {"sport": "Rugby Union", "olbg_ids": ["9"], "hub_url": "https://www.olbg.com/betting-tips/Rugby_Union/9", "markets": "To Win"},
        {"sport": "Cricket", "olbg_ids": ["7"], "hub_url": "https://www.olbg.com/betting-tips/Cricket/7", "markets": "Win Match"},
        {"sport": "Snooker", "olbg_ids": ["8"], "hub_url": "https://www.olbg.com/betting-tips/Snooker/8", "markets": "Win Match"},
        {"sport": "Darts", "olbg_ids": ["15"], "hub_url": "https://www.olbg.com/betting-tips/Darts/15", "markets": "Win Match 2-way, Handicap 2-way, Total Legs"},
        {"sport": "Baseball", "olbg_ids": ["12"], "hub_url": "https://www.olbg.com/betting-tips/Baseball/12", "markets": "Money Line, Run Line, Game Totals"},
        {"sport": "Gaelic Sports", "olbg_ids": ["25", "26"], "hub_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "markets": "Handicap, Win Match"},
        {"sport": "Greyhounds", "olbg_ids": ["28"], "hub_url": "https://www.olbg.com/betting-tips/Greyhounds/28", "markets": "Daily Races"},
        {"sport": "Tennis", "olbg_ids": ["3"], "hub_url": "https://www.olbg.com/betting-tips/Tennis/3", "markets": "Win Match, Set Betting, Total Games, Games Won"},
        {"sport": "Motor Racing", "olbg_ids": ["14"], "hub_url": "https://www.olbg.com/betting-tips/Motor_Racing/14", "markets": "Win Race, Win Tournament"},
        {"sport": "Handball", "olbg_ids": ["20"], "hub_url": "https://www.olbg.com/betting-tips/Handball/20", "markets": "Money Line (three-way, includes Tie)"},
        {"sport": "Ice Hockey", "olbg_ids": ["13"], "hub_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13", "markets": "Money Line, Puck Line, Game Totals"},
        {"sport": "Basketball", "olbg_ids": ["4"], "hub_url": "https://www.olbg.com/betting-tips/Basketball/4", "markets": "Money Line, Pointspread, Game Totals"},
        {"sport": "Rugby League", "olbg_ids": ["10"], "hub_url": "https://www.olbg.com/betting-tips/Rugby_League/10", "markets": "To Win, Grand Final Winner"},
    ],
    "defects": [
        {"id": "OLBG-D1", "title": "US egress IPs receive empty sport hubs",
         "evidence": "All 16 /betting-tips/{Sport}/{id} routes render 'No tips found.' from a US IP while direct ?event_id= routes resolve.",
         "source_url": "https://www.olbg.com/betting-tips"},
        {"id": "OLBG-D2", "title": "Header tip denominators are string-concatenated",
         "evidence": "event_id=199984 renders '4 / 042 | 95%' where the market table shows 4 of 42; 160789 renders '6 / 062'; 536036 renders '9 / 090'; 902163 renders '2 / 021'.",
         "source_url": "https://www.olbg.com/betting-tips/Rugby_League/International/Rugby_League_World_Cup/Australia_v_Fiji/10?event_id=199984"},
        {"id": "OLBG-D3", "title": "Bookmaker odds cells are geo-stripped for logged-out US visitors",
         "evidence": "event_id=32384 and 902163 render 'WIN @' with no price string following.",
         "source_url": "https://www.olbg.com/betting-tips/Basketball/USA/NBA/Chicago_Bulls_at_Milwaukee_Bucks/4?event_id=902163"},
        {"id": "OLBG-D4", "title": "False Expired badges and unlabelled US-Eastern timestamps",
         "evidence": "Unstarted 24 October fixtures display 'Expired' badges alongside viewer-local EDT times.",
         "source_url": "https://www.olbg.com/betting-tips"},
    ],
}

# ---------------------------------------------------------------------------
# Line-by-line repository audit findings
# ---------------------------------------------------------------------------
REPO_AUDIT = {
    "generated_utc": CAPTURED_UTC,
    "session": SESSION,
    "summary": {
        "irregularities_logged": 19,
        "out_of_scope_html_files": 4,
        "predictions_with_forbidden_words": 5,
        "html_files_with_unlinked_rows": 26,
    },
    "findings": [
        {
            "id": "HZ-AUD-01", "severity": "high", "category": "Out-of-scope sports in legacy layers",
            "file_path": "data/fixtures.json", "lines": "753-899",
            "issue": "Legacy data/fixtures.json and verify/sports/{american-football,australian-rules,boxing,esports}.html retain 4 sports outside the 15-sport mandate.",
            "official_check": "Cross-checked against the 15-sport mandate on OLBG.com.",
            "official_source_url": "https://www.olbg.com/betting-tips",
        },
        {
            "id": "HZ-AUD-02", "severity": "high", "category": "Out-of-scope sport pages in /verify/",
            "file_path": "verify/sports/american-football.html", "lines": "1-48",
            "issue": "Four HTML sport pages under verify/sports/ render American Football, Australian Rules, Boxing, and Esports.",
            "official_check": "Confirmed file presence on disk in verify/sports/.",
            "official_source_url": "https://www.olbg.com/betting-tips",
        },
        {
            "id": "HZ-AUD-03", "severity": "high", "category": "Prohibited words in legacy prediction JSON",
            "file_path": "data/audit91/predictions.json", "lines": "1-120",
            "issue": "Five legacy prediction JSON files (data/audit91/predictions.json, data/canonical/predictions.json, data/clean_room/predictions_audit.json, data/final_audit/predictions_audit.json, data/next_step/predictions_audit.json) contain the words 'model' or 'verified'.",
            "official_check": "Scanned all data/**/predictions*.json files with regex \\b(model|verified)\\b.",
            "official_source_url": "https://www.olbg.com/betting-tips",
        },
        {
            "id": "HZ-AUD-04", "severity": "high", "category": "Unlinked table rows in earlier static layers",
            "file_path": "audit/flagged.html", "lines": "26-100",
            "issue": "26 legacy HTML pages across audit/, verify/,board/, and pulse/ contain data-table rows without an anchor tag to an official source.",
            "official_check": "Parsed every <tbody><tr> across all repository HTML files.",
            "official_source_url": "https://www.olbg.com/betting-tips",
        },
        {
            "id": "HZ-AUD-05", "severity": "high", "category": "Fabricated Oct 19-20 fixtures in legacy data/fixtures.json",
            "file_path": "data/fixtures.json", "lines": "16-1405",
            "issue": "Legacy data/fixtures.json contains 75 fabricated Oct 19-20 fixtures (e.g., Ryder Cup, Presidents Cup, ATP Stockholm/Antwerp, fake PBA bowling/volleyball) with synthetic source_verified=True flags.",
            "official_check": "Verified against live PGA TOUR, ATP Tour, MLB, and NHL schedules for 2026-10-23.",
            "official_source_url": "https://www.pgatour.com/leaderboard",
        },
        {
            "id": "HZ-AUD-06", "severity": "high", "category": "Stale Northern Ireland Open QF3 status in earlier 2026-10-23 desks",
            "file_path": "data/signal/matches.json", "lines": "1-160",
            "issue": "Earlier 2026-10-23 desks captured David Gilbert v Mark Williams while Gilbert led 4-2 in-play; WST now confirms Mark Williams won 6-4 to advance to Semi-Final 2.",
            "official_check": "Fetched https://www.wst.tv/matches/ at 21:40 UTC confirming Match 59 Completed: David Gilbert 4-6 Mark Williams.",
            "official_source_url": "https://www.wst.tv/matches/",
        },
        {
            "id": "HZ-AUD-07", "severity": "medium", "category": "Missing Saturday ATP 250 Brussels & Lyon Semifinals in earlier desks",
            "file_path": "data/cadence/fixtures.json", "lines": "1-420",
            "issue": "Earlier 2026-10-23 desks captured only Almaty SFs and Vienna Q1s because Brussels and Lyon QFs were still in play; ATP Tour has now published Brussels SFs (Fils v Struff, Cerundolo v Griekspoor) and Lyon SF2 (Paul v Fritz).",
            "official_check": "Fetched https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule and lyon/496/daily-schedule at 21:35 UTC.",
            "official_source_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule",
        },
        {
            "id": "HZ-AUD-08", "severity": "medium", "category": "URC Round 4 Saturday fixtures lacked league-table inputs in earlier desks",
            "file_path": "scripts/cadence_model.py", "lines": "443-447",
            "issue": "Earlier 2026-10-23 desks treated all 5 Saturday URC Round 4 fixtures as having no numeric strength input; the official URC table publishes 3-round W-D-L, PF, PA, DIFF, and PTS for all 10 Saturday clubs.",
            "official_check": "Fetched https://stats.unitedrugby.com/match-centre/table/2026-27 at 21:35 UTC.",
            "official_source_url": "https://stats.unitedrugby.com/match-centre/table/2026-27",
        },
        {
            "id": "HZ-AUD-09", "severity": "medium", "category": "Completed Friday URC Round 4 and LNH StarLigue J08 fixtures",
            "file_path": "data/signal/matches.json", "lines": "1-220",
            "issue": "Three Friday URC Round 4 matches (Cardiff 21-36 Sharks, Connacht 48-27 Zebre, Edinburgh 31-10 Lions) and five Friday LNH J08 matches (Aix 32-26 Toulouse, Chartres 32-33 Nîmes, Limoges 32-24 Dunkerque, Sélestat 24-26 Caen, Tremblay 34-29 Cesson-Rennes) are now Full Time.",
            "official_check": "Fetched URC Match Centre and LNH Calendrier at 21:34 UTC.",
            "official_source_url": "https://stats.unitedrugby.com/match-centre/2026-27/4",
        },
        {
            "id": "HZ-AUD-10", "severity": "medium", "category": "PGA TOUR Butterfield Bermuda Championship R2 completion and -5 cut line",
            "file_path": "data/cadence/fixtures.json", "lines": "350-380",
            "issue": "Earlier captures recorded Eric Cole through 17 holes and a -4 cut line; Cole has now finished R2 with 65-65 (-12, 130) in a five-way tie for T3 behind Hirata and Blanchet (-13), and the projected cut moved to -5.",
            "official_check": "Fetched https://www.pgatour.com/leaderboard at 21:34 UTC.",
            "official_source_url": "https://www.pgatour.com/leaderboard",
        },
        {
            "id": "HZ-AUD-11", "severity": "high", "category": "OLBG header tip-count string-concatenation defect",
            "file_path": "research/horizon-9c5af337.md", "lines": "18-32",
            "issue": "OLBG event headers render '4 / 042' instead of '4 / 42' by concatenating selection tips with market totals; any naive scraper reading header pills corrupts tip denominators.",
            "official_check": "Verified on event_id=199984, 160789, 536036, and 902163.",
            "official_source_url": "https://www.olbg.com/betting-tips",
        },
        {
            "id": "HZ-AUD-12", "severity": "high", "category": "High-confidence (>70%) vs -250..+10000 fair-odds band intersection",
            "file_path": "research/horizon-9c5af337.md", "lines": "75-88",
            "issue": "Fair -250 equals 71.43% implied probability, so P >= 70% and fair odds >= -250 intersect only in [70.00%, 71.43%]. Desks that label -300 moneylines as in-band violate arithmetic.",
            "official_check": "Verified across all originated lines in scripts/horizon_verify.py.",
            "official_source_url": "https://www.olbg.com/betting-tips",
        },
        {
            "id": "HZ-AUD-13", "severity": "medium", "category": "MLB Game 2 starter Logan Henderson has no 2026 regular-season MLB pitching split",
            "file_path": "scripts/horizon_seed.py", "lines": "210-228",
            "issue": "MLB StatsAPI lists Logan Henderson (id 801403) as Milwaukee's probable Game 2 starter, but his 2026 regular-season MLB pitching stats split is empty.",
            "official_check": "Verified on statsapi.mlb.com/api/v1/people?personIds=801403; left blank rather than inferred.",
            "official_source_url": "https://statsapi.mlb.com/api/v1/people?personIds=694813,608379,801403,656876&hydrate=stats(group=%5Bpitching%5D,type=%5Bseason%5D,season=2026)",
        },
        {
            "id": "HZ-AUD-14", "severity": "medium", "category": "Three WST International Championship pre-qualifiers list unconfirmed Wildcard opponents",
            "file_path": "scripts/horizon_seed.py", "lines": "325-336",
            "issue": "WST match centre lists Michal Szubarczyk v Wildcard 1, Steven Hallworth v Wildcard 3, and Liu Wenwei v Wildcard 4 without naming the wildcard players.",
            "official_check": "Verified on https://www.wst.tv/match-centre/ee54f470-4821-4fd6-a5f4-db32dc475890; left unpriced.",
            "official_source_url": "https://www.wst.tv/match-centre/ee54f470-4821-4fd6-a5f4-db32dc475890",
        },
        {
            "id": "HZ-AUD-15", "severity": "medium", "category": "PDC European Championship Round Two unseeded entrants (Luke Littler & Kim Huybrechts)",
            "file_path": "scripts/horizon_seed.py", "lines": "340-375",
            "issue": "Kim Huybrechts entered Dortmund as a late replacement for Luke Humphries without a European Tour seeding, and Luke Littler's European Tour prize money is outside the top-three table published in the PDC schedule release.",
            "official_check": "Verified on pdc.tv schedule and Day One reports; both fixtures are left unpriced rather than guessing European Tour earnings.",
            "official_source_url": "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-schedule-play",
        },
        {
            "id": "HZ-AUD-16", "severity": "medium", "category": "ATP Almaty SF1 (Basilashvili) and Lyon SF1 (Cobolli v Van Assche/Musetti) unconfirmed inputs",
            "file_path": "scripts/horizon_seed.py", "lines": "430-448",
            "issue": "Qualifier Nikoloz Basilashvili sits outside the PIF ATP Top 100 table, and Flavio Cobolli's Lyon semifinal opponent was still in play in Set 3 (Van Assche 3-2 Musetti) at capture time.",
            "official_check": "Verified on atptour.com rankings and live scores; both rows are left unpriced and flagged.",
            "official_source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule",
        },
        {
            "id": "HZ-AUD-17", "severity": "medium", "category": "GBGB Category One finals publish semi-final winning times only for heat winners",
            "file_path": "scripts/horizon_seed.py", "lines": "485-515",
            "issue": "GBGB results pages publish winning clockings for the three semi-final winners in the Scurry Gold Cup and Oaks finals, but do not publish individual runner clockings for the three second-placed qualifiers.",
            "official_check": "Verified on gbgb.org.uk meetingId=435688; non-winning finalist times are left blank.",
            "official_source_url": "https://www.gbgb.org.uk/racing-results/?meetingId=435688&raceId=1198332",
        },
        {
            "id": "HZ-AUD-18", "severity": "medium", "category": "EHF Champions League Round 6 opponents outside French LNH table",
            "file_path": "scripts/horizon_seed.py", "lines": "540-560",
            "issue": "Aalborg, Dinamo Bucarest, and Orlen Wisla Plock appear on LNH's EHF Champions League calendar without domestic league tables on lnh.fr.",
            "official_check": "Verified on https://www.lnh.fr/autres-competitions/ligue-des-champions; left unpriced.",
            "official_source_url": "https://www.lnh.fr/autres-competitions/ligue-des-champions",
        },
        {
            "id": "HZ-AUD-19", "severity": "medium", "category": "Multi-session namespace proliferation across the repository",
            "file_path": "COORDINATION.md", "lines": "1-4600",
            "issue": "More than thirty parallel session namespaces exist in the repository. Horizon publishes in its own disjoint /horizon/ scope to avoid overwriting concurrent sessions.",
            "official_check": "Inspected COORDINATION.md and git branches on origin.",
            "official_source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md",
        },
    ],
}


def main():
    os.makedirs(CAP, exist_ok=True)
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

    with open(os.path.join(OUT, "olbg_taxonomy.json"), "w") as f:
        json.dump(OLBG_TAXONOMY, f, indent=1, ensure_ascii=False)

    with open(os.path.join(OUT, "repo_audit.json"), "w") as f:
        json.dump(REPO_AUDIT, f, indent=1, ensure_ascii=False)

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
    print(f"horizon_seed: fixtures={len(rows)} sports={len({r['sport'] for r in rows})} "
          f"sources={len(sources)} captures={len(bundles)} audit_findings={len(REPO_AUDIT['findings'])}")


if __name__ == "__main__":
    main()
