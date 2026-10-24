"""Vantage snapshot regression: official/source boundaries and clear picks.

These are structural checks on a *dated* 2026-10-24 reading. They cannot prove an
external site still shows the same result tomorrow. See /vantage/flagged.html.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vantage"
OUT = ROOT / "vantage"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class SourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")
        cls.fixtures = {f["id"]: f for f in load("fixtures.json")["fixtures"]}
        cls.picks = load("picks.json")
        cls.lines = load("lines.json")
        cls.predictions = load("predictions.json")
        cls.flags = load("flagged.json")
        cls.taxonomy = load("olbg_taxonomy.json")

    def test_exact_requested_fifteen_categories(self):
        self.assertEqual([h["sport"] for h in self.taxonomy["hubs"]], SPORTS)
        self.assertEqual(set(m["sport"] for m in self.matches["matches"]) | {"Golf"}, set(SPORTS))
        self.assertNotIn("eSports", set(m["sport"] for m in self.matches["matches"]))

    def test_import_provenance_and_hurling_are_explicitly_separate(self):
        imported = json.loads((DATA / "captures/olbg_first_page.json").read_text())
        self.assertEqual(imported["source_commit"], "6926afe")
        self.assertEqual(imported["source_committed_file"], "data/today/olbg_listings.json")
        hurling = json.loads((DATA / "captures/olbg_hurling_first_page.json").read_text())
        self.assertEqual(hurling["listing"]["event_id"], "714")
        discovery = load("discovery.json")
        self.assertEqual(discovery["listings"], imported["listings"] + [hurling["listing"]])
        self.assertEqual(self.matches["listings"], 97)
        self.assertEqual(self.taxonomy["hubs"][7]["sport_ids"], [25, 26])

    def test_every_discovery_record_is_separate_from_official_fields(self):
        unmatched = [m for m in self.matches["matches"] if not m["official_confirmed"]]
        self.assertEqual(len(unmatched), 56)
        for r in unmatched:
            with self.subTest(r["id"]):
                self.assertIsNone(r["official_start_utc"])
                self.assertIsNone(r["fixture_source_url"])
                self.assertIsNone(r["official_home"])
                self.assertIsNone(r["official_date"])
                self.assertIsNone(r["primary_selection"])
                self.assertTrue(r["review_target_url"].startswith("https://"))
                self.assertEqual(r["official_status"], "unverified listing")

    def test_no_unconfirmed_start_or_expired_fixture_is_priced(self):
        cutoff = datetime.fromisoformat(self.matches["as_of_utc"].replace("Z", "+00:00"))
        self.assertEqual(self.matches["priced"], 15)
        for row in self.matches["matches"]:
            if row["primary_selection"]:
                start = datetime.fromisoformat(row["official_start_utc"].replace("Z", "+00:00"))
                self.assertGreater(start, cutoff + timedelta(minutes=90))
                self.assertTrue(row["official_confirmed"])
        by_id = {r["olbg_event_id"]: r for r in self.matches["matches"]}
        for event in ("199999", "9952", "609581", "609555", "188835", "714"):
            self.assertIsNone(by_id[event]["primary_selection"], event)

    def test_mlb_world_series_date_bucket_is_not_utc_start(self):
        row = self.fixtures["mlb-849802"]
        self.assertEqual(row["date"], "2026-10-24")
        self.assertEqual(row["start_utc"], "2026-10-25T00:00:00Z")
        self.assertEqual(row["olbg_event_id"], "160792")
        self.assertEqual(row["stats"]["kind"], "mlb")

    def test_nhl_scores_are_cited_not_goalie_injuries_inferred(self):
        boston = self.fixtures["nhl-2026020170"]
        self.assertEqual(boston["team_records"]["home"], "8-2-1")
        self.assertEqual(boston["stats"]["home"], {"gp": 11, "gf": 42, "ga": 22})
        self.assertEqual(boston["stats"]["away"], {"gp": 11, "gf": 32, "ga": 36})
        self.assertEqual(boston["offered_quote"]["home_american"], -178)
        self.assertEqual(len([f for f in boston["facts"] if "22 October" in f["claim"]]), 2)
        for p in self.predictions["predictions"]:
            self.assertIsNone(p["injury_status"])

    def test_tennis_darts_golf_rugby_league_unsupported_gates_are_blank(self):
        by_id = {r["olbg_event_id"]: r for r in self.matches["matches"]}
        for eid in ("902207", "902251", "32397", "32400", "2695857", "2801554"):
            self.assertIsNone(by_id[eid]["primary_selection"], eid)
        self.assertEqual(self.taxonomy["hubs"][0]["listings"], 0)
        self.assertEqual(self.fixtures["tennis-ningbo-final"]["start_utc"], None)
        self.assertEqual(self.fixtures["cricket-nz-ind-t20i3"]["start_utc"], None)
        self.assertIn("Live Now", self.fixtures["wst-williams-jones"]["status_note"])

    def test_nba_pdf_supplies_matchups_but_no_weak_1_game_lines(self):
        rows = [m for m in self.matches["matches"] if m["sport"] == "Basketball"]
        self.assertEqual(sum(r["official_confirmed"] for r in rows), 8)
        self.assertTrue(all(r["primary_selection"] is None for r in rows))
        by_id = {m["olbg_event_id"]: m for m in rows}
        self.assertEqual(by_id["536116"]["official_start_utc"], "2026-10-25T01:00:00Z")
        self.assertEqual(by_id["536116"]["olbg_displayed_time"], "Today 22:00")
        self.assertEqual(by_id["536118"]["official_start_utc"], "2026-10-25T02:00:00Z")
        self.assertEqual(by_id["536118"]["olbg_displayed_time"], "Today 23:00")

    def test_per_event_flags_and_fifteen_individual_shortfalls(self):
        self.assertEqual(self.flags["count"], len(self.flags["flags"]))
        gaps = [f for f in self.flags["flags"] if f["category"] == "five-per-sport shortfall"]
        self.assertEqual({f["sport"] for f in gaps}, set(SPORTS))
        self.assertEqual(len([f for f in self.flags["flags"] if f["category"] == "unverified listing"]), 56)
        codes = {f["id"] for f in self.flags["flags"]}
        for code in ("V-CRICKET-DATE", "V-NBA-TIMES", "V-NZC-TIME", "V-BCCI-TIME", "V-WTA-DRAW", "V-NHL-CGY"):
            self.assertIn(code, codes)
        self.assertTrue(all(f["official_url"].startswith("https://") for f in self.flags["flags"]))


class OriginalLineTests(unittest.TestCase):
    def test_all_three_markets_are_independently_originated_where_allowed(self):
        data = load("lines.json")
        self.assertEqual(data["fixtures"], 15)
        self.assertEqual(data["count"], 95)
        by_fixture = {}
        for line in data["lines"]:
            by_fixture.setdefault(line["fixture_id"], {}).setdefault(line["market"], []).append(line)
        for fid, markets in by_fixture.items():
            self.assertEqual(len(markets), 3, fid)
            for name, outcomes in markets.items():
                self.assertAlmostEqual(sum(row["probability"] for row in outcomes), 1, places=4)
        self.assertTrue(any(len(next(iter(g.values()))) == 3 for g in by_fixture.values()))

    def test_our_fair_price_is_not_an_offered_quote(self):
        picks = load("picks.json")["picks"]
        high = [p for p in picks if p["confidence"] == "high"]
        self.assertEqual(len(high), 1)
        b = high[0]
        self.assertEqual(b["selection"], "Boston Bruins")
        self.assertEqual((b["fair_american"], b["observed_american"]), (-238, -178))
        self.assertEqual(b["observed_in_band"], True)
        self.assertIsNone(b["olbg_offered_price"])
        for line in load("lines.json")["lines"]:
            self.assertEqual(line["fair_in_band"], -250 <= line["fair_american"] <= 10000)
            self.assertIsNone(line["olbg_offered_price"])
            if line["observed_american"] is not None:
                self.assertEqual(line["sport"], "Ice Hockey")
                self.assertIn("api-web.nhle.com", line["observed_source_url"])

    def test_no_bare_picks_or_robotic_short_previews(self):
        picks = load("picks.json")["picks"]
        preds = load("predictions.json")["predictions"]
        self.assertEqual(len(picks), len(preds))
        ids = {p["id"] for p in picks}
        texts = set()
        for pred in preds:
            with self.subTest(pred["id"]):
                self.assertIn(pred["pick_id"], ids)
                self.assertGreaterEqual(len(pred["text"].split()), 30)
                self.assertIsNone(re.search(r"\b(model|verified)\b", pred["text"], re.I))
                self.assertIn(pred["selection"].casefold(), pred["text"].casefold())
                self.assertNotIn(pred["text"], texts)
                texts.add(pred["text"])
                self.assertGreaterEqual(len(pred["sources"]), 2)

    def test_recomputations_and_site_links_pass(self):
        report = module("vantage_verify").checks()
        self.assertEqual(report["pages"], 27)
        self.assertEqual(report["previews"], 15)
        self.assertGreater(report["assertions"], 3000)
        self.assertGreater(report["links"], 1500)

    def test_site_has_an_obvious_executive_card_and_an_expiry_guard(self):
        page = (OUT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Know the match.", page)
        self.assertIn("Boston Bruins", page)
        self.assertIn("17:45 UTC", page)
        self.assertIn("fair -238", (OUT / "band.html").read_text(encoding="utf-8").replace("<td>", "fair "))
        js = (OUT / "assets/app.js").read_text(encoding="utf-8")
        self.assertIn("Started / archived", js)
        self.assertIn("card.hidden = true", js)

    def test_site_rebuild_is_byte_for_byte_deterministic(self):
        files = sorted([*OUT.rglob("*.html"), *OUT.rglob("*.css"), *OUT.rglob("*.js")])
        before = {str(f.relative_to(ROOT)): f.read_bytes() for f in files}
        for script in ("vantage_seed", "vantage_model", "vantage_predictions", "vantage_flags", "vantage_build"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / (script + ".py"))], cwd=ROOT,
                           check=True, capture_output=True)
        after = {str(f.relative_to(ROOT)): f.read_bytes() for f in files}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
