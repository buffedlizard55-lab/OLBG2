"""Additional official tennis, volleyball and handball inputs for 24 October 2026.

The structures contain only values read from the linked governing-body or league pages.
Prices and probabilities are derived separately in today_model.py.
"""
from __future__ import annotations

ATP_SCHEDULE = "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"
ATP_H2H = "https://www.atptour.com/en/players/atp-head-2-head/daniil-medvedev-vs-nikoloz-basilashvili/mm58/bg23"
ATP_FINAL_REPORT = "https://www.atptour.com/en/news/medvedev-bublik-almaty-2026-saturday"
WTA_NINGBO = "https://www.wtatennis.com/news/4598107/elena-rybakina-vs-leylah-fernandez-everything-to-know-about-the-ningbo-final"
WTA_NINGBO_EVENT = "https://www.wtatennis.com/tournaments/2092/ningbo/2026"
WTA_RYBAKINA = "https://www.wtatennis.com/players/324166/elena-rybakina"
WTA_FERNANDEZ = "https://www.wtatennis.com/players/326735/leylah-fernandez"
WTA_OSAKA_DRAW = "https://wtafiles.wtatennis.com/pdf/draws/2026/405/MDS.pdf"
WTA_OSAKA_EVENT = "https://www.wtatennis.com/tournaments/405/osaka/2026"
WTA_ASIAN_SCHEDULE = "https://www.wtatennis.com/news/4576359/asian-swing-2026-preview-dates-draws-prize-money-and-everything-you-need-to-know"
WTA_SINIAKOVA_SF = "https://www.wtatennis.com/videos/4598182/siniakova-defeats-boulter-in-osaka-semis-to-reach-first-wta-singles-final-since-2023"
WTA_KRUEGER = "https://www.wtatennis.com/players/329409/ashlyn-krueger"
LEGA_CAL = "https://www.legavolley.it/calendario/?idCampionato=999"
LEGA_TABLE = "https://www.legavolley.it/classifica/?IdCampionato=999"
LNH_CAL = "https://www.lnh.fr/daikin-starligue/calendrier"
LNH_TABLE = "https://www.lnh.fr/daikin-starligue/classement"
HBL_SCHEDULE = "https://www.opel-hbl.de/en/hbl"
HBL_TABLE = "https://www.opel-hbl.de/de/hbl/tabelle"
HBL_PREVIEW = "https://www.opel-hbl.de/de/hbl/content/vorschau-spieltag-10-abts-heimdeb%C3%BCt-gegen-den-meister-torj%C3%A4gertreffen-in-gummersbach-und-schw%C3%A4bisches-derby"
HBL_RNL_TEAM = "https://www.opel-hbl.de/de/team/Rhein-Neckar%20L%C3%B6wen/fe80598a-3952-11ef-914c-af5c55c3771d"
HBL_FUCHSE_TEAM = "https://www.opel-hbl.de/de/team/fe7bdd16-3952-11ef-b585-af5c55c3771d"
HBL_HAMBURG_TEAM = "https://www.opel-hbl.de/de/team/Handball%20Sport%20Verein%20Hamburg/0045fbc4-3953-11ef-a217-af5c55c3771d"


def tennis_fixture(identifier, competition, home, away, venue, start, start_display,
                   home_record, away_record, event_id, listed_selection, source,
                   stats_source, pricing_sources, basis, home_season=None, away_season=None,
                   home_sets=None, away_sets=None, fact_home="", fact_away="", extra_facts=None):
    return dict(
        id=identifier, sport="Tennis", competition=competition, home=home, away=away,
        venue=venue, start_utc=start, start_display=start_display,
        start_source="Official tournament order of play; not-before time converted to UTC",
        home_record=home_record, away_record=away_record,
        market_decimal_home=None, market_decimal_away=None, market_source=None,
        olbg_event_id=event_id, olbg_listed_selection=listed_selection, olbg_market="Win Match",
        fact_home=fact_home, fact_away=fact_away, source_url=source,
        source_label="Official tennis tournament schedule", stats_source_url=stats_source,
        pricing_source_urls=pricing_sources,
        tennis=dict(basis=basis, home_season=home_season, away_season=away_season,
                    home_sets=home_sets, away_sets=away_sets),
        extra_facts=extra_facts or [], injuries=[], injury_report_status="no official availability report read",
    )


