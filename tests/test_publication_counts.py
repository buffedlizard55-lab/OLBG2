"""Guard against stale hard-coded snapshot statistics in root publication copy."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publication_builder", ROOT / "scripts" / "build_site.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class Hrefs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        self.values.extend(value for key, value in attrs if key == "href" and value)


class PublicationCountTests(unittest.TestCase):
    def test_root_index_and_category_copy_derive_counts_from_checked_in_data(self):
        payload = json.loads((ROOT / "data/verified/matches.json").read_text())
        total = len(payload["matches"])
        active_sports = len({row["sport"] for row in payload["matches"]})
        eligible = json.loads((ROOT / "data/verified/sports.json").read_text())["eligible_sports"]

        index = builder.build_index(payload["matches"])
        categories = builder.build_sports_index()
        archive = builder.build_archive()

        self.assertIn(f"This page is the {total}-row verified layer", index)
        self.assertNotIn("118-row verified layer", index)
        self.assertIn(f"{len(eligible)} eligible OLBG sports. {active_sports} carry rows", categories)
        self.assertIn(f"{total} rows across {active_sports} sports", archive)
        self.assertNotIn("15 sports)", archive)

    def test_methodology_competition_scope_count_is_data_derived(self):
        payload = json.loads((ROOT / "data/verified/matches.json").read_text())
        competition_rows = sum(row.get("source_scope") != "fixture" for row in payload["matches"])
        methodology = builder.build_methodology(payload["matches"])
        self.assertIn(f"({competition_rows} rows in this snapshot)", methodology)
        self.assertNotIn("(63 rows)", methodology)

    def test_readme_describes_current_root_and_consolidated_snapshots(self):
        root_data = json.loads((ROOT / "data/verified/matches.json").read_text())
        final_summary = json.loads((ROOT / "data/final/summary.json").read_text())
        readme = (ROOT / "README.md").read_text()

        self.assertIn(f"{root_data['counts']['total_rows']} rows", readme)
        self.assertIn(f"{final_summary['counts']['rows']} deduplicated rows", readme)
        self.assertNotIn("178 rows", readme)
        self.assertNotIn("80 tests", readme)

    def test_reproducibility_review_page_discloses_pending_findings_and_links_sources(self):
        page = (ROOT / "review/reproducibility.html").read_text()
        self.assertIn("Flagged for Review", page)
        self.assertIn("not externally verified", page)
        self.assertIn("expected 207; rebuild produced 277", page)
        self.assertIn("https://www.nba.com/schedule?date=2026-10-24", page)
        self.assertIn("https://www.nba.com/game/mia-vs-cha-0022600104", page)
        self.assertIn("did not fetch their page contents", page)

        parser = Hrefs()
        parser.feed(page)
        page_path = ROOT / "review/reproducibility.html"
        for href in parser.values:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page_path.parent / unquote(url.path)).resolve()
            self.assertTrue(target.is_relative_to(ROOT.resolve()), href)
            self.assertTrue(target.is_file(), href)


if __name__ == "__main__":
    unittest.main()
