from __future__ import annotations

import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTAL = ROOT / "portal"
sys.path.insert(0, str(ROOT / "scripts"))

import portal_verify  # noqa: E402


class PortalAccessibilityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.labels: list[str] = []
        self.controls: list[dict[str, str | None]] = []
        self.navs: list[dict[str, str | None]] = []
        self.current_pages = 0
        self.skip_links: list[str | None] = []
        self.main_ids: list[str | None] = []
        self.tables = 0
        self.captions = 0
        self.headers: list[dict[str, str | None]] = []
        self.scroll_regions: list[dict[str, str | None]] = []
        self.filter_roots = 0
        self.filter_counts: list[dict[str, str | None]] = []
        self.empty_messages = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"] or "")
        if tag == "label" and a.get("for"):
            self.labels.append(a["for"] or "")
        if tag in ("input", "select") and any(
            key in a
            for key in ("data-filter-search", "data-filter-sport", "data-filter-conf", "data-filter-type")
        ):
            self.controls.append(a)
        if tag == "nav":
            self.navs.append(a)
        if a.get("aria-current") == "page":
            self.current_pages += 1
        if tag == "a" and "skip-link" in (a.get("class") or "").split():
            self.skip_links.append(a.get("href"))
        if tag == "main":
            self.main_ids.append(a.get("id"))
        if tag == "table":
            self.tables += 1
        if tag == "caption":
            self.captions += 1
        if tag == "th":
            self.headers.append(a)
        if "table-wrap" in (a.get("class") or "").split():
            self.scroll_regions.append(a)
        if "data-filter-root" in a:
            self.filter_roots += 1
        if "data-filter-count" in a:
            self.filter_counts.append(a)
        if "data-filter-empty" in a:
            self.empty_messages += 1


class TestPortalAccessibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pages = sorted(PORTAL.rglob("*.html"))
        cls.parsed: dict[Path, PortalAccessibilityParser] = {}
        for page in cls.pages:
            parser = PortalAccessibilityParser()
            parser.feed(page.read_text(encoding="utf-8"))
            cls.parsed[page] = parser

    def test_every_page_has_skip_link_named_navigation_and_current_location(self) -> None:
        self.assertEqual(len(self.pages), 26)
        for page, parser in self.parsed.items():
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertEqual(parser.skip_links, ["#main-content"])
                self.assertEqual(parser.main_ids, ["main-content"])
                self.assertTrue(parser.navs)
                self.assertTrue(all(nav.get("aria-label") for nav in parser.navs))
                self.assertEqual(parser.current_pages, 1)
                self.assertEqual(len(parser.ids), len(set(parser.ids)), "duplicate IDs make labels ambiguous")

    def test_filter_controls_are_labeled_and_target_their_result_table(self) -> None:
        filtered_pages = 0
        control_count = 0
        for page, parser in self.parsed.items():
            if not parser.filter_roots:
                continue
            filtered_pages += 1
            control_count += len(parser.controls)
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertEqual(parser.filter_roots, 1)
                self.assertTrue(parser.controls)
                for control in parser.controls:
                    control_id = control.get("id")
                    self.assertTrue(control_id, "filter control needs an ID")
                    self.assertIn(control_id, parser.labels, "filter control needs an associated label")
                    self.assertIn(control.get("aria-controls"), parser.ids, "filter must identify the table it updates")
                self.assertEqual(len(parser.filter_counts), 1)
                status = parser.filter_counts[0]
                self.assertEqual(status.get("role"), "status")
                self.assertEqual(status.get("aria-live"), "polite")
                self.assertEqual(status.get("aria-atomic"), "true")
                self.assertEqual(parser.empty_messages, 1)
        self.assertEqual(filtered_pages, 20)
        self.assertEqual(control_count, 41)

    def test_tables_have_captions_column_headers_and_keyboard_scroll_regions(self) -> None:
        table_count = 0
        header_count = 0
        region_count = 0
        for page, parser in self.parsed.items():
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertEqual(parser.tables, parser.captions)
                self.assertTrue(all(header.get("scope") == "col" for header in parser.headers))
                self.assertTrue(
                    all(
                        region.get("role") == "region"
                        and region.get("tabindex") == "0"
                        and region.get("aria-label")
                        for region in parser.scroll_regions
                    )
                )
            table_count += parser.tables
            header_count += len(parser.headers)
            region_count += len(parser.scroll_regions)
        self.assertEqual(table_count, 42)
        self.assertEqual(header_count, 293)
        self.assertEqual(region_count, 42)

    def test_filter_and_focus_enhancements_are_present(self) -> None:
        js = (PORTAL / "assets" / "app.js").read_text(encoding="utf-8")
        css = (PORTAL / "assets" / "style.css").read_text(encoding="utf-8")
        self.assertIn("tr.hidden = !ok", js)
        self.assertIn("emptyEl.hidden = shown > 0", js)
        self.assertIn(":focus-visible", css)
        self.assertIn(".skip-link:focus", css)
        self.assertIn("@media (max-width: 640px)", css)

    def test_official_row_sources_and_internal_links_remain_valid(self) -> None:
        result = portal_verify.verify_all()
        self.assertEqual(result["html_pages"], 26)
        self.assertEqual(result["tbody_rows_with_https_official_link"], 707)
        self.assertEqual(result["internal_links_and_fragments_verified"], 1562)


if __name__ == "__main__":
    unittest.main()
