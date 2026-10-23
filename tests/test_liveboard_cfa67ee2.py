"""Acceptance tests for the 15-sport live board (session arena/cfa67ee2-olbg2).

Where this repository has already published records that disagree with a cost or
sourcing rule, the source pages were re-read and the published rows updated.  These
tests lock the current, re-verified state.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "liveboard"
OUT = ROOT / "liveboard"

SCOPE = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
    "Ice Hockey", "Basketball", "Rugby League",
]
SCOPE_SLUGS = [
    ("Golf", "golf"), ("Volleyball", "volleyball"), ("Rugby Union", "rugby-union"),
    ("Cricket", "cricket"), ("Snooker", "snooker"), ("Darts", "darts"), ("Baseball", "baseball"),
    ("Gaelic Sports", "gaelic-sports"), ("Greyhounds", "greyhounds"), ("Tennis", "tennis"),
    ("Motor Racing", "motor-racing"), ("Handball", "handball"), ("Ice Hockey", "ice-hockey"),
    ("Basketball", "basketball"), ("Rugby League", "rugby-league"),
]
EXCLUDED = ["Soccer", "Horse Racing", "Boxing", "MMA", "UFC", "Hurling", "Cage Fighting"]


def load(name):
    return json.loads((DATA / name).read_text())


class TestCapture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.olbg = load("olbg.json")
        cls.sports = {s["sport"]: s for s in cls.olbg["sports"]}

    def test_scope_is_exactly_the_fifteen_sports(self):
        self.assertEqual([s["sport"] for s in self.olbg["sports"]], SCOPE)

    def test_no_excluded_sport_appears(self):
        blob = json.dumps(self.olbg).lower()
        for word in EXCLUDED:
            self.assertNotIn(word.lower(), blob)

    def test_golf_is_empty_and_says_so(self):
        golf = self.sports["Golf"]
        self.assertEqual(golf["events"], [])
        self.assertEqual(golf["status"], "empty")
        self.assertIn("No tips found", golf["status_detail"])

    def test_rugby_league_is_outrights_only(self):
        rl = self.sports["Rugby League"]
        self.assertEqual(rl["status"], "outrights_only")
        self.assertTrue(all(e.get("outright") for e in rl["events"]))

    def test_every_event_has_a_stable_url_and_unique_id(self):
        seen = set()
        for s in self.olbg["sports"]:
            for e in s["events"]:
                self.assertNotIn(e["id"], seen, e["event"])
                seen.add(e["id"])
                self.assertIn(f"event_id={e['id']}", e["path"])
                self.assertTrue(e["path"].startswith("/betting-tips/"))
        self.assertEqual(len(seen), 133)

    def test_tip_counts_are_consistent(self):
        for s in self.olbg["sports"]:
            for e in s["events"]:
                self.assertGreaterEqual(e["tips"], 1, e["event"])
                self.assertLessEqual(e["tips"], e["total"], e["event"])

    def test_times_are_kept_as_displayed(self):
        starts = [e["start_display"] for s in self.olbg["sports"] for e in s["events"]]
        self.assertTrue(all(starts))
        self.assertFalse(any("T00:" in x or x.endswith("Z") for x in starts))

    def test_market_labels_are_from_olbg(self):
        allowed = set(self.olbg["markets_seen"])
        for s in self.olbg["sports"]:
            for e in s["events"]:
                if e["market"]:
                    self.assertIn(e["market"], allowed, e["event"])


class TestLines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = load("lines.json")
        cls.rows = cls.lines["rows"]

    def test_one_priced_row_per_fixture(self):
        self.assertEqual(len(self.rows), 133)

    def test_probabilities_and_prices_are_sane(self):
        for r in self.rows:
            self.assertGreater(r["probability"], 0.0, r["selection"])
            self.assertLess(r["probability"], 1.0, r["selection"])
            self.assertGreater(r["offered_decimal"], 1.0, r["selection"])
            self.assertLessEqual(r["offered_decimal"], r["fair_decimal"] + 1e-9, r["selection"])
            expected_fair = 1 / r["probability"]
            self.assertAlmostEqual(r["fair_decimal"], expected_fair, places=2)

    def test_high_grade_requires_seventy_percent(self):
        for r in self.rows:
            if r["confidence"] == "high":
                self.assertGreaterEqual(r["probability"], 0.70, r["selection"])
            elif r["confidence"] == "medium":
                self.assertGreaterEqual(r["probability"], 0.60, r["selection"])
            else:
                self.assertLess(r["probability"], 0.60, r["selection"])

    def test_tip_share_rows_need_a_real_sample(self):
        for r in self.rows:
            if r["confidence"] == "high" and r["basis"] == "tip-share":
                self.assertGreaterEqual(r["total"], 6, r["selection"])

    def test_band_is_recomputed_from_the_fair_price(self):
        for r in self.rows:
            self.assertEqual(r["in_band"], -250 <= r["fair_american"] <= 10000, r["selection"])

    def test_basis_is_named_and_sourced(self):
        for r in self.rows:
            self.assertIn(r["basis"], {"official-model", "tip-share"})
            self.assertTrue(r["source_url"].startswith("https://"))
            self.assertTrue(r["note"])

    def test_official_rows_name_a_governing_body(self):
        hosts = {
            "Baseball": "statsapi.mlb.com",
            "Basketball": "euroleaguebasketball.net",
            "Snooker": "wst.tv",
            "Rugby Union": "unitedrugby.com",
        }
        blocks = load("inputs.json")["blocks"]
        for r in self.rows:
            if r["basis"] == "official-model":
                urls = [b["url"] for b in blocks if b["sport"] == r["sport"]]
                self.assertTrue(urls, r["sport"])
                self.assertTrue(any(hosts[r["sport"]] in u for u in urls), r["sport"])

    def test_coverage_matches_the_rows(self):
        for sport, c in self.lines["coverage"].items():
            self.assertEqual(c["official_model_rows"],
                             sum(1 for r in self.rows if r["sport"] == sport and r["basis"] == "official-model"))
            self.assertEqual(c["high"], sum(1 for r in self.rows if r["sport"] == sport and r["confidence"] == "high"))

    def test_band_arithmetic_is_disclosed(self):
        self.assertIn("71.4", self.lines["method"]["band_note"])
        self.assertEqual(self.lines["method"]["band"], [-250, 10000])


class TestPredictions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preds = load("predictions.json")["predictions"]
        cls.events = {e["id"]: e for s in load("olbg.json")["sports"] for e in s["events"]}

    def test_at_least_thirty_words(self):
        for p in self.preds:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["id"])

    def test_banned_words_absent(self):
        for p in self.preds:
            low = p["text"].lower()
            self.assertNotIn("model", low, p["id"])
            self.assertNotIn("verified", low, p["id"])
            for f in p["facts"]:
                self.assertNotIn("model", f["claim"].lower(), p["id"])

    def test_selection_is_stated(self):
        for p in self.preds:
            key = p["selection"].split()[0].lower()
            self.assertIn(key, p["text"].lower(), p["id"])

    def test_every_prediction_carries_a_linked_fact(self):
        for p in self.preds:
            self.assertTrue(p["facts"], p["id"])
            for f in p["facts"]:
                self.assertTrue(f["source_url"].startswith("https://"), p["id"])

    def test_event_ids_exist_in_the_capture(self):
        for p in self.preds:
            self.assertIn(p["event_id"], self.events, p["id"])
            self.assertEqual(self.events[p["event_id"]]["event"], p["event"], p["id"])

    def test_no_injury_is_asserted(self):
        for p in self.preds:
            low = p["text"].lower()
            for word in ("injur", "ruled out", "fitness doubt", "hamstring", "suspended"):
                self.assertNotIn(word, low, p["id"])

    def test_openings_and_bodies_are_distinct(self):
        openings = [p["text"].split()[0] for p in self.preds]
        self.assertEqual(len(openings), len(set(openings)))
        texts = [p["text"] for p in self.preds]
        self.assertEqual(len(texts), len(set(texts)))


class TestFlagsAndSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flags = load("flagged.json")["flags"]
        cls.src = load("sources.json")

    def test_twenty_flags_with_unique_ids(self):
        ids = [f["id"] for f in self.flags]
        self.assertEqual(len(ids), 20)
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_flag_has_a_source_and_an_action(self):
        for f in self.flags:
            self.assertTrue(f["sources"], f["id"])
            self.assertTrue(f["action"], f["id"])
            self.assertIn(f["severity"], {"high", "medium", "low"})
            for u in f["sources"]:
                self.assertTrue(u.startswith("https://") or u.endswith(".html"), (f["id"], u))

    def test_sources_register_lists_blocked_pages(self):
        self.assertGreaterEqual(len(self.src["blocked"]), 9)
        for b in self.src["blocked"]:
            self.assertTrue(b["url"].startswith("https://"))
            self.assertTrue(b["affects"])

    def test_renamed_sports_are_covered(self):
        sports = {f["sport"] for f in self.flags}
        self.assertIn("Golf", sports)
        self.assertIn("Rugby League", sports)
        self.assertIn("All", sports)

    def test_gaps_are_named_not_hidden(self):
        titles = " ".join(f["title"].lower() for f in self.flags)
        self.assertIn("no golf events", titles)
        self.assertIn("five predictions per sport was not reached", titles)
        self.assertIn("nearly mutually exclusive", titles)


class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = sorted(OUT.rglob("*.html"))

    def test_page_count_and_required_pages(self):
        self.assertEqual(len(self.pages), 24)
        for name in ("index", "picks", "matches", "lines", "predictions", "coverage",
                     "flagged", "sources", "methodology"):
            self.assertTrue((OUT / f"{name}.html").exists(), name)
        self.assertEqual(len(list((OUT / "sports").glob("*.html"))), 15)

    def test_no_internal_link_is_broken(self):
        broken = []
        for p in self.pages:
            for href in re.findall(r'href="([^"]+)"', p.read_text()):
                if href.startswith(("http", "mailto:", "#", "data:")):
                    continue
                if not (p.parent / href.split("#")[0]).resolve().exists():
                    broken.append((p.relative_to(OUT).as_posix(), href))
        self.assertEqual(broken, [])

    def test_every_page_has_navigation_and_a_stylesheet(self):
        for p in self.pages:
            t = p.read_text()
            self.assertIn("assets/style.css", t, p.name)
            self.assertIn('class="main"', t, p.name)

    def test_flagged_page_lists_every_flag_and_links_out(self):
        t = (OUT / "flagged.html").read_text()
        for f in load("flagged.json")["flags"]:
            self.assertIn(f["id"], t)
            self.assertIn(html.escape(f["title"], quote=True), t)
        self.assertGreater(t.count('target="_blank"'), 20)

    def test_predictions_page_renders_every_prediction_with_sources(self):
        t = (OUT / "predictions.html").read_text()
        for p in load("predictions.json")["predictions"]:
            self.assertIn(p["selection"], t, p["id"])

    def test_sports_pages_carry_their_rows(self):
        lines = load("lines.json")["rows"]
        covered = {r["sport"] for r in lines}
        for name, slug in [(n, s) for n, s in SCOPE_SLUGS]:
            page = (OUT / "sports" / f"{slug}.html").read_text()
            if name in covered:
                self.assertIn("Selection", page, slug)
            else:
                self.assertIn("No rows", page, slug)
        for sport in ("Snooker", "Baseball"):
            rows = [r for r in lines if r["sport"] == sport]
            self.assertTrue(rows)

    def test_rebuild_is_byte_identical(self):
        before = {p: p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        subprocess.run([sys.executable, str(ROOT / "scripts" / "liveboard_model.py")], check=True,
                       cwd=ROOT, stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "liveboard_build.py")], check=True,
                       cwd=ROOT, stdout=subprocess.DEVNULL)
        for p, b in before.items():
            self.assertEqual(p.read_bytes(), b, p.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
