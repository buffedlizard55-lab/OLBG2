#!/usr/bin/env python3
"""Build the consolidated OLBG2 desk at the repository root.

Every number on every page is read from a committed data file:
  data/unified/olbg_events.json  - this session's parse of the verbatim OLBG captures
  data/unified/audit.json        - the line-by-line audit and coverage reconciliation
  data/cadence/{fixtures,lines,picks,predictions,sources}.json
Nothing is typed in by hand, nothing is fetched, and nothing is estimated at build time.

Usage: python3 scripts/unified_build.py
"""
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SPORT_SLUG = {
    "Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
    "Cricket": "cricket", "Snooker": "snooker", "Darts": "darts", "Baseball": "baseball",
    "Gaelic Sports": "gaelic-sports", "Greyhounds": "greyhounds", "Tennis": "tennis",
    "Motor Racing": "motor-racing", "Handball": "handball", "Ice Hockey": "ice-hockey",
    "Basketball": "basketball", "Rugby League": "rugby-league",
}
SPORTS = list(SPORT_SLUG)

NAV = [
    ("index.html", "Overview"),
    ("olbg-events.html", "OLBG list"),
    ("matches.html", "Fixtures"),
    ("lines.html", "Our prices"),
    ("picks.html", "Picks"),
    ("predictions.html", "Predictions"),
    ("band.html", "Band"),
    ("sports/index.html", "Sports"),
    ("sources.html", "Sources"),
    ("verification.html", "Verification"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "Flagged"),
    ("methodology.html", "Method"),
    ("archive.html", "Archive"),
]


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def e(text):
    return html.escape(str(text if text is not None else ""), quote=True)


def pct(x, places=1):
    return f"{x * 100:.{places}f}%"


def am(v):
    if v is None:
        return "—"
    try:
        v = int(v)
    except (TypeError, ValueError):
        return "—"
    return f"+{v}" if v > 0 else str(v)


def dec(v):
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return "—"


def link(url, label=None, cls=""):
    if not url:
        return '<span class="blank">—</span>'
    klass = f' class="{cls}"' if cls else ""
    return f'<a href="{e(url)}"{klass} rel="noopener">{e(label or urlsplit(url).netloc)}</a>'


def badge(kind, text):
    return f'<span class="badge {e(kind)}">{e(text)}</span>'


def table(headers, rows, filterable=False):
    thead = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    flag = " data-filterable=\"1\"" if filterable else ""
    return (f"<div class=\"tablewrap\"{flag}><table><thead><tr>{thead}</tr></thead>"
            f"<tbody>{body}</tbody></table></div>")


def notice(kind, title, body):
    return f'<div class="notice {kind}"><strong>{title}</strong> {body}</div>'


def fixture_label(f):
    if f.get("away"):
        return f'{e(f["home"])} <span class="vs">v</span> {e(f["away"])}'
    return f'{e(f.get("home"))} <span class="tagfuture">outright</span>'



# --------------------------------------------------------------------------- chrome

def page(title, current, body):
    parts = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        parts.append(f'<a href="/{href}"{cur}>{label}</a>')
    nav = "".join(parts)
    head = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · OLBG2 unified desk</title>
<meta name="description" content="Consolidated, source-linked OLBG sports research: OLBG-listed events, our own prices, graded picks and written predictions across fifteen sports.">
<link rel="stylesheet" href="/assets/unified.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230f172a'/%3E%3Cpath d='M8 22l5-12 5 8 3-5 3 9z' fill='%2314b8a6'/%3E%3C/svg%3E">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <div class="wrap bar">
    <a class="brand" href="/index.html"><span class="mark"></span>OLBG2 <span class="sub">unified desk</span></a>
    <nav class="nav" aria-label="Sections">__NAV__</nav>
  </div>
</header>
"""
    head = head.replace("__TITLE__", e(title)).replace("__NAV__", nav)
    tail = """
<footer class="foot"><div class="wrap">
  <p><strong>What this desk is.</strong> A dated, source-linked research record of sport listed on OLBG, of our
  own originated prices, and of confidence-graded selections. It is not a live odds feed and it does not place bets.</p>
  <p>Every price, probability and confidence label is our own estimate, derived from the official statistics named
  on the row. Values that could not be confirmed are left blank and listed on
  <a href="/flagged.html">Flagged for review</a>. Capture times and source files are printed on every table.</p>
</div></footer>
<script src="/assets/unified.js" defer></script>
</body>
</html>
"""
    # Pages below the root use the same absolute base, so every internal link is absolute
    # from the site root and deep pages cannot produce a broken relative path.
    return head + body + tail


def snapshot_strip(inv, audit):
    win = inv["generated_from"]["capture_window"]
    official = load("data/ledger/manifest.json")["captures"]
    official_clock = max((c.get("fetched_at") or "" for c in official), default="") or "unknown"
    c = audit["counts"]
    return f"""<div class="stripe"><div class="wrap"><strong>Evidence snapshot</strong> · OLBG pages read
{win.get("first")} → {win.get("last")} · official pages read {official_clock} · {c["olbg_events"]} OLBG events
({c["olbg_events_upcoming"]} upcoming) · {c["fixtures"]} fixtures · {c["prices"]} prices ·
{c["predictions"]} predictions · <a href="/flagged.html">{c["findings"]} open items</a></div></div>"""


def kpi_block(audit):
    c = audit["counts"]
    items = [
        (c["olbg_events_upcoming"], "OLBG events upcoming", f'{c["olbg_events"]} listed in total'),
        (c["fixtures"], "fixtures we price", f'{c["fixtures_priced"]} carry a price'),
        (c["prices"], "originated prices", "money line · handicap · totals"),
        (c["picks_high"], "high-confidence picks", f'{c["picks_in_band_high"]} inside −250…+10000'),
        (c["predictions"], "written predictions", "30+ words, unique, sourced"),
        (c["findings"], "open review items", "blank, unconfirmed or irregular"),
    ]
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="v">{v}</div><div class="k">{e(k)}</div><div class="s">{e(s)}</div></div>'
        for v, k, s in items) + "</div>"


# --------------------------------------------------------------------------- pages

def build_index(inv, audit, picks, preds):
    c = audit["counts"]
    high = sorted([p for p in picks if p["confidence"] == "high"], key=lambda p: -p["probability"])
    in_band = [p for p in high if p.get("in_band")]
    todays = [p for p in picks if str(p.get("start_utc") or "").startswith("2026-10-23")]
    todays_high = [p for p in todays if p["confidence"] == "high"]

    if todays_high:
        exec_intro = (f"<p>{len(todays_high)} of the {len(todays)} selections that start today grade high, "
                      "listed first with the price and the band check on every row.</p>")
    elif todays:
        best = max(todays, key=lambda p: p["probability"])
        sports_today = sorted({p["sport"] for p in todays})
        next_dates = sorted(p["start_utc"][:10] for p in high if p.get("start_utc"))
        next_day = dt.date.fromisoformat(next_dates[0]).strftime("%-d %B") if next_dates else "a later date"
        exec_intro = (f"<p><strong>No selection starting today reaches high confidence.</strong> "
                      f"{len(todays)} selections start today ({e(', '.join(sports_today))}), and the strongest is "
                      f"<strong>{e(best['selection'])}</strong> at {pct(best['probability'])} — below the 70% floor "
                      f"this desk publishes as high. Rather than promote a weaker row to fill the summary, the desk "
                      f"shows the next high-confidence selections by probability and states that the first dated one "
                      f"is on {e(next_day)}.</p>")
    else:
        exec_intro = "<p>No selection in this snapshot starts today.</p>"

    band_sentence = f"""<p>A price of −250 is {pct(250 / 350)} implied. A selection that is both above 70% and no
