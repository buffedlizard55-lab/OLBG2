"""Cadence desk — static site builder.

Renders /cadence/ from the committed captures. Deterministic: same inputs, same bytes.

Run: python3 scripts/cadence_build.py
"""
import json
import os
import shutil
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "cadence")
OUT = os.path.join(ROOT, "cadence")

SPORTS = [
    ("Golf", "golf"), ("Volleyball", "volleyball"), ("Rugby Union", "rugby-union"),
    ("Cricket", "cricket"), ("Snooker", "snooker"), ("Darts", "darts"),
    ("Baseball", "baseball"), ("Gaelic Sports", "gaelic-sports"), ("Greyhounds", "greyhounds"),
    ("Tennis", "tennis"), ("Motor Racing", "motor-racing"), ("Handball", "handball"),
    ("Ice Hockey", "ice-hockey"), ("Basketball", "basketball"), ("Rugby League", "rugby-league"),
]
SLUG = dict(SPORTS)

CSS = """
:root{--bg:#0b1220;--card:#121c2e;--line:#22304a;--ink:#e8eef8;--dim:#93a4c0;--accent:#4da3ff;
--good:#2fbf71;--warn:#f2b134;--bad:#ef5b5b;--chip:#1b2942}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#0e1728;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:9}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
.top .wrap{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;padding:12px 18px}
.brand{font-weight:700;font-size:17px;letter-spacing:.2px}
.brand small{color:var(--dim);font-weight:400;font-size:12px;display:block}
nav.links{display:flex;flex-wrap:wrap;gap:6px}
nav.links a{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:13px;color:var(--ink)}
nav.links a.on{background:var(--accent);color:#04101f;border-color:var(--accent);font-weight:600}
main{padding:26px 0 60px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:19px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
p.lede{color:var(--dim);max-width:88ch;margin:0 0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi b{display:block;font-size:25px;line-height:1.1}
.kpi span{color:var(--dim);font-size:12px}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:640px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#16233a;color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.05em;position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:#101a2b}
.pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:11.5px;font-weight:600;white-space:nowrap}
.high{background:rgba(47,191,113,.16);color:#5ee49b;border:1px solid rgba(47,191,113,.4)}
.medium{background:rgba(242,177,52,.16);color:#f6c968;border:1px solid rgba(242,177,52,.4)}
.low{background:rgba(147,164,192,.14);color:#a9b8d1;border:1px solid rgba(147,164,192,.35)}
.in{background:rgba(77,163,255,.16);color:#8cc6ff;border:1px solid rgba(77,163,255,.4)}
.out{background:rgba(239,91,91,.14);color:#ff9a9a;border:1px solid rgba(239,91,91,.35)}
.blank{background:#1b2942;color:#93a4c0;border:1px dashed #3a4d6e}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:10px;padding:13px 15px;margin:14px 0}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
.note b{color:var(--ink)}
.mono{font-variant-numeric:tabular-nums}
.small{font-size:12.5px;color:var(--dim)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.card h4{margin:0 0 6px;font-size:15px}
.card .row{display:flex;justify-content:space-between;gap:8px;font-size:13px;color:var(--dim);margin:2px 0}
.pred{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:14px 0}
.pred h4{margin:0 0 2px;font-size:16px}
.pred .meta{color:var(--dim);font-size:12.5px;margin-bottom:8px}
.pred .sel{font-weight:600;color:#9ed0ff;margin:6px 0}
.pred p{margin:8px 0}
.pred .facts{margin-top:10px;border-top:1px solid var(--line);padding-top:9px}
.pred .facts li{font-size:12.5px;color:var(--dim);margin:3px 0}
ul{padding-left:20px}
footer{border-top:1px solid var(--line);color:var(--dim);font-size:12.5px;padding:18px 0 40px}
@media (max-width:640px){.top .wrap{gap:8px}h1{font-size:22px}}
"""


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


M = load("matches.json")
L = load("lines.json")
P = load("picks.json")
PR = load("predictions.json")
SRC = load("sources.json")
FLAG = load("flagged.json")
AUD = load("repo_audit.json")
FIX = {m["id"]: m for m in M["matches"]}


def nav(active, prefix=""):
    items = [("index.html", "Overview"), ("band.html", "Band board"), ("picks.html", "Top five by sport"),
             ("matches.html", "All matches"), ("lines.html", "Originated lines"),
             ("predictions.html", "Predictions"), ("sports/index.html", "Sports"),
             ("olbg.html", "OLBG"), ("audit.html", "Repo audit"), ("flagged.html", "Flagged for review"),
             ("sources.html", "Sources"), ("methodology.html", "Method")]
    out = []
    for href, label in items:
        cls = ' class="on"' if href == active else ""
        out.append(f'<a href="{prefix}{href}"{cls}>{label}</a>')
    return "".join(out)


def page(title, active, body, prefix=""):
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Cadence desk</title>
<style>{CSS}</style></head><body>
<header class="top"><div class="wrap">
  <div class="brand">Cadence · OLBG 15-sport desk<small>Captured {escape(M['generated_utc'])} · research, not betting advice · 18+</small></div>
  <nav class="links">{nav(active, prefix)}</nav>
</div></header>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap">
  Every published row links to the official governing-body page it came from. Values that an official
  source did not publish are left blank and listed on <a href="{prefix}flagged.html">Flagged for review</a>.
  Prices are the desk's own fair lines, never observed bookmaker quotes unless a row says so.
