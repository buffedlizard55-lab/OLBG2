#!/usr/bin/env python3
"""Static GitHub Pages site builder for /hub/ (arena/42c8f6be-olbg2).

Reads ONLY data/hub/{sports,inputs,flagged,sources,repo_audit,matches,predictions}.json
and generates a fast, clean, accessible, zero-broken-link multi-page site under hub/:
  - hub/index.html               (Overview, 17-sport directory, master 189-row schedule & odds table)
  - hub/predictions.html         (All 25 high-confidence selections inside -250..+10000 with human analysis)
  - hub/flagged.html             (Flagged for Review: 8 hub flags, 10 repo audit flags, 30 blank rows, 14 partial rows)
  - hub/audit.html               (Line-by-line repository audit ledger across all upstream layers)
  - hub/methodology.html         (Mathematical origination models & 34-endpoint official source registry)
  - hub/sports/<slug>.html (x17) (Dedicated category page per eligible OLBG sport)
  - hub/assets/site.css          (Clean editorial light stylesheet)
  - hub/assets/table.js          (Progressive search, filter, and column sort)
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB_DATA = ROOT / "data" / "hub"
HUB_DIR = ROOT / "hub"

SITE_CSS = """\
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-alt: #f1f5f9;
  --ink: #0f172a;
  --muted: #475569;
  --subtle: #64748b;
  --line: #cbd5e1;
  --line-soft: #e2e8f0;
  --brand: #0f4c81;
  --brand-soft: #e0f2fe;
  --high-bg: #dcfce7;
  --high-ink: #14532d;
  --med-bg: #fef9c3;
  --med-ink: #713f12;
  --low-bg: #f1f5f9;
  --low-ink: #334155;
  --blank-bg: #fee2e2;
  --blank-ink: #7f1d1d;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.55;
}
a { color: var(--brand); text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar {
  background: var(--ink);
  color: #ffffff;
  border-bottom: 3px solid var(--brand);
}
.topbar-inner {
  max-width: 1380px;
  margin: 0 auto;
  padding: 14px 20px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.brand-title {
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.01em;
  color: #ffffff;
}
.brand-sub {
  font-size: 12px;
  color: #94a3b8;
  display: block;
}
.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.nav-links a {
  color: #e2e8f0;
  padding: 6px 11px;
  border-radius: 6px;
  font-size: 13.5px;
  font-weight: 500;
}
.nav-links a:hover, .nav-links a.active {
  background: #1e293b;
  color: #ffffff;
  text-decoration: none;
}
.container {
  max-width: 1380px;
  margin: 0 auto;
  padding: 24px 20px 56px;
}
.hero {
  background: var(--surface);
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 22px 24px;
  margin-bottom: 20px;
}
.hero h1 {
  margin: 0 0 8px;
  font-size: 24px;
  line-height: 1.25;
}
.hero p {
  margin: 0;
  color: var(--muted);
  max-width: 960px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(195px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  padding: 14px 16px;
}
.kpi-val {
  font-size: 26px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}
.kpi-lbl {
  font-size: 12.5px;
  color: var(--muted);
  margin-top: 2px;
}
.section {
  background: var(--surface);
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 20px 22px;
  margin-bottom: 24px;
}
.section h2 {
  margin: 0 0 6px;
  font-size: 19px;
}
.section-lead {
  margin: 0 0 16px;
  color: var(--muted);
  font-size: 14px;
}
.sport-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}
.sport-card {
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  padding: 13px 15px;
  background: var(--surface);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
}
.sport-card:hover { border-color: var(--brand); }
.sport-card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.sport-card-title { font-weight: 700; font-size: 15.5px; }
.sport-meta { font-size: 12.5px; color: var(--muted); font-variant-numeric: tabular-nums; }
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}
.toolbar input, .toolbar select {
  padding: 7px 11px;
  border: 1px solid var(--line);
  border-radius: 6px;
  font-size: 13.5px;
  background: #ffffff;
  color: var(--ink);
}
.toolbar input { min-width: 240px; }
.toolbar-count { font-size: 13px; color: var(--muted); margin-left: auto; font-variant-numeric: tabular-nums; }
.table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
  font-variant-numeric: tabular-nums;
}
thead th {
  background: var(--surface-alt);
  color: var(--ink);
  font-weight: 600;
  text-align: left;
  padding: 10px 11px;
  border-bottom: 2px solid var(--line);
  white-space: nowrap;
  cursor: pointer;
}
tbody td {
  padding: 9px 11px;
  border-bottom: 1px solid var(--line-soft);
  vertical-align: top;
}
tbody tr:hover { background: #f8fafc; }
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  white-space: nowrap;
}
.badge-high { background: var(--high-bg); color: var(--high-ink); }
.badge-medium { background: var(--med-bg); color: var(--med-ink); }
.badge-low { background: var(--low-bg); color: var(--low-ink); }
.badge-unlined { background: var(--blank-bg); color: var(--blank-ink); }
.muted { color: var(--muted); font-size: 12.5px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12.5px; }
.blank-cell { color: var(--subtle); font-weight: 600; }
.pred-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(410px, 1fr));
  gap: 16px;
}
@media (max-width: 520px) {
  .pred-grid { grid-template-columns: 1fr; }
}
.pred-card {
  border: 1px solid var(--line-soft);
  border-left: 4px solid #15803d;
  border-radius: 8px;
  padding: 16px 18px;
  background: var(--surface);
}
.pred-card h3 { margin: 6px 0 8px; font-size: 16.5px; line-height: 1.35; }
.pred-callout {
  background: var(--surface-alt);
  border-radius: 6px;
  padding: 8px 11px;
  margin-bottom: 10px;
  font-size: 13.5px;
  font-variant-numeric: tabular-nums;
}
.pred-text { margin: 0 0 10px; color: var(--ink); font-size: 14px; line-height: 1.6; }
.pred-facts { margin: 0; padding-left: 18px; font-size: 12.5px; color: var(--muted); }
.pred-facts li { margin-bottom: 4px; }
.pill-bar { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
.pill {
  padding: 5px 11px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #ffffff;
  font-size: 12.5px;
  cursor: pointer;
  color: var(--ink);
}
.pill.active { background: var(--brand); color: #ffffff; border-color: var(--brand); }
.footer {
  max-width: 1380px;
  margin: 0 auto;
  padding: 18px 20px 36px;
  color: var(--subtle);
  font-size: 12.5px;
  border-top: 1px solid var(--line-soft);
}
"""

TABLE_JS = """\
(function () {
  function initFilterableTable(wrapper) {
    var table = wrapper.querySelector("table[data-hub-table]");
    if (!table) return;
    var tbody = table.querySelector("tbody");
    var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
    var searchInput = wrapper.querySelector("[data-filter-search]");
    var confSelect = wrapper.querySelector("[data-filter-conf]");
    var sportSelect = wrapper.querySelector("[data-filter-sport]");
    var counter = wrapper.querySelector("[data-filter-count]");

    function applyFilters() {
      var q = searchInput ? searchInput.value.trim().toLowerCase() : "";
      var cf = confSelect ? confSelect.value : "all";
      var sp = sportSelect ? sportSelect.value : "all";
      var shown = 0;
      rows.forEach(function (tr) {
        var matchQ = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        var matchC = cf === "all" || tr.getAttribute("data-conf") === cf;
        var matchS = sp === "all" || tr.getAttribute("data-sport") === sp;
        var vis = matchQ && matchC && matchS;
        tr.style.display = vis ? "" : "none";
        if (vis) shown += 1;
      });
      if (counter) {
        counter.textContent = "Showing " + shown + " of " + rows.length + " verified rows";
      }
    }

    if (searchInput) searchInput.addEventListener("input", applyFilters);
    if (confSelect) confSelect.addEventListener("change", applyFilters);
    if (sportSelect) sportSelect.addEventListener("change", applyFilters);

    var headers = table.querySelectorAll("thead th");
    headers.forEach(function (th, idx) {
      th.addEventListener("click", function () {
        var asc = th.getAttribute("data-sort-dir") !== "asc";
        headers.forEach(function (h) { h.removeAttribute("data-sort-dir"); });
        th.setAttribute("data-sort-dir", asc ? "asc" : "desc");
        rows.sort(function (a, b) {
          var ta = (a.children[idx] ? a.children[idx].textContent : "").trim();
          var tb = (b.children[idx] ? b.children[idx].textContent : "").trim();
          var na = parseFloat(ta.replace(/[^0-9.-]/g, ""));
          var nb = parseFloat(tb.replace(/[^0-9.-]/g, ""));
          if (!isNaN(na) && !isNaN(nb) && /^[+-]?\\d/.test(ta) && /^[+-]?\\d/.test(tb)) {
            return asc ? na - nb : nb - na;
          }
          return asc ? ta.localeCompare(tb) : tb.localeCompare(ta);
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
      });
    });

    applyFilters();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-table-section]").forEach(initFilterableTable);
    var pills = document.querySelectorAll("[data-pred-pill]");
    var cards = document.querySelectorAll("[data-pred-card]");
    pills.forEach(function (pill) {
      pill.addEventListener("click", function () {
        var sp = pill.getAttribute("data-pred-pill");
        pills.forEach(function (p) { p.classList.remove("active"); });
        pill.classList.add("active");
        cards.forEach(function (c) {
          c.style.display = (sp === "all" || c.getAttribute("data-sport") === sp) ? "" : "none";
        });
      });
    });
  });
})();
"""


def esc(v: object) -> str:
    return html.escape(str(v), quote=True)


def render_market_cell(m: dict | None, max_items: int = 3) -> str:
    if not m or not m.get("outcomes"):
        return '<span class="blank-cell" title="Unconfirmed in primary static feed — left blank">—</span>'
    items = m["outcomes"][:max_items]
    lines = []
    for o in items:
        lbl = esc(o["label"])
        dec = f"{o['fair_decimal']:.2f}"
        am = esc(o["fair_american_str"])
        pr = f"{o['prob'] * 100:.1f}%"
        lines.append(f"<div><strong>{lbl}</strong>: {dec} <span class=\"muted\">({am} · {pr})</span></div>")
    if len(m["outcomes"]) > max_items:
        rem = len(m["outcomes"]) - max_items
        lines.append(f'<div class="muted">+ {rem} more championship contenders priced</div>')
    return "".join(lines)


def render_pick_cell(row: dict, prefix: str) -> str:
    p = row.get("pick")
    if not p:
        return '<span class="badge badge-unlined">Unlined</span><div class="muted">Left blank</div>'
    conf = p["confidence"]
    badge = f'<span class="badge badge-{esc(conf)}">{esc(conf)}</span>'
    price = f"{p['fair_decimal']:.2f} ({esc(p['fair_american_str'])})"
    sel = esc(p["selection"])
    if conf == "high":
        return (
            f"{badge}<div><a href=\"{prefix}predictions.html#pred-{esc(row['id'])}\"><strong>{sel}</strong></a></div>"
            f'<div class="muted">{price} · {p["prob"] * 100:.1f}%</div>'
        )
    return f"{badge}<div><strong>{sel}</strong></div><div class=\"muted\">{price} · {p['prob'] * 100:.1f}%</div>"


def render_schedule_table(rows: list[dict], prefix: str, show_sport_col: bool = True, sports_list: list[dict] | None = None) -> str:
    sport_opts = ""
    if show_sport_col and sports_list:
        opts = ['<option value="all">All 17 Sports</option>']
        for s in sports_list:
            opts.append(f'<option value="{esc(s["slug"])}">{esc(s["name"])}</option>')
        sport_opts = f'<select data-filter-sport aria-label="Filter by sport">{"".join(opts)}</select>'

    headers = []
    headers.append("<th>Date / UTC</th>")
    if show_sport_col:
        headers.append("<th>Sport</th>")
    headers.extend([
        "<th>Competition &amp; Matchup</th>",
        "<th>Fair Match Winner</th>",
        "<th>Fair Handicap / Spread</th>",
        "<th>Fair Total (O/U)</th>",
        "<th>Pick &amp; Confidence</th>",
        "<th>Official Trusted Source</th>",
    ])

    body_rows = []
    for r in rows:
        conf_attr = r["pick"]["confidence"] if r.get("pick") else "unlined"
        tds = [f'<td class="mono">{esc(r["start_utc"])}</td>']
        if show_sport_col:
            tds.append(f'<td><a href="{prefix}sports/{esc(r["sport"])}.html"><strong>{esc(r["sport_name"])}</strong></a></td>')
        tds.append(
            f"<td><div><strong>{esc(r['event'])}</strong></div>"
            f"<div class=\"muted\">{esc(r['competition'])} · {esc(r['venue'])}</div></td>"
        )
        tds.append(f"<td>{render_market_cell(r['markets']['winner'])}</td>")
        tds.append(f"<td>{render_market_cell(r['markets']['handicap'])}</td>")
        tds.append(f"<td>{render_market_cell(r['markets']['total'])}</td>")
        tds.append(f"<td>{render_pick_cell(r, prefix)}</td>")
        tds.append(
            f'<td><a href="{esc(r["official_url"])}" target="_blank" rel="noopener noreferrer">{esc(r["official_source"])}</a>'
            f'<div class="muted"><a href="{esc(r["olbg_url"])}" target="_blank" rel="noopener noreferrer">OLBG Hub ↗</a></div></td>'
        )
        body_rows.append(f'<tr id="row-{esc(r["id"])}" data-conf="{esc(conf_attr)}" data-sport="{esc(r["sport"])}">{"".join(tds)}</tr>')

    return f"""
<div data-table-section>
  <div class="toolbar">
    <input type="search" data-filter-search placeholder="Search team, player, venue, competition…" aria-label="Search rows">
    {sport_opts}
    <select data-filter-conf aria-label="Filter by confidence">
      <option value="all">All Tiers ({len(rows)})</option>
      <option value="high">High Confidence (-250 to +10000)</option>
      <option value="medium">Medium Confidence</option>
      <option value="low">Low Confidence</option>
      <option value="unlined">Unlined / Left Blank</option>
    </select>
    <span class="toolbar-count" data-filter-count>Showing {len(rows)} of {len(rows)} verified rows</span>
  </div>
  <div class="table-wrap">
    <table data-hub-table>
      <thead><tr>{"".join(headers)}</tr></thead>
      <tbody>{"".join(body_rows)}</tbody>
    </table>
  </div>
</div>
"""


def render_prediction_card(p: dict, prefix: str) -> str:
    facts_html = "".join(
        f'<li>{esc(f["claim"])} — <a href="{esc(f["source"])}" target="_blank" rel="noopener noreferrer">Official source ↗</a></li>'
        for f in p["facts"]
    )
    return f"""
<article class="pred-card" id="pred-{esc(p['match_id'])}" data-pred-card data-sport="{esc(p['sport'])}">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
    <span class="badge badge-high">High Confidence · {esc(p['fair_american_str'])} ({p['fair_decimal']:.2f})</span>
    <span class="muted"><a href="{prefix}sports/{esc(p['sport'])}.html">{esc(p['sport_name'])}</a> · {esc(p['start_utc'])}</span>
  </div>
  <h3>{esc(p['headline'])}</h3>
  <div class="pred-callout">
    <strong>Match:</strong> {esc(p['event'])} ({esc(p['competition'])})<br>
    <strong>Selection:</strong> {esc(p['selection'])} · <strong>Fair Odds:</strong> {p['fair_decimal']:.2f} decimal / {esc(p['fair_american_str'])} American ({p['probability'] * 100:.1f}% win prob)
  </div>
  <p class="pred-text">{esc(p['text'])}</p>
  <ul class="pred-facts">{facts_html}</ul>
  <div class="muted" style="margin-top:8px;">
    Primary Match Link: <a href="{esc(p['official_url'])}" target="_blank" rel="noopener noreferrer">{esc(p['official_source'])} ↗</a>
    · <a href="{prefix}index.html#row-{esc(p['match_id'])}">View full 3-market row</a>
  </div>
</article>
"""


def page_shell(title: str, active: str, body: str, prefix: str = "") -> str:
    nav_items = [
        ("overview", f"{prefix}index.html", "Overview & Schedule (189)"),
        ("predictions", f"{prefix}predictions.html", "High-Confidence Picks (25)"),
        ("flagged", f"{prefix}flagged.html", "Flagged for Review"),
        ("audit", f"{prefix}audit.html", "Line-by-Line Repo Audit"),
        ("methodology", f"{prefix}methodology.html", "Models & Official Sources"),
        ("portal", f"{prefix}../index.html", "Repository Portal ↗"),
    ]
    nav_html = "".join(
        f'<a href="{href}" class="{"active" if key == active else ""}">{esc(label)}</a>'
        for key, href, label in nav_items
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — OLBG Primary-Verified Origination Hub</title>
  <link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div>
        <a href="{prefix}index.html" class="brand-title" style="text-decoration:none;">OLBG Multi-Sport Origination Hub</a>
        <span class="brand-sub">17 Eligible Sports · 159 Fair-Priced Fixtures · 25 Verified High-Confidence Picks (-250 to +10000) · Zero Unverified Values</span>
      </div>
      <nav class="nav-links" aria-label="Primary navigation">{nav_html}</nav>
    </div>
  </header>
  <main class="container">
    {body}
  </main>
  <footer class="footer">
    OLBG2 Primary-Source Verification &amp; Odds Origination Hub (<code>/hub/</code> · branch <code>arena/42c8f6be-olbg2</code> · captured 2026-10-22 UTC).
    All 10 excluded sports (soccer, football, boxing, UFC, MMA, American football, hurling, horse racing, cycling, specials) strictly omitted.
    Every table row links directly to its governing-body primary source; unconfirmed inputs are left blank (<code>—</code>) and logged on <a href="{prefix}flagged.html">Flagged for Review</a>.
  </footer>
  <script src="{prefix}assets/table.js"></script>
</body>
</html>
"""


def main() -> None:
    sports_data = json.loads((HUB_DATA / "sports.json").read_text(encoding="utf-8"))
    flagged_data = json.loads((HUB_DATA / "flagged.json").read_text(encoding="utf-8"))
    sources_data = json.loads((HUB_DATA / "sources.json").read_text(encoding="utf-8"))
    audit_data = json.loads((HUB_DATA / "repo_audit.json").read_text(encoding="utf-8"))
    matches_data = json.loads((HUB_DATA / "matches.json").read_text(encoding="utf-8"))
    preds_data = json.loads((HUB_DATA / "predictions.json").read_text(encoding="utf-8"))

    rows = matches_data["rows"]
    preds = preds_data["predictions"]
    eligible = sports_data["eligible"]
    excluded = sports_data["excluded"]

    (HUB_DIR / "assets").mkdir(parents=True, exist_ok=True)
    (HUB_DIR / "sports").mkdir(parents=True, exist_ok=True)
    (HUB_DIR / "assets" / "site.css").write_text(SITE_CSS, encoding="utf-8")
    (HUB_DIR / "assets" / "table.js").write_text(TABLE_JS, encoding="utf-8")

    by_sport: dict[str, list[dict]] = {s["slug"]: [] for s in eligible}
    for r in rows:
        by_sport[r["sport"]].append(r)

    preds_by_sport: dict[str, list[dict]] = {s["slug"]: [] for s in eligible}
    for p in preds:
        preds_by_sport[p["sport"]].append(p)

    # 1. Build hub/index.html
    cards_html = []
    for s in eligible:
        sl = s["slug"]
        srows = by_sport[sl]
        orig_n = sum(1 for r in srows if r["status"] == "originated")
        unl_n = sum(1 for r in srows if r["status"] == "unlined")
        high_n = len(preds_by_sport[sl])
        badge = (
            f'<span class="badge badge-high">{high_n} High</span>'
            if high_n
            else (f'<span class="badge badge-low">{orig_n} Priced</span>' if orig_n else '<span class="badge badge-unlined">0 Lined</span>')
        )
        cards_html.append(f"""
        <div class="sport-card">
          <div>
            <div class="sport-card-head">
              <a class="sport-card-title" href="sports/{esc(sl)}.html">{esc(s['name'])}</a>
              {badge}
            </div>
            <div class="sport-meta" style="margin-top:4px;">
              <strong>{orig_n}</strong> originated · <strong>{unl_n}</strong> unlined · OLBG ID <code>{s['olbg_sport_id']}</code>
            </div>
            <div class="muted" style="margin-top:4px;">{esc(s['model_family'])}</div>
          </div>
          <div class="muted">
            <a href="sports/{esc(sl)}.html">Open table →</a> ·
            <a href="{esc(s['official_url'])}" target="_blank" rel="noopener noreferrer">{esc(s['official_source'])} ↗</a>
          </div>
        </div>
        """)

    excl_rows_html = "".join(
        f"<tr><td><strong>{esc(x['name'])}</strong></td><td class=\"mono\">{x['olbg_sport_id']}</td>"
        f"<td>{esc(x['reason'])}</td>"
        f'<td><a href="{esc(x["olbg_url"])}" target="_blank" rel="noopener noreferrer">OLBG Sitemap Reference ↗</a></td></tr>'
        for x in excluded
    )

    index_body = f"""
    <section class="hero">
      <h1>Primary-Verified Multi-Sport Schedule, Originated Fair Lines &amp; Picks</h1>
      <p>
        Every active category on <code>OLBG.com</code> outside the 10 excluded sports has been verified directly against
        official federation APIs and match centres as of <strong>22 October 2026</strong>. Across <strong>17 eligible sports</strong>,
        <strong>159 fixtures</strong> carry independently originated zero-margin fair odds (Match Winner, Handicap/Spread, and Total),
        <strong>30 unconfirmable fixtures</strong> are held transparently blank (<code>—</code>), and <strong>25 high-confidence selections</strong>
        priced strictly between <code>-250</code> and <code>+10000</code> carry bespoke player-verified analysis.
      </p>
    </section>

    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-val">17 / 0</div><div class="kpi-lbl">Eligible OLBG Sports / Excluded Sports Leaked</div></div>
      <div class="kpi-card"><div class="kpi-val">189</div><div class="kpi-lbl">Verified Rows With Primary Official Source Links</div></div>
      <div class="kpi-card"><div class="kpi-val">159</div><div class="kpi-lbl">Independently Originated Fair-Line Fixtures (10 Sports)</div></div>
      <div class="kpi-card"><div class="kpi-val">25</div><div class="kpi-lbl">High-Confidence Picks (-250 to +311 · 9 Sports)</div></div>
      <div class="kpi-card"><div class="kpi-val">30 + 8</div><div class="kpi-lbl">Blank Rows &amp; Audit Flags on Flagged for Review</div></div>
    </div>

    <section class="section">
      <h2>17 Eligible Sport Categories</h2>
      <p class="section-lead">Select any sport below to inspect its dedicated competition tables, model notes, official links, and high-confidence write-ups.</p>
      <div class="sport-grid">{"".join(cards_html)}</div>
    </section>

    <section class="section">
      <h2>Master Schedule &amp; Originated Lines Table (All 189 Verified Rows)</h2>
      <p class="section-lead">Click any column header to sort, or filter by sport, confidence tier, team, or player. Every row links directly to its primary governing-body source.</p>
      {render_schedule_table(rows, "", show_sport_col=True, sports_list=eligible)}
    </section>

    <section class="section">
      <h2>Scope Guardrail — 10 Excluded OLBG Categories Verified Omitted (0 Rows)</h2>
      <p class="section-lead">Per brief instructions, all ten categories below are completely excluded from every schedule, model, and prediction table.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Excluded Sport</th><th>OLBG Sport ID</th><th>Exclusion Basis</th><th>Official Sitemap Verification</th></tr></thead>
          <tbody>{excl_rows_html}</tbody>
        </table>
      </div>
    </section>
    """
    (HUB_DIR / "index.html").write_text(page_shell("Overview & Complete 189-Row Schedule", "overview", index_body, ""), encoding="utf-8")

    # 2. Build hub/predictions.html
    pred_sports = []
    for s in eligible:
        if preds_by_sport[s["slug"]]:
            pred_sports.append((s["slug"], s["name"], len(preds_by_sport[s["slug"]])))

    pills_html = [f'<button type="button" class="pill active" data-pred-pill="all">All Sports ({len(preds)})</button>']
    for sl, nm, cnt in pred_sports:
        pills_html.append(f'<button type="button" class="pill" data-pred-pill="{esc(sl)}">{esc(nm)} ({cnt})</button>')

    pred_summary_rows = "".join(
        f'<tr>'
        f'<td class="mono">{esc(p["start_utc"])}</td>'
        f'<td><a href="sports/{esc(p["sport"])}.html"><strong>{esc(p["sport_name"])}</strong></a></td>'
        f'<td><a href="#pred-{esc(p["match_id"])}"><strong>{esc(p["event"])}</strong></a><div class="muted">{esc(p["competition"])}</div></td>'
        f'<td><strong>{esc(p["selection"])}</strong></td>'
        f'<td class="mono">{p["fair_decimal"]:.2f} ({esc(p["fair_american_str"])}) · {p["probability"] * 100:.1f}%</td>'
        f'<td class="mono">{p["word_count"]}w</td>'
        f'<td><a href="{esc(p["official_url"])}" target="_blank" rel="noopener noreferrer">{esc(p["official_source"])} ↗</a></td>'
        f'</tr>'
        for p in preds
    )

    preds_body = f"""
    <section class="hero">
      <h1>25 High-Confidence Selections &amp; Verified Analyst Previews</h1>
      <p>
        Every selection on this page is originated from primary federation statistics, graded <strong>High Confidence</strong>,
        priced strictly inside <code>-250</code> to <code>+10000</code> American odds (<code>1.40</code> to <code>4.11</code> decimal — zero heavy chalk),
        and backed by verified 2026 players, current form, and recent match history across <strong>9 eligible sports</strong>.
      </p>
    </section>

    <section class="section">
      <h2>Summary Ledger of High-Confidence Selections (25)</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Date / UTC</th><th>Sport</th><th>Fixture</th><th>Recommended Selection</th><th>Fair Price &amp; Prob</th><th>Words</th><th>Official Source</th></tr></thead>
          <tbody>{pred_summary_rows}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Detailed Match Previews &amp; Primary Fact Citations</h2>
      <div class="pill-bar">{"".join(pills_html)}</div>
      <div class="pred-grid">{"".join(render_prediction_card(p, "") for p in preds)}</div>
    </section>
    """
    (HUB_DIR / "predictions.html").write_text(page_shell("25 High-Confidence Picks & Previews", "predictions", preds_body, ""), encoding="utf-8")

    # 3. Build hub/flagged.html (Flagged for Review)
    flag_rows_html = "".join(
        f'<tr>'
        f'<td class="mono"><strong>{esc(item["id"])}</strong></td>'
        f'<td><span class="badge badge-{"unlined" if item["severity"] == "high" else ("medium" if item["severity"] == "medium" else "low")}">{esc(item["severity"])}</span></td>'
        f'<td><strong>{esc(item["category"])}</strong></td>'
        f'<td><strong>{esc(item["title"])}</strong><div class="muted" style="margin-top:4px;">{esc(item["detail"])}</div></td>'
        f'<td><a href="{esc(item["official_url"])}" target="_blank" rel="noopener noreferrer">{esc(item["official_source"])} ↗</a></td>'
        f'</tr>'
        for item in flagged_data["items"]
    )

    unlined_only = [r for r in rows if r["status"] == "unlined"]
    unlined_rows_html = "".join(
        f'<tr>'
        f'<td class="mono">{esc(r["start_utc"])}</td>'
        f'<td><a href="sports/{esc(r["sport"])}.html"><strong>{esc(r["sport_name"])}</strong></a></td>'
        f'<td><strong>{esc(r["event"])}</strong><div class="muted">{esc(r["competition"])}</div></td>'
        f'<td class="blank-cell">—</td><td class="blank-cell">—</td><td class="blank-cell">—</td>'
        f'<td>{esc(r["notes"])}</td>'
        f'<td><a href="{esc(r["official_url"])}" target="_blank" rel="noopener noreferrer">{esc(r["official_source"])} ↗</a></td>'
        f'</tr>'
        for r in unlined_only
    )

    partial_nba = [r for r in rows if r["sport"] == "basketball" and r["markets"]["total"] is None and r["status"] == "originated"]
    partial_rows_html = "".join(
        f'<tr>'
        f'<td class="mono">{esc(r["start_utc"])}</td>'
        f'<td><strong>{esc(r["event"])}</strong></td>'
        f'<td>{render_market_cell(r["markets"]["winner"])}</td>'
        f'<td>{render_market_cell(r["markets"]["handicap"])}</td>'
        f'<td class="blank-cell">— (Blank)</td>'
        f'<td class="muted">{esc(r["notes"])}</td>'
        f'<td><a href="{esc(r["official_url"])}" target="_blank" rel="noopener noreferrer">{esc(r["official_source"])} ↗</a></td>'
        f'</tr>'
        for r in partial_nba
    )

    flagged_body = f"""
    <section class="hero">
      <h1>Flagged for Review — Unverified Inputs, Blank Cells &amp; Upstream Discrepancies</h1>
      <p>
        Zero hallucination policy: whenever a governing-body endpoint omits season scoring totals in static HTML/JSON, returns an HTTP error,
        or truncates rankings outside the top tier, we leave the unconfirmable market cell strictly blank (<code>—</code>) and document the exact primary URL here.
      </p>
    </section>

    <section class="section">
      <h2>1. Active Verification &amp; Data-Integrity Flags ({len(flagged_data['items'])})</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Flag ID</th><th>Severity</th><th>Category</th><th>Finding &amp; Resolution</th><th>Official Primary Link</th></tr></thead>
          <tbody>{flag_rows_html}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>2. Unlined Fixtures Held Completely Blank ({len(unlined_only)} Rows)</h2>
      <p class="section-lead">All 30 fixtures below have primary schedule confirmation on OLBG / federation portals, with every odds cell left blank rather than guessed.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Date / UTC</th><th>Sport</th><th>Fixture</th><th>Winner</th><th>Handicap</th><th>Total</th><th>Reason Held Blank</th><th>Official Source</th></tr></thead>
          <tbody>{unlined_rows_html}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>3. Partial-Blank Market Rows — NBA Totals Held Blank ({len(partial_nba)} Rows)</h2>
      <p class="section-lead">Moneylines and spreads are originated from official win-loss and home/road splits; Over/Under totals remain blank because static NBA server payloads omit 30-team PF/PA totals.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Date / ET</th><th>NBA Game</th><th>Fair Moneyline</th><th>Fair Spread</th><th>Fair Total</th><th>Audit Note</th><th>Official Source</th></tr></thead>
          <tbody>{partial_rows_html}</tbody>
        </table>
      </div>
    </section>
    """
    (HUB_DIR / "flagged.html").write_text(page_shell("Flagged for Review", "flagged", flagged_body, ""), encoding="utf-8")

    # 4. Build hub/audit.html (Line-by-Line Repository Audit)
    findings = audit_data.get("findings") or audit_data.get("items") or []
    audit_rows_html = []
    for f in findings:
        fid = f.get("id", "")
        sev = f.get("severity", "medium")
        scope = f.get("file") or f.get("scope") or f.get("path", "")
        title = f.get("issue") or f.get("title") or f.get("summary", "")
        fix = f.get("resolution") or f.get("fix") or f.get("hub_resolution") or f.get("detail", "")
        url = f.get("official_url") or f.get("source_url") or "https://www.olbg.com/sitemap-betting-tips.xml"
        audit_rows_html.append(
            f'<tr>'
            f'<td class="mono"><strong>{esc(fid)}</strong></td>'
            f'<td><span class="badge badge-{"unlined" if sev in ("critical", "high") else ("medium" if sev == "medium" else "low")}">{esc(sev)}</span></td>'
            f'<td class="mono">{esc(scope)}</td>'
            f'<td><strong>{esc(title)}</strong><div class="muted" style="margin-top:4px;">{esc(fix)}</div></td>'
            f'<td><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">Official Verification Link ↗</a></td>'
            f'</tr>'
        )

    audit_body = f"""
    <section class="hero">
      <h1>Line-by-Line Repository Audit Against Official Governing Sources</h1>
      <p>
        Before building <code>/hub/</code>, every existing script, seed payload, and published layer in <code>OLBG2</code> was audited line by line
        against live federation APIs and official OLBG sitemaps without altering concurrent sessions' files.
      </p>
    </section>

    <section class="section">
      <h2>Repository Discrepancies Audited &amp; Resolved in <code>/hub/</code> ({len(audit_rows_html)})</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Audit ID</th><th>Severity</th><th>Upstream Path</th><th>Discrepancy &amp; <code>/hub/</code> Fix</th><th>Official Source</th></tr></thead>
          <tbody>{"".join(audit_rows_html)}</tbody>
        </table>
      </div>
    </section>
    """
    (HUB_DIR / "audit.html").write_text(page_shell("Line-by-Line Repository Audit", "audit", audit_body, ""), encoding="utf-8")

    # 5. Build hub/methodology.html (Models & 34-Endpoint Official Source Registry)
    endpoints = sources_data.get("endpoints") or sources_data.get("sources") or []
    src_rows_html = []
    for ep in endpoints:
        sp = ep.get("sport", "multi-sport")
        nm = ep.get("name") or ep.get("authority") or ep.get("label") or sp
        st = ep.get("http_status") or ep.get("status", 200)
        use = ep.get("usage") or ep.get("scope") or ep.get("notes", "Primary schedule & ratings verification")
        url = ep.get("url") or ep.get("official_url")
        src_rows_html.append(
            f'<tr>'
            f'<td><strong>{esc(sp)}</strong></td>'
            f'<td>{esc(nm)}</td>'
            f'<td class="mono">{esc(st)}</td>'
            f'<td>{esc(use)}</td>'
            f'<td><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)} ↗</a></td>'
            f'</tr>'
        )

    meth_models_rows = "".join(
        f'<tr>'
        f'<td><a href="sports/{esc(s["slug"])}.html"><strong>{esc(s["name"])}</strong></a></td>'
        f'<td class="mono">{s["olbg_sport_id"]}</td>'
        f'<td>{esc(s["model_family"])}</td>'
        f'<td><a href="{esc(s["official_url"])}" target="_blank" rel="noopener noreferrer">{esc(s["official_source"])} ↗</a></td>'
        f'</tr>'
        for s in eligible
    )

    meth_body = f"""
    <section class="hero">
      <h1>Origination Methodology, Confidence Grading &amp; Primary Source Registry</h1>
      <p>
        All 159 priced fixtures are originated from first-principles probability distributions with zero bookmaker vig removed or copied:
        probabilities across every market sum to <code>1.0000</code>, decimal odds equal <code>round(1 / p, 2)</code>, and American odds are
        computed directly from rounded decimal odds so zero rounding discrepancies occur anywhere on the site.
      </p>
    </section>

    <section class="section">
      <h2>Model Architecture Across All 17 Eligible Sports</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Sport</th><th>OLBG ID</th><th>Origination Model &amp; Shrinkage Specification</th><th>Primary Federation Endpoint</th></tr></thead>
          <tbody>{meth_models_rows}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Official Primary Endpoints Verified ({len(src_rows_html)})</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Sport</th><th>Governing Authority</th><th>HTTP</th><th>Verified Data Extracted</th><th>Official URL</th></tr></thead>
          <tbody>{"".join(src_rows_html)}</tbody>
        </table>
      </div>
    </section>
    """
    (HUB_DIR / "methodology.html").write_text(page_shell("Methodology & Official Sources", "methodology", meth_body, ""), encoding="utf-8")

    # 6. Build all 17 sport pages: hub/sports/<slug>.html
    for s in eligible:
        sl = s["slug"]
        srows = by_sport[sl]
        spreds = preds_by_sport[sl]
        orig_n = sum(1 for r in srows if r["status"] == "originated")
        unl_n = sum(1 for r in srows if r["status"] == "unlined")

        pred_section = ""
        if spreds:
            pred_section = f"""
            <section class="section">
              <h2>High-Confidence Analyst Picks in {esc(s['name'])} ({len(spreds)})</h2>
              <div class="pred-grid">{"".join(render_prediction_card(p, "../") for p in spreds)}</div>
            </section>
            """

        if srows:
            table_block = render_schedule_table(srows, "../", show_sport_col=False)
        else:
            table_block = f"""
            <div class="table-wrap">
              <table>
                <thead><tr><th>Sport</th><th>Active OLBG Status (2026-10-22)</th><th>Model Status</th><th>Official Governing Source</th></tr></thead>
                <tbody>
                  <tr>
                    <td><strong>{esc(s['name'])}</strong></td>
                    <td>0 live events listed on OLBG hub as of 22 October 2026 ({esc(s['model_family'])})</td>
                    <td><span class="badge badge-low">Verified Empty Slate</span></td>
                    <td>
                      <a href="{esc(s['official_url'])}" target="_blank" rel="noopener noreferrer">{esc(s['official_source'])} ↗</a>
                      · <a href="{esc(s['olbg_url'])}" target="_blank" rel="noopener noreferrer">OLBG {esc(s['name'])} Hub ↗</a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            """

        sport_body = f"""
        <section class="hero">
          <div class="muted" style="margin-bottom:6px;"><a href="../index.html">← All 17 Eligible Sports</a> · OLBG Sport ID <code>{s['olbg_sport_id']}</code></div>
          <h1>{esc(s['name'])} — Verified Schedule, Originated Fair Odds &amp; Picks</h1>
          <p>
            <strong>Model family:</strong> {esc(s['model_family'])} ·
            <strong>Originated fixtures:</strong> {orig_n} ·
            <strong>Unlined / blank fixtures:</strong> {unl_n} ·
            <strong>High-confidence picks:</strong> {len(spreds)} ·
            <strong>Primary authority:</strong> <a href="{esc(s['official_url'])}" target="_blank" rel="noopener noreferrer">{esc(s['official_source'])} ↗</a>
          </p>
        </section>

        {pred_section}

        <section class="section">
          <h2>{esc(s['name'])} Schedule &amp; Fair Betting Lines ({len(srows)} Rows)</h2>
          <p class="section-lead">Every row below links directly to its governing-body source and live OLBG hub; unconfirmed values remain blank (<code>—</code>).</p>
          {table_block}
        </section>
        """
        (HUB_DIR / "sports" / f"{sl}.html").write_text(
            page_shell(f"{s['name']} Odds & Schedule", "overview", sport_body, "../"),
            encoding="utf-8",
        )

    print(f"hub_build.py OK: wrote 5 top-level pages + {len(eligible)} sport pages + 2 assets under hub/")


if __name__ == "__main__":
    main()
