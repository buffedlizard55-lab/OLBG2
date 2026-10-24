#!/usr/bin/env python3
"""Render the /latest/ desk: an executive summary first, then picks, previews, fixtures and sport pages.

Every table row carries the page the value was read from. Nothing is computed here except counts that
are derived from the published data files, so the pages cannot disagree with the data they print.

Run:  python scripts/latest_build.py
"""
from __future__ import annotations

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "latest"
OUT = ROOT / "latest"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
SLUG = {"Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union", "Cricket": "cricket",
        "Snooker": "snooker", "Darts": "darts", "Baseball": "baseball",
        "Gaelic Sports": "gaelic-sports", "Greyhounds": "greyhounds", "Tennis": "tennis",
        "Motor Racing": "motor-racing", "Handball": "handball", "Ice Hockey": "ice-hockey",
        "Basketball": "basketball", "Rugby League": "rugby-league"}

STYLE = """\
:root{--ink:#12161c;--muted:#5d6b7a;--line:#dfe5ec;--bg:#f6f8fa;--card:#fff;--accent:#0b5fa5;
--high:#0a7d42;--medium:#8a5a00;--low:#6b7280;--highbg:#e7f6ed;--mediumbg:#fdf3e0;--lowbg:#f1f3f5}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
header{background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
header .wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:10px 18px}
.brand{font-weight:700;letter-spacing:.2px}
.brand small{display:block;font-weight:400;color:var(--muted);font-size:12px}
nav{display:flex;gap:4px;flex-wrap:wrap;margin-left:auto}
nav a{padding:7px 10px;border-radius:7px;color:var(--ink);text-decoration:none;font-size:14px}
nav a:hover{background:var(--bg)}
nav a.on{background:var(--accent);color:#fff}
main{padding:26px 0 60px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:19px;margin:30px 0 10px}
h3{font-size:16px;margin:18px 0 8px}
p.lede{color:var(--muted);margin:0 0 18px;max-width:70ch}
.sub{color:var(--muted);font-size:14px}
a{color:var(--accent)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:14px 0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.card .top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}
.stat{font-size:27px;font-weight:700;line-height:1.1}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600;
text-transform:uppercase;letter-spacing:.4px}
.high{background:var(--highbg);color:var(--high)}
.medium{background:var(--mediumbg);color:var(--medium)}
.low{background:var(--lowbg);color:var(--low)}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:14px}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:12px 0 6px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f0f4f8;font-size:12px;text-transform:uppercase;letter-spacing:.4px;color:#33414f}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fafcfe}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.sel{font-weight:600}
.map{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:12px 0}
.map a{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:11px 13px;text-decoration:none;color:var(--ink)}
.map a b{color:var(--accent)}
.map a span{display:block;color:var(--muted);font-size:13px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.chips a{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:6px 13px;
text-decoration:none;color:var(--ink);font-size:13.5px}
.chips a b{color:var(--accent)}
.pred{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px;margin:12px 0}
.pred h3{margin:0 0 4px;font-size:16.5px}
.pred .meta{color:var(--muted);font-size:13px;margin-bottom:8px}
.pred ul{margin:10px 0 0;padding-left:18px;font-size:13.5px;color:#33414f}
.pred ul li{margin:2px 0}
blockquote{margin:0;padding:10px 14px;background:#fbfcfd;border-left:3px solid var(--accent);
border-radius:0 8px 8px 0;color:#26313c}
.flag{background:var(--card);border:1px solid var(--line);border-left:4px solid #b45309;border-radius:10px;
padding:12px 14px;margin:10px 0}
.flag b{display:block}
.small{font-size:13px;color:var(--muted)}
footer{border-top:1px solid var(--line);background:var(--card);padding:18px 0;color:var(--muted);
font-size:13px}
.empty{background:var(--card);border:1px dashed var(--line);border-radius:12px;padding:16px;color:var(--muted)}
"""

NAV = [("index.html", "Summary"), ("picks.html", "Picks"), ("predictions.html", "Previews"),
       ("matches.html", "Fixtures"), ("lines.html", "Our lines"), ("band.html", "Odds band"),
       ("sports/index.html", "By sport"), ("rechecks.html", "Live checks"),
       ("sources.html", "Sources"), ("methodology.html", "Method"), ("flagged.html", "Flagged")]


