#!/usr/bin/env python3
"""Build self-contained static HTML dashboard & CSS/JS assets under verified/.

Generates:
  - verified/assets/style.css
  - verified/assets/app.js
  - verified/index.html
  - verified/predictions.html
  - verified/flagged.html        (explicitly titled & headed 'Flagged for Review')
  - verified/audit.html
  - verified/methodology.html
  - verified/sports/<slug>.html  (all 17 eligible OLBG sports)
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "verified"
SITE = ROOT / "verified"

CSS = """\
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-alt: #f1f5f9;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --ink: #0f172a;
  --ink-muted: #475569;
  --ink-subtle: #64748b;
  --accent: #0f766e;
  --accent-soft: #ccfbf1;
  --accent-ink: #115e59;
  --high-bg: #dcfce7;
  --high-ink: #166534;
  --med-bg: #fef9c3;
  --med-ink: #854d0e;
  --low-bg: #f1f5f9;
  --low-ink: #334155;
  --flag-bg: #fef2f2;
  --flag-border: #fecaca;
  --flag-ink: #991b1b;
  --warn-bg: #fffbeb;
  --warn-ink: #92400e;
  --link: #0369a1;
  --radius: 10px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.55;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}

a {
  color: var(--link);
  text-decoration: none;
}
a:hover { text-decoration: underline; }

.topbar {
  background: #0f172a;
  color: #f8fafc;
  border-bottom: 1px solid #1e293b;
  position: sticky;
  top: 0;
  z-index: 30;
}
.topbar-inner {
  max-width: 1380px;
  margin: 0 auto;
  padding: 0.75rem 1.25rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem 1.25rem;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 700;
  font-size: 1rem;
  color: #f8fafc;
  letter-spacing: -0.01em;
}
.brand:hover { text-decoration: none; color: #5eead4; }
.brand-badge {
  background: #0d9488;
  color: #ffffff;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.16rem 0.48rem;
  border-radius: 999px;
  letter-spacing: 0.04em;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}
.nav a {
  color: #cbd5e1;
  font-size: 0.86rem;
  font-weight: 500;
  padding: 0.36rem 0.68rem;
  border-radius: 6px;
  transition: background 0.15s, color 0.15s;
}
.nav a:hover, .nav a.active {
  background: #1e293b;
  color: #ffffff;
  text-decoration: none;
}
.nav a.nav-flag {
  color: #fecaca;
}
.nav a.nav-flag.active, .nav a.nav-flag:hover {
  background: #7f1d1d;
  color: #ffffff;
}

.subbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.subbar-inner {
  max-width: 1380px;
  margin: 0 auto;
  padding: 0.5rem 1.25rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.75rem;
  align-items: center;
  font-size: 0.8rem;
  color: var(--ink-muted);
}
.subbar a {
  font-weight: 500;
  color: var(--ink-muted);
}
.subbar a:hover { color: var(--accent); }

.container {
  max-width: 1380px;
  margin: 0 auto;
  padding: 1.75rem 1.25rem 3.5rem;
}

.hero {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.6rem 1.75rem;
  margin-bottom: 1.5rem;
}
.eyebrow {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--accent);
  margin: 0 0 0.4rem;
}
.hero h1 {
  margin: 0 0 0.55rem;
  font-size: 1.85rem;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.hero p {
  margin: 0;
  color: var(--ink-muted);
  max-width: 92ch;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
  gap: 0.9rem;
  margin-bottom: 1.75rem;
}
.kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.15rem;
}
.kpi-val {
  font-size: 1.65rem;
  font-weight: 750;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}
.kpi-label {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--ink-muted);
}

.section-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem 1rem;
  margin: 2rem 0 0.9rem;
}
.section-head h2 {
  margin: 0;
  font-size: 1.3rem;
  letter-spacing: -0.015em;
}
.section-head p {
  margin: 0;
  font-size: 0.88rem;
  color: var(--ink-muted);
}

.sport-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 0.9rem;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.1rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
}
.card h3 {
  margin: 0;
  font-size: 1.02rem;
}
.card p {
  margin: 0;
  font-size: 0.86rem;
  color: var(--ink-muted);
}
.card-meta {
  margin-top: auto;
  padding-top: 0.55rem;
  border-top: 1px solid var(--surface-alt);
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.4rem;
  font-size: 0.79rem;
  color: var(--ink-subtle);
}