TENNIS_ADDITIONS = [
    tennis_fixture(
        "tennis-atp-almaty-2026-final", "ATP 250 Almaty — final",
        "Daniil Medvedev", "Nikoloz Basilashvili", "Almaty Arena",
        "2026-10-25T09:00:00Z", "Not before 2026-10-25 09:00 UTC (15:00 Almaty)",
        "45-18", "7-10", "902251", "Daniil Medvedev", ATP_SCHEDULE, ATP_H2H,
        [ATP_SCHEDULE, ATP_H2H, ATP_FINAL_REPORT], "season", (45, 18), (7, 10),
        fact_home="Rank 5 with a 45-18 season record; 37 hard-court wins and a 10-1 Almaty record",
        fact_away="Rank 128 with a 7-10 season record; first tour final since Doha 2022 and live rank 97",
        extra_facts=[
            (f"ATP final report: Medvedev has 37 hard-court wins in 2026 and is 10-1 at Almaty; Basilashvili reached his first tour final since Doha 2022 and is live-ranked 97", ATP_FINAL_REPORT),
            ("ATP head-to-head: Medvedev leads 1-0 after winning their 2022 Vienna meeting 6-2 6-2", ATP_H2H),
        ]),
    tennis_fixture(
        "tennis-wta-osaka-2026-final", "WTA 250 Osaka — final",
        "Ashlyn Krueger", "Katerina Siniakova", "Utsubo Tennis Center",
        "2026-10-25T04:30:00Z", "Not before 2026-10-25 04:30 UTC (13:30 Japan)",
        "4-0", "4-0", "902171", "Katerina Siniakova", WTA_ASIAN_SCHEDULE, WTA_OSAKA_DRAW,
        [WTA_ASIAN_SCHEDULE, WTA_OSAKA_DRAW, WTA_SINIAKOVA_SF, WTA_KRUEGER], "tournament",
        home_sets=(8, 1), away_sets=(7, 1),
        fact_home="4-0 at Osaka with an 8-1 completed-set record; 2023 champion and current singles rank 55",
        fact_away="4-0 at Osaka with a 7-1 completed-set record; beat Katie Boulter 6-1 6-4 in the semifinal after an opening-round retirement", 
        extra_facts=[
            ("WTA Osaka draw: Krueger beat Tjen 6-4 6-4, Tararudee 6-3 6-1, Gibson 6-1 6-3 and top seed Ann Li 6-4 6-7(4) 6-3", WTA_OSAKA_DRAW),
            ("WTA Osaka draw: Siniakova beat Stearns 6-4 6-0 4-0 RET, Linette 6-4 6-1 and Stoiana 6-1 6-2", WTA_OSAKA_DRAW),
            ("WTA semifinal report: Siniakova beat Boulter 6-1 6-4 to reach her first singles final since 2023", WTA_SINIAKOVA_SF),
            ("WTA player profile: Krueger is current singles rank 55 and the 2023 Osaka champion", WTA_KRUEGER),
        ]),
    tennis_fixture(
        "tennis-wta-ningbo-2026-final", "WTA 500 Ningbo — final",
        "Elena Rybakina", "Leylah Fernandez", "Ningbo, China",
        "2026-10-25T09:00:00Z", "Not before 2026-10-25 09:00 UTC (17:00 Ningbo)",
        "49-14", "24-25", "902207", "Elena Rybakina", WTA_NINGBO_EVENT, WTA_NINGBO,
        [WTA_NINGBO_EVENT, WTA_NINGBO, WTA_RYBAKINA, WTA_FERNANDEZ], "season", (49, 14), (24, 25),
        fact_home="World No. 1 with a 49-14 season record and three titles; defending Ningbo champion",
        fact_away="World No. 30 with a 24-25 season record and one title; 11-2 since the start of the Asian Swing",
        extra_facts=[
            ("WTA final preview: Rybakina leads the head-to-head 3-2 and beat Fernandez in Stuttgart in 2026", WTA_NINGBO),
            ("WTA final preview: both players won their semifinals 6-3 7-5; Fernandez is 11-2 since the start of the Asian Swing", WTA_NINGBO),
            ("WTA player profiles: Rybakina is rank 1 with a 49-14 record and three titles; Fernandez is rank 30 with a 24-25 record and one title", WTA_RYBAKINA),
            ("Fernandez player profile corroborates rank 30, the 24-25 season record and one 2026 title", WTA_FERNANDEZ),
        ]),
]