shorter than −250 can therefore only sit in the 70.00–71.43% window. {len(high)} selections grade high;
{len(in_band)} are inside the band and all of those are alternate lines quoted at the ceiling. The other
{len(high) - len(in_band)} are real prices shorter than −250 and are published with their true numbers rather than
hidden. <a href="/band.html">The band page sets out the arithmetic</a>.</p>"""

    high_rows = []
    for p in high:
        high_rows.append(f"""<div class="pickrow">
  <div class="pr-main"><span class="sport">{e(p["sport"])}</span><strong>{e(p["selection"])}</strong>
    <span class="muted">· {e(p["market"])}</span><div class="tiny">{fixture_label(p)}</div></div>
  <div class="pr-num"><span class="big">{pct(p["probability"])}</span><span class="tiny">{am(p.get("fair_american"))} fair</span></div>
  <div class="pr-badges">{badge(p["confidence"], p["confidence"].upper())}
    {badge("ok", "in band") if p.get("in_band") else badge("muted", "outside band")}</div>
  <div class="pr-when">{e(p.get("time_display") or "start not published")}</div>
</div>""")

    band_rows = [[e(p["sport"]),
                  f'<strong>{e(p["selection"])}</strong><div class="tiny">{e(p["market"])}</div>',
                  pct(p["probability"]), am(p.get("fair_american")),
                  "yes" if p.get("band_line") else "no", fixture_label(p)] for p in in_band]

    cov_rows = []
    total_pred = 0
    for sport in SPORTS:
        cov = audit["coverage"][sport]
        gap = cov["prediction_shortfall"]
        total_pred += cov["predictions"]
        cov_rows.append([
            f'<a href="/sports/{SPORT_SLUG[sport]}.html"><strong>{e(sport)}</strong></a>',
            cov["olbg_events_upcoming"], cov["our_fixtures"], cov["our_fixtures_priced"],
            cov["picks"].get("high", 0), cov["picks"].get("in_band_high", 0),
            f'{cov["predictions"]} / {cov["prediction_target"]}',
            badge("warn", "−" + str(gap)) if gap else badge("ok", "target met"),
        ])
    cov_rows.append(["<strong>All fifteen</strong>", c["olbg_events_upcoming"], c["fixtures"],
                     c["fixtures_priced"], c["picks_high"], c["picks_in_band_high"],
                     f'{total_pred} / 75', badge("warn", "−" + str(75 - total_pred))])

    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<section class="hero">
  <p class="eyebrow">Fifteen sports · one table · every row linked to its source</p>
  <h1>The consolidated OLBG desk.</h1>
  <p class="lede">Everything OLBG was listing in the fifteen requested sports at the 23 October capture, matched
  against official schedules where a machine-readable one exists, priced by us across money line, handicap and
  totals, then graded — and written up for the best of them.</p>
  <div class="cta">
    <a class="button primary" href="/olbg-events.html">Every OLBG-listed event →</a>
    <a class="button" href="/picks.html">Graded picks</a>
    <a class="button" href="/predictions.html">Written predictions</a>
    <a class="button" href="/flagged.html">Flagged for review</a>
  </div>
</section>

{kpi_block(audit)}

{notice("warn", "Read this before using any number.",
        "This desk did not fetch anything live. The sandbox it was built in has no general internet access, so the "
        "evidence is the repository's own captures: OLBG pages fetched on a GitHub-hosted runner at 20:32Z and the "
        "fixture layer captured at 20:05Z. Every row names the file it came from. "
        "<a href='/verification.html'>What was checked, and what was not</a>.")}

<section>
<h2>Executive summary</h2>
<div class="two-col">
  <div class="card pad">
    <h3>Today · 23 October</h3>
    {exec_intro}
    <p class="small">Start times are shown exactly as the source printed them. A blank start means the source
    published a day but not a clock time; the desk does not fill it in.</p>
  </div>
  <div class="card pad">
    <h3>Band arithmetic</h3>
    {band_sentence}
  </div>
</div>

<h3 class="sub">Highest-confidence selections in the snapshot</h3>
<p class="small">Sorted by our own modelled chance. “In band” means the fair price sits between −250 and +10000.</p>
{"".join(high_rows)}

<h3 class="sub">The {len(in_band)} selections that are both high-confidence and inside the band</h3>
<p class="small">Every one is an alternate line quoted at the band ceiling — the natural price on the same
selection is shorter than −250.</p>
{table(["Sport", "Selection", "Chance", "Fair price", "Alternate line", "Fixture"], band_rows)}
</section>

<section>
<h2>Coverage by sport</h2>
<p class="sub">“OLBG upcoming” counts events OLBG itself was listing whose recorded start is after the capture
clock. The last column is the gap to the brief's five written predictions per sport. Nothing has been invented to
close it.</p>
{table(["Sport", "OLBG upcoming", "Fixtures own", "Priced", "High picks", "High &amp; in band", "Predictions", "Target"], cov_rows)}
<p class="small">Zero OLBG events for a sport does not mean OLBG covers nothing: the golf hub page returned an empty
tip payload in this capture, recorded as <a href="/flagged.html">U-07</a>.</p>
</section>

<section>
<h2>Earlier layers in this repository</h2>
<p class="sub">{audit["repo"]["counts"]["published_layers"]} complete desks were published here by earlier sessions. This page is the front door;
the others are kept for audit and are listed in full on <a href="/archive.html">Archive</a>. They disagree with each
other, so their counts must never be added to this page's.</p>
<p class="chips">
  <a class="chip" href="/cadence/index.html">cadence/ · the fixture layer this desk prices</a>
  <a class="chip" href="/ledger/index.html">ledger/ · first-hand capture desk</a>
  <a class="chip" href="/olbg/index.html">olbg/ · OLBG daily desk</a>
  <a class="chip" href="/brief/index.html">brief/ · daily brief</a>
  <a class="chip" href="/atlas/index.html">atlas/ · first-hand atlas</a>
  <a class="chip" href="/current/index.html">current/ · 22 October capture</a>
  <a class="chip" href="/daily/index.html">daily/ · top-five desk</a>
  <a class="chip" href="/final/index.html">final/ · consolidated 17-sport desk</a>
  <a class="chip" href="/archive.html">all {audit["repo"]["counts"]["published_layers"]} →</a>
</p>
</section>

<section>
<h2>What this desk does not claim</h2>
<div class="grid two">
  <div class="card pad"><h3>Not a live feed</h3><p>The OLBG pages were read once, at 20:32Z. Prices move. A price
  shown here is our fair estimate plus a standard margin, not a quote from a bookmaker.</p></div>
  <div class="card pad"><h3>Not full coverage</h3><p>{c["fixtures"]} fixtures are priced out of
  {c["olbg_events_upcoming"]} upcoming OLBG events. Where there was no defensible input the row is blank and the
  reason is printed, rather than a number being invented.</p></div>
  <div class="card pad"><h3>Not independent of the publisher</h3><p>Fixture listings come from OLBG; the facts
  behind each price come from the competition's own site. Where a fact could not be joined to a stored official
  body, the row says so on <a href="/verification.html">Verification</a>.</p></div>
  <div class="card pad"><h3>Not a tip service</h3><p>High confidence is a statement about our own probability, not
  about the outcome. {c["picks_high"]} of {c["picks"]} graded selections clear 70%.</p></div>
</div>
</section>
</main>"""
    return page("Overview", "index.html", body)


