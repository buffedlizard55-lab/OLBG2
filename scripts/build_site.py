#!/usr/bin/env python3
"""Build the static GitHub Pages dashboard from the verified data files.

Outputs (repo root, because GitHub Pages serves main:/):
  index.html, picks.html, flagged.html, methodology.html, sources.html,
  sports/<slug>.html, data/matches.json (already produced by model.py)

Run:  python3 scripts/build_site.py
Exit code 1 if any prediction is under 30 words or any link is broken.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

SPORTS = {
    "Ice Hockey": {"slug": "ice-hockey", "blurb": "NHL — lines originated from this season's official team goal rates."},
    "Basketball": {"slug": "basketball", "blurb": "NBA — lines originated from the completed 2025-26 season as a prior."},
    "Rugby Union": {"slug": "rugby-union", "blurb": "United Rugby Championship Round 4 — lines from the official league table."},
    "Cricket": {"slug": "cricket", "blurb": "ICC-listed internationals — fixtures verified, lines deliberately not originated."},
}

NAV = [
    ("index.html", "Dashboard"),
    ("picks.html", "Picks & predictions"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "Methodology"),
    ("sources.html", "Sources"),
    ("site/index.html", "Evidence desk v2"),
]

E = html.escape


def load(name):
    with open(os.path.join(DATA, name)) as fh:
        return json.load(fh)


def badge(conf: str) -> str:
    cls = {"high": "b-high", "medium": "b-med", "low": "b-low"}.get(conf, "b-unv")
    label = {"high": "High", "medium": "Medium", "low": "Low"}.get(conf, "Unverified")
    return f'<span class="badge {cls}">{label}</span>'


def page(title: str, active: str, body: str, subtitle: str = "") -> str:
    prefix = "../" * active.count("/")
    links = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{prefix}{href}"{cur}>{E(label)}</a>')
    nav = "".join(links)
    prefix = "../" * active.count("/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} · OLBG2 Sports Betting Data</title>
<meta name="description" content="{E(subtitle or title)}">
<link rel="stylesheet" href="{prefix}assets/style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230d1730'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%234f8cff'/%3E%3C/svg%3E">
</head>
<body>
<header class="site">
  <div class="wrap">
    <a class="brand" href="{prefix}index.html"><span class="dot"></span>OLBG2 · Sports Betting Data</a>
    <nav class="main">{nav}</nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="site">
  <div class="wrap">
    <span>Independent line origination · data captured 2026-10-21 UTC · 18+ · Bet responsibly</span>
    <span><a href="{prefix}methodology.html">Methodology</a> · <a href="{prefix}sources.html">Sources</a> · <a href="{prefix}flagged.html">Flagged</a> · <a href="{prefix}site/index.html">Evidence desk v2</a></span>
  </div>
</footer>
</body>
</html>
"""


def stat(k, v, s=""):
    return f'<div class="card stat"><div class="k">{E(k)}</div><div class="v">{v}</div><div class="s">{E(s)}</div></div>'


def match_name(m):
    if m["home"]["name"] and m["away"]["name"]:
        return f'{E(m["away"]["name"])} <span class="muted">@</span> {E(m["home"]["name"])}'
    return "TBC"


def fixture_link(m):
    fs = m.get("fixture_source") or {}
    if not fs.get("url"):
        return '<span class="muted">—</span>'
    return f'<a href="{E(fs["url"])}" rel="noopener">{E(fs.get("name", "source"))}</a>'


def row_summary(m):
    conf = m.get("confidence", "unverified")
    if m["line_status"] != "originated":
        pick = '<span class="badge b-unv">Not originated</span>'
        price = '<span class="muted">—</span>'
    else:
        pick = f'{E(m["pick"]["selection"])}<span class="sub">{E(m["pick"]["market"])} · {m["pick"]["probability"]*100:.1f}% model</span>'
        price = f'<span class="num">{m["pick"]["price"]:.2f}</span>'
    return f"""<tr data-sport="{E(m["sport"])}" data-conf="{E(conf)}">
      <td><span class="match">{match_name(m)}</span><span class="sub">{E(m["competition"])}</span></td>
      <td class="num">{E(m.get("start_display") or "—")}</td>
      <td>{pick}</td>
      <td>{badge(conf)}</td>
      <td class="num">{price}</td>
      <td class="small">{fixture_link(m)}{('<span class="sub"><a href="' + E(m["olbg_event_url"]) + '" rel="noopener">OLBG event</a></span>') if m.get("olbg_event_url") else ''}</td>
    </tr>"""


