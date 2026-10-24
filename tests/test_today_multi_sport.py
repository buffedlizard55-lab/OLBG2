"""Regression tests for official tennis, volleyball and handball expansion."""
from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


class TodayMultiSportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = load("olbg_listings")
        cls.fixtures = {f["id"]: f for f in cls.board["fixtures"]}
        cls.listings = {row["event_id"]: row for row in cls.board["listings"]}
        cls.lines = load("lines")["lines"]
        cls.picks = load("picks")["picks"]
        cls.predictions = {p["fixture_id"]: p for p in load("predictions")["predictions"]}

    def rows(self, fixture_id):
        return [line for line in self.lines if line["fixture_id"] == fixture_id]

    def test_every_pick_has_a_matching_captured_olbg_row(self):
        for pick in self.picks:
            fixture = self.fixtures[pick["fixture_id"]]
            event_id = fixture.get("olbg_event_id")
            self.assertIn(event_id, self.listings, fixture["id"])
            self.assertEqual(pick["olbg_event_url"], self.listings[event_id]["url"])

    def test_official_only_fixtures_are_priced_but_never_picked(self):
        official_only = {f["id"] for f in self.fixtures.values() if not f.get("olbg_event_id")}
        self.assertEqual(official_only, {
            "vol-20261025-piacenza-modena", "vol-20261025-milano-cuneo",
        })
        picked = {p["fixture_id"] for p in self.picks}
        self.assertFalse(official_only & picked)
        for fixture_id in official_only:
            self.assertTrue(self.rows(fixture_id), fixture_id)

    def test_handball_has_three_way_result_and_half_goal_markets(self):
        for fixture in self.fixtures.values():
            if fixture["sport"] != "Handball":
                continue
            rows = self.rows(fixture["id"])
            moneylines = [row for row in rows if row["market"] == "Moneyline"]
            self.assertEqual(len(moneylines), 3)
            self.assertEqual(sum(row["selection"] == "Tie" for row in moneylines), 1)
            self.assertAlmostEqual(sum(row["probability"] for row in moneylines), 1, delta=0.0002)
            for row in rows:
                if row["market"] in ("Match handicap", "Total goals"):
                    self.assertEqual(abs(row["line"] % 1), 0.5, row["id"])

    def test_set_markets_are_complementary(self):
        for fixture in self.fixtures.values():
            if fixture["sport"] not in ("Tennis", "Volleyball"):
                continue
            rows = self.rows(fixture["id"])
            handicaps = [row for row in rows if row["market"] == "Set handicap"]
            self.assertEqual(len(handicaps), 4)
            for favourite, underdog in ((fixture["home"], fixture["away"]),
                                        (fixture["away"], fixture["home"])):
                minus = next(row for row in handicaps if row["selection"] == favourite and row["line"] == -1.5)
                plus = next(row for row in handicaps if row["selection"] == underdog and row["line"] == 1.5)
                self.assertAlmostEqual(minus["probability"] + plus["probability"], 1, delta=0.0002)
            totals = [row for row in rows if row["market"] == "Total sets"]
            for total in {row["line"] for row in totals}:
                pair = [row for row in totals if row["line"] == total]
                self.assertEqual({row["selection"] for row in pair}, {"Over", "Under"})
                self.assertAlmostEqual(sum(row["probability"] for row in pair), 1, delta=0.0002)

    def test_osaka_retirement_does_not_count_as_a_completed_set(self):
        fixture = self.fixtures["tennis-wta-osaka-2026-final"]
        self.assertEqual(fixture["tennis"]["away_sets"], [7, 1])
        self.assertNotIn("8-0", fixture["fact_away"])
        self.assertIn("retirement", fixture["fact_away"])
        self.assertTrue(fixture["start_display"].startswith("Not before"))

    def test_ningbo_date_conflict_is_explicitly_flagged(self):
        fixture = self.fixtures["tennis-wta-ningbo-2026-final"]
        self.assertEqual(fixture["start_utc"], "2026-10-25T09:00:00Z")
        self.assertTrue(fixture["start_display"].startswith("Not before"))
        flags = load("flagged")["items"]
        item = next(item for item in flags if item["code"] == "WTA-DATE-CONFLICT")
        self.assertIn("Saturday 24 October", item["detail"])
        self.assertIn("Sunday 25 October", item["detail"])

    def test_new_high_picks_keep_their_calculated_band_status(self):
        by_id = {p["fixture_id"]: p for p in self.picks}
        for fixture_id in ("tennis-atp-almaty-2026-final", "tennis-wta-ningbo-2026-final"):
            self.assertEqual(by_id[fixture_id]["confidence"], "high")
            self.assertTrue(by_id[fixture_id]["in_band"])
        paris = by_id["hb-20261025-saint-raphael-paris"]
        self.assertEqual(paris["confidence"], "high")
        self.assertFalse(paris["in_band"])

    def test_new_lines_expose_schedule_and_statistics_sources(self):
        for fixture in self.fixtures.values():
            if fixture["sport"] not in ("Tennis", "Volleyball", "Handball"):
                continue
            for row in self.rows(fixture["id"]):
                self.assertGreaterEqual(len(row["source_urls"]), 2, row["id"])
                self.assertTrue(all(url.startswith("https://") for url in row["source_urls"]))

    def test_f1_field_and_podium_probabilities_are_exhaustive(self):
        fixture = self.fixtures["f1-2026-united-states"]
        rows = self.rows(fixture["id"])
        winners = [row for row in rows if row["market"] == "Race winner"]
        podium = [row for row in rows if row["market"] == "Podium finish"]
        self.assertEqual(len(fixture["motor"]["drivers"]), 22)
        self.assertEqual(len(winners), 22)
        self.assertAlmostEqual(sum(row["probability"] for row in winners), 1, delta=0.0002)
        self.assertEqual(len(podium), 44)
        self.assertAlmostEqual(sum(row["probability"] for row in podium
                                   if row["selection"].endswith("Yes")), 3, delta=0.0002)
        self.assertNotIn("Yuki Tsunoda", {row["selection"] for row in winners})

    def test_f1_start_selection_and_event_display(self):
        fixture = self.fixtures["f1-2026-united-states"]
        self.assertEqual(fixture["start_utc"], "2026-10-25T20:00:00Z")
        pick = next(p for p in self.picks if p["fixture_id"] == fixture["id"])
        self.assertEqual(pick["selection"], "Kimi Antonelli")
        self.assertEqual(pick["confidence"], "low")
        self.assertTrue(pick["in_band"])
        page = (ROOT / "today" / "sports" / "motor-racing.html").read_text(encoding="utf-8")
        self.assertIn("United States Grand Prix", page)
        self.assertNotIn("Race <span", page)

    def test_darts_markets_are_complementary_and_current(self):
        fixtures = [f for f in self.fixtures.values() if f["sport"] == "Darts"]
        self.assertEqual(len(fixtures), 3)
        self.assertNotIn("32399", self.listings)
        self.assertNotIn("32398", self.listings)
        self.assertIn("26023", self.listings)
        for fixture in fixtures:
            rows = self.rows(fixture["id"])
            self.assertEqual(len(rows), 8)
            moneylines = [row for row in rows if row["market"] == "Moneyline"]
            self.assertAlmostEqual(sum(row["probability"] for row in moneylines), 1, delta=0.0002)
            handicaps = [row for row in rows if row["market"] == "Leg handicap"]
            for favourite, underdog in ((fixture["home"], fixture["away"]),
                                        (fixture["away"], fixture["home"])):
                minus = next(row for row in handicaps if row["selection"] == favourite and row["line"] == -2.5)
                plus = next(row for row in handicaps if row["selection"] == underdog and row["line"] == 2.5)
                self.assertAlmostEqual(minus["probability"] + plus["probability"], 1, delta=0.0002)
            totals = [row for row in rows if row["market"] == "Total legs"]
            self.assertAlmostEqual(sum(row["probability"] for row in totals), 1, delta=0.0002)

    def test_darts_price_uses_only_disclosed_official_inputs(self):
        fixture = self.fixtures["darts-ec-clayton-rock"]
        home, away = fixture["darts"]["home"], fixture["darts"]["away"]
        logit = (0.08 * math.log(home["world_money"] / away["world_money"])
                 + 0.06 * math.log(home["et_money"] / away["et_money"])
                 + 0.035 * ((home["legs_won"] - home["legs_lost"])
                            - (away["legs_won"] - away["legs_lost"])))
        q = 1 / (1 + math.exp(-logit))
        expected = sum(math.comb(9 + losses, losses) * q ** 10 * (1 - q) ** losses
                       for losses in range(10))
        home_line = next(row for row in self.rows(fixture["id"])
                         if row["market"] == "Moneyline" and row["selection"] == fixture["home"])
        self.assertAlmostEqual(home_line["probability"], expected, delta=0.0001)
        pick = next(p for p in self.picks if p["fixture_id"] == fixture["id"])
        self.assertEqual(pick["selection"], "Josh Rock")
        self.assertEqual(pick["confidence"], "low")
        self.assertTrue(all(row["source_url"] == "https://www.pdc.tv/rankings"
                            for row in self.rows(fixture["id"])))


if __name__ == "__main__":
    unittest.main()
