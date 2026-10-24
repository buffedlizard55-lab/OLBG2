"""Fixture records for the /compass/ desk (session arena/9f424dec-olbg2).

Each record: id, sport, competition, home, away, start_utc (official), start_display,
venue, official_url, blank (why the official source is missing), facts [(claim, value, source_key)],
inputs (model inputs), and the OLBG listing it came from (from compass_data_olbg.LISTINGS by event_id).
Facts marked facts_inherited come from the official capture committed by session
arena/4a8390fe-olbg2 at 2026-10-24T17:35Z (data/now/fixtures.json) and were corroborated
where this session re-fetched the same official source at ~22:30Z.
"""

S = {
    "olbg_capture": "https://www.olbg.com/betting-tips (all 15 hubs, this session)",
    "nhl_standings": "https://www.nhl.com/standings",
    "nhl_sched_24": "https://www.nhl.com/schedule/2026-10-24",
    "nhl_sched_25": "https://www.nhl.com/schedule/2026-10-25",
    "mlb_sched_ws": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-24&endDate=2026-10-31&hydrate=team,probablePitcher,decisions",
    "mlb_al": "https://statsapi.mlb.com/api/v1/standings?leagueId=103&season=2026&standingsTypes=regularSeason",
    "mlb_nl": "https://statsapi.mlb.com/api/v1/standings?leagueId=104&season=2026&standingsTypes=regularSeason",
    "mlb_pitchers": "https://statsapi.mlb.com/api/v1/people?personIds=656876,701656&hydrate=stats(group=[pitching],type=[season],season=2026)",
    "mlb_pitchers_g3": "https://statsapi.mlb.com/api/v1/people?personIds=688107,642547&hydrate=stats(group=[pitching],type=[season],season=2026)",
    "nba_standings": "https://www.nba.com/standings",
    "atp_almaty": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule?day=7",
    "atp_current": "https://www.atptour.com/en/scores/current",
    "wta_tournaments": "https://www.wtatennis.com/tournaments",
    "top14_cal": "https://top14.lnr.fr/calendrier-et-resultats",
    "top14_class": "https://top14.lnr.fr/classement",
    "galway_gaa": "https://www.galwaygaa.ie/changes-weekend-football-fixture-schedule/",
    "pdc_ec": "https://www.pdc.tv/news/2026/october/24/astonishing-littler-powers-through-to-finals-day-in-dortmund",
    "pdc_ec_r1": "https://www.pdc.tv/news/2026/october/23/Littler-kickstarts-European-Championship-title-bid-in-style/",
    "csa_pro20": "https://cricket.co.za/upcoming/8/",
    "rugby_au_a": "https://www.rugby.com.au/news/australia-a-team-confirmed-to-play-usa-in-nashville-20261022",
    "ecb_triseries": "https://www.ecb.co.uk/news/4594465/how-to-watch-and-follow-the-england-men-v-pakistan-and-sri-lanka",
    "icc_sl_chase": "https://www.icc-cricket.com/news/sri-lanka-pull-off-a-monumental-odi-chase-against-england",
    "icc_pak_87": "https://www.icc-cricket.com/news/pakistan-youngster-joins-elite-odi-group-with-superb-haul",
    "icc_nz_india": "https://www.icc-cricket.com/news/tilak-nitish-hold-their-nerve-as-india-take-2-0-lead",
    "opel_hbl": "https://www.opel-hbl.de/de/team/Rhein-Neckar%20L%C3%B6wen/fe80598a-3952-11ef-914c-af5c55c3771d",
    "lnh_starligue": "https://www.lnh.fr/daikin-starligue/accueil",
    "legavolley_tre": "https://www.legavolley.it/2026/ready-for-piacenza-2/?lang=en",
    "legavolley_per": "https://www.legavolley.it/2026/brand-new-administration-council-4/?lang=en",
    "prem_r4": "https://www.premrugby.com/competitions/gallagher-prem/fixtures-results?competition=gallagher-prem&round=4",
    "munster_gaa": "https://munster.gaa.ie/event/2026-cork-premier-senior-football-championship-final/",
    "nrl_rlwc": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/australia-v-fiji/",
    "pgatour": "https://www.pgatour.com/leaderboard",
    "europeantour": "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/leaderboard",
    "f1_us": "https://www.formula1.com/en/racing/2026/united-states",
    "wst_ni": "https://www.wst.tv/matches/",
    "gbgb": "https://www.gbgb.org.uk/",
}

# NHL 2026-27 standings at capture (30 of 32 teams; Chicago and Vancouver not captured —
# flagged). (gf, ga, gp)
NHL_TEAM = {
    "BOS": (42, 22, 11), "TBL": (34, 29, 10), "OTT": (31, 30, 11), "CAR": (47, 33, 12),
    "NYR": (37, 29, 12), "NJD": (36, 32, 11), "TOR": (43, 39, 12), "NYI": (29, 23, 10),
    "MTL": (34, 35, 10), "FLA": (31, 34, 11), "DET": (28, 30, 10), "WSH": (30, 29, 9),
    "BUF": (28, 37, 10), "PIT": (37, 38, 11), "PHI": (24, 42, 13), "CBJ": (20, 29, 8),
    "UTA": (41, 36, 11), "MIN": (32, 27, 11), "DAL": (26, 17, 10), "EDM": (47, 32, 10),
    "VGK": (46, 36, 12), "SEA": (44, 37, 11), "COL": (47, 34, 11), "SJS": (33, 37, 11),
    "STL": (35, 31, 10), "WPG": (26, 29, 10), "ANA": (32, 37, 11), "NSH": (23, 30, 9),
    "CGY": (19, 38, 9), "LAK": (21, 32, 9),
}

# (id, sport, comp, home, away, start_utc, start_display, venue, official_url, blank, facts, inputs)
FIXTURES = []


def F(*a, **kw):
    FIXTURES.append(dict(zip(
        ["id", "sport", "competition", "home", "away", "start_utc", "start_display",
         "venue", "official_url", "blank", "facts", "inputs"], a), **kw))


