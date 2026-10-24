import json
import unittest
from pathlib import Path

from scripts import audit34_integrity as audit34


class Audit34IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit34.audit()
        cls.codes = {item["code"] for item in cls.report["findings"]}

    def test_official_nhl_coverage_gap_is_exact(self):
        self.assertEqual(
            self.report["summary"]["missing_nhl_fixture_ids"],
            [2026020175, 2026020176, 2026020177, 2026020178, 2026020179],
        )
        self.assertIn("NHL-OFFICIAL-COVERAGE-GAP", self.codes)
        self.assertIn("NHL-OLBG-JOIN-GAP", self.codes)

    def test_transcribed_official_fixture_fields_match_published_rows(self):
        self.assertNotIn("NHL-FIXTURE-FIELD-MISMATCH", self.codes)
        self.assertNotIn("MLB-FIXTURE-FIELD-MISMATCH", self.codes)
        self.assertEqual(self.report["summary"]["fixtures"], 8)
        self.assertEqual(self.report["summary"]["official_fixture_index"], 13)

    def test_price_arithmetic_and_band_flags_are_internally_consistent(self):
        self.assertNotIn("PRICE-AMERICAN-MISMATCH", self.codes)
        self.assertNotIn("PRICE-DECIMAL-MISMATCH", self.codes)
        self.assertNotIn("PICK-BAND-FLAG-MISMATCH", self.codes)
        self.assertTrue(audit34.within_requested_band(-250))
        self.assertTrue(audit34.within_requested_band(-237))
        self.assertFalse(audit34.within_requested_band(-251))
        self.assertTrue(audit34.within_requested_band(10000))
        self.assertFalse(audit34.within_requested_band(10001))
        self.assertEqual(audit34.american(0.70), -233)
        self.assertEqual(audit34.american(0.40), 150)

    def test_requested_confidence_rule_exposes_boston_boundary(self):
        self.assertIn("HIGH-THRESHOLD-NOT-70", self.codes)
        self.assertEqual(self.report["summary"]["high_at_stored_65_rule"], 3)
        self.assertEqual(self.report["summary"]["high_at_requested_70_rule"], 2)
        self.assertEqual(self.report["summary"]["qualified_high_in_band_with_olbg"], 1)

    def test_all_current_previews_meet_baseline_prose_rules(self):
        self.assertNotIn("PICK-PREVIEW-MISSING", self.codes)
        self.assertNotIn("PREVIEW-TOO-SHORT", self.codes)
        self.assertNotIn("PREVIEW-WORD-COUNT-MISMATCH", self.codes)
        self.assertNotIn("PREVIEW-FORBIDDEN-TERM", self.codes)
        self.assertNotIn("PREVIEW-DUPLICATE", self.codes)
        self.assertNotIn("PREVIEW-FACT-SOURCE-MISSING", self.codes)
        self.assertNotIn("PREVIEW-PICK-MISMATCH", self.codes)

    def test_every_today_table_row_has_external_review_link(self):
        self.assertGreater(self.report["summary"]["html_table_rows_checked"], 300)
        self.assertEqual(self.report["summary"]["html_rows_without_external_link"], 0)
        self.assertEqual(self.report["summary"]["local_link_errors"], 0)

    def test_qualified_quota_is_not_overstated(self):
        self.assertIn("QUALIFIED-FIVE-PER-SPORT-SHORTFALL", self.codes)
        self.assertEqual(self.report["qualified_by_sport"]["Ice Hockey"]["count"], 1)
        self.assertEqual(self.report["qualified_by_sport"]["Baseball"]["count"], 0)
        self.assertTrue(all(v["shortfall"] for v in self.report["qualified_by_sport"].values()))

    def test_manual_findings_have_review_and_source_links(self):
        data = json.loads(Path(audit34.AUDIT_DATA / "manual_findings.json").read_text())
        self.assertGreaterEqual(len(data["source_reads"]), 6)
        for row in data["source_reads"]:
            self.assertTrue(row["url"].startswith("https://"))
            self.assertTrue(row["result"].strip())
        for row in data["findings"]:
            self.assertTrue(row["source_url"].startswith("https://"))
            self.assertTrue(row["review_url"].startswith("https://"))
            self.assertTrue(row["affected_ids"])

    def test_report_is_deterministic(self):
        self.assertEqual(self.report, audit34.audit())


if __name__ == "__main__":
    unittest.main()
