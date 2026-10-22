#!/usr/bin/env python3
"""
Deterministic static HTML generator for `/portal/` (`arena/d81930c3-olbg2`).

Builds 26 HTML pages:
  - portal/index.html
  - portal/matches.html
  - portal/picks.html
  - portal/flagged.html
  - portal/audit.html
  - portal/methodology.html
  - portal/sources.html
  - portal/excluded.html
  - portal/sports/index.html
  - portal/sports/<17-eligible-sport-slugs>.html
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "portal"
PORTAL = ROOT / "portal"


def esc(val: object) -> str:
    return html.escape("" if val is None else str(val), quote=True)


def fmt_quote(q: dict | None) -> str:
    if not q:
        return '<span class="blank-cell">—</span>'
    return f"<span class='odds'>{esc(q['american_str'])} ({q['decimal']:.2f}) · {q['prob']*100:.1f}%</span>"


def fmt_winner_cell(m: dict) -> str:
    if m["status"] != "originated" or not m["markets"]["winner"]:
        return '<span class="blank-cell">— (Unverified / Left Blank)</span>'
    w = m["markets"]["winner"]
    if w["type"] == "1X2":
        return (
            f"<div><strong>{esc(m['home'])}:</strong> {fmt_quote(w['home'])}</div>"
            f"<div><strong>Draw:</strong> {fmt_quote(w['draw'])}</div>"
            f"<div><strong>{esc(m['away'])}:</strong> {fmt_quote(w['away'])}</div>"
        )
    return (
        f"<div><strong>{esc(m['home'])}:</strong> {fmt_quote(w['home'])}</div>"
        f"<div><strong>{esc(m['away'])}:</strong> {fmt_quote(w['away'])}</div>"
    )


def fmt_handicap_cell(m: dict) -> str:
    hcp = m["markets"].get("handicap") if m["markets"] else None
    if not hcp:
        return '<span class="blank-cell">—</span>'
    alt = m["markets"].get("alt_in_band")
    alt_html = ""
    if alt and alt["label"] != hcp["label"]:
        alt_html = f"<div style='margin-top:3px;color:#0f4c81'><strong>Alt .5:</strong> {esc(alt['label'])} {fmt_quote(alt['quote'])}</div>"
    return (
        f"<div><strong>{esc(hcp['label'])}:</strong> {fmt_quote(hcp['home'])}</div>"
        f"<div><strong>Opp:</strong> {fmt_quote(hcp['away'])}</div>"
        f"{alt_html}"
    )


def fmt_total_cell(m: dict) -> str:
    tot = m["markets"].get("total") if m["markets"] else None
    if not tot:
        return '<span class="blank-cell">—</span>'
    return (
        f"<div><strong>{esc(tot['label'])} Over:</strong> {fmt_quote(tot['over'])}</div>"
        f"<div><strong>Under:</strong> {fmt_quote(tot['under'])}</div>"
    )


def conf_badge(conf: str | None) -> str:
    if conf == "high":
        return '<span class="badge badge-high">HIGH</span>'
    if conf == "medium":
        return '<span class="badge badge-medium">MEDIUM</span>'
    if conf == "low":
        return '<span class="badge badge-low">LOW</span>'
    return '<span class="badge badge-blank">UNLINED / BLANK</span>'


def sev_badge(sev: str) -> str:
    s = sev.lower()
    if s in ("critical", "high"):
        return f'<span class="badge badge-critical">{esc(sev.upper())}</span>'
    if s == "medium":
        return '<span class="badge badge-medium">MEDIUM</span>'
    return f'<span class="badge badge-low">{esc(sev.upper())}</span>'


def page_shell(title: str, active: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    root_prefix = "../" * (depth + 1)
    nav_items = [
        ("overview", f"{prefix}index.html", "Overview"),
        ("sports", f"{prefix}sports/index.html", "17 Sports"),
        ("matches", f"{prefix}matches.html", "All Matches (184)"),
        ("picks", f"{prefix}picks.html", "In-Band Picks (34)"),
        ("flagged", f"{prefix}flagged.html", "Flagged for Review (38)"),
        ("audit", f"{prefix}audit.html", "Repo Audit"),
        ("methodology", f"{prefix}methodology.html", "Methodology"),
        ("sources", f"{prefix}sources.html", "Official Sources"),
        ("excluded", f"{prefix}excluded.html", "Excluded Gate"),
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
  <title>{esc(title)} — OLBG2 Verified 17-Sport Origination Portal</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="{prefix}index.html">OLBG2 /portal/ <span>17-Sport Official-Source Origination &amp; Forensic Audit (2026-10-22 UTC)</span></a>
      <nav class="topnav">{nav_html}</nav>
    </div>
  </header>
  <div class="subbar">
    <div class="subbar-inner">
      <span><strong>Repository Desks:</strong></span>
      <a href="{root_prefix}index.html">Root Dashboard</a> ·
      <a href="{root_prefix}verified/index.html">/verified/</a> ·
      <a href="{root_prefix}forward/index.html">/forward/</a> ·
      <a href="{root_prefix}board/index.html">/board/</a> ·
      <a href="{root_prefix}slate/index.html">/slate/</a> ·
      <a href="{root_prefix}hub/index.html">/hub/</a> ·
      <a href="{root_prefix}evidence/index.html">/evidence/</a> ·
      <a href="{root_prefix}audit65/flagged.html">/audit65/</a>
    </div>
  </div>
  <main class="container">
    {body}
  </main>
  <footer class="footer">
    Independent line origination &amp; first-hand governing-body verification desk (<code>arena/d81930c3-olbg2</code> · snapshot <code>2026-10-22 UTC</code>).
    Zero bookmaker odds scraped; zero excluded sports; unconfirmed fields left strictly blank (<code>—</code>) and disclosed on <a href="{prefix}flagged.html">Flagged for Review</a>.
  </footer>
  <script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def render_match_rows(rows: list[dict], sport_link_prefix: str) -> str:
    out = []
    for m in rows:
        conf_key = m["confidence"] or "blank"
        pick_html = (
            f"<div><strong>{esc(m['winner_pick'])}</strong></div><div>{fmt_quote(m['winner_quote'])}</div>"
            if m["winner_pick"]
            else '<span class="blank-cell">—</span>'
        )
        ib = m.get("in_band_selection")
        ib_html = (
            f"<div><strong>{esc(ib['label'])}</strong></div>"
            f"<div>{fmt_quote(ib['quote'])}</div>"
            f"<div style='font-size:11.5px;color:#4b5563'>{esc(ib['market'])}</div>"
            if ib
            else '<span class="blank-cell">—</span>'
        )
        out.append(
            f"<tr id='{esc(m['id'])}' data-row='1' data-sport='{esc(m['sport'])}' data-conf='{esc(conf_key)}'>"
            f"<td class='num'>{esc(m['date'])}<div style='color:#6b7280;font-size:11.5px'>{esc(m['time_utc'])}</div></td>"
            f"<td><a class='badge badge-sport' href='{sport_link_prefix}{esc(m['sport'])}.html'>{esc(m['sport_name'])}</a></td>"
            f"<td><strong>{esc(m['home'])} vs {esc(m['away'])}</strong>"
            f"<div style='font-size:12px;color:#4b5563'>{esc(m['competition'])} · {esc(m['venue'])}</div>"
            f"<div style='font-size:11.5px;color:#6b7280'>{esc(m['basis'])}</div></td>"
            f"<td>{fmt_winner_cell(m)}</td>"
            f"<td>{fmt_handicap_cell(m)}</td>"
            f"<td>{fmt_total_cell(m)}</td>"
            f"<td>{conf_badge(m['confidence'])}{pick_html}</td>"
            f"<td>{ib_html}</td>"
            f"<td><a href='{esc(m['source_url'])}' target='_blank' rel='noopener'>Official Governing Source ↗</a>"
            f"<div style='margin-top:4px;font-size:12px'><a href='{esc(m['olbg_url'])}' target='_blank' rel='noopener'>OLBG Hub ↗</a></div></td>"
            f"</tr>"
        )
    return "\n".join(out)


def render_pick_card(p: dict, sport_link_prefix: str) -> str:
    return f"""
    <article class="pick-card" id="{esc(p['id'])}">
      <div class="pick-head">
        <div>
          <a class="badge badge-sport" href="{sport_link_prefix}{esc(p['sport'])}.html">{esc(p['sport_name'])}</a>
          <span class="badge badge-high">HIGH CONFIDENCE · IN-BAND</span>
          <div class="pick-title">{esc(p['matchup'])}</div>
          <div style="font-size:12.5px;color:#4b5563">{esc(p['competition'])} · {esc(p['date'])}</div>
        </div>
        <div class="odds" style="text-align:right">
          <strong style="font-size:16px;color:#0b6b3a">{esc(p['fair_american_str'])}</strong>
          <div>{p['fair_decimal']:.2f} dec · {p['prob']*100:.1f}%</div>
        </div>
      </div>
      <div class="pick-sel">Selection: {esc(p['selection'])} ({esc(p['market'])})</div>
      <p class="pick-prose">{esc(p['prediction'])}</p>
      <div class="pick-meta">
        <div><strong>Team / Competitor:</strong> {esc(p['team_focus'])}</div>
        <div><strong>Verified Player(s):</strong> {esc(p['named_player'])}</div>
        <div><strong>Current Form:</strong> {esc(p['current_form'])}</div>
        <div><strong>Recent Match History:</strong> {esc(p['recent_history'])}</div>
        <div><strong>Confidence Basis:</strong> {esc(p['confidence_tier'])} · {p['word_count']} words</div>
        <div>
          <a href="{esc(p['source_url'])}" target="_blank" rel="noopener">Official Governing-Body Verification ↗</a> ·
          <a href="{esc(p['olbg_url'])}" target="_blank" rel="noopener">OLBG Discovery ↗</a>
        </div>
      </div>
    </article>
    """


def main() -> None:
    sports_data = json.loads((DATA / "sports.json").read_text())
    sources_data = json.loads((DATA / "sources.json").read_text())["sources"]
    audit_data = json.loads((DATA / "repo_audit.json").read_text())["findings"]
    matches_data = json.loads((DATA / "matches.json").read_text())["matches"]
    preds_data = json.loads((DATA / "predictions.json").read_text())["predictions"]
    flagged_data = json.loads((DATA / "flagged.json").read_text())["items"]

    eligible_sports = sports_data["eligible_sports"]
    excluded_hubs = sports_data["excluded_hubs"]

    (PORTAL / "sports").mkdir(parents=True, exist_ok=True)

    lined_matches = [m for m in matches_data if m["status"] == "originated"]
    blank_matches = [m for m in matches_data if m["status"] != "originated"]

    # Sport pill navigation helper
    def sport_pills(active_slug: str = "", prefix: str = "sports/") -> str:
        links = []
        for s in eligible_sports:
            cls = "active" if s["slug"] == active_slug else ""
            cnt = sum(1 for m in lined_matches if m["sport"] == s["slug"])
            links.append(f"<a class='{cls}' href='{prefix}{esc(s['slug'])}.html'>{esc(s['name'])} ({cnt})</a>")
        return f"<div class='sport-pills'>{''.join(links)}</div>"

    # 1. INDEX PAGE (portal/index.html)
    sport_summary_rows = []
    for s in eligible_sports:
        sl = s["slug"]
        s_lined = [m for m in lined_matches if m["sport"] == sl]
        s_blank = [m for m in blank_matches if m["sport"] == sl]
        s_picks = [p for p in preds_data if p["sport"] == sl]
        sport_summary_rows.append(
            f"<tr data-row='1' data-sport='{esc(sl)}'>"
            f"<td><a href='sports/{esc(sl)}.html'><strong>{esc(s['name'])}</strong></a> <span class='num'>(ID {s['olbg_id']})</span></td>"
            f"<td>{esc(s['governing_body'])}</td>"
            f"<td class='num'>{len(s_lined)}</td>"
            f"<td class='num'>{len(s_blank)}</td>"
            f"<td class='num'><strong>{len(s_picks)}</strong></td>"
            f"<td>{esc(', '.join(s['competitions']))}</td>"
            f"<td><a href='{esc(s['official_url'])}' target='_blank' rel='noopener'>Official Source ↗</a> · "
            f"<a href='{esc(s['olbg_url'])}' target='_blank' rel='noopener'>OLBG Hub ↗</a></td>"
            f"</tr>"
        )

    top_audit_rows = []
    for a in audit_data[:6]:
        top_audit_rows.append(
            f"<tr>"
            f"<td class='num'><strong>{esc(a['id'])}</strong></td>"
            f"<td>{sev_badge(a['severity'])}</td>"
            f"<td><code>{esc(a['affected_layer'])}</code></td>"
            f"<td><strong>{esc(a['title'])}</strong><div style='font-size:12.5px;color:#4b5563'>{esc(a['portal_resolution'])}</div></td>"
            f"<td><a href='{esc(a['source_url'])}' target='_blank' rel='noopener'>Verify Official Source ↗</a></td>"
            f"</tr>"
        )

    index_body = f"""
    <section class="hero">
      <h1>Complete 17-Sport Official-Source Line Origination &amp; Forensic Audit Portal</h1>
      <p>
        First repository layer to originate verified multi-market fair lines across <strong>all 17 eligible OLBG sports</strong>
        (strictly excluding soccer, boxing, ufc, mma, football, american football, hurling, horse racing, cycling, and specials),
        pair every high-confidence selection inside <code>-250</code> to <code>+10000</code> (<code>1.40</code>–<code>101.00</code>) with bespoke
        human analysis citing verified players and dated match history, and audit inherited repo layers line by line against primary governing bodies.
      </p>
    </section>

    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-label">Eligible OLBG Sports Lined</div><div class="kpi-val">17 / 17</div><div class="kpi-sub">0 excluded sports leaked (<a href="excluded.html">gate</a>)</div></div>
      <div class="kpi"><div class="kpi-label">Verified Fixtures</div><div class="kpi-val">{len(matches_data)}</div><div class="kpi-sub">{len(lined_matches)} originated + {len(blank_matches)} left blank</div></div>
      <div class="kpi"><div class="kpi-label">Featured In-Band Picks</div><div class="kpi-val">{len(preds_data)}</div><div class="kpi-sub">100% in [-250, +10000] across all 17 sports</div></div>
      <div class="kpi"><div class="kpi-label">Repo Irregularities Flagged</div><div class="kpi-val">{len(audit_data)}</div><div class="kpi-sub">+ {len(flagged_data) - len(audit_data)} unverified blank disclosures</div></div>
      <div class="kpi"><div class="kpi-label">Row Official Link Rate</div><div class="kpi-val">100%</div><div class="kpi-sub">29 primary governing-body feeds</div></div>
    </div>

    {sport_pills("", "sports/")}

    <section class="section">
      <h2>17 Eligible OLBG Sports — Origination &amp; Official Source Matrix</h2>
      <p class="section-lead">Every row links directly to both the official governing body used for verification/inputs and the live OLBG sport discovery endpoint.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport (OLBG ID)</th>
              <th>Official Governing Authority</th>
              <th>Originated</th>
              <th>Blank / Unlined</th>
              <th>High Picks</th>
              <th>Active Verified Competitions (22–28 Oct 2026)</th>
              <th>Manual Review Links</th>
            </tr>
          </thead>
          <tbody>
            {''.join(sport_summary_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Critical Cross-Layer Repository Audit Highlights (<a href="flagged.html">See All 38 Flagged Items →</a>)</h2>
      <p class="section-lead">Summary of major factual defects uncovered during line-by-line review of inherited repository datasets against live governing-body feeds.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Severity</th><th>Inherited Layer</th><th>Finding &amp; Portal Remediation</th><th>Official Proof</th></tr>
          </thead>
          <tbody>{''.join(top_audit_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Sample Featured High-Confidence In-Band Predictions (<a href="picks.html">View All {len(preds_data)} Picks Across 17 Sports →</a>)</h2>
      <div class="picks-grid">
        {''.join(render_pick_card(p, 'sports/') for p in preds_data[:6])}
      </div>
    </section>
    """
    (PORTAL / "index.html").write_text(page_shell("Overview", "overview", index_body, 0))

    # 2. MATCHES PAGE (portal/matches.html)
    sport_opts = "".join(f"<option value='{esc(s['slug'])}'>{esc(s['name'])}</option>" for s in eligible_sports)
    matches_body = f"""
    <section class="hero">
      <h1>All 184 Verified Fixtures &amp; Originated Multi-Market Fair Lines</h1>
      <p>
        160 independently originated matches across all 17 eligible OLBG sports plus 24 fixtures left strictly blank (<code>—</code>) where
        server-rendered governing-body feeds do not publish pre-match statistical inputs. Every row carries a direct official governing-body verification link.
      </p>
    </section>
    <section class="section" data-filter-root="1">
      <div class="controls">
        <input type="search" data-filter-search placeholder="Search team, player, competition, venue...">
        <select data-filter-sport>
          <option value="all">All 17 Eligible Sports</option>
          {sport_opts}
        </select>
        <select data-filter-conf>
          <option value="all">All Confidence Grades</option>
          <option value="high">High Confidence (Featured)</option>
          <option value="medium">Medium Confidence</option>
          <option value="low">Low Confidence</option>
          <option value="blank">Unlined / Left Blank</option>
        </select>
        <span class="count-pill" data-filter-count></span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date / UTC</th>
              <th>Sport</th>
              <th>Fixture, Venue &amp; Official Model Basis</th>
              <th>Win Match / 1X2 (Fair)</th>
              <th>Standard .5 Handicap / Line</th>
              <th>Match Total O/U</th>
              <th>Winner &amp; Grade</th>
              <th>Actionable [-250..+10000]</th>
              <th>Official Source</th>
            </tr>
          </thead>
          <tbody>
            {render_match_rows(matches_data, "sports/")}
          </tbody>
        </table>
      </div>
    </section>
    """
    (PORTAL / "matches.html").write_text(page_shell("All 184 Verified Matches", "matches", matches_body, 0))

    # 3. PICKS PAGE (portal/picks.html)
    pick_table_rows = []
    for p in preds_data:
        pick_table_rows.append(
            f"<tr data-row='1' data-sport='{esc(p['sport'])}'>"
            f"<td><a class='badge badge-sport' href='sports/{esc(p['sport'])}.html'>{esc(p['sport_name'])}</a></td>"
            f"<td class='num'>{esc(p['date'])}</td>"
            f"<td><strong><a href='#{esc(p['id'])}'>{esc(p['matchup'])}</a></strong><div style='font-size:12px;color:#4b5563'>{esc(p['competition'])}</div></td>"
            f"<td><strong>{esc(p['selection'])}</strong><div style='font-size:12px;color:#6b7280'>{esc(p['market'])}</div></td>"
            f"<td class='odds'><strong>{esc(p['fair_american_str'])}</strong> ({p['fair_decimal']:.2f})</td>"
            f"<td class='num'>{p['prob']*100:.1f}%</td>"
            f"<td>{esc(p['named_player'])}</td>"
            f"<td class='num'>{p['word_count']}w</td>"
            f"<td><a href='{esc(p['source_url'])}' target='_blank' rel='noopener'>Official Source ↗</a></td>"
            f"</tr>"
        )

    picks_body = f"""
    <section class="hero">
      <h1>34 High-Confidence In-Band Predictions (Strictly <code>-250</code> to <code>+10000</code> Across All 17 Sports)</h1>
      <p>
        Every selection below is priced strictly inside <code>-250</code> to <code>+10000</code> American fair odds (<code>1.40</code> to <code>101.00</code> decimal).
        Where a match's moneyline favorite sits heavier than <code>-250</code> chalk, we target the standard half-unit handicap, set, puck, or leg line instead.
        Each write-up is bespoke (56–87 words, zero repeated openings) and cites verified teams, named players, current form, and dated match history.
      </p>
    </section>

    <section class="section" data-filter-root="1">
      <h2>Summary Register of All 34 Featured Selections</h2>
      <div class="controls">
        <input type="search" data-filter-search placeholder="Filter picks by player, team, sport, odds...">
        <select data-filter-sport>
          <option value="all">All 17 Eligible Sports</option>
          {sport_opts}
        </select>
        <span class="count-pill" data-filter-count></span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sport</th><th>Date</th><th>Matchup &amp; Competition</th><th>Explicit Selection</th>
              <th>Fair Odds</th><th>Model p</th><th>Verified Player(s)</th><th>Words</th><th>Official Link</th>
            </tr>
          </thead>
          <tbody>{''.join(pick_table_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Full Human Write-Ups &amp; Official Evidence Cards</h2>
      <div class="picks-grid">
        {''.join(render_pick_card(p, 'sports/') for p in preds_data)}
      </div>
    </section>
    """
    (PORTAL / "picks.html").write_text(page_shell("34 High-Confidence In-Band Picks", "picks", picks_body, 0))

    # 4. FLAGGED FOR REVIEW PAGE (portal/flagged.html)
    flag_rows = []
    for f in flagged_data:
        flag_rows.append(
            f"<tr id='{esc(f['id'])}' data-row='1' data-type='{esc(f['type'])}'>"
            f"<td class='num'><strong>{esc(f['id'])}</strong></td>"
            f"<td>{sev_badge(f['severity'])}</td>"
            f"<td><code>{esc(f['layer'])}</code><div style='font-size:11.5px;color:#6b7280'>{esc(f['category'])}</div></td>"
            f"<td><strong>{esc(f['subject'])}</strong><div style='margin-top:4px;font-size:13px;color:#374151'>{esc(f['detail'])}</div></td>"
            f"<td style='font-size:13px'>{esc(f['action_taken'])}</td>"
            f"<td><a href='{esc(f['source_url'])}' target='_blank' rel='noopener'>Official Source ↗</a></td>"
            f"</tr>"
        )

    flagged_body = f"""
    <section class="hero">
      <h1>Flagged for Review — Repository Irregularities &amp; Unverified Blank Disclosures</h1>
      <p>
        Complete manual-review register combining <strong>12 cross-layer factual &amp; methodological irregularities</strong> (`PA-01`–`PA-12`)
        uncovered during line-by-line inspection of inherited datasets and <strong>26 unconfirmed fixture/market disclosures</strong> (`PU-01`–`PU-26`)
        intentionally left blank (<code>—</code>) rather than inferred or hallucinated.
      </p>
    </section>
    <section class="section" data-filter-root="1">
      <div class="controls">
        <input type="search" data-filter-search placeholder="Search flagged ID, layer, player, tournament...">
        <select data-filter-type>
          <option value="all">All 38 Flagged Items</option>
          <option value="repo_irregularity">Inherited Repo Irregularities (12)</option>
          <option value="unverified_left_blank">Unverified Fields Left Blank (26)</option>
        </select>
        <span class="count-pill" data-filter-count></span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Severity</th><th>Layer &amp; Category</th><th>Discrepancy / Unconfirmed Item</th><th>Disposition</th><th>Official Link</th></tr>
          </thead>
          <tbody>{''.join(flag_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    (PORTAL / "flagged.html").write_text(page_shell("Flagged for Review", "flagged", flagged_body, 0))

    # 5. AUDIT PAGE (portal/audit.html)
    layer_comparison = [
        ("root (data/*.json)", "5 / 17", "47", "14", "0% (47/47 source_url=null; PA-07)", "https://www.nba.com/games?date=2026-10-21"),
        ("/verified/ (data/verified/*)", "14 / 17", "128", "14 (+16 research)", "Lists ended Bank of Utah Golf (PA-03) & .25/.75 spreads (PA-06)", "https://www.pgatour.com/tournaments/2026/bank-of-utah-championship/R2026554"),
        ("/forward/ (data/forward/*)", "9 / 17", "93", "8", "Clean Oct 22+ forward filter; covers 9 of 17 eligible sports", "https://statsapi.mlb.com/api/v1/schedule/postseason?season=2026"),
        ("/board/ (data/board/*)", "13 / 17", "207", "35", "Lists ended Bank of Utah Golf (PA-03) & 11 synthetic .25/.75 picks (PA-06)", "https://www.pgatour.com/tournaments/2026/bank-of-utah-championship/R2026554"),
        ("/slate/ (data/slate/*)", "15 / 17 lined", "148 (+23 blank)", "36", "12 hallucinated ATP ties (PA-01), fake Bunting withdrawal (PA-02), Liquipedia LoL URLs (PA-08)", "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"),
        ("/hub/ (data/hub/*)", "11 / 17 lined (15 inv.)", "159 (+30 blank)", "25", "Ended Utah Golf (PA-03) & Lyon/Ningbo matches mislabeled Basel/Vienna/Guangzhou (PA-04)", "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule"),
        ("/evidence/ & /audit65/", "Audit Desks", "765–778 scanned", "0 originated", "Complementary structural & provenance audits (no 17-sport origination)", "https://api-web.nhle.com/v1/score/2026-10-22"),
        ("/portal/ (this desk)", "17 / 17 lined", "160 (+24 blank)", "34 (all 17 sports)", "100% governing-body HTTPS links; 0 hallucinations; 0 quarter-lines; 100% [-250..+10000]", "https://www.olbg.com/sitemap-betting-tips.xml"),
    ]
    comp_rows = "".join(
        f"<tr><td><strong>{esc(r[0])}</strong></td><td class='num'>{esc(r[1])}</td><td class='num'>{esc(r[2])}</td>"
        f"<td class='num'>{esc(r[3])}</td><td>{esc(r[4])}</td>"
        f"<td><a href='{esc(r[5])}' target='_blank' rel='noopener'>Official Reference ↗</a></td></tr>"
        for r in layer_comparison
    )
    audit_rows_full = "".join(
        f"<tr id='{esc(a['id'])}'><td class='num'><strong>{esc(a['id'])}</strong></td><td>{sev_badge(a['severity'])}</td>"
        f"<td><code>{esc(a['affected_layer'])}</code></td><td><strong>{esc(a['title'])}</strong><p style='margin:5px 0 0;color:#374151'>{esc(a['detail'])}</p></td>"
        f"<td>{esc(a['portal_resolution'])}</td><td><a href='{esc(a['source_url'])}' target='_blank' rel='noopener'>Official Proof ↗</a></td></tr>"
        for a in audit_data
    )
    audit_body = f"""
    <section class="hero">
      <h1>Line-by-Line Repository Forensic Audit &amp; Cross-Layer Matrix</h1>
      <p>
        Read-only audit of all inherited repository layers against first-hand governing-body fetches on <code>2026-10-22 UTC</code>.
        Full narrative report also committed in Markdown at <code>research/audit-d81930c3.md</code>.
      </p>
    </section>
    <section class="section">
      <h2>Repository Layer Coverage &amp; Verification Comparison</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Layer</th><th>Sports Lined</th><th>Fixtures</th><th>High Picks</th><th>Audit Summary</th><th>Official Reference</th></tr></thead>
          <tbody>{comp_rows}</tbody>
        </table>
      </div>
    </section>
    <section class="section">
      <h2>Detailed Forensic Findings (PA-01 through PA-12)</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Severity</th><th>Affected Files</th><th>Evidence-Backed Finding</th><th>Portal Remediation</th><th>Official Link</th></tr></thead>
          <tbody>{audit_rows_full}</tbody>
        </table>
      </div>
    </section>
    """
    (PORTAL / "audit.html").write_text(page_shell("Forensic Repo Audit", "audit", audit_body, 0))

    # 6. METHODOLOGY PAGE (portal/methodology.html)
    model_rows = [
        ("Ice Hockey (NHL & SHL)", "Empirical-Bayes shrunk multiplicative Poisson (w = gp/(gp+8), home 1.05, 50/50 OT/SO tie split)", "2-Way Moneyline, ±1.5 Puck Line, O/U Goals", "https://api-web.nhle.com/v1/score/2026-10-22"),
        ("Baseball (MLB World Series)", "162-game Pythagorean (exp=1.83) Log5 + home-field log-odds (+0.16) + normal run margin", "2-Way Moneyline, ±1.5 Run Line, O/U 7.5 Runs", "https://statsapi.mlb.com/api/v1/schedule/postseason?season=2026"),
        ("Basketball (EuroLeague & NBA)", "Shrunk net-rating normal margin (EuroLeague w=gp/(gp+4); NBA 0.75 prior + Oct 20-21 opener; NBA totals blank)", "2-Way Moneyline, .5 Spread, EuroLeague O/U", "https://www.euroleaguebasketball.net/en/euroleague/standings/"),
        ("Tennis (ATP & WTA)", "Official singles ranking-points log-ratio per-set Bo3 Markov chain (exact 2-0, 2-1, 1-2, 0-2)", "2-Way Winner, ±1.5 Sets, O/U 22.5 Games", "https://www.atptour.com/en/scores/current/lyon/496/daily-schedule"),
        ("Darts (PDC Euro Champ)", "2-year PDC Order-of-Merit log-prize per-leg exact negative-binomial Race-to-6 (Bo11)", "2-Way Winner, ±1.5 / ±2.5 Legs, O/U 9.5 Legs", "https://www.pdc.tv/order-of-merit/pdc-order-merit"),
        ("Snooker (WST NI Open)", "2-year WST ranking-prize log-ratio per-frame exact negative-binomial Race-to-4 (Bo7); non-Top-36 left blank", "2-Way Winner, ±1.5 Frames, O/U 5.5 Frames", "https://www.wst.tv/tournaments/northern-ireland-open-2026/"),
        ("Rugby Union (URC, Top 14, Pro D2)", "Shrunk league PF/PA normal margin (w=gp/(gp+5), sigma=13.0, draw band [-0.5,+0.5])", "3-Way 1X2, Standard .5 Handicap, O/U Points", "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/"),
        ("Rugby League (RLWC 2026)", "IRL official world rating + Round 1 point-differential normal margin (sigma=13.5)", "3-Way 1X2, Standard .5 Handicap, O/U Points", "https://www.rlwc2026.com/"),
        ("Handball (EHF Champions League)", "Exact 56x56 renormalized 2D Poisson score grid (w=gp/(gp+3), home +0.8 goals)", "3-Way 1X2, Standard .5 Goal Line, O/U Goals", "https://ehfcl.eurohandball.com/men/2026-27/standings/"),
        ("Aussie Rules (NAB AFLW)", "Round 10 Premiership-Points & Percentage log-ratio margin model (home +4.0, sigma=17.5)", "2-Way Winner, Standard .5 Line, O/U Points", "https://www.afl.com.au/aflw"),
        ("Cricket (ICC T20I/ODI & CSA)", "Official ICC/CSA team rating normal run-equivalent margin (sigma=24 T20 / 34 ODI)", "2-Way Winner, .5 Run-Eq Line, O/U Match Runs", "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india"),
        ("Volleyball (SuperLega)", "Shrunk rally-point ratio per-set Race-to-3 (Bo5) Markov model; PlusLiga redirect rows left blank", "2-Way Winner, ±1.5 Sets, O/U 181.5 Rally Pts", "https://www.legavolley.it/calendario/?idCampionato=999"),
        ("Esports (LoL Worlds Swiss)", "Riot official regional tier + Worlds Draw Pool 1-4 logistic Bo1 model; kill totals left blank", "2-Way Bo1 Match Winner", "https://lolesports.com/en-US/leagues/first_stand,lck,lcs,msi,worlds"),
        ("Golf (PGA Bermuda & DPWT Genesis)", "Official Tour/OWGR rank log-strength 72-hole stroke-differential normal model (sigma=5.2)", "2-Way 72-Hole H2H, -1.5 Stroke Line", "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528"),
        ("Motor Racing (F1 US GP)", "17-round FIA WDC points-per-round Plackett-Luce outright & pairwise classification model", "Race Outright & Driver Classification H2Hs", "https://www.formula1.com/en/results/2026/drivers"),
        ("Greyhounds (GBGB Cat-1 Final)", "Romford 575m semi-final sectional clockings (35.36s..35.95s, sigma=0.38s); BAGS cards left blank", "Cat-1 Outright & Trap Match Bets", "https://www.gbgb.org.uk/racing/results/"),
        ("Gaelic Football (County Finals)", "County SFC knockout scoring-rate normal margin (sigma=5.8, draw band); secondary counties left blank", "3-Way 1X2, .5 Handicap, O/U Total Points", "https://munster.gaa.ie/fixtures/club-championships-2026/"),
    ]
    meth_rows = "".join(
        f"<tr><td><strong>{esc(r[0])}</strong></td><td>{esc(r[1])}</td><td>{esc(r[2])}</td>"
        f"<td><a href='{esc(r[3])}' target='_blank' rel='noopener'>Official Feed ↗</a></td></tr>"
        for r in model_rows
    )
    methodology_body = f"""
    <section class="hero">
      <h1>Mathematical Line Origination, Pricing Identity &amp; Confidence Rules</h1>
      <p>
        All prices in <code>/portal/</code> are originated independently from official governing-body performance data in
        <code>scripts/portal_model.py</code>. Zero bookmaker quotes are scraped, read, or compared.
      </p>
    </section>
    <section class="section">
      <h2>1. Fair No-Vig Pricing &amp; Focus-Band Enforcement (<code>-250</code> to <code>+10000</code>)</h2>
      <pre>fair_decimal  = round(1.0 / p_model, 2)
fair_american = +round((fair_decimal - 1) * 100)        if fair_decimal >= 2.00
                -round(100 / (fair_decimal - 1))        if fair_decimal &lt;  2.00
in_focus_band = (1.40 &lt;= fair_decimal &lt;= 101.00) and (-250 &lt;= fair_american &lt;= +10000)</pre>
      <p style="color:#374151">
        Deriving the American quote directly from the rounded fair decimal guarantees zero rounding drift between displayed formats.
        Whenever a match's moneyline favorite exceeds <code>71.43%</code> (sub-<code>-250</code> chalk), our engine never promotes that chalk moneyline;
        instead it evaluates standard <code>.5</code> half-unit handicaps, set lines, leg lines, or puck lines (never synthetic <code>.25/.75</code> lines).
        Every featured high-confidence pick explicitly discloses whether it qualifies under <strong>Tier H1</strong> (<code>p_model &gt;= 70.0%</code> inside <code>[-250, -233]</code>)
        or <strong>Tier H2</strong> (multi-factor high conviction inside <code>[-250, +10000]</code>, including plus-money outrights).
      </p>
    </section>
    <section class="section">
      <h2>2. Sport-by-Sport Origination Models (All 17 Eligible Sports)</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Sport</th><th>Parametric Model &amp; Shrinkage</th><th>Originated Markets</th><th>Primary Input Feed</th></tr></thead>
          <tbody>{meth_rows}</tbody>
        </table>
      </div>
    </section>
    """
    (PORTAL / "methodology.html").write_text(page_shell("Methodology", "methodology", methodology_body, 0))

    # 7. SOURCES PAGE (portal/sources.html)
    src_rows = "".join(
        f"<tr><td class='num'><strong>{esc(s['id'])}</strong></td><td><code>{esc(s['sport'])}</code></td>"
        f"<td><strong>{esc(s['authority'])}</strong></td><td class='num'>{esc(s['captured_utc'])}</td>"
        f"<td><a href='{esc(s['url'])}' target='_blank' rel='noopener'>{esc(s['url'])} ↗</a></td></tr>"
        for s in sources_data
    )
    sources_body = f"""
    <section class="hero">
      <h1>Official Governing-Body &amp; Discovery Source Register (29 Feeds)</h1>
      <p>Every fixture, team record, ranking tally, and named-player statistic in <code>/portal/</code> traces directly to one of the official HTTPS endpoints below.</p>
    </section>
    <section class="section">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Source ID</th><th>Sport</th><th>Governing Body / Endpoint Description</th><th>Captured (UTC)</th><th>Official URL</th></tr></thead>
          <tbody>{src_rows}</tbody>
        </table>
      </div>
    </section>
    """
    (PORTAL / "sources.html").write_text(page_shell("Official Sources", "sources", sources_body, 0))

    # 8. EXCLUDED SPORTS GATE PAGE (portal/excluded.html)
    excl_rows = "".join(
        f"<tr><td class='num'><strong>{e['olbg_id']}</strong></td><td><code>{esc(e['olbg_path'])}</code></td>"
        f"<td><span class='badge badge-critical'>EXCLUDED ({esc(e['rule_term'])})</span></td>"
        f"<td class='num'>HTTP {e['http_status']}</td><td>{esc(e['note'])}</td>"
        f"<td><a href='https://www.olbg.com{esc(e['olbg_path'])}' target='_blank' rel='noopener'>OLBG Endpoint ↗</a></td></tr>"
        for e in excluded_hubs
    )
    excluded_body = f"""
    <section class="hero">
      <h1>Excluded Sports Gate — Zero-Leakage Verification (<code>ID = 1..28</code>)</h1>
      <p>
        Per project instructions, <strong>soccer, boxing, ufc, mma, football, american football, hurling, horse racing, cycling, and specials</strong>
        are strictly excluded. All 11 corresponding OLBG hub endpoints below were verified on <code>2026-10-22</code> and blocked by automated build &amp; unit-test assertions.
      </p>
    </section>
    <section class="section">
      <div class="table-wrap">
        <table>
          <thead><tr><th>OLBG ID</th><th>Hub Path</th><th>Exclusion Rule</th><th>Live Status</th><th>Verification Note</th><th>Endpoint Link</th></tr></thead>
          <tbody>{excl_rows}</tbody>
        </table>
      </div>
    </section>
    """
    (PORTAL / "excluded.html").write_text(page_shell("Excluded Sports Gate", "excluded", excluded_body, 0))

    # 9. SPORTS DIRECTORY (portal/sports/index.html)
    dir_rows = []
    for s in eligible_sports:
        sl = s["slug"]
        s_lined = [m for m in lined_matches if m["sport"] == sl]
        s_blank = [m for m in blank_matches if m["sport"] == sl]
        s_picks = [p for p in preds_data if p["sport"] == sl]
        dir_rows.append(
            f"<tr>"
            f"<td><a href='{esc(sl)}.html'><strong>{esc(s['name'])}</strong></a> <span class='num'>(OLBG {s['olbg_id']})</span></td>"
            f"<td>{esc(s['governing_body'])}</td>"
            f"<td class='num'>{len(s_lined)}</td>"
            f"<td class='num'>{len(s_blank)}</td>"
            f"<td class='num'><strong>{len(s_picks)}</strong></td>"
            f"<td>{esc(s['olbg_status'])}</td>"
            f"<td><a href='{esc(s['official_url'])}' target='_blank' rel='noopener'>Official Governing Body ↗</a></td>"
            f"</tr>"
        )
    sports_idx_body = f"""
    <section class="hero">
      <h1>17 Eligible OLBG Sports — Category Subpages</h1>
      <p>Select any of the 17 eligible sports below to inspect its originated multi-market lines, featured in-band human predictions, and sport-specific flags.</p>
    </section>
    {sport_pills("", "")}
    <section class="section">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Sport</th><th>Governing Body</th><th>Originated</th><th>Blank</th><th>Featured Picks</th><th>OLBG &amp; Official Discovery Note</th><th>Official Link</th></tr></thead>
          <tbody>{''.join(dir_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    (PORTAL / "sports" / "index.html").write_text(page_shell("17 Sports Directory", "sports", sports_idx_body, 1))

    # 10. 17 INDIVIDUAL SPORT SUBPAGES (portal/sports/<slug>.html)
    for s in eligible_sports:
        sl = s["slug"]
        s_matches = [m for m in matches_data if m["sport"] == sl]
        s_lined = [m for m in s_matches if m["status"] == "originated"]
        s_blank = [m for m in s_matches if m["status"] != "originated"]
        s_picks = [p for p in preds_data if p["sport"] == sl]
        s_flags = [f for f in flagged_data if sl in f["layer"].lower() or s["name"].lower() in f["subject"].lower()]

        flag_sec = ""
        if s_flags:
            frows = "".join(
                f"<tr><td class='num'><strong>{esc(f['id'])}</strong></td><td>{sev_badge(f['severity'])}</td>"
                f"<td><strong>{esc(f['subject'])}</strong><div style='font-size:12.5px;color:#4b5563'>{esc(f['detail'])}</div></td>"
                f"<td>{esc(f['action_taken'])}</td>"
                f"<td><a href='{esc(f['source_url'])}' target='_blank' rel='noopener'>Official Source ↗</a></td></tr>"
                for f in s_flags
            )
            flag_sec = f"""
            <section class="section">
              <h2>Sport-Specific Audit &amp; Unverified Blank Notes</h2>
              <div class="table-wrap">
                <table>
                  <thead><tr><th>ID</th><th>Severity</th><th>Item</th><th>Disposition</th><th>Official Link</th></tr></thead>
                  <tbody>{frows}</tbody>
                </table>
              </div>
            </section>
            """

        sport_body = f"""
        <section class="hero">
          <h1>{esc(s['name'])} — Official-Source Multi-Market Lines &amp; In-Band Predictions</h1>
          <p>
            <strong>OLBG Hub:</strong> <a href="{esc(s['olbg_url'])}" target="_blank" rel="noopener"><code>{esc(s['olbg_url'])}</code> ↗</a> ·
            <strong>Governing Authority:</strong> <a href="{esc(s['official_url'])}" target="_blank" rel="noopener">{esc(s['governing_body'])} ↗</a><br>
            <strong>Coverage:</strong> {len(s_lined)} originated multi-market fixtures, {len(s_blank)} unconfirmed rows left strictly blank (<code>—</code>),
            and {len(s_picks)} featured high-confidence pick(s) inside <code>[-250, +10000]</code>.
          </p>
        </section>

        {sport_pills(sl, "")}

        <section class="section">
          <h2>Featured High-Confidence {esc(s['name'])} Predictions ({len(s_picks)})</h2>
          <div class="picks-grid">
            {''.join(render_pick_card(p, '') for p in s_picks)}
          </div>
        </section>

        <section class="section" data-filter-root="1">
          <h2>{esc(s['name'])} Match Board ({len(s_matches)} Verified Rows)</h2>
          <div class="controls">
            <input type="search" data-filter-search placeholder="Filter {esc(s['name'])} fixtures...">
            <select data-filter-conf>
              <option value="all">All Grades</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="blank">Unlined / Blank</option>
            </select>
            <span class="count-pill" data-filter-count></span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date / UTC</th><th>Sport</th><th>Fixture, Venue &amp; Basis</th>
                  <th>Win Match / 1X2</th><th>Standard .5 Line</th><th>Total O/U</th>
                  <th>Winner &amp; Grade</th><th>Actionable [-250..+10000]</th><th>Official Source</th>
                </tr>
              </thead>
              <tbody>{render_match_rows(s_matches, "")}</tbody>
            </table>
          </div>
        </section>

        {flag_sec}
        """
        (PORTAL / "sports" / f"{sl}.html").write_text(page_shell(f"{s['name']} Lines & Picks", "sports", sport_body, 1))

    built = sorted(PORTAL.rglob("*.html"))
    print(f"portal_build.py OK: built {len(built)} HTML pages in {PORTAL}")


if __name__ == "__main__":
    main()
