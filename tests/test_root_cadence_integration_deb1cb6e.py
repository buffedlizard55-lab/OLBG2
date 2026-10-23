"""Root landing-page discoverability checks for the exact 15-sport Cadence desk."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RootCadenceIntegration(unittest.TestCase):
    def test_root_builder_exposes_the_exact_15_sport_desk(self):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_site.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        link = 'href="cadence/index.html"'
        self.assertGreaterEqual(html.count(link), 2, "expected a navigation link and a landing-page CTA")
        self.assertIn("Exact 15-sport card &amp; evidence audit", html)
        self.assertTrue((ROOT / "cadence" / "index.html").is_file())

    def test_flagged_page_exposes_the_source_year_mismatch(self):
        page = (ROOT / "flagged.html").read_text(encoding="utf-8")
        self.assertIn("AUDIT-GREY-01", page)
        self.assertIn("2025-category-one-schedule", page)
        self.assertIn("current official 2026 schedule is checked", page)
        self.assertIn('href="https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/"', page)
        self.assertIn("AUDIT-ODDS-02", page)
        self.assertIn("Displayed offered prices are constructed, not captured market quotes", page)
        self.assertIn('href="https://www.olbg.com/betting-tips"', page)
        self.assertIn("applying a code-defined margin", page)


if __name__ == "__main__":
    unittest.main()
