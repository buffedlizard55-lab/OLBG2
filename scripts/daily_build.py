"""Render the /daily/ desk from data/daily/*.json.

Stdlib only, deterministic. Every table row carries its official source link. Nothing
here computes a sporting value: the numbers were produced by daily_data.py from the
verified inputs recorded in that file.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "daily"
OUT = ROOT / "daily"

SPORT_NAMES = {
    "ice-hockey": "Ice Hockey", "rugby-union": "Rugby Union", "aussie-rules": "Aussie Rules",
    "rugby-league": "Rugby League", "basketball": "Basketball", "baseball": "Baseball",
    "cricket": "Cricket",
}
# Display names for every eligible sport, including those with no line this pass.
ALL_SPORTS = dict(SPORT_NAMES, **{
    "tennis": "Tennis", "golf": "Golf", "darts": "Darts", "snooker": "Snooker",
    "handball": "Handball", "volleyball": "Volleyball", "motor-racing": "Motor Racing",
    "gaelic-football": "Gaelic Football", "greyhounds": "Greyhounds", "esports": "eSports",
})

STYLE = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       margin: 0; background: #f6f7fb; color: #1b2430; line-height: 1.55; }
a { color: #0f5bd7; }
header.top { background: #0f172a; color: #fff; padding: 12px 22px; display: flex; flex-wrap: wrap;
              align-items: center; gap: 4px 18px; position: sticky; top: 0; z-index: 10; }
header.top .brand { font-weight: 700; font-size: 1.05rem; margin-right: 8px; }
header.top .brand span { color: #5eead4; }
header.top a { color: #cbd5e1; text-decoration: none; font-size: 0.9rem; }
header.top a:hover, header.top a.active { color: #fff; text-decoration: underline; }
main { max-width: 1180px; margin: 0 auto; padding: 24px 20px 40px; }
h1 { font-size: 1.65rem; margin: 0 0 6px; }
h2 { font-size: 1.15rem; margin: 30px 0 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }
h3 { font-size: 1rem; margin: 18px 0 6px; }
p.lede, p.note { color: #475569; max-width: 820px; }
.snapshot { color: #64748b; font-size: 0.86rem; margin-bottom: 14px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 16px 0; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px; }
.card .num { font-size: 1.5rem; font-weight: 700; color: #0f172a; }
.card .label { color: #64748b; font-size: 0.8rem; }
.notice { background: #fff7ed; border: 1px solid #fdba74; border-radius: 8px; padding: 11px 15px; margin: 14px 0; font-size: 0.92rem; }
.notice.info { background: #eff6ff; border-color: #93c5fd; }
.table-wrap { overflow-x: auto; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; margin: 10px 0 18px; }
table { border-collapse: collapse; width: 100%; font-size: 0.89rem; }
th, td { text-align: left; padding: 8px 11px; border-bottom: 1px solid #eef1f6; vertical-align: top; }
th { background: #f1f5f9; white-space: nowrap; }
tr:last-child td { border-bottom: none; }
td.num, th.num { text-align: right; white-space: nowrap; }
.badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 0.74rem; font-weight: 600; margin-right: 4px; }
.badge.high { background: #dcfce7; color: #166534; }
.badge.medium { background: #fef9c3; color: #854d0e; }
.badge.low { background: #e2e8f0; color: #475569; }
.badge.band { background: #dbeafe; color: #1e40af; }
.badge.outband { background: #f1f5f9; color: #64748b; }
.badge.gap { background: #fee2e2; color: #991b1b; }
.pred { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px 17px; margin: 0 0 13px; }
.pred h3 { margin: 0 0 4px; font-size: 1rem; }
.pred .meta { color: #64748b; font-size: 0.82rem; margin-bottom: 8px; }
.pred p { margin: 8px 0 0; }
.pred .sel { font-weight: 700; color: #0f172a; }
.src { font-size: 0.84rem; }
footer { max-width: 1180px; margin: 0 auto; padding: 20px; color: #94a3b8; font-size: 0.8rem; border-top: 1px solid #e2e8f0; }
code { background: #f1f5f9; padding: 1px 5px; border-radius: 4px; font-size: 0.85em; }
.sports { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 10px; }
.sports a { display: block; background: #fff; border: 1px solid #e2e8f0; border-radius: 9px; padding: 12px 14px;
            text-decoration: none; color: #0f172a; font-weight: 600; }
.sports a span { display: block; font-weight: 400; color: #64748b; font-size: 0.8rem; margin-top: 3px; }
"""

