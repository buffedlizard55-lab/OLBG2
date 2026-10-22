"""Unit test suite for the /board/ unified verification & origination layer (arena/ddcbf63c-olbg2)."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "board"
BOARD_DIR = ROOT / "board"

EXCLUDED_SLUGS = {
    "soccer",
    "football",
    "american-football",
    "boxing",
    "ufc",
    "mma",
    "hurling",
    "horse-racing",
    "cycling",
    "specials",
}


def expected_american(dec: float) -> int:
    if dec <= 1.0:
        return -10000
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100))
    return int(round(-100.0 / (dec - 1.0)))


class TestBoardLayerDdcbf63c(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matches_payload = json.loads((DATA_DIR / "matches.json").read_text(encoding="utf-8"))
        cls.preds_payload = json.loads((DATA_DIR / "predictions.json").read_text(encoding="utf-8"))
        cls.sports_payload = json.loads((DATA_DIR / "sports.json").read_text(encoding="utf-8"))
        cls.sources_payload = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
        cls.flagged_payload = json.loads((DATA_DIR / "flagged.json").read_text(encoding="utf-8"))
        cls.audit_payload = json.loads((DATA_DIR / "repo_audit.json").read_text(encoding="utf-8"))

    def test_excluded_sports_strictly_absent(self) -> None:
        for m in self.matches_payload["matches"]:
            self.assertNotIn(m["sport"].lower(), EXCLUDED_SLUGS)
        for p in self.preds_payload["predictions"]:
            self.assertNotIn(p["sport"].lower(), EXCLUDED_SLUGS)

    def test_matches_deduplication_and_counts(self) -> None:
        matches = self.matches_payload["matches"]
        counts = self.matches_payload["counts"]
        self.assertEqual(len(matches), 207)
        self.assertEqual(counts["total"], 207)
        self.assertEqual(counts["originated"], 167)
        self.assertEqual(counts["unlined"], 40)

        ids = [m["id"] for m in matches]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate match IDs found in data/board/matches.json")

        # Verify MLB World Series Games 1-7 use canonical gamePk IDs and not duplicate mlb-ws-g1..g4
        for dup_id in ("mlb-ws-g1", "mlb-ws-g2", "mlb-ws-g3", "mlb-ws-g4"):
            self.assertNotIn(dup_id, ids)
        for canonical_id in (
            "mlb-849805",
            "mlb-849802",
            "mlb-849804",
            "mlb-849803",
            "mlb-849799",
            "mlb-849801",
            "mlb-849800",
        ):
            self.assertIn(canonical_id, ids)

    def test_originated_vs_unlined_integrity_and_american_odds_math(self) -> None:
        orig_count = 0
        unlined_count = 0
        for m in self.matches_payload["matches"]:
            self.assertTrue(str(m.get("official_url", "")).startswith("https://"))
            self.assertTrue(str(m.get("olbg_url", "")).startswith("https://"))
            if m.get("line_status") == "originated":
                orig_count += 1
                wm = m.get("winner_market")
                pk = m.get("pick")
                self.assertIsNotNone(wm)
                self.assertIsNotNone(pk)
                self.assertIn(pk.get("confidence"), {"low", "medium", "high"})
                self.assertEqual(
                    pk["fair_american"],
                    expected_american(pk["fair_odds"]),
                    f"Decimal/American mismatch on {m['id']}",
                )
                self.assertEqual(
                    wm["home_american"],
                    expected_american(wm["home_odds"]),
                )
                self.assertEqual(
                    wm["away_american"],
                    expected_american(wm["away_odds"]),
                )
            else:
                unlined_count += 1
                self.assertIsNone(m.get("winner_market"))
                self.assertIsNone(m.get("handicap_market"))
                self.assertIsNone(m.get("total_market"))
                self.assertIsNone(m.get("pick"))
        self.assertEqual(orig_count, 167)
        self.assertEqual(unlined_count, 40)

    def test_high_confidence_predictions_requirements(self) -> None:
        preds = self.preds_payload["predictions"]
        self.assertEqual(len(preds), 35)
        self.assertEqual(self.preds_payload["strict_70pct_count"], 22)
        self.assertEqual(self.preds_payload["multifactor_count"], 13)

        narratives = set()
        for p in preds:
            mid = p["match_id"]
            text = p["text"]
            words = len(re.findall(r"\S+", text))
            self.assertEqual(words, p["word_count"])
            self.assertGreaterEqual(words, 30, f"Prediction {mid} has fewer than 30 words ({words})")
            self.assertGreaterEqual(p["fair_american"], -250, f"{mid} below -250 focus band")
            self.assertLessEqual(p["fair_american"], 10000, f"{mid} above +10000 focus band")
            self.assertEqual(p["fair_american"], expected_american(p["fair_odds"]))
            self.assertEqual(p["confidence"], "high")
            self.assertTrue(p.get("player_cited"), f"Missing player_cited on {mid}")
            self.assertTrue(p.get("form_cited"), f"Missing form_cited on {mid}")
            self.assertTrue(p.get("history_cited"), f"Missing history_cited on {mid}")
            self.assertTrue(p.get("selection"), f"Missing selection on {mid}")
            self.assertTrue(str(p.get("official_url", "")).startswith("https://"))
            self.assertTrue(str(p.get("olbg_url", "")).startswith("https://"))
            narratives.add(text)

        self.assertEqual(len(narratives), 35, "All 35 high-confidence narratives must be unique")

    def test_board_html_pages_and_row_source_links(self) -> None:
        expected_pages = [
            BOARD_DIR / "index.html",
            BOARD_DIR / "matches.html",
            BOARD_DIR / "picks.html",
            BOARD_DIR / "flagged.html",
            BOARD_DIR / "sources.html",
            BOARD_DIR / "audit.html",
        ]
        for sp in self.sports_payload["eligible_sports"]:
            expected_pages.append(BOARD_DIR / "sports" / f"{sp['slug']}.html")

        for page in expected_pages:
            self.assertTrue(page.is_file(), f"Missing HTML page: {page}")
            content = page.read_text(encoding="utf-8")

            # Check internal relative links resolve on disk
            for href in re.findall(r'href="([^"]+)"', content):
                if href.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                rel_path = href.split("#")[0].split("?")[0]
                if not rel_path:
                    continue
                target = (page.parent / rel_path).resolve()
                self.assertTrue(target.exists(), f"Broken relative link {href} in {page}")

            # Check every tbody tr has at least one official https:// link
            for tbody in re.findall(r"<tbody[^>]*>(.*?)</tbody>", content, flags=re.S):
                rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody, flags=re.S)
                for r in rows:
                    self.assertIn(
                        'href="https://',
                        r,
                        f"Table row in {page.name} is missing an external https:// source link",
                    )


if __name__ == "__main__":
    unittest.main()
