#!/usr/bin/env python3
"""Build the static Executive desk from data/executive/*.json."""
from __future__ import annotations
import html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "executive"
SITE = ROOT / "executive"

SPORTS = ["Ice Hockey", "Basketball", "Motor Racing", "Tennis", "Golf", "Cricket", "Darts",
          "Snooker", "Volleyball", "Rugby Union", "Handball", "Gaelic Sports", "Greyhounds",
          "Baseball", "Rugby League"]
SLUG = {"Ice Hockey": "ice-hockey", "Basketball": "basketball", "Motor Racing": "motor-racing",
        "Tennis": "tennis", "Golf": "golf", "Cricket": "cricket", "Darts": "darts",
        "Snooker": "snooker", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
        "Handball": "handball", "Gaelic Sports": "gaelic-sports", "Greyhounds": "greyhounds",
        "Baseball": "baseball", "Rugby League": "rugby-league"}
NAV = [("Overview", "index.html"), ("Matches", "matches.html"), ("Our lines", "lines.html"),
       ("Picks", "picks.html"), ("Predictions", "predictions.html"),
       ("Sources", "sources.html"), ("Methodology", "methodology.html"),
       ("Flagged for Review", "flagged.html")]


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def esc(x):
    return html.escape(str(x or ""), quote=True)


def link(url, label="Official source"):
    if str(url).startswith("https://"):
        return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
    return '<span class="muted">No link</span>'


def cell(s):
    return f"<td>{s}</td>"


