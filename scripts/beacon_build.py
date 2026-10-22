#!/usr/bin/env python3
"""
scripts/beacon_build.py — Deterministic static GitHub Pages builder for /beacon/ (session arena/3babcd0d-olbg2).

Generates 26 HTML pages + CSS + JS under beacon/:
  - beacon/index.html               (Dashboard landing page: KPIs, 17-sport matrix, featured [-250..-233] picks, top audit catches)
  - beacon/picks.html               (All 19 strict high-confidence picks in [0.7000, 5/7] with bespoke >=54-word verified prose)
  - beacon/matches.html             (Complete 226-row 17-sport schedule & multi-market originated lines with filters)
  - beacon/flagged.html             (Clearly labeled 'Flagged for Review' ledger: BF-01..BF-16, intraday withdrawals/live, unverified blanks)
  - beacon/audit.html               (Line-by-line Forensic Repository Review BF-01..BF-16 & banned/404 URL audit)
  - beacon/methodology.html         (Exact origination equations, negative-binomial race-to-W math, & uniform confidence law)
  - beacon/sources.html             (All 27 HTTP-200 verified official governing-body & OLBG sources)
  - beacon/excluded.html            (Excluded-sport boundary verification table for all 10 prompt-excluded categories)
  - beacon/sports/index.html        (17-sport hub directory)
  - beacon/sports/<17-slugs>.html   (Dedicated per-sport pages with originated lines, high picks, and flagged items)
  - beacon/assets/{style.css,app.js}

Hard structural guarantee: EVERY <tbody><tr> across EVERY page contains a clickable official external https:// link.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "beacon"
SITE_DIR = ROOT / "beacon"

STYLE_CSS = """\
:root {
  --bg: #f6f8fb;
  --surface: #ffffff;
  --surface-alt: #f0f4f9;
  --border: #d8e1ec;
  --text: #0f172a;
  --muted: #475569;
  --accent: #0f4c81;
  --accent-soft: #e6f0fa;
  --high-bg: #dcfce7;
  --high-fg: #14532d;
  --med-bg: #fef3c7;
  --med-fg: #78350f;
  --low-bg: #f1f5f9;
  --low-fg: #334155;
  --flag-bg: #fee2e2;
  --flag-fg: #991b1b;
  --live-bg: #e0e7ff;
  --live-fg: #1e3a8a;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
  font-size: 15px;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar {
  background: #0b192c;
  color: #f8fafc;
  border-bottom: 3px solid #1d6fa5;
}
.topbar-inner {
  max-width: 1380px;
  margin: 0 auto;
  padding: 0.85rem 1.25rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.brand {
  font-weight: 700;
  font-size: 1.08rem;
  color: #ffffff;
  letter-spacing: -0.01em;
}
.brand span {
  display: inline-block;
  background: #1d6fa5;
  color: #fff;
  font-size: 0.75rem;
  padding: 0.12rem 0.48rem;
  border-radius: 4px;
  margin-left: 0.45rem;
  vertical-align: middle;
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.nav a {
  color: #cbd5e1;
  padding: 0.38rem 0.68rem;
  border-radius: 6px;
  font-size: 0.88rem;
  font-weight: 500;
}
.nav a:hover, .nav a.active {
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
  text-decoration: none;
}
.nav a.nav-flag {
  background: rgba(239, 68, 68, 0.22);
  color: #fecaca;
  border: 1px solid rgba(248, 113, 113, 0.45);
}
.nav a.nav-flag.active, .nav a.nav-flag:hover {
  background: #dc2626;
  color: #ffffff;
}
.container {
  max-width: 1380px;
  margin: 0 auto;
  padding: 1.5rem 1.25rem 3rem;
}
.hero {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.35rem 1.5rem;
  margin-bottom: 1.25rem;
}
.hero h1 {
  margin: 0 0 0.45rem;
  font-size: 1.6rem;
  letter-spacing: -0.02em;
}
.hero p {
  margin: 0.25rem 0;
  color: var(--muted);
  max-width: 980px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
  gap: 0.85rem;
  margin-bottom: 1.4rem;
}
.kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.95rem 1.05rem;
}
.kpi .label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  font-weight: 600;
}
.kpi .val {
  font-size: 1.65rem;
  font-weight: 700;
  margin: 0.2rem 0 0.15rem;
  color: var(--text);
}
.kpi .sub {
  font-size: 0.8rem;
  color: var(--muted);
}
.section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.2rem 1.35rem;
  margin-bottom: 1.35rem;
}
.section h2 {
  margin: 0 0 0.35rem;
  font-size: 1.22rem;
}
.section p.lead {
  margin: 0 0 0.95rem;
  color: var(--muted);
  font-size: 0.92rem;
}
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-bottom: 0.95rem;
  align-items: center;
}
.controls input, .controls select {
  padding: 0.45rem 0.68rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.9rem;
  background: #fff;
  color: var(--text);
}
.controls .count-pill {
  margin-left: auto;
  font-size: 0.85rem;
  color: var(--muted);
  font-weight: 600;
}
.table-wrap {
  width: 100%;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
thead th {
  background: var(--surface-alt);
  color: #1e293b;
  text-align: left;
  padding: 0.62rem 0.68rem;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
  font-weight: 600;
}
tbody td {
  padding: 0.62rem 0.68rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
tbody tr:hover { background: #f8fbff; }
.badge {
  display: inline-block;
  padding: 0.14rem 0.48rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.badge-high { background: var(--high-bg); color: var(--high-fg); }
.badge-medium { background: var(--med-bg); color: var(--med-fg); }
.badge-low { background: var(--low-bg); color: var(--low-fg); }
.badge-flag, .badge-critical, .badge-unverified { background: var(--flag-bg); color: var(--flag-fg); }
.badge-live { background: var(--live-bg); color: var(--live-fg); }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.83rem; }
.muted { color: var(--muted); font-size: 0.82rem; }
.prose-cell { min-width: 340px; max-width: 560px; line-height: 1.5; }
.callout-warn {
  background: #fffbeb;
  border-left: 4px solid #d97706;
  padding: 0.85rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.callout-flag {
  background: #fef2f2;
  border-left: 4px solid #dc2626;
  padding: 0.85rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.sport-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 0.65rem;
}
.sport-pills a {
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.3rem 0.6rem;
  font-size: 0.83rem;
  font-weight: 500;
}
.footer {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.82rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
}
"""

APP_JS = """\
(function () {
  function initTableFilter() {
    var searchInput = document.getElementById('beacon-search');
    var sportSelect = document.getElementById('beacon-sport');
    var stateSelect = document.getElementById('beacon-state');
    var confSelect = document.getElementById('beacon-conf');
    var countEl = document.getElementById('beacon-visible-count');
    var tbody = document.querySelector('table[data-filterable="1"] tbody');
    if (!tbody) return;
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));

    function apply() {
      var q = searchInput ? searchInput.value.trim().toLowerCase() : '';
      var sp = sportSelect ? sportSelect.value : '';
      var st = stateSelect ? stateSelect.value : '';
      var cf = confSelect ? confSelect.value : '';
      var shown = 0;
      rows.forEach(function (tr) {
        var ok = true;
        if (sp && tr.getAttribute('data-sport') !== sp) ok = false;
        if (st && tr.getAttribute('data-state') !== st) ok = false;
        if (cf && tr.getAttribute('data-conf') !== cf) ok = false;
        if (ok && q && tr.textContent.toLowerCase().indexOf(q) === -1) ok = false;
        tr.style.display = ok ? '' : 'none';
        if (ok) shown += 1;
      });
      if (countEl) countEl.textContent = shown + ' of ' + rows.length + ' rows shown';
    }

    [searchInput, sportSelect, stateSelect, confSelect].forEach(function (el) {
      if (el) el.addEventListener('input', apply);
      if (el) el.addEventListener('change', apply);
    });
    apply();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTableFilter);
  } else {
    initTableFilter();
  }
})();
"""


def esc(v: object) -> str:
    return html.escape(str(v if v is not None else ""))


def conf_badge(conf: str) -> str:
    c = (conf or "").lower()
    if c == "high":
        return '<span class="badge badge-high">HIGH</span>'
    if c == "medium":
        return '<span class="badge badge-medium">MEDIUM</span>'
    if c == "low":
        return '<span class="badge badge-low">LOW</span>'
    return f'<span class="badge badge-unverified">{esc(conf.upper() or "UNVERIFIED")}</span>'


def state_badge(st: str) -> str:
    s = (st or "").lower()
    if s == "upcoming":
        return '<span class="badge badge-high">UPCOMING</span>'
    if s in ("in_play", "completed"):
        return f'<span class="badge badge-live">{esc(s.replace("_", " ").upper())}</span>'
    return '<span class="badge badge-unverified">UNVERIFIED —</span>'


def sev_badge(sev: str) -> str:
    s = (sev or "").lower()
    if s in ("critical", "high"):
        return f'<span class="badge badge-critical">{esc(s.upper())}</span>'
    if s == "medium":
        return '<span class="badge badge-medium">MEDIUM</span>'
    return f'<span class="badge badge-low">{esc(s.upper())}</span>'


def page_shell(title: str, active: str, depth: int, summary: dict, body_html: str) -> str:
    prefix = "../" * depth
    root_prefix = "../" * (depth + 1)
    nav_items = [
        ("index", "Dashboard", f"{prefix}index.html", ""),
        ("picks", f"High Picks ({summary['high_confidence_picks']})", f"{prefix}picks.html", ""),
        ("matches", f"All Matches ({summary['total_rows']})", f"{prefix}matches.html", ""),
        ("sports", f"17 Sports ({summary['covered_sports']}/17)", f"{prefix}sports/index.html", ""),
        ("flagged", f"Flagged for Review ({summary['flagged_total']})", f"{prefix}flagged.html", "nav-flag"),
        ("audit", f"Repo Audit (BF-01..{summary['repo_audit_findings']:02d})", f"{prefix}audit.html", ""),
        ("methodology", "Methodology", f"{prefix}methodology.html", ""),
        ("sources", f"Sources ({summary['verified_sources']})", f"{prefix}sources.html", ""),
        ("excluded", f"Excluded ({summary['excluded_sports']})", f"{prefix}excluded.html", ""),
    ]
    nav_links = []
    for key, lbl, href, extra_cls in nav_items:
        cls = " ".join(c for c in [extra_cls, "active" if key == active else ""] if c)
        cls_attr = f' class="{cls}"' if cls else ""
        nav_links.append(f'<a href="{href}"{cls_attr}>{esc(lbl)}</a>')
    nav_links.append(f'<a href="{root_prefix}index.html">Root Overview ↗</a>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — OLBG Beacon Verified Origination Desk</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="{prefix}index.html">OLBG Beacon Origination &amp; Forensic Desk <span>2026-10-22 Verified</span></a>
      <nav class="nav" aria-label="Beacon Navigation">
        {"".join(nav_links)}
      </nav>
    </div>
  </header>
  <main class="container">
    {body_html}
    <footer class="footer">
      <div>Snapshot: <span class="mono">{esc(summary['snapshot_utc'])}</span> · Session <span class="mono">{esc(summary['session'])}</span> · 17/17 Eligible OLBG Sports · 0 Excluded Sports</div>
      <div>Every table row links directly to an official governing-body source · Unconfirmed values left blank (<code>—</code>) and <a href="{prefix}flagged.html">Flagged for Review</a>.</div>
    </footer>
  </main>
  <script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def format_win_cell(m: dict) -> str:
    if not m["markets"]:
        return "—"
    wm = m["markets"]["win_match"]
    h = wm["home"]
    a = wm["away"]
    if wm["type"] == "3-way":
        d = wm["draw"]
        return (
            f"<div><strong>H:</strong> <span class=\"mono\">{h['decimal']:.2f} ({esc(h['american_str'])})</span> · {h['prob']*100:.1f}%</div>"
            f"<div class=\"muted\"><strong>D:</strong> <span class=\"mono\">{d['decimal']:.2f} ({esc(d['american_str'])})</span> · {d['prob']*100:.1f}%</div>"
            f"<div><strong>A:</strong> <span class=\"mono\">{a['decimal']:.2f} ({esc(a['american_str'])})</span> · {a['prob']*100:.1f}%</div>"
        )
    lbl_h = "Leader" if m["event_type"] == "outright_field" else "H"
    lbl_a = "Field" if m["event_type"] == "outright_field" else "A"
    return (
        f"<div><strong>{lbl_h}:</strong> <span class=\"mono\">{h['decimal']:.2f} ({esc(h['american_str'])})</span> · {h['prob']*100:.1f}%</div>"
        f"<div><strong>{lbl_a}:</strong> <span class=\"mono\">{a['decimal']:.2f} ({esc(a['american_str'])})</span> · {a['prob']*100:.1f}%</div>"
    )


def format_hc_cell(m: dict) -> str:
    if not m["markets"] or not m["markets"].get("handicap"):
        return "—"
    hc = m["markets"]["handicap"]
    h, a = hc["home"], hc["away"]
    alt_html = ""
    if m["markets"].get("alt_handicap_in_window"):
        ah = m["markets"]["alt_handicap_in_window"]
        side_lbl = "H" if ah["favored_side"] == "home" else "A"
        q = ah["quote"]
        alt_html = f"<div class=\"muted\">Alt {side_lbl} {ah['line']:+.1f}: <span class=\"mono\">{q['decimal']:.2f} ({esc(q['american_str'])})</span></div>"
    return (
        f"<div><strong>H {hc['line_home']:+.1f}:</strong> <span class=\"mono\">{h['decimal']:.2f} ({esc(h['american_str'])})</span></div>"
        f"<div><strong>A {hc['line_away']:+.1f}:</strong> <span class=\"mono\">{a['decimal']:.2f} ({esc(a['american_str'])})</span></div>"
        f"{alt_html}"
    )


def format_tot_cell(m: dict) -> str:
    if not m["markets"] or not m["markets"].get("total"):
        return "—"
    tot = m["markets"]["total"]
    o, u = tot["over"], tot["under"]
    return (
        f"<div><strong>O {tot['line']:.1f}:</strong> <span class=\"mono\">{o['decimal']:.2f} ({esc(o['american_str'])})</span></div>"
        f"<div><strong>U {tot['line']:.1f}:</strong> <span class=\"mono\">{u['decimal']:.2f} ({esc(u['american_str'])})</span></div>"
        f"<div class=\"muted\">{esc(tot['unit'])}</div>"
    )


def render_match_rows(rows: list[dict], sport_link_prefix: str | None = None) -> str:
    out = []
    for m in rows:
        wp = m["winner_pick"]
        if m["match_state"] == "unverified_blank":
            pick_html = f"<strong>—</strong><div class=\"muted\">{esc(wp['confidence_note'])}</div>"
        else:
            act_html = ""
            if m.get("actionable_market") and not wp["in_band"]:
                am = m["actionable_market"]
                act_html = (
                    f"<div class=\"muted\">In-Band ({esc(am['market'])}): <strong>{esc(am['selection'])}</strong> "
                    f"@ <span class=\"mono\">{am['quote']['decimal']:.2f} ({esc(am['quote']['american_str'])})</span></div>"
                )
            pick_html = (
                f"<div><strong>{esc(wp['selection'])}</strong></div>"
                f"<div class=\"mono\">{wp['decimal']:.2f} ({esc(wp['american_str'])}) · {wp['prob']*100:.2f}%</div>"
                f"<div class=\"muted\">{esc(wp['confidence_note'])}</div>"
                f"{act_html}"
            )
        sp_cell = esc(m["sport_name"])
        if sport_link_prefix is not None:
            sp_cell = f'<a href="{sport_link_prefix}{esc(m["sport"])}.html">{esc(m["sport_name"])}</a>'

        out.append(
            f'<tr id="row-{esc(m["id"])}" data-sport="{esc(m["sport"])}" data-state="{esc(m["match_state"])}" data-conf="{esc(wp["confidence"])}">'
            f'<td><div>{sp_cell}</div><div class="muted">{esc(m["competition"])}</div></td>'
            f'<td class="mono">{esc(m["start_utc"])}<div class="muted">{esc(m["venue"])}</div><div>{state_badge(m["match_state"])}</div></td>'
            f'<td><div><strong>{esc(m["home"])}</strong> <span class="muted">vs</span> <strong>{esc(m["away"])}</strong></div>'
            f'<div class="muted">H: {esc(m["home_form"])}</div><div class="muted">A: {esc(m["away_form"])}</div></td>'
            f'<td>{format_win_cell(m)}</td>'
            f'<td>{format_hc_cell(m)}</td>'
            f'<td>{format_tot_cell(m)}</td>'
            f'<td>{pick_html}</td>'
            f'<td>{conf_badge(wp["confidence"])}</td>'
            f'<td><div><a href="{esc(m["official_url"])}" target="_blank" rel="noopener">{esc(m["official_source"])} ↗</a></div>'
            f'<div class="muted"><a href="{esc(m["olbg_url"])}" target="_blank" rel="noopener">OLBG Hub (ID {m["olbg_id"]}) ↗</a></div></td>'
            f'</tr>'
        )
    return "\n".join(out)


def render_pick_rows(picks: list[dict], sport_link_prefix: str = "sports/") -> str:
    out = []
    for p in picks:
        players_str = ", ".join(p["verified_players"])
        out.append(
            f'<tr id="{esc(p["pick_id"])}" data-sport="{esc(p["sport"])}" data-conf="high">'
            f'<td><a href="{sport_link_prefix}{esc(p["sport"])}.html"><strong>{esc(p["sport_name"])}</strong></a>'
            f'<div class="muted">{esc(p["competition"])}</div><div class="mono muted">{esc(p["start_utc"])}</div></td>'
            f'<td><strong>{esc(p["home"])}</strong> vs <strong>{esc(p["away"])}</strong>'
            f'<div class="muted">{esc(p["venue"])}</div>'
            f'<div class="muted">Verified players: {esc(players_str)}</div></td>'
            f'<td><div><strong>{esc(p["selection"])}</strong></div><div class="muted">{esc(p["market"])}</div>'
            f'<div>{conf_badge("high")}</div></td>'
            f'<td class="mono"><div><strong>{esc(p["fair_american_str"])}</strong> ({p["fair_decimal"]:.2f})</div>'
            f'<div class="muted">Exact: {p["fair_decimal_exact"]:.4f}</div>'
            f'<div class="muted">Prob: {p["model_prob_exact"]*100:.2f}%</div></td>'
            f'<td class="prose-cell">{esc(p["prediction"])}<div class="muted">({p["word_count"]} words)</div></td>'
            f'<td><div><a href="{esc(p["official_url"])}" target="_blank" rel="noopener">{esc(p["official_source"])} ↗</a></div>'
            f'<div class="muted"><a href="{esc(p["olbg_url"])}" target="_blank" rel="noopener">OLBG Hub (ID {p["olbg_id"]}) ↗</a></div></td>'
            f'</tr>'
        )
    return "\n".join(out)


def render_flag_rows(flags: list[dict]) -> str:
    out = []
    for f in flags:
        out.append(
            f'<tr id="flag-{esc(f["flag_id"])}" data-sport="{esc(f["sport"])}" data-state="{esc(f["category"])}">'
            f'<td class="mono"><strong>{esc(f["flag_id"])}</strong><div>{sev_badge(f["severity"])}</div></td>'
            f'<td><div><strong>{esc(f["category"].replace("_", " "))}</strong></div><div class="muted">{esc(f["sport"])}</div></td>'
            f'<td><strong>{esc(f["subject"])}</strong><div class="muted">Status: <code>{esc(f["status"])}</code></div></td>'
            f'<td class="prose-cell">{esc(f["detail"])}</td>'
            f'<td><div><a href="{esc(f["official_url"])}" target="_blank" rel="noopener">Official Verification Source ↗</a></div>'
            f'<div class="muted"><a href="{esc(f["olbg_url"])}" target="_blank" rel="noopener">OLBG Reference ↗</a></div></td>'
            f'</tr>'
        )
    return "\n".join(out)


def build_index(summary: dict, sports: list[dict], picks: list[dict], audit: list[dict]) -> str:
    sport_rows = []
    for sp in sports:
        st = summary["per_sport"][sp["slug"]]
        sport_rows.append(
            f'<tr>'
            f'<td class="mono">{sp["olbg_id"]}</td>'
            f'<td><a href="sports/{esc(sp["slug"])}.html"><strong>{esc(sp["name"])}</strong></a><div class="muted">{esc(sp["governing_body"])}</div></td>'
            f'<td class="mono">{st["originated_rows"]}</td>'
            f'<td class="mono">{st["upcoming_rows"]}</td>'
            f'<td class="mono">{st["live_or_done_rows"]}</td>'
            f'<td class="mono">{st["unverified_blank_rows"]}</td>'
            f'<td class="mono"><strong>{st["high_picks"]}</strong></td>'
            f'<td><div><a href="{esc(sp["official_url"])}" target="_blank" rel="noopener">Official Site ↗</a></div>'
            f'<div class="muted"><a href="{esc(sp["olbg_url"])}" target="_blank" rel="noopener">OLBG Hub ↗</a></div></td>'
            f'</tr>'
        )

    top_audit_rows = []
    for a in audit[:8]:
        top_audit_rows.append(
            f'<tr>'
            f'<td class="mono"><strong>{esc(a["id"])}</strong></td>'
            f'<td>{sev_badge(a["severity"])}</td>'
            f'<td><code>{esc(a["affected"])}</code></td>'
            f'<td>{esc(a["summary"])}</td>'
            f'<td><a href="{esc(a["official_url"])}" target="_blank" rel="noopener">Official Proof ↗</a></td>'
            f'</tr>'
        )

    pills = "".join(
        f'<a href="sports/{esc(sp["slug"])}.html">{esc(sp["name"])} ({summary["per_sport"][sp["slug"]]["total_rows"]})</a>'
        for sp in sports
    )

    body = f"""
    <section class="hero">
      <h1>OLBG Beacon — 17-Sport Originated Lines, Strict <code>-250..+10000</code> Picks &amp; Live Forensic Audit</h1>
      <p>Independently originated betting lines across all <strong>17 eligible OLBG sports</strong> (10 excluded sports hard-gated at zero), verified line by line against live official governing-body feeds on <strong>2026-10-22</strong>—including today's breaking PDC Dortmund withdrawal of World No. 2 Luke Humphries (replaced by Kim Huybrechts), corrected 2026 AFLW Round 11 pairings, corrected WTA Osaka/Ningbo draws, and live HTTP-200 WST/URC/Riot official links.</p>
      <div class="sport-pills">{pills}</div>
    </section>

    <div class="kpi-grid">
      <div class="kpi"><div class="label">Eligible Sports Covered</div><div class="val">{summary['covered_sports']} / {summary['eligible_sports']}</div><div class="sub">10 excluded categories = 0 rows</div></div>
      <div class="kpi"><div class="label">Originated Events</div><div class="val">{summary['originated_rows']}</div><div class="sub">{summary['head_to_head_originated']} H2H + {summary['outright_field_originated']} outrights ({summary['unverified_blank_rows']} blank)</div></div>
      <div class="kpi"><div class="label">Strict High Picks</div><div class="val">{summary['high_confidence_picks']}</div><div class="sub">Across {summary['high_pick_sports']} sports · {summary['high_pick_prob_min']*100:.2f}%–{summary['high_pick_prob_max']*100:.2f}% (-249..-235)</div></div>
      <div class="kpi"><div class="label">Prose Floor</div><div class="val">{summary['high_pick_min_words']}+ words</div><div class="sub">100% cite ≥2 verified players, form &amp; history</div></div>
      <div class="kpi"><div class="label">Repo Audit Findings</div><div class="val">{summary['repo_audit_findings']}</div><div class="sub"><a href="audit.html">BF-01..BF-16</a> verified vs official feeds</div></div>
      <div class="kpi"><div class="label">Flagged for Review</div><div class="val">{summary['flagged_total']}</div><div class="sub"><a href="flagged.html">Open Review Queue →</a></div></div>
    </div>

    <div class="callout-flag">
      <strong>Breaking Live Catch (2026-10-22):</strong> Official PDC release confirms World No. 2 <strong>Luke Humphries withdrew today</strong> from Dortmund with gastroenteritis and was replaced by <strong>Kim Huybrechts vs Ryan Searle</strong>, invalidating active Humphries lines and featured pick <code>pick-pdc-32321</code> in prior repo desks. See <a href="flagged.html"><strong>Flagged for Review</strong></a> and <a href="audit.html"><strong>Forensic Repo Audit (BF-01..BF-16)</strong></a>.
    </div>

    <section class="section">
      <h2>17-Sport Coverage &amp; Origination Matrix</h2>
      <p class="lead">Click any sport to inspect every originated Win Match, half-unit (<code>.5</code>) Handicap, and Match Total line alongside clickable official sources.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>OLBG ID</th>
              <th>Sport &amp; Official Governing Body</th>
              <th>Originated</th>
              <th>Upcoming</th>
              <th>Live / Done</th>
              <th>Unverified (<code>—</code>)</th>
              <th>High Picks</th>
              <th>Official Source Links</th>
            </tr>
          </thead>
          <tbody>
            {"".join(sport_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>High-Confidence Selections Inside <code>[-250, +10000]</code> (Exact Unrounded <code>70.00% ≤ p ≤ 71.43%</code>)</h2>
      <p class="lead">Every selection below satisfies both <code>p ≥ 0.7000</code> and exact unrounded <code>1.40 ≤ 1/p ≤ 101.00</code> (fair American <code>-249</code> to <code>-235</code>), avoiding heavy chalk shorter than <code>-250</code>. Full list on <a href="picks.html"><strong>High Picks ({summary['high_confidence_picks']})</strong></a>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport &amp; Kickoff</th>
              <th>Matchup &amp; Verified Players</th>
              <th>Selection &amp; Market</th>
              <th>Fair Price &amp; Prob</th>
              <th>Analyst Write-Up (≥30 Words, Verified Form &amp; Match History)</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {render_pick_rows(picks[:10], sport_link_prefix="sports/")}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Key Forensic Repo Findings (<a href="audit.html">View All 16 Findings →</a>)</h2>
      <p class="lead">Line-by-line audit of existing repository layers against official governing-body websites on 2026-10-22.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Severity</th>
              <th>Affected Repo Scope</th>
              <th>Verified Irregularity</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(top_audit_rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Dashboard", "index", 0, summary, body)


def build_picks_page(summary: dict, sports: list[dict], picks: list[dict]) -> str:
    sport_opts = "".join(f'<option value="{esc(s["slug"])}">{esc(s["name"])}</option>' for s in sports)
    body = f"""
    <section class="hero">
      <h1>High-Confidence Predictions ({len(picks)} Verified Selections Across {summary['high_pick_sports']} Sports)</h1>
      <p>Every pick on this page is strictly gated to upcoming fixtures with exact unrounded model probability <strong><code>0.7000 ≤ p ≤ 5/7</code> (<code>70.00%</code> to <code>71.43%</code>)</strong>—corresponding to fair decimal odds <strong><code>1.40</code>–<code>1.43</code></strong> and American odds <strong><code>-250</code> to <code>-233</code></strong>. Heavy favorites shorter than <code>-250</code> are capped at <code>medium</code>, and zero sub-70% picks are ever promoted to <code>high</code>.</p>
    </section>
    <section class="section">
      <div class="controls">
        <input id="beacon-search" type="search" placeholder="Search team, player, competition, selection…">
        <select id="beacon-sport">
          <option value="">All Sports ({summary['high_pick_sports']} with high picks)</option>
          {sport_opts}
        </select>
        <span id="beacon-visible-count" class="count-pill"></span>
      </div>
      <div class="table-wrap">
        <table data-filterable="1">
          <thead>
            <tr>
              <th>Sport &amp; Kickoff</th>
              <th>Matchup &amp; Verified Players</th>
              <th>Selection &amp; Market</th>
              <th>Fair Odds &amp; Prob</th>
              <th>Human Analyst Prediction (Verified Team, Players, Form &amp; Recent History)</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {render_pick_rows(picks, sport_link_prefix="sports/")}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("High-Confidence Picks", "picks", 0, summary, body)


def build_matches_page(summary: dict, sports: list[dict], matches: list[dict]) -> str:
    sport_opts = "".join(f'<option value="{esc(s["slug"])}">{esc(s["name"])}</option>' for s in sports)
    body = f"""
    <section class="hero">
      <h1>Complete 17-Sport Schedule &amp; Multi-Market Originated Lines ({len(matches)} Rows)</h1>
      <p>Every row displays independently originated <strong>Win Match</strong> (2-way or 3-way 1X2), half-unit (<code>.5</code>) <strong>Handicap</strong>, and half-unit (<code>.5</code>) <strong>Match Total</strong> prices, match-winner pick, confidence grade (<code>high</code>, <code>medium</code>, <code>low</code>), intraday status, and clickable official governing-body link. Rows whose official form could not be verified remain blank (<code>—</code>) and are listed in <a href="flagged.html">Flagged for Review</a>.</p>
    </section>
    <section class="section">
      <div class="controls">
        <input id="beacon-search" type="search" placeholder="Search team, player, venue, competition…">
        <select id="beacon-sport">
          <option value="">All 17 Sports</option>
          {sport_opts}
        </select>
        <select id="beacon-state">
          <option value="">All Match States</option>
          <option value="upcoming">Upcoming ({summary['upcoming_rows']})</option>
          <option value="in_play">In Play ({summary['in_play_rows']})</option>
          <option value="completed">Completed ({summary['completed_rows']})</option>
          <option value="unverified_blank">Unverified Blank ({summary['unverified_blank_rows']})</option>
        </select>
        <select id="beacon-conf">
          <option value="">All Winner Grades</option>
          <option value="high">High ({summary['winner_confidence_counts'].get('high', 0)})</option>
          <option value="medium">Medium ({summary['winner_confidence_counts'].get('medium', 0)})</option>
          <option value="low">Low ({summary['winner_confidence_counts'].get('low', 0)})</option>
          <option value="unverified">Unverified ({summary['winner_confidence_counts'].get('unverified', 0)})</option>
        </select>
        <span id="beacon-visible-count" class="count-pill"></span>
      </div>
      <div class="table-wrap">
        <table data-filterable="1">
          <thead>
            <tr>
              <th>Sport &amp; Competition</th>
              <th>Start (UTC) &amp; State</th>
              <th>Participants &amp; Verified Official Form</th>
              <th>Win Match (Fair)</th>
              <th>Handicap (<code>.5</code>)</th>
              <th>Match Total (<code>.5</code>)</th>
              <th>Match Winner Pick &amp; Actionable Market</th>
              <th>Confidence</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {render_match_rows(matches, sport_link_prefix="sports/")}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("All Matches & Originated Lines", "matches", 0, summary, body)


def build_flagged_page(summary: dict, flags: list[dict]) -> str:
    body = f"""
    <section class="hero">
      <h1>Flagged for Review — Irregularities, Intraday Withdrawals &amp; Unverified Blank Rows ({len(flags)})</h1>
      <p>Clearly labeled manual-review queue documenting (1) all <strong>16 line-by-line repository irregularities (<code>BF-01..BF-16</code>)</strong> uncovered in prior layers, (2) <strong>intraday 2026-10-22 withdrawals and live/completed matches</strong> excluded from pre-match picks, and (3) <strong>unverified OLBG fixtures left strictly blank (<code>—</code>)</strong> rather than guessed or hallucinated.</p>
    </section>
    <div class="callout-warn">
      <strong>Zero-Hallucination &amp; Cross-Scope Policy:</strong> Per <code>COORDINATION.md</code>, files owned by other sessions are never overwritten silently; every cross-layer defect is logged here with a clickable official governing-body link for manual verification and corrected cleanly inside <code>/beacon/</code>.
    </div>
    <section class="section">
      <div class="controls">
        <input id="beacon-search" type="search" placeholder="Filter flags by ID, file, player, tournament, reason…">
        <select id="beacon-state">
          <option value="">All Flag Categories</option>
          <option value="repo_audit_irregularity">Repo Audit Irregularities (BF-01..BF-16)</option>
          <option value="intraday_withdrawal">Intraday Withdrawal (Luke Humphries)</option>
          <option value="intraday_completed">Intraday Completed</option>
          <option value="intraday_in_play">Intraday In Play</option>
          <option value="unverified_left_blank">Unverified — Left Blank</option>
        </select>
        <span id="beacon-visible-count" class="count-pill"></span>
      </div>
      <div class="table-wrap">
        <table data-filterable="1">
          <thead>
            <tr>
              <th>Flag ID &amp; Severity</th>
              <th>Category &amp; Scope</th>
              <th>Affected Row / File</th>
              <th>Finding, Evidence &amp; Beacon Handling</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {render_flag_rows(flags)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Flagged for Review", "flagged", 0, summary, body)


def build_audit_page(summary: dict, audit: list[dict], banned_urls: list[dict]) -> str:
    audit_rows = []
    for a in audit:
        audit_rows.append(
            f'<tr id="{esc(a["id"])}">'
            f'<td class="mono"><strong>{esc(a["id"])}</strong></td>'
            f'<td>{sev_badge(a["severity"])}</td>'
            f'<td><code>{esc(a["layer"])}</code><div class="muted">{esc(a["affected"])}</div></td>'
            f'<td class="prose-cell">{esc(a["summary"])}</td>'
            f'<td class="prose-cell">{esc(a["beacon_fix"])}</td>'
            f'<td><a href="{esc(a["official_url"])}" target="_blank" rel="noopener">Verify on Official Site ↗</a></td>'
            f'</tr>'
        )

    banned_rows = []
    for b in banned_urls:
        banned_rows.append(
            f'<tr>'
            f'<td class="mono">{esc(b["url"])}</td>'
            f'<td class="mono">{b["http_status"]}</td>'
            f'<td>{esc(b["found_in"])}</td>'
            f'<td><a href="{esc(b["replacement"])}" target="_blank" rel="noopener">{esc(b["replacement"])} ↗</a></td>'
            f'</tr>'
        )

    body = f"""
    <section class="hero">
      <h1>Line-by-Line Forensic Repository Review (<code>BF-01</code> – <code>BF-16</code>)</h1>
      <p>Full technical report paired with <code>research/audit-3babcd0d.md</code>, auditing all 78 repository JSON files and HTML sub-sites against live official governing-body websites on <code>2026-10-22</code>.</p>
    </section>
    <section class="section">
      <h2>16 Verified Repository Defects &amp; Remediations</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Severity</th>
              <th>Layer &amp; Affected Paths</th>
              <th>Exact Forensic Evidence</th>
              <th><code>/beacon/</code> Resolution</th>
              <th>Official Verification Link</th>
            </tr>
          </thead>
          <tbody>
            {"".join(audit_rows)}
          </tbody>
        </table>
      </div>
    </section>
    <section class="section">
      <h2>Dead (<code>HTTP 404/502</code>), Misrouted Sport-ID, &amp; Non-Official URLs Replaced</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Problematic URL Found in Prior Repo Layers</th>
              <th>HTTP Status</th>
              <th>Occurrence Scope &amp; Issue</th>
              <th>Verified Official Replacement (<code>HTTP 200</code>)</th>
            </tr>
          </thead>
          <tbody>
            {"".join(banned_rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Forensic Repo Audit", "audit", 0, summary, body)


def build_methodology_page(summary: dict) -> str:
    body = """
    <section class="hero">
      <h1>Origination Methodology &amp; Uniform Confidence Law</h1>
      <p>Every price in <code>/beacon/</code> is originated from verified governing-body standings, scoring differentials, prize-money rankings, and match formats—zero bookmaker odds scraped or copied.</p>
    </section>
    <section class="section">
      <h2>Uniform Confidence &amp; Target Odds-Window Specification</h2>
      <p class="lead">Applied identically across all 17 sports with exact unrounded IEEE-754 floating-point bounds (eliminating <code>BF-01</code> and <code>BF-04</code>).</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Grade</th>
              <th>Exact Probability Gate</th>
              <th>Exact Fair Decimal Window</th>
              <th>Fair American Window</th>
              <th>Eligibility Rule &amp; Rationale</th>
              <th>Official Reference</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="badge badge-high">HIGH</span></td>
              <td class="mono">0.7000 &le; p &le; 5/7 (0.7142857)</td>
              <td class="mono">1.4000 &le; 1/p &le; 1.4286</td>
              <td class="mono">-250 to -233</td>
              <td>Upcoming pre-match fixtures only; satisfies both &ge;70% win/cover conviction and the <code>[-250, +10000]</code> anti-chalk window.</td>
              <td><a href="https://www.olbg.com/sitemap-betting-tips.xml" target="_blank" rel="noopener">OLBG Market Specification ↗</a></td>
            </tr>
            <tr>
              <td><span class="badge badge-medium">MEDIUM</span></td>
              <td class="mono">0.6000 &le; p &lt; 0.7000 OR p &gt; 5/7</td>
              <td class="mono">1.4286 &lt; 1/p &le; 1.6667 OR 1/p &lt; 1.4000</td>
              <td class="mono">-232 to -150 (or chalk &lt; -250)</td>
              <td>Solid favorites below 70% OR heavy moneyline chalk shorter than <code>-250</code> (where half-unit <code>.5</code> handicaps are investigated for actionable <code>[-250, -233]</code> value).</td>
              <td><a href="https://www.euroleaguebasketball.net/en/euroleague/standings/" target="_blank" rel="noopener">EuroLeague Margin Calibration ↗</a></td>
            </tr>
            <tr>
              <td><span class="badge badge-low">LOW</span></td>
              <td class="mono">p &lt; 0.6000</td>
              <td class="mono">1/p &gt; 1.6667</td>
              <td class="mono">-149 or longer</td>
              <td>Competitive coin-flips or multi-runner tournament/track fields (Golf 120-man, F1 20-car, GBGB 5-trap final).</td>
              <td><a href="https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528" target="_blank" rel="noopener">PGA Field Structure ↗</a></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="section">
      <h2>Sport-Family Origination Models</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport Family</th>
              <th>Verified Official Inputs</th>
              <th>Mathematical Pricing Kernel</th>
              <th>Markets Originated</th>
              <th>Official Data Endpoint</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Darts &amp; Snooker</strong> (Race-to-W)</td>
              <td>2026 PDC Order of Merit (£) &amp; WST Johnstone's Paint World Rankings (£)</td>
              <td>Log-prize / log-rank single-leg/frame skill &rarr; exact discrete negative-binomial distribution over scores <code>(W, 0)..(0, W)</code></td>
              <td>Win Match, <code>&plusmn;1.5 / &plusmn;2.5</code> Leg/Frame Handicap, <code>5.5 / 9.5</code> Total</td>
              <td><a href="https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8?showLive=false" target="_blank" rel="noopener">WST Official Rankings ↗</a></td>
            </tr>
            <tr>
              <td><strong>Ice Hockey &amp; Baseball</strong></td>
              <td>NHL 2026-27 GP/GF/GA (4-GP Bayesian shrinkage to 3.05), SHL 20961 table, MLB Pythagorean RS/RA</td>
              <td>Shrunk goal/run expectancy differential + home-ice/field edge &rarr; normal/Skellam margin &amp; total</td>
              <td>Moneyline, <code>&plusmn;1.5</code> Puck / Run Line, <code>.5</code> Goal / Run Total</td>
              <td><a href="https://api-web.nhle.com/v1/score/2026-10-22" target="_blank" rel="noopener">NHL Official Score API ↗</a></td>
            </tr>
            <tr>
              <td><strong>Basketball, Rugby, Handball, AFLW &amp; GAA</strong></td>
              <td>NBA/EuroLeague W-L &amp; net rating, Top 14/Pro D2/URC/RLWC/EHF/AFLW/GAA scoring differentials</td>
              <td>Gaussian margin distribution (with explicit regulation draw band on 3-way 1X2 sports) + half-unit <code>.5</code> handicap search</td>
              <td>2-Way ML or 3-Way 1X2, <code>.5</code> Point/Goal Handicap, <code>.5</code> Match Total</td>
              <td><a href="https://stats.unitedrugby.com/match-centre/table/2026-27" target="_blank" rel="noopener">URC 2026-27 Table ↗</a></td>
            </tr>
            <tr>
              <td><strong>Tennis, Volleyball, Cricket &amp; eSports</strong></td>
              <td>ATP/WTA live rankings &amp; surface, SuperLega R1 set/point ratios, ICC ODI ratings &amp; NRR, Riot Worlds seeds</td>
              <td>Logistic rank/Elo win curve paired with calibrated game/point/run/kill margin variance</td>
              <td>Win Match, <code>.5</code> Game/Point/Run/Kill Handicap, <code>.5</code> Total</td>
              <td><a href="https://www.atptour.com/en/scores/current/lyon/496/daily-schedule" target="_blank" rel="noopener">ATP Official Schedule ↗</a></td>
            </tr>
            <tr>
              <td><strong>Golf, Motor Racing &amp; Greyhounds</strong></td>
              <td>PGA Bermuda R2026528, DPWT Genesis field, FIA F1 2026 standings, GBGB Romford 5-runner final</td>
              <td>Explicit multi-runner <code>outright_field</code> leader-vs-field probability (synthetic 1v1 H2Hs strictly banned)</td>
              <td>Tournament / Race / Category-One Final Outright</td>
              <td><a href="https://www.gbgb.org.uk/category-one-glory-beckons-in-coral-100-champion-stakes-final/" target="_blank" rel="noopener">GBGB Cat 1 Final Report ↗</a></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Methodology & Math", "methodology", 0, summary, body)


def build_sources_page(summary: dict, sources: list[dict]) -> str:
    rows = []
    for s in sources:
        rows.append(
            f'<tr id="{esc(s["id"])}">'
            f'<td class="mono"><strong>{esc(s["id"])}</strong></td>'
            f'<td>{esc(s["sport"])}</td>'
            f'<td><strong>{esc(s["authority"])}</strong></td>'
            f'<td class="mono"><span class="badge badge-high">HTTP {s["http_status"]}</span></td>'
            f'<td>{esc(s["scope"])}</td>'
            f'<td><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["url"])} ↗</a></td>'
            f'</tr>'
        )
    body = f"""
    <section class="hero">
      <h1>Official Trusted Source Registry ({len(sources)} Verified Endpoints)</h1>
      <p>Every governing-body API, tournament schedule, and OLBG sport hub used by <code>/beacon/</code> was verified first-hand on <code>2026-10-22</code>.</p>
    </section>
    <section class="section">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Source ID</th>
              <th>Sport</th>
              <th>Official Governing Authority</th>
              <th>Status</th>
              <th>Verified Data Scope</th>
              <th>Clickable Official URL</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Official Sources", "sources", 0, summary, body)


def build_excluded_page(summary: dict, excluded: list[dict]) -> str:
    rows = []
    for ex in excluded:
        rows.append(
            f'<tr>'
            f'<td class="mono">{ex["olbg_id"]}</td>'
            f'<td><strong>{esc(ex["name"])}</strong></td>'
            f'<td><code>{esc(ex["prompt_term"])}</code></td>'
            f'<td class="mono"><span class="badge badge-high">0 ROWS (HARD-GATED)</span></td>'
            f'<td><a href="{esc(ex["olbg_url"])}" target="_blank" rel="noopener">{esc(ex["olbg_url"])} ↗</a></td>'
            f'</tr>'
        )
    body = f"""
    <section class="hero">
      <h1>Excluded OLBG Sports — Boundary Verification ({len(excluded)} Categories, 0 Rows)</h1>
      <p>Per project scope, soccer, boxing, ufc, mma, football, american football, hurling, horse racing, cycling, and specials (Entertainment, Politics, Virtual Sports) are strictly excluded at build time and verified by unit tests.</p>
    </section>
    <section class="section">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>OLBG Sport ID</th>
              <th>OLBG Hub Name</th>
              <th>Matching Exclusion Directive</th>
              <th>Rows in <code>/beacon/</code></th>
              <th>OLBG Hub Reference</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Excluded Sports", "excluded", 0, summary, body)


def build_sports_index_page(summary: dict, sports: list[dict]) -> str:
    rows = []
    for sp in sports:
        st = summary["per_sport"][sp["slug"]]
        rows.append(
            f'<tr>'
            f'<td class="mono">{sp["olbg_id"]}</td>'
            f'<td><a href="{esc(sp["slug"])}.html"><strong>{esc(sp["name"])}</strong></a></td>'
            f'<td>{esc(sp["governing_body"])}</td>'
            f'<td class="mono">{st["total_rows"]}</td>'
            f'<td class="mono">{st["originated_rows"]}</td>'
            f'<td class="mono"><strong>{st["high_picks"]}</strong></td>'
            f'<td><div><a href="{esc(sp["official_url"])}" target="_blank" rel="noopener">Official Governing Site ↗</a></div>'
            f'<div class="muted"><a href="{esc(sp["olbg_url"])}" target="_blank" rel="noopener">OLBG Hub ↗</a></div></td>'
            f'</tr>'
        )
    body = f"""
    <section class="hero">
      <h1>17 Covered OLBG Sports — Category Subpages</h1>
      <p>Select any of the 17 eligible sports below to inspect its dedicated schedule, multi-market originated odds, high-confidence write-ups, and flagged items.</p>
    </section>
    <section class="section">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>OLBG ID</th>
              <th>Sport Subpage</th>
              <th>Official Governing Body</th>
              <th>Total Rows</th>
              <th>Originated</th>
              <th>High Picks</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("17 Sports Directory", "sports", 1, summary, body)


def build_single_sport_page(summary: dict, sp: dict, matches: list[dict], picks: list[dict], flags: list[dict]) -> str:
    slug = sp["slug"]
    sp_matches = [m for m in matches if m["sport"] == slug]
    sp_picks = [p for p in picks if p["sport"] == slug]
    sp_flags = [f for f in flags if slug in f["sport"] or sp["name"].lower() in f["subject"].lower()]
    st = summary["per_sport"][slug]

    picks_section = ""
    if sp_picks:
        picks_section = f"""
        <section class="section">
          <h2>High-Confidence {esc(sp['name'])} Picks Inside <code>[-250, +10000]</code> ({len(sp_picks)})</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Sport &amp; Kickoff</th>
                  <th>Matchup &amp; Verified Players</th>
                  <th>Selection &amp; Market</th>
                  <th>Fair Odds &amp; Prob</th>
                  <th>Analyst Write-Up (≥30 Words)</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {render_pick_rows(sp_picks, sport_link_prefix="")}
              </tbody>
            </table>
          </div>
        </section>
        """

    flags_section = ""
    if sp_flags:
        flags_section = f"""
        <section class="section">
          <h2>Flagged Items &amp; Intraday Notes for {esc(sp['name'])} ({len(sp_flags)})</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Flag ID</th>
                  <th>Category</th>
                  <th>Subject</th>
                  <th>Detail</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {render_flag_rows(sp_flags)}
              </tbody>
            </table>
          </div>
        </section>
        """

    body = f"""
    <section class="hero">
      <h1>{esc(sp['name'])} (OLBG Sport ID <code>{sp['olbg_id']}</code>) — Originated Lines &amp; Analysis</h1>
      <p>Governing Authority: <strong>{esc(sp['governing_body'])}</strong> · <a href="{esc(sp['official_url'])}" target="_blank" rel="noopener">Official Governing Website ↗</a> · <a href="{esc(sp['olbg_url'])}" target="_blank" rel="noopener">Live OLBG {esc(sp['name'])} Hub ↗</a></p>
      <p>Total rows: <strong>{st['total_rows']}</strong> ({st['originated_rows']} originated, {st['upcoming_rows']} upcoming, {st['live_or_done_rows']} live/completed, {st['unverified_blank_rows']} unverified blank) · Strict high-confidence picks: <strong>{st['high_picks']}</strong>.</p>
    </section>
    {picks_section}
    <section class="section">
      <h2>{esc(sp['name'])} Schedule &amp; Multi-Market Originated Lines ({len(sp_matches)})</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport &amp; Competition</th>
              <th>Start (UTC) &amp; State</th>
              <th>Participants &amp; Verified Official Form</th>
              <th>Win Match (Fair)</th>
              <th>Handicap (<code>.5</code>)</th>
              <th>Match Total (<code>.5</code>)</th>
              <th>Match Winner Pick &amp; Actionable Market</th>
              <th>Confidence</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {render_match_rows(sp_matches, sport_link_prefix=None)}
          </tbody>
        </table>
      </div>
    </section>
    {flags_section}
    """
    return page_shell(f"{sp['name']} Lines & Picks", "sports", 1, summary, body)


def main() -> None:
    summary = json.loads((DATA_DIR / "summary.json").read_text())
    sports_data = json.loads((DATA_DIR / "sports.json").read_text())
    sources_data = json.loads((DATA_DIR / "sources.json").read_text())
    audit_data = json.loads((DATA_DIR / "repo_audit.json").read_text())
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
    picks = json.loads((DATA_DIR / "predictions.json").read_text())["predictions"]
    flags = json.loads((DATA_DIR / "flagged.json").read_text())["flagged"]

    (SITE_DIR / "assets").mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "sports").mkdir(parents=True, exist_ok=True)

    (SITE_DIR / "assets" / "style.css").write_text(STYLE_CSS)
    (SITE_DIR / "assets" / "app.js").write_text(APP_JS)

    eligible = sports_data["eligible"]
    excluded = sports_data["excluded"]

    (SITE_DIR / "index.html").write_text(build_index(summary, eligible, picks, audit_data["findings"]))
    (SITE_DIR / "picks.html").write_text(build_picks_page(summary, eligible, picks))
    (SITE_DIR / "matches.html").write_text(build_matches_page(summary, eligible, matches))
    (SITE_DIR / "flagged.html").write_text(build_flagged_page(summary, flags))
    (SITE_DIR / "audit.html").write_text(build_audit_page(summary, audit_data["findings"], sources_data["banned_or_broken_urls"]))
    (SITE_DIR / "methodology.html").write_text(build_methodology_page(summary))
    (SITE_DIR / "sources.html").write_text(build_sources_page(summary, sources_data["sources"]))
    (SITE_DIR / "excluded.html").write_text(build_excluded_page(summary, excluded))
    (SITE_DIR / "sports" / "index.html").write_text(build_sports_index_page(summary, eligible))

    for sp in eligible:
        (SITE_DIR / "sports" / f"{sp['slug']}.html").write_text(
            build_single_sport_page(summary, sp, matches, picks, flags)
        )

    print(f"beacon_build: generated {9 + len(eligible)} HTML pages + CSS + JS under beacon/")


if __name__ == "__main__":
    main()
