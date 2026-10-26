#!/usr/bin/env python3
"""Render the 26 October 2026 fifteen-sport desk into slate26/ and own the root front door.

Inputs are the committed JSON in data/slate26. Output is deterministic: run twice, same bytes.

Run: python scripts/slate26_build.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slate26"
OUT = ROOT / "slate26"

SPORTS = [
    ("ice-hockey", "Ice Hockey"), ("basketball", "Basketball"), ("tennis", "Tennis"),
    ("cricket", "Cricket"), ("handball", "Handball"), ("volleyball", "Volleyball"),
    ("gaelic", "Gaelic Sports"), ("baseball", "Baseball"), ("greyhounds", "Greyhounds"),
    ("motor-racing", "Motor Racing"), ("golf", "Golf"), ("snooker", "Snooker"),
    ("darts", "Darts"), ("rugby-union", "Rugby Union"), ("rugby-league", "Rugby League"),
]
SLUG = {k: k for k, _ in SPORTS}

CSS = """
:root{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--bg:#f8fafc;--teal:#0d9488;--amber:#b45309;--red:#b91c1c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
a{color:#0f766e}
.wrap{max-width:1160px;margin:0 auto;padding:0 18px}
header.top{background:#0f172a;color:#fff;padding:14px 0}
header.top .wrap{display:flex;gap:18px;align-items:center;flex-wrap:wrap}
header.top a{color:#cbd5e1;text-decoration:none;font-size:14px;font-weight:600}
header.top a:hover{color:#fff}
header.top .brand{color:#fff;font-weight:800;letter-spacing:.02em}
main{padding:26px 0 60px}
h1{font-size:30px;line-height:1.2;margin:8px 0 6px}
h2{font-size:21px;margin:34px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}
h3{font-size:17px;margin:22px 0 8px}
p.lede{font-size:17px;color:#334155;max-width:78ch}
.sub{color:var(--mut);font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0}
.k{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px}
.k .n{font-size:26px;font-weight:800;line-height:1.1}
.k .l{color:var(--mut);font-size:13px;margin-top:2px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:16px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px}
.card b{display:block;font-size:16px;margin-bottom:4px}
.card span{color:var(--mut);font-size:14px}
.card a{text-decoration:none}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f5f9;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#475569}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.03em}
.high{background:#dcfce7;color:#166534}
.medium{background:#fef3c7;color:#92400e}
.low{background:#e2e8f0;color:#334155}
.full{background:#dbeafe;color:#1e40af}
.market{background:#f1f5f9;color:#475569}
.flag{background:#fee2e2;color:#991b1b}
.note{background:#f1f5f9;color:#475569}
.pick{background:#fff;border:1px solid var(--line);border-left:4px solid var(--teal);border-radius:10px;padding:14px;margin:12px 0}
.pick h3{margin:0 0 6px}
.pick .meta{color:var(--mut);font-size:13px;margin-bottom:8px}
.note-box{background:#fff7ed;border:1px solid #fdba74;border-radius:10px;padding:14px;margin:16px 0}
.ok-box{background:#ecfdf5;border:1px solid #6ee7b7;border-radius:10px;padding:14px;margin:16px 0}
footer{border-top:1px solid var(--line);padding:20px 0 50px;color:var(--mut);font-size:13px}
code{background:#f1f5f9;padding:1px 5px;border-radius:5px;font-size:13px}
.scroll{overflow-x:auto}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def money(price) -> str:
    if price in ("", None):
        return "—"
    p = int(price)
    return f"+{p}" if p > 0 else str(p)


def pct(p) -> str:
    return "—" if p in (None, "") else f"{float(p) * 100:.1f}%"


def nav(page: str, depth: int = 0, prefix: str = "") -> str:
    pre = prefix + "../" * depth
    items = [("index.html", "Summary"), ("picks.html", "Picks"), ("predictions.html", "Predictions"),
             ("matches.html", "Matches"), ("lines.html", "Our lines"), ("sports/index.html", "By sport"),
             ("sources.html", "Sources"), ("flagged.html", "Flagged")]
    links = ""
    for href, label in items:
        style = ' style="color:#fff"' if href == page else ""
        links += f'<a href="{pre}{href}"{style}>{label}</a>'
    return (f'<header class="top"><div class="wrap"><a class="brand" href="{pre}index.html">OLBG2 · 26 Oct 2026</a>'
            f'{links}</div></header>')


def page(title: str, body: str, page_path: str, depth: int = 0) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
{nav(page_path, depth)}
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>OLBG2 · fifteen-sport desk captured 2026-10-26T05:45Z · every row links the source it came from ·
<a href="{('../' * depth)}flagged.html">Flagged for Review</a> · <a href="{('../' * depth)}methodology.html">Method</a> ·
<a href="{('../' * (depth + 1))}archive.html">every earlier desk</a></p>
</div></footer>
</body>
</html>
"""


def confidence_badge(c: str) -> str:
    return f'<span class="badge {esc(c)}">{esc(c)}</span>'


def pick_rows(picks, limit=None, denom=10):
    rows = []
    ordered = sorted(picks, key=lambda p: ({"high": 0, "medium": 1, "low": 2}.get(p["confidence"], 3),
                                           -(p["probability"] or 0)))
    for i, p in enumerate(ordered[:limit] if limit else ordered, 1):
        rows.append(
            f'<tr><td class="num">{i}</td><td><b>{esc(p["selection"])}</b></td>'
            f'<td>{esc(p["market"])}</td><td>{esc(p["event"])}</td>'
            f'<td class="num">{money(p["price"])}</td><td class="num">{pct(p["probability"])}</td>'
            f'<td>{confidence_badge(p["confidence"])}</td><td class="num">{esc(p["tips"])}</td>'
            f'<td><a href="{esc(p["hub_url"])}" rel="nofollow">OLBG</a></td></tr>')
    return "".join(rows)


def preview_map(preds):
    return {r["fixture"]: r for r in preds["predictions"]}


def build_index() -> str:
    fx, picks, preds, lines, hubs, flags, outs = (load("fixtures.json"), load("picks.json"),
                                                  load("predictions.json"), load("lines.json"),
                                                  load("hubs.json"), load("flagged.json"), load("outrights.json"))
    pm = preview_map(preds)
    highs = [p for p in picks["picks"] if p["confidence"] == "high"]
    high_rows = ""
    for i, p in enumerate(sorted(highs, key=lambda x: -(x["probability"] or 0)), 1):
        prev = pm.get(p["fixture"])
        link = (f'<a href="predictions.html#{p["fixture"]}">read the preview</a>' if prev
                else '<span class="sub">market-only row</span>')
        high_rows += (f'<tr><td class="num">{i}</td><td>{esc(p["sport_label"])}</td>'
                      f'<td><b>{esc(p["selection"])}</b><br><span class="sub">{esc(p["event"])}</span></td>'
                      f'<td>{esc(p["market"])}</td><td class="num">{money(p["price"])}</td>'
                      f'<td class="num">{pct(p["probability"])}</td><td class="num">{esc(p["tips"])}</td>'
                      f'<td>{link}</td></tr>')

    cover = ""
    for key, label in SPORTS:
        h = next(x for x in hubs["hubs"] if x["sport"] == key)
        sp = [p for p in picks["picks"] if p["sport"] == key]
        sp_prev = [r for r in preds["predictions"] if r["sport"] == key]
        sp_high = [p for p in sp if p["confidence"] == "high"]
        state = {"matches": "match listed", "outright-only": "outright only", "none": "nothing listed"}[h["state"]]
        badge = {"matches": "medium", "outright-only": "low", "none": "flag"}[h["state"]]
        cover += (f'<tr><td><a href="sports/{SLUG[key]}.html">{esc(label)}</a></td>'
                  f'<td><span class="badge {badge}">{state}</span></td>'
                  f'<td class="num">{len(sp)}</td><td class="num">{len(sp_high)}</td>'
                  f'<td class="num">{len(sp_prev)}</td><td class="num">'
                  f'{max(0, 5 - len(sp_prev)) if len(sp) else "n/a"}</td></tr>')

    body = f"""
<h1>Fifteen sports, one page: what OLBG has listed, what we price, what we have written</h1>
<p class="lede">Captured from OLBG's fifteen sport hubs between 05:05 and 05:45 UTC on Monday 26 October 2026.
Every fixture below is on OLBG now, carries our own price and a confidence grade, and links the source it came from.
Where an official feed was readable we say so; where it was not, the row says that too.</p>

<div class="grid">
  <div class="k"><div class="n">{fx['count']}</div><div class="l">upcoming matches</div></div>
  <div class="k"><div class="n">{picks['count']}</div><div class="l">picks still to start</div></div>
  <div class="k"><div class="n">{picks['high']}</div><div class="l">high confidence, all inside the band</div></div>
  <div class="k"><div class="n">{lines['count']}</div><div class="l">prices originated here</div></div>
  <div class="k"><div class="n">{preds['count']}</div><div class="l">written predictions</div></div>
  <div class="k"><div class="n">{flags['count']}</div><div class="l">flagged for review</div></div>
</div>

<div class="cards">
  <a class="card" href="picks.html"><b>Picks →</b><span>The picks, sport by sport, numbered and graded high, medium or low.</span></a>
  <a class="card" href="predictions.html"><b>Written predictions →</b><span>{preds['count']} previews of 30+ words, with the facts and links under each one.</span></a>
  <a class="card" href="matches.html"><b>Every match →</b><span>All {fx['count']} OLBG fixtures with the official facts and source links.</span></a>
  <a class="card" href="lines.html"><b>Our lines →</b><span>Probability and price for each market, and how each was originated.</span></a>
</div>

<h2>The executive summary: today's highest-confidence picks</h2>
<p class="sub">Nine picks graded high, every one inside the requested −250 to +10000 window. Sorted by our probability.</p>
<div class="scroll"><table>
<thead><tr><th class="num">#</th><th>Sport</th><th>Pick</th><th>Market</th><th class="num">Our price</th>
<th class="num">Our chance</th><th class="num">OLBG tips</th><th>Write-up</th></tr></thead>
<tbody>{high_rows}</tbody>
</table></div>

<div class="note-box">
<p><b>Read this before the numbers.</b> Five of the fifteen sports had no match on OLBG at capture: Golf and Snooker
returned “No tips found.”, while Darts, Rugby Union and Rugby League showed 2027 outrights only. Nine high-confidence
picks from those five sports cannot exist, so none was invented. Across the other ten sports the board gave
{picks['count']} priced matches; this desk writes up the ones it can stand behind and prints the rest as priced picks
without prose. <a href="flagged.html">The full list of what is missing, with sources, is on the flagged page.</a></p>
</div>

<h2>Coverage by sport</h2>
<p class="sub">“Written” counts previews, not picks. The last column is the honest shortfall against the five-a-day target.</p>
<div class="scroll"><table>
<thead><tr><th>Sport</th><th>OLBG board</th><th class="num">Priced matches</th><th class="num">High picks</th>
<th class="num">Written</th><th class="num">Short of 5</th></tr></thead>
<tbody>{cover}</tbody></table></div>

<h2>Where the picks are</h2>
<div class="cards">
  <a class="card" href="picks.html"><b>1. Picks page</b><span>One table per sport. Pick 1 to 10 per sport, each with price, chance and grade.</span></a>
  <a class="card" href="predictions.html"><b>2. Predictions page</b><span>{preds['count']} written previews. {preds['full']} quote official statistics, {preds['market']} are market-only and say so.</span></a>
  <a class="card" href="band.html"><b>3. Odds band</b><span>Which prices sit inside −250 to +10000 and which were pushed outside by the favourite's price.</span></a>
  <a class="card" href="methodology.html"><b>4. Method</b><span>How each price was originated, with the formula printed, and what was not available.</span></a>
</div>

<h2>What this desk does not claim</h2>
<ul>
<li>Only {preds['full']} fixtures had an official fixture-level statistical feed readable in this session (NHL and MLB).
The other {fx['count'] - preds['full']} rows carry the OLBG listing and our own price, and nothing more.</li>
<li>No official injury or availability report was captured for any sport, so no preview mentions one.</li>
<li>OLBG's hub times are US Eastern, proved against the Austrian Volleyball Federation fixture list. They are printed
verbatim and never treated as UTC; the UTC column is filled only where an official feed gave it.</li>
<li>{outs['count']} season outrights are listed separately and kept out of the match totals.</li>
</ul>
"""
    return page("OLBG2 — 26 October 2026 fifteen-sport desk", body, "index.html")


def build_picks() -> str:
    picks = load("picks.json")
    preds = load("predictions.json")
    pm = preview_map(preds)
    sections = ""
    for key, label in SPORTS:
        sp = [p for p in picks["picks"] if p["sport"] == key]
        prev = [r for r in preds["predictions"] if r["sport"] == key]
        if not sp:
            sections += (f'<h2 id="{key}">{esc(label)}</h2>'
                         '<div class="note-box"><p>No match was priced by OLBG for this sport at capture, so there is no '
                         'pick to make. The reason and the source are on the '
                         f'<a href="sports/{SLUG[key]}.html">sport page</a>.</p></div>')
            continue
        n_high = sum(1 for p in sp if p["confidence"] == "high")
        sections += (f'<h2 id="{key}">{esc(label)} <span class="sub">— {len(sp)} priced match'
                     f'{"" if len(sp) == 1 else "es"}, {n_high} high, {len(prev)} written</span></h2>')
        sections += ('<div class="scroll"><table><thead><tr><th class="num">#</th><th>Pick</th><th>Market</th>'
                     '<th>Fixture</th><th class="num">Our price</th><th class="num">Our chance</th><th>Grade</th>'
                     '<th class="num">OLBG tips</th><th>Write-up</th><th>Source</th></tr></thead><tbody>')
        ordered = sorted(sp, key=lambda p: ({"high": 0, "medium": 1, "low": 2}.get(p["confidence"], 3),
                                            -(p["probability"] or 0)))
        for i, p in enumerate(ordered, 1):
            link = f'<a href="predictions.html#{p["fixture"]}">preview</a>' if p["fixture"] in pm else '<span class="sub">—</span>'
            sections += (f'<tr><td class="num">{i}</td><td><b>{esc(p["selection"])}</b></td>'
                         f'<td>{esc(p["market"])}</td><td>{esc(p["event"])}<br><span class="sub">{esc(p["league"])}</span></td>'
                         f'<td class="num">{money(p["price"])}</td><td class="num">{pct(p["probability"])}</td>'
                         f'<td>{confidence_badge(p["confidence"])}</td><td class="num">{esc(p["tips"])}</td>'
                         f'<td>{link}</td><td><a href="{esc(p["hub_url"])}" rel="nofollow">OLBG</a></td></tr>')
        sections += '</tbody></table></div>'

    body = f"""
<h1>Every pick, sport by sport</h1>
<p class="lede">{picks['count']} picks across ten sports. Numbered 1 upwards within each sport, highest confidence first.
{money(-250)} is the shortest price the desk will call high; anything shorter is graded medium and shown on the
<a href="band.html">band page</a> as outside the window.</p>
<div class="grid">
  <div class="k"><div class="n">{picks['high']}</div><div class="l">high</div></div>
  <div class="k"><div class="n">{picks['medium']}</div><div class="l">medium</div></div>
  <div class="k"><div class="n">{picks['low']}</div><div class="l">low</div></div>
  <div class="k"><div class="n">{picks['in_band']}</div><div class="l">inside −250…+10000</div></div>
</div>
{sections}
"""
    return page("Picks — OLBG2 26 October 2026", body, "picks.html")


def build_predictions() -> str:
    preds = load("predictions.json")
    fx = load("fixtures.json")
    cards = ""
    for r in preds["predictions"]:
        facts = "".join(
            f'<tr><td>{esc(f["claim"])}</td><td>{esc(f["value"])}</td>'
            f'<td><a href="{esc(f["url"])}" rel="nofollow">{esc(f["source"])}</a></td></tr>'
            for f in r["facts"])
        facts_block = (f'<h3>Official facts behind it</h3><div class="scroll"><table><thead><tr><th>Claim</th>'
                       f'<th>Value</th><th>Source</th></tr></thead><tbody>{facts}</tbody></table></div>'
                       if facts else
                       '<p class="sub">No official fixture-level feed was readable for this competition, so this '
                       'preview quotes no form, no recent results and no availability. It is confined to the OLBG '
                       'listing and our own price, and it says so on the card.</p>')
        cards += f"""
<div class="pick" id="{esc(r['fixture'])}">
  <h3>{esc(r['selection'])} <span class="sub">· {esc(r['event'])}</span></h3>
  <p class="meta">{esc(r['sport_label'])} · {esc(r['league'])} · {esc(r['market'])} ·
    our price <b>{money(r['price'])}</b> · our chance {pct(r['probability'])} · <span class="badge {esc(r['tier'])}">{esc(r['tier'])} preview</span></p>
  <p>{esc(r['text'])}</p>
  {facts_block}
  <p class="sub">{r['words']} words · OLBG board {esc(r['tips'])} tips ({esc(r['share'])}%) ·
    <a href="{esc(r['hub_url'])}" rel="nofollow">OLBG listing</a> · event id {esc(r['olbg_event_id'])}</p>
</div>"""
    body = f"""
<h1>The written predictions</h1>
<p class="lede">{preds['count']} previews, {preds['shortest_words']} words at the shortest, one per pick that the desk will
write up. Two tiers, labelled on every card: <span class="badge full">full</span> quotes statistics read from an
official governing-body feed; <span class="badge market">market</span> is confined to the OLBG listing and our price
because no official fixture-level feed was readable for that competition.</p>
<div class="grid">
  <div class="k"><div class="n">{preds['count']}</div><div class="l">previews</div></div>
  <div class="k"><div class="n">{preds['full']}</div><div class="l">full, official statistics</div></div>
  <div class="k"><div class="n">{preds['market']}</div><div class="l">market-only</div></div>
  <div class="k"><div class="n">{preds['on_high_picks']}</div><div class="l">on high-confidence picks</div></div>
</div>
<div class="note-box"><p><b>Why there are {preds['count']} and not 75.</b> A preview is only written where it can name
the selection and stand behind every sentence. Eleven rows met that bar today: two because an official feed supplied the
numbers, nine because the pick is inside the −250 to +10000 window with a sample of three tips or more. The
{fx['count'] - preds['count']} rows without prose keep their price and grade on the picks page and are listed by sport on the
<a href="flagged.html">flagged page</a>.</p></div>
{cards}
"""
    return page("Predictions — OLBG2 26 October 2026", body, "predictions.html")


def build_matches() -> str:
    fx = load("fixtures.json")
    rows = ""
    for f in sorted(fx["fixtures"], key=lambda r: (r["sport"], r["event"])):
        facts = (f'{len(f["facts"])} official fact{"" if len(f["facts"]) == 1 else "s"}'
                 if f["facts"] else '<span class="sub">none</span>')
        grade = {"official": "high", "official-time-only": "medium", "olbg-only": "flag"}[f["data_grade"]]
        rows += (f'<tr><td>{esc(f["sport_label"])}</td><td><b>{esc(f["event"])}</b><br>'
                 f'<span class="sub">{esc(f["league"])}</span></td>'
                 f'<td>{esc(f["olbg_display_time"])}</td>'
                 f'<td>{esc(f["official_start_utc"] or "—")}</td>'
                 f'<td>{esc(f["selection"])}<br><span class="sub">{esc(f["market"])}</span></td>'
                 f'<td>{facts}</td><td><span class="badge {grade}">{esc(f["data_grade"])}</span></td>'
                 f'<td><a href="{esc(f["hub_url"])}" rel="nofollow">OLBG</a><br>'
                 f'<span class="sub">id {esc(f["olbg_event_id"])}</span></td></tr>')
    body = f"""
<h1>All {fx['count']} OLBG fixtures</h1>
<p class="lede">Every match the fifteen hubs listed at capture, with OLBG's displayed time kept verbatim next to the
official UTC start where one was read. The data grade says what the row rests on: <span class="badge high">official</span>
means an official feed supplied fixture-level statistics, <span class="badge medium">official-time-only</span> means only
the start time was confirmed, <span class="badge flag">olbg-only</span> means the listing is all we have.</p>
<div class="scroll"><table>
<thead><tr><th>Sport</th><th>Fixture</th><th>OLBG shows</th><th>Official UTC</th><th>Listed pick</th>
<th>Official facts</th><th>Grade</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="sub">Blank UTC cells are blank on purpose: OLBG's string is US Eastern and is not an official start for that
competition. They are listed together on the <a href="flagged.html">flagged page</a>.</p>
"""
    return page("Matches — OLBG2 26 October 2026", body, "matches.html")


def build_lines() -> str:
    lines = load("lines.json")
    rows = ""
    for l in lines["lines"]:
        basis = {"official-input": "official season records",
                 "olbg-tip-share": "OLBG tip share, shrunk 15%",
                 "olbg-tip-share-thin": "OLBG tip share, shrunk and clamped (under 3 tips)"}[l["basis"]]
        band_cell = "yes" if l["in_band"] else '<span class="badge flag">no</span>'
        rows += (f'<tr><td>{esc(l["fixture"])}</td><td>{esc(l["market"])}</td><td><b>{esc(l["selection"])}</b></td>'
                 f'<td class="num">{pct(l["probability"])}</td><td class="num">{money(l["price"])}</td>'
                 f'<td class="num">{money(l["opposite_price"])}</td><td>{esc(basis)}</td>'
                 f'<td>{band_cell}</td></tr>')
    body = f"""
<h1>Our own lines</h1>
<p class="lede">One originated price per fixture on the market OLBG lists, plus the opposite side wherever the market is
two-way. {lines['in_band']} of {lines['count']} sit inside −250 to +10000. No bookmaker price was copied: the OLBG hub
publishes no odds, only the share of tips, and the method page prints the conversion in full.</p>
<div class="scroll"><table>
<thead><tr><th>Fixture</th><th>Market</th><th>Selection</th><th class="num">Our chance</th>
<th class="num">Our price</th><th class="num">Opposite side</th><th>How it was originated</th><th>In band</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="sub">Three-way markets (the handball money line carries a draw) get a price only on the named outcome: the
split between the two teams cannot be derived from a single tip share, so it is not invented.</p>
"""
    return page("Our lines — OLBG2 26 October 2026", body, "lines.html")


def build_band() -> str:
    picks = load("picks.json")
    inside = [p for p in picks["picks"] if p["in_band"]]
    outside = [p for p in picks["picks"] if not p["in_band"]]

    def table(rows):
        out = ('<div class="scroll"><table><thead><tr><th>Sport</th><th>Pick</th><th>Fixture</th>'
               '<th class="num">Our price</th><th class="num">Our chance</th><th>Grade</th></tr></thead><tbody>')
        for p in sorted(rows, key=lambda x: -(x["probability"] or 0)):
            out += (f'<tr><td>{esc(p["sport_label"])}</td><td><b>{esc(p["selection"])}</b></td>'
                    f'<td>{esc(p["event"])}</td><td class="num">{money(p["price"])}</td>'
                    f'<td class="num">{pct(p["probability"])}</td><td>{confidence_badge(p["confidence"])}</td></tr>')
        return out + "</tbody></table></div>"

    body = f"""
<h1>The −250 to +10000 window</h1>
<p class="lede">The brief asks for high-confidence picks between −250 and +10000. That window starts at a 71.4% implied
chance, so a genuine short favourite lands outside it on the short side. Both lists are printed rather than trimming the
board to fit.</p>
<div class="grid">
  <div class="k"><div class="n">{len(inside)}</div><div class="l">inside the window</div></div>
  <div class="k"><div class="n">{len(outside)}</div><div class="l">outside, all on the short side</div></div>
</div>
<h2>Inside −250 to +10000</h2>
{table(inside)}
<h2>Outside the window</h2>
<p class="sub">These are priced shorter than −250 — no pick sits beyond +10000 today.</p>
{table(outside)}
"""
    return page("Odds band — OLBG2 26 October 2026", body, "band.html")


def build_sources() -> str:
    src = load("sources.json")
    rows = "".join(f'<tr><td><b>{esc(s["name"])}</b></td><td><a href="{esc(s["url"])}" rel="nofollow">{esc(s["url"])}</a></td>'
                   f'<td>{esc(s["note"])}</td></tr>' for s in src["sources"])
    body = f"""
<h1>Sources</h1>
<p class="lede">Every source read in this session, with what it supported. {src['count']} entries. A source appears here
only if it was actually opened; nothing is listed from memory.</p>
<div class="scroll"><table><thead><tr><th>Source</th><th>URL</th><th>What it was used for</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    return page("Sources — OLBG2 26 October 2026", body, "sources.html")


def build_flagged() -> str:
    fl = load("flagged.json")
    rows = ""
    for f in fl["items"]:
        badge = "flag" if f["status"] == "unverified" else "note"
        rows += (f'<tr><td>{esc(f["id"])}</td><td>{esc(f["sport"])}</td><td><b>{esc(f["event"])}</b><br>'
                 f'<span class="sub">{esc(f["fixture"])}</span></td><td>{esc(f["detail"])}</td>'
                 f'<td><span class="badge {badge}">{esc(f["status"])}</span></td>'
                 f'<td><a href="{esc(f["source"])}" rel="nofollow">source</a></td></tr>')
    unver = sum(1 for f in fl["items"] if f["status"] == "unverified")
    body = f"""
<h1>Flagged for Review</h1>
<p class="lede">Everything this desk could not put on firm ground, with the source that was checked. Nothing here blocks
the publish: each item is labelled, linked and left out of the numbers rather than filled in with a guess.</p>
<div class="grid">
  <div class="k"><div class="n">{fl['count']}</div><div class="l">items</div></div>
  <div class="k"><div class="n">{unver}</div><div class="l">unverified values left blank</div></div>
  <div class="k"><div class="n">{fl['count'] - unver}</div><div class="l">notes on the data itself</div></div>
</div>
<div class="scroll"><table><thead><tr><th>ID</th><th>Sport</th><th>Item</th><th>What was found</th>
<th>Status</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    return page("Flagged for Review — OLBG2 26 October 2026", body, "flagged.html")


def build_outrights() -> str:
    outs = load("outrights.json")
    rows = "".join(f'<tr><td>{esc(o["sport"])}</td><td><b>{esc(o["competition"])}</b></td><td>{esc(o["selection"])}</td>'
                   f'<td>{esc(o["market"])}</td><td>{esc(o["display_time"])}</td>'
                   f'<td class="num">{o["tips"]}/{o["total_tips"]}</td><td class="num">{o["share"]}%</td></tr>'
                   for o in outs["outrights"])
    body = f"""
<h1>Season outrights, kept out of the match count</h1>
<p class="lede">OLBG lists {outs['count']} futures markets across cricket, darts, rugby union, rugby league and Gaelic
football. They are real listings and they are shown here in full, but counting them as matches would inflate the fixture
total, so they are excluded from it.</p>
<div class="scroll"><table><thead><tr><th>Sport</th><th>Competition</th><th>Selection</th><th>Market</th>
<th>OLBG date</th><th class="num">Tips</th><th class="num">Share</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    return page("Outrights — OLBG2 26 October 2026", body, "outrights.html")


def build_methodology() -> str:
    body = """
<h1>Method</h1>
<p class="lede">Short version: the fixtures come from OLBG, the facts come from governing bodies, the prices are ours,
and the gaps are printed instead of filled.</p>

<h2>1. Finding the fixtures</h2>
<p>Each of the fifteen sport hubs was opened in turn (<code>olbg.com/betting-tips/&lt;Sport&gt;/&lt;id&gt;</code>) and the
tips table read row by row: event name, competition label, displayed time, market, the most-tipped selection, the tip
count as <code>n/m</code> and OLBG's own percentage. Those ten fields are the only things taken from OLBG. No odds are
published on the hub, so no bookmaker price was copied anywhere on this site.</p>

<h2>2. Originating a price</h2>
<p>Two routes, printed on every line row:</p>
<ul>
<li><b>OLBG tip share</b> (74 rows). The share <code>s</code> is shrunk 15% toward a coin flip:
<code>p = 0.5 + 0.85 × (s − 0.5)</code>, and capped at 78%. A share is a popularity poll, not a probability, and both the
shrinkage and the cap are the allowance for that: a unanimous board is not a 92% winner. Rows with fewer than three tips
are clamped further, to 65%, because one tip reads 100% and would otherwise price as a −1233 favourite.</li>
<li><b>Official season records</b> (1 row, Detroit at Edmonton). With both records read from the NHL feed:
<code>logit = 3.6 × (points%home − points%away) + 0.22</code>, <code>p = 1/(1+e^−logit)</code>. The 3.6 weight and the
0.22 home-ice term are this desk's own choices and are stated here so the number can be argued with.</li>
</ul>
<p>The American price follows from the probability (<code>−100p/(1−p)</code> above even money, <code>100(1−p)/p</code>
below). Two-way markets also get the opposite side.</p>

<h2>3. Grading a pick</h2>
<ul>
<li><b>high</b> — our chance at least 62%, at least four tips behind the row, and the price inside −250 to +10000.</li>
<li><b>medium</b> — our chance at least 55% with at least three tips, or a high chance that falls outside the window.</li>
<li><b>low</b> — everything else, including every row where OLBG's most-tipped selection is the draw.</li>
</ul>

<h2>4. Writing the previews</h2>
<p>Two tiers appear on every prediction card. <b>Full</b> means the text quotes statistics read from an official feed
that day and the facts are listed under the preview with their links. <b>Market</b> means no official fixture-level feed
was readable for that competition: the preview then confines itself to the fixture, the OLBG tip sample and our price,
and makes no claim about form, recent results or availability. Every preview is at least 30 words, none repeats another's
opening, and the words “model” and “verified” are kept out of reader-facing copy — the checks run in
<code>scripts/slate26_predictions.py</code>.</p>

<h2>5. Times</h2>
<p>OLBG's displayed time is US Eastern. The proof is on the desk: four Austrian Volley League matches read
11:30/12:30/13:00/14:00 on OLBG and 16:30/17:30/18:00/19:00 CET on the federation's own fixture list, exactly five hours
apart on every row. The three NHL rows carry a further +7 minute display offset against the official puck drop. The UTC
column is filled only from an official feed and is left blank otherwise.</p>

<h2>6. What was not available</h2>
<ul>
<li>No official injury or availability feed was readable for any of the fifteen sports. No preview mentions one.</li>
<li>Golf and Snooker showed no tips at all; Darts, Rugby Union and Rugby League showed 2027 outrights only. Five sports
therefore have no fixture, no pick and no preview.</li>
<li>Basketball, tennis, handball, volleyball (outside Austria) and cricket had no readable official fixture-level feed in
this session, so those rows carry a price and a grade but no statistical preview.</li>
<li>OLBG's generic event path <code>/betting-tips/event/&lt;id&gt;</code> renders an empty page, so rows link the sport hub
and print the event id instead of deep-linking.</li>
</ul>
"""
    return page("Method — OLBG2 26 October 2026", body, "methodology.html")


def build_sports_index() -> str:
    fx, picks, preds, hubs = load("fixtures.json"), load("picks.json"), load("predictions.json"), load("hubs.json")
    rows = ""
    for key, label in SPORTS:
        h = next(x for x in hubs["hubs"] if x["sport"] == key)
        n = sum(1 for f in fx["fixtures"] if f["sport"] == key)
        n_high = sum(1 for p in picks["picks"] if p["sport"] == key and p["confidence"] == "high")
        n_pred = sum(1 for r in preds["predictions"] if r["sport"] == key)
        rows += (f'<tr><td><a href="{SLUG[key]}.html"><b>{esc(label)}</b></a></td>'
                 f'<td class="num">{n}</td><td class="num">{n_high}</td><td class="num">{n_pred}</td>'
                 f'<td>{esc(h["note"])}</td></tr>')
    body = f"""
<h1>By sport</h1>
<p class="lede">Fifteen pages, one per covered sport. Each carries that sport's OLBG board state, every fixture, every
pick and any preview, so a single sport can be checked without reading the rest of the desk.</p>
<div class="scroll"><table><thead><tr><th>Sport</th><th class="num">Matches</th><th class="num">High picks</th>
<th class="num">Previews</th><th>What OLBG showed at capture</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    return page("By sport — OLBG2 26 October 2026", body, "sports/index.html", depth=1)


def build_sport(key: str, label: str) -> str:
    fx, picks, preds, hubs = load("fixtures.json"), load("picks.json"), load("predictions.json"), load("hubs.json")
    outs = load("outrights.json")
    h = next(x for x in hubs["hubs"] if x["sport"] == key)
    sp = [f for f in fx["fixtures"] if f["sport"] == key]
    sp_picks = sorted([p for p in picks["picks"] if p["sport"] == key],
                      key=lambda p: ({"high": 0, "medium": 1, "low": 2}.get(p["confidence"], 3),
                                     -(p["probability"] or 0)))
    sp_preds = [r for r in preds["predictions"] if r["sport"] == key]
    sp_out = [o for o in outs["outrights"] if o["sport"] == key]

    boards = {"matches": ("medium", "match listed"), "outright-only": ("low", "outright only"),
              "none": ("flag", "nothing listed")}[h["state"]]
    head = (f'<h1>{esc(label)}</h1><p class="lede">{esc(h["note"])}</p>'
            f'<p>OLBG hub: <a href="{esc(h["url"])}" rel="nofollow">{esc(h["url"])}</a> · '
            f'<span class="badge {boards[0]}">{boards[1]}</span></p>')

    if not sp:
        gap = (f'<div class="note-box"><p><b>No pick for {esc(label)} today, and why.</b> OLBG listed no match on this '
               'hub at capture, so there is no fixture to price and no preview to write. The desk does not invent a '
               'fixture to fill the five-a-day target. <a href="../flagged.html">See the flagged page.</a></p></div>')
        picks_html = ""
    else:
        gap = ""
        picks_html = ('<h2>Picks, highest confidence first</h2><div class="scroll"><table><thead><tr>'
                      '<th class="num">#</th><th>Pick</th><th>Market</th><th>Fixture</th><th class="num">Our price</th>'
                      '<th class="num">Our chance</th><th>Grade</th><th class="num">OLBG tips</th></tr></thead><tbody>')
        for i, p in enumerate(sp_picks, 1):
            picks_html += (f'<tr><td class="num">{i}</td><td><b>{esc(p["selection"])}</b></td>'
                           f'<td>{esc(p["market"])}</td><td>{esc(p["event"])}</td>'
                           f'<td class="num">{money(p["price"])}</td><td class="num">{pct(p["probability"])}</td>'
                           f'<td>{confidence_badge(p["confidence"])}</td><td class="num">{esc(p["tips"])}</td></tr>')
        picks_html += '</tbody></table></div>'

    fix_html = ""
    if sp:
        fix_html = ('<h2>Every fixture</h2><div class="scroll"><table><thead><tr><th>Fixture</th><th>Competition</th>'
                    '<th>OLBG shows</th><th>Official UTC</th><th>Listed pick</th><th>Official facts</th>'
                    '<th>Source</th></tr></thead><tbody>')
        for f in sorted(sp, key=lambda r: r["event"]):
            facts = (", ".join(x["claim"] for x in f["facts"]) if f["facts"]
                     else '<span class="sub">none captured</span>')
            fix_html += (f'<tr><td><b>{esc(f["event"])}</b></td><td>{esc(f["league"])}</td>'
                         f'<td>{esc(f["olbg_display_time"])}</td><td>{esc(f["official_start_utc"] or "—")}</td>'
                         f'<td>{esc(f["selection"])}</td><td class="sub">{facts}</td>'
                         f'<td><a href="{esc(f["hub_url"])}" rel="nofollow">OLBG</a></td></tr>')
        fix_html += '</tbody></table></div>'

    prev_html = ""
    if sp_preds:
        prev_html = '<h2>Written predictions</h2>'
        for r in sp_preds:
            prev_html += (f'<div class="pick"><h3><a href="../predictions.html#{esc(r["fixture"])}">'
                          f'{esc(r["selection"])}</a> <span class="sub">· {esc(r["event"])}</span> '
                          f'<span class="badge {esc(r["tier"])}">{esc(r["tier"])}</span></h3>'
                          f'<p>{esc(r["text"])}</p></div>')
    else:
        prev_html = ('<h2>Written predictions</h2><div class="note-box"><p>None for this sport. A preview is written only '
                     'where an official fixture-level feed was readable, and none was for this competition in this '
                     'session.</p></div>')

    out_html = ""
    if sp_out:
        out_html = ('<h2>Season outrights (excluded from the match count)</h2><div class="scroll"><table><thead><tr>'
                    '<th>Competition</th><th>Selection</th><th>Market</th><th>OLBG date</th><th class="num">Tips</th>'
                    '</tr></thead><tbody>')
        for o in sp_out:
            out_html += (f'<tr><td>{esc(o["competition"])}</td><td>{esc(o["selection"])}</td>'
                         f'<td>{esc(o["market"])}</td><td>{esc(o["display_time"])}</td>'
                         f'<td class="num">{o["tips"]}/{o["total_tips"]}</td></tr>')
        out_html += '</tbody></table></div>'

    body = f"""{head}
<div class="grid">
  <div class="k"><div class="n">{len(sp)}</div><div class="l">matches</div></div>
  <div class="k"><div class="n">{sum(1 for p in sp_picks if p['confidence'] == 'high')}</div><div class="l">high picks</div></div>
  <div class="k"><div class="n">{len(sp_preds)}</div><div class="l">written previews</div></div>
  <div class="k"><div class="n">{max(0, 5 - len(sp_preds))}</div><div class="l">short of five</div></div>
</div>
{gap}{picks_html}{fix_html}{prev_html}{out_html}
<p class="sub"><a href="../picks.html">All picks</a> · <a href="../matches.html">all matches</a> ·
<a href="index.html">all sports</a></p>
"""
    return page(f"{label} — OLBG2 26 October 2026", body, f"sports/{SLUG[key]}.html", depth=1)


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    files = {
        "index.html": build_index(), "picks.html": build_picks(),
        "predictions.html": build_predictions(), "matches.html": build_matches(),
        "lines.html": build_lines(), "band.html": build_band(),
        "sources.html": build_sources(), "flagged.html": build_flagged(),
        "outrights.html": build_outrights(), "methodology.html": build_methodology(),
        "sports/index.html": build_sports_index(),
    }
    for key, label in SPORTS:
        files[f"sports/{SLUG[key]}.html"] = build_sport(key, label)
    for name, html_text in files.items():
        (OUT / name).write_text(html_text, encoding="utf-8")
    return {"pages": len(files)}


def write_front_door() -> str:
    """The repository's single landing page for this session (called by scripts/build_site.py)."""
    fx, picks, preds, flags = load("fixtures.json"), load("picks.json"), load("predictions.json"), load("flagged.json")
    highs = sorted([p for p in picks["picks"] if p["confidence"] == "high"], key=lambda x: -(x["probability"] or 0))
    pm = preview_map(preds)
    rows = ""
    for p in highs:
        link = (f'<a href="slate26/predictions.html#{esc(p["fixture"])}">preview</a>'
                if p["fixture"] in pm else '<span class="sub">—</span>')
        rows += (f'<tr><td>{esc(p["sport_label"])}</td><td><b>{esc(p["selection"])}</b><br>'
                 f'<span class="sub">{esc(p["event"])}</span></td><td>{esc(p["market"])}</td>'
                 f'<td class="num">{money(p["price"])}</td><td class="num">{pct(p["probability"])}</td>'
                 f'<td class="num">{esc(p["tips"])}</td><td>{link}</td>'
                 f'<td><a href="{esc(p["hub_url"])}" rel="nofollow">OLBG</a></td></tr>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OLBG2 — fifteen sports, 26 October 2026</title>
<meta name="description" content="OLBG's fifteen covered sports captured 26 October 2026: 75 fixtures, 75 originated prices, 9 high-confidence picks inside -250 to +10000, 11 written predictions, every gap flagged.">
<style>{CSS}</style>
</head>
<body>
{nav("index.html", prefix="slate26/")}
<main><div class="wrap">
<h1>Start here: the 26 October desk, fifteen sports</h1>
<p class="lede">Captured from OLBG's fifteen sport hubs at 05:05–05:45 UTC today. One page tells you what OLBG has
listed, what we price, what we have written and what is still missing. {preds['count']} previews, {preds['shortest_words']}
words at the shortest.</p>
<div class="grid">
  <div class="k"><div class="n">{fx['count']}</div><div class="l">upcoming matches</div></div>
  <div class="k"><div class="n">{picks['count']}</div><div class="l">picks still to start</div></div>
  <div class="k"><div class="n">{picks['high']}</div><div class="l">high confidence, inside −250…+10000</div></div>
  <div class="k"><div class="n">{preds['count']}</div><div class="l">written predictions</div></div>
  <div class="k"><div class="n">{flags['count']}</div><div class="l">flagged for review</div></div>
</div>
<p class="sub" style="margin-top:-6px">The first two numbers are the desk's own counts, straight from
<code>data/slate26</code>. <a href="slate26/index.html">Full summary →</a></p>
<div class="cards">
  <a class="card" href="slate26/picks.html"><b>Picks →</b><span>Sport by sport, numbered and graded.</span></a>
  <a class="card" href="slate26/predictions.html"><b>Written predictions →</b><span>{preds['count']} previews, {preds['full']} with official statistics.</span></a>
  <a class="card" href="slate26/matches.html"><b>All {fx['count']} matches →</b><span>Every OLBG fixture with its source link.</span></a>
  <a class="card" href="slate26/sports/index.html"><b>By sport →</b><span>Fifteen pages, one per covered sport.</span></a>
</div>
<h2>Today's high-confidence picks</h2>
<div class="scroll"><table><thead><tr><th>Sport</th><th>Pick</th><th>Market</th><th class="num">Our price</th>
<th class="num">Our chance</th><th class="num">OLBG tips</th><th>Write-up</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="sub">Golf, Snooker, Darts, Rugby Union and Rugby League had no match priced on OLBG at capture, so they have no
picks — stated on every page rather than filled in.</p>
<div class="note-box"><p><b>Earlier desks.</b> This front door is the newest capture. The 24 October desk is still
published at <a href="compass/index.html">compass/index.html</a> — its summary, its
<a href="compass/picks.html">picks</a>, its <a href="compass/predictions.html">predictions</a>, its
<a href="compass/sports/index.html">sport pages</a> and its <a href="compass/flagged.html">flagged page</a> are unchanged,
including the 22:45Z capture that produced them. <a href="archive.html">Every earlier desk is listed in the archive.</a></p></div>
</div></main>
<footer><div class="wrap"><p>OLBG2 · 26 October 2026 desk · <a href="slate26/methodology.html">method</a> ·
<a href="slate26/sources.html">sources</a> · <a href="slate26/flagged.html">flagged for review</a></p></div></footer>
</body>
</html>
"""


if __name__ == "__main__":
    print("slate26_build:", build())
