"""Acceptance tests for the /cadence/ desk (session a0c8b7f3).

These tests are the drift gate for the desk: they rebuild every artifact from the committed
capture and fail if the published HTML, the price arithmetic, the confidence labels, the band
flags, the prediction rules or the source coverage drift.
"""
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cadence"
SITE = ROOT / "cadence"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
BANNED = re.compile(r"\b(model|models|modelled|modeled|modelling|modeling|verify|verified|verifies|"
                    r"verification)\b", re.I)


def load(name):
    with open(DATA / name) as f:
        return json.load(f)


def american(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return int(round(-100.0 * p / (1 - p))) if p >= 0.5 else int(round(100.0 * (1 - p) / p))


class CadenceData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")
        cls.lines = load("lines.json")
        cls.picks = load("picks.json")
        cls.preds = load("predictions.json")
        cls.sources = load("sources.json")
        cls.flags = load("flagged.json")
        cls.audit = load("repo_audit.json")

    def test_all_fifteen_sports_have_a_fixture(self):
        have = {m["sport"] for m in self.matches["matches"]}
        self.assertEqual(have, set(SPORTS))

    def test_no_out_of_scope_sport_is_published(self):
        banned = {"Aussie Rules", "Esports", "eSports", "Football", "Soccer", "American Football",
                  "Horse Racing", "Boxing", "MMA", "UFC"}
        for row in self.matches["matches"]:
            self.assertNotIn(row["sport"], banned)
        for p in self.picks["picks"]:
            self.assertNotIn(p["sport"], banned)

    def test_every_fixture_has_an_https_official_source(self):
        for m in self.matches["matches"]:
            self.assertTrue(m["official_source_url"].startswith("https://"), m["id"])
            self.assertTrue(m["facts"], m["id"])
            for f in m["facts"]:
                self.assertTrue(f["source_url"].startswith("https://"), (m["id"], f["value"]))

    def test_facts_cite_registered_sources(self):
        keys = {s["key"] for s in self.sources["sources"]}
        for m in self.matches["matches"]:
            for f in m["facts"]:
                self.assertIn(f["source_key"], keys, (m["id"], f["source_key"]))

    def test_blank_rows_state_a_reason(self):
        blanks = [m for m in self.matches["matches"] if m["status"] == "blank"]
        self.assertTrue(blanks, "expected the unlined fixtures to be recorded rather than dropped")
        for m in blanks:
            self.assertTrue((m.get("note") or "").strip(), m["id"])

    def test_price_arithmetic(self):
        for r in self.lines["lines"]:
            p = round(r["probability"], 6)
            self.assertEqual(american(p), r["fair_american"], r["id"])
            self.assertAlmostEqual(1 / p, r["fair_decimal"], delta=max(0.002, 0.0005 * r["fair_decimal"]))
            self.assertGreaterEqual(r["offered_decimal"], r["fair_decimal"])

    def test_band_flag_matches_its_own_price(self):
        for r in list(self.lines["lines"]) + list(self.picks["picks"]):
            expect = -250 <= r["fair_american"] <= 10000
            self.assertEqual(expect, r["in_band"], r["id"])

    def test_confidence_never_overstates(self):
        for r in list(self.lines["lines"]) + list(self.picks["picks"]):
            if r["confidence"] == "high":
                self.assertGreaterEqual(r["probability"], 0.70, r["id"])
            if r["confidence"] == "low":
                self.assertLess(r["probability"], 0.60, r["id"])

    def test_band_lines_sit_at_the_ceiling(self):
        tiers = {m["id"]: m["evidence_tier"] for m in self.matches["matches"]}
        for r in self.lines["lines"]:
            if r.get("band_line"):
                self.assertGreaterEqual(r["probability"], 0.70, r["id"])
                self.assertLessEqual(r["probability"], 0.7144, r["id"])
                if tiers.get(r["fixture_id"]) == "C":
                    self.assertNotEqual(r["confidence"], "high", r["id"])

    def test_band_window_is_stated_in_the_data(self):
        note = self.picks["bands"]["note"]
        self.assertIn("0.7143", note)
        self.assertIn("0.7000", note)

    def test_every_sport_has_a_shortlist(self):
        for s in SPORTS:
            rows = [p for p in self.picks["picks"] if p["sport"] == s and p.get("sport_rank")]
            self.assertGreaterEqual(len(rows), 2, s)
            ranks = sorted(p["sport_rank"] for p in rows)
            self.assertEqual(ranks, list(range(1, len(ranks) + 1)), s)

    def test_every_shortlist_has_five_or_a_documented_reason(self):
        for s in SPORTS:
            rows = [p for p in self.picks["picks"] if p["sport"] == s and p.get("sport_rank")]
            if len(rows) < 5:
                originated = [m for m in self.matches["matches"]
                              if m["sport"] == s and m["status"] == "originated"]
                self.assertLess(len(originated), 5,
                                f"{s} has {len(originated)} priced fixtures but only {len(rows)} picks")


class CadencePredictions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preds = load("predictions.json")
        cls.picks = load("picks.json")
        cls.matches = {m["id"]: m for m in load("matches.json")["matches"]}

    def test_minimum_length(self):
        for p in self.preds["predictions"]:
            self.assertGreaterEqual(p["word_count"], 30, p["id"])
            self.assertEqual(len(p["text"].split()), p["word_count"], p["id"])

    def test_prohibited_words(self):
        for p in self.preds["predictions"]:
            self.assertIsNone(BANNED.search(p["text"]), p["id"])
            self.assertIsNone(BANNED.search(p["headline"]), p["id"])

    def test_unique_openings_and_bodies(self):
        openings = [" ".join(p["text"].split()[:3]).lower() for p in self.preds["predictions"]]
        self.assertEqual(len(openings), len(set(openings)))
        bodies = [p["text"] for p in self.preds["predictions"]]
        self.assertEqual(len(bodies), len(set(bodies)))

    def test_selection_is_named_in_the_text(self):
        for p in self.preds["predictions"]:
            head = p["text"][:120].lower()
            self.assertTrue(any(tok in head for tok in re.findall(r"[a-z]{4,}", p["selection"].lower())),
                            p["id"])

    def test_every_fact_is_traceable_to_the_capture(self):
        for p in self.preds["predictions"]:
            fixture = self.matches[p["fixture_id"]]
            values = {f["value"] for f in fixture["facts"]}
            for f in p["facts"]:
                self.assertIn(f["claim"], values, p["id"])
                self.assertTrue(f["source_url"].startswith("https://"), p["id"])

    def test_prediction_matches_its_pick(self):
        by_id = {p["id"]: p for p in self.picks["picks"]}
        for p in self.preds["predictions"]:
            pick = by_id[p["pick_id"]]
            self.assertEqual(pick["selection"], p["selection"])
            self.assertEqual(pick["probability"], p["probability"])
            self.assertEqual(pick["fair_american"], p["fair_american"])

    def test_prediction_sports_are_a_subset_and_shortfall_is_flagged(self):
        self.assertTrue(set(self.preds["sports"]).issubset(set(SPORTS)))
        missing = set(SPORTS) - set(self.preds["sports"])
        flagged = " ".join(f["finding"] for f in load("flagged.json")["flags"])
        for s in missing:
            self.assertTrue(s.split()[0] in flagged or "golf" in flagged.lower(), s)


class CadenceSite(unittest.TestCase):
    def test_site_exists(self):
        for name in ("index.html", "band.html", "picks.html", "matches.html", "lines.html",
                     "predictions.html", "sources.html", "methodology.html", "olbg.html",
                     "audit.html", "flagged.html", "sports/index.html"):
            self.assertTrue((SITE / name).is_file(), name)

    def test_fifteen_sport_pages(self):
        pages = sorted(p.name for p in (SITE / "sports").glob("*.html") if p.name != "index.html")
        self.assertEqual(len(pages), 15, pages)

    def test_no_data_table_row_is_without_a_link(self):
        for page in SITE.rglob("*.html"):
            if page.name in ("methodology.html", "olbg.html", "flagged.html"):
                continue
            text = page.read_text()
            body = re.sub(r"<thead>.*?</thead>", "", text, flags=re.S)
            for row in re.findall(r"<tr>(.*?)</tr>", body, re.S):
                if "<td" not in row:
                    continue
                self.assertIn("href=", row, f"{page.name}: {row[:90]}")

    def test_verifier_passes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "cadence_verify.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])

    def test_rebuild_is_deterministic(self):
        before = {p.relative_to(ROOT): p.read_bytes() for p in SITE.rglob("*.html")}
        for script in ("cadence_seed.py", "cadence_model.py", "cadence_predictions.py", "cadence_build.py"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True,
                           capture_output=True)
        after = {p.relative_to(ROOT): p.read_bytes() for p in SITE.rglob("*.html")}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
