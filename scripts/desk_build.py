#!/usr/bin/env python3
"""Build the /desk/ static dashboard from the committed capture files."""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "desk")

SPORTS = [
    ("Golf", "golf"), ("Volleyball", "volleyball"), ("Rugby Union", "rugby-union"),
    ("Cricket", "cricket"), ("Snooker", "snooker"), ("Darts", "darts"),
    ("Baseball", "baseball"), ("Gaelic Sports", "gaelic-sports"), ("Greyhounds", "greyhounds"),
    ("Tennis", "tennis"), ("Motor Racing", "motor-racing"), ("Handball", "handball"),
    ("Ice Hockey", "ice-hockey"), ("Basketball", "basketball"), ("Rugby League", "rugby-league"),
]

CSS = """
:root{--ink:#152238;--muted:#5b6b82;--line:#dde3ec;--bg:#f5f7fa;--card:#fff;--accent:#1b4f8a;
--hi:#0f7b4f;--hi-bg:#e5f5ec;--med:#8a5a00;--med-bg:#fdf1d8;--low:#6b7280;--low-bg:#eef0f3;
--warn:#9b1c1c;--warn-bg:#fdeaea}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
header{background:#fff;border-bottom:1px solid var(--line);padding:18px 22px 12px}
header h1{margin:0 0 2px;font-size:22px;letter-spacing:-.2px}
header p{margin:0;color:var(--muted);font-size:13px}
nav{background:#fff;border-bottom:1px solid var(--line);padding:0 22px;overflow-x:auto;white-space:nowrap}
nav a{display:inline-block;padding:11px 13px;color:var(--muted);text-decoration:none;font-size:13.5px;font-weight:500;border-bottom:2px solid transparent}
nav a:hover{color:var(--accent)}
nav a.on{color:var(--accent);border-bottom-color:var(--accent)}
main{max-width:1280px;margin:0 auto;padding:22px}
h2{font-size:18px;margin:26px 0 8px}
h3{font-size:15px;margin:20px 0 6px}
p.lede{color:var(--muted);margin:6px 0 18px;max-width:900px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:8px 0 6px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.kpi b{display:block;font-size:26px;line-height:1.1}
.kpi span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
table{width:100%;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:13px}
table{border-collapse:collapse}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eef2f7;font-size:11.5px;text-transform:uppercase;letter-spacing:.35px;color:#3c4a5e;position:sticky;top:0}
tbody tr:nth-child(even){background:#fafbfd}
tbody tr:hover{background:#f1f6fc}
.scroll{overflow-x:auto;border-radius:10px}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.2px}
.hi{color:var(--hi);background:var(--hi-bg)}.med{color:var(--med);background:var(--med-bg)}
.low{color:var(--low);background:var(--low-bg)}.warn{color:var(--warn);background:var(--warn-bg)}
.ok{color:#0f5c8a;background:#e6f1fa}
.muted{color:var(--muted)}.num{text-align:right;font-variant-numeric:tabular-nums}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
ul.tight{margin:6px 0 0 18px;padding:0}ul.tight li{margin:3px 0}
footer{max-width:1280px;margin:30px auto 0;padding:18px 22px 40px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--line)}
.pred{border-left:3px solid var(--accent);padding:2px 0 2px 14px;margin:14px 0}
.pred h3{margin:0 0 4px;font-size:15px}
.pred .meta{color:var(--muted);font-size:12px;margin-bottom:6px}
.note{background:#fffbe8;border:1px solid #f0e2b6;border-radius:8px;padding:10px 12px;font-size:13px}
"""


def esc(x):
    return html.escape(str(x)) if x is not None else ""


def money(l):
    a = l["fair_american"]
    return f"+{a}" if a > 0 else str(a)


def pill(conf):
    return f'<span class="pill {conf}">{conf}</span>'


def page(title, active, body, subtitle="OLBG 15-sport desk · captured 23 October 2026", prefix=""):
    nav = [("index.html", "Overview"), ("matches.html", "Verified fixtures"),
           ("olbg.html", "OLBG event list"), ("lines.html", "Originated lines"),
           ("picks.html", "Top-5 picks"), ("predictions.html", "Predictions"),
           ("audit.html", "Repo audit"), ("flagged.html", "Flagged for review"),
           ("sources.html", "Sources"), ("methodology.html", "Methodology")]
    links = "".join(
        f'<a class="{"on" if href == active else ""}" href="{prefix}{href}">{esc(label)}</a>' for href, label in nav)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · OLBG2 desk</title>
