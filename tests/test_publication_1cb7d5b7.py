"""Publication-level regression tests for the current OLBG landing and ledger pages.

These tests deliberately check rendered HTML, not only the input JSON: a passing data
verifier cannot catch malformed table rows or a misleading cross-desk summary.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger"


class TableParser(HTMLParser):
    """Capture table rows, cells, visible cell text, and links using the stdlib parser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[dict] = []
        self.table: dict | None = None
        self.row: dict | None = None
        self.cell: dict | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "table":
            self.table = {"rows": []}
            self.tables.append(self.table)
        elif tag == "tr" and self.table is not None:
            self.row = {"cells": [], "links": []}
            self.table["rows"].append(self.row)
        elif tag in ("td", "th") and self.row is not None:
            self.cell = {"tag": tag, "text": "", "links": []}
            self.row["cells"].append(self.cell)
        elif tag == "a" and self.row is not None:
            href = attrs.get("href")
            if href:
                self.row["links"].append(href)
                if self.cell is not None:
                    self.cell["links"].append(href)

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th"):
            self.cell = None
        elif tag == "tr":
            self.row = None
            self.cell = None
        elif tag == "table":
            self.table = None
            self.row = None
            self.cell = None


def parse_tables(path: Path) -> TableParser:
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def ledger_events() -> list[dict]:
    return json.loads((ROOT / "data/ledger/matches.json").read_text(encoding="utf-8"))["events"]


def ledger_picks() -> list[dict]:
    return json.loads((ROOT / "data/ledger/picks.json").read_text(encoding="utf-8"))["picks"]


