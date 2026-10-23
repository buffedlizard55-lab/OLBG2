#!/usr/bin/env python3
"""Static builder for /liveboard/. No network, no templates, deterministic output."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "liveboard"
OUT = ROOT / "liveboard"

SPORTS = [
    ("Golf", "golf"), ("Volleyball", "volleyball"), ("Rugby Union", "rugby-union"),
    ("Cricket", "cricket"), ("Snooker", "snooker"), ("Darts", "darts"),
    ("Baseball", "baseball"), ("Gaelic Sports", "gaelic-sports"), ("Greyhounds", "greyhounds"),
    ("Tennis", "tennis"), ("Motor Racing", "motor-racing"), ("Handball", "handball"),
    ("Ice Hockey", "ice-hockey"), ("Basketball", "basketball"), ("Rugby League", "rugby-league"),
]
SLUG = dict(SPORTS)
NAV = [
    ("index.html", "Dashboard"), ("picks.html", "Top picks"), ("matches.html", "All fixtures"),
    ("lines.html", "Originated lines"), ("predictions.html", "Predictions"),
    ("coverage.html", "Coverage"), ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"), ("methodology.html", "Method"),
]

CSS = """\
:root{--ink:#0f172a;--mut:#5b6779;--line:#dde3ea;--bg:#f6f8fa;--card:#fff;--accent:#0d6a5f;--accent2:#e8f4f2;
--high:#0a7a4f;--highbg:#dff3e8;--med:#8a5a00;--medbg:#fdf0d5;--low:#6b7280;--lowbg:#eceff3;--flag:#a3282b;--flagbg:#fdeaea}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
header.top{background:var(--ink);color:#fff;padding:14px 0 0}
header.top .brand{font-weight:700;letter-spacing:.02em;font-size:1.05rem}
header.top .brand span{color:#7fd7c9;font-weight:500}
header.top .stamp{margin:.15rem 0 .8rem;color:#a9b6c6;font-size:.82rem}
nav.main{display:flex;flex-wrap:wrap;gap:2px;padding-bottom:10px}
nav.main a{color:#c9d4e2;text-decoration:none;font-size:.86rem;padding:.36rem .6rem;border-radius:6px}
nav.main a:hover{background:#1d2937;color:#fff}
nav.main a.on{background:var(--accent);color:#fff;font-weight:600}
main{padding:28px 0 10px}
h1{font-size:1.9rem;line-height:1.2;margin:.2rem 0 .5rem;letter-spacing:-.01em}
h2{font-size:1.28rem;margin:2rem 0 .5rem}
h3{font-size:1.02rem;margin:1.2rem 0 .3rem}
p.lede{font-size:1.06rem;color:#33404f;max-width:70ch}
.muted{color:var(--mut)}.small{font-size:.84rem}
section{margin:0 0 1.6rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:1.2rem 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:1.7rem;line-height:1.1}
.kpi span{color:var(--mut);font-size:.8rem;text-transform:uppercase;letter-spacing:.05em}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card);margin:.6rem 0 1rem}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{text-align:left;padding:.5rem .7rem;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eef2f6;font-size:.76rem;text-transform:uppercase;letter-spacing:.04em;color:#46536a;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fbfcfd}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.badge{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:.12rem .45rem;border-radius:999px}
.b-high{color:var(--high);background:var(--highbg)}.b-medium{color:var(--med);background:var(--medbg)}.b-low{color:var(--low);background:var(--lowbg)}
.b-yes{color:var(--high);background:var(--highbg)}.b-no{color:var(--mut);background:var(--lowbg)}
.sev{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;padding:.1rem .4rem;border-radius:999px;margin-right:.4rem}
.s-high{color:#fff;background:var(--flag)}.s-medium{color:#7c3b00;background:#fde0c2}.s-low{color:var(--mut);background:var(--lowbg)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:.8rem 0}
.card h2,.card h3{margin-top:0}
.pred .copy{font-size:1rem;margin:.5rem 0 .8rem;max-width:80ch}
.facts{margin:.3rem 0 .6rem;padding-left:1.1rem;font-size:.88rem;color:#33404f}
.facts li{margin:.2rem 0}
.sports{display:flex;flex-wrap:wrap;gap:6px}
.sports a{font-size:.84rem;background:#eef2f6;padding:.2rem .5rem;border-radius:6px;text-decoration:none}
footer{margin-top:2.6rem;padding:20px 0 40px;border-top:1px solid var(--line);color:var(--mut);font-size:.86rem}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
@media(max-width:620px){h1{font-size:1.5rem}th,td{padding:.4rem .5rem}}
"""


OUTRIGHT_TAG = ' <span class="badge b-low">outright</span>'


def esc(x):
    return html.escape(str(x), quote=True)


def load(name):
    return json.loads((DATA / name).read_text())


OLBG = load("olbg.json")
LINES = load("lines.json")
PRED = load("predictions.json")
FLAGS = load("flagged.json")["flags"]
SRC = load("sources.json")
ROWS = LINES["rows"]
PREDS = PRED["predictions"]


def page(title, active, body, prefix=""):
    links = "".join(
        f'<a class="{"on" if href == active else ""}" href="{prefix}{href}">{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG live board</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="brand"><a href="{prefix}index.html" style="color:#fff;text-decoration:none">OLBG <span>live board</span></a>
      <p class="stamp">Captured 23 Oct 2026 · 15 sports · 133 fixtures · every row carries its source</p></div>
    <nav class="main">{links}</nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
  <p>Research aid, not betting advice. Prices here are originated by this project, not quotes from a bookmaker.
  OLBG supplies the fixture list and its published tip shares; governing bodies supply every other number.
  Where an official number was not obtained, the value is blank and the row appears on
  <a href="{prefix}flagged.html">Flagged for review</a>.</p>
  <p class="small">Part of the wider research desk:
  <a href="{prefix}../index.html">root dashboard</a> ·
  <a href="{prefix}../integration.html">cross-layer review</a> ·
  <a href="{prefix}../archive.html">earlier layers</a>.</p>
  <details><summary class="small">Sports</summary><div class="sports">
  {"".join(f'<a href="{prefix}sports/{slug}.html">{esc(name)}</a>' for name, slug in SPORTS)}
  </div></details>
</footer>
</body>
</html>
"""


def badge(conf):
    return f'<span class="badge b-{conf}">{conf}</span>'


def yesno(v):
    return '<span class="badge b-yes">in band</span>' if v else '<span class="badge b-no">outside</span>'


def price(r):
    return f'{r["price"]:+d}' if r["price"] > 0 else str(r["price"])


def table(headers, rows, cls=""):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(c for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def src(url, label="source"):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{label}</a>'


def per_sport(sport):
    return [r for r in ROWS if r["sport"] == sport]


def board_picks(sport, n=5):
    return sorted(per_sport(sport), key=lambda r: (-r["probability"], r["event"]))[:n]


# --------------------------------------------------------------------------- pages
def kpi_block():
    hb = [r for r in ROWS if r["confidence"] == "high" and r["in_band"]]
    tuned = [
        ("sports covered", "15", "of 15 in the brief"),
        ("fixtures captured", len(ROWS), "first page of each hub"),
        ("markets priced", len(ROWS), "every fixture carries a price"),
        ("high confidence", sum(1 for r in ROWS if r["confidence"] == "high"), "70% or better"),
        ("high and in band", len(hb), "−250 to +10000"),
        ("predictions", len(PREDS), "30 words minimum each"),
        ("review flags", len(FLAGS), "all published, none hidden"),
    ]
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><b>{esc(v)}</b><span>{esc(k)}</span><p class="small muted" style="margin:.2rem 0 0">{esc(s)}</p></div>'
        for k, v, s in tuned
    ) + "</div>"


def index_page():
    high = sorted([r for r in ROWS if r["confidence"] == "high"], key=lambda r: (-r["probability"], r["sport"]))
    rows = []
    for r in high[:10]:
        rows.append([
            f'<td>{esc(r["sport"])}</td>',
            f'<td>{esc(r["event"])}</td>',
            f'<td><strong>{esc(r["selection"])}</strong><br><span class="small muted">{esc(r["market"])}</span></td>',
            f'<td class="num">{price(r)}</td>',
            f'<td class="num">{r["probability"] * 100:.1f}%</td>',
            f'<td>{badge(r["confidence"])}</td>',
            f'<td>{yesno(r["in_band"])}</td>',
            f'<td>{src(r["source_url"], "OLBG")}</td>',
        ])
    body = f"""
<section>
  <h1>Fifteen sports, captured this afternoon</h1>
  <p class="lede">A first-hand read of OLBG's fifteen sport boards on 23 October 2026, priced independently and
  graded by confidence. OLBG supplies the fixtures and its published tip splits. Every other number comes from a
  governing body and is linked. Where a number could not be obtained it is blank and the row is on the
  <a href="flagged.html">Flagged for review</a> page.</p>
  {kpi_block()}
  <p class="small muted">Read this first: <a href="methodology.html">the method</a> explains what “high” means,
  why the −250 to +10000 window is narrow, and why no injury is named anywhere on this board.</p>
</section>

<section>
  <h2>The strongest ten on the board</h2>
  <p class="muted">Graded on our own probability, not on how much the crowd likes them. Two of these ten sit inside
  the brief's price window; the rest are shorter than −250, which is the arithmetic explained on the method page.</p>
  {table(["Sport", "Fixture", "Selection", "Our price", "Our chance", "Grade", "Band", "Source"], rows)}
</section>

<section>
  <h2>What is not here, and why</h2>
  <div class="grid2">
    <div class="card"><h3>Golf: nothing to publish</h3>
      <p class="small">OLBG's golf hub answered “No tips found.” for both paths tried. An empty hub is recorded as
      empty, not filled from another week. <a href="flagged.html">F-01</a></p></div>
    <div class="card"><h3>Rugby League: outrights only</h3>
      <p class="small">Both 2026 seasons are finished, so the hub carries three 2027 season markets and no fixture.
      They are priced and labelled as outrights. <a href="flagged.html">F-02</a></p></div>
    <div class="card"><h3>Eleven of fifteen sports have no official input</h3>
      <p class="small">Handball, darts, tennis, volleyball, cricket, NBA, hockey's European leagues and the rest are
      priced from the published tip split alone. Each row says so. <a href="coverage.html">Coverage</a></p></div>
    <div class="card"><h3>Fourteen predictions, not seventy-five</h3>
      <p class="small">A thirty-word write-up needs facts. Where no official current-form input existed, no
      prediction was written rather than invented. <a href="flagged.html">F-13</a></p></div>
  </div>
</section>

<section>
  <h2>Where to look next</h2>
  <div class="grid2">
    <div class="card"><h3><a href="picks.html">Top picks by sport</a></h3>
      <p class="small">Five selections per sport where five exist, ordered by our probability, with the grade and
      the price beside every one.</p></div>
    <div class="card"><h3><a href="lines.html">Originated lines</a></h3>
      <p class="small">All {len(ROWS)} priced markets with fair price, offered price, basis and source.</p></div>
    <div class="card"><h3><a href="matches.html">All fixtures</a></h3>
      <p class="small">The raw capture: 133 rows, OLBG's own time string, market and tip split, linked back to the
      page it came from.</p></div>
    <div class="card"><h3><a href="flagged.html">Flagged for review</a></h3>
      <p class="small">{len(FLAGS)} irregularities with a source link on each, including the two gates that cannot
      both be satisfied at once.</p></div>
  </div>
</section>
"""
    return page("The board, as it stands", "index.html", body)


def coverage_page():
    cov = LINES["coverage"]
    rows = []
    for name, slug in SPORTS:
        c = cov[name]
        npred = sum(1 for p in PREDS if p["sport"] == name)
        nflag = sum(1 for f in FLAGS if f["sport"] in (name, "All"))
        rows.append([
            f'<td><a href="sports/{slug}.html">{esc(name)}</a></td>',
            f'<td class="num">{c["events"]}</td>',
            f'<td class="num">{c["priced"]}</td>',
            f'<td class="num">{c["official_model_rows"]}</td>',
            f'<td class="num">{c["high"]}</td>',
            f'<td class="num">{c["high_in_band"]}</td>',
            f'<td class="num">{npred}</td>',
            f'<td class="num">{nflag}</td>',
            f'<td class="small muted">{esc(c["status"])}</td>',
        ])
    body = f"""
<section>
  <h1>Coverage</h1>
  <p class="lede">What OLBG was actually publishing for each of the fifteen sports, what could be priced from an
  official number, and what could not.</p>
  {table(["Sport", "Fixtures", "Priced", "Official input", "High", "High + in band", "Predictions", "Flags", "Hub status"], rows)}
  <p class="small muted">“Official input” counts rows whose probability came from a governing body rather than from
  OLBG's tip split. Four sports have at least one such row: Baseball, Basketball (EuroLeague), Snooker and Rugby Union (URC).</p>
</section>
<section>
  <h2>Reading the counts</h2>
  <p><strong>Fixtures</strong> are the first page of each OLBG hub, not a complete worldwide card. OLBG's own
  “Load More Tips” control was not followed, so these counts are slices.</p>
  <p><strong>High</strong> means our probability reached 70%. A tip-share row also needs at least six tips before it
  can be graded high, so a 2-of-2 split never becomes a certainty.</p>
  <p><strong>High and in band</strong> is the intersection the brief asks for. Because −250 is itself a 71.4%
  price, that intersection is about one and a half percentage points wide. See
  <a href="methodology.html">the method</a> and <a href="flagged.html">F-14</a>.</p>
</section>
"""
    return page("Coverage", "coverage.html", body)


def matches_page():
    rows = []
    for sp in OLBG["sports"]:
        for ev in sp["events"]:
            rows.append([
                f'<td>{esc(sp["sport"])}</td>',
                f'<td>{esc(ev["start_display"])}</td>',
                f'<td>{esc(ev["event"])}{OUTRIGHT_TAG if ev.get("outright") else ""}</td>',
                f'<td class="small">{esc(ev.get("competition") or "—")}</td>',
                f'<td class="small">{esc(ev["market"] or "—")}</td>',
                f'<td>{esc(ev["selection"])}</td>',
                f'<td class="num">{ev["tips"]}/{ev["total"]}</td>',
                f'<td class="num">{ev["comments"]}</td>',
                f'<td>{src("https://www.olbg.com" + ev["path"], "OLBG")}</td>',
            ])
    body = f"""
<section>
  <h1>Every fixture captured from OLBG</h1>
  <p class="lede">The raw inventory: {len(rows)} rows across fifteen sports, exactly as OLBG presented them.
  Time strings are OLBG's own and are not converted — see <a href="flagged.html">F-11</a>, because North American
  rows are US Eastern and European rows are UK local.</p>
  <p class="small muted">“Tips” is the split OLBG publishes for the one market it chooses to highlight on the hub.
  It is not a price, and 1/1 is one person's opinion.</p>
  {table(["Sport", "Start (as shown)", "Fixture", "Competition", "Market", "Tipped selection", "Tips", "Comments", "Source"], rows)}
</section>
"""
    return page("All fixtures", "matches.html", body)


def lines_page():
    rows = []
    for r in sorted(ROWS, key=lambda x: (SPORTS.index((x["sport"], SLUG[x["sport"]])), -x["probability"])):
        rows.append([
            f'<td>{esc(r["sport"])}</td>',
            f'<td>{esc(r["event"])}</td>',
            f'<td class="small">{esc(r["market"])}</td>',
            f'<td><strong>{esc(r["selection"])}</strong></td>',
            f'<td class="num">{r["probability"] * 100:.1f}%</td>',
            f'<td class="num">{r["fair_american"]:+d}</td>',
            f'<td class="num">{price(r)}</td>',
            f'<td>{badge(r["confidence"])}</td>',
            f'<td>{yesno(r["in_band"])}</td>',
            f'<td class="small">{esc(r["basis"])}<br><span class="muted">{esc(r["note"])}</span></td>',
            f'<td>{src(r["source_url"], "source")}</td>',
        ])
    fl = []
    for f in LINES["originated_lines"]:
        fl.append([
            f'<td>{esc(f["sport"])}</td>',
            f'<td>{esc(f["event"])}</td>',
            f'<td>{esc(f["market"])}</td>',
            f'<td class="num">{esc(f.get("line"))}</td>',
            f'<td>{esc(f.get("read", "—"))}</td>',
            f'<td class="small">{esc(f["note"])}</td>',
            f'<td>{src(f["source_url"], "source")}</td>',
        ])
    body = f"""
<section>
  <h1>Originated lines</h1>
  <p class="lede">One price per fixture, built here. Fair price is 1 ÷ probability; the offered price takes the
  sport's book margin on the profit. No bookmaker price appears anywhere on this board, because OLBG does not
  publish one to a logged-out visitor (<a href="flagged.html">F-10</a>).</p>
  {table(["Sport", "Fixture", "Market", "Selection", "Chance", "Fair", "Offered", "Grade", "Band", "Basis", "Source"], rows)}
</section>
<section>
  <h2>Handicaps and totals derived from an official number</h2>
  <p class="muted">These are the only prices on the board built from something other than a tip split. Where a
  governing body supplied runs or points, a second market could be originated rather than guessed.</p>
  {table(["Sport", "Fixture", "Market", "Line", "Model read", "How it was derived", "Source"], fl)}
</section>
<section>
  <h2>Where the unlined rows are</h2>
  <p class="small muted">{len(LINES["unlined"])} rows had neither a usable tip sample nor an official input and are
  published as blank rather than estimated.</p>
</section>
"""
    return page("Originated lines", "lines.html", body)


def picks_page():
    cards = []
    for name, slug in SPORTS:
        picks = board_picks(name)
        if not picks:
            cards.append(f"""<div class="card"><h3><a href="sports/{slug}.html">{esc(name)}</a></h3>
            <p class="small muted">No fixture to pick from. The hub returned
            {'no events at all' if OLBG['sports'][[s['sport'] for s in OLBG['sports']].index(name)]['status'] == 'empty' else 'outrights only'}.</p></div>""")
            continue
        rows = []
        for r in picks:
            rows.append([
                f'<td>{esc(r["event"])}<br><span class="small muted">{esc(r["start_display"])}</span></td>',
                f'<td><strong>{esc(r["selection"])}</strong><br><span class="small muted">{esc(r["market"])}</span></td>',
                f'<td class="num">{price(r)}</td>',
                f'<td class="num">{r["probability"] * 100:.1f}%</td>',
                f'<td>{badge(r["confidence"])}</td>',
                f'<td>{yesno(r["in_band"])}</td>',
            ])
        cards.append(f"""<div class="card"><h3><a href="sports/{slug}.html">{esc(name)}</a>
        <span class="small muted">— {len(per_sport(name))} priced</span></h3>
        {table(["Fixture", "Selection", "Price", "Chance", "Grade", "Band"], rows)}</div>""")
    body = f"""
<section>
  <h1>Top picks, sport by sport</h1>
  <p class="lede">Up to five selections per sport, chosen by our own probability rather than by popularity, so the
  same five appear whatever the crowd thinks. Only rows that reach 70% carry a high grade; a majority of these are
  shorter than the brief's −250 floor, which is why the band column matters.</p>
  <p class="small muted">Five per sport is not 75 picks: Golf has no fixture, Rugby League has outrights only, and
  Baseball has a single game. Where fewer than five exist, fewer are shown.</p>
</section>
{''.join(cards)}
"""
    return page("Top picks", "picks.html", body)


def predictions_page():
    cards = []
    for p in PREDS:
        facts = "".join(
            f'<li>{esc(f["claim"])} — {src(f["source_url"])}</li>' for f in p["facts"]
        )
        words = len(p["text"].split())
        cards.append(f"""<article class="card pred">
  <h2>{esc(p["selection"])} <span class="small muted">— {esc(p["sport"])} · {esc(p["event"])}</span></h2>
  <p class="small muted">{esc(p["market"])} · {words} words · selection stated plainly · every fact linked below</p>
  <p class="copy">{esc(p["text"])}</p>
  <h3 class="small">Facts behind it</h3>
  <ul class="facts">{facts}</ul>
  <p class="small muted">Injury and availability: no official list was obtained for this fixture, so none is asserted.</p>
</article>""")
    body = f"""
<section>
  <h1>Written predictions</h1>
  <p class="lede">{len(PREDS)} selections, each written around that fixture's own numbers, each at least thirty
  words, each stating the side plainly. Every claim underneath is a link to the page it came from.</p>
  <p class="small muted">The brief asked for five per sport. That target was not reached; the shortfall and the
  reason for each sport are on <a href="flagged.html">Flagged for review</a> (F-13) and on
  <a href="coverage.html">Coverage</a>.</p>
</section>
{''.join(cards)}
"""
    return page("Predictions", "predictions.html", body)


def flagged_page():
    cards = []
    for f in FLAGS:
        links = " · ".join(
            src(u, u.replace("https://", "")) if u.startswith("http") else f'<a href="{u.split("/")[-1]}">{esc(u)}</a>'
            for u in f["sources"]
        )
        cards.append(f"""<article class="card">
  <h3><span class="sev s-{esc(f['severity'])}">{esc(f['severity'])}</span>{esc(f['id'])} · {esc(f['title'])}</h3>
  <p class="small muted">{esc(f['sport'])}</p>
  <p>{esc(f['detail'])}</p>
  <p class="small"><strong>Action:</strong> {esc(f['action'])}</p>
  <p class="small">Sources: {links}</p>
</article>""")
    body = f"""
<section>
  <h1>Flagged for review</h1>
  <p class="lede">{len(FLAGS)} items. Every gap, disagreement and irregularity found while building this board is
  listed here with a source link, including the ones that limit the coverage most. Nothing on this page blocks
  publication and nothing here has been quietly dropped.</p>
</section>
{''.join(cards)}
"""
    return page("Flagged for review", "flagged.html", body)


def sources_page():
    read_rows = [[f'<td>{esc(s["kind"])}</td>', f'<td>{esc(s["label"])}</td>', f'<td>{src(s["url"])}</td>'] for s in SRC["read"]]
    block_rows = [[f'<td>{esc(s["label"])}</td>', f'<td>{esc(s["affects"])}</td>', f'<td>{src(s["url"])}</td>'] for s in SRC["blocked"]]
    body = f"""
<section>
  <h1>Sources</h1>
  <p class="lede">Everything read in this session, and everything that refused to be read. The second table matters
  as much as the first: a blocked page is why a sport has no official input.</p>
</section>
<section>
  <h2>Read and used ({len(SRC["read"])})</h2>
  {table(["Type", "What it gave", "URL"], read_rows)}
</section>
<section>
  <h2>Blocked ({len(SRC["blocked"])})</h2>
  <p class="muted">Recorded rather than worked around. No value was inferred from a page that would not load.</p>
  {table(["What was wanted", "Sport affected", "URL"], block_rows)}
</section>
<section>
  <h2>Rule applied throughout</h2>
  <p>A number appears on this board only if it was read on a page linked in the row it appears in. Where that was
  not possible the cell is blank and the row is on <a href="flagged.html">Flagged for review</a>.</p>
</section>
"""
    return page("Sources", "sources.html", body)


def methodology_page():
    m = LINES["method"]
    margins = "".join(f"<tr><td>{esc(k)}</td><td class='num'>{v * 100:.0f}%</td></tr>" for k, v in m["margins"].items())
    body = f"""
<section>
  <h1>Method</h1>
  <p class="lede">Two sources of probability, never blended: a governing-body number where one was read, and OLBG's
  published tip split where one was not. The basis is printed on every row.</p>
</section>

<section class="card">
  <h2>1. Two kinds of probability</h2>
  <p><strong>Official input</strong> — a probability computed from a governing body's own number. Four sports have
  one: Baseball (season records, log5 with a four-point home adjustment), Basketball's three EuroLeague games
  (points scored minus points conceded per game, a three-point home edge, a twelve-point spread), Snooker (world and
  one-year ranking money on a log scale at 0.45, so an eight-place gap is a real gap and not a certainty), and
  Rugby Union's three URC games (a single round of results, shrunk hard towards the mean because one round is a
  thin sample).</p>
  <p><strong>Tip share</strong> — the other eleven sports. OLBG publishes the split for the one market it
  highlights. It is smoothed as (tips + 1) ÷ (total + 2), so a 1-of-1 tip becomes 66.7% rather than 100%, and a
  tip-share row needs at least six tips before it can be graded high. That gate is why a 2-of-2 split shows as
  medium here and a 26-of-31 split shows as high.</p>
</section>

<section class="card">
  <h2>2. From probability to price</h2>
  <p>Fair decimal is 1 ÷ p. The offered price is 1 + (fair − 1) × (1 − margin), so the margin is taken on the profit
  and a favourite is never priced at a shorter decimal than its fair price. American odds follow from the offered
  decimal.</p>
  <div class="scroll"><table><thead><tr><th>Sport</th><th>Margin</th></tr></thead><tbody>{margins}</tbody></table></div>
</section>

<section class="card">
  <h2>3. Grading and the band</h2>
  <p><strong>High</strong> is p ≥ 0.70. <strong>Medium</strong> is 0.60 to 0.70. <strong>Low</strong> is below that.
  The band is −250 to +10000 measured on the fair price.</p>
  <p>{esc(m["band_note"])}</p>
  <p class="small muted">{esc(m["band_basis"])}</p>
</section>

<section class="card">
  <h2>4. What is deliberately absent</h2>
  <ul>
    <li><strong>No bookmaker price.</strong> OLBG's event pages render market labels and tip splits with the price
    fields empty for a logged-out visitor. Nothing was borrowed from elsewhere.</li>
    <li><strong>No injury claim.</strong> No official availability list was obtained, so none is asserted. Every
    prediction card says so.</li>
    <li><strong>No converted kick-off times.</strong> OLBG mixes US Eastern with UK local; the original string is
    published untouched.</li>
    <li><strong>No completed rows.</strong> Six rows truncated on the hub were dropped rather than finished by eye.</li>
    <li><strong>No carried-over numbers.</strong> Every figure on this board was read in this session; nothing comes
    from another desk's capture.</li>
  </ul>
</section>
"""
    return page("Method", "methodology.html", body)


def sport_page(name, slug):
    rows = sorted(per_sport(name), key=lambda r: (-r["probability"], r["event"]))
    body_rows = []
    for r in rows:
        body_rows.append([
            f'<td>{esc(r["event"])}<br><span class="small muted">{esc(r["start_display"])}</span></td>',
            f'<td class="small">{esc(r["market"])}</td>',
            f'<td><strong>{esc(r["selection"])}</strong></td>',
            f'<td class="num">{r["probability"] * 100:.1f}%</td>',
            f'<td class="num">{price(r)}</td>',
            f'<td>{badge(r["confidence"])}</td>',
            f'<td>{yesno(r["in_band"])}</td>',
            f'<td class="small">{esc(r["note"])}</td>',
            f'<td>{src(r["source_url"], "OLBG")}</td>',
        ])
    preds = [p for p in PREDS if p["sport"] == name]
    pred_html = ""
    for p in preds:
        facts = "".join(f'<li>{esc(f["claim"])} — {src(f["source_url"])}</li>' for f in p["facts"])
        pred_html += f"""<article class="card pred"><h3>{esc(p["selection"])} <span class="small muted">— {esc(p["event"])}</span></h3>
        <p class="copy">{esc(p["text"])}</p><ul class="facts">{facts}</ul></article>"""
    if not pred_html:
        pred_html = ('<p class="muted">No prediction was written for this sport. '
                     'The reason is listed on <a href="../flagged.html">Flagged for review</a>.</p>')
    flags = [f for f in FLAGS if f["sport"] in (name, "All")]
    flag_html = "".join(
        f'<li><span class="sev s-{esc(f["severity"])}">{esc(f["severity"])}</span>{esc(f["id"])} {esc(f["title"])}</li>'
        for f in flags
    ) or '<li class="muted">No sport-specific flag.</li>'
    hub = next(s for s in OLBG["sports"] if s["sport"] == name)
    body = f"""
<section>
  <h1>{esc(name)}</h1>
  <p class="lede">{len(rows)} priced markets captured from OLBG on 23 October 2026.
  Hub status: <strong>{esc(hub["status"])}</strong>{(" — " + esc(hub["status_detail"].rstrip("."))) if hub.get("status_detail") else ""}.</p>
  <p class="small">{src(hub["hub"], "OLBG hub for " + name)}</p>
</section>
<section>
  {table(["Fixture", "Market", "Selection", "Chance", "Price", "Grade", "Band", "Basis", "Source"], body_rows) if rows else '<p class="muted">No rows.</p>'}
</section>
<section>
  <h2>Predictions</h2>
  {pred_html}
</section>
<section>
  <h2>Flags touching this sport</h2>
  <ul class="facts">{flag_html}</ul>
</section>
"""
    return page(name, "", body, prefix="../")


def build():
    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS)
    (OUT / "index.html").write_text(index_page())
    (OUT / "coverage.html").write_text(coverage_page())
    (OUT / "matches.html").write_text(matches_page())
    (OUT / "lines.html").write_text(lines_page())
    (OUT / "picks.html").write_text(picks_page())
    (OUT / "predictions.html").write_text(predictions_page())
    (OUT / "flagged.html").write_text(flagged_page())
    (OUT / "sources.html").write_text(sources_page())
    (OUT / "methodology.html").write_text(methodology_page())
    for name, slug in SPORTS:
        (OUT / "sports" / f"{slug}.html").write_text(sport_page(name, slug))
    pages = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*.html"))
    print(f"built {len(pages)} pages + assets/style.css")


if __name__ == "__main__":
    build()
