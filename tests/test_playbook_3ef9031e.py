"""Tests for the /playbook/ desk (session arena/3ef9031e-olbg2).

Runs against the committed artefacts and re-runs each generator to prove the layer is
deterministic. Picked up by `python -m unittest discover -s tests`.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "playbook"
OUT = ROOT / "playbook"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
SLUGS = ["golf", "volleyball", "rugby-union", "cricket", "snooker", "darts", "baseball",
         "gaelic-sports", "greyhounds", "tennis", "motor-racing", "handball", "ice-hockey",
         "basketball", "rugby-league"]
BANNED = re.compile(r"\b(model|models|modelling|verified|verification|algorithm)\b", re.I)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def module(name):
    spec = importlib.util.spec_from_file_location(f"playbook_{name}", ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PlaybookScope(unittest.TestCase):
    def test_exactly_the_fifteen_requested_sports(self):
        fixtures = load("fixtures.json")["fixtures"]
        self.assertEqual(set(load("fixtures.json")["by_sport"]), set(SPORTS))
        self.assertTrue({f["sport"] for f in fixtures} <= set(SPORTS))

    def test_every_sport_has_a_page(self):
        pages = {p.stem for p in (OUT / "sports").glob("*.html")}
        self.assertEqual(pages, set(SLUGS) | {"index"})

    def test_empty_sports_are_labelled_rather_than_padded(self):
        fixtures = load("fixtures.json")["fixtures"]
        empty = {s for s in SPORTS if not any(f["sport"] == s for f in fixtures)}
        self.assertEqual(empty, {"Golf", "Snooker", "Motor Racing", "Rugby League"})
        for slug in ("golf", "snooker", "motor-racing", "rugby-league"):
            text = (OUT / "sports" / f"{slug}.html").read_text()
            self.assertIn("Nothing to price", text)

    def test_no_fixture_is_invented(self):
        cap = json.loads((DATA / "olbg_capture.json").read_text())
        on_olbg = sum(1 for f in load("fixtures.json")["fixtures"] if f["olbg_event_id"])
        self.assertEqual(on_olbg, len(cap["rows"]))
        self.assertEqual(load("fixtures.json")["match_count"], on_olbg)


class PlaybookSources(unittest.TestCase):
    def test_every_row_carries_a_https_source(self):
        registered = {s["url"] for s in load("sources.json")["sources"]}
        for f in load("fixtures.json")["fixtures"]:
            self.assertTrue(f["source_url"].startswith("https://"), f["fid"])
            self.assertIn(f["source_url"], registered, f["fid"])

    def test_every_pick_links_a_registered_source(self):
        registered = {s["url"] for s in load("sources.json")["sources"]}
        for p in load("picks.json")["picks"]:
            self.assertIn(p["source_url"], registered, p["pick_id"])

    def test_every_preview_fact_has_a_registered_source(self):
        registered = {s["url"] for s in load("sources.json")["sources"]}
        for p in load("predictions.json")["predictions"]:
            self.assertGreaterEqual(len(p["facts"]), 2, p["pid"])
            for fact in p["facts"]:
                self.assertIn(fact["source"], registered, p["pid"])


class PlaybookPricing(unittest.TestCase):
    def test_offered_price_is_never_better_than_fair(self):
        mod = module("playbook_model")
        for line in load("lines.json")["lines"]:
            for s in line["lines"]:
                self.assertLessEqual(s["price"], mod.american(s["probability"]) + 1,
                                     f"{line['event']} {s['selection']}")

    def test_band_flag_is_arithmetic(self):
        for p in load("picks.json")["picks"]:
            self.assertEqual(p["in_band"], -250 <= p["price"] <= 10000, p["pick_id"])

    def test_high_grade_needs_a_shortlisted_chance_and_official_input(self):
        for p in load("picks.json")["picks"]:
            if p["confidence"] == "high":
                self.assertEqual(p["tier"], "A", p["pick_id"])
                self.assertGreaterEqual(p["probability"], 0.65, p["pick_id"])
                self.assertTrue(p["in_band"], p["pick_id"])

    def test_nobody_grades_above_low_on_a_coin_flip(self):
        for p in load("picks.json")["picks"]:
            if p["probability"] < 0.5:
                self.assertEqual(p["confidence"], "low", p["pick_id"])

    def test_pick_cap_and_spread(self):
        picks = load("picks.json")["picks"]
        per = {}
        for p in picks:
            per[p["sport"]] = per.get(p["sport"], 0) + 1
        self.assertTrue(all(n <= 10 for n in per.values()), per)
        self.assertEqual(len(picks), sum(per.values()))
        self.assertGreaterEqual(len(per), 10)

    def test_nhl_lines_are_complementary(self):
        for line in load("lines.json")["lines"]:
            if line["tier"] != "A":
                continue
            for market in ("Puck line 1.5", "Match total 5.5", "Match total 6.5"):
                sides = [s for s in line["lines"] if s["market"] == market]
                if len(sides) == 2:
                    total = sum(s["probability"] for s in sides)
                    self.assertAlmostEqual(total, 1.0, places=3, msg=f"{line['event']} {market}")


class PlaybookProse(unittest.TestCase):
    def test_predictions_are_substantial_and_unique(self):
        preds = load("predictions.json")["predictions"]
        seen = set()
        for p in preds:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["pid"])
            self.assertEqual(len(re.findall(r"[A-Za-z0-9'+.-]+", p["text"])), p["words"], p["pid"])
            self.assertNotIn(p["text"], seen, p["pid"])
            seen.add(p["text"])

    def test_no_banned_vocabulary_in_reader_facing_prose(self):
        for p in load("predictions.json")["predictions"]:
            self.assertIsNone(BANNED.search(p["text"]), p["pid"])

    def test_selection_and_price_are_stated_in_the_copy(self):
        for p in load("predictions.json")["predictions"]:
            self.assertIn(str(p["price"]), p["text"], p["pid"])

    def test_no_two_previews_share_an_eight_word_run(self):
        def runs(text):
            words = re.findall(r"[a-z0-9']+", text.lower())
            return {" ".join(words[i:i + 8]) for i in range(max(0, len(words) - 7))}
        preds = load("predictions.json")["predictions"]
        for i, a in enumerate(preds):
            for b in preds[i + 1:]:
                self.assertFalse(runs(a["text"]) & runs(b["text"]), f"{a['pid']} / {b['pid']}")


class PlaybookPages(unittest.TestCase):
    def test_core_pages_exist_and_link_each_other(self):
        for name in ("index.html", "picks.html", "predictions.html", "matches.html", "lines.html",
                     "sources.html", "flagged.html", "methodology.html", "sports/index.html"):
            self.assertTrue((OUT / name).is_file(), name)

    def test_root_front_door_points_at_the_desk(self):
        front = (ROOT / "index.html").read_text()
        for target in ("playbook/picks.html", "playbook/predictions.html",
                       "playbook/sports/index.html", "playbook/flagged.html"):
            self.assertIn(f'href="{target}"', front)
        self.assertIn("archive.html", front)

    def test_flagged_page_publishes_every_flag(self):
        flags = load("flagged.json")["flags"]
        page = (OUT / "flagged.html").read_text()
        self.assertGreaterEqual(len(flags), 1)
        for f in flags:
            self.assertIn(f["id"], page)
            self.assertIn(f["source"].replace("&", "&amp;"), page)

    def test_no_placeholder_or_local_paths(self):
        for path in list(OUT.rglob("*.html")):
            text = path.read_text()
            self.assertNotIn("/home/", text, str(path))
            self.assertNotIn("TODO", text, str(path))
            self.assertNotIn("<<<<<<<", text, str(path))


class PlaybookDeterminism(unittest.TestCase):
    def test_generators_rerun_without_changing_a_byte(self):
        scripts = ["playbook_seed", "playbook_model", "playbook_predictions", "playbook_build"]
        for script in scripts:
            subprocess.run([sys.executable, str(ROOT / "scripts" / f"{script}.py")],
                           check=True, cwd=ROOT, capture_output=True)
        diff = subprocess.run(["git", "diff", "--name-only", "--", "playbook", "data/playbook"],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(diff.stdout.strip(), "", diff.stdout)

    def test_verifier_passes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "playbook_verify.py")],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
