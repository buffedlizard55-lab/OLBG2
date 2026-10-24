#!/usr/bin/env python3
"""Build the /clarity/ static dashboard from data/clarity/*.json."""
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clarity"
OUT = ROOT / "clarity"

SPORTS = [
    ("golf", "Golf"), ("volleyball", "Volleyball"), ("rugby-union", "Rugby Union"),
    ("cricket", "Cricket"), ("snooker", "Snooker"), ("darts", "Darts"),
    ("baseball", "Baseball"), ("gaelic-sports", "Gaelic Sports"), ("greyhounds", "Greyhounds"),
    ("tennis", "Tennis"), ("motor-racing", "Motor Racing"), ("handball", "Handball"),
    ("ice-hockey", "Ice Hockey"), ("basketball", "Basketball"), ("rugby-league", "Rugby League"),
]
SLUG = dict((name, slug) for slug, name in SPORTS)

NAV = [
    ("index.html", "Executive summary"), ("picks.html", "Picks"), ("predictions.html", "Predictions"),
    ("matches.html", "All matches"), ("lines.html", "Originated lines"), ("band.html", "Odds band"),
    ("sports/index.html", "Sports"), ("sources.html", "Sources"), ("flagged.html", "Flagged"),
    ("methodology.html", "Method"), ("olbg.html", "OLBG"), ("repo-review.html", "Repo review"),
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def e(x):
    return html.escape(str(x), quote=True)


def human(ts):
    if not ts:
        return "—"
    try:
        d = dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return e(ts)
    return d.strftime("%a %d %b %H:%M UTC")


def day(ts):
    try:
        return ts[:10]
    except Exception:
        return ""


def badge(conf):
    return f'<span class="badge {conf}">{conf}</span>'


def price(x):
    return f'<span class="price">{e(x)}</span>'


def css():
    return """
:root{--ink:#12161c;--muted:#5c6773;--line:#e2e7ee;--bg:#f7f9fc;--card:#fff;--brand:#0f5c4a;--brand2:#12876a;
--high:#0b7a4b;--highbg:#e6f5ec;--med:#8a5a00;--medbg:#fdf3e0;--low:#5c6773;--lowbg:#eef1f5;--warn:#a3231f;--warnbg:#fdeceb}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:#0b5fa5;text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.bar{display:flex;align-items:center;gap:18px;height:60px;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:-.2px;color:var(--brand);font-size:18px}
.brand span{color:var(--muted);font-weight:500;font-size:13px}
nav.main{display:flex;gap:4px;flex-wrap:wrap;margin-left:auto}
nav.main a{padding:7px 10px;border-radius:8px;color:#2b3440;font-size:14px}
nav.main a:hover{background:var(--bg);text-decoration:none}
nav.main a.on{background:var(--brand);color:#fff}
main{padding:28px 0 60px}
h1{font-size:30px;line-height:1.2;margin:0 0 8px;letter-spacing:-.5px}
h2{font-size:21px;margin:34px 0 10px;letter-spacing:-.2px}
h3{font-size:16px;margin:22px 0 8px}
p.lede{font-size:18px;color:#2b3440;margin:0 0 14px;max-width:70ch}
p.sub{color:var(--muted);margin:0 0 18px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:18px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi b{display:block;font-size:26px;letter-spacing:-.5px;color:var(--brand)}
.kpi span{color:var(--muted);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:10px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.card h3{margin:0 0 6px;font-size:16px}
.card p{margin:0;color:var(--muted);font-size:14px}
.card a.more{display:inline-block;margin-top:10px;font-size:14px;font-weight:600}
.jump{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}
.jump a{background:var(--brand);color:#fff;border-radius:12px;padding:16px;display:block}
.jump a:hover{background:var(--brand2);text-decoration:none}
.jump b{display:block;font-size:17px}
.jump span{font-size:13px;opacity:.9}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:#fff;margin:10px 0 4px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f1f4f8;font-size:12.5px;text-transform:uppercase;letter-spacing:.4px;color:#44505e;white-space:nowrap}
tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fbfcfe}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:700;text-transform:capitalize}
.badge.high{background:var(--highbg);color:var(--high)}
.badge.medium{background:var(--medbg);color:var(--med)}
.badge.low{background:var(--lowbg);color:var(--low)}
.price{font-variant-numeric:tabular-nums;font-weight:700}
.pick{background:#f4fbf7;border-left:3px solid var(--high);padding:6px 10px;border-radius:0 8px 8px 0;display:inline-block}
.muted{color:var(--muted)}
.small{font-size:13px}
.notice{border-radius:12px;padding:14px 16px;margin:16px 0;font-size:14.5px}
.notice.info{background:#eef4ff;border:1px solid #d5e2fb}
.notice.warn{background:var(--warnbg);border:1px solid #f6cbc8}
.notice.ok{background:var(--highbg);border:1px solid #cbe9d8}
.pred{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}
.pred h3{margin:0 0 4px;font-size:17px;letter-spacing:-.2px}
.pred .meta{font-size:13px;color:var(--muted);margin:0 0 10px}
.pred .sel{background:#f4fbf7;border:1px solid #cbe9d8;border-radius:10px;padding:8px 12px;margin:0 0 10px;font-weight:600}
.pred p.body{margin:0 0 10px}
details{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:8px 0}
summary{cursor:pointer;font-weight:600;font-size:14px}
footer{border-top:1px solid var(--line);background:#fff;padding:22px 0;color:var(--muted);font-size:13.5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}h1{font-size:24px}}
.pill{display:inline-block;background:#eef1f5;color:#3c4653;border-radius:999px;padding:2px 9px;font-size:12px;margin:0 4px 4px 0}
"""


def page(title, body, current="", subtitle=""):
    prefix = "../" if current == "sports" else ""
    _ = prefix
    footer_nav = " · ".join('<a href="%s%s">%s</a>' % (prefix, u, e(t)) for u, t in NAV[:6])
    footer_nav += ' · <a href="%sflagged.html">Flagged for review</a>' % prefix
    nav_parts = []
    for u, t in NAV:
        cls = ' class="on"' if u == current else ''
        nav_parts.append('<a href="%s%s"%s>%s</a>' % (prefix, u, cls, e(t)))
    nav = "".join(nav_parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · OLBG2 /clarity/</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<header class="top"><div class="wrap bar">
<a class="brand" href="{prefix}index.html">OLBG2 <span>/clarity/ · 24 Oct 2026 snapshot</span></a>
<nav class="main">{nav}</nav>
</div></header>
<main><div class="wrap">
<h1>{e(title)}</h1>
{f'<p class="lede">{subtitle}</p>' if subtitle else ''}
{body}
</div></main>
<footer><div class="wrap">
Snapshot captured 2026-10-24 17:35 UTC · every row carries the official page it came from ·
{footer_nav}
</div></footer>
</body></html>"""


def sport_href(sport):
    return f"sports/{SLUG[sport]}.html"


def build_index(fx, matches, picks, preds, flags):
    high = [p for p in picks["picks"] if p["confidence"] == "high"]
    todays = [p for p in picks["picks"] if day(p["start_utc"]) == "2026-10-24"]
    nextday = [p for p in picks["picks"] if day(p["start_utc"]) == "2026-10-25"]
    rows = "".join(
        f"<tr><td>{human(p['start_utc'])}</td><td>{badge(p['confidence'])}</td>"
        f"<td><a href=\"{sport_href(p['sport'])}\">{e(p['sport'])}</a></td>"
        f"<td><strong>{e(p['selection'])}</strong><div class=\"small muted\">{e(p['market'])}</div></td>"
        f"<td>{price(p['american_display'])}<div class=\"small muted\">{p['probability'] * 100:.1f}%</div></td>"
        f"<td class=\"small\">{e(p['home'])} v {e(p['away'])}</td>"
        f"<td class=\"small\"><a href=\"{e(p['official_url'])}\">official</a></td></tr>"
        for p in high)
    sport_cards = ""
    for slug, name in SPORTS:
        ms = [m for m in matches if m["sport"] == name]
        ps = [p for p in picks["picks"] if p["sport"] == name]
        ws = [p for p in preds["predictions"] if p["sport"] == name]
        hi = [p for p in ps if p["confidence"] == "high"]
        sport_cards += (
            f'<div class="card"><h3><a href="{sport_href(name)}">{e(name)}</a></h3>'
            f'<p>{len(ms)} fixtures · {len(ps)} priced picks · <strong>{len(hi)} high</strong> · '
            f'{len(ws)} write-ups</p>'
            f'<a class="more" href="{sport_href(name)}">Open {e(name)} →</a></div>')
    body = f"""
<div class="jump">
<a href="predictions.html"><b>Read the write-ups</b><span>{preds['count']} full predictions with sourced facts</span></a>
<a href="picks.html"><b>See every pick</b><span>{picks['count']} graded selections, confidence first</span></a>
<a href="band.html"><b>−250 to +10000 board</b><span>{sum(1 for p in picks['picks'] if p['in_band'])} selections inside the focus band</span></a>
<a href="matches.html"><b>All {matches['count'] if isinstance(matches, dict) else len(matches)} matches</b><span>every fixture with its official source</span></a>
</div>

<h2>Today at a glance</h2>
<div class="kpis">
  <div class="kpi"><b>{len(high)}</b><span>high-confidence picks</span></div>
  <div class="kpi"><b>{len(todays)}</b><span>picks for 24 Oct</span></div>
  <div class="kpi"><b>{len(nextday)}</b><span>picks for 25 Oct</span></div>
  <div class="kpi"><b>{picks['count']}</b><span>graded picks in total</span></div>
  <div class="kpi"><b>{preds['count']}</b><span>written predictions</span></div>
  <div class="kpi"><b>{len(matches) if not isinstance(matches, dict) else matches['count']}</b><span>verified fixtures</span></div>
  <div class="kpi"><b>{load('lines.json')['count']}</b><span>originated selections</span></div>
  <div class="kpi"><b>{flags['count']}</b><span>flagged items</span></div>
</div>

<div class="notice ok"><strong>Where the picks are.</strong> Every pick has a
<a href="picks.html">line, a price and a confidence badge</a> on the Picks page, and every pick that
carries a write-up appears in full on <a href="predictions.html">Predictions</a>. The executive table below
is only the high-confidence shortlist: it is the same data, not a separate list.</div>

<h2>Executive summary — high-confidence picks</h2>
<p class="sub">Each row states the selection in betting terms (team or side plus line or total), the price,
the probability and the official page the fixture came from.</p>
<div class="table-wrap"><table>
<thead><tr><th>Starts</th><th>Confidence</th><th>Sport</th><th>Selection</th><th>Our price</th><th>Match</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Where the picks are, sport by sport</h2>
<div class="cards">{sport_cards}</div>

<h2>How to read this desk</h2>
<div class="grid2">
<div class="card"><h3>1. Fixtures come from governing bodies</h3><p>Fifty fixtures across exactly the fifteen
requested sports, each captured from the league, tour or federation page named on its row. OLBG is used only
to cross-check what is listed.</p><a class="more" href="sources.html">Source register →</a></div>
<div class="card"><h3>2. Lines are ours</h3><p>No bookmaker price is read to build a line. Where the
PGA TOUR leaderboard embeds FanDuel prices, the row is labelled market-implied and kept out of the
originated totals.</p><a class="more" href="methodology.html">Method →</a></div>
<div class="card"><h3>3. Gaps are published</h3><p>Ten fixtures carry no line and say why. Thirteen review
items name the exact page that could not be read.</p><a class="more" href="flagged.html">Flagged for review →</a></div>
<div class="card"><h3>4. The repo is audited too</h3><p>Seven findings from a line-by-line scan of the
existing layers, including a future-only desk that still prices started games.</p><a class="more" href="repo-review.html">Repo review →</a></div>
</div>
"""
    return page("Executive summary", body, "index.html",
                "Every pick, its price, its confidence and its source on one screen — 2026-10-24 snapshot.")


def build_picks(picks, preds):
    have = {p["fixture_id"]: p for p in preds["predictions"]}
    rows = ""
    for p in picks["picks"]:
        link = f'<a href="predictions.html#pred-{e(p["fixture_id"])}">read</a>' if p["fixture_id"] in have else '<span class="muted">—</span>'
        rows += (f"<tr><td>{human(p['start_utc'])}</td><td>{badge(p['confidence'])}</td>"
                 f"<td><a href=\"{sport_href(p['sport'])}\">{e(p['sport'])}</a></td>"
                 f"<td><strong>{e(p['selection'])}</strong><div class=\"small muted\">{e(p['market'])}</div></td>"
                 f"<td>{price(p['american_display'])}</td><td class=\"small\">{p['probability']*100:.1f}%</td>"
                 f"<td class=\"small\">{e(p['home'])} v {e(p['away'])}</td><td>{link}</td>"
                 f"<td class=\"small\"><a href=\"{e(p['official_url'])}\">official page</a></td></tr>")
    by = picks["by_sport"]
    body = f"""
<p class="lede">One selection per priced fixture. Confidence is graded from the originated probability and
capped by the sport's evidence quality; the cap and its reason are printed under every sport page.</p>
<div class="kpis">
  <div class="kpi"><b>{picks['high']}</b><span>high</span></div>
  <div class="kpi"><b>{sum(1 for p in picks['picks'] if p['confidence'] == 'medium')}</b><span>medium</span></div>
  <div class="kpi"><b>{sum(1 for p in picks['picks'] if p['confidence'] == 'low')}</b><span>low</span></div>
  <div class="kpi"><b>{picks['high_in_band']}</b><span>high inside the band</span></div>
</div>
<p class="sub">Coverage: {" · ".join(f"{e(s)} {n}" for s, n in sorted(by.items()))}</p>
<div class="notice info"><strong>Every pick is a price we originated, not a bookmaker quote.</strong>
The American figure is the reciprocal of the probability we derived from the sourced inputs. It tells you
what the selection would pay at our fair line; it does not claim that any bookmaker offers it.</div>
<div class="table-wrap"><table>
<thead><tr><th>Starts</th><th>Confidence</th><th>Sport</th><th>Selection</th><th>Our price</th><th>Chance</th><th>Match</th><th>Write-up</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    return page("Picks and confidence", body, "picks.html",
                f"{picks['count']} graded selections across {len(by)} sports.")


def build_predictions(preds, picks):
    cards = ""
    for p in preds["predictions"]:
        olbg_link = f' · <a href="{e(p["olbg_url"])}">OLBG listing</a>' if p["olbg_url"] else ""
        facts = "".join(f"<li><strong>{e(f['value'])}</strong> — {e(f['claim'])} "
                        f"<a href=\"{e(f['source_url'])}\">source</a></li>" for f in p["facts"])
        cards += f"""
<article class="pred" id="pred-{e(p['fixture_id'])}">
<h3>{e(p['headline'])}</h3>
<p class="meta">{human(p['start_utc'])} · <a href="{sport_href(p['sport'])}">{e(p['sport'])}</a> ·
{e(p['competition'])} · {badge(p['confidence'])}</p>
<div class="sel">Selection: {e(p['selection'])} · {e(p['market'])} · our price {price(p['american_display'])}
{p['probability']*100:.1f}%</div>
<p class="body">{e(p['text'])}</p>
<details><summary>Sourced facts behind this prediction ({len(p['facts'])})</summary><ul class="small">{facts}</ul>
<p class="small"><a href="{e(p['official_url'])}">Fixture source</a>{olbg_link}</p></details>
</article>"""
    body = f"""
<p class="lede">Each prediction states the market and the selection, then supports it with the form,
recent results, match statistics and — where an official report exists — the availability picture for that
specific fixture. Every numbered claim is linked to the page it came from.</p>
<div class="kpis">
  <div class="kpi"><b>{preds['count']}</b><span>written predictions</span></div>
  <div class="kpi"><b>{len(preds['by_sport'])}</b><span>sports covered</span></div>
  <div class="kpi"><b>{preds['min_words']}</b><span>shortest prediction (words)</span></div>
  <div class="kpi"><b>{sum(1 for p in preds['predictions'] if p['confidence']=='high')}</b><span>on high-confidence picks</span></div>
</div>
<div class="notice warn">{e(preds['shortfall_note'])}</div>
{cards}
"""
    return page("Predictions", body, "predictions.html",
                "Full write-ups, each with the sourced facts that support it.")


def build_matches(matches):
    rows = ""
    for m in matches:
        pick = m["pick"]
        pickcell = (f"<strong>{e(pick['selection'])}</strong><div class=\"small muted\">{e(pick['market'])} · "
                    f"{e(pick['american_display'])}</div>") if pick else '<span class="muted">no line</span>'
        status = ('<span class="badge high">priced</span>' if m["status"] == "priced"
                  else f'<span class="badge low">{e(m["status"])}</span>')
        reason = f'<div class="small muted">{e(m["blank_reason"])}</div>' if m.get("blank_reason") else ""
        extra = ''
        if m["olbg_url"]:
            extra = ' · <a href="%s">OLBG</a>' % e(m["olbg_url"])
        rows += ("<tr><td>%s</td><td>%s</td><td><a href=\"%s\">%s</a></td>"
                 "<td>%s v %s<div class=\"small muted\">%s · %s</div></td>"
                 "<td>%s<div class=\"small muted\">%d selections</div></td>"
                 "<td>%s%s</td><td class=\"small\"><a href=\"%s\">official</a>%s</td></tr>" % (
                     human(m["start_utc"]),
                     badge(m["pick"]["confidence"]) if pick else "—",
                     sport_href(m["sport"]), e(m["sport"]),
                     e(m["home"]), e(m["away"]), e(m["competition"]), e(m["venue"]),
                     status, m["markets"], pickcell, reason, e(m["official_url"]), extra))
    body = f"""
<p class="lede">All {len(matches)} fixtures captured for this snapshot. Rows marked <em>blank</em> were
published anyway, with the reason no line could be originated.</p>
<div class="table-wrap"><table>
<thead><tr><th>Starts</th><th>Conf.</th><th>Sport</th><th>Fixture</th><th>Status</th><th>Pick</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    return page("All matches", body, "matches.html",
                f"{len(matches)} fixtures across exactly fifteen sports.")


def build_lines(lines, matches):
    src = {m["id"]: m["official_url"] for m in matches}
    rows = ""
    for r in lines["lines"]:
        cls = "high" if r["in_band"] else "low"
        rows += (f"<tr><td class=\"small\">{e(r['fixture_id'])}</td><td>{e(r['market'])}</td>"
                 f"<td><strong>{e(r['selection'])}</strong></td><td class=\"small\">{r['probability']*100:.1f}%</td>"
                 f"<td>{price(r['american_display'])}</td><td class=\"small\">{r['decimal']}</td>"
                 f"<td><span class=\"badge {cls}\">{'in band' if r['in_band'] else 'outside'}</span></td>"
                 f"<td class=\"small\">{e(r['basis'])}</td>"
                 f"<td class=\"small\"><a href=\"{e(src.get(r['fixture_id'], ''))}\">official</a></td></tr>")
    body = f"""
<p class="lede">{lines['count']} selections originated from the captured official inputs: match winner,
handicap/spread/puck line/run line/set or leg handicap, and match totals. Nothing here is a bookmaker price.</p>
<div class="notice warn"><strong>{lines['market_implied_count']} outright selections are kept out of this
table</strong> because they are market-implied: the PGA TOUR leaderboard embeds FanDuel win prices, which are
published on the golf page and labelled as such rather than counted as our own line.</div>
<div class="notice info"><strong>The price is the reciprocal of our probability.</strong> A selection at
−250 wins 71.4% of the time at our fair line; the same selection at +10000 wins 0.99% of the time. The
Odds band page explains why the band and the 70% rule barely overlap.</div>
<div class="table-wrap"><table>
<thead><tr><th>Fixture</th><th>Market</th><th>Selection</th><th>Chance</th><th>Our price</th><th>Decimal</th><th>Band</th><th>Basis</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    return page("Originated lines", body, "lines.html",
                "Multi-market lines originated in this snapshot.")


def build_band(picks):
    inband = [p for p in picks["picks"] if p["in_band"]]
    high_in = [p for p in inband if p["confidence"] == "high"]
    rows = "".join(
        "<tr><td>%s</td><td>%s</td><td><strong>%s</strong><div class=\"small muted\">%s</div></td>"
        "<td>%s</td><td class=\"small\">%.1f%%</td><td class=\"small\">%s v %s</td>"
        "<td class=\"small\"><a href=\"%s\">official</a></td></tr>" % (
            badge(p["confidence"]), e(p["sport"]), e(p["selection"]), e(p["market"]),
            price(p["american_display"]), p["probability"] * 100, e(p["home"]), e(p["away"]),
            e(p["official_url"])) for p in inband)
    body = f"""
<p class="lede">The brief asks for high-confidence picks in the −250 to +10000 window. Those two rules pull in
opposite directions, and this page shows exactly where they meet.</p>
<div class="kpis">
  <div class="kpi"><b>{len(inband)}</b><span>picks inside the band</span></div>
  <div class="kpi"><b>{len(high_in)}</b><span>of them high confidence</span></div>
  <div class="kpi"><b>{picks['count'] - len(inband)}</b><span>picks outside the band</span></div>
  <div class="kpi"><b>71.4%</b><span>the chance −250 implies</span></div>
</div>
<div class="notice info">
<p><strong>The arithmetic.</strong> −250 is a decimal price of 1.40, which implies 71.43%. So a two-way
selection cannot be both "more than 70% likely" and "longer than −250" unless it sits between 70.0% and
71.43%. That is why the shortlist is full of alternate lines — puck lines, run lines, set handicaps and
totals — rather than short-priced favourites.</p>
<p><strong>What we did instead of fudging it.</strong> Every market for every fixture was originated, and the
pick for each fixture is the strongest <em>in-band</em> selection. A 78% favourite whose money line sits at
−355 is not published as a high-confidence pick; its handicap or total is, if that line is genuinely inside
the band.</p>
</div>
<h2>Everything inside the window</h2>
<div class="table-wrap"><table>
<thead><tr><th>Confidence</th><th>Sport</th><th>Selection</th><th>Our price</th><th>Chance</th><th>Match</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    return page("The −250 to +10000 board", body, "band.html",
                "Where the odds window and the confidence rule actually overlap.")


def build_sports_index(picks, preds, matches):
    cards = ""
    for slug, name in SPORTS:
        ms = [m for m in matches if m["sport"] == name]
        ps = [p for p in picks["picks"] if p["sport"] == name]
        ws = [p for p in preds["predictions"] if p["sport"] == name]
        cards += (f'<div class="card"><h3><a href="{slug}.html">{e(name)}</a></h3>'
                  f'<p>{len(ms)} fixtures · {len(ps)} picks · {len(ws)} write-ups</p></div>')
    body = f'<p class="lede">Fifteen categories, one page each, with that sport\'s fixtures, picks and write-ups.</p><div class="cards">{cards}</div>'
    return page("Sports", body, "sports", "Every covered sport, in the order the brief lists them.")


def build_sport(name, matches, picks, preds, lines, flags):
    ms = [m for m in matches if m["sport"] == name]
    ps = [p for p in picks["picks"] if p["sport"] == name]
    ws = [p for p in preds["predictions"] if p["sport"] == name]
    fl = [f for f in flags["items"] if f["sport"] in (name, "Multiple")]
    ls = [l for l in lines["lines"] if any(m["id"] == l["fixture_id"] for m in ms)]
    cap = picks["cap_reason"].get(name, "no cap: inputs are complete for this competition")
    frow_parts = []
    for m in ms:
        if m["pick"]:
            cell = ('<strong>%s</strong><div class="small muted">%s · %s</div>' % (
                e(m["pick"]["selection"]), e(m["pick"]["market"]), e(m["pick"]["american_display"])))
        else:
            cell = '<span class="muted">no line</span>'
            if m.get("blank_reason"):
                cell += '<div class="small muted">%s</div>' % e(m["blank_reason"])
        frow_parts.append(
            '<tr><td>%s</td><td>%s v %s</td><td class="small">%s<div class="muted">%s</div></td>'
            '<td>%s</td><td class="small"><a href="%s">official</a></td></tr>' % (
                human(m["start_utc"]), e(m["home"]), e(m["away"]), e(m["competition"]),
                e(m["venue"]), cell, e(m["official_url"])))
    frows = "".join(frow_parts)
    prows = "".join(
        f"<tr><td>{badge(p['confidence'])}</td><td>{e(p['selection'])}<div class=\"small muted\">{e(p['market'])}</div></td>"
        f"<td>{price(p['american_display'])}</td><td>{p['probability']*100:.1f}%</td></tr>" for p in ps)
    wblocks = "".join(
        f"<div class=\"pred\"><h3>{e(p['headline'])}</h3><p class=\"meta\">{badge(p['confidence'])} · "
        f"{human(p['start_utc'])}</p><div class=\"sel\">{e(p['selection'])} · {e(p['market'])} · "
        f"{price(p['american_display'])}</div><p class=\"body\">{e(p['text'])}</p>"
        f"<p class=\"small\"><a href=\"{e(p['official_url'])}\">Fixture source</a></p></div>" for p in ws)
    lrows = "".join(f"<tr><td>{e(l['market'])}</td><td>{e(l['selection'])}</td>"
                    f"<td>{l['probability']*100:.1f}%</td><td>{price(l['american_display'])}</td>"
                    f"<td>{'in band' if l['in_band'] else 'outside'}</td></tr>" for l in ls)
    flags_html = "".join(f"<li><strong>{e(f['id'])}</strong> — {e(f['title'])}</li>" for f in fl[:6])
    body = f"""
<p class="lede">{len(ms)} fixtures, {len(ps)} graded picks, {len(ws)} full write-ups and {len(ls)} originated
selections.</p>
<div class="notice info"><strong>Confidence ceiling for {e(name)}:</strong> {e(cap)}.</div>
<h2>Fixtures and picks</h2>
<div class="table-wrap"><table><thead><tr><th>Starts</th><th>Fixture</th><th>Competition and venue</th><th>Pick</th><th>Source</th></tr></thead>
<tbody>{frows}</tbody></table></div>
<h2>Graded selections</h2>
<div class="table-wrap"><table><thead><tr><th>Confidence</th><th>Selection</th><th>Our price</th><th>Chance</th></tr></thead>
<tbody>{prows}</tbody></table></div>
<h2>Written predictions</h2>
{wblocks or '<p class="muted">No write-up is published for this sport in this snapshot. The reason is on the Flagged for Review page.</p>'}
<h2>Every originated line</h2>
<div class="table-wrap"><table><thead><tr><th>Market</th><th>Selection</th><th>Chance</th><th>Our price</th><th>Band</th></tr></thead>
<tbody>{lrows}</tbody></table></div>
<h2>Review items touching this sport</h2>
<ul class="small">{flags_html or '<li>None.</li>'}</ul>
<p class="small"><a href="../flagged.html">All flagged items →</a></p>
"""
    return page(name, body, "sports", f"{name} at a glance.")


def build_sources(sources, fx):
    rows = "".join(f"<tr><td>{e(s['key'])}</td><td>{e(s['label'])}</td><td class=\"small\">{e(s['kind'])}</td>"
                   f"<td class=\"small\"><a href=\"{e(s['url'])}\">{e(s['url'])}</a></td></tr>"
                   for s in sources["sources"])
    used = {}
    for f in fx["fixtures"]:
        for fact in f["facts"]:
            used[fact["source_url"]] = used.get(fact["source_url"], 0) + 1
    urows = "".join(f"<tr><td class=\"small\"><a href=\"{e(u)}\">{e(u)}</a></td><td>{n}</td></tr>"
                    for u, n in sorted(used.items(), key=lambda kv: -kv[1]))
    body = f"""
<p class="lede">{sources['count']} official endpoints were read for this snapshot: governing bodies, leagues,
tours and the tournaments themselves. No aggregator, no mirror site and no bookmaker price feed.</p>
<div class="notice ok"><strong>Every fact has a URL.</strong> {sum(used.values())} per-fact citations resolve
to {len(used)} distinct official pages. Each is printed beside the claim it supports on the fixture and
prediction pages.</div>
<h2>Register</h2>
<div class="table-wrap"><table><thead><tr><th>Key</th><th>What it is</th><th>Type</th><th>URL</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>Citations by page</h2>
<div class="table-wrap"><table><thead><tr><th>Page</th><th>Facts cited from it</th></tr></thead>
<tbody>{urows}</tbody></table></div>
"""
    return page("Official sources", body, "sources.html",
                "The full register of official pages used in this snapshot.")


def src(value):
    """A repo-relative evidence path becomes a link that resolves from /clarity/."""
    if value.startswith("http"):
        return e(value)
    return e("../" + value)


def build_flagged(flags, matches, preds):
    blanks = [m for m in matches if m["status"] == "blank"]
    items = "".join(
        f"""<div class="card" style="margin:12px 0"><h3>{e(f['id'])} · {e(f['title'])}</h3>
<p class="small">{badge('high' if f['severity']=='high' else ('medium' if f['severity']=='medium' else 'low'))}
· {e(f['sport'])}</p><p>{e(f['detail'])}</p>
<p class="small"><a href="{src(f['source'])}">source</a></p></div>""" for f in flags["items"])
    brows = "".join(f"<tr><td><a href=\"{sport_href(m['sport'])}\">{e(m['sport'])}</a></td>"
                    f"<td>{e(m['home'])} v {e(m['away'])}</td><td class=\"small\">{e(m['blank_reason'])}</td>"
                    f"<td class=\"small\"><a href=\"{e(m['official_url'])}\">official</a></td></tr>" for m in blanks)
    body = f"""
<p class="lede">Nothing is hidden to make the numbers look better. This page lists every gap, every
assumption and every fixture that carries no line.</p>
<div class="kpis">
  <div class="kpi"><b>{flags['count']}</b><span>review items</span></div>
  <div class="kpi"><b>{flags['high']}</b><span>of them high severity</span></div>
  <div class="kpi"><b>{len(blanks)}</b><span>fixtures without a line</span></div>
  <div class="kpi"><b>{len([s for s in SPORTS if s[1] not in preds['by_sport']])}</b><span>sports without a write-up</span></div>
</div>
{items}
<h2>Fixtures published without a line</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Fixture</th><th>Why no line</th><th>Source</th></tr></thead>
<tbody>{brows}</tbody></table></div>
"""
    return page("Flagged for review", body, "flagged.html",
                "Gaps, assumptions and unreadable pages, published rather than smoothed over.")


def build_methodology(picks, fx):
    body = f"""
<p class="lede">Six steps, applied identically to every fixture. The chain never starts from a bookmaker
price.</p>
<h2>1. Discovery and listing cross-check</h2>
<p>The fifteen sports are taken from the brief. OLBG's own sport routes are recorded so the mapping is
auditable: Ice Hockey is OLBG id 13, Gaelic Football is 25 and Hurling is 26, and id 11 is American Football.
Every one of the fifteen hubs was read on 2026-10-24. OLBG is a listing source only.</p>
<h2>2. Fixture confirmation</h2>
<p>A fixture is published only when a governing body, league or tour page names both participants and a
start time or a scheduled round. The link on the row is that page. Where only one side is official (for
example the USA Eagles, whose squad was not published), the row is published with a stated blank.</p>
<h2>3. Inputs</h2>
<p>Only official numbers enter the pricing: records, goals or points for and against, games played, league
tables, match reports, published averages, semi-final times, practice times and scorelines. Where a number
could not be read, the fixture is blank rather than filled.</p>
<h2>4. Line origination</h2>
<table class="small"><thead><tr><th>Sport family</th><th>Transform</th></tr></thead><tbody>
<tr><td>Ice hockey</td><td>Shrunk multiplicative Poisson over a 0–16 goal grid; overtime and shootout split
from the tie mass; puck line from P(margin ≥ 2)</td></tr>
<tr><td>Baseball</td><td>Run expectancy from team runs per game blended with the announced starters' ERA and
WHIP; extra-inning tie mass split 52/48</td></tr>
<tr><td>Basketball</td><td>Win-rate logit with a three-win pseudo-count prior and a 0.22 home-court term, plus
1.6 points of margin per confirmed absence; normal margin and total</td></tr>
<tr><td>Rugby union</td><td>League-table attack and defence with shrinkage on games played, or points
difference per game where that is all the league publishes; normal margin and total</td></tr>
<tr><td>Rugby league</td><td>Round 1 winning margins damped into an expected points line (no per-team points
table is published in the World Cup match centre)</td></tr>
<tr><td>Cricket</td><td>Series win-loss differential into a logit; totals held at 50/50 where no venue par
exists</td></tr>
<tr><td>Darts, tennis, volleyball</td><td>Race-to-target state model, so every set or leg score is enumerated
and the handicap and total fall out of the same grid</td></tr>
<tr><td>Golf, F1, greyhounds</td><td>Outright fields priced from the leaderboard, the practice order and the
semi-final clock respectively</td></tr>
</tbody></table>
<h2>5. Confidence</h2>
<p>A selection is <strong>high</strong> when a two-way price is at least 60% at a price inside
−250…+10000, and the sport's inputs are complete. Outright fields are graded on their own scale, because a
30-runner field never produces a 60% favourite. Each sport then has a ceiling; the ceiling and its reason are
printed on the sport page and in <code>data/clarity/picks.json</code>.</p>
<h2>6. Prices</h2>
<p>Every published price is the reciprocal of the probability: decimal = 1/p, and the American figure follows
from that same rounded decimal, so the two always agree. There is no margin and no bookmaker input. A price of
−250 means we think the selection wins one time in 1.40.</p>
<h2>What would make this desk wrong</h2>
<p>Small samples, missing injury sheets, a client-rendered table, an unpublished average, or a fixture whose
start time was captured from a page that later changed. Each of those is named on the Flagged page rather than
buried.</p>
"""
    return page("Method", body, "methodology.html",
                "How a fixture becomes a priced selection.")


def build_olbg(olbg):
    hubs = "".join(f"<tr><td>{e(k)}</td><td>{v['sport_id']}</td><td class=\"small\">"
                   f"<a href=\"{e(v['url'])}\">{e(v['url'])}</a></td><td>{v['listed_events']}</td>"
                   f"<td class=\"small\">{e(v.get('note', ''))}</td></tr>" for k, v in olbg["olbg_hubs"].items())
    body = f"""
<p class="lede">What OLBG actually exposes, read first-hand on 2026-10-24 across all fifteen requested sports.</p>
<h2>Route schema</h2>
<p>Every sport is served at <code>/betting-tips/&lt;Sport&gt;/&lt;id&gt;</code>, and individual events at
<code>/betting-tips/&lt;Sport&gt;/&lt;Competition&gt;/&lt;Group&gt;/&lt;Home&gt;_v_&lt;Away&gt;/&lt;id&gt;?event_id=&lt;n&gt;</code>.
Event pages list markets as Money Line, Puck Line, Game Totals, Pointspread, Handicap, Win Match 2-way,
Total 180s, Most 180s, Handicap 2-way, Total Legs, Frame Betting, Top Team1 Batsman and Outright Winner.
A single event page can carry five or more markets, which is what makes the "investigate every market"
requirement tractable from OLBG's own vocabulary.</p>
<div class="notice warn"><strong>Two route traps.</strong> Ice Hockey is id <strong>13</strong>; id 11 is
American Football. Gaelic sports are split: Gaelic Football is <strong>25</strong> and Hurling is
<strong>26</strong>. A layer that uses 11 for hockey, or that assumes one Gaelic route, is wrong.</div>
<h2>The fifteen hubs, as read</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>OLBG id</th><th>Hub</th><th>Listed events seen</th><th>Note</th></tr></thead>
<tbody>{hubs}</tbody></table></div>
<h2>Defects that change how OLBG can be used</h2>
<ol>
<li><strong>Times are US Eastern.</strong> A handball fixture OLBG lists as "Today 14:00" is 20:00 CEST on
the league's own page. Six hours, every row.</li>
<li><strong>Prices are blank on some event pages.</strong> The NHL event page for Carolina at St. Louis
renders "WIN @" with no number after it, while the tip counts render normally.</li>
<li><strong>"No tips found."</strong> The golf hub returned that string on a day a PGA TOUR event was in
progress, so a listing-driven desk would conclude golf has no fixtures.</li>
<li><strong>Outright-only sports.</strong> Rugby League returned three 2027 futures and no match market.</li>
<li><strong>Tip share is not a probability.</strong> "15/26 Win Tips 58%" is the share of tipsters, not a
chance of winning, and it is not used as a pricing input here.</li>
</ol>
<h2>How this desk uses OLBG</h2>
<p>As a cross-check that a fixture is being offered to bettors, and as the source of the event URL printed on
rows that have one. Never as a price, never as a probability, and never as a substitute for a governance
source.</p>
"""
    return page("OLBG reverse engineering", body, "olbg.html",
                "The route schema, market vocabulary and defects, read first-hand.")


def build_repo_review(audit):
    cards = ""
    for f in audit["findings"]:
        ev = json.dumps(f["evidence"], indent=1)[:1200]
        cards += f"""<div class="card" style="margin:12px 0"><h3>{e(f['id'])} · {e(f['title'])}</h3>
<p class="small">{badge('high' if f['severity']=='high' else ('medium' if f['severity']=='medium' else 'low'))}</p>
<p>{e(f['detail'])}</p>
<details><summary>Evidence</summary><pre class="small" style="white-space:pre-wrap">{e(ev)}</pre></details>
<p class="small"><strong>Action:</strong> {e(f['action'])}</p></div>"""
    body = f"""
<p class="lede">A line-by-line scan of the checkout this desk was built into, produced by a script so it can
be re-run. {audit['count']} findings across {audit['layers']} published dashboards.</p>
<div class="notice info"><strong>Scope.</strong> This session owns only <code>/clarity/</code>,
<code>data/clarity/</code>, <code>scripts/clarity_*.py</code>, one test module, one research note and
append-only edits to COORDINATION.md. Every finding below is in another session's files and is reported,
not edited.</div>
{cards}
"""
    return page("Repository review", body, "repo-review.html",
                "The repo audited with the same standard as the data.")


def main() -> int:
    fx = load("fixtures.json")
    matches_doc = load("matches.json")
    matches = matches_doc["matches"]
    picks = load("picks.json")
    preds = load("predictions.json")
    lines = load("lines.json")
    sources = load("sources.json")
    flags = load("flagged.json")
    audit = load("repo_audit.json")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(css().strip() + "\n", encoding="utf-8")

    (OUT / "index.html").write_text(build_index(fx, matches, picks, preds, flags), encoding="utf-8")
    (OUT / "picks.html").write_text(build_picks(picks, preds), encoding="utf-8")
    (OUT / "predictions.html").write_text(build_predictions(preds, picks), encoding="utf-8")
    (OUT / "matches.html").write_text(build_matches(matches), encoding="utf-8")
    (OUT / "lines.html").write_text(build_lines(lines, matches), encoding="utf-8")
    (OUT / "band.html").write_text(build_band(picks), encoding="utf-8")
    (OUT / "sports" / "index.html").write_text(build_sports_index(picks, preds, matches), encoding="utf-8")
    (OUT / "sources.html").write_text(build_sources(sources, fx), encoding="utf-8")
    (OUT / "flagged.html").write_text(build_flagged(flags, matches, preds), encoding="utf-8")
    (OUT / "methodology.html").write_text(build_methodology(picks, fx), encoding="utf-8")
    (OUT / "olbg.html").write_text(build_olbg(fx if "olbg_hubs" in fx else fx), encoding="utf-8")
    (OUT / "repo-review.html").write_text(build_repo_review(audit), encoding="utf-8")
    for slug, name in SPORTS:
        (OUT / "sports" / f"{slug}.html").write_text(
            build_sport(name, matches, picks, preds, lines, flags), encoding="utf-8")
    pages = len(list(OUT.rglob("*.html")))
    print(f"clarity_build: {pages} HTML pages, {len(matches)} fixtures, {picks['count']} picks, "
          f"{preds['count']} predictions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