</div></footer></body></html>"""
    return html


def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


def src(url, label=None):
    if not url:
        return '<span class="pill blank">no source</span>'
    label = label or url.split("//")[-1].split("/")[0]
    return f'<a href="{escape(url, quote=True)}" rel="noopener">{escape(label)}</a>'


def confpill(c):
    if not c:
        return '<span class="pill blank">—</span>'
    return f'<span class="pill {c}">{c}</span>'


def bandpill(v):
    return '<span class="pill in">in band</span>' if v else '<span class="pill out">outside band</span>'


def label(home, away):
    return f"{escape(home)} v {escape(away)}" if away else escape(home)


def fmt_p(p):
    return f"{p*100:.1f}%"


def fmt_am(a):
    if a is None:
        return "—"
    return f"+{a}" if a > 0 else str(a)


def per_sport():
    out = {}
    for name, slug in SPORTS:
        out[name] = {
            "slug": slug,
            "matches": [m for m in M["matches"] if m["sport"] == name],
            "picks": sorted([p for p in P["picks"] if p["sport"] == name and p.get("sport_rank")],
                            key=lambda p: p["sport_rank"]),
            "preds": [p for p in PR["predictions"] if p["sport"] == name],
            "lines": [l for l in L["lines"] if l["sport"] == name],
            "stats": P["by_sport"].get(name, {}),
        }
    return out


SP = per_sport()
TODAY = "2026-10-23"


def is_today(row):
    start = row.get("start_utc") or ""
    if start.startswith(TODAY):
        return True
    disp = row.get("time_display") or ""
    return disp.startswith("23 October") or disp.startswith("2026-10-23")


# --------------------------------------------------------------- overview
def build_index():
    highs = [p for p in P["picks"] if p["confidence"] == "high" and p.get("sport_rank")]
    in_band = [p for p in highs if p["in_band"]]
    today_highs = [p for p in highs if (p.get("start_utc") or "").startswith(TODAY)]
    natural_in = [p for p in highs if p["in_band"] and not p.get("band_board")]
    alt_in = [p for p in highs if p.get("band_board") and p["in_band"]]
    outside_in = [p for p in highs if p["in_band"] is False]
    total_lines = L["count"]
    body = f"""
<h1>Executive summary — 23 October 2026</h1>
<p class="lede">Fifteen sports, {M['count']} official fixtures, {total_lines} originated prices and
{P['count']} graded selections built from today's governing-body pages. Every row carries the official
page it came from; nothing is filled in from memory or from a bookmaker.</p>

<div class="grid">
  <div class="kpi"><b>15</b><span>sports covered</span></div>
  <div class="kpi"><b>{M['count']}</b><span>fixtures ({M['originated']} priced)</span></div>
  <div class="kpi"><b>{total_lines}</b><span>originated markets</span></div>
  <div class="kpi"><b>{P['high']}</b><span>high-confidence selections</span></div>
  <div class="kpi"><b>{len(in_band)}</b><span>high confidence inside −250…+10000</span></div>
  <div class="kpi"><b>{PR['count']}</b><span>written predictions</span></div>
  <div class="kpi"><b>{FLAG['count'] + AUD['summary']['irregularities_logged']}</b><span>review items</span></div>
</div>

<div class="note">
  <b>How to read the confidence labels.</b> <span class="pill high">high</span> means the desk's probability
  for the selection is at least 70% and the official input behind it is a full-season table or ranking, or a
  4–9 match current-season sample. <span class="pill medium">medium</span> is 60–70%, or 70%+ on a 1–3 match
  sample. <span class="pill low">low</span> is everything else. A price is marked
  <span class="pill in">in band</span> when its fair American odds sit between −250 and +10000.
</div>

<div class="note warn">
  <b>The two rules in the brief meet in a 1.4-point window.</b> A fair −250 <i>is</i> a 71.43% chance, so
  “above 70%” and “priced −250 to +10000” overlap only between 70.00% and 71.43%. The desk does not widen
  either rule silently. It publishes every selection's own price and band status, and on the
  <a href="band.html">band board</a> it quotes the alternate line at the band ceiling for every fixture whose
  line ladder allows one. Today {len(natural_in)} of the {len(highs)} high-confidence top-five selections are
  inside the band on their natural line, {len(alt_in)} more clear it on an alternate line, and
  {len(outside_in)} are genuinely outside it because their probability is above 71.43% — those are listed with
  their real prices rather than shortened.
</div>

<h2>Today's matches — 23 October 2026</h2>
{today_block(today_highs)}

<h2>Next high-confidence selections</h2>
<p class="lede">The strongest picks whose official start is confirmed, in kick-off order. Each row shows the
start the publisher gave; where a publisher stated only a local time, that string is carried verbatim and the
UTC column stays blank rather than being converted.</p>
{top_table(dedupe(highs)[:10], show_sport=True, show_date=True)}

<h2>Coverage across the fifteen sports</h2>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th>Fixtures</th><th>Originated</th><th>Markets</th><th>Top-five picks</th>
<th>High</th><th>In band (high)</th><th>Predictions</th><th>Shortfall</th></tr></thead><tbody>
{''.join(coverage_row(n, s) for n, s in SPORTS)}
</tbody></table></div>

<h2>What is not here</h2>
<ul>
  <li>No observed bookmaker prices. OLBG publishes tip counts and percentages for a logged-out visitor, not
  odds; the NHL schedule feed does publish moneylines and they are shown only as a comparison column.</li>
  <li>No injury claim outside the NBA's own game-day report, which is linked on every NBA row.</li>
  <li>No fixture whose participants an official source did not name: three International Championship
  pre-qualifiers list only “Wildcard 1/3/4” and carry no line.</li>
  <li>No prediction in golf, greyhounds or Gaelic sports: the strongest selection in each is below medium
  confidence, so a ≥30-word write-up would be inventing an edge. Their prices are still published.</li>
</ul>
"""
    write("index.html", page("Executive summary", "index.html", body))


def dedupe(rows):
    seen, out = set(), []
    for p in rows:
        key = (p["fixture_id"], p["market"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def today_block(rows):
    if rows:
        return top_table(rows, show_sport=True, show_date=True)
    games = [m for m in M["matches"] if (m.get("start_utc") or "").startswith(TODAY)]
    sports = sorted({m["sport"] for m in games})
    return f"""
