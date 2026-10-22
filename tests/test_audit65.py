"""Read-only publication audit regression checks; no online access required."""
import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit65


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.rows = []
        self._in_row = False
        self._row_links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr" and attrs.get("id", "").startswith("A65-"):
            self._in_row = True
            self._row_links = []
        if tag == "a":
            self.links.append(attrs.get("href", ""))
            if self._in_row:
                self._row_links.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "tr" and self._in_row:
            self.rows.append(self._row_links)
            self._in_row = False


class Audit65Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit65.audit()

    def test_scans_all_declared_layers_without_inflating_unique_fixtures(self):
        self.assertEqual(self.report["scanned_rows"], sum(v["rows"] for v in self.report["layers"].values()))
        self.assertEqual(self.report["scanned_predictions"], sum(v["predictions"] for v in self.report["layers"].values()))
        self.assertEqual(set(self.report["layers"]), set(audit65.LAYERS))

    def test_each_flag_has_first_party_link_and_uncertain_values_stay_blank(self):
        flags = self.report["findings"]
        self.assertEqual(len({x["id"] for x in flags}), len(flags))
        for f in flags:
            self.assertIn(urlsplit(f["official_url"]).hostname, audit65.OFFICIAL_HOSTS)
            self.assertEqual(urlsplit(f["official_url"]).scheme, "https")
        for f in flags:
            if f["id"] == "A65-DARTS-slate" or f["id"] in ("A65-ES-6", "A65-ES-7", "A65-ES-8"):
                self.assertFalse(f["official_value"])

    def test_essential_claims_are_tracked_as_review_not_new_picks(self):
        ids = {f["id"] for f in self.report["findings"]}
        self.assertIn("A65-DARTS-slate", ids)
        self.assertEqual(len([i for i in ids if i.startswith("A65-GOLF-")]), 3)
        self.assertEqual(len([i for i in ids if i.startswith("A65-ES-")]), 8)
        self.assertEqual(self.report["prediction_issues"], [
            {"layer": "slate", "match_id": "lol-w26-r1-1", "issue": "non-primary main citation"}
        ])

    def test_generated_files_match_builder_and_every_flagged_row_links_to_official_source(self):
        for file in ("index.html", "flagged.html"):
            contents = (ROOT / "audit65" / file).read_text()
            parser = Links()
            parser.feed(contents)
            for href in parser.links:
                if not href or href.startswith(("https://", "#")):
                    continue
                self.assertTrue((ROOT / "audit65" / file).parent.joinpath(href.split("#")[0]).exists(), href)
            if file == "flagged.html":
                self.assertEqual(len(parser.rows), len(self.report["findings"]))
                for row in parser.rows:
                    self.assertTrue(any(urlsplit(url).hostname in audit65.OFFICIAL_HOSTS for url in row), row)
        self.assertEqual(json.loads((ROOT / "data/audit65/report.json").read_text()), self.report)


if __name__ == "__main__":
    unittest.main()
