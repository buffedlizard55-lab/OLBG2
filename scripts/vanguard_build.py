"""Vanguard desk — static site builder (GitHub Pages, no JS dependencies)."""
from __future__ import annotations

import json
from collections import defaultdict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vanguard"
OUT = ROOT / "vanguard"
(OUT / "sports").mkdir(parents=True, exist_ok=True)

M = json.loads((DATA / "matches.json").read_text())
L = json.loads((DATA / "lines.json").read_text())
PR = json.loads((DATA / "predictions.json").read_text())
FL = json.loads((DATA / "flagged.json").read_text())
INP = json.loads((DATA / "inputs.json").read_text())

SPORTS = sorted({m["sport"] for m in M["matches"]})
NAME = {"ice-hockey": "Ice Hockey", "basketball": "Basketball", "rugby-union": "Rugby Union",
        "baseball": "Baseball", "handball": "Handball", "tennis": "Tennis", "snooker": "Snooker",
        "rugby-league": "Rugby League", "aussie-rules": "Aussie Rules", "darts": "Darts",
        "esports": "eSports", "gaelic-football": "Gaelic Football", "volleyball": "Volleyball",
        "cricket": "Cricket", "motor-racing": "Motor Racing", "golf": "Golf", "greyhounds": "Greyhounds"}

CSS = """body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;color:#14202b;background:#f6f8fa}
header{background:#0f2a43;color:#fff;padding:14px 22px}header a{color:#cfe3f5;text-decoration:none;margin-right:14px;font-size:14px}
header .brand{font-weight:700;color:#fff;font-size:17px;margin-right:22px}
main{max-width:1180px;margin:0 auto;padding:22px}
h1{font-size:26px;margin:8px 0 6px}h2{font-size:19px;margin:26px 0 8px}
p.lede{color:#42556a;max-width:820px;line-height:1.5}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13px;box-shadow:0 1px 2px rgba(0,0,0,.08);margin:8px 0 18px}
th,td{padding:7px 9px;border-bottom:1px solid #e6ecf2;text-align:left;vertical-align:top}
th{background:#eef3f8;font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:#42556a}
tr:hover td{background:#f9fbfd}
.badge{display:inline-block;padding:2px 7px;border-radius:10px;font-size:11px;font-weight:700}
.high{background:#d9f2e3;color:#166534}.med{background:#fef3c7;color:#92400e}.low{background:#e8eef5;color:#42556a}.blank{background:#fde2e2;color:#991b1b}
.kpis{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0}
.kpi{background:#fff;border-left:4px solid #0f2a43;padding:10px 16px;box-shadow:0 1px 2px rgba(0,0,0,.08);min-width:150px}
.kpi b{display:block;font-size:22px}.kpi span{font-size:12px;color:#42556a}
.notice{background:#fff8e6;border-left:4px solid #b45309;padding:10px 14px;font-size:13px;margin:12px 0}
.card{background:#fff;padding:12px 16px;margin:6px 0;border-left:4px solid #0f2a43}
small,.muted{color:#5b7086}
a{color:#0b5cab}
"""


