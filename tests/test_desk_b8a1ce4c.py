"""Tests for the /desk/ 15-sport layer (session arena/b8a1ce4c-olbg2)."""
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESK = os.path.join(ROOT, "desk")


def load(name):
    with open(os.path.join(ROOT, "data/olbgdesk", name)) as fh:
        return json.load(fh)


class DeskVerifierTest(unittest.TestCase):
    def test_verifier_passes(self):
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/desk_verify.py")],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ALL CHECKS PASS", proc.stdout)


class DeskDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = load("olbg_inventory.json")
        cls.rows = [dict(zip(cls.inv["header"], r)) for r in cls.inv["rows"]]
        cls.inputs = load("inputs.json")
        cls.lines = load("lines.json")["lines"]
        cls.preds = load("predictions.json")["predictions"]
        cls.flags = load("flagged.json")["flags"]

    def test_inventory_shape(self):
        self.assertEqual(len(self.rows), 125)
        self.assertEqual({r["sport"] for r in self.rows} & {"Golf"}, set())
        self.assertTrue(all(r["event_id"] for r in self.rows))

    def test_every_inventory_row_has_a_positive_tip_sample(self):
        for r in self.rows:
            self.assertGreater(r["tips"], 0, r["event"])
            self.assertLessEqual(r["tips"], r["total"], r["event"])

    def test_fixtures_all_cite_a_governing_body(self):
        for f in self.inputs["fixtures"]:
            self.assertTrue(f["src"].startswith("https://"))
            self.assertNotIn("olbg.com", f["src"])

    def test_two_price_bases_are_never_mixed(self):
        for l in self.lines:
            self.assertIn(l["basis"], ("official", "consensus"))
            if l["basis"] == "consensus":
                self.assertGreater(l["sample"], 0)
                self.assertIn("OLBG", l["basis_note"])

    def test_high_confidence_follows_the_seventy_percent_rule(self):
        for l in self.lines:
            self.assertEqual(l["confidence"] == "high", l["p"] >= 0.70, l["fixture"])

    def test_band_is_the_brief_price_range(self):
        for l in self.lines:
            self.assertEqual(l["in_band"], 1.40 <= l["fair_decimal"] <= 101.00, l["fixture"])

    def test_predictions_are_long_unique_and_clean(self):
        openings = set()
        for p in self.preds:
            self.assertGreaterEqual(len(re.findall(r"[A-Za-z0-9'\-]+", p["text"])), 30)
            low = p["text"].lower()
            for banned in ("model", "verified"):
                self.assertNotIn(banned, low)
            first = p["text"].split()[0]
            self.assertNotIn(first, openings)
            openings.add(first)

    def test_prediction_matches_a_priced_high_confidence_market(self):
        for p in self.preds:
            match = [l for l in self.lines if l["sid"] == p["sid"]
                     and l["selection"] == p["selection"] and l["market"] == p["market"]]
            self.assertEqual(len(match), 1, p["selection"])
            self.assertEqual(match[0]["confidence"], "high")

    def test_flags_are_sourced(self):
        self.assertEqual(len(self.flags), 17)
        for f in self.flags:
            self.assertTrue(f["source"].startswith("https://"), f["id"])

    def test_no_unresolved_conflict_marker_in_this_layers_files(self):
        for base, _, files in os.walk(DESK):
            for fn in files:
                if fn.endswith(".html"):
                    body = open(os.path.join(base, fn), encoding="utf-8").read()
                    for marker in ("<<<<<<<", ">>>>>>>"):
                        self.assertNotIn(marker, body, fn)

    def test_sport_pages_cover_the_brief_list(self):
        expected = {"golf", "volleyball", "rugby-union", "cricket", "snooker", "darts", "baseball",
                    "gaelic-sports", "greyhounds", "tennis", "motor-racing", "handball",
                    "ice-hockey", "basketball", "rugby-league"}
        built = {f[:-5] for f in os.listdir(os.path.join(DESK, "sports")) if f.endswith(".html")}
        self.assertEqual(built, expected)


if __name__ == "__main__":
    unittest.main()
