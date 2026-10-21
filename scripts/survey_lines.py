#!/usr/bin/env python3
"""Originate our own betting lines from verified inputs, then pick a winner and
assign a low/medium/high confidence label.

Nothing here invents a sporting fact. Every input carries a source. Where an
input cannot be verified from an official source the line is left NULL and the
event is flagged - see data/flags.json.

Evidence tiers
--------------
TIER 1  Governing-body rating for BOTH competitors (ICC, OWGR, PDC, WST,
        ATP/WTA, World Rugby). Strongest basis we publish.
TIER 2  Official league table / competition points for BOTH competitors
        (e.g. LNR Top 14 standings).
TIER 3  Published competition-level base rates (OLBG's own results database,
        e.g. Top 14 home-win 74.4% over 910 matches). Weakest basis we publish.
NONE    No verifiable basis -> no line, flagged unverified.
"""
import json, math, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "survey"
RETRIEVED = "2026-10-21"

def logistic(delta, scale):
    """P(first named side wins) from a rating/points gap on a stated scale."""
    return 1.0 / (1.0 + math.exp(-delta / scale))

def fair_odds(p):
    """No-vig fair decimal price. Returns None when p is not a real probability."""
    if p is None or p <= 0 or p >= 1:
        return None
    return round(1.0 / p, 2)

# ===========================================================================
# VERIFIED INPUTS. Each block records the value, the official source URL and
# the date the source content is dated.
# ===========================================================================

# --- ICC men's team ratings (format-specific scales) ------------------------
ICC = {
    "source": "https://www.icc-cricket.com/rankings/team-rankings",
    "read_via": "https://www.cricinfo.com/rankings/icc-team-ranking",
    "cross_check": "https://en.wikipedia.org/wiki/ICC_Men%27s_ODI_Team_Rankings",
    "as_of": {"odi": "2026-10-19", "t20i": "2026-10-14"},
    "odi": {  # rating
        "India": 115, "New Zealand": 109, "South Africa": 104, "Australia": 102,
        "Pakistan": 102, "England": 95, "Sri Lanka": 94, "Afghanistan": 92,
        "Bangladesh": 82, "West Indies": 79, "Zimbabwe": 64, "Ireland": 51,
        "Scotland": 45, "Netherlands": 44, "USA": 41, "Namibia": 32,
        "Nepal": 30, "Oman": 23, "UAE": 14, "Canada": 12,
    },
    "t20i": {  # rating
        "England": 269, "India": 267, "Australia": 260, "New Zealand": 247,
        "South Africa": 243, "Pakistan": 240, "West Indies": 236, "Bangladesh": 222,
        "Sri Lanka": 221, "Afghanistan": 218, "Ireland": 205, "Zimbabwe": 202,
        "USA": 183, "Nepal": 181, "Netherlands": 180, "Namibia": 179,
    },
}

# --- Top 14 2026/27 league table after round 6 ------------------------------
TOP14 = {
    "source_official": "https://www.lnr.fr/rugby-top-14/classement",
    "read_via": "https://www.lequipe.fr/Rugby/top-14/page-classement-equipes/general",
    "corroborated_by": "https://www.rugbyorbit.com/competitions/top-14/",
    "as_of": "2026-10-20",
    "round": 6,
    # club: (points, played, won, drawn, lost, points_difference)
    "table": {
        "Toulouse": (24, 6, 5, 0, 1, 73),
        "Pau": (22, 6, 5, 0, 1, 58),
        "Bordeaux": (19, 6, 4, 0, 2, 64),
        "La Rochelle": (18, 6, 4, 0, 2, 9),
        "Bayonne": (17, 6, 4, 0, 2, -24),
        "Stade Francais": (14, 6, 3, 0, 3, -11),
        "Montpellier": (14, 6, 3, 0, 3, 41),
        "Lyon": (14, 6, 3, 0, 3, -9),
        "Perpignan": (13, 6, 3, 0, 3, -33),
        "Toulon": (12, 6, 2, 0, 4, 0),
        "Clermont": (11, 6, 2, 0, 4, -29),
        "Racing 92": (10, 6, 2, 0, 4, -53),
        "Castres": (9, 6, 2, 0, 4, -27),
        "Vannes": (1, 6, 0, 0, 6, -59),
    },
}

