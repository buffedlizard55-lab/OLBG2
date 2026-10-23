import json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
D = ROOT/"data"/"focus"

class Focus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads((D/"matches.json").read_text())["matches"]
        cls.p = json.loads((D/"predictions.json").read_text())["predictions"]
        cls.inp = json.loads((D/"inputs.json").read_text())
    def test_15_sports(self):
        self.assertEqual(len(self.inp["sports"]), 15)
        self.assertEqual(set(x["sport"] for x in self.m), set(self.inp["sports"]))
    def test_every_row_sourced(self):
        for row in self.m: self.assertTrue(row["source_url"].startswith("https://"), row["id"])
    def test_prices_recompute(self):
        for row in self.m:
            for p in row["prices"]:
                self.assertAlmostEqual(max(round(1/p["p"],2),1.01), p["decimal"], places=1)
    def test_high_gate(self):
        for row in self.m:
            for p in row["in_band"]:
                self.assertGreaterEqual(p["p"], 0.70); self.assertLessEqual(p["p"], 5/7+1e-9)
                self.assertGreaterEqual(p["american"], -250); self.assertLessEqual(p["american"], 10000)
    def test_predictions(self):
        for p in self.p:
            self.assertGreaterEqual(len(p["text"].split()), 30)
            self.assertNotIn("model", p["text"].lower()); self.assertNotIn("verified", p["text"].lower())
    def test_pages_exist(self):
        for name in ["index.html","matches.html","top5.html","predictions.html","flagged.html","sources.html","methodology.html"]:
            self.assertTrue((ROOT/"focus"/name).exists(), name)
    def test_blank_rows_have_no_prices(self):
        for row in self.m:
            if row["confidence"]=="blank": self.assertEqual(row["prices"], [])

if __name__ == "__main__": unittest.main()
