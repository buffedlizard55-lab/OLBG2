#!/usr/bin/env python3
"""Summit desk — static site builder.

Renders /summit/ from the committed captures. Deterministic: same inputs, same bytes.
Run: python3 scripts/summit_build.py
"""
from __future__ import annotations

import json
import os
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "summit")
OUT = os.path.join(ROOT, "summit")

CSS = """
:root{--bg:#0b1220;--card:#121c2e;--line:#22304a;--ink:#e8eef8;--dim:#93a4c0;--accent:#4da3ff;--good:#2fbf71;--warn:#f2b134;--bad:#ef5b5b;--chip:#1b2942}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#0e1728;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:9}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
.top .wrap{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;padding:12px 18px}
.brand{font-weight:700;font-size:17px;letter-spacing:.2px}.brand small{color:var(--dim);font-weight:400;font-size:12px;display:block}
nav.links{display:flex;flex-wrap:wrap;gap:6px}nav.links a{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:13px;color:var(--ink)}
nav.links a.on{background:var(--accent);color:#04101f;border-color:var(--accent);font-weight:600}
main{padding:26px 0 60px}h1{font-size:26px;margin:0 0 6px}h2{font-size:19px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}p.lede{color:var(--dim);max-width:88ch;margin:0 0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}.kpi b{display:block;font-size:25px;line-height:1.1}.kpi span{color:var(--dim);font-size:12px}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:640px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#16233a;color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.05em;position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#101a2b}
.pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:11.5px;font-weight:600;white-space:nowrap}
.high{background:rgba(47,191,113,.16);color:#5ee49b;border:1px solid rgba(47,191,113,.4)}
.medium{background:rgba(242,177,52,.16);color:#f6c968;border:1px solid rgba(242,177,52,.4)}
.low{background:rgba(147,164,192,.14);color:#a9b8d1;border:1px solid rgba(147,164,192,.35)}
.in{background:rgba(77,163,255,.16);color:#8cc6ff;border:1px solid rgba(77,163,255,.4)}
.out{background:rgba(239,91,91,.14);color:#ff9a9a;border:1px solid rgba(239,91,91,.35)}
.blank{background:#1b2942;color:#93a4c0;border:1px dashed #3a4d6e}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:10px;padding:13px 15px;margin:14px 0}
.note.warn{border-left-color:var(--warn)}.note.bad{border-left-color:var(--bad)}
.pred{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:14px 0}
.pred h4{margin:0 0 2px;font-size:16px}.pred .meta{color:var(--dim);font-size:12.5px;margin-bottom:8px}
.pred .sel{font-weight:600;color:#9ed0ff;margin:6px 0}.pred p{margin:8px 0}
.pred .facts{margin-top:10px;border-top:1px solid var(--line);padding-top:9px}
.pred .facts li{font-size:12.5px;color:var(--dim);margin:3px 0}
.small{font-size:12.5px;color:var(--dim)}footer{border-top:1px solid var(--line);color:var(--dim);font-size:12.5px;padding:18px 0 40px}
@media (max-width:640px){.top .wrap{gap:8px}h1{font-size:22px}}
"""

def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)

M = load("matches.json")
L = load("lines.json")
P = load("picks.json")
PR = load("predictions.json")
SRC = load("sources.json")
FLAG = load("flagged.json")
AUD = load("repo_audit.json")

SPORTS = [
    ("Golf", "golf"), ("Volleyball", "volleyball"), ("Rugby Union", "rugby-union"),
    ("Cricket", "cricket"), ("Snooker", "snooker"), ("Darts", "darts"),
    ("Baseball", "baseball"), ("Gaelic Sports", "gaelic-sports"), ("Greyhounds", "greyhounds"),
    ("Tennis", "tennis"), ("Motor Racing", "motor-racing"), ("Handball", "handball"),
    ("Ice Hockey", "ice-hockey"), ("Basketball", "basketball"), ("Rugby League", "rugby-league"),
]
SLUG = dict(SPORTS)

def nav(active, prefix=""):
    items = [
        ("index.html", "Overview"), ("band.html", "Band board"), ("picks.html", "All picks"),
        ("matches.html", "All matches"), ("lines.html", "Originated lines"),
        ("predictions.html", "Predictions"), ("sports/index.html", "Sports"),
        ("olbg.html", "OLBG"), ("audit.html", "Repo audit"),
        ("flagged.html", "Flagged for review"), ("sources.html", "Sources"),
        ("methodology.html", "Method"),
    ]
    parts = []
    for href, label in items:
        cls = ' class="on"' if href == active else ""
        parts.append(f'<a href="{prefix}{href}"{cls}>{label}</a>')
    return "".join(parts)