def page(path: Path, title: str, body: str, depth: int = 0):
    pre = "../" * depth
    nav = "".join(
        f'<a href="{pre}{href}">{label}</a>'
        for href, label in [("index.html", "Dashboard"), ("matches.html", "All matches"),
                            ("picks.html", "Picks"), ("predictions.html", "Predictions"),
                            ("top5.html", "Top 5 per sport"), ("sports/index.html", "By sport"),
                            ("rows.html", "Row-by-row audit"), ("flagged.html", "Flagged for Review"),
                            ("sources.html", "Sources"), ("methodology.html", "Methodology")])
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · Vanguard OLBG desk</title>
<style>{CSS}</style></head><body>
<header><span class="brand">Vanguard · OLBG research desk</span>{nav}</header>
<main>{body}
<p class="muted" style="margin-top:26px"><small>Research, not betting advice. 18+. Prices are model-derived fair odds, not bookmaker quotes. Captured 2026-10-22 22:00Z by session arena/ca03be92-olbg2. Every fixture row links the official page it was read from.</small></p>
</main></body></html>"""
    path.write_text(html)


def badge(c):
    cls = {"high": "high", "medium": "med", "low": "low"}.get(c, "blank")
    return f'<span class="badge {cls}">{escape(c or "blank")}</span>'


def price_cell(pr):
    return f'{pr["p"]*100:.2f}% · {pr["decimal"]:.2f} · {pr["american"]:+d}'


counts = M["counts"]
# ---------------------------------------------------------------- landing
cards = "".join(
    f'<div class="card"><a href="sports/{s}.html"><b>{NAME[s]}</b></a> — '
    f'{sum(1 for m in M["matches"] if m["sport"]==s)} fixtures, '
    f'{sum(1 for p in PR["predictions"] if p["sport"]==s)} predictions</div>' for s in SPORTS)
body = f"""<h1>Vanguard — 17-sport fixture, line and prediction desk</h1>
<p class="lede">A first-hand capture of the OLBG sport universe at 22:00Z on 22 October 2026: every fixture below was read from an official
governing-body page during this session, every price is originated by our own model from those published figures, and every selection is
labelled with a confidence. Soccer, boxing, UFC/MMA, American football, hurling, horse racing, cycling and specials are excluded, as the brief requires.</p>
<div class="notice"><strong>Read this first.</strong> {counts['fixtures']} fixtures across {counts['sports']} sports; {counts['band_picks']} selections fall inside the
−250…+10000 band at ≥70% probability, of which {counts['predictions']} carry a written prediction. Sports with fewer than five written predictions are listed, with the reason,
on <a href="flagged.html">Flagged for Review</a>. No value is inferred: where an official page published no numeric input the row is blank and flagged.</div>
<div class="kpis">
<div class="kpi"><b>{counts['fixtures']}</b><span>verified fixtures</span></div>
<div class="kpi"><b>{counts['sports']}</b><span>sports covered</span></div>
<div class="kpi"><b>{counts['markets']}</b><span>originated prices</span></div>
<div class="kpi"><b>{counts['band_picks']}</b><span>in-band picks</span></div>
<div class="kpi"><b>{counts['predictions']}</b><span>written predictions</span></div>
<div class="kpi"><b>{FL['count']}</b><span>flags for review</span></div>
</div>
<h2>Sports</h2>{cards}
<h2>How to read this desk</h2>
<table><thead><tr><th>Page</th><th>What it shows</th></tr></thead><tbody>
<tr><td><a href="matches.html">All matches</a></td><td>Every fixture, its official source link, derived model inputs and confidence.</td></tr>
<tr><td><a href="lines.html">Originated lines</a></td><td>All {counts['markets']} prices: match winner, handicap and match total, with probability, decimal and American odds.</td></tr>
<tr><td><a href="picks.html">Picks</a></td><td>Every selection inside the strict high-confidence band, ranked by probability.</td></tr>
<tr><td><a href="predictions.html">Predictions</a></td><td>The written, source-based previews for high-confidence selections.</td></tr>
<tr><td><a href="top5.html">Top 5 per sport</a></td><td>The five highest-probability selections for each sport, whatever their confidence label.</td></tr>
<tr><td><a href="rows.html">Row-by-row audit</a></td><td>One line per fixture: source URL, input basis, markets, pick count and flags.</td></tr>
<tr><td><a href="flagged.html">Flagged for Review</a></td><td>Blank rows, partial markets, shortfalls against the five-per-sport target and data irregularities.</td></tr>
<tr><td><a href="sources.html">Sources</a></td><td>Every official endpoint read, with what it returned.</td></tr>
<tr><td><a href="methodology.html">Methodology</a></td><td>Model constants, the confidence gate and its arithmetic.</td></tr>
</tbody></table>"""
page(OUT / "index.html", "Dashboard", body)

# ---------------------------------------------------------------- matches
rows = "".join(
    f'<tr><td><a href="sports/{m["sport"]}.html">{NAME[m["sport"]]}</a></td><td>{escape(m["competition"])}</td>'
    f'<td>{escape(m["start_utc"])}</td><td>{escape(m["home"])} v {escape(m["away"])}</td>'
    f'<td>{len([x for x in m["prices"]])}</td><td>{len(m["in_band"])}</td><td>{badge(m["confidence"])}</td>'
    f'<td><a href="{escape(m["source_url"])}" rel="noopener">official source</a></td></tr>'
    for m in sorted(M["matches"], key=lambda x: (x["start_utc"], x["sport"])))
page(OUT / "matches.html", "All matches", f"""<h1>All {counts['fixtures']} verified fixtures</h1>
<p class="lede">Ordered by start time (UTC). The source column opens the official page the fixture and its inputs were read from; the
input basis for each model is repeated on the sport page and on the row-by-row audit.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Competition</th><th>Start (UTC)</th><th>Fixture</th><th>Prices</th><th>In band</th><th>Confidence</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>""")

# ---------------------------------------------------------------- lines
lrows = "".join(
    f'<tr><td>{NAME[x["sport"]]}</td><td>{escape(x["fixture"])}</td><td>{escape(x["market"])}</td>'
    f'<td>{escape(x["selection"])}</td><td>{x["p"]*100:.2f}%</td><td>{x["decimal"]:.2f}</td>'
    f'<td>{x["american"]:+d}</td><td>{"yes" if x.get("in_band") else "—"}</td></tr>'
    for x in sorted(L["rows"], key=lambda y: (y["sport"], y["fixture"], y["market"], -y["p"])))
page(OUT / "lines.html", "Originated lines", f"""<h1>{L['count']} originated prices</h1>
<p class="lede">Fair odds: decimal = 1 / probability, with the probability rounded to four decimals first. American odds are derived from
that rounded decimal, so any number on this page can be reproduced from its neighbour. "In band" marks a price inside −250…+10000 at ≥70%.</p>
<table><thead><tr><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th><th>Probability</th><th>Decimal</th><th>American</th><th>In band</th></tr></thead><tbody>{lrows}</tbody></table>""")

# ---------------------------------------------------------------- picks
band = [x for x in L["rows"] if x.get("in_band")]
prows = "".join(
    f'<tr><td>{NAME[x["sport"]]}</td><td>{escape(x["fixture"])}</td><td>{escape(x["market"])}</td>'
    f'<td>{escape(x["selection"])}</td><td>{x["p"]*100:.2f}%</td><td>{x["decimal"]:.2f}</td><td>{x["american"]:+d}</td></tr>'
    for x in sorted(band, key=lambda y: (-y["p"], y["fixture"])))
page(OUT / "picks.html", "Picks", f"""<h1>{len(band)} in-band selections</h1>
<p class="lede">High confidence requires probability of at least 0.7000 <em>and</em> fair American odds from −250 to +10000
(decimal 1.40 to 101.00). That is a 1.43-point-wide window, so most selections here are alternate handicaps or totals rather than
money lines — a money line almost never lands inside it.</p>
<table><thead><tr><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th><th>Probability</th><th>Decimal</th><th>American</th></tr></thead><tbody>{prows}</tbody></table>""")

# ---------------------------------------------------------------- predictions
blocks = "".join(
    f'<div class="card"><h3 style="margin:2px 0 4px">{escape(p["selection"])} — {escape(p["market"])}</h3>'
    f'<div class="muted"><small>{NAME[p["sport"]]} · {escape(p["competition"])} · {escape(p["start_utc"])} · '
    f'{p["probability"]*100:.2f}% · {p["decimal"]:.2f} ({p["american"]:+d})</small></div>'
    f'<p>{escape(p["text"])}</p>'
    f'<div class="muted"><small>{p["words"]} words · <a href="{escape(p["source_url"])}" rel="noopener">official source</a></small></div></div>'
    for p in PR["predictions"])
page(OUT / "predictions.html", "Predictions", f"""<h1>{PR['count']} written predictions</h1>
<p class="lede">Each preview names the selection, the competition and the price, and carries the verified form and recent-history facts
that the model used. Every one is at least 30 words; the shortest here is {min((p['words'] for p in PR['predictions']), default=0)} words.</p>
{blocks}""")

# ---------------------------------------------------------------- top 5
GRP = defaultdict(list)
for x in L["rows"]:
    if x["market"] == "match winner":
        GRP[x["sport"]].append(x)
trows = ""
for s in SPORTS:
    top = sorted(GRP.get(s, []), key=lambda y: -y["p"])[:5]
    if not top:
        trows += f'<tr><td>{NAME[s]}</td><td colspan="5" class="muted">No money-line price was originated for this sport — see Flagged for Review.</td></tr>'
        continue
    for i, x in enumerate(top, 1):
        trows += (f'<tr><td>{NAME[s]}</td><td>{i}</td><td>{escape(x["selection"])}</td>'
                  f'<td>{x["p"]*100:.2f}%</td><td>{x["decimal"]:.2f} ({x["american"]:+d})</td>'
                  f'<td>{escape(x["fixture"])}</td></tr>')
page(OUT / "top5.html", "Top 5 per sport", f"""<h1>Top five selections per sport</h1>
<p class="lede">Ranked by model probability among <em>match-winner</em> prices, one row per rank. This is the daily five-per-sport shortlist the
brief asks for; confidence labels are shown on the picks page, and a rank-1 selection is not automatically high confidence — most sit well
below the 70% band. Sports with fewer than five money-line prices are shown in full.</p>
<table><thead><tr><th>Sport</th><th>#</th><th>Selection</th><th>Probability</th><th>Price</th><th>Fixture</th></tr></thead><tbody>{trows}</tbody></table>""")

