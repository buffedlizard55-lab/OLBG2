#!/usr/bin/env python3
"""update_build.py — build the /update/ dashboard from data/update/*.json.

Pages (all self-contained, table-first, every data row carries its official source link):
    update/index.html      dashboard landing
    update/matches.html    full match list (all rows)
    update/picks.html      predictions with write-ups
    update/band.html       in-band selections only
    update/<sport>.html    category subpages for the 17 eligible sports
    update/sources.html    official source registry
    update/methodology.html
    update/flagged.html    "Flagged for Review"
"""
import html
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(ROOT, "data", "update")
OUT = os.path.join(ROOT, "update")

SPORTS = [
    ("tennis", "Tennis"), ("darts", "Darts"), ("snooker", "Snooker"), ("golf", "Golf"),
    ("cricket", "Cricket"), ("baseball", "Baseball"), ("basketball", "Basketball"),
    ("ice-hockey", "Ice Hockey"), ("rugby-union", "Rugby Union"), ("rugby-league", "Rugby League"),
    ("handball", "Handball"), ("volleyball", "Volleyball"), ("aussie-rules", "Aussie Rules"),
    ("motor-racing", "Motor Racing"), ("esports", "Esports"), ("greyhounds", "Greyhounds"),
    ("gaelic-football", "Gaelic Football"),
]
SPORT_TITLES = dict(SPORTS)

CSS = """
:root{--ink:#12253f;--muted:#5b6b7f;--line:#e3e8ee;--accent:#0d5c63;--hot:#b3261e;--warm:#8a5a00;--cool:#1b5e20;--wash:#f6f8fa}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:#fff}
header{background:var(--ink);color:#fff;padding:18px 24px}header h1{margin:0;font-size:21px;letter-spacing:.2px}header .sub{opacity:.8;font-size:13px;margin-top:2px}
nav{background:var(--wash);border-bottom:1px solid var(--line);padding:9px 24px;display:flex;flex-wrap:wrap;gap:3px 14px;font-size:13px}
nav a{color:var(--accent);text-decoration:none;font-weight:600}nav a:hover{text-decoration:underline}
main{max-width:1220px;margin:0 auto;padding:22px 24px 60px}
h2{font-size:19px;margin:26px 0 10px}h3{font-size:16px;margin:20px 0 8px}
p.lede{color:var(--muted);margin:6px 0 16px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0 20px}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:var(--wash);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
tr:nth-child(even) td{background:#fcfdfe}
a.src{color:var(--accent);font-weight:600;text-decoration:none;word-break:break-all}
a.src:hover{text-decoration:underline}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:700;white-space:nowrap}
.p-high{background:#fdecea;color:var(--hot)}.p-medium{background:#fff4e0;color:var(--warm)}.p-low{background:#eef2f6;color:var(--muted)}
.p-ok{background:#e7f4ea;color:var(--cool)}.p-flag{background:#fdecea;color:var(--hot)}
.p-cap{background:#e8f0fe;color:#1a4fa0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:14px 0 22px}
.card{border:1px solid var(--line);border-radius:8px;padding:12px 14px;background:var(--wash)}
.card .num{font-size:24px;font-weight:700}.card .lbl{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.writeup{color:#233246;font-size:13.5px}
small.mut{color:var(--muted)}
.flagitem{border-left:4px solid var(--hot);background:#fffafa;padding:10px 14px;margin:10px 0;border-radius:0 6px 6px 0}
.flagitem .t{font-weight:700}footer{border-top:1px solid var(--line);color:var(--muted);font-size:12px;padding:18px 24px}
.blank{color:#98a4b3;font-style:italic}
"""


def esc(x):
    return html.escape(str(x if x is not None else ""))


def link(url, label=None):
    if not url:
        return '<span class="blank">unverified</span>'
    return f'<a class="src" href="{esc(url)}">{esc(label or url)}</a>'


def conf_pill(conf):
    base = (conf or "low").split()[0]
    cls = {"high": "p-high", "medium": "p-medium", "low": "p-low"}.get(base, "p-low")
    return f'<span class="pill {cls}">{esc(conf)}</span>'


