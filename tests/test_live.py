"""Checks for the Layer-4 live slate (session arena/d4b9d560-olbg2)."""
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
LIVE = os.path.join(ROOT, "data", "live")


def load(name):
    with open(os.path.join(LIVE, name)) as fh:
        return json.load(fh)


class LiveSlate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "live_model.py")],
                       check=True, capture_output=True)
        cls.lines = load("lines.json")
        cls.rows = cls.lines["rows"]

    def test_every_row_has_an_official_source(self):
        for row in self.rows:
            self.assertTrue(row["source_url"].startswith("https://"), row["id"])
            self.assertTrue(row["inputs"]["source_url"].startswith("https://"), row["id"])

    def test_three_markets_priced_on_every_row(self):
        for row in self.rows:
            self.assertEqual(set(row["markets"]), {"match_winner", "handicap", "total"}, row["id"])
            for block in row["markets"].values():
                self.assertTrue(block["options"])
                for priced in block["options"].values():
                    self.assertGreater(priced["probability"], 0.0)
                    self.assertLess(priced["probability"], 1.0)
                    self.assertGreater(priced["decimal"], 1.0)

    def test_match_winner_options_sum_to_one(self):
        for row in self.rows:
            total = sum(p["probability"] for p in row["markets"]["match_winner"]["options"].values())
            self.assertAlmostEqual(total, 1.0, places=2, msg=row["id"])

    def test_every_row_has_a_pick_and_confidence(self):
        for row in self.rows:
            self.assertIn(row["pick"]["confidence"], {"high", "medium", "low"})
            self.assertEqual(row["pick"]["market"], "match_winner")

    def test_high_confidence_picks_have_long_predictions(self):
        highs = [r for r in self.rows if r["pick"]["confidence"] == "high"]
        self.assertTrue(highs, "expected at least one high-confidence pick")
        for row in highs:
            self.assertIsNotNone(row["prediction"], row["id"])
            self.assertGreaterEqual(row["prediction"]["words"], 30, row["id"])
            self.assertIn(row["home_name"], row["prediction"]["text"] + " " + row["prediction"]["text"].lower())

    def test_predictions_only_on_high_picks(self):
        for row in self.rows:
            if row["pick"]["confidence"] != "high":
                self.assertIsNone(row["prediction"], row["id"])

    def test_no_high_label_fails_the_published_window_rule(self):
        # Uniform rule across layers: high requires probability >= 0.72, or
        # >= 0.70 with the fair no-vig price inside [-250, +10000]. Never high
        # below the 70% floor.
        def fair_american(prob):
            return round(-100.0 / (1.0 / prob - 1.0)) if prob >= 0.5 else round((1.0 / prob - 1.0) * 100.0)

        for row in self.rows:
            prob = row["pick"]["probability"]
            if row["pick"]["confidence"] == "high":
                self.assertGreaterEqual(prob, 0.70, row["id"])
                in_band = -250 <= fair_american(prob) <= 10000
                self.assertTrue(prob >= 0.72 or in_band, row["id"])

    def test_predictions_carry_price_band_annotations(self):
        preds = load("predictions.json")["predictions"]
        self.assertTrue(preds)
        for pr in preds:
            self.assertIn(pr["price_band"], {"in-band", "outside-band"}, pr["fixture_id"])
            row = next(r for r in self.rows if r["id"] == pr["fixture_id"])
            prob = row["pick"]["probability"]
            am = round(-100.0 / (1.0 / prob - 1.0)) if prob >= 0.5 else round((1.0 / prob - 1.0) * 100.0)
            self.assertEqual(pr["fair_american"], am, pr["fixture_id"])
            expected = "in-band" if -250 <= am <= 10000 else "outside-band"
            self.assertEqual(pr["price_band"], expected, pr["fixture_id"])

    def test_run_line_price_is_venue_independent(self):
        """The model applies no home edge, so a side's run-line price must not depend on venue."""
        mlb = [r for r in self.rows if r["sport"] == "Baseball"]
        self.assertEqual(len(mlb), 3)
        for team in ("MIL", "TB"):
            prices = {r["markets"]["handicap"]["options"][team]["probability"]
                      for r in mlb if team in r["markets"]["handicap"]["options"]}
            self.assertEqual(len(prices), 1, "%s run-line price varies by venue: %s" % (team, prices))
        for r in mlb:
            fav = "MIL"
            self.assertLess(r["markets"]["handicap"]["options"][fav]["probability"], 0.5, r["id"])

    def test_flags_all_have_sources(self):
        flags = load("flags.json")["flags"]
        self.assertTrue(flags)
        for flag in flags:
            self.assertTrue(flag["sources"], flag["id"])
            self.assertTrue(all(s.startswith("https://") for s in flag["sources"]), flag["id"])

    def test_coverage_lists_every_sport_with_a_status(self):
        for sport in load("coverage.json")["sports"]:
            self.assertTrue(sport["status"], sport["sport"])

    def test_model_is_deterministic(self):
        before = json.dumps(self.lines, sort_keys=True)
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "live_model.py")],
                       check=True, capture_output=True)
        self.assertEqual(before, json.dumps(load("lines.json"), sort_keys=True))


class SiteBuild(unittest.TestCase):
    def test_build_writes_pages_with_no_broken_links(self):
        result = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "live_build.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 broken local links", result.stdout)
        for name in ("index.html", "picks.html", "flagged.html", "methodology.html",
                     "sports/rugby-union.html", "sports/baseball.html", "assets/style.css"):
            path = os.path.join(ROOT, "live", name)
            self.assertTrue(os.path.exists(path), path)
            self.assertGreater(os.path.getsize(path), 500, path)

    def test_pages_carry_source_links(self):
        with open(os.path.join(ROOT, "live", "index.html")) as fh:
            text = fh.read()
        self.assertGreaterEqual(text.count(">official source<"), 22)
        self.assertIn("stats.unitedrugby.com", text)
        self.assertIn("statsapi.mlb.com", text)


if __name__ == "__main__":
    unittest.main()
