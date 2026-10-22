#!/usr/bin/env python3
"""
scripts/beacon_model.py — Independent multi-market line origination & strict confidence grading
for /beacon/ (session arena/3babcd0d-olbg2).

Uniform Mathematical Laws Enforced:
  1. Excluded-sport hard gate: rejects soccer, football, horse racing, boxing, american football,
     entertainment/specials, cycling, politics, virtual sports, hurling, ufc, mma (OLBG IDs
     1, 2, 6, 11, 16, 17, 19, 24, 26, 27).
  2. Half-unit (.5) market lines only: all spreads, puck/run/frame/leg/set handicaps, and match
     totals end strictly in '.5' (zero synthetic .25 / .75 Asian quarter-lines; minimum spread
     magnitude is 1.5 so -0.5 never duplicates Win Match).
  3. Exact unrounded confidence & odds-band law:
       HIGH_MAX_PROB = 5.0 / 7.0  (0.7142857142857143 -> exact decimal 1.400000, American -250)
       HIGH_MIN_PROB = 0.7000     (exact decimal 1.428571, American -233)
       BAND_MIN_PROB = 1.0 / 101.0 (0.0099009901 -> exact decimal 101.000000, American +10000)
     A market leg is graded 'high' iff:
       match_state == 'upcoming' AND 0.7000 <= p <= (5.0 / 7.0).
     Selections with p > 5/7 (heavy chalk shorter than -250) are capped at 'medium'.
     Selections with 0.6000 <= p < 0.7000 are 'medium'; selections with p < 0.6000 are 'low'.
  4. Zero hallucinations: rows lacking machine-verifiable official form/ratings remain
     match_state == 'unverified_blank' with '—' across all price fields and are logged in flagged.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEACON_DIR = ROOT / "data" / "beacon"

HIGH_MIN_PROB = 0.7000
HIGH_MAX_PROB = 5.0 / 7.0          # 0.7142857142857143 -> exact 1.40 decimal / -250 American
BAND_MIN_PROB = 1.0 / 101.0        # 0.0099009900990099 -> exact 101.00 decimal / +10000 American
EXCLUDED_IDS = {1, 2, 6, 11, 16, 17, 18, 19, 24, 26, 27}
EXCLUDED_SLUGS = {
    "soccer", "football", "horse-racing", "boxing", "american-football",
    "specials", "entertainment", "cycling", "politics", "virtual-sports",
    "hurling", "ufc", "mma", "ufc-mma",
}


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def clamp(p: float, lo: float = 0.015, hi: float = 0.985) -> float:
    return max(lo, min(hi, p))


def half_line(val: float, minimum: float = 1.5) -> float:
    mag = max(minimum, math.floor(abs(val)) + 0.5)
    return mag if val >= 0 else -mag


def signed_half_spread(expected_margin_home: float, min_abs: float = 1.5) -> float:
    mag = max(min_abs, math.floor(abs(expected_margin_home)) + 0.5)
    return -mag if expected_margin_home >= 0 else mag


def quote_prob(p: float) -> dict:
    p = clamp(p, 0.005, 0.995)
    d_exact = 1.0 / p
    d_disp = round(d_exact, 2)
    if p >= 0.5:
        amer = -int(round(100.0 * p / (1.0 - p)))
        amer_str = f"{amer}"
    else:
        amer = int(round(100.0 * (1.0 - p) / p))
        amer_str = f"+{amer}"
    in_band = (BAND_MIN_PROB <= p <= HIGH_MAX_PROB)
    is_high_window = (HIGH_MIN_PROB <= p <= HIGH_MAX_PROB)
    return {
        "prob": round(p, 4),
        "prob_exact": round(p, 8),
        "decimal": d_disp,
        "decimal_exact": round(d_exact, 6),
        "american": amer,
        "american_str": amer_str,
        "in_band": in_band,
        "is_high_window": is_high_window,
    }


def classify_confidence(p_exact: float, match_state: str) -> tuple[str, str]:
    if match_state != "upcoming":
        if p_exact >= 0.6000:
            return "medium", f"{match_state} (excluded from pre-match high picks)"
        return "low", f"{match_state} (<60%)"
    if HIGH_MIN_PROB <= p_exact <= HIGH_MAX_PROB:
        return "high", "high (70.0%–71.4%, exact -250..-233 window)"
    if p_exact > HIGH_MAX_PROB:
        return "medium", "medium (capped: heavy chalk shorter than -250)"
    if p_exact >= 0.6000:
        return "medium", "medium (60.0%–69.9%)"
    return "low", "low (<60.0%)"


def make_race_to_w_markets(q_unit_home: float, target_wins: int, unit: str, total_line: float) -> dict:
    """Exact discrete negative-binomial match-score distribution for Race-to-W formats (Darts, Snooker)."""
    q = clamp(q_unit_home, 0.20, 0.80)
    scores: list[tuple[int, int, float]] = []
    for k in range(target_wins):
        # Home wins target_wins to k: last unit won by home, k losses among first target_wins - 1 + k units
        comb = math.comb(target_wins - 1 + k, k)
        p_hk = comb * (q ** target_wins) * ((1.0 - q) ** k)
        p_kh = comb * ((1.0 - q) ** target_wins) * (q ** k)
        scores.append((target_wins, k, p_hk))
        scores.append((k, target_wins, p_kh))

    p_home = sum(p for h, a, p in scores if h > a)
    win_market = {
        "type": "2-way",
        "home": quote_prob(p_home),
        "away": quote_prob(1.0 - p_home),
    }

    exp_margin = sum((h - a) * p for h, a, p in scores)
    line_home = -1.5 if exp_margin >= 0 else 1.5
    if abs(exp_margin) >= 2.2:
        line_home = -2.5 if exp_margin >= 0 else 2.5
    p_cov_home = sum(p for h, a, p in scores if (h - a) + line_home > 0)
    handicap_market = {
        "unit": unit,
        "line_home": line_home,
        "line_away": -line_home,
        "home": quote_prob(p_cov_home),
        "away": quote_prob(1.0 - p_cov_home),
    }

    p_over = sum(p for h, a, p in scores if (h + a) > total_line)
    total_market = {
        "unit": unit,
        "line": total_line,
        "over": quote_prob(p_over),
        "under": quote_prob(1.0 - p_over),
    }

    alt_handicap = None
    best_fav_side = "home" if p_home >= 0.5 else "away"
    best_win_p = p_home if best_fav_side == "home" else (1.0 - p_home)
    if best_win_p > HIGH_MAX_PROB:
        for k in range(1, target_wins):
            h = k + 0.5
            if best_fav_side == "home":
                p_cov = sum(p for hs, as_, p in scores if (hs - as_) > h)
            else:
                p_cov = sum(p for hs, as_, p in scores if (as_ - hs) > h)
            if HIGH_MIN_PROB <= p_cov <= HIGH_MAX_PROB:
                alt_handicap = {
                    "unit": unit,
                    "favored_side": best_fav_side,
                    "line": -h,
                    "quote": quote_prob(p_cov),
                }
                break

    return {
        "win_match": win_market,
        "handicap": handicap_market,
        "total": total_market,
        "alt_handicap_in_window": alt_handicap,
    }


def make_standard_markets(
    margin_home: float,
    total_mean: float,
    sd_margin: float,
    sd_total: float,
    unit: str,
    draw_band: float = 0.0,
    fixed_spread_abs: float | None = None,
    p_home_override: float | None = None,
) -> dict:
    if draw_band > 0.0:
        p_home_3 = clamp(1.0 - norm_cdf((draw_band - margin_home) / sd_margin), 0.02, 0.95)
        p_away_3 = clamp(norm_cdf((-draw_band - margin_home) / sd_margin), 0.02, 0.95)
        p_draw_3 = max(0.01, 1.0 - p_home_3 - p_away_3)
        s3 = p_home_3 + p_draw_3 + p_away_3
        p_home_3, p_draw_3, p_away_3 = p_home_3 / s3, p_draw_3 / s3, p_away_3 / s3
        win_market = {
            "type": "3-way",
            "home": quote_prob(p_home_3),
            "draw": quote_prob(p_draw_3),
            "away": quote_prob(p_away_3),
        }
    else:
        p_home_2 = p_home_override if p_home_override is not None else clamp(norm_cdf(margin_home / sd_margin), 0.02, 0.98)
        win_market = {
            "type": "2-way",
            "home": quote_prob(p_home_2),
            "away": quote_prob(1.0 - p_home_2),
        }

    if fixed_spread_abs is not None:
        line_home = -fixed_spread_abs if margin_home >= 0 else fixed_spread_abs
    else:
        line_home = signed_half_spread(margin_home, min_abs=1.5)
    threshold = -line_home
    p_cover_home = clamp(1.0 - norm_cdf((threshold - margin_home) / sd_margin), 0.04, 0.96)
    handicap_market = {
        "unit": unit,
        "line_home": line_home,
        "line_away": -line_home,
        "home": quote_prob(p_cover_home),
        "away": quote_prob(1.0 - p_cover_home),
    }

    total_line = half_line(total_mean, minimum=1.5)
    # Small structural continuity offset when total_mean lands on exact .5
    eff_mean = total_mean + 0.18 if abs(total_mean - total_line) < 1e-6 else total_mean
    p_over = clamp(1.0 - norm_cdf((total_line - eff_mean) / sd_total), 0.05, 0.95)
    total_market = {
        "unit": unit,
        "line": total_line,
        "over": quote_prob(p_over),
        "under": quote_prob(1.0 - p_over),
    }

    # Investigate genuine half-unit (.5) spreads >= 1.5 when moneyline is heavy chalk (> 5/7)
    alt_handicap = None
    best_fav_side = "home" if margin_home >= 0 else "away"
    fav_margin = abs(margin_home)
    best_win_p = win_market["home"]["prob_exact"] if best_fav_side == "home" else win_market["away"]["prob_exact"]
    if best_win_p > HIGH_MAX_PROB:
        for k in range(1, 65):
            h = k + 0.5
            p_cov = clamp(1.0 - norm_cdf((h - fav_margin) / sd_margin), 0.04, 0.96)
            if HIGH_MIN_PROB <= p_cov <= HIGH_MAX_PROB:
                alt_handicap = {
                    "unit": unit,
                    "favored_side": best_fav_side,
                    "line": -h,
                    "quote": quote_prob(p_cov),
                }
                break

    return {
        "win_match": win_market,
        "handicap": handicap_market,
        "total": total_market,
        "alt_handicap_in_window": alt_handicap,
    }


def finalize_match_row(
    *,
    row_id: str,
    sport: str,
    sport_name: str,
    olbg_id: int,
    competition: str,
    event_type: str,
    match_state: str,
    date: str,
    start_utc: str,
    venue: str,
    home: str,
    away: str,
    home_form: str,
    away_form: str,
    markets: dict | None,
    official_source: str,
    official_url: str,
    olbg_url: str,
    state_note: str = "",
) -> dict:
    assert olbg_id not in EXCLUDED_IDS, f"Excluded OLBG ID {olbg_id} on {row_id}"
    assert sport not in EXCLUDED_SLUGS, f"Excluded sport slug {sport} on {row_id}"
    for bad in ("Basketball/19", "Australian_Rules/27", "Esports/28", "northern-ireland-open-2026", "unitedrugby.com/standings", "liquipedia.net"):
        assert bad not in official_url and bad not in olbg_url, f"Banned URL token {bad} on {row_id}"

    if match_state == "unverified_blank" or markets is None:
        return {
            "id": row_id,
            "sport": sport,
            "sport_name": sport_name,
            "olbg_id": olbg_id,
            "competition": competition,
            "event_type": event_type,
            "match_state": "unverified_blank",
            "date": date,
            "start_utc": start_utc or "—",
            "venue": venue or "—",
            "home": home,
            "away": away,
            "home_form": home_form or "—",
            "away_form": away_form or "—",
            "markets": None,
            "winner_pick": {
                "selection": "—",
                "market": "—",
                "prob": None,
                "decimal": None,
                "american_str": "—",
                "in_band": False,
                "confidence": "unverified",
                "confidence_note": state_note or "Unverified — left blank per zero-hallucination rule",
            },
            "actionable_market": None,
            "official_source": official_source,
            "official_url": official_url,
            "olbg_url": olbg_url,
        }

    if markets.get("handicap"):
        lh = abs(markets["handicap"]["line_home"])
        assert lh >= 1.5 and abs((lh - math.floor(lh)) - 0.5) < 1e-9, f"Invalid handicap {lh} on {row_id}"
    if markets.get("total"):
        tl = abs(markets["total"]["line"])
        assert abs((tl - math.floor(tl)) - 0.5) < 1e-9, f"Non-.5 total {tl} on {row_id}"

    wm = markets["win_match"]
    if wm["home"]["prob_exact"] >= wm["away"]["prob_exact"]:
        w_side, w_name, w_q = "home", home, wm["home"]
    else:
        w_side, w_name, w_q = "away", away, wm["away"]

    conf, conf_note = classify_confidence(w_q["prob_exact"], match_state)
    if state_note and match_state != "upcoming":
        conf_note = f"{match_state}: {state_note}"

    actionable = None
    if w_q["in_band"]:
        actionable = {
            "market": "Win Match" if event_type == "head_to_head" else "Tournament / Race Outright",
            "selection": f"{w_name} to Win",
            "quote": w_q,
            "confidence": classify_confidence(w_q["prob_exact"], match_state)[0],
        }
    elif markets.get("alt_handicap_in_window"):
        ah = markets["alt_handicap_in_window"]
        team_lbl = home if ah["favored_side"] == "home" else away
        actionable = {
            "market": f"Handicap ({ah['unit']})",
            "selection": f"{team_lbl} {ah['line']:+.1f} {ah['unit']}",
            "quote": ah["quote"],
            "confidence": classify_confidence(ah["quote"]["prob_exact"], match_state)[0],
        }
    elif markets.get("handicap"):
        hc = markets["handicap"]
        if hc["home"]["prob_exact"] >= hc["away"]["prob_exact"]:
            actionable = {
                "market": f"Handicap ({hc['unit']})",
                "selection": f"{home} {hc['line_home']:+.1f} {hc['unit']}",
                "quote": hc["home"],
                "confidence": classify_confidence(hc["home"]["prob_exact"], match_state)[0],
            }
        else:
            actionable = {
                "market": f"Handicap ({hc['unit']})",
                "selection": f"{away} {hc['line_away']:+.1f} {hc['unit']}",
                "quote": hc["away"],
                "confidence": classify_confidence(hc["away"]["prob_exact"], match_state)[0],
            }

    return {
        "id": row_id,
        "sport": sport,
        "sport_name": sport_name,
        "olbg_id": olbg_id,
        "competition": competition,
        "event_type": event_type,
        "match_state": match_state,
        "date": date,
        "start_utc": start_utc,
        "venue": venue,
        "home": home,
        "away": away,
        "home_form": home_form,
        "away_form": away_form,
        "markets": markets,
        "winner_pick": {
            "side": w_side,
            "selection": w_name,
            "market": "Win Match" if event_type == "head_to_head" else "Outright Winner",
            "prob": w_q["prob"],
            "prob_exact": w_q["prob_exact"],
            "decimal": w_q["decimal"],
            "decimal_exact": w_q["decimal_exact"],
            "american": w_q["american"],
            "american_str": w_q["american_str"],
            "in_band": w_q["in_band"],
            "confidence": conf,
            "confidence_note": conf_note,
        },
        "actionable_market": actionable,
        "official_source": official_source,
        "official_url": official_url,
        "olbg_url": olbg_url,
    }


PROSE_CATALOG: dict[str, dict] = {
    "nhl-2026020162": {
        "players": ["Kirill Kaprizov", "Filip Gustavsson", "Rasmus Andersson"],
        "prose": (
            "Minnesota arrives at Scotiabank Saddledome at 6-2-2 with a +6 goal differential (31 GF, 25 GA in 10 GP), "
            "powered by Kirill Kaprizov's elite five-on-five creation and Filip Gustavsson's steady crease work. "
            "Calgary sits 2-6-0 after surrendering 37 goals across its opening eight games (4.63 GA/G) despite heavy "
            "top-pair minutes from defenseman Rasmus Andersson; back the Minnesota Wild to win on the Moneyline."
        ),
    },
    "pdc-32329": {
        "players": ["Ross Smith", "Karel Sedlacek"],
        "prose": (
            "Former Dortmund European Champion Ross Smith enters Thursday's opening session ranked World No. 13 on the "
            "official PDC Order of Merit (£567,250) with tour-leading 180 power on the Westfalenhalle stage. Czech qualifier "
            "Karel Sedlacek scraped into the 32nd and final European Tour qualification spot (£34,500, edging Kim Huybrechts "
            "on countback), giving heavy-scoring Ross Smith a clear edge to win their best-of-11 opener."
        ),
    },
    "nba-0022600101": {
        "players": ["Stephen Curry", "Draymond Green", "Ja Morant"],
        "prose": (
            "Golden State protects Chase Center behind Stephen Curry's off-ball gravity and Draymond Green's half-court defensive "
            "communication after posting a winning 22-19 home record last campaign. Visiting Memphis stumbled to a 25-57 mark "
            "(11-29 on the road) despite Ja Morant's rim pressure, giving the Warriors a decisive shot-quality advantage; "
            "back Golden State Warriors to win."
        ),
    },
    "nba-0022600106": {
        "players": ["Tyrese Maxey", "Joel Embiid", "Giannis Antetokounmpo"],
        "prose": (
            "Philadelphia opened the 2026-27 NBA campaign with a composed 106-100 victory over New York behind Tyrese Maxey's "
            "perimeter shot creation and Joel Embiid's half-court interior gravity, building on a 45-37 baseline (23-18 at home). "
            "Milwaukee went just 13-28 on the road during its 32-50 campaign despite Giannis Antetokounmpo's paint scoring; "
            "back Philadelphia 76ers to win."
        ),
    },
    "nba-0022600152": {
        "players": ["Victor Wembanyama", "De'Aaron Fox", "Anthony Edwards"],
        "prose": (
            "San Antonio posted a dominant 32-8 home mark during its 62-20 campaign and returns to Frost Bank Center behind "
            "rim protector Victor Wembanyama and guard De'Aaron Fox after Tuesday's 116-104 road loss in Oklahoma City. Minnesota "
            "finished 49-33 (23-18 away) led by Anthony Edwards, but San Antonio's interior length controls home paint touches; "
            "take San Antonio Spurs to win."
        ),
    },
    "el-E2026-67": {
        "players": ["Kendrick Nunn", "Kostas Sloukas", "Tadas Sedekerskis"],
        "prose": (
            "First-placed Panathinaikos (5-1, +90 point differential, 528 PF / 438 PA) returns to Telekom Center Athens welcoming "
            "back Kendrick Nunn—who scored 16 points with 6 assists in 21 minutes in his weekend return—alongside Kostas Sloukas "
            "after Round 6's defeat to Hapoel Tel Aviv. Visiting Baskonia sits 1-5 (-60 differential) despite Tadas Sedekerskis; "
            "lay Panathinaikos AKTOR Athens -11.5 Points."
        ),
    },
    "top14-11867": {
        "players": ["Antoine Dupont", "Thomas Ramos", "Tom Ecochard"],
        "prose": (
            "Top 14 leaders Stade Toulousain (1st, 24 points, 5-0-1, 197 PF / 124 PA on a five-match league winning streak) host "
            "ninth-placed USA Perpignan (13 points, -33 differential) at Stade Ernest-Wallon behind halfback Antoine Dupont and "
            "goal-kicker Thomas Ramos. Perpignan shipped 55 points at Racing 92 (55-25) and lost 29-14 at Dragons despite Tom Ecochard; "
            "take Stade Toulousain -5.5 Points."
        ),
    },
    "prod2-12068": {
        "players": ["Luka Matkava", "Justin Bouraux", "Jérôme Bosviel"],
        "prose": (
            "Unbeaten Pro D2 juggernaut Oyonnax Rugby (1st, 33 points, 7-0-0, +159 differential at 313 PF / 154 PA) travels to "
            "Stade Sapiac fresh off routing Valence Romans 51-25 and Narbonne 57-14 with fly-half Luka Matkava pulling the strings. "
            "Eighth-placed US Montauban (17 points, -32 differential) just conceded 54 points in a 54-28 loss at Dax despite Jérôme "
            "Bosviel; back Oyonnax Rugby -1.5 Points."
        ),
    },
    "prod2-12066": {
        "players": ["Tedo Abzhandadze", "Karsen Talalua", "Luka Plataret"],
        "prose": (
            "Stade Aurillacois returns to Stade Jean-Alric in composed Pro D2 form (16 points, 4-0-3) right after edging Béziers "
            "25-24 on the road behind fly-half Tedo Abzhandadze and center Karsen Talalua. Bottom club USON Nevers remains winless "
            "through seven rounds (0-0-7, 4 points, -116 differential) after losing 38-7 to Agen despite flanker Luka Plataret; "
            "lay Stade Aurillacois -1.5 Points."
        ),
    },
    "urc-292610": {
        "players": ["Ewan Ashman", "Darcy Graham", "Francke Horn"],
        "prose": (
            "Unbeaten URC leaders Edinburgh Rugby (1st, 14 points, 3-0-0, 80 PF / 54 PA) return to Hive Stadium eager to bounce "
            "back from Friday's 27-17 Challenge Cup loss to Toulon in which hooker Ewan Ashman scored alongside winger Darcy Graham. "
            "The visiting 10bet Lions sit 2-0-1 with 102 points conceded (-25 differential) behind No. 8 Francke Horn; "
            "back Edinburgh Rugby -3.5 Points."
        ),
    },
    "rlwc-r2-ton-leb": {
        "players": ["Haumole Olakau'atu", "Isaiya Katoa", "Jacob Kiraz"],
        "prose": (
            "Tonga stunned England 30-12 in Perth in Rugby League World Cup Round 1, powered by a dominant Haumole Olakau'atu "
            "double, a Tolutau Koula try, and clinical goal-kicking from halfback Isaiya Katoa. Lebanon fell 42-18 to Papua New "
            "Guinea in Round 1 despite winger Jacob Kiraz's yardage, leaving the Cedars outgunned through the middle; "
            "back Tonga -28.5 Points at CommBank Stadium."
        ),
    },
    "rlwc-r2-nzl-cok": {
        "players": ["Jamayne Isaako", "Casey McLean", "Esan Marsters"],
        "prose": (
            "New Zealand pushed reigning champions Australia to the final four minutes in Sydney's 24-22 World Cup opener, led by "
            "winger Casey McLean's early try and five-from-five goal-kicking (10 points) by Jamayne Isaako. The Cook Islands "
            "surrendered seven tries in a 40-12 Round 1 defeat to Fiji in Newcastle despite Esan Marsters's offloading; "
            "take New Zealand -9.5 Points in Christchurch."
        ),
    },
    "pdc-32324": {
        "players": ["Dirk van Duijvenbode", "Luke Woodhouse"],
        "prose": (
            "Dutch power scorer Dirk van Duijvenbode brings prolific 180-hitting pedigree onto the Westfalenhalle stage in Dortmund "
            "for Thursday's opening best-of-11 tie against World No. 25 Luke Woodhouse. With just £39,000 separating their two-year "
            "Order of Merit totals in a tight race-to-six format where single-break deciders are common, receiving a leg start "
            "offers standout value; take Dirk van Duijvenbode +1.5 Legs."
        ),
    },
    "pdc-2026-ec-r1-huybrechts-searle": {
        "players": ["Ryan Searle", "Kim Huybrechts", "Luke Humphries"],
        "prose": (
            "World No. 15 Ryan Searle (£562,250 on the PDC Order of Merit) receives a massive Dortmund draw boost after World No. 2 "
            "Luke Humphries withdrew today with gastroenteritis. Late Belgian replacement Kim Huybrechts (World No. 55, European Tour "
            "#33) enters off a 6-5 qualifying loss to Jimmy van Schie in which he missed match darts; back Ryan Searle to win."
        ),
    },
    "wst-nio-r16-williams-odonnell": {
        "players": ["Mark Williams", "Martin O'Donnell"],
        "prose": (
            "Three-time Crucible champion Mark Williams sits World No. 8 on the official Johnstone's Paint World Rankings (£747,400) "
            "and brings clinical tactical control into Belfast's Waterfront Hall against World No. 46 Martin O'Donnell (£149,500). "
            "Across a short best-of-7 Last-16 clash, Williams's heavy scoring among the balls sets up multi-frame cushion potential; "
            "back Mark Williams to win."
        ),
    },
    "atp-lyo-qf-moutet-paul": {
        "players": ["Tommy Paul", "Corentin Moutet", "Benjamin Bonzi"],
        "prose": (
            "Fourth-seeded American Tommy Paul (World No. 17) survived a stern indoor test in Lyon's second round, outlasting "
            "Frenchman Benjamin Bonzi 6-4, 6-7, 6-3 with relentless return depth and late-set poise. Left-hander Corentin Moutet "
            "(World No. 54) beat qualifier Felix Balshaw 6-4, 6-4, yet Paul's superior first-strike court positioning neutralizes "
            "Moutet's slice variety indoors; back Tommy Paul to win."
        ),
    },
    "wta-osa-qf-boulter-ruzic": {
        "players": ["Katie Boulter", "Antonia Ruzic"],
        "prose": (
            "British No. 1 Katie Boulter (World No. 31) brings proven Asian-swing outdoor hard-court pedigree into Friday's WTA 250 "
            "Japan Open quarterfinal in Osaka against Croatia's World No. 96 Antonia Ruzic. Boulter's flat first serve and aggressive "
            "forehand return consistently punish second serves on Utsubo's quick hard courts, giving her the matchup edge; "
            "back Katie Boulter to win."
        ),
    },
    "ehfcl-202711020101049": {
        "players": ["Dika Mem", "Sergey Hernandez", "Kyllian Villeminot"],
        "prose": (
            "Twelve-time European champions Barça sit a perfect 4-0 atop EHF Champions League Group E (+33 differential, 137 GF / "
            "104 GA), led by captain Dika Mem (23 CL goals) and goalkeeper Sergey Hernandez after edging Montpellier 28-27 away in "
            "Round 2 and routing Cangas 37-28 domestically. Against 1-3 Montpellier and Kyllian Villeminot (15 goals), "
            "back Barça -3.5 Goals at Palau Blaugrana."
        ),
    },
    "ehfcl-202711020101064": {
        "players": ["Gisli Kristjansson", "Simon Jeppsson"],
        "prose": (
            "Unbeaten Group F leaders SC Magdeburg (4-0, +33 goal differential, 141 GF / 108 GA) crushed Kolstad 37-22 (19-12 at "
            "halftime) in Round 1 and arrive off a 29-28 Bundesliga win over Stuttgart behind playmaker Gisli Kristjansson (25 CL "
            "goals). Winless Kolstad sits 0-4 (-32 differential) and just lost 37-25 to Elverum despite Simon Jeppsson's 28 goals; "
            "back SC Magdeburg on the minus handicap."
        ),
    },
    "superlega-r2-9-piacenza-modena": {
        "players": ["Antoine Brizard", "Yuri Romanò", "Paul Buchegger"],
        "prose": (
            "Gas Sales Bluenergy Piacenza opened the 2026-27 SuperLega campaign with an authoritative 3-0 road sweep at Padova "
            "(75-56 total points, +19 point differential) orchestrated by French Olympic setter Antoine Brizard and opposite Yuri "
            "Romanò. Visiting Modena dropped its PalaPanini opener 3-0 (61-75) to Trentino despite opposite Paul Buchegger; "
            "back Gas Sales Bluenergy Piacenza -4.5 Points in the Via Emilia derby."
        ),
    },
    "aflw-2026-r11-syd-wce": {
        "players": ["Chloe Molloy", "Laura Gardiner", "Ella Roberts"],
        "prose": (
            "Fifth-placed Sydney Swans (28 points, 135.4% percentage, 3-0 all-time head-to-head against West Coast) return to Henson "
            "Park surging off an emphatic 80-29 Round 10 demolition of Collingwood fueled by ball magnet Laura Gardiner and forward "
            "star Chloe Molloy. Eleventh-placed West Coast (16 points, 86.2%) leans heavily on Ella Roberts away from Perth; "
            "take Sydney Swans -10.5 Points."
        ),
    },
    "aflw-2026-r11-nmfc-adel": {
        "players": ["Jasmine Garner", "Ash Riddell", "Ebony Marinoff"],
        "prose": (
            "Ladder-leading North Melbourne (1st, 36 points, 251.9% percentage) heads to North Hobart Oval behind All-Australian "
            "midfielders Jasmine Garner and Ash Riddell. Ninth-placed Adelaide (20 points, 102.4% percentage) relies heavily on "
            "stoppage tackling from Ebony Marinoff and Anne Hatchard and lacks the scoring efficiency to match the Kangaroos across "
            "four quarters in Tasmania; lay North Melbourne's minus handicap."
        ),
    },
    "lol-w26-r1-hle-tes": {
        "players": ["Viper", "Zeka", "JackeyLove"],
        "prose": (
            "LCK second seed and reigning 2026 Mid-Season Invitational champion Hanwha Life Esports—who defeated Bilibili Gaming 3-2 "
            "for the MSI title before reaching the LCK Grand Final behind star carries Viper and Zeka—opens Swiss play in Allen "
            "against LPL third seed TOP Esports. While JackeyLove brings early bot-lane aggression, HLE's superior objective setups "
            "make Hanwha Life Esports Moneyline the top selection."
        ),
    },
    "crk-uae-final-afg-zim": {
        "players": ["Rashid Khan", "Sediqullah Atal", "Craig Ervine"],
        "prose": (
            "Afghanistan dominated the UAE ODI Tri-Series group table at 2-0 (NRR +2.362), routing Zimbabwe by 158 runs (294 vs 136) "
            "on October 19 behind Sediqullah Atal's century (102) and Rashid Khan's 4/17 before beating Bangladesh by 7 wickets "
            "(Rashid 4/31). Even with Craig Ervine leading 1-1 Zimbabwe, Sharjah's turning deck favors Afghanistan's spin attack; "
            "back Afghanistan -13.5 Runs."
        ),
    },
    "gaa-3532-galway-sfc": {
        "players": ["Dessie Conneely", "Peter Cooke", "Robert Finnerty"],
        "prose": (
            "Defending Galway champions Maigh Cuilinn (Moycullen) roared into Sunday's county final at Pearse Stadium behind a "
            "commanding 4-26 to 0-08 semi-final rout of Annaghdown, spearheaded by accurate corner-forward Dessie Conneely (2-16 "
            "campaign tally) and midfielder Peter Cooke. Salthill-Knocknacarra edged Corofin 0-15 to 2-07 behind Robert Finnerty, "
            "making Maigh Cuilinn -1.5 Points the clear selection."
        ),
    },
}


def build_all_matches(inp: dict) -> list[dict]:
    rows: list[dict] = []

    # 1. Ice Hockey — NHL (12 games on Oct 22, shrunk 4 GP toward 3.05 league mean per METHODOLOGY.md) + SHL (6 games on Oct 22)
    nhl_t = inp["nhl_teams"]
    for g in inp["nhl_fixtures"]:
        gid = str(g["game_id"])
        hm, aw = nhl_t[g["home"]], nhl_t[g["away"]]
        h_gpg = (hm["gf"] + 4.0 * 3.05) / (hm["gp"] + 4.0)
        h_gapg = (hm["ga"] + 4.0 * 3.05) / (hm["gp"] + 4.0)
        a_gpg = (aw["gf"] + 4.0 * 3.05) / (aw["gp"] + 4.0)
        a_gapg = (aw["ga"] + 4.0 * 3.05) / (aw["gp"] + 4.0)
        lam_h = 0.5 * (h_gpg + a_gapg) + 0.16
        lam_a = 0.5 * (a_gpg + h_gapg) - 0.04
        margin = lam_h - lam_a
        tot = max(5.2, min(7.2, lam_h + lam_a))
        p_home = clamp(norm_cdf(margin / 1.95), 0.25, 0.75)
        mkts = make_standard_markets(margin, tot, sd_margin=1.95, sd_total=2.15, unit="Goals", fixed_spread_abs=1.5, p_home_override=p_home)
        leaders = inp["nhl_leaders"].get(gid, {}).get("leaders", {})
        h_lead = leaders.get(g["home"], {})
        a_lead = leaders.get(g["away"], {})
        h_extra = f"; {h_lead['goals'][0]} {h_lead['goals'][1]}G, {h_lead['assists'][0]} {h_lead['assists'][1]}A" if h_lead else ""
        a_extra = f"; {a_lead['goals'][0]} {a_lead['goals'][1]}G, {a_lead['assists'][0]} {a_lead['assists'][1]}A" if a_lead else ""
        rows.append(finalize_match_row(
            row_id=f"nhl-{gid}", sport="ice-hockey", sport_name="Ice Hockey", olbg_id=13,
            competition="NHL 2026-27 Regular Season", event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["start_utc"], venue=g["venue"],
            home=hm["name"], away=aw["name"],
            home_form=f"{hm['w']}-{hm['l']}-{hm['otl']} ({hm['gf']} GF / {hm['ga']} GA in {hm['gp']} GP{h_extra})",
            away_form=f"{aw['w']}-{aw['l']}-{aw['otl']} ({aw['gf']} GF / {aw['ga']} GA in {aw['gp']} GP{a_extra})",
            markets=mkts, official_source="NHL Official Score & Standings API",
            official_url="https://api-web.nhle.com/v1/score/2026-10-22",
            olbg_url="https://www.olbg.com/betting-tips/Ice_Hockey/13",
        ))

    shl_t = inp["shl_teams"]
    for g in inp["shl_fixtures"]:
        hm, aw = shl_t[g["home"]], shl_t[g["away"]]
        lam_h = 0.5 * ((hm["gf"] + 12.0) / (hm["gp"] + 4.0) + (aw["ga"] + 12.0) / (aw["gp"] + 4.0)) + 0.18
        lam_a = 0.5 * ((aw["gf"] + 12.0) / (aw["gp"] + 4.0) + (hm["ga"] + 12.0) / (hm["gp"] + 4.0)) - 0.04
        margin = lam_h - lam_a
        mkts = make_standard_markets(margin, lam_h + lam_a, sd_margin=1.90, sd_total=2.05, unit="Goals", fixed_spread_abs=1.5)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="ice-hockey", sport_name="Ice Hockey", olbg_id=13,
            competition="Swedish Hockey League (SHL) 2026-27", event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["time"], venue=g["venue"],
            home=hm["name"], away=aw["name"],
            home_form=f"{hm['pts']} pts in {hm['gp']} GP ({hm['gf']} GF / {hm['ga']} GA)",
            away_form=f"{aw['pts']} pts in {aw['gp']} GP ({aw['gf']} GF / {aw['ga']} GA)",
            markets=mkts, official_source="Swedish Ice Hockey Association (SHL 20961)",
            official_url="https://stats.swehockey.se/ScheduleAndResults/Standings/20961",
            olbg_url="https://www.olbg.com/betting-tips/Ice_Hockey/13",
        ))

    # 2. Basketball — NBA (74 games Oct 22-31) + EuroLeague Round 7 (9 games Oct 22-23)
    nba_t = inp["nba_teams"]
    nba_open = inp["nba_2026_opening"]
    for g in inp["nba_fixtures"]:
        hm, aw = nba_t[g["home"]], nba_t[g["away"]]
        h_wp = (hm["w"] + 4.0) / 90.0
        a_wp = (aw["w"] + 4.0) / 90.0
        margin = (h_wp - a_wp) * 26.5 + 2.8
        tot = 223.8 + (h_wp + a_wp - 1.0) * 14.0
        mkts = make_standard_markets(margin, tot, sd_margin=11.8, sd_total=13.5, unit="Points")
        h_open = f" | 2026-27: {nba_open[g['home']]['record_26_27']}" if g["home"] in nba_open else ""
        a_open = f" | 2026-27: {nba_open[g['away']]['record_26_27']}" if g["away"] in nba_open else ""
        gid = g.get("id") or f"nba-{g['game_id']}"
        slug_h = g["home"].lower()
        slug_a = g["away"].lower()
        raw_num = gid.replace("nba-", "")
        rows.append(finalize_match_row(
            row_id=gid, sport="basketball", sport_name="Basketball", olbg_id=4,
            competition="NBA 2026-27 Regular Season", event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=f"{g['date']} {g.get('tip_et') or g.get('time', '19:00 ET')}",
            venue=g["venue"], home=hm["name"], away=aw["name"],
            home_form=f"Baseline {hm['w']}-{hm['l']} (Home {hm['home_w']}-{hm['home_l']}){h_open}",
            away_form=f"Baseline {aw['w']}-{aw['l']} (Road {aw['road_w']}-{aw['road_l']}){a_open}",
            markets=mkts, official_source="NBA Official Schedule & Standings",
            official_url=f"https://www.nba.com/game/{slug_a}-vs-{slug_h}-{raw_num}",
            olbg_url="https://www.olbg.com/betting-tips/Basketball/4",
        ))

    el_t = inp["euroleague_teams"]
    for g in inp["euroleague_fixtures"]:
        hm, aw = el_t[g["home"]], el_t[g["away"]]
        h_net = (hm["pf"] - hm["pa"]) / hm["gp"]
        a_net = (aw["pf"] - aw["pa"]) / aw["gp"]
        hca = 0.0 if g.get("neutral") else 3.4
        margin = 0.56 * (h_net - a_net) + hca
        tot = 0.5 * ((hm["pf"] + hm["pa"]) / hm["gp"] + (aw["pf"] + aw["pa"]) / aw["gp"])
        mkts = make_standard_markets(margin, tot, sd_margin=10.6, sd_total=11.8, unit="Points")
        rows.append(finalize_match_row(
            row_id=g["id"], sport="basketball", sport_name="Basketball", olbg_id=4,
            competition="EuroLeague 2026-27 — Round 7", event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["time"], venue=g["venue"],
            home=hm["name"], away=aw["name"],
            home_form=f"Rank #{hm['rank']} ({hm['w']}-{hm['l']}, {hm['pf']}:{hm['pa']})",
            away_form=f"Rank #{aw['rank']} ({aw['w']}-{aw['l']}, {aw['pf']}:{aw['pa']})",
            markets=mkts, official_source="EuroLeague Basketball Official Game Center",
            official_url=g["url"], olbg_url="https://www.olbg.com/betting-tips/Basketball/4",
        ))

    # 3. Rugby Union — Top 14 (7), Pro D2 (8), URC R4 (8) + URC R5 (8)
    for comp_lbl, teams_key, fix_key, src_lbl in [
        ("French Top 14 — Round 7", "top14_teams", "top14_fixtures", "LNR Top 14 Official Match Sheet"),
        ("French Pro D2 — Round 8", "prod2_teams", "prod2_fixtures", "LNR Pro D2 Official Match Sheet"),
    ]:
        tmap = inp[teams_key]
        for g in inp[fix_key]:
            hm, aw = tmap[g["home"]], tmap[g["away"]]
            h_pd = (hm["pf"] - hm["pa"]) / hm["gp"]
            a_pd = (aw["pf"] - aw["pa"]) / aw["gp"]
            margin = 0.46 * (h_pd - a_pd) + 4.2
            tot = 0.5 * ((hm["pf"] + hm["pa"]) / hm["gp"] + (aw["pf"] + aw["pa"]) / aw["gp"])
            mkts = make_standard_markets(margin, tot, sd_margin=12.4, sd_total=13.0, unit="Points", draw_band=0.45)
            rows.append(finalize_match_row(
                row_id=g["id"], sport="rugby-union", sport_name="Rugby Union", olbg_id=9,
                competition=comp_lbl, event_type="head_to_head", match_state="upcoming",
                date=g["date"], start_utc=g["time"], venue="Official Club Stadium (LNR)",
                home=hm["name"], away=aw["name"],
                home_form=f"#{hm['rank']} ({hm['pts']} pts, {hm['w']}-{hm['d']}-{hm['l']}, {hm['pf']}:{hm['pa']})",
                away_form=f"#{aw['rank']} ({aw['pts']} pts, {aw['w']}-{aw['d']}-{aw['l']}, {aw['pf']}:{aw['pa']})",
                markets=mkts, official_source=src_lbl, official_url=g["url"], olbg_url=g["olbg_url"],
            ))

    urc_t = inp["urc_teams"]
    for rnd_lbl, fix_key in [("United Rugby Championship — Round 4", "urc_r4_fixtures"), ("United Rugby Championship — Round 5", "urc_r5_fixtures")]:
        for g in inp[fix_key]:
            hm, aw = urc_t[g["home"]], urc_t[g["away"]]
            h_pd = (hm["pf"] - hm["pa"]) / hm["gp"]
            a_pd = (aw["pf"] - aw["pa"]) / aw["gp"]
            margin = 0.40 * (h_pd - a_pd) + 3.8
            tot = 0.5 * ((hm["pf"] + hm["pa"]) / hm["gp"] + (aw["pf"] + aw["pa"]) / aw["gp"])
            mkts = make_standard_markets(margin, tot, sd_margin=12.6, sd_total=13.2, unit="Points", draw_band=0.45)
            rows.append(finalize_match_row(
                row_id=g["id"], sport="rugby-union", sport_name="Rugby Union", olbg_id=9,
                competition=rnd_lbl, event_type="head_to_head", match_state="upcoming",
                date=g["date"], start_utc=g["time"], venue=g["venue"],
                home=hm["name"], away=aw["name"],
                home_form=f"{hm['w']}-{hm['d']}-{hm['l']} ({hm['pf']} PF / {hm['pa']} PA in {hm['gp']} GP)",
                away_form=f"{aw['w']}-{aw['d']}-{aw['l']} ({aw['pf']} PF / {aw['pa']} PA in {aw['gp']} GP)",
                markets=mkts, official_source="URC Official Match Centre & 2026-27 Table",
                official_url=g["url"], olbg_url="https://www.olbg.com/betting-tips/Rugby_Union/9",
            ))

    # 4. Rugby League — RLWC 2026 Men's Round 2 (5 matches)
    rl_t = inp["rlwc_teams"]
    for g in inp["rlwc_fixtures"]:
        hm, aw = rl_t[g["home"]], rl_t[g["away"]]
        r1_diff_h = hm["r1_pf"] - hm["r1_pa"]
        r1_diff_a = aw["r1_pf"] - aw["r1_pa"]
        rank_gap = aw["irl_rank"] - hm["irl_rank"]
        hca = 0.0 if g.get("neutral") else 3.0
        margin = 1.65 * rank_gap + 0.14 * (r1_diff_h - r1_diff_a) + hca
        tot = 44.5 + 0.12 * abs(margin)
        mkts = make_standard_markets(margin, tot, sd_margin=13.2, sd_total=12.5, unit="Points", draw_band=0.40)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="rugby-league", sport_name="Rugby League", olbg_id=10,
            competition=g["competition"], event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["time"], venue=g["venue"],
            home=hm["name"], away=aw["name"],
            home_form=f"IRL #{hm['irl_rank']}; R1: {hm['r1_note']}",
            away_form=f"IRL #{aw['irl_rank']}; R1: {aw['r1_note']}",
            markets=mkts, official_source="NRL / IRL 2026 World Cup Match Centre",
            official_url=g["official_url"], olbg_url="https://www.olbg.com/betting-tips/Rugby_League/10",
        ))

    # 5. Baseball — 2026 MLB World Series Games 1-4
    mlb_t = inp["mlb_teams"]
    for g in inp["mlb_fixtures"]:
        hm, aw = mlb_t[g["home"]], mlb_t[g["away"]]
        pyth_h = hm["runs_scored"] ** 1.83 / (hm["runs_scored"] ** 1.83 + hm["runs_allowed"] ** 1.83)
        pyth_a = aw["runs_scored"] ** 1.83 / (aw["runs_scored"] ** 1.83 + aw["runs_allowed"] ** 1.83)
        margin = (pyth_h - pyth_a) * 4.2 + 0.24
        tot = 7.8
        mkts = make_standard_markets(margin, tot, sd_margin=2.95, sd_total=3.10, unit="Runs", fixed_spread_abs=1.5)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="baseball", sport_name="Baseball", olbg_id=12,
            competition=f"2026 MLB World Series — {g['description']}", event_type="head_to_head", match_state="upcoming",
            date=g["official_date"], start_utc=g["game_date_utc"], venue=g["venue"],
            home=hm["name"], away=aw["name"],
            home_form=f"{hm['wins']}-{hm['losses']} ({hm['runs_scored']} RS / {hm['runs_allowed']} RA)",
            away_form=f"{aw['wins']}-{aw['losses']} ({aw['runs_scored']} RS / {aw['runs_allowed']} RA)",
            markets=mkts, official_source="MLB StatsAPI Official Gameday",
            official_url=g["human_url"], olbg_url="https://www.olbg.com/betting-tips/Baseball/12",
        ))

    # 6. Handball — EHF Champions League Men Round 5 (5 matches on Oct 22)
    ehf_t = inp["ehf_teams"]
    for g in inp["ehf_fixtures"]:
        hm, aw = ehf_t[g["home"]], ehf_t[g["away"]]
        h_gd = (hm["gf"] - hm["ga"]) / hm["gp"]
        a_gd = (aw["gf"] - aw["ga"]) / aw["gp"]
        margin = 0.44 * (h_gd - a_gd) + 1.7
        tot = 0.5 * ((hm["gf"] + hm["ga"]) / hm["gp"] + (aw["gf"] + aw["ga"]) / aw["gp"])
        mkts = make_standard_markets(margin, tot, sd_margin=5.1, sd_total=5.4, unit="Goals", draw_band=0.42)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="handball", sport_name="Handball", olbg_id=20,
            competition=f"EHF Champions League Men 2026-27 — Group {hm['group']} Round 5",
            event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["start_utc"], venue="Official EHF Arena",
            home=hm["name"], away=aw["name"],
            home_form=f"Group {hm['group']}: {hm['w']}-{hm['d']}-{hm['l']} ({hm['gf']}:{hm['ga']}, {hm['pts']} pts)",
            away_form=f"Group {aw['group']}: {aw['w']}-{aw['d']}-{aw['l']} ({aw['gf']}:{aw['ga']}, {aw['pts']} pts)",
            markets=mkts, official_source="EHF Champions League Official Match Details",
            official_url=g["detail_url"], olbg_url="https://www.olbg.com/betting-tips/Handball/20",
        ))

    # 7. Volleyball — Italian SuperLega Credem Banca Round 2 (6 matches on Oct 25)
    vb_t = inp["superlega_teams"]
    for g in inp["superlega_fixtures"]:
        hm, aw = vb_t[g["home"]], vb_t[g["away"]]
        h_pr = hm["pf"] / max(1, hm["pa"])
        a_pr = aw["pf"] / max(1, aw["pa"])
        club_prior = {"trentino": 6.5, "perugia": 7.5, "piacenza": 4.5, "civitanova": 4.2, "verona": 2.0, "milano": 1.8, "modena": 1.2, "monza": 0.5, "cisterna": 0.8}
        margin = (club_prior.get(g["home"], 0.0) - club_prior.get(g["away"], 0.0)) + 8.0 * (h_pr - a_pr) + 3.2
        tot = 179.5 - 1.1 * abs(margin)
        mkts = make_standard_markets(margin, tot, sd_margin=11.5, sd_total=15.0, unit="Points")
        rows.append(finalize_match_row(
            row_id=g["id"], sport="volleyball", sport_name="Volleyball", olbg_id=21,
            competition="Italian SuperLega Credem Banca 2026-27 — Round 2", event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["time"], venue=g["venue"],
            home=hm["name"], away=aw["name"],
            home_form=f"R1: {hm['w']}-{hm['l']} (Sets {hm['sw']}:{hm['sl']}, Points {hm['pf']}:{hm['pa']})",
            away_form=f"R1: {aw['w']}-{aw['l']} (Sets {aw['sw']}:{aw['sl']}, Points {aw['pf']}:{aw['pa']})",
            markets=mkts, official_source="Lega Pallavolo Serie A Official Calendar & Standings",
            official_url="https://www.legavolley.it/classifica/?IdCampionato=999",
            olbg_url="https://www.olbg.com/betting-tips/Volleyball/21",
        ))

    # 8. Aussie Rules — Official 2026 NAB AFLW Round 11 (9 matches Oct 23-25)
    afl_t = inp["aflw_teams"]
    for g in inp["aflw_fixtures"]:
        hm, aw = afl_t[g["home"]], afl_t[g["away"]]
        margin = 0.22 * (hm["pct"] - aw["pct"]) + 0.55 * (hm["pts"] - aw["pts"]) + 3.5
        tot = 79.5 + 0.08 * (hm["pct"] + aw["pct"] - 200.0)
        mkts = make_standard_markets(margin, tot, sd_margin=18.5, sd_total=15.5, unit="Points")
        rows.append(finalize_match_row(
            row_id=g["id"], sport="aussie-rules", sport_name="Aussie Rules", olbg_id=22,
            competition="2026 NAB AFLW Premiership — Round 11", event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["start_utc"], venue=g["venue"],
            home=hm["name"], away=aw["name"],
            home_form=f"Ladder #{hm['rank']} ({hm['pts']} pts, {hm['pct']:.1f}% — {hm['stars']})",
            away_form=f"Ladder #{aw['rank']} ({aw['pts']} pts, {aw['pct']:.1f}% — {aw['stars']})",
            markets=mkts, official_source="AFL.com.au Official AFLW Round 11 Teams & Ladder",
            official_url="https://www.afl.com.au/aflw/news/1634432/aflw-teams-dees-make-hore-call-freo-star-returns-another-pies-blow",
            olbg_url="https://www.olbg.com/betting-tips/Aussie_Rules/22",
        ))

    # 9. eSports — LoL Worlds 2026 Swiss Stage Round 1 (8 Bo1 matches on Oct 23)
    for g in inp["lol_fixtures"]:
        elo_diff = g["home_elo"] - g["away_elo"]
        p_home = 1.0 / (1.0 + 10.0 ** (-elo_diff / 270.0))
        kill_margin = elo_diff / 28.0
        mkts = make_standard_markets(kill_margin, 28.8, sd_margin=7.8, sd_total=6.5, unit="Kills", p_home_override=p_home)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="esports", sport_name="eSports", olbg_id=23,
            competition="2026 LoL World Championship — Swiss Stage Round 1 (Bo1)",
            event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["start_utc"], venue="Credit Union of Texas Event Center, Allen, TX",
            home=g["home"], away=g["away"],
            home_form=g["home_form"], away_form=g["away_form"],
            markets=mkts, official_source="Riot Games LoL Esports Worlds 2026 Primer",
            official_url="https://lolesports.com/en-US/news/worlds-2026-primer",
            olbg_url="https://www.olbg.com/betting-tips/eSports/23",
        ))

    # 10. Darts — Exact negative-binomial Race-to-6-legs model (Best of 11)
    pdc_p = inp["pdc_players"]
    for g in inp["darts_fixtures"]:
        p1, p2 = pdc_p[g["p1"]], pdc_p[g["p2"]]
        s1 = 0.16 * math.log(max(30000, p1["prize_gbp"])) - 0.11 * math.log(p1["rank"])
        s2 = 0.16 * math.log(max(30000, p2["prize_gbp"])) - 0.11 * math.log(p2["rank"])
        q_leg = clamp(1.0 / (1.0 + math.exp(-(s1 - s2))), 0.34, 0.66)
        mkts = make_race_to_w_markets(q_leg, target_wins=6, unit="Legs", total_line=9.5)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="darts", sport_name="Darts", olbg_id=15,
            competition="2026 PDC Machineseeker European Championship — Round 1 (Best of 11)",
            event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["time"], venue="Westfalenhalle, Dortmund",
            home=g["p1"], away=g["p2"],
            home_form=f"PDC World #{p1['rank']} (£{p1['prize_gbp']:,})" + (f" | {g['note']}" if g.get("note") else ""),
            away_form=f"PDC World #{p2['rank']} (£{p2['prize_gbp']:,})",
            markets=mkts, official_source="PDC Official Dortmund Schedule & Order of Merit",
            official_url=g["official_url"], olbg_url=g["olbg_url"],
        ))

    # 11. Snooker — Exact negative-binomial Race-to-4-frames model (Best of 7)
    for g in inp["snooker_fixtures"]:
        s1 = 0.19 * math.log(g["p1_prize_gbp"]) - 0.13 * math.log(g["p1_rank"])
        s2 = 0.19 * math.log(g["p2_prize_gbp"]) - 0.13 * math.log(g["p2_rank"])
        q_frame = clamp(1.0 / (1.0 + math.exp(-(s1 - s2))), 0.32, 0.68)
        mkts = make_race_to_w_markets(q_frame, target_wins=4, unit="Frames", total_line=5.5)
        extra1 = f" | {g['p1_extra']}" if g.get("p1_extra") else ""
        rows.append(finalize_match_row(
            row_id=g["id"], sport="snooker", sport_name="Snooker", olbg_id=8,
            competition="2026 BetVictor Northern Ireland Open — Last 16 (Best of 7)",
            event_type="head_to_head", match_state=g["match_state"],
            date=g["date"], start_utc=g["start_utc"], venue="Waterfront Hall, Belfast",
            home=g["p1"], away=g["p2"],
            home_form=f"WST World #{g['p1_rank']} (£{g['p1_prize_gbp']:,}){extra1}",
            away_form=f"WST World #{g['p2_rank']} (£{g['p2_prize_gbp']:,})",
            markets=mkts, official_source="World Snooker Tour Johnstone's Paint World Rankings",
            official_url=g["official_url"], olbg_url=g["olbg_url"],
            state_note=g.get("note", ""),
        ))

    # 12. Tennis — Verified ATP (Almaty, Brussels, Lyon) & WTA (Osaka, Ningbo)
    for g in inp["tennis_fixtures"]:
        log_gap = math.log(g["p2_rank"]) - math.log(g["p1_rank"])
        p_home = clamp(1.0 / (1.0 + math.exp(-0.76 * log_gap)), 0.12, 0.88)
        game_margin = (p_home - 0.5) * 9.6
        tot_games = 22.8 if abs(log_gap) < 1.1 else 21.3
        mkts = make_standard_markets(game_margin, tot_games, sd_margin=4.35, sd_total=3.6, unit="Games", p_home_override=p_home)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="tennis", sport_name="Tennis", olbg_id=3,
            competition=g["competition"], event_type="head_to_head", match_state=g["match_state"],
            date=g["date"], start_utc=g["start_utc"], venue=g["venue"],
            home=g["p1"], away=g["p2"],
            home_form=g["p1_form"], away_form=g["p2_form"],
            markets=mkts, official_source=f"{g['tour']} Official Tournament Daily Schedule",
            official_url=g["official_url"], olbg_url=g["olbg_url"],
            state_note=g.get("result_note", ""),
        ))

    # 13. Cricket — Verified International ODIs + Unverified Domestic Blank Row
    for g in inp["cricket_fixtures"]:
        if g["match_state"] == "unverified_blank":
            rows.append(finalize_match_row(
                row_id=g["id"], sport="cricket", sport_name="Cricket", olbg_id=7,
                competition=g["competition"], event_type="head_to_head", match_state="unverified_blank",
                date=g["date"], start_utc="—", venue="—",
                home=g["home"], away=g["away"], home_form="—", away_form="—",
                markets=None, official_source="ICC / CSA Fixture Verification",
                official_url=g["official_url"], olbg_url=g["olbg_url"],
                state_note=g["flag_reason"],
            ))
        else:
            rgap = g["home_rating"] - g["away_rating"]
            p_home = clamp(1.0 / (1.0 + math.exp(-0.062 * rgap)), 0.08, 0.92)
            run_margin = rgap * 1.95
            mkts = make_standard_markets(run_margin, 506.0, sd_margin=42.0, sd_total=48.0, unit="Runs", p_home_override=p_home)
            rows.append(finalize_match_row(
                row_id=g["id"], sport="cricket", sport_name="Cricket", olbg_id=7,
                competition=g["competition"], event_type="head_to_head", match_state=g["match_state"],
                date=g["date"], start_utc=g["start_utc"], venue=g["venue"],
                home=g["home"], away=g["away"], home_form=g["home_form"], away_form=g["away_form"],
                markets=mkts, official_source="ICC Official ODI Tournament Hub",
                official_url=g["official_url"], olbg_url=g["olbg_url"],
                state_note=g.get("result_note", ""),
            ))

    # 14. Gaelic Football — Cork & Galway County SFC Finals
    for g in inp["gaa_fixtures"]:
        margin = (g["home_rating"] - g["away_rating"]) * 0.56
        mkts = make_standard_markets(margin, 31.8, sd_margin=4.8, sd_total=4.6, unit="Points", draw_band=0.45)
        rows.append(finalize_match_row(
            row_id=g["id"], sport="gaelic-football", sport_name="Gaelic Football", olbg_id=25,
            competition=g["competition"], event_type="head_to_head", match_state="upcoming",
            date=g["date"], start_utc=g["start_utc"], venue=g["venue"],
            home=g["home"], away=g["away"], home_form=g["home_form"], away_form=g["away_form"],
            markets=mkts, official_source="Munster GAA / GAA.ie County Finals",
            official_url=g["official_url"], olbg_url=g["olbg_url"],
        ))

    # 15-17. Outright Field Events (Golf, Motor Racing, Greyhounds)
    for ev in inp["outright_events"]:
        p_fav = ev["fav_prob"]
        mkts = {
            "win_match": {
                "type": "outright-leader-vs-field",
                "home": quote_prob(p_fav),
                "away": quote_prob(1.0 - p_fav),
            },
            "handicap": None,
            "total": None,
            "alt_handicap_in_window": None,
        }
        rows.append(finalize_match_row(
            row_id=ev["id"], sport=ev["sport"], sport_name=ev["sport_name"], olbg_id=ev["olbg_id"],
            competition=ev["competition"], event_type="outright_field", match_state=ev["match_state"],
            date=ev["date"], start_utc=ev["start_utc"], venue=ev["venue"],
            home=ev["home"], away=ev["away"], home_form=ev["home_form"], away_form=ev["away_form"],
            markets=mkts, official_source=ev["official_source"],
            official_url=ev["official_url"], olbg_url=ev["olbg_url"],
            state_note="Round 1 underway on Oct 22" if ev["match_state"] == "in_play" else "",
        ))

    for u in inp["unverified_rows"]:
        rows.append(finalize_match_row(
            row_id=u["id"], sport=u["sport"], sport_name=u["sport_name"], olbg_id=u["olbg_id"],
            competition=u["competition"], event_type="head_to_head", match_state="unverified_blank",
            date=u["date"], start_utc="—", venue="—",
            home=u["home"], away=u["away"], home_form="—", away_form="—",
            markets=None, official_source="Official Governing Body / OLBG Hub Audit",
            official_url=u["official_url"], olbg_url=u["olbg_url"],
            state_note=u["reason"],
        ))

    return rows


def build_predictions(matches: list[dict]) -> list[dict]:
    by_id = {m["id"]: m for m in matches}
    picks: list[dict] = []

    for mid, spec in PROSE_CATALOG.items():
        m = by_id.get(mid)
        if not m or m["match_state"] != "upcoming" or not m["markets"]:
            continue

        candidates: list[tuple[str, str, dict]] = []
        wm = m["markets"]["win_match"]
        for side_k, team_name in [("home", m["home"]), ("away", m["away"])]:
            q = wm[side_k]
            if HIGH_MIN_PROB <= q["prob_exact"] <= HIGH_MAX_PROB:
                candidates.append(("Win Match", f"{team_name} to Win", q))

        if m["markets"].get("alt_handicap_in_window"):
            ah = m["markets"]["alt_handicap_in_window"]
            q = ah["quote"]
            tname = m["home"] if ah["favored_side"] == "home" else m["away"]
            if HIGH_MIN_PROB <= q["prob_exact"] <= HIGH_MAX_PROB:
                candidates.append((f"Handicap ({ah['unit']})", f"{tname} {ah['line']:+.1f} {ah['unit']}", q))

        if m["markets"].get("handicap"):
            hc = m["markets"]["handicap"]
            for side_k, tname, line_v in [
                ("home", m["home"], hc["line_home"]),
                ("away", m["away"], hc["line_away"]),
            ]:
                q = hc[side_k]
                if HIGH_MIN_PROB <= q["prob_exact"] <= HIGH_MAX_PROB:
                    candidates.append((f"Handicap ({hc['unit']})", f"{tname} {line_v:+.1f} {hc['unit']}", q))

        if not candidates:
            continue

        mkt_name, sel_label, q = candidates[0]
        prose = spec["prose"].strip()
        wc = len(prose.split())
        assert wc >= 30, f"Pick {mid} prose under 30 words ({wc})"
        assert HIGH_MIN_PROB <= q["prob_exact"] <= HIGH_MAX_PROB, f"Pick {mid} prob {q['prob_exact']} outside [0.70, 5/7]"
        assert 1.40 <= q["decimal_exact"] <= 101.00, f"Pick {mid} decimal {q['decimal_exact']} outside [1.40, 101.00]"
        assert -250 <= q["american"] <= 10000, f"Pick {mid} american {q['american']} outside [-250, +10000]"

        picks.append({
            "pick_id": f"beacon-pick-{mid}",
            "match_id": mid,
            "sport": m["sport"],
            "sport_name": m["sport_name"],
            "olbg_id": m["olbg_id"],
            "competition": m["competition"],
            "date": m["date"],
            "start_utc": m["start_utc"],
            "venue": m["venue"],
            "home": m["home"],
            "away": m["away"],
            "market": mkt_name,
            "selection": sel_label,
            "confidence": "high",
            "model_prob": q["prob"],
            "model_prob_exact": q["prob_exact"],
            "fair_decimal": q["decimal"],
            "fair_decimal_exact": q["decimal_exact"],
            "fair_american": q["american"],
            "fair_american_str": q["american_str"],
            "verified_players": spec["players"],
            "word_count": wc,
            "prediction": prose,
            "official_source": m["official_source"],
            "official_url": m["official_url"],
            "olbg_url": m["olbg_url"],
        })

    return picks


def build_flagged(matches: list[dict], audit_findings: list[dict]) -> list[dict]:
    items: list[dict] = []

    for f in audit_findings:
        items.append({
            "flag_id": f["id"],
            "category": "repo_audit_irregularity",
            "severity": f["severity"],
            "sport": f["layer"],
            "subject": f["affected"],
            "status": "remediated_in_beacon",
            "detail": f"{f['summary']} Resolution: {f['beacon_fix']}",
            "official_url": f["official_url"],
            "olbg_url": "https://www.olbg.com/sitemap-betting-tips.xml",
        })

    items.append({
        "flag_id": "INTRA-PDC-HUMPHRIES",
        "category": "intraday_withdrawal",
        "severity": "critical",
        "sport": "darts",
        "subject": "Luke Humphries vs Ryan Searle (voided -> Kim Huybrechts vs Ryan Searle)",
        "status": "updated_live",
        "detail": "World No. 2 Luke Humphries officially withdrew on 2026-10-22 with gastroenteritis and was replaced by Kim Huybrechts (#55, Euro Tour #33); voided from pre-match Humphries picks.",
        "official_url": "https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship",
        "olbg_url": "https://www.olbg.com/betting-tips/Darts/15",
    })

    for m in matches:
        if m["match_state"] in ("completed", "in_play"):
            items.append({
                "flag_id": f"STATE-{m['id']}",
                "category": f"intraday_{m['match_state']}",
                "severity": "info",
                "sport": m["sport"],
                "subject": f"{m['home']} vs {m['away']} ({m['competition']})",
                "status": m["match_state"],
                "detail": m["winner_pick"]["confidence_note"],
                "official_url": m["official_url"],
                "olbg_url": m["olbg_url"],
            })
        elif m["match_state"] == "unverified_blank":
            items.append({
                "flag_id": f"UNVERIFIED-{m['id']}",
                "category": "unverified_left_blank",
                "severity": "medium",
                "sport": m["sport"],
                "subject": f"{m['home']} vs {m['away']} ({m['competition']})",
                "status": "blank_unverified",
                "detail": m["winner_pick"]["confidence_note"],
                "official_url": m["official_url"],
                "olbg_url": m["olbg_url"],
            })

    return items


def main() -> None:
    inp = json.loads((BEACON_DIR / "inputs.json").read_text())
    audit = json.loads((BEACON_DIR / "repo_audit.json").read_text())["findings"]
    sports_meta = json.loads((BEACON_DIR / "sports.json").read_text())
    sources_meta = json.loads((BEACON_DIR / "sources.json").read_text())

    matches = build_all_matches(inp)
    predictions = build_predictions(matches)
    flagged = build_flagged(matches, audit)

    covered_sports = sorted({m["sport"] for m in matches})
    assert len(covered_sports) == 17, f"Expected 17 covered sports, got {len(covered_sports)}: {covered_sports}"

    originated = [m for m in matches if m["match_state"] != "unverified_blank"]
    upcoming = [m for m in matches if m["match_state"] == "upcoming"]
    in_play = [m for m in matches if m["match_state"] == "in_play"]
    completed = [m for m in matches if m["match_state"] == "completed"]
    blanks = [m for m in matches if m["match_state"] == "unverified_blank"]

    win_conf_counts = {"high": 0, "medium": 0, "low": 0, "unverified": 0}
    for m in matches:
        c = m["winner_pick"]["confidence"]
        win_conf_counts[c] = win_conf_counts.get(c, 0) + 1

    per_sport = {}
    for sp in sports_meta["eligible"]:
        slug = sp["slug"]
        sp_rows = [m for m in matches if m["sport"] == slug]
        sp_orig = [m for m in sp_rows if m["match_state"] != "unverified_blank"]
        sp_picks = [p for p in predictions if p["sport"] == slug]
        per_sport[slug] = {
            "olbg_id": sp["olbg_id"],
            "name": sp["name"],
            "total_rows": len(sp_rows),
            "originated_rows": len(sp_orig),
            "upcoming_rows": sum(1 for m in sp_rows if m["match_state"] == "upcoming"),
            "live_or_done_rows": sum(1 for m in sp_rows if m["match_state"] in ("in_play", "completed")),
            "unverified_blank_rows": sum(1 for m in sp_rows if m["match_state"] == "unverified_blank"),
            "high_picks": len(sp_picks),
            "official_url": sp["official_url"],
            "olbg_url": sp["olbg_url"],
        }

    summary = {
        "snapshot_utc": inp["snapshot_utc"],
        "session": inp["session"],
        "eligible_sports": 17,
        "covered_sports": len(covered_sports),
        "excluded_sports": sports_meta["excluded_count"],
        "total_rows": len(matches),
        "originated_rows": len(originated),
        "head_to_head_originated": sum(1 for m in originated if m["event_type"] == "head_to_head"),
        "outright_field_originated": sum(1 for m in originated if m["event_type"] == "outright_field"),
        "upcoming_rows": len(upcoming),
        "in_play_rows": len(in_play),
        "completed_rows": len(completed),
        "unverified_blank_rows": len(blanks),
        "winner_confidence_counts": win_conf_counts,
        "high_confidence_picks": len(predictions),
        "high_pick_sports": len({p["sport"] for p in predictions}),
        "high_pick_min_words": min(p["word_count"] for p in predictions) if predictions else 0,
        "high_pick_prob_min": min(p["model_prob_exact"] for p in predictions) if predictions else 0.0,
        "high_pick_prob_max": max(p["model_prob_exact"] for p in predictions) if predictions else 0.0,
        "flagged_total": len(flagged),
        "repo_audit_findings": len(audit),
        "verified_sources": sources_meta["verified_count"],
        "per_sport": per_sport,
    }

    (BEACON_DIR / "matches.json").write_text(json.dumps({"snapshot_utc": inp["snapshot_utc"], "count": len(matches), "matches": matches}, indent=2) + "\n")
    (BEACON_DIR / "predictions.json").write_text(json.dumps({"snapshot_utc": inp["snapshot_utc"], "count": len(predictions), "predictions": predictions}, indent=2) + "\n")
    (BEACON_DIR / "flagged.json").write_text(json.dumps({"snapshot_utc": inp["snapshot_utc"], "count": len(flagged), "flagged": flagged}, indent=2) + "\n")
    (BEACON_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"beacon_model: {len(matches)} total rows ({len(originated)} originated, {len(blanks)} blank) across {len(covered_sports)}/17 sports; "
          f"{len(predictions)} strict high-confidence picks across {summary['high_pick_sports']} sports; {len(flagged)} flagged items")


if __name__ == "__main__":
    main()