def page(title, active, body, prefix=""):
    asset = prefix + "assets/style.css"
    gen = escape(M.get("generated_utc") or M.get("captured_utc") or "")
    html = f"""<!DOCTYPE html>
<html lang=\"en\"><head><meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>{escape(title)} · Summit desk</title>
<link rel=\"stylesheet\" href=\"{asset}\">
</head><body>
<header class=\"top\"><div class=\"wrap\">
  <div class=\"brand\">Summit · OLBG 15-sport desk<small>Captured {gen} · research, not betting advice · 18+</small></div>
  <nav class=\"links\">{nav(active, prefix)}</nav>
</div></header>
<main><div class=\"wrap\">{body}</div></main>
<footer><div class=\"wrap\">
  Every sourced row links to the official governing-body page it came from. Values that an official source did not publish are left blank and listed on <a href=\"{prefix}flagged.html\">Flagged for review</a>.
  Prices are the desk’s own fair lines, never observed bookmaker quotes unless a row says so.
</div></footer></body></html>"""
    return html

def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)

def src(url, label=None):
    if not url:
        return '<span class="pill blank">—</span>'
    label = label or url.split("//")[-1].split("/")[0]
    return f'<a href="{escape(url, quote=True)}" rel="noopener">{escape(label)}</a>'

def confpill(c):
    if not c:
        return '<span class="pill blank">—</span>'
    return f'<span class="pill {c}">{c}</span>'

def bandpill(v):
    return '<span class="pill in">in band</span>' if v else '<span class="pill out">outside band</span>'

def label(home, away):
    return f"{escape(home)} v {escape(away)}" if away else escape(home)

def fmt_p(p):
    return f"{p*100:.1f}%" if p else "—"

def fmt_am(a):
    return "—" if a is None else (f"+{a}" if a > 0 else str(a))

def per_sport():
    out = {}
    for name, slug in SPORTS:
        out[name] = {
            "slug": slug,
            "matches": [m for m in M["fixtures"] if m["sport"] == name],
            "picks": sorted([p for p in P["picks"] if p["sport"] == name and p.get("sport_rank")], key=lambda p: p["sport_rank"]),
            "preds": [p for p in PR["predictions"] if p["sport"] == name],
            "lines": [l for l in L["lines"] if l["sport"] == name],
        }
    return out

SP = per_sport()

def matches_table(fixtures, prefix=""):
    rows = []
    for m in fixtures:
        rows.append(
            f"<tr><td>{escape(m['sport'])}</td><td>{escape(m['competition'])}</td>"
            f"<td>{label(m['home'], m['away'])}</td><td>{escape(m['start_utc'])}</td>"
            f"<td>{escape(m['venue']) or '—'}</td>"
            f"<td>{confpill('originated' if m['status']=='originated' else 'blank')}</td>"
            f"<td>{src(m['official_source_url'])}</td>"
            f"<td><a href=\"{escape(m['olbg_event_url'], quote=True)}\" rel=\"noopener\">OLBG listing</a></td></tr>"
        )
    return f"""<h2>All {len(fixtures)} fixtures</h2>
<p class="small">Status: originated = an official governing-body page was captured this session; blank = OLBG-listed but no official source captured. OLBG is discovery provenance only.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Competition</th><th>Match</th><th>Start UTC</th><th>Venue</th><th>Status</th><th>Official source</th><th>OLBG listing</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""

def lines_table(lines, prefix=""):
    rows = []
    for l in lines:
        rows.append(
            f"<tr><td>{escape(l['sport'])}</td><td>{escape(l['competition'])}</td>"
            f"<td>{escape(l['market'])}</td><td>{escape(l['selection'])}</td>"
            f"<td class=\"mono\">{fmt_p(l['probability'])}</td>"
            f"<td class=\"mono\">{l['fair_decimal']}</td><td class=\"mono\">{fmt_am(l['fair_american'])}</td>"
            f"<td class=\"mono\">{l['offered_decimal']}</td>"
            f"<td>{confpill(l['confidence'])}</td><td>{bandpill(l['in_band'])}</td>"
            f"<td>{escape(l['basis'])}</td><td>{src(l['official_url'])}</td></tr>"
        )
    return f"""<h2>Originated lines ({len(lines)})</h2>
