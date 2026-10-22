"""Evidence boundary / model / generated-site regression tests (no network)."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from command_model import confidence, originate, quote
from command_seed import build
from command_verify import verify

class CommandTests(unittest.TestCase):
    def test_strict_band_and_calibration(self):
        self.assertEqual(confidence(.71,1/.71),'medium')
        self.assertEqual(confidence(.71,1/.71,calibrated=True),'high')
        self.assertEqual(confidence(.72,1/.72,calibrated=True),'medium')
        self.assertEqual(confidence(.699999,1/.699999,calibrated=True),'medium')
        self.assertEqual(confidence(5/7,1.4,calibrated=True),'high')
    def test_quote_does_not_add_margin(self):
        q=quote(.7)
        self.assertAlmostEqual(q['fair_decimal'],1/.7,places=4)
        self.assertEqual(q['fair_american'],-233)
        self.assertFalse(quote(.715)['in_focus_band'])
        self.assertTrue(quote(.714)['in_focus_band'])
    def test_poisson_symmetry_and_normalization(self):
        team={'gp':10,'gf':30,'ga':30}
        m=originate(team,team)
        self.assertAlmostEqual(m['winner']['home']['probability'],.5)
        self.assertAlmostEqual(sum(q['probability'] for q in m['regulation'].values()),1,places=5)
        self.assertAlmostEqual(m['total']['over']['probability']+m['total']['under']['probability'],1)
        self.assertEqual(m['handicap']['period'],'regulation only')
    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError): quote(1)
        with self.assertRaises(ValueError): originate({'gp':0,'gf':2,'ga':3},{'gp':1,'gf':3,'ga':2})
    def test_inputs_and_blanks_preserved(self):
        result=build(); self.assertEqual(result['counts'],{'rows':48,'originated':7,'high':0})
        for row in result['matches']:
            if not row['rates']:
                self.assertIsNone(row['markets']); self.assertIsNone(row['winner_pick'])
            if row['sport']=='aussie-rules':
                self.assertIsNone(row['date']); self.assertIsNone(row['start_utc']); self.assertIsNone(row['venue'])
            if row['sport']=='greyhounds':
                self.assertIsNone(row['home']); self.assertIsNone(row['away'])
            self.assertNotEqual(row['confidence'],'high')
    def test_no_in_play_picks(self):
        rows=build()['matches']
        live=[r for r in rows if 'live' in r['status'] or 'warming' in r['status']]
        self.assertEqual(len(live),4)
        self.assertTrue(all(r['markets'] is None for r in live))
    def test_no_fabricated_high_narratives(self):
        build()
        p=json.loads((ROOT/'data/command/predictions.json').read_text())
        self.assertEqual(p['predictions'],[])
        self.assertIn('calibration',p['reason'])
    def test_scope_and_exclusions(self):
        sports=json.loads((ROOT/'data/command/sports.json').read_text())
        self.assertEqual(len(sports),17)
        excluded={'football','soccer','boxing','ufc','mma','american-football','hurling','horse-racing','cycling','specials'}
        self.assertFalse({s['slug'] for s in sports}&excluded)
        for row in build()['matches']:
            self.assertIn(row['sport'],{s['slug'] for s in sports})
    def test_site_deterministic_and_links(self):
        subprocess.run([sys.executable,str(ROOT/'scripts/command_build.py')],check=True,capture_output=True)
        before={p.relative_to(ROOT):p.read_bytes() for p in (ROOT/'command').rglob('*.html')}
        subprocess.run([sys.executable,str(ROOT/'scripts/command_build.py')],check=True,capture_output=True)
        self.assertEqual(before,{p.relative_to(ROOT):p.read_bytes() for p in (ROOT/'command').rglob('*.html')})
        self.assertEqual(verify()['local_link_errors'],0)
        self.assertEqual(verify()['pages'],23)
    def test_disclosures_present(self):
        for page in (ROOT/'command').rglob('*.html'):
            text=page.read_text()
            self.assertIn('not a complete live slate',text)
            self.assertIn('Skip to content',text)
            self.assertIn('scope="col"',text)
        self.assertIn('27 of 34',(ROOT/'command/flagged.html').read_text())

if __name__=='__main__': unittest.main()
