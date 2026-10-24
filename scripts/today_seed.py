#!/usr/bin/env python3
"""Seed the 2026-10-24 snapshot: OLBG listings as displayed, and first-hand official fixture facts.

Every value in `OLBG` was read off the live sport hub listed in `HUB` during the capture
window recorded in `CAPTURE`.  Every value in `FIXTURES` was read off the official league
feed named in the row's source URLs.  Nothing here is inferred: if a field was not seen it
is `None` and is reported as blank/unverified downstream.
"""
from __future__ import annotations
import json
from pathlib import Path
from today_official_data import expand_fixtures

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "today"
OUT.mkdir(parents=True, exist_ok=True)

CAPTURE_UTC = "2026-10-24T17:15:00Z"
CAPTURE_END_UTC = "2026-10-24T18:25:00Z"
SESSION = "arena/9f69ce85-olbg2"

HUB = {
    "Golf": ("https://www.olbg.com/betting-tips/Golf/5", 5),
    "Volleyball": ("https://www.olbg.com/betting-tips/Volleyball/21", 21),
    "Rugby Union": ("https://www.olbg.com/betting-tips/Rugby_Union/9", 9),
    "Cricket": ("https://www.olbg.com/betting-tips/Cricket/7", 7),
    "Snooker": ("https://www.olbg.com/betting-tips/Snooker/8", 8),
    "Darts": ("https://www.olbg.com/betting-tips/Darts/15", 15),
    "Baseball": ("https://www.olbg.com/betting-tips/Baseball/12", 12),
    "Gaelic Sports": ("https://www.olbg.com/betting-tips/Gaelic_Football/25", 25),
    "Greyhounds": ("https://www.olbg.com/betting-tips/Greyhounds/28", 28),
    "Tennis": ("https://www.olbg.com/betting-tips/Tennis/3", 3),
    "Motor Racing": ("https://www.olbg.com/betting-tips/Motor_Racing/14", 14),
    "Handball": ("https://www.olbg.com/betting-tips/Handball/20", 20),
    "Ice Hockey": ("https://www.olbg.com/betting-tips/Ice_Hockey/13", 13),
    "Basketball": ("https://www.olbg.com/betting-tips/Basketball/4", 4),
    "Rugby League": ("https://www.olbg.com/betting-tips/Rugby_League/10", 10),
}

B = "https://www.olbg.com/betting-tips"

