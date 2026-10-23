"""Deterministic static monitor with runtime freshness protection and explicit abstention."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit
from monitor_core import SPORTS, SPORT_MAP, MAX_AGE_HOURS, stamp, fresh, top_five, american, log5

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/monitor'
OUT=ROOT/'monitor'

def esc(x): return html.escape('' if x is None else str(x),quote=True)
def link(url,label):
    if not url: return ''
    if urlsplit(url).scheme != 'https': raise ValueError('HTTPS sources only: '+url)
    return f'<a href="{esc(url)}" rel="noopener noreferrer">{esc(label)} ↗</a>'
def pct(x): return '' if x is None else f'{100*x:.1f}%'
def odd(x): return '' if x is None else f'{x:+.1f}'
def badge(text,kind='neutral'): return f'<span class="badge {kind}">{esc(text)}</span>'

def load(runtime=None):
    seed=json.loads((DATA/'seed.json').read_text())
    seed['generated_at']=seed['captured_at']
    seed['runtime_status']='No automated refresh in this artifact; session capture only.'
    if runtime and runtime.exists():
        rt=json.loads(runtime.read_text())
        if stamp(rt['generated_at']) >= stamp(seed['captured_at']):
            seed['generated_at']=rt['generated_at']
            seed['sources']+=rt['sources']
            rows={r['id']:r for r in seed['events']}
            for r in rt['events']: rows[r['id']]=r
            seed['events']=list(rows.values())
            seed['discovery']+=rt['discovery']
            seed['runtime_status']=f"Automated attempt {rt['generated_at']}. {len(rt['events'])} official fixture rows parsed (MLB / NHL adapters); other source bodies and discovery links require review. An attempted refresh is not successful verification."
    return seed

def validate(data):
    sources={s['id']:s for s in data['sources']}
    assert len(sources)==len(data['sources']), 'duplicate source ids'
    ids=set()
    for s in data['sources']:
        assert urlsplit(s['url']).scheme=='https'
        stamp(s['captured_at'])
        if s['method'].startswith('agent'):
            assert hashlib.sha256(s['excerpt'].encode()).hexdigest()==s['sha256'],s['id']
    for r in data['events']:
        assert r['id'] not in ids, 'duplicate event'
        ids.add(r['id'])
        assert r['sport'] in SPORT_MAP
        assert r['source_id'] in sources and sources[r['source_id']]['kind']=='official'
        assert sources[r['source_id']]['status'] in ('read','read-partial','parsed')
        assert r['official_url'] and r['name'] and r['date']
        if r['start_utc']: stamp(r['start_utc'])
        if r.get('probability') is not None:
            assert r.get('inputs') and r['inputs']['source_id'] in sources
            assert sources[r['inputs']['source_id']]['kind']=='official'
            assert 0<r['probability']<1
            assert abs(american(r['probability'])-r['fair_american'])<1e-9
            inp=r['inputs']
            assert abs(log5(inp['home_wins'],inp['home_losses'],inp['away_wins'],inp['away_losses'])-r['probability'])<1e-12
        if r.get('market_price') is None:
            assert r.get('confidence') != 'high', 'No published high label without an observed quote'
        if r.get('prediction'):
            assert len(r['prediction'].split())>=30
            assert not {'model','verified'} & {w.lower().strip('.,;:!?') for w in r['prediction'].split()}
            assert all(i in sources and sources[i]['kind']=='official' for i in r['prediction_source_ids'])
    return True

def table(headers,rows,caption,filterable=False):
    controls='<label class="search">Filter this table <input type="search" data-search placeholder="Search a sport, team, status…"></label><p class="results" aria-live="polite"></p>' if filterable else ''
    return f'<section class="table-section">{controls}<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(caption)}"><table><caption>{esc(caption)}</caption><thead><tr>'+''.join(f'<th scope="col">{esc(h)}</th>' for h in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><p class="empty-filter" hidden>No rows match. Try a different search.</p></section>'

def shell(title,body,data,active='index',prefix=''):
    nav=[('index','Overview'),('matches','Fixtures'),('picks','Picks & top five'),('markets','Markets'),('sources','Sources'),('flagged','Flagged for Review'),('methodology','Methodology')]
    menu=''.join(f'<a href="{prefix}{key}.html"'+(' aria-current="page"' if active==key else '')+f'>{label}</a>' for key,label in nav)
    sportlinks=''.join(f'<a href="{prefix}sports/{slug}.html"'+(' aria-current="page"' if active==slug else '')+f'>{name}</a>' for slug,name,_,_ in SPORTS)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · OLBG2 Research</title><meta name="description" content="Evidence-first research for 15 sports. Official fixtures, transparent fair lines and clearly flagged gaps."><link rel="stylesheet" href="{prefix}style.css"><script src="{prefix}app.js" defer></script></head><body>
<a class="skip" href="#main">Skip to content</a><aside class="sidebar"><a class="brand" href="{prefix}index.html"><span class="brand-mark">O</span> OLBG<span class="brand-two">2</span></a><p class="brand-sub">INDEPENDENT RESEARCH</p><nav aria-label="Research pages">{menu}</nav><details class="sport-nav" open><summary>15 covered sports</summary><nav aria-label="Sport categories">{sportlinks}</nav></details><a class="archive-link" href="{prefix}../archive.html">Earlier research archive ↗</a></aside>
<div class="workspace"><header class="topbar"><span>RESEARCH DESK <span class="separator">/</span> {esc(title)}</span>{badge('Partial coverage','warn')}</header><main id="main"><div class="capture"><span class="status-dot"></span> Session evidence: {esc(data['captured_at'])} <span class="freshness" data-captured="{esc(data['captured_at'])}">Dated snapshot — check age</span></div>{body}<section class="refresh-note"><h2>Refresh & evidence status</h2><p>{esc(data['runtime_status'])}</p><p>Freshness limit: {MAX_AGE_HOURS} hours. Started events and stale captures cannot qualify for a new recommendation. This page remains readable without JavaScript; timestamps above are authoritative.</p></section></main><footer>Independent research, not affiliated with OLBG. Estimates are not guarantees. No automatic wagers. 18+ · <a href="{prefix}flagged.html">Read the limitations</a> · <a href="{prefix}../research/monitor-8226c94a.md">Audit notes</a></footer></div></body></html>'''

def sources_for(r,sources):
    s=sources[r['source_id']]
    extra=''
    if r.get('inputs'): extra='<br>'+link(sources[r['inputs']['source_id']]['url'],'Official inputs')
    return link(r['official_url'],'Official fixture')+'<br>'+link(s['url'],'Capture source')+extra+('<br>'+link(r['olbg_url'],'OLBG listing') if r.get('olbg_url') else '')

def fixture_table(events,sources):
    rows=[]
    for r in sorted(events,key=lambda r:(r['date'],r.get('start_utc') or '99',r['name'])):
        rows.append(f'<tr data-start="{esc(r.get("start_utc"))}" data-captured="{esc(r["captured_at"])}"><td><strong>{esc(r["name"])}</strong><small>{esc(SPORT_MAP[r["sport"]][1])}</small></td><td>{esc(r["date"])}<small>Official calendar date</small>{esc(r["display_time"])}</td><td>{esc(r.get("start_utc"))}<small>{"Normalized from ET" if r["sport"]=="basketball" else ""}</small></td><td>{badge("Pairing / date sourced","good")}<small>{esc(r["captured_at"])}</small><span class="event-state">{esc(r["status"])}</span></td><td>{badge("OLBG participants matched" if r.get("olbg_url") else "OLBG membership unverified", "neutral" if r.get("olbg_url") else "warn")}<small>{esc(r["note"])}</small></td><td>{sources_for(r,sources)}</td></tr>')
    return table(['Fixture / sport','Source date & time','Start UTC','Evidence','Eligibility & gaps','Sources'],rows,'Official-source fixture inventory · empty UTC cells mean the timezone is unverified',True)

def coverage(data):
    rows=[]
    eligible=top_five(data['events'],data['generated_at'])
    for slug,name,hubs,url in SPORTS:
        events=[r for r in data['events'] if r['sport']==slug]
        count=len(events); picks=len(eligible[slug])
        rows.append(f'<tr><td><a href="sports/{slug}.html"><strong>{name}</strong></a></td><td>{count}</td><td>{sum(bool(r.get("olbg_url")) for r in events)}</td><td>{picks} / 5</td><td>{badge("Shortfall: "+str(5-picks),"warn")}</td><td>{link(url.format(date=data["captured_at"][:10]),"Official source")}<br>{link(f"https://www.olbg.com/betting-tips/{hubs[0][0]}/{hubs[0][1]}","OLBG hub")}</td></tr>')
    return table(['Sport','Sourced fixtures','OLBG pairings','Qualified picks / target','Daily target status','Sources'],rows,'All 15 requested categories · counts are this partial capture, not real-world totals',True)

def overview(data,sources):
    rows=data['events']; matches=sum(bool(r.get('olbg_url')) for r in rows)
    qualified=sum(len(x) for x in top_five(rows,data['generated_at']).values())
    lined=sum(r.get('probability') is not None for r in rows)
    return f'''<section class="hero"><p class="eyebrow">FACTS FIRST. PICKS SECOND.</p><h1>The daily research desk.</h1><p class="lede">One clear view of the 15 sports you follow. Official fixtures, independent calculations, and the evidence still missing — kept separate.</p><div class="actions"><a class="button primary" href="matches.html">Explore fixtures →</a><a class="button" href="flagged.html">See what needs review</a></div></section>
<div class="metrics"><article><span>SPORTS IN SCOPE</span><strong>15</strong><small>Including both Gaelic disciplines</small></article><article><span>SOURCED FIXTURE ROWS</span><strong>{len(rows)}</strong><small>{matches} OLBG participant matches</small></article><article><span>ORIGINATED MATCHES</span><strong>{lined}</strong><small>Experimental, low confidence</small></article><article><span>HIGH-CONFIDENCE PICKS</span><strong>{qualified}</strong><small>No quota-filling selections</small></article></div>
<section class="summary"><div><p class="eyebrow">EXECUTIVE SUMMARY</p><h2>No high-confidence picks cleared.</h2><p>No selection has the complete evidence needed for a high-confidence recommendation in today’s or the upcoming slate. Missing offered odds, insufficient inputs and uncertain times are not filled with assumptions.</p><a href="picks.html">View the top-five shortfall by sport →</a></div><div class="summary-side"><h3>What is ready</h3><ul><li>Row-level official source links</li><li>Exact 15-category navigation</li><li>Separate fair and bookmaker prices</li><li>Visible freshness and review flags</li></ul><p><strong>Not ready:</strong> full OLBG inventory, every market, and five defensible predictions per sport.</p></div></section>
<h2>Coverage at a glance</h2><p class="muted">A zero means no eligible pick in our evidence — not that the sport has no matches. “Today” in the pick gate means the UTC calendar day of the refresh; official local dates remain visible.</p>{coverage(data)}'''

def picks(data,sources):
    blocks=[]
    for r in data['events']:
        if r.get('prediction'):
            blocks.append(f'<article class="prediction">{badge("Experimental • low confidence","warn")}<h3>{esc(r["name"])}</h3><p class="selection">Selection: {esc(r.get("selection"))}</p><p>{esc(r["prediction"])}</p><div class="prediction-meta">Calculated win probability: {pct(r["probability"])} · Fair American: {odd(r["fair_american"])} · Not a bookmaker quote</div><p>{sources_for(r,sources)}</p><p class="muted">No high-confidence designation. Recent match history and injuries remain unverified; no absence of injuries is asserted.</p></article>')
    return '<p class="eyebrow">QUALITY OVER QUOTA</p><h1>Picks & the daily top five</h1><div class="notice"><strong>No qualified high-confidence picks.</strong> Five per sport is a target, not permission to invent evidence. This page separates exploratory analysis from recommendations.</div>'+coverage(data)+'<h2>Exploratory selection — not high confidence</h2>'+(''.join(blocks) or '<p>No current exploratory selection has sufficient inputs.</p>')

def markets(data,sources):
    rows=[]
    for r in data['events']:
        if r['sport']=='baseball':
            p=r.get('probability')
            for selection,prob in [(r['selection'],p),(r['other_selection'],1-p)] if p is not None else [('Winner — research pending',None)]:
                rows.append(f'<tr><td>{esc(r["name"])}</td><td>Money Line</td><td>{esc(selection)}</td><td>{pct(prob)}</td><td>{odd(None if prob is None else american(prob))}</td><td></td><td>{badge("Low • experimental" if prob else "Unverified","warn")}</td><td>{sources_for(r,sources)}</td></tr>')
            for market in ('Run Line','Game Totals'):
                observed=next((m for m in r.get('observed_markets',[]) if m['name']==market),None)
                label=observed['line']+' observed at session capture; prices withheld' if observed else 'Market line unverified'
                rows.append(f'<tr><td>{esc(r["name"])}</td><td>{market}</td><td>{label}</td><td></td><td></td><td></td><td>{badge("Unverified inputs","warn")}</td><td>{sources_for(r,sources)}</td></tr>')
    inventory=table(['Fixture','Market','Selection / observed line','Our probability','Fair American','Bookmaker American','Confidence / status','Sources'],rows,'Empty cells are unverified, not zero; no bookmaker odds captured',True)
    # A study checklist, explicitly not a claim that each sport offers each market.
    checkrows=[]
    for slug,name,hubs,url in SPORTS:
        checkrows.append(f'<tr><td>{name}</td><td>Winner / handicap / total / event-specific markets</td><td>{"Money Line, Run Line ±1.50, Game Totals 6.50: event page inspected" if slug=="baseball" else "Hub discovery only; exhaustive event-market review incomplete"}</td><td>{link(url.format(date=data["captured_at"][:10]),"Official source")}<br>{link(f"https://www.olbg.com/betting-tips/{hubs[0][0]}/{hubs[0][1]}","OLBG hub")}</td></tr>')
    return '<p class="eyebrow">FAIR IS NOT OFFERED</p><h1>Markets & independent lines</h1><p class="lede">Calculated lines are our estimates, never official sporting facts or available betting prices. We do not manufacture handicap or total prices from a win percentage.</p>'+inventory+'<h2>Investigation checklist</h2><p>The market families below are research tasks, not assertions that every event offers those markets.</p>'+table(['Sport','Families to investigate','Progress','Sources'],checkrows,'Market investigation status')

def source_page(data):
    rows=[]
    for s in data['sources']:
        body=''
        if s.get('body_path'): body=f'<br><a href="../data/monitor/runtime/captures/{esc(s["body_path"])}">HTTP capture</a>'
        rows.append(f'<tr id="{esc(s["id"])}"><td><strong>{esc(s["id"])}</strong><small>{esc(s["kind"])} · {esc(s["sport"])}</small></td><td>{badge(s["status"],"good" if s["status"] in ("read","parsed") else "warn")}<small>{esc(s["captured_at"])}</small></td><td>{esc(s["excerpt"])}<small>{esc(s["note"])}</small></td><td>{link(s["url"],"Source")}<small>{esc(s["method"])}</small>{body}</td></tr>')
    return '<p class="eyebrow">PROVENANCE, NOT A CHECKMARK</p><h1>Source ledger</h1><p>A URL alone is not verification. Each record says what was actually read and what it supports. Tool-level success can still return a 404 body. Session evidence is a selected field transcription, not original response bytes.</p><p><a href="../data/monitor/seed.json">Download the complete evidence JSON</a> · Includes extract hashes and null fields.</p>'+table(['Source ID','Result & capture','Selected evidence / limitation','Link & method'],rows,'Every source attempt and selected extract',True)

def flags(data,sources):
    rows=[f'<tr id="collector-nhl-review"><td>COL-NHL</td><td><strong>NHL adapter requires live-source review</strong><p>Schedule parsing is covered by synthetic contract tests, not a new live capture. Official-site access was restricted during this code audit. Only successful runtime responses can supply new fixture facts; OLBG matching, offered odds, form and injuries remain unconfirmed. <a href="../research/collector-6cd8cc4c.md">Read the audit</a>.</p></td><td>{badge("Needs review","warn")}</td><td>{link("https://api-web.nhle.com/v1/score/"+data["generated_at"][:10],"Official check target")}</td></tr>']
    for f in data['flags']:
        rows.append(f'<tr id="{f["id"]}"><td>{f["id"]}</td><td><strong>{esc(f["title"])}</strong><p>{esc(f["detail"])}</p></td><td>{badge("Needs review","warn")}</td><td>{link(f["url"],"Evidence / source")}</td></tr>')
    for slug,name,_,official in SPORTS:
        relevant=[s for s in data['sources'] if s['sport']==slug and s['kind']=='official']
        details='; '.join(s['id']+': '+s['status'] for s in relevant)
        rows.append(f'<tr id="coverage-{slug}"><td>{esc(name)}</td><td>Five qualified picks not achieved. {esc(details)}. Missing prices, form, history and injuries stay blank.</td><td>{badge("Coverage shortfall","warn")}</td><td>{link(official.format(date=data["captured_at"][:10]),"Official source")}</td></tr>')
    discovery=[]
    for d in data['discovery']:
        s=sources[d['source_id']]; official=SPORT_MAP[d['sport']][3].format(date=data['captured_at'][:10])
        discovery.append(f'<tr><td>{esc(SPORT_MAP[d["sport"]][1])}</td><td>{esc(d["label"])}</td><td></td><td></td><td>{badge("Unverified fixture","warn")}</td><td>{link(d.get("olbg_url") or s["url"],"OLBG reported listing")}<br>{link(official,"Official check target")}</td></tr>')
    return '<p class="eyebrow">OPEN AND NON-BLOCKING</p><h1>Flagged for Review</h1><p>Missing evidence is published here, not silently filled. These flags do not prevent a functioning research site from being published.</p>'+table(['ID / category','Finding','Status','Source'],rows,'Repository and source irregularities',True)+'<h2>Unconfirmed OLBG discoveries</h2><p>Reported labels below are OLBG text, not confirmed fixture facts. Official-name and UTC cells remain blank. These are selected examples and automated links, not the complete OLBG inventory.</p>'+table(['Sport','OLBG-reported label','Official name','Start UTC','Status','Sources'],discovery,'Unconfirmed discoveries · not eligible picks',True)

METHODOLOGY='''<p class="eyebrow">REPRODUCIBLE AND EXPLICIT</p><h1>How the desk works</h1>
<section class="prose"><h2>1. Exact scope, no silent expansion</h2><p>The 15 requested categories are the only categories in this monitor. Gaelic Sports includes Gaelic Football and Hurling, with no automatic equivalence between the disciplines. The historical 17-sport desks are archived separately.</p>
<h2>2. OLBG discovery is not official confirmation</h2><p>Public hubs expose event links with numeric event_id parameters. The collector extracts those links, deduplicated within a sport. The first-page/load-more inventory is partial; JavaScript pagination and private APIs have not been certified. No access controls are bypassed. An OLBG vote share describes tipster support, not a win probability.</p><p>Fixture names, dates, clocks and IDs are checked against the governing body. A generic official page that does not contain a fixture is only a check target. Relative OLBG dates are not converted to UTC. NBA clocks explicitly labelled ET are normalized using America/New_York; all other ambiguous clocks remain unconverted.</p>
<h2>3. Source facts versus derived estimates</h2><p>Only MLB Game 1 has an experimental originated moneyline. For home regular-season win fraction H and away fraction A, P(home) = (H − H×A) / (H + A − 2×H×A). The away probability is 1 − P(home). The inputs are the official 2026 records, 103–59 and 98–64. No bookmaker odds or tip shares enter the calculation.</p><p>This log5 baseline assumes comparable opposition and a neutral venue. It is not calibrated and does not account for starters, injuries, postseason form or home advantage. Its confidence is low regardless of the numeric output. No asserted factual values are invented. Run-line and total prices are withheld because appropriate scoring and settlement assumptions have not been validated.</p>
<h2>4. Odds band applies to an observed offered price</h2><p>Fair American odds: −100p/(1−p) above 50%; +100(1−p)/p at or below 50%. Bookmaker American odds are a different field and require a dated quote and source. The requested offered-price band is −250 to +10000. A fair-price-only proxy at p ≥ 70% would restrict p to 70–71.43%, but that is not the same as finding a well-supported selection available at those odds. We never silently substitute the proxy.</p>
<h2>5. Low, medium, high</h2><p>Missing inputs produce no confidence label. Uncalibrated exploratory estimates are low. A future calibrated estimate would be low below 60%, medium from 60% to below 70%, and high from 70%. Publishing a high-confidence recommendation additionally requires a current official scheduled fixture, OLBG match identity, a future UTC start, fresh evidence, an actual price in the band and a dated official evidence packet. No current record passes.</p>
<h2>6. Ranking and original writing</h2><p>Qualifying events are sorted by probability, then UTC start, then stable ID; only one selection per event counts toward the five-per-sport target. Today means UTC at refresh. Upcoming is kept separate from today. Shortfalls stay visible. High-confidence writing must have at least 30 words with match-specific official facts, clear selection, non-repetitive prose and supported recent form/history. Injuries are included only with relevant dated evidence; absence of a report never means everyone is healthy. No high-confidence prose is generated until that evidence exists.</p>
<h2>7. Freshness and automation</h2><p>The Pages workflow runs unattended every six hours. It archives source responses and failures, extracts OLBG event links and parses MLB and NHL schedules. Other official fixture adapters and automatic supported prose are not complete. The checked-in seed is never relabelled as a fresh capture. Runtime evidence uses separate timestamps and overrides a matching official fixture without carrying old predictions into it. Failed refreshes leave historical evidence dated and display the failure ledger. The browser marks starts in the past and captures older than six hours, without relying on a frozen “today” date.</p>
<h2>8. What tests prove</h2><p>Tests check arithmetic, nulls, evidence references, filtering, duplicate protection, links, odds boundaries, source integrity and reproducible output. They do not establish sports facts beyond the source extracts. Local links are audited separately from external source access. This work is a selected line/field audit, not a claim to have externally verified every line of all historical data.</p></section>'''

CSS='''@charset "UTF-8";
:root{--ink:#182c3b;--muted:#526774;--line:#dce5e8;--teal:#006d68;--soft:#edf5f4;--amber:#855508;--nav:#122a36}*{box-sizing:border-box}body{margin:0;background:#f6f8fa;color:var(--ink);font:15px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:3px}a:hover{color:#004d49}button,input,summary{font:inherit}a:focus-visible,input:focus-visible,summary:focus-visible,div:focus-visible{outline:3px solid #d58d17;outline-offset:4px}.skip{position:absolute;top:-70px;left:15px;background:white;padding:12px;z-index:5}.skip:focus{top:12px}.sidebar{position:fixed;inset:0 auto 0 0;width:230px;background:var(--nav);color:#eaf3f4;padding:27px 22px;overflow-y:auto}.brand{display:flex;align-items:center;gap:9px;color:white;text-decoration:none;font-size:26px;font-weight:750;letter-spacing:-1px}.brand-two{color:#7cd6cb;margin-left:-8px}.brand-mark{display:inline-grid;place-items:center;width:32px;height:32px;border:2px solid #7cd6cb;border-radius:9px;color:#7cd6cb;font-size:19px}.brand-sub{font-size:9px;letter-spacing:2px;color:#a4bcc5;margin:6px 0 28px}.sidebar nav{display:grid;gap:3px}.sidebar nav a{color:#d4e0e6;text-decoration:none;padding:7px 11px;border-radius:6px;font-size:13px}.sidebar a:hover,.sidebar a[aria-current]{background:#244653;color:#b8f2e9}.sport-nav{border-top:1px solid #35505c;margin-top:23px;padding-top:16px}.sport-nav summary{font-size:10px;text-transform:uppercase;letter-spacing:1.3px;color:#b4c7ce;cursor:pointer;margin-bottom:8px}.sport-nav nav a{font-size:12px;padding:4px 11px}.archive-link{display:block;font-size:11px;margin-top:23px;color:#b4c7ce}.workspace{margin-left:230px}.topbar{height:63px;border-bottom:1px solid var(--line);background:white;padding:0 38px;display:flex;align-items:center;justify-content:space-between;font-size:11px;font-weight:650;letter-spacing:.6px}.separator{margin:0 12px;color:#a4b2ba}main{max-width:1440px;padding:30px 38px 45px;margin:0 auto}.capture{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:11px;color:var(--muted);margin-bottom:24px}.status-dot{width:7px;height:7px;border-radius:50%;background:#cf932f}.freshness{padding-left:10px;font-weight:650;color:var(--amber)}.eyebrow{font-size:10px;font-weight:750;letter-spacing:1.7px;color:var(--teal);margin:0 0 10px}h1{font-size:clamp(29px,3vw,42px);line-height:1.2;letter-spacing:-1.5px;margin:0 0 18px;font-weight:720}h2{font-size:21px;letter-spacing:-.4px;margin:27px 0 9px}h3{font-size:16px;margin:10px 0}.lede{font-size:16px;max-width:720px;color:var(--muted);line-height:1.8}.actions{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0 30px}.button{border:1px solid #bdd0d4;border-radius:7px;padding:10px 17px;text-decoration:none;font-size:12px;font-weight:650;background:white}.button.primary{background:var(--teal);color:white;border-color:var(--teal)}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0 26px}.metrics article{border:1px solid var(--line);border-radius:9px;background:white;padding:19px 20px}.metrics span{display:block;font-size:9px;color:var(--muted);letter-spacing:1px;font-weight:700}.metrics strong{display:block;font-size:35px;line-height:1.5;font-weight:650;letter-spacing:-1px}.metrics small{font-size:10px;color:var(--muted)}.summary{display:grid;grid-template-columns:1.6fr 1fr;gap:30px;background:white;border:1px solid var(--line);border-top:3px solid var(--teal);border-radius:9px;padding:25px 28px}.summary h2{margin:8px 0 14px;font-size:24px}.summary p,.summary li{font-size:13px}.summary a{font-size:12px;font-weight:650}.summary-side{border-left:1px solid var(--line);padding-left:28px}.summary-side h3{margin-top:0}.summary-side ul{padding-left:18px}.muted{color:var(--muted);font-size:12px}.badge{display:inline-block;white-space:normal;font-size:10px;font-weight:650;border-radius:5px;padding:3px 7px;line-height:1.45;background:#eef2f5;color:#465e6a}.badge.warn{background:#fff2d9;color:#805000}.badge.good{background:#e3f3ed;color:#196045}.search{font-size:11px;color:var(--muted);font-weight:650;display:flex;align-items:center;gap:12px;margin:17px 0 8px}.search input{border:1px solid #bacbd2;border-radius:6px;padding:9px 12px;background:white;color:var(--ink);width:310px;max-width:100%;font-size:12px}.results{font-size:10px;color:var(--muted);margin:3px 0 8px}.table-scroll{overflow:auto;background:white;border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;min-width:800px;text-align:left;font-size:12px}caption{text-align:left;padding:13px 17px;font-size:11px;color:var(--muted);border-bottom:1px solid var(--line);background:#fff}th{padding:11px 14px;background:#eef3f5;color:#455d69;white-space:nowrap;font-size:10px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--line)}td{padding:14px;vertical-align:top;border-bottom:1px solid #e8eef0;max-width:340px}td small{display:block;font-size:10px;color:var(--muted);margin-top:5px}td a{font-size:11px}td strong{font-weight:650}td p{margin:7px 0}tbody tr:hover{background:#f7fbfa}tr[hidden]{display:none}td:empty:after{content:""}table td:empty{background:repeating-linear-gradient(135deg,#fff,#fff 7px,#fafbfc 7px,#fafbfc 8px)}.notice{padding:17px 20px;border:1px solid #efd9aa;border-radius:8px;background:#fffbf2;font-size:13px;margin:20px 0}.prediction{padding:25px;background:white;border:1px solid var(--line);border-radius:8px;max-width:900px}.prediction p{font-size:14px}.prediction .selection{color:var(--teal);font-weight:650}.prediction-meta{font-size:11px;padding:12px 0;border-top:1px solid var(--line)}.prose{max-width:850px}.prose p{color:var(--muted);font-size:14px}.refresh-note{margin-top:32px;padding:16px 20px;background:#eef3f5;border:1px solid var(--line);border-radius:8px}.refresh-note h2{font-size:13px;margin:0 0 5px}.refresh-note p{font-size:11px;color:var(--muted);margin:5px 0}footer{border-top:1px solid var(--line);padding:20px 38px;font-size:10px;color:var(--muted)}.event-state{font-size:10px;color:var(--amber)}@media(max-width:1100px){.sidebar{width:195px;padding:22px 14px}.workspace{margin-left:195px}main{padding:25px}.topbar{padding:0 25px}.metrics{grid-template-columns:repeat(2,1fr)}.summary{grid-template-columns:1fr}.summary-side{border:0;border-top:1px solid var(--line);padding:15px 0 0}}@media(max-width:700px){.sidebar{position:static;width:auto;padding:18px}.brand-sub{margin-bottom:15px}.sidebar>nav{grid-template-columns:repeat(3,1fr);gap:5px}.sidebar nav a{padding:6px;font-size:11px}.sport-nav{margin-top:12px;padding-top:10px}.sport-nav nav{grid-template-columns:repeat(3,1fr)}.sport-nav nav a{font-size:10px}.archive-link{margin-top:12px}.workspace{margin-left:0}.topbar{padding:0 18px;height:50px;font-size:9px}main{padding:20px 16px}.metrics{gap:9px}.metrics article{padding:15px 13px}.metrics span{font-size:8px}.metrics strong{font-size:29px}.summary{padding:20px;gap:8px}.search{align-items:flex-start;flex-direction:column;gap:6px}.search input{width:100%}.table-scroll{border-radius:6px}footer{padding:18px}h1{letter-spacing:-.7px}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
'''
JS='''"use strict";
document.querySelectorAll("[data-search]").forEach(input=>{const section=input.closest(".table-section"), rows=[...section.querySelectorAll("tbody tr")]; const apply=()=>{const q=input.value.trim().toLocaleLowerCase();let n=0;rows.forEach(row=>{row.hidden=!row.textContent.toLocaleLowerCase().includes(q);if(!row.hidden)n++;});section.querySelector(".results").textContent=`${n} of ${rows.length} rows`;section.querySelector(".empty-filter").hidden=n!==0;};input.addEventListener("input",apply);apply();});
function updateAge(){const now=Date.now();document.querySelectorAll(".freshness[data-captured]").forEach(el=>{const age=(now-Date.parse(el.dataset.captured))/3600000;el.textContent=age<0?"Capture clock conflict — review":age>6?"Stale capture — refresh required":"Within 6-hour evidence window — partial coverage";});document.querySelectorAll("tr[data-start]").forEach(row=>{const state=row.querySelector(".event-state");if(!state)return;const start=Date.parse(row.dataset.start), age=(now-Date.parse(row.dataset.captured))/3600000;state.textContent=Number.isFinite(start)&&start<=now?"Start time passed — no pre-match pick":age<0?"Capture clock conflict":age>6?"Stale — not currently confirmed":Number.isFinite(start)?"Future at this clock; last source status only":"UTC unverified — not eligible";});}
updateAge();setInterval(updateAge,60000);
'''

def build(output=OUT,runtime=None):
    data=load(runtime); validate(data)
    sources={s['id']:s for s in data['sources']}
    output.mkdir(parents=True,exist_ok=True); (output/'sports').mkdir(exist_ok=True)
    pages={'index':('Overview',overview(data,sources)),
           'matches':('Fixtures','<p class="eyebrow">OFFICIAL-SOURCE INVENTORY</p><h1>Fixtures, with the gaps visible.</h1><p class="lede">Pairing and date support do not certify every field. Unknown UTC times, odds, injuries and forecasting inputs stay blank. Official-only fixtures are explicitly marked where OLBG membership is not confirmed.</p>'+fixture_table(data['events'],sources)),
           'picks':('Picks & top five',picks(data,sources)), 'markets':('Markets',markets(data,sources)),
           'sources':('Sources',source_page(data)), 'flagged':('Flagged for Review',flags(data,sources)),
           'methodology':('Methodology',METHODOLOGY)}
    for slug,(title,body) in pages.items(): (output/(slug+'.html')).write_text(shell(title,body,data,slug))
    for slug,name,hubs,url in SPORTS:
        rows=[r for r in data['events'] if r['sport']==slug]
        body=f'<p class="eyebrow">SPORT RESEARCH</p><h1>{name}</h1><p class="lede">{len(rows)} official-source fixture rows in this partial capture. No high-confidence pick qualifies; the daily five-pick target is not met.</p><div class="notice">Unknown values are intentionally blank. A missing fixture in this desk is not proof that no match exists. {link(url.format(date=data["captured_at"][:10]),"Official source")}</div>'
        body+=fixture_table(rows,sources) if rows else '<h2>No confirmed fixture rows in this capture</h2><p>Do not substitute OLBG tip shares or historical desk records. The source-attempt ledger explains the missing evidence.</p>'
        body+='<p><a href="../flagged.html#coverage-'+slug+'">Review this category’s evidence gaps →</a></p><p><a href="../sources.html">Source ledger</a> · <a href="../markets.html">Market investigation</a></p>'
        (output/'sports'/f'{slug}.html').write_text(shell(name,body,data,slug,'../'))
    (output/'style.css').write_text(CSS); (output/'app.js').write_text(JS)
    print(f'monitor build: {len(pages)+len(SPORTS)} pages; {len(data["events"])} fixture rows; no invented high-confidence picks')
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=OUT);p.add_argument('--runtime',type=Path)
    args=p.parse_args(); build(args.output,args.runtime)
