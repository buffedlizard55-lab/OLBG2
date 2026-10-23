#!/usr/bin/env python3
"""Render the clean, static /olbg/ dashboard from committed research outputs."""
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "olbg"
OUT = ROOT / "olbg"
OUT.mkdir(exist_ok=True)
(OUT / "sports").mkdir(exist_ok=True)

source = json.loads((DATA / "source.json").read_text(encoding="utf-8"))
matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))["matches"]
lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))["lines"]
picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["shortlists"]
predictions = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]
flags = json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]
sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]
counts = json.loads((DATA / "summary.json").read_text(encoding="utf-8"))["counts"]
by_event = {e["id"]: e for e in matches}
by_sport = defaultdict(list)
for event in matches:
    by_sport[event["sport"]].append(event)
sport_names = {s["slug"]: s["name"] for s in source["sports"]}


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def link(url, label, cls=""):
    if not url:
        return ""
    if urlsplit(url).scheme not in {"https", "http"} and not url.startswith(("../", "./")):
        raise ValueError("unsupported link: " + url)
    return f'<a href="{esc(url)}" class="{esc(cls)}" rel="noopener noreferrer">{esc(label)} ↗</a>'


def pct(p):
    return "—" if p is None else f"{100*p:.2f}%"


def american(value):
    if value is None:
        return "—"
    return f"−{abs(value)}" if value < 0 else f"+{value}"


def badge(text, kind="neutral"):
    return f'<span class="badge {esc(kind)}">{esc(text)}</span>'


def confidence(value):
    return badge(value, value) if value else '<span class="blank">—</span>'


PROVENANCE = {
    "active": "Active on OLBG now",
    "last_seen": "Last seen on OLBG earlier today",
    "official_context": "Official context only",
}


def provenance(event):
    kind = "active" if event["provenance"] == "active" else ("seen" if event["provenance"] == "last_seen" else "context")
    detail = event.get("olbg_state") or "No individual OLBG event observed"
    return badge(PROVENANCE[event["provenance"]], kind) + f'<small>{esc(detail)}</small>'


def source_links(items, olbg_url=None, olbg_state=None):
    bits = ['<ul class="source-list">']
    for item in items:
        bits.append(f'<li>{link(item["url"], item["label"])}</li>')
    if olbg_url:
        bits.append(f'<li>{link(olbg_url, "OLBG listing / discovery")}</li>')
    bits.append('</ul>')
    return ''.join(bits)


def event_sort(event):
    return (event.get("start_utc") or event["date"] + "T23:59:59Z", event["date"], event["name"])


