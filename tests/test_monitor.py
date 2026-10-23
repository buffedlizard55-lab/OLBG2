"""Monitor tests: structural integrity, not invented external verification."""
import copy
import hashlib
import json
import math
import sys
import tempfile
import unittest
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import monitor_core as core
import monitor_build as build
import monitor_collect as collect

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.rows=[];self.row=None;self.isdata=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr': self.row=[];self.isdata=False
        if tag=='td': self.isdata=True
        if 'id' in a:self.ids.add(a['id'])
        for key in ('href','src'):
            if a.get(key):
                self.links.append(a[key])
                if self.row is not None:self.row.append(a[key])
    def handle_endtag(self,tag):
        if tag=='tr' and self.row is not None:
            self.rows.append((self.isdata,self.row));self.row=None

class MonitorMath(unittest.TestCase):
    def test_band_is_observed_price_not_fair_probability(self):
        self.assertTrue(core.in_price_band(-250));self.assertTrue(core.in_price_band(10000))
        for x in [-251,10001,0,99,-99,None,math.nan]: self.assertFalse(core.in_price_band(x))
        self.assertAlmostEqual(core.implied(-250),5/7)
        self.assertAlmostEqual(core.implied(10000),1/101)
    def test_american_roundtrip(self):
        for p in [.01,.2,.5,.7,.8,.999]: self.assertAlmostEqual(core.implied(core.american(p)),p)
        for p in [0,1,-1,math.nan,math.inf]:
            with self.assertRaises(ValueError):core.american(p)
    def test_log5_independently_recomputed(self):
        h,a=103/162,98/162
        p=h*(1-a)/(h*(1-a)+a*(1-h))
        self.assertAlmostEqual(core.log5(103,59,98,64),p)
        self.assertAlmostEqual(core.log5(98,64,103,59),1-p)
        self.assertAlmostEqual(core.log5(90,72,90,72),.5)
        with self.assertRaises(ValueError):core.log5(0,0,10,2)
    def test_no_probability_no_label_and_uncalibrated_never_high(self):
        self.assertIsNone(core.confidence(None))
        for p in [.3,.7,.99]:self.assertEqual(core.confidence(p),'low')
        self.assertEqual(core.confidence(.65,True),'medium')
    def candidate(self):
        return dict(id='test-1',sport='baseball',probability=.8,confidence='high',calibrated=True,
                    fixture_status='confirmed',olbg_status='matched',status='scheduled',
                    captured_at='2026-10-23T15:00:00Z',start_utc='2026-10-24T00:00:00Z',
                    market_price=-200,market_price_source='https://example.com/test-only',market_price_at='2026-10-23T15:00:00Z')
    def test_gate_all_requirements(self):
        r=self.candidate();now='2026-10-23T16:00:00Z'
        self.assertTrue(core.qualifies(r,now)) # fair -400 must not incorrectly reject an observed -200
        for key,value in [('market_price',None),('market_price',-300),('market_price_source',None),('calibrated',False),('probability',.69),('start_utc',None),('status','completed'),('fixture_status','unverified'),('olbg_status','unverified'),('captured_at','2026-10-22T15:00:00Z'),('market_price_at','2026-10-22T15:00:00Z'),('captured_at','2026-10-24T15:00:00Z')]:
            other=dict(r);other[key]=value
            self.assertFalse(core.qualifies(other,now),(key,value))
        self.assertFalse(core.qualifies(r,'2026-10-24T00:00:00Z'))
    def test_unique_events_not_selections_and_topfive_limit(self):
        rows=[]
        for i in range(9):
            r=self.candidate();r['id']='test-'+str(i);rows.extend([r,dict(r)])
        ranked=core.top_five(rows,'2026-10-23T16:00:00Z')
        self.assertEqual(len(ranked['baseball']),5)
        self.assertEqual(len({r['id'] for r in ranked['baseball']}),5)
        self.assertEqual(core.top_five(rows,'2026-10-23T16:00:00Z',today=True)['baseball'],[])
    def test_freshness_boundaries(self):
        self.assertTrue(core.fresh('2026-10-23T10:00:00Z','2026-10-23T16:00:00Z'))
        self.assertFalse(core.fresh('2026-10-23T09:59:59Z','2026-10-23T16:00:00Z'))
        self.assertFalse(core.fresh('2026-10-23T17:00:00Z','2026-10-23T16:00:00Z'))
        with self.assertRaises(ValueError):core.stamp('2026-10-23T16:00:00')

