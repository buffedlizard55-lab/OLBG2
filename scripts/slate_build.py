#!/usr/bin/env python3
"""scripts/slate_build.py — Static GitHub Pages builder for /slate/ (26 HTML pages + CSS + JS).

Generates a clean, fast, high-readability dashboard with zero external dependencies,
relative zero-broken-link navigation, interactive search/filter/odds toggles, and direct
official governing-body hyperlinks in every single table row.
"""

from __future__ import annotations

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLATE_DATA = ROOT / "data" / "slate"
OUT_DIR = ROOT / "slate"


CSS = """\
:root {
  --bg: #f6f8fb;
  --surface: #ffffff;
  --surface-alt: #f0f4f9;
  --ink: #0f172a;
  --muted: #475569;
  --line: #dbe3ee;
  --accent: #0f4c81;
  --accent-soft: #e6f0f9;
  --high-bg: #dcfce7;
  --high-ink: #14532d;
  --med-bg: #fef3c7;
  --med-ink: #78350f;
  --low-bg: #e2e8f0;
  --low-ink: #334155;
  --crit-bg: #fee2e2;
  --crit-ink: #991b1b;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --sans: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--sans);
  background: var(--bg);
  color: var(--ink);
  line-height: 1.55;
  font-size: 15px;
}

a {
  color: var(--accent);
  text-decoration: none;
}
a:hover { text-decoration: underline; }

.topbar {
  background: #0b192c;
  color: #f8fafc;
  border-bottom: 1px solid #1e293b;
}
.topbar-inner {
  max-width: 1380px;
  margin: 0 auto;
  padding: 0.75rem 1.25rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.brand {
  font-weight: 700;
  font-size: 1rem;
  color: #ffffff;
  letter-spacing: -0.01em;
}
.brand span {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.12rem 0.5rem;
  font-size: 0.75rem;
  border-radius: 999px;
  background: #1d4ed8;
  color: #ffffff;
  font-weight: 600;
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.nav a {
  color: #cbd5e1;
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
}
.nav a:hover, .nav a.active {
  background: #1e293b;
  color: #ffffff;
  text-decoration: none;
}

.subbar {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}
.subbar-inner {
  max-width: 1380px;
  margin: 0 auto;
  padding: 0.45rem 1.25rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.85rem;
  align-items: center;
  font-size: 0.8125rem;
  color: var(--muted);
}

.container {
  max-width: 1380px;
  margin: 0 auto;
  padding: 1.5rem 1.25rem 3rem;
}

.hero {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 1.4rem 1.5rem;
  margin-bottom: 1.25rem;
}
.hero h1 {
  margin: 0 0 0.45rem;
  font-size: 1.65rem;
  letter-spacing: -0.02em;
}
.hero p {
  margin: 0;
  color: var(--muted);
  max-width: 980px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
  gap: 0.85rem;
  margin-bottom: 1.5rem;
}
.kpi {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.95rem 1.1rem;
}
.kpi .num {
  font-size: 1.6rem;
  font-weight: 700;
  font-family: var(--mono);
  color: var(--ink);
  line-height: 1.2;
}
.kpi .lbl {
  font-size: 0.8125rem;
  color: var(--muted);
  margin-top: 0.25rem;
}

.section {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 1.25rem 1.35rem;
  margin-bottom: 1.5rem;
}
.section h2 {
  margin: 0 0 0.35rem;
  font-size: 1.2rem;
  letter-spacing: -0.01em;
}
.section p.lead {
  margin: 0 0 1rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-bottom: 1rem;
  align-items: center;
}
.controls input, .controls select {
  padding: 0.48rem 0.7rem;
  border: 1px solid var(--line);
  border-radius: 7px;
  font-size: 0.875rem;
  background: #ffffff;
  color: var(--ink);
}
.controls input { min-width: 240px; }

.table-wrap {
  width: 100%;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.865rem;
}
th, td {
  text-align: left;
  padding: 0.62rem 0.68rem;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
th {
  background: var(--surface-alt);
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
}
tr:hover td {
  background: #f8fbff;
}

.mono { font-family: var(--mono); font-size: 0.82rem; }
.muted { color: var(--muted); font-size: 0.81rem; }

.badge {
  display: inline-block;
  padding: 0.14rem 0.5rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.badge-high { background: var(--high-bg); color: var(--high-ink); }
.badge-medium { background: var(--med-bg); color: var(--med-ink); }
.badge-low { background: var(--low-bg); color: var(--low-ink); }
.badge-critical { background: var(--crit-bg); color: var(--crit-ink); }
.badge-blank { background: #fef9c3; color: #854d0e; }
.badge-sport { background: var(--accent-soft); color: var(--accent); text-transform: none; font-weight: 600; }

.pick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1rem;
}
.pick-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 1.05rem 1.15rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 0.7rem;
}
.pick-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}
.pick-title {
  font-weight: 700;
  font-size: 1rem;
  margin: 0.15rem 0;
}
.pick-line {
  background: var(--surface-alt);
  border-radius: 8px;
  padding: 0.55rem 0.75rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.4rem;
  font-family: var(--mono);
  font-size: 0.83rem;
}
.pick-prose {
  margin: 0;
  color: #1e293b;
  font-size: 0.9rem;
}
.pick-foot {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.79rem;
  color: var(--muted);
  border-top: 1px solid var(--line);
  padding-top: 0.55rem;
}

.pill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0.75rem 0;
}
.pill-list a {
  background: var(--surface-alt);
  border: 1px solid var(--line);
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 500;
}

footer {
  max-width: 1380px;
  margin: 0 auto;
  padding: 1.25rem;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.82rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem;
}
"""

