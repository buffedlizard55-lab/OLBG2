"""Tests for the /ledger/ layer (session arena/41b3bae5-olbg2).

These run against the committed artefacts: they are a guard on what is published, not a
re-run of the build. The CI workflow rebuilds the layer and fails on any drift.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ledger"
OUT = ROOT / "ledger"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class LedgerData(unittest.TestCase):
    def test_all_data_files_parse(self):
        for name in ("olbg.json", "official.json", "matches.json", "lines.json", "picks.json",
                     "predictions.json", "flagged.json", "sources.json", "repo_review.json",
                     "verify.json", "manifest.json"):
            self.assertIsInstance(load(name), dict, name)

    def test_capture_bodies_match_manifest_hashes(self):
        manifest = load("manifest.json")
        checked = 0
        for c in manifest["captures"]:
            if c.get("status") != 200:
                continue
            body = (DATA / c["stored_as"]).read_bytes()
            self.assertEqual(hashlib.sha256(body).hexdigest(), c["sha256"], c["key"])
            checked += 1
        self.assertGreater(checked, 50)

    def test_every_olbg_row_links_its_listing(self):
        for tip in load("olbg.json")["tips"]:
            self.assertTrue(tip["event_url"].startswith("https://www.olbg.com"), tip["event"])

    def test_matched_rows_carry_an_official_source(self):
        for ev in load("matches.json")["events"]:
            if ev["verify"]["state"] == "unmatched":
                continue
            self.assertTrue(ev["verify"]["official_url"].startswith("http"), ev["event"])
            self.assertTrue(ev["verify"]["captured_at"], ev["event"])

    def test_scope_is_exactly_the_fifteen_sports(self):
        events = load("matches.json")["events"]
        self.assertTrue(events)
        self.assertTrue({e["sport"] for e in events} <= set(SPORTS))


class LedgerPricing(unittest.TestCase):
    def test_every_selection_states_a_basis_and_a_price(self):
        for p in load("picks.json")["picks"]:
            self.assertIn(p["basis"], ("originated", "market-implied"))
            self.assertGreater(p["prob"], 0)
            self.assertLess(p["prob"], 1)
            self.assertTrue(p["american"])

    def test_band_flag_follows_the_american_price(self):
        for p in load("picks.json")["picks"]:
            try:
                a = int(p["american"])
            except (TypeError, ValueError):
                continue
            self.assertEqual(p["in_band"], -250 <= a <= 10000, p["id"])

    def test_confidence_follows_the_probability(self):
        for p in load("picks.json")["picks"]:
            expected = "high" if p["prob"] >= 0.70 else ("medium" if p["prob"] >= 0.60 else "low")
            self.assertEqual(p["confidence"], expected, p["id"])

    def test_no_bookmaker_price_is_published_as_ours(self):
        for p in load("picks.json")["picks"]:
            if p["basis"] == "originated":
                self.assertTrue(p["official_url"].startswith("http"), p["id"])

    def test_model_probabilities_sum_to_one_per_two_way_market(self):
        for f in load("lines.json")["fixtures"]:
            win = f["markets"]["win"]
            self.assertAlmostEqual(win[0]["prob"] + win[1]["prob"], 1.0, places=3, msg=f["fixture_id"])


class LedgerProse(unittest.TestCase):
    def test_every_preview_is_at_least_thirty_words(self):
        for p in load("predictions.json")["predictions"]:
            self.assertGreaterEqual(p["words"], 30, p["id"])
            self.assertGreaterEqual(len(p["text"].split()), 30, p["id"])

    def test_forbidden_words_do_not_appear(self):
        for p in load("predictions.json")["predictions"]:
            for word in ("model", "verified"):
                self.assertIsNone(re.search(rf"\b{word}\b", p["text"].lower()), f"{p['id']} contains {word}")

    def test_previews_are_unique(self):
        texts = [p["text"] for p in load("predictions.json")["predictions"]]
        self.assertEqual(len(texts), len(set(texts)))
        openings = [" ".join(t.split()[:6]).lower() for t in texts]
        self.assertEqual(len(openings), len(set(openings)))

    def test_every_preview_names_its_selection_and_cites_two_facts(self):
        for p in load("predictions.json")["predictions"]:
            sticky = [w for w in re.findall(r"[a-z]+", p["selection"].lower()) if len(w) >= 4]
            self.assertTrue(any(w in p["text"].lower() for w in sticky), p["id"])
            self.assertGreaterEqual(len(p["facts"]), 2, p["id"])
            self.assertTrue(p["prediction_source"].startswith("http"), p["id"])


class LedgerSite(unittest.TestCase):
    def test_all_pages_exist_and_link_home(self):
        pages = sorted(OUT.rglob("*.html"))
        self.assertGreaterEqual(len(pages), 25)
        for page in pages:
            self.assertIn("OLBG2", page.read_text(encoding="utf-8"))
            self.assertIn("index.html", page.read_text(encoding="utf-8"), page.name)

    def test_every_sport_has_a_page(self):
        for s in SPORTS:
            self.assertTrue((OUT / "sports" / (s.lower().replace(" ", "-") + ".html")).exists(), s)

    def test_internal_links_resolve(self):
        broken = []
        for page in OUT.rglob("*.html"):
            for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
                if href.startswith(("http", "mailto:", "#")):
                    continue
                target = (page.parent / href.split("#")[0]).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    broken.append(f"{page.relative_to(ROOT)} -> {href}")
        self.assertEqual(broken, [])

    def test_published_counts_match_the_data(self):
        picks = load("picks.json")
        self.assertEqual(picks["meta"]["selections"], len(picks["picks"]))
        high = [p for p in picks["picks"] if p["confidence"] == "high"]
        self.assertEqual(picks["meta"]["high"], len(high))
        self.assertEqual(picks["meta"]["high_in_band"], len([p for p in high if p["in_band"]]))

    def test_self_audit_passed(self):
        report = load("verify.json")
        self.assertEqual(report["failed"], 0, report["failures"])


class LedgerWorkflow(unittest.TestCase):
    def test_capture_workflow_commits_back_to_the_branch(self):
        wf = (ROOT / ".github" / "workflows" / "ledger-capture.yml").read_text(encoding="utf-8")
        self.assertIn("contents: write", wf)
        self.assertIn("git push", wf)
        self.assertIn("scripts/ledger_capture.py", wf)

    def test_pages_workflow_rebuilds_the_layer(self):
        wf = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/ledger_build.py", wf)
        self.assertIn("ledger data/ledger", wf)


if __name__ == "__main__":
    unittest.main()
