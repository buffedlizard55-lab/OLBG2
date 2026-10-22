#!/usr/bin/env python3
"""Self-contained source-evidence desk. Does not modify upstream outputs."""
import json
from html import escape
from pathlib import Path
from command_seed import build
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/command'
OUT=ROOT/'command'

def e(v):
    return escape(str(v),quote=True) if v is not None else ''

def source(url,label='Official source'):
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'

def table(head,rows,caption):
    return '<div class="scroll" tabindex="0" role="region" aria-label="'+e(caption)+'"><table><caption>'+e(caption)+'</caption><thead><tr>'+''.join('<th scope="col">'+e(h)+'</th>' for h in head)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'

def tr(cells):
    return '<tr>'+''.join('<td>'+c+'</td>' for c in cells)+'</tr>'

def render(title,body,path,base=''):
    nav=[('index.html','Overview'),('matches.html','Source ledger'),('sports/index.html','Sports'),('picks.html','Research lines'),('flagged.html','Flagged for Review'),('sources.html','Sources & method')]
    links=''.join(f'<a href="{base}{p}"'+(' aria-current="page"' if p==path else '')+'>'+n+'</a>' for p,n in nav)
    text=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · OLBG evidence command</title><link rel="stylesheet" href="{base}assets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header><div class="brand">OLBG<span> / EVIDENCE COMMAND</span></div><nav aria-label="Primary">{links}</nav></header><main id="main"><p class="eyebrow">22 OCTOBER 2026 · BOUNDED INDEPENDENT AUDIT</p><h1>{e(title)}</h1>{body}</main><footer>Research, not betting advice · 18+ · No profit or outcome guarantee.<br><a href="{base}../index.html">Repository dashboard</a> · <a href="{base}../data/command/inputs.json">Selected-field evidence JSON</a> · <a href="{base}../research/audit-58642817.md">Audit boundary</a></footer></body></html>'''
    target=OUT/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(text)


def match_table(matches):
    rows=[]
    for m in matches:
        model=m['markets']
        winner=e(m['winner_pick']) if model else ''
        if model:
            q=model['winner'][model['winner_selection']]
            winner+=f'<br><strong>{q["fair_decimal"]:.4f} / {q["fair_american"]:+d}</strong><br>{100*q["probability"]:.2f}% model'
        status='<span class="badge">'+e(m['status'])+'</span>'
        desc=e(m['event'])+'<br><strong>'+e(m['home'])+(' vs '+e(m['away']) if m['away'] else '')+'</strong>'
        rows.append(tr([e(m['sport']),desc,e(m['date'])+'<br>'+e(m['start_utc']),e(m['venue']),status,winner,e(m['confidence']),e(m['blank_reason'] or model['assumptions']),source(m['source_url'])]))
    return table(['Sport','Event / participants','Date / exact UTC','Venue','Source status at capture','Model winner / fair odds','Confidence','Limits / blank reason','Evidence'],rows,'Selected-field schedule ledger — blank cells are unverified')