<link rel="stylesheet" href="{prefix}assets/style.css"></head>
<body>
<header><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></header>
<nav>{links}</nav>
<main>{body}</main>
<footer>
Research, not betting advice. Every price on this desk is originated here; none is a bookmaker quote.
Selections carry a probability, not a guarantee. 18+.
Rows without a governing-body source are labelled and listed on
<a href="{prefix}flagged.html">Flagged for review</a>. Built from committed captures by
<code>scripts/desk_build.py</code>.
</footer></body></html>"""


def main():
    inv = json.load(open(os.path.join(ROOT, "data/olbgdesk/olbg_inventory.json")))
    inputs = json.load(open(os.path.join(ROOT, "data/olbgdesk/inputs.json")))
    lines = json.load(open(os.path.join(ROOT, "data/olbgdesk/lines.json")))["lines"]
    preds = json.load(open(os.path.join(ROOT, "data/olbgdesk/predictions.json")))["predictions"]
    flags = json.load(open(os.path.join(ROOT, "data/olbgdesk/flagged.json")))["flags"]
    rows = [dict(zip(inv["header"], r)) for r in inv["rows"]]
    fixtures = inputs["fixtures"]

    by_sport = {}
    for r in rows:
        by_sport.setdefault(r["sport"], []).append(r)
    lines_by_sport = {}
    for l in lines:
        lines_by_sport.setdefault(l["sport"], []).append(l)
    fx_by_sport = {}
    for f in fixtures:
        fx_by_sport.setdefault(f["sport"], []).append(f)

    highs = sorted([l for l in lines if l["confidence"] == "high"],
                   key=lambda x: (-x["p"], x["sport"]))
    picks = {}
    for sport, _ in SPORTS:
        pool = [l for l in lines_by_sport.get(sport, [])
                if l["market_type"] in ("Match Winner", "Race Winner")]
        picks[sport] = sorted(pool, key=lambda x: -x["p"])[:5]

    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "sports"), exist_ok=True)
    open(os.path.join(OUT, "assets/style.css"), "w").write(CSS)

    total_markets = len(lines)
    total_events = len(rows)
    covered = sum(1 for s, _ in SPORTS if by_sport.get(s))
    official_high = len([l for l in highs if l["basis"] == "official"])

    # ---------- index ----------
    kpis = f"""<div class="kpis">
<div class="kpi"><b>{total_events}</b><span>OLBG events listed</span></div>
<div class="kpi"><b>{covered}/15</b><span>sports with OLBG rows</span></div>
<div class="kpi"><b>{len(fixtures)}</b><span>governing-body fixtures</span></div>
<div class="kpi"><b>{total_markets}</b><span>originated markets</span></div>
<div class="kpi"><b>{len(highs)}</b><span>high-confidence picks</span></div>
<div class="kpi"><b>{len(preds)}</b><span>written predictions</span></div>
<div class="kpi"><b>{len(flags)}</b><span>flagged items</span></div>
</div>"""

    hrows = ""
    for l in highs:
        hrows += (f"<tr><td>{esc(l['sport'])}</td><td>{esc(l['fixture'])}</td>"
                  f"<td>{esc(l['market'])}</td><td><b>{esc(l['selection'])}</b></td>"
                  f"<td class='num'>{l['p']*100:.1f}%</td><td class='num'>{money(l)}</td>"
                  f"<td>{'yes' if l['in_band'] else 'no'}</td><td>{pill(l['confidence'])}</td>"
                  f"<td>{'official' if l['basis']=='official' else 'consensus only'}</td></tr>")
    high_table = f"""<div class="scroll"><table>
<thead><tr><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th><th>Probability</th>
<th>Fair price</th><th>In -250…+10000 band</th><th>Confidence</th><th>Evidence</th></tr></thead>
<tbody>{hrows}</tbody></table></div>"""

    cov = ""
    for sport, slug in SPORTS:
        n_ev = len(by_sport.get(sport, []))
        n_l = len(lines_by_sport.get(sport, []))
        n_f = len(fx_by_sport.get(sport, []))
        n_h = len([l for l in lines_by_sport.get(sport, []) if l["confidence"] == "high"])
        n_p = len([p for p in preds if p["sid"] in {l["sid"] for l in lines_by_sport.get(sport, [])}])
        n_off = len([l for l in lines_by_sport.get(sport, []) if l["basis"] == "official"])
        if sport == "Golf":
            state = '<span class="pill warn">no OLBG events</span>'
        elif n_off:
            state = '<span class="pill hi">priced from official inputs</span>'
        elif n_f and n_l:
            state = '<span class="pill med">fixtures confirmed; consensus prices</span>'
        elif n_l:
            state = '<span class="pill med">consensus prices only</span>'
        else:
            state = '<span class="pill low">no match market</span>'
        cov += (f"<tr><td><a href='sports/{slug}.html'>{esc(sport)}</a></td><td class='num'>{n_ev}</td>"
                f"<td class='num'>{n_f}</td><td class='num'>{n_l}</td><td class='num'>{n_h}</td>"
                f"<td class='num'>{n_p}</td><td>{state}</td></tr>")
    cov_table = f"""<div class="scroll"><table>