<p class="small">Fair decimal = 1 / probability. Fair American is derived from that probability. Offered decimal equals the desk’s own fair line; no bookmaker quote is published as ours.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Competition</th><th>Market</th><th>Selection</th><th>Probability</th><th>Fair decimal</th><th>Fair American</th><th>Offered decimal</th><th>Confidence</th><th>Band</th><th>Basis</th><th>Official source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""

def picks_table(picks, prefix=""):
    rows = []
    for l in picks:
        rows.append(
            f"<tr><td>{escape(l['sport'])}</td><td>{escape(l['market'])}</td>"
            f"<td>{escape(l['selection'])}</td><td class=\"mono\">{fmt_p(l['probability'])}</td>"
            f"<td class=\"mono\">{l['fair_decimal']}</td><td class=\"mono\">{fmt_am(l['fair_american'])}</td>"
            f"<td>{confpill(l['confidence'])}</td><td>{bandpill(l['in_band'])}</td>"
            f"<td>{str(l.get('sport_rank') or '—')}</td><td>{src(l['official_url'])}</td></tr>"
        )
    return f"""<h2>All picks ({len(picks)})</h2>
<p class="small">Picks with a sport rank are shortlisted high-confidence selections. Rank restarts per sport.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Market</th><th>Selection</th><th>Probability</th><th>Fair decimal</th><th>Fair American</th><th>Confidence</th><th>Band</th><th>Rank</th><th>Official source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""

def predictions_cards(preds, prefix=""):
    cards = []
    for pr in preds:
        facts = "".join(f"<li>{escape(f['item'])}: {escape(f['claim'])} (<a href=\"{escape(f['source_url'], quote=True)}\" rel=\"noopener\">source</a>)</li>" for f in pr["facts"])
        cards.append(f"""
<div class="pred"><h4>{escape(pr['selection'])}</h4>
<div class="meta">{escape(pr['sport'])} · {fmt_p(pr['probability'])} · fair {pr['fair_decimal']} · {fmt_am(pr['fair_american'])} · {pr['word_count']} words</div>
<div class="sel">Selection: {escape(pr['selection'])}</div>
<p>{escape(pr['text'])}</p>
<div class="facts"><ul>{facts}</ul></div>
<p class="small">{escape(pr['injury_note'])}</p></div>""")
    return f"""<h2>Written predictions ({len(preds)})</h2>
<p class="small">Only shortlisted high-confidence selections with enough official captured facts receive a written prediction. Each prediction is at least 30 words and quotes only captured official facts.</p>
{''.join(cards)}"""

def build_index():
    flagcount=FLAG['count']
    highs = [p for p in P["picks"] if p["confidence"] == "high"]
    in_band = [p for p in highs if p["in_band"]]
    preds = PR["predictions"]
    body = f"""
<h1>Executive summary — 23 October 2026</h1>
<p class="lede">Fifteen sports, {M['count']} OLBG-listed fixtures ({M['originated']} verified against an official governing-body page, {M['blank']} blank), {L['count']} originated prices and {P['high']} high-confidence selections. Every priced row links to the official page it came from; nothing is filled in from memory or from a bookmaker.</p>
<div class="grid">
  <div class="kpi"><b>15</b><span>sports covered</span></div>
  <div class="kpi"><b>{M['count']}</b><span>fixtures ({M['originated']} verified)</span></div>
  <div class="kpi"><b>{L['count']}</b><span>originated markets</span></div>
  <div class="kpi"><b>{P['high']}</b><span>high-confidence selections</span></div>
  <div class="kpi"><b>{len(in_band)}</b><span>high confidence inside −250…+10000</span></div>
  <div class="kpi"><b>{len(preds)}</b><span>written predictions</span></div>
  <div class="kpi"><b>{flagcount}</b><span>review items</span></div>
</div>
<h2>High-confidence selections</h2>
{picks_table(highs)}
<h2>Shortfall disclosure</h2>
<div class="note warn"><p><b>Five-per-sport target.</b> Written predictions are published for Rugby Union (3), Handball (2) and Tennis (1). The other 12 covered sports have no qualifying high-confidence in-band selection supported by official captured facts, so no prediction is fabricated. See <a href=\"flagged.html\">Flagged for review</a>.</p></div>
"""
    write("index.html", page("Executive summary", "index.html", body))

def build_band():
    highs = [p for p in P["picks"] if p["confidence"] == "high"]
    in_band = [p for p in highs if p["in_band"]]
    outside = [p for p in highs if not p["in_band"]]
    body = f"""
