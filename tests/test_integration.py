"""Structural regression tests across Root, Verified, Survey, and Desk layers."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration_audit', ROOT / 'scripts/integration_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class IntegrationTests(unittest.TestCase):
    def test_all_published_layers_have_resolving_local_links(self):
        self.assertEqual(audit.local_link_errors(), [])

    def test_broken_assets_and_encoded_links_are_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'index.html').write_text('<img src="missing.png"><a href="missing%20page.html">x</a>')
            self.assertEqual(len(audit.local_link_errors(root)), 2)

    def test_external_and_fragment_links_are_not_local_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'index.html').write_text('<a href="#x">x</a><a href="https://example.com">y</a>')
            self.assertEqual(audit.local_link_errors(root), [])

    def test_each_survey_narrative_fact_is_disclosed(self):
        facts = sum(len(p['facts_used']) for p in audit.load('data/survey/predictions.json'))
        self.assertEqual(sum(row[1] == 'UNVERIFIED IN THIS AUDIT' for row in audit.findings()), facts)

    def test_disclosures_are_escaped_and_link_verified_desk(self):
        text = audit.body()
        self.assertIn('not a live complete match feed', text)
        self.assertIn('not unique combined totals', text)
        self.assertIn('UNVERIFIED IN THIS AUDIT', text)
        self.assertIn('survey/flagged.html', text)
        self.assertIn('verified/index.html', text)
        self.assertIn('verified/flagged.html', text)


if __name__ == '__main__':
    unittest.main()