def cap_pill(cap):
    if cap.startswith("this"):
        return '<span class="pill p-ok">fresh capture</span>'
    if cap.startswith("cross-ref"):
        return '<span class="pill p-cap">form cross-ref</span>'
    return '<span class="pill p-cap">inherited</span>'


def page(name, title, body, current=""):
    nav_items = [("index.html", "Dashboard"), ("matches.html", "Matches"), ("picks.html", "Picks"),
                 ("band.html", "In-Band Picks"), ("sources.html", "Sources"),
                 ("methodology.html", "Methodology"), ("flagged.html", "Flagged for Review")]
    sport_nav = "".join(f'<a href="{s}.html"{"" if current != s else ""}>{esc(n)}</a>' for s, n in SPORTS)
    nav = "".join(f'<a href="{u}">{esc(t)}</a>' for u, t in nav_items)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — OLBG2 /update/</title><style>{CSS}</style></head>
<body>
<header><h1>OLBG2 · Updated Match List &amp; Betting Lines</h1>
<div class="sub">Window 22–28 October 2026 · every value from verified official sources · nothing inferred</div></header>
<nav>{nav}<span style="flex-basis:100%;height:0"></span>{sport_nav}</nav>
<main>{body}</main>
<footer>Built by <code>scripts/update_build.py</code> from <code>data/update/</code> · session branch arena/d69dc1c9-olbg2 ·
unverified values are left blank and flagged — never filled by guess.</footer>
</body></html>"""
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write(doc)


def matches_table(rows, with_sport=True):
    head = ("<tr>" + ("<th>Sport</th>" if with_sport else "") +
            "<th>Date</th><th>Time (as rendered)</th><th>Competition</th><th>Match</th><th>Form (home | away)</th>"
            "<th>Win line (our price)</th><th>Pick</th><th>Capture</th><th>Official source</th></tr>")
    out = ["<table>", head]
    for m in rows:
        wm = (m.get("markets") or {}).get("winner") or {}
        pick = m.get("winner_pick") or {}
        if wm.get("home_prob") is not None:
            line = (f"{esc(m['home'])} {wm.get('home_american_str','')} / {esc(m['away'])} {wm.get('away_american_str','')}<br>"
                    f"<small class='mut'>prob {wm.get('home_prob'):.0%}–{wm.get('away_prob'):.0%} · dec {wm.get('home_decimal')} / {wm.get('away_decimal')}</small>")
        elif wm.get("probs"):
            fav = wm.get("favourite")
            line = (f"race-winner model · fav {esc(fav)} {wm.get('favourite_american_str','')}<br>"
                    f"<small class='mut'>see methodology (multi-outcome field)</small>")
        else:
            line = "<span class='blank'>not originated — form unverified</span>"
        if pick:
            pickcell = f"{esc(pick.get('selection'))} {conf_pill(pick.get('confidence'))}<br><small class='mut'>{esc(pick.get('american_str'))}</small>"
        else:
            pickcell = "<span class='blank'>no pick (blank per policy)</span>"
        matchup = esc(m.get("home") or "(field)") + (" vs " + esc(m["away"]) if m.get("away") else "")
        form = f"{esc(m.get('home_summary') or '—')} | {esc(m.get('away_summary') or '—')}"
        out.append("<tr>" + (f"<td>{esc(m.get('sport_name'))}</td>" if with_sport else "") +
                   f"<td>{esc(m.get('date'))}</td><td>{esc(m.get('time') or '')}</td><td>{esc(m.get('competition'))}</td>"
                   f"<td><strong>{matchup}</strong><br><small class='mut'>{esc(m.get('venue') or '')}</small></td>"
                   f"<td>{form}</td><td>{line}</td><td>{pickcell}</td><td>{cap_pill(m.get('capture',''))}</td>"
                   f"<td>{link(m.get('official_url'), 'official')}</td></tr>")
    out.append("</table>")
    return "\n".join(out)


def picks_table(preds):
    out = ["<table><tr><th>Date</th><th>Sport</th><th>Match</th><th>Selection</th><th>Market</th>"
           "<th>Prob / fair odds</th><th>Confidence</th><th>Band</th><th>Prediction write-up</th><th>Official source</th></tr>"]
    for p in sorted(preds, key=lambda x: (x.get("date") or "", x.get("sport") or "")):
        wo = p.get("writeup_origin") or ""
        wu = p.get("writeup") or ""
        wcell = f"<div class='writeup'>{esc(wu)}</div>"
        if wo:
            wcell += f"<small class='mut'>{esc(wo)}</small>"
        if not wu:
            wcell = "<span class='blank'>write-up blank (no verified detail captured)</span>"
        band = "<span class='pill p-ok'>in band</span>" if p.get("in_band") else "<span class='pill p-low'>out of band</span>"
        out.append(f"<tr><td>{esc(p.get('date'))}</td><td>{esc(p.get('sport'))}</td><td>{esc(p.get('matchup'))}</td>"
                   f"<td><strong>{esc(p.get('selection'))}</strong></td><td>{esc(p.get('market'))}</td>"
                   f"<td>{p.get('prob') if p.get('prob') is not None else ''} · {esc(p.get('american_str'))} ({esc(p.get('decimal'))})</td>"
                   f"<td>{conf_pill(p.get('confidence'))}</td><td>{band}</td><td>{wcell}</td>"
                   f"<td>{link(p.get('official_url'), 'official')}</td></tr>")
    out.append("</table>")
    return "\n".join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    matches = json.load(open(os.path.join(UPD, "matches.json")))["matches"]
    preds = json.load(open(os.path.join(UPD, "predictions.json")))["predictions"]
    band = json.load(open(os.path.join(UPD, "band.json")))["picks"]
    flags = json.load(open(os.path.join(UPD, "flagged.json")))["items"]
    sources = json.load(open(os.path.join(UPD, "sources.json")))["sources"]

    hi = [p for p in preds if p.get("confidence") == "high"]
    med = [p for p in preds if p.get("confidence") == "medium"]
    fresh = [m for m in matches if m.get("capture", "").startswith("this")]
    inh = [m for m in matches if m.get("capture", "").startswith("inherited")]
    xref = [m for m in matches if m.get("capture", "").startswith("cross-ref")]

    # ---- index ----
    by_sport = Counter(m["sport"] for m in matches)
    cards = f"""<div class="cards">
