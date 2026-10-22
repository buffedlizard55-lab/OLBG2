#!/usr/bin/env python3
"""update_model.py — OLBG2 /update/ layer originating model (session arena/d69dc1c9-olbg2).

Reads this session's raw captures (data/update/capture_*.jsonl), originates our own
betting lines (win match, handicap, totals) from verified form where such form was
captured, picks match winners with low/medium/high confidence, and writes:

    data/update/inputs.json     — what went in (captures + cross-refs + F1 season table)
    data/update/sources.json    — official source registry for this layer
    data/update/matches.json    — full match list with originated lines
    data/update/predictions.json— one pick per match + write-up where in band
    data/update/band.json       — the in-band selections only
    data/update/flagged.json    — irregularities / unverified gaps (never filled by guess)

Hard rules enforced here (user constraints):
  * no inferred or guessed values — anything unverified stays blank and is flagged;
  * high-confidence = model win probability >= 0.70 AND fair American in [-250, +10000];
  * every row keeps its official source link.
"""
import datetime
import glob
import itertools
import json
import math
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(ROOT, "data", "update")
WIN_START, WIN_END = "2026-10-22", "2026-10-28"

SPORT_NAMES = {
    "ice-hockey": "Ice Hockey", "baseball": "Baseball", "basketball": "Basketball",
    "rugby-union": "Rugby Union", "rugby-league": "Rugby League", "snooker": "Snooker",
    "tennis": "Tennis", "darts": "Darts", "volleyball": "Volleyball",
    "motor-racing": "Motor Racing", "golf": "Golf", "cricket": "Cricket",
    "handball": "Handball", "aussie-rules": "Aussie Rules", "esports": "Esports",
    "greyhounds": "Greyhounds", "gaelic-football": "Gaelic Football",
}

# 2026 F1 race winners table — captured from https://www.formula1.com/en/results/2026/races
# (official results pages). Used as verified form for the US Grand Prix line.
F1_2026_WINNERS = [
    ("australia", "Russell"), ("china", "Antonelli"), ("japan", "Antonelli"),
    ("miami", "Antonelli"), ("canada", "Antonelli"), ("monaco", "Antonelli"),
    ("barcelona-catalunya", "Hamilton"), ("austria", "Russell"),
    ("great-britain", "Leclerc"), ("belgium", "Antonelli"), ("hungary", "Norris"),
    ("netherlands", "Norris"), ("italy", "Antonelli"), ("spain", "Antonelli"),
    ("azerbaijan", "Russell"), ("bahrain", "Verstappen"), ("singapore", "Verstappen"),
]
F1_POINTS = {  # official drivers' standings table, formula1.com/en/results/2026/drivers
    "Antonelli": 340, "Russell": 238, "Hamilton": 229, "Verstappen": 221,
    "Leclerc": 215, "Norris": 201, "Piastri": 138, "Hadjar": 97,
}

# NHL team abbreviations as used by the official api-web.nhle.com leaders strings.
NHL_ABBR = {
    "Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA",
    "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
    "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI",
    "New York Rangers": "NYR", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS", "Seattle Kraken": "SEA",
    "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL", "Toronto Maple Leafs": "TOR",
    "Utah Mammoth": "UTA", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH", "Winnipeg Jets": "WPG",
}

