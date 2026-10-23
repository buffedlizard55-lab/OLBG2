#!/usr/bin/env python3
"""Prepare a traceable 15-sport evidence snapshot for the Zenith desk.

This desk keeps two distinct evidence layers: the timestamped OLBG hub inventory from
ledger capture (discovery only), and the official-source fixtures/facts previously
captured in the same-day Cadence evidence bundle. It never upgrades those source timestamps
or states that an OLBG consensus quote is our price.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "zenith"
AS_OF_UTC = "2026-10-23T21:45:00Z"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    official = load("data/cadence/matches.json")
    olbg = load("data/zenith/olbg_events.json")
    source_records = load("data/cadence/sources.json")
    source_map = {x["key"]: x for x in source_records["sources"]}
    fixtures: list[dict[str, Any]] = []
    for m in official["matches"]:
        if m.get("sport") not in SPORTS:
            continue
        facts = []
        for f in m.get("facts", []):
            # Keep a reachable official injury-report URL on the row, but do not copy
            # disputed/unvalidated player-to-team extraction into fact prose.
            if "injury" in str(f.get("source_key", "")).lower():
                continue
            facts.append({
                "subject": f.get("team_or_item", ""),
                "value": f.get("value", ""),
                "source_key": f.get("source_key", ""),
                "source_url": f.get("source_url", ""),
                "capture_timestamp_utc": (source_map.get(f.get("source_key", ""), {}).get("fetched_at") or ""),
            })
        # Exact OLBG ID matches are authoritative only for discovery; no fuzzy name inference.
        olbg_id = str(m.get("olbg_event_id") or "")
        olbg_event = next((e for e in olbg["events"] if e["event_id"] == olbg_id), None) if olbg_id else None
        start = m.get("start_utc") or ""
        if start and start[:19] <= AS_OF_UTC[:19]:
            temporal = "started_or_due_at_capture"
        elif start:
            temporal = "upcoming_at_capture"
        else:
            temporal = "official_start_time_unconfirmed"
        fixtures.append({
            "id": m["id"], "sport": m["sport"], "competition": m.get("competition", ""),
            "home": m.get("home", ""), "away": m.get("away", ""), "venue": m.get("venue", ""),
            "start_utc": start or None, "time_display": m.get("time_display", ""),
            "olbg_event_id": olbg_id or None,
            "olbg_event_url": olbg_event.get("event_url", "") if olbg_event else "",
            "official_fixture_url": m.get("official_source_url", ""),
            "official_stats_url": m.get("stats_source_url", ""),
            "injury_report_url": m.get("injury_source_url", ""),
            "temporal_state": temporal,
            "evidence_tier": m.get("evidence_tier", ""),
            "evidence_note": m.get("evidence", ""),
            "fixture_status": m.get("status", ""),
            "blank_reason": m.get("note") or "",
            "facts": facts,
        })
    payload = {
        "as_of_utc": AS_OF_UTC,
        "source_snapshot_utc": official.get("generated_utc", ""),
        "source_snapshot_session": official.get("session", ""),
        "sport_count": len(SPORTS), "sports": SPORTS,
        "count": len(fixtures), "fixtures": fixtures,
        "provenance_note": "Official fixture/fact records are from the dated same-day Cadence capture bundle, not a continuously refreshed feed. OLBG contributes listing discovery and market labels only; all confidence and our lines are computed independently in this desk. Exact URLs and source capture times are preserved row-by-row.",
    }
    (OUT / "fixtures.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"zenith_seed: {len(fixtures)} fixtures, {len(SPORTS)} sports; {sum(1 for x in fixtures if x['temporal_state']=='upcoming_at_capture')} have a confirmed start after the capture clock.")

if __name__ == "__main__":
    main()