<div class="card"><div class="num">{len(matches)}</div><div class="lbl">matches in window</div></div>
<div class="card"><div class="num">{len(fresh)}</div><div class="lbl">fresh captures</div></div>
<div class="card"><div class="num">{len(inh)}</div><div class="lbl">inherited rows</div></div>
<div class="card"><div class="num">{len(preds)}</div><div class="lbl">picks made</div></div>
<div class="card"><div class="num">{len(hi)}</div><div class="lbl">high confidence</div></div>
<div class="card"><div class="num">{len(band)}</div><div class="lbl">in-band selections</div></div>
</div>"""
    sport_rows = "".join(
        f"<tr><td><a class='src' href='{s}.html'>{esc(n)}</a></td><td>{by_sport.get(s, 0)}</td>"
        f"<td>{'covered' if by_sport.get(s) else 'gap — see Flagged'}</td></tr>" for s, n in SPORTS)
    hi_rows = ""
    for p in sorted(hi, key=lambda x: x["date"]):
        prob_str = f"{p['prob']:.0%}" if p.get("prob") is not None else ""
        hi_rows += (f"<tr><td>{esc(p['date'])}</td><td>{esc(p['selection'])}</td><td>{esc(p['matchup'])}</td>"
                    f"<td>{esc(p['american_str'])}</td><td>{esc(prob_str)}</td>"
                    f"<td>{link(p.get('official_url'), 'official')}</td></tr>")
    body = f"""
