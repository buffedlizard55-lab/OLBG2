"""Read-only cross-layer audit. Links and model estimates are not verified facts."""
from pathlib import Path
import json
import re
from html import escape
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ('verified', 'forward', 'board', 'hub', 'slate')

def https(value):
    return isinstance(value, str) and urlsplit(value).scheme == 'https' and bool(urlsplit(value).hostname)

def records(document, keys):
    if isinstance(document, list):
        return document
    return [row for key in keys for row in document.get(key, [])]

def prediction_issues(row):
    issues = []
    text = row.get('text', row.get('analysis', ''))
    words = len(text.split())
    if words < 30:
        issues.append('Prediction has fewer than 30 whitespace-separated words.')
    probability = next((row[k] for k in ('probability', 'fair_prob') if row.get(k) is not None), None)
    if row.get('confidence') == 'high':
        if probability is None:
            issues.append('High confidence has no explicit prediction probability in this record.')
        elif probability < .70:
            issues.append(f'High confidence with {probability:.2%} model probability; conviction is not a 70% likelihood claim.')
    odds = next((row[k] for k in ('fair_american', 'fair_am') if row.get(k) is not None), None)
    if odds is not None:
        try:
            if not -250 <= float(odds) <= 10000:
                issues.append('Fair American price lies outside requested -250..+10000 band.')
        except (TypeError, ValueError):
            issues.append('Fair American price is not numeric.')
    # Compare explicit player ranking facts only, without interpreting general prose.
    for side in ('home', 'away'):
        record = row.get(side + '_record', '')
        rank = re.search(r'ATP #(\d+)\b', record)
        name = row.get('matchup', '').split(' vs ')
        if rank and len(name) == 2:
            player = name[0 if side == 'home' else 1]
            prose = re.search(r'(?:World|world) #(\d+)\s+' + re.escape(player), text)
            if prose and prose.group(1) != rank.group(1):
                issues.append(f'Internal ranking contradiction for {player}: row #{rank.group(1)}, prose #{prose.group(1)}. Official value not reverified.')
    if not https(row.get('official_url')):
        issues.append('Missing valid HTTPS official-source URL; value remains unverified.')
    return issues

def audit(root=ROOT):
    result = {'audit_date': '2026-10-22', 'scope': 'Structural and internal consistency only; no blanket official verification.', 'layers': [], 'findings': [], 'inventory': []}
    for layer in LAYERS:
        base = root / 'data' / layer
        matches_file = base / 'matches.json'
        if not matches_file.exists():
            continue
        doc = json.loads(matches_file.read_text())
        matches = records(doc, ('matches', 'rows', 'unlined_fixtures'))
        for row in matches:
            result['inventory'].append({'layer': layer, 'id': row.get('id', ''), 'sport': row.get('sport', ''), 'event': row.get('event') or ' vs '.join(str(row.get(k) or '') for k in ('home', 'away')), 'official_url': row.get('official_url', ''), 'status': 'Source linked; not independently reverified in this audit' if https(row.get('official_url')) else 'Unverified: missing HTTPS source'})
        pfile = base / 'predictions.json'
        predictions = records(json.loads(pfile.read_text()), ('predictions',)) if pfile.exists() else []
        n = 0
        for i, row in enumerate(predictions):
            for issue in prediction_issues(row):
                n += 1
                result['findings'].append({'layer': layer, 'record': row.get('match_id', row.get('fixture_id', str(i))), 'sport': row.get('sport', ''), 'selection': row.get('selection', ''), 'issue': issue, 'official_url': row.get('official_url', ''), 'file': str(pfile.relative_to(root)), 'index': i, 'status': 'needs review'})
        result['layers'].append({'layer': layer, 'rows': len(matches), 'predictions': len(predictions), 'findings': n})
    return result

STYLE = '''body{font:16px/1.6 system-ui,sans-serif;color:#172b40;background:#f3f6fa;margin:0}header,main{max-width:1200px;margin:auto;padding:24px}header{background:#172b40;color:white;max-width:none}header>div{max-width:1200px;margin:auto}nav a{color:#bde5ff;margin-right:20px}h1{font-size:2.2rem}a{color:#075a9c}section,.notice{background:white;padding:20px;border-radius:10px;margin:20px 0}.notice{border-left:5px solid #c37a00}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #d4dfeb}th{background:#e6edf6}caption{text-align:left;padding:12px;font-weight:bold}.scroll{overflow:auto}input{padding:12px;width:min(90%,500px);font:inherit}small{color:#536379}footer{padding:24px}'''

def link(url):
    return f'<a href="{escape(url, quote=True)}" rel="noreferrer">Official source ↗</a>' if https(url) else '— <strong>Unverified</strong>'

def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th scope="col">'+escape(h)+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in rows) + '</tbody></table></div>'

