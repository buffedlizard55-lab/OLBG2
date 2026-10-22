from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import beacon_verify  # noqa: E402

DATA_DIR = ROOT / "data" / "beacon"
SITE_DIR = ROOT / "beacon"


class TestBeacon3babcd0d(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sports = json.loads((DATA_DIR / "sports.json").read_text())
        cls.sources = json.loads((DATA_DIR / "sources.json").read_text())
        cls.audit = json.loads((DATA_DIR / "repo_audit.json").read_text())
        cls.matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
        cls.picks = json.loads((DATA_DIR / "predictions.json").read_text())["predictions"]
        cls.flags = json.loads((DATA_DIR / "flagged.json").read_text())["flagged"]
        cls.summary = json.loads((DATA_DIR / "summary.json").read_text())

    def test_01_seventeen_eligible_sports_covered_and_ten_excluded(self) -> None:
        eligible_ids = {s["olbg_id"] for s in self.sports["eligible"]}
        self.assertEqual(eligible_ids, {3, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15, 20, 21, 22, 23, 25, 28})
        excluded_ids = {s["olbg_id"] for s in self.sports["excluded"]}
        self.assertEqual(excluded_ids, {1, 2, 6, 11, 16, 17, 19, 24, 26, 27})
        covered_slugs = {m["sport"] for m in self.matches}
        self.assertEqual(len(covered_slugs), 17)
        for m in self.matches:
            self.assertNotIn(m["olbg_id"], excluded_ids)
            self.assertIn(m["olbg_id"], eligible_ids)

    def test_02_every_match_has_official_and_olbg_urls_and_no_banned_links(self) -> None:
        for m in self.matches:
            self.assertTrue(m["official_url"].startswith("https://"))
            self.assertTrue(m["olbg_url"].startswith("https://www.olbg.com/betting-tips/"))
            for bad in beacon_verify.BANNED_HREF_SUBSTRINGS:
                self.assertNotIn(bad, m["official_url"])
                self.assertNotIn(bad, m["olbg_url"])

    def test_03_half_unit_spreads_and_totals_only(self) -> None:
        for m in self.matches:
            if not m["markets"]:
                continue
            hc = m["markets"].get("handicap")
            if hc:
                lh = abs(hc["line_home"])
                self.assertGreaterEqual(lh, 1.5, msg=m["id"])
                self.assertAlmostEqual(lh - math.floor(lh), 0.5, places=9, msg=m["id"])
                self.assertAlmostEqual(hc["line_home"] + hc["line_away"], 0.0, places=9)
            tot = m["markets"].get("total")
            if tot:
                tl = abs(tot["line"])
                self.assertAlmostEqual(tl - math.floor(tl), 0.5, places=9, msg=m["id"])

    def test_04_high_confidence_picks_strictly_satisfy_unrounded_bounds(self) -> None:
        self.assertGreaterEqual(len(self.picks), 15)
        high_max = 5.0 / 7.0
        for p in self.picks:
            self.assertEqual(p["confidence"], "high")
            self.assertGreaterEqual(p["model_prob_exact"], 0.7000, msg=p["pick_id"])
            self.assertLessEqual(p["model_prob_exact"], high_max, msg=p["pick_id"])
            self.assertGreaterEqual(p["fair_decimal_exact"], 1.40, msg=p["pick_id"])
            self.assertLessEqual(p["fair_decimal_exact"], 101.00, msg=p["pick_id"])
            self.assertGreaterEqual(p["fair_american"], -250, msg=p["pick_id"])
            self.assertLessEqual(p["fair_american"], 10000, msg=p["pick_id"])

    def test_05_high_confidence_prose_quality_and_verified_players(self) -> None:
        seen = set()
        for p in self.picks:
            words = p["prediction"].split()
            self.assertGreaterEqual(len(words), 30, msg=p["pick_id"])
            self.assertEqual(len(words), p["word_count"])
            self.assertNotIn(p["prediction"], seen)
            seen.add(p["prediction"])
            self.assertGreaterEqual(len(p["verified_players"]), 2, msg=p["pick_id"])
            # At least two verified players must appear in the prose itself
            hits = sum(1 for pl in p["verified_players"] if pl.split()[-1] in p["prediction"])
            self.assertGreaterEqual(hits, 2, msg=f"Missing player names in {p['pick_id']}")

    def test_06_intraday_pdc_humphries_withdrawal_applied(self) -> None:
        darts_pairs = {(m["home"], m["away"]) for m in self.matches if m["sport"] == "darts"}
        self.assertIn(("Kim Huybrechts", "Ryan Searle"), darts_pairs)
        self.assertNotIn(("Luke Humphries", "Ryan Searle"), darts_pairs)
        for p in self.picks:
            self.assertNotIn("Luke Humphries", p["selection"])

    def test_07_real_aflw_round_11_and_no_fabricated_atp_or_1v1_golf_f1_greyhound_rows(self) -> None:
        afl_pairs = {(m["home"], m["away"]) for m in self.matches if m["sport"] == "aussie-rules"}
        self.assertIn(("Port Adelaide Power", "Collingwood Magpies"), afl_pairs)
        self.assertIn(("Western Bulldogs", "Melbourne Demons"), afl_pairs)
        self.assertNotIn(("Hawthorn Hawks", "Melbourne Demons"), afl_pairs)

        tennis_pairs = {(m["home"], m["away"]) for m in self.matches if m["sport"] == "tennis"}
        self.assertNotIn(("Arthur Fils", "Adrian Mannarino"), tennis_pairs)

        for m in self.matches:
            if m["sport"] in ("golf", "motor-racing") and m["match_state"] != "unverified_blank":
                self.assertEqual(m["event_type"], "outright_field")

    def test_08_unverified_rows_left_strictly_blank_and_flagged(self) -> None:
        blanks = [m for m in self.matches if m["match_state"] == "unverified_blank"]
        self.assertGreaterEqual(len(blanks), 6)
        flagged_ids = {f["flag_id"] for f in self.flags}
        for b in blanks:
            self.assertIsNone(b["markets"])
            self.assertEqual(b["winner_pick"]["selection"], "—")
            self.assertEqual(b["home_form"], "—")
            self.assertEqual(b["away_form"], "—")
            self.assertIn(f"UNVERIFIED-{b['id']}", flagged_ids)

    def test_09_all_html_pages_pass_row_source_and_broken_link_verifier(self) -> None:
        res = beacon_verify.verify_all()
        self.assertTrue(res["ok"], msg=f"Verifier errors: {res['errors']}")
        self.assertEqual(res["pages"], 26)
        self.assertGreater(res["tbody_rows"], 500)

    def test_10_deterministic_rebuild_zero_drift(self) -> None:
        tracked = sorted(list(DATA_DIR.glob("*.json")) + list(SITE_DIR.rglob("*.html")))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
        for script in ("beacon_seed.py", "beacon_model.py", "beacon_build.py"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True, cwd=str(ROOT))
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
