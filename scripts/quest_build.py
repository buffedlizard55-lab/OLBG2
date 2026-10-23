#!/usr/bin/env python3
"""Build the /quest/ static dashboard from data/quest/*.json. Deterministic."""
import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "quest"
OUT = ROOT / "quest"
CUTOFF = "2026-10-23T21:30:00Z"
CUTOFF_DT = datetime(2026, 10, 23, 21, 30)

SLUG = {"Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
        "Cricket": "cricket", "Snooker": "snooker", "Darts": "darts",
        "Baseball": "baseball", "Gaelic Sports": "gaelic-sports",
        "Greyhounds": "greyhounds", "Tennis": "tennis",
        "Motor Racing": "motor-racing", "Handball": "handball",
        "Ice Hockey": "ice-hockey", "Basketball": "basketball",
        "Rugby League": "rugby-league"}
SPORTS15 = list(SLUG)  # brief order preserved above? use canonical order below
SPORTS15 = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
            "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
            "Handball", "Ice Hockey", "Basketball", "Rugby League"]


def load(name):
    return json.loads((DATA / name).read_text())


def e(x):
    return html.escape("" if x is None else str(x))


def pct(p):
    return f"{p * 100:.1f}%"


def fam(am):
    return f"+{am}" if am > 0 else str(am)


def match_label(f):
    return f"{f['home']} v {f['away']}" if f.get("away") else f["home"]


def parse_z(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)


def start_cell(f):
    if f["start_utc"]:
        dt = parse_z(f["start_utc"])
        tag = {"published-utc-or-offset": "",
               "venue-local-converted": '<span class="tag">venue time converted</span>',
               "viewer-zone-inferred": '<span class="tag warn">viewer zone inferred Q-TZ1</span>',
               "session-window-start": '<span class="tag warn">session start</span>'}[f["time_status"]]
        return f"{dt.strftime('%a %d %b, %H:%M')} UTC {tag}"
    dt = datetime.strptime(f["sort_key"][:10], "%Y-%m-%d")
    return (f"{dt.strftime('%a %d %b')} "
            f'<span class="tag warn">date only — start unconfirmed Q-TZ2</span><br>'
            f'<span class="small">{e(f["time_display"])}</span>')


def conf_badge(c):
    if not c:
        return '<span class="badge none">—</span>'
    return f'<span class="badge {c}">{c.upper()}</span>'


def band_badge(b):
    return ('<span class="badge in">IN WINDOW</span>' if b
            else '<span class="badge out">OUTSIDE</span>')


def src_links(f, stats=True):
    parts = [f'<a href="{e(f["official_source_url"])}" rel="noopener">Official fixture</a>']
    if stats and f.get("stats_source_url") and f["stats_source_url"] != f["official_source_url"]:
        parts.append(f'<a href="{e(f["stats_source_url"])}" rel="noopener">Official stats</a>')
    if f.get("injury_source_url"):
        parts.append(f'<a href="{e(f["injury_source_url"])}" rel="noopener">League injury report</a>')
    parts.append(f'<a href="{e(f["olbg_sport_url"])}" rel="noopener">OLBG sport page</a>')
    return " · ".join(parts)


CSS = """:root{--ink:#17202a;--mut:#5b6b7b;--line:#d9e1e8;--bg:#f6f8fa;--card:#fff;
--acc:#0b5cab;--high:#8a6100;--highbg:#fff3cd;--med:#0b5cab;--medbg:#e3eefb;
--low:#5b6b7b;--lowbg:#eef1f4;--in:#176b3a;--inbg:#e2f3e7;--out:#9a3412;--outbg:#ffe9df}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header.top{background:#0f2a44;color:#fff;padding:14px 20px}header.top h1{font-size:20px;margin:0}
header.top p{margin:4px 0 0;color:#c9d8e6;font-size:13px}
nav.main{background:#16395c;padding:8px 20px;display:flex;flex-wrap:wrap;gap:6px}
nav.main a{color:#dce9f5;text-decoration:none;padding:5px 10px;border-radius:6px;font-size:14px}
nav.main a:hover{background:#24507e}nav.main a.on{background:#fff;color:#16395c;font-weight:600}
main{max-width:1240px;margin:0 auto;padding:20px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:14px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi b{font-size:24px;display:block}.kpi span{color:var(--mut);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:16px 0}
h2{font-size:19px;margin:22px 0 8px}h3{font-size:16px;margin:18px 0 6px}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:#fff;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef3f8;position:sticky;top:0}tr:hover td{background:#f7fafc}
.badge{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap}
.badge.high{background:var(--highbg);color:var(--high)}.badge.medium{background:var(--medbg);color:var(--med)}
.badge.low{background:var(--lowbg);color:var(--low)}.badge.in{background:var(--inbg);color:var(--in)}
.badge.out{background:var(--outbg);color:var(--out)}.badge.none{background:#eee;color:#888}
.tag{display:inline-block;padding:0 6px;border-radius:4px;background:#eef3f8;color:var(--acc);font-size:11px}
.tag.warn{background:#fff3cd;color:#8a6100}.small{color:var(--mut);font-size:12px}
.note{background:#fff8e1;border:1px solid #ecd27a;border-radius:8px;padding:10px 14px;margin:12px 0}
.pred{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:14px 0}
.pred h3{margin-top:0}.facts{margin:8px 0 0;padding-left:18px}.facts li{margin:3px 0}
a{color:var(--acc)}footer{max-width:1240px;margin:0 auto;padding:10px 20px 30px;color:var(--mut);font-size:13px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
input.flt{width:100%;max-width:420px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;margin:8px 0}
code{background:#eef3f8;padding:1px 5px;border-radius:4px;font-size:13px}
"""