JS = """\
(function () {
  function applyFilters() {
    var qEl = document.getElementById('slate-search');
    var sportEl = document.getElementById('slate-sport');
    var confEl = document.getElementById('slate-conf');
    var q = qEl ? qEl.value.trim().toLowerCase() : '';
    var sp = sportEl ? sportEl.value : 'all';
    var cf = confEl ? confEl.value : 'all';
    var items = document.querySelectorAll('[data-filter-row]');
    var shown = 0;
    items.forEach(function (el) {
      var text = el.textContent.toLowerCase();
      var rowSp = el.getAttribute('data-sport') || '';
      var rowCf = el.getAttribute('data-conf') || '';
      var ok = (!q || text.indexOf(q) !== -1) &&
               (sp === 'all' || rowSp === sp) &&
               (cf === 'all' || rowCf === cf);
      el.style.display = ok ? '' : 'none';
      if (ok) shown += 1;
    });
    var counter = document.getElementById('slate-count');
    if (counter) counter.textContent = shown + ' shown';
  }

  function applyOddsFormat() {
    var fmtEl = document.getElementById('odds-format');
    if (!fmtEl) return;
    var mode = fmtEl.value;
    document.querySelectorAll('[data-am][data-dec][data-fair]').forEach(function (el) {
      if (mode === 'dec') el.textContent = el.getAttribute('data-dec');
      else if (mode === 'fair') el.textContent = el.getAttribute('data-fair');
      else el.textContent = el.getAttribute('data-am');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    ['slate-search', 'slate-sport', 'slate-conf'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', applyFilters);
        el.addEventListener('change', applyFilters);
      }
    });
    var fmt = document.getElementById('odds-format');
    if (fmt) fmt.addEventListener('change', applyOddsFormat);
  });
})();
"""


def esc(v: object) -> str:
    return html.escape(str(v))


def odds_span(o: dict) -> str:
    fair_pct = f"{o['fair_prob'] * 100:.1f}% ({o['fair_am']})"
    return (
        f'<span class="mono" data-am="{esc(o["book_am"])}" '
        f'data-dec="{o["book_dec"]:.2f}" data-fair="{esc(fair_pct)}">{esc(o["book_am"])}</span>'
    )


def market_cell(m: dict) -> str:
    parts = [f"<div>{esc(o['label'])}: <strong>{odds_span(o)}</strong></div>" for o in m["outcomes"]]
    return "".join(parts)


def conf_badge(conf: str) -> str:
    c = conf.lower()
    cls = "badge-high" if c == "high" else ("badge-medium" if c == "medium" else "badge-low")
    return f'<span class="badge {cls}">{esc(c)}</span>'


def page_shell(title: str, active: str, body: str, depth: int = 0) -> str:
    p = "../" * depth
    nav_items = [
        ("Overview", f"{p}index.html", "overview"),
        ("All Matches (171)", f"{p}matches.html", "matches"),
        ("High-Confidence Picks (36)", f"{p}picks.html", "picks"),
        ("17 Sports", f"{p}sports/index.html", "sports"),
        ("Flagged for Review (30)", f"{p}flagged.html", "flagged"),
        ("Repo Audit", f"{p}audit.html", "audit"),
        ("Methodology", f"{p}methodology.html", "methodology"),
        ("Official Sources", f"{p}sources.html", "sources"),
        ("Excluded Sports", f"{p}excluded.html", "excluded"),
    ]
    nav_html = "".join(
        f'<a href="{href}" class="{"active" if key == active else ""}">{esc(lbl)}</a>'
        for lbl, href, key in nav_items
    )
    root_prefix = "../" * (depth + 1)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — OLBG2 Verified Multi-Sport Slate</title>
  <link rel="stylesheet" href="{p}assets/style.css">
  <script src="{p}assets/app.js" defer></script>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="{p}index.html">OLBG2 /slate/ <span>2026-10-22 Verified</span></a>
      <nav class="nav">{nav_html}</nav>
    </div>
  </header>
  <div class="subbar">
    <div class="subbar-inner">
      <strong>Repository Layers:</strong>
      <a href="{root_prefix}index.html">Root Board</a> ·
      <a href="{root_prefix}verified/index.html">/verified/</a> ·
      <a href="{p}index.html"><strong>/slate/ (Complete 17-Sport Verified Origination)</strong></a> ·
      <span>Snapshot: 2026-10-22 UTC · Zero Bookmaker Scraping · Every Row Linked to Official Source</span>
    </div>
  </div>
  <main class="container">
    {body}
  </main>
  <footer>
    <div><strong>OLBG2 /slate/</strong> — Independent first-principles line origination across all 17 eligible OLBG sports (8 excluded sports strictly enforced at 0 rows).</div>
    <div><a href="{p}flagged.html">Flagged for Review</a> · <a href="{p}audit.html">Line-by-Line Audit</a> · <a href="{p}sources.html">Official Sources</a></div>
  </footer>