def market_rows(m):
    if m["line_status"] != "originated":
        reason = E(m.get("reason", "No verified input."))
        return f'<tr><td colspan="4" class="muted small">No line originated — {reason}</td></tr>'
    out = []
    for mk in m["markets"]:
        line = "—" if mk.get("line") in (None, "") else f'{mk["line"]:g}'
        out.append(
            f'<tr><td>{E(mk["market"])}</td><td>{E(mk["selection"])}</td>'
            f'<td class="num">{line}</td><td class="num">{mk["probability"]*100:.1f}%</td>'
            f'<td class="num">{mk["price"]:.2f}</td></tr>'
        )
    return "".join(out)


def inputs_block(m):
    inp = m.get("inputs")
    if not inp:
        return '<span class="muted">—</span>'
    h, a = inp.get("home", {}), inp.get("away", {})
    def fmt(d):
        keys = [k for k in ("record", "gp", "pl", "season", "gf", "ga", "gf_pg", "ga_pg", "pf", "pa", "pts", "form", "home", "road") if k in d]
        return ", ".join(f"{k}={d[k]}" for k in keys)
    return f'<span class="small"><b>{E(m["home"]["name"])}</b>: {E(fmt(h))}<br><b>{E(m["away"]["name"])}</b>: {E(fmt(a))}</span>'


def build_index(matches, preds, flagged):
    c = matches["counts"]
    sport_cards = []
    for sport, meta in SPORTS.items():
        rows = [m for m in matches["matches"] if m["sport"] == sport]
        lined = sum(1 for m in rows if m["line_status"] == "originated")
        high = sum(1 for m in rows if m.get("confidence") == "high")
        sport_cards.append(f"""<a class="card sport-card" href="sports/{meta['slug']}.html">
          <h3>{E(sport)}</h3>
          <p>{E(meta['blurb'])}</p>
          <div class="row"><span>Fixtures</span><b>{len(rows)}</b></div>
          <div class="row"><span>Lines originated</span><b>{lined}</b></div>
          <div class="row"><span>High confidence</span><b>{high}</b></div>
        </a>""")

    table = "".join(row_summary(m) for m in matches["matches"])
    body = f"""
<section class="hero">
  <h1>Verified fixtures, our own lines, and the confidence behind every pick.</h1>
  <p class="lede">A reverse-engineered view of OLBG's sports coverage: every fixture re-checked against the
  official league or governing body, every price originated here from verified data, and every gap left blank
  and flagged rather than guessed.</p>
  <p class="meta">Capture window 2026-10-21 05:10–05:45 UTC · {c['total']} fixtures · {c['originated']} with originated lines ·
  {c['high']} high-confidence picks · {len(flagged['items'])} items flagged for review</p>
</section>

<div class="grid stats">
  {stat("Fixtures verified", c['total'], "official source on every row")}
  {stat("Lines originated", c['originated'], "moneyline · handicap · totals")}
  {stat("High-confidence picks", c['high'], "written predictions included")}
  {stat("Flagged for review", len(flagged['items']), "blank, unverified or irregular")}
</div>

<h2 class="section">Sports covered</h2>
<p class="section-sub">Thirteen of OLBG's seventeen included sports are not covered in this release. Each one is listed on the flagged page with the reason — absence here is not evidence that OLBG lists no events.</p>
<div class="grid sports">{''.join(sport_cards)}</div>

<h2 class="section">All fixtures</h2>
<p class="section-sub">Filter by sport, confidence or search a team. Every row links to the official fixture source; OLBG event links appear only where the pairing matched exactly.</p>
<div class="panel">
  <div class="toolbar">
    <input id="q" type="search" placeholder="Search team, competition or pick…" aria-label="Search fixtures">
    <select id="fsport" aria-label="Filter by sport">
      <option value="">All sports</option>
      {''.join(f'<option>{E(s)}</option>' for s in SPORTS)}
    </select>
    <select id="fconf" aria-label="Filter by confidence">
      <option value="">Any confidence</option>
      <option value="high">High</option>
      <option value="medium">Medium</option>
      <option value="low">Low</option>
      <option value="unverified">Not originated</option>
    </select>
    <span class="hint" id="count"></span>
  </div>
  <div class="table-scroll">
  <table id="tbl">
    <thead><tr><th>Match</th><th>Start</th><th>Pick</th><th>Confidence</th><th>Price</th><th>Official source</th></tr></thead>
    <tbody>{table}</tbody>
  </table>
  </div>
</div>

<h2 class="section">How to read this</h2>
<details open>
  <summary>Prices are ours, not the market's</summary>
  <p>OLBG publishes tip percentages but no prices, and no bookmaker odds were used. Every price above is
  <code>1 / (probability × 1.04)</code>, i.e. our own fair price plus a 4% theoretical margin. They are not
  available prices and should not be read as such. The full formulas live in <a href="methodology.html">Methodology</a>.</p>
</details>
<details>
  <summary>What "confidence" means here</summary>
  <p>Confidence grades how decisive the model is <em>and</em> how much verified data stands behind it.
  High requires a probability of at least 65% from at least seven games of current-season data. The NBA's
  season is one game old, so NBA picks are capped at medium; the URC has played three rounds, so it is also
  capped at medium.</p>
</details>
<details>
  <summary>Sports we could not cover in this capture</summary>
  <p>Baseball, Darts, Golf, Greyhounds, Handball, Motor Racing, Rugby League, Snooker, Tennis, Volleyball,
  eSports, Aussie Rules and Gaelic Football were listed by OLBG but could not be verified (or, for baseball,
  had no games). Each has an entry on the <a href="flagged.html">Flagged for review</a> page with the reason.</p>
</details>

<script>
(function () {{
  var q = document.getElementById('q'), fs = document.getElementById('fsport'),
      fc = document.getElementById('fconf'), tbl = document.getElementById('tbl'),
      count = document.getElementById('count');
  function apply() {{
    var term = (q.value || '').toLowerCase(), sport = fs.value, conf = fc.value, shown = 0;
    Array.prototype.forEach.call(tbl.tBodies[0].rows, function (row) {{
      var text = row.innerText.toLowerCase();
      var okTerm = !term || text.indexOf(term) > -1;
      var okSport = !sport || row.getAttribute('data-sport') === sport;
      var rowConf = row.getAttribute('data-conf');
      var okConf = !conf || (conf === 'unverified' ? rowConf !== 'high' && rowConf !== 'medium' && rowConf !== 'low' : rowConf === conf);
      var show = okTerm && okSport && okConf;
      row.style.display = show ? '' : 'none';
      if (show) shown++;
    }});
    count.textContent = shown + ' of ' + tbl.tBodies[0].rows.length + ' shown';
  }}
  [q, fs, fc].forEach(function (el) {{ el.addEventListener('input', apply); el.addEventListener('change', apply); }});
  apply();
}})();
</script>
"""
    return page("Dashboard", "index.html", body, "Verified OLBG fixtures with independently originated betting lines and confidence-graded picks.")


