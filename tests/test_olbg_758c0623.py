from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "olbg"
OUT = ROOT / "olbg"
sys.path.insert(0, str(ROOT / "scripts"))
from olbg_model import american, log5  # noqa: E402


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class OLGDeskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load("source.json")
        cls.matches = load("matches.json")["matches"]
        cls.lines = load("lines.json")["lines"]
        cls.picks = load("picks.json")["shortlists"]
        cls.predictions = load("predictions.json")["predictions"]
        cls.flags = load("flagged.json")["items"]
        cls.counts = load("summary.json")["counts"]
        cls.events = {e["id"]: e for e in cls.matches}

    def test_exact_taxonomy_and_pages(self):
        expected = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey", "Basketball", "Rugby League"]
        self.assertEqual([s["name"] for s in self.source["sports"]], expected)
        self.assertEqual(len(list(OUT.rglob("*.html"))), 22)
        for sport in self.source["sports"]:
            self.assertTrue((OUT / "sports" / f"{sport['slug']}.html").is_file())

    def test_every_event_has_official_link_and_valid_provenance(self):
        self.assertTrue(self.matches)
        for event in self.matches:
            self.assertIn(event["provenance"], {"active", "last_seen", "official_context"})
            self.assertTrue(event["official_sources"], event["id"])
            for source in event["official_sources"]:
                self.assertEqual(source["kind"], "official")
                self.assertTrue(source["url"].startswith("https://"))
            if event["provenance"] == "official_context":
                self.assertIsNone(event["olbg_url"])
            if event["provenance"] == "last_seen":
                self.assertTrue(event["olbg_url"])
        self.assertEqual(sum(e["provenance"] == "active" for e in self.matches), 0)

    def test_all_prices_are_fair_and_no_bookmaker_quote_is_fabricated(self):
        for line in self.lines:
            self.assertGreater(line["probability"], 0)
            self.assertLess(line["probability"], 1)
            self.assertIsNone(line["market_price"])
            self.assertIsNone(line["market_price_source"])
            expected = american(Fraction(line["probability"]).limit_denominator(10**12))
            self.assertLessEqual(abs(expected-line["fair_american"]), 1)
            self.assertAlmostEqual(line["fair_decimal"], 1/line["probability"])

    def test_high_gate_and_prediction_content(self):
        high = [x for x in self.lines if x["primary"] and x["confidence"] == "high"]
        self.assertEqual(len(high), len(self.predictions))
        normalized = set()
        for line in high:
            self.assertGreater(line["probability"], .70)
            self.assertGreaterEqual(line["fair_american"], -250)
            self.assertLessEqual(line["fair_american"], 10000)
            self.assertTrue(self.events[line["event_id"]]["high_detail"])
        for pred in self.predictions:
            self.assertGreaterEqual(len(pred["text"].split()), 30)
            self.assertTrue(pred["text"].startswith("Bet "))
            self.assertIn(pred["selection"].lower(), pred["text"].lower())
            self.assertNotRegex(pred["text"], r"(?i)\b(model|verified)\b")
            norm = re.sub(r"\W+", " ", pred["text"].lower()).strip()
            self.assertNotIn(norm, normalized)
            normalized.add(norm)
            self.assertTrue(pred["official_sources"])

    def test_montreal_exact_boundary(self):
        event = self.events["nhl-2026020166"]
        teams = self.source["inputs"]["nhl"]["teams"]
        mtl, chi = teams["Montreal Canadiens"], teams["Chicago Blackhawks"]
        p = log5(Fraction(mtl["points"], 2*mtl["gp"]), Fraction(chi["points"], 2*chi["gp"]))
        self.assertEqual(p, Fraction(5, 7))
        self.assertAlmostEqual(event["line"]["probability"], float(p))
        self.assertEqual(event["line"]["fair_american"], -250)
        self.assertEqual(event["line"]["confidence"], "high")

    def test_boston_venue_split_not_overall_record(self):
        event = self.events["nba-0022600008"]
        teams = self.source["inputs"]["nba"]["teams"]
        nyk, bos = teams["NYK"], teams["BOS"]
        away = log5(Fraction(nyk["road_w"], 41), Fraction(bos["home_w"], 41))
        self.assertAlmostEqual(event["line"]["away_probability"], float(away))
        self.assertAlmostEqual(event["line"]["home_probability"], 1-float(away))
        self.assertGreater(event["line"]["probability"], .70)
        self.assertLess(event["line"]["probability"], .71)

    def test_top_five_is_a_cap_not_a_quota(self):
        for sport in self.source["sports"]:
            short = self.picks[sport["slug"]]
            self.assertLessEqual(short["count"], 5)
            self.assertEqual(short["count"], len(short["lines"]))
            self.assertEqual(short["shortfall"], 5-short["count"])
            self.assertTrue(all(x["primary"] for x in short["lines"]))
        self.assertEqual(self.picks["golf"]["count"], 0)
        self.assertEqual(self.picks["volleyball"]["count"], 0)

    def test_incomplete_and_conflicting_rows_are_not_promoted(self):
        names = [e["name"] for e in self.matches]
        self.assertFalse(any("Bertola" in n or "Player Competing" in n for n in names))
        self.assertFalse(any("India Women" in n for n in names))
        self.assertFalse(any(e["sport"] == "gaelic-sports" for e in self.matches))
        self.assertNotIn("f1-828", self.events)
        atp_blank = [e for e in self.matches if e["sport"] == "tennis" and not e["line"]]
        self.assertEqual(len(atp_blank), 7)
        for event in atp_blank:
            self.assertIn("ranking", event["blank_reason"].lower())

    def test_blank_and_cap_flags_are_complete(self):
        ids = {f["id"] for f in self.flags}
        for event in self.matches:
            if not event["line"]:
                self.assertIn("BLANK-"+event["id"], ids)
        for line in self.lines:
            if line["probability"] > .70 and -250 <= line["fair_american"] <= 10000 and line["confidence"] != "high":
                self.assertIn("CAP-"+line["id"], ids)
        self.assertEqual(len(ids), len(self.flags))
        self.assertTrue(all(f["links"] for f in self.flags))

    def test_extra_nhl_markets_are_explicitly_low_confidence(self):
        extras = [x for x in self.lines if not x["primary"]]
        self.assertEqual(len(extras), 4)
        self.assertEqual({x["event_id"] for x in extras}, {"nhl-2026020166", "nhl-2026020167"})
        self.assertTrue(all(x["confidence"] == "low" for x in extras))
        self.assertTrue(all("Poisson" in x["method"] for x in extras))

    def test_summary_and_rendered_rows(self):
        self.assertEqual(self.counts["events"], len(self.matches))
        self.assertEqual(self.counts["priced_matches"], sum(bool(e["line"]) for e in self.matches))
        self.assertEqual(self.counts["originated_markets"], len(self.lines))
        self.assertEqual(self.counts["predictions"], len(self.predictions))
        self.assertEqual(self.counts["flags"], len(self.flags))
        text = (OUT / "matches.html").read_text(encoding="utf-8")
        for event in self.matches:
            self.assertIn(f'id="{event["id"]}"', text)

    def test_offline_rebuild_is_deterministic(self):
        paths = sorted(DATA.glob("*.json")) + sorted(p for p in OUT.rglob("*") if p.is_file())
        def digest():
            h = hashlib.sha256()
            for path in paths:
                h.update(str(path.relative_to(ROOT)).encode())
                h.update(path.read_bytes())
            return h.hexdigest()
        before = digest()
        for script in ("olbg_seed.py", "olbg_model.py", "olbg_predictions.py", "olbg_build.py", "olbg_verify.py"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(digest(), before)


if __name__ == "__main__":
    unittest.main()
