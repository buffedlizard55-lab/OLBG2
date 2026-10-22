#!/usr/bin/env python3
"""Build the consolidated 17-sport dashboard under /final/.

Deterministic: reads data/final/{matches,predictions,summary}.json plus
data/hub/sports.json, and writes static HTML, CSS and JS. Re-running produces
byte-identical output.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "final"
OUT = ROOT / "final"
NOW = "2026-10-22T08:22:00Z"
SNAPSHOT = "2026-10-22 08:22 UTC"
TOTAL_ROWS = 0  # set in main(); used by the shared page template

SPORT_ORDER = [
    "ice-hockey", "basketball", "rugby-union", "darts", "tennis", "handball",
    "volleyball", "baseball", "motor-racing", "snooker", "cricket", "golf",
    "rugby-league", "gaelic-football", "greyhounds", "aussie-rules", "esports",
]
SLUG_NAME = {
    "ice-hockey": "Ice Hockey", "basketball": "Basketball", "rugby-union": "Rugby Union",
    "darts": "Darts", "tennis": "Tennis", "handball": "Handball", "volleyball": "Volleyball",
    "baseball": "Baseball", "motor-racing": "Motor Racing", "snooker": "Snooker",
    "cricket": "Cricket", "golf": "Golf", "rugby-league": "Rugby League",
    "gaelic-football": "Gaelic Football", "greyhounds": "Greyhounds",
    "aussie-rules": "Aussie Rules", "esports": "eSports",
}
CONF_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3}
LAYER_FILES = [
    ("hub", "matches.json", "rows"),
    ("slate", "matches.json", "matches"),
    ("board", "matches.json", "matches"),
    ("verified", "matches.json", "matches"),
    ("forward", "matches.json", "matches"),
]


# --------------------------------------------------------------------------- io
def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def domain(url: str) -> str:
    return urlsplit(url or "").netloc.replace("www.", "")


def layer_stats():
    """Read each source layer so the archive page can never drift from the files."""
    out = []
    for name, filename, key in LAYER_FILES:
        payload = read(ROOT / "data" / name / filename)
        rows = payload[key]
        lined = 0
        for r in rows:
            m = r.get("markets")
            if isinstance(m, dict):
                lined += 1 if any((v or {}).get("outcomes") for v in m.values() if isinstance(v, dict)) else 0
            elif isinstance(m, list):
                lined += 1 if m else 0
            else:
                lined += 1 if r.get("winner_market") else 0
        sports = {r.get("sport") for r in rows}
        out.append({"name": name, "rows": len(rows), "lined": lined, "sports": len(sports)})
    return out


def pct(value) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def dec(value) -> str:
    return "—" if value is None else f"{value:.2f}"


def am(value) -> str:
    if value is None:
        return "—"
    return f"+{value}" if value > 0 else str(value)


def status_of(row):
    start = row.get("start_utc") or ""
    if start < NOW:
        return "started"
    if start[:10] == "2026-10-22":
        return "today"
    if start[:10] == "2026-10-23":
        return "tomorrow"
    return "upcoming"


def conf_of(row):
    pick = row.get("pick") or {}
    return pick.get("confidence") or "none"


# --------------------------------------------------------------------------- css/js
CSS = r"""
:root{--bg:#f5f7fb;--panel:#ffffff;--ink:#0f172a;--muted:#5b667a;--line:#e2e8f0;--accent:#0d9488;--accent2:#115e59;--high:#b91c1c;--med:#b45309;--low:#475569;--ok:#047857;--warn:#b45309;--blue:#1d4ed8}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent2);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1220px;margin:0 auto;padding:0 18px}
.topbar{position:sticky;top:0;z-index:20;background:rgba(15,23,42,.97);color:#e2e8f0;backdrop-filter:blur(6px)}
.bar{display:flex;align-items:center;gap:18px;min-height:56px;flex-wrap:wrap}
.brand{color:#fff;font-weight:700;display:flex;align-items:center;gap:8px;letter-spacing:.2px}
.brand:hover{text-decoration:none}
.dot{width:9px;height:9px;border-radius:50%;background:#2dd4bf;display:inline-block}
.brand-sub{font-weight:400;color:#94a3b8;font-size:12px}
.nav{display:flex;gap:14px;flex-wrap:wrap;font-size:13.5px}
.nav a{color:#cbd5e1;padding:4px 0;border-bottom:2px solid transparent}
.nav a[aria-current=page]{color:#fff;border-bottom-color:#2dd4bf}
.nav a:hover{color:#fff;text-decoration:none}
.stripe{background:#0f172a;color:#cbd5e1;font-size:12.5px;padding:7px 0;border-top:1px solid #1e293b}
.stripe strong{color:#fff}
main{padding:26px 0 50px}
.hero{padding:10px 0 6px}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:11.5px;color:var(--accent2);font-weight:700;margin:0 0 8px}
h1{font-size:36px;line-height:1.12;margin:0 0 12px;letter-spacing:-.02em}
h2{font-size:23px;margin:34px 0 10px;letter-spacing:-.01em}
h3{font-size:16px;margin:0 0 8px}
.lede{font-size:17px;color:#334155;max-width:900px}
.sub{color:var(--muted);max-width:900px;margin-top:4px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin:22px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 15px}
.kpi .v{font-size:27px;font-weight:750;letter-spacing:-.02em}
.kpi .k{font-size:12.5px;color:var(--muted);margin-top:2px}
.kpi .s{font-size:11.5px;color:#94a3b8;margin-top:1px}
.grid{display:grid;gap:12px}
.grid.sports{grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px;color:inherit}
.card:hover{border-color:#99f6e4;text-decoration:none;box-shadow:0 6px 20px rgba(15,23,42,.06)}
.cardhead{display:flex;align-items:center;justify-content:space-between;gap:10px}
.card h3{margin:0;font-size:16px}
.card p{color:var(--muted);font-size:13px;margin:8px 0 10px}
.metrics{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.metrics b{color:var(--ink)}
.pill{font-size:11.5px;background:#e6fffb;color:#0f766e;border:1px solid #99f6e4;padding:2px 8px;border-radius:999px;white-space:nowrap}
.button{display:inline-block;background:#fff;border:1px solid var(--line);padding:8px 14px;border-radius:9px;font-weight:600;font-size:13.5px;color:var(--ink)}
.button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.button:hover{text-decoration:none;border-color:#94a3b8}
.cta{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0 4px}
.notice{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:12px 14px;color:#78350f;margin:16px 0;font-size:13.5px}
.notice.blue{background:#eff6ff;border-color:#bfdbfe;color:#1e3a8a}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px}
.two-col{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
ul.clean{margin:6px 0 0;padding-left:18px}
ul.clean li{margin:5px 0}
.tablewrap{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:auto;max-height:78vh}
table{width:100%;border-collapse:collapse;font-size:13px}
thead th{position:sticky;top:0;background:#f8fafc;text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:#64748b;z-index:2}
tbody td{padding:9px 10px;border-bottom:1px solid #f1f5f9;vertical-align:top}
tbody tr:hover{background:#f8fafc}
tbody tr.past{opacity:.62}
.teams{font-weight:600}
.teams span{color:#94a3b8;font-weight:400;margin:0 4px}
.tiny{font-size:11.5px;color:#64748b;margin-top:2px}
.nowrap{white-space:nowrap}
.blank{color:#94a3b8}
.badge{display:inline-block;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;padding:2px 6px;border-radius:5px;border:1px solid transparent}
.badge.high{background:#fee2e2;color:#991b1b;border-color:#fecaca}
.badge.medium{background:#fef3c7;color:#92400e;border-color:#fde68a}
.badge.low{background:#e2e8f0;color:#334155;border-color:#cbd5e1}
.badge.none{background:#f1f5f9;color:#64748b;border-color:#e2e8f0}
.badge.ok{background:#d1fae5;color:#065f46;border-color:#a7f3d0}
.badge.warn{background:#ffedd5;color:#9a3412;border-color:#fed7aa}
.badge.info{background:#dbeafe;color:#1e40af;border-color:#bfdbfe}
.pick{font-weight:650}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0;align-items:center}
.filters select,.filters input{font:13px inherit;padding:7px 9px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink)}
.filters input{min-width:210px}
.count{font-size:12.5px;color:var(--muted);margin-left:auto}
.pickcard{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}
.pickcard .top{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:flex-start}
.pickcard h3{margin:0 0 3px;font-size:18px}
.pickcard .sel{font-size:15px;font-weight:700;color:#0f766e}
.pickcard p.text{margin:12px 0;color:#1e293b}
.facts{margin:10px 0 0;padding-left:18px;font-size:12.5px;color:#475569}
.facts li{margin:4px 0}
.flag{background:var(--panel);border:1px solid var(--line);border-left:4px solid #f59e0b;border-radius:10px;padding:14px 16px;margin:10px 0}
.flag.high{border-left-color:#dc2626}
.flag.medium{border-left-color:#f59e0b}
.flag.low{border-left-color:#64748b}
.flag h3{margin:0 0 4px;font-size:15px}
.flag .meta{font-size:11.5px;color:#64748b;margin-bottom:6px}
code{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:12px}
footer{border-top:1px solid var(--line);padding:22px 0 40px;color:var(--muted);font-size:12.5px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
@media (max-width:640px){h1{font-size:28px}.nav{font-size:12.5px;gap:10px}.tablewrap{max-height:none}}
"""

JS = r"""
(function(){
  const table=document.getElementById('matches');
  if(!table) return;
  const rows=[...table.tBodies[0].rows];
  const sport=document.getElementById('f-sport');
  const conf=document.getElementById('f-conf');
  const status=document.getElementById('f-status');
  const text=document.getElementById('f-text');
  const count=document.getElementById('f-count');
  function apply(){
    const s=sport.value,c=conf.value,st=status.value,q=text.value.toLowerCase().trim();
    let n=0;
    rows.forEach(r=>{
      const ok=(!s||r.dataset.sport===s)&&(!c||r.dataset.conf===c)&&(!st||r.dataset.status===st)&&(!q||r.dataset.search.includes(q));
      r.style.display=ok?'':'none'; if(ok)n++;
    });
    if(count) count.textContent=n+' of '+rows.length+' rows';
  }
  [sport,conf,status].forEach(el=>el&&el.addEventListener('change',apply));
  text&&text.addEventListener('input',apply);
  apply();
})();
"""


# --------------------------------------------------------------------------- components
NAV = [
    ("index.html", "Dashboard"),
    ("matches.html", "All matches"),
    ("sports/index.html", "Sports"),
    ("picks.html", "High-confidence picks"),
    ("verification.html", "Verification"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "Methodology"),
    ("sources.html", "Sources"),
    ("archive.html", "Source layers"),
]


def page(title: str, active: str, body: str, prefix: str = "") -> str:
    nav = "".join(
        f'<a href="{prefix}{href}"{" aria-current=page" if href == active else ""}>{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG2 consolidated desk</title>
<meta name="description" content="Consolidated OLBG reverse-engineering desk: {TOTAL_ROWS} de-duplicated fixtures across 17 eligible sports, originated lines, strict confidence grades and sourced predictions.">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="topbar"><div class="wrap bar">
<a class="brand" href="{prefix}index.html"><span class="dot"></span>OLBG2 <span class="brand-sub">consolidated desk</span></a>
<nav class="nav" aria-label="Main navigation">{nav}</nav>
</div></header>
<div class="stripe"><div class="wrap"><strong>Snapshot {SNAPSHOT}</strong> · {TOTAL_ROWS} de-duplicated fixtures · 17 eligible sports · every row carries its official source link · <a href="{prefix}flagged.html">open review items</a></div></div>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
Research, not betting advice. 18+. Prices are our own fair (no-vig) model prices, never bookmaker quotes.
Every inherited value keeps the official URL of the layer that captured it; rows not re-read in this pass are labelled.
<a href="{prefix}methodology.html">Methodology</a> · <a href="{prefix}verification.html">Verification ledger</a> · <a href="{prefix}flagged.html">Flagged for review</a>
</div></footer>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def conf_badge(conf):
    return f'<span class="badge {conf}">{conf}</span>'


def verification_badge(row):
    v = row.get("verification") or {}
    status = v.get("status")
    if status == "reverified":
        return '<span class="badge ok">re-read 22 Oct</span>'
    if status == "form":
        return '<span class="badge info">form re-read</span>'
    if status == "corrected":
        return '<span class="badge ok">corrected 22 Oct</span>'
    if status == "unverified":
        return '<span class="badge high">unverified</span>'
    return '<span class="badge warn">inherited</span>'


def markets_cell(row):
    if row["line_status"] != "originated":
        return f'<span class="blank">—</span><div class="tiny">{esc(row.get("blank_reason") or "no official pre-match input")}</div>'
    bits = []
    for market in row.get("markets") or []:
        name = market["market"]
        outs = market.get("outcomes") or []
        if not outs:
            continue
        if name == "Moneyline":
            bits.append(f'<div><b>ML</b> {pct(outs[0]["probability"])} / {pct(outs[1]["probability"])}</div>')
        elif name == "1X2" and len(outs) == 3:
            bits.append(f'<div><b>1X2</b> {pct(outs[0]["probability"])} / {pct(outs[1]["probability"])} / {pct(outs[2]["probability"])}</div>')
        elif name == "Handicap":
            line = market.get("line")
            label = f"HCP {line:g}" if isinstance(line, (int, float)) else "HCP"
            bits.append(f'<div><b>{label}</b> {pct(outs[0]["probability"])} / {pct(outs[1]["probability"])}</div>')
        elif name == "Total":
            line = market.get("line")
            bits.append(f'<div><b>Total {line:g}</b> O {pct(outs[0]["probability"])} / U {pct(outs[1]["probability"])}</div>' if isinstance(line, (int, float)) else f'<div><b>Total</b> O {pct(outs[0]["probability"])} / U {pct(outs[1]["probability"])}</div>')
        else:
            bits.append(f'<div><b>{esc(name)}</b> {pct(outs[0]["probability"])}</div>')
    return "".join(bits) or '<span class="blank">—</span>'


def pick_cell(row):
    pick = row.get("pick")
    if not pick:
        return '<span class="blank">—</span>'
    return (
        f'<div class="pick">{esc(pick["selection"])}</div>'
        f'<div class="tiny">{pct(pick["probability"])} · {dec(pick["fair_decimal"])} · {am(pick["fair_american"])} · '
        f'{conf_badge(pick["confidence"])}</div>'
    )


def source_cell(row):
    url = row.get("official_url") or ""
    if not url:
        return '<span class="blank">—</span>'
    scope = row.get("source_scope") or "competition"
    return f'<a href="{esc(url)}" rel="noopener">{esc(domain(url))}</a><div class="tiny">{esc(scope)} page</div>'


def row_html(row, show_sport=True):
    status = status_of(row)
    conf = conf_of(row)
    search = " ".join(str(row.get(k) or "") for k in ("home", "away", "competition", "venue", "id")).lower()
    cells = [
        f'<td class="nowrap">{esc(row["date"])}<div class="tiny">{esc(status)}</div></td>',
    ]
    if show_sport:
        cells.append(f'<td><a href="sports/{esc(row["sport"])}.html">{esc(row["sport_name"])}</a></td>')
    cells += [
        f'<td>{esc(row["competition"])}<div class="tiny">{esc(row["id"])}</div></td>',
        f'<td><div class="teams">{esc(row["home"])} <span>v</span> {esc(row["away"])}</div><div class="tiny">{esc(row["venue"] or "venue not published")}</div></td>',
        f'<td>{markets_cell(row)}</td>',
        f'<td>{pick_cell(row)}</td>',
        f'<td>{source_cell(row)}<div class="tiny">{verification_badge(row)}</div></td>',
    ]
    cls = "past" if status == "started" else ("row-today" if status == "today" else "")
    return (f'<tr class="{cls}" data-sport="{esc(row["sport"])}" data-conf="{conf}" '
            f'data-status="{status}" data-search="{esc(search)}">' + "".join(cells) + "</tr>")


def table(rows, *, show_sport=True, table_id="matches"):
    head = ["Date", "Sport", "Competition", "Match", "Markets (model)", "Pick", "Official source"] if show_sport else \
           ["Date", "Competition", "Match", "Markets (model)", "Pick", "Official source"]
    return (f'<div class="tablewrap"><table id="{table_id}"><thead><tr>'
            + "".join(f"<th>{h}</th>" for h in head)
            + "</tr></thead><tbody>" + "".join(row_html(r, show_sport) for r in rows) + "</tbody></table></div>")


def filter_bar(sports):
    opts = "".join(f'<option value="{esc(slug)}">{esc(name)}</option>' for slug, name in sports)
    return f"""<div class="filters">
<label class="sr" for="f-sport">Sport</label><select id="f-sport"><option value="">All sports</option>{opts}</select>
<label class="sr" for="f-conf">Confidence</label><select id="f-conf"><option value="">All confidence</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option><option value="none">Unlined</option></select>
<label class="sr" for="f-status">Status</label><select id="f-status"><option value="">All dates</option><option value="today">Today</option><option value="tomorrow">Tomorrow</option><option value="upcoming">Later</option><option value="started">Started / past</option></select>
<label class="sr" for="f-text">Search</label><input id="f-text" type="search" placeholder="Search team, competition, venue…">
<span class="count" id="f-count"></span></div>"""


# --------------------------------------------------------------------------- data helpers
def sport_meta():
    hub = read(ROOT / "data" / "hub" / "sports.json")
    eligible = {s["slug"]: s for s in hub["eligible"]}
    return eligible, hub["excluded"]


def sport_stats(rows):
    stats = defaultdict(lambda: {"rows": 0, "originated": 0, "unlined": 0, "high": 0, "medium": 0, "low": 0,
                                  "comps": set(), "first": None, "last": None})
    for r in rows:
        s = stats[r["sport"]]
        s["rows"] += 1
        if r["line_status"] == "originated":
            s["originated"] += 1
        else:
            s["unlined"] += 1
        s[conf_of(r)] = s.get(conf_of(r), 0) + 1
        s["comps"].add(r["competition"])
        d = r["date"]
        s["first"] = d if not s["first"] or d < s["first"] else s["first"]
        s["last"] = d if not s["last"] or d > s["last"] else s["last"]
    return stats


def render_flags(rows, preds):
    items = read(DATA / "flagged.json")["items"]
    body = [
        '<section class="hero"><p class="eyebrow">Transparency</p><h1>Flagged for review</h1>',
        f'<p class="lede">{len(items)} items: every correction made in this pass, every inherited value that was not '
        're-read, every blank fixture, and every cross-layer irregularity found while consolidating the five source layers. '
        'Nothing here blocks publication; each item carries the source link needed to re-check it.</p></section>',
    ]
    sev = Counter(i.get("severity") for i in items)
    body.append('<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="v">{sev.get(k,0)}</div><div class="k">{k.title()}</div></div>'
        for k in ("high", "medium", "low")) + "</div>")
    for item in items:
        body.append(
            f'<article class="flag {esc(item["severity"])}">'
            f'<div class="meta">{esc(item["id"])} · {esc(item["category"])} · {esc(item.get("sport") or "cross-sport")}</div>'
            f'<h3>{esc(item["item"])}</h3><p>{esc(item["detail"])}</p>'
            + (f'<p class="tiny"><a href="{esc(item["source_url"])}" rel="noopener">{esc(item.get("source_name") or item["source_url"])}</a></p>' if item.get("source_url") else "")
            + "</article>"
        )
    return page("Flagged for review", "flagged.html", "".join(body))


def render_picks(preds):
    body = ['<section class="hero"><p class="eyebrow">High-confidence selections</p>',
            f'<h1>{len(preds)} sourced predictions</h1>',
            '<p class="lede">Every selection below has a model probability of at least 70% <em>and</em> a fair decimal '
            'price between 1.40 and 101.00, the only overlap of the brief\'s &minus;250…+10000 band with the 70% rule. '
            'Each write-up is at least 30 words, names both sides, gives the captured form and recent history, names a '
            'player, and states the selection in plain words. Facts carry the official URL that supports them; '
            '<span class="badge ok">re-read</span> marks facts checked again on 2026-10-22.</p></section>']
    body.append('<div class="notice blue"><strong>Form is a dated capture.</strong> Records and player totals are the '
                'official figures published on 2026-10-22, not the state on the day of each game. Player-level facts marked '
                'inherited were captured by the source layer and are listed on the verification page as not re-read in this pass.</div>')
    for p in preds:
        fact_lines = []
        for f in p["facts"]:
            badge = ('<span class="badge ok">re-read</span>' if f.get("verified")
                     else '<span class="badge warn">inherited</span>')
            fact_lines.append(
                f'<li>{esc(f["claim"])} — <a href="{esc(f["source"])}" rel="noopener">{esc(domain(f["source"]))}</a> {badge}</li>'
            )
        facts = "".join(fact_lines)
        body.append(f"""<article class="pickcard" id="{esc(p['match_id'])}">
<div class="top"><div><h3>{esc(p['home'])} v {esc(p['away'])}</h3>
<div class="tiny">{esc(p['sport_name'])} · {esc(p['competition'])} · {esc(p['date'])} · {esc(p['venue'] or 'venue not published')}</div></div>
<div>{conf_badge('high')} <span class="sel">{esc(p['selection'])}</span>
<div class="tiny">{pct(p['probability'])} · {dec(p['fair_decimal'])} · {am(p['fair_american'])} · {p['word_count']} words</div></div></div>
<p class="text">{esc(p['text'])}</p>
<ul class="facts">{facts}</ul>
<p class="tiny">Fixture source: <a href="{esc(p['official_url'])}" rel="noopener">{esc(domain(p['official_url']))}</a> · provenance: {esc(p['provenance'])} layer</p>
</article>""")
    return page("High-confidence picks", "picks.html", "".join(body))


def render_index(rows, preds, stats):
    counts = Counter(conf_of(r) for r in rows)
    sports = [s for s in SPORT_ORDER if s in stats]
    meta, excluded = sport_meta()
    body = [
        '<section class="hero"><p class="eyebrow">OLBG reverse-engineering · consolidated desk</p>',
        '<h1>17 sports. One de-duplicated table. Every row sourced.</h1>',
        f'<p class="lede">This desk merges the five earlier layers into <strong>{len(rows)} unique fixtures</strong> '
        f'across all <strong>17 eligible OLBG sports</strong>, excluding soccer/football, boxing, UFC/MMA, American football, '
        'hurling, horse racing, cycling and specials. Fixtures, records and player facts are linked to the governing body '
        'that publishes them; prices are our own fair model prices, never bookmaker quotes. '
        f'<strong>{counts["high"]} selections</strong> clear both the 70% probability rule and the &minus;250…+10000 band and '
        'each has a sourced write-up.</p>',
        f'<div class="cta"><a class="button primary" href="matches.html">Browse all {len(rows)} rows</a>'
        f'<a class="button" href="picks.html">{counts["high"]} high-confidence picks</a>'
        '<a class="button" href="flagged.html">Flagged for review</a></div></section>',
        '<div class="kpis">',
        f'<div class="kpi"><div class="v">{len(rows)}</div><div class="k">unique fixtures</div><div class="s">17 sports · {len({r["competition"] for r in rows})} competitions</div></div>',
        f'<div class="kpi"><div class="v">{sum(1 for r in rows if r["line_status"]=="originated")}</div><div class="k">originated lines</div><div class="s">moneyline, handicap, total</div></div>',
        f'<div class="kpi"><div class="v">{counts["high"]}</div><div class="k">high-confidence</div><div class="s">≥70% and 1.40–101.00</div></div>',
        f'<div class="kpi"><div class="v">{len(preds)}</div><div class="k">written predictions</div><div class="s">68–94 words, unique</div></div>',
        f'<div class="kpi"><div class="v">{sum(1 for r in rows if r["line_status"]=="unlined")}</div><div class="k">honestly unlined</div><div class="s">blank with a stated reason</div></div>',
        f'<div class="kpi"><div class="v">{sum(1 for r in rows if (r.get("verification") or {}).get("status") in ("reverified","corrected"))}</div><div class="k">rows re-read today</div><div class="s">NHL, SHL and PGA Tour</div></div>',
        '</div>',
        '<div class="notice"><strong>Read the date column.</strong> The snapshot is 2026-10-22 08:22 UTC. '
        f'{sum(1 for r in rows if status_of(r)=="started")} fixtures had already started and stay visible for audit; they are never presented as live tips. '
        'Form figures are the official capture of that morning, not game-day state.</div>',
        '<h2>Sports covered</h2>',
        '<p class="sub">All 17 eligible sports are shown. A sport with zero high-confidence picks still carries its full '
        'fixture table, originated prices where the official inputs allowed, and a written reason wherever a market is blank. '
        '<a href="sports/index.html">Open the category index</a>.</p>',
        '<div class="grid sports">',
    ]
    for slug in sports:
        s = stats[slug]
        info = meta.get(slug, {})
        body.append(
            f'<a class="card" href="sports/{slug}.html"><div class="cardhead"><h3>{esc(SLUG_NAME[slug])}</h3>'
            f'<span class="pill">{s["rows"]} rows</span></div>'
            f'<p>{esc(info.get("official_source") or "Governing-body source")} · {len(s["comps"])} competitions · '
            f'{esc(s["first"])} to {esc(s["last"])}</p>'
            f'<div class="metrics"><span><b>{s["originated"]}</b> lined</span><span><b>{s["high"]}</b> high</span>'
            f'<span><b>{s["unlined"]}</b> blank</span></div></a>')
    body += ['</div>', '<h2>Top high-confidence picks</h2>',
             '<p class="sub">All are inside the brief\'s focus band. The full write-up and its source links open on the picks page.</p>',
             '<div class="grid sports">']
    for p in preds[:6]:
        body.append(
            f'<a class="card" href="picks.html#{esc(p["match_id"])}"><div class="cardhead"><h3>{esc(p["home"])} v {esc(p["away"])}</h3>'
            f'<span class="pill">{esc(p["sport_name"])}</span></div><p class="sel">{esc(p["selection"])}</p>'
            f'<div class="metrics"><span><b>{pct(p["probability"])}</b> model</span><span><b>{dec(p["fair_decimal"])}</b> fair price</span>'
            f'<span><b>{p["word_count"]}</b> words</span></div></a>')
    body += ['</div>', '<h2>Analysis of this snapshot</h2>', '<div class="two-col">',
             '<div class="panel"><h3>Coverage and evidence</h3><ul class="clean">',
             f'<li><strong>{sum(1 for r in rows if r["line_status"]=="originated")} of {len(rows)} rows ({sum(1 for r in rows if r["line_status"]=="originated")/len(rows)*100:.0f}%)</strong> carry originated prices; the other {sum(1 for r in rows if r["line_status"]=="unlined")} are blank with a published reason.</li>',
             f'<li><strong>{sum(1 for r in rows if r["source_scope"]=="fixture")} rows</strong> cite a URL that identifies the individual fixture; '
             f'{sum(1 for r in rows if r["source_scope"]!="fixture")} cite a competition, rankings or player page. Both are disclosed on every row.</li>',
             f'<li>The five source layers held <strong>{sum(s["rows"] for s in layer_stats())} rows</strong>; de-duplication produced <strong>{len(rows)} fixtures</strong>. '
             'No layer is summed into another.</li>',
             f'<li><strong>0 excluded-sport rows</strong> survived the filter. Aussie Rules keeps nine real fixtures from the slate layer; '
             'the eight eSports pairings were only captured on a community wiki, so they are published unlined and unverified.</li>',
             '</ul></div>',
             '<div class="panel"><h3>Prices and confidence</h3><ul class="clean">',
             f'<li>Confidence split: <strong>{counts["high"]} high</strong>, {counts["medium"]} medium, {counts["low"]} low, {counts["none"]} unlined.</li>',
             '<li>High means <strong>≥70% model probability and a fair price of 1.40–101.00</strong>. Because a 70% shot prices at 1.43, '
             'the only overlap is roughly 70.0–71.4%; that is why the high set is small and why 100+ stronger favourites are graded medium '
             'with the explicit reason "shorter than &minus;250".</li>',
             f'<li>The longest high-confidence price is <strong>{max(p["fair_decimal"] for p in preds):.2f}</strong>; the shortest is '
             f'<strong>{min(p["fair_decimal"] for p in preds):.2f}</strong>.</li>',
             '<li>No bookmaker price enters any equation. Where a source layer published synthetic "book" columns, they were dropped.</li>',
             '</ul></div></div>',
             '<h2>What changed in this pass</h2>', '<div class="two-col">',
             '<div class="panel"><h3>Corrections</h3><ul class="clean">',
             '<li><strong>Golf:</strong> the inherited "Bank of Utah Championship" row was replaced by the official 22–25 October '
             'Butterfield Bermuda Championship at Port Royal.</li>',
             '<li><strong>Tennis:</strong> the Fils write-up quoted #22 / 2,050 points; the official capture has #10 / 3,325. The text was corrected.</li>',
             '<li><strong>NHL:</strong> the Boston write-up quoted Pastrnak at 4 goals / 8 assists; the official game page shows 6 points. '
             'The Josi line was corrected from 8 assists to 6.</li>',
             '<li><strong>Darts:</strong> the earlier "Bunting withdrew" claim was <em>not</em> applied — no official page confirms it and multiple '
             'dated sources list Noppert v Bunting. The row stands, and the claim is on the flagged page.</li>',
             '</ul></div>',
             '<div class="panel"><h3>Limits</h3><ul class="clean">',
             '<li>Only <strong>7 rows</strong> were re-read against their official page today (NHL fixtures on 22 October, the SHL table, the PGA Tour tournament page). '
             'The rest carry the capture stamp of the layer that collected them and are marked inherited.</li>',
             '<li>Player facts inside inherited write-ups were checked where the official leaders feed covered the player; the rest are marked '
             'inherited with their source URL.</li>',
             '<li>The PDC schedule page could not be read past its consent wall, so the darts draw is inherited rather than re-verified.</li>',
             '</ul></div></div>',
             f'<h2>Excluded by the brief ({len(excluded)})</h2>',
             '<p class="sub">These OLBG categories are intentionally absent; the filter is enforced in code and tested.</p>',
             '<div class="panel"><p>' + " · ".join(esc(s["name"]) for s in excluded) + '</p></div>']
    return page("Dashboard", "index.html", "".join(body))


def render_matches(rows):
    sports = [(s, SLUG_NAME[s]) for s in SPORT_ORDER if any(r["sport"] == s for r in rows)]
    body = ['<section class="hero"><p class="eyebrow">Complete list</p>',
            f'<h1>All {len(rows)} fixtures</h1>',
            '<p class="lede">One row per unique fixture after merging the five layers. Filter by sport, confidence, date or free text. '
            'Markets show our model probabilities; the pick is the selection used on the picks page; the source column always links to the official page.</p></section>',
            filter_bar(sports), table(rows)]
    return page("All matches", "matches.html", "".join(body))


def render_sports_index(rows, stats):
    meta, _ = sport_meta()
    body = ['<section class="hero"><p class="eyebrow">Categories</p><h1>17 eligible sports</h1>',
            '<p class="lede">Each page carries every fixture in that sport, its originated markets, confidence grades and the official sources. '
            'A blank market is a deliberate, disclosed omission, not a missing value.</p></section>',
            '<div class="grid sports">']
    for slug in SPORT_ORDER:
        if slug not in stats:
            continue
        s = stats[slug]
        info = meta.get(slug, {})
        body.append(
            f'<a class="card" href="{slug}.html"><div class="cardhead"><h3>{esc(SLUG_NAME[slug])}</h3>'
            f'<span class="pill">{s["rows"]} rows</span></div>'
            f'<p>{esc(info.get("model_family") or "Governing-body model")}</p>'
            f'<div class="metrics"><span><b>{s["originated"]}</b> lined</span><span><b>{s["high"]}</b> high</span>'
            f'<span><b>{s["unlined"]}</b> blank</span></div></a>')
    body.append('</div>')
    return page("Sports", "sports/index.html", "".join(body), prefix="../")


def render_sport(rows, slug, stats):
    meta, _ = sport_meta()
    info = meta.get(slug, {})
    s = stats[slug]
    body = [
        f'<section class="hero"><p class="eyebrow"><a href="index.html">Sports</a> / {esc(SLUG_NAME[slug])}</p>',
        f'<h1>{esc(SLUG_NAME[slug])}</h1>',
        f'<p class="lede">{s["rows"]} unique fixtures across {len(s["comps"])} competitions, {esc(s["first"])} to {esc(s["last"])}. '
        f'{s["originated"]} carry originated markets and {s["unlined"]} are deliberately blank with a published reason. '
        f'High-confidence picks: {s["high"]}.</p></section>',
        '<div class="notice blue"><strong>Model and source.</strong> '
        f'{esc(info.get("model_family") or "Model documented in the source layer.")} '
        f'Official endpoint: <a href="{esc(info.get("official_url") or "#")}" rel="noopener">{esc(domain(info.get("official_url") or ""))}</a>. '
        f'OLBG category: <a href="{esc(info.get("olbg_url") or "#")}" rel="noopener">sport {esc(info.get("olbg_sport_id") or "—")}</a>.</div>',
        filter_bar([(slug, SLUG_NAME[slug])]),
        table(rows, show_sport=False),
    ]
    return page(SLUG_NAME[slug], f"sports/{slug}.html", "".join(body), prefix="../")


def render_verification(rows):
    status_counts = Counter((r.get("verification") or {}).get("status") for r in rows)
    checked = [r for r in rows if (r.get("verification") or {}).get("status") in ("reverified", "form", "corrected")]
    scope = Counter(r["source_scope"] for r in rows)
    body = [
        '<section class="hero"><p class="eyebrow">Evidence ledger</p><h1>Verification performed</h1>',
        '<p class="lede">This page separates what was actually re-read on 2026-10-22 from what was inherited from the source layers. '
        'A green badge means the value was checked against the official page linked on the row; amber means the row carries its original '
        'capture and has not been re-read in this pass. No value was promoted to verified without a page fetch.</p></section>',
        '<div class="kpis">',
        f'<div class="kpi"><div class="v">{status_counts.get("reverified",0)}</div><div class="k">fixtures re-read</div><div class="s">NHL schedule + SHL table</div></div>',
        f'<div class="kpi"><div class="v">{status_counts.get("form",0)}</div><div class="k">form re-read</div><div class="s">team record checked, fixture inherited</div></div>',
        f'<div class="kpi"><div class="v">{status_counts.get("corrected",0)}</div><div class="k">corrected</div><div class="s">golf fixture replaced</div></div>',
        f'<div class="kpi"><div class="v">{status_counts.get("unverified",0)}</div><div class="k">unverified</div><div class="s">non-official source, no market</div></div>',
        f'<div class="kpi"><div class="v">{status_counts.get("inherited",0)}</div><div class="k">inherited</div><div class="s">source link kept, not re-read</div></div>',
        '</div>',
        '<h2>Official pages read in this pass</h2>',
        '<div class="tablewrap"><table><thead><tr><th>Source</th><th>What it confirmed</th><th>Checks</th><th>Result</th></tr></thead><tbody>',
        '<tr><td><a href="https://api-web.nhle.com/v1/schedule/2026-10-22" rel="noopener">NHL schedule API</a></td><td>12 games, start times and venues on 22 Oct; first five fixtures matched game ids 2026020154–158</td><td>5</td><td><span class="badge ok">match</span></td></tr>',
        '<tr><td><a href="https://api-web.nhle.com/v1/standings/2026-10-22" rel="noopener">NHL standings</a></td><td>Boston 7-2-1 (36/22), Carolina 8-2-1 (42/27), Edmonton 7-1-1 (41/27)</td><td>3</td><td><span class="badge ok">match</span></td></tr>',
        '<tr><td><a href="https://api-web.nhle.com/v1/skater-stats-leaders/20262027/2?categories=goals,assists,points&amp;limit=10" rel="noopener">NHL skater leaders</a></td><td>Kaprizov 11 goals, Q. Hughes 11 assists, Matthews 18 points, McDavid 20 assists, Draisaitl 8 goals, MacKinnon 10 assists, Lehkonen 8 goals, Karlsson 10 assists, Schmaltz 7 goals</td><td>8</td><td><span class="badge ok">match</span></td></tr>',
        '<tr><td><a href="https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154" rel="noopener">NHL GameCenter NSH@BOS</a></td><td>Boston 7-2-1, Swayman 6-1-1 / 1.98 / .928, Pastrnak 6 points, Nashville 3-2-3, Josi 6 assists, O’Reilly 4 goals, Saros 3 wins</td><td>2</td><td><span class="badge ok">match</span> and one text correction</td></tr>',
        '<tr><td><a href="https://stats.swehockey.se/ScheduleAndResults/Standings/20961" rel="noopener">SHL official standings</a></td><td>Skellefteå 3rd, 19 pts, 5-3-2, 32:25, 3-1-1 home; Djurgården 12th, 0-2-3 away</td><td>1</td><td><span class="badge ok">match</span></td></tr>',
        '<tr><td><a href="https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview" rel="noopener">PGA Tour tournament page</a></td><td>Butterfield Bermuda Championship, Port Royal GC, 22–25 Oct 2026</td><td>1</td><td><span class="badge ok">fixture corrected</span></td></tr>',
        '<tr><td><a href="https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/" rel="noopener">PDC schedule article</a></td><td>Not readable past consent wall; no withdrawal confirmation found</td><td>0</td><td><span class="badge warn">not re-read</span></td></tr>',
        '</tbody></table></div>',
        '<h2>Every re-read or corrected row</h2>',
        '<div class="tablewrap"><table><thead><tr><th>Fixture</th><th>Status</th><th>What was checked</th><th>Source</th></tr></thead><tbody>',
    ]
    for r in checked:
        v = r["verification"]
        body.append(
            f'<tr><td>{esc(r["home"])} v {esc(r["away"])}<div class="tiny">{esc(r["date"])} · {esc(r["id"])}</div></td>'
            f'<td>{verification_badge(r)}</td><td>{esc(v.get("note"))}</td>'
            f'<td><a href="{esc(v.get("source_url") or r["official_url"])}" rel="noopener">{esc(domain(v.get("source_url") or r["official_url"]))}</a></td></tr>')
    body += ['</tbody></table></div>',
             '<h2>Coverage limits</h2>',
             '<div class="two-col"><div class="panel"><h3>What was not re-read</h3><ul class="clean">',
             f'<li><strong>{status_counts.get("inherited",0)} rows</strong> across 15 sports keep their original capture. Their source link is on the row; '
             'the site does not claim they were re-checked today.</li>',
             '<li>The PDC draw, ATP rankings table, LNR and URC tables, EHF, EuroLeague/EuroCup, NBA, MLB, Formula 1, ' 
             'SuperLega, PlusLiga, AFLW, NRL, LoL, GAA and GBGB pages were not fetched again for this pass.</li>',
             '<li>Player stats inside inherited write-ups are marked individually; 20 of the 43 listed facts are marked inherited.</li>',
             '</ul></div>',
             '<div class="panel"><h3>Source scope of the table</h3><ul class="clean">',
             f'<li><strong>{scope.get("fixture",0)} rows</strong> link to a page that identifies the individual fixture.</li>',
             f'<li><strong>{scope.get("competition",0)} rows</strong> link to a competition, rankings, player or tournament page.</li>',
             f'<li><strong>{scope.get("player",0)} rows</strong> link to a player page (two tennis rows) — flagged, because that page does not identify the fixture.</li>',
             '<li>Every URL is https and on a governing-body, league, tour or official tournament domain; no bookmaker or tipster URL is used as a source.</li>',
             '</ul></div></div>']
    return page("Verification", "verification.html", "".join(body))


def render_methodology(rows, preds):
    meta, excluded = sport_meta()
    body = [
        '<section class="hero"><p class="eyebrow">Method</p><h1>How the consolidated desk is built</h1>',
        '<p class="lede">The five published layers are merged by fixture, not added together. Market prices stay exactly as the originating '
        'layer computed them; confidence is regraded under one rule; predictions are written only for selections that clear both the '
        'probability and price constraints.</p></section>',
        '<h2>The confidence rule</h2>',
        '<div class="panel"><ul class="clean">',
        '<li><strong>High:</strong> model probability ≥ 70% <em>and</em> fair decimal price in 1.40–101.00 (American &minus;250 to +10000).</li>',
        '<li><strong>Medium:</strong> probability ≥ 60%, or ≥70% priced shorter than 1.40. The second case carries the reason '
        '“outside the focus band” rather than being silently called high.</li>',
        '<li><strong>Low:</strong> below 60%.</li>',
        '<li><strong>Unlined:</strong> no market is published and the reason is on the row.</li>',
        '</ul>',
        '<p class="tiny">The band is 1.40–101.00 decimal because &minus;250 American = 1.40 and +10000 = 101.00. A 70% probability is 1.43 decimal; '
        'therefore the overlap of “≥70%” and “no shorter than &minus;250” is 70.0–71.4%. That intersection produces the 15 high picks. '
        'A 75% favourite (1.33) is outside the band even though it is more likely to win; it is graded medium with that exact reason so the label never overstates the price constraint.</p></div>',
        '<h2>De-duplication and provenance</h2>',
        '<div class="panel"><p>Rows are clustered by sport, unordered team pair and date (with a one-day tolerance only when the two '
        'buckets share no source layer, which is how timezone-shifted duplicates merge without collapsing back-to-back games). '
        f'{sum(x["rows"] for x in layer_stats())} layer rows became <strong>{len(rows)} fixtures</strong>. Each row records the layer used, every layer that contained it, the original ids '
        'and the capture timestamp. The preferred row is the one with an originated status, an in-band outcome, the most markets and the '
        'highest layer priority (verified → hub → board → slate → forward).</p></div>',
        '<h2>Models by sport</h2>',
        '<div class="tablewrap"><table><thead><tr><th>Sport</th><th>Model</th><th>Official endpoint</th><th>OLBG id</th></tr></thead><tbody>',
    ]
    for slug in SPORT_ORDER:
        info = meta.get(slug, {})
        body.append(f'<tr><td>{esc(SLUG_NAME[slug])}</td><td>{esc(info.get("model_family") or "See source layer")}</td>'
                    f'<td><a href="{esc(info.get("official_url") or "#")}" rel="noopener">{esc(domain(info.get("official_url") or ""))}</a></td>'
                    f'<td>{esc(info.get("olbg_sport_id") or "—")}</td></tr>')
    body += ['</tbody></table></div>',
             '<h2>What the prices are and are not</h2>',
             '<div class="two-col"><div class="panel"><h3>Are</h3><ul class="clean">',
             '<li>Fair (no-vig) decimal prices derived from the model probability: <code>decimal = round(1/p, 2)</code>.</li>',
             '<li>Our own estimates from official governing-body inputs: records, goals, points, rankings, prize money.</li>',
             '<li>Consistent across probability, decimal and American odds on every row.</li>',
             '</ul></div><div class="panel"><h3>Are not</h3><ul class="clean">',
             '<li>Bookmaker quotes. No sportsbook price is read, scraped or synthesised.</li>',
             '<li>A claim that the market agrees. Where our fair price differs from a book, the model is the source of the number.</li>',
             '<li>Guarantees. Confidence is a model label, not a strike rate.</li>',
             '</ul></div></div>',
             f'<h2>Excluded categories</h2><p class="sub">Enforced in the consolidation script and asserted by tests: '
             + ", ".join(esc(s["name"]) for s in excluded) + '.</p>']
    return page("Methodology", "methodology.html", "".join(body))


def render_sources(rows):
    by_domain = defaultdict(list)
    for r in rows:
        by_domain[domain(r["official_url"])].append(r)
    body = [
        '<section class="hero"><p class="eyebrow">Provenance</p><h1>Sources</h1>',
        '<p class="lede">Every row links to a governing-body, league, tour, tournament or official club page. '
        'The table groups the consolidated set by host so the provenance can be audited at a glance.</p></section>',
        '<div class="kpis">',
        f'<div class="kpi"><div class="v">{len(by_domain)}</div><div class="k">hosts</div><div class="s">all https</div></div>',
        f'<div class="kpi"><div class="v">{sum(1 for r in rows if r["source_scope"]=="fixture")}</div><div class="k">fixture pages</div><div class="s">individual match URL</div></div>',
        f'<div class="kpi"><div class="v">{sum(1 for r in rows if r["source_scope"]!="fixture")}</div><div class="k">competition / player</div><div class="s">disclosed per row</div></div>',
        '</div>',
        '<div class="tablewrap"><table><thead><tr><th>Host</th><th>Rows</th><th>Sports</th><th>Example link</th></tr></thead><tbody>',
    ]
    for host in sorted(by_domain, key=lambda h: (-len(by_domain[h]), h)):
        items = by_domain[host]
        sports = ", ".join(sorted({r["sport_name"] for r in items}))
        example = items[0]["official_url"]
        body.append(f'<tr><td>{esc(host)}</td><td>{len(items)}</td><td>{esc(sports)}</td>'
                    f'<td><a href="{esc(example)}" rel="noopener">{esc(example[:70])}{"…" if len(example)>70 else ""}</a></td></tr>')
    body += ['</tbody></table></div>',
             '<h2>Official source registry</h2>',
             '<div class="panel"><ul class="clean">',
             '<li><strong>NHL:</strong> <a href="https://api-web.nhle.com/v1/standings/2026-10-22" rel="noopener">standings</a>, '
             '<a href="https://api-web.nhle.com/v1/skater-stats-leaders/20262027/2" rel="noopener">skater leaders</a>, '
             '<a href="https://www.nhl.com/gamecenter" rel="noopener">GameCenter</a></li>',
             '<li><strong>SHL:</strong> <a href="https://stats.swehockey.se/ScheduleAndResults/Standings/20961" rel="noopener">Svenska Ishockeyförbundet standings</a></li>',
             '<li><strong>NBA:</strong> <a href="https://www.nba.com/schedule" rel="noopener">official schedule</a> · '
             '<strong>EuroLeague/EuroCup:</strong> <a href="https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games" rel="noopener">official live API</a></li>',
             '<li><strong>Rugby:</strong> <a href="https://top14.lnr.fr/classement" rel="noopener">LNR Top 14</a>, '
             '<a href="https://prod2.lnr.fr/classement" rel="noopener">LNR Pro D2</a>, '
             '<a href="https://stats.unitedrugby.com/match-centre/table/2026-27" rel="noopener">URC</a></li>',
             '<li><strong>Darts:</strong> <a href="https://www.pdc.tv/rankings" rel="noopener">PDC rankings</a> · '
             '<strong>Snooker:</strong> <a href="https://www.wst.tv/rankings" rel="noopener">WST rankings</a></li>',
             '<li><strong>Tennis:</strong> <a href="https://www.atptour.com/en/rankings/singles" rel="noopener">PIF ATP rankings</a> · '
             '<strong>Handball:</strong> <a href="https://ehfcl.eurohandball.com/men/2026-27/standings/" rel="noopener">EHF Champions League</a></li>',
             '<li><strong>Baseball:</strong> <a href="https://statsapi.mlb.com/api/v1/schedule/postseason?season=2026" rel="noopener">MLB StatsAPI</a> · '
             '<strong>Motor racing:</strong> <a href="https://www.formula1.com/en/results/2026/drivers" rel="noopener">Formula 1 results</a></li>',
             '<li><strong>Volleyball:</strong> <a href="https://www.legavolley.it/calendario/" rel="noopener">Lega Pallavolo</a>, '
             '<a href="https://www.plusliga.pl/games.html" rel="noopener">PlusLiga</a> · '
             '<strong>Golf:</strong> <a href="https://www.pgatour.com/schedule" rel="noopener">PGA Tour</a></li>',
             '<li><strong>Rugby league:</strong> <a href="https://www.nrl.com/draw/" rel="noopener">NRL</a> · '
             '<strong>Gaelic:</strong> <a href="https://www.gaa.ie/fixtures-results/" rel="noopener">GAA</a> · '
             '<strong>Greyhounds:</strong> <a href="https://www.gbgb.org.uk/racing/results/" rel="noopener">GBGB</a></li>',
             '<li><strong>Aussie Rules:</strong> <a href="https://www.afl.com.au/aflw" rel="noopener">AFLW</a> · '
             '<strong>eSports:</strong> <a href="https://lolesports.com/" rel="noopener">LoL Esports</a></li>',
             '</ul></div>',
             '<div class="notice"><strong>No third-party tipster or bookmaker source is used.</strong> OLBG is the subject of the '
             'reverse-engineering, not a source for prices. Its category URLs appear only as taxonomy labels.</div>']
    return page("Sources", "sources.html", "".join(body))


def render_archive(rows):
    stats = {s["name"]: s for s in layer_stats()}
    notes = {
        "hub": f"Primary-source hub, newest capture ({stats['hub']['sports']} sports). Its own ≥65% threshold labels more picks high than the strict rule used here.",
        "slate": "Widest sport list, including Aussie Rules and eSports. Row-level confidence used a price-only band; synthetic book columns are dropped here.",
        "board": "Forward window rows plus World Series games. Board prices come from the same model family as the verified desk.",
        "verified": "The primary-source desk re-read line by line earlier on 22 Oct; the source of most band picks.",
        "forward": "Forward window 23 Oct–2 Nov across NHL, NBA and MLB.",
    }
    layers = [(name, f"../{name}/index.html", stats[name]["rows"], stats[name]["lined"], notes[name])
              for name, _f, _k in LAYER_FILES]
    body = ['<section class="hero"><p class="eyebrow">Provenance</p><h1>Source layers</h1>',
            '<p class="lede">The consolidated desk is a merge, not a sum. These five layers remain published exactly as their own sessions '
            'left them, so every merged value can be traced back. Do not add their counts together: they overlap heavily.</p></section>',
            '<div class="tablewrap"><table><thead><tr><th>Layer</th><th>Rows</th><th>Lined</th><th>What it contributes</th><th>Link</th></tr></thead><tbody>']
    for name, url, count, lined, note in layers:
        body.append(f'<tr><td><strong>{esc(name)}</strong></td><td>{count}</td><td>{lined}</td><td>{esc(note)}</td>'
                    f'<td><a href="{url}" rel="noopener">open /{name}/</a></td></tr>')
    body += ['</tbody></table></div>',
             '<h2>Overlap</h2><div class="panel"><p>'
             f'{len(rows)} unique fixtures came from {sum(s["rows"] for s in stats.values())} layer rows. '
             f'{sum(1 for r in rows if len(r["provenance"]["layers"]) > 1)} fixtures appeared in two or more layers; '
             'the same fixture can carry different model probabilities because each layer ran its own model on its own capture. '
             'The consolidated desk keeps one row per fixture and records the other layers in provenance rather than blending the numbers.'
             '</p></div>',
             '<h2>Root pages</h2><p class="sub">The earlier root dashboard and its evidence pages remain at '
             '<a href="../index.html">/index.html</a>, <a href="../verification.html">/verification.html</a>, '
             '<a href="../integration.html">/integration.html</a>. They describe the earlier 118-row desk, not this consolidated table.</p>']
    return page("Source layers", "archive.html", "".join(body))


# --------------------------------------------------------------------------- main
def main():
    global TOTAL_ROWS
    payload = read(DATA / "matches.json")
    rows = payload["matches"]
    TOTAL_ROWS = len(rows)
    preds = read(DATA / "predictions.json")["predictions"]
    stats = sport_stats(rows)

    write(OUT / "assets" / "style.css", CSS)
    write(OUT / "assets" / "app.js", JS)
    write(OUT / "index.html", render_index(rows, preds, stats))
    write(OUT / "matches.html", render_matches(rows))
    write(OUT / "sports" / "index.html", render_sports_index(rows, stats))
    for slug in SPORT_ORDER:
        if slug in stats:
            write(OUT / "sports" / f"{slug}.html", render_sport([r for r in rows if r["sport"] == slug], slug, stats))
    write(OUT / "picks.html", render_picks(preds))
    write(OUT / "verification.html", render_verification(rows))
    write(OUT / "flagged.html", render_flags(rows, preds))
    write(OUT / "methodology.html", render_methodology(rows, preds))
    write(OUT / "sources.html", render_sources(rows))
    write(OUT / "archive.html", render_archive(rows))
    pages = len(list(OUT.rglob("*.html")))
    print(f"built {pages} pages, {len(rows)} rows, {len(preds)} predictions")


if __name__ == "__main__":
    main()
