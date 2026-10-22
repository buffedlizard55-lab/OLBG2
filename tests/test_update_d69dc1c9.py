#!/usr/bin/env python3
"""Tests for the /update/ layer (session arena/d69dc1c9-olbg2).

Covers the model outputs in data/update/, the high-confidence gate, the no-inference
policy, write-up quality, and the rendered site in update/.
"""
import glob
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(ROOT, "data", "update")
OUT = os.path.join(ROOT, "update")
WIN_START, WIN_END = "2026-10-22", "2026-10-28"

SPORTS = {"tennis", "darts", "snooker", "golf", "cricket", "baseball", "basketball",
          "ice-hockey", "rugby-union", "rugby-league", "handball", "volleyball",
          "aussie-rules", "motor-racing", "esports", "greyhounds", "gaelic-football"}
EXCLUDED = {"soccer", "football", "american-football", "boxing", "ufc", "mma",
            "hurling", "horse-racing", "cycling", "specials"}


def load(name):
    return json.load(open(os.path.join(UPD, name)))


class UpdateDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")["matches"]
        cls.preds = load("predictions.json")["predictions"]
        cls.band = load("band.json")["picks"]
        cls.flags = load("flagged.json")["items"]
        cls.sources = load("sources.json")["sources"]
        cls.inputs = load("inputs.json")

    def test_files_exist(self):
        for name in ("inputs.json", "sources.json", "matches.json", "predictions.json",
                     "band.json", "flagged.json"):
            self.assertTrue(os.path.exists(os.path.join(UPD, name)), name)

    def test_every_match_has_official_source(self):
        for m in self.matches:
            self.assertTrue((m.get("official_url") or "").startswith("http"),
                            f"{m['id']} missing official source")

    def test_no_excluded_sports(self):
        for m in self.matches:
            self.assertNotIn(m["sport"], EXCLUDED, m["id"])
            self.assertIn(m["sport"], SPORTS, m["id"])

    def test_window_discipline(self):
        for m in self.matches:
            self.assertGreaterEqual(m["date"], WIN_START, m["id"])
            self.assertLessEqual(m["date"], WIN_END, m["id"])

    def test_capture_labels_present(self):
        for m in self.matches:
            self.assertTrue(m.get("capture"), m["id"])
        fresh = [m for m in self.matches if m["capture"] == "this session"]
        self.assertGreater(len(fresh), 50, "fresh captures expected to dominate the layer")

    def test_high_confidence_gate(self):
        for p in self.preds:
            if p.get("confidence") == "high":
                self.assertGreaterEqual(p["prob"], 0.70, p["id"])
                self.assertTrue(-250 <= p["american"] <= 10000, p["id"])

    def test_band_odds_window(self):
        for p in self.band:
            self.assertTrue(-250 <= p["american"] <= 10000, p["id"])
            self.assertTrue(p["in_band"], p["id"])

    def test_high_writeups_30_words_unique(self):
        seen = set()
        for p in self.preds:
            if p.get("confidence") != "high":
                continue
            words = (p.get("writeup") or "").split()
            self.assertGreaterEqual(len(words), 30, p["id"])
            self.assertNotIn(p["writeup"], seen, f"duplicate write-up on {p['id']}")
            seen.add(p["writeup"])

    def test_writeups_name_selection(self):
        for p in self.preds:
            wu = p.get("writeup") or ""
            if not wu:
                continue
            self.assertGreaterEqual(len(wu.split()), 30, p["id"])
            sel = re.sub(r"\s*\([^)]*\)", "", p["selection"]).split(" +")[0].split(" -")[0]
            self.assertIn(sel.split()[0], wu, f"{p['id']} write-up should mention {sel}")
            if not (p.get("writeup_origin") or "").startswith("prior layer"):
                self.assertIn("Selection:", wu, p["id"])

    def test_never_infer_blank_rows_are_flagged(self):
        flag_ids = {f.get("id") for f in self.flags}
        for m in self.matches:
            if m.get("line_status") == "not-originated":
                self.assertIn(m["id"], flag_ids, f"{m['id']} blank but unflagged")

    def test_originated_rows_carry_basis(self):
        for m in self.matches:
            if m.get("line_status", "").startswith("originated"):
                self.assertTrue(m.get("basis"), m["id"])

    def test_no_duplicate_fixtures(self):
        def norm(n):
            return re.sub(r"\s*\([^)]*\)", "", (n or "")).strip().lower()
        keys = [(m["sport"], m["date"], norm(m["home"]), norm(m["away"])) for m in self.matches]
        self.assertEqual(len(keys), len(set(keys)), "duplicate fixtures in matches.json")

    def test_pdc_withdrawal_flagged(self):
        text = json.dumps(self.flags)
        self.assertIn("Humphries", text)
        self.assertIn("huybrechts", text.lower())

    def test_nba_gap_documented(self):
        text = json.dumps(self.flags)
        self.assertIn("NBA", text)
        self.assertIn("inherited", text.lower())

    def test_sources_registry(self):
        self.assertGreater(len(self.sources), 5)
        for s in self.sources:
            self.assertTrue(s["url"].startswith("http"), s)

    def test_f1_inputs_are_official_table(self):
        winners = self.inputs["f1_2026_winners"]
        self.assertGreaterEqual(len(winners), 15)
        self.assertEqual(self.inputs["f1_2026_driver_points"]["Antonelli"], 340)

    def test_preds_reference_existing_matches(self):
        ids = {m["id"] for m in self.matches}
        for p in self.preds:
            self.assertIn(p["id"], ids, p["id"])


class UpdateSiteTest(unittest.TestCase):
    def test_pages_exist(self):
        expected = ["index.html", "matches.html", "picks.html", "band.html", "sources.html",
                    "methodology.html", "flagged.html"]
        for s in SPORTS:
            expected.append(s + ".html")
        for name in expected:
            self.assertTrue(os.path.exists(os.path.join(OUT, name)), name)

    def test_rendered_rows_have_source_links(self):
        for path in sorted(glob.glob(os.path.join(OUT, "*.html"))):
            with open(path) as fh:
                html = fh.read()
            for row in re.findall(r"<tr>(.*?)</tr>", html, re.S):
                if "<th>" in row or "<td>" not in row:
                    continue
                self.assertTrue("src" in row or "official" in row,
                                f"{os.path.basename(path)}: table row without source link")

    def test_flagged_page_lists_items(self):
        with open(os.path.join(OUT, "flagged.html")) as fh:
            html = fh.read()
        self.assertIn("Flagged for Review", html)
        self.assertGreater(html.count("flagitem"), 10)

    def test_index_links_categories(self):
        with open(os.path.join(OUT, "index.html")) as fh:
            html = fh.read()
        for s in ("tennis.html", "darts.html", "ice-hockey.html", "methodology.html"):
            self.assertIn(s, html, s)


if __name__ == "__main__":
    unittest.main()