<thead><tr><th>Sport</th><th>OLBG events</th><th>Official fixtures</th><th>Markets originated</th>
<th>High-confidence</th><th>Predictions</th><th>Status</th></tr></thead><tbody>{cov}</tbody></table></div>"""

    fx_rows = ""
    for f in fixtures:
        n = len([l for l in lines if l["sid"] == f["sid"]])
        fx_rows += (f"<tr><td>{esc(f['sport'])}</td><td>{esc(f['comp'])}</td>"
                    f"<td>{esc(f['away'])} at {esc(f['home'])}</td><td>{esc(f['start_utc'])}</td>"
                    f"<td>{esc(f['venue'])}</td><td class='num'>{n}</td>"
                    f"<td><a href='{esc(f['src'])}'>official</a></td></tr>")
    fx_table = f"""<div class="scroll"><table>
<thead><tr><th>Sport</th><th>Competition</th><th>Fixture</th><th>Start (UTC)</th><th>Venue</th>
<th>Markets</th><th>Source</th></tr></thead><tbody>{fx_rows}</tbody></table></div>"""

    body = f"""
<p class="lede">This desk lists every event OLBG published on the fifteen requested sport hubs on
23 October 2026, re-states it with the governing body where an official page could be read, and
originates an independent fair price for all 173 markets. Confidence follows the brief: high means a
70% or better probability for the named selection. Evidence strength is a separate column, because a
crowd-derived number is not the same thing as one corroborated by a league.</p>
{kpis}
<div class="note"><b>Read this first.</b> {len(highs)} high-confidence picks exist, but only
{official_high} of them rest on a governing-body numeric input. Six written predictions cover the
Ice Hockey selections; the Darts and Baseball selections are published with their confidence and no
narrative, because no official numeric fact base for them was captured. The five-per-sport prediction
target is <b>not</b> met and is item F-12 on the review page.</div>

<h2>Executive summary — highest-confidence picks</h2>
<p class="lede">Ranked by probability. “In band” marks the brief's price filter, a fair American price
between −250 and +10000; that filter implies a probability ceiling of 71.43%, so a 78% favourite is a
high-confidence pick that sits <i>outside</i> the band by construction.</p>
{high_table}

<h2>Coverage by sport</h2>
{cov_table}

<h2>Governing-body fixtures on this board</h2>
<p class="lede">Ten fixtures were read first-hand from an official league page. Six NHL games carry a
full goals-based price; the URC and World Series rows are published unlined because the inputs needed
to price them did not render.</p>
{fx_table}

<h2>What is where</h2>
<div class="grid2">
<div class="card"><h3 style="margin-top:0">The 125-row OLBG list</h3>
<p class="muted">Every event on the fifteen hubs, with OLBG's displayed time, most-tipped market,
selection and tip split, and a link back to the event. Golf returned “No tips found.”</p>
<p><a href="olbg.html">Open the OLBG event list →</a></p></div>
<div class="card"><h3 style="margin-top:0">The price file</h3>
<p class="muted">173 markets: 48 NHL markets from club goal aggregates, 125 consensus markets from
OLBG's published tip splits. Each row shows probability, fair decimal, fair American and the basis.</p>
<p><a href="lines.html">Open originated lines →</a></p></div>
</div>
"""
    open(os.path.join(OUT, "index.html"), "w").write(page("OLBG 15-sport desk", "index.html", body))

    # ---------- OLBG inventory ----------
    per = {}
    orows = ""
    for r in sorted(rows, key=lambda x: (x["sport"], -(x["pct"] or 0))):
        url = (f"https://www.olbg.com/betting-tips/{r['sport'].replace(' ', '_')}/"
               f"{SPORT_ID_LOOKUP[r['sport']]}?event_id={r['event_id']}")
        seen = any(f["olbg"] == r["event"] for f in fixtures)
        badge = ("official fixture captured" if seen
                 else '<span class="pill low">not re-read</span>')
        orows += (f"<tr><td>{esc(r['sport'])}</td><td>{esc(r['event'])}</td>"
                  f"<td>{esc(r['time_display'])}</td><td>{esc(r['market'])}</td>"
                  f"<td>{esc(r['selection'])}</td><td class='num'>{r['tips']}/{r['total']}</td>"
                  f"<td class='num'>{r['pct']}%</td>"
                  f"<td><a href='{esc(url)}'>OLBG</a></td><td>{badge}</td></tr>")
        per[r["sport"]] = per.get(r["sport"], 0) + 1
    summary = ", ".join(f"{s} {n}" for s, n in sorted(per.items(), key=lambda x: -x[1]))
    body = f"""