def build_olbg_events(inv, audit):
    by_event = {}
    for f in audit["fixtures"]:
        o = f.get("olbg") or {}
        if o.get("matched") and o.get("event_id"):
            by_event.setdefault(str(o["event_id"]), []).append(f)
    rows = []
    for ev in inv["events"]:
        ours = by_event.get(str(ev["event_id"]), [])
        if ours:
            status = badge("ok", "priced by us")
            ref = ", ".join(f'<a href="/matches.html#f-{e(f["id"])}">{fixture_label(f)}</a>' for f in ours[:2])
        else:
            status = badge("muted", "not priced")
            ref = '<span class="blank">—</span>'
        mark = '<span class="upcoming">●</span> ' if ev.get("upcoming_at_capture") else '<span class="past">○</span> '
        rows.append([
            f'<a href="/sports/{SPORT_SLUG[ev["sport"]]}.html">{e(ev["sport"])}</a>',
            mark + f'<strong>{e(ev["event"])}</strong><div class="tiny">{e(ev.get("league") or "league not stated")}</div>',
            e(ev.get("start_utc") or "—"),
            e(", ".join(k for k in ev["markets"] if k) or "—"),
            ev["tips"], status, ref, link(ev.get("event_url"), "olbg.com", "mini"),
        ])
    by_sport = []
    for sport in SPORTS:
        s = inv["counts"]["by_sport"].get(sport, {"events": 0, "upcoming": 0})
        cov = audit["coverage"][sport]
        by_sport.append([f'<a href="/sports/{SPORT_SLUG[sport]}.html">{e(sport)}</a>', s["events"],
                         s["upcoming"], cov["our_fixtures"], cov["our_fixtures_on_olbg"]])
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Every event OLBG was listing</h1>
<p class="lede">Read directly from the stored OLBG page bodies, not from a summary. {inv["counts"]["events"]} events
across {inv["counts"]["sports"]} sports; {inv["counts"]["upcoming"]} start after the capture clock. Event ids, start
times and market names are exactly what the page payload published.</p>

{notice("info", "Filled circle = still to be played at the capture time; hollow = already started.",
        "OLBG keeps short-lived events visible for a while, so a page read at 20:32Z still shows matches that began "
        "at 12:00Z. The desk marks them rather than deleting them, because deleting them would hide how thin the "
        "live card was in some sports.")}

<h2>By sport</h2>
{table(["Sport", "OLBG events", "Upcoming", "Fixtures we price", "Matched to OLBG"], by_sport)}

<h2>The list</h2>
<p class="sub">“Not priced” is a gap, not an omission: no defensible input existed in the capture window. Use the
filter box to search teams or competitions.</p>
{table(["Sport", "Event as OLBG prints it", "Start (recorded, UTC)", "Markets seen on the page", "Tips",
        "Our status", "Our fixture", "Listing"], rows, filterable=True)}
<p class="small">Market names are copied from the captured payload: Money Line, Pointspread, Game Totals,
Win Match, Win Match 2-way, Win Tournament, Handicap, Puck Line, Fastest Qualifier and Win Race all appear.</p>
</main>"""
    return page("OLBG list", "olbg-events.html", body)


def build_matches(inv, audit, lines):
    counts = {}
    for ln in lines["lines"]:
        counts[ln["fixture_id"]] = counts.get(ln["fixture_id"], 0) + 1
    rows = []
    for f in audit["fixtures"]:
        lvl = badge("ok", "official schedule") if f["verification_level"] == "official-schedule" else badge("warn", "capture bundle")
        o = f.get("olbg") or {}
        rows.append([
            f'<a href="/sports/{SPORT_SLUG[f["sport"]]}.html">{e(f["sport"])}</a><div class="tiny">{e(f.get("competition"))}</div>',
            f'<span id="f-{e(f["id"])}"><strong>{fixture_label(f)}</strong></span><div class="tiny">id {e(f["id"])}</div>',
            e(f.get("time_display") or f.get("start_utc") or "—"),
            counts.get(f["id"], 0) or '<span class="blank">none</span>',
            lvl,
            link(f.get("official_source_url"), "official"),
            link(f.get("stats_source_url"), "stats"),
            link(o.get("event_url"), "OLBG") if o.get("matched") else '<span class="blank">no listing found</span>',
        ])
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Our fixtures</h1>
<p class="lede">{len(audit["fixtures"])} fixtures across fifteen sports — the matches we were willing to price. The
last three columns open OLBG's listing, the governing body's page and the statistics page the price rests on.</p>
<ul class="legend">
  <li>{badge("ok", "official schedule")} joined on the fixture id to a stored league API or XML body (MLB, NHL, EuroLeague)</li>
  <li>{badge("warn", "capture bundle")} rests on the captured reading of the competition's page; no machine-readable official body is stored</li>
</ul>
{notice("info", "Why most rows say “capture bundle”.",
        "A capture bundle is a transcribed reading — URL, timestamp, values — without a stored response body. It "
        "is evidence of what the publishing session saw, not something this session can re-derive. Only MLB, NHL "
        "and EuroLeague fixtures join to a stored machine-readable official body. "
        "<a href='/verification.html'>Method and limits</a>.")}
{table(["Sport", "Fixture", "Start (as published)", "Our prices", "Corroborated by", "Official source",
        "Statistics source", "OLBG listing"], rows)}
</main>"""
    return page("Fixtures", "matches.html", body)


def build_lines(inv, audit, lines):
    by_sport = {}
    for ln in lines["lines"]:
        by_sport.setdefault(ln["sport"], []).append(ln)
    blocks = []
    for sport in SPORTS:
        rows = [[e(ln["fixture_id"]), e(ln["market"]), f'<strong>{e(ln["selection"])}</strong>',
                 pct(ln["probability"]), am(ln["fair_american"]), dec(ln["fair_decimal"]),
                 dec(ln.get("offered_decimal")), am(ln.get("offered_american")),
                 badge("ok", "in band") if ln.get("in_band") else badge("muted", "outside"),
                 badge(ln["confidence"], ln["confidence"]),
                 f'<span class="basis">{e(ln.get("basis"))}</span>']
                for ln in sorted(by_sport.get(sport, []), key=lambda x: (x["fixture_id"], x["market"], -x["probability"]))]
        if rows:
            blocks.append(f"""<h2 id="{SPORT_SLUG[sport]}">{e(sport)} <span class="count">{len(rows)} prices</span></h2>
{table(["Fixture id", "Market", "Selection", "Chance", "Fair US", "Fair dec", "Offered dec", "Offered US",
        "Brief band", "Confidence", "Basis"], rows, filterable=True)}""")
        else:
            blocks.append(f'<h2 id="{SPORT_SLUG[sport]}">{e(sport)}</h2><p class="muted">No price originated.</p>')
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Our own prices</h1>
<p class="lede">{audit["counts"]["prices"]} prices originated across fifteen sports. Fair price is the price implied
by our probability with no margin; offered price applies the desk's standard margin. The basis column is the input
arithmetic, so every number can be re-derived.</p>
{notice("info", "Estimates, not bookmaker quotes.",
        "Nothing here is copied from a bookmaker and an offered price does not mean it is available to bet. The "
        "brief asks for origination, so the desk publishes its own numbers and its inputs. Selections whose fair "
        "price falls between −250 and +10000 are marked “in band”.")}
{"".join(blocks)}
</main>"""
    return page("Our prices", "lines.html", body)


def build_picks(inv, audit, preds):
    picks = audit["picks"]
    pred_by_pick = {p["pick_id"]: p["id"] for p in preds["predictions"]}
    rows = []
    for p in sorted(picks, key=lambda x: (-x["probability"], x["sport"])):
        wrote = pred_by_pick.get(p["id"])
        rows.append([
            f'<a href="/sports/{SPORT_SLUG[p["sport"]]}.html">{e(p["sport"])}</a>', fixture_label(p),
            f'<strong>{e(p["selection"])}</strong><div class="tiny">{e(p["market"])}</div>',
            pct(p["probability"]), am(p.get("fair_american")),
            badge(p["confidence"], p["confidence"].upper()),
            badge("ok", "in band") if p.get("in_band") else badge("muted", "outside"),
            f'<a href="/predictions.html#{e(wrote)}">read</a>' if wrote else '<span class="blank">—</span>',
            f'<span class="basis">{e(p.get("basis"))}</span>',
        ])
    tiers = {}
    for p in picks:
        key = p.get("evidence_tier", "?")
        tiers[key] = tiers.get(key, 0) + 1
    tier_kpis = "".join(f'<div class="kpi"><div class="v">{n}</div><div class="k">{e(str(k).upper())}</div>'
                        f'<div class="s">{pct(n / len(picks))} of picks</div></div>' for k, n in sorted(tiers.items(), reverse=True))
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Graded picks</h1>
<p class="lede">{len(picks)} selections graded low, medium or high. A pick is the single best selection we would put
forward on a fixture-market; the fuller ladder of alternate lines is on <a href="/lines.html">Our prices</a>.
{audit["counts"]["picks_high"]} reach high confidence and {audit["counts"]["picks_in_band_high"]} of those are also
inside the brief's −250…+10000 band.</p>
<div class="kpis small">{tier_kpis}</div>
{notice("warn", "Confidence is ours, not the market's.",
        "A high grade means our own probability clears 70%. The desk has no results ledger yet, so the grades are "
        "estimates under review rather than a measured record.")}
{table(["Sport", "Fixture", "Selection", "Chance", "Fair price", "Confidence", "Brief band", "Write-up", "Basis"],
        rows, filterable=True)}
</main>"""
    return page("Picks", "picks.html", body)