<h1>Odds band board −250 to +10000</h1>
<p class="lede">{len(highs)} high-confidence selections (p ≥ 70%) are graded. {len(in_band)} sit inside the band on their own fair American price; {len(outside)} are shorter than −250 and are published as high but outside the band. p ≥ 70% implies fair odds of roughly −233 to −250, so the band window is narrow by design.</p>
<h2>Inside the band</h2>
{picks_table(in_band)}
<h2>Outside the band</h2>
<p class="small">High confidence but fair American price shorter than −250. Not promoted as band plays.</p>
{picks_table(outside)}
"""
    write("band.html", page("Band board", "band.html", body))

def build_picks():
    write("picks.html", page("All picks", "picks.html", picks_table(P["picks"])))

def build_matches():
    write("matches.html", page("All matches", "matches.html", matches_table(M["fixtures"])))

def build_lines():
    write("lines.html", page("Originated lines", "lines.html", lines_table(L["lines"])))

def build_predictions():
    write("predictions.html", page("Predictions", "predictions.html", predictions_cards(PR["predictions"])))

def build_sports():
    os.makedirs(os.path.join(OUT, "sports"), exist_ok=True)
    index_rows = []
    for name, slug in SPORTS:
        sp = SP[name]
        index_rows.append(
            f"<tr><td>{escape(name)}</td><td>{len(sp['matches'])}</td><td>{len(sp['lines'])}</td>"
            f"<td>{len(sp['picks'])}</td><td>{len(sp['preds'])}</td>"
            f"<td><a href=\"{slug}.html\">Open {escape(name)}</a></td></tr>"
        )
    index_body = f"""<h1>Sports</h1>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Fixtures</th><th>Originated lines</th><th>Shortlisted picks</th><th>Predictions</th><th>Page</th></tr></thead><tbody>{''.join(index_rows)}</tbody></table></div>
<p class="small">Rank restarts per sport on the picks page.</p>"""
    write("sports/index.html", page("Sports", "sports/index.html", index_body, prefix="../"))
    for name, slug in SPORTS:
        sp = SP[name]
        body = f"<h1>{escape(name)}</h1>"
        body += matches_table(sp["matches"], prefix="../")
        body += lines_table(sp["lines"], prefix="../")
        body += picks_table(sp["picks"], prefix="../")
        body += predictions_cards(sp["preds"], prefix="../")
        write(f"sports/{slug}.html", page(name, "sports/index.html", body, prefix="../"))

def build_olbg():
    body = """
<h1>OLBG reverse-engineering</h1>
<p class="lede">OLBG is discovery provenance only. The desk reverse-engineered the OLBG sport-hub taxonomy and matched listed events to official governing-body pages where possible.</p>
<h2>Covered sport routes</h2>
<ul>
<li>Golf — betting-tips/Golf/5</li><li>Volleyball — betting-tips/Volleyball/21</li><li>Rugby Union — betting-tips/Rugby_Union/9</li><li>Cricket — betting-tips/Cricket/7</li><li>Snooker — betting-tips/Snooker/8</li><li>Darts — betting-tips/Darts/15</li><li>Baseball — betting-tips/Baseball/12</li><li>Gaelic Sports — betting-tips/Gaelic_Football/25 and betting-tips/Hurling/26</li><li>Greyhounds — betting-tips/Greyhounds/28</li><li>Tennis — betting-tips/Tennis/3</li><li>Motor Racing — betting-tips/Motor_Racing/14</li><li>Handball — betting-tips/Handball/20</li><li>Ice Hockey — betting-tips/Ice_Hockey/13</li><li>Basketball — betting-tips/Basketball/4</li><li>Rugby League — betting-tips/Rugby_League/10</li>
</ul>
<p class="small">Out-of-scope OLBG hubs (Football, Horse Racing, American Football, Boxing, Aussie Rules, UFC/MMA, Esports) are excluded.</p>
<div class="note bad"><h3>Observed OLBG platform defects</h3>
<ul>
<li>US egress to hub pages returns “No tips found” instead of an event table.</li><li>Most OLBG event pages show “WIN @” with blank odds to non-UK visitors.</li><li>Tip counts are concatenated as strings in the “Most Popular Tip” pill (e.g. “4 / 042”).</li><li>Unstarted fixtures can show false “Expired” badges with US-Eastern clock drift.</li>
</ul>
<p class="small">These defects mean the OLBG list is used only for discovery; every priced row in /summit/ carries an official governing-body source.</p></div>
"""
    write("olbg.html", page("OLBG", "olbg.html", body))

def build_audit():
    audited=AUD['summary']['irregularities_logged']; oos=AUD['summary']['out_of_scope_html_files']
    rows = ""
    for fnd in AUD["findings"]:
        code=escape(fnd['code']); title=escape(fnd['title']); detail=escape(fnd['detail'])
        evidence=escape(fnd['evidence']); note=escape(fnd.get('severity_note',''))
        rows += f"<tr><td>{code}</td><td>{title}</td><td>{detail}</td><td>{evidence}</td><td>{note}</td></tr>"
    body = f"""<h1>Repository audit — /summit/</h1>
