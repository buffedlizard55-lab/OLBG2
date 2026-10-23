#!/usr/bin/env python3
"""Signal desk (session 6b10ecda) - render the static pages under /signal/.

Input : data/signal/{matches,predictions,flagged,sources}.json
Output: signal/index.html, signal/sports/<slug>.html and the support pages.

Every table row that carries a value also carries the official source link the
value came from. Rows without an official input are rendered with an empty
selection cell and a flag reference instead of a guessed number.
"""
from __future__ import annotations

import html
import json
import os
import re
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "signal")
SITE = os.path.join(ROOT, "signal")
GENERATED = "23 October 2026"
SESSION = "arena/6b10ecda-olbg2"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
          "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
          "Handball", "Ice Hockey", "Basketball", "Rugby League"]


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def esc(x):
    return html.escape(str(x), quote=True)


def link(url, text=None, cls=""):
    if not url:
        return '<span class="blank">not published</span>'
    c = ' class="%s"' % cls if cls else ""
    return '<a%s href="%s" rel="noopener" target="_blank">%s</a>' % (
        c, esc(url), esc(text or "official source"))


def load(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


CSS = """
:root{--bg:#0f1720;--panel:#16202b;--line:#24323f;--ink:#e9eef3;--dim:#9fb0c0;
--hi:#48d597;--mid:#f2c14e;--low:#7f93a6;--warn:#ff7a6b;--link:#6cc0ff;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
header.top{background:linear-gradient(180deg,#132030,#0f1720);border-bottom:1px solid var(--line);
padding:22px 20px 16px}
header.top h1{margin:0 0 4px;font-size:21px;letter-spacing:.2px}
header.top p{margin:0;color:var(--dim);font-size:13px}
nav{display:flex;flex-wrap:wrap;gap:6px;padding:10px 16px;background:#111b25;
border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
nav a{padding:5px 10px;border:1px solid var(--line);border-radius:999px;font-size:12.5px;color:var(--ink)}
nav a:hover{background:#1d2a37;text-decoration:none}
nav a.here{background:#1f3b31;border-color:#2f6b55;color:#bff3dd}
main{max-width:1180px;margin:0 auto;padding:22px 16px 60px}
h2{font-size:17px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:22px 0 8px;color:#cfe0ee}
p.note{color:var(--dim);font-size:13px;margin:6px 0 14px}
table{width:100%;border-collapse:collapse;margin:10px 0 18px;font-size:13.2px;background:var(--panel);
border:1px solid var(--line);border-radius:8px;overflow:hidden}
th{background:#1b2735;text-align:left;padding:8px 10px;font-weight:600;color:#cfe0ee;
border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid #1d2935;vertical-align:top}
tr:last-child td{border-bottom:none}
tr:nth-child(even) td{background:#17222e}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:12px;margin:14px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 13px}
.card h4{margin:0 0 6px;font-size:14px}
.card .big{font-size:22px;font-weight:600}
.card .sub{color:var(--dim);font-size:12.3px}
.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:8px 0 4px}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11.5px;border:1px solid var(--line)}
.high{background:#13342a;color:#8ff0c6;border-color:#2b6a52}
.medium{background:#352c13;color:#f4d68c;border-color:#6d5a26}
.low{background:#222c35;color:#b6c6d4}
.band{background:#132b3a;color:#9fd8ff;border-color:#2a5d7d}
.nob{background:#331d1b;color:#ffb3a8;border-color:#7a3a33}
.blank{color:#6f8294;font-style:italic}
.sev-high{color:#ff9b8e;font-weight:600}
.sev-medium{color:#f2c14e}
.sev-low{color:var(--dim)}
.pred{background:var(--panel);border:1px solid var(--line);border-left:3px solid #2f6b55;
border-radius:8px;padding:12px 14px;margin:10px 0}
.pred .meta{color:var(--dim);font-size:12.3px;margin-bottom:6px}
footer{border-top:1px solid var(--line);color:var(--dim);font-size:12.3px;padding:18px 16px 40px;
max-width:1180px;margin:0 auto}
code{background:#101a24;padding:1px 5px;border-radius:4px;font-size:12.4px}
"""

PAGES = [("index.html", "Dashboard"), ("picks.html", "Picks"),
         ("predictions.html", "Write-ups"), ("matches.html", "All matches"),
         ("flagged.html", "Flagged for review"), ("sources.html", "Sources"),
         ("verification.html", "Verification"), ("methodology.html", "Method")]


def nav(current, depth=0):
    up = "../" * depth
    out = ['<nav>']
    for href, label in PAGES:
        cls = ' class="here"' if href == current and depth == 0 else ""
        out.append('<a%s href="%s%s">%s</a>' % (cls, up, href, label))
    out.append('<a href="%s../index.html">OLBG2 home</a>' % up)
    out.append('</nav>')
    return "".join(out)


def page(path, title, body, depth=0, current=""):
    up = "../" * depth
    doc = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s | Signal desk</title>
<link rel="stylesheet" href="%sassets/signal.css">
</head><body>
<header class="top"><h1>Signal desk &mdash; %s</h1>
<p>Own prices for 15 sports, built only from official sources. Generated %s &middot; session <code>%s</code></p></header>
%s
<main>%s</main>
<footer>Every value on this desk comes from the official source linked in its row. Where an official
source published nothing, the cell is left blank and the row is listed on the
<a href="%sflagged.html">Flagged for review</a> page. Prices are our own fair prices with no
overround and are published for analysis, not as advice. 18+.</footer>
</body></html>""" % (esc(title), up, esc(title), GENERATED, SESSION,
                     nav(current, depth), body, up)
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(doc)


def conf_tag(c, in_band):
    t = '<span class="tag %s">%s</span>' % (c, c)
    t += ' <span class="tag %s">%s</span>' % ("band" if in_band else "nob",
                                              "in band" if in_band else "outside band")
    return t


def build():
    matches = load("matches.json")["matches"]
    preds = load("predictions.json")["predictions"]
    flags = load("flagged.json")["flags"]
    sources = load("sources.json")["sources"]

    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    with open(os.path.join(SITE, "assets", "signal.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)

    by_sport = defaultdict(list)
    for m in matches:
        by_sport[m["sport"]].append(m)
    preds_by_sport = defaultdict(list)
    for p in preds:
        preds_by_sport[p["sport"]].append(p)
    prose = {p["id"]: p for p in preds}

    # ---------------------------------------------------------- dashboard
    tier_a = [p for p in preds if p["prob"] >= 0.70 and p["in_band"]]
    tier_b = sorted([p for p in preds if p["prob"] >= 0.70 and not p["in_band"]],
                    key=lambda p: -p["prob"])
    tier_c = sorted([p for p in preds if p["in_band"] and p["prob"] < 0.70],
                    key=lambda p: -p["prob"])[:10]

    def pick_table(rows, empty_msg):
        if not rows:
            return '<p class="note">%s</p>' % esc(empty_msg)
        out = ['<table><tr><th>Sport</th><th>Match</th><th>Selection</th>'
               '<th>Market</th><th>Our price</th><th>Win %</th><th>Confidence</th>'
               '<th>Start (UTC)</th><th>Source</th></tr>']
        for p in rows:
            out.append("<tr><td>%s</td><td>%s</td><td><b>%s</b></td><td>%s</td>"
                       "<td>%s / %.2f</td><td>%.1f%%</td><td>%s</td><td>%s</td>"
                       "<td>%s</td></tr>" % (
                           esc(p["sport"]), esc(p["event"]), esc(p["selection"]),
                           esc(p["market"]), esc(p["american"]), p["decimal"],
                           100 * p["prob"], conf_tag(p["confidence"], p["in_band"]),
                           esc(p["start_utc"]), link(p["source_url"], "official")))
        out.append("</table>")
        return "".join(out)

    covered = sum(1 for s in SPORTS if by_sport.get(s))
    priced_sports = sum(1 for s in SPORTS if preds_by_sport.get(s))
    body = []
    body.append('<h2>Executive summary &mdash; %s</h2>' % GENERATED)
    body.append('<div class="kpis">')
    for label, value, sub in [
            ("Sports in scope", len(SPORTS), "the fifteen requested"),
            ("Sports with fixtures", covered, "official fixture list found"),
            ("Sports with prices", priced_sports, "official numeric inputs found"),
            ("Matches published", len(matches), "every row carries a source"),
            ("Priced selections", len(preds), "our own lines, no overround"),
            ("Written previews", sum(1 for p in preds if p["write_up"]), "30+ words each"),
            ("Items flagged", len(flags), "see Flagged for review")]:
        body.append('<div class="card"><div class="big">%s</div>'
                    '<div class="sub">%s<br>%s</div></div>' % (value, esc(label), esc(sub)))
    body.append('</div>')

    body.append('<h3>Tier A &mdash; high confidence <em>and</em> inside the -250 to +10000 band</h3>')
    body.append('<p class="note">The brief sets two rules at once: a high-confidence pick implies '
                'a win probability above 70%, and the focus band runs from -250 to +10000. Read as '
                'an intersection that leaves a narrow window of 70.0% to 71.4%. Today that window is '
                'reported exactly as it falls - nothing is nudged into it.</p>')
    body.append(pick_table(tier_a, "No selection landed inside the 70.0%-71.4% window today. "
                                   "The two tables below show both halves of the brief instead: "
                                   "everything above 70% that is priced shorter than -250, and the "
                                   "strongest selections that do sit inside the price band."))
    body.append('<h3>Tier B &mdash; high confidence, priced shorter than -250</h3>')
    body.append(pick_table(tier_b, "none"))
    body.append('<h3>Tier C &mdash; strongest selections inside the price band</h3>')
    body.append(pick_table(tier_c, "none"))

    body.append('<h2>Sports</h2><div class="cards">')
    for s in SPORTS:
        ms = by_sport.get(s, [])
        ps = preds_by_sport.get(s, [])
        best = max(ps, key=lambda p: p["prob"]) if ps else None
        body.append('<div class="card"><h4><a href="sports/%s.html">%s</a></h4>'
                    '<div class="sub">%d fixture%s published &middot; %d priced</div>'
                    '<div class="sub">%s</div></div>' % (
                        slug(s), esc(s), len(ms), "" if len(ms) == 1 else "s", len(ps),
                        ("Best: <b>%s</b> %s" % (esc(best["selection"]), esc(best["american"])))
                        if best else '<span class="blank">no priced selection today</span>'))
    body.append('</div>')

    body.append('<h2>How to read this desk</h2>')
    body.append('<p class="note">Prices are originated from official numbers only: league feeds, '
                'governing-body results and official rankings. Bookmaker prices are never an input. '
                'Where an official source published no usable number, the selection cell is blank and '
                'the row appears on the flagged page with the reason. Full method on the '
                '<a href="methodology.html">Method</a> page; every input is listed on '
                '<a href="verification.html">Verification</a>.</p>')
    page("index.html", "Dashboard", "".join(body), 0, "index.html")

    # --------------------------------------------------------------- picks
    body = ['<h2>Every priced selection, strongest first</h2>',
            '<p class="note">%d selections across %d sports. "In band" means our fair American '
            'price sits between -250 and +10000.</p>' % (len(preds), priced_sports)]
    body.append(pick_table(sorted(preds, key=lambda p: -p["prob"]), "none"))
    page("picks.html", "Picks", "".join(body), 0, "picks.html")

    # ---------------------------------------------------------- predictions
    body = ['<h2>Written previews</h2>',
            '<p class="note">One write-up per selection we are prepared to argue for, each at least '
            'thirty words, each naming the team or player, the form, the recent head-to-head or '
            'result history and the match-specific numbers behind the call.</p>']
    for s in SPORTS:
        rows = [p for p in preds_by_sport.get(s, []) if p["write_up"]]
        if not rows:
            continue
        rows.sort(key=lambda p: -p["prob"])
        body.append('<h3>%s</h3>' % esc(s))
        for p in rows:
            body.append('<div class="pred"><div class="meta">%s &middot; %s &middot; '
                        'selection <b>%s</b> at %s (%.1f%%) %s &middot; %s</div>%s</div>' % (
                            esc(p["event"]), esc(p["start_utc"]), esc(p["selection"]),
                            esc(p["american"]), 100 * p["prob"],
                            conf_tag(p["confidence"], p["in_band"]),
                            link(p["source_url"], "official source"),
                            esc(p["write_up"])))
    page("predictions.html", "Write-ups", "".join(body), 0, "predictions.html")

    # ------------------------------------------------------------- matches
    body = ['<h2>All published fixtures</h2>',
            '<p class="note">Every fixture captured from an official source today, including the '
            'ones we deliberately did not price.</p>',
            '<table><tr><th>Sport</th><th>Competition</th><th>Match</th><th>Start</th>'
            '<th>Our selection</th><th>Price</th><th>Status</th><th>Source</th></tr>']
    for s in SPORTS:
        for m in by_sport.get(s, []):
            if m["pick"]:
                sel = "<b>%s</b>" % esc(m["pick"]["selection"])
                pr = esc(m["pick"]["american"])
            else:
                sel = '<span class="blank">blank &mdash; flagged</span>'
                pr = '<span class="blank">&mdash;</span>'
            body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                        "<td>%s</td><td>%s</td><td>%s</td></tr>" % (
                            esc(m["sport"]), esc(m["competition"]), esc(m["event"]),
                            esc(m["start_utc"]), sel, pr, esc(m["status"]),
                            link(m["source_url"], "official")))
    body.append("</table>")
    page("matches.html", "All matches", "".join(body), 0, "matches.html")

    # -------------------------------------------------------------- flagged
    body = ['<h2>Flagged for review</h2>',
            '<p class="note">Nothing here was guessed around. Each entry is a value we could not '
            'confirm, a source that would not serve data, or a price whose inputs are thin enough '
            'that the reader should know.</p>',
            '<table><tr><th>Id</th><th>Sport</th><th>Subject</th><th>Severity</th>'
            '<th>Detail</th><th>Source</th></tr>']
    for f in sorted(flags, key=lambda f: (f["sport"], f["id"])):
        body.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td>'
                    '<td class="sev-%s">%s</td><td>%s</td><td>%s</td></tr>' % (
                        esc(f["id"]), esc(f["sport"]), esc(f["subject"]),
                        esc(f["severity"]), esc(f["severity"]), esc(f["detail"]),
                        link(f["source_url"], "source")))
    body.append("</table>")
    blanks = [m for m in matches if not m["pick"] and m["status"] != "result"]
    body.append('<h3>Fixtures published with a blank selection (%d)</h3>' % len(blanks))
    body.append('<table><tr><th>Sport</th><th>Match</th><th>Why no price</th><th>Source</th></tr>')
    for m in blanks:
        body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(m["sport"]), esc(m["event"]),
            esc(" ".join(m["flags"])) or '<span class="blank">no reason recorded</span>',
            link(m["source_url"], "official")))
    body.append("</table>")
    page("flagged.html", "Flagged for review", "".join(body), 0, "flagged.html")

    # -------------------------------------------------------------- sources
    body = ['<h2>Official sources used today</h2>',
            '<p class="note">Each row is a page or feed read first-hand during this session. '
            'Nothing on this desk comes from a secondary aggregator except the darts fixture list, '
            'which is labelled as an operator source because the governing body would not serve one.</p>',
            '<table><tr><th>Sport</th><th>Source</th><th>Used for</th><th>Link</th></tr>']
    for s in sources:
        body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(s["sport"]), esc(s["name"]), esc(s["used_for"]),
            link(s["url"], s["url"][:68])))
    body.append("</table>")
    page("sources.html", "Sources", "".join(body), 0, "sources.html")

    # --------------------------------------------------------- verification
    body = ['<h2>Line-by-line verification</h2>',
            '<p class="note">One row per published fixture: the official inputs behind its price, '
            'the source to check them against, and whether the row is confirmed or carries a flag. '
            'Rows marked "no input" are published as fixtures only.</p>',
            '<table><tr><th>Id</th><th>Sport</th><th>Match</th><th>Inputs used</th>'
            '<th>State</th><th>Check against</th></tr>']
    for s in SPORTS:
        for m in by_sport.get(s, []):
            if m["inputs"]:
                state = "confirmed against source" if not m["flags"] else "confirmed, with flags"
            elif m["status"] == "result":
                state = "official result, not priced"
            else:
                state = "no input published &mdash; left blank"
            body.append("<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td>"
                        "<td>%s</td><td>%s</td></tr>" % (
                            esc(m["id"]), esc(m["sport"]), esc(m["event"]),
                            esc(m["inputs"]) or '<span class="blank">none published</span>',
                            state, link(m["source_url"], "official")))
    body.append("</table>")
    page("verification.html", "Verification", "".join(body), 0, "verification.html")

    # ---------------------------------------------------------- methodology
    method = """
<h2>How these prices are made</h2>
<p class="note">Three rules sit above everything else on this desk. Official sources only. No value is
ever filled in by assumption - if the governing body did not publish it, the cell stays blank and the
row gets flagged. And no bookmaker price is ever an input, so every number here is ours.</p>
<h3>The -250 to +10000 band</h3>
<p class="note">The brief gives two instructions that overlap: treat a high-confidence selection as one
implying better than a 70% chance, and focus on prices between -250 and +10000. A fair price of -250 is
exactly 71.43%, so the intersection is the narrow window 70.0% to 71.43%. Rather than quietly widen it,
the dashboard publishes three tiers: Tier A for selections inside the window, Tier B for selections
above 70% that price shorter than -250, and Tier C for the strongest selections that satisfy the price
band. Every table carries an "in band" marker so the distinction is never hidden.</p>
<h3>Per-sport method</h3>
<table><tr><th>Sport</th><th>Official input</th><th>How it becomes a price</th></tr>
<tr><td>Ice Hockey</td><td>NHL team summary: goals for, goals against, games played</td>
<td>Scoring rates shrunk towards the league mean, 5% home scoring edge, independent Poisson scorelines;
a regulation tie is split 50/50 for the money line and resolved as a one-goal win for the puck line.</td></tr>
<tr><td>Baseball</td><td>Official 2026 runs scored and allowed, final standings</td>
<td>Pythagorean win rates at exponent 1.83, combined with log5 and an 8% home-odds edge; run totals from
a Poisson approximation of each club's run environment.</td></tr>
<tr><td>Basketball</td><td>EuroLeague standings after round 7: points for, against, games</td>
<td>Per-game offence and defence averaged across the pairing, three points of home edge, normal margin
with sigma 11.5 and totals with sigma 15.</td></tr>
<tr><td>Rugby League</td><td>Official World Cup results, rounds 1 and 2</td>
<td>Points differential per match, capped at 30 and shrunk by games/(games+2) because each nation has
played once or twice; four points of home edge for a true home venue, none in Perth; sigma 16.</td></tr>
<tr><td>Rugby Union</td><td>PREM fixtures page: last-three form strings</td>
<td>3.5 points per win of form difference plus a flat five-point home edge, sigma 13. Deliberately
cautious because the league table would not render.</td></tr>
<tr><td>Handball</td><td>Official first-leg score of the only tie with a result</td>
<td>First-leg margin, plus three goals for losing the away disadvantage and three for the home edge in
leg two, sigma 7.</td></tr>
<tr><td>Snooker</td><td>Official world ranking prize money</td>
<td>Logistic comparison of the natural logarithms of ranking money, k = 1.1. Players outside the
captured top 36 are bounded at the 36th-placed figure, so the favourite's number is a floor.</td></tr>
<tr><td>Cricket</td><td>Official result of the first match of the series</td>
<td>Unused overs converted at 5.3 runs each into a dominance figure, scaled at 0.0025 per run and
capped at 0.80.</td></tr>
<tr><td>Golf</td><td>Official 36-hole leaderboard</td>
<td>Win weight = exp(-0.55 x strokes behind the lead) across the captured top 25, normalised. Published
as conditional on the winner coming from that group.</td></tr>
<tr><td>Motor Racing</td><td>Official drivers' standings after round 17</td>
<td>Win weight = points^1.6 across the eight drivers published in the captured chunk, normalised and
labelled conditional.</td></tr>
<tr><td>Tennis, Darts, Greyhounds, Gaelic Sports, Volleyball</td><td>see the flagged page</td>
<td>No official numeric input was obtainable today, so fixtures are published with blank selections
rather than invented prices.</td></tr></table>
<h3>Caps and guard rails</h3>
<p class="note">Published probabilities are clamped to the range 5% to 95%: a single fixture always keeps
variance that a season-long rate cannot see. Markets are published as fair prices with no overround, so
the two sides of every two-way market add to 100%. Confidence is high at 70% or better, medium from 60%,
low below that.</p>
<h3>What we do not do</h3>
<p class="note">We do not use community tip percentages, pundit opinion or bookmaker prices as inputs; we
do not reconstruct a value that was truncated in a captured page; and we do not assert an injury or a
team-sheet change that was not published by an official source. Where no availability information
exists, the write-up says so.</p>
"""
    page("methodology.html", "Method", method, 0, "methodology.html")

    # ---------------------------------------------------------- sport pages
    for s in SPORTS:
        ms = by_sport.get(s, [])
        ps = sorted(preds_by_sport.get(s, []), key=lambda p: -p["prob"])
        srcs = [x for x in sources if x["sport"] == s or x["sport"] == "All sports"]
        fl = [f for f in flags if s.lower() in f["sport"].lower()]
        b = ['<h2>%s</h2>' % esc(s)]
        if not ms:
            b.append('<p class="note">No fixture could be read from an official source for this '
                     'sport today. The reason is recorded on the flagged table below rather than '
                     'filled in with a guess.</p>')
        b.append('<h3>Top selections</h3>')
        if ps:
            b.append('<table><tr><th>#</th><th>Match</th><th>Selection</th><th>Market</th>'
                     '<th>Our price</th><th>Win %</th><th>Confidence</th><th>Start (UTC)</th>'
                     '<th>Source</th></tr>')
            for i, p in enumerate(ps[:5], 1):
                b.append("<tr><td>%d</td><td>%s</td><td><b>%s</b></td><td>%s</td><td>%s / %.2f</td>"
                         "<td>%.1f%%</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                             i, esc(p["event"]), esc(p["selection"]), esc(p["market"]),
                             esc(p["american"]), p["decimal"], 100 * p["prob"],
                             conf_tag(p["confidence"], p["in_band"]), esc(p["start_utc"]),
                             link(p["source_url"], "official")))
            b.append("</table>")
            if len(ps) < 5:
                b.append('<p class="note">Only %d selection%s could be priced from official inputs '
                         'today, short of the five-a-day target. The missing rows are fixtures '
                         'whose governing body published no usable number - they are listed below '
                         'with blank selections.</p>' % (len(ps), "" if len(ps) == 1 else "s"))
        else:
            b.append('<p class="note">No selection is published for this sport today. Every fixture '
                     'we could read is listed below with a blank selection and a flag explaining '
                     'why.</p>')
        writeups = [p for p in ps if p["write_up"]]
        if writeups:
            b.append('<h3>Previews</h3>')
            for p in writeups:
                b.append('<div class="pred"><div class="meta">%s &middot; %s &middot; '
                         '<b>%s</b> at %s (%.1f%%) %s &middot; %s</div>%s</div>' % (
                             esc(p["event"]), esc(p["start_utc"]), esc(p["selection"]),
                             esc(p["american"]), 100 * p["prob"],
                             conf_tag(p["confidence"], p["in_band"]),
                             link(p["source_url"], "official source"), esc(p["write_up"])))
        b.append('<h3>Fixtures and our full market set</h3>')
        b.append('<table><tr><th>Match</th><th>Start</th><th>Venue</th><th>Market</th>'
                 '<th>Our prices</th><th>Inputs</th><th>Source</th></tr>')
        for m in ms:
            if m["markets"]:
                groups = OrderedDict()
                for mk in m["markets"]:
                    groups.setdefault(mk["market"], []).append(mk)
                mk_html = "<br>".join(esc(k) for k in groups)
                pr_html = "<br>".join(
                    " &middot; ".join("%s <b>%s</b>" % (esc(x["selection"]), esc(x["american"]))
                                      for x in v) for v in groups.values())
            else:
                mk_html = '<span class="blank">no market priced</span>'
                pr_html = '<span class="blank">&mdash;</span>'
            notes = esc(m["inputs"]) if m["inputs"] else (
                '<span class="blank">%s</span>' % esc(" ".join(m["flags"]) or "no official input"))
            b.append("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                     "<td>%s</td><td>%s</td></tr>" % (
                         esc(m["event"]), esc(m["start_utc"]), esc(m["venue"]) or "&mdash;",
                         mk_html, pr_html, notes, link(m["source_url"], "official")))
        b.append("</table>")
        b.append('<h3>Sources for this sport</h3><table><tr><th>Source</th><th>Used for</th>'
                 '<th>Link</th></tr>')
        for x in srcs:
            b.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(x["name"]), esc(x["used_for"]), link(x["url"], x["url"][:70])))
        b.append("</table>")
        if fl:
            b.append('<h3>Flagged on this page</h3><table><tr><th>Id</th><th>Subject</th>'
                     '<th>Detail</th><th>Source</th></tr>')
            for f in fl:
                b.append("<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    esc(f["id"]), esc(f["subject"]), esc(f["detail"]),
                    link(f["source_url"], "source")))
            b.append("</table>")
        page(os.path.join("sports", slug(s) + ".html"), s, "".join(b), 1)

    print("built %d sport pages and %d support pages under signal/" %
          (len(SPORTS), len(PAGES)))


if __name__ == "__main__":
    build()