<p class="lede">Read first-hand from each OLBG sport hub on 23 October 2026 between 16:20 and 16:30 UTC.
OLBG renders one row per event: the most-tipped market, the most-tipped selection, and the tip split on
that market. It does not render a price on the hub, and the event page's price field is blank too, so no
OLBG price appears anywhere in this repository. Displayed times are copied verbatim and are not treated
as UTC.</p>
<div class="card"><b>{total_events} events</b> — {esc(summary)}. Golf returned “No tips found.”</div>
<div class="scroll"><table>
<thead><tr><th>Sport</th><th>Event</th><th>OLBG displayed time</th><th>Market</th><th>Most-tipped selection</th>
<th>Tips</th><th>Share</th><th>Event</th><th>Governing body</th></tr></thead>
<tbody>{orows}</tbody></table></div>
<p class="muted" style="margin-top:12px">“Not re-read” means the event was listed by OLBG but no official
page for that specific fixture was captured in this window. It is a coverage statement, not a claim that
the fixture is wrong.</p>
"""
    open(os.path.join(OUT, "olbg.html"), "w").write(page("OLBG event list", "olbg.html", body))

    # ---------- fixtures ----------
    frows = ""
    for f in fixtures:
        fl = [l for l in lines if l["sid"] == f["sid"]]
        st = (f"{len(fl)} markets" if fl else '<span class="pill warn">unlined</span>')
        frows += (f"<tr><td>{esc(f['sport'])}</td><td>{esc(f['comp'])}</td>"
                  f"<td><b>{esc(f['away'])}</b> at <b>{esc(f['home'])}</b></td>"
                  f"<td>{esc(f['start_utc'])}</td><td>{esc(f['venue'])}</td><td>{st}</td>"
                  f"<td><a href='{esc(f['src'])}'>governing body</a></td></tr>")
    body = f"""
<p class="lede">A fixture enters this table only when its date, venue and teams were read on an official
league page in this session. Ten did. Everything else OLBG listed stays on the
<a href="olbg.html">OLBG list</a> and is flagged as not re-read.</p>
<div class="scroll"><table>
<thead><tr><th>Sport</th><th>Competition</th><th>Fixture</th><th>Start (UTC)</th><th>Venue</th>
<th>Board status</th><th>Source</th></tr></thead><tbody>{frows}</tbody></table></div>
<div class="card"><h3 style="margin-top:0">Why three of the ten are unlined</h3>
<ul class="tight">
<li><b>Cardiff v Sharks, Connacht v Zebre, Edinburgh v Lions</b> — the URC table renders client-side and
returned no numeric columns, so there are no points-for/points-against inputs to price from. Flag F-03.</li>
<li><b>Rays at Brewers</b> — the MLB standings capture returned the American League East block only.
Milwaukee's season totals were never read, so the World Series opener stays blank. Flag F-04.</li>
</ul></div>
"""
    open(os.path.join(OUT, "matches.html"), "w").write(page("Verified fixtures", "matches.html", body))

    # ---------- lines ----------
    lrows = ""
    for l in sorted(lines, key=lambda x: (x["sport"], x["fixture"], x["market"], -x["p"])):
        ev = ("official" if l["basis"] == "official" else '<span class="pill med">consensus</span>')
        lrows += (f"<tr><td>{esc(l['sport'])}</td><td>{esc(l['fixture'])}</td>"
                  f"<td>{esc(l['market'])}</td><td><b>{esc(l['selection'])}</b></td>"
                  f"<td class='num'>{l['p']*100:.1f}%</td><td class='num'>{l['fair_decimal']:.2f}</td>"
                  f"<td class='num'>{money(l)}</td><td>{'yes' if l['in_band'] else 'no'}</td>"
                  f"<td>{pill(l['confidence'])}</td><td>{ev}</td>"
                  f"<td><a href='{esc(l['src'])}'>source</a></td></tr>")
    body = f"""