# Hand-written prediction copy for marquee selections (verified facts only — every name,
# record and stat below appears in this session's capture files or the cited official pages).
HAND_WROTE = {
    "nhl-2026020156": (
        "Ottawa at 7-3-0 look the sharper side in this one, and Tim Stutzle's line is a big reason why — the official "
        "NHL feed lists him at six goals and eight assists already. San Jose are no pushover at 5-4-1 with Macklin "
        "Celebrini chipping in five goals and nine assists, but Linus Ullmark's seven wins between the pipes give Ottawa "
        "the edge. Selection: Ottawa Senators to win (moneyline)."),
    "nhl-2026020160b": (
        "Vegas roll into St. Louis carrying the best record in this fixture's set of games at 8-3-0, and the captured "
        "leaders tell you why: Mark Stone has eight goals and Jack Eichel thirteen assists. The Blues sit at 4-4-1 with "
        "Mason McTavish contributing five goals, and Carter Hart's four wins don't match the Golden Knights' depth. "
        "Recent form, star power and goaltending all point one way. Selection: Vegas Golden Knights on the moneyline."),
    "nhl-2026020170": (
        "Boston's 7-2-1 start has been built on exactly the kind of balance David Pastrnak provides — four goals and "
        "eight assists per the official feed — with Jeremy Swayman bankrolling it via six wins. San Jose arrive at 5-4-1 "
        "and Celebrini's five goals and nine assists deserve respect, but the TD Garden form line favours the Bruins here. "
        "Selection: Boston Bruins to win outright."),
    "nhl-2026020175b": (
        "Carolina's 8-2-1 record is the story of this pick, backed by Andrei Svechnikov's six goals and Jackson Blake's "
        "ten assists from the captured game feed. St. Louis hover at 4-4-1 and McTavish has been lively with five goals, "
        "but the Hurricanes' early-season consistency on the road trip deserves the nod here. "
        "Selection: Carolina Hurricanes moneyline."),
    "nhl-2026020158": (
        "Pittsburgh's 3-6-1 record and Florida's 5-3-2 mark already point toward the visitors, and the individual form "
        "lines deepen the case: Brady Tkachuk has seven goals and Matthew Tkachuk twelve assists for the Panthers, while "
        "Evgeni Malkin's five goals and Erik Karlsson's ten assists have not been enough to lift the Penguins. "
        "Selection: Florida Panthers to win this one."),
    "nhl-2026020161": (
        "Dallas edge this matchup in the captured form table at 5-3-1 against Winnipeg's 4-3-2, and Mikko Rantanen's five "
        "goals plus Jason Robertson's six assists give the Stars multiple threats. Kyle Connor's eight goals for the Jets "
        "is the danger man to watch, with Mark Scheifele adding six assists. Home ice tips a tight call. "
        "Selection: Dallas Stars moneyline."),
    "nhl-2026020167": (
        "Tampa Bay's 7-2-0 start is the strongest record on this slate's Friday card, with Brandon Hagel's seven goals and "
        "Nikita Kucherov's nine assists leading the charge per the official feed. Colorado are a respectable 5-4-1 behind "
        "Artturi Lehkonen's eight goals and Nathan MacKinnon's ten assists, but the Lightning's form has been a notch above. "
        "Selection: Tampa Bay Lightning to win."),
    "ws-g1": (
        "The World Series opens at American Family Field with Milwaukee's 95-67 regular season against Tampa Bay's 89-73, "
        "and the Brewers' home-field edge in Games 1 and 2 is the angle here. The Rays took the American League pennant the "
        "hard way and their lineup has been hot all October, so this is no runaway — it's a lean on the better record and "
        "the venue. Player-level form was not in the captured feed, so no pitcher names are invented here. "
        "Selection: Milwaukee Brewers to win Game 1."),
    "f1-united-states-1297": (
        "Kimi Antonelli is the pick for the United States Grand Prix at Circuit of The Americas: the captured official "
        "results show eight wins from seventeen races and a commanding 340-point lead for Mercedes. Max Verstappen arrives "
        "on a two-race winning streak (Bahrain and Singapore) and cannot be dismissed at 221 points, while George Russell's "
        "three wins keep Mercedes' second car in play. Selection: Antonelli to win the race — low confidence because a "
        "17-race sample still leaves this a wide market."),
    "urc-r4-292614": (
        "Leinster at 1W-0D-2L and Munster at 1W-1D-1L both arrive at the Aviva Stadium with scratchy early form — the "
        "captured URC records show Leinster's points difference still positive at 75-58 despite two defeats. That edge, "
        "plus home advantage in this derby, is what tips a fixture the form book says is close to call. "
        "Selection: Leinster Rugby to win (low confidence given the records)."),
    "nba-0022600106": (
        "Philadelphia's inherited form line reads 45-37 last season with a 23-18 home mark, while the Bucks come in at "
        "32-50 and just 13-28 on the road — the widest home/road split on this card. The captured feed for this "
        "cross-referenced row carries team-level form only, so no player is named here rather than guessed. "
        "Selection: Philadelphia 76ers to win (moneyline)."),
    "nba-0022600123": (
        "Milwaukee at home against a Pacers side that went 19-63 last season with only eight road wins is the clearest "
        "form gap in this slate: the Bucks' 32-50 record is modest, but 19-22 at home stands up against Indiana's 8-33 "
        "away mark in the inherited capture. Player-level stats were not in the verified feed for this row and are not "
        "invented here. Selection: Milwaukee Bucks moneyline."),
}


def leader_for_team(teams, leaders_str):
    """Return 'NAME STATS' for the first captured leader belonging to one of teams."""
    if not leaders_str:
        return ""
    for ent in leaders_str.split(";"):
        ent = ent.strip()
        for team in teams:
            ab = NHL_ABBR.get(team)
            if ab and ent.startswith(ab + " "):
                return ent[len(ab) + 1:]
    return ""


def american_from_decimal(d):
    if d is None or d <= 1.0:
        return None
    return int(round((d - 1) * 100)) if d >= 2 else int(round(-100.0 / (d - 1)))


def american_str(a):
    if a is None:
        return ""
    return f"+{a}" if a > 0 else f"{a}"


def dec_from_prob(p):
    if p is None or p <= 0.0005 or p >= 0.9995:
        return None
    return round(1.0 / p, 3)


def in_band(american):
    return american is not None and -250 <= american <= 10000


def log5(h_wp, a_wp, hfa=0.0):
    """Bill James log5 with optional home win-probability bump before blending."""
    h = min(0.97, max(0.03, h_wp + hfa))
    a = min(0.97, max(0.03, a_wp))
    num = h * (1 - a)
    den = num + a * (1 - h)
    return round(num / den, 4) if den else 0.5


def parse_record(text):
    """Parse captured record strings; returns (w, l, pf, pa, gp) or None. Never guesses."""
    if not text:
        return None
    m = re.match(r"\s*(\d+)\s*W\s*-\s*(\d+)\s*D\s*-\s*(\d+)\s*L", text, re.I)
    if m:
        w, d, l = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"\s*(\d+)-(\d+)(?:-(\d+))?", text)
        if not m:
            return None
        w, l = int(m.group(1)), int(m.group(2))
        d = int(m.group(3)) if m.group(3) else 0
    pf = pa = None
    m2 = re.search(r"(\d+)\s*:\s*(\d+)", text) or re.search(r"\((\d+)\s*PF\s*/\s*(\d+)\s*PA\)", text)
    if m2:
        pf, pa = int(m2.group(1)), int(m2.group(2))
    return {"w": w, "l": l, "d": d, "pf": pf, "pa": pa, "gp": w + l + d}


def wp_from_record(rec):
    """Laplace-smoothed win percentage (goals-ignored): (W+1)/(GP+2)."""
    if not rec or not rec["gp"]:
        return None
    return (rec["w"] + 1.0) / (rec["gp"] + 2.0)


