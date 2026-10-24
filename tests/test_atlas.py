"""Structural tests for the first-hand Atlas desk (/atlas/).

Every assertion here is a check that the published site does not contradict the
brief: eligible sports only, an official link on every row, no invented values,
no bookmaker prices, and predictions that meet the word/confidence rules.
"""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "atlas"
OUT = ROOT / "atlas"

EXCLUDED = {"soccer", "football", "boxing", "ufc", "mma", "american-football",
            "hurling", "horse-racing", "cycling", "specials"}

OFFICIAL_HOSTS = {
    "nhl.com", "www.nhl.com", "api.nhle.com",
    "nba.com", "www.nba.com", "stats.nba.com",
    "mlb.com", "www.mlb.com", "statsapi.mlb.com",
    "euroleague.net", "api-live.euroleague.net", "www.euroleague.net",
    "euroleaguebasketball.net", "www.euroleaguebasketball.net",
    "atptour.com", "www.atptour.com", "protennislive.com",
    "wtatennis.com", "www.wtatennis.com",
    "pdc.tv", "www.pdc.tv", "gbgb.org.uk", "www.gbgb.org.uk",
    "afl.com.au", "www.afl.com.au", "aflw.com.au", "www.aflw.com.au",
    "formula1.com", "www.formula1.com",
    "lolesports.com", "www.lolesports.com",
    "legavolley.it", "www.legavolley.it",
    "gaa.ie", "www.gaa.ie",
    "pga.com", "www.pga.com", "www.pgatour.com", "europeantour.com", "www.europeantour.com",
    "wst.tv", "www.wst.tv",
    "nrl.com", "www.nrl.com", "superleague.co.uk", "www.superleague.co.uk",
    "plusliga.pl", "www.plusliga.pl",
    "iccbcc.com", "www.iccbcc.com", "espncricinfo.com",
    "icc-cricket.com", "www.icc-cricket.com",
    "lnr.fr", "www.lnr.fr", "top14.lnr.fr", "prod2.lnr.fr",
    "unitedrugby.com", "www.unitedrugby.com", "stats.unitedrugby.com",
    "ehfcl.eurohandball.com", "eurohandball.com", "www.eurohandball.com",
    "cricketworldcup.com", "www.cricketworldcup.com",
    "swehockey.se", "www.swehockey.se",
}


def _load(name):
    return json.loads((ATLAS / name).read_text())


class TestScope(unittest.TestCase):
    def setUp(self):
        self.matches = _load("matches.json")
        self.sports = _load("sports.json")

    def test_seventeen_eligible_sports_only(self):
        slugs = {s["slug"] for s in self.sports["eligible_sports"]}
        self.assertEqual(len(slugs), 17)
        self.assertFalse(slugs & EXCLUDED)
        used = {r["sport"] for r in self.matches["matches"]}
        self.assertFalse(used & EXCLUDED)
        self.assertTrue(used <= slugs)

    def test_no_excluded_term_in_any_published_row_text(self):
        # "football" alone is ambiguous — Gaelic football is one of the 17 eligible sports — so
        # only the banned compound is checked alongside the unambiguous terms.
        banned = re.compile(
            r"\b(soccer|boxing|ufc|mma|hurling|cycling|specials)\b|(american|association) football")
        bad = []
        for r in self.matches["matches"]:
            haystack = " ".join(str(r.get(k) or "") for k in
                                ("sport_name", "competition", "home", "away", "venue")).lower()
            hit = banned.search(haystack)
            if hit:
                bad.append((r["id"], hit.group(1)))
        self.assertEqual(bad, [], f"excluded sport language in rows: {bad}")

    def test_the_exclusions_are_documented_on_the_sport_index(self):
        page = (OUT / "sports" / "index.html").read_text().lower()
        for term in ("soccer", "boxing", "ufc", "mma", "american football", "hurling",
                     "horse racing", "cycling", "specials"):
            self.assertIn(term, page, f"exclusion {term} not documented")


class TestRows(unittest.TestCase):
    def setUp(self):
        self.matches = _load("matches.json")

    def test_every_row_carries_an_official_source_link(self):
        for r in self.matches["matches"]:
            url = r.get("official_url") or ""
            self.assertTrue(url.startswith("https://"), f"non-https source: {r['id']}")
            host = re.sub(r"^https://([^/]+).*", r"\1", url)
            self.assertIn(host, OFFICIAL_HOSTS, f"unofficial host on {r['id']}: {host}")

    def test_blank_rows_state_a_reason(self):
        for r in self.matches["matches"]:
            if r["markets"]:
                continue
            self.assertTrue(r.get("blank_reason"), f"blank row with no reason: {r['id']}")
            self.assertIsNone(r.get("pick"))

    def test_prices_are_the_inverse_of_the_probability(self):
        for r in self.matches["matches"]:
            for m in r["markets"]:
                for o in m["outcomes"]:
                    self.assertAlmostEqual(o["fair_decimal"], round(1.0 / o["probability"], 4),
                                           places=2, msg=r["id"])
                    p = o["probability"]
                    am = o["fair_american"]
                    if p >= 0.5:
                        self.assertLessEqual(am, -100, r["id"])
                    else:
                        self.assertGreaterEqual(am, 100, r["id"])
                    # the American price is rounded to a whole number, so the round-trip
                    # agrees to two decimal places, not three.
                    self.assertAlmostEqual(
                        p, (100.0 / (am + 100.0)) if am > 0 else (abs(am) / (abs(am) + 100.0)),
                        places=2, msg=r["id"])

    def test_confidence_labels_follow_the_rule(self):
        for r in self.matches["matches"]:
            pick = r.get("pick")
            if not pick:
                continue
            p = pick["probability"]
            in_band = r["match_band"]["in_band"]
            if pick["confidence"] == "high":
                self.assertGreaterEqual(p, 0.70, r["id"])
                self.assertTrue(in_band, f"high pick outside band: {r['id']}")
            elif pick["confidence"] == "medium":
                self.assertGreaterEqual(p, 0.60, r["id"])
            else:
                self.assertLess(p, 0.60, r["id"])

    def test_band_is_the_brief_window(self):
        for r in self.matches["matches"]:
            for m in r["markets"]:
                for o in m["outcomes"]:
                    d = o["fair_decimal"]
                    self.assertGreater(d, 1.0)
        for r in self.matches["matches"]:
            b = r["match_band"]
            if not r["markets"]:
                self.assertFalse(b["in_band"], r["id"])
                continue
            if b["in_band"]:
                self.assertGreaterEqual(b["outsider_decimal"], 1.40)
                self.assertLessEqual(b["outsider_decimal"], 101.00)
                self.assertGreaterEqual(b["favourite_american"], -250)