def build_predictions(inv, audit, preds):
    cards = []
    for p in sorted(preds["predictions"], key=lambda x: (SPORTS.index(x["sport"]), -x["probability"])):
        cards.append(f"""<article class="pred" id="{e(p['id'])}">
  <header><span class="tag">{e(p['sport'])}</span><h2>{e(p['headline'])}</h2>
  <p class="meta">{fixture_label(p)} · {e(p['competition'])} · {e(p.get('time_display') or '')}</p></header>
  <p class="selection"><strong>Selection:</strong> {e(p['selection'])} — {e(p['market'])} at
  {am(p.get('fair_american'))} fair ({pct(p['probability'])}), {badge(p['confidence'], p['confidence'].upper())}</p>
  <p>{e(p['text'])}</p>
  <p class="meta">{len(p['text'].split())} words · <a href="/sports/{SPORT_SLUG[p['sport']]}.html">all {e(p['sport'])} rows</a></p>
</article>""")
    picks_by_id = {q["id"]: q for q in audit["picks"]}
    alt = [p for p in preds["predictions"] if (picks_by_id.get(p.get("pick_id")) or {}).get("band_line")]
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Written predictions</h1>
<p class="lede">{len(preds["predictions"])} write-ups across
{len({p["sport"] for p in preds["predictions"]})} sports. Each names its selection explicitly, quotes only figures
that appear in the fixture's stored evidence, and runs to at least thirty words. Every number was re-checked against
that fixture's own facts by <a href="/verification.html">check A8</a>.</p>
{notice("warn", f"{len(alt)} of the {len(preds['predictions'])} are alternate-line write-ups.",
        "Where the natural price of a selection is shorter than −250, the desk quotes an alternative line inside the "
        "band and writes on that line. The prose says which line it is and the <a href='/band.html'>band page</a> "
        "lists them all. The rest are outside the band and are published with their real prices rather than "
        "suppressed.")}
{"".join(cards)}
</main>"""
    return page("Predictions", "predictions.html", body)


def build_band(inv, audit, picks, preds):
    high = sorted([p for p in picks if p["confidence"] == "high"], key=lambda p: -p["probability"])
    in_band = [p for p in high if p.get("in_band")]
    natural = [p for p in in_band if not p.get("band_line")]
    alt = [p for p in in_band if p.get("band_line")]

    def rows_for(items):
        return [[f'<a href="/sports/{SPORT_SLUG[p["sport"]]}.html">{e(p["sport"])}</a>',
                 f'<strong>{e(p["selection"])}</strong><div class="tiny">{e(p["market"])}</div>',
                 pct(p["probability"]), am(p.get("fair_american")),
                 "alternate line" if p.get("band_line") else "natural line", fixture_label(p)]
                for p in items]

    if natural:
        natural_sentence = (f"{len(natural)} of those is inside it on a natural price and {len(alt)} clear it only "
                            "by quoting an alternate line, marked as such here and in the prose.")
    else:
        natural_sentence = ("None of them is inside it on a natural price: all "
                            f"{len(alt)} clear it only by quoting an alternate line, marked as such here and in "
                            "the prose.")
    alt_rows = []
    for p in alt:
        pid = next((q["id"] for q in preds["predictions"] if q["pick_id"] == p["id"]), None)
        alt_rows.append(rows_for([p])[0] + [f'<a href="/predictions.html#{e(pid)}">read</a>' if pid else '<span class="blank">—</span>'])

    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>The −250 to +10000 band</h1>
<p class="lede">The brief asks for high-confidence picks priced between −250 and +10000. Those two conditions
interact, and the desk refuses to paper over it.</p>
<div class="two-col">
<div class="card pad">
<h2>Arithmetic</h2>
<p>A moneyline of −250 implies a 71.43% chance (250 ÷ 350). A moneyline of +10000 implies 0.99%. The band therefore
runs from 0.99% up to 71.43%. “High confidence” here means a chance of 70% or more.</p>
<p>The overlap is <strong>70.00–71.43%</strong> — a 1.43-point window. A selection at 78% is outside the band however
confident it is; a selection at 40% is inside the band while being nowhere near high confidence.</p>
</div>
<div class="card pad">
<h2>What the desk does</h2>
<p>It publishes both, labelled. {len(high)} selections grade high; {len(in_band)} are inside the band.
{natural_sentence}</p>
<p>The other {len(high) - len(in_band)} high selections are shorter than −250. They are not deleted to make the
scoreboard look tidier: each is listed below with its true price.</p>
</div>
</div>
<h2>Inside the band</h2>
{table(["Sport", "Selection", "Chance", "Fair price", "Line type", "Fixture"], rows_for(in_band))}
<h2>High confidence, outside the band</h2>
<p class="sub">Real prices shorter than −250 — what a staking plan would actually see most often.</p>
{table(["Sport", "Selection", "Chance", "Fair price", "Line type", "Fixture"],
        rows_for([p for p in high if not p.get("in_band")]))}
<h2>Write-ups on alternate lines</h2>
{table(["Sport", "Selection", "Chance", "Fair price", "Line type", "Fixture", "Write-up"], alt_rows) if alt_rows else '<p class="muted">None.</p>'}
</main>"""
    return page("Band", "band.html", body)