def main():
    result=build(); ms=result['matches']; counts=result['counts']
    sports=json.loads((DATA/'sports.json').read_text())
    flags=json.loads((DATA/'repo_audit.json').read_text())['items']
    sources=json.loads((DATA/'sources.json').read_text())
    notice='<div class="notice"><strong>Partial, dated research — not a complete live slate.</strong> Only selected fields actually read from official responses are transcribed. Blank means unverified, not zero. Source links and passing tests do not certify every adjacent claim. Model prices are estimates, never official or bookmaker values.</div>'
    cards=f'<section class="stats"><div><strong>{counts["rows"]}</strong>Transcribed entries</div><div><strong>{counts["originated"]}</strong>Experimental models</div><div><strong>0</strong>Certified high picks</div><div><strong>{len(flags)}</strong>Review findings</div></section>'
    coverage=[]
    for s in sports:
        group=[m for m in ms if m['sport']==s['slug']]
        lined=sum(bool(m['markets']) for m in group)
        coverage.append(tr([f'<a href="sports/{s["slug"]}.html">{e(s["name"])}</a>',str(len(group)),str(lined),e(s['coverage_note']),source(s['source_url'])]))
    render('Facts first. Estimates separate.',notice+cards+'<p class="lede">A compact review of inherited inconsistencies, source-confirmed schedule fields and explicitly experimental lines. No unsupported selection is promoted to high confidence.</p><h2>Coverage by category</h2>'+table(['Category','Entries','Modelled','Coverage boundary','Official review link'],coverage,'All 17 eligible categories — counts are not completeness claims')+'<h2>Start with the findings</h2><p>The independent audit identified portal confidence-rule mismatches, AFLW fixture contradictions, live tennis rows, and unsupported cricket citations. <a href="flagged.html">Read all findings →</a></p>', 'index.html')
    render('Source ledger',notice+'<p>Includes calendar events and already-live rows for traceability. These are not all actionable matches. Dates follow the source convention; unknown UTC times remain blank. The AFLW ribbon did not supply an unambiguous date/time zone, so those fields are withheld.</p>'+match_table(ms),'matches.html')
    line_rows=[]
    for m in ms:
        d=m['markets']
        if not d: continue
        def q(x): return f'{x["fair_decimal"]:.4f} / {x["fair_american"]:+d} ({100*x["probability"]:.2f}%)'
        line_rows.append(tr([e(m['home'])+' vs '+e(m['away']),q(d['winner']['home'])+'<br>'+q(d['winner']['away']),f'Home {d["handicap"]["home_line"]:+.1f}: '+q(d['handicap']['home'])+'<br>Away: '+q(d['handicap']['away']),str(d['total']['line'])+' goals<br>Over '+q(d['total']['over'])+'<br>Under '+q(d['total']['under']),e(m['confidence']),source(m['rates']['source_url'],'Official scoring inputs')+'<br>'+source(m['source_url'],'Fixture source')]))
    render('Research lines, not endorsements',notice+'<p class="lede">Independent-Poisson estimates from official scoring inputs. Fair decimal / American / model probability are shown together. No margin or bookmaker odds are applied.</p>'+table(['Fixture','Winner home / away','Regulation handicap','Regulation total','Winner confidence','Sources'],line_rows,'Seven supported scoring models — no backtest or calibration established')+'<h2>Why there are no high-confidence predictions</h2><p>A model probability of 70% is not evidence that a model is calibrated. High confidence requires p ≥ 70%, exact fair decimal 1.40–101.00 (−250…+10000 American), and independent calibration. The latter is not established here. Stronger probabilities alone do not override that safeguard. No high write-ups were fabricated.</p><p>Winner estimates split a regulation tie 50/50 as an explicit assumption. Handicap and total estimates are regulation-only; they are not quotes for a bookmaker’s overtime-inclusive market. Full regulation three-way probabilities are in <a href="../data/command/matches.json">the machine-readable output</a>.</p>','picks.html')
    flagged=[]
    for f in flags:
        flagged.append(tr([e(f['id']),e(f['severity']),'<strong>'+e(f['title'])+'</strong><br>'+e(f['finding']),'<code>'+e(f['file'])+'</code>','',source(f['source_url'])]))
    render('Flagged for Review',notice+'<p>Findings are bounded to the exact fields read or mechanically inspected. Corrected values remain blank where no official replacement was confirmed. Upstream pages remain unchanged to respect parallel-session ownership.</p>'+table(['ID','Severity','Finding','Affected file','Unverified replacement','Official review link'],flagged,'Independent review queue — unresolved items do not imply complete verification'),'flagged.html')
    srcrows=[tr([e(s['id']),e(s['retrieved_date']),e(s['method']),source(s['url'])]) for s in sources]
    render('Sources & methodology',notice+'<h2>Evidence boundary</h2><p>This ledger is a selected-field manual transcription of tool responses, not a raw response archive. Some pages were read only in selected chunks; unread objects are not imported. Local shell network restrictions are distinct from agent fetch-page access. The latter returned official content in this session, but not all fields on every source.</p><h2>Experimental model</h2><p>λ home = mean(home goals for per game, away goals against per game); λ away is the reverse. Independent Poisson goals are summed over 0–40 and normalized. Regulation ties are split equally for the winner estimate. No home edge is asserted. Historical aggregate scoring is not a verified forecast. Injuries, starting goalies, travel, lineup changes and calibration are not established. Confidence is capped at medium.</p><p>Fair decimal is 1/p; American prices use the unrounded p, not a rounded decimal. The focus gate uses the exact reciprocal, preventing rounding at −250 from promoting a disallowed selection. Raw probabilities, not bookmaker-derived prices, drive the estimates. No unsupported props or artificial alternate lines are invented.</p>'+table(['Source family','Retrieval date','Method / limit','Official link'],srcrows,'Source register — a URL alone does not validate a factual assertion'),'sources.html')
    render('Sport categories',notice+table(['Category','Entries','Modelled','Coverage boundary','Official review link'],[r.replace('href="sports/','href="') for r in coverage],'Eligible categories'),'sports/index.html',base='../')
    for s in sports:
        group=[m for m in ms if m['sport']==s['slug']]
        intro='<p>'+e(s['coverage_note'])+' '+source(s['source_url'],'Governing-body review link')+'</p>'
        if not group: intro+='<div class="notice">No fixture row is certified in this bounded ledger for this category. This is a coverage gap, not a statement that no fixtures exist. Participants, dates, selections and prices remain blank.</div>'
        render(s['name'],notice+intro+match_table(group),'sports/'+s['slug']+'.html',base='../')
    print(f'Built {len(list(OUT.rglob("*.html")))} pages: {counts}')

if __name__=='__main__': main()