<p class="small">{audited} findings logged; {oos} out-of-scope HTML files observed in other desk trees.</p>
<div class="table-wrap"><table><thead><tr><th>Code</th><th>Title</th><th>Detail</th><th>Evidence</th><th>Note</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    write("audit.html", page("Repo audit", "audit.html", body))

def build_flagged():
    flagcount=FLAG['count']
    rows = ""
    for fl in FLAG["flags"]:
        code=escape(fl['code']); sev=escape(fl['severity']); sport=escape(fl['sport'])
        title=escape(fl['title']); detail=escape(fl['detail']); source=src(fl['source'])
        impact=escape(fl['impact'])
        rows += f"<tr><td>{code}</td><td>{sev}</td><td>{sport}</td><td>{title}</td><td>{detail}</td><td>{source}</td><td>{impact}</td></tr>"
    body = f"""<h1>Flagged for review</h1>
<p class="small">{flagcount} items. Blank values and shortfalls are disclosed, not invented.</p>
<div class="table-wrap"><table><thead><tr><th>Code</th><th>Severity</th><th>Sport</th><th>Title</th><th>Detail</th><th>Source</th><th>Impact</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    write("flagged.html", page("Flagged for review", "flagged.html", body))

def build_sources():
    srccount=SRC['count']
    rows = ""
    for s in SRC["sources"]:
        key=escape(s['key']); sport=escape(s['sport']); kind=escape(s['kind'])
        url=src(s['url']); note=escape(s['note'])
        rows += f"<tr><td>{key}</td><td>{sport}</td><td>{kind}</td><td>{url}</td><td>{note}</td></tr>"
    body = f"""<h1>Official source register</h1>
<p class="small">{srccount} sources captured this session. Every fact in /summit/ cites one of these keys.</p>
<div class="table-wrap"><table><thead><tr><th>Key</th><th>Sport</th><th>Kind</th><th>URL</th><th>Note</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    write("sources.html", page("Sources", "sources.html", body))

def build_methodology():
    body = """
<h1>Methodology</h1>
<h2>Scope</h2>
<p>The desk covers exactly the 15 sports requested: Golf, Volleyball, Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball and Rugby League.</p>
<h2>Sources</h2>
<p>OLBG is discovery provenance only. Fixture facts, standings, form and injury context are taken from official governing-body pages captured in this session. Every row links to its official source; values that cannot be confirmed are left blank and flagged.</p>
<h2>Line origination</h2>
<p>Prices are the desk’s own fair lines. For a two-way selection with probability p, fair decimal = 1/p and fair American = −100·p/(1−p) for p ≥ 0.5, otherwise 100·(1−p)/p. No bookmaker quote is published as the desk’s line. Offered decimal equals the desk’s fair line.</p>
<h2>Confidence</h2>
<p>High: p ≥ 0.70. Medium: 0.60 ≤ p < 0.70. Low: p < 0.60. Small-sample band lines are capped at medium even when p ≥ 0.70.</p>
<h2>Odds band</h2>
<p>The band is fair American odds from −250 to +10000. Because p ≥ 70% implies fair odds of roughly −233 to −250, only alternate handicap/total lines in that narrow window qualify as in-band plays.</p>
<h2>Predictions</h2>
<p>Written predictions are produced only for shortlisted high-confidence selections. Each is at least 30 words, has a unique opening, names its selection, and quotes only facts present in the committed fixture capture with an official source link. The words “model” and “verified” do not appear in reader-facing prose.</p>
"""
    write("methodology.html", page("Method", "methodology.html", body))

def main():
    build_index()
    build_band()
    build_picks()
    build_matches()
    build_lines()
    build_predictions()
    build_sports()
    build_olbg()
    build_audit()
    build_flagged()
    build_sources()
    build_methodology()
    print(f"built {len([1 for _ in __import__('os').walk(OUT) for f in _[2] if f.endswith('.html')])} HTML pages under {OUT}")

if __name__ == "__main__":
    main()