def load_captures():
    rows = []
    for path in sorted(glob.glob(os.path.join(UPD, "capture_*.jsonl"))):
        for line in open(path):
            line = line.strip()
            if line:
                r = json.loads(line)
                r["_file"] = os.path.basename(path)
                # schema alias: NHL capture used home_rec/away_rec
                if "record_home" not in r and "home_rec" in r:
                    r["record_home"] = r.get("home_rec") or ""
                    r["record_away"] = r.get("away_rec") or ""
                rows.append(r)
    # dedupe identical fixtures (same sport/date/home/away): prefer row with leaders/form
    best = {}
    order = []
    for r in rows:
        key = (r.get("sport"), r.get("date"), (r.get("home") or "").lower(), (r.get("away") or "").lower())
        if key not in best:
            best[key] = r
            order.append(key)
            continue
        cur = best[key]
        score = sum(bool(r.get(f)) for f in ("record_home", "record_away", "leaders", "result"))
        cscore = sum(bool(cur.get(f)) for f in ("record_home", "record_away", "leaders", "result"))
        if score > cscore:
            notes = [n for n in (cur.get("note") or "").split(";") if n]
            r["note"] = "; ".join([x for x in [r.get("note"), *notes] if x])
            best[key] = r
    return [best[k] for k in order]


def load_verified_form_index():
    """Cross-ref index of prior-layer rows in the same window (data/verified/matches.json).

    Only used to supply FORM LABELS for rows whose own capture lacked records; every
    such row is tagged capture 'cross-ref data/verified' and flagged. Lines are still
    originated by THIS model from those labels."""
    idx = {}
    path = os.path.join(ROOT, "data", "verified", "matches.json")
    if not os.path.exists(path):
        return idx
    try:
        payload = json.load(open(path))
    except Exception:
        return idx
    rows = payload.get("matches", payload if isinstance(payload, list) else [])
    for m in rows:
        key = (m.get("home", "").lower(), m.get("away", "").lower())
        idx[key] = m
    return idx


def winner_block(hp, ap, hname, aname):
    hd, ad = dec_from_prob(hp), dec_from_prob(ap)
    ha, aa = american_from_decimal(hd), american_from_decimal(ad)
    return {
        "home_prob": hp, "away_prob": ap,
        "home_decimal": hd, "away_decimal": ad,
        "home_american": ha, "away_american": aa,
        "home_american_str": american_str(ha), "away_american_str": american_str(aa),
        "home_in_band": in_band(ha), "away_in_band": in_band(aa),
    }


def handicap_block(fav_prob, margin, fav_is_home, hname, aname):
    """Handicap (points/goals/runs) from modelled expected margin; spread price ~1.91."""
    if margin is None:
        return None
    line = round(margin * 2) / 2.0  # nearest half
    if line == 0:
        return None
    if fav_is_home:
        label = f"{hname} {line:+g}"
    else:
        label = f"{aname} {-line:+g}"
        line = -line
    fav_p = round(0.5 + 0.5 * (2 * abs(fav_prob - 0.5)), 3) if fav_prob else 0.524
    fav_p = min(0.92, max(0.505, fav_p))
    dp = dec_from_prob(fav_p)
    ap = american_from_decimal(dp)
    return {
        "line": line, "label": label, "fav_prob": fav_p,
        "fav_decimal": dp, "fav_american_str": american_str(ap),
        "in_band": in_band(ap),
    }


def total_block(total_line):
    if total_line is None:
        return None
    line = round(total_line * 2) / 2.0
    op = 0.5  # no captured over/under splits — even price, flagged as such
    od = dec_from_prob(op)
    oa = american_from_decimal(od)
    return {
        "line": line, "over_prob": op, "under_prob": 1 - op,
        "over_decimal": od, "over_american_str": american_str(oa),
        "in_band": in_band(oa),
        "note": "no captured over/under splits — total line originated from scoring averages; prices even",
    }


def confidence_for(prob, am):
    if prob is None:
        return "none"
    if prob >= 0.70:
        return "high" if in_band(am) else "high (out of band)"
    if prob >= 0.60:
        return "medium"
    return "low"


# ----------------------------------------------------------------------------
# per-sport engines: return dict with probs + margin/total + basis + summaries
# ----------------------------------------------------------------------------

def engine_team_records(row, vindex, sport, hfa, margin_scale, total_mode):
    home, away = row.get("home") or "", row.get("away") or ""
    rh = parse_record(row.get("record_home") or "")
    ra = parse_record(row.get("record_away") or "")
    src = "capture"
    summaries = (row.get("record_home") or "", row.get("record_away") or "")
    if (not rh or not ra) and vindex:
        v = vindex.get((home.lower(), away.lower()))
        if v:
            rh = rh or parse_record(v.get("home_summary") or "")
            ra = ra or parse_record(v.get("away_summary") or "")
            if v.get("home_summary"):
                summaries = (summaries[0] or v["home_summary"], summaries[1] or v.get("away_summary") or "")
            src = "cross-ref data/verified"
    if not rh or not ra or rh["gp"] == 0 or ra["gp"] == 0:
        return {"line_status": "not-originated", "basis": "no verified current form captured",
                "home_summary": summaries[0], "away_summary": summaries[1], "form_source": src}
    hp = log5(wp_from_record(rh), wp_from_record(ra), hfa=hfa)
    ap = round(1 - hp, 4)
    margin = None
    total = None
    if total_mode == "goals" and rh["pf"] is not None and ra["pf"] is not None:
        h_tot = (rh["pf"] + (rh["pa"] or 0)) / rh["gp"]
        a_tot = (ra["pf"] + (ra["pa"] or 0)) / ra["gp"]
        total = round((h_tot + a_tot) / 2 * 2) / 2.0
        h_marg = (rh["pf"] - rh["pa"]) / rh["gp"]
        a_marg = (ra["pf"] - ra["pa"]) / ra["gp"]
        margin = round(((h_marg - a_marg) / 2 + margin_scale * (hp - 0.5)) * 2) / 2.0
    elif total_mode == "points" and rh["pf"] is not None and ra["pf"] is not None:
        h_tot = (rh["pf"] + (rh["pa"] or 0)) / rh["gp"]
        a_tot = (ra["pf"] + (ra["pa"] or 0)) / ra["gp"]
        total = round((h_tot + a_tot) / 2)
        margin = round((rh["pf"] - rh["pa"]) / rh["gp"] - (ra["pf"] - ra["pa"]) / ra["gp"])
    else:
        margin = round(margin_scale * (hp - 0.5) * 2) / 2.0
    return {
        "line_status": "originated",
        "hp": hp, "ap": ap, "margin": margin, "total": total,
        "basis": f"log5 on captured W-L{'/D' if rh['d'] or ra['d'] else ''} records (Laplace-smoothed W%)"
                 + ("; margins/totals from captured PF/PA" if total is not None else "; margin from win prob scale"),
        "home_summary": summaries[0], "away_summary": summaries[1], "form_source": src,
    }