def page(title, content):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+' · OLBG evidence review</title><link rel="stylesheet" href="style.css"></head><body><header><div><strong>OLBG2 / Evidence integrity</strong><nav aria-label="Main"><a href="../index.html">Dashboard</a><a href="index.html">Audit overview</a><a href="flagged.html">Flagged for Review</a><a href="inventory.html">Source inventory</a></nav></div></header><main><h1>'+escape(title)+'</h1>'+content+'</main><footer>Audit date: 22 October 2026 · Research only, not betting advice. Model prices are estimates, not verified official facts.</footer><script src="filter.js"></script></body></html>'

def build(root=ROOT):
    report = audit(root)
    out = root / 'evidence'
    out.mkdir(exist_ok=True)
    (out / 'audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    (out / 'style.css').write_text(STYLE+'\n')
    (out / 'filter.js').write_text("document.querySelectorAll('[data-filter]').forEach(input=>input.addEventListener('input',()=>{const q=input.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(q));}));\n")
    search = '<p><label>Filter rows <input data-filter type="search" placeholder="Search sport, layer, selection or issue"></label></p>'
    flags = [[escape(f[k]) for k in ('layer','record','selection','issue')] + [f'<code>{escape(f["file"])} / predictions[{f["index"]}]</code>',link(f['official_url'])] for f in report['findings']]
    (out / 'flagged.html').write_text(page('Flagged for Review', '<p>These are reproducible internal inconsistencies or requirement gaps, not findings that an official source is wrong. Owners should re-fetch the cited official page before changing facts. Missing values remain blank.</p>'+search+table(['Layer','Record','Selection','Review finding','Local evidence location','Official review source'],flags)))
    rows = [[escape(r[k]) for k in ('layer','id','sport','event','status')] + [link(r['official_url'])] for r in report['inventory']]
    (out / 'inventory.html').write_text(page('Source inventory', '<p>All rows from five stored match layers, including unlined fixtures. Overlapping layers are deliberately not summed as unique matches. An HTTPS link is not evidence that its contents match the row or that it is currently reachable.</p>'+search+table(['Layer','Record','Sport','Event','Verification status','Source'], rows)))
    summary = ''.join(f'<li><a href="../{escape(x["layer"])}/index.html">{escape(x["layer"])}</a>: {x["rows"]} stored rows; {x["predictions"]} predictions; {x["findings"]} review findings.</li>' for x in report['layers'])
    content = '<p>A read-only quality gate across existing research layers. It does not originate new lines, upgrade inherited verification labels, or claim full live coverage.</p><div class="notice"><strong>Verification boundary:</strong> only two NHL fixtures were independently checked in this session. Other facts remain unverified by this audit. See <a href="nhl-check.html">the exact fields checked</a>. Source links alone do not establish verification.</div><section><h2>What needs attention</h2><p>'+str(len(report['findings']))+' prediction-level review findings. <a href="flagged.html">Review every flagged entry →</a></p><p>“High confidence” sometimes represents editorial conviction rather than a ≥70% model win chance. Do not read these as interchangeable. At fair odds, 70% probability means 1.4286 decimal; the -250 floor is 1.40, so the overlap is only 70%–71.43%.</p></section><section><h2>Existing category dashboards</h2><ul>'+summary+'</ul><p><a href="inventory.html">Search the row-level source inventory →</a> · <a href="audit.json">Download machine-readable findings</a></p></section><section><h2>Audit limitations</h2><p>Not an exhaustive line-by-line factual verification of every repository value. This pass checks every prediction record in the five named layers for length, explicit probability, price band, explicit ranking contradictions, and source URL structure. It does not verify players, recent form, availability, market completeness, calibration, or live freshness. No new betting recommendations are issued.</p></section>'
    (out / 'index.html').write_text(page('Evidence before confidence', content))
    check = json.loads((out / 'nhl-check.json').read_text())
    checked_rows = []
    for game in check['games']:
        checked_rows.append([escape(str(game[k])) for k in ('id', 'gameDate', 'venue', 'startTimeUTC', 'awayAbbrev', 'awayRecord', 'homeAbbrev', 'homeRecord', 'gameState')] + [link(check['official_url'])])
    (out / 'nhl-check.html').write_text(page('Limited official NHL check', '<p>'+escape(check['scope'])+'</p><p>'+escape(check['retrieval'])+'</p><p>These selected fields were transcribed from the retrieved response. They confirm the corresponding fixture ID, date, venue, start time and team records in the stored verified layer. They do not verify model probabilities, goal totals, player form or the other games. FUT is the state reported at retrieval, not a live status.</p><p><a href="nhl-check.json">Download selected-field evidence</a></p>'+table(['ID','Date','Venue','UTC start','Away','Away record','Home','Home record','State at retrieval','Official source'], checked_rows)))
    return report

if __name__ == '__main__':
    result = build()
    print(f"Audited {len(result['inventory'])} overlapping stored rows; {len(result['findings'])} prediction review findings")