# ---------------------------------------------------------------- row audit
arows = ""
for m in sorted(M["matches"], key=lambda x: (x["sport"], x["start_utc"])):
    fl = [f["text"] for f in FL["flags"] if f["fixture"] == m["id"]]
    arows += (f'<tr><td>{escape(m["id"])}</td><td>{NAME[m["sport"]]}</td><td>{escape(m["home"])} v {escape(m["away"])}</td>'
              f'<td>{escape(m["basis"])}</td><td>{len(m["prices"])}</td><td>{len(m["in_band"])}</td>'
              f'<td>{"<br>".join(escape(t) for t in fl) or "—"}</td>'
              f'<td><a href="{escape(m["source_url"])}" rel="noopener">source</a></td></tr>')
page(OUT / "rows.html", "Row-by-row audit", f"""<h1>Row-by-row audit</h1>
<p class="lede">One row per fixture. The basis column states exactly which published figures were used and the formula applied, so a reviewer
can recompute the price. The flags column repeats anything published on Flagged for Review for this fixture.</p>
<table><thead><tr><th>ID</th><th>Sport</th><th>Fixture</th><th>Input basis</th><th>Prices</th><th>In band</th><th>Flags</th><th>Source</th></tr></thead><tbody>{arows}</tbody></table>""")

