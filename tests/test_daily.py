#!/usr/bin/env python3
"""Tests for the /daily/ layer.

These assert on the RENDERED HTML, not only on the JSON, because the defects a
link audit cannot see are the ones where a href resolves but resolves to the
wrong page - and the ones where a number is printed correctly in JSON and
wrongly in the page.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "daily")
OUT = os.path.join(ROOT, "daily")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as handle:
        return json.load(handle)


FIXTURES = load("fixtures.json")["fixtures"]
FIX = {f["id"]: f for f in FIXTURES}
LINES = load("lines.json")
PREDICTIONS = load("predictions.json")["predictions"]
FLAGS = load("flags.json")["flags"]
SOURCES = load("sources.json")["sources"]
SPORTS_HTML = sorted(f for f in os.listdir(os.path.join(OUT, "sports")) if f.endswith(".html"))
NON_SPORT_PAGES = ["index.html", "matches.html", "lines.html", "picks.html",
                   "predictions.html", "flagged.html", "sources.html", "methodology.html"]


class TestFixtures(unittest.TestCase):
    def test_every_fixture_has_an_official_https_source(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture["id"]):
                self.assertTrue(fixture["official_url"].startswith("https://"), fixture["official_url"])
                self.assertIn("source_name", fixture)
                self.assertTrue(os.path.exists(os.path.join(ROOT, fixture["capture_file"])))

    def test_no_fixture_asserts_a_date_it_could_not_read(self):
        """A row with no date must carry the reason; a row with a date must not be flagged as dateless."""
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture["id"]):
                if fixture["date"] == "":
                    self.assertTrue(fixture.get("date_note"), "blank date without a note")
                else:
                    self.assertRegex(fixture["date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_cricket_rows_have_blank_prices_and_a_reason(self):
        cricket = [f for f in FIXTURES if f["sport"] == "cricket"]
        self.assertEqual(len(cricket), 9)
        for fixture in cricket:
            rows = [r for r in LINES["rows"] if r["fixture_id"] == fixture["id"]]
            self.assertTrue(rows, "no line row at all for " + fixture["id"])
            for row in rows:
                self.assertIsNone(row["p"], "cricket price must stay blank")
                self.assertIsNone(row["fair_decimal"])
                self.assertTrue(row["blank_reason"])


class TestModel(unittest.TestCase):
    def test_counts_match_the_rows(self):
        priced = [r for r in LINES["rows"] if r["p"] is not None]
        self.assertEqual(LINES["counts"]["prices"], len(priced))
        self.assertEqual(LINES["counts"]["fixtures"], len(FIXTURES))
        self.assertEqual(LINES["counts"]["lined_fixtures"], len({r["fixture_id"] for r in priced}))
        self.assertEqual(LINES["counts"]["unlined_fixtures"],
                         len({r["fixture_id"] for r in LINES["rows"] if r["p"] is None}))

    def test_price_is_reproducible_from_the_printed_probability(self):
        for row in LINES["rows"]:
            if row["p"] is None:
                continue
            with self.subTest(selection=row["selection"]):
                self.assertAlmostEqual(row["fair_decimal"], round(1.0 / round(row["p"], 4), 2), places=2)

    def test_confidence_label_follows_the_stated_rule(self):
        for row in LINES["rows"]:
            if row["p"] is None:
                self.assertEqual(row["confidence"], "")
                continue
            expected = "high" if row["p"] >= 0.70 else "medium" if row["p"] >= 0.60 else "low"
            self.assertEqual(row["confidence"], expected, row["selection"])

    def test_in_band_flag_is_the_stated_window(self):
        for row in LINES["rows"]:
            if row["p"] is None:
                self.assertFalse(row["in_band"])
                continue
            self.assertEqual(row["in_band"], 0.7000 <= row["p"] <= 250.0 / 350.0, row["selection"])

    def test_no_line_sits_on_a_whole_number(self):
        """A whole-number handicap or total can push; every originated line is a half point."""
        for row in LINES["rows"]:
            if row["market"] == "match_winner" or row["line"] is None:
                continue
            with self.subTest(selection=row["selection"]):
                self.assertNotAlmostEqual(row["line"], round(row["line"]), places=6)

    def test_top_picks_are_the_five_highest_winners(self):
        winner = [w for w in LINES["winner_picks"] if w["sport"] == "tennis"]
        expected = sorted(winner, key=lambda w: -w["p"])[:5]
        got = LINES["top_picks"]["tennis"]
        self.assertEqual([g["fixture_id"] for g in got], [e["fixture_id"] for e in expected])
        self.assertEqual(len(got), 5)
        for pick in got:
            self.assertGreaterEqual(pick["p"], 0.70, "a top pick must clear the 70% bar")


class TestPredictions(unittest.TestCase):
    def test_five_predictions_and_all_at_least_30_words(self):
        self.assertEqual(len(PREDICTIONS), 5)
        for prediction in PREDICTIONS:
            with self.subTest(prediction=prediction["id"]):
                words = len(prediction["text"].split())
                self.assertGreaterEqual(words, 30)
                self.assertEqual(words, prediction["word_count"])

    def test_each_prediction_names_its_selection_and_a_player(self):
        for prediction in PREDICTIONS:
            with self.subTest(prediction=prediction["id"]):
                fixture = FIX[prediction["fixture_id"]]
                self.assertIn(fixture["a"]["name"].split()[-1], prediction["text"])
                self.assertTrue(prediction["selection"].split()[0] in prediction["text"])
                self.assertIn("fair", prediction["text"])

    def test_every_prediction_fact_links_to_an_official_https_page(self):
        for prediction in PREDICTIONS:
            self.assertTrue(prediction["facts_used"], prediction["id"])
            for fact in prediction["facts_used"]:
                with self.subTest(fact=fact["fact"][:40]):
                    self.assertTrue(fact["source_url"].startswith("https://"), fact["source_url"])

    def test_predictions_are_not_repetitive(self):
        texts = [p["text"] for p in PREDICTIONS]
        self.assertEqual(len(set(texts)), len(texts), "duplicate prediction text")
        for text in texts:
            self.assertLess(text.count("at a fair"), 2, "the same closing phrase twice")
        openings = [text.split(",")[0] for text in texts]
        self.assertEqual(len(set(openings)), len(openings), "two predictions open identically")

    def test_prediction_metrics_match_the_model_rows(self):
        for prediction in PREDICTIONS:
            winner = next(w for w in LINES["winner_picks"] if w["fixture_id"] == prediction["fixture_id"])
            self.assertEqual(prediction["selection"], winner["selection"] + " to win")
            self.assertAlmostEqual(prediction["probability"], winner["p"], places=4)
            self.assertEqual(prediction["fair_american"], winner["fair_american"])


class TestRenderedPages(unittest.TestCase):
    def test_all_pages_are_built(self):
        for name in NON_SPORT_PAGES:
            self.assertTrue(os.path.exists(os.path.join(OUT, name)), name)
        # 17 eligible sports plus the index.
        self.assertEqual(len(SPORTS_HTML), 18)

    def test_no_page_has_an_unrendered_placeholder(self):
        for name in NON_SPORT_PAGES:
            html = read(os.path.join(OUT, name))
            for token in (">None<", "&lt;span", "&amp;amp;"):
                self.assertNotIn(token, html, f"{name} renders {token!r}")
            self.assertNotRegex(html, r"\bnan\b|\binf\b|\bNaN\b", name)

    def test_chrome_hrefs_are_exact_at_depth_zero(self):
        html = read(os.path.join(OUT, "index.html"))
        for target in ("index.html", "matches.html", "lines.html", "picks.html", "predictions.html",
                       "sports/index.html", "flagged.html", "sources.html", "methodology.html"):
            self.assertIn(f'<a href="{target}"', html, target)
        self.assertIn('<a class="brand" href="../index.html">', html)
        self.assertIn('href="../assets/style.css"', html)

    def test_chrome_hrefs_are_exact_at_depth_one(self):
        html = read(os.path.join(OUT, "sports", "tennis.html"))
        # In-layer chrome must stay inside /daily/, repo links must climb exactly one more level.
        self.assertIn('<a href="../index.html"', html)
        self.assertIn('href="../flagged.html"', html)
        self.assertIn('href="../../assets/style.css"', html)   # repo-root stylesheet: two levels up
        self.assertIn('href="../assets/daily.css"', html)      # layer stylesheet: one level up
        self.assertNotIn('href="../daily/', html)
        self.assertNotIn('href="/', html)

    def test_no_chrome_link_escapes_the_layer(self):
        for name in SPORTS_HTML:
            html = read(os.path.join(OUT, "sports", name))
            for href in re.findall(r'href="([^"#]+)"', html):
                if href.startswith("http"):
                    continue
                with self.subTest(page=name, href=href):
                    target = os.path.normpath(os.path.join(OUT, "sports", href))
                    # A link may climb to the repository (../../index.html) but never above it,
                    # and an in-layer link must not repeat the layer name.
                    self.assertTrue(target.startswith(ROOT + os.sep), href)
                    self.assertNotIn(os.sep + "daily" + os.sep + "daily", target)

    def test_every_internal_link_resolves(self):
        for root, _dirs, files in os.walk(OUT):
            for name in files:
                if not name.endswith(".html"):
                    continue
                path = os.path.join(root, name)
                for href in re.findall(r'href="([^"]+)"', read(path)):
                    if href.startswith(("http", "mailto:", "#", "data:")):
                        continue
                    href = href.split("#")[0]
                    if not href:
                        continue
                    target = os.path.normpath(os.path.join(root, href))
                    with self.subTest(page=os.path.relpath(path, OUT), href=href):
                        self.assertTrue(os.path.exists(target), f"{path} -> {href}")

    def test_every_anchor_target_exists(self):
        for root, _dirs, files in os.walk(OUT):
            for name in files:
                if not name.endswith(".html"):
                    continue
                path = os.path.join(root, name)
                html = read(path)
                for href in re.findall(r'href="([^"#]*#[^"]+)"', html):
                    page, anchor = href.split("#", 1)
                    target = path if not page else os.path.normpath(os.path.join(root, page))
                    with self.subTest(page=os.path.relpath(path, OUT), href=href):
                        self.assertTrue(os.path.exists(target), target)
                        self.assertIn(f'id="{anchor}"', read(target), f"missing anchor {href}")

    def test_every_fixture_row_shows_its_official_source(self):
        html = read(os.path.join(OUT, "matches.html"))
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture["id"]):
                self.assertIn(f'href="{fixture["official_url"]}"', html)

    def test_matches_page_prints_every_fixture_once(self):
        html = read(os.path.join(OUT, "matches.html"))
        for fixture in FIXTURES:
            label = f'{fixture["a"]["name"]} v {fixture["b"]["name"]}'
            self.assertEqual(html.count(f"<strong>{label}</strong>"), 1, label)

    def test_blank_dates_are_visible_not_invented(self):
        html = read(os.path.join(OUT, "matches.html"))
        blanks = [f for f in FIXTURES if not f["date"]]
        self.assertEqual(html.count('class="note"'), len(blanks))

    def test_window_disclosure_is_on_every_page_that_shows_a_price(self):
        ranked = [w for w in LINES["winner_picks"] if not w["in_band"]]
        self.assertTrue(ranked, "expected at least one priced pick")
        for name in ("index.html", "picks.html", "predictions.html", "lines.html"):
            html = read(os.path.join(OUT, name))
            with self.subTest(page=name):
                self.assertIn("DL-05", html, "the out-of-window finding must be linked")
        for name in ("index.html", "picks.html"):
            self.assertIn("outside −250 window", read(os.path.join(OUT, name)))

    def test_flagged_page_carries_every_flag_and_its_source(self):
        html = read(os.path.join(OUT, "flagged.html"))
        for flag in FLAGS:
            with self.subTest(flag=flag["id"]):
                self.assertIn(f'id="{flag["id"]}"', html)
                import html as _html
                self.assertIn(_html.escape(flag["title"], quote=True), html)
        self.assertEqual(len(FLAGS), 15)

    def test_sources_page_lists_every_source_including_the_failures(self):
        html = read(os.path.join(OUT, "sources.html"))
        for source in SOURCES:
            with self.subTest(source=source["name"]):
                self.assertIn(source["url"], html)
        failed = [s for s in SOURCES if not s["status"].startswith("read")]
        self.assertTrue(failed, "the register must record its failed reads")
        self.assertIn("failed", html)

    def test_sports_index_covers_all_seventeen(self):
        html = read(os.path.join(OUT, "sports", "index.html"))
        for name in ("Aussie Rules", "Baseball", "Basketball", "Cricket", "Darts", "eSports",
                     "Gaelic Football", "Golf", "Greyhounds", "Handball", "Ice Hockey", "Motor Racing",
                     "Rugby League", "Rugby Union", "Snooker", "Tennis", "Volleyball"):
            self.assertIn(name, html, name)

    def test_empty_sports_say_why(self):
        html = read(os.path.join(OUT, "sports", "esports.html"))
        self.assertIn("No tips found", html)
        self.assertIn("DL-11", html)

    def test_prediction_page_prints_the_full_text(self):
        html = read(os.path.join(OUT, "predictions.html"))
        for prediction in PREDICTIONS:
            body = prediction["text"].replace("'", "&#x27;")
            self.assertTrue(prediction["text"] in html or body in html, prediction["id"])

    def test_landing_counts_match_the_data(self):
        html = read(os.path.join(OUT, "index.html"))
        self.assertIn(f">{LINES['counts']['fixtures']}<", html)
        self.assertIn(f">{LINES['counts']['prices']}<", html)
        self.assertIn(f">{LINES['counts']['high_confidence_winners']}<", html)
        self.assertNotIn(">0<", html.split("Inside −250 window")[0].split("kpis")[-1][:40])

    def test_root_navigation_links_the_layer(self):
        workflow = read(os.path.join(ROOT, ".github", "workflows", "pages.yml"))
        self.assertIn("python scripts/daily_build.py", workflow)
        self.assertIn("daily data/daily", workflow)


class TestDeterminism(unittest.TestCase):
    def test_rebuild_is_byte_identical(self):
        before = {name: read(os.path.join(OUT, name)) for name in NON_SPORT_PAGES}
        before_sports = {name: read(os.path.join(OUT, "sports", name)) for name in SPORTS_HTML}
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "daily_model.py")],
                       check=True, capture_output=True, cwd=ROOT)
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "daily_build.py")],
                       check=True, capture_output=True, cwd=ROOT)
        for name, html in before.items():
            self.assertEqual(html, read(os.path.join(OUT, name)), name + " changed on rebuild")
        for name, html in before_sports.items():
            self.assertEqual(html, read(os.path.join(OUT, "sports", name)), name + " changed on rebuild")


if __name__ == "__main__":
    unittest.main()
