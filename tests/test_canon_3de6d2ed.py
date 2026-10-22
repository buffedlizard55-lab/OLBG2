"""Structural tests for the /canon/ desk (session arena/3de6d2ed-olbg2)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "canon"
SITE_DIR = ROOT / "canon"

EXCLUDED_TERMS = ["soccer", "boxing", "ufc", "mma", "american football",
                  "hurling", "horse racing", "cycling", "special"]


def load(name):
    return json.loads((DATA_DIR / name).read_text())


class CanonDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")
        cls.preds = load("predictions.json")
        cls.flags = load("flagged.json")
        cls.sources = load("sources.json")

    def test_seventeen_sports_zero_excluded(self):
        sports = {m["sport_name"].lower() for m in self.matches["matches"]}
        self.assertEqual(len(sports), 17, sports)
        for s in sports:
            for term in EXCLUDED_TERMS:
                self.assertNotIn(term, s, f"excluded term '{term}' leaked into sport '{s}'")
            # "football" alone is only allowed as part of "gaelic football"
            if "football" in s:
                self.assertIn("gaelic", s)

    def test_every_row_has_https_source(self):
        for m in self.matches["matches"]:
            self.assertTrue(m["source_url"].startswith("https://"), m["id"])
        for p in self.preds["predictions"]:
            self.assertTrue(p["source_url"].startswith("https://"), p["id"])
        for f in self.flags["flags"]:
            self.assertTrue(f["source_url"].startswith("https://"), f["id"])

    def test_counts_are_internally_consistent(self):
        m = self.matches
        self.assertEqual(m["total_count"], len(m["matches"]))
        originated = [r for r in m["matches"] if r["lined"]]
        unlined = [r for r in m["matches"] if not r["lined"]]
        self.assertEqual(m["originated_count"], len(originated))
        self.assertEqual(m["unlined_count"], len(unlined))
        high = [r for r in m["matches"] if r["confidence"] == "high"]
        self.assertEqual(m["high_confidence_count"], len(high))

    def test_unlined_rows_have_no_markets_and_no_confidence(self):
        for m in self.matches["matches"]:
            if not m["lined"]:
                self.assertEqual(m["markets"], [], m["id"])
                self.assertIsNone(m["confidence"], m["id"])
                self.assertIsNone(m["top_market"], m["id"])

    def test_uniform_high_confidence_odds_window(self):
        for m in self.matches["matches"]:
            for mk in m["markets"]:
                if mk["confidence"] == "high":
                    self.assertGreaterEqual(mk["probability"], 0.70, m["id"])
                    self.assertTrue(-250 <= mk["fair_american"] <= 10000, m["id"])
                    self.assertTrue(1.40 <= mk["fair_decimal"] <= 101.00, m["id"])

    def test_predictions_min_30_words_and_unique(self):
        texts = [p["prediction"] for p in self.preds["predictions"]]
        for p in self.preds["predictions"]:
            self.assertGreaterEqual(p["word_count"], 30, p["id"])
            self.assertGreaterEqual(len(p["prediction"].split()), 30, p["id"])
        self.assertEqual(len(texts), len(set(texts)), "duplicate prediction text found")

    def test_predictions_have_distinct_openers(self):
        openers = [" ".join(p["prediction"].split()[:4]) for p in self.preds["predictions"]]
        self.assertEqual(len(openers), len(set(openers)), "repeated opening phrase across predictions")

    def test_predictions_strictly_in_band(self):
        for p in self.preds["predictions"]:
            self.assertGreaterEqual(p["probability"], 0.70, p["id"])
            self.assertTrue(-250 <= p["fair_american"] <= 10000, p["id"])

    def test_predictions_carry_explicit_selection_and_price_in_text(self):
        for p in self.preds["predictions"]:
            self.assertIn(p["selection"], p["prediction"], p["id"])
            american_str = f"+{p['fair_american']}" if p["fair_american"] > 0 else str(p["fair_american"])
            self.assertIn(american_str, p["prediction"], p["id"])

    def test_flagged_items_present_and_sourced(self):
        self.assertGreaterEqual(self.flags["count"], 8)
        ids = [f["id"] for f in self.flags["flags"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_unclassified_sources(self):
        unclassified = [s for s in self.sources["sources"] if s["publisher"].startswith("UNCLASSIFIED")]
        self.assertEqual(unclassified, [])

    def test_source_registry_covers_every_match_url(self):
        registered = {s["url"] for s in self.sources["sources"]}
        for m in self.matches["matches"]:
            self.assertIn(m["source_url"], registered, m["id"])


class CanonSiteTests(unittest.TestCase):
    def test_site_builds_without_error(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "canon_verify.py")],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_expected_pages_exist(self):
        expected = ["index.html", "matches.html", "picks.html", "flagged.html",
                    "audit.html", "methodology.html", "sources.html", "sports/index.html"]
        for rel in expected:
            self.assertTrue((SITE_DIR / rel).is_file(), rel)

    def test_per_sport_pages_exist(self):
        sports = {m["sport"] for m in load("matches.json")["matches"]}
        self.assertEqual(len(sports), 17)
        for slug in sports:
            self.assertTrue((SITE_DIR / "sports" / f"{slug}.html").is_file(), slug)


if __name__ == "__main__":
    unittest.main()