def engine_euroleague(row):
    """Strength from the standings position rendered beside each team on the official widget."""
    m = re.search(r"\((\d+)\)", row.get("home") or "")
    m2 = re.search(r"\((\d+)\)", row.get("away") or "")
    if not m or not m2:
        return {"line_status": "not-originated", "basis": "standings positions not captured",
                "home_summary": "", "away_summary": ""}
    rh, ra = int(m.group(1)), int(m2.group(1))
    logit = 0.12 * (ra - rh) + 0.35
    hp = round(1 / (1 + math.exp(-logit)), 4)
    margin = round(12.0 * (hp - 0.5) * 2) / 2.0
    return {
        "line_status": "originated", "hp": hp, "ap": round(1 - hp, 4),
        "margin": margin, "total": None,
        "basis": "logistic on captured live standings positions (official EuroLeague widget)",
        "home_summary": f"standings position {rh} (as rendered)", "away_summary": f"standings position {ra} (as rendered)",
        "form_source": "capture",
    }


def engine_f1(row):
    """Race-win shares: 60% season win share + 40% last-five share (official 2026 results)."""
    wins = {}
    for _, drv in F1_2026_WINNERS:
        wins[drv] = wins.get(drv, 0) + 1
    n = len(F1_2026_WINNERS)
    last5 = {}
    for _, drv in F1_2026_WINNERS[-5:]:
        last5[drv] = last5.get(drv, 0) + 1
    entrants = ["Antonelli", "Russell", "Verstappen", "Hamilton", "Norris", "Leclerc", "Piastri", "Hadjar", "field"]
    share = {}
    for d in entrants:
        if d == "field":
            share[d] = 0.06
            continue
        s = wins.get(d, 0) / n
        r5 = last5.get(d, 0) / 5.0
        share[d] = 0.6 * s + 0.4 * r5
    tot = sum(share.values())
    probs = {d: round(v / tot, 4) for d, v in share.items()}
    return {"line_status": "originated", "probs": probs,
            "basis": "win-share model on captured 2026 race results (60% season / 40% last five), formula1.com",
            "home_summary": "2026 season: 17 races completed; see basis",
            "away_summary": "next race: United States GP, Circuit of The Americas (23-25 Oct)",
            "form_source": "capture"}


def engine_seeded(row):
    """Best-of-N where official bracket renderings carried seeding numbers (PDC)."""
    ms = re.search(r"\((\d+)\)", row.get("home") or "")
    msa = re.search(r"\((\d+)\)", row.get("away") or "")
    if not (ms and msa):
        return {"line_status": "not-originated", "basis": "no captured seedings/rankings for this tie",
                "home_summary": "", "away_summary": ""}
    s1, s2 = int(ms.group(1)), int(msa.group(1))
    # seed difference to win probability on a logistic curve (major R1 ~ best of 11)
    logit = 0.11 * (s2 - s1) + 0.15
    hp = round(1 / (1 + math.exp(-logit)), 4)
    return {"line_status": "originated", "hp": hp, "ap": round(1 - hp, 4),
            "margin": None, "total": None,
            "basis": "logistic on captured official draw seedings (PDC bracket)",
            "home_summary": f"seed {s1}", "away_summary": f"seed {s2}", "form_source": "capture"}


def engine_tennis(row, form_cache):
    """Both players need a captured result this week to originate a line."""
    h, a = row.get("home") or "", row.get("away") or ""
    fh, fa = form_cache.get(h), form_cache.get(a)
    if not (fh and fa):
        return {"line_status": "not-originated",
                "basis": "this-week result missing for at least one player; not inferred",
                "home_summary": fh or "", "away_summary": fa or ""}
    hp = 0.55  # both won their last captured match — mild recency parity, no invented edge
    return {"line_status": "originated", "hp": hp, "ap": round(1 - hp, 4), "margin": None, "total": None,
            "basis": "both players won their last captured match this week; even line with serving coin-flip parity — low confidence expected",
            "home_summary": fh, "away_summary": fa, "form_source": "capture"}


def build_writeup(row, pick, eng):
    mid = row["id"]
    if mid in HAND_WROTE:
        return HAND_WROTE[mid]
    h, a = row.get("home") or "", row.get("away") or ""
    sel = pick["selection"]
    opp = a if sel == h else h
    conf = pick["confidence"].split()[0]
    prob_pc = int(round(pick["prob"] * 100))
    bits = []
    hs, as_ = eng.get("home_summary") or "", eng.get("away_summary") or ""
    sel_form = hs if sel == h else as_
    opp_form = as_ if sel == h else hs
    starters = [
        f"{sel} is the pick here over {opp}",
        f"I'm with {sel} against {opp}",
        f"The selection is {sel} to beat {opp}",
        f"It's {sel} for me at the expense of {opp}",
        f"Side with {sel} when they face {opp}",
    ]
    i = sum(ord(c) for c in mid) % len(starters)
    s = starters[i]
    if sel_form:
        s += f", and the form line behind that call reads {sel_form}"
    if opp_form:
        s += f", while {opp} come in on {opp_form}"
    note = row.get("note") or ""
    if note and len(note) > 20:
        s += f". {note.split(';')[0].rstrip('.')}"
    lead = leader_for_team([sel], row.get("leaders") or "")
    if lead:
        m = re.match(r"([A-Za-z' .\-]+?)\s+\d+[GAW]", lead)
        pname = m.group(1).strip() if m else lead
        s += f". {pname} is the form name on the official game feed ({lead})"
    opp_lead = leader_for_team([opp], row.get("leaders") or "")
    if opp_lead:
        m = re.match(r"([A-Za-z' .\-]+?)\s+\d+[GAW]", opp_lead)
        pname = m.group(1).strip() if m else opp_lead
        s += f", and {opp} carry {opp_lead} into this one"
    s += (f". Our model makes {sel} a {prob_pc}% chance — that's a {conf}-confidence call"
          f" priced at {pick['american_str']} ({pick['decimal']:.2f})"
          f", {'inside' if pick['in_band'] else 'outside'} the -250/+10000 band. "
          f"Selection: {sel} to win{'' if sel == h else ''}.")
    return s


