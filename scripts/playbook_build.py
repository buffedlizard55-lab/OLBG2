#!/usr/bin/env python3
"""Playbook build: render the desk and the root front door as static HTML."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "playbook"
OUT = ROOT / "playbook"

SPORT_ORDER = ["Ice Hockey", "Basketball", "Tennis", "Cricket", "Volleyball", "Handball",
               "Rugby Union", "Baseball", "Gaelic Sports", "Darts", "Greyhounds",
               "Golf", "Snooker", "Motor Racing", "Rugby League"]
SPORT_SLUG = {"Ice Hockey": "ice-hockey", "Basketball": "basketball", "Tennis": "tennis",
              "Cricket": "cricket", "Volleyball": "volleyball", "Handball": "handball",
              "Rugby Union": "rugby-union", "Baseball": "baseball", "Gaelic Sports": "gaelic-sports",
              "Darts": "darts", "Greyhounds": "greyhounds", "Golf": "golf", "Snooker": "snooker",
              "Motor Racing": "motor-racing", "Rugby League": "rugby-league"}
NO_EVENTS = {
    "Golf": "OLBG returned \"No tips found.\" on the Golf hub at 22:44 UTC. No tournament, no fixture, nothing to price.",
    "Snooker": "OLBG returned \"No tips found.\" on the Snooker hub. The one match listed earlier in the evening had gone off.",
    "Motor Racing": "OLBG returned \"No tips found.\" on the Motor Racing hub. The United States Grand Prix card had come down.",
    "Rugby League": "OLBG listed no match at all, only three 2027 season outrights.",
}

CSS = """
:root{--ink:#0f172a;--muted:#5b6779;--line:#e3e8ef;--bg:#f6f8fb;--card:#fff;--accent:#0f766e;
--accent2:#0b5c56;--hi:#047857;--med:#b45309;--low:#64748b;--warn:#b91c1c;--chip:#eef2f7}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent2)}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
header.top{background:var(--ink);color:#fff}
header.top .wrap{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;padding:12px 18px}
.brand{font-weight:700;color:#fff;text-decoration:none;font-size:17px}
.brand span{color:#5eead4}
nav.top a{color:#cbd5e1;text-decoration:none;margin-left:14px;font-size:14px}
nav.top a.on,nav.top a:hover{color:#fff}
main{padding:26px 0 70px}
h1{font-size:30px;line-height:1.2;margin:0 0 8px}
h2{font-size:21px;margin:34px 0 10px}
h3{font-size:17px;margin:22px 0 8px}
p.lede{font-size:17px;color:var(--muted);max-width:840px;margin:0 0 18px}
.eyebrow{text-transform:uppercase;letter-spacing:.09em;font-size:11.5px;color:var(--muted);font-weight:700;margin:0 0 6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi .v{font-size:26px;font-weight:750;line-height:1}
.kpi .k{font-size:12.5px;color:var(--muted);margin-top:5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
.pickgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.pick{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fff;border-left:5px solid var(--hi)}
.pick.med{border-left-color:var(--med)}.pick.low{border-left-color:var(--low)}
.pick .head{display:flex;justify-content:space-between;gap:8px;font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:700}
.pick .match{font-weight:700;margin:7px 0 2px}
.pick .sel{font-size:18px;font-weight:750;color:var(--accent2);margin:4px 0}
.pick .meta{font-size:13.5px;color:var(--muted)}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11.5px;font-weight:700;letter-spacing:.03em}
.b-high{background:#d1fae5;color:#065f46}.b-medium{background:#fef3c7;color:#92400e}.b-low{background:#e2e8f0;color:#475569}
.b-band{background:#dbeafe;color:#1e40af}.b-out{background:#fee2e2;color:#991b1b}
.b-A{background:#dcfce7;color:#166534}.b-B{background:#f1f5f9;color:#475569}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f1f5f9;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#475569}
tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl-wrap{overflow-x:auto;border-radius:10px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.chips a.pickcard{border:1px solid var(--border);background:#fff;border-radius:999px;padding:.3rem .7rem;font-size:.82rem;color:var(--ink);text-decoration:none;display:inline-block}
.chips a.pickcard:hover{border-color:var(--accent);color:var(--accent)}
.chip{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:6px 12px;font-size:13.5px;text-decoration:none;color:var(--ink)}
.chip b{color:var(--accent2)}
.note{font-size:13.5px;color:var(--muted)}
.warn{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:12px 14px;font-size:14px}
ul.tight{margin:8px 0;padding-left:20px}ul.tight li{margin:4px 0}
.pred{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
.pred h3{margin:0 0 6px;font-size:17px}
.pred .top{display:flex;flex-wrap:wrap;gap:10px;align-items:center;font-size:12.5px;color:var(--muted);margin-bottom:8px}
.pred .body{font-size:15.5px}
.pred .facts{margin:12px 0 0;padding:10px 12px;background:#f8fafc;border:1px dashed var(--line);border-radius:8px;font-size:13px}
.pred .facts li{margin:3px 0}
footer{border-top:1px solid var(--line);padding:22px 0 50px;color:var(--muted);font-size:13.5px}
.src{font-size:12.5px;word-break:break-all}
""".strip()


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def money(p) -> str:
    if p is None:
        return "—"
    return f"+{p}" if p > 0 else str(p)


def pct(p) -> str:
    return "—" if p is None else f"{p * 100:.1f}%"


def badge(conf) -> str:
    return f'<span class="badge b-{conf}">{conf}</span>'


def band_badge(ok) -> str:
    return '<span class="badge b-band">in band</span>' if ok else '<span class="badge b-out">outside band</span>'


def tier_badge(t) -> str:
    label = "official stats" if t == "A" else "OLBG board"
    return f'<span class="badge b-{t}" title="{"governing-body statistics" if t == "A" else "OLBG published tip share"}">{label}</span>'


def best_cell(best) -> str:
    if not best:
        return '<span class="note">no pick</span>'
    return (esc(best["selection"]) + '<div class="note">' + money(best["price"]) +
            " · " + best["confidence"] + "</div>")


def src_cell(f) -> str:
    url = f.get("source_url") or f["olbg_url"]
    if not url:
        return "not listed"
    return '<a href="' + esc(url) + '">' + esc(f.get("source_label") or "OLBG") + "</a>"



def previous_desk_cards(n: int = 3) -> str:
    """Three still-open calls from the /now/ desk, kept on the front door for continuity.

    The /now/ verifier pins its own cards on the root index; this keeps that contract while the
    front door itself belongs to this desk.
    """
    try:
        preds = json.loads((ROOT / "data" / "now" / "predictions.json").read_text())["predictions"]
        picks = {p["id"]: p for p in json.loads((ROOT / "data" / "now" / "picks.json").read_text())["picks"]}
        as_of = json.loads((ROOT / "data" / "now" / "picks.json").read_text())["as_of_utc"]
    except (OSError, KeyError, ValueError):
        return ""
    cards = []
    for p in preds:
        pick = picks.get(p.get("pick_id"))
        if not pick or pick.get("started") or (pick.get("start_utc") or "") <= as_of:
            continue
        cards.append(f'<a class="pickcard" href="now/predictions.html#{esc(p["id"])}">'
                     f'{esc(pick["selection"])} <b>{money(pick["american"])}</b></a>')
        if len(cards) == n:
            break
    return ('<h2>Also open on the previous board</h2>\n<p class="note">The 24 October <a href="now/index.html">/now/</a> '
            'desk is superseded by this one but stays published, and three of its calls have not started.</p>\n'
            '<div class="chips">' + "".join(cards) + "</div>\n") if cards else ""

def page(title: str, active: str, body: str, root: str = "") -> str:
    nav = [("index.html", "Overview"), ("picks.html", "Picks"), ("predictions.html", "Predictions"),
           ("matches.html", "All matches"), ("lines.html", "Our lines"),
           ("sports/index.html", "Sports"), ("sources.html", "Sources"),
           ("methodology.html", "Method"), ("flagged.html", "Flagged")]
    links = "".join(
        f'<a class="{"on" if h == active else ""}" href="{root}{h}">{esc(l)}</a>' for h, l in nav)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{root}assets/style.css">
</head><body>
<header class="top"><div class="wrap"><a class="brand" href="{root}index.html">OLBG <span>Playbook</span></a>
<nav class="top">{links}</nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p><b>What this desk is.</b> A read of the matches OLBG listed across fifteen sports on the evening of
24 October 2026, with a price this desk originated for each match it could price, a confidence grade, and a written
preview where the evidence carried one. Every row links to the page it came from, and every fact in a preview links
to the page it was read from.</p>
<p>Prices on this desk are ours, not OLBG's: OLBG does not serve bookmaker prices to this location. Nothing here is a
tip to follow blindly. 18+. <a href="{root}methodology.html">How the prices and grades are made</a> ·
<a href="{root}flagged.html">What we could not confirm</a> · <a href="{root}../archive.html">Earlier desks</a></p>
</div></footer></body></html>"""


def pick_card(p, root="") -> str:
    cls = {"high": "", "medium": " med", "low": " low"}[p["confidence"]]
    anchor = p["pick_id"]
    return (f'<div class="pick{cls}" id="{esc(anchor)}"><div class="head"><span>{esc(p["sport"])} · '
            f'{esc(p["competition"])}</span>{badge(p["confidence"])}</div>'
            f'<div class="match">{esc(p["event"])}</div>'
            f'<div class="sel">{esc(p["selection"])}</div>'
            f'<div class="meta">{esc(p["market"])} · our price <b>{money(p["price"])}</b> · chance {pct(p["probability"])}'
            f' · {band_badge(p["in_band"])} · {esc(p["day"])}</div></div>')


def write_front_door() -> str:
    """Write the root index.html.

    The owner asked for one obvious front door, so this desk owns it. build_site.py calls this
    as well, which means every builder that touches the root writes the same bytes and the
    order the layers are rebuilt in cannot change the published page.
    """
    fixtures_doc = json.loads((DATA / "fixtures.json").read_text())
    picks_doc = json.loads((DATA / "picks.json").read_text())
    preds_doc = json.loads((DATA / "predictions.json").read_text())
    lines_doc = json.loads((DATA / "lines.json").read_text())
    sources_doc = json.loads((DATA / "sources.json").read_text())
    flags = json.loads((DATA / "flagged.json").read_text())["flags"]
    picks = picks_doc["picks"]
    all_sel = [s for l in lines_doc["lines"] for s in l["lines"]]
    short = [s for s in all_sel if s["probability"] >= 0.70]
    short_in = [s for s in short if s["in_band"]]
    in_band_all = [s for s in all_sel if s["in_band"]]
    big = picks_doc["count"]
    hi = picks_doc["by_confidence"]["high"]
    by_sport_fx = {}
    for f in fixtures_doc["fixtures"]:
        by_sport_fx.setdefault(f["sport"], []).append(f)
    banded = sorted([p for p in picks if p["in_band"]], key=lambda x: -x["probability"])[:8]
    root_picks = [p for p in picks if p["confidence"] == "high"][:3] or banded[:3]

    root_picks = [p for p in picks if p["confidence"] == "high"][:3] or banded[:3]
    front = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OLBG Playbook — 15 sports, our own prices, {big} graded picks</title>
<meta name="description" content="Sunday 25 October 2026: {fixtures_doc['match_count']} OLBG matches across 15 sports, {len(all_sel)} prices originated here, {big} graded picks and {preds_doc['count']} written previews.">
<link rel="stylesheet" href="playbook/assets/style.css">
</head><body>
<header class="top"><div class="wrap"><a class="brand" href="index.html">OLBG <span>Playbook</span></a>
<nav class="top"><a class="on" href="index.html">Overview</a><a href="playbook/picks.html">Picks</a>
<a href="playbook/predictions.html">Predictions</a><a href="playbook/matches.html">All matches</a>
<a href="playbook/sports/index.html">Sports</a><a href="playbook/flagged.html">Flagged</a></nav></div></header>
<main><div class="wrap">
<p class="eyebrow">Desk snapshot 24 October 2026, 22:50 UTC · fifteen sports</p>
<h1>{fixtures_doc['match_count']} OLBG matches, {len(all_sel)} prices of our own, {big} graded picks.</h1>
<p class="lede">This is the only page you need to start from. Everything below is a link into the desk:
<a href="playbook/picks.html"><b>Picks</b></a> is the full table of graded selections,
<a href="playbook/predictions.html"><b>Predictions</b></a> holds the {preds_doc['count']} written previews, and
<a href="playbook/sports/index.html"><b>Sports</b></a> splits it fifteen ways.</p>

<div class="kpis">
  <div class="kpi"><div class="v">{fixtures_doc['match_count']}</div><div class="k">matches on OLBG</div></div>
  <div class="kpi"><div class="v">{big}</div><div class="k">graded picks</div></div>
  <div class="kpi"><div class="v">{hi}</div><div class="k">high confidence</div></div>
  <div class="kpi"><div class="v">{preds_doc['count']}</div><div class="k">written previews</div></div>
  <div class="kpi"><div class="v">{sources_doc['count']}</div><div class="k">sources linked</div></div>
</div>

<h2>Today's strongest calls</h2>
<div class="pickgrid">{''.join(pick_card(p) for p in root_picks)}</div>
<p class="note"><a href="playbook/picks.html">All {big} picks, with price, chance, band and source on every row →</a></p>

<h2>What is on the desk</h2>
<div class="tbl-wrap"><table>
<tr><th>Page</th><th>What is on it</th></tr>
<tr><td><a href="playbook/picks.html"><b>Picks</b></a></td><td>{big} graded selections, one row each, with the band test and the source.</td></tr>
<tr><td><a href="playbook/predictions.html"><b>Predictions</b></a></td><td>{preds_doc['count']} written previews, {preds_doc['min_words']} words at the shortest, each with its facts and links.</td></tr>
<tr><td><a href="playbook/matches.html"><b>All matches</b></a></td><td>Every event OLBG listed across the fifteen sports, plus the outrights kept separately.</td></tr>
<tr><td><a href="playbook/lines.html"><b>Our lines</b></a></td><td>{len(all_sel)} prices, match by match, with the chance behind each one.</td></tr>
<tr><td><a href="playbook/sports/index.html"><b>Sports</b></a></td><td>One page per sport: matches, picks, prices and previews together.</td></tr>
<tr><td><a href="playbook/sources.html"><b>Sources</b></a></td><td>{sources_doc['count']} links: governing bodies, OLBG hubs, OLBG event pages.</td></tr>
<tr><td><a href="playbook/methodology.html"><b>Method</b></a></td><td>How each price and each grade was made, including the band problem.</td></tr>
<tr><td><a href="playbook/flagged.html"><b>Flagged</b></a></td><td>{len(flags)} open items and every blank value, with the reason.</td></tr>
</table></div>

<h2>Where the confidence sits</h2>
<p class="note">{hi} high, {picks_doc['by_confidence']['medium']} medium and {picks_doc['by_confidence']['low']} low.
A price of −250 is a 71.4% chance, so a "70% or better" rule and a "−250 or longer" rule overlap only inside a
1.4-point window: {len(short)} of {len(all_sel)} prices cleared 70%, {len(in_band_all)} sat in the band, and
{len(short_in)} did both. The full explanation is on <a href="playbook/methodology.html">Method</a>.</p>

<div class="chips">{''.join(f'<a class="chip" href="playbook/sports/{SPORT_SLUG[s]}.html"><b>{esc(s)}</b> · {len(by_sport_fx.get(s, []))}</a>' for s in SPORT_ORDER)}</div>

{previous_desk_cards()}
<p class="note" style="margin-top:26px">Earlier desks are preserved exactly as they were published and listed on
<a href="archive.html">the archive page</a>. Nothing on them was deleted or rewritten.</p>
</div></main>
<footer><div class="wrap"><p>Prices are ours, not OLBG's, and are published for study rather than as advice. 18+.
<a href="playbook/flagged.html">Flagged for review</a> · <a href="archive.html">Archive</a></p></div></footer>
</body></html>"""
    (ROOT / "index.html").write_text(front)
    return front

def main() -> None:
    fixtures_doc = json.loads((DATA / "fixtures.json").read_text())
    picks_doc = json.loads((DATA / "picks.json").read_text())
    preds_doc = json.loads((DATA / "predictions.json").read_text())
    lines_doc = json.loads((DATA / "lines.json").read_text())
    sources_doc = json.loads((DATA / "sources.json").read_text())
    flags_doc = json.loads((DATA / "flagged.json").read_text())
    outrights_doc = json.loads((DATA / "outrights.json").read_text())

    fixtures = fixtures_doc["fixtures"]
    picks = picks_doc["picks"]
    preds = preds_doc["predictions"]
    lines = {l["fid"]: l for l in lines_doc["lines"]}
    flags = flags_doc["flags"]
    outrights = outrights_doc["outrights"]

    OUT.mkdir(exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS + "\n")

    # ---------------------------------------------------------------- band analysis
    all_sel = [s for l in lines_doc["lines"] for s in l["lines"]]
    short = [s for s in all_sel if s["probability"] >= 0.70]
    short_in = [s for s in short if s["in_band"]]
    in_band_all = [s for s in all_sel if s["in_band"]]
    big = picks_doc["count"]
    hi = picks_doc["by_confidence"]["high"]

    by_sport_preds = {}
    for p in preds:
        by_sport_preds.setdefault(p["sport"], []).append(p)
    by_sport_picks = {}
    for p in picks:
        by_sport_picks.setdefault(p["sport"], []).append(p)
    by_sport_fx = {}
    for f in fixtures:
        by_sport_fx.setdefault(f["sport"], []).append(f)

    # ------------------------------------------------------------------- overview
    highs = [p for p in picks if p["confidence"] == "high"]
    banded = sorted([p for p in picks if p["in_band"]], key=lambda x: -x["probability"])[:8]
    next_in_band = [p for p in picks if p["in_band"] and p["confidence"] != "high"]
    next_in_band = sorted(next_in_band, key=lambda x: -x["probability"])[:8]
    in_band_total = sum(1 for p in picks if p["in_band"])
    nxt = sorted([p for p in picks if p["day"] == "2026-10-25"], key=lambda x: -x["probability"])[:6]

    overview = f"""
<p class="eyebrow">Snapshot 24 October 2026, 22:50 UTC · desk covers 24–31 October</p>
<h1>Every match OLBG lists, priced by us, graded, and written up.</h1>
<p class="lede">Fifteen sports. {fixtures_doc['match_count']} matches read straight off OLBG's own event list,
{len(all_sel)} prices originated here, {big} graded picks and {preds_doc['count']} written previews.
Start with the picks below. The full tables are one click away in the navigation bar.</p>

<div class="kpis">
  <div class="kpi"><div class="v">{fixtures_doc['match_count']}</div><div class="k">matches on OLBG</div></div>
  <div class="kpi"><div class="v">{len(all_sel)}</div><div class="k">prices we originated</div></div>
  <div class="kpi"><div class="v">{big}</div><div class="k">graded picks</div></div>
  <div class="kpi"><div class="v">{hi}</div><div class="k">high confidence</div></div>
  <div class="kpi"><div class="v">{preds_doc['count']}</div><div class="k">written previews</div></div>
  <div class="kpi"><div class="v">{sources_doc['count']}</div><div class="k">sources linked</div></div>
</div>

<div class="card">
<p class="eyebrow">Where the picks are</p>
<p style="margin:0 0 10px">Picks live on <a href="picks.html"><b>Picks</b></a> and every one of them is also printed on its
sport page under <a href="sports/index.html"><b>Sports</b></a>. Each pick links straight to the written preview where
one exists. The reasoning behind the price is on <a href="lines.html"><b>Our lines</b></a>. Anything we could not
confirm is on <a href="flagged.html"><b>Flagged</b></a>, never in the tables.</p>
</div>

<h2>The highest-confidence calls</h2>
<p class="note">High confidence here means three things at once: an official league input behind the price, a modelled
chance of 65% or better, and a price inside the requested −250 to +10000 band. {hi} calls clear all three.</p>
<div class="pickgrid">{''.join(pick_card(p) for p in highs)}</div>

<h2>The best in-band picks</h2>
<p class="note">Ranked by our chance of winning, showing only prices that sit inside −250 to +10000.
{in_band_total} of {big} picks are inside the band. Read the preview on each one before you treat it as a bet.</p>
<div class="pickgrid">{''.join(pick_card(p) for p in next_in_band)}</div>

<h2>Sunday 25 October at a glance</h2>
<div class="tbl-wrap"><table>
<tr><th>Match</th><th>Sport</th><th>Our pick</th><th class="num">Price</th><th class="num">Chance</th><th>Grade</th></tr>
{''.join(f'<tr><td>{esc(p["event"])}</td><td>{esc(p["sport"])}</td><td><b>{esc(p["selection"])}</b></td>'
         f'<td class="num">{money(p["price"])}</td><td class="num">{pct(p["probability"])}</td><td>{badge(p["confidence"])}</td></tr>'
         for p in nxt)}
</table></div>

<h2>What the −250 to +10000 band does to the brief</h2>
<div class="card">
<p>This is the finding that shaped the desk, so it is on the front page rather than buried.</p>
<ul class="tight">
<li>Across the whole capture, <b>{len(short)}</b> of the {len(all_sel)} selections we priced carry a chance of 70% or
better.</li>
<li><b>{len(in_band_all)}</b> of the {len(all_sel)} sit inside the −250 to +10000 band.</li>
<li><b>{len(short_in)}</b> sit in both. A price of −250 is a 71.4% chance, so "70% or better" and "no shorter than
−250" can only ever overlap across a 1.4-point window.</li>
</ul>
<p class="note" style="margin-bottom:0">That is why the high-confidence label on this desk asks for evidence as well as
probability, and why the picks page shows the band as its own column instead of pretending the two rules always agree.</p>
</div>

<h2>Where each sport stands</h2>
<div class="chips">
{''.join(f'<a class="chip" href="sports/{SPORT_SLUG[s]}.html"><b>{esc(s)}</b> · {len(by_sport_fx.get(s, []))} matches · '
         f'{len(by_sport_picks.get(s, []))} picks</a>' for s in SPORT_ORDER)}
</div>
<p class="note">{len(NO_EVENTS)} sports had nothing to price. Each is named with its reason on the sport page and on
<a href="flagged.html">Flagged</a>; none of them was filled in.</p>
"""
    (OUT / "index.html").write_text(page("OLBG Playbook — Sunday 25 October 2026 picks desk", "index.html", overview))

    # ---------------------------------------------------------------------- picks
    rows = []
    for p in picks:
        pred = next((x for x in preds if x["fid"] == p["fid"] and x["selection"] == p["selection"]), None)
        link = f'<a href="predictions.html#{pred["pid"]}">preview</a>' if pred else '<span class="note">—</span>'
        rows.append(
            f'<tr><td>{esc(p["sport"])}</td><td>{esc(p["event"])}<div class="note">{esc(p["competition"])}</div></td>'
            f'<td>{esc(p["day"])}<div class="note">{esc((p.get("start_utc") or "")[11:16])} UTC</div></td>'
            f'<td><b>{esc(p["selection"])}</b></td><td>{esc(p["market"])}</td>'
            f'<td class="num">{money(p["price"])}</td><td class="num">{pct(p["probability"])}</td>'
            f'<td>{badge(p["confidence"])}</td><td>{band_badge(p["in_band"])}</td><td>{tier_badge(p["tier"])}</td>'
            f'<td>{link}</td><td class="src"><a href="{esc(p["source_url"])}">{esc(p.get("source_label", "OLBG"))}</a></td></tr>')

    picks_body = f"""
<p class="eyebrow">Picks · {big} selections</p>
<h1>Every graded pick, in one table.</h1>
<p class="lede">One row per pick. The selection is bold. Our price and our chance sit beside it, then the confidence
grade, whether the price is inside the requested band, and what the price was built from. The last column links to
OLBG's own page for the match.</p>
<div class="kpis">
  <div class="kpi"><div class="v">{hi}</div><div class="k">high</div></div>
  <div class="kpi"><div class="v">{picks_doc['by_confidence']['medium']}</div><div class="k">medium</div></div>
  <div class="kpi"><div class="v">{picks_doc['by_confidence']['low']}</div><div class="k">low</div></div>
  <div class="kpi"><div class="v">{picks_doc['in_band']}</div><div class="k">inside the band</div></div>
  <div class="kpi"><div class="v">{picks_doc['by_tier']['A']}</div><div class="k">backed by league stats</div></div>
</div>
<h2>By sport</h2>
<div class="chips">{''.join(f'<a class="chip" href="sports/{SPORT_SLUG[s]}.html"><b>{esc(s)}</b> · {len(by_sport_picks.get(s, []))}</a>' for s in SPORT_ORDER)}</div>
<h2>The table</h2>
<div class="tbl-wrap"><table>
<tr><th>Sport</th><th>Match</th><th>OLBG day</th><th>Selection</th><th>Market</th><th class="num">Our price</th>
<th class="num">Our chance</th><th>Confidence</th><th>Band</th><th>Built from</th><th>Preview</th><th>Source</th></tr>
{''.join(rows)}
</table></div>
<p class="note">A price shown in red is outside the −250 to +10000 band the brief asked for. It is still published so
the slate is complete, and it is never counted as a high-confidence call unless the band test passes.</p>
"""
    (OUT / "picks.html").write_text(page("Picks — OLBG Playbook", "picks.html", picks_body))

    # ---------------------------------------------------------------- predictions
    blocks = []
    for sport in SPORT_ORDER:
        group = by_sport_preds.get(sport, [])
        if not group:
            continue
        blocks.append(f'<h2 id="{SPORT_SLUG[sport]}">{esc(sport)} <span class="note">({len(group)} written previews)</span></h2>')
        for p in group:
            facts = "".join(f'<li>{esc(f["label"])}: <b>{esc(f["value"])}</b> — '
                            f'<a class="src" href="{esc(f["source"])}">source</a></li>' for f in p["facts"])
            blocks.append(f"""<article class="pred" id="{p['pid']}">
<div class="top"><span class="badge b-{p['confidence']}">{p['confidence']}</span>
<span>{esc(p['competition'])}</span><span>{esc(p['day'])}</span>
<span>{tier_badge(p['evidence_tier'])}</span>{band_badge(p['in_band'])}</div>
<h3>{esc(p['event'])} — <span style="color:#0b5c56">{esc(p['selection'])}</span></h3>
<p class="note" style="margin:0 0 8px">{esc(p['market'])} · our price <b>{money(p['price'])}</b> ·
our chance {pct(p['probability'])} · {p['words']} words</p>
<p class="body">{esc(p['text'])}</p>
<div class="facts"><b>What the preview rests on</b><ul class="tight">{facts}</ul>
<p style="margin:8px 0 0"><a href="{esc(p['source_url'])}">{esc(p.get('source_label', 'OLBG'))} event page</a></p></div>
</article>""")

    pred_body = f"""
<p class="eyebrow">Written previews · {preds_doc['count']}</p>
<h1>{preds_doc['count']} unique previews, {preds_doc['min_words']} words at the shortest.</h1>
<p class="lede">One preview for each short-listed selection, grouped by sport. Each one names the selection in the heading, states the price
and the chance, makes the case in a paragraph, and then lists the facts it rests on with a link to where each fact was
read. Sports with fewer than five are named on <a href="flagged.html">Flagged</a> with the reason.</p>
<div class="chips">{''.join(f'<a class="chip" href="#{SPORT_SLUG[s]}"><b>{esc(s)}</b> · {len(by_sport_preds.get(s, []))}</a>' for s in SPORT_ORDER if by_sport_preds.get(s))}</div>
{''.join(blocks)}
"""
    (OUT / "predictions.html").write_text(page("Predictions — OLBG Playbook", "predictions.html", pred_body))

    # -------------------------------------------------------------------- matches
    mrows = []
    for sport in SPORT_ORDER:
        group = sorted(by_sport_fx.get(sport, []), key=lambda f: (f["olbg_day"] or "", f["event"]))
        if not group:
            mrows.append(f'<tr><td>{esc(sport)}</td><td colspan="7" class="note">{esc(NO_EVENTS.get(sport, "No event listed."))}</td></tr>')
            continue
        for f in group:
            picks_here = [p for p in picks if p["fid"] == f["fid"]]
            best = max(picks_here, key=lambda x: x["probability"]) if picks_here else None
            n_lines = len(lines.get(f["fid"], {}).get("lines", []))
            link = (f'<a href="{esc(f.get("source_url") or f["olbg_url"])}">{esc(f.get("source_label") or "OLBG")} event</a>' if f["olbg_url"]
                    else '<span class="note">not on OLBG</span>')
            mrows.append(
                f'<tr><td>{esc(sport)}</td><td>{esc(f["competition"])}</td><td>{esc(f["event"])}</td>'
                f'<td>{esc(f["olbg_day"] or "—")}<div class="note">OLBG: {esc(f["olbg_display"] or "—")}</div></td>'
                f'<td class="num">{n_lines}</td>'
                f'<td>{best_cell(best)}</td>'
                f'<td>{tier_badge(f["tier"])}</td><td>{link}</td></tr>')

    match_body = f"""
<p class="eyebrow">All matches · {fixtures_doc['match_count']} on OLBG, {len(fixtures)} in the set</p>
<h1>Everything OLBG listed, sport by sport.</h1>
<p class="lede">The day is OLBG's own, as printed on the card. The clock string beside it is OLBG's too, shown exactly
as it rendered. Start times we could read from a governing body are on the fixture row of
<a href="lines.html">Our lines</a>; where we could not read one it is left blank and flagged.</p>
<div class="tbl-wrap"><table>
<tr><th>Sport</th><th>Competition</th><th>Match</th><th>Day</th><th class="num">Our prices</th><th>Best pick</th>
<th>Price built from</th><th>Source</th></tr>
{''.join(mrows)}
</table></div>
<h2>Season outrights, kept out of the match count</h2>
<p class="note">OLBG lists these long-range markets alongside the fixtures. They are not matches, so they are here
rather than in the table above, which is why the match total is not inflated.</p>
<div class="tbl-wrap"><table>
<tr><th>Sport</th><th>Market</th><th>OLBG's tipped selection</th><th class="num">Tips</th><th>OLBG date</th><th>Source</th></tr>
{''.join(f'<tr><td>{esc(o["sport"])}</td><td>{esc(o["event"])} — {esc(o["market"])}</td><td>{esc(o["tipped_selection"])}</td>'
         f'<td class="num">{o["tips_won"]}/{o["tips_total"]}</td><td>{esc(o["olbg_display"])}</td>'
         f'<td class="src"><a href="{esc(o.get("source_url") or o["olbg_url"])}">OLBG</a></td></tr>' for o in outrights)}
</table></div>
"""
    (OUT / "matches.html").write_text(page("All matches — OLBG Playbook", "matches.html", match_body))

    # ---------------------------------------------------------------------- lines
    lrows = []
    for l in sorted(lines_doc["lines"], key=lambda x: (x["day"] or "", x["sport"], x["event"])):
        n_fx = len(l["lines"])
        detail = "".join(
            f'<tr><td><span class="note">{esc(s["market"])}</span></td><td>{esc(s["selection"])}</td>'
            f'<td class="num">{pct(s["probability"])}</td><td class="num">{money(s["price"])}</td>'
            f'<td>{band_badge(s["in_band"])}</td>'
            f'<td class="src"><a href="{esc(l.get("source_url") or l["olbg_url"] or "#")}">{esc(l.get("source_label") or "OLBG")}</a></td></tr>'
            for s in l["lines"])
        lam = ""
        if l["lambda_home"] is not None:
            lam = (f'<div class="note">expected goals {l["lambda_home"]:.2f} v {l["lambda_away"]:.2f}</div>')
        lrows.append(f"""<tr><td colspan="6" style="background:#f8fafc">
<b>{esc(l["event"])}</b> <span class="note">· {esc(l["competition"])} · {esc(l["day"])} · {tier_badge(l["tier"])} ·
built from {esc(l["input"])} · {n_fx} prices</span>{lam}</td></tr>{detail}""")

    lines_body = f"""
<p class="eyebrow">Our lines · {len(all_sel)} prices on {lines_doc['count']} matches</p>
<h1>Every price we originated, match by match.</h1>
<p class="lede">These are our numbers. OLBG does not show bookmaker prices to this location, so nothing here is copied
from a market. Each match gets a win line; the five NHL fixtures also get a puck line and two totals because official
scoring totals were available for them.</p>
<div class="warn"><b>How to read a price.</b> A price of −219 means you stake 219 to win 100. It implies a 68.7% chance
before any margin. The chance column is ours and the price is that chance with a 4% margin applied, so the price is
always slightly worse than fair. The full method is on <a href="methodology.html">Method</a>.</div>
<div class="tbl-wrap"><table>
<tr><th>Market</th><th>Selection</th><th class="num">Our chance</th><th class="num">Our price</th><th>Band</th><th>Source</th></tr>
{''.join(lrows)}
</table></div>
"""
    (OUT / "lines.html").write_text(page("Our lines — OLBG Playbook", "lines.html", lines_body))

    # --------------------------------------------------------------------- sports
    sport_rows = []
    for s in SPORT_ORDER:
        sport_rows.append(
            f'<tr><td><a href="{SPORT_SLUG[s]}.html"><b>{esc(s)}</b></a></td>'
            f'<td class="num">{len(by_sport_fx.get(s, []))}</td>'
            f'<td class="num">{len(by_sport_picks.get(s, []))}</td>'
            f'<td class="num">{len(by_sport_preds.get(s, []))}</td>'
            f'<td>{esc("nothing listed" if not by_sport_fx.get(s) else "")}</td></tr>')
    sindex = f"""
<p class="eyebrow">Sports · fifteen in scope</p>
<h1>One page per sport.</h1>
<p class="lede">Each sport page carries that sport's matches, its picks in full, its prices and its written previews,
so the whole picture for one sport sits on one page.</p>
<div class="tbl-wrap"><table>
<tr><th>Sport</th><th class="num">Matches</th><th class="num">Picks</th><th class="num">Previews</th><th>Note</th></tr>
{''.join(sport_rows)}
</table></div>
"""
    (OUT / "sports" / "index.html").write_text(page("Sports — OLBG Playbook", "sports/index.html", sindex, root="../"))

    for s in SPORT_ORDER:
        fx = sorted(by_sport_fx.get(s, []), key=lambda f: (f["olbg_day"] or "", f["event"]))
        pk = by_sport_picks.get(s, [])
        pr = by_sport_preds.get(s, [])
        if not fx:
            body = (f'<p class="eyebrow">{esc(s)}</p><h1>{esc(s)}</h1>'
                    f'<div class="warn"><b>Nothing to price.</b> {esc(NO_EVENTS.get(s, "OLBG listed no event."))}'
                    f' This is recorded on <a href="../flagged.html">Flagged</a> rather than filled in with a '
                    f'fixture from somewhere else.</div>')
        else:
            frows = "".join(
                f'<tr><td>{esc(f["competition"])}</td><td>{esc(f["event"])}</td>'
                f'<td>{esc(f["olbg_day"] or "—")}<div class="note">OLBG: {esc(f["olbg_display"] or "—")}</div></td>'
                f'<td>{tier_badge(f["tier"])}</td>'
                f'<td class="src">{src_cell(f)}</td></tr>'
                for f in fx)
            prows = "".join(
                f'<tr><td><b>{esc(p["selection"])}</b></td><td>{esc(p["event"])}</td><td>{esc(p["market"])}</td>'
                f'<td class="num">{money(p["price"])}</td><td class="num">{pct(p["probability"])}</td>'
                f'<td>{badge(p["confidence"])}</td><td>{band_badge(p["in_band"])}</td></tr>' for p in pk)
            blocks = "".join(
                f'<article class="pred"><div class="top">{badge(p["confidence"])}<span>{esc(p["day"])}</span>'
                f'{band_badge(p["in_band"])}</div><h3>{esc(p["event"])} — <span style="color:#0b5c56">'
                f'{esc(p["selection"])}</span></h3><p class="body">{esc(p["text"])}</p>'
                f'<div class="facts"><b>Facts behind it</b><ul class="tight">'
                + "".join(f'<li>{esc(f["label"])}: <b>{esc(f["value"])}</b> — <a class="src" href="{esc(f["source"])}">source</a></li>' for f in p["facts"])
                + '</ul></div></article>' for p in pr)
            body = f"""
<p class="eyebrow">{esc(s)} · {len(fx)} matches · {len(pk)} picks · {len(pr)} previews</p>
<h1>{esc(s)}</h1>
<p class="lede">{len(fx)} matches listed by OLBG, {len(pk)} graded picks and {len(pr)} written previews.
The pick table comes first, because that is what the desk is for.</p>
<h2>Picks</h2>
<div class="tbl-wrap"><table>
<tr><th>Selection</th><th>Match</th><th>Market</th><th class="num">Price</th><th class="num">Chance</th><th>Grade</th><th>Band</th></tr>
{prows or '<tr><td colspan="7" class="note">No pick cleared the evidence bar on this sport.</td></tr>'}
</table></div>
<h2>Matches</h2>
<div class="tbl-wrap"><table>
<tr><th>Competition</th><th>Match</th><th>Day</th><th>Price built from</th><th>Source</th></tr>{frows}
</table></div>
<h2>Written previews</h2>
{blocks or '<p class="note">No preview on this sport. The reason is on <a href="../flagged.html">Flagged</a>.</p>'}
"""
        (OUT / "sports" / f"{SPORT_SLUG[s]}.html").write_text(
            page(f"{s} — OLBG Playbook", "sports/index.html", body, root="../"))

    # -------------------------------------------------------------------- sources
    groups = {}
    for s in sources_doc["sources"]:
        groups.setdefault(s["kind"], []).append(s)
    kind_label = {"olbg-hub": "OLBG sport hubs", "olbg-event": "OLBG event pages",
                  "official": "Governing-body feeds"}
    srows = ""
    for kind in ("official", "olbg-hub", "olbg-event"):
        rows = groups.get(kind, [])
        srows += (f'<h2>{esc(kind_label.get(kind, kind))} <span class="note">({len(rows)})</span></h2>'
                  '<div class="tbl-wrap"><table><tr><th>Source</th><th>What it was read for</th></tr>')
        srows += "".join(f'<tr><td class="src"><a href="{esc(s["url"])}">{esc(s["url"])}</a></td>'
                         f'<td>{esc(s["label"])}</td></tr>' for s in rows)
        srows += "</table></div>"
    sources_body = f"""
<p class="eyebrow">Sources</p>
<h1>Every link this desk used, {sources_doc['count']} of them.</h1>
<p class="lede">Three families: the governing-body feeds that supply statistics, OLBG's sport hubs where the event list
came from, and the OLBG event page behind every single row.</p>
{srows}
"""
    (OUT / "sources.html").write_text(page("Sources — OLBG Playbook", "sources.html", sources_body))

    # -------------------------------------------------------------------- flagged
    frows = "".join(
        f'<tr><td><code>{esc(f["id"])}</code></td><td>{esc(f["sport"])}</td><td><b>{esc(f["title"])}</b>'
        f'<div class="note">{esc(f["detail"])}</div></td><td>{esc(f["severity"])}</td>'
        f'<td class="src"><a href="{esc(f["source"])}">source</a></td></tr>' for f in flags)
    short_sports = [s for s in SPORT_ORDER if len(by_sport_preds.get(s, [])) < 5]
    flagged_body = f"""
<p class="eyebrow">Flagged for review · {len(flags)} items</p>
<h1>What we could not confirm, and what it costs.</h1>
<p class="lede">Nothing on this page is a guess that crept into a table. Each item is something the desk could not
stand behind, published so it can be checked and corrected.</p>
<div class="tbl-wrap"><table>
<tr><th>ID</th><th>Sport</th><th>Item</th><th>Status</th><th>Source</th></tr>{frows}
</table></div>
<h2>Sports short of the five-preview target</h2>
<p class="note">The brief asks for five written previews per sport. These sports did not reach five, and the reason is
the size of the board rather than a decision to skip them.</p>
<div class="tbl-wrap"><table><tr><th>Sport</th><th class="num">Previews</th><th class="num">Matches listed</th><th>Why</th></tr>
{''.join(f'<tr><td>{esc(s)}</td><td class="num">{len(by_sport_preds.get(s, []))}</td><td class="num">{len(by_sport_fx.get(s, []))}</td><td class="note">{esc("OLBG listed no event." if not by_sport_fx.get(s) else "Fewer fixtures on the OLBG board than the target, or the board carried too few tips to write from.")}</td></tr>' for s in short_sports)}
</table></div>
<h2>Blank values</h2>
<p class="note">Where a value could not be read from an official source it is left blank and pointed at here rather than
filled in: the official start time on every tennis, cricket, handball, volleyball, Gaelic, darts, greyhound and rugby
fixture; the tournament name on every tennis row; the venue on every non-NHL row; and the injury list on every fixture,
because no governing-body injury report was read for any of them.</p>
"""
    (OUT / "flagged.html").write_text(page("Flagged for review — OLBG Playbook", "flagged.html", flagged_body))

    # ---------------------------------------------------------------- methodology
    method_body = f"""
<p class="eyebrow">Method</p>
<h1>How a price and a grade get made here.</h1>
<p class="lede">Two inputs, never mixed silently, and a rubric written down before the picks were graded.</p>

<h2>1. Where the matches come from</h2>
<p>Every match is a row OLBG itself listed on one of its sixteen sport hubs, read first-hand on 24 October 2026
between 22:35 and 23:05 UTC. The hub in scope for each sport is listed on <a href="sources.html">Sources</a>. OLBG's
hub is a tip feed, not a fixture list: it only shows an event once at least one tip has been placed on it. That is why
Golf, Snooker, Motor Racing and Rugby League have no matches — those hubs returned "No tips found." or, for Rugby
League, only 2027 outrights.</p>

<h2>2. Where the prices come from</h2>
<p><b>Tier A, {sum(1 for f in fixtures if f['tier'] == 'A')} fixtures.</b> The five NHL games on 25 October. Each club's
goals for and goals against per game are read from the NHL's own season summary, regressed toward the league mean with
fifteen prior games because ten games is a small sample, adjusted for home ice (and not adjusted for the neutral-site
Heritage Classic), and run through a bivariate Poisson. That produces a win price, a puck line and two totals.</p>
<p><b>Tier B, {sum(1 for f in fixtures if f['tier'] == 'B')} fixtures.</b> Everything else. OLBG publishes the share of
its own tips on the highlighted selection. That share is already normalised across the market's outcomes, so it is read
as the market's implied chance for that selection. A share built on a handful of tips is not a probability, so it is
pulled toward 50% with six pseudo-tips before it is priced. Only the market OLBG printed can be originated this way: a
handicap or a total needs scoring data that this capture does not contain for these sports.</p>
<p>Both tiers then get the same margin: the fair decimal price from the chance, with 4% taken off the win part.</p>

<h2>3. How confidence is graded</h2>
<div class="tbl-wrap"><table>
<tr><th>Grade</th><th>Rule</th></tr>
<tr><td><span class="badge b-high">high</span></td><td>A governing-body input behind the price, a chance of 65% or
better, and a price inside −250 to +10000. All three.</td></tr>
<tr><td><span class="badge b-medium">medium</span></td><td>A price inside the band with a chance of 50% or better, or
a chance of 70% or better whose price falls outside the band.</td></tr>
<tr><td><span class="badge b-low">low</span></td><td>Everything else.</td></tr>
</table></div>
<p><b>Why the rule is not simply "over 70%".</b> A price of −250 is a 71.43% chance. A rule that calls anything above
70% high, combined with a rule that anything shorter than −250 is out of scope, can only ever be satisfied inside a
1.4-point window. On this slate {len(short)} selections cleared 70%, {len(in_band_all)} prices sat inside the band, and
{len(short_in)} did both. The grade therefore asks for evidence as well as probability, and the band is shown as its own
column on every table so the shortfall is visible rather than hidden.</p>

<h2>4. What a written preview has to contain</h2>
<ul class="tight">
<li>At least 30 words, one author, no repeated opening across previews.</li>
<li>The selection named in the heading, so the bet is never ambiguous.</li>
<li>Team or player, competition, the situation, and the numbers the case rests on.</li>
<li>A fact list under each preview, with a link to where each fact was read.</li>
<li>No use of the words "model" or "verified" anywhere in the prose — those are internal terms.</li>
</ul>

<h2>5. What is deliberately absent</h2>
<p>OLBG serves no bookmaker price to this location, so no market price is quoted anywhere on the desk. No injury list
is published against any fixture, because no governing-body injury report was read. No tennis tournament name is given,
because no official draw page returned to this reader. All of that is on <a href="flagged.html">Flagged</a>.</p>
"""
    (OUT / "methodology.html").write_text(page("Method — OLBG Playbook", "methodology.html", method_body))

    write_front_door()

    print(f"playbook_build: {9 + 1 + 15} pages, {len(fixtures)} fixtures, {big} picks, "
          f"{preds_doc['count']} predictions, root front door rebuilt")


if __name__ == "__main__":
    main()
