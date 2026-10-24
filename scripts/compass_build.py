#!/usr/bin/env python3
"""Render the /compass/ desk (session arena/9f424dec-olbg2).

One clean dashboard: executive summary first, then picks, written predictions,
all matches, our lines, the odds band, the OLBG list, sources, method and the
Flagged for Review page, plus a page per sport. Every data row carries a link
to the official page it came from. Output is deterministic: same data in,
byte-identical pages out.
"""
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "compass"
OUT = ROOT / "compass"
AS_OF = "2026-10-24T22:45:00Z"
SHOWN_DATE = "24 October 2026"

SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
SLUG = {
    "Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
    "Cricket": "cricket", "Snooker": "snooker", "Darts": "darts", "Baseball": "baseball",
    "Gaelic Sports": "gaelic-sports", "Greyhounds": "greyhounds", "Tennis": "tennis",
    "Motor Racing": "motor-racing", "Handball": "handball", "Ice Hockey": "ice-hockey",
    "Basketball": "basketball", "Rugby League": "rugby-league",
}
NAV = [
    ("index.html", "Executive summary"),
    ("picks.html", "Picks"),
    ("predictions.html", "Written predictions"),
    ("matches.html", "All matches"),
    ("lines.html", "Our lines"),
    ("band.html", "Odds band"),
    ("sports/index.html", "By sport"),
    ("olbg.html", "OLBG list"),
    ("sources.html", "Sources"),
    ("methodology.html", "Method"),
    ("flagged.html", "Flagged for review"),
]

NO_LISTING_NOTE = {
    "Golf": "No OLBG golf tips at capture (22:35Z). PGA TOUR Bermuda Championship R4 and DP World Tour Genesis Championship R4 were in play on the official tours; context links below. No picks.",
    "Snooker": "No OLBG snooker tips at capture (22:35Z). The WST Northern Ireland Open final (Kyren Wilson, 13:00Z) had been listed earlier in the day and expired. No picks.",
    "Motor Racing": "No OLBG motor racing tips at capture (22:35Z). The F1 United States Grand Prix (Round 18, 25 Oct 20:00Z) had been listed earlier in the day and expired. No picks.",
}


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def host(url: str) -> str:
    if not url:
        return ""
    try:
        return url.split("//")[-1].split("/")[0]
    except Exception:
        return url


def page(title: str, body: str, active: str = "", prefix: str = "") -> str:
    nav = "".join(
        f'<a class="{"active" if h == active else ""}" href="{prefix}{h}">{t}</a>' for h, t in NAV
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(title)} — OLBG2 /compass/ desk</title>"
        f"<link rel='stylesheet' href='{prefix}assets/style.css'></head><body>"
        f"<div class='bar'><div class='wrap'><a class='brand' href='{prefix}index.html'>OLBG2 <span>/compass/ desk</span></a>"
        f"<nav>{nav}</nav></div></div>"
        f"<main class='wrap'>{body}"
        f"<footer class='footer'><p>Captured {SHOWN_DATE} 22:25–22:45 UTC by session arena/9f424dec-olbg2. "
        "All lines originated from official captured statistics or the OLBG community tip share "
        "(flagged where so). No bookmaker prices were read. "
        f"<a href='{prefix}flagged.html'>Flagged for review →</a></p></footer>"
        "</main></body></html>"
    )


def conf_badge(c: str) -> str:
    return f"<span class='conf {c}'>{c}</span>"


def fixture_link(f):
    name = f"{f['home']} v {f['away']}" if f["sport"] != "Baseball" else f"{f['away']} @ {f['home']}"
    return esc(name)