<p class="lede">Every market originated on this board. A price is the inverse of the stated probability,
rounded to two decimals. “Official” rows come from the NHL goals model; “consensus” rows come from
OLBG's published tip split, shrunk toward 0.50 with a twelve-tip prior. The two bases are never blended
inside one price.</p>
<div class="kpis">
<div class="kpi"><b>{total_markets}</b><span>markets</span></div>
<div class="kpi"><b>{len([l for l in lines if l['basis']=='official'])}</b><span>official-input markets</span></div>
<div class="kpi"><b>{len([l for l in lines if l['basis']=='consensus'])}</b><span>consensus markets</span></div>
<div class="kpi"><b>{len([l for l in lines if l['in_band']])}</b><span>inside the price band</span></div>
</div>
<div class="scroll"><table>
<thead><tr><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th><th>Probability</th>
<th>Fair decimal</th><th>Fair American</th><th>Band</th><th>Confidence</th><th>Basis</th><th>Source</th>
</tr></thead><tbody>{lrows}</tbody></table></div>
"""
    open(os.path.join(OUT, "lines.html"), "w").write(page("Originated lines", "lines.html", body))

    # ---------- picks ----------
    blocks = ""
    for sport, slug in SPORTS:
        pl = picks.get(sport, [])
        if not pl:
            blocks += (f"<h3>{esc(sport)}</h3><div class='note'>No match-winner market was captured "
                       f"for this sport, so no top-five can be listed. See the sport page.</div>")
            continue
        rws = ""
        for i, l in enumerate(pl, 1):
            rws += (f"<tr><td class='num'>{i}</td><td>{esc(l['fixture'])}</td>"
                    f"<td><b>{esc(l['selection'])}</b></td><td class='num'>{l['p']*100:.1f}%</td>"
                    f"<td class='num'>{money(l)}</td><td>{'yes' if l['in_band'] else 'no'}</td>"
                    f"<td>{pill(l['confidence'])}</td><td>{'official' if l['basis']=='official' else 'consensus'}</td></tr>")
        blocks += f"""<h3>{esc(sport)} <span class="muted" style="font-weight:400">— {len(pl)} of 5</span></h3>
<div class="scroll"><table><thead><tr><th>#</th><th>Fixture</th><th>Selection</th><th>Probability</th>
<th>Fair price</th><th>Band</th><th>Confidence</th><th>Evidence</th></tr></thead><tbody>{rws}</tbody></table></div>"""
    body = f"""
<p class="lede">The five highest-probability match-winner selections in each sport, taken from the price
file. Where a sport lists fewer than five events, the table is shorter and says so. No selection is
promoted to fill a quota.</p>
{blocks}
"""
    open(os.path.join(OUT, "picks.html"), "w").write(page("Top-5 picks by sport", "picks.html", body))

    # ---------- predictions ----------
    pblocks = ""
    for p in preds:
        pblocks += f"""<div class="pred">
<h3>{esc(p['selection'])} — {esc(p['market'])} — {esc(p['match'])}</h3>
<div class="meta">{esc(p['start_utc'])} · {p['words']} words · sources:
{', '.join(f"<a href='{esc(u)}'>official</a>" for u in p['sources'])}</div>
<p>{esc(p['text'])}</p>
<div class="muted" style="font-size:12px">Figures used: {esc('; '.join(p['facts']))}</div>
</div>"""
    withheld = [l for l in highs if l["basis"] != "official"]
    wrows = "".join(f"<tr><td>{esc(l['sport'])}</td><td>{esc(l['fixture'])}</td>"
                    f"<td>{esc(l['selection'])}</td><td class='num'>{l['p']*100:.1f}%</td>"
                    f"<td>{pill(l['confidence'])}</td><td>no official numeric fact base captured</td></tr>"
                    for l in withheld)
    body = f"""
