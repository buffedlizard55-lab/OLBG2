"""Quest desk tests (session 693dbf40). Read-only: committed data + pages."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def load(name):
    return json.loads((ROOT / "data" / "quest" / name).read_text())


class TestQuestDesk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fix = load("fixtures.json")
        cls.lines = load("lines.json")["lines"]
        cls.picks = load("picks.json")["picks"]
        cls.top5 = load("top5.json")["top5"]
        cls.preds = load("predictions.json")["predictions"]

    def test_exactly_15_sports_everywhere(self):
        sports = {f["sport"] for f in self.fix["fixtures"]}
        self.assertEqual(len(sports), 15)
        self.assertEqual(set(self.top5), sports)

    def test_counts_match_meta(self):
        m = self.fix["meta"]
        self.assertEqual(m["fixtures"], len(self.fix["fixtures"]))
        self.assertEqual(m["lines"], len(self.lines))
        self.assertEqual(m["picks"], len(self.picks))
        self.assertEqual(m["predictions"], len(self.preds))
        self.assertEqual(m["cutoff_utc"], "2026-10-23T21:30:00Z")

    def test_every_fixture_has_official_link_and_none_started(self):
        for f in self.fix["fixtures"]:
            self.assertTrue(f["official_source_url"].startswith("https://"), f["id"])
            if f["start_utc"]:
                self.assertGreaterEqual(f["start_utc"], "2026-10-23T21:30:00Z", f["id"])

    def test_blank_fixtures_have_reason_and_no_lines(self):
        lined = {l["fixture_id"] for l in self.lines}
        for f in self.fix["fixtures"]:
            if f["status"] == "blank":
                self.assertTrue(f["blank_reason"], f["id"])
                self.assertNotIn(f["id"], lined, f["id"])

    def test_window_flags_and_high_threshold(self):
        for l in self.lines:
            self.assertEqual(l["in_band"], -250 <= l["fair_american"] <= 10000, l["id"])
            if l["confidence"] == "high":
                self.assertGreaterEqual(l["probability"], 0.70, l["id"])

    def test_every_in_window_high_pick_has_prose(self):
        covered = {x["pick_id"] for x in self.preds}
        for p in self.picks:
            if p["confidence"] == "high" and p["in_band"]:
                self.assertIn(p["id"], covered, p["id"])

    def test_prose_rules(self):
        banned = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
        texts = [x["text"] for x in self.preds]
        self.assertEqual(len(texts), len(set(texts)), "duplicate prediction text")
        for x in self.preds:
            self.assertGreaterEqual(len(x["text"].split()), 30, x["id"])
            self.assertIsNone(banned.search(x["text"]), x["id"])
            self.assertIsNone(banned.search(x["headline"]), x["id"])
            self.assertTrue(x["facts"], x["id"])

    def test_top5_rule(self):
        for sport, rows in self.top5.items():
            self.assertLessEqual(len(rows), 5, sport)
            probs = [r["probability"] for r in rows]
            self.assertEqual(probs, sorted(probs, reverse=True), sport)

    def test_verifier_passes(self):
        import quest_verify
        self.assertEqual(quest_verify.run(), [])

    def test_pages_exist(self):
        for name in ("index.html", "today.html", "matches.html", "markets.html",
                     "picks.html", "top5.html", "predictions.html", "olbg.html",
                     "methodology.html", "sources.html", "flagged.html"):
            self.assertTrue((ROOT / "quest" / name).exists(), name)
        self.assertEqual(len(list((ROOT / "quest" / "sports").glob("*.html"))), 15)


if __name__ == "__main__":
    unittest.main()
