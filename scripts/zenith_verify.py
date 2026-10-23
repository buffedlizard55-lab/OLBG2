#!/usr/bin/env python3
"""Fail-closed structural, provenance, arithmetic, prose and site-link checks for Zenith."""
from __future__ import annotations
import json,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'zenith'; SITE=ROOT/'zenith'
BAD=re.compile(r'\b(model\w*|verif\w*)\b',re.I); errors=[]; checks=0

def ck(ok,msg):
 global checks; checks+=1
 if not ok: errors.append(msg)

def load(n):return json.loads((DATA/f'{n}.json').read_text())
fixtures=load('fixtures'); matches=load('matches'); lines=load('lines'); picks=load('picks'); preds=load('predictions'); flags=load('flagged'); sources=load('sources')
allowed=set(fixtures['sports']); sids={s['sport'] for s in sources['sports']}
ck(allowed==sids and len(allowed)==15,'sport taxonomy is not exactly the 15 mandated sports')
ck(len(fixtures['fixtures'])==fixtures['count']==len(matches['matches']),'fixture/match counts disagree')
by={m['id']:m for m in matches['matches']}
for m in matches['matches']:
 ck(m['sport'] in allowed,f"{m['id']}: out-of-scope sport")
 ck(m.get('official_fixture_url','').startswith('https://'),f"{m['id']}: missing official fixture source")
 ck(bool(m['facts']),f"{m['id']}: missing captured fact ledger")
 for f in m['facts']:
  ck(f.get('source_url','').startswith('https://'),f"{m['id']}: fact missing official URL")
  ck(bool(f.get('source_key')),f"{m['id']}: fact missing source key")
for m in matches['matches']:
 ck((m['market_count']==0)==(not bool(m['our_selection'])),f"{m['id']}: displayed pick does not match market availability")
for r in lines['lines']:
 ck(r['fixture_id'] in by,f"{r['id']}: orphan line")
 ck(0<r['probability']<1,f"{r['id']}: probability out of bounds")
 ck(r['our_fair_american']==(int(round(-100*r['probability']/(1-r['probability']))) if r['probability']>=.5 else int(round(100*(1-r['probability'])/r['probability']))),f"{r['id']}: fair American arithmetic")
 ck(r['in_user_odds_band']==(-250<=r['our_fair_american']<=10000),f"{r['id']}: band arithmetic")
 ck(r.get('official_fixture_url','').startswith('https://'),f"{r['id']}: line missing official source")
for p in preds['predictions']:
 ck(p['fixture_id'] in by,f"{p['id']}: orphan prediction")
 ck(p['word_count']>=30 and p['word_count']==len(p['text'].split()),f"{p['id']}: word count")
 ck(not BAD.search(p['text']) and not BAD.search(p['headline']),f"{p['id']}: prohibited word")
 ck(p.get('official_fixture_url','').startswith('https://'),f"{p['id']}: no official fixture link")
 ck(bool(p.get('facts')),f"{p['id']}: no fact citation")
 for fact in p['facts']: ck(fact.get('source_url','').startswith('https://'),f"{p['id']}: fact source not HTTPS")
# All JSON site data stays exactly 15 sports and no OLBG quote is interpreted as our price.
allowed_slugs={s['slug'] for s in sources['sports']}
for e in load('olbg_events')['events']:
 ck(e['sport_slug'] in allowed_slugs,f"OLBG event {e['event_id']}: out-of-scope sport")
# HTML link, table shape and source-bearing table-row checks.
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.rows=[];self.current=None;self.inrow=False;self.cellcount=0;self.is_header=False
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='a' and d.get('href'):self.links.append(d['href'])
  if t=='tr':self.inrow=True;self.cellcount=0;self.current=[];self.is_header=False
  if self.inrow and t=='th':self.is_header=True
  if self.inrow and t in ('td','th'):self.cellcount+=1
  if self.inrow and t=='a' and d.get('href','').startswith('https://') and self.current is not None:self.current.append(d['href'])
 def handle_endtag(self,t):
  if t=='tr' and self.inrow:self.rows.append((self.cellcount,self.current or [],self.is_header));self.inrow=False

def check_html():
 for page in SITE.rglob('*.html'):
  parser=Parser();parser.feed(page.read_text(encoding='utf-8'))
  for n,links,is_header in parser.rows:
   if is_header: continue
   ck(n>0,f"{page.relative_to(ROOT)}: empty table row")
   ck(bool(links),f"{page.relative_to(ROOT)}: table row missing official source link")
  for href in parser.links:
   u=urlsplit(href)
   if u.scheme or u.netloc or not u.path: continue
   target=(page.parent/unquote(u.path)).resolve()
   ck(target.is_relative_to(ROOT.resolve()) and target.is_file(),f"{page.relative_to(ROOT)}: broken local link {href}")
check_html()
print(f"Zenith verifier: {checks} assertions, {len(errors)} errors")
for e in errors:print('ERROR',e)
sys.exit(bool(errors))