<p class="lede">Six predictions, one per high-confidence Ice Hockey selection, each at least 30 words,
each opening differently, and each built only from figures read on the NHL's own statistics and score
feeds. No injury sentence appears anywhere: no official injury report was captured, and a blank is
preferable to a guess.</p>
{pblocks}
<h2>High-confidence selections without a written prediction</h2>
<div class="scroll"><table><thead><tr><th>Sport</th><th>Fixture</th><th>Selection</th><th>Probability</th>
<th>Confidence</th><th>Why there is no paragraph</th></tr></thead><tbody>{wrows}</tbody></table></div>
"""
    open(os.path.join(OUT, "predictions.html"), "w").write(page("Predictions", "predictions.html", body))

    # ---------- sport pages ----------
    notes = {
        "Golf": "OLBG returned “No tips found.” for Golf at capture time, so the sport has no events on this board. No official golf fixture was captured either.",
        "Rugby League": "OLBG lists only 2027 outright markets. There is no match fixture to price, so no match-winner row exists.",
        "Ice Hockey": "The only sport with governing-body numeric inputs on this board. Six NHL fixtures carry club goal aggregates and therefore a full price set: money line, puck line and match total.",
        "Rugby Union": "Three Round 4 fixtures were confirmed on the URC match centre. The league table did not render numbers, so the fixtures are unlined and the remaining eleven rows are OLBG-only consensus prices.",
        "Baseball": "World Series Game 1 was confirmed on the MLB schedule. Milwaukee's season totals were not captured, so the fixture is unlined; the consensus price is shown separately and labelled.",
    }
    for sport, slug in SPORTS:
        srows = sorted(by_sport.get(sport, []), key=lambda x: -(x["pct"] or 0))
        srow_html = "".join(
            f"<tr><td>{esc(r['event'])}</td><td>{esc(r['time_display'])}</td><td>{esc(r['market'])}</td>"
            f"<td>{esc(r['selection'])}</td><td class='num'>{r['tips']}/{r['total']}</td>"
            f"<td class='num'>{r['pct']}%</td><td><a href='https://www.olbg.com/betting-tips/"
            f"{esc(r['sport'].replace(' ', '_'))}/{SPORT_ID_LOOKUP[r['sport']]}?event_id={r['event_id']}'>OLBG</a></td></tr>"
            for r in srows)
        slines = sorted(lines_by_sport.get(sport, []), key=lambda x: -x["p"])
        sl_html = "".join(
            f"<tr><td>{esc(l['fixture'])}</td><td>{esc(l['market'])}</td><td><b>{esc(l['selection'])}</b></td>"
            f"<td class='num'>{l['p']*100:.1f}%</td><td class='num'>{money(l)}</td>"
            f"<td>{'yes' if l['in_band'] else 'no'}</td><td>{pill(l['confidence'])}</td>"
            f"<td>{'official' if l['basis']=='official' else 'consensus'}</td></tr>"
            for l in slines)
        sfx = fx_by_sport.get(sport, [])
        sfx_html = "".join(
            f"<tr><td>{esc(f['away'])} at {esc(f['home'])}</td><td>{esc(f['start_utc'])}</td>"
            f"<td>{esc(f['venue'])}</td><td><a href='{esc(f['src'])}'>governing body</a></td></tr>"
            for f in sfx)
        spreds = [p for p in preds if p["sid"] in {l["sid"] for l in slines}]
        spred_html = "".join(f"<div class='pred'><h3>{esc(p['selection'])} — {esc(p['match'])}</h3>"
                             f"<p>{esc(p['text'])}</p></div>" for p in spreds)
        note = notes.get(sport, "")
        body = f"""
<p class="lede">{esc(note)}</p>
<div class="kpis">
<div class="kpi"><b>{len(srows)}</b><span>OLBG events</span></div>
<div class="kpi"><b>{len(sfx)}</b><span>official fixtures</span></div>
<div class="kpi"><b>{len(slines)}</b><span>markets</span></div>
<div class="kpi"><b>{len([l for l in slines if l['confidence']=='high'])}</b><span>high confidence</span></div>
<div class="kpi"><b>{len(spreds)}</b><span>predictions</span></div>
</div>
<h2>OLBG events</h2>
{('<div class="scroll"><table><thead><tr><th>Event</th><th>Displayed time</th><th>Market</th><th>Most-tipped</th><th>Tips</th><th>Share</th><th>Link</th></tr></thead><tbody>' + srow_html + '</tbody></table></div>') if srows else '<div class="note">No OLBG event was listed for this sport at capture time.</div>'}
<h2>Governing-body fixtures</h2>
{('<div class="scroll"><table><thead><tr><th>Fixture</th><th>Start (UTC)</th><th>Venue</th><th>Source</th></tr></thead><tbody>' + sfx_html + '</tbody></table></div>') if sfx else '<div class="note">No official fixture was captured for this sport in this window.</div>'}
<h2>Originated markets</h2>
{('<div class="scroll"><table><thead><tr><th>Fixture</th><th>Market</th><th>Selection</th><th>Probability</th><th>Fair price</th><th>Band</th><th>Confidence</th><th>Basis</th></tr></thead><tbody>' + sl_html + '</tbody></table></div>') if slines else '<div class="note">No market was originated: there is no numeric input to price from.</div>'}
{('<h2>Predictions</h2>' + spred_html) if spred_html else ''}
"""
        open(os.path.join(OUT, "sports", f"{slug}.html"),
             "w").write(page(sport, "", body, subtitle="15-sport desk · 23 October 2026", prefix="../"))

    # ---------- flagged ----------
    frows = "".join(
        f"<tr><td><b>{esc(f['id'])}</b></td><td>{esc(f['sport'])}</td><td>{esc(f['finding'])}</td>"
        f"<td><a href='{esc(f['source'])}'>source</a></td></tr>" for f in flags)
    body = f"""
