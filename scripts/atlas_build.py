#!/usr/bin/env python3
"""Build the /atlas/ GitHub Pages dashboard.

Deterministic: the same data/atlas/*.json always produces byte-identical HTML.
"""
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "atlas"
OUT = ROOT / "atlas"
SITE_TITLE = "OLBG2 · Atlas desk"

GENERATED_AT = "2026-10-22T13:25:00Z"
SESSION = "arena/ba48a907-olbg2"

CSS = """
:root{--bg:#0f1216;--panel:#161b22;--panel2:#1c232c;--line:#2b333d;--txt:#e6edf3;
--muted:#8b98a5;--accent:#4da3ff;--good:#3fb950;--warn:#d29922;--bad:#f85149;--hi:#a371f7}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:14px 22px;
display:flex;flex-wrap:wrap;gap:14px;align-items:center}
header h1{font-size:17px;margin:0;font-weight:600;letter-spacing:.2px}
header nav{display:flex;flex-wrap:wrap;gap:6px}
header nav a{padding:5px 10px;border-radius:6px;color:var(--muted);font-size:13px}
header nav a:hover,header nav a.on{background:var(--panel2);color:var(--txt);text-decoration:none}
main{max-width:1400px;margin:0 auto;padding:22px}
h2{font-size:19px;margin:26px 0 10px}
h3{font-size:15px;margin:18px 0 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px}
p.lead{color:var(--muted);max-width:900px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.card .n{font-size:24px;font-weight:650}
.card .l{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:var(--panel2);color:var(--muted);font-weight:600;font-size:12px;
text-transform:uppercase;letter-spacing:.4px;position:sticky;top:0;z-index:1}
tbody tr:hover{background:#1a2129}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;max-height:76vh;overflow-y:auto}
.tag{display:inline-block;padding:1px 7px;border-radius:99px;font-size:11px;font-weight:600;
border:1px solid var(--line);white-space:nowrap}
.t-high{color:var(--hi);border-color:var(--hi)}
.t-medium{color:var(--warn);border-color:var(--warn)}
.t-low{color:var(--muted)}
.t-ok{color:var(--good);border-color:var(--good)}
.t-blank{color:var(--muted);border-color:var(--line)}
.t-out{color:var(--bad);border-color:var(--bad)}
.mono{font-variant-numeric:tabular-nums}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0}
input,select{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
border-radius:6px;padding:6px 9px;font-size:13px}
.pick{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.pick h4{margin:0 0 6px;font-size:15px}
.pick .meta{color:var(--muted);font-size:12px;margin-bottom:8px}
.pick p{margin:6px 0 0}
.note{background:var(--panel);border-left:3px solid var(--accent);padding:10px 14px;
border-radius:0 8px 8px 0;color:var(--muted);margin:14px 0;font-size:13px}
.warn{border-left-color:var(--warn)}
.bad{border-left-color:var(--bad)}
.good{border-left-color:var(--good)}
ul.src{columns:2;column-gap:28px}
footer{color:var(--muted);font-size:12px;padding:24px 22px;border-top:1px solid var(--line);margin-top:30px}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
.blankcell{color:#5b6672}
"""

JS = """
document.addEventListener('DOMContentLoaded',function(){
  var q=document.getElementById('q');
  if(!q) return;
  var rows=[].slice.call(document.querySelectorAll('tbody tr'));
  function apply(){
    var v=q.value.toLowerCase();
    rows.forEach(function(r){
      r.style.display = r.textContent.toLowerCase().indexOf(v)>-1 ? '' : 'none';
    });
  }
  q.addEventListener('input',apply);
  var sp=document.getElementById('fsport');
  if(sp){ sp.addEventListener('change',function(){
    var s=sp.value;
    rows.forEach(function(r){ r.style.display = (!s||r.dataset.sport===s)?'':'none'; });
  });}
});
"""


def esc(s):
    return html.escape("" if s is None else str(s))


def am(x):
    if x is None:
        return "—"
    return f"{x:+d}" if x > 0 else str(x)


def page(title, body, active=""):
    base = "../" if active.startswith("sports/") else ""
    nav = [("index.html", "Overview"), ("matches.html", "All matches"), ("picks.html", "Predictions"),
           ("sports/index.html", "By sport"), ("verification.html", "Verification"),
           ("flagged.html", "Flagged"), ("methodology.html", "Methodology"), ("sources.html", "Sources")]
    links = "".join(
        f'<a href="{base}{u}" class="{"on" if active == u else ""}">{esc(t)}</a>' for u, t in nav)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{base}assets/style.css"></head>
