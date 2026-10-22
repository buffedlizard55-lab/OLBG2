#!/usr/bin/env python3
"""Structural validation only. Does not fetch or certify external claims."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]
OFFICIAL={'www.atptour.com','stats.swehockey.se','api-web.nhle.com','api.nhle.com','statsapi.mlb.com','www.nrl.com','www.gbgb.org.uk','www.afl.com.au'}

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        if tag in ('a','link','script','img'):
            ref=attrs.get('href') or attrs.get('src')
            if ref: self.refs.append(ref)


def verify():
    data=json.loads((ROOT/'data/command/matches.json').read_text())
    rows=data['matches']; ids=set(); errors=[]
    for r in rows:
        if r['id'] in ids: errors.append('Duplicate '+r['id'])
        ids.add(r['id'])
        u=urlsplit(r['source_url'])
        if u.scheme!='https' or u.hostname not in OFFICIAL: errors.append('Unrecognized source '+r['id'])
        if r['markets'] is None and any(r[k] is not None for k in ['winner_pick','confidence']): errors.append('Unsupported tip '+r['id'])
        if r['confidence']=='high': errors.append('Uncalibrated high '+r['id'])
    pages=list((ROOT/'command').rglob('*.html'))
    for page in pages:
        parser=Links(); parser.feed(page.read_text())
        for ref in parser.refs:
            url=urlsplit(ref)
            if url.scheme or url.netloc: continue
            target=(page.parent/unquote(url.path)).resolve() if url.path else page
            if target.is_dir(): target/='index.html'
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append(f'{page.relative_to(ROOT)} -> {ref}'); continue
            if url.fragment and target.suffix=='.html':
                p=Links(); p.feed(target.read_text())
                if unquote(url.fragment) not in p.ids: errors.append('Missing anchor '+ref)
    if errors: raise ValueError('\n'.join(errors))
    return {'pages':len(pages),'rows':len(rows),'local_link_errors':0,'external_facts_checked_by_this_script':0}

if __name__=='__main__': print(verify())
