"""Regression tests for the 24 October board (/today/)."""
from __future__ import annotations
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


class TodayBoardTests(unittest.TestCase):
    def test_all_fifteen_sports_present(self):
        self.assertEqual(set(load("olbg_listings")["hubs"]), set(SPORTS))
        self.assertEqual(len(SPORTS), 15)

    def test_every_listing_is_an_olbg_url_with_matching_event_id(self):
        rows = load("olbg_listings")["listings"]
        self.assertGreater(len(rows), 50)
        for row in rows:
            self.assertTrue(row["url"].startswith("https://www.olbg.com/betting-tips/"), row)
            self.assertIn(f"event_id={row['event_id']}", row["url"])
            self.assertTrue(row["event"] and row["selection"])

    def test_prices_are_consistent_with_probabilities(self):
        for line in load("lines")["lines"]:
            p = line["probability"]
            fair = line["fair_american"]
            implied = (-fair / (-fair + 100)) if fair < 0 else (100 / (fair + 100))
            self.assertAlmostEqual(implied, p, delta=0.02, msg=line["id"])

    def test_confidence_and_band_flags(self):
        for pick in load("picks")["picks"]:
            want = "high" if pick["probability"] >= 0.70 else ("medium" if pick["probability"] >= 0.55 else "low")
            self.assertEqual(pick["confidence"], want, pick["fixture_id"])
            self.assertEqual(pick["in_band"], -250 <= pick["fair_american"] <= 10000, pick["fixture_id"])

    def test_previews_are_long_unique_and_clean(self):
        preds = load("predictions")["predictions"]
        self.assertGreaterEqual(len(preds), 5)
        seen = set()
        banned = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
        for p in preds:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["id"])
            self.assertEqual(p["word_count"], len(p["text"].split()))
            self.assertIsNone(re.search(banned, p["text"]), p["id"])
            self.assertNotIn(p["text"].lower(), seen, p["id"])
            seen.add(p["text"].lower())
            self.assertGreaterEqual(len(p["facts"]), 2)
            for fact in p["facts"]:
                self.assertTrue(fact["source_url"].startswith("https://"), fact)

    def test_every_pick_has_a_preview_and_a_source(self):
        picks = {p["fixture_id"] for p in load("picks")["picks"]}
        preds = {p["fixture_id"] for p in load("predictions")["predictions"]}
        self.assertEqual(picks, preds)
        for p in load("picks")["picks"]:
            self.assertTrue(p["source_url"].startswith("https://"))

    def test_fixtures_only_from_official_feeds(self):
        allowed = (
            "https://api-web.nhle.com/", "https://statsapi.mlb.com/", "https://www.nba.com/",
            "https://www.atptour.com/", "https://www.wtatennis.com/", "https://wtafiles.wtatennis.com/",
            "https://www.legavolley.it/", "https://www.lnh.fr/", "https://www.opel-hbl.de/",
            "https://www.formula1.com/", "https://www.pdc.tv/",
        )
        for f in load("olbg_listings")["fixtures"]:
            self.assertTrue(f["source_url"].startswith(allowed), f["id"])

    def test_every_sport_page_exists(self):
        for sport in SPORTS:
            slug = sport.lower().replace(" ", "-")
            page = ROOT / "today" / "sports" / f"{slug}.html"
            self.assertTrue(page.is_file(), sport)

    def test_verifier_passes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "today_verify.py")],
                                capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 errors", result.stdout)


if __name__ == "__main__":
    unittest.main()