<p class="lede">Everything that could not be confirmed, everything left blank, and everything a reader
should weigh before using this board. None of these items blocks publication; all of them are published
so the gap is visible rather than smoothed over.</p>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Scope</th><th>Finding</th><th>Source</th></tr></thead>
<tbody>{frows}</tbody></table></div>
"""
    open(os.path.join(OUT, "flagged.html"), "w").write(page("Flagged for review", "flagged.html", body))

    # ---------- sources ----------
    srows = ""
    for k, v in inputs["official_sources"].items():
        srows += (f"<tr><td>{esc(k)}</td><td><a href='{esc(v['url'])}'>{esc(v['label'])}</a></td>"
                  f"<td>{esc(v['fields'])}</td><td>{esc(v.get('limit', '—'))}</td></tr>")
    body = f"""
<p class="lede">Every row on this desk resolves to one of these pages. Governing bodies are listed first;
OLBG is listed separately because it is the source of the event list and the tip split, not of the
fixtures or the prices.</p>
<h2>Governing-body sources</h2>
<div class="scroll"><table><thead><tr><th>Key</th><th>Page</th><th>Fields used</th><th>Capture limit</th></tr></thead>
<tbody>{srows}</tbody></table></div>
<h2>OLBG pages</h2>
<div class="scroll"><table><thead><tr><th>Sport</th><th>Hub</th><th>Events used</th></tr></thead><tbody>
{''.join(f"<tr><td>{esc(s)}</td><td><a href='https://www.olbg.com/betting-tips/{esc(s.replace(' ', '_'))}/{SPORT_ID_LOOKUP[s]}'>https://www.olbg.com/betting-tips/{esc(s.replace(' ', '_'))}/{SPORT_ID_LOOKUP[s]}</a></td><td class='num'>{len(by_sport.get(s, []))}</td></tr>" for s, _ in SPORTS)}
</tbody></table></div>
<div class="note">Routes that failed this session and are therefore <b>not</b> cited as evidence:
the ATP order-of-play page (HTTP 404), the NBA scoreboard JSON (HTTP 500) and the PDC tournament page
(cookie-consent shell only). They are listed on the review page as F-13, F-14 and F-15.</div>
"""
    open(os.path.join(OUT, "sources.html"), "w").write(page("Sources", "sources.html", body))

    # ---------- methodology ----------
    body = f"""
<p class="lede">How a row gets on this board, how a price is built, and what the labels mean. Nothing here
is a bookmaker quote.</p>
<div class="card"><h3 style="margin-top:0">1. Event discovery</h3>
<p>Each of the fifteen requested OLBG sport hubs was read once on 23 October 2026. Every rendered event
became a row: sport, event name, OLBG's displayed start, the most-tipped market, the most-tipped
selection, the tip split, and the OLBG event id. Golf returned “No tips found.” The hubs paginate, so the
list is what OLBG showed above the fold (F-09).</p></div>
<div class="card"><h3 style="margin-top:0">2. Fixture confirmation</h3>
<p>A fixture is promoted to the verified table only when its clubs, date and venue were read on a league
page. Ten qualified: six NHL games, three URC Round 4 fixtures and World Series Game 1. OLBG's displayed
time is never used as UTC; the leagues' own timestamps are.</p></div>
<div class="card"><h3 style="margin-top:0">3. Prices</h3>
<p><b>Official basis.</b> NHL goals are modelled as independent Poisson counts. Each club's goals for and
goals against per game are shrunk toward the league mean with an eight-game prior, the home side gets a
+0.10 goal edge, and the away side −0.10. The grid runs to twelve goals. A regulation tie is split 50/50
between the two clubs to represent overtime and the shootout. Money line, puck line ±1.5 and totals 5.5
and 6.5 are read off the same grid.</p>
<p><b>Consensus basis.</b> Where no official numeric input exists, the price comes from OLBG's published
tip split: the selection's share is shrunk toward 0.50 with a twelve-tip prior. A 1-in-1 tip split
therefore does not become a 98% probability. This is a crowd signal; it is labelled
<i>consensus</i> on every row and is never described as a market price.</p>
<p><b>Fair odds</b> are 1/p rounded to two decimals and converted to American. The brief's focus band is
−250 to +10000, i.e. decimal 1.40 to 101.00 inclusive.</p></div>
<div class="card"><h3 style="margin-top:0">4. Confidence</h3>
<p>High: probability of 70% or better. Medium: 65% to 69.9%. Low: below 65%. The band filter is a
separate column, because a fair price of −345 implies 77.5% and therefore cannot sit inside a band whose
short end is −250. Every such case is shown rather than dropped.</p></div>
<div class="card"><h3 style="margin-top:0">5. Predictions</h3>
<p>Written only for high-confidence selections that rest on a governing-body numeric input, and only from
figures in the stored capture. Each is at least 30 words, opens differently, and names the competition,
both clubs, their records, goals for and against, and the leading scorers where the feed supplied them.
No injury sentence appears because no official injury report was captured (F-11).</p></div>
<div class="card"><h3 style="margin-top:0">6. Blanks</h3>
<p>A value that could not be read is left blank. It is never inferred, back-filled from a similar club,
or copied from a tipster comment. The review page lists each blank and the route that failed.</p></div>
"""
    open(os.path.join(OUT, "methodology.html"), "w").write(page("Methodology", "methodology.html", body))

    # ---------- audit ----------
    body = """