# (sport, competition, event as displayed, displayed time, market, most-tipped selection, tips, pct, event_id, url)
OLBG = [
    # Ice Hockey — refreshed from the live hub after the initial capture --------
    ("Ice Hockey", "NHL", "CAR Hurricanes @ STL Blues", "Today 19:07", "Money Line", "CAR Hurricanes", "5/5", 100, "200002", f"{B}/Ice_Hockey/NHL/NHL/CAR_Hurricanes_@_STL_Blues/13?event_id=200002"),
    ("Ice Hockey", "NHL", "NY Rangers @ OTT Senators", "Today 19:07", "Money Line", "NY Rangers", "4/4", 100, "200008", f"{B}/Ice_Hockey/NHL/NHL/NY_Rangers_@_OTT_Senators/13?event_id=200008"),
    ("Ice Hockey", "NHL", "MIN Wild @ SEA Kraken", "Today 23:07", "Money Line", "MIN Wild", "4/5", 80, "200005", f"{B}/Ice_Hockey/NHL/NHL/MIN_Wild_@_SEA_Kraken/13?event_id=200005"),
    ("Ice Hockey", "NHL", "LA Kings @ NJ Devils", "Today 15:37", "Money Line", "NJ Devils", "3/5", 60, "200000", f"{B}/Ice_Hockey/NHL/NHL/LA_Kings_@_NJ_Devils/13?event_id=200000"),
    ("Ice Hockey", "NHL", "SJ Sharks @ BOS Bruins", "Today 19:07", "Money Line", "BOS Bruins", "3/3", 100, "200007", f"{B}/Ice_Hockey/NHL/NHL/SJ_Sharks_@_BOS_Bruins/13?event_id=200007"),
    ("Ice Hockey", "NHL", "TOR Maple Leafs @ EDM Oilers", "Today 19:07", "Money Line", "EDM Oilers", "3/5", 60, "200010", f"{B}/Ice_Hockey/NHL/NHL/TOR_Maple_Leafs_@_EDM_Oilers/13?event_id=200010"),
    ("Ice Hockey", "NHL", "TB Lightning @ UTA Mammoth", "Today 22:07", "Money Line", "UTA Mammoth", "3/5", 60, "200009", f"{B}/Ice_Hockey/NHL/NHL/TB_Lightning_@_UTA_Mammoth/13?event_id=200009"),
    ("Ice Hockey", "NHL", "DET Red Wings @ CGY Flames", "Today 23:07", "Money Line", "DET Red Wings", "3/4", 75, "200004", f"{B}/Ice_Hockey/NHL/NHL/DET_Red_Wings_@_CGY_Flames/13?event_id=200004"),
    ("Ice Hockey", "NHL", "VGS Golden Knights @ CLB Blue Jackets", "Today 19:07", "Money Line", "VGS Golden Knights", "2/3", 67, "200001", f"{B}/Ice_Hockey/NHL/NHL/VGS_Golden_Knights_@_CLB_Blue_Jackets/13?event_id=200001"),
    ("Ice Hockey", "NHL", "BUF Sabres @ WAS Capitals", "Today 19:07", "Money Line", "BUF Sabres", "2/3", 67, "200003", f"{B}/Ice_Hockey/NHL/NHL/BUF_Sabres_@_WAS_Capitals/13?event_id=200003"),
    ("Ice Hockey", "NHL", "NSH Predators @ PIT Penguins", "Today 19:07", "Money Line", "PIT Penguins", "2/3", 67, "200006", f"{B}/Ice_Hockey/NHL/NHL/NSH_Predators_@_PIT_Penguins/13?event_id=200006"),
    ("Ice Hockey", "Germany Eishockey Liga", "Lowen Frankfurt vs Grizzlys Wolfsburg", "Tomorrow 09:00", "Money Line", "Grizzlys Wolfsburg", "2/2", 100, "200037", f"{B}/Ice_Hockey/Other/Germany_Eishockey_Liga/Lowen_Frankfurt_vs_Grizzlys_Wolfsburg/13?event_id=200037"),
    ("Ice Hockey", "Switzerland NLA", "Servette GE vs ZSC Lions", "Tomorrow 09:00", "Money Line", "ZSC Lions", "2/2", 100, "200021", f"{B}/Ice_Hockey/Other/Switzerland_NLA/Servette_GE_vs_ZSC_Lions/13?event_id=200021"),
    ("Ice Hockey", "Germany Eishockey Liga", "Schwenninger Wild Wings vs Eisbaren Berlin", "Tomorrow 09:00", "Money Line", "Eisbaren Berlin", "2/2", 100, "200041", f"{B}/Ice_Hockey/Other/Germany_Eishockey_Liga/Schwenninger_Wild_Wings_vs_Eisbaren_Berlin/13?event_id=200041"),
    ("Ice Hockey", "Switzerland NLA", "Bern vs Lugano", "Tomorrow 09:00", "Money Line", "Bern", "1/1", 100, "200018", f"{B}/Ice_Hockey/Other/Switzerland_NLA/Bern_vs_Lugano/13?event_id=200018"),
    ("Ice Hockey", "Austria EHL", "Vienna Capitals vs Graz 99ers", "Tomorrow 09:45", "Money Line", "Vienna Capitals", "1/1", 100, "200043", f"{B}/Ice_Hockey/Other/Austria_EHL/Vienna_Capitals_vs_Graz_99ers/13?event_id=200043"),
    ("Ice Hockey", "Germany Eishockey Liga", "Iserlohn Roosters vs Nurnberg Ice Tigers", "Tomorrow 11:30", "Money Line", "Iserlohn Roosters", "1/1", 100, "200038", f"{B}/Ice_Hockey/Other/Germany_Eishockey_Liga/Iserlohn_Roosters_vs_Nurnberg_Ice_Tigers/13?event_id=200038"),
    ("Ice Hockey", "Germany Eishockey Liga", "Augsburger Panther vs Straubing Tigers", "Tomorrow 11:30", "Money Line", "Straubing Tigers", "1/1", 100, "200036", f"{B}/Ice_Hockey/Other/Germany_Eishockey_Liga/Augsburger_Panther_vs_Straubing_Tigers/13?event_id=200036"),
    ("Ice Hockey", "Germany Eishockey Liga", "Krefeld Pinguine vs EHC Munchen", "Tomorrow 11:30", "Money Line", "EHC Munchen", "1/1", 100, "200039", f"{B}/Ice_Hockey/Other/Germany_Eishockey_Liga/Krefeld_Pinguine_vs_EHC_Munchen/13?event_id=200039"),
    ("Ice Hockey", "Germany Eishockey Liga", "Fischtown Pinguins Bremerhaven vs ERC Ingolstadt", "Tomorrow 14:00", "Money Line", "Fischtown Pinguins Bremerhaven", "1/1", 100, "200040", f"{B}/Ice_Hockey/Other/Germany_Eishockey_Liga/Fischtown_Pinguins_Bremerhaven_vs_ERC_Ingolstadt/13?event_id=200040"),
    # Basketball — refreshed from the live hub after the initial capture ---------
    ("Basketball", "Brazil NBB", "Pato Basquete vs Botafogo", "Today 18:00", "Money Line", "Pato Basquete", "3/3", 100, "536087", f"{B}/Basketball/Other/Brazil_NBB/Pato_Basquete_vs_Botafogo/4?event_id=536087"),
    ("Basketball", "NBA", "BKN Nets @ CLE Cavaliers", "Today 19:30", "Money Line", "CLE Cavaliers", "3/4", 75, "536112", f"{B}/Basketball/NBA/NBA/BKN_Nets_@_CLE_Cavaliers/4?event_id=536112"),
    ("Basketball", "NBA", "MIL Bucks @ PHI 76ers", "Today 19:30", "Money Line", "PHI 76ers", "3/4", 75, "536111", f"{B}/Basketball/NBA/NBA/MIL_Bucks_@_PHI_76ers/4?event_id=536111"),
    ("Basketball", "NBA", "HOU Rockets @ ATL Hawks", "Today 20:30", "Pointspread", "ATL Hawks -1.50", "3/3", 100, "536115", f"{B}/Basketball/NBA/NBA/HOU_Rockets_@_ATL_Hawks/4?event_id=536115"),
    ("Basketball", "NBA", "MIA Heat @ CHA Hornets", "Today 18:00", "Money Line", "CHA Hornets", "2/2", 100, "536117", f"{B}/Basketball/NBA/NBA/MIA_Heat_@_CHA_Hornets/4?event_id=536117"),
    ("Basketball", "NBA", "NO Pelicans @ DEN Nuggets", "Today 22:00", "Money Line", "DEN Nuggets", "2/3", 67, "536116", f"{B}/Basketball/NBA/NBA/NO_Pelicans_@_DEN_Nuggets/4?event_id=536116"),
    ("Basketball", "NBA", "SA Spurs @ DAL Mavericks", "Today 20:00", "Money Line", "SA Spurs", "1/2", 50, "536114", f"{B}/Basketball/NBA/NBA/SA_Spurs_@_DAL_Mavericks/4?event_id=536114"),
    ("Basketball", "NBA", "WAS Wizards @ CHI Bulls", "Today 20:00", "Money Line", "CHI Bulls", "1/2", 50, "536113", f"{B}/Basketball/NBA/NBA/WAS_Wizards_@_CHI_Bulls/4?event_id=536113"),
    ("Basketball", "NBA", "GS Warriors @ PHX Suns", "Today 23:00", "Money Line", "PHX Suns", "1/2", 50, "536118", f"{B}/Basketball/NBA/NBA/GS_Warriors_@_PHX_Suns/4?event_id=536118"),
    # Tennis ------------------------------------------------------------------
    ("Tennis", None, "Ashlyn Krueger vs Katerina Siniakova", "Tomorrow 00:30", "Win Match", "Katerina Siniakova", "3/4", 75, "902171", f"{B}/Tennis/All_Tennis/All_Events/Ashlyn_Krueger_vs_Katerina_Siniakova/3?event_id=902171"),
    ("Tennis", None, "Elena Rybakina vs Leylah Fernandez", "Tomorrow 05:00", "Win Match", "Elena Rybakina", "4/4", 100, "902207", f"{B}/Tennis/All_Tennis/All_Events/Elena_Rybakina_vs_Leylah_Fernandez/3?event_id=902207"),
    ("Tennis", None, "Daniil Medvedev vs Nikoloz Basilashvili", "Tomorrow 06:00", "Win Match", "Daniil Medvedev", "3/3", 100, "902251", f"{B}/Tennis/All_Tennis/All_Events/Daniil_Medvedev_vs_Nikoloz_Basilashvili/3?event_id=902251"),
    ("Tennis", None, "Alexandra Eala vs Mika Stojsavljevic", "26 Oct 22:00", "Win Match", "Alexandra Eala", "1/1", 100, "902175", f"{B}/Tennis/All_Tennis/All_Events/Alexandra_Eala_vs_Mika_Stojsavljevic/3?event_id=902175"),
    ("Tennis", None, "Moyuka Uchijima vs Elise Mertens", "26 Oct 22:00", "Win Match", "Elise Mertens", "1/1", 100, "902173", f"{B}/Tennis/All_Tennis/All_Events/Moyuka_Uchijima_vs_Elise_Mertens/3?event_id=902173"),
    ("Tennis", None, "Leylah Fernandez vs Himeno Sakatsume", "26 Oct 22:00", "Win Match", "Leylah Fernandez", "1/1", 100, "902172", f"{B}/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Himeno_Sakatsume/3?event_id=902172"),
    # Cricket -----------------------------------------------------------------
    ("Cricket", "Global T20 Canada", "Toronto Kings vs Vancouver Guardians T20", "Today 19:00", "Win Match", "Toronto Kings", "6/7", 86, "188845", f"{B}/Cricket/All_Cricket/All_Events/Toronto_Kings_vs_Vancouver_Guardians_T20/7?event_id=188845"),
    ("Cricket", "ODI", "Pakistan vs England One Day Match", "Tomorrow 04:00", "Win Match", "Pakistan", "5/10", 50, "188838", f"{B}/Cricket/All_Cricket/All_Events/Pakistan_vs_England_One_Day_Match/7?event_id=188838"),
    ("Cricket", "CSA T20 Challenge", "North West Dragons vs Northern Cape Heat T20", "Tomorrow 07:00", "Win Match", "North West Dragons", "4/5", 80, "188851", f"{B}/Cricket/All_Cricket/All_Events/North_West_Dragons_vs_Northern_Cape_Heat_T20/7?event_id=188851"),
    ("Cricket", "CSA T20 Challenge", "Tuskers vs Western Province T20", "Tomorrow 07:00", "Win Match", "Western Province", "4/4", 100, "188850", f"{B}/Cricket/All_Cricket/All_Events/Tuskers_vs_Western_Province_T20/7?event_id=188850"),
    ("Cricket", "T20I", "New Zealand vs India 3rd T20 Match", "27 Oct 03:00", "Win Match", "India", "3/3", 100, "188852", f"{B}/Cricket/All_Cricket/All_Events/New_Zealand_vs_India_3rd_T20_Match/7?event_id=188852"),
    ("Cricket", "WODI", "India W vs Zimbabwe W 2nd ODI", "Tomorrow 04:30", "Top Team1 Batsman", "S Mandhana (India W)", "2/2", 100, "188847", f"{B}/Cricket/All_Cricket/All_Events/India_W_vs_Zimbabwe_W_2nd_ODI/7?event_id=188847"),
    ("Cricket", "CSA T20 Challenge", "Eastern Storm vs South Africa Emerging T20", "Tomorrow 07:00", "Win Match", "Eastern Storm", "2/3", 67, "188848", f"{B}/Cricket/All_Cricket/All_Events/Eastern_Storm_vs_South_Africa_Emerging_T20/7?event_id=188848"),
    ("Cricket", "CSA T20 Challenge", "Boland vs Titans T20", "Tomorrow 07:00", "Win Match", "Titans", "2/3", 67, "188849", f"{B}/Cricket/All_Cricket/All_Events/Boland_vs_Titans_T20/7?event_id=188849"),
    ("Cricket", "ODI", "South Africa vs Australia", "31 Oct 04:30", "Draw No Bet", "Australia", "2/2", 100, "188835", f"{B}/Cricket/All_Cricket/All_Events/South_Africa_vs_Australia/7?event_id=188835"),
    ("Cricket", "Outright", "World Cup 2027", "21 Nov 2027 05:00", "Outright Winner", "India", "6/12", 50, "182606", f"{B}/Cricket/All_Cricket/All_Events/World_Cup_2027/7?event_id=182606"),
    ("Cricket", "Outright", "T20 Big Bash 2026-27", "12 Dec 03:15", "Outright Winner", "Adelaide Strikers", "1/2", 50, "187503", f"{B}/Cricket/All_Cricket/All_Events/T20_Big_Bash_2026-27/7?event_id=187503"),
    # Rugby Union -------------------------------------------------------------
    ("Rugby Union", "URC", "Ospreys v Dragons", "Today 14:00", "To Win", "Dragons", "4/8", 50, "609581", f"{B}/Rugby_Union/All_Rugby_Union/All_Events/Ospreys_v_Dragons/9?event_id=609581"),
    ("Rugby Union", "Top 14", "Toulon v Pau", "Today 15:00", "To Win", "Toulon", "4/7", 57, "609555", f"{B}/Rugby_Union/All_Rugby_Union/All_Events/Toulon_v_Pau/9?event_id=609555"),
    ("Rugby Union", None, "USA v Australia A", "Today 19:00", "To Win", "Australia A", "1/2", 50, "609583", f"{B}/Rugby_Union/All_Rugby_Union/All_Events/USA_v_Australia_A/9?event_id=609583"),
    ("Rugby Union", "Premiership", "Harlequins v Saracens", "Tomorrow 11:00", "To Win", "Harlequins", "1/1", 100, "609571", f"{B}/Rugby_Union/All_Rugby_Union/All_Events/Harlequins_v_Saracens/9?event_id=609571"),
    ("Rugby Union", "Top 14", "La Rochelle v Bordeaux", "Tomorrow 16:05", "To Win", "Bordeaux", "1/2", 50, "609554", f"{B}/Rugby_Union/All_Rugby_Union/All_Events/La_Rochelle_v_Bordeaux/9?event_id=609554"),
    ("Rugby Union", "Outright", "Six Nations 2027", "14 Mar 2027 16:00", "Win Tournament", "Ireland", "3/9", 33, "609013", f"{B}/Rugby_Union/All_Rugby_Union/All_Events/Six_Nations_2027/9?event_id=609013"),
    # Volleyball — all rows exposed by the captured current hub ---------------
    ("Volleyball", 'Poland TAURON Liga W', 'Mogilno W vs Chemik Police W', 'Today 14:30', 'Win Match', 'Chemik Police W', '3/3', 100, '37078', f"{B}/Volleyball/All_Volleyball/All_Events/Mogilno_W_vs_Chemik_Police_W/21?event_id=37078"),
    ("Volleyball", 'Brazil Superliga W', 'Mackenzie W vs Osasco W', 'Today 15:00', 'Win Match', 'Mackenzie W', '2/4', 50, '37002', f"{B}/Volleyball/All_Volleyball/All_Events/Mackenzie_W_vs_Osasco_W/21?event_id=37002"),
    ("Volleyball", 'Brazil Superliga W', 'Abel-Moda Brusque W vs Praia Clube W', 'Today 20:00', 'Win Match', 'Abel/Moda Brusque W', '2/3', 67, '37003', f"{B}/Volleyball/All_Volleyball/All_Events/Abel-Moda_Brusque_W_vs_Praia_Clube_W/21?event_id=37003"),
    ("Volleyball", 'Italy SuperLega', 'Trentino vs Cisterna', 'Tomorrow 12:00', 'Win Match', 'Cisterna', '2/2', 100, '36994', f"{B}/Volleyball/All_Volleyball/All_Events/Trentino_vs_Cisterna/21?event_id=36994"),
    ("Volleyball", 'Poland PlusLiga', 'CHKS Chelm vs Resovia Rzeszow', 'Tomorrow 13:00', 'Win Match', 'Resovia Rzeszow', '2/3', 67, '36965', f"{B}/Volleyball/All_Volleyball/All_Events/CHKS_Chelm_vs_Resovia_Rzeszow/21?event_id=36965"),
    ("Volleyball", 'Italy SuperLega', 'Perugia vs Pordenone', 'Tomorrow 13:00', 'Win Match', 'Pordenone', '2/2', 100, '36997', f"{B}/Volleyball/All_Volleyball/All_Events/Perugia_vs_Pordenone/21?event_id=36997"),
    ("Volleyball", None, 'Talmassons W vs Chieri W', 'Today 14:45', 'Win Match', 'Chieri W', '1/1', 100, '37072', f"{B}/Volleyball/All_Volleyball/All_Events/Talmassons_W_vs_Chieri_W/21?event_id=37072"),
    ("Volleyball", None, 'ETV Hamburg W vs Munster W', 'Tomorrow 10:30', 'Set Score', 'Munster W to win 3-2', '1/1', 100, '37059', f"{B}/Volleyball/All_Volleyball/All_Events/ETV_Hamburg_W_vs_Munster_W/21?event_id=37059"),
    ("Volleyball", None, 'Barock Volleys Ludwigsburg vs TV Rottenburg', 'Tomorrow 12:00', 'Set Score', 'TV Rottenburg to win 3-1', '1/1', 100, '37014', f"{B}/Volleyball/All_Volleyball/All_Events/Barock_Volleys_Ludwigsburg_vs_TV_Rottenburg/21?event_id=37014"),
    ("Volleyball", 'Italy SuperLega', 'Civitanova vs Padova', 'Tomorrow 13:00', 'Set Score', 'Civitanova to win 3-1', '1/1', 100, '36995', f"{B}/Volleyball/All_Volleyball/All_Events/Civitanova_vs_Padova/21?event_id=36995"),
    ("Volleyball", 'Italy SuperLega', 'Monza vs Verona', 'Tomorrow 13:00', 'Win Match', 'Monza', '1/1', 100, '36996', f"{B}/Volleyball/All_Volleyball/All_Events/Monza_vs_Verona/21?event_id=36996"),
    # Handball — all upcoming rows exposed by the captured hub chunks --------
    ("Handball", 'EHF Champions League', 'SC Magdeburg vs HC Kriens Luzern', '28 Oct 15:45', "Money Line", 'Tie', '3/4', 75, '12136', f"{B}/Handball/All_Handball/All_Events/SC_Magdeburg_vs_HC_Kriens_Luzern/20?event_id=12136"),
    ("Handball", 'Spain ASOBAL', 'BM Granollers vs Angel Ximenez Puente Genil', 'Tomorrow 07:30', "Money Line", 'BM Granollers', '2/5', 40, '12102', f"{B}/Handball/All_Handball/All_Events/BM_Granollers_vs_Angel_Ximenez_Puente_Genil/20?event_id=12102"),
    ("Handball", 'Germany HBL', 'Rhein Neckar Lowen vs SC Magdeburg', 'Tomorrow 10:00', "Money Line", 'Rhein Neckar Lowen', '2/3', 67, '12092', f"{B}/Handball/All_Handball/All_Events/Rhein_Neckar_Lowen_vs_SC_Magdeburg/20?event_id=12092"),
    ("Handball", 'France StarLigue', 'Saint Raphael vs PSG Handball', 'Tomorrow 11:00', "Money Line", 'PSG Handball', '2/3', 67, '12084', f"{B}/Handball/All_Handball/All_Events/Saint_Raphael_vs_PSG_Handball/20?event_id=12084"),
    ("Handball", 'Women', 'Luxembourg W vs Great Britain W', 'Tomorrow 11:00', "Money Line", 'Great Britain (W)', '2/2', 100, '12126', f"{B}/Handball/All_Handball/All_Events/Luxembourg_W_vs_Great_Britain_W/20?event_id=12126"),
    ("Handball", 'Spain ASOBAL', 'BM Torrelavega vs BM Proin', 'Tomorrow 13:00', "Money Line", 'BM Proin', '2/3', 67, '12105', f"{B}/Handball/All_Handball/All_Events/BM_Torrelavega_vs_BM_Proin/20?event_id=12105"),
    ("Handball", 'EHF Champions League', 'HC Vardar vs MT Melsungen', '28 Oct 13:45', "Money Line", 'HC Vardar', '2/3', 67, '12130', f"{B}/Handball/All_Handball/All_Events/HC_Vardar_vs_MT_Melsungen/20?event_id=12130"),
    ("Handball", 'EHF Champions League', 'KS Kielce vs Kolstad', '28 Oct 15:45', "Money Line", 'Tie', '2/3', 67, '12132', f"{B}/Handball/All_Handball/All_Events/KS_Kielce_vs_Kolstad/20?event_id=12132"),
    ("Handball", 'EHF Champions League', 'GOG vs Sporting CP', '29 Oct 13:45', "Money Line", 'GOG', '2/2', 100, '12129', f"{B}/Handball/All_Handball/All_Events/GOG_vs_Sporting_CP/20?event_id=12129"),
    ("Handball", None, 'Fuchse Berlin vs RK Partizan', '29 Oct 13:45', "Money Line", 'RK Partizan', '2/4', 50, '12128', f"{B}/Handball/All_Handball/All_Events/Fuchse_Berlin_vs_RK_Partizan/20?event_id=12128"),
    ("Handball", None, 'CBM Sporting Alicante vs Ademar Leon', 'Tomorrow 07:00', "Money Line", 'Ademar Leon', '1/2', 50, '12106', f"{B}/Handball/All_Handball/All_Events/CBM_Sporting_Alicante_vs_Ademar_Leon/20?event_id=12106"),
    ("Handball", None, 'Ystads IF HF vs Hammarby IF HF', 'Tomorrow 09:00', "Money Line", 'Hammarby IF HF', '1/2', 50, '12152', f"{B}/Handball/All_Handball/All_Events/Ystads_IF_HF_vs_Hammarby_IF_HF/20?event_id=12152"),
    ("Handball", 'Women', 'Lithuania W vs Belgium W', 'Tomorrow 10:00', "Money Line", 'Lithuania (W)', '1/3', 33, '12125', f"{B}/Handball/All_Handball/All_Events/Lithuania_W_vs_Belgium_W/20?event_id=12125"),
    ("Handball", None, 'Skanderborg Handbold vs Team Tvis Holstebro', 'Tomorrow 11:00', "Money Line", 'Team Tvis Holstebro', '1/2', 50, '12075', f"{B}/Handball/All_Handball/All_Events/Skanderborg_Handbold_vs_Team_Tvis_Holstebro/20?event_id=12075"),
    ("Handball", None, 'HIF Karlskrona vs IFK Kristianstad', 'Tomorrow 11:00', "Money Line", 'HIF Karlskrona', '1/2', 50, '12148', f"{B}/Handball/All_Handball/All_Events/HIF_Karlskrona_vs_IFK_Kristianstad/20?event_id=12148"),
    ("Handball", None, 'Amo HK vs HK Malmo', 'Tomorrow 11:15', "Money Line", 'HK Malmo', '1/2', 50, '12144', f"{B}/Handball/All_Handball/All_Events/Amo_HK_vs_HK_Malmo/20?event_id=12144"),
    ("Handball", 'Germany HBL', 'Fuchse Berlin vs HSG Wetzlar', 'Tomorrow 11:30', "Money Line", 'Fuchse Berlin', '1/3', 33, '12089', f"{B}/Handball/All_Handball/All_Events/Fuchse_Berlin_vs_HSG_Wetzlar/20?event_id=12089"),
    ("Handball", 'Germany HBL', 'Bergischer HC vs HC Hamburg', 'Tomorrow 11:30', "Money Line", 'Tie', '1/1', 100, '12087', f"{B}/Handball/All_Handball/All_Events/Bergischer_HC_vs_HC_Hamburg/20?event_id=12087"),
    ("Handball", None, 'Skanela IF vs IK Savehof', 'Tomorrow 11:30', "Money Line", 'Skanela IF', '1/2', 50, '12151', f"{B}/Handball/All_Handball/All_Events/Skanela_IF_vs_IK_Savehof/20?event_id=12151"),
    ("Handball", 'France StarLigue', 'Montpellier vs Saran Loiret', 'Tomorrow 12:00', "Money Line", 'Tie', '1/1', 100, '12081', f"{B}/Handball/All_Handball/All_Events/Montpellier_vs_Saran_Loiret/20?event_id=12081"),
    # Darts — current hub after the first two Saturday evening matches began ---
    ("Darts", None, "Nathan Aspinall vs Luke Littler", "Today 15:15", "Win Match 2-way", "Luke Littler", "15/21", 71, "32397", f"{B}/Darts/All_Darts/All_Events/Nathan_Aspinall_vs_Luke_Littler/15?event_id=32397"),
    ("Darts", None, "Jonny Clayton vs Josh Rock", "Today 16:15", "Win Match 2-way", "Jonny Clayton", "15/21", 71, "32400", f"{B}/Darts/All_Darts/All_Events/Jonny_Clayton_vs_Josh_Rock/15?event_id=32400"),
    ("Darts", None, "Gerwyn Price vs Stephen Bunting", "Tomorrow 07:00", "Win Match 2-way", "Gerwyn Price", "2/2", 100, "32407", f"{B}/Darts/All_Darts/All_Events/Gerwyn_Price_vs_Stephen_Bunting/15?event_id=32407"),
    ("Darts", "Outright", "PDC World Championship 2027", "03 Jan 2027 12:00", "Win Tournament", "Luke Littler", "22/36", 61, "26023", f"{B}/Darts/All_Darts/All_Events/PDC_World_Championship_2027/15?event_id=26023"),
    ("Darts", "Outright", "European Championship", "Tomorrow 14:00", "Win Tournament", "Luke Littler", "9/19", 47, "32338", f"{B}/Darts/All_Darts/All_Events/European_Championship/15?event_id=32338"),
    # Snooker -----------------------------------------------------------------
    ("Snooker", "Northern Ireland Open", "Mark Williams v Jak Jones", "Today 14:05", "Win Match", "Jak Jones", "15/26", 58, "9952", f"{B}/Snooker/All_Snooker/All_Events/Mark_Williams_v_Jak_Jones/8?event_id=9952"),
    # Baseball ----------------------------------------------------------------
    ("Baseball", "MLB World Series", "TB Rays @ MIL Brewers", "Today 20:00", "Money Line", "TB Rays", "9/17", 53, "160792", f"{B}/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160792"),
    # Gaelic Sports -----------------------------------------------------------
    ("Gaelic Sports", "Galway SFC", "Moycullen v Salthill-Knocknacarra", "Tomorrow 12:00", "Handicap", "SalthillKnocknacarra +3.50", "23/42", 55, "3532", f"{B}/Gaelic_Football/All_Gaelic_Football/All_Events/Moycullen_v_Salthill-Knocknacarra/25?event_id=3532"),
    ("Gaelic Sports", "Cork SFC", "St Finbarrs v Nemo Rangers", "Tomorrow 12:00", "Handicap", "Nemo Rangers +1.50", "20/25", 80, "3530", f"{B}/Gaelic_Football/All_Gaelic_Football/All_Events/St_Finbarrs_v_Nemo_Rangers/25?event_id=3530"),
    ("Gaelic Sports", "Cork SFC", "Kanturk v Eire Og Cor", "01 Nov 09:00", "Handicap", "Eire Og Cor +0.50", "4/4", 100, "3531", f"{B}/Gaelic_Football/All_Gaelic_Football/All_Events/Kanturk_v_Eire_Og_Cor/25?event_id=3531"),
    ("Gaelic Sports", "Limerick SFC", "Fr Caseys v Kildimo Pallaskenry", "01 Nov 10:30", "To Win", "Fr Caseys", "3/4", 75, "3537", f"{B}/Gaelic_Football/All_Gaelic_Football/All_Events/Fr_Caseys_v_Kildimo_Pallaskenry/25?event_id=3537"),
    # Greyhounds --------------------------------------------------------------
    ("Greyhounds", "Monmore", "8:54 Monmore", "Today 15:54", "Daily Races", "Crossfield Jess", "2/3", 67, "690013", f"{B}/Greyhounds/All_Greyhounds/All_Events/8:54_Monmore/28?event_id=690013"),
    ("Greyhounds", "Monmore", "9:14 Monmore", "Today 16:14", "Daily Races", "Skylars Vision", "2/2", 100, "690017", f"{B}/Greyhounds/All_Greyhounds/All_Events/9:14_Monmore/28?event_id=690017"),
    ("Greyhounds", "Doncaster", "7:58 Doncaster", "Today 14:58", "Daily Races", "Lady Gambet", "2/2", 100, "689890", f"{B}/Greyhounds/All_Greyhounds/All_Events/7:58_Doncaster/28?event_id=689890"),
    ("Greyhounds", "Dunstall Park", "9:18 Dunstall Park", "Today 16:18", "Daily Races", "Avarua Lake", "2/4", 50, "689892", f"{B}/Greyhounds/All_Greyhounds/All_Events/9:18_Dunstall_Park/28?event_id=689892"),
    ("Greyhounds", "Dunstall Park", "10:14 Dunstall Park", "Today 17:14", "Daily Races", "Greenwell Gypsy", "2/3", 67, "690035", f"{B}/Greyhounds/All_Greyhounds/All_Events/10:14_Dunstall_Park/28?event_id=690035"),
    ("Greyhounds", "Central Park", "6:10 Central Park", "Today 13:10", "Daily Races", "Barnfield Story", "1/3", 33, "689951", f"{B}/Greyhounds/All_Greyhounds/All_Events/6:10_Central_Park/28?event_id=689951"),
    ("Greyhounds", "Doncaster", "6:11 Doncaster", "Today 13:11", "Daily Races", "Charming Delight", "1/2", 50, "689953", f"{B}/Greyhounds/All_Greyhounds/All_Events/6:11_Doncaster/28?event_id=689953"),
    ("Greyhounds", "Monmore", "6:14 Monmore", "Today 13:14", "Daily Races", "Longacres Boycie", "2/2", 100, "689954", f"{B}/Greyhounds/All_Greyhounds/All_Events/6:14_Monmore/28?event_id=689954"),
    ("Greyhounds", "Doncaster", "6:29 Doncaster", "Today 13:29", "Daily Races", "Jacktavern Beaut", "2/2", 100, "689956", f"{B}/Greyhounds/All_Greyhounds/All_Events/6:29_Doncaster/28?event_id=689956"),
    # Motor Racing ------------------------------------------------------------
    ("Motor Racing", "Formula 1", "USA Grand Prix", "Tomorrow 16:00", "Win Race", "Max Verstappen", "18/55", 33, "913", f"{B}/Motor_Racing/All_Motor_Racing/All_Events/USA_Grand_Prix/14?event_id=913"),
    # Rugby League (no match events listed at capture) -------------------------
    ("Rugby League", "Outright", "State of Origin 2027", "27 May 2027 06:00", "Win Tournament", "New South Wales", "9/12", 75, "2695857", f"{B}/Rugby_League/All_Rugby_League/All_Events/State_of_Origin_2027/10?event_id=2695857"),
    ("Rugby League", "Outright", "Super League 2027", "02 Oct 2027 13:00", "Grand Final Winner", "Hull KR", "1/3", 33, "2801554", f"{B}/Rugby_League/All_Rugby_League/All_Events/Super_League_2027/10?event_id=2801554"),
    ("Rugby League", "Outright", "NRL 2027", "03 Oct 2027 04:30", "Grand Final Winner", "Penrith Panthers", "1/2", 50, "2801600", f"{B}/Rugby_League/All_Rugby_League/All_Events/NRL_2027/10?event_id=2801600"),
]

