#!/usr/bin/env python3
"""Render the /now/ desk: one clean dashboard, an executive summary first, and one page
per sport. Every data row carries a link to the official page it came from.

Pages: index, picks, predictions, matches, lines, band, top5, olbg, checks, sources,
methodology, flagged, sports/index + 15 sport pages, assets/style.css, assets/app.js.

The 22:32Z first-hand hub and official page rechecks are committed in
``data/final-desk/rechecks.json``, copied to ``data/now/checks.json`` by now_seed.py and
published here. Output is deterministic: same data in, byte-identical pages out.
"""
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "now"
OUT = ROOT / "now"
AS_OF = "2026-10-24T22:32:00Z"
SHOWN_DATE = "24 October 2026"

SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
SLUG = {
    "Golf": "golf", "Volleyball": "volleyball", "Rugby Union": "rugby-union",
    "Cricket": "cricket", "Snooker": "snooker", "Darts": "darts", "Baseball": "baseball",
    "Gaelic Sports": "gaelic-sports", "Greyhounds": "greyhounds", "Tennis": "tennis",
    "Motor Racing": "motor-racing", "Handball": "handball", "Ice Hockey": "ice-hockey",
    "Basketball": "basketball", "Rugby League": "rugby-league",
}
NAV = [
    ("index.html", "Executive summary"),
    ("picks.html", "Picks"),
    ("predictions.html", "Written predictions"),
    ("top5.html", "Top 5 by sport"),
    ("matches.html", "All matches"),
    ("lines.html", "Our lines"),
    ("band.html", "Odds band"),
    ("sports/index.html", "By sport"),
    ("olbg.html", "OLBG list"),
    ("checks.html", "Source checks"),
    ("sources.html", "Sources"),
    ("methodology.html", "Method"),
    ("flagged.html", "Flagged for review"),
]


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def host(url: str) -> str:
    if not url:
        return ""
    body = url.split("//", 1)[-1]
    return body.split("/")[0]


def src(url: str, label: str | None = None) -> str:
    if not url:
        return '<span class="tiny">no link recorded</span>'
    return (f'<a href="{esc(url)}" target="_blank" rel="noopener">'
            f'{esc(label or host(url))}</a>')


def badge(conf: str) -> str:
    return f'<span class="badge {esc(conf)}">{esc(conf)}</span>'


def score_chip(score) -> str:
    """The 0-10 number, coloured like the grade it belongs to."""
    if score is None:
        return '<span class="tiny">—</span>'
    tone = "high" if score >= 7 else ("medium" if score >= 5.5 else "low")
    return f'<span class="score {tone}">{score:.1f}<span class="den">/10</span></span>'


def money(am: int, display: str) -> str:
    return f'<span class="price">{esc(display)}</span>'


def pick_line(p: dict, show_fixture: bool = True, prefix: str = "", with_pred=None) -> str:
    inner = ('<div class="teams">' + esc(p["home"]) + ' <span>v</span> ' + esc(p["away"]) + '</div>'
             + '<div class="tiny">' + esc(p["competition"]) + " · "
             + esc(p.get("start_display") or p["start_utc"]) + "</div>")
    link = prefix + "predictions.html#pred-" + p["fixture_id"]
    has_pred = with_pred is None or p["fixture_id"] in with_pred
    match_cell = ('<a href="' + link + '">' + inner + "</a>") if (show_fixture and has_pred) else inner
    return (
        "<tr>"
        + "<td>" + badge(p["confidence"]) + "</td>"
        + '<td><a href="' + prefix + 'sports/' + SLUG[p["sport"]] + '.html#picks">' + esc(p["sport"]) + "</a></td>"
        + "<td>" + match_cell + "</td>"
        + '<td><strong class="selection">' + esc(p["selection"]) + "</strong>"
        + '<div class="tiny">' + esc(p["market"]) + "</div></td>"
        + '<td class="nowrap">' + f"{p['probability'] * 100:.1f}%" + "</td>"
        + '<td class="nowrap">' + score_chip(p.get("score")) + "</td>"
        + '<td class="nowrap">' + money(p["american"], p["american_display"]) + "</td>"
        + "<td>" + src(p["official_url"]) + "</td>"
        + "</tr>"
    )


def pick_table(picks, show_fixture=True, link_predictions=True, prefix="", with_pred=None) -> str:
    head = ("<thead><tr><th>Confidence</th><th>Sport</th><th>Match</th><th>Selection</th>"
            "<th>Our chance</th><th>Score</th><th>Our price</th><th>Official source</th></tr></thead>")
    rows = []
    for p in picks:
        row = pick_line(p, show_fixture, prefix, with_pred)
        if not link_predictions:
            row = row.replace(prefix + f'predictions.html#pred-{p["fixture_id"]}', '#')
        rows.append(row)
    return f'<div class="table-wrap"><table class="data">{head}<tbody>{"".join(rows)}</tbody></table></div>'


CSS = """/* OLBG2 /now/ desk — one dashboard, plain and readable */
:root{
  --ink:#0f172a; --ink-2:#334155; --muted:#64748b; --line:#e2e8f0; --bg:#f8fafc;
  --card:#ffffff; --accent:#0f766e; --accent-2:#115e59; --high:#047857; --med:#b45309;
  --low:#475569; --warn:#b91c1c; --band:#1d4ed8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent-2);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1160px;margin:0 auto;padding:0 20px}
header.topbar{background:var(--ink);color:#fff;position:sticky;top:0;z-index:20}
header.topbar .bar{display:flex;align-items:center;gap:18px;min-height:56px;flex-wrap:wrap}
.brand{color:#fff;font-weight:700;letter-spacing:.2px;display:flex;align-items:center;gap:9px}
.brand .dot{width:9px;height:9px;border-radius:50%;background:#2dd4bf;display:inline-block}
.brand-sub{font-weight:400;color:#94a3b8;font-size:13px}
nav.main{display:flex;gap:4px;flex-wrap:wrap;margin-left:auto}
nav.main a{color:#cbd5e1;padding:6px 10px;border-radius:7px;font-size:14px}
nav.main a:hover{background:#1e293b;color:#fff;text-decoration:none}
nav.main a[aria-current="page"]{background:#0f766e;color:#fff}
main{padding:26px 0 60px}
h1{font-size:32px;line-height:1.2;margin:0 0 8px}
h2{font-size:21px;margin:34px 0 10px}
h3{font-size:17px;margin:0 0 6px}
p{margin:0 0 12px;color:var(--ink-2)}
.lede{font-size:18px;color:var(--ink-2);max-width:78ch}
.sub{color:var(--muted);font-size:14px}
.tiny{font-size:12px;color:var(--muted)}
.eyebrow{text-transform:uppercase;letter-spacing:.09em;font-size:12px;font-weight:700;
  color:var(--accent);margin:0 0 6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:12px;margin:20px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi .v{font-size:26px;font-weight:750;letter-spacing:-.5px}
.kpi .k{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-top:2px}
.kpi .s{font-size:12px;color:var(--muted);margin-top:6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.top-picks{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));margin:16px 0 8px}
.toppick{border:1px solid var(--line);border-left:5px solid var(--high);border-radius:12px;
  background:var(--card);padding:16px}
.toppick .sel{font-size:20px;font-weight:750;color:var(--high);display:block;margin:2px 0 4px}
.toppick .meta{font-size:13px;color:var(--muted)}
.toppick .price{font-weight:700;color:var(--ink)}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;
  font-weight:700;text-transform:uppercase;letter-spacing:.05em}
.score{font-variant-numeric:tabular-nums;font-weight:750;font-size:14px;padding:1px 7px;
  border-radius:7px;background:#f1f5f9;color:var(--low);display:inline-block}
.score .den{font-weight:500;font-size:11px;color:var(--muted)}
.score.high{background:#d1fae5;color:var(--high)}
.score.medium{background:#fef3c7;color:var(--med)}
.score.low{background:#f1f5f9;color:var(--low)}
.badge.high{background:#d1fae5;color:var(--high)}
.badge.medium{background:#fef3c7;color:var(--med)}
.badge.low{background:#e2e8f0;color:var(--low)}
.badge.band{background:#dbeafe;color:var(--band)}
.badge.out{background:#fee2e2;color:var(--warn)}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--card)}
table.data{width:100%;border-collapse:collapse;font-size:14px}
table.data th{text-align:left;background:#f1f5f9;color:#334155;font-size:12px;
  text-transform:uppercase;letter-spacing:.05em;padding:10px 12px;white-space:nowrap}
table.data td{padding:10px 12px;border-top:1px solid var(--line);vertical-align:top}
table.data tr:hover td{background:#fafcff}
.teams{font-weight:600}
.teams span{color:var(--muted);font-weight:400;padding:0 3px}
.selection{color:var(--high)}
.price{font-variant-numeric:tabular-nums}
.nowrap{white-space:nowrap}
.notice{border-left:4px solid var(--accent);background:#ecfdf5;padding:12px 14px;border-radius:0 10px 10px 0;
  margin:14px 0;font-size:14.5px}
.notice.warn{border-color:var(--warn);background:#fef2f2}
.notice.info{border-color:var(--band);background:#eff6ff}
.cta{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
.btn{display:inline-block;border:1px solid var(--line);background:var(--card);border-radius:9px;
  padding:9px 14px;font-weight:600;font-size:14px;color:var(--ink)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn:hover{text-decoration:none;border-color:var(--accent)}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0}
details summary{cursor:pointer;font-weight:650}
.pred{border:1px solid var(--line);border-radius:14px;background:var(--card);padding:18px;margin:14px 0}
.pred h3{margin:0 0 4px}
.pred .selection{font-size:17px;font-weight:700}
.pred .facts{margin-top:12px;border-top:1px dashed var(--line);padding-top:10px}
.pred .facts li{margin:5px 0;font-size:13px;color:var(--ink-2)}
ul.clean{padding-left:18px;margin:8px 0}
footer{border-top:1px solid var(--line);padding:22px 0 40px;color:var(--muted);font-size:13px}
.sportgrid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.sportcard{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.sportcard .head{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.pill{background:#f1f5f9;color:#334155;border-radius:999px;padding:2px 9px;font-size:12px}
.srcnote{font-size:12px;color:var(--muted);margin-top:8px}
@media(max-width:640px){h1{font-size:26px}nav.main a{font-size:13px;padding:5px 8px}}
"""