.pill {
  display: inline-block;
  padding: 0.16rem 0.52rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.pill-high { background: var(--high-bg); color: var(--high-ink); }
.pill-medium { background: var(--med-bg); color: var(--med-ink); }
.pill-low { background: var(--low-bg); color: var(--low-ink); }
.pill-unlined { background: var(--flag-bg); color: var(--flag-ink); border: 1px solid var(--flag-border); }
.pill-originated { background: var(--accent-soft); color: var(--accent-ink); }
.pill-excluded { background: #e2e8f0; color: #334155; }
.pill-sev-high { background: #fee2e2; color: #991b1b; }
.pill-sev-medium { background: #fef3c7; color: #92400e; }
.pill-sev-low { background: #e0f2fe; color: #075985; }

.controls {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem 0.9rem;
  align-items: center;
}
.controls input, .controls select {
  padding: 0.44rem 0.68rem;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  font-size: 0.86rem;
  background: #ffffff;
  color: var(--ink);
}
.controls input { min-width: 240px; flex: 1 1 240px; }
.controls .count-note {
  font-size: 0.82rem;
  color: var(--ink-muted);
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}
th {
  background: var(--surface-alt);
  color: var(--ink);
  font-weight: 650;
  text-align: left;
  padding: 0.68rem 0.75rem;
  border-bottom: 1px solid var(--border-strong);
  white-space: nowrap;
}
td {
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  font-variant-numeric: tabular-nums;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f8fafc; }

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8rem;
}
.blank-cell {
  color: var(--ink-subtle);
  font-style: italic;
}
.source-links {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  font-size: 0.78rem;
  white-space: nowrap;
}
.provenance {
  margin-top: 0.35rem;
  font-size: 0.75rem;
  line-height: 1.4;
  color: var(--ink-muted);
  max-width: 32rem;
}
.provenance strong { color: var(--accent-ink); }
.gate-note {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--ink-muted);
  max-width: 24rem;
}
.table-wrap table { min-width: 1180px; }

.pred-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}
.pred-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: var(--radius);
  padding: 1.25rem 1.4rem;
}
.pred-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.45rem;
}
.pred-card h3 {
  margin: 0.2rem 0 0.55rem;
  font-size: 1.1rem;
}
.pred-pick-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.1rem;
  background: var(--surface-alt);
  padding: 0.55rem 0.8rem;
  border-radius: 6px;
  font-size: 0.84rem;
  margin-bottom: 0.75rem;
  font-variant-numeric: tabular-nums;
}
.pred-body {
  margin: 0 0 0.85rem;
  color: var(--ink);
  font-size: 0.95rem;
  line-height: 1.62;
}
.fact-list {
  margin: 0;
  padding-left: 1.15rem;
  font-size: 0.82rem;
  color: var(--ink-muted);
}
.fact-list li { margin-bottom: 0.25rem; }

.callout-warn {
  background: var(--warn-bg);
  border: 1px solid #fde68a;
  color: var(--warn-ink);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  margin-bottom: 1.25rem;
  font-size: 0.9rem;
}