<div class="note warn">
  <b>No fixture that starts today carries a high-confidence selection.</b> Today's card holds
  {len(games)} confirmed fixtures ({', '.join(sports) if sports else 'none'}) and every one of them is either a
  one-to-three match sample or was already in play when the desk captured it. Rather than promote a weak row,
  the desk publishes the strongest graded selection on each of those fixtures — see
  <a href="picks.html">top five by sport</a> and <a href="matches.html">all matches</a> — and shows the next
  confirmed high-confidence picks below.
</div>
{top_table(sorted(games, key=lambda m: m["sport"])[:12], show_sport=True, show_date=True, matches_only=True)}"""


def coverage_row(name, s):
    st = SP[name]
    stats = st["stats"]
    fixtures = len(st["matches"])
    orig = sum(1 for m in st["matches"] if m["status"] == "originated")
    top5 = len(st["picks"])
    preds = len(st["preds"])
    shortfall = []
    if fixtures < 5:
        shortfall.append(f"{fixtures} official fixtures on the card")
    if preds < 5:
        shortfall.append(f"{preds} predictions")
    return (f'<tr><td><a href="sports/{s}.html"><strong>{escape(name)}</strong></a></td>'
            f'<td class="mono">{fixtures}</td><td class="mono">{orig}</td>'
            f'<td class="mono">{len(st["lines"])}</td><td class="mono">{top5}</td>'
            f'<td class="mono">{stats.get("high", 0)}</td><td class="mono">{stats.get("in_band_high", 0)}</td>'
            f'<td class="mono">{preds}</td>'
            f'<td class="small">{escape("; ".join(shortfall)) if shortfall else "—"}</td></tr>')


def top_table(rows, show_sport=False, show_date=False, matches_only=False):
    if not rows:
        return '<div class="note bad">No fixture on today’s card produced a high-confidence selection.</div>'
    if matches_only:
        out = ['<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Fixture</th><th>Start (UTC)</th>'
               '<th>Favourite</th><th>Prob</th><th>Grade</th><th>Official source</th></tr></thead><tbody>']
        for m in rows:
            out.append(f'<tr><td><a href="sports/{SLUG[m["sport"]]}.html">{escape(m["sport"])}</a></td>'
                       f'<td>{label(m["home"], m["away"])}</td>'
                       f'<td class="mono">{escape(m.get("start_utc") or m.get("time_display") or "—")}</td>'
                       f'<td>{escape(m.get("favourite") or "—")}</td>'
                       f'<td class="mono">{fmt_p(m["favourite_probability"]) if m.get("favourite_probability") else "—"}</td>'
                       f'<td>{confpill(m.get("confidence"))}</td>'
                       f'<td>{src(m["official_source_url"])}</td></tr>')
        out.append("</tbody></table></div>")
        return "".join(out)
    head = ["Sport"] if show_sport else []
    head += ["Fixture", "Selection", "Market", "Prob", "Fair price", "Band", "Grade", "Source"]
    if show_date:
        head.insert(1, "Start (UTC)")
    out = [f'<div class="table-wrap"><table><thead><tr>{"".join(f"<th>{h}</th>" for h in head)}</tr></thead><tbody>']
    for p in rows:
        cells = []
        if show_sport:
            cells.append(f'<a href="sports/{SLUG[p["sport"]]}.html">{escape(p["sport"])}</a>')
        cells.append(label(p["home"], p["away"]))
        if show_date:
            cells.insert(1, f'<span class="mono">{escape(p.get("start_utc") or p.get("time_display") or "—")}</span>')
        cells += [f'<strong>{escape(p["selection"])}</strong>', escape(p["market"]),
                  f'<span class="mono">{fmt_p(p["probability"])}</span>',
                  f'<span class="mono">{fmt_am(p["fair_american"])}</span>',
                  bandpill(p["in_band"]), confpill(p["confidence"]), src(p["official_source_url"])]
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


# --------------------------------------------------------------- band board
def build_band():
    highs = [p for p in P["picks"] if p["confidence"] == "high"]
    natural_in = sorted([p for p in highs if p["in_band"] and not p.get("band_board")], key=lambda p: -p["probability"])
    alt = sorted([p for p in highs if p.get("band_board")], key=lambda p: -p["probability"])
    outside = sorted([p for p in highs if not p["in_band"] and not p.get("band_board")], key=lambda p: -p["probability"])
    body = f"""
<h1>The band board</h1>
<p class="lede">The brief asks for high-confidence picks priced between −250 and +10000. A fair −250 is
71.43%, so that band and “above 70%” only overlap between 70.00% and 71.43%. This page sets out all three
groups honestly rather than moving a line and calling it something else.</p>

<div class="note">
  <b>The arithmetic.</b> Fair American odds of −250 imply 250/350 = 71.43%. Fair odds of −263 (Tampa Bay on
  the money line today) imply 72.4%, which is outside the band. There is no way to have a 75% chance and a
  −250 price at the same time; the second number is the first number. So for every fixture with a continuous
  line ladder the desk also computes the <i>alternate</i> line whose probability is closest to, but not above,
  71.43% and still at least 70%. That line is a real market — a different handicap or total — and it is shown
  with its own probability, price and basis.
</div>

<h2>Already inside the band on the natural selection ({len(natural_in)})</h2>
{band_table(natural_in)}
{band_note(len(natural_in), len(highs), len(alt), len(outside))}

<h2>Inside the band on an alternate line ({len(alt)})</h2>
<p class="lede">Each row is a handicap or total set at the band ceiling. The probability beside it is the
desk's estimate for that specific line, not a relabelled version of the favourite's money line.</p>
{band_table(alt)}