# ---------------------------------------------------------------- flagged
ids = {m["id"]: m["source_url"] for m in M["matches"]}
sports_set = {m["sport"] for m in M["matches"]}


def flag_source(f):
    if f["fixture"] in ids:
        return f'<a href="{escape(ids[f["fixture"]])}" rel="noopener">official source</a>'
    if f["fixture"] in sports_set:
        return f'<a href="sports/{f["fixture"]}.html">sport page</a>'
    return '<span class="muted">this page</span>'


frows = "".join(
    f'<tr><td>{escape(f["fixture"])}</td><td>{escape(f["kind"])}</td><td>{escape(f["text"])}</td>'
    f'<td>{flag_source(f)}</td></tr>'
    for f in FL["flags"])
srows = "".join(f'<tr><td>{escape(x["sport"])}</td><td>{x["predictions"]}</td><td>{escape(x["reason"])}</td></tr>'
                for x in PR["shortfall"])
page(OUT / "flagged.html", "Flagged for Review", f"""<h1>Flagged for Review</h1>
<p class="lede">Nothing on this page blocks publication. It records, with a click-through to the official page, every place where the desk
publishes less than the brief asks for or where an official source could not settle a value.</p>
<div class="notice"><strong>Coverage shortfall.</strong> The brief asks for five written predictions per covered sport per day. This desk
publishes {PR['count']} in total, because the strict gate (≥70% and −250…+10000) is narrow and only the sports with a score distribution
produce alternate lines that land inside it. The table below lists every sport that fell short, with the count actually published.</div>
<table><thead><tr><th>Sport</th><th>Predictions</th><th>Reason</th></tr></thead><tbody>{srows}</tbody></table>
<h2>Fixture-level flags ({FL['count']})</h2>
<table><thead><tr><th>Fixture</th><th>Kind</th><th>Finding</th><th>Source</th></tr></thead><tbody>{frows}</tbody></table>
<h2>Sport-level disclosures</h2>
<ul>
<li><strong>Gaelic football</strong> publishes three fixtures with no price at all. Munster GAA and the county boards publish fixtures, venues and throw-in times but no rating or points table for club sides, so any line would be invented.</li>
<li><strong>NBA</strong> prices use preseason net ratings from NBA.com's official Week 1 power rankings, not regular-season form; the four rows are capped and flagged.</li>
<li><strong>Rugby league</strong> uses round-one score differentials as a strength input because no rating table exists after one round.</li>
<li><strong>Golf, Formula 1 and greyhounds</strong> publish outright markets only, priced from an official points or prize-money table; the field beyond the named contenders is not modelled.</li>
<li><strong>Darts</strong> uses the official European Tour seed bracket; unseeded players are treated as seed 40, which is an assumption and is stated on every affected row.</li>
</ul>""")