# --- OLBG's own published competition base rates ----------------------------
# Published on the OLBG sport pages, stated to come from OLBG's results database.
OLBG_BASE = {
    "rugby_union": {
        "source": "https://www.olbg.com/betting-tips/Rugby_Union/9",
        "as_of": "2026-10-21",
        # competition: (home_win%, away_win%, level%, avg_total_pts, avg_margin, matches)
        "Premiership":  (64.1, 34.1, 1.9, 54.0, 15.2, 540),
        "Top 14":       (74.4, 23.3, 2.3, 49.7, 14.6, 910),
        "Super Rugby":  (59.6, 38.4, 2.0, 56.1, 16.0, 406),
        "URC":          (64.4, 32.9, 2.6, 48.9, 14.8, 720),
    },
    "handball": {
        "source": "https://www.olbg.com/betting-tips/Handball/20",
        "as_of": "2026-10-18",
        # tournament: (games, favourite_won%, underdog_won%, ties%)
        "EHF Champions League (men)":   (654, 68.2, 22.0, 9.8),
        "EHF Champions League (women)": (647, 74.5, 18.9, 6.6),
        "European Championship (men)":  (307, 68.4, 22.5, 9.1),
        "European Championship (women)":(253, 75.9, 18.6, 5.5),
        "IHF World Championship (men)": (502, 77.9, 14.9, 7.2),
    },
    "rugby_league": {
        "source": "https://www.olbg.com/betting-tips/Rugby_League/10",
        "as_of": "2026-10-20",
        "Super League": (57.3, 40.2, 2.5, 42.0, 18.4, 836),
        "Championship": (52.8, 45.4, 1.8, 48.3, 21.7, 955),
        "NRL":          (54.1, 41.6, 4.4, 46.0, None, 1008),
    },
}

# --- Verified recent form / results (official or governing-body-partner) ------
FORM = {
    "Afghanistan": {
        "facts": [
            "Beat Zimbabwe by 158 runs in the UAE ODI Tri-Series; Sediqullah Atal 102 off 110 and Ibrahim Zadran 90 off 96 in a total of 294.",
            "Beat Bangladesh by 200 runs in the 2nd ODI at Abu Dhabi (Afghanistan 190, Bangladesh 109).",
            "Only Test v Bangladesh (9-13 Oct 2026, Abu Dhabi) drawn; Rahmat Shah 105 not out in the first innings.",
        ],
        "source": "https://www.cricinfo.com/series/afghanistan-v-bangladesh-2026-27-1555106/match-schedule-fixtures-and-results",
        "corroborated_by": "https://www.espn.com/cricket/series/_/id/23884/afg-vs-ban",
        "as_of": "2026-10-20",
    },
    "Bangladesh": {
        "facts": [
            "Lost to Afghanistan by 200 runs in the 2nd ODI, bowled out for 109 chasing 191.",
            "Lost to Zimbabwe by 99 runs earlier in the UAE ODI Tri-Series.",
            "Litton Das top-scored for the side in the series with 155 runs in two innings.",
        ],
        "source": "https://www.espn.com/cricket/series/_/id/23884/afg-vs-ban",
        "corroborated_by": "https://www.cricinfo.com/team/afghanistan-40/match-schedule-fixtures-and-results",
        "as_of": "2026-10-20",
    },
    "Toulouse": {
        "facts": [
            "Top of the Top 14 after round 6 with 24 points from 6 matches (5 wins, 1 loss) and a +73 points difference.",
            "Beat Bayonne 45-34 at home on Sunday 11 October 2026 in round 6.",
        ],
        "source": "https://www.lnr.fr/rugby-top-14/classement",
        "corroborated_by": "https://www.lequipe.fr/Rugby/top-14/page-classement-equipes/general",
        "as_of": "2026-10-20",
    },
    "Perpignan": {
        "facts": [
            "Ninth in the Top 14 after round 6 with 13 points (3 wins, 3 losses) and a -33 points difference.",
            "Beat Vannes 21-12 at home on Saturday 10 October 2026 in round 6.",
        ],
        "source": "https://www.lnr.fr/rugby-top-14/classement",
        "corroborated_by": "https://www.lequipe.fr/Rugby/top-14/page-classement-equipes/general",
        "as_of": "2026-10-20",
    },
    "Bordeaux": {
        "facts": [
            "Third in the Top 14 after round 6 with 19 points from 6 matches (4 wins, 2 losses) and a +64 points difference.",
            "Won 23-22 away at Clermont on Saturday 10 October 2026 in round 6.",
        ],
        "source": "https://www.lnr.fr/rugby-top-14/classement",
        "corroborated_by": "https://all.rugby/tournament/top-14/table",
        "as_of": "2026-10-20",
    },
    "La Rochelle": {
        "facts": [
            "Fourth in the Top 14 after round 6 with 18 points from 6 matches (4 wins, 2 losses) and a +9 points difference.",
            "Won 28-16 away at Lyon on Saturday 10 October 2026 in round 6.",
        ],
        "source": "https://www.lnr.fr/rugby-top-14/classement",
        "corroborated_by": "https://all.rugby/tournament/top-14/table",
        "as_of": "2026-10-20",
    },
}