<h2>Dashboard — window 22–28 October 2026</h2>
<p class="lede">This layer re-captures official league sources during the week of 22 Oct and originates our own
win / handicap / total lines from verified form. Where a sport's official endpoints were unreachable this session,
rows are cross-referenced from the earlier <a class="src" href="../verified/">/verified/</a> layer and clearly
labelled <em>inherited</em>. Unconfirmable values stay blank and land on
<a class="src" href="flagged.html">Flagged for Review</a> — nothing is guessed.</p>
{cards}
<h3>High-confidence picks (win chance ≥ 70%, fair price inside −250…+10000)</h3>
<table><tr><th>Date</th><th>Selection</th><th>Match</th><th>Fair American</th><th>Model prob</th><th>Official source</th></tr>
{hi_rows}</table>
<h3>Coverage by sport</h3>
<table><tr><th>Sport</th><th>Rows</th><th>Status</th></tr>{sport_rows}</table>
<h3>How to read this site</h3>
<p class="lede"><a class="src" href="matches.html">Matches</a> lists every fixture with our originated price;
<a class="src" href="picks.html">Picks</a> adds the selection, the confidence label and the prediction write-up;
<a class="src" href="band.html">In-Band Picks</a> is the subset that qualifies for the odds band;
<a class="src" href="methodology.html">Methodology</a> documents the models and the confidence gate.</p>
"""
    page("index.html", "Dashboard", body)

    # ---- matches ----
    body = ("<h2>Full match list — 22–28 October 2026</h2>"
            "<p class='lede'>Every row carries its official source. Blank cells are values we could not verify — "
            "see <a class='src' href='flagged.html'>Flagged for Review</a>.</p>" + matches_table(matches))
    page("matches.html", "Matches", body)

    # ---- picks ----
    body = ("<h2>Predictions &amp; confidence</h2>"
            "<p class='lede'>Each match we can price gets a winner pick graded low / medium / high. High confidence "
            "requires model win probability ≥ 70% <em>and</em> fair American odds inside −250…+10000; picks above "
            "70% but shorter than −250 are labelled <em>high (out of band)</em> and excluded from the in-band table. "
            "Write-ups are ≥30 words and only use verified facts (players named only where an official feed supplied them).</p>"
            + picks_table(preds))
    page("picks.html", "Picks", body)

    # ---- band ----
    body = ("<h2>In-band selections (fair American −250…+10000)</h2>"
            f"<p class='lede'>{len(band)} selections qualify. High-confidence entries are shown first.</p>"
            + picks_table(sorted(band, key=lambda p: (p.get("confidence") != "high", p.get("date") or ""))))
    page("band.html", "In-Band Picks", body)

    # ---- per sport ----
    for s, name in SPORTS:
        rows = [m for m in matches if m["sport"] == s]
        prows = [p for p in preds if p.get("sport") == s]
        body = f"<h2>{esc(name)} — 22–28 October 2026</h2>"
        if not rows:
            body += ("<p class='lede'>No verified fixture rows for this window. The capture attempts and reasons are "
                     "recorded on <a class='src' href='flagged.html'>Flagged for Review</a> — we do not invent fixtures.</p>")
        else:
            body += f"<p class='lede'>{len(rows)} rows · {len(prows)} picks · sources per row.</p>" + matches_table(rows, with_sport=False)
            if prows:
                body += "<h3>Picks</h3>" + picks_table(prows)
        page(f"{s}.html", name, body, current=s)

    # ---- sources ----
    rows = "".join(f"<tr><td>{esc(s.get('sport'))}</td><td>{link(s.get('url'))}</td><td>{esc((s.get('note') or '')[:160])}</td></tr>"
                   for s in sources)
    body = ("<h2>Official source registry</h2>"
            "<p class='lede'>Every feed touched while building this layer. Consent-walled or client-rendered sources "
            "are flagged on the Flagged page.</p>"
            f"<table><tr><th>Sport</th><th>Official URL</th><th>Note</th></tr>{rows}</table>")
    page("sources.html", "Sources", body)

    # ---- methodology ----
    body = """