# Officially sourced fixtures (read from the league feeds named in `fixture_source`).
NHLE_SCORE = "https://api-web.nhle.com/v1/score/2026-10-24"
NHLE_SCHED = "https://api-web.nhle.com/v1/schedule/2026-10-24"
MLB_SCHED = ("https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24"
             "&hydrate=probablePitcher,team")
MLB_MIL = "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings&season=2026"
MLB_STAND = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"

FIXTURES = [
    dict(id="nhl-2026020168", sport="Ice Hockey", competition="NHL", home="Philadelphia Flyers",
         away="Anaheim Ducks", venue="Xfinity Mobile Arena", start_utc="2026-10-24T17:00:00Z",
         start_source="NHL schedule feed startTimeUTC", home_record="3-6-3", away_record="4-6-0",
         market_decimal_home=1.84, market_decimal_away=2.01, market_source="NHL schedule feed odds array (providerId 3, Tipsport)",
         olbg_event_id="199999", olbg_listed_selection="ANA Ducks", olbg_market="Money Line",
         fact_home="3-6-3 in 12 games (9 points); Michael Michkov leads the club with 6 goals",
         fact_away="4-6-0 in 10 games (8 points); Beckett Sennecke leads with 5 goals, Leo Carlsson 9 assists",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020169", sport="Ice Hockey", competition="NHL", home="New Jersey Devils",
         away="Los Angeles Kings", venue="Prudential Center", start_utc="2026-10-24T19:30:00Z",
         start_source="NHL schedule feed startTimeUTC", home_record="6-4-0", away_record="2-4-2",
         market_decimal_home=1.53, market_decimal_away=2.55, market_source="NHL schedule feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200000", olbg_listed_selection="NJ Devils", olbg_market="Money Line",
         fact_home="6-4-0 in 10 games (12 points); Jack Hughes has 8 assists, Arseny Gritsyuk 5 goals, Jake Allen 4 wins",
         fact_away="2-4-2 in 8 games (6 points); Artemi Panarin has 6 goals, Brandt Clarke 5 assists",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020170", sport="Ice Hockey", competition="NHL", home="Boston Bruins",
         away="San Jose Sharks", venue="TD Garden", start_utc="2026-10-24T23:00:00Z",
         start_source="NHL schedule feed startTimeUTC", home_record="8-2-1", away_record="6-4-1",
         market_decimal_home=1.54, market_decimal_away=2.52, market_source="NHL schedule feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200007", olbg_listed_selection="BOS Bruins", olbg_market="Money Line",
         fact_home="8-2-1 in 11 games; David Pastrnak has 6 goals and 10 assists, Jeremy Swayman 6 wins",
         fact_away="6-4-1 in 11 games (13 points); Macklin Celebrini 5 goals and 9 assists",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020171", sport="Ice Hockey", competition="NHL", home="Ottawa Senators",
         away="New York Rangers", venue="Canadian Tire Centre", start_utc="2026-10-24T23:00:00Z",
         start_source="NHL schedule feed startTimeUTC", home_record="7-4-0", away_record="7-4-1",
         market_decimal_home=1.80, market_decimal_away=2.05, market_source="NHL schedule feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200008", olbg_listed_selection="NY Rangers", olbg_market="Money Line",
         fact_home="7-4-0 in 11 games (14 points); Tim Stutzle 7 goals and 8 assists, Linus Ullmark 7 wins",
         fact_away="7-4-1 in 12 games (15 points); Alexis Lafreniere 8 goals, Adam Fox 14 assists",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020172", sport="Ice Hockey", competition="NHL", home="Pittsburgh Penguins",
         away="Nashville Predators", venue="PPG Paints Arena", start_utc="2026-10-24T23:00:00Z",
         start_source="NHL schedule feed startTimeUTC", home_record="4-6-1", away_record="3-3-3",
         market_decimal_home=1.82, market_decimal_away=2.03, market_source="NHL schedule feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200006", olbg_listed_selection="PIT Penguins", olbg_market="Money Line",
         fact_home="4-6-1 in 11 games (9 points); Evgeni Malkin 6 goals, Erik Karlsson 10 assists, Arturs Silovs 4 wins",
         fact_away="3-3-3 in 9 games (9 points); Ryan O'Reilly 4 goals, Roman Josi 8 assists",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="nhl-2026020173", sport="Ice Hockey", competition="NHL", home="Washington Capitals",
         away="Buffalo Sabres", venue="Capital One Arena", start_utc="2026-10-24T23:00:00Z",
         start_source="NHL schedule feed startTimeUTC", home_record="5-4-0", away_record="4-4-2",
         market_decimal_home=1.84, market_decimal_away=2.01, market_source="NHL schedule feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200003", olbg_listed_selection="BUF Sabres", olbg_market="Money Line",
         fact_home="5-4-0 in 9 games (10 points); Alex Tuch 5 goals, Dylan Strome 5 assists, Logan Thompson 4 wins",
         fact_away="4-4-2 in 10 games (10 points); Tage Thompson 5 goals, Zach Benson 6 assists",
         source_url=NHLE_SCHED, source_label="NHL schedule feed"),
    dict(id="nhl-2026020174", sport="Ice Hockey", competition="NHL", home="Columbus Blue Jackets",
         away="Vegas Golden Knights", venue="Nationwide Arena", start_utc="2026-10-24T23:00:00Z",
         start_source="NHL schedule feed startTimeUTC", home_record="3-5-0", away_record="8-4-0",
         market_decimal_home=2.11, market_decimal_away=1.76, market_source="NHL schedule feed odds array (providerId 3, Tipsport)",
         olbg_event_id="200001", olbg_listed_selection="VGS Golden Knights", olbg_market="Money Line",
         fact_home="3-5-0 in 8 games; Kent Johnson has 4 goals, Zach Werenski 6 assists and Jet Greaves 2 wins",
         fact_away="8-4-0 in 12 games; Mark Stone has 8 goals, Jack Eichel 13 assists and Carter Hart 4 wins",
         source_url=NHLE_SCORE, source_label="NHL scores feed"),
    dict(id="mlb-849802", sport="Baseball", competition="MLB World Series", home="Milwaukee Brewers",
         away="Tampa Bay Rays", venue="American Family Field", start_utc="2026-10-25T00:00:00Z",
         start_source="MLB Stats API gameDate", home_record="103-59", away_record="98-64",
         market_decimal_home=None, market_decimal_away=None, market_source=None,
         runs=dict(home_scored=832, home_allowed=618, away_scored=736, away_allowed=650, games=162),
         olbg_event_id="160792", olbg_listed_selection="TB Rays", olbg_market="Money Line",
         fact_home="103-59 (.636) with 832 runs scored and 618 allowed, 55-26 at home, 8-2 over the last ten; Logan Henderson is the probable starter",
         fact_away="98-64 (.605) with 736 runs scored and 650 allowed, 43-38 on the road, 5-5 over the last ten; Drew Rasmussen is the probable starter",
         source_url=MLB_SCHED, source_label="MLB Stats API schedule (probable pitchers)"),
]