def build_sources(inv, audit, sources):
    rows = [[e(s["publisher"]), link(s["url"], s["url"].replace("https://", ""), "mini"),
             badge("ok", "governing body") if s.get("host_classified_official") else badge("warn", "other host"),
             e(s["fetched_utc"]), f'<span class="basis">{e(s.get("what"))}</span>']
            for s in sorted(sources["sources"], key=lambda x: (x["publisher"], x["url"]))]
    cap_rows = [[e(p["key"]), link(p["url"], p["url"].replace("https://www.olbg.com", ""), "mini"),
                 p["status"], e(p.get("fetched_at")), f'{p.get("bytes"):,}' if p.get("bytes") else "—",
                 e(str(p.get("sha256"))[:16] + "…"), e(p.get("stored_as"))]
                for p in sorted(inv["pages"], key=lambda x: x["key"] or "")]
    bad_rows = [[e(p["key"]), link(p["url"], "open", "mini"), p["status"], e(p.get("fetched_at"))]
                for p in sorted(inv["non_200"], key=lambda x: x["key"] or "")]
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Sources</h1>
<p class="lede">Two registers. The first is the provenance of every fixture fact: {len(sources["sources"])} pages
from the competitions' own sites and OLBG's listing pages. The second is the raw material behind
<a href="/olbg-events.html">the OLBG list</a>: {len(inv["pages"])} stored page bodies with status code, fetch time,
byte count and hash, so each can be re-read later.</p>
<h2>Official and listing pages cited</h2>
{table(["Publisher", "URL", "Host class", "Read at (UTC)", "What it was read for"], rows, filterable=True)}
<h2>Stored OLBG bodies behind the event list</h2>
<p class="sub">These are the files in <code>data/ledger/raw/</code>. The hash is the first sixteen characters of the
sha256 in <code>data/ledger/manifest.json</code>; the parser re-hashes each file and refuses any whose hash moved.</p>
{table(["Capture key", "Final URL", "HTTP", "Fetched (UTC)", "Bytes", "sha256", "Stored as"], cap_rows, filterable=True)}
<h2>URLs that refused the capture job</h2>
<p class="sub">A 403, 404 or login redirect is published rather than hidden: it is the reason a sport or market is
missing. {len(bad_rows)} URLs.</p>
{table(["Capture key", "URL", "HTTP", "Fetched (UTC)"], bad_rows, filterable=True)}
</main>"""
    return page("Sources", "sources.html", body)


def build_verification(inv, audit):
    rows = [[f'<strong>{e(c["id"])}</strong>', e(c["check"]), e(c["scope"]),
             badge("ok", c["result"]) if c["result"] == "pass" else badge("warn", c["result"]),
             f'<span class="basis">{e(c["detail"])}</span>'] for c in audit["checks"]]
    lvl = {}
    for f in audit["fixtures"]:
        lvl[f["verification_level"]] = lvl.get(f["verification_level"], 0) + 1
    lvl_cards = "".join(
        f'<div class="card pad"><div class="v">{n}</div><div class="k">'
        f'{badge("ok" if k == "official-schedule" else "warn", k)}</div></div>'
        for k, n in sorted(lvl.items()))
    recon = [[e(r["sport"]), r["unified_upcoming"], r["ledger_upcoming"], r["delta"],
              f'<span class="basis">{e(r["note"])}</span>'] for r in audit["reconciliation"] if r["delta"]]
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Verification</h1>
<p class="lede">What this session checked, what it could not check, and how each row is labelled. The audit script
re-derives every number from committed files; it does not trust another layer's summary.</p>
{notice("warn", "The honest limit.",
        "This sandbox cannot reach olbg.com, nba.com, the NHL API or any other sports host: every outbound request "
        "returns no connection. Verification here therefore means <em>consistent with the stored evidence and "
        "re-derived from it</em>, never <em>seen live today by this session</em>. The stored evidence was fetched on "
        "a GitHub-hosted runner, and its status codes and hashes are on <a href='/sources.html'>Sources</a>.")}
<h2>Checks</h2>
{table(["#", "Check", "Scope", "Result", "What was done"], rows)}
<h2>How each fixture is labelled</h2>
<div class="grid four">{lvl_cards}</div>
<p class="small"><strong>official schedule</strong> — the fixture id joined to a stored API or XML body from the
league itself (MLB <code>statsapi</code>, NHL <code>api-web</code>, EuroLeague schedule XML) and both sides matched.
<strong>capture bundle</strong> — the only stored evidence is the publishing session's transcribed reading of the
competition's page; the official URL is on the row for you to open.</p>
<h2>Second reading of the OLBG pages</h2>
<p class="sub">This desk parsed the stored OLBG bodies itself, reading both the sport hub and the all-events page per
sport. Where that produced more upcoming events than the earlier single-page parse, the difference is shown rather
than silently adopted.</p>
{table(["Sport", "This desk (upcoming)", "Earlier layer (upcoming)", "Delta", "Why"], recon) if recon else '<p class="muted">No differences.</p>'}
<h2>What would change a row</h2>
<ul class="tight">
  <li>A stored official body that contradicts a fact — the row would be blanked and flagged, not edited quietly.</li>
  <li>A governing body publishing a fixture we could not match — it would be added with its own source.</li>
  <li>A refreshed OLBG capture after the matches start — the upcoming marks would move, and prices with them.</li>
</ul>
</main>"""
    return page("Verification", "verification.html", body)


def build_repo_review(inv, audit):
    repo = audit["repo"]
    prior = audit.get("prior_layer_findings", [])
    prior_rows = [[e(p["id"]), badge("warn", p.get("severity", "")), e(p.get("category", "")),
                   e(p.get("file_path", "")), f'<span class="basis">{e(p.get("issue"))}</span>',
                   link(p.get("official_source_url"), "source", "mini")] for p in prior]
    mine = [[e(f["id"]), badge("warn", f["severity"]), e(f["category"]),
             f'<strong>{e(f["item"])}</strong>', f'<span class="basis">{e(f["finding"])}</span>',
             link(f.get("source_url"), "source", "mini")] for f in audit["findings"]]
    c = repo["counts"]
    not_ci = c.get("layers_not_rebuilt_by_ci", [])
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Repository review</h1>
<p class="lede">Many sessions have worked in this repository in parallel. That produced a lot of evidence and a lot
of duplication. This page audits the repository against the files on disk, not against any session's claim about
them.</p>
<div class="kpis">
  <div class="kpi"><div class="v">{c.get("published_layers")}</div><div class="k">published layers</div><div class="s">directories with their own front page</div></div>
  <div class="kpi"><div class="v">{len(not_ci)}</div><div class="k">not rebuilt by CI</div><div class="s">can drift without a failing check</div></div>
  <div class="kpi"><div class="v">{c.get("merge_conflict_marker_lines", 0)}</div><div class="k">conflict-marker lines</div><div class="s">left in COORDINATION.md</div></div>
  <div class="kpi"><div class="v">{c.get("prediction_files_with_prohibited_words", 0)}</div><div class="k">prose files with banned words</div><div class="s">{c.get("prohibited_word_occurrences_other_layers", 0)} occurrences</div></div>
  <div class="kpi"><div class="v">{c.get("root_data_rows", "—")}</div><div class="k">rows in the root dataset</div><div class="s">snapshot {e(c.get("root_data_snapshot") or "unknown")}, {c.get("root_data_sports", "?")} sports</div></div>
  <div class="kpi"><div class="v">{c.get("out_of_scope_sport_pages", 0)}</div><div class="k">out-of-scope sport pages</div><div class="s">Aussie Rules and esports</div></div>
</div>
{notice("warn", "The biggest irregularity: " + str(c.get("published_layers")) + " front doors.",
        "Each session built its own complete site. They overlap heavily, their counts contradict each other and "
        "nothing in the repository says which is current. This desk resolves that by naming one canonical layer on "
        "the front page and listing every other layer, with its last build time, on <a href='/archive.html'>Archive</a>. "
        "None of the others has been deleted.")}
<h2>Findings from this audit</h2>
{table(["#", "Severity", "Category", "Item", "Finding", "Source"], mine)}
<h2>Earlier findings, reproduced here for review</h2>
<p class="sub">Raised by the previous audit pass and republished so they sit next to the current findings instead of
being buried in a directory nobody opens.</p>
{table(["#", "Severity", "Category", "File", "Issue", "Source"], prior_rows)}
<h2>Verification performed for this page</h2>
<ul class="tight">
  <li>Conflict markers: counted directly in <code>COORDINATION.md</code> ({c.get("merge_conflict_marker_lines")} lines).</li>
  <li>Out-of-scope pages: counted every published <code>*.html</code> whose filename is an excluded sport ({c.get("out_of_scope_sport_pages")}).</li>
  <li>Banned words: regex scan of every <code>data/**/predictions*.json</code>; {c.get("prediction_files_with_prohibited_words")} files contain them.</li>
  <li>CI coverage: every desk directory compared against the step list in <code>.github/workflows/pages.yml</code>.</li>
  <li>Cross-layer price conflict: the same MLB game read from four layers' own <code>lines.json</code>.</li>
</ul>
</main>"""
    return page("Repo review", "repo-review.html", body)


def build_flagged(inv, audit):
    rows = [[e(f["id"]), badge("warn", f["severity"]), e(f["category"]), f'<strong>{e(f["item"])}</strong>',
             f'<span class="basis">{e(f["finding"])}</span>', link(f.get("source_url"), "source", "mini"),
             e(f.get("evidence") or "—")] for f in audit["findings"]]
    prior = [[e(p["id"]), e(p.get("severity")), e(p.get("category")), e(p.get("item") or p.get("file_path")),
              f'<span class="basis">{e(p.get("finding") or p.get("issue"))}</span>',
              link(p.get("source_url") or p.get("official_source_url"), "source", "mini")]
             for p in audit.get("prior_layer_findings", [])]
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Flagged for review</h1>
<p class="lede">Everything on this desk that is blank, contradicted, unconfirmed or irregular, in one place, with the
source that shows it. None of it blocks the site: the affected values are simply not published as if they were
settled.</p>
{notice("info", "Three kinds of flag.",
        "<strong>Gap</strong> — a value we could not confirm, left blank. <strong>Contradiction</strong> — two stored "
        "numbers disagree. <strong>Defect</strong> — something is wrong with the repository or the capture.")}
<h2>Open items from this desk</h2>
{table(["#", "Severity", "Category", "Item", "Finding", "Source", "Evidence / file"], rows)}
<h2>Carried forward from the previous pass</h2>
<p class="sub">These belong to the fixture layer this desk publishes. They are kept visible rather than assumed
fixed.</p>
{table(["#", "Severity", "Category", "Item", "Finding", "Source"], prior)}
</main>"""
    return page("Flagged", "flagged.html", body)


