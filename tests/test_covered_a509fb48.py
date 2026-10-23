"""Checks for the /covered/ 15-sport desk (session a509fb48).

What is checked:
* the committed covered/ output is exactly what scripts/covered_build.py produces
  from the committed data/covered/*.json (no hand edits to generated HTML);
* every internal link on the site resolves to a file in the repo;
* every fixture row in the matches data cites an official source host;
* every flag that needs a source has one;
* prediction text obeys the wording rules (30+ words, no "model" or
  "verified", unique), and every high-confidence selection passes the gate
  (p >= 0.70 and fair American price in -250..+10000).
"""
import html
import importlib.util
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
COVERED = ROOT / "covered"
DATA = ROOT / "data" / "covered"

SPORTS_15 = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]

# Official governing-body, league, tour or broadcaster-owned hosts only.
# OLBG is a reference site and is deliberately not on this list.
OFFICIAL_DOMAINS = {
    "api-web.nhle.com", "nhl.com", "statsapi.mlb.com", "mlb.com", "nba.com",
    "formula1.com", "atptour.com", "wst.tv", "pgatour.com", "nrl.com", "gaa.ie",
    "fivb.com", "pdc.tv", "gbgb.org.uk", "icc-cricket.com", "unitedrugby.com",
    "premiershiprugby.com", "premrugby.com", "ehfcl.com", "ehf.eu", "wtatennis.com",
    "github.com",  # repo-internal flags (COORDINATION.md) only
}

# OLBG is a reference site. It may be cited on the Flagged page for reverse-engineering
# notes, never as the source of a fixture row.
REFERENCE_DOMAINS = {"olbg.com", "www.olbg.com"}

BANNED = re.compile(r"\b(model|verified)\b", re.IGNORECASE)


def _load_build():
    spec = importlib.util.spec_from_file_location("covered_build", ROOT / "scripts" / "covered_build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _host_ok(url: str) -> bool:
    p = urlparse(url)
    if p.scheme != "https" or not p.netloc:
        return False
    host = p.netloc.lower().split(":")[0]
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


class CoveredSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = _load_build()
        cls.files = cls.build.build()

    def test_committed_site_matches_build_output(self):
        committed = sorted(
            str(p.relative_to(COVERED)).replace("\\", "/")
            for p in COVERED.rglob("*") if p.is_file()
        )
        self.assertEqual(committed, sorted(self.files.keys()),
                         "covered/ file set differs from scripts/covered_build.py output; rebuild and commit")
        for rel, content in self.files.items():
            with self.subTest(file=rel):
                self.assertEqual((COVERED / rel).read_text(encoding="utf-8"), content)

    def test_one_page_per_sport(self):
        slugs = [slug for _, slug in self.build.SPORTS]
        self.assertEqual(len(slugs), 15)
        for slug in slugs:
            self.assertIn(f"sports/{slug}.html", self.files)
        self.assertEqual({s for s, _ in self.build.SPORTS}, set(SPORTS_15))

    def test_internal_links_resolve(self):
        broken = []
        for rel in self.files:
            if not rel.endswith(".html"):
                continue
            base = (COVERED / rel).parent
            for href in re.findall(r'href="([^"#?]+)', self.files[rel]):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (base / href).resolve().exists():
                    broken.append((rel, href))
        self.assertEqual(broken, [])

    def test_every_table_row_has_a_source_link(self):
        # Brief: every table row needs a source link. The one exception is FL-01, an internal
        # decision about the brief itself, which cites no external page (stated on the page).
        for rel, content in self.files.items():
            if not rel.endswith(".html"):
                continue
            for table in re.findall(r"<table.*?</table>", content, flags=re.S):
                rows = re.findall(r"<tr>(.*?)</tr>", table, flags=re.S)[1:]  # skip header row
                for r in rows:
                    if rel == "flagged.html" and 'id="FL-01"' in r:
                        continue
                    with self.subTest(file=rel):
                        self.assertIn('href="', r, re.sub(r"<[^>]+>", " ", r)[:120])

    def test_no_script_or_external_assets(self):
        for rel, content in self.files.items():
            if rel.endswith(".html"):
                self.assertNotIn("<script", content.lower(), rel)
                self.assertNotRegex(content, r'<link[^>]+href="https?://', rel)


class CoveredDataTests(unittest.TestCase):
    def test_every_fixture_row_has_official_source(self):
        sources = {s["id"]: s for s in _json("sources.json")["sources"]}
        rows = _json("matches.json")["matches"]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(match=row["id"]):
                src = sources.get(row["source_id"])
                self.assertIsNotNone(src, "source id not in sources.json")
                self.assertEqual(src["kind"], "official")
                self.assertTrue(_host_ok(src["url"]), src["url"])
                # The row link is either the registered page or a per-match page on the same official host.
                self.assertTrue(_host_ok(row["source_url"]), row["source_url"])
                self.assertEqual(urlparse(row["source_url"]).netloc, urlparse(src["url"]).netloc)
                self.assertIn(row["sport"], SPORTS_15)

    def test_no_fixture_row_uses_olbg_as_its_source(self):
        for row in _json("matches.json")["matches"]:
            self.assertNotIn("olbg.com", row["source_url"].lower(), row["id"])

    def test_blank_values_are_blank_not_guessed(self):
        # A fixture with no UTC start must not carry a UTC timestamp invented from local time.
        for row in _json("matches.json")["matches"]:
            if row.get("start_utc") is None:
                self.assertNotRegex(row["start_as_read"], r"Z\b", row["id"])

    def test_flags_have_sources_unless_decision(self):
        for flag in _json("flagged.json")["flags"]:
            with self.subTest(flag=flag["id"]):
                if flag["severity"] != "decision":
                    self.assertTrue(flag["source_urls"], "non-decision flag without a source link")
                for url in flag["source_urls"]:
                    ok = _host_ok(url) or urlparse(url).netloc.lower() in REFERENCE_DOMAINS
                    self.assertTrue(ok, url)

    def test_top_five_cap_and_sport_keys(self):
        picks = _json("picks.json")
        self.assertEqual(set(picks["top5_by_sport"].keys()), set(SPORTS_15))
        for sport, rows in picks["top5_by_sport"].items():
            self.assertLessEqual(len(rows), 5, sport)

    def test_high_confidence_gate_on_every_line(self):
        for ln in _json("lines.json")["lines"]:
            for side, v in ln["sides"].items():
                if v["label"] == "high":
                    self.assertGreaterEqual(v["p"], 0.70, ln["fixture_id"])
                    self.assertTrue(-250 <= v["fair_american"] <= 10000, ln["fixture_id"])

    def test_predictions_obey_wording_and_gate(self):
        preds = _json("predictions.json")["predictions"]
        texts = []
        for pr in preds:
            text = pr["text"]
            texts.append(text)
            with self.subTest(prediction=pr.get("fixture_id")):
                self.assertGreaterEqual(len(text.split()), 30, "fewer than 30 words")
                self.assertIsNone(BANNED.search(text), "banned word in prediction text")
                self.assertGreaterEqual(pr["p"], 0.70)
                self.assertTrue(-250 <= pr["fair_american"] <= 10000)
                self.assertEqual(pr["label"], "high")
        self.assertEqual(len(texts), len(set(texts)), "duplicate prediction text")

    def test_no_prediction_text_when_no_pick_passes(self):
        picks = _json("picks.json")
        preds = _json("predictions.json")["predictions"]
        if not picks["high_confidence_qualifying"]:
            self.assertEqual(preds, [])


if __name__ == "__main__":
    unittest.main()
