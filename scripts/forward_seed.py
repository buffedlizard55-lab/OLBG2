#!/usr/bin/env python3
"""Normalise the raw forward-slate captures into data/forward/inputs.json.

Reads only files this session captured from official endpoints:
  data/forward/capture_nhl.jsonl        (70 NHL fixtures, 2026-10-23 .. 2026-11-02)
  data/forward/capture_nhl_teams.jsonl  (32 NHL club records + GF/GA)
  data/forward/capture_mlb.jsonl        (2026 MLB World Series Games 1-7)
  data/forward/capture_mlb_teams.json   (Rays/Brewers records, runs, leaders, paths)
  data/forward/capture_eurocup_r5.jsonl (EuroCup Round 5 card, 16 matches)
  data/forward/capture_nba_slate.json   (official per-day NBA game counts)
  data/forward/capture_gap_notes.json   (VF-14 / VF-20 / VF-22 attempt logs)

Writes data/forward/inputs.json. No value is invented here; anything absent
from the captures stays absent downstream (rows ship unlined with a reason).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FWD = ROOT / "data" / "forward"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    nhl_fixtures = read_jsonl(FWD / "capture_nhl.jsonl")
    nhl_teams = read_jsonl(FWD / "capture_nhl_teams.jsonl")
    mlb_fixtures = read_jsonl(FWD / "capture_mlb.jsonl")
    mlb_teams = read_json(FWD / "capture_mlb_teams.json")
    eurocup = read_jsonl(FWD / "capture_eurocup_r5.jsonl")
    nba = read_json(FWD / "capture_nba_slate.json")
    gaps = read_json(FWD / "capture_gap_notes.json")

    teams_by_abbr = {t["abbr"]: t for t in nhl_teams}
    missing = sorted(
        {
            f["home"]
            for f in nhl_fixtures
            if f["home"] not in teams_by_abbr
        }
        | {
            f["away"]
            for f in nhl_fixtures
            if f["away"] not in teams_by_abbr
        }
    )
    if missing:
        raise SystemExit(f"fixtures reference teams absent from capture_nhl_teams.jsonl: {missing}")

    ids = [f["id"] for f in nhl_fixtures]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate NHL game ids in capture_nhl.jsonl")

    inputs = {
        "captured_at": "2026-10-22",
        "forward_window": {"start": "2026-10-23", "end": "2026-11-02"},
        "sources": {
            "nhl_fixtures": "https://api-web.nhle.com/v1/score/{date} (gameWeek 2026-10-23 .. 2026-11-02)",
            "nhl_teams": "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027 and gameTypeId=2",
            "mlb_fixtures": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-22&endDate=2026-11-02",
            "mlb_teams": mlb_teams.get("source"),
            "eurocup": "https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/games (Round 5 recovered from full-season feed)",
            "nba": nba.get("source"),
        },
        "nhl_teams": {t["abbr"]: t for t in nhl_teams},
        "nhl_fixtures": nhl_fixtures,
        "mlb_teams": mlb_teams["teams"],
        "mlb_fixtures": mlb_fixtures,
        "eurocup_r5": eurocup,
        "nba_slate": nba,
        "gap_notes": gaps,
    }

    out = FWD / "inputs.json"
    out.write_text(json.dumps(inputs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = {
        "nhl_fixtures": len(nhl_fixtures),
        "nhl_teams": len(nhl_teams),
        "mlb_fixtures": len(mlb_fixtures),
        "eurocup_r5": len(eurocup),
    }
    print(f"wrote {out.relative_to(ROOT)}: {counts}")


if __name__ == "__main__":
    main()
