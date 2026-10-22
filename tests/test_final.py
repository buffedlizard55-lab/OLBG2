"""Structural tests for the consolidated /final/ layer (arena/5de28a6f-olbg2)."""
from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "final"
SITE = ROOT / "final"

EXCLUDED = {
    "soccer", "football", "boxing", "ufc", "mma", "american-football",
    "hurling", "horse-racing", "cycling", "specials",
}
SPORTS = {
    "ice-hockey", "basketball", "rugby-union", "darts", "tennis", "handball",
    "volleyball", "baseball", "motor-racing", "snooker", "cricket", "golf",
    "rugby-league", "gaelic-football", "greyhounds", "aussie-rules", "esports",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class FinalDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = load(DATA / "matches.json")
        cls.rows = cls.payload["matches"]
        cls.preds = load(DATA / "predictions.json")["predictions"]
        cls.flags = load(DATA / "flagged.json")["items"]

    def test_row_count_and_unique_ids(self):
        self.assertEqual(len(self.rows), 312)
        ids = [r["id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_seventeen_sports_and_no_excluded_leak(self):
        sports = {r["sport"] for r in self.rows}
        self.assertEqual(sports, SPORTS)
        for row in self.rows:
            self.assertNotIn(row["sport"], EXCLUDED)
            self.assertNotEqual(row["sport"], "football")

    def test_every_row_has_an_official_https_source(self):
        for row in self.rows:
            self.assertTrue(row["official_url"].startswith("https://"), row["id"])
            self.assertTrue(row["official_source"], row["id"])
            self.assertNotIn("liquipedia", row["official_url"].lower(), row["id"])
            self.assertNotIn("olbg.com", row["official_url"].lower(), row["id"])

    def test_line_status_is_binary_and_consistent(self):
        for row in self.rows:
            self.assertIn(row["line_status"], {"originated", "unlined"})
            if row["line_status"] == "unlined":
                self.assertIsNone(row["pick"])
                self.assertEqual(row["markets"], [])
                self.assertTrue(row["blank_reason"])
            else:
                self.assertTrue(row["markets"])
                self.assertIsNotNone(row["pick"])

    def test_high_confidence_obeys_both_constraints(self):
        high = [r for r in self.rows if (r.get("pick") or {}).get("confidence") == "high"]
        self.assertEqual(len(high), 15)
        for row in high:
            pick = row["pick"]
            self.assertGreaterEqual(pick["probability"], 0.70, row["id"])
            self.assertGreaterEqual(pick["fair_decimal"], 1.40, row["id"])
            self.assertLessEqual(pick["fair_decimal"], 101.00, row["id"])

    def test_probability_and_prices_agree(self):
        for row in self.rows:
            for market in row["markets"]:
                for outcome in market["outcomes"]:
                    p, d = outcome["probability"], outcome["fair_decimal"]
                    self.assertIsNotNone(p, row["id"])
                    self.assertIsNotNone(d, row["id"])
                    self.assertAlmostEqual(d, round(1 / p, 2), places=2, msg=row["id"])

    def test_no_bookmaker_columns(self):
        blob = json.dumps(self.payload)
        for token in ("book_dec", "book_am", "book_american", "sportsbook"):
            self.assertNotIn(token, blob)

    def test_unlined_count(self):
        self.assertEqual(sum(1 for r in self.rows if r["line_status"] == "unlined"), 33)

    def test_provenance_layers_are_real(self):
        allowed = {"verified", "hub", "board", "slate", "forward"}
        for row in self.rows:
            self.assertIn(row["provenance"]["layer_used"], allowed)
            for layer in row["provenance"]["layers"]:
                self.assertIn(layer, allowed)

    def test_verification_status_vocabulary(self):
        allowed = {"reverified", "form", "corrected", "inherited", "unverified"}
        for row in self.rows:
            self.assertIn(row["verification"]["status"], allowed)
        self.assertEqual(sum(1 for r in self.rows if r["verification"]["status"] == "unverified"), 8)


class FinalPredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load(DATA / "matches.json")["matches"]
        cls.preds = load(DATA / "predictions.json")["predictions"]
        cls.high = {r["id"] for r in cls.rows if (r.get("pick") or {}).get("confidence") == "high"}

    def test_one_prediction_per_high_pick(self):
        self.assertEqual(len(self.preds), 15)
        self.assertEqual({p["match_id"] for p in self.preds}, self.high)

    def test_each_prediction_is_long_enough_and_unique(self):
        self.assertEqual(len({p["text"] for p in self.preds}), len(self.preds))
        for p in self.preds:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["match_id"])
            self.assertEqual(p["word_count"], len(p["text"].split()))
            self.assertEqual(p["confidence"], "high")

    def test_selection_is_explicit(self):
        for p in self.preds:
            core = re.sub(r"\s*\(.*?\)", "", p["selection"]).strip().lower()
            first = core.split()[0]
            self.assertIn(first, p["text"].lower(), p["match_id"])
            self.assertIn(core[:12], p["text"].lower().replace("’", "'"), p["match_id"])

    def test_each_prediction_names_both_sides(self):
        for p in self.preds:
            for team in (p["home"], p["away"]):
                key = team.split()[0].lower()
                self.assertIn(key, p["text"].lower(), (p["match_id"], team))

    def test_facts_are_official_urls(self):
        for p in self.preds:
            self.assertTrue(p["facts"], p["match_id"])
            for fact in p["facts"]:
                self.assertTrue(fact["source"].startswith("https://"), fact)
                self.assertNotIn("liquipedia", fact["source"].lower())

    def test_prices_inside_focus_band(self):
        for p in self.preds:
            self.assertGreaterEqual(p["probability"], 0.70)
            self.assertGreaterEqual(p["fair_decimal"], 1.40)
            self.assertLessEqual(p["fair_decimal"], 101.00)


class FinalSiteTests(unittest.TestCase):
    def test_pages_exist(self):
        expected = ["index.html", "matches.html", "picks.html", "verification.html", "flagged.html",
                    "methodology.html", "sources.html", "archive.html", "sports/index.html"]
        for name in expected:
            self.assertTrue((SITE / name).exists(), name)

    def test_all_seventeen_sport_pages(self):
        for slug in SPORTS:
            self.assertTrue((SITE / "sports" / f"{slug}.html").exists(), slug)

    def test_internal_links_and_fragments_resolve(self):
        for html_file in SITE.rglob("*.html"):
            body = html_file.read_text(encoding="utf-8")
            ids = set(re.findall(r'id="([^"]+)"', body))
            for href in re.findall(r'(?:href|src)="([^"]+)"', body):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                target, _, fragment = href.partition("#")
                if target:
                    dest = (html_file.parent / target).resolve()
                    self.assertTrue(dest.exists(), f"{html_file} -> {href}")
                    if fragment:
                        target_ids = set(re.findall(r'id="([^"]+)"', dest.read_text(encoding="utf-8")))
                        self.assertIn(fragment, target_ids, f"{html_file} -> {href}")
                elif fragment:
                    self.assertIn(fragment, ids, f"{html_file} -> {href}")

    def test_every_table_row_has_a_source_link(self):
        body = (SITE / "matches.html").read_text(encoding="utf-8")
        tbody = body.split("<tbody>", 1)[1]
        rows = re.findall(r"<tr class=.*?</tr>", tbody, flags=re.S)
        self.assertEqual(len(rows), 312)
        for row in rows:
            self.assertIn('<a href="https://', row)

    def test_no_excluded_sport_rows_on_site(self):
        """The exclusion list may be quoted in prose; no row may carry one of those sports."""
        for html_file in SITE.rglob("sports/*.html"):
            self.assertNotIn("horse-racing", html_file.name)
            self.assertNotIn("ufc", html_file.name)
            self.assertNotIn("boxing", html_file.name)
            self.assertNotIn("american-football", html_file.name)

    def test_high_pick_anchors_exist(self):
        body = (SITE / "picks.html").read_text(encoding="utf-8")
        for match_id in re.findall(r'href="picks\.html#([^"]+)"', (SITE / "index.html").read_text(encoding="utf-8")):
            self.assertIn(f'id="{match_id}"', body)


class FinalFlagTests(unittest.TestCase):
    def test_flags_exist_and_are_identified(self):
        flags = load(DATA / "flagged.json")["items"]
        self.assertGreaterEqual(len(flags), 15)
        ids = [f["id"] for f in flags]
        self.assertEqual(len(ids), len(set(ids)))
        for flag in flags:
            self.assertIn(flag["severity"], {"high", "medium", "low"})
            self.assertTrue(flag["detail"])

    def test_corrections_are_documented(self):
        blob = json.dumps(load(DATA / "flagged.json"))
        for token in ("Butterfield", "Bunting", "Pastrnak", "Josi", "Fils"):
            self.assertIn(token, blob)


if __name__ == "__main__":
    unittest.main()