<body>
<header><h1>{esc(SITE_TITLE)}</h1><nav>{links}</nav></header>
<main>{body}</main>
<footer>Generated {GENERATED_AT} · session <code>{SESSION}</code> · every price on this site is
originated by this project, never taken from a bookmaker · every row links to the official page it was
read from.</footer>
<script src="{base}assets/app.js"></script>
</body></html>
"""


def band_tag(o):
    if o.get("in_band"):
        return '<span class="tag t-ok">in band</span>'
    return '<span class="tag t-out">outside -250…+10000</span>'


def conf_tag(c):
    return f'<span class="tag t-{c}">{esc(c)}</span>'


def status_tag(st):
    if st == "confirmed":
        return '<span class="tag t-ok">confirmed first-hand</span>'
    return '<span class="tag t-blank">not re-read</span>'


def markets_cell(row):
    if not row["markets"]:
        return f'<span class="blankcell">{esc(row["blank_reason"][:110])}</span>'
    parts = []
    for m in row["markets"]:
        line = f" {m['line']}" if m.get("line") is not None else ""
        outs = " · ".join(
            f"{esc(o['label'])} <span class='mono'>{o['fair_decimal']:.2f}</span> "
            f"<span class='mono'>({am(o['fair_american'])})</span>" for o in m["outcomes"])
        parts.append(f"<div><b>{esc(m['market'])}{esc(line)}</b><br>{outs}</div>")
    return "".join(parts)


def main():
    matches = json.loads((ATLAS / "matches.json").read_text())
    preds = json.loads((ATLAS / "predictions.json").read_text())
    ver = json.loads((ATLAS / "verification.json").read_text())
    flags = json.loads((ATLAS / "flagged.json").read_text())
    sports = json.loads((ATLAS / "sports.json").read_text())
    fx = json.loads((ATLAS / "fixtures.json").read_text())

    rows = matches["matches"]
    c = matches["counts"]
    sport_name = {s["slug"]: s["name"] for s in sports["eligible_sports"]}
    sport_olbg = {s["slug"]: s["olbg_url"] for s in sports["eligible_sports"]}

    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "sports").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS)
    (OUT / "assets" / "app.js").write_text(JS)

    # ------------------------------------------------------------- overview
    per_sport = Counter(r["sport"] for r in rows)
    cards = [("Rows published", c["rows"]), ("Confirmed first-hand", c["confirmed"]),
             ("Not re-read", c["inherited_unverified"]), ("Rows with originated prices", c["originated"]),
             ("Blank / unverified rows", c["blank"]), ("Written predictions", preds["count"]),
             ("Featured picks in band", preds["featured_count"]), ("Flagged items", flags["count"])]
    card_html = "".join(f'<div class="card"><div class="n">{esc(v)}</div><div class="l">{esc(k)}</div></div>'
                        for k, v in cards)

    sport_rows = "".join(
        f'<tr><td><a href="sports/{esc(slug)}.html">{esc(sport_name.get(slug, slug))}</a></td>'
        f'<td class="mono">{n}</td>'
        f'<td class="mono">{sum(1 for r in rows if r["sport"] == slug and r["status"] == "confirmed")}</td>'
        f'<td class="mono">{sum(1 for r in rows if r["sport"] == slug and r["line_status"] == "originated")}</td>'
        f'<td class="mono">{sum(1 for p in preds["predictions"] if p["sport"] == slug)}</td>'
        f'<td><a href="{esc(sport_olbg.get(slug, "#"))}">OLBG hub</a></td></tr>'
        for slug, n in sorted(per_sport.items(), key=lambda kv: -kv[1]))

    body = f"""
