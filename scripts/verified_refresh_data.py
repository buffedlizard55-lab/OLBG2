#!/usr/bin/env python3
"""2026-10-22 source register and active-inventory overlay for /verified/.

The baseline seed remains useful for officially captured rating tables.  This
module replaces its stale event inventory, corrects taxonomy, and records the
provenance of every active row.  Relative OLBG dates are labels, not UTC facts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DATE = "2026-10-22"

HUBS = {
    "ice-hockey": "https://www.olbg.com/betting-tips/Ice_Hockey/13",
    "basketball": "https://www.olbg.com/betting-tips/Basketball/4",
    "rugby-union": "https://www.olbg.com/betting-tips/Rugby_Union/9",
    "handball": "https://www.olbg.com/betting-tips/Handball/20",
    "darts": "https://www.olbg.com/betting-tips/Darts/15",
    "tennis": "https://www.olbg.com/betting-tips/Tennis/3",
    "snooker": "https://www.olbg.com/betting-tips/Snooker/8",
    "baseball": "https://www.olbg.com/betting-tips/Baseball/12",
    "motor-racing": "https://www.olbg.com/betting-tips/Motor_Racing/14",
    "volleyball": "https://www.olbg.com/betting-tips/Volleyball/21",
    "cricket": "https://www.olbg.com/betting-tips/Cricket/7",
    "golf": "https://www.olbg.com/betting-tips/Golf/5",
    "rugby-league": "https://www.olbg.com/betting-tips/Rugby_League/10",
    "gaelic-football": "https://www.olbg.com/betting-tips/Gaelic_Football/25",
    "greyhounds": "https://www.olbg.com/betting-tips/Greyhounds/28",
    "aussie-rules": "https://www.olbg.com/betting-tips/Aussie_Rules/22",
    "esports": "https://www.olbg.com/betting-tips/eSports/23",
}

NHL_FIXTURE_IDS = [f"nhl-{n}" for n in range(2026020154, 2026020166)]

# Official NBA game pages reviewed individually.  tip_et is the official ET
# display; no conversion is inferred.  Only four have visible OLBG cards.
NBA_FIXTURES = [
    {"date": "2026-10-22", "tip_et": "19:00", "away": "CLE", "home": "PHI", "game_id": "0022600006", "venue": "Xfinity Mobile Arena, Philadelphia", "olbg_event_id": "534845"},
    {"date": "2026-10-22", "tip_et": "21:30", "away": "DEN", "home": "OKC", "game_id": "0022600007", "venue": "Paycom Center, Oklahoma City", "olbg_event_id": "534843"},
    {"date": "2026-10-23", "tip_et": "16:00", "away": "CHI", "home": "MIL", "game_id": "0022600099", "venue": "Fiserv Forum, Milwaukee"},
    {"date": "2026-10-23", "tip_et": "19:00", "away": "NYK", "home": "BOS", "game_id": "0022600008", "venue": "TD Garden, Boston", "olbg_event_id": "534842"},
    {"date": "2026-10-23", "tip_et": "19:00", "away": "ATL", "home": "CHA", "game_id": "0022600094", "venue": "Spectrum Center, Charlotte"},
    {"date": "2026-10-23", "tip_et": "19:00", "away": "DAL", "home": "IND", "game_id": "0022600095", "venue": "Gainbridge Fieldhouse, Indianapolis"},
    {"date": "2026-10-23", "tip_et": "19:00", "away": "MIN", "home": "ORL", "game_id": "0022600096", "venue": "Kia Center, Orlando"},
    {"date": "2026-10-23", "tip_et": "19:00", "away": "TOR", "home": "WAS", "game_id": "0022600097", "venue": "Capital One Arena, Washington"},
    {"date": "2026-10-23", "tip_et": "20:00", "away": "DET", "home": "MIA", "game_id": "0022600098", "venue": "Kaseya Center, Miami"},
    {"date": "2026-10-23", "tip_et": "21:30", "away": "NOP", "home": "UTA", "game_id": "0022600100", "venue": "Delta Center, Salt Lake City"},
    {"date": "2026-10-23", "tip_et": "21:30", "away": "HOU", "home": "SAS", "game_id": "0022600009", "venue": "Moody Center, Austin (neutral site)", "neutral": True, "olbg_event_id": "534841"},
    {"date": "2026-10-23", "tip_et": "22:00", "away": "MEM", "home": "GSW", "game_id": "0022600101", "venue": "Chase Center, San Francisco"},
    {"date": "2026-10-23", "tip_et": "22:00", "away": "LAC", "home": "LAL", "game_id": "0022600102", "venue": "Crypto.com Arena, Los Angeles"},
    {"date": "2026-10-23", "tip_et": "22:00", "away": "POR", "home": "SAC", "game_id": "0022600103", "venue": "Golden 1 Center, Sacramento"},
]

EUROLEAGUE_ACTIVE_IDS = {
    "el-E2026-64", "el-E2026-65", "el-E2026-62", "el-E2026-67",
    "el-E2026-63", "el-E2026-66", "el-E2026-68", "el-E2026-70", "el-E2026-69",
}
EUROLEAGUE_OLBG_IDS = {
    "el-E2026-64": "535918", "el-E2026-62": "535921",
    "el-E2026-67": "535923", "el-E2026-68": "535928",
}

TOP14_OLBG_IDS = {"top14-11867": "609567", "top14-11861": "609564", "top14-11864": "609554"}
PROD2_OLBG_IDS = {
    "prod2-12068": "609556", "prod2-12066": "609560", "prod2-12069": "609557",
    "prod2-12063": "609558", "prod2-12065": "609563", "prod2-12070": "609559",
    "prod2-12067": "609561", "prod2-12064": "609562",
}
URC_OLBG_IDS = {"urc-292609": "609577", "urc-292611": "609576", "urc-292614": "609578", "urc-292612": "609580"}
EHF_ACTIVE_IDS = {
    "ehfcl-202711020101041", "ehfcl-202711020101049", "ehfcl-202711020101064",
    "ehfcl-202711020101043", "ehfcl-202711020101019",
}
EHF_OLBG_IDS = {
    "ehfcl-202711020101041": "12054", "ehfcl-202711020101049": "12046",
    "ehfcl-202711020101064": "12048", "ehfcl-202711020101043": "12051",
    "ehfcl-202711020101019": "12049",
}

# SweHockey official table, last update 2026-10-21 18:30.  W/T/L are the
# official table's notation; the model uses GP/GF/GA only.
SHL_TEAMS = {
    "FBK": {"name": "Färjestad BK", "gp": 10, "w": 8, "t": 2, "l": 0, "gf": 40, "ga": 11, "points": 27},
    "FHC": {"name": "Frölunda HC", "gp": 11, "w": 7, "t": 2, "l": 2, "gf": 38, "ga": 24, "points": 25},
    "SKE": {"name": "Skellefteå AIK", "gp": 10, "w": 5, "t": 3, "l": 2, "gf": 32, "ga": 25, "points": 19},
    "BJO": {"name": "IF Björklöven", "gp": 10, "w": 5, "t": 1, "l": 4, "gf": 23, "ga": 25, "points": 17},
    "BIF": {"name": "Brynäs IF", "gp": 10, "w": 4, "t": 1, "l": 5, "gf": 28, "ga": 23, "points": 14},
    "RBK": {"name": "Rögle BK", "gp": 10, "w": 4, "t": 1, "l": 5, "gf": 23, "ga": 21, "points": 14},
    "MIF": {"name": "IF Malmö Redhawks", "gp": 9, "w": 3, "t": 4, "l": 2, "gf": 26, "ga": 25, "points": 14},
    "LHF": {"name": "Luleå HF", "gp": 10, "w": 4, "t": 2, "l": 4, "gf": 26, "ga": 30, "points": 14},
    "OHK": {"name": "Örebro HK", "gp": 10, "w": 4, "t": 2, "l": 4, "gf": 20, "ga": 29, "points": 14},
    "TIK": {"name": "Timrå IK", "gp": 10, "w": 2, "t": 3, "l": 5, "gf": 20, "ga": 23, "points": 12},
    "VLH": {"name": "Växjö Lakers HC", "gp": 10, "w": 3, "t": 2, "l": 5, "gf": 29, "ga": 34, "points": 12},
    "DIF": {"name": "Djurgårdens IF", "gp": 11, "w": 2, "t": 4, "l": 5, "gf": 23, "ga": 33, "points": 12},
    "HV": {"name": "HV 71", "gp": 11, "w": 1, "t": 5, "l": 5, "gf": 29, "ga": 39, "points": 10},
    "LHC": {"name": "Linköping HC", "gp": 10, "w": 2, "t": 2, "l": 6, "gf": 17, "ga": 32, "points": 9},
}
SHL_FIXTURES = [
    {"id": "shl-20261022-bjo-mif", "home": "BJO", "away": "MIF", "venue": "Visionite Arena"},
    {"id": "shl-20261022-rbk-fhc", "home": "RBK", "away": "FHC", "venue": "Catena Arena"},
    {"id": "shl-20261022-ske-dif", "home": "SKE", "away": "DIF", "venue": "Skellefteå Kraft Arena", "olbg_event_id": "199905"},
    {"id": "shl-20261022-tik-fbk", "home": "TIK", "away": "FBK", "venue": "SCA Arena", "olbg_event_id": "199901"},
    {"id": "shl-20261022-vlh-lhf", "home": "VLH", "away": "LHF", "venue": "Vida Arena"},
    {"id": "shl-20261022-ohk-bif", "home": "OHK", "away": "BIF", "venue": "Behrn Arena", "olbg_event_id": "199900"},
]
LIIGA_TEAMS = {
    "JYP": {"name": "JYP Jyväskylä", "gp": 12, "w": 7, "t": 2, "l": 3, "gf": 37, "ga": 32, "points": 24},
    "HPK": {"name": "HPK Hämeenlinna", "gp": 14, "w": 5, "t": 3, "l": 6, "gf": 32, "ga": 38, "points": 21},
}
LIIGA_FIXTURE = {
    "id": "liiga-20261022-jyp-hpk", "date": "2026-10-22", "time": "2026-10-22 18:30 EEST",
    "home": "JYP", "away": "HPK", "venue": None, "olbg_event_id": "199912",
    "url": "https://www.jypliiga.fi/ottelu/jyp-hpk-14/",
}


def provenance(event_id: str | None, sport: str, official_status: str = "fixture and model inputs checked against official sources", time_basis: str = "official") -> dict:
    discovered = bool(event_id)
    return {
        "discovery": "OLBG-discovered" if discovered else "official supplementary",
        "official_status": official_status,
        "time_basis": time_basis,
        "olbg_event_id": event_id,
        "source_scope": (
            "Static rendered OLBG card captured 2026-10-22; hidden Load More results not claimed"
            if discovered else
            "Official schedule supplement; no current OLBG card is claimed"
        ),
    }


def unlined(
    row_id: str, sport: str, competition: str, home: str, away: str,
    official_source: str, official_url: str, blank_reason: str,
    olbg_event_id: str, time_label: str, *, date: str | None = None,
    venue: str | None = None, official_status: str = "official confirmation pending",
    time_basis: str = "OLBG card label; timezone and date semantics not independently confirmed",
) -> dict:
    return {
        "id": row_id, "sport": sport, "competition": competition,
        "date": date, "time": time_label, "home": home, "away": away,
        "venue": venue, "official_source": official_source, "official_url": official_url,
        "olbg_url": HUBS[sport], "olbg_event_id": olbg_event_id,
        "blank_reason": blank_reason,
        "provenance": {
            "discovery": "OLBG-discovered", "official_status": official_status,
            "time_basis": time_basis, "olbg_event_id": olbg_event_id,
            "source_scope": "Static rendered OLBG card captured 2026-10-22; hidden Load More results not claimed",
        },
    }


def build_unlined() -> list[dict]:
    rows: list[dict] = []
    # Basketball: current domestic cards without a verified current rating feed.
    rows += [
        unlined("kbl-536021", "basketball", "Korea KBL — OLBG card", "Mobis", "Changwon", "Korean Basketball League", "https://www.kbl.or.kr/", "Current official club ratings and the precise fixture page were not independently captured; no price originated.", "536021", "OLBG card label: Tomorrow 06:00"),
        unlined("nbb-536019", "basketball", "Brazil NBB — OLBG card", "Fortaleza", "Pinheiros", "Liga Nacional de Basquete", "https://lnb.com.br/", "Current official club ratings and the precise fixture page were not independently captured; no price originated.", "536019", "OLBG card label: Tomorrow 18:30"),
    ]
    # Rugby Union outright: preserve the raw label while exposing the official mismatch.
    rows.append(unlined(
        "six-nations-609013", "rugby-union", "2027 Guinness Men's Six Nations — Outright",
        "Six-Team Championship Field", "Outright", "Six Nations Rugby official schedule",
        "https://www.sixnationsrugby.com/en/m6n/news/mens-six-nations-2027-fixtures-and-schedule-confirmed",
        "No current official championship-strength model was captured. OLBG displays 14 Mar 2027 20:00, while the official schedule concludes 13 Mar; the label is retained and flagged.",
        "609013", "OLBG card label: 14 Mar 2027 20:00; official final: Ireland v France, 13 Mar 2027 20:10 GMT",
        date="2027-03-13", official_status="official tournament schedule confirmed; OLBG date label conflicts",
        time_basis="Official championship end date used in date field; raw OLBG label preserved separately",
    ))

    # Handball's 15 non-EHF cards.  Generic official review pages are not
    # represented as fixture confirmations.
    handball = [
        ("hb-12109", "Bulgaria W", "Italy W", "Tomorrow 12:00", "International Handball Federation", "https://www.ihf.info/"),
        ("hb-12094", "TVB Stuttgart", "SG BBM Bietigheim", "Tomorrow 13:00", "Handball Bundesliga", "https://www.dkb-handball-bundesliga.de/"),
        ("hb-12073", "SonderjyskE", "Nordsjaelland", "Tomorrow 13:30", "Dansk Håndbold Forbund", "https://dhf.dk/"),
        ("hb-12074", "KIF Kolding", "Fredericia", "Tomorrow 14:00", "Dansk Håndbold Forbund", "https://dhf.dk/"),
        ("hb-12116", "Onnereds", "Ystads", "Tomorrow 13:00", "Svensk Handboll", "https://www.svenskhandboll.se/"),
        ("hb-12100", "Granollers", "Ciudad Encantada", "Tomorrow 14:00", "Real Federación Española de Balonmano", "https://www.rfesbm.es/"),
        ("hb-12083", "Pays dAix", "Toulouse", "23 Oct 14:00", "Fédération Française de Handball", "https://www.ffhandball.fr/"),
        ("hb-12110", "Estonia W", "Kosovo W", "23 Oct 14:00", "International Handball Federation", "https://www.ihf.info/"),
        ("hb-12088", "Goppingen", "Eisenach", "23 Oct 14:00", "Handball Bundesliga", "https://www.dkb-handball-bundesliga.de/"),
        ("hb-12080", "Limoges 87", "Dunkerque", "23 Oct 14:00", "Fédération Française de Handball", "https://www.ffhandball.fr/"),
        ("hb-12085", "Selestat", "Caen", "23 Oct 14:30", "Fédération Française de Handball", "https://www.ffhandball.fr/"),
        ("hb-12076", "Skive", "Aalborg", "24 Oct 09:00", "Dansk Håndbold Forbund", "https://dhf.dk/"),
        ("hb-12107", "Villa de Aranda", "Puerto Sagunto", "24 Oct 13:00", "Real Federación Española de Balonmano", "https://www.rfesbm.es/"),
        ("hb-12117", "Skanela", "Karlskrona", "Tomorrow 12:30", "Svensk Handboll", "https://www.svenskhandboll.se/"),
        ("hb-12101", "Bidasoa Irun", "Caserio Ciudad Real", "23 Oct 13:00", "Real Federación Española de Balonmano", "https://www.rfesbm.es/"),
    ]
    for eid, home, away, label, source, url in handball:
        rows.append(unlined(eid, "handball", "Domestic / International Handball — OLBG card", home, away, source, url, "The OLBG pairing is catalogued, but the precise official fixture and comparable current ratings were not independently confirmed.", eid.split("-")[1], f"OLBG card label: {label}"))

    # Twenty tennis cards in displayed order.  No stale 21 October ranking
    # pairs are carried forward, and no tour/event assignment is guessed.
    tennis = [
        ("902063", "Ann Li", "Zeynep Sonmez", "Today 22:30", "wta"),
        ("902067", "Mary Stoiana", "Moyuka Uchijima", "Tomorrow 00:00", "wta"),
        ("902093", "Katarzyna Kawa", "Belinda Bencic", "Tomorrow 02:30", "wta"),
        ("902073", "Elena Rybakina", "Polina Kudermetova", "Tomorrow 07:00", "wta"),
        ("902069", "Daniil Medvedev", "Sho Shimabukuro", "Tomorrow 05:30", "atp"),
        ("902075", "Iva Jovic", "Jasmine Paolini", "Tomorrow 01:00", "wta"),
        ("902071", "Magda Linette", "Katerina Siniakova", "Tomorrow 01:30", "wta"),
        ("902066", "Antonia Ruzic", "Kayla Day", "Today 22:30", "wta"),
        ("902110", "Tomas Machac", "Karen Khachanov", "Tomorrow 04:00", "atp"),
        ("902072", "Alexandra Eala", "Diana Shnaider", "Tomorrow 04:00", "wta"),
        ("902104", "Raphael Collignon", "Jiri Lehecka", "Tomorrow 07:30", "atp"),
        ("902087", "Pierre Hugues Herbert", "Taylor Fritz", "Tomorrow 09:30", "atp"),
        ("902103", "Valentin Vacherot", "Luca Van Assche", "Tomorrow 08:00", "atp"),
        ("902100", "Borna Gojo", "Daniel Altmaier", "Tomorrow 08:00", "atp"),
        ("902109", "Terence Atmane", "Mattia Bellucci", "Tomorrow 02:30", "atp"),
        ("902131", "David Goffin", "Alex Michelsen", "Tomorrow 09:00", "atp"),
        ("902082", "Alexander Bublik", "Fabian Marozsan", "Tomorrow 10:30", "atp"),
        ("902120", "Damir Dzumhur", "Zizou Bergs", "Tomorrow 11:00", "atp"),
        ("902126", "Flavio Cobolli", "Stan Wawrinka", "Tomorrow 13:00", "atp"),
        ("902105", "Kyrian Jacquet", "Brandon Nakashima", "Tomorrow 14:30", "atp"),
    ]
    for eid, home, away, label, tour in tennis:
        source = "WTA official tournaments" if tour == "wta" else "ATP Tour official scores"
        url = "https://www.wtatennis.com/tournaments" if tour == "wta" else "https://www.atptour.com/en/scores/current"
        rows.append(unlined(f"tennis-{eid}", "tennis", "Tennis Match — exact tour/event unconfirmed", home, away, source, url, "Both players' current official ranking/form inputs and the precise event page were not re-verified in this capture; winner, handicap and totals remain blank.", eid, f"OLBG card label: {label}"))

    # Volleyball: five Czech fixtures have official CVF date/time confirmation.
    rows.append(unlined("vb-36988", "volleyball", "Polish Women's Volleyball — OLBG card", "Radomka Radom W", "Mielec W", "TAURON Liga", "https://www.tauronliga.pl/games.html", "Exact official fixture and comparable team ratings were not independently confirmed.", "36988", "OLBG card label: Tomorrow 11:30"))
    czech = [
        ("36990", "Ceske Budejovice", "Beskydy"),
        ("36992", "Ostrava", "Kladno"),
        ("36989", "Brno", "Odolena Voda"),
        ("36993", "Usti Nad Labem", "Zlin"),
        ("36991", "Liberec", "Benatky nad Jizerou"),
    ]
    raw_labels = {"36990": "Tomorrow 12:00", "36992": "Tomorrow 12:00", "36989": "Tomorrow 12:00", "36993": "Tomorrow 12:00", "36991": "Tomorrow 12:00"}
    for eid, home, away in czech:
        rows.append(unlined(f"vb-{eid}", "volleyball", "Czech Men's Extraliga 2026/27", home, away, "Czech Volleyball Federation Extraliga", "https://www.cvf.cz/extraliga/extraliga-muzi?filteredGroupId=29147", "Official schedule confirms the pairing, but a complete comparable ratings input was not captured; no independent price.", eid, f"Official: 22 Oct 2026 18:00 local; OLBG card label: {raw_labels[eid]}", date="2026-10-22", official_status="fixture date and time confirmed by CVF; model inputs pending", time_basis="Official local date/time; raw OLBG label retained"))
    polish = [
        ("36963", "Slepsk Suwalki", "GKS Katowice", "23 Oct 11:30"),
        ("36964", "PGE Skra Belchatow", "Projekt Warszawa", "24 Oct 12:00"),
        ("36965", "CHKS Chelm", "Resovia Rzeszow", "25 Oct 13:00"),
    ]
    for eid, home, away, label in polish:
        rows.append(unlined(f"vb-{eid}", "volleyball", "Polish PlusLiga — OLBG card", home, away, "PlusLiga official games review URL", "https://www.plusliga.pl/games.html", "plusliga.pl redirected to the TAURON Liga shell during review; exact PlusLiga fixture and ratings are not treated as confirmed.", eid, f"OLBG card label: {label}", official_status="official confirmation pending; PlusLiga URL redirected"))

    # Cricket match cards with official schedule evidence where captured.
    rows += [
        unlined("cricket-188814", "cricket", "New Zealand v India — 1st T20I", "New Zealand", "India", "New Zealand Cricket", "https://www.nzc.nz/nzc-sky-confirm-free-to-air-offerings-tiktok-first", "Fixture is official, but a complete comparable current team-strength feed was not captured; no price originated.", "188814", "Official: 22 Oct 2026 20:00 local; OLBG card label: Tomorrow 03:00", date="2026-10-22", venue="Hagley Oval, Christchurch", official_status="fixture confirmed by NZC; model inputs pending", time_basis="Official local date/time; raw OLBG label retained"),
        unlined("cricket-188829", "cricket", "Pakistan ODI Tri-Series — Sri Lanka v England", "England", "Sri Lanka", "England and Wales Cricket Board", "https://www.ecb.co.uk/news/4594465/how-to-watch-and-follow-the-england-men-v-pakistan-and-sri-lanka", "Fixture is official, but comparable current team-strength inputs were not captured; no price originated.", "188829", "Official: 22 Oct 2026 09:00 BST; OLBG card label: Tomorrow 04:00", date="2026-10-22", venue="Rawalpindi Cricket Stadium", official_status="fixture confirmed by ECB; model inputs pending", time_basis="Official date/time; raw OLBG label retained"),
        unlined("cricket-188828", "cricket", "Namibia v Ireland — 1st ODI", "Namibia", "Ireland", "Cricket Ireland tour schedule", "https://cricketireland.ie/tour-of-namibia-2026/", "Official tour page confirms the date and Windhoek; exact ground/start time and comparable ratings remain unconfirmed.", "188828", "Official date: 22 Oct 2026; OLBG card label: Tomorrow 04:00", date="2026-10-22", official_status="fixture date confirmed by Cricket Ireland; precise venue/time and model inputs pending", time_basis="Official date; raw OLBG time label retained"),
        unlined("cricket-188826", "cricket", "Australia Women v New Zealand Women — 3rd T20I", "Australia Women", "New Zealand Women", "Cricket Australia", "https://www.cricket.com.au/matches/series/CA:4608/australia-v-new-zealand-t20is-2026-women", "Fixture is official, but comparable current team-strength inputs were not captured; no price originated.", "188826", "Official: 22 Oct 2026 19:15 AEDT; OLBG card label: Tomorrow 04:15", date="2026-10-22", venue="North Sydney Oval, Sydney", official_status="fixture confirmed by Cricket Australia; model inputs pending", time_basis="Official local date/time; raw OLBG label retained"),
        unlined("cricket-188811", "cricket", "CSA Pro20 Cup 2026/27", "Eastern Storm", "Tuskers", "Cricket South Africa", "https://www.cricket.co.za/upcoming/", "Official fixture is confirmed, but comparable current ratings were not captured; no price originated.", "188811", "Official: 22 Oct 2026 18:00 local; OLBG card label: Tomorrow 12:00", date="2026-10-22", venue="World Sports Betting Willowmoore Park Stadium", official_status="fixture confirmed by CSA; model inputs pending", time_basis="Official local date/time; raw OLBG label retained"),
        unlined("cricket-188825", "cricket", "CSA Pro20 Cup 2026/27", "Mpumalanga Rhinos", "South Africa Emerging / CSA High Performance", "Cricket South Africa", "https://www.cricket.co.za/upcoming/", "Official fixture lists CSA High Performance; OLBG says South Africa Emerging. Both labels are preserved and comparable ratings remain unconfirmed.", "188825", "Official: 22 Oct 2026 13:00 local; OLBG card label: Tomorrow 07:00", date="2026-10-22", venue="White River Country Club", official_status="fixture confirmed by CSA; team-label difference and model inputs flagged", time_basis="Official local date/time; raw OLBG label retained"),
        unlined("cricket-188831", "cricket", "UAE ODI Tri-Series 2026 — Final (OLBG pairing)", "Afghanistan", "Zimbabwe", "Afghanistan Cricket Board", "https://acb.af/en-US/post/afghanistan-to-host-bangladesh-and-zimbabwe-for-multi-format-series-in-uae", "ACB confirms a 23 October final but its schedule does not pre-confirm the finalists. The OLBG pairing remains official confirmation pending; no third-party substitute used.", "188831", "Official final date: 23 Oct 2026; OLBG card label: 23 Oct 07:30", date="2026-10-23", official_status="final date official; participants and start time pending official confirmation", time_basis="Official tournament final date; raw OLBG pairing/time retained"),
    ]
    cricket_outrights = [
        ("182606", "ICC Men's World Cup 2027", "World Cup 2027 Field", "International Cricket Council", "https://www.icc-cricket.com/tournaments", "21 Nov 2027 05:00"),
        ("187184", "WBBL 2026 — Outright", "WBBL Field", "Cricket Australia", "https://www.cricket.com.au/matches", "05 Dec 03:10"),
        ("187503", "BBL 2026/27 — Outright", "BBL Field", "Cricket Australia", "https://www.cricket.com.au/matches/series", "12 Dec 03:15"),
        ("187504", "SA20 2026/27 — Outright", "SA20 Field", "SA20", "https://www.sa20.co.za/", "24 Jan 2027 11:30"),
        ("188350", "T20 Blast 2027 — Outright", "T20 Blast Field", "England and Wales Cricket Board", "https://www.ecb.co.uk/", "18 Jul 2027 11:00"),
    ]
    for eid, comp, home, source, url, label in cricket_outrights:
        rows.append(unlined(f"cricket-{eid}", "cricket", comp, home, "Outright", source, url, "Outright field, exact market settlement date and a complete official strength distribution were not independently confirmed; no price originated.", eid, f"OLBG card label: {label}"))

    # Golf: official tournament windows differ from several OLBG labels.
    golf = [
        ("101904", "PGA Tour — Butterfield Bermuda Championship", "Bermuda Championship Field", "PGA Tour", "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview", "2026-10-22", "Port Royal Golf Course, Southampton", "Official tournament: 22–25 Oct 2026; OLBG card label: Tomorrow 14:10"),
        ("101911", "Legends Tour — Senior Italian Open", "Senior Italian Open Field", "Legends Tour", "https://legendstour.com/tournament/sergio-melpignano-senior-italian-open-2026", "2026-10-22", "San Domenico Golf, Italy", "Official tournament: 22–24 Oct 2026; OLBG card label: 24 Oct 11:45"),
        ("101912", "Sunshine Tour — Stella Artois Players Championship", "Stella Artois Players Championship Field", "Sunshine Tour", "https://sunshinetour.com/schedule?code=RWAO&id=226S", "2026-10-22", "Glendower Golf Club", "Official tournament: 22–25 Oct 2026; OLBG card label: 25 Oct 10:45"),
        ("101903", "PGA Tour Champions — Stifel Charity Classic", "Stifel Charity Classic Field", "PGA Tour Champions", "https://www.pgatour.com/pgatour-champions/tournaments/2026/stifel-charity-classic/S2026625/overview", "2026-10-23", "Norwood Hills Country Club, St. Louis", "Official tournament: 23–25 Oct 2026; OLBG card label: 25 Oct 17:45"),
    ]
    for eid, comp, home, source, url, date, venue, label in golf:
        rows.append(unlined(f"golf-{eid}", "golf", comp, home, "Tournament Outright", source, url, "Official tournament window is confirmed; no complete official field-strength distribution was captured. OLBG's later label may represent another round and is not treated as the start date.", eid, label, date=date, venue=venue, official_status="official tournament dates and venue confirmed; field-strength inputs pending", time_basis="Official tournament start date; raw OLBG later-round label retained"))

    # Rugby League futures: IDs and raw dates corrected from the live cards.
    rl = [
        ("2695857", "State of Origin 2027 — Series Winner", "New South Wales / Queensland Field", "NRL official draw", "https://www.nrl.com/draw/", "27 May 2027 06:00"),
        ("2801554", "Super League 2027 — Grand Final Winner", "Super League Field", "Super League official", "https://www.superleague.co.uk/match-centre", "02 Oct 2027 13:00"),
        ("2801600", "NRL 2027 — Grand Final Winner", "NRL Field", "NRL official draw", "https://www.nrl.com/draw/", "03 Oct 2027 04:30"),
    ]
    for eid, comp, home, source, url, label in rl:
        rows.append(unlined(f"rl-{eid}", "rugby-league", comp, home, "Outright", source, url, "Pre-season squad and market-settlement details are not final; no independent price originated.", eid, f"OLBG card label: {label}"))

    # Gaelic Football club cards and All-Ireland future.
    gaa = [
        ("3530", "Gaelic Football Club Match — OLBG card", "St Finbarrs", "Nemo Rangers", "25 Oct 12:00"),
        ("3532", "Gaelic Football Club Match — OLBG card", "Moycullen", "Salthill-Knocknacarra", "24 Oct 14:00"),
        ("3531", "Gaelic Football Club Match — OLBG card", "Kanturk", "Eire Og Cor", "01 Nov 09:00"),
        ("3536", "Gaelic Football Club Match — OLBG card", "Rathgormack", "The Nire", "01 Nov 10:30"),
        ("3537", "Gaelic Football Club Match — OLBG card", "Fr Caseys", "Kildimo Pallaskenry", "01 Nov 10:30"),
        ("3327", "All Ireland Football Championship 2027 — Outright", "Inter-County Field", "Outright", "25 Jul 2027 10:30"),
    ]
    for eid, comp, home, away, label in gaa:
        rows.append(unlined(f"gaa-{eid}", "gaelic-football", comp, home, away, "Gaelic Athletic Association", "https://www.gaa.ie/football", "No unified official county-club ratings/final field feed was captured; exact fixture and prices remain unconfirmed.", eid, f"OLBG card label: {label}"))

    # Two darts outrights; all 16 match rows are originated separately.
    rows += [
        unlined("pdc-32338", "darts", "2026 PDC European Championship — Outright", "32-Player Draw Outright", "Field", "PDC official rankings", "https://www.pdc.tv/rankings", "Full bracket-path probabilities were not independently originated; match rows remain separate.", "32338", "OLBG card label: 25 Oct 14:00", official_status="official rankings reviewed; exact market settlement date pending"),
        unlined("pdc-26023", "darts", "2027 PDC World Darts Championship — Outright", "96-Player Field Outright", "Field", "PDC official rankings", "https://www.pdc.tv/rankings", "Qualifying field is not final; no independent outright price originated.", "26023", "OLBG card label: 03 Jan 2027 12:00", official_status="official rankings reviewed; final field and market settlement date pending"),
    ]
    assert len(rows) == 74, len(rows)
    return rows


def _sports_refresh(sports_doc: dict) -> dict:
    sports_doc["captured_at"] = CAPTURE_DATE
    for item in sports_doc["excluded_sports"]:
        item["reason"] = item["reason"].replace("2026-10-21", CAPTURE_DATE)
    summaries = {
        "ice-hockey": ("National Hockey League, Swedish Ice Hockey Federation & Liiga", "https://api-web.nhle.com/v1/score/2026-10-22", "19 originated rows: all 12 official NHL games on 22 October, all six SHL games (three OLBG-discovered), and JYP–HPK. NHL and three SHL additions are official supplements, not claimed OLBG cards."),
        "basketball": ("NBA & Euroleague Basketball; KBL/NBB review links", "https://www.nba.com/games?date=2026-10-23", "25 rows: 14 official NBA games (four OLBG cards), nine current EuroLeague games (four cards), and two unlined KBL/NBB cards. Three expired 21 October NBA cards were removed."),
        "rugby-union": ("LNR, United Rugby Championship & Six Nations Rugby", "https://prod2.lnr.fr/classement", "24 rows: seven Top 14, eight Pro D2 and eight URC fixtures originated; the Six Nations outright is unlined and its OLBG date label conflicts with the official 13 March conclusion."),
        "handball": ("European Handball Federation plus domestic review sources", "https://ehfcl.eurohandball.com/men/2026-27/matches/", "20 visible cards: five current EHF Champions League fixtures originated and 15 domestic/international cards left unlined pending precise official fixture and ratings verification."),
        "darts": ("Professional Darts Corporation (PDC)", "https://www.pdc.tv/rankings", "18 visible cards: 16 European Championship ties originated from official ranking prize sums; two outrights remain unlined. Fixture labels come from OLBG and are not represented as PDC fixture verification."),
        "tennis": ("ATP Tour & WTA Tour", "https://www.atptour.com/en/scores/current", "20 current visible cards catalogued in displayed order. All are unlined because the precise event and both players' current official inputs were not re-verified; stale 21 October pairs were removed."),
        "snooker": ("World Snooker Tour (WST)", "https://www.wst.tv/matches/", "The current OLBG hub displays 'No tips found'; zero active rows are published."),
        "baseball": ("Major League Baseball (MLB)", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-27&hydrate=team,venue", "Three World Series games originated from official season run rates. Only Game 1 has a visible OLBG card; Games 2 and 3 are official supplements."),
        "motor-racing": ("FIA Formula One World Championship", "https://www.formula1.com/en/racing/2026/united-states", "Three current OLBG markets originated: US Grand Prix, 2026 Drivers' Championship, and Championship Without Kimi Antonelli. Standings retain their stored official capture date; the race time is corrected from the official COTA page."),
        "volleyball": ("Czech Volleyball Federation, PlusLiga & TAURON Liga", "https://www.cvf.cz/extraliga/extraliga-muzi?filteredGroupId=29147", "Nine visible cards catalogued and unlined. CVF confirms five Czech fixtures; PlusLiga's URL redirected to TAURON Liga and is not treated as fixture confirmation."),
        "cricket": ("ICC, ECB, NZC, Cricket Ireland, Cricket Australia, CSA & ACB", "https://www.cricket.com.au/matches", "12 visible cards: seven match rows and five outrights, all unlined. Official fixture confirmations and pending states are shown per row; no third-party ratings were substituted."),
        "golf": ("PGA Tour, PGA Tour Champions, Legends Tour & Sunshine Tour", "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview", "Four current tournament cards catalogued and unlined. Official start dates are linked; later OLBG labels are preserved and flagged as potentially different round semantics."),
        "rugby-league": ("National Rugby League (NRL) & Super League", "https://www.nrl.com/draw/", "Three 2027 futures catalogued with corrected event IDs and raw card dates: State of Origin 2695857, Super League 2801554 and NRL 2801600. All remain unlined."),
        "gaelic-football": ("Gaelic Athletic Association (GAA)", "https://www.gaa.ie/football", "Six visible cards: five club fixtures including Fr Caseys–Kildimo Pallaskenry and the 2027 All-Ireland outright. All remain unlined pending unified official inputs."),
        "greyhounds": ("Greyhound Board of Great Britain (GBGB)", "https://www.gbgb.org.uk/racing/results/", "The current OLBG hub displays 'No tips found'; stale 21 October race cards were removed."),
        "aussie-rules": ("Australian Football League (AFL)", "https://www.afl.com.au/fixture", "The current OLBG hub displays 'No tips found' on 22 October 2026."),
        "esports": ("Riot LoL Esports / Valve CS2", "https://lolesports.com/schedule", "The current OLBG hub displays 'No tips found' on 22 October 2026."),
    }
    for sport in sports_doc["eligible_sports"]:
        slug = sport["slug"]
        sport["olbg_url"] = HUBS[slug]
        if slug == "basketball":
            sport["olbg_sport_id"] = 4
        if slug == "golf":
            sport["olbg_sport_id"] = 5
        if slug in summaries:
            sport["governing_body"], sport["official_url"], sport["status_summary"] = summaries[slug]
    return sports_doc


def refresh_inputs(inputs: dict) -> dict:
    inputs["captured_at"] = CAPTURE_DATE
    inputs["nhl_fixture_ids"] = NHL_FIXTURE_IDS
    inputs["nba_fixtures"] = NBA_FIXTURES
    inputs["euroleague_fixtures"] = [
        {**f, "olbg_url": HUBS["basketball"]}
        for f in inputs["euroleague_fixtures"] if f["id"] in EUROLEAGUE_ACTIVE_IDS
    ]
    inputs["eurocup_teams"] = {}
    inputs["eurocup_fixtures"] = []
    inputs["ehf_fixture_ids"] = sorted(EHF_ACTIVE_IDS)
    inputs["ehf_olbg_map"] = {row_id: HUBS["handball"] for row_id in sorted(EHF_ACTIVE_IDS)}
    inputs.pop("nba_extra_game_ids", None)
    inputs["shl_teams"] = SHL_TEAMS
    inputs["shl_fixtures"] = SHL_FIXTURES
    inputs["liiga_teams"] = LIIGA_TEAMS
    inputs["liiga_fixture"] = LIIGA_FIXTURE
    inputs["tennis_originated"] = []
    inputs["snooker_originated"] = []
    inputs["mlb_world_series"] = {
        **inputs["mlb_world_series"],
        "url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-27&hydrate=team,venue",
        "olbg_url": HUBS["baseball"],
    }
    inputs["unlined_rows"] = build_unlined()

    prov: dict[str, dict] = {}
    for row_id in NHL_FIXTURE_IDS:
        prov[row_id] = provenance(None, "ice-hockey")
    for f in NBA_FIXTURES:
        row_id = f"nba-{f['game_id']}"
        prov[row_id] = provenance(f.get("olbg_event_id"), "basketball", "official fixture confirmed; completed 2025-26 official records used with Medium cap")
    for f in inputs["euroleague_fixtures"]:
        prov[f["id"]] = provenance(EUROLEAGUE_OLBG_IDS.get(f["id"]), "basketball")
    for mapping in (TOP14_OLBG_IDS, PROD2_OLBG_IDS, URC_OLBG_IDS):
        for row_id, event_id in mapping.items():
            prov[row_id] = provenance(event_id, "rugby-union")
    # Official-only rugby fixtures receive explicit supplement provenance too.
    for f in inputs["top14_fixtures"] + inputs["prod2_fixtures"]:
        prov.setdefault(f["id"], provenance(None, "rugby-union"))
    urc_raw = json.loads((ROOT / "data" / "inputs" / "urc.json").read_text(encoding="utf-8"))
    for f in urc_raw["fixtures"]:
        prov.setdefault(f["id"], provenance(URC_OLBG_IDS.get(f["id"]), "rugby-union"))
    for row_id in sorted(EHF_ACTIVE_IDS):
        prov[row_id] = provenance(EHF_OLBG_IDS[row_id], "handball")
    for f in SHL_FIXTURES:
        prov[f["id"]] = provenance(f.get("olbg_event_id"), "ice-hockey")
    prov[LIIGA_FIXTURE["id"]] = provenance("199912", "ice-hockey", "fixture and current JYP/HPK official records checked; venue unconfirmed")
    for f in inputs["darts_fixtures"]:
        prov[f["id"]] = provenance(f["id"].split("-")[-1], "darts", "official PDC ranking inputs checked; fixture label and date come from OLBG", "OLBG card label; not independently confirmed as PDC start time")
    live_mlb = json.loads((ROOT / "data" / "live" / "mlb.json").read_text(encoding="utf-8"))
    for f in live_mlb["fixtures"]:
        prov[f["id"]] = provenance("160789" if f["id"] == "mlb-849805" else None, "baseball")
    prov["f1-2026-usgp"] = provenance("913", "motor-racing", "official race page confirmed; standings retain stored 2026-10-21 capture")
    prov["f1-2026-drivers"] = provenance("828", "motor-racing", "official standings captured 2026-10-21; not represented as refreshed 22 October values", "OLBG season-outright card label; not a fixture start time")
    prov["f1-2026-without-antonelli"] = provenance("912", "motor-racing", "official standings captured 2026-10-21; not represented as refreshed 22 October values", "OLBG season-outright card label; not a fixture start time")
    inputs["provenance_by_id"] = prov
    return inputs


def refresh_flags(_old_flags: list[dict]) -> list[dict]:
    return [
        {"id": "VF-01", "severity": "high", "category": "Dynamic coverage limitation", "sport": "Cross-sport", "item": "Load More Tips remains unresolved on ten active hubs", "detail": "The 126 current static cards are covered, but hidden results behind Load More are not claimed. Basketball pagination probes did not advance the inventory. This dashboard is therefore a fullest supportable static capture, not exhaustive dynamic OLBG coverage.", "source_name": "OLBG global tips and sport hubs", "source_url": "https://www.olbg.com/betting-tips"},
        {"id": "VF-02", "severity": "high", "category": "Stale event removal", "sport": "Cross-sport", "item": "Expired 21 October rows removed", "detail": "Stale NHL, NBA, EuroLeague/EuroCup, tennis, snooker, volleyball, cricket and greyhound entries are excluded from the active desk. Three still-visible but expired NBA cards (534839, 535674, 534893) are logged rather than published as upcoming picks.", "source_name": "NBA official calendar", "source_url": "https://www.nba.com/games?date=2026-10-22"},
        {"id": "VF-03", "severity": "medium", "category": "Discovery provenance", "sport": "Cross-sport", "item": "Official supplements separated from OLBG-discovered rows", "detail": "Forty official-only supplements (12 NHL, 10 NBA, five EuroLeague, eight rugby union, three SHL and two MLB) carry 'official supplementary' provenance and no OLBG link. The dashboard never presents them as proof of OLBG coverage.", "source_name": "NHL official daily schedule", "source_url": "https://api-web.nhle.com/v1/score/2026-10-22"},
        {"id": "VF-04", "severity": "medium", "category": "Blank market and model cap", "sport": "Basketball (NBA)", "item": "14 NBA totals blank; all NBA picks capped Medium", "detail": "Moneyline and spread use completed official 2025-26 records. Current totals are not inferred from unavailable current PF/PA inputs, and off-season roster uncertainty caps every NBA selection at Medium.", "source_name": "NBA official standings", "source_url": "https://www.nba.com/standings?Season=2025-26"},
        {"id": "VF-05", "severity": "medium", "category": "Blank unconfirmed inputs", "sport": "Cross-sport", "item": "74 visible cards deliberately unlined", "detail": "Rows lacking precise official fixture confirmation or comparable current strength inputs retain blank winner, handicap, total and pick cells. Official review links are not mislabeled as proof of verification.", "source_name": "OLBG sitemap and hubs", "source_url": "https://www.olbg.com/sitemap-betting-tips.xml"},
        {"id": "VF-06", "severity": "medium", "category": "Date/time semantics", "sport": "Cross-sport", "item": "Relative OLBG labels retained without UTC inference", "detail": "Today/Tomorrow labels and viewer-timezone renders are preserved as raw card text. ISO date/time fields are used only where official pages independently establish them.", "source_name": "OLBG Tennis hub", "source_url": "https://www.olbg.com/betting-tips/Tennis/3"},
        {"id": "VF-07", "severity": "medium", "category": "Official/date mismatch", "sport": "Rugby Union", "item": "Six Nations OLBG 14 March label vs official 13 March finish", "detail": "The official 2027 schedule concludes with Ireland–France on 13 March at 20:10 GMT. OLBG's 14 March 20:00 label is retained as raw text and not treated as an official fixture date.", "source_name": "Six Nations official 2027 schedule", "source_url": "https://www.sixnationsrugby.com/en/m6n/news/mens-six-nations-2027-fixtures-and-schedule-confirmed"},
        {"id": "VF-08", "severity": "medium", "category": "Tournament-round semantics", "sport": "Golf", "item": "Four OLBG labels differ from official tournament starts", "detail": "Official sources confirm Bermuda, Senior Italian Open and Stella Artois beginning 22 October, and Stifel beginning 23 October. Later OLBG labels are preserved but flagged as potentially later rounds rather than overwritten.", "source_name": "PGA Tour Bermuda official page", "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview"},
        {"id": "VF-09", "severity": "medium", "category": "Stored capture / corrected start", "sport": "Motor Racing", "item": "F1 race time corrected; standings remain tied to stored capture", "detail": "Formula 1's official US GP page gives 25 October at 16:00 track time. Stored standings inputs are explicitly dated 2026-10-21 and are not described as newly refreshed on 22 October.", "source_name": "Formula 1 United States GP", "source_url": "https://www.formula1.com/en/racing/2026/united-states"},
        {"id": "VF-10", "severity": "high", "category": "Official-source redirect", "sport": "Volleyball", "item": "PlusLiga URL redirected to TAURON Liga", "detail": "Three Polish PlusLiga cards remain official confirmation pending. A redirect to a different competition's shell is not accepted as fixture or ratings verification.", "source_name": "PlusLiga review URL", "source_url": "https://www.plusliga.pl/games.html"},
        {"id": "VF-11", "severity": "high", "category": "Participant confirmation pending", "sport": "Cricket", "item": "Afghanistan–Zimbabwe displayed as 23 October final", "detail": "ACB officially confirms the final date but its schedule does not pre-confirm participants. The pairing and start label remain OLBG-sourced and unlined; no third-party report is used as official proof.", "source_name": "Afghanistan Cricket Board schedule", "source_url": "https://acb.af/en-US/post/afghanistan-to-host-bangladesh-and-zimbabwe-for-multi-format-series-in-uae"},
        {"id": "VF-12", "severity": "low", "category": "Zero active markets", "sport": "Snooker, Greyhounds, Aussie Rules & eSports", "item": "Four eligible hubs display no tips", "detail": "Their category pages remain present with zero rows so the empty checks are visible; no substitute fixtures are invented.", "source_name": "OLBG Snooker hub", "source_url": "https://www.olbg.com/betting-tips/Snooker/8"},
        {"id": "VF-13", "severity": "low", "category": "Taxonomy / event-ID corrections", "sport": "Basketball, Golf & Rugby League", "item": "Correct routes and futures IDs enforced", "detail": "Basketball uses sport ID 4 and Golf 5. Rugby League maps State of Origin 2695857, Super League 2801554 and NRL 2801600; the previous State of Origin/NRL swap is removed.", "source_name": "OLBG betting-tips sitemap", "source_url": "https://www.olbg.com/sitemap-betting-tips.xml"},
        {"id": "VF-14", "severity": "low", "category": "Neutral-site handling", "sport": "Basketball (NBA)", "item": "HOU @ SAS at Moody Center has no home-court adjustment", "detail": "San Antonio remains the official designated home team, but the official Austin neutral venue is shown and the NBA model's home-court logit adjustment is set to zero for this game.", "source_name": "NBA official HOU–SAS game page", "source_url": "https://www.nba.com/game/hou-vs-sas-0022600009"},
        {"id": "VF-15", "severity": "low", "category": "Confidence price-band gate", "sport": "Cross-sport", "item": "Probability alone cannot produce High", "detail": "High requires p > 0.70 and fair American odds from -250 through +10000 inclusive. Stronger favourites shorter than -250 are capped Medium and expose the failed price-band gate in matches.json.", "source_name": "Methodology and deterministic tests", "source_url": "https://github.com/buffedlizard55-lab/OLBG2"},
    ]


def refresh_audit(old_audit: list[dict]) -> list[dict]:
    additions = [
        {"id": "RA-11", "severity": "high", "layer": "Verified (/verified/)", "file": "scripts/verified_seed.py & data/verified/matches.json", "published": "Baseline active desk retained stale 21 October events and used Basketball/19 and Golf/4.", "official": "Current sitemap and hubs use Basketball/4 and Golf/5; expired cards are not upcoming official fixtures.", "source_name": "OLBG betting-tips sitemap", "source_url": "https://www.olbg.com/sitemap-betting-tips.xml", "resolution": "Replaced active inventory, corrected taxonomy and added exact per-event provenance."},
        {"id": "RA-12", "severity": "high", "layer": "Verified (/verified/)", "file": "scripts/verified_model.py", "published": "HIGH_THRESHOLD=0.72 with no American odds gate; 20 High picks included stale or unsupported narratives.", "official": "Requested rule is strict p>0.70 plus fair American -250 through +10000; each High narrative needs unique officially supported form facts.", "source_name": "NHL official MIN–CGY game feed", "source_url": "https://api-web.nhle.com/v1/score/2026-10-22", "resolution": "Implemented two-part gate and regenerated only qualifying current High narratives."},
        {"id": "RA-13", "severity": "high", "layer": "Verified (/verified/)", "file": "data/verified/matches.json", "published": "Official-only NHL/rugby/baseball fixtures were indistinguishable from OLBG-discovered cards.", "official": "The current Ice Hockey hub shows four SHL/Liiga cards and no current NHL card; official schedules can supplement but cannot prove OLBG discovery.", "source_name": "OLBG Ice Hockey hub", "source_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13", "resolution": "Added OLBG-discovered vs official supplementary states and removed OLBG links from supplements."},
        {"id": "RA-14", "severity": "medium", "layer": "Verified (/verified/)", "file": "scripts/verified_model.py (f1-2026-usgp)", "published": "US Grand Prix stored as 2026-10-25T20:00:00Z and old 2027 championship row substituted for event 912.", "official": "Official COTA page gives 25 October at 16:00 track time; current event 912 is 2026 Championship Without Kimi Antonelli.", "source_name": "Formula 1 United States GP", "source_url": "https://www.formula1.com/en/racing/2026/united-states", "resolution": "Corrected race label/time, replaced the wrong future and originated the actual without-Antonelli market."},
        {"id": "RA-15", "severity": "medium", "layer": "Verified (/verified/)", "file": "data/verified/matches.json", "published": "Six Nations and golf card dates were treated as ordinary fixture start times.", "official": "Six Nations ends 13 March 2027; official golf tournament windows begin 22 or 23 October while several OLBG labels are later.", "source_name": "Six Nations official schedule", "source_url": "https://www.sixnationsrugby.com/en/m6n/news/mens-six-nations-2027-fixtures-and-schedule-confirmed", "resolution": "Separated official dates from raw OLBG labels and added explicit semantic flags."},
        {"id": "RA-16", "severity": "medium", "layer": "Verified (/verified/)", "file": "scripts/verified_model.py (NBA)", "published": "NBA model applied a standard home-court adjustment to every fixture and omitted venues.", "official": "NBA lists HOU@SAS at Moody Center in Austin; it is not a normal San Antonio home-court fixture.", "source_name": "NBA official HOU–SAS page", "source_url": "https://www.nba.com/game/hou-vs-sas-0022600009", "resolution": "Added all official venues and disabled home-court adjustment for the neutral-site game."},
        {"id": "RA-17", "severity": "medium", "layer": "Verified (/verified/)", "file": "data/verified/matches.json & sports.json", "published": "Coverage wording implied all active OLBG events were captured despite Load More controls.", "official": "Static rendered chunks expose 126 current cards; dynamic controls remain unresolved and pagination probes are not valid page advancement.", "source_name": "OLBG Basketball hub", "source_url": "https://www.olbg.com/betting-tips/Basketball/4", "resolution": "Publish static coverage plus labelled supplements and flag the unresolved dynamic limitation on every relevant page."},
        {"id": "RA-18", "severity": "low", "layer": "Verified (/verified/)", "file": "scripts/verified_build.py", "published": "Generic 'Official Fixture' labels and hard-coded 21 October counts, dates, thresholds and another session's branch name.", "official": "Some rows have only official review pages or stored stats captures; those states must not be described as newly verified fixtures.", "source_name": "Verified methodology source", "source_url": "https://github.com/buffedlizard55-lab/OLBG2", "resolution": "Generate labels and methodology from current data, capture date and per-row provenance."},
    ]
    return old_audit + additions