class PublishedTableIntegrity(unittest.TestCase):
    def test_every_ledger_table_row_matches_its_header_width(self) -> None:
        failures = []
        for page in sorted(LEDGER.rglob("*.html")):
            parser = parse_tables(page)
            for table_number, table in enumerate(parser.tables):
                rows = table["rows"]
                header = next((row for row in rows if any(c["tag"] == "th" for c in row["cells"])), None)
                if header is None:
                    continue
                expected = len(header["cells"])
                for row_number, row in enumerate(rows):
                    if row is header:
                        continue
                    actual = len(row["cells"])
                    if actual != expected:
                        failures.append(f"{page.relative_to(ROOT)} table {table_number} row {row_number}: {actual} cells, expected {expected}")
        self.assertEqual(failures, [], "\n".join(failures[:40]))

    def test_olbg_event_rows_separate_official_sources_from_listing_links(self) -> None:
        parser = parse_tables(LEDGER / "matches.html")
        event_tables = [
            table for table in parser.tables
            if table["rows"]
            and [cell["text"].strip() for cell in table["rows"][0]["cells"]]
            == ["Start (UTC)", "Event", "Competition", "OLBG quote", "Our price", "Official check", "Official source", "Listing"]
        ]
        self.assertTrue(event_tables)
        for table in event_tables:
            for row in table["rows"][1:]:
                if not row["cells"]:
                    continue
                state = row["cells"][5]["text"].strip().casefold()
                official_links = row["cells"][6]["links"]
                listing_links = row["cells"][7]["links"]
                self.assertTrue(any("olbg.com/betting-tips/" in href for href in listing_links), row)
                if "unmatched" in state:
                    self.assertEqual(official_links, [], row)
                else:
                    self.assertTrue(official_links, row)

    def test_pick_page_rows_link_to_the_official_matched_fixtures(self) -> None:
        events = ledger_events()
        official_urls = {
            e["verify"].get("official_url")
            for e in events
            if e.get("our_markets") and e["verify"].get("state") == "official-fixture"
        }
        self.assertEqual(len(official_urls), 3)
        parser = parse_tables(LEDGER / "picks.html")
        body_rows = [row for table in parser.tables for row in table["rows"] if row["cells"] and all(c["tag"] == "td" for c in row["cells"])]
        self.assertEqual(len(body_rows), 3 + 2 + 24)  # recommendations, high-band table, all-market table
        for row in body_rows:
            self.assertTrue(set(row["links"]) & official_urls, row)

    def test_high_picks_have_source_linked_previews_and_no_gap(self) -> None:
        flagged = (LEDGER / "flagged.html").read_text(encoding="utf-8")
        self.assertIn("High-confidence OLBG preview coverage", flagged)
        self.assertIn("All 2 high-confidence originated OLBG recommendations", flagged)
        previews = (LEDGER / "predictions.html").read_text(encoding="utf-8")
        self.assertIn("Previews tied to OLBG-listed events — 7", previews)
        self.assertIn("2 high-confidence previews", previews)
        official_standings = "https://api-web.nhle.com/v1/standings/2026-10-23"
        for pick_id, game_url in (
            ("nhl-2026020166-total-Over_5.5", "https://www.nhl.com/gamecenter/mtl-vs-chi/2026/10/24/2026020166"),
            ("nhl-2026020167-handicap-Avalanche_+1.5", "https://www.nhl.com/gamecenter/tbl-vs-col/2026/10/24/2026020167"),
        ):
            self.assertIn(f'id="{pick_id}"', previews)
            self.assertIn(f'href="{official_standings}"', previews)
            self.assertIn(f'href="{game_url}"', previews)

    def test_36_hour_table_uses_capture_time_and_does_not_overrun(self) -> None:
        matches = json.loads((ROOT / "data/ledger/matches.json").read_text(encoding="utf-8"))
        anchor = datetime.fromisoformat(matches["meta"]["generated_at"].replace("Z", "+00:00"))
        parser = parse_tables(LEDGER / "index.html")
        table = next(
            t for t in parser.tables
            if t["rows"]
            and len(t["rows"][0]["cells"]) == 7
            and [c["text"].strip() for c in t["rows"][0]["cells"]][1] == "Start (UTC)"
        )
        header = [c["text"].strip() for c in table["rows"][0]["cells"]]
        start_col = header.index("Start (UTC)")
        rows = [r for r in table["rows"][1:] if r["cells"]]
        self.assertLessEqual(len(rows), 12)
        for row in rows:
            start = datetime.strptime(row["cells"][start_col]["text"].strip(), "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
            self.assertGreaterEqual(start, anchor)
            self.assertLessEqual(start, anchor + timedelta(hours=36))

    def test_root_and_readme_surface_the_independent_cross_check(self) -> None:
        root = (ROOT / "index.html").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn('href="cadence/index.html"', root)
        self.assertIn("Independent cross-check", root)
        self.assertIn("Historical root /verified snapshot", root)
        self.assertIn("Current 15-sport OLBG ledger", root)
        self.assertIn("Current primary desk: 15-sport OLBG ledger", readme)
        self.assertIn("/cadence/", readme)
        self.assertLess(readme.index("Current primary desk: 15-sport OLBG ledger"), readme.index("Independent OLBG daily desk"))

    def test_high_preview_facts_match_the_hashed_official_nhl_capture(self) -> None:
        raw = json.loads((ROOT / "data/ledger/raw/ieh_standings.json").read_text(encoding="utf-8"))
        source_url = "https://api-web.nhle.com/v1/standings/2026-10-23"
        sources = json.loads((ROOT / "data/ledger/sources.json").read_text(encoding="utf-8"))["sources"]
        source = next(row for row in sources if row["key"] == "ieh_standings")
        self.assertEqual(source["url"], source_url)
        self.assertEqual(source["status"], 200)
        self.assertEqual(source["fetched_at"], "2026-10-23T20:32:14Z")
        by_abbrev = {row["teamAbbrev"]["default"]: row for row in raw["standings"]}
        self.assertEqual((by_abbrev["MTL"]["gamesPlayed"], by_abbrev["MTL"]["wins"], by_abbrev["MTL"]["losses"], by_abbrev["MTL"]["otLosses"], by_abbrev["MTL"]["goalFor"], by_abbrev["MTL"]["goalAgainst"]), (9, 4, 3, 2, 30, 34))
        self.assertEqual((by_abbrev["CHI"]["homeWins"], by_abbrev["CHI"]["homeLosses"], by_abbrev["CHI"]["homeGoalsFor"], by_abbrev["CHI"]["homeGoalsAgainst"]), (3, 2, 15, 17))
        self.assertEqual((by_abbrev["COL"]["gamesPlayed"], by_abbrev["COL"]["wins"], by_abbrev["COL"]["losses"], by_abbrev["COL"]["otLosses"], by_abbrev["COL"]["goalFor"], by_abbrev["COL"]["goalAgainst"]), (10, 5, 4, 1, 41, 31))
        self.assertEqual((by_abbrev["TBL"]["roadWins"], by_abbrev["TBL"]["roadLosses"], by_abbrev["TBL"]["streakCode"], by_abbrev["TBL"]["streakCount"]), (2, 2, "W", 3))

    def test_olbg_summary_discloses_reference_and_context_limits(self) -> None:
        text = (LEDGER / "index.html").read_text(encoding="utf-8")
        self.assertIn("only <b>3</b> have our own originated lines", text)
        self.assertIn("90 not on the OLBG list", text)
        self.assertIn("139</b> selections are derived from OLBG's one-sided quoted prices", text)
        self.assertIn("2</b> of 2 high-confidence OLBG recommendations have a matching written preview", text)
        picks = (LEDGER / "picks.html").read_text(encoding="utf-8")
        self.assertIn("not our line", picks)
        self.assertIn("130 are unmatched to an official source", picks)
        self.assertIn("The following remaining listed sports have no originated OLBG selection", picks)
        self.assertNotIn("These sports have no originated OLBG selection", picks)
        previews = (LEDGER / "predictions.html").read_text(encoding="utf-8")
        self.assertIn("Previews tied to OLBG-listed events — 7", previews)
        self.assertIn("Other official-schedule previews — 14", previews)
        self.assertIn("Carried previews — 26", previews)


if __name__ == "__main__":
    unittest.main()