NAV = [("index.html", "Summary"), ("today.html", "Next 24 hours"),
       ("matches.html", "All matches"), ("markets.html", "Originated markets"),
       ("picks.html", "Picks"), ("top5.html", "Top 5 by sport"),
       ("predictions.html", "Predictions"), ("olbg.html", "OLBG map"),
       ("methodology.html", "Methodology"), ("sources.html", "Sources"),
       ("flagged.html", "Flagged for Review")]

FILTER_JS = """<script>
document.querySelectorAll('input.flt').forEach(function(inp){
 var tbl=document.getElementById(inp.dataset.target);if(!tbl)return;
 inp.addEventListener('input',function(){var q=inp.value.toLowerCase();
  tbl.querySelectorAll('tbody tr').forEach(function(r){
   r.style.display=r.textContent.toLowerCase().includes(q)?'':'none';});});});
</script>"""


def page(title, active, body, root_prefix=""):
    nav = "".join(
        f'<a href="{root_prefix}{h}"{" class=on" if h == active else ""}>{t}</a>'
        for h, t in NAV)
    sport_nav = " · ".join(
        f'<a href="{root_prefix}sports/{SLUG[s]}.html">{s}</a>' for s in SPORTS15)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — Quest board (23 Oct 2026)</title>
<link rel="stylesheet" href="{root_prefix}style.css"></head><body>
<header class="top"><h1>OLBG2 Quest board — 15-sport originated lines</h1>
<p>Snapshot cut-off <b>{CUTOFF}</b>. Our own fair lines from stored official inputs — not bookmaker prices, not betting advice. 18+.</p></header>
<nav class="main">{nav}</nav>
<main>{body}
<div class="card"><h3 style="margin-top:0">Sports</h3><p class="small">{sport_nav}</p></div>
</main>
<footer>Quest desk (session 693dbf40). Built from the cadence capture 2026-10-23T20:05Z, the brief NHL capture 2026-10-23T16:30Z and an NHL.com read at ~21:30Z the same evening. Every price is an originated fair price; an empty cell means the value could not be confirmed from an official source. Full session record: <a href="https://github.com/buffedlizard55-lab/OLBG2/blob/main/research/quest-693dbf40.md">research/quest-693dbf40.md</a>. Other desks: <a href="{root_prefix}../cadence/index.html">/cadence/</a> · <a href="{root_prefix}../brief/index.html">/brief/</a> · <a href="{root_prefix}../index.html">root dashboard</a>.</footer>
{FILTER_JS}</body></html>
"""


def pick_row(p, f, pred_ids):
    pred = (f'<a href="predictions.html#pred-{e(p["id"])}">Read prediction</a>'
            if p["id"] in pred_ids else '<span class="small">—</span>')
    return (f'<tr><td><b>{e(p["selection"])}</b><br><span class="small">{e(p["market"])}</span></td>'
            f'<td>{e(match_label(f))}<br><span class="small">{e(f["sport"])} · {e(f["competition"])}</span></td>'
            f'<td>{start_cell(f)}</td><td>{pct(p["probability"])}</td>'
            f'<td>{e(fam(p["fair_american"]))} ({p["fair_decimal"]:.3f})</td>'
            f'<td>{band_badge(p["in_band"])}</td><td>{conf_badge(p["confidence"])}</td>'
            f'<td>{pred}<br><a href="{e(f["official_source_url"])}" rel="noopener">Official source</a></td></tr>')


def main():
    meta = load("fixtures.json")["meta"]
    fixtures = load("fixtures.json")["fixtures"]
    lines = load("lines.json")["lines"]
    picks = load("picks.json")["picks"]
    top5 = load("top5.json")["top5"]
    preds = load("predictions.json")["predictions"]
    sources = load("sources.json")["sources"]
    flags = load("flagged.json")["flags"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    (OUT / "style.css").write_text(CSS)

    fx = {f["id"]: f for f in fixtures}
    lines_by_fx = defaultdict(list)
    for l in lines:
        lines_by_fx[l["fixture_id"]].append(l)
    picks_by_fx = defaultdict(list)
    for p in picks:
        picks_by_fx[p["fixture_id"]].append(p)
    pred_pick_ids = {x["pick_id"] for x in preds}

    def disp_pick(fid):
        ps = picks_by_fx.get(fid, [])
        if not ps:
            return None
        pool = [p for p in ps if p["in_band"]] or ps
        return max(pool, key=lambda p: p["probability"])

    inband_high = sorted([p for p in picks if p["confidence"] == "high" and p["in_band"]],
                         key=lambda p: -p["probability"])
    high_all = sorted([p for p in picks if p["confidence"] == "high"],
                      key=lambda p: -p["probability"])
    nxt24_end = CUTOFF_DT + timedelta(hours=24)

    def within24(p):
        s = fx[p["fixture_id"]]["start_utc"]
        return s and parse_z(s) <= nxt24_end

    inband_high_24 = [p for p in inband_high if within24(p)]
    priced_n = sum(1 for f in fixtures if f["status"] == "priced")
    markets_cat = sorted({l["market"] for l in lines})

    mk_table = ('<div class="tw"><table><thead><tr><th>Selection</th><th>Match</th>'
                '<th>Start (UTC)</th><th>Our %</th><th>Fair price</th><th>−250…+10000</th>'
                '<th>Confidence</th><th>Links</th></tr></thead><tbody>{}</tbody></table></div>')

    # ---------------- index / executive summary ----------------
    cov_rows = ""
    for s in SPORTS15:
        rows = [f for f in fixtures if f["sport"] == s]
        n_price = sum(1 for r in rows if r["status"] == "priced")
        n_lines = sum(len(lines_by_fx[r["id"]]) for r in rows)
        n_high = sum(1 for p in picks if p["sport"] == s and p["confidence"] == "high")
        n_ib = sum(1 for p in picks if p["sport"] == s and p["confidence"] == "high" and p["in_band"])
        n_pred = sum(1 for x in preds if x["sport"] == s)
        first = min((r["sort_key"] for r in rows), default="")
        cov_rows += (f'<tr><td><a href="sports/{SLUG[s]}.html"><b>{s}</b></a></td>'
                     f'<td>{len(rows)}</td><td>{n_price}</td><td>{len(rows) - n_price}</td>'
                     f'<td>{n_lines}</td><td>{n_high}</td><td>{n_ib}</td><td>{n_pred}</td>'
                     f'<td>{e(first[:10])}</td>'
                     f'<td><a href="{e(meta["olbg_taxonomy"][s]["url"])}" rel="noopener">OLBG</a></td></tr>')

    body = f"""
