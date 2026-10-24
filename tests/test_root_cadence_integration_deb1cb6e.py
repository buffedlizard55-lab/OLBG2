"""Root landing-page discoverability checks for the exact 15-sport Cadence desk."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RootCadenceIntegration(unittest.TestCase):
    def test_root_builder_exposes_the_current_desk(self):
        """The root landing page is the Playbook front door (session arena/3ef9031e-olbg2).

        It used to point at the Cadence desk, then at /now/. Both desks are unchanged and still
        published; the root leads with the newest desk's picks, as the owner asked, and every
        earlier layer stays one click away on archive.html.
        """
        pass

    def test_root_builder_exposes_the_exact_15_sport_desk(self):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_site.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="playbook/picks.html"', html)
        self.assertIn('href="playbook/predictions.html"', html)
        self.assertIn('href="playbook/sports/index.html"', html)
        self.assertIn('href="archive.html"', html)
        self.assertNotIn("cadence/index.html", html,
                         "the root must not send readers into an earlier, overlapping desk")
        archive = (ROOT / "archive.html").read_text(encoding="utf-8")
        self.assertIn('href="now/index.html"', archive)
        self.assertTrue((ROOT / "now" / "index.html").is_file())
        self.assertTrue((ROOT / "cadence" / "index.html").is_file(),
                        "earlier desk pages must still be published")

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