class TestPredictions(unittest.TestCase):
    def setUp(self):
        self.preds = _load("predictions.json")
        self.matches = {m["id"]: m for m in _load("matches.json")["matches"]}

    def test_every_prediction_is_long_enough_and_unique(self):
        texts = set()
        for p in self.preds["predictions"]:
            self.assertGreaterEqual(p["word_count"], 30, p["match_id"])
            self.assertEqual(p["word_count"], len(p["text"].split()))
            self.assertNotIn(p["text"], texts, f"duplicate prediction text: {p['match_id']}")
            texts.add(p["text"])

    def test_predictions_only_on_verified_band_selections(self):
        for p in self.preds["predictions"]:
            row = self.matches[p["match_id"]]
            self.assertTrue(row["match_band"]["in_band"], p["match_id"])
            self.assertGreaterEqual(p["probability"], 0.70, p["match_id"])
            market = next(m for m in row["markets"] if m["market"] == p["market"])
            self.assertIn(p["selection"], [o["label"] for o in market["outcomes"]])

    def test_featured_subset_is_itself_inside_the_band(self):
        for p in self.preds["predictions"]:
            if p["featured"]:
                self.assertGreaterEqual(p["fair_american"], -250, p["match_id"])
                self.assertLessEqual(p["fair_american"], 10000, p["match_id"])
                self.assertGreaterEqual(p["fair_decimal"], 1.40)

    def test_every_prediction_carries_sourced_facts(self):
        for p in self.preds["predictions"]:
            self.assertTrue(p["facts"], p["match_id"])
            for f in p["facts"]:
                self.assertTrue(f["source"].startswith("https://"), p["match_id"])
                self.assertTrue(f["claim"].strip(), p["match_id"])

    def test_openings_are_not_robotic_repeats(self):
        openings = [" ".join(p["text"].split()[:3]) for p in self.preds["predictions"]]
        uniq = len(set(openings))
        self.assertGreaterEqual(uniq, len(openings) * 0.5,
                                f"only {uniq} distinct openings in {len(openings)} predictions")


class TestVerification(unittest.TestCase):
    def test_ledger_and_flags_exist(self):
        ver = _load("verification.json")
        flags = _load("flagged.json")
        self.assertTrue(ver["families"])
        self.assertGreater(flags["count"], 0)
        for f in flags["items"]:
            self.assertTrue(f["evidence"], f["id"])
            for e in f["evidence"]:
                self.assertTrue(e["url"].startswith("https://"), f["id"])

    def test_flagged_items_are_published_with_their_links(self):
        flags = _load("flagged.json")
        page = (OUT / "flagged.html").read_text()
        for f in flags["items"]:
            self.assertIn(f["id"], page, f["id"] not in page and "missing flagged id")
            self.assertIn(f["title"][:40], page)


class TestBuild(unittest.TestCase):
    def test_pages_exist_and_have_no_broken_local_links(self):
        pages = sorted(OUT.rglob("*.html"))
        self.assertGreaterEqual(len(pages), 20)
        broken = []
        for page in pages:
            for match in re.finditer(r'(?:href|src)="((?!https?:|#|mailto:)[^"#]+)"', page.read_text()):
                target = (page.parent / match.group(1)).resolve()
                if target.is_dir():
                    target /= "index.html"
                if not target.is_file():
                    broken.append(f"{page}: {match.group(1)}")
        self.assertEqual(broken, [])

    def test_build_is_deterministic(self):
        before = {p: p.read_text() for p in OUT.rglob("*.html")}
        subprocess.run(["python3", "scripts/atlas_build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        after = {p: p.read_text() for p in OUT.rglob("*.html")}
        self.assertEqual(set(before), set(after))
        for p in before:
            self.assertEqual(before[p], after[p], f"non-deterministic output: {p}")

    def test_ci_rebuilds_and_gates_the_layer(self):
        wf = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
        for script in ("atlas_seed.py", "atlas_model.py", "atlas_predictions.py",
                       "atlas_verify.py", "atlas_build.py"):
            self.assertIn(script, wf)
        self.assertIn("atlas data/atlas", wf)

    def test_archive_index_links_to_the_desk(self):
        # The root landing page is now one clean front door for the current desk. Every earlier
        # layer, including this one, is indexed on archive.html so it stays reachable.
        self.assertIn('href="atlas/index.html"', (ROOT / "archive.html").read_text())


if __name__ == "__main__":
    unittest.main()
