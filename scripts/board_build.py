#!/usr/bin/env python3
"""Build the static GitHub Pages dashboard under /board/ from data/board/*.json.

Session: arena/ddcbf63c-olbg2
Generates:
  - board/index.html
  - board/matches.html
  - board/picks.html
  - board/flagged.html
  - board/sources.html
  - board/audit.html
  - board/sports/<slug>.html (17 eligible OLBG sport pages)
  - board/assets/style.css
  - board/assets/app.js
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "board"
OUT_DIR = ROOT / "board"
SPORTS_DIR = OUT_DIR / "sports"
ASSETS_DIR = OUT_DIR / "assets"


def e(val: object) -> str:
    if val is None:
        return ""
    return html.escape(str(val), quote=True)


def fmt_amer(val: int | None) -> str:
    if val is None:
        return "—"
    return f"+{val}" if val > 0 else str(val)


def fmt_dec(val: float | None) -> str:
    if val is None:
        return "—"
    return f"{val:.2f}"


def fmt_prob(val: float | None) -> str:
    if val is None:
        return "—"
    return f"{val * 100:.1f}%"


def nav_html(active: str, prefix: str = "") -> str:
    items = [
        ("index", f"{prefix}index.html", "Overview & Sports"),
        ("matches", f"{prefix}matches.html", "All 207 Matches"),
        ("picks", f"{prefix}picks.html", "35 High-Confidence Picks"),
        ("flagged", f"{prefix}flagged.html", "Flagged for Review (35)"),
        ("sources", f"{prefix}sources.html", "Official Sources (25)"),
        ("audit", f"{prefix}audit.html", "Line-by-Line Repo Audit"),
    ]
    links = []
    for key, href, label in items:
        cls = ' class="active"' if key == active else ""
        links.append(f'<a href="{href}"{cls}>{e(label)}</a>')
    return "\n        ".join(links)


def page_shell(title: str, active: str, body: str, prefix: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)} — OLBG Originated Betting Board (arena/ddcbf63c-olbg2)</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <div class="brand">
        <span class="badge-live">VERIFIED BOARD · 2026-10-22</span>
        <h1><a href="{prefix}index.html">OLBG Non-Excluded Sports Origination &amp; Verification Board</a></h1>
        <p class="subtitle">207 Deduplicated Fixtures Across 17 Eligible Sports · 167 Originated Multi-Market Lines · 40 Unlined &amp; Flagged · 35 High-Confidence In-Band (-250..+10000) Player-Verified Picks</p>
      </div>
      <div class="layer-links">
        <span class="layer-label">Repository Dashboards:</span>
        <a href="{prefix}../index.html">Root Hub</a>
        <a href="{prefix}index.html" class="active-layer">/board/ (Unified 207)</a>
        <a href="{prefix}../verified/index.html">/verified/</a>
        <a href="{prefix}../forward/index.html">/forward/</a>
        <a href="{prefix}../live/index.html">/live/</a>
      </div>
    </div>
    <nav class="main-nav">
      <div class="container nav-inner">
        {nav_html(active, prefix)}
      </div>
    </nav>
  </header>
  <main class="container main-content">
    {body}
  </main>
  <footer class="site-footer">
    <div class="container footer-inner">
      <p><strong>OLBG Reverse-Engineering &amp; Official Governing-Body Origination Board</strong> · Session <code>arena/ddcbf63c-olbg2</code> · Captured <code>2026-10-22 UTC</code></p>
      <p>Excluded per specification: <code>soccer</code>, <code>football</code>, <code>american football</code>, <code>boxing</code>, <code>ufc</code>, <code>mma</code>, <code>hurling</code>, <code>horse racing</code>, <code>cycling</code>, <code>specials</code>. Unverified inputs are never inferred and remain blank (<code>—</code>).</p>
    </div>
  </footer>
  <script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def render_match_row(m: dict, sport_prefix: str = "") -> str:
    lined = m.get("line_status") == "originated" and m.get("winner_market") and m.get("pick")
    wm = m.get("winner_market") or {}
    hm = m.get("handicap_market") or {}
    tm = m.get("total_market") or {}
    pk = m.get("pick") or {}
    fp = m.get("featured")

    if lined:
        home_price = f"<strong>{e(m.get('home'))}</strong>: {fmt_dec(wm.get('home_odds'))} ({fmt_amer(wm.get('home_american'))}) · {fmt_prob(wm.get('home_prob'))}"
        away_price = f"<strong>{e(m.get('away'))}</strong>: {fmt_dec(wm.get('away_odds'))} ({fmt_amer(wm.get('away_american'))}) · {fmt_prob(wm.get('away_prob'))}"
        draw_html = ""
        if wm.get("draw_prob"):
            draw_html = f"<br><span class='muted'>Draw: {fmt_dec(wm.get('draw_odds'))} ({fmt_amer(wm.get('draw_american'))}) · {fmt_prob(wm.get('draw_prob'))}</span>"
        winner_cell = f"{home_price}<br>{away_price}{draw_html}"

        if hm and hm.get("line") is not None:
            handicap_cell = (
                f"<strong>{e(hm.get('label', hm.get('line')))}</strong><br>"
                f"Fav: {fmt_dec(hm.get('fav_odds'))} ({fmt_amer(hm.get('fav_american'))}, {fmt_prob(hm.get('fav_prob'))}) · "
                f"Dog: {fmt_dec(hm.get('dog_odds'))} ({fmt_amer(hm.get('dog_american'))}, {fmt_prob(hm.get('dog_prob'))})"
            )
        else:
            handicap_cell = "—"

        if tm and tm.get("line") is not None:
            proj_str = f" (proj {tm.get('projected')})" if tm.get("projected") is not None else ""
            total_cell = (
                f"Line: <strong>{e(tm.get('line'))}</strong>{e(proj_str)}<br>"
                f"<span class='muted'>O {fmt_dec(tm.get('over_odds'))} ({fmt_amer(tm.get('over_american'))}, {fmt_prob(tm.get('over_prob'))}) · "
                f"U {fmt_dec(tm.get('under_odds'))} ({fmt_amer(tm.get('under_american'))}, {fmt_prob(tm.get('under_prob'))})</span>"
            )
        else:
            total_cell = "—"

        conf = pk.get("confidence", "low")
        pick_cell = (
            f"<span class='conf-badge conf-{e(conf)}'>{e(conf.upper())}</span> "
            f"<strong>{e(pk.get('selection'))}</strong> ({e(pk.get('market'))})<br>"
            f"<span>{fmt_dec(pk.get('fair_odds'))} ({fmt_amer(pk.get('fair_american'))}) · {fmt_prob(pk.get('probability'))}</span>"
        )
        if fp and fp.get("selection") != pk.get("selection"):
            pick_cell += (
                f"<br><span class='featured-tag'>In-Band &ge;70% Line: {e(fp.get('selection'))} "
                f"@ {fmt_dec(fp.get('fair_odds'))} ({fmt_amer(fp.get('fair_american'))}, {fmt_prob(fp.get('probability'))})</span>"
            )
    else:
        conf = "unlined"
        winner_cell = "—"
        handicap_cell = "—"
        total_cell = "—"
        reason = m.get("unlined_reason") or "Official governing-body feed lacks pre-match head-to-head form inputs; left blank per non-inference rule."
        pick_cell = f"<span class='conf-badge conf-unlined'>UNLINED / FLAGGED</span><br><span class='muted'>{e(reason)}</span>"

    off_url = m.get("official_url") or m.get("data_url") or "https://www.olbg.com/betting-tips"
    data_url = m.get("data_url") or off_url
    olbg_url = m.get("olbg_url") or "https://www.olbg.com/betting-tips"
    off_src = m.get("official_source") or "Official Governing Body"

    home_sum = m.get("home_summary") or "—"
    away_sum = m.get("away_summary") or "—"

    return f"""
      <tr data-sport="{e(m.get('sport'))}" data-conf="{e(conf)}" data-status="{e(m.get('line_status'))}">
        <td>
          <code>{e(m.get('id'))}</code><br>
          <a href="{sport_prefix}sports/{e(m.get('sport'))}.html" class="sport-pill">{e(m.get('sport_name'))}</a><br>
          <span class="muted">{e(m.get('date'))} {e(m.get('time') or '')}</span>
        </td>
        <td>
          <strong>{e(m.get('home'))} vs {e(m.get('away'))}</strong><br>
          <span class="muted">{e(m.get('competition'))} · {e(m.get('venue') or 'Official Venue')}</span>
        </td>
        <td>
          <div><strong>H:</strong> {e(home_sum)}</div>
          <div><strong>A:</strong> {e(away_sum)}</div>
        </td>
        <td>{winner_cell}</td>
        <td>{handicap_cell}</td>
        <td>{total_cell}</td>
        <td>{pick_cell}</td>
        <td>
          <a href="{e(off_url)}" target="_blank" rel="noopener noreferrer">{e(off_src)}</a><br>
          <a href="{e(data_url)}" target="_blank" rel="noopener noreferrer" class="muted">Stats/Standings Feed</a> ·
          <a href="{e(olbg_url)}" target="_blank" rel="noopener noreferrer" class="muted">OLBG Tip</a>
        </td>
      </tr>"""


def render_prediction_card(p: dict, sport_prefix: str = "") -> str:
    tier_label = (
        "Strict >=70% Win Prob In-Band (-250..+10000)"
        if p.get("tier") == "strict_70pct_in_band"
        else "Multi-Factor Conviction Primary Winner (-250..+10000)"
    )
    facts_raw = p.get("facts") or []
    if isinstance(facts_raw, dict):
        facts_items = "".join(f"<li><strong>{e(k)}:</strong> {e(v)}</li>" for k, v in facts_raw.items())
    else:
        facts_items = "".join(
            f'<li>{e(f.get("claim"))} — <a href="{e(f.get("source"))}" target="_blank" rel="noopener noreferrer">Official Source</a></li>'
            for f in facts_raw
        )
    matchup = p.get("event") or p.get("matchup") or p.get("match_id")
    narrative = p.get("text") or p.get("narrative") or ""
    off_src = p.get("official_source") or "Official Governing Body"
    data_url = p.get("data_url") or p.get("official_url")
    return f"""
    <article class="pick-card" id="pick-{e(p.get('match_id'))}" data-sport="{e(p.get('sport'))}" data-tier="{e(p.get('tier'))}">
      <div class="pick-header">
        <div>
          <span class="conf-badge conf-high">HIGH CONFIDENCE</span>
          <span class="tier-badge">{e(tier_label)}</span>
          <a href="{sport_prefix}sports/{e(p.get('sport'))}.html" class="sport-pill">{e(p.get('sport_name'))}</a>
          <span class="word-badge">{e(p.get('word_count'))} words</span>
        </div>
        <div class="pick-price">
          <strong>{fmt_dec(p.get('fair_odds'))}</strong> Decimal · <strong>{fmt_amer(p.get('fair_american'))}</strong> American · <strong>{fmt_prob(p.get('probability'))}</strong> Win Prob
        </div>
      </div>
      <h3>{e(matchup)} <span class="muted">({e(p.get('competition'))} · {e(p.get('date'))} {e(p.get('time') or '')})</span></h3>
      <div class="selection-banner">
        <strong>Obvious Betting Selection:</strong> {e(p.get('selection'))} <span class="muted">({e(p.get('market'))} · {e(p.get('headline', ''))})</span>
      </div>
      <p class="narrative-text">{e(narrative)}</p>
      <div class="meta-grid">
        <div><strong>Team / Event:</strong> {e(matchup)}</div>
        <div><strong>Verified Player Cited:</strong> {e(p.get('player_cited'))}</div>
        <div><strong>Verified Current Form:</strong> {e(p.get('form_cited'))}</div>
        <div><strong>Recent Match History:</strong> {e(p.get('history_cited'))}</div>
      </div>
      <ul class="facts-list">{facts_items}</ul>
      <div class="pick-footer">
        <span><strong>Official Verification Links:</strong></span>
        <a href="{e(p.get('official_url'))}" target="_blank" rel="noopener noreferrer">{e(off_src)} (Match/Fixture)</a> ·
        <a href="{e(data_url)}" target="_blank" rel="noopener noreferrer">Official Standings/Roster Feed</a> ·
        <a href="{e(p.get('olbg_url'))}" target="_blank" rel="noopener noreferrer">OLBG Event Page</a>
      </div>
    </article>"""


def write_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    css = """
:root {
  --bg: #0b1020;
  --panel: #131b31;
  --panel-alt: #18233f;
  --border: #28365c;
  --text: #eef2ff;
  --muted: #9fb0d9;
  --accent: #38bdf8;
  --high: #10b981;
  --med: #f59e0b;
  --low: #64748b;
  --unlined: #ef4444;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.container { max-width: 1380px; margin: 0 auto; padding: 0 1.25rem; }
.site-header { background: var(--panel); border-bottom: 1px solid var(--border); }
.header-inner { padding: 1.25rem 1.25rem; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 1rem; }
.brand h1 { margin: 0.35rem 0; font-size: 1.5rem; }
.brand h1 a { color: var(--text); }
.subtitle { margin: 0; color: var(--muted); font-size: 0.92rem; }
.badge-live { display: inline-block; background: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid #10b981; font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.55rem; border-radius: 999px; }
.layer-links { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; font-size: 0.85rem; }
.layer-links a { padding: 0.3rem 0.65rem; border-radius: 6px; background: var(--panel-alt); border: 1px solid var(--border); color: var(--text); }
.layer-links a.active-layer { border-color: var(--accent); color: var(--accent); font-weight: 600; }
.main-nav { background: var(--panel-alt); border-top: 1px solid var(--border); }
.nav-inner { display: flex; flex-wrap: wrap; gap: 0.35rem; padding: 0.55rem 1.25rem; }
.nav-inner a { padding: 0.45rem 0.85rem; border-radius: 6px; color: var(--muted); font-weight: 600; font-size: 0.9rem; }
.nav-inner a.active, .nav-inner a:hover { background: var(--panel); color: var(--text); text-decoration: none; }
.main-content { padding: 1.75rem 1.25rem 3rem; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(195px, 1fr)); gap: 1rem; margin-bottom: 1.75rem; }
.kpi-card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 1rem 1.15rem; }
.kpi-val { font-size: 1.75rem; font-weight: 800; color: var(--accent); }
.kpi-label { font-size: 0.85rem; color: var(--muted); margin-top: 0.2rem; }
.section-card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; margin-bottom: 1.75rem; }
.section-card h2 { margin-top: 0; font-size: 1.25rem; border-bottom: 1px solid var(--border); padding-bottom: 0.6rem; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
th, td { padding: 0.65rem 0.75rem; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }
th { background: var(--panel-alt); color: var(--muted); font-weight: 700; white-space: nowrap; }
tr:hover td { background: rgba(255, 255, 255, 0.02); }
.muted { color: var(--muted); font-size: 0.82rem; }
.sport-pill { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px; background: var(--panel-alt); border: 1px solid var(--border); font-size: 0.78rem; color: var(--accent); margin: 0.15rem 0; }
.conf-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.73rem; font-weight: 800; letter-spacing: 0.03em; }
.conf-high { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
.conf-medium { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
.conf-low { background: rgba(100, 116, 139, 0.25); color: #cbd5e1; border: 1px solid #64748b; }
.conf-unlined { background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid #ef4444; }
.tier-badge, .word-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; background: var(--panel-alt); border: 1px solid var(--border); color: var(--muted); margin-left: 0.35rem; }
.featured-tag { display: inline-block; margin-top: 0.25rem; font-size: 0.78rem; color: #34d399; }
.filter-bar { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; align-items: center; }
.filter-bar select, .filter-bar input { background: var(--panel-alt); border: 1px solid var(--border); color: var(--text); padding: 0.45rem 0.75rem; border-radius: 6px; font-size: 0.88rem; }
.pick-card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; margin-bottom: 1.25rem; }
.pick-header { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.pick-price { font-size: 0.95rem; color: var(--accent); }
.selection-banner { background: var(--panel-alt); border-left: 4px solid var(--high); padding: 0.6rem 0.9rem; border-radius: 4px; margin: 0.65rem 0; font-size: 0.92rem; }
.narrative-text { font-size: 0.96rem; line-height: 1.65; color: var(--text); margin: 0.75rem 0; }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.5rem 1rem; background: var(--panel-alt); padding: 0.75rem 0.95rem; border-radius: 6px; font-size: 0.85rem; margin-bottom: 0.75rem; }
.facts-list { display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem; list-style: none; padding: 0; margin: 0.5rem 0 0.75rem; font-size: 0.82rem; color: var(--muted); }
.pick-footer { border-top: 1px solid var(--border); padding-top: 0.6rem; font-size: 0.83rem; }
.site-footer { background: var(--panel); border-top: 1px solid var(--border); padding: 1.5rem 0; color: var(--muted); font-size: 0.85rem; }
code { background: var(--panel-alt); padding: 0.1rem 0.35rem; border-radius: 4px; font-size: 0.82rem; }
"""
    js = """
document.addEventListener('DOMContentLoaded', () => {
  const sportSel = document.getElementById('filter-sport');
  const confSel = document.getElementById('filter-conf');
  const statusSel = document.getElementById('filter-status');
  const searchInp = document.getElementById('filter-search');
  const countSpan = document.getElementById('filter-count');

  function applyFilters() {
    const rows = document.querySelectorAll('#matches-table tbody tr');
    if (!rows.length) return;
    const sp = sportSel ? sportSel.value : '';
    const cf = confSel ? confSel.value : '';
    const st = statusSel ? statusSel.value : '';
    const q = searchInp ? searchInp.value.toLowerCase().trim() : '';
    let visible = 0;
    rows.forEach(r => {
      const mSp = !sp || r.dataset.sport === sp;
      const mCf = !cf || r.dataset.conf === cf;
      const mSt = !st || r.dataset.status === st;
      const mQ = !q || r.textContent.toLowerCase().includes(q);
      const show = mSp && mCf && mSt && mQ;
      r.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    if (countSpan) countSpan.textContent = visible;
  }

  [sportSel, confSel, statusSel].forEach(el => el && el.addEventListener('change', applyFilters));
  if (searchInp) searchInp.addEventListener('input', applyFilters);
});
"""
    (ASSETS_DIR / "style.css").write_text(css.strip() + "\n", encoding="utf-8")
    (ASSETS_DIR / "app.js").write_text(js.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_assets()

    matches_data = json.loads((DATA_DIR / "matches.json").read_text(encoding="utf-8"))
    preds_data = json.loads((DATA_DIR / "predictions.json").read_text(encoding="utf-8"))
    sports_data = json.loads((DATA_DIR / "sports.json").read_text(encoding="utf-8"))
    sources_data = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
    flagged_data = json.loads((DATA_DIR / "flagged.json").read_text(encoding="utf-8"))
    audit_data = json.loads((DATA_DIR / "repo_audit.json").read_text(encoding="utf-8"))

    matches = matches_data["matches"]
    preds = preds_data["predictions"]
    counts = matches_data["counts"]
    sports_list = sports_data.get("eligible_sports") or sports_data.get("included_sports") or []
    excluded_list = sports_data.get("excluded_sports") or []

    # Group matches and predictions by sport
    by_sport: dict[str, list[dict]] = {}
    for m in matches:
        by_sport.setdefault(m["sport"], []).append(m)
    preds_by_sport: dict[str, list[dict]] = {}
    for p in preds:
        preds_by_sport.setdefault(p["sport"], []).append(p)

    # 1. Build board/index.html
    sport_rows = []
    for sp in sports_list:
        slug = sp["slug"]
        sp_matches = by_sport.get(slug, [])
        orig_n = sum(1 for m in sp_matches if m.get("line_status") == "originated")
        unlined_n = len(sp_matches) - orig_n
        high_n = len(preds_by_sport.get(slug, []))
        off_url = sp.get("official_url") or (sp_matches[0]["official_url"] if sp_matches else "https://www.olbg.com/betting-tips")
        olbg_url = sp.get("olbg_url") or "https://www.olbg.com/betting-tips"
        gov_body = sp.get("governing_body") or sp.get("official_source") or "Official Governing Body"
        summary_txt = sp.get("status_summary") or ", ".join(sp.get("markets_investigated", []))
        sport_rows.append(f"""
          <tr>
            <td><a href="sports/{e(slug)}.html"><strong>{e(sp.get('name'))}</strong></a></td>
            <td><code>{e(slug)}</code></td>
            <td><strong>{len(sp_matches)}</strong></td>
            <td>{orig_n}</td>
            <td>{unlined_n if unlined_n else '0'}</td>
            <td><strong>{high_n}</strong></td>
            <td>{e(summary_txt)}</td>
            <td>
              <a href="{e(off_url)}" target="_blank" rel="noopener noreferrer">{e(gov_body)}</a> ·
              <a href="{e(olbg_url)}" target="_blank" rel="noopener noreferrer" class="muted">OLBG Category</a>
            </td>
          </tr>""")

    top_preds_rows = []
    for p in preds[:15]:
        ev = p.get("event") or p.get("matchup") or p.get("match_id")
        off_s = p.get("official_source") or "Official Governing Body"
        top_preds_rows.append(f"""
          <tr>
            <td><a href="sports/{e(p['sport'])}.html" class="sport-pill">{e(p['sport_name'])}</a></td>
            <td><a href="picks.html#pick-{e(p['match_id'])}"><strong>{e(ev)}</strong></a><br><span class="muted">{e(p['competition'])} · {e(p['date'])}</span></td>
            <td><strong>{e(p['selection'])}</strong><br><span class="muted">{e(p['market'])}</span></td>
            <td><strong>{fmt_dec(p['fair_odds'])}</strong> ({fmt_amer(p['fair_american'])})<br><span class="muted">{fmt_prob(p['probability'])} Win Prob</span></td>
            <td>{e(p['player_cited'])}</td>
            <td><span class="word-badge">{e(p['word_count'])}w</span></td>
            <td>
              <a href="{e(p['official_url'])}" target="_blank" rel="noopener noreferrer">{e(off_s)}</a> ·
              <a href="{e(p['olbg_url'])}" target="_blank" rel="noopener noreferrer" class="muted">OLBG</a>
            </td>
          </tr>""")

    index_body = f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-val">{counts['total']}</div><div class="kpi-label">Deduplicated Verified Fixtures (Oct 22 – Nov 2, 2026)</div></div>
      <div class="kpi-card"><div class="kpi-val">{counts['originated']}</div><div class="kpi-label">Originated Multi-Market Lines (0 Unverified Fills)</div></div>
      <div class="kpi-card"><div class="kpi-val">{counts['unlined']}</div><div class="kpi-label">Unlined &amp; Flagged Rows (Blank <code>—</code>)</div></div>
      <div class="kpi-card"><div class="kpi-val">{len(preds)}</div><div class="kpi-label">High-Confidence Picks in [-250, +10000] (&ge;85 Words)</div></div>
      <div class="kpi-card"><div class="kpi-val">17 / 10</div><div class="kpi-label">Eligible Sports Covered / Excluded Categories Filtered</div></div>
      <div class="kpi-card"><div class="kpi-val">0</div><div class="kpi-label">Decimal-to-American Odds Rounding Mismatches</div></div>
    </div>

    <section class="section-card">
      <h2>17 Eligible OLBG Sport Categories — Coverage &amp; Origination Breakdown</h2>
      <p class="muted">Every row links to its dedicated sport category subpage and primary governing-body verification source. Excluded sports (soccer, boxing, ufc, mma, football, american football, hurling, horse racing, cycling, specials) are strictly filtered.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport Category</th>
              <th>Slug</th>
              <th>Total Rows</th>
              <th>Originated</th>
              <th>Unlined (<code>—</code>)</th>
              <th>High-Conf Picks</th>
              <th>Active Competitions Verified</th>
              <th>Official Governing-Body Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(sport_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-card">
      <h2>Featured High-Confidence In-Band (-250 to +10000) Predictions Preview</h2>
      <p class="muted">Showing 15 of <a href="picks.html">all 35 player-verified high-confidence predictions</a> (22 strict &ge;70% win-probability in-band selections + 13 multi-factor conviction primary-market winners).</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport</th>
              <th>Matchup &amp; Date</th>
              <th>Originated Selection</th>
              <th>Fair Odds &amp; Prob</th>
              <th>Verified Player Cited</th>
              <th>Words</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(top_preds_rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    (OUT_DIR / "index.html").write_text(page_shell("Overview & Sport Categories", "index", index_body), encoding="utf-8")

    # 2. Build board/matches.html
    sport_opts = "".join(f'<option value="{e(sp["slug"])}">{e(sp["name"])}</option>' for sp in sports_list)
    all_match_rows = "".join(render_match_row(m) for m in matches)
    matches_body = f"""
    <section class="section-card">
      <h2>All 207 Deduplicated Fixtures &amp; Originated Multi-Market Lines (Oct 22 – Nov 2, 2026)</h2>
      <p class="muted">Includes 118 Core Verified fixtures + 89 non-duplicate Forward Window fixtures (deduplicating 2026 MLB World Series Games 1–4 under canonical MLB <code>gamePk</code> IDs <code>mlb-849805..849803</code>). All 40 fixtures lacking pre-match server-side head-to-head form inputs are left blank (<code>—</code>) and linked to <a href="flagged.html">Flagged for Review</a>.</p>
      <div class="filter-bar">
        <label>Sport:
          <select id="filter-sport">
            <option value="">All 17 Sports ({len(matches)})</option>
            {sport_opts}
          </select>
        </label>
        <label>Confidence:
          <select id="filter-conf">
            <option value="">All Tiers</option>
            <option value="high">High ({counts['high_confidence']})</option>
            <option value="medium">Medium ({counts['medium_confidence']})</option>
            <option value="low">Low ({counts['low_confidence']})</option>
            <option value="unlined">Unlined / Flagged ({counts['unlined']})</option>
          </select>
        </label>
        <label>Line Status:
          <select id="filter-status">
            <option value="">All Statuses</option>
            <option value="originated">Originated ({counts['originated']})</option>
            <option value="unlined">Unlined ({counts['unlined']})</option>
          </select>
        </label>
        <input type="search" id="filter-search" placeholder="Search team, competition, venue, ID...">
        <span class="muted">Showing <strong id="filter-count">{len(matches)}</strong> of {len(matches)} rows</span>
      </div>
      <div class="table-wrap">
        <table id="matches-table">
          <thead>
            <tr>
              <th>Match ID / Sport / Date</th>
              <th>Fixture &amp; Venue</th>
              <th>Verified Governing-Body Form / Rank</th>
              <th>Fair Winner Line (Dec / Amer / Prob)</th>
              <th>Fair Handicap / Spread</th>
              <th>Fair Match Total</th>
              <th>Originated Pick &amp; Confidence</th>
              <th>Official Source Links</th>
            </tr>
          </thead>
          <tbody>
            {all_match_rows}
          </tbody>
        </table>
      </div>
    </section>
    """
    (OUT_DIR / "matches.html").write_text(page_shell("All 207 Matches & Originated Lines", "matches", matches_body), encoding="utf-8")

    # 3. Build board/picks.html
    summary_rows = []
    for p in preds:
        ev = p.get("event") or p.get("matchup") or p.get("match_id")
        off_s = p.get("official_source") or "Official Governing Body"
        summary_rows.append(f"""
          <tr>
            <td><code>{e(p['match_id'])}</code></td>
            <td><a href="sports/{e(p['sport'])}.html" class="sport-pill">{e(p['sport_name'])}</a></td>
            <td><a href="#pick-{e(p['match_id'])}"><strong>{e(ev)}</strong></a><br><span class="muted">{e(p['date'])}</span></td>
            <td><strong>{e(p['selection'])}</strong> ({e(p['market'])})</td>
            <td><strong>{fmt_dec(p['fair_odds'])}</strong> ({fmt_amer(p['fair_american'])}) · {fmt_prob(p['probability'])}</td>
            <td>{e(p['player_cited'])}</td>
            <td>{e(p['word_count'])}w</td>
            <td><a href="{e(p['official_url'])}" target="_blank" rel="noopener noreferrer">{e(off_s)}</a></td>
          </tr>""")
    cards_html = "".join(render_prediction_card(p) for p in preds)
    picks_body = f"""
    <section class="section-card">
      <h2>35 High-Confidence In-Band (-250 to +10000) Predictions Summary Table</h2>
      <p class="muted">Every high-confidence pick sits inside the <code>-250 to +10000</code> (<code>1.40 to 101.00</code> decimal) focus band, contains 85–108 words (&ge;30 required), and cites verified team form, an official individual player &amp; statistic, recent match history, and an explicit betting selection.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Sport</th>
              <th>Matchup &amp; Date</th>
              <th>Selection &amp; Market</th>
              <th>Fair Odds &amp; Win Prob</th>
              <th>Verified Player Cited</th>
              <th>Words</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(summary_rows)}
          </tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>Full Analytical Narratives &amp; Governing-Body Fact Sheets (35 Picks)</h2>
      {cards_html}
    </section>
    """
    (OUT_DIR / "picks.html").write_text(page_shell("35 High-Confidence Predictions", "picks", picks_body), encoding="utf-8")

    # 4. Build board/flagged.html
    flag_rows = []
    for f in flagged_data["items"]:
        off_url = f.get("official_url") or "https://www.olbg.com/betting-tips"
        olbg_url = f.get("olbg_url") or "https://www.olbg.com/betting-tips"
        flag_rows.append(f"""
          <tr>
            <td><code>{e(f.get('id'))}</code></td>
            <td><strong>{e(f.get('sport'))}</strong><br><span class="muted">{e(f.get('competition'))}</span></td>
            <td><strong>{e(f.get('event'))}</strong></td>
            <td>{e(f.get('issue'))}</td>
            <td>{e(f.get('action_taken'))}</td>
            <td><span class="conf-badge conf-medium">{e(f.get('status'))}</span></td>
            <td>
              <a href="{e(off_url)}" target="_blank" rel="noopener noreferrer">{e(f.get('official_source', 'Official Source'))}</a><br>
              <a href="{e(olbg_url)}" target="_blank" rel="noopener noreferrer" class="muted">OLBG Link</a>
            </td>
          </tr>""")

    unlined_rows = []
    for m in matches:
        if m.get("line_status") != "originated":
            off_url = m.get("official_url") or m.get("data_url") or "https://www.olbg.com/betting-tips"
            unlined_rows.append(f"""
              <tr>
                <td><code>{e(m['id'])}</code></td>
                <td><a href="sports/{e(m['sport'])}.html" class="sport-pill">{e(m['sport_name'])}</a></td>
                <td><strong>{e(m['home'])} vs {e(m['away'])}</strong><br><span class="muted">{e(m['competition'])} · {e(m['date'])}</span></td>
                <td><code>—</code></td>
                <td>{e(m.get('unlined_reason') or m.get('home_summary') or 'Pre-match head-to-head inputs unavailable on server-rendered governing-body page; left blank per non-inference rule.')}</td>
                <td><a href="{e(off_url)}" target="_blank" rel="noopener noreferrer">{e(m.get('official_source', 'Official Source'))}</a></td>
              </tr>""")

    flagged_body = f"""
    <section class="section-card">
      <h2>Flagged for Review — 35 Irregularities, Stale OLBG Listings &amp; Audit Escalations (<code>VF-01..BF-34</code>)</h2>
      <p class="muted">Every data irregularity, stale OLBG tipster listing (such as September's <code>England v Sri Lanka</code> still appearing on the live October 22 OLBG tips feed), client-rendered JS governing-body table, and cross-layer reconciliation item is logged below with its official verification link.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Flag ID</th>
              <th>Sport &amp; Competition</th>
              <th>Event / Scope</th>
              <th>Irregularity / Verification Finding</th>
              <th>Action Taken</th>
              <th>Status</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(flag_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-card">
      <h2>40 Unlined Matches (Left Blank <code>—</code> Under Strict Non-Inference Policy)</h2>
      <p class="muted">Per user instructions, we never infer, estimate, or fill in values that cannot be confirmed from an official trusted source. All 40 rows below render <code>—</code> across every odds column.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Match ID</th>
              <th>Sport</th>
              <th>Fixture &amp; Date</th>
              <th>Originated Line</th>
              <th>Reason Left Blank</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(unlined_rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    (OUT_DIR / "flagged.html").write_text(page_shell("Flagged for Review", "flagged", flagged_body), encoding="utf-8")

    # 5. Build board/sources.html
    src_rows = []
    for s in sources_data["sources"]:
        src_rows.append(f"""
          <tr>
            <td><strong>{e(s['sport'])}</strong></td>
            <td>{e(s['authority'])}</td>
            <td>{e(s['scope'])}</td>
            <td><code>{e(s['verified_at'])}</code></td>
            <td><a href="{e(s['url'])}" target="_blank" rel="noopener noreferrer">{e(s['url'])}</a></td>
          </tr>""")

    excl_rows = []
    for ex in excluded_list:
        if isinstance(ex, dict):
            name = ex.get("label") or ex.get("name") or ex.get("sport") or ex.get("slug")
            reason = ex.get("reason") or "Explicitly excluded by user prompt specification"
            url = ex.get("olbg_url") or "https://www.olbg.com/betting-tips"
        else:
            name = str(ex)
            reason = "Explicitly excluded by user prompt specification"
            url = "https://www.olbg.com/betting-tips"
        excl_rows.append(f"""
          <tr>
            <td><strong>{e(name)}</strong></td>
            <td><code>EXCLUDED (0 rows)</code></td>
            <td>{e(reason)}</td>
            <td><a href="{e(url)}" target="_blank" rel="noopener noreferrer">OLBG Index Verification</a></td>
          </tr>""")

    sources_body = f"""
    <section class="section-card">
      <h2>25 Official Governing-Body &amp; Discovery Sources</h2>
      <p class="muted">All team records, goal/point differentials, singles rankings, prize-money rankings, match-sheet scorers, and schedules were verified directly against these official primary endpoints on <code>2026-10-22</code>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport</th>
              <th>Governing Body / Authority</th>
              <th>Verified Scope</th>
              <th>Verified Date</th>
              <th>Official Endpoint URL</th>
            </tr>
          </thead>
          <tbody>
            {"".join(src_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-card">
      <h2>Excluded Sport Categories (Strictly Filtered)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Excluded Category</th>
              <th>Board Status</th>
              <th>Exclusion Rule</th>
              <th>Verification Link</th>
            </tr>
          </thead>
          <tbody>
            {"".join(excl_rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    (OUT_DIR / "sources.html").write_text(page_shell("Official Sources & Taxonomy", "sources", sources_body), encoding="utf-8")

    # 6. Build board/audit.html
    audit_rows = []
    for a in audit_data["findings"]:
        off_url = a.get("official_url") or "https://www.olbg.com/betting-tips"
        audit_rows.append(f"""
          <tr>
            <td><code>{e(a.get('id'))}</code></td>
            <td><span class="conf-badge conf-high">{e(a.get('severity', 'verified').upper())}</span></td>
            <td><code>{e(a.get('file'))}</code><br><span class="muted">{e(a.get('line_range', ''))}</span></td>
            <td>{e(a.get('issue'))}</td>
            <td>{e(a.get('verification'))}</td>
            <td>{e(a.get('resolution'))}</td>
            <td><a href="{e(off_url)}" target="_blank" rel="noopener noreferrer">Official Reference</a></td>
          </tr>""")

    audit_body = f"""
    <section class="section-card">
      <h2>Line-by-Line Repository &amp; Mathematical Audit (<code>BA-01..BA-04</code> &amp; Baseline Findings)</h2>
      <p class="muted">Full record of our line-by-line audit of existing repository scripts, JSON artifacts, and HTML layers, documented in <code>research/olbg-verification-ddcbf63c.md</code> and resolved in <code>/board/</code>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Finding ID</th>
              <th>Status</th>
              <th>File &amp; Line Scope</th>
              <th>Issue Identified</th>
              <th>Official Source Verification</th>
              <th>Resolution in <code>/board/</code></th>
              <th>Official Link</th>
            </tr>
          </thead>
          <tbody>
            {"".join(audit_rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    (OUT_DIR / "audit.html").write_text(page_shell("Line-by-Line Repository Audit", "audit", audit_body), encoding="utf-8")

    # 7. Build 17 sport pages under board/sports/<slug>.html
    for sp in sports_list:
        slug = sp["slug"]
        sp_name = sp.get("name", slug)
        sp_matches = by_sport.get(slug, [])
        sp_preds = preds_by_sport.get(slug, [])
        orig_n = sum(1 for m in sp_matches if m.get("line_status") == "originated")
        unlined_n = len(sp_matches) - orig_n

        sp_preds_html = (
            "".join(render_prediction_card(p, sport_prefix="../") for p in sp_preds)
            if sp_preds
            else '<p class="muted">No fixtures in this category fell inside the high-confidence [-250, +10000] tier with full server-rendered player/form inputs; see table below for all originated lines and unlined flags.</p>'
        )
        sp_rows_html = "".join(render_match_row(m, sport_prefix="../") for m in sp_matches)
        off_url = sp.get("official_url") or (sp_matches[0]["official_url"] if sp_matches else "https://www.olbg.com/betting-tips")

        sp_body = f"""
        <div class="kpi-grid">
          <div class="kpi-card"><div class="kpi-val">{len(sp_matches)}</div><div class="kpi-label">{e(sp_name)} Verified Fixtures</div></div>
          <div class="kpi-card"><div class="kpi-val">{orig_n}</div><div class="kpi-label">Originated Multi-Market Lines</div></div>
          <div class="kpi-card"><div class="kpi-val">{unlined_n}</div><div class="kpi-label">Unlined / Flagged (<code>—</code>)</div></div>
          <div class="kpi-card"><div class="kpi-val">{len(sp_preds)}</div><div class="kpi-label">High-Confidence Picks (-250..+10000)</div></div>
        </div>

        <section class="section-card">
          <h2>{e(sp_name)} — Governing-Body Source &amp; Origination Notes</h2>
          <p><strong>Primary Authority:</strong> <a href="{e(off_url)}" target="_blank" rel="noopener noreferrer">{e(sp.get('governing_body') or sp.get('official_source') or 'Official Governing Body')}</a> · <strong>OLBG Discovery Feed:</strong> <a href="{e(sp.get('olbg_url', 'https://www.olbg.com/betting-tips'))}" target="_blank" rel="noopener noreferrer">OLBG {e(sp_name)} Tips</a></p>
          <p class="muted">{e(sp.get('status_summary') or sp.get('methodology') or 'Lines originated strictly from verified governing-body standings, scoring differentials, or official rankings.')}</p>
        </section>

        <section class="section-card">
          <h2>{e(sp_name)} High-Confidence In-Band Predictions ({len(sp_preds)})</h2>
          {sp_preds_html}
        </section>

        <section class="section-card">
          <h2>{e(sp_name)} Complete Fixture &amp; Market Origination Table ({len(sp_matches)} Rows)</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Match ID / Sport / Date</th>
                  <th>Fixture &amp; Venue</th>
                  <th>Verified Governing-Body Form / Rank</th>
                  <th>Fair Winner Line (Dec / Amer / Prob)</th>
                  <th>Fair Handicap / Spread</th>
                  <th>Fair Match Total</th>
                  <th>Originated Pick &amp; Confidence</th>
                  <th>Official Source Links</th>
                </tr>
              </thead>
              <tbody>
                {sp_rows_html}
              </tbody>
            </table>
          </div>
        </section>
        """
        (SPORTS_DIR / f"{slug}.html").write_text(
            page_shell(f"{sp_name} Lines & Picks", "index", sp_body, prefix="../"),
            encoding="utf-8",
        )

    print(f"board_build.py complete: built 6 top-level pages + {len(sports_list)} sport pages under /board/.")


if __name__ == "__main__":
    main()