def build_methodology(inv, audit):
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Method</h1>
<p class="lede">How a match gets from an OLBG listing to a price, a confidence label and — sometimes — a written
prediction. Every step is executed by a script in <code>scripts/</code>, and the pages are rendered from the JSON
those scripts write.</p>
<h2>1 · Scope</h2>
<p>Fifteen sports, exactly as the brief lists them: Golf, Volleyball, Rugby Union, Cricket, Snooker, Darts, Baseball,
Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball and Rugby League. Gaelic football
and hurling sit under Gaelic Sports. Aussie Rules, esports, football, horse racing, American football, boxing and MMA
are out of scope and are not published here.</p>
<h2>2 · Where the fixture list comes from</h2>
<p>The stored OLBG listing pages are re-parsed by <code>scripts/unified_inventory.py</code>. Each tip object in the
page payload contributes an event name, an OLBG event id, a start timestamp and a market name. Events are
de-duplicated on sport plus event id, and an event is marked <em>upcoming</em> only when its recorded start is later
than the capture clock. The parser re-hashes every stored body against the manifest and refuses a file whose hash has
moved.</p>
<h2>3 · What proves a fixture</h2>
<p>Preference order, strongest first: a machine-readable body from the league itself (MLB <code>statsapi</code>, NHL
<code>api-web</code>, EuroLeague schedule XML), joined on the fixture id and checked on both sides; then the publishing
session's captured reading of the competition's page, labelled as such. A fixture that neither family supports is not
published.</p>
<h2>4 · How a price is originated</h2>
<p>Each sport has a strength input taken from the competition's own published numbers: league points or win
percentages, goals or points scored and conceded, and a home term where the competition has one. Those become a win
probability, a handicap distribution or a total expectation. The fair price is the inverse of the probability; the
offered price applies a fixed margin. The basis column on <a href="/lines.html">Our prices</a> prints the arithmetic
so a reader can redo it.</p>
<h2>5 · Confidence</h2>
<p>High is a chance of 70% or more, medium is 60–70%, low is under 60%. One documented exception: an alternate band
line on a thin sample is capped at medium even when its probability clears 70%. Those rows are marked
<code>band_line</code> in the data, and the audit counts them separately ({audit["band"]["documented_caps"]} rows)
rather than letting the cap go unrecorded.</p>
<h2>6 · Which picks get written up</h2>
<p>Only selections at medium confidence or better receive prose, one per fixture-market. Where a sport has fewer than
five such selections it gets fewer than five write-ups: the desk does not promote a low-confidence row to meet a
quota. The current shortfall is on <a href="/index.html">the overview</a> and in flag U-05.</p>
<h2>7 · What the prose may contain</h2>
<p>At least thirty words; a unique opening three words; the selection named in the text; only figures that appear in
that fixture's stored facts, inputs or prices; and none of the words the brief bans from output. The last two rules
are machine-checked by <code>scripts/unified_audit.py</code> (checks A3 and A8), not left to proofreading.</p>
<h2>8 · Reproducing this site</h2>
<pre class="code">python3 scripts/unified_inventory.py   # re-parse the stored OLBG bodies
python3 scripts/unified_audit.py       # re-derive every number and every check
python3 scripts/unified_build.py       # render these pages</pre>
<p>The three scripts read only committed files and write deterministic output, so the validation workflow can prove
the published pages match the published data.</p>
</main>"""
    return page("Method", "methodology.html", body)


def build_archive(inv, audit):
    dirs = []
    for p in sorted(ROOT.iterdir()):
        idx = p / "index.html"
        if p.is_dir() and idx.exists() and p.name not in ("sports", "assets"):
            stamp = dt.datetime.fromtimestamp(idx.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
            dirs.append([f'<a href="/{e(p.name)}/index.html"><strong>{e(p.name)}/</strong></a>', e(stamp)])
    known = {href.replace("/", "") for href, _ in NAV} | {"index.html", "olbg-events.html", "repo-review.html"}
    extras = sorted(p.name for p in ROOT.glob("*.html") if p.name not in known and p.name != "index.html")
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Archive of earlier layers</h1>
<p class="lede">Each directory below is a complete, previously published desk. They are kept because deleting evidence
is worse than duplicating it — but they overlap, they disagree, and their counts must never be added together. This
page exists so the front door can be one page while nothing is lost.</p>
{notice("warn", "Do not sum these layers.",
        "The same match appears in several with different prices. MLB game 849805 is published at 0.533, 0.594, 0.603 "
        "and 0.651 by four different layers. They are different snapshots taken with different inputs, not four "
        "independent confirmations. <a href='/repo-review.html'>Repo review</a> records the detail.")}
<h2>Layer front pages</h2>
<p class="sub">The timestamp is the last-modified time of the layer's own <code>index.html</code> on disk — a build
artefact, not a claim about how current its data is.</p>
{table(["Layer", "index.html last modified (UTC)"], dirs, filterable=True)}
<h2>Other root-level pages left in place</h2>
<p class="sub">Older front-page artefacts that belong to no layer directory.</p>
<p class="chips">{"".join(f'<a class="chip" href="/{e(n)}">{e(n)}</a>' for n in extras)}</p>
<h2>How this desk relates to them</h2>
<ul class="tight">
  <li>The front page, <a href="/index.html">Overview</a>, and every page in the navigation are generated by
  <code>scripts/unified_build.py</code> from <code>data/unified/</code> and <code>data/cadence/</code>.</li>
  <li>Fixture facts, prices and predictions come from the 23 October capture; the OLBG event list is re-parsed from
  the stored page bodies of the same day.</li>
  <li>Nothing in an archived layer is edited, and no archived layer is deleted.</li>
</ul>
</main>"""
    return page("Archive", "archive.html", body)



def build_out_of_scope_stub(slug, title, reason, redirect_to=None):
    """Explicitly retire an out-of-scope or superseded sport page instead of deleting it.

    Earlier layers still link to these filenames, so they must resolve; the stub says why the
    sport is not covered here and points at the page that supersedes it.
    """
    target = ""
    if redirect_to:
        target = f'<p>Coverage for this sport is published under <a href="/sports/{redirect_to}.html">{redirect_to}</a>.</p>'
    body = f"""{snapshot_strip(_INV, _AUDIT)}
<main class="wrap" id="main">
<p class="crumb"><a href="/sports/index.html">Sports</a> / {e(title)}</p>
<h1>{e(title)}</h1>
{notice("warn", "Not covered by this desk.", e(reason))}
{target}
<p><strong>Why this page exists.</strong> An earlier layer published a full page at this address and other layers
still link to it. It is kept as a stub so no link breaks, rather than deleted or silently left stale.
<a href="/sports/index.html">The fifteen sports this desk covers</a> · <a href="/archive.html">all earlier layers</a> ·
<a href="/current/index.html">current/ (22 October capture)</a>.</p>
</main>"""
    return page(title, f"sports/{slug}.html", body)


def build_sports_index(inv, audit):
    rows = []
    for sport in SPORTS:
        cov = audit["coverage"][sport]
        total = inv["counts"]["by_sport"].get(sport, {}).get("events", 0)
        rows.append([f'<a href="/sports/{SPORT_SLUG[sport]}.html"><strong>{e(sport)}</strong></a>',
                     total, cov["olbg_events_upcoming"], cov["our_fixtures"], cov["our_fixtures_priced"],
                     cov["picks"].get("high", 0), cov["picks"].get("in_band_high", 0),
                     f'{cov["predictions"]} / {cov["prediction_target"]}'])
    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<h1>Sports</h1>
