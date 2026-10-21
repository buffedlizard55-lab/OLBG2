import copy
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build import DATA, OUT, build, link, validate  # noqa: E402
from model import evaluate, markets  # noqa: E402


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ("a", "link"):
            self.links += [v for k, v in attrs if k == "href"]


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_snapshot_valid(self):
        validate(self.data)

    def test_excluded_sport_rejected(self):
        for sport in ("Football", "Boxing", "UFC", "MMAs", "American Football", "Hurling",
                      "Horse racing", "Cycling", "Specials", "Gaelic football"):
            modified = copy.deepcopy(self.data)
            modified["events"][0]["sport"] = sport
            with self.assertRaises(ValueError, msg=sport):
                validate(modified)

    def test_unapproved_source_host_rejected(self):
        with self.assertRaises(ValueError):
            link("https://example.com/score", "bad")
        with self.assertRaises(ValueError):
            link("javascript:alert(1)", "bad")

    def test_unapproved_event_source_rejected(self):
        modified = copy.deepcopy(self.data)
        modified["events"][0]["sources"]["official"] = "https://example.com/x"
        with self.assertRaises(ValueError):
            validate(modified)

    def test_high_confidence_requires_long_narrative(self):
        modified = copy.deepcopy(self.data)
        high = next(e for e in modified["events"] if e["pick"]["confidence"] == "high")
        high["pick"]["narrative"] = "Short call."
        with self.assertRaises(ValueError):
            validate(modified)

    def test_high_confidence_narrative_must_name_selection(self):
        modified = copy.deepcopy(self.data)
        high = next(e for e in modified["events"] if e["pick"]["confidence"] == "high")
        high["pick"]["narrative"] = " ".join(["word"] * 40)
        with self.assertRaises(ValueError):
            validate(modified)

    def test_pick_must_match_model(self):
        modified = copy.deepcopy(self.data)
        modified["events"][0]["pick"]["selection"] = "Someone Else"
        with self.assertRaises(ValueError):
            validate(modified)

    def test_confidence_must_match_model(self):
        modified = copy.deepcopy(self.data)
        pick = modified["events"][0]["pick"]
        pick["confidence"] = "low" if pick["confidence"] != "low" else "high"
        with self.assertRaises(ValueError):
            validate(modified)

    def test_coverage_row_count_must_match(self):
        modified = copy.deepcopy(self.data)
        modified["coverage"][0]["rows"] += 1
        with self.assertRaises(ValueError):
            validate(modified)

    def test_every_event_has_three_sources_and_two_teams(self):
        for e in self.data["events"]:
            for key in ("official", "official_api", "olbg"):
                self.assertTrue(e["sources"][key].startswith("https://"), (e["id"], key))
            self.assertNotEqual(e["away"]["name"], e["home"]["name"])
            self.assertIn(e["sport"], {c["sport"] for c in self.data["coverage"]})

    def test_all_high_narratives_are_unique_and_long_enough(self):
        texts = [e["pick"]["narrative"] for e in self.data["events"] if e["pick"]["narrative"]]
        self.assertEqual(len(texts), len(set(texts)), "narratives must not repeat")
        for text in texts:
            self.assertGreaterEqual(len(text.split()), 30)


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text(encoding="utf-8"))
        self.params = self.data["model"]

    def test_two_way_probabilities_sum_to_one(self):
        for e in self.data["events"]:
            mk = evaluate(e, self.params)
            # displayed percentages are rounded to 0.1pp, so the printed sum can sit 0.2pp below 100
            self.assertAlmostEqual(mk["money_line"]["home"] + mk["money_line"]["away"], 100.0, delta=0.25)

    def test_fair_odds_are_inverse_probability(self):
        for e in self.data["events"]:
            mk = markets(e["home"], e["away"], self.params)
            p = mk["money_line"]["home"] / 100.0
            # odds are derived from the exact probability, not the displayed 0.1pp one
            self.assertAlmostEqual(mk["money_line"]["home_odds"], round(1 / p, 2), delta=0.02)

    def test_complementary_markets_sum_to_one(self):
        for e in self.data["events"]:
            mk = markets(e["home"], e["away"], self.params)
            self.assertAlmostEqual(mk["puck_line"]["home_minus_1_5"] + mk["puck_line"]["away_plus_1_5"], 100.0, delta=0.25)
            self.assertAlmostEqual(mk["totals"]["5.5"]["over"] + mk["totals"]["5.5"]["under"], 100.0, delta=0.25)

    def test_expected_goals_follow_inputs(self):
        """A team that scores more and concedes less must never be priced longer."""
        for e in self.data["events"]:
            mk = evaluate(e, self.params)
            gf_diff = e["home"]["gf_pg"] - e["home"]["ga_pg"]
            if gf_diff > 0.5:
                self.assertGreater(mk["money_line"]["home"], 50.0, e["id"])

    def test_model_is_deterministic(self):
        e = self.data["events"][0]
        self.assertEqual(markets(e["home"], e["away"], self.params), markets(e["home"], e["away"], self.params))

    def test_changing_parameters_changes_prices(self):
        e = self.data["events"][0]
        base = markets(e["home"], e["away"], self.params)
        shifted = dict(self.params, home_multiplier=1.5)
        self.assertNotEqual(base["money_line"]["home"], markets(e["home"], e["away"], shifted)["money_line"]["home"])


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_generated_local_links_resolve(self):
        for page in OUT.rglob("*.html"):
            parser = LocalLinks()
            parser.feed(page.read_text(encoding="utf-8"))
            for target in parser.links:
                if urlparse(target).scheme or target.startswith("#"):
                    continue
                path = (page.parent / unquote(urlparse(target).path)).resolve()
                self.assertTrue(path.is_relative_to(OUT.resolve()), f"{page}: escapes site root")
                self.assertTrue(path.is_file(), f"{page.name}: broken link {target}")

    def test_navigation_and_categories_exist(self):
        for target in ("index.html", "fixtures.html", "sports/index.html", "methodology.html",
                       "sources.html", "flagged.html", "assets/style.css"):
            self.assertTrue((OUT / target).is_file(), target)
        for cov in self.data["coverage"]:
            self.assertTrue((OUT / "sports" / f'{cov["slug"]}.html').is_file(), cov["slug"])

    def test_every_fixture_appears_with_a_source_link(self):
        fixtures = (OUT / "fixtures.html").read_text(encoding="utf-8")
        for e in self.data["events"]:
            self.assertIn(e["away"]["name"], fixtures)
            self.assertIn(e["sources"]["official"], fixtures)
            self.assertIn(e["sources"]["olbg"], fixtures)

    def test_flags_page_lists_every_flag(self):
        flagged = (OUT / "flagged.html").read_text(encoding="utf-8")
        for f in self.data["flags"]:
            self.assertIn(f["item"].replace("&", "&amp;"), flagged)

    def test_no_unrendered_placeholders(self):
        for page in OUT.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("None</", text, page.name)
            self.assertNotIn("None%", text, page.name)
            self.assertNotIn("&lt;span", text, page.name)

    def test_no_excluded_sport_published(self):
        index = (OUT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("Horse Racing</a>", index)
        self.assertNotIn("Boxing", index.split("coverage board")[0])


if __name__ == "__main__":
    unittest.main()