# ---------------------------------------------------------------- sources
seen = {}
for m in M["matches"]:
    seen.setdefault(m["source_url"], set()).add(m["sport"])
srcrows = "".join(f'<tr><td><a href="{escape(u)}" rel="noopener">{escape(u)}</a></td>'
                  f'<td>{", ".join(NAME[s] for s in sorted(v))}</td></tr>' for u, v in sorted(seen.items()))
page(OUT / "sources.html", "Sources", f"""<h1>Official sources</h1>
<p class="lede">Every endpoint below was read during the 2026-10-22 evening session. Values were transcribed from what the page returned;
where a page returned nothing usable, the fixture is blank and flagged rather than filled in.</p>
<table><thead><tr><th>Official URL</th><th>Used for</th></tr></thead><tbody>{srcrows}</tbody></table>""")

# ---------------------------------------------------------------- methodology
page(OUT / "methodology.html", "Methodology", f"""<h1>Methodology</h1>
<p class="lede">Six model families, all documented, all computed from official published figures. No bookmaker price is read at any point.</p>
<table><thead><tr><th>Sport</th><th>Input</th><th>Distribution</th></tr></thead><tbody>
<tr><td>Ice hockey</td><td>NHL goals for/against per game, shrunk gp/(gp+8), home +0.10</td><td>Poisson score grid to 15; regulation ties split 50/50 for overtime</td></tr>
<tr><td>Baseball</td><td>MLB runs for/against per game, shrunk gp/(gp+20), home +0.12</td><td>Poisson grid to 25; ties split for extra innings</td></tr>
<tr><td>Handball</td><td>EHF goals for/against, shrunk gp/(gp+3), home +0.40</td><td>Poisson grid to 80; draws stand</td></tr>
<tr><td>Basketball</td><td>EuroLeague points for/against, shrunk gp/(gp+6), home +3.0; NBA preseason net rating +3.0</td><td>Normal margin, sd 11.0; total sd 15.0</td></tr>
<tr><td>Rugby union</td><td>URC points for/against, shrunk pl/(pl+6), home +3.0</td><td>Normal margin, sd 13.0, draw band ±1; total sd 16.0</td></tr>
<tr><td>Tennis, snooker, darts, eSports, cricket, volleyball, rugby league, AFLW</td><td>Official ranking points, seed, power score, team rating, ladder points/percentage or round-one margin — each stated on the row</td><td>Logistic on the stated strength difference; scale per sport in <code>data/vanguard/inputs.json</code></td></tr>
<tr><td>Golf, motor racing, greyhounds</td><td>Official money or points share among the named contenders</td><td>Direct share; capped at low confidence</td></tr>
</tbody></table>
<h2>The band</h2>
<p>High confidence requires <code>0.7000 ≤ p ≤ 5/7 = 0.714285…</code> and fair American odds between −250 and +10000. Fair −250 is
p = 0.714286, so the window is 1.43 percentage points wide. The gate is searched across every originated market and both sides, and the
alternate-line grids are deliberate: a handicap or total can be chosen so a genuine 70.7% opinion lands inside the window, which a money
line almost never does.</p>
<h2>Reproducibility</h2>
<p>Prices are <code>decimal = 1 / p</code> with <code>p</code> rounded to four decimals first, then the American price derived from the rounded
decimal. Round-trip a row's probability through the formula in <code>scripts/vanguard_verify.py</code> and you get the printed numbers exactly.</p>""")

