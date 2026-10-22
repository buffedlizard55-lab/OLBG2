"""Structural, mathematical and generated-output gates for the /verified/ pipeline.

These tests do not claim to replace manual verification against the linked
official sources.  They prove inventory consistency, blank discipline, formulas,
provenance states, narrative requirements and internal-link integrity.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "verified"
SITE = ROOT / "verified"
sys.path.insert(0, str(ROOT / "scripts"))

from verified_model import (  # noqa: E402
    HIGH_AMERICAN_MAX,
    HIGH_AMERICAN_MIN,
    american_in_high_band,
    fair_american,
    high_eligible,
)

BANNED_DOMAINS = {
    "wikipedia.org", "en.wikipedia.org", "espn.com", "www.espn.com",
    "espncricinfo.com", "www.espncricinfo.com", "cricinfo.com",
    "thesportsencounter.com", "www.thesportsencounter.com", "flashscore.com",
    "sofascore.com", "basketball-reference.com", "hockey-reference.com",
}
EXCLUDED_SLUGS = {
    "soccer", "football", "horse-racing", "american-football", "boxing",
    "ufc", "mma", "ufc-mma", "hurling", "cycling", "specials",
}
EXPECTED_SPORT_COUNTS = {
    "ice-hockey": 19, "basketball": 25, "rugby-union": 24,
    "handball": 20, "darts": 18, "tennis": 20, "baseball": 3,
    "motor-racing": 3, "volleyball": 9, "cricket": 12, "golf": 4,
    "rugby-league": 3, "gaelic-football": 6,
}
EXPECTED_ORIGINATED = {
    "ice-hockey": 19, "basketball": 23, "rugby-union": 23,
    "handball": 5, "darts": 16, "baseball": 3, "motor-racing": 3,
}
EXPECTED_HIGH_IDS = {"nhl-2026020162", "prod2-12066", "urc-292609"}


class VerifiedPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sports = json.loads((DATA / "sports.json").read_text())
        cls.inputs = json.loads((DATA / "inputs.json").read_text())
        cls.matches = json.loads((DATA / "matches.json").read_text())
        cls.preds = json.loads((DATA / "predictions.json").read_text())
        cls.flags = json.loads((DATA / "flagged.json").read_text())
        cls.audit = json.loads((DATA / "repo_audit.json").read_text())
        cls.rows = cls.matches["matches"]
        cls.by_id = {m["id"]: m for m in cls.rows}

    def test_scope_gate_excludes_all_forbidden_sports(self) -> None:
        excl = {x["slug"] for x in self.sports["excluded_sports"]}
        self.assertEqual(excl, {
            "soccer", "horse-racing", "american-football", "boxing",
            "ufc-mma", "hurling", "cycling", "specials",
        })
        elig = {s["slug"] for s in self.sports["eligible_sports"]}
        self.assertEqual(len(elig), 17)
        self.assertTrue(elig.isdisjoint(EXCLUDED_SLUGS))
        for m in self.rows:
            self.assertNotIn(m["sport"], EXCLUDED_SLUGS)

    def test_exact_refreshed_inventory_counts_and_capture(self) -> None:
        self.assertEqual(len(self.rows), 166)
        self.assertEqual(len(self.by_id), 166, "Duplicate match IDs")
        self.assertEqual(self.matches["counts"], {
            "total_rows": 166, "originated_rows": 92, "unlined_rows": 74,
            "high_confidence": 3, "medium_confidence": 41, "low_confidence": 48,
        })
        self.assertEqual(collections.Counter(m["sport"] for m in self.rows), collections.Counter(EXPECTED_SPORT_COUNTS))
        self.assertEqual(
            collections.Counter(m["sport"] for m in self.rows if m["line_status"] == "originated"),
            collections.Counter(EXPECTED_ORIGINATED),
        )
        for doc in (self.sports, self.inputs, self.matches, self.preds, self.flags, self.audit):
            self.assertEqual(doc["captured_at"], "2026-10-22")

    def test_every_row_has_trusted_official_or_review_url(self) -> None:
        for m in self.rows:
            self.assertTrue(m.get("official_source"), m["id"])
            url = m.get("official_url") or ""
            parsed = urlparse(url)
            self.assertEqual(parsed.scheme, "https", f"Non-HTTPS URL on {m['id']}: {url}")
            self.assertNotIn(parsed.netloc, BANNED_DOMAINS, f"Banned domain on {m['id']}: {url}")
            if m.get("data_url"):
                dp = urlparse(m["data_url"])
                self.assertEqual(dp.scheme, "https")
                self.assertNotIn(dp.netloc, BANNED_DOMAINS)

    def test_discovery_provenance_and_official_supplements(self) -> None:
        discoveries = collections.Counter(m["provenance"]["discovery"] for m in self.rows)
        self.assertEqual(discoveries, {"OLBG-discovered": 126, "official supplementary": 40})
        required = {"discovery", "official_status", "time_basis", "source_scope"}
        for m in self.rows:
            prov = m["provenance"]
            self.assertTrue(required.issubset(prov), m["id"])
            if prov["discovery"] == "OLBG-discovered":
                self.assertTrue(m.get("olbg_event_id"), m["id"])
                self.assertTrue((m.get("olbg_url") or "").startswith("https://www.olbg.com/"), m["id"])
            else:
                self.assertIsNone(m.get("olbg_event_id"), m["id"])
                self.assertIsNone(m.get("olbg_url"), m["id"])
                self.assertIn("no current OLBG card", prov["source_scope"])
        supplements = collections.Counter(
            m["sport"] for m in self.rows if m["provenance"]["discovery"] == "official supplementary"
        )
        self.assertEqual(supplements, {"ice-hockey": 15, "basketball": 15, "rugby-union": 8, "baseball": 2})

    def test_current_official_slate_and_stale_removal(self) -> None:
        self.assertEqual(
            {m["id"] for m in self.rows if m["id"].startswith("nhl-")},
            {f"nhl-{n}" for n in range(2026020154, 2026020166)},
        )
        self.assertEqual(
            {m["id"] for m in self.rows if m["id"].startswith("urc-")},
            {f"urc-{n}" for n in range(292608, 292616)},
        )
        self.assertEqual(
            {m["id"] for m in self.rows if m["id"].startswith("ehfcl-")},
            {
                "ehfcl-202711020101041", "ehfcl-202711020101049",
                "ehfcl-202711020101064", "ehfcl-202711020101043",
                "ehfcl-202711020101019",
            },
        )
        stale = {
            "el-E2026-61", "ec-R4-bosna-bks", "ehfcl-202711020101001",
            "wst-9934", "dog-689384", "f1-2027-drivers", "nhl-2026020152",
        }
        self.assertTrue(stale.isdisjoint(self.by_id))
        visible_event_ids = {m.get("olbg_event_id") for m in self.rows}
        self.assertTrue({"534839", "535674", "534893"}.isdisjoint(visible_event_ids))
        self.assertEqual(len([m for m in self.rows if m["id"].startswith("nba-")]), 14)
        self.assertEqual(len([m for m in self.rows if m["id"].startswith("shl-")]), 6)

    def test_taxonomy_event_links_and_tennis_display_order(self) -> None:
        sports = {s["slug"]: s for s in self.sports["eligible_sports"]}
        self.assertEqual(sports["basketball"]["olbg_sport_id"], 4)
        self.assertEqual(sports["golf"]["olbg_sport_id"], 5)
        for m in self.rows:
            if m["sport"] == "basketball" and m.get("olbg_url"):
                self.assertTrue(m["olbg_url"].endswith("/Basketball/4"), m["id"])
            if m["sport"] == "golf" and m.get("olbg_url"):
                self.assertTrue(m["olbg_url"].endswith("/Golf/5"), m["id"])
        tennis_ids = [m["olbg_event_id"] for m in self.rows if m["sport"] == "tennis"]
        self.assertEqual(tennis_ids, [
            "902063", "902067", "902093", "902073", "902069", "902075",
            "902071", "902066", "902110", "902072", "902104", "902087",
            "902103", "902100", "902109", "902131", "902082", "902120",
            "902126", "902105",
        ])
        self.assertIn("rl-2695857", self.by_id)
        self.assertIn("State of Origin", self.by_id["rl-2695857"]["competition"])
        self.assertIn("rl-2801554", self.by_id)
        self.assertIn("rl-2801600", self.by_id)

    def test_originated_math_high_gate_and_blank_discipline(self) -> None:
        placeholder_tokens = {"TBD", "N/A", "NA", "UNKNOWN", "GUESS"}
        for m in self.rows:
            for field in ("home_summary", "away_summary", "venue"):
                val = m.get(field)
                if isinstance(val, str):
                    self.assertNotIn(val.strip().upper(), placeholder_tokens)
            if m["line_status"] == "unlined":
                self.assertIsNone(m["winner_market"])
                self.assertIsNone(m["handicap_market"])
                self.assertIsNone(m["total_market"])
                self.assertIsNone(m["pick"])
                self.assertTrue(m.get("blank_reason"), m["id"])
                continue
            wm = m["winner_market"]
            self.assertIsNotNone(wm)
            total_p = wm["home_prob"] + wm["away_prob"] + wm.get("draw_prob", 0.0)
            self.assertAlmostEqual(total_p, 1.0, delta=0.003, msg=f"Bad probability sum on {m['id']}")
            p = m["pick"]
            self.assertAlmostEqual(p["fair_odds"], round(1.0 / p["probability"], 2), delta=0.02)
            american = fair_american(p["probability"])
            self.assertEqual(p["fair_american"], american)
            above = p["probability"] > 0.70
            in_band = american_in_high_band(american)
            self.assertEqual(p["high_gate"], {
                "probability_gt_70": above, "fair_american_in_band": in_band,
                "eligible": above and in_band,
                "rule": "p > 0.70 and -250 <= fair American <= +10000",
            })
            expected_high = above and in_band and m.get("confidence_cap") != "medium"
            self.assertEqual(p["confidence"] == "high", expected_high, m["id"])
            if p["confidence"] == "low":
                self.assertLess(p["probability"], 0.60)
            else:
                self.assertGreaterEqual(p["probability"], 0.60)
            if "NBA Regular Season" in m["competition"]:
                self.assertIsNone(m["total_market"])
                self.assertEqual(m["confidence_cap"], "medium")
                self.assertNotEqual(p["confidence"], "high")
                self.assertTrue(m.get("venue"), m["id"])

    def test_american_price_boundaries_including_positive_odds(self) -> None:
        self.assertEqual((HIGH_AMERICAN_MIN, HIGH_AMERICAN_MAX), (-250, 10000))
        self.assertEqual(fair_american(0.75), -300)
        self.assertEqual(fair_american(0.50), -100)
        self.assertEqual(fair_american(0.25), 300)
        self.assertEqual(fair_american(1.0 / 101.0), 10000)
        self.assertTrue(american_in_high_band(-250))
        self.assertTrue(american_in_high_band(300))
        self.assertTrue(american_in_high_band(10000))
        self.assertFalse(american_in_high_band(-251))
        self.assertFalse(american_in_high_band(10001))
        self.assertFalse(high_eligible(0.70), "Exactly 70% must not be High")
        self.assertTrue(high_eligible(5.0 / 7.0), "p>70% at exactly -250 qualifies")
        self.assertTrue(high_eligible(0.7082))
        self.assertFalse(high_eligible(0.72), "Price shorter than -250 must block High")
        self.assertFalse(high_eligible(0.25), "Positive price band never bypasses p>70%")

    def test_high_predictions_unique_official_facts_and_selections(self) -> None:
        high_ids = {
            m["id"] for m in self.rows
            if m["line_status"] == "originated" and m["pick"]["confidence"] == "high"
        }
        self.assertEqual(high_ids, EXPECTED_HIGH_IDS)
        preds = self.preds["predictions"]
        self.assertEqual(self.preds["count"], 3)
        self.assertEqual({p["match_id"] for p in preds}, high_ids)
        openings, headlines = set(), set()
        for p in preds:
            body = p["text"]
            words = body.split()
            self.assertEqual(p["word_count"], len(words))
            self.assertGreaterEqual(len(words), 30, f"Too short: {p['match_id']}")
            self.assertNotIn("**", body)
            self.assertIn(p["selection"].split(" (")[0], body)
            self.assertGreater(p["probability"], 0.70)
            self.assertTrue(american_in_high_band(p["fair_american"]))
            openings.add(" ".join(words[:5]).lower())
            headlines.add(p["headline"])
            self.assertGreaterEqual(len(p["facts"]), 2)
            for fact in p["facts"]:
                parsed = urlparse(fact["source"])
                self.assertEqual(parsed.scheme, "https")
                self.assertNotIn(parsed.netloc, BANNED_DOMAINS)
        self.assertEqual(len(openings), len(preds), "Duplicate prediction openings")
        self.assertEqual(len(headlines), len(preds), "Duplicate headlines")

    def test_neutral_nba_and_actual_f1_market(self) -> None:
        neutral = self.by_id["nba-0022600009"]
        self.assertTrue(neutral["neutral_site"])
        self.assertIn("Moody Center", neutral["venue"])
        self.assertEqual(neutral["home"], "San Antonio Spurs")
        self.assertEqual(neutral["away"], "Houston Rockets")
        self.assertEqual(neutral["olbg_event_id"], "534841")
        f1 = self.by_id["f1-2026-usgp"]
        self.assertEqual(f1["time"], "2026-10-25 16:00 track time")
        self.assertIn("racing/2026/united-states", f1["official_url"])
        without = self.by_id["f1-2026-without-antonelli"]
        self.assertEqual(without["olbg_event_id"], "912")
        self.assertIn("George Russell", without["pick"]["selection"])
        self.assertNotIn("f1-2027-drivers", self.by_id)

    def test_raw_date_semantics_and_pending_states(self) -> None:
        for m in self.rows:
            if m["sport"] == "tennis":
                self.assertIsNone(m["date"])
                self.assertTrue(m["time"].startswith("OLBG card label:"))
        six = self.by_id["six-nations-609013"]
        self.assertEqual(six["date"], "2027-03-13")
        self.assertIn("14 Mar 2027", six["time"])
        self.assertIn("conflicts", six["provenance"]["official_status"])
        self.assertEqual(self.by_id["golf-101904"]["date"], "2026-10-22")
        self.assertEqual(self.by_id["golf-101903"]["date"], "2026-10-23")
        afghan = self.by_id["cricket-188831"]
        self.assertIn("participants", afghan["provenance"]["official_status"])
        self.assertIn("pending", afghan["provenance"]["official_status"])
        plus = self.by_id["vb-36963"]
        self.assertIn("redirected", plus["provenance"]["official_status"])
        # Pending cards retain captured OLBG spellings rather than guessed club names.
        self.assertEqual((self.by_id["kbl-536021"]["home"], self.by_id["kbl-536021"]["away"]), ("Mobis", "Changwon"))
        self.assertEqual((self.by_id["hb-12073"]["home"], self.by_id["hb-12073"]["away"]), ("SonderjyskE", "Nordsjaelland"))
        self.assertEqual(self.by_id["gaa-3530"]["home"], "St Finbarrs")
        self.assertEqual(self.by_id["gaa-3531"]["away"], "Eire Og Cor")
        self.assertEqual(self.by_id["gaa-3536"]["away"], "The Nire")
        self.assertEqual(self.by_id["vb-36990"]["home"], "Ceske Budejovice")
        self.assertEqual(self.by_id["vb-36993"]["away"], "Zlin")

    def test_flags_audit_and_generated_html(self) -> None:
        self.assertEqual(len(self.flags["items"]), 15)
        self.assertEqual(len(self.audit["findings"]), 18)
        flag_ids = {f["id"] for f in self.flags["items"]}
        self.assertTrue({"VF-01", "VF-03", "VF-07", "VF-09", "VF-14", "VF-15"}.issubset(flag_ids))
        html_files = list(SITE.rglob("*.html"))
        self.assertEqual(len(html_files), 22)
        index = (SITE / "index.html").read_text()
        self.assertIn('<div class="kpi-val">166</div>', index)
        self.assertIn("2026-10-22", index)
        self.assertNotIn("≥72.0%", index)
        self.assertNotIn("Official Fixture ↗", index)
        self.assertIn("High gate passed", index)
        self.assertIn("High blocked", index)
        self.assertIn("<h1>Flagged for Review</h1>", (SITE / "flagged.html").read_text())

        href_re = re.compile(r'(?:href|src)="([^"]+)"')
        id_cache: dict[Path, set[str]] = {}
        for page in html_files:
            txt = page.read_text()
            self.assertNotIn("cdn.", txt.lower())
            for target in href_re.findall(txt):
                if target.startswith(("https://", "mailto:", "javascript:")):
                    continue
                self.assertFalse(target.startswith("http://"), f"Insecure link {target} in {page}")
                rel_path, _, frag = target.partition("#")
                resolved = (page.parent / rel_path).resolve() if rel_path else page.resolve()
                self.assertTrue(resolved.exists(), f"Broken link {target} in {page} -> {resolved}")
                if frag:
                    if resolved not in id_cache:
                        id_cache[resolved] = set(re.findall(r'id="([^"]+)"', resolved.read_text()))
                    self.assertIn(frag, id_cache[resolved], f"Missing anchor #{frag} in {resolved} from {page}")


if __name__ == "__main__":
    unittest.main()