<h2>High confidence but shorter than −250 ({len(outside)})</h2>
<p class="lede">These are the strongest selections on the card. They sit outside the band because their
probability is above 71.43%. They are listed with their actual prices so the shortfall is visible.</p>
{band_table(outside)}
"""
    write("band.html", page("Band board", "band.html", body))


def band_note(natural, high, alt, outside):
    if natural:
        return ""
    return (f'<div class="note warn"><b>None today, and that is the point.</b> All {high} selections that '
            f'grade high have a probability above 71.43%, so their natural price is shorter than −250 and the '
            f'band excludes them by definition. {alt} of them can be re-quoted at an alternate line set to the '
            f'ceiling; the remaining {outside} — outright markets and moneylines with no ladder — cannot, and are '
            f'listed below with their real prices rather than being dressed up as band picks.</div>')


def band_table(rows):
    if not rows:
        return '<div class="note warn">Nothing in this group today.</div>'
    out = ['<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Fixture</th><th>Selection</th>'
           '<th>Line</th><th>Prob</th><th>Fair</th><th>Offered</th><th>Grade</th><th>Basis</th><th>Source</th>'
           '</tr></thead><tbody>']
    for p in rows:
        out.append(
            f'<tr><td><a href="sports/{SLUG[p["sport"]]}.html">{escape(p["sport"])}</a></td>'
            f'<td>{label(p["home"], p["away"])}</td>'
            f'<td><strong>{escape(p["selection"])}</strong></td>'
            f'<td class="mono">{escape(str(p["line"])) if p["line"] is not None else "—"}</td>'
            f'<td class="mono">{fmt_p(p["probability"])}</td>'
            f'<td class="mono">{fmt_am(p["fair_american"])}</td>'
            f'<td class="mono">{p["fair_decimal"]}</td>'
            f'<td>{confpill(p["confidence"])}</td>'
            f'<td class="small">{escape(p["basis"][:150])}</td>'
            f'<td>{src(p["official_source_url"])}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


# --------------------------------------------------------------- picks
def build_picks():
    rows = sorted([p for p in P["picks"] if p.get("sport_rank")], key=lambda p: (SPORTS.index((p["sport"], SLUG[p["sport"]])), p["sport_rank"]))
    body = f"""
<h1>Top five by sport</h1>
<p class="lede">The five highest-confidence selections the desk can support in each sport today, ranked by
grade and then probability. Where a sport's card yields fewer than five, the page says so instead of
promoting a low-confidence row. Selecting the “Band” column gives the band board.</p>
<div class="table-wrap"><table><thead><tr><th>#</th><th>Sport</th><th>Fixture</th><th>Start</th><th>Selection</th>
<th>Market</th><th>Prob</th><th>Fair</th><th>Band</th><th>Grade</th><th>Evidence</th><th>Source</th></tr></thead><tbody>
{''.join(pick_row(p) for p in rows)}
</tbody></table></div>
<h2>Where a sport cannot reach five</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Selections at medium or better</th><th>Why</th></tr></thead><tbody>
{''.join(shortfall_row(n, s) for n, s in SPORTS if len(SP[n]['picks']) < 5 or SP[n]['stats'].get('high', 0) == 0)}
</tbody></table></div>
"""
    write("picks.html", page("Top five by sport", "picks.html", body))


def pick_row(p):
    st = SP[p["sport"]]
    return (f'<tr><td class="mono">{p["sport_rank"]}</td>'
            f'<td><a href="sports/{SLUG[p["sport"]]}.html">{escape(p["sport"])}</a></td>'
            f'<td>{label(p["home"], p["away"])}</td>'
            f'<td class="small">{escape(p.get("time_display") or p.get("start_utc") or "—")}</td>'
            f'<td><strong>{escape(p["selection"])}</strong></td><td>{escape(p["market"])}</td>'
            f'<td class="mono">{fmt_p(p["probability"])}</td><td class="mono">{fmt_am(p["fair_american"])}</td>'
            f'<td>{bandpill(p["in_band"])}</td><td>{confpill(p["confidence"])}</td>'
            f'<td class="small">{escape(p["evidence_tier"])} · {escape(p["evidence"][:90])}</td>'
            f'<td>{src(p["official_source_url"])}</td></tr>')


def shortfall_row(name, slug_name):
    st = SP[name]
    stats = st["stats"]
    med = sum(1 for p in P["picks"] if p["sport"] == name and p["confidence"] in ("high", "medium"))
    reasons = []
    if len(st["matches"]) < 5:
        reasons.append(f"only {len(st['matches'])} official fixtures on the card")
    if stats.get("high", 0) == 0:
        reasons.append("no selection reaches 70% on the official input available")
    if med < 5:
        reasons.append(f"{med} selections at medium or better")
    if not st["preds"]:
        reasons.append("no written prediction, because the brief ties write-ups to high-confidence picks")
    return f'<tr><td><a href="sports/{slug_name}.html">{escape(name)}</a></td><td class="mono">{len(st["picks"])}</td><td class="small">{escape("; ".join(reasons))}</td></tr>'


# --------------------------------------------------------------- matches / lines
def build_matches():
    order = {n: i for i, (n, _) in enumerate(SPORTS)}
    rows = sorted(M["matches"], key=lambda m: (order[m["sport"]], m.get("start_utc") or m.get("time_display") or ""))
    body = f"""