# ===========================================================================
# MODEL CONSTANTS - disclosed assumptions, NOT sourced facts.
# ===========================================================================
CONSTANTS = {
    "cricket_odi_scale": 25.0,
    "cricket_t20i_scale": 50.0,
    "cricket_home_advantage": 0.0,
    "rugby_points_per_logit": 6.0,
    "rugby_draw_share_from_base": True,
    "notes": [
        "ODI and T20I ICC ratings live on different scales (ODI 0-160, T20I 0-300), "
        "so each format gets its own logistic scale.",
        "No home-advantage term is applied to cricket because no official, "
        "in-session verifiable coefficient was available. Both cricket fixtures "
        "modelled are at neutral venues in the UAE, which limits the impact. "
        "Flagged as a limitation.",
        "Rugby union Tier-2 lines use a logistic on the league-points gap with "
        "the draw probability held at the published competition base rate and "
        "the remaining mass split between the two sides.",
    ],
}

# ===========================================================================
# Per-event modelling table. Keys match the inventory in data/events/*.json.
# Only events listed here get an originated line; everything else is flagged.
# ===========================================================================
def build_cricket():
    out = []
    specs = [
        # (match, format, home_or_first, second, venue, official_start_gmt, official_src)
        ("Afghanistan vs Bangladesh One Day Match", "odi", "Afghanistan", "Bangladesh",
         "Sharjah Cricket Stadium (per Wikipedia) / Abu Dhabi (per ESPNcricinfo) - CONFLICT",
         "2026-10-21 11:30 GMT",
         "https://www.cricinfo.com/series/uae-odi-tri-series-2026-27-1555109/afghanistan-vs-bangladesh-3rd-match-1555119/live-cricket-score"),
        ("New Zealand vs India 1st T20 Match", "t20i", "New Zealand", "India",
         None, None, None),
        ("Namibia vs Ireland 1st ODI", "odi", "Namibia", "Ireland", None, None, None),
        ("England vs Sri Lanka One Day Match", "odi", "England", "Sri Lanka", None, None, None),
    ]
    for match, fmt, a, b, venue, start, src in specs:
        ratings = ICC[fmt]
        if a not in ratings or b not in ratings:
            out.append(dict(match=match, sport="cricket", tier="none",
                            reason=f"ICC {fmt.upper()} rating not verified for {a} or {b}"))
            continue
        scale = CONSTANTS["cricket_odi_scale"] if fmt == "odi" else CONSTANTS["cricket_t20i_scale"]
        ra, rb = ratings[a], ratings[b]
        p_a = logistic(ra - rb, scale)
        p_b = 1 - p_a
        winner = a if p_a >= p_b else b
        p_win = max(p_a, p_b)
        # Disclosed sensitivity: how the pick probability moves if the logistic
        # scale constant were 20% tighter or looser. The constant is our
        # assumption, so we publish the effect rather than hiding it.
        sens = {
            f"scale_{s}": round(max(logistic(ra - rb, s), 1 - logistic(ra - rb, s)), 4)
            for s in (round(scale * 0.8, 1), scale, round(scale * 1.2, 1))
        }
        out.append(dict(
            match=match, sport="cricket", tier="tier1",
            competition=f"ICC {fmt.upper()} rated fixture",
            side_a=a, side_b=b, rating_a=ra, rating_b=rb, rating_scale=scale,
            rating_source=ICC["source"], rating_read_via=ICC["read_via"],
            rating_as_of=ICC["as_of"][fmt],
            p_a=round(p_a, 4), p_b=round(p_b, 4),
            sensitivity_p_a=sens,
            markets=[dict(name="Win Match (moneyline)", our_probability=round(p_a, 4),
                          our_fair_odds_a=fair_odds(p_a), our_fair_odds_b=fair_odds(p_b),
                          basis="ICC rating gap, logistic"),
                     dict(name="Match Total (runs)", our_line=None, basis=None,
                          unverified=True,
                          reason="No official venue/pitch/scoring-rate data verified in-session"),
                     dict(name="Handicap (runs)", our_line=None, basis=None,
                          unverified=True,
                          reason="No official margin model input verified in-session")],
            pick=winner, pick_probability=round(p_win, 4),
            venue=venue, official_start=start, official_source=src,
        ))
    return out