def build_sport_page(sport, matches, preds):
    meta = SPORTS[sport]
    rows = [m for m in matches if m["sport"] == sport]
    lined = sum(1 for m in rows if m["line_status"] == "originated")
    high = [m for m in rows if m.get("confidence") == "high"]
    pred_by_id = {p["match_id"]: p for p in preds["predictions"]}

    cards = []
    for m in rows:
        if m["line_status"] != "originated":
            markets = market_rows(m)
            pick_html = '<span class="badge b-unv">Not originated</span>'
        else:
            markets = market_rows(m)
            pick_html = f'<span class="sel">{E(m["pick"]["selection"])}</span> {badge(m["confidence"])}'
        model = m.get("model")
        model_html = ""
        if model:
            kv = " · ".join(f"{E(k).replace('_',' ')}: {v}" for k, v in model.items())
            model_html = f'<p class="small muted" style="margin:10px 0 0">{kv}</p>'
        pred = pred_by_id.get(m["id"])
        pred_html = ""
        if pred:
            pred_html = f"""<div style="margin-top:14px;border-top:1px solid var(--line);padding-top:12px">
              <div class="pill">High-confidence prediction</div>
              <p style="margin:8px 0 0"><b>{E(pred['headline'])}</b></p>
              <p class="small" style="margin:6px 0 0">{E(pred['text'])}</p></div>"""
        cards.append(f"""
        <div class="card" style="margin:14px 0">
          <div style="display:flex;gap:14px;justify-content:space-between;flex-wrap:wrap;align-items:baseline">
            <div><span class="match" style="font-size:16px">{match_name(m)}</span>
              <span class="sub">{E(m['competition'])} · {E(m.get('start_display') or '')}{(' · ' + E(m['venue'])) if m.get('venue') else ''}</span></div>
            <div>{pick_html}</div>
          </div>
          <p class="small muted" style="margin:10px 0 6px">Verified inputs — {inputs_block(m)}</p>
          <div class="table-scroll" style="max-height:none">
          <table><thead><tr><th>Market</th><th>Selection</th><th>Line</th><th>Model %</th><th>Our price</th></tr></thead>
          <tbody>{markets}</tbody></table></div>
          {model_html}
          {pred_html}
          <p class="small" style="margin:12px 0 0">Fixture source: {fixture_link(m)}
          {(' · <a href="' + E(m['olbg_event_url']) + '" rel="noopener">OLBG event page</a>') if m.get('olbg_event_url') else ''}</p>
        </div>""")

    body = f"""
<section class="hero">
  <h1>{E(sport)}</h1>
  <p class="lede">{E(meta['blurb'])}</p>
  <p class="meta">{len(rows)} verified fixtures · {lined} with originated lines · {len(high)} high-confidence picks</p>
</section>
<div class="note info">Every price on this page is originated by this project from verified official data, not taken
from a bookmaker. Blank values mean the input could not be verified — see
<a href="../flagged.html">Flagged for review</a>.</div>
{''.join(cards)}
<p class="small muted" style="margin-top:22px"><a href="../index.html">← Back to dashboard</a></p>
"""
    return page(sport, f"sports/{meta['slug']}.html", body, meta["blurb"])


