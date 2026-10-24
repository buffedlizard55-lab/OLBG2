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
        # The root is now the /now/ front door, so its numbers must come from data/now, not from
        # any hand-written sentence. The verified-layer copy it used to carry now lives on the
        # archived pages, which are unchanged.
        now_matches = json.loads((ROOT / "data/now/matches.json").read_text())
        now_picks = json.loads((ROOT / "data/now/picks.json").read_text())
        payload = json.loads((ROOT / "data/verified/matches.json").read_text())
        total = len(payload["matches"])
        active_sports = len({row["sport"] for row in payload["matches"]})
        eligible = json.loads((ROOT / "data/verified/sports.json").read_text())["eligible_sports"]

        index = builder.build_index(payload["matches"])
        categories = builder.build_sports_index()
        archive = builder.build_archive()

        started = sum(bool(m["started"]) for m in now_matches["matches"])
        not_started = now_matches["count"] - started
        self.assertIn(f">{now_matches['count']}</div><div class=\"k\">fixture records", index)
        self.assertIn(f"{not_started} still to start", index)
        self.assertIn(f"{started} started at snapshot", index)
        self.assertNotIn("50 upcoming matches", index)
        self.assertIn(f">{now_picks['pregame_count']}</div><div class=\"k\">picks still to start", index)
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

    def test_readme_describes_the_current_desk_with_data_derived_counts(self):
        """The README leads with the current /now/ desk and quotes its numbers from data/now."""
        matches = json.loads((ROOT / "data/now/matches.json").read_text())
        picks = json.loads((ROOT / "data/now/picks.json").read_text())
        preds = json.loads((ROOT / "data/now/predictions.json").read_text())
        lines = json.loads((ROOT / "data/now/lines.json").read_text())
        readme = (ROOT / "README.md").read_text()

        self.assertIn(f"Fixture records on the desk | **{matches['count']}**", readme)
        started = sum(bool(m["started"]) for m in matches["matches"])
        self.assertIn(f"{matches['count'] - started} still to start", readme)
        self.assertIn(f"{started} started at 18:10Z", readme)
        self.assertIn(f"Prices originated here | **{lines['count']}**", readme)
        self.assertIn(f"Graded picks | **{picks['count']}**", readme)
        self.assertIn(f"Written predictions | **{preds['count']}**", readme)
        self.assertIn("now/picks.html", readme)
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
