#!/usr/bin/env python3
"""tests/test_slate.py — Comprehensive validation suite for /slate/ pipeline & HTML pages."""

from __future__ import annotations

import json
import pathlib
import re
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLATE_DATA = ROOT / "data" / "slate"
SLATE_HTML = ROOT / "slate"

EXCLUDED_SLUGS = {
    "soccer",
    "football",
    "boxing",
    "ufc",
    "mma",
    "mma-ufc",
    "american-football",
    "american football",
    "hurling",
    "horse-racing",
    "horse racing",
    "cycling",
    "specials",
}


class LinkAndRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.in_tbody = False
        self.in_tr = False
        self.cur_tr_https = 0
        self.tbody_row_https_counts: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        if ad.get("id"):
            self.ids.add(ad["id"])  # type: ignore[arg-type]
        if tag in ("a", "link") and ad.get("href"):
            href = ad["href"]  # type: ignore[assignment]
            self.links.append(href)
            if self.in_tbody and self.in_tr and href.startswith("https://"):
                self.cur_tr_https += 1
        if tag == "script" and ad.get("src"):
            self.links.append(ad["src"])  # type: ignore[arg-type]
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.cur_tr_https = 0

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_tbody and self.in_tr:
            self.tbody_row_https_counts.append(self.cur_tr_https)
            self.in_tr = False
        elif tag == "tbody":
            self.in_tbody = False


class TestSlateDeliverables(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seed = json.loads((SLATE_DATA / "inputs.json").read_text())
        cls.matches_doc = json.loads((SLATE_DATA / "matches.json").read_text())
        cls.preds_doc = json.loads((SLATE_DATA / "predictions.json").read_text())
        cls.flags_doc = json.loads((SLATE_DATA / "flagged.json").read_text())
        cls.audit_doc = json.loads((SLATE_DATA / "repo_audit.json").read_text())

    def test_01_all_17_eligible_sports_and_zero_excluded_sports(self) -> None:
        eligible = {s["slug"] for s in self.seed["eligible_sports"]}
        self.assertEqual(len(eligible), 17)
        self.assertTrue(eligible.isdisjoint(EXCLUDED_SLUGS))
        for m in self.matches_doc["matches"]:
            self.assertNotIn(m["sport"].lower(), EXCLUDED_SLUGS)
            self.assertIn(m["sport"], eligible)
        for u in self.matches_doc["unlined_fixtures"]:
            self.assertNotIn(u["sport"].lower(), EXCLUDED_SLUGS)
            self.assertIn(u["sport"], eligible)

    def test_02_multi_market_mathematical_coherence(self) -> None:
        matches = self.matches_doc["matches"]
        self.assertGreaterEqual(len(matches), 120)
        for m in matches:
            self.assertGreaterEqual(len(m["markets"]), 2, m["id"])
            self.assertIn(m["confidence"], {"low", "medium", "high"})
            self.assertTrue(m["official_url"].startswith("https://"), m["id"])
            for mkt in m["markets"]:
                psum = sum(o["fair_prob"] for o in mkt["outcomes"])
                self.assertAlmostEqual(psum, 1.0, delta=0.005, msg=f"{m['id']} {mkt['market']}")
                self.assertGreaterEqual(mkt["overround_pct"], 1.0)
                self.assertLessEqual(mkt["overround_pct"], 10.0)
                for o in mkt["outcomes"]:
                    self.assertLessEqual(o["book_dec"], o["fair_dec"] + 0.01)

    def test_03_danny_noppert_vs_ritchie_edhouse_fix_applied(self) -> None:
        by_id = {m["id"]: m for m in self.matches_doc["matches"]}
        tie = by_id["pdc-32330"]
        self.assertEqual(tie["home"], "Danny Noppert")
        self.assertEqual(tie["away"], "Ritchie Edhouse")
        self.assertIn("SL-01", tie["flags"])

    def test_04_high_confidence_predictions_human_and_odds_band(self) -> None:
        preds = self.preds_doc["predictions"]
        self.assertGreaterEqual(len(preds), 30)
        openings: set[str] = set()
        sports_covered: set[str] = set()
        for p in preds:
            words = p["analysis"].split()
            self.assertGreaterEqual(len(words), 30, p["match_id"])
            self.assertEqual(len(words), p["word_count"])
            self.assertGreaterEqual(p["book_am_int"], -250, p["match_id"])
            self.assertLessEqual(p["book_am_int"], 10000, p["match_id"])
            h, a = p["matchup"].split(" vs ")
            self.assertIn(h.split()[-1].lower(), p["analysis"].lower(), p["match_id"])
            self.assertIn(a.split()[-1].lower(), p["analysis"].lower(), p["match_id"])
            op = " ".join(words[:4]).lower()
            self.assertNotIn(op, openings, f"Duplicate opening phrase: {op}")
            openings.add(op)
            sports_covered.add(p["sport"])
        self.assertGreaterEqual(len(sports_covered), 12)

    def test_05_every_html_page_table_row_has_official_https_link_and_zero_broken_links(self) -> None:
        html_files = sorted(SLATE_HTML.rglob("*.html"))
        self.assertEqual(len(html_files), 26)
        parsed: dict[pathlib.Path, LinkAndRowParser] = {}
        for f in html_files:
            parser = LinkAndRowParser()
            parser.feed(f.read_text())
            parsed[f.resolve()] = parser
            self.assertGreater(len(parser.tbody_row_https_counts), 0, f"No table rows on {f}")
            for idx, cnt in enumerate(parser.tbody_row_https_counts):
                self.assertGreaterEqual(cnt, 1, f"Row {idx} in {f} lacks an official https:// link")

        for src_file, parser in parsed.items():
            for href in parser.links:
                if href.startswith(("https://", "http://", "mailto:")):
                    continue
                path_part, _, frag = href.partition("#")
                target = (src_file.parent / path_part).resolve() if path_part else src_file
                self.assertTrue(target.exists(), f"Broken relative link {href} in {src_file}")
                if frag and target in parsed:
                    self.assertIn(frag, parsed[target].ids, f"Missing anchor #{frag} in {target} (from {src_file})")

    def test_06_deterministic_rebuild_matches_committed_files(self) -> None:
        import subprocess
        import sys

        tracked = [
            SLATE_DATA / "inputs.json",
            SLATE_DATA / "matches.json",
            SLATE_DATA / "predictions.json",
            SLATE_DATA / "flagged.json",
            SLATE_HTML / "index.html",
            SLATE_HTML / "matches.html",
            SLATE_HTML / "picks.html",
            SLATE_HTML / "flagged.html",
        ]
        before = {p: p.read_bytes() for p in tracked}
        for script in ("slate_seed.py", "slate_model.py", "slate_build.py"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True)
        after = {p: p.read_bytes() for p in tracked}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
