"""Tests for the /recheck independent audit desk (session 26707f98, 2026-10-24).

The desk re-derives every rule of the current /now/ front-door desk from the committed
capture, offline. These tests run the strict verifier (which itself rebuilds the data and
pages and fails on any byte of drift), then pin the headline counts and the reader-facing
word rules so a hand edit cannot ship unnoticed.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "recheck"
OUT = ROOT / "recheck"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
PAGES = ["index.html", "picks.html", "predictions.html", "lines.html", "fixtures.html",
         "sources.html", "flagged.html", "methodology.html"]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class RecheckVerifier(unittest.TestCase):
    def test_strict_verifier_passes(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / "recheck_verify.py")],
                             cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_recorded_verdict_is_clean(self):
        doc = load("results.json")
        self.assertEqual(doc["verdict"], "pass")
        self.assertEqual(doc["summary"]["checks_failed"], 0)
        self.assertTrue(all(c["failed"] == 0 for c in doc["checks"]))
        self.assertEqual(len(doc["checks"]), 9)


class RecheckCounts(unittest.TestCase):
    def test_headline_counts_match_the_now_desk(self):
        doc = load("results.json")
        s = doc["summary"]
        self.assertEqual((s["fixtures"], s["matches"], s["lines"]), (50, 50, 866))
        self.assertEqual((s["picks"], s["predictions"], s["olbg_listings"]), (39, 39, 96))
        self.assertEqual(s["high_picks"] + s["medium_picks"] + s["low_picks"], 39)
        self.assertEqual(len(doc["pick_rows"]), 39)
        self.assertEqual(len(doc["pred_rows"]), s["predictions"])
        self.assertEqual(len(doc["fixture_rows"]), 50)
        self.assertEqual(doc["line_check"]["total"], 866)
        self.assertEqual(len(doc["line_check"]["failures"]), 0)

    def test_grade_and_score_rederivations_agree(self):
        doc = load("results.json")
        for row in doc["pick_rows"]:
            self.assertEqual(row["verdict"], "pass", row["id"])
            self.assertEqual(row["published_grade"], row["rederived_grade"], row["id"])
            self.assertEqual(float(row["published_score"]),
                             float(row["rederived_score"]), row["id"])
            self.assertTrue(row["in_band"], row["id"])

    def test_observations_are_the_documented_three(self):
        doc = load("results.json")
        self.assertEqual(len(doc["observations"]), 3)
        ids = {o["id"] for o in doc["observations"]}
        self.assertEqual(ids, {"O-mlb-tb-mil-g3-olbg-url",
                               "O-cri-bol-tit-olbg-url",
                               "O-cri-tus-cob-olbg-url"})
        for o in doc["observations"]:
            self.assertTrue(o["official_url"].startswith("https://"))


class RecheckSite(unittest.TestCase):
    def test_page_set_and_stylesheet(self):
        self.assertEqual(sorted(p.name for p in OUT.glob("*.html")), sorted(PAGES))
        self.assertTrue((OUT / "assets" / "style.css").is_file())

    def test_reader_facing_word_rules_and_brand(self):
        for name in PAGES:
            text = (OUT / name).read_text(encoding="utf-8")
            self.assertIn("OLBG2", text, name)
            self.assertNotRegex(text, BANNED, name)
            self.assertIn("../index.html", text, name)

    def test_no_broken_local_links(self):
        from urllib.parse import unquote
        broken = []
        for page in OUT.rglob("*.html"):
            for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
                if href.startswith(("http", "mailto:", "#", "data:")):
                    continue
                target = (page.parent / unquote(href.split("#")[0])).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    broken.append(f"{page.relative_to(ROOT)} -> {href}")
        self.assertEqual(broken, [])

    def test_every_entity_row_carries_an_https_source(self):
        for name in ("picks.html", "predictions.html", "fixtures.html", "sources.html"):
            body = (OUT / name).read_text(encoding="utf-8")
            bodies = re.findall(r"<tbody>(.*?)</tbody>", body, flags=re.S)
            rows = [r for section in bodies for r in re.findall(r"<tr>.*?</tr>", section, flags=re.S)]
            self.assertTrue(rows, name)
            self.assertTrue(all("https://" in r for r in rows), name)


if __name__ == "__main__":
    unittest.main()
