#!/usr/bin/env python3
"""
Quest desk seed — deterministic, offline.

Merges the two freshest checked-in captures in this repository into one current
board for exactly the 15 mandated sports:

  * /cadence/ capture 2026-10-23T20:05Z (93 fixtures, 728 originated prices,
    122 graded picks, 33 written predictions) — the base layer;
  * /brief/ capture 2026-10-23T16:30Z NHL rows for Saturday 24 October
    (games 2026020168-0179) which cadence does not hold, re-priced here with a
    documented Poisson engine from the same stored official team inputs;
  * NHL fixtures for 25-26 October (games 2026020180-0187) read first-hand from
    NHL.com on 2026-10-23 ~21:30Z by this session; priced only where both clubs
    have stored official inputs in the brief capture, otherwise listed blank
    with the reason on the row.

No network access. No value is invented: every fixture, fact and price traces to
a stored capture or to the NHL.com read recorded in research/quest-693dbf40.md.
Start times are normalised into three explicit provenance classes (see TZ
handling below); anything whose clock basis cannot be resolved stays date-only
with start_utc null and is flagged, never silently converted.

Cut-off for "upcoming": 2026-10-23T21:30:00Z (CUTOFF), printed on every page.
"""
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "quest"
CUTOFF = "2026-10-23T21:30:00Z"
SESSION = "693dbf40"

SPORTS15 = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
            "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
            "Handball", "Ice Hockey", "Basketball", "Rugby League"]

# OLBG taxonomy read live from https://www.olbg.com/betting-tips on 2026-10-23.
OLBG = {
    "Tennis": (3, "https://www.olbg.com/betting-tips/Tennis/3"),
    "Basketball": (4, "https://www.olbg.com/betting-tips/Basketball/4"),
    "Golf": (5, "https://www.olbg.com/betting-tips/Golf/5"),
    "Cricket": (7, "https://www.olbg.com/betting-tips/Cricket/7"),
    "Snooker": (8, "https://www.olbg.com/betting-tips/Snooker/8"),
    "Rugby Union": (9, "https://www.olbg.com/betting-tips/Rugby_Union/9"),
    "Rugby League": (10, "https://www.olbg.com/betting-tips/Rugby_League/10"),
    "Baseball": (12, "https://www.olbg.com/betting-tips/Baseball/12"),
    "Ice Hockey": (13, "https://www.olbg.com/betting-tips/Ice_Hockey/13"),
    "Motor Racing": (14, "https://www.olbg.com/betting-tips/Motor_Racing/14"),
    "Darts": (15, "https://www.olbg.com/betting-tips/Darts/15"),
    "Handball": (20, "https://www.olbg.com/betting-tips/Handball/20"),
    "Volleyball": (21, "https://www.olbg.com/betting-tips/Volleyball/21"),
    "Gaelic Sports": (25, "https://www.olbg.com/betting-tips/Gaelic_Football/25"),
    "Greyhounds": (28, "https://www.olbg.com/betting-tips/Greyhounds/28"),
}
OLBG_HURLING = ("Hurling (under Gaelic Sports)", 26,
                "https://www.olbg.com/betting-tips/Hurling/26")

HIGH_P, MED_P = 0.70, 0.60
BAND_MAX_P = 250 / 350  # fair -250 == 0.7142857...