def volleyball_stats(wins, losses, sets_for, sets_against, points_for, points_against):
    return dict(wins=wins, losses=losses, sets_for=sets_for, sets_against=sets_against,
                points_for=points_for, points_against=points_against)


def volleyball_fixture(identifier, home, away, venue, start, home_record, away_record,
                       event_id, listed_selection, listed_market, home_stats, away_stats,
                       fact_home, fact_away):
    return dict(
        id=identifier, sport="Volleyball", competition="Italy SuperLega — Round 2",
        home=home, away=away, venue=venue, start_utc=start,
        start_source="Lega Volley official calendar local time; Italy is UTC+1 after the 25 October clock change",
        home_record=home_record, away_record=away_record,
        market_decimal_home=None, market_decimal_away=None, market_source=None,
        olbg_event_id=event_id, olbg_listed_selection=listed_selection, olbg_market=listed_market,
        fact_home=fact_home, fact_away=fact_away, source_url=LEGA_CAL,
        source_label="Lega Volley official calendar", stats_source_url=LEGA_TABLE,
        pricing_source_urls=[LEGA_CAL, LEGA_TABLE],
        volleyball=dict(home=home_stats, away=away_stats), injuries=[],
        injury_report_status="no official availability report read",
    )


VOLLEYBALL_ADDITIONS = [
    volleyball_fixture("vol-20261025-trentino-cisterna", "Itas Trentino", "Cisterna Volley",
        "BTS Arena, Trento", "2026-10-25T16:00:00Z", "1-0", "1-0", "36994", "Cisterna", "Win Match",
        volleyball_stats(1, 0, 3, 0, 75, 61), volleyball_stats(1, 0, 3, 0, 79, 56),
        "Won 3-0 at Modena with 75 points for and 61 against", "Won 3-0 at home to Milano with 79 points for and 56 against"),
    volleyball_fixture("vol-20261025-perugia-pordenone", "Sir Susa Scai Perugia", "Tinet Prata di Pordenone",
        "Pala Barton Energy, Perugia", "2026-10-25T17:00:00Z", "1-0", "1-0", "36997", "Pordenone", "Win Match",
        volleyball_stats(1, 0, 3, 2, 114, 95), volleyball_stats(1, 0, 3, 1, 94, 91),
        "Won 3-2 at Cuneo with 114 points for and 95 against", "Won 3-1 at home to Monza with 94 points for and 91 against"),
    volleyball_fixture("vol-20261025-piacenza-modena", "Gas Sales Bluenergy Piacenza", "Valsa Group Modena",
        "PalaBancaSport, Piacenza", "2026-10-25T17:00:00Z", "1-0", "0-1", None, None, "Win Match",
        volleyball_stats(1, 0, 3, 0, 75, 56), volleyball_stats(0, 1, 0, 3, 61, 75),
        "Won 3-0 at Padova with 75 points for and 56 against", "Lost 0-3 at home to Trentino with 61 points for and 75 against"),
    volleyball_fixture("vol-20261025-civitanova-padova", "Cucine Lube Civitanova", "Pallavolo Padova",
        "Eurosuole Forum, Civitanova Marche", "2026-10-25T17:00:00Z", "1-0", "0-1", "36995", "Civitanova to win 3-1", "Set Score",
        volleyball_stats(1, 0, 3, 0, 78, 65), volleyball_stats(0, 1, 0, 3, 56, 75),
        "Won 3-0 at Verona with 78 points for and 65 against", "Lost 0-3 at home to Piacenza with 56 points for and 75 against"),
    volleyball_fixture("vol-20261025-milano-cuneo", "Allianz Milano", "Acqua Sant'Anna Cuneo",
        "Allianz Cloud (Palalido), Milano", "2026-10-25T18:00:00Z", "0-1", "0-1", None, None, "Win Match",
        volleyball_stats(0, 1, 0, 3, 56, 79), volleyball_stats(0, 1, 2, 3, 95, 114),
        "Lost 0-3 at Cisterna with 56 points for and 79 against", "Lost 2-3 at home to Perugia with 95 points for and 114 against"),
    volleyball_fixture("vol-20261025-monza-verona", "Vero Volley Monza", "Rana Verona",
        "OpiquadArena, Monza", "2026-10-25T17:00:00Z", "0-1", "0-1", "36996", "Monza", "Win Match",
        volleyball_stats(0, 1, 1, 3, 91, 94), volleyball_stats(0, 1, 0, 3, 65, 78),
        "Lost 1-3 at Pordenone with 91 points for and 94 against", "Lost 0-3 at home to Civitanova with 65 points for and 78 against"),
]


