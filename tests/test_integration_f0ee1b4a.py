"""Final-integration regression checks for the 23 October 15-sport desk.

These tests check source-to-record consistency and publication boundaries. They do not
turn a source link into proof that an external page was re-read; live spot checks are
recorded separately in research/integration-f0ee1b4a.md.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cadence"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def gaelic_points(score: str) -> int:
    """Convert a Gaelic goals-points score such as 2-12 to total points."""
    goals, points = (int(part) for part in score.split("-"))
    return goals * 3 + points


class SourceToPriceRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load("fixtures.json")["fixtures"]
        cls.matches = {row["id"]: row for row in load("matches.json")["matches"]}
        cls.picks = {row["id"]: row for row in load("picks.json")["picks"]}
        cls.sources = load("sources.json")["sources"]

    def test_cork_semi_final_scores_produce_equal_two_point_margins(self):
        row = self.matches["gaa-cork-psfc"]
        fact = next(fact["value"] for fact in row["facts"] if fact["team_or_item"] == "Semi-finals")
        scores = re.findall(r"\b\d+-\d+\b", fact)
        self.assertEqual(scores, ["1-15", "0-16", "2-12", "0-16"])
        nemo_margin = gaelic_points(scores[0]) - gaelic_points(scores[1])
        finbarrs_margin = gaelic_points(scores[2]) - gaelic_points(scores[3])
        self.assertEqual((nemo_margin, finbarrs_margin), (2, 2))
        self.assertIn("margins +2 v +2 points", row["evidence"])
        self.assertIsNone(row["home_win_probability"])  # three-way summary, not a two-way probability
        self.assertEqual(row["favourite_probability"], 0.48)
        self.assertEqual(row["confidence"], "low")
        pick = self.picks["gaa-cork-psfc-pick"]
        self.assertEqual(pick["probability"], 0.48)  # 50% two-way strength less 4% draw mass
        self.assertEqual(pick["confidence"], "low")

    def test_waterford_score_margins_still_match_the_published_basis(self):
        row = self.matches["gaa-waterford-sfc"]
        fact = next(fact["value"] for fact in row["facts"] if fact["team_or_item"] == "Semi-finals")
        scores = re.findall(r"\b\d+-\d+\b", fact)
        self.assertEqual(len(scores), 4)
        margins = (gaelic_points(scores[0]) - gaelic_points(scores[1]),
                   gaelic_points(scores[2]) - gaelic_points(scores[3]))
        self.assertEqual(margins, (2, 7))
        self.assertIn("margins +2 v +7 points", row["evidence"])

    def test_every_olbg_event_id_has_a_matching_registered_event_url(self):
        event_urls = [source["url"] for source in self.sources if "olbg.com" in source["url"]]
        for row in self.fixtures:
            event_id = row.get("olbg_event_id")
            if event_id is None:
                continue
            self.assertTrue(any(f"event_id={event_id}" in url for url in event_urls),
                            f"{row['id']}: unsupported OLBG event id {event_id}")

    def test_match_summary_is_the_actual_primary_selection(self):
        for row in self.matches.values():
            if row["status"] != "originated":
                continue
            primary = self.picks.get(f"{row['id']}-pick")
            self.assertIsNotNone(primary, row["id"])
            self.assertEqual(row["favourite"], primary["selection"], row["id"])
            self.assertEqual(row["favourite_probability"], round(primary["probability"], 4), row["id"])
            self.assertEqual(row["confidence"], primary["confidence"], row["id"])
            if not row.get("away"):
                self.assertIsNone(row["home_win_probability"], row["id"])

    def test_outright_pages_do_not_render_a_phantom_opponent(self):
        matches_html = (ROOT / "cadence" / "matches.html").read_text(encoding="utf-8")
        predictions_html = (ROOT / "cadence" / "predictions.html").read_text(encoding="utf-8")
        self.assertIn("<strong>Butterfield Bermuda Championship</strong>", matches_html)
        self.assertNotIn("Butterfield Bermuda Championship v", matches_html)
        self.assertNotIn("Formula 1 Drivers&#x27; Championship 2026 v", predictions_html)


if __name__ == "__main__":
    unittest.main()
