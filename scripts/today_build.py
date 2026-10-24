#!/usr/bin/env python3
"""Build the /today/ dashboard: one page per job, selections impossible to miss."""
from __future__ import annotations
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
SITE = ROOT / "today"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
SLUG = {s: s.lower().replace(" ", "-") for s in SPORTS}

NAV = [("Executive board", "index.html"), ("Picks", "picks.html"), ("Matches", "matches.html"),
       ("Our lines", "lines.html"), ("Predictions", "predictions.html"),
       ("By sport", "sports/index.html"), ("OLBG list", "olbg.html"),
       ("Flagged for review", "flagged.html"), ("Sources", "sources.html"),
       ("Method", "methodology.html")]


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def esc(x):
    return html.escape(str(x if x not in (None, "") else ""), quote=True)


def src(url, label="source"):
    return (f'<a class="src" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
            if str(url).startswith("http") else '<span class="muted">no link</span>')


def table(headers, rows, cls=""):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def pill(confidence, in_band):
    cls = {"high": "ok", "medium": "mid", "low": "low"}.get(confidence, "low")
    band = ('<span class="tag in">in band</span>' if in_band
            else '<span class="tag out">outside −250 floor</span>')
    return f'<span class="pill {cls}">{esc(confidence)}</span> {band}'


def pct(p):
    return f"{p * 100:.1f}%"


def usd(p):
    return f"+{p}" if p > 0 else f"{p}"


