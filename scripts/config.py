"""Scope configuration for the OLBG reverse-engineering project.

The user's brief excludes: soccer, boxing, UFC/MMA, football, american football,
hurling, horse racing, cycling and "specials".
"""

# OLBG numeric sport ids (extracted from https://www.olbg.com/sitemap-betting-tips.xml)
OLBG_SPORTS = {
    1: "Football",            # soccer - EXCLUDED
    2: "Horse Racing",        # EXCLUDED
    3: "Tennis",
    4: "Basketball",
    5: "Golf",
    7: "Cricket",
    8: "Snooker",
    9: "Rugby Union",
    10: "Rugby League",
    11: "American Football",  # EXCLUDED
    12: "Baseball",
    13: "Ice Hockey",
    14: "Motor Racing",
    15: "Darts",
    16: "Boxing",             # EXCLUDED (UFC/MMA are filed under this id on OLBG)
    17: "Cycling",            # EXCLUDED
    20: "Handball",
    21: "Volleyball",
    22: "Aussie Rules",
    23: "eSports",
    25: "Gaelic Football",
    26: "Hurling",            # EXCLUDED
    28: "Greyhounds",
}

INCLUDED_SPORTS = {
    "Tennis", "Basketball", "Golf", "Cricket", "Snooker", "Rugby Union",
    "Rugby League", "Baseball", "Ice Hockey", "Motor Racing", "Darts",
    "Handball", "Volleyball", "Aussie Rules", "eSports", "Gaelic Football",
    "Greyhounds",
}

EXCLUDED_SPORTS = {
    "Football", "American Football", "Boxing", "Cycling", "Horse Racing",
    "Hurling", "Specials",
}

assert not (INCLUDED_SPORTS & EXCLUDED_SPORTS)
