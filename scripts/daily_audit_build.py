#!/usr/bin/env python3
"""Build the /daily/ dashboard from the committed data in data/daily-audit/.

Every href is composed from a page depth so nothing can point at the wrong
page: a page at daily/ uses '' as its in-layer prefix and '../' as its repo-root
prefix; a page at daily/sports/ uses '../' and '../../'.

Deterministic: no clock is read, the capture timestamp is the one stored in the
data files.
"""

from __future__ import annotations

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "daily-audit")
OUT = os.path.join(ROOT, "daily-audit")
CURRENT = os.path.join(ROOT, "data", "current")

NAV = [
    ("index.html", "Dashboard"),
    ("matches.html", "Matches"),
    ("lines.html", "Lines"),
    ("picks.html", "Picks"),
    ("predictions.html", "Predictions"),
    ("sports/index.html", "By sport"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
    ("methodology.html", "Methodology"),
]

TITLE = "Daily audit — 23 October 2026"

# The 17 eligible sports of the brief, in the order the layer publishes them.
SPORTS = [
    ("aussie-rules", "Aussie Rules", 22, "not surveyed", "No OLBG hub capture was taken this session (DL-14)."),
    ("baseball", "Baseball", 12, "covered elsewhere", "See the current desk for MLB rows captured today."),
    ("basketball", "Basketball", 4, "covered elsewhere", "See the current desk for EuroLeague rows captured today."),
    ("cricket", "Cricket", 7, "rows here, no lines", "Nine official ICC fixtures published; no official strength input exists, so prices are blank (DL-04)."),
    ("darts", "Darts", 15, "verified unavailable", "Eight OLBG fixtures listed, but the PDC pages returned a consent wall, so no official data (DL-10)."),
    ("esports", "eSports", 23, "empty on OLBG", "OLBG's own eSports hub renders 'No tips found.' (DL-11)."),
    ("gaelic-football", "Gaelic Football", 25, "verified unavailable", "Two in-window club fixtures on OLBG; no official GAA page for them was found (DL-09)."),
    ("golf", "Golf", 5, "not surveyed", "No OLBG hub capture was taken this session (DL-14)."),
    ("greyhounds", "Greyhounds", 28, "not surveyed", "No OLBG hub capture was taken this session (DL-14)."),
    ("handball", "Handball", 20, "covered elsewhere", "See the current desk for EHF Champions League rows captured today."),
    ("ice-hockey", "Ice Hockey", 13, "covered elsewhere", "See the current desk for NHL rows captured today."),
    ("motor-racing", "Motor Racing", 14, "covered elsewhere", "See the current desk for the Formula 1 round captured today."),
    ("rugby-league", "Rugby League", 10, "no fixture", "OLBG lists only 2027 outrights; no match in the capture window (DL-12)."),
    ("rugby-union", "Rugby Union", 9, "covered elsewhere", "See the current desk for United Rugby Championship rows captured today."),
    ("snooker", "Snooker", 8, "covered elsewhere", "See the current desk for WST Northern Ireland Open rows captured today."),
    ("tennis", "Tennis", 3, "rows and picks here", "Eight official ATP quarter-finals, 288 originated prices, five written picks."),
    ("volleyball", "Volleyball", 21, "not surveyed", "No OLBG hub capture was taken this session (DL-14)."),
]
SPORT_NAME = {row[0]: row[1] for row in SPORTS}

CSS = "../assets/style.css"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as handle:
        return json.load(handle)


def load_current(name):
    path = os.path.join(CURRENT, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def domain(url):
    return url.split("//", 1)[-1].split("/", 1)[0] if url else ""


def source_link(url, label=None):
    if not url:
        return '<span class="pill">no source</span>'
    return f'<a href="{esc(url)}" rel="noopener">{esc(label or domain(url))}</a>'


def dash(value):
    return esc(value) if value not in (None, "") else '<span class="muted">—</span>'


def confidence_badge(conf):
    if not conf:
        return '<span class="pill">unpriced</span>'
    return f'<span class="conf {esc(conf)}">{esc(conf)}</span>'


def window_badge(flag):
    if flag is True:
        return '<span class="pill ok">in −250 window</span>'
    return '<span class="pill warn">outside −250 window</span>'


def page(title, active, body, depth=0):
    inlayer = "../" * depth
    root = "../" * (depth + 1)
    links = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{esc(inlayer + href)}"{current}>{esc(label)}</a>')
    nav = "".join(links)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG2 {esc(TITLE)}</title>
<meta name="description" content="Dated research snapshot of officially verified fixtures, originated fair prices and written picks. Not a live feed and not betting advice.">
<link rel="stylesheet" href="{esc(root + "assets/style.css")}">
<link rel="stylesheet" href="{esc(inlayer + "assets/daily.css")}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f172a'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%2314b8a6'/%3E%3C/svg%3E">
</head>
<body>
<header class="topbar"><div class="wrap bar">
<a class="brand" href="{esc(root + "index.html")}"><span class="dot"></span>OLBG2 <span class="brand-sub">daily audit</span></a>
<nav class="nav" aria-label="Daily slate navigation">{nav}</nav>
</div></header>
<div class="stripe"><div class="wrap"><strong>Snapshot 2026-10-22 21:30 UTC</strong> · {COUNT['fixtures']} fixtures · {len(rows_by_sport)} sports with rows · {COUNT['prices']} originated prices · {len(predictions_doc)} written picks · <a href="{esc(inlayer + "flagged.html")}">{len(flags_doc)} review items</a> · <a href="{esc(root + "current/index.html")}">current desk</a></div></div>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p><strong>Research snapshot, not a live feed and not betting advice.</strong> Prices are this layer's own fair odds derived from the model on the
<a href="{esc(inlayer + "methodology.html")}">methodology page</a>; they are not bookmaker quotes. A linked official page records provenance for the
fixture and the inputs on that row — it is not proof that every value beside it is current. Values that could not be confirmed are blank and listed on
<a href="{esc(inlayer + "flagged.html")}">Flagged for Review</a>. 18+.</p>
<p class="tiny">Built by <code>scripts/daily_audit_build.py</code> from checked-in captures in <code>data/daily-audit/</code>. Other layers:
<a href="{esc(root + "index.html")}">root dashboard</a> · <a href="{esc(root + "current/index.html")}">current desk</a> ·
<a href="{esc(root + "final/index.html")}">consolidated desk</a>.</p>
</div></footer>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #
fixtures_doc = load("fixtures.json")
fixtures = fixtures_doc["fixtures"]
lines_doc = load("lines.json")
predictions_doc = load("predictions.json")["predictions"]
flags_doc = load("flags.json")["flags"]
sources_doc = load("sources.json")["sources"]
inputs_doc = load("inputs.json")

FIX = {f["id"]: f for f in fixtures}
PRED_BY_FIX = {p["fixture_id"]: p for p in predictions_doc}
LINES_BY_FIX = {}
for row in lines_doc["rows"]:
    LINES_BY_FIX.setdefault(row["fixture_id"], []).append(row)
COUNT = lines_doc["counts"]
TOP_PICKS = lines_doc["top_picks"].get("tennis", [])
WINNER = {w["fixture_id"]: w for w in lines_doc["winner_picks"]}

cur_matches = load_current("matches.json")
cur_preds = load_current("predictions.json")
cur_rows_by_sport, cur_preds_by_sport = {}, {}
if cur_matches:
    for row in cur_matches["matches"]:
        cur_rows_by_sport[row["sport"]] = cur_rows_by_sport.get(row["sport"], 0) + 1
if cur_preds:
    for row in cur_preds.get("predictions", []):
        cur_preds_by_sport[row["sport"]] = cur_preds_by_sport.get(row["sport"], 0) + 1

rows_by_sport = {}
for fixture in fixtures:
    rows_by_sport.setdefault(fixture["sport"], []).append(fixture)


def match_label(fixture):
    return f'{fixture["a"]["name"]} v {fixture["b"]["name"]}'


def fixture_table(rows, depth=0):
    inlayer = "../" * depth
    sport_href = (lambda slug: f"sports/{slug}.html") if depth == 0 else (lambda slug: f"{slug}.html")
    out = ["""<div class="tablewrap"><table class="data">
<thead><tr><th>Sport</th><th>Competition</th><th>Match</th><th>Date</th><th>Time (verbatim)</th><th>Round</th><th>Official source</th><th>Lines</th></tr></thead><tbody>"""]
    for f in rows:
        priced = [r for r in LINES_BY_FIX.get(f["id"], []) if r["p"] is not None]
        status = f'{len(priced)} prices' if priced else '<span class="pill warn">blank</span>'
        out.append(
            "<tr>"
            f'<td><a href="{esc(sport_href(f["sport"]))}">{esc(SPORT_NAME[f["sport"]])}</a></td>'
            f'<td>{dash(f["competition"])}</td>'
            f'<td><strong>{esc(match_label(f))}</strong></td>'
            f'<td>{dash(f.get("date"))}</td>'
            f'<td>{dash(f.get("time_note"))}</td>'
            f'<td>{dash(f.get("round"))}</td>'
            f'<td>{source_link(f["official_url"])}</td>'
            f'<td>{status}</td>'
            "</tr>"
        )
        if not f.get("date") and f.get("date_note"):
            out.append(f'<tr class="note"><td colspan="8">{esc(f["date_note"])}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


# --------------------------------------------------------------------------- #
# landing page
# --------------------------------------------------------------------------- #
def landing():
    cards = []
    for pick in TOP_PICKS:
        fixture = FIX[pick["fixture_id"]]
        pred = PRED_BY_FIX.get(pick["fixture_id"], {})
        cards.append(f"""<a class="card" href="predictions.html#{esc(pred.get('id', ''))}">
<div class="cardhead"><span class="pill">{esc(fixture['competition'])}</span>{confidence_badge(pick['confidence'])}</div>
<h3>{esc(match_label(fixture))}</h3>
<p><strong>{esc(pick['selection'])}</strong> · fair {esc(pick['fair_decimal'])} ({esc(pick['fair_american']):>}) · model {pick['p']*100:.1f}%</p>
<div class="metrics"><span>{window_badge(pick['in_band'])}</span></div></a>""")

    cov = []
    for slug, name, olbg_id, status, note in SPORTS:
        here = len(rows_by_sport.get(slug, []))
        preds = sum(1 for p in predictions_doc if p["sport"] == slug)
        cov.append(
            "<tr>"
            f'<td><a href="sports/{esc(slug)}.html">{esc(name)}</a></td>'
            f'<td>{here or "—"}</td><td>{preds or "—"}</td>'
            f'<td>{cur_rows_by_sport.get(slug, "—")}</td>'
            f'<td>{cur_preds_by_sport.get(slug, "—")}</td>'
            f'<td>{esc(status)}</td>'
            f'<td class="small">{esc(note)}</td>'
            "</tr>"
        )

    probe = lines_doc.get("window_probe") or {}
    body = f"""
<p class="crumb">Dashboard</p>
<section class="hero">
<p class="eyebrow">Daily slate · captured 2026-10-22 21:30 UTC</p>
<h1>{esc(TITLE)}</h1>
<p class="lede">A dated snapshot built from pages fetched first-hand this session: the ATP Tour's own order of play and draws
for the Almaty and Brussels quarter-finals, and the ICC's own fixtures list. Every fixture row carries the official page it was read from;
every price is this layer's own fair line, not a bookmaker quote. Where no official input existed the price is blank and the reason is on the
<a href="flagged.html">Flagged for Review</a> page.</p>
<div class="cta">
<a class="button primary" href="matches.html">All {COUNT['fixtures']} fixtures</a>
<a class="button" href="predictions.html">The {len(predictions_doc)} written picks</a>
<a class="button" href="lines.html">{COUNT['prices']} originated prices</a>
<a class="button" href="flagged.html">{len(flags_doc)} review items</a>
</div>
</section>

<div class="kpis">
<div class="kpi"><div class="v">{COUNT['fixtures']}</div><div class="k">Fixtures published</div><div class="s">{' · '.join(f"{len(v)} {SPORT_NAME[k]}" for k, v in sorted(rows_by_sport.items()))}</div></div>
<div class="kpi"><div class="v">{COUNT['lined_fixtures']}</div><div class="k">Fixtures with prices</div><div class="s">{COUNT['unlined_fixtures']} blank, with reasons</div></div>
<div class="kpi"><div class="v">{COUNT['prices']}</div><div class="k">Originated prices</div><div class="s">across {COUNT['markets']} fixture-markets</div></div>
<div class="kpi"><div class="v">{COUNT['high_confidence_winners']}</div><div class="k">High-confidence winners</div><div class="s">p ≥ 0.7000</div></div>
<div class="kpi"><div class="v">{COUNT['in_band_prices']}</div><div class="k">Inside −250 window</div><div class="s">see DL-05</div></div>
</div>

<div class="notice warn"><strong>Read this before the numbers.</strong> The brief asks for picks that are both above 70% and priced between
−250 and +10000. Those two conditions intersect in a window 1.43 probability points wide (0.7000 to 0.714286). With half-point lines the
closest of the {COUNT['prices']} originated prices is <strong>{esc(probe.get('selection', '—'))}</strong> at p = {probe.get('p', 0)} (fair
{esc(probe.get('fair_american', '—'))}), {esc(probe.get('gap_points', '—'))} points outside it. The five published picks are therefore the
highest-confidence match winners and each one is labelled <em>outside the −250 window</em> rather than reclassified. Detail: <a href="flagged.html#DL-05">DL-05</a>.</div>

<h2>The five for today</h2>
<p class="sub">Five highest-confidence match-winner selections in tennis, each with a written prediction of at least 30 words on
<a href="predictions.html">the predictions page</a>. Cricket has no pick because it has no official strength input (<a href="flagged.html#DL-04">DL-04</a>).</p>
<div class="grid sports">{''.join(cards)}</div>

<h2>Coverage across all 17 eligible sports</h2>
<p class="sub">This layer and the <a href="../current/index.html">current desk</a> are separate snapshots of the same day. Their counts must not be
added together: the desks overlap and neither is a complete inventory. Zero in a column means that snapshot has no row for the sport, not that the
sport has no fixtures.</p>
<div class="tablewrap"><table class="data">
<thead><tr><th>Sport</th><th>Rows here</th><th>Picks here</th><th>Rows in <a href="../current/index.html">current desk</a></th><th>Picks there</th><th>Status</th><th>Why</th></tr></thead>
<tbody>{''.join(cov)}</tbody></table></div>

<h2>What was fetched, and what failed</h2>
<div class="two-col">
<div class="panel"><h3>Read successfully</h3><ul>
<li>OLBG global tips page, tennis hub, tennis event page, cricket hub, darts hub, Gaelic football hub, rugby league hub, eSports hub</li>
<li>ATP Tour: Almaty and Brussels daily schedules, singles draws, live scores, top-12 rankings</li>
<li>ICC fixtures list, the Afghanistan v Zimbabwe match page</li>
<li>GAA October 2026 fixtures page</li>
</ul></div>
<div class="panel"><h3>Attempted and unusable</h3><ul>
<li>WTA Hong Kong draws — site chrome only, no draw content (<a href="flagged.html#DL-03">DL-03</a>)</li>
<li>ICC team rankings — the table body rendered empty (<a href="flagged.html#DL-04">DL-04</a>)</li>
<li>PDC /matches and the European Championship page — cookie-consent wall (<a href="flagged.html#DL-10">DL-10</a>)</li>
<li>OLBG eSports hub — empty state, "No tips found." (<a href="flagged.html#DL-11">DL-11</a>)</li>
</ul></div>
</div>

<h2>How a price is made</h2>
<p>Each player gets a rating from their official ATP seeding plus verified sets won and lost in the tournament. The rating gap becomes a win
probability through a logistic curve; the gap in games becomes a normal margin distribution, which prices every alternate handicap and total on the
<a href="lines.html">lines page</a>. The constants are ours, listed in full on the <a href="methodology.html">methodology page</a>, and reproducible with
<code>python3 scripts/daily_audit_model.py</code>. No bookmaker price is read, compared or implied anywhere in this layer.</p>
"""
    return page("Dashboard", "index.html", body)


# --------------------------------------------------------------------------- #
# matches
# --------------------------------------------------------------------------- #
def matches_page():
    body = f"""
<p class="crumb">Dashboard / Matches</p>
<h1>Fixtures — 23 and 24 October 2026</h1>
<p class="lede">Every row was read from an official page fetched in this session, and the source link on the row is that page. Dates and times are
printed verbatim from the source that supplied them: no timezone is converted, and a date the source did not print is left blank with the reason
shown underneath rather than guessed.</p>
{fixture_table(fixtures)}

<h2>What the table does not claim</h2>
<div class="panel">
<ul>
<li>The eight tennis rows are singles quarter-finals only. OLBG's sixteen tennis events also include eight WTA matches that could not be verified
(<a href="flagged.html#DL-03">DL-03</a>).</li>
<li>The nine cricket rows have no date because the ICC list prints a start time and "(Your time)" but no date (<a href="flagged.html#DL-08">DL-08</a>).</li>
<li>A fixture whose official page does not state a timezone keeps the source's own wording in the time column; nothing is converted to UTC
(<a href="flagged.html#DL-01">DL-01</a>).</li>
<li>No cricket row has a price: the ICC rankings table rendered empty, so there is no official strength input and no line
(<a href="flagged.html#DL-04">DL-04</a>).</li>
</ul></div>
"""
    return page("Matches", "matches.html", body)


# --------------------------------------------------------------------------- #
# lines
# --------------------------------------------------------------------------- #
def lines_page():
    sections = []
    for sport in ("tennis", "cricket"):
        for fixture in rows_by_sport.get(sport, []):
            rows = LINES_BY_FIX.get(fixture["id"], [])
            priced = [r for r in rows if r["p"] is not None]
            head = f"""<h2>{esc(match_label(fixture))}</h2>
<p class="sub">{esc(fixture['competition'])} · {esc(fixture['round'])} · {esc(fixture['date'] or 'date not printed')} · {esc(fixture['time_note'])} ·
{source_link(fixture['official_url'])}</p>"""
            if not priced:
                sections.append(head + f'<div class="notice"><strong>No price originated.</strong> {esc(rows[0]["blank_reason"])} '
                                       f'See <a href="flagged.html#DL-04">DL-04</a>.</div>')
                continue
            table = ["""<div class="tablewrap"><table class="data">
<thead><tr><th>Market</th><th>Selection</th><th>Model probability</th><th>Fair decimal</th><th>Fair American</th><th>Confidence</th><th>−250 window</th></tr></thead><tbody>"""]
            market_label = {"match_winner": "Match winner", "games_handicap": "Games handicap", "total_games": "Total games"}
            for row in rows:
                table.append(
                    "<tr>"
                    f'<td>{esc(market_label.get(row["market"], row["market"]))}</td>'
                    f'<td>{esc(row["selection"])}</td>'
                    f'<td>{row["p"]*100:.2f}%</td>'
                    f'<td>{esc(row["fair_decimal"])}</td>'
                    f'<td>{esc(row["fair_american"])}</td>'
                    f'<td>{confidence_badge(row["confidence"])}</td>'
                    f'<td>{"yes" if row["in_band"] else "no"}</td>'
                    "</tr>"
                )
            table.append("</tbody></table></div>")
            sections.append(head + "".join(table))

    body = f"""
<p class="crumb">Dashboard / Lines</p>
<h1>Originated lines</h1>
<p class="lede">{COUNT['prices']} fair prices across {COUNT['markets']} fixture-markets, derived only from the official inputs on this layer's
methodology page. Nothing here is a bookmaker quote; a "fair" price is 1 ÷ model probability with no margin added. Alternate handicap and total
lines are shown so the whole market can be inspected, not only the selection that was picked.</p>
<div class="notice"><strong>No price here is inside the brief's −250 window.</strong> That is a finding, not an omission: see
<a href="flagged.html#DL-05">DL-05</a> for the arithmetic and for why manufacturing a quarter-game line to sit inside it was rejected.</div>
<div class="notice"><strong>Reading the American column.</strong> A fair decimal of 1.09 prints as −1176 because that is how American odds encode a
heavy favourite. The <em>−250 window</em> column answers the brief's price condition (American ≥ −250); every row in this layer says <em>no</em>,
which is the finding recorded as <a href="flagged.html#DL-05">DL-05</a>.</div>
{''.join(sections)}
"""
    return page("Lines", "lines.html", body)


# --------------------------------------------------------------------------- #
# picks
# --------------------------------------------------------------------------- #
def picks_page():
    order = sorted(lines_doc["winner_picks"], key=lambda w: (w["sport"], -w["p"]))
    rows = []
    for pick in order:
        fixture = FIX[pick["fixture_id"]]
        top5 = any(p["fixture_id"] == pick["fixture_id"] for p in TOP_PICKS)
        rows.append(
            "<tr>"
            f'<td><a href="sports/{esc(pick["sport"])}.html">{esc(SPORT_NAME[pick["sport"]])}</a></td>'
            f'<td>{esc(match_label(fixture))}</td>'
            f'<td><strong>{esc(pick["selection"])}</strong></td>'
            f'<td>{pick["p"]*100:.2f}%</td>'
            f'<td>{esc(pick["fair_decimal"])}</td>'
            f'<td>{esc(pick["fair_american"])}</td>'
            f'<td>{confidence_badge(pick["confidence"])}</td>'
            f'<td>{window_badge(pick["in_band"])}</td>'
            f'<td>{"yes" if top5 else "—"}</td>'
            "</tr>"
        )
    body = f"""
<p class="crumb">Dashboard / Picks</p>
<h1>Match-winner picks and confidence</h1>
<p class="lede">One winner is named for every priced fixture. Confidence follows the model probability: <strong>high</strong> at 70% or more,
<strong>medium</strong> from 60% to 69.99%, <strong>low</strong> below 60%. The five highest-probability selections are marked in the last column and
are the five that carry written predictions.</p>
<div class="tablewrap"><table class="data">
<thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th>Probability</th><th>Fair decimal</th><th>Fair American</th><th>Confidence</th><th>−250 window</th><th>Today's five</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<h2>Why the confidence and the price window disagree</h2>
<p>Four of the eight priced fixtures produce a winner above the 70% confidence bar, and one more sits just above it. All five of those prices are
shorter than −250, so they fall outside the brief's price window even though they pass its confidence bar. The reverse is also true: the only prices
long enough to sit in the window are alternate lines whose probability is close to 50%, and those are not confident picks. Publishing a quarter-game
handicap purely to manufacture a −250 price would be inventing a market, so it was not done. The full reasoning, with the arithmetic, is on
<a href="flagged.html#DL-05">DL-05</a>.</p>

<h2>The five highest-confidence selections</h2>
<div class="grid sports">
{''.join(f'''<a class="card" href="predictions.html#{esc(PRED_BY_FIX[p['fixture_id']]['id'])}">
<div class="cardhead"><span class="pill">{esc(FIX[p['fixture_id']]['competition'])}</span>{confidence_badge(p['confidence'])}</div>
<h3>{esc(p['selection'])}</h3>
<p>{esc(match_label(FIX[p['fixture_id']]))} · {p['p']*100:.2f}% · fair {esc(p['fair_decimal'])} ({esc(p['fair_american'])})</p>
<div class="metrics"><span>{window_badge(p['in_band'])}</span><span>written prediction →</span></div></a>''' for p in TOP_PICKS)}
</div>
"""
    return page("Picks", "picks.html", body)


# --------------------------------------------------------------------------- #
# predictions
# --------------------------------------------------------------------------- #
def predictions_page():
    cards = []
    for pred in predictions_doc:
        facts = "".join(
            f'<li>{esc(fact["fact"])} — {source_link(fact["source_url"])}</li>' for fact in pred["facts_used"]
        )
        cards.append(f"""<article class="panel" id="{esc(pred['id'])}">
<div class="cardhead"><span class="pill">{esc(pred['competition'])} · {esc(pred['round'])}</span>{confidence_badge(pred['confidence'])}</div>
<h2>{esc(pred['match'])}</h2>
<p class="sub">{esc(pred['date'])} · selection: <strong>{esc(pred['selection'])}</strong> · fair {esc(pred['fair_decimal'])} ({esc(pred['fair_american'])}) · model {pred['probability']*100:.2f}% · {pred['word_count']} words</p>
<p class="lede">{esc(pred['text'])}</p>
<h3>Facts used, each with its source</h3>
<ul>{facts}</ul>
<p class="predfoot">{source_link(pred['official_url'], 'Official draw on atptour.com')} ·
<a href="sports/{esc(pred['sport'])}.html">All {esc(pred['sport_name'])} rows</a> ·
<a href="lines.html">Every price for this fixture</a></p>
</article>""")
    body = f"""
<p class="crumb">Dashboard / Predictions</p>
<h1>Five written predictions</h1>
<p class="lede">Each paragraph is at least 30 words, names the player and the exact selection, states the tournament form read from the official ATP
draw this session, and states a recent completed scoreline. Nothing in a paragraph is asserted unless the fact list underneath it links to the
official page that printed it. Where a player entered on a bye and has no scoreline this week, the paragraph says so instead of inventing form.</p>
<div class="notice"><strong>Every selection below is high confidence and outside the brief's −250 price window.</strong> The confidence bar (70%) and
the price window (−250 to +10000, i.e. 70.00%–71.43%) intersect in a 1.43-point band that half-point lines step over; the arithmetic and the
alternatives that were rejected are in <a href="flagged.html#DL-05">DL-05</a>.</div>
{''.join(cards)}
"""
    return page("Predictions", "predictions.html", body)


# --------------------------------------------------------------------------- #
# flagged
# --------------------------------------------------------------------------- #
def flagged_page():
    items = []
    for flag in flags_doc:
        src = flag["source_url"]
        link = (f'<a href="{esc(src)}" rel="noopener">{esc(domain(src))}</a>' if src.startswith("http")
                else f'<a href="../{esc(src)}">methodology page</a>')
        items.append(f"""<article class="panel" id="{esc(flag['id'])}">
<div class="cardhead"><span class="pill warn">{esc(flag['id'])}</span><span class="pill">needs review</span></div>
<h2>{esc(flag['title'])}</h2>
<p><strong>What was seen.</strong> {esc(flag['what'])}</p>
<p><strong>How it is handled.</strong> {esc(flag['reason'])}</p>
<p class="predfoot">Source: {link}</p>
</article>""")
    body = f"""
<p class="crumb">Dashboard / Flagged for Review</p>
<h1>Flagged for Review</h1>
<p class="lede">Fifteen items where a value could not be confirmed from an official source, where two official sources disagree, or where the brief's
target was not met. None of them blocks publication: every affected cell is blank or labelled rather than filled in, and each item links to the page
that produced it. Flagged items are listed here so they can be checked by hand after the site is live.</p>
<div class="notice warn">The shortfall that matters most: <strong>five written picks exist for tennis and none for cricket</strong>, because cricket has
no official strength input in this session. See <a href="#DL-13">DL-13</a> and <a href="#DL-04">DL-04</a>.</div>
{''.join(items)}
"""
    return page("Flagged for Review", "flagged.html", body)


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #
def sources_page():
    rows = []
    for source in sources_doc:
        status = source["status"]
        pill = "ok" if status == "read" else "warn"
        rows.append(
            "<tr>"
            f'<td><strong>{esc(source["name"])}</strong><br><span class="small">{esc(source["url"])}</span></td>'
            f'<td>{esc(source["family"])}</td>'
            f'<td>{esc(source["verified"])}</td>'
            f'<td><span class="pill {pill}">{esc(status)}</span></td>'
            f'<td>{source_link(source["url"])}</td>'
            "</tr>"
        )
    body = f"""
<p class="crumb">Dashboard / Sources</p>
<h1>Source register</h1>
<p class="lede">Every page fetched for this layer, what it was used to verify, and whether it delivered. Capture timestamp for the whole register:
<strong>2026-10-22 21:30 UTC</strong>, by the agent fetch tool on server-rendered HTML. Failed and partial reads are listed with the same prominence as
successful ones, because the layer's blank prices are a direct consequence of them.</p>
<div class="tablewrap"><table class="data">
<thead><tr><th>Source</th><th>Family</th><th>What it verified</th><th>Status</th><th>Link</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<h2>Captures on disk</h2>
<p>Each source's rendered rows are stored verbatim next to the fetch in <code>data/daily-audit/capture/</code>:
<code>olbg_taxonomy_and_hubs_2026-10-22.md</code>, <code>atp_almaty_2026-10-22.md</code>, <code>atp_brussels_2026-10-22.md</code> and
<code>icc_2026-10-22.md</code>. The captures keep OLBG's own day labels and scores exactly as printed so a reviewer can re-check them without re-fetching.</p>
"""
    return page("Sources", "sources.html", body)


# --------------------------------------------------------------------------- #
# methodology
# --------------------------------------------------------------------------- #
def methodology_page():
    c = inputs_doc["constants"]
    body = f"""
<p class="crumb">Dashboard / Methodology</p>
<h1>Methodology</h1>
<p class="lede">This layer publishes a dated snapshot: officially verified fixtures, fair prices this layer originates itself, a confidence label per
selection, and written predictions for the five highest-confidence picks. It is not a live feed and it is not betting advice.</p>

<h2>1. Fixtures</h2>
<p>A fixture is published only when an official governing-body page prints the pairing. The official page is linked on the row and its rendered text is
stored verbatim under <code>data/daily-audit/capture/</code>. Discovery comes from OLBG, but OLBG is never used as the authority for a pairing, a date or a
price: OLBG publishes tip counts, not odds. Dates and times are printed as the official source printed them; nothing is converted between timezones.</p>

<h2>2. Inputs</h2>
<p>The only strength inputs are the official ATP seeding, the entry status (seeded, unseeded, qualifier) and the sets each player actually won and lost
in the tournament according to the official draw. A player who entered on a bye has a zero form input, and that gap is disclosed rather than filled.
Cricket has no input at all in this session because the ICC rankings table rendered empty, so cricket carries no price.</p>

<h2>3. The price model</h2>
<div class="panel"><ul>
<li><code>rating = {c['seed_rating_base']} + {c['seed_rating_step']} × ({c['seed_rating_anchor']} − seed)</code> for a seeded player</li>
<li><code>rating = {c['unseeded_rating']}</code> unseeded, <code>{c['qualifier_rating']}</code> for a qualifier</li>
<li><code>rating += {c['form_per_set']} × (sets won − sets lost)</code> from verified scorelines only</li>
<li><code>p(A wins) = 1 ÷ (1 + 10^(−(rating_A − rating_B) ÷ {c['rating_scale']}))</code></li>
<li>games margin ~ Normal(<code>{c['margin_games_per_probability_unit']} × (p − 0.5)</code>, <code>{c['margin_sd_games']}</code>) — drives every handicap line</li>
<li>total games ~ Normal(<code>{c['total_mean_games']}</code>, <code>{c['total_sd_games']}</code>) — drives every total line</li>
<li>fair decimal <code>= 1 ÷ p</code>, rounded from a probability rounded to four decimals first, so a reader can reproduce every printed price</li>
</ul></div>
<p>These constants are this layer's assumptions. No governing body publishes them. They are stated here in full so anyone can re-run
<code>python3 scripts/daily_audit_model.py</code> with different values and see how far the prices move.</p>

<h2>4. Confidence and the price window</h2>
<p><strong>high</strong> means model probability ≥ 0.7000; <strong>medium</strong> 0.6000–0.6999; <strong>low</strong> below 0.6000. The brief's price
condition — a fair American price between −250 and +10000 — is reported separately in a <em>−250 window</em> column: −250 equals a probability of
0.714286, so the condition holds only for probabilities between 0.7000 and 0.714286. That 1.43-point window is stepped over by half-point lines at the
margin and total deviations used here, so this layer publishes zero in-window picks and says so on every page rather than adjusting a line until one
appears (<a href="flagged.html#DL-05">DL-05</a>).</p>

<h2>5. Predictions</h2>
<p>A written prediction exists only for a published pick. Each is at least 30 words, names the selection, states the tournament form and a recent
completed scoreline, and lists each fact with the official URL it came from. No paragraph names a player, a score or an opponent that is not in the
fixture's fact list, and no paragraph implies a bookmaker price.</p>

<h2>6. Reproducing the layer</h2>
<div class="panel"><p><code>python3 scripts/daily_audit_model.py &amp;&amp; python3 scripts/daily_audit_build.py</code></p>
<p>The model reads <code>data/daily-audit/fixtures.json</code> and <code>data/daily-audit/inputs.json</code>, writes <code>data/daily-audit/lines.json</code>, and the
builder renders this site. The build is deterministic: no clock, no network, no randomness. <code>python3 -m unittest tests.test_daily_audit</code> checks the
rendered pages, not only the JSON.</p></div>

<h2>7. Limits stated up front</h2>
<ul>
<li>Two sports have rows here. Fifteen of the seventeen eligible sports do not, and each reason is listed on the landing page and on
<a href="flagged.html">Flagged for Review</a>.</li>
<li>The sample is one day of one sport's quarter-finals. Eight tennis fixtures cannot support any claim about the model's long-run accuracy.</li>
<li>Seeding is a proxy for strength, not a measurement of it. A bye inflates the uncertainty and the model does not add a variance term for rust.</li>
<li>Retirement, walkover and in-play states are not modelled. A walkover is recorded as a statement about the draw, never as a completed score.</li>
</ul>
"""
    return page("Methodology", "methodology.html", body)


# --------------------------------------------------------------------------- #
# sports
# --------------------------------------------------------------------------- #
def sport_index():
    cards = []
    for slug, name, olbg_id, status, note in SPORTS:
        here = len(rows_by_sport.get(slug, []))
        preds = sum(1 for p in predictions_doc if p["sport"] == slug)
        cards.append(f"""<a class="card" href="{esc(slug)}.html">
<div class="cardhead"><span class="pill">{esc(status)}</span></div>
<h3>{esc(name)}</h3>
<p>{esc(note)}</p>
<div class="metrics"><span><b>{here}</b> rows</span><span><b>{preds}</b> picks</span><span>OLBG id {olbg_id}</span></div></a>""")
    body = f"""
<p class="crumb"><a href="../index.html">Dashboard</a> / Sports</p>
<h1>All 17 eligible sports</h1>
<p class="lede">The brief's exclusion list removes soccer, boxing, UFC/MMA, American football, hurling, horse racing, cycling and "specials". That leaves
seventeen sports on OLBG's own taxonomy. Every one of them has a page here, including the ones with no row today: a page that says why a sport is empty
is more useful than a sport that silently disappears.</p>
<div class="grid sports">{''.join(cards)}</div>
"""
    return page("Sports", "sports/index.html", body, depth=1)


def sport_page(slug):
    name = SPORT_NAME[slug]
    meta = next(row for row in SPORTS if row[0] == slug)
    rows = rows_by_sport.get(slug, [])
    preds = [p for p in predictions_doc if p["sport"] == slug]
    olbg_url = f"https://www.olbg.com/betting-tips/{name.replace(' ', '_')}/{meta[2]}"
    parts = [f"""
<p class="crumb"><a href="../index.html">Dashboard</a> / <a href="index.html">Sports</a> / {esc(name)}</p>
<h1>{esc(name)}</h1>
<div class="kpis small">
<div class="kpi"><div class="v">{len(rows)}</div><div class="k">Fixtures here</div></div>
<div class="kpi"><div class="v">{len(preds)}</div><div class="k">Written picks</div></div>
<div class="kpi"><div class="v">{cur_rows_by_sport.get(slug, 0)}</div><div class="k">Rows in current desk</div></div>
<div class="kpi"><div class="v">{meta[2]}</div><div class="k">OLBG sport id</div></div>
</div>
<div class="notice{' warn' if not rows else ''}"><strong>Status: {esc(meta[3])}.</strong> {esc(meta[4])} OLBG hub:
{source_link(olbg_url)}</div>
"""]
    if rows:
        parts.append("<h2>Fixtures</h2>")
        parts.append(fixture_table(rows, depth=1))
        parts.append("<h2>Prices and picks</h2>")
        pick_rows = []
        for fixture in rows:
            win = WINNER.get(fixture["id"])
            if not win:
                pick_rows.append(f'<tr><td>{esc(match_label(fixture))}</td><td colspan="5"><span class="pill warn">no price: no official strength input</span></td></tr>')
                continue
            pick_rows.append(
                "<tr>"
                f'<td>{esc(match_label(fixture))}</td>'
                f'<td><strong>{esc(win["selection"])}</strong></td>'
                f'<td>{win["p"]*100:.2f}%</td>'
                f'<td>{esc(win["fair_decimal"])} ({esc(win["fair_american"])})</td>'
                f'<td>{confidence_badge(win["confidence"])}</td>'
                f'<td>{window_badge(win["in_band"])}</td>'
                "</tr>"
            )
        parts.append("""<div class="tablewrap"><table class="data">
<thead><tr><th>Match</th><th>Winner pick</th><th>Probability</th><th>Fair price</th><th>Confidence</th><th>−250 window</th></tr></thead>
<tbody>""" + "".join(pick_rows) + "</tbody></table></div>")
    if preds:
        parts.append("<h2>Written predictions</h2>")
        for pred in preds:
            parts.append(f'<article class="panel"><h3>{esc(pred["selection"])} — {esc(pred["match"])}</h3>'
                         f'<p>{esc(pred["text"])}</p>'
                         f'<p class="predfoot">{source_link(pred["official_url"])} · '
                         f'<a href="../predictions.html#{esc(pred["id"])}">Read with its fact list</a></p></article>')
    parts.append(f'<p><a class="button" href="index.html">All sports</a> <a class="button" href="../flagged.html">Flagged for Review</a></p>')
    return page(name, "sports/index.html", "".join(parts), depth=1)


# --------------------------------------------------------------------------- #
# write
# --------------------------------------------------------------------------- #
def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as handle:
        handle.write(content)


def main():
    write("index.html", landing())
    write("matches.html", matches_page())
    write("lines.html", lines_page())
    write("picks.html", picks_page())
    write("predictions.html", predictions_page())
    write("flagged.html", flagged_page())
    write("sources.html", sources_page())
    write("methodology.html", methodology_page())
    write("sports/index.html", sport_index())
    for slug, *_ in SPORTS:
        write(f"sports/{slug}.html", sport_page(slug))
    pages = 9 + len(SPORTS)
    print(json.dumps({"pages": pages, "fixtures": COUNT["fixtures"], "prices": COUNT["prices"],
                      "predictions": len(predictions_doc), "flags": len(flags_doc),
                      "sports": len(SPORTS)}, indent=1))


if __name__ == "__main__":
    main()
