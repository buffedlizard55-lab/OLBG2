"""Regression tests for the publication dependency (no third-party parser needed)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicationGateTests(unittest.TestCase):
    def test_deploy_requires_reusable_validation(self):
        text = (ROOT / '.github/workflows/deploy-pages.yml').read_text()
        self.assertIn('  validate:\n    uses: ./.github/workflows/pages.yml', text)
        self.assertIn('  deploy:\n    needs: validate\n', text)
        self.assertNotIn('continue-on-error:', text)
        self.assertNotIn('always()', text)

    def test_validation_is_callable_and_checks_generated_content(self):
        text = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn('  workflow_call:\n', text)
        self.assertIn('python -m unittest discover -s tests -v', text)
        self.assertIn('python scripts/integration_audit.py', text)
        self.assertIn('git diff --exit-code', text)


if __name__ == '__main__':
    unittest.main()