expand_fixtures(FIXTURES)

SPORT_STATUS = {
    "Golf": dict(listings=0, verified=0, note="The Golf hub returned \"No tips found.\" at 17:16 UTC, so OLBG listed no golf event to attach a pick to."),
    "Rugby League": dict(listings=3, verified=0, note="Only 2027 outright futures were listed; no Rugby League match event was listed on the hub at capture."),
    "Greyhounds": dict(listings=9, verified=0, note="Race-by-race dog form is not published by GBGB in a form reachable from this environment, so no greyhound pick is published."),
    "Basketball": dict(listings=10, verified=8, note="All eight NBA fixtures are confirmed on the official games page. Availability is limited to the 1:30 PM ET injury report; teams marked NOT YET SUBMITTED remain flagged."),
}

payload = dict(
    capture_utc=CAPTURE_UTC, capture_end_utc=CAPTURE_END_UTC, session=SESSION,
    hubs={s: dict(url=u, sport_id=i) for s, (u, i) in HUB.items()},
    listings=[dict(sport=s, competition=c, event=e, displayed_time=t, market=m, selection=sel,
                   tips=ti, pct=p, event_id=eid, url=u) for (s, c, e, t, m, sel, ti, p, eid, u) in OLBG],
    fixtures=FIXTURES, sport_status=SPORT_STATUS,
    notes=[
        "OLBG displays one most-tipped selection per listed event, with a tip count and a percentage of tips on that market.",
        "Displayed times are OLBG's own strings. They are not UTC and are stored verbatim; official start times come from the league feed.",
        "OLBG publishes no odds on its hub pages, so every price on this site is originated here, not copied from OLBG.",
    ],
)

(OUT / "olbg_listings.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"today_seed: {len(OLBG)} OLBG listing rows, {len(FIXTURES)} officially sourced fixtures")