def build_picks(matches, preds):
    m_by_id = {m["id"]: m for m in matches["matches"]}
    cards = []
    for p in preds["predictions"]:
        m = m_by_id[p["match_id"]]
        facts = "".join(f'<li>{E(f["claim"])} — <a href="{E(f["source"])}" rel="noopener">source</a></li>' for f in p["facts"])
        cards.append(f"""
        <div class="card pick">
          <div>{badge("high")} <span class="pill">{E(m['sport'])}</span></div>
          <h3 style="margin-top:10px">{E(p['headline'])}</h3>
          <div class="small muted">{match_name(m)} · {E(m.get('start_display') or '')}</div>
          <div class="sel" style="margin-top:10px">{E(p['selection'])}</div>
          <p>{E(p['text'])}</p>
          <div class="foot">Model probability {m['pick']['probability']*100:.1f}% · our price {m['pick']['price']:.2f} · {len(p['text'].split())} words</div>
          <ul class="facts">{facts}</ul>
        </div>""")

    rows = []
    for m in sorted(matches["matches"], key=lambda x: ({"high": 0, "medium": 1, "low": 2}.get(x.get("confidence"), 3), x["sport"])):
        if m["line_status"] != "originated":
            continue
        rows.append(f"""<tr><td>{E(m['sport'])}</td><td>{match_name(m)}</td>
          <td>{E(m['pick']['selection'])}</td><td class="num">{m['pick']['probability']*100:.1f}%</td>
          <td class="num">{m['pick']['price']:.2f}</td><td>{badge(m['confidence'])}</td></tr>""")

    body = f"""
<section class="hero">
  <h1>Picks and predictions</h1>
  <p class="lede">One selection per fixture, graded by how decisive the model is and how much verified data backs it.
  Written predictions exist only for high-confidence picks — four NHL games in this release.</p>
  <p class="meta">{len(preds['predictions'])} written predictions · {matches['counts']['high']} high · {matches['counts']['medium']} medium · {matches['counts']['low']} low</p>
</section>

<div class="grid picks">{''.join(cards)}</div>

<h2 class="section">Every selection</h2>
<p class="section-sub">Low-confidence rows are honest reads on thin samples, not recommendations.</p>
<div class="panel"><div class="table-scroll"><table>
<thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th>Model %</th><th>Our price</th><th>Confidence</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></div>

<div class="note">No pick was made on a market we could not originate. NBA totals, all cricket markets and the
San Jose–Ottawa NHL game are blank for that reason.</div>
"""
    return page("Picks & predictions", "picks.html", body, "Confidence-graded selections with verified-source written predictions.")


