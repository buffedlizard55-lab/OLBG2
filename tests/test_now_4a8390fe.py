"""Tests for the /now/ desk (session arena/4a8390fe-olbg2, 2026-10-24).

They run against the committed artefacts and re-run each generator once, so a stale page or a
hand-edited data file fails the suite rather than shipping. Picked up by
``python -m unittest discover -s tests``.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "now"
OUT = ROOT / "now"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def module(name):
    spec = importlib.util.spec_from_file_location(f"now_{name}", ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NowScope(unittest.TestCase):
    def test_exactly_the_fifteen_requested_sports(self):
        self.assertEqual(set(load("fixtures.json")["sports"]), set(SPORTS))
        self.assertTrue({m["sport"] for m in load("matches.json")["matches"]} <= set(SPORTS))

    def test_every_sport_has_a_page(self):
        pages = sorted((OUT / "sports").glob("*.html"))
        self.assertEqual(len(pages), 16, "15 sport pages plus an index")

    def test_every_fixture_has_an_official_source_and_a_capture_time(self):
        for f in load("fixtures.json")["fixtures"]:
            self.assertTrue(f["official_url"].startswith("https://"), f["id"])
            self.assertGreaterEqual(len(f["facts"]), 1, f["id"])
            for fact in f["facts"]:
                self.assertTrue(fact["source_url"].startswith("https://"), f["id"])
                self.assertTrue(fact["captured_utc"].endswith("Z"), f["id"])


class NowPricing(unittest.TestCase):
    def test_every_price_is_the_reciprocal_of_its_probability(self):
        model = module("now_model")
        for row in load("lines.json")["lines"]:
            self.assertEqual(row["american"], model.american(row["probability"]),
                             f'{row["fixture_id"]} {row["selection"]}')
            self.assertEqual(row["in_band"], -250 <= row["american"] <= 10000)

    def test_band_boundary_is_the_documented_71_43_percent(self):
        self.assertEqual(round(100 / 1.40, 2), 71.43)
        model = module("now_model")
        self.assertTrue(model.in_band(-250))
        self.assertFalse(model.in_band(-251))
        self.assertTrue(model.in_band(10000))
        self.assertFalse(model.in_band(10001))

    def test_every_published_pick_is_inside_the_band(self):
        for p in load("picks.json")["picks"]:
            self.assertTrue(p["in_band"], p["id"])
            self.assertIn(p["confidence"], ("low", "medium", "high"))
            self.assertTrue(p["official_url"].startswith("https://"), p["id"])

    def test_confidence_rules_are_applied(self):
        for row in load("lines.json")["lines"]:
            if row["confidence"] == "high":
                self.assertGreaterEqual(row["probability"], 0.62, row["fixture_id"])
                self.assertNotEqual(row["basis"], "class_ladder", row["fixture_id"])
                self.assertNotEqual(row["kind"], "total", row["fixture_id"])
            if row["confidence"] == "medium":
                self.assertGreaterEqual(row["probability"], 0.55, row["fixture_id"])

    def test_blank_rows_state_a_reason(self):
        for m in load("matches.json")["matches"]:
            if not m["priced"]:
                self.assertTrue(m["blank_reason"], m["id"])


class NowProse(unittest.TestCase):
    def test_length_uniqueness_vocabulary_and_selection(self):
        preds = load("predictions.json")["predictions"]
        self.assertGreaterEqual(len(preds), 20)
        openings, texts = set(), set()
        for p in preds:
            self.assertGreaterEqual(p["words"], 30, p["id"])
            self.assertEqual(p["words"], len(p["text"].split()), p["id"])
            self.assertIsNone(BANNED.search(p["text"]), p["id"])
            self.assertIsNone(BANNED.search(p["headline"]), p["id"])
            self.assertNotIn(p["text"], texts)
            texts.add(p["text"])
            opening = " ".join(p["text"].split()[:5]).lower()
            self.assertNotIn(opening, openings, p["id"])
            openings.add(opening)
            self.assertGreaterEqual(len(p["facts"]), 2, p["id"])
            sticky = [w for w in re.findall(r"[A-Za-z]{4,}", p["selection"])]
            self.assertTrue(any(w.lower() in p["text"].lower() for w in sticky), p["id"])

    def test_every_high_and_medium_pick_has_a_preview(self):
        written = {p["fixture_id"] for p in load("predictions.json")["predictions"]}
        for pick in load("picks.json")["picks"]:
            if pick["confidence"] in {"high", "medium"}:
                self.assertIn(pick["fixture_id"], written, pick["id"])


class NowPages(unittest.TestCase):
    def _pages(self):
        return sorted(OUT.rglob("*.html"))

    def test_no_reader_facing_banned_words(self):
        for page in self._pages():
            text = re.sub(r"<[^>]+>", " ", page.read_text(encoding="utf-8"))
            self.assertIsNone(BANNED.search(text), page)

    def test_every_table_row_carries_a_source_link(self):
        for page in self._pages():
            html = page.read_text(encoding="utf-8")
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
                if "<th" in row:
                    continue
                self.assertIn("href=", row, page)

    def test_internal_links_and_anchors_resolve(self):
        ids = {p.resolve(): set(re.findall(r'id="([^"]+)"', p.read_text(encoding="utf-8")))
               for p in self._pages()}
        for page in self._pages():
            for href in re.findall(r'(?:href|src)="([^"]+)"', page.read_text(encoding="utf-8")):
                if href.startswith(("http://", "https://", "#", "data:", "mailto:")):
                    continue
                target, _, anchor = href.partition("#")
                path = (page.parent / target).resolve() if target else page.resolve()
                self.assertTrue(path.exists(), f"{page}: {href}")
                if anchor and path in ids:
                    self.assertIn(anchor, ids[path], f"{page}: {href}")

    def test_executive_summary_leads_the_landing_page(self):
        html = (OUT / "index.html").read_text(encoding="utf-8")
        self.assertLess(html.index("Executive summary"), html.index("The strongest calls"))
        self.assertIn("Where the picks are", html)
        self.assertIn('href="picks.html"', html)
        self.assertIn('href="flagged.html"', html)

    def test_only_pre_game_fixtures_are_promoted(self):
        picks = load("picks.json")
        started = {p["fixture_id"] for p in picks["picks"] if p["started"]}
        self.assertEqual(len(started), picks["started_count"])
        self.assertEqual(picks["pregame_count"] + picks["started_count"], picks["count"])
        index = (OUT / "index.html").read_text(encoding="utf-8")
        cards = re.findall(r'class="sel" href="predictions\.html#pred-([^"]+)"', index)
        self.assertTrue(cards)
        for fid in cards:
            self.assertNotIn(fid, started)
        root = (ROOT / "index.html").read_text(encoding="utf-8")
        for fid in re.findall(r'class="pickcard" href="now/predictions\.html#pred-([^"]+)"', root):
            self.assertNotIn(fid, started)

    def test_started_fixtures_are_flagged(self):
        flagged = load("flagged.json")
        self.assertTrue(any(f["id"] == "V-08" for f in flagged["flags"]))

    def test_coverage_shortfall_is_disclosed(self):
        flagged = load("flagged.json")
        coverage = [f for f in flagged["flags"] if f["id"].startswith("COV-")]
        for sport in SPORTS:
            n = load("predictions.json")["by_sport"].get(sport, 0)
            if n < 5:
                self.assertTrue(any(f["sport"] == sport for f in coverage),
                                f"{sport} shortfall not disclosed")


class NowDeterminism(unittest.TestCase):
    def test_rebuild_is_byte_identical(self):
        before = {p: p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        data_before = {p: p.read_bytes() for p in DATA.glob("*.json")}
        for name in ("now_seed", "now_model", "now_predictions", "now_build"):
            module(name).main()
        after = {p: p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        data_after = {p: p.read_bytes() for p in DATA.glob("*.json")}
        self.assertEqual(sorted(before), sorted(after))
        for path, blob in before.items():
            self.assertEqual(blob, after[path], str(path))
        self.assertEqual(sorted(data_before), sorted(data_after))
        for path, blob in data_before.items():
            self.assertEqual(blob, data_after[path], str(path))


if __name__ == "__main__":
    unittest.main()