# --------------------------------------------------------------------------- index
def build_index():
    matches = load("fixtures.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    lines = load("lines.json")
    olbg = load("olbg.json")
    flagged = load("flagged.json")

    hs = [p for p in picks["picks"] if p["confidence"] == "high"]
    ms = [p for p in picks["picks"] if p["confidence"] == "medium"]
    top = (hs + ms)[:12]
    cards = []
    for p in top:
        cards.append(
            f"<a class='pickcard' href='predictions.html#{'pred-' + p['id'][len('pick-'):]}'>"
            f"<div class='pc-top'><span class='pc-sport'>{esc(p['sport'])}</span>{conf_badge(p['confidence'])}</div>"
            f"<div class='pc-match'>{esc(p['home'])} v {esc(p['away'])}</div>"
            f"<div class='pc-sel'>{esc(p['selection'])}</div>"
            f"<div class='pc-meta'>{esc(p['market'])} · {p['probability'] * 100:.1f}% · {esc(p['american_display'])}"
            + ("" if p["in_band"] else " <em>(outside band)</em>") + "</div>"
            f"<div class='pc-score'>Score <strong>{p['score']:.1f}</strong>/10</div>"
            f"<div class='pc-src'>Source: {esc(host(p['official_url']) or 'OLBG only — flagged')}</div></a>"
        )

    sport_cards = []
    for s in SPORTS:
        sp = picks["by_sport"].get(s, 0)
        sh = sum(1 for p in picks["picks"] if p["sport"] == s and p["confidence"] == "high")
        note = NO_LISTING_NOTE.get(s)
        extra = f"<div class='pc-note'>{esc(note)}</div>" if note else ""
        sport_cards.append(
            f"<a class='chip' href='sports/{SLUG[s]}.html'>{esc(s)}<span>{sp} picks"
            + (f" · {sh} high" if sh else "") + "</span></a>" + ("" if note else "")
        )

    fx_rows = []
    for m in matches["fixtures"][:12]:
        ol = m.get("olbg_listing")
        sel = ol["selection"] if ol else "—"
        fx_rows.append(
            f"<tr><td>{esc(m['sport'])}</td><td>{fixture_link(m)} <span class='mini'>{esc(m['competition'])}</span></td>"
            f"<td>{esc(m['start_utc'][:16].replace('T', ' '))}Z</td>"
            f"<td>{esc(sel)}</td>"
            f"<td>{'<a href=' + esc(m['official_url']) + '>' + esc(host(m['official_url'])) + '</a>' if m['official_url'] else '<span class=blank>— flagged</span>'}</td></tr>"
        )

    body = f"""
<h1>Executive summary — {SHOWN_DATE} (22:45Z capture)</h1>
<p class='sub'>{olbg['count']} OLBG-listed events across 15 sports · {matches['count']} fixture records ·
{lines['count']} originated lines ({lines['in_band']} inside the −250 to +10000 band) ·
{picks['count']} picks ({picks['high']} high / {picks['medium']} medium / {picks['low']} low) ·
{preds['count']} written previews · {flagged['count']} flags.
<a href='picks.html'>All picks →</a></p>

<h2>Where the picks live</h2>
<div class='wheregrid'>
  <a class='wherecard' href='picks.html'><b>Picks</b><span>Every selection, its price and its confidence grade.</span></a>
  <a class='wherecard' href='predictions.html'><b>Written predictions</b><span>Full previews for the {picks['high']} high-confidence picks, short lines for medium.</span></a>
  <a class='wherecard' href='matches.html'><b>All matches</b><span>Every OLBG-listed fixture with the official facts and source links.</span></a>
  <a class='wherecard' href='lines.html'><b>Our lines</b><span>Winner, handicap and total for each fixture, all originated.</span></a>
  <a class='wherecard' href='band.html'><b>Odds band</b><span>The −250 to +10000 test on every price we made.</span></a>
  <a class='wherecard' href='flagged.html'><b>Flagged for review</b><span>Blank values, OLBG data errors and unverified items.</span></a>
</div>

<h2>Top picks right now</h2>
<div class='pickgrid'>{''.join(cards)}</div>

<h2>By sport</h2>
<div class='chips'>{''.join(sport_cards)}</div>

<h2>Next on the board</h2>
<div class='table-wrap'><table class='data'><thead><tr><th>Sport</th><th>Fixture</th><th>Start (UTC)</th>
<th>Most-tipped (OLBG)</th><th>Official source</th></tr></thead><tbody>{''.join(fx_rows)}</tbody></table></div>
<p class='sub'><a href='matches.html'>All {matches['count']} fixtures →</a></p>
"""
    return page("Executive summary", body, "index.html")


# --------------------------------------------------------------------------- picks
def build_picks():
    picks = load("picks.json")
    rows = []
    for p in sorted(picks["picks"], key=lambda x: (-{"high": 2, "medium": 1, "low": 0}[x["confidence"]], -x["probability"])):
        band = "in band" if p["in_band"] else "outside band"
        src = f"<a href='{esc(p['official_url'])}'>{esc(host(p['official_url']))}</a>" if p["official_url"] else "<span class=blank>OLBG only — flagged</span>"
        rows.append(
            f"<tr><td>{esc(p['sport'])}</td><td>{esc(p['home'])} v {esc(p['away'])} <span class='mini'>{esc(p['start_utc'][:16].replace('T', ' '))}Z</span></td>"
            f"<td><strong>{esc(p['selection'])}</strong></td><td>{esc(p['market'])}</td>"
            f"<td class='num'>{p['probability'] * 100:.1f}%</td><td class='num'>{esc(p['american_display'])}</td>"
            f"<td>{band}</td><td>{conf_badge(p['confidence'])}</td><td class='num'>{p['score']:.1f}</td><td>{src}</td></tr>"
        )
    body = f"""
<h1>Picks — {picks['count']} total ({picks['high']} high / {picks['medium']} medium / {picks['low']} low)</h1>
<p class='sub'>One primary pick per fixture (plus run totals in Baseball). High-confidence prices sit between
−250 and +10000; prices outside the band are marked and the in-band alternative is preferred.
Every row links to the official page the pick's facts came from (OLBG-only rows are flagged).</p>
<div class='table-wrap'><table class='data'><thead><tr><th>Sport</th><th>Fixture</th><th>Selection</th>
<th>Market</th><th>Our chance</th><th>Our price</th><th>Band</th><th>Grade</th><th>Score</th><th>Official source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""
    return page("Picks", body, "picks.html")


# --------------------------------------------------------------------------- predictions
def build_predictions():
    preds = load("predictions.json")
    blocks = []
    for p in sorted(preds["predictions"], key=lambda x: (-{"high": 2, "medium": 1, "low": 0}[x["confidence"]], x["sport"])):
        facts = ""
        ol = ""
        if p["olbg_url"]:
            ol = f"<a href='{esc(p['olbg_url'])}'>OLBG event page</a> · "
        if p["official_url"]:
            src = f"<a href='{esc(p['official_url'])}'>{esc(host(p['official_url']))}</a>"
        else:
            src = "<span class=blank>no official page captured — flagged</span>"
        blocks.append(
            f'<section class="pred" id="{esc(p["id"])}">'
            f"<h3>{fixture_label(p)} {conf_badge(p['confidence'])} <span class='num'>{p['probability'] * 100:.1f}% \u00b7 {esc(p['american_display'])}</span></h3>"
            f"<p class='pred-sel'><strong>{esc(p['selection'])}</strong> \u2014 {esc(p['market'])} \u00b7 {esc(p['competition'])}</p>"
            f"<p>{esc(p['text'])}</p>"
            f"<p class='predfoot'>{ol}{src}</p></section>"
        )
    body = f"""
<h1>Written predictions — {preds['count']}</h1>
<p class='sub'>Full unique previews for the high-confidence picks (30+ words each), short lines for medium.
No pick text reuses another's opening; every block links to the official source behind it.</p>
{''.join(blocks)}
"""
    return page("Written predictions", body, "predictions.html")


def fixture_label(p):
    if p["sport"] == "Baseball":
        return f"{p['away']} @ {p['home']}"
    if p["sport"] in ("Golf", "Snooker", "Motor Racing"):
        return p["competition"]
    return f"{p['home']} v {p['away']}"


# --------------------------------------------------------------------------- matches
def build_matches():
    matches = load("fixtures.json")
    rows = []
    for m in matches["fixtures"]:
        ol = m.get("olbg_listing")
        if ol:
            ol_cell = (f"<a href='{esc(ol['url'])}'>{esc(ol['selection'] or '—')}</a>"
                       f" <span class='mini'>{esc(ol['tips'] or '')} ({esc(ol['pct'])}%)</span>"
                       f" · <span class='mini'>{esc(ol['displayed_time'])} ET</span>")
        else:
            ol_cell = "<span class=blank>not on OLBG hub at capture</span>"
        src = f"<a href='{esc(m['official_url'])}'>{esc(host(m['official_url']))}</a>" if m["official_url"] else "<span class=blank>— flagged</span>"
        facts = "".join(
            f"<li>{esc(f['claim'])}: {esc(f['value'])} <span class='mini'>({esc(host(f['source_url']))}"
            + (" · inherited 17:35Z" if f["source_key"] == "now_4a8390fe" else "") + ")</li>"
            for f in m["facts"]
        )
        blank = f"<p class='blank'>Blank/flagged: {esc(m['blank_reason'])}</p>" if m["blank_reason"] else ""
        rows.append(
            f"<details class='match'><summary><b>{fixture_link(m)}</b> <span class='mini'>{esc(m['competition'])} · {esc(m['start_utc'][:16].replace('T', ' '))}Z · {esc(m['venue'])}</span></summary>"
            f"<div class='mrow'>{ol_cell}</div>{blank}"
            f"<ul class='sources'>{facts}</ul><p class='predfoot'>{src}</p></details>"
        )
    body = f"""
<h1>All matches — {matches['count']} fixture records</h1>
<p class='sub'>Every event on the 15 OLBG sport hubs at 22:25–22:45Z (plus the official World Series Game 3).
Each record carries the official facts with links; anything OLBG-only or unconfirmable is blanked and
flagged. Expand a row for its facts.</p>
{''.join(rows)}
"""
    return page("All matches", body, "matches.html")


# --------------------------------------------------------------------------- lines
def build_lines():
    lines = load("lines.json")
    rows = []
    for l in lines["lines"]:
        band = "in band" if l["in_band"] else "outside band"
        src = f"<a href='{esc(l['official_url'])}'>{esc(host(l['official_url']))}</a>" if l["official_url"] else "<span class=blank>OLBG only — flagged</span>"
        rows.append(
            f"<tr><td>{esc(l['sport'])}</td><td>{esc(l['home'])} v {esc(l['away'])}</td>"
            f"<td><strong>{esc(l['selection'])}</strong></td><td>{esc(l['market'])}</td>"
            f"<td class='num'>{l['probability'] * 100:.1f}%</td><td class='num'>{l['decimal']}</td>"
            f"<td class='num'>{esc(l['american_display'])}</td><td>{band}</td>"
            f"<td>{esc(l['basis'])}</td><td>{conf_badge(l['confidence'])}</td><td>{src}</td></tr>"
        )
    body = f"""
<h1>Our lines — {lines['count']} originated prices ({lines['in_band']} in band)</h1>
<p class='sub'>Every price is ours: Poisson (NHL goals, MLB runs), normal margin (rugby, Gaelic, cricket,
basketball, handball, tennis), binomial legs (darts), class ladder (volleyball) or the shrunk OLBG
community share where no official fixture-level statistic exists (flagged). No bookmaker price was
read, scraped or compared.</p>
<div class='table-wrap'><table class='data'><thead><tr><th>Sport</th><th>Fixture</th><th>Selection</th>
<th>Market</th><th>Chance</th><th>Decimal</th><th>American</th><th>Band</th><th>Basis</th><th>Grade</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""
    return page("Our lines", body, "lines.html")


# --------------------------------------------------------------------------- band
def build_band():
    lines = load("lines.json")
    ib = [l for l in lines["lines"] if l["in_band"]]
    ob = [l for l in lines["lines"] if not l["in_band"]]
    rows = []
    for l in sorted(ib, key=lambda x: x["american"])[:60]:
        rows.append(f"<tr><td>{esc(l['sport'])}</td><td>{esc(l['selection'])} <span class='mini'>{esc(l['home'])} v {esc(l['away'])}</span></td>"
                    f"<td class='num'>{l['probability'] * 100:.1f}%</td><td class='num'>{esc(l['american_display'])}</td></tr>")
    obrows = []
    for l in sorted(ob, key=lambda x: x["american"])[:40]:
        obrows.append(f"<tr><td>{esc(l['sport'])}</td><td>{esc(l['selection'])} <span class='mini'>{esc(l['home'])} v {esc(l['away'])}</span></td>"
                      f"<td class='num'>{l['probability'] * 100:.1f}%</td><td class='num'>{esc(l['american_display'])}</td></tr>")
    body = f"""
<h1>Odds band — the −250 to +10000 test</h1>
<p class='sub'>{len(ib)} of {lines['count']} originated prices fall inside the requested band; {len(ob)} fall
outside (mostly heavy favourites at −250 or shorter). Picks outside the band carry the in-band
alternative where one exists (e.g. the −1.5 puck line for a −500 money line).</p>
<h2>Inside the band (shortest first, top 60)</h2>
<div class='table-wrap'><table class='data'><thead><tr><th>Sport</th><th>Selection</th><th>Chance</th><th>American</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>Outside the band (top 40)</h2>
<div class='table-wrap'><table class='data'><thead><tr><th>Sport</th><th>Selection</th><th>Chance</th><th>American</th></tr></thead><tbody>{''.join(obrows)}</tbody></table></div>
"""
    return page("Odds band", body, "band.html")


# --------------------------------------------------------------------------- olbg
def build_olbg():
    olbg = load("olbg.json")
    rows = []
    for r in olbg["listings"]:
        rows.append(
            f"<tr><td>{esc(r['sport'])}</td><td><a href='{esc(r['url'])}'>{esc(r['event'])}</a></td>"
            f"<td>{esc(r['displayed_time'])} <span class='mini'>ET</span></td><td>{esc(r['market'])}</td>"
            f"<td><strong>{esc(r['selection'] or '—')}</strong></td><td class='num'>{esc(r['tips'] or '—')}</td>"
            f"<td class='num'>{r['pct'] if r['pct'] is not None else '—'}%</td></tr>"
        )
    status = "".join(f"<li><b>{esc(k)}</b>: {esc(v)}</li>" for k, v in olbg["capture"]["sport_status"].items())
    body = f"""
<h1>OLBG list — {olbg['count']} events captured 22:25–22:45Z</h1>
<p class='sub'>Verbatim from the 15 sport hubs (display times are US Eastern, as rendered to the
capture tool; verified against the official NHL schedule). Event links open the OLBG event page.</p>
<ul class='excluded'>{status}</ul>
<div class='table-wrap'><table class='data'><thead><tr><th>Sport</th><th>Event</th><th>Displayed</th>
<th>Market</th><th>Most-tipped</th><th>Tips</th><th>Share</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
"""
    return page("OLBG list", body, "olbg.html")


# --------------------------------------------------------------------------- sources
def build_sources():
    sources = load("sources.json")
    rows = []
    for s in sources["sources"]:
        if s["url"].startswith("http"):
            cell = f"<a href='{esc(s['url'])}'>{esc(s['name'])}</a>"
        else:
            cell = f"<code>{esc(s['url'])}</code> — {esc(s['name'])}"
        rows.append(f"<tr><td>{esc(s['key'])}</td><td>{cell}</td>"
                    f"<td>{esc(s['captured_utc'])}</td><td>{esc(s['note'])}</td></tr>")
    body = f"""
<h1>Sources — {sources['count']}</h1>
<p class='sub'>Every official URL captured this session (22:25–23:00Z) plus the same-day 17:35Z
official capture inherited from session arena/4a8390fe-olbg2, which was re-corroborated where this
session re-fetched the same source. Facts on each match page name the source key that proved them.</p>
<div class='table-wrap'><table class='data'><thead><tr><th>Key</th><th>Source</th><th>Captured</th><th>What it proves</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
"""
    return page("Sources", body, "sources.html")


# --------------------------------------------------------------------------- methodology
def build_methodology():
    body = f"""
<h1>Method</h1>
<p class='sub'>Same house methodology as the rest of the repository (see METHODOLOGY.md at the repo root),
applied to the 22:45Z capture.</p>
<h2>Pricing families</h2>
<ul class='steps'>
<li><b>Poisson (NHL)</b> — expected goals = geometric mean of each team's goals-for rate and the
opponent's goals-against rate, against the league average (30 captured teams, flag cmp-15), with home
multipliers 1.06/0.98; regulation ties split evenly because the money line settles with overtime.
Puck line −1.5/+1.5 and a half-goal game total are priced from the same matrix.</li>
<li><b>Poisson runs (MLB)</b> — expected runs from each club's 2026 run rate vs the opponent's
conceded rate (baseline 4.5 runs/team/game; no official league-average source was captured), scaled
for both starters' season ERA/WHIP (official StatsAPI); extra innings settle the money line so ties
split evenly. Run line ±1.5 and a half-run total are priced from the same matrix.</li>
<li><b>Normal margin (rugby, Gaelic, cricket, basketball, handball, tennis)</b> — a margin
distribution (sigma 12 rugby / 8 Gaelic / 25 cricket runs / 8.0 NBA points / 6.5 handball goals)
centred on a home advantage (2.5 / 1.5 / 2.0 / +4 points / 1.5 goals) shifted by edge terms set from
the sourced facts on each record (form, series position, venue, squad quality). Handball adds the
3-way draw as the mass inside ±1 goal.</li>
<li><b>Binomial legs (darts)</b> — leg win rate from the sourced round results and match averages;
match probability is the binomial tail to 10 legs (best of 19, official format).</li>
<li><b>Class ladder (volleyball)</b> — 62% (70% for top-two vs clearly weaker) for the better
established club; no set-level statistics were captured.</li>
<li><b>OLBG community line</b> — where no official fixture-level statistic exists, the price is the
tip share shrunk toward 50% (weight 0.85 / 0.70 / 0.50 by sample size, clamped 30–72%, 30–60% for
three-or-fewer tips) and flagged as unverified. Ante-post outrights are capped at low.</li>
</ul>
<h2>Confidence</h2>
<ul class='steps'>
<li><b>High</b> — numeric family, our chance ≥ 62%, price inside −250…+10000. Totals capped at medium.
Unverified-event fixtures and the two-game NBA sample are capped at medium (flags cmp-07, cmp-16).</li>
<li><b>Medium</b> — numeric ≥ 55%, or community/ladder ≥ 70%.</li>
<li><b>Low</b> — everything else.</li>
<li><b>Score</b> = 10 × chance × basis shade (1.0 numeric, 0.8 community/ladder), capped at 7.5 in band.</li>
</ul>
<h2>Honesty rules</h2>
<ul class='steps'>
<li>No bookmaker price is read, scraped or compared — the odds shown on nhl.com schedule rows are ignored.</li>
<li>Unconfirmable values are left blank and carried to <a href='flagged.html'>Flagged for review</a>.</li>
<li>OLBG display times (US Eastern) are never used as the official time; official kickoffs win.</li>
</ul>
"""
    return page("Method", body, "methodology.html")


# --------------------------------------------------------------------------- flagged
def build_flagged():
    flagged = load("flagged.json")
    rows = []
    sev_order = {"data-error": 0, "time": 1, "data-quality": 2, "unverified": 3, "coverage": 4, "method": 5, "market": 6}
    for it in sorted(flagged["items"], key=lambda x: (sev_order.get(x["severity"], 9), x["id"])):
        src = f"<a href='{esc(it['source'])}'>{esc(host(it['source']))}</a>" if it["source"] else "—"
        rows.append(f"<tr><td>{esc(it['id'])}</td><td><span class='conf low'>{esc(it['severity'])}</span></td>"
                    f"<td>{esc(it['sport'])}</td><td>{esc(it['text'])}</td><td>{src}</td></tr>")
    body = f"""
<h1>Flagged for review — {flagged['count']} items</h1>
<p class='sub'>Everything blank, corrected, unconfirmed or anomalous, with the source that was
checked. Nothing here blocks publication; each flag names its source so a human can re-verify.</p>
<div class='table-wrap'><table class='data'><thead><tr><th>Id</th><th>Type</th><th>Sport</th><th>Issue</th><th>Source checked</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""
    return page("Flagged for review", body, "flagged.html")


# --------------------------------------------------------------------------- sport pages
def build_sport(sport: str):
    matches = load("fixtures.json")["fixtures"]
    picks = load("picks.json")["picks"]
    preds = load("predictions.json")["predictions"]
    olbg = load("olbg.json")["listings"]
    lines = load("lines.json")["lines"]
    flagged = load("flagged.json")["items"]

    fx = [m for m in matches if m["sport"] == sport]
    pk = [p for p in picks if p["sport"] == sport]
    pd = [t for t in preds if t["sport"] == sport]
    ol = [r for r in olbg if r["sport"] == sport]
    ln = [l for l in lines if l["sport"] == sport]
    fl = [i for i in flagged if i["sport"] == sport]

    pk_rows = []
    for p in sorted(pk, key=lambda x: (-{"high": 2, "medium": 1, "low": 0}[x["confidence"]], -x["probability"])):
        band = "in band" if p["in_band"] else "outside band"
        src = f"<a href='{esc(p['official_url'])}'>{esc(host(p['official_url']))}</a>" if p["official_url"] else "<span class=blank>OLBG only — flagged</span>"
        pk_rows.append(f"<tr><td>{esc(p['home'])} v {esc(p['away'])} <span class='mini'>{esc(p['start_utc'][:16].replace('T', ' '))}Z</span></td>"
                       f"<td><strong>{esc(p['selection'])}</strong></td><td>{esc(p['market'])}</td>"
                       f"<td class='num'>{p['probability'] * 100:.1f}%</td><td class='num'>{esc(p['american_display'])}</td>"
                       f"<td>{band}</td><td>{conf_badge(p['confidence'])}</td><td>{src}</td></tr>")

    pd_blocks = []
    for t in pd:
        src = f"<a href='{esc(t['official_url'])}'>{esc(host(t['official_url']))}</a>" if t["official_url"] else "<span class=blank>no official page captured — flagged</span>"
        pd_blocks.append(f"<section class='pred'><h3>{fixture_label(t)} {conf_badge(t['confidence'])}</h3>"
                         f"<p><strong>{esc(t['selection'])}</strong> — {esc(t['market'])}</p><p>{esc(t['text'])}</p>"
                         f"<p class='predfoot'>{src}</p></section>")

    fx_rows = []
    for m in fx:
        o = m.get("olbg_listing")
        ol_cell = (f"{esc(o['selection'] or '—')} <span class='mini'>{esc(o['tips'] or '')}</span>" if o
                   else "<span class=blank>not listed</span>")
        src = f"<a href='{esc(m['official_url'])}'>{esc(host(m['official_url']))}</a>" if m["official_url"] else "<span class=blank>— flagged</span>"
        fx_rows.append(f"<tr><td>{fixture_link(m)} <span class='mini'>{esc(m['competition'])}</span></td>"
                       f"<td>{esc(m['start_utc'][:16].replace('T', ' '))}Z</td><td>{ol_cell}</td><td>{src}</td></tr>")

    note = NO_LISTING_NOTE.get(sport)
    note_html = f"<p class='sub note'>{esc(note)}</p>" if note else ""

    body = f"""
<h1>{esc(sport)} — {len(fx)} fixtures · {len(pk)} picks · {len(ln)} lines</h1>
{note_html}
{'<h2>Picks</h2><div class="table-wrap"><table class="data"><thead><tr><th>Fixture</th><th>Selection</th><th>Market</th><th>Chance</th><th>Price</th><th>Band</th><th>Grade</th><th>Source</th></tr></thead><tbody>' + ''.join(pk_rows) + '</tbody></table></div>' if pk_rows else '<h2>Picks</h2><p class="sub">No picks this capture — see the note above.</p>'}
{'<h2>Written predictions</h2>' + ''.join(pd_blocks) if pd_blocks else ''}
<h2>Fixtures</h2>
<div class='table-wrap'><table class='data'><thead><tr><th>Fixture</th><th>Start (UTC)</th><th>OLBG most-tipped</th><th>Official source</th></tr></thead><tbody>{''.join(fx_rows) if fx_rows else '<tr><td colspan="4" class="blank">No OLBG-listed fixtures at capture.</td></tr>'}</tbody></table></div>
{'<h2>Flags on this sport</h2><ul class="excluded">' + ''.join(f"<li>{esc(i['text'])}</li>" for i in fl) + '</ul>' if fl else ''}
"""
    return page(f"{sport} — /compass/", body, "sports", prefix="../")


def build_sports_index():
    cards = []
    for s in SPORTS:
        n = len([1 for _ in []])
        cards.append(f"<a class='chip' href='{SLUG[s]}.html'>{esc(s)}</a>")
    body = f"""
<h1>By sport</h1>
<p class='sub'>The 15 sports from the brief, each with its fixtures, picks, lines and flags.</p>
<div class='chips'>{''.join(cards)}</div>
"""
    return page("By sport", body, "sports/index.html", prefix="../")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    css = (ROOT / "now" / "assets" / "style.css").read_text(encoding="utf-8")
    (OUT / "assets" / "style.css").write_text(css, encoding="utf-8")
    (OUT / "index.html").write_text(build_index(), encoding="utf-8")
    (OUT / "picks.html").write_text(build_picks(), encoding="utf-8")
    (OUT / "predictions.html").write_text(build_predictions(), encoding="utf-8")
    (OUT / "matches.html").write_text(build_matches(), encoding="utf-8")
    (OUT / "lines.html").write_text(build_lines(), encoding="utf-8")
    (OUT / "band.html").write_text(build_band(), encoding="utf-8")
    (OUT / "olbg.html").write_text(build_olbg(), encoding="utf-8")
    (OUT / "sources.html").write_text(build_sources(), encoding="utf-8")
    (OUT / "methodology.html").write_text(build_methodology(), encoding="utf-8")
    (OUT / "flagged.html").write_text(build_flagged(), encoding="utf-8")
    (OUT / "sports" / "index.html").write_text(build_sports_index(), encoding="utf-8")
    for s in SPORTS:
        (OUT / "sports" / f"{SLUG[s]}.html").write_text(build_sport(s), encoding="utf-8")
    print("compass_build: 27 pages written to /compass/")


if __name__ == "__main__":
    main()