def build_flagged(flagged, matches):
    order = {"high": 0, "medium": 1, "low": 2}
    items = sorted(flagged["items"], key=lambda i: (order.get(i["severity"], 3), i["id"]))
    rows = "".join(f"""<tr>
      <td class="mono">{E(i['id'])}</td>
      <td><span class="badge b-sev-{E(i['severity'])}">{E(i['severity']).title()}</span></td>
      <td>{E(i['category'])}</td>
      <td><b>{E(i['item'])}</b><span class="sub" style="max-width:560px">{E(i['detail'])}</span></td>
      <td class="small"><a href="{E(i['source'])}" rel="noopener">official / source page</a></td>
    </tr>""" for i in items)

    blanks = []
    for m in matches["matches"]:
        if m["line_status"] != "originated":
            blanks.append(f"<li><b>{match_name(m)}</b> ({E(m['sport'])}) — {E(m.get('reason','not originated'))}</li>")
        for mk in m.get("markets_not_originated", []):
            blanks.append(f"<li><b>{match_name(m)}</b> ({E(m['sport'])}) · {E(mk['market'])} — {E(mk['reason'])}</li>")

    body = f"""
<section class="hero">
  <h1>Flagged for review</h1>
  <p class="lede">Everything that could not be confirmed from an official source, every value deliberately left
  blank, and every irregularity found in OLBG's own pages. These items do not block publication — they are the
  review queue.</p>
  <p class="meta">{len(items)} items · {len(blanks)} blank or unoriginated values</p>
</section>

<div class="panel"><div class="table-scroll"><table>
<thead><tr><th>ID</th><th>Severity</th><th>Category</th><th>Item and detail</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div></div>

<h2 class="section">Values left blank on purpose</h2>
<p class="section-sub">No value in this list was estimated. Blank means the official source did not supply it inside the capture window.</p>
<div class="panel" style="padding:16px 20px"><ul class="small">{''.join(blanks)}</ul></div>

<h2 class="section">What a reviewer should do next</h2>
<details open><summary>Highest-value fixes</summary>
<ul>
<li>Capture the missing NHL game on 22 October (Seattle home) and the Sharks' goal totals, then re-run <code>scripts/model.py</code>.</li>
<li>Read the ATP rankings and PDC Order of Merit from a browser-rendered page so tennis and darts can be lined.</li>
<li>Confirm the Gaelic football club fixtures on the relevant county board sites before publishing them.</li>
<li>Survey the eight sports that were not captured at all (Handball, Volleyball, Golf, Motor Racing, Greyhounds, eSports, Aussie Rules, Rugby League).</li>
</ul></details>
"""
    return page("Flagged for review", "flagged.html", body, "Unverified, blank and irregular items with source links.")


