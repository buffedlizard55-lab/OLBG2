import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import portal_verify  # noqa: E402


class TestPortalD81930c3(unittest.TestCase):
    def test_verify_all_invariants(self) -> None:
        summary = portal_verify.verify_all()
        self.assertEqual(summary["html_pages"], 26)
        self.assertEqual(summary["eligible_sports_lined"], 17)
        self.assertGreaterEqual(summary["originated_matches"], 155)
        self.assertEqual(summary["featured_in_band_predictions"], 34)
        self.assertGreaterEqual(summary["tbody_rows_with_https_official_link"], 400)

    def test_all_17_sports_have_in_band_high_confidence_picks(self) -> None:
        sports = {
            s["slug"]
            for s in json.loads((ROOT / "data" / "portal" / "sports.json").read_text())["eligible_sports"]
        }
        preds = json.loads((ROOT / "data" / "portal" / "predictions.json").read_text())["predictions"]
        self.assertEqual(len(sports), 17)
        self.assertEqual({p["sport"] for p in preds}, sports)
        for p in preds:
            self.assertEqual(p["confidence"], "high")
            self.assertGreaterEqual(p["fair_american"], -250)
            self.assertLessEqual(p["fair_american"], 10000)
            self.assertGreaterEqual(p["fair_decimal"], 1.40)
            self.assertLessEqual(p["fair_decimal"], 101.00)
            self.assertGreaterEqual(len(p["prediction"].split()), 30)

    def test_zero_hallucinated_repairs_present(self) -> None:
        matches = json.loads((ROOT / "data" / "portal" / "matches.json").read_text())["matches"]
        by_id = {m["id"]: m for m in matches}
        # PDC Dortmund R1: Danny Noppert vs Stephen Bunting (NOT Ritchie Edhouse)
        self.assertEqual(by_id["pdc-32330"]["home"], "Danny Noppert")
        self.assertEqual(by_id["pdc-32330"]["away"], "Stephen Bunting")
        # Completed Bank of Utah Championship must not appear on active match board
        for m in matches:
            self.assertNotIn("Bank of Utah", f"{m['competition']} {m['home']} {m['away']}")

    def test_deterministic_pipeline(self) -> None:
        before = {
            p: p.read_bytes()
            for p in list((ROOT / "data" / "portal").glob("*.json")) + list((ROOT / "portal").rglob("*.html"))
        }
        for script in ("portal_seed.py", "portal_model.py", "portal_build.py", "portal_verify.py"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)
        after = {
            p: p.read_bytes()
            for p in list((ROOT / "data" / "portal").glob("*.json")) + list((ROOT / "portal").rglob("*.html"))
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
