"""Integrity tests for the root dashboard's originated data.

These check internal consistency only. They do not and cannot verify an external
fact; every external claim is checked against the cited official source by hand,
and the record of that work lives in research/.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


class DashboardIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")
        cls.preds = load("predictions.json")["predictions"]
        cls.by_id = {m["id"]: m for m in cls.matches["matches"]}

    def test_every_high_confidence_row_has_exactly_one_prediction(self):
        high = {m["id"] for m in self.matches["matches"] if m.get("confidence") == "high"}
        predicted = [p["match_id"] for p in self.preds]
        self.assertEqual(sorted(high), sorted(predicted))
        self.assertEqual(len(predicted), len(set(predicted)))

    def test_predictions_are_long_enough_and_unique(self):
        texts = [p["text"] for p in self.preds]
        for p in self.preds:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["match_id"])
        self.assertEqual(len(texts), len(set(texts)))

    def test_prediction_quotes_the_published_probability(self):
        for p in self.preds:
            row = self.by_id[p["match_id"]]
            expected = f'{row["pick"]["probability"] * 100:.1f}%'
            self.assertIn(expected, p["text"], p["match_id"])

    def test_every_prediction_fact_cites_a_url(self):
        for p in self.preds:
            self.assertTrue(p["facts"], p["match_id"])
            for fact in p["facts"]:
                self.assertRegex(fact["source"], r"^(https://|data/)", p["match_id"])
                self.assertTrue(fact["claim"].strip(), p["match_id"])

    def test_every_fixture_cites_an_official_source_url(self):
        for m in self.matches["matches"]:
            self.assertTrue(m["fixture_source"]["url"].startswith("https://"), m["id"])

    def test_handball_rows_are_all_lined_and_come_from_ehf(self):
        rows = [m for m in self.matches["matches"] if m["sport"] == "Handball"]
        self.assertEqual(len(rows), 12)
        for m in rows:
            self.assertEqual(m["line_status"], "originated")
            self.assertIn("ehfcl.eurohandball.com", m["fixture_source"]["url"])
            self.assertIn("ehfcl.eurohandball.com", m["data_source"]["url"])
            markets = {x["market"] for x in m["markets"]}
            self.assertEqual(markets, {"Match winner", "Handicap", "Match total"})
            for mk in m["markets"]:
                self.assertGreater(mk["probability"], 0)
                self.assertLess(mk["probability"], 1)
                self.assertGreaterEqual(mk["price"], 1.05)


if __name__ == "__main__":
    unittest.main()
