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
        # Front door taken over by the /compass/ desk (session arena/9f424dec-olbg2).
        now_matches = json.loads((ROOT / "data/compass/fixtures.json").read_text())
        now_picks = json.loads((ROOT / "data/compass/picks.json").read_text())
        payload = json.loads((ROOT / "data/verified/matches.json").read_text())
        total = len(payload["matches"])
        active_sports = len({row["sport"] for row in payload["matches"]})
        eligible = json.loads((ROOT / "data/verified/sports.json").read_text())["eligible_sports"]

        index = (ROOT / "index.html").read_text()
        categories = builder.build_sports_index()
        archive = builder.build_archive()

        self.assertIn(f">{now_matches['count']}</div><div class=\"k\">upcoming matches", index)
        self.assertIn(f">{now_picks['count']}</div><div class=\"k\">picks still to start", index)
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
        matches = json.loads((ROOT / "data/compass/fixtures.json").read_text())
        picks = json.loads((ROOT / "data/compass/picks.json").read_text())
        preds = json.loads((ROOT / "data/compass/predictions.json").read_text())
        lines = json.loads((ROOT / "data/compass/lines.json").read_text())
        readme = (ROOT / "README.md").read_text()

        self.assertIn(f"Upcoming fixtures on the desk | **{matches['count']}**", readme)
        self.assertIn(f"Prices originated here | **{lines['count']}**", readme)
        self.assertIn(f"Graded picks | **{picks['count']}**", readme)
        self.assertIn(f"Written predictions | **{preds['count']}**", readme)
        self.assertIn("compass/picks.html", readme)
        self.assertNotIn("178 rows", readme)
        self.assertNotIn("80 tests", readme)
