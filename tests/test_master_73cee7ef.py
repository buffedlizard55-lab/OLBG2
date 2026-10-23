"""Tests for the consolidated 15-sport desk (session arena/73cee7ef-olbg2).

The structural checks live in scripts/master_verify.py.  These tests cover the rules
that a structural pass cannot see: the maths behind a price, the grade boundaries,
the price window, the prediction gates, and the promise that a started match is
never published as an upcoming pick.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "master"
OUT = ROOT / "master"

SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
    "Ice Hockey", "Basketball", "Rugby League",
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class MasterDeskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")["matches"]
        cls.picks = load("picks.json")["picks"]
        cls.predictions = load("predictions.json")["predictions"]
        cls.summary = load("summary.json")
        cls.flagged = load("flagged.json")["items"]

    def test_all_fifteen_sports_are_present_in_the_scope(self):
        meta = load("matches.json")["meta"]
        self.assertEqual(sorted(meta["scope"]), sorted(SPORTS))
        self.assertEqual(len(SPORTS), 15)

    def test_no_out_of_scope_sport_leaks_into_the_desk(self):
        for m in self.matches:
            self.assertIn(m["sport"], SPORTS, m["id"])
        for p in self.picks:
            self.assertIn(p["sport"], SPORTS, p["id"])

    def test_fair_price_recomputes_from_probability(self):
        for p in self.picks:
            prob = p["prob"]
            expected = -round(100 * prob / (1 - prob)) if prob >= 0.5 else round(100 * (1 - prob) / prob)
            self.assertLessEqual(
                abs(expected - p["fair_american"]), max(2, abs(expected) * 0.02),
                f'{p["id"]} price {p["fair_american"]} vs {expected}',
            )

    def test_confidence_matches_probability(self):
        for p in self.picks:
            want = "high" if p["prob"] >= 0.70 else ("medium" if p["prob"] >= 0.60 else "low")
            self.assertEqual(p["confidence"], want, p["id"])

    def test_price_window_flag_matches_price(self):
        for p in self.picks:
            self.assertEqual(p["in_band"], -250 <= p["fair_american"] <= 10000, p["id"])

    def test_started_matches_never_carry_a_pick(self):
        for m in self.matches:
            if m.get("started"):
                self.assertIsNone(m.get("pick"), m["id"])

    def test_every_pick_has_a_source(self):
        for p in self.picks:
            self.assertTrue(p["official_url"] or p["olbg_url"], p["id"])

    def test_originated_picks_have_official_records(self):
        by_id = {m["id"]: m for m in self.matches}
        for p in self.picks:
            if p["basis"] == "originated":
                self.assertTrue(by_id[p["match_id"]].get("records"), p["id"])

    def test_predictions_are_at_least_thirty_words(self):
        for pred in self.predictions:
            self.assertGreaterEqual(len(pred["text"].split()), 30, pred["id"])

    def test_predictions_avoid_the_banned_words(self):
        for pred in self.predictions:
            for word in ("model", "verified"):
                self.assertIsNone(
                    re.search(rf"\b{word}\b", pred["text"], re.I), f'{pred["id"]} uses {word}'
                )

    def test_prediction_openings_are_unique(self):
        openings = [" ".join(p["text"].split()[:4]).lower() for p in self.predictions]
        self.assertEqual(len(openings), len(set(openings)))

    def test_predictions_only_cover_high_confidence_picks(self):
        picks = {(p["match_id"], p["selection"]) for p in self.picks if p["confidence"] == "high"}
        for pred in self.predictions:
            self.assertIn((pred["match_id"], pred["selection"]), picks, pred["id"])

    def test_every_prediction_names_its_selection(self):
        for pred in self.predictions:
            words = re.findall(r"[A-Za-z]{4,}", pred["selection"])
            self.assertTrue(any(w.lower() in pred["text"].lower() for w in words), pred["id"])

    def test_prediction_figures_exist_in_the_stored_record(self):
        by_id = {m["id"]: m for m in self.matches}
        for pred in self.predictions:
            record = by_id[pred["match_id"]].get("records") or {}
            flattened = json.dumps(record)
            for figure in re.findall(r"\d+(?:\.\d+)?", " ".join(pred["facts"])):
                self.assertIn(figure, flattened, f'{pred["id"]} cites {figure} not in the record')

    def test_summary_counts_are_derived_not_typed(self):
        self.assertEqual(self.summary["matches"], len(self.matches))
        self.assertEqual(self.summary["picks"], len(self.picks))
        self.assertEqual(self.summary["high"], sum(1 for p in self.picks if p["confidence"] == "high"))
        self.assertEqual(
            self.summary["high_in_band"],
            sum(1 for p in self.picks if p["confidence"] == "high" and p["in_band"]),
        )

    def test_every_flagged_item_links_a_source(self):
        for item in self.flagged:
            self.assertTrue(item.get("sources"), item["id"])
            for url in item["sources"]:
                self.assertTrue(url.startswith("https://"), (item["id"], url))

    def test_capture_audit_counts_are_internally_consistent(self):
        audit = load("capture_audit.json")
        failed = [c for c in audit["captures"] if c["verdict"] in ("http error", "error page", "no status")]
        self.assertEqual(audit["meta"]["failed"], len(failed))
        self.assertEqual(audit["meta"]["captures"], len(audit["captures"]))
        for c in failed:
            self.assertTrue(c["url"].startswith("https://"), c["key"])

    def test_published_pages_exist_for_every_sport(self):
        for sport in SPORTS:
            slug = sport.lower().replace(" ", "-")
            self.assertTrue((OUT / "sports" / f"{slug}.html").exists(), slug)

    def test_root_landing_points_at_the_desk(self):
        root = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("master/index.html", root)
        self.assertIn("Consolidated desk", root)


    def test_every_sport_has_at_least_one_row(self):
        seen = {m["sport"] for m in self.matches}
        missing = [s for s in SPORTS if s not in seen]
        self.assertEqual(missing, [], f"sports with no row: {missing}")

    def test_golf_and_snooker_rows_carry_a_first_hand_https_source(self):
        for sport in ("Golf", "Snooker"):
            rows = [m for m in self.matches if m["sport"] == sport]
            self.assertTrue(rows, sport)
            for m in rows:
                self.assertTrue(m["official_url"].startswith("https://"), m["id"])
                self.assertTrue(m["official_captured_at"].endswith("Z"), m["id"])

    def test_five_per_sport_card_respects_the_ceiling(self):
        board = load("top5.json")["board"]
        meta = load("top5.json")["meta"]
        self.assertEqual(meta["limit"], 5)
        for sport, entry in board.items():
            self.assertLessEqual(len(entry["featured"]), 5, sport)
            self.assertLessEqual(len(entry["featured"]), entry["high_available"], sport)
            for f in entry["featured"]:
                self.assertTrue((f["official_url"] or f["olbg_url"]).startswith("https://"), f["pick_id"])

    def test_featured_selections_are_high_confidence_picks(self):
        picks = {p["id"]: p for p in self.picks}
        for entry in load("top5.json")["board"].values():
            for f in entry["featured"]:
                self.assertEqual(picks[f["pick_id"]]["confidence"], "high", f["pick_id"])

    def test_new_capture_flags_are_published_with_sources(self):
        ids = {f["id"]: f for f in self.flagged}
        for fid in ("MR-17", "MR-18", "MR-19"):
            self.assertIn(fid, ids)
            self.assertTrue(ids[fid]["sources"])
            for url in ids[fid]["sources"]:
                self.assertTrue(url.startswith("https://"), fid)

    def test_golf_prices_are_labelled_market_implied(self):
        for p in self.picks:
            if p["sport"] == "Golf":
                self.assertEqual(p["basis"], "market-implied", p["id"])

    def test_snooker_price_is_our_own_and_is_not_high(self):
        rows = [p for p in self.picks if p["sport"] == "Snooker"]
        self.assertTrue(rows)
        for p in rows:
            self.assertEqual(p["basis"], "originated", p["id"])
            self.assertNotEqual(p["confidence"], "high", f'{p["id"]} claims a 70% floor it cannot support')

    def test_root_landing_links_the_desk_without_merging_the_counts(self):
        root = (ROOT / "index.html").read_text(encoding="utf-8")
        for href in ("master/index.html", "master/top5.html"):
            self.assertIn(href, root)
        # the root desk is a different layer; it must say so rather than folding these rows in
        self.assertIn("separate layer with its own counts", root)

    def test_methodology_states_the_five_per_sport_ceiling(self):
        page = (OUT / "methodology.html").read_text(encoding="utf-8")
        self.assertIn("Five per sport, as a ceiling", page)
        self.assertIn("never padded", page)

    def test_no_prediction_claims_an_injury(self):
        for pred in self.predictions:
            for word in ("injur", "hamstring", "suspended", "ruled out"):
                self.assertNotIn(word, pred["text"].lower(), pred["id"])


if __name__ == "__main__":
    unittest.main()