# --------------------------------------------------------------------------- Ice Hockey
F("nhl-tor-edm", "Ice Hockey", "NHL, 2026-27 regular season", "Edmonton Oilers", "Toronto Maple Leafs",
  "2026-10-24T23:00:00Z", "2026-10-24 23:00 UTC (NHL schedule)", "Rogers Place, Edmonton", S["nhl_sched_24"], "",
  [("Edmonton record", "8-1-1, 17 pts, 47 GF 32 GA in 10 GP; road 5-0-0", "nhl_standings"),
   ("Edmonton streak", "W3", "nhl_standings"),
   ("Toronto record", "6-4-2, 14 pts, 43 GF 39 GA in 12 GP; home 4-3-1", "nhl_standings"),
   ("Fixture", "TOR @ EDM, 7:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "EDM", "away": "TOR"})
F("nhl-sjs-bos", "Ice Hockey", "NHL, 2026-27 regular season", "Boston Bruins", "San Jose Sharks",
  "2026-10-24T23:00:00Z", "2026-10-24 23:00 UTC (NHL schedule)", "TD Garden, Boston", S["nhl_sched_24"], "",
  [("Boston record", "8-2-1, 17 pts, 42 GF 22 GA in 11 GP; home 4-1-0 (21 GF 6 GA in 5)", "nhl_standings"),
   ("Boston home defence", "6 goals against in 5 home games", "nhl_standings"),
   ("San Jose record", "6-4-1, 13 pts, 33 GF 37 GA in 11 GP; road 4-2-1", "nhl_standings"),
   ("San Jose regulation", "1 regulation win in 11 (inherited, 17:35Z capture)", "now_4a8390fe"),
   ("Fixture", "SJS @ BOS, 7:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "BOS", "away": "SJS"})
F("nhl-car-stl", "Ice Hockey", "NHL, 2026-27 regular season", "St. Louis Blues", "Carolina Hurricanes",
  "2026-10-24T23:00:00Z", "2026-10-24 23:00 UTC (NHL schedule)", "Enterprise Center, St. Louis", S["nhl_sched_24"], "",
  [("Carolina record", "8-2-2, 18 pts (league lead), 47 GF 33 GA in 12 GP; road 6-1-1 (34 GF 23 GA)", "nhl_standings"),
   ("St. Louis record", "5-4-1, 11 pts, 35 GF 31 GA in 10 GP; home 3-0-1", "nhl_standings"),
   ("St. Louis streak", "W2", "nhl_standings"),
   ("Fixture", "CAR @ STL, 7:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "STL", "away": "CAR"})
F("nhl-vgk-clb", "Ice Hockey", "NHL, 2026-27 regular season", "Columbus Blue Jackets", "Vegas Golden Knights",
  "2026-10-24T23:00:00Z", "2026-10-24 23:00 UTC (NHL schedule)", "Nationwide Arena, Columbus", S["nhl_sched_24"], "",
  [("Vegas record", "8-4-0, 16 pts, 46 GF 36 GA in 12 GP; road 3-2-0", "nhl_standings"),
   ("Columbus record", "3-5-0, 6 pts, 20 GF 29 GA in 8 GP; home 3-3-0", "nhl_standings"),
   ("Columbus streak", "L2", "nhl_standings"),
   ("Fixture", "VGS @ CLB, 7:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "CBJ", "away": "VGK"})
F("nhl-nyr-ott", "Ice Hockey", "NHL, 2026-27 regular season", "Ottawa Senators", "New York Rangers",
  "2026-10-24T23:00:00Z", "2026-10-24 23:00 UTC (NHL schedule)", "Canadian Tire Centre, Ottawa", S["nhl_sched_24"], "",
  [("Ottawa record", "7-4-0, 14 pts, 31 GF 30 GA in 11 GP; home 4-2-0", "nhl_standings"),
   ("New York record", "7-4-1, 15 pts, 37 GF 29 GA in 12 GP; home 6-0-0, road 1-4-1", "nhl_standings"),
   ("New York home/road split", "Perfect 6-0-0 at home; 1-4-1 on the road", "nhl_standings"),
   ("Fixture", "NYR @ OTT, 7:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "OTT", "away": "NYR"})
F("nhl-buf-was", "Ice Hockey", "NHL, 2026-27 regular season", "Washington Capitals", "Buffalo Sabres",
  "2026-10-24T23:00:00Z", "2026-10-24 23:00 UTC (NHL schedule)", "Capital One Arena, Washington", S["nhl_sched_24"], "",
  [("Washington record", "5-4-0, 10 pts, 30 GF 29 GA in 9 GP; home 4-2-0", "nhl_standings"),
   ("Buffalo record", "4-4-2, 10 pts, 28 GF 37 GA in 10 GP; road 1-1-2", "nhl_standings"),
   ("Fixture", "BUF @ WAS, 7:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "WSH", "away": "BUF"})
F("nhl-nsh-pit", "Ice Hockey", "NHL, 2026-27 regular season", "Pittsburgh Penguins", "Nashville Predators",
  "2026-10-24T23:00:00Z", "2026-10-24 23:00 UTC (NHL schedule)", "PPG Paints Arena, Pittsburgh", S["nhl_sched_24"], "",
  [("Pittsburgh record", "4-6-1, 9 pts, 37 GF 38 GA in 11 GP; home 3-1-0", "nhl_standings"),
   ("Nashville record", "3-3-3, 9 pts, 23 GF 30 GA in 9 GP; road 1-1-2", "nhl_standings"),
   ("Fixture", "NSH @ PIT, 7:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "PIT", "away": "NSH"})
F("nhl-tbl-uta", "Ice Hockey", "NHL, 2026-27 regular season", "Utah Mammoth", "Tampa Bay Lightning",
  "2026-10-25T01:00:00Z", "2026-10-24 21:00 EDT / 01:00Z (NHL schedule)", "Delta Center, Salt Lake City", S["nhl_sched_24"], "",
  [("Utah record", "7-4-0, 14 pts, 41 GF 36 GA in 11 GP; home 3-1-0", "nhl_standings"),
   ("Tampa Bay record", "7-3-0, 14 pts, 34 GF 29 GA in 10 GP; road 2-3-0", "nhl_standings"),
   ("Fixture", "TBL @ UTA, 9:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "UTA", "away": "TBL"})
F("nhl-det-cgy", "Ice Hockey", "NHL, 2026-27 regular season", "Calgary Flames", "Detroit Red Wings",
  "2026-10-25T02:00:00Z", "2026-10-24 22:00 EDT / 02:00Z (NHL schedule)", "Scotiabank Saddledome, Calgary", S["nhl_sched_24"], "",
  [("Calgary record", "3-6-0, 6 pts, 19 GF 38 GA in 9 GP (league-worst goal differential -19)", "nhl_standings"),
   ("Detroit record", "4-3-3, 11 pts, 28 GF 30 GA in 10 GP; W1", "nhl_standings"),
   ("Fixture", "DET @ CGY, 10:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "CGY", "away": "DET"})
F("nhl-min-sea", "Ice Hockey", "NHL, 2026-27 regular season", "Seattle Kraken", "Minnesota Wild",
  "2026-10-25T02:00:00Z", "2026-10-24 22:00 EDT / 02:00Z (NHL schedule)", "Climate Pledge Arena, Seattle", S["nhl_sched_24"], "",
  [("Seattle record", "7-3-1, 15 pts, 44 GF 37 GA in 11 GP; home 3-1-0, W2", "nhl_standings"),
   ("Minnesota record", "6-3-2, 14 pts, 32 GF 27 GA in 11 GP; road 2-3-2", "nhl_standings"),
   ("Fixture", "MIN @ SEA, 10:00 PM EDT Saturday 24 Oct (official)", "nhl_sched_24")],
  {"kind": "nhl", "home": "SEA", "away": "MIN"})
F("nhl-mtl-wpg", "Ice Hockey", "NHL, 2026-27 regular season (special event, neutral site)", "Winnipeg Jets", "Montral Canadiens".replace("Montral", "Montréal"),
  "2026-10-25T23:00:00Z", "2026-10-25 19:00 EDT / 23:00Z, neutral site (NHL schedule)", "Neutral site (NHL special event)", S["nhl_sched_25"], "",
  [("Fixture", "Canadiens vs Jets at a neutral site, 7:00 PM EDT Sunday 25 Oct (official; NHL marks it a special-event-season game)", "nhl_sched_25"),
   ("Montreal record", "5-3-2, 12 pts, 34 GF 35 GA in 10 GP; W1", "nhl_standings"),
   ("Winnipeg record", "4-3-3, 11 pts, 26 GF 29 GA in 10 GP", "nhl_standings")],
  {"kind": "nhl", "home": "WPG", "away": "MTL"})

# European ice hockey (OLBG-listed; no official league fixture page captured — flagged)
EU_HOCKEY = [
    ("200021", "ice-serv-zsc", "ZSC Lions", "Servette Genf", "Swiss National League", "2026-10-25T13:00:00Z"),
    ("200037", "ice-fra-wol", "Grizzlys Wolfsburg", "Lowen Frankfurt", "Deutsche Eishockey Liga", "2026-10-25T13:00:00Z"),
    ("200041", "ice-schw-ber", "Eisbaren Berlin", "Schwenninger Wild Wings", "Deutsche Eishockey Liga", "2026-10-25T13:00:00Z"),
    ("200018", "ice-bern-lug", "HC Lugano", "SC Bern", "Swiss National League", "2026-10-25T13:00:00Z"),
    ("200043", "ice-vie-grz", "Graz 99ers", "Vienna Capitals", "Austrian ICE Hockey League", "2026-10-25T13:45:00Z"),
    ("200039", "ice-kre-muc", "EHC Munchen", "Krefeld Pinguine", "Deutsche Eishockey Liga", "2026-10-25T15:30:00Z"),
    ("200038", "ice-ise-nur", "Nurnberg Ice Tigers", "Iserlohn Roosters", "Deutsche Eishockey Liga", "2026-10-25T15:30:00Z"),
    ("200036", "ice-aug-str", "Straubing Tigers", "Augsburger Panther", "Deutsche Eishockey Liga", "2026-10-25T15:30:00Z"),
    ("200040", "ice-bre-erc", "ERC Ingolstadt", "Fischtown Pinguins Bremerhaven", "Deutsche Eishockey Liga", "2026-10-25T18:00:00Z"),
]
for ev, fid, home, away, comp, st in EU_HOCKEY:
    F(fid, "Ice Hockey", comp, home, away, st, f"per OLBG display ({st[11:16]}Z)", "—", "",
      "No official league fixture page captured for this European-league game; start time is OLBG-derived.",
      [], {"kind": "olbg_only", "two_way": True})

# --------------------------------------------------------------------------- Baseball
F("mlb-g2", "Baseball", "MLB World Series 2026, Game 2 (Tampa Bay AL vs Milwaukee NL)", "Milwaukee Brewers", "Tampa Bay Rays",
  "2026-10-25T00:00:00Z", "2026-10-24 20:00 EDT / 00:00Z (MLB StatsAPI)", "American Family Field, Milwaukee", S["mlb_sched_ws"], "",
  [("Brewers regular season", "103-59 (.636), NL Central champions; 832 runs scored 618 allowed; home 55-26; night 68-35; W5 streak, last ten 8-2", "mlb_nl"),
   ("Rays regular season", "98-64 (.605), AL East champions; 736 runs scored 650 allowed; road 43-38; night 63-35", "mlb_al"),
   ("World Series Game 1 result", "Brewers 3, Rays 2 (23 October); Misiorowski win, Martinez loss, Megill save (inherited, corroborated by series record 1-0 in this session's schedule fetch)", "now_4a8390fe"),
   ("Game 2 probable pitchers", "Drew Rasmussen (TB) vs Logan Henderson (MIL) (official)", "mlb_sched_ws"),
   ("Rasmussen 2026", "30 GS, 16-5, 2.67 ERA, 172.0 IP, 174 K, 32 BB, 0.91 WHIP, 9.10 K/9", "mlb_pitchers"),
   ("Henderson 2026", "18 GS, 11-3, 2.47 ERA, 98.1 IP, 110 K, 19 BB, 0.84 WHIP, 10.07 K/9", "mlb_pitchers")],
  {"kind": "mlb", "home": "MIL", "away": "TB",
   "home_rs_pg": 5.136, "home_ra_pg": 3.815, "away_rs_pg": 4.543, "away_ra_pg": 4.012,
   "home_sp_era": 2.47, "away_sp_era": 2.67, "home_sp_whip": 0.84, "away_sp_whip": 0.91})
F("mlb-g3", "Baseball", "MLB World Series 2026, Game 3 (official schedule; not on the OLBG hub at capture)", "Tampa Bay Rays", "Milwaukee Brewers",
  "2026-10-27T00:00:00Z", "2026-10-26 20:00 EDT / 00:00Z (MLB StatsAPI)", "Tropicana Field, St. Petersburg", S["mlb_sched_ws"], "",
  [("Game 3 identity", "officialDate 2026-10-26 (gamePk 849804), Tropicana Field (inherited)", "now_4a8390fe"),
   ("Game 3 probable pitchers", "Robert Gasser (MIL) vs Freddy Peralta (TB) (official)", "mlb_sched_ws"),
   ("Gasser 2026", "20 GS, 5-5, 3.87 ERA, 109.1 IP, WHIP 1.19, 8.48 K/9, 2.88 BB/9 (LHP)", "mlb_pitchers_g3"),
   ("Peralta 2026 with TB", "10 GS, 5-2, 3.25 ERA, 55.1 IP, WHIP 1.01 (RHP; traded from New York mid-season)", "mlb_pitchers_g3")],
  {"kind": "mlb", "home": "TB", "away": "MIL",
   "home_rs_pg": 4.543, "home_ra_pg": 4.012, "away_rs_pg": 5.136, "away_ra_pg": 3.815,
   "home_sp_era": 3.25, "away_sp_era": 3.87, "home_sp_whip": 1.01, "away_sp_whip": 1.19})

# --------------------------------------------------------------------------- Basketball (NBA 2026-27, 2 games played each)
NBA_REC = {  # (w, l, home_w, home_l, road_w, road_l)
    "PHI": (2, 0, 1, 0, 1, 0), "MIL": (0, 2, 0, 1, 0, 1), "DEN": (0, 1, 0, 0, 0, 1),
    "NO": (0, 2, 0, 1, 0, 1), "CLE": (0, 1, 0, 0, 0, 1), "BKN": (0, 1, 0, 1, 0, 0),
    "DAL": (1, 1, 0, 0, 1, 1), "SA": (0, 2, 0, 0, 0, 2), "ATL": (2, 0, 0, 0, 2, 0),
    "HOU": (2, 0, 1, 0, 1, 0), "WAS": (1, 1, 1, 1, 0, 0), "CHI": (1, 1, 0, 0, 1, 1),
    "GS": (0, 2, 0, 1, 0, 1), "PHX": (0, 1, 0, 0, 0, 1),
}
NBA_FIX = [
    ("536111", "nba-mil-phi", "Philadelphia 76ers", "Milwaukee Bucks", "2026-10-24T23:30:00Z", "PHI", "MIL"),
    ("536112", "nba-bkn-cle", "Cleveland Cavaliers", "Brooklyn Nets", "2026-10-24T23:30:00Z", "CLE", "BKN"),
    ("536114", "nba-sa-dal", "Dallas Mavericks", "San Antonio Spurs", "2026-10-25T00:00:00Z", "DAL", "SA"),
    ("536113", "nba-was-chi", "Chicago Bulls", "Washington Wizards", "2026-10-25T00:00:00Z", "CHI", "WAS"),
    ("536115", "nba-hou-atl", "Atlanta Hawks", "Houston Rockets", "2026-10-25T00:30:00Z", "ATL", "HOU"),
    ("536116", "nba-no-den", "Denver Nuggets", "New Orleans Pelicans", "2026-10-25T01:00:00Z", "DEN", "NO"),
    ("536118", "nba-gs-phx", "Phoenix Suns", "Golden State Warriors", "2026-10-25T02:00:00Z", "PHX", "GS"),
]
for ev, fid, home, away, st, h, a in NBA_FIX:
    F(fid, "Basketball", "NBA 2026-27 regular season (2 games played each side at capture)", home, away, st,
      f"official UTC (2025-26 priors unavailable; nba.com standings page is JS-gated — flagged)", "—", S["nba_standings"],
      "Prior-season (2025-26) records unavailable from the official static page (JS-gated); current 2-game records only, so confidence is capped at medium.",
      [(f"{home} 2026-27 record", f"{NBA_REC[h][0]}-{NBA_REC[h][1]} (home {NBA_REC[h][2]}-{NBA_REC[h][3]}, road {NBA_REC[h][4]}-{NBA_REC[h][5]})", "nba_standings"),
       (f"{away} 2026-27 record", f"{NBA_REC[a][0]}-{NBA_REC[a][1]} (home {NBA_REC[a][2]}-{NBA_REC[a][3]}, road {NBA_REC[a][4]}-{NBA_REC[a][5]})", "nba_standings")],
      {"kind": "nba", "home": h, "away": a})
KBL = [
    ("536125", "kbl-gas-thr", "Seoul Thunders", "Korea Gas", "2026-10-25T07:30:00Z"),
    ("536126", "kbl-any-won", "Wonju", "Anyang", "2026-10-25T05:00:00Z"),
    ("536127", "kbl-seo-suw", "Suwon Sonicboom", "Seoul Knights", "2026-10-25T05:00:00Z"),
]
for ev, fid, home, away, st in KBL:
    F(fid, "Basketball", "Korean Basketball League (KBL)", home, away, st, "per OLBG display", "—", "",
      "No official KBL fixture page captured; OLBG listing only.", [], {"kind": "olbg_only", "two_way": True})

# --------------------------------------------------------------------------- Cricket
F("cri-pak-eng-odi4", "Cricket", "Pakistan ODI Tri-Series (Pakistan, England, Sri Lanka), 4th ODI", "Pakistan", "England",
  "2026-10-25T08:00:00Z", "2026-10-25 08:00 GMT (ECB)", "Gaddafi Stadium, Lahore", S["ecb_triseries"], "",
  [("Match 1 (tri-series)", "Pakistan beat Sri Lanka by 37 runs at Rawalpindi on 18 October (inherited)", "icc_pak_87"),
   ("Match 2", "Pakistan beat England by 87 runs at Rawalpindi on 20 October; Arafat Minhas took five wickets and made a half-century (inherited)", "icc_pak_87"),
   ("Match 3", "Sri Lanka chased 430 to beat England by two wickets at Rawalpindi on 22 October (inherited)", "icc_sl_chase"),
   ("England innings vs SL", "429/4; Harry Brook 202, the fastest ODI double century; Joe Root 69, Will Jacks 66 not out (inherited)", "icc_sl_chase"),
   ("England series position", "No win in three matches of the tri-series (inherited)", "icc_sl_chase"),
   ("Fixture", "Pakistan v England, 4th ODI, Gaddafi Stadium Lahore, 25 October 08:00 GMT (ECB, inherited)", "ecb_triseries")],
  {"kind": "cricket", "home": "PAK", "away": "ENG", "home_edge": 0.28, "away_edge": -0.10})
F("cri-tor-van", "Cricket", "Canadian T20 league (OLBG listing; league not on CSA/ICC schedules captured)", "Vancouver Guardians", "Toronto Kings",
  "2026-10-24T23:00:00Z", "per OLBG display (Today 19:00 ET)", "—", "",
  "No official fixture page found for this Canadian T20 fixture; OLBG listing only (flagged).",
  [], {"kind": "olbg_only", "two_way": True})
F("cri-nwd-nch", "Cricket", "CSA Pro20 Cup 2026/27, Pool B", "Northern Cape Heat", "North West Dragons",
  "2026-10-25T11:00:00Z", "2026-10-25 13:00 SAST (CSA)", "Senwes Park, Potchefstroom", S["csa_pro20"], "",
  [("Fixture", "North West Dragons vs Northern Cape Heat, 25 Oct 13:00 SAST, Senwes Park/NWC Oval Potchefstroom (CSA official page)", "csa_pro20")],
  {"kind": "cricket", "home": "NWD", "away": "NCH", "home_edge": 0.05, "away_edge": 0.05})
F("cri-tus-wp", "Cricket", "CSA Pro20 Cup 2026/27, Pool B", "Western Province", "Tuskers",
  "2026-10-25T11:00:00Z", "2026-10-25 13:00 SAST (CSA)", "City Oval, Pietermaritzburg", S["csa_pro20"], "",
  [("Fixture", "Tuskers vs Western Province (YesPlay WP Cobras), 25 Oct 13:00 SAST, City Oval Pietermaritzburg (CSA official page; Western Province's own fixture list confirms the pairing)", "csa_pro20"),
   ("OLBG vs CSA naming", "OLBG lists 'Tuskers vs Western Province'; CSA lists the home side as 'YesPlay WP Cobras' (Western Province's sponsored name) — same fixture", "csa_pro20")],
  {"kind": "cricket", "home": "WP", "away": "TUS", "home_edge": 0.10, "away_edge": 0.0})
F("cri-es-sae", "Cricket", "CSA Pro20 Cup 2026/27, Pool B", "Eastern Storm", "SA Emerging",
  "2026-10-25T11:00:00Z", "2026-10-25 13:00 SAST (per schedule listings)", "Willowmoore Park, Benoni", "",
      "Eastern Storm vs CSA Emerging appears on schedule aggregators (ESPN/SA fixture lists) but no CSA official match-centre page was captured (flagged).",
  [], {"kind": "cricket", "home": "ES", "away": "SAE", "home_edge": 0.05, "away_edge": -0.05})
F("cri-bol-tit", "Cricket", "CSA Pro20 Cup 2026/27, Pool A", "Momentum Multiply Titans", "Boland",
  "2026-10-25T11:00:00Z", "2026-10-25 13:00 SAST (CSA)", "Boland Park, Paarl", S["csa_pro20"], "",
  [("Fixture", "Boland vs Momentum Multiply Titans, 25 Oct 13:00 SAST, Boland Park Paarl (CSA official page)", "csa_pro20")],
  {"kind": "cricket", "home": "TIT", "away": "BOL", "home_edge": 0.05, "away_edge": -0.05})
F("cri-indw-zimbw", "Cricket", "India Women tour of Zimbabwe, 2nd ODI", "Zimbabwe Women", "India Women",
  "2026-10-25T08:30:00Z", "per OLBG display (Tomorrow 04:30 ET)", "—", "",
  "No official ICC fixture page captured for this match at session time; OLBG listing only (flagged).",
  [], {"kind": "olbg_only", "two_way": True, "prop_market": "Top Team 1 Batter"})
F("cri-nz-ind-t20i3", "Cricket", "India tour of New Zealand, 3rd T20I", "New Zealand", "India",
  "2026-10-27T07:00:00Z", "2026-10-27 (ICC match list, inherited)", "—", S["icc_nz_india"], "",
  [("Series position", "India lead the series 2-0 after the first two T20Is (inherited, ICC news 24 Oct)", "icc_nz_india"),
   ("Injury note", "India took an injury blow ahead of the 2nd T20I (inherited, ICC news)", "icc_nz_india")],
  {"kind": "cricket", "home": "NZ", "away": "IND", "home_edge": 0.05, "away_edge": 0.35})
F("cri-nam-irl-odi3", "Cricket", "Ireland tour of Namibia, 3rd ODI", "Namibia", "Ireland",
  "2026-10-27T07:30:00Z", "per OLBG display (27 Oct 03:30 ET)", "—", "",
  "No official ICC fixture page captured for this match at session time; OLBG listing only (flagged).",
  [], {"kind": "olbg_only", "two_way": True})
F("cri-sa-aus", "Cricket", "Australia tour of South Africa (OLBG listing; series context not captured)", "South Africa", "Australia",
  "2026-10-31T08:30:00Z", "per OLBG display (31 Oct 04:30 ET)", "—", "",
  "No official fixture page captured for this Test at session time; OLBG listing only (flagged).",
  [], {"kind": "olbg_only", "two_way": True, "prop_market": "Man of the Match"})
CRICKET_OUT = [
    ("182606", "cri-out-wc27", "ICC Men's Cricket World Cup 2027", "2027-11-21", "India", 6, 12),
    ("187184", "cri-out-bblw26", "Big Bash Women 2026", "2026-12-05", "Sydney Sixers Women", 2, 3),
    ("187503", "cri-out-bbl26", "T20 Big Bash 2026-27", "2026-12-12", "Adelaide Strikers", 1, 2),
    ("187504", "cri-out-sa20", "SA20 2026-27", "2027-01-24", "Pretoria Capitals", 1, 1),
    ("188350", "cri-out-blast27", "T20 Blast 2027", "2027-07-18", "Sussex", 1, 2),
]
for ev, fid, comp, dt, sel, tn, tt in CRICKET_OUT:
    F(fid, "Cricket", comp, "Field", sel, dt + "T00:00:00Z", f"ante-post ({dt})", "—", "",
      "Ante-post outright; no official market page captured; OLBG tip-share only (flagged).",
      [], {"kind": "outright", "selection": sel, "tips": tn, "total_tips": tt})

# --------------------------------------------------------------------------- Rugby Union
F("rug-usa-ausa", "Rugby Union", "Australia A tour of the USA, match 1 of 2", "USA Eagles", "Australia A",
  "2026-10-24T22:00:00Z", "2026-10-24 22:00 UTC = 9:00 AEDT Sunday 25 Oct (Rugby Australia)", "Geodis Park Stadium, Nashville", S["rugby_au_a"], "",
  [("Kickoff", "Sunday 25 October 9:00am AEDT at Geodis Park Stadium, Nashville (official; = 22:00Z Saturday 24 Oct UTC)", "rugby_au_a"),
   ("Squad", "Nine Wallabies in the matchday 23; captain Matt Faessler; Kadin Pritchard's first senior start at outside centre; head coach Stephen Larkham", "rugby_au_a"),
   ("OLBG time discrepancy", "OLBG displayed 'Today 19:00' (23:00Z) — one hour off the official 22:00Z kickoff; official time used (flagged)", "rugby_au_a")],
  {"kind": "rugby", "home": "USA", "away": "AUS_A", "home_edge": -0.25, "away_edge": 0.25})
F("rug-har-sar", "Rugby Union", "Gallagher Premiership, Round 4", "Harlequins", "Saracens",
  "2026-10-25T11:00:00Z", "2026-10-25 11:00 UTC (Premiership fixture, inherited)", "—", S["prem_r4"], "",
  [("Fixture", "Harlequins v Saracens, Gallagher Premiership Round 4 (inherited official capture 17:35Z)", "prem_r4"),
   ("OLBG time discrepancy", "OLBG displayed 'Tomorrow 11:00' (15:00Z in the OLBG Eastern view); the Premiership fixture page lists 11:00 UTC — official used (flagged)", "prem_r4")],
  {"kind": "rugby", "home": "HAR", "away": "SAR", "home_edge": 0.15, "away_edge": 0.0})
F("rug-lar-ubb", "Rugby Union", "Top 14 2026-27, J7", "Stade Rochelais", "Union Bordeaux-Begles",
  "2026-10-25T20:05:00Z", "2026-10-25 21:05 Paris local (LNR; France on CET after the Oct 25 changeover) = 20:05Z", "Stade de la Rochelle", S["top14_cal"], "",
  [("Kickoff", "dimanche 25 octobre 21h05 local, Canal+ (LNR official calendar)", "top14_cal"),
   ("Standings after J6", "La Rochelle 4th, 18 pts (4W-2L, PF 144 PA 135, +9); Bordeaux-Begles 3rd, 19 pts (4W-2L, +64) (LNR official)", "top14_class"),
   ("J7 Saturday results", "Toulouse 38-33 Perpignan; Toulon 41-20 Pau; Vannes 27-26 Clermont; Lyon 31-27 Bayonne; Castres 16-8 Paris; Montpellier 20-17 Racing 92 (LNR official)", "top14_cal"),
   ("La Rochelle form", "V-D-D-V-V over J2-J6; UBB D-V-D-V-V (LNR form column)", "top14_class")],
  {"kind": "rugby", "home": "LAR", "away": "UBB", "home_edge": 0.10, "away_edge": 0.15})
F("rug-out-six27", "Rugby Union", "Six Nations 2027 (ante-post)", "Field", "Ireland", "2027-03-14T00:00:00Z",
  "ante-post (OLBG lists event date 14 Mar 2027)", "—", "",
  "Ante-post outright; no official market page captured; OLBG tip-share only (flagged).",
  [], {"kind": "outright", "selection": "Ireland", "tips": 3, "total_tips": 10})

# --------------------------------------------------------------------------- Gaelic Sports (Gaelic Football hub)
F("gae-sal-mcg", "Gaelic Sports", "Galway Senior Football Championship Final (Pearse Stadium)", "Maigh Cuilinn", "Salthill-Knocknacarra",
  "2026-10-25T16:00:00Z", "2026-10-25 4:00pm (Galway GAA)", "Pearse Stadium, Galway", S["galway_gaa"], "",
  [("Fixture (official)", "Bon Secours Hospital Senior Football Championship County Final, Maigh Cuilinn vs Salthill-Knocknacarra, 4:00pm Sunday 25 Oct, Pearse Stadium (Galway GAA official, published 23 Oct after weather-related rescheduling)", "galway_gaa"),
   ("OLBG data error", "OLBG lists this event as 'Moycullen v Salthill-Knocknacarra' — the official Galway GAA schedule shows Maigh Cuilinn as Salthill-Knocknacarra's opponent; official used (flagged)", "galway_gaa")],
  {"kind": "gaelic", "home": "SAL", "away": "MC", "home_edge": 0.05, "away_edge": 0.0,
   "handicap": 3.5, "underdog_side": "Salthill-Knocknacarra"})
F("gae-stf-nem", "Gaelic Sports", "Cork Premier Senior Football Championship Final", "St Finbarrs", "Nemo Rangers",
  "2026-10-25T16:00:00Z", "2026-10-25 16:00 UTC (Munster GAA event page, inherited)", "—", S["munster_gaa"], "",
  [("Fixture (official)", "2026 Cork Premier Senior Football Championship Final, St Finbarrs v Nemo Rangers (Munster GAA event page, inherited)", "munster_gaa")],
  {"kind": "gaelic", "home": "STF", "away": "NEM", "home_edge": 0.05, "away_edge": 0.0,
   "handicap": 1.5, "underdog_side": "Nemo Rangers"})
F("gae-kan-eoc", "Gaelic Sports", "Cork club football (OLBG listing; fixture page not captured)", "Kanturk", "Eire Og Cor",
  "2026-11-01T13:00:00Z", "per OLBG display (01 Nov 09:00 ET)", "—", "",
  "No official fixture page captured for this Cork club fixture; OLBG listing only (flagged).",
  [], {"kind": "gaelic", "home": "KANT", "away": "EIREOG", "home_edge": 0.0, "away_edge": 0.0,
       "handicap": 0.5, "underdog_side": "Eire Og Cor"})
F("gae-frc-kil", "Gaelic Sports", "Limerick club football (OLBG listing; fixture page not captured)", "Kildimo Pallaskenry", "Fr Caseys",
  "2026-11-01T14:30:00Z", "per OLBG display (01 Nov 10:30 ET)", "—", "",
  "No official fixture page captured for this Limerick club fixture; OLBG listing only (flagged).",
  [], {"kind": "gaelic", "home": "KILD", "away": "FRC", "home_edge": -0.05, "away_edge": 0.05})
F("gae-out-aic27", "Gaelic Sports", "All-Ireland Football Championship 2027 (ante-post)", "Field", "Kerry",
  "2027-07-25T10:30:00Z", "ante-post (OLBG event date 25 Jul 2027)", "—", "",
  "Ante-post outright; no official market page captured; OLBG tip-share only (flagged).",
  [], {"kind": "outright", "selection": "Kerry", "tips": 5, "total_tips": 7})

# --------------------------------------------------------------------------- Greyhounds
F("gry-don-1104", "Greyhounds", "Doncaster, 11:04 race (OLBG 'Daily Races' card)", "Field (5 listed runners)", "Snowfall",
  "2026-10-25T11:04:00Z", "2026-10-25 11:04 BST/GMT (UK; clock change applies that day)", "Doncaster", "",
  "GBGB does not publish a public online racecard; the OLBG event page is the only runner list captured (flagged). OLBG shows five named selections (Grouchos Badger, Heathmill Barron, Luminous Dream, Shots Fired, Snowfall); a British card normally carries six.",
  [], {"kind": "olbg_only", "two_way": True, "runners": 5})

# --------------------------------------------------------------------------- Darts
F("dar-rsm-lwk", "Darts", "PDC Machineseeker European Championship, quarter-final (Finals Day)", "Luke Woodhouse", "Ross Smith",
  "2026-10-25T12:15:00Z", "2026-10-25 morning session (OLBG 08:15 ET = 12:15Z)", "Westfalenhalle, Dortmund", S["pdc_ec"], "",
  [("Woodhouse Round 2", "beat defending champion Gian van Veen 10-6 (official PDC result, Saturday 24 Oct)", "pdc_ec"),
   ("Ross Smith Round 2", "beat Damon Heta 10-7 (official PDC result, Saturday 24 Oct)", "pdc_ec"),
   ("Venue/format", "Machineseeker European Championship, Westfalenhalle Dortmund; quarter-finals on Finals Day Sunday 25 October, top prize £150,000 (official PDC)", "pdc_ec")],
  {"kind": "darts", "home": "WOO", "away": "RSM", "home_edge": -0.025, "away_edge": 0.025})
F("dar-prc-bun", "Darts", "PDC Machineseeker European Championship, quarter-final (Finals Day)", "Stephen Bunting", "Gerwyn Price",
  "2026-10-25T13:15:00Z", "2026-10-25 afternoon session (OLBG 09:15 ET = 13:15Z)", "Westfalenhalle, Dortmund", S["pdc_ec"], "",
  [("Price Round 2", "beat Cameron Menzies 10-4; hat-trick of ton-plus checkouts; won seven of the last eight legs (official PDC)", "pdc_ec"),
   ("Bunting Round 2", "beat Kim Huybrechts 10-3; converted 100, 108, 116 and 121 finishes; his first European Championship quarter-final since 2014 (official PDC)", "pdc_ec"),
   ("Littler context", "Littler reached Finals Day averaging 114.47 in a 10-5 win over Aspinall after 105.05 in round 1 (official PDC)", "pdc_ec")],
  {"kind": "darts", "home": "BUN", "away": "PRC", "home_edge": -0.05, "away_edge": 0.05})
F("dar-out-ec26", "Darts", "PDC Machineseeker European Championship, winner (Finals Day)", "Field (8 remaining)", "Luke Littler",
  "2026-10-25T18:00:00Z", "Finals Day Sunday 25 Oct (OLBG 14:00 ET = 18:00Z; PDC evening session)", "Westfalenhalle, Dortmund", S["pdc_ec"], "",
  [("Littler run", "Round 1: 6-3 over William O'Connor, avg 105.05, six 180s; Round 2: 10-5 over Aspinall, avg 114.47, four-leg flurry of 11/11/12/11-dart legs (official PDC)", "pdc_ec_r1"),
   ("Other Finals Day players", "Quarter-finalists include Price, Bunting, Ross Smith, Woodhouse (official PDC results)", "pdc_ec"),
   ("Prize", "£750,000 event; £150,000 to the winner (inherited, official PDC day-3 note)", "pdc_ec")],
  {"kind": "darts_outright", "selection": "Luke Littler", "tips": 13, "total_tips": 21})
F("dar-out-pdc27", "Darts", "PDC World Championship 2027 (ante-post)", "Field", "Luke Littler", "2027-01-03T00:00:00Z",
  "ante-post (OLBG event date 03 Jan 2027)", "—", "",
  "Ante-post outright; OLBG tip-share only (flagged).",
  [], {"kind": "outright", "selection": "Luke Littler", "tips": 22, "total_tips": 36})

# --------------------------------------------------------------------------- Tennis
F("ten-med-bas", "Tennis", "ATP Almaty, men's singles final", "Nikoloz Basilashvili", "Daniil Medvedev",
  "2026-10-25T09:00:00Z", "2026-10-25, not before 14:00 Almaty local (UTC+5) = 09:00Z (ATP daily schedule)", "Center Court, Almaty", S["atp_almaty"], "",
  [("Final pairing", "Medvedev (1) v Basilashvili (Q), day 9 (finals) of the Almaty event; not before 14:00 local (ATP official daily schedule)", "atp_almaty"),
   ("Medvedev semi-final", "beat Alexander Bublik (3) 6-3 with Bublik retiring in set 2 (ATP live score)", "atp_current"),
   ("Basilashvili semi-final", "beat Stefanos Tsitsipas (7) 6-4 6-7(5) 6-3 (ATP live score)", "atp_current"),
   ("OLBG time discrepancy", "OLBG displayed 'Tomorrow 06:00' (10:00Z in the Eastern view); the ATP schedule says not before 14:00 local = 09:00Z (flagged)", "atp_almaty")],
  {"kind": "tennis", "home": "MED", "away": "BAS", "home_edge": -0.05, "away_edge": 0.20})
F("ten-mus-fri", "Tennis", "ATP Lyon, men's singles final", "Taylor Fritz", "Lorenzo Musetti",
  "2026-10-25T13:30:00Z", "2026-10-25 13:30Z (OLBG display; ATP finals day)", "Court Central, Lyon", S["atp_current"], "",
  [("Final pairing", "Musetti (6) v Fritz (2), Lyon finals day (ATP live score page)", "atp_current"),
   ("Musetti semi-final", "beat Flavio Cobolli (1) 4-6 6-2 7-5 (ATP live score)", "atp_current"),
   ("Fritz semi-final", "beat Tommy Paul (4) 6-3 7-5 (ATP live score)", "atp_current")],
  {"kind": "tennis", "home": "FRI", "away": "MUS", "home_edge": 0.0, "away_edge": 0.10})
F("ten-ryb-fer", "Tennis", "WTA Tour event (name not confirmed on the official site — WTA draw pages are JS-gated; Osaka and Tokyo are the live Asia events)", "Leylah Fernandez", "Elena Rybakina",
  "2026-10-25T09:00:00Z", "per OLBG display (Tomorrow 05:00 ET = 09:00Z)", "—", S["wta_tournaments"],
  "WTA official draw/schedule pages render client-side; the tournament hosting this match could not be named from the official site (flagged).",
  [("WTA events active", "WTA update feed shows Kinoshita Group Japan Open (Osaka, draw 8 days old) and Toray Pan Pacific Open (Tokyo, draw released ~16h before capture) as the current Asia events", "wta_tournaments")],
  {"kind": "tennis", "home": "FER", "away": "RYB", "home_edge": -0.10, "away_edge": 0.30})
F("ten-krueg-sin", "Tennis", "WTA Tour event (name not confirmed on the official site — WTA draw pages are JS-gated)", "Katerina Siniakova", "Ashlyn Krueger",
  "2026-10-25T04:30:00Z", "per OLBG display (Tomorrow 00:30 ET = 04:30Z)", "—", S["wta_tournaments"],
  "WTA official draw/schedule pages render client-side; the tournament hosting this match could not be named from the official site (flagged).",
  [], {"kind": "tennis", "home": "SIN", "away": "KRUE", "home_edge": 0.05, "away_edge": 0.0})
WTA26 = [
    ("902175", "ten-eal-sto", "Mika Stojsavljevic", "Alexandra Eala", "2026-10-27T02:00:00Z"),
    ("902173", "ten-uch-mer", "Elise Mertens", "Moyuka Uchijima", "2026-10-27T02:00:00Z"),
    ("902172", "ten-fer-sak", "Himeno Sakatsume", "Leylah Fernandez", "2026-10-27T02:00:00Z"),
]
for ev, fid, home, away, st in WTA26:
    F(fid, "Tennis", "WTA Tour event (name not confirmed on the official site — WTA draw pages are JS-gated)", home, away, st,
      "per OLBG display", "—", S["wta_tournaments"],
      "WTA official draw/schedule pages render client-side; the tournament hosting this match could not be named from the official site (flagged).",
      [], {"kind": "tennis", "home": home[:3].upper(), "away": away[:3].upper(), "home_edge": 0.0, "away_edge": 0.05})
ATP26 = [
    ("902232", "ten-waw-leh", "Jiri Lehecka", "Stan Wawrinka"),
    ("902240", "ten-mic-vdz", "Botic Van De Zandschulp", "Alex Michelsen"),
    ("902237", "ten-vac-nav", "Mariano Navone", "Valentin Vacherot"),
    ("902231", "ten-she-ruu", "Casper Ruud", "Ben Shelton"),
    ("902234", "ten-kym-rin", "Arthur Rinderknech", "Jerome Kym"),
    ("902233", "ten-djo-hum", "Ugo Humbert", "Novak Djokovic"),
    ("902239", "ten-fri-tsi", "Stefanos Tsitsipas", "Taylor Fritz"),
    ("902236", "ten-run-hal", "Quentin Halys", "Holger Rune"),
    ("902235", "ten-fok-ber", "Zizou Bergs", "Alejandro Davidovich Fokina"),
    ("902238", "ten-tab-jod", "Rafael Jodar", "Alejandro Tabilo"),
    ("902247", "ten-hur-fil", "Arthur Fils", "Hubert Hurkacz"),
]
for ev, fid, home, away in ATP26:
    F(fid, "Tennis", "ATP Tour event starting 26 Oct (event name not confirmed from the ATP static pages captured)", home, away,
      "2026-10-26T10:00:00Z", "per OLBG display (26 Oct 06:00 ET = 10:00Z)", "—", S["atp_current"],
      "First-round pairings listed on OLBG with a single tipper each; the hosting ATP event could not be named from the static ATP pages captured this session (flagged).",
      [], {"kind": "tennis", "home": home[:3].upper(), "away": away[:3].upper(), "home_edge": 0.0, "away_edge": 0.0})

# --------------------------------------------------------------------------- Handball
F("han-rnl-mag", "Handball", "DAIKIN Handball-Bundesliga, Matchday 10", "SC Magdeburg", "Rhein-Neckar Lowen",
  "2026-10-25T13:00:00Z", "2026-10-25 13:00 UTC (opel-hbl.de, inherited)", "—", S["opel_hbl"], "",
  [("Fixture (official)", "SC Magdeburg v Rhein-Neckar Lowen, DAIKIN Handball-Bundesliga Matchday 10 (opel-hbl.de, inherited 17:35Z)", "opel_hbl"),
   ("RNL form context", "Rhein-Neckar Lowen team page (inherited): top-of-table Bundesliga side", "opel_hbl"),
   ("OLBG time discrepancy", "OLBG displayed 'Tomorrow 10:00' (14:00Z in the Eastern view); the official league page lists 13:00 UTC — official used (flagged)", "opel_hbl")],
  {"kind": "handball", "home": "MAG", "away": "RNL", "home_edge": -0.15, "away_edge": 0.30})
F("han-psg-sra", "Handball", "Daikin StarLigue (LNH), Journée 8", "PSG Handball", "Saint-Raphael",
  "2026-10-25T15:00:00Z", "2026-10-25 15:00 UTC (lnh.fr, inherited)", "Paris", S["lnh_starligue"], "",
  [("Fixture (official)", "PSG v Saint-Raphael, Daikin StarLigue Journée 8 (lnh.fr, inherited 17:35Z)", "lnh_starligue"),
   ("OLBG tip pattern", "OLBG's most-tipped selection on this event is 'Tie' 5/7 (71%) despite PSG being top-of-league hosts — community tip distribution flagged for review", "olbg_capture")],
  {"kind": "handball", "home": "PSG", "away": "SRA", "home_edge": 0.35, "away_edge": -0.30})
HAN_O = [
    ("12152", "han-yis-ham", "Ystads IF HF", "Hammarby IF HF", "2026-10-25T13:00:00Z", "Swedish Handball"),
    ("12106", "han-ali-adl", "CBM Sporting Alicante", "Ademar Leon", "2026-10-25T11:00:00Z", "ASOBAL (Spain)"),
    ("12136", "han-mag-kri", "SC Magdeburg", "HC Kriens Luzern", "2026-10-28T19:45:00Z", "EHF Champions League qualifying"),
    ("12102", "han-gra-pug", "BM Granollers", "Angel Ximenez Puente Genil", "2026-10-25T11:30:00Z", "ASOBAL (Spain)"),
    ("12125", "han-lit-bel", "Belgium W", "Lithuania W", "2026-10-25T14:00:00Z", "International (women)"),
    ("12126", "han-lux-gbr", "Great Britain W", "Luxembourg W", "2026-10-25T15:00:00Z", "International (women)"),
    ("12144", "han-amo-mal", "Amo HK", "HK Malmo", "2026-10-25T15:15:00Z", "Swedish Handball"),
    ("12087", "han-ber-ham", "Bergischer HC", "HC Hamburg", "2026-10-25T15:30:00Z", "Deutsche Handball-Bundesliga"),
    ("12128", "han-fuc-par", "Fuchse Berlin", "RK Partizan", "2026-10-29T17:45:00Z", "EHF Champions League qualifying"),
    ("12089", "han-fuc-wet", "Fuchse Berlin", "HSG Wetzlar", "2026-10-25T15:30:00Z", "Deutsche Handball-Bundesliga"),
    ("12154", "han-fol-kri", "Follo", "Kristiansand", "2026-10-25T17:00:00Z", "Norwegian Handball"),
    ("12132", "han-ksk-kol", "KS Kielce", "Kolstad", "2026-10-28T19:45:00Z", "EHF Champions League qualifying"),
    ("12075", "han-ska-tth", "Team Tvis Holstebro", "Skanderborg Handbold", "2026-10-25T15:00:00Z", "Danish Handball"),
    ("12148", "han-hif-ikc", "HIF Karlskrona", "IFK Kristianstad", "2026-10-25T15:00:00Z", "Swedish Handball"),
    ("12081", "han-mon-sar", "Montpellier", "Saran Loiret", "2026-10-25T16:00:00Z", "LNH (France)"),
    ("12149", "han-lug-sko", "Lugi HF", "IFK Skovde HK", "2026-10-25T16:00:00Z", "Swedish Handball"),
    ("12147", "han-ali-onn", "Alingsas HK", "Onnereds HK", "2026-10-25T16:30:00Z", "Swedish Handball"),
    ("12095", "han-gum-fln", "Vfl Gummersbach", "SG Flensburg Handewitt", "2026-10-25T17:00:00Z", "Deutsche Handball-Bundesliga"),
]
for ev, fid, home, away, st, comp in HAN_O:
    F(fid, "Handball", comp, home, away, st, "per OLBG display", "—", "",
      "No official league/EHF fixture page captured for this match at session time; OLBG listing only (flagged). EHF CL qualifiers additionally carry the note that OLBG's most-tipped selections are 'Tie', which is unusual for top-tier European fixtures.",
      [], {"kind": "handball", "home": home[:3].upper(), "away": away[:3].upper(), "home_edge": 0.0, "away_edge": 0.0})

# --------------------------------------------------------------------------- Volleyball
VBO = [
    ("37003", "vol-bru-pra", "Praia Clube W", "Abel-Moda Brusque W", "2026-10-25T00:00:00Z", "Brazil (Superliga)", "37003"),
    ("36994", "vol-cis-tre", "Itas Trentino", "Cisterna Volley", "2026-10-25T16:00:00Z", "SuperLega Credem Banca, Round 2", "elite"),
    ("37014", "vol-lud-rot", "TV Rottenburg", "Barock Volleys Ludwigsburg", "2026-10-25T16:00:00Z", "German Volleyball Bundesliga", ""),
    ("36995", "vol-pad-civ", "Lube Civitanova", "Kioene Padova", "2026-10-25T17:00:00Z", "SuperLega Credem Banca, Round 2", "elite"),
    ("36997", "vol-per-por", "Sir Susa Scai Perugia", "Tinet Prata di Pordenone", "2026-10-25T17:00:00Z", "SuperLega Credem Banca, Round 2", "elite"),
    ("37110", "vol-vak-gal", "Vakifbank W", "Galatasaray W", "2026-10-25T11:00:00Z", "Turkish women's league", ""),
    ("37059", "vol-ham-mun", "Munster W", "ETV Hamburg W", "2026-10-25T14:30:00Z", "German women's Bundesliga", ""),
    ("37076", "vol-con-val", "Imoco Volley Conegliano W", "Vallefoglia W", "2026-10-28T19:00:00Z", "Italian women's Serie A1", ""),
    ("37107", "vol-orp-kng", "LP Kangasala W", "Orpo W", "2026-10-25T15:00:00Z", "Finnish women's league", ""),
    ("36965", "vol-chl-res", "Resovia Rzeszow", "CHKS Chelm", "2026-10-25T17:00:00Z", "Polish PlusLiga", ""),
    ("36996", "vol-mnz-ver", "Verona Volley", "Vero Volley Monza", "2026-10-25T17:00:00Z", "SuperLega Credem Banca, Round 2", ""),
    ("37108", "vol-bes-goz", "Goztepe W", "Besiktas W", "2026-10-25T10:00:00Z", "Turkish women's league", ""),
    ("37109", "vol-kuz-nil", "Nilufer Bld W", "Kuzeyboru W", "2026-10-25T11:00:00Z", "Turkish women's league", ""),
    ("37111", "vol-ara-thy", "THY Spor Kulubu W", "Aras Kargo W", "2026-10-25T13:00:00Z", "Turkish women's league", ""),
    ("37112", "vol-ilb-afy", "Afyon Bld W", "Ilbank W", "2026-10-25T13:00:00Z", "Turkish women's league", ""),
    ("37113", "vol-man-zer", "Zeren Spor W", "Manisa BBSK W", "2026-10-25T13:00:00Z", "Turkish women's league", ""),
    ("37054", "vol-tou-nic", "Tourcoing", "Nice", "2026-10-25T16:00:00Z", "French Ligue A", ""),
    ("37114", "vol-fen-ecz", "Fenerbahce W", "Eczacibasi W", "2026-10-25T16:00:00Z", "Turkish women's league", ""),
    ("37101", "vol-mon-cru", "Sada Cruzeiro", "Montes Claros", "2026-10-26T23:00:00Z", "Brazilian men's league", ""),
    ("37102", "vol-nor-ren", "Volei Renata", "Norde Volei", "2026-10-27T01:00:00Z", "Brazilian men's league", ""),
]
for ev, fid, home, away, st, comp, x in VBO:
    elite = "elite" in x
    if fid == "vol-cis-tre":
        facts = [("Fixture (official)", "Cisterna v Trentino, SuperLega Round 2, 25 Oct (legavolley.it, inherited 17:35Z)", "legavolley_tre")]
    elif fid == "vol-per-por":
        facts = [("Fixture (official)", "Perugia v Pordenone, SuperLega Round 2, 25 Oct (legavolley.it, inherited 17:35Z)", "legavolley_per")]
    elif fid == "vol-pad-civ":
        facts = [("Context (official)", "Lega Pallavolo site live at capture; Civitanova/Padova listed in OLBG SuperLega Round 2 block (fixture page not individually captured)", "legavolley_tre")]
    else:
        facts = []
    F(fid, "Volleyball", comp, home, away, st, "per OLBG display / league schedule", "—",
      S["legavolley_tre"] if comp.startswith("SuperLega") else "",
      "" if comp.startswith("SuperLega") else "No official league fixture page captured for this match at session time; OLBG listing only (flagged).",
      facts, {"kind": "volleyball", "home": home, "away": away, "home_edge": 0.05, "away_edge": 0.0,
              **({"elite": True} if elite else {})})

# --------------------------------------------------------------------------- Rugby League (ante-post only on the hub)
RL_O = [
    ("2695857", "rl-out-soo27", "State of Origin 2027", "2027-05-27", "New South Wales", 9, 12),
    ("2801554", "rl-out-sl27", "Super League 2027 Grand Final", "2027-10-02", "Leeds Rhinos", 1, 3),
    ("2801600", "rl-out-nrl27", "NRL 2027 Grand Final", "2027-10-03", "Penrith Panthers", 1, 2),
]
for ev, fid, comp, dt, sel, tn, tt in RL_O:
    F(fid, "Rugby League", comp, "Field", sel, dt + "T00:00:00Z", f"ante-post ({dt})", "—", "",
      "Ante-post outright; no official market page captured; OLBG tip-share only (flagged). The hub listed no current RLWC 2026 match tips at capture even though the tournament is in progress (nrl.com context noted on the sport page).",
      [("RLWC context (official)", "Rugby League World Cup 2026 in progress; Round 2: Australia v Fiji 25 Oct (inherited, nrl.com draw)", "nrl_rlwc")],
      {"kind": "outright", "selection": sel, "tips": tn, "total_tips": tt})