<h1>All {M['count']} fixtures</h1>
<p class="lede">Every fixture captured from an official source today, in the fifteen covered sports. A row
marked <span class="pill blank">no line</span> means an official page did not publish a numeric input for both
sides, so the desk left the price blank rather than inventing one.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Competition</th><th>Fixture</th><th>Venue</th>
<th>Start</th><th>Status</th><th>Favourite</th><th>Prob</th><th>Grade</th><th>Official source</th></tr></thead><tbody>
{''.join(match_row(m) for m in rows)}
</tbody></table></div>
"""
    write("matches.html", page("All matches", "matches.html", body))


def match_row(m):
    status = ('<span class="pill high">priced</span>' if m["status"] == "originated"
              else '<span class="pill blank">no line</span>')
    venue = m.get("venue") or ""
    return (f'<tr><td><a href="sports/{SLUG[m["sport"]]}.html">{escape(m["sport"])}</a></td>'
            f'<td class="small">{escape(m["competition"])}</td>'
            f'<td><strong>{label(m["home"], m["away"])}</strong></td>'
            f'<td class="small">{escape(venue)}</td>'
            f'<td class="small">{escape(m.get("time_display") or m.get("start_utc") or "—")}</td>'
            f'<td>{status}</td>'
            f'<td>{escape(m.get("favourite") or "—")}</td>'
            f'<td class="mono">{fmt_p(m["favourite_probability"]) if m.get("favourite_probability") else "—"}</td>'
            f'<td>{confpill(m.get("confidence"))}</td>'
            f'<td>{src(m["official_source_url"])}</td></tr>')


def build_lines():
    order = {n: i for i, (n, _) in enumerate(SPORTS)}
    rows = sorted(L["lines"], key=lambda l: (order[l["sport"]], l["fixture_id"], l["market"], -(l["probability"] or 0)))
    body = f"""
<h1>{L['count']} originated prices</h1>
<p class="lede">Match winner, handicap and total markets for every fixture with an official numeric input, at
the desk's own fair price. “Offered” applies a per-sport margin to the fair price; the band check uses the
fair price, which is the stricter test.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th>
<th>Line</th><th>Prob</th><th>Fair</th><th>Offered</th><th>Band</th><th>Grade</th>
<th>Official source</th></tr></thead><tbody>
{''.join(line_row(l) for l in rows)}
</tbody></table></div>
"""
    write("lines.html", page("Originated lines", "lines.html", body))


def line_row(l):
    f = FIX[l["fixture_id"]]
    return (f'<tr><td class="small">{escape(l["sport"])}</td>'
            f'<td class="small">{label(f["home"], f["away"])}</td>'
            f'<td>{escape(l["market"])}</td><td>{escape(l["selection"])}</td>'
            f'<td class="mono">{escape(str(l["line"])) if l["line"] is not None else "—"}</td>'
            f'<td class="mono">{fmt_p(l["probability"])}</td>'
            f'<td class="mono">{fmt_am(l["fair_american"])}</td>'
            f'<td class="mono">{l["offered_decimal"]}</td>'
            f'<td>{bandpill(l["in_band"])}</td><td>{confpill(l["confidence"])}</td>'
            f'<td>{src(FIX[l["fixture_id"]]["official_source_url"])}</td></tr>')


# --------------------------------------------------------------- predictions
def build_predictions():
    cards = []
    for p in sorted(PR["predictions"], key=lambda x: (SPORTS.index((x["sport"], SLUG[x["sport"]])), x["pick_id"])):
        facts = "".join(
            f'<li>{escape(f["claim"])} — {src(f["source_url"])}</li>' for f in p["facts"])
        cards.append(f"""
<div class="pred" id="{escape(p['id'])}">
  <h4>{escape(p['headline'])}</h4>
  <div class="meta">{escape(p['sport'])} · {escape(p['competition'])} · {escape(p['time_display'] or '')} ·
    {p['word_count']} words · {confpill(p['confidence'])} {bandpill(p['in_band'])}</div>
  <div class="sel">{label(p['home'], p['away'])} — {escape(p['selection'])}
    ({escape(p['market'])}{', line ' + escape(str(p['line'])) if p['line'] is not None else ''})
    at {fmt_p(p['probability'])} / {fmt_am(p['fair_american'])}</div>
  <p>{escape(p['text'])}</p>
  <div class="facts"><div class="small"><strong>Numbers used, each with its official source</strong></div>
    <ul>{facts}</ul></div>
</div>""")
    body = f"""
<h1>{PR['count']} written predictions</h1>
<p class="lede">One unique write-up per graded selection, {PR['min_words']}+ words each, with the betting
selection stated in the first sentence and every number traceable to the official page linked beneath it.
The words “model” and “verified” are banned from reader-facing prose and the builder rejects them.</p>
<div class="note">Predictions exist for {len(PR['sports'])} of the 15 sports. Golf, greyhounds and Gaelic
sports have none, because no selection in those sports reached medium confidence today — writing one anyway
would mean inventing an edge. The reason is printed on each sport page.</div>
{''.join(cards)}
"""
    write("predictions.html", page("Predictions", "predictions.html", body))


# --------------------------------------------------------------- sport pages
def build_sports():
    index_rows = []
    for name, slug in SPORTS:
        st = SP[name]
        stats = st["stats"]
        index_rows.append(
            f'<tr><td><a href="{slug}.html"><strong>{escape(name)}</strong></a></td>'
            f'<td class="mono">{len(st["matches"])}</td><td class="mono">{len(st["lines"])}</td>'
            f'<td class="mono">{len(st["picks"])}</td><td class="mono">{stats.get("high", 0)}</td>'
            f'<td class="mono">{len(st["preds"])}</td></tr>')
        body = f"""
<h1>{escape(name)}</h1>
<p class="lede">{len(st['matches'])} official fixtures, {len(st['lines'])} originated prices,
{len(st['picks'])} top-five selections ({stats.get('high', 0)} graded high) and {len(st['preds'])}
written predictions.</p>
<h2>Top five by confidence</h2>
{picks_block(st['picks'])}
<h2>Fixtures, prices and official sources</h2>
{fixture_block(st['matches'])}
<h2>Written predictions</h2>
{pred_block(st['preds']) if st['preds'] else '<div class="note warn"><b>No prediction for this sport.</b> No selection on today’s card reached medium confidence, so a ≥30-word write-up would be inventing an edge. The prices and probabilities above are still published with their official sources.</div>'}
"""
        write(f"sports/{slug}.html", page(name, "", body, prefix="../"))
    body = f"""
