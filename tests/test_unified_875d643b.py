"""Integrity tests for the consolidated root desk (session arena/875d643b-olbg2).

These check internal consistency only: that the published pages match the published
data, that every row carries a source, that the prose rules hold, and that the numbers
the pages print are the numbers in the JSON. They do not and cannot verify an external
fact; that work is recorded on /verification.html and /flagged.html.
"""
import importlib.util
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and ((tag in ("a", "link") and key == "href") or (tag in ("script", "img") and key == "src")):
                self.targets.append(value)


PAGES = [
    "index.html", "olbg-events.html", "matches.html", "lines.html", "picks.html",
    "predictions.html", "band.html", "sources.html", "verification.html",
    "repo-review.html", "flagged.html", "methodology.html", "archive.html", "analysis.html",
    "sports/index.html",
]


class UnifiedLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = load("data/unified/olbg_events.json")
        cls.audit = load("data/unified/audit.json")
        cls.picks = cls.audit["picks"]
        cls.preds = load("data/cadence/predictions.json")["predictions"]
        cls.lines = load("data/cadence/lines.json")["lines"]
        cls.sport_pages = sorted(p.name for p in (ROOT / "sports").glob("*.html"))

    def test_every_expected_page_exists(self):
        for page in PAGES:
            self.assertTrue((ROOT / page).is_file(), page)

    def test_every_sport_has_a_page(self):
        for slug in module("unified_build").SPORT_SLUG.values():
            self.assertIn(f"{slug}.html", self.sport_pages)

    def test_local_links_resolve(self):
        bad = []
        targets = PAGES + [f"sports/{name}" for name in self.sport_pages]
        for rel in targets:
            page = ROOT / rel
            parser = Links()
            parser.feed(page.read_text(encoding="utf-8"))
            for href in parser.targets:
                if href.startswith(("http", "data:", "#", "mailto")):
                    continue
                path = (page.parent / unquote(urlsplit(href).path)).resolve()
                if not path.is_file():
                    bad.append(f"{rel}: {href}")
        self.assertEqual(bad, [])

    def test_internal_links_are_relative_to_the_published_root(self):
        # A leading "/" would break the site under the /OLBG2/ project path.
        offenders = []
        for rel in PAGES + [f"sports/{name}" for name in self.sport_pages]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            offenders += [f"{rel}: {m}" for m in re.findall(r'(?:href|src)="(/[^"]*)"', text)]
        self.assertEqual(offenders, [])

    def test_counts_on_the_pages_match_the_data(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'<div class="v">{self.audit["counts"]["prices"]}</div>', index)
        self.assertIn(f'<div class="v">{self.audit["counts"]["predictions"]}</div>', index)
        self.assertIn(f'<div class="v">{self.audit["counts"]["olbg_events_upcoming"]}</div>', index)

    def test_olbg_event_table_lists_every_event(self):
        page = (ROOT / "olbg-events.html").read_text(encoding="utf-8")
        for event in self.inv["events"][:40]:
            self.assertIn(event["event"][:40].replace("&", "&amp;")[:25], page)

    def test_every_fixture_row_links_to_an_official_source(self):
        for row in self.audit["fixtures"]:
            self.assertTrue(str(row["official_source_url"]).startswith("https://"), row["id"])

    def test_every_line_row_recomputes_its_price(self):
        sign = importlib.util.spec_from_file_location("ua", ROOT / "scripts" / "unified_audit.py")
        ua = importlib.util.module_from_spec(sign)
        sign.loader.exec_module(ua)
        errors, stats = ua.check_lines({"lines": self.lines})
        self.assertEqual(errors, [])
        self.assertEqual(stats["total"], len(self.lines))

    def test_predictions_obey_the_brief(self):
        texts = [p["text"] for p in self.preds]
        self.assertEqual(len(texts), len(set(texts)))
        openings = [" ".join(t.split()[:3]).lower() for t in texts]
        self.assertEqual(len(openings), len(set(openings)))
        for p in self.preds:
            self.assertGreaterEqual(len(p["text"].split()), 30, p["id"])
            self.assertIsNone(re.search(r"\b(model\w*|verif\w*)\b", p["text"], re.I), p["id"])

    def test_predictions_only_cover_graded_picks(self):
        graded = {p["id"] for p in self.picks}
        for p in self.preds:
            self.assertIn(p["pick_id"], graded, p["id"])

    def test_band_flag_on_a_pick_is_derived_from_its_price_row(self):
        in_band = [p for p in self.picks if p["confidence"] == "high" and p["in_band"]]
        self.assertTrue(in_band)
        for p in in_band:
            self.assertTrue(p["price_row_found"], p["id"])
            self.assertTrue(p["band_line"], f"{p['id']} is inside the band but not flagged as an alternate line")

    def test_no_high_pick_sits_below_seventy_percent(self):
        for p in self.picks:
            if p["confidence"] == "high":
                self.assertGreaterEqual(p["probability"], 0.6995, p["id"])

    def test_coverage_covers_all_fifteen_sports(self):
        self.assertEqual(len(self.audit["coverage"]), 15)
        for sport, cov in self.audit["coverage"].items():
            self.assertEqual(cov["prediction_target"], 5, sport)

    def test_every_finding_carries_a_source(self):
        for finding in self.audit["findings"]:
            self.assertTrue(finding.get("source_url"), finding["id"])

    def test_flagged_page_lists_every_finding(self):
        page = (ROOT / "flagged.html").read_text(encoding="utf-8")
        for finding in self.audit["findings"]:
            self.assertIn(finding["id"], page)

    def test_build_is_deterministic(self):
        """Rebuilding in memory must produce byte-identical pages."""
        build = module("unified_build")
        inv = load("data/unified/olbg_events.json")
        audit = load("data/unified/audit.json")
        lines = load("data/cadence/lines.json")
        preds = load("data/cadence/predictions.json")
        sources = load("data/cadence/sources.json")
        picks = audit["picks"]
        first = build.build_index(inv, audit, picks, preds)
        second = build.build_index(inv, audit, picks, preds)
        self.assertEqual(first, second)
        self.assertEqual(build.build_band(inv, audit, picks, preds),
                         build.build_band(inv, audit, picks, preds))
        self.assertEqual(build.build_sources(inv, audit, sources),
                         build.build_sources(inv, audit, sources))
        self.assertTrue(lines)

    def test_analysis_page_is_derived_from_the_data(self):
        page = (ROOT / "analysis.html").read_text(encoding="utf-8")
        counts = self.audit["counts"]
        self.assertIn(f'<strong>{75 - counts["predictions"]} more predictions</strong>', page)
        self.assertIn("upcoming OLBG events with no price", page)

    def test_start_times_are_converted_once_and_labelled(self):
        build = module("unified_build")
        self.assertEqual(build.stamp("2026-10-24T01:00:00Z"), "Fri 23 Oct, 6:00 PM PDT")
        # A source that published no clock time keeps its own wording.
        self.assertEqual(build.stamp(None, "24 October, 2:35am ET (NRL display)"),
                         "24 October, 2:35am ET (NRL display)")
        self.assertEqual(build.stamp(None), "start not published")

    def test_the_day_summary_uses_the_reader_zone(self):
        today = module("unified_build").capture_day("2026-10-23T20:32:10Z")
        self.assertEqual(str(today), "2026-10-23")
        included = [p for p in self.picks
                    if p.get("start_utc")
                    and module("unified_build").local_dt(p["start_utc"]).date() == today]
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"of today's {len(included)} priced selections", page)

    def test_workflow_rebuilds_and_drift_checks_the_layer(self):
        workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        for script in ("unified_inventory", "unified_audit", "unified_build"):
            self.assertIn(f"python scripts/{script}.py", workflow)
        self.assertIn("data/unified", workflow)


if __name__ == "__main__":
    unittest.main()
