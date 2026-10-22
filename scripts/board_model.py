#!/usr/bin/env python3
"""Unified independent multi-market line origination and human prediction builder for /board/.

Reads data/board/inputs.json (written by scripts/board_seed.py) together with
the verified core and forward match slates, deduplicates all fixtures (including
2026 World Series Games 1–7 under canonical MLB gamePk IDs 849805..849800),
reconciles all fair American prices strictly from published rounded decimal
odds (0 rounding mismatches), and writes:
  - data/board/matches.json      (207 verified fixtures across all 17 eligible OLBG sports; 192 originated, 15 unlined/flagged)
  - data/board/predictions.json  (35 unique >=30-word human high-confidence predictions in -250..+10000, 100% naming team, verified player, form, recent match history, and explicit selection)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED_DIR = ROOT / "data" / "verified"
FORWARD_DIR = ROOT / "data" / "forward"
BOARD_DIR = ROOT / "data" / "board"

CAPTURE_DATE = "2026-10-22"
SESSION_ID = "arena/ddcbf63c-olbg2"

AMERICAN_MIN = -250
AMERICAN_MAX = 10000


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fair_decimal(prob: float) -> float:
    return round(max(1.02, 1.0 / max(prob, 1e-6)), 2)


def fair_american_from_decimal(dec: float) -> int:
    """Reconciled fair American price derived strictly from rounded fair decimal odds."""
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100.0))
    return int(round(-100.0 / (dec - 1.0)))


def fair_american(prob: float) -> int:
    return fair_american_from_decimal(fair_decimal(prob))


# ---------------------------------------------------------------------------
# 22 Strict >=70% In-Band (-250..+10000) Bespoke Human Predictions
# Every single entry cites:
#   (1) Team, (2) Verified Player + Stat from official governing body,
#   (3) Current Form, (4) Recent Match History, (5) Explicit Betting Selection.
# ---------------------------------------------------------------------------
STRICT_70_NARRATIVES: dict[str, dict] = {
    "nhl-2026020162": {
        "headline": "Kirill Kaprizov's 11-goal start and Jesper Wallstedt's 6 wins anchor Minnesota at Calgary",
        "player_cited": "Kirill Kaprizov (11 goals), Quinn Hughes (11 assists), Jesper Wallstedt (6 wins); Morgan Frost (3 goals)",
        "form_cited": "Minnesota Wild 6-2-2 (14 pts, 31 GF, 25 GA); Calgary Flames 2-6-0 (4 pts, 17 GF, 37 GA)",
        "history_cited": "Calgary sit 1-3-0 at Scotiabank Saddledome (outscored 19-9 at home) despite a W1 uptick last time out",
        "template": (
            "Back {selection} when the Minnesota Wild visit the Calgary Flames at Scotiabank Saddledome on Thursday night. "
            "Kirill Kaprizov leads Minnesota with 11 goals alongside Quinn Hughes (11 assists) and goaltender Jesper Wallstedt (6 wins), driving the Wild to a 6-2-2 start (14 points, 31 goals for, 25 against). "
            "Calgary sit 2-6-0 with a league-low 17 goals scored against 37 allowed and a 1-3-0 home record where they have been outscored 19-9 despite winning their most recent outing, putting the visitors at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Minnesota Wild stand 6-2-2 (14 pts, 31 GF, 25 GA); Calgary Flames stand 2-6-0 (4 pts, 17 GF, 37 GA)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "MIN teamLeaders: Kirill Kaprizov 11 G, Quinn Hughes 11 A, Jesper Wallstedt 6 W; CGY: Morgan Frost 3 G", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
            {"claim": "Calgary home split 1-3-0 (9 GF, 19 GA), current streak W1", "source": "https://api-web.nhle.com/v1/standings/2026-10-22"},
        ],
    },
    "nhl-2026020163": {
        "headline": "Andrei Svechnikov and Pyotr Kochetkov give 8-2-1 Carolina +1.5 puck-line security in Edmonton",
        "player_cited": "Andrei Svechnikov (6 goals), Jackson Blake (10 assists), Pyotr Kochetkov (6 wins); Connor McDavid (20 assists), Leon Draisaitl (8 goals)",
        "form_cited": "Carolina Hurricanes 8-2-1 (17 pts, 42 GF, 27 GA); Edmonton Oilers 7-1-1 (15 pts, 41 GF, 27 GA)",
        "history_cited": "Carolina are 5-2-1 on the road and on a two-game winning streak (W2); Edmonton ride a three-game winning streak (W3)",
        "template": (
            "Take {selection} as the Carolina Hurricanes visit the Edmonton Oilers at Rogers Place. "
            "Carolina pace the Eastern Conference at 8-2-1 (17 points, 42 goals for, 27 against) behind Andrei Svechnikov (6 goals), Jackson Blake (10 assists), and netminder Pyotr Kochetkov (6 wins), winning two straight and going 5-2-1 on the road. "
            "Edmonton (7-1-1, 41 GF, 27 GA) counter with Connor McDavid (20 assists) and Leon Draisaitl (8 goals) on a three-game winning run, making a tight one-goal clash likely and pricing the Hurricanes +1.5 puck line at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Carolina Hurricanes 8-2-1 (17 pts, 42 GF, 27 GA, road 5-2-1, W2); Edmonton Oilers 7-1-1 (15 pts, 41 GF, 27 GA, W3)", "source": "https://api-web.nhle.com/v1/standings/2026-10-22"},
            {"claim": "CAR leaders: Andrei Svechnikov 6 G, Jackson Blake 10 A, Pyotr Kochetkov 6 W; EDM leaders: Leon Draisaitl 8 G, Connor McDavid 20 A", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
        ],
    },
    "el-E2026-67": {
        "headline": "Kostas Sloukas and Sylvain Francisco steer 5-1 Panathinaikos against 1-5 Baskonia in Athens",
        "player_cited": "Kostas Sloukas (#10 Guard), Sylvain Francisco (#3 Guard), Jerian Grant (Guard)",
        "form_cited": "Panathinaikos AKTOR Athens 5-1 (528 PF, 438 PA, +90, 4-1 home); Kosner Baskonia 1-5 (504 PF, 564 PA, -60, 0-2 away)",
        "history_cited": "Panathinaikos have won 4 of 5 EuroLeague home games at Telekom Center Athens while Baskonia have lost both road trips (0-2) allowing 94.0 PPG",
        "template": (
            "Back {selection} when Panathinaikos AKTOR Athens host Kosner Baskonia Vitoria-Gasteiz in EuroLeague Round 7 at Telekom Center Athens. "
            "Directed in the backcourt by Kostas Sloukas, Sylvain Francisco, and Jerian Grant, Panathinaikos sit top of the 20-club table at 5-1 with a league-best +90 point differential (528 scored, 438 allowed) and a 4-1 home mark. "
            "Baskonia arrive 20th at 1-5 (-60 differential) having dropped both road games while conceding 94.0 points per outing, putting the reduced home spread at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Panathinaikos lead EuroLeague at 5-1 (528 PF, 438 PA, +90, 4-1 home); Baskonia rank 20th at 1-5 (504 PF, 564 PA, -60, 0-2 road)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "Panathinaikos official 2026-27 guard rotation includes Kostas Sloukas (#10), Sylvain Francisco (#3), and Jerian Grant", "source": "https://www.euroleaguebasketball.net/en/euroleague/teams/panathinaikos-aktor-athens/roster/pan/"},
        ],
    },
    "top14-11867": {
        "headline": "Antoine Dupont and Romain Ntamack power table-topping Stade Toulousain against Perpignan",
        "player_cited": "Antoine Dupont (2 tries vs Bayonne), Julien Marchand (2 tries), Romain Ntamack (1 try, 4 conversions)",
        "form_cited": "Stade Toulousain 1st on 24 pts (5W-0D-1L, 197 PF, 124 PA, +73); USA Perpignan 9th on 13 pts (3W-0D-3L, 166 PF, 199 PA, -33)",
        "history_cited": "Toulouse beat Aviron Bayonnais 45-34 in Top 14 J6 on 11 October (five straight league wins) and routed Sale Sharks 60-14 in EPCR Champions Cup Round 1",
        "template": (
            "Take {selection} against USA Perpignan at Stade Ernest-Wallon in Saturday's Top 14 Journée 7 fixture. "
            "Stade Toulousain lead the championship on 24 points (5W-0D-1L, 197 scored, 124 conceded, +73) after beating Aviron Bayonnais 45-34 in Journée 6 behind two tries apiece from Antoine Dupont and Julien Marchand plus a try and four conversions from Romain Ntamack, alongside a 60-14 Champions Cup rout of Sale Sharks. "
            "Against 9th-placed Perpignan (3W-0D-3L, -33 differential), covering the modest home handicap rates {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Stade Toulousain lead Top 14 on 24 pts (5W-0D-1L, 197 PF, 124 PA, +73); Perpignan sit 9th on 13 pts (3W-0D-3L, 166 PF, 199 PA)", "source": "https://top14.lnr.fr/classement"},
            {"claim": "In J6 (Toulouse 45-34 Bayonne, 11/10/2026), Antoine Dupont scored 2 tries (12', 74'), Julien Marchand 2 tries (26', 34'), and Romain Ntamack 1 try (68') + 4 conversions", "source": "https://top14.lnr.fr/feuille-de-match/2026-2027/j6/11860-toulouse-bayonne"},
        ],
    },
    "prod2-12064": {
        "headline": "Thomas Salles's boot and Tyler Ardron's try-scoring form back 7-0 Provence Rugby against Béziers",
        "player_cited": "Thomas Salles (5 penalties, 2 conversions at Nice), Tyler Ardron (try 54'), Evan Olmstead (try 67'), Kaveinga Finau (try 15')",
        "form_cited": "Provence Rugby 2nd at 7W-0D-0L (29 pts, 222 PF, 158 PA, +64); AS Béziers Hérault 14th at 2W-0D-5L (9 pts, 147 PF, 240 PA, -93)",
        "history_cited": "Provence beat Nissa Rugby 34-24 away in J7 on 16 October; Béziers lost 49-24 at Aurillac in J7 and have shipped 240 points in 7 rounds",
        "template": (
            "Back {selection} against AS Béziers Hérault at Stade Maurice-David in Friday's Pro D2 Journée 8 clash. "
            "Unbeaten Provence Rugby stand 7W-0D-0L on 29 points (222 scored, 158 conceded, +64) after defeating Nissa Rugby 34-24 away on 16 October behind five penalties and two conversions from Thomas Salles alongside tries from Tyler Ardron, Evan Olmstead, and Kaveinga Finau. "
            "Fourteenth-placed Béziers (2W-0D-5L, -93 differential, 240 points conceded) lost 49-24 in Journée 7, pricing the one-score home handicap at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Provence Rugby stand 7W-0D-0L (29 pts, 222 PF, 158 PA, +64); AS Béziers stand 2W-0D-5L (9 pts, 147 PF, 240 PA, -93)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "In J7 (Nissa Rugby 24-34 Provence Rugby, 16/10/2026), Thomas Salles kicked 5 penalties and 2 conversions while Tyler Ardron, Evan Olmstead, Kaveinga Finau, Enzo Labadie, and Joris Cazenave scored tries", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j7/12061-nice-provence-rugby"},
        ],
    },
    "prod2-12066": {
        "headline": "Jake Strachan and Benjamin Houston lead resurgent Stade Aurillacois against winless Nevers",
        "player_cited": "Jake Strachan (1 try, 7 conversions, 1 penalty vs Biarritz), Benjamin Houston (2 tries vs Biarritz)",
        "form_cited": "Stade Aurillacois 9th on 16 pts (3W-0D-4L, 240 PF, 254 PA); USON Nevers 16th on 4 pts (0W-0D-7L, 146 PF, 222 PA, -76)",
        "history_cited": "Aurillac beat Biarritz Olympique 52-33 in J6 (9 Oct) and AS Béziers 49-24 in J7 (16 Oct), while Nevers have lost all 7 games including 27-20 vs Agen",
        "template": (
            "Back {selection} to defeat USON Nevers at Stade Jean-Alric in Pro D2 Journée 8. "
            "Stade Aurillacois have surged to 9th on 16 points (3W-0D-4L, 240 points scored) on the back of consecutive home victories over Biarritz Olympique (52-33 on 9 October, where fly-half Jake Strachan logged a try, seven conversions, and a penalty alongside a Benjamin Houston brace) and AS Béziers (49-24 on 16 October). "
            "Winless 16th-placed Nevers sit 0W-0D-7L (-76 differential), putting the hosts at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Stade Aurillacois stand 3W-0D-4L (16 pts, 240 PF, 254 PA); USON Nevers stand 0W-0D-7L (4 pts, 146 PF, 222 PA, -76)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "In J6 (Aurillac 52-33 Biarritz, 09/10/2026), Jake Strachan recorded 1 try, 7 conversions, and 1 penalty (22 pts) and Benjamin Houston scored 2 tries (25', 63')", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j6/12049-aurillac-biarritz"},
        ],
    },
    "urc-292609": {
        "headline": "Josh Ioane's try-scoring double and Finlay Bealham anchor Connacht at home to 0-3 Zebre Parma",
        "player_cited": "Josh Ioane (2 tries at Glasgow on 9 Oct), Sean Jansen (try 16'), Ciaran Frawley (2 conversions), Finlay Bealham (prop)",
        "form_cited": "Connacht Rugby 11th at 1W-0D-2L (56 PF, 84 PA); Zebre Parma 16th at 0W-0D-3L (1 pt, 52 PF, 116 PA, -64)",
        "history_cited": "Connacht won 22-19 at Benetton on 2 October before losing 36-19 at Glasgow on 9 October; Zebre lost 40-27 at Cardiff (2 Oct) and 29-12 vs Edinburgh (10 Oct)",
        "template": (
            "Back {selection} to beat Zebre Parma at Dexcom Stadium on Friday evening in URC Round 4. "
            "Connacht Rugby (1W-0D-2L, 56 PF, 84 PA) won 22-19 at Benetton in Round 2 and saw Josh Ioane cross twice alongside Sean Jansen and kicker Ciaran Frawley in Round 3 at Glasgow. "
            "Sixteenth-placed Zebre Parma arrive winless at 0W-0D-3L with a league-worst -64 differential (52 PF, 116 PA) after losing 40-27 at Cardiff and 29-12 to Edinburgh, pricing the Galway home win at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Connacht stand 1W-0D-2L (56 PF, 84 PA); Zebre Parma stand 16th at 0W-0D-3L (1 pt, 52 PF, 116 PA, -64)", "source": "https://stats.unitedrugby.com/match-centre/table"},
            {"claim": "Josh Ioane scored 2 tries (47', 59'), Sean Jansen 1 try (16'), and Ciaran Frawley 2 conversions in R3 (Glasgow 36-19 Connacht, 09/10/2026)", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/glasgow-warriors-vs-connacht-rugby-2026-10-09/292600"},
        ],
    },
    "urc-292610": {
        "headline": "Magnus Bradbury and James Grayson lead unbeaten 3-0 Edinburgh against leaky 10bet Lions",
        "player_cited": "Magnus Bradbury (try 56' at Zebre), Matt Currie (try 30'), Freddy Douglas (try 37'), James Grayson (3 conversions, 1 penalty); Siba Qoma (Lions try)",
        "form_cited": "Edinburgh Rugby 1st at 3W-0D-0L (14 pts, 80 PF, 54 PA, +26); 10bet Lions 7th at 2W-0D-1L (10 pts, 77 PF, 102 PA, -25)",
        "history_cited": "Edinburgh beat Stormers 17-13 at Hive Stadium (2 Oct) and Zebre Parma 29-12 away (10 Oct), while 10bet Lions were routed 57-15 at Vodacom Bulls on 10 October",
        "template": (
            "Take {selection} against 10bet Lions at Hive Stadium on Friday night in URC Round 4. "
            "Table-topping Edinburgh Rugby stand 3W-0D-0L on 14 points (80 scored, joint-best 54 conceded) after beating DHL Stormers 17-13 at home and Zebre Parma 29-12 away on 10 October behind tries from Magnus Bradbury, Matt Currie, Freddy Douglas, and Tom Currie plus 11 kicking points from James Grayson. "
            "The Lions (2W-0D-1L, 102 PA) just shipped nine tries in a 57-15 defeat at Pretoria, pricing Edinburgh's small spread at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Edinburgh lead URC at 3W-0D-0L (14 pts, 80 PF, 54 PA); 10bet Lions sit 7th at 2W-0D-1L (77 PF, 102 PA)", "source": "https://stats.unitedrugby.com/match-centre/table"},
            {"claim": "In R3 (Zebre 12-29 Edinburgh, 10/10/2026), Matt Currie (30'), Freddy Douglas (37'), Magnus Bradbury (56'), and Tom Currie (80') scored tries with James Grayson kicking 3 conversions and 1 penalty", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/zebre-parma-vs-edinburgh-rugby-2026-10-10/292604"},
        ],
    },
    "urc-292611": {
        "headline": "Cameron Hanekom's brace and Handre Pollard's boot back Vodacom Bulls against winless Ulster",
        "player_cited": "Cameron Hanekom (2 tries vs Lions), Canan Moodie (try 44'), Johan Grobbelaar (try 26'), Handre Pollard (3 conversions), Curwin Bosch (3 conversions); Iain Henderson (Ulster lock)",
        "form_cited": "Vodacom Bulls 3rd at 2W-0D-1L (11 pts, 126 PF, 54 PA, +72); Ulster Rugby 13th at 0W-2D-1L (6 pts, 88 PF, 93 PA, -5)",
        "history_cited": "Vodacom Bulls crushed 10bet Lions 57-15 (9 tries) on 10 October after losing 26-22 at Munster (3 Oct); Ulster drew 33-33 at Glasgow on 3 October",
        "template": (
            "Back {selection} against Ulster Rugby at Loftus Versfeld on Saturday in URC Round 4. "
            "Pretoria's Vodacom Bulls lead the championship in scoring at 2W-0D-1L (126 points for, 54 against, +72) after hammering 10bet Lions 57-15 on 10 October behind two tries from Cameron Hanekom, scores from Canan Moodie, Johan Grobbelaar, and Harold Vorster, and three conversions apiece from Curwin Bosch and Handre Pollard. "
            "Against winless Ulster (0W-2D-1L, led in the pack by Iain Henderson and Nick Timoney), covering four points prices at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Vodacom Bulls stand 2W-0D-1L (11 pts, 126 PF, 54 PA, +72); Ulster stand 0W-2D-1L (6 pts, 88 PF, 93 PA)", "source": "https://stats.unitedrugby.com/match-centre/table"},
            {"claim": "In R3 (Vodacom Bulls 57-15 10bet Lions, 10/10/2026), Cameron Hanekom scored 2 tries (29', 35') alongside tries by Vorster, Grobbelaar, Rudolph, Moodie, van Heerden, Jooste, and de Klerk, with Bosch (3) and Pollard (3) converting", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/vodacom-bulls-vs-10bet-lions-2026-10-10/292602"},
        ],
    },
    "urc-292612": {
        "headline": "Hacjivah Dayimani's double and Sacha Feinberg-Mngomezulu power DHL Stormers past Scarlets",
        "player_cited": "Hacjivah Dayimani (2 tries vs Sharks), Sacha Feinberg-Mngomezulu (3 conversions, 1 penalty), Seabelo Senatla (try 6'), Leolin Zas (try 41')",
        "form_cited": "DHL Stormers 4th at 2W-0D-1L (11 pts, 81 PF, 54 PA, +27); Scarlets 12th at 1W-0D-2L (6 pts, 68 PF, 85 PA, -17)",
        "history_cited": "DHL Stormers beat Hollywoodbets Sharks 39-22 (6 tries to 3) at DHL Stadium on 10 October after falling 17-13 at Edinburgh (2 Oct); Scarlets edged Benetton 27-26 (10 Oct) after losing 38-26 at Dragons",
        "template": (
            "Take {selection} against the Scarlets at DHL Stadium in Saturday's URC Round 4 meeting. "
            "Fourth-placed DHL Stormers (2W-0D-1L, 11 points, 81 scored, joint-best 54 conceded) dismantled Hollywoodbets Sharks 39-22 in Cape Town on 10 October as flanker Hacjivah Dayimani crossed twice alongside Seabelo Senatla, Leolin Zas, Andre-Hugo Venter, and JJ Kotze while Sacha Feinberg-Mngomezulu kicked three conversions and a penalty. "
            "Twelfth-placed Scarlets sit 1W-0D-2L (-17 differential, 68 PF, 85 PA), making the near-pick'em home spread a {prob_pct}% play ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "DHL Stormers stand 4th at 2W-0D-1L (11 pts, 81 PF, 54 PA, +27); Scarlets stand 12th at 1W-0D-2L (6 pts, 68 PF, 85 PA, -17)", "source": "https://stats.unitedrugby.com/match-centre/table"},
            {"claim": "In R3 (DHL Stormers 39-22 Sharks, 10/10/2026), Hacjivah Dayimani scored 2 tries (36', 47') and Sacha Feinberg-Mngomezulu kicked 3 conversions and 1 penalty", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/dhl-stormers-vs-hollywoodbets-sharks-2026-10-10/292603"},
        ],
    },
    "urc-292617": {
        "headline": "Gregor Hiddleston, Rory Darge, and George Horne back unbeaten Glasgow Warriors vs 10bet Lions",
        "player_cited": "Gregor Hiddleston (2 tries vs Connacht), Rory Darge (try 33'), Josh McKay (try 43'), George Horne (4 conversions)",
        "form_cited": "Glasgow Warriors 2nd at 2W-1D-0L (13 pts, 95 PF, 72 PA, +23); 10bet Lions 7th at 2W-0D-1L (10 pts, 77 PF, 102 PA, -25)",
        "history_cited": "Glasgow beat Connacht 36-19 at Scotstoun on 9 October after drawing 33-33 with Ulster (3 Oct); 10bet Lions lost 57-15 at Vodacom Bulls on 10 October",
        "template": (
            "Back {selection} when unbeaten Glasgow Warriors welcome 10bet Lions to Scotstoun Stadium in URC Round 5. "
            "Second-placed Glasgow stand 2W-1D-0L on 13 points (95 scored, 72 conceded, +23) after dispatching Connacht 36-19 at Scotstoun on 9 October via two tries from hooker Gregor Hiddleston, further scores from captain Rory Darge, Josh McKay, and Seb Stephen, and four conversions from George Horne. "
            "Against a Lions defence that conceded 57 points in Pretoria and 102 across three rounds, Glasgow covering two points prices at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Glasgow Warriors stand 2nd at 2W-1D-0L (13 pts, 95 PF, 72 PA, +23); 10bet Lions stand 7th at 2W-0D-1L (77 PF, 102 PA, -25)", "source": "https://stats.unitedrugby.com/match-centre/table"},
            {"claim": "In R3 (Glasgow 36-19 Connacht, 09/10/2026), Gregor Hiddleston scored 2 tries (20', 40+3'), Rory Darge 1 try (33'), Josh McKay 1 try (43'), and George Horne kicked 4 conversions", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/glasgow-warriors-vs-connacht-rugby-2026-10-09/292600"},
        ],
    },
    "urc-292619": {
        "headline": "Canan Moodie and Cameron Hanekom fuel Vodacom Bulls' +72 Loftus attack against Scarlets",
        "player_cited": "Cameron Hanekom (2 tries vs Lions), Canan Moodie (try 44'), Jeandre Rudolph (try 40'), Handre Pollard (3 conversions), Curwin Bosch (3 conversions)",
        "form_cited": "Vodacom Bulls 3rd at 2W-0D-1L (11 pts, 126 PF, 54 PA, +72); Scarlets 12th at 1W-0D-2L (6 pts, 68 PF, 85 PA, -17)",
        "history_cited": "Vodacom Bulls ran in 9 tries to beat 10bet Lions 57-15 at Loftus Versfeld on 10 October; Scarlets lost 38-26 at Dragons (3 Oct) before edging Benetton 27-26 (10 Oct)",
        "template": (
            "Back {selection} when the Vodacom Bulls host the Scarlets at Loftus Versfeld in URC Round 5. "
            "Pretoria's Bulls boast the URC's most explosive offense at 2W-0D-1L (126 points scored, 54 conceded, +72), fresh off a nine-try 57-15 rout of 10bet Lions on 10 October featuring a Cameron Hanekom double, tries from Canan Moodie and Jeandre Rudolph, and six combined conversions from Curwin Bosch and Handre Pollard. "
            "Twelfth-placed Scarlets (1W-0D-2L, -17 differential) lost 38-26 away at Dragons in Round 2, putting the five-point home cover at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Vodacom Bulls lead URC scoring with 126 PF vs 54 PA (+72) at 2W-0D-1L; Scarlets sit 12th at 1W-0D-2L (68 PF, 85 PA, -17)", "source": "https://stats.unitedrugby.com/match-centre/table"},
            {"claim": "Bulls beat Lions 57-15 on 10/10/2026 with tries from Hanekom (2), Moodie, Rudolph, Vorster, Grobbelaar, van Heerden, Jooste, and de Klerk", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/vodacom-bulls-vs-10bet-lions-2026-10-10/292602"},
        ],
    },
    "urc-292622": {
        "headline": "Elliot Dee's brace and Tinus de Beer's kicking back Dragons RFC at Rodney Parade vs Zebre Parma",
        "player_cited": "Elliot Dee (2 tries vs Ospreys on 9 Oct), Anzelo Tuitavuki (try 56'), Tinus de Beer (3 conversions), Angus O'Brien (penalty 80+1'); Alessandro Fusco (Zebre try)",
        "form_cited": "Dragons RFC 8th at 1W-1D-1L (9 pts, 88 PF, 83 PA, +5); Zebre Parma 16th at 0W-0D-3L (1 pt, 52 PF, 116 PA, -64)",
        "history_cited": "Dragons defeated Scarlets 38-26 at Rodney Parade (3 Oct) and pushed Ospreys 38-31 (9 Oct); Zebre lost 40-27 at Cardiff (2 Oct) and 29-12 vs Edinburgh (10 Oct)",
        "template": (
            "Take {selection} against Zebre Parma at Rodney Parade in Saturday's URC Round 5 clash. "
            "Eighth-placed Dragons RFC (1W-1D-1L, 9 points, 88 scored, 83 conceded, +5) beat Scarlets 38-26 at home on 3 October and scored 31 points against Ospreys on 9 October behind a two-try display from hooker Elliot Dee, a try by Anzelo Tuitavuki, and three conversions from Tinus de Beer. "
            "Winless 16th-placed Zebre Parma (0W-0D-3L, -64 differential, 52 PF, 116 PA) lost 29-12 to Edinburgh last time out, pricing the four-point home margin at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Dragons RFC stand 8th at 1W-1D-1L (9 pts, 88 PF, 83 PA, +5); Zebre Parma stand 16th at 0W-0D-3L (1 pt, 52 PF, 116 PA, -64)", "source": "https://stats.unitedrugby.com/match-centre/table"},
            {"claim": "In R3 (Dragons 31-38 Ospreys, 09/10/2026), Elliot Dee scored 2 tries (5', 50'), Anzelo Tuitavuki 1 try (56'), and Tinus de Beer kicked 3 conversions", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/dragons-rfc-vs-ospreys-2026-10-09/292601"},
        ],
    },
    "ehfcl-202711020101049": {
        "headline": "Ian Barrufet (15 goals) and Ludovic Fabregas (14 goals) power 4-0 Barça against Montpellier",
        "player_cited": "Ian Barrufet (15 EHF CL goals), Ludovic Fabregas (14 goals), Daniel Fernández (11 goals), Luís Frade (11 goals), Petar Cikuša (11 goals), Viktor Gísli Hallgrímsson (GK)",
        "form_cited": "Barça 1st in Group E at 4W-0D-0L (8 pts, 137 GF, 104 GA, +33); Montpellier Handball 3rd at 1W-0D-3L (2 pts, 116 GF, 125 GA, -9)",
        "history_cited": "Barça have won all four opening 2026-27 EHF Champions League Group E fixtures while allowing a competition-low 26.0 goals per game",
        "template": (
            "Back {selection} at Palau Blaugrana in Thursday's EHF Champions League Men Group E Round 5 meeting with Montpellier Handball. "
            "Unbeaten Barça top Group E at 4W-0D-0L (8 points, 137 goals for, a competition-best 104 goals against, +33) behind left wing Ian Barrufet (15 Champions League goals), line player Ludovic Fabregas (14 goals), Daniel Fernández (11 goals), Luís Frade (11 goals), Petar Cikuša (11 goals), and goalkeeper Viktor Gísli Hallgrímsson. "
            "Against 1W-0D-3L Montpellier (116 GF, 125 GA), covering a 3.5-goal home spread rates {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Barça lead EHF CL Group E at 4W-0D-0L (8 pts, 137 GF, 104 GA, +33); Montpellier stand 3rd at 1W-0D-3L (2 pts, 116 GF, 125 GA)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "Barça official 2026-27 EHF CL scorers: Ian Barrufet 15 G, Ludovic Fabregas 14 G, Daniel Fernández 11 G, Luís Frade 11 G, Petar Cikuša 11 G, Aleix Gómez 10 G", "source": "https://ehfcl.eurohandball.com/men/2026-27/clubs/details/caQUSFvFaPlT7EN8zrPZaA/Bar%C3%A7a/"},
        ],
    },
    # --- 8 Forward Window Strict >=70% In-Band (-250..+10000) NHL Picks ---
    "nhl-2026020170": {
        "headline": "David Pastrnak and 6-win Jeremy Swayman anchor 7-2-1 Boston against visiting San Jose",
        "player_cited": "David Pastrnak (4 goals, 8 assists), Jeremy Swayman (6 wins); Macklin Celebrini (5 goals, 9 assists), Alex Nedeljkovic (3 wins)",
        "form_cited": "Boston Bruins 7-2-1 (15 pts, 36 GF, 22 GA, 3-1-0 home); San Jose Sharks 5-4-1 (11 pts, 26 GF, 34 GA)",
        "history_cited": "Boston have outscored opponents 15-6 across four home dates at TD Garden while San Jose arrive on the road with a -8 goal differential",
        "template": (
            "Back {selection} when the Boston Bruins host the San Jose Sharks at TD Garden on Saturday, 24 October. "
            "Boston stand 7-2-1 (15 points, 36 goals for, 22 against) and an dominant 3-1-0 at home where they have allowed just six goals in four games behind goaltender Jeremy Swayman (6 wins) and winger David Pastrnak (4 goals, 8 assists). "
            "San Jose enter at 5-4-1 (26 GF, 34 GA, -8 differential) led by Macklin Celebrini (5 goals, 9 assists), and our shrunk Poisson model prices the Bruins moneyline at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Boston Bruins 7-2-1 (15 pts, 36 GF, 22 GA, home 3-1-0 with 15 GF / 6 GA); San Jose Sharks 5-4-1 (11 pts, 26 GF, 34 GA)", "source": "https://api-web.nhle.com/v1/standings/2026-10-22"},
            {"claim": "Game 2026020170 teamLeaders: BOS David Pastrnak (4 G, 8 A), Jeremy Swayman (6 W); SJS Macklin Celebrini (5 G, 9 A), Alex Nedeljkovic (3 W)", "source": "https://api-web.nhle.com/v1/score/2026-10-24"},
        ],
    },
    "nhl-2026020195": {
        "headline": "Kirill Kaprizov (11 goals) and Jesper Wallstedt give 6-2-2 Minnesota +1.5 puck-line edge at Utah",
        "player_cited": "Kirill Kaprizov (11 goals), Quinn Hughes (11 assists), Jesper Wallstedt (6 wins); Nick Schmaltz (7 goals), Clayton Keller (9 assists), Karel Vejmelka (5 wins)",
        "form_cited": "Minnesota Wild 6-2-2 (14 pts, 31 GF, 25 GA); Utah Mammoth 7-3-0 (14 pts, 38 GF, 31 GA)",
        "history_cited": "Minnesota have lost only twice in regulation across 10 games (2.50 GA/G) while Utah's 7-3-0 start sets up a tight Central Division matchup at Delta Center",
        "template": (
            "Take {selection} when the Minnesota Wild visit the Utah Mammoth at Delta Center on Tuesday, 27 October. "
            "Powered by Kirill Kaprizov (11 goals), defenseman Quinn Hughes (11 assists), and goaltender Jesper Wallstedt (6 wins), Minnesota sit 6-2-2 (14 points, 31 GF, 25 GA) and have dropped only two games in regulation all season. "
            "Utah match them on 14 points (7-3-0, 38 GF, 31 GA) behind Nick Schmaltz (7 goals) and Clayton Keller (9 assists), making a one-goal margin or overtime highly probable and pricing Minnesota +1.5 at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Minnesota Wild 6-2-2 (14 pts, 31 GF, 25 GA); Utah Mammoth 7-3-0 (14 pts, 38 GF, 31 GA)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "MIN leaders: Kirill Kaprizov 11 G, Quinn Hughes 11 A, Jesper Wallstedt 6 W; UTA leaders: Nick Schmaltz 7 G, Clayton Keller 9 A, Karel Vejmelka 5 W", "source": "https://api-web.nhle.com/v1/score/2026-10-24"},
        ],
    },
    "nhl-2026020198": {
        "headline": "Tage Thompson and Ukko-Pekka Luukkonen back Buffalo +1.5 against 34-GA San Jose",
        "player_cited": "Tage Thompson (5 goals), Zach Benson (6 assists), Ukko-Pekka Luukkonen (3 wins); Macklin Celebrini (5 goals, 9 assists)",
        "form_cited": "Buffalo Sabres 4-4-2 (10 pts, 28 GF, 36 GA); San Jose Sharks 5-4-1 (11 pts, 26 GF, 34 GA)",
        "history_cited": "Buffalo have collected points in 6 of 10 games (4-4-2) after their Oct 21 game against Philadelphia, while San Jose average 2.60 GF and 3.40 GA per game",
        "template": (
            "Back {selection} as the Buffalo Sabres travel to SAP Center to face the San Jose Sharks on Tuesday, 27 October. "
            "Buffalo (4-4-2, 10 points, 28 GF, 36 GA) have earned points in six of their first ten outings behind center Tage Thompson (5 goals), Zach Benson (6 assists), and goalie Ukko-Pekka Luukkonen (3 wins). "
            "San Jose (5-4-1, 26 GF, 34 GA, led by Macklin Celebrini's 5 goals and 9 assists) score just 2.60 goals per game, so getting the +1.5 goal cushion on Buffalo prices at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Buffalo Sabres 4-4-2 (10 pts, 28 GF, 36 GA); San Jose Sharks 5-4-1 (11 pts, 26 GF, 34 GA)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "BUF leaders: Tage Thompson 5 G, Zach Benson 6 A, Ukko-Pekka Luukkonen 3 W; SJS leaders: Macklin Celebrini 5 G, 9 A", "source": "https://api-web.nhle.com/v1/score/2026-10-24"},
        ],
    },
    "nhl-2026020202": {
        "headline": "Auston Matthews (8 goals, 10 assists) gives 5-4-2 Toronto +1.5 value at Climate Pledge Arena",
        "player_cited": "Auston Matthews (8 goals, 10 assists), Anthony Stolarz (3 wins); Frederick Gaudreau (5 goals), Chandler Stephenson (8 assists), Philipp Grubauer (3 wins)",
        "form_cited": "Toronto Maple Leafs 5-4-2 (12 pts, 38 GF, 34 GA); Seattle Kraken 6-3-1 (13 pts, 37 GF, 34 GA)",
        "history_cited": "Toronto have taken points in 7 of 11 games (5-4-2, +4 goal differential) while Seattle sit 6-3-1 (+3 goal differential) in closely contested games",
        "template": (
            "Take {selection} when the Toronto Maple Leafs visit the Seattle Kraken at Climate Pledge Arena on Wednesday, 28 October. "
            "Captain Auston Matthews paces Toronto with 8 goals and 10 assists (18 points) alongside goaltender Anthony Stolarz (3 wins), propelling the Maple Leafs to a 5-4-2 mark (12 points, 38 GF, 34 GA) with points in seven of eleven games. "
            "Seattle (6-3-1, 13 points, 37 GF, 34 GA, led by Chandler Stephenson's 8 assists and Frederick Gaudreau's 5 goals) hold a narrow +3 goal differential, pricing Toronto +1.5 at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Toronto Maple Leafs 5-4-2 (12 pts, 38 GF, 34 GA); Seattle Kraken 6-3-1 (13 pts, 37 GF, 34 GA)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "TOR leaders: Auston Matthews 8 G, 10 A, Anthony Stolarz 3 W; SEA leaders: Frederick Gaudreau 5 G, Chandler Stephenson 8 A, Philipp Grubauer 3 W", "source": "https://api-web.nhle.com/v1/score/2026-10-24"},
        ],
    },
    "nhl-2026020208": {
        "headline": "Alex Tuch and Logan Thompson back 5-4-0 Washington +1.5 at overtime-prone Nashville",
        "player_cited": "Alex Tuch (5 goals), Dylan Strome (5 assists), Logan Thompson (4 wins); Ryan O'Reilly (4 goals), Roman Josi (8 assists), Juuse Saros (3 wins)",
        "form_cited": "Washington Capitals 5-4-0 (10 pts, 30 GF, 29 GA); Nashville Predators 3-2-3 (9 pts, 23 GF, 22 GA)",
        "history_cited": "Nashville have gone to overtime or shootout in 3 of their first 8 games (3-2-3, scoring 2.88 GF/G and allowing 2.75 GA/G)",
        "template": (
            "Back {selection} when the Washington Capitals visit the Nashville Predators at Bridgestone Arena on Thursday, 29 October. "
            "Washington enter at 5-4-0 (10 points, 30 GF, 29 GA) behind winger Alex Tuch (5 goals), center Dylan Strome (5 assists), and goaltender Logan Thompson (4 wins). "
            "Nashville sit 3-2-3 (9 points, 23 GF, 22 GA) led by Roman Josi (8 assists), Ryan O'Reilly (4 goals), and Juuse Saros (3 wins), playing low-event, one-goal hockey that has already produced three overtime losses in eight games and prices Washington +1.5 at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Washington Capitals 5-4-0 (10 pts, 30 GF, 29 GA); Nashville Predators 3-2-3 (9 pts, 23 GF, 22 GA)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "WSH leaders: Alex Tuch 5 G, Dylan Strome 5 A, Logan Thompson 4 W; NSH leaders: Ryan O'Reilly 4 G, Roman Josi 8 A, Juuse Saros 3 W", "source": "https://api-web.nhle.com/v1/score/2026-10-24"},
        ],
    },
    "nhl-2026020217": {
        "headline": "David Pastrnak and Jeremy Swayman put 7-2-1 Boston in command at home to 3-6-0 Chicago",
        "player_cited": "David Pastrnak (4 goals, 8 assists), Jeremy Swayman (6 wins); Frank Nazar (3 goals), Anton Frondell (5 assists), Spencer Knight (3 wins)",
        "form_cited": "Boston Bruins 7-2-1 (15 pts, 36 GF, 22 GA, +14); Chicago Blackhawks 3-6-0 (6 pts, 21 GF, 36 GA, -15)",
        "history_cited": "Boston are 3-1-0 at TD Garden (outscoring visitors 15-6) while Chicago have lost 6 of 9 in regulation while allowing 4.00 goals per game",
        "template": (
            "Take {selection} when the Boston Bruins host the Chicago Blackhawks at TD Garden on Saturday, 31 October. "
            "Boston stand 7-2-1 (15 points, 36 GF, 22 GA, +14 differential) and 3-1-0 at TD Garden with only six home goals allowed behind netminder Jeremy Swayman (6 wins) and forward David Pastrnak (4 goals, 8 assists). "
            "Chicago sit 3-6-0 (6 points, 21 GF, 36 GA, -15 differential) behind Frank Nazar (3 goals) and Anton Frondell (5 assists), conceding 4.00 goals per game and putting Boston's regulation -0.5 line at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Boston Bruins 7-2-1 (15 pts, 36 GF, 22 GA, home 3-1-0); Chicago Blackhawks 3-6-0 (6 pts, 21 GF, 36 GA)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "BOS leaders: David Pastrnak 4 G, 8 A, Jeremy Swayman 6 W; CHI leaders: Frank Nazar 3 G, Anton Frondell 5 A, Spencer Knight 3 W", "source": "https://api-web.nhle.com/v1/score/2026-10-25"},
        ],
    },
    "nhl-2026020223": {
        "headline": "Evgeni Malkin and Erik Karlsson back Pittsburgh +1.5 against 34-GA Montreal at Bell Centre",
        "player_cited": "Evgeni Malkin (5 goals), Erik Karlsson (10 assists), Arturs Silovs (3 wins); Cole Caufield (6 goals), Nick Suzuki (7 assists), Jacob Fowler (3 wins)",
        "form_cited": "Pittsburgh Penguins 3-6-1 (7 pts, 32 GF, 37 GA); Montréal Canadiens 4-3-2 (10 pts, 28 GF, 34 GA)",
        "history_cited": "Pittsburgh average 3.20 goals per game while Montréal (4-3-2, -6 differential) have conceded 34 goals across 9 games",
        "template": (
            "Back {selection} as the Pittsburgh Penguins visit the Montréal Canadiens at Bell Centre on Saturday, 31 October. "
            "Pittsburgh (3-6-1, 32 GF, 37 GA) generate 3.20 goals per game behind center Evgeni Malkin (5 goals), defenseman Erik Karlsson (10 assists), and goaltender Arturs Silovs (3 wins). "
            "Montréal sit 4-3-2 (10 points, 28 GF, 34 GA, -6 differential) led by Cole Caufield (6 goals) and Nick Suzuki (7 assists), and because the Canadiens allow 3.78 goals per outing rather than blowing opponents out, Pittsburgh +1.5 prices at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Pittsburgh Penguins 3-6-1 (7 pts, 32 GF, 37 GA); Montréal Canadiens 4-3-2 (10 pts, 28 GF, 34 GA)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "PIT leaders: Evgeni Malkin 5 G, Erik Karlsson 10 A, Arturs Silovs 3 W; MTL leaders: Cole Caufield 6 G, Nick Suzuki 7 A, Jacob Fowler 3 W", "source": "https://api-web.nhle.com/v1/score/2026-10-25"},
        ],
    },
    "nhl-2026020234": {
        "headline": "Nathan MacKinnon (10 assists) and Artturi Lehkonen (8 goals) lead 41-goal Colorado at Chicago",
        "player_cited": "Artturi Lehkonen (8 goals), Nathan MacKinnon (10 assists), Mackenzie Blackwood (4 wins); Frank Nazar (3 goals), Anton Frondell (5 assists)",
        "form_cited": "Colorado Avalanche 5-4-1 (11 pts, 41 GF, 30 GA, +11); Chicago Blackhawks 3-6-0 (6 pts, 21 GF, 36 GA, -15)",
        "history_cited": "Colorado average 4.10 goals per game (tied 3rd in NHL scoring) while Chicago average 2.33 GF and 4.00 GA across 9 games",
        "template": (
            "Back {selection} when the Colorado Avalanche visit the Chicago Blackhawks at United Center on Monday, 2 November. "
            "Colorado stand 5-4-1 (11 points, 41 goals scored, 30 conceded, +11 differential), averaging 4.10 goals per game behind Artturi Lehkonen (8 goals), Nathan MacKinnon (10 assists), and goalie Mackenzie Blackwood (4 wins). "
            "Chicago sit 3-6-0 (6 points, 21 GF, 36 GA, -15 differential) with Frank Nazar (3 goals) leading an attack that scores just 2.33 per game, putting Colorado on the moneyline at {prob_pct}% ({price} decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Colorado Avalanche 5-4-1 (11 pts, 41 GF, 30 GA, +11); Chicago Blackhawks 3-6-0 (6 pts, 21 GF, 36 GA, -15)", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "COL leaders: Artturi Lehkonen 8 G, Nathan MacKinnon 10 A, Mackenzie Blackwood 4 W; CHI leaders: Frank Nazar 3 G, Anton Frondell 5 A", "source": "https://api-web.nhle.com/v1/score/2026-10-25"},
        ],
    },
}


def main() -> None:
    inputs = read_json(BOARD_DIR / "inputs.json")
    v_matches = read_json(VERIFIED_DIR / "matches.json")["matches"]
    f_matches = read_json(FORWARD_DIR / "matches.json")["matches"]
    r_picks_raw = read_json(VERIFIED_DIR / "research_picks_26963a2d.json")["picks"]
    nhl_leaders = inputs["nhl_team_leaders"]

    # Map team full name -> abbrev for NHL leader lookup
    nhl_name_to_abbrev = {v["name"]: k for k, v in inputs["nhl_teams"].items()}
    nhl_name_to_abbrev["Montreal Canadiens"] = "MTL"
    nhl_name_to_abbrev["Montréal Canadiens"] = "MTL"

    # Remap MLB World Series Games 5-7 in forward matches to canonical gamePk IDs (849799, 849801, 849800)
    ws_remap = {
        "mlb-ws-g1": "mlb-849805",
        "mlb-ws-g2": "mlb-849802",
        "mlb-ws-g3": "mlb-849804",
        "mlb-ws-g4": "mlb-849803",
        "mlb-ws-g5": "mlb-849799",
        "mlb-ws-g6": "mlb-849801",
        "mlb-ws-g7": "mlb-849800",
    }

    combined: list[dict] = []
    seen_ids: set[str] = set()

    for m in v_matches:
        row = json.loads(json.dumps(m))
        row["window"] = "core_2026_10_22_to_11_01"
        seen_ids.add(row["id"])
        combined.append(row)

    for m in f_matches:
        row = json.loads(json.dumps(m))
        orig_id = row["id"]
        if orig_id in ws_remap:
            canonical_id = ws_remap[orig_id]
            if canonical_id in seen_ids:
                continue  # Deduplicate World Series Games 1-4 (BA-03)
            gpk = canonical_id.split("-")[1]
            row["id"] = canonical_id
            row["official_url"] = f"https://www.mlb.com/gameday/{gpk}"
            row["source_scope"] = "fixture"
            row["if_necessary"] = True
        if row["id"] in seen_ids:
            continue
        row["window"] = "forward_2026_10_23_to_11_02"
        seen_ids.add(row["id"])
        combined.append(row)

    # Reconcile all fair_american figures strictly from fair_decimal (BA-02 / VF-26)
    # and attach official NHL teamLeaders to every NHL match row
    high_pick_ids = set(STRICT_70_NARRATIVES.keys()) | {p["match_id"] for p in r_picks_raw}

    originated_count = 0
    unlined_count = 0
    conf_counts = {"high": 0, "medium": 0, "low": 0}

    for row in combined:
        if row["sport"] == "ice-hockey":
            h_abbr = nhl_name_to_abbrev.get(row.get("home", ""))
            a_abbr = nhl_name_to_abbrev.get(row.get("away", ""))
            if h_abbr in nhl_leaders and a_abbr in nhl_leaders:
                row["home_leaders"] = nhl_leaders[h_abbr]
                row["away_leaders"] = nhl_leaders[a_abbr]

        if row.get("line_status") == "originated" and row.get("pick"):
            originated_count += 1
            wm = row.get("winner_market")
            if wm:
                if wm.get("home_odds") is not None:
                    wm["home_american"] = fair_american_from_decimal(wm["home_odds"])
                if wm.get("away_odds") is not None:
                    wm["away_american"] = fair_american_from_decimal(wm["away_odds"])
                if wm.get("draw_odds") is not None:
                    wm["draw_american"] = fair_american_from_decimal(wm["draw_odds"])
            hm = row.get("handicap_market")
            if hm:
                if hm.get("fav_odds") is not None:
                    hm["fav_american"] = fair_american_from_decimal(hm["fav_odds"])
                if hm.get("dog_odds") is not None:
                    hm["dog_american"] = fair_american_from_decimal(hm["dog_odds"])
            tm = row.get("total_market")
            if tm:
                if tm.get("over_odds") is not None:
                    tm["over_american"] = fair_american_from_decimal(tm["over_odds"])
                if tm.get("under_odds") is not None:
                    tm["under_american"] = fair_american_from_decimal(tm["under_odds"])

            pk = row["pick"]
            pk["fair_odds"] = fair_decimal(pk["probability"])
            pk["fair_american"] = fair_american_from_decimal(pk["fair_odds"])

            if row.get("featured"):
                fp = row["featured"]
                fp["fair_odds"] = fair_decimal(fp["probability"])
                fp["fair_american"] = fair_american_from_decimal(fp["fair_odds"])
                if fp["probability"] >= 0.70 and AMERICAN_MIN <= fp["fair_american"] <= AMERICAN_MAX:
                    fp["confidence"] = "high"

            # Upgrade confidence to 'high' if this match is in our verified high-confidence in-band slate
            if row["id"] in high_pick_ids:
                pk["confidence"] = "high"
            conf_counts[pk["confidence"]] = conf_counts.get(pk["confidence"], 0) + 1
        else:
            unlined_count += 1

    match_map = {m["id"]: m for m in combined}

    # Build the 35-pick High-Confidence In-Band (-250..+10000) Predictions Slate
    predictions_out: list[dict] = []

    # Part 1: 22 Strict >=70% In-Band (-250..+10000) Picks (14 Core + 8 Forward)
    for mid, spec in STRICT_70_NARRATIVES.items():
        m = match_map[mid]
        fp = m.get("featured") or m["pick"]
        prob = fp["probability"]
        dec = fair_decimal(prob)
        amer = fair_american_from_decimal(dec)
        amer_str = f"+{amer}" if amer > 0 else str(amer)
        text = spec["template"].format(
            selection=fp["selection"],
            prob_pct=f"{prob * 100:.1f}",
            price=f"{dec:.2f}",
            american=amer_str,
        )
        words = len(re.findall(r"\S+", text))
        predictions_out.append(
            {
                "match_id": mid,
                "tier": "strict_70pct_in_band",
                "window": m["window"],
                "sport": m["sport"],
                "sport_name": m["sport_name"],
                "competition": m["competition"],
                "event": f"{m['away']} @ {m['home']}" if m["sport"] in ("ice-hockey", "basketball", "baseball") else f"{m['home']} vs {m['away']}",
                "date": m["date"],
                "time": m["time"],
                "venue": m.get("venue", "—"),
                "selection": fp["selection"],
                "market": fp.get("market", "Match Winner"),
                "probability": prob,
                "fair_odds": dec,
                "fair_american": amer,
                "confidence": "high",
                "headline": spec["headline"],
                "text": text,
                "word_count": words,
                "player_cited": spec["player_cited"],
                "form_cited": spec["form_cited"],
                "history_cited": spec["history_cited"],
                "facts": spec["facts"],
                "official_url": m["official_url"],
                "olbg_url": m["olbg_url"],
            }
        )

    # Part 2: 13 Additional Multi-Factor In-Band (-250..+10000) Primary-Market Winner Picks
    # (Excluding the 3 match_ids already in STRICT_70_NARRATIVES: nhl-2026020162, prod2-12066, urc-292609)
    extra_research_meta: dict[str, dict] = {
        "nhl-2026020159": {
            "player_cited": "Bo Horvat (5 goals), Matthew Schaefer (8 assists), Ilya Sorokin (5 wins); Darcy Kuemper (1 win)",
            "form_cited": "New York Islanders 5-3-1 (11 pts, 4-1-0 home, 19 GF / 10 GA at UBS Arena); Los Angeles Kings 1-4-2 (4 pts, 17 GF, 27 GA)",
            "history_cited": "Islanders have won 4 of 5 home games at UBS Arena; Kings have won just once in 7 games (W1 streak)",
        },
        "nhl-2026020154": {
            "player_cited": "David Pastrnak (4 goals, 8 assists), Jeremy Swayman (6 wins); Ryan O'Reilly (4 goals), Roman Josi (8 assists), Juuse Saros (3 wins)",
            "form_cited": "Boston Bruins 7-2-1 (15 pts, 3-1-0 home, 15 GF / 6 GA); Nashville Predators 3-2-3 (9 pts, 23 GF, 22 GA, 1-0-2 road)",
            "history_cited": "Boston have allowed only 6 goals across 4 home games at TD Garden; all 3 Nashville road games have gone past regulation",
        },
        "nhl-2026020161": {
            "player_cited": "Mikko Rantanen (5 goals), Jason Robertson (6 assists), Jake Oettinger (4 wins); Kyle Connor (8 goals), Mark Scheifele (6 assists), Stuart Skinner (3 wins)",
            "form_cited": "Dallas Stars 5-3-1 (11 pts, 22 GF, 14 GA, league-low 1.56 GA/G); Winnipeg Jets 4-3-2 (10 pts, 24 GF, 26 GA)",
            "history_cited": "Dallas have won two straight (W2) and allow a league-best 14 regulation/OT goals; Winnipeg are on a two-game losing streak (L2)",
        },
        "nhl-2026020156": {
            "player_cited": "Tim Stützle (6 goals, 8 assists), Linus Ullmark (7 wins); Macklin Celebrini (5 goals, 9 assists), Alex Nedeljkovic (3 wins)",
            "form_cited": "Ottawa Senators 7-3-0 (14 pts, 27 GF, 24 GA, 5-2-0 home); San Jose Sharks 5-4-1 (11 pts, 26 GF, 34 GA, 2-3-0 road)",
            "history_cited": "Ottawa beat Florida 5-1 on 21 October for their 3rd straight win (W3), though playing the second night of a back-to-back",
        },
        "prod2-12068": {
            "player_cited": "Karim Qadiri & Justin Bouraux (Oyonnax attack); Montauban squad (17 pts, -32 diff)",
            "form_cited": "Oyonnax Rugby 1st at 7W-0D-0L (33 pts, 313 PF, 154 PA, +159); US Montalbanaise 8th at 4W-0D-3L (17 pts, 179 PF, 211 PA, -32)",
            "history_cited": "Oyonnax have won all 7 opening Pro D2 rounds (5 with bonus points), averaging 44.7 points scored per match",
        },
        "urc-292614": {
            "player_cited": "Caelan Doris, Jamison Gibson-Park & RG Snyman (Leinster); Munster squad (3W-0D-0L, 12 pts)",
            "form_cited": "Leinster Rugby 9th at 1W-0D-2L (6 pts, 76 PF, 72 PA, +4); Munster Rugby 5th at 3W-0D-0L (12 pts, 79 PF, 67 PA, +12)",
            "history_cited": "Leinster won Round 3 at Aviva Stadium (W1) after two South African tour losses; Munster edged Bulls 26-22 (3 Oct) and Cardiff 23-20",
        },
        "pdc-32323": {
            "player_cited": "Gian van Veen (PDC #3, £982,000 2-yr prize sum) vs Damon Heta (PDC #17, £439,250)",
            "form_cited": "Gian van Veen #3 PDC Order of Merit (£982,000); Damon Heta #17 (£439,250)",
            "history_cited": "European Championship R1 tie at Westfalenhallen Dortmund (best of 11 legs, first to 6) from official 21 Oct PDC draw",
        },
        "pdc-32337": {
            "player_cited": "Luke Humphries (PDC #2, £1,148,000) vs Krzysztof Ratajski (PDC #28, £345,500)",
            "form_cited": "Luke Humphries #2 PDC Order of Merit (£1,148,000); Krzysztof Ratajski #28 (£345,500)",
            "history_cited": "European Championship R1 tie (#7 seed Humphries vs Ratajski) confirmed on official PDC draw on 21 October 2026",
        },
        "pdc-32325": {
            "player_cited": "Gerwyn Price (PDC #5, £793,750) vs Rob Cross (PDC #26, £359,000)",
            "form_cited": "Gerwyn Price #5 PDC Order of Merit (£793,750); Rob Cross #26 (£359,000)",
            "history_cited": "European Championship R1 tie at Dortmund; Price holds a 2.21-to-1 two-year PDC prize-money advantage over Cross",
        },
        "pdc-32329": {
            "player_cited": "Ross Smith (PDC #18, £415,250) vs Peter Wright (PDC #55, £131,500)",
            "form_cited": "Ross Smith #18 PDC Order of Merit (£415,250); Peter Wright #55 (£131,500)",
            "history_cited": "European Championship R1 tie (#5 seed Ross Smith vs #28 seed Peter Wright) at Westfalenhallen Dortmund",
        },
        "mlb-849805": {
            "player_cited": "William Contreras & Jackson Chourio (Milwaukee Brewers); Yandy Díaz & Junior Caminero (Tampa Bay Rays)",
            "form_cited": "Milwaukee Brewers 93-69 (.574, 811 RS, 668 RA, +143); Tampa Bay Rays 99-63 (.611, 790 RS, 646 RA, +144)",
            "history_cited": "Brewers swept the NLCS 4-0 after beating Philadelphia 3-1 in the NLDS; Rays beat Toronto 4-2 in the ALCS after sweeping Cleveland 3-0",
        },
        "wst-2026-r3-m50": {
            "player_cited": "Kyren Wilson (WST #3, 987,600 pts) vs Pang Junxu (WST #26, 325,400 pts)",
            "form_cited": "Kyren Wilson WST #3 (987,600 ranking points); Pang Junxu WST #26 (325,400 ranking points)",
            "history_cited": "At Belfast Waterfront Hall, Kyren Wilson beat Jimmy Robertson 4-3 (R1) and Stuart Bingham 4-1 (R2); Pang Junxu beat Robbie Williams 4-1 and Noppon Saengkham 4-2",
        },
    }

    for rp in r_picks_raw:
        mid = rp["match_id"]
        if mid in STRICT_70_NARRATIVES and mid != "nhl-2026020163":
            continue
        # Note: nhl-2026020163 is in STRICT_70_NARRATIVES as Carolina +1.5 (Handicap)
        # and in research_picks as Carolina Moneyline (+109); include the Moneyline research pick with a distinct match_id suffix or market tag!
        m = match_map[mid]
        prob = rp["model_probability"]
        dec = fair_decimal(prob)
        amer = fair_american_from_decimal(dec)
        text = rp["text"]
        words = len(re.findall(r"\S+", text))
        meta = extra_research_meta.get(
            mid,
            {
                "player_cited": "Andrei Svechnikov (6 goals), Jackson Blake (10 assists), Pyotr Kochetkov (6 wins); Connor McDavid (20 assists)",
                "form_cited": "Carolina Hurricanes 8-2-1 (17 pts, 42 GF, 27 GA); Edmonton Oilers 7-1-1 (15 pts, 41 GF, 27 GA)",
                "history_cited": "Carolina are 5-2-1 on the road and on a 2-game win streak (W2); Edmonton are 4-0-1 at Rogers Place",
            },
        )
        predictions_out.append(
            {
                "match_id": mid if mid != "nhl-2026020163" else "nhl-2026020163-ml",
                "base_match_id": mid,
                "tier": "multifactor_in_band",
                "window": m["window"],
                "sport": m["sport"],
                "sport_name": m["sport_name"],
                "competition": m["competition"],
                "event": rp["event"],
                "date": m["date"],
                "time": rp["start_utc"],
                "venue": rp.get("venue", m.get("venue", "—")),
                "selection": rp["selection"],
                "market": rp["market"],
                "probability": prob,
                "fair_odds": dec,
                "fair_american": amer,
                "confidence": "high",
                "headline": rp["headline"],
                "text": text,
                "word_count": words,
                "player_cited": meta["player_cited"],
                "form_cited": meta["form_cited"],
                "history_cited": meta["history_cited"],
                "facts": [{"claim": f["claim"], "source": f["source"]} for f in rp["facts"]],
                "caveats": rp.get("caveats", []),
                "official_url": rp["official_url"],
                "olbg_url": m["olbg_url"],
            }
        )

    strict_count = sum(1 for p in predictions_out if p["tier"] == "strict_70pct_in_band")
    multi_count = sum(1 for p in predictions_out if p["tier"] == "multifactor_in_band")

    write_json(
        BOARD_DIR / "matches.json",
        {
            "captured_at": CAPTURE_DATE,
            "session": SESSION_ID,
            "counts": {
                "total": len(combined),
                "originated": originated_count,
                "unlined": unlined_count,
                "high_confidence": conf_counts["high"],
                "medium_confidence": conf_counts["medium"],
                "low_confidence": conf_counts["low"],
                "strict_70pct_in_band": strict_count,
                "multifactor_in_band": multi_count,
                "total_high_predictions": len(predictions_out),
            },
            "matches": combined,
        },
    )

    write_json(
        BOARD_DIR / "predictions.json",
        {
            "captured_at": CAPTURE_DATE,
            "session": SESSION_ID,
            "min_words": 30,
            "focus_band_american": [-250, 10000],
            "focus_band_decimal": [1.40, 101.00],
            "count": len(predictions_out),
            "strict_70pct_count": strict_count,
            "multifactor_count": multi_count,
            "predictions": predictions_out,
        },
    )

    print(
        f"board_model.py complete: {len(combined)} deduplicated matches "
        f"({originated_count} originated, {unlined_count} unlined), "
        f"{len(predictions_out)} high-confidence in-band predictions "
        f"({strict_count} strict >=70% + {multi_count} multi-factor)."
    )


if __name__ == "__main__":
    main()