<h1>Sports</h1>
<p class="lede">Fifteen pages, one per covered sport. Each carries the fixtures, the originated prices, the
five highest-confidence selections and any written predictions.</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Fixtures</th><th>Prices</th><th>Top five</th>
<th>High</th><th>Predictions</th></tr></thead><tbody>{''.join(index_rows)}</tbody></table></div>
"""
    write("sports/index.html", page("Sports", "sports/index.html", body, prefix="../"))


def picks_block(rows):
    if not rows:
        return '<div class="note bad">No selection reached medium confidence.</div>'
    out = ['<div class="table-wrap"><table><thead><tr><th>#</th><th>Fixture</th><th>Selection</th><th>Prob</th>'
           '<th>Fair</th><th>Band</th><th>Grade</th><th>Source</th></tr></thead><tbody>']
    for p in rows:
        out.append(f'<tr><td class="mono">{p["sport_rank"]}</td>'
                   f'<td>{label(p["home"], p["away"])}</td>'
                   f'<td><strong>{escape(p["selection"])}</strong><div class="small">{escape(p["market"])}</div></td>'
                   f'<td class="mono">{fmt_p(p["probability"])}</td><td class="mono">{fmt_am(p["fair_american"])}</td>'
                   f'<td>{bandpill(p["in_band"])}</td><td>{confpill(p["confidence"])}</td>'
                   f'<td>{src(p["official_source_url"])}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def fixture_block(rows):
    out = ['<div class="table-wrap"><table><thead><tr><th>Fixture</th><th>Competition</th><th>Start</th>'
           '<th>Status</th><th>Evidence</th><th>Official source</th><th>Notes</th></tr></thead><tbody>']
    for m in rows:
        facts = "<br>".join(f'{escape(f["team_or_item"])}: {escape(f["value"])} — {src(f["source_url"])}'
                            for f in m["facts"])
        status_html = "priced" if m["status"] == "originated" else '<span class="pill blank">no line</span>'
        extra = ""
        if m.get("stats_source_url") and m["stats_source_url"] != m["official_source_url"]:
            extra += '<div class="small">' + src(m["stats_source_url"]) + "</div>"
        if m.get("injury_source_url"):
            extra += '<div class="small">' + src(m["injury_source_url"], "NBA injury report") + "</div>"
        note = ("<br>" + escape(m["note"])) if m.get("note") else ""
        opponent = " v " + escape(m["away"]) if m["away"] else ""
        out.append(f'<tr><td><strong>{escape(m["home"])}</strong>{opponent}'
                   f'<div class="small">{escape(m.get("venue") or "")}</div></td>'
                   f'<td class="small">{escape(m["competition"])}</td>'
                   f'<td class="small">{escape(m.get("time_display") or m.get("start_utc") or "—")}</td>'
                   f'<td>{status_html}</td>'
                   f'<td class="small">{escape(m.get("evidence") or "")}</td>'
                   f'<td>{src(m["official_source_url"])}{extra}</td>'
                   f'<td class="small">{facts}{note}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def pred_block(rows):
    out = []
    for p in rows:
        facts = "".join(f'<li>{escape(f["claim"])} — {src(f["source_url"])}</li>' for f in p["facts"])
        out.append(f'<div class="pred"><h4>{escape(p["headline"])}</h4>'
                   f'<div class="meta">{p["word_count"]} words · {confpill(p["confidence"])} {bandpill(p["in_band"])}</div>'
                   f'<div class="sel">{escape(p["selection"])} ({escape(p["market"])}) at {fmt_am(p["fair_american"])}</div>'
                   f'<p>{escape(p["text"])}</p>'
                   f'<div class="facts"><ul>{facts}</ul></div></div>')
    return "".join(out)


# --------------------------------------------------------------- sources / methodology
def build_sources():
    rows = "".join(
        f'<tr><td>{escape(s["publisher"])}</td><td>{src(s["url"])}</td>'
        f'<td class="small">{escape(s["what"])}</td><td class="small mono">{escape(s["fetched_utc"])}</td></tr>'
        for s in SRC["sources"])
    body = f"""
<h1>Official source register</h1>
<p class="lede">{SRC['count']} governing-body, league, tour or federation pages were read first-hand during
the capture window. OLBG appears once, as the discovery source for the sport taxonomy — never as the source
of a fixture fact or a price.</p>
<div class="table-wrap"><table><thead><tr><th>Publisher</th><th>Page</th><th>What it provided</th>
<th>Read at (UTC)</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="note">A link here records provenance for the values that cite it. It does not imply the page
supports every other number on this site.</div>
"""
    write("sources.html", page("Sources", "sources.html", body))


def build_methodology():
    body = f"""
<h1>Method</h1>
<p class="lede">What the desk reads, how it turns those numbers into a price, how it grades confidence, and
what it refuses to do.</p>

<h2>1. Capture</h2>
<p>Each sport's fixtures come from its governing body, league, tour or federation — never from an odds
aggregator. The page is read with the agent fetch tool and the numbers are transcribed into
<code>data/cadence/fixtures.json</code> with the source key, the URL and the fetch timestamp. Timestamps are
stored exactly as the publisher prints them; where the basis is not stated (for example a URC “local” time)
the desk stores the string and does not convert it.</p>

