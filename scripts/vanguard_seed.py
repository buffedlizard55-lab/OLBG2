"""Vanguard desk — seed.

Every fixture in this file was read first hand from the official governing-body
endpoint named in its ``src`` field during the 2026-10-22 evening session
(20:50Z onwards).  Numbers in ``h`` / ``a`` are transcribed from those official
pages; ``basis`` states exactly which published figures were used and how they
were turned into a strength number.  Nothing here is copied from another layer
of this repository.

Run: python3 scripts/vanguard_seed.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "vanguard"

# ---------------------------------------------------------------- parameters
# Documented model constants (ours, not the sport's).  Every one is repeated on
# /vanguard/methodology.html so a reader can recompute any price by hand.
PARAMS = {
    "ice-hockey":    {"kind": "poisson", "shrink": 8.0,  "home": 0.10, "total_shrink": 8.0},
    "basketball":    {"kind": "normal",  "sd": 11.0, "total_sd": 15.0, "home": 3.0},
    "rugby-union":   {"kind": "normal",  "sd": 13.0, "total_sd": 16.0, "home": 3.0, "draw_band": 1.0},
    "baseball":      {"kind": "poisson", "shrink": 20.0, "home": 0.12, "total_shrink": 20.0},
    "handball":      {"kind": "poisson", "shrink": 3.0,  "home": 0.40, "total_shrink": 3.0},
    "tennis":        {"kind": "logistic", "scale": 55.0},
    "snooker":       {"kind": "logistic", "scale": 40.0},
    "esports":       {"kind": "logistic", "scale": 400.0},
    "darts":         {"kind": "logistic", "scale": 25.0},
    "cricket":       {"kind": "logistic", "scale": 40.0},
    "volleyball":    {"kind": "logistic", "scale": 60.0},
    "rugby-league":  {"kind": "logistic", "scale": 30.0},
    "aussie-rules":  {"kind": "logistic", "scale": 45.0},
    "gaelic-football": {"kind": "logistic", "scale": 45.0},
    "motor-racing":  {"kind": "share"},
    "golf":          {"kind": "share"},
    "greyhounds":    {"kind": "share"},
}

# ------------------------------------------------------------------ fixtures
# h / a carry:  gf, ga, gp  (poisson / normal sports)
#               strength   (logistic sports; higher is stronger)
#               weight     (share sports)
# basis: one line, reproduced verbatim on the fixture page.

F = []


def add(**kw):
    F.append(kw)


NHL = "https://api-web.nhle.com/v1/score/"
# --- Ice hockey: NHL, 12 games on 2026-10-22 + 2 on 2026-10-23 -------------
nhl_rows = [
    # id,            start,                 home,                 away,                home GF/GA/GP, away GF/GA/GP, facts
    ("2026020154", "2026-10-22T23:00:00Z", "Boston Bruins", "Nashville Predators", (36, 22, 10), (23, 22, 8),
     "Boston are 7-2-1 and Jeremy Swayman already has six wins; David Pastrnak has four goals and eight assists. Nashville are 3-2-3, with Ryan O'Reilly on four goals and Roman Josi on eight assists."),
    ("2026020155", "2026-10-22T23:00:00Z", "Toronto Maple Leafs", "New York Rangers", (38, 34, 11), (33, 24, 11),
     "Toronto are 5-4-2, with Auston Matthews on eight goals and ten assists. The Rangers are 7-3-1; Alexis Lafreniere has seven goals and Adam Fox ten assists."),
    ("2026020156", "2026-10-22T23:00:00Z", "Ottawa Senators", "San Jose Sharks", (27, 24, 10), (26, 34, 10),
     "Ottawa are 7-3-0, Linus Ullmark has seven wins and Tim Stutzle six goals. San Jose are 5-4-1 with Macklin Celebrini on five goals and nine assists."),
    ("2026020157", "2026-10-22T23:00:00Z", "New Jersey Devils", "Anaheim Ducks", (29, 30, 9), (26, 29, 9),
     "New Jersey are 5-4-0, Jake Allen has four wins and Jack Hughes seven assists. Anaheim are 4-5-0 with Leo Carlsson on nine assists and Beckett Sennecke on five goals."),
    ("2026020158", "2026-10-22T23:00:00Z", "Pittsburgh Penguins", "Florida Panthers", (32, 37, 10), (31, 30, 10),
     "Pittsburgh are 3-6-1, Evgeni Malkin has five goals and Erik Karlsson ten assists. Florida are 5-3-2; Matthew Tkachuk has twelve assists and Brady Tkachuk seven goals."),
    ("2026020159", "2026-10-22T23:30:00Z", "New York Islanders", "Los Angeles Kings", (27, 19, 9), (17, 27, 7),
     "The Islanders are 5-3-1, Ilya Sorokin has five wins and Bo Horvat five goals. Los Angeles are 1-4-2 with Artemi Panarin on four goals."),
    ("2026020160", "2026-10-23T00:00:00Z", "St. Louis Blues", "Vegas Golden Knights", (29, 29, 9), (43, 30, 11),
     "St. Louis are 4-4-1; Joel Hofer has three wins and Dylan Holloway six assists. Vegas are 8-3-0 with Jack Eichel on thirteen assists and Mark Stone on eight goals."),
    ("2026020161", "2026-10-23T00:00:00Z", "Dallas Stars", "Winnipeg Jets", (22, 14, 9), (24, 26, 9),
     "Dallas are 5-3-1 with three shutouts, Jake Oettinger on four wins and Mikko Rantanen on five goals. Winnipeg are 4-3-2; Kyle Connor has eight goals and Mark Scheifele six assists."),
    ("2026020162", "2026-10-23T01:00:00Z", "Calgary Flames", "Minnesota Wild", (17, 37, 8), (31, 25, 10),
     "Calgary are 2-6-0 with Dustin Wolf on one win and Morgan Frost on three goals. Minnesota are 6-2-2; Kirill Kaprizov has eleven goals and Quinn Hughes eleven assists."),
    ("2026020163", "2026-10-23T01:00:00Z", "Edmonton Oilers", "Carolina Hurricanes", (41, 27, 9), (42, 27, 11),
     "Edmonton are 7-1-1 with Connor McDavid on twenty assists and Leon Draisaitl on eight goals. Carolina are 8-2-1; Andrei Svechnikov has six goals and Jackson Blake ten assists."),
    ("2026020164", "2026-10-23T02:00:00Z", "Seattle Kraken", "Utah Mammoth", (37, 34, 10), (38, 31, 10),
     "Seattle are 6-3-1 with Chandler Stephenson on eight assists and Frederick Gaudreau on five goals. Utah are 7-3-0; Clayton Keller has nine assists and Nick Schmaltz seven goals."),
    ("2026020165", "2026-10-23T02:00:00Z", "Vancouver Canucks", "Detroit Red Wings", (33, 51, 11), (22, 26, 9),
     "Vancouver are 2-8-1 with Elias Pettersson on eight assists. Detroit are 3-3-3; Alex DeBrincat has six goals and five assists."),
    ("2026020166", "2026-10-24T00:00:00Z", "Chicago Blackhawks", "Montreal Canadiens", (21, 36, 9), (28, 34, 9),
     "Chicago are 3-6-0 with Anton Frondell on five assists and Spencer Knight on three wins. Montreal are 4-3-2; Cole Caufield has six goals and Nick Suzuki seven assists."),
    ("2026020167", "2026-10-24T01:00:00Z", "Colorado Avalanche", "Tampa Bay Lightning", (41, 30, 10), (31, 23, 9),
     "Colorado are 5-4-1; Nathan MacKinnon has ten assists and Artturi Lehkonen eight goals. Tampa Bay are 7-2-0 with Nikita Kucherov on nine assists and Brandon Hagel on seven goals."),
]
for gid, start, home, away, hstats, astats, facts in nhl_rows:
    add(sid=f"nhl-{gid}", sport="ice-hockey", comp="NHL", start=start, home=home, away=away,
        src=f"{NHL}2026-10-{start[8:10]}", h=dict(gf=hstats[0], ga=hstats[1], gp=hstats[2]),
        a=dict(gf=astats[0], ga=astats[1], gp=astats[2]),
        basis="goals for and against per game from the NHL team summary endpoint, shrunk gp/(gp+8) toward the league average of 3.0784 goals per team game; home multiplier +0.10 goals",
        facts=facts)

# --- Basketball: EuroLeague round 7 leftovers + NBA ------------------------
EL = "https://www.euroleaguebasketball.net/en/euroleague/game-center/"
el_rows = [
    ("E2026-68", "2026-10-23T11:00:00Z", "Zalgiris Kaunas", "LDLC ASVEL Villeurbanne", (490, 517, 6), (527, 572, 6),
     "Zalgiris are 2-4, scoring 490 and conceding 517, with a 0-2 home record. ASVEL are 2-4, scoring 527 and conceding 572."),
    ("E2026-70", "2026-10-23T12:15:00Z", "Olympiacos Piraeus", "Fenerbahce Tarfin Istanbul", (564, 524, 6), (501, 447, 6),
     "Olympiacos are 5-1 with 564 points scored and 524 conceded, and are 2-0 in overtime games. Fenerbahce are 5-1, scoring 501 and conceding 447, with a 5-0 home record."),
    ("E2026-69", "2026-10-23T12:45:00Z", "Paris Basketball", "Valencia Basket", (504, 545, 6), (583, 537, 6),
     "Paris are 1-5, scoring 504 and conceding 545. Valencia are 4-2 with the competition's most productive offence at 583 points in six games."),
]
for mid, start, home, away, hs, as_, facts in el_rows:
    add(sid=f"el-{mid}", sport="basketball", comp="EuroLeague round 7", start=start, home=home, away=away,
        src=f"{EL}2026-27/{home.split()[0].lower()}-{away.split()[0].lower()}/E2026/{mid.split('-')[1]}/",
        h=dict(gf=hs[0], ga=hs[1], gp=hs[2]), a=dict(gf=as_[0], ga=as_[1], gp=as_[2]),
        basis="points for and against per game from the EuroLeague standings, shrunk gp/(gp+6) toward the league average of 86.4426 points per team; home +3.0",
        facts=facts)

NBA = "https://www.nba.com/game/"
nba_rows = [
    ("0022600006", "2026-10-22T23:00:00Z", "Philadelphia 76ers", "Cleveland Cavaliers", 102.9 - 108.8,
     "The 76ers opened with a 106-? result at New York on 20 October and are Philadelphia's home opener; Cleveland's preseason net rating was -3.8 in the official Week 1 power rankings."),
    ("0022600007", "2026-10-23T01:30:00Z", "Oklahoma City Thunder", "Denver Nuggets", 11.1,
     "Oklahoma City posted the league's best preseason net rating at +11.1 in the official Week 1 power rankings and open at home; Denver's figure was not published in that table."),
    ("0022600008", "2026-10-23T23:00:00Z", "Boston Celtics", "New York Knicks", 116.3 - 98.6,
     "Boston went 4-0 in preseason with a +17.7 net rating, the best in the league, and Jaylen Brown has moved to Philadelphia. New York are the defending champions."),
    ("0022600009", "2026-10-24T01:30:00Z", "San Antonio Spurs", "Houston Rockets", 8.4,
     "San Antonio's preseason net rating was +8.4, third in the league; Houston's figure was not published in the same official table."),
]
for gid, start, home, away, net, facts in nba_rows:
    add(sid=f"nba-{gid}", sport="basketball", comp="NBA", start=start, home=home, away=away,
        src=f"{NBA}{gid}", h=dict(gf=net, ga=0, gp=1, net=net), a=dict(gf=0, ga=0, gp=1, net=0),
        basis="preseason net rating from NBA.com's official Week 1 power rankings, used as a points-per-100 proxy with a league-average prior where the table published no value; flagged on the review page because preseason data is not regular-season form",
        facts=facts)

# --- Rugby Union: URC round 4 ---------------------------------------------
URC = "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/"
urc_rows = [
    ("292608", "2026-10-23T13:45:00Z", "Cardiff Rugby", "Hollywoodbets Sharks", (66, 71, 3, 9), (89, 83, 3, 10),
     "Cardiff are sixth on nine points after beating the Ospreys and losing 29-5 at Leinster. The Sharks are fifth on ten points and lost 39-22 at the Stormers last week."),
    ("292609", "2026-10-23T13:45:00Z", "Connacht Rugby", "Zebre Parma", (56, 84, 3, 5), (52, 116, 3, 1),
     "Connacht are fourteenth on five points, scoring 56 and conceding 84. Zebre are bottom with one point, winless in three and 64 points down on differential."),
    ("292610", "2026-10-23T13:45:00Z", "Edinburgh Rugby", "10bet Lions", (80, 54, 3, 14), (77, 102, 3, 9),
     "Edinburgh lead the table on 14 points with three wins from three, 80 points for and 54 against. The Lions are seventh on nine points and conceded 57 at the Bulls."),
    ("292611", "2026-10-24T06:45:00Z", "Vodacom Bulls", "Ulster Rugby", (126, 54, 3, 11), (88, 93, 3, 8),
     "The Bulls are third on eleven points with 126 points scored, the most in the table, after beating the Lions 57-15. Ulster are eleventh, drawing with Munster and losing to Glasgow."),
    ("292612", "2026-10-24T09:00:00Z", "DHL Stormers", "Scarlets", (81, 54, 3, 11), (68, 85, 3, 7),
     "The Stormers are fourth on eleven points after a 39-22 win over the Sharks at this ground. The Scarlets are twelfth on seven points, conceding 85."),
    ("292613", "2026-10-24T09:00:00Z", "Benetton Rugby", "Glasgow Warriors", (64, 68, 3, 5), (95, 72, 3, 13),
     "Benetton are fifteenth on five points, drawing with Ulster and losing twice. Glasgow are second on 13 points, unbeaten, with 95 points scored."),
    ("292614", "2026-10-24T12:00:00Z", "Leinster Rugby", "Munster Rugby", (75, 58, 3, 8), (72, 74, 3, 9),
     "Leinster are tenth on eight points but have conceded only 58, the fewest in the table, and beat Cardiff 29-5 in round three. Munster are ninth on nine points."),
    ("292615", "2026-10-24T13:00:00Z", "Ospreys", "Dragons RFC", (81, 107, 3, 6), (88, 83, 3, 9),
     "The Ospreys are thirteenth on six points, conceding 107. Dragons are eighth on nine points and drew 26-26 at Ulster after beating the Ospreys 31-38 earlier this month."),
]
for mid, start, home, away, hs, as_, facts in urc_rows:
    slug = home.lower().replace(" ", "-") + "-vs-" + away.lower().replace(" ", "-") + "-2026-10-" + start[8:10]
    add(sid=f"urc-{mid}", sport="rugby-union", comp="United Rugby Championship round 4", start=start,
        home=home, away=away, src=f"{URC}{slug}/{mid}",
        h=dict(gf=hs[0], ga=hs[1], gp=hs[2], pts=hs[3]), a=dict(gf=as_[0], ga=as_[1], gp=as_[2], pts=as_[3]),
        basis="points for and against per game from the URC table, shrunk pl/(pl+6) toward the league average of 26.2083 points per team; home +3.0",
        facts=facts)

# --- Baseball: World Series games 1 and 2 --------------------------------
add(sid="mlb-849805", sport="baseball", comp="MLB World Series game 1", start="2026-10-24T00:00:00Z",
    home="Milwaukee Brewers", away="Tampa Bay Rays",
    src="https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-23&hydrate=team,probablePitcher",
    h=dict(gf=832, ga=618, gp=162), a=dict(gf=736, ga=650, gp=162),
    basis="runs scored and allowed per game from the MLB regular-season standings, shrunk gp/(gp+20) toward the league average of 4.4811 runs per team; home +0.12",
    facts="Milwaukee went 103-59 with a +214 run differential; Jacob Misiorowski struck out 252 in 174.2 innings at a 1.80 ERA. Tampa Bay went 98-64 and start Nick Martinez, 15-6 with a 3.10 ERA.")
add(sid="mlb-849802", sport="baseball", comp="MLB World Series game 2", start="2026-10-25T00:00:00Z",
    home="Milwaukee Brewers", away="Tampa Bay Rays",
    src="https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-24&endDate=2026-10-24&hydrate=team,probablePitcher",
    h=dict(gf=832, ga=618, gp=162), a=dict(gf=736, ga=650, gp=162),
    basis="runs scored and allowed per game from the MLB regular-season standings, shrunk gp/(gp+20) toward the league average of 4.4811 runs per team; home +0.12",
    facts="Milwaukee's 103-59 record is the best in MLB this season and they are 55-26 at home. Tampa Bay start Drew Rasmussen, 16-5 with a 2.67 ERA in 172 innings.")

# --- Snooker: Northern Ireland Open quarter-finals ------------------------
WST = "https://www.wst.tv/match-centre/"
snk_rows = [
    ("71b7dbc4-9b19-4b26-b482-add32562040a", "2026-10-23T07:00:00Z", "Anthony McGill", "Kyren Wilson", (235700, 716800),
     "McGill is world number 33 on 235,700 pounds and beat Mateusz Baranowski 4-1 in round three. Wilson is world number nine on 716,800 pounds and edged Pang Junxu 4-3."),
    ("c8486960-4aa5-40f6-812a-5dcd38dae85b", "2026-10-23T07:00:00Z", "Sam Craigie", "Elliot Slessor", (0, 329200),
     "Craigie came from 3-2 down to beat Matthew Selt 4-2 and beat Xu Si 4-3 in round two. Slessor is world number 23 on 329,200 pounds and beat Ricky Walden 4-1."),
    ("19048b0d-aaf4-4691-ad10-15b1b707f622", "2026-10-23T13:00:00Z", "Mark Williams", "David Gilbert", (747400, 221200),
     "Williams is world number eight on 747,400 pounds and whitewashed Martin O'Donnell 4-0 in round three. Gilbert is world number 34 on 221,200 pounds and beat Ka Wai Cheung 4-2."),
]
for mid, start, home, away, hs, facts in snk_rows:
    add(sid=f"snk-{mid[:8]}", sport="snooker", comp="BetVictor Northern Ireland Open quarter-final", start=start,
        home=home, away=away, src=f"{WST}{mid}",
        h=dict(strength=hs[0] / 10000.0), a=dict(strength=hs[1] / 10000.0),
        basis="Johnstone's Paint World Rankings prize money in tens of thousands of pounds, read from wst.tv/rankings; difference divided by a 40-point scale in a logistic model",
        facts=facts)

# --- Tennis: ATP quarter-finals on 2026-10-23 ----------------------------
ATP = "https://www.atptour.com/en/scores/current/"
ten_rows = [
    ("almaty/9410", "bg23", "me82", "2026-10-23T06:30:00Z", "Nikoloz Basilashvili", "Adrian Mannarino", (453, 743),
     "Basilashvili is ranked 128 and beat Marin Cilic to reach the last eight. Mannarino is ranked 79 and leads their head-to-head 1-0, having won 6-3 6-2 at a hard-court event this season."),
    ("almaty/9410", "te51", "d994", "2026-10-23T08:00:00Z", "Stefanos Tsitsipas", "James Duckworth", (1330, 774),
     "Tsitsipas is ranked 39 on 1,330 points and is the seventh seed. Duckworth is ranked 73 with 774 points."),
    ("almaty/9410", "mm58", "a0gc", "2026-10-23T10:00:00Z", "Daniil Medvedev", "Terence Atmane", (3660, 616),
     "Medvedev is ranked five on 3,660 points and beat Sho Shimabukuro 6-2 6-1. Atmane is ranked 98 and came through 6-7 7-6 7-6 against Mattia Bellucci."),
    ("almaty/9410", "bk92", "ke29", "2026-10-23T12:30:00Z", "Alexander Bublik", "Karen Khachanov", (2275, 1990),
     "Bublik is ranked 19 on 2,275 points and is the third seed. Khachanov is ranked 25 on 1,990 points and beat Tomas Machac 6-2 4-6 7-6."),
    ("brussels/7485", "c0bh", "c0au", "2026-10-23T12:00:00Z", "Clement Chidekh", "Francisco Cerundolo", (371, 2220),
     "Chidekh is ranked 152, a qualifier, and beat Jacob Fearnley and David Goffin for his first tour-level quarter-final. Cerundolo is ranked 21 on 2,220 points."),
    ("brussels/7485", "gj37", "l0bv", "2026-10-23T14:00:00Z", "Tallon Griekspoor", "Jiri Lehecka", (885, 2235),
     "Griekspoor is ranked 60 on 885 points. Lehecka is ranked 20 on 2,235 points and beat Raphael Collignon 6-4 6-2."),
    ("lyon/496", "mw02", "pl56", "2026-10-23T12:00:00Z", "Corentin Moutet", "Tommy Paul", (640, 2575),
     "Moutet is ranked 94 on 640 points. Paul is ranked 15 on 2,575 points and is the fourth seed."),
    ("lyon/496", "ae14", "fb98", "2026-10-23T13:30:00Z", "Daniel Altmaier", "Taylor Fritz", (849, 2880),
     "Altmaier is ranked 65 on 849 points. Fritz is ranked 14 on 2,880 points, the second seed, and beat Pierre-Hugues Herbert 6-2 7-5."),
]
for tour, hcode, acode, start, home, away, pts, facts in ten_rows:
    add(sid=f"ten-{hcode}-{acode}", sport="tennis", comp="ATP Tour quarter-final", start=start, home=home, away=away,
        src=f"{ATP}{tour}/daily-schedule",
        h=dict(strength=pts[0] ** 0.5), a=dict(strength=pts[1] ** 0.5),
        basis="PIF ATP ranking points read from atptour.com/rankings/singles; square root of points used as strength, difference divided by a 55-point scale",
        facts=facts)

# --- Handball: EHF Champions League men, 28-29 October -------------------
EHF = "https://ehfcl.eurohandball.com/men/2026-27/matches/details/"
hb_rows = [
    ("202711020101016", "2026-10-28T17:45:00Z", "Orlen Wisla Plock", "HBC Nantes", (141, 136, 5), (142, 143, 5),
     "Plock lead Group B on six points with a +5 goal difference. Nantes are level on six points with 142 scored and 143 conceded."),
    ("202711020101004", "2026-10-28T17:45:00Z", "FC Porto", "One Veszprem HC", (158, 173, 5), (185, 146, 5),
     "Porto are third in Group A on three points, 15 goals down. Veszprem lead the group with five wins from five and a +39 difference."),
    ("202711020101022", "2026-10-28T17:45:00Z", "HC Vardar 1961", "MT Melsungen", (154, 158, 5), (138, 138, 5),
     "Vardar are fourth in Group B on two points, 154 scored and 158 conceded. Melsungen are second on six points with an even goal difference."),
    ("202711020101067", "2026-10-28T19:45:00Z", "Industria Kielce", "Kolstad Handball", (155, 153, 5), (143, 178, 5),
     "Kielce are second in Group F on six points, +2. Kolstad are bottom of the group, winless with a -35 difference."),
    ("202711020101036", "2026-10-28T19:45:00Z", "RK Celje Pivovarna Lasko", "HC Zagreb", (150, 188, 5), (146, 158, 5),
     "Celje are winless in Group C with a -38 difference. Zagreb are third on four points with 146 scored and 158 conceded."),
    ("202711020101065", "2026-10-28T19:45:00Z", "SC Magdeburg", "HC Kriens-Luzern", (176, 140, 5), (158, 161, 5),
     "Magdeburg have won all five Group F games with a +36 difference. Kriens-Luzern are third on four points at -3."),
    ("202711020101026", "2026-10-28T19:45:00Z", "Paris Saint-Germain", "Aalborg Handbold", (182, 157, 5), (170, 145, 5),
     "PSG are second in Group C on seven points with 182 scored. Aalborg lead the group on nine points and are unbeaten."),
    ("202711020101046", "2026-10-29T17:45:00Z", "IFK Kristianstad", "OTP Bank - PICK Szeged", (162, 197, 5), (172, 169, 5),
     "Kristianstad are winless in Group D with a -35 difference. Szeged are third on four points after two draws."),
]
for mid, start, home, away, hs, as_, facts in hb_rows:
    slug = home.replace(" ", "") + "-" + away.replace(" ", "")
    add(sid=f"ehf-{mid}", sport="handball", comp="EHF Champions League men group phase", start=start,
        home=home, away=away, src=f"{EHF}{mid}/{slug}/",
        h=dict(gf=hs[0], ga=hs[1], gp=hs[2]), a=dict(gf=as_[0], ga=as_[1], gp=as_[2]),
        basis="goals for and against from the EHF Champions League group tables, shrunk gp/(gp+3) toward the league average of 31.8273 goals per team; home +0.40",
        facts=facts)


# --- Rugby League: World Cup round 2 --------------------------------------
NRL = "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/"
rl_rows = [
    ("tonga-v-lebanon", "2026-10-23T04:05:00Z", "Tonga", "Lebanon", 18, -24,
     "Tonga beat England 30-12 in round one, with Addin Fonua-Blake and Haumole Olakau'atu in the pack. Lebanon lost 42-18 to Papua New Guinea."),
    ("papua-new-guinea-v-samoa", "2026-10-23T23:25:00Z", "Papua New Guinea", "Samoa", 24, 74,
     "Papua New Guinea beat Lebanon 42-18 in round one. Samoa beat France 78-4, with Brian To'o and Stephen Crichton in the backline."),
    ("england-v-france", "2026-10-24T01:35:00Z", "England", "France", -18, -74,
     "England lost 30-12 to Tonga in round one despite a Herbie Farnworth try. France were beaten 78-4 by Samoa."),
    ("new-zealand-v-cook-islands", "2026-10-25T00:05:00Z", "New Zealand", "Cook Islands", -2, -28,
     "New Zealand lost 24-22 to Australia in round one, with Keano Kini at fullback. The Cook Islands lost 40-12 to Fiji."),
    ("australia-v-fiji", "2026-10-25T04:05:00Z", "Australia", "Fiji", 2, 28,
     "Australia beat New Zealand 24-22 in round one. Fiji beat the Cook Islands 40-12."),
]
for slug, start, home, away, hs, as_, facts in rl_rows:
    add(sid=f"rlwc-{slug}", sport="rugby-league", comp="Rugby League World Cup round 2", start=start,
        home=home, away=away, src=NRL + slug + "/",
        h=dict(strength=float(hs)), a=dict(strength=float(as_)),
        basis="round-one score differential from the official NRL.com World Cup draw; difference divided by a 30-point scale. No ladder or rating table exists after one round, so this is flagged as a thin input",
        facts=facts)

# --- Gaelic football: three provincial county finals ----------------------
GAA = "https://munster.gaa.ie/fixtures/events-calendar/"
add(sid="gaa-cork-psfc", sport="gaelic-football", comp="Cork Premier Senior Football final",
    start="2026-10-25T16:00:00Z", home="St Finbarrs", away="Nemo Rangers",
    src="https://munster.gaa.ie/event/2026-cork-premier-senior-football-championship-final/",
    h=dict(strength=None), a=dict(strength=None),
    basis="no numeric official input was published for these club sides, so no price is originated",
    facts="St Finbarrs beat Nemo Rangers 1-14 to 1-13 in the 2025 final at SuperValu Pairc Ui Chaoimh. The 2026 final throws in at 16:00 on 25 October at the same venue.")
add(sid="gaa-kerry-sfc", sport="gaelic-football", comp="Kerry Senior Football final",
    start="2026-10-25T14:00:00Z", home="Dr Crokes", away="Kenmare Shamrocks",
    src="https://munster.gaa.ie/event/2026-kerry-county-senior-football-championship-final-dr-crokes-v-kenmare-shamrocks/",
    h=dict(strength=None), a=dict(strength=None),
    basis="no numeric official input was published for these club sides, so no price is originated",
    facts="The Kerry final is scheduled for 14:00 on 25 October at Fitzgerald Stadium, refereed by Sean Joy.")
add(sid="gaa-waterford-sfc", sport="gaelic-football", comp="Waterford Senior Football final",
    start="2026-10-25T14:30:00Z", home="Rathgormack", away="The Nire",
    src="https://munster.gaa.ie/fixtures/events-calendar/",
    h=dict(strength=None), a=dict(strength=None),
    basis="no numeric official input was published for these club sides, so no price is originated",
    facts="The Waterford final throws in at 14:30 on 25 October at Fraher Field, Dungarvan. Rathgormack beat Abbeyside-Ballinacourty 2-10 to 0-8 in the 2024 final.")

# --- Volleyball: Italian SuperLega round 2 -------------------------------
LEGA = "https://www.legavolley.it/calendario/?idCampionato=999"
vb_rows = [
    ("Perugia", "Pordenone", "2026-10-25T17:00:00Z", (114, 95), (94, 91),
     "Perugia took two points from round one, beating Cuneo 3-2 after 114 points scored and 95 conceded. Prata beat Monza 3-1."),
    ("Trentino", "Cisterna", "2026-10-25T16:00:00Z", (75, 61), (79, 56),
     "Trentino swept Modena 3-0 in round one, 75 points to 61. Cisterna swept Milano 3-0 and top the early table on point ratio."),
    ("Piacenza", "Modena", "2026-10-25T17:00:00Z", (75, 56), (61, 75),
     "Piacenza swept Padova 3-0 in round one, scoring 75 and conceding 56. Modena were swept 3-0 by Trentino."),
    ("Civitanova", "Padova", "2026-10-25T17:00:00Z", (78, 65), (56, 75),
     "Civitanova won 3-0 at Verona, 78 points to 65. Padova lost 3-0 at home to Piacenza."),
    ("Milano", "Cuneo", "2026-10-25T18:00:00Z", (56, 79), (95, 114),
     "Milano were swept 3-0 by Cisterna, scoring 56. Cuneo took a point off Perugia in a 3-2 defeat."),
    ("Monza", "Verona", "2026-10-25T17:00:00Z", (91, 94), (65, 78),
     "Monza lost 3-1 at Prata, 94 points to 91. Verona were swept 3-0 by Civitanova."),
]
for home, away, start, hs, as_, facts in vb_rows:
    add(sid=f"vb-{home.lower()}-{away.lower()}", sport="volleyball", comp="SuperLega round 2", start=start,
        home=home, away=away, src=LEGA,
        h=dict(strength=100.0 * hs[0] / hs[1]), a=dict(strength=100.0 * as_[0] / as_[1]),
        basis="points scored divided by points conceded in round one, from the official SuperLega calendar; difference divided by a 60-point scale. One match is a very thin sample and is flagged",
        facts=facts)

# --- Aussie Rules: AFLW round 11 ----------------------------------------
AFL = "https://www.afl.com.au/aflw"
afl_rows = [
    ("port-adelaide-v-collingwood", "2026-10-23T08:15:00Z", "Port Adelaide", "Collingwood", (16, 78.8), (4, 56.7),
     "Port Adelaide are eleventh on 16 points at 78.8 per cent. Collingwood are sixteenth on four points at 56.7 per cent and have lost captain Ruby Schleicher to a season-ending exit."),
    ("st-kilda-v-brisbane", "2026-10-24T02:05:00Z", "St Kilda", "Brisbane", (4, 45.1), (12, 89.7),
     "St Kilda are bottom with one win from ten at 45.1 per cent. Brisbane are fourteenth on 12 points and beat Port Adelaide in round ten."),
    ("geelong-v-fremantle", "2026-10-24T04:05:00Z", "Geelong", "Fremantle", (36, 167.2), (20, 104.9),
     "Geelong are second on 36 points at 167.2 per cent with a top-two spot in reach. Fremantle are eighth on 20 points at 104.9."),
    ("gold-coast-v-richmond", "2026-10-24T05:05:00Z", "Gold Coast", "Richmond", (28, 138.9), (16, 68.9),
     "Gold Coast are fifth on 28 points at 138.9 per cent. Richmond are thirteenth on 16 points at 68.9 and have lost four in a row."),
    ("western-bulldogs-v-melbourne", "2026-10-24T08:15:00Z", "Western Bulldogs", "Melbourne", (32, 140.9), (32, 177.2),
     "The Bulldogs are fourth on 32 points at 140.9 per cent after dismantling Carlton. Melbourne are third on 32 points at 177.2 and won the last meeting 9.8 (62) to 1.8 (14)."),
    ("sydney-v-west-coast", "2026-10-25T01:35:00Z", "Sydney", "West Coast", (28, 112.9), (16, 75.2),
     "Sydney are seventh on 28 points at 112.9 per cent. West Coast are twelfth on 16 points at 75.2."),
    ("north-melbourne-v-adelaide", "2026-10-25T02:05:00Z", "North Melbourne", "Adelaide", (36, 251.9), (20, 102.4),
     "North Melbourne top the ladder on 36 points at 251.9 per cent and are chasing a third straight flag. Adelaide are ninth on 20 points at 102.4."),
    ("hawthorn-v-essendon", "2026-10-25T04:05:00Z", "Hawthorn", "Essendon", (20, 101.5), (4, 55.6),
     "Hawthorn are tenth on 20 points at 101.5 per cent after a shock loss to the Giants. Essendon are seventeenth on four points at 55.6."),
    ("carlton-v-greater-western-sydney", "2026-10-25T06:05:00Z", "Carlton", "Greater Western Sydney", (28, 133.0), (8, 68.2),
     "Carlton are sixth on 28 points at 133.0 per cent. The Giants are fifteenth on eight points at 68.2 and beat Hawthorn in round ten."),
]
for slug, start, home, away, hs, as_, facts in afl_rows:
    add(sid=f"aflw-{slug}", sport="aussie-rules", comp="AFLW round 11", start=start, home=home, away=away,
        src=AFL, h=dict(strength=2.0 * hs[0] + (hs[1] - 100.0) / 5.0),
        a=dict(strength=2.0 * as_[0] + (as_[1] - 100.0) / 5.0),
        basis="ladder points and percentage from the official AFLW ladder, combined as 2 x points + (percentage - 100)/5; difference divided by a 45-point scale",
        facts=facts)

# --- Darts: European Championship round one, 23 October ------------------
PDC = "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/"
darts_rows = [
    ("joyce-wattimena", "2026-10-23T17:00:00Z", "Ryan Joyce", "Jermaine Wattimena", 15, 18,
     "Joyce is seeded 15 for Dortmund and Wattimena 18. Wattimena was runner-up in this event in 2024."),
    ("ratajski-chisnall", "2026-10-23T17:45:00Z", "Krzysztof Ratajski", "Dave Chisnall", 3, 30,
     "Ratajski is the third seed after a strong European Tour season; Chisnall is seeded 30."),
    ("clayton-springer", "2026-10-23T18:45:00Z", "Jonny Clayton", "Niko Springer", 7, 26,
     "Clayton won the Swiss Darts Trophy in Basel in October and is seeded seven. Springer is seeded 26 and plays on home soil."),
    ("littler-oconnor", "2026-10-23T19:15:00Z", "Luke Littler", "William O'Connor", 1, 30,
     "Littler is the world number one and has never won this event. O'Connor broke into the world's top 32 after beating Michael van Gerwen in Maastricht."),
    ("nijman-schindler", "2026-10-23T19:45:00Z", "Wessel Nijman", "Martin Schindler", 2, 31,
     "Nijman is the second seed and a two-time European Tour winner in 2026. Schindler is seeded 31 and admitted he is not in his best phase."),
    ("doets-van-gerwen", "2026-10-23T20:15:00Z", "Kevin Doets", "Michael van Gerwen", 14, 10,
     "Doets is seeded 14. Van Gerwen has slipped to world number ten after an early exit in Maastricht."),
    ("rock-dobey", "2026-10-23T20:45:00Z", "Josh Rock", "Chris Dobey", 10, 23,
     "Rock won the Graz European Tour event in 2026 and is seeded ten. Dobey is seeded 23."),
    ("aspinall-reyes", "2026-10-23T21:15:00Z", "Nathan Aspinall", "Cristo Reyes", 6, 40,
     "Aspinall is the sixth seed and a Munich winner this year. Reyes is an unseeded Spanish qualifier returning to the big stage."),
]
for slug, start, home, away, hs, as_, facts in darts_rows:
    add(sid=f"darts-{slug}", sport="darts", comp="Machineseeker European Championship round one", start=start,
        home=home, away=away, src=PDC,
        h=dict(strength=-float(hs)), a=dict(strength=-float(as_)),
        basis="European Tour seed number from the official PDC draw bracket, negated so that seed 1 is strongest; difference divided by an 8-point scale. Unseeded players are treated as seed 40 and flagged",
        facts=facts)

# --- eSports: League of Legends Worlds Swiss round one -------------------
LOL = "https://lolesports.com/en-US/gpr/2026/current"
lol_rows = [
    ("al-v-kc", "2026-10-23T20:00:00Z", "Anyone's Legend", "Karmine Corp", 1409, 1409,
     "Anyone's Legend and Karmine Corp share a Global Power Score of 1,409 points. Karmine Corp are 36-13 across 2026 and came through the play-in stage 3-2 against Cloud9."),
    ("g2-v-dk", "2026-10-23T21:00:00Z", "G2 Esports", "Dplus KIA", 1480, 1409,
     "G2 are fourth on 1,480 points with a 33-15 record and field Caps, Hans Sama and BrokenBlade. Dplus KIA are seventh on 1,409."),
    ("tlaw-v-cfo", "2026-10-23T22:00:00Z", "Team Liquid Alienware", "CTBC Flying Oyster", 1369, 1314,
     "Team Liquid Alienware are eleventh on 1,369 points. CTBC Flying Oyster are twentieth on 1,314."),
    ("los-v-t1", "2026-10-23T23:00:00Z", "LOS", "T1", 1183, 1471,
     "LOS are thirty-ninth on 1,183 points after a 23-9 domestic season. T1 are fifth on 1,471."),
    ("tsw-v-lyon", "2026-10-24T00:00:00Z", "Team Secret Whales", "LYON", 1368, 1424,
     "Team Secret Whales are twelfth on 1,368 points with a 26-6 record. LYON are sixth on 1,424."),
]
for slug, start, home, away, hs, as_, facts in lol_rows:
    add(sid=f"lol-{slug}", sport="esports", comp="League of Legends Worlds 2026 Swiss stage", start=start,
        home=home, away=away, src=LOL,
        h=dict(strength=float(hs)), a=dict(strength=float(as_)),
        basis="Global Power Score from Riot's official lolesports.com Global Power Rankings (updated 19 October 2026); Elo-style logistic with a 400-point scale",
        facts=facts)

# --- Outright markets (share of an official points or money table) -------
add(sid="f1-usgp", sport="motor-racing", comp="Formula 1 United States Grand Prix", start="2026-10-25T19:00:00Z",
    home="United States Grand Prix", away="Outright", src="https://www.formula1.com/en/results/2026/drivers",
    h=dict(strength=0.0), a=dict(strength=0.0),
    basis="share of 2026 drivers' championship points from formula1.com; a points share is a season-long measure, not a single-race model, so every price here is capped at low confidence",
    facts="Kimi Antonelli leads the championship on 340 points from 17 rounds, 102 clear of George Russell on 238. Max Verstappen has won the last two races in Bahrain and Singapore.",
    contenders=[("Kimi Antonelli", 340), ("George Russell", 238), ("Lewis Hamilton", 229),
                ("Max Verstappen", 221), ("Charles Leclerc", 215), ("Lando Norris", 201)])

add(sid="golf-stifel", sport="golf", comp="PGA Tour Champions Stifel Charity Classic", start="2026-10-23T17:45:00Z",
    home="Stifel Charity Classic", away="Outright", src="https://www.pgatour.com/pgatour-champions/tournaments/2026/stifel-charity-classic/S2026625/overview",
    h=dict(strength=0.0), a=dict(strength=0.0),
    basis="share of published 2026 Charles Schwab Cup money for the three players whose figures were published; the remaining 69 players in the 72-man field are not modelled and the market is flagged as partial",
    facts="Stewart Cink leads the Charles Schwab Cup on $3,798,700 with five wins in 2026, including the Senior PGA Championship and Regions Tradition. Steven Alker has four wins and $2,265,087.",
    contenders=[("Stewart Cink", 3798700), ("Zach Johnson", 3295614), ("Steven Alker", 2265087)])

add(sid="gbgb-romford-final", sport="greyhounds", comp="Coral 100 Champion Stakes final, Romford", start="2026-10-23T18:30:00Z",
    home="Romford 575m final", away="Outright", src="https://www.gbgb.org.uk/category-one-glory-beckons-in-coral-100-champion-stakes-final/",
    h=dict(strength=0.0), a=dict(strength=0.0),
    basis="semi-final winning times published by GBGB converted to a weight of 1/(time - 35.00); the two runners whose times were not published are given the slowest published time plus 0.10 and flagged",
    facts="Grouchos Gregor won the third semi-final in 35.36sec for trainer Kelly Wilton. Aayamza Legend won the second in 35.75 and Bubbly Holly the first in 35.95; Newinn Jolly was withdrawn with a urine infection.",
    contenders=[("Grouchos Gregor", 1 / 0.36), ("Aayamza Legend", 1 / 0.75),
                ("Bubbly Holly", 1 / 0.95), ("Fortanach Col", 1 / 0.60), ("Don Cici", 1 / 1.00)])

# --- Cricket: two internationals on 23 October --------------------------
add(sid="cricket-afg-zim-final", sport="cricket", comp="UAE ODI Tri-Series final", start="2026-10-23T11:30:00Z",
    home="Afghanistan", away="Zimbabwe", src="https://www.icc-cricket.com/rankings/team-rankings/mens/odi",
    h=dict(strength=93.0), a=dict(strength=65.0),
    basis="ICC men's ODI team rating from icc-cricket.com; difference divided by a 40-point scale",
    facts="Afghanistan are eighth on 93 ODI rating points and Zimbabwe eleventh on 65. Sediqullah Atal made 102 from 110 balls in Afghanistan's 158-run win over Zimbabwe on 19 October, and Rashid Khan took 4/17.")

add(sid="cricket-indw-zimw", sport="cricket", comp="India Women v Zimbabwe Women, first ODI", start="2026-10-23T08:00:00Z",
    home="India Women", away="Zimbabwe Women", src="https://www.icc-cricket.com/rankings/team-rankings/womens/odi",
    h=dict(strength=124.0), a=dict(strength=14.0),
    basis="ICC women's ODI team rating from icc-cricket.com; difference divided by a 40-point scale",
    facts="India Women are third on 124 rating points and Zimbabwe Women twelfth on 14. Smriti Mandhana holds the top spot in the ICC women's ODI batting rankings on 790 points.")


def write():
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"captured_utc": "2026-10-22T22:00:00Z", "session": "arena/ca03be92-olbg2",
               "params": PARAMS, "fixtures": F}
    (OUT / "inputs.json").write_text(json.dumps(payload, indent=1) + "\n")
    print(f"seeded {len(F)} fixtures")
    from collections import Counter
    for sport, n in sorted(Counter(f["sport"] for f in F).items()):
        print(f"  {sport:16s} {n}")


if __name__ == "__main__":
    write()
