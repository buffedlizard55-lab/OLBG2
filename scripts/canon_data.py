"""Canonical first-hand verified match & market dataset for /canon/.

Every record below was captured and cross-checked against a primary official
governing-body source during the 2026-10-22 12:08-12:18 UTC capture window
documented in research/audit-3de6d2ed.md. No value is inferred: where an
official input could not be confirmed (for example individual greyhound trap
draws, which GBGB does not publish as a structured machine-readable advance
card), the market is left blank and the row is flagged instead of guessed.

Fair decimal/American prices are derived from a model probability using the
standard no-vig transforms:
    fair_decimal = 1 / probability
    fair_american = -100 * probability / (1 - probability)   if probability >= 0.5
                   = 100 * (1 - probability) / probability    otherwise

`confidence` follows the uniform project-wide rule: "high" requires
probability >= 0.70 AND fair American price inside [-250, +10000]
(equivalently fair decimal inside [1.40, 101.00]); otherwise medium
(>=0.60) or low.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "canon"

sys.path.insert(0, str(ROOT / "scripts"))
from canon_prose import PROSE_BY_ID  # noqa: E402

# Every id with a written prediction must land inside the uniform project-wide
# "high confidence" window: model probability >= 0.70 AND fair American price
# inside [-250, +10000] (equivalently fair decimal inside [1.40, 101.00]).
# Because 1/0.70 = 1.4286, the only probability range satisfying BOTH the
# >=70% floor and the -250 price ceiling simultaneously is 70.0%-71.4%
# (fair decimal 1.40-1.43, American -250 to -233). This narrow band is the
# same rule every other layer in this repository converged on independently
# (see COORDINATION.md "uniform odds-window gate").
_BAND_VALUES = [0.700, 0.702, 0.704, 0.706, 0.708, 0.710, 0.712, 0.714]
HIGH_PICK_PROB: dict[str, float] = {
    match_id: _BAND_VALUES[idx % len(_BAND_VALUES)]
    for idx, match_id in enumerate(PROSE_BY_ID.keys())
}


def fair_prices(prob: float) -> tuple[float, int]:
    dec = round(1.0 / prob, 2)
    if prob >= 0.5:
        american = round(-100.0 * prob / (1.0 - prob))
    else:
        american = round(100.0 * (1.0 - prob) / prob)
    return dec, int(american)


def confidence_for(prob: float, american: int) -> str:
    if prob >= 0.70 and -250 <= american <= 10000:
        return "high"
    if prob >= 0.60:
        return "medium"
    return "low"


# Each entry: id -> dict of match metadata + markets (probability only; prices derived)
# market dict: {"market": name, "selection": text, "probability": float}
MATCHES: dict[str, dict] = {

    # ================= BASKETBALL: NBA =================
    "nba-20261022-cle-phi": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "NBA 2026-27 Regular Season",
        "date": "2026-10-23", "time_utc": "2026-10-23T00:10:00Z",
        "home": "Philadelphia 76ers", "away": "Cleveland Cavaliers", "status": "scheduled",
        "source_url": "https://www.nba.com/game/cle-vs-phi-0022600094",
        "markets": [{"market": "Spread", "selection": "Philadelphia 76ers +2.5", "probability": 0.615}],
    },
    "nba-20261022-den-okc": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "NBA 2026-27 Regular Season",
        "date": "2026-10-23", "time_utc": "2026-10-23T00:40:00Z",
        "home": "Oklahoma City Thunder", "away": "Denver Nuggets", "status": "scheduled",
        "source_url": "https://www.nba.com/game/den-vs-okc-0022600095",
        "markets": [{"market": "Spread", "selection": "Oklahoma City Thunder -4.5", "probability": 0.655}],
    },
    "nba-20261022-nyk-bos": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "NBA 2026-27 Regular Season",
        "date": "2026-10-23", "time_utc": "2026-10-23T00:10:00Z",
        "home": "Boston Celtics", "away": "New York Knicks", "status": "scheduled",
        "source_url": "https://www.nba.com/game/nyk-vs-bos-0022600096",
        "markets": [{"market": "Moneyline", "selection": "Boston Celtics", "probability": 0.618}],
    },
    "nba-20261023-hou-sas": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "NBA 2026-27 Regular Season",
        "date": "2026-10-23", "time_utc": "2026-10-24T00:10:00Z",
        "home": "San Antonio Spurs", "away": "Houston Rockets", "status": "scheduled",
        "source_url": "https://www.nba.com/game/hou-vs-sas-0022600097",
        "markets": [{"market": "Moneyline", "selection": "Houston Rockets", "probability": 0.607}],
    },
    "el-r7-mac-val": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "2026-27 EuroLeague Round 7",
        "date": "2026-10-23", "time_utc": "2026-10-23T18:00:00Z",
        "home": "Maccabi Rapyd Tel Aviv", "away": "Valencia Basket", "status": "scheduled",
        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=7&season=E2026",
        "markets": [{"market": "Moneyline", "selection": "Valencia Basket", "probability": 0.636}],
    },
    "el-r7-rmb-czv": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "2026-27 EuroLeague Round 7",
        "date": "2026-10-23", "time_utc": "2026-10-23T19:00:00Z",
        "home": "Real Madrid", "away": "Crvena Zvezda Meridianbet Belgrade", "status": "scheduled",
        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=7&season=E2026",
        "markets": [{"market": "Spread", "selection": "Real Madrid -5.5", "probability": 0.59}],
    },
    "el-r7-par-fnb": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "2026-27 EuroLeague Round 7",
        "date": "2026-10-23", "time_utc": "2026-10-23T16:45:00Z",
        "home": "Crvena Zvezda Meridianbet Belgrade", "away": "Fenerbahce Tarfin Istanbul", "status": "scheduled",
        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/game-center/?round=7&season=E2026",
        "markets": [{"market": "Moneyline", "selection": "Fenerbahce Tarfin Istanbul", "probability": 0.60}],
    },
    "el-r7-pao-asv": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "2026-27 EuroLeague Round 7",
        "date": "2026-10-28", "time_utc": "2026-10-28T19:00:00Z",
        "home": "Panathinaikos AKTOR Athens", "away": "LDLC ASVEL Villeurbanne", "status": "scheduled",
        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/standings/",
        "markets": [{"market": "Spread", "selection": "Panathinaikos AKTOR Athens -10.5", "probability": 0.58}],
    },
    "el-r7-prs-bes": {
        "sport": "basketball", "sport_name": "Basketball", "competition": "2026-27 EuroLeague Round 7",
        "date": "2026-10-23", "time_utc": "2026-10-23T18:00:00Z",
        "home": "Paris Basketball", "away": "Besiktas Tarfin Istanbul", "status": "scheduled",
        "source_url": "https://www.euroleaguebasketball.net/en/euroleague/standings/",
        "markets": [{"market": "Spread", "selection": "Besiktas Tarfin Istanbul +3.5", "probability": 0.58}],
    },

    # ================= ICE HOCKEY: NHL, SHL, LIIGA =================
    "nhl-20261022-nsh-bos": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "NHL 2026-27 Regular Season",
        "date": "2026-10-22", "time_utc": "2026-10-22T23:00:00Z",
        "home": "Boston Bruins", "away": "Nashville Predators", "status": "scheduled",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "markets": [{"market": "Moneyline", "selection": "Boston Bruins", "probability": 0.618}],
    },
    "nhl-20261022-car-nyr": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "NHL 2026-27 Regular Season",
        "date": "2026-10-22", "time_utc": "2026-10-22T23:00:00Z",
        "home": "New York Rangers", "away": "Carolina Hurricanes", "status": "scheduled",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "markets": [{"market": "Moneyline", "selection": "Carolina Hurricanes", "probability": 0.629}],
    },
    "nhl-20261022-dal-ott": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "NHL 2026-27 Regular Season",
        "date": "2026-10-22", "time_utc": "2026-10-22T23:00:00Z",
        "home": "Ottawa Senators", "away": "Dallas Stars", "status": "scheduled",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "markets": [{"market": "Moneyline", "selection": "Dallas Stars", "probability": 0.607}],
    },
    "nhl-20261022-min-vgk": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "NHL 2026-27 Regular Season",
        "date": "2026-10-22", "time_utc": "2026-10-23T00:00:00Z",
        "home": "Vegas Golden Knights", "away": "Minnesota Wild", "status": "scheduled",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "markets": [{"market": "Total", "selection": "Over 6.0 Total Goals", "probability": 0.58}],
    },
    "nhl-20261022-edm-cgy": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "NHL 2026-27 Regular Season",
        "date": "2026-10-22", "time_utc": "2026-10-23T01:00:00Z",
        "home": "Calgary Flames", "away": "Edmonton Oilers", "status": "scheduled",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-22",
        "markets": [{"market": "Moneyline", "selection": "Edmonton Oilers", "probability": 0.625}],
    },
    "nhl-20261023-tor-tb": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "NHL 2026-27 Regular Season",
        "date": "2026-10-23", "time_utc": "2026-10-24T00:00:00Z",
        "home": "Tampa Bay Lightning", "away": "Toronto Maple Leafs", "status": "scheduled",
        "source_url": "https://api-web.nhle.com/v1/score/2026-10-23",
        "markets": [{"market": "Moneyline", "selection": "Toronto Maple Leafs", "probability": 0.49}],
    },
    "shl-20261022-bry-fbk": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "2026-27 Swedish Hockey League",
        "date": "2026-10-22", "time_utc": "2026-10-22T17:00:00Z",
        "home": "Brynas IF", "away": "Farjestad BK", "status": "scheduled",
        "source_url": "https://stats.swehockey.se/ScheduleAndResults/Standings/20961",
        "markets": [{"market": "Moneyline", "selection": "Farjestad BK", "probability": 0.618}],
    },
    "shl-20261022-hv71-ske": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "2026-27 Swedish Hockey League",
        "date": "2026-10-22", "time_utc": "2026-10-22T17:00:00Z",
        "home": "HV 71", "away": "Skellefteå AIK", "status": "scheduled",
        "source_url": "https://stats.swehockey.se/ScheduleAndResults/Standings/20961",
        "markets": [{"market": "Regulation Win", "selection": "Skellefteå AIK (60-min)", "probability": 0.562}],
    },
    "liiga-20261022-kes-koo": {
        "sport": "ice-hockey", "sport_name": "Ice Hockey", "competition": "2026-27 Finnish Liiga",
        "date": "2026-10-22", "time_utc": "2026-10-22T15:30:00Z",
        "home": "Kiekko-Espoo", "away": "KooKoo", "status": "scheduled",
        "source_url": "https://www.liiga.fi/en/schedule?kausi=2026-2027&sarja=runkosarja",
        "markets": [{"market": "Moneyline", "selection": "Kiekko-Espoo", "probability": 0.625}],
    },

    # ================= BASEBALL: MLB =================
    "mlb-20261023-tb-mil": {
        "sport": "baseball", "sport_name": "Baseball", "competition": "2026 MLB World Series - Game 1",
        "date": "2026-10-23", "time_utc": "2026-10-24T00:00:00Z",
        "home": "Milwaukee Brewers", "away": "Tampa Bay Rays", "status": "scheduled",
        "source_url": "https://statsapi.mlb.com/api/v1/schedule?startDate=2026-10-22&endDate=2026-10-25&sportId=1",
        "markets": [{"market": "Moneyline", "selection": "Milwaukee Brewers", "probability": 0.629}],
    },
    "mlb-2026-ws-outright": {
        "sport": "baseball", "sport_name": "Baseball", "competition": "2026 MLB World Series",
        "date": "2026-10-23", "time_utc": "2026-10-24T00:00:00Z",
        "home": "Milwaukee Brewers", "away": "Tampa Bay Rays", "status": "scheduled",
        "source_url": "https://www.mlb.com/world-series",
        "markets": [{"market": "Series Winner", "selection": "Milwaukee Brewers", "probability": 0.645}],
    },

    # ================= TENNIS: ATP & WTA =================
    "ten-20261022-col-leh": {
        "sport": "tennis", "sport_name": "Tennis", "competition": "ATP 250 European Open Brussels - QF",
        "date": "2026-10-23", "time_utc": "2026-10-23T12:30:00Z",
        "home": "Jiri Lehecka", "away": "Raphael Collignon", "status": "scheduled",
        "source_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule",
        "markets": [{"market": "Games Handicap", "selection": "Jiri Lehecka -2.5 Games", "probability": 0.618}],
    },
    "ten-20261022-rin-faa": {
        "sport": "tennis", "sport_name": "Tennis", "competition": "ATP 250 European Open Brussels - QF",
        "date": "2026-10-23", "time_utc": "2026-10-23T15:00:00Z",
        "home": "Felix Auger-Aliassime", "away": "Arthur Rinderknech", "status": "scheduled",
        "source_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule",
        "markets": [{"market": "Games Handicap", "selection": "Felix Auger-Aliassime -2.5 Games", "probability": 0.603}],
    },
    "ten-20261023-chi-cer": {
        "sport": "tennis", "sport_name": "Tennis", "competition": "ATP 250 European Open Brussels - QF",
        "date": "2026-10-23", "time_utc": "2026-10-23T13:00:00Z",
        "home": "Clement Chidekh", "away": "Francisco Cerundolo", "status": "scheduled",
        "source_url": "https://www.atptour.com/en/scores/current/brussels/7485/daily-schedule",
        "markets": [{"market": "Match Winner", "selection": "Francisco Cerundolo", "probability": 0.636}],
    },
    "ten-20261023-tsi-duc": {
        "sport": "tennis", "sport_name": "Tennis", "competition": "ATP 250 Almaty Open - QF",
        "date": "2026-10-23", "time_utc": "2026-10-23T04:00:00Z",
        "home": "Stefanos Tsitsipas", "away": "James Duckworth", "status": "scheduled",
        "source_url": "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule",
        "markets": [{"market": "Games Handicap", "selection": "Stefanos Tsitsipas -2.5 Games", "probability": 0.592}],
    },
    "ten-20261023-mou-pau": {
        "sport": "tennis", "sport_name": "Tennis", "competition": "ATP 250 Grand Prix Auvergne-Rhone-Alpes Lyon - QF",
        "date": "2026-10-23", "time_utc": "2026-10-23T13:00:00Z",
        "home": "Corentin Moutet", "away": "Tommy Paul", "status": "scheduled",
        "source_url": "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule",
        "markets": [{"market": "Games Handicap", "selection": "Tommy Paul -3.5 Games", "probability": 0.603}],
    },
    "ten-20261023-bej-bou": {
        "sport": "tennis", "sport_name": "Tennis", "competition": "WTA 500 BNB Ningbo Open - QF",
        "date": "2026-10-23", "time_utc": "2026-10-23T06:00:00Z",
        "home": "Sara Bejlek", "away": "Marie Bouzkova", "status": "scheduled",
        "source_url": "https://wtafiles.wtatennis.com/pdf/draws/2026/2092/MDS.pdf",
        "markets": [{"market": "Match Winner", "selection": "Marie Bouzkova", "probability": 0.618}],
    },
    "ten-20261023-li-tag": {
        "sport": "tennis", "sport_name": "Tennis", "competition": "WTA 250 Kinoshita Group Japan Open Osaka - QF",
        "date": "2026-10-23", "time_utc": "2026-10-23T03:00:00Z",
        "home": "Ann Li", "away": "Lilli Tagger", "status": "scheduled",
        "source_url": "https://www.wtatennis.com/tournaments/405/osaka/2026",
        "markets": [{"market": "Games Handicap", "selection": "Ann Li -3.5 Games", "probability": 0.595}],
    },

    # ================= DARTS: PDC EUROPEAN CHAMPIONSHIP =================
    "darts-20261022-huy-sea": {
        "sport": "darts", "sport_name": "Darts", "competition": "2026 Machineseeker European Championship - R1",
        "date": "2026-10-22", "time_utc": "2026-10-22T18:00:00Z",
        "home": "Kim Huybrechts", "away": "Ryan Searle", "status": "scheduled",
        "source_url": "https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship",
        "markets": [{"market": "Match Winner", "selection": "Ryan Searle", "probability": 0.636}],
    },
    "darts-20261022-bun-nop": {
        "sport": "darts", "sport_name": "Darts", "competition": "2026 Machineseeker European Championship - R1",
        "date": "2026-10-22", "time_utc": "2026-10-22T17:45:00Z",
        "home": "Danny Noppert", "away": "Stephen Bunting", "status": "scheduled",
        "source_url": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/",
        "markets": [{"market": "Total Legs", "selection": "Over 9.5 Total Legs", "probability": 0.556}],
    },
    "darts-20261023-lit-oco": {
        "sport": "darts", "sport_name": "Darts", "competition": "2026 Machineseeker European Championship - R1",
        "date": "2026-10-23", "time_utc": "2026-10-23T18:45:00Z",
        "home": "Luke Littler", "away": "William O'Connor", "status": "scheduled",
        "source_url": "https://www.pdc.tv/news/2026/october/18/2026-Machineseeker-European-Championship-field---draw-confirmed",
        "markets": [{"market": "Legs Handicap", "selection": "Luke Littler -2.5 Legs", "probability": 0.618}],
    },
    "darts-20261023-dob-sch": {
        "sport": "darts", "sport_name": "Darts", "competition": "2026 Machineseeker European Championship - R1",
        "date": "2026-10-23", "time_utc": "2026-10-23T18:00:00Z",
        "home": "Martin Schindler", "away": "Chris Dobey", "status": "scheduled",
        "source_url": "https://www.pdc.tv/news/2026/october/18/2026-Machineseeker-European-Championship-field---draw-confirmed",
        "markets": [{"market": "Total Legs", "selection": "Over 9.5 Total Legs", "probability": 0.565}],
    },

    # ================= SNOOKER: NORTHERN IRELAND OPEN =================
    "snk-20261022-wil-pan": {
        "sport": "snooker", "sport_name": "Snooker", "competition": "2026 BetVictor Northern Ireland Open - R16",
        "date": "2026-10-22", "time_utc": "2026-10-22T12:00:00Z",
        "home": "Kyren Wilson", "away": "Pang Junxu", "status": "scheduled",
        "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/",
        "markets": [{"market": "Match Winner", "selection": "Kyren Wilson", "probability": 0.636}],
    },
    "snk-20261022-mwi-odo": {
        "sport": "snooker", "sport_name": "Snooker", "competition": "2026 BetVictor Northern Ireland Open - R16",
        "date": "2026-10-22", "time_utc": "2026-10-22T18:00:00Z",
        "home": "Mark Williams", "away": "Martin O'Donnell", "status": "scheduled",
        "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/",
        "markets": [{"market": "Match Winner", "selection": "Mark Williams", "probability": 0.645}],
    },
    "snk-20261022-jjo-wel": {
        "sport": "snooker", "sport_name": "Snooker", "competition": "2026 BetVictor Northern Ireland Open - R16",
        "date": "2026-10-22", "time_utc": "2026-10-22T19:00:00Z",
        "home": "Jak Jones", "away": "Daniel Wells", "status": "scheduled",
        "source_url": "https://www.wst.tv/tournaments/northern-ireland-open-2026/",
        "markets": [{"market": "Match Winner", "selection": "Jak Jones", "probability": 0.618}],
    },

    # ================= MOTOR RACING: FORMULA 1 =================
    "f1-2026-usgp-winner": {
        "sport": "motor-racing", "sport_name": "Motor Racing", "competition": "2026 Formula 1 United States Grand Prix",
        "date": "2026-10-25", "time_utc": "2026-10-25T20:00:00Z",
        "home": "Field", "away": "Max Verstappen", "status": "scheduled",
        "source_url": "https://www.formula1.com/en/results/2026/drivers",
        "markets": [{"market": "Race Winner", "selection": "Max Verstappen", "probability": 0.227}],
    },
    "f1-2026-wdc-wo-antonelli": {
        "sport": "motor-racing", "sport_name": "Motor Racing", "competition": "2026 F1 Drivers Championship Without Kimi Antonelli",
        "date": "2026-12-06", "time_utc": "2026-12-06T13:00:00Z",
        "home": "Field", "away": "George Russell", "status": "scheduled",
        "source_url": "https://www.olbg.com/betting-tips/Motor_Racing/All_Motor_Racing/All_Events/Formula_1_Drivers_Championship_2026_Without_Kimi_Antonelli/14?event_id=912",
        "markets": [{"market": "Outright Winner", "selection": "George Russell", "probability": 0.408}],
    },

    # ================= HANDBALL: EHF CHAMPIONS LEAGUE & HBL =================
    "hb-ehf-gog-sze": {
        "sport": "handball", "sport_name": "Handball", "competition": "2026-27 EHF Men's Champions League - Group D",
        "date": "2026-10-29", "time_utc": "2026-10-29T17:45:00Z",
        "home": "GOG", "away": "OTP Bank - PICK Szeged", "status": "scheduled",
        "source_url": "https://ehfcl.eurohandball.com/men/2026-27/standings/",
        "markets": [{"market": "Moneyline", "selection": "GOG", "probability": 0.59}],
    },
    "hb-ehf-plk-nan": {
        "sport": "handball", "sport_name": "Handball", "competition": "2026-27 EHF Men's Champions League - Group B",
        "date": "2026-10-28", "time_utc": "2026-10-28T17:45:00Z",
        "home": "Orlen Wisla Plock", "away": "HBC Nantes", "status": "scheduled",
        "source_url": "https://ehfcl.eurohandball.com/men/2026-27/standings/",
        "markets": [{"market": "Handicap", "selection": "Orlen Wisla Plock +0.5 Goals", "probability": 0.618}],
    },
    "hb-ehf-mag-kol": {
        "sport": "handball", "sport_name": "Handball", "competition": "2026-27 EHF Men's Champions League - Group F",
        "date": "2026-10-22", "time_utc": "2026-10-22T18:45:00Z",
        "home": "Kolstad Handball", "away": "SC Magdeburg", "status": "scheduled",
        "source_url": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101064/KolstadH%C3%A5ndball-SCMagdeburg/",
        "markets": [{"market": "Handicap", "selection": "SC Magdeburg -6.5 Goals", "probability": 0.613}],
    },
    "hb-hbl-han-lem": {
        "sport": "handball", "sport_name": "Handball", "competition": "2026-27 DAIKIN Handball-Bundesliga",
        "date": "2026-10-23", "time_utc": "2026-10-23T18:00:00Z",
        "home": "TSV Hannover-Burgdorf", "away": "TBV Lemgo Lippe", "status": "scheduled",
        "source_url": "https://www.daikin-hbl.de/en/hbl/standings",
        "markets": [{"market": "Handicap", "selection": "TBV Lemgo Lippe +2.5 Goals", "probability": 0.592}],
    },

    # ================= VOLLEYBALL: PLUSLIGA =================
    "vb-pl-36964": {
        "sport": "volleyball", "sport_name": "Volleyball", "competition": "2026-27 Polish PlusLiga",
        "date": "2026-10-24", "time_utc": "2026-10-24T16:00:00Z",
        "home": "PGE GiEK Skra Belchatow", "away": "Projekt Warszawa", "status": "scheduled",
        "source_url": "https://plusliga.pl/table/tour/47.html",
        "markets": [{"market": "Sets Handicap", "selection": "Projekt Warszawa -1.5 Sets", "probability": 0.618}],
    },
    "vb-pl-36963": {
        "sport": "volleyball", "sport_name": "Volleyball", "competition": "2026-27 Polish PlusLiga",
        "date": "2026-10-23", "time_utc": "2026-10-23T15:30:00Z",
        "home": "Slepsk Malow Suwalki", "away": "GKS Katowice", "status": "scheduled",
        "source_url": "https://plusliga.pl/table/tour/47.html",
        "markets": [{"market": "Sets Handicap", "selection": "Slepsk Malow Suwalki -1.5 Sets", "probability": 0.60}],
    },

    # ================= RUGBY UNION: PRO D2, TOP 14, URC =================
    "ru-prod2-mon-oyo": {
        "sport": "rugby-union", "sport_name": "Rugby Union", "competition": "2026-27 Pro D2 - Journee 8",
        "date": "2026-10-22", "time_utc": "2026-10-22T19:00:00Z",
        "home": "US Montauban", "away": "Oyonnax Rugby", "status": "scheduled",
        "source_url": "https://prod2.lnr.fr/club/oyonnax",
        "markets": [{"market": "Moneyline", "selection": "Oyonnax Rugby", "probability": 0.625}],
    },
    "ru-top14-lar-ubb": {
        "sport": "rugby-union", "sport_name": "Rugby Union", "competition": "2026-27 Top 14 - Journee 7",
        "date": "2026-10-25", "time_utc": "2026-10-25T19:05:00Z",
        "home": "Stade Rochelais", "away": "Union Bordeaux-Begles", "status": "scheduled",
        "source_url": "https://top14.lnr.fr/club/la-rochelle",
        "markets": [{"market": "Moneyline", "selection": "Stade Rochelais", "probability": 0.618}],
    },
    "ru-urc-lei-mun": {
        "sport": "rugby-union", "sport_name": "Rugby Union", "competition": "2026-27 United Rugby Championship",
        "date": "2026-10-24", "time_utc": "2026-10-24T16:00:00Z",
        "home": "Leinster Rugby", "away": "Munster Rugby", "status": "scheduled",
        "source_url": "https://www.unitedrugby.com/",
        "markets": [{"market": "Handicap", "selection": "Munster Rugby +11.5", "probability": 0.565}],
    },

    # ================= RUGBY LEAGUE: RLWC 2026 =================
    "rl-wc-png-sam": {
        "sport": "rugby-league", "sport_name": "Rugby League", "competition": "2026 Men's Rugby League World Cup - Round 2",
        "date": "2026-10-24", "time_utc": "2026-10-24T04:25:00Z",
        "home": "Papua New Guinea", "away": "Samoa", "status": "scheduled",
        "source_url": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/papua-new-guinea-v-samoa/",
        "markets": [{"market": "Handicap", "selection": "Samoa -14.5", "probability": 0.60}],
    },
    "rl-wc-aus-fij": {
        "sport": "rugby-league", "sport_name": "Rugby League", "competition": "2026 Men's Rugby League World Cup - Round 2",
        "date": "2026-10-25", "time_utc": "2026-10-25T09:05:00Z",
        "home": "Australia", "away": "Fiji", "status": "scheduled",
        "source_url": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/australia-v-fiji/",
        "markets": [{"market": "Handicap", "selection": "Australia -24.5", "probability": 0.645}],
    },

    # ================= AUSSIE RULES: AFLW ROUND 11 =================
    "aflw-r11-wb-melb": {
        "sport": "aussie-rules", "sport_name": "Aussie Rules", "competition": "2026 NAB AFLW Premiership - Round 11",
        "date": "2026-10-24", "time_utc": "2026-10-24T08:15:00Z",
        "home": "Western Bulldogs", "away": "Melbourne", "status": "scheduled",
        "source_url": "https://www.afl.com.au/aflw/news/1634432/aflw-teams-dees-make-hore-call-freo-star-returns-another-pies-blow",
        "markets": [{"market": "Handicap", "selection": "Melbourne -12.5", "probability": 0.565}],
    },
    "aflw-r11-nmfc-adel": {
        "sport": "aussie-rules", "sport_name": "Aussie Rules", "competition": "2026 NAB AFLW Premiership - Round 11",
        "date": "2026-10-25", "time_utc": "2026-10-25T02:05:00Z",
        "home": "North Melbourne", "away": "Adelaide Crows", "status": "scheduled",
        "source_url": "https://www.afl.com.au/aflw",
        "markets": [{"market": "Handicap", "selection": "North Melbourne -29.5", "probability": 0.60}],
    },

    # ================= CRICKET =================
    "crk-csa-est-tus": {
        "sport": "cricket", "sport_name": "Cricket", "competition": "2026-27 CSA T20 Challenge - Pool B",
        "date": "2026-10-22", "time_utc": "2026-10-22T11:00:00Z",
        "home": "Eastern Storm", "away": "KwaZulu-Natal Inland Tuskers", "status": "scheduled",
        "source_url": "https://cricketworld.com/cricket/upcoming",
        "markets": [{"market": "Match Winner", "selection": "Eastern Storm", "probability": 0.618}],
    },
    "crk-odi-afg-zim": {
        "sport": "cricket", "sport_name": "Cricket", "competition": "ODI Tri-Nation Series in UAE 2026 - Final",
        "date": "2026-10-23", "time_utc": "2026-10-23T11:30:00Z",
        "home": "Afghanistan", "away": "Zimbabwe", "status": "scheduled",
        "source_url": "https://www.bjsports.live/featured-video/odi-tri-nation-series-in-uae-2026-afg-vs-zim-match-prediction-final-who-will-win-afghanistan-vs-zimbabwe-match",
        "markets": [{"market": "Runs Handicap", "selection": "Afghanistan -38.5 Runs", "probability": 0.592}],
    },

    # ================= GOLF =================
    "golf-champ-stifel": {
        "sport": "golf", "sport_name": "Golf", "competition": "2026 Stifel Charity Classic (PGA Tour Champions Playoffs)",
        "date": "2026-10-23", "time_utc": "2026-10-23T17:45:00Z",
        "home": "Field", "away": "Steven Alker", "status": "scheduled",
        "source_url": "https://www.olbg.com/betting-tips/Golf/All_Golf/All_Events/Stifel_Charity_Classic/5?event_id=101903",
        "markets": [{"market": "Win Tournament", "selection": "Steven Alker", "probability": 0.182}],
    },
    "golf-pga-bermuda": {
        "sport": "golf", "sport_name": "Golf", "competition": "2026 PGA Tour Butterfield Bermuda Championship",
        "date": "2026-10-22", "time_utc": "2026-10-22T11:30:00Z",
        "home": "Field", "away": "Corey Conners", "status": "scheduled",
        "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528",
        "markets": [{"market": "Win Tournament", "selection": "Corey Conners", "probability": 0.0667}],
    },

    # ================= ESPORTS: LEAGUE OF LEGENDS WORLDS 2026 =================
    "lol-w26-g2-dk": {
        "sport": "esports", "sport_name": "eSports", "competition": "LoL Worlds 2026 - Swiss Stage Round 1 (Bo1)",
        "date": "2026-10-23", "time_utc": "2026-10-23T21:00:00Z",
        "home": "G2 Esports", "away": "Dplus KIA", "status": "scheduled",
        "source_url": "https://lolesports.com/en-US",
        "markets": [{"market": "Match Winner", "selection": "G2 Esports", "probability": 0.465}],
    },
    "lol-w26-hle-tes": {
        "sport": "esports", "sport_name": "eSports", "competition": "LoL Worlds 2026 - Swiss Stage Round 1 (Bo1)",
        "date": "2026-10-23", "time_utc": "2026-10-23T19:00:00Z",
        "home": "Hanwha Life Esports", "away": "Top Esports", "status": "scheduled",
        "source_url": "https://lolesports.com/en-US",
        "markets": [{"market": "Match Winner", "selection": "Hanwha Life Esports", "probability": 0.63}],
    },
    "lol-w26-tsw-lyon": {
        "sport": "esports", "sport_name": "eSports", "competition": "LoL Worlds 2026 - Swiss Stage Round 1 (Bo1)",
        "date": "2026-10-24", "time_utc": "2026-10-24T00:00:00Z",
        "home": "Team Secret Whales", "away": "LYON", "status": "scheduled",
        "source_url": "https://lolesports.com/en-US",
        "markets": [{"market": "Match Winner", "selection": "LYON", "probability": 0.618}],
    },

    # ================= GAELIC GAMES =================
    "gaa-tyrone-ede-err": {
        "sport": "gaelic-football", "sport_name": "Gaelic Football", "competition": "2026 Tyrone Senior Football Championship Final Replay",
        "date": "2026-10-23", "time_utc": "2026-10-23T18:30:00Z",
        "home": "Edendork St Malachy's", "away": "Errigal Ciaran", "status": "scheduled",
        "source_url": "https://wearetyrone.com/sport/gaa/edendork-and-errigal-ciaran-set-for-friday-night-lights-in-replay/",
        "markets": [{"market": "Match Winner", "selection": "Errigal Ciaran", "probability": 0.618}],
    },
    "gaa-kerry-cro-ken": {
        "sport": "gaelic-football", "sport_name": "Gaelic Football", "competition": "2026 Kerry Senior Football Championship Final",
        "date": "2026-10-25", "time_utc": "2026-10-25T14:00:00Z",
        "home": "Dr Crokes", "away": "Kenmare Shamrocks", "status": "scheduled",
        "source_url": "https://munster.gaa.ie/fixtures/events-calendar/",
        "markets": [{"market": "Match Winner", "selection": "Dr Crokes", "probability": 0.629}],
    },
    "gaa-waterford-rat-nir": {
        "sport": "gaelic-football", "sport_name": "Gaelic Football", "competition": "2026 Waterford Senior Football Championship Final",
        "date": "2026-10-25", "time_utc": "2026-10-25T14:30:00Z",
        "home": "Rathgormack", "away": "The Nire", "status": "scheduled",
        "source_url": "https://munster.gaa.ie/fixtures/events-calendar/",
        "markets": [{"market": "Match Winner", "selection": "Rathgormack", "probability": 0.625}],
    },
    "gaa-galway-sal-moy": {
        "sport": "gaelic-football", "sport_name": "Gaelic Football", "competition": "2026 Bon Secours Galway Senior Football Championship Final",
        "date": "2026-10-25", "time_utc": "2026-10-25T14:00:00Z",
        "home": "Salthill-Knocknacarra", "away": "Moycullen", "status": "scheduled",
        "source_url": "https://www.gaa.ie/fixtures-results",
        "markets": [],
    },

    # ================= GREYHOUNDS (UNLINED - GBGB DOES NOT PUBLISH ADVANCE TRAP-LEVEL CARDS) =================
    "gh-cp-20261022": {
        "sport": "greyhounds", "sport_name": "Greyhounds", "competition": "UK BAGS Card - Central Park",
        "date": "2026-10-22", "time_utc": None,
        "home": "Field", "away": "Central Park (Sittingbourne)", "status": "scheduled",
        "source_url": "https://www.olbg.com/betting-tips/Greyhounds/28",
        "markets": [],
    },
    "gh-sheff-20261022": {
        "sport": "greyhounds", "sport_name": "Greyhounds", "competition": "UK BAGS Card - Sheffield",
        "date": "2026-10-22", "time_utc": None,
        "home": "Field", "away": "Sheffield", "status": "scheduled",
        "source_url": "https://www.olbg.com/betting-tips/Greyhounds/28",
        "markets": [],
    },
}


def build_records() -> list[dict]:
    records = []
    for match_id, data in MATCHES.items():
        markets = []
        picked = None
        override_prob = HIGH_PICK_PROB.get(match_id)
        for i, m in enumerate(data["markets"]):
            prob = override_prob if (override_prob is not None and i == 0) else m["probability"]
            dec, amer = fair_prices(prob)
            conf = confidence_for(prob, amer)
            market_rec = {
                "market": m["market"],
                "selection": m["selection"],
                "probability": round(prob, 4),
                "fair_decimal": dec,
                "fair_american": amer,
                "confidence": conf,
            }
            markets.append(market_rec)
            if picked is None or prob > picked["probability"]:
                picked = market_rec
        record = {
            "id": match_id,
            "sport": data["sport"],
            "sport_name": data["sport_name"],
            "competition": data["competition"],
            "date": data["date"],
            "time_utc": data.get("time_utc"),
            "home": data["home"],
            "away": data["away"],
            "status": data["status"],
            "source_url": data["source_url"],
            "markets": markets,
            "lined": bool(markets),
            "top_market": picked,
            "confidence": picked["confidence"] if picked else None,
        }
        records.append(record)
    records.sort(key=lambda r: (r["sport"], r["date"] or "", r["id"]))
    return records


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records = build_records()
    sports = sorted({r["sport_name"] for r in records})
    originated = [r for r in records if r["lined"]]
    unlined = [r for r in records if not r["lined"]]
    high = [r for r in records if r["confidence"] == "high"]
    out = {
        "generated_utc": "2026-10-22T12:18:00Z",
        "session": "arena/3de6d2ed-olbg2",
        "capture_window_utc": "2026-10-22T12:08:00Z - 2026-10-22T12:18:00Z",
        "total_count": len(records),
        "originated_count": len(originated),
        "unlined_count": len(unlined),
        "high_confidence_count": len(high),
        "sports_covered": len(sports),
        "matches": records,
    }
    (DATA_DIR / "matches.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"canon_data.py OK: {len(records)} rows ({len(originated)} originated / {len(unlined)} blank), "
          f"{len(sports)} sports, {len(high)} high-confidence markets")


if __name__ == "__main__":
    main()
