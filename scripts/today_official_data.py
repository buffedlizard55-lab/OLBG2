"""Official 24 October 2026 NHL and NBA inputs transcribed from league pages.

This module is deliberately data-only.  Rates, probabilities and prices are calculated
in today_model.py; no number here is inferred from a market or another dashboard.
"""
from __future__ import annotations

NHLE_SCORE = "https://api-web.nhle.com/v1/score/2026-10-24"
NHLE_TEAM = ("https://api.nhle.com/stats/rest/en/team/summary?isAggregate=false&isGame=false"
             "&sort=%5B%7B%22property%22:%22points%22,%22direction%22:%22DESC%22%7D%5D"
             "&start=0&limit=50&cayenneExp=seasonId=20262027%20and%20gameTypeId=2")
NBA_GAMES = "https://www.nba.com/games?date=2026-10-24"
NBA_STATS = "https://www.nba.com/stats/teams/traditional"
NBA_PRIOR = "https://www.nba.com/standings?Season=2025-26"
NBA_CURRENT = "https://www.nba.com/standings"
NBA_INJURY = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_30PM.pdf"

# games played, wins, regulation losses, OT losses, goals for, goals against.
# The official team-summary feed is used consistently for scoring rates.  Its GA
# convention can differ by one from the standings feed because of shootouts.
NHL = {
    "Carolina Hurricanes": (12, 8, 2, 2, 47, 32),
    "Edmonton Oilers": (10, 8, 1, 1, 46, 32),
    "Boston Bruins": (11, 8, 2, 1, 42, 22),
    "Vegas Golden Knights": (12, 8, 4, 0, 45, 36),
    "Seattle Kraken": (11, 7, 3, 1, 42, 37),
    "New York Rangers": (12, 7, 4, 1, 37, 29),
    "Tampa Bay Lightning": (10, 7, 3, 0, 34, 29),
    "Minnesota Wild": (11, 6, 3, 2, 32, 27),
    "Utah Mammoth": (11, 7, 4, 0, 41, 36),
    "Toronto Maple Leafs": (12, 6, 4, 2, 43, 38),
    "Ottawa Senators": (11, 7, 4, 0, 29, 30),
    "San Jose Sharks": (11, 6, 4, 1, 32, 36),
    "New Jersey Devils": (10, 6, 4, 0, 33, 31),
    "Detroit Red Wings": (10, 4, 3, 3, 27, 28),
    "St. Louis Blues": (10, 5, 4, 1, 35, 31),
    "Buffalo Sabres": (10, 4, 4, 2, 28, 36),
    "Washington Capitals": (9, 5, 4, 0, 30, 29),
    "Nashville Predators": (9, 3, 3, 3, 23, 28),
    "Pittsburgh Penguins": (11, 4, 6, 1, 36, 37),
    "Philadelphia Flyers": (12, 3, 6, 3, 20, 36),
    "Anaheim Ducks": (10, 4, 6, 0, 27, 33),
    "Columbus Blue Jackets": (8, 3, 5, 0, 19, 29),
    "Calgary Flames": (9, 3, 6, 0, 19, 38),
    "Los Angeles Kings": (8, 2, 4, 2, 20, 29),
}

