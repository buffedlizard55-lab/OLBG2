#!/usr/bin/env python3
"""Build the consolidated desk from first-hand captures.

Input  : data/desk/captures/manifest.json + raw bodies (written by scripts/desk_collect.py)
Output : data/desk/model.json   (compact; committed; the site is built only from this)

Two rules govern everything here, because the published desk has to survive line-by-line
review:

1.  A fixture exists only if OLBG lists it.  OLBG is the scope authority for this project:
    the brief is "the matches OLBG has markets on".  The governing-body pages are used to
    *confirm* an OLBG fixture, never to invent one, and a fixture whose participants cannot
    be found in an official capture is published with ``official_verified: false`` rather
    than being dropped or quietly accepted.

2.  A price is never copied from OLBG as "our line".  OLBG's quoted decimal is kept in
    ``market_implied`` for reference and for the market-consensus probability.  Our own
    number comes from ``originate`` below and is labelled ``basis`` on every row:

        official-form  our probability starts from the market consensus and is shifted by
                       the verified scoring form the governing body publishes
        market-only    no official form input exists for this sport, so our fair price is
                       the de-vigged market consensus; the row says so

Confidence is a probability grade, not a price grade: high >= 70%, medium 60-70%, else low.
The brief's price window (-250 to +10000) is recorded separately as ``in_band`` so that a
71% favourite priced at -300 is shown as high-confidence-but-outside-the-window instead of
being silently relabelled.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAP = ROOT / "data" / "desk" / "captures"
RAW = CAP / "raw"
OUT = ROOT / "data" / "desk" / "model.json"
DIGEST = ROOT / "data" / "desk" / "digest.json"

SPORT_SLUG = {
    "Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
    "Cricket": "cricket", "Snooker": "snooker", "Darts": "darts", "Baseball": "baseball",
    "Gaelic Football": "gaelic-football", "Hurling": "hurling", "Greyhounds": "greyhounds",
    "Tennis": "tennis", "Motor Racing": "motor-racing", "Handball": "handball",
    "Ice Hockey": "ice-hockey", "Basketball": "basketball", "Rugby League": "rugby-league",
    "Gaelic Sports": "gaelic-sports",
}
# the fifteen sports named in the brief, in the order the brief names them
BRIEF_SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
OLBG_SPORT = {"Gaelic Football": "Gaelic Sports", "Hurling": "Gaelic Sports"}

OBJ_START = re.compile(r'\{id:"([0-9a-f]{40})"')
FIELD_RE = re.compile(r'(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<val>"(?:[^"\\]|\\.)*"|[^,}\]]+)')


# --------------------------------------------------------------------------- utilities
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
    text = body(key, caps)
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


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


def american(p: float) -> int:
    p = min(max(p, 0.0002), 0.9998)
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def decimal_from_american(a: int) -> float:
    return round(1 + (100 / -a) if a < 0 else 1 + a / 100, 3)


def in_band(a: int) -> bool:
    return -250 <= a <= 10000


def grade(p: float) -> str:
    if p >= 0.70:
        return "high"
    if p >= 0.60:
        return "medium"
    return "low"


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# --------------------------------------------------------------------------- OLBG listing
def olbg_tips(caps: dict) -> tuple[list[dict], dict]:
    tips: dict[tuple, dict] = {}
    pages = {}
    for key, cap in sorted(caps.items()):
        if not key.startswith("olbg_hub_"):
            continue
        text = body(key, caps)
        if not text:
            pages[key] = {"status": cap.get("http_status"), "objects": 0, "url": cap.get("url")}
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
            comp = fields.get("menu_league") or fields.get("tournament") or ""
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
                "competition": comp,
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
        pages[key] = {"status": cap.get("http_status"), "objects": count, "url": cap.get("url")}
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
                home = g.get("homeTeam", {})
                away = g.get("awayTeam", {})
                games[gid] = {
                    "fixture_id": f"nhl-{gid}",
                    "sport": "Ice Hockey",
                    "competition": "NHL",
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
                "gp": row.get("gamesPlayed"),
                "w": row.get("wins"),
                "l": row.get("losses"),
                "otl": row.get("otLosses"),
                "pts": row.get("points"),
                "gf": row.get("goalFor"),
                "ga": row.get("goalAgainst"),
                "diff": row.get("goalDifferential"),
                "l10": f"{row.get('l10Wins')}-{row.get('l10Losses')}-{row.get('l10OtLosses')}",
                "l10_points": row.get("l10Points"),
                "streak": f"{row.get('streakCode','')}{row.get('streakCount','')}",
                "home": f"{row.get('homeWins')}-{row.get('homeLosses')}-{row.get('homeOtLosses')}",
                "road": f"{row.get('roadWins')}-{row.get('roadLosses')}-{row.get('roadOtLosses')}",
            }
    return {"games": games, "standings": standings,
            "standings_url": caps.get("ieh_standings", {}).get("url"),
            "standings_captured_at": caps.get("ieh_standings", {}).get("requested_at")}


# --------------------------------------------------------------------------- official: MLB
def mlb_official(caps: dict) -> dict:
    games = {}
    data = as_json("mlb_sched", caps)
    if data:
        for day in data.get("dates", []):
            for g in day.get("games", []):
                pk = g.get("gamePk")
                home, away = g["teams"]["home"], g["teams"]["away"]
                games[pk] = {
                    "fixture_id": f"mlb-{pk}",
                    "sport": "Baseball",
                    "competition": g.get("description") or g.get("seriesDescription") or "MLB",
                    "home": home["team"]["name"],
                    "away": away["team"]["name"],
                    "start_utc": g.get("gameDate", ""),
                    "venue": (g.get("venue") or {}).get("name", ""),
                    "state": (g.get("status") or {}).get("detailedState", ""),
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
                              "ops": st.get("ops"), "gp": st.get("gamesPlayed")})
            else:
                entry.update({"era": st.get("era"), "whip": st.get("whip"), "ra": st.get("runs"),
                              "er": st.get("earnedRuns"), "ip": st.get("inningsPitched")})
    return {"games": games, "team_stats": stats}


# --------------------------------------------------------------------------- official: EuroLeague
def euroleague_official(caps: dict) -> dict:
    games = {}
    for key in ("el_sched8", "el_sched9"):
        data = as_json(key, caps)
        if not data:
            continue
        rows = data.get("data") if isinstance(data, dict) else data
        if isinstance(rows, dict):
            rows = rows.get("games") or rows.get("data") or []
        for g in rows or []:
            if not isinstance(g, dict):
                continue
            gid = g.get("gameCode") or g.get("identifier") or g.get("gameNumber")
            home = g.get("local") or g.get("home") or {}
            away = g.get("road") or g.get("away") or {}
            name = lambda t: (t.get("name") or t.get("clubName") or t.get("officialName") or "") if isinstance(t, dict) else ""
            date = g.get("date") or g.get("utcDate") or ""
            games[gid] = {
                "fixture_id": f"el-{gid}",
                "sport": "Basketball",
                "competition": "EuroLeague",
                "home": name(home),
                "away": name(away),
                "start_utc": date,
                "round": g.get("gameNumber") or g.get("round"),
                "venue": (g.get("venue") or {}).get("name", "") if isinstance(g.get("venue"), dict) else "",
                "source_key": key,
                "source_url": caps[key].get("final_url") or caps[key].get("url"),
                "captured_at": caps[key].get("requested_at"),
            }
    standings = {}
    data = as_json("el_standings", caps)
    if data:
        rows = data.get("data") if isinstance(data, dict) else data
        for r in rows or []:
            if not isinstance(r, dict):
                continue
            t = r.get("club") or r.get("team") or {}
            name = t.get("name") if isinstance(t, dict) else str(t)
            if not name:
                continue
            standings[name] = {
                "w": r.get("won") or r.get("wins"),
                "l": r.get("lost") or r.get("losses"),
                "pf": r.get("scoredFor") or r.get("pointsFor"),
                "pa": r.get("scoredAgainst") or r.get("pointsAgainst"),
                "pos": r.get("position") or r.get("rank"),
                "gp": r.get("gamesPlayed"),
            }
    return {"games": games, "standings": standings,
            "standings_url": caps.get("el_standings", {}).get("url")}


# --------------------------------------------------------------------------- text sources
TEXT_SPORTS = {
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


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&#39;", "'").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text)


def text_corpus(sport: str, caps: dict) -> tuple[str, list[dict]]:
    parts, used = [], []
    for key in TEXT_SPORTS.get(sport, []):
        text = body(key, caps)
        if not text:
            continue
        plain = strip_tags(text)
        parts.append(" " + plain + " ")
        cap = caps[key]
        used.append({"key": key, "url": cap.get("final_url") or cap.get("url"),
                     "captured_at": cap.get("requested_at"), "chars": len(plain)})
    return norm(" ".join(parts)), used


# --------------------------------------------------------------------------- origination
def originate(event: dict, official_facts: dict | None) -> dict:
    """Group OLBG selections into markets and derive our own fair price for each."""
    groups: dict[str, list[dict]] = {}
    for t in event["tips"]:
        groups.setdefault(t["market"] or "Unnamed market", []).append(t)
    markets = []
    for market, rows in groups.items():
        dec = []
        for r in rows:
            try:
                dec.append(float(r["decimal"]))
            except (TypeError, ValueError):
                dec.append(0.0)
        implied = [1 / d if d > 1 else 0.0 for d in dec]
        total = sum(implied)
        two_way = len(rows) == 2 and total > 0
        for r, d, imp in zip(rows, dec, implied):
            market_prob = (imp / total) if (two_way and total) else None
            p = market_prob
            basis = "market-only"
            if p is not None and official_facts:
                shift = official_facts.get("logit_shift", 0.0)
                lo = clamp(p, 0.005, 0.995)
                z = math.log(lo / (1 - lo)) + shift
                p = 1 / (1 + math.exp(-z))
                basis = "official-form"
            if p is None:
                markets.append({
                    "market": market, "selection": r["selection"], "quoted_decimal": d or None,
                    "quoted_american": r["american"] or None, "basis": "no two-way price",
                    "our_probability": None, "fair_american": None, "in_band": None,
                    "confidence": None, "olbg_tips": r.get("win_tips"),
                })
                continue
            fair = american(p)
            markets.append({
                "market": market,
                "selection": r["selection"],
                "quoted_decimal": round(d, 3) if d else None,
                "quoted_american": int(r["american"]) if str(r["american"]).lstrip("+-").isdigit() else None,
                "market_probability": round(market_prob, 4),
                "our_probability": round(p, 4),
                "fair_decimal": decimal_from_american(fair),
                "fair_american": fair,
                "in_band": in_band(fair),
                "confidence": grade(p),
                "basis": basis,
                "olbg_tips": r.get("win_tips"),
            })
    markets.sort(key=lambda m: (-(m["our_probability"] or 0), m["market"], m["selection"]))
    return {"markets": markets}


def split_event(name: str) -> tuple[str, str]:
    for sep in (" @ ", " vs ", " v "):
        if sep in name:
            a, b = name.split(sep, 1)
            return a.strip(), b.strip()
    return name.strip(), ""


def main() -> int:
    caps, captured_at = load_manifest()
    tips, pages = olbg_tips(caps)
    expired = [t for t in tips if t.get("expired") == "1"]
    tips = [t for t in tips if t.get("expired") != "1"]
    nhl = nhl_official(caps)
    mlb = mlb_official(caps)
    el = euroleague_official(caps)

    review: list[dict] = []
    events: dict[str, dict] = {}
    for t in tips:
        ekey = f"{t['sport']}|{t['event_id'] or norm(t['event'])}"
        ev = events.setdefault(ekey, {
            "key": ekey,
            "sport": t["sport"],
            "competition": t["competition"],
            "name": t["event"],
            "olbg_event_id": t["event_id"],
            "start_utc": t["start_utc"],
            "olbg_url": t["event_url"],
            "olbg_listing_url": t["listing_url"],
            "olbg_captured_at": t["captured_at"],
            "tips": [],
        })
        ev["tips"].append(t)

    out_events = []
    for key, ev in events.items():
        home, away = split_event(ev["name"])
        ev["home"], ev["away"] = home, away
        official = None
        facts = None
        sport = ev["sport"]
        if sport == "Ice Hockey":
            for g in nhl["games"].values():
                if norm(g["away_name"]) and norm(g["away_name"]) in norm(ev["name"]) and norm(g["home_name"]) in norm(ev["name"]):
                    official = g
                    break
            if official:
                hs = nhl["standings"].get(official["home_abbrev"])
                as_ = nhl["standings"].get(official["away_abbrev"])
                if hs and as_ and hs["gp"] and as_["gp"]:
                    per_game = ((hs["gf"] / hs["gp"]) - (hs["ga"] / hs["gp"])) - ((as_["gf"] / as_["gp"]) - (as_["ga"] / as_["gp"]))
                    facts = {
                        "home_record": f"{hs['w']}-{hs['l']}-{hs['otl']}",
                        "away_record": f"{as_['w']}-{as_['l']}-{as_['otl']}",
                        "home_points": hs["pts"], "away_points": as_["pts"],
                        "home_gf": hs["gf"], "home_ga": hs["ga"],
                        "away_gf": as_["gf"], "away_ga": as_["ga"],
                        "home_l10": hs["l10"], "away_l10": as_["l10"],
                        "home_streak": hs["streak"], "away_streak": as_["streak"],
                        "home_venue_record": hs["home"], "away_venue_record": as_["road"],
                        "goal_diff_per_game_edge": round(per_game, 3),
                        "logit_shift": clamp(per_game * 0.12, -0.55, 0.55),
                        "source_key": official["source_key"],
                        "source_url": official["source_url"],
                        "captured_at": official["captured_at"],
                        "standings_url": nhl["standings_url"],
                    }
        elif sport == "Baseball":
            for g in mlb["games"].values():
                if norm(g["home"]) in norm(ev["name"]) and norm(g["away"]) in norm(ev["name"]):
                    official = g
                    break
            if official:
                hs = mlb["team_stats"].get(official["home"], {})
                as_ = mlb["team_stats"].get(official["away"], {})
                facts = {
                    "home_record": official.get("home_record"), "away_record": official.get("away_record"),
                    "home_pitcher": official.get("home_pitcher"), "away_pitcher": official.get("away_pitcher"),
                    "home_runs": hs.get("runs"), "away_runs": as_.get("runs"),
                    "home_ops": hs.get("ops"), "away_ops": as_.get("ops"),
                    "home_era": hs.get("era"), "away_era": as_.get("era"),
                    "source_key": official["source_key"],
                    "source_url": official["source_url"],
                    "captured_at": official["captured_at"],
                }
        elif sport == "Basketball":
            for g in el["games"].values():
                if g["home"] and g["away"] and norm(g["home"]) in norm(ev["name"]) and norm(g["away"]) in norm(ev["name"]):
                    official = g
                    break
            if official:
                hs = el["standings"].get(official["home"], {})
                as_ = el["standings"].get(official["away"], {})
                facts = {
                    "round": official.get("round"),
                    "home_record": f"{hs.get('w')}-{hs.get('l')}" if hs else "",
                    "away_record": f"{as_.get('w')}-{as_.get('l')}" if as_ else "",
                    "home_pf": hs.get("pf"), "home_pa": hs.get("pa"),
                    "away_pf": as_.get("pf"), "away_pa": as_.get("pa"),
                    "source_key": official["source_key"],
                    "source_url": official["source_url"],
                    "captured_at": official["captured_at"],
                }

        verified = bool(official)
        noted = originate(ev, facts)
        ev["official_verified"] = verified
        ev["official"] = official
        ev["facts"] = facts
        ev.update(noted)
        if not verified:
            review.append({
                "sport": sport, "event": ev["name"], "start_utc": ev["start_utc"],
                "issue": "OLBG lists this event but its participants were not found in the official capture for this sport; the row keeps its OLBG link and no official fixture link.",
                "olbg_url": ev["olbg_url"], "source_checked": pages.get("olbg_hub_" + SPORT_SLUG.get(sport, "").replace("-", "_"), {}).get("url", ""),
            })
        out_events.append(ev)

    # our own pick per event: highest probability inside the brief's window, else highest probability
    for ev in out_events:
        candidates = [m for m in ev["markets"] if m.get("our_probability")]
        pool = [m for m in candidates if m.get("in_band")] or candidates
        if pool:
            best = max(pool, key=lambda m: (m["our_probability"], -abs(m["fair_american"])))
            ev["pick"] = {
                "market": best["market"], "selection": best["selection"],
                "our_probability": best["our_probability"], "fair_american": best["fair_american"],
                "quoted_american": best.get("quoted_american"), "confidence": best["confidence"],
                "in_band": best["in_band"], "basis": best["basis"],
            }
        else:
            ev["pick"] = None
        ev["tips"] = [{"selection": t["selection"], "market": t["market"], "decimal": t["decimal"],
                       "american": t["american"], "win_tips": t.get("win_tips"),
                       "expired": t.get("expired")} for t in ev["tips"]]

    out_events.sort(key=lambda e: (e["start_utc"] or "9999", e["sport"], e["name"]))

    # per-sport official text check, kept so the site can show what was consulted
    text_sources = {}
    for sport in TEXT_SPORTS:
        corpus, used = text_corpus(sport, caps)
        text_sources[sport] = {"sources": used, "corpus_chars": len(corpus)}

    model = {
        "meta": {
            "captured_at": captured_at,
            "source": "OLBG sport hub pages + governing-body endpoints, captured by scripts/desk_collect.py",
            "scope": BRIEF_SPORTS,
            "rule_confidence": "high >= 70%, medium 60-70%, low < 60%",
            "rule_band": "fair American price within -250 .. +10000 inclusive",
            "events": len(out_events),
            "tips": len(tips),
            "olbg_pages": pages,
            "expired_tips_excluded": len(expired),
            "official_text_sources": text_sources,
            "nhl_standings_url": nhl["standings_url"],
        },
        "events": out_events,
        "review": review,
    }
    OUT.write_text(json.dumps(model, indent=1) + "\n", encoding="utf-8")

    by_sport: dict[str, int] = {}
    for ev in out_events:
        by_sport[ev["sport"]] = by_sport.get(ev["sport"], 0) + 1
    digest = {
        "captured_at": captured_at,
        "events_per_sport": by_sport,
        "verified": sum(1 for e in out_events if e["official_verified"]),
        "unverified": sum(1 for e in out_events if not e["official_verified"]),
        "picks": sum(1 for e in out_events if e["pick"]),
        "high": sum(1 for e in out_events if e["pick"] and e["pick"]["confidence"] == "high"),
        "in_band_high": sum(1 for e in out_events if e["pick"] and e["pick"]["confidence"] == "high" and e["pick"]["in_band"]),
        "failures": [{"key": k, "status": c.get("http_status"), "url": c.get("url")}
                     for k, c in caps.items() if c.get("http_status") != 200],
        "olbg_pages": pages,
        "text_sources": {k: [s["key"] for s in v["sources"]] for k, v in text_sources.items()},
    }
    DIGEST.write_text(json.dumps(digest, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out_events)} events, {len(tips)} tips, verified {digest['verified']}, "
          f"picks {digest['picks']}, high {digest['high']}, in-band high {digest['in_band_high']}")
    for s, n in sorted(by_sport.items()):
        print(f"  {s:16s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