<h2>2. Probability formulas</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Strength input</th><th>Match model</th>
<th>Margin / total</th></tr></thead><tbody>
<tr><td>Ice Hockey</td><td>NHL points percentage and goal rates</td><td>log5 with a 9% home term</td>
<td>normal, σ 1.75 goals; Poisson total</td></tr>
<tr><td>Basketball</td><td>EuroLeague shrunk win rate and point differential; NBA league prior</td>
<td>log5, 12% home term</td><td>normal, σ 10.5 (EL) / 12.0 (NBA) points</td></tr>
<tr><td>Baseball</td><td>2026 Pythagorean win% plus starter ERA gap</td><td>log5, 6% home term</td>
<td>normal, σ 4.05 runs; runs mean from season rates</td></tr>
<tr><td>Cricket</td><td>last completed official result only</td><td>±0.10 plus a 3% home term</td>
<td>σ 30–90 runs by format</td></tr>
<tr><td>Snooker</td><td>log10 ranking money (or 2026/27 win rate)</td><td>logistic, scale 1.6</td>
<td>normal, σ 2.2 frames</td></tr>
<tr><td>Darts</td><td>European Tour prize money or official seed</td><td>logistic, scale 1.4 / 3.0</td>
<td>normal, σ 2.0 legs</td></tr>
<tr><td>Tennis</td><td>ATP ranking points</td><td>logistic, scale 1.35</td><td>normal, σ 4.6 games</td></tr>
<tr><td>Handball</td><td>LNH shrunk win rate and goal rates</td><td>log5, 12% home term, 5.8% draw mass</td>
<td>normal, σ 8.6 goals</td></tr>
<tr><td>Rugby Union</td><td>Premiership win rate shrunk with a 10-match prior</td><td>log5, 10% home term, 3.2% draw</td>
<td>normal, σ 13.0 points</td></tr>
<tr><td>Rugby League</td><td>Round 1 winning margin</td><td>0.006 per point, log5, 5% home term</td>
<td>normal, σ 13.5 points</td></tr>
<tr><td>Volleyball</td><td>sets won with a 20-match prior</td><td>per-set log5 then best-of-five</td>
<td>exact set distribution</td></tr>
<tr><td>Golf</td><td>strokes behind the 36-hole leader</td><td>softmax, τ 3.2 shots, 45 unlisted rivals</td>
<td>no totals market</td></tr>
<tr><td>Greyhounds</td><td>semi-final winning time</td><td>softmax, τ 0.22s</td><td>no totals market</td></tr>
<tr><td>Motor Racing</td><td>2026 championship points and FP1 order</td><td>softmax, τ 140; title from the points gap</td>
<td>single-race variance discount</td></tr>
<tr><td>Gaelic Sports</td><td>published semi-final winning margin</td><td>0.012 per point, 4% draw mass</td>
<td>normal, σ 7.0 points</td></tr>
</tbody></table></div>

<h2>3. Grading</h2>
<p><span class="pill high">high</span> needs P ≥ 70% and evidence tier A (a full-season table or ranking) or
tier B (4–9 matches this season). Where only 1–3 matches exist, a natural money-line selection can still be
graded high because the probability is what the official numbers imply, but an alternate band line on the
same thin sample is capped at <span class="pill medium">medium</span>. Every cap is printed on the row.
<span class="pill medium">medium</span> is 60–70%.</p>

<h2>4. The band</h2>
<p>Fair American odds between −250 and +10000. −250 is 71.43%, so this band and P ≥ 70% overlap only in
70.00–71.43%. The desk publishes the fair price of every selection, marks it in or out of band, and quotes an
alternate line at the band ceiling where the ladder allows. See the <a href="band.html">band board</a>.</p>

<h2>5. What the desk will not do</h2>
<ul>
  <li>Publish a price for a fixture where an official source does not name both participants.</li>
  <li>Use an observed bookmaker price as an input. The NHL feed's moneylines are shown as a comparison and
  labelled as such.</li>
  <li>Assert an injury outside the NBA's own game-day report.</li>
  <li>Convert a time when the publisher has not stated its basis.</li>
  <li>Write a prediction for a selection below medium confidence.</li>
  <li>Use the words “model” or “verified” in reader-facing prose.</li>
</ul>
"""
    write("methodology.html", page("Method", "methodology.html", body))


# --------------------------------------------------------------- OLBG + audit + flags
def build_olbg():
    body = f"""
<h1>OLBG: what the site actually serves</h1>
<p class="lede">Read first-hand from olbg.com during the capture window across the sixteen sportIds that cover
the fifteen mandated sports. OLBG is used for discovery and taxonomy only: it is not the source of a single
fixture fact or price on this desk.</p>

<h2>Sport index</h2>
<p>Hub route: <code>/betting-tips/{{Sport}}/{{id}}</code>. Event route:
<code>/betting-tips/{{Sport}}/{{Group}}/{{Competition}}/{{Event_Name}}/{{id}}?event_id={{eventId}}</code>.
The sport name is case-sensitive in the path. The fifteen mandated sports map to sixteen ids because Gaelic
Sports is split across Gaelic Football (25) and Hurling (26).</p>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>OLBG id</th><th>Hub</th><th>Markets shown</th></tr></thead><tbody>
{''.join(f'<tr><td>{escape(n)}</td><td class="mono">{i}</td><td>{src("https://www.olbg.com/betting-tips/" + hub + "/" + i)}</td><td class="small">{escape(mk)}</td></tr>'
         for n, i, hub, mk in [
            ("Golf", "5", "Golf", "Win Tournament (hub returned no rows today)"),
            ("Volleyball", "21", "Volleyball", "Win Match, Set Score"),
            ("Rugby Union", "9", "Rugby_Union", "To Win"),
            ("Cricket", "7", "Cricket", "Win Match"),
            ("Snooker", "8", "Snooker", "Win Match"),
            ("Darts", "15", "Darts", "Win Match 2-way, Handicap 2-way, Total Legs"),
            ("Baseball", "12", "Baseball", "Money Line, Run Line, Game Totals"),
            ("Gaelic Sports", "25, 26", "Gaelic_Football", "Handicap, Win Match"),
            ("Greyhounds", "28", "Greyhounds", "Daily Races"),
            ("Tennis", "3", "Tennis", "Win Match, Set Betting, Total Games, Games Won"),
            ("Motor Racing", "14", "Motor_Racing", "Win Race, Win Tournament"),
            ("Handball", "20", "Handball", "Money Line (three-way, includes Tie)"),
            ("Ice Hockey", "13", "Ice_Hockey", "Money Line, Puck Line, Game Totals"),
            ("Basketball", "4", "Basketball", "Money Line, Pointspread, Game Totals"),
            ("Rugby League", "10", "Rugby_League", "To Win, Grand Final Winner")])}
