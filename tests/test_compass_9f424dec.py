"""Tests for the /compass/ desk (session arena/9f424dec-olbg2, 2026-10-24 22:45Z capture).

Covers: the OLBG hub capture, the fixture records with their official sources, the
originated lines and the -250..+10000 band, the confidence-graded picks, the written
predictions (word counts, unique openings, no banned vocabulary), the Flagged for
Review page, and the root front-door takeover.
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import compass_build as B  # noqa: E402

DATA = ROOT / "data" / "compass"
OUT = ROOT / "compass"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class CaptureTests(unittest.TestCase):
    def test_all_fifteen_sports_have_hubs(self):
        capture = load("olbg.json")["capture"]
        for s in SPORTS:
            self.assertIn(s, capture["hubs"])

    def test_listings_carry_event_ids_and_tips(self):
        for r in load("olbg.json")["listings"]:
            self.assertTrue(r["event_id"])
            self.assertTrue(r["event"])
            self.assertTrue(r["url"].startswith("https://www.olbg.com/betting-tips/event/"))

    def test_empty_sports_are_recorded(self):
        status = load("olbg.json")["capture"]["sport_status"]
        for s in ("Golf", "Snooker", "Motor Racing"):
            self.assertIn("No tips found", status[s])


class FixtureTests(unittest.TestCase):
    def test_every_olbg_listing_maps_to_a_fixture(self):
        fixtures = {f["olbg_listing"]["event_id"]: f for f in load("fixtures.json")["fixtures"]
                    if f.get("olbg_listing")}
        for r in load("olbg.json")["listings"]:
            self.assertIn(r["event_id"], fixtures, r["event"])

    def test_official_sources_are_http(self):
        for f in load("fixtures.json")["fixtures"]:
            if f["official_url"]:
                self.assertTrue(f["official_url"].startswith("http"), f["id"])
            for fact in f["facts"]:
                self.assertTrue(
                    fact["source_url"].startswith(("http", "data/")),
                    f"{f['id']}: {fact['claim']}")

    def test_olbg_data_error_is_flagged(self):
        flags = load("flagged.json")["items"]
        self.assertTrue(any("Maigh Cuilinn" in f["text"] and "Moycullen" in f["text"]
                            for f in flags), "Galway SFC final data error not flagged")

    def test_official_kickoffs_used_not_olbg_display(self):
        fx = {f["id"]: f for f in load("fixtures.json")["fixtures"]}
        self.assertEqual(fx["rug-usa-ausa"]["start_utc"], "2026-10-24T22:00:00Z")
        self.assertEqual(fx["mlb-g2"]["start_utc"], "2026-10-25T00:00:00Z")
        self.assertEqual(fx["nhl-det-cgy"]["start_utc"], "2026-10-25T02:00:00Z")


class LineTests(unittest.TestCase):
    def test_band_flag_matches_american(self):
        for l in load("lines.json")["lines"]:
            self.assertEqual(l["in_band"], -250 <= l["american"] <= 10000, l["selection"])

    def test_high_lines_are_in_band_and_numeric(self):
        for l in load("lines.json")["lines"]:
            if l["confidence"] == "high":
                self.assertTrue(l["in_band"], l["selection"])
                self.assertIn(l["basis"], ("poisson", "poisson_runs", "normal_margin",
                                           "binomial_legs"), l["selection"])

    def test_no_bookmaker_price_is_used(self):
        text = (DATA / "lines.json").read_text()
        self.assertNotIn("draftkings", text.lower())
        self.assertNotIn("bookmaker price", text.lower())


class PickTests(unittest.TestCase):
    def test_five_to_ten_picks_per_active_sport(self):
        by = load("picks.json")["by_sport"]
        fx_by = {}
        for f in load("fixtures.json")["fixtures"]:
            fx_by[f["sport"]] = fx_by.get(f["sport"], 0) + 1
        active = [s for s in SPORTS if s not in ("Golf", "Snooker", "Motor Racing")]
        for s in active:
            floor = min(5, fx_by.get(s, 0))
            self.assertGreaterEqual(by.get(s, 0), floor, s)
            self.assertLessEqual(by.get(s, 0), 10, s)

    def test_high_picks_count(self):
        picks = load("picks.json")["picks"]
        self.assertEqual(sum(1 for p in picks if p["confidence"] == "high"),
                         load("picks.json")["high"])

    def test_every_pick_references_an_originated_line(self):
        lines = {(l["fixture_id"], l["selection"]) for l in load("lines.json")["lines"]}
        for p in load("picks.json")["picks"]:
            self.assertIn((p["fixture_id"], p["selection"]), lines, p["id"])


class PredictionTests(unittest.TestCase):
    def test_high_predictions_are_long_and_unique(self):
        preds = load("predictions.json")["predictions"]
        highs = [p for p in preds if p["confidence"] == "high"]
        self.assertGreaterEqual(len(highs), 5)
        for p in highs:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["id"])
        openings = [" ".join(p["text"].split()[:4]).lower() for p in preds]
        self.assertEqual(len(openings), len(set(openings)), "repeated openings")

    def test_no_banned_vocabulary(self):
        banned = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
        for p in load("predictions.json")["predictions"]:
            self.assertIsNone(banned.search(p["text"] + " " + p["headline"]), p["id"])
        for p in load("picks.json")["picks"]:
            self.assertIsNone(banned.search(p.get("assumption", "")), p["id"])

    def test_high_picks_name_their_selection(self):
        for p in load("predictions.json")["predictions"]:
            if p["confidence"] == "high":
                self.assertIn(p["selection"], p["text"], p["id"])


class PageTests(unittest.TestCase):
    def test_pages_render_deterministically(self):
        for name, fn in [("index.html", B.build_index),
                         ("picks.html", B.build_picks),
                         ("predictions.html", B.build_predictions),
                         ("flagged.html", B.build_flagged)]:
            self.assertEqual((OUT / name).read_text(encoding="utf-8"), fn(), name)

    def test_flagged_page_lists_all_items(self):
        page = (OUT / "flagged.html").read_text(encoding="utf-8")
        for f in load("flagged.json")["items"]:
            self.assertIn(f["id"], page)

    def test_front_door_points_at_compass(self):
        root = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="compass/picks.html"', root)
        self.assertIn('href="compass/predictions.html"', root)
        self.assertIn("22:45Z", root)
        # prediction anchors resolve on the compass predictions page
        pred_page = (OUT / "predictions.html").read_text(encoding="utf-8")
        for anchor in re.findall(r'href="compass/predictions\.html#([^"]+)"', root):
            self.assertIn(f'id="{anchor}"', pred_page, anchor)

    def test_sport_pages_link_back(self):
        for s in SPORTS:
            page = (OUT / "sports" / (B.SLUG[s] + ".html")).read_text(encoding="utf-8")
            self.assertIn('href="../picks.html"', page)

    def test_verify_script_passes(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / "compass_verify.py")],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
