#!/usr/bin/env python3
"""Build the live desk model from first-hand captures.

Input  : data/live_desk/captures/manifest.json + raw bodies (scripts/livedesk_collect.py)
Output : data/live_desk/model.json   compact, committed; the site is built from this only
         data/live_desk/digest.json  per-sport coverage + every failed read

Scope rule
----------
A fixture exists only if OLBG lists it.  The governing-body pages confirm an OLBG fixture;
they never invent one.  A fixture whose participants cannot be found in an official capture
is published with ``official_verified: false`` and appears on the review page.

Price rule
----------
The OLBG decimal is the price OLBG quoted for the selection it tips.  It is kept as a
reference and is never presented as our line.  Our number comes from scripts/livedesk_ratings.py
and carries a ``basis`` and a ``tier`` on every row.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import livedesk_ratings as R  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAP = ROOT / "data" / "live_desk" / "captures"
RAW = CAP / "raw"
OUT = ROOT / "data" / "live_desk" / "model.json"
DIGEST = ROOT / "data" / "live_desk" / "digest.json"

BRIEF_SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
OLBG_SPORT = {"Gaelic Football": "Gaelic Sports", "Hurling": "Gaelic Sports"}
SPORT_SLUG = {s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") for s in BRIEF_SPORTS}

OBJ_START = re.compile(r'\{id:"([0-9a-f]{40})"')
FIELD_RE = re.compile(r'(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<val>"(?:[^"\\]|\\.)*"|[^,}\]]+)')

TEXT_SOURCES = {
    "Snooker": ["wst_matches", "wst_rankings", "wst_tournaments"],
    "Darts": ["pdc_tournaments", "pdc_oom", "pdc_euro"],
    "Tennis": ["wta_scores", "wta_rankings", "wta_tournaments"],
    "Cricket": ["ca_upcoming", "icc_odi", "icc_t20"],
    "Rugby Union": ["urc_matchcentre", "prem_fixtures", "prem_table"],
    "Rugby League": ["rlwc_fixtures", "nrl_draw", "superleague"],
    "Handball": ["ehf_calendar", "lnh", "asobal"],
    "Volleyball": ["cev_club", "volleyballworld", "plusliga"],
    "Golf": ["dpwt_schedule", "dpwt_leaderboard", "pga_schedule"],
    "Greyhounds": ["gbgb_racing", "gbgb_results", "gbgb_open"],
    "Gaelic Sports": ["gaa_fixtures", "gaa_club", "gaa_hurling"],
    "Motor Racing": ["f1_calendar", "f1_standings"],
}


# --------------------------------------------------------------------------- helpers
def load_manifest() -> tuple[dict, str]:
    m = json.loads((CAP / "manifest.json").read_text(encoding="utf-8"))
    return {c["key"]: c for c in m["captures"]}, m["captured_at"]


def body(key: str, caps: dict) -> str:
    cap = caps.get(key)
    if not cap or cap.get("http_status") != 200 or not cap.get("stored"):
        return ""
    path = RAW / cap["stored"]
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def as_json(key: str, caps: dict):
    try:
        return json.loads(body(key, caps))
    except ValueError:
        return None


def as_xml(key: str, caps: dict):
    text = body(key, caps)
    if not text.strip().startswith("<"):
        return None
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return None


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&#39;", "'").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text)


def plain(key: str, caps: dict) -> str:
    return strip_tags(body(key, caps))


def unquote(v: str):
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1].replace('\\"', '"')
    if v in ("null", "void 0", "undefined"):
        return None
    if v == "true":
        return True
    if v == "false":
        return False
    try:
        return json.loads(v)
    except ValueError:
        return v


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def surname(name: str) -> str:
    parts = (name or "").split()
    return parts[-1] if parts else ""


# --------------------------------------------------------------------------- OLBG listing
def olbg_tips(caps: dict):
    tips: dict[tuple, dict] = {}
    pages: dict[str, dict] = {}
    for key, cap in sorted(caps.items()):
        if not key.startswith("olbg_hub_"):
            continue
        text = body(key, caps)
        pages[key] = {"status": cap.get("http_status"), "objects": 0,
                      "url": cap.get("url"), "captured_at": cap.get("requested_at"),
                      "bytes": cap.get("bytes"), "sha256": cap.get("sha256"),
                      "truncated": cap.get("truncated")}
        if not text:
            continue
        count = 0
        for m in OBJ_START.finditer(text):
            chunk = text[m.start(): m.start() + 4000]
            fields: dict = {}
            for f in FIELD_RE.finditer(chunk):
                fields.setdefault(f.group("key"), unquote(f.group("val")))
            event = fields.get("event_name_alias")
            if not event:
                continue
            count += 1
            sport = (fields.get("sport") or "").replace("_", " ")
            if not sport:
                mm = re.search(r"/betting-tips/([A-Za-z_]+)/", (fields.get("eventUrl") or ""))
                sport = mm.group(1).replace("_", " ") if mm else ""
            sport = OLBG_SPORT.get(sport, sport)
            eid = ""
            mm = re.search(r"event_id=(\d+)", fields.get("eventUrl") or "")
            if mm:
                eid = mm.group(1)
            start = ""
            ts = fields.get("event_start_unix_timestamp")
            if ts:
                try:
                    start = dt.datetime.fromtimestamp(int(float(ts)), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, OSError):
                    start = ""
            url = fields.get("eventUrl") or ""
            if url.startswith("/"):
                url = "https://www.olbg.com" + url
            row = {
                "sport": sport,
                "competition": fields.get("menu_league") or fields.get("tournament") or "",
                "event": event,
                "event_id": eid,
                "start_utc": start,
                "selection": fields.get("selection") or "",
                "market": fields.get("market_alias") or fields.get("market_name") or "",
                "decimal": str(fields.get("odds") or ""),
                "american": str(fields.get("american_odds") or ""),
                "olbg_confidence": fields.get("confidence"),
                "win_tips": fields.get("win_tips"),
                "expired": str(fields.get("expired") or ""),
                "event_url": url,
                "listing_url": cap.get("url"),
                "captured_at": cap.get("requested_at"),
            }
            k = (sport, norm(event), row["market"], row["selection"])
            if k not in tips or (row["captured_at"] or "") > (tips[k]["captured_at"] or ""):
                tips[k] = row
        pages[key]["objects"] = count
    return sorted(tips.values(), key=lambda r: (r["start_utc"], r["sport"], r["event"])), pages


# --------------------------------------------------------------------------- official: NHL
def nhl_official(caps: dict) -> dict:
    games = {}
    for key in caps:
        if not key.startswith("ieh_sched"):
            continue
        data = as_json(key, caps)
        if not data:
            continue
        for day in data.get("gameWeek", []):
            for g in day.get("games", []):
                gid = g.get("id")
                if not gid:
                    continue
                home, away = g.get("homeTeam", {}), g.get("awayTeam", {})
                games[f"nhl-{gid}"] = {
                    "fixture_id": f"nhl-{gid}",
                    "home": (home.get("placeName") or {}).get("default", ""),
                    "home_name": (home.get("commonName") or {}).get("default", ""),
                    "home_abbrev": home.get("abbrev", ""),
                    "away": (away.get("placeName") or {}).get("default", ""),
                    "away_name": (away.get("commonName") or {}).get("default", ""),
                    "away_abbrev": away.get("abbrev", ""),
                    "start_utc": g.get("startTimeUTC", ""),
                    "venue": (g.get("venue") or {}).get("default", ""),
                    "state": g.get("gameState", ""),
                    "source_key": key,
                    "source_url": caps[key].get("final_url") or caps[key].get("url"),
                    "captured_at": caps[key].get("requested_at"),
                }
    standings = {}
    data = as_json("ieh_standings", caps)
    if data:
        for row in data.get("standings", []):
            ab = (row.get("teamAbbrev") or {}).get("default", "")
            standings[ab] = {
                "team": (row.get("teamName") or {}).get("default", ""),
                "gp": row.get("gamesPlayed"), "w": row.get("wins"), "l": row.get("losses"),
                "otl": row.get("otLosses"), "pts": row.get("points"),
                "gf": row.get("goalFor"), "ga": row.get("goalAgainst"),
                "l10": f"{row.get('l10Wins')}-{row.get('l10Losses')}-{row.get('l10OtLosses')}",
                "l10_pts": row.get("l10Points"),
                "streak": f"{row.get('streakCode','')}{row.get('streakCount','')}",
                "home": f"{row.get('homeWins')}-{row.get('homeLosses')}-{row.get('homeOtLosses')}",
                "road": f"{row.get('roadWins')}-{row.get('roadLosses')}-{row.get('roadOtLosses')}",
            }
    return {"games": games, "standings": standings,
            "standings_url": caps.get("ieh_standings", {}).get("final_url") or caps.get("ieh_standings", {}).get("url"),
            "standings_captured_at": caps.get("ieh_standings", {}).get("requested_at"),
            "standings_sha": caps.get("ieh_standings", {}).get("sha256")}


# --------------------------------------------------------------------------- official: MLB
def mlb_official(caps: dict) -> dict:
    games = {}
    data = as_json("mlb_sched", caps)
    if data:
        for day in data.get("dates", []):
            for g in day.get("games", []):
                pk = g.get("gamePk")
                home, away = g["teams"]["home"], g["teams"]["away"]
                games[f"mlb-{pk}"] = {
                    "fixture_id": f"mlb-{pk}",
                    "home": home["team"]["name"], "away": away["team"]["name"],
                    "start_utc": g.get("gameDate", ""),
                    "venue": (g.get("venue") or {}).get("name", ""),
                    "state": (g.get("status") or {}).get("detailedState", ""),
                    "description": g.get("description") or g.get("seriesDescription") or "",
                    "home_record": f"{home.get('leagueRecord',{}).get('wins','')}-{home.get('leagueRecord',{}).get('losses','')}",
                    "away_record": f"{away.get('leagueRecord',{}).get('wins','')}-{away.get('leagueRecord',{}).get('losses','')}",
                    "home_pitcher": (home.get("probablePitcher") or {}).get("fullName", ""),
                    "away_pitcher": (away.get("probablePitcher") or {}).get("fullName", ""),
                    "source_key": "mlb_sched",
                    "source_url": caps["mlb_sched"].get("final_url") or caps["mlb_sched"].get("url"),
                    "captured_at": caps["mlb_sched"].get("requested_at"),
                }
    stats = {}
    for key, group in (("mlb_hitting", "hitting"), ("mlb_pitching", "pitching")):
        data = as_json(key, caps)
        if not data:
            continue
        for s in data.get("stats", []):
            name = (s.get("team") or {}).get("name", "")
            splits = s.get("splits", [{}])
            st = splits[0].get("stat", {}) if splits else {}
            entry = stats.setdefault(name, {})
            if group == "hitting":
                entry.update({"avg": st.get("avg"), "runs": st.get("runs"), "hr": st.get("homeRuns"),
                              "ops": st.get("ops"), "gp": st.get("gamesPlayed"),
                              "ra": st.get("runs")})
            else:
                entry.update({"era": st.get("era"), "whip": st.get("whip"),
                              "ra": st.get("runs"), "era_gp": st.get("gamesPlayed")})
    return {"games": games, "team_stats": stats,
            "source_url": caps.get("mlb_sched", {}).get("final_url"),
            "captured_at": caps.get("mlb_sched", {}).get("requested_at")}


# --------------------------------------------------------------------------- official: EuroLeague
def euroleague_official(caps: dict) -> dict:
    """EuroLeague serves its schedule and standings as XML, with venue-local tip times."""
    games = {}
    for key in ("el_sched8", "el_sched9"):
        root = as_xml(key, caps)
        if root is None:
            continue
        for item in root.findall("item"):
            code = (item.findtext("gamecode") or "").strip()
            date = (item.findtext("date") or "").strip()
            start = (item.findtext("startime") or "").strip()[:5]
            local = f"{date} {start}".strip()
            games[f"el-{code}"] = {
                "fixture_id": f"el-{code}",
                "home": (item.findtext("hometeam") or "").strip(),
                "away": (item.findtext("awayteam") or "").strip(),
                "start_local": local,
                "start_utc": "",
                "time_basis": "venue-local tip time exactly as the league serves it; not converted",
                "round": (item.findtext("gameday") or "").strip(),
                "venue": (item.findtext("arenaname") or "").strip(),
                "source_key": key,
                "source_url": caps[key].get("final_url") or caps[key].get("url"),
                "captured_at": caps[key].get("requested_at"),
                "official_url": f"https://www.euroleaguebasketball.net/euroleague/game-center/{code}/",
            }
    standings = {}
    root = as_xml("el_standings", caps)
    if root is not None:
        for team in root.iter("team"):
            name = (team.findtext("name") or "").strip()
            if not name:
                continue
            standings[name.upper()] = {
                "w": int(team.findtext("wins") or 0), "l": int(team.findtext("losses") or 0),
                "pf": int(team.findtext("ptsfavour") or 0), "pa": int(team.findtext("ptsagainst") or 0),
                "pos": int(team.findtext("ranking") or 0), "gp": int(team.findtext("totalgames") or 0),
            }
    return {"games": games, "standings": standings,
            "standings_url": caps.get("el_standings", {}).get("final_url"),
            "standings_captured_at": caps.get("el_standings", {}).get("requested_at")}


# --------------------------------------------------------------------------- text corpora
def text_corpus(sport: str, caps: dict) -> tuple[str, list[dict]]:
    parts, used = [], []
    for key in TEXT_SOURCES.get(sport, []):
        text = body(key, caps)
        if not text:
            continue
        p = strip_tags(text)
        parts.append(" " + p + " ")
        cap = caps[key]
        used.append({"key": key, "url": cap.get("final_url") or cap.get("url"),
                     "captured_at": cap.get("requested_at"), "chars": len(p),
                     "sha256": (cap.get("sha256") or "")[:16]})
    return norm(" ".join(parts)), used



STOP = {"fc", "bc", "sc", "the", "club", "de", "cf", "ac", "bk", "hc", "if", "ik", "sk"}


def name_in(official_name: str, event_text: str) -> bool:
    """Tolerant participant match: full name, then the final token, then any long token.

    OLBG writes "TB Rays @ MIL Brewers" for Tampa Bay Rays; the official feed writes
    "Tampa Bay Rays".  A whole-string test is too strict, so the fallback compares the
    distinctive words, longest first.  The sport is already fixed, so a nickname collision
    across sports cannot happen here.
    """
    on = norm(official_name)
    ev = norm(event_text)
    if not on or not ev:
        return False
    if on in ev:
        return True
    toks = [w for w in on.split() if len(w) >= 4 and w not in STOP]
    if not toks:
        return False
    last = toks[-1]
    if last in ev.split():
        return True
    return any(w in ev.split() for w in toks)

def split_event(name: str) -> tuple[str, str]:
    for sep in (" @ ", " vs ", " v "):
        if sep in name:
            a, b = name.split(sep, 1)
            return a.strip(), b.strip()
    return name.strip(), ""


# --------------------------------------------------------------------------- main
def main() -> int:
    caps, captured_at = load_manifest()
    tips, pages = olbg_tips(caps)
    expired = [t for t in tips if t.get("expired") == "1"]
    tips = [t for t in tips if t.get("expired") != "1"]

    nhl = nhl_official(caps)
    mlb = mlb_official(caps)
    el = euroleague_official(caps)
    wta = R.wta_rankings(plain("wta_rankings", caps))
    f1 = R.f1_standings(plain("f1_standings", caps))

    review: list[dict] = []
    events: dict[str, dict] = {}
    for t in tips:
        ekey = f"{t['sport']}|{t['event_id'] or norm(t['event'])}"
        ev = events.setdefault(ekey, {
            "key": ekey, "sport": t["sport"], "competition": t["competition"],
            "name": t["event"], "olbg_event_id": t["event_id"], "start_utc": t["start_utc"],
            "olbg_url": t["event_url"], "olbg_listing_url": t["listing_url"],
            "olbg_captured_at": t["captured_at"], "tips": [],
        })
        ev["tips"].append(t)

    corpora = {s: text_corpus(s, caps) for s in TEXT_SOURCES}

    for key, ev in events.items():
        ev["home"], ev["away"] = split_event(ev["name"])
        # An OLBG event is a match unless its name is a season or tournament outright.
        # Races (greyhounds) and single-fixture events have no " v " separator but are not
        # outrights, so the test is the year/tournament wording rather than the separator.
        name_l = ev["name"].lower()
        looks_like_outright = bool(re.search(r"\b20\d\d\b", ev["name"])) or any(
            k in name_l for k in ("grand prix", "championship", "super league", "state of origin", "nrl", "series winner")
        )
        ev["kind"] = "outright" if looks_like_outright else "match"
        sport = ev["sport"]
        tip = max(ev["tips"], key=lambda t: (int(t.get("win_tips") or 0)))
        ev["primary_tip"] = {k: tip[k] for k in
                             ("selection", "market", "decimal", "american", "olbg_confidence",
                              "win_tips", "event_url", "captured_at")}
        ev["primary_tip"]["flipped"] = False
        official = None
        facts: dict = {}
        p_sel = None
        tier = "no-basis"
        detail = ""

        if sport == "Ice Hockey":
            for g in nhl["games"].values():
                if name_in(g["away_name"], ev["name"]) and name_in(g["home_name"], ev["name"]):
                    official = g
                    break
            if official:
                hs = nhl["standings"].get(official["home_abbrev"])
                as_ = nhl["standings"].get(official["away_abbrev"])
                if hs and as_:
                    p_home = R.hockey_probability(hs, as_)
                    if p_home is not None:
                        is_home = any(w in norm(tip["selection"]) for w in norm(g["home_name"]).split())
                        p_sel = R.blend(p_home if is_home else 1 - p_home, tip.get("decimal"))
                        tier, detail = "official-model", "NHL club standings blended with the quoted price"
                        facts = {
                            "home_team": official["home"], "away_team": official["away"],
                            "home_record": f"{hs['w']}-{hs['l']}-{hs['otl']}",
                            "away_record": f"{as_['w']}-{as_['l']}-{as_['otl']}",
                            "home_points": hs["pts"], "away_points": as_["pts"],
                            "home_goals_for": hs["gf"], "home_goals_against": hs["ga"],
                            "away_goals_for": as_["gf"], "away_goals_against": as_["ga"],
                            "home_last_ten": hs["l10"], "away_last_ten": as_["l10"],
                            "home_streak": hs["streak"], "away_streak": as_["streak"],
                            "home_record_at_home": hs["home"], "away_record_on_road": as_["road"],
                            "home_points_share": round(hs["pts"] / max(hs["gp"], 1), 3),
                            "away_points_share": round(as_["pts"] / max(as_["gp"], 1), 3),
                            "home_goals_per_game": round(hs["gf"] / max(hs["gp"], 1), 2),
                            "away_goals_per_game": round(as_["gf"] / max(as_["gp"], 1), 2),
                        }
        elif sport == "Baseball":
            for g in mlb["games"].values():
                if name_in(g["home"], ev["name"]) and name_in(g["away"], ev["name"]):
                    official = g
                    break
            if official:
                hs = mlb["team_stats"].get(official["home"], {})
                as_ = mlb["team_stats"].get(official["away"], {})
                p_home = R.baseball_probability(hs, as_)
                if p_home is not None:
                    is_home = any(w in norm(tip["selection"]) for w in norm(official["home"]).split())
                    p_sel = R.blend(p_home if is_home else 1 - p_home, tip.get("decimal"))
                    tier, detail = "official-model", "MLB team season splits blended with the quoted price"
                    facts = {
                        "home_team": official["home"], "away_team": official["away"],
                        "home_record": official["home_record"], "away_record": official["away_record"],
                        "home_pitcher": official["home_pitcher"], "away_pitcher": official["away_pitcher"],
                        "home_runs": hs.get("runs"), "away_runs": as_.get("runs"),
                        "home_runs_allowed": hs.get("ra"), "away_runs_allowed": as_.get("ra"),
                        "home_ops": hs.get("ops"), "away_ops": as_.get("ops"),
                        "home_era": hs.get("era"), "away_era": as_.get("era"),
                        "venue": official["venue"], "stage": official["description"],
                    }
        elif sport == "Basketball":
            for g in el["games"].values():
                if g["home"] and g["away"] and name_in(g["home"], ev["name"]) \
                        and name_in(g["away"], ev["name"]):
                    official = g
                    break
            if official:
                hs = el["standings"].get(official["home"].upper(), {})
                as_ = el["standings"].get(official["away"].upper(), {})
                p_home = R.euroleague_probability(hs, as_)
                if p_home is not None:
                    is_home = any(w in norm(tip["selection"]) for w in norm(official["home"]).split())
                    p_sel = R.blend(p_home if is_home else 1 - p_home, tip.get("decimal"))
                    tier, detail = "official-model", "EuroLeague standings blended with the quoted price"
                    facts = {
                        "home_team": official["home"], "away_team": official["away"],
                        "round": official.get("round"), "venue": official.get("venue"),
                        "home_record": f"{hs.get('w')}-{hs.get('l')}",
                        "away_record": f"{as_.get('w')}-{as_.get('l')}",
                        "home_points_for": hs.get("pf"), "home_points_against": hs.get("pa"),
                        "away_points_for": as_.get("pf"), "away_points_against": as_.get("pa"),
                        "home_position": hs.get("pos"), "away_position": as_.get("pos"),
                    }
        elif sport == "Tennis":
            player = tip["selection"]
            opponent = ev["away"] if norm(player) in norm(ev["home"]) else ev["home"]
            pk, ok = norm(player), norm(opponent)
            pr, orow = wta.get(pk), wta.get(ok)
            if pr and orow:
                p_sel = R.blend(R.tennis_probability(pr["points"], orow["points"]), tip.get("decimal"))
                tier, detail = "official-model", "WTA ranking points blended with the quoted price"
                facts = {
                    "player": pr["name"], "player_rank": pr["rank"], "player_points": pr["points"],
                    "opponent": orow["name"], "opponent_rank": orow["rank"],
                    "opponent_points": orow["points"],
                    "player_country": pr["country"], "opponent_country": orow["country"],
                }
                official = {"source_url": caps.get("wta_rankings", {}).get("final_url"),
                            "captured_at": caps.get("wta_rankings", {}).get("requested_at")}
        elif sport == "Motor Racing":
            drv = None
            for k, v in f1.items():
                if surname(tip["selection"]).lower() in k or k in norm(tip["selection"]):
                    drv = v
                    break
            if drv:
                field = [v["points"] for v in f1.values()][:20]
                p_sel = R.f1_winner_probability(drv["points"], field)
                tier, detail = "official-model", "F1 championship points, race-winner market"
                facts = {
                    "driver": drv["name"], "team": drv["team"], "position": drv["pos"],
                    "points": drv["points"], "field_size": len(field),
                    "leader_points": field[0] if field else None,
                }
                official = {"source_url": caps.get("f1_standings", {}).get("final_url"),
                            "captured_at": caps.get("f1_standings", {}).get("requested_at")}

        if p_sel is None:
            qp = R.quoted_probability(tip.get("decimal"))
            if qp is not None:
                p_sel, tier = qp, "quoted-market"
                detail = "price quoted for this selection by OLBG; no official table is captured for this competition"
        if p_sel is None:
            crowd, why = R.consensus_probability(tip.get("olbg_confidence"), tip.get("win_tips"))
            if crowd is not None:
                p_sel, tier, detail = crowd, "crowd-consensus", why
            else:
                tier, detail = "no-basis", why

        verified = bool(official)
        ev["official_verified"] = verified
        ev["official"] = official
        ev["facts"] = facts
        ev["tier"] = tier
        ev["basis_detail"] = detail
        # Two-way markets let us take the other side.  If the fixture's only quoted tip is a
        # side our own number puts below even money, the desk's selection is the opponent at
        # 1 - p, which is a line we originate rather than a price we copy.
        two_way = bool(ev["away"]) and (p_sel is not None) and (p_sel < 0.5) and sport in (
            "Ice Hockey", "Baseball", "Basketball", "Tennis", "Rugby Union", "Rugby League",
            "Cricket", "Handball", "Volleyball", "Darts", "Snooker", "Gaelic Sports")
        if two_way:
            opponent = ev["away"] if norm(tip["selection"]) in norm(ev["home"]) else ev["home"]
            if opponent:
                p_sel = round(1 - p_sel, 4)
                tip = dict(tip, selection=opponent, decimal="", american="", flipped=True)
                ev["primary_tip"].update({"selection": opponent, "decimal": "", "american": "",
                                          "flipped": True, "market": tip["market"]})
        if p_sel is None:
            ev["estimate"] = None
            ev["pick"] = None
        else:
            fair = R.american(p_sel)
            ev["estimate"] = {
                "selection": tip["selection"], "market": tip["market"],
                "probability": p_sel, "fair_american": fair,
                "fair_decimal": R.decimal_from_american(fair),
                "in_band": R.in_band(fair), "confidence": R.grade(p_sel, tier), "tier": tier,
            }
            ev["pick"] = dict(ev["estimate"], quoted_decimal=tip.get("decimal"),
                              quoted_american=tip.get("american"))
        # verification by name presence in the official corpus for sports without a feed
        corpus, used = corpora.get(sport, ("", []))
        names = [n for n in (ev["home"], ev["away"]) if n]
        seen = [n for n in names if norm(surname(n) if sport in ("Tennis", "Motor Racing") else n) in corpus]
        ev["text_check"] = {"checked": len(used), "names_found": len(seen), "of": len(names),
                            "sources": used}
        ctx = ""
        if corpus and names:
            key = norm(names[0])
            idx = corpus.find(key)
            if idx >= 0:
                window = corpus[max(0, idx - 120): idx + 160]
                ctx = re.sub(r"\s+", " ", window).strip()
        ev["official_context"] = ctx
        if not verified and not ev["official"]:
            review.append({
                "sport": sport, "event": ev["name"], "start_utc": ev["start_utc"],
                "issue": ("no official fixture feed confirmed both participants"
                          if not seen else
                          "both participants appear in the official page text, but no structured fixture feed was captured"),
                "olbg_url": ev["olbg_url"],
                "sources": [s["url"] for s in used],
            })

    out_events = sorted(events.values(), key=lambda e: (e["start_utc"] or "9999", e["sport"], e["name"]))

    # top five per sport: strongest tier first, then highest probability inside the price window
    top5: dict[str, list[dict]] = {}
    rank = {"official-model": 0, "quoted-market": 1, "crowd-consensus": 2, "no-basis": 3}
    conf_rank = {"high": 0, "medium": 1, "low": 2, None: 3}
    for sport in BRIEF_SPORTS:
        rows = [e for e in out_events if e["sport"] == sport and e.get("pick")
                and e.get("kind", "match") == "match"]
        rows.sort(key=lambda e: (rank.get(e["tier"], 3),
                                 conf_rank.get(e["pick"]["confidence"], 3),
                                 0 if e["pick"]["in_band"] else 1,
                                 -e["pick"]["probability"]))
        top5[sport] = [{"event_key": e["key"], "name": e["name"], "start_utc": e["start_utc"],
                        "selection": e["pick"]["selection"], "market": e["pick"]["market"],
                        "probability": e["pick"]["probability"], "fair_american": e["pick"]["fair_american"],
                        "confidence": e["pick"]["confidence"], "in_band": e["pick"]["in_band"],
                        "tier": e["tier"]} for e in rows[:5]]

    model = {
        "meta": {
            "captured_at": captured_at,
            "generated_by": "scripts/livedesk_model.py",
            "source": "OLBG sport hub pages and governing-body endpoints, read once each by scripts/livedesk_collect.py on a GitHub-hosted runner",
            "scope": BRIEF_SPORTS,
            "rule_confidence": "high >= 70% and requires an official numeric input; consensus-only rows cap at medium",
            "rule_band": "fair American price inside -250 .. +10000 inclusive",
            "events": len(out_events),
            "tips": len(tips),
            "expired_tips_excluded": len(expired),
            "matches": sum(1 for e in out_events if e.get("kind", "match") == "match"),
            "outrights": sum(1 for e in out_events if e.get("kind") == "outright"),
            "olbg_pages": pages,
            "text_sources": {s: v[1] for s, v in corpora.items()},
            "ratings": {
                "nhl_standings_url": nhl["standings_url"],
                "nhl_standings_captured_at": nhl["standings_captured_at"],
                "mlb_schedule_url": mlb.get("source_url"),
                "euroleague_standings_url": el["standings_url"],
                "wta_rankings_url": caps.get("wta_rankings", {}).get("final_url"),
                "wta_players_parsed": len(wta),
                "f1_standings_url": caps.get("f1_standings", {}).get("final_url"),
                "f1_drivers_parsed": len(f1),
                "parameters": {
                    "nhl_scale": R.NHL_SCALE, "nhl_home_edge": R.HOME_EDGE_NHL,
                    "mlb_scale": R.MLB_SCALE, "mlb_home_edge": R.MLB_HOME,
                    "mlb_era_weight": R.MLB_ERA_SCALE, "el_scale": R.EL_SCALE,
                    "el_home_edge": R.EL_HOME, "el_sigma": R.EL_SIGMA,
                    "tennis_scale": R.TENNIS_SCALE, "f1_scale": R.F1_SCALE,
                },
            },
        },
        "events": out_events,
        "top5": top5,
        "review": review,
    }
    OUT.write_text(json.dumps(model, indent=1) + "\n", encoding="utf-8")

    by_sport: dict[str, int] = {}
    picks_by_sport: dict[str, int] = {}
    high_by_sport: dict[str, int] = {}
    for ev in out_events:
        by_sport[ev["sport"]] = by_sport.get(ev["sport"], 0) + 1
        if ev.get("pick"):
            picks_by_sport[ev["sport"]] = picks_by_sport.get(ev["sport"], 0) + 1
            if ev["pick"]["confidence"] == "high":
                high_by_sport[ev["sport"]] = high_by_sport.get(ev["sport"], 0) + 1
    digest = {
        "captured_at": captured_at,
        "events_per_sport": by_sport,
        "picks_per_sport": picks_by_sport,
        "high_per_sport": high_by_sport,
        "verified": sum(1 for e in out_events if e["official_verified"]),
        "total": len(out_events),
        "tiers": {t: sum(1 for e in out_events if e["tier"] == t)
                  for t in ("official-model", "quoted-market", "crowd-consensus", "no-basis")},
        "wta_players_parsed": len(wta),
        "f1_drivers_parsed": len(f1),
        "failures": [{"key": k, "status": c.get("http_status"), "url": c.get("url"),
                      "error": c.get("error")}
                     for k, c in caps.items() if c.get("http_status") != 200],
        "review_items": len(review),
        "top5_counts": {s: len(v) for s, v in top5.items()},
    }
    DIGEST.write_text(json.dumps(digest, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out_events)} events, {sum(len(v) for v in top5.values())} top-five selections, "
          f"verified {digest['verified']}, tiers {digest['tiers']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