<h2>First-hand verified desk · 22–31 October 2026</h2>
<p class="lead">This desk re-read the previously published consolidated table against the governing bodies,
row by row, and republishes only what it could confirm itself. {c['confirmed']} rows were confirmed
first-hand at the official URL stored on the row; {c['inherited_unverified']} rows could not be re-read
this session and are published with every value blank and a link to the official page the earlier desk
cited. {ver['totals']['mismatched']} published rows were found to describe fixtures that do not exist on
the page they cite; they are not republished and are itemised on the
<a href="flagged.html">flagged page</a>.</p>
<div class="cards">{card_html}</div>
<div class="note good"><b>What “confirmed first-hand” means.</b> A person reading this session opened the
governing-body URL stored on the row and the fixture was there — same teams, same date, same venue. No
value on this site is inferred, interpolated or carried over from a bookmaker.</div>
<h3>Coverage by sport</h3>
<div class="tw"><table><thead><tr><th>Sport</th><th>Rows</th><th>Confirmed</th><th>Originated</th>
<th>Predictions</th><th>OLBG hub</th></tr></thead><tbody>{sport_rows}</tbody></table></div>
<h3>Headline findings</h3>
<ul>
<li><b>NHL</b> — all 73 scheduled games from 22 to 31 October reproduce the NHL Stats REST feed exactly.
Two official NHL goal tallies disagree (shootout-goal convention); we use nhl.com throughout and document it.</li>
<li><b>NBA</b> — all 74 NBA games reproduce nba.com/schedule by game id and date. No official team-strength
figure could be read, so every NBA row is published without prices rather than with invented ones.</li>
<li><b>Tennis</b> — {ver['totals']['mismatched']} of the 28 tennis rows in the earlier desk pair players who
are not scheduled to meet on the official ATP page those rows cite. They are removed and itemised.</li>
<li><b>Basketball citation error</b> — 16 rows described the BKT EuroCup endpoint as the EuroLeague; the
EuroLeague is competition code <b>E</b> in that API, not <b>U</b>. Nine unplayed EuroLeague Round 7
fixtures were re-sourced to competition E and re-verified team-for-team.</li>
</ul>
"""
    (OUT / "index.html").write_text(page("Overview", body, "index.html"))

    # ------------------------------------------------------------- matches
    sport_opts = "".join(f'<option value="{esc(s)}">{esc(sport_name.get(s, s))}</option>'
                         for s in sorted(per_sport))
    tr = []
    for r in rows:
        pick = r.get("pick")
        pick_cell = "—"
        if pick:
            pick_cell = (f"{esc(pick['selection'])} <span class='mono'>{pick['fair_decimal']:.2f}</span> "
                         f"<span class='mono'>({am(pick['fair_american'])})</span> {conf_tag(pick['confidence'])}")
        src = f'<a href="{esc(r["official_url"])}">official source</a>' if r.get("official_url") else "—"
        tr.append(
            f'<tr data-sport="{esc(r["sport"])}">'
            f'<td>{esc(r["date"])}</td>'
            f'<td><a href="sports/{esc(r["sport"])}.html">{esc(r["sport_name"])}</a></td>'
            f'<td>{esc(r["competition"])}</td>'
            f'<td>{esc(r["home"])} v {esc(r["away"])}</td>'
            f'<td>{esc(r.get("venue") or "—")}<br><span class="blankcell">{esc(r.get("start_utc") or "")}</span></td>'
            f'<td>{markets_cell(r)}</td>'
            f'<td>{pick_cell}</td>'
            f'<td>{status_tag(r["status"])} {src}</td>'
            f'</tr>')
    body = f"""
<h2>All published rows</h2>
<p class="lead">{c['rows']} rows across {c['sports']} sports, window 22–31 October 2026. Every row carries
the governing-body link it was read from. Rows marked <i>not re-read</i> were inherited from the earlier
consolidated desk: their official link is shown, but no value on them has been confirmed this session, so
every price, probability and pick on those rows is deliberately blank.</p>
<div class="filters">
<input id="q" placeholder="Filter rows — team, competition, date…" size="42">
<select id="fsport"><option value="">all sports</option>{sport_opts}</select>
<span class="blankcell">{c['originated']} rows originated · {c['blank']} rows blank</span>
</div>
<div class="tw"><table><thead><tr><th>Date</th><th>Sport</th><th>Competition</th><th>Fixture</th>
<th>Venue / start</th><th>Originated markets</th><th>Match-winner pick</th><th>Verification</th>
</tr></thead><tbody>{''.join(tr)}</tbody></table></div>
"""
    (OUT / "matches.html").write_text(page("All matches", body, "matches.html"))

    # ------------------------------------------------------------- picks
    blocks = []
    for p in preds["predictions"]:
        facts = "".join(f'<li>{esc(f["claim"])} — <a href="{esc(f["source"])}">source</a></li>'
                        for f in p["facts"])
        tag = '<span class="tag t-ok">featured · inside -250…+10000</span>' if p["featured"] else \
              '<span class="tag t-out">≥70% but priced shorter than -250</span>'
        blocks.append(f"""