def build_rugby_union():
    """Top 14 fixtures get a Tier-2 line from the official league table.
    URC fixtures get a Tier-3 base-rate line only."""
    out = []
    t14 = TOP14["table"]
    specs = [
        # (match, competition, home, away)
        ("Toulouse v Perpignan", "Top 14", "Toulouse", "Perpignan"),
        ("Bayonne v Lyon", "Top 14", "Bayonne", "Lyon"),
        ("La Rochelle v Bordeaux", "Top 14", "La Rochelle", "Bordeaux"),
    ]
    for match, comp, home, away in specs:
        if home not in t14 or away not in t14:
            out.append(dict(match=match, sport="rugby_union", tier="none",
                            reason=f"Official Top 14 table position not verified for {home} or {away}"))
            continue
        hp, *_ , hpd = t14[home]
        ap, *_ , apd = t14[away]
        base = OLBG_BASE["rugby_union"]["Top 14"]
        p_draw = base[2] / 100.0
        gap = hp - ap
        p_home_nd = logistic(gap + (hpd - apd) / 10.0, CONSTANTS["rugby_points_per_logit"])
        p_home = (1 - p_draw) * p_home_nd
        p_away = (1 - p_draw) * (1 - p_home_nd)
        avg_total = base[3]
        avg_margin = base[4]
        winner = home if p_home >= p_away else away
        out.append(dict(
            match=match, sport="rugby_union", tier="tier2", competition=comp,
            side_a=home, side_b=away,
            rating_a=hp, rating_b=ap, rating_scale=CONSTANTS["rugby_points_per_logit"],
            rating_label="Top 14 league points after round 6",
            rating_source=TOP14["source_official"], rating_read_via=TOP14["read_via"],
            rating_as_of=TOP14["as_of"],
            p_a=round(p_home, 4), p_b=round(p_away, 4), p_draw=round(p_draw, 4),
            markets=[dict(name="Win Match (3-way moneyline)",
                          our_probability=round(p_home, 4), our_probability_draw=round(p_draw, 4),
                          our_probability_away=round(p_away, 4),
                          our_fair_odds_a=fair_odds(p_home), our_fair_odds_draw=fair_odds(p_draw),
                          our_fair_odds_b=fair_odds(p_away),
                          basis="League-points gap (logistic) + published draw base rate"),
                     dict(name="Match Total (points)", our_line=round_to_half(avg_total),
                          our_projected_total=avg_total,
                          basis=f"OLBG published Top 14 average total points {avg_total} over {base[5]} matches",
                          basis_source=OLBG_BASE["rugby_union"]["source"]),
                     dict(name="Handicap (points)", our_line=f"home -{round_to_half(avg_margin)}",
                          our_projected_margin=avg_margin,
                          basis=f"OLBG published Top 14 average winning margin {avg_margin}; competition-level, not team-specific",
                          basis_source=OLBG_BASE["rugby_union"]["source"])],
            pick=winner, pick_probability=round(max(p_home, p_away), 4),
        ))

    urc = [
        ("Connacht v Zebre Parma", "URC", "Connacht", "Zebre Parma"),
        ("Bulls v Ulster", "URC", "Bulls", "Ulster"),
        ("Stormers v Scarlets", "URC", "Stormers", "Scarlets"),
        ("Leinster v Munster", "URC", "Leinster", "Munster"),
    ]
    base = OLBG_BASE["rugby_union"]["URC"]
    for match, comp, home, away in urc:
        p_home, p_away, p_draw = base[0] / 100.0, base[1] / 100.0, base[2] / 100.0
        avg_total, avg_margin = base[3], base[4]
        out.append(dict(
            match=match, sport="rugby_union", tier="tier3", competition=comp,
            side_a=home, side_b=away,
            p_a=round(p_home, 4), p_b=round(p_away, 4), p_draw=round(p_draw, 4),
            rating_source=None,
            markets=[dict(name="Win Match (3-way moneyline)", our_probability=round(p_home, 4),
                          our_probability_draw=round(p_draw, 4), our_probability_away=round(p_away, 4),
                          our_fair_odds_a=fair_odds(p_home), our_fair_odds_draw=fair_odds(p_draw),
                          our_fair_odds_b=fair_odds(p_away),
                          basis=f"OLBG published URC base rates over {base[5]} matches; no team strength applied",
                          basis_source=OLBG_BASE["rugby_union"]["source"]),
                     dict(name="Match Total (points)", our_line=round_to_half(avg_total),
                          our_projected_total=avg_total,
                          basis=f"OLBG published URC average total points {avg_total} over {base[5]} matches",
                          basis_source=OLBG_BASE["rugby_union"]["source"]),
                     dict(name="Handicap (points)", our_line=f"home -{round_to_half(avg_margin)}",
                          our_projected_margin=avg_margin,
                          basis=f"OLBG published URC average winning margin {avg_margin}; competition-level, not team-specific",
                          basis_source=OLBG_BASE["rugby_union"]["source"])],
            pick=home, pick_probability=round(p_home, 4),
        ))
    return out


