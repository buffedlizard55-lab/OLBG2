#!/usr/bin/env python3
"""Build the static, evidence-first Zenith GitHub Pages desk."""
from __future__ import annotations
import html, json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'zenith'; SITE=ROOT/'zenith'
SPORTS=["Golf","Volleyball","Rugby Union","Cricket","Snooker","Darts","Baseball","Gaelic Sports","Greyhounds","Tennis","Motor Racing","Handball","Ice Hockey","Basketball","Rugby League"]
SLUG={"Golf":"golf","Volleyball":"volleyball","Rugby Union":"rugby-union","Cricket":"cricket","Snooker":"snooker","Darts":"darts","Baseball":"baseball","Gaelic Sports":"gaelic-sports","Greyhounds":"greyhounds","Tennis":"tennis","Motor Racing":"motor-racing","Handball":"handball","Ice Hockey":"ice-hockey","Basketball":"basketball","Rugby League":"rugby-league"}

def load(name): return json.loads((DATA/f'{name}.json').read_text(encoding='utf-8'))
def esc(x): return html.escape(str(x or ''), quote=True)
def link(url,label='Official source'):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>' if str(url).startswith('https://') else '<span class="muted">Unverified / no link</span>'
def cell(s): return f'<td>{s}</td>'
def table(headers, rows):
    h=''.join(f'<th>{esc(x)}</th>' for x in headers)
    body=''.join('<tr>'+''.join(cell(c) for c in row)+'</tr>' for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'

NAV=[('Overview','index.html'),('Matches','matches.html'),('Our lines','lines.html'),('Picks','picks.html'),('Predictions','predictions.html'),('OLBG inventory','olbg.html'),('Repository audit','audit.html'),('Sources','sources.html'),('Methodology','methodology.html'),('Flagged for Review','flagged.html')]
def shell(title, body, active='', sub=False):
    prefix='../' if sub else ''
    nav=''.join(f'<a class="{"active" if label==active else ""}" href="{prefix}{path}">{label}</a>' for label,path in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Zenith OLBG desk</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body><header class="top"><a class="brand" href="{prefix}index.html">ZENITH <span>OLBG evidence desk</span></a><button class="nav-toggle" onclick="document.body.classList.toggle('nav-open')" aria-label="Toggle navigation">☰</button><nav>{nav}</nav></header><main><div class="crumb">OLBG · 15 covered sports · evidence-first snapshot · 23 Oct 2026</div>{body}</main><footer><p>Research snapshot, not a live feed or betting recommendation. Sources, capture times and unresolved gaps are shown on each row.</p><p><a href="../index.html">Repository dashboard</a> · <a href="https://www.olbg.com/betting-tips">OLBG sport hubs</a></p></footer></body></html>'''

def fixture_rows(rows):
    out=[]
    for m in rows:
        matchup=esc(m['home'])+(f' <span class="vs">vs</span> {esc(m["away"])}' if m.get('away') else '')
        st=m.get('start_utc') or m.get('time_display') or '—'
        official=link(m.get('official_fixture_url'), 'Fixture')
        stats=link(m.get('official_stats_url'), 'Stats') if m.get('official_stats_url') else ''
        injury=link(m.get('injury_report_url'),'Injury report') if m.get('injury_report_url') else ''
        olbg=link(m.get('olbg_event_url'),'OLBG') if m.get('olbg_event_url') else '—'
        status=m.get('temporal_state','')
        out.append([esc(m['sport']), matchup, esc(m.get('competition')), esc(st), esc(status), esc(m.get('our_selection') or '—'), esc(m.get('confidence') or '—'), ' · '.join(x for x in [official,stats,injury,olbg] if x)])
    return out

def build():
    SITE.mkdir(exist_ok=True); (SITE/'assets').mkdir(exist_ok=True); (SITE/'sports').mkdir(exist_ok=True)
    matches=load('matches')['matches']; lines=load('lines')['lines']; picks=load('picks')['picks']; preds=load('predictions')['predictions']; olbg=load('olbg_events'); flags=load('flagged')['items']; audit=load('repo_audit')['findings']; sources=load('sources')['sports']
    active_sports=sorted({m['sport'] for m in matches})
    upcoming=[m for m in matches if m['temporal_state']=='upcoming_at_capture']
    high=[p for p in picks if p['confidence']=='high']
    pred_by_sport={s:sum(p['sport']==s for p in preds) for s in SPORTS}
    hero=f'''<section class="hero"><p class="eyebrow">Evidence-led · 15 sport categories</p><h1>OLBG fixtures, independent lines, and the facts behind them.</h1><p class="lede">A dated research desk connecting OLBG's event listings to official governing-body sources. Unconfirmed facts stay blank; fair prices are not bookmaker offers.</p><div class="actions"><a class="button primary" href="matches.html">Explore fixtures</a><a class="button" href="flagged.html">Review limitations</a></div></section>'''
    cards=[('Official fixture records',str(len(matches)),f'{len(upcoming)} have a confirmed start after the 21:45 UTC cutoff','matches.html'),('Originated market prices',str(len(lines)),'fair odds recalculated from stored probabilities; not live bookmaker quotes','lines.html'),('High-confidence selections',str(len(high)),f'{len(preds)} evidence-backed writeups; five-per-sport is a target, not filled by invention','picks.html'),('OLBG tip inventory',str(olbg['total_unique_covered_hub_events']),f"{olbg['strictly_future_by_cutoff']} strictly future by OLBG start time at cutoff",'olbg.html')]
    cardhtml=''.join(f'<a class="kpi" href="{href}"><span>{esc(label)}</span><strong>{esc(value)}</strong><small>{esc(note)}</small></a>' for label,value,note,href in cards)
    sportcards=[]
    for s in SPORTS:
        n=sum(m['sport']==s for m in matches); p=pred_by_sport[s]
        sportcards.append(f'<a class="sport-card" href="sports/{SLUG[s]}.html"><strong>{esc(s)}</strong><span>{n} fixture rows</span><small>{p} written previews</small></a>')
    executive_rows=[]
    for p in sorted(high,key=lambda x:x['probability'],reverse=True)[:12]:
        m=next((x for x in matches if x['id']==p['fixture_id']),{})
        official=link(p['official_fixture_url'],'Official fixture')
        stats=link(p['official_stats_url'],'Official stats') if p.get('official_stats_url') else ''
        executive_rows.append([esc(p['sport']),esc(f"{p['home']} vs {p['away']}"),esc(p['selection']),f"{p['probability']:.1%}",esc(p['confidence']), ' · '.join(x for x in [official,stats] if x)])
    summary='<h2>Executive summary</h2><p>Top selections are ranked by the stored independent probability. They are not guaranteed outcomes. The odds-band test uses fair American prices and does not imply a bookmaker has the market.</p>'+table(['Sport','Match','Selection','Probability','Confidence','Source'],executive_rows) if executive_rows else '<h2>Executive summary</h2><div class="notice">No high-confidence pick is available in the current official-evidence snapshot. The desk does not promote lower-confidence picks to fill the headline.</div>'
    body=hero+f'<section class="kpis">{cardhtml}</section>'+summary+'<h2>Browse by sport</h2><div class="sport-grid">'+''.join(sportcards)+'</div><section class="notice"><strong>Data freshness:</strong> official evidence in the underlying same-day capture bundle ranges from 19:00–20:20 UTC on 23 October. OLBG hub inventory was captured around 20:31 UTC, with event pages re-read around 21:35 UTC. The displayed 21:45 UTC cutoff is a snapshot boundary, not proof a row remains upcoming now.</section>'
    (SITE/'index.html').write_text(shell('Overview',body,'Overview'),encoding='utf-8')
    # all fixtures
    (SITE/'matches.html').write_text(shell('Matches','<h1>Official fixture ledger</h1><p class="lede">Each row links the official fixture source and any separately captured official statistics/injury record. “Unconfirmed time” means no official start clock was stored.</p>'+table(['Sport','Fixture','Competition','Start time','Snapshot status','Selection','Confidence','Evidence links'],fixture_rows(matches)),'Matches'),encoding='utf-8')
    line_rows=[]
    for r in lines:
        links=' · '.join(x for x in [link(r['official_fixture_url'],'Fixture'),link(r['official_stats_url'],'Official stats') if r.get('official_stats_url') else '',link(r['olbg_event_url'],'OLBG listing') if r.get('olbg_event_url') else ''] if x)
        line_rows.append([esc(r['sport']),esc(r['competition']),esc(r['market']),esc(r['selection']),esc(r.get('line') if r.get('line') is not None else '—'),f"{r['probability']:.1%}",str(r['our_fair_american']),f"{r['our_fair_decimal']:.3f}",esc(r['confidence']),links])
    (SITE/'lines.html').write_text(shell('Our lines','<h1>Independent fair-price ledger</h1><p class="lede">All available captured markets from the official-input origination layer. Fair odds are reciprocal probabilities; the displayed probability is the input, not an OLBG consensus percentage or bookmaker quote.</p>'+table(['Sport','Competition','Market','Selection','Line','Probability','Fair American','Fair Decimal','Confidence','Evidence'],line_rows),'Our lines'),encoding='utf-8')
    pick_rows=[]
    for p in picks:
        links=' · '.join(x for x in [link(p['official_fixture_url'],'Fixture'),link(p['official_stats_url'],'Statistics') if p.get('official_stats_url') else '',link(p['olbg_event_url'],'OLBG event') if p.get('olbg_event_url') else ''] if x)
        pick_rows.append([esc(p['sport']),esc(str(p.get('home') or p.get('competition') or '')+((' vs '+str(p.get('away'))) if p.get('away') else '')),esc(p['selection']),esc(p['market']),f"{p['probability']:.1%}",str(p['fair_american']),esc(p['confidence']), 'in' if p['in_user_odds_band'] else 'out',links])
    (SITE/'picks.html').write_text(shell('Picks','<h1>Selections & confidence</h1><p class="lede">One highest-supported selection per priced fixture from the available captured markets. The user odds interval is checked against our fair odds only.</p>'+table(['Sport','Fixture','Selection','Market','Probability','Fair price (US)','Confidence','−250…+10000','Official source'],pick_rows),'Picks'),encoding='utf-8')
    pred_cards=[]
    for p in preds:
        facts=' · '.join(link(f.get('source_url',''),'Official fact') for f in p.get('facts',[]))
        pred_cards.append(f'<article class="prediction"><div class="eyebrow">{esc(p["sport"])} · {esc(p["confidence"])} · {p["probability"]:.1%}</div><h3>{esc(p["headline"])}</h3><p class="selection">{esc(p["selection"])} — {esc(p["market"])}</p><p>{esc(p["text"])}</p><div class="source-list">{facts} · {link(p["official_fixture_url"],"Fixture source")}</div></article>')
    (SITE/'predictions.html').write_text(shell('Predictions','<h1>Human-written previews</h1><p class="lede">Writeups are retained only where the source capture supports the stated match facts. Injury status is never inferred; check the source record linked below.</p>'+''.join(pred_cards),'Predictions'),encoding='utf-8')
    olbg_rows=[]
    for e in olbg['events']:
        marketnames='<br>'.join(f"{esc(m.get('market') or 'Market unspecified')}: {esc(m.get('selection'))} · {esc(m.get('quoted_american') or m.get('quoted_decimal') or 'quote blank')} · {esc(m.get('olbg_consensus_tips'))} tips" for m in e['markets_on_hub'])
        olbg_rows.append([esc(e['sport']),esc(e['competition']),esc(e['event']),esc(e['start_utc']),esc(e['evaluated_state_at_utc_cutoff']),marketnames or '—',link(e['event_url'],'OLBG event')])
    olbg_intro=f"<h1>OLBG reverse-engineering & inventory</h1><p class=lede>Captured tip objects are grouped by event id and split into the exact requested 15 categories. This is a dated tip inventory, not a complete schedule of every match in the world.</p><div class=notice>Sport hubs use /betting-tips/{{sportSlug}}/{{sportId}}; event-detail pages carry a ?event_id= key. Gaelic Sports is represented by two OLBG ids (25 Football; 26 Hurling). OLBG raw hub capture: {esc(olbg['capture_timestamp_utc'])}; event state evaluated at {esc(olbg['status_evaluated_at_utc'])}. The inventory contains {olbg['total_unique_covered_hub_events']} unique covered events; {olbg['strictly_future_by_cutoff']} have a listed start after the evaluation cutoff. Quotes below are OLBG's tip/odds display, not our lines.</div>"
    (SITE/'olbg.html').write_text(shell('OLBG inventory',olbg_intro+table(['Sport','Competition','Event','OLBG UTC start','State at cutoff','Markets / consensus / OLBG quote','Source'],olbg_rows),'OLBG inventory'),encoding='utf-8')
    # audit and flagged
    audit_rows=[[esc(x['severity']),esc(x['title']),esc(x['detail']),link(x['source_url'],x['artifact'])] for x in audit]
    (SITE/'audit.html').write_text(shell('Repository audit','<h1>Repository audit</h1><p class="lede">Structural inspection plus checked findings; this page does not certify every historical row in every archived desk.</p>'+table(['Severity','Finding','Detail','Review/source'],audit_rows),'Repository audit'),encoding='utf-8')
    all_flags=[*flags,*[{"code":x['id'],"sport":"Repository","title":x['title'],"detail":x['detail'],"source":x['source_url']} for x in audit]]
    flag_rows=[[esc(x.get('code')),esc(x.get('sport')),esc(x.get('title') or x.get('detail')),esc(x.get('detail')),link(x.get('source') or x.get('source_url',''),'Source / artifact')] for x in all_flags]
    (SITE/'flagged.html').write_text(shell('Flagged for Review','<h1>Flagged for Review</h1><p class="lede">Known gaps and irregularities are published here, not silently guessed away. A blank value is not a negative finding.</p>'+table(['Code','Scope','Finding','Detail','Source'],flag_rows),'Flagged for Review'),encoding='utf-8')
    source_rows=[]
    for s in sources:
        urls=[s['primary_official_url'],*s.get('secondary_official_urls',[])]
        source_rows.append([esc(s['sport']),esc(s['governing_body']),'<br>'.join(link(u,u.split('/')[2]) for u in urls),'<br>'.join(link(u,'OLBG hub') for u in s['olbg_hub_urls'])])
    (SITE/'sources.html').write_text(shell('Sources','<h1>Source register</h1><p class="lede">Official governing-body links and OLBG discovery links. The cited pages are the primary audit trail; values remain dated to their capture time.</p><p><a href="../data/zenith/captures/source_read_log.json">Open the structured current-session source-read log</a> · <a href="../research/zenith-110cf432.md">Research and verification notes</a></p>'+table(['Sport','Governing body','Official sources','OLBG source'],source_rows),'Sources'),encoding='utf-8')
    method='''<h1>Methodology & evidence limits</h1><h2>Coverage and freshness</h2><p>Sports in scope: Golf, Volleyball, Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball and Rugby League. The source inventory is captured on 23 October 2026 and is not continuously refreshed.</p><h2>Fixture confirmation</h2><p>Fixture pairings and numeric facts remain tied to their official source URLs. A missing start time is displayed as unconfirmed; no local-time conversion is inferred. OLBG is used only to discover its event rows and market taxonomy.</p><h2>Independent fair prices</h2><p>For each supported market, the ledger publishes the captured same-day official-input probability, then independently recalculates a fair American price and fair decimal price as its reciprocal. The underlying probability calculation is retained from the existing Cadence official-input evidence bundle; this desk does not claim a newly invented or separately calibrated probability engine. No margin is added, no OLBG consensus or quote is used as our line, and no line is claimed to be currently offered by a bookmaker. Where the official capture has no comparable numeric inputs, the market/pick remains blank.</p><h2>Confidence</h2><p>Confidence labels are computed from the stored probability and evidence tier; thin samples may be capped at medium. They are not calibrated guarantees. “High” is not an endorsement of a wager.</p><h2>Odds band</h2><p>The requested −250 through +10000 band is checked against our fair American price. A fair price inside the band does not establish bookmaker availability. Because −250 implies about 71.43%, the overlap with a ≥70% high threshold is narrow.</p><h2>Predictions</h2><p>Preview paragraphs are unique, at least 30 words, and cite the official facts used. Injury claims appear only when an official match-specific report was captured. Five previews per sport is a target, not permission to invent.</p><h2>Reproduce</h2><pre>python3 scripts/zenith_seed.py\npython3 scripts/zenith_model.py\npython3 scripts/zenith_predictions.py\npython3 scripts/zenith_audit.py\npython3 scripts/zenith_build.py\npython3 scripts/zenith_verify.py</pre>'''
    (SITE/'methodology.html').write_text(shell('Methodology',method,'Methodology'),encoding='utf-8')
    sports_nav=''.join(f'<a class="sport-card" href="{SLUG[s]}.html"><strong>{esc(s)}</strong><span>{sum(m["sport"]==s for m in matches)} fixtures</span></a>' for s in SPORTS)
    (SITE/'sports/index.html').write_text(shell('Sports','<h1>Sport categories</h1><div class="sport-grid">'+sports_nav,sub=True),'utf-8')
    for s in SPORTS:
        ms=[m for m in matches if m['sport']==s]
        ps=[p for p in preds if p['sport']==s]
        body=f'<p><a href="index.html">← Overview</a> · <a href="../sports/index.html">All sports</a></p><h1>{esc(s)}</h1><p class="lede">{len(ms)} fixture rows · {len(ps)} written previews in this dated evidence snapshot.</p>'
        body+='<h2>Fixtures and selections</h2>'+table(['Fixture','Competition','Start','State','Selection','Confidence','Official source'],[[esc(m['home']+((' vs '+m['away']) if m.get('away') else '')),esc(m['competition']),esc(m.get('start_utc') or m.get('time_display') or '—'),esc(m['temporal_state']),esc(m['our_selection'] or '—'),esc(m['confidence'] or '—'),link(m['official_fixture_url'],'Official source')] for m in ms])
        if ps:
            body+='<h2>Previews</h2>'+''.join(f'<article class="prediction"><h3>{esc(p["headline"])}</h3><p class="selection">{esc(p["selection"])} · {esc(p["confidence"])}</p><p>{esc(p["text"])}</p><p>{link(p["official_fixture_url"],"Official fixture")}</p></article>' for p in ps)
        else: body+='<div class="notice">No written preview is published for this category in this snapshot. See Flagged for Review for the reason.</div>'
        body+='<p><a href="../lines.html">All market lines</a> · <a href="../flagged.html">Flagged for Review</a></p>'
        (SITE/'sports'/f'{SLUG[s]}.html').write_text(shell(s,body,sub=True),'utf-8')
    css='''*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#142033;font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#086c82}a:hover{color:#06495a} .top{position:sticky;top:0;z-index:4;background:#10273b;color:#fff;padding:.75rem max(1rem,calc((100vw - 1240px)/2));display:flex;align-items:center;justify-content:space-between;gap:1rem;box-shadow:0 2px 12px #12283b20}.brand{font-weight:900;letter-spacing:.12em;color:#fff;text-decoration:none}.brand span{font-weight:500;letter-spacing:0;color:#bad2dc;margin-left:.65rem}nav{display:flex;flex-wrap:wrap;gap:.25rem}nav a{padding:.4rem .55rem;color:#dcebf0;text-decoration:none;border-radius:7px;font-size:.86rem}nav a:hover,nav a.active{background:#1f6375;color:white}.nav-toggle{display:none}main{max-width:1240px;margin:auto;padding:1rem 1.1rem 4rem}.crumb,.eyebrow{color:#527087;text-transform:uppercase;font-weight:750;letter-spacing:.1em;font-size:.75rem}.hero{padding:clamp(2rem,6vw,4.8rem);border-radius:24px;background:linear-gradient(120deg,#10273b,#1b6172);color:white;margin:1rem 0 1.25rem}.hero h1{font-size:clamp(2rem,5vw,4rem);line-height:1.08;max-width:850px;margin:.5rem 0 1rem}.hero .lede{color:#d4e8ec;max-width:750px;font-size:1.15rem}.hero .eyebrow{color:#8ce1d1}.actions{display:flex;gap:.7rem;flex-wrap:wrap}.button{display:inline-block;padding:.75rem 1rem;border:1px solid #a8d4dc;border-radius:9px;color:white;text-decoration:none}.button.primary{background:#79dac4;color:#10273b;border-color:#79dac4;font-weight:800}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin:1rem 0 2rem}.kpi,.sport-card{display:flex;flex-direction:column;text-decoration:none;background:white;padding:1rem;border:1px solid #dce4ec;border-radius:14px;color:#17283b;box-shadow:0 3px 10px #12283b07}.kpi span{color:#527087;font-size:.88rem}.kpi strong{font-size:2rem}.kpi small,.sport-card small{color:#64778a}.sport-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:.7rem}.sport-card:hover,.kpi:hover{border-color:#15859a;transform:translateY(-1px)}h1{font-size:2.2rem;line-height:1.15;margin:.5rem 0}.lede{color:#52677b;max-width:900px}.notice{margin:1.3rem 0;padding:1rem 1.2rem;background:#fff9e9;border-left:5px solid #e0a323;border-radius:8px;color:#4d4126}h2{margin-top:2rem;border-bottom:1px solid #dce4ec;padding-bottom:.45rem}.table-wrap{overflow:auto;background:white;border:1px solid #dce4ec;border-radius:12px;margin:1rem 0 2rem}table{border-collapse:collapse;width:100%;min-width:850px;font-size:.9rem}th,td{padding:.7rem .75rem;text-align:left;vertical-align:top;border-bottom:1px solid #e7edf2}th{background:#eaf1f5;color:#203a50;position:sticky;top:0}tr:last-child td{border-bottom:0}tr:hover td{background:#f8fbfc}.vs{color:#8091a2}.prediction{background:white;border:1px solid #dce4ec;border-radius:14px;margin:1rem 0;padding:1.1rem 1.3rem;box-shadow:0 3px 10px #12283b07}.prediction h3{margin:.3rem 0}.selection{font-weight:800;color:#145e6d}.source-list{display:flex;gap:.8rem;flex-wrap:wrap;font-size:.86rem}.muted,small{color:#738393}footer{border-top:1px solid #dce4ec;text-align:center;padding:1.5rem;color:#687c8d;font-size:.86rem}pre{overflow:auto;background:#10273b;color:#d7f1ed;padding:1rem;border-radius:10px}@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}.sport-grid{grid-template-columns:repeat(3,1fr)}nav{display:none;position:absolute;top:100%;left:0;right:0;background:#10273b;padding:1rem}.nav-open nav{display:flex;flex-direction:column}.nav-toggle{display:block;background:none;color:white;border:0;font-size:1.4rem}}@media(max-width:520px){main{padding:.7rem .6rem 2rem}.sport-grid{grid-template-columns:repeat(2,1fr)}.kpi{padding:.8rem}.kpi strong{font-size:1.6rem}.brand span{display:block;margin:0;font-size:.8rem}.hero{border-radius:16px;padding:1.5rem}}
'''
    (SITE/'assets/style.css').write_text(css,encoding='utf-8')
    print(f"zenith_build: {len(list(SITE.rglob('*.html')))} pages, {len(matches)} matches, {len(lines)} lines, {len(preds)} previews")
if __name__=='__main__':build()