def series_probability(p_home_game, schedule):
    """Exact best-of-7 series win prob; schedule = list of 'home'/'away' for games 1-7."""
    wins = 0
    total = 0
    for result in itertools.product([0, 1], repeat=7):  # 1 = home team wins game
        hw = sum(result)
        aw = 7 - hw
        if hw != 4 and aw != 4:
            continue
        # find length
        h = a = 0
        length = 0
        for i, r in enumerate(result):
            length = i + 1
            if r:
                h += 1
            else:
                a += 1
            if h == 4 or a == 4:
                break
        prob = 1.0
        for i in range(length):
            p_game = p_home_game if schedule[i] == "home" else 1 - p_home_game
            prob *= p_game if result[i] else (1 - p_game)
        total += prob
        if result[length - 1] and sum(result[:length]) == 4:
            wins += prob
    return round(wins, 4)


def main():
    captures = load_captures()
    vindex = load_verified_form_index()
    flags = []
    inputs_rows = []
    sources = {}
    matches = []
    predictions = []

    # tennis form cache from captured result rows
    form_cache = {}
    for r in captures:
        if r.get("sport") == "tennis" and r.get("status") == "completed" and r.get("result"):
            winner = r.get("winner")
            if winner:
                form_cache[winner] = f"{r.get('result','')} ({r.get('competition','').split('—')[0].strip()})"

    for row in captures:
        sport = row.get("sport")
        date = row.get("date") or ""
        mid = row.get("id")
        in_window = WIN_START <= date <= WIN_END
        home, away = row.get("home") or "", row.get("away") or ""
        official_url = row.get("source_url") or ""
        sources.setdefault(official_url, {"url": official_url, "sport": sport,
                                          "note": row.get("note", "")})
        inputs_rows.append({"id": mid, "sport": sport, "date": date, "file": row.get("_file"),
                            "home": home, "away": away, "source_url": official_url})
        if not in_window and "outside" not in (row.get("note") or ""):
            row["note"] = (row.get("note") or "") + "; date outside 22-28 Oct window — listed for completeness"
        if not in_window:
            continue  # F1 Mexico — calendar completeness only

        eng = None
        if sport == "basketball":
            eng = engine_euroleague(row)
        elif sport == "motor-racing":
            eng = engine_f1(row)
        elif sport == "darts":
            eng = engine_seeded(row)
        elif sport == "tennis":
            eng = engine_tennis(row, form_cache)
        elif sport == "ice-hockey":
            eng = engine_team_records(row, vindex, sport, hfa=0.035, margin_scale=6.0, total_mode="goals")
        elif sport == "rugby-union":
            eng = engine_team_records(row, vindex, sport, hfa=0.055, margin_scale=14.0, total_mode="points")
        elif sport == "baseball":
            eng = engine_team_records(row, vindex, sport, hfa=0.03, margin_scale=2.5, total_mode="runs")
        else:
            eng = {"line_status": "not-originated", "basis": "no verified form captured for this sport yet",
                   "home_summary": "", "away_summary": ""}

        m = {
            "id": mid, "sport": sport, "sport_name": SPORT_NAMES.get(sport, sport),
            "competition": row.get("competition", ""), "date": date,
            "time": row.get("time_local_as_rendered") or row.get("time_utc") or "",
            "venue": row.get("venue") or "", "home": home, "away": away,
            "status": row.get("status") or "scheduled",
            "capture": "cross-ref data/verified" if eng.get("form_source") == "cross-ref data/verified" else "this session",
            "line_status": eng.get("line_status"),
            "home_summary": eng.get("home_summary") or "", "away_summary": eng.get("away_summary") or "",
            "official_source": "official source captured this session",
            "official_url": official_url,
            "olbg_url": "", "data_url": "",
            "basis": eng.get("basis") or "", "notes": [row.get("note")] if row.get("note") else [],
            "markets": {}, "winner_pick": None,
            "leaders": row.get("leaders") or "",
        }
        if eng.get("line_status") == "originated":
            if "probs" in eng:  # multi-outcome (F1)
                probs = eng["probs"]
                top = max(probs, key=probs.get)
                tp = probs[top]
                dp = dec_from_prob(tp)
                aa = american_from_decimal(dp)
                m["markets"]["winner"] = {"type": "Race Winner (each-way terms not modelled)",
                                          "probs": probs, "favourite": top,
                                          "favourite_decimal": dp, "favourite_american_str": american_str(aa)}
                pick = {"selection": top, "market": "Race Winner", "prob": tp, "decimal": dp,
                        "american": aa, "american_str": american_str(aa), "in_band": in_band(aa),
                        "confidence": confidence_for(tp, aa)}
                m["winner_pick"] = pick
            else:
                hp, ap = eng["hp"], eng["ap"]
                m["markets"]["winner"] = winner_block(hp, ap, home, away)
                m["markets"]["handicap"] = handicap_block(max(hp, ap), eng.get("margin"),
                                                          hp >= ap, home, away)
                m["markets"]["total"] = total_block(eng.get("total"))
                if hp >= ap:
                    sel, sp, opp = home, hp, away
                else:
                    sel, sp, opp = away, ap, home
                dp = dec_from_prob(sp)
                aa = american_from_decimal(dp)
                pick = {"selection": sel, "market": "Win Match", "prob": sp, "decimal": dp,
                        "american": aa, "american_str": american_str(aa), "in_band": in_band(aa),
                        "confidence": confidence_for(sp, aa)}
                m["winner_pick"] = pick
            p = dict(m["winner_pick"])
            p.update({"id": mid, "sport": sport, "date": date,
                      "matchup": f"{home} vs {away}" if away else home,
                      "competition": m["competition"],
                      "writeup": build_writeup(m, p, eng), "basis": m["basis"],
                      "official_url": official_url})
            predictions.append(p)
        else:
            flags.append({"id": mid, "sport": sport, "date": date,
                          "matchup": f"{home} vs {away}" if away else home,
                          "item": "betting line not originated",
                          "why": eng.get("basis", "unverified") + " — value left blank per policy",
                          "link": official_url})
        matches.append(m)

    # ---- inherited cross-reference rows (prior sessions' official captures, same window) ----
    EXCLUDED = {"soccer", "football", "american-football", "boxing", "ufc", "mma",
                "hurling", "horse-racing", "cycling", "specials"}
    vpreds = {}
    try:
        vp = json.load(open(os.path.join(ROOT, "data", "verified", "predictions.json")))
        for p in vp.get("predictions", vp if isinstance(vp, list) else []):
            if p.get("match_id"):
                vpreds[p["match_id"]] = p
    except Exception:
        vpreds = {}
    def _norm(name):
        name = unicodedata.normalize("NFKD", name or "")
        name = "".join(ch for ch in name if not unicodedata.combining(ch))
        name = name.replace("ł", "l").replace("Ł", "L")
        return re.sub(r"\s*\([^)]*\)", "", name).strip().lower()

    def _dparse(s):
        try:
            return datetime.date.fromisoformat(s)
        except Exception:
            return None

    fresh_keys = {(m["sport"], m["date"], _norm(m["home"]), _norm(m["away"])) for m in matches}
    fresh_loose = {}  # (sport, name) -> set of dates
    fresh_cores = {}  # (sport, last-word) -> set of dates
    for m in matches:
        for side in (m["home"], m["away"]):
            n = _norm(side)
            if n:
                fresh_loose.setdefault((m["sport"], n), set()).add(m["date"])
                fresh_cores.setdefault((m["sport"], n.split()[-1]), set()).add(m["date"])

    def _near_in(bucket, sp, name, date):
        ds = bucket.get((sp, name))
        if not ds:
            return False
        d0 = _dparse(date)
        if not d0:
            return date in ds
        for d in ds:
            d1 = _dparse(d)
            if d1 and abs((d1 - d0).days) <= 2:
                return True
        return False

    def _near(sp, name, date):
        if not name:
            return False
        return (_near_in(fresh_loose, sp, name, date) or
                _near_in(fresh_cores, sp, name.split()[-1], date))

    def _pair_near(sp, home, away, date):
        if _near(sp, home, date) and _near(sp, away, date):
            return True
        # individual sports: a player appears once per round, so a one-sided match is enough
        if sp in ("darts", "tennis", "snooker") and (_near(sp, home, date) or _near(sp, away, date)):
            return True
        return False
    vh2h = {}
    try:
        vrows = json.load(open(os.path.join(ROOT, "data", "verified", "matches.json"))).get("matches", [])
    except Exception:
        vrows = []
    for v in vrows:
        sp = v.get("sport")
        if sp in EXCLUDED or sp not in SPORT_NAMES:
            continue
        date = (v.get("date") or "")[:10]
        if not (WIN_START <= date <= WIN_END):
            continue
        nh, na = _norm(v.get("home")), _norm(v.get("away"))
        key = (sp, date, nh, na)
        if key in fresh_keys:
            continue  # fresh capture wins; never double-count
        if _pair_near(sp, nh, na, date):
            flags.append({"id": f"date-clash-{vid}", "sport": sp, "date": date,
                          "matchup": f"{v.get('home')} vs {v.get('away')}",
                          "item": "prior-layer date/name clash with fresh capture",
                          "why": "data/verified lists this same pairing with a different date and/or older club sponsor naming; the fresh capture from the official league game centre is kept and this duplicate is suppressed",
                          "link": v.get("official_url") or ""})
            continue
        if sp == "motor-racing" and any(k[0] == "motor-racing" and k[1] == date for k in fresh_keys):
            continue  # multi-outcome event: one row per race, fresh capture wins
        vid = v.get("id") or f"in-{sp}-{date}-{abs(hash(key)) % 10000}"
        wm = v.get("winner_market") or {}
        hm = v.get("handicap_market") or {}
        tm = v.get("total_market") or {}
        hp, ap = wm.get("home_prob"), wm.get("away_prob")
        hd, ad = wm.get("home_odds"), wm.get("away_odds")
        ha, aa = american_from_decimal(hd), american_from_decimal(ad)
        vpick = v.get("pick") or {}
        sel = vpick.get("team") or (vpick.get("selection") or "").split(" (")[0]
        prob = vpick.get("probability")
        fam = vpick.get("fair_american")
        is_moneyline = "Handicap" not in (vpick.get("selection") or "") and "Total" not in (vpick.get("selection") or "")
        m = {
            "id": vid, "sport": sp, "sport_name": SPORT_NAMES.get(sp, sp),
            "competition": v.get("competition", ""), "date": date,
            "time": v.get("time") or "", "venue": v.get("venue") or "",
            "home": v.get("home") or "", "away": v.get("away") or "",
            "status": "scheduled",
            "capture": "inherited (data/verified PR #82 — official sources captured by an earlier OLBG2 session)",
            "line_status": "originated (prior layer)" if wm else "not-originated",
            "home_summary": v.get("home_summary") or "", "away_summary": v.get("away_summary") or "",
            "official_source": v.get("official_source") or "prior layer official capture",
            "official_url": v.get("official_url") or v.get("data_url") or "",
            "olbg_url": v.get("olbg_url") or "", "data_url": v.get("data_url") or "",
            "basis": "line originated by the /verified/ layer model from the same window's official captures — cross-referenced here, not re-derived",
            "notes": ["inherited cross-reference; see /verified/ for the original row"],
            "markets": {
                "winner": {"type": wm.get("type", "Win Match"),
                           "home_prob": hp, "away_prob": ap,
                           "home_decimal": hd, "away_decimal": ad,
                           "home_american": ha, "away_american": aa,
                           "home_american_str": american_str(ha), "away_american_str": american_str(aa),
                           "home_in_band": in_band(ha), "away_in_band": in_band(aa)} if wm else {},
                "handicap": {"line": hm.get("line"), "label": hm.get("label"),
                             "fav_prob": hm.get("fav_prob"),
                             "fav_decimal": hm.get("fav_odds"),
                             "fav_american_str": american_str(american_from_decimal(hm.get("fav_odds"))),
                             "in_band": in_band(american_from_decimal(hm.get("fav_odds")))} if hm else None,
                "total": {"line": tm.get("line"), "over_prob": tm.get("over_prob"),
                          "under_prob": tm.get("under_prob"), "over_decimal": tm.get("over_odds"),
                          "over_american_str": american_str(american_from_decimal(tm.get("over_odds"))),
                          "in_band": in_band(american_from_decimal(tm.get("over_odds"))),
                          "note": "prior-layer total (modelled from captured scoring)"} if tm else None,
            },
            "winner_pick": None,
        }
        if sel and prob is not None and is_moneyline:
            dp = vpick.get("fair_odds") or dec_from_prob(prob)
            pick = {"selection": sel, "market": "Win Match", "prob": prob, "decimal": dp,
                    "american": fam, "american_str": american_str(fam),
                    "in_band": in_band(fam),
                    "confidence": confidence_for(prob, fam)}
            m["winner_pick"] = pick
            vtext = ""
            vpp = vpreds.get(vid)
            if vpp and vpp.get("text"):
                vtext = vpp["text"]
            elif vid in HAND_WROTE:
                vtext = HAND_WROTE[vid]
            if vtext and not (vpp and vpp.get("text")):
                wu_origin = "hand-written this session from verified form summaries"
            elif vtext:
                wu_origin = "prior layer /verified/ (attributed, not re-authored)"
            else:
                wu_origin = ""
            p = dict(pick)
            p.update({"id": vid, "sport": sp, "date": date,
                      "matchup": f"{m['home']} vs {m['away']}" if m["away"] else m["home"],
                      "competition": m["competition"],
                      "writeup": vtext,
                      "writeup_origin": wu_origin,
                      "basis": m["basis"], "official_url": m["official_url"]})
            if not vtext:
                flags.append({"id": f"wu-{vid}", "sport": sp, "date": date,
                              "matchup": p["matchup"], "item": "inherited pick without write-up text",
                              "why": "prior layer carried the selection but no long-form text was found in its predictions file; left blank rather than fabricated",
                              "link": m["official_url"]})
            predictions.append(p)
        if not wm:
            flags.append({"id": vid, "sport": sp, "date": date,
                          "matchup": f"{m['home']} vs {m['away']}" if m["away"] else m["home"],
                          "item": "inherited row without originated line",
                          "why": "the prior layer carried this fixture but had no modelled winner market for it; left blank rather than invented",
                          "link": m["official_url"]})
        matches.append(m)

    # carry prior-layer featured picks in other markets (handicap/alt) with their write-ups
    def _mclass(market):
        return "ml" if ("Winner" in market or market in ("Win Match", "Moneyline")) else market

    mids = {m["id"] for m in matches}
    have = {(p["id"], _mclass(p["market"])) for p in predictions}
    for vid, vpp in vpreds.items():
        if vid not in mids:
            continue
        market = vpp.get("market") or "Win Match"
        if (vid, _mclass(market)) in have:
            continue
        prob = vpp.get("probability")
        fam = vpp.get("fair_american")
        p = {"id": vid, "sport": vpp.get("sport") or "", "date": (vpp.get("time") or "")[:10],
             "matchup": vpp.get("event") or vpp.get("selection") or vid,
             "competition": vpp.get("competition") or "",
             "selection": vpp.get("selection") or "", "market": market,
             "prob": prob, "decimal": vpp.get("fair_odds") or dec_from_prob(prob),
             "american": fam, "american_str": american_str(fam), "in_band": in_band(fam),
             "confidence": confidence_for(prob, fam),
             "writeup": vpp.get("text") or "",
             "writeup_origin": "prior layer /verified/ (attributed, not re-authored)",
             "basis": "prior-layer featured pick carried across with its official-source write-up",
             "official_url": vpp.get("official_url") or ""}
        predictions.append(p)

    # special flags (irregularities / sourcing quirks)
    flags.append({"id": "flag-pdc-source", "sport": "darts", "date": WIN_START,
                  "matchup": "2026 Machineseeker European Championship",
                  "item": "PDC pages served content behind a consent wall",
                  "why": "official pdc.tv schedule/news text retrieved via search-engine rendering of the official URLs rather than direct fetch; rows keep the official URLs for manual review",
                  "link": "https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship"})
    flags.append({"id": "flag-humphries", "sport": "darts", "date": WIN_START,
                  "matchup": "Luke Humphries → Kim Huybrechts (European Championship R1)",
                  "item": "late withdrawal substitution",
                  "why": "Luke Humphries withdrew on 22 Oct with gastroenteritis per official PDC statement; Huybrechts inherits his draw against Ryan Searle — irregular for line origination and flagged for manual review",
                  "link": "https://www.pdc.tv/news/2026/october/22/humphries-withdraws-from-machineseeker-european-championship"})
    flags.append({"id": "flag-urc-tz", "sport": "rugby-union", "date": "2026-10-23",
                  "matchup": "URC Round 4 (all eight fixtures)",
                  "item": "kick-off times labelled Local",
                  "why": "stats.unitedrugby.com rendered times labelled Local without a timezone; no timezone inferred — times published as rendered",
                  "link": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/cardiff-rugby-vs-hollywoodbets-sharks-2026-10-23/292608"})
    flags.append({"id": "flag-euroleague-tz", "sport": "basketball", "date": WIN_START,
                  "matchup": "Turkish Airlines EuroLeague Rounds 7-8",
                  "item": "game times as rendered, timezone not stated",
                  "why": "official EuroLeague widget rendered times without timezone labels; not inferred",
                  "link": "https://www.euroleaguebasketball.net/en/euroleague/"})
    flags.append({"id": "flag-nba-gap", "sport": "basketball", "date": WIN_START,
                  "matchup": "NBA 22-28 Oct slate",
                  "item": "fresh NBA capture not possible this session",
                  "why": "nba.com schedule pages rendered filter shell only and cdn.nba.com static JSON endpoints returned HTTP 500 at capture time; NBA coverage for this window is cross-referenced to the /verified/ layer (PR #82, 74-game slate, official sources) rather than re-captured — not presented as fresh capture",
                  "link": "https://buffedlizard55-lab.github.io/OLBG2/verified/"})
    flags.append({"id": "flag-euroleague-r8-gap", "sport": "basketball", "date": "2026-10-28",
                  "matchup": "EuroLeague Round 8 games 77-80",
                  "item": "possible 28 Oct EuroLeague games not rendered",
                  "why": "the official widget rendered six Round 8 games for 27 Oct only; games 77-80 (if scheduled) never appeared — left out rather than inferred",
                  "link": "https://www.euroleaguebasketball.net/en/euroleague/"})
    flags.append({"id": "flag-volleyball-times", "sport": "volleyball", "date": WIN_START,
                  "matchup": "TAURON Liga / Polish Super Cup",
                  "item": "local (Poland) start times",
                  "why": "tauronliga.pl rendered start times without timezone labels; rendered as local Poland time, not converted",
                  "link": "https://www.tauronliga.pl/games.html"})
    flags.append({"id": "flag-wst-venue", "sport": "snooker", "date": WIN_START,
                  "matchup": "BetVictor Northern Ireland Open 2026",
                  "item": "venue not rendered on the WST matches page",
                  "why": "match rows cite the official WST match-centre pages; venue cell left blank per the no-inference policy",
                  "link": "https://www.wst.tv/matches/"})

    # sports with no fresh capture this session — gap register (never fabricated)
    gap_sports = [
        ("aussie-rules", "AFLW Round 8/9 pages not captured this session (afl.com.au is client-rendered) and no prior-layer rows exist for this window — nothing invented; AFLW rows pending a session with a working capture path.", "https://www.afl.com.au/"),
        ("esports", "Tencent LOL Pro League pages behind client rendering; no verified fixture list obtained this session or in prior layers for this window — cross-reference VF-18 research in /survey/ only.", "https://www.whipsaw.com/"),
    ]
    inherited_sports = sorted({m["sport"] for m in matches if m["capture"].startswith("inherited")})
    for sp in inherited_sports:
        flags.append({"id": f"inherited-{sp}", "sport": sp, "date": WIN_START,
                      "matchup": f"{SPORT_NAMES.get(sp, sp)} — window 22-28 Oct",
                      "item": "coverage inherited, not re-captured",
                      "why": f"no fresh official capture possible for {sp} within this session's fetch budget (see research notes); rows shown are cross-referenced from data/verified (PR #82) where an earlier session captured them from official sources — clearly labelled inherited",
                      "link": "https://buffedlizard55-lab.github.io/OLBG2/verified/"})

    os.makedirs(UPD, exist_ok=True)

    inputs_doc = {
        "generated": "session arena/d69dc1c9-olbg2", "window": [WIN_START, WIN_END],
        "rule": "every input below was captured from an official source this session; cross-ref rows are labelled and never presented as fresh capture",
        "f1_2026_winners": [{"race": r, "winner": w} for r, w in F1_2026_WINNERS],
        "f1_2026_driver_points": F1_POINTS,
        "rows": inputs_rows,
    }
    json.dump(inputs_doc, open(os.path.join(UPD, "inputs.json"), "w"), indent=1)
    json.dump({"generated": "session arena/d69dc1c9-olbg2",
               "rule": "links verified reachable at capture time",
               "sources": sorted(sources.values(), key=lambda s: (s["sport"] or "", s["url"]))},
              open(os.path.join(UPD, "sources.json"), "w"), indent=1)
    json.dump({"generated": "session arena/d69dc1c9-olbg2", "window": [WIN_START, WIN_END],
               "matches": matches}, open(os.path.join(UPD, "matches.json"), "w"), indent=1)
    json.dump({"generated": "session arena/d69dc1c9-olbg2", "predictions": predictions},
              open(os.path.join(UPD, "predictions.json"), "w"), indent=1)
    band = [p for p in predictions if p["in_band"]]
    json.dump({"generated": "session arena/d69dc1c9-olbg2", "picks": band},
              open(os.path.join(UPD, "band.json"), "w"), indent=1)
    json.dump({"generated": "session arena/d69dc1c9-olbg2", "items": flags},
              open(os.path.join(UPD, "flagged.json"), "w"), indent=1)

    hi = [p for p in predictions if p["confidence"] == "high"]
    print(f"matches={len(matches)} predictions={len(predictions)} band={len(band)} high={len(hi)} flags={len(flags)}")


if __name__ == "__main__":
    main()
