"""Checks for the /daily-picks/ five-a-sport picks desk (session arena/6b4da610-olbg2)."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "daily-picks"
PAGES = ROOT / "daily-picks"

ALLOWED_SPORTS = {
    "tennis", "golf", "rugby-league", "rugby-union", "cricket", "basketball", "baseball",
    "darts", "snooker", "ice-hockey", "motor-racing", "handball", "volleyball", "greyhounds",
    "gaelic-football", "esports", "aussie-rules",
}
EXCLUDED = {"football", "soccer", "boxing", "ufc", "mma", "american-football", "hurling",
            "horse-racing", "cycling", "specials"}


def load(name):
    return json.loads((DATA / name).read_text())


class DailyDataTests(unittest.TestCase):
    def setUp(self):
        self.matches = load("matches.json")
        self.selections = load("selections.json")["selections"]
        self.picks = load("picks.json")["picks"]
        self.preds = load("predictions.json")["predictions"]
        self.flags = load("flagged.json")

    def test_scope_excludes_the_named_sports(self):
        used = {m["sport"] for m in self.matches["matches"]}
        self.assertTrue(used <= ALLOWED_SPORTS, used - ALLOWED_SPORTS)
        self.assertFalse(used & EXCLUDED)

    def test_every_fixture_has_an_official_https_source(self):
        for m in self.matches["matches"]:
            self.assertTrue(m["url"].startswith("https://"), m["id"])
            self.assertTrue(m["source_name"], m["id"])
            self.assertIn(m["source_check"], {"this session", "inherited capture 2026-10-22"})

    def test_fixture_ids_unique_and_complete(self):
        ids = [m["id"] for m in self.matches["matches"]]
        self.assertEqual(len(ids), len(set(ids)))
        for m in self.matches["matches"]:
            for key in ("home", "away", "competition", "date", "start", "markets"):
                self.assertTrue(m.get(key), (m["id"], key))

    def test_prices_are_internally_consistent(self):
        for s in self.selections:
            self.assertAlmostEqual(1.0 / s["probability"], s["fair_decimal"], places=1)
            if s["fair_american"] < 0:
                implied = abs(s["fair_american"]) / (abs(s["fair_american"]) + 100.0)
            else:
                implied = 100.0 / (s["fair_american"] + 100.0)
            self.assertAlmostEqual(implied, s["probability"], delta=0.01)

    def test_two_way_markets_sum_to_one(self):
        for m in self.matches["matches"]:
            for market in m["markets"]:
                total = sum(o["probability"] for o in market["outcomes"])
                self.assertAlmostEqual(total, 1.0, places=3, msg=(m["id"], market["market"]))

    def test_picks_are_five_per_sport_at_most_and_come_from_published_prices(self):
        pool = {(s["match_id"], s["selection"]) for s in self.selections}
        per_sport = {}
        for p in self.picks:
            self.assertIn((p["match_id"], p["selection"]), pool)
            per_sport.setdefault(p["sport"], []).append(p)
        for sport, rows in per_sport.items():
            self.assertLessEqual(len(rows), 5, sport)
            # no two picks may back different sides of the same market on the same match
            keys = [(r["match_id"], r["market"]) for r in rows]
            self.assertEqual(len(keys), len(set(keys)), sport)

    def test_confidence_labels_follow_the_declared_thresholds(self):
        for s in self.selections:
            expected = ("high" if s["probability"] >= 0.70
                        else "medium" if s["probability"] >= 0.60 else "low")
            self.assertEqual(s["confidence"], expected, s)

    def test_band_membership_matches_the_declared_range(self):
        for s in self.selections:
            self.assertEqual(s["in_band"], -250 <= s["fair_american"] <= 10000, s)

    def test_predictions_cover_every_pick_once(self):
        pick_keys = {(p["match_id"], p["selection"]) for p in self.picks}
        pred_keys = [(p["match_id"], p["selection"]) for p in self.preds]
        self.assertEqual(len(pred_keys), len(set(pred_keys)))
        self.assertEqual(set(pred_keys), pick_keys)

    def test_every_prediction_is_long_enough_and_names_its_selection(self):
        for p in self.preds:
            words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'./-]*", p["prediction"])
            self.assertGreaterEqual(len(words), 30, p["match_id"])
            self.assertEqual(len(words), p["word_count"])
            self.assertIn(p["selection"].lower(), p["prediction"].lower(), p["match_id"])
            self.assertTrue(p["prediction"].endswith("."), p["match_id"])

    def test_predictions_are_unique_prose(self):
        texts = [p["prediction"] for p in self.preds]
        self.assertEqual(len(texts), len(set(texts)))
        openers = [t.split()[0].lower() for t in texts]
        self.assertEqual(len(openers), len(set(openers)), "predictions share an opening word")

    def test_every_prediction_names_its_official_source(self):
        for p in self.preds:
            self.assertTrue(p["source_url"].startswith("https://"), p["match_id"])
            self.assertTrue(p["source_name"], p["match_id"])

    def test_nothing_numeric_is_blank_without_a_recorded_reason(self):
        flagged_sports = {s["sport"] for s in self.flags["sports_not_covered"]}
        covered = {m["sport"] for m in self.matches["matches"]}
        self.assertTrue(covered)
        for m in self.matches["matches"]:
            self.assertTrue(m["home_summary"] and m["away_summary"], m["id"])
        # every covered sport either meets the five-pick target or is disclosed as short
        short = {c["sport"] for c in self.flags["coverage"] if not c["target_met"]}
        for c in self.flags["coverage"]:
            if not c["target_met"]:
                self.assertIn("verified fixture", c["note"], c["sport"])
        self.assertFalse(short & flagged_sports)

    def test_review_register_records_gaps_and_conflicts(self):
        self.assertGreaterEqual(len(self.flags["sports_not_covered"]), 10)
        self.assertGreaterEqual(len(self.flags["discrepancies"]), 1)
        for d in self.flags["discrepancies"]:
            self.assertNotEqual(d["published"], d["verified"])
            self.assertTrue(d["source"].startswith("https://"))


class DailySiteTests(unittest.TestCase):
    def test_every_planned_page_exists(self):
        for name in ["index.html", "matches.html", "lines.html", "picks.html",
                     "predictions.html", "flagged.html", "methodology.html",
                     "sources.html", "sports/index.html", "assets/style.css"]:
            self.assertTrue((PAGES / name).is_file(), name)
        for sport in ["ice-hockey", "rugby-union", "aussie-rules", "rugby-league",
                      "basketball", "baseball", "cricket"]:
            self.assertTrue((PAGES / "sports" / f"{sport}.html").is_file(), sport)

    def test_navigation_resolves_inside_the_layer_at_both_depths(self):
        top = (PAGES / "index.html").read_text()
        deep = (PAGES / "sports" / "ice-hockey.html").read_text()
        for href in ["index.html", "matches.html", "lines.html", "picks.html",
                     "predictions.html", "sports/index.html", "flagged.html",
                     "methodology.html", "sources.html"]:
            self.assertIn(f'href="{href}"', top)
            self.assertIn(f'href="../{href}"', deep)
        # the deep page must not contain a bare relative link that would escape upward
        for href in re.findall(r'href="([^"#]+)"', deep):
            if href.startswith("http") or href.startswith("../"):
                continue
            self.assertTrue((PAGES / "sports" / href).exists(), href)

    def test_sport_pages_do_not_link_to_the_repository_root_except_through_one_step(self):
        for page in (PAGES / "sports").glob("*.html"):
            for href in re.findall(r'href="([^"#]+)"', page.read_text()):
                if href.startswith("http"):
                    continue
                self.assertIn(href.count("../"), (0, 1, 2), (page.name, href))
                if href.startswith("../../"):
                    self.assertEqual(href, "../../index.html", page.name)

    def test_counts_rendered_in_the_dashboard_match_the_data(self):
        html = (PAGES / "index.html").read_text()
        matches = load("matches.json")
        picks = load("picks.json")["picks"]
        self.assertIn(f'<div class="num">{matches["counts"]["matches"]}</div>'
                      f'<div class="label">verified fixtures</div>', html)
        self.assertIn(f'<div class="num">{len(picks)}</div>'
                      f'<div class="label">five-a-sport picks</div>', html)

    def test_flagged_page_lists_every_uncovered_sport(self):
        html = (PAGES / "flagged.html").read_text()
        labels = {"tennis": "Tennis", "darts": "Darts", "snooker": "Snooker",
                  "handball": "Handball", "volleyball": "Volleyball", "golf": "Golf",
                  "motor-racing": "Motor Racing", "gaelic-football": "Gaelic Football",
                  "greyhounds": "Greyhounds", "esports": "eSports"}
        for row in load("flagged.json")["sports_not_covered"]:
            self.assertIn(labels[row["sport"]], html)

    def test_rebuild_is_byte_identical(self):
        before = {p: p.read_bytes() for p in PAGES.rglob("*") if p.is_file()}
        subprocess.run([sys.executable, "scripts/daily_picks_data.py"], cwd=ROOT, check=True,
                       capture_output=True)
        subprocess.run([sys.executable, "scripts/daily_picks_predictions.py"], cwd=ROOT, check=True,
                       capture_output=True)
        subprocess.run([sys.executable, "scripts/daily_picks_flags.py"], cwd=ROOT, check=True,
                       capture_output=True)
        subprocess.run([sys.executable, "scripts/daily_picks_build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        after = {p: p.read_bytes() for p in PAGES.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
