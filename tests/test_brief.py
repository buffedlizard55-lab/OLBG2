"""Tests for the /brief/ 15-sport desk (session 7a073c9a).

They cover the published data, the published pages and the desk's own audit script.
They deliberately do not attempt to re-fetch external sources: the repository's
convention is that a committed capture is the evidence of record.
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "brief"
BRIEF = ROOT / "brief"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
          "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
          "Handball", "Ice Hockey", "Basketball", "Rugby League"]


def load(name):
    return json.loads((DATA / name).read_text())


class BriefDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")
        cls.preds = load("predictions.json")
        cls.sources = load("sources.json")["sources"]
        cls.flags = load("flags.json")["flags"]

    def test_scope_is_exactly_the_fifteen_sports(self):
        self.assertEqual({f["sport"] for f in self.matches["fixtures"]}, set(SPORTS))

    def test_every_fixture_has_an_https_source_on_the_ledger(self):
        keys = {s["key"] for s in self.sources}
        for f in self.matches["fixtures"]:
            self.assertTrue(f["source_url"].startswith("https://"), f["id"])
            self.assertIn(f["source_key"], keys, f["id"])

    def test_every_priced_fixture_records_its_input(self):
        for f in self.matches["fixtures"]:
            if f["markets"]:
                self.assertTrue(f["input_note"].strip(), f["id"])

    def test_unpriced_fixtures_say_why(self):
        for f in self.matches["fixtures"]:
            if not f["markets"]:
                self.assertTrue(f["flags"], f["id"])

    def test_probabilities_are_clamped_and_two_way_markets_sum_to_one(self):
        for f in self.matches["fixtures"]:
            groups = {}
            for m in f["markets"]:
                self.assertGreaterEqual(m["prob"], 0.05)
                self.assertLessEqual(m["prob"], 0.95)
                groups.setdefault(m["market"], []).append(m)
            for name, g in groups.items():
                if len(g) == 2 and "Money line" in name:
                    self.assertAlmostEqual(sum(x["prob"] for x in g), 1.0, places=3)

    def test_in_band_flag_matches_the_price(self):
        for f in self.matches["fixtures"]:
            for m in f["markets"]:
                a = int(m["american"].replace("+", ""))
                self.assertEqual(m["in_band"], -250 <= a <= 10000, (f["id"], m["market"]))

    def test_no_pick_when_the_favourite_is_shorter_than_the_band(self):
        for f in self.matches["fixtures"]:
            if not f["markets"]:
                continue
            results = [m for m in f["markets"] if m["market"].startswith(
                ("Money line", "Match winner", "Tournament winner", "Race winner"))]
            if not results:
                continue
            strongest = max(results, key=lambda m: m["prob"])
            if strongest["prob"] > 0.7143:
                self.assertIsNone(f.get("pick"), f["id"])

    def test_started_fixtures_are_never_picks(self):
        for f in self.matches["fixtures"]:
            if not f["eligible"]:
                self.assertIsNone(f.get("pick"), f["id"])

    def test_predictions_meet_the_brief(self):
        seen_open = set()
        for p in self.preds["predictions"]:
            self.assertGreaterEqual(p["words"], 30, p["id"])
            for bad in ("model", "verified"):
                self.assertNotIn(bad, p["text"].lower(), p["id"])
            opening = " ".join(p["text"].split()[:4]).lower()
            self.assertNotIn(opening, seen_open, p["id"])
            seen_open.add(opening)
            self.assertIn(p["tier"], "ABCD")

    def test_prediction_selection_exists_in_the_fixture_markets(self):
        fixtures = {f["id"]: f for f in self.matches["fixtures"]}
        for p in self.preds["predictions"]:
            f = fixtures[p["fixture_id"]]
            pairs = {(m["market"], m["selection"]) for m in f["markets"]}
            self.assertIn((p["market"], p["selection"]), pairs, p["id"])

    def test_no_prediction_for_an_unpriced_or_started_fixture(self):
        fixtures = {f["id"]: f for f in self.matches["fixtures"]}
        for p in self.preds["predictions"]:
            f = fixtures[p["fixture_id"]]
            self.assertTrue(f["markets"], p["id"])
            self.assertTrue(f["eligible"], p["id"])

    def test_review_queue_carries_the_blocking_items(self):
        ids = {f["id"] for f in self.flags}
        for required in ("BR-01", "BR-02", "BR-03", "BR-04", "BR-08", "BR-09", "BR-10"):
            self.assertIn(required, ids)


class BriefPageTest(unittest.TestCase):
    def test_all_pages_exist(self):
        for name in ("index.html", "matches.html", "picks.html", "predictions.html",
                     "sources.html", "flagged.html", "methodology.html", "olbg.html",
                     "review.html", "sports/index.html"):
            self.assertTrue((BRIEF / name).exists(), name)
        for s in SPORTS:
            self.assertTrue((BRIEF / "sports" / (s.lower().replace(" ", "-") + ".html")).exists(), s)

    def test_no_broken_internal_links(self):
        for page in BRIEF.rglob("*.html"):
            text = page.read_text()
            for href in re.findall(r'href="([^"#]+)(?:#[^"]*)?"', text):
                if href.startswith(("http", "mailto")):
                    continue
                self.assertTrue((page.parent / href.split("#")[0]).resolve().exists(),
                                f"{page.relative_to(BRIEF)} -> {href}")

    def test_executive_summary_names_the_tier_rule(self):
        text = (BRIEF / "index.html").read_text()
        self.assertIn("Tier A", text)
        self.assertIn("−250", text)
        self.assertIn("+10000", text)

    def test_flagged_page_publishes_every_flag(self):
        text = (BRIEF / "flagged.html").read_text()
        for f in json.loads((DATA / "flags.json").read_text())["flags"]:
            self.assertIn(f["id"], text)

    def test_root_navigation_links_to_the_brief(self):
        root = (ROOT / "index.html").read_text()
        self.assertIn('href="brief/index.html"', root)


class BriefAuditTest(unittest.TestCase):
    def test_the_desks_own_audit_passes(self):
        spec = importlib.util.spec_from_file_location("brief_verify", ROOT / "scripts" / "brief_verify.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()  # raises SystemExit(1) on failure
        self.assertEqual(mod.failures, [])


if __name__ == "__main__":
    unittest.main()
