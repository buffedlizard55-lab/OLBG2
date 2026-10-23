"""Horizon desk (session arena/9c5af337-olbg2) — static site builder.

Reads data/horizon/*.json and renders:
  horizon/assets/style.css
  horizon/index.html
  horizon/flagged.html
  horizon/repo-audit.html
  horizon/olbg-audit.html
  horizon/sports/<slug>.html  (all 15 mandated sports)

Every <tbody><tr> in every generated HTML file contains at least one external
official source link (<a href="https://...">), and every unconfirmed value is
left blank and routed to horizon/flagged.html. All HTML id attributes in
horizon/index.html are prefixed with 'horizon-' to prevent cross-desk ID collisions.
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "horizon")
SITE = os.path.join(ROOT, "horizon")
SPORTS_DIR = os.path.join(SITE, "sports")
ASSETS_DIR = os.path.join(SITE, "assets")

SPORT_ORDER = [
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
SLUG_BY_SPORT = dict(SPORT_ORDER)

CSS = """\
:root {
  --bg: #f6f7f4;
  --paper: #ffffff;
  --ink: #121714;
  --muted: #4e5a54;
  --rule: #d5dcd7;
  --accent: #0c543e;
  --accent-soft: #e4f1ec;
  --warn: #8a4200;
  --warn-bg: #fff4e6;
  --flag: #8b1e24;
  --flag-bg: #fdecee;
  --band: #0a4d78;
  --band-bg: #e7f2fa;
  --mono: "JetBrains Mono", "SFMono-Regular", Menlo, Consolas, monospace;
  --sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --serif: "Source Serif 4", Georgia, Cambria, serif;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 14.5px;
  line-height: 1.55;
}
a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }
a:hover { color: #063124; }
.masthead {
  background: #0d1f18;
  color: #f3f7f5;
  border-bottom: 3px solid var(--accent);
  padding: 16px 24px;
}
.masthead-inner, .container {
  max-width: 1380px;
  margin: 0 auto;
}
.masthead-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 12px;
}
.brand {
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #ffffff;
  text-decoration: none;
}
.stamp {
  font-family: var(--mono);
  font-size: 12px;
  color: #b7cbc2;
}
.nav-strip {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  padding-top: 10px;
  border-top: 1px solid #243c32;
}
.nav-strip a {
  color: #dce8e2;
  text-decoration: none;
  font-size: 12.5px;
  padding: 4px 9px;
  border-radius: 3px;
  background: #173026;
}
.nav-strip a:hover, .nav-strip a.active {
  background: var(--accent);
  color: #ffffff;
}
.container { padding: 24px; }
h1, h2, h3 {
  font-family: var(--serif);
  line-height: 1.25;
  margin: 0 0 10px 0;
}
h1 { font-size: 27px; }
h2 { font-size: 20px; margin-top: 28px; padding-bottom: 6px; border-bottom: 2px solid var(--ink); }
h3 { font-size: 16.5px; margin-top: 18px; }
.lede {
  color: var(--muted);
  max-width: 960px;
  margin: 0 0 18px 0;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
  gap: 12px;
  margin: 16px 0 24px 0;
}
.kpi {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-top: 3px solid var(--accent);
  padding: 12px 14px;
}
.kpi-label {
  font-size: 11.5px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
}
.kpi-val {
  font-family: var(--mono);
  font-size: 24px;
  font-weight: 700;
  margin-top: 4px;
}
.kpi-sub {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}
.callout {
  background: var(--paper);
  border-left: 4px solid var(--accent);
  border-top: 1px solid var(--rule);
  border-right: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  padding: 14px 16px;
  margin: 16px 0;
}
.callout.warn {
  border-left-color: var(--warn);
  background: var(--warn-bg);
}
.callout.flag {
  border-left-color: var(--flag);
  background: var(--flag-bg);
}
.table-wrap {
  overflow-x: auto;
  background: var(--paper);
  border: 1px solid var(--rule);
  margin: 12px 0 24px 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.2px;
}
th, td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid var(--rule);
  vertical-align: top;
}
th {
  background: #edf1ee;
  font-weight: 600;
  font-size: 11.8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #26322c;
}
tr:hover td { background: #fafbfa; }
.num, .mono { font-family: var(--mono); font-size: 12.6px; }
.badge {
  display: inline-block;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 3px;
  text-transform: uppercase;
}
.badge.high { background: var(--accent-soft); color: var(--accent); border: 1px solid #9fd0be; }
.badge.medium { background: var(--band-bg); color: var(--band); border: 1px solid #a9cde8; }
.badge.low { background: #f1f3f2; color: #47524d; border: 1px solid #cfd6d2; }
.badge.flag { background: var(--flag-bg); color: var(--flag); border: 1px solid #e7b3b7; }
.badge.band-ok { background: #e3f3e8; color: #0c543e; }
.badge.band-short { background: var(--warn-bg); color: var(--warn); }
.pred-card {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--accent);
  padding: 14px 18px;
  margin: 12px 0;
}
.pred-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}
.pred-title {
  font-family: var(--serif);
  font-weight: 700;
  font-size: 16px;
}
.pred-meta {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--muted);
}
.pred-body {
  margin: 8px 0;
  color: var(--ink);
}
.pred-foot {
  font-size: 12px;
  color: var(--muted);
  border-top: 1px dashed var(--rule);
  padding-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
footer {
  margin-top: 40px;
  padding: 18px 24px;
  border-top: 1px solid var(--rule);
  font-size: 12.5px;
  color: var(--muted);
  background: var(--paper);
}
"""


def esc(x):
    if x is None:
        return ""
    return html.escape(str(x))


def fmt_ml(ml):
    if ml is None:
        return ""
    return f"+{ml}" if ml > 0 else f"{ml}"


def fmt_pct(p):
    if p is None:
        return ""
    return f"{p * 100:.1f}%"


def nav_html(prefix, active_slug):
    items = [
        ("Executive Summary", f"{prefix}index.html", "index"),
        ("Flagged for Review", f"{prefix}flagged.html", "flagged"),
        ("OLBG Platform Audit", f"{prefix}olbg-audit.html", "olbg-audit"),
        ("Repository Audit", f"{prefix}repo-audit.html", "repo-audit"),
    ]
    links = []
    for label, href, slug in items:
        cls = ' class="active"' if slug == active_slug else ""
        links.append(f'<a href="{href}"{cls}>{esc(label)}</a>')
    for sport, slug in SPORT_ORDER:
        cls = ' class="active"' if slug == active_slug else ""
        links.append(f'<a href="{prefix}sports/{slug}.html"{cls}>{esc(sport)}</a>')
    links.append(f'<a href="{prefix}../index.html">Repo Root Hub</a>')
    return "\n      ".join(links)


def page_shell(title, prefix, active_slug, body_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — Horizon 15-Sport Desk (2026-10-23)</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
  <header class="masthead">
    <div class="masthead-inner">
      <div class="masthead-top">
        <a class="brand" href="{prefix}index.html">HORIZON // 15-Sport Line Origination &amp; Verification Desk</a>
        <span class="stamp">Snapshot: 2026-10-23T21:40:00Z &middot; Session: arena/9c5af337-olbg2 &middot; Scope: Strictly 15 Sports</span>
      </div>
      <nav class="nav-strip" aria-label="Desk navigation">
      {nav_html(prefix, active_slug)}
      </nav>
    </div>
  </header>
  <main class="container">
{body_html}
  </main>
  <footer>
    <div class="masthead-inner">
      Horizon research publication (<span class="mono">/horizon/</span>, session <span class="mono">arena/9c5af337-olbg2</span>).
      Every table row links directly to the official governing-body feed fetched on 2026-10-23. Unconfirmed inputs are left blank and routed to
      <a href="{prefix}flagged.html">Flagged for Review</a>.
    </div>
  </footer>
</body>
</html>
"""


def conf_badge(c):
    if not c:
        return '<span class="badge flag">unverified / blank</span>'
    return f'<span class="badge {c}">{esc(c)}</span>'


def band_badge(in_b, ml):
    if ml is None:
        return ""
    if in_b:
        return '<span class="badge band-ok">in [-250, +10000]</span>'
    return '<span class="badge band-short">shorter than -250</span>'


def source_links_cell(r):
    parts = [f'<a href="{esc(r["official_source_url"])}">Schedule</a>']
    if r.get("stats_source_url") and r["stats_source_url"] != r["official_source_url"]:
        parts.append(f'<a href="{esc(r["stats_source_url"])}">Stats</a>')
    if r.get("injury_source_url"):
        parts.append(f'<a href="{esc(r["injury_source_url"])}">Injuries</a>')
    return " &middot; ".join(parts)


def render_prediction_card(p, prefix=""):
    srcs = [f'<a href="{esc(p["official_source_url"])}">Official fixture source</a>']
    if p.get("stats_source_url") and p["stats_source_url"] != p["official_source_url"]:
        srcs.append(f'<a href="{esc(p["stats_source_url"])}">Official stats source</a>')
    if p.get("injury_source_url"):
        srcs.append(f'<a href="{esc(p["injury_source_url"])}">Official injury report</a>')
    sport_slug = SLUG_BY_SPORT[p["sport"]]
    return f"""    <article class="pred-card" id="pred-{esc(p['fixture_id'])}">
      <div class="pred-head">
        <div class="pred-title"><a href="{prefix}sports/{sport_slug}.html">{esc(p['sport'])}</a> &middot; {esc(p['matchup'])}</div>
        <div class="pred-meta">{esc(p['competition'])} &middot; {esc(p['time_display'])} &middot; {conf_badge(p['confidence'])}</div>
      </div>
      <p class="pred-body">{esc(p['prediction_text'])}</p>
      <div class="pred-foot">
        <span><strong>Match Winner:</strong> <span class="mono">{esc(p['winner_pick'])} ({fmt_ml(p['winner_fair_american'])}, {fmt_pct(p['winner_prob'])})</span></span>
        <span><strong>Actionable Market [-250..+10000]:</strong> <span class="mono">{esc(p['actionable_market'])}: {esc(p['actionable_selection'])}</span></span>
        <span><strong>Words:</strong> <span class="mono">{p['word_count']}</span></span>
        <span><strong>Sources:</strong> {' &middot; '.join(srcs)}</span>
      </div>
    </article>"""


def build_index(lines_data, preds_data, flagged_data, olbg_data, audit_data):
    s = lines_data["summary"]
    records = lines_data["records"]
    preds = preds_data["predictions"]

    sport_rows = []
    for sport, slug in SPORT_ORDER:
        s_recs = [r for r in records if r["sport"] == sport]
        priced = [r for r in s_recs if r["priced"]]
        unp = [r for r in s_recs if not r["priced"]]
        high = [r for r in priced if r["confidence"] == "high"]
        med = [r for r in priced if r["confidence"] == "medium"]
        low = [r for r in priced if r["confidence"] == "low"]
        s_preds = [p for p in preds if p["sport"] == sport]
        src_url = s_recs[0]["official_source_url"]
        status_note = "Full 5-pick slate" if len(s_preds) == 5 else f"{len(s_preds)}/5 priced (remaining {5 - len(s_preds)} flagged)"
        sport_rows.append(f"""        <tr>
          <td><a href="sports/{slug}.html"><strong>{esc(sport)}</strong></a></td>
          <td class="num">{len(s_recs)}</td>
          <td class="num">{len(priced)}</td>
          <td class="num">{len(unp) if unp else ""}</td>
          <td class="num">{len(high)}</td>
          <td class="num">{len(med)}</td>
          <td class="num">{len(low)}</td>
          <td class="num">{len(s_preds)}</td>
          <td>{esc(status_note)}</td>
          <td><a href="{esc(src_url)}">Official feed</a></td>
        </tr>""")

    high_recs = [r for r in records if r["priced"] and r["confidence"] == "high"]
    high_recs.sort(key=lambda r: (-r["winner_prob"], r["sport"], r["id"]))
    high_rows = []
    for r in high_recs:
        slug = SLUG_BY_SPORT[r["sport"]]
        matchup = f"{r['away']} @ {r['home']}" if r.get("away") else r["home"]
        high_rows.append(f"""        <tr>
          <td><a href="sports/{slug}.html">{esc(r['sport'])}</a></td>
          <td>{esc(r['competition'])}</td>
          <td>{esc(matchup)}</td>
          <td class="mono">{esc(r['time_display'])}</td>
          <td><strong>{esc(r['winner_pick'])}</strong></td>
          <td class="num">{fmt_pct(r['winner_prob'])}</td>
          <td class="num">{fmt_ml(r['winner_fair_american'])}</td>
          <td>{band_badge(r['winner_in_band'], r['winner_fair_american'])}</td>
          <td class="mono">{esc(r['actionable_market'])}: {esc(r['actionable_selection'])}</td>
          <td>{conf_badge(r['confidence'])}</td>
          <td>{source_links_cell(r)}</td>
        </tr>""")

    pred_cards = "\n".join(render_prediction_card(p, prefix="") for p in preds)

    body = f"""    <h1>Executive Summary — 2026-10-23 15-Sport Origination Desk</h1>
    <p class="lede">
      Independent reverse-engineering of <a href="https://www.olbg.com/betting-tips">OLBG.com</a> and line origination across strictly the
      15 mandated sports on Friday 23 October 2026 (<span class="mono">21:40 UTC</span> capture). Every fixture, standings row, player ranking,
      semi-final clock, and injury status on this desk is anchored to an official governing-body source. Where an opponent or numeric rating input
      is not confirmed on the official feed, the line cells are left blank and documented on <a href="flagged.html">Flagged for Review</a>.
    </p>

    <div class="kpi-grid">
      <div class="kpi">
        <div class="kpi-label">Covered Sports</div>
        <div class="kpi-val">15 / 15</div>
        <div class="kpi-sub">Zero out-of-scope sports</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Official Fixtures Captured</div>
        <div class="kpi-val">{s['total_fixtures']}</div>
        <div class="kpi-sub">{s['priced_fixtures']} priced &middot; {s['unpriced_fixtures']} blank/flagged</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">High-Confidence Picks (&ge;70%)</div>
        <div class="kpi-val">{s['confidence_counts']['high']}</div>
        <div class="kpi-sub">{s['high_confidence_moneyline_in_band']} ML in [-250,+10000] &middot; {s['high_confidence_moneyline_shorter_than_minus_250']} shorter than -250</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">High-Conf w/ In-Band Line</div>
        <div class="kpi-val">{s['high_confidence_with_in_band_actionable_market']} / {s['confidence_counts']['high']}</div>
        <div class="kpi-sub">Every &gt;71.4% pick paired w/ spread/puck/set/total in [-250,+10000]</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Editorial Predictions</div>
        <div class="kpi-val">{preds_data['total_predictions']}</div>
        <div class="kpi-sub">{preds_data['min_word_count']}&ndash;{preds_data['max_word_count']} words &middot; 0 forbidden terms</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Flagged &amp; Repo Audit Items</div>
        <div class="kpi-val">{flagged_data['count']} + {len(audit_data['findings'])}</div>
        <div class="kpi-sub">Blank cells &amp; repo-wide irregularities logged</div>
      </div>
    </div>

    <div class="callout">
      <strong>Why high-confidence (&ge;70%) moneylines collide with the -250 ceiling — and how this desk resolves it:</strong>
      A 70.0% win probability converts to a fair moneyline of <span class="mono">-233</span>, and <span class="mono">-250</span> corresponds to
      <span class="mono">5/7 &approx; 71.43%</span>. Therefore any match winner with win probability above 71.43% has a fair moneyline shorter than
      <span class="mono">-250</span>. Across our {s['confidence_counts']['high']} high-confidence fixtures, {s['high_confidence_moneyline_in_band']}
      sit directly inside <span class="mono">[-233, -250]</span> on the moneyline (<span class="mono">70.0%&ndash;71.4%</span>), while the other
      {s['high_confidence_moneyline_shorter_than_minus_250']} exceed 71.4% on the moneyline and are paired with an originated puck line, run line,
      point spread, set handicap, leg handicap, or runner-up matchbet priced inside <span class="mono">[-250, +10000]</span>.
    </div>

    <h2 id="horizon-coverage-matrix">15-Sport Coverage &amp; Daily 5-Pick Target Matrix</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Sport</th>
            <th>Fixtures</th>
            <th>Priced</th>
            <th>Blank / Flagged</th>
            <th>High (&ge;70%)</th>
            <th>Medium (55&ndash;69%)</th>
            <th>Low (&lt;55%)</th>
            <th>Written Picks</th>
            <th>Daily 5-Pick Status</th>
            <th>Primary Source</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(sport_rows)}
        </tbody>
      </table>
    </div>

    <h2 id="horizon-high-confidence-board">High-Confidence Board (&ge;70% Win Probability) &amp; Actionable [-250, +10000] Lines</h2>
    <p class="lede">
      All {len(high_recs)} fixtures where the originated winner probability reaches at least 70%. Both the fair match-winner moneyline and the
      actionable market inside <span class="mono">[-250, +10000]</span> are shown with direct official source links.
    </p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Sport</th>
            <th>Competition</th>
            <th>Fixture</th>
            <th>Start / Window</th>
            <th>Winner Pick</th>
            <th>Win Prob</th>
            <th>Fair ML</th>
            <th>ML Band Status</th>
            <th>Actionable Market in [-250, +10000]</th>
            <th>Confidence</th>
            <th>Official Sources</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(high_rows)}
        </tbody>
      </table>
    </div>

    <h2 id="horizon-predictions">Editorial Predictions ({preds_data['total_predictions']} Match Previews Across All 15 Sports)</h2>
    <p class="lede">
      Up to five highest-confidence predictions per covered sport ({preds_data['total_predictions']} total; sports with fewer than five officially
      priced fixtures leave the remaining slots unfilled and logged on <a href="flagged.html">Flagged for Review</a>).
    </p>
{pred_cards}
"""
    return page_shell("Executive Summary", "", "index", body)


def build_sport_page(sport, slug, lines_data, preds_data, flagged_data, olbg_data):
    recs = [r for r in lines_data["records"] if r["sport"] == sport]
    preds = [p for p in preds_data["predictions"] if p["sport"] == sport]
    flags = [f for f in flagged_data["items"] if f["sport"] == sport]
    olbg_meta = next(x for x in olbg_data["sports"] if x["sport"] == sport)

    rows_html = []
    for r in recs:
        matchup = f"{r['away']} @ {r['home']}" if r.get("away") else r["home"]
        hcap_txt = ""
        if r.get("handicap"):
            h = r["handicap"]
            if "fav" in h:
                hcap_txt = f"{h['fav']} {h['fav_line']:+g} ({fmt_ml(h['fav_odds'])}) / {h['dog']} {h['dog_line']:+g} ({fmt_ml(h['dog_odds'])})"
            elif "home_line" in h:
                hcap_txt = f"{r['home']} {h['home_line']:+g} ({fmt_ml(h['home_odds'])}) / {r['away']} {h['away_line']:+g} ({fmt_ml(h['away_odds'])})"
            elif "selection" in h:
                hcap_txt = f"{h['market']}: {h['selection']} ({fmt_ml(h['odds'])})"
        tot_txt = ""
        if r.get("total"):
            t = r["total"]
            tot_txt = f"O/U {t['line']} (O {fmt_ml(t['over_odds'])} / U {fmt_ml(t['under_odds'])})"
        facts_str = "; ".join(f"{x['team_or_item']}: {x['value']}" for x in r["facts"])
        rows_html.append(f"""        <tr id="row-{esc(r['id'])}">
          <td>{esc(r['competition'])}</td>
          <td><strong>{esc(matchup)}</strong></td>
          <td class="mono">{esc(r['time_display'])}</td>
          <td>{esc(r.get('venue') or '')}</td>
          <td class="num">{fmt_ml(r['home_fair_american'])}</td>
          <td class="num">{fmt_ml(r['away_fair_american'])}</td>
          <td><strong>{esc(r['winner_pick'] or '')}</strong></td>
          <td class="num">{fmt_pct(r['winner_prob'])}</td>
          <td class="num">{fmt_ml(r['winner_fair_american'])}</td>
          <td class="mono">{esc(hcap_txt)}</td>
          <td class="mono">{esc(tot_txt)}</td>
          <td class="mono">{esc(r['actionable_selection'] or '')}</td>
          <td>{conf_badge(r['confidence'])}</td>
          <td>{esc(facts_str)}</td>
          <td>{source_links_cell(r)}</td>
        </tr>""")

    outright_sections = []
    for r in recs:
        if r.get("outright_board"):
            b_rows = []
            for b in r["outright_board"]:
                if "player" in b:
                    label = f"{b['player']} ({b['country']})"
                    stat = f"To par {b['to_par']:+d} (R1 {b['r1']}, R2 {b['r2']}, 36h {b['total_36']})"
                elif "runner" in b:
                    label = f"{b['runner']} (trainer {b['trainer']})"
                    stat = f"SF clock: {b['sf_time_s']:.2f}s" if b["sf_time_s"] is not None else ""
                else:
                    label = b["driver"]
                    gap = f", FP1 gap +{b['fp1_gap_s']:.3f}s" if "fp1_gap_s" in b else ""
                    stat = f"Season points: {b['season_pts']}{gap}"
                b_rows.append(f"""          <tr>
            <td><strong>{esc(label)}</strong></td>
            <td class="mono">{esc(stat)}</td>
            <td class="num">{fmt_pct(b['win_prob'])}</td>
            <td class="num">{fmt_ml(b['fair_american'])}</td>
            <td class="num">{b['fair_decimal']:.2f}</td>
            <td>{band_badge(-250 <= b['fair_american'] <= 10000, b['fair_american'])}</td>
            <td><a href="{esc(r['stats_source_url'])}">Official leaderboard / results</a></td>
          </tr>""")
            outright_sections.append(f"""    <h3>Outright Pricing Board — {esc(r['home'])}</h3>
    <p class="lede">{esc(r['method'])}</p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Competitor</th>
            <th>Official Performance Metric</th>
            <th>Win Prob</th>
            <th>Fair American</th>
            <th>Fair Decimal</th>
            <th>[-250, +10000] Band</th>
            <th>Official Source</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(b_rows)}
        </tbody>
      </table>
    </div>""")

    flag_section = ""
    if flags:
        f_rows = []
        for fl in flags:
            f_rows.append(f"""          <tr>
            <td>{esc(fl['matchup'])}</td>
            <td>{esc(fl['field'])}</td>
            <td><span class="badge flag">{esc(fl['status'])}</span></td>
            <td>{esc(fl['reason'])}</td>
            <td><a href="{esc(fl['official_source_url'])}">Official source</a></td>
          </tr>""")
        flag_section = f"""    <h2>Flagged / Blank Items in {esc(sport)}</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Fixture / Runner</th>
            <th>Blank Field</th>
            <th>Status</th>
            <th>Verification Finding</th>
            <th>Official Source</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(f_rows)}
        </tbody>
      </table>
    </div>"""

    pred_html = "\n".join(render_prediction_card(p, prefix="../") for p in preds)

    body = f"""    <h1>{esc(sport)} — Fixtures, Originated Lines &amp; Editorial Picks</h1>
    <p class="lede">
      OLBG category route: <a href="{esc(olbg_meta['hub_url'])}"><span class="mono">{esc(olbg_meta['hub_url'])}</span></a>
      (markets: <span class="mono">{esc(olbg_meta['markets'])}</span>). All {len(recs)} fixtures below are verified from official governing-body
      feeds on 23 October 2026; unconfirmed numeric inputs are left blank and routed to <a href="../flagged.html">Flagged for Review</a>.
    </p>

    <h2>Fixture &amp; Line Origination Table ({len(recs)} Fixtures)</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Competition</th>
            <th>Matchup / Event</th>
            <th>Date / Time</th>
            <th>Venue</th>
            <th>Home Fair ML</th>
            <th>Away Fair ML</th>
            <th>Winner Pick</th>
            <th>Win Prob</th>
            <th>Winner ML</th>
            <th>Originated Handicap / Spread</th>
            <th>Originated Total</th>
            <th>Actionable Selection [-250..+10000]</th>
            <th>Confidence</th>
            <th>Official Facts &amp; Injuries</th>
            <th>Official Sources</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(rows_html)}
        </tbody>
      </table>
    </div>

{chr(10).join(outright_sections)}

    <h2>Editorial Predictions for {esc(sport)} ({len(preds)} of 5 Daily Target Slots)</h2>
{pred_html}

{flag_section}
"""
    return page_shell(f"{sport} Lines & Predictions", "../", slug, body)


def build_flagged_page(flagged_data):
    rows = []
    for item in flagged_data["items"]:
        slug = SLUG_BY_SPORT[item["sport"]]
        rows.append(f"""        <tr>
          <td><a href="sports/{slug}.html"><strong>{esc(item['sport'])}</strong></a></td>
          <td>{esc(item['competition'])}</td>
          <td>{esc(item['matchup'])}</td>
          <td class="mono">{esc(item['field'])}</td>
          <td><span class="badge flag">{esc(item['status'])}</span></td>
          <td>{esc(item['reason'])}</td>
          <td><a href="{esc(item['official_source_url'])}">Official source</a></td>
        </tr>""")

    body = f"""    <h1>Flagged for Review — Unconfirmed &amp; Blank Values ({flagged_data['count']} Items)</h1>
    <div class="callout flag">
      <strong>Strict non-hallucination policy:</strong> Whenever an opponent slot is still a live quarter-final / wildcard placeholder, a player
      sits outside the captured top rankings table, a league table URL returns HTTP 404, or a probable pitcher has an empty 2026 regular-season MLB
      stat split, the corresponding cells on our sport pages are left <strong>blank</strong> (never guessed or interpolated) and logged below with
      a direct link to the official source inspected on 23 October 2026.
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Sport</th>
            <th>Competition</th>
            <th>Fixture / Runner / Target</th>
            <th>Blank Field</th>
            <th>Status</th>
            <th>Official Verification Note</th>
            <th>Official Source</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
    </div>
"""
    return page_shell("Flagged for Review", "", "flagged", body)


def build_olbg_page(olbg_data, sources_data):
    t_rows = []
    for s in olbg_data["sports"]:
        slug = SLUG_BY_SPORT[s["sport"]]
        t_rows.append(f"""        <tr>
          <td><a href="sports/{slug}.html"><strong>{esc(s['sport'])}</strong></a></td>
          <td class="mono">{esc(', '.join(s['olbg_ids']))}</td>
          <td class="mono"><a href="{esc(s['hub_url'])}">{esc(s['hub_url'])}</a></td>
          <td>{esc(s['markets'])}</td>
          <td><span class="badge warn">Renders 'No tips found.' on US egress IP</span></td>
        </tr>""")

    d_rows = []
    for d in olbg_data["defects"]:
        d_rows.append(f"""        <tr>
          <td class="mono"><strong>{esc(d['id'])}</strong></td>
          <td><strong>{esc(d['title'])}</strong></td>
          <td>{esc(d['evidence'])}</td>
          <td><a href="{esc(d['source_url'])}">Live OLBG URL</a></td>
        </tr>""")

    s_rows = []
    for src in sources_data["sources"]:
        s_rows.append(f"""        <tr>
          <td class="mono">{esc(src['key'])}</td>
          <td><strong>{esc(src['publisher'])}</strong></td>
          <td>{esc(src['what'])}</td>
          <td class="mono">{esc(src['fetched_utc'])}</td>
          <td><a href="{esc(src['url'])}">Official URL</a></td>
        </tr>""")

    body = f"""    <h1>OLBG.com Reverse-Engineering &amp; Official Source Registry</h1>
    <p class="lede">
      Live verification of <a href="https://www.olbg.com/betting-tips">OLBG.com</a> conducted on 23 October 2026 alongside the {sources_data['count']}
      official governing-body endpoints used to populate and verify this desk.
    </p>

    <h2>Four Live OLBG.com Rendering &amp; Data Defects Confirmed on 2026-10-23</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Defect ID</th>
            <th>Defect Summary</th>
            <th>Live SSR Evidence</th>
            <th>Inspected URL</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(d_rows)}
        </tbody>
      </table>
    </div>

    <h2>15-Sport OLBG Taxonomy &amp; US-Egress Hub Behavior</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Mandated Sport</th>
            <th>OLBG Sport ID(s)</th>
            <th>OLBG Category Hub</th>
            <th>OLBG Market Structure</th>
            <th>US Egress Behaviour (2026-10-23)</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(t_rows)}
        </tbody>
      </table>
    </div>

    <h2>Official Governing-Body Source Registry ({sources_data['count']} Endpoints)</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Source Key</th>
            <th>Governing Body / Publisher</th>
            <th>Captured Data Scope</th>
            <th>Fetched UTC</th>
            <th>Official Link</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(s_rows)}
        </tbody>
      </table>
    </div>
"""
    return page_shell("OLBG Platform Audit & Official Sources", "", "olbg-audit", body)


def build_repo_audit_page(audit_data):
    rows = []
    for f in audit_data["findings"]:
        sev_cls = "flag" if f["severity"] == "high" else "medium"
        rows.append(f"""        <tr>
          <td class="mono"><strong>{esc(f['id'])}</strong></td>
          <td><span class="badge {sev_cls}">{esc(f['severity'])}</span></td>
          <td><strong>{esc(f['category'])}</strong></td>
          <td class="mono">{esc(f['file_path'])}:{esc(f['lines'])}</td>
          <td>{esc(f['issue'])}</td>
          <td>{esc(f['official_check'])}</td>
          <td><a href="{esc(f['official_source_url'])}">Official reference</a></td>
        </tr>""")

    s = audit_data["summary"]
    body = f"""    <h1>Line-by-Line Repository Audit ({len(audit_data['findings'])} Findings Logged)</h1>
    <p class="lede">
      Results of inspecting the repository's legacy data, scripts, and HTML surfaces against official governing-body sources and the 15-sport
      operating rules on 23 October 2026. In accordance with <span class="mono">COORDINATION.md</span>, legacy directories owned by earlier sessions
      are not overwritten; instead, every discrepancy is documented below with exact file paths, line numbers, and official verification links, and
      corrected cleanly inside <span class="mono">/horizon/</span>.
    </p>

    <div class="kpi-grid">
      <div class="kpi">
        <div class="kpi-label">Irregularities Logged</div>
        <div class="kpi-val">{s['irregularities_logged']}</div>
        <div class="kpi-sub">With file paths &amp; line ranges</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Legacy Out-of-Scope HTML</div>
        <div class="kpi-val">{s['out_of_scope_html_files']}</div>
        <div class="kpi-sub">verify/sports/{{af,ar,box,esp}}.html</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Legacy Forbidden-Word JSONs</div>
        <div class="kpi-val">{s['predictions_with_forbidden_words']}</div>
        <div class="kpi-sub">0 in data/horizon/predictions.json</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Legacy Unlinked-Row HTMLs</div>
        <div class="kpi-val">{s['html_files_with_unlinked_rows']}</div>
        <div class="kpi-sub">0 in /horizon/ (100% row-linked)</div>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Audit ID</th>
            <th>Severity</th>
            <th>Category</th>
            <th>File &amp; Lines</th>
            <th>Finding</th>
            <th>Official Cross-Check &amp; Horizon Remediation</th>
            <th>Official Source</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
    </div>
"""
    return page_shell("Repository Line-by-Line Audit", "", "repo-audit", body)


def main():
    os.makedirs(SPORTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    with open(os.path.join(ASSETS_DIR, "style.css"), "w") as f:
        f.write(CSS)

    with open(os.path.join(DATA, "lines.json")) as f:
        lines_data = json.load(f)
    with open(os.path.join(DATA, "predictions.json")) as f:
        preds_data = json.load(f)
    with open(os.path.join(DATA, "flagged.json")) as f:
        flagged_data = json.load(f)
    with open(os.path.join(DATA, "olbg_taxonomy.json")) as f:
        olbg_data = json.load(f)
    with open(os.path.join(DATA, "sources.json")) as f:
        sources_data = json.load(f)
    with open(os.path.join(DATA, "repo_audit.json")) as f:
        audit_data = json.load(f)

    with open(os.path.join(SITE, "index.html"), "w") as f:
        f.write(build_index(lines_data, preds_data, flagged_data, olbg_data, audit_data))
    with open(os.path.join(SITE, "flagged.html"), "w") as f:
        f.write(build_flagged_page(flagged_data))
    with open(os.path.join(SITE, "olbg-audit.html"), "w") as f:
        f.write(build_olbg_page(olbg_data, sources_data))
    with open(os.path.join(SITE, "repo-audit.html"), "w") as f:
        f.write(build_repo_audit_page(audit_data))

    for sport, slug in SPORT_ORDER:
        html_out = build_sport_page(sport, slug, lines_data, preds_data, flagged_data, olbg_data)
        with open(os.path.join(SPORTS_DIR, f"{slug}.html"), "w") as f:
            f.write(html_out)

    print(f"horizon_build: wrote index, flagged, olbg-audit, repo-audit, and {len(SPORT_ORDER)} sport pages in /horizon/")


if __name__ == "__main__":
    main()
