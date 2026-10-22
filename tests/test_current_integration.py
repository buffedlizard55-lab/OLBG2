"""Final integration gates: generated navigation, CI and automatic link discovery."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class CurrentIntegrationTests(unittest.TestCase):
    def test_root_and_sport_navigation_target_current_desk(self):
        for page in [ROOT / 'index.html', *sorted((ROOT / 'sports').glob('*.html'))]:
            prefix = '../' if page.parent.name == 'sports' else ''
            self.assertIn(f'href="{prefix}current/index.html"', page.read_text())

    def test_unregistered_future_layer_is_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'future-desk' / 'sports' / 'example.html'
            page.parent.mkdir(parents=True)
            page.write_text('<a href="missing.html">Missing</a>')
            self.assertEqual(module('integration_audit').local_link_errors(root),
                             ['future-desk/sports/example.html: missing.html'])

    def test_staging_and_hidden_directories_are_not_published_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ['_site', '.git', 'node_modules']:
                page = root / folder / 'index.html'
                page.parent.mkdir()
                page.write_text('<a href="missing.html">Missing</a>')
            self.assertEqual(module('integration_audit').local_link_errors(root), [])

    def test_current_build_and_drift_gates_present(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        for script in ['current_seed', 'current_model', 'current_build']:
            self.assertIn(f'python scripts/{script}.py', workflow)
        drift_line = next(line for line in workflow.splitlines() if 'git diff --exit-code' in line)
        self.assertIn('current data/current', drift_line)

    def test_review_links_and_verification_boundary_are_rendered(self):
        page = (ROOT / 'integration.html').read_text()
        for name in ['index', 'matches', 'lines', 'predictions', 'sources', 'flagged']:
            self.assertIn(f'href="current/{name}.html"', page)
        self.assertIn('No fresh official-source verification is claimed', page)
        self.assertIn('fragment anchors and external URLs are not checked', page)


if __name__ == '__main__':
    unittest.main()