def handball_stats(gp, wins, losses, draws, goals_for, goals_against):
    return dict(gp=gp, wins=wins, losses=losses, draws=draws,
                goals_for=goals_for, goals_against=goals_against)


def handball_fixture(identifier, home, away, venue, start, home_record, away_record,
                     event_id, listed_selection, home_stats, away_stats, fact_home, fact_away):
    return dict(
        id=identifier, sport="Handball", competition="France Daikin StarLigue — Round 8",
        home=home, away=away, venue=venue, start_utc=start,
        start_source="LNH official calendar local time; France is UTC+1 after the 25 October clock change",
        home_record=home_record, away_record=away_record,
        market_decimal_home=None, market_decimal_away=None, market_source=None,
        olbg_event_id=event_id, olbg_listed_selection=listed_selection, olbg_market="Money Line",
        fact_home=fact_home, fact_away=fact_away, source_url=LNH_CAL,
        source_label="LNH official calendar", stats_source_url=LNH_TABLE,
        pricing_source_urls=[LNH_CAL, LNH_TABLE],
        handball=dict(home=home_stats, away=away_stats), injuries=[],
        injury_report_status="no official availability report read",
    )


HANDBALL_ADDITIONS = [
    handball_fixture("hb-20261025-saint-raphael-paris", "Saint-Raphaël", "Paris Saint-Germain Handball",
        "Saint-Raphaël, France", "2026-10-25T15:00:00Z", "2-5-0", "7-0-0", "12084", "PSG Handball",
        handball_stats(7, 2, 5, 0, 207, 225), handball_stats(7, 7, 0, 0, 239, 190),
        "2-5-0 in seven games with 207 goals for and 225 against", "7-0-0 in seven games with 239 goals for and 190 against"),
    handball_fixture("hb-20261025-montpellier-saran", "Montpellier Handball", "Saran Loiret Handball",
        "Montpellier, France", "2026-10-25T16:00:00Z", "4-1-2", "3-4-0", "12081", "Tie",
        handball_stats(7, 4, 1, 2, 234, 205), handball_stats(7, 3, 4, 0, 202, 216),
        "4-1-2 in seven games with 234 goals for and 205 against", "3-4-0 in seven games with 202 goals for and 216 against"),
]

