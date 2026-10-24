"""Tests for the /latest/ desk (session arena/4dd1b17c-olbg2).

They run against the committed artefacts, re-run the verifier, and prove the pipeline is
deterministic by rebuilding every file into memory and comparing bytes.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "latest"
OUT = ROOT / "latest"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class LatestScope(unittest.TestCase):
    def test_exactly_the_fifteen_sports(self):
        self.assertEqual(load("fixtures.json")["sports"], SPORTS)
        self.assertTrue({f["sport"] for f in load("fixtures.json")["fixtures"]} <= set(SPORTS))

    def test_every_sport_has_a_page_and_a_summary_row(self):
        index = (OUT / "index.html").read_text(encoding="utf-8")
        for sport in SPORTS:
            slug = sport.lower().replace(" ", "-")
            self.assertTrue((OUT / "sports" / f"{slug}.html").exists(), sport)
            self.assertIn(sport, index)

    def test_summary_opens_with_the_executive_summary(self):
        index = (OUT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Executive summary", index)
        self.assertIn('href="picks.html"', index)
        self.assertIn('href="predictions.html"', index)


class LatestProvenance(unittest.TestCase):
    def test_every_fact_carries_an_https_source_and_a_capture_time(self):
        for fixture in load("fixtures.json")["fixtures"]:
            self.assertTrue(fixture["official_url"].startswith("https://"), fixture["id"])
            self.assertTrue(fixture["facts"], fixture["id"])
            for fact in fixture["facts"]:
                self.assertTrue(fact["source_url"].startswith("https://"), fixture["id"])
                self.assertTrue(fact["captured_utc"], fixture["id"])
                self.assertTrue(fact["value"].strip(), fixture["id"])

    def test_unpriced_fixtures_state_a_reason(self):
        for fixture in load("fixtures.json")["fixtures"]:
            if fixture.get("blank_reason"):
                self.assertGreaterEqual(len(fixture["blank_reason"]), 20, fixture["id"])


class LatestPicks(unittest.TestCase):
    def test_every_pick_is_inside_the_band_on_an_unstarted_fixture(self):
        build = load("fixtures.json")["build_utc"]
        for pick in load("picks.json")["picks"]:
            self.assertTrue(pick["in_band"], pick["id"])
            self.assertGreaterEqual(pick["american"], -250, pick["id"])
            self.assertLessEqual(pick["american"], 10000, pick["id"])
            self.assertGreater(pick["start_utc"], build, pick["id"])

    def test_grade_follows_the_stated_rule(self):
        for pick in load("picks.json")["picks"]:
            expected = ("high" if pick["probability"] >= 0.70 and pick["in_band"]
                        else "medium" if pick["probability"] >= 0.60 else "low")
            self.assertEqual(pick["confidence"], expected, pick["id"])

    def test_counts_match_the_lists(self):
        picks = load("picks.json")
        self.assertEqual(picks["count"], len(picks["picks"]))
        for sport, n in picks["by_sport"].items():
            self.assertEqual(n, sum(1 for p in picks["picks"] if p["sport"] == sport))
            self.assertTrue(1 <= n <= 10, sport)

    def test_withheld_fixtures_are_named_and_published(self):
        picks = load("picks.json")
        self.assertTrue(picks["withheld_fixtures"])
        page = (OUT / "flagged.html").read_text(encoding="utf-8")
        for row in picks["withheld_fixtures"]:
            self.assertNotIn(row["fixture_id"], {p["fixture_id"] for p in picks["picks"]})
            self.assertIn("withheld", page.lower())


class LatestProse(unittest.TestCase):
    def test_every_preview_is_long_enough_and_clean(self):
        for pred in load("predictions.json")["predictions"]:
            self.assertGreaterEqual(len(pred["text"].split()), 30, pred["pick_id"])
            self.assertIsNone(BANNED.search(pred["text"]), pred["pick_id"])
            self.assertIsNone(BANNED.search(pred["headline"]), pred["pick_id"])
            self.assertGreaterEqual(len(pred["facts"]), 2, pred["pick_id"])

    def test_previews_map_one_to_one_onto_picks(self):
        pick_ids = {p["id"] for p in load("picks.json")["picks"]}
        used = [p["pick_id"] for p in load("predictions.json")["predictions"]]
        self.assertEqual(len(used), len(set(used)))
        self.assertTrue(set(used) <= pick_ids)

    def test_no_two_previews_open_the_same_way(self):
        openings = [" ".join(p["text"].split()[:6]) for p in load("predictions.json")["predictions"]]
        self.assertEqual(len(openings), len(set(openings)))

    def test_flagged_page_publishes_the_known_gaps(self):
        page = (OUT / "flagged.html").read_text(encoding="utf-8")
        for needle in ("Golf", "Snooker", "Greyhounds", "Darts", "started"):
            self.assertIn(needle.lower(), page.lower())


class LatestVerifier(unittest.TestCase):
    def test_strict_verifier_passes(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / "latest_verify.py")],
                             cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_rebuild_is_byte_identical(self):
        before = {p.relative_to(ROOT): p.read_bytes() for p in list(OUT.rglob("*")) + list(DATA.glob("*.json")) if p.is_file()}
        for script in ("latest_seed.py", "latest_model.py", "latest_predictions.py", "latest_build.py"):
            run = subprocess.run([sys.executable, str(ROOT / "scripts" / script)],
                                 cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, script + run.stdout + run.stderr)
        after = {p.relative_to(ROOT): p.read_bytes() for p in list(OUT.rglob("*")) + list(DATA.glob("*.json")) if p.is_file()}
        drifted = sorted(str(k) for k in after if before.get(k) != after[k])
        self.assertEqual(drifted, [])


if __name__ == "__main__":
    unittest.main()
