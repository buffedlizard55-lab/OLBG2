#!/usr/bin/env python3
"""Print a compact fact sheet per fixture so the prose can be authored against it.

This is a working tool, not part of the published pipeline.  It prints one line per fixture
with exactly the values a prediction is allowed to use, which is the same set the verifier
later checks the prose against.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = json.loads((ROOT / "data" / "live_desk" / "model.json").read_text(encoding="utf-8"))

sport_filter = sys.argv[1] if len(sys.argv) > 1 else ""
for ev in MODEL["events"]:
    if sport_filter and ev["sport"].lower() != sport_filter.lower():
        continue
    p = ev.get("pick") or {}
    facts = "; ".join(f"{k}={v}" for k, v in (ev.get("facts") or {}).items() if v not in (None, ""))
    print(f"{ev['key']} | {ev['sport']} | {ev['start_utc'] or (ev.get('official') or {}).get('start_local','')} | "
          f"{ev['name']} | comp={ev.get('competition') or '-'} | tip={ev['primary_tip']['selection']} "
          f"[{ev['primary_tip']['market']}] quote={ev['primary_tip']['decimal']} "
          f"share={ev['primary_tip'].get('olbg_confidence')} tips={ev['primary_tip'].get('win_tips')} | "
          f"PICK={p.get('selection','-')} p={p.get('probability')} price={p.get('fair_american')} "
          f"conf={p.get('confidence')} inband={p.get('in_band')} tier={ev['tier']} | {facts} | "
          f"olbg={ev['olbg_url']} | off={(ev.get('official') or {}).get('source_url','-')}")
