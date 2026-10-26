"""Tests for the 26 October 2026 fifteen-sport desk (session arena/9cf54b86-olbg2)."""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "slate26"
DATA = ROOT / "data" / "slate26"

sys.path.insert(0, str(ROOT / "scripts"))


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class DataTests(unittest.TestCase):
    def test_every_fixture_has_a_source_link_and_a_pick(self):
        fx = load("fixtures.json")
        picks = load("picks.json")
        self.assertEqual(fx["count"], len(fx["fixtures"]))
        self.assertEqual({f["id"] for f in fx["fixtures"]}, {p["fixture"] for p in picks["picks"]})
        for f in fx["fixtures"]:
            self.assertTrue(f["hub_url"].startswith("https://www.olbg.com/"), f["id"])
            self.assertTrue(f["olbg_event_id"], f["id"])

    def test_high_picks_are_inside_the_band_with_a_usable_sample(self):
        picks = load("picks.json")
        for p in picks["picks"]:
            self.assertIn(p["confidence"], {"high", "medium", "low"})
            if p["confidence"] == "high":
                self.assertTrue(p["in_band"], p["fixture"])
                self.assertGreaterEqual(int(p["tips"].split("/")[1]), 4, p["fixture"])
            if p["selection"].strip().lower() in {"tie", "draw"}:
                self.assertNotEqual(p["confidence"], "high", p["fixture"])
        self.assertEqual(picks["high"], sum(1 for p in picks["picks"] if p["confidence"] == "high"))

    def test_every_price_was_originated_on_a_stated_basis(self):
        lines = load("lines.json")
        self.assertEqual(lines["count"], len(lines["lines"]))
        for l in lines["lines"]:
            self.assertIn(l["basis"], {"official-input", "olbg-tip-share", "olbg-tip-share-thin"})
            self.assertIsNotNone(l["probability"])
            self.assertLess(abs(int(l["price"])), 1400, l["fixture"])
        official = [l for l in lines["lines"] if l["basis"] == "official-input"]
        self.assertEqual(len(official), 1)
        self.assertEqual(official[0]["fixture"], "S26-008")

    def test_no_match_is_invented_for_a_sport_olbg_did_not_list(self):
        hubs = load("hubs.json")
        fx = load("fixtures.json")
        empty = {h["sport"] for h in hubs["hubs"] if h["state"] == "none"}
        listed = {f["sport"] for f in fx["fixtures"]}
        self.assertTrue(empty == {"golf", "snooker"}, empty)
        self.assertFalse(empty & listed)


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.preds = load("predictions.json")
        self.fx = {f["id"]: f for f in load("fixtures.json")["fixtures"]}
        self.picks = {p["fixture"]: p for p in load("picks.json")["picks"]}

    def test_every_preview_is_thirty_words_with_a_unique_opening(self):
        openings = set()
        for r in self.preds["predictions"]:
            words = len(r["text"].split())
            self.assertGreaterEqual(words, 30, r["fixture"])
            self.assertEqual(words, r["words"])
            opening = " ".join(r["text"].split()[:5]).lower()
            self.assertNotIn(opening, openings, r["fixture"])
            openings.add(opening)

    def test_reader_facing_copy_avoids_the_internal_vocabulary(self):
        for r in self.preds["predictions"]:
            for word in ("model", "verified"):
                self.assertIsNone(re.search(rf"\b{word}", r["text"], re.I), (r["fixture"], word))

    def test_tiers_match_the_evidence(self):
        for r in self.preds["predictions"]:
            if r["tier"] == "full":
                self.assertTrue(r["facts"], r["fixture"])
                for fact in r["facts"]:
                    self.assertTrue(fact["url"].startswith("http"))
                    page = (OUT / "predictions.html").read_text(encoding="utf-8")
                    self.assertIn(html.escape(fact["url"]), page)
            else:
                self.assertEqual(r["tier"], "market")
                self.assertEqual(r["facts"], [], r["fixture"])

    def test_every_high_pick_has_a_preview_anchor(self):
        page = (OUT / "predictions.html").read_text(encoding="utf-8")
        highs = [p for p in self.picks.values() if p["confidence"] == "high"]
        written = {r["fixture"] for r in self.preds["predictions"]}
        for p in highs:
            self.assertIn(p["fixture"], written, p["fixture"])
        for fid in written:
            self.assertIn(f'id="{fid}"', page, fid)


class PageTests(unittest.TestCase):
    PAGES = ["index.html", "picks.html", "predictions.html", "matches.html", "lines.html", "band.html",
             "sources.html", "flagged.html", "outrights.html", "methodology.html", "sports/index.html"]

    def test_pages_render_deterministically(self):
        import slate26_build as B
        before = {name: (OUT / name).read_text(encoding="utf-8") for name in self.PAGES}
        B.build()
        for name in self.PAGES:
            self.assertEqual(before[name], (OUT / name).read_text(encoding="utf-8"), name)

    def test_every_sport_has_a_page(self):
        for slug in ("ice-hockey", "basketball", "tennis", "cricket", "handball", "volleyball",
                     "gaelic", "baseball", "greyhounds", "motor-racing", "golf", "snooker", "darts",
                     "rugby-union", "rugby-league"):
            self.assertTrue((OUT / "sports" / f"{slug}.html").is_file(), slug)

    def test_unlisted_sports_say_so_instead_of_padding(self):
        for slug in ("golf", "snooker"):
            page = (OUT / "sports" / f"{slug}.html").read_text(encoding="utf-8")
            self.assertIn("No pick for", page)
            self.assertNotIn("<h2>Picks, highest confidence first</h2>", page)

    def test_flagged_items_are_all_published_with_a_source(self):
        page = (OUT / "flagged.html").read_text(encoding="utf-8")
        for item in load("flagged.json")["items"]:
            self.assertIn(item["id"], page)
            self.assertTrue(item["source"].startswith("http"))

    def test_root_front_door_quotes_the_desk_and_keeps_the_older_one_reachable(self):
        root = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f">{load('fixtures.json')['count']}</div><div class=\"l\">upcoming matches", root)
        self.assertIn('href="slate26/picks.html"', root)
        self.assertIn('href="slate26/flagged.html"', root)
        self.assertIn('href="compass/index.html"', root)

    def test_verify_script_passes(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / "slate26_verify.py")],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("slate26_verify: ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
