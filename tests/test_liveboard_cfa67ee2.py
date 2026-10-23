#!/usr/bin/env python3
"""Tests for the /liveboard/ layer (session arena/cfa67ee2-olbg2).

The point of these tests is not to check that HTML exists. It is to check that the desk's own
rules still hold: that every row has a source, that the band and confidence gates are applied
as documented, that the build is reproducible, that no internal link is broken, and that no
prediction contains a claim without an official page behind it.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "liveboard"
OUT = ROOT / "liveboard"

# Words the brief bans from the published predictions.
BANNED = ("model", "verified")


def load(name):
    return json.loads((DATA / name).read_text())


class TestOlbgCapture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.olbg = load("olbg.json")

    def test_every_hub_declares_its_source(self):
        for hub in self.olbg["hubs"]:
            self.assertTrue(hub["hub_url"].startswith("https://www.olbg.com/betting-tips/"))
            self.assertIn("id", hub)

    def test_every_event_has_a_stable_source_url(self):
        for hub in self.olbg["hubs"]:
            for ev in hub.get("events", []):
                self.assertIn("u", ev, ev)
                self.assertTrue(ev["u"].startswith("https://www.olbg.com/betting-tips/"), ev["u"])
                self.assertIn(f"event_id={ev['id']}", ev["u"], ev["u"])
                for key in ("n", "t", "s", "w", "tw", "p"):
                    self.assertIn(key, ev, ev)

    def test_tip_counts_are_consistent(self):
        for hub in self.olbg["hubs"]:
            for ev in hub.get("events", []):
                self.assertGreaterEqual(ev["w"], 0)
                self.assertGreaterEqual(ev["tw"], ev["w"], ev)
                self.assertTrue(0 <= ev["p"] <= 100, ev)

    def test_sport_scope_is_exactly_the_fifteen_in_the_brief(self):
        expected = {"Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
                    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
                    "Ice Hockey", "Basketball", "Rugby League"}
        self.assertEqual({h["sport"] for h in self.olbg["hubs"]}, expected)

    def test_excluded_sports_absent(self):
        names = {h["sport"].lower() for h in self.olbg["hubs"]}
        for banned in ("football", "soccer", "boxing", "mma", "american football", "hurling",
                       "horse racing", "cycling", "esports", "aussie rules"):
            self.assertNotIn(banned, names)

    def test_golf_really_is_empty_not_missing(self):
        golf = next(h for h in self.olbg["hubs"] if h["sport"] == "Golf")
        self.assertEqual(golf["events"], [])
        self.assertIn("NO TIPS", golf["hub_status"])


class TestLineOrigination(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = load("lines.json")
        cls.rows = cls.lines["rows"]

    def test_every_price_has_a_source_and_a_basis(self):
        for r in self.rows:
            self.assertTrue(r["source_url"].startswith("https://"), r)
            self.assertTrue(r["basis"], r)

    def test_source_class_is_one_of_two_values(self):
        for r in self.rows:
            self.assertIn(r["source_class"], ("official-model", "community-implied"))

    def test_probability_bounds(self):
        for r in self.rows:
            self.assertGreater(r["probability"], 0)
            self.assertLess(r["probability"], 1)

    def test_high_label_requires_seventy_percent(self):
        for r in self.rows:
            if r["confidence"] == "high":
                self.assertGreaterEqual(r["probability"], 0.70, r)

    def test_tip_share_rows_need_a_real_sample_to_be_high(self):
        for r in self.rows:
            if r["source_class"] == "community-implied" and r["confidence"] == "high":
                self.assertIsNotNone(r["tip_sample"])
                self.assertGreaterEqual(r["tip_sample"], self.lines["method"]["min_tips_for_high"], r)

    def test_band_flag_recomputes_from_the_offered_price(self):
        for r in self.rows:
            am = int(str(r["offered_american"]).replace("+", ""))
            expected = -250 <= am <= 10000
            self.assertEqual(r["in_band"], expected, r)

    def test_high_and_in_band_is_the_conjunction(self):
        for r in self.rows:
            self.assertEqual(r["high_and_in_band"], r["confidence"] == "high" and r["in_band"], r)

    def test_offered_price_is_longer_than_fair_price(self):
        for r in self.rows:
            self.assertGreater(r["offered_decimal"], r["fair_decimal"], r)

    def test_one_of_one_tips_never_becomes_certainty(self):
        singles = [r for r in self.rows if r["tip_sample"] == 1]
        self.assertTrue(singles, "expected at least one 1-tip row in the capture")
        for r in singles:
            self.assertLess(r["probability"], 0.70, r)

    def test_unlined_rows_name_a_reason(self):
        for u in self.lines["unlined"]:
            self.assertTrue(u["reason"])
            self.assertTrue(u["source_url"].startswith("https://"))

    def test_coverage_counts_match_the_rows(self):
        for sport, cov in self.lines["coverage"].items():
            priced = [r for r in self.rows if r["sport"] == sport]
            self.assertEqual(cov["markets_priced"], len(priced), sport)
            official = [r for r in priced if r["source_class"] == "official-model"]
            self.assertEqual(cov["rows_official_model"], len(official), sport)


class TestPredictions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preds = load("predictions.json")["predictions"]

    def test_at_least_thirty_words(self):
        for p in self.preds:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["id"])

    def test_banned_vocabulary_absent(self):
        for p in self.preds:
            low = p["text"].lower()
            for word in BANNED:
                self.assertNotIn(word, re.findall(r"[a-z]+", low), f"{p['id']} contains {word}")

    def test_every_prediction_carries_official_facts(self):
        for p in self.preds:
            self.assertTrue(p.get("facts"), p["id"])
            for f in p["facts"]:
                self.assertTrue(f["source_url"].startswith("https://"), f)

    def test_selection_is_stated_plainly(self):
        for p in self.preds:
            self.assertTrue(any(v in p["selection"].lower() for v in ("to win", "over", "under", "+1.5", "-1.5")), p["id"])

    def test_openings_are_not_repetitive(self):
        firsts = [p["text"].split()[0].lower() for p in self.preds]
        self.assertEqual(len(firsts), len(set(firsts)), firsts)

    def test_no_prediction_claims_an_injury(self):
        for p in self.preds:
            low = p["text"].lower()
            for word in ("injur", "ruled out", "doubtful", "suspension"):
                self.assertNotIn(word, low, p["id"])

    def test_event_ids_exist_in_capture(self):
        ids = {ev["id"] for h in load("olbg.json")["hubs"] for ev in h.get("events", [])}
        for p in self.preds:
            self.assertIn(p["event_id"], ids, p["id"])


class TestFlagsAndSources(unittest.TestCase):
    def test_every_flag_has_a_source_and_an_action(self):
        for f in load("flagged.json")["flags"]:
            self.assertTrue(f["sources"], f["id"])
            self.assertTrue(f["action"], f["id"])
            self.assertTrue(f["detail"], f["id"])

    def test_flag_ids_unique(self):
        ids = [f["id"] for f in load("flagged.json")["flags"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_blocked_sources_are_recorded(self):
        blocked = load("sources.json")["blocked"]
        self.assertGreaterEqual(len(blocked), 5)
        for b in blocked:
            self.assertTrue(b["result"])

    def test_official_inputs_carry_urls(self):
        for b in load("inputs.json")["blocks"]:
            self.assertTrue(b["source_url"].startswith("https://"), b["id"])


class TestBuild(unittest.TestCase):
    def test_expected_pages_exist(self):
        for name in ("index.html", "picks.html", "matches.html", "lines.html", "predictions.html",
                     "coverage.html", "flagged.html", "sources.html", "methodology.html",
                     "assets/style.css"):
            self.assertTrue((OUT / name).exists(), name)
        sports = [p.stem for p in (OUT / "sports").glob("*.html")]
        self.assertEqual(len(sports), 15)

    def test_no_internal_link_is_broken(self):
        manifest = load("link-manifest.json")
        self.assertTrue(manifest)
        broken = []
        for src, targets in manifest.items():
            for t in targets:
                if not (ROOT / t).exists():
                    broken.append((src, t))
        self.assertEqual(broken, [])

    def test_every_page_carries_the_navigation(self):
        for p in OUT.rglob("*.html"):
            txt = p.read_text()
            for label in ("Dashboard", "Top picks", "Flagged for review"):
                self.assertIn(label, txt, p.name)

    def test_rebuild_is_byte_identical(self):
        before = {p: p.read_text() for p in list(OUT.rglob("*.html")) + [DATA / "lines.json"]}
        subprocess.run([sys.executable, "scripts/liveboard_model.py"], cwd=ROOT, check=True,
                       capture_output=True)
        subprocess.run([sys.executable, "scripts/liveboard_build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        after = {p: p.read_text() for p in list(OUT.rglob("*.html")) + [DATA / "lines.json"]}
        self.assertEqual(set(before), set(after))
        for p in before:
            self.assertEqual(before[p], after[p], f"{p} changed on rebuild")

    def test_dashboard_numbers_match_the_data(self):
        lines = load("lines.json")
        txt = (OUT / "index.html").read_text()
        high = len([r for r in lines["rows"] if r["high_and_in_band"] and r["is_match"]])
        self.assertIn(f"<b>{high}</b><span>High confidence, in band</span>", txt)
        self.assertIn(f"<b>{len(lines['rows'])}</b><span>Markets priced</span>", txt)

    def test_flagged_page_lists_every_flag(self):
        txt = (OUT / "flagged.html").read_text()
        for f in load("flagged.json")["flags"]:
            self.assertIn(f["id"], txt)

    def test_predictions_page_links_each_fact_source(self):
        txt = (OUT / "predictions.html").read_text()
        for p in load("predictions.json")["predictions"]:
            for f in p["facts"]:
                self.assertIn(html.escape(f["source_url"], quote=True), txt, p["id"])

    def test_no_page_quotes_a_bookmaker_price(self):
        """We never assert OLBG's price, because OLBG publishes none to a logged-out visitor."""
        for p in OUT.rglob("*.html"):
            txt = p.read_text()
            self.assertNotIn("OLBG odds", txt)
            self.assertNotIn("bookmaker odds", txt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