# ---------------------------------------------------------------- sport pages
by_sport = defaultdict(list)
for m in M["matches"]:
    by_sport[m["sport"]].append(m)
for s in SPORTS:
    ms = sorted(by_sport[s], key=lambda x: x["start_utc"])
    trs = "".join(
        f'<tr><td>{escape(m["start_utc"])}</td><td>{escape(m["home"])} v {escape(m["away"])}</td>'
        f'<td>{len(m["prices"])}</td><td>{len(m["in_band"])}</td><td>{badge(m["confidence"])}</td>'
        f'<td><a href="../rows.html">basis</a> · <a href="{escape(m["source_url"])}" rel="noopener">source</a></td></tr>' for m in ms)
    preds = [p for p in PR["predictions"] if p["sport"] == s]
    pblocks = "".join(f'<div class="card"><b>{escape(p["selection"])}</b> — {escape(p["market"])} '
                      f'{p["probability"]*100:.2f}% · {p["decimal"]:.2f} ({p["american"]:+d})<p>{escape(p["text"])}</p></div>'
                      for p in preds) or '<p class="muted">No selection in this sport cleared the strict band, so no prediction is published. The reason is on <a href="../flagged.html">Flagged for Review</a>.</p>'
    page(OUT / "sports" / f"{s}.html", NAME[s], f"""<h1>{NAME[s]}</h1>
<p class="lede">{len(ms)} verified fixtures, {sum(1 for m in ms for _ in m["prices"])} originated prices,
{sum(len(m["in_band"]) for m in ms)} in-band picks and {len(preds)} written predictions.
<a href="index.html">Back to all sports</a>.</p>
<table><thead><tr><th>Start (UTC)</th><th>Fixture</th><th>Prices</th><th>In band</th><th>Confidence</th><th>Evidence</th></tr></thead><tbody>{trs}</tbody></table>
<h2>Predictions</h2>{pblocks}""", depth=1)

idx = "".join(f'<tr><td><a href="{s}.html">{NAME[s]}</a></td><td>{len(by_sport[s])}</td>'
              f'<td>{sum(len(m["in_band"]) for m in by_sport[s])}</td>'
              f'<td>{sum(1 for p in PR["predictions"] if p["sport"]==s)}</td></tr>' for s in SPORTS)
page(OUT / "sports" / "index.html", "By sport", f"""<h1>By sport</h1>
<p class="lede">All 17 eligible sports, with verified fixture counts. Excluded sports are not listed at all: soccer/football, boxing,
UFC/MMA, American football, hurling, horse racing, cycling and specials.</p>
<table><thead><tr><th>Sport</th><th>Fixtures</th><th>In-band picks</th><th>Predictions</th></tr></thead><tbody>{idx}</tbody></table>""", depth=1)

print("built", len(list(OUT.rglob('*.html'))), "pages")