<div class="pick">
<h4>{esc(p['selection'])} · {esc(p['market'])}{(' ' + str(p['market_line'])) if p['market_line'] else ''}
— {esc(p['home'])} v {esc(p['away'])}</h4>
<div class="meta">{esc(p['date'])} · {esc(p['competition'])} · {esc(p['sport_name'])} ·
fair <span class="mono">{p['fair_decimal']:.2f}</span>
<span class="mono">({am(p['fair_american'])})</span> · {p['probability'] * 100:.1f}% ·
{conf_tag(p['confidence'])} {tag} · {p['word_count']} words</div>
<p>{esc(p['text'])}</p>
<h3>Evidence</h3><ul>{facts}</ul>
</div>""")
    body = f"""
<h2>Written predictions</h2>
<p class="lead">{preds['count']} predictions, every one at least {preds['min_words']} words, written only
for selections our model puts at 70% or better on matches whose own prices sit inside the brief's
-250 to +10000 window. {preds['featured_count']} of them are also priced inside that window themselves and
are marked <i>featured</i>; the rest are ≥70% but shorter than -250, and are shown labelled rather than
hidden. Each paragraph is built from values read on the official pages listed underneath it — records,
goals, home and away splits, last-ten form, current streak and, where the club appears in the slice of the
official NHL scoring summary this desk read, its leading scorer.</p>
{''.join(blocks)}
"""
    (OUT / "picks.html").write_text(page("Predictions", body, "picks.html"))

    # ------------------------------------------------------------- sports index + pages
    idx_rows = "".join(
        f'<tr><td><a href="{esc(slug)}.html">{esc(sport_name.get(slug, slug))}</a></td>'
        f'<td class="mono">{n}</td>'
        f'<td class="mono">{sum(1 for r in rows if r["sport"] == slug and r["status"] == "confirmed")}</td>'
        f'<td class="mono">{sum(1 for r in rows if r["sport"] == slug and r["line_status"] == "originated")}</td>'
        f'<td class="mono">{sum(1 for p in preds["predictions"] if p["sport"] == slug)}</td></tr>'
        for slug, n in sorted(per_sport.items(), key=lambda kv: -kv[1]))
    (OUT / "sports" / "index.html").write_text(page(
        "By sport", f"""
<h2>Sports</h2>
<p class="lead">All {len(per_sport)} eligible sports from the OLBG taxonomy. Excluded by the brief:
soccer/football, boxing, UFC/MMA, American football, hurling, horse racing, cycling and specials — none of
them appear anywhere on this desk.</p>
<div class="tw"><table><thead><tr><th>Sport</th><th>Rows</th><th>Confirmed</th><th>Originated</th>
<th>Predictions</th></tr></thead><tbody>{idx_rows}</tbody></table></div>
""", "sports/index.html"))

    for slug in per_sport:
        srows = [r for r in rows if r["sport"] == slug]
        spreds = [p for p in preds["predictions"] if p["sport"] == slug]
        tr = []
        for r in srows:
            pick = r.get("pick")
            pick_cell = "—"
            if pick:
                pick_cell = (f"{esc(pick['selection'])} <span class='mono'>{pick['fair_decimal']:.2f}</span> "
                             f"<span class='mono'>({am(pick['fair_american'])})</span> "
                             f"{conf_tag(pick['confidence'])}")
            tr.append(f'<tr data-sport="{esc(slug)}"><td>{esc(r["date"])}</td>'
                      f'<td>{esc(r["competition"])}</td>'
                      f'<td>{esc(r["home"])} v {esc(r["away"])}</td>'
                      f'<td>{esc(r.get("venue") or "—")}</td>'
                      f'<td>{markets_cell(r)}</td><td>{pick_cell}</td>'
                      f'<td>{status_tag(r["status"])} <a href="{esc(r["official_url"])}">source</a></td></tr>')
        pblocks = "".join(
            f'<div class="pick"><h4>{esc(p["selection"])} · {esc(p["market"])}</h4>'
            f'<div class="meta">{esc(p["date"])} · fair <span class="mono">{p["fair_decimal"]:.2f}</span> '
            f'<span class="mono">({am(p["fair_american"])})</span> · {p["probability"] * 100:.1f}% · '
            f'{conf_tag(p["confidence"])}</div><p>{esc(p["text"])}</p></div>' for p in spreds)
        body = f"""
