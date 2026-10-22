import json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

class TestFresh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((ROOT / "data/fresh/audit.json").read_text())
        cls.c = cls.audit["checks"]
        cls.rows = json.loads((ROOT / "data/verified/matches.json").read_text())["matches"]

    def test_no_excluded_leakage_or_duplicates(self):
        self.assertEqual(self.c["excluded_sport_leakage_rows"], [])
        self.assertEqual(self.c["duplicate_ids"], [])
        self.assertEqual(self.c["duplicate_fixtures"], [])

    def test_all_rows_have_official_link(self):
        self.assertEqual(self.c["rows_without_official_https_url"], [])
        self.assertEqual(len(self.rows), 188)

    def test_probability_arithmetic(self):
        self.assertEqual(self.c["winner_prob_sum_failures"], [])
        self.assertEqual(self.c["handicap_total_prob_sum_failures"], [])
        self.assertEqual(self.c["fair_odds_failures"], [])

    def test_gate_violations_are_published_not_hidden(self):
        # FR-01 must stay visible until the upstream owner regrades them.
        ids = {g["match_id"] for g in self.c["confidence_gate_violations"]}
        self.assertEqual(ids, {"nhl-2026020159", "pdc-32323"})
        self.assertTrue(any(f["id"] == "FR-01" for f in self.audit["flags"]))

    def test_predictions_meet_brief(self):
        self.assertEqual(self.c["predictions_under_30_words"], [])
        self.assertEqual(self.c["duplicate_prediction_texts"], 0)
        self.assertEqual(self.c["predictions_with_unknown_match_id"], [])
        self.assertEqual(self.c["predictions_without_fact_sources"], [])

    def test_fresh_pages_built_with_source_links(self):
        for name in ("index", "matches", "picks", "flagged", "sources", "methodology"):
            html = (ROOT / f"fresh/{name}.html").read_text()
            self.assertIn("https://", html, name)
        matches = (ROOT / "fresh/matches.html").read_text()
        self.assertEqual(matches.count("<tr>") - 1, 188)  # minus header row in thead usage

if __name__ == "__main__":
    unittest.main()