NHL_ADDITIONS = [
    dict(id="nhl-2026020175", sport="Ice Hockey", competition="NHL",
         home="St. Louis Blues", away="Carolina Hurricanes", venue="Enterprise Center",
         start_utc="2026-10-24T23:00:00Z", start_source="NHL score feed startTimeUTC",
         home_record="5-4-1", away_record="8-2-2", market_decimal_home=2.28,
         market_decimal_away=1.65,
         market_source="NHL score feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200002", olbg_listed_selection="CAR Hurricanes", olbg_market="Money Line",
         fact_home="5-4-1 in 10 games; Mason McTavish has 6 goals, Dylan Holloway 7 assists and Joel Hofer 4 wins",
         fact_away="8-2-2 in 12 games; Sebastian Aho has 7 goals, Jackson Blake 10 assists and Pyotr Kochetkov 6 wins",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020176", sport="Ice Hockey", competition="NHL",
         home="Edmonton Oilers", away="Toronto Maple Leafs", venue="Rogers Place",
         start_utc="2026-10-24T23:00:00Z", start_source="NHL score feed startTimeUTC",
         home_record="8-1-1", away_record="6-4-2", market_decimal_home=1.56,
         market_decimal_away=2.45,
         market_source="NHL score feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200010", olbg_listed_selection="EDM Oilers", olbg_market="Money Line",
         fact_home="8-1-1 in 10 games; Leon Draisaitl has 10 goals, Connor McDavid 23 assists and Devon Levi 6 wins",
         fact_away="6-4-2 in 12 games; Auston Matthews has 8 goals and 10 assists, Sergei Bobrovsky 3 wins",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020177", sport="Ice Hockey", competition="NHL",
         home="Utah Mammoth", away="Tampa Bay Lightning", venue="Delta Center",
         start_utc="2026-10-25T01:00:00Z", start_source="NHL score feed startTimeUTC",
         home_record="7-4-0", away_record="7-3-0", market_decimal_home=1.71,
         market_decimal_away=2.17,
         market_source="NHL score feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200009", olbg_listed_selection="TB Lightning", olbg_market="Money Line",
         fact_home="7-4-0 in 11 games; Nick Schmaltz has 7 goals, Mikhail Sergachev 10 assists and Karel Vejmelka 5 wins",
         fact_away="7-3-0 in 10 games; Brandon Hagel has 7 goals, Nikita Kucherov 9 assists and Andrei Vasilevskiy 5 wins",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020178", sport="Ice Hockey", competition="NHL",
         home="Calgary Flames", away="Detroit Red Wings", venue="Scotiabank Saddledome",
         start_utc="2026-10-25T02:00:00Z", start_source="NHL score feed startTimeUTC",
         home_record="3-6-0", away_record="4-3-3", market_decimal_home=2.06,
         market_decimal_away=1.79,
         market_source="NHL score feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200004", olbg_listed_selection="DET Red Wings", olbg_market="Money Line",
         fact_home="3-6-0 in 9 games; Morgan Frost has 3 goals, Joel Farabee 5 assists and Devin Cooley 2 wins",
         fact_away="4-3-3 in 10 games; Alex DeBrincat has 6 goals and 6 assists, John Gibson 3 wins",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020179", sport="Ice Hockey", competition="NHL",
         home="Seattle Kraken", away="Minnesota Wild", venue="Climate Pledge Arena",
         start_utc="2026-10-25T02:00:00Z", start_source="NHL score feed startTimeUTC",
         home_record="7-3-1", away_record="6-3-2", market_decimal_home=2.33,
         market_decimal_away=1.63,
         market_source="NHL score feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200005", olbg_listed_selection="MIN Wild", olbg_market="Money Line",
         fact_home="7-3-1 in 11 games; Frederick Gaudreau has 6 goals, Chandler Stephenson 8 assists and Philipp Grubauer 4 wins",
         fact_away="6-3-2 in 11 games; Kirill Kaprizov has 11 goals, Quinn Hughes 11 assists and Jesper Wallstedt 6 wins",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
]


def nhl_stat(team):
    gp, w, l, o, gf, ga = NHL[team]
    return dict(gp=gp, wins=w, losses=l, ot_losses=o, goals_for=gf, goals_against=ga,
                source_url=NHLE_TEAM)


def injury(team, player, status, reason):
    return dict(team=team, player=player, status=status, reason=reason, source_url=NBA_INJURY)


def nba_game(game_id, home, away, start, home_record, away_record, prior_home, prior_away,
             home_stats, away_stats, fact_home, fact_away, event_id, listed_selection,
             injuries=None, report_status="submitted", listed_market="Money Line"):
    def pack(s):
        gp, w, l, pts, diff = s
        return dict(gp=gp, wins=w, losses=l, points_per_game=pts, point_differential=diff)
    return dict(
        id=f"nba-{game_id}", sport="Basketball", competition="NBA", home=home, away=away,
        venue=None, start_utc=start, start_source="NBA games page start time",
        home_record=home_record, away_record=away_record,
        market_decimal_home=None, market_decimal_away=None, market_source=None,
        prior_home_record=prior_home, prior_away_record=prior_away,
        nba=dict(home=pack(home_stats), away=pack(away_stats), source_url=NBA_STATS),
        olbg_event_id=event_id, olbg_listed_selection=listed_selection, olbg_market=listed_market,
        fact_home=fact_home, fact_away=fact_away, source_url=NBA_GAMES,
        source_label="NBA games page", injuries=injuries or [], injury_report_status=report_status,
        prior_source_url=NBA_PRIOR, current_standings_url=NBA_CURRENT,
    )


NBA_ADDITIONS = [
    nba_game("0022600104", "Charlotte Hornets", "Miami Heat", "2026-10-24T22:00:00Z",
             "1-1", "0-2", "44-38", "43-39", (2, 1, 1, 95.5, -20.0),
             (2, 0, 2, 108.5, -21.0),
             "1-1; Naz Reid averages 18.5 points, 8.5 rebounds and 4.5 assists",
             "0-2; Giannis Antetokounmpo averages 35.5 points, 9.0 rebounds and 3.0 assists",
             "536117", "CHA Hornets",
             [injury("Miami Heat", "Pelle Larsson", "Probable", "left finger sprain"),
              injury("Charlotte Hornets", "Christian Anderson", "Probable", "left ankle sprain"),
              injury("Charlotte Hornets", "Kylan Boswell", "Out", "right knee surgery"),
              injury("Charlotte Hornets", "Kon Knueppel", "Out", "left hamstring strain"),
              injury("Charlotte Hornets", "Coby White", "Out", "left calf strain"),
              injury("Charlotte Hornets", "Grant Williams", "Out", "right hamstring strain")]),
    nba_game("0022600105", "Cleveland Cavaliers", "Brooklyn Nets", "2026-10-24T23:30:00Z",
             "0-1", "0-1", "52-30", "20-62", (1, 0, 1, 106.0, -8.0),
             (1, 0, 1, 103.0, -7.0),
             "0-1; Donovan Mitchell posted 32 points, 10 rebounds and 3 assists",
             "0-1; Julius Randle posted 33 points, 8 rebounds and 7 assists",
             "536112", "CLE Cavaliers",
             [injury("Brooklyn Nets", "Tyler Bilodeau", "Out", "right shoulder labral tear"),
              injury("Cleveland Cavaliers", "Khalifa Diop", "Out", "left knee injury management"),
              injury("Cleveland Cavaliers", "Nae'Qwan Tomlin", "Out", "low back stress reaction"),
              injury("Cleveland Cavaliers", "Ernest Udeh Jr.", "Out", "G League two-way")]),
    nba_game("0022600106", "Philadelphia 76ers", "Milwaukee Bucks", "2026-10-24T23:30:00Z",
             "2-0", "0-2", "45-37", "32-50", (2, 2, 0, 110.0, 7.0),
             (2, 0, 2, 120.5, -9.5),
             "2-0; Tyrese Maxey averages 30.0 points, 3.5 rebounds and 5.5 assists",
             "0-2; Tyler Herro averages 29.0 points, 3.5 rebounds and 6.5 assists",
             "536111", "PHI 76ers",
             [injury("Philadelphia 76ers", "Dominick Barlow", "Out", "low back contusion"),
              injury("Philadelphia 76ers", "Tacko Fall", "Out", "left quad contusion"),
              injury("Philadelphia 76ers", "Ariel Hukporti", "Out", "right Achilles surgery"),
              injury("Philadelphia 76ers", "LeBron James", "Out", "low back sciatica")]),
    nba_game("0022600107", "Atlanta Hawks", "Houston Rockets", "2026-10-24T00:30:00Z".replace("2026-10-24", "2026-10-25"),
             "2-0", "2-0", "46-36", "52-30", (2, 2, 0, 130.0, 27.0),
             (2, 2, 0, 121.0, 11.0),
             "2-0; Jalen Johnson averages 19.5 points, 10.5 rebounds and 7.0 assists",
             "2-0; Alperen Sengun averages 26.0 points, 8.5 rebounds and 6.0 assists",
             "536115", "ATL Hawks -1.50",
             [injury("Houston Rockets", "Steven Adams", "Out", "left ankle injury management"),
              injury("Houston Rockets", "Reed Sheppard", "Questionable", "left knee contusion"),
              injury("Houston Rockets", "Fred VanVleet", "Out", "right knee injury management"),
              injury("Atlanta Hawks", "Mouhamed Gueye", "Out", "left foot fracture"),
              injury("Atlanta Hawks", "Henri Veesaar", "Out", "right ACL repair")],
             listed_market="Pointspread"),
    nba_game("0022600108", "Chicago Bulls", "Washington Wizards", "2026-10-25T00:00:00Z",
             "1-1", "1-1", "31-51", "17-65", (2, 1, 1, 112.0, -18.0),
             (2, 1, 1, 115.0, 1.0),
             "1-1; Jalen Smith averages 14.5 points, 10.5 rebounds and 1.0 assist",
             "1-1; Anthony Davis averages 21.5 points, 10.5 rebounds and 2.0 assists",
             "536113", "CHI Bulls",
             [injury("Chicago Bulls", "Nic Claxton", "Out", "left hamstring strain"),
              injury("Chicago Bulls", "Noa Essengue", "Probable", "right head contusion")],
             report_status="Washington Wizards NOT YET SUBMITTED"),
    nba_game("0022600109", "Dallas Mavericks", "San Antonio Spurs", "2026-10-25T00:00:00Z",
             "1-1", "0-2", "26-56", "62-20", (2, 1, 1, 115.5, -1.0),
             (2, 0, 2, 107.0, -8.0),
             "1-1; Cooper Flagg averages 23.0 points, 5.0 rebounds and 4.0 assists",
             "0-2; Victor Wembanyama averages 18.5 points, 13.0 rebounds and 2.5 assists",
             "536114", "SA Spurs", [], report_status="San Antonio Spurs and Dallas Mavericks NOT YET SUBMITTED"),
    nba_game("0022600110", "Denver Nuggets", "New Orleans Pelicans", "2026-10-25T01:00:00Z",
             "0-1", "0-2", "54-28", "26-56", (1, 0, 1, 84.0, -12.0),
             (2, 0, 2, 119.5, -2.0),
             "0-1; Aaron Gordon posted 20 points, 6 rebounds and 1 assist",
             "0-2; Dejounte Murray averages 19.5 points, 4.5 rebounds and 6.5 assists",
             "536116", "DEN Nuggets",
             [injury("Denver Nuggets", "Alpha Diallo", "Questionable", "right wrist sprain"),
              injury("Denver Nuggets", "Cameron Johnson", "Out", "right ankle sprain"),
              injury("Denver Nuggets", "Spencer Jones", "Out", "bilateral hamstring injury management"),
              injury("Denver Nuggets", "Julian Strawther", "Out", "left knee injury management")],
             report_status="New Orleans Pelicans NOT YET SUBMITTED"),
    nba_game("0022600111", "Phoenix Suns", "Golden State Warriors", "2026-10-25T02:00:00Z",
             "0-1", "0-2", "45-37", "37-45", (1, 0, 1, 83.0, -41.0),
             (2, 0, 2, 106.5, -12.5),
             "0-1; Devin Booker posted 23 points, 4 rebounds and 2 assists",
             "0-2; Stephen Curry averages 23.5 points, 2.0 rebounds and 2.5 assists",
             "536118", "PHX Suns",
             [injury("Phoenix Suns", "Oso Ighodaro", "Doubtful", "right oblique strain"),
              injury("Phoenix Suns", "Luke Kennard", "Questionable", "left knee soreness"),
              injury("Phoenix Suns", "Mark Williams", "Out", "left shoulder injury management")],
             report_status="Golden State Warriors NOT YET SUBMITTED"),
]


def expand_fixtures(fixtures):
    """Add newly read fixtures and attach structured official statistics in place."""
    fixtures.extend(NHL_ADDITIONS)
    for fixture in fixtures:
        if fixture["sport"] == "Ice Hockey":
            fixture["nhl"] = dict(home=nhl_stat(fixture["home"]), away=nhl_stat(fixture["away"]),
                                  source_url=NHLE_TEAM)
            fixture["stats_source_url"] = NHLE_TEAM
            fixture.setdefault("injuries", [])
            fixture.setdefault("injury_report_status", "no official team injury report read")
    fixtures.extend(NBA_ADDITIONS)
    # Imported lazily so this module remains the single expansion entry point while
    # the additional sports keep a separately auditable data file.
    from today_extra_data import EXTRA_FIXTURES
    from today_motor_data import MOTOR_FIXTURE
    from today_darts_data import DARTS_FIXTURES
    fixtures.extend(EXTRA_FIXTURES)
    fixtures.append(MOTOR_FIXTURE)
    fixtures.extend(DARTS_FIXTURES)
    return fixtures
