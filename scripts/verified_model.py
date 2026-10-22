#!/usr/bin/env python3
"""Independent multi-market line origination and human prediction builder for /verified/.

Reads the single self-contained official-input capture in data/verified/inputs.json
(written by scripts/verified_seed.py) and writes:
  - data/verified/matches.json
  - data/verified/predictions.json

Every lined match gets an independently originated winner market, handicap and
totals line plus a named pick graded low/medium/high. A per-match "featured"
selection is the strongest market (moneyline, handicap or totals) whose model
probability is >= 0.70 and whose fair American price sits inside the
-250..+10000 focus band; featured selections each carry a bespoke written
prediction of at least 30 words.

Zero bookmaker odds or tipster consensus percentages enter any equation.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "data" / "verified"

HIGH_THRESHOLD = 0.72
MEDIUM_THRESHOLD = 0.60
FEATURED_MIN_PROB = 0.70
AMERICAN_MIN = -250
AMERICAN_MAX = 10000


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fair_decimal(prob: float) -> float:
    return round(max(1.02, 1.0 / max(prob, 1e-6)), 2)


def fair_american(prob: float) -> int:
    """Fair (no-vig) American moneyline price implied by a model probability.

    Derived from the *published* rounded decimal price so the decimal and
    American figures on a row always agree; deriving both independently from
    the unrounded probability left three rows quoting two different prices for
    the same selection (e.g. 1.43 next to -230)."""
    dec = fair_decimal(prob)
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100))
    return int(round(-100.0 / (dec - 1.0)))


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


def _grid_margin_total_probs(grid: dict) -> tuple[dict, dict]:
    """Collapse a Poisson score grid into margin / total probability maps."""
    margin_probs: dict[int, float] = {}
    total_probs: dict[int, float] = {}
    for (i, j), p in grid.items():
        margin_probs[i - j] = margin_probs.get(i - j, 0.0) + p
        total_probs[i + j] = total_probs.get(i + j, 0.0) + p
    return margin_probs, total_probs


FIXTURE_SCOPED_URL_PATTERNS = (
    r"nhl\.com/gamecenter/",
    r"nba\.com/game/",
    r"euroleaguebasketball\.net/.*/game-center/.*/E2026/\d+/",
    r"feuille-de-match/",
    r"stats\.unitedrugby\.com/match-centre/\d{6}/",
    r"/matches/details/",
    r"wst\.tv/match-centre/",
    r"mlb\.com/gameday",
    r"icc-cricket\.com/matches/\d+",
)


def source_scope(url: str) -> str:
    """Whether the row's official URL identifies this fixture or only a competition.

    The dashboard prints this distinction on every table (VF-11). It is derived
    from the URL shape rather than asserted per row, so it cannot drift from the
    link a reader can actually click.
    """
    import re

    if not url:
        return "competition"
    for pattern in FIXTURE_SCOPED_URL_PATTERNS:
        if re.search(pattern, url):
            return "fixture"
    return "competition"


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


# Hand-crafted, non-templated human analyses for every featured selection
# (probability >= 0.70 with a fair American price inside -250..+10000).
# Each entry uses verified official figures only and embeds {selection},
# {prob_pct}, {price} and {american} directly from the live model run so
# prose and table numbers can never diverge.
BESPOKE_HIGH_NARRATIVES: dict[str, dict] = {
    "nhl-2026020162": {
        "headline": "Minnesota's 2.50 goals-against clamp meets Calgary's 2.13-per-game attack",
        "template": (
            "Back {selection} at Scotiabank Saddledome on Thursday night. "
            "Minnesota have banked 14 points from ten games (6-2-2) on the back of just 25 goals conceded (2.50 per game), while Calgary sit 2-6-0 having scored only 17 goals in eight outings and shipped 37. "
            "Our shrunk Poisson model makes the visiting Wild a {prob_pct}% shot ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Minnesota Wild stand 6-2-2 (14 pts, 31 GF, 25 GA) after ten games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Calgary Flames stand 2-6-0 (4 pts, 17 GF, 37 GA) after eight games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Game 2026020162 confirmed at Scotiabank Saddledome on the official NHL score feed", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
        ],
    },
    "nhl-2026020163": {
        "headline": "Two 15-plus-point starts collide in Edmonton — take Carolina with the goal and a half",
        "template": (
            "Take {selection} in Thursday's heavyweight clash at Rogers Place. "
            "Carolina have lost only twice in regulation through eleven games (8-2-1, 17 points, 42 scored against 27 allowed), a profile built on one-goal games, while Edmonton (7-1-1, 41-27) rarely blow elite opponents away. "
            "The +1.5 puck line cashes on any Hurricanes win or one-goal defeat including overtime, and our Poisson grid prices that cover at {prob_pct}% ({price}, {american} American)."
        ),
        "facts": [
            {"claim": "Carolina Hurricanes stand 8-2-1 (17 pts, 42 GF, 27 GA) after eleven games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Edmonton Oilers stand 7-1-1 (15 pts, 41 GF, 27 GA) after nine games", "source": "https://api.nhle.com/stats/rest/en/team/summary"},
            {"claim": "Game 2026020163 confirmed at Rogers Place on the official NHL score feed", "source": "https://api-web.nhle.com/v1/score/2026-10-22"},
        ],
    },
    "el-E2026-67": {
        "headline": "Athens fortress and +90 net differential make Panathinaikos overwhelming hosts",
        "template": (
            "Back {selection} in EuroLeague Round 7 at Telekom Center Athens rather than swallowing the ultra-short straight moneyline. "
            "Panathinaikos sit top of the 20-club standings at 5-1 with a competition-best +90 point differential (528 scored, 438 conceded) and a 4-1 home record. "
            "Baskonia arrive bottom at 1-5 (-60 differential, 0-2 away, allowing 94.0 points per game), so covering a reduced spread prices at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Panathinaikos lead the 2026-27 EuroLeague table at 5-1 (528 PF, 438 PA, +90, 4-1 home)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "Kosner Baskonia sit 20th at 1-5 (504 PF, 564 PA, -60, 0-2 road)", "source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
            {"claim": "Round 7 fixture confirmed at Telekom Center Athens on 22 October 2026", "source": "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/panathinaikos-aktor-athens-kosner-baskonia-vitoria-gasteiz/E2026/67/"},
        ],
    },
    "top14-11867": {
        "headline": "Table-topping Stade Toulousain bring five straight Top 14 victories to Ernest-Wallon",
        "template": (
            "Take {selection} against USA Perpignan on Saturday afternoon in Top 14 Journée 7. "
            "Toulouse sit first on 24 points (5W-0D-1L, 197 for, 124 against, +73) riding five consecutive league wins plus a 60-14 Champions Cup demolition of Sale Sharks. "
            "Ninth-placed Perpignan (3W-0D-3L, 166-199, -33) must keep it within a converted score to spoil a {prob_pct}% cover price ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Stade Toulousain lead Top 14 on 24 pts (5W-0D-1L, 197 PF, 124 PA, W-W-W-W-W)", "source": "https://top14.lnr.fr/classement"},
            {"claim": "USA Perpignan rank 9th on 13 pts (3W-0D-3L, 166 PF, 199 PA, -33)", "source": "https://top14.lnr.fr/classement"},
            {"claim": "Stade Toulousain beat Sale Sharks 60-14 in EPCR Champions Cup Round 1", "source": "https://top14.lnr.fr/club/toulouse"},
            {"claim": "Journée 7 fixture sheet 11867 confirmed on LNR", "source": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan"},
        ],
    },
    "prod2-12064": {
        "headline": "Seven-from-seven Provence Rugby host leaky Béziers in Aix-en-Provence",
        "template": (
            "Back {selection} against AS Béziers Hérault in Friday's Pro D2 Journée 8 card. "
            "Unbeaten Provence stand 7W-0D-0L on 29 points after conceding just 158 points across seven rounds (222 scored, +64). "
            "Fourteenth-placed Béziers have lost three of their last five matches while shipping 240 points (-93 differential), and covering a one-score alternate line rates {prob_pct}% ({price} fair decimal, {american} American)."
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
            "Back {selection} — Stade Aurillacois simply to beat USON Nevers at home in Pro D2 Journée 8. "
            "Aurillac arrive on back-to-back victories over Biarritz and Béziers to reach 16 points (3W-0D-4L, 240 points scored). "
            "Bottom-placed Nevers are the lone winless club in the division at 0W-0D-7L with a -76 differential (146 scored, 222 conceded), putting the home win at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Stade Aurillacois sit 9th on 16 pts (3W-0D-4L, 240 PF, 254 PA, consecutive wins)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "USON Nevers sit 16th on 4 pts (0W-0D-7L, 146 PF, 222 PA, -76)", "source": "https://prod2.lnr.fr/classement"},
            {"claim": "Journée 8 match sheet 12066 confirmed on LNR Pro D2", "source": "https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12066-aurillac-nevers"},
        ],
    },
    "urc-292609": {
        "headline": "Connacht host winless Zebre Parma (-64 differential) under Friday night lights in Galway",
        "template": (
            "Back {selection} — Connacht Rugby to defeat Zebre Parma at Dexcom Stadium in Friday's URC Round 4 meeting. "
            "Bottom-placed Zebre arrive at 0W-0D-3L with a competition-worst -64 differential (52 scored, 116 conceded) after losing 29-12 to Edinburgh on 10 October. "
            "Against 1W-0D-2L Connacht (56 PF, 84 PA) in Galway, our shrunk margin model prices the home win at {prob_pct}% ({price} fair decimal, {american} American)."
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
            "Take {selection} at home against 10bet Lions in Friday night's URC Round 4 fixture rather than the short outright price. "
            "Edinburgh sit top of the URC on 14 points as the only 3W-0D-0L side (80 PF, 54 PA) after beating Zebre 29-12 away, whereas the Lions shipped 57 points at Loftus last time out (77 PF, 102 PA overall). "
            "Winning by two or more rates {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Edinburgh lead the URC table at 3W-0D-0L (14 pts, 80 PF, 54 PA)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "10bet Lions sit 2W-0D-1L (77 PF, 102 PA) after losing 57-15 at Bulls on 10 Oct", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Round 4 fixture 292610 confirmed at Hive Stadium", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/edinburgh-rugby-vs-10bet-lions-2026-10-23/292610"},
        ],
    },
    "urc-292611": {
        "headline": "Loftus Versfeld firepower makes Vodacom Bulls heavy hosts against winless Ulster",
        "template": (
            "Back {selection} against Ulster Rugby at Loftus Versfeld on Saturday morning in URC Round 4. "
            "Pretoria's Bulls lead the entire URC in scoring with 126 points across three matches against only 54 conceded (+72), fresh off hammering the Lions 57-15 on 10 October. "
            "Winless Ulster enter at 0W-2D-1L (88 PF, 93 PA), and a four-point winning margin prices at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Vodacom Bulls stand 2W-0D-1L with a URC-high 126 PF and 54 PA (+72)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Vodacom Bulls beat 10bet Lions 57-15 on 10 October 2026", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Ulster Rugby stand winless at 0W-2D-1L (88 PF, 93 PA)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Round 4 fixture 292611 confirmed at Loftus Versfeld", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/vodacom-bulls-vs-ulster-rugby-2026-10-24/292611"},
        ],
    },
    "urc-292612": {
        "headline": "DHL Stormers' stingy Cape Town defence faces point-shy Scarlets in Round 4",
        "template": (
            "Take {selection} at DHL Stadium in Saturday's URC Round 4 clash with the Scarlets. "
            "Cape Town's Stormers stand 4th on 11 points (2W-0D-1L, 81 PF, joint-best 54 PA) coming off a comprehensive 39-22 home victory over the Sharks on 10 October. "
            "Twelfth-placed Scarlets sit 1W-0D-2L (-17 differential, 68 PF, 85 PA), making any home win beyond a penalty a {prob_pct}% cover ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "DHL Stormers stand 4th in the URC at 2W-0D-1L (81 PF, 54 PA, +27)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Stormers beat Hollywoodbets Sharks 39-22 on 10 October 2026", "source": "https://stats.unitedrugby.com/match-centre/2026-27/4"},
            {"claim": "Scarlets stand 12th at 1W-0D-2L (68 PF, 85 PA) before visiting DHL Stadium", "source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/dhl-stormers-vs-scarlets-2026-10-24/292612"},
        ],
    },
    "urc-292617": {
        "headline": "Second-placed Glasgow Warriors bring unbeaten Scotstoun record against leaky Lions",
        "template": (
            "Back {selection} in Friday night's URC Round 5 clash with 10bet Lions at Scotstoun Stadium. "
            "Unbeaten Glasgow sit second on 13 points (2W-1D-0L, 95 points scored, 72 conceded) after beating Connacht 36-19 at home on 9 October. "
            "Seventh-placed Lions have shipped 102 points in three games following their 57-15 loss in Pretoria, so a two-point home margin rates {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Glasgow Warriors sit 2nd in URC at 2W-1D-0L (13 pts, 95 PF, 72 PA) and beat Connacht 36-19", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "10bet Lions stand 2W-0D-1L (77 PF, 102 PA) after losing 57-15 at Bulls", "source": "https://stats.unitedrugby.com/match-centre/2026-27/5"},
        ],
    },
    "urc-292619": {
        "headline": "Vodacom Bulls' +72 scoring surge hosts point-negative Scarlets in Pretoria",
        "template": (
            "Back {selection} at Loftus Versfeld in Saturday's URC Round 5 fixture against the Scarlets. "
            "Pretoria's Bulls lead the URC with 126 points scored and only 54 allowed (+72) after their 57-15 demolition of the Lions, while twelfth-placed Scarlets sit 1W-0D-2L (-17 differential, 68 PF, 85 PA). "
            "Clearing a five-point alternate spread prices the hosts at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Vodacom Bulls lead the URC with 126 PF against 54 PA (+72) at 2W-0D-1L", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Scarlets sit 12th at 1W-0D-2L (68 PF, 85 PA) before visiting Loftus Versfeld", "source": "https://stats.unitedrugby.com/match-centre/2026-27/5"},
        ],
    },
    "urc-292622": {
        "headline": "Rodney Parade attack backs Dragons RFC against winless cellar-dwellers Zebre Parma",
        "template": (
            "Take {selection} at Rodney Parade against Zebre Parma in Saturday's URC Round 5 meeting. "
            "Eighth-placed Dragons hold a +5 differential on 9 points (1W-1D-1L, 88 PF, 83 PA) after scoring 31 points at home on 9 October, whereas bottom-placed Zebre are 0W-0D-3L with a competition-worst -64 differential (52 PF, 116 PA). "
            "Winning by four or more rates {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Dragons RFC stand 8th on 9 pts (1W-1D-1L, 88 PF, 83 PA)", "source": "https://stats.unitedrugby.com/match-centre/table/2026-27"},
            {"claim": "Zebre Parma sit 16th at 0W-0D-3L (1 pt, 52 PF, 116 PA, -64)", "source": "https://stats.unitedrugby.com/match-centre/2026-27/5"},
        ],
    },
    "ehfcl-202711020101049": {
        "headline": "Competition-best defence gives unbeaten Barça commanding home control over Montpellier",
        "template": (
            "Back {selection} at Palau Blaugrana in Thursday's EHF Champions League Group E clash instead of the prohibitive 1X2 price. "
            "Barça have won all four group fixtures (4W-0D-0L, 8 points) while conceding only 104 goals — the stingiest mark among all 24 clubs — alongside 137 goals scored. "
            "Against 1W-0D-3L Montpellier (116 GF, 125 GA), winning by four or more projects at {prob_pct}% ({price} fair decimal, {american} American)."
        ),
        "facts": [
            {"claim": "Barça lead Group E at 4W-0D-0L with 137 GF and 104 GA (fewest goals allowed in EHF CL)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "Montpellier Handball stand 3rd in Group E at 1W-0D-3L (116 GF, 125 GA)", "source": "https://ehfcl.eurohandball.com/men/2026-27/standings/"},
            {"claim": "EHF Round 5 match 202711020101049 scheduled 22 Oct 20:45 CEST", "source": "https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101049/Bar%C3%A7a-MontpellierHandball/"},
        ],
    },
}

def originate_nhl(teams: dict, fixtures: list[dict]) -> list[dict]:
    # Team goals are the official NHL Stats REST summary convention (the
    # shootout-deciding goal is excluded), captured in verified_seed.py.
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
                "_dist": {
                    "margin_probs": _grid_margin_total_probs(grid)[0],
                    "total_probs": _grid_margin_total_probs(grid)[1],
                    "unit": "goals",
                },
                "official_source": "NHL GameCenter & Stats API",
                "official_url": f"https://www.nhl.com/gamecenter/{f['away'].lower()}-vs-{f['home'].lower()}/{f['date'].replace('-', '/')}/{f['game_id']}",
                "data_url": "https://api.nhle.com/stats/rest/en/team/summary",
                "olbg_url": f.get("olbg_event_url") or "https://www.olbg.com/betting-tips/Ice_Hockey/13",
            }
        )
    return rows


def originate_nba(teams: dict, fixtures: list[dict]) -> list[dict]:
    # 2026-27 opening week: no current-season games have been played, so the
    # strength prior is each club's completed 2025-26 regular-season record
    # (copied into inputs.json by verified_seed.py). Confidence is therefore
    # capped at medium and NBA rows never become featured written predictions.
    rows: list[dict] = []
    k = 10.0
    for idx, f in enumerate(fixtures, 1):
        h = teams[f["home"]]
        a = teams[f["away"]]
        gid = f.get("game_id")
        slug_url = f"https://www.nba.com/game/{f['away'].lower()}-vs-{f['home'].lower()}-{gid}" if gid else f"https://www.nba.com/schedule?date={f['date']}"
        ph0 = (h["w"] + 0.5 * k) / (h["w"] + h["l"] + k)
        pa0 = (a["w"] + 0.5 * k) / (a["w"] + a["l"] + k)
        logit = math.log(ph0 / (1.0 - ph0)) - math.log(pa0 / (1.0 - pa0)) + 0.28
        p_home = logistic(logit)
        p_away = 1.0 - p_home
        exp_margin = logit * 6.8
        hcap = spread_line(exp_margin)
        p_cover = 1.0 - normal_cdf((-hcap - exp_margin) / 12.0)
        win_side = h["name"] if p_home >= p_away else a["name"]
        win_prob = max(p_home, p_away)
        conf = grade(win_prob, cap="medium")
        rows.append(
            {
                "id": f"nba-{gid or idx}",
                "sport": "basketball",
                "sport_name": "Basketball",
                "competition": "NBA Regular Season 2026-27 (Opening Week)",
                "date": f["date"],
                "time": f"{f['date']} {f['tip_et']} ET",
                "home": h["name"],
                "away": a["name"],
                "venue": f.get("venue"),
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
                "_dist": {"margin": (exp_margin, 10.8), "total": (exp_total, 13.5), "unit": "points"},
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
                "_dist": {"margin": (exp_margin, sigma), "total": (exp_total, 14.2), "unit": "points"},
                "official_source": source_label,
                "official_url": f["url"],
                "data_url": standings_url,
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


def originate_handball(teams: dict, fixtures: list[dict], olbg_map: dict) -> list[dict]:
    lg_gf = sum(t["gf"] for t in teams.values()) / sum(t["gp"] for t in teams.values())
    k = 3.0
    rows: list[dict] = []
    for f in fixtures:
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
                "_dist": {
                    "margin_probs": _grid_margin_total_probs(grid)[0],
                    "total_probs": _grid_margin_total_probs(grid)[1],
                    "unit": "goals",
                },
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
                "_dist": {"score_dist": dist, "unit": "legs"},
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
                "_dist": {"score_dist": dist, "unit": "sets"},
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
                "_dist": {"score_dist": dist, "unit": "frames"},
                "official_source": "WST Official Match Centre",
                "official_url": f["url"],
                "data_url": "https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false",
                "olbg_url": f["olbg_url"],
            }
        )
    return rows


MLB_OLBG_URL = "https://www.olbg.com/betting-tips/Baseball/12"
MLB_STANDINGS_URL = (
    "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
    "&standingsTypes=regularSeason"
)


def originate_mlb(teams: dict, fixtures: list[dict]) -> list[dict]:
    rows = []
    # League scoring rate derived only from the two verified World Series
    # clubs' official 162-game run totals (no outside constants).
    gp_total = sum(t["wins"] + t["losses"] for t in teams.values())
    rs_pg = sum(t["runs_scored"] for t in teams.values()) / gp_total
    ra_pg = sum(t["runs_allowed"] for t in teams.values()) / gp_total
    lg = 0.5 * (rs_pg + ra_pg)
    for f in fixtures:
        h = teams[f["home"]]
        a = teams[f["away"]]
        gp_h = h["wins"] + h["losses"]
        gp_a = a["wins"] + a["losses"]
        lh = lg * ((h["runs_scored"] / gp_h) / lg) * ((a["runs_allowed"] / gp_a) / lg) * 1.04
        la = lg * ((a["runs_scored"] / gp_a) / lg) * ((h["runs_allowed"] / gp_h) / lg)
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
                "_dist": {
                    "margin_probs": _grid_margin_total_probs(grid)[0],
                    "total_probs": _grid_margin_total_probs(grid)[1],
                    "unit": "runs",
                },
                "official_source": "MLB Stats API Official",
                "official_url": f["human_url"],
                "data_url": MLB_STANDINGS_URL,
                "olbg_url": MLB_OLBG_URL,
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


def _in_band(prob: float) -> bool:
    return prob >= FEATURED_MIN_PROB and AMERICAN_MIN <= fair_american(prob) <= AMERICAN_MAX


def _best_alt_line(prob_gt, lo: float, hi: float, quarters: bool = False) -> tuple[float, float] | None:
    """Alternate line whose P(value > line) lands closest to the middle of the
    featured band. Lines are always .5 fractions (no pushes); when `quarters`
    is set — continuous normal-margin models only — Asian .25/.75 lines are
    also scanned, priced from the same CDF, doubling line density so strong
    favourites can be repriced inside the -250 floor."""
    best: tuple[float, float] | None = None
    step = 0.5 if quarters else 1.0
    x = math.floor(lo) + (0.25 if quarters else 0.5)
    while x <= hi:
        p = prob_gt(x)
        if _in_band(p) and (best is None or abs(p - 0.7071) < abs(best[1] - 0.7071)):
            best = (x, p)
        x += step
    return best


def _fmt_line(v: float) -> str:
    s = f"{v:+.2f}".rstrip("0").rstrip(".")
    return s if s not in {"+", "-"} else f"{v:+.1f}"


def _alternate_candidates(row: dict) -> list[dict]:
    """Alternate handicap/total lines priced from the originator's own
    distribution so strong favourites can be taken at in-band prices
    (e.g. -6.5 instead of the main -13.5) instead of ultra-short moneylines."""
    dist = row.get("_dist")
    if not dist:
        return []
    home, away, unit = row["home"], row["away"], dist.get("unit", "points")
    out: list[dict] = []

    def add_handicaps(prob_gt_home, prob_gt_away, lo, hi, quarters=False):
        alt = _best_alt_line(prob_gt_home, lo, hi, quarters)
        if alt:
            line, p = alt
            out.append({"selection": f"{home} {_fmt_line(-line)} (Alternate Handicap)", "market": "Alternate Handicap", "probability": round(p, 4)})
        alt = _best_alt_line(prob_gt_away, lo, hi, quarters)
        if alt:
            line, p = alt
            out.append({"selection": f"{away} {_fmt_line(-line)} (Alternate Handicap)", "market": "Alternate Handicap", "probability": round(p, 4)})

    def add_totals(prob_gt_total, lo, hi):
        alt = _best_alt_line(prob_gt_total, lo, hi)
        if alt:
            line, p = alt
            out.append({"selection": f"Over {line:.1f} {unit} (Alternate Total)", "market": "Alternate Total", "probability": round(p, 4)})
        alt = _best_alt_line(lambda x: 1.0 - prob_gt_total(x), lo, hi)
        if alt:
            line, p = alt
            out.append({"selection": f"Under {line:.1f} {unit} (Alternate Total)", "market": "Alternate Total", "probability": round(p, 4)})

    if "margin" in dist:  # normal margin/total models (basketball, rugby)
        mu, sigma = dist["margin"]
        add_handicaps(
            lambda x: 1.0 - normal_cdf((x - mu) / sigma),
            lambda x: 1.0 - normal_cdf((x + mu) / sigma),
            mu - 2.2 * sigma,
            mu + 2.2 * sigma,
            quarters=True,
        )
        mu_t, sigma_t = dist["total"]
        add_totals(lambda x: 1.0 - normal_cdf((x - mu_t) / sigma_t), mu_t - 2.2 * sigma_t, mu_t + 2.2 * sigma_t)
    if "margin_probs" in dist:  # Poisson-grid models (NHL, handball, MLB)
        mp = {int(k): v for k, v in dist["margin_probs"].items()}
        tp = {int(k): v for k, v in dist["total_probs"].items()}
        neg = {-k: v for k, v in mp.items()}
        add_handicaps(
            lambda x: sum(p for v, p in mp.items() if v > x),
            lambda x: sum(p for v, p in neg.items() if v > x),
            min(mp),
            max(mp),
        )
        add_totals(lambda x: sum(p for v, p in tp.items() if v > x), min(tp), max(tp))
    if "score_dist" in dist:  # race formats (darts legs, snooker frames, tennis sets)
        sd = dist["score_dist"]
        add_handicaps(
            lambda x: sum(pr for a, b, pr in sd if (a - b) > x),
            lambda x: sum(pr for a, b, pr in sd if (b - a) > x),
            -8,
            8,
        )
        add_totals(lambda x: sum(pr for a, b, pr in sd if (a + b) > x), 0, 16)
    return out


def featured_selection(row: dict) -> dict | None:
    """Strongest in-band selection for one match across every originated market.

    A selection qualifies when its model probability is >= FEATURED_MIN_PROB
    and its fair American price falls inside [AMERICAN_MIN, AMERICAN_MAX], so
    the featured desk never pads itself with ultra-short prices. NBA opening
    week (prior-season records only) is excluded by design.
    """
    if row["competition"].startswith("NBA"):
        return None
    candidates: list[dict] = [
        {
            "selection": row["pick"]["selection"],
            "market": "Match Winner",
            "probability": row["pick"]["probability"],
        }
    ]
    hm = row.get("handicap_market")
    if hm:
        label = hm["label"]
        if " / " in label:  # fixed ±1.5 lines name both sides explicitly
            fav_label, dog_label = label.split(" / ", 1)
            candidates.append({"selection": f"{fav_label} (Handicap)", "market": "Handicap", "probability": hm["fav_prob"]})
            candidates.append({"selection": f"{dog_label} (Handicap)", "market": "Handicap", "probability": hm["dog_prob"]})
        else:
            candidates.append({"selection": f"{label} (Handicap)", "market": "Handicap", "probability": hm["fav_prob"]})
    tm = row.get("total_market")
    if tm:
        candidates.append({"selection": f"Over {tm['line']} (Match Total)", "market": "Match Total", "probability": tm["over_prob"]})
        candidates.append({"selection": f"Under {tm['line']} (Match Total)", "market": "Match Total", "probability": tm["under_prob"]})
    # Alternates only reprice existing conviction into the band — they never
    # manufacture a featured angle for a coin-flip match. Alternate handicaps
    # require a >= 0.70 moneyline pick and must back the pick's team; alternate
    # totals require a >= 0.60 lean on the main totals line in that direction.
    pick_prob = row["pick"]["probability"]
    pick_team = row["pick"].get("team") or ""
    for cand in _alternate_candidates(row):
        if cand["market"] == "Alternate Handicap":
            if pick_prob >= FEATURED_MIN_PROB and pick_team and cand["selection"].startswith(pick_team):
                candidates.append(cand)
        elif cand["market"] == "Alternate Total" and tm:
            if cand["selection"].startswith("Over") and tm["over_prob"] >= MEDIUM_THRESHOLD:
                candidates.append(cand)
            elif cand["selection"].startswith("Under") and tm["under_prob"] >= MEDIUM_THRESHOLD:
                candidates.append(cand)
    in_band = []
    for c in candidates:
        if _in_band(c["probability"]):
            in_band.append(
                {
                    **c,
                    "fair_odds": fair_decimal(c["probability"]),
                    "fair_american": fair_american(c["probability"]),
                    "confidence": "high",
                }
            )
    if not in_band:
        return None
    # The straight match winner is the cleanest expression of conviction;
    # alternate lines only headline when the moneyline itself is out of band.
    return max(in_band, key=lambda c: (c["market"] == "Match Winner", c["probability"]))


_BAND_MARKET_MAP = {
    "Match Winner": "moneyline",
    "Handicap": "handicap",
    "Alternate Handicap": "handicap",
    "Match Total": "total",
    "Alternate Total": "total",
}


def _band_pick(feat: dict) -> dict:
    import re

    m = re.search(r"([+-]?\d+\.\d+)", feat["selection"])
    return {
        "selection": feat["selection"],
        "market": _BAND_MARKET_MAP.get(feat["market"], feat["market"]),
        "line": float(m.group(1)) if m else None,
        "probability": feat["probability"],
        "fair_odds": feat["fair_odds"],
        "fair_american": feat["fair_american"],
        "confidence": "high",
        "price_band": "in-band",
    }


def main() -> None:
    inputs = read_json(VERIFIED / "inputs.json")
    captured_at = inputs["captured_at"]
    sports_meta = {s["slug"]: s["name"] for s in read_json(VERIFIED / "sports.json")["eligible_sports"]}

    originated: list[dict] = []
    originated.extend(originate_nhl(inputs["nhl_teams"], inputs["nhl_fixtures"]))
    originated.extend(originate_nba(inputs["nba_teams"], inputs["nba_fixtures"]))
    originated.extend(originate_euro_hoops(inputs["euroleague_teams"], inputs["euroleague_fixtures"], "EuroLeague 2026-27 — Round 7", "https://www.euroleaguebasketball.net/en/euroleague/standings/"))
    # EuroCup Round 5 was not captured this refresh (VF-12); the fixture list
    # is empty so this call is a no-op until the next official capture.
    originated.extend(originate_euro_hoops(inputs["eurocup_teams"], inputs["eurocup_fixtures"], "BKT EuroCup 2026-27", "https://www.euroleaguebasketball.net/en/eurocup/standings/"))
    originated.extend(originate_rugby(inputs["top14_teams"], inputs["top14_fixtures"], "French Top 14 2026-27 — Journée 7", "https://top14.lnr.fr/classement", "LNR Official Top 14"))
    originated.extend(originate_rugby(inputs["prod2_teams"], inputs["prod2_fixtures"], "French Pro D2 2026-27 — Journée 8", "https://prod2.lnr.fr/classement", "LNR Official Pro D2"))
    originated.extend(originate_rugby(inputs["urc_teams"], inputs["urc_r4_fixtures"], "United Rugby Championship 2026-27 — Round 4", "https://stats.unitedrugby.com/match-centre/table/2026-27", "URC Official Match Centre"))
    originated.extend(originate_rugby(inputs["urc_teams"], inputs["urc_r5_fixtures"], "United Rugby Championship 2026-27 — Round 5", "https://stats.unitedrugby.com/match-centre/table/2026-27", "URC Official Match Centre"))
    originated.extend(originate_handball(inputs["ehf_teams"], inputs["ehf_fixtures"], inputs["ehf_olbg_map"]))
    originated.extend(originate_darts(inputs["pdc_players"], inputs["darts_fixtures"]))
    originated.extend(originate_tennis(inputs["atp_players"], inputs["tennis_originated"]))
    originated.extend(originate_snooker(inputs["wst_top36"], inputs["snooker_originated"]))
    originated.extend(originate_mlb(inputs["mlb_teams"], inputs["mlb_fixtures"]))
    originated.extend(originate_f1(inputs["f1_drivers"]))

    for row in originated:
        pick = row["pick"]
        pick["fair_american"] = fair_american(pick["probability"])
        # The published grading copy (root pages, /verified/ methodology) reads
        # "high >= 72%, or a band pick >= 70%". Apply that second clause to the
        # row's own pick as well: three rows previously showed the same
        # selection as HIGH on the picks page and MEDIUM in their match row.
        # NBA keeps its medium cap (prior-season records only).
        if (
            not row["competition"].startswith("NBA")
            and pick["probability"] >= FEATURED_MIN_PROB
            and AMERICAN_MIN <= pick["fair_american"] <= AMERICAN_MAX
        ):
            pick["confidence"] = "high"
        row["source_scope"] = source_scope(row["official_url"])
        row["featured"] = featured_selection(row)
        # band_pick mirrors `featured` for the root dashboard / band.json
        # contract introduced by session 36f79c71 (same -250..+10000 rule).
        row["band_pick"] = _band_pick(row["featured"]) if row["featured"] else None
        row.pop("_dist", None)  # ephemeral distribution used only for alternates

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
                "featured": None,
                "band_pick": None,
                "blank_reason": u["blank_reason"],
                "official_source": u["official_source"],
                "official_url": u["official_url"],
                "source_scope": source_scope(u["official_url"]),
                "data_url": None,
                "olbg_url": u.get("olbg_url"),
            }
        )

    all_rows = originated + unlined
    featured_rows = [m for m in originated if m.get("featured")]

    if os.environ.get("VERIFIED_DRY_RUN"):
        for m in featured_rows:
            f = m["featured"]
            print(
                f"{m['id']:24s} {f['selection']:52s} p={f['probability']:.3f} "
                f"dec={f['fair_odds']:.2f} am={f['fair_american']:+d} | pick p={m['pick']['probability']:.3f}"
            )
        print(f"originated={len(originated)} unlined={len(unlined)} featured={len(featured_rows)}")
        print("missing narratives:", [m["id"] for m in featured_rows if m["id"] not in BESPOKE_HIGH_NARRATIVES])
        print("stale narratives:", [k for k in BESPOKE_HIGH_NARRATIVES if k not in {m['id'] for m in featured_rows}])
        return

    predictions: list[dict] = []
    missing_ids = [m["id"] for m in featured_rows if m["id"] not in BESPOKE_HIGH_NARRATIVES]
    if missing_ids:
        raise RuntimeError(f"Missing bespoke human narratives for featured selections: {missing_ids}")

    for m in featured_rows:
        spec = BESPOKE_HIGH_NARRATIVES[m["id"]]
        feat = m["featured"]
        prob_pct = f"{feat['probability'] * 100:.1f}"
        price = f"{feat['fair_odds']:.2f}"
        american = f"{feat['fair_american']:+d}"
        text = spec["template"].format(
            prob_pct=prob_pct, price=price, american=american, selection=feat["selection"]
        ).replace("**", "")
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
                "selection": feat["selection"],
                "market": feat["market"],
                "match_type": "band",
                "probability": feat["probability"],
                "fair_odds": feat["fair_odds"],
                "fair_american": feat["fair_american"],
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
        "featured": len(featured_rows),
    }
    write_json(VERIFIED / "matches.json", {"captured_at": captured_at, "counts": counts, "matches": all_rows})
    write_json(VERIFIED / "predictions.json", {"captured_at": captured_at, "min_words": 30, "count": len(predictions), "predictions": predictions})
    band_selections = [
        {
            "id": m["id"],
            "date": m["date"],
            "sport": m["sport"],
            **{k: m["band_pick"][k] for k in ("selection", "market", "line", "probability", "fair_odds", "confidence", "price_band")},
        }
        for m in featured_rows
    ]
    write_json(
        VERIFIED / "band.json",
        {
            "captured_at": captured_at,
            "definition": {"min_decimal": 1.4, "max_decimal": 101.0, "min_probability": 0.7},
            "selections": band_selections,
        },
    )
    print(f"verified_model: {counts}")


if __name__ == "__main__":
    main()
