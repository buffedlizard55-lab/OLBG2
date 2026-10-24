#!/usr/bin/env python3
"""Build a compact evidence-first 15-sport GitHub Pages dashboard at /vantage/.

All public rows are generated from the checked-in frozen first-page OLBG snapshot,
fixture/fact ledger, originated estimates, write-ups and the review queue.
Only the one fully written, future-at-cutoff, independently price-checked high pick
appears in the executive spotlight. Browser-time expiry prevents a static snapshot
from continuing to display a started event as a current highlight.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vantage"
OUT = ROOT / "vantage"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
NAV = [("index.html", "Executive summary"), ("picks.html", "Picks & analysis"),
       ("matches.html", "All matches"), ("lines.html", "Originated lines"),
       ("sports/index.html", "Sports"), ("flagged.html", "Flagged for Review")]


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def domain(u: str) -> str:
    return urlsplit(u).hostname or "source"


def link(u, label=None, *, css="", role="") -> str:
    if not u:
        return '<span class="blank" aria-label="Unverified">—</span>'
    assert u.startswith("https://"), u
    return f'<a class="{e(css)}" href="{e(u)}" rel="noopener noreferrer" target="_blank" title="{e(role)}">{e(label or domain(u))}<span class="external" aria-hidden="true">↗</span></a>'


def odd(x) -> str:
    if x is None:
        return "—"
    return f"+{x}" if x > 0 else str(x)


def pct(p) -> str:
    return "—" if p is None else f"{p * 100:.1f}%"


def badge(text, kind=None) -> str:
    return f'<span class="badge {e(kind or slug(text))}">{e(text)}</span>'


def local_nav(path, prefix="") -> str:
    menu = ''.join(f'<a href="{prefix}{e(u)}" class="{"active" if path == u else ""}">{e(t)}</a>' for u, t in NAV)
    return menu


def shell(title: str, current: str, body: str, *, prefix="", subtitle="") -> str:
    nav = local_nav(current, prefix)
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Vantage / OLBG2</title>
<meta name="description" content="Dated 15-sport OLBG evidence desk: executive summary, written match predictions, official fixture links, fair lines and flagged uncertainties.">
<link rel="stylesheet" href="{prefix}assets/style.css">
<script src="{prefix}assets/app.js" defer></script>
</head><body>
<a class="skip" href="#content">Skip to content</a>
<header class="header"><div class="shell header-inner">
<a class="brand" href="{prefix}index.html"><span class="brand-mark">V</span><span><b>Vantage</b><small>OLBG2 · 15-sport desk</small></span></a>
<nav class="nav" aria-label="Primary navigation">{nav}</nav>
</div></header>
<div class="ribbon"><div class="shell">Evidence snapshot · <b>24 Oct 2026, 17:45 UTC</b> <span>· First visible OLBG page only · Never a live odds feed</span></div></div>
<main id="content" class="shell"><div class="page-eyebrow">{e(subtitle or title)}</div>
{body}</main>
<footer class="footer"><div class="shell footer-inner"><span><b>Vantage</b> · evidence-led match research</span>
<span>Captured data are dated; full OLBG coverage and offered OLBG prices remain unconfirmed. No guarantees or betting advice. 18+.</span>
<span>{link('https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md', 'Shared coordination')} · <a href="{prefix}methodology.html">Methodology</a> · <a href="{prefix}sources.html">Official sources</a> · <a href="{prefix}audit.html">Repo audit</a></span></div></footer>
</body></html>'''


def notice(text, kind="info"):
    return f'<div class="notice {e(kind)}">{text}</div>'


def stats_grid(entries):
    return '<div class="stats">' + ''.join(f'<div class="metric"><strong>{e(value)}</strong><span>{e(label)}</span><small>{e(note)}</small></div>' for value, label, note in entries) + '</div>'


def olbg_cell(row):
    return (f'{link(row["olbg_event_url"], row["olbg_listing"], css="event")}'
            f'<div class="sub">OLBG: {e(row["olbg_displayed_time"])} · {e(row["olbg_top_market"])} · {e(row["olbg_top_selection"])}</div>')


def official_cell(row):
    if not row["official_confirmed"]:
        return '<span class="blank">— official fixture not established</span>'
    desc = e(row["official_home"]) + (f' <span class="vs">v</span> {e(row["official_away"])}' if row["official_away"] else "")
    return f'<b>{desc}</b><div class="sub">{e(row["competition"])}{", " + e(row["official_venue"]) if row["official_venue"] else ""}</div>'


def start_cell(row):
    utc = row["official_start_utc"]
    if not utc:
        return (f'{e(row["official_date"])}<div class="sub">time — unconfirmed</div>' if row["official_confirmed"] and row["official_date"]
                else '<span class="blank">— unconfirmed</span>')
    return f'<time datetime="{e(utc)}">{e(utc.replace("T", " ").replace("Z", " UTC"))}</time>'


def proof_cell(row):
    if row["official_confirmed"]:
        return f'{link(row["fixture_source_url"], "Official fixture", role="Governing-body or league record used for this pairing")}<div class="sub">{e(row["official_status"])}</div>'
    return (f'{link(row["review_target_url"], "Official check target", role="Not evidence for the OLBG listing")}<div class="sub warn-text">Not evidence for this event</div>')


def selection_cell(row, *, prefix=""):
    if not row["primary_selection"]:
        return f'<span class="blank">— no independently supported selection</span><div class="sub">{e(row["line_reason"])}</div>'
    p = f'predictions.html#preview-{slug(row["id"])}'
    return (f'<a class="selection" href="{prefix}{p}">{e(row["primary_selection"])} → analysis</a>'
            f'<div class="sub">{e(row["primary_market"])} · {pct(row["primary_probability"])} · fair {odd(row["primary_fair_american"])} · {badge(row["primary_confidence"])}</div>')


def matches_table(rows, *, prefix="") -> str:
    heads = ("OLBG listing / discovery", "Officially confirmed fixture", "Official start", "Our selection & analysis", "Official source / review", "State")
    body = []
    for r in rows:
        state = ("Confirmed + priced" if r["primary_selection"] else
                 "Confirmed / unpriced" if r["official_confirmed"] else "Unverified listing")
        official_row_link = f'{prefix}sports/{slug(r["sport"])}.html'
        body.append(
            f'<tr data-sport="{e(slug(r["sport"]))}" data-status="{e(slug(state))}" '
            f'data-search="{e(" ".join(str(v or "") for v in (r["olbg_listing"], r["official_home"], r["official_away"], r["sport"], r["competition"])))}">'
            f'<td><a class="sub sport-tag" href="{official_row_link}">{e(r["sport"])}</a><br>{olbg_cell(r)}</td>'
            f'<td>{official_cell(r)}</td><td>{start_cell(r)}</td>'
            f'<td>{selection_cell(r, prefix=prefix)}</td><td>{proof_cell(r)}</td>'
            f'<td>{badge(state, "good" if r["primary_selection"] else "warn" if r["official_confirmed"] else "muted")}</td></tr>'
        )
    return f'''<div class="table-scroller"><table class="table"><thead><tr>{''.join(f'<th scope="col">{e(h)}</th>' for h in heads)}</tr></thead>
<tbody>{''.join(body)}</tbody></table></div>'''


def filters(sport=True, status=True, query=True):
    return f'''<div class="filters" aria-label="Table filters">
{('<label>Find a match<input id="filter-search" type="search" placeholder="Team, sport, competition…"></label>' if query else '')}
{('<label>Sport<select id="filter-sport"><option value="">All 15 sports</option>' + ''.join(f'<option value="{slug(s)}">{e(s)}</option>' for s in SPORTS) + '</select></label>' if sport else '')}
{('<label>Evidence<select id="filter-status"><option value="">All states</option><option value="confirmed-priced">Priced</option><option value="confirmed-unpriced">Official, unpriced</option><option value="unverified-listing">Unverified listing</option></select></label>' if status else '')}
<span id="filter-count" role="status"></span></div>'''


def label_fixture(p):
    return f'{e(p["official_away"])} <span class="vs">@</span> {e(p["official_home"])}' if p["official_away"] else e(p["official_home"])


def cards_from_predictions(previews, picks, *, prefix="", compact=False):
    out = []
    by_pick = {p["id"]: p for p in picks}
    for pred in previews:
        p = by_pick[pred["pick_id"]]
        sources = ''.join(f'<li>{link(url, domain(url))}</li>' for url in pred["sources"])
        observed = (f'{odd(p["observed_american"])} <span class="sub">NHL partner snapshot</span>' if p["observed_american"] is not None
                    else '<span class="blank">— not captured</span>')
        band = badge("Both fair + observed in band", "good") if p["confidence"] == "high" and p["fair_in_band"] and p["observed_in_band"] else badge("Not a featured band pick", "muted")
        out.append(f'''<article class="prediction {e(p['confidence'])}" id="preview-{slug(pred['fixture_id'])}" data-start="{e(p['start_utc'])}" data-archive-badge>
<div class="prediction-head"><span class="kicker">{e(p['sport'])} · {e(p['competition'])}</span>{badge(p['confidence'])}{band}</div>
<h3>{e(p['selection'])} <span class="soft">· {e(p['market'])}</span></h3>
<p class="fixtureline">{label_fixture(p)} · Official start <time datetime="{e(p['start_utc'])}">{e(p['start_utc'].replace('T',' ').replace('Z',' UTC'))}</time> <span class="expiry" aria-live="polite"></span></p>
<div class="pricebar"><div><span>Our estimate</span><b>{pct(p['probability'])} · {odd(p['fair_american'])}</b></div>
<div><span>Observed partner quote</span><b>{observed}</b></div><div><span>OLBG offered odds</span><b class="blank">— unconfirmed</b></div></div>
<p class="analysis">{e(pred['text'])}</p>
<div class="sources-block"><div><b>Official source trail</b><ul>{sources}</ul></div>
<div><b>Availability / injuries</b><p>Injuries: <span class="blank">— unconfirmed</span><br>{e(pred['evidence_note'])}</p></div></div>
<p class="deep-link">{link(p['olbg_event_url'], 'Open OLBG event')} · <a href="{prefix}lines.html">See all originated markets</a></p>
</article>''')
    return ''.join(out)


def index_page(matches, lines, picks, predictions, flags, taxonomy):
    m = matches["matches"]
    all_picks = picks["picks"]
    preds = predictions["predictions"]
    featured = [p for p in all_picks if p["confidence"] == "high" and p["fair_in_band"] and p["observed_in_band"] is True]
    featured_ids = {p["id"] for p in featured}
    featured_previews = [x for x in preds if x["pick_id"] in featured_ids]
    today_count = sum((r["official_start_utc"] or "").startswith("2026-10-24") and r["primary_selection"] is not None for r in m)
    missing_high = 5 * len(SPORTS) - sum(p["confidence"] == "high" for p in all_picks)
    feature_area = cards_from_predictions(featured_previews, all_picks, compact=True) if featured else '<div class="empty">No high-confidence, in-band pick cleared all gates in this snapshot. The board is intentionally blank rather than padded.</div>'
    for p in featured:
        assert any(x["pick_id"] == p["id"] for x in featured_previews)
    cards = []
    n_by = Counter(r["sport"] for r in m)
    c_by = Counter(r["sport"] for r in m if r["official_confirmed"])
    p_by = Counter(p["sport"] for p in all_picks)
    w_by = Counter(x["sport"] for x in preds if x["confidence"] == "high")
    for s in SPORTS:
        cards.append(f'<a class="sport-card" href="sports/{slug(s)}.html"><strong>{e(s)} <span>↗</span></strong>'
                     f'<small>{n_by[s]} OLBG · {c_by[s]} official · {p_by[s]} priced</small>'
                     f'<em>{w_by[s]} of 5 high write-ups</em></a>')
    featured_date = '2026-10-24T23:00:00Z'
    hero = f'''<section class="hero"><div><p class="eyebrow">OLBG / researched independently / 15 sports</p>
<h1>Know the match.<br><span>See the pick.</span></h1>
<p>Executive summary for the 24 October capture. Only a fully written, officially sourced match prediction with a confirmed future start and a separately captured in-band quote earns the lead spot.</p>
<div class="hero-actions"><a class="button prime" href="picks.html">Read the picks & analysis →</a><a class="button ghost" href="matches.html">Browse all {matches['listings']} OLBG listings</a></div></div>
<div class="hero-card"><div>At capture · {e(matches['as_of_utc'])}</div>
<strong>{len(featured)} qualified</strong><span>high-confidence in-band analysis</span><hr>
<p><b>{today_count}</b> priced records start on 24 Oct UTC · <b>{len(preds)}</b> unique 30+ word analyses in this desk</p></div></section>'''
    body = f'''{hero}
{notice(f'<b>Executive read:</b> this is a first-page OLBG discovery extract, not an exhaustive match inventory. {matches["listings"] - 1} OLBG listings were copied from a documented 24 October source session, one Hurling listing was read directly here, and the fifteen primary hubs were spot-checked again; only {matches["confirmed"]} events were matched to official records. {len(featured)} high in-band analytical selection(s) met the evidence gate. The other {missing_high} high write-ups needed for a five-per-sport target do not exist and were not invented. <a href="flagged.html">See every gap and irregularity</a>.', 'important')}
{stats_grid([(len(featured), 'High + band shortlist', 'with a written prediction'), (matches['listings'], 'OLBG first-page listings', 'not the entire active slate'), (matches['confirmed'], 'Officially matched', 'fixture, date or session sourced'), (matches['priced'], 'Priced match records', f'{lines["count"]} fair market selections'), (len(preds), 'Written analyses', 'one for every displayed pick'), (flags['count'], 'Flagged for Review', 'row-level blanks included')])}
<section class="section-title"><div><div class="eyebrow">01 / Executive pick</div><h2>Highest confidence, no guessing</h2><p>Only selections with separate observable odds and a 30+ word official-source analysis appear here. Our price is not an OLBG offer.</p></div><a class="text-link" href="band.html">Price-band details →</a></section>
<div data-expire-group class="feature-board">{feature_area}</div><div class="after-expiry" hidden role="status">The highlighted fixture has started since this snapshot. It remains available in <a href="predictions.html">the dated analysis archive</a>, not as a current pick.</div>
<section class="section-title"><div><div class="eyebrow">02 / Find a match</div><h2>Every captured listing, one table</h2><p>OLBG discovery and official confirmation are separate columns. Unconfirmed values are blank, with an official site supplied as a review target only.</p></div><a class="text-link" href="matches.html">All 96 rows →</a></section>
{matches_table(sorted([r for r in m if r['primary_selection']], key=lambda r: (r['official_start_utc'] or '', r['sport']))[:8])}
<section class="section-title"><div><div class="eyebrow">03 / By category</div><h2>Exactly the 15 covered sports</h2><p>No football, racing horses, eSports or Aussie Rules in this current board. A zero is a disclosed gap, not a synthetic prediction.</p></div><a class="text-link" href="sports/index.html">Full sport index →</a></section>
<div class="sport-grid">{''.join(cards)}</div>
<section class="section-title"><div><div class="eyebrow">04 / The evidence boundary</div><h2>What the figures mean</h2></div></section>
<div class="explainer-grid"><div><b>Our own fair odds</b><p>Poisson and normal approximations from a dated official statistical snapshot. They are estimates with explicit assumptions, not market offers.</p><a href="methodology.html">See calculations →</a></div><div><b>Observed league quote</b><p>The NHL schedule feed carried a named partner's money-line quote. It is separate from our fair line and not evidence of an OLBG or still-available price.</p><a href="sources.html">Source register →</a></div><div><b>Blank means unknown</b><p>A sport, venue, lineup, injury or bookmaker quote not confirmed against an official source remains empty and appears in the review queue.</p><a href="flagged.html">Flagged for Review →</a></div></div>
<noscript>{notice('JavaScript is off. Read the frozen capture date above; some matches may have started since this page was created.', 'important')}</noscript>'''
    return shell("Executive summary", "index.html", body, subtitle="24 OCT / EXECUTIVE BRIEF")


def matches_page(matches):
    rows = matches["matches"]
    by_sport = Counter(x["sport"] for x in rows)
    body = f'''<h1>All captured OLBG matches & events</h1>
<p class="lead">{len(rows)} first-page OLBG listings in {len(by_sport)} sports. Official fixture values are filled only for {matches['confirmed']} independently matched events. In the other {matches['unknown']}, the official fixture/date/start cells are intentionally blank. {matches['priced']} have enough input for an independently priced future match.</p>
{notice('<b>Scope limit:</b> “Load More Tips” on OLBG means this is not a full slate. OLBG dates and most-tipped outcomes belong in a discovery column; they do not confirm league schedules or chances. The official link on an unverified row is a <em>review target only</em>.','important')}
{filters()}{matches_table(rows)}
<p class="fineprint">Rows stay visible after the match for auditing. This table is dated at {e(matches['as_of_utc'])}; filter labels describe that snapshot, not real-time availability.</p>'''
    return shell("All matches", "matches.html", body, subtitle="MATCH DIRECTORY / FIRST-PAGE EXTRACT")


def picks_page(picks, preds):
    all_picks = picks["picks"]
    previews = preds["predictions"]
    high = [x for x in previews if x["confidence"] == "high"]
    rest = [x for x in previews if x["confidence"] != "high"]
    head = f'''<h1>Picks with analysis, not one-word picks</h1>
<p class="lead">{len(previews)} independently written, source-linked 30+ word analyses. One is high and fits the fair -250…+10000 window with a separate league-served quote also in that band. A quote on the OLBG site itself was not captured. Other estimates are clearly graded medium or low.</p>
{notice('<b>Temporal gate:</b> all listed selections had official starts at least 90 minutes after the 17:45 UTC cutoff. The browser labels those that have since started. Unverified, started, and unpriced events do not appear on this page.','important')}
<div class="tabs-line"><a href="#high">High · {len(high)}</a><a href="#other">Medium / low · {len(rest)}</a><a href="band.html">Odds-band board</a></div>'''
    section_high = f'<section id="high"><div class="section-title"><div><div class="eyebrow">Top line</div><h2>High-confidence pick</h2></div></div>{cards_from_predictions(high, all_picks)}</section>'
    section_rest = f'<section id="other"><div class="section-title"><div><div class="eyebrow">Second look</div><h2>Medium and low research</h2><p>Published for transparency; neither grade is promoted to high to reach a daily quota.</p></div></div><div class="prediction-grid">{cards_from_predictions(rest, all_picks)}</div></section>'
    return shell("Picks & analysis", "picks.html", head + section_high + section_rest,
                 subtitle="WRITTEN PICKS / CONFIDENCE SEPARATED")


def predictions_page(preds, picks):
    all_picks = picks["picks"]
    cards = cards_from_predictions(preds["predictions"], all_picks)
    body = f'''<h1>Full written prediction archive</h1><p class="lead">{len(preds['predictions'])} individual previews. Each names its betting selection, explains relevant official statistics, cites the specific official pages and makes no unconfirmed injury assertion.</p>
{notice('<b>Dated archive:</b> an event can start after this snapshot. A browser-time badge indicates expiry; no text here is automatically re-researched or updated after publication.','important')}
<div class="prediction-grid">{cards}</div>'''
    return shell("Written predictions", "predictions.html", body, subtitle="FULL ANALYSIS / NOT A LIVE FEED")


def lines_page(lines, matches):
    fixtures = {p["fixture_id"]: p for p in lines["detail"]}
    source_url = {r["id"]: r["olbg_event_url"] for r in matches["matches"]}
    rows = []
    for l in lines["lines"]:
        f = fixtures[l["fixture_id"]]
        rows.append(f'''<tr data-sport="{slug(l['sport'])}" data-search="{e(f['away']+' '+f['home']+' '+l['selection']+' '+l['market'])}">
<td><a href="sports/{slug(l['sport'])}.html">{e(l['sport'])}</a><br><b>{e(f['away'])} @ {e(f['home'])}</b><div class="sub">{e(l['start_utc'])}</div></td>
<td>{e(l['market'])}</td><td><strong>{e(l['selection'])}</strong></td><td>{pct(l['probability'])}</td>
<td><b>{odd(l['fair_american'])}</b><div class="sub">our estimate</div></td>
<td>{('<b>'+odd(l['observed_american'])+'</b><div class="sub">FanDuel, NHL feed</div>') if l['observed_american'] is not None else '<span class="blank">— unconfirmed</span>'}</td>
<td>{badge('Fair in band' if l['fair_in_band'] else 'Fair outside band', 'good' if l['fair_in_band'] else 'warn')}
<div class="sub">{('Observed '+('in band' if l['observed_in_band'] else 'outside band')) if l['observed_in_band'] is not None else 'Observed odds unavailable'}</div></td>
<td>{link(l['official_source_url'], 'Fixture')} · {link(l['stats_source_url'], 'Stats')}<br>{link(source_url[l['fixture_id']], 'OLBG event')}</td></tr>''')
    body = f'''<h1>Originated match, handicap & total lines</h1>
<p class="lead">{lines['count']} independently estimated selections across {lines['fixtures']} officially matched, future-at-cutoff matches. Multi-market pricing is available only in Ice Hockey, Baseball, Rugby Union and Handball, where both participants had relevant official numeric records. Other markets are left blank and flagged.</p>
{notice('<b>Read three different prices separately:</b> Our fair American price is calculated from league statistics. An observed FanDuel quote is only a dated NHL feed partner snapshot. OLBG offered odds are blank for every row because they were not captured. Hypothetical totals/handicaps do not imply an identical selectable OLBG line.','important')}
{filters(status=False)}
<div class="table-scroller"><table class="table"><thead><tr>{''.join(f'<th scope="col">{e(h)}</th>' for h in ['Fixture','Market','Selection','Estimated chance','Our fair American','Observed partner quote','-250…+10000 band','Official source + OLBG'])}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''
    return shell("Originated lines", "lines.html", body, subtitle="95 ESTIMATED PRICES / THREE MARKETS WHERE SUPPORTED")


def band_page(picks):
    rows = []
    for p in picks["picks"]:
        if not p["fair_in_band"]:
            continue
        rows.append(f'<tr><td>{e(p["sport"])}<div class="sub">{e(p["competition"])}</div></td><td>{label_fixture(p)}</td>'
                    f'<td><a class="selection" href="predictions.html#preview-{slug(p["fixture_id"])}">{e(p["selection"])} → full analysis</a><div class="sub">{e(p["market"])}</div></td>'
                    f'<td>{pct(p["probability"])}</td><td>{odd(p["fair_american"])}</td>'
                    f'<td>{odd(p["observed_american"])}{(" · NHL partner" if p["observed_american"] is not None else " · not captured")}</td>'
                    f'<td>{badge(p["confidence"])}</td><td>{link(p["official_url"], "Official match")}</td></tr>')
    body = f'''<h1>−250 to +10000, without short-price padding</h1><p class="lead">{len(rows)} match-winner fair prices fall inside the requested American-odds band. Only {picks['focused']} also have a high grade, a fully written prediction, and a separate captured league-partner quote within the same range. No verified current OLBG bookmaker quote is available.</p>
{notice('At 70% chance, fair American odds are about −233. At −250, the implied chance is 71.43%. The overlap for <b>high at ≥70% and fair odds no shorter than −250</b> is only 70.00% to 71.43%. A short-priced favourite is not made eligible by relabelling its probability.','important')}
<div class="table-scroller"><table class="table"><thead><tr>{''.join(f'<th scope="col">{e(x)}</th>' for x in ['Sport','Confirmed fixture','Clear selection + analysis','Our chance','Our fair American','Observed quote','Grade','Official source'])}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''
    return shell("Odds band", "band.html", body, subtitle="AMERICAN ODDS / FAIR PRICE ≠ OBSERVED QUOTE")


def sports_index(matches, picks, predictions, hubs):
    rows = []
    high = Counter(x["sport"] for x in predictions["predictions"] if x["confidence"] == "high")
    by = {s: [x for x in matches["matches"] if x["sport"] == s] for s in SPORTS}
    p_by = Counter(x["sport"] for x in picks["picks"])
    for h in hubs["hubs"]:
        s = h["sport"]
        rows.append(f'<tr><td><a class="selection" href="{slug(s)}.html">{e(s)} →</a></td><td>{h["listings"]}</td><td>{h["official_matches"]}</td><td>{p_by[s]}</td><td>{high[s]} / 5</td>'
                    f'<td>{link(h["official_check_target"], "Official check")}</td><td>{link(h["url"], "OLBG hub")}</td></tr>')
    body = f'''<h1>Choose a sport</h1><p class="lead">Fifteen requested categories, one clear table. Open a category to see what OLBG listed, which rows the sport's official publisher actually confirmed, where independent lines were possible, and exactly how far the five-per-sport written-pick target remains from reality.</p>
<div class="table-scroller"><table class="table"><thead><tr>{''.join(f'<th scope="col">{e(x)}</th>' for x in ['Sport','OLBG first page','Official matched','Priced & written','High / target','Official source','OLBG'])}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''
    return shell("Sports", "sports/index.html", body, prefix="../", subtitle="15 SPORT CATEGORIES / NO HIDDEN QUOTAS")


def sport_page(sport, matches, picks, previews, hub):
    rows = [x for x in matches["matches"] if x["sport"] == sport]
    selection = [p for p in picks["picks"] if p["sport"] == sport]
    written = [x for x in previews["predictions"] if x["sport"] == sport]
    high = [x for x in written if x["confidence"] == "high"]
    by_pick = {x["id"]: x for x in picks["picks"]}
    short = 5 - len(high)
    body = f'''<p class="crumb"><a href="index.html">All sports</a> / {e(sport)}</p>
<h1>{e(sport)} — matches and picks</h1>
<p class="lead">{len(rows)} OLBG first-page entries; {sum(r['official_confirmed'] for r in rows)} matched to an official event; {len(selection)} priced with a written analysis; {len(high)} high-confidence write-ups. <b>{short} of five high slots remain unfilled</b>, not invented.</p>
{notice(f'<b>Source boundary.</b> OLBG hub: {link(hub["url"], "open first-page listing")}. Official review target: {link(hub["official_check_target"], "open governing site")}. An unmatched row below retains a blank official fixture and a non-confirming target link.', 'important')}
{('<div class="section-title"><div><div class="eyebrow">Picks with full prose</div><h2>Written analyses</h2></div></div>' + cards_from_predictions(written, picks['picks'], prefix='../')) if selection else notice('No priced and written selection cleared the official-fixture, future-start and numeric-input checks in this captured first page. See row-by-row reasons below.', 'info')}
<div class="section-title"><div><div class="eyebrow">All discovered events</div><h2>{e(sport)} fixture table</h2><p>Verified fields are kept apart from the OLBG listing, which is discovery only.</p></div></div>
{matches_table(rows, prefix='../') if rows else '<div class="empty">The captured OLBG hub did not list a match/event in this sport. No row or pick was invented.</div>'}
<p class="fineprint"><a href="../flagged.html">Find review items for {e(sport)} →</a></p>'''
    return shell(f"{sport} category", "", body, prefix="../", subtitle="SPORTS / " + sport.upper())


def flags_page(flags):
    rows = []
    for f in flags["flags"]:
        label = e(f["sport"])
        rows.append(f'<tr data-sport="{slug(f["sport"])}" data-category="{slug(f["category"])}" data-search="{e(f["summary"]+" "+f["detail"])}">'
                    f'<td><b>{e(f["id"])}</b><div class="sub">{label} · {e(f["category"])}</div></td>'
                    f'<td>{badge(f["severity"], "warn" if f["severity"] == "medium" else "critical")}</td>'
                    f'<td><strong>{e(f["summary"])}</strong><div class="sub">{e(f["detail"])}</div></td>'
                    f'<td>{e(", ".join(f["missing_fields"]))}</td>'
                    f'<td>{link(f["official_url"], "Official / review target", role=f["official_link_role"])}<div class="sub">{e(f["official_link_role"])}</div><br>{link(f["olbg_url"], "OLBG event/hub")}</td></tr>')
    body = f'''<h1>Flagged for Review</h1><p class="lead">{flags['count']} open items: {flags['by_category'].get('five-per-sport shortfall',0)} per-sport quota gaps, {flags['by_category'].get('unverified listing',0)} individual OLBG-only listings, {flags['by_category'].get('unpriced official match',0)} official but unpriced events, and {flags['by_category'].get('cross-source irregularity',0)} cross-source cautions.</p>
{notice('<b>No silent filling.</b> A linked official check target on an unconfirmed listing does not verify the row. Blank official fields and odds remain blank until the specific fixture, time or market is established. This review queue does not block publication.', 'important')}
<div class="filters"><label>Search flags<input id="filter-search" type="search" placeholder="Event, code, issue…"></label>
<label>Category<select id="filter-category"><option value="">All categories</option>{''.join(f'<option value="{slug(cat)}">{e(cat)}</option>' for cat in sorted(flags['by_category']))}</select></label>
<label>Sport<select id="filter-sport"><option value="">All sports</option>{''.join(f'<option value="{slug(s)}">{e(s)}</option>' for s in SPORTS)}</select></label><span id="filter-count" role="status"></span></div>
<div class="table-scroller"><table class="table"><thead><tr>{''.join(f'<th scope="col">{e(x)}</th>' for x in ['Flag / sport','Severity','Irregularity & evidence','Unconfirmed values','Source links'])}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''
    return shell("Flagged for Review", "flagged.html", body, subtitle="OPEN ITEMS / NONE HIDDEN")


def sources_page(sources, taxonomy):
    rows = ''.join(f'<tr><td>{e(s["scope"])}</td><td>{link(s["url"], s["url"])}</td><td>{e(s["what_checked"])}</td><td>{e(s["capture"])}</td></tr>'
                   for s in sources["sources"])
    body = f'''<h1>Official source register</h1><p class="lead">{sources['count']} authority URLs checked in the 24 October pass; the PDC session and WTA Osaka draw are official-site indexed excerpts because their direct pages did not return usable body text. Those events are never priced here. A link supports only the stated fields, not every value nearby; OLBG is discovery only.</p>
{notice('<b>Reproducibility:</b> most fixture/stat inputs were transcribed from first-hand official pages; the two indexed-excerpt exceptions are named below, and this layer does not persist all raw response bodies. The separate OLBG first-page extract preserves its source commit and SHA-256, and the full 96 rows remain independently inspectable on their event URLs. External pages may update after this dated read.','important')}
<div class="table-scroller"><table class="table"><thead><tr>{''.join(f'<th scope="col">{e(x)}</th>' for x in ['Authority','URL','Fields checked','Capture status'])}</tr></thead><tbody>{rows}</tbody></table></div>'''
    return shell("Official sources", "sources.html", body, subtitle="PROVENANCE / MANUAL REVIEW LINKS")


def olbg_page(taxonomy):
    rows = ''.join(f'<tr><td><b>{e(h["sport"])}</b> / {e(h.get("sport_ids") or h["sport_id"])}</td>'
                   f'<td>{link(h["url"], "OLBG hub")}'
                   f'{(" · " + link(h["subhub_url"], "Hurling sub-hub")) if h.get("subhub_url") else ""}</td>'
                   f'<td>{h["listings"]} visible · {h["official_matches"]} matched</td><td>{link(h["official_check_target"], "Official review target")}</td></tr>'
                   for h in taxonomy["hubs"])
    capture_note = (f'<b>Scope:</b> {e(taxonomy["first_page_source"])} was copied at SHA-256 '
                    f'{e(taxonomy["first_page_source_sha256"])}. We re-opened all fifteen hubs, '
                    f'but the first-page catalogue ({sum(h["listings"] for h in taxonomy["hubs"])} rows: '
                    '96 imported plus one directly checked Hurling match) is not a complete pagination crawl. '
                    'All findings below can be checked against OLBG itself.')
    body = f'''<h1>How the OLBG pages work</h1><p class="lead">Reverse engineered from the fifteen requested sport hubs and selected individual event pages. Sport IDs live in the URL; an event id identifies an event, not a bookmaker price or verified fixture.</p>
{notice(capture_note,'important')}
<div class="explainer-grid"><div><b>1 · Sport hub</b><p><code>/betting-tips/Ice_Hockey/13</code>. The ID is required; the page shows its most-tipped outcome per event, not every tip or match.</p></div>
<div><b>2 · Individual event</b><p><code>/.../SJ_Sharks_@_BOS_Bruins/13?event_id=200007</code>. Opens money line, puck line, game total and member commentary for that NHL event.</p></div>
<div><b>3 · Our own board</b><p>Confirm that event against the NHL/league source, then keep the observed bookmaker quote separate from the estimated fair price. No quote was recovered from OLBG.</p></div></div>
<div class="section-title"><div><h2>Sport URLs and review destinations</h2></div></div>
<div class="table-scroller"><table class="table"><thead><tr><th>Sport / ID</th><th>OLBG source</th><th>Visible scope</th><th>Official verification target</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="section-title"><div><h2>Observed structural issues</h2></div></div><ul class="notes-list">{''.join('<li>'+e(x)+'</li>' for x in taxonomy['reverse_engineering'])}</ul>
<p>{link('https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/SJ_Sharks_@_BOS_Bruins/13?event_id=200007','Example multi-market event')} · {link('https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/SC_Magdeburg_vs_HC_Kriens_Luzern/20?event_id=12136','Example three-way event')}</p>'''
    return shell("OLBG reverse engineering", "olbg.html", body, subtitle="DISCOVERY ROUTES / EVENT STRUCTURES")


def audit_page(audit):
    rows = ''.join(f'<tr><td><b>{e(x["code"])}</b><div class="sub">{badge(x["severity"], "critical" if x["severity"] == "high" else "warn")}</div></td>'
                   f'<td><code>{e(x["path"])}</code></td><td>{e(x["finding"])}</td><td>{link(x["source_url"], "Review source")}</td></tr>'
                   for x in audit["findings"])
    body = f'''<h1>Line-by-line repo & evidence audit</h1><p class="lead">{len(audit['findings'])} specific file-range findings against repository commit <code>{e(audit['reviewed_main_sha'])}</code>. Each has a link to a first-hand league/OLBG source or to the official repository record. Structural tests pass only schema, mathematics and local links; they do not magically recheck a changing external website.</p>
{notice('<b>Important:</b> flagged irregularities are published, not marked resolved. Existing historical research layers are not aggregated here; their dated counts cannot be added to these 96 first-page rows.','important')}
<div class="table-scroller"><table class="table"><thead><tr><th>Finding</th><th>Path / lines</th><th>Assessment</th><th>Manual source</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return shell("Repository audit", "audit.html", body, subtitle="STRUCTURAL REVIEW / EXTERNAL LIMITS")


def methodology_page(lines, picks, matches):
    a = lines["assumptions"]
    body = f'''<h1>How a row becomes a written selection</h1>
<p class="lead">The first OLBG page is a discovery list, not a complete fixture feed or an odds provider. An individual match only gets our own fair line after its league confirms the exact participants and a future official start, and both sides have comparable numerical input. At 17:45 UTC we withheld starts under 90 minutes away to allow for static-site publishing latency.</p>
<div class="steps"><div><span>01</span><b>Discover</b><p>Keep the OLBG event URL, single most-tipped outcome and original displayed time. Do not convert the unspecific publisher clock to UTC.</p></div>
<div><span>02</span><b>Confirm</b><p>Check the pairing and start against a sporting governing body; dates and time zones are displayed as published. Unknown or conflicting fields are blank and reviewed.</p></div>
<div><span>03</span><b>Originate</b><p>Use goals or runs for both clubs from a dated league table. Calculations below produce independent, no-vig estimates for win, handicap, total where those inputs exist.</p></div>
<div><span>04</span><b>Write</b><p>Every displayed candidate needs 30+ unique human words, a named market/selection, opponent context, current form and direct official links. Unsupported injuries are not guessed.</p></div></div>
<div class="section-title"><div><h2>Independent pricing, fully disclosed</h2></div></div>
<div class="table-scroller"><table class="table"><thead><tr><th>Sport</th><th>Inputs & calculation</th><th>Market types / limitations</th><th>Official example</th></tr></thead><tbody>
<tr><td>Ice Hockey / NHL</td><td>Team GF/GA per GP are shrunk toward a <b>{a['NHL_PRIOR_GOALS']}</b>-goal/team prior by GP/(GP+<b>{a['NHL_SHRINK_GAMES']}</b>). Expected home goals = prior × home attack × away defence × <b>{a['NHL_HOME_FACTOR']}</b>; away divides by the same factor. Independent Poisson grids (0–35 goals) estimate win, ±1.5 puck line and half-goal total.</td><td>Regulation ties split 50:50 for a two-way winner. Shootout-goal convention, in-game totals and starting goaltenders are not fitted. Input sample only 8–12 games.</td><td>{link('https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2','NHL team summary')}</td></tr>
<tr><td>Baseball / MLB</td><td>Expected runs = mean of own runs/game and opponent runs allowed/game with a <b>{a['MLB_HOME_FACTOR']}</b> home multiplier. Poisson sums give a two-way result, ±1.5 run line and a half-run total.</td><td>Regular-season rates across 162 games; postseason pitching and roster differences are <b>not</b> priced. No observed bookmaker quote. Both teams' official probable starters are provided for context only.</td><td>{link('https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason','MLB official standings')}</td></tr>
<tr><td>Rugby Union / Handball</td><td>Home/away scoring averages, shrunk GP/(GP+<b>{a['NORMAL_SHRINK_GAMES']}</b>) toward priors of <b>{a['RUGBY_PRIOR_POINTS']}</b> and <b>{a['HANDBALL_PRIOR_GOALS']}</b>. Own home allowances of {a['RUGBY_HOME_EDGE']} rugby points / {a['HANDBALL_HOME_EDGE']} handball goals. Normal margin SD {a['RUGBY_MARGIN_SD']} / {a['HANDBALL_MARGIN_SD']}, separate total SD {a['RUGBY_TOTAL_SD']} / {a['HANDBALL_TOTAL_SD']}.</td><td>Three-way <b>regular time</b> includes a draw (difference within ±0.5), unlike NHL overtime-inclusive winners. Handicaps and totals are hypothetical if OLBG event page did not display that exact line. Small 3–6 game samples keep confidence low/medium.</td><td>{link('https://ehfcl.eurohandball.com/men/2026-27/standings/','EHF official table')}</td></tr></tbody></table></div>
<div class="explainer-grid"><div><b>Fair price is not a quote</b><p>p≥50% → American = −round(100 p/(1−p)); below 50% → +round(100 (1−p)/p). Estimated lines are no-vig and omit bookmaker margin.</p></div>
<div><b>Grade ≠ guarantee</b><p>High if an eligible NHL match-winner estimate is ≥70%; medium if ≥58%; otherwise low. EHF and MLB high estimates are capped at medium, and short-sample rugby at low. These rules are editorial, not externally calibrated.</p></div>
<div><b>Band is a second check</b><p>Only −250…+10000 American is inside the fair-price focus. For an executive pick we require high grade, written prose and a separate in-band observed quote. OLBG's current offered price remains unconfirmed.</p></div></div>
{notice('<b>Known limits:</b> sport hubs only expose their first page; no five-per-sport quota can be met on unsupported events. Injury fields require a dated, event-specific official report; the NHL, EHF, MLB and Top 14 rows shown here do not imply an injury-free lineup. Once a fixture starts, a static page cannot place a bet or re-check its status.','important')}
<p>{link('https://www.olbg.com/betting-tips','OLBG discovery')} · <a href="sources.html">Full official source register</a> · <a href="flagged.html">Every missing field</a></p>'''
    return shell("Methodology", "methodology.html", body, subtitle="OUR ESTIMATES / PRICE & CONFIDENCE RULES")


def css() -> str:
    return ''':root{--ink:#17212c;--muted:#556777;--deep:#10293b;--line:#dce6e8;--sea:#027f75;--sea2:#0c9e8b;--warm:#e9a45d;--paper:#f7faf8;--white:#fff;--red:#9c4b38;--shadow:0 10px 30px rgba(8,41,51,.07)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{background:var(--paper);color:var(--ink);font:15px/1.52 system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0}
a{color:#006e73;text-decoration:none}a:hover{text-decoration:underline}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #f9aa4f;outline-offset:2px}.shell{max-width:1250px;padding:0 clamp(1rem,3vw,2.5rem);margin:auto}.skip{position:absolute;top:-100px;left:1rem;background:white;padding:1rem;z-index:99}.skip:focus{top:1rem}
.header{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:8}.header-inner{min-height:70px;display:flex;align-items:center;justify-content:space-between;gap:1.5rem}.brand{display:flex;gap:.7rem;align-items:center;color:var(--deep);white-space:nowrap}.brand:hover{text-decoration:none}.brand b{display:block;font-size:1.08rem;letter-spacing:-.025em}.brand small{display:block;font-size:.65rem;letter-spacing:.03em;text-transform:uppercase;color:var(--muted)}.brand-mark{background:var(--deep);color:#4be3b9;font-weight:800;border-radius:9px;padding:.2rem .65rem;font-size:1.2rem}.nav{display:flex;gap:.1rem;flex-wrap:wrap}.nav a{font-size:.79rem;color:#314a57;padding:.54rem .57rem;border-radius:6px;font-weight:650}.nav a.active,.nav a:hover{color:#004e51;background:#e5f7f1;text-decoration:none}.ribbon{background:#e3f4ef;border-bottom:1px solid #c6e7df;padding:.45rem 0;font-size:.77rem;color:#244f56}.ribbon span{color:#486772}
main{padding-top:1.75rem!important;padding-bottom:4rem!important;min-height:60vh}.page-eyebrow,.eyebrow,.kicker{font-size:.73rem;text-transform:uppercase;letter-spacing:.11em;color:var(--sea);font-weight:800}.page-eyebrow{margin-bottom:.7rem}h1,h2,h3,p{margin:0}h1{font-size:clamp(2.05rem,4vw,3.1rem);line-height:1.12;letter-spacing:-.055em;margin:0 0 .95rem}h2{font-size:clamp(1.4rem,2.5vw,1.95rem);letter-spacing:-.04em;line-height:1.15}h3{font-size:1.28rem;line-height:1.3;letter-spacing:-.02em}p{line-height:1.58}.lead{font-size:1.04rem;max-width:900px;color:#3d5361;margin:.35rem 0 1.25rem}.fineprint,.sub{font-size:.76rem;color:var(--muted)}.fineprint{margin:1rem 0}.warn-text{color:#8d4b17}.blank{color:#8b989b}.vs,.soft{color:#768b93;font-weight:400}.sport-tag{display:inline-block;margin-bottom:.15rem;text-transform:uppercase;letter-spacing:.06em;font-weight:750}.event{font-weight:750}.external{font-size:.7rem;margin-left:.2em;opacity:.7}
.hero{background:radial-gradient(circle at 70% 95%,#155c59 0,#10293b 50%,#081d2e 100%);color:#fff;padding:clamp(1.5rem,4vw,3rem);border-radius:18px;box-shadow:var(--shadow);display:grid;grid-template-columns:1.55fr .85fr;gap:2rem;align-items:center}.hero .eyebrow{color:#78dcca}.hero h1{font-size:clamp(2.5rem,5vw,4.7rem);margin:.65rem 0 1rem}.hero h1 span{color:#9de3cd}.hero p{color:#c8d6d9;max-width:620px}.hero-actions{display:flex;gap:.55rem;flex-wrap:wrap;margin-top:1.5rem}.button{display:inline-flex;align-items:center;justify-content:center;border-radius:8px;padding:.7rem 1rem;font-size:.85rem;font-weight:750;border:1px solid #95b6b1}.button:hover{text-decoration:none}.button.prime{background:#d3fae5;border-color:#d3fae5;color:#063b3a}.button.prime:hover{background:white}.button.ghost{background:transparent;color:white}.hero-card{padding:1.4rem;border:1px solid #416479;border-radius:14px;background:rgba(255,255,255,.06)}.hero-card div{font-size:.72rem;color:#b1cacc;text-transform:uppercase;letter-spacing:.06em}.hero-card strong{display:block;font-size:2.4rem;letter-spacing:-.06em;line-height:1.2;margin:.65rem 0 0}.hero-card span{color:#b9d7d0;font-size:.82rem}.hero-card hr{border:0;border-top:1px solid #467175;margin:1.2rem 0}.hero-card b{color:#eaf7ec}
.notice{padding:.83rem 1rem;border-left:4px solid #5c9fa9;background:#eef7f7;margin:1.1rem 0;border-radius:7px;font-size:.87rem}.notice.important{background:#fff6e8;border-color:#dd9b48}.notice b{color:#284250}.notice a{font-weight:750}.stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:.65rem;margin:1.2rem 0}.metric{padding:1rem;border-radius:10px;border:1px solid var(--line);background:var(--white)}.metric strong{font-size:1.75rem;line-height:1.1;display:block;letter-spacing:-.04em;color:#123c42}.metric span{display:block;font-weight:750;margin:.3rem 0 .1rem;font-size:.77rem}.metric small{display:block;font-size:.68rem;color:var(--muted)}
.section-title{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:2.4rem 0 .8rem}.section-title h2{margin:.25rem 0}.section-title p{color:var(--muted);font-size:.86rem;max-width:740px}.text-link{font-size:.84rem;font-weight:750;white-space:nowrap}.table-scroller{overflow:auto;border-radius:10px;background:#fff;border:1px solid var(--line);box-shadow:var(--shadow)}.table{width:100%;min-width:970px;border-collapse:collapse;text-align:left}.table th{padding:.85rem .85rem;background:#eaf3f1;color:#294a51;text-transform:uppercase;letter-spacing:.07em;font-size:.68rem;white-space:nowrap}.table td{padding:.78rem .85rem;border-top:1px solid #ecf1f1;vertical-align:top;font-size:.82rem}.table tr:hover td{background:#f8fcfb}.table td .sub{margin:.16rem 0}.table b,.table strong{font-weight:700}.table code{white-space:normal;overflow-wrap:anywhere}.selection{font-weight:790;color:#006a68}.badge{display:inline-flex;align-items:center;white-space:nowrap;font-size:.66rem;padding:.2rem .48rem;border-radius:99px;background:#ecf0f0;color:#475767;font-weight:750;text-transform:uppercase;letter-spacing:.015em}.badge.high,.badge.good{background:#d4f6e6;color:#135b46}.badge.medium{background:#e5f4ff;color:#245880}.badge.low,.badge.muted{background:#edf0f2;color:#52616c}.badge.warn{background:#fff0d7;color:#8a5619}.badge.critical{background:#ffebe7;color:#9d473d}.filters{display:flex;flex-wrap:wrap;gap:.8rem;align-items:flex-end;margin:1rem 0;padding:.85rem;background:#fff;border:1px solid var(--line);border-radius:9px}.filters label{display:flex;flex-direction:column;font-size:.73rem;font-weight:750;color:#49616a;gap:.25rem}.filters input,.filters select{border:1px solid #b7cbd0;padding:.53rem .65rem;border-radius:6px;font:inherit;background:white;color:var(--ink);min-width:170px}.filters input{min-width:250px}.filters #filter-count{color:var(--muted);font-size:.78rem;margin-left:auto;padding:.35rem 0}
.prediction{background:#fff;border:1px solid var(--line);border-left:4px solid var(--sea);padding:1.2rem;border-radius:10px;box-shadow:var(--shadow);margin:.8rem 0;scroll-margin-top:110px}.prediction.high{border-left-color:#189c70}.prediction-head{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin-bottom:.6rem}.kicker{margin-right:auto}.prediction h3{margin:.3rem 0}.fixtureline{color:#516674;font-size:.81rem}.pricebar{display:flex;gap:1.2rem;flex-wrap:wrap;margin:1.15rem 0;padding:.8rem 1rem;background:#f1f8f6;border-radius:8px;border:1px solid #d9ede8}.pricebar>div{min-width:145px}.pricebar span{display:block;color:#617679;font-size:.7rem;text-transform:uppercase;font-weight:750}.pricebar b{display:block;color:#173843;font-size:1rem}.pricebar b .sub{display:block;text-transform:none;font-weight:400}.prediction .analysis{max-width:920px;line-height:1.7;font-size:.94rem}.sources-block{display:grid;grid-template-columns:1.15fr .85fr;gap:.8rem;margin:1rem 0;padding:.8rem;background:#fafcfa;border:1px solid var(--line);border-radius:7px;font-size:.77rem}.sources-block b{color:#233d43}.sources-block p{margin:.25rem 0;color:#526575}.sources-block ul{margin:.3rem 0 0;padding-left:1.2rem;display:flex;flex-wrap:wrap;gap:.25rem 1.3rem}.sources-block li{color:#60707a}.deep-link{font-size:.8rem;font-weight:700}.prediction-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:.7rem}.prediction-grid .prediction{margin:0}.prediction-grid .pricebar{gap:.7rem}.prediction-grid .sources-block{grid-template-columns:1fr}.expiry{margin-left:.3rem}.expiry.expired{color:#a24031;font-weight:800}.after-expiry,.empty{padding:1.1rem 1.2rem;border:1px dashed #b8c9cc;background:#fff;color:#49606a;border-radius:8px}.after-expiry[hidden]{display:none}.tabs-line{display:flex;gap:1rem;flex-wrap:wrap;border-bottom:1px solid var(--line);padding:.6rem 0;margin:1.1rem 0}.tabs-line a{font-weight:700}.sport-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.65rem}.sport-card{background:#fff;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:1rem;display:block}.sport-card:hover{text-decoration:none;border-color:var(--sea);box-shadow:var(--shadow)}.sport-card strong{display:flex;justify-content:space-between;font-size:.95rem}.sport-card strong span{color:var(--sea)}.sport-card small,.sport-card em{display:block;font-size:.75rem;color:var(--muted);margin-top:.2rem}.sport-card em{font-style:normal;color:#267568}.explainer-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.7rem;margin:1rem 0}.explainer-grid>div,.steps>div{border:1px solid var(--line);background:#fff;border-radius:9px;padding:1.1rem}.explainer-grid b{display:block;color:#1d3d42;margin-bottom:.3rem}.explainer-grid p{font-size:.81rem;color:var(--muted);margin-bottom:.4rem}.explainer-grid a{font-size:.8rem;font-weight:750}.steps{display:grid;grid-template-columns:repeat(4,minmax(190px,1fr));gap:.65rem;margin:1.2rem 0}.steps span{color:var(--sea);font-weight:850;font-size:1.4rem}.steps b{display:block}.steps p{color:var(--muted);font-size:.81rem}.notes-list{padding:0;margin:1rem 0 1.5rem;list-style:none;display:grid;gap:.5rem}.notes-list li{padding:.7rem .9rem;background:#fff;border-left:3px solid var(--sea);border-radius:4px;font-size:.87rem}.crumb{font-size:.78rem;color:var(--muted);margin-bottom:.6rem}.footer{background:#112b38;color:#c7d6d7;padding:2rem 0;font-size:.75rem}.footer a{color:#a6e9dd}.footer-inner{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}.footer-inner>span{max-width:350px}
code{font-family:ui-monospace,Consolas,monospace;font-size:.83em;background:#eaf0ee;padding:.1em .3em;border-radius:3px}.table code{display:inline-block}
@media(max-width:1000px){.hero{grid-template-columns:1fr}.stats{grid-template-columns:repeat(3,1fr)}.steps{grid-template-columns:repeat(2,1fr)}.header{position:relative}.header-inner{padding-top:.65rem;padding-bottom:.65rem;flex-wrap:wrap}.nav{max-height:90px;overflow:auto}}@media(max-width:650px){.hero{padding:1.4rem}.hero-card{padding:1rem}.stats{grid-template-columns:repeat(2,1fr)}.steps{grid-template-columns:1fr}.section-title{align-items:flex-start;flex-direction:column}.sources-block{grid-template-columns:1fr}.prediction-grid{grid-template-columns:1fr}.filters label,.filters input,.filters select{width:100%;min-width:0}.filters #filter-count{margin:0}.nav{gap:0}.nav a{font-size:.73rem}.ribbon span{display:none}}
'''


def js() -> str:
    return '''(() => {
  const table = document.querySelector('table.table tbody');
  const rows = table ? Array.from(table.querySelectorAll('tr')) : [];
  const search = document.querySelector('#filter-search');
  const sport = document.querySelector('#filter-sport');
  const status = document.querySelector('#filter-status');
  const category = document.querySelector('#filter-category');
  const count = document.querySelector('#filter-count');
  function applyFilters() {
    let n = 0;
    const q = (search?.value || '').trim().toLocaleLowerCase();
    for (const row of rows) {
      const text = (row.dataset.search || row.textContent).toLocaleLowerCase();
      const ok = (!q || text.includes(q)) && (!sport?.value || row.dataset.sport === sport.value)
        && (!status?.value || row.dataset.status === status.value)
        && (!category?.value || row.dataset.category === category.value);
      row.hidden = !ok;
      if (ok) n++;
    }
    if (count) count.textContent = `${n} of ${rows.length} rows`;
  }
  [search, sport, status, category].filter(Boolean).forEach(control => control.addEventListener('input', applyFilters));
  if (count) applyFilters();
  function expireHighlights() {
    const now = Date.now();
    document.querySelectorAll('[data-archive-badge][data-start]').forEach(card => {
      const date = Date.parse(card.dataset.start);
      const label = card.querySelector('.expiry');
      if (Number.isFinite(date) && date <= now) {
        if (label) { label.textContent = 'Started / archived'; label.classList.add('expired'); }
        if (card.closest('[data-expire-group]')) card.hidden = true;
      } else if (label) { label.textContent = 'Future at device time'; label.classList.remove('expired'); }
    });
    const group = document.querySelector('[data-expire-group]');
    const empty = document.querySelector('.after-expiry');
    if (group && empty) empty.hidden = !!group.querySelector('[data-start]:not([hidden])');
  }
  expireHighlights();
  setInterval(expireHighlights, 60000);
})();'''


def main():
    matches, lines, picks = read("matches.json"), read("lines.json"), read("picks.json")
    previews, flags = read("predictions.json"), read("flagged.json")
    sources, taxonomy, audit = read("sources.json"), read("olbg_taxonomy.json"), read("repo_audit.json")
    assert len(SPORTS) == 15 and set(SPORTS) == {x["sport"] for x in taxonomy["hubs"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    outputs = {
        "index.html": index_page(matches, lines, picks, previews, flags, taxonomy),
        "matches.html": matches_page(matches),
        "picks.html": picks_page(picks, previews),
        "predictions.html": predictions_page(previews, picks),
        "lines.html": lines_page(lines, matches),
        "band.html": band_page(picks),
        "sports/index.html": sports_index(matches, picks, previews, taxonomy),
        "flagged.html": flags_page(flags),
        "sources.html": sources_page(sources, taxonomy),
        "olbg.html": olbg_page(taxonomy),
        "audit.html": audit_page(audit),
        "methodology.html": methodology_page(lines, picks, matches),
    }
    hub_by = {x["sport"]: x for x in taxonomy["hubs"]}
    for s in SPORTS:
        outputs[f"sports/{slug(s)}.html"] = sport_page(s, matches, picks, previews, hub_by[s])
    for name, content in outputs.items():
        (OUT / name).write_text(content, encoding="utf-8")
    (OUT / "assets" / "style.css").write_text(css(), encoding="utf-8")
    (OUT / "assets" / "app.js").write_text(js(), encoding="utf-8")
    print(f"vantage_build: {len(outputs)} HTML pages, {len(SPORTS)} sports; {picks['focused']} executive pick / {previews['count']} written / {flags['count']} review items")


if __name__ == "__main__":
    main()
