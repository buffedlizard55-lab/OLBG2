#!/usr/bin/env python3
"""Tests for the 22:32Z final-integration source dossier and published recheck pages."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class FinalRecheck(unittest.TestCase):
    def test_validator_passes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "final_recheck.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dossier_is_exact_fifteen_and_first_hand(self):
        dossier = load("data/final-desk/rechecks.json")
        self.assertEqual(dossier["checked_utc"], "2026-10-24T22:32:00Z")
        self.assertEqual([h["sport"] for h in dossier["hub_checks"]], SPORTS)
        self.assertGreaterEqual(len(dossier["official_checks"]), 15)
        self.assertTrue(set(SPORTS) <= {
            sport for check in dossier["official_checks"] for sport in check["sports"]
        })
        for row in dossier["hub_checks"] + dossier["official_checks"]:
            self.assertTrue(row["url"].startswith("https://"))
            self.assertTrue(row["result"].strip())

    def test_published_checks_and_top_five_are_complete(self):
        checks = load("data/now/checks.json")
        top5 = load("data/now/top5.json")
        self.assertEqual(checks["hub_count"], 15)
        self.assertEqual(len(top5["by_sport"]), 15)
        for sport, group in top5["by_sport"].items():
            self.assertIn(sport, SPORTS)
            self.assertLessEqual(group["count"], 5)
            self.assertEqual(group["count"], len(group["lines"]))
            for line in group["lines"]:
                self.assertTrue(line["in_band"])
                self.assertTrue(line["official_url"].startswith("https://"))
        checks_html = (ROOT / "now" / "checks.html").read_text(encoding="utf-8")
        top5_html = (ROOT / "now" / "top5.html").read_text(encoding="utf-8")
        for hub in load("data/now/checks.json")["hub_checks"]:
            self.assertIn(hub["url"], checks_html)
        for sport in SPORTS:
            slug = sport.lower().replace(" ", "-")
            self.assertIn(f'id="{slug}"', top5_html)
            sport_html = (ROOT / "now" / "sports" / f"{slug}.html").read_text(encoding="utf-8")
            self.assertIn('id="top5"', sport_html)

    def test_every_pick_has_a_preview(self):
        picks = load("data/now/picks.json")
        preds = load("data/now/predictions.json")
        written = {p["fixture_id"] for p in preds["predictions"]}
        self.assertEqual(preds.get("missing_for_published_pick"), [])
        self.assertEqual(len(picks["picks"]), preds["count"])
        for pick in picks["picks"]:
            self.assertIn(pick["fixture_id"], written)


if __name__ == "__main__":
    unittest.main()
