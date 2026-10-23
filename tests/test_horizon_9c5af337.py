"""Unit tests for the /horizon/ 15-sport desk (session arena/9c5af337-olbg2)."""
import json
import os
import re
import unittest

from scripts.horizon_verify import EXPECTED_SLUGS, FORBIDDEN, MANDATED_SPORTS, PageInspector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "horizon")
SITE = os.path.join(ROOT, "horizon")


class HorizonDeskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(DATA, "sources.json")) as f:
            cls.sources = json.load(f)
        with open(os.path.join(DATA, "fixtures.json")) as f:
            cls.fixtures = json.load(f)
        with open(os.path.join(DATA, "lines.json")) as f:
            cls.lines = json.load(f)
        with open(os.path.join(DATA, "predictions.json")) as f:
            cls.predictions = json.load(f)
        with open(os.path.join(DATA, "flagged.json")) as f:
            cls.flagged = json.load(f)
        with open(os.path.join(DATA, "olbg_taxonomy.json")) as f:
            cls.olbg = json.load(f)
        with open(os.path.join(DATA, "repo_audit.json")) as f:
            cls.repo_audit = json.load(f)
        with open(os.path.join(DATA, "verification.json")) as f:
            cls.verification = json.load(f)

    def test_strictly_fifteen_mandated_sports(self):
        fx_sports = {r["sport"] for r in self.fixtures["fixtures"]}
        ln_sports = {r["sport"] for r in self.lines["records"]}
        pr_sports = {r["sport"] for r in self.predictions["predictions"]}
        olbg_sports = {r["sport"] for r in self.olbg["sports"]}
        self.assertEqual(fx_sports, MANDATED_SPORTS)
        self.assertEqual(ln_sports, MANDATED_SPORTS)
        self.assertEqual(pr_sports, MANDATED_SPORTS)
        self.assertEqual(olbg_sports, MANDATED_SPORTS)

        slugs = {
            os.path.splitext(fn)[0]
            for fn in os.listdir(os.path.join(SITE, "sports"))
            if fn.endswith(".html")
        }
        self.assertEqual(slugs, EXPECTED_SLUGS)

    def test_every_fixture_has_official_https_source(self):
        for r in self.fixtures["fixtures"]:
            self.assertTrue(r["official_source_url"].startswith("https://"), r["id"])
            self.assertGreaterEqual(len(r["facts"]), 1, r["id"])
            for fact in r["facts"]:
                self.assertTrue(fact["source_url"].startswith("https://"), r["id"])

    def test_line_origination_and_actionable_band(self):
        s = self.lines["summary"]
        self.assertEqual(s["total_fixtures"], len(self.lines["records"]))
        self.assertEqual(s["priced_fixtures"] + s["unpriced_fixtures"], s["total_fixtures"])
        self.assertGreaterEqual(s["confidence_counts"]["high"], 35)
        self.assertEqual(
            s["high_confidence_with_in_band_actionable_market"],
            s["confidence_counts"]["high"],
        )

        flagged_ids = {x["fixture_id"] for x in self.flagged["items"]}
        for r in self.lines["records"]:
            if r["priced"]:
                self.assertIn(r["confidence"], ("low", "medium", "high"))
                self.assertIsNotNone(r["winner_pick"])
                self.assertIsNotNone(r["winner_fair_american"])
                self.assertTrue(r["actionable_in_band"], r["id"])
                self.assertGreaterEqual(r["actionable_odds"], -250, r["id"])
                self.assertLessEqual(r["actionable_odds"], 10000, r["id"])
            else:
                self.assertIsNone(r["winner_pick"])
                self.assertIsNone(r["winner_fair_american"])
                self.assertIsNone(r["confidence"])
                self.assertIn(r["id"], flagged_ids)

    def test_predictions_prose_rules(self):
        preds = self.predictions["predictions"]
        self.assertEqual(len(preds), 54)
        openings = set()
        sentences = set()
        for p in preds:
            txt = p["prediction_text"]
            words = txt.split()
            self.assertGreaterEqual(len(words), 30, p["fixture_id"])
            self.assertEqual(len(words), p["word_count"], p["fixture_id"])
            self.assertIsNone(FORBIDDEN.search(txt), f"Forbidden word in {p['fixture_id']}")
            op = " ".join(words[:5]).lower()
            self.assertNotIn(op, openings, f"Duplicate opening in {p['fixture_id']}")
            openings.add(op)
            for sent in [x.strip() for x in re.split(r"(?<=[.!?])\s+", txt) if x.strip()]:
                self.assertNotIn(sent, sentences, f"Duplicate sentence in {p['fixture_id']}")
                sentences.add(sent)

    def test_html_pages_row_links_and_local_links(self):
        html_files = []
        for root, _dirs, files in os.walk(SITE):
            for fn in sorted(files):
                if fn.endswith(".html"):
                    html_files.append(os.path.join(root, fn))
        self.assertEqual(len(html_files), 19)

        for path in html_files:
            insp = PageInspector()
            with open(path, encoding="utf-8") as f:
                insp.feed(f.read())
            self.assertGreater(insp.total_tbody_rows, 0, path)
            self.assertEqual(insp.unlinked_tbody_rows, 0, path)
            for pt in insp.pred_texts:
                self.assertIsNone(FORBIDDEN.search(pt), path)
                self.assertGreaterEqual(len(pt.split()), 30, path)

    def test_verification_report_passed(self):
        self.assertTrue(self.verification["passed"])
        self.assertEqual(self.verification["unlinked_tbody_rows"], 0)
        self.assertEqual(self.verification["broken_local_links"], 0)


if __name__ == "__main__":
    unittest.main()