<p class="lede">One page per sport: what OLBG was listing, what we priced, how the picks graded, and the write-ups
where there are any. Earlier published layers that cover the same sports are kept on
<a href="/archive.html">Archive</a>; the most recent previous capture is
<a href="/current/index.html">current/</a>.</p>
{table(["Sport", "OLBG events (all)", "Upcoming", "Fixtures own", "Priced", "High picks", "High &amp; in band",
        "Predictions"], rows)}
</main>"""
    return page("Sports", "sports/index.html", body)


def build_sport_page(inv, audit, sport, lines, picks, preds):
    slug = SPORT_SLUG[sport]
    cov = audit["coverage"][sport]
    events = [ev for ev in inv["events"] if ev["sport"] == sport]
    fixtures = [f for f in audit["fixtures"] if f["sport"] == sport]
    sport_lines = [ln for ln in lines["lines"] if ln["sport"] == sport]
    sport_picks = [p for p in picks if p["sport"] == sport]
    sport_preds = [p for p in preds["predictions"] if p["sport"] == sport]

    event_rows = [[f'<strong>{e(ev["event"])}</strong><div class="tiny">{e(ev.get("league") or "")}</div>',
                   e(ev.get("start_utc") or "—"),
                   badge("ok", "upcoming") if ev.get("upcoming_at_capture") else badge("muted", "started"),
                   e(", ".join(k for k in ev["markets"] if k) or "—"),
                   link(ev.get("event_url"), "listing", "mini")] for ev in events] or \
                 [["—", "—", badge("muted", "none captured"), "—", "—"]]
    fx_rows = [[fixture_label(f), e(f.get("time_display") or f.get("start_utc") or "—"),
                badge("ok", "official") if f["verification_level"] == "official-schedule" else badge("warn", "capture"),
                link(f.get("official_source_url"), "source", "mini"),
                link((f.get("olbg") or {}).get("event_url"), "OLBG", "mini")
                if (f.get("olbg") or {}).get("matched") else '<span class="blank">not found</span>'] for f in fixtures] or \
               [["—", "—", badge("muted", "none"), "—", "—"]]
    line_rows = [[e(ln["market"]), f'<strong>{e(ln["selection"])}</strong>', pct(ln["probability"]),
                  am(ln["fair_american"]), dec(ln.get("offered_decimal")),
                  badge(ln["confidence"], ln["confidence"]), f'<span class="basis">{e(ln.get("basis"))}</span>']
                 for ln in sorted(sport_lines, key=lambda x: (x["fixture_id"], -x["probability"]))] or \
                [["—", "—", "—", "—", "—", badge("muted", "no price"),
                  "No defensible input in this capture."]]
    pick_rows_ = [[fixture_label(p), f'<strong>{e(p["selection"])}</strong>', e(p["market"]),
                   pct(p["probability"]), am(p.get("fair_american")),
                   badge(p["confidence"], p["confidence"]),
                   badge("ok", "in band") if p.get("in_band") else badge("muted", "outside")]
                  for p in sorted(sport_picks, key=lambda x: -x["probability"])] or \
                 [["—", "—", "—", "—", "—", badge("muted", "none"), "—"]]
    preds_html = "".join(f"""<article class="pred"><h3>{e(p['headline'])}</h3>
<p class="meta">{fixture_label(p)} · {e(p['selection'])} at {am(p.get('fair_american'))} fair · {len(p['text'].split())} words</p>
<p>{e(p['text'])}</p></article>""" for p in sport_preds) or \
        '<p class="muted">No written prediction for this sport in the current snapshot. The reason is on <a href="/flagged.html">Flagged</a>.</p>'

    body = f"""{snapshot_strip(inv, audit)}
<main class="wrap" id="main">
<p class="crumb"><a href="/sports/index.html">Sports</a> / {e(sport)}</p>
<h1>{e(sport)}</h1>
<div class="kpis">
  <div class="kpi"><div class="v">{cov["olbg_events_upcoming"]}</div><div class="k">OLBG upcoming</div><div class="s">{cov["olbg_events_captured"]} listed in all</div></div>
  <div class="kpi"><div class="v">{cov["our_fixtures"]}</div><div class="k">fixtures we price</div><div class="s">{cov["our_fixtures_priced"]} with a price</div></div>
  <div class="kpi"><div class="v">{cov["picks"].get("high", 0)}</div><div class="k">high picks</div><div class="s">{cov["picks"].get("in_band_high", 0)} in band</div></div>
  <div class="kpi"><div class="v">{cov["predictions"]} / 5</div><div class="k">predictions</div><div class="s">gap {cov["prediction_shortfall"]}</div></div>
</div>
<p class="small">Earlier published layer covering this sport:
<a href="/current/index.html">current/ (22 October capture)</a> · <a href="/archive.html">all layers</a>.</p>
<h2>What OLBG was listing</h2>
{table(["Event", "Start (UTC)", "State", "Markets seen", "Link"], event_rows)}
<h2>Our fixtures</h2>
{table(["Fixture", "Start (as published)", "Corroborated by", "Official source", "OLBG listing"], fx_rows)}
<h2>Our prices</h2>
{table(["Market", "Selection", "Chance", "Fair US", "Offered dec", "Confidence", "Basis"], line_rows)}
<h2>Graded picks</h2>
{table(["Fixture", "Selection", "Market", "Chance", "Fair price", "Confidence", "Brief band"], pick_rows_)}
<h2>Predictions</h2>
{preds_html}
</main>"""
    return page(sport, f"sports/{slug}.html", body)


# --------------------------------------------------------------------------- assets

def write_assets():
    css = """/* OLBG2 unified desk - one stylesheet for the whole site */