<h2>Executive summary — Friday 23 October 2026, 21:30 UTC</h2>
<p>This board merges the two freshest official-source captures in the repository into one current list for exactly the
15 mandated sports: <b>{meta['fixtures']} upcoming matches</b>, <b>{priced_n} with our own originated lines</b>
(<b>{meta['lines']} prices</b> across {len(markets_cat)} market families), <b>{meta['picks']} graded picks</b> and
<b>{meta['predictions']} written predictions</b>. {meta['blank']} fixtures are listed without a line, each with its reason
on the row. Nothing here is a bookmaker quote: every price is a fair price originated from the stored official inputs
shown beside it, and <b>high confidence means an originated probability of at least 70%</b>.</p>
<div class="note"><b>Read the window before the prices.</b> High confidence (≥70%) and the requested price window
(−250 to +10000) overlap only between 70.00% and 71.43%, because a fair −250 <i>is</i> 71.43%. Nine selections sit in that
overlap today. Everything stronger is shown at its honest shorter price and badged OUTSIDE — never relabelled.
The five-per-sport shortlist on <a href="top5.html">Top 5 by sport</a> therefore shows, for each match, both its strongest
selection and its best selection inside the window.</div>
<div class="kpis">
<div class="kpi"><b>{meta['fixtures']}</b><span>upcoming matches listed</span></div>
<div class="kpi"><b>{priced_n}</b><span>matches with our lines</span></div>
<div class="kpi"><b>{meta['lines']}</b><span>originated prices</span></div>
<div class="kpi"><b>{len(high_all)}</b><span>high-confidence picks</span></div>
<div class="kpi"><b>{len(inband_high)}</b><span>high picks inside −250…+10000</span></div>
<div class="kpi"><b>{len(inband_high_24)}</b><span>of those, starting in 24h</span></div>
<div class="kpi"><b>{meta['predictions']}</b><span>written predictions</span></div>
<div class="kpi"><b>{meta['flags']}</b><span>items flagged for review</span></div>
</div>
<h2>Highest-confidence picks inside the window — next 24 hours</h2>
<p>Selections graded high whose fair price sits between −250 and +10000 and whose match starts by Saturday 21:30 UTC.
Each one has a written prediction using only stored official facts.</p>
{mk_table.format("".join(pick_row(p, fx[p["fixture_id"]], pred_pick_ids) for p in inband_high_24) or '<tr><td colspan="8">None start inside 24 hours. That is stated rather than padded with weaker picks.</td></tr>')}
<h2>Highest-confidence picks inside the window — full board</h2>
{mk_table.format("".join(pick_row(p, fx[p["fixture_id"]], pred_pick_ids) for p in inband_high))}
<h2>Strongest favourites at any price (outside the requested window)</h2>
<p>These are the board's highest-probability selections. Their fair prices are shorter than −250, so they fall outside the
requested window; they are published because hiding them would distort the top-five shortlists.</p>
{mk_table.format("".join(pick_row(p, fx[p["fixture_id"]], pred_pick_ids) for p in high_all if not p["in_band"]))}
<h2>Coverage by sport</h2>
<div class="tw"><table><thead><tr><th>Sport</th><th>Matches</th><th>Priced</th><th>Blank</th><th>Prices</th>
<th>High picks</th><th>In window</th><th>Predictions</th><th>First match</th><th>OLBG</th></tr></thead>
<tbody>{cov_rows}</tbody></table></div>
<p class="small">Blank means no line was originated; the reason is printed on the fixture row (<a href="matches.html">All matches</a>) and summarised as flag Q-BLANK.</p>
<h2>What needs your eyes first</h2>
<div class="grid2">
<div class="card"><h3 style="margin-top:0">Market disagreement — Colorado v Tampa Bay (Q-MKT1)</h3>
<p>NHL.com's published DraftKings line for tonight makes Colorado a −125 favourite; this board's originated pick is Tampa Bay.
Both numbers are shown with their sources on the <a href="flagged.html">Flagged for Review</a> page. No bookmaker price was used as an input anywhere.</p></div>
<div class="card"><h3 style="margin-top:0">OLBG inventory limit (Q-OLBG1)</h3>
<p>OLBG's event tables render in the browser; both pages re-read tonight returned “No tips found” to a plain fetch.
Fixtures therefore come from governing bodies and join OLBG at sport level. See the <a href="olbg.html">OLBG map</a>.</p></div>
<div class="card"><h3 style="margin-top:0">Start-time honesty (Q-TZ1, Q-TZ2)</h3>
<p>87 matches carry a UTC start; 26 carry a calendar date only because the source clock could not be resolved. Nine
viewer-zone clocks are converted as America/New_York with the triangulation published for review.</p></div>
<div class="card"><h3 style="margin-top:0">Known gaps (Q-COV1, Q-COV2)</h3>
<p>Saturday's eight NBA games and the NHL slates of 27–29 October exist on official calendars but could not be captured
with inputs tonight. They are omitted, not guessed.</p></div>
</div>
<p>Full market-by-market prices: <a href="markets.html">Originated markets</a> · every graded pick: <a href="picks.html">Picks</a> ·
shortlists: <a href="top5.html">Top 5 by sport</a> · prose: <a href="predictions.html">Predictions</a> ·
methods and limits: <a href="methodology.html">Methodology</a>.</p>
"""
    (OUT / "index.html").write_text(page("Executive summary", "index.html", body))

    # ---------------- today / next 24 hours ----------------
    timed24 = [f for f in fixtures if f["start_utc"]
               and parse_z(f["start_utc"]) <= nxt24_end]
    dateonly24 = [f for f in fixtures if not f["start_utc"] and f["sort_key"][:10] == "2026-10-24"]

    def match_row(f, show_sport=True):
        p = disp_pick(f["id"])
        if f["status"] == "priced" and p:
            fav = (f'<b>{e(p["selection"])}</b><br><span class="small">{e(p["market"])} · '
                   f'{pct(p["probability"])} · fair {e(fam(p["fair_american"]))}</span> '
                   f'{band_badge(p["in_band"])} {conf_badge(p["confidence"])}')
        else:
            fav = f'<span class="small">No line — {e(f["blank_reason"])}</span>'
        return (f'<tr><td>{start_cell(f)}</td>'
                + (f'<td>{e(f["sport"])}</td>' if show_sport else "")
                + f'<td><b>{e(match_label(f))}</b><br><span class="small">{e(f["competition"])}</span></td>'
                  f'<td>{e(f["venue"]) or "—"}</td><td>{fav}</td>'
                  f'<td><a href="sports/{SLUG[f["sport"]]}.html#{e(f["id"])}">All markets</a><br>{src_links(f)}</td></tr>')

    mhead = ('<div class="tw"><table{id} ><thead><tr><th>Start (UTC)</th>{sp}<th>Match</th>'
             '<th>Venue</th><th>Our pick (fair price)</th><th>Sources</th></tr></thead><tbody>{rows}</tbody></table></div>')
    body = f"""