<h2>Methodology</h2>
<p class="lede">Session arena/d69dc1c9-olbg2 · window 22–28 Oct 2026 · branch arena/d69dc1c9-olbg2.</p>
<h3>Origination rules</h3>
<ul>
<li><strong>Win match:</strong> Bill James log5 on Laplace-smoothed win percentages (W+1)/(GP+2) from captured W-L(-D)
records; EuroLeague uses a logistic on the standings position rendered by the official widget; darts uses a logistic on
official draw seedings where the bracket rendered them; the F1 race winner uses a 60/40 blend of season and last-five
win shares from the official 2026 results table.</li>
<li><strong>Handicap:</strong> expected margin from captured PF/PA differentials blended with the win probability
(NHL scale 6 goals, URC 14 points, MLB 2.5 runs); priced at the standard ~1.91 two-way. Alternates come from the prior
layer where that layer already priced them (labelled inherited).</li>
<li><strong>Totals:</strong> mean of the two teams' captured per-game combined scoring, rounded to the half. Where no
captured over/under splits exist the price is left even and said so.</li>
<li><strong>Never inferred:</strong> no player names without an official feed, no times/timezones conversions without a
label, no lines where form was not verified. Those rows keep the pick blank and appear on Flagged for Review.</li>
</ul>
<h3>Confidence gate</h3>
<ul>
<li><strong>High:</strong> model win probability ≥ 70% <em>and</em> fair American inside −250…+10000 (70.0–71.4%
maps to roughly −250…−233). A 75% favourite at −300 is honestly labelled <em>high (out of band)</em> and kept out
of the in-band tables.</li>
<li><strong>Medium:</strong> 60–70% (or high-probability out-of-band picks' underlying moneyline where the listed
selection is an alternative handicap carrying its own price).</li>
<li><strong>Low:</strong> below 60%.</li>
</ul>
<h3>Capture vs inherited</h3>
<p class="lede"><em>Fresh capture</em> = fetched from the official league source during this session (NHL score feeds,
MLB Stats API, URC match centre, WST match centre, ATP day schedules, EuroLeague official site, PDC official pages,
F1 official results, TAURON Liga game centre). <em>Form cross-ref</em> = fixture captured fresh, form label borrowed
from the prior /verified/ layer where the fresh feed lacked records (clearly marked on the row). <em>Inherited</em> =
entire row carried from data/verified (PR #82) because no fresh capture was possible (NBA endpoints were down; other
sports exceeded the session's fetch budget). Inherited rows never claim fresh-capture credit.</p>
<h3>Irregularities</h3>
<p class="lede">PDC pages served consent walls (schedule text obtained via search rendering of the official URLs —
rows keep the official links for manual review); Luke Humphries' same-day withdrawal (gastroenteritis, official PDC
statement 22 Oct) replaced him with Kim Huybrechts in the European Championship draw — flagged; URC and EuroLeague and
TAURON Liga times are published exactly as rendered, timezones not inferred.</p>
"""
    page("methodology.html", "Methodology", body)

    # ---- flagged ----
    items = "".join(
        f"<div class='flagitem'><div class='t'>{esc(f.get('item'))} — {esc(f.get('matchup'))} "
        f"<span class='pill p-flag'>{esc(f.get('sport'))}</span></div>"
        f"<div>{esc(f.get('why'))}</div><div style='margin-top:4px'>{link(f.get('link'), 'official source / reference')}</div></div>"
        for f in flags)
    body = (f"<h2>Flagged for Review — {len(flags)} items</h2>"
            "<p class='lede'>Irregularities, gaps and unverified values. None of these block the publish; all remain "
            "visible until a reviewer closes them. Nothing here has been filled in by guesswork.</p>" + items)
    page("flagged.html", "Flagged for Review", body)

    print(f"update/ built: matches={len(matches)} preds={len(preds)} band={len(band)} high={len(hi)} flags={len(flags)}")


if __name__ == "__main__":
    main()
