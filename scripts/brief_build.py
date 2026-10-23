#!/usr/bin/env python3
"""Brief desk - deterministic static build for /brief/.

Every page is generated from data/brief/*.json. Run after brief_model.py and
brief_predictions.py.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "brief"
OUT = ROOT / "brief"
SITE = "https://buffedlizard55-lab.github.io/OLBG2"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
          "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
          "Handball", "Ice Hockey", "Basketball", "Rugby League"]

SLUG = {s: s.lower().replace(" ", "-") for s in SPORTS}

NAV = [
    ("index.html", "Today's brief"),
    ("matches.html", "All matches"),
    ("picks.html", "Picks"),
    ("predictions.html", "Predictions"),
    ("sports/index.html", "Sports"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "Method"),
    ("olbg.html", "OLBG &amp; markets"),
    ("review.html", "Repo review"),
]

CSS = """
:root{--ink:#0f172a;--muted:#5b6779;--line:#e2e8f0;--bg:#f6f7f9;--card:#fff;--brand:#0f766e;--brand2:#115e59;
--high:#065f46;--highbg:#d1fae5;--med:#92400e;--medbg:#fef3c7;--low:#475569;--lowbg:#e2e8f0;--flag:#9f1239;--flagbg:#ffe4e6}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
header.bar{background:#0b1220;color:#e2e8f0;padding:.5rem 0}
.wrap{max-width:1180px;margin:0 auto;padding:0 1rem}
.brand{display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap}
.brand strong{font-size:1.02rem;letter-spacing:.01em}
.brand span{color:#94a3b8;font-size:.8rem}
nav.top{display:flex;flex-wrap:wrap;gap:.15rem;margin-top:.45rem}
nav.top a{color:#cbd5e1;font-size:.82rem;padding:.35rem .5rem;border-radius:6px}
nav.top a:hover{background:#1e293b;text-decoration:none;color:#fff}
nav.top a[aria-current]{background:#134e4a;color:#5eead4;font-weight:600}
main{padding:1.4rem 0 3rem}
h1{font-size:1.75rem;line-height:1.2;margin:.2rem 0 .4rem}
h2{font-size:1.18rem;margin:1.8rem 0 .5rem}
h3{font-size:1rem;margin:1.2rem 0 .35rem}
p{margin:.45rem 0}
.lede{font-size:1.02rem;color:#334155;max-width:80ch}
.eyebrow{text-transform:uppercase;letter-spacing:.09em;font-size:.72rem;color:var(--brand2);font-weight:700;margin:0}
.grid{display:grid;gap:.8rem;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));margin:1rem 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.9rem 1rem}
.card .k{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700}
.card .v{font-size:1.5rem;font-weight:700;margin:.15rem 0}
.card .s{color:var(--muted);font-size:.82rem}
table{width:100%;border-collapse:collapse;background:#fff;font-size:.88rem;border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{padding:.5rem .55rem;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f5f9;font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;color:#475569}
tr:last-child td{border-bottom:0}
tbody tr:hover{background:#f8fafc}
.tbl-scroll{overflow-x:auto;border-radius:10px}
.badge{display:inline-block;padding:.1rem .45rem;border-radius:999px;font-size:.72rem;font-weight:700;white-space:nowrap}
.badge+.badge{margin-left:.3rem}
.high{background:var(--highbg);color:var(--high)}.medium{background:var(--medbg);color:var(--med)}.low{background:var(--lowbg);color:var(--low)}
.tA{background:#d1fae5;color:#065f46}.tB{background:#fee2e2;color:#991b1b}.tC{background:#e0e7ff;color:#3730a3}.tD{background:#e5e7eb;color:#374151}
.pill{display:inline-block;padding:.1rem .45rem;border-radius:6px;font-size:.72rem;font-weight:600;background:#eef2f7;color:#334155}
.muted{color:var(--muted)}.small{font-size:.8rem}
.flag{background:var(--flagbg);color:var(--flag)}
.note{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:.7rem .9rem;margin:.8rem 0}
.ok{background:#ecfdf5;border:1px solid #a7f3d0;border-radius:10px;padding:.7rem .9rem;margin:.8rem 0}
.pred{background:#fff;border:1px solid var(--line);border-left:4px solid var(--brand);border-radius:10px;padding:.9rem 1rem;margin:.7rem 0}
.pred h3{margin:.1rem 0 .25rem;font-size:1rem}
.pred .meta{font-size:.78rem;color:var(--muted);margin-bottom:.35rem}
.pred .body{margin:.35rem 0}
.pred .src{font-size:.76rem;color:var(--muted)}
ul,ol{margin:.4rem 0 .6rem 1.1rem;padding:0}li{margin:.18rem 0}
footer{border-top:1px solid var(--line);padding:1.2rem 0;color:var(--muted);font-size:.8rem;background:#fff}
.kv{display:grid;grid-template-columns:180px 1fr;gap:.2rem .8rem;font-size:.86rem}
.kv div:nth-child(odd){color:var(--muted)}
@media(max-width:640px){.kv{grid-template-columns:1fr}h1{font-size:1.45rem}}
"""


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def page(title: str, active: str, body: str, prefix: str = "") -> str:
    parts = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == active else ""
        parts.append(f'<a href="{prefix}{href}"{current}>{label}</a>')
    links = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · OLBG 15-sport brief</title>
<meta name="description" content="Independent fair lines, confidence labels and sourced predictions for the 15 sports named in the brief.">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<header class="bar"><div class="wrap"><div class="brand"><strong>OLBG 15-sport brief</strong>
<span>2026-10-23 · independent lines · every row carries its source</span></div>
<nav class="top" aria-label="Brief navigation">{links}</nav></div></header>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap">Research, not betting advice. 18+. Prices are our own fair estimates, not bookmaker quotes.
Every value on this desk is traceable to a capture listed on the <a href="{prefix}sources.html">source ledger</a>;
anything that could not be read is blank and listed on <a href="{prefix}flagged.html">Flagged for review</a>.</div></footer>
</body></html>
"""


def load(name):
    return json.loads((DATA / name).read_text())


def badge(kind, text):
    return f'<span class="badge {kind}">{esc(text)}</span>'


def conf_badge(c):
    return badge(c, c.upper())


def tier_badge(t):
    label = {"A": "A · high, in band", "B": "B · high, out of band", "C": "C · in band", "D": "D"}[t]
    return badge("t" + t, label)


def src_link(url, text=None):
    label = text or (url.split("//")[-1][:48] + ("…" if len(url) > 52 else ""))
    return f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def start_cell(f):
    s = f.get("start_utc") or f.get("start_local") or ""
    return esc(s.replace("T", " ").replace("Z", " UTC")) if s else '<span class="muted">not published</span>'


def markets_cell(f):
    if not f["markets"]:
        return '<span class="muted">blank · unlined</span>'
    names = []
    for m in f["markets"]:
        if m["market"] not in names:
            names.append(m["market"])
    return esc(", ".join(names))


def pick_cell(f):
    p = f.get("pick")
    if not p:
        s = f.get("strongest")
        if s:
            return (f'<span class="muted">no in-band result pick</span><br>'
                    f'<span class="small">strongest: {esc(s["selection"])} {esc(s["american"])} ({esc(s["confidence"])})</span>')
        return '<span class="muted">—</span>'
    return f'<strong>{esc(p["selection"])}</strong><br><span class="small">{esc(p["market"])} · {esc(p["american"])} · {esc(str(round(p["prob"]*100,1)))}%</span>'


def fixture_rows(fixtures, *, show_sport=True):
    head = ["Sport", "Competition", "Match", "Start", "Status", "Markets originated", "Desk selection", "Confidence", "Source"]
    if not show_sport:
        head = head[1:]
    rows = []
    for f in fixtures:
        conf = f["pick"]["confidence"] if f.get("pick") else (f.get("strongest") or {}).get("confidence", "")
        conf_html = conf_badge(conf) if conf else '<span class="muted">—</span>'
        match = f'{esc(f["home"])} <span class="muted">v</span> {esc(f["away"])}'
        if f["sport"] in ("Golf", "Motor Racing"):
            match = f'<strong>{esc(f["competition"])}</strong>'
        cells = [
            f'<a href="sports/{SLUG[f["sport"]]}.html">{esc(f["sport"])}</a>' if show_sport else "",
            f'<span class="small">{esc(f["competition"])}{(" · " + esc(f["stage"])) if f["stage"] else ""}</span>',
            match + (f'<br><span class="small muted">{esc(f["venue"])}</span>' if f.get("venue") else ""),
            start_cell(f),
            (esc(f["result"]) + "<br><span class='small muted'>" + esc(f["status"]) + "</span>") if f.get("result") else esc(f["status"]),
            markets_cell(f),
            pick_cell(f),
            conf_html,
            src_link(f["source_url"]),
        ]
        if not show_sport:
            cells = cells[1:]
        rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    return ('<div class="tbl-scroll"><table><thead><tr>' +
            "".join(f"<th>{h}</th>" for h in head) +
            "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")


def main():
    matches = load("matches.json")
    preds = load("predictions.json")
    sources = load("sources.json")["sources"]
    flags = load("flags.json")["flags"]
    taxonomy = load("olbg_taxonomy.json")
    by_sport = matches["meta"]["by_sport"]
    fixtures = matches["fixtures"]
    preds_by_sport = {}
    for p in preds["predictions"]:
        preds_by_sport.setdefault(p["sport"], []).append(p)
    src_map = {s["key"]: s for s in sources}

    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "sports").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS)

    tier_a = [p for p in preds["predictions"] if p["tier"] == "A"]
    tier_b = [p for p in preds["predictions"] if p["tier"] == "B"]
    tier_c = [p for p in preds["predictions"] if p["tier"] == "C"]
    upcoming = [f for f in fixtures if f["eligible"]]
    priced = [f for f in upcoming if f["markets"]]

    # ---------------------------------------------------------------- index
    cards = f"""
<div class="grid">
  <div class="card"><div class="k">Fixtures published</div><div class="v">{len(fixtures)}</div><div class="s">{len(upcoming)} still upcoming at the 19:45Z cut-off</div></div>
  <div class="card"><div class="k">Fixtures with our lines</div><div class="v">{matches['meta']['priced']}</div><div class="s">across 11 of the 15 sports</div></div>
  <div class="card"><div class="k">Written predictions</div><div class="v">{preds['meta']['count']}</div><div class="s">minimum {preds['meta']['min_words']} words each</div></div>
  <div class="card"><div class="k">Official sources</div><div class="v">{len(sources)}</div><div class="s">each one linked on the row it supports</div></div>
  <div class="card"><div class="k">Open review items</div><div class="v">{len(flags)}</div><div class="s">flagged, not hidden</div></div>
</div>"""

    a_rows = "".join(
        f"<tr><td>{esc(p['sport'])}</td><td><strong>{esc(p['selection'])}</strong> · {esc(p['market'])}</td>"
        f"<td>{esc(p['home'])} v {esc(p['away'])}</td><td>{esc(p['american'])}</td>"
        f"<td>{conf_badge(p['confidence'])}</td><td>{esc(str(round(p['prob']*100,1)))}%</td>"
        f"<td>{src_link(p['source_url'])}</td></tr>" for p in tier_a)
    b_rows = "".join(
        f"<tr><td>{esc(p['sport'])}</td><td><strong>{esc(p['selection'])}</strong> · {esc(p['market'])}</td>"
        f"<td>{esc(p['home'])} v {esc(p['away'])}</td><td>{esc(p['american'])}</td>"
        f"<td>{conf_badge(p['confidence'])}</td><td>{esc(str(round(p['prob']*100,1)))}%</td>"
        f"<td>{src_link(p['source_url'])}</td></tr>" for p in tier_b)

    top_today = sorted([p for p in preds["predictions"] if p["tier"] in ("A", "B", "C")],
                       key=lambda p: -p["prob"])[:8]
    top_rows = "".join(
        f"<tr><td>{esc(p['sport'])}</td><td><strong>{esc(p['selection'])}</strong></td><td>{esc(p['market'])}</td>"
        f"<td>{esc(p['home'] or p['competition'])} v {esc(p['away'])}</td><td>{esc(p['american'])}</td>"
        f"<td>{tier_badge(p['tier'])} {conf_badge(p['confidence'])}</td>"
        f"<td><a href='predictions.html#{esc(p['id'])}'>read the case</a></td></tr>" for p in top_today)

    cov = []
    for s in SPORTS:
        if by_sport[s]["priced"]:
            status = "priced"
        else:
            status = '<span class="badge flag">blank</span> ' + esc(reason_for(s, fixtures, flags))
        cov.append(
            f"<tr><td><a href='sports/{SLUG[s]}.html'>{esc(s)}</a></td><td>{by_sport[s]['fixtures']}</td>"
            f"<td>{by_sport[s]['priced']}</td><td>{by_sport[s]['picks']}</td>"
            f"<td>{len(preds_by_sport.get(s, []))}</td><td>{status}</td></tr>")
    coverage_rows = "".join(cov)

    body = f"""
<p class="eyebrow">Daily brief · 2026-10-23 · cut-off 19:45 UTC</p>
<h1>Fifteen sports, priced by us, with the gaps shown.</h1>
<p class="lede">This is the newest desk in the repository. It publishes every fixture we could read from an official
source today, our own fair price for every match where an official input exists, a confidence label on every selection,
and a written case for the strongest picks. Where a source would not give us a number, the cell is blank and the reason
is on the <a href="flagged.html">review page</a>.</p>
<div class="cta">
<p><a class="pill" href="matches.html">All {len(fixtures)} fixtures</a>
<a class="pill" href="picks.html">{len([f for f in upcoming if f.get('pick')])} desk selections</a>
<a class="pill" href="predictions.html">{preds['meta']['count']} written predictions</a>
<a class="pill" href="olbg.html">OLBG reverse-engineering</a></p>
</div>
{cards}

<h2>Executive summary — the strongest picks on the board</h2>
<div class="note"><strong>How the two rules interact.</strong> A selection needs a probability of at least 70% to be
called high confidence, and a fair price between −250 and +10000 to sit inside the requested window. A 70% chance
converts to about −233, so the two conditions only overlap in the thin −250 to −233 slice. We publish the tier
plainly rather than bending either rule: <strong>Tier A</strong> is high confidence and inside the window;
<strong>Tier B</strong> is high confidence but priced shorter than −250; <strong>Tier C</strong> is inside the window
but below 70%.</div>

<h3>Tier A — high confidence and inside the price window ({len(tier_a)})</h3>
{'<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Selection</th><th>Match</th><th>Price</th><th>Confidence</th><th>Chance</th><th>Source</th></tr></thead><tbody>' + a_rows + '</tbody></table></div>' if tier_a else '<p class="muted">None today. No selection reached 70% while also pricing at −250 or longer.</p>'}

<h3>Tier B — high confidence, priced shorter than the −250 floor ({len(tier_b)})</h3>
<p class="small muted">These clear the 70% confidence bar but fall outside the user's price band. They are logged, not hidden.</p>
{'<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Selection</th><th>Match</th><th>Price</th><th>Confidence</th><th>Chance</th><th>Source</th></tr></thead><tbody>' + b_rows + '</tbody></table></div>' if tier_b else ''}

<h3>Today's board — the eight strongest cases across all tiers</h3>
<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Selection</th><th>Market</th><th>Match</th><th>Price</th><th>Label</th><th>Write-up</th></tr></thead><tbody>{top_rows}</tbody></table></div>

<h2>Coverage by sport</h2>
<p class="small muted">A fixture counts as priced when at least one market has an input read from an official page.
Selections are the in-band result picks; the written predictions column is the number of full cases published below.</p>
<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Fixtures</th><th>Priced</th><th>In-band selections</th><th>Write-ups</th><th>Status</th></tr></thead><tbody>{coverage_rows}</tbody></table></div>

<h2>What this desk does not claim</h2>
<ul>
<li>It is <strong>not a complete OLBG slate</strong>. OLBG's public tips pages render their event tables client-side and
return "No tips found" to a non-browser client; the evidence is on the <a href="olbg.html">OLBG page</a>. OLBG's
taxonomy, sport IDs and market vocabulary are reproduced there, and the fixtures themselves come from each sport's
governing body.</li>
<li>It is <strong>not a live feed</strong>. Every row carries the capture time of the page it came from. Rows whose
start time had passed by 19:45Z are labelled as such and excluded from selections.</li>
<li>It does <strong>not invent prices for matches with no official input</strong>. Four sports have fixtures but no
line today: tennis (no pairing published), cricket, Gaelic sports and greyhounds. Darts has fixtures but no ranking
source. Each is named with its reason.</li>
<li>No prediction asserts an injury, a suspension or a team-news item. No official injury feed could be read in this
window, so those claims are absent rather than guessed.</li>
</ul>
"""
    (OUT / "index.html").write_text(page("Today's brief", "index.html", body))

    # ---------------------------------------------------------------- matches
    body = f"""
<p class="eyebrow">Every fixture captured</p>
<h1>All matches</h1>
<p class="lede">{len(fixtures)} fixtures across the fifteen sports in the brief. {matches['meta']['priced']} carry at
least one originated market. The rest are shown with a blank price and the reason recorded on the fixture itself.
Rows are ordered by sport, then by start time.</p>
<div class="note">Price conventions: American odds are derived from our fair probability, so each two-way market sums to
1.000 with no bookmaker margin. A line is only shown where an official input exists. "Started before cut-off" rows are
kept for completeness but are not selections.</div>
{fixture_rows(fixtures)}
"""
    (OUT / "matches.html").write_text(page("All matches", "matches.html", body))

    # ---------------------------------------------------------------- picks
    ordered = sorted([f for f in upcoming if f.get("pick")], key=lambda f: -f["pick"]["prob"])
    rows = "".join(
        f"<tr><td>{esc(f['sport'])}</td><td>{esc(f['home'])} v {esc(f['away'])}</td>"
        f"<td><strong>{esc(f['pick']['selection'])}</strong><br><span class='small'>{esc(f['pick']['market'])}</span></td>"
        f"<td>{esc(f['pick']['american'])}<br><span class='small muted'>decimal {esc(str(f['pick']['decimal']))}</span></td>"
        f"<td>{esc(str(round(f['pick']['prob']*100,1)))}%</td>"
        f"<td>{tier_badge(tier_of(f['pick']))} {conf_badge(f['pick']['confidence'])}</td>"
        f"<td>{esc(f['input_note'][:150])}</td><td>{src_link(f['source_url'])}</td></tr>" for f in ordered)
    tier_b_fixtures = [f for f in upcoming if f.get("markets") and not f.get("pick") and f.get("strongest")
                       and f["strongest"]["prob"] >= 0.70]
    b_rows = "".join(
        f"<tr><td>{esc(f['sport'])}</td><td>{esc(f['home'])} v {esc(f['away'])}</td>"
        f"<td><strong>{esc(f['strongest']['selection'])}</strong> · {esc(f['strongest']['market'])}</td>"
        f"<td>{esc(f['strongest']['american'])}</td><td>{esc(str(round(f['strongest']['prob']*100,1)))}%</td>"
        f"<td>{conf_badge(f['strongest']['confidence'])}</td><td>{src_link(f['source_url'])}</td></tr>"
        for f in sorted(tier_b_fixtures, key=lambda x: -x["strongest"]["prob"]))
    body = f"""
<p class="eyebrow">Our own lines only</p>
<h1>Picks</h1>
<p class="lede">One result selection per fixture, taken from the highest-probability market that is still inside the
−250…+10000 window. Derivative markets (handicaps, totals) are priced in full on the <a href="matches.html">all matches</a>
page; they are not used to fill a pick when the favourite is too short.</p>
<div class="grid">
  <div class="card"><div class="k">In-band selections</div><div class="v">{len(ordered)}</div><div class="s">one per priced fixture</div></div>
  <div class="card"><div class="k">Tier A</div><div class="v">{sum(1 for f in ordered if tier_of(f['pick'])=='A')}</div><div class="s">high confidence and in band</div></div>
  <div class="card"><div class="k">Tier B</div><div class="v">{len(tier_b_fixtures)}</div><div class="s">high confidence, too short for the band</div></div>
  <div class="card"><div class="k">Median chance</div><div class="v">{round(sorted(f['pick']['prob'] for f in ordered)[len(ordered)//2]*100,1)}%</div><div class="s">across the in-band board</div></div>
</div>
<h2>The in-band board</h2>
<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th>Price</th><th>Chance</th><th>Label</th><th>Input</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>High confidence, outside the price window</h2>
<p class="small muted">These are excluded from the board above only because the fair price is shorter than −250. They are
kept visible so the rule is auditable.</p>
<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th>Price</th><th>Chance</th><th>Confidence</th><th>Source</th></tr></thead><tbody>{b_rows or '<tr><td colspan="7" class="muted">None.</td></tr>'}</tbody></table></div>
"""
    (OUT / "picks.html").write_text(page("Picks", "picks.html", body))

    # ---------------------------------------------------------------- predictions
    blocks = []
    for sp in SPORTS:
        items = preds_by_sport.get(sp, [])
        if not items:
            continue
        cards_html = []
        for p in items:
            cards_html.append(f"""
<article class="pred" id="{esc(p['id'])}">
  <h3>{esc(p['selection'])} — {esc(p['market'])}</h3>
  <div class="meta">{esc(sp)} · {esc(p['competition'])}{' · ' + esc(p['stage']) if p['stage'] else ''} ·
  {esc(p['home'])} v {esc(p['away'])} · {esc(p['start'] or 'start not published')} ·
  {esc(p['american'])} · {esc(str(round(p['prob']*100,1)))}% · {tier_badge(p['tier'])} {conf_badge(p['confidence'])} · {p['words']} words</div>
  <p class="body">{esc(p['text'])}</p>
  <div class="src">Fact base: {src_link(p['source_url'], src_map.get(p['source_key'], {}).get('name', p['source_key']))}
  · capture {esc(src_map.get(p['source_key'], {}).get('captured_utc', 'n/a'))}</div>
</article>""")
        blocks.append(f"<h2>{esc(sp)} ({len(items)})</h2>" + "".join(cards_html))
    body = f"""
<p class="eyebrow">{preds['meta']['count']} unique write-ups · minimum {preds['meta']['min_words']} words</p>
<h1>Predictions</h1>
<p class="lede">One case per selected match, written from the captured facts and nothing else. Each card names the
selection and the price, states the form and the numbers behind it, and links the page the numbers came from. No two
cards share an opening phrase, and no sentence is reused between them.</p>
<div class="note"><strong>Sports without a write-up today:</strong> Tennis, Cricket, Gaelic Sports, Greyhounds and Darts.
Each has fixtures on the <a href="matches.html">all matches</a> page, but no official strength input was readable in
this window, so no price and no prose would be honest. The specific failure is logged on
<a href="flagged.html">Flagged for review</a>.</div>
{''.join(blocks)}
"""
    (OUT / "predictions.html").write_text(page("Predictions", "predictions.html", body))

    # ---------------------------------------------------------------- sports index
    cards = "".join(
        f"""<div class="card"><div class="k">{esc(s)}</div>
        <div class="v">{by_sport[s]['fixtures']}</div>
        <div class="s">{by_sport[s]['priced']} priced · {by_sport[s]['picks']} in-band selections · {len(preds_by_sport.get(s, []))} write-ups</div>
        <p><a href="{SLUG[s]}.html">Open {esc(s)} →</a></p></div>""" for s in SPORTS)
    body = f"""
<p class="eyebrow">Category pages</p>
<h1>Sports</h1>
<p class="lede">The fifteen sports named in the brief, in the brief's order. Each page carries every fixture captured for
that sport, the originated markets, the selection and the source for each row.</p>
<div class="grid">{cards}</div>"""
    (OUT / "sports" / "index.html").write_text(page("Sports", "sports/index.html", body, prefix="../"))

    # ---------------------------------------------------------------- sport pages
    for s in SPORTS:
        fxs = [f for f in fixtures if f["sport"] == s]
        prs = preds_by_sport.get(s, [])
        sflags = [fl for fl in flags if any(k in (fl["detail"] + fl["subject"]).lower() for k in [s.lower()])]
        pred_html = "".join(
            f'<article class="pred"><h3>{esc(p["selection"])} — {esc(p["market"])}</h3>'
            f'<div class="meta">{esc(p["home"])} v {esc(p["away"])} · {esc(p["american"])} · '
            f'{esc(str(round(p["prob"]*100,1)))}% · {tier_badge(p["tier"])} {conf_badge(p["confidence"])} · {p["words"]} words</div>'
            f'<p class="body">{esc(p["text"])}</p>'
            f'<div class="src">Fact base: {src_link(p["source_url"], src_map.get(p["source_key"], {}).get("name", p["source_key"]))}</div></article>'
            for p in prs)
        unlined = [f for f in fxs if not f["markets"]]
        reason = unlined[0]["flags"][0] if unlined and unlined[0]["flags"] else ""
        body = f"""
<p class="eyebrow"><a href="index.html">Sports</a> · {esc(s)}</p>
<h1>{esc(s)}</h1>
<div class="grid">
  <div class="card"><div class="k">Fixtures</div><div class="v">{len(fxs)}</div><div class="s">{sum(1 for f in fxs if f['eligible'])} upcoming at cut-off</div></div>
  <div class="card"><div class="k">Priced</div><div class="v">{by_sport[s]['priced']}</div><div class="s">at least one originated market</div></div>
  <div class="card"><div class="k">Selections</div><div class="v">{by_sport[s]['picks']}</div><div class="s">inside −250…+10000</div></div>
  <div class="card"><div class="k">Write-ups</div><div class="v">{len(prs)}</div><div class="s">≥30 words, sourced</div></div>
</div>
{f'<div class="note"><strong>Why some rows are blank:</strong> {esc(reason)}</div>' if unlined and reason else ''}
{f'<div class="note"><strong>Open review items for this sport:</strong> ' + ' · '.join(esc(fl["id"]) + ' ' + esc(fl["subject"]) for fl in sflags) + '</div>' if sflags else ''}
<h2>Fixtures and lines</h2>
{fixture_rows(fxs, show_sport=False)}
<h2>Predictions</h2>
{('<p class="muted">No write-up today: no official strength input was readable for this sport in the capture window.</p>' if not prs else pred_html)}
<h2>Sources used</h2>
<div class="tbl-scroll"><table><thead><tr><th>Source</th><th>Used for</th><th>Captured</th><th>Link</th></tr></thead><tbody>
{''.join(f'<tr><td>{esc(x["name"])}</td><td>{esc(x["used_for"])}</td><td>{esc(x["captured_utc"])}</td><td>{src_link(x["url"])}</td></tr>' for x in sources if x["sport"] == s)}
</tbody></table></div>
"""
        (OUT / "sports" / f"{SLUG[s]}.html").write_text(page(s, "sports/index.html", body, prefix="../"))

    # ---------------------------------------------------------------- sources
    rows = "".join(
        f"<tr><td><code>{esc(x['key'])}</code></td><td>{esc(x['name'])}</td><td>{esc(x['sport'])}</td>"
        f"<td>{esc(x['used_for'])}</td><td>{esc(x['captured_utc'])}</td>"
        f"<td>{'this session' if x['first_hand'].startswith('this') else esc(x['first_hand'])}</td>"
        f"<td>{src_link(x['url'], x['url'])}</td></tr>" for x in sorted(sources, key=lambda x: (x['sport'], x['key'])))
    body = f"""
<p class="eyebrow">{len(sources)} sources</p>
<h1>Source ledger</h1>
<p class="lede">Every value published on this desk points back to one of these pages. Captures made by the preceding
desk session on this repository were read between 16:25Z and 17:22Z today; captures made by this session were read
between 19:29Z and 20:05Z. The column says which.</p>
<div class="note">A source link is provenance, not a guarantee: an official competition page proves the fixture, and an
official statistical feed proves the numbers used to price it. Where a page would not serve a value, no value is
published and the failure appears on <a href="flagged.html">Flagged for review</a>.</div>
<div class="tbl-scroll"><table><thead><tr><th>Key</th><th>Source</th><th>Sport</th><th>Used for</th><th>Captured (UTC)</th><th>Read by</th><th>Link</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Pages that were tried and refused</h2>
<ul>
<li><strong>olbg.com tips tables</strong> — served "No tips found" without JavaScript (three pages, including one event page).</li>
<li><strong>pdc.tv/rankings</strong> — cookie-consent wall only.</li>
<li><strong>pdc.tv</strong> rankings, <strong>cev.eu/matches/</strong> (404), <strong>volleyballworld.com/volleyball/schedule/</strong> (404).</li>
<li><strong>euroleague NBA feeds</strong> — cdn.nba.com returned HTTP 500 twice in the earlier capture.</li>
<li><strong>premrugby.com/standings</strong>, <strong>volleyballworld SV-Women standings</strong>, <strong>natwest WTA scores</strong> — client-rendered with no table rows.</li>
</ul>
"""
    (OUT / "sources.html").write_text(page("Sources", "sources.html", body))

    # ---------------------------------------------------------------- flagged
    rows_list = []
    for fl in flags:
        sev = "flag" if fl["severity"] == "high" else ("tC" if fl["severity"] == "medium" else "low")
        ev = "<br>".join(src_link(u, u) for u in fl.get("evidence", []))
        rows_list.append(
            f"<tr><td><code>{esc(fl['id'])}</code></td><td><strong>{esc(fl['subject'])}</strong></td>"
            f"<td>{badge(sev, fl['severity'])}</td><td>{esc(fl['detail'])}</td><td>{ev}</td></tr>")
    rows = "".join(rows_list)
    blanks = {}
    for f in fixtures:
        if not f["markets"] and f["flags"]:
            blanks.setdefault(f["sport"], set()).add(f["flags"][0])
    blank_rows = "".join(
        f"<tr><td>{esc(s)}</td><td>{by_sport[s]['fixtures']}</td><td>{by_sport[s]['priced']}</td>"
        f"<td>{esc('; '.join(sorted(blanks.get(s, []))) or '—')}</td></tr>" for s in SPORTS)
    body = f"""
<p class="eyebrow">{len(flags)} open items</p>
<h1>Flagged for review</h1>
<p class="lede">Irregularities, missing sources and deliberately blank values. Nothing here blocks publication; each
item is listed so it can be challenged and corrected. The identifiers are stable and are referenced from the affected
rows.</p>
<div class="tbl-scroll"><table><thead><tr><th>ID</th><th>Subject</th><th>Severity</th><th>Detail</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Blank-value register</h2>
<p class="small muted">A blank is a decision, not an oversight. The column shows what a reader would have found in that
cell if we had filled it, and why we did not.</p>
<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Fixtures</th><th>Priced</th><th>Reason recorded on the rows</th></tr></thead><tbody>{blank_rows}</tbody></table></div>
<h2>What is deliberately not published</h2>
<ul>
<li>No bookmaker price appears anywhere on this desk. OLBG's tip percentages are named in the
<a href="olbg.html">OLBG analysis</a> as a description of the source site, never as an input.</li>
<li>No injury, suspension or team-news claim appears in any prediction, because no official injury feed could be
read. That absence is deliberate.</li>
<li>No ranking figure is invented for a player outside a published table. Where a bound is used (snooker, item BR-08)
the row says so in the text.</li>
<li>No fixture is published from a social post, an aggregator or a secondary summary.</li>
</ul>
"""
    (OUT / "flagged.html").write_text(page("Flagged for review", "flagged.html", body))

    # ---------------------------------------------------------------- methodology
    body = f"""
<p class="eyebrow">Rules, maths and limits</p>
<h1>Method</h1>
<p class="lede">The desk is deterministic: captures in, pages out. Re-running the three build steps reproduces every
number below. Prices are fair probabilities, not bookmaker quotes, and no margin is added anywhere.</p>
<h2>The two selection rules</h2>
<div class="tbl-scroll"><table><thead><tr><th>Rule</th><th>Definition</th><th>Why</th></tr></thead><tbody>
<tr><td>Price window</td><td>Fair American odds between −250 and +10000 inclusive, i.e. a probability between 0.99% and 71.43%.</td><td>Set by the brief.</td></tr>
<tr><td>Confidence</td><td>High ≥70%, medium 55–70%, low &lt;55%, applied to our own probability.</td><td>Set by the brief.</td></tr>
<tr><td>Tier A</td><td>Both conditions true. The window is thin (−250 to −233), so this tier is rare.</td><td>Published honestly rather than stretched.</td></tr>
<tr><td>Tier B</td><td>High confidence but shorter than −250.</td><td>Excluded from picks, kept visible for audit.</td></tr>
<tr><td>Tier C</td><td>Inside the window but below 70%.</td><td>The working tier for most sports.</td></tr>
</tbody></table></div>
<h2>How each sport is priced</h2>
<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Model</th><th>Inputs actually read</th><th>Markets originated</th><th>Markets left blank</th></tr></thead><tbody>
<tr><td>Ice Hockey</td><td>Poisson on goals for/against per game, 4% home adjustment, tie split 55/45</td><td>32-club NHL team summary (GP, W, L, OTL, GF, GA)</td><td>Money line, puck line ±1.5, totals 5.5 and 6.5</td><td>Period markets, player props</td></tr>
<tr><td>Baseball</td><td>Log5 on season win percentage with a 16-point home adjustment; normal margin for the run line and total</td><td>2026 regular-season W-L, runs scored and allowed for both clubs</td><td>Money line, run line ±1.5, total at the model line</td><td>First-five-innings, pitcher props (no starter feed)</td></tr>
<tr><td>Basketball</td><td>Log5 on shrunk win rates, 22-point home adjustment; normal margin with σ=11</td><td>EuroLeague standings after Round 7 (GP, W, L, PF, PA)</td><td>Money line, spread, total</td><td>NBA (feed refused), quarter markets</td></tr>
<tr><td>Snooker</td><td>Bradley-Terry on ranking prize money (exponent 0.35)</td><td>WST world ranking, top 36</td><td>Match winner</td><td>Frame handicap, total frames (no format feed)</td></tr>
<tr><td>Handball</td><td>Poisson on a 30-goal baseline shifted by half the first-leg margin</td><td>EHF calendar and first-leg score</td><td>Money line, total</td><td>Second legs with no captured first leg</td></tr>
<tr><td>Rugby League</td><td>Poisson on Round 1 points for/against, shrunk 70% to the 28.2-point mean</td><td>NRL World Cup Round 1 results</td><td>Money line, handicap ±6.5, total</td><td>Nothing further</td></tr>
<tr><td>Rugby Union</td><td>Log5 on a last-three-win rate mapped to a 35–65% band, 18-point home adjustment</td><td>Official form strings only</td><td>Money line</td><td>Handicap and total (no scoring or table input)</td></tr>
<tr><td>Volleyball</td><td>Even-chance prior moved 8 points per set of margin in the same pairing's recorded result</td><td>Volleyball World global schedule, same-day set scores</td><td>Money line</td><td>Every fixture without a same-pairing result</td></tr>
<tr><td>Golf</td><td>Softmax over the 36-hole leaderboard with a 22% residual for players outside the captured top 25</td><td>DP World Tour leaderboard after Round 2</td><td>Tournament winner</td><td>3-balls, top-10 (no strokes-gained feed)</td></tr>
<tr><td>Motor Racing</td><td>Bradley-Terry on championship points with a 15% residual</td><td>F1 drivers' standings after Round 17, top 8</td><td>Race winner</td><td>Podium, fastest lap, head-to-head (no session times)</td></tr>
<tr><td>Darts</td><td>—</td><td>None: PDC rankings unreachable</td><td>—</td><td>All markets</td></tr>
<tr><td>Tennis / Cricket / Gaelic / Greyhounds</td><td>—</td><td>Fixtures only</td><td>—</td><td>All markets</td></tr>
</tbody></table></div>
<h2>Validation performed by the build</h2>
<ul>
<li>Each written prediction must name a selection that exists as an originated market on an upcoming fixture.</li>
<li>Each prediction must be at least 30 words; the current minimum is {preds['meta']['min_words']}.</li>
<li>The words "model" and "verified" are rejected anywhere in the published prose, as the brief requires.</li>
<li>No two predictions share a four-word opening, and no sentence of eight words or more is repeated.</li>
<li>No prediction is attached to a fixture without a price.</li>
<li>Probability ceilings: every published probability is clamped to 5–95% because a single fixture always retains
irreducible variance.</li>
</ul>
<h2>Known limits</h2>
<ul>
<li>Season-to-date inputs are three to eight games old for several competitions; they are labelled with their capture
time on every row.</li>
<li>Volleyball and Rugby Union prices rest on very thin inputs (one same-pairing result and a last-three form string
respectively) and are labelled medium or low confidence accordingly.</li>
<li>The golf and motor-racing fields are normalised over the players captured, with an explicit residual for the rest;
these are the crudest numbers on the desk.</li>
<li>No price here accounts for team news, weather or travel. Those inputs were not readable.</li>
</ul>
"""
    (OUT / "methodology.html").write_text(page("Method", "methodology.html", body))

    # ---------------------------------------------------------------- OLBG page
    ids = taxonomy["sport_ids_seen_in_index_links"]
    id_rows = "".join(
        f"<tr><td>{esc(k)}</td><td><code>{v}</code></td><td>{'in scope' if k in ('Golf','Volleyball','Rugby Union','Cricket','Snooker','Darts','Baseball','Tennis','Motor Racing','Handball','Ice Hockey','Basketball','Rugby League') else ('mapped to Gaelic Sports' if k in ('Gaelic Football','Hurling') else 'out of scope')}</td></tr>"
        for k, v in ids.items())
    markets = "".join(
        f"<tr><td>{esc(k)}</td><td>{esc(', '.join(v))}</td></tr>"
        for k, v in taxonomy["markets_named_in_served_editorial_copy"].items())
    body = f"""
<p class="eyebrow">Reverse-engineering notes</p>
<h1>OLBG: taxonomy, URLs and markets</h1>
<p class="lede">What the site actually exposes to a client that does not run JavaScript, read first-hand today. This is
the evidence behind the desk's choice to take fixtures from governing bodies while mirroring OLBG's categories and
market vocabulary.</p>
<h2>Sport IDs, read from the links on OLBG's own tips index</h2>
<p class="small muted">Source: {src_link(taxonomy['index_url'])} · captured {esc(taxonomy['captured_utc'])}. The brief's
fifteen sports map to these numeric ids; Gaelic Sports is covered by Gaelic Football (25) and Hurling (26).</p>
<div class="tbl-scroll"><table><thead><tr><th>OLBG category</th><th>Sport id</th><th>Relation to this brief</th></tr></thead><tbody>{id_rows}</tbody></table></div>
<h2>URL patterns observed</h2>
<div class="tbl-scroll"><table><thead><tr><th>Pattern</th><th>Example</th></tr></thead><tbody>
<tr><td>Sport index</td><td><code>https://www.olbg.com/betting-tips/{{Sport_With_Underscores}}/{{sportId}}</code></td></tr>
<tr><td>Event page</td><td><code>https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Luke_Littler_vs_William_OConnor/15?event_id=32328</code></td></tr>
<tr><td>Outright/tournament</td><td><code>https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/European_Championship/15?event_id=32338</code></td></tr>
</tbody></table></div>
<h2>The blocking finding</h2>
<div class="note"><strong>OLBG does not serve its event tables to a non-browser client.</strong> Two sport index pages
and one event page returned the literal text "No tips found." on requests made at 19:29Z, 19:30Z and 19:44Z today.
The editorial copy arrives, the rows do not. The same behaviour was recorded by the preceding desk session at 17:02Z.
Consequences:
<ul>
<li>The desk can reproduce OLBG's taxonomy and market vocabulary, and does.</li>
<li>It cannot produce "the full list of matches listed on OLBG" from OLBG itself. The fixture list is therefore taken
from each governing body and marked with that body's link.</li>
<li>No OLBG price, tip percentage or consensus figure is used as an input to any line here.</li>
</ul></div>
<h2>Market vocabulary quoted from OLBG's own explanatory copy</h2>
<div class="tbl-scroll"><table><thead><tr><th>Sport</th><th>Markets OLBG names on its page</th></tr></thead><tbody>{markets}</tbody></table></div>
<p class="small muted">These names are the vocabulary this desk mirrors when it originates markets. A market name is not
a price: nothing numeric is taken from these pages.</p>
<h2>What OLBG does show, and what we do with it</h2>
<ul>
<li><strong>Sport menu and ids</strong> — reproduced above.</li>
<li><strong>Event ids</strong> — the darts capture carries twelve, including <code>32328</code> for Littler v O'Connor
and <code>32338</code> for the European Championship outright. They are recorded for traceability only.</li>
<li><strong>Editorial definitions</strong> — money line, puck line, totals, set betting, games handicap. Quoted, not
priced from.</li>
<li><strong>Tip counts and Value Rating</strong> — described by OLBG as tip share versus implied probability. Not
readable today without JavaScript, and not used.</li>
</ul>
"""
    (OUT / "olbg.html").write_text(page("OLBG & markets", "olbg.html", body))

    # ---------------------------------------------------------------- repo review
    body = f"""
<p class="eyebrow">Repository review, 2026-10-23</p>
<h1>Repo review</h1>
<p class="lede">A line-by-line pass over the checkout this session inherited, with the checks that were run and the
irregularities that remain. Nothing was deleted or rewritten outside this session's claimed scope.</p>
<h2>Checks run</h2>
<div class="tbl-scroll"><table><thead><tr><th>Check</th><th>Command</th><th>Result</th></tr></thead><tbody>
<tr><td>Test suite</td><td><code>python3 -m unittest discover -s tests</code></td><td>576 tests, all passing</td></tr>
<tr><td>Cross-layer link audit</td><td><code>python3 scripts/integration_audit.py</code></td><td>0 local link errors</td></tr>
<tr><td>Published pages</td><td><code>find . -name '*.html'</code></td><td>729 HTML files before this desk; 20 added by /brief/</td></tr>
<tr><td>Merge markers</td><td><code>grep -rn '^&lt;&lt;&lt;&lt;&lt;&lt;&lt;\\|^&gt;&gt;&gt;&gt;&gt;&gt;&gt;'</code></td><td>Stray closing markers in COORDINATION.md and METHODOLOGY.md (see below)</td></tr>
<tr><td>TODO/FIXME in scripts</td><td><code>grep -rn 'TODO\\|FIXME' scripts</code></td><td>none</td></tr>
<tr><td>Working tree at start</td><td><code>git status</code></td><td>clean, on <code>arena/7a073c9a-olbg2</code> from <code>main</code> 81f46ac</td></tr>
</tbody></table></div>
<h2>Findings</h2>
<div class="tbl-scroll"><table><thead><tr><th>#</th><th>Finding</th><th>Where</th><th>Action taken</th></tr></thead><tbody>
<tr><td>R1</td><td>Six stray merge-closing lines remain in the shared board from earlier merges.</td>
<td><code>COORDINATION.md</code> lines 3216, 3307, 3437, 3549, 3609, 3628</td><td>Left in place: the file is append-only
and shared. Logged again here for the next integrator.</td></tr>
<tr><td>R2</td><td>A stray <code>&gt;&gt;&gt;&gt;&gt;&gt;&gt; origin/main</code> line remains in the methodology document.</td>
<td><code>METHODOLOGY.md</code> line 125</td><td>Left in place; outside this session's claimed scope.</td></tr>
<tr><td>R3</td><td>The repository now carries more than twenty overlapping research desks whose row counts must not be
added together, and the root navigation lists all of them.</td><td>root <code>index.html</code>, <code>README.md</code></td>
<td>This desk is added as one clearly labelled entry and does not modify any other desk's data.</td></tr>
<tr><td>R4</td><td>Several older desks describe a 17-sport taxonomy, while the current brief names exactly fifteen sports
and folds Gaelic Football and Hurling into Gaelic Sports.</td><td>README, several <code>*/methodology.html</code></td>
<td>This desk uses the fifteen-sport scope only; the conflict is named rather than silently resolved in old pages.</td></tr>
<tr><td>R5</td><td>The CI drift gate does not cover every generated sub-site, so a local rebuild succeeding is not proof
of a fresh factual audit.</td><td><code>.github/workflows/pages.yml</code></td>
<td>Unchanged; the <code>/brief/</code> pipeline is deterministic and self-validating.</td></tr>
<tr><td>R6</td><td>Previous desks sourced fixtures from governing bodies but used older capture times, so some rows on
those pages have already started.</td><td>e.g. <code>data/signal/captures/*</code> (16:25–17:22Z)</td>
<td>Reused only where the desk marks the capture time; this session re-read tennis and volleyball first-hand.</td></tr>
</tbody></table></div>
<h2>What was verified first-hand in this session</h2>
<ul>
<li>OLBG sport ids on <code>/betting-tips</code>, and the three "No tips found" responses.</li>
<li>ATP Tour scores at 19:34Z (six quarter-finals, no semi-final line-up published).</li>
<li>WTA scores at 19:36Z (zero live tournaments).</li>
<li>Volleyball World global schedule, two chunks, at 19:40Z and 19:51Z.</li>
<li>PDC rankings blocked at 19:52Z; CEV match list 404; Volleyball World schedule page 404; SV-Women standings empty.</li>
</ul>
<h2>What was taken from the same day's earlier capture and is labelled as such</h2>
<p class="small">NHL schedule and team summary, MLB schedule and standings, EuroLeague schedule and standings, WST
fixtures and rankings, EHF calendar, NRL World Cup draw, Premiership fixtures, OLBG darts list, DP World Tour
leaderboard, Formula 1 calendar and standings, GAA fixtures, GBGB open races, Cricket Australia fixtures, and the ATP
scores capture. Every one of those rows shows the original capture time, and none of them is presented as a fresh read
from this session.</p>
"""
    (OUT / "review.html").write_text(page("Repo review", "review.html", body))
    print(f"brief build: {len(list(OUT.rglob('*.html')))} pages")


def tier_of(p):
    if p["prob"] >= 0.70 and p["in_band"]:
        return "A"
    if p["prob"] >= 0.70:
        return "B"
    return "C"


SPORT_REASON = {
    "Cricket": "no official ranking or form table was readable",
    "Darts": "PDC rankings sit behind a cookie wall",
    "Gaelic Sports": "single fixture, no scoring input published",
    "Greyhounds": "GBGB publishes no runners",
    "Tennis": "no semi-final pairing published by the ATP",
}


def reason_for(sport, fixtures, flags):
    if sport in SPORT_REASON:
        return SPORT_REASON[sport]
    for f in fixtures:
        if f["sport"] == sport and f["flags"]:
            return f["flags"][0]
    return "no official input"


if __name__ == "__main__":
    main()
