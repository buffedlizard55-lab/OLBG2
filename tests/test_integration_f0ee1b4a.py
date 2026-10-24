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


class RootIntegrationTests(unittest.TestCase):
    """The root landing page is now a single front door for the current desk.

    These checks used to read the cadence-era root. The cadence layer is untouched and still
    published at /cadence/; what is asserted here is that the root derives its numbers from the
    current data and never folds earlier layers into them.
    """

    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.review = (ROOT / "integration.html").read_text(encoding="utf-8")
        cls.audit = json.loads((ROOT / "data" / "integration-f0ee1b4a" / "audit.json").read_text(encoding="utf-8"))
        cls.now = json.loads((ROOT / "data" / "playbook" / "fixtures.json").read_text(encoding="utf-8"))
        cls.now_picks = json.loads((ROOT / "data" / "playbook" / "picks.json").read_text(encoding="utf-8"))
        cls.now_preds = json.loads((ROOT / "data" / "playbook" / "predictions.json").read_text(encoding="utf-8"))
        cls.picks_page = (ROOT / "playbook" / "picks.html").read_text(encoding="utf-8")
        cls.pred_page = (ROOT / "playbook" / "predictions.html").read_text(encoding="utf-8")
        cls.archive = (ROOT / "archive.html").read_text(encoding="utf-8")

    def test_root_uses_the_current_fifteen_sport_snapshot(self):
        self.assertIn(str(self.now["match_count"]), self.index)
        self.assertIn('href="playbook/matches.html"', self.index)
        self.assertNotIn("Every eligible OLBG sport, one verified table", self.index)
        self.assertEqual(self.index.count('class="chip"'), 15)

    def test_earlier_layers_are_reachable_from_the_archive_only(self):
        self.assertNotIn("cadence/index.html", self.index)
        self.assertNotIn("master/index.html", self.index)
        self.assertIn("cadence/index.html", self.archive)
        self.assertIn("now/index.html", self.archive)

    def test_band_counts_and_writeup_shortfall_are_data_derived(self):
        self.assertIn(f'{self.now_picks["count"]} graded picks', self.index)
        self.assertIn(f'{self.now_preds["count"]} written previews', self.index)
        self.assertIn(str(self.now_preds["min_words"]) + " words at the shortest", self.index)

    def test_every_published_data_row_has_an_external_source_link(self):
        # The front door is now a summary with no data rows of its own; the published data table
        # is /playbook/picks.html and every row of it must carry a source link.
        rows = re.findall(r"<tr><td>(.*?)</tr>", self.picks_page, flags=re.S)
        self.assertGreaterEqual(len(rows), 8)
        for row in rows:
            self.assertIn("https://", row, row[:160])

    def test_prediction_anchors_resolve(self):
        anchors = re.findall(r'href="predictions\.html#([^"]+)"', self.picks_page)
        self.assertGreaterEqual(len(anchors), 4)
        for anchor in anchors:
            self.assertIn(f'id="{anchor}"', self.pred_page, anchor)

    def test_review_publishes_corrections_and_open_findings(self):
        for finding in self.audit["findings"]:
            self.assertIn(finding["id"], self.review)
            self.assertIn(finding["item"], self.review)
        self.assertIn("Open the older cross-layer audit", self.review)
        self.assertIn("AUDIT-GREY-01", self.review)
        self.assertIn("AUDIT-ODDS-02", self.review)
        self.assertEqual(self.audit["summary"]["row_internal_fail"], 0)
        self.assertEqual(len(self.audit["row_checks"]), 93)
        cork = next(row for row in self.audit["row_checks"] if row["id"] == "gaa-cork-psfc")
        self.assertIn("Nemo Rangers first", " ".join(cork["review_notes"]))
        self.assertEqual(self.audit["summary"]["errors"], [])

    def test_workflow_rebuilds_and_drift_checks_current_integration(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        for script in ("cadence_seed.py", "cadence_model.py", "cadence_predictions.py",
                       "cadence_build.py", "cadence_verify.py", "integration_f0ee1b4a_audit.py"):
            self.assertIn(f"python scripts/{script}", workflow)
        self.assertIn("cadence data/cadence data/integration-f0ee1b4a", workflow)


if __name__ == "__main__":
    unittest.main()