def table(headers, rows, caption, table_id=""):
    ident = f' id="{esc(table_id)}"' if table_id else ""
    return (f'<div class="table-wrap" tabindex="0" role="region" aria-label="{esc(caption)}"><table{ident}>'
            f'<caption>{esc(caption)}</caption><thead><tr>' + ''.join(f'<th scope="col">{esc(h)}</th>' for h in headers) +
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')


def event_row(event, show_sport=True):
    line = event.get("line")
    sport = f'<td><a href="{("../" if False else "")}sports/{event["sport"]}.html">{esc(sport_names[event["sport"]])}</a></td>' if show_sport else ""
    # This helper is used on root pages only; category pages use event_row_local.
    selection = esc(line["selection"]) if line else '<span class="blank">—</span>'
    reason = "" if line else f'<small>{esc(event["blank_reason"])}</small>'
    time = f'<strong>{esc(event["date"])}</strong><small>{esc(event.get("start_utc") or event.get("display_time") or "Clock not confirmed")}</small>'
    if event.get("timezone_note"):
        time += f'<small class="muted">{esc(event["timezone_note"])}</small>'
    event_cell = f'<strong>{esc(event["name"])}</strong><small>{esc(event["competition"])}</small>'
    if event.get("venue"):
        event_cell += f'<small>{esc(event["venue"])}</small>'
    event_cell += f'<details><summary>Market review</summary><p>{esc(event["market_note"])}</p></details>'
    return (f'<tr id="{esc(event["id"])}">' + sport + f'<td>{event_cell}</td><td>{time}</td><td>{provenance(event)}<small>{esc(event["official_status"])}</small></td>'
            f'<td><strong>{selection}</strong>{reason}</td><td>{pct(line["probability"] if line else None)}</td>'
            f'<td>{american(line["fair_american"] if line else None)}<small>fair, not a bookmaker quote</small></td>'
            f'<td>{confidence(line["confidence"] if line else None)}</td>'
            f'<td>{source_links(event["official_sources"], event.get("olbg_url"), event.get("olbg_state"))}</td></tr>')


def event_row_local(event):
    line = event.get("line")
    selection = esc(line["selection"]) if line else '<span class="blank">—</span>'
    reason = "" if line else f'<small>{esc(event["blank_reason"])}</small>'
    time = f'<strong>{esc(event["date"])}</strong><small>{esc(event.get("start_utc") or event.get("display_time") or "Clock not confirmed")}</small>'
    event_cell = f'<strong>{esc(event["name"])}</strong><small>{esc(event["competition"])}</small><details><summary>Market review</summary><p>{esc(event["market_note"])}</p></details>'
    return (f'<tr id="{esc(event["id"])}"><td>{event_cell}</td><td>{time}<small>{esc(event.get("timezone_note"))}</small></td><td>{provenance(event)}</td>'
            f'<td><strong>{selection}</strong>{reason}</td><td>{pct(line["probability"] if line else None)}</td>'
            f'<td>{american(line["fair_american"] if line else None)}</td><td>{confidence(line["confidence"] if line else None)}</td>'
            f'<td>{source_links(event["official_sources"], event.get("olbg_url"))}</td></tr>')


def line_row(line):
    event = by_event[line["event_id"]]
    score = ""
    if line.get("score_context"):
        sc = line["score_context"]
        score = f'<small>Score context: {sc["expected_away_points"]:.2f}–{sc["expected_home_points"]:.2f}; total {sc["expected_total"]:.2f}; home margin {sc["expected_home_margin"]:+.2f}. Analysis only.</small>'
    inputs = '<ul class="compact-list">' + ''.join(f'<li><strong>{esc(k)}:</strong> {esc(v)}</li>' for k, v in line["inputs"].items()) + '</ul>'
    return (f'<tr><td><strong>{esc(event["name"])}</strong><small>{esc(sport_names[event["sport"]])} · {esc(event["date"])}</small></td>'
            f'<td>{esc(line["market"])}<small>{esc(line.get("observed_line") or ("Originated primary market" if line["primary"] else "Additional market"))}</small></td>'
            f'<td>{esc(line.get("line") or "—")}</td><td><strong>{esc(line["selection"])}</strong></td><td>{pct(line["probability"])}</td>'
            f'<td>{american(line["fair_american"])}<small>fair, no current quote</small></td><td>{confidence(line["confidence"])}</td>'
            f'<td><details><summary>{esc(line["method"])}</summary><p>{esc(line["formula"])}</p>{inputs}{score}</details></td>'
            f'<td>{source_links(event["official_sources"], event.get("olbg_url"))}</td></tr>')


def prediction_card(pred, prefix=""):
    fact_items = ''.join(
        f'<li><span class="fact-kind">{esc(f["kind"].replace("_", " "))}</span> {esc(f["text"])} '
        f'{link(f["source_url"], "official evidence")}</li>' for f in pred.get("facts", [])
    )
    fact_review = (f'<details class="fact-review"><summary>Inspect {len(pred.get("facts", []))} fact-level evidence links</summary>'
                   f'<ul>{fact_items}</ul><p><strong>Reviewed:</strong> {esc(pred.get("reviewed_at"))}. {esc(pred.get("review_scope"))}</p></details>')
    return (f'<article class="prediction"><div class="prediction-top"><div><p class="eyebrow">{esc(sport_names[pred["sport"]])} · high confidence</p>'
            f'<h3>{esc(pred["match"])}</h3></div><div class="price"><strong>{american(pred["fair_american"])}</strong><span>{pct(pred["probability"])} · fair</span></div></div>'
            f'<p class="selection">Selection: {esc(pred["selection"])}</p><p>{esc(pred["text"])}</p>{fact_review}'
            f'<div class="prediction-foot"><span>{pred["word_count"]} words · {esc(PROVENANCE[pred["provenance"]])}</span>'
            f'<a href="{prefix}matches.html#{esc(pred["event_id"])}">Fixture evidence</a></div>'
            f'{source_links(pred["official_sources"], pred.get("olbg_url"))}</article>')


def shortlist_rows(slug):
    rows = []
    for line in picks[slug]["lines"]:
        event = by_event[line["event_id"]]
        rows.append(f'<tr><td><a href="sports/{slug}.html">{esc(sport_names[slug])}</a></td><td>{esc(event["name"])}<small>{esc(event["date"])}</small></td><td><strong>{esc(line["selection"])}</strong></td><td>{pct(line["probability"])}</td><td>{american(line["fair_american"])}</td><td>{confidence(line["confidence"])}</td><td>{provenance(event)}</td><td>{source_links(event["official_sources"])}</td></tr>')
    return rows


def shell(title, body, active="index", prefix=""):
    nav = [("index", "Overview"), ("matches", "All matches"), ("picks", "Picks & predictions"), ("markets", "Markets"), ("sources", "Sources"), ("flagged", f"Flagged for Review ({counts['flags']})"), ("methodology", "Methodology")]
    menu = ''.join(f'<a href="{prefix}{key}.html"' + (' aria-current="page"' if active == key else '') + f'>{esc(label)}</a>' for key, label in nav)
    sport_links = ''.join(f'<a href="{prefix}sports/{s["slug"]}.html"' + (' aria-current="page"' if active == s["slug"] else '') + f'>{esc(s["name"])}</a>' for s in source["sports"])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · OLBG daily research</title><meta name="description" content="Dated OLBG discovery, official fixtures, independent fair prices and source-linked review across exactly 15 sports.">
<link rel="stylesheet" href="{prefix}style.css"><script src="{prefix}app.js" defer></script></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><a class="brand" href="{prefix}index.html"><span class="brand-mark">O</span><span>OLBG <b>daily desk</b></span></a><button class="menu-button" type="button" data-menu aria-expanded="false">Menu</button>
<nav class="main-nav" data-nav aria-label="Desk navigation">{menu}</nav></header>
<div class="subnav"><span>Snapshot {esc(source['research_cutoff'])}</span><span>0 active OLBG offers</span><span>No current bookmaker prices</span></div>
<div class="layout"><aside><nav aria-label="Exactly 15 sport categories"><p class="nav-title">15 sport categories</p>{sport_links}</nav><a class="root-link" href="{prefix}../index.html">Repository dashboard</a></aside>
<main id="main">{body}</main></div>
<footer><strong>Dated, partial research — not a live feed or betting advice.</strong> Estimates are not guarantees. Official links support the stated fields; they do not prove adjacent values. 18+. <a href="{prefix}flagged.html">Read all review items</a> · <a href="{prefix}../research/olbg-refresh-1b2c50af.md">Latest research & audit record</a></footer>
</body></html>'''


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


# Overview
high_cards = ''.join(prediction_card(p) for p in predictions)
category_cards = []
coverage_rows = []
for sport in source["sports"]:
    slug = sport["slug"]
    rows = by_sport[slug]
    priced = sum(bool(e["line"]) for e in rows)
    high = sum(e["confidence"] == "high" for e in rows)
    short = picks[slug]
    note = source["category_notes"].get(slug, f"{len(rows)} upcoming rows; {priced} with an originated match-winner price; {len(rows)-priced} deliberately blank.")
    category_cards.append(f'<a class="sport-card" href="sports/{slug}.html"><div><h3>{esc(sport["name"])}</h3>{badge(str(high)+" high", "high" if high else "neutral")}</div><p>{esc(note)}</p><span>{len(rows)} fixtures · {priced} priced · shortlist {short["count"]}/5</span></a>')
    coverage_rows.append(f'<tr><td><a href="sports/{slug}.html">{esc(sport["name"])}</a></td><td>{len(rows)}</td><td>{priced}</td><td>{len(rows)-priced}</td><td>{high}</td><td>{short["count"]}/5</td><td>{esc("No manufactured selections; see category note." if short["shortfall"] else "Five supportable selections ranked.")}</td></tr>')
next_rows = ''.join(event_row(e) for e in sorted(matches, key=event_sort)[:12])
index_body = f'''
<section class="hero"><p class="eyebrow">23 October 2026 · exact 15-sport scope</p><h1>OLBG coverage, independently priced.</h1>
<p class="lede">Officially sourced upcoming fixtures, transparent fair lines and an honest review queue. Every OLBG-linked row is distinguished from official context; no event is presented as an active offer.</p>
<div class="actions"><a class="button primary" href="picks.html">Today’s highest-confidence picks</a><a class="button" href="matches.html">Browse all {counts['events']} matches</a><a class="button quiet" href="flagged.html">Review {counts['flags']} flags</a></div></section>
<div class="notice warning"><strong>Availability boundary:</strong> checked OLBG hubs exposed no active tips. Direct event pages marked Expired can still be officially upcoming; both states are shown. This is a checked-page result, not proof of a globally empty OLBG board.</div>
<section class="kpis"><div><strong>{counts['events']}</strong><span>upcoming rows</span></div><div><strong>{counts['priced_matches']}</strong><span>priced matches</span></div><div><strong>{counts['originated_markets']}</strong><span>originated markets</span></div><div><strong>{counts['high']}</strong><span>high-confidence picks</span></div><div><strong>{counts['flags']}</strong><span>review items</span></div></section>
<section><div class="section-head"><div><p class="eyebrow">Executive summary</p><h2>Today’s highest-confidence selections</h2></div><a href="picks.html">All shortlists</a></div><p><strong>{counts['high']} detailed write-ups:</strong> {sum(p['sport']=='basketball' for p in predictions)} Basketball and {sum(p['sport']=='ice-hockey' for p in predictions)} Ice Hockey, covering tonight and officially scheduled games through Sunday 25 October. Every other sport remains below the high-confidence gate or lacks a supportable price. Each estimate is strictly above 70%, with fair American −250 through +10000; prices are originated, not available bookmaker quotes.</p><div class="predictions">{high_cards}</div></section>
<section><div class="section-head"><div><p class="eyebrow">Category coverage</p><h2>Exactly 15 sports</h2></div></div><div class="sport-grid">{''.join(category_cards)}</div></section>
<section><div class="section-head"><div><p class="eyebrow">Next in the snapshot</p><h2>Upcoming matches</h2></div><a href="matches.html">Full fixture table</a></div>{table(['Sport','Match','Date / time','Provenance','Selection','Estimate','Fair American','Confidence','Sources'], [next_rows], 'Next 12 rows by published UTC, then official calendar date', 'next-table')}</section>
<section><div class="section-head"><div><p class="eyebrow">Daily target</p><h2>Five per sport only where supportable</h2></div></div><p>The shortlist ranks confidence and then estimated probability. Blank matches never count toward the target.</p>{table(['Sport','Fixtures','Priced','Blank','High','Shortlist','Coverage decision'], coverage_rows, 'Coverage and top-five shortfall by sport')}</section>
'''
write("index.html", shell("Overview", index_body, "index"))

# All matches
match_rows = ''.join(event_row(e) for e in sorted(matches, key=event_sort))
matches_body = f'''<section class="page-head"><p class="eyebrow">{counts['events']}-row research inventory</p><h1>All upcoming matches</h1><p class="lede">Every row carries official fixture/input links. Blank means no supportable price—not a missing selection that was silently filled.</p></section>
<div class="notice"><strong>Three provenance states:</strong> Active on OLBG now (0 rows), Last seen on OLBG earlier today ({counts['last_seen']}), and Official context only ({counts['official_context']}). The 16:20 inventory is a discovery snapshot, not current availability.</div>
<label class="filter">Filter matches <input type="search" data-filter="all-matches" placeholder="Team, sport, selection, status…"></label>
{table(['Sport','Match / market review','Date / time','Provenance','Selection','Estimate','Fair American','Confidence','Official & OLBG sources'], [match_rows], 'All upcoming fixture rows at the research cutoff', 'all-matches')}
'''
write("matches.html", shell("All matches", matches_body, "matches"))

# Picks and prediction prose
short_rows = ''.join(row for s in source["sports"] for row in shortlist_rows(s["slug"]))
picks_body = f'''<section class="page-head"><p class="eyebrow">Daily selections</p><h1>Picks & predictions</h1><p class="lede">Up to five highest-confidence priced selections per sport. {counts['high']} rows pass the high-confidence evidence and price gates; every card exposes its fact-level official evidence.</p></section>
<section><h2>High-confidence analysis</h2><div class="predictions">{high_cards}</div></section>
<section><div class="section-head"><div><p class="eyebrow">Ranked, not padded</p><h2>Daily top-five shortlists</h2></div></div><p>There are {sum(picks[s['slug']]['count'] for s in source['sports'])} shortlisted selections in total. Sports with no supportable price contribute zero.</p>{table(['Sport','Match','Selection','Estimate','Fair American','Confidence','Provenance','Official sources'], [short_rows], 'Up to five priced selections per sport', 'shortlist-table')}</section>
'''
write("picks.html", shell("Picks & predictions", picks_body, "picks"))

# Originated markets and market investigation notes
market_rows = ''.join(line_row(x) for x in lines)
notes_rows = ''.join(f'<tr><td>{esc(sport_names[e["sport"]])}</td><td>{esc(e["name"])}</td><td>{esc(e["market_note"])}</td><td>{source_links(e["official_sources"], e.get("olbg_url"))}</td></tr>' for e in matches)
markets_body = f'''<section class="page-head"><p class="eyebrow">Independent origination</p><h1>Markets & calculations</h1><p class="lede">{counts['originated_markets']} originated market rows: match winner on {counts['priced_matches']} matches plus four NHL total/puck-line markets. All prices are fair, not bookmaker quotes.</p></section>
<section><h2>Originated lines</h2>{table(['Match','Market','Line','Selection','Estimate','Fair American','Confidence','Method & inputs','Sources'], [market_rows], 'Every originated market with its formula and official inputs', 'markets-table')}</section>
<section><h2>Market investigation register</h2><p>These notes record which handicap, total and other markets were observed or investigated, and why a price is present or blank.</p>{table(['Sport','Match','Investigation / limitation','Sources'], [notes_rows], 'Market-by-market review notes', 'market-notes-table')}</section>
'''
write("markets.html", shell("Markets", markets_body, "markets"))

# Sources, fresh hub audit, raw-capture integrity and row-level review register
source_rows = ''.join(f'<tr><td>{badge(s["kind"], "context" if s["kind"]=="official" else "neutral")}</td><td>{esc(s["label"])}</td><td>{esc(s["captured"])}</td><td>{esc(s["note"])}</td><td>{link(s["url"], s["url"])}</td></tr>' for s in sources)
review = source["review"]
hub_rows = ''.join(
    f'<tr><td>{esc(sport_names[d["sport"]])}</td><td>{esc(d["result"])}</td><td>{esc(d["checked"])}</td><td>{link(d["url"], "inspected OLBG hub")}</td></tr>'
    for d in source["discovery"]
)
reconciliation_rows = ''.join(
    f'<tr><td><code>{esc(r["id"])}</code></td><td>{esc(r["subject"])}</td><td>{esc(r["result"])}</td><td>{link(r["url"], "official source")}</td></tr>'
    for r in review["input_reconciliations"]
)
capture_rows = ''.join(
    f'<tr><td>{esc(c["key"])}</td><td>{esc(c["fetched_at"])}</td><td><code class="hash">{esc(c["sha256"])}</code></td>'
    f'<td>{link(c["url"], "official API")} {link("../data/olbg/captures/"+c["path"], "raw JSON")}</td></tr>'
    for c in source["capture_manifest"]["captures"]
)
row_audit = []
for e in sorted(matches, key=event_sort):
    if e.get("reviewed_at"):
        state = f'{badge("fresh detail review", "high")}<small>{esc(e["reviewed_at"])}</small><details><summary>Review scope</summary><p>{esc(e["review_scope"])}</p></details>'
    else:
        state = f'{badge("dated source capture", "context")}<small>Not freshly detail-reviewed in the latest batch; see each source timestamp.</small>'
    price_state = ("Originated fair price" if e.get("line") else "Blank; " + e["blank_reason"])
    row_audit.append(
        f'<tr><td><a href="matches.html#{esc(e["id"])}"><code>{esc(e["id"])}</code></a><small>{esc(e["name"])}</small></td>'
        f'<td>{esc(sport_names[e["sport"]])}</td><td>{esc(price_state)}</td><td>{state}</td>'
        f'<td>{source_links(e["official_sources"], e.get("olbg_url"))}</td></tr>'
    )
sources_body = f'''<section class="page-head"><p class="eyebrow">Manual review trail</p><h1>Sources & audit</h1><p class="lede">{len(sources)} unique source records, {len(source['discovery'])} fresh OLBG hub checks and a review state for every one of the {len(matches)} fixture rows. Official sporting bodies support factual inputs; OLBG supplies discovery/market provenance only.</p></section>
<div class="notice warning"><strong>A link is not blanket proof.</strong> Read the note beside each source to see which fields it supports. Timestamped availability and uncertified clocks remain limited. The hub audit covers only the inspected renders, not every event or market.</div>
<section><h2>Fresh OLBG hub access audit</h2><p>{esc(review['olbg_scope_note'])} Audit batch completed {esc(review['audit_cutoff'])}.</p>{table(['Sport / hub','Observed result','Audit completed','Manual review link'], [hub_rows], 'Checked-page OLBG results; not a global empty-market claim', 'hub-audit-table')}</section>
<section><h2>Input reconciliation</h2>{table(['ID','Subject','Resolution','Official link'], [reconciliation_rows], 'Explicitly resolved input discrepancies', 'reconciliation-table')}</section>
<section><h2>Raw NHL capture integrity</h2><p>The offline seed checks byte counts and SHA-256 hashes before using these committed official API captures.</p>{table(['Capture','Fetched at','SHA-256','Evidence'], [capture_rows], 'Hash-checked raw official inputs', 'capture-table')}</section>
<section><h2>Row-by-row review register</h2><p>Fresh detail review is reserved for the seven high-confidence candidates. Other rows retain their dated official captures and are not represented as freshly re-read.</p><label class="filter">Filter audit rows <input type="search" data-filter="row-audit-table" placeholder="Team, sport, blank, fresh…"></label>{table(['Event','Sport','Price state','Review state','Official & OLBG links'], row_audit, 'All fixture rows with price and evidence-review state', 'row-audit-table')}</section>
<section><h2>Complete source register</h2>{table(['Kind','Source','Captured / read window','Supported fields / limitation','Manual review link'], [source_rows], 'Official, OLBG and repository sources', 'sources-table')}</section>
'''
write("sources.html", shell("Sources & audit", sources_body, "sources"))

# Review queue
flag_rows = ''.join(f'<tr id="{esc(f["id"])}"><td><code>{esc(f["id"])}</code></td><td>{badge(f["severity"], "warning" if f["severity"] in {"irregularity","repository"} else "neutral")}</td><td><strong>{esc(f["title"])}</strong><p>{esc(f["detail"])}</p></td><td>{source_links(f["links"])}</td></tr>' for f in flags)
flagged_body = f'''<section class="page-head"><p class="eyebrow">Clearly labeled review queue</p><h1>Flagged for Review</h1><p class="lede">{len(flags)} source-linked findings: irregularities, unpriced rows, capped selections and evidence limitations. Flags do not hide a broken value; they explain what remains unknown.</p></section>
<div class="notice warning"><strong>Do not treat these as resolved.</strong> In particular, review the OLBG line/comment mismatches, PDC clock conflict, GAA status conflict, NBA report timestamp and repository conflict markers.</div>
{table(['ID','Severity','Finding','Manual review links'], [flag_rows], 'All irregularities, blanks and limitations', 'flags-table')}
'''
write("flagged.html", shell("Flagged for Review", flagged_body, "flagged"))

# Methodology
method_body = f'''<section class="page-head"><p class="eyebrow">Reproducible rules</p><h1>Methodology</h1><p class="lede">Simple public formulas, exact official inputs, explicit abstention. No OLBG tipster share is treated as a probability.</p></section>
<section class="method-grid"><article><h2>Two-way log5</h2><p><code>p(A beats B) = (a − ab) / (a + b − 2ab)</code>.</p><ul><li>NBA: official 2025-26 away-road and home-home win fractions, 41 games per split.</li><li>NHL: exact points / (2 × games), not rounded percentage strings.</li><li>MLB: official 162-game overall records.</li><li>EuroLeague: official wins / games after Round 7; detailed-evidence gate closed.</li></ul></article>
<article><h2>Ranking-value share</h2><p><code>p(player 1) = rating 1 / (rating 1 + rating 2)</code>, with the complement for player 2. Used for ATP ranking points, PDC world-ranking pounds and same-format ICC ODI ratings. Ranking-only rows are capped below high; missing ratings remain blank.</p></article>
<article><h2>NHL totals & puck lines</h2><p>Expected goals combine official scoring and opponent allowance per game. Independent Poisson marginals are truncated at 40 and normalized. A regulation tie adds one goal. Only observed 6.5 and 1.5 lines on the two OLBG-linked games are priced; these extra markets remain low confidence.</p></article>
<article><h2>Fair American price</h2><p>Favorite: <code>−100p/(1−p)</code>. Underdog/even: <code>100(1−p)/p</code>. Fair decimal is <code>1/p</code>. Rounded to a whole American unit. These are originated prices, never current bookmaker quotes.</p></article></section>
<section><h2>High-confidence gate</h2><ol><li>Estimated chance strictly greater than 70%.</li><li>Fair American between −250 and +10000 inclusive.</li><li>Detailed official matchup/statistical evidence and dated availability review where a standard official report exists.</li><li>Unique, natural prediction of at least 30 words with an explicit selection, official source links, and fact-level evidence covering team form, recent form/history, a player or goalie, and availability or its documented absence.</li></ol><p>Rows meeting only the arithmetic condition stay capped and receive a <code>CAP-…</code> flag. Medium starts at 60%; lower priced estimates are low.</p></section>
<section><h2>Provenance and blanks</h2><p><strong>Active on OLBG now</strong> requires a current active offer; there are none. <strong>Last seen on OLBG earlier today</strong> includes expired direct pages and the 16:20 discovery inventory. <strong>Official context only</strong> means no individual OLBG event was observed. Official sources control fixture facts; OLBG supplies discovery only.</p><p>Every blank row states why no price is supportable and appears in the review queue. No quota, injury, timezone, rating or market value is manufactured.</p></section>
<section><h2>Reproduce offline</h2><pre><code>python scripts/olbg_seed.py
python scripts/olbg_model.py
python scripts/olbg_predictions.py
python scripts/olbg_build.py
python scripts/olbg_verify.py
python -m unittest discover -s tests -q
python scripts/integration_audit.py</code></pre><p>The research cutoff is <strong>{esc(source['research_cutoff'])}</strong>. CI rebuilds committed evidence; it does not refresh events or availability.</p></section>
'''
write("methodology.html", shell("Methodology", method_body, "methodology"))

# Category subpages
for sport in source["sports"]:
    slug, name = sport["slug"], sport["name"]
    rows = sorted(by_sport[slug], key=event_sort)
    high = [p for p in predictions if p["sport"] == slug]
    note = source["category_notes"].get(slug, "Upcoming rows are restricted to official-source evidence. Official-context rows are not asserted OLBG offers.")
    if rows:
        body_rows = ''.join(event_row_local(e) for e in rows)
        fixture_section = table(['Match / market review','Date / time','Provenance','Selection','Estimate','Fair American','Confidence','Sources'], [body_rows], f'{name}: all upcoming rows', f'{slug}-matches')
    else:
        fixture_section = f'<div class="empty"><h2>No supportable upcoming rows</h2><p>{esc(note)}</p><p><a href="../flagged.html">Open the source-linked review queue</a>.</p></div>'
    cards = ''.join(prediction_card(p, "../") for p in high)
    short = ''.join(shortlist_rows(slug))
    # Category shortlist links need ../sports paths adjusted by replacing root-relative links.
    short = short.replace('href="sports/', 'href="../sports/').replace('href="matches.html', 'href="../matches.html')
    shortlist_section = table(['Sport','Match','Selection','Estimate','Fair American','Confidence','Provenance','Official sources'], [short], f'{name}: ranked daily shortlist (maximum five)', f'{slug}-shortlist') if short else '<p class="blank-block">No priced selection qualifies for the daily shortlist.</p>'
    body = f'''<section class="page-head"><p class="eyebrow">Category · {esc(name)}</p><h1>{esc(name)}</h1><p class="lede">{esc(note)}</p></section>
<section class="kpis compact"><div><strong>{len(rows)}</strong><span>upcoming rows</span></div><div><strong>{sum(bool(e['line']) for e in rows)}</strong><span>priced matches</span></div><div><strong>{len(high)}</strong><span>high picks</span></div><div><strong>{picks[slug]['count']}/5</strong><span>daily shortlist</span></div></section>
{('<section><h2>High-confidence analysis</h2><div class="predictions">'+cards+'</div></section>') if cards else ''}
<section><h2>Daily selections</h2>{shortlist_section}</section>
<section><h2>All upcoming rows</h2>{fixture_section}</section>
<section><h2>Official discovery hub</h2><p>{link(sport['hub'], 'OLBG '+name+' hub')} was checked for coverage. Its tipster percentages are not used as probabilities. Latest inspected result: <strong>{esc('; '.join(d['result'] for d in source['discovery'] if d['sport']==slug))}</strong> <a href="../methodology.html">Read the pricing and provenance rules</a>.</p></section>
'''
    write(f"sports/{slug}.html", shell(name, body, slug, "../"))

STYLE = r'''
:root{--ink:#13231f;--muted:#5c6b66;--paper:#f5f7f4;--card:#fff;--line:#d9e1dc;--green:#0b6b50;--green2:#0e8a66;--lime:#d9f99d;--amber:#fff4cf;--red:#9b332a;--blue:#245a8d}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--green);text-underline-offset:3px}a:hover{color:#064b38}h1,h2,h3{line-height:1.15;letter-spacing:-.025em}h1{font-size:clamp(2rem,4vw,3.5rem);margin:.25rem 0 1rem}h2{font-size:1.55rem;margin:0 0 .7rem}h3{margin:.2rem 0}p{margin:.45rem 0 1rem}small{display:block;color:var(--muted);font-size:.78rem;margin-top:.2rem}code{background:#eaf0eb;border-radius:4px;padding:.1rem .3rem}pre{white-space:pre-wrap;background:#12241e;color:#effaf4;padding:1rem;border-radius:10px;overflow:auto}pre code{background:none;padding:0}.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:white;padding:1rem;z-index:20}.site-header{display:flex;align-items:center;gap:1.5rem;background:#10261f;color:#fff;padding:.8rem clamp(1rem,3vw,2.5rem);position:sticky;top:0;z-index:10}.brand{display:flex;align-items:center;gap:.6rem;color:#fff;text-decoration:none;font-size:1.05rem;white-space:nowrap}.brand b{display:block;font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:#b9d7ca}.brand-mark{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--lime);color:#10261f;font-weight:900}.main-nav{display:flex;gap:.15rem;flex-wrap:wrap}.main-nav a{color:#d8e8df;text-decoration:none;padding:.45rem .6rem;border-radius:6px;font-size:.82rem}.main-nav a:hover,.main-nav a[aria-current=page]{background:#2b473c;color:#fff}.menu-button{display:none}.subnav{display:flex;gap:1.4rem;flex-wrap:wrap;background:#1d392f;color:#d8e8df;padding:.4rem clamp(1rem,3vw,2.5rem);font-size:.76rem}.layout{display:grid;grid-template-columns:190px minmax(0,1fr);max-width:1680px;margin:auto}.layout aside{padding:1.5rem 1rem;border-right:1px solid var(--line);min-height:80vh}.layout aside nav{position:sticky;top:105px}.layout aside a{display:block;color:var(--muted);text-decoration:none;padding:.27rem .35rem;font-size:.83rem}.layout aside a[aria-current=page]{color:var(--green);font-weight:750}.nav-title{text-transform:uppercase;letter-spacing:.1em;font-size:.68rem;color:#76877f}.root-link{margin-top:1.3rem;border-top:1px solid var(--line);padding-top:1rem!important}main{padding:2rem clamp(1rem,3vw,2.5rem);min-width:0}main>section{margin:0 0 2.7rem}footer{padding:2rem clamp(1rem,3vw,2.5rem);border-top:1px solid var(--line);color:var(--muted);font-size:.8rem}.hero{padding:2rem 0 1rem;max-width:1050px}.lede{font-size:1.08rem;color:var(--muted);max-width:950px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:var(--green);font-weight:800;font-size:.7rem;margin:0 0 .4rem}.actions{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1.3rem}.button{border:1px solid var(--green);border-radius:7px;padding:.65rem .9rem;text-decoration:none;font-weight:700}.button.primary{background:var(--green);color:#fff}.button.primary:hover{background:#07513d}.button.quiet{border-color:var(--line)}.notice{padding:1rem 1.2rem;border-left:4px solid var(--blue);background:#eaf2f8;margin:1rem 0 2rem;border-radius:0 8px 8px 0}.notice.warning{background:var(--amber);border-color:#b47c08}.kpis{display:grid;grid-template-columns:repeat(5,minmax(110px,1fr));gap:.7rem;margin:1.5rem 0 2.5rem}.kpis.compact{grid-template-columns:repeat(4,minmax(100px,1fr));max-width:760px}.kpis div{background:var(--card);border:1px solid var(--line);padding:1rem;border-radius:10px}.kpis strong{display:block;font-size:1.8rem;letter-spacing:-.04em}.kpis span{color:var(--muted);font-size:.77rem}.section-head{display:flex;justify-content:space-between;gap:1rem;align-items:end}.sport-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem}.sport-card{background:var(--card);border:1px solid var(--line);padding:1rem;border-radius:10px;text-decoration:none;color:var(--ink)}.sport-card:hover{border-color:var(--green2);transform:translateY(-1px)}.sport-card>div{display:flex;justify-content:space-between;gap:.5rem}.sport-card p{color:var(--muted);font-size:.85rem}.sport-card>span{font-size:.75rem;font-weight:750;color:var(--green)}.badge{display:inline-block;padding:.15rem .43rem;border-radius:99px;background:#e9efeb;color:#42534c;font-size:.69rem;font-weight:800;white-space:nowrap}.badge.high{background:#d6f3e4;color:#075a3e}.badge.medium{background:#e3edf7;color:#245a8d}.badge.low{background:#f2eee4;color:#725c2c}.badge.seen{background:#e5f0eb;color:#165d46}.badge.context{background:#ececf7;color:#4c4c79}.badge.active{background:#d6f3e4;color:#075a3e}.badge.warning{background:#ffe4cf;color:#8a3f16}.predictions{display:grid;gap:1rem}.prediction{background:var(--card);border:1px solid #bfd7ca;border-top:4px solid var(--green);border-radius:11px;padding:1.2rem}.prediction-top{display:flex;justify-content:space-between;gap:1rem}.prediction .price{text-align:right;min-width:110px}.prediction .price strong{display:block;font-size:1.6rem}.prediction .price span{color:var(--muted);font-size:.76rem}.prediction .selection{display:inline-block;background:#eaf6ef;color:#075a3e;font-weight:800;padding:.35rem .55rem;border-radius:5px}.prediction-foot{display:flex;justify-content:space-between;gap:1rem;color:var(--muted);font-size:.75rem;border-top:1px solid var(--line);padding-top:.6rem}.source-list{list-style:none;padding:0;margin:.3rem 0;font-size:.74rem;min-width:150px}.source-list li{margin:.2rem 0;overflow-wrap:anywhere}.compact-list{padding-left:1rem;font-size:.78rem}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:9px;background:var(--card);margin:.8rem 0 1rem}table{border-collapse:collapse;width:100%;min-width:850px;font-size:.79rem}caption{text-align:left;font-weight:800;padding:.8rem 1rem;background:#eef3ef;color:#384a42}th{text-align:left;background:#f7f9f7;color:#4a5b53;font-size:.68rem;text-transform:uppercase;letter-spacing:.055em}th,td{padding:.68rem .7rem;border-bottom:1px solid var(--line);vertical-align:top}tbody tr:last-child td{border-bottom:0}tbody tr:hover{background:#fbfdfb}td details{max-width:340px}td details summary{cursor:pointer;color:var(--green);font-size:.72rem;margin-top:.25rem}td p{font-size:.78rem}.filter{display:block;max-width:480px;font-weight:700;margin:1rem 0}.filter input{display:block;width:100%;padding:.65rem .75rem;border:1px solid #aabbb1;border-radius:7px;margin-top:.35rem;font:inherit}.method-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.method-grid article{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1.1rem}.empty,.blank-block{padding:1.2rem;background:#fff;border:1px dashed #aabbb1;border-radius:9px}.blank{color:#77847e}.page-head{max-width:1050px;margin-bottom:1.3rem!important}.muted{color:var(--muted)}.fact-review{margin:.9rem 0;background:#f4f8f5;border:1px solid var(--line);border-radius:7px;padding:.65rem .8rem}.fact-review summary{cursor:pointer;color:var(--green);font-weight:750}.fact-review ul{padding-left:1.15rem}.fact-review li{margin:.45rem 0}.fact-kind{display:inline-block;text-transform:uppercase;letter-spacing:.05em;font-size:.65rem;font-weight:800;color:var(--muted)}.hash{display:block;max-width:250px;overflow-wrap:anywhere;word-break:break-all}
@media(max-width:1100px){.sport-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.site-header{position:static}.layout{grid-template-columns:160px minmax(0,1fr)}.main-nav a{font-size:.74rem}.kpis{grid-template-columns:repeat(3,1fr)}}
@media(max-width:760px){.site-header{flex-wrap:wrap}.menu-button{display:block;margin-left:auto;background:#29473b;color:#fff;border:1px solid #547164;border-radius:6px;padding:.45rem .7rem}.main-nav{display:none;width:100%}.main-nav.open{display:grid;grid-template-columns:1fr 1fr}.layout{display:block}.layout aside{display:none}main{padding:1.2rem .8rem}.sport-grid,.method-grid{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}.prediction-top{display:block}.prediction .price{text-align:left;margin:.6rem 0}.subnav{gap:.6rem}.section-head{display:block}table{min-width:780px}}
'''
write("style.css", STYLE)
write("app.js", r'''
document.querySelectorAll('[data-menu]').forEach(function(button){button.addEventListener('click',function(){var nav=document.querySelector('[data-nav]');var open=nav.classList.toggle('open');button.setAttribute('aria-expanded',String(open));});});
document.querySelectorAll('[data-filter]').forEach(function(input){input.addEventListener('input',function(){var table=document.getElementById(input.dataset.filter);var query=input.value.toLowerCase().trim();table.querySelectorAll('tbody tr').forEach(function(row){row.hidden=query && !row.textContent.toLowerCase().includes(query);});});});
''')
print(f"Built /olbg/: {len(list(OUT.rglob('*.html')))} HTML pages, {counts['events']} fixture rows, {counts['originated_markets']} originated markets")
