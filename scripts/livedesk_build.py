#!/usr/bin/env python3
"""Build the live desk site from the committed model and the authored predictions.

The generator is deterministic: it reads data/live_desk/model.json (written on the runner by
scripts/livedesk_model.py) and data/live_desk/predictions.json (written by hand, one entry per
fixture), and writes static HTML.  Re-running it on unchanged inputs produces byte-identical
files, which is what the CI drift check relies on.

Pages
    live-desk/index.html            executive summary
    live-desk/picks.html            every graded selection
    live-desk/matches.html          every OLBG fixture, with its verification state
    live-desk/predictions.html      the written predictions
    live-desk/sports/index.html     the 15 sport categories
    live-desk/sports/<slug>.html    one page per sport
    live-desk/sources.html          every captured URL with status, time and digest
    live-desk/flagged.html          unverified rows and failed reads
    live-desk/methodology.html      how a price is originated, and what is not claimed
    live-desk/archive.html          the earlier research layers, kept for provenance
    index.html                      landing page with the executive summary
"""
from __future__ import annotations

import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "live_desk"
OUT = ROOT / "live-desk"
MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
PRED_PATH = DATA / "predictions.json"
PREDICTIONS = json.loads(PRED_PATH.read_text(encoding="utf-8")) if PRED_PATH.exists() else {"items": []}

SPORTS = MODEL["meta"]["scope"]
e = html.escape

CSS = """
:root{--ink:#0f172a;--muted:#5b6472;--line:#e3e7ee;--bg:#f7f9fc;--card:#fff;
--accent:#0e7490;--high:#0f766e;--med:#a16207;--low:#6b7280;--flag:#b45309;--bad:#b91c1c}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.site{background:#fff;border-bottom:1px solid var(--line)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.top{display:flex;flex-wrap:wrap;align-items:center;gap:18px;padding:14px 0}
.brand{font-weight:700;font-size:17px;letter-spacing:-.2px;margin-right:auto}
.brand span{color:var(--muted);font-weight:500;font-size:13px;display:block;letter-spacing:0}
nav.main{display:flex;flex-wrap:wrap;gap:14px;font-size:14px}
nav.main a{color:var(--muted)}
nav.main a.on{color:var(--ink);font-weight:600}
.hero{padding:26px 0 6px}
h1{font-size:28px;margin:0 0 6px;letter-spacing:-.4px}
h2{font-size:19px;margin:30px 0 10px}
h3{font-size:15px;margin:18px 0 8px}
p.lead{color:var(--muted);max-width:820px;margin:0 0 8px}
.stamp{font-size:13px;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card .n{font-size:24px;font-weight:700;letter-spacing:-.5px}
.card .l{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f5f9;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid}
.pill.high{color:var(--high);border-color:#99e0d6;background:#ecfdf5}
.pill.medium{color:var(--med);border-color:#f3d9a4;background:#fffbeb}
.pill.low{color:var(--low);border-color:#dfe3e8;background:#f8fafc}
.pill.band{color:#1d4ed8;border-color:#c7d2fe;background:#eef2ff}
.pill.out{color:#9a3412;border-color:#fed7aa;background:#fff7ed}
.pill.ok{color:var(--high);border-color:#99e0d6;background:#ecfdf5}
.pill.warn{color:var(--flag);border-color:#fcd34d;background:#fffbeb}
.note{background:#fff;border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:12px 14px;margin:16px 0;color:#243044}
.note.warn{border-left-color:var(--flag)}
.note.bad{border-left-color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.pred{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px}
.pred h3{margin:0 0 4px;font-size:16px}
.pred .meta{font-size:12px;color:var(--muted);margin-bottom:8px}
.pred .facts{font-size:13px;color:#334155;margin:10px 0 0;padding-left:16px}
.pred .facts li{margin:2px 0}
.pred .src{font-size:12px;margin-top:10px;color:var(--muted);word-break:break-all}
footer.site{border-top:1px solid var(--line);margin-top:40px;padding:18px 0;color:var(--muted);font-size:13px;background:#fff}
.small{font-size:12px;color:var(--muted)}
.flags{color:var(--flag);font-weight:600}
code{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:12px}
.scroll{overflow-x:auto}
@media (max-width:700px){h1{font-size:23px}th,td{padding:8px}}
"""