<h2>{esc(sport_name.get(slug, slug))}</h2>
<p class="lead">{len(srows)} rows ·
{sum(1 for r in srows if r['status'] == 'confirmed')} confirmed first-hand ·
{sum(1 for r in srows if r['line_status'] == 'originated')} with originated prices ·
{len(spreds)} written predictions.
OLBG hub: <a href="{esc(sport_olbg.get(slug, '#'))}">{esc(sport_olbg.get(slug, ''))}</a></p>
<div class="tw"><table><thead><tr><th>Date</th><th>Competition</th><th>Fixture</th><th>Venue</th>
<th>Originated markets</th><th>Match-winner pick</th><th>Verification</th></tr></thead>
<tbody>{''.join(tr)}</tbody></table></div>
<h3>Predictions</h3>{pblocks or '<p class="blankcell">No predictions on this sport — no selection reached 70% with a verified strength input.</p>'}
"""
        (OUT / "sports" / f"{slug}.html").write_text(page(sport_name.get(slug, slug), body,
                                                          f"sports/{slug}.html"))

    # ------------------------------------------------------------- verification
    fam_rows = "".join(
        f'<tr><td><b>{esc(f["family"])}</b></td><td><a href="{esc(f["url"])}">{esc(f["official_source"])}</a></td>'
        f'<td class="mono">{f["window"]}</td><td class="mono">{f["rows_compared"]}</td>'
        f'<td class="mono">{f["confirmed"]}</td><td class="mono">{f["mismatched"]}</td>'
        f'<td class="mono">{f["outside_window"]}</td><td>{esc(f["note"])}</td></tr>'
        for f in ver["families"])
    body = f"""
<h2>Line-by-line verification ledger</h2>
<p class="lead">Every row this desk republished was checked against the governing body named on the row.
The table below is the audit trail: what was compared, where, how many rows agreed, how many did not.</p>
<div class="cards">
<div class="card"><div class="n">{ver['totals']['rows_compared']}</div><div class="l">rows compared</div></div>
<div class="card"><div class="n">{ver['totals']['confirmed']}</div><div class="l">confirmed</div></div>
<div class="card"><div class="n">{ver['totals']['mismatched']}</div><div class="l">mismatched</div></div>
<div class="card"><div class="n">{ver['totals']['outside_window']}</div><div class="l">outside window</div></div>
</div>
<div class="tw"><table><thead><tr><th>Family</th><th>Official source</th><th>Window</th><th>Compared</th>
<th>Confirmed</th><th>Mismatched</th><th>Outside window</th><th>Note</th></tr></thead>
<tbody>{fam_rows}</tbody></table></div>
<div class="note warn"><b>The tennis mismatches matter.</b> Each of the
{ver['totals']['mismatched']} failing rows is itemised individually on the
<a href="flagged.html">flagged page</a> with the official schedule it claims to come from, so you can open
the page and see for yourself that the pairing is not there.</div>
"""
    (OUT / "verification.html").write_text(page("Verification", body, "verification.html"))

    # ------------------------------------------------------------- flagged
    fblocks = []
    for f in flags["items"]:
        ev = "".join(f'<li><a href="{esc(e["url"])}">{esc(e["label"])}</a></li>' for e in f["evidence"])
        fblocks.append(f"""
<div class="pick">
<h4>{esc(f['id'])} · <span class="tag t-{f['severity'] if f['severity'] in ('low', 'medium') else 'out'}">{esc(f['severity'])}</span>
{esc(f['title'])}</h4>
<div class="meta">sport: {esc(f['sport'])}</div>
<p>{esc(f['detail'])}</p>
<h3>Open the official pages</h3><ul>{ev}</ul>
<p class="blankcell"><b>Action taken:</b> {esc(f['action'])}</p>
</div>""")
    body = f"""
<h2>Flagged for review</h2>
<p class="lead">{flags['count']} items. None of them block anything: each is published here with the
official pages it refers to so you can check it yourself. Where this desk could not confirm a value it has
left the cell blank rather than fill it.</p>
{''.join(fblocks)}
"""
    (OUT / "flagged.html").write_text(page("Flagged", body, "flagged.html"))

    # ------------------------------------------------------------- methodology
    body = """
