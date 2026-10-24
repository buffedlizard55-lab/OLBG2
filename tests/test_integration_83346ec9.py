"""Regression checks for shared publishing integration, not external facts."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import integration_audit as audit


class IntegrationPublishing(unittest.TestCase):
    def test_discovers_new_layers_without_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'future' / 'sports').mkdir(parents=True)
            (root / 'future/sports/test.html').write_text('<a href="missing.html">test</a>')
            self.assertEqual(audit.local_link_errors(root), ['future/sports/test.html: missing.html'])

    def test_current_navigation_at_both_depths(self):
        # Root: one front door for the current desk. Archive: the full index of earlier layers.
        self.assertIn('href="playbook/picks.html"', (ROOT / 'index.html').read_text())
        self.assertIn('href="current/index.html"', (ROOT / 'archive.html').read_text())
        self.assertIn('href="now/index.html"', (ROOT / 'archive.html').read_text())

    def test_current_counts_derived_from_data(self):
        counts = audit.load('data/current/band.json')['counts']
        row = audit._current_row()
        self.assertIn(f'{counts["fixture_rows"]} stored fixtures', row)
        self.assertIn(f'{counts["band_picks"]} model-band predictions', row)
        self.assertIn('not live', row)

    def test_layer_rows_inside_table(self):
        html = audit.body()
        start = html.index('<h2>Explore every research layer')
        end = html.index('</tbody>', start)
        for href in ['atlas/index.html', 'current/index.html']:
            self.assertIn(href, html[start:end])

    def test_limitations_published(self):
        html = (ROOT / 'integration.html').read_text()
        self.assertIn('UNVERIFIED EXTERNALLY', html)
        self.assertIn('actual availability is unverified', html)
        self.assertIn('research/integration-83346ec9.md', html)

    def test_workflow_current_rebuild_and_drift(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        for phase in ['seed', 'model', 'build']:
            self.assertIn(f'python scripts/current_{phase}.py', workflow)
        self.assertIn('-- current data/current ', workflow)
