"""Unattended public-source access/discovery checks. Not an exhaustive scraper.
Failures are evidence records, never fabricated fixtures. Run-time output is deployed
as a Pages artifact, not committed by a bot. No credentials or paid feeds required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from monitor_core import SPORTS, OLBGLinks, parse_mlb, stamp

MAX_BYTES = 2_000_000
ERROR_BODY = re.compile(r'(?:<title[^>]*>[^<]*(?:404|access denied)|page not found|# 404 Not Found|captcha|just a moment)', re.I)

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urlsplit(req.full_url), urlsplit(newurl)
        if new.scheme != 'https' or new.hostname not in (old.hostname, 'www.'+old.hostname.removeprefix('www.'), 'stats.unitedrugby.com'):
            raise ValueError('Cross-host redirect requires review: '+newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch_task(task, folder, captured_at):
    key, sport, kind, url = task
    record = dict(id=key,sport=sport,kind=kind,url=url,captured_at=captured_at,
                  method='automated HTTPS GET',status='fetch-failed',http_status=None,
                  sha256=None,body_path=None,excerpt='',note='',events=[],discovery=[])
    try:
        req = Request(url,headers={'User-Agent':'OLBG2Research/1.0 (+https://github.com/buffedlizard55-lab/OLBG2)', 'Accept':'text/html,application/json;q=0.9'})
        with build_opener(SafeRedirect()).open(req, timeout=12) as response:
            body=response.read(MAX_BYTES+1)
            record['http_status']=response.status
            record['final_url']=response.url
        if len(body)>MAX_BYTES:
            raise ValueError('Response exceeds capture limit; not parsed')
        text=body.decode('utf-8',errors='replace')
        record['sha256']=hashlib.sha256(body).hexdigest()
        filename=key+'.txt'
        (folder/filename).write_bytes(body)
        record['body_path']=filename
        record['status']='soft-error' if ERROR_BODY.search(text) else 'fetched-unparsed'
        record['excerpt']=re.sub(r'<[^>]*>', ' ', text[:1200]).strip()[:350]
        if record['status']=='soft-error':
            record['note']='Error/challenge body, not fixture evidence. No attempt to bypass it.'
        elif kind=='olbg':
            parser=OLBGLinks(sport,url); parser.feed(text)
            record['discovery']=list(parser.events.values())
            for d in record['discovery']: d['source_id']=key
            record['status']='discovery-only'
            record['note']=f'{len(parser.events)} distinct event links; no date, odds, status or complete pagination claim. Load-more/API routes are not reverse-engineered.'
        elif sport=='baseball':
            record['events']=parse_mlb(json.loads(text),key,captured_at)
            record['status']='parsed'
            record['note']='Official MLB schedule parsed; OLBG mapping and betting inputs are not auto-confirmed.'
        else:
            record['note']='Response archived for review. No trusted structured fixture adapter implemented for this source.'
    except (OSError, ValueError, KeyError, TypeError) as exc:
        record['status']='http-error' if isinstance(exc,HTTPError) else 'fetch-failed'
        record['http_status']=getattr(exc,'code',record['http_status'])
        record['note']=str(exc)[:350]
    return record

def collect(output, now=None):
    at=now or datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    stamp(at)
    output.mkdir(parents=True,exist_ok=True)
    captures=output/'captures'; captures.mkdir(exist_ok=True)
    tasks=[]
    for slug,_,hubs,official in SPORTS:
        tasks.append(('runtime-'+slug,slug,'official',official.format(date=at[:10])))
        for path,num in hubs:
            tasks.append(('runtime-olbg-'+str(num),slug,'olbg',f'https://www.olbg.com/betting-tips/{path}/{num}'))
    with ThreadPoolExecutor(max_workers=3) as pool:
        records=list(pool.map(lambda t:fetch_task(t,captures,at),tasks))
    result=dict(schema_version=1,generated_at=at,sources=records,
                events=[e for s in records for e in s['events']],
                discovery=[e for s in records for e in s['discovery']])
    # Atomic ledger, even if all remote sources fail. A failed fetch never changes seed evidence dates.
    path=output/'latest.json'; temp=output/'latest.tmp'
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); temp.replace(path)
    print(json.dumps({'attempts':len(records),'official_fixtures':len(result['events']),
                      'olbg_links':len(result['discovery']),'failed':sum(s['status'] in ('fetch-failed','http-error','soft-error') for s in records)}))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,default=Path('data/monitor/runtime')); p.add_argument('--now')
    args=p.parse_args(); collect(args.output,args.now)