def hbl_fixture(identifier, home, away, venue, start, home_record, away_record,
                event_id, listed_selection, home_stats, away_stats, fact_home, fact_away,
                venue_source, preview_fact):
    fixture = handball_fixture(identifier, home, away, venue, start, home_record, away_record,
                               event_id, listed_selection, home_stats, away_stats, fact_home, fact_away)
    fixture.update(
        competition="Germany Opel HBL — Round 10", source_url=HBL_SCHEDULE,
        source_label="Opel HBL official schedule", stats_source_url=HBL_TABLE,
        start_source="Opel HBL official schedule local time; Germany is UTC+1 after the 25 October clock change",
        pricing_source_urls=[HBL_SCHEDULE, HBL_TABLE, HBL_PREVIEW],
        extra_facts=[(preview_fact, HBL_PREVIEW),
                     (f"Official team page confirms {home}–{away}, {venue} and the Sunday local start", venue_source)],
    )
    return fixture


HBL_ADDITIONS = [
    hbl_fixture(
        "hb-20261025-rhein-neckar-magdeburg", "Rhein-Neckar Löwen", "SC Magdeburg", "SAP Arena",
        "2026-10-25T14:00:00Z", "3-5-1", "8-1-0", "12092", "Rhein Neckar Lowen",
        handball_stats(9, 3, 5, 1, 266, 273), handball_stats(9, 8, 1, 0, 301, 266),
        "3-5-1 in nine games with 266 goals for and 273 against", "8-1-0 in nine games with 301 goals for and 266 against",
        HBL_RNL_TEAM,
        "HBL matchday preview: Löwen lost 36-37 at Kiel and took one point from the last three; Magdeburg won four after its 30-34 defeat and latest won 29-28 at Stuttgart; Magdeburg is unbeaten in the last 11 head-to-heads with ten wins and one draw; Felix Claar has 53 goals, Haukur Thrastarson 48 and David Späth 118 saves"),
    hbl_fixture(
        "hb-20261025-bergischer-hamburg", "Bergischer HC", "Handball Club Hamburg", "Mitsubishi Electric Halle",
        "2026-10-25T15:30:00Z", "1-7-0", "2-6-1", "12087", "Tie",
        handball_stats(8, 1, 7, 0, 223, 256), handball_stats(9, 2, 6, 1, 274, 285),
        "1-7-0 in eight games with 223 goals for and 256 against", "2-6-1 in nine games with 274 goals for and 285 against",
        HBL_HAMBURG_TEAM,
        "HBL matchday preview: Bergischer won 29-28 at Balingen then lost 26-33 at Melsungen and has no home point; Hamburg won 35-30 at Bietigheim for its second win; Nicolaj Jørgensen has 59 goals and Fynn Hangstein 54; Bergischer won both meetings last season and leads the overall series 8-6"),
    hbl_fixture(
        "hb-20261025-fuchse-wetzlar", "Füchse Berlin", "HSG Wetzlar", "Max-Schmeling-Halle",
        "2026-10-25T15:30:00Z", "5-3-0", "0-7-2", "12089", "Fuchse Berlin",
        handball_stats(8, 5, 3, 0, 270, 256), handball_stats(9, 0, 7, 2, 272, 303),
        "5-3-0 in eight games with 270 goals for and 256 against", "0-7-2 in nine games with 272 goals for and 303 against",
        HBL_FUCHSE_TEAM,
        "HBL matchday preview: Füchse lost 36-37 to Lemgo and 33-34 at Flensburg on last-second goals; Wetzlar lost 30-34 to Erlangen and still seeks its first win; Mathias Gidsel has 70 goals in eight games and Niklas Theiß 54; Füchse won the last ten head-to-heads and leads the overall series 29-6"),
]

HANDBALL_ADDITIONS.extend(HBL_ADDITIONS)
EXTRA_FIXTURES = TENNIS_ADDITIONS + VOLLEYBALL_ADDITIONS + HANDBALL_ADDITIONS