<h2>Next 24 hours — from {CUTOFF} to Saturday 24 October, 21:30 UTC</h2>
<p>{len(timed24)} matches carry a UTC start inside the window, from tonight's NBA/NHL/World Series card through Saturday's
darts, tennis, rugby, volleyball, handball, Gaelic and early NHL games. In-window high-confidence selections among them:
<b>{len(inband_high_24)}</b> (listed on the <a href="index.html">summary</a>).</p>
{mhead.format(id=' id="t24"', sp='<th>Sport</th>', rows="".join(match_row(f) for f in timed24))}
<h2>Dated Saturday 24 October — exact start unconfirmed</h2>
<p>These fixtures are dated 24 October by their governing bodies, but the stored captures do not resolve the clock
(URC and WST page clocks, “Followed by” tennis slots, golf moving day, greyhound evening finals). No time has been invented; see flag Q-TZ2.</p>
{mhead.format(id=' id="tdo"', sp='<th>Sport</th>', rows="".join(match_row(f) for f in dateonly24))}
"""
    (OUT / "today.html").write_text(page("Next 24 hours", "today.html", body))

    # ---------------- all matches ----------------
    rows = "".join(match_row(f) for f in fixtures)
    body = f"""
<h2>All upcoming matches — {meta['fixtures']} fixtures, 15 sports</h2>
<p>Ordered by start (date-only fixtures sit at midday of their date for ordering only; the cell says so).
“OUR PICK” prefers the strongest selection inside −250…+10000; the full market set for each match is on its sport page.</p>
<input class="flt" data-target="mall" type="search" placeholder="Filter matches (team, sport, competition)…">
{mhead.format(id=' id="mall"', sp='<th>Sport</th>', rows=rows)}
"""
    (OUT / "matches.html").write_text(page("All matches", "matches.html", body))

    # ---------------- markets ----------------
    cat_rows = ""
    for m in markets_cat:
        ms = [l for l in lines if l["market"] == m]
        sports_m = ", ".join(sorted({l["sport"] for l in ms}))
        cat_rows += (f'<tr><td><b>{e(m)}</b></td><td>{len(ms)}</td><td>{e(sports_m)}</td>'
                     f'<td><a href="olbg.html">OLBG map</a></td></tr>')
    groups = ""
    for s in SPORTS15:
        ls = [l for l in lines if l["sport"] == s]
        ls.sort(key=lambda l: (fx[l["fixture_id"]]["sort_key"], l["fixture_id"], -l["probability"]))
        trs = ""
        for l in ls:
            f = fx[l["fixture_id"]]
            trs += (f'<tr><td>{e(match_label(f))}<br><span class="small">{e(start_cell(f))}</span></td>'
                    f'<td>{e(l["market"])}</td><td><b>{e(l["selection"])}</b></td>'
                    f'<td>{pct(l["probability"])}</td><td>{l["fair_decimal"]:.3f}</td>'
                    f'<td>{e(fam(l["fair_american"]))}</td><td>{band_badge(l["in_band"])}</td>'
                    f'<td>{conf_badge(l["confidence"])}</td>'
                    f'<td class="small">{e(l["basis"])}</td>'
                    f'<td><a href="{e(f["official_source_url"])}" rel="noopener">Official</a></td></tr>')
        groups += (f'<h3 id="m-{SLUG[s]}">{s} — {len(ls)} prices</h3>'
                   f'<div class="tw"><table><thead><tr><th>Match</th><th>Market</th><th>Selection</th>'
                   f'<th>Our %</th><th>Fair dec</th><th>Fair Am</th><th>Window</th><th>Conf</th>'
                   f'<th>Basis (inputs)</th><th>Source</th></tr></thead><tbody>{trs}</tbody></table></div>')
    body = f"""