def american(p):
    p = min(max(p, 0.005), 0.995)
    if p >= 0.5:
        return -int(round(100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def dec(p):
    return round(1 / p, 3)


def in_band_am(am):
    return -250 <= am <= 10000


def conf(p):
    if p >= HIGH_P:
        return "high"
    if p >= MED_P:
        return "medium"
    return "low"


def load(path):
    return json.loads((ROOT / path).read_text())


def dump(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------
# Time normalisation. Three provenance classes:
#   venue-local  : domestic league / order-of-play clocks, converted with
#                  zoneinfo (DST-correct, incl. the 25 Oct Europe transition).
#   viewer-et   : pages that rendered in the capturing browser's zone. The
#                  zone is triangulated as America/New_York from nine
#                  independent venue-plausibility checks (see research note);
#                  converted but flagged Q-TZ1 for review.
#   date-only   : clock basis unresolved (WST site clock, EuroLeague/URC
#                  "local", TBC, followed-by, season outrights). start_utc
#                  stays null; only the calendar date is asserted.
# Darts uses the published session-window start (CEST stated on the page).
# --------------------------------------------------------------------------
VENUE_LOCAL = {
    "vb-perugia-prata": ("2026-10-25T18:00", "Europe/Rome"),
    "vb-trentino-cisterna": ("2026-10-25T17:00", "Europe/Rome"),
    "vb-piacenza-modena": ("2026-10-25T18:00", "Europe/Rome"),
    "vb-civitanova-padova": ("2026-10-25T18:00", "Europe/Rome"),
    "vb-milano-cuneo": ("2026-10-25T19:00", "Europe/Rome"),
    "vb-monza-verona": ("2026-10-25T18:00", "Europe/Rome"),
    "vb-friedrichshafen-karlsruhe": ("2026-10-24T18:30", "Europe/Berlin"),
    "vb-lueneburg-warnemuende": ("2026-10-24T19:00", "Europe/Berlin"),
    "vb-giesen-berlin": ("2026-10-24T19:30", "Europe/Berlin"),
    "vb-dueren-muenchen": ("2026-10-24T19:30", "Europe/Berlin"),
    "gaa-shinty-hurling": ("2026-10-24T18:00", "Europe/Dublin"),
    "gaa-cork-psfc": ("2026-10-25T16:00", "Europe/Dublin"),
    "gaa-kerry-sfc": ("2026-10-25T14:00", "Europe/Dublin"),
    "gaa-waterford-sfc": ("2026-10-25T14:30", "Europe/Dublin"),
    "gaa-limerick-shc": ("2026-10-25T15:45", "Europe/Dublin"),
    "ten-almaty-sf1": ("2026-10-24T18:00", "Asia/Almaty"),
    "ten-almaty-sf2": ("2026-10-24T15:00", "Asia/Almaty"),
    "ten-vienna-q1a": ("2026-10-24T11:30", "Europe/Vienna"),
}
SESSION_START = {
    "drt-r2-1": ("2026-10-24T13:00", "Europe/Berlin"),
    "drt-r2-2": ("2026-10-24T13:00", "Europe/Berlin"),
    "drt-r2-3": ("2026-10-24T13:00", "Europe/Berlin"),
    "drt-r2-4": ("2026-10-24T13:00", "Europe/Berlin"),
    "drt-r2-5": ("2026-10-24T19:00", "Europe/Berlin"),
    "drt-r2-6": ("2026-10-24T19:00", "Europe/Berlin"),
    "drt-r2-7": ("2026-10-24T19:00", "Europe/Berlin"),
    "drt-r2-8": ("2026-10-24T19:00", "Europe/Berlin"),
}
VIEWER_ET = {
    "cri-40681": "2026-10-23T19:30", "cri-40683": "2026-10-24T02:00",
    "cri-41095": "2026-10-24T03:00", "cri-40981": "2026-10-25T04:00",
    "cri-40394": "2026-10-25T04:30", "cri-39992": "2026-10-27T04:30",
    "ru-leicester-northampton": "2026-10-24T10:05",
    "ru-bristol-exeter": "2026-10-24T12:30",
    "ru-quins-saracens": "2026-10-25T11:00",
}
DATE_ONLY = {
    "el-E2026_76": "2026-10-27", "el-E2026_75": "2026-10-27",
    "el-E2026_73": "2026-10-27", "el-E2026_79": "2026-10-28",
    "el-E2026_77": "2026-10-28", "el-E2026_80": "2026-10-28",
    "snk-ni-sf1": "2026-10-24", "snk-ic-murphy": "2026-10-30",
    "snk-ic-zhou": "2026-10-30", "snk-ic-liu": "2026-10-30",
    "snk-ic-white": "2026-10-30", "snk-ic-szubarczyk": "2026-10-30",
    "snk-ic-hallworth": "2026-10-30", "snk-ic-liuwenwei": "2026-10-30",
    "ru-bulls-ulster": "2026-10-24", "ru-stormers-scarlets": "2026-10-24",
    "ru-benetton-glasgow": "2026-10-24", "ru-leinster-munster": "2026-10-24",
    "ru-ospreys-dragons": "2026-10-24",
    "ten-vienna-q1b": "2026-10-24", "ten-vienna-q1c": "2026-10-24",
    "golf-bermuda": "2026-10-24", "golf-genesis": "2026-10-24",
    "grey-scurry": "2026-10-24", "grey-oaks": "2026-10-24",
    "f1-wdc": "2026-12-06",
}


def to_utc(local_iso, zone):
    dt = datetime.fromisoformat(local_iso).replace(tzinfo=ZoneInfo(zone))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalise_time(fid, start_utc, display):
    """Return (start_utc, time_status, time_note, sort_key)."""
    if start_utc:
        dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
        z = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return z, "published-utc-or-offset", \
            f"As stored in the source capture ({start_utc}); shown in UTC. {display}", z
    if fid in VENUE_LOCAL:
        local, zone = VENUE_LOCAL[fid]
        u = to_utc(local, zone)
        return u, "venue-local-converted", \
            f"Published clock read as {zone} venue time ({display}); converted to UTC.", u
    if fid in SESSION_START:
        local, zone = SESSION_START[fid]
        u = to_utc(local, zone)
        return u, "session-window-start", \
            f"Session window start, not an exact throw time ({display}).", u
    if fid in VIEWER_ET:
        u = to_utc(VIEWER_ET[fid], "America/New_York")
        return u, "viewer-zone-inferred", \
            ("Page rendered in the capturing browser's zone; read as America/New_York "
             f"(triangulated, flag Q-TZ1). Original: {display}"), u
    assert fid in DATE_ONLY, f"no time rule for {fid}"
    d = DATE_ONLY[fid]
    return None, "date-only-unconfirmed", \
        f"Calendar date only; clock basis unresolved (flag Q-TZ2). Original: {display}", \
        f"{d}T12:00:00Z"


# --------------------------------------------------------------------------
# NHL Poisson engine for the added fixtures.
# Expected goals: att/def vs league mean from the 27 stored team lines,
# 4% home lift on the home club (none at a neutral site). Regulation score
# matrix 0..12 each way; a regulation tie is settled in OT/SO in proportion
# to expected goals, counts as a one-goal margin and adds one goal to the
# total. Markets: money line, puck line -1.5/+1.5 on the favourite/underdog,
# totals 5.5 and 6.5, plus a band-ceiling alternate where the natural
# favourite is high-confidence but shorter than -250 (cadence convention).
# --------------------------------------------------------------------------
def pois(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def nhl_price(home, away, th, ta, league_gpg, neutral=False):
    hg = th["goalsFor"] / th["gamesPlayed"]
    hga = th["goalsAgainst"] / th["gamesPlayed"]
    ag = ta["goalsFor"] / ta["gamesPlayed"]
    aga = ta["goalsAgainst"] / ta["gamesPlayed"]
    lift = 1.0 if neutral else 1.04
    lh = (hg + aga) / 2 * lift
    la = (ag + hga) / 2
    ph = [pois(k, lh) for k in range(13)]
    pa = [pois(k, la) for k in range(13)]
    p_home_ml = p_away_ml = 0.0
    margin = {}   # home margin -> prob (OT tie-break folded in as +-1)
    total = {}    # total goals -> prob (OT goal folded in as +1)
    for i in range(13):
        for j in range(13):
            w = ph[i] * pa[j]
            if i > j:
                p_home_ml += w
                margin[i - j] = margin.get(i - j, 0) + w
                total[i + j] = total.get(i + j, 0) + w
            elif j > i:
                p_away_ml += w
                margin[i - j] = margin.get(i - j, 0) + w
                total[i + j] = total.get(i + j, 0) + w
            else:
                share = lh / (lh + la)
                p_home_ml += w * share
                p_away_ml += w * (1 - share)
                margin[1] = margin.get(1, 0) + w * share
                margin[-1] = margin.get(-1, 0) + w * (1 - share)
                total[i + j + 1] = total.get(i + j + 1, 0) + w
    s = p_home_ml + p_away_ml
    p_home_ml, p_away_ml = p_home_ml / s, p_away_ml / s

    def p_margin_at_least(team_home, need):
        if team_home:
            return sum(v for m, v in margin.items() if m >= need)
        return sum(v for m, v in margin.items() if -m >= need)

    def p_total_over(line):
        return sum(v for t, v in total.items() if t > line)

    basis = (f"Poisson on stored NHL inputs to 23 Oct: {home} {hg:.2f} scored / "
             f"{hga:.2f} conceded per game ({th['gamesPlayed']} GP), {away} "
             f"{ag:.2f} / {aga:.2f} ({ta['gamesPlayed']} GP); league mean "
             f"{league_gpg:.2f}; expected goals {lh:.2f}-{la:.2f}"
             + ("" if neutral else "; 4% home lift"))
    fav_home = p_home_ml >= p_away_ml
    fav = home if fav_home else away
    dog = away if fav_home else home
    rows = [
        ("Money line", home, None, p_home_ml),
        ("Money line", away, None, p_away_ml),
        ("Puck line", f"{fav} -1.5", -1.5, p_margin_at_least(fav_home, 2)),
        ("Puck line", f"{dog} +1.5", 1.5, 1 - p_margin_at_least(fav_home, 2)),
    ]
    for line in (5.5, 6.5):
        po = p_total_over(line)
        rows += [("Total goals", f"Over {line}", line, po),
                 ("Total goals", f"Under {line}", line, 1 - po)]
    out = []
    for market, sel, line, p in rows:
        p = min(max(p, 0.005), 0.995)
        am = american(p)
        out.append({"market": market, "selection": sel, "line": line,
                    "probability": round(p, 6), "fair_american": am,
                    "fair_decimal": dec(p), "in_band": in_band_am(am),
                    "confidence": conf(p), "basis": basis, "band_line": False})
    # Band-ceiling alternate (only when the natural favourite is shorter
    # than -250): search the totals ladder, then the puck ladder.
    pfav = max(p_home_ml, p_away_ml)
    if pfav > BAND_MAX_P:
        cands = []
        for line in (4.5, 5.5, 6.5, 7.5, 8.5):
            po = p_total_over(line)
            cands += [("Total goals", f"Over {line}", line, po),
                      ("Total goals", f"Under {line}", line, 1 - po)]
        for need, lab, thome in ((1, "-0.5", fav_home), (2, "-1.5", fav_home),
                                 (1, "+0.5", not fav_home), (2, "+1.5", not fav_home),
                                 (3, "+2.5", not fav_home)):
            team = fav if thome == fav_home else dog
            cands.append(("Puck line", f"{team} {lab}", float(lab),
                          p_margin_at_least(thome, need)
                          if lab.startswith("-") else
                          1 - p_margin_at_least(not thome, need + 1)))
        best = None
        for market, sel, line, p in cands:
            if HIGH_P <= p <= BAND_MAX_P and (best is None or p > best[3]):
                if any(r["market"] == market and r["selection"] == sel for r in out):
                    continue
                best = (market, sel, line, p)
        if best:
            market, sel, line, p = best
            am = american(p)
            out.append({"market": market, "selection": sel, "line": line,
                        "probability": round(p, 6), "fair_american": am,
                        "fair_decimal": dec(p), "in_band": True,
                        "confidence": conf(p),
                        "basis": basis + "; alternate line at the -250 ceiling",
                        "band_line": True})
    return out, p_home_ml, basis


# New NHL fixtures read first-hand from NHL.com, 2026-10-23 ~21:30Z.
# (id, away, home, EDT wall clock, neutral site)
NHL_NEW = [
    ("nhl-2026020180", "Florida Panthers", "Chicago Blackhawks", "2026-10-25T15:00", False,
     "https://www.nhl.com/gamecenter/fla-vs-chi/2026/10/25/2026020180"),
    ("nhl-2026020181", "New York Islanders", "Dallas Stars", "2026-10-25T18:00", False,
     "https://www.nhl.com/gamecenter/nyi-vs-dal/2026/10/25/2026020181"),
    ("nhl-2026020182", "Montreal Canadiens", "Winnipeg Jets", "2026-10-25T19:00", True,
     "https://www.nhl.com/gamecenter/mtl-vs-wpg/2026/10/25/2026020182"),
    ("nhl-2026020183", "Colorado Avalanche", "Nashville Predators", "2026-10-25T20:00", False,
     "https://www.nhl.com/gamecenter/col-vs-nsh/2026/10/25/2026020183"),
    ("nhl-2026020184", "Minnesota Wild", "Vancouver Canucks", "2026-10-25T22:00", False,
     "https://www.nhl.com/gamecenter/min-vs-van/2026/10/25/2026020184"),
    ("nhl-2026020185", "Los Angeles Kings", "New York Rangers", "2026-10-26T19:00", False,
     "https://www.nhl.com/gamecenter/lak-vs-nyr/2026/10/26/2026020185"),
    ("nhl-2026020186", "Toronto Maple Leafs", "Calgary Flames", "2026-10-26T20:30", False,
     "https://www.nhl.com/gamecenter/tor-vs-cgy/2026/10/26/2026020186"),
    ("nhl-2026020187", "Detroit Red Wings", "Edmonton Oilers", "2026-10-26T21:30", False,
     "https://www.nhl.com/gamecenter/det-vs-edm/2026/10/26/2026020187"),
]
NHL_STATS_URL = ("https://api.nhle.com/stats/rest/en/team/summary"
                 "?cayenneExp=seasonId=20262027%20and%20gameTypeId=2")
NHL_SCHED25_URL = "https://www.nhl.com/schedule/2026-10-25"

# Hand-written predictions for NEW in-band high-confidence picks only.
# Filled after the first pricing pass; quest_seed refuses to finish while an
# in-band high pick lacks prose. Facts must quote stored inputs verbatim.
NEW_PROSE = {
    "nhl-2026020170-pick": {
        "headline": "Boston's two-way start is too much for San Jose at the Garden",
        "text": (
            "Boston Bruins to beat the San Jose Sharks at TD Garden on Saturday night. "
            "Boston have made the sharpest two-way start on this board, winning eight of eleven "
            "with one overtime loss, scoring 42 goals and conceding just 22 — two a night — "
            "for 17 points in the bank already. San Jose arrive at 6-4 with one overtime loss "
            "and 13 points, but they have shipped 36 goals in the same eleven games, and that "
            "leak is a hard one to carry into the Garden. The fair price here is -236 on the Bruins."
        ),
        "facts": [
            {"claim": "8 wins, 2 losses, 1 overtime loss in 11 games, 42 goals scored, 22 conceded, 17 points",
             "source_url": NHL_STATS_URL, "source_key": "nhl-teams (brief capture)"},
            {"claim": "6 wins, 4 losses, 1 overtime loss in 11 games, 32 goals scored, 36 conceded, 13 points",
             "source_url": NHL_STATS_URL, "source_key": "nhl-teams (brief capture)"},
            {"claim": "San Jose at Boston, TD Garden, 2026-10-24 23:00Z, game 2026020170",
             "source_url": "https://www.nhl.com/gamecenter/sjs-vs-bos/2026/10/24/2026020170",
             "source_key": "nhl-schedule (brief capture)"},
        ],
    },
}


def team_fact(t):
    return (f"{t['wins']} wins, {t['losses']} losses, {t['otLosses']} overtime losses "
            f"in {t['gamesPlayed']} games, {t['goalsFor']} goals scored, "
            f"{t['goalsAgainst']} conceded, {t['points']} points")


def main():
    cad_m = load("data/cadence/matches.json")["matches"]
    cad_l = load("data/cadence/lines.json")["lines"]
    cad_p = load("data/cadence/picks.json")["picks"]
    cad_pr = load("data/cadence/predictions.json")["predictions"]
    brief = load("data/brief/matches.json")["fixtures"]
    brief_nhl = {f["id"]: f for f in brief if f["sport"] == "Ice Hockey"}

    # Stored NHL team inputs (brief capture, stats-API view). Assert the
    # snapshot is internally consistent where a club appears twice.
    teams = {}
    for f in brief_nhl.values():
        for side in ("home", "away"):
            t = f["inputs"][0][side]
            if t["team"] in teams:
                assert teams[t["team"]] == t, f"inconsistent inputs for {t['team']}"
            teams[t["team"]] = t
    league_gpg = (sum(t["goalsFor"] for t in teams.values())
                  / sum(t["gamesPlayed"] for t in teams.values()))

    fixtures, lines, picks = [], [], []

    # ---- base layer: cadence -------------------------------------------
    for m in cad_m:
        su, tstat, tnote, skey = normalise_time(
            m["id"], m.get("start_utc"), m.get("time_display"))
        fixtures.append({
            "id": m["id"], "sport": m["sport"], "competition": m["competition"],
            "home": m["home"], "away": m.get("away"), "venue": m.get("venue"),
            "start_utc": su, "time_display": m.get("time_display"),
            "time_status": tstat, "time_note": tnote, "sort_key": skey,
            "olbg_sport_id": OLBG[m["sport"]][0], "olbg_sport_url": OLBG[m["sport"]][1],
            "olbg_event_id": m.get("olbg_event_id"),
            "official_source_url": m["official_source_url"],
            "stats_source_url": m.get("stats_source_url"),
            "injury_source_url": m.get("injury_source_url"),
            "facts": m.get("facts", []), "evidence": m.get("evidence"),
            "evidence_tier": m.get("evidence_tier"),
            "status": "priced" if m.get("status") == "originated" else "blank",
            "blank_reason": None if m.get("status") == "originated" else m.get("note"),
            "favourite": m.get("favourite"),
            "favourite_probability": m.get("favourite_probability"),
            "confidence": m.get("confidence"),
            "source_desks": ["cadence"],
        })
    for l in cad_l:
        lines.append({"id": l["id"], "fixture_id": l["fixture_id"], "sport": l["sport"],
                      "market": l["market"], "selection": l["selection"],
                      "line": l.get("line"), "probability": l["probability"],
                      "fair_american": l["fair_american"],
                      "fair_decimal": l["fair_decimal"], "in_band": l["in_band"],
                      "confidence": l["confidence"], "basis": l["basis"],
                      "band_line": l.get("band_line", False), "origin": "cadence"})
    for p in cad_p:
        picks.append({**p, "origin": "cadence"})

    # ---- added NHL fixtures ---------------------------------------------
    added = []
    for fid, f in sorted(brief_nhl.items()):
        if fid in ("nhl-2026020166", "nhl-2026020167"):
            continue
        th, ta = teams[f["home"]], teams[f["away"]]
        added.append({"id": fid, "home": f["home"], "away": f["away"],
                      "venue": f.get("venue"), "start_utc": f["start_utc"],
                      "time_display": f["start_utc"] + " (NHL feed via brief capture)",
                      "official": f["source_url"], "neutral": False,
                      "th": th, "ta": ta, "desks": ["brief"]})
    for fid, away, home, edt, neutral, url in NHL_NEW:
        su = to_utc(edt, "America/New_York")
        th, ta = teams.get(home), teams.get(away)
        added.append({"id": fid, "home": home, "away": away, "venue": None,
                      "start_utc": su,
                      "time_display": f"{edt.replace('T', ' ')} EDT (NHL.com schedule, read 2026-10-23)",
                      "official": url, "neutral": neutral,
                      "th": th, "ta": ta, "desks": ["nhl.com 2026-10-23"]})

    for a in added:
        facts = []
        if a["th"]:
            facts.append({"team_or_item": a["home"], "value": team_fact(a["th"]),
                          "source_key": "nhl-teams (brief capture)",
                          "source_url": NHL_STATS_URL})
        if a["ta"]:
            facts.append({"team_or_item": a["away"], "value": team_fact(a["ta"]),
                          "source_key": "nhl-teams (brief capture)",
                          "source_url": NHL_STATS_URL})
        fx = {
            "id": a["id"], "sport": "Ice Hockey",
            "competition": "NHL" + (" (neutral site)" if a["neutral"] else ""),
            "home": a["home"], "away": a["away"], "venue": a["venue"],
            "start_utc": a["start_utc"], "time_display": a["time_display"],
            "time_status": "published-utc-or-offset",
            "time_note": "NHL-published start converted to UTC.",
            "sort_key": a["start_utc"],
            "olbg_sport_id": OLBG["Ice Hockey"][0],
            "olbg_sport_url": OLBG["Ice Hockey"][1], "olbg_event_id": None,
            "official_source_url": a["official"], "stats_source_url": NHL_STATS_URL,
            "injury_source_url": None, "facts": facts,
            "evidence": None, "evidence_tier": "B",
            "status": "blank", "blank_reason": None,
            "favourite": None, "favourite_probability": None, "confidence": None,
            "source_desks": a["desks"],
        }
        if a["th"] and a["ta"]:
            fx["evidence"] = (f"NHL 2026-27 to 23 Oct, {a['th']['gamesPlayed']} and "
                              f"{a['ta']['gamesPlayed']} games played "
                              f"(stats-API view, flag Q-DQ1)")
            rows, p_home, basis = nhl_price(a["home"], a["away"], a["th"], a["ta"],
                                            league_gpg, neutral=a["neutral"])
            for i, r in enumerate(rows):
                lines.append({"id": f"{a['id']}-q{i}", "fixture_id": a["id"],
                              "sport": "Ice Hockey", **r, "origin": "quest"})
            fav_home = p_home >= 0.5
            fav = a["home"] if fav_home else a["away"]
            pfav = p_home if fav_home else 1 - p_home
            fx.update({"status": "priced", "favourite": fav,
                       "favourite_probability": round(pfav, 6),
                       "confidence": conf(pfav)})
            am = american(pfav)
            picks.append({
                "id": f"{a['id']}-pick", "fixture_id": a["id"], "sport": "Ice Hockey",
                "competition": fx["competition"], "home": a["home"], "away": a["away"],
                "start_utc": a["start_utc"], "time_display": a["time_display"],
                "selection": fav, "market": "Money line", "line": None,
                "probability": round(pfav, 6), "fair_american": am,
                "fair_decimal": dec(pfav), "in_band": in_band_am(am),
                "confidence": conf(pfav), "evidence_tier": "B",
                "evidence": fx["evidence"], "basis": basis,
                "official_source_url": a["official"],
                "stats_source_url": NHL_STATS_URL, "origin": "quest"})
            band_rows = [r for r in rows if r["band_line"]]
            if band_rows:
                r = band_rows[0]
                picks.append({
                    "id": f"{a['id']}-band", "fixture_id": a["id"],
                    "sport": "Ice Hockey", "competition": fx["competition"],
                    "home": a["home"], "away": a["away"],
                    "start_utc": a["start_utc"], "time_display": a["time_display"],
                    "selection": r["selection"], "market": r["market"],
                    "line": r["line"], "probability": r["probability"],
                    "fair_american": r["fair_american"],
                    "fair_decimal": r["fair_decimal"], "in_band": True,
                    "confidence": r["confidence"], "evidence_tier": "B",
                    "evidence": fx["evidence"], "basis": r["basis"],
                    "official_source_url": a["official"],
                    "stats_source_url": NHL_STATS_URL, "origin": "quest"})
        else:
            missing = [n for n, t in ((a["home"], a["th"]), (a["away"], a["ta"])) if not t]
            fx["blank_reason"] = ("No stored official team inputs for "
                                  + " and ".join(missing)
                                  + " in either source capture; listed for schedule "
                                    "completeness with no line originated (flag Q-BLANK).")
        fixtures.append(fx)

    fixtures.sort(key=lambda x: x["sort_key"])
    assert {f["sport"] for f in fixtures} == set(SPORTS15), \
        {f["sport"] for f in fixtures} ^ set(SPORTS15)
    for f in fixtures:
        assert not f["start_utc"] or f["start_utc"] >= CUTOFF, f["id"]

    # ---- top five per sport ----------------------------------------------
    fx_by_id = {f["id"]: f for f in fixtures}
    by_fixture = {}
    for p in picks:
        by_fixture.setdefault(p["fixture_id"], []).append(p)

    def display_pick(fid):
        ps = by_fixture.get(fid, [])
        if not ps:
            return None
        inband = [p for p in ps if p["in_band"]]
        pool = inband if inband else ps
        return max(pool, key=lambda p: p["probability"])

    lines_by_fixture = {}
    for l in lines:
        lines_by_fixture.setdefault(l["fixture_id"], []).append(l)

    def best_inband_line(fid):
        ls = [l for l in lines_by_fixture.get(fid, []) if l["in_band"]]
        if not ls:
            return None
        b = max(ls, key=lambda l: l["probability"])
        return {"selection": b["selection"], "market": b["market"],
                "line": b.get("line"), "probability": b["probability"],
                "fair_american": b["fair_american"],
                "fair_decimal": b["fair_decimal"], "confidence": b["confidence"]}

    top5 = {}
    for sport in SPORTS15:
        fids = [f["id"] for f in fixtures if f["sport"] == sport and f["status"] == "priced"]
        disp = [(display_pick(fid), fx_by_id[fid]) for fid in fids]
        disp = [(p, f) for p, f in disp if p]
        disp.sort(key=lambda x: -x[0]["probability"])
        top5[sport] = []
        for rank, (p, f) in enumerate(disp[:5], 1):
            top5[sport].append({
                "rank": rank, "pick_id": p["id"], "fixture_id": f["id"],
                "best_inband_line": best_inband_line(f["id"]),
                "sport": sport, "competition": f["competition"],
                "home": f["home"], "away": f["away"], "venue": f["venue"],
                "start_utc": f["start_utc"], "time_display": f["time_display"],
                "time_status": f["time_status"],
                "selection": p["selection"], "market": p["market"],
                "line": p.get("line"), "probability": p["probability"],
                "fair_american": p["fair_american"], "fair_decimal": p["fair_decimal"],
                "in_band": p["in_band"], "confidence": p["confidence"],
                "evidence": p.get("evidence"), "basis": p["basis"],
                "official_source_url": f["official_source_url"],
                "stats_source_url": f.get("stats_source_url"),
                "olbg_sport_url": f["olbg_sport_url"]})

    # ---- predictions -------------------------------------------------------
    predictions = [{**x, "origin": "cadence"} for x in cad_pr]
    pick_by_id = {p["id"]: p for p in picks}
    for pid, prose in NEW_PROSE.items():
        p = pick_by_id[pid]
        f = fx_by_id[p["fixture_id"]]
        predictions.append({
            "id": f"pred-{pid}", "pick_id": pid, "fixture_id": p["fixture_id"],
            "sport": p["sport"], "competition": p["competition"],
            "home": p["home"], "away": p["away"], "start_utc": f["start_utc"],
            "time_display": f["time_display"], "selection": p["selection"],
            "market": p["market"], "line": p.get("line"),
            "probability": p["probability"], "fair_american": p["fair_american"],
            "confidence": p["confidence"], "in_band": p["in_band"],
            "headline": prose["headline"], "text": prose["text"],
            "word_count": len(prose["text"].split()), "facts": prose["facts"],
            "official_source_url": f["official_source_url"], "origin": "quest"})

    missing_prose = [p["id"] for p in picks
                     if p["confidence"] == "high" and p["in_band"]
                     and p["id"] not in {x["pick_id"] for x in predictions}]
    if missing_prose:
        print("IN-BAND HIGH PICKS WITHOUT PROSE (fill NEW_PROSE):")
        for pid in missing_prose:
            p = pick_by_id[pid]
            print(f"  {pid}: {p['selection']} ({p['market']}) p={p['probability']:.4f} "
                  f"am={p['fair_american']} fixture={p['fixture_id']}")

    # ---- sources -----------------------------------------------------------
    cad_s = load("data/cadence/sources.json")["sources"]
    brief_s = load("data/brief/sources.json")["sources"]
    sources = {}
    for s in cad_s:
        sources[s["url"]] = {"key": s["key"], "publisher": s["publisher"],
                             "url": s["url"], "what": s["what"],
                             "captured_utc": s["fetched_utc"], "desks": ["cadence"]}
    for s in brief_s:
        if s["url"] in sources:
            sources[s["url"]]["desks"].append("brief")
        else:
            sources[s["url"]] = {"key": s["key"], "publisher": s["name"],
                                 "url": s["url"], "what": s["used_for"],
                                 "captured_utc": s["captured_utc"], "desks": ["brief"]}
    for key, pub, url, what in [
        ("olbg-tips-quest", "OLBG", "https://www.olbg.com/betting-tips",
         "Sport taxonomy and IDs re-read first-hand 2026-10-23; event table returned 'No tips found'"),
        ("olbg-basketball-quest", "OLBG", "https://www.olbg.com/betting-tips/Basketball/4",
         "Market vocabulary (Money Line, Pointspread, Game Totals) re-read first-hand 2026-10-23"),
        ("nhl-sched23-quest", "NHL", "https://www.nhl.com/schedule",
         "23-24 Oct fixtures, game ids and two published DraftKings moneylines; read 2026-10-23 ~21:30Z"),
        ("nhl-sched25-quest", "NHL", NHL_SCHED25_URL,
         "25-26 Oct fixtures 2026020180-0187 with EDT starts; read 2026-10-23 ~21:30Z"),
        ("nba-games-quest", "NBA", "https://www.nba.com/games",
         "Calendar counts (8 games 24 Oct, 7 on 25 Oct); fixture list did not render — flag Q-COV1"),
        ("nhl-teams-quest", "NHL stats API", NHL_STATS_URL,
         "Team GP/GF/GA/W/L/OTL/Pts snapshot via brief capture 2026-10-23T16:30Z (stats-API view)"),
    ]:
        sources[url] = {"key": key, "publisher": pub, "url": url, "what": what,
                        "captured_utc": CUTOFF, "desks": ["quest"]}

    # ---- flagged -----------------------------------------------------------
    cad_flags = load("data/cadence/flagged.json")["flags"]
    flags = [{**f, "carried_from": "cadence"} for f in cad_flags]
    flags += [
        {"id": "Q-TZ1", "severity": "medium", "category": "Start times",
         "item": "Nine start times converted on an inferred viewer zone",
         "finding": "Six Cricket Australia rows and three Gallagher PREM rows were captured with 'viewer-local' clocks and no named zone. They are converted here as America/New_York because all nine land on orthodox venue starts under that reading (for example Newlands 10:30 SAST, Hagley Oval 20:00 NZDT, Leicester 15:05 BST) and on implausible ones otherwise. The inference is marked on every affected row (time_status viewer-zone-inferred) and needs review against the capturing browser's settings.",
         "source_url": "https://www.cricket.com.au/matches?isCompleted=0&year=2026",
         "status": "needs review"},
        {"id": "Q-TZ2", "severity": "medium", "category": "Start times",
         "item": "26 fixtures carry a calendar date only",
         "finding": "EuroLeague game-centre times, WST site-clock times, URC 'local' times, two 'Followed by' tennis slots, one EuroLeague TBC, two golf moving days, two greyhound evening cards and the Formula 1 title outright have no resolvable clock basis in the stored captures. start_utc is left blank on those rows; only the date is asserted. Nothing was converted on a guess.",
         "source_url": "https://www.wst.tv/matches/", "status": "needs review"},
        {"id": "Q-OLBG1", "severity": "high", "category": "OLBG inventory",
         "item": "OLBG event tables are not readable without a browser",
         "finding": "Both OLBG pages re-read first-hand on 2026-10-23 (~21:30Z) returned the literal text 'No tips found' where the event table renders client-side, so a complete server-side OLBG event inventory still cannot be captured. Fixtures therefore come from each governing body and are joined to OLBG at sport level. Only 2 of 93 cadence fixtures carry an OLBG event id, and one of them (gaa-cork-psfc, id 14) reads like a sport id rather than an event id — that value needs review before any event-level join is trusted.",
         "source_url": "https://www.olbg.com/betting-tips", "status": "needs review"},
        {"id": "Q-MKT1", "severity": "high", "category": "Market cross-check",
         "item": "One originated favourite disagrees with the only observed market price",
         "finding": "NHL.com published DraftKings moneylines for the two 23 October NHL games when re-read on 2026-10-23: Montreal -170 at Chicago +142, and Tampa Bay +105 at Colorado -125. The first agrees in direction with this board (Montreal), the second does not: the board's Tampa Bay pick (72.4%) opposes the market favourite Colorado. The disagreement is disclosed, not smoothed over, and no bookmaker price was used as a pricing input anywhere on this board. Saturday prices were not yet published on NHL.com at read time, so all other observed-price cells stay blank.",
         "source_url": "https://www.nhl.com/schedule", "status": "needs review"},
        {"id": "Q-COV1", "severity": "medium", "category": "Coverage",
         "item": "Saturday's NBA slate is not listed",
         "finding": "NBA.com's calendar shows 8 games on 24 October and 7 on 25 October, but the fixture list itself failed to render for capture ('Sorry, something went wrong') on 2026-10-23. Those games are not listed here rather than sourced from a non-official listing. The 12 NBA rows on this board are the 23 October (US) games from the cadence capture, tipping from 23:00Z.",
         "source_url": "https://www.nba.com/games", "status": "needs review"},
        {"id": "Q-COV2", "severity": "medium", "category": "Coverage",
         "item": "NHL coverage stops at 26 October",
         "finding": "NHL.com's week strip shows further NHL slates inside the board's window (11 games on 27 October, 4 on 28 October, 11 on 29 October) that neither source capture holds with team inputs. They are omitted, not half-priced. The next refresh should capture them with a fresh standings snapshot.",
         "source_url": NHL_SCHED25_URL, "status": "needs review"},
        {"id": "Q-DQ1", "severity": "medium", "category": "Data conventions",
         "item": "Two official NHL goal conventions meet on one board",
         "finding": "The cadence rows price from the NHL standings feed, which counts the shootout-deciding goal; the added NHL rows price from the NHL stats-API team summary via the brief capture, which does not (for example Montreal 30 goals for in one feed, 28 in the other, over the same nine games). Every Ice Hockey row links the exact feed its inputs came from. Prices across the two groups are comparable in method but not identical in input convention.",
         "source_url": NHL_STATS_URL, "status": "needs review"},
        {"id": "Q-BLANK", "severity": "medium", "category": "Unpriced fixtures",
         "item": "Fixtures listed without a line",
         "finding": "Every unpriced fixture states its reason on its own row: missing comparative inputs (snooker ranking money, EHF Champions League strengths, darts order-of-merit pairs) in the cadence capture, and four added NHL fixtures involving clubs with no stored inputs (Florida, NY Islanders, Dallas, Winnipeg, Vancouver). Blank means blank: no price, probability or favourite was inferred for them.",
         "source_url": "https://www.wst.tv/rankings/", "status": "needs review"},
        {"id": "Q-INJ", "severity": "low", "category": "Availability news",
         "item": "Only the NBA publishes a readable official availability feed here",
         "finding": "NBA rows link the league's own 23 October injury report PDF. No other sport on this board has a readable official injury or team-news feed in the stored captures, and no written prediction on this board asserts that any individual player is injured or unavailable. Line-up-sensitive prices (NBA especially, on a one-to-two-game sample) should be re-checked against the linked report before use.",
         "source_url": "https://official.nba.com/nba-injury-report-2026-27-season/",
         "status": "needs review"},
        {"id": "Q-CONF", "severity": "medium", "category": "Confidence labels",
         "item": "Confidence is a probability band, not a calibrated strike rate",
         "finding": "High means an originated probability of at least 70% from the stored inputs on the row (with the cadence tier caps preserved); medium at least 60%. The engines behind the two source captures have not been backtested on settled results inside this repository, NBA prices rest on a league-average prior after one or two games, and golf, greyhound and Gaelic rows carry low-confidence labels throughout. Treat the labels as a transparency device, not as a promise.",
         "source_url": "https://www.nba.com/standings", "status": "needs review"},
    ]

    meta = {"desk": "quest", "session": SESSION, "cutoff_utc": CUTOFF,
            "generated_from": ["data/cadence (2026-10-23T20:05Z)",
                               "data/brief NHL (2026-10-23T16:30Z)",
                               "NHL.com read 2026-10-23 ~21:30Z"],
            "fixtures": len(fixtures),
            "priced": sum(1 for f in fixtures if f["status"] == "priced"),
            "blank": sum(1 for f in fixtures if f["status"] == "blank"),
            "lines": len(lines), "picks": len(picks),
            "predictions": len(predictions), "sources": len(sources),
            "flags": len(flags),
            "band": {"low": -250, "high": 10000,
                     "note": "fair -250 is 71.43%; high (>=70%) and the band meet only in 70.00-71.43%"},
            "league_gpg_nhl": round(league_gpg, 4),
            "olbg_taxonomy": {s: {"id": OLBG[s][0], "url": OLBG[s][1]} for s in SPORTS15}}
    dump("fixtures.json", {"meta": meta, "fixtures": fixtures})
    dump("lines.json", {"meta": meta, "lines": lines})
    dump("picks.json", {"meta": meta, "picks": picks})
    dump("top5.json", {"meta": meta, "top5": top5})
    dump("predictions.json", {"meta": meta, "predictions": predictions})
    dump("sources.json", {"meta": meta, "sources": sorted(sources.values(), key=lambda s: s["key"])})
    dump("flagged.json", {"meta": meta, "flags": flags})
    print(f"fixtures={len(fixtures)} priced={meta['priced']} blank={meta['blank']} "
          f"lines={len(lines)} picks={len(picks)} predictions={len(predictions)} "
          f"sources={len(sources)} flags={len(flags)} league_gpg={league_gpg:.3f}")
    if missing_prose:
        raise SystemExit("Refusing to finish: in-band high picks lack prose (see above).")


if __name__ == "__main__":
    main()