JS = """// Small progressive enhancement only: deep-link sections and copy a pick.
document.addEventListener('click', function (e) {
  var a = e.target.closest('a[data-copy]');
  if (!a) return;
  e.preventDefault();
  if (navigator.clipboard) navigator.clipboard.writeText(a.getAttribute('data-copy'));
  a.textContent = 'copied';
});
"""


def primary_cell(m: dict) -> str:
    pr = m.get("primary")
    if not pr:
        return '<span class="tiny">' + esc(m.get("blank_reason", "")) + "</span>"
    return ('<strong class="selection">' + esc(pr["selection"]) + "</strong>"
            + '<div class="tiny">' + esc(pr["market"]) + " · "
            + f'{pr["probability"] * 100:.1f}%' + " · " + esc(pr["american_display"]) + "</div>")


def conf_cell(m: dict) -> str:
    return badge(m["primary"]["confidence"]) if m.get("primary") else '<span class="badge out">no price</span>'


def flag_source(url: str) -> str:
    if url.startswith("http"):
        return src(url)
    return '<a href="' + esc(url) + '">local page</a>'


def page(title: str, current: str, body: str, prefix: str = "") -> str:
    nav = "".join(
        f'<a href="{prefix}{href}"'
        + (' aria-current="page"' if href == current else "") + f'>{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG2</title>
<meta name="description" content="OLBG2 research desk, 24 October 2026: our own lines, confidence-graded picks, written predictions and the official source behind every row.">
<link rel="stylesheet" href="{prefix}assets/style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f172a'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%2314b8a6'/%3E%3C/svg%3E">
</head>
<body>
<header class="topbar"><div class="wrap bar">
  <a class="brand" href="{prefix}index.html"><span class="dot"></span>OLBG2 <span class="brand-sub">desk · {SHOWN_DATE}</span></a>
  <nav class="main" aria-label="Sections">{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
  <p>Every row links to the official page it was read from. OLBG is named only where OLBG itself lists the event.
  Prices are originated on this desk from official inputs, not copied from a bookmaker, and are research output rather
  than betting advice. Snapshot {esc(AS_OF)}.</p>
  <p><a href="{prefix}methodology.html">How the numbers are made</a> ·
     <a href="{prefix}flagged.html">What is missing or unconfirmed</a> ·
     <a href="{prefix}../archive.html">Earlier desks (archive)</a> ·
     <a href="{prefix}../index.html">Repository home</a></p>
</footer>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def facts_list(facts) -> str:
    items = "".join(
        f'<li><strong>{esc(f["claim"])}:</strong> {esc(f["value"])} — {src(f["source_url"])}'
        f'<span class="tiny"> · captured {esc(f.get("captured_utc", ""))}</span></li>'
        for f in facts
    )
    return f'<ul class="clean facts">{items}</ul>'


def main() -> int:
    fixtures = load("fixtures.json")
    matches = load("matches.json")
    lines = load("lines.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    olbg = load("olbg.json")
    sources = load("sources.json")
    checks = load("checks.json")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "assets" / "app.js").write_text(JS, encoding="utf-8")

    hs = [p for p in picks["picks"] if p["confidence"] == "high"]
    ms = [p for p in picks["picks"] if p["confidence"] == "medium"]
    ls = [p for p in picks["picks"] if p["confidence"] == "low"]
    by_fixture = {m["id"]: m for m in matches["matches"]}
    pred_by_fixture = {p["fixture_id"]: p for p in preds["predictions"]}
    pred_ids = set(pred_by_fixture)

    # ------------------------------------------------------------------ top five by sport
    grade_order = {"high": 0, "medium": 1, "low": 2}
    kind_order = {"winner": 0, "handicap": 1, "total": 2}
    top5_by_sport = {}
    for s in SPORTS:
        candidates = [r for r in lines["lines"] if r["sport"] == s and r["in_band"]]
        candidates.sort(key=lambda r: (grade_order[r["confidence"]], -r["probability"],
                                       kind_order.get(r["kind"], 3), r["fixture_id"],
                                       r["market"], r["selection"]))
        chosen, seen = [], set()
        for r in candidates:
            key = (r["fixture_id"], r["market"], r["selection"])
            if key in seen:
                continue
            seen.add(key)
            row = dict(r)
            m = by_fixture.get(r["fixture_id"], {})
            row["competition"] = m.get("competition", "")
            row["start_display"] = m.get("start_display", "")
            row["olbg_url"] = m.get("olbg_url", "")
            chosen.append(row)
            if len(chosen) == 5:
                break
        if len(chosen) == 5:
            reason = ""
        elif chosen:
            reason = (f"Only {len(chosen)} in-band originated lines are available for this sport; "
                      "the published blank rows explain the missing inputs.")
        else:
            reason = next((m["blank_reason"] for m in matches["matches"]
                           if m["sport"] == s and not m["priced"]),
                          "No in-band originated line is available for this sport.")
        top5_by_sport[s] = {"count": len(chosen), "reason": reason, "lines": chosen}
    payload_top5 = {
        "as_of_utc": AS_OF,
        "target_per_sport": 5,
        "count": sum(v["count"] for v in top5_by_sport.values()),
        "by_sport": top5_by_sport,
    }
    (DATA / "top5.json").write_text(json.dumps(payload_top5, indent=1) + "\n",
                                    encoding="utf-8")

    # ------------------------------------------------------------------ flags
    flags = []
    for m in matches["matches"]:
        if not m["priced"]:
            flags.append({
                "id": "F-" + m["id"], "severity": "open", "sport": m["sport"],
                "item": f"{m['home']} v {m['away']} carries no originated price",
                "detail": m["blank_reason"],
                "source": m["official_url"],
            })
    for s in SPORTS:
        n = preds["by_sport"].get(s, 0)
        if n < 5:
            flags.append({
                "id": "COV-" + SLUG[s], "severity": "open", "sport": s,
                "item": f"{n} written prediction{'s' if n != 1 else ''} for {s}, against a target of five",
                "detail": ("The five-a-day target could only be met where enough upcoming fixtures had "
                           "an official record with the rates this desk needs. Rather than pad the card, "
                           "the shortfall is published. See the sport page for what is missing."),
                "source": f"sports/{SLUG[s]}.html",
            })
    flags += [
        {
            "id": "V-01", "severity": "note", "sport": "All",
            "item": "Fixture facts are inherited from the official capture made at 17:35Z today",
            "detail": ("All 50 fixture records and their per-fact source links come from the official "
                       "capture committed at 17:35Z on 24 October. At 22:32Z all fifteen OLBG hubs "
                       "and nineteen official pages were re-read first-hand. The inherited numbers "
                       "still drive the prices; a changed or incomplete recheck is published below "
                       "rather than silently blended into the dated capture."),
            "source": "checks.html",
        },
        {
            "id": "V-02", "severity": "corrected", "sport": "Gaelic Sports",
            "item": "Stored Gaelic semi-final margin inputs disagreed with the official scorelines",
            "detail": ("The inherited record carried margins of 44 and -6 for the Galway final. The "
                       "official scorelines give Maigh Cuilinn 4-26 to 0-8 (30 points) and "
                       "Salthill-Knocknacarra 0-15 to 2-7 (2 points), so this desk recomputed the "
                       "margins from the scores and ignored the stored values."),
            "source": "https://gaa.ie/",
        },
        {
            "id": "V-03", "severity": "corrected", "sport": "Rugby League",
            "item": "Raw round-one margins were not used for Australia v Fiji",
            "detail": ("A two-point win over New Zealand and a 28-point win over Cook Islands cannot be "
                       "compared without adjusting for the opponent, so the price comes from the "
                       "evidence ladder instead and the fixture is capped at medium confidence."),
            "source": "https://www.nrl.com/",
        },
        {
            "id": "V-04", "severity": "note", "sport": "All",
            "item": "OLBG display times are US Eastern strings and have not been converted",
            "detail": ("OLBG prints 'Today 14:05' style times in US Eastern. They are stored exactly as "
                       "shown. Where an official start time exists it is used for the fixture, and the "
                       "OLBG string is kept beside it rather than converted."),
            "source": "https://www.olbg.com/betting-tips",
        },
        {
            "id": "V-05", "severity": "open", "sport": "Golf",
            "item": "The OLBG golf hub still lists no events at 22:32Z",
            "detail": ("The golf hub returned 'No tips found.' both at 18:06Z and on the 22:32Z "
                       "re-read. The two golf fixtures remain on the card with official leaderboard "
                       "facts, but neither is asserted to be an active OLBG listing."),
            "source": "https://www.olbg.com/betting-tips/Golf/5",
        },
        {
            "id": "V-08", "severity": "note", "sport": "All",
            "item": "Six picks are for matches that had already started when the snapshot was taken",
            "detail": ("Volleyball (Giesen v Berlin, 17:30Z), Rugby Union (Ospreys v Dragons and "
                       "Toulon v Pau), Darts (Littler v Aspinall), Handball (Balingen v Melsungen) "
                       "and Basketball (Miami v Charlotte, 22:00Z) began before the 22:32Z snapshot. "
                       "They keep their prices and write-ups for the record, are marked as under way "
                       "and are excluded from the executive summary."),
            "source": "https://www.nba.com/standings",
        },
        {
            "id": "V-07", "severity": "note", "sport": "All",
            "item": "Some fixture source links point at a news or squad-announcement page rather than a fixture list",
            "detail": ("Where a governing body publishes a round preview rather than a stable fixture URL, the "
                       "inherited record links the article that carries the fixture time and team news. The facts "
                       "on the row are the ones that page supports; a per-fixture permalink is not claimed."),
            "source": "https://www.legavolley.it/",
        },
        {
            "id": "V-06", "severity": "note", "sport": "Basketball",
            "item": "Four NBA clubs had not filed an injury report at the 1:00 PM ET deadline",
            "detail": ("Milwaukee, Washington, New Orleans and Golden State are recorded as NOT YET "
                       "SUBMITTED. No absence is stated for those rosters, and the fields are blank "
                       "rather than guessed."),
            "source": "https://official.nba.com/nba-injury-report-2026-27-season/",
        },
        {
            "id": "V-09", "severity": "open", "sport": "Golf",
            "item": "PGA Tour leaderboard moved on after the 17:35Z capture",
            "detail": ("At 22:32Z the official leaderboard showed round three as Official and a tie "
                       "at -16 between Austin Smotherman and Seamus Power on +210. The inherited "
                       "record described Smotherman at -16 through ten holes and Chandler Blanchet "
                       "second at -15. The newer state is flagged, not blended into the dated price "
                       "inputs, and no golf win price is originated."),
            "source": "https://www.pgatour.com/leaderboard",
        },
        {
            "id": "V-10", "severity": "open", "sport": "Snooker",
            "item": "The snooker hub has no tips and the final opponent is still undecided",
            "detail": ("OLBG rendered 'No tips found.' at 22:32Z. World Snooker Tour showed Mark "
                       "Williams and Jak Jones level at 5-5 in the live semi-final, with Sunday's "
                       "final listed as Kyren Wilson against the winner of that match. No opposing "
                       "player or match-winner price is inferred."),
            "source": "https://www.wst.tv/matches/",
        },
        {
            "id": "V-11", "severity": "open", "sport": "Rugby League",
            "item": "The OLBG rugby league hub shows only 2027 futures",
            "detail": ("The 22:32Z first page listed State of Origin 2027, Super League 2027 and "
                       "NRL 2027, but no Australia v Fiji match row. The official NRL match centre "
                       "still schedules that round-two game for 25 October at Suncorp Stadium, so "
                       "the official event is retained without claiming an OLBG match listing."),
            "source": "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/australia-v-fiji/",
        },
        {
            "id": "V-12", "severity": "open", "sport": "Greyhounds",
            "item": "The two inherited greyhound finals have expired from the OLBG hub",
            "detail": ("At 22:32Z the first OLBG greyhound page showed only the 11:04 Doncaster "
                       "race for tomorrow. The Scurry Gold Cup and Oaks final facts remain sourced "
                       "from GBGB, but their starts were 18:00Z and 18:15Z and they are no longer "
                       "offered as current pre-race listings."),
            "source": "https://www.olbg.com/betting-tips/Greyhounds/28",
        },
        {
            "id": "V-13", "severity": "open", "sport": "Motor Racing",
            "item": "The OLBG motor racing hub lists no events",
            "detail": ("The 22:32Z hub read returned 'No tips found.' The Formula 1 United States "
                       "Grand Prix event page and 2026 standings were reachable, but qualifying had "
                       "not been captured in a usable grid, so no race-winner number is originated "
                       "and no active OLBG listing is claimed."),
            "source": "https://www.olbg.com/betting-tips/Motor_Racing/14",
        },
        {
            "id": "V-14", "severity": "open", "sport": "Darts",
            "item": "The darts hub has rotated to Sunday's later round",
            "detail": ("The Littler v Aspinall row from the earlier capture is no longer visible. "
                       "At 22:32Z OLBG showed Ross Smith v Luke Woodhouse, Gerwyn Price v Stephen "
                       "Bunting and European Championship outrights. The inherited PDC facts are "
                       "kept with their 18:00Z start marked as under way rather than refreshed "
                       "from a different match."),
            "source": "https://www.olbg.com/betting-tips/Darts/15",
        },
        {
            "id": "V-15", "severity": "open", "sport": "All",
            "item": "Five written predictions per sport remain an unmet target on this slate",
            "detail": (f"This desk publishes {preds['count']} written predictions across "
                       f"{len(preds['by_sport'])} sports, and "
                       f"{sum(1 for s in SPORTS if preds['by_sport'].get(s, 0) < 5)} sports are "
                       "below five. The top-five page shows every in-band line that can be "
                       "originated from the captured official inputs; blank rows are not padded "
                       "with invented rates, prices or injuries."),
            "source": "top5.html",
        },
    ]

    payload_flags = {
        "as_of_utc": AS_OF,
        "count": len(flags),
        "open": sum(1 for f in flags if f["severity"] == "open"),
        "corrected": sum(1 for f in flags if f["severity"] == "corrected"),
        "flags": flags,
    }
    (DATA / "flagged.json").write_text(json.dumps(payload_flags, indent=1) + "\n",
                                       encoding="utf-8")

    # ------------------------------------------------------------------ index
    pregame = [p for p in picks["picks"] if not p["started"]]
    shown = [p for p in (hs + ms) if not p["started"]][:4]
    cards = []
    for p in shown:
        pred = pred_by_fixture.get(p["fixture_id"], {})
        cards.append(
            f'<div class="toppick">'
            f'<div class="meta">{esc(p["sport"])} · {esc(p["competition"])}</div>'
            f'<div class="teams" style="margin-top:6px">{esc(p["home"])} <span>v</span> {esc(p["away"])}</div>'
            f'<a class="sel" href="predictions.html#pred-{esc(p["fixture_id"])}">{esc(p["selection"])}</a>'
            f'<div class="meta">{esc(p["market"])} · our chance {p["probability"] * 100:.1f}% · '
            f'<span class="price">{esc(p["american_display"])}</span> {badge(p["confidence"])}'
            f' {score_chip(p.get("score"))}</div>'
            + (f'<div class="tiny" style="margin-top:8px">{esc(pred.get("headline", ""))}</div>' if pred else "")
            + f'<div class="srcnote">Source: {src(p["official_url"])} · '
              f'<a href="predictions.html#pred-{esc(p["fixture_id"])}">read the prediction</a></div>'
            f'</div>'
        )
    sport_cards = []
    for s in SPORTS:
        st = matches["by_sport"][s]
        n_pred = preds["by_sport"].get(s, 0)
        note = ("no price published" if st["priced"] == 0
                else f'{st["picks"]} picks · {n_pred} written')
        sport_cards.append(
            f'<a class="sportcard" href="sports/{SLUG[s]}.html">'
            f'<div class="head"><h3>{esc(s)}</h3><span class="pill">{st["fixtures"]} fixtures</span></div>'
            f'<p class="sub">{st["priced"]} priced · {st["markets"]} originated prices · {note}</p>'
            f'<div class="sub">{st["high"]} high · {st["medium"]} medium · {st["low"]} low</div></a>'
        )
    today_rows = []
    for m in matches["matches"]:
        pr = m.get("primary")
        today_rows.append(
            "<tr>"
            f'<td><a href="sports/{SLUG[m["sport"]]}.html">{esc(m["sport"])}</a></td>'
            f'<td><a href="matches.html#{esc(m["id"])}"><div class="teams">{esc(m["home"])} <span>v</span> {esc(m["away"])}</div></a>'
            f'<div class="tiny">{esc(m["competition"])}</div></td>'
            f'<td class="tiny">{esc(m.get("start_display") or m["start_utc"])}</td>'
            + '<td>' + (('<strong class="selection">' + esc(pr["selection"]) + '</strong><div class="tiny">' + esc(pr["market"]) + '</div>') if pr else '<span class="tiny">no selection</span>') + '</td>'
            + '<td class="nowrap">' + ((f'{pr["probability"] * 100:.1f}% ' + esc(pr["american_display"])) if pr else "—") + '</td>'
            + '<td>' + (badge(pr["confidence"]) if pr else "—") + '</td>'
            f'<td>{src(m["official_url"])}</td>'
            "</tr>"
        )
    index_body = f"""
<p class="eyebrow">Executive summary · snapshot {esc(AS_OF)}</p>
<h1>{picks['pregame_high']} high-confidence picks still to start, and {picks['count']} graded picks in total</h1>
<p class="lede">This is the whole desk on one screen: what we are backing, at what price, and the official page behind
every number. {matches['count']} upcoming fixtures were read from {sources['official_count']} official sources,
{lines['count']} prices were originated here, and {preds['count']} of the picks carry a full written preview.</p>

<div class="cta">
  <a class="btn primary" href="picks.html">See every pick →</a>
  <a class="btn" href="predictions.html">Read the {preds['count']} predictions</a>
  <a class="btn" href="top5.html">Top 5 by sport</a>
  <a class="btn" href="checks.html">Source checks</a>
  <a class="btn" href="matches.html">All {matches['count']} matches</a>
  <a class="btn" href="sports/index.html">Sport by sport</a>
</div>

<h2>The strongest calls</h2>
<p class="sub">Highest confidence first. Every price sits inside the requested −250 to +10000 band.</p>
<div class="top-picks">{''.join(cards)}</div>
<p class="sub"><a href="picks.html">All {picks['count']} picks, including {len(ms)} medium and {len(ls)} low →</a></p>

<div class="kpis">
  <div class="kpi"><div class="v">{matches['count']}</div><div class="k">upcoming matches</div><div class="s">{matches['priced']} priced · {matches['unpriced']} blank with a reason</div></div>
  <div class="kpi"><div class="v">{lines['count']}</div><div class="k">originated prices</div><div class="s">match winner, handicap and total</div></div>
  <div class="kpi"><div class="v">{picks['pregame_count']}</div><div class="k">picks still to start</div><div class="s">{len(hs)} high · {len(ms)} medium · {len(ls)} low overall</div></div>
  <div class="kpi"><div class="v">{preds['count']}</div><div class="k">written predictions</div><div class="s">shortest {preds['min_words']} words</div></div>
  <div class="kpi"><div class="v">{olbg['listings_count']}</div><div class="k">OLBG listing rows</div><div class="s">{len(olbg['sports_listed'])} of 15 sports listed today</div></div>
  <div class="kpi"><div class="v">{payload_flags['count']}</div><div class="k">review items</div><div class="s">{payload_flags['open']} open · {payload_flags['corrected']} corrected</div></div>
</div>

<div class="notice">
<strong>Where the picks are.</strong> <a href="picks.html">Picks</a> lists every selection with the price we made and
the confidence grade. <a href="predictions.html">Written predictions</a> holds a full preview for every published pick,
with the official facts underneath. <a href="top5.html">Top 5 by sport</a> gathers the strongest in-band lines, and
<a href="checks.html">Source checks</a> records the 22:32Z first-hand re-reads. Each sport page repeats that sport's
matches, picks and previews in the same order, so nothing has to be hunted for.
</div>

<h2>Today and tonight — every fixture on the desk</h2>
<p class="sub">All {matches['count']} fixtures, priced or not, with the primary selection. A dash means no originated
price, and the reason is on <a href="flagged.html">Flagged for review</a>.</p>
<div class="table-wrap"><table class="data">
<thead><tr><th>Sport</th><th>Match</th><th>Start</th><th>Selection</th><th>Chance · price</th><th>Confidence</th><th>Official source</th></tr></thead>
<tbody>{''.join(today_rows)}</tbody></table></div>

<h2>By sport</h2>
<p class="sub">All fifteen requested sports are here, including the ones where the sources did not support a price.</p>
<div class="sportgrid">{''.join(sport_cards)}</div>

<div class="notice info" style="margin-top:26px">
<strong>What this desk does not claim.</strong> These are our own numbers, not bookmaker odds, and a pick is a research
opinion rather than advice. {sum(1 for s in SPORTS if preds['by_sport'].get(s, 0) < 5)} sports carry fewer than five written predictions because only fixtures with a real
official record were written up; the gap is listed on <a href="flagged.html">Flagged for review</a> rather than filled
with filler. Where OLBG does not list an event, the row says so instead of implying a market exists.
</div>
"""
    (OUT / "index.html").write_text(page("Executive summary", "index.html", index_body),
                                    encoding="utf-8")

    # ------------------------------------------------------------------ picks
    pregame_hm = [p for p in (hs + ms) if not p["started"]]
    started_rows = [p for p in picks["picks"] if p["started"]]
    picks_body = f"""
<p class="eyebrow">Picks</p>
<h1>Every selection, graded</h1>
<p class="lede">One row per match: the selection in green, the market, the chance we give it and the price that chance
implies. {picks['pregame_count']} picks are for matches that had not started when this snapshot was taken: the
{len(pregame_hm)} below are offered, and {len(ls)} more are priced but not backed because our own number is too close
to a coin flip. A further {picks['started_count']} matches had already started, so they are kept for the record and are
not offered as pre-match calls.</p>

<h2>Available now — {len(pregame_hm)} picks on matches still to start</h2>
<p class="sub">High confidence first, then medium. A dash of confidence still means what it says: high needs a 62%
chance from a numeric official input and a price inside the band. The <strong>score</strong> column puts that on a
0-10 scale so sports can be compared at a glance: 5.0 is a coin flip, and every pick above is shaded down when its
price rests on the evidence ladder rather than on a scoring rate (<a href="methodology.html">method</a>).</p>
{pick_table(pregame_hm, with_pred=pred_ids)}

<h2>Already under way at the snapshot ({len(started_rows)})</h2>
<p class="sub">These {len(started_rows)} matches started before {esc(AS_OF)}. They stay on the desk with their prices and their
write-ups so the record is complete, but they cannot be backed before kick-off any more.</p>
{pick_table(started_rows, with_pred=pred_ids)}

<h2>Priced but not backed ({len(ls)})</h2>
<p class="sub">{len(ls)} cricket fixtures where our own number is close enough to a coin flip that it is not worth
backing. They stay in the table and now carry their own full previews, so the price book is complete and nobody has
to guess why they are missing from the two tables above. A low grade is not a prediction against; it is the desk
saying it has no edge.</p>
{pick_table(ls, with_pred=pred_ids)}

<div class="notice info"><strong>How the price was made.</strong> Each price is the reciprocal of our own probability,
so −250 always means exactly 71.4%. The method behind the probability differs by sport and is written out on the
<a href="methodology.html">method page</a>.</div>
"""
    (OUT / "picks.html").write_text(page("Picks", "picks.html", picks_body), encoding="utf-8")

    # ------------------------------------------------------------------ predictions
    blocks = []
    for p in sorted(preds["predictions"], key=lambda x: (SPORTS.index(x["sport"]),
                                                          {"high": 0, "medium": 1, "low": 2}[x["confidence"]])):
        blocks.append(f"""
<article class="pred" id="pred-{esc(p['fixture_id'])}">
  <div class="sub">{esc(p['sport'])} · {esc(p['competition'])} · {esc(p.get('start_display') or p['start_utc'])}</div>
  <h3>{esc(p['headline'])}</h3>
  <div class="teams" style="font-size:15px">{esc(p['home'])} <span>v</span> {esc(p['away'])}</div>
  <p style="margin-top:8px"><span class="selection">{esc(p['selection'])}</span>
     <span class="tiny">· {esc(p['market'])} · our chance {p['probability'] * 100:.1f}% ·
     {esc(p['american_display'])} · {p['words']} words</span> {badge(p['confidence'])} {score_chip(p.get('score'))}</p>
  <p>{esc(p['text'])}</p>
  <div class="facts"><div class="tiny"><strong>Official facts behind this prediction</strong></div>
  {facts_list(p['facts'])}</div>
  <div class="srcnote">Fixture source: {src(p['official_url'])}
  {'· OLBG event: ' + src(p['olbg_url'], 'OLBG listing') if p.get('olbg_url') else '· not listed on OLBG at capture'}</div>
</article>""")
    preds_body = f"""
<p class="eyebrow">Written predictions</p>
<h1>{preds['count']} predictions, each one written for its own match</h1>
<p class="lede">Every published pick has its own preview: the selection, the teams, the current form and the
official facts that support it. The shortest is {preds['min_words']} words. The official facts are listed under each
write-up with the page they came from, so any line can be checked.</p>
<div class="notice"><strong>Coverage.</strong> {', '.join(f'{k} {v}' for k, v in preds['by_sport'].items())}.
Sports with fewer than five are listed on <a href="flagged.html">Flagged for review</a> with the reason.</div>
{''.join(blocks)}
"""
    (OUT / "predictions.html").write_text(page("Written predictions", "predictions.html", preds_body),
                                          encoding="utf-8")

    # ------------------------------------------------------------------ matches
    rows = []
    for m in matches["matches"]:
        pr = m.get("primary")
        rows.append(
            f'<tr id="{esc(m["id"])}">'
            f'<td><a href="sports/{SLUG[m["sport"]]}.html">{esc(m["sport"])}</a></td>'
            f'<td><div class="teams">{esc(m["home"])} <span>v</span> {esc(m["away"])}</div>'
            f'<div class="tiny">{esc(m["competition"])} · {esc(m.get("venue") or "venue not captured")}</div></td>'
            f'<td class="tiny">{esc(m.get("start_display") or m["start_utc"])}<br>'
            f'{"started at snapshot" if m["started"] else ("OLBG listed" if m["olbg_listed"] else "not on OLBG at capture")}</td>'
            "<td>" + primary_cell(m) + "</td>"
            + "<td>" + conf_cell(m) + "</td>"
            f'<td class="nowrap">{m["markets"]}</td>'
            f'<td>{src(m["official_url"])}</td>'
            "</tr>"
        )
    matches_body = f"""
<p class="eyebrow">Matches</p>
<h1>All {matches['count']} fixtures on the desk</h1>
<p class="lede">{matches['priced']} carry an originated price and {matches['unpriced']} are blank with a stated reason.
Each row links to the official page that lists the fixture, and every fixture expands on its sport page with the full
fact list.</p>
<div class="table-wrap"><table class="data">
<thead><tr><th>Sport</th><th>Match</th><th>Start · OLBG</th><th>Primary selection</th><th>Confidence</th><th>Prices</th><th>Official source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<div class="notice warn"><strong>Blank is a real answer.</strong> {matches['unpriced']} fixtures have no price because
the official record does not contain the rate needed to make one. They are on
<a href="flagged.html">Flagged for review</a> with the exact reason and the source that was checked.</div>
"""
    (OUT / "matches.html").write_text(page("Matches", "matches.html", matches_body), encoding="utf-8")

    # ------------------------------------------------------------------ lines
    grouped = defaultdict(lambda: defaultdict(list))
    for r in lines["lines"]:
        grouped[r["sport"]][r["fixture_id"]].append(r)
    blocks = []
    for s in SPORTS:
        if s not in grouped:
            continue
        fid_blocks = []
        for fid, rows in grouped[s].items():
            m = by_fixture[fid]
            cells = []
            for r in rows:
                band_cell = ('<span class="badge band">in band</span>' if r["in_band"]
                             else '<span class="badge out">outside band</span>')
                cells.append(
                    "<tr><td>" + esc(r["market"]) + "</td><td>" + esc(r["selection"]) + "</td>"
                    + '<td class="nowrap">' + f'{r["probability"] * 100:.1f}%' + "</td>"
                    + '<td class="nowrap">' + f'{r["decimal"]:.2f}' + "</td>"
                    + '<td class="nowrap">' + esc(r["american_display"]) + "</td>"
                    + "<td>" + band_cell + "</td><td>" + badge(r["confidence"]) + "</td>"
                    + "<td>" + src(m["official_url"]) + "</td></tr>")
            body_rows = "".join(cells)
            fid_blocks.append(f"""
<details>
  <summary>{esc(m['home'])} v {esc(m['away'])} <span class="pill">{len(rows)} prices</span></summary>
  <div class="table-wrap" style="margin-top:10px"><table class="data">
  <thead><tr><th>Market</th><th>Selection</th><th>Chance</th><th>Decimal</th><th>American</th><th>Band</th><th>Grade</th><th>Official source</th></tr></thead>
  <tbody>{body_rows}</tbody></table></div>
  <div class="srcnote">Official inputs: {src(m['official_url'])}</div>
  <div class="srcnote"><em>Assumption:</em> {esc(rows[0]['assumption'])}</div>
</details>""")
        blocks.append(f'<h2>{esc(s)}</h2>{"".join(fid_blocks)}')
    lines_body = f"""
<p class="eyebrow">Our lines</p>
<h1>{lines['count']} prices originated on this desk</h1>
<p class="lede">Match winner, handicap and match total for every fixture that has an official rate. Nothing here is a
bookmaker quote: each price is 1 / our probability, and the assumption behind every family of prices is printed under
its table.</p>
<div class="notice"><strong>{lines['in_band']}</strong> of {lines['count']} prices fall inside −250 to +10000. The rest
are kept visible on the <a href="band.html">odds band</a> page, because hiding an out-of-band price would hide what
the market really looks like.</div>
{''.join(blocks)}
"""
    (OUT / "lines.html").write_text(page("Our lines", "lines.html", lines_body), encoding="utf-8")

    # ------------------------------------------------------------------ band
    inb = [r for r in lines["lines"] if r["in_band"]]
    out = [r for r in lines["lines"] if not r["in_band"]]
    band_rows = "".join(
        f'<tr><td>{esc(r["sport"])}</td><td>{esc(r["home"])} v {esc(r["away"])}</td>'
        f'<td>{esc(r["market"])}</td><td>{esc(r["selection"])}</td>'
        f'<td class="nowrap">{r["probability"] * 100:.1f}%</td><td class="nowrap">{esc(r["american_display"])}</td>'
        f'<td>{src(r["official_url"])}</td></tr>'
        for r in out[:120]
    )
    band_body = f"""
<p class="eyebrow">Odds band</p>
<h1>The −250 to +10000 test</h1>
<p class="lede">The brief asks for picks priced between −250 and +10000. A fair −250 is 71.43%, so any selection above
that is outside the band however confident it looks. We keep the band test on every price: {len(inb)} of
{lines['count']} qualify and {len(out)} do not.</p>
<div class="kpis">
  <div class="kpi"><div class="v">{len(inb)}</div><div class="k">inside the band</div><div class="s">−250 … +10000</div></div>
  <div class="kpi"><div class="v">{len(out)}</div><div class="k">outside the band</div><div class="s">mostly heavy favourites</div></div>
  <div class="kpi"><div class="v">{picks['in_band']} / {picks['count']}</div><div class="k">published picks in band</div><div class="s">no pick is relabelled to fit</div></div>
  <div class="kpi"><div class="v">71.43%</div><div class="k">the −250 boundary</div><div class="s">100 / 1.40</div></div>
</div>
<div class="notice info"><strong>Why handicaps carry the card.</strong> A side we rate at 85% cannot be backed at a
price inside the band, so the same opinion is published as the handicap at which our number lands near 68%. That is
what a handicap is for, and it is why most high-confidence picks above are handicaps rather than money lines.</div>
<h2>Every price outside the band ({len(out)})</h2>
<p class="sub">Shown in full rather than removed, so the reasoning stays auditable.</p>
<div class="table-wrap"><table class="data">
<thead><tr><th>Sport</th><th>Match</th><th>Market</th><th>Selection</th><th>Chance</th><th>Price</th><th>Official source</th></tr></thead>
<tbody>{band_rows}</tbody></table></div>
"""
    (OUT / "band.html").write_text(page("Odds band", "band.html", band_body), encoding="utf-8")

    # ------------------------------------------------------------------ olbg
    lrows = "".join(
        f'<tr><td>{esc(r["sport"])}</td><td>{esc(r["competition"])}</td>'
        f'<td>{esc(r["event"])}</td><td class="tiny">{esc(r["displayed_time"])}</td>'
        f'<td>{esc(r["market"])}</td><td>{esc(r["selection"])}</td>'
        f'<td class="nowrap">{esc(r["tips"])} · {r["pct"]}%</td>'
        f'<td class="tiny">{esc(r["event_id"])}</td>'
        f'<td>{src(r["url"], "OLBG event")}</td></tr>'
        for r in olbg["listings"]
    )
    hub_rows = "".join(
        f'<tr><td>{esc(s)}</td><td>{src(h["url"], h["url"].split("olbg.com")[-1])}</td>'
        f'<td class="nowrap">{h["sport_id"]}</td><td class="nowrap">{h["listed_events"]}</td>'
        f'<td class="tiny">{esc(h.get("note", ""))}</td></tr>'
        for s, h in olbg["hubs"].items()
    )
    def recheck_badge(status: str) -> str:
        tone = "high" if status == "confirmed" else ("medium" if status in ("changed", "partial") else "low")
        return badge(tone) + f' <span class="tiny">{esc(status)}</span>'

    recheck_rows = "".join(
        f'<tr><td>{esc(r["hub"])}</td><td>{src(r["url"])}</td>'
        f'<td class="tiny">{esc(r["checked_utc"])}</td><td>{esc(r["result"])}</td>'
        f'<td>{recheck_badge(r["status"])}</td></tr>'
        for r in olbg["rechecks"]
    )
    olbg_body = f"""
<p class="eyebrow">OLBG</p>
<h1>What OLBG actually lists today</h1>
<p class="lede">{olbg['listings_count']} event rows across {len(olbg['sports_listed'])} of the 15 requested sports,
each with OLBG's own event id and the URL of the event page. The site publishes one most-tipped selection per event,
which is a community vote and not a price, so no OLBG figure is copied into our lines.</p>
<div class="notice"><strong>Capture.</strong> Base listing capture {esc(olbg['capture_utc'])} to
{esc(olbg['capture_end_utc'])} (inherited unchanged). {olbg['recheck_count']} hub reads are recorded below: three at
17:56-18:06Z and all fifteen again at 22:32Z. Rotated, empty and futures-only hubs are also on the
<a href="checks.html">Source checks</a> and <a href="flagged.html">Flagged for review</a> pages.</div>
<h2>Hubs re-read live</h2>
<div class="table-wrap"><table class="data">
<thead><tr><th>Hub</th><th>URL</th><th>Checked</th><th>Result</th><th>State</th></tr></thead>
<tbody>{recheck_rows}</tbody></table></div>
<h2>The fifteen hub routes</h2>
<div class="table-wrap"><table class="data">
<thead><tr><th>Sport</th><th>OLBG route</th><th>Sport id</th><th>Events captured</th><th>Note</th></tr></thead>
<tbody>{hub_rows}</tbody></table></div>
<h2>Every listing row captured today</h2>
<div class="table-wrap"><table class="data">
<thead><tr><th>Sport</th><th>Competition</th><th>Event as listed</th><th>Time shown</th><th>Market</th><th>Most-tipped</th><th>Tips</th><th>Event id</th><th>Event page</th></tr></thead>
<tbody>{lrows}</tbody></table></div>
<div class="notice info"><strong>Reading the times.</strong> OLBG prints US Eastern times such as "Today 14:05".
They are kept exactly as shown and are never converted here; the official start time is used on the fixture itself.</div>
"""
    (OUT / "olbg.html").write_text(page("OLBG list", "olbg.html", olbg_body), encoding="utf-8")

    # ------------------------------------------------------------------ sources
    srows = "".join(
        f'<tr><td>{src(r["url"])}</td><td class="tiny">{esc(r["source_key"])}</td>'
        f'<td>{"official" if r["official"] else "OLBG"}</td>'
        f'<td class="tiny">{esc(r.get("kind", ""))}</td>'
        f'<td>{esc(", ".join(r["sports"]))}</td>'
        f'<td class="nowrap">{r["claims"]}</td><td class="tiny">{esc(r["captured_utc"])}</td></tr>'
        for r in sources["sources"]
    )
    sources_body = f"""
<p class="eyebrow">Sources</p>
<h1>{sources['count']} sources, {sources['official_count']} of them official</h1>
<p class="lede">Every value on this site points back to one of these pages. The fixture captures were made at 17:35Z
today and are inherited. All fifteen OLBG hubs and {checks['official_count']} official pages were re-read first-hand at
22:32Z; see <a href="checks.html">Source checks</a> for each observation.</p>
<div class="table-wrap"><table class="data">
<thead><tr><th>Source</th><th>Key</th><th>Type</th><th>Role</th><th>Sports covered</th><th>Claims used</th><th>Captured</th></tr></thead>
<tbody>{srows}</tbody></table></div>
<div class="notice"><strong>What a link proves.</strong> A link shows where a value was read. It is not a claim that the
page still shows the same number now, and the capture time on each fact is the moment it was read.</div>
"""
    (OUT / "sources.html").write_text(page("Sources", "sources.html", sources_body), encoding="utf-8")

    # ------------------------------------------------------------------ source checks
    def check_tone(status: str) -> str:
        if status == "confirmed":
            return "high"
        if status in ("changed", "partial"):
            return "medium"
        return "low"

    hub_check_rows = "".join(
        f'<tr id="hub-{SLUG[r["sport"]]}"><td>{esc(r["sport"])}</td>'
        f'<td>{src(r["url"], r["hub"])}</td><td>{esc(r["status"])}</td>'
        f'<td>{esc(r["result"])}</td>'
        f'<td>{badge(check_tone(r["status"]))} '
        f'{"needs review" if r["flag"] else "clear"}</td></tr>'
        for r in checks["hub_checks"]
    )
    official_check_rows = "".join(
        f'<tr><td>{esc(", ".join(r["sports"]))}</td><td>{esc(r["publisher"])}</td>'
        f'<td>{src(r["url"])}</td><td>{esc(r["status"])}</td>'
        f'<td>{esc(r["result"])}</td>'
        f'<td>{badge(check_tone(r["status"]))} '
        f'{"needs review" if r["flag"] else "clear"}</td></tr>'
        for r in checks["official_checks"]
    )
    checks_body = f"""
<p class="eyebrow">Source checks</p>
<h1>First-hand reads at 22:32Z, kept separate from the price capture</h1>
<p class="lede">{checks['hub_count']} OLBG hubs and {checks['official_count']} official pages were opened at
{esc(checks['as_of_utc'])}. {checks['flagged_count']} observations need manual review. The dated 17:35Z fixture facts
still drive the prices; a changed page is flagged instead of silently replacing the older number.</p>
<div class="notice"><strong>How to read this.</strong> {esc(checks['method'])} A green state means the page returned
the expected fixture or statistic; an amber state means the page changed or only part of its text could be read; a
grey state means no usable listing remained. Each row links the exact page that was opened.</div>

<h2>The fifteen OLBG hubs</h2>
<div class="table-wrap"><table class="data">
<thead><tr><th>Sport</th><th>Hub</th><th>State</th><th>First-hand observation</th><th>Review</th></tr></thead>
<tbody>{hub_check_rows}</tbody></table></div>

<h2>Official pages re-read</h2>
<div class="table-wrap"><table class="data">
<thead><tr><th>Sport</th><th>Publisher</th><th>Source</th><th>State</th><th>First-hand observation</th><th>Review</th></tr></thead>
<tbody>{official_check_rows}</tbody></table></div>
<p class="sub">The same dossier is committed in <code>data/final-desk/rechecks.json</code> and summarised in
<code>research/final-desk-1ecc0d92.md</code>. Changed events are also on
<a href="flagged.html">Flagged for review</a>.</p>
"""
    (OUT / "checks.html").write_text(page("Source checks", "checks.html", checks_body),
                                     encoding="utf-8")

    # ------------------------------------------------------------------ top five by sport
    sections = []
    for s in SPORTS:
        group = top5_by_sport[s]
        rows5 = "".join(
            f'<tr><td>{esc(r["home"])} <span class="tiny">v</span> {esc(r["away"])}</td>'
            f'<td class="tiny">{esc(r.get("start_display") or r["start_utc"])}</td>'
            f'<td><strong class="selection">{esc(r["selection"])}</strong>'
            f'<div class="tiny">{esc(r["market"])}</div></td>'
            f'<td>{badge(r["confidence"])}</td>'
            f'<td class="nowrap">{r["probability"] * 100:.1f}%</td>'
            f'<td class="nowrap">{money(r["american"], r["american_display"])}</td>'
            f'<td class="tiny">{esc(r["basis"])}</td>'
            f'<td>{src(r["official_url"])}</td></tr>'
            for r in group["lines"]
        )
        if rows5:
            table = ('<div class="table-wrap"><table class="data"><thead><tr>'
                     '<th>Event</th><th>Start</th><th>Selection and market</th><th>Confidence</th>'
                     '<th>Our chance</th><th>Our price</th><th>Basis</th><th>Sources</th>'
                     '</tr></thead><tbody>' + rows5 + '</tbody></table></div>')
        else:
            table = '<p class="sub">No in-band originated line is available for this sport.</p>'
        short = (f'<div class="notice warn"><strong>{group["count"]} of five selections available.</strong> '
                 f'{esc(group["reason"])}</div>' if group["reason"] else "")
        sections.append(f"""
<section id="{SLUG[s]}">
  <h2>{esc(s)} <span class="tiny">· {group['count']}/5</span></h2>
  {short}
  {table}
  <p class="sub"><a href="sports/{SLUG[s]}.html#top5">Open the full {esc(s)} page →</a></p>
</section>""")
    top5_body = f"""
<p class="eyebrow">Top 5 by sport</p>
<h1>The five strongest in-band lines for each requested sport</h1>
<p class="lede">These are selections from our own full market book, ordered by confidence and then by chance. They are
not copied bookmaker prices. Several can come from the same match when that is the only event with a complete official
input set; where fewer than five exist, the shortfall and its official reason are shown instead of inventing lines.</p>
<div class="cta"><a class="btn primary" href="picks.html">Published picks →</a>
<a class="btn" href="lines.html">Full {lines['count']}-line book</a>
<a class="btn" href="flagged.html">Coverage gaps</a></div>
{''.join(sections)}
"""
    (OUT / "top5.html").write_text(page("Top 5 by sport", "top5.html", top5_body),
                                   encoding="utf-8")

    # ------------------------------------------------------------------ methodology
    method_body = f"""
<p class="eyebrow">Method</p>
<h1>How every number on this desk is made</h1>
<p class="lede">No bookmaker price is used anywhere. Each probability comes from an official rate on the fixture
record, and the same data always produces the same page.</p>

<h2>1. The four families</h2>
<div class="grid">
  <div class="card"><h3>Poisson scoring</h3><p class="sub">Ice hockey and baseball. Expected score = geometric mean
  of a club's scoring rate and the opponent's conceding rate, so no league-wide constant is invented. Home
  multipliers 1.06 / 0.98. Ties are split because the money line includes overtime.</p></div>
  <div class="card"><h3>Normal margin</h3><p class="sub">Rugby union, rugby league, Gaelic games, basketball, tennis.
  A mean margin with a stated standard deviation: 13 points rugby union, 12 league, 9 Gaelic, 12.5 basketball,
  6 games tennis. Draws are removed by renormalising the two win tails.</p></div>
  <div class="card"><h3>Race to legs</h3><p class="sub">Darts. A per-leg chance from the evidence ladder, then a
  negative-binomial race to ten legs, which also gives the distribution of total legs used for the total market.</p></div>
  <div class="card"><h3>Evidence ladder</h3><p class="sub">Volleyball, handball, cricket, tennis and the two rugby
  league / Gaelic cards. Each side is placed on five rungs using only the facts on the record; one rung of
  separation is worth ten probability points from 50%. Never graded higher than medium.</p></div>
</div>

<h2>2. Handicaps carry the confident opinions</h2>
<p>−250 is a 71.43% chance, so a side we rate at 85% cannot be backed inside the requested band at all. The desk
therefore publishes a handicap ladder for every priced fixture and puts the pick on the line where our number lands
nearest 68%. That is a real, actionable way to hold an opinion about a heavy favourite, and it keeps every published
pick inside the band.</p>

<h2>3. Confidence</h2>
<div class="table-wrap"><table class="data">
<thead><tr><th>Grade</th><th>Rule</th><th>Where it is implemented</th></tr></thead><tbody>
<tr><td>{badge('high')}</td><td>Numeric family, 62% or better, quality 0.85+, price inside the band, and not a match
total (totals carry more variance and are capped at medium).</td>
<td><a href="../scripts/now_model.py">scripts/now_model.py</a> · <a href="../data/now/lines.json">lines.json</a></td></tr>
<tr><td>{badge('medium')}</td><td>55% or better inside the band, or a strong price built on a weaker input class.</td>
<td><a href="../scripts/now_model.py">scripts/now_model.py</a> · <a href="../data/now/picks.json">picks.json</a></td></tr>
<tr><td>{badge('low')}</td><td>Everything else, including any number within five points of a coin flip.</td>
<td><a href="../scripts/now_model.py">scripts/now_model.py</a></td></tr>
</tbody></table></div>

<h2>4. The 0-10 score</h2>
<p>Every pick carries one number so that picks from different sports can be compared without reading the price. It is
our chance of the selection winning, read on a 0-10 scale where <strong>5.0 is a coin flip</strong> and 10.0 would be
a certainty, shaded by how strong the basis is: a price built from a goals or points rate counts at face value, a
price built on the evidence ladder counts at 0.8 of its face value. The formula is
<code>score = 10 × chance × basis shade</code>, so two picks with the same chance and the same basis always carry the
same score, and no pick can score above 7.5 while the band stops at 71.4%.</p>
<div class="table-wrap"><table class="data">
<thead><tr><th>Example</th><th>Our chance</th><th>Basis</th><th>Score</th><th>Where it is implemented</th></tr></thead><tbody>
<tr><td>Rugby union handicap at −249</td><td>71.4%</td><td>normal margin (full)</td><td>{score_chip(7.1)}</td>
<td><a href="../scripts/now_model.py">score_for() in scripts/now_model.py</a></td></tr>
<tr><td>Volleyball on the evidence ladder</td><td>70.0%</td><td>class ladder (0.8)</td><td>{score_chip(5.6)}</td>
<td><a href="../data/now/picks.json">data/now/picks.json</a></td></tr>
<tr><td>Anything at 50%</td><td>50.0%</td><td>any</td><td>{score_chip(5.0)}</td>
<td><a href="../scripts/now_verify.py">scripts/now_verify.py</a> checks the arithmetic</td></tr>
</tbody></table></div>

<h2>5. What is never done</h2>
<ul class="clean">
  <li>No bookmaker or exchange price is read, and no OLBG tip share is turned into a price.</li>
  <li>No value is inferred. If a field is not on an official page it stays blank and is published on
  <a href="flagged.html">Flagged for review</a>.</li>
  <li>No row is promoted to high confidence to fill a five-a-day target.</li>
  <li>Displayed times are not converted from one timezone to another.</li>
</ul>

<h2>6. Rebuilding</h2>
<pre class="tiny">python scripts/now_seed.py
python scripts/now_model.py
python scripts/now_predictions.py
python scripts/now_build.py
python scripts/now_verify.py</pre>
"""
    (OUT / "methodology.html").write_text(page("Method", "methodology.html", method_body),
                                          encoding="utf-8")

    # ------------------------------------------------------------------ flagged
    frows = "".join(
        f'<tr id="{esc(f["id"])}"><td class="nowrap">{esc(f["id"])}</td>'
        f'<td>{badge("medium" if f["severity"] == "open" else "low")}</td>'
        f'<td>{esc(f["sport"])}</td>'
        f'<td><strong>{esc(f["item"])}</strong><div class="tiny">{esc(f["detail"])}</div></td>'
        "<td>" + flag_source(f["source"]) + "</td></tr>"
        for f in payload_flags["flags"]
    )
    flagged_body = f"""
<p class="eyebrow">Flagged for review</p>
<h1>{payload_flags['count']} items for your review</h1>
<p class="lede">Nothing on this page blocks publication. It is the list of what could not be confirmed, what was
corrected, and where the five-a-day target was not met, each with the source that was checked.</p>
<div class="table-wrap"><table class="data">
<thead><tr><th>ID</th><th>State</th><th>Sport</th><th>Item and detail</th><th>Source</th></tr></thead>
<tbody>{frows}</tbody></table></div>
"""
    (OUT / "flagged.html").write_text(page("Flagged for review", "flagged.html", flagged_body),
                                      encoding="utf-8")

    # ------------------------------------------------------------------ sports
    def sport_pages():
        rows = []
        for s in SPORTS:
            st = matches["by_sport"][s]
            rows.append(
                f'<a class="sportcard" href="{SLUG[s]}.html"><div class="head"><h3>{esc(s)}</h3>'
                f'<span class="pill">{st["fixtures"]} fixtures</span></div>'
                f'<p class="sub">{st["priced"]} priced · {st["picks"]} picks · '
                f'{preds["by_sport"].get(s, 0)} written · {top5_by_sport[s]["count"]}/5 top lines · '
                f'{st["high"]} high</p></a>'
            )
        body = f"""
<p class="eyebrow">By sport</p>
<h1>Fifteen sports, same layout on every page</h1>
<p class="lede">Each sport page shows the fixtures, the picks, the five strongest in-band lines and the written
predictions in the same order, so once you have read one you know where everything is on the others.</p>
<div class="cta"><a class="btn primary" href="../top5.html">See all 15 top-fives →</a>
<a class="btn" href="../checks.html">Source checks</a></div>
<div class="sportgrid">{''.join(rows)}</div>
"""
        (OUT / "sports" / "index.html").write_text(
            page("By sport", "sports/index.html", body, prefix="../"), encoding="utf-8")

        for s in SPORTS:
            st = matches["by_sport"][s]
            sp_matches = [m for m in matches["matches"] if m["sport"] == s]
            sp_picks = [p for p in picks["picks"] if p["sport"] == s]
            sp_preds = [p for p in preds["predictions"] if p["sport"] == s]
            sp_top5 = top5_by_sport[s]
            top5_rows = "".join(
                f'<tr><td><strong class="selection">{esc(r["selection"])}</strong>'
                f'<div class="tiny">{esc(r["market"])}</div></td>'
                f'<td>{badge(r["confidence"])}</td>'
                f'<td class="nowrap">{r["probability"] * 100:.1f}%</td>'
                f'<td class="nowrap">{money(r["american"], r["american_display"])}</td>'
                f'<td class="tiny">{esc(r["basis"])}</td>'
                f'<td>{src(r["official_url"])}</td></tr>'
                for r in sp_top5["lines"]
            )
            top5_table = (
                '<div class="table-wrap"><table class="data"><thead><tr>'
                '<th>Selection and market</th><th>Confidence</th><th>Our chance</th><th>Our price</th>'
                '<th>Basis</th><th>Official source</th></tr></thead><tbody>' + top5_rows +
                '</tbody></table></div>'
                if top5_rows else
                '<p class="sub">No in-band originated line is available for this sport.</p>'
            )
            top5_note = (
                f'<div class="notice warn"><strong>{sp_top5["count"]} of five selections available.</strong> '
                f'{esc(sp_top5["reason"])}</div>'
                if sp_top5["reason"] else ""
            )
            mrows = "".join(
                f'<tr id="{esc(m["id"])}"><td><div class="teams">{esc(m["home"])} <span>v</span> {esc(m["away"])}</div>'
                f'<div class="tiny">{esc(m["competition"])}</div></td>'
                f'<td class="tiny">{esc(m.get("start_display") or m["start_utc"])}</td>'
                + "<td>" + primary_cell(m) + "</td>"
                + "<td>" + conf_cell(m) + "</td>"
                f'<td>{src(m["official_url"])}</td></tr>'
                for m in sp_matches
            )
            pblocks = []
            for p in sp_preds:
                pblocks.append(f"""
<article class="pred" id="pred-{esc(p['fixture_id'])}">
  <div class="sub">{esc(p['competition'])} · {esc(p.get('start_display') or p['start_utc'])}</div>
  <h3>{esc(p['headline'])}</h3>
  <div class="teams">{esc(p['home'])} <span>v</span> {esc(p['away'])}</div>
  <p style="margin-top:8px"><span class="selection">{esc(p['selection'])}</span>
  <span class="tiny">· {esc(p['market'])} · {p['probability'] * 100:.1f}% · {esc(p['american_display'])}</span>
  {badge(p['confidence'])}</p>
  <p>{esc(p['text'])}</p>
  <div class="facts"><div class="tiny"><strong>Official facts</strong></div>{facts_list(p['facts'])}</div>
</article>""")
            if sp_picks:
                sport_pick_table = ('<div class="table-wrap"><table class="data"><thead><tr>'
                                    '<th>Confidence</th><th>Sport</th><th>Match</th><th>Selection</th>'
                                    '<th>Our chance</th><th>Our price</th><th>Official source</th>'
                                    '</tr></thead><tbody>'
                                    + "".join(pick_line(p, prefix="../", with_pred=pred_ids) for p in sp_picks
                      if not p["started"])
                                    + "</tbody></table></div>")
            else:
                sport_pick_table = '<p class="sub">No pick published for this sport.</p>'
            gap = 5 - len(sp_preds)
            gap_note = ("" if gap <= 0 else
                        f'<div class="notice warn"><strong>{gap} short of five written predictions.</strong> '
                        f'Only fixtures with an official record that carries the needed rates can be written up '
                        f'honestly; see <a href="../flagged.html">Flagged for review</a>.</div>')
            body = f"""
<p class="eyebrow">Sport</p>
<h1>{esc(s)}</h1>
<p class="lede">{st['fixtures']} fixtures, {st['priced']} priced, {st['markets']} originated prices,
{st['picks']} picks ({st['high']} high, {st['medium']} medium, {st['low']} low), {sp_top5['count']} of five
top lines and {len(sp_preds)} written predictions. {st['olbg_listed']} of the fixtures were listed by OLBG at capture.</p>
<div class="cta"><a class="btn" href="../picks.html">All picks</a>
<a class="btn" href="../predictions.html">All predictions</a>
<a class="btn" href="../lines.html">All lines</a>
<a class="btn" href="../top5.html#{SLUG[s]}">All top fives</a></div>
<h2 id="fixtures">Fixtures</h2>
<div class="table-wrap"><table class="data">
<thead><tr><th>Match</th><th>Start</th><th>Selection or reason for a blank</th><th>Confidence</th><th>Official source</th></tr></thead>
<tbody>{mrows}</tbody></table></div>
<h2 id="picks">Picks</h2>
{sport_pick_table}
<h2 id="top5">Top 5 in-band lines</h2>
<p class="sub">The strongest selections from this sport's full market book. These can be on different markets within
one match when the official evidence supports only one fixture. <a href="../top5.html#{SLUG[s]}">See all sports →</a></p>
{top5_note}
{top5_table}
<h2 id="predictions">Written predictions</h2>
{gap_note}
{''.join(pblocks) if pblocks else '<p class="sub">No written prediction for this sport, and the reason is published on the flagged page.</p>'}
"""
            (OUT / "sports" / f"{SLUG[s]}.html").write_text(
                page(s, f"sports/{SLUG[s]}.html", body, prefix="../"), encoding="utf-8")

    sport_pages()

    pages_written = len(list(OUT.rglob("*.html")))
    print(f"now_build: {pages_written} pages, {matches['count']} fixtures, "
          f"{picks['count']} picks, {preds['count']} predictions, "
          f"{payload_top5['count']} top-five selections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
