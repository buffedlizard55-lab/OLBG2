#!/usr/bin/env python3
"""Seed the /relay/ fixture list for session arena/103d996c-olbg2.

Two evidence classes, both stated on every row:

  A  captured first-hand in THIS session (2026-10-22 ~20:55-21:05 UTC) through
     the agent web-fetch tool from the official endpoint named on the row;
  B  carried over verbatim from the first-hand captures of the completed
     /current/ session (read 2026-10-22 12:20-13:05 UTC, stored under
     data/current/capture/ and published in PR #119). Class B is used only for
     fixtures and strength tables this session could not re-read because the
     fetch proxy failed repeatedly; every such row says so.

Nothing is invented: a fixture exists here only if one of those capture files
returned it. Stdlib only, deterministic.
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELAY = os.path.join(ROOT, "data", "relay")
CURCAP = os.path.join(ROOT, "data", "current", "capture")
RELCAP = os.path.join(ROOT, "data", "relay", "capture")

A_NOTE = ("captured first-hand 2026-10-22 20:55-21:05 UTC by session "
          "arena/103d996c-olbg2 (data/relay/capture/)")
B_NOTE = ("carried over verbatim from the /current/ session's first-hand capture "
          "of 2026-10-22 12:20-13:05 UTC (data/current/capture/); this session's "
          "fetch proxy failed on the live endpoint at re-read time")


def load(directory, name):
    with open(os.path.join(directory, name), encoding="utf-8") as handle:
        return json.load(handle)


def team(name, abbrev="", record=""):
    return {"name": name, "abbrev": abbrev, "record": record}


def nhl_rows(matches):
    out = []
    fresh23 = load(RELCAP, "nhl_score_2026-10-23.json")
    fresh24 = load(RELCAP, "nhl_score_2026-10-24.json")
    carry24 = load(CURCAP, "nhl_score_2026-10-24.json")

    fresh_ids = {}
    for g in fresh23["games"] + fresh24["games"]:
        fresh_ids[g["id"]] = g
    carry_ids = {g["game_id"]: g for g in carry24["games"]}

    # Chronological slate: the two 23 October games, then the twelve-game
    # 24 October local slate (ids 2026020168-2026020179; the three western
    # games carry gameDate 2026-10-25 because they start after midnight UTC).
    order = [2026020166, 2026020167] + list(range(2026020168, 2026020180))
    for gid in order:
        if gid in fresh_ids:
            g = fresh_ids[gid]
            ev, note, cap = "A", A_NOTE, "data/relay/capture/nhl_score_2026-10-%s.json" % g["gameDate"][-2:]
            src = "https://api-web.nhle.com/v1/score/%s" % g["gameDate"]
            home = team("%s %s" % (g["home"]["team"], g["home"]["abbrev"]),
                        g["home"]["abbrev"], g["home"]["record"])
            away = team("%s %s" % (g["away"]["team"], g["away"]["abbrev"]),
                        g["away"]["abbrev"], g["away"]["record"])
            start = g["startTimeUTC"]
            venue = g["venue"]
        else:
            g = carry_ids[gid]
            ev, note = "B", B_NOTE
            cap = "data/current/capture/nhl_score_2026-10-24.json"
            src = "https://api-web.nhle.com/v1/score/2026-10-24"
            home = team("%s %s" % (g["home"]["name"], g["home"]["abbrev"]),
                        g["home"]["abbrev"], g["home"]["record"])
            away = team("%s %s" % (g["away"]["name"], g["away"]["abbrev"]),
                        g["away"]["abbrev"], g["away"]["record"])
            start = g["start_time_utc"]
            venue = g["venue"]
        out.append({
            "id": "nhl-%d" % gid, "kind": "fixture", "sport": "ice-hockey",
            "sport_name": "Ice Hockey", "competition": "NHL 2026-27 regular season",
            "date": start[:10], "time_note": "%s (UTC start)" % start[11:16],
            "home": home, "away": away, "venue": venue,
            "official_url": "https://www.nhl.com/gamecenter/%s-vs-%s/%s/%d" % (
                away["abbrev"].lower(), home["abbrev"].lower(), start[:10], gid),
            "source_name": "NHL official API (api-web.nhle.com) score/schedule feed",
            "source_url": src, "capture_file": cap,
            "evidence": ev, "evidence_note": note,
            "inputs": {"home_abbrev": home["abbrev"], "away_abbrev": away["abbrev"]},
        })
    return out


def urc_rows():
    cap = load(CURCAP, "urc_round4_2026-10-22.json")
    out = []
    for f in cap["fixtures"]:
        out.append({
            "id": "urc-%s" % f["match_id"], "kind": "fixture", "sport": "rugby-union",
            "sport_name": "Rugby Union",
            "competition": "United Rugby Championship 2026/27, Round 4",
            "date": f["date"], "time_note": "%s local (as rendered)" % f["kickoff_local"],
            "home": team(f["home"]), "away": team(f["away"]), "venue": f.get("venue", ""),
            "official_url": f["match_url"], "source_name": cap["source_name"],
            "source_url": cap["source_url"],
            "capture_file": "data/current/capture/urc_round4_2026-10-22.json",
            "evidence": "B", "evidence_note": B_NOTE, "inputs": {},
        })
    return out


def euroleague_rows():
    cap = load(CURCAP, "euroleague_round7_2026-10-22.json")
    out = []
    for f in cap["fixtures"]:
        if f["date"] != "2026-10-23":
            continue  # the six 22 October games are finished/in-play at capture time
        out.append({
            "id": "el-%s" % f["game_code"].replace("/", "-"), "kind": "fixture",
            "sport": "basketball", "sport_name": "Basketball",
            "competition": "EuroLeague 2026-27, Round 7",
            "date": f["date"], "time_note": "%s (tip time as rendered)" % f["tip_time_as_rendered"],
            "home": team(f["home"], f["home_code"]), "away": team(f["away"], f["away_code"]),
            "venue": f["venue"], "official_url": f["official_url"],
            "source_name": cap["source_name"], "source_url": cap["source_url_games"],
            "capture_file": "data/current/capture/euroleague_round7_2026-10-22.json",
            "evidence": "B", "evidence_note": B_NOTE, "inputs": {},
        })
    return out


def ehf_rows():
    cap = load(CURCAP, "ehf_2026-10-22.json")
    out = []
    for f in cap["fixtures"]:
        if f["competition"].startswith("IHF"):
            continue  # played 22 Oct, and no official group table exists for it
        if f["date"] == "2026-10-22":
            continue  # in-play on the evening of 22 October
        out.append({
            "id": "ehfcl-%s" % f["match_id"], "kind": "fixture", "sport": "handball",
            "sport_name": "Handball",
            "competition": "EHF Champions League Men 2026/27, group phase",
            "date": f["date"], "time_note": "%s (as rendered)" % f["time_as_rendered"],
            "home": team(f["home"]), "away": team(f["away"]), "venue": "",
            "official_url": f["official_url"], "source_name": cap["source_name"],
            "source_url": cap["source_url"],
            "capture_file": "data/current/capture/ehf_2026-10-22.json",
            "evidence": "B", "evidence_note": B_NOTE, "inputs": {},
        })
    return out


def mlb_rows():
    fresh = load(RELCAP, "mlb_world_series_2026-10-22.json")
    out = []
    for g in fresh["games"]:
        out.append({
            "id": "mlb-%d" % g["gamePk"], "kind": "fixture", "sport": "baseball",
            "sport_name": "Baseball", "competition": "MLB %s" % g["description"],
            "date": g["officialDate"], "time_note": "%s (UTC start)" % g["gameDate"][11:16],
            "home": team(g["home"]["name"]), "away": team(g["away"]["name"]),
            "venue": g["venue"],
            "official_url": "https://www.mlb.com/gameday/rays-vs-brewers/2026/10/%s/%d"
                            % (g["officialDate"][-2:], g["gamePk"]),
            "source_name": fresh["source_name"], "source_url": fresh["source_url"],
            "capture_file": "data/relay/capture/mlb_world_series_2026-10-22.json",
            "evidence": "A", "evidence_note": A_NOTE, "inputs": {},
        })
    return out


def f1_rows():
    cap = load(CURCAP, "f1_calendar_2026-10-22.json")
    nr = cap["next_round"]
    return [{
        "id": "f1-2026-r%d" % nr["round"], "kind": "event", "sport": "motor-racing",
        "sport_name": "Motor Racing",
        "competition": "FIA Formula 1 World Championship 2026, Round %d" % nr["round"],
        "date": "2026-10-25", "time_note": "race day; event dates as rendered: %s" % nr["dates_as_rendered"],
        "event": "United States Grand Prix (Austin)", "venue": "",
        "official_url": nr["official_url"], "source_name": cap["source_name"],
        "source_url": cap["source_url"],
        "capture_file": "data/current/capture/f1_calendar_2026-10-22.json",
        "evidence": "B", "evidence_note": B_NOTE, "inputs": {},
    }]


def main():
    matches = []
    matches += nhl_rows(matches)
    matches += urc_rows()
    matches += euroleague_rows()
    matches += ehf_rows()
    matches += mlb_rows()
    matches += f1_rows()
    matches.sort(key=lambda m: (m["date"], m["id"]))
    doc = {
        "layer": "relay",
        "generated_by": "scripts/relay_seed.py (session arena/103d996c-olbg2)",
        "window": "2026-10-23 to 2026-10-29 (upcoming fixtures only at capture time 2026-10-22 21:00 UTC)",
        "evidence_classes": {"A": A_NOTE, "B": B_NOTE},
        "counts": {
            "fixtures": len(matches),
            "by_sport": {},
            "by_evidence": {"A": sum(1 for m in matches if m["evidence"] == "A"),
                            "B": sum(1 for m in matches if m["evidence"] == "B")},
        },
        "matches": matches,
    }
    for m in matches:
        c = doc["counts"]["by_sport"]
        c[m["sport_name"]] = c.get(m["sport_name"], 0) + 1
    out = os.path.join(RELAY, "matches.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    print("relay_seed OK:", json.dumps(doc["counts"]))


if __name__ == "__main__":
    main()