def shell(title, active, body, sub=False):
    prefix = "../" if sub else ""
    links = "".join(
        f'<a class="{"on" if label == active else ""}" href="{prefix}{path}">{esc(label)}</a>'
        for label, path in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · OLBG2 today's board</title>
<meta name="description" content="Dated OLBG listing capture, independently originated prices and written predictions for the 15 covered sports.">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<header class="top"><div class="wrap bar">
  <a class="brand" href="{prefix}index.html"><span class="dot"></span>OLBG2 <span class="sub">today's board</span></a>
  <nav class="nav">{links}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="foot"><div class="wrap">
<p><strong>Dated snapshot, not a live feed and not betting advice.</strong> OLBG listings were read on 24 October 2026 between 17:15 and 17:50 UTC.
Prices are originated here from official league inputs; they are not bookmaker quotes. Anything that could not be confirmed from an official source is left blank and listed on
<a href="{prefix}flagged.html">Flagged for review</a>. 18+.</p>
<p><a href="../index.html">Repository home</a> · <a href="https://www.olbg.com/betting-tips">OLBG sport hubs</a></p>
</div></footer></body></html>"""


def build():
    SITE.mkdir(exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)
    (SITE / "sports").mkdir(exist_ok=True)
    (SITE / "assets" / "style.css").write_text(CSS, encoding="utf-8")

    listings = load("olbg_listings")
    picks = load("picks")
    lines = load("lines")
    preds = load("predictions")
    flagged = load("flagged")
    sources = load("sources")
    fixtures = listings["fixtures"]

    pk = picks["picks"]
    pr = {p["fixture_id"]: p for p in preds["predictions"]}
    by_sport = flagged["sports"]
    status = {s["sport"]: s for s in by_sport}
    highs = [p for p in pk if p["confidence"] == "high"]
    in_band_high = [p for p in highs if p["in_band"]]
    capture = listings["capture_end_utc"]

    def pick_card(p, big=False):
        pred = pr.get(p["fixture_id"], {})
        headline = pred.get("headline", "")
        return f"""<article class="pickcard{' hero-pick' if big else ''}">
  <div class="pc-top"><span class="sport">{esc(p['sport'])}</span>{pill(p['confidence'], p['in_band'])}</div>
  <p class="match">{esc(p['home'])} <span class="vs">vs</span> {esc(p['away'])}</p>
  <p class="call"><span class="sel-label">PICK</span><span class="sel">{esc(p['selection'])}</span> <span class="mkt">{esc(p['market'])}</span></p>
  <p class="price">fair {esc(usd(p['fair_american']))} · {pct(p['probability'])}</p>
  {f'<p class="why">{esc(headline)}</p>' if headline else ''}
  <p class="links">{src(p['source_url'], 'official fixture')} · {src(p.get('olbg_event_url') or '', 'OLBG listing') if p.get('olbg_event_url') else '<span class="muted">no OLBG listing</span>'}</p>
</article>"""

    # ---------------------------------------------------------------- board
    hero_cards = "".join(pick_card(p, big=True) for p in pk[:3])
    pick_rows = [[
        esc(p["sport"]), f"{esc(p['home'])} <span class=\"vs\">vs</span> {esc(p['away'])}",
        f'<strong class="sel">{esc(p["selection"])}</strong>', esc(p["market"]),
        usd(p["fair_american"]), pct(p["probability"]), pill(p["confidence"], p["in_band"]),
        f'<a href="predictions.html#{esc(p["fixture_id"])}">read the preview</a>',
        (src(p["olbg_event_url"], "OLBG") if p.get("olbg_event_url") else '<span class="muted">—</span>')
        + " " + src(p["source_url"], "official"),
    ] for p in pk]

    sport_rows = [[
        f'<a href="sports/{SLUG[s["sport"]]}.html">{esc(s["sport"])}</a>',
        s["listings"], s["fixtures"], s["picks"], s["previews"],
        esc(s["status"]) if s["status"] else '<span class="ok-text">covered from official league data</span>',
        src(s["hub_url"], "OLBG hub"),
    ] for s in sorted(by_sport, key=lambda r: (-r["picks"], -r["listings"], r["sport"]))]

    board = f"""
<section class="hero">
  <p class="eyebrow">Saturday 24 October 2026 · listings read {esc(listings['capture_utc'])}–{esc(capture)} UTC</p>
  <h1>Today's board: the picks first, everything else underneath.</h1>
  <p class="lede">{len(pk)} written picks across {len({p['sport'] for p in pk})} sports, {len(fixtures)} officially confirmed fixtures,
  {len(lines['lines'])} prices we originated ourselves, and {len(listings['listings'])} OLBG listings across all 15 covered sports.
  Every row links to the official source it came from, and every gap is listed rather than guessed.</p>
  <div class="cta">
    <a class="btn primary" href="picks.html">See all {len(pk)} picks →</a>
    <a class="btn" href="predictions.html">Read the written predictions</a>
    <a class="btn" href="flagged.html">What is still missing ({len(flagged['items'])})</a>
  </div>
</section>

<section class="block">
  <div class="sechead"><h2>Executive summary — today's strongest calls</h2><a href="picks.html">all picks →</a></div>
  <p class="sub">{len(highs)} picks grade high, {len(in_band_high)} of them inside the −250…+10000 band. The rest are graded medium and shown exactly as graded.</p>
  <div class="grid3">{hero_cards}</div>
</section>

<section class="block">
  <div class="sechead"><h2>Fifteen sports, one status table</h2><a href="sports/index.html">sport pages →</a></div>
  <p class="sub">"Listings" is what OLBG actually showed today. Where a sport has no pick, the reason is written in the row and expanded on the review page.</p>
  {table(["Sport", "OLBG listings", "Officially confirmed fixtures", "Picks", "Written previews", "Status / why blank", "Hub"], sport_rows)}
</section>

<section class="block">
  <div class="sechead"><h2>How this site is organised</h2></div>
  <div class="grid3">
    <a class="navcard" href="picks.html"><strong>1 · Picks</strong><span>The selection, the price we made, the confidence grade and the band test — one row per match.</span></a>
    <a class="navcard" href="predictions.html"><strong>2 · Predictions</strong><span>The full written preview for each pick, with the official facts listed underneath it.</span></a>
    <a class="navcard" href="matches.html"><strong>3 · Matches</strong><span>Every officially confirmed fixture with start time, venue and source link.</span></a>
    <a class="navcard" href="lines.html"><strong>4 · Our lines</strong><span>All {len(lines['lines'])} prices originated from official inputs, including totals.</span></a>
    <a class="navcard" href="olbg.html"><strong>5 · OLBG list</strong><span>The raw {len(listings['listings'])}-row capture per sport: event, displayed time, most-tipped selection, tip share.</span></a>
    <a class="navcard" href="flagged.html"><strong>6 · Flagged</strong><span>Everything unverified, blocked or contradictory, with the link that shows why.</span></a>
  </div>
</section>
"""
    (SITE / "index.html").write_text(shell("Executive board", "Executive board", board), encoding="utf-8")

    # ---------------------------------------------------------------- picks
    picks_body = f"""
<section class="hero small">
  <p class="eyebrow">Picks · ranked by our own probability</p>
  <h1>Every pick, one row each.</h1>
  <p class="lede">The bold green text is the selection. "Fair" is the price we originated from official league inputs; the confidence grade and the band test sit beside it.
  None of these prices is a bookmaker quote.</p>
</section>
<section class="block">
{table(["Sport", "Match", "Selection", "Market", "Our fair price", "Probability", "Confidence", "Preview", "Sources"], pick_rows)}
</section>
<section class="block">
  <h2>Why some picks are marked outside the band</h2>
  <p>−250 is an implied 71.43%, so a "70% or better" rule and a "−250 to +10000" rule only overlap between 70.00% and 71.43%.
  The New Jersey call is 73.6%, a fair −279. It is published as high confidence and marked outside the floor rather than repriced to fit.
  See <a href="flagged.html">Flagged for review</a>, item R1.</p>
</section>
"""
    (SITE / "picks.html").write_text(shell("Picks", "Picks", picks_body), encoding="utf-8")

    # ---------------------------------------------------------------- matches
    fix_rows = []
    picked = {p["fixture_id"]: p for p in pk}
    for f in sorted(fixtures, key=lambda r: (r["start_utc"], r["sport"])):
        p = picked.get(f["id"])
        state = ("pick published" if p else "fixture only — outside the selection cut-off")
        fix_rows.append([
            esc(f["sport"]), f"<strong>{esc(f['home'])}</strong> <span class=\"vs\">vs</span> {esc(f['away'])}",
            esc(f["competition"]), esc(f["venue"]), f["start_utc"].replace("T", " ").replace("Z", " UTC"),
            f"{esc(f['home_record'])} / {esc(f['away_record'])}",
            (f'<strong class="sel">{esc(p["selection"])}</strong>' if p else '<span class="muted">—</span>'),
            esc(state),
            src(f["source_url"], "official fixture"),
            (src(f["olbg_listed_selection"] and next((l["url"] for l in listings["listings"] if l["event_id"] == f["olbg_event_id"]), ""), "OLBG")
             if f.get("olbg_event_id") else '<span class="muted">not listed</span>'),
        ])
    matches_body = f"""
<section class="hero small">
  <p class="eyebrow">Matches · {len(fixtures)} confirmed by the league itself</p>
  <h1>Fixtures with a start time and a source.</h1>
  <p class="lede">Record strings are shown home / away exactly as the league feed published them. Anaheim at Philadelphia began before the selection cut-off, so it appears here without a pick.</p>
</section>
<section class="block">{table(["Sport", "Match", "Competition", "Venue", "Start (UTC)", "Record H / A", "Our pick", "State", "Official fixture", "OLBG"], fix_rows)}</section>
<section class="block"><h2>What is not here</h2>
<p>Ten of the fifteen sports have no confirmed fixture on this page because their official page could not be read or listed nothing. Each one is named, with the link that shows it, on <a href="flagged.html">Flagged for review</a>.</p></section>
"""
    (SITE / "matches.html").write_text(shell("Matches", "Matches", matches_body), encoding="utf-8")

    # ---------------------------------------------------------------- lines
    line_rows = []
    fix_by_id = {f["id"]: f for f in fixtures}
    for l in lines["lines"]:
        f = fix_by_id[l["fixture_id"]]
        market_implied = (f"{l['market_implied_home'] * 100:.1f}% home" if l.get("market_implied_home") is not None else "—")
        line_rows.append([
            esc(l["sport"]), f"{esc(f['home'])} <span class=\"vs\">vs</span> {esc(f['away'])}",
            esc(l["market"]), (f'<strong class="sel">{esc(l["selection"])}</strong>'),
            esc(l.get("line") if l.get("line") is not None else "—"),
            pct(l["probability"]), usd(l["fair_american"]), f"{l['fair_decimal']:.3f}",
            market_implied, src(l["source_url"], "input"),
        ])
    lines_body = f"""
<section class="hero small">
  <p class="eyebrow">Our lines · {len(lines['lines'])} prices</p>
  <h1>Prices we made, not prices we found.</h1>
  <p class="lede">Money lines are derived from the official record and a fixed home edge; the baseball totals come from each club's season runs per game.
  The market column is the league feed's own two-way price, de-vigged, and is shown only so you can see where we disagree.</p>
</section>
<section class="block">{table(["Sport", "Match", "Market", "Selection", "Line", "Probability", "Fair US", "Fair decimal", "League-feed implied", "Input"], line_rows)}</section>
<section class="block"><h2>Markets we did not price</h2>
<p>Handicaps and game totals were investigated for every confirmed fixture. NHL totals and puck lines need a goal distribution we did not capture in this window, so they are left blank rather than approximated.
The baseball total below is priced because both clubs' season runs scored and allowed were read from the league's own standings.</p></section>
"""
    (SITE / "lines.html").write_text(shell("Our lines", "Our lines", lines_body), encoding="utf-8")

    # ---------------------------------------------------------------- predictions
    cards = []
    for p in preds["predictions"]:
        facts = "".join(f'<li>{esc(f["claim"])} {src(f["source_url"], "source")}</li>' for f in p["facts"])
        cards.append(f"""<article class="pred" id="{esc(p['fixture_id'])}">
  <p class="eyebrow">{esc(p['sport'])} · {esc(p['competition'])} · starts {esc(p['start_utc'].replace('T', ' ').replace('Z', ' UTC'))}</p>
  <h3>{esc(p['headline'])}</h3>
  <p class="callbar"><span class="sel-label">PICK</span><span class="sel">{esc(p['selection'])}</span>
     <span class="mkt">{esc(p['market'])} · fair {usd(p['fair_american'])} · {pct(p['probability'])} · {esc(p['confidence'])}</span></p>
  <p class="match">{esc(p['home'])} <span class="vs">vs</span> {esc(p['away'])}</p>
  <p class="body">{esc(p['text'])}</p>
  <p class="muted">{p['word_count']} words · injuries: {esc(p['injuries_note'])}</p>
  <details><summary>The {len(p['facts'])} official facts behind this preview</summary><ul class="facts">{facts}</ul></details>
  <p class="links">{src(p['official_fixture_url'], 'official fixture')}{(' · ' + src(p['olbg_event_url'], 'OLBG listing')) if p.get('olbg_event_url') else ''}</p>
</article>""")
    preds_body = f"""
<section class="hero small">
  <p class="eyebrow">Predictions · {len(preds['predictions'])} write-ups, shortest {preds['min_words']} words</p>
  <h1>The reasoning, written per match.</h1>
  <p class="lede">Each preview states the selection in the green bar first, then the form, the numbers and the price. Every figure used in the prose appears in the fact list underneath, with its official link.</p>
</section>
<section class="block">{''.join(cards)}</section>
"""
    (SITE / "predictions.html").write_text(shell("Predictions", "Predictions", preds_body), encoding="utf-8")

    # ---------------------------------------------------------------- olbg list
    groups = {}
    for row in listings["listings"]:
        groups.setdefault(row["sport"], []).append(row)
    jumps = "".join(f'<a class="chip" href="#{SLUG[s]}">{esc(s)} ({len(groups.get(s, []))})</a>' for s in SPORTS)
    blocks = []
    for s in SPORTS:
        rows = groups.get(s, [])
        body = table(["Event as listed", "Competition", "Displayed time", "Market", "Most-tipped selection", "Tips", "Share", "Event id", "Link"],
                     [[esc(r["event"]), esc(r["competition"] or "—"), esc(r["displayed_time"]), esc(r["market"]),
                       f'<strong class="sel">{esc(r["selection"])}</strong>', esc(r["tips"]), f'{r["pct"]}%',
                       esc(r["event_id"]),
                       src(r["url"], "OLBG event")] for r in rows]) if rows else \
               '<p class="muted">No event was listed on this hub at capture.</p>'
        blocks.append(f'<section class="block" id="{SLUG[s]}"><div class="sechead"><h2>{esc(s)}</h2>'
                      f'{src(listings["hubs"][s]["url"], "hub")}</div>{body}</section>')
    olbg_body = f"""
<section class="hero small">
  <p class="eyebrow">OLBG list · {len(listings['listings'])} rows · {len(listings['hubs'])} hubs</p>
  <h1>What OLBG actually showed today.</h1>
  <p class="lede">One row per listed event: the most-tipped selection, how many tips backed it and the share of that market. Times are OLBG's own strings and are not UTC.
  The first page of each hub was read; every hub is paginated, so this is not a complete inventory.</p>
  <div class="chips">{jumps}</div>
</section>
{''.join(blocks)}
"""
    (SITE / "olbg.html").write_text(shell("OLBG list", "OLBG list", olbg_body), encoding="utf-8")

    # ---------------------------------------------------------------- sports index
    cards_sport = "".join(
        f'<a class="navcard" href="{SLUG[s["sport"]]}.html"><strong>{esc(s["sport"])}</strong>'
        f'<span>{s["listings"]} OLBG listings · {s["fixtures"]} official fixtures · {s["picks"]} picks · {s["previews"]} previews</span></a>'
        for s in by_sport)
    sports_index = f"""
<section class="hero small">
  <p class="eyebrow">By sport · the 15 you asked for</p>
  <h1>One page per sport.</h1>
  <p class="lede">Each sport page carries the same sections in the same order: status, picks, confirmed fixtures, our prices, written previews and the raw OLBG listing rows.</p>
</section>
<section class="block"><div class="grid3">{cards_sport}</div></section>
"""
    (SITE / "sports" / "index.html").write_text(shell("By sport", "By sport", sports_index, sub=True), encoding="utf-8")

    for s in SPORTS:
        meta = status[s]
        sp_picks = [p for p in pk if p["sport"] == s]
        sp_preds = [p for p in preds["predictions"] if p["sport"] == s]
        sp_fix = [f for f in fixtures if f["sport"] == s]
        sp_lines = [l for l in lines["lines"] if l["sport"] == s]
        sp_list = groups.get(s, [])
        sp_flags = [f for f in flagged["items"] if f["sport"] == s]
        pick_block = "".join(pick_card(p) for p in sp_picks) or '<p class="muted">No pick published for this sport today.</p>'
        pred_block = "".join(f'<article class="pred"><h3>{esc(p["headline"])}</h3>'
                             f'<p class="callbar"><span class="sel-label">PICK</span><span class="sel">{esc(p["selection"])}</span>'
                             f'<span class="mkt">fair {usd(p["fair_american"])} · {pct(p["probability"])}</span></p>'
                             f'<p class="body">{esc(p["text"])}</p></article>' for p in sp_preds)
        flag_block = table(["Code", "What happened", "Evidence"], [[esc(x["code"]), esc(x["detail"]), src(x["source"], "link")] for x in sp_flags]) if sp_flags else '<p class="muted">No review item for this sport.</p>'
        fix_block = table(["Match", "Venue", "Start (UTC)", "Record H / A", "Official source"],
                          [[f"{esc(f['home'])} <span class=\"vs\">vs</span> {esc(f['away'])}", esc(f["venue"]),
                            f["start_utc"].replace("T", " ").replace("Z", ""), f"{esc(f['home_record'])} / {esc(f['away_record'])}",
                            src(f["source_url"], "fixture")] for f in sp_fix]) if sp_fix else '<p class="muted">No officially confirmed fixture for this sport today.</p>'
        line_block = table(["Market", "Selection", "Line", "Probability", "Fair US", "Input"],
                           [[esc(l["market"]), esc(l["selection"]), esc(l.get("line") if l.get("line") is not None else "—"),
                             pct(l["probability"]), usd(l["fair_american"]), src(l["source_url"], "input")] for l in sp_lines]) if sp_lines else '<p class="muted">No price originated for this sport today.</p>'
        list_block = table(["Event as listed", "Displayed time", "Market", "Most-tipped", "Tips", "Link"],
                           [[esc(r["event"]), esc(r["displayed_time"]), esc(r["market"]), f'<strong class="sel">{esc(r["selection"])}</strong>', esc(r["tips"]), src(r["url"], "OLBG")] for r in sp_list]) if sp_list else '<p class="muted">Nothing listed on this hub at capture.</p>'
        body = f"""
<section class="hero small">
  <p class="eyebrow">{esc(s)} · {meta['listings']} OLBG listings · {meta['fixtures']} official fixtures</p>
  <h1>{esc(s)}</h1>
  <p class="lede">{esc(meta['status']) if meta['status'] else 'Fixtures and picks for this sport come from the official league feed named on each row.'}</p>
  <div class="cta"><a class="btn" href="../picks.html">All picks</a><a class="btn" href="../flagged.html">Review queue</a>{src(meta['hub_url'], 'OLBG hub')}</div>
</section>
<section class="block"><h2>Picks ({len(sp_picks)})</h2><div class="grid3">{pick_block}</div></section>
<section class="block"><h2>Written previews ({len(sp_preds)})</h2>{pred_block}</section>
<section class="block"><h2>Officially confirmed fixtures ({len(sp_fix)})</h2>{fix_block}</section>
<section class="block"><h2>Our prices ({len(sp_lines)})</h2>{line_block}</section>
<section class="block"><h2>OLBG listing rows ({len(sp_list)})</h2>{list_block}</section>
<section class="block"><h2>Review items ({len(sp_flags)})</h2>{flag_block}</section>
"""
        (SITE / "sports" / f"{SLUG[s]}.html").write_text(shell(s, "By sport", body, sub=True), encoding="utf-8")

    # ---------------------------------------------------------------- flagged
    flag_rows = [[esc(f["code"]), esc(f["sport"] or "all sports"), esc(f["detail"]), esc(f["needs"]), src(f["source"], "evidence")]
                 for f in flagged["items"]]
    flagged_body = f"""
<section class="hero small">
  <p class="eyebrow">Flagged for review · {len(flagged['items'])} items</p>
  <h1>What is missing, and the link that shows it.</h1>
  <p class="lede">Nothing here blocks the page. Each item is either a gap in today's listing, an official source that would not respond, or a rule in the brief that contradicts another rule.
  "Evidence" opens the exact page that was read.</p>
</section>
<section class="block">{table(["Code", "Sport", "What happened", "What would fix it", "Evidence"], flag_rows)}</section>
"""
    (SITE / "flagged.html").write_text(shell("Flagged for review", "Flagged for review", flagged_body), encoding="utf-8")

    # ---------------------------------------------------------------- sources
    src_rows = [[esc(s["label"]), src(s["url"], "open"), esc(s["read"]), f'<span class="tag {s["outcome"]}">{esc(s["outcome"])}</span>']
                for s in sources["sources"]]
    sources_body = f"""
<section class="hero small">
  <p class="eyebrow">Sources · {len(sources['sources'])} pages read on 24 October 2026</p>
  <h1>Where each number came from.</h1>
  <p class="lede">Read means the page returned readable content in this session; partial means only part of it was consumed; blocked means it did not return usable data, and that is why the related rows are blank.</p>
</section>
<section class="block">{table(["Source", "Link", "What was read", "Outcome"], src_rows)}</section>
"""
    (SITE / "sources.html").write_text(shell("Sources", "Sources", sources_body), encoding="utf-8")

    # ---------------------------------------------------------------- method
    method_body = f"""
<section class="hero small">
  <p class="eyebrow">Method</p>
  <h1>How a pick gets on this page.</h1>
</section>
<section class="block prose">
<h2>1 · Listing</h2>
<p>Each of the 15 sport hubs is read directly. The event, its displayed time, the most-tipped selection, the tip count and the tip share are copied verbatim into
<a href="olbg.html">the OLBG list</a>. OLBG publishes no odds on hub pages, so nothing here is copied from an OLBG price.</p>
<h2>2 · Official confirmation</h2>
<p>A fixture is only publishable once a governing body or league feed confirmed the teams and the start time. That is why 10 of the 15 sports show listings but no pick:
their official page either would not return data or was not reached in this capture. The evidence is on <a href="flagged.html">Flagged for review</a>.</p>
<h2>3 · Our line</h2>
<p>Strength comes from the official record: points percentage for the NHL, winning percentage for MLB. The home edge is a fixed 4.5 points (NHL) or 4.0 (MLB).
Probability = 0.5 + home edge + 0.85 × (home strength − away strength), clamped to 12–88%. The fair American price is the reciprocal of that probability.
For the baseball total, expected runs are the average of each side's season runs scored plus the opponent's runs allowed per game, and the over/under is a Poisson tail on that expectation.</p>
<h2>4 · Confidence and the band</h2>
<p>High is 65% or better, medium 55–65%, low below 55%. The band test checks only our own fair price against −250…+10000.
Because −250 is 71.43%, a "70% or better" rule and that band overlap only between 70.00% and 71.43%; the one pick above that overlap is published with its real price and marked outside the band.</p>
<h2>5 · The writing</h2>
<p>Every preview states the selection first, then form, numbers and price. Every figure in the prose appears in the fact list under that preview with its official link.
Injuries are stated only when an official report was read. None was available for this slate, so the injury line says so instead of guessing.</p>
<h2>6 · What is deliberately absent</h2>
<p>No price is labelled as available at a bookmaker. No fixture is invented to fill a five-per-sport quota. No value is inferred where a source was silent.</p>
</section>
"""
    (SITE / "methodology.html").write_text(shell("Method", "Method", method_body), encoding="utf-8")

    pages = len(list(SITE.rglob("*.html")))
    print(f"today_build: {pages} pages, {len(pk)} picks, {len(preds['predictions'])} previews, "
          f"{len(listings['listings'])} listing rows")


CSS = """
:root{--ink:#0f172a;--muted:#5b6478;--line:#e2e8f0;--bg:#f7f9fc;--card:#fff;--brand:#0f766e;--brand2:#14b8a6;--warn:#b45309;--high:#047857;}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
.top{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.bar{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:10px 18px}
.brand{font-weight:800;letter-spacing:.02em;color:var(--ink)}
.brand .dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--brand2);margin-right:6px}
.brand .sub{font-weight:500;color:var(--muted);font-size:.82rem}
.nav{display:flex;gap:4px;flex-wrap:wrap}
.nav a{font-size:.84rem;color:var(--muted);padding:6px 9px;border-radius:999px}
.nav a.on,.nav a:hover{background:#ecfdf5;color:#065f46;text-decoration:none}
main{padding:22px 0 50px}
.hero{background:linear-gradient(180deg,#fff,#f0fdfa);border:1px solid var(--line);border-radius:16px;padding:26px;margin-bottom:22px}
.hero.small{padding:20px}
.hero h1{margin:.25rem 0 .5rem;font-size:1.85rem;line-height:1.15}
.eyebrow{margin:0;font-size:.74rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--brand)}
.lede{color:var(--muted);max-width:74ch;margin:0}
.cta{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;align-items:center}
.btn{border:1px solid var(--line);background:#fff;color:var(--ink);padding:9px 14px;border-radius:10px;font-weight:600;font-size:.9rem}
.btn.primary{background:var(--brand);border-color:var(--brand);color:#fff}
.btn:hover{text-decoration:none;border-color:var(--brand2)}
.block{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:20px}
.sechead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.sechead h2{margin:0;font-size:1.15rem}
.sub{color:var(--muted);font-size:.9rem;margin:.4rem 0 14px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.pickcard{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fff;display:flex;flex-direction:column;gap:6px}
.pickcard.hero-pick{background:linear-gradient(180deg,#f0fdfa,#fff);border-color:#99f6e4}
.pc-top{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.sport{font-size:.74rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.match{margin:0;color:var(--muted);font-size:.9rem}
.vs{color:#94a3b8}
.pickcard .call,.callbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:2px 0}
.sel-label{background:#065f46;color:#fff;font-size:.66rem;font-weight:800;letter-spacing:.1em;padding:3px 7px;border-radius:6px}
.sel{font-weight:800;font-size:1.02rem;color:#065f46}
.hero-pick .sel{font-size:1.22rem}
.mkt{color:var(--muted);font-size:.82rem}
.price{margin:0;font-weight:700;font-size:.9rem}
.why{margin:0;font-size:.86rem;color:#334155}
.pill{font-size:.7rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:999px}
.pill.ok{background:#d1fae5;color:#065f46}
.pill.mid{background:#fef3c7;color:#92400e}
.pill.low{background:#e2e8f0;color:#334155}
.tag{font-size:.68rem;font-weight:700;padding:2px 7px;border-radius:999px;background:#eef2f7;color:#475569}
.tag.in{background:#dbeafe;color:#1e40af}.tag.out{background:#fee2e2;color:#991b1b}
.tag.used{background:#d1fae5;color:#065f46}.tag.partial{background:#fef3c7;color:#92400e}.tag.blocked{background:#fee2e2;color:#991b1b}
.links{margin:0;font-size:.78rem}
.src{font-size:.78rem}
.muted{color:var(--muted)}
.ok-text{color:#047857;font-weight:600}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:.85rem;background:#fff}
th,td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f5f9;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:#475569;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#f8fafc}
.navcard{display:flex;flex-direction:column;gap:4px;border:1px solid var(--line);border-radius:12px;padding:14px;background:#fff;color:var(--ink)}
.navcard:hover{border-color:var(--brand2);text-decoration:none}
.navcard span{color:var(--muted);font-size:.87rem}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.chip{font-size:.8rem;border:1px solid var(--line);border-radius:999px;padding:5px 11px;background:#fff;color:var(--ink)}
.pred{border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:16px;background:#fff}
.pred h3{margin:.3rem 0 .6rem;font-size:1.12rem}
.callbar{background:#ecfdf5;border:1px solid #a7f3d0;border-radius:10px;padding:9px 12px;margin:0 0 10px}
.pred .body{margin:.4rem 0 .8rem;max-width:82ch}
details summary{cursor:pointer;font-weight:600;font-size:.86rem;color:var(--brand)}
.facts{margin:.6rem 0 0;padding-left:18px;font-size:.84rem;color:#334155}
.facts li{margin-bottom:4px}
.prose h2{font-size:1.02rem;margin:1.2rem 0 .3rem}
.prose p{margin:.2rem 0;color:#334155;max-width:88ch}
.foot{border-top:1px solid var(--line);background:#fff;padding:18px 0;color:var(--muted);font-size:.8rem}
.foot p{max-width:100ch;margin:.3rem 0}
@media(max-width:640px){.hero h1{font-size:1.45rem}.nav{overflow-x:auto;flex-wrap:nowrap;padding-bottom:4px}}
"""

if __name__ == "__main__":
    build()
