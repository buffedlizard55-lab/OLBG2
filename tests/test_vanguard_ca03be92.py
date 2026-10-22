"""Tests for the /vanguard/ desk (session ca03be92)."""
import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "vanguard"
V = ROOT / "vanguard"


def load(n):
    return json.loads((D / n).read_text())


class TestVanguard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("matches.json"); cls.l = load("lines.json")
        cls.p = load("predictions.json"); cls.f = load("flagged.json")

    def test_seventeen_sports_and_scope(self):
        sports = {x["sport"] for x in self.m["matches"]}
        self.assertEqual(len(sports), 17)
        banned = {"soccer", "football", "boxing", "ufc", "mma", "american-football",
                  "hurling", "horse-racing", "cycling", "specials"}
        self.assertFalse(sports & banned)

    def test_every_fixture_has_official_https_source(self):
        for x in self.m["matches"]:
            self.assertTrue(x["source_url"].startswith("https://"), x["id"])

    def test_prices_are_reciprocals_of_probability(self):
        for x in self.l["rows"]:
            self.assertAlmostEqual(x["decimal"], round(1 / x["p"], 2), delta=0.011)

    def test_band_gate_is_exact(self):
        for x in self.l["rows"]:
            if x.get("in_band"):
                self.assertGreaterEqual(x["p"], 0.69995)
                self.assertLessEqual(x["p"], 5 / 7 + 1e-9)
                self.assertGreaterEqual(x["american"], -250)
                self.assertLessEqual(x["american"], 10000)

    def test_high_confidence_rows_imply_a_band_pick(self):
        for x in self.m["matches"]:
            if x["confidence"] == "high":
                self.assertTrue(x["in_band"], x["id"])

    def test_predictions_meet_the_prose_rules(self):
        for p in self.p["predictions"]:
            self.assertGreaterEqual(len(p["text"].split()), 30)
            self.assertGreaterEqual(p["words"], 30)
            self.assertIn(p["selection"].split()[0], p["text"])
            self.assertEqual(p["confidence"], "high")
            self.assertGreaterEqual(p["probability"], 0.70)
            self.assertLessEqual(p["probability"], 5 / 7 + 1e-9)

    def test_prediction_openings_are_unique(self):
        heads = [p["text"][:40] for p in self.p["predictions"]]
        self.assertEqual(len(heads), len(set(heads)))

    def test_shortfall_disclosed_for_every_sport_under_five(self):
        short = {s["sport"] for s in self.p["shortfall"]}
        for p in self.p["predictions"]:
            if sum(1 for q in self.p["predictions"] if q["sport"] == p["sport"]) < 5:
                self.assertIn(p["sport"], short)

    def test_blank_rows_are_flagged(self):
        blank = [x["id"] for x in self.m["matches"] if x["confidence"] == "blank"]
        flagged = {f["fixture"] for f in self.f["flags"] if f["kind"] == "blank market"}
        for b in blank:
            self.assertIn(b, flagged)

    def test_rendered_pages_carry_their_headline_numbers(self):
        idx = (V / "index.html").read_text()
        self.assertIn(f'{self.m["counts"]["fixtures"]}</b><span>verified fixtures', idx)
        picks = (V / "picks.html").read_text()
        band = sum(1 for x in self.l["rows"] if x.get("in_band"))
        self.assertIn(f"{band} in-band selections", picks)
        self.assertEqual(band, len(re.findall(r'<tr><td>[^<]*</td><td>[^<]*</td><td>(?:match winner|handicap|match total)</td>', picks)))

    def test_sport_pages_exist(self):
        self.assertTrue((ROOT / "vanguard" / "sports" / "index.html").is_file())
        self.assertEqual(len(list((ROOT / "vanguard" / "sports").glob("*.html"))), 18)


if __name__ == "__main__":
    unittest.main()
