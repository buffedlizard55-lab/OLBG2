#!/usr/bin/env python3
"""Parse the captured official governing-body responses into fixtures, team records and
a searchable text index.  Nothing here reads the network: it only reads files under
data/ledger/raw that scripts/ledger_capture.py committed, plus data/ledger/manifest.json.

Every parsed fixture keeps the capture key, the URL and the capture timestamp, so a row on
the site can always be traced back to the exact response it came from.
"""
from __future__ import annotations

import datetime as _dt
import html
import json
import pathlib
import re
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402
DATA = ROOT / "data" / "ledger"
ANCHOR = anchor()
import datetime as _dtmod
ANCHOR_DT = _dtmod.datetime.strptime(ANCHOR, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dtmod.timezone.utc)
RAW = DATA / "raw"


def manifest() -> dict[str, dict]:
    m = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    return {c["key"]: c for c in m["captures"]}


def load_json(key: str, caps: dict):
    cap = caps.get(key)
    if not cap or cap.get("status") != 200:
        return None, cap
    path = DATA / cap.get("stored_as", "")
    try:
        return json.loads(path.read_text(encoding="utf-8")), cap
    except (OSError, ValueError):
        return None, cap


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text)


# --------------------------------------------------------------------------- fixtures
def nhl_fixtures(caps: dict) -> list[dict]:
    out = {}
    for key in [k for k in caps if k.startswith("ieh_sched")]:
        data, cap = load_json(key, caps)
        if not data:
            continue
        for day in data.get("gameWeek", []):
            for g in day.get("games", []):
                gid = g.get("id")
                out[gid] = {
                    "sport": "Ice Hockey",
                    "competition": "NHL",
                    "home": g.get("homeTeam", {}).get("commonName", {}).get("default", ""),
                    "home_full": g.get("homeTeam", {}).get("name", {}).get("default", ""),
                    "away": g.get("awayTeam", {}).get("commonName", {}).get("default", ""),
                    "away_full": g.get("awayTeam", {}).get("name", {}).get("default", ""),
                    "home_abbrev": g.get("homeTeam", {}).get("abbrev", ""),
                    "away_abbrev": g.get("awayTeam", {}).get("abbrev", ""),
                    "home_score": g.get("homeTeam", {}).get("score"),
                    "away_score": g.get("awayTeam", {}).get("score"),
                    "start_utc": g.get("startTimeUTC", ""),
                    "venue": g.get("venue", {}).get("default", ""),
                    "state": g.get("gameState", ""),
                    "official_url": f"https://www.nhl.com/gamecenter/{g.get('awayTeam',{}).get('abbrev','').lower()}-vs-{g.get('homeTeam',{}).get('abbrev','').lower()}/{(g.get('startTimeUTC') or '')[:4]}/{(g.get('startTimeUTC') or '')[5:7]}/{(g.get('startTimeUTC') or '')[8:10]}/{gid}",
                    "source_key": key,
                    "source_url": cap.get("final_url"),
                    "captured_at": cap.get("fetched_at"),
                    "fixture_id": f"nhl-{gid}",
                }
    return sorted(out.values(), key=lambda f: f["start_utc"])


def mlb_fixtures(caps: dict) -> list[dict]:
    data, cap = load_json("baseball_schedule2", caps)
    out = []
    if not data:
        return out
    for day in data.get("dates", []):
        for g in day.get("games", []):
            home = g["teams"]["home"]
            away = g["teams"]["away"]
            out.append({
                "sport": "Baseball",
                "competition": "MLB",
                "home": home["team"]["name"],
                "home_full": home["team"]["name"],
                "away": away["team"]["name"],
                "away_full": away["team"]["name"],
                "home_abbrev": home["team"].get("teamCode", ""),
                "away_abbrev": away["team"].get("teamCode", ""),
                "home_score": home.get("score"),
                "away_score": away.get("score"),
                "start_utc": g.get("gameDate", ""),
                "venue": g.get("venue", {}).get("name", ""),
                "state": g.get("status", {}).get("detailedState", ""),
                "home_pitcher": (home.get("probablePitcher") or {}).get("fullName", ""),
                "away_pitcher": (away.get("probablePitcher") or {}).get("fullName", ""),
                "official_url": f"https://www.mlb.com/gameday/{g.get('gamePk')}",
                "source_key": "baseball_schedule2",
                "source_url": cap.get("final_url"),
                "captured_at": cap.get("fetched_at"),
                "fixture_id": f"mlb-{g.get('gamePk')}",
            })
    return out


