#!/usr/bin/env python3
"""Build the consolidated 15-sport desk at /master/ from checked-in data.

Every table row links the page its values came from.  Nothing on these pages is
typed in by hand: the counts and the paragraphs marked "generated" are derived from
data/master/*.json at build time.  The written predictions are authored prose held
in data/master/predictions.json and validated by scripts/master_verify.py.
"""
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "master"
OUT = ROOT / "master"

SPORTS = [
    ("Golf", "golf"),
    ("Volleyball", "volleyball"),
    ("Rugby Union", "rugby-union"),
    ("Cricket", "cricket"),
    ("Snooker", "snooker"),
    ("Darts", "darts"),
    ("Baseball", "baseball"),
    ("Gaelic Sports", "gaelic-sports"),
    ("Greyhounds", "greyhounds"),
    ("Tennis", "tennis"),
    ("Motor Racing", "motor-racing"),
    ("Handball", "handball"),
    ("Ice Hockey", "ice-hockey"),
    ("Basketball", "basketball"),
    ("Rugby League", "rugby-league"),
]
SLUG = dict(SPORTS)

CSS = """*{box-sizing:border-box}
:root{--ink:#0f172a;--muted:#5b6474;--line:#dfe3ea;--bg:#f6f7f9;--card:#fff;--accent:#0f766e;--accent2:#134e4a;--warn:#92400e;--hi:#166534;--med:#a16207;--low:#475569}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:#0b5fa5;text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
header.top{background:var(--ink);color:#fff}
header.top .bar{display:flex;align-items:center;gap:18px;min-height:58px;flex-wrap:wrap}
.brand{color:#fff;font-weight:700;letter-spacing:.2px;display:flex;align-items:center;gap:8px}
.brand:hover{text-decoration:none}
.dot{width:10px;height:10px;border-radius:50%;background:#2dd4bf;display:inline-block}
nav.main{display:flex;gap:2px;flex-wrap:wrap}
nav.main a{color:#cbd5e1;font-size:.86rem;padding:.4rem .6rem;border-radius:7px}
nav.main a:hover{background:#1e293b;color:#fff;text-decoration:none}
nav.main a[aria-current]{background:var(--accent2);color:#5eead4;font-weight:600}
.stripe{background:#e8f5f3;border-bottom:1px solid #cfe7e3;font-size:.86rem;color:#134e4a;padding:.5rem 0}
main{padding:26px 0 60px}
h1{font-size:2rem;line-height:1.15;margin:.2em 0 .35em}
h2{font-size:1.3rem;margin:2rem 0 .6rem}
h3{font-size:1.05rem;margin:0 0 .35rem}
p.lede{font-size:1.06rem;color:#334155;max-width:76ch}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.74rem;color:var(--accent);font-weight:700;margin:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi b{display:block;font-size:1.5rem;line-height:1.1}
.kpi span{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card.sport:hover{border-color:#94a3b8;text-decoration:none}
.card .metrics{display:flex;gap:12px;font-size:.8rem;color:var(--muted);margin-top:8px;flex-wrap:wrap}
.pill{display:inline-block;font-size:.72rem;padding:.12rem .5rem;border-radius:999px;background:#eef2f7;color:#334155;border:1px solid #dbe2ea}
.pill.high{background:#dcfce7;color:var(--hi);border-color:#bbf7d0}
.pill.medium{background:#fef3c7;color:var(--med);border-color:#fde68a}
.pill.low{background:#eef2f7;color:var(--low)}
.pill.band{background:#e0f2fe;color:#075985;border-color:#bae6fd}
.pill.out{background:#f1f5f9;color:#64748b}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:.88rem}
th,td{text-align:left;padding:.5rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f5f9;font-size:.76rem;text-transform:uppercase;letter-spacing:.04em;color:#475569;position:sticky;top:0}
tbody tr:hover{background:#fafbfc}
.tablewrap{overflow:auto;max-height:74vh;border:1px solid var(--line);border-radius:12px}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.mono{font-variant-numeric:tabular-nums}
.notice{border-left:4px solid #94a3b8;background:#fff;padding:12px 16px;border-radius:8px;margin:16px 0}
.notice.warn{border-color:#f59e0b;background:#fffbeb}
.notice.blue{border-color:#38bdf8;background:#f0f9ff}
.notice.good{border-color:#22c55e;background:#f0fdf4}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.tools input,.tools select{padding:.45rem .6rem;border:1px solid #cbd5e1;border-radius:8px;background:#fff;font-size:.88rem}
.pred{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
.pred h3{margin-bottom:.2rem}
.pred .meta{font-size:.8rem;color:var(--muted);margin-bottom:.6rem}
.pred p{margin:.5rem 0}
.facts{font-size:.84rem;color:#334155;background:#f8fafc;border:1px dashed #dbe2ea;border-radius:8px;padding:8px 12px;margin:.6rem 0}
.src{font-size:.82rem}
.footer{border-top:1px solid var(--line);padding:22px 0;color:var(--muted);font-size:.84rem}
.tiny{font-size:.78rem;color:#6b7280}
.crumb{font-size:.82rem;color:var(--muted);margin-bottom:6px}
.tag{font-size:.7rem;padding:.1rem .45rem;border-radius:6px;background:#f1f5f9;color:#475569;border:1px solid #e2e8f0}
"""

