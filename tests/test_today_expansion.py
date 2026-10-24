"""Regression coverage for the expanded NHL/NBA official-data board."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
NBA_INJURY = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_30PM.pdf"


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


class TodayExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = load("olbg_listings")
        cls.fixtures = {f["id"]: f for f in cls.board["fixtures"]}
        cls.lines = load("lines")["lines"]
        cls.picks = load("picks")["picks"]
        cls.predictions = load("predictions")["predictions"]

    def test_complete_official_nhl_and_nba_slates(self):
        self.assertEqual(sum(f["sport"] == "Ice Hockey" for f in self.fixtures.values()), 12)
        self.assertEqual(sum(f["sport"] == "Basketball" for f in self.fixtures.values()), 8)
        self.assertEqual(sum(f["sport"] == "Baseball" for f in self.fixtures.values()), 1)
        self.assertEqual(sum(f["sport"] == "Tennis" for f in self.fixtures.values()), 3)
        self.assertEqual(sum(f["sport"] == "Volleyball" for f in self.fixtures.values()), 6)
        self.assertEqual(sum(f["sport"] == "Handball" for f in self.fixtures.values()), 5)
        self.assertEqual(sum(f["sport"] == "Motor Racing" for f in self.fixtures.values()), 1)
        self.assertEqual(sum(f["sport"] == "Darts" for f in self.fixtures.values()), 3)
        self.assertEqual(len(self.fixtures), 39)

    def test_every_fixture_has_all_three_market_families(self):
        expected = {
            "Ice Hockey": ({"Moneyline", "Puck line", "Total goals"}, 10),
            "Basketball": ({"Moneyline", "Point spread", "Total points"}, 6),
            "Baseball": ({"Moneyline", "Run line", "Total runs"}, 10),
            "Tennis": ({"Moneyline", "Set handicap", "Total sets"}, 8),
            "Volleyball": ({"Moneyline", "Set handicap", "Total sets"}, 10),
            "Handball": ({"Moneyline", "Match handicap", "Total goals"}, 7),
            "Motor Racing": ({"Race winner", "Podium finish"}, 66),
            "Darts": ({"Moneyline", "Leg handicap", "Total legs"}, 8),
        }
        for fixture_id, fixture in self.fixtures.items():
            rows = [line for line in self.lines if line["fixture_id"] == fixture_id]
            markets, count = expected[fixture["sport"]]
            self.assertEqual(len(rows), count, fixture_id)
            self.assertEqual({row["market"] for row in rows}, markets, fixture_id)

    def test_five_pick_targets_where_official_slate_supports_them(self):
        for sport in ("Ice Hockey", "Basketball"):
            self.assertEqual(sum(p["sport"] == sport for p in self.picks), 5, sport)
        self.assertEqual(sum(p["sport"] == "Baseball" for p in self.picks), 1)
        self.assertEqual(sum(p["sport"] == "Tennis" for p in self.picks), 3)
        self.assertEqual(sum(p["sport"] == "Volleyball" for p in self.picks), 4)
        self.assertEqual(sum(p["sport"] == "Handball" for p in self.picks), 5)
        self.assertEqual(sum(p["sport"] == "Motor Racing" for p in self.picks), 1)
        self.assertEqual(sum(p["sport"] == "Darts" for p in self.picks), 3)
        self.assertEqual(len(self.picks), 27)

    def test_corrected_high_threshold_and_band(self):
        by_fixture = {p["fixture_id"]: p for p in self.picks}
        self.assertEqual(by_fixture["nhl-2026020170"]["confidence"], "medium")
        self.assertLess(by_fixture["nhl-2026020170"]["probability"], 0.70)
        self.assertEqual(by_fixture["nhl-2026020174"]["confidence"], "high")
        self.assertGreaterEqual(by_fixture["nhl-2026020174"]["probability"], 0.70)
        self.assertTrue(by_fixture["nhl-2026020174"]["in_band"])
        for pick in self.picks:
            self.assertEqual(pick["in_band"], -250 <= pick["fair_american"] <= 10000)

    def test_nba_spreads_are_coherent_half_point_lines(self):
        for fixture in self.fixtures.values():
            if fixture["sport"] != "Basketball":
                continue
            rows = [line for line in self.lines if line["fixture_id"] == fixture["id"]]
            home_ml = next(line for line in rows if line["market"] == "Moneyline"
                           and line["selection"] == fixture["home"])
            home_spread = next(line for line in rows if line["market"] == "Point spread"
                               and line["selection"] == fixture["home"])
            self.assertLess((home_ml["probability"] - 0.5) * home_spread["line"], 0, fixture["id"])
            for row in rows:
                if row["market"] in ("Point spread", "Total points"):
                    self.assertEqual(abs(row["line"] % 1), 0.5, row["id"])

    def test_nba_fixture_olbg_ids_match_refreshed_listing(self):
        listings = {row["event_id"]: row for row in self.board["listings"]}
        for fixture in self.fixtures.values():
            if fixture["sport"] != "Basketball":
                continue
            event_id = fixture["olbg_event_id"]
            self.assertIn(event_id, listings, fixture["id"])
            self.assertIn(f"event_id={event_id}", listings[event_id]["url"])
            self.assertEqual(fixture["olbg_listed_selection"], listings[event_id]["selection"])
            self.assertEqual(fixture["olbg_market"], listings[event_id]["market"])

    def test_nba_injury_provenance_and_pending_reports(self):
        for fixture in self.fixtures.values():
            if fixture["sport"] == "Basketball":
                for item in fixture["injuries"]:
                    self.assertEqual(item["source_url"], NBA_INJURY)
        previews = {p["fixture_id"]: p for p in self.predictions}
        self.assertIn("NOT YET SUBMITTED", previews["nba-0022600109"]["injuries_note"])
        self.assertIn("New Orleans Pelicans NOT YET SUBMITTED",
                      previews["nba-0022600110"]["injuries_note"])
        self.assertTrue(all(item["team"] != "New Orleans Pelicans"
                            for item in previews["nba-0022600110"]["injuries"]))

    def test_ambiguous_page_break_row_is_not_used(self):
        for fixture in self.fixtures.values():
            self.assertTrue(all(item["player"] != "Dean Wade" for item in fixture.get("injuries", [])))
        for preview in self.predictions:
            self.assertNotIn("Dean Wade", preview["text"])
            self.assertTrue(all("Dean Wade" not in fact["claim"] for fact in preview["facts"]))

    def test_numeric_preview_claims_have_linked_facts(self):
        for preview in self.predictions:
            claims = " ".join(fact["claim"] for fact in preview["facts"])
            numbers = set(re.findall(r"\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)*", preview["text"]))
            for number in numbers:
                self.assertIn(number, claims, (preview["id"], number))
            self.assertIn(preview["selection"], preview["text"])

    def test_sources_and_pages_no_longer_call_nba_blocked(self):
        sources = load("sources")["sources"]
        nba_games = next(s for s in sources if s["label"] == "NBA games page, 2026-10-24")
        self.assertEqual(nba_games["outcome"], "used")
        for page in (ROOT / "today").rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("NBA.com returned its games shell", text, page)
            self.assertNotIn("High is 65%", text, page)
            self.assertNotIn("NHL totals and puck lines need", text, page)


if __name__ == "__main__":
    unittest.main()