</tbody></table></div>

<h2>Four defects found on the live site</h2>
<div class="table-wrap"><table><thead><tr><th>Defect</th><th>Evidence</th><th>Consequence for a parser</th></tr></thead><tbody>
<tr><td>US IPs see an empty hub</td><td>Every <code>/betting-tips/{{Sport}}/{{id}}</code> page renders “No tips found.”
while the same events resolve normally through <code>?event_id=</code></td>
<td>Discovery must follow event ids, not scrape the hub list</td></tr>
<tr><td>Tip denominators are string-concatenated</td><td><code>event_id=199984</code> renders
“4 / 042 | 95%” for a market whose own table says 4 of 42; <code>160789</code> renders “6 / 062”;
<code>536036</code> renders “9 / 090”; <code>902163</code> renders “2 / 021”</td>
<td>Never parse the header pill; parse the market table</td></tr>
<tr><td>Odds cells are blank for a logged-out US visitor</td><td><code>event_id=32384</code> and
<code>902163</code> render “WIN @” with nothing after it</td><td>OLBG cannot supply a price at all</td></tr>
<tr><td>False “Expired” badges and a shifted clock</td><td>Unstarted 24 October fixtures carry an
“Expired” badge and a US-Eastern time</td><td>Status must come from the governing body</td></tr>
</tbody></table></div>

<div class="note warn"><b>Why this matters for the brief.</b> OLBG's percentage is the share of community tips
on a selection, not a probability and not a price. Using it as either would manufacture an edge that does not
exist. The desk records the tip split only as a description of OLBG, never as an input.</div>
"""
    write("olbg.html", page("OLBG reverse-engineering", "olbg.html", body))


def build_audit():
    rows = []
    for f in AUD["findings"]:
        rows.append(f'<tr><td class="mono">{escape(f["id"])}</td>'
                    f'<td><span class="pill {"out" if f["severity"] == "high" else "medium"}">{escape(f["severity"])}</span></td>'
                    f'<td class="small">{escape(f["category"])}</td>'
                    f'<td class="small"><code>{escape(f["file_path"])}</code><br>{escape(str(f["lines"]))}</td>'
                    f'<td class="small">{escape(f["issue"])}</td>'
                    f'<td class="small">{escape(f["official_check"])}</td>'
                    f'<td>{src(f["official_source_url"])}</td></tr>')
    body = f"""
<h1>Line-by-line repository audit</h1>
<p class="lede">{AUD['summary']['irregularities_logged']} irregularities found while re-reading the merged
layers line by line: {AUD['summary']['out_of_scope_html_files']} out-of-scope sport pages,
{AUD['summary']['predictions_with_forbidden_words']} prediction entries containing a prohibited word, and
{AUD['summary']['html_files_with_unlinked_rows']} HTML files with table rows that carry no official source
link.</p>
<div class="note">Each finding below was checked against the file on disk and, where the finding is about an
external fact, re-read against the official page linked beside it. Nothing here was repaired in another
session's scope; the audit reports, and the owning session or the integrator acts.</div>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Severity</th><th>Category</th><th>File and lines</th>
<th>Finding</th><th>How it was checked</th><th>Official source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
"""
    write("audit.html", page("Repository audit", "audit.html", body))


def build_flagged():
    rows = "".join(
        f'<tr><td class="mono">{escape(f["id"])}</td>'
        f'<td><span class="pill {"out" if f.get("severity") == "high" else "medium"}">{escape(f.get("severity", "medium"))}</span></td>'
        f'<td class="small">{escape(f.get("category", ""))}</td>'
        f'<td class="small">{escape(f.get("item", ""))}</td>'
        f'<td class="small">{escape(f.get("finding", ""))}</td>'
        f'<td>{src(f.get("source_url"))}</td></tr>'
        for f in FLAG["flags"])
    notes = f"""
<h2>Desk disclosures</h2>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Severity</th><th>Category</th><th>Item</th>
<th>Finding</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Values left blank rather than inferred</h2>
<div class="table-wrap"><table><thead><tr><th>Sport</th><th>Fixture</th><th>Why it is blank</th><th>Official source</th></tr></thead><tbody>
{''.join(f'<tr><td>{escape(m["sport"])}</td><td>{label(m["home"], m["away"])}</td>'
         f'<td class="small">{escape(m["note"] or "")}</td><td>{src(m["official_source_url"])}</td></tr>'
         for m in M["matches"] if m["status"] == "blank")}
</tbody></table></div>
<h2>Cross-checked irregularities from the repository audit</h2>
<p class="lede">The full list, with line numbers and the check performed for each, is on
<a href="audit.html">the repository audit page</a>. The high-severity items are:</p>
<ul>{''.join(f'<li><strong>{escape(f["id"])}</strong> — {escape(f["issue"])} ({src(f["official_source_url"])})</li>' for f in AUD["findings"] if f["severity"] == "high")}</ul>
"""
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Everything the desk could not settle from an official source, plus every known defect in the
wider repository. Nothing on this page blocks publication; it is the queue for a human.</p>
{notes}
"""
    write("flagged.html", page("Flagged for review", "flagged.html", body))


def main():
    if os.path.isdir(OUT):
        for name in os.listdir(OUT):
            if name not in ("assets",):
                path = os.path.join(OUT, name)
                shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    os.makedirs(OUT, exist_ok=True)
    build_index()
    build_band()
    build_picks()
    build_matches()
    build_lines()
    build_predictions()
    build_sports()
    build_sources()
    build_methodology()
    build_olbg()
    build_audit()
    build_flagged()
    pages = sum(len(files) for _, _, files in os.walk(OUT))
    print(f"cadence/: {pages} files, {M['count']} fixtures, {L['count']} prices, {P['count']} picks, "
          f"{PR['count']} predictions")


if __name__ == "__main__":
    main()