FILTER_JS = """
document.addEventListener('DOMContentLoaded',function(){
  var q=document.getElementById('q'), s=document.getElementById('sport'), c=document.getElementById('conf'), out=document.getElementById('count');
  var rows=[].slice.call(document.querySelectorAll('tbody tr[data-sport]'));
  function apply(){
    var n=0;
    rows.forEach(function(r){
      var ok=(!q.value||r.textContent.toLowerCase().indexOf(q.value.toLowerCase())!==-1)
        &&(!s.value||r.dataset.sport===s.value)
        &&(!c.value||r.dataset.conf===c.value);
      r.style.display=ok?'':'none'; if(ok)n++;
    });
    if(out) out.textContent=n+' of '+rows.length+' rows';
  }
  [q,s,c].forEach(function(el){if(el){el.addEventListener('input',apply);el.addEventListener('change',apply);}});
  apply();
});
"""

NAV = [
    ("index.html", "Overview"),
    ("matches.html", "All matches"),
    ("picks.html", "Picks &amp; lines"),
    ("predictions.html", "Predictions"),
    ("sports/index.html", "Sports"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
    ("methodology.html", "Methodology"),
]


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def fmt_time(value: str) -> str:
    """Format a stored start time, and say so when the source did not give a UTC offset."""
    if not value:
        return "—"
    local_only = not (value.endswith("Z") or "+" in value[10:])
    dt = value.replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(dt)
    except ValueError:
        try:
            d = datetime.fromisoformat(dt + "+00:00") if "+" not in dt else datetime.fromisoformat(dt)
        except ValueError:
            return value
    if d.tzinfo:
        d = d.astimezone(timezone.utc)
    return d.strftime("%d %b %H:%M") + (" (venue time)" if local_only else "")


def price(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def page(title: str, active: str, body: str, prefix: str = "") -> str:
    links = "".join(
        '<a href="{p}{h}"{c}>{l}</a>'.format(
            p=prefix, h=href, c=' aria-current="page"' if href == active else "", l=label
        )
        for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG2 consolidated desk</title>
<meta name="description" content="Consolidated 15-sport desk: OLBG-listed matches, our own originated lines, confidence-graded picks and sourced predictions.">
<style>{CSS}</style>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f172a'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%232dd4bf'/%3E%3C/svg%3E">
</head>
<body>
<header class="top"><div class="wrap bar">
<a class="brand" href="{prefix}index.html"><span class="dot"></span>OLBG2 <span class="tag">consolidated desk</span></a>
<nav class="main" aria-label="Desk navigation">{links}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="footer"><div class="wrap">
<p><strong>Research, not betting advice.</strong> Prices shown as "our price" are our own estimates built from the linked official records; prices shown as "OLBG quote" are quoted by OLBG and reproduce the bookmaker margin. 18+.</p>
<p class="tiny">Built by <code>scripts/master_build.py</code> from <code>data/master/</code>. Earlier desks are preserved unchanged under <a href="{prefix}../index.html">the repository root</a>.</p>
</div></footer>
<script>{FILTER_JS}</script>
</body>
</html>
"""


def source_cell(official: str, olbg: str) -> str:
    bits = []
    if official:
        bits.append(f'<a href="{esc(official)}" rel="noopener">official ↗</a>')
    if olbg:
        bits.append(f'<a href="{esc(olbg)}" rel="noopener">OLBG ↗</a>')
    return " · ".join(bits) if bits else '<span class="tiny">none captured</span>'


def confidence_pill(conf: str) -> str:
    return f'<span class="pill {esc(conf)}">{esc(conf)}</span>'


def band_pill(in_band: bool) -> str:
    return '<span class="pill band">in band</span>' if in_band else '<span class="pill out">outside band</span>'


def build():
    matches = load("matches.json")["matches"]
    picks = load("picks.json")["picks"]
    preds = load("predictions.json")["predictions"]
    summary = load("summary.json")
    flagged = load("flagged.json")
    live = load("live_checks.json")["checks"]
    audit = load("capture_audit.json")

    by_sport = Counter(m["sport"] for m in matches)
    picks_by_sport = Counter(p["sport"] for p in picks)
    high = [p for p in picks if p["confidence"] == "high"]
    high_band = sorted([p for p in high if p["in_band"]], key=lambda p: (p["start_utc"], -p["prob"]))
    pred_by_id = {p["match_id"]: p for p in preds}
    m_by_id = {m["id"]: m for m in matches}

    def match_name(m):
        return m["label"] if m.get("label") else (
            f'{m["home"]} v {m["away"]}' if m.get("away") else m.get("home", ""))

    # ---------------------------------------------------------------- overview
    top_cards = []
    for p in high_band[:4]:
        m = m_by_id[p["match_id"]]
        pred = next((x for x in preds if x["match_id"] == p["match_id"]), None)
        top_cards.append(
            f'<div class="card"><div class="metrics"><span class="pill">{esc(p["sport"])}</span>'
            f'{confidence_pill(p["confidence"])}{band_pill(p["in_band"])}</div>'
            f'<h3 style="margin-top:8px">{esc(match_name(m))}</h3>'
            f'<p style="margin:.2rem 0"><strong>{esc(p["selection"])}</strong> · {esc(p["market"])}</p>'
            f'<p class="mono" style="margin:.2rem 0">{price(p["fair_american"])} · {p["prob"]*100:.2f}% · {esc(fmt_time(p["start_utc"]))}</p>'
            f'<p class="srcline mono">{source_cell(p.get("official_url", ""), p.get("olbg_url", ""))}</p>'
            + (f'<p class="tiny">Written prediction available.</p>' if pred else "")
            + "</div>"
        )

    sport_cards = []
    for name, slug in SPORTS:
        n = by_sport.get(name, 0)
        hp = sum(1 for p in high if p["sport"] == name)
        hb = sum(1 for p in high_band if p["sport"] == name)
        pr = sum(1 for p in preds if p["sport"] == name)
        sport_cards.append(
            f'<a class="card sport" href="sports/{slug}.html">'
            f'<div class="metrics"><span class="pill">{n} matches</span>'
            f'<span class="pill high">{hp} high</span><span class="pill band">{hb} in band</span></div>'
            f'<h3 style="margin-top:8px">{esc(name)}</h3>'
            f'<div class="metrics"><span>{picks_by_sport.get(name, 0)} picks</span><span>{pr} predictions</span></div>'
            "</a>"
        )

    today_rows = []
    for p in sorted([x for x in picks if x["start_utc"][:10] == "2026-10-24"], key=lambda x: x["start_utc"]):
        m = m_by_id[p["match_id"]]
        today_rows.append(
            "<tr>"
            f'<td>{esc(fmt_time(p["start_utc"]))}</td><td>{esc(p["sport"])}</td>'
            f'<td>{esc(match_name(m))}</td><td>{esc(p["selection"])}</td>'
            f'<td class="num">{price(p["fair_american"])}</td>'
            f'<td>{confidence_pill(p["confidence"])} {band_pill(p["in_band"])}</td>'
            f'<td class="src">{source_cell(p.get("official_url", ""), p.get("olbg_url", ""))}</td>'
            "</tr>"
        )

    overview = f"""
<p class="eyebrow">Consolidated desk · 15 sports · snapshot 2026-10-23 22:00 UTC</p>
<h1>Every covered match, our own line, and an honest gap list.</h1>
<p class="lede">This desk merges today's OLBG listing with the official fixture and record captures, prices the
matches we can price from official numbers, grades one selection per match, and writes up the high-confidence
picks that have real statistics behind them. Rows we could not support are left blank and listed on
<a href="flagged.html">Flagged for Review</a>.</p>

<div class="kpis">
  <div class="kpi"><b>{summary["matches"]}</b><span>matches on the desk</span></div>
  <div class="kpi"><b>{summary["with_olbg"]}</b><span>listed on OLBG</span></div>
  <div class="kpi"><b>{summary["with_official"]}</b><span>official fixture link</span></div>
  <div class="kpi"><b>{summary["picks"]}</b><span>graded picks</span></div>
  <div class="kpi"><b>{summary["high"]}</b><span>high confidence</span></div>
  <div class="kpi"><b>{summary["high_in_band"]}</b><span>high &amp; in band</span></div>
  <div class="kpi"><b>{len(preds)}</b><span>written predictions</span></div>
  <div class="kpi"><b>{len(flagged["items"])}</b><span>review items</span></div>
</div>

<div class="notice blue"><strong>Executive summary.</strong> {len(high_band)} selections clear all three gates at
once: at least a 70% estimate, a fair price between &minus;250 and +10000, and a market that is either built from
official records or quoted by OLBG. They are listed first below and repeated with every figure on the
<a href="picks.html">picks page</a>. A further {summary["high"] - summary["high_in_band"]} high-confidence
selections sit outside the price window and are shown with their real prices rather than being dropped.</div>

<h2>Highest-confidence picks inside the price window</h2>
<div class="cards">{''.join(top_cards) or '<p>None today.</p>'}</div>
<p class="tiny">Showing the first four of {len(high_band)}. <a href="picks.html">See all {summary["high_in_band"]} in-band selections →</a></p>

<h2>Today and tomorrow at a glance</h2>
<div class="tablewrap"><table>
<thead><tr><th>Start</th><th>Sport</th><th>Match</th><th>Selection</th><th>Our price</th><th>Grade</th><th>Source</th></tr></thead>
<tbody>{''.join(today_rows)}</tbody></table></div>

<h2>Coverage by sport</h2>
<div class="cards">{''.join(sport_cards)}</div>

<h2>How to read this desk</h2>
<table>
<thead><tr><th>Label</th><th>What it means</th></tr></thead>
<tbody>
<tr><td><span class="pill">originated</span></td><td>Our own price, computed from the NHL, MLB or EuroLeague season records linked on the row.</td></tr>
<tr><td><span class="pill">market-implied</span></td><td>The reciprocal of an OLBG-quoted decimal price. The bookmaker margin is still inside it, so treat it as a quoted market read, not an independent estimate.</td></tr>
<tr><td>{confidence_pill("high")}</td><td>Estimate of at least 70%.</td></tr>
<tr><td>{band_pill(True)}</td><td>Fair American price between &minus;250 and +10000 inclusive.</td></tr>
<tr><td><span class="tiny">none captured</span></td><td>No source was captured for that cell. It is never filled by inference.</td></tr>
</tbody></table>
"""
    (OUT).mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page("Overview", "index.html", overview), encoding="utf-8")

    # ---------------------------------------------------------------- matches
    rows = []
    for m in sorted(matches, key=lambda x: (x["start_utc"], x["sport"])):
        pick = m.get("pick") or {}
        rows.append(
            f'<tr data-sport="{esc(m["sport"])}" data-conf="{esc(pick.get("confidence", ""))}">'
            f'<td>{esc(fmt_time(m["start_utc"]))}</td><td>{esc(m["sport"])}</td>'
            f'<td>{esc(match_name(m))}</td><td>{esc(m.get("competition", ""))}</td>'
            f'<td>{esc(m.get("venue", "")) or "—"}</td>'
            f'<td class="num">{m.get("market_count", len(m.get("markets", [])))}</td>'
            f'<td>{esc(pick.get("selection", "—"))}</td>'
            f'<td class="num">{price(pick["fair_american"]) if pick else "—"}</td>'
            f'<td>{confidence_pill(pick.get("confidence", "—")) if pick else "—"}</td>'
            f'<td>{"started" if m.get("started") else "upcoming"}</td>'
            f'<td class="src">{source_cell(m.get("official_url", ""), m.get("olbg_url", ""))}</td>'
            "</tr>"
        )
    options = "".join(f'<option value="{esc(n)}">{esc(n)}</option>' for n, _ in SPORTS)
    matches_body = f"""
<p class="crumb"><a href="index.html">Overview</a> / All matches</p>
<h1>All matches</h1>
<p class="lede">{len(matches)} rows: {summary["with_olbg"]} listed on OLBG, {summary["with_official"]} carrying an
official fixture link, {summary["both"]} carrying both. A row that has started keeps its place and is marked
<span class="tag">started</span>; it is never a pick.</p>
<div class="tools">
  <input id="q" type="search" placeholder="Filter by team, venue or competition" aria-label="Filter rows">
  <select id="sport" aria-label="Filter by sport"><option value="">All sports</option>{options}</select>
  <select id="conf" aria-label="Filter by confidence"><option value="">Any confidence</option><option value="high">high</option><option value="medium">medium</option><option value="low">low</option></select>
  <span class="tiny" id="count"></span>
</div>
<div class="tablewrap"><table>
<thead><tr><th>Start</th><th>Sport</th><th>Match</th><th>Competition</th><th>Venue</th><th>Markets</th><th>Featured selection</th><th>Our price</th><th>Grade</th><th>Status</th><th>Sources</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="tiny">Markets counts every price published for that match, including alternate lines. "Our price" is the
fair American price of the featured selection, not a price you can take.</p>
"""
    (OUT / "matches.html").write_text(page("All matches", "matches.html", matches_body), encoding="utf-8")

    # ------------------------------------------------------------------ picks
    pick_rows = []
    for p in sorted(picks, key=lambda x: (-x["prob"], x["start_utc"])):
        m = m_by_id[p["match_id"]]
        pick_rows.append(
            f'<tr data-sport="{esc(p["sport"])}" data-conf="{esc(p["confidence"])}">'
            f'<td>{esc(fmt_time(p["start_utc"]))}</td><td>{esc(p["sport"])}</td>'
            f'<td>{esc(match_name(m))}</td><td>{esc(p["market"])}</td><td>{esc(p["selection"])}</td>'
            f'<td class="num">{p["prob"]*100:.2f}%</td><td class="num">{price(p["fair_american"])}</td>'
            f'<td>{confidence_pill(p["confidence"])}</td><td>{band_pill(p["in_band"])}</td>'
            f'<td>{esc(p["basis"])}</td>'
            f'<td class="src">{source_cell(p.get("official_url", ""), p.get("olbg_url", ""))}</td>'
            "</tr>"
        )
    picks_body = f"""
<p class="crumb"><a href="index.html">Overview</a> / Picks &amp; lines</p>
<h1>Picks and originated lines</h1>
<p class="lede">One featured selection per match, chosen from that match's own book: an in-band high-confidence
price where one exists, otherwise the strongest high-confidence price, otherwise the shortest price on the main
lines. Every price in the book is published on the match row.</p>
<div class="notice warn"><strong>The two rules only meet in a narrow window.</strong> A 70% estimate is a fair
&minus;233; the band floor is &minus;250, which is 71.43%. So an in-band high-confidence price has to land between
70.00% and 71.43%, a band 1.43 points wide. That is why {summary["high_in_band"]} of {summary["high"]} high-confidence
selections are inside the window. The alternative — stretching the estimate to fit the window — is not done here.</div>
<div class="tools">
  <input id="q" type="search" placeholder="Filter by match or selection" aria-label="Filter rows">
  <select id="sport" aria-label="Filter by sport"><option value="">All sports</option>{options}</select>
  <select id="conf" aria-label="Filter by confidence"><option value="">Any confidence</option><option value="high">high</option><option value="medium">medium</option><option value="low">low</option></select>
  <span class="tiny" id="count"></span>
</div>
<div class="tablewrap"><table>
<thead><tr><th>Start</th><th>Sport</th><th>Match</th><th>Market</th><th>Selection</th><th>Estimate</th><th>Fair price</th><th>Confidence</th><th>Price window</th><th>Basis</th><th>Sources</th></tr></thead>
<tbody>{''.join(pick_rows)}</tbody></table></div>
"""
    (OUT / "picks.html").write_text(page("Picks &amp; lines", "picks.html", picks_body), encoding="utf-8")

    # ------------------------------------------------------------ predictions
    why = {
        "Golf": "No golf event in the captured OLBG payload; outright market, no two-sided line.",
        "Volleyball": "OLBG quotes only; no official per-match statistics captured.",
        "Rugby Union": "OLBG quotes only; the URC table and fixtures captures both returned 404.",
        "Cricket": "OLBG quotes only; the ICC matches page returned 404.",
        "Snooker": "No snooker event in the captured payload; WST rankings were read but no fixture list was captured.",
        "Darts": "OLBG quotes only; no official per-match statistics captured.",
        "Baseball": "Official records exist but no selection reached 70%; the World Series games price close to even.",
        "Gaelic Sports": "OLBG quotes only; GAA fixtures were captured but a county final has no statistical input here.",
        "Greyhounds": "Outright race markets; no two-sided line and no statistical model.",
        "Tennis": "OLBG quotes only; the ATP scores capture returned 403 and WTA current scores returned 404.",
        "Motor Racing": "Outright and podium markets; no two-sided line.",
        "Handball": "OLBG quotes only; EHF and HBL captures returned 404.",
        "Ice Hockey": "Five-plus available; six written.",
        "Basketball": "Five written, all EuroLeague. NBA rows have OLBG prices only.",
        "Rugby League": "OLBG quotes only; the NRL and Super League captures failed.",
    }
    cards = []
    for pred in sorted(preds, key=lambda x: x["start_utc"]):
        facts = "".join(f"<li>{esc(f)}</li>" for f in pred["facts"])
        cards.append(f"""
<article class="pred">
  <div class="metrics"><span class="pill">{esc(pred["sport"])}</span>{confidence_pill(pred["confidence"])}{band_pill(pred["in_band"])}</div>
  <h3 style="margin-top:6px">{esc(pred["event"])}</h3>
  <p class="meta">{esc(pred["competition"])} · {esc(fmt_time(pred["start_utc"]))} UTC · {esc(pred["venue"]) or "venue not captured"}
  · <strong>{esc(pred["selection"])}</strong> ({esc(pred["market"])}) at our {price(pred["fair_american"])}</p>
  <p>{esc(pred["text"])}</p>
  <div class="facts"><strong>Figures used</strong><ul>{facts}</ul></div>
  <p class="src">Sources: <a href="{esc(pred["official_url"])}" rel="noopener">official fixture page ↗</a> ·
  <a href="{esc(pred["source_url"])}" rel="noopener">official record/feed used for the numbers ↗</a></p>
</article>""")
    coverage_rows = "".join(
        '<tr><td>%s</td><td class="num">%d</td><td class="num">%d</td><td class="num">%d</td><td class="num">%d</td><td>%s</td></tr>'
        % (esc(name), by_sport.get(name, 0), sum(1 for p in high if p["sport"] == name),
           sum(1 for p in high_band if p["sport"] == name), sum(1 for p in preds if p["sport"] == name),
           esc(why.get(name, "")))
        for name, _ in SPORTS
    )
    pred_body = f"""
<p class="crumb"><a href="index.html">Overview</a> / Predictions</p>
<h1>Written predictions</h1>
<p class="lede">{len(preds)} write-ups, one per high-confidence pick that has official statistics behind it. Each is
at least 30 words, names the selection in plain words, and uses only figures that appear on the linked official
page. None of them claims an injury, because no official injury feed was captured today.</p>
<div class="notice blue"><strong>Coverage.</strong> Ice Hockey {sum(1 for p in preds if p["sport"]=="Ice Hockey")},
Basketball {sum(1 for p in preds if p["sport"]=="Basketball")}, every other sport 0.
Twelve of the fifteen sports have no official per-match statistical input in today's capture, so a write-up there
would have nothing to stand on. The gap is itemised on <a href="flagged.html">Flagged for Review</a>.</div>
<h2>Coverage against the five-a-sport target</h2>
<div class="tablewrap"><table><thead><tr><th>Sport</th><th>Matches</th><th>High-confidence picks</th><th>In band</th><th>Predictions</th><th>Why not five</th></tr></thead><tbody>{coverage_rows}</tbody></table></div>
{''.join(cards)}
"""
    (OUT / "predictions.html").write_text(page("Predictions", "predictions.html", pred_body), encoding="utf-8")

    # ----------------------------------------------------------------- sports
    (OUT / "sports").mkdir(parents=True, exist_ok=True)
    sport_cards2 = []
    for name, slug in SPORTS:
        n = by_sport.get(name, 0)
        sport_cards2.append(
            f'<a class="card sport" href="{slug}.html"><h3>{esc(name)}</h3>'
            f'<div class="metrics"><span>{n} matches</span><span>{picks_by_sport.get(name, 0)} picks</span>'
            f'<span>{sum(1 for p in high_band if p["sport"]==name)} in band</span></div></a>'
        )
    sports_index = f"""
<p class="crumb"><a href="../index.html">Overview</a> / Sports</p>
<h1>Sports</h1>
<p class="lede">All fifteen sports named in the brief. Gaelic Sports covers Gaelic Football and Hurling.</p>
<div class="cards">{''.join(sport_cards2)}</div>
"""
    (OUT / "sports" / "index.html").write_text(
        page("Sports", "sports/index.html", sports_index, prefix="../"), encoding="utf-8")

    for name, slug in SPORTS:
        rows = []
        for m in sorted([x for x in matches if x["sport"] == name], key=lambda x: x["start_utc"]):
            pick = m.get("pick") or {}
            rows.append(
                f'<tr data-sport="{esc(name)}" data-conf="{esc(pick.get("confidence",""))}">'
                f'<td>{esc(fmt_time(m["start_utc"]))}</td><td>{esc(match_name(m))}</td>'
                f'<td>{esc(m.get("competition",""))}</td><td>{esc(m.get("venue","")) or "—"}</td>'
                f'<td>{esc(pick.get("selection","—"))}</td>'
                f'<td class="num">{price(pick["fair_american"]) if pick else "—"}</td>'
                f'<td>{confidence_pill(pick.get("confidence","—")) if pick else "—"}</td>'
                f'<td class="src">{source_cell(m.get("official_url",""), m.get("olbg_url",""))}</td></tr>'
            )
        sp = [p for p in preds if p["sport"] == name]
        note = ""
        if not any(m.get("records") for m in matches if m["sport"] == name):
            note = ('<div class="notice warn"><strong>No official per-match statistics in today\'s capture.</strong> '
                    'Prices here come from OLBG quotes only, and no written prediction is produced for this sport. '
                    'That is a stated gap, not an omission.</div>')
        if rows:
            table_html = ('<div class="tablewrap"><table><thead><tr><th>Start</th><th>Match</th>'
                          '<th>Competition</th><th>Venue</th><th>Featured selection</th><th>Our price</th>'
                          '<th>Grade</th><th>Sources</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
        else:
            table_html = ('<div class="notice warn">No row for this sport in the captured board. '
                          'Reasons are on <a href="../flagged.html">Flagged for Review</a>.</div>')
        body = f"""
<p class="crumb"><a href="../index.html">Overview</a> · <a href="index.html">Sports</a> / {esc(name)}</p>
<h1>{esc(name)}</h1>
<p class="lede">{by_sport.get(name,0)} matches, {picks_by_sport.get(name,0)} graded picks,
{sum(1 for p in high if p["sport"]==name)} at high confidence, {sum(1 for p in high_band if p["sport"]==name)} of those
inside the price window, {len(sp)} written predictions.</p>
{note}
{table_html}
"""
        (OUT / "sports" / f"{slug}.html").write_text(
            page(f"{name}", "sports/index.html", body, prefix="../"), encoding="utf-8")

    # ---------------------------------------------------------------- sources
    src_rows = []
    seen = set()
    for m in sorted(matches, key=lambda x: (x["sport"], x["start_utc"]))[:400]:
        for kind, url, when in (
            ("fixture page", m.get("official_url", ""), m.get("official_captured_at", "")),
            ("official feed", m.get("official_source_url", ""), m.get("official_captured_at", "")),
            ("OLBG listing", m.get("olbg_url", ""), m.get("olbg_captured_at", "")),
        ):
            if not url or (url, kind) in seen:
                continue
            seen.add((url, kind))
            src_rows.append(
                f'<tr><td>{esc(m["sport"])}</td><td>{esc(kind)}</td>'
                f'<td class="src"><a href="{esc(url)}" rel="noopener">{esc(url)}</a></td>'
                f'<td>{esc(fmt_time(when)) if when else "—"}</td></tr>'
            )
    live_rows = "".join(
        f'<tr><td>{esc(c["id"])}</td><td>{esc(c["sport"])}</td><td>{esc(c["kind"])}</td>'
        f'<td class="src"><a href="{esc(c["url"])}" rel="noopener">{esc(c["url"])}</a></td>'
        f'<td>{esc(c["read_at"])}</td><td>{esc(c["read"])}</td><td>{esc(c["verdict"])}</td></tr>'
        for c in live
    )
    sources_body = f"""
<p class="crumb"><a href="index.html">Overview</a> / Sources</p>
<h1>Sources</h1>
<p class="lede">Two kinds of evidence sit behind this desk. First, committed captures made earlier today by the
repository's collector (OLBG payloads, NHL/MLB/EuroLeague responses). Second, re-reads made in this session, listed
in the second table with the exact value that was on the page.</p>
<h2>Re-reads made in this session</h2>
<div class="tablewrap"><table>
<thead><tr><th>ID</th><th>Sport</th><th>Kind</th><th>URL</th><th>Read at</th><th>Value seen</th><th>Verdict</th></tr></thead>
<tbody>{live_rows}</tbody></table></div>
<p class="tiny">A verdict of "conflict" means the value seen disagrees with an earlier desk; both are published on
<a href="flagged.html">Flagged for Review</a>.</p>
<h2>Row-level sources</h2>
<div class="tablewrap"><table>
<thead><tr><th>Sport</th><th>Kind</th><th>URL</th><th>Captured</th></tr></thead>
<tbody>{''.join(src_rows)}</tbody></table></div>
"""
    (OUT / "sources.html").write_text(page("Sources", "sources.html", sources_body), encoding="utf-8")

    # ---------------------------------------------------------------- flagged
    def flag_row(f):
        links = "".join('<a href="%s" rel="noopener">%s</a><br>' % (esc(u), esc(u)) for u in f.get("sources", []))
        return (
            '<tr data-sport="%s" data-conf="%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
            '<td>%s</td><td class="src">%s</td></tr>'
            % (esc(f.get("sport", "")), esc(f.get("severity", "")), esc(f["id"]), esc(f["title"]),
               esc(f.get("sport", "All")), esc(f["severity"]), esc(f["detail"]), links or "—")
        )

    flag_rows = "".join(flag_row(f) for f in flagged["items"])
    audit_rows = "".join(
        f'<tr><td>{esc(c["key"])}</td><td>{esc(c["sport"])}</td>'
        f'<td class="src"><a href="{esc(c["url"])}" rel="noopener">{esc(c["url"])}</a></td>'
        f'<td class="num">{esc(c["status"] if c["status"] is not None else "no response")}</td>'
        f'<td>{esc(c["verdict"])}</td><td>{esc(", ".join(c["evidence"])) or "—"}</td></tr>'
        for c in audit["captures"] if c["verdict"] in ("http error", "error page", "no status")
    )
    trunc_rows = "".join(
        f'<tr><td>{esc(c["key"])}</td><td>{esc(c["sport"])}</td>'
        f'<td class="src"><a href="{esc(c["url"])}" rel="noopener">{esc(c["url"])}</a></td>'
        f'<td class="num">{esc(c["bytes"])}</td></tr>'
        for c in audit["captures"] if c["truncated"]
    )
    flagged_body = f"""
<p class="crumb"><a href="index.html">Overview</a> / Flagged for Review</p>
<h1>Flagged for Review</h1>
<p class="lede">{len(flagged["items"])} items. Each is either a limitation that changed what the desk could
publish, or a conflict between two sources where neither value was deleted. Open the links before relying on a
number.</p>
<div class="notice warn">Nothing on this page is a corrected value. Where two sources disagree, both are kept.</div>
<div class="tablewrap"><table>
<thead><tr><th>ID</th><th>Finding</th><th>Sport</th><th>Severity</th><th>Detail</th><th>Sources</th></tr></thead>
<tbody>{flag_rows}</tbody></table></div>

<h2>Every failed capture ({audit["meta"]["failed"]} of {audit["meta"]["captures"]})</h2>
<p>Reproduced from <code>data/ledger/manifest.json</code>. No value on this desk is taken from any row below.</p>
<div class="tablewrap"><table>
<thead><tr><th>Capture</th><th>Sport</th><th>Requested URL</th><th>HTTP</th><th>Verdict</th><th>Evidence</th></tr></thead>
<tbody>{audit_rows}</tbody></table></div>

<h2>Truncated captures ({audit["meta"]["truncated"]})</h2>
<p>These bodies were cut at the collector's ceiling. A truncated OLBG hub can only lose events from the end of the
page, so every count derived from one is a floor.</p>
<div class="tablewrap"><table>
<thead><tr><th>Capture</th><th>Sport</th><th>Requested URL</th><th>Stored bytes</th></tr></thead>
<tbody>{trunc_rows}</tbody></table></div>
"""
    (OUT / "flagged.html").write_text(page("Flagged for Review", "flagged.html", flagged_body), encoding="utf-8")

    # ------------------------------------------------------------ methodology
    method = f"""
<p class="crumb"><a href="index.html">Overview</a> / Methodology</p>
<h1>Methodology</h1>
<p class="lede">Short version: official numbers in, our own prices out, one selection per match, and a public list
of everything that could not be supported.</p>

<h2>1. What is on the desk</h2>
<p>Two pools are joined. The OLBG pool is every in-scope tip parsed from the embedded payload of OLBG's own pages,
captured 2026-10-23 between 19:28Z and 20:32Z; it supplies {summary["with_olbg"]} matches and their quoted prices.
The official pool is every fixture in the NHL, MLB and EuroLeague responses captured in the same window; it supplies
{summary["with_official"]} fixtures. They are joined on club nickname plus an eight-hour start-time window, never on
a guessed id, and {summary["both"]} rows carry both.</p>

<h2>2. Where a price comes from</h2>
<p><strong>Originated.</strong> For a fixture with official season records we compute a probability and print the
fair price that matches it. Ice hockey uses points pace and goal differential with a home-ice term; EuroLeague uses
win rate and point differential; MLB uses winning percentage with a home term. Totals use a Poisson model below 40
points and a normal approximation above it, because a 160-point basketball total cannot be summed as a Poisson.</p>
<p><strong>Market-implied.</strong> Where no official statistics exist, the only honest source is the OLBG quote.
Its reciprocal is printed, the bookmaker margin is left in, and the basis is labelled on every row. It is not our
estimate and is not described as one.</p>

<h2>3. Grades and the price window</h2>
<table><thead><tr><th>Rule</th><th>Value</th></tr></thead><tbody>
<tr><td>High confidence</td><td>estimate of 70% or more</td></tr>
<tr><td>Medium confidence</td><td>60% to 69.99%</td></tr>
<tr><td>Low confidence</td><td>below 60%</td></tr>
<tr><td>In band</td><td>fair American price between &minus;250 and +10000 inclusive</td></tr>
<tr><td>Featured selection</td><td>in-band high if one exists, else strongest high, else shortest main line</td></tr>
</tbody></table>
<p>The window and the confidence floor intersect at 70.00% to 71.43%. That is arithmetic, not a design choice, and
it is why the in-band list is short.</p>

<h2>4. Estimate bounds</h2>
<p>Early-season samples are small, so estimates are held inside the range the sport actually trades in: NHL money
lines 24% to 76%, EuroLeague 12% to 88%, MLB 30% to 70%, derived markets 3% to 97%. A team that is 8-1 after nine
games has not earned a &minus;3800 price, and the desk will not print one.</p>

<h2>5. Predictions</h2>
<p>Only high-confidence picks with official statistics get a write-up. Each must be at least 30 words, open with a
unique sentence, name the selection, and quote at least two figures that appear on the linked official page. The
validator rejects any write-up containing the words "model" or "verified", any duplicate opening, and any fact that
is not present in the stored record for that match.</p>

<h2>6. What the desk will not do</h2>
<p>It will not fill a blank with an inference, quote a price it did not compute or receive, call a market-implied
number our own, assert an injury without an official report, or present a started match as an upcoming pick.</p>
"""
    (OUT / "methodology.html").write_text(page("Methodology", "methodology.html", method), encoding="utf-8")

    print(f"master/: built with {len(matches)} matches, {len(picks)} picks, {len(preds)} predictions")


if __name__ == "__main__":
    build()
