#!/usr/bin/env python3
"""Daily Top-5 desk seed (session arena/b499dfe1-olbg2).

Builds the upcoming-fixture pool (2026-10-23..2026-10-30) ONLY from official
sources captured in this repository on 2026-10-22 (data/verified/inputs.json,
data/current/capture/*.json) plus fresh confirmations fetched by this session
on 2026-10-22 from api-web.nhle.com, statsapi.mlb.com and olbg.com
(recorded in research/daily-b499dfe1.md). No value is inferred: fixtures or
inputs that are not in an official capture are left out and flagged.
Excluded by brief: soccer/football, boxing, UFC/MMA, american football,
hurling, Horse Racing, cycling, specials.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "daily")
os.makedirs(OUT, exist_ok=True)
WIN = ("2026-10-23", "2026-10-30")

def load(*p):
    with open(os.path.join(ROOT, *p)) as f: return json.load(f)

def inwin(d): return bool(d) and WIN[0] <= d <= WIN[1]

V = load("data", "verified", "inputs.json")
VS = load("data", "verified", "sports.json")
VM = load("data", "verified", "matches.json")["matches"]
fixtures, sources = [], {}

def src(sid, name, url, captured="2026-10-22", note=""):
    sources[sid] = {"id": sid, "name": name, "url": url, "captured": captured, "note": note}

# ---------- NHL: current capture score feeds + team summary ----------
src("nhl-score", "NHL official score API (api-web.nhle.com)", "https://api-web.nhle.com/v1/score/2026-10-24",
    note="Fresh re-fetch by this session 2026-10-22 confirmed 23 Oct (2 games) and 24 Oct (12 games) FUT state, records and team leaders match the repo capture files.")
src("nhl-summary", "NHL Stats REST team summary", "https://api-web.nhle.com/v1/standings/2026-10-22",
    note="Standings endpoint re-fetched 2026-10-22; GP/W/L/OTL/GF/GA agree with data/current/capture/nhl_team_summary_2026-10-22.json.")
nhl_teams = {t["abbrev"]: t for t in load("data", "current", "capture", "nhl_team_summary_2026-10-22.json")["teams"]}
for fn in ["nhl_score_2026-10-23.json", "nhl_score_2026-10-24.json"]:
    cap = load("data", "current", "capture", fn)
    for g in cap["games"]:
        gdate = g.get("game_date") or g.get("gameDate", "")
        if not inwin(gdate): continue
        h, a = g["home"]["abbrev"], g["away"]["abbrev"]
        leaders = {}
        for ld in g.get("team_leaders") or g.get("leaders", []):
            leaders.setdefault(ld["team"], {})[ld["category"]] = {"player": ld["player"], "value": ld["value"]}
        gid = g.get("game_id") or g.get("id")
        gurl = g.get("official_url") or g.get("gameCenterLink", "")
        fixtures.append({
            "id": f"nhl-{gid}", "sport": "ice-hockey", "competition": "NHL Regular Season 2026-27",
            "date": gdate, "start_utc": g.get("start_time_utc") or g.get("startTimeUTC", ""), "venue": g.get("venue", ""),
            "home": nhl_teams[h]["team"], "away": nhl_teams[a]["team"], "home_code": h, "away_code": a,
            "official_url": gurl, "source_id": "nhl-score", "family": "poisson",
            "inputs": {"home": nhl_teams[h], "away": nhl_teams[a], "leaders": leaders,
                       "home_record": g["home"].get("record", ""), "away_record": g["away"].get("record", "")}})

# ---------- NBA + EuroLeague (verified inputs) ----------
src("nba", "NBA official schedule & 2025-26 standings (nba.com)", "https://www.nba.com/standings?Season=2025-26",
    note="Current-season records were 0-0 at capture; prior-season records are the only verified performance input. OLBG front page re-fetched 2026-10-22 lists CLE@PHI and DEN@OKC 'Today', corroborating opening-week capture.")
for fx in V["nba_fixtures"]:
    if not inwin(fx["date"]): continue
    h, a = V["nba_teams"][fx["home"]], V["nba_teams"][fx["away"]]
    fixtures.append({
        "id": f"nba-{fx['game_id']}", "sport": "basketball", "competition": "NBA Regular Season 2026-27",
        "date": fx["date"], "start_utc": fx.get("tip_et", "") + " ET", "venue": fx.get("venue", ""),
        "home": h["name"], "away": a["name"], "home_code": fx["home"], "away_code": fx["away"],
        "official_url": f"https://www.nba.com/game/{fx['away'].lower()}-vs-{fx['home'].lower()}-{fx['game_id']}",
        "source_id": "nba", "family": "nba_prior",
        "inputs": {"home": h, "away": a}})

src("euroleague", "EuroLeague Basketball official game centre & standings", "https://www.euroleaguebasketball.net/en/euroleague/standings/")
for fx in V["euroleague_fixtures"]:
    if not inwin(fx["date"]): continue
    h, a = V["euroleague_teams"][fx["home"]], V["euroleague_teams"][fx["away"]]
    fixtures.append({
        "id": fx["id"], "sport": "basketball", "competition": "EuroLeague 2026-27 Regular Season",
        "date": fx["date"], "start_utc": fx.get("time", ""), "venue": fx.get("venue", ""),
        "home": h["name"], "away": a["name"], "home_code": fx["home"], "away_code": fx["away"],
        "official_url": fx["url"], "source_id": "euroleague", "family": "margin",
        "inputs": {"home": h, "away": a}})

# ---------- Rugby Union: Top14, Pro D2, URC ----------
src("lnr", "Ligue Nationale de Rugby official tables & fixtures (Top 14 / Pro D2)", "https://top14.lnr.fr/classement")
src("urc", "United Rugby Championship official match centre & table", "https://www.unitedrugby.com/match-centre")
for comp, tk, fk, sid in [("Top 14 2026-27", "top14_teams", "top14_fixtures", "lnr"),
                          ("Pro D2 2026-27", "prod2_teams", "prod2_fixtures", "lnr")]:
    for fx in V[fk]:
        if not inwin(fx["date"]): continue
        h, a = V[tk][fx["home"]], V[tk][fx["away"]]
        fixtures.append({
            "id": fx["id"], "sport": "rugby-union", "competition": comp, "date": fx["date"],
            "start_utc": fx.get("time", ""), "venue": "", "home": h["name"], "away": a["name"],
            "home_code": fx["home"], "away_code": fx["away"], "official_url": fx["url"],
            "source_id": sid, "family": "margin", "inputs": {"home": h, "away": a}})
urc_r3 = {r.get("home", ""): r for r in load("data", "current", "capture", "urc_table_2026-10-22.json").get("round3_results", [])}
for rnd, fk in [("Round 4", "urc_r4_fixtures"), ("Round 5", "urc_r5_fixtures")]:
    for fx in V[fk]:
        if not inwin(fx["date"]): continue
        h, a = V["urc_teams"][fx["home"]], V["urc_teams"][fx["away"]]
        fixtures.append({
            "id": fx["id"], "sport": "rugby-union", "competition": f"United Rugby Championship 2026-27 {rnd}",
            "date": fx["date"], "start_utc": fx.get("time", ""), "venue": fx.get("venue", ""),
            "home": h["name"], "away": a["name"], "home_code": fx["home"], "away_code": fx["away"],
            "official_url": fx["url"], "source_id": "urc", "family": "margin",
            "inputs": {"home": h, "away": a}})

# ---------- Handball: EHF (verified + current capture adds 28/29 Oct) ----------
src("ehf", "EHF Champions League Men official matches & standings", "https://ehfcl.eurohandball.com/men/2026-27/matches/")
ehf_by_name = {t["name"]: t for t in load("data", "current", "capture", "ehf_standings_2026-10-22.json")["clubs"]} if False else {}
seen_ehf = set()
cur = load("data", "current", "matches.json")["matches"]
for m in cur:
    if m["sport"] == "handball" and inwin(m["date"]):
        key = (m["home"]["name"], m["away"]["name"], m["date"])
        if key in seen_ehf: continue
        seen_ehf.add(key)
        inp = m.get("inputs", {})
        fixtures.append({
            "id": m["id"], "sport": "handball", "competition": m["competition"], "date": m["date"],
            "start_utc": m.get("time_note", ""), "venue": m.get("venue", ""),
            "home": m["home"]["name"], "away": m["away"]["name"], "home_code": "", "away_code": "",
            "official_url": m["official_url"], "source_id": "ehf", "family": "poisson_handball",
            "inputs": {"home": {"name": m["home"]["name"], "gp": inp.get("home_gp"), "gf": inp.get("home_for"), "ga": inp.get("home_against"), "record": m["home"].get("record", "")},
                       "away": {"name": m["away"]["name"], "gp": inp.get("away_gp"), "gf": inp.get("away_for"), "ga": inp.get("away_against"), "record": m["away"].get("record", "")},
                       "standings_url": inp.get("standings_url", "")}})

# ---------- Darts: PDC European Championship ----------
src("pdc", "PDC official Werner Rankings Ladder & European Championship draw", "https://www.pdc.tv/rankings",
    note="OLBG front page re-fetched 2026-10-22 lists 'Ryan Joyce vs Jermaine Wattimena, Tomorrow 13:15, Win Match 2-way' (event 32332), corroborating the 23 Oct Round 1 capture.")
for fx in V["darts_fixtures"]:
    if not inwin(fx["date"]): continue
    p1, p2 = V["pdc_players"].get(fx["p1"]), V["pdc_players"].get(fx["p2"])
    if not p1 or not p2: continue
    fixtures.append({
        "id": fx["id"], "sport": "darts", "competition": "PDC European Championship 2026 — Round 1 (best of 11 legs)",
        "date": fx["date"], "start_utc": fx.get("time", ""), "venue": "",
        "home": fx["p1"], "away": fx["p2"], "home_code": "", "away_code": "",
        "official_url": "https://www.pdc.tv/rankings", "olbg_url": fx.get("olbg_url", ""),
        "source_id": "pdc", "family": "darts",
        "inputs": {"home": {"name": fx["p1"], **p1}, "away": {"name": fx["p2"], **p2}}})

# ---------- Baseball: MLB World Series (fresh-confirmed) ----------
src("mlb", "MLB Stats API official schedule & standings (statsapi.mlb.com)",
    "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-29",
    note="Re-fetched by this session 2026-10-22: Games 1-5, gamePk 849805/849802/849804/849803/849799 (Game 5 if-necessary), venues American Family Field / Tropicana Field, all 'Scheduled'.")
mlb_extra = [{"id": "mlb-849799", "game_pk": 849799, "official_date": "2026-10-28", "game_date_utc": "2026-10-29T00:00:00Z",
              "away": "MIL", "home": "TB", "venue": "Tropicana Field", "description": "World Series Game 5 (if necessary)",
              "human_url": "https://www.mlb.com/gameday/849799"}]
# league sample for run-environment (runs/team/game) from official capture
sample = load("data", "current", "capture", "mlb_standings_sample_2026-10-22.json")
for fx in list(V["mlb_fixtures"]) + mlb_extra:
    if not inwin(fx["official_date"]): continue
    h, a = V["mlb_teams"][fx["home"]], V["mlb_teams"][fx["away"]]
    fixtures.append({
        "id": fx["id"], "sport": "baseball", "competition": f"MLB World Series 2026 — {fx['description']}",
        "date": fx["official_date"], "start_utc": fx.get("game_date_utc", ""), "venue": fx.get("venue", ""),
        "home": h["name"], "away": a["name"], "home_code": fx["home"], "away_code": fx["away"],
        "official_url": fx["human_url"], "source_id": "mlb", "family": "poisson_baseball",
        "inputs": {"home": h, "away": a, "league_runs_pg": sample.get("league_avg_runs_per_game")}})

# ---------- Motor Racing: F1 United States GP outright ----------
f1cap = load("data", "current", "capture", "f1_calendar_2026-10-22.json")
src("f1", "Formula1.com official 2026 calendar & driver standings", f1cap.get("source_url_drivers", "https://www.formula1.com/en/results/2026/drivers"))
nxt = f1cap.get("next_round", {})
# Official capture renders weekend "23 - 25 OCT" R18 United States; race day = final day (disclosed).
f1_date = "2026-10-25"
if inwin(f1_date) and f1cap.get("drivers_standings"):
    fixtures.append({
        "id": "f1-us-gp-2026", "sport": "motor-racing",
        "competition": "FIA Formula One World Championship 2026 - United States Grand Prix (Round 18; weekend rendered 23-25 Oct on formula1.com)",
        "date": f1_date, "start_utc": "", "venue": "",
        "home": "United States Grand Prix", "away": "", "home_code": "", "away_code": "",
        "official_url": nxt.get("official_url", "https://www.formula1.com/en/racing/2026/united-states"),
        "source_id": "f1", "family": "outright",
        "inputs": {"drivers": f1cap["drivers_standings"], "winners": f1cap.get("race_winners_first_hand", []),
                   "previous_round": f1cap.get("previous_round", {})}})

# ---------- Unlined official fixtures (blank lines, honest reasons) ----------
REASONS = {
 "volleyball": "No verified performance input (set/point rates) was captured from the official PlusLiga pages read; line left blank rather than inferred.",
 "cricket": "Official ICC fixture verified, but no verified team-strength input (rankings table rendered empty in capture) — line left blank.",
 "golf": "Tournament field verified on the official tour site; no verified player-form input captured — outright lines left blank.",
 "rugby-league": "Futures market catalogued on OLBG; no verified 2027 squad/performance input from nrl.com captured — line left blank.",
 "gaelic-football": "County club fixture catalogued on OLBG; county-board performance data not captured from an official source — line left blank.",
 "greyhounds": "GBGB Category One race date verified from the official 2026 schedule; confirmed runners/form not published in the official capture — line left blank.",
 "tennis": "No upcoming fixture with both players' official ranking inputs was server-rendered in the ATP/WTA captures — no row originated.",
 "snooker": "Northern Ireland Open Round 3 was played 2026-10-22; next-round pairings were not published in the official WST capture at seed time — no pairing invented.",
 "aussie-rules": "AFL off-season after the Grand Final; the official fixture page lists no match in the window.",
 "esports": "LoL Worlds 2026 is listed on lolesports.com, but dated upcoming match pairings were not server-rendered in the capture read 2026-10-22 — no pairing invented.",
}
unlined = []
for m in VM:
    if m.get("line_status") == "originated": continue
    if not inwin(m.get("date")): continue
    unlined.append({"id": m["id"], "sport": m["sport"], "competition": m.get("competition", ""),
                    "date": m["date"], "home": m.get("home", ""), "away": m.get("away", ""),
                    "official_url": m.get("official_url", ""), "source_name": m.get("official_source", ""),
                    "blank_reason": REASONS.get(m["sport"], "No verified origination input captured — line left blank.")})

sports = []
for s in VS["eligible_sports"]:
    sports.append({"slug": s["slug"], "name": s["name"], "olbg_sport_id": s.get("olbg_sport_id"),
                   "olbg_url": s.get("olbg_url", ""), "official_url": s.get("official_url", ""),
                   "markets_investigated": s.get("markets_investigated", [])})
src("olbg", "OLBG.com betting-tips hub (taxonomy & market labels only; OLBG publishes no prices used here)",
    "https://www.olbg.com/betting-tips", note="Re-fetched 2026-10-22. URL schema /betting-tips/{Sport}/{SportId} and event pages ...?event_id={id}; markets seen include Money Line, Win Match 2-way, Full Time Result (excluded sports ignored).")

fixtures.sort(key=lambda r: (r["sport"], r["date"], r["id"]))
json.dump({"layer": "daily", "session": "arena/b499dfe1-olbg2", "captured_at": "2026-10-22",
           "window": list(WIN), "count": len(fixtures), "fixtures": fixtures},
          open(os.path.join(OUT, "fixtures.json"), "w"), indent=1)
json.dump({"sports": sports, "excluded": VS.get("excluded_sports", [])},
          open(os.path.join(OUT, "sports.json"), "w"), indent=1)
json.dump({"sources": list(sources.values())}, open(os.path.join(OUT, "sources.json"), "w"), indent=1)
json.dump({"unlined": unlined, "zero_row_reasons": REASONS}, open(os.path.join(OUT, "unlined.json"), "w"), indent=1)
print(f"fixtures={len(fixtures)} unlined={len(unlined)} sports={len(sports)} sources={len(sources)}")