def build_methodology(matches):
    p = matches["params"]
    body = f"""
<section class="hero">
  <h1>Methodology</h1>
  <p class="lede">How a fixture becomes a line: what we take from OLBG, what we re-verify, how the probabilities are
  computed, and the exact rules that decide a confidence grade.</p>
</section>

<h2 class="section">1. Scope</h2>
<p class="section-sub">Included: Tennis, Basketball, Golf, Cricket, Snooker, Rugby Union, Rugby League, Baseball,
Ice Hockey, Motor Racing, Darts, Handball, Volleyball, Aussie Rules, eSports, Gaelic Football, Greyhounds.</p>
<p>Excluded by the brief: football (soccer, OLBG id 1), horse racing (2), American football (11), boxing (16),
cycling (17) and hurling (26). UFC/MMA have no separate OLBG sport id — they are filed under Boxing/16, so the
exclusion of id 16 covers them. "Specials" are not a sport on OLBG; they are a bet-type, and no specials market
is included anywhere. The list is enforced in <code>scripts/config.py</code>.</p>
<div class="note info">Two scope judgement calls, both flagged: Gaelic Football is treated as a distinct sport and kept
(the brief excludes "football", which we read as soccer); hurling is excluded by name.</div>

<h2 class="section">2. What OLBG gives us, and what it does not</h2>
<p>Sport hub pages supply the event list, the event_id, the market label a tipster used, and tip percentages.
They do <b>not</b> publish prices. Nothing in this dataset uses OLBG tip percentages as a probability: our lines
are originated independently. OLBG is only an event-discovery and market-vocabulary source.</p>

<h2 class="section">3. Verification</h2>
<p>Every fixture is re-checked against the league or governing body before it is published: NBA.com, the NHL
score API, the URC match centre, the ICC match list, the WST draw. If the official source does not confirm the
fixture, the row is not published and the OLBG event goes to the flagged page. If the official source confirms the
fixture but no verified strength input exists, the fixture is published with a blank line and a stated reason.</p>

<h2 class="section">4. The models</h2>
<h3>Ice Hockey (NHL)</h3>
<p>A multiplicative Poisson attack/defence model on season-to-date goals, with empirical-Bayes shrinkage because
only 7–11 games have been played.</p>
<pre><code>league_avg = mean(goals for per game) over all 32 teams
w          = gp / (gp + {p['nhl_shrink_k']})
attack_i   = 1 + w * ((gf_i / gp_i) / league_avg - 1)
defence_i  = 1 + w * ((ga_i / gp_i) / league_avg - 1)
lambda_home = league_avg * attack_home * defence_away * {p['nhl_home_ice_factor']}
lambda_away = league_avg * attack_away * defence_home / {p['nhl_home_ice_factor']}
P(home)    = Poisson score grid, tie split 50/50 (overtime / shootout)
puck line  = fixed at 1.5, P(home covers) = P(margin >= 2)
total line = nearest half-point to lambda_home + lambda_away</code></pre>
<p class="small muted">Home-ice factor {p['nhl_home_ice_factor']} and shrinkage k={p['nhl_shrink_k']} are our own
line-setting parameters, not sourced facts. They are recorded in every NHL row.</p>

<h3>Basketball (NBA)</h3>
<p>The 2026-27 season is one game old and every team playing on 21 October was 0-0, so the completed 2025-26
season is used as a prior, shrunk 25% toward .500.</p>
<pre><code>raw      = wins / (wins + losses)            # 2025-26
shrunk   = 0.75 * raw + 0.25 * 0.5
rating   = logit(shrunk)
margin   = {p['nba_points_per_logit']} * (rating_home + {p['nba_home_logit_edge']} - rating_away)
P(home)  = logistic(margin / {p['nba_margin_sigma']})
handicap = nearest half-point to -margin
total    = NOT ORIGINATED (no verified points-for/against input was captured)</code></pre>

<h3>Rugby Union (URC)</h3>
<p>Points for and against per game from the official league table, shrunk toward the league mean because only
three rounds have been played.</p>
<pre><code>w = pl / (pl + {p['urc_shrink_k']})
attack_i  = 1 + w * ((pf_i / pl_i) / league_pf - 1)
defence_i = 1 + w * ((pa_i / pl_i) / league_pa - 1)
expected_home = league_pf * attack_home * defence_away + {p['urc_home_points']}/2
expected_away = league_pa * attack_away * defence_home - {p['urc_home_points']}/2
P(home)  = logistic((expected_home - expected_away) / {p['urc_margin_sigma']})
handicap = nearest half-point to the expected margin
total    = expected_home + expected_away, nearest half-point</code></pre>

<h3>Prices</h3>
<p>Every price is <code>round(1 / (p * 1.04), 2)</code>, clamped to 1.05–12.00. That is a fair price plus a 4%
theoretical margin. <b>These are not bookmaker prices and were not compared to any bookmaker.</b></p>

<h2 class="section">5. Confidence rules</h2>
<table>
<thead><tr><th>Sport</th><th>High</th><th>Medium</th><th>Low</th></tr></thead>
<tbody>
<tr><td>NHL</td><td>p ≥ 65% and both teams ≥ {p['nhl_min_gp_high']} games played</td><td>p ≥ 57% with ≥ {p['nhl_min_gp_high']} games, or p ≥ 68% with ≥ {p['nhl_min_gp_medium']}</td><td>everything else</td></tr>
<tr><td>NBA</td><td>not permitted — zero current-season games</td><td>p ≥ 68%</td><td>p &lt; 68%</td></tr>
<tr><td>URC</td><td>not permitted — three rounds played</td><td>p ≥ 62%</td><td>p &lt; 62%</td></tr>
</tbody></table>
<p class="small muted" style="margin-top:10px">The rule is deliberately conservative: promoting a three-game sample to
"high" would be a confidence trick, not a prediction.</p>

<h2 class="section">6. Predictions</h2>
<p>Written predictions are produced only for high-confidence picks. Each one must be at least 30 words, name the
selection explicitly, and state the team, its record and goal rate, at least one named player with a verified
statistic, and the model probability. No claim about injuries, line-ups, travel or transfers appears anywhere,
because none could be verified from an official source in this capture. Every factual sentence carries a source
link on the <a href="picks.html">Picks page</a>.</p>

<h2 class="section">7. Provenance</h2>
<p>Raw captures and what was taken from each URL are logged in <code>research/collection-log.md</code>. The
machine-readable dataset is <a href="data/matches.json">data/matches.json</a>; regenerate it with
<code>python3 scripts/model.py</code> and rebuild this site with <code>python3 scripts/build_site.py</code>.
The builder fails the build if a prediction is under 30 words or a link is broken.</p>
"""
    return page("Methodology", "methodology.html", body, "Line origination formulas, confidence rules and verification process.")


