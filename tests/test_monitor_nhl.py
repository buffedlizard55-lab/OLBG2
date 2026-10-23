"""Synthetic contract tests, not current NHL evidence or external verification."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from monitor_core import parse_nhl, qualifies, SPORTS
from monitor_collect import fetch_task

AT = '2026-10-23T12:00:00Z'
URL = 'https://api-web.nhle.com/v1/score/2026-10-23'


def sample():
    return {'games': [dict(id=123, gameDate='2026-10-23',
        startTimeUTC='2026-10-24T01:00:00Z', gameState='FUT',
        gameScheduleState='OK', awayTeam={'name': {'default': 'Synthetic Away'}},
        homeTeam={'name': {'default': 'Synthetic Home'}})]}


class NHLContract(unittest.TestCase):
    def test_preserves_source_date_without_inference(self):
        row, = parse_nhl(sample(), 'test-source', AT)
        self.assertEqual(row['date'], '2026-10-23')
        self.assertEqual(row['start_utc'], '2026-10-24T01:00:00Z')
        self.assertEqual(row['name'], 'Synthetic Away @ Synthetic Home')
        self.assertEqual(row['official_url'], 'https://www.nhl.com/gamecenter/123')
        self.assertEqual(row['source_id'], 'test-source')
        for key in ('probability', 'confidence', 'market_price', 'injuries', 'prediction'):
            self.assertIsNone(row[key])
        self.assertFalse(qualifies(row, AT))

    def test_non_upcoming_and_uncertain_schedules_excluded(self):
        for state in ('LIVE', 'CRIT', 'FINAL', 'OFF', 'UNKNOWN', None):
            data = sample(); data['games'][0]['gameState'] = state
            self.assertEqual(parse_nhl(data, 'test', AT), [])
        for schedule in ('PPD', 'SUSP', 'TBD', None):
            data = sample(); data['games'][0]['gameScheduleState'] = schedule
            self.assertEqual(parse_nhl(data, 'test', AT), [])
        data = sample(); data['games'][0]['startTimeUTC'] = AT
        self.assertEqual(parse_nhl(data, 'test', AT), [])

    def test_pregame_future_allowed(self):
        data = sample(); data['games'][0]['gameState'] = 'PRE'
        self.assertEqual(len(parse_nhl(data, 'test', AT)), 1)

    def test_bad_schema_fails_closed(self):
        for data in ({}, {'games': None}, {'games': [None]}, []):
            with self.assertRaises(ValueError): parse_nhl(data, 'test', AT)
        self.assertEqual(parse_nhl({'games': []}, 'test', AT), [])

    def test_bad_candidate_fails_closed(self):
        for field, value in [('id', True), ('id', -1), ('startTimeUTC', None),
                             ('startTimeUTC', '2026-10-24T01:00:00'),
                             ('gameDate', '2026-02-30'), ('awayTeam', {}),
                             ('homeTeam', {'name': {'default': ''}})]:
            data = sample(); data['games'][0][field] = value
            with self.assertRaises(ValueError, msg=field): parse_nhl(data, 'test', AT)
        data = sample(); data['games'].append(copy.deepcopy(data['games'][0]))
        with self.assertRaises(ValueError): parse_nhl(data, 'test', AT)

    def test_endpoint_contract_and_collector_dispatch(self):
        endpoint = next(s[3] for s in SPORTS if s[0] == 'ice-hockey')
        self.assertEqual(endpoint.format(date=AT[:10]), URL)
        class Response:
            status = 200
            url = URL
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return json.dumps(sample()).encode()
        with tempfile.TemporaryDirectory() as folder:
            with patch('monitor_collect.build_opener') as opener:
                opener.return_value.open.return_value = Response()
                result = fetch_task(('test-nhl', 'ice-hockey', 'official', URL), Path(folder), AT)
            self.assertEqual(result['status'], 'parsed')
            self.assertEqual(len(result['events']), 1)
            self.assertTrue((Path(folder) / result['body_path']).exists())
            self.assertTrue(result['sha256'])


if __name__ == '__main__':
    unittest.main()
