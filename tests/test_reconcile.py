"""Tests for the cross-layer reconciliation console (session arena/3552df3e-olbg2).

The audit is deterministic, so these tests pin the behaviour that makes its findings
trustworthy: identity normalisation, non-fixture classification, internal consistency of
the report, and the provenance rules the brief requires (a source link on every row;
nothing inferred).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reconcile"
SITE = ROOT / "reconcile"

sys.path.insert(0, str(ROOT / "scripts"))
import reconcile_audit as ra  # noqa: E402


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


class NormalisationTests(unittest.TestCase):
    def test_accents_and_punctuation_collapse(self):
        self.assertEqual(ra.norm_name("IF Björklöven"), ra.norm_name("IF Bjorkloven"))
        self.assertEqual(ra.norm_name("St. Louis Blues"), "st louis blues")

    def test_alias_resolution_merges_la_and_los_angeles(self):
        self.assertEqual(ra.norm_name("LA Clippers"), ra.norm_name("Los Angeles Clippers"))

    def test_club_code_expands_only_from_captured_tables(self):
        self.assertEqual(ra.expand_side("BOS"), "Boston Bruins")
        # a code the repository never captured is left alone, never invented
        self.assertEqual(ra.expand_side("ZZZ"), "ZZZ")

    def test_sport_slug_is_case_and_separator_insensitive(self):
        self.assertEqual(ra.sport_slug("Ice Hockey"), "ice-hockey")
        self.assertEqual(ra.sport_slug("ice_hockey"), "ice-hockey")
        self.assertEqual(ra.sport_slug("Rugby Union"), "rugby-union")

    def test_fixture_key_is_order_insensitive(self):
        a = {"sport": "ice-hockey", "date": "2026-10-22", "home_norm": "boston bruins", "away_norm": "nashville predators"}
        b = dict(a, home_norm="nashville predators", away_norm="boston bruins")
        self.assertEqual(ra.fixture_key(a), ra.fixture_key(b))

    def test_dates_are_extracted_not_guessed(self):
        self.assertEqual(ra.as_date("2026-10-22 19:00 ET"), "2026-10-22")
        self.assertEqual(ra.as_date("19:00 ET"), "")


class ClassifierTests(unittest.TestCase):
    def test_real_fixture(self):
        self.assertEqual(ra.classify("Boston Bruins", "Nashville Predators",
                                     "NHL Regular Season 2026-27")[0], "fixture")

    def test_outright_is_not_a_fixture(self):
        cls, reason = ra.classify("Inter-County Outright", "Field",
                                  "All-Ireland Senior Football Championship 2027")
        self.assertEqual(cls, "non_fixture")
        self.assertIn("outright", reason)

    def test_tournament_field_is_not_a_fixture(self):
        cls, _ = ra.classify("120-Player Strokeplay Field", "Port Royal Golf Course",
                             "PGA Tour — Butterfield Bermuda Championship")
        self.assertEqual(cls, "non_fixture")

    def test_race_card_is_not_a_fixture(self):
        cls, _ = ra.classify("11:14 Kinsley — 6-Trap Race Card", "GBGB Licensed Meeting",
                             "UK Greyhounds")
        self.assertEqual(cls, "non_fixture")

    def test_field_opponent_is_not_a_fixture(self):
        cls, _ = ra.classify("Kimi Antonelli (Mercedes)", "19-Driver Field",
                             "Formula 1 United States Grand Prix")
        self.assertEqual(cls, "non_fixture")

    def test_gaelic_football_is_not_soccer(self):
        cls, _ = ra.classify("St Finbarr's", "Nemo Rangers",
                             "Cork Premier Senior Football Championship")
        self.assertEqual(cls, "fixture")
        self.assertEqual(ra.sport_slug("Gaelic Football"), "gaelic-football")


class ReportIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = load("report.json")
        cls.rows = load("rows.json")
        cls.totals = cls.report["totals"]
        cls.findings = cls.report["findings"]

    def test_rows_file_matches_report_total(self):
        self.assertEqual(self.rows["count"], self.totals["rows"])
        self.assertEqual(len(self.rows["rows"]), self.totals["rows"])

    def test_fixture_and_non_fixture_counts_add_up(self):
        self.assertEqual(self.totals["fixtures"] + self.totals["non_fixtures"], self.totals["rows"])

    def test_every_non_fixture_has_a_reason(self):
        for row in self.findings["non_fixture"]:
            self.assertTrue(row["reason"], row)
            self.assertTrue(row["layer"])

    def test_price_conflicts_really_differ(self):
        for c in self.findings["price_conflict"]:
            values = {v["decimal"] for v in c["values"]}
            self.assertGreater(len(values), 1, c)
            self.assertGreater(c["spread"], 0)

    def test_confidence_conflicts_have_at_least_two_grades(self):
        for c in self.findings["confidence_conflict"]:
            self.assertGreater(len({g["confidence"] for g in c["grades"]}), 1, c)

    def test_rule_violations_are_genuine(self):
        for v in self.findings["rule_violations"]:
            if "70%" in v["why"]:
                self.assertLess(v["probability"], 0.70, v)
            else:
                self.assertFalse(1.40 <= v["decimal"] <= 101.0, v)

    def test_no_excluded_sport_rows(self):
        self.assertEqual(self.totals["excluded_scope_rows"], 0)
        for row in self.rows["rows"]:
            self.assertNotIn(row["sport"], ra.EXCLUDED_SLUGS, row)

    def test_all_seventeen_eligible_sports_appear(self):
        self.assertEqual(self.totals["sports"], 17)
        self.assertEqual(set(self.findings["eligible_coverage"]), set(ra.ELIGIBLE_SLUGS))

    def test_every_case_json_row_has_a_sport_and_layer(self):
        for row in self.rows["rows"]:
            self.assertIn(row["layer"], self.report["layers"])
            self.assertTrue(row["sport"])

    def test_predictions_meet_the_word_floor_and_are_unique(self):
        preds = self.findings["predictions"]
        self.assertEqual(preds["under_30"], 0)
        self.assertEqual(preds["duplicate_texts"], 0)
        texts = [p["text"] for p in preds["rows"] if p["text"]]
        self.assertEqual(len(texts), len(set(texts)))


class ProvenanceTests(unittest.TestCase):
    def test_spot_checks_are_first_hand_and_linked(self):
        doc = load("spot_checks.json")
        self.assertTrue(doc["checks"])
        for c in doc["checks"]:
            self.assertIn(c["verdict"], doc["verdict_key"], c["id"])
            self.assertTrue(c["official_url"].startswith("https://"), c["id"])
            self.assertTrue(c["observed"], c["id"])
            self.assertTrue(c["claim_checked"], c["id"])

    def test_contradicted_check_names_the_official_evidence(self):
        doc = load("spot_checks.json")
        bad = [c for c in doc["checks"] if c["verdict"] == "contradicted"]
        self.assertTrue(bad, "the audit records at least one contradiction")
        for c in bad:
            self.assertGreater(len(c["observed"]), 80)

    def test_rows_without_a_source_url_are_never_called_confirmed(self):
        rows = load("rows.json")["rows"]
        no_url = [r for r in rows if not r["official_url"]]
        self.assertEqual(sum(1 for r in no_url if r.get("scope") == "fixture"), 0)


class SiteTests(unittest.TestCase):
    def test_expected_pages_exist(self):
        for name in ["index", "conflicts", "non-fixtures", "freshness", "provenance",
                     "predictions", "spot-checks", "flagged", "methodology", "sources",
                     "sports/index"]:
            self.assertTrue((SITE / f"{name}.html").exists(), name)

    def test_flagged_page_lists_every_flag_with_evidence(self):
        text = (SITE / "flagged.html").read_text(encoding="utf-8")
        ids = re.findall(r"<td>R(\d{2})</td>", text)
        self.assertGreaterEqual(len(ids), 9)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("Flagged for review", text)
        self.assertIn("material", text)

    def test_no_page_claims_a_value_it_does_not_publish(self):
        text = (SITE / "index.html").read_text(encoding="utf-8")
        report = load("report.json")
        self.assertIn(f"{report['totals']['rows']:,}", text)
        self.assertIn(str(report["totals"]["non_fixtures"]), text)

    def test_verifier_passes(self):
        out = subprocess.run([sys.executable, "scripts/reconcile_verify.py"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_build_is_deterministic(self):
        before = (SITE / "index.html").read_bytes()
        out = subprocess.run([sys.executable, "scripts/reconcile_build.py"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(before, (SITE / "index.html").read_bytes())


if __name__ == "__main__":
    unittest.main()
