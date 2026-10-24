#!/usr/bin/env python3
"""Validate the 22:32Z first-hand OLBG hub and official-source recheck dossier.

The dossier is committed evidence, not a live network call: it records the exact URL,
time, status and observation from each first-hand page read. This script fails closed if
a hub is missing, a sport falls outside the exact fifteen, an entry lacks a result, or a
link is not HTTPS. ``now_seed.py`` copies the dossier into ``data/now/checks.json`` and
``now_build.py`` publishes it so readers can repeat the manual review.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "final-desk" / "rechecks.json"
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
VALID_STATUS = {"confirmed", "changed", "partial", "no-listings", "futures-only"}


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    errors: list[str] = []
    hubs = data.get("hub_checks", [])
    officials = data.get("official_checks", [])
    if data.get("checked_utc") != "2026-10-24T22:32:00Z":
        errors.append("unexpected recheck timestamp")
    if len(hubs) != 15:
        errors.append(f"expected 15 hub checks, found {len(hubs)}")
    if [h.get("sport") for h in hubs] != SPORTS:
        errors.append("hub sport order does not match the exact fifteen sports")
    if len(officials) < 15:
        errors.append(f"expected at least 15 official checks, found {len(officials)}")
    official_sports = {s for row in officials for s in row.get("sports", [])}
    if not set(SPORTS) <= official_sports:
        errors.append("official checks do not cover every requested sport")
    for group, rows in (("hub", hubs), ("official", officials)):
        urls = set()
        for row in rows:
            label = row.get("hub") or row.get("publisher") or "?"
            url = row.get("url", "")
            if not url.startswith("https://"):
                errors.append(f"{group} {label}: URL is not HTTPS")
            if url in urls:
                errors.append(f"{group} {label}: duplicate URL {url}")
            urls.add(url)
            if row.get("status") not in VALID_STATUS:
                errors.append(f"{group} {label}: unknown status {row.get('status')!r}")
            if not row.get("result", "").strip():
                errors.append(f"{group} {label}: empty result")
            if not isinstance(row.get("flag"), bool):
                errors.append(f"{group} {label}: flag is not boolean")
    if errors:
        print(f"final_recheck: {len(errors)} errors")
        for err in errors:
            print("  FAIL", err)
        return 1
    print(f"final_recheck: {len(hubs)} OLBG hubs, {len(officials)} official pages, "
          f"{sum(1 for r in hubs + officials if r['flag'])} flagged observations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
