import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from official_source_audit import audit, classify


class SourceAuditTests(unittest.TestCase):
    def test_olbg_is_not_official_fixture_evidence(self):
        self.assertEqual(classify('https://www.olbg.com/betting-tips/Cricket'), 'olbg_provenance_only')

    def test_near_match_domains_not_official(self):
        self.assertEqual(classify('https://evil-lnr.fr/match'), 'not_allowlisted')
        self.assertEqual(classify('https://lnr.fr.evil.org/match'), 'not_allowlisted')
        self.assertEqual(classify('javascript:alert(1)'), 'missing_or_invalid')
        self.assertEqual(classify('https://top14.lnr.fr/fixture'), 'official_domain_candidate')

    def test_audit_reconciles_counts(self):
        result = audit()
        self.assertEqual(result['inventory_count'], sum(result['fixture_source_classes'].values()))
        self.assertEqual(result['facts_count'], sum(result['fact_source_classes'].values()))
        self.assertEqual(result['inventory_count'] - result['fixture_source_classes'].get('official_domain_candidate', 0),
                         len(result['events_needing_official_fixture_source']))


if __name__ == '__main__':
    unittest.main()