<p class="lede">A line-by-line read of the merged repository, done on the same tree this desk was built
from. Findings are recorded, not silently fixed: shared files are owned by other sessions.</p>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Area</th><th>Finding</th><th>Evidence</th><th>Status</th></tr></thead><tbody>
<tr><td><b>A-01</b></td><td>COORDINATION.md</td><td>Three unresolved merge-conflict blocks remain in the
committed file: six marker lines (<code>&lt;&lt;&lt;&lt;&lt;&lt;&lt;</code>, <code>=======</code>,
<code>&gt;&gt;&gt;&gt;&gt;&gt;&gt;</code>) at lines 3216/3307, 3437/3549 and 3609/3628.</td>
<td><code>grep -n '^=======$\\|^&gt;&gt;&gt;&gt;&gt;&gt;&gt;' COORDINATION.md</code> → 6 hits</td>
<td><span class="pill warn">open</span></td></tr>
<tr><td><b>A-02</b></td><td>Scope</td><td>The repository now carries 34 published desks/layers
(<code>atlas, beacon, board, canon, command, current, daily, daily-audit, daily-picks, final, final-desk,
forward, fresh, hub, live, portal, pulse, reconcile, relay, site, slate, survey, vanguard, verified</code>
and others). Their row counts overlap and must not be summed.</td>
<td><code>ls -d */</code></td><td><span class="pill warn">open</span></td></tr>
<tr><td><b>A-03</b></td><td>README</td><td>README states the consolidated desk has 382 rows “across all 17
eligible sports”, while this brief names 15 sports and excludes Aussie Rules and eSports. The two scopes
coexist without a single stated mapping.</td>
<td>README.md, “Consolidated desk” row</td><td><span class="pill warn">open</span></td></tr>
<tr><td><b>A-04</b></td><td>Coverage claims</td><td>Earlier desks report “25 high-confidence picks” and
“85 in-band picks”. Those labels were produced by other models with their own gates; they are not
comparable with this desk's eight and must not be added to them.</td>
<td>README.md; vanguard/index.html</td><td><span class="pill med">disclosed</span></td></tr>
<tr><td><b>A-05</b></td><td>Tests</td><td>The full suite (467 tests) passes on this tree before any edit.</td>
<td><code>python3 -m unittest discover -s tests</code> → OK</td><td><span class="pill hi">clear</span></td></tr>
<tr><td><b>A-06</b></td><td>Shared files</td><td>Two sessions claim the same root integration files
(<code>33e9eee7</code> task F6 and <code>8226c94a</code>). This session therefore edits none of them and
logs its navigation request instead.</td>
<td>COORDINATION.md claims, 16:15–16:16 UTC</td><td><span class="pill med">handled by scope</span></td></tr>
</tbody></table></div>
<div class="note">Request to the root owner: add a <code>desk/</code> entry to the root navigation and a
<code>desk data/olbgdesk</code> drift path to the Pages workflow. This session does not touch
<code>index.html</code>, <code>scripts/build_site.py</code> or <code>.github/workflows/**</code>.</div>
"""
    open(os.path.join(OUT, "audit.html"), "w").write(page("Repository audit", "audit.html", body))

    # redirect-style index of sport pages
    print(f"built {len(os.listdir(os.path.join(OUT, 'sports')))} sport pages, "
          f"{len([f for f in os.listdir(OUT) if f.endswith('.html')])} top-level pages, "
          f"{len(highs)} high picks, {len(preds)} predictions")


SPORT_ID_LOOKUP = {"Tennis": 3, "Volleyball": 21, "Rugby Union": 9, "Cricket": 7, "Snooker": 8,
                   "Darts": 15, "Basketball": 4, "Ice Hockey": 13, "Handball": 20, "Greyhounds": 28,
                   "Gaelic Sports": 25, "Motor Racing": 14, "Baseball": 12, "Rugby League": 10, "Golf": 5}

if __name__ == "__main__":
    main()
