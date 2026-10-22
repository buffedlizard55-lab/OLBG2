"""End-to-end automated test suite for /hub/ (session arena/42c8f6be-olbg2)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB_DATA = ROOT / "data" / "hub"
HUB_DIR = ROOT / "hub"


def sha256_tree(paths: list[Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(paths):
        if p.is_file():
            out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


class TestHubOriginationSuite(unittest.TestCase):
    def test_01_pipeline_rebuilds_deterministically(self) -> None:
        tracked = list(HUB_DATA.glob("*.json")) + list(HUB_DIR.rglob("*"))
        before = sha256_tree(tracked)
        for script in ("hub_seed.py", "hub_model.py", "hub_build.py", "hub_verify.py"):
            res = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, msg=f"{script} failed:\n{res.stdout}\n{res.stderr}")
        after = sha256_tree(list(HUB_DATA.glob("*.json")) + list(HUB_DIR.rglob("*")))
        self.assertEqual(before, after, "Re-running hub_{seed,model,build}.py mutated committed files")

    def test_02_sport_scope_and_id_corrections(self) -> None:
        sports = json.loads((HUB_DATA / "sports.json").read_text(encoding="utf-8"))
        self.assertEqual(len(sports["eligible"]), 17)
        self.assertEqual(len(sports["excluded"]), 10)
        by_slug = {s["slug"]: s for s in sports["eligible"]}
        self.assertEqual(by_slug["basketball"]["olbg_sport_id"], 4)
        self.assertEqual(by_slug["golf"]["olbg_sport_id"], 5)
        excl_by_slug = {s["slug"]: s for s in sports["excluded"]}
        self.assertEqual(excl_by_slug["boxing"]["olbg_sport_id"], 16)
        self.assertEqual(excl_by_slug["cycling"]["olbg_sport_id"], 17)

    def test_03_fair_odds_zero_overround_and_band_invariants(self) -> None:
        matches = json.loads((HUB_DATA / "matches.json").read_text(encoding="utf-8"))["rows"]
        preds = json.loads((HUB_DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]
        self.assertEqual(len(matches), 189)
        orig = [r for r in matches if r["status"] == "originated"]
        unl = [r for r in matches if r["status"] == "unlined"]
        self.assertEqual(len(orig), 159)
        self.assertEqual(len(unl), 30)
        self.assertEqual(len(preds), 25)
        self.assertGreaterEqual(len({p["sport"] for p in preds}), 9)

        for p in preds:
            self.assertGreaterEqual(p["fair_decimal"], 1.40)
            self.assertLessEqual(p["fair_decimal"], 101.00)
            self.assertTrue((-250 <= p["fair_american"] <= -100) or (100 <= p["fair_american"] <= 10000))
            self.assertGreaterEqual(len(p["text"].split()), 30)

    def test_04_html_links_fragments_and_row_sources(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import hub_verify  # noqa: PLC0415

        summary = hub_verify.verify_all()
        self.assertEqual(summary["html_pages"], 22)
        self.assertGreaterEqual(summary["table_rows_verified_with_https_source"], 500)
        self.assertGreaterEqual(summary["internal_links_and_fragments_verified"], 700)


if __name__ == "__main__":
    unittest.main()