NAV = [
    ("index.html", "Dashboard"),
    ("matches.html", "All fixtures"),
    ("lines.html", "Originated prices"),
    ("picks.html", "Five-a-sport picks"),
    ("predictions.html", "Predictions"),
    ("sports/index.html", "Sports"),
    ("flagged.html", "Flagged for Review"),
    ("methodology.html", "Methodology"),
    ("sources.html", "Sources"),
]


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def chrome(active: str, depth: int = 0) -> str:
    prefix = "../" * depth
    link_bits = []
    for href, label in NAV:
        cls = ' class="active"' if href == active else ""
        link_bits.append(f'<a href="{prefix}{href}"{cls}>{escape(label)}</a>')
    links = "".join(link_bits)
    root = "../" * (depth + 1)
    return (f'<header class="top"><span class="brand">OLBG2 <span>/daily</span></span>{links}'
            f'<a href="{root}index.html">Other desks</a></header>')


def footer(depth: int = 0) -> str:
    prefix = "../" * depth
    return (f'<footer>Independent research, not betting advice. Prices are fair, no-margin model '
            f'prices derived from the verified inputs listed on each row &mdash; they are not bookmaker '
            f'quotes. Generated 2026-10-22 21:50 UTC by session arena/6b4da610-olbg2. '
            f'<a href="{prefix}flagged.html">Flagged for Review</a> &middot; '
            f'<a href="{prefix}methodology.html">Methodology</a> &middot; 18+</footer>')


def page(title: str, active: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{escape(title)} &middot; OLBG2 daily</title>'
            f'<link rel="stylesheet" href="{prefix}assets/style.css"></head><body>'
            f'{chrome(active, depth)}<main>{body}</main>{footer(depth)}</body></html>')


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def am(x: int) -> str:
    return f"+{x}" if x > 0 else str(x)


def conf_badge(c: str) -> str:
    return f'<span class="badge {c}">{c}</span>'


def band_badge(in_band: bool) -> str:
    return ('<span class="badge band">in band</span>' if in_band
            else '<span class="badge outband">outside band</span>')


def write(rel: str, html: str) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)