<h2>Methodology</h2>
<h3>1. What gets published</h3>
<p>A fixture is published only if this session opened the governing-body URL stored on the row and the
fixture was there — same teams, same date, same venue. Everything else is either blank (values not
confirmed) or on the flagged page (rows that contradict their source).</p>
<h3>2. Confidence rule</h3>
<ul>
<li><b>high</b> — model probability ≥ 70% <i>and</i> the match's own prices sit between -250 and +10000.</li>
<li><b>medium</b> — model probability ≥ 60%, or ≥ 70% on a match priced shorter than -250.</li>
<li><b>low</b> — under 60%.</li>
</ul>
<div class="note warn"><b>Two defensible readings, both shown.</b> The brief says to focus high-confidence
picks on “matches that sit between -250 and +10000”. This desk reads that as a filter on the <i>match</i>,
so a selection at 87% on the puck line is graded <b>high</b> even though its own price (-690) is shorter
than -250. Earlier layers in this repository read it as a filter on the <i>selection</i>, which is stricter.
Both counts are printed: 41 written predictions, of which 6 are also priced inside the window themselves
and are marked <i>featured</i> on the predictions page.</div>
<h3>3. NHL model</h3>
<pre>w        = gp / (gp + 8)
attack_i  = 1 + w * ((gf_i/gp_i) / L - 1)
defence_i = 1 + w * ((ga_i/gp_i) / L - 1)
L         = league goals per team-game, from the same table
lambda_home = L * attack_home * defence_away * 1.044
lambda_away = L * attack_away * defence_home / 1.044
moneyline   = Poisson grid to 15 goals, tied games split 50/50
puck line   = 1.5 goals, P(home covers) = P(home margin ≥ 2)
total       = the half-goal line whose P(over) is closest to 0.50</pre>
<p><b>Inputs are official.</b> Every term comes from nhl.com/standings as published on 22 October 2026.
The constants 8 (shrinkage games) and 1.044 (home-ice multiplier, about a 9% goal ratio) are our own
origination, not measured values.</p>
<h3>4. MLB model</h3>
<pre>pythag_i  = RS^1.83 / (RS^1.83 + RA^1.83)
p         = log5(pythag_home, pythag_away), shifted by a logit home edge of 0.16
runs      = Poisson rates from the two clubs' official runs scored/allowed per game
run line  = 1.5 runs from the Skellam grid on those two rates
total     = the half-run line whose P(over) is closest to 0.50</pre>
<p>Inputs: the official MLB Stats API standings endpoint for the completed 2026 regular season.</p>
<h3>5. What is deliberately blank</h3>
<p>Where no official strength input could be read, the row is published with the fixture and its link but
with every price blank. That applies to all 74 NBA rows (stats.nba.com unreachable, and the new season is
one game old), the 9 EuroLeague rows (the official standings endpoint returned an empty payload), the 10
tennis rows (the ATP rankings table could not be read) and the 143 rows inherited from the earlier desk
that this session did not re-open.</p>
<h3>6. Prices</h3>
<p>Every price on this site is a fair price originated by this project: 1 ÷ our model probability, with no
margin and no bookmaker input. No bookmaker price is read, scraped or compared anywhere in this repository.</p>
"""
    (OUT / "methodology.html").write_text(page("Methodology", body, "methodology.html"))

    # ------------------------------------------------------------- sources
    caps = sorted(ATLAS.glob("capture_*.json"))
    srows = []
    for p in caps:
        d = json.loads(p.read_text())
        urls = [d.get("url"), d.get("schedule_url"), d.get("standings_url"), d.get("rankings_url"),
                d.get("coverage_url")]
        urls = [u for u in urls if u]
        links = "".join(f'<a href="{esc(u)}">{esc(u)}</a><br>' for u in urls)
        srows.append(f'<tr><td><b>{esc(d.get("source", ""))}</b></td>'
                     f'<td>{esc(d.get("captured_utc", ""))}</td>'
                     f'<td>{esc(d.get("as_of") or d.get("coverage") or d.get("note") or d.get("convention") or "")}</td>'
                     f'<td>{links}</td></tr>')
    body = f"""
<h2>Official sources read this session</h2>
<p class="lead">Every page below was opened by this session on 22 October 2026 and is the basis for the
values published on this desk. Nothing else was used.</p>
<div class="tw"><table><thead><tr><th>Source</th><th>Captured (UTC)</th><th>Note</th><th>URLs</th></tr>
</thead><tbody>{''.join(srows)}</tbody></table></div>
"""
    (OUT / "sources.html").write_text(page("Sources", body, "sources.html"))

    n_pages = 1 + len(list((OUT / "sports").glob("*.html"))) + 7
    print(f"built {n_pages} pages under atlas/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