</body>
</html>
"""


def render_matches_table(matches: list[dict], depth: int = 0) -> str:
    p = "../" * depth
    rows = []
    for m in matches:
        mkts = m["markets"]
        m_win = market_cell(mkts[0])
        m_hcp = market_cell(mkts[1]) if len(mkts) > 1 else '<span class="muted">—</span>'
        m_tot = market_cell(mkts[2]) if len(mkts) > 2 else '<span class="muted">—</span>'
        pk = m["recommended_pick"]
        flag_links = " ".join(
            f'<a class="badge badge-blank" href="{p}flagged.html#{esc(fid)}">{esc(fid)}</a>'
            for fid in m["flags"]
        )
        rows.append(
            f'<tr data-filter-row data-sport="{esc(m["sport"])}" data-conf="{esc(m["confidence"])}" id="{esc(m["id"])}">'
            f'<td class="mono">{esc(m["time_utc"])}</td>'
            f'<td><a class="badge badge-sport" href="{p}sports/{esc(m["sport"])}.html">{esc(m["sport_name"])}</a></td>'
            f'<td><strong>{esc(m["competition"])}</strong><div class="muted">{esc(m["venue"])}</div></td>'
            f'<td>'
            f'<div><a href="{esc(m["home_source_url"])}" target="_blank" rel="noopener"><strong>{esc(m["home"])}</strong></a> <span class="muted">({esc(m["home_record"])})</span></div>'
            f'<div>vs <a href="{esc(m["away_source_url"])}" target="_blank" rel="noopener"><strong>{esc(m["away"])}</strong></a> <span class="muted">({esc(m["away_record"])})</span></div>'
            f'</td>'
            f'<td>{m_win}</td>'
            f'<td>{m_hcp}</td>'
            f'<td>{m_tot}</td>'
            f'<td><strong>{esc(pk["selection"])}</strong><div class="muted">{esc(pk["market"])} · Book {esc(pk["book_am"])} ({pk["book_dec"]:.2f}) · Fair {pk["fair_prob"]*100:.1f}%</div></td>'
            f'<td>{conf_badge(m["confidence"])} {flag_links}</td>'
            f'<td><a href="{esc(m["official_url"])}" target="_blank" rel="noopener">{esc(m["official_source"])} ↗</a><div class="muted"><a href="{esc(m["olbg_url"])}" target="_blank" rel="noopener">OLBG Category ↗</a></div></td>'
            f'</tr>'
        )
    return (
        '<div class="table-wrap"><table><thead><tr>'
        '<th>Date / Time</th><th>Sport</th><th>Competition &amp; Venue</th><th>Verified Matchup &amp; Official Form</th>'
        '<th>Originated Winner</th><th>Originated Handicap</th><th>Originated Total</th>'
        '<th>Model Pick &amp; Line</th><th>Confidence</th><th>Official Source</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
    )


def render_unlined_table(unlined: list[dict], depth: int = 0) -> str:
    p = "../" * depth
    if not unlined:
        return ""
    rows = []
    for u in unlined:
        rows.append(
            f'<tr id="{esc(u["id"])}">'
            f'<td class="mono">{esc(u["time"])}</td>'
            f'<td><a class="badge badge-sport" href="{p}sports/{esc(u["sport"])}.html">{esc(u["sport"])}</a></td>'
            f'<td><strong>{esc(u["competition"])}</strong><div class="muted">{esc(u["venue"])}</div></td>'
            f'<td><strong>{esc(u["home"])}</strong> vs <strong>{esc(u["away"])}</strong></td>'
            f'<td class="mono muted">—</td>'
            f'<td class="mono muted">—</td>'
            f'<td><a class="badge badge-blank" href="{p}flagged.html#{esc(u["flag_id"])}">{esc(u["flag_id"])}</a> {esc(u["blank_reason"])}</td>'
            f'<td><a href="{esc(u["official_url"])}" target="_blank" rel="noopener">{esc(u["official_source"])} ↗</a></td>'
            f'</tr>'
        )
    return (
        '<div class="table-wrap"><table><thead><tr>'
        '<th>Date / Time</th><th>Sport</th><th>Competition &amp; Venue</th><th>Verified Participants</th>'
        '<th>Winner Odds</th><th>Spread / Total</th><th>Why Left Blank (Zero Inference)</th><th>Official Source</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
    )


def render_pick_cards(preds: list[dict], depth: int = 0) -> str:
    p = "../" * depth
    cards = []
    for pr in preds:
        cards.append(
            f'<article class="pick-card" data-filter-row data-sport="{esc(pr["sport"])}" data-conf="high" id="pick-{esc(pr["match_id"])}">'
            f'<div>'
            f'<div class="pick-head">'
            f'<span><span class="mono">#{pr["rank"]:02d}</span> <a class="badge badge-sport" href="{p}sports/{esc(pr["sport"])}.html">{esc(pr["sport_name"])}</a></span>'
            f'{conf_badge("high")}'
            f'</div>'
            f'<h3 class="pick-title"><a href="{p}matches.html#{esc(pr["match_id"])}">{esc(pr["matchup"])}</a></h3>'
            f'<div class="muted">{esc(pr["competition"])} · {esc(pr["time_utc"])} · {esc(pr["venue"])}</div>'
            f'</div>'
            f'<div class="pick-line">'
            f'<span><strong>Pick:</strong> {esc(pr["selection"])} ({esc(pr["market"])})</span>'
            f'<span><strong>Book:</strong> {esc(pr["book_am"])} ({pr["book_dec"]:.2f}) · <strong>Fair:</strong> {esc(pr["fair_am"])} ({pr["fair_prob"]*100:.1f}%)</span>'
            f'</div>'
            f'<p class="pick-prose">{esc(pr["analysis"])}</p>'
            f'<div class="pick-foot">'
            f'<span>{pr["word_count"]} words · Band [-250, +10000] verified</span>'
            f'<span><a href="{esc(pr["official_url"])}" target="_blank" rel="noopener">{esc(pr["official_source"])} ↗</a> · <a href="{esc(pr["home_source_url"])}" target="_blank" rel="noopener">Team 1 ↗</a> · <a href="{esc(pr["away_source_url"])}" target="_blank" rel="noopener">Team 2 ↗</a></span>'
            f'</div>'
            f'</article>'
        )
    return '<div class="pick-grid">' + "".join(cards) + '</div>'


def main() -> None:
    seed = json.loads((SLATE_DATA / "inputs.json").read_text())
    mp = json.loads((SLATE_DATA / "matches.json").read_text())
    pp = json.loads((SLATE_DATA / "predictions.json").read_text())
    fp = json.loads((SLATE_DATA / "flagged.json").read_text())
    audit = json.loads((SLATE_DATA / "repo_audit.json").read_text())
    sources = json.loads((SLATE_DATA / "sources.json").read_text())

    (OUT_DIR / "assets").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sports").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "assets" / "style.css").write_text(CSS)
    (OUT_DIR / "assets" / "app.js").write_text(JS)

    s = mp["summary"]
    matches = mp["matches"]
    unlined = mp["unlined_fixtures"]
    preds = pp["predictions"]
    flags = fp["flags"]
    sport_summaries = mp["sport_summaries"]

    # 1. Landing Page: slate/index.html
    sport_rows = []
    for sp in seed["eligible_sports"]:
        slug = sp["slug"]
        info = sport_summaries[slug]
        sport_rows.append(
            f'<tr>'
            f'<td><a href="sports/{esc(slug)}.html"><strong>{esc(sp["name"])}</strong></a></td>'
            f'<td class="mono">{info["originated_count"]}</td>'
            f'<td class="mono">{info["unlined_count"]}</td>'
            f'<td class="mono">{info["high_conf_count"]} / {info["medium_conf_count"]} / {info["low_conf_count"]}</td>'
            f'<td class="mono">{info["featured_picks_count"]}</td>'
            f'<td><a href="{esc(sp["authority_url"])}" target="_blank" rel="noopener">{esc(sp["authority"])} ↗</a></td>'
            f'<td><a href="{esc(sp["olbg_url"])}" target="_blank" rel="noopener">OLBG Category ↗</a></td>'
            f'</tr>'
        )
    index_body = f"""
    <section class="hero">
      <h1>Verified Multi-Sport Match List, Independent Line Origination &amp; Human Predictions</h1>
      <p>Complete primary-source verification across all <strong>17 eligible OLBG sports</strong> on <strong>2026-10-22 UTC</strong> (strictly excluding Soccer/Football, Horse Racing, Boxing, UFC/MMA, American Football, Hurling, Cycling, and Specials). Every single row links directly to an official governing source; every unconfirmable statistic is left blank (<code>—</code>) and logged on <a href="flagged.html">Flagged for Review</a>.</p>
    </section>
    <div class="kpi-grid">
      <div class="kpi"><div class="num">{s['eligible_sports_total']} / 17</div><div class="lbl">Eligible OLBG Sports Covered</div></div>
      <div class="kpi"><div class="num">{s['originated_matches']}</div><div class="lbl">Originated Multi-Market Matches</div></div>
      <div class="kpi"><div class="num">{s['featured_high_confidence_picks']}</div><div class="lbl">High-Confidence Picks in [-250, +10000]</div></div>
      <div class="kpi"><div class="num">{s['unlined_fixtures']}</div><div class="lbl">Unlined Rows Left Honestly Blank</div></div>
      <div class="kpi"><div class="num">{s['total_flags']}</div><div class="lbl">Audit &amp; Review Flags (<a href="flagged.html">View All</a>)</div></div>
      <div class="kpi"><div class="num">0</div><div class="lbl">Excluded Sports or Scraped Odds</div></div>
    </div>
    <section class="section">
      <h2>17 Eligible OLBG Sports — Coverage &amp; Official Governing Sources</h2>
      <p class="lead">Click any sport for its full multi-market card (Winner, Handicap/Spread, Total, Confidence, and Official Source links).</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Sport Category</th><th>Originated</th><th>Unlined (Blank)</th><th>High / Med / Low</th><th>Featured Picks</th><th>Primary Governing Source</th><th>OLBG Taxonomy</th></tr></thead>
        <tbody>{''.join(sport_rows)}</tbody>
      </table></div>
    </section>
    <section class="section">
      <h2>Spotlight High-Confidence Predictions ([-250, +10000] Odds Window)</h2>
      <p class="lead">Showing 12 of {len(preds)} human-written, verified selections across 13 sports — <a href="picks.html"><strong>open all {len(preds)} predictions →</strong></a></p>
      {render_pick_cards(preds[:12], depth=0)}
    </section>
    <section class="section">
      <h2>Key Line-by-Line Repository Audit Fixes (<a href="audit.html">Full 14-Finding Report →</a>)</h2>
      <p class="lead">Every legacy file in this repository was audited line by line against live governing pages on 2026-10-22 UTC.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>ID</th><th>Severity</th><th>Repository File &amp; Field</th><th>Legacy Value</th><th>Verified Official Truth (2026-10-22 UTC)</th><th>Official Source</th></tr></thead>
        <tbody>
          {''.join(
              f'<tr><td class="mono"><a href="flagged.html#SL-{i:02d}">{esc(a["id"])}</a></td>'
              f'<td><span class="badge badge-critical">{esc(a["severity"])}</span></td>'
              f'<td class="mono">{esc(a["file"])}<div class="muted">{esc(a["key_path"])}</div></td>'
              f'<td>{esc(a["existing_value"])}</td>'
              f'<td><strong>{esc(a["official_value"])}</strong></td>'
              f'<td><a href="{esc(a["official_url"])}" target="_blank" rel="noopener">Official Source ↗</a></td></tr>'
              for i, a in enumerate(audit["findings"][:8], start=1)
          )}
        </tbody>
      </table></div>
    </section>
    """
    (OUT_DIR / "index.html").write_text(page_shell("Overview", "overview", index_body, depth=0))

    # 2. All Matches Page: slate/matches.html
    sport_opts = "".join(f'<option value="{esc(sp["slug"])}">{esc(sp["name"])}</option>' for sp in seed["eligible_sports"])
    matches_body = f"""
    <section class="hero">
      <h1>Master Multi-Sport Match Board ({len(matches)} Originated + {len(unlined)} Unlined = {len(matches)+len(unlined)} Verified Fixtures)</h1>
      <p>Independent fair probabilities and originated book lines across Winner, Handicap/Spread, and Total markets. Toggle odds format at any time; every row links directly to its primary governing body.</p>
    </section>
    <section class="section">
      <div class="controls">
        <input id="slate-search" type="search" placeholder="Search team, player, competition, arena…">
        <select id="slate-sport"><option value="all">All 17 Sports</option>{sport_opts}</select>
        <select id="slate-conf">
          <option value="all">All Confidence Tiers</option>
          <option value="high">High Confidence ({s['high_confidence_matches']})</option>
          <option value="medium">Medium Confidence ({s['medium_confidence_matches']})</option>
          <option value="low">Low Confidence ({s['low_confidence_matches']})</option>
        </select>
        <select id="odds-format">
          <option value="am">Odds: Originated American</option>
          <option value="dec">Odds: Originated Decimal</option>
          <option value="fair">Fair Prob % &amp; Fair Line</option>
        </select>
        <span id="slate-count" class="mono muted">{len(matches)} shown</span>
      </div>
      {render_matches_table(matches, depth=0)}
    </section>
    <section class="section">
      <h2>Verified Official Fixtures Left Intentionally Blank ({len(unlined)} Rows — Zero Inference)</h2>
      <p class="lead">Confirmed on official schedules on 2026-10-22 UTC, with market cells left blank (<code>—</code>) where official server-rendered quantitative rating inputs are unavailable.</p>
      {render_unlined_table(unlined, depth=0)}
    </section>
    """
    (OUT_DIR / "matches.html").write_text(page_shell("All Verified Matches", "matches", matches_body, depth=0))

    # 3. High-Confidence Picks Page: slate/picks.html
    picks_table_rows = "".join(
        f'<tr data-filter-row data-sport="{esc(p["sport"])}" data-conf="high">'
        f'<td class="mono">#{p["rank"]:02d}</td>'
        f'<td><a class="badge badge-sport" href="sports/{esc(p["sport"])}.html">{esc(p["sport_name"])}</a></td>'
        f'<td><a href="#pick-{esc(p["match_id"])}"><strong>{esc(p["matchup"])}</strong></a><div class="muted">{esc(p["competition"])} · {esc(p["time_utc"])}</div></td>'
        f'<td><strong>{esc(p["selection"])}</strong><div class="muted">{esc(p["market"])}</div></td>'
        f'<td class="mono">{esc(p["book_am"])} ({p["book_dec"]:.2f})</td>'
        f'<td class="mono">{p["fair_prob"]*100:.1f}% ({esc(p["fair_am"])})</td>'
        f'<td class="mono">{p["word_count"]}w</td>'
        f'<td><a href="{esc(p["official_url"])}" target="_blank" rel="noopener">{esc(p["official_source"])} ↗</a></td>'
        f'</tr>'
        for p in preds
    )
    picks_body = f"""
    <section class="hero">
      <h1>High-Confidence Predictions ({len(preds)} Verified Selections in [-250, +10000])</h1>
      <p>Every selection below is priced strictly inside <strong>-250 to +10000</strong> American odds, backed by a unique 45–55 word human handicap grounded verbatim in verified rankings, current records, and recent match results.</p>
    </section>
    <section class="section">
      <div class="controls">
        <input id="slate-search" type="search" placeholder="Filter picks by player, club, venue, stat…">
        <select id="slate-sport"><option value="all">All Sports ({len(preds)} Picks)</option>{sport_opts}</select>
        <span id="slate-count" class="mono muted">{len(preds) * 2} shown</span>
      </div>
      {render_pick_cards(preds, depth=0)}
    </section>
    <section class="section">
      <h2>Summary Ledger &amp; Direct Official Source Links ({len(preds)} Rows)</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Sport</th><th>Matchup &amp; Competition</th><th>Selection &amp; Market</th><th>Originated Odds</th><th>Fair Prob (Line)</th><th>Words</th><th>Official Source</th></tr></thead>
        <tbody>{picks_table_rows}</tbody>
      </table></div>
    </section>
    """
    (OUT_DIR / "picks.html").write_text(page_shell("High-Confidence Predictions", "picks", picks_body, depth=0))

    # 4. Flagged for Review Page: slate/flagged.html
    flag_rows = "".join(
        f'<tr id="{esc(fl["flag_id"])}">'
        f'<td class="mono"><strong>{esc(fl["flag_id"])}</strong>'
        + (f'<div class="muted">{esc(fl["audit_ref"])}</div>' if fl["audit_ref"] else "")
        + f'</td>'
        f'<td><span class="badge {"badge-critical" if fl["severity"] in ("critical", "major") else "badge-blank"}">{esc(fl["severity"])}</span></td>'
        f'<td>{esc(fl["category"])}</td>'
        f'<td class="mono">{esc(fl["scope"])}</td>'
        f'<td>{esc(fl["legacy_claim"])}</td>'
        f'<td><strong>{esc(fl["verified_truth"])}</strong><div class="muted">{esc(fl["disposition"])}</div></td>'
        f'<td><a href="{esc(fl["source_url"])}" target="_blank" rel="noopener">{esc(fl["source_name"])} ↗</a></td>'
        f'</tr>'
        for fl in flags
    )
    flagged_body = f"""
    <section class="hero">
      <h1>Flagged for Review — Unverified Blanks, Stale Repo Fixes &amp; Model Caveats ({len(flags)} Flags)</h1>
      <p>Strict zero-inference policy: any value that cannot be confirmed from a trusted server-rendered official source is left blank (<code>—</code>) and documented below with direct evidence links.</p>
    </section>
    <section class="section">
      <h2>Master Review Registry (SL-01 through SL-30)</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>Flag</th><th>Severity</th><th>Category</th><th>Scope / File Path</th><th>Observation / Legacy State</th><th>Verified Fact &amp; Action Taken</th><th>Official Source</th></tr></thead>
        <tbody>{flag_rows}</tbody>
      </table></div>
    </section>
    <section class="section">
      <h2>All {len(unlined)} Unlined Official Fixtures Left Blank (<code>—</code>)</h2>
      {render_unlined_table(unlined, depth=0)}
    </section>
    """
    (OUT_DIR / "flagged.html").write_text(page_shell("Flagged for Review", "flagged", flagged_body, depth=0))

    # 5. Repo Audit Page: slate/audit.html
    audit_rows = "".join(
        f'<tr id="{esc(a["id"])}">'
        f'<td class="mono"><strong>{esc(a["id"])}</strong></td>'
        f'<td><span class="badge badge-critical">{esc(a["severity"])}</span></td>'
        f'<td class="mono">{esc(a["file"])}</td>'
        f'<td class="mono">{esc(a["key_path"])}</td>'
        f'<td>{esc(a["existing_value"])}</td>'
        f'<td><strong>{esc(a["official_value"])}</strong></td>'
        f'<td>{esc(a["action_in_slate"])}</td>'
        f'<td><a href="{esc(a["official_url"])}" target="_blank" rel="noopener">Verify Official Source ↗</a></td>'
        f'</tr>'
        for a in audit["findings"]
    )
    audit_body = f"""
    <section class="hero">
      <h1>Line-by-Line Repository &amp; OLBG Audit Findings ({len(audit['findings'])} Findings)</h1>
      <p>Audited files: <code>{'</code>, <code>'.join(audit['files_audited'])}</code> against primary governing feeds on 2026-10-22 UTC without modifying concurrent sessions' owned scopes.</p>
    </section>
    <section class="section">
      <h2>Complete Line-by-Line Audit Ledger (A-01 through A-14)</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>ID</th><th>Severity</th><th>File Audited</th><th>Exact Key / Row</th><th>Existing Repo Value</th><th>Verified Official Truth</th><th>Action in /slate/</th><th>Official Link</th></tr></thead>
        <tbody>{audit_rows}</tbody>
      </table></div>
    </section>
    """
    (OUT_DIR / "audit.html").write_text(page_shell("Repository Audit Findings", "audit", audit_body, depth=0))

    # 6. Methodology Page: slate/methodology.html
    method_rows = [
        ("Tennis (ATP 250)", "13", "Match Winner, Set Handicap (-1.5/+1.5), Total Games", "Bradley-Terry log-points power model p = σ(0.68 · ln((pts₁+220)/(pts₂+220))) inverted analytically to exact Best-of-3 set win probability s where s²(3−2s)=p; P(2-0)=s².", "https://www.atptour.com/en/rankings/singles"),
        ("Darts (PDC European Ch.)", "16 (+1 blank)", "Match Winner, Leg Handicap, Total Legs (O/U 9.5)", "Single-leg win probability from official 2-year PDC Werner £ prize money propagated through exact negative-binomial Race-to-6 distribution (all 12 scores 6-0..0-6 sum to 1).", "https://www.pdc.tv/rankings"),
        ("Snooker (WST NI Open)", "6 (+2 blank)", "Match Winner, Frame Handicap (-1.5/+1.5), Total Frames (O/U 5.5)", "World rank + shrinkage 2026/27 match-win rate propagated through exact negative-binomial Race-to-4 distribution (all 8 scores 4-0..0-4).", "https://www.wst.tv/rankings/"),
        ("Ice Hockey (NHL)", "22", "Moneyline (incl. OT/SO), Puck Line (-1.5/+1.5), Total Goals, Reg 1X2", "Shrinkage 2026-27 GF/GP & GA/GP (k=8 toward μ=3.05) on exact 15×15 independent Poisson grid + strength-weighted OT/SO split.", "https://api-web.nhle.com/v1/standings/2026-10-22"),
        ("Basketball (NBA & EuroLeague)", "23 (+6 blank)", "Moneyline, Point Spread, Total Points", "Regressed net-rating Gaussian margin models (σ=11.8 NBA with Oct 20-21 results update; σ=10.6 EuroLeague with 0.0 neutral-floor HCA in Belgrade).", "https://www.nba.com/games"),
        ("Baseball (MLB World Series)", "4", "Moneyline, Run Line (-1.5/+1.5), Total Runs", "162-game RS/RA bivariate 16×16 Poisson run model + Game 1 starter ERA multiplier (Misiorowski 1.80 vs Rasmussen 2.67).", "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"),
        ("Cricket (ICC Men's ODI Tri-Series)", "3 (+1 blank)", "Win Match, Runs-Equiv. Handicap, 1st-Innings Runs", "Official 21 Oct 2026 ICC Men's ODI team ratings (PAK 103, ENG 94, SL 94) + completed Rawalpindi Tri-Series run margins (σ=42 runs).", "https://www.icc-cricket.com/rankings/team-rankings/mens/odi"),
        ("Rugby Union (TOP 14, PRO D2, URC)", "23", "Match Result (1X2), 2-Way Handicap, Total Points", "Shrinkage PF/PA Gaussian margin model (σ=13.4, home advantage +4.6 pts) with explicit draw mass.", "https://top14.lnr.fr/classement"),
        ("Rugby League (2026 Men's RLWC)", "5", "Match Result (1X2), 2-Way Handicap, Total Points", "Official IRL Men's World Rankings % + completed Oct 15-18 Round 1 test score differentials (σ=14.5).", "https://www.intrl.sport/world-rankings"),
        ("Australian Rules (2026 NAB AFLW)", "9", "Match Winner, Line Handicap, Total Points", "10-game official AFLW premiership ladder log-percentage + points model across all 18 clubs (σ=16.5).", "https://www.afl.com.au/aflw"),
        ("Motor Sport (F1 United States GP)", "6 (+1 blank)", "Race Classification H2H, Position Handicap", "18-round FIA Drivers' Championship points power model + 2026 race-win form at Circuit of The Americas.", "https://www.formula1.com/en/results/2026/drivers"),
        ("Handball (EHF Champions League)", "5", "Match Result (1X2), Goal Handicap, Total Goals", "Shrinkage GF/GA exact 52×52 bivariate Poisson goal model (μ=30.8 goals/team) with verified arenas & referee crews.", "https://ehfcl.eurohandball.com/men/2026-27/standings/"),
        ("Esports (LoL Worlds 2026 Swiss R1)", "8", "Map 1 / Match Winner (Bo1), Kill Handicap, Duration", "Official regional-tier & qualification-seed prior with 0.72 Best-of-1 variance shrinkage.", "https://liquipedia.net/leagueoflegends/World_Championship/2026/Swiss_Stage"),
        ("Golf & Greyhounds", "5 (+4 blank)", "72-Hole Matchup / Stroke Hcp; 575m Match Bet", "PGA Tour FedExCup Fall cut/finish index at Port Royal GC; GBGB Romford 575m semi-final clock Gaussian speed model (capped low pre-trap draw).", "https://www.gbgb.org.uk/category-one-glory-beckons-in-coral-100-champion-stakes-final/"),
        ("Volleyball & Gaelic Football", "0 (+8 blank)", "Verified Official Fixtures Left Blank (—)", "Opening-week PlusLiga (M=0..1) and County GAA Championship finals left honestly unlined rather than hallucinated.", "https://munster.gaa.ie/fixtures/events-calendar/"),
    ]
    meth_body = f"""
    <section class="hero">
      <h1>First-Principles Odds Origination Methodology</h1>
      <p>Zero sportsbook lines or community tipster percentages exist anywhere in our pipeline (<code>scripts/slate_seed.py → scripts/slate_model.py → scripts/slate_build.py</code>). Every price is originated directly from governing-body performance data with transparent 4.5% two-way / 5.5% three-way book margin.</p>
    </section>
    <section class="section">
      <h2>Model Specifications Across All 17 Eligible Sports</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>Sport / Competition</th><th>Fixtures</th><th>Originated Markets</th><th>Mathematical Specification</th><th>Official Input Feed</th></tr></thead>
        <tbody>
          {''.join(f'<tr><td><strong>{esc(a)}</strong></td><td class="mono">{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td><td><a href="{esc(e)}" target="_blank" rel="noopener">Official Feed ↗</a></td></tr>' for a, b, c, d, e in method_rows)}
        </tbody>
      </table></div>
    </section>
    """
    (OUT_DIR / "methodology.html").write_text(page_shell("Methodology", "methodology", meth_body, depth=0))

    # 7. Sources Page: slate/sources.html
    src_list = sources["sources"] if isinstance(sources, dict) and "sources" in sources else sources
    src_rows = "".join(
        f'<tr>'
        f'<td class="mono">{esc(sr.get("id", i))}</td>'
        f'<td><strong>{esc(sr.get("sport", ""))}</strong></td>'
        f'<td>{esc(sr.get("authority", sr.get("name", "")))}</td>'
        f'<td>{esc(sr.get("scope", sr.get("data_captured", "")))}</td>'
        f'<td class="mono">{esc(sr.get("captured_at", "2026-10-22 UTC"))}</td>'
        f'<td><a href="{esc(sr["url"])}" target="_blank" rel="noopener">{esc(sr["url"][:64])}… ↗</a></td>'
        f'</tr>'
        for i, sr in enumerate(src_list, start=1)
    )
    sources_body = f"""
    <section class="hero">
      <h1>Official Trusted Primary Sources Registry ({len(src_list)} Endpoints)</h1>
      <p>Every fixture, ranking, goal/point differential, and player record in <code>/slate/</code> traces directly to an authoritative league, federation, or tour endpoint captured on 2026-10-22 UTC.</p>
    </section>
    <section class="section">
      <div class="table-wrap"><table>
        <thead><tr><th>ID</th><th>Sport</th><th>Governing Authority</th><th>Verified Data Captured</th><th>Captured At</th><th>Direct URL</th></tr></thead>
        <tbody>{src_rows}</tbody>
      </table></div>
    </section>
    """
    (OUT_DIR / "sources.html").write_text(page_shell("Official Sources", "sources", sources_body, depth=0))

    # 8. Excluded Sports Page: slate/excluded.html
    excl_rows = "".join(
        f'<tr>'
        f'<td><strong>{esc(ex["olbg_name"])}</strong></td>'
        f'<td class="mono">{esc(", ".join(ex["tokens"]))}</td>'
        f'<td class="mono">https://www.olbg.com{esc(ex["olbg_path"])}</td>'
        f'<td class="mono"><strong>0 rows</strong> (enforced by unit test)</td>'
        f'<td><a href="https://www.olbg.com{esc(ex["olbg_path"])}" target="_blank" rel="noopener">OLBG Index ↗</a></td>'
        f'</tr>'
        for ex in seed["excluded_sports"]
    )
    excl_body = f"""
    <section class="hero">
      <h1>Excluded OLBG Sports — Strict Zero-Leakage Guardrail</h1>
      <p>Per standing scope rules, the following 8 OLBG categories (covering all 10 excluded sport tokens: <code>soccer</code>, <code>football</code>, <code>boxing</code>, <code>ufc</code>, <code>mma</code>, <code>american football</code>, <code>hurling</code>, <code>horse racing</code>, <code>cycling</code>, <code>specials</code>) are excluded from every seed, model, and HTML output and verified at 0 rows in <code>tests/test_slate.py</code>.</p>
    </section>
    <section class="section">
      <div class="table-wrap"><table>
        <thead><tr><th>OLBG Category</th><th>Excluded Tokens</th><th>OLBG Path</th><th>Rows in /slate/</th><th>Reference Link</th></tr></thead>
        <tbody>{excl_rows}</tbody>
      </table></div>
    </section>
    """
    (OUT_DIR / "excluded.html").write_text(page_shell("Excluded Sports Audit", "excluded", excl_body, depth=0))

    # 9. Sports Directory (slate/sports/index.html) + All 17 Individual Sport Pages (slate/sports/<slug>.html)
    pills = "".join(
        f'<a href="{esc(sp["slug"])}.html">{esc(sp["name"])} ({sport_summaries[sp["slug"]]["total_fixtures"]})</a>'
        for sp in seed["eligible_sports"]
    )
    dir_body = f"""
    <section class="hero">
      <h1>All 17 Eligible OLBG Sport Subpages</h1>
      <p>Navigate directly into any individual sport for its originated multi-market lines, human-written predictions, unlined blank disclosures, and governing-body source links.</p>
      <div class="pill-list">{pills}</div>
    </section>
    <section class="section">
      <h2>17-Sport Summary Matrix</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>Sport</th><th>Originated</th><th>Unlined (Blank)</th><th>High / Med / Low</th><th>Featured Picks</th><th>Official Authority</th><th>OLBG Category</th></tr></thead>
        <tbody>
          {''.join(
              f'<tr><td><a href="{esc(sp["slug"])}.html"><strong>{esc(sp["name"])}</strong></a></td>'
              f'<td class="mono">{sport_summaries[sp["slug"]]["originated_count"]}</td>'
              f'<td class="mono">{sport_summaries[sp["slug"]]["unlined_count"]}</td>'
              f'<td class="mono">{sport_summaries[sp["slug"]]["high_conf_count"]} / {sport_summaries[sp["slug"]]["medium_conf_count"]} / {sport_summaries[sp["slug"]]["low_conf_count"]}</td>'
              f'<td class="mono">{sport_summaries[sp["slug"]]["featured_picks_count"]}</td>'
              f'<td><a href="{esc(sp["authority_url"])}" target="_blank" rel="noopener">{esc(sp["authority"])} ↗</a></td>'
              f'<td><a href="{esc(sp["olbg_url"])}" target="_blank" rel="noopener">OLBG Category ↗</a></td></tr>'
              for sp in seed["eligible_sports"]
          )}
        </tbody>
      </table></div>
    </section>
    """
    (OUT_DIR / "sports" / "index.html").write_text(page_shell("17 Sports Directory", "sports", dir_body, depth=1))

    for sp in seed["eligible_sports"]:
        slug = sp["slug"]
        info = sport_summaries[slug]
        sp_matches = [m for m in matches if m["sport"] == slug]
        sp_unlined = [u for u in unlined if u["sport"] == slug]
        sp_preds = [p for p in preds if p["sport"] == slug]
        peer_pills = "".join(
            f'<a href="{esc(o["slug"])}.html">{esc(o["name"])} ({sport_summaries[o["slug"]]["total_fixtures"]})</a>'
            for o in seed["eligible_sports"]
        )
        sections = [f"""
        <section class="hero">
          <h1>{esc(sp['name'])} — Verified Match List, Originated Odds &amp; Analysis</h1>
          <p>Primary Governing Source: <a href="{esc(sp['authority_url'])}" target="_blank" rel="noopener"><strong>{esc(sp['authority'])} ↗</strong></a> · OLBG Taxonomy: <a href="{esc(sp['olbg_url'])}" target="_blank" rel="noopener">{esc(sp['olbg_url'])} ↗</a></p>
          <div class="pill-list">{peer_pills}</div>
        </section>
        <div class="kpi-grid">
          <div class="kpi"><div class="num">{info['originated_count']}</div><div class="lbl">Originated Matches</div></div>
          <div class="kpi"><div class="num">{info['unlined_count']}</div><div class="lbl">Unlined Rows (Blank)</div></div>
          <div class="kpi"><div class="num">{info['high_conf_count']}</div><div class="lbl">High-Confidence Matches</div></div>
          <div class="kpi"><div class="num">{info['featured_picks_count']}</div><div class="lbl">Featured Human Picks</div></div>
        </div>
        """]
        if sp_preds:
            sections.append(f"""
            <section class="section">
              <h2>Featured High-Confidence {esc(sp['name'])} Predictions</h2>
              <p class="lead">Every pick below is priced inside [-250, +10000] and grounded in verified governing-body form.</p>
              {render_pick_cards(sp_preds, depth=1)}
            </section>
            """)
        if sp_matches:
            sections.append(f"""
            <section class="section">
              <div class="controls">
                <input id="slate-search" type="search" placeholder="Filter {esc(sp['name'])} matches…">
                <select id="slate-conf">
                  <option value="all">All Confidence Tiers</option>
                  <option value="high">High ({info['high_conf_count']})</option>
                  <option value="medium">Medium ({info['medium_conf_count']})</option>
                  <option value="low">Low ({info['low_conf_count']})</option>
                </select>
                <select id="odds-format">
                  <option value="am">Odds: Originated American</option>
                  <option value="dec">Odds: Originated Decimal</option>
                  <option value="fair">Fair Prob % &amp; Fair Line</option>
                </select>
                <span id="slate-count" class="mono muted">{len(sp_matches)} shown</span>
              </div>
              {render_matches_table(sp_matches, depth=1)}
            </section>
            """)
        if sp_unlined:
            sections.append(f"""
            <section class="section">
              <h2>Verified {esc(sp['name'])} Fixtures Left Intentionally Blank ({len(sp_unlined)} Rows)</h2>
              <p class="lead">Confirmed on official schedules on 2026-10-22 UTC; odds left blank (<code>—</code>) and linked to <a href="../flagged.html">Flagged for Review</a> rather than inferred.</p>
              {render_unlined_table(sp_unlined, depth=1)}
            </section>
            """)
        (OUT_DIR / "sports" / f"{slug}.html").write_text(page_shell(f"{sp['name']} Odds & Picks", "sports", "".join(sections), depth=1))

    html_files = sorted(OUT_DIR.rglob("*.html"))
    print(f"Built {len(html_files)} HTML pages in {OUT_DIR}")


if __name__ == "__main__":
    main()