def euroleague_fixtures(caps: dict) -> list[dict]:
    out = {}
    for key in ["basketball_el_schedule", "basketball_el_sched9"]:
        cap = caps.get(key)
        if not cap or cap.get("status") != 200:
            continue
        path = DATA / cap.get("stored_as", "")
        try:
            root = ET.fromstring(path.read_text(encoding="utf-8"))
        except (OSError, ET.ParseError):
            continue
        for item in root.findall("item"):
            code = (item.findtext("gamecode") or "").strip()
            date = (item.findtext("date") or "").strip()
            start = (item.findtext("startime") or "").strip()
            try:
                dt = _dt.datetime.strptime(date, "%b %d, %Y")
                start_utc = dt.strftime("%Y-%m-%dT") + start[:5] + ":00"  # EuroLeague serves local tip time; flagged, not converted
            except ValueError:
                start_utc = ""
            out[code] = {
                "sport": "Basketball",
                "competition": "EuroLeague",
                "home": (item.findtext("hometeam") or "").strip(),
                "home_full": (item.findtext("hometeam") or "").strip(),
                "away": (item.findtext("awayteam") or "").strip(),
                "away_full": (item.findtext("awayteam") or "").strip(),
                "home_abbrev": "", "away_abbrev": "",
                "home_score": None, "away_score": None,
                "start_utc": start_utc,
                "time_basis": "as served (venue-local tip time, not converted)",
                "venue": (item.findtext("arenaname") or "").strip(),
                "state": "scheduled",
                "official_url": f"https://www.euroleaguebasketball.net/euroleague/game-center/{code}/",
                "source_key": key,
                "source_url": cap.get("final_url"),
                "captured_at": cap.get("fetched_at"),
                "fixture_id": f"el-{code}",
            }
    return sorted(out.values(), key=lambda f: f["start_utc"])


# --------------------------------------------------------------------------- records
def nhl_records(caps: dict) -> dict[str, dict]:
    data, cap = load_json("ieh_standings", caps)
    out = {}
    for t in (data or {}).get("standings", []):
        name = t.get("teamCommonName", {}).get("default") or t.get("teamName", {}).get("default", "")
        out[norm(name)] = {
            "name": t.get("teamName", {}).get("default", ""),
            "gp": t.get("gamesPlayed"), "w": t.get("wins"), "l": t.get("losses"), "otl": t.get("otLosses"),
            "pts": t.get("points"), "gf": t.get("goalFor"), "ga": t.get("goalAgainst"),
            "home_w": t.get("homeWins"), "home_l": t.get("homeLosses"), "home_otl": t.get("homeOtLosses"),
            "road_w": t.get("roadWins"), "road_l": t.get("roadLosses"), "road_otl": t.get("roadOtLosses"),
            "l10_w": t.get("l10Wins"), "l10_l": t.get("l10Losses"), "l10_otl": t.get("l10OtLosses"),
            "streak": t.get("streakCode", ""), "streak_count": t.get("streakCount"),
            "source_url": "https://api-web.nhle.com/v1/standings/now",
            "captured_at": cap.get("fetched_at") if cap else "",
        }
    return out


def mlb_records(caps: dict) -> dict[str, dict]:
    out = {}
    for key in ("baseball_standings_al", "baseball_standings_nl"):
        data, cap = load_json(key, caps)
        for rec in (data or {}).get("records", []):
            for t in rec.get("teamRecords", []):
                name = t["team"]["name"]
                out[norm(name)] = {
                    "name": name, "w": t.get("wins"), "l": t.get("losses"),
                    "pct": t.get("winningPercentage"), "gb": t.get("gamesBack"),
                    "rs": t.get("runsScored"), "ra": t.get("runsAllowed"),
                    "diff": t.get("runDifferential"),
                    "home": t.get("records", {}).get("splitRecords", [{}])[0].get("wins") if False else None,
                    "streak": (t.get("streak") or {}).get("streakCode", ""),
                    "source_url": f"https://statsapi.mlb.com/api/v1/standings?leagueId={'103' if key.endswith('al') else '104'}&season=2026&standingsTypes=regularSeason",
                    "captured_at": cap.get("fetched_at") if cap else "",
                }
    return out


def euroleague_records(caps: dict) -> dict[str, dict]:
    cap = caps.get("basketball_el_standings")
    out = {}
    if not cap or cap.get("status") != 200:
        return out
    try:
        root = ET.fromstring((DATA / cap.get("stored_as", "")).read_text(encoding="utf-8"))
    except (OSError, ET.ParseError):
        return out
    for t in root.findall(".//team"):
        name = (t.findtext("name") or "").strip()
        out[norm(name)] = {
            "name": name, "gp": int(t.findtext("totalgames") or 0),
            "w": int(t.findtext("wins") or 0), "l": int(t.findtext("losses") or 0),
            "pf": int(t.findtext("ptsfavour") or 0), "pa": int(t.findtext("ptsagainst") or 0),
            "rank": int(t.findtext("ranking") or 0),
            "source_url": "https://api-live.euroleague.net/v1/standings?seasonCode=E2026&gameNumber=7",
            "captured_at": cap.get("fetched_at"),
        }
    return out


