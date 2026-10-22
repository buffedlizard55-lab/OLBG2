"""Forward-slate layer tests (data/forward + scripts/forward_* + forward/).

Everything here is read-only against generated artefacts — the pipeline is
deterministic, so the published files must always match what the scripts
produce from the captures, and every market must respect the uniform
high-confidence gate.
"""
from __future__ import annotations

import html
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import forward_model as fm  # noqa: E402

FWD = ROOT / "data" / "forward"
SITE = ROOT / "forward"

WINDOW_START = "2026-10-23"
WINDOW_END = "2026-11-02"


def load(name: str) -> dict:
    return json.loads((FWD / name).read_text(encoding="utf-8"))


class ForwardPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load("inputs.json")
        cls.matches = load("matches.json")
        cls.preds = load("predictions.json")
        cls.flags = load("flagged.json")
        cls.rows = cls.matches["matches"]
        cls.by_id = {r["id"]: r for r in cls.rows}

    # ---- slate composition -------------------------------------------------
    def test_slate_counts(self):
        c = self.matches["counts"]
        self.assertEqual(c["total"], 93)
        self.assertEqual(c["nhl"], 70)
        self.assertEqual(c["mlb"], 7)
        self.assertEqual(c["eurocup"], 16)
        self.assertEqual(c["originated"], 77)
        self.assertEqual(c["unlined"], 16)
        self.assertEqual(len(self.rows), 93)
        self.assertEqual(len(self.by_id), 93, "row ids must be unique")

    def test_all_rows_inside_forward_window(self):
        for r in self.rows:
            self.assertGreaterEqual(r["date"], WINDOW_START, r["id"])
            self.assertLessEqual(r["date"], WINDOW_END, r["id"])

    def test_vf15_world_series_g4_is_originated(self):
        g4 = self.by_id["mlb-ws-g4"]
        self.assertEqual(g4["line_status"], "originated")
        self.assertIn("Game 4", g4["competition"])
        self.assertEqual(g4["date"], "2026-10-27")
        self.assertEqual(g4["home"], "Tampa Bay Rays")
        self.assertEqual(g4["away"], "Milwaukee Brewers")
        self.assertIsNotNone(g4["winner_market"])

    def test_mlb_if_necessary_games_are_marked(self):
        for gid in ("mlb-ws-g5", "mlb-ws-g6", "mlb-ws-g7"):
            self.assertIn("if necessary", self.by_id[gid]["competition"], gid)

    def test_vf20_eurocup_round5_unlined(self):
        euro = [r for r in self.rows if r["sport"] == "basketball"]
        self.assertEqual(len(euro), 16)
        for r in euro:
            self.assertEqual(r["line_status"], "unlined")
            self.assertIsNone(r["winner_market"])
            self.assertIsNone(r["pick"])
            self.assertTrue(r["blank_reason"])
            self.assertIn("never infers", r["blank_reason"])

    # ---- market integrity -------------------------------------------------
    def test_originated_rows_have_consistent_markets(self):
        for r in self.rows:
            if r["line_status"] != "originated":
                continue
            wm, hm, tm = r["winner_market"], r["handicap_market"], r["total_market"]
            self.assertAlmostEqual(wm["home_prob"] + wm["away_prob"], 1.0, places=3, msg=r["id"])
            self.assertAlmostEqual(hm["fav_prob"] + hm["dog_prob"], 1.0, places=3, msg=r["id"])
            self.assertAlmostEqual(tm["over_prob"] + tm["under_prob"], 1.0, places=3, msg=r["id"])
            for p, o in (
                (wm["home_prob"], wm["home_odds"]),
                (wm["away_prob"], wm["away_odds"]),
                (hm["fav_prob"], hm["fav_odds"]),
                (hm["dog_prob"], hm["dog_odds"]),
                (tm["over_prob"], tm["over_odds"]),
                (tm["under_prob"], tm["under_odds"]),
            ):
                # odds are computed from the unrounded probability; the published
                # probability is rounded to 4dp, so allow one cent of drift.
                self.assertAlmostEqual(o, round(max(1.02, 1.0 / p), 2), delta=0.011, msg=r["id"])
            self.assertIn(r["pick"]["confidence"], {"low", "medium", "high"})
            self.assertAlmostEqual(
                r["pick"]["fair_american"],
                fm.fair_american(r["pick"]["probability"]),
                delta=1,
                msg=r["id"],
            )

    def test_no_bookmaker_language_in_rows(self):
        blob = json.dumps(self.matches).lower()
        for phrase in ("best odds", "oddschecker", "tipster consensus", "paddy power", "bet365"):
            self.assertNotIn(phrase, blob)

    # ---- uniform high-confidence gate -------------------------------------
    def test_band_picks_respect_uniform_gate(self):
        band = [r for r in self.rows if r.get("band_pick")]
        self.assertEqual(len(band), 8)
        for r in band:
            feat = r["featured"]
            self.assertGreaterEqual(feat["probability"], fm.FEATURED_MIN_PROB, r["id"])
            self.assertGreaterEqual(feat["fair_american"], fm.AMERICAN_MIN, r["id"])
            self.assertLessEqual(feat["fair_american"], fm.AMERICAN_MAX, r["id"])
            self.assertEqual(feat["confidence"], "high")
            self.assertEqual(r["band_pick"]["price_band"], "in-band")

    def test_picks_never_label_high_outside_the_gate(self):
        for r in self.rows:
            if not r.get("pick"):
                continue
            p = r["pick"]
            if p["confidence"] == "high":
                self.assertGreaterEqual(p["probability"], fm.HIGH_THRESHOLD, r["id"])

    # ---- predictions ------------------------------------------------------
    def test_prediction_language_rules(self):
        self.assertEqual(self.preds["count"], 8)
        self.assertEqual(len(self.preds["predictions"]), 8)
        texts = set()
        for p in self.preds["predictions"]:
            self.assertGreaterEqual(p["word_count"], 30, p["match_id"])
            self.assertEqual(p["word_count"], len(p["text"].split()), p["match_id"])
            self.assertGreaterEqual(len(p["text"].split()), 30, p["match_id"])
            self.assertNotIn(p["text"], texts, "prediction texts must be unique")
            texts.add(p["text"])
            self.assertIn(p["selection"], p["text"], p["match_id"])
            self.assertTrue(p["facts"], p["match_id"])
            self.assertGreaterEqual(p["probability"], fm.FEATURED_MIN_PROB, p["match_id"])
            self.assertGreaterEqual(p["fair_american"], fm.AMERICAN_MIN, p["match_id"])
            self.assertLessEqual(p["fair_american"], fm.AMERICAN_MAX, p["match_id"])

    def test_every_band_pick_has_a_prediction_and_vice_versa(self):
        band_ids = {r["id"] for r in self.rows if r.get("band_pick")}
        pred_ids = {p["match_id"] for p in self.preds["predictions"]}
        self.assertEqual(band_ids, pred_ids)

    def test_prediction_facts_are_sourced(self):
        url_re = re.compile(r"^https://")
        for p in self.preds["predictions"]:
            for f in p["facts"]:
                self.assertRegex(f["source"], url_re, p["match_id"])
                self.assertTrue(f["claim"], p["match_id"])

    # ---- gap flags --------------------------------------------------------
    def test_gap_flags_cover_named_items(self):
        ids = {it["id"] for it in self.flags["items"]}
        self.assertEqual(ids, {"VF-14", "VF-15", "VF-20", "VF-22", "VF-WINDOW"})
        by_id = {it["id"]: it for it in self.flags["items"]}
        self.assertIn("closed", by_id["VF-15"]["status"])
        self.assertIn("closed", by_id["VF-20"]["status"])
        self.assertIn("BLOCKED", by_id["VF-22"]["status"])
        self.assertIn("PARTIAL", by_id["VF-14"]["status"])

    # ---- determinism ------------------------------------------------------
    def test_published_matches_match_script_output(self):
        regen_nhl = fm.originate_nhl(self.inputs)
        regen_mlb = fm.originate_mlb(self.inputs)
        regen_ec = fm.eurocup_unlined(self.inputs)
        regen = regen_nhl + regen_mlb + regen_ec
        self.assertEqual(len(regen), len(self.rows))
        for new, old in zip(regen, self.rows):
            clean = {k: v for k, v in new.items() if not k.startswith("_")}
            if clean["line_status"] == "originated":
                feat = fm.featured_selection(new)
                clean["featured"] = feat
                clean["band_pick"] = fm._band_pick(feat) if feat else None
            self.assertEqual(clean, old, new["id"])

    # ---- site layer -------------------------------------------------------
    def test_site_pages_exist_and_reference_every_row(self):
        matches_html = (SITE / "matches.html").read_text(encoding="utf-8")
        for r in self.rows:
            self.assertIn(html.escape(r["home"]), matches_html, r["id"])
            self.assertIn(html.escape(r["away"]), matches_html, r["id"])
        for name in ("index.html", "picks.html", "gaps.html", "assets/style.css"):
            self.assertTrue((SITE / name).is_file(), name)

    def test_picks_page_embeds_every_writeup(self):
        picks_html = (SITE / "picks.html").read_text(encoding="utf-8")
        for p in self.preds["predictions"]:
            self.assertIn(html.escape(p["text"]), picks_html, p["match_id"])


if __name__ == "__main__":
    unittest.main()