def table(headers, rows):
    h = "".join(f"<th>{esc(x)}</th>" for x in headers)
    body = "".join("<tr>" + "".join(cell(c) for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'


def shell(title, body, active="", sub=False):
    prefix = "../" if sub else ""
    nav = "".join(f'<a class="{"active" if label == active else ""}" href="{prefix}{path}">{label}</a>'
                  for label, path in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Executive OLBG desk</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body><header class="top"><a class="brand" href="{prefix}index.html">EXECUTIVE <span>OLBG desk</span></a><button class="nav-toggle" onclick="document.body.classList.toggle('nav-open')" aria-label="Toggle navigation">&#9776;</button><nav>{nav}</nav></header><main><div class="crumb">OLBG · 15 covered sports · evidence-first snapshot · 24 Oct 2026</div>{body}</main><footer><p>Research snapshot, not a live feed or a betting recommendation. Every row carries its official source; unresolved values are left blank and flagged rather than guessed.</p><p><a href="../index.html">Repository dashboard</a> · <a href="https://www.olbg.com/betting-tips">OLBG sport hubs</a></p></footer></body></html>'''


def source_for(keys, sources):
    out = []
    for k in keys:
        s = sources.get(k)
        if s:
            out.append(link(s["url"], s.get("label", "Official source").split(",")[0]))
    return " &middot; ".join(out) if out else '<span class="muted">No link</span>'


CSS = '''*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#142033;font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#086c82}a:hover{color:#06495a}.top{position:sticky;top:0;z-index:4;background:#10273b;color:#fff;padding:.75rem max(1rem,calc((100vw - 1240px)/2));display:flex;align-items:center;justify-content:space-between;gap:1rem;box-shadow:0 2px 12px #12283b20}.brand{font-weight:900;letter-spacing:.12em;color:#fff;text-decoration:none}.brand span{font-weight:500;letter-spacing:0;color:#bad2dc;margin-left:.65rem}nav{display:flex;flex-wrap:wrap;gap:.25rem}nav a{padding:.4rem .55rem;color:#dcebf0;text-decoration:none;border-radius:7px;font-size:.86rem}nav a:hover,nav a.active{background:#1f6375;color:white}.nav-toggle{display:none}main{max-width:1240px;margin:auto;padding:1rem 1.1rem 4rem}.crumb,.eyebrow{color:#527087;text-transform:uppercase;font-weight:750;letter-spacing:.1em;font-size:.75rem}.hero{padding:clamp(2rem,6vw,4.8rem);border-radius:24px;background:linear-gradient(120deg,#10273b,#1b6172);color:white;margin:1rem 0 1.25rem}.hero h1{font-size:clamp(2rem,5vw,4rem);line-height:1.08;max-width:850px;margin:.5rem 0 1rem}.hero .lede{color:#d4e8ec;max-width:780px;font-size:1.15rem}.hero .eyebrow{color:#8ce1d1}.actions{display:flex;gap:.7rem;flex-wrap:wrap}.button{display:inline-block;padding:.75rem 1rem;border:1px solid #a8d4dc;border-radius:9px;color:white;text-decoration:none}.button.primary{background:#79dac4;color:#10273b;border-color:#79dac4;font-weight:800}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin:1rem 0 2rem}.kpi,.sport-card{display:flex;flex-direction:column;text-decoration:none;background:white;padding:1rem;border:1px solid #dce4ec;border-radius:14px;color:#17283b;box-shadow:0 3px 10px #12283b07}.kpi span{color:#527087;font-size:.88rem}.kpi strong{font-size:2rem}.kpi small,.sport-card small{color:#64778a}.sport-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:.7rem}.sport-card:hover,.kpi:hover{border-color:#15859a;transform:translateY(-1px)}h1{font-size:2.2rem;line-height:1.15;margin:.5rem 0}.lede{color:#52677b;max-width:920px}.notice{margin:1.3rem 0;padding:1rem 1.2rem;background:#fff9e9;border-left:5px solid #e0a323;border-radius:8px;color:#4d4126}h2{margin-top:2rem;border-bottom:1px solid #dce4ec;padding-bottom:.45rem}.table-wrap{overflow:auto;background:white;border:1px solid #dce4ec;border-radius:12px;margin:1rem 0 2rem}table{border-collapse:collapse;width:100%;min-width:820px;font-size:.9rem}th,td{padding:.7rem .75rem;text-align:left;vertical-align:top;border-bottom:1px solid #e7edf2}th{background:#eaf1f5;color:#203a50;position:sticky;top:0}tr:last-child td{border-bottom:0}tr:hover td{background:#f8fbfc}.vs{color:#8091a2}.prediction{background:white;border:1px solid #dce4ec;border-radius:14px;margin:1rem 0;padding:1.1rem 1.3rem;box-shadow:0 3px 10px #12283b07}.prediction h3{margin:.3rem 0}.selection{font-weight:800;color:#145e6d}.source-list{display:flex;gap:.8rem;flex-wrap:wrap;font-size:.86rem}.muted,small{color:#738393}.badge{display:inline-block;padding:.05rem .45rem;border-radius:6px;background:#e7f3f1;color:#0c5a68;font-size:.78rem;font-weight:700}.badge.out{background:#fdecec;color:#9b2226}.badge.low{background:#eef1f4;color:#5b6b7c}footer{border-top:1px solid #dce4ec;text-align:center;padding:1.5rem;color:#687c8d;font-size:.86rem}pre{overflow:auto;background:#10273b;color:#d7f1ed;padding:1rem;border-radius:10px}@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}.sport-grid{grid-template-columns:repeat(3,1fr)}nav{display:none;position:absolute;top:100%;left:0;right:0;background:#10273b;padding:1rem}.nav-open nav{display:flex;flex-direction:column}.nav-toggle{display:block;background:none;color:white;border:0;font-size:1.4rem}}@media(max-width:520px){main{padding:.7rem .6rem 2rem}.sport-grid{grid-template-columns:repeat(2,1fr)}.kpi{padding:.8rem}.kpi strong{font-size:1.6rem}.brand span{display:block;margin:0;font-size:.8rem}.hero{border-radius:16px;padding:1.5rem}}'''


def build():
    SITE.mkdir(exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)
    (SITE / "sports").mkdir(exist_ok=True)
    fixtures = load("fixtures")["fixtures"]
    lines = load("lines")["lines"]
    picks = load("picks")["picks"]
    preds = load("predictions")["predictions"]
    flags = load("flagged")["items"]
    sources = {s["key"]: s for s in load("sources")["sources"]}

    by_sport = {}
    for m in fixtures:
        by_sport[m["sport"]] = by_sport.get(m["sport"], 0) + 1
    active_sports = [s for s in SPORTS]
    pred_count = {s: sum(1 for p in preds if p["sport"] == s) for s in SPORTS}

    high = [p for p in picks if p["confidence"] == "high"]
    focus = [p for p in picks if p["in_band"] and p["input_verified"] and p["confidence"] in ("high", "medium")]
    high_in_band = sum(1 for p in high if p["in_band"])

    hero = '''<section class="hero"><p class="eyebrow">Evidence-led · 15 sport categories · fair lines, not bookmaker quotes</p><h1>Executive desk: fixtures, our own lines, and the facts behind them.</h1><p class="lede">A dated snapshot of live sport on 24 October 2026. Every row links the official governing-body source read in this session; values that could not be confirmed are left blank and flagged, never invented.</p><div class="actions"><a class="button primary" href="matches.html">Explore fixtures</a><a class="button" href="flagged.html">Review limitations</a><a class="button" href="predictions.html">Read the picks</a></div></section>'''

    cards = [
        ("Priced fixtures", str(len(fixtures)),
         f"{sum(1 for m in fixtures if m['sport'] == 'Ice Hockey')} hockey, {sum(1 for m in fixtures if m['sport'] == 'Basketball')} basketball and more — all linked to official sources", "matches.html"),
        ("Originated lines", str(len(lines)),
         "fair American and decimal prices computed from stored probabilities", "lines.html"),
        ("High-confidence picks", str(len(high)),
         f"{len(focus)} verified picks price inside −250…+10000 at medium or high conviction", "picks.html"),
        ("Written previews", str(len(preds)),
         "unique previews, each tied to the official facts captured for its fixture", "predictions.html"),
    ]
    cardhtml = "".join(f'<a class="kpi" href="{href}"><span>{esc(label)}</span><strong>{esc(value)}</strong>'
                       f'<small>{esc(note)}</small></a>' for label, value, note, href in cards)

    sportcards = "".join(
        f'<a class="sport-card" href="sports/{SLUG[s]}.html"><strong>{esc(s)}</strong>'
        f'<span>{by_sport.get(s, 0)} priced fixtures</span>'
        f'<small>{pred_count.get(s, 0)} written previews</small></a>' for s in SPORTS)

    focus_rows = []
    for p in sorted(focus, key=lambda x: -x["fair_probability"]):
        m = next((x for x in fixtures if x["id"] == p["fixture_id"]), {})
        focus_rows.append([esc(p["sport"]), esc(p["match"]), esc(p["market"]), esc(p["selection"]),
                           str(p["fair_odds"]), f"{p['fair_probability']:.1%}", esc(p["confidence"]),
                           source_for(p["source_keys"], sources)])

    high_rows = []
    for p in sorted(high, key=lambda x: -x["fair_probability"]):
        band = '<span class="badge">in −250…+10000</span>' if p["in_band"] else '<span class="badge out">below −250</span>'
        high_rows.append([esc(p["sport"]), esc(p["match"]), esc(p["selection"]), str(p["fair_odds"]),
                          f"{p['fair_probability']:.1%}", esc(p["confidence"]), band,
                          source_for(p["source_keys"], sources)])

    summary = f'''<h2>Executive summary</h2>
<p>This desk prices <strong>{len(fixtures)} fixtures across {len(SPORTS)} sports</strong> for 24&ndash;26 October 2026 and selects one winner per fixture, graded low/medium/high conviction.
The priority list below is the verified-input selections that price inside the requested <strong>&minus;250 to +10000</strong> window at medium or high conviction — that is where the brief asks us to concentrate.
{high_in_band} of the {len(high)} high-conviction picks price inside that window; the remaining {len(high) - high_in_band} are stronger favourites whose fair price sits below &minus;250, so they are listed separately rather than dropped.</p>
{table(['Sport','Fixture','Market','Selection','Fair price (US)','Probability','Conviction','Official source'], focus_rows)}'''

    if high_rows:
        summary += f'''<h3>High-conviction picks (full list)</h3><p>Ranked by probability. Where the fair price is below &minus;250 the pick falls outside the requested window; it is shown for completeness, not as a recommendation.</p>{table(['Sport','Fixture','Selection','Fair price (US)','Probability','Conviction','Price window','Official source'], high_rows)}'''

    body = hero + f'<section class="kpis">{cardhtml}</section>' + summary + \
        '<h2>Browse by sport</h2><div class="sport-grid">' + sportcards + '</div>' + \
        '<section class="notice"><strong>Data freshness:</strong> every fixture, strength input and price in this desk was read live from the linked official sources on 24 October 2026. ' + \
        'Fair prices are analysis outputs derived from those inputs; they are not bookmaker quotes and are not calibrated to observed closing prices. ' + \
        'Where a governing body publishes no comparable strength table the value is left blank and flagged.</section>'
    (SITE / "index.html").write_text(shell("Overview", body, "Overview"), encoding="utf-8")

    # all fixtures
    mrows = []
    for m in sorted(fixtures, key=lambda x: (x["sport"], x["start_utc"])):
        sel = next((p["selection"] for p in picks if p["fixture_id"] == m["id"]), "—")
        conf = next((p["confidence"] for p in picks if p["fixture_id"] == m["id"]), "—")
        mrows.append([esc(m["sport"]), esc(m["match"]), esc(m["competition"]), esc(m["start_utc"]),
                      esc(m["market"]), esc(sel), esc(conf), source_for(m["source_keys"], sources)])
    (SITE / "matches.html").write_text(shell("Matches",
        '<h1>Official fixture ledger</h1><p class="lede">Each row links the official fixture source read for this snapshot. ' +
        '“Blank” means no official value was published for that field; it is never inferred.</p>' +
        table(['Sport', 'Fixture', 'Competition', 'Start (UTC)', 'Market', 'Selection', 'Conviction', 'Official source'], mrows),
        "Matches"), encoding="utf-8")

    lrows = []
    for r in lines:
        lv = '<span class="badge">verified input</span>' if r["input_verified"] else '<span class="badge low">default input</span>'
        lrows.append([esc(r["sport"]), esc(r["competition"]), esc(r["market"]), esc(r["selection"]),
                      f"{r['home_probability']:.1%} / {r['away_probability']:.1%}",
                      str(r["home_fair_odds"]), str(r["away_fair_odds"]),
                      str(r["fair_odds"]), f"{r['fair_decimal']:.3f}", esc(r["confidence"]), lv,
                      source_for(next((m["source_keys"] for m in fixtures if m["id"] == r["fixture_id"]), []), sources)])
    (SITE / "lines.html").write_text(shell("Our lines",
        '<h1>Independent fair-price ledger</h1><p class="lede">One line per priced fixture, recalculated from the stored strength inputs. ' +
        'Prices are reciprocal probabilities — not OLBG consensus and not a bookmaker offer.</p>' +
        table(['Sport','Competition','Market','Selection','Home / away probability','Home fair (US)','Away fair (US)','Pick fair (US)','Pick decimal','Conviction','Input','Official source'], lrows),
        "Our lines"), encoding="utf-8")

    prows = []
    for p in sorted(picks, key=lambda x: (x["sport"], -x["fair_probability"])):
        band = '<span class="badge">in band</span>' if p["in_band"] else '<span class="badge out">outside band</span>'
        iv = '<span class="badge">verified</span>' if p["input_verified"] else '<span class="badge low">default</span>'
        prows.append([esc(p["sport"]), esc(p["match"]), esc(p["market"]), esc(p["selection"]),
                      f"{p['fair_probability']:.1%}", str(p["fair_odds"]), esc(p["confidence"]), band, iv,
                      source_for(p["source_keys"], sources)])
    (SITE / "picks.html").write_text(shell("Picks",
        '<h1>Selections &amp; confidence</h1><p class="lede">One selection per priced fixture. Conviction is derived from the probability and the strength of the input; ' +
        'a default input can never claim high conviction. The price window is tested against our fair American price only.</p>' +
        table(['Sport','Fixture','Market','Selection','Probability','Fair price (US)','Conviction','−250…+10000','Input','Official source'], prows),
        "Picks"), encoding="utf-8")

    pred_html = []
    for sport in SPORTS:
        ps = [p for p in preds if p["sport"] == sport]
        if not ps:
            continue
        pred_html.append(f"<h2>{esc(sport)}</h2>")
        for p in ps:
            facts = " &middot; ".join(link(f.get("source_url", ""), esc(f.get("subject", "fact"))) for f in p.get("facts", []))
            pred_html.append(f'''<article class="prediction"><div class="eyebrow">{esc(p["sport"])} · {esc(p["confidence"])} · {p["fair_probability"]:.1%} · fair {p["fair_odds"]}</div><h3>{esc(p["headline"])}</h3><p class="selection">{esc(p["match"])} — {esc(p["market"])}</p><p>{esc(p["text"])}</p><div class="source-list">{facts} &middot; {link(p["official_fixture_url"], "Fixture source")}</div></article>''')
    (SITE / "predictions.html").write_text(shell("Predictions",
        '<h1>Written previews</h3><p class="lede">Unique previews for every priced fixture, written against the official facts captured for that fixture. ' +
        'Conviction is capped where the governing body publishes no strength input. Injury status is never inferred; check the linked record.</p>' +
        "".join(pred_html), "Predictions"), encoding="utf-8")

    vf = []
    vpath = DATA / "verify_findings.json"
    if vpath.exists():
        vf = load("verify_findings")["findings"]
    rows = [{"code": x.get("code"), "sport": x.get("sport"), "detail": x.get("detail"),
             "source": x.get("source", "")} for x in flags]
    rows += [{"code": y["title"], "sport": "Repository", "detail": y["detail"],
              "source": "https://github.com/buffedlizard55-lab/OLBG2"} for y in vf]
    frows = [[esc(r["code"]), esc(r["sport"]), esc(r["detail"]), link(r["source"], "Source / artifact")]
             for r in rows]
    (SITE / "flagged.html").write_text(shell("Flagged for Review",
        '<h1>Flagged for Review</h1><p class="lede">Known gaps and irregularities are published here rather than silently filled. ' +
        'A blank value is not a negative finding.</p>' +
        table(['Code','Scope','Finding','Source'], frows), "Flagged for Review"), encoding="utf-8")

    srows = []
    for k, s in sources.items():
        srows.append([esc(k), esc(s.get("label")), esc(s.get("domain")), link(s.get("url"), s.get("url"))])
    (SITE / "sources.html").write_text(shell("Sources",
        '<h1>Source register</h1><p class="lede">Official governing-body links read live on 24 October 2026. ' +
        'The cited pages are the audit trail; values remain dated to their capture.</p>' +
        table(['Key','Source','Domain','Link'], srows), "Sources"), encoding="utf-8")

    method = '''<h1>Methodology &amp; evidence limits</h1>
<h2>Coverage and freshness</h2><p>Sports in scope: Ice Hockey, Basketball, Motor Racing, Tennis, Golf, Cricket, Darts, Snooker, Volleyball, Rugby Union, Handball, Gaelic Sports, Greyhounds, Baseball and Rugby League — the exact 15 categories requested. Fixture pairings and numeric facts are captured live from official governing-body sources on 24 October 2026 and are not continuously refreshed.</p>
<h2>Fixture confirmation</h2><p>Every priced row carries the official source URL it was read from. Where a governing body publishes no comparable numeric table the value is left blank and flagged rather than filled from another sport's convention.</p>
<h2>Our own lines</h2><p>Each fixture carries two per-side strength inputs taken from the linked official source (NHL points percentage, NBA power-ranking slot, ATP/WST/PDC ranking, SuperLega round points, F1 championship points, OWGR position, and so on). Two-way probabilities are computed as p(home) = sigmoid(K·(s_home − s_away) + home_edge) with K = 3.0 and home_edge = 0.15; outright probabilities are the event-position estimates recorded in the fixture. Fair American and decimal prices are the reciprocals of those probabilities. No margin is added and no OLBG quote is used.</p>
<h2>Confidence</h2><p>Conviction is high at probability ≥ 0.70, medium at ≥ 0.60, low below 0.60. A fixture whose only strength input is a league-average default is forced to low, so an unmodelled matchup can never masquerade as a conviction call.</p>
<h2>The &minus;250 to +10000 window</h2><p>The requested band is tested against our fair American price. High-conviction picks in the window sit at probability 0.70–0.714; picks priced below &minus;250 are stronger favourites and are shown separately, not dropped.</p>
<h2>Previews</h2><p>Each preview is written uniquely from the captured facts. Where a sport has fewer than five priced fixtures on this date, the shortfall is flagged rather than padded with invented selections.</p>
<h2>Reproduce</h2><pre>python3 scripts/executive_seed.py\npython3 scripts/executive_model.py\npython3 scripts/executive_predictions.py\npython3 scripts/executive_build.py\npython3 scripts/executive_verify.py</pre>'''
    (SITE / "methodology.html").write_text(shell("Methodology", method, "Methodology"), encoding="utf-8")

    sportcards_sub = "".join(
        f'<a class="sport-card" href="{SLUG[s]}.html"><strong>{esc(s)}</strong>'
        f'<span>{by_sport.get(s, 0)} priced fixtures</span>'
        f'<small>{pred_count.get(s, 0)} written previews</small></a>' for s in SPORTS)
    (SITE / "sports" / "index.html").write_text(shell("Sports",
        '<h1>Sport categories</h1><div class="sport-grid">' + sportcards_sub, "Sports", sub=True), encoding="utf-8")

    for s in SPORTS:
        ms = [m for m in fixtures if m["sport"] == s]
        ps = [p for p in preds if p["sport"] == s]
        body = (f'<p><a href="../index.html">← Overview</a> · <a href="../sports/index.html">All sports</a></p><h1>{esc(s)}</h1>'
                f'<p class="lede">{len(ms)} priced fixtures · {len(ps)} written previews in this dated snapshot.</p>')
        if not ms:
            body += '<div class="notice"><strong>No live fixture on this date.</strong> ' + esc(
                next((x.get("detail") for x in flags if x.get("sport") == s and x.get("code") == "NO-LIVE-FIXTURE"), "")) + "</div>"
        body += '<h2>Fixtures and selections</h2>' + table(
            ['Fixture', 'Competition', 'Start (UTC)', 'Market', 'Selection', 'Conviction', 'Official source'],
            [[esc(m["match"]), esc(m["competition"]), esc(m["start_utc"]), esc(m["market"]),
              esc(next((p["selection"] for p in picks if p["fixture_id"] == m["id"]), "—")),
              esc(next((p["confidence"] for p in picks if p["fixture_id"] == m["id"]), "—")),
              source_for(m["source_keys"], sources)] for m in ms])
        if ps:
            body += '<h2>Previews</h2>' + "".join(
                f'<article class="prediction"><h3>{esc(p["headline"])}</h3><p class="selection">{esc(p["selection"])} · {esc(p["confidence"])} · fair {p["fair_odds"]}</p><p>{esc(p["text"])}</p><p>{link(p["official_fixture_url"], "Official fixture")}</p></article>' for p in ps)
        else:
            body += '<div class="notice">No written preview is published for this category in this snapshot. See Flagged for Review for the reason.</div>'
        body += '<p><a href="../lines.html">All market lines</a> · <a href="../flagged.html">Flagged for Review</a></p>'
        (SITE / "sports" / f"{SLUG[s]}.html").write_text(shell(s, body, sub=True), encoding="utf-8")

    (SITE / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    print(f"executive_build: {len(list(SITE.rglob('*.html')))} pages, {len(fixtures)} fixtures, "
          f"{len(lines)} lines, {len(picks)} picks, {len(preds)} previews")


if __name__ == "__main__":
    build()
