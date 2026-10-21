#!/usr/bin/env python3
"""Independent multi-market line origination and human prediction builder for /verified/.

Reads cleanroom primary-official inputs from data/verified/inputs.json (plus the
verified shared tables in data/inputs/{nhl_teams,nba_teams,fixtures,urc,handball_ehf}.json)
and writes:
  - data/verified/matches.json
  - data/verified/predictions.json

Zero bookmaker odds or tipster consensus percentages enter any equation.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "data" / "verified"
SHARED = ROOT / "data" / "inputs"

HIGH_THRESHOLD = 0.72
MEDIUM_THRESHOLD = 0.60


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fair_decimal(prob: float) -> float:
    return round(max(1.02, 1.0 / max(prob, 1e-6)), 2)


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def half_line(raw: float) -> float:
    """Nearest half-point market line to raw projection."""
    return math.floor(raw) + 0.5


def spread_line(expected_home_margin: float) -> float:
    """Standard half-point home handicap (negative when home is favoured)."""
    target = -expected_home_margin
    return math.floor(target) + 0.5


def poisson_grid(lh: float, la: float) -> dict[tuple[int, int], float]:
    max_k = max(35, int(math.ceil(max(lh, la) + 7.5 * math.sqrt(max(lh, la, 1.0)))))
    ph = [math.exp(-lh) * (lh**k) / math.factorial(k) for k in range(max_k + 1)]
    pa = [math.exp(-la) * (la**k) / math.factorial(k) for k in range(max_k + 1)]
    grid: dict[tuple[int, int], float] = {}
    total_mass = 0.0
    for i in range(max_k + 1):
        for j in range(max_k + 1):
            p = ph[i] * pa[j]
            grid[(i, j)] = p
            total_mass += p
    return {k: v / total_mass for k, v in grid.items()}


def grade(prob: float, cap: str | None = None) -> str:
    raw = "high" if prob >= HIGH_THRESHOLD else ("medium" if prob >= MEDIUM_THRESHOLD else "low")
    order = ["low", "medium", "high"]
    if cap and order.index(raw) > order.index(cap):
        return cap
    return raw


def best_of_race(p: float, target: int) -> list[tuple[int, int, float]]:
    """Exact score distribution for first-to-`target` legs/frames/sets."""
    outcomes: list[tuple[int, int, float]] = []
    q = 1.0 - p
    for opp in range(target):
        ways = math.comb(target - 1 + opp, opp)
        outcomes.append((target, opp, ways * (p**target) * (q**opp)))
        outcomes.append((opp, target, ways * (q**target) * (p**opp)))
    return outcomes


# Hand-crafted, non-templated human analyses for every HIGH-confidence selection.
# Each entry uses verified official figures only and embeds {prob_pct} and {price}
# directly from the live model run so prose and table numbers can never diverge.
BESPOKE_HIGH_NARRATIVES: dict[str, dict] = {
    "el-E2026-67": {
        "headline": "Athens fortress and +90 net differential make Panathinaikos overwhelming hosts",
        "template": (
            "Back **Panathinaikos AKTOR Athens to beat Kosner Baskonia Vitoria-Gasteiz** on the EuroLeague Round 7 moneyline at Telekom Center Athens. "
            "Panathinaikos sit top of the 20-club standings at 5-1 with a competition-best +90 point differential (528 scored, 438 conceded) and a 4-1 home record. "
            "Baskonia arrive bottom at 1-5 (-60 differential, 0-2 away, allowing 94.0 points per game), pricing the hosts at {prob_pct}% ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Panathinaikos lead the 2026-27 EuroLeague table at 5-1 (528 PF, 438 PA, +90, 4-1 home)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "Kosner Baskonia sit 20th at 1-5 (504 PF, 564 PA, -60, 0-2 road)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "Round 7 fixture confirmed at Telekom Center Athens on 22 October 2026", "source": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/panathinaikos-aktor-athens-kosner-baskonia-vitoria-gasteiz/E2026/67/"},
        ],
    },
    "ec-R4-bosna-bks": {
        "headline": "Unbeaten Group D leaders Bahcesehir carry a +21.3 per-game margin into Sarajevo",
        "template": (
            "Select **Bahcesehir College Istanbul to win away against BOSNA BH Telecom Sarajevo** in BKT EuroCup Group D. "
            "Bahcesehir have swept their opening three group games 3-0 while outscoring opponents 291-227 (+64 net, 97.0 points per outing). "
            "Bosna are winless at 0-3 (237 scored, 252 allowed), and even after accounting for Sarajevo home court our shrinkage model makes Bahcesehir {prob_pct}% favourites ({price} fair odds)."
        ),
        "facts": [
            {"claim": "Bahcesehir top EuroCup Group D at 3-0 with 291 PF and 227 PA (+64)", "source": "https://www.euroleaguebasketball.net/en/eurocup/standings/"},
            {"claim": "BOSNA BH Telecom Sarajevo stand 7th in Group D at 0-3 (237 PF, 252 PA, -15)", "source": "https://www.euroleaguebasketball.net/en/eurocup/standings/"},
        ],
    },
    "ec-R4-jlm-rig": {
        "headline": "Hapoel Midtown Jerusalem's defensive stinginess separates them from Riga Zelli",
        "template": (
            "Take **Hapoel Midtown Jerusalem on the moneyline over Riga Zelli** in EuroCup Group A action. "
            "Jerusalem enter undefeated at 3-0 having held three opponents to 221 combined points (73.7 allowed per game against 84.7 scored). "
            "Riga Zelli are 2-1 overall (261-250) with an 0-1 road mark, and on a neutral floor our efficiency model still rates Hapoel at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Hapoel Midtown Jerusalem sit 3-0 in Group A (254 PF, 221 PA, +33)", "source": "https://www.euroleaguebasketball.net/en/eurocup/standings/"},
            {"claim": "Riga Zelli sit 2-1 in Group A (261 PF, 250 PA, +11, 0-1 away)", "source": "https://www.euroleaguebasketball.net/en/eurocup/standings/"},
        ],
    },
    "top14-11867": {
        "headline": "Table-topping Stade Toulousain bring five straight Top 14 victories to Ernest-Wallon",
        "template": (
            "Stade Toulousain to win the match-winner market at home against USA Perpignan on Saturday afternoon in Top 14 Journée 7. "
            "Toulouse sit first on 24 points (5W-0D-1L, 197 for, 124 against, +73) riding five consecutive league wins plus a 60-14 Champions Cup demolition of Sale Sharks. "
            "Ninth-placed Perpignan (3W-0D-3L, 166-199, -33) face a {prob_pct}% home favourite ({price} fair price)."
        ),
        "facts": [
            {"claim": "Stade Toulousain lead Top 14 on 24 pts (5W-0D-1L, 197 PF, 124 PA, W-W-W-W-W)", "source": "https://top14.lnr.fr/classement"},
            {"claim": "USA Perpignan rank 9th on 13 pts (3W-0D-3L, 166 PF, 199 PA, -33)", "source": "https://top14.lnr.fr/classement"},
            {"claim": "Stade Toulousain beat Sale Sharks 60-14 in EPCR Champions Cup Round 1", "source": "https://top14.lnr.fr/club/toulouse"},
            {"claim": "Journée 7 fixture sheet 11867 confirmed on LNR", "source": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan"},
        ],
    },
    "prod2-12068": {
        "headline": "Unbeaten Oyonnax average 44.7 points per game heading to Montauban",
        "template": (
            "Oyonnax Rugby to beat US Montauban away in Thursday night's Pro D2 Journée 8 opener. "
            "Top-seeded Oyonnax have won all seven league fixtures (7W-0D-0L, 33 points with five bonus points), piling up 313 points while conceding only 154 (+159). "
            "Eighth-placed Montauban carry a -32 differential (182 for, 214 against) and three losses in five, leaving Oyonnax at {prob_pct}% ({price}) even away from home."
        ),
        "facts": [
            {"claim": "Oyonnax lead Pro D2 on 33 pts (7W-0D-0L, 313 PF, 154 PA, +159)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "US Montauban sit 8th on 17 pts (4W-0D-3L, 182 PF, 214 PA, -32)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Journée 8 match sheet 12068 confirmed on LNR Pro D2", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12068-montauban-oyonnax"},
        ],
    },
    "prod2-12064": {
        "headline": "Seven-from-seven Provence Rugby host leaky Béziers in Aix-en-Provence",
        "template": (
            "Provence Rugby to defeat AS Béziers Hérault at home in Friday's Pro D2 Journée 8 card. "
            "Unbeaten Provence stand 7W-0D-0L on 29 points after conceding just 158 points across seven rounds (222 scored, +64). "
            "Fourteenth-placed Béziers have dropped four of their last five matches while shipping 240 points (-93 differential), giving Provence an {prob_pct}% win probability ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Provence Rugby rank 2nd in Pro D2 at 7W-0D-0L (29 pts, 222 PF, 158 PA, +64)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "AS Béziers Hérault rank 14th at 2W-0D-5L (9 pts, 147 PF, 240 PA, -93)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Journée 8 match sheet 12064 confirmed on LNR Pro D2", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12064-provence-rugby-beziers"},
        ],
    },
    "prod2-12066": {
        "headline": "Resurgent Aurillac catch winless bottom club Nevers on home turf",
        "template": (
            "Back Stade Aurillacois to beat USON Nevers at home in Pro D2 Journée 8. "
            "Aurillac arrive on back-to-back victories over Biarritz and Béziers to reach 16 points (3W-0D-4L, 240 points scored). "
            "Bottom-placed Nevers are the lone winless club in the division at 0W-0D-7L with a -76 differential (146 scored, 222 conceded), putting home side Aurillac at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Stade Aurillacois sit 9th on 16 pts (3W-0D-4L, 240 PF, 254 PA, consecutive wins)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "USON Nevers sit 16th on 4 pts (0W-0D-7L, 146 PF, 222 PA, -76)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Journée 8 match sheet 12066 confirmed on LNR Pro D2", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12066-aurillac-nevers"},
        ],
    },
    "prod2-12069": {
        "headline": "CA Brive's defensive structure outclasses Narbonne's league-worst 296 points conceded",
        "template": (
            "CA Brive to win away at RC Narbonnais in Pro D2 Journée 8. "
            "Fourth-placed Brive (5W-0D-2L, 21 points) allow just 23.4 points per game (206 scored, 164 conceded, +42). "
            "Fifteenth-placed Narbonne own the worst defence in Pro D2 having leaked 296 points in seven outings (-110 differential, four straight defeats), giving Brive a {prob_pct}% edge ({price})."
        ),
        "facts": [
            {"claim": "CA Brive rank 4th on 21 pts (5W-0D-2L, 206 PF, 164 PA, +42)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "RC Narbonnais rank 15th on 9 pts (2W-0D-5L, 186 PF, 296 PA, -110)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Journée 8 match sheet 12069 confirmed on LNR Pro D2", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12069-narbonne-brive"},
        ],
    },
    "urc-292611": {
        "headline": "Loftus Versfeld firepower makes Vodacom Bulls heavy hosts against winless Ulster",
        "template": (
            "Vodacom Bulls to win the 1X2 match-winner market against Ulster Rugby at Loftus Versfeld on Saturday morning in URC Round 4. "
            "Pretoria's Bulls lead the entire URC in scoring with 126 points across three matches against only 54 conceded (+72), fresh off hammering the Lions 57-15 on 10 October. "
            "Winless Ulster enter at 0W-2D-1L (88 PF, 93 PA), putting the Bulls at {prob_pct}% ({price} fair price)."
        ),
        "facts": [
            {"claim": "Vodacom Bulls stand 2W-0D-1L with a URC-high 126 PF and 54 PA (+72)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Vodacom Bulls beat 10bet Lions 57-15 on 10 October 2026", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Ulster Rugby stand winless at 0W-2D-1L (88 PF, 93 PA)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Round 4 fixture 292611 confirmed at Loftus Versfeld", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/vodacom-bulls-vs-ulster-rugby-2026-10-24/292611"},
        ],
    },
    "urc-292609": {
        "headline": "Connacht host winless Zebre Parma (-64 differential) under Friday night lights in Galway",
        "template": (
            "Connacht Rugby to defeat Zebre Parma at Dexcom Stadium in Friday's URC Round 4 meeting. "
            "Bottom-placed Zebre arrive at 0W-0D-3L with a competition-worst -64 differential (52 scored, 116 conceded) after losing 29-12 to Edinburgh on 10 October. "
            "Against 1W-0D-2L Connacht (56 PF, 84 PA) in Galway, our shrunk margin model prices the home win at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Zebre Parma sit 16th in the URC at 0W-0D-3L (52 PF, 116 PA, -64)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Edinburgh beat Zebre Parma 29-12 in Round 3 on 10 October 2026", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Connacht Rugby stand 1W-0D-2L (56 PF, 84 PA) ahead of Dexcom Stadium kick-off", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/connacht-rugby-vs-zebre-parma-2026-10-23/292609"},
        ],
    },
    "urc-292610": {
        "headline": "Three-from-three league leaders Edinburgh welcome leaky Lions to Hive Stadium",
        "template": (
            "Edinburgh Rugby to win the 1X2 match-winner market at home against 10bet Lions in Friday night's URC Round 4 fixture. "
            "Edinburgh sit top of the URC on 14 points as the only 3W-0D-0L side (80 PF, 54 PA) after beating Zebre 29-12 away, whereas the Lions shipped 57 points at Loftus last time out (77 PF, 102 PA overall), pricing Edinburgh at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Edinburgh lead the URC table at 3W-0D-0L (14 pts, 80 PF, 54 PA)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "10bet Lions sit 2W-0D-1L (77 PF, 102 PA) after losing 57-15 at Bulls on 10 Oct", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Round 4 fixture 292610 confirmed at Hive Stadium", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/edinburgh-rugby-vs-10bet-lions-2026-10-23/292610"},
        ],
    },
    "urc-292617": {
        "headline": "Second-placed Glasgow Warriors bring unbeaten Scotstoun record against leaky Lions",
        "template": (
            "Glasgow Warriors to defeat 10bet Lions in Friday night's URC Round 5 clash at Scotstoun Stadium. "
            "Unbeaten Glasgow sit second on 13 points (2W-1D-0L, 95 points scored, 72 conceded) after beating Connacht 36-19 at home on 9 October. "
            "Seventh-placed Lions have shipped 102 points in three games following their 57-15 loss in Pretoria, pricing Glasgow at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Glasgow Warriors sit 2nd in URC at 2W-1D-0L (13 pts, 95 PF, 72 PA) and beat Connacht 36-19", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "10bet Lions stand 2W-0D-1L (77 PF, 102 PA) after losing 57-15 at Bulls", "source": "https://stats.unitedrugby.com/match-centre/2026-27/5"},
        ],
    },
    "urc-292618": {
        "headline": "Cape Town defence gives DHL Stormers clear home edge over winless Ulster",
        "template": (
            "DHL Stormers to win the 1X2 match-winner market at DHL Stadium against Ulster Rugby in URC Round 5. "
            "Stormers have conceded a league-low 54 points across three rounds (2W-0D-1L, 81 PF) and routed the Sharks 39-22 at this venue on 10 October, whereas Ulster enter winless at 0W-2D-1L (88 PF, 93 PA), pricing Stormers at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "DHL Stormers stand 4th at 2W-0D-1L (81 PF, 54 PA) and beat Sharks 39-22", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Ulster Rugby sit winless at 0W-2D-1L (88 PF, 93 PA) ahead of Cape Town trip", "source": "https://stats.unitedrugby.com/match-centre/2026-27/5"},
        ],
    },
    "urc-292619": {
        "headline": "Vodacom Bulls' +72 scoring surge hosts point-negative Scarlets in Pretoria",
        "template": (
            "Vodacom Bulls to beat Scarlets on the 1X2 match-winner line at Loftus Versfeld in Saturday's URC Round 5 fixture. "
            "Pretoria's Bulls lead the URC with 126 points scored and only 54 allowed (+72) after their 57-15 demolition of the Lions, while twelfth-placed Scarlets sit 1W-0D-2L (-17 differential, 68 PF, 85 PA), putting the hosts at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Vodacom Bulls lead the URC with 126 PF against 54 PA (+72) at 2W-0D-1L", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Scarlets sit 12th at 1W-0D-2L (68 PF, 85 PA) before visiting Loftus Versfeld", "source": "https://stats.unitedrugby.com/match-centre/2026-27/5"},
        ],
    },
    "urc-292622": {
        "headline": "Rodney Parade attack backs Dragons RFC against winless cellar-dwellers Zebre Parma",
        "template": (
            "Dragons RFC to win at Rodney Parade against Zebre Parma in Saturday's URC Round 5 meeting. "
            "Eighth-placed Dragons hold a +5 differential on 9 points (1W-1D-1L, 88 PF, 83 PA) after scoring 31 points at home on 9 October, whereas bottom-placed Zebre are 0W-0D-3L with a competition-worst -64 differential (52 PF, 116 PA), rating Dragons at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Dragons RFC stand 8th on 9 pts (1W-1D-1L, 88 PF, 83 PA)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Zebre Parma sit 16th at 0W-0D-3L (1 pt, 52 PF, 116 PA, -64)", "source": "https://stats.unitedrugby.com/match-centre/2026-27/5"},
        ],
    },
    "urc-292612": {
        "headline": "DHL Stormers' stingy Cape Town defence faces point-shy Scarlets in Round 4",
        "template": (
            "DHL Stormers to beat Scarlets at DHL Stadium in Saturday's URC Round 4 clash. "
            "Cape Town's Stormers stand 4th on 11 points (2W-0D-1L, 81 PF, joint-best 54 PA) coming off a comprehensive 39-22 home victory over the Sharks on 10 October. "
            "Twelfth-placed Scarlets sit 1W-0D-2L (-17 differential, 68 PF, 85 PA), making Stormers {prob_pct}% favourites ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "DHL Stormers stand 4th in the URC at 2W-0D-1L (81 PF, 54 PA, +27)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Stormers beat Hollywoodbets Sharks 39-22 on 10 October 2026", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Scarlets stand 12th at 1W-0D-2L (68 PF, 85 PA) before visiting DHL Stadium", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/dhl-stormers-vs-scarlets-2026-10-24/292612"},
        ],
    },
    "ehfcl-202711020101041": {
        "headline": "Unbeaten Sporting Clube de Portugal meet Group D's leakiest defence in Lisbon",
        "template": (
            "Sporting Clube de Portugal to win the match-winner market at home over IFK Kristianstad in Thursday's EHF Champions League Round 5 tie. "
            "Sporting stand unbeaten in Group D at 3W-1D-0L (7 points, 149 goals scored, 125 conceded). "
            "Winless Kristianstad sit 0W-0D-4L having conceded a competition-high 155 goals (122 scored), making Sporting {prob_pct}% favourites ({price} fair price)."
        ),
        "facts": [
            {"claim": "Sporting lead Group D unbeaten at 3W-1D-0L (7 pts, 149 GF, 125 GA)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "IFK Kristianstad sit 4th in Group D at 0W-0D-4L (0 pts, 122 GF, 155 GA)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "EHF Round 5 match 202711020101041 scheduled 22 Oct 20:45 CEST", "source": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101041/SportingClubedePortugal-IFKKristianstad/"},
        ],
    },
    "ehfcl-202711020101029": {
        "headline": "Unbeaten Aalborg Håndbold hold a +55 goal-difference swing over winless Celje",
        "template": (
            "Aalborg Håndbold to beat RK Celje Pivovarna Laško at home in Wednesday's Group C EHF Champions League fixture. "
            "Aalborg are unbeaten at 3W-1D-0L (7 points, 136 goals for, 115 against, +21), whereas Celje have dropped all four games (0W-0D-4L) while conceding 154 goals (-34). "
            "Full-support Poisson pricing rates Aalborg at {prob_pct}% ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Aalborg stand 3W-1D-0L in Group C (7 pts, 136 GF, 115 GA, +21)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "RK Celje Pivovarna Laško stand 0W-0D-4L in Group C (0 pts, 120 GF, 154 GA, -34)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "EHF Round 5 match 202711020101029 scheduled 21 Oct 20:45 CEST", "source": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101029/AalborgH%C3%A5ndbold-RKCeljePivovarnaLa%C5%A1ko/"},
        ],
    },
    "ehfcl-202711020101064": {
        "headline": "Four-from-four SC Magdeburg travel to Trondheim against 0W-0D-4L Kolstad",
        "template": (
            "SC Magdeburg to defeat Kolstad Håndball away in Thursday night's EHF Champions League Group F contest. "
            "Magdeburg boast a perfect 4W-0D-0L record (8 points) with 141 goals scored and only 108 conceded (+33). "
            "Kolstad sit bottom at 0W-0D-4L (111 scored, 143 conceded, -32), leaving visiting Magdeburg at {prob_pct}% ({price} fair odds)."
        ),
        "facts": [
            {"claim": "SC Magdeburg lead Group F at 4W-0D-0L (8 pts, 141 GF, 108 GA, +33)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "Kolstad Håndball sit 4th in Group F at 0W-0D-4L (0 pts, 111 GF, 143 GA, -32)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "EHF Round 5 match 202711020101064 scheduled 22 Oct 20:45 CEST", "source": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101064/KolstadH%C3%A5ndball-SCMagdeburg/"},
        ],
    },
    "ehfcl-202711020101049": {
        "headline": "Competition-best defence gives unbeaten Barça commanding home control over Montpellier",
        "template": (
            "Barça to beat Montpellier Handball at Palau Blaugrana in Thursday's EHF Champions League Group E clash. "
            "Barça have won all four group fixtures (4W-0D-0L, 8 points) while conceding only 104 goals — the stingiest mark among all 24 clubs — alongside 137 goals scored. "
            "Against 1W-0D-3L Montpellier (116 GF, 125 GA), Barça project at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Barça lead Group E at 4W-0D-0L with 137 GF and 104 GA (fewest goals allowed in EHF CL)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "Montpellier Handball stand 3rd in Group E at 1W-0D-3L (116 GF, 125 GA)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "EHF Round 5 match 202711020101049 scheduled 22 Oct 20:45 CEST", "source": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101049/Bar%C3%A7a-MontpellierHandball/"},
        ],
    },
    "pdc-32328": {
        "headline": "World No. 1 Luke Littler's £3.11m prize haul towers over William O'Connor over 11 legs",
        "template": (
            "Luke Littler to win his PDC European Championship first-round tie against William O'Connor on Friday afternoon. "
            "Littler leads the official PDC Werner Ranking Ladder by more than £2 million on £3,113,500 across the two-year cycle, whereas world No. 32 O'Connor sits on £274,500. "
            "Over best-of-11 legs, that 11.3-to-1 prize ratio translates into an {prob_pct}% match win probability ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Luke Littler ranks #1 on the official PDC Werner Ranking Ladder with £3,113,500", "source": "https://www.pdc.tv/rankings"},
            {"claim": "William O'Connor ranks #32 on the official PDC Werner Ranking Ladder with £274,500", "source": "https://www.pdc.tv/rankings"},
            {"claim": "European Championship R1 tie confirmed on OLBG Darts hub (event_id=32328)", "source": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Luke_Littler_vs_William_OConnor/15?event_id=32328"},
        ],
    },
    "pdc-32327": {
        "headline": "World No. 11 Nathan Aspinall holds a six-fold ranking money edge on qualifier Cristo Reyes",
        "template": (
            "Nathan Aspinall to defeat Cristo Reyes in Friday's PDC European Championship Round 1 contest (contrarian to casual tipster upset chatter). "
            "Official PDC standings place Aspinall 11th on £579,500 against No. 71 Reyes on £95,000 — the widest ranking-position gap in the entire 16-match draw. "
            "Across a first-to-six-legs race our binomial leg model prices Aspinall at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Nathan Aspinall ranks #11 on the PDC Werner Ranking Ladder with £579,500", "source": "https://www.pdc.tv/rankings"},
            {"claim": "Cristo Reyes ranks #71 on the PDC Werner Ranking Ladder with £95,000", "source": "https://www.pdc.tv/rankings"},
            {"claim": "European Championship R1 tie confirmed on OLBG Darts hub (event_id=32327)", "source": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Nathan_Aspinall_vs_Cristo_Reyes/15?event_id=32327"},
        ],
    },
    "atp-902102": {
        "headline": "World No. 15 Tommy Paul carries more than quadruple Benjamin Bonzi's ATP points",
        "template": (
            "Tommy Paul to beat Benjamin Bonzi in Wednesday afternoon's indoor hard-court singles clash. "
            "On the official 19 October 2026 PIF ATP Rankings, Paul stands No. 15 on 2,575 points (+200 movement across 22 tournaments) while Bonzi clings to No. 100 on 605 points (-8 places). "
            "In best-of-three sets our Markov set model makes Paul an {prob_pct}% favourite ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Tommy Paul ranks #15 on 2,575 official ATP singles points (2026.10.19)", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Benjamin Bonzi ranks #100 on 605 official ATP singles points (2026.10.19)", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Match listed on OLBG Tennis hub for 21 Oct 14:30 (event_id=902102)", "source": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Benjamin_Bonzi_vs_Tommy_Paul/3?event_id=902102"},
        ],
    },
    "atp-7485-MS008": {
        "headline": "Top-10 seed Arthur Fils brings a 3,325-to-1,010 ATP points margin into Brussels R16",
        "template": (
            "Arthur Fils to defeat Jaume Munar in the BNP Paribas Fortis European Open Round of 16 in Brussels. "
            "Official PIF ATP singles standings rank the 22-year-old Frenchman No. 10 in the world on 3,325 points across 19 events, more than triple No. 51 Munar's 1,010 points. "
            "Across best-of-three indoor sets our model rates Fils at {prob_pct}% ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Arthur Fils holds ATP world rank #10 on 3,325 points (2026.10.19)", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Jaume Munar holds ATP world rank #51 on 1,010 points (2026.10.19)", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Brussels Round of 16 match MS008 confirmed on official ATP Tour live scores", "source": "https://www.atptour.com/en/scores/stats-centre/live/2026/7485/MS008"},
        ],
    },
    "atp-902037": {
        "headline": "Andrey Rublev's 2,175-point ranking base outguns 38-year-old Adrian Mannarino in Almaty",
        "template": (
            "Andrey Rublev to win his Almaty Open singles meeting with Adrian Mannarino. "
            "Rublev sits No. 22 in the official 19 October 2026 ATP rankings on 2,175 points compared with No. 79 Mannarino on 743 points across 33 tournaments played. "
            "That nearly three-to-one ATP points gap yields a {prob_pct}% best-of-three win probability ({price} fair price) for Rublev."
        ),
        "facts": [
            {"claim": "Andrey Rublev ranks #22 on 2,175 official ATP points", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Adrian Mannarino ranks #79 on 743 official ATP points", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Almaty Open match confirmed on ATP Tour & OLBG (event_id=902037)", "source": "https://www.atptour.com/en/tournaments/almaty/9410/overview"},
        ],
    },
    "atp-9410-MS015": {
        "headline": "Second seed Luciano Darderi holds a 50-place ATP ranking cushion over James Duckworth",
        "template": (
            "Luciano Darderi to prevail over James Duckworth in the Almaty Open Round of 16 on Center Court. "
            "Seeded second in Kazakhstan, world No. 23 Darderi carries 2,160 official ATP points into the tie against 34-year-old No. 73 Duckworth on 774 points (-103 week-on-week). "
            "Over best-of-three sets our ranking points model prices Darderi at {prob_pct}% ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Luciano Darderi ranks #23 on 2,160 official ATP points and is #2 seed in Almaty", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "James Duckworth ranks #73 on 774 official ATP points", "source": "https://www.atptour.com/en/rankings/singles"},
            {"claim": "Almaty Round of 16 match MS015 confirmed on official ATP Tour stats centre", "source": "https://www.atptour.com/en/scores/stats-centre/live/2026/9410/MS015"},
        ],
    },
    "f1-2026-drivers": {
        "headline": "Kimi Antonelli's 102-point cushion atop the FIA Drivers' Championship commands title market",
        "template": (
            "Kimi Antonelli to win the 2026 FIA Formula 1 Drivers' World Championship outright. "
            "Official Formula 1 standings entering Austin show Mercedes rookie sensation Antonelli on 340 points — a massive 102 points clear of team-mate George Russell (238), 111 ahead of Lewis Hamilton (229), and 119 clear of Max Verstappen (221). "
            "Our championship points-rate model puts Antonelli's title probability at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "Kimi Antonelli leads the 2026 FIA Drivers' Standings on 340 points for Mercedes", "source": "https://www.formula1.com/en/results/2026/drivers"},
            {"claim": "Nearest chasers: George Russell 238 pts, Lewis Hamilton 229 pts, Max Verstappen 221 pts", "source": "https://www.formula1.com/en/results/2026/drivers"},
            {"claim": "Market active on OLBG Motor Racing hub", "source": "https://www.olbg.com/betting-tips/Motor_Racing/14"},
        ],
    },
    # Additional high-conviction candidates in case shrinkage parameters push any border match >= 72%:
    "nhl-2026020159": {
        "headline": "Sorokin and stingy Islanders defence host struggling Kings at UBS Arena",
        "template": (
            "New York Islanders to win on the moneyline against the Los Angeles Kings at UBS Arena. "
            "New York enter at 5-3-1 having allowed only 19 goals across nine games (2.11 GA/G) behind five wins from Ilya Sorokin, while Los Angeles sit 1-4-2 with 27 goals conceded in seven outings (3.86 GA/G). "
            "Our shrunk Poisson model prices the Islanders at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "NY Islanders stand 5-3-1 with 27 GF and 19 GA in 9 games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Los Angeles Kings stand 1-4-2 with 17 GF and 27 GA in 7 games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Sorokin 5 wins, Horvat 5 goals on official NHL GameCenter feed", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
        ],
    },
    "pdc-32323": {
        "headline": "World No. 3 Gian van Veen holds a near three-to-one prize advantage over Andrew Gilding",
        "template": (
            "Gian van Veen to beat Andrew Gilding in Thursday's PDC European Championship first round. "
            "Van Veen sits third on the official PDC Werner Ranking Ladder with £1,035,750 in two-year prize money, facing world No. 27 Gilding on £355,750. "
            "Across a best-of-11-legs format that sustained scoring superiority translates into a {prob_pct}% win probability ({price} fair price)."
        ),
        "facts": [
            {"claim": "Gian van Veen ranks #3 on the official PDC Werner Ranking Ladder (£1,035,750)", "source": "https://www.pdc.tv/rankings"},
            {"claim": "Andrew Gilding ranks #27 on the official PDC Werner Ranking Ladder (£355,750)", "source": "https://www.pdc.tv/rankings"},
            {"claim": "European Championship R1 tie confirmed on OLBG Darts hub (event_id=32323)", "source": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gian_van_Veen_vs_Andrew_Gilding/15?event_id=32323"},
        ],
    },
    "pdc-32329": {
        "headline": "Top-16 seed Ross Smith brings triple Karel Sedlacek's PDC prize haul to Dortmund",
        "template": (
            "Ross Smith to defeat Karel Sedlacek in Thursday afternoon's PDC European Championship opener. "
            "Official PDC rankings place Smith 13th on £567,250 against world No. 44 Sedlacek on £177,250 — a £390,000 two-year prize gap that makes OLBG's slight underdog lean toward Sedlacek look mispriced. "
            "Over best-of-11 legs our model rates Smith at {prob_pct}% ({price} fair decimal)."
        ),
        "facts": [
            {"claim": "Ross Smith ranks #13 on the official PDC Werner Ranking Ladder (£567,250)", "source": "https://www.pdc.tv/rankings"},
            {"claim": "Karel Sedlacek ranks #44 on the official PDC Werner Ranking Ladder (£177,250)", "source": "https://www.pdc.tv/rankings"},
            {"claim": "European Championship R1 tie confirmed on OLBG Darts hub (event_id=32329)", "source": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Ross_Smith_vs_Karel_Sedlacek/15?event_id=32329"},
        ],
    },
    "pdc-32335": {
        "headline": "Fifth-ranked Jonny Clayton carries triple Niko Springer's ranking money into Friday's tie",
        "template": (
            "Jonny Clayton to win his PDC European Championship Round 1 clash against German youngster Niko Springer. "
            "Clayton holds world No. 5 status on £706,000 on the official PDC Werner Ranking Ladder compared with No. 36 Springer on £239,750. "
            "Across first-to-six legs our binomial leg model gives the Welshman a {prob_pct}% win probability ({price} fair odds)."
        ),
        "facts": [
            {"claim": "Jonny Clayton ranks #5 on the official PDC Werner Ranking Ladder (£706,000)", "source": "https://www.pdc.tv/rankings"},
            {"claim": "Niko Springer ranks #36 on the official PDC Werner Ranking Ladder (£239,750)", "source": "https://www.pdc.tv/rankings"},
            {"claim": "European Championship R1 tie confirmed on OLBG Darts hub (event_id=32335)", "source": "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Jonny_Clayton_vs_Niko_Springer/15?event_id=32335"},
        ],
    },
    "wst-9934": {
        "headline": "World No. 6 John Higgins brings nearly triple Jak Jones's ranking money into Belfast R2",
        "template": (
            "John Higgins to defeat Jak Jones in Wednesday's BetVictor Northern Ireland Open Round 2 clash in Belfast. "
            "Official Johnstone's Paint World Rankings place Higgins sixth on £905,000 across the two-year cycle against world No. 24 Jak Jones on £319,300, making OLBG's heavy public lean toward Jones a prime fade. "
            "Over best-of-seven frames our model puts Higgins at {prob_pct}% ({price})."
        ),
        "facts": [
            {"claim": "John Higgins ranks #6 on £905,000 in official WST World Rankings", "source": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false"},
            {"claim": "Jak Jones ranks #24 on £319,300 in official WST World Rankings", "source": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false"},
            {"claim": "Northern Ireland Open Match 45 confirmed on WST Match Centre", "source": "https://www.wst.tv/match-centre/eba55492-fba6-4a53-90be-a04b3560ae65"},
        ],
    },
}


def originate_nhl(nhl_teams: dict, fixtures: list[dict]) -> list[dict]:
    teams = {k: dict(v) for k, v in nhl_teams["teams"].items()}
    # Apply verified 2026-10-21T07:35Z NHL REST summary updates (including 20 Oct games; see L01)
    teams["TBL"].update({"gp": 9, "w": 7, "l": 2, "otl": 0, "gf": 31, "ga": 23, "points": 14})
    teams["VAN"].update({"gp": 11, "w": 2, "l": 8, "otl": 1, "gf": 33, "ga": 51, "points": 5})
    teams["VGK"].update({"gp": 11, "w": 8, "l": 3, "otl": 0, "gf": 43, "ga": 30, "points": 16})
    teams["CAR"].update({"gp": 11, "w": 8, "l": 2, "otl": 1, "gf": 42, "ga": 27, "points": 17})
    lg_gf = sum(t["gf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    rows: list[dict] = []
    for f in fixtures:
        h = teams[f["home"]]
        a = teams[f["away"]]
        k = 8.0
        att_h = ((h["gf"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        def_h = ((h["ga"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        att_a = ((a["gf"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        def_a = ((a["ga"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        lh = lg_gf * att_h * def_a * 1.05
        la = lg_gf * att_a * def_h
        grid = poisson_grid(lh, la)
        reg_h = sum(p for (i, j), p in grid.items() if i > j)
        reg_d = sum(p for (i, j), p in grid.items() if i == j)
        reg_a = sum(p for (i, j), p in grid.items() if i < j)
        p_home = reg_h + 0.52 * reg_d
        p_away = 1.0 - p_home
        p_h_pl = sum(p for (i, j), p in grid.items() if i - j >= 2)
        p_a_pl = 1.0 - p_h_pl
        tot_line = 5.5 if (lh + la) < 6.0 else 6.5
        p_over = sum(p for (i, j), p in grid.items() if (i + j) > tot_line)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        conf = grade(win_prob)
        rows.append(
            {
                "id": f"nhl-{f['game_id']}",
                "sport": "ice-hockey",
                "sport_name": "Ice Hockey",
                "competition": "NHL Regular Season 2026-27",
                "date": f["date"],
                "time": f["start_utc"],
                "home": h["name"],
                "away": a["name"],
                "venue": f["venue"],
                "line_status": "originated",
                "home_summary": f"{h['w']}-{h['l']}-{h['otl']} ({h['gf']} GF / {h['ga']} GA)",
                "away_summary": f"{a['w']}-{a['l']}-{a['otl']} ({a['gf']} GF / {a['ga']} GA)",
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": -1.5, "label": f"{h['name']} -1.5 / {a['name']} +1.5", "fav_prob": round(p_h_pl, 4), "dog_prob": round(p_a_pl, 4), "fav_odds": fair_decimal(p_h_pl), "dog_odds": fair_decimal(p_a_pl)},
                "total_market": {"line": tot_line, "projected": round(lh + la, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Moneyline)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": conf},
                "official_source": "NHL GameCenter & Stats API",
                "official_url": f"https://www.nhl.com/gamecenter/{f['away'].lower()}-vs-{f['home'].lower()}/{f['date'].replace('-', '/')}/{f['game_id']}",
                "data_url": "https://api.nhle.com/stats/rest/en/team/summary",
                "olbg_url": f.get("olbg_event_url") or "https://www.olbg.com/betting-tips/Ice_Hockey/13",
            }
        )
    return rows


def originate_nba(nba_teams: dict, fixtures: list[dict], extra_ids: dict) -> list[dict]:
    teams = nba_teams["teams"]
    rows: list[dict] = []
    k = 10.0
    for idx, f in enumerate(fixtures, 1):
        h = teams[f["home"]]
        a = teams[f["away"]]
        key = f"{f['away']}|{f['home']}|{f['date']}"
        gid = f.get("game_id") or extra_ids.get(key)
        slug_url = f"https://www.nba.com/game/{f['away'].lower()}-vs-{f['home'].lower()}-{gid}" if gid else "https://www.nba.com/games?date=2026-10-21"
        ph0 = (h["w"] + 0.5 * k) / (h["w"] + h["l"] + k)
        pa0 = (a["w"] + 0.5 * k) / (a["w"] + a["l"] + k)
        logit = math.log(ph0 / (1.0 - ph0)) - math.log(pa0 / (1.0 - pa0)) + 0.28
        p_home = logistic(logit)
        p_away = 1.0 - p_home
        exp_margin = logit * 6.8
        hcap = spread_line(exp_margin)
        p_cover = 1.0 - normal_cdf((-hcap - exp_margin) / 12.0)
        win_side = f["home"] if p_home >= p_away else f["away"]
        win_prob = max(p_home, p_away)
        conf = grade(win_prob, cap="medium")
        rows.append(
            {
                "id": f"nba-{gid or idx}",
                "sport": "basketball",
                "sport_name": "Basketball",
                "competition": "NBA Regular Season 2026-27 (Opening Night)",
                "date": f["date"],
                "time": f"{f['date']} {f['tip_et']} ET",
                "home": h["name"],
                "away": a["name"],
                "venue": None,
                "line_status": "originated",
                "home_summary": f"2025-26: {h['w']}-{h['l']} (Home {h['home_w']}-{h['home_l']})",
                "away_summary": f"2025-26: {a['w']}-{a['l']} (Road {a['road_w']}-{a['road_l']})",
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": None,  # Explicitly left blank: nba.com standings omit team points for/against
                "pick": {"selection": f"{win_side} (Moneyline)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": conf},
                "official_source": "NBA Official Game Page",
                "official_url": slug_url,
                "data_url": "https://www.nba.com/standings?Season=2025-26",
                "olbg_url": f.get("olbg_event_url") or "https://www.olbg.com/betting-tips/Basketball/19",
            }
        )
    return rows


def originate_euro_hoops(teams: dict, fixtures: list[dict], comp: str, standings_url: str) -> list[dict]:
    lg_ppg = sum(t["pf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    k = 3.0
    rows: list[dict] = []
    for f in fixtures:
        h = teams[f["home"]]
        a = teams[f["away"]]
        off_h = (h["pf"] + k * lg_ppg) / (h["gp"] + k)
        def_h = (h["pa"] + k * lg_ppg) / (h["gp"] + k)
        off_a = (a["pf"] + k * lg_ppg) / (a["gp"] + k)
        def_a = (a["pa"] + k * lg_ppg) / (a["gp"] + k)
        hca = 0.0 if f.get("neutral") else 3.4
        exp_h = 0.5 * (off_h + def_a) + 0.5 * hca
        exp_a = 0.5 * (off_a + def_h) - 0.5 * hca
        exp_margin = exp_h - exp_a
        exp_total = exp_h + exp_a
        p_home = normal_cdf(exp_margin / 10.8)
        p_away = 1.0 - p_home
        hcap = spread_line(exp_margin)
        p_cover = 1.0 - normal_cdf((-hcap - exp_margin) / 10.8)
        tline = half_line(exp_total)
        p_over = 1.0 - normal_cdf((tline - exp_total) / 13.5)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        rows.append(
            {
                "id": f["id"],
                "sport": "basketball",
                "sport_name": "Basketball",
                "competition": comp,
                "date": f["date"],
                "time": f["time"],
                "home": h["name"],
                "away": a["name"],
                "venue": f.get("venue"),
                "line_status": "originated",
                "home_summary": f"{h['w']}-{h['l']} ({h['pf']} PF / {h['pa']} PA)",
                "away_summary": f"{a['w']}-{a['l']} ({a['pf']} PF / {a['pa']} PA)",
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": tline, "projected": round(exp_total, 1), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Moneyline)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "Euroleague Basketball Official",
                "official_url": f["url"],
                "data_url": standings_url,
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_rugby(teams: dict, fixtures: list[dict], comp: str, standings_url: str, source_label: str) -> list[dict]:
    lg_ppg = sum(t["pf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    k = 3.0
    rows: list[dict] = []
    for f in fixtures:
        h = teams[f["home"]]
        a = teams[f["away"]]
        off_h = (h["pf"] + k * lg_ppg) / (h["gp"] + k)
        def_h = (h["pa"] + k * lg_ppg) / (h["gp"] + k)
        off_a = (a["pf"] + k * lg_ppg) / (a["gp"] + k)
        def_a = (a["pa"] + k * lg_ppg) / (a["gp"] + k)
        hca = 4.2
        exp_h = 0.5 * (off_h + def_a) + 0.5 * hca
        exp_a = 0.5 * (off_a + def_h) - 0.5 * hca
        exp_margin = exp_h - exp_a
        exp_total = exp_h + exp_a
        sigma = 12.6
        p_draw = normal_cdf((0.5 - exp_margin) / sigma) - normal_cdf((-0.5 - exp_margin) / sigma)
        p_home_1x2 = 1.0 - normal_cdf((0.5 - exp_margin) / sigma)
        p_away_1x2 = normal_cdf((-0.5 - exp_margin) / sigma)
        dnb_home = p_home_1x2 / (p_home_1x2 + p_away_1x2)
        hcap = spread_line(exp_margin)
        p_cover = 1.0 - normal_cdf((-hcap - exp_margin) / sigma)
        tline = half_line(exp_total)
        p_over = 1.0 - normal_cdf((tline - exp_total) / 14.2)
        win_side = h["name"] if p_home_1x2 >= p_away_1x2 else a["name"]
        win_prob = max(p_home_1x2, p_away_1x2)
        rows.append(
            {
                "id": f["id"],
                "sport": "rugby-union",
                "sport_name": "Rugby Union",
                "competition": comp,
                "date": f["date"],
                "time": f["time"],
                "home": h["name"],
                "away": a["name"],
                "venue": f.get("venue"),
                "line_status": "originated",
                "home_summary": f"{h['w']}W-{h['d']}D-{h['l']}L ({h['pf']} PF / {h['pa']} PA)",
                "away_summary": f"{a['w']}W-{a['d']}D-{a['l']}L ({a['pf']} PF / {a['pa']} PA)",
                "winner_market": {
                    "type": "1X2 Match Result",
                    "home_prob": round(p_home_1x2, 4),
                    "draw_prob": round(p_draw, 4),
                    "away_prob": round(p_away_1x2, 4),
                    "home_odds": fair_decimal(p_home_1x2),
                    "draw_odds": fair_decimal(p_draw),
                    "away_odds": fair_decimal(p_away_1x2),
                    "dnb_home_prob": round(dnb_home, 4),
                },
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": tline, "projected": round(exp_total, 1), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (1X2 Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": source_label,
                "official_url": f["url"],
                "data_url": standings_url,
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_handball(ehf_data: dict, olbg_map: dict) -> list[dict]:
    teams = ehf_data["teams"]
    lg_gf = sum(t["gf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    k = 3.0
    rows: list[dict] = []
    for f in ehf_data["fixtures"]:
        h = teams[f["home"]]
        a = teams[f["away"]]
        att_h = ((h["gf"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        def_h = ((h["ga"] + k * lg_gf) / (h["gp"] + k)) / lg_gf
        att_a = ((a["gf"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        def_a = ((a["ga"] + k * lg_gf) / (a["gp"] + k)) / lg_gf
        lh = lg_gf * att_h * def_a * 1.06
        la = lg_gf * att_a * def_h
        grid = poisson_grid(lh, la)
        p_home = sum(p for (i, j), p in grid.items() if i > j)
        p_draw = sum(p for (i, j), p in grid.items() if i == j)
        p_away = sum(p for (i, j), p in grid.items() if i < j)
        hcap = spread_line(lh - la)
        p_cover = sum(p for (i, j), p in grid.items() if (i - j) + hcap > 0)
        tline = half_line(lh + la)
        p_over = sum(p for (i, j), p in grid.items() if (i + j) > tline)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        rows.append(
            {
                "id": f["id"],
                "sport": "handball",
                "sport_name": "Handball",
                "competition": "EHF Champions League Men 2026/27 — Round 5",
                "date": f["date"],
                "time": f"{f['date']} {f['time_local']} {f['timezone']}",
                "home": h["name"],
                "away": a["name"],
                "venue": f["venue"],  # None where unconfirmed -> renders blank '—'
                "line_status": "originated",
                "home_summary": f"Grp {h['group']}: {h['w']}W-{h['d']}D-{h['l']}L ({h['gf']} GF / {h['ga']} GA)",
                "away_summary": f"Grp {a['group']}: {a['w']}W-{a['d']}D-{a['l']}L ({a['gf']} GF / {a['ga']} GA)",
                "winner_market": {"type": "1X2 Match Result", "home_prob": round(p_home, 4), "draw_prob": round(p_draw, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "draw_odds": fair_decimal(p_draw), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": hcap, "label": f"{h['name']} {hcap:+.1f}", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": tline, "projected": round(lh + la, 1), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (1X2 Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "EHF Official Match Details",
                "official_url": f["detail_url"],
                "data_url": "https://ehfcl.eurohandball.com/men/2026-27/standings/",
                "olbg_url": olbg_map.get(f["id"]),
            }
        )
    return rows


def originate_darts(players: dict, fixtures: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for f in fixtures:
        p1 = players[f["p1"]]
        p2 = players[f["p2"]]
        leg_p1 = logistic(0.24 * math.log(p1["prize_gbp"] / p2["prize_gbp"]))
        dist = best_of_race(leg_p1, target=6)
        m_p1 = sum(pr for a, b, pr in dist if a > b)
        m_p2 = 1.0 - m_p1
        hcap = -1.5 if m_p1 >= 0.5 else 1.5
        p_cover = sum(pr for a, b, pr in dist if (a - b) + hcap > 0)
        exp_legs = sum((a + b) * pr for a, b, pr in dist)
        p_over = sum(pr for a, b, pr in dist if (a + b) > 9.5)
        win_side = f["p1"] if m_p1 >= m_p2 else f["p2"]
        win_prob = max(m_p1, m_p2)
        rows.append(
            {
                "id": f["id"],
                "sport": "darts",
                "sport_name": "Darts",
                "competition": "2026 PDC European Championship — Round 1 (Best of 11 Legs)",
                "date": f["date"],
                "time": f["time"],
                "home": f["p1"],
                "away": f["p2"],
                "venue": "Westfalenhalle, Dortmund",
                "line_status": "originated",
                "home_summary": f"PDC #{p1['rank']} (£{p1['prize_gbp']:,})",
                "away_summary": f"PDC #{p2['rank']} (£{p2['prize_gbp']:,})",
                "winner_market": {"type": "2-way Match Winner", "home_prob": round(m_p1, 4), "away_prob": round(m_p2, 4), "home_odds": fair_decimal(m_p1), "away_odds": fair_decimal(m_p2)},
                "handicap_market": {"line": hcap, "label": f"{f['p1']} {hcap:+.1f} legs", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": 9.5, "projected": round(exp_legs, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "PDC Official Rankings",
                "official_url": "https://www.pdc.tv/rankings",
                "data_url": "https://www.pdc.tv/rankings",
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_tennis(players: dict, fixtures: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for f in fixtures:
        p1 = players[f["p1"]]
        p2 = players[f["p2"]]
        set_p1 = logistic(0.68 * math.log(p1["points"] / p2["points"]))
        dist = best_of_race(set_p1, target=2)
        m_p1 = sum(pr for a, b, pr in dist if a > b)
        m_p2 = 1.0 - m_p1
        hcap = -1.5 if m_p1 >= 0.5 else 1.5
        p_cover = sum(pr for a, b, pr in dist if (a - b) + hcap > 0)
        exp_sets = sum((a + b) * pr for a, b, pr in dist)
        p_over = sum(pr for a, b, pr in dist if (a + b) > 2.5)
        win_side = f["p1"] if m_p1 >= m_p2 else f["p2"]
        win_prob = max(m_p1, m_p2)
        rows.append(
            {
                "id": f["id"],
                "sport": "tennis",
                "sport_name": "Tennis",
                "competition": f["competition"],
                "date": f["date"],
                "time": f["time"],
                "home": f["p1"],
                "away": f["p2"],
                "venue": None,
                "line_status": "originated",
                "home_summary": f"ATP #{p1['rank']} ({p1['points']:,} pts)",
                "away_summary": f"ATP #{p2['rank']} ({p2['points']:,} pts)",
                "winner_market": {"type": "2-way Match Winner", "home_prob": round(m_p1, 4), "away_prob": round(m_p2, 4), "home_odds": fair_decimal(m_p1), "away_odds": fair_decimal(m_p2)},
                "handicap_market": {"line": hcap, "label": f"{f['p1']} {hcap:+.1f} sets", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": 2.5, "projected": round(exp_sets, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "ATP Tour Official",
                "official_url": f["url"],
                "data_url": "https://www.atptour.com/en/rankings/singles",
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_snooker(players: dict, fixtures: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for f in fixtures:
        p1 = players[f["p1"]]
        p2 = players[f["p2"]]
        frame_p1 = logistic(0.36 * math.log(p1["prize_gbp"] / p2["prize_gbp"]))
        dist = best_of_race(frame_p1, target=4)
        m_p1 = sum(pr for a, b, pr in dist if a > b)
        m_p2 = 1.0 - m_p1
        hcap = -1.5 if m_p1 >= 0.5 else 1.5
        p_cover = sum(pr for a, b, pr in dist if (a - b) + hcap > 0)
        exp_frames = sum((a + b) * pr for a, b, pr in dist)
        p_over = sum(pr for a, b, pr in dist if (a + b) > 5.5)
        win_side = f["p1"] if m_p1 >= m_p2 else f["p2"]
        win_prob = max(m_p1, m_p2)
        rows.append(
            {
                "id": f["id"],
                "sport": "snooker",
                "sport_name": "Snooker",
                "competition": "BetVictor Northern Ireland Open 2026 — Round 2 (Best of 7 Frames)",
                "date": f["date"],
                "time": f["time"],
                "home": f["p1"],
                "away": f["p2"],
                "venue": "Waterfront Hall, Belfast",
                "line_status": "originated",
                "home_summary": f"WST #{p1['rank']} (£{p1['prize_gbp']:,})",
                "away_summary": f"WST #{p2['rank']} (£{p2['prize_gbp']:,})",
                "winner_market": {"type": "2-way Match Winner", "home_prob": round(m_p1, 4), "away_prob": round(m_p2, 4), "home_odds": fair_decimal(m_p1), "away_odds": fair_decimal(m_p2)},
                "handicap_market": {"line": hcap, "label": f"{f['p1']} {hcap:+.1f} frames", "fav_prob": round(p_cover, 4), "dog_prob": round(1.0 - p_cover, 4), "fav_odds": fair_decimal(p_cover), "dog_odds": fair_decimal(1.0 - p_cover)},
                "total_market": {"line": 5.5, "projected": round(exp_frames, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{win_side} (Match Winner)", "team": win_side, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "WST Official Match Centre",
                "official_url": f["url"],
                "data_url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false",
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_mlb(ws: dict, live_mlb: dict) -> list[dict]:
    teams = live_mlb["teams"]
    rows = []
    lg = 4.45
    for f in live_mlb["fixtures"]:
        h = teams[f["home"]]
        a = teams[f["away"]]
        lh = lg * ((h["runs_scored"] / 162.0) / lg) * ((a["runs_allowed"] / 162.0) / lg) * 1.04
        la = lg * ((a["runs_scored"] / 162.0) / lg) * ((h["runs_allowed"] / 162.0) / lg)
        grid = poisson_grid(lh, la)
        reg_h = sum(p for (i, j), p in grid.items() if i > j)
        reg_d = sum(p for (i, j), p in grid.items() if i == j)
        p_home = reg_h + 0.51 * reg_d
        p_away = 1.0 - p_home
        fav_is_home = p_home >= p_away
        fav_name = h["name"] if fav_is_home else a["name"]
        dog_name = a["name"] if fav_is_home else h["name"]
        win_prob = max(p_home, p_away)
        if fav_is_home:
            p_rl = sum(p for (i, j), p in grid.items() if i - j >= 2)
        else:
            p_rl = sum(p for (i, j), p in grid.items() if j - i >= 2)
        p_over = sum(p for (i, j), p in grid.items() if (i + j) > 7.5)
        rows.append(
            {
                "id": f["id"],
                "sport": "baseball",
                "sport_name": "Baseball",
                "competition": f"2026 MLB {f['description']}",
                "date": f["official_date"],
                "time": f["game_date_utc"],
                "home": h["name"],
                "away": a["name"],
                "venue": f["venue"],
                "line_status": "originated",
                "home_summary": f"{h['wins']}-{h['losses']} ({h['runs_scored']} RS / {h['runs_allowed']} RA)",
                "away_summary": f"{a['wins']}-{a['losses']} ({a['runs_scored']} RS / {a['runs_allowed']} RA)",
                "winner_market": {"type": "2-way Moneyline", "home_prob": round(p_home, 4), "away_prob": round(p_away, 4), "home_odds": fair_decimal(p_home), "away_odds": fair_decimal(p_away)},
                "handicap_market": {"line": -1.5, "label": f"{fav_name} -1.5 / {dog_name} +1.5", "fav_prob": round(p_rl, 4), "dog_prob": round(1.0 - p_rl, 4), "fav_odds": fair_decimal(p_rl), "dog_odds": fair_decimal(1.0 - p_rl)},
                "total_market": {"line": 7.5, "projected": round(lh + la, 2), "over_prob": round(p_over, 4), "under_prob": round(1.0 - p_over, 4), "over_odds": fair_decimal(p_over), "under_odds": fair_decimal(1.0 - p_over)},
                "pick": {"selection": f"{fav_name} (Moneyline)", "team": fav_name, "probability": round(win_prob, 4), "fair_odds": fair_decimal(win_prob), "confidence": grade(win_prob)},
                "official_source": "MLB Stats API Official",
                "official_url": f["human_url"],
                "data_url": live_mlb["meta"]["standings_source"]["url"],
                "olbg_url": ws["olbg_url"],
            }
        )
    return rows


def originate_f1(drivers: list[dict]) -> list[dict]:
    weights = [d["points"] ** 1.65 for d in drivers]
    total_w = sum(weights) * 1.08  # 8% residual share for P9–P20 grid
    p_usgp_win = weights[0] / total_w
    p_usgp_field = 1.0 - p_usgp_win
    p_podium = min(0.88, 1.0 - (1.0 - p_usgp_win) ** 3)
    # Championship title probability given +102 pt cushion over #2 Russell with 7 rounds left
    gap = drivers[0]["points"] - drivers[1]["points"]
    p_title = normal_cdf(gap / 46.0)
    return [
        {
            "id": "f1-2026-usgp",
            "sport": "motor-racing",
            "sport_name": "Motor Racing",
            "competition": "2026 Formula 1 United States Grand Prix (Round 18, COTA)",
            "date": "2026-10-25",
            "time": "2026-10-25 20:00 UTC",
            "home": "Kimi Antonelli (Mercedes)",
            "away": "19-Driver Field (led by Russell 238, Hamilton 229, Verstappen 221)",
            "venue": "Circuit of the Americas, Austin",
            "line_status": "originated",
            "home_summary": "FIA #1 — 340 pts (17 rounds)",
            "away_summary": "Russell 238 · Hamilton 229 · Verstappen 221",
            "winner_market": {"type": "Race Outright Winner", "home_prob": round(p_usgp_win, 4), "away_prob": round(p_usgp_field, 4), "home_odds": fair_decimal(p_usgp_win), "away_odds": fair_decimal(p_usgp_field)},
            "handicap_market": {"line": -0.5, "label": "Antonelli Top-3 Podium Yes / No", "fav_prob": round(p_podium, 4), "dog_prob": round(1.0 - p_podium, 4), "fav_odds": fair_decimal(p_podium), "dog_odds": fair_decimal(1.0 - p_podium)},
            "total_market": None,
            "pick": {"selection": "Kimi Antonelli — Race Winner (Outright)", "team": "Kimi Antonelli (Mercedes)", "probability": round(p_usgp_win, 4), "fair_odds": fair_decimal(p_usgp_win), "confidence": grade(p_usgp_win)},
            "official_source": "Formula 1 Official Standings",
            "official_url": "https://www.formula1.com/en/results/2026/drivers",
            "data_url": "https://www.formula1.com/en/results/2026/drivers",
            "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        },
        {
            "id": "f1-2026-drivers",
            "sport": "motor-racing",
            "sport_name": "Motor Racing",
            "competition": "2026 FIA Formula 1 Drivers' World Championship — Outright",
            "date": "2026-12-06",
            "time": "Season Outright (7 Rounds Left)",
            "home": "Kimi Antonelli (Mercedes)",
            "away": "Chasing Pack (Russell 238, Hamilton 229, Verstappen 221)",
            "venue": None,
            "line_status": "originated",
            "home_summary": "FIA #1 — 340 pts (+102 lead)",
            "away_summary": "Russell #2 (238 pts) · Hamilton #3 (229 pts)",
            "winner_market": {"type": "Championship Outright", "home_prob": round(p_title, 4), "away_prob": round(1.0 - p_title, 4), "home_odds": fair_decimal(p_title), "away_odds": fair_decimal(1.0 - p_title)},
            "handicap_market": {"line": -65.5, "label": "Antonelli Season Margin -65.5 pts vs Russell", "fav_prob": round(normal_cdf((gap - 65.5) / 46.0), 4), "dog_prob": round(1.0 - normal_cdf((gap - 65.5) / 46.0), 4), "fav_odds": fair_decimal(normal_cdf((gap - 65.5) / 46.0)), "dog_odds": fair_decimal(1.0 - normal_cdf((gap - 65.5) / 46.0))},
            "total_market": None,
            "pick": {"selection": "Kimi Antonelli — 2026 World Champion", "team": "Kimi Antonelli (Mercedes)", "probability": round(p_title, 4), "fair_odds": fair_decimal(p_title), "confidence": grade(p_title)},
            "official_source": "Formula 1 Official Standings",
            "official_url": "https://www.formula1.com/en/results/2026/drivers",
            "data_url": "https://www.formula1.com/en/results/2026/drivers",
            "olbg_url": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        },
    ]


def main() -> None:
    inputs = read_json(VERIFIED / "inputs.json")
    nhl_teams = read_json(SHARED / "nhl_teams.json")
    nba_teams = read_json(SHARED / "nba_teams.json")
    shared_fx = read_json(SHARED / "fixtures.json")
    urc_raw = read_json(SHARED / "urc.json")
    ehf_raw = read_json(SHARED / "handball_ehf.json")
    sports_meta = {s["slug"]: s["name"] for s in read_json(VERIFIED / "sports.json")["eligible_sports"]}

    urc_teams = {
        k: {"name": v["name"], "gp": v["pl"], "w": v["w"], "d": v["d"], "l": v["l"], "pf": v["pf"], "pa": v["pa"]}
        for k, v in urc_raw["table"].items()
    }
    urc_fixtures = [
        {
            "id": f["id"],
            "date": f["date_local"],
            "time": f"{f['date_local']} {f['time_local']} Local",
            "home": f["home"],
            "away": f["away"],
            "venue": f["venue"],
            "url": f["url"],
            "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9",
        }
        for f in urc_raw["fixtures"]
    ]

    urc_r5_raw = json.loads((ROOT / "data" / "live" / "urc.json").read_text())
    live_mlb_raw = json.loads((ROOT / "data" / "live" / "mlb.json").read_text())
    urc_r5_fixtures = [
        {
            "id": f["id"],
            "date": f["date_local"],
            "time": f"{f['date_local']} {f['time_local']} Local",
            "home": f["home"],
            "away": f["away"],
            "venue": f["venue"],
            "url": f["url"],
            "olbg_url": "https://www.olbg.com/betting-tips/Rugby_Union/9",
        }
        for f in urc_r5_raw["fixtures"]
    ]

    originated: list[dict] = []
    originated.extend(originate_nhl(nhl_teams, shared_fx["nhl"]["fixtures"]))
    originated.extend(originate_nba(nba_teams, shared_fx["nba"]["fixtures"], inputs["nba_extra_game_ids"]))
    originated.extend(originate_euro_hoops(inputs["euroleague_teams"], inputs["euroleague_fixtures"], "EuroLeague 2026-27 — Round 7", "https://www.euroleaguebasketball.net/en/euroleague/standings/"))
    originated.extend(originate_euro_hoops(inputs["eurocup_teams"], inputs["eurocup_fixtures"], "BKT EuroCup 2026-27 — Round 4", "https://www.euroleaguebasketball.net/en/eurocup/standings/"))
    originated.extend(originate_rugby(inputs["top14_teams"], inputs["top14_fixtures"], "French Top 14 2026-27 — Journée 7", "https://top14.lnr.fr/classement", "LNR Official Top 14"))
    originated.extend(originate_rugby(inputs["prod2_teams"], inputs["prod2_fixtures"], "French Pro D2 2026-27 — Journée 8", "https://prod2.lnr.fr/classement", "LNR Official Pro D2"))
    originated.extend(originate_rugby(urc_teams, urc_fixtures, "United Rugby Championship 2026-27 — Round 4", "https://stats.unitedrugby.com/match-centre/table/2026-27", "URC Official Match Centre"))
    originated.extend(originate_rugby(urc_teams, urc_r5_fixtures, "United Rugby Championship 2026-27 — Round 5", "https://stats.unitedrugby.com/match-centre/table/2026-27", "URC Official Match Centre"))
    originated.extend(originate_handball(ehf_raw, inputs["ehf_olbg_map"]))
    originated.extend(originate_darts(inputs["pdc_players"], inputs["darts_fixtures"]))
    originated.extend(originate_tennis(inputs["atp_players"], inputs["tennis_originated"]))
    originated.extend(originate_snooker(inputs["wst_top36"], inputs["snooker_originated"]))
    originated.extend(originate_mlb(inputs["mlb_world_series"], live_mlb_raw))
    originated.extend(originate_f1(inputs["f1_drivers"]))

    unlined: list[dict] = []
    for u in inputs["unlined_rows"]:
        unlined.append(
            {
                "id": u["id"],
                "sport": u["sport"],
                "sport_name": sports_meta[u["sport"]],
                "competition": u["competition"],
                "date": u["date"],
                "time": u["time"],
                "home": u["home"],
                "away": u["away"],
                "venue": None,
                "line_status": "unlined",
                "home_summary": None,
                "away_summary": None,
                "winner_market": None,
                "handicap_market": None,
                "total_market": None,
                "pick": None,
                "blank_reason": u["blank_reason"],
                "official_source": u["official_source"],
                "official_url": u["official_url"],
                "data_url": None,
                "olbg_url": u.get("olbg_url"),
            }
        )

    all_rows = originated + unlined
    high_rows = [m for m in originated if m["pick"]["confidence"] == "high"]

    predictions: list[dict] = []
    missing_ids = [m["id"] for m in high_rows if m["id"] not in BESPOKE_HIGH_NARRATIVES]
    if missing_ids:
        raise RuntimeError(f"Missing bespoke human narratives for HIGH picks: {missing_ids}")

    for m in high_rows:
        spec = BESPOKE_HIGH_NARRATIVES[m["id"]]
        prob_pct = f"{m['pick']['probability'] * 100:.1f}"
        price = f"{m['pick']['fair_odds']:.2f}"
        text = spec["template"].format(prob_pct=prob_pct, price=price).replace("**", "")
        plain_words = len(text.split())
        if plain_words < 30:
            raise AssertionError(f"Prediction {m['id']} has only {plain_words} words (< 30)")
        predictions.append(
            {
                "match_id": m["id"],
                "sport": m["sport"],
                "sport_name": m["sport_name"],
                "competition": m["competition"],
                "event": f"{m['away']} @ {m['home']}" if m["sport"] in {"ice-hockey", "baseball"} else f"{m['home']} v {m['away']}",
                "time": m["time"],
                "selection": m["pick"]["selection"],
                "probability": m["pick"]["probability"],
                "fair_odds": m["pick"]["fair_odds"],
                "confidence": "high",
                "headline": spec["headline"],
                "text": text,
                "word_count": plain_words,
                "facts": spec["facts"],
                "official_url": m["official_url"],
                "olbg_url": m["olbg_url"],
            }
        )

    counts = {
        "total_rows": len(all_rows),
        "originated_rows": len(originated),
        "unlined_rows": len(unlined),
        "high_confidence": sum(1 for m in originated if m["pick"]["confidence"] == "high"),
        "medium_confidence": sum(1 for m in originated if m["pick"]["confidence"] == "medium"),
        "low_confidence": sum(1 for m in originated if m["pick"]["confidence"] == "low"),
    }
    write_json(VERIFIED / "matches.json", {"captured_at": "2026-10-21", "counts": counts, "matches": all_rows})
    write_json(VERIFIED / "predictions.json", {"captured_at": "2026-10-21", "min_words": 30, "count": len(predictions), "predictions": predictions})
    print(f"verified_model: {counts}")


if __name__ == "__main__":
    main()