footer {
  max-width: 1380px;
  margin: 0 auto;
  padding: 1.5rem 1.25rem 2.5rem;
  border-top: 1px solid var(--border);
  color: var(--ink-subtle);
  font-size: 0.8rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem 1.5rem;
}
"""

JS = """\
(function () {
  function initTableFilter() {
    var search = document.getElementById('filter-search');
    var sport = document.getElementById('filter-sport');
    var conf = document.getElementById('filter-conf');
    var status = document.getElementById('filter-status');
    var countEl = document.getElementById('filter-count');
    var rows = Array.prototype.slice.call(document.querySelectorAll('tr[data-match-row="1"]'));
    if (!rows.length) return;

    function apply() {
      var q = search ? search.value.trim().toLowerCase() : '';
      var sp = sport ? sport.value : 'all';
      var cf = conf ? conf.value : 'all';
      var st = status ? status.value : 'all';
      var shown = 0;
      rows.forEach(function (tr) {
        var ok = true;
        if (sp !== 'all' && tr.getAttribute('data-sport') !== sp) ok = false;
        if (cf !== 'all' && tr.getAttribute('data-conf') !== cf) ok = false;
        if (st !== 'all' && tr.getAttribute('data-status') !== st) ok = false;
        if (ok && q && tr.textContent.toLowerCase().indexOf(q) === -1) ok = false;
        tr.style.display = ok ? '' : 'none';
        if (ok) shown += 1;
      });
      if (countEl) {
        countEl.textContent = 'Showing ' + shown + ' of ' + rows.length + ' verified rows';
      }
    }

    [search, sport, conf, status].forEach(function (el) {
      if (el) {
        el.addEventListener('input', apply);
        el.addEventListener('change', apply);
      }
    });
    apply();
  }

  function initPredFilter() {
    var sel = document.getElementById('pred-sport-filter');
    var cards = Array.prototype.slice.call(document.querySelectorAll('[data-pred-card="1"]'));
    var countEl = document.getElementById('pred-filter-count');
    if (!sel || !cards.length) return;
    sel.addEventListener('change', function () {
      var v = sel.value;
      var shown = 0;
      cards.forEach(function (c) {
        var ok = (v === 'all' || c.getAttribute('data-sport') === v);
        c.style.display = ok ? '' : 'none';
        if (ok) shown += 1;
      });
      if (countEl) countEl.textContent = 'Showing ' + shown + ' of ' + cards.length + ' HIGH confidence picks';
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTableFilter();
    initPredFilter();
  });
})();
"""


def esc(val: object) -> str:
    if val is None or val == "":
        return "—"
    return html.escape(str(val), quote=True)


def render_shell(title: str, active: str, body: str, depth: int = 0) -> str:
    capture = json.loads((DATA / "sports.json").read_text(encoding="utf-8"))["captured_at"]
    prefix = "../" * depth
    root_prefix = "../" * (depth + 1)
    nav_items = [
        ("index", f"{prefix}index.html", "Overview & All Matches", ""),
        ("predictions", f"{prefix}predictions.html", "High-Confidence Picks", ""),
        ("flagged", f"{prefix}flagged.html", "Flagged for Review", "nav-flag"),
        ("audit", f"{prefix}audit.html", "Line-by-Line Repo Audit", ""),
        ("methodology", f"{prefix}methodology.html", "Methodology & Models", ""),
    ]
    nav_html = "\n".join(
        f'<a href="{href}" class="{" ".join(c for c in [cls, "active" if key == active else ""] if c)}">{label}</a>'
        for key, href, label, cls in nav_items
    )
    live_link = (
        f'<span>·</span>\n      <a href="{root_prefix}live/index.html">Live Slate (/live/)</a>\n      '
        if (ROOT / "live" / "index.html").exists()
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — OLBG Verified Multi-Sport Origination Desk</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="{prefix}index.html">
        <span>OLBG Verified Research &amp; Origination Desk</span>
        <span class="brand-badge">{capture} Source Audit</span>
      </a>
      <nav class="nav" aria-label="Primary navigation">
        {nav_html}
      </nav>
    </div>
  </header>
  <div class="subbar">
    <div class="subbar-inner">
      <span><strong>Cross-Layer Navigation:</strong></span>
      <a href="{root_prefix}index.html">Root Dashboard (/)</a>
      {live_link}<span>·</span>
      <a href="{root_prefix}survey/index.html">All-Sports Survey (/survey/)</a>
      <span>·</span>
      <a href="{root_prefix}site/index.html">Evidence Desk v2 (/site/)</a>
      <span>·</span>
      <a href="{root_prefix}integration.html">Integration Status</a>
    </div>
  </div>
  <main class="container">
{body}
  </main>
  <footer>
    <div>Capture: <strong>{capture}</strong>. Every row carries an official source or review link plus a discovery/confirmation state. Unconfirmed fields remain blank (<code>—</code>) and are listed on <a href="{prefix}flagged.html">Flagged for Review</a>. Stored inputs retain their own capture caveats.</div>
    <div>Excluded per brief: Soccer/Football, Horse Racing, American Football, Boxing, UFC/MMA, Hurling, Cycling, Specials.</div>
  </footer>
  <script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def fmt_winner(wm: dict | None, home: str, away: str) -> str:
    if not wm:
        return '<span class="blank-cell">—</span>'
    if wm.get("draw_prob") is not None:
        return (
            f"<div><strong>{esc(home)}:</strong> {wm['home_odds']:.2f} ({wm['home_prob']*100:.1f}%)</div>"
            f"<div><strong>Draw:</strong> {wm['draw_odds']:.2f} ({wm['draw_prob']*100:.1f}%)</div>"
            f"<div><strong>{esc(away)}:</strong> {wm['away_odds']:.2f} ({wm['away_prob']*100:.1f}%)</div>"
        )
    return (
        f"<div><strong>{esc(home)}:</strong> {wm['home_odds']:.2f} ({wm['home_prob']*100:.1f}%)</div>"
        f"<div><strong>{esc(away)}:</strong> {wm['away_odds']:.2f} ({wm['away_prob']*100:.1f}%)</div>"
    )


def fmt_handicap(hm: dict | None) -> str:
    if not hm:
        return '<span class="blank-cell">—</span>'
    return (
        f"<div>{esc(hm['label'])}</div>"
        f"<div><strong>Cover:</strong> {hm['fav_odds']:.2f} ({hm['fav_prob']*100:.1f}%) · "
        f"<strong>Opp:</strong> {hm['dog_odds']:.2f} ({hm['dog_prob']*100:.1f}%)</div>"
    )


def fmt_total(tm: dict | None) -> str:
    if not tm:
        return '<span class="blank-cell">—</span>'
    proj = f" (proj {tm['projected']})" if tm.get("projected") is not None else ""
    return (
        f"<div>Line <strong>{tm['line']}</strong>{esc(proj)}</div>"
        f"<div><strong>O:</strong> {tm['over_odds']:.2f} ({tm['over_prob']*100:.1f}%) · "
        f"<strong>U:</strong> {tm['under_odds']:.2f} ({tm['under_prob']*100:.1f}%)</div>"
    )


def render_match_table(rows: list[dict], depth: int = 0, show_sport_col: bool = True) -> str:
    prefix = "../" * depth
    sport_th = "<th>Sport</th>" if show_sport_col else ""
    body_rows: list[str] = []
    for m in rows:
        conf = m["pick"]["confidence"] if m.get("pick") else "unlined"
        status = m["line_status"]
        sport_td = (
            f'<td><a href="{prefix}sports/{esc(m["sport"])}.html"><strong>{esc(m["sport_name"])}</strong></a></td>'
            if show_sport_col
            else ""
        )
        venue_html = esc(m["venue"]) if m.get("venue") else '<span class="blank-cell">—</span>'
        if m.get("home_summary") or m.get("away_summary"):
            form_html = (
                f"<div><strong>{esc(m['home'])}:</strong> {esc(m.get('home_summary'))}</div>"
                f"<div><strong>{esc(m['away'])}:</strong> {esc(m.get('away_summary'))}</div>"
            )
        else:
            reason = m.get("blank_reason") or "Unconfirmed on official feed — flagged for review"
            form_html = f'<span class="blank-cell">— ({esc(reason)})</span>'

        if m.get("pick"):
            p = m["pick"]
            american = p.get("fair_american")
            american_text = f"{american:+d}" if isinstance(american, int) else "—"
            gate = p.get("high_gate") or {}
            gate_html = ""
            if conf == "high":
                gate_html = '<div class="gate-note">High gate passed: probability and fair price both qualify.</div>'
            elif gate.get("probability_gt_70") and not gate.get("eligible"):
                gate_html = f'<div class="gate-note">High blocked: fair American {american_text} fails the required price band.</div>'
            elif m.get("confidence_cap") == "medium":
                gate_html = '<div class="gate-note">Medium cap: prior-season NBA baseline.</div>'
            pick_html = (
                f"<div><strong>{esc(p['selection'])}</strong></div>"
                f"<div>Fair <strong>{p['fair_odds']:.2f}</strong> · American <strong>{american_text}</strong> ({p['probability']*100:.1f}%)</div>"
                + gate_html
                + (
                    f'<div><a href="{prefix}predictions.html#{esc(m["id"])}">Read full write-up →</a></div>'
                    if conf == "high"
                    else ""
                )
            )
            badge_html = f'<span class="pill pill-{esc(conf)}">{esc(conf)}</span>'
        else:
            pick_html = f'<span class="blank-cell">— (<a href="{prefix}flagged.html#{esc(m["id"])}">Flagged</a>)</span>'
            badge_html = '<span class="pill pill-unlined">Unlined</span>'

        official_label = m.get("official_source") or "Official source"
        if m["line_status"] == "unlined":
            official_label = f"Official review: {official_label}"
        links = [f'<a href="{esc(m["official_url"])}" target="_blank" rel="noopener">{esc(official_label)} ↗</a>']
        if m.get("data_url"):
            links.append(f'<a href="{esc(m["data_url"])}" target="_blank" rel="noopener">Official model input / standings ↗</a>')
        if m.get("olbg_url"):
            event_label = f"OLBG card #{m['olbg_event_id']}" if m.get("olbg_event_id") else "OLBG market"
            links.append(f'<a href="{esc(m["olbg_url"])}" target="_blank" rel="noopener">{esc(event_label)} ↗</a>')
        prov = m.get("provenance") or {}
        prov_html = ""
        if prov:
            prov_html = (
                f'<div class="provenance"><strong>{esc(prov.get("discovery"))}</strong>'
                f' · {esc(prov.get("official_status"))}<br>{esc(prov.get("time_basis"))}</div>'
            )
        date_html = ""
        if m.get("date") and m["date"] not in str(m.get("time")):
            date_html = f'<div class="mono">Official/raw date: {esc(m["date"])}</div>'

        body_rows.append(
            f'<tr id="{esc(m["id"])}" data-match-row="1" data-sport="{esc(m["sport"])}" '
            f'data-conf="{esc(conf)}" data-status="{esc(status)}">'
            f"{sport_td}"
            f"<td><div><strong>{esc(m['competition'])}</strong></div>{date_html}<div class=\"mono\">{esc(m['time'])}</div></td>"
            f"<td><div><strong>{esc(m['home'])}</strong> vs <strong>{esc(m['away'])}</strong></div>"
            f"<div style=\"font-size:0.78rem;color:#64748b;\">Venue: {venue_html}</div></td>"
            f"<td>{form_html}</td>"
            f"<td>{fmt_winner(m.get('winner_market'), m['home'], m['away'])}</td>"
            f"<td>{fmt_handicap(m.get('handicap_market'))}</td>"
            f"<td>{fmt_total(m.get('total_market'))}</td>"
            f"<td>{pick_html}</td>"
            f"<td>{badge_html}</td>"
            f'<td><div class="source-links">{"".join(links)}</div>{prov_html}</td>'
            f"</tr>"
        )

    return f"""<div class="table-wrap">
  <table>
    <thead>
      <tr>
        {sport_th}
        <th>Competition &amp; Time</th>
        <th>Match &amp; Venue</th>
        <th>Official Form / Ranking / Blank Reason</th>
        <th>Originated Winner Line</th>
        <th>Handicap / Spread</th>
        <th>Match Total</th>
        <th>Model Pick &amp; Price</th>
        <th>Confidence</th>
        <th>Official / Review Sources &amp; Provenance</th>
      </tr>
    </thead>
    <tbody>
      {"".join(body_rows)}
    </tbody>
  </table>
</div>"""


def render_prediction_card(p: dict, depth: int = 0) -> str:
    prefix = "../" * depth
    wc = p["word_count"]
    facts_html = "\n".join(
        f'<li>{esc(f["claim"])} — <a href="{esc(f["source"])}" target="_blank" rel="noopener">Official Source ↗</a></li>'
        for f in p["facts"]
    )
    olbg_link = (
        f' · <a href="{esc(p["olbg_url"])}" target="_blank" rel="noopener">OLBG Hub / Card ↗</a>'
        if p.get("olbg_url")
        else ""
    )
    return f"""<article class="pred-card" id="{esc(p['match_id'])}" data-pred-card="1" data-sport="{esc(p['sport'])}">
  <div class="pred-header">
    <div>
      <span class="pill pill-high">HIGH CONFIDENCE</span>
      <a href="{prefix}sports/{esc(p['sport'])}.html" style="margin-left:0.45rem;font-weight:600;">{esc(p['sport_name'])}</a>
      <span style="color:#64748b;font-size:0.84rem;"> · {esc(p['competition'])} · {esc(p['time'])}</span>
    </div>
    <span class="mono" style="color:#64748b;">{wc} words · ID: {esc(p['match_id'])}</span>
  </div>
  <h3>{esc(p['headline'])}</h3>
  <div class="pred-pick-bar">
    <span><strong>Fixture:</strong> {esc(p['event'])}</span> ·
    <span><strong>Selection:</strong> {esc(p['selection'])}</span> ·
    <span><strong>Model Win Prob:</strong> {p['probability']*100:.1f}%</span> ·
    <span><strong>Originated Fair Odds:</strong> {p['fair_odds']:.2f}</span> ·
    <span><strong>Fair American:</strong> {p['fair_american']:+d}</span>
  </div>
  <p class="pred-body">{esc(p['text'])}</p>
  <ul class="fact-list">
    {facts_html}
  </ul>
  <div style="margin-top:0.65rem;font-size:0.8rem;">
    <a href="{esc(p['official_url'])}" target="_blank" rel="noopener">Verify Official Match Record ↗</a>{olbg_link}
  </div>
</article>"""


def main() -> None:
    sports_doc = json.loads((DATA / "sports.json").read_text())
    matches_doc = json.loads((DATA / "matches.json").read_text())
    preds_doc = json.loads((DATA / "predictions.json").read_text())
    flags_doc = json.loads((DATA / "flagged.json").read_text())
    audit_doc = json.loads((DATA / "repo_audit.json").read_text())

    eligible = sports_doc["eligible_sports"]
    excluded = sports_doc["excluded_sports"]
    matches = matches_doc["matches"]
    preds = preds_doc["predictions"]
    flags = flags_doc["items"]
    audits = audit_doc["findings"]
    counts = matches_doc["counts"]
    captured_at = matches_doc["captured_at"]
    discovered_count = sum(1 for m in matches if (m.get("provenance") or {}).get("discovery") == "OLBG-discovered")
    supplement_count = sum(1 for m in matches if (m.get("provenance") or {}).get("discovery") == "official supplementary")
    originated_sports = len({m["sport"] for m in matches if m["line_status"] == "originated"})

    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    (SITE / "sports").mkdir(parents=True, exist_ok=True)
    (SITE / "assets" / "style.css").write_text(CSS)
    (SITE / "assets" / "app.js").write_text(JS)

    by_sport: dict[str, list[dict]] = {s["slug"]: [] for s in eligible}
    for m in matches:
        by_sport[m["sport"]].append(m)
    preds_by_sport: dict[str, list[dict]] = {s["slug"]: [] for s in eligible}
    for p in preds:
        preds_by_sport[p["sport"]].append(p)

    # 1. Landing Page (/verified/index.html)
    sport_cards = []
    for s in eligible:
        s_rows = by_sport[s["slug"]]
        n_orig = sum(1 for r in s_rows if r["line_status"] == "originated")
        n_unl = sum(1 for r in s_rows if r["line_status"] == "unlined")
        n_high = sum(1 for r in s_rows if (r.get("pick") or {}).get("confidence") == "high")
        badge = (
            f'<span class="pill pill-originated">{n_orig} Originated</span>'
            if n_orig
            else f'<span class="pill pill-unlined">{n_unl} Unlined</span>'
        )
        sport_cards.append(
            f'<div class="card">'
            f'<div class="card-top"><h3><a href="sports/{esc(s["slug"])}.html">{esc(s["name"])}</a></h3>{badge}</div>'
            f"<p>{esc(s['status_summary'])}</p>"
            f'<div class="card-meta">'
            f"<span>Rows: <strong>{len(s_rows)}</strong> ({n_high} HIGH)</span>"
            f'<a href="{esc(s["official_url"])}" target="_blank" rel="noopener">{esc(s["governing_body"])} ↗</a>'
            f"</div></div>"
        )

    excl_rows = "".join(
        f'<tr><td><strong>{esc(x["label"])}</strong></td>'
        f'<td><span class="pill pill-excluded">Excluded</span></td>'
        f'<td>{esc(x["reason"])}</td>'
        f'<td><a href="{esc(x["olbg_url"])}" target="_blank" rel="noopener">OLBG Hub ↗</a></td></tr>'
        for x in excluded
    )

    sport_opts = "".join(
        f'<option value="{esc(s["slug"])}">{esc(s["name"])} ({len(by_sport[s["slug"]])})</option>'
        for s in eligible
    )

    top_preds_preview = "\n".join(render_prediction_card(p, depth=0) for p in preds[:6])

    index_body = f"""
<section class="hero">
  <p class="eyebrow">Independent Primary-Source Verification &amp; Line Origination</p>
  <h1>OLBG Multi-Sport Verified Origination Desk</h1>
  <p>Cleanroom review of <strong>OLBG.com</strong> across all <strong>{len(eligible)} eligible sports</strong> on <strong>{captured_at}</strong>, strictly excluding Soccer/Football, Horse Racing, American Football, Boxing, UFC/MMA, Hurling, Cycling, and Specials. The desk contains <strong>{discovered_count} static OLBG-discovered cards</strong> plus <strong>{supplement_count} clearly labelled official supplements</strong>. Confirmation and pending states are shown per row; no third-party or inferred values fill official-data gaps.</p>
</section>

<div class="kpi-grid">
  <div class="kpi"><div class="kpi-val">{len(eligible)}</div><div class="kpi-label">Eligible OLBG Sports Audited (8 Excluded)</div></div>
  <div class="kpi"><div class="kpi-val">{counts['total_rows']}</div><div class="kpi-label">Catalogued Match &amp; Market Rows</div></div>
  <div class="kpi"><div class="kpi-val">{counts['originated_rows']}</div><div class="kpi-label">Independently Originated Lines ({originated_sports} Sports)</div></div>
  <div class="kpi"><div class="kpi-val">{counts['high_confidence']}</div><div class="kpi-label">Bespoke Human HIGH Picks (&ge;30 Words)</div></div>
  <div class="kpi"><div class="kpi-val">{counts['unlined_rows']}</div><div class="kpi-label">Unconfirmed Rows Left Blank &amp; Flagged</div></div>
  <div class="kpi"><div class="kpi-val">{len(audits)}</div><div class="kpi-label">Existing Repo Audit Findings Documented</div></div>
</div>

<div class="section-head">
  <h2>Featured High-Confidence Human Predictions</h2>
  <p><a href="predictions.html">View all {len(preds)} bespoke HIGH-confidence write-ups →</a></p>
</div>
<div class="pred-list">
  {top_preds_preview}
</div>

<div class="section-head">
  <h2>Eligible Sports Coverage ({len(eligible)} Sports)</h2>
  <p>Select any sport subpage to inspect competition models, market availability, and row-level official source links.</p>
</div>
<div class="sport-grid">
  {"".join(sport_cards)}
</div>

<div class="section-head" id="master-schedule">
  <h2>Master Multi-Sport Origination Table ({counts['total_rows']} Catalogued Rows)</h2>
  <p>Every row links to an official fixture, standings page, or explicitly labelled review source. Unconfirmed inputs render as <code>—</code> rather than guesses.</p>
</div>
<div class="controls">
  <input id="filter-search" type="search" placeholder="Search team, player, competition, or venue…">
  <select id="filter-sport" aria-label="Filter by sport">
    <option value="all">All 17 Eligible Sports ({counts['total_rows']})</option>
    {sport_opts}
  </select>
  <select id="filter-conf" aria-label="Filter by confidence">
    <option value="all">All Confidence Grades</option>
    <option value="high">HIGH ({counts['high_confidence']})</option>
    <option value="medium">MEDIUM ({counts['medium_confidence']})</option>
    <option value="low">LOW ({counts['low_confidence']})</option>
    <option value="unlined">Unlined / Blank ({counts['unlined_rows']})</option>
  </select>
  <select id="filter-status" aria-label="Filter by status">
    <option value="all">All Origination Statuses</option>
    <option value="originated">Originated ({counts['originated_rows']})</option>
    <option value="unlined">Unlined / Flagged ({counts['unlined_rows']})</option>
  </select>
  <span id="filter-count" class="count-note">Showing {counts['total_rows']} of {counts['total_rows']} verified rows</span>
</div>
{render_match_table(matches, depth=0, show_sport_col=True)}

<div class="section-head">
  <h2>Scope Exclusions Gate ({len(excluded)} Excluded Categories)</h2>
  <p>Explicitly blocked from fixture ingestion and line origination per project instructions.</p>
</div>
<div class="table-wrap">
  <table>
    <thead><tr><th>Category</th><th>Status</th><th>Exclusion Rule</th><th>Reference Hub</th></tr></thead>
    <tbody>{excl_rows}</tbody>
  </table>
</div>
"""
    (SITE / "index.html").write_text(render_shell("Overview & All Matches", "index", index_body, depth=0))

    # 2. High-Confidence Predictions Page (/verified/predictions.html)
    pred_sport_counts: dict[str, int] = {}
    for p in preds:
        pred_sport_counts[p["sport"]] = pred_sport_counts.get(p["sport"], 0) + 1
    pred_sport_opts = "".join(
        f'<option value="{esc(s["slug"])}">{esc(s["name"])} ({pred_sport_counts[s["slug"]]})</option>'
        for s in eligible
        if pred_sport_counts.get(s["slug"])
    )
    preds_body = f"""
<section class="hero">
  <p class="eyebrow">Human Editorial Selection Desk · Strictly Verified Primary Facts</p>
  <h1>High-Confidence Predictions ({len(preds)} Picks)</h1>
  <p>Every <strong>HIGH</strong> pick has a published model probability strictly greater than 70% <em>and</em> a fair American price from -250 through +10000 inclusive. Each carries a unique write-up of at least 30 words with an explicit selection and relevant official form or recent-match evidence. Stronger favourites outside the price band remain Medium.</p>
</section>
<div class="controls">
  <select id="pred-sport-filter" aria-label="Filter predictions by sport">
    <option value="all">All Sports with HIGH Picks ({len(preds)})</option>
    {pred_sport_opts}
  </select>
  <span id="pred-filter-count" class="count-note">Showing {len(preds)} of {len(preds)} HIGH confidence picks</span>
</div>
<div class="pred-list">
  {"".join(render_prediction_card(p, depth=0) for p in preds)}
</div>
"""
    (SITE / "predictions.html").write_text(render_shell("High-Confidence Picks", "predictions", preds_body, depth=0))

    # 3. Flagged for Review Page (/verified/flagged.html)
    audit_rows_html = "".join(
        f'<tr id="{esc(a["id"])}">'
        f'<td class="mono"><strong>{esc(a["id"])}</strong></td>'
        f'<td><span class="pill pill-sev-{esc(a["severity"])}">{esc(a["severity"])}</span></td>'
        f'<td><div><strong>{esc(a["layer"])}</strong></div><div class="mono">{esc(a["file"])}</div></td>'
        f"<td>{esc(a['published'])}</td>"
        f"<td>{esc(a['official'])}</td>"
        f"<td>{esc(a['resolution'])}</td>"
        f'<td><a href="{esc(a["source_url"])}" target="_blank" rel="noopener">{esc(a["source_name"])} ↗</a></td>'
        f"</tr>"
        for a in audits
    )
    gap_rows_html = "".join(
        f'<tr id="{esc(f["id"])}">'
        f'<td class="mono"><strong>{esc(f["id"])}</strong></td>'
        f"<td><strong>{esc(f['sport'])}</strong></td>"
        f"<td>{esc(f['category'])}</td>"
        f"<td>{esc(f['item'])}</td>"
        f"<td>{esc(f['detail'])}</td>"
        f'<td><a href="{esc(f["source_url"])}" target="_blank" rel="noopener">{esc(f["source_name"])} ↗</a></td>'
        f"</tr>"
        for f in flags
    )
    unlined_rows = [m for m in matches if m["line_status"] == "unlined"]
    flagged_body = f"""
<section class="hero">
  <p class="eyebrow">Zero-Inference Integrity Register · Manual Verification Links Included</p>
  <h1>Flagged for Review</h1>
  <p>Every discrepancy uncovered during our line-by-line audit of existing repository files and every match or market field that could not be confirmed server-side from an official trusted governing-body feed is quarantined here for manual review — never guessed, backfilled from third-party sites, or hallucinated.</p>
</section>

<div class="callout-warn">
  <strong>Anti-Hallucination Policy Active:</strong> Across {counts['total_rows']} rows, <strong>{counts['unlined_rows']}</strong> have no originated price because a precise official fixture, final field, or comparable current strength input remains unconfirmed. NBA totals are also blank. Official review links are not represented as factual verification, and raw OLBG date labels are not silently converted to UTC.
</div>

<div class="section-head">
  <h2>1. Existing Repository Irregularities &amp; Audit Findings ({len(audits)} Items)</h2>
  <p>Line-by-line discrepancies verified against primary governing-body endpoints across <code>/</code>, <code>/survey/</code>, and <code>/site/</code>.</p>
</div>
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Severity</th>
        <th>Layer &amp; File</th>
        <th>Published / Existing Repo Value</th>
        <th>Verified Official Primary Value</th>
        <th>Remediation Status</th>
        <th>Manual Review Link</th>
      </tr>
    </thead>
    <tbody>{audit_rows_html}</tbody>
  </table>
</div>

<div class="section-head">
  <h2>2. Upstream Official-Feed Data Gaps ({len(flags)} Categories)</h2>
  <p>Exact reason why specific cells render blank (<code>—</code>) when an official governing-body feed omits or client-renders a required input.</p>
</div>
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Flag ID</th>
        <th>Sport</th>
        <th>Affected Scope</th>
        <th>Blank Fields</th>
        <th>Technical Verification Finding</th>
        <th>Official Source Link</th>
      </tr>
    </thead>
    <tbody>{gap_rows_html}</tbody>
  </table>
</div>

<div class="section-head">
  <h2>3. Unlined &amp; Blank-Field Match Rows ({len(unlined_rows)} Rows)</h2>
  <p>All catalogued cards and futures whose betting lines were intentionally left blank rather than estimated without sufficient official inputs. Some fixtures are confirmed; others remain explicitly pending.</p>
</div>
{render_match_table(unlined_rows, depth=0, show_sport_col=True)}
"""
    (SITE / "flagged.html").write_text(render_shell("Flagged for Review", "flagged", flagged_body, depth=0))

    # 4. Line-by-Line Audit Page (/verified/audit.html)
    audit_body = f"""
<section class="hero">
  <p class="eyebrow">Forensic Repository Review · Historical Baseline Plus Current Refresh</p>
  <h1>Line-by-Line Repository Audit</h1>
  <p>The active verified desk was reviewed against official governing-body sources on <strong>{captured_at}</strong>. RA-01–RA-10 preserve the earlier cross-layer baseline; RA-11–RA-18 record this refresh's taxonomy, stale-event, provenance, confidence, date/time and presentation findings. Overlapping <code>/</code>, <code>/site/</code>, <code>/survey/</code>, <code>/live/</code> and <code>/verified/</code> rows are never summed.</p>
</section>
<div class="sport-grid">
  <div class="card"><h3>Current verified desk</h3><p>{counts['total_rows']} rows, {counts['originated_rows']} originated and {counts['unlined_rows']} unlined. Every row has an official/review URL, discovery state, confirmation state and time basis. See <code>research/verified-refresh-4daa1e65.md</code> for the evidence audit.</p></div>
  <div class="card"><h3>Stale events and taxonomy</h3><p>Expired 21 October events were removed; Basketball now uses OLBG sport ID 4, Golf ID 5, and Rugby League futures use their corrected event IDs. Still-visible expired NBA cards are excluded rather than repriced.</p></div>
  <div class="card"><h3>Coverage and provenance</h3><p>{discovered_count} static OLBG cards and {supplement_count} official supplements are labelled separately. Load More remains unresolved, so exhaustive dynamic coverage is not claimed.</p></div>
  <div class="card"><h3>Historical findings retained</h3><p>Older findings remain visible for manual review even where another session owned or remediated that layer. Their presence in this ledger does not claim a new fix in the current refresh.</p></div>
</div>
<div class="section-head">
  <h2>Complete Audit Ledger ({len(audits)} Findings with Review URLs)</h2>
  <p>Published/existing values, official comparisons and recorded resolutions are preserved line by line.</p>
</div>
<div class="table-wrap">
  <table>
    <thead><tr><th>ID</th><th>Severity</th><th>Layer &amp; File</th><th>Published / Existing Value</th><th>Official Comparison</th><th>Recorded Resolution</th><th>Official / Review Proof</th></tr></thead>
    <tbody>{audit_rows_html}</tbody>
  </table>
</div>
"""
    (SITE / "audit.html").write_text(render_shell("Line-by-Line Repo Audit", "audit", audit_body, depth=0))

    # 5. Methodology Page (/verified/methodology.html)
    meth_body = f"""
<section class="hero">
  <p class="eyebrow">Cleanroom Mathematical Origination &amp; Verification Rules</p>
  <h1>Origination Models, Market Coverage &amp; Confidence Grading</h1>
  <p>Fair probabilities and no-vig decimal prices (<code>1 / p</code>) are computed deterministically in <code>scripts/verified_model.py</code> using only Python's standard library and official-input registers. No bookmaker price, OLBG tipster consensus, or third-party rating enters an equation. The active output contains {counts['originated_rows']} originated rows across {originated_sports} sports and {counts['unlined_rows']} deliberately unlined rows.</p>
</section>
<div class="sport-grid">
  <div class="card"><h3>1. Ice Hockey — 19 Originated Rows</h3><p>Twelve NHL, six SHL and one Liiga fixture use eight-game empirical-Bayes shrinkage of official GF/GA toward a scoring baseline, a Poisson score grid, and a 52% home share of tied regulation outcomes for two-way moneyline. Puck line -1.5/+1.5 and 5.5/6.5 totals are also priced. Liiga's baseline uses only JYP/HPK because a complete current league table was not captured.</p></div>
  <div class="card"><h3>2. Basketball — 23 Originated Rows</h3><p>Fourteen NBA games use ten-game shrinkage of completed official 2025–26 win records, a win-rate logit and normal spread model. Every NBA pick is Medium-capped and every total is blank. HOU@SAS has zero home-court adjustment at neutral Moody Center. Nine current EuroLeague games use three-game PF/PA shrinkage, 3.4-point home advantage, moneyline, spread and totals; expired EuroCup rows are removed.</p></div>
  <div class="card"><h3>3. Rugby Union — 23 Originated Rows</h3><p>Seven Top 14, eight Pro D2 and eight URC Round 4 fixtures use three-match PF/PA shrinkage, 4.2-point home advantage and normal scoring distributions (margin SD 12.6; total SD 14.2). Markets are 1X2 match result, half-point handicap and total points. The Six Nations future remains unlined.</p></div>
  <div class="card"><h3>4. Handball — Five Originated Rows</h3><p>Only the five current EHF Champions League fixtures are priced. Three-match GF/GA shrinkage and a Poisson grid produce 1X2, handicap and total-goal lines. Fifteen other visible domestic/international cards remain unlined pending exact official fixture and ratings confirmation.</p></div>
  <div class="card"><h3>5. Darts — 16 Originated Rows</h3><p>Official PDC ranking prize sums enter a log-ratio leg-strength model; an exact race-to-six distribution prices match winner, leg handicap and 9.5 total legs. PDC inputs are official, while fixture/date labels remain OLBG-sourced. Two outrights are unlined.</p></div>
  <div class="card"><h3>6. Baseball &amp; Motor Racing — Six Originated Rows</h3><p>Three official World Series games use team season run rates in a Poisson model for moneyline, run line and totals. Formula 1 uses official-standing points raised to 1.65 with an explicit 8% residual, a race market, title market, and the actual without-Antonelli market. The US race is 25 October at 16:00 track time; standings retain their stored 21 October capture caveat.</p></div>
  <div class="card"><h3>7. Unlined Markets — {counts['unlined_rows']} Rows</h3><p>Tennis has 20 current cards but zero originated lines; Snooker, Greyhounds, Aussie Rules and eSports have zero active rows. Volleyball, cricket, golf, rugby league and Gaelic football are catalogued with blank markets where exact fixtures, final fields or comparable current official inputs are insufficient. NBA totals and not-applicable outright handicap/total cells are also blank.</p></div>
  <div class="card"><h3>8. Strict High Confidence Gate</h3><p><strong>High requires both:</strong> published <code>p &gt; 0.70</code> and fair American <code>-250 &lt;= odds &lt;= +10000</code>. American prices are derived from the same probability: favourites <code>-100p/(1-p)</code>, underdogs <code>+100(1-p)/p</code>. Exactly 70% is not High; -250 and +10000 are inclusive. High also requires a unique official-fact narrative of at least 30 words.</p></div>
  <div class="card"><h3>9. Medium, Low &amp; Explicit Caps</h3><p>Medium applies from 60% upward when the High gate is not passed, including strong favourites shorter than -250, and to every NBA pick regardless of probability. Low applies below 60%. Each pick stores its fair American price and both gate booleans in <code>matches.json</code>; the table exposes blocked High cases.</p></div>
  <div class="card"><h3>10. Discovery, Dates &amp; Coverage</h3><p>The desk contains {discovered_count} static OLBG-discovered cards and {supplement_count} official supplements. Supplements do not claim OLBG coverage. Relative Today/Tomorrow labels and later golf/futures labels remain raw text unless an official page independently establishes date/time. Load More is unresolved, so this is the fullest supportable static capture—not exhaustive dynamic coverage.</p></div>
</div>
"""
    (SITE / "methodology.html").write_text(render_shell("Methodology & Models", "methodology", meth_body, depth=0))

    # 6. All 17 Sport Subpages (/verified/sports/<slug>.html)
    for s in eligible:
        s_rows = by_sport[s["slug"]]
        s_preds = preds_by_sport[s["slug"]]
        mkts = ", ".join(s["markets_investigated"])
        pred_section = (
            f'<div class="section-head"><h2>High-Confidence Human Predictions — {esc(s["name"])} ({len(s_preds)})</h2></div>'
            f'<div class="pred-list">{"".join(render_prediction_card(p, depth=1) for p in s_preds)}</div>'
            if s_preds
            else ""
        )
        rows_section = (
            render_match_table(s_rows, depth=1, show_sport_col=False)
            if s_rows
            else f'<div class="callout-warn">The live OLBG hub displayed <strong>No tips found</strong> on {captured_at}; zero active rows are published rather than substitutes.</div>'
        )
        sp_body = f"""
<p style="margin:0 0 0.75rem;font-size:0.85rem;"><a href="../index.html">← Back to All 17 Eligible Sports</a></p>
<section class="hero">
  <p class="eyebrow">{esc(s['governing_body'])} · Verified Category Subpage</p>
  <h1>{esc(s['name'])} — Fixtures, Originated Lines &amp; Sources</h1>
  <p>{esc(s['status_summary'])}</p>
  <p style="margin-top:0.65rem;font-size:0.85rem;">
    <strong>Markets Investigated:</strong> {esc(mkts)} ·
    <a href="{esc(s['official_url'])}" target="_blank" rel="noopener">Official Governing-Body Source ↗</a> ·
    <a href="{esc(s['olbg_url'])}" target="_blank" rel="noopener">OLBG {esc(s['name'])} Hub ↗</a>
  </p>
</section>
{pred_section}
<div class="section-head">
  <h2>Catalogued {esc(s['name'])} Schedule &amp; Originated Lines ({len(s_rows)} Rows)</h2>
  <p>Every row carries an official or explicitly labelled review link plus provenance. Unconfirmed cells render as <code>—</code>.</p>
</div>
{rows_section}
"""
        (SITE / "sports" / f"{s['slug']}.html").write_text(
            render_shell(f"{s['name']} Lines & Audit", "", sp_body, depth=1)
        )

    print(
        f"verified_build: built 5 core HTML pages + {len(eligible)} sport pages "
        f"({counts['total_rows']} rows, {len(preds)} HIGH predictions)"
    )


if __name__ == "__main__":
    main()