class MonitorParsers(unittest.TestCase):
    def test_olbg_dedup_scope_no_odds_inference(self):
        p=core.OLBGLinks('baseball','https://www.olbg.com/betting-tips/Baseball/12')
        p.feed('<a href="/betting-tips/Baseball/MLB/X/12?event_id=42">A @ B</a><a href="/betting-tips/Baseball/MLB/X/12?event_id=42">81%</a><a href="https://evil.example/12?event_id=43">Bad</a><a href="/betting-tips/Football/1?event_id=44">Soccer</a>')
        self.assertEqual(set(p.events),{'42'})
        self.assertEqual(p.events['42']['label'],'A @ B')
        self.assertIsNone(p.events['42']['probability']);self.assertIsNone(p.events['42']['market_price'])
    def test_gaelic_both_disciplines_one_category(self):
        p=core.OLBGLinks('gaelic-sports','https://www.olbg.com/')
        p.feed('<a href="/betting-tips/Hurling/26?event_id=5">Hurling</a><a href="/betting-tips/Gaelic_Football/25?event_id=6">Football</a>')
        self.assertEqual(len(p.events),2)
        self.assertEqual(len(core.SPORTS),15)
        self.assertNotIn('esports',core.SPORT_MAP);self.assertNotIn('aussie-rules',core.SPORT_MAP)
    def payload(self):
        return {'totalGames':1,'dates':[{'games':[{'gamePk':42,'officialDate':'2026-10-23','gameDate':'2026-10-24T00:00:00Z','status':{'abstractGameState':'Preview','detailedState':'Scheduled','startTimeTBD':False},'teams':{'away':{'team':{'name':'Away'}},'home':{'team':{'name':'Home'}}}}]}]}
    def test_mlb_calendar_date_distinct_from_utc(self):
        r=core.parse_mlb(self.payload(),'fixture-source','2026-10-23T16:00:00Z')[0]
        self.assertNotEqual(r['date'],r['start_utc'][:10]);self.assertIsNone(r['probability'])
        self.assertIsNone(r['injuries']);self.assertEqual(r['olbg_status'],'unverified')
    def test_mlb_excludes_tbd_started_postponed_complete(self):
        for key,value in [('abstractGameState','Final'),('startTimeTBD',True),('detailedState','Postponed')]:
            p=self.payload();p['dates'][0]['games'][0]['status'][key]=value
            self.assertEqual(core.parse_mlb(p,'source','2026-10-23T16:00:00Z'),[])
        self.assertEqual(core.parse_mlb(self.payload(),'source','2026-10-24T00:00:00Z'),[])
        with self.assertRaises(ValueError):core.parse_mlb({'message':'404'},'source','2026-10-23T16:00:00Z')
    def test_transport_failure_is_a_record_not_fake_data(self):
        with tempfile.TemporaryDirectory() as t,patch.object(collect,'build_opener',side_effect=OSError('blocked')):
            r=collect.fetch_task(('test','baseball','official','https://statsapi.mlb.com/api/v1/schedule'),Path(t),'2026-10-23T16:00:00Z')
        self.assertEqual(r['status'],'fetch-failed');self.assertEqual(r['events'],[]);self.assertIsNone(r['sha256'])
    def test_soft_404_and_challenge_detection(self):
        for body in ['<title>Error404</title>','We are sorry!Page not found','<title>Just a moment</title>']:
            self.assertIsNotNone(collect.ERROR_BODY.search(body))
    def test_redirect_refuses_unrelated_hosts(self):
        req=collect.Request('https://www.olbg.com/betting-tips')
        with self.assertRaises(ValueError):collect.SafeRedirect().redirect_request(req,None,302,'',{},'http://evil.example/x')

class MonitorPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=build.load()
    def test_evidence_integrity(self): self.assertTrue(build.validate(self.data))
    def test_gaelic_extracts_have_separate_source_attribution(self):
        sources={s['id']:s for s in self.data['sources']}
        self.assertIn('St Finbarrs',sources['olbg-25']['excerpt'])
        self.assertNotIn('Ballyhale',sources['olbg-25']['excerpt'])
        self.assertIn('Ballyhale',sources['olbg-26']['excerpt'])
        self.assertNotIn('St Finbarrs',sources['olbg-26']['excerpt'])
    def test_modified_extract_rejected(self):
        d=copy.deepcopy(self.data);d['sources'][0]['excerpt']+='invented'
        with self.assertRaises(AssertionError):build.validate(d)
    def test_24_official_rows_19_olbg_pairings(self):
        self.assertEqual(len(self.data['events']),24)
        self.assertEqual(sum(bool(r['olbg_url']) for r in self.data['events']),19)
        self.assertEqual(sum(r.get('probability') is not None for r in self.data['events']),1)
    def test_unknown_values_stay_null(self):
        for r in self.data['events']:
            self.assertIsNone(r['market_price']);self.assertIsNone(r['injuries'])
            if r['sport'] not in ('basketball','baseball'):self.assertIsNone(r['start_utc'])
        self.assertFalse(any(core.top_five(self.data['events'],self.data['captured_at']).values()))
    def test_nba_utc_conversions(self):
        from zoneinfo import ZoneInfo
        for r in self.data['events']:
            if r['sport']=='basketball':
                dt=datetime.strptime(r['date']+' '+r['display_time'].replace(' ET',''),'%Y-%m-%d %I:%M %p').replace(tzinfo=ZoneInfo('America/New_York'))
                self.assertEqual(dt,core.stamp(r['start_utc']))
    def test_prediction_exactly_separated_from_high(self):
        for r in self.data['events']:
            if r['prediction']:
                self.assertGreaterEqual(len(r['prediction'].split()),30)
                self.assertNotRegex(r['prediction'].lower(),r'\b(model|verified)\b')
                self.assertEqual(r['confidence'],'low')
                self.assertTrue(r['prediction_source_ids'])
    def test_rebuild_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);build.build(folder)
            for page in folder.rglob('*'):
                if page.is_file():self.assertEqual(page.read_bytes(),(ROOT/'monitor'/page.relative_to(folder)).read_bytes(),str(page))
    def test_pages_links_and_every_data_row_has_https_source(self):
        pages=list((ROOT/'monitor').rglob('*.html'))
        self.assertEqual(len(pages),22)
        for page in pages:
            p=Links();p.feed(page.read_text())
            for isdata,row in p.rows:
                if isdata:self.assertTrue(any(urlsplit(x).scheme=='https' for x in row),str(page))
            for href in p.links:
                u=urlsplit(href)
                if u.scheme or u.netloc:continue
                target=(page.parent/unquote(u.path)).resolve() if u.path else page
                self.assertTrue(target.is_file(),f'{page}: {href}')
                if u.fragment and target.suffix=='.html':
                    q=Links();q.feed(target.read_text());self.assertIn(u.fragment,q.ids)
    def test_javascript_filters_and_stale_guard_no_browser_api_calls(self):
        js=(ROOT/'monitor/app.js').read_text()
        for text in ['data-search','toLocaleLowerCase','row.hidden','age>6','start<=now','setInterval']:
            self.assertIn(text,js)
        self.assertNotIn('fetch(',js)
    def test_scheduled_collection_and_safe_publication(self):
        text=(ROOT/'.github/workflows/deploy-pages.yml').read_text()
        self.assertIn('cron: "17 */6 * * *"',text)
        self.assertIn('needs: validate',text)
        self.assertIn('python scripts/monitor_collect.py',text)
        self.assertIn('--runtime data/monitor/runtime/latest.json',text)
        self.assertNotIn('git push',text)
    def test_runtime_failure_never_refreshes_seed(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'latest.json'
            f.write_text(json.dumps({'generated_at':'2026-10-24T16:00:00Z','sources':[],'events':[],'discovery':[]}))
            combined=build.load(f)
        self.assertEqual(combined['captured_at'],self.data['captured_at'])
        self.assertEqual(combined['events'],self.data['events'])
        self.assertFalse(any(core.top_five(combined['events'],combined['generated_at']).values()))
    def test_no_legacy_data_read_by_monitor(self):
        text=(ROOT/'scripts/monitor_build.py').read_text()
        self.assertNotIn('data/verified',text);self.assertNotIn('data/daily',text)

if __name__=='__main__':unittest.main()