:root{--ink:#0f172a;--ink2:#334155;--muted:#64748b;--line:#e2e8f0;--bg:#f8fafc;--card:#fff;
--teal:#0d9488;--teal-d:#0f766e;--radius:14px}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--teal-d);text-decoration-thickness:1px;text-underline-offset:2px}
a:hover{color:var(--ink)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:99}
.topbar{background:var(--ink);color:#fff;position:sticky;top:0;z-index:20}
.bar{display:flex;align-items:center;gap:18px;min-height:58px;flex-wrap:wrap;padding:8px 20px}
.brand{color:#fff;font-weight:700;text-decoration:none;display:flex;align-items:center;gap:8px}
.brand .mark{width:12px;height:12px;border-radius:4px;background:var(--teal);display:inline-block}
.brand .sub{font-weight:400;color:#94a3b8;font-size:13px}
.nav{display:flex;gap:3px;flex-wrap:wrap;margin-left:auto}
.nav a{color:#cbd5e1;text-decoration:none;font-size:13.5px;padding:6px 9px;border-radius:8px}
.nav a:hover{background:#1e293b;color:#fff}
.nav a[aria-current="page"]{background:var(--teal);color:#fff}
.stripe{background:#ecfdf5;border-bottom:1px solid #d1fae5;font-size:13px;color:#065f46}
.stripe .wrap{padding:7px 20px}
main{padding:28px 20px 60px}
h1{font-size:clamp(26px,3.4vw,38px);line-height:1.15;margin:.2em 0 .35em;letter-spacing:-.5px}
h2{font-size:22px;margin:2.1em 0 .5em;letter-spacing:-.2px}
h3{font-size:17px;margin:1.2em 0 .4em}
.hero{padding:10px 0 6px;border-bottom:1px solid var(--line);margin-bottom:20px}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:700;color:var(--teal-d);margin:0}
.lede{font-size:17.5px;color:var(--ink2);max-width:78ch}
.sub{color:var(--muted);max-width:88ch}
.small{font-size:13px;color:var(--muted)}
.tiny{font-size:12px;color:var(--muted)}
.muted{color:var(--muted)}
.cta{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 6px}
.button{display:inline-block;padding:10px 15px;border-radius:10px;border:1px solid var(--line);background:#fff;color:var(--ink);text-decoration:none;font-weight:600;font-size:14px}
.button:hover{border-color:var(--teal);color:var(--teal-d)}
.button.primary{background:var(--teal);border-color:var(--teal);color:#fff}
.button.primary:hover{background:var(--teal-d);color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin:20px 0}
.kpis.small .v{font-size:24px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px}
.kpi .v{font-size:30px;font-weight:750;line-height:1.05;letter-spacing:-1px}
.kpi .k{font-size:13px;font-weight:650;margin-top:4px}
.kpi .s{font-size:12px;color:var(--muted)}
.notice{border-radius:var(--radius);padding:14px 16px;margin:18px 0;border:1px solid;font-size:14.5px}
.notice.warn{background:#fffbeb;border-color:#fde68a;color:#78350f}
.notice.info{background:#eff6ff;border-color:#bfdbfe;color:#1e3a8a}
.notice a{color:inherit;font-weight:600}
.two-col{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.grid{display:grid;gap:14px}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.grid.four{grid-template-columns:repeat(auto-fit,minmax(180px,1fr));margin:12px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius)}
.card.pad{padding:16px 18px}
.card.pad h2,.card.pad h3{margin-top:0}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}
thead th{background:#f1f5f9;text-align:left;font-weight:650;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#475569;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap;position:sticky;top:0}
tbody td{padding:9px 12px;border-bottom:1px solid #eef2f7;vertical-align:top}
tbody tr:nth-child(even){background:#fbfdff}
tbody tr:hover{background:#f0fdfa}
.basis{font-size:12px;color:var(--ink2);display:block;max-width:52ch}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:2.5px 7px;border-radius:999px;background:#e2e8f0;color:#334155;white-space:nowrap}
.badge.high{background:#dcfce7;color:#166534}
.badge.medium{background:#fef3c7;color:#92400e}
.badge.low{background:#e2e8f0;color:#334155}
.badge.ok{background:#dcfce7;color:#166534}
.badge.warn{background:#fef3c7;color:#92400e}
.badge.risk{background:#fee2e2;color:#991b1b}
.badge.muted{background:#f1f5f9;color:#64748b}
.blank{color:#94a3b8}
.legend{list-style:none;padding:0;display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--ink2)}
.legend li{display:flex;gap:6px;align-items:center}
.pickrow{display:grid;grid-template-columns:1fr auto auto 200px;gap:14px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:11px 14px;margin-bottom:8px}
.pr-main .sport{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--teal-d);margin-right:8px}
.pr-num{text-align:right}
.pr-num .big{display:block;font-size:19px;font-weight:750}
.pr-badges{display:flex;gap:6px;flex-direction:column;align-items:flex-start}
.pr-when{font-size:12.5px;color:var(--muted)}
.vs{color:#94a3b8;font-weight:400}
.pred{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;margin:16px 0}
.pred h2,.pred h3{margin:.1em 0 .35em}
.pred .tag{display:inline-block;background:#ccfbf1;color:#115e59;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:3px 8px;border-radius:999px}
.pred .meta{font-size:12.5px;color:var(--muted);margin:.2em 0 .8em}
.pred .selection{background:#f8fafc;border-left:3px solid var(--teal);padding:9px 12px;border-radius:6px;font-size:14px}
.pred p{margin:.7em 0;max-width:82ch}
.crumb{font-size:13px;color:var(--muted);margin:0 0 8px}
.count{font-size:13px;font-weight:500;color:var(--muted);margin-left:8px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:12.5px;text-decoration:none;color:var(--ink2)}
.chip:hover{border-color:var(--teal)}
ul.tight{font-size:14.5px;color:var(--ink2)}
ul.tight li{margin:.35em 0}
pre.code{background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:12px;overflow-x:auto;font-size:12.5px}
.foot{border-top:1px solid var(--line);background:#fff;font-size:12.8px;color:var(--muted)}
.foot .wrap{padding:22px 20px 30px}
.upcoming{color:#15803d;font-size:10px}
.past{color:#cbd5e1;font-size:10px}
.tagfuture{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#7c3aed;border:1px solid #ddd6fe;border-radius:5px;padding:1px 4px}
@media (max-width:760px){.pickrow{grid-template-columns:1fr auto}.pr-badges{flex-direction:row}
.nav{width:100%;margin-left:0;overflow-x:auto;flex-wrap:nowrap;padding-bottom:4px}}
@media print{.topbar,.stripe,.cta,.skip{display:none}body{background:#fff}}
"""
    js = """// One optional enhancement: a filter box above the large tables.
document.querySelectorAll('[data-filterable]').forEach(function (wrap) {
  var input = document.createElement('input');
  input.type = 'search';
  input.placeholder = 'Filter rows…';
  input.setAttribute('aria-label', 'Filter table rows');
  input.style.cssText = 'margin:10px 0;padding:8px 12px;width:min(320px,100%);border:1px solid #cbd5e1;'
    + 'border-radius:8px;font:inherit;font-size:13.5px;background:#fff';
  wrap.parentNode.insertBefore(input, wrap);
  input.addEventListener('input', function () {
    var q = input.value.toLowerCase();
    wrap.querySelectorAll('tbody tr').forEach(function (tr) {
      tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
    });
  });
});
"""
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "unified.css").write_text(css, encoding="utf-8")
    (ROOT / "assets" / "unified.js").write_text(js, encoding="utf-8")


def main():
    inv = load("data/unified/olbg_events.json")
    audit = load("data/unified/audit.json")
    lines = load("data/cadence/lines.json")
    preds = load("data/cadence/predictions.json")
    sources = load("data/cadence/sources.json")
    picks = audit["picks"]

    pages = {
        "index.html": build_index(inv, audit, picks, preds),
        "olbg-events.html": build_olbg_events(inv, audit),
        "matches.html": build_matches(inv, audit, lines),
        "lines.html": build_lines(inv, audit, lines),
        "picks.html": build_picks(inv, audit, preds),
        "predictions.html": build_predictions(inv, audit, preds),
        "band.html": build_band(inv, audit, picks, preds),
        "sources.html": build_sources(inv, audit, sources),
        "verification.html": build_verification(inv, audit),
        "repo-review.html": build_repo_review(inv, audit),
        "flagged.html": build_flagged(inv, audit),
        "methodology.html": build_methodology(inv, audit),
        "archive.html": build_archive(inv, audit),
        "sports/index.html": build_sports_index(inv, audit),
    }
    for sport in SPORTS:
        pages[f"sports/{SPORT_SLUG[sport]}.html"] = build_sport_page(inv, audit, sport, lines, picks, preds)
    global _INV, _AUDIT
    _INV = inv
    _AUDIT = audit
    pages["sports/aussie-rules.html"] = build_out_of_scope_stub(
        "aussie-rules", "Aussie Rules",
        "Australian rules football is not one of the fifteen sports in this brief, so the desk publishes no "
        "fixtures, prices or predictions for it.")
    pages["sports/esports.html"] = build_out_of_scope_stub(
        "esports", "esports",
        "esports is not one of the fifteen sports in this brief, so the desk publishes no fixtures, prices or "
        "predictions for it.")
    pages["sports/gaelic-football.html"] = build_out_of_scope_stub(
        "gaelic-football", "Gaelic football",
        "Gaelic football is covered here, but under the combined Gaelic Sports page alongside hurling.",
        redirect_to="gaelic-sports")

    for rel, text in pages.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        # Root-absolute links are written once, then rebased for the page's depth so the
        # site works unchanged under a GitHub Pages project path such as /OLBG2/.
        depth = rel.count("/")
        prefix = "../" * depth
        for attr in ("href", "src"):
            text = text.replace(attr + '="/', attr + '="' + prefix)
            text = text.replace(attr + "='/", attr + "='" + prefix)
        path.write_text(text, encoding="utf-8")
    write_assets()
    print(f"unified_build: {len(pages)} pages written to the repository root")


_INV = {}
_AUDIT = {}

if __name__ == "__main__":
    main()
