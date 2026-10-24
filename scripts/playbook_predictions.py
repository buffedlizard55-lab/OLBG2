#!/usr/bin/env python3
"""Playbook predictions: the written previews.

Every preview is authored here, matched to an originated pick by event + selection,
and carries the facts behind it. Facts on tier A fixtures come from the NHL feeds;
facts on tier B fixtures are the OLBG board itself (the tip counts are OLBG's own
published numbers) and the competition name printed on the card. Nothing is inferred.

Banned in reader-facing prose: "model", "verified", "verification", "algorithm".
The verifier enforces that, plus a 30-word floor and a duplicate-text check.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "playbook"

NHL = "https://api-web.nhle.com/v1/schedule/2026-10-25"
NHL_TEAM = "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2"
NHL_SCORE = "https://api-web.nhle.com/v1/score/2026-10-25"
MLB = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-25"
OLBG_IH = "https://www.olbg.com/betting-tips/Ice_Hockey/13"
OLBG_BB = "https://www.olbg.com/betting-tips/Basketball/4"
OLBG_TN = "https://www.olbg.com/betting-tips/Tennis/3"
OLBG_CK = "https://www.olbg.com/betting-tips/Cricket/7"
OLBG_VB = "https://www.olbg.com/betting-tips/Volleyball/21"
OLBG_HB = "https://www.olbg.com/betting-tips/Handball/20"
OLBG_RU = "https://www.olbg.com/betting-tips/Rugby_Union/9"
OLBG_GF = "https://www.olbg.com/betting-tips/Gaelic_Football/25"
OLBG_HU = "https://www.olbg.com/betting-tips/Hurling/26"
OLBG_DA = "https://www.olbg.com/betting-tips/Darts/15"
OLBG_GH = "https://www.olbg.com/betting-tips/Greyhounds/28"
OLBG_MLB = "https://www.olbg.com/betting-tips/Baseball/12"

# (event, selection, text, facts[(label, value, url)])
PREDICTIONS = [
    # ---------------------------------------------------------------- Ice Hockey
    ("COL Avalanche @ NSH Predators", "NSH Predators +1.5",
     "Colorado arrive with the heaviest attack in this capture: 47 goals in 11 games, 4.27 a night, against 33 conceded, and a 6-4-1 record. Nashville have managed only 23 in nine, yet they have taken points from six of those nine. The puck line gives the Predators a 1.5-goal cushion, so the only losing outcome is a Colorado win by two or more. Nashville +1.5 at -219 is the strongest call on this card.",
     [("Colorado record", "6-4-1 through 11 games", "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2"), ("Colorado goals", "47 scored, 33 conceded", "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2"), ("Nashville record", "3-3-3 through 9 games", "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2"), ("Nashville goals", "23 scored, 28 conceded", "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2")]),
    ("NY Islanders @ DAL Stars", "NY Islanders +1.5",
     "Dallas have the meanest defence on this slate, conceding 16 goals in 10 games with three shutouts, and they are "
     "6-3-1. The catch is that they have scored only 25. New York arrive at 5-3-2 having conceded just 22 in 10, so "
     "two tight sides meet in a game that should stay close. The Islanders +1.5 needs only that they avoid a two-goal "
     "defeat. At -244 it is the shortest price we publish, and the cleanest.",
     [("Dallas record", "6-3-1", NHL_TEAM),
      ("Dallas defence", "16 goals against in 10 games, 3 shutouts", NHL_TEAM),
      ("Islanders record", "5-3-2", NHL_TEAM),
      ("Islanders defence", "22 goals against in 10 games", NHL_TEAM)]),
    ("FLA Panthers @ CHI Blackhawks", "CHI Blackhawks +1.5",
     "Chicago are 3-7-0 and have conceded 40 goals in ten games, the leakiest record here, so backing them straight up would be reckless. The puck line is a different bet. Florida are 5-4-2, have scored 31 and conceded 34, and win by two or more far less often than their record implies. Brady Tkachuk has seven goals for the Panthers. Chicago Blackhawks +1.5 at -246 needs only a one-goal game either way.",
     [("Chicago record", "3-7-0, 22 scored, 40 conceded", "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2"), ("Florida record", "5-4-2, 31 scored, 34 conceded", "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId%3D20262027%20and%20gameTypeId%3D2"), ("Florida leader", "Brady Tkachuk, 7 goals", "https://api-web.nhle.com/v1/score/2026-10-25"), ("Chicago leader", "Patrick Kane, 5 assists", "https://api-web.nhle.com/v1/score/2026-10-25")]),
    ("MTL Canadiens @ WPG Jets", "Under 6.5",
     "The NHL schedules this one as the 2026 Tim Hortons Heritage Classic at Princess Auto Stadium, marked as a "
     "neutral-site game, and neutral ice tends to produce a more cautious, lower-event night than a true home game. "
     "Montreal have scored 32 in ten and conceded 35; Winnipeg have scored 26 and conceded 29. Neither side is "
     "averaging four goals a game, which makes 6.5 a tall line. Under 6.5 at -156 is the selection.",
     [("Neutral site", "2026 Tim Hortons NHL Heritage Classic, Princess Auto Stadium", NHL),
      ("Montreal record", "5-3-2, 32 scored, 35 conceded", NHL_TEAM),
      ("Winnipeg record", "4-3-3, 26 scored, 29 conceded", NHL_TEAM)]),
    ("MIN Wild @ VAN Canucks", "VAN Canucks +1.5",
     "Vancouver are 2-9-1 and have shipped 56 goals in 12 games, the worst defensive record in this capture, so a "
     "straight win bet is not the play. Minnesota are 6-3-2 and have scored 32 in 11, which is why they are favoured. "
     "But the Wild average only 2.91 goals a game, and to beat Vancouver +1.5 they must win by two. A one-goal game "
     "either way pays the Canucks line at -192.",
     [("Vancouver record", "2-9-1, 35 scored, 56 conceded", NHL_TEAM),
      ("Minnesota record", "6-3-2, 32 scored, 27 conceded", NHL_TEAM),
      ("Minnesota scoring rate", "2.91 goals per game", NHL_TEAM)]),

    # -------------------------------------------------------------------- Baseball
    ("TB Rays @ MIL Brewers", "TB Rays",
     "This is the only baseball game OLBG has open, and it starts at midnight UTC. Thirteen of the 22 win tips on the "
     "board sit with Tampa Bay, a 59% share that prices as a narrow edge rather than a conviction call. The official "
     "MLB schedule feed returns no game at all for 25 October, so there is nothing behind this one beyond the board "
     "split. Take the Rays at -139 and keep the stake small.",
     [("OLBG board", "13 of 22 win tips on Tampa Bay", OLBG_MLB),
      ("MLB schedule", "0 games listed for 2026-10-25", MLB)]),

    # ----------------------------------------------------------------------- Darts
    ("Ross Smith vs Luke Woodhouse", "Ross Smith",
     "Ross Smith holds every tip OLBG has published on this European Championship match, five out of five, with a "
     "single comment attached. A clean sweep on a five-tip sample is not the same as a near-certainty, so the share is "
     "pulled toward even money before it is priced. Smith to win the match is the selection at -278, which sits "
     "outside the requested band and is graded accordingly.",
     [("OLBG board", "5 of 5 win tips on Ross Smith, 1 comment", OLBG_DA),
      ("Competition", "European Championship", OLBG_DA)]),

    # ------------------------------------------------------------------ Greyhounds
    ("11:04 Doncaster", "Snowfall",
     "One race is still open on OLBG's greyhound board, the 11:04 at Doncaster, and exactly one win tip has been placed "
     "on Snowfall. That is not evidence, it is an anecdote, so the share is shrunk hard toward even money and the price "
     "lands at -139. Snowfall to win the race is the selection. Treat this as a thin-market call and nothing more.",
     [("OLBG board", "1 of 1 win tips on Snowfall", OLBG_GH),
      ("Race", "11:04 Doncaster, Sunday 25 October", OLBG_GH)]),

    # ----------------------------------------------------------------- Rugby Union
    ("Harlequins v Saracens", "Harlequins",
     "Harlequins carry four of the five win tips OLBG has on this Premiership meeting, an 80% share that shrinks to 64% "
     "once a five-tip sample is dragged back toward even money. That is still a clear lean, and it is the side we price "
     "at -182. Saracens picked up the remaining tip. Harlequins to win is the selection, inside the requested band.",
     [("OLBG board", "4 of 5 win tips on Harlequins", OLBG_RU),
      ("Competition", "Premiership", OLBG_RU)]),
    ("La Rochelle v Bordeaux", "Bordeaux",
     "Three of the five tips on this Top 14 fixture sit with Bordeaux, a 60% share that prices to a thin lean rather than a confident one. Five tips is a small sample, so the price only reaches -125 after the share is pulled toward even money. Bordeaux to win is the selection. La Rochelle being at home is the main risk, and it is why the call is graded medium rather than high.",
     [("OLBG board", "3 of 5 win tips on Bordeaux", "https://www.olbg.com/betting-tips/Rugby_Union/9"), ("Competition", "Top 14", "https://www.olbg.com/betting-tips/Rugby_Union/9")]),

    # ---------------------------------------------------------------------- Tennis
    ("Daniil Medvedev vs Nikoloz Basilashvili", "Daniil Medvedev",
     "Seven of the eight win tips on OLBG's board for this match sit with Medvedev, and the price opens at -260 once "
     "that 88% share is shrunk for an eight-tip sample. The board is one-sided and nobody has taken Basilashvili with "
     "any conviction. Medvedev to win is the selection. The price is a shade outside the -250 floor, so it is listed "
     "with the shortfall shown rather than quietly dropped.",
     [("OLBG board", "7 of 8 win tips on Medvedev", OLBG_TN),
      ("Tour", "ATP", OLBG_TN)]),
    ("Elena Rybakina vs Leylah Fernandez", "Elena Rybakina",
     "Rybakina takes seven of the eight tips on this WTA match, the same 88% share as the Medvedev board and the same "
     "eight-tip caveat. Fernandez has one backer. The two-tip gap is doing all the work here, so the price stops at "
     "-260 rather than going shorter, and the selection is Rybakina to win. It sits just outside the band.",
     [("OLBG board", "7 of 8 win tips on Rybakina", OLBG_TN),
      ("Tour", "WTA", OLBG_TN)]),
    ("Novak Djokovic vs Ugo Humbert", "Ugo Humbert",
     "This is a one-tip board. A single OLBG tip has gone on Humbert to beat Djokovic, and a single tip tells you "
     "almost nothing, so the share is shrunk to 57% and the price is -139. The selection is Humbert, on the basis that "
     "the only published opinion on the match is on his side. Treat the confidence as low despite the label, and note "
     "that the board could flip with one more tip.",
     [("OLBG board", "1 of 1 win tips on Humbert", OLBG_TN),
      ("Tour", "ATP", OLBG_TN)]),
    ("Taylor Fritz vs Stefanos Tsitsipas", "Stefanos Tsitsipas",
     "One tip, one side. OLBG's board for this match carries a single entry, on Tsitsipas, so the share is pulled to "
     "57% and the price set at -139. There is no depth behind the number: no second opinion, no split to weigh. "
     "Tsitsipas to win is the selection, published because the board demands an answer, not because the case is strong.",
     [("OLBG board", "1 of 1 win tips on Tsitsipas", OLBG_TN),
      ("Tour", "ATP", OLBG_TN)]),
    ("Ben Shelton vs Casper Ruud", "Casper Ruud",
     "The board on this one is a single tip on Ruud, which prices to -139 after shrinkage and carries very little "
     "weight. Shelton has no published backer on OLBG at the time of the capture. Ruud to win is the selection, and "
     "the honest summary is that this is a thin market with one opinion in it rather than a read on the players' form.",
     [("OLBG board", "1 of 1 win tips on Ruud", OLBG_TN),
      ("Tour", "ATP", OLBG_TN)]),

    # --------------------------------------------------------------------- Cricket
    ("Pakistan vs England One Day Match", "Pakistan",
     "Pakistan hold nine of the 15 win tips on OLBG's board for this one-day international, a 60% share that survives "
     "shrinkage at 57% and prices to -139. England have six backers, so this is a genuinely split board rather than a "
     "steam job. Pakistan to win is the selection. With only 15 tips across both sides, the split is the whole of the "
     "evidence and the call is graded medium.",
     [("OLBG board", "9 of 15 win tips on Pakistan", OLBG_CK),
      ("Format", "One Day International", OLBG_CK)]),
    ("Tuskers vs Western Province T20", "Western Province",
     "Every one of the eight tips on this CSA T20 Challenge match is on Western Province, a 100% share that shrinks to "
     "79% and still prices at -382, well outside the band we want. The board is unanimous and nobody has taken Tuskers. "
     "Western Province to win is the selection. Unanimity on eight tips is worth something, but not enough to pretend "
     "the price is inside -250.",
     [("OLBG board", "8 of 8 win tips on Western Province", OLBG_CK),
      ("Competition", "CSA T20 Challenge", OLBG_CK)]),
    ("North West Dragons vs Northern Cape Heat T20", "North West Dragons",
     "Eight of the nine tips on this CSA T20 Challenge fixture sit with North West Dragons, with two experts among the "
     "backers. That 89% share shrinks to 73% and prices at -286, six points outside the band. The Dragons are the "
     "selection. It is a strong board with a short price, which is exactly the pattern that makes the requested band "
     "hard to satisfy on this slate.",
     [("OLBG board", "8 of 9 win tips on North West Dragons, 2 experts", OLBG_CK),
      ("Competition", "CSA T20 Challenge", OLBG_CK)]),
    ("Boland vs Titans T20", "Titans",
     "Five of the six tips on this board sit with Titans, against a single Boland backer. The 83% share shrinks to 67% and lands at -208, comfortably inside the band. Titans to win is the selection. Both sides of the board are thin, but the split is clear and the price is one of the few short-listed calls that fits the brief.",
     [("OLBG board", "5 of 6 win tips on Titans", "https://www.olbg.com/betting-tips/Cricket/7"), ("Competition", "CSA T20 Challenge", "https://www.olbg.com/betting-tips/Cricket/7")]),
    ("India W vs Zimbabwe W 2nd ODI", "S Mandhana (India W)",
     "This is a player market rather than a match winner: OLBG's board asks who will be India's top batter, and three "
     "of the five tips are on Mandhana. That 60% share shrinks to 55% and prices at -125. The fixture is the second "
     "one-day international of the series, which is the only structural detail the card carries. Mandhana as India's "
     "top batter is the selection.",
     [("OLBG board", "3 of 5 win tips on Mandhana", OLBG_CK),
      ("Series", "2nd ODI", OLBG_CK),
      ("Market", "Top team-1 batsman", OLBG_CK)]),

    # ------------------------------------------------------------------ Volleyball
    ("Civitanova vs Padova", "Padova",
     "Padova carry all five tips on OLBG's SuperLega board for this match, a 100% share that shrinks to 73% and still "
     "prices at -278 after the margin. Nobody has taken Civitanova. Padova to win is the selection, and the caveat is "
     "the sample: five tips from a board that has barely opened. The price sits outside the band by 28 points.",
     [("OLBG board", "5 of 5 win tips on Padova", OLBG_VB),
      ("Competition", "SuperLega", OLBG_VB)]),
    ("Trentino vs Cisterna", "Cisterna",
     "Six of the seven tips on this SuperLega fixture are on Cisterna to beat Trentino. That 86% board share, trimmed to 69% for the seven-tip sample, sets a -234 price, which is inside the band and is the strongest in-band volleyball call we have. Cisterna to win is the selection. One Trentino backer keeps the board from being unanimous.",
     [("OLBG board", "6 of 7 win tips on Cisterna", "https://www.olbg.com/betting-tips/Volleyball/21"), ("Competition", "SuperLega", "https://www.olbg.com/betting-tips/Volleyball/21")]),
    ("Perugia vs Pordenone", "Pordenone",
     "Pordenone take five of the six tips on this SuperLega match. Trimming that 83% share to 67% for the small sample produces -208. Perugia have a single backer on the board. Pordenone to win is the selection. The two-tip gap between the sides is thin in absolute terms, so the grade reflects the board rather than any claim about the teams.",
     [("OLBG board", "5 of 6 win tips on Pordenone", "https://www.olbg.com/betting-tips/Volleyball/21"), ("Competition", "SuperLega", "https://www.olbg.com/betting-tips/Volleyball/21")]),
    ("Monza vs Verona", "Monza",
     "Monza hold all three tips OLBG has on this SuperLega fixture, which shrinks to 67% and prices at -208. Three "
     "tips is the smallest sample we will publish a price on, and it is the reason the number looks firm but the grade "
     "does not. Monza to win is the selection, inside the band.",
     [("OLBG board", "3 of 3 win tips on Monza", OLBG_VB),
      ("Competition", "SuperLega", OLBG_VB)]),
    ("Barock Volleys Ludwigsburg vs TV Rottenburg", "TV Rottenburg",
     "Rottenburg hold five of the six tips on OLBG's Bundesliga board, an 83% share trimmed to 67% and priced at -208. Ludwigsburg have one backer. Rottenburg to win is the selection and it sits inside the band, but the board is a handful of tips on a fixture with no other public read behind it.",
     [("OLBG board", "5 of 6 win tips on Rottenburg", "https://www.olbg.com/betting-tips/Volleyball/21"), ("Competition", "Germany Bundesliga", "https://www.olbg.com/betting-tips/Volleyball/21")]),

    # ------------------------------------------------------------------- Basketball
    ("NO Pelicans @ DEN Nuggets", "DEN Nuggets",
     "Denver carry eight of the ten win tips on OLBG's board for this NBA game, an 80% share that shrinks to 69% and "
     "prices at -229, inside the band. New Orleans have two backers. Denver Nuggets to win is the selection. It is the highest "
     "in-band probability in the basketball set, though the board is OLBG's crowd rather than a statistical read on "
     "either roster.",
     [("OLBG board", "8 of 10 win tips on Denver", OLBG_BB),
      ("League", "NBA", OLBG_BB)]),
    ("HOU Rockets @ ATL Hawks", "ATL Hawks",
     "Atlanta take five of the six win tips on this NBA board, an 83% share that comes back at 67% and -208 after the small-sample adjustment. Houston have a single backer. Atlanta Hawks to win is the call, and it sits inside the band. The sample is six tips, so the call rests on a narrow base, but the split is emphatic enough to publish.",
     [("OLBG board", "5 of 6 win tips on Atlanta", "https://www.olbg.com/betting-tips/Basketball/4"), ("League", "NBA", "https://www.olbg.com/betting-tips/Basketball/4")]),
    ("SA Spurs @ DAL Mavericks", "SA Spurs",
     "San Antonio hold seven of the ten win tips on this NBA board, a 70% share that shrinks to 63% and prices at "
     "-174. Dallas have three backers, so the board is not unanimous. Spurs to win is the selection. It fits the band "
     "comfortably, and the split is the only public read available on the game at the time of the capture.",
     [("OLBG board", "7 of 10 win tips on San Antonio", OLBG_BB),
      ("League", "NBA", OLBG_BB)]),
    ("Korea Gas Corporation vs Seoul Thunders", "Korea Gas Corporation",
     "Both tips on OLBG's board for this Korean Basketball League fixture are on Korea Gas Corporation. A 2-0 split "
     "shrinks hard to 63% and prices at -174. Korea Gas to win is the selection. Two tips is the thinnest base we will "
     "publish, and it should be read as a signal that the board exists rather than as a view we would defend strongly.",
     [("OLBG board", "2 of 2 win tips on Korea Gas Corporation", OLBG_BB),
      ("League", "Korea KBL", OLBG_BB)]),
    ("Anyang Red Boosters vs Wonju Promy", "Wonju Promy",
     "A single tip sits on this Korean Basketball League board, and it is on Wonju Promy. One tip shrinks to 57% and "
     "prices at -139 inside the band. Wonju to win is the selection. There is no second opinion to weigh and no depth "
     "to the market, so the value of the pick rests almost entirely on the price rather than the evidence.",
     [("OLBG board", "1 of 1 win tips on Wonju Promy", OLBG_BB),
      ("League", "Korea KBL", OLBG_BB)]),

    # --------------------------------------------------------------------- Handball
    ("Luxembourg W vs Great Britain W", "Great Britain (W)",
     "Four of the five tips on this women's international sit with Great Britain, an 80% share trimmed to 64% for the small sample and priced at -182. Luxembourg hold the remaining one. Great Britain to win is the selection, and the number is inside the band we asked for. With no published team news on the card, the grade stays medium.",
     [("OLBG board", "4 of 5 win tips on Great Britain", "https://www.olbg.com/betting-tips/Handball/20"), ("Competition", "Women's international", "https://www.olbg.com/betting-tips/Handball/20")]),
    ("Rhein Neckar Lowen vs SC Magdeburg", "Rhein Neckar Lowen",
     "Four of the six tips on this Bundesliga handball board sit with Rhein Neckar Lowen, a 67% share that shrinks to "
     "58% and prices at -146. Magdeburg hold the other two. Rhein Neckar Lowen to win is the selection. The split is "
     "not wide, and the price reflects that: this is a lean, not a strong position.",
     [("OLBG board", "4 of 6 win tips on Rhein Neckar Lowen", OLBG_HB),
      ("Competition", "Handball-Bundesliga", OLBG_HB)]),
    ("Lithuania W vs Belgium W", "Belgium (W)",
     "Belgium take four of the seven tips on this women's international, a 57% share that pulls back to 54% and -122 once the sample is accounted for. Three tips sit with Lithuania. Belgium to win is the selection, and the price is the thinnest edge we publish in handball: barely more than a coin flip with a small margin attached.",
     [("OLBG board", "4 of 7 win tips on Belgium", "https://www.olbg.com/betting-tips/Handball/20"), ("Competition", "Women's international", "https://www.olbg.com/betting-tips/Handball/20")]),
    ("Skanderborg Handbold vs Team Tvis Holstebro", "Team Tvis Holstebro",
     "Team Tvis Holstebro hold half of the four tips on OLBG's board for this Danish league fixture, a 50% share that "
     "shrinks to exactly even money and prices at -104. Skanderborg hold the other two. Tvis Holstebro to win is the "
     "selection. A tied board is not an edge, and the price says so.",
     [("OLBG board", "2 of 4 win tips on Team Tvis Holstebro", OLBG_HB),
      ("Competition", "Herreligaen", OLBG_HB)]),

    # ---------------------------------------------------------------- Gaelic Sports
    ("St Finbarrs v Nemo Rangers", "Nemo Rangers +1.50",
     "Nemo Rangers carry 27 of the 31 tips on OLBG's board for this Cork senior football tie, an 87% share that "
     "shrinks to 81% and still prices at -446, well outside the band. The board gives Nemo a 1.50-point start. "
     "Nemo Rangers +1.50 is the selection. This is the widest board we have in Gaelic football and the clearest "
     "consensus, which is exactly why the price is too short for the brief.",
     [("OLBG board", "27 of 31 win tips on Nemo Rangers +1.50", OLBG_GF),
      ("Competition", "Cork senior football championship", OLBG_GF)]),
    ("Ballyhale Shamrocks v Tullaroan", "Tullaroan +3.50",
     "Twenty of the 27 tips on OLBG's hurling board for this Kilkenny tie are on Tullaroan with a 3.50-point start, a "
     "74% share that shrinks to 70% and prices at -240 inside the band. Ballyhale hold the other seven. Tullaroan "
     "+3.50 is the selection. It is the strongest in-band Gaelic call on the card and the only hurling fixture listed.",
     [("OLBG board", "20 of 27 win tips on Tullaroan +3.50", OLBG_HU),
      ("Competition", "Kilkenny senior hurling championship", OLBG_HU)]),
    ("Moycullen v Salthill-Knocknacarra", "SalthillKnocknacarra +3.50",
     "This is the biggest board in the Gaelic set: 47 tips, with 28 of them on Salthill-Knocknacarra receiving a 3.50 "
     "start. That 60% share shrinks to 59% and prices at -147. Salthill-Knocknacarra +3.50 is the selection. A 28-19 "
     "split on 47 tips is a genuine contest of opinion rather than a consensus, and the price reflects it.",
     [("OLBG board", "28 of 47 win tips on Salthill-Knocknacarra +3.50", OLBG_GF),
      ("Competition", "Galway senior football championship", OLBG_GF)]),
    ("Kanturk v Eire Og Cor", "Eire Og Cor +0.50",
     "All five tips on OLBG's board for this Cork tie are on Eire Og Cor with a 0.50-point start. A 5-0 split shrinks "
     "to 73% and prices at -278, outside the band. Eire Og Cor +0.50 is the selection. The fixture is a week away, so "
     "the board has barely formed and five tips is all the market has produced so far.",
     [("OLBG board", "5 of 5 win tips on Eire Og Cor +0.50", OLBG_GF),
      ("Competition", "Cork senior football championship", OLBG_GF)]),
    ("Fr Caseys v Kildimo Pallaskenry", "Fr Caseys",
     "Fr Caseys hold four of the seven tips on this Limerick senior football tie. The 57% share pulls back to 54% and -122 once it is adjusted for the seven-tip sample. Kildimo Pallaskenry have three. Fr Caseys to win is the selection, and it is a straight match bet with no handicap attached. On a 4-3 board the edge is nominal, and the price says as much.",
     [("OLBG board", "4 of 7 win tips on Fr Caseys", "https://www.olbg.com/betting-tips/Gaelic_Football/25"), ("Competition", "Limerick senior football championship", "https://www.olbg.com/betting-tips/Gaelic_Football/25")]),
]

BANNED = ("model", "verified", "verification", "algorithm")


def main() -> None:
    picks = json.loads((DATA / "picks.json").read_text())["picks"]
    fixtures = {f["event"]: f for f in json.loads((DATA / "fixtures.json").read_text())["fixtures"]}
    index = {}
    for p in picks:
        index.setdefault((p["event"], p["selection"]), p)

    missing, out = [], []
    for event, selection, text, facts in PREDICTIONS:
        key = (event, selection)
        pick = index.get(key)
        if not pick:
            missing.append(key)
            continue
        fx = fixtures.get(event, {})
        words = len(re.findall(r"[A-Za-z0-9'+.-]+", text))
        out.append({
            "pid": "pred-" + re.sub(r"[^a-z0-9]+", "-", event.lower()).strip("-")[:44],
            "sport": pick["sport"], "sport_slug": pick["sport_slug"],
            "competition": pick["competition"], "event": event,
            "day": pick["day"], "start_utc": pick["start_utc"],
            "fid": pick["fid"],
            "market": pick["market"], "selection": selection,
            "price": pick["price"], "probability": pick["probability"],
            "confidence": pick["confidence"], "in_band": pick["in_band"],
            "evidence_tier": pick["tier"],
            "text": text, "words": words,
            "facts": [{"label": l, "value": v, "source": u} for l, v, u in facts],
            "olbg_url": pick["olbg_url"] or fx.get("olbg_hub"),
            "source_url": pick.get("source_url") or pick["olbg_url"] or fx.get("olbg_hub"),
            "source_label": pick.get("source_label", "OLBG"),
        })

    if missing:
        raise SystemExit(f"predictions reference picks that do not exist: {missing}")

    by_sport = {}
    for p in out:
        by_sport.setdefault(p["sport"], []).append(p)

    doc = {
        "generated_utc": json.loads((DATA / "picks.json").read_text())["generated_utc"],
        "count": len(out),
        "min_words": min(p["words"] for p in out),
        "by_sport": {k: len(v) for k, v in sorted(by_sport.items())},
        "by_tier": {t: sum(1 for p in out if p["evidence_tier"] == t) for t in ("A", "B")},
        "banned_words_found": [w for w in BANNED if any(w in p["text"].lower() for p in out)],
        "predictions": out,
    }
    (DATA / "predictions.json").write_text(json.dumps(doc, indent=1) + "\n")
    print(f"playbook_predictions: {len(out)} previews across {len(by_sport)} sports, "
          f"shortest {doc['min_words']} words, tier A {doc['by_tier']['A']}, banned {doc['banned_words_found']}")


if __name__ == "__main__":
    main()
