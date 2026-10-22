import importlib.util
import unittest
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('evidence_integrity', ROOT/'scripts/evidence_integrity.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EvidenceIntegrityTests(unittest.TestCase):
    def valid(self, **overrides):
        return dict(text=' '.join(['word']*35), probability=.71, confidence='high', fair_american=-245, official_url='https://www.nhl.com/gamecenter/', **overrides)

    def test_clean_record(self):
        self.assertEqual(module.prediction_issues(self.valid()), [])

    def test_low_probability_flag(self):
        row = self.valid(); row['probability'] = .39
        self.assertTrue(any('39.00%' in x for x in module.prediction_issues(row)))

    def test_missing_is_not_zero(self):
        row = self.valid(); del row['probability']
        self.assertTrue(any('no explicit' in x for x in module.prediction_issues(row)))

    def test_band_boundaries(self):
        for odds in [-250, 10000]:
            row = self.valid(); row['fair_american'] = odds
            self.assertEqual(module.prediction_issues(row), [])
        row['fair_american'] = -251
        self.assertTrue(any('outside' in x for x in module.prediction_issues(row)))

    def test_sources_and_escaping(self):
        for value in [None, '', 'javascript:alert(1)', 'https:///foo', 'http://example.com']:
            self.assertFalse(module.https(value))
            self.assertIn('Unverified', module.link(value))
        self.assertIn('&quot;', module.link('https://example.com/?q="'))

    def test_rank_contradiction(self):
        row = self.valid(); row.update(home_record='ATP #26 (1870 pts)', matchup='Lorenzo Musetti vs Tomas Machac', text='World #13 Lorenzo Musetti ' + 'word '*32)
        self.assertTrue(any('ranking contradiction' in x for x in module.prediction_issues(row)))

    def test_report_reproducible(self):
        self.assertEqual(module.audit(), json.loads((ROOT/'evidence/audit.json').read_text()))

    def test_two_official_records_match_stored_fields(self):
        checks = json.loads((ROOT/'evidence/nhl-check.json').read_text())
        rows = json.loads((ROOT/'data/verified/matches.json').read_text())['matches']
        for c in checks['games']:
            row = next(r for r in rows if r['id'] == 'nhl-'+str(c['id']))
            self.assertEqual(row['venue'], c['venue'])
            self.assertEqual(row['time'], c['startTimeUTC'])
            self.assertEqual(row['date'], c['gameDate'])
            self.assertTrue(row['home_summary'].startswith(c['homeRecord']))
            self.assertTrue(row['away_summary'].startswith(c['awayRecord']))

if __name__ == '__main__':
    unittest.main()
