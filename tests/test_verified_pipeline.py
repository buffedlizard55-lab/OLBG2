"""Comprehensive automated verification tests for the /verified/ pipeline."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "verified"
SITE = ROOT / "verified"

BANNED_DOMAINS = {
    "wikipedia.org",
    "en.wikipedia.org",
    "espn.com",
    "www.espn.com",
    "espncricinfo.com",
    "www.espncricinfo.com",
    "cricinfo.com",
    "thesportsencounter.com",
    "www.thesportsencounter.com",
    "flashscore.com",
    "sofascore.com",
    "basketball-reference.com",
    "hockey-reference.com",
}

EXCLUDED_SLUGS = {
    "soccer",
    "football",
    "horse-racing",
    "american-football",
    "boxing",
    "ufc",
    "mma",
    "ufc-mma",
    "hurling",
    "cycling",
    "specials",
}


class VerifiedPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sports = json.loads((DATA / "sports.json").read_text())
        cls.matches = json.loads((DATA / "matches.json").read_text())
        cls.preds = json.loads((DATA / "predictions.json").read_text())
        cls.flags = json.loads((DATA / "flagged.json").read_text())
        cls.audit = json.loads((DATA / "repo_audit.json").read_text())

    def test_scope_gate_excludes_all_forbidden_sports(self) -> None:
        excl = {x["slug"] for x in self.sports["excluded_sports"]}
        self.assertEqual(
            excl,
            {
                "soccer",
                "horse-racing",
                "american-football",
                "boxing",
                "ufc-mma",
                "hurling",
                "cycling",
                "specials",
            },
        )
        elig = {s["slug"] for s in self.sports["eligible_sports"]}
        self.assertEqual(len(elig), 17)
        self.assertTrue(elig.isdisjoint(EXCLUDED_SLUGS))
        for m in self.matches["matches"]:
            self.assertNotIn(m["sport"], EXCLUDED_SLUGS)

    def test_every_row_has_trusted_official_source_url_and_no_third_party_domains(self) -> None:
        rows = self.matches["matches"]
        self.assertGreaterEqual(len(rows), 140)
        for m in rows:
            url = m.get("official_url") or ""
            parsed = urlparse(url)
            self.assertEqual(parsed.scheme, "https", f"Non-HTTPS URL on {m['id']}: {url}")
            self.assertNotIn(parsed.netloc, BANNED_DOMAINS, f"Banned domain on {m['id']}: {url}")
            if m.get("data_url"):
                dp = urlparse(m["data_url"])
                self.assertEqual(dp.scheme, "https")
                self.assertNotIn(dp.netloc, BANNED_DOMAINS)

    def test_originated_math_and_blank_unconfirmed_discipline(self) -> None:
        placeholder_tokens = {"TBD", "N/A", "NA", "UNKNOWN", "GUESS"}
        orig = 0
        unl = 0
        for m in self.matches["matches"]:
            for field in ("home_summary", "away_summary", "venue"):
                val = m.get(field)
                if isinstance(val, str):
                    self.assertNotIn(val.strip().upper(), placeholder_tokens)
            if m["line_status"] == "originated":
                orig += 1
                wm = m["winner_market"]
                self.assertIsNotNone(wm)
                if wm.get("draw_prob") is not None:
                    total_p = wm["home_prob"] + wm["draw_prob"] + wm["away_prob"]
                else:
                    total_p = wm["home_prob"] + wm["away_prob"]
                self.assertAlmostEqual(total_p, 1.0, delta=0.003, msg=f"Bad prob sum on {m['id']}")
                p = m["pick"]
                self.assertIn(p["confidence"], {"low", "medium", "high"})
                self.assertAlmostEqual(p["fair_odds"], round(1.0 / p["probability"], 2), delta=0.02)
                if "NBA Regular Season" in m["competition"]:
                    self.assertIsNone(m["total_market"])
                    self.assertNotEqual(p["confidence"], "high")
            else:
                unl += 1
                self.assertIsNone(m["winner_market"])
                self.assertIsNone(m["handicap_market"])
                self.assertIsNone(m["total_market"])
                self.assertIsNone(m["pick"])
        self.assertEqual(orig, 102)
        self.assertEqual(unl, 43)

    def test_high_confidence_predictions_are_unique_human_and_ge_30_words(self) -> None:
        high_ids = {
            m["id"]
            for m in self.matches["matches"]
            if m["line_status"] == "originated" and m["pick"]["confidence"] == "high"
        }
        preds = self.preds["predictions"]
        pred_ids = {p["match_id"] for p in preds}
        self.assertEqual(high_ids, pred_ids)
        self.assertEqual(len(preds), 17)
        openings = set()
        headlines = set()
        for p in preds:
            body = p["text"]
            words = body.split()
            self.assertGreaterEqual(len(words), 30, f"Too short ({len(words)}w): {p['match_id']}")
            self.assertNotIn("**", body, f"Raw markdown left in {p['match_id']}")
            openings.add(" ".join(words[:5]).lower())
            headlines.add(p["headline"])
            self.assertGreaterEqual(len(p["facts"]), 2)
            for fact in p["facts"]:
                parsed = urlparse(fact["source"])
                self.assertEqual(parsed.scheme, "https")
                self.assertNotIn(parsed.netloc, BANNED_DOMAINS)
        self.assertEqual(len(openings), len(preds), "Duplicate prediction openings found")
        self.assertEqual(len(headlines), len(preds), "Duplicate headlines found")

    def test_html_pages_flagged_heading_and_zero_broken_internal_links(self) -> None:
        html_files = list(SITE.rglob("*.html"))
        self.assertEqual(len(html_files), 22)
        flagged_html = (SITE / "flagged.html").read_text()
        self.assertIn("<h1>Flagged for Review</h1>", flagged_html)

        href_re = re.compile(r'(?:href|src)="([^"]+)"')
        id_cache: dict[Path, set[str]] = {}
        for page in html_files:
            txt = page.read_text()
            self.assertNotIn("cdn.", txt.lower())
            for target in href_re.findall(txt):
                if target.startswith(("https://", "mailto:", "javascript:")):
                    continue
                self.assertFalse(target.startswith("http://"), f"Insecure HTTP link {target} in {page}")
                rel_path, _, frag = target.partition("#")
                resolved = (page.parent / rel_path).resolve() if rel_path else page.resolve()
                self.assertTrue(resolved.exists(), f"Broken link {target} in {page} -> {resolved}")
                if frag:
                    if resolved not in id_cache:
                        id_cache[resolved] = set(re.findall(r'id="([^"]+)"', resolved.read_text()))
                    self.assertIn(frag, id_cache[resolved], f"Missing anchor #{frag} in {resolved} from {page}")


if __name__ == "__main__":
    unittest.main()