# --------------------------------------------------------------------------- text index
HTML_SOURCES = [
    ("gaelic_gaa_fixtures", "Gaelic Sports", "GAA fixtures & results"),
    ("volleyball_fivb", "Volleyball", "Volleyball World competitions"),
    ("volleyball_cev_club", "Volleyball", "CEV club competitions"),
    ("handball_ehf_calendar", "Handball", "EHF calendar"),
    ("handball_ehf_matches", "Handball", "EHF matches"),
    ("greyhounds_gbgb_races", "Greyhounds", "GBGB racing"),
    ("greyhounds_gbgb", "Greyhounds", "GBGB open races"),
    ("tennis_wta_scores", "Tennis", "WTA scores"),
    ("tennis_wta_rankings", "Tennis", "WTA rankings"),
    ("snooker_wst_home", "Snooker", "WST home"),
    ("snooker_wst_rankings", "Snooker", "WST rankings"),
    ("snooker_wst_news", "Snooker", "WST news"),
    ("darts_pdc_oom", "Darts", "PDC Order of Merit"),
    ("darts_pdc_tournaments", "Darts", "PDC tournaments"),
    ("golf_euro_schedule", "Golf", "DP World Tour schedule"),
    ("golf_euro_lb", "Golf", "DP World Tour leaderboard"),
    ("golf_pga_schedule", "Golf", "PGA Tour schedule"),
    ("motor_f1_races", "Motor Racing", "Formula 1 calendar"),
    ("motor_f1_standings2", "Motor Racing", "Formula 1 driver standings"),
    ("rugby_union_prem_fixtures2", "Rugby Union", "Premiership Rugby fixtures"),
    ("rugby_union_prem_table", "Rugby Union", "Premiership Rugby table"),
    ("rugby_union_urc_fixtures", "Rugby Union", "URC fixtures"),
    ("rugby_union_urc_table", "Rugby Union", "URC table"),
    ("rugby_league_rlwc", "Rugby League", "RLWC 2026 fixtures"),
    ("cricket_com_au2", "Cricket", "Cricket Australia matches"),
    ("cricket_com_au_results", "Cricket", "Cricket Australia recent results"),
    ("cricket_icc_t20_rankings", "Cricket", "ICC T20I team rankings"),
    ("cricket_icc_odi_rankings", "Cricket", "ICC ODI team rankings"),
    ("tennis_wta_singles", "Tennis", "WTA singles rankings"),
    ("tennis_wta_scores_current", "Tennis", "WTA current scores"),
    ("darts_pdc_news", "Darts", "PDC news"),
    ("darts_pdc_euro_2026", "Darts", "PDC European Championship 2026"),
    ("snooker_wst_tournaments", "Snooker", "WST tournaments"),
    ("handball_spain", "Handball", "ASOBAL (Spain)"),
    ("handball_france", "Handball", "LNH (France)"),
    ("handball_norway", "Handball", "NHF (Norway)"),
    ("volleyball_bundesliga", "Volleyball", "Volleyball Bundesliga"),
    ("volleyball_legavolley", "Volleyball", "Lega Volley Serie A"),
    ("volleyball_superliga", "Volleyball", "Brazilian Superliga"),
    ("volleyball_plusliga", "Volleyball", "Polish PlusLiga"),
    ("rugby_union_urc_matchcentre", "Rugby Union", "URC match centre"),
    ("greyhounds_gbgb_results", "Greyhounds", "GBGB results"),
    ("cricket_icc_rankings", "Cricket", "ICC rankings"),
]


def text_sources(caps: dict) -> list[dict]:
    out = []
    for key, sport, label in HTML_SOURCES:
        cap = caps.get(key)
        if not cap or cap.get("status") != 200:
            out.append({"key": key, "sport": sport, "label": label,
                        "url": cap.get("final_url") if cap else "", "status": cap.get("status") if cap else 0,
                        "captured_at": cap.get("fetched_at") if cap else "", "text": "", "ok": False})
            continue
        path = DATA / cap.get("stored_as", "")
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            raw = ""
        text = strip_tags(raw)
        out.append({"key": key, "sport": sport, "label": label, "url": cap.get("final_url"),
                    "status": cap.get("status"), "captured_at": cap.get("fetched_at"),
                    "stored_as": cap.get("stored_as", ""),
                    "truncated": cap.get("truncated", False), "text": text, "ok": len(text) > 500})
    return out


def main() -> int:
    caps = manifest()
    fixtures = nhl_fixtures(caps) + mlb_fixtures(caps) + euroleague_fixtures(caps)
    out = {
        "meta": {
            "generated_at": ANCHOR,
            "note": "Fixtures and records parsed verbatim from the official responses captured in data/ledger/raw.",
            "counts": {
                "fixtures": len(fixtures),
                "nhl_records": len(nhl_records(caps)),
                "mlb_records": len(mlb_records(caps)),
                "euroleague_records": len(euroleague_records(caps)),
                "text_sources": len([s for s in text_sources(caps) if s["ok"]]),
            },
        },
        "fixtures": fixtures,
        "records": {
            "nhl": nhl_records(caps),
            "mlb": mlb_records(caps),
            "euroleague": euroleague_records(caps),
        },
        "text_sources": [{"key": s["key"], "sport": s["sport"], "label": s["label"], "url": s["url"], "stored_as": s.get("stored_as",""),
                          "status": s["status"], "captured_at": s["captured_at"], "ok": s["ok"],
                          "truncated": s.get("truncated", False), "chars": len(s["text"])}
                         for s in text_sources(caps)],
    }
    (DATA / "official.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["meta"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
