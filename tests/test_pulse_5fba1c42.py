"""Structural tests for the /pulse/ desk (arena/5fba1c42-olbg2)."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pulse"
SITE = ROOT / "pulse"

EXCLUDED_RE = re.compile(
    r"\b(europa league|premier league|la liga|serie a|bundesliga|ligue 1|"
    r"\bnfl\b|\bncaaf\b|american football|horse racing|thoroughbred|boxing|"
    r"\bufc\b|\bmma\b|cycling|tour de france|hurling)\b", re.I)

OFFICIAL_HOSTS = (
    "api-web.nhle.com", "api.nhle.com", "www.nhl.com", "www.nba.com",
    "statsapi.mlb.com", "www.mlb.com", "www.pdc.tv", "ehfcl.eurohandball.com",
    "www.wst.tv", "www.atptour.com", "prod2.lnr.fr", "www.icc-cricket.com",
    "icc-cricket.com", "www.formula1.com", "lolesports.com",
    "www.europeantour.com", "www.gbgb.org.uk", "www.gaa.ie",
    "en.volleyballworld.com", "www.nrl.com", "www.afl.com.au",
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PulseDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load(DATA / "matches.json")
        cls.flagged = load(DATA / "flagged.json")
        cls.preds = load(DATA / "predictions.json")
        cls.inputs = load(DATA / "inputs.json")

    def test_data_files_exist(self):
        for name in ("inputs.json", "matches.json", "flagged.json", "predictions.json"):
            self.assertTrue((DATA / name).is_file(), name)

    def test_match_count_and_uniqueness(self):
        self.assertGreaterEqual(len(self.matches), 40)
        ids = [m["id"] for m in self.matches]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_row_official_source(self):
        for m in self.matches:
            u = m["official_url"]
            self.assertTrue(u.startswith("https://"), (m["id"], u))
            self.assertTrue(any(h in u for h in OFFICIAL_HOSTS), (m["id"], u))

    def test_no_excluded_sport_content(self):
        for m in self.matches:
            self.assertFalse(EXCLUDED_RE.search(m["sport"]), m["id"])
            self.assertFalse(EXCLUDED_RE.search(m["competition"]), m["id"])
            self.assertFalse(EXCLUDED_RE.search(m["home"] + " " + m["away"]), m["id"])

    def test_winner_market_sums_to_one(self):
        for m in self.matches:
            wm = m.get("winner_market")
            if isinstance(wm, list):
                s = sum(x["probability"] for x in wm)
                self.assertAlmostEqual(s, 1.0, delta=0.02, msg=m["id"])

    def test_pick_is_favourite_side_with_confidence(self):
        confs = set()
        for m in self.matches:
            wm = m.get("winner_market")
            if not isinstance(wm, list):
                self.assertTrue(m.get("line_status"), m["id"])
                self.assertIsNone(m["pick"])
                continue
            pick = m["pick"]
            self.assertIn(pick, wm)
            best = max(wm, key=lambda x: x["probability"])
            self.assertEqual(pick, best, m["id"])
            self.assertIn(pick["confidence"], ("low", "medium", "high"))
            confs.add(pick["confidence"])
        self.assertIn("medium", confs)  # desk is genuinely graded, not all-one-band

    def test_band_rule_arithmetic(self):
        for m in self.matches:
            wm = m.get("winner_market")
            if not isinstance(wm, list):
                continue
            for x in wm:
                p, fa = x["probability"], x["fair_american"]
                if p >= 0.70 and fa is not None and -250 <= fa <= 10000:
                    self.assertEqual(x["confidence"], "high", (m["id"], x["selection"]))
                elif p >= 0.575:
                    self.assertEqual(x["confidence"], "medium", (m["id"], x["selection"]))
                else:
                    self.assertEqual(x["confidence"], "low", (m["id"], x["selection"]))

    def test_predictions_minimums_and_band(self):
        highs = self.preds["high_picks"]
        self.assertGreaterEqual(len(highs), 1)
        seen = set()
        for h in highs:
            wc = len(re.findall(r"\w+", h["text"]))
            self.assertGreaterEqual(wc, 30, h["match_id"])
            self.assertEqual(wc, h["words"])
            self.assertTrue(h["probability"] >= 0.70)
            self.assertTrue(-250 <= h["fair_american"] <= 10000)
            self.assertNotIn(h["text"], seen)
            seen.add(h["text"])
            self.assertGreaterEqual(len(h["verified_claims"]), 3)
            for c in h["verified_claims"]:
                self.assertTrue(c["url"].startswith("https://"))
                self.assertTrue(any(host in c["url"] for host in OFFICIAL_HOSTS))

    def test_predictions_match_model_output(self):
        model_high = {
            (m["id"], m["pick"]["selection"])
            for m in self.matches
            if isinstance(m.get("winner_market"), list)
            and m["pick"]["probability"] >= 0.70
            and -250 <= (m["pick"]["fair_american"] or 0) <= 10000
        }
        pred_high = {(h["match_id"], h["selection"]) for h in self.preds["high_picks"]}
        self.assertEqual(model_high, pred_high)

    def test_blank_fixtures_are_flagged(self):
        blanks = [m for m in self.matches if m.get("winner_market") is None]
        self.assertGreaterEqual(len(blanks), 2)  # NBA x2 + cricket
        for m in blanks:
            self.assertTrue(m.get("line_status"), m["id"])
        codes = {f["code"] for f in self.flagged["flags"]}
        self.assertIn("PU-01", codes)
        self.assertIn("PU-03", codes)

    def test_flag_count_and_links(self):
        self.assertGreaterEqual(len(self.flagged["flags"]), 15)
        for f in self.flagged["flags"]:
            self.assertTrue(f["code"].startswith("PU-"))
            self.assertGreaterEqual(len(f["links"]), 1)
            for u in f["links"]:
                self.assertTrue(u.startswith("http"))

    def test_inputs_record_capture_time(self):
        self.assertIn("2026-10-22", self.inputs["captured_at"])
        self.assertIn("12:", self.inputs["captured_at"])


class PulseSiteTests(unittest.TestCase):
    PAGES = ["index", "matches", "picks", "flagged", "sources", "methodology"]
    SPORTS = ["index", "ice-hockey", "basketball", "baseball", "darts", "handball",
              "snooker", "tennis", "rugby-union", "cricket", "motor-racing"]

    def test_pages_exist(self):
        for p in self.PAGES:
            self.assertTrue((SITE / f"{p}.html").is_file(), p)
        for s in self.SPORTS:
            self.assertTrue((SITE / "sports" / f"{s}.html").is_file(), s)
        self.assertTrue((SITE / "assets" / "style.css").is_file())

    def test_no_placeholder_text(self):
        for p in list(self.PAGES) + [f"sports/{s}" for s in self.SPORTS]:
            t = (SITE / f"{p}.html").read_text(encoding="utf-8")
            for bad in ("TODO", "TBD", "FIXME", "lorem ipsum", "PLACEHOLDER"):
                self.assertNotIn(bad, t, p)

    def test_sport_pages_row_per_match(self):
        matches = load(DATA / "matches.json")
        for s in self.SPORTS[1:]:
            ms = [m for m in matches if m["sport"] == s]
            t = (SITE / "sports" / f"{s}.html").read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"<tr>\s*<td>", t)), len(ms), s)
            for m in ms:
                self.assertIn(m["home"].split()[0], t, (s, m["home"]))

    def test_matches_page_covers_all(self):
        matches = load(DATA / "matches.json")
        t = (SITE / "matches.html").read_text(encoding="utf-8")
        for m in matches:
            self.assertIn(m["home"].split()[0], t, m["id"])
        self.assertEqual(
            len([m for m in matches]),
            t.count("official source ↗"),
        )

    def test_flagged_page_lists_all_flags(self):
        flagged = load(DATA / "flagged.json")
        t = (SITE / "flagged.html").read_text(encoding="utf-8")
        for f in flagged["flags"]:
            self.assertIn(f["code"], t)

    def test_https_only(self):
        for p in list(self.PAGES) + [f"sports/{s}" for s in self.SPORTS]:
            t = (SITE / f"{p}.html").read_text(encoding="utf-8")
            self.assertNotIn('href="http://', t, p)

    def test_prediction_visible_on_picks_page(self):
        preds = load(DATA / "predictions.json")
        t = (SITE / "picks.html").read_text(encoding="utf-8")
        for h in preds["high_picks"]:
            self.assertIn(h["text"][:60], t)

    def test_flagged_page_title(self):
        t = (SITE / "flagged.html").read_text(encoding="utf-8")
        self.assertIn("Flagged for Review", t)


class PulseScriptTests(unittest.TestCase):
    def test_model_is_deterministic(self):
        import subprocess
        out1 = (DATA / "matches.json").read_bytes()
        subprocess.run(["python3", "scripts/pulse_model.py"], cwd=ROOT, check=True,
                       capture_output=True)
        out2 = (DATA / "matches.json").read_bytes()
        self.assertEqual(out1, out2)

    def test_verifier_passes(self):
        import subprocess
        r = subprocess.run(["python3", "scripts/pulse_verify.py"], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ALL CHECKS PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
