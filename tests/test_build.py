import copy
import html as html_lib
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build as B  # noqa: E402
import model as M  # noqa: E402


def snapshot():
    return {
        "meta": B.load("meta.json"),
        "sources": B.load("sources.json"),
        "nhl_teams": B.load("team_inputs/nhl.json"),
        "fixtures": B.load("fixtures.json"),
        "picks": B.load("picks.json"),
        "flagged": B.load("flagged.json"),
        "coverage": B.load("coverage.json"),
    }


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ("a", "link"):
            self.links += [v for k, v in attrs if k == "href"]


class DataTests(unittest.TestCase):
    def setUp(self):
        self.data = snapshot()

    def test_snapshot_validates(self):
        B.validate(self.data)
        B.build_rows(self.data)

    def test_excluded_sport_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["fixtures"]["fixtures"][0]["sport"] = "Football"
        with self.assertRaises(ValueError):
            B.validate(bad)

    def test_non_official_fixture_source_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["fixtures"]["fixtures"][0]["official_url"] = "https://example.com/game"
        with self.assertRaises(ValueError):
            B.validate(bad)

    def test_olbg_cannot_be_the_official_source(self):
        bad = copy.deepcopy(self.data)
        bad["fixtures"]["fixtures"][0]["official_url"] = bad["fixtures"]["fixtures"][0]["olbg_url"]
        with self.assertRaises(ValueError):
            B.validate(bad)

    def test_high_confidence_always_has_a_prediction(self):
        # Confidence is computed: removing the evidence pack downgrades the row instead of
        # leaving a high-confidence line without written support.
        rows = B.build_rows(self.data)
        highs = [r for r in rows if r["confidence"] == "high"]
        self.assertTrue(highs)
        for row in highs:
            self.assertIsNotNone(row["pick"])
            self.assertTrue(row["evidence"])
        bad = copy.deepcopy(self.data)
        bad["picks"]["picks"].pop(highs[0]["fixture"]["id"])
        downgraded = [r for r in B.build_rows(bad) if r["fixture"]["id"] == highs[0]["fixture"]["id"]][0]
        self.assertNotEqual(downgraded["confidence"], "high")

    def test_pick_must_match_model_favourite(self):
        bad = copy.deepcopy(self.data)
        fid = "nhl-2026020152"
        bad["picks"]["picks"][fid]["selection"] = "Philadelphia Flyers"
        with self.assertRaises(ValueError):
            B.build_rows(bad)

    def test_short_prediction_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["picks"]["picks"]["nhl-2026020152"]["narrative"] = "Sabres win."
        with self.assertRaises(ValueError):
            B.validate(bad)

    def test_duplicate_prediction_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["picks"]["picks"]["nhl-2026020154"]["narrative"] = bad["picks"]["picks"]["nhl-2026020152"]["narrative"]
        with self.assertRaises(ValueError):
            B.validate(bad)

    def test_unregistered_source_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["picks"]["picks"]["nhl-2026020152"]["sources"].append("https://www.nhl.com/not-registered")
        with self.assertRaises(ValueError):
            B.validate(bad)

    def test_prediction_must_cite_its_own_game(self):
        bad = copy.deepcopy(self.data)
        bad["picks"]["picks"]["nhl-2026020152"]["sources"] = [
            "https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154",
            "https://www.nhl.com/standings",
        ]
        with self.assertRaises(ValueError):
            B.build_rows(bad)

    def test_every_fixture_is_inside_the_window(self):
        start = self.data["meta"]["window_start"]
        end = self.data["meta"]["window_end"]
        for fx in self.data["fixtures"]["fixtures"]:
            self.assertTrue(start <= fx["date"] <= end, fx["id"])

    def test_every_pick_is_a_known_market(self):
        for fid, pick in self.data["picks"]["picks"].items():
            self.assertIn(pick["market"], B.MARKETS, fid)


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.params = B.load("meta.json")["params"]

    def test_price_and_probability_are_consistent(self):
        for p in (0.05, 0.25, 0.4, 0.5, 0.62, 0.83, 0.95):
            price = M.american(p)
            self.assertFalse(-100 < price < 100)
            self.assertAlmostEqual(M.implied(price), p, delta=0.02)

    def test_bad_probability_rejected(self):
        for p in (0, 1, -0.2, 1.2):
            with self.assertRaises(ValueError):
                M.american(p)

    def test_probabilities_are_complementary(self):
        home = {"abbr": "AAA", "name": "A", "gp": 10, "gf": 30, "ga": 30}
        away = {"abbr": "BBB", "name": "B", "gp": 10, "gf": 30, "ga": 30}
        market = M.nhl_market(home, away, self.params)
        self.assertAlmostEqual(market["money_line"]["p_home"] + market["money_line"]["p_away"], 1.0, places=3)
        self.assertAlmostEqual(market["handicap"]["p_home_cover"] + market["handicap"]["p_away_cover"], 1.0, places=3)
        self.assertAlmostEqual(market["total"]["p_over"] + market["total"]["p_under"], 1.0, places=3)

    def test_home_advantage_when_teams_are_identical(self):
        home = {"abbr": "AAA", "name": "A", "gp": 10, "gf": 30, "ga": 30}
        away = {"abbr": "BBB", "name": "B", "gp": 10, "gf": 30, "ga": 30}
        market = M.nhl_market(home, away, self.params)
        self.assertGreater(market["money_line"]["p_home"], 0.5)
        self.assertLess(market["expected_margin"], self.params["nhl_home_goals"] + 1e-9)

    def test_small_sample_is_shrunk(self):
        small = M.shrunk_goal_rate(20, 10, 2, self.params["nhl_shrink_games"])
        raw = (20 - 10) / 2
        self.assertLess(abs(small), abs(raw))

    def test_total_line_is_a_half_goal(self):
        for gf, ga, gp in ((30, 20, 10), (17, 36, 11), (42, 24, 10)):
            home = {"abbr": "AAA", "name": "A", "gp": gp, "gf": gf, "ga": ga}
            away = {"abbr": "BBB", "name": "B", "gp": gp, "gf": ga, "ga": gf}
            line = M.nhl_market(home, away, self.params)["total"]["line"]
            self.assertEqual((line * 2) % 2, 1.0, line)

    def test_baseline_nba_has_no_total(self):
        market = M.nba_market({"abbr": "AAA", "name": "A", "gp": 0}, {"abbr": "BBB", "name": "B", "gp": 0}, self.params)
        self.assertIsNone(market["total"])
        self.assertGreater(market["money_line"]["p_home"], 0.5)

    def test_confidence_caps_without_evidence(self):
        self.params = dict(self.params)
        edge = 0.2
        label, reason = M.confidence_label(edge, evidence=False, sample_ok=True, baseline=False, params=self.params)
        self.assertEqual(label, "medium")
        self.assertIn("no evidence pack", reason)
        label, _ = M.confidence_label(edge, evidence=True, sample_ok=True, baseline=False, params=self.params)
        self.assertEqual(label, "high")
        label, _ = M.confidence_label(edge, evidence=True, sample_ok=True, baseline=True, params=self.params)
        self.assertEqual(label, "low")


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = B.build()

    def test_local_links_resolve(self):
        root = B.OUT.resolve()
        for page in B.OUT.rglob("*.html"):
            parser = Links()
            parser.feed(page.read_text(encoding="utf-8"))
            for target in parser.links:
                if not target or urlparse(target).scheme or target.startswith("#"):
                    continue
                path = (page.parent / unquote(urlparse(target).path)).resolve()
                self.assertTrue(path.is_relative_to(root), f"{page}: escapes site root")
                self.assertTrue(path.is_file(), f"{page}: missing {target}")

    def test_no_insecure_links(self):
        for page in B.OUT.rglob("*.html"):
            parser = Links()
            parser.feed(page.read_text(encoding="utf-8"))
            for target in parser.links:
                if urlparse(target).scheme:
                    self.assertEqual(urlparse(target).scheme, "https", f"{page}: {target}")

    def test_unverified_sports_do_not_link_to_missing_pages(self):
        html = (B.OUT / "index.html").read_text(encoding="utf-8")
        for row in B.load("coverage.json")["coverage"]:
            if row["status"] != "covered":
                self.assertNotIn(f'href="sports/{row["slug"]}.html"', html)

    def test_navigation_targets_exist(self):
        for target in ("index.html", "picks.html", "sports/index.html", "sports/ice-hockey.html",
                       "sports/basketball.html", "methodology.html", "sources.html",
                       "flagged.html", "assets/style.css", "data/lines.json"):
            self.assertTrue((B.OUT / target).is_file(), target)

    def test_every_fixture_is_published_with_its_official_link(self):
        html = (B.OUT / "picks.html").read_text(encoding="utf-8")
        for fx in B.load("fixtures.json")["fixtures"]:
            self.assertIn(fx["official_url"], html, fx["id"])

    def test_no_excluded_sport_is_published_as_a_fixture(self):
        html = (B.OUT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("Horse racing</strong>", html)
        self.assertNotIn(">Premier League<", html)

    def test_high_confidence_rows_have_narratives_on_the_pick_sheet(self):
        html = (B.OUT / "picks.html").read_text(encoding="utf-8")
        for row in self.result["high"]:
            self.assertIn(html_lib.escape(row["pick"]["narrative"], quote=True), html)

    def test_machine_readable_output_matches_rows(self):
        payload = json.loads((B.OUT / "data" / "lines.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["fixtures"]), len(self.result["rows"]))
        for item in payload["fixtures"]:
            self.assertTrue(item["official_url"].startswith("https://"))
            self.assertIn(item["confidence"], {"low", "medium", "high"})


if __name__ == "__main__":
    unittest.main()