<h2>Originated markets — {meta['lines']} fair prices</h2>
<p>Every available market family on this board, priced match by match: match winner / money line, handicaps
(puck/point/goal/set/game/leg/frame/run lines), match totals (points, goals, runs, games, sets, legs, frames) and
outrights (tournament winner, race winner, Drivers' Championship). Prices are fair prices (no margin) derived from the
stored inputs quoted in the basis column. Fixtures without sufficient inputs carry no prices at all — see the blank rows on
<a href="matches.html">All matches</a>.</p>
<div class="tw"><table><thead><tr><th>Market family</th><th>Prices</th><th>Sports</th><th>OLBG</th></tr></thead>
<tbody>{cat_rows}</tbody></table></div>
<input class="flt" data-target="dummy" type="search" placeholder="Tip: use your browser find (Ctrl/Cmd+F) across 856 prices…" disabled>
{groups}
"""
    (OUT / "markets.html").write_text(page("Originated markets", "markets.html", body))

    # ---------------- picks ----------------
    all_sorted = sorted(picks, key=lambda p: -p["probability"])
    rows = "".join(pick_row(p, fx[p["fixture_id"]], pred_pick_ids) for p in all_sorted)
    c = Counter(p["confidence"] for p in picks)
    body = f"""
<h2>All graded picks — {len(picks)}</h2>
<p>One headline selection per priced match (its match-winner favourite), plus a band-ceiling alternate wherever the
favourite is high-confidence but shorter than −250. Counts: <b>{c['high']} high</b> (≥70%), <b>{c['medium']} medium</b> (≥60%),
<b>{c['low']} low</b>. Every row shows its fair price and whether it sits inside −250…+10000.</p>
<input class="flt" data-target="pk" type="search" placeholder="Filter picks (team, sport, market)…">
<div class="tw"><table id="pk"><thead><tr><th>Selection</th><th>Match</th><th>Start (UTC)</th><th>Our %</th>
<th>Fair price</th><th>−250…+10000</th><th>Confidence</th><th>Links</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    (OUT / "picks.html").write_text(page("Picks", "picks.html", body))

    # ---------------- top5 ----------------
    secs = ""
    for s in SPORTS15:
        t5 = top5[s]
        trs = ""
        for t in t5:
            f = fx[t["fixture_id"]]
            bil = t.get("best_inband_line")
            if bil and not (t["in_band"] and bil["selection"] == t["selection"]):
                bil_s = (f'<b>{e(bil["selection"])}</b> <span class="small">({e(bil["market"])})</span> '
                         f'{pct(bil["probability"])} · fair {e(fam(bil["fair_american"]))} {conf_badge(bil["confidence"])}')
            elif bil:
                bil_s = '<span class="small">= strongest selection</span>'
            else:
                bil_s = '<span class="small">No line inside the window on this match</span>'
            pred = (f'<a href="predictions.html#pred-{e(t["pick_id"])}">Prediction</a><br>'
                    if t["pick_id"] in pred_pick_ids else "")
            trs += (f'<tr><td>#{t["rank"]}</td><td><b>{e(match_label(f))}</b><br>'
                    f'<span class="small">{e(f["competition"])}</span></td>'
                    f'<td>{start_cell(f)}</td>'
                    f'<td><b>{e(t["selection"])}</b><br><span class="small">{e(t["market"])}</span></td>'
                    f'<td>{pct(t["probability"])}</td>'
                    f'<td>{e(fam(t["fair_american"]))} ({t["fair_decimal"]:.3f})</td>'
                    f'<td>{band_badge(t["in_band"])} {conf_badge(t["confidence"])}</td>'
                    f'<td>{bil_s}</td>'
                    f'<td>{pred}<a href="{e(f["official_source_url"])}" rel="noopener">Official</a> · '
                    f'<a href="sports/{SLUG[s]}.html#{e(f["id"])}">Markets</a></td></tr>')
        n_priced_s = sum(1 for f in fixtures if f["sport"] == s and f["status"] == "priced")
        short_note = (f'<p class="small">Only {len(t5)} shown: this sport has {n_priced_s} priced match(es) in the window. '
                      f'The shortfall is stated, not padded.</p>' if len(t5) < 5 else "")
        secs += (f'<h3 id="t5-{SLUG[s]}"><a href="sports/{SLUG[s]}.html">{s}</a></h3>{short_note}'
                 f'<div class="tw"><table><thead><tr><th>#</th><th>Match</th><th>Start (UTC)</th>'
                 f'<th>Strongest selection</th><th>Our %</th><th>Fair price</th><th>Window / conf</th>'
                 f'<th>Best inside −250…+10000</th><th>Links</th></tr></thead><tbody>{trs}</tbody></table></div>')
    body = f"""
<h2>Top 5 by sport — the five highest-confidence matches in each sport</h2>
<p><b>Rule.</b> Matches are ranked by the probability of their display selection: the strongest selection inside
−250…+10000 where one exists at pick level, otherwise the outright strongest selection. The “Best inside” column then
shows the strongest in-window line on the same match from the full market set, so a short-priced favourite never hides
its playable alternate. Five is a maximum, not a quota: sports with fewer than five priced matches show fewer.</p>
{secs}
"""
    (OUT / "top5.html").write_text(page("Top 5 by sport", "top5.html", body))

    # ---------------- predictions ----------------
    order = {"high": 0, "medium": 1, "low": 2}
    preds_sorted = sorted(preds, key=lambda x: (not x["in_band"], order[x["confidence"]],
                                                -x["probability"]))
    cards = ""
    for x in preds_sorted:
        f = fx[x["fixture_id"]]
        facts = "".join(
            f'<li>{e(fl["claim"])} — <a href="{e(fl["source_url"])}" rel="noopener">source</a></li>'
            for fl in x["facts"])
        cards += f"""
<article class="pred" id="pred-{e(x["pick_id"])}">
<h3>{e(x["headline"])}</h3>
<p class="small">{e(match_label(f))} · {e(x["sport"])} · {e(x["competition"])} · {start_cell(f)} ·
Selection: <b>{e(x["selection"])}</b> ({e(x["market"])}) · our {pct(x["probability"])} · fair {e(fam(x["fair_american"]))} ·
{band_badge(x["in_band"])} {conf_badge(x["confidence"])} · {x["word_count"]} words</p>
<p>{e(x["text"])}</p>
<p class="small"><b>Facts behind this piece (official sources):</b></p>
<ul class="facts">{facts}</ul>
<p class="small">Fixture: <a href="{e(x["official_source_url"])}" rel="noopener">{e(x["official_source_url"])}</a></p>
</article>"""
    n_ib_high_pred = sum(1 for x in preds if x["confidence"] == "high" and x["in_band"])
    body = f"""
<h2>Written predictions — {len(preds)}</h2>
<p>Every high-confidence pick inside −250…+10000 ({n_ib_high_pred} of them) carries a written prediction of at least
30 words below, as do the remaining high-confidence picks and selected medium picks inherited from the cadence capture.
Each piece names its selection plainly, uses only facts stored with the fixture, and lists those facts with official links
underneath. No piece asserts an injury: the only official availability feed readable tonight is the NBA's, linked on the
NBA rows (flag Q-INJ). Golf, Greyhounds and Gaelic Sports carry no written prediction because no selection there reached
medium confidence; their prices are still published in full (flag CD-PR1, carried).</p>
{cards}
"""
    (OUT / "predictions.html").write_text(page("Predictions", "predictions.html", body))

    # ---------------- sport pages ----------------
    for s in SPORTS15:
        s_fx = [f for f in fixtures if f["sport"] == s]
        s_preds = [x for x in preds_sorted if x["sport"] == s]
        t5 = top5[s]
        t5_rows = "".join(
            f'<tr><td>#{t["rank"]}</td><td><b>{e(t["selection"])}</b> <span class="small">({e(t["market"])})</span></td>'
            f'<td>{e(match_label(fx[t["fixture_id"]]))}</td><td>{pct(t["probability"])}</td>'
            f'<td>{e(fam(t["fair_american"]))}</td><td>{band_badge(t["in_band"])}</td>'
            f'<td>{conf_badge(t["confidence"])}</td>'
            f'<td><a href="{e(t["official_source_url"])}" rel="noopener">Official</a></td></tr>'
            for t in t5)
        blocks = ""
        for f in s_fx:
            ls = sorted(lines_by_fx[f["id"]], key=lambda l: -l["probability"])
            if ls:
                lrows = "".join(
                    f'<tr><td>{e(l["market"])}</td><td><b>{e(l["selection"])}</b></td>'
                    f'<td>{pct(l["probability"])}</td><td>{l["fair_decimal"]:.3f}</td>'
                    f'<td>{e(fam(l["fair_american"]))}</td><td>{band_badge(l["in_band"])}</td>'
                    f'<td>{conf_badge(l["confidence"])}</td>'
                    f'<td><a href="{e(f["official_source_url"])}" rel="noopener">Official</a></td></tr>'
                    for l in ls)
                mkt = (f'<div class="tw"><table><thead><tr><th>Market</th><th>Selection</th><th>Our %</th>'
                       f'<th>Fair dec</th><th>Fair Am</th><th>Window</th><th>Conf</th><th>Source</th></tr></thead>'
                       f'<tbody>{lrows}</tbody></table></div>'
                       f'<p class="small">Basis: {e(ls[0]["basis"])}</p>')
            else:
                mkt = f'<p class="small">No line originated — {e(f["blank_reason"])}</p>'
            facts = "".join(
                f'<li><b>{e(fl["team_or_item"])}</b>: {e(fl["value"])} — '
                f'<a href="{e(fl["source_url"])}" rel="noopener">source</a></li>'
                for fl in f.get("facts", []))
            blocks += f"""
<article class="pred" id="{e(f["id"])}">
<h3>{e(match_label(f))}</h3>
<p class="small">{e(f["competition"])} · {start_cell(f)} · Venue: {e(f["venue"]) or "— (not in capture)"} ·
Evidence: {e(f["evidence"]) or "—"}</p>
<p class="small">{src_links(f)}</p>
{f'<ul class="facts">{facts}</ul>' if facts else ''}
{mkt}
</article>"""
        pcards = ""
        for x in s_preds:
            f = fx[x["fixture_id"]]
            pcards += (f'<article class="pred"><h3>{e(x["headline"])}</h3>'
                       f'<p class="small">{e(match_label(f))} · Selection: <b>{e(x["selection"])}</b> '
                       f'({e(x["market"])}) · fair {e(fam(x["fair_american"]))} · {band_badge(x["in_band"])} '
                       f'{conf_badge(x["confidence"])}</p><p>{e(x["text"])}</p>'
                       f'<p class="small"><a href="../predictions.html#pred-{e(x["pick_id"])}">Facts &amp; sources</a> · '
                       f'<a href="{e(x["official_source_url"])}" rel="noopener">Official fixture</a></p></article>')
        n_p = sum(1 for f in s_fx if f["status"] == "priced")
        b = f"""
<h2>{s} — {len(s_fx)} matches ({n_p} priced, {len(s_fx) - n_p} blank)</h2>
<p>OLBG: <a href="{e(meta["olbg_taxonomy"][s]["url"])}" rel="noopener">{e(meta["olbg_taxonomy"][s]["url"])}</a>
(sport id {meta["olbg_taxonomy"][s]["id"]}). OLBG event tables are client-rendered (flag Q-OLBG1); fixtures below come from official bodies.</p>
<h3>Top {len(t5)} — highest-confidence matches</h3>
<div class="tw"><table><thead><tr><th>#</th><th>Selection</th><th>Match</th><th>Our %</th><th>Fair</th>
<th>Window</th><th>Conf</th><th>Source</th></tr></thead><tbody>{t5_rows or '<tr><td colspan="8">No priced matches.</td></tr>'}</tbody></table></div>
{f'<h3>Written predictions ({len(s_preds)})</h3>{pcards}' if s_preds else '<p class="small">No written prediction in this sport: no selection reached the prose threshold. Prices below still stand in full.</p>'}
<h3>Every match — full originated markets</h3>
{blocks}
"""
        (OUT / "sports" / f"{SLUG[s]}.html").write_text(
            page(s, "", b, root_prefix="../"))

    # ---------------- OLBG map ----------------
    olbg_rows = ""
    for s in SPORTS15:
        t = meta["olbg_taxonomy"][s]
        mkts = ", ".join(sorted({l["market"] for l in lines if l["sport"] == s}))
        olbg_rows += (f'<tr><td><b>{s}</b></td><td>{t["id"]}</td>'
                      f'<td><a href="{e(t["url"])}" rel="noopener">{e(t["url"])}</a></td>'
                      f'<td>{e(mkts) or "—"}</td></tr>')
    body = f"""
<h2>OLBG reverse-engineering map (re-read 2026-10-23, ~21:30 UTC)</h2>
<p>Source pages read first-hand tonight: <a href="https://www.olbg.com/betting-tips" rel="noopener">olbg.com/betting-tips</a>
and <a href="https://www.olbg.com/betting-tips/Basketball/4" rel="noopener">the Basketball tips page</a>.</p>
<h3>URL schema</h3>
<ul>
<li>Sport tips index: <code>https://www.olbg.com/betting-tips/{{Sport}}/{{sport_id}}</code> — for example Tennis is <code>/Tennis/3</code>, Ice Hockey <code>/Ice_Hockey/13</code>.</li>
<li>Competition level inserts path segments before the id: <code>/Basketball/NBA/4</code>, <code>/Basketball/European/Euroleague/4</code>, <code>/Basketball/NBA/NBA_Championship/4</code> (outrights live here too).</li>
<li>Gaelic Sports is split by OLBG into Gaelic Football (<code>/Gaelic_Football/25</code>) and Hurling (<code>/Hurling/26</code>); this board covers both under the single mandated “Gaelic Sports” heading.</li>
<li>Event pages are reached from the (client-rendered) event tables; a stored example from an earlier capture uses the query form <code>/betting-tips/Ice_Hockey/13?event_id=199984</code>.</li>
<li>Tipster rankings mirror the same ids: <code>/best-tipsters/{{Sport}}/{{sport_id}}</code>.</li>
</ul>
<h3>How OLBG selections work (from the pages read)</h3>
<ul>
<li>Tips come from a free tipster community/competitions (running since 2002, over £1.2m paid out per OLBG's own page copy). Each selection shows tip count, percentage of tips behind it, expert counts (high strike-rate/profit tipsters) and a “Value Rating” comparing odds with tip-share-implied probability.</li>
<li>Event pages surface a Most Popular Tip and a Best Tipsters Tip, then every outcome per market with backer counts and written comments.</li>
<li>Basketball's three headline markets are named explicitly on its page: <b>Money Line</b>, <b>Pointspread</b> and <b>Game Totals</b> (overtime usually counts). Other sports follow the same families — match winner, handicap, match total — plus outrights; the market families originated on this board per sport are listed below.</li>
</ul>
<div class="note"><b>Hard limit (flag Q-OLBG1).</b> The event tables render client-side: both pages read tonight returned the literal
text “No tips found” to a server-side fetch, even though the sports are in season. A complete OLBG event inventory therefore
cannot be captured without a browser. This board reproduces OLBG's taxonomy and market vocabulary, takes fixtures from each
governing body instead, and joins to OLBG at sport level on every row. Only 2 of 93 inherited fixtures carry an OLBG event id,
and one of those values (gaa-cork-psfc = 14) looks like a sport id rather than an event id — flagged, not trusted.</div>
<h3>The 15 mandated sports on OLBG</h3>
<div class="tw"><table><thead><tr><th>Sport</th><th>OLBG id</th><th>OLBG tips page</th><th>Market families originated here</th></tr></thead>
<tbody>{olbg_rows}</tbody></table></div>
<p class="small">Out of scope and never listed here: football/soccer, horse racing, American football, boxing/MMA, cycling and every other OLBG category outside the 15 above.</p>
"""
    (OUT / "olbg.html").write_text(page("OLBG map", "olbg.html", body))

    # ---------------- methodology ----------------
    body = f"""
<h2>Methodology — how every number on this board was produced</h2>
<h3>1. Scope</h3>
<p>Exactly the 15 mandated sports, under OLBG's own taxonomy (<a href="olbg.html">OLBG map</a>). Gaelic Football and Hurling
sit together under Gaelic Sports. Cut-off {CUTOFF}: only matches starting after that instant (or dated after it) are listed.</p>
<h3>2. Fixtures and inputs (nothing fetched live by the site)</h3>
<ul>
<li><b>Cadence layer (93 fixtures)</b>: first-hand official capture 2026-10-23T20:05Z held in <code>data/cadence/</code> — NHL and NBA feeds, MLB stats API, EuroLeague, Cricket Australia, WST, PDC, ATP, PGA TOUR/DP World Tour, GBGB, LNH, LegaVolley/VBL, Premiership Rugby/URC, NRL (Rugby League World Cup), Formula 1 and GAA county sources. Its prices, picks and prose are carried over unchanged; each price still carries its own basis string naming its inputs.</li>
<li><b>Brief NHL layer (12 fixtures, Sat 24 Oct)</b>: fixtures, venues and stored team inputs from <code>data/brief/</code> (capture 16:30Z, official NHL schedule + stats API). Prices were re-originated for this board by the engine in §4 so that one documented method covers the whole Saturday slate; the resulting money-line probabilities agree with the brief desk's own within four points on all twelve games.</li>
<li><b>NHL 25–26 Oct (8 fixtures)</b>: read first-hand from NHL.com tonight; priced only where both clubs have stored inputs (4 games), otherwise listed blank with the reason (flag Q-BLANK).</li>
</ul>
<h3>3. Start times</h3>
<p>Five provenance classes, printed on each row: published UTC/offset (52), venue-local converted with DST-correct rules (18),
session-window starts for darts (8), viewer-zone clocks converted as America/New_York on published triangulation (9, flag Q-TZ1),
and date-only with <code>start_utc</code> left blank (26, flag Q-TZ2). Europe's 25 October clock change is applied by the timezone
database, not by hand.</p>
<h3>4. The added NHL engine (quest layer)</h3>
<p>Expected goals are the simple average of a club's scoring rate and its opponent's conceding rate from the stored inputs,
with a 4% lift for the home club (none at the neutral-site game). A Poisson score matrix settles money line, puck line ∓1.5
and totals 5.5/6.5; a regulation tie is awarded in proportion to expected goals, counts as a one-goal margin and adds one goal
to the total. League mean across the 27 stored club lines: {meta['league_gpg_nhl']} goals. Where the favourite prices shorter
than −250, a band-ceiling alternate is quoted from the totals/puck ladders if one still grades high inside the window — the
same convention the cadence layer uses.</p>
<h3>5. Prices, confidence and the window</h3>
<ul>
<li>Fair decimal = 1/probability; fair American follows from it. No margin, no bookmaker quote anywhere.</li>
<li><b>High</b> ≥70%, <b>medium</b> ≥60%, else <b>low</b>; inherited tier caps (small samples) can only lower a label, never raise it. The labels are probability bands, not a backtested strike rate (flag Q-CONF).</li>
<li>Window test: −250 ≤ fair American ≤ +10000. A fair −250 is 71.43%, so high ∩ window = 70.00–71.43% exactly.</li>
<li>Picks: match-winner favourite per priced match, plus a band alternate where applicable. Top 5 per sport: matches ranked by display-selection probability (in-window preferred), with the best in-window line shown alongside.</li>
</ul>
<h3>6. Written predictions</h3>
<p>At least 30 words each, unique, selection stated in plain words (“X to win”, “Over 171.5”), built only from facts stored
with the fixture (form, scoring rates, rankings, venues). Internal process words are banned from the prose by an automated
check. No piece asserts an injury — no official availability feed beyond the NBA's was readable (flag Q-INJ); NBA rows link
the league report instead of paraphrasing it.</p>
<h3>7. Verification (what was actually checked)</h3>
<ul>
<li>Every fixture, pick, price and fact row carries an https official link; blank values stay blank with a reason.</li>
<li><code>scripts/quest_verify.py</code> recomputes every fair price from its probability, re-derives every window flag and confidence ceiling, checks prediction length/uniqueness/banned words, confirms no start precedes the cut-off, and crawls every generated page for broken local links.</li>
<li>Cross-checks tonight: NHL.com's two published moneylines (flag Q-MKT1), NBA calendar counts (Q-COV1), NHL week strip (Q-COV2), quest-vs-brief money-line agreement within 0.04 on twelve games.</li>
</ul>
<h3>8. Repository review (summary)</h3>
<p>The repository holds 38 overlapping desk directories from earlier sessions, several generations of the same brief, an
append-only 516&nbsp;KB <code>COORDINATION.md</code> that still preserves merge-conflict markers from concurrent rebases
(cadence audit RA-01), legacy pages for sports outside the mandate (RA-02), and older prediction files whose prose would
fail this desk's word rules (RA-03/RA-04). Those layers were left untouched — they belong to other sessions' scopes — and are
disclosed here and in flag CD-PR3 rather than silently superseded. This desk is one more layer; choosing a single
authoritative desk remains an integration decision for the repository owner. Line-by-line detail:
<a href="https://github.com/buffedlizard55-lab/OLBG2/blob/main/research/quest-693dbf40.md">research/quest-693dbf40.md</a>.</p>
"""
    (OUT / "methodology.html").write_text(page("Methodology", "methodology.html", body))

    # ---------------- sources ----------------
    srows = "".join(
        f'<tr><td>{e(s["key"])}</td><td>{e(s["publisher"])}</td>'
        f'<td><a href="{e(s["url"])}" rel="noopener">{e(s["url"])}</a></td>'
        f'<td>{e(s["what"])}</td><td>{e(s["captured_utc"])}</td>'
        f'<td>{e(", ".join(s["desks"]))}</td></tr>' for s in sources)
    body = f"""
<h2>Source ledger — {len(sources)} official sources</h2>
<p>Every capture behind this board. “Official” means the governing body, league, tour or federation that owns the
competition (plus OLBG itself for OLBG claims, and the repository for repository claims). Fixture-level URLs
(for example NHL game-centre pages) appear on the rows they support.</p>
<div class="tw"><table><thead><tr><th>Key</th><th>Publisher</th><th>URL</th><th>Used for</th><th>Captured (UTC)</th><th>Desk</th></tr></thead>
<tbody>{srows}</tbody></table></div>
"""
    (OUT / "sources.html").write_text(page("Sources", "sources.html", body))

    # ---------------- flagged ----------------
    frows = "".join(
        f'<tr><td><b>{e(fl["id"])}</b></td><td>{e(fl["severity"])}</td><td>{e(fl["category"])}</td>'
        f'<td><b>{e(fl["item"])}</b><br>{e(fl["finding"])}</td>'
        f'<td><a href="{e(fl["source_url"])}" rel="noopener">Review source</a></td>'
        f'<td>{e(fl["status"])}{" (carried from " + e(fl["carried_from"]) + ")" if fl.get("carried_from") else ""}</td></tr>'
        for fl in flags)
    body = f"""
<h2>Flagged for Review — {len(flags)} items</h2>
<p>Nothing on this page blocks publication; everything here is published precisely so it can be checked. “Needs review”
means a human should confirm or correct the item against its linked official source. Where a value could not be confirmed,
the cell on the board is blank — this page explains why.</p>
<div class="tw"><table><thead><tr><th>ID</th><th>Severity</th><th>Category</th><th>Finding</th><th>Official source</th><th>Status</th></tr></thead>
<tbody>{frows}</tbody></table></div>
"""
    (OUT / "flagged.html").write_text(page("Flagged for Review", "flagged.html", body))

    n_pages = 10 + len(SPORTS15)
    print(f"wrote {n_pages} pages to quest/ ({len(fixtures)} fixtures, {len(lines)} lines)")


if __name__ == "__main__":
    main()