def build_sources(sources, matches):
    rows = "".join(f"""<tr>
      <td class="mono">{E(s['id'])}</td>
      <td>{E(s['publisher'])}</td>
      <td>{E(s['type'])}</td>
      <td class="small"><a href="{E(s['url'])}" rel="noopener">{E(s['url'])}</a></td>
      <td class="small">{E(s['used_for'])}{('<span class="sub">' + E(s['note']) + '</span>') if s.get('note') else ''}</td>
    </tr>""" for s in sources["sources"])

    per_source = {}
    for m in matches["matches"]:
        for key in ("fixture_source", "data_source"):
            src = m.get(key)
            if src and src.get("url"):
                per_source.setdefault(src["url"], 0)
                per_source[src["url"]] += 1

    body = f"""
<section class="hero">
  <h1>Sources</h1>
  <p class="lede">Every URL used to build this dataset, what it verified, and whether it is an official body.
  OLBG rows are discovery-only and marked as such.</p>
  <p class="meta">{len(sources['sources'])} sources · {len(per_source)} of them are cited directly by a published fixture row</p>
</section>
<div class="panel"><div class="table-scroll"><table>
<thead><tr><th>ID</th><th>Publisher</th><th>Type</th><th>URL</th><th>Used for</th></tr></thead>
<tbody>{rows}</tbody></table></div></div>
<div class="note">Capture window 2026-10-21 05:10–05:45 UTC. Pages change; a reviewer re-checking later may see
different numbers, especially on the NHL and NBA standings pages, which update after every game.</div>
"""
    return page("Sources", "sources.html", body, "Official and discovery sources with what each one verified.")


def collect_internal_links(pages):
    """Resolve every relative href on disk. Absolute paths are rejected on purpose:
    the site must work both on GitHub Pages and from a local checkout."""
    problems = []
    for path, content in pages.items():
        base = os.path.dirname(path)
        for href in re.findall(r'href="([^"]+)"', content):
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                if href.startswith("http://"):
                    problems.append(f"{path}: insecure external link {href}")
                continue
            if href.startswith("/"):
                problems.append(f"{path}: absolute internal link {href}")
                continue
            target = os.path.normpath(os.path.join(base, href.split("#")[0]))
            if target.endswith(os.sep) or target == ".":
                target = os.path.join(target, "index.html")
            if not os.path.exists(os.path.join(ROOT, target)):
                problems.append(f"{path}: broken internal link {href}")
    return problems


def main():
    matches = load("matches.json")
    preds = load("predictions.json")
    flagged = load("flagged.json")
    sources = load("sources.json")

    short = [p for p in preds["predictions"] if len(p["text"].split()) < 30]
    if short:
        print("FAIL: predictions under 30 words:", [p["match_id"] for p in short])
        return 1

    pages = {
        "index.html": build_index(matches, preds, flagged),
        "picks.html": build_picks(matches, preds),
        "flagged.html": build_flagged(flagged, matches),
        "methodology.html": build_methodology(matches),
        "sources.html": build_sources(sources, matches),
    }
    for sport, meta in SPORTS.items():
        pages[f"sports/{meta['slug']}.html"] = build_sport_page(sport, matches["matches"], preds)

    for path, content in pages.items():
        full = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write(content)

    open(os.path.join(ROOT, ".nojekyll"), "w").close()

    problems = collect_internal_links(pages)
    for m in matches["matches"]:
        if not (m.get("fixture_source") or {}).get("url"):
            problems.append(f"match {m['id']} has no fixture source URL")

    if problems:
        print("BUILD PROBLEMS:")
        for p in problems:
            print(" -", p)
        return 1
    print(f"Built {len(pages)} pages, {len(matches['matches'])} fixtures, {len(preds['predictions'])} predictions, no broken links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