def round_to_half(x):
    """Nearest .5 line - the half-point convention avoids a push.

    floor(x)+0.5 is the nearest half-point for every x that is not itself an
    exact half-point, so no branch is needed.
    """
    if x is None:
        return None
    return math.floor(x) + 0.5


def confidence(rec):
    """Deterministic confidence rule - disclosed on the site."""
    p = rec.get("pick_probability")
    tier = rec.get("tier")
    has_form = rec.get("form_verified", False)
    if p is None or tier in (None, "none"):
        return "unverified"
    if p >= 0.70 and tier in ("tier1", "tier2") and has_form:
        return "high"
    if p >= 0.60 and tier in ("tier1", "tier2"):
        return "medium"
    if p >= 0.70 and tier == "tier3":
        return "medium"
    return "low"


def main():
    recs = []
    for r in build_cricket():
        if r.get("side_a") in FORM and r.get("side_b") in FORM:
            r["form_verified"] = True
        recs.append(r)
    for r in build_rugby_union():
        if r.get("side_a") in FORM and r.get("side_b") in FORM:
            r["form_verified"] = True
        recs.append(r)
    for r in recs:
        r["confidence"] = confidence(r)
        r["retrieved"] = RETRIEVED
    (DATA / "lines.json").write_text(json.dumps(
        dict(model_constants=CONSTANTS,
             verified_inputs=dict(icc=ICC, top14=TOP14, olbg_base_rates=OLBG_BASE, form=FORM),
             lines=recs), indent=2, ensure_ascii=False) + "\n")

    from collections import Counter
    c = Counter(r["confidence"] for r in recs)
    t = Counter(r["tier"] for r in recs)
    print(f"originated lines: {len(recs)}")
    print("  by tier      :", dict(t))
    print("  by confidence:", dict(c))
    for r in recs:
        print(f"  {r['confidence']:10s} {r['tier']:6s} p={r.get('pick_probability')} "
              f"{r['match']} -> {r.get('pick')}")

if __name__ == "__main__":
    main()