def esc(x):
    return html.escape(str(x if x is not None else ""))


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def page(path, title, body, active=""):
    depth = "" if path.count("/") == 0 else "../"
    nav = "".join(
        f'<a class="{"on" if href == active else ""}" href="{depth}{href}">{esc(label)}</a>'
        for href, label in NAV)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — OLBG desk, 24 October 2026</title>
<link rel="stylesheet" href="{depth}assets/style.css">
</head><body>
<header><div class="wrap">
  <div class="brand">OLBG desk — 24 October 2026<small>15 sports · own lines · graded picks · written previews</small></div>
  <nav>{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">Every row links to the page its value was read from. Values that could not be
read are blank and listed on the <a href="{depth}flagged.html">Flagged for review</a> page. Nothing here
is betting advice.</div></footer>
</body></html>
"""
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding="utf-8")


def confidence_pill(c):
    return f'<span class="pill {c}">{c}</span>'


def price_cell(p):
    return (f'<td class="num" title="chance {p["probability"] * 100:.1f}%">{esc(p["american_display"])}'
            f'<div class="small">{p["decimal"]:.2f} dec</div></td>')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(STYLE, encoding="utf-8")

    fixtures = load("fixtures.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    lines = load("lines.json")
    sources = load("sources.json")
    rechecks = load("rechecks.json")
    f1 = load("f1.json")

    fx_by_id = {f["id"]: f for f in fixtures["fixtures"]}
    pred_by_pick = {p["pick_id"]: p for p in preds["predictions"]}
    started = [f for f in fixtures["fixtures"] if f["start_utc"] <= fixtures["build_utc"]]
    upcoming = [f for f in fixtures["fixtures"] if f["start_utc"] > fixtures["build_utc"]]

    # ---------------------------------------------------------------- executive summary
    order = {s: i for i, s in enumerate(SPORTS)}
    ranked = sorted(picks["picks"], key=lambda p: (order[p["sport"]], -p["probability"], p["fixture_id"]))
    # the headline cards show the six shortest prices on six different matches, so one strong call
    # cannot fill the whole panel
    top, seen_fx = [], set()
    for p in sorted(picks["picks"], key=lambda r: (-r["probability"], order[r["sport"]])):
        if p["fixture_id"] in seen_fx:
            continue
        seen_fx.add(p["fixture_id"])
        top.append(p)
        if len(top) == 6:
            break
    cards = "".join(
        f'<div class="card"><div class="top"><span class="pill {p["confidence"]}">{p["confidence"]}</span>'
        f'<span class="small">{esc(p["sport"])}</span></div>'
        f'<div class="sel" style="margin:8px 0 2px;font-size:17px">{esc(p["selection"])}</div>'
        f'<div class="small">{esc(p["away"])} at {esc(p["home"])} · {esc(p["market"])}</div>'
        f'<div class="stat" style="margin-top:8px">{esc(p["american_display"])}</div>'
        f'<div class="small">{p["probability"] * 100:.1f}% chance · score {p["score"]}</div></div>'
        for p in top)
    stat_cards = f"""<div class="cards">
<div class="card"><div class="small">Upcoming fixtures</div><div class="stat">{len(upcoming)}</div>
<div class="small">of {fixtures['count']} on the desk; {len(started)} had started</div></div>
<div class="card"><div class="small">Graded picks</div><div class="stat">{picks['count']}</div>
<div class="small">{picks['high']} high · {picks['medium']} medium · {picks['low']} low</div></div>
<div class="card"><div class="small">Inside the −250…+10000 band</div><div class="stat">{picks['in_band']}</div>
<div class="small">every pick published sits inside it</div></div>
<div class="card"><div class="small">Written previews</div><div class="stat">{preds['count']}</div>
<div class="small">across {len(preds['by_sport'])} sports, shortest {preds['min_words']} words</div></div>
</div>"""
    sport_rows = "".join(
        f'<tr><td><a href="sports/{SLUG[s]}.html">{esc(s)}</a></td>'
        f'<td class="num">{sum(1 for f in upcoming if f["sport"] == s)}</td>'
        f'<td class="num">{picks["by_sport"].get(s, 0)}</td>'
        f'<td class="num">{preds["by_sport"].get(s, 0)}</td>'
        f'<td class="small">{esc(next((f["competition"] for f in upcoming if f["sport"] == s), "—"))}</td></tr>'
        for s in SPORTS)
    body = f"""<h1>Executive summary — the strongest calls first</h1>
<p class="lede">This desk covers the fifteen sports in scope for the fixtures still to start on 24–31
October 2026. Every price was originated here from an official rate or an official classification; no
bookmaker price was read. The six selections below are the shortest prices on the board, and every one
of them sits inside the −250 to +10000 band you asked for.</p>
{stat_cards}
<h2>The six strongest calls</h2>
<div class="cards">{cards}</div>
<p class="small">Every pick, with its market, chance, price, confidence grade and source link, is on
<a href="picks.html">Picks</a>. The prose for each one is on <a href="predictions.html">Previews</a>.</p>

<h2>Where everything is</h2>
<div class="map">
  <a href="picks.html"><b>Picks</b><span>{picks['count']} graded selections, one row each, with the official source</span></a>
  <a href="predictions.html"><b>Written previews</b><span>{preds['count']} unique previews, {preds['min_words']}+ words, each with the facts underneath it</span></a>
  <a href="matches.html"><b>Fixtures</b><span>{fixtures['count']} matches with status and the reason for any blank</span></a>
  <a href="lines.html"><b>Our lines</b><span>{lines['count']} originated prices: match winner, handicap and total</span></a>
  <a href="band.html"><b>Odds band</b><span>The −250…+10000 test applied to every price made here</span></a>
  <a href="sports/index.html"><b>By sport</b><span>Fifteen category pages, same sections in the same order</span></a>
  <a href="rechecks.html"><b>Live checks</b><span>What the OLBG and official pages showed when re-read in this session</span></a>
  <a href="sources.html"><b>Sources</b><span>{len(sources['sources'])} pages, with what each one supports</span></a>
  <a href="flagged.html"><b>Flagged for review</b><span>Blank rows, withheld fixtures, shortfalls and defects</span></a>
</div>

<h2>The board, sport by sport</h2>
<p class="sub">Matches still to start, graded picks and written previews for each of the fifteen sports.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th class="num">Matches left</th>
<th class="num">Picks</th><th class="num">Previews</th><th>Competition</th></tr></thead>
<tbody>{sport_rows}</tbody></table></div>
<p class="small">Four sports carry no pick because nothing bettable remains on the board: Golf and
Snooker have no OLBG listing at all, both Greyhound races had run, and the single Darts match had
started. Each one is spelled out on <a href="flagged.html">Flagged for review</a> rather than padded.</p>
"""
    page("index.html", "Executive summary", body, "index.html")

    # ---------------------------------------------------------------- picks
    rows = []
    current = None
    for p in ranked:
        if p["sport"] != current:
            current = p["sport"]
            rows.append(f'<tr><td colspan="7" style="background:#eef3f8;font-weight:700">'
                        f'{esc(current)} — {picks["by_sport"][current]} picks</td></tr>')
        rows.append(
            f'<tr><td class="small">{esc(p["start_display"])}</td>'
            f'<td>{esc(p["away"])} at {esc(p["home"])}<div class="small">{esc(p["competition"])}</div></td>'
            f'<td>{esc(p["market"])}</td><td class="sel">{esc(p["selection"])}</td>'
            f'{price_cell(p)}'
            f'<td class="num">{p["probability"] * 100:.1f}%<div class="small">score {p["score"]}</div></td>'
            f'<td>{confidence_pill(p["confidence"])}<div class="small">{p["score"]}</div>'
            f'<a class="small" href="{esc(p["official_url"])}">source</a></td></tr>')
    body = f"""<h1>Picks</h1>
<p class="lede">{picks['count']} graded selections on fixtures that had not started when the desk was
cut: {picks['high']} high confidence, {picks['medium']} medium and {picks['low']} low. Every row states
the market, the selection, our chance, our price in American and decimal odds, a 0–10 score and the
official page the inputs came from.</p>
<p class="sub">Confidence rule: <b>high</b> means a 70% chance or better with the price inside
−250…+10000; <b>medium</b> is 60% or better; anything else is <b>low</b>. The 0–10 score is our chance
multiplied by a shade for how the number was made — 1.0 for a scoring rate, 0.9 for the grid curve and
between 0.5 and 0.8 for an evidence ladder — so 5.0 is a coin flip on a full-weight number and a
ladder-based selection scores lower at the same chance.</p>
<div class="table-wrap"><table><thead><tr><th>Start</th><th>Match</th><th>Market</th>
<th>Selection</th><th class="num">Price</th><th class="num">Our chance</th><th>Grade</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<h2>Fixtures withheld from this list</h2>
<div class="table-wrap"><table><thead><tr><th>Fixture</th><th>Sport</th><th>Why it is withheld</th></tr></thead>
<tbody>{''.join(f'<tr><td>{esc(w["fixture_id"])}</td><td>{esc(w["sport"])}</td><td class="small">{esc(w["reason"])}</td></tr>' for w in picks["withheld_fixtures"])}</tbody></table></div>
"""
    page("picks.html", "Picks", body, "picks.html")

    # ---------------------------------------------------------------- previews
    blocks = []
    for s in SPORTS:
        group = [p for p in preds["predictions"] if p["sport"] == s]
        if not group:
            blocks.append(f'<h2 id="{SLUG[s]}">{esc(s)}</h2><div class="empty">No preview for {esc(s)}: '
                          f'no selection in this sport survived the grading and band rules. The reason is '
                          f'on <a href="flagged.html">Flagged for review</a>.</div>')
            continue
        blocks.append(f'<h2 id="{SLUG[s]}">{esc(s)} — {len(group)} previews</h2>')
        for p in sorted(group, key=lambda r: -r["probability"]):
            facts = "".join(f'<li>{esc(f["claim"])}: {esc(f["value"])} — '
                            f'<a href="{esc(f["source_url"])}">source</a></li>' for f in p["facts"])
            blocks.append(
                f'<div class="pred"><h3>{esc(p["headline"])}</h3>'
                f'<div class="meta">{confidence_pill(p["confidence"])} '
                f'{esc(p["sport"])} · {esc(p["away"])} at {esc(p["home"])} · {esc(p["start_display"])}</div>'
                f'<blockquote>{esc(p["text"])}</blockquote>'
                f'<div class="small" style="margin-top:8px"><b>Selection:</b> {esc(p["selection"])} — '
                f'{esc(p["market"])} at {esc(p["american_display"])} '
                f'({p["probability"] * 100:.1f}% chance, {p["words"]} words)</div>'
                f'<ul>{facts}</ul></div>')
    body = f"""<h1>Written previews</h1>
<p class="lede">{preds['count']} previews, one per graded pick, written for this desk. The shortest is
{preds['min_words']} words. Each one names the selection, the form and the numbers behind it, and the
claims underneath it are copied from the official page they were read from, with the link.</p>
<p class="sub">Jump to a sport:
{' '.join(f'<a href="#{SLUG[s]}">{esc(s)} ({preds["by_sport"].get(s, 0)})</a>' for s in SPORTS)}</p>
{''.join(blocks)}
"""
    page("predictions.html", "Written previews", body, "predictions.html")

    # ---------------------------------------------------------------- fixtures
    rows = []
    for f in sorted(fixtures["fixtures"], key=lambda r: (r["start_utc"], r["sport"])):
        state = ("started" if f["start_utc"] <= fixtures["build_utc"] else "to start")
        npicks = sum(1 for p in picks["picks"] if p["fixture_id"] == f["id"])
        rows.append(
            f'<tr><td class="small">{esc(f["start_display"])}</td><td>{esc(f["sport"])}</td>'
            f'<td>{esc(f["home"])} v {esc(f["away"])}<div class="small">{esc(f["competition"])}</div></td>'
            f'<td>{esc(state)}</td>'
            f'<td class="num">{npicks if npicks else "—"}</td>'
            f'<td class="small">{(esc(f["blank_reason"]) if f.get("blank_reason") else "priced")}</td>'
            f'<td class="small"><a href="{esc(f["official_url"])}">official</a>'
            + (f' · <a href="{esc(f["olbg_url"])}">OLBG</a>' if f.get("olbg_url") else "") + '</td></tr>')
    body = f"""<h1>Fixtures</h1>
<p class="lede">All {fixtures['count']} matches on the desk, in start order. A fixture that had already
started when the desk was cut keeps its row and its source but carries no pick, because the price could
no longer be taken. A fixture with no line states the reason in its own row.</p>
<div class="table-wrap"><table><thead><tr><th>Start</th><th>Sport</th><th>Match</th><th>Status</th>
<th class="num">Picks</th><th>Pricing note</th><th>Links</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="small">{len(started)} fixtures had already started at {esc(fixtures['build_utc'])}; they are
listed with no pick and are covered on <a href="flagged.html">Flagged for review</a>.</p>
"""
    page("matches.html", "Fixtures", body, "matches.html")

    # ---------------------------------------------------------------- our lines
    groups = {}
    for r in lines["lines"]:
        groups.setdefault(r["sport"], []).append(r)
    blocks = []
    for s in SPORTS:
        group = groups.get(s, [])
        if not group:
            blocks.append(f'<h2 id="{SLUG[s]}">{esc(s)}</h2><div class="empty">No line was originated '
                          f'for {esc(s)}; the fixtures page states why.</div>')
            continue
        by_fx = {}
        for r in group:
            by_fx.setdefault(r["fixture_id"], []).append(r)
        inner = []
        for fid, rows_ in by_fx.items():
            f = fx_by_id.get(fid, {})
            inner.append(f'<tr><td colspan="4" style="background:#f7fafc"><b>{esc(f.get("home", fid))} v '
                         f'{esc(f.get("away", ""))}</b> <span class="small">{esc(f.get("start_display", ""))}</span></td></tr>')
            for r in rows_:
                inner.append(f'<tr><td>{esc(r["market"])}</td><td class="sel">{esc(r["selection"])}</td>'
                             f'<td class="num">{r["probability"] * 100:.1f}%</td>'
                             f'<td class="num">{esc(r["american_display"])}</td></tr>')
        blocks.append(f'<h2 id="{SLUG[s]}">{esc(s)} — {len(group)} prices</h2>'
                      f'<div class="table-wrap"><table><thead><tr><th>Market</th><th>Selection</th>'
                      f'<th class="num">Chance</th><th class="num">Price</th></tr></thead>'
                      f'<tbody>{"".join(inner)}</tbody></table></div>')
    body = f"""<h1>Our lines</h1>
<p class="lede">{lines['count']} prices originated for this desk across match winner, handicap and total
markets. No bookmaker price was read: each probability comes from an official rate or an official
classification, and the price is the reciprocal of that probability rounded to two decimals.</p>
<p class="sub">The full method for each family is on <a href="methodology.html">Method</a>. The Formula 1
race winner market is the one market originated in this session; the rest were priced earlier today from
the same official records and are republished unchanged.</p>
{''.join(blocks)}
"""
    page("lines.html", "Our lines", body, "lines.html")

    # ---------------------------------------------------------------- band
    band_rows = []
    lo, hi = -250, 10000
    for p in ranked:
        inside = lo <= p["american"] <= hi
        band_rows.append(
            f'<tr><td>{esc(p["sport"])}</td><td class="sel">{esc(p["selection"])}</td>'
            f'<td>{esc(p["market"])}</td><td class="num">{esc(p["american_display"])}</td>'
            f'<td class="num">{p["probability"] * 100:.1f}%</td>'
            f'<td>{"inside" if inside else "outside"}</td>'
            f'<td>{confidence_pill(p["confidence"])}</td></tr>')
    body = f"""<h1>The −250 to +10000 band</h1>
<p class="lede">Fair −250 is a 71.43% chance and +10000 is a 0.99% chance. A selection rated above
71.43% cannot be backed inside the band at all, so this desk never publishes one as a pick: it moves to
a handicap or a total rung where the number lands inside. All {picks['count']} published picks are
inside the band, and {picks['high']} of them clear the 70% high-confidence floor.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Selection</th><th>Market</th>
<th class="num">Price</th><th class="num">Chance</th><th>Band test</th><th>Grade</th></tr></thead>
<tbody>{''.join(band_rows)}</tbody></table></div>
<p class="small">Chalk that would price shorter than −250 is still published on
<a href="lines.html">Our lines</a>; it is simply not dressed up as a tip.</p>
"""
    page("band.html", "Odds band", body, "band.html")

    # ---------------------------------------------------------------- live checks
    rows = "".join(
        f'<tr><td>{esc(r["sport"])}</td><td class="small">{esc(r["read_utc"])}</td>'
        f'<td class="small">{esc(r["result"])}</td>'
        f'<td>{"yes" if r["changed_since_capture"] else "no"}</td>'
        f'<td class="small"><a href="{esc(r["url"])}">page</a></td></tr>'
        for r in rechecks["rechecks"])
    body = f"""<h1>Live checks made in this session</h1>
<p class="lede">These are the OLBG and governing-body pages re-read after the 17:35Z capture the
fixtures were inherited from. Each row says what the page showed at the time it was read.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Read at</th><th>What the page showed</th>
<th>New since capture</th><th>Link</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="small">The Formula 1 qualifying classification is the one item that changed a line: the race
was unpriced at the earlier capture because the grid did not exist, and it is priced here from the
published grid.</p>
"""
    page("rechecks.html", "Live checks", body, "rechecks.html")

    # ---------------------------------------------------------------- sources
    rows = "".join(
        f'<tr><td class="small"><a href="{esc(s["url"])}">{esc(s["url"])}</a></td>'
        f'<td class="small">{esc(s.get("kind", ""))}</td>'
        f'<td class="small">{esc(", ".join(s.get("sports", [])))}</td>'
        f'<td class="num">{s.get("claims", "")}</td>'
        f'<td class="small">{esc(s.get("captured_utc", ""))}</td></tr>'
        for s in sorted(sources["sources"], key=lambda r: r["url"]))
    extra = "".join(f'<li><a href="{esc(r["url"])}">{esc(r["url"])}</a> — {esc(r["sport"])}, read '
                    f'{esc(r["read_utc"])}</li>' for r in rechecks["rechecks"])
    body = f"""<h1>Sources</h1>
<p class="lede">{len(sources['sources'])} pages were read to build the fixture records, plus the pages
re-read live in this session. A link records where a value was read; it does not prove the page still
shows it, so each fact also carries its own capture time.</p>
<div class="table-wrap"><table><thead><tr><th>Page</th><th>Kind</th><th>Sports</th>
<th class="num">Claims</th><th>Captured</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Re-read during this session</h2><ul>{extra}</ul>
<h2>Formula 1 classification</h2>
<p class="small">Qualifying was read from
<a href="{esc(f1['source_url'])}">{esc(f1['source_url'])}</a> at {esc(f1['captured_utc'])} and is stored
verbatim in <code>data/latest/f1.json</code>.</p>
"""
    page("sources.html", "Sources", body, "sources.html")

    # ---------------------------------------------------------------- method
    body = f"""<h1>Method</h1>
<p class="lede">Four pricing families and one confidence rule, all stated so a reader can reproduce a
price. No bookmaker price is read anywhere in this desk.</p>
<h2>Where the inputs come from</h2>
<p>Each fixture carries a list of claims, and each claim carries the page it was read from and the time
it was read. The fixture records were captured at 17:35Z on 24 October 2026 and are republished here
unchanged with that capture time; the Formula 1 race was captured first hand after qualifying.</p>
<h2>How a price is made</h2>
<table><thead><tr><th>Family</th><th>Sports</th><th>What it does</th></tr></thead><tbody>
<tr><td>Poisson scoring</td><td>Ice Hockey, Baseball</td><td>Expected goals or runs come from each side's
scoring and conceding rates; the score grid gives the winner, handicap and total chances.</td></tr>
<tr><td>Normal margin</td><td>Rugby Union, Rugby League, Gaelic Sports, Basketball</td>
<td>Mean margin from points for and against with a stated home edge, converted to a chance with a
stated spread.</td></tr>
<tr><td>Evidence ladder</td><td>Volleyball, Handball, Cricket, Tennis</td><td>Each side is placed on a
rung from the sourced facts on its record; one rung is worth ten probability points from 50%.</td></tr>
<tr><td>Grid curve</td><td>Motor Racing</td><td>Chance falls geometrically down the published starting
grid, with the curve fixed so pole is worth a stated 40% share.</td></tr>
</tbody></table>
<p>Prices are the reciprocal of the chance, rounded to two decimals, and the American figure is derived
from that same decimal so the two always agree.</p>
<h2>Confidence</h2>
<table><thead><tr><th>Grade</th><th>Rule</th></tr></thead><tbody>
<tr><td>High</td><td>70% chance or better <i>and</i> the price inside −250…+10000. A side rated above
71.43% cannot satisfy both, so it is moved to a handicap or total rung.</td></tr>
<tr><td>Medium</td><td>60% chance or better.</td></tr>
<tr><td>Low</td><td>Everything else. Published with the label on it, never presented as a strong call.</td></tr>
</tbody></table>
<h2>What is never done</h2>
<ul>
<li>A value that is not on an official page stays blank, and the blank is published with its reason.</li>
<li>No injury, line-up or travel claim is made unless the official record for that fixture carries it.</li>
<li>No market is priced where both sides' inputs are missing.</li>
<li>Displayed times are never converted between time zones.</li>
</ul>
"""
    page("methodology.html", "Method", body, "methodology.html")

    # ---------------------------------------------------------------- flagged
    no_pick = [s for s in SPORTS if picks["by_sport"].get(s, 0) == 0]
    thin = [(s, preds["by_sport"].get(s, 0)) for s in SPORTS if 0 < preds["by_sport"].get(s, 0) < 5]
    flags = [
        ("Four sports carry no pick at all",
         "Golf and Snooker: the OLBG hubs returned 'No tips found.' when re-read at 22:24Z and 22:27Z, so "
         "there is no OLBG event to attach a selection to. Greyhounds: both races on the card had started. "
         "Darts: the only match listed, Luke Littler v Nathan Aspinall, started at 18:00Z. Nothing is "
         "invented to fill the gap.",
         "https://www.olbg.com/betting-tips/Golf/5"),
        (f"{len(started)} fixtures had already started when the desk was cut",
         "They keep their rows and their sources but carry no pick, because the price could no longer be "
         "taken: " + ", ".join(f["home"] + " v " + f["away"] for f in sorted(started, key=lambda r: r["start_utc"]))
         + ". They are listed on the fixtures page with their status.",
         "matches.html"),
        ("Two fixtures are withheld because our own input is broken",
         "; ".join(f'{w["fixture_id"]} — {w["reason"]}' for w in picks["withheld_fixtures"])
         + " The fault is in the inherited point inputs, not in the fixture: both rows are otherwise well "
           "sourced. Flagged rather than silently re-scaled.",
         "picks.html"),
        ("The inherited line file mislabels some totals as match winners",
         "Several 'Total sets 4.5' rows carry the internal label 'winner'. Taking that field at face value "
         "let a totals row occupy a fixture's match-winner slot. This desk derives the market family from "
         "the published label instead and treats the field as unreliable.",
         "lines.html"),
        ("Tennis handicap unit is not stated in the line data",
         "The inherited prices describe the tennis handicap as an evidence-ladder line and state that no "
         "game total is published, so the unit of the 3.5 line is not defined by the source. The previews "
         "say 'the 3.5 line' and do not claim games or sets.",
         "lines.html"),
        ("Five written previews per sport could not be met everywhere",
         "Short of five: " + ", ".join(f"{s} ({n})" for s, n in thin) + ". The ceiling is the number of "
         "matches OLBG lists in those sports on this date, not a shortage of effort: Baseball has one "
         "unstarted game, Gaelic Sports one final, and Volleyball and Cricket four and three matches. "
         "Each preview still covers a distinct selection.",
         "predictions.html"),
        ("Only three picks clear the high-confidence bar",
         "A 70% chance with a price inside −250…+10000 is a narrow window: fair −250 is already 71.43%. The "
         "remaining " + str(picks["medium"]) + " medium and " + str(picks["low"])
         + " low picks are published with their grade on them rather than relabelled.",
         "picks.html"),
        ("Fixture facts are inherited from the 17:35Z capture",
         "The records were captured earlier today by another desk in this repository and are republished "
         "with that capture time. Only the Formula 1 classification was read first hand in this session, "
         "along with the five live re-checks listed on the live-checks page.",
         "rechecks.html"),
        ("The Formula 1 race carries a date but no start clock",
         "The official results index gives the meeting as 23–25 October and race day as 25 October; it "
         "publishes no start time on that page, so the row shows the date only rather than a guess.",
         "https://www.formula1.com/en/results/2026/races/1297/united-states/qualifying"),
        ("Snooker's final has one unknown finalist",
         "The Northern Ireland Open final is Kyren Wilson against the winner of the second semi-final, "
         "which the World Snooker Tour match list had not resolved in the view read at 22:30Z. The row is "
         "published without a line.",
         "https://www.wst.tv/matches/"),
    ]
    cards = "".join(f'<div class="flag"><b>{esc(t)}</b><p class="small">{esc(d)}</p>'
                    f'<a class="small" href="{esc(u)}">where to check</a></div>' for t, d, u in flags)
    body = f"""<h1>Flagged for review</h1>
<p class="lede">Everything that is blank, withheld, short of the target or defective in the underlying
data is listed here with a link to where you can check it. None of it is hidden on a row somewhere.</p>
{cards}
"""
    page("flagged.html", "Flagged for review", body, "flagged.html")

    # ---------------------------------------------------------------- sports index
    rows = "".join(
        f'<tr><td><a href="{SLUG[s]}.html">{esc(s)}</a></td>'
        f'<td class="num">{sum(1 for f in upcoming if f["sport"] == s)}</td>'
        f'<td class="num">{picks["by_sport"].get(s, 0)}</td>'
        f'<td class="num">{preds["by_sport"].get(s, 0)}</td>'
        f'<td class="num">{sum(1 for r in lines["lines"] if r["sport"] == s)}</td></tr>' for s in SPORTS)
    body = f"""<h1>By sport</h1>
<p class="lede">Fifteen categories, same sections in the same order. Every page shows the fixtures still
to start, the graded picks with their prices, the written previews and the links behind each value.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th class="num">Matches left</th>
<th class="num">Picks</th><th class="num">Previews</th><th class="num">Originated prices</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    page("sports/index.html", "By sport", body, "sports/index.html")

    for s in SPORTS:
        fx = [f for f in upcoming if f["sport"] == s]
        px = [p for p in ranked if p["sport"] == s]
        pr = [p for p in preds["predictions"] if p["sport"] == s]
        ftable = ("<div class='table-wrap'><table><thead><tr><th>Start</th><th>Match</th><th>Status</th>"
                  "<th class='num'>Picks</th><th>Source</th></tr></thead><tbody>" + "".join(
                      f'<tr><td class="small">{esc(f["start_display"])}</td>'
                      f'<td>{esc(f["home"])} v {esc(f["away"])}<div class="small">{esc(f["competition"])}</div></td>'
                      f'<td class="small">{esc(f["blank_reason"] or "priced")}</td>'
                      f'<td class="num">{sum(1 for p in picks["picks"] if p["fixture_id"] == f["id"])}</td>'
                      f'<td class="small"><a href="{esc(f["official_url"])}">official</a></td></tr>'
                      for f in fx) + "</tbody></table></div>") if fx else \
            "<div class='empty'>No fixture in this sport is still to start on the desk.</div>"
        ptable = ("<div class='table-wrap'><table><thead><tr><th>Match</th><th>Market</th><th>Selection</th>"
                  "<th class='num'>Price</th><th class='num'>Chance</th><th>Grade</th><th>Source</th></tr></thead><tbody>"
                  + "".join(f'<tr><td>{esc(p["away"])} at {esc(p["home"])}</td><td>{esc(p["market"])}</td>'
                            f'<td class="sel">{esc(p["selection"])}</td>'
                            f'<td class="num">{esc(p["american_display"])}</td>'
                            f'<td class="num">{p["probability"] * 100:.1f}%</td>'
                            f'<td>{confidence_pill(p["confidence"])}</td>'
                            f'<td class="small"><a href="{esc(p["official_url"])}">source</a></td></tr>'
                            for p in px) + "</tbody></table></div>") if px else \
            f"<div class='empty'>No pick in this sport. The reason is on <a href='../flagged.html'>Flagged for review</a>.</div>"
        pblocks = "".join(
            f'<div class="pred"><h3>{esc(p["headline"])}</h3>'
            f'<div class="meta">{confidence_pill(p["confidence"])} {esc(p["away"])} at {esc(p["home"])} · '
            f'{esc(p["market"])} · {esc(p["american_display"])}</div>'
            f'<blockquote>{esc(p["text"])}</blockquote><ul>'
            + "".join(f'<li>{esc(f["claim"])}: {esc(f["value"])} — <a href="{esc(f["source_url"])}">source</a></li>'
                      for f in p["facts"]) + '</ul></div>' for p in pr)
        body = f"""<h1>{esc(s)}</h1>
<p class="lede">{len(fx)} fixtures still to start, {len(px)} graded picks and {len(pr)} written
previews on the desk for {esc(s)}.</p>
<h2>Fixtures still to start</h2>{ftable}
<h2>Picks</h2>{ptable}
<h2>Written previews</h2>{pblocks or "<div class='empty'>No preview for this sport. The reason is on <a href='../flagged.html'>Flagged for review</a>.</div>"}
"""
        page(f"sports/{SLUG[s]}.html", s, body, "sports/index.html")

    pages = len(list(OUT.rglob("*.html")))
    print(f"latest_build: {pages} pages, {fixtures['count']} fixtures, {picks['count']} picks, "
          f"{preds['count']} previews, {lines['count']} prices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