NAV = [
    ("index.html", "Summary"),
    ("picks.html", "Picks"),
    ("matches.html", "Matches"),
    ("predictions.html", "Predictions"),
    ("sports/index.html", "Sports"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "Method"),
    ("archive.html", "Archive"),
]


def page(title: str, body: str, here: str, root: str = "") -> str:
    links = "".join(
        f'<a href="{root}{href}"{" class=\'on\'" if href == here else ""}>{e(label)}</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · OLBG2 live desk</title>
<link rel="stylesheet" href="{root}assets/style.css">
</head><body>
<header class="site"><div class="wrap"><div class="top">
<div class="brand">OLBG2 live desk<span>Fifteen sports · own lines · dated evidence</span></div>
<nav class="main">{links}</nav>
</div></div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">
Every row links to the page it was read from. Nothing on this site is a bookmaker quote presented as
our own number, and no value is filled in when the source did not carry it.
</div></footer>
</body></html>
"""


def slug(sport: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", sport.lower()).strip("-")


def am(v) -> str:
    if v is None:
        return "—"
    return f"+{v}" if v > 0 else str(v)


def pct(p) -> str:
    return "—" if p is None else f"{100*p:.1f}%"


def pill(conf) -> str:
    if not conf:
        return '<span class="pill low">unrated</span>'
    return f'<span class="pill {conf}">{conf}</span>'


def band(v) -> str:
    if v is None:
        return "—"
    return '<span class="pill band">in window</span>' if v else '<span class="pill out">outside</span>'


def verified(v) -> str:
    return '<span class="pill ok">official</span>' if v else '<span class="pill warn">OLBG only</span>'


def by_sport() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {s: [] for s in SPORTS}
    for ev in MODEL["events"]:
        out.setdefault(ev["sport"], []).append(ev)
    return out


def when(ev: dict) -> str:
    if ev.get("start_utc"):
        return e(ev["start_utc"].replace("T", " ").replace("Z", " UTC"))
    if (ev.get("official") or {}).get("start_local"):
        return e(ev["official"]["start_local"]) + " <span class='small'>(venue local)</span>"
    return "—"


def pick_row(ev: dict, root: str = "") -> str:
    p = ev.get("pick") or {}
    return (
        "<tr>"
        f"<td>{when(ev)}</td>"
        f"<td><a href=\"{root}sports/{slug(ev['sport'])}.html\">{e(ev['sport'])}</a></td>"
        f"<td>{e(ev['name'])}<div class='small'>{e(ev.get('competition') or '')}</div></td>"
        f"<td><strong>{e(p.get('selection',''))}</strong><div class='small'>{e(p.get('market',''))}</div></td>"
        f"<td class='num'>{pct(p.get('probability'))}</td>"
        f"<td class='num'>{am(p.get('fair_american'))}</td>"
        f"<td>{pill(p.get('confidence'))}</td>"
        f"<td>{band(p.get('in_band'))}</td>"
        f"<td>{e(ev.get('tier',''))}</td>"
        f"<td>{'<a href=\"%s\">OLBG</a>' % e(ev['olbg_url']) if ev.get('olbg_url') else '—'}"
        f" {(('<a href=\"%s\">official</a>' % e((ev.get('official') or {}).get('source_url'))) if (ev.get('official') or {}).get('source_url') else '')}</td>"
        "</tr>"
    )


def ranked_picks() -> list[dict]:
    order = {"high": 0, "medium": 1, "low": 2, None: 3}
    rows = [ev for ev in MODEL["events"] if ev.get("pick")]
    rows.sort(key=lambda ev: (
        0 if ev["pick"]["in_band"] else 1,
        order.get(ev["pick"]["confidence"], 3),
        -ev["pick"]["probability"],
    ))
    return rows


def summary_stats() -> dict:
    evs = MODEL["events"]
    picks = [x for x in evs if x.get("pick")]
    high = [x for x in picks if x["pick"]["confidence"] == "high"]
    inband_high = [x for x in high if x["pick"]["in_band"]]
    return {
        "events": len(evs),
        "sports": len({x["sport"] for x in evs if x.get("pick")}) if picks else 0,
        "picks": len(picks),
        "high": len(high),
        "inband_high": len(inband_high),
        "verified": sum(1 for x in evs if x["official_verified"]),
        "predictions": len(PREDICTIONS.get("items", [])),
        "flagged": len(MODEL.get("review", [])),
    }


def coverage_rows() -> str:
    groups = by_sport()
    preds = PREDICTIONS.get("items", [])
    pred_counts: dict[str, int] = {}
    for p in preds:
        pred_counts[p["sport"]] = pred_counts.get(p["sport"], 0) + 1
    rows = []
    for sport in SPORTS:
        evs = groups.get(sport, [])
        picks = [x for x in evs if x.get("pick")]
        high = [x for x in picks if x["pick"]["confidence"] == "high"]
        tiers = sorted({x["tier"] for x in picks}) or ["no-basis"]
        rows.append(
            "<tr>"
            f"<td><a href=\"sports/{slug(sport)}.html\">{e(sport)}</a></td>"
            f"<td class='num'>{len(evs)}</td>"
            f"<td class='num'>{len(picks)}</td>"
            f"<td class='num'>{len(high)}</td>"
            f"<td class='num'>{pred_counts.get(sport,0)} / 5</td>"
            f"<td>{e(', '.join(tiers))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- pages
def build_index(root: str = "") -> str:
    st = summary_stats()
    top = ranked_picks()[:8]
    rows = "".join(pick_row(ev, root) for ev in top)
    meta = MODEL["meta"]
    cards = f"""
<div class="cards">
  <div class="card"><div class="n">{st['events']}</div><div class="l">OLBG fixtures in scope</div></div>
  <div class="card"><div class="n">{st['picks']}</div><div class="l">graded selections</div></div>
  <div class="card"><div class="n">{st['high']}</div><div class="l">high confidence</div></div>
  <div class="card"><div class="n">{st['inband_high']}</div><div class="l">high and inside -250…+10000</div></div>
  <div class="card"><div class="n">{st['verified']}</div><div class="l">official fixture confirmed</div></div>
  <div class="card"><div class="n">{st['predictions']}</div><div class="l">written predictions</div></div>
</div>"""
    here = f"{root}index.html"
    body = f"""
<div class="hero">
<h1>Today's desk: every OLBG match in the fifteen sports we cover, priced our way</h1>
<p class="lead">This is the executive summary. It answers three questions in order: which matches are on,
what we would pay on each of them, and which written predictions are ready to read. Every number is
traceable to the page named beside it.</p>
<p class="stamp">Capture: {e(meta['captured_at'])} · {st['events']} fixtures · {len(SPORTS)} sports in scope ·
{st['flagged']} review items</p>
</div>
{cards}
<h2>Highest confidence picks</h2>
<p class="lead">Sorted by price window first, then confidence, then probability. A high-confidence row
must rest on an official numeric input; a row built only from OLBG's published tip share can never be
labelled high, and says so in the basis column.</p>
<div class="scroll"><table>
<thead><tr><th>Start</th><th>Sport</th><th>Match</th><th>Selection</th><th class="num">Our chance</th>
<th class="num">Our price</th><th>Confidence</th><th>Window</th><th>Basis</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="small"><a href="{root}picks.html">See every graded selection →</a></p>

<h2>Coverage by sport</h2>
<div class="scroll"><table>
<thead><tr><th>Sport</th><th class="num">Fixtures</th><th class="num">Priced</th><th class="num">High</th>
<th class="num">Predictions</th><th>Probability sources used</th></tr></thead>
<tbody>{coverage_rows()}</tbody></table></div>
<p class="small">A prediction count below five is a shortfall that is explained on
<a href="{root}flagged.html">Flagged for review</a>, not hidden.</p>
{shortfall_note(root)}
"""
    return page("Executive summary", body, here, root)


def shortfall_note(root: str) -> str:
    groups = by_sport()
    preds: dict[str, int] = {}
    for p in PREDICTIONS.get("items", []):
        preds[p["sport"]] = preds.get(p["sport"], 0) + 1
    zero = [s for s in SPORTS if not preds.get(s)]
    fewer = [f"{s} ({preds.get(s,0)})" for s in SPORTS if 0 < preds.get(s, 0) < 5]
    nofix = [s for s in SPORTS if not groups.get(s)]
    bits = []
    if nofix:
        bits.append("No OLBG fixture was listed at capture time for: " + ", ".join(nofix) + ".")
    if fewer:
        bits.append("Fewer than five written predictions: " + ", ".join(fewer) + ".")
    if zero:
        bits.append("No written prediction yet: " + ", ".join(zero) + ".")
    if not bits:
        return ""
    return ('<div class="note warn"><strong>Where this desk is short.</strong> ' + " ".join(bits) +
            ' Each case is itemised with its reason and source on the '
            f'<a href="{root}flagged.html">review page</a>.</div>')


def build_picks() -> str:
    groups = by_sport()
    parts = ["<div class='hero'><h1>Every graded selection</h1>"
             "<p class='lead'>One row per fixture. The selection is the OLBG-listed market we price; the "
             "price is ours, from the basis named. Quoted OLBG prices are shown beside it for comparison only."
             "</p></div>"]
    for sport in SPORTS:
        evs = [x for x in groups.get(sport, []) if x.get("pick")]
        if not evs:
            continue
        rows = "".join(
            "<tr>"
            f"<td>{when(ev)}</td><td>{e(ev['name'])}<div class='small'>{e(ev.get('competition') or '')}</div></td>"
            f"<td>{e(ev['pick']['selection'])}<div class='small'>{e(ev['pick']['market'])}</div></td>"
            f"<td class='num'>{pct(ev['pick']['probability'])}</td>"
            f"<td class='num'>{am(ev['pick']['fair_american'])}<div class='small'>dec {ev['pick']['fair_decimal']}</div></td>"
            f"<td class='num'>{e(ev['pick'].get('quoted_american') or '—')}</td>"
            f"<td>{pill(ev['pick']['confidence'])}</td><td>{band(ev['pick']['in_band'])}</td>"
            f"<td class='small'>{e(ev.get('tier',''))}<br>{e(ev.get('basis_detail') or '')}</td>"
            f"<td>{'<a href=\"%s\">OLBG</a>' % e(ev['olbg_url']) if ev.get('olbg_url') else '—'}</td>"
            "</tr>"
            for ev in sorted(evs, key=lambda x: x["start_utc"] or "")
        )
        parts.append(f"<h2>{e(sport)}</h2><div class='scroll'><table><thead><tr><th>Start</th><th>Match</th>"
                     "<th>Selection</th><th class='num'>Our chance</th><th class='num'>Our price</th>"
                     "<th class='num'>OLBG quote</th><th>Confidence</th><th>Window</th><th>Basis</th>"
                     f"<th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>")
    return page("Picks", "".join(parts), "picks.html")


def build_matches() -> str:
    groups = by_sport()
    parts = ["<div class='hero'><h1>Matches listed on OLBG</h1>"
             "<p class='lead'>The fixture universe is exactly what OLBG listed at capture time. The "
             "verification column says whether both participants were also found on the governing body's "
             "own page; if not, the row keeps its OLBG link and is counted on the review page.</p></div>"]
    for sport in SPORTS:
        evs = groups.get(sport, [])
        if not evs:
            continue
        rows = "".join(
            "<tr>"
            f"<td>{when(ev)}</td>"
            f"<td>{e(ev['competition'] or '—')}</td>"
            f"<td>{e(ev['name'])}</td>"
            f"<td>{e(ev['primary_tip']['selection'])}<div class='small'>{e(ev['primary_tip']['market'])} "
            f"@ {e(ev['primary_tip']['decimal'] or '—')}</div></td>"
            f"<td>{verified(ev['official_verified'])}</td>"
            f"<td class='small'>{e(ev.get('tier',''))}</td>"
            f"<td>{'<a href=\"%s\">OLBG</a>' % e(ev['olbg_url']) if ev.get('olbg_url') else '—'}"
            f"{' · <a href=\"%s\">official</a>' % e((ev.get('official') or {}).get('source_url')) if (ev.get('official') or {}).get('source_url') else ''}</td>"
            "</tr>"
            for ev in sorted(evs, key=lambda x: x["start_utc"] or "")
        )
        parts.append(f"<h2>{e(sport)} <span class='small'>({len(evs)})</span></h2>"
                     "<div class='scroll'><table><thead><tr><th>Start</th><th>Competition</th><th>Match</th>"
                     "<th>OLBG tip</th><th>Verification</th><th>Basis</th><th>Links</th></tr></thead>"
                     f"<tbody>{rows}</tbody></table></div>")
    return page("Matches", "".join(parts), "matches.html")


def build_predictions() -> str:
    items = PREDICTIONS.get("items", [])
    head = ("<div class='hero'><h1>Written predictions</h1>"
            "<p class='lead'>Each entry names the selection in the first line, then the evidence behind it. "
            "The facts listed under each write-up are the values the text relies on; the source line beneath "
            "them links the page each value was read from.</p>"
            f"<p class='stamp'>{len(items)} predictions · minimum 30 words · one per fixture</p></div>")
    if not items:
        return page("Predictions", head + "<div class='note warn'>No prediction file yet.</div>",
                    "predictions.html")
    cards = []
    for p in items:
        facts = "".join(f"<li>{e(f)}</li>" for f in p.get("facts", []))
        srcs = " · ".join(f'<a href="{e(u)}">{e(u)}</a>' for u in p.get("sources", []))
        cards.append(
            f"<div class='pred'><h3>{e(p['headline'])}</h3>"
            f"<div class='meta'>{e(p['sport'])} · {e(p.get('competition',''))} · {e(p.get('start',''))} · "
            f"{pill(p.get('confidence'))} · our price {am(p.get('fair_american'))} · {pct(p.get('probability'))}</div>"
            f"<p><strong>{e(p['selection'])}</strong> — {e(p['body'])}</p>"
            f"<ul class='facts'>{facts}</ul><div class='src'>Sources: {srcs}</div></div>"
        )
    grouped: dict[str, list[str]] = {}
    for p, card in zip(items, cards):
        grouped.setdefault(p["sport"], []).append(card)
    body = [head]
    for sport in SPORTS:
        if sport in grouped:
            body.append(f"<h2>{e(sport)}</h2><div class='grid'>{''.join(grouped[sport])}</div>")
    return page("Predictions", "".join(body), "predictions.html")


def build_sports_index() -> str:
    rows = "".join(
        f"<tr><td><a href=\"{slug(sport)}.html\">{e(sport)}</a></td>"
        f"<td class='num'>{len(by_sport().get(sport, []))}</td>"
        f"<td class='num'>{len([x for x in by_sport().get(sport, []) if x.get('pick')])}</td>"
        f"<td class='num'>{len([x for x in by_sport().get(sport, []) if x.get('official_verified')])}</td></tr>"
        for sport in SPORTS
    )
    body = ("<div class='hero'><h1>Sport categories</h1>"
            "<p class='lead'>The fifteen sports named in the brief. Gaelic Football and Hurling are shown "
            "together under Gaelic Sports, as OLBG lists them.</p></div>"
            "<div class='scroll'><table><thead><tr><th>Sport</th><th class='num'>Fixtures</th>"
            f"<th class='num'>Priced</th><th class='num'>Officially confirmed</th></tr></thead><tbody>{rows}</tbody></table></div>")
    return page("Sports", body, "sports/index.html")


def build_sport(sport: str) -> str:
    evs = sorted(by_sport().get(sport, []), key=lambda x: x["start_utc"] or "")
    preds = [p for p in PREDICTIONS.get("items", []) if p["sport"] == sport]
    parts = [f"<div class='hero'><h1>{e(sport)}</h1>"
             f"<p class='lead'>{len(evs)} fixtures listed on OLBG at capture time, "
             f"{len([x for x in evs if x.get('pick')])} priced, "
             f"{len([x for x in evs if x.get('official_verified')])} confirmed on the governing body's own feed.</p></div>"]
    if not evs:
        parts.append("<div class='note warn'>No OLBG fixture in this sport at the capture time. "
                     "The desk lists a sport only when OLBG lists a match in it.</div>")
    else:
        rows = "".join(
            "<tr>"
            f"<td>{when(ev)}</td><td>{e(ev['name'])}<div class='small'>{e(ev['competition'] or '')}</div></td>"
            f"<td>{e(ev['primary_tip']['selection'])}<div class='small'>{e(ev['primary_tip']['market'])}</div></td>"
            f"<td>{pct((ev.get('pick') or {}).get('probability'))}</td>"
            f"<td>{am((ev.get('pick') or {}).get('fair_american'))}</td>"
            f"<td>{pill((ev.get('pick') or {}).get('confidence'))}</td>"
            f"<td>{verified(ev['official_verified'])}</td>"
            f"<td>{'<a href=\"%s\">OLBG</a>' % e(ev['olbg_url']) if ev.get('olbg_url') else '—'}</td>"
            "</tr>" for ev in evs
        )
        parts.append("<div class='scroll'><table><thead><tr><th>Start</th><th>Match</th><th>OLBG tip</th>"
                     "<th class='num'>Our chance</th><th class='num'>Our price</th><th>Confidence</th>"
                     f"<th>Verification</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>")
    if preds:
        cards = "".join(
            f"<div class='pred'><h3>{e(p['headline'])}</h3><div class='meta'>"
            f"{pill(p.get('confidence'))} · {am(p.get('fair_american'))}</div>"
            f"<p><strong>{e(p['selection'])}</strong> — {e(p['body'])}</p>"
            f"<ul class='facts'>{''.join('<li>%s</li>' % e(f) for f in p.get('facts', []))}</ul>"
            f"<div class='src'>Sources: {' · '.join('<a href=\"%s\">%s</a>' % (e(u), e(u)) for u in p.get('sources', []))}</div></div>"
            for p in preds
        )
        parts.append(f"<h2>Written predictions</h2><div class='grid'>{cards}</div>")
    else:
        parts.append("<div class='note warn'>No written prediction for this sport. A write-up needs an "
                     "official numeric input for the specific fixture; see the review page for what was "
                     "and was not available.</div>")
    return page(sport, "".join(parts), "sports/index.html", root="../")


def build_sources() -> str:
    pages = MODEL["meta"]["olbg_pages"]
    rows = []
    for key, c in sorted(pages.items()):
        rows.append(f"<tr><td>{e(key)}</td><td>{e(c.get('url') or '')}</td><td class='num'>{c.get('status')}</td>"
                    f"<td class='num'>{c.get('bytes') or ''}</td><td class='num'>{c.get('objects')}</td>"
                    f"<td class='small'>{e(c.get('captured_at') or '')}</td></tr>")
    texts = MODEL["meta"].get("text_sources", {})
    trows = []
    for sport, srcs in texts.items():
        for s in srcs:
            trows.append(f"<tr><td>{e(sport)}</td><td>{e(s['key'])}</td><td><a href='{e(s['url'])}'>{e(s['url'])}</a></td>"
                         f"<td class='num'>{s.get('chars')}</td><td class='num'>{e(s.get('sha256') or '')}</td>"
                         f"<td class='small'>{e(s.get('captured_at') or '')}</td></tr>")
    ratings = MODEL["meta"]["ratings"]
    rrows = [
        ("NHL club standings", ratings.get("nhl_standings_url"), ratings.get("nhl_standings_captured_at")),
        ("MLB schedule", ratings.get("mlb_schedule_url"), ""),
        ("EuroLeague standings", ratings.get("euroleague_standings_url"), ""),
        ("WTA singles rankings", ratings.get("wta_rankings_url"), f"{ratings.get('wta_players_parsed')} players parsed"),
        ("F1 drivers' standings", ratings.get("f1_standings_url"), f"{ratings.get('f1_drivers_parsed')} drivers parsed"),
    ]
    rrows = "".join(f"<tr><td>{e(a)}</td><td><a href='{e(u or '')}'>{e(u or '')}</a></td><td class='small'>{e(str(b))}</td></tr>"
                    for a, u, b in rrows)
    body = f"""<div class='hero'><h1>Sources</h1>
<p class='lead'>Every read this desk relies on, with its status, its size, the UTC time it was taken and the
first characters of its SHA-256 so a later read can be compared.</p>
<p class='stamp'>All reads were taken once each by <code>scripts/livedesk_collect.py</code> on a GitHub-hosted
runner at {e(MODEL['meta']['captured_at'])}; the raw bodies are kept as a workflow artifact, not as repository content.</p></div>
<h2>OLBG listings</h2>
<div class='scroll'><table><thead><tr><th>Key</th><th>URL</th><th class='num'>HTTP</th><th class='num'>Bytes</th>
<th class='num'>Tips</th><th>Read at</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>Official rating inputs</h2>
<div class='scroll'><table><thead><tr><th>Input</th><th>URL</th><th>Note</th></tr></thead><tbody>{rrows}</tbody></table></div>
<h2>Official pages consulted for verification</h2>
<div class='scroll'><table><thead><tr><th>Sport</th><th>Key</th><th>URL</th><th class='num'>Text chars</th>
<th class='num'>SHA-256</th><th>Read at</th></tr></thead><tbody>{''.join(trows)}</tbody></table></div>
"""
    return page("Sources", body, "sources.html")


def build_flagged() -> str:
    review = MODEL.get("review", [])
    fails = [c for c in MODEL["meta"]["olbg_pages"].items() if c[1].get("status") != 200]
    rows = "".join(
        f"<tr><td>{e(r['sport'])}</td><td>{e(r['event'])}</td><td class='small'>{e(r['start_utc'] or '')}</td>"
        f"<td>{e(r['issue'])}</td>"
        f"<td>{'<a href=\"%s\">OLBG</a>' % e(r['olbg_url']) if r.get('olbg_url') else '—'}"
        f"{''.join('<br><a href=\"%s\">official page</a>' % e(u) for u in (r.get('sources') or [])[:2])}</td></tr>"
        for r in review
    )
    body = f"""<div class='hero'><h1>Flagged for review</h1>
<p class='lead'>Anything that could not be confirmed from an official page is listed here with the link that
was checked. A row on this page is published, not deleted, and it never carries an invented value.</p></div>
<div class='cards'>
<div class='card'><div class='n'>{len(review)}</div><div class='l'>fixtures without an official feed confirmation</div></div>
<div class='card'><div class='n'>{len(fails)}</div><div class='l'>OLBG listing failures</div></div>
</div>
<h2>Fixtures awaiting official confirmation</h2>
<div class='scroll'><table><thead><tr><th>Sport</th><th>Fixture</th><th>Start</th><th>What is missing</th>
<th>Links</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>OLBG read failures</h2>
<div class='scroll'><table><thead><tr><th>Key</th><th>URL</th><th class='num'>HTTP</th></tr></thead>
<tbody>{''.join(f"<tr><td>{e(k)}</td><td>{e(v.get('url') or '')}</td><td class='num'>{v.get('status')}</td></tr>" for k, v in fails)}</tbody></table></div>
"""
    return page("Flagged for review", body, "flagged.html")


def build_methodology() -> str:
    p = MODEL["meta"]["ratings"]["parameters"]
    body = f"""<div class='hero'><h1>Method</h1>
<p class='lead'>How a match gets on this desk, how a price is originated, and what the desk does not claim.</p></div>
<h2>1. The fixture list is OLBG's</h2>
<p>The desk reads the sixteen OLBG sport hub pages that cover the fifteen requested sports (Gaelic Football and
Hurling are the two OLBG pages behind Gaelic Sports) and keeps every upcoming event with a quoted selection.
An event is dropped only if OLBG itself marks it expired. Nothing is added from a governing body that OLBG
did not list.</p>
<h2>2. Verification</h2>
<p>For ice hockey, baseball, basketball, tennis and motor racing the desk also reads the official feed and
matches the participants. Those rows are marked <span class='pill ok'>official</span>. Every other row keeps
its OLBG link, is marked <span class='pill warn'>OLBG only</span>, and is listed on the review page. The
official pages that were consulted are named on the sources page with the size of the text read from each.</p>
<h2>3. Our price, not OLBG's</h2>
<p>OLBG quotes one price for the selection it tips. That number is shown as <em>OLBG quote</em> and is never
reused as our line. Our number is produced as follows.</p>
<table><thead><tr><th>Sport</th><th>Formula</th><th>Parameter</th></tr></thead><tbody>
<tr><td>Ice Hockey</td><td>logistic(scale × (goal difference per game, home − away) + home edge)</td><td>{p['nhl_scale']} · {p['nhl_home_edge']}</td></tr>
<tr><td>Baseball</td><td>logistic(scale × (run difference per game) + home edge + era weight × (ERA_away − ERA_home)/9)</td><td>{p['mlb_scale']} · {p['mlb_home_edge']} · {p['mlb_era_weight']}</td></tr>
<tr><td>Basketball</td><td>normal CDF((scale × point-difference edge + home edge) / sigma)</td><td>{p['el_scale']} · {p['el_home_edge']} · {p['el_sigma']}</td></tr>
<tr><td>Tennis</td><td>logistic(scale × (ln points − ln opponent points)), WTA singles ranking points</td><td>{p['tennis_scale']}</td></tr>
<tr><td>Motor racing</td><td>softmax over entered drivers of championship points / scale</td><td>{p['f1_scale']}</td></tr>
</tbody></table>
<p>Where none of those inputs exists, the desk falls back to OLBG's published tip share, shrunk halfway to an
even split, and labels the row <code>crowd-consensus</code>. Where even that is absent the fixture is
published with no price at all.</p>
<h2>4. Confidence and the price window</h2>
<p><strong>High</strong> requires a probability of at least 70% <em>and</em> an official numeric input.
<strong>Medium</strong> is 60–70% (or any consensus row at 60%+). Everything else is <strong>low</strong>. The
price window is shown separately: a fair price inside −250 to +10000 is marked <em>in window</em>. A 75%
favourite is priced near −300, which is outside the window while still being a high-confidence pick — both
facts are printed rather than one replacing the other.</p>
<h2>5. What this desk does not claim</h2>
<ul><li>It is not a bookmaker feed and it does not place bets.</li>
<li>It does not claim to hold every market OLBG offers; it prices the selection OLBG publishes for each event.</li>
<li>It does not claim injuries, team news or line-ups unless an official page in the sources table carried them.</li>
<li>It does not convert venue-local tip times to UTC; where the league serves local time, the row says so.</li></ul>
"""
    return page("Method", body, "methodology.html")


def build_archive() -> str:
    layers = [
        ("../site/", "Evidence desk v2", "The first audit layer: 25 NHL/NBA fixtures, 64 markets, 4 picks.", "2026-10-21"),
        ("../desk/", "15-sport desk", "An earlier desk built on the same OLBG captures with its own pricing notes.", "2026-10-23"),
        ("../brief/", "Daily brief", "113 fixtures from 22 official reads, 39 write-ups.", "2026-10-23"),
        ("../olbg/", "OLBG discovery desk", "OLBG taxonomy and URL schema notes, 94 rows.", "2026-10-23"),
        ("../cadence/", "Cadence", "93 fixture records, 728 originated prices.", "2026-10-23"),
        ("../master/", "Consolidated master", "235 matches joined to official captures.", "2026-10-23"),
        ("../monitor/", "Evidence monitor", "Unattended collection diagnostics.", "2026-10-23"),
        ("../atlas/", "Atlas", "15-sport first-hand desk.", "2026-10-23"),
        ("../ledger/", "Ledger", "First-hand capture ledger with source registry.", "2026-10-23"),
    ]
    rows = "".join(f"<tr><td><a href='{e(h)}'>{e(n)}</a></td><td>{e(d)}</td><td class='small'>{e(s)}</td></tr>"
                   for h, n, d, s in layers)
    body = ("<div class='hero'><h1>Archive</h1><p class='lead'>Earlier research layers are kept for "
            "provenance and are not part of today's desk. Their counts are dated and are never added to "
            "the numbers on this site.</p></div>"
            "<div class='scroll'><table><thead><tr><th>Layer</th><th>What it is</th><th>Dated</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")
    return page("Archive", body, "archive.html")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "assets" / "style.css", CSS)
    write(OUT / "index.html", build_index())
    write(OUT / "picks.html", build_picks())
    write(OUT / "matches.html", build_matches())
    write(OUT / "predictions.html", build_predictions())
    write(OUT / "sports" / "index.html", build_sports_index())
    for sport in SPORTS:
        write(OUT / "sports" / f"{slug(sport)}.html", build_sport(sport))
    write(OUT / "sources.html", build_sources())
    write(OUT / "flagged.html", build_flagged())
    write(OUT / "methodology.html", build_methodology())
    write(OUT / "archive.html", build_archive())

    # The repository root is the landing page. It repeats the executive summary and links into
    # the desk, so a visitor who lands on the Pages URL sees the answer first.
    root_html = build_index(root="live-desk/").replace('href="live-desk/assets/style.css"',
                                                       'href="live-desk/assets/style.css"')
    write(ROOT / "index.html", root_html.replace("live-desk/index.html", "index.html"))
    print(f"built {len(list(OUT.rglob('*.html')))} desk pages + root index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