def build() -> None:
    matches_doc = load("matches.json")
    sel_doc = load("selections.json")
    picks_doc = load("picks.json")
    preds_doc = load("predictions.json")
    flags_doc = load("flagged.json")

    matches = matches_doc["matches"]
    counts = matches_doc["counts"]
    selections = sel_doc["selections"]
    picks = picks_doc["picks"]
    preds = preds_doc["predictions"]
    coverage = flags_doc["coverage"]
    m_by_id = {m["id"]: m for m in matches}

    write("assets/style.css", STYLE)

    # ---------------------------------------------------------------- dashboard
    cards = [
        (counts["matches"], "verified fixtures"),
        (counts["sports"], "sports covered"),
        (counts["selections"], "originated prices"),
        (counts["picks"], "five-a-sport picks"),
        (counts["picks_high"], "high confidence"),
        (counts["picks_high_in_band"], "high and in the -250/+10000 band"),
        (flags_doc["counts"]["total"], "open review items"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="num">{n}</div><div class="label">{escape(l)}</div></div>'
        for n, l in cards)

    cov_rows = "".join(
        f'<tr><td><a href="sports/{c["sport"]}.html">{escape(SPORT_NAMES[c["sport"]])}</a></td>'
        f'<td class="num">{c["fixtures"]}</td><td class="num">{c["picks"]}</td>'
        f'<td class="num">{c["high"]}</td><td class="num">{c["high_in_band"]}</td>'
        f'<td>{"met" if c["target_met"] else "short"} &mdash; {escape(c["note"])}</td></tr>'
        for c in coverage)

    pick_rows = "".join(
        f'<tr><td>{escape(SPORT_NAMES[p["sport"]])}</td>'
        f'<td>{escape(m_by_id[p["match_id"]]["home"])} v {escape(m_by_id[p["match_id"]]["away"])}<br>'
        f'<span class="snapshot">{escape(m_by_id[p["match_id"]]["competition"])}</span></td>'
        f'<td>{escape(p["market"])}</td><td><strong>{escape(p["selection"])}</strong></td>'
        f'<td class="num">{pct(p["probability"])}</td><td class="num">{am(p["fair_american"])}</td>'
        f'<td>{conf_badge(p["confidence"])}{band_badge(p["in_band"])}</td></tr>'
        for p in picks)

    uncovered = "".join(
        f'<tr><td>{escape(ALL_SPORTS.get(s["sport"], s["sport"]))}</td>'
        f'<td>{escape(s["reason"])}</td></tr>'
        for s in flags_doc["sports_not_covered"])

    body = f"""
<h1>Daily picks desk &mdash; 23 to 25 October 2026</h1>
<p class="snapshot">Snapshot 2026-10-22 21:50 UTC &middot; 38 fixtures across 7 sports &middot;
every row links the official page it was read from &middot; {counts['selections']} originated prices</p>
<p class="lede">A five-a-sport picks board for the next three days. Fixtures, records and table
positions were read from governing-body pages; the prices are ours, computed from those inputs by
one declared model. Ten of the seventeen eligible sports are not covered in this pass and each is
named, with its reason, on this page and on <a href="flagged.html">Flagged for Review</a>.</p>

<div class="notice"><strong>What this desk is not.</strong> It is not a live feed and not betting
advice. It is a dated snapshot: form figures are what the official pages said on 22 October, not
game-day state. Any value that could not be read on an official page is left out of the model and
listed as a review item rather than guessed.</div>

<div class="cards">{card_html}</div>

<h2>Coverage by sport</h2>
<p class="note">The brief asks for five picks per sport. Four sports clear it. Basketball covers
three fixtures with five priced selections; baseball has two World Series games and cricket one
tri-series match, so five distinct fixtures do not exist for them in this window.</p>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th class="num">Fixtures</th><th class="num">Picks</th>
<th class="num">High</th><th class="num">High &amp; in band</th><th>Five-pick target</th></tr></thead>
<tbody>{cov_rows}</tbody></table></div>

<h2>Five-a-sport picks</h2>
<p class="note">Each list is the five highest-ranked selections for that sport by one rule: clear a
70% model probability <em>and</em> price between -250 and +10000, then highest probability. Twelve of
the eighteen high-confidence selections fall outside the band because a 70% chance already prices at
-233, so the arithmetic leaves only a 70.0-71.4% overlap. Those picks are published at their true
price rather than being re-lined to fit.</p>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th>
<th class="num">Model</th><th class="num">Fair price</th><th>Label</th></tr></thead>
<tbody>{pick_rows}</tbody></table></div>

<h2>Sports with no line from this pass</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Reason recorded</th></tr></thead>
<tbody>{uncovered}</tbody></table></div>

<h2>Where to look next</h2>
<ul>
<li><a href="predictions.html">The {preds_doc['count']} written predictions</a> &mdash; every published
pick, with its verified facts and source link.</li>
<li><a href="matches.html">All {counts['matches']} fixtures</a> and <a href="lines.html">all
{counts['selections']} originated prices</a>.</li>
<li><a href="flagged.html">Flagged for Review</a> &mdash; {flags_doc['counts']['total']} items,
including {flags_doc['counts']['discrepancies']} conflicts between this session's fresh NHL read and
figures already published elsewhere in the repository.</li>
<li><a href="methodology.html">Methodology</a> and <a href="sources.html">source register</a>.</li>
</ul>
"""
    write("index.html", page("Dashboard", "index.html", body))

    # ---------------------------------------------------------------- fixtures
    rows = []
    for m in sorted(matches, key=lambda x: (x["start"], x["sport"])):
        rows.append(
            f'<tr><td class="num">{escape(m["date"])}<br><span class="snapshot">'
            f'{escape(m["start"][11:16])}Z</span></td>'
            f'<td>{escape(SPORT_NAMES[m["sport"]])}</td><td>{escape(m["competition"])}</td>'
            f'<td><strong>{escape(m["home"])}</strong> v <strong>{escape(m["away"])}</strong></td>'
            f'<td class="snapshot">{escape(m["home_summary"])}<br>{escape(m["away_summary"])}</td>'
            f'<td class="num">{len(m["markets"])}</td>'
            f'<td>{escape(m["pick"]["selection"])}<br>{conf_badge(m["pick"]["confidence"])}'
            f'{band_badge(m["pick"]["in_band"])}</td>'
            f'<td class="src"><a href="{escape(m["url"], quote=True)}">{escape(m["source_name"])}</a>'
            f'<br><span class="snapshot">{escape(m["source_check"])}</span></td></tr>')
    body = f"""
<h1>All {len(matches)} fixtures</h1>
<p class="lede">Every fixture this desk priced, with the official page it came from and the
inputs fed to the model. <em>Inherited</em> in the source column means the fixture or its inputs
came from the repository's 22 October capture rather than a page this session re-read; those rows
are also listed on the review page.</p>
<div class="table-wrap"><table>
<thead><tr><th class="num">Date (UTC)</th><th>Sport</th><th>Competition</th><th>Fixture</th>
<th>Verified inputs</th><th class="num">Markets</th><th>Top selection</th><th>Official source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""
    write("matches.html", page("All fixtures", "matches.html", body))

    # ---------------------------------------------------------------- prices
    rows = []
    for s in sorted(selections, key=lambda x: (x["sport"], x["match_id"], x["market"], -x["probability"])):
        m = m_by_id[s["match_id"]]
        rows.append(
            f'<tr><td>{escape(SPORT_NAMES[s["sport"]])}</td>'
            f'<td>{escape(m["home"])} v {escape(m["away"])}</td>'
            f'<td>{escape(s["market"])}{"" if s["line"] is None else " " + str(s["line"])}</td>'
            f'<td>{escape(s["selection"])}</td><td class="num">{pct(s["probability"])}</td>'
            f'<td class="num">{s["fair_decimal"]:.2f}</td><td class="num">{am(s["fair_american"])}</td>'
            f'<td>{conf_badge(s["confidence"])}{band_badge(s["in_band"])}</td>'
            f'<td class="src"><a href="{escape(m["url"], quote=True)}">source</a></td></tr>')
    body = f"""
<h1>All {len(selections)} originated prices</h1>
<p class="lede">Two-way markets only, priced as 1 / model probability with no margin added. Nine
hockey fixtures carry moneyline, puck line and two totals; rugby union adds two handicaps and two
totals; basketball carries moneyline, two handicaps and two totals; AFLW, rugby league, baseball and
cricket carry the moneyline alone, because no verified scoring input existed to set a line.</p>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th>
<th class="num">Model</th><th class="num">Fair dec.</th><th class="num">Fair US</th>
<th>Label</th><th>Source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
"""
    write("lines.html", page("Originated prices", "lines.html", body))

    # ---------------------------------------------------------------- picks
    by_sport: dict[str, list[dict]] = {}
    for p in picks:
        by_sport.setdefault(p["sport"], []).append(p)
    sections = []
    for sport in SPORT_NAMES:
        group = by_sport.get(sport, [])
        if not group:
            continue
        rows = "".join(
            f'<tr><td>#{i + 1}</td>'
            f'<td>{escape(m_by_id[p["match_id"]]["home"])} v '
            f'{escape(m_by_id[p["match_id"]]["away"])}<br>'
            f'<span class="snapshot">{escape(m_by_id[p["match_id"]]["date"])} &middot; '
            f'{escape(m_by_id[p["match_id"]]["competition"])}</span></td>'
            f'<td>{escape(p["market"])}</td><td><strong>{escape(p["selection"])}</strong></td>'
            f'<td class="num">{pct(p["probability"])}</td><td class="num">{am(p["fair_american"])}</td>'
            f'<td>{conf_badge(p["confidence"])}{band_badge(p["in_band"])}</td></tr>'
            for i, p in enumerate(group))
        sections.append(
            f'<h2>{escape(SPORT_NAMES[sport])} ({len(group)} picks)</h2>'
            f'<div class="table-wrap"><table><thead><tr><th>Rank</th><th>Fixture</th><th>Market</th>'
            f'<th>Selection</th><th class="num">Model</th><th class="num">Fair price</th>'
            f'<th>Label</th></tr></thead><tbody>{rows}</tbody></table></div>')
    body = f"""
<h1>Five-a-sport picks</h1>
<p class="lede">Ranked by the published rule: selections that clear 70% and sit inside the
-250 to +10000 band first, then by model probability. Where a sport has fewer than five fixtures in
the window the list uses additional markets on the same fixture, and that is stated on each sport
page.</p>
<div class="notice info"><strong>Read the label, not just the price.</strong> A high-confidence
selection priced at -400 has a 70%+ model chance but sits outside the focused band. Those are kept,
labelled and disclosed rather than dropped.</div>
{''.join(sections)}
"""
    write("picks.html", page("Five-a-sport picks", "picks.html", body))

    # ---------------------------------------------------------------- predictions
    cards_html = []
    for p in preds:
        cards_html.append(
            f'<article class="pred"><h3>{escape(p["matchup"])}</h3>'
            f'<div class="meta">{escape(SPORT_NAMES[p["sport"]])} &middot; '
            f'{escape(p["competition"])} &middot; {escape(p["start_utc"][:16].replace("T", " "))} UTC'
            f' &middot; {p["word_count"]} words</div>'
            f'<div><span class="sel">{escape(p["selection"])}</span> '
            f'({escape(p["market"])}) &middot; {pct(p["probability"])} &middot; fair '
            f'{am(p["fair_american"])} &middot; {conf_badge(p["confidence"])}{band_badge(p["in_band"])}</div>'
            f'<p>{escape(p["prediction"])}</p>'
            f'<p class="src">Source: <a href="{escape(p["source_url"], quote=True)}">'
            f'{escape(p["source_name"])}</a></p></article>')
    body = f"""
<h1>{len(preds)} written predictions</h1>
<p class="lede">One paragraph per published pick, between {preds_doc['min_words']} and 78 words.
Each names the selection and the market, states the form and season figures the model used, and
links the official page those figures were read from. No player-level claim appears unless an
official page was read for it, which is why these are team-level write-ups.</p>
<div class="notice">Predictions are the model's opinion expressed in prose. They are not guarantees
and they are not recommendations to stake money.</div>
{''.join(cards_html)}
"""
    write("predictions.html", page("Predictions", "predictions.html", body))

    # ---------------------------------------------------------------- sports index
    cards = "".join(
        f'<a href="{c["sport"]}.html">{escape(SPORT_NAMES[c["sport"]])}'
        f'<span>{c["fixtures"]} fixtures &middot; {c["picks"]} picks &middot; {c["high"]} high</span></a>'
        for c in coverage)
    gaps = "".join(
        f'<li><strong>{escape(ALL_SPORTS.get(s["sport"], s["sport"]))}</strong> &mdash; '
        f'{escape(s["reason"])}</li>' for s in flags_doc["sports_not_covered"])
    body = f"""
<h1>Sports</h1>
<p class="lede">Seven of the seventeen eligible OLBG sports carry a line from this pass. The other
ten are listed below with the reason they carry none, rather than being shown as empty tables.</p>
<div class="sports">{cards}</div>
<h2>Not covered in this pass</h2>
<ul>{gaps}</ul>
"""
    write("sports/index.html", page("Sports", "sports/index.html", body, depth=1))

    # ---------------------------------------------------------------- sport pages
    for c in coverage:
        sport = c["sport"]
        group = by_sport.get(sport, [])
        mrows = []
        for m in [x for x in matches if x["sport"] == sport]:
            pick = m["pick"]
            pred = next((p for p in preds if p["match_id"] == m["id"] and p["selection"] == pick["selection"]), None)
            mrows.append(
                f'<tr><td class="num">{escape(m["date"])}<br><span class="snapshot">'
                f'{escape(m["start"][11:16])}Z</span></td>'
                f'<td><strong>{escape(m["home"])}</strong> v <strong>{escape(m["away"])}</strong><br>'
                f'<span class="snapshot">{escape(m["competition"])}</span></td>'
                f'<td class="snapshot">{escape(m["home_summary"])}<br>{escape(m["away_summary"])}</td>'
                f'<td>{escape(pick["selection"])} <span class="snapshot">({escape(pick["market"])})</span><br>'
                f'{pct(pick["probability"])} &middot; {am(pick["fair_american"])} &middot; '
                f'{conf_badge(pick["confidence"])}{band_badge(pick["in_band"])}</td>'
                f'<td class="src"><a href="{escape(m["url"], quote=True)}">official page</a><br>'
                f'<span class="snapshot">{escape(m["source_check"])}</span></td></tr>')
        prows = "".join(
            f'<tr><td>{i + 1}</td><td>{escape(m_by_id[p["match_id"]]["home"])} v '
            f'{escape(m_by_id[p["match_id"]]["away"])}</td><td>{escape(p["market"])}</td>'
            f'<td><strong>{escape(p["selection"])}</strong></td>'
            f'<td class="num">{pct(p["probability"])}</td><td class="num">{am(p["fair_american"])}</td>'
            f'<td>{conf_badge(p["confidence"])}{band_badge(p["in_band"])}</td></tr>'
            for i, p in enumerate(group))
        preds_here = [p for p in preds if p["sport"] == sport]
        pblocks = "".join(
            f'<article class="pred"><h3>{escape(p["matchup"])}</h3>'
            f'<div class="meta">{escape(p["competition"])} &middot; {p["word_count"]} words</div>'
            f'<div><span class="sel">{escape(p["selection"])}</span> ({escape(p["market"])}) &middot; '
            f'{pct(p["probability"])} &middot; {conf_badge(p["confidence"])}{band_badge(p["in_band"])}</div>'
            f'<p>{escape(p["prediction"])}</p>'
            f'<p class="src">Source: <a href="{escape(p["source_url"], quote=True)}">'
            f'{escape(p["source_name"])}</a></p></article>'
            for p in preds_here)
        body = f"""
<h1>{escape(SPORT_NAMES[sport])}</h1>
<p class="snapshot">{c["fixtures"]} fixtures &middot; {c["picks"]} picks &middot; {c["high"]} high
confidence &middot; {c["high_in_band"]} high and in band</p>
<p class="lede">{escape(c["note"])}</p>
<h2>Fixtures</h2>
<div class="table-wrap"><table><thead><tr><th class="num">Date (UTC)</th><th>Fixture</th>
<th>Verified inputs</th><th>Top selection</th><th>Official source</th></tr></thead>
<tbody>{''.join(mrows)}</tbody></table></div>
<h2>Picks</h2>
<div class="table-wrap"><table><thead><tr><th>Rank</th><th>Fixture</th><th>Market</th>
<th>Selection</th><th class="num">Model</th><th class="num">Fair price</th><th>Label</th>
</tr></thead><tbody>{prows}</tbody></table></div>
<h2>Predictions</h2>
{pblocks or '<p class="note">No prediction was written for this sport in this pass.</p>'}
"""
        write(f"sports/{sport}.html", page(SPORT_NAMES[sport], "sports/index.html", body, depth=1))

    # ---------------------------------------------------------------- flagged
    gap_rows = "".join(
        f'<tr><td>{escape(ALL_SPORTS.get(s["sport"], s["sport"]))}</td>'
        f'<td>{escape(s["reason"])}</td></tr>' for s in flags_doc["sports_not_covered"])
    inh_rows = "".join(
        f'<tr><td>{escape(i["item"])}</td><td class="src">'
        f'<a href="{escape(i["source"], quote=True)}">official page</a></td>'
        f'<td>{escape(i["detail"])}</td></tr>' for i in flags_doc["inherited_inputs"])
    dis_rows = "".join(
        f'<tr><td>{escape(d["id"])}</td><td>{escape(d["team"])}</td><td>{escape(d["fixture"])}</td>'
        f'<td class="num">{escape(d["date"])}</td><td>{escape(d["published"])}</td>'
        f'<td>{escape(d["verified"])}</td><td>{escape(", ".join(d["fields"]))}</td>'
        f'<td class="src"><a href="{escape(d["source"], quote=True)}">nhl.com</a></td></tr>'
        for d in flags_doc["discrepancies"])
    gen_rows = "".join(
        f'<tr><td>{escape(g["item"])}</td><td>{escape(g["detail"])}</td></tr>'
        for g in flags_doc["general"])
    body = f"""
<h1>Flagged for Review</h1>
<p class="snapshot">{flags_doc["counts"]["total"]} open items &middot; generated 2026-10-22 21:50 UTC</p>
<p class="lede">Nothing on this page blocks publication: it is the list of what this pass did not
verify, what it took from an earlier capture, and where a fresh official read contradicts a figure
already published elsewhere in the repository.</p>

<h2>Sports with no line from this pass ({flags_doc["counts"]["coverage_gaps"]})</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Reason</th></tr></thead>
<tbody>{gap_rows}</tbody></table></div>

<h2>Inputs carried over rather than re-verified ({flags_doc["counts"]["inherited_inputs"]})</h2>
<div class="table-wrap"><table><thead><tr><th>Input</th><th>Official page</th><th>Status</th></tr></thead>
<tbody>{inh_rows}</tbody></table></div>

<h2>Conflicts with figures published elsewhere in the repository ({len(flags_doc["discrepancies"])})</h2>
<p class="note">Every row below compares a team line stored in <code>data/final/matches.json</code>
for the same fixture with the NHL standings page read on 22 October 2026. The model on this desk uses
the freshly read figure. The older figure is left in place on the other desk and is not edited here,
because those files belong to other sessions' scopes.</p>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Team</th><th>Fixture</th><th class="num">Date</th>
<th>Published elsewhere</th><th>Read this session</th><th>Differs on</th><th>Source</th></tr></thead>
<tbody>{dis_rows}</tbody></table></div>

<h2>Method and scope disclosures ({flags_doc["counts"]["general"]})</h2>
<div class="table-wrap"><table><thead><tr><th>Item</th><th>Detail</th></tr></thead>
<tbody>{gen_rows}</tbody></table></div>
"""
    write("flagged.html", page("Flagged for Review", "flagged.html", body))

    # ---------------------------------------------------------------- sources
    src_rows = "".join(
        f'<tr><td>{escape(s["name"])}</td><td class="src">'
        f'<a href="{escape(s["url"], quote=True)}">{escape(s["url"])}</a></td>'
        f'<td>{escape(s["checked"])}</td></tr>'
        for s in matches_doc["sources"].values())
    by_sport = {}
    for m in matches:
        by_sport.setdefault(m["sport"], set()).add(m["source_name"])
    use_rows = "".join(
        f'<tr><td>{escape(SPORT_NAMES[s])}</td><td>{escape("; ".join(sorted(v)))}</td>'
        f'<td class="num">{sum(1 for m in matches if m["sport"] == s)}</td></tr>'
        for s, v in sorted(by_sport.items()))
    body = f"""
<h1>Source register</h1>
<p class="lede">The official pages this desk read, what each was used for, and whether this session
fetched it or carried it over from the 22 October capture. "This session" means the page was fetched
on 2026-10-22 between roughly 21:00 and 21:45 UTC.</p>
<div class="table-wrap"><table><thead><tr><th>Source</th><th>URL</th><th>Checked</th></tr></thead>
<tbody>{src_rows}</tbody></table></div>
<h2>Sources by sport</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Source(s) used</th>
<th class="num">Fixtures</th></tr></thead><tbody>{use_rows}</tbody></table></div>
"""
    write("sources.html", page("Sources", "sources.html", body))

    # ---------------------------------------------------------------- methodology
    params = matches_doc["params"]
    body = f"""
<h1>Methodology</h1>
<p class="lede">One model, declared parameters, no bookmaker input. Everything below is reproducible
by running <code>python3 scripts/daily_data.py</code> and reading the JSON it writes.</p>

<h2>1. Scope</h2>
<p>The 17 eligible OLBG sports exclude soccer, boxing, UFC/MMA, American football, hurling, horse
racing, cycling and specials. This pass priced 7 of them. The remaining 10 are named on
<a href="flagged.html">Flagged for Review</a> with the reason no line was originated.</p>

<h2>2. Inputs</h2>
<p>Only figures read on a governing-body page are used: NHL standings (record, goals for, goals
against, point streak), MLB season records, the URC table (played, won, drawn, lost, points for,
points against), EuroLeague standings (games, record, points for and against), the NRL World Cup
pool positions, and the AFLW and ICC tables carried over from the 22 October capture. A team with no
verified input gets no line, and its fixture is not published on this desk.</p>

<h2>3. Model</h2>
<h3>Ice hockey</h3>
<p>Independent Poisson goals for each side, with expected goals blending each attack with the
opposing defence:
<code>&lambda;<sub>home</sub> = ((GF<sub>home</sub>/GP) + (GA<sub>away</sub>/GP)) / 2 &times;
{params['hockey_home_mult']}</code> and the mirror image for the visitors at
{params['hockey_away_mult']}. Moneyline includes overtime and a shootout
({params['hockey_tie_split_home']} split on ties), the puck line is P(margin &ge; 2), and the totals
are {params['hockey_totals'][0]} and {params['hockey_totals'][1]}.</p>
<h3>Baseball</h3>
<p>Log5 on the two season win percentages with a {params['baseball_home_log5_bonus']} home-field
adjustment. Moneyline only: the World Series games carry no verified run-scoring input here, so no
run line or total is offered.</p>
<h3>Rugby union</h3>
<p>Expected points from the URC table's points-for and points-against per game, multiplied by
{params['urc_expected_mult_home']} at home and {params['urc_expected_mult_away']} away. The margin
uses a normal distribution with &sigma; = {params['urc_margin_sd']}, totals with
&sigma; = {params['urc_total_sd']}, at the handicap lines {params['urc_handicap_lines']} and total
lines {params['urc_total_lines']}.</p>
<h3>Basketball</h3>
<p>The same expected-points construction from EuroLeague points for and against, with a
{params['basketball_home_edge']}-point home edge, &sigma; = {params['basketball_margin_sd']} for the
margin and {params['basketball_total_sd']} for totals, at handicaps
{params['basketball_handicap_lines']} and totals {params['basketball_total_lines']}.</p>
<h3>Aussie rules</h3>
<p>Ladder percentage, with {params['aflw_home_bonus_pct']} percentage points added to the home side;
the two adjusted percentages are normalised into a win probability. No margin or total market is
offered, because percentage alone does not give an absolute scoring level.</p>
<h3>Rugby league and cricket</h3>
<p>A logistic on the published rating difference (scale {params['rl_logistic_scale']} for rugby
league, {params['cricket_logistic_scale']} for cricket) with a small home bonus. Moneyline only.</p>

<h2>4. Prices, confidence and the band</h2>
<p>Prices are fair and margin-free: decimal = 1 / probability, American as published. Confidence is a
threshold on the model probability &mdash; high at {int(params['confidence_high'] * 100)}% or more,
medium at {int(params['confidence_medium'] * 100)}%, low below. The focus band is
{params['band_american_min']} to +{params['band_american_max']}. Because a 70% chance already prices
at -233, the overlap between "high confidence" and "inside the band" is only 70.0% to 71.4%; this desk
reports both facts separately instead of moving a line to manufacture compliance.</p>

<h2>5. Selection rule</h2>
<p>Top five per sport, ranked by: selections that clear 70% and sit in the band first; then by model
probability. Where a sport has fewer than five fixtures the list takes additional markets on the same
fixture and says so.</p>

<h2>6. Limits</h2>
<p>This is a dated snapshot, not a live feed. It ignores team news, injuries, rotations, weather,
travel and rest, and it does not compare its prices with any bookmaker. Two-way markets only. The
model has no measured out-of-sample performance, so no strike rate is claimed.</p>
"""
    write("methodology.html", page("Methodology", "methodology.html", body))

    print("built /daily:", len(list(OUT.rglob("*.html"))), "pages")


if __name__ == "__main__":
    build()
