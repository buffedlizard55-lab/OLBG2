import importlib.util
import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "executive"
SITE = ROOT / "executive"
SPEC = importlib.util.spec_from_file_location("executive_build_test", ROOT / "scripts" / "executive_build.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
SPORTS = {"Ice Hockey", "Basketball", "Motor Racing", "Tennis", "Golf", "Cricket", "Darts",
          "Snooker", "Volleyball", "Rugby Union", "Handball", "Gaelic Sports", "Greyhounds",
          "Baseball", "Rugby League"}
SLUGS = {"Ice Hockey": "ice-hockey", "Basketball": "basketball", "Motor Racing": "motor-racing",
         "Tennis": "tennis", "Golf": "golf", "Cricket": "cricket", "Darts": "darts",
         "Snooker": "snooker", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
         "Handball": "handball", "Gaelic Sports": "gaelic-sports", "Greyhounds": "greyhounds",
         "Baseball": "baseball", "Rugby League": "rugby-league"}


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.rows = []
        self.row_links = []
        self.inrow = False
        self.row_header = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in ("a", "link", "script", "img"):
            v = d.get("href") if tag in ("a", "link") else d.get("src")
            if v:
                self.links.append(v)
        if tag == "tr":
            self.inrow = True
            self.row_links = []
            self.row_header = False
        if self.inrow and tag == "th":
            self.row_header = True
        if self.inrow and tag == "a" and d.get("href", "").startswith("https://"):
            self.row_links.append(d["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.inrow:
            self.rows.append((self.row_header, self.row_links))
            self.inrow = False


class ExecutiveDataTests(unittest.TestCase):
    def test_exact_fifteen_sport_scope_and_all_category_pages(self):
        for sport in SPORTS:
            self.assertTrue((SITE / "sports" / f"{SLUGS[sport]}.html").is_file(), sport)
        covered = {m["sport"] for m in load("fixtures")["fixtures"]}
        self.assertTrue(covered <= SPORTS)
        self.assertEqual(covered | {"Rugby League"}, SPORTS)

    def test_fixture_rows_have_unique_ids_and_official_sources(self):
        fixtures = load("fixtures")["fixtures"]
        self.assertEqual(len({m["id"] for m in fixtures}), len(fixtures))
        for m in fixtures:
            self.assertTrue(m["match"])
            self.assertTrue(m["start_utc"])
            self.assertTrue(m["source_keys"], m["id"])
            self.assertTrue(m["facts"], m["id"])
            for fc in m["facts"]:
                self.assertTrue(fc["source_url"].startswith("https://"), m["id"])
                self.assertTrue(fc["source_key"], m["id"])

    def test_fair_odds_and_band_are_recomputed_from_probabilities(self):
        for row in load("lines")["lines"]:
            p = row["fair_probability"]
            expected = round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)
            self.assertEqual(row["fair_odds"], expected, row["fixture_id"])
            self.assertLessEqual(abs(1.0 / row["fair_decimal"] - p), 0.02, row["fixture_id"])
        for p in load("picks")["picks"]:
            self.assertEqual(p["in_band"], -250 <= p["fair_odds"] <= 10000, p["fixture_id"])

    def test_default_input_cannot_claim_high_conviction(self):
        for p in load("picks")["picks"]:
            if not p["input_verified"]:
                self.assertEqual(p["confidence"], "low", p["fixture_id"])

    def test_predictions_unique_long_explicit_and_linked(self):
        rows = load("predictions")["predictions"]
        self.assertTrue(rows)
        texts = set()
        for row in rows:
            self.assertGreaterEqual(row["word_count"], 30, row["id"])
            self.assertEqual(row["word_count"], len(row["text"].split()))
            self.assertFalse(BANNED.search(row["text"]), row["id"])
            if row["selection"].casefold() not in row["text"].casefold():
                self.assertTrue(any(team and any(part.casefold() in row["text"].casefold()
                                      for part in team.split() if len(part) > 3)
                                   for team in (row.get("home"), row.get("away"))), row["id"])
            self.assertNotIn(row["text"].casefold(), texts)
            texts.add(row["text"].casefold())
            self.assertTrue(row["official_fixture_url"].startswith("https://"), row["id"])
            self.assertTrue(row["facts"], row["id"])
            for fc in row["facts"]:
                self.assertTrue(fc["source_url"].startswith("https://"), row["id"])

    def test_high_conviction_previews_are_unique_written_minimum_thirty_words(self):
        highs = [p for p in load("predictions")["predictions"] if p["confidence"] == "high"]
        self.assertTrue(highs)
        for row in highs:
            self.assertGreaterEqual(row["word_count"], 30, row["id"])
            self.assertFalse(BANNED.search(row["text"]), row["id"])

    def test_rendered_rows_link_sources_and_local_links_resolve(self):
        for page in SITE.rglob("*.html"):
            parser = PageLinks()
            parser.feed(page.read_text(encoding="utf-8"))
            for is_header, links in parser.rows:
                if not is_header:
                    self.assertTrue(links, f"{page.relative_to(ROOT)} has an unlinked table row")
            for href in parser.links:
                u = urlsplit(href)
                if u.scheme or u.netloc or not u.path:
                    continue
                target = (page.parent / unquote(u.path)).resolve()
                if target.is_dir():
                    target /= "index.html"
                self.assertTrue(target.is_relative_to(ROOT.resolve()), href)
                self.assertTrue(target.is_file(), f"{page.relative_to(ROOT)}: {href}")

    def test_executive_summary_present_on_landing(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("Executive summary", html)
        self.assertIn("&minus;250", html)

    def test_strict_cli_verifier_passes(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / "executive_verify.py")],
                             cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_deterministic_rebuild_and_flagged_findings(self):
        before = {p.relative_to(ROOT): p.read_bytes() for p in SITE.rglob("*") if p.is_file()}
        BUILDER.build()
        after = {p.relative_to(ROOT): p.read_bytes() for p in SITE.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertGreaterEqual(load("flagged")["count"], 4)


if __name__ == "__main__":
    unittest.main()
