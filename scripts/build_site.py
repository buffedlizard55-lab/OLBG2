#!/usr/bin/env python3
"""Build the unified OLBG2 research dashboard at the repository root.

The published dataset is the /verified/ primary-source desk (155 rows across 15
of the 17 eligible sports). The four earlier layers are preserved untouched and
indexed from archive.html; none of their rows is counted twice here.

Outputs (all deterministic):
  index.html, matches.html, verification.html, picks.html, flagged.html,
  methodology.html, sources.html, archive.html, sports/index.html,
  sports/<slug>.html, assets/style.css, integration.html
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VERIFIED = DATA / "verified"
SITE = ROOT

AS_OF = "2026-10-22"
AS_OF_CLOCK = "2026-10-22 01:30 UTC"
TODAY = "2026-10-22"


# --------------------------------------------------------------------------- data
def load(name: str):
    """Load a file from data/ (kept for the integration tests)."""
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def load_verified(name: str):
    return json.loads((VERIFIED / name).read_text(encoding="utf-8"))


CAPTURED_AT = "2026-10-22"  # set from data/verified/matches.json by dataset()
SNAPSHOT = {"rows": 119, "originated": 93, "band": 14, "flags": 26}  # refreshed by dataset()
_MONTHS = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
           "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}


def dataset():
    global CAPTURED_AT
    payload = load_verified("matches.json")
    CAPTURED_AT = payload.get("captured_at") or CAPTURED_AT
    SNAPSHOT.update(
        rows=len(payload["matches"]),
        originated=sum(1 for m in payload["matches"] if m.get("line_status") == "originated"),
        band=sum(1 for m in payload["matches"] if m.get("band_pick")),
        flags=len(load_verified("flagged.json")["items"]),
    )
    matches = payload["matches"]
    preds = load_verified("predictions.json")["predictions"]
    flags = load_verified("flagged.json")["items"]
    sports = load_verified("sports.json")
    band = load_verified("band.json")
    return matches, preds, flags, sports, band


# --------------------------------------------------------------------------- helpers
def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def status_of(row: dict) -> str:
    date = row.get("date") or ""
    if date < TODAY:
        return "past"
    if date == TODAY:
        return "today"
    return "upcoming"


def pct(prob) -> str:
    return "—" if prob is None else f"{prob * 100:.1f}%"


def odds(price) -> str:
    return "—" if price is None else f"{price:.2f}"


def domain(url: str) -> str:
    return urlsplit(url).netloc.replace("www.", "")


def markets_cell(row: dict) -> str:
    if row["line_status"] != "originated":
        reason = row.get("blank_reason") or "unconfirmed on the official feed"
        return f'<span class="blank">—</span><div class="tiny">{esc(reason)}</div>'
    bits = []
    ml = row.get("winner_market")
    if ml:
        if ml.get("draw_prob") is not None:
            bits.append(
                f'<div><b>1X2</b> {pct(ml["home_prob"])} / {pct(ml["draw_prob"])} / {pct(ml["away_prob"])}</div>'
            )
        else:
            bits.append(
                f'<div><b>ML</b> {pct(ml["home_prob"])} / {pct(ml["away_prob"])}</div>'
            )
    hcp = row.get("handicap_market")
    if hcp:
        bits.append(
            f'<div><b>HCP</b> {esc(hcp["line"])} · {pct(hcp["fav_prob"])} / {pct(hcp["dog_prob"])}</div>'
        )
    total = row.get("total_market")
    if total:
        bits.append(
            f'<div><b>Total</b> {esc(total["line"])} · O {pct(total["over_prob"])} / U {pct(total["under_prob"])}</div>'
        )
    return "".join(bits)


def pick_cell(row: dict) -> str:
    pick = row.get("pick")
    if not pick:
        return '<span class="blank">—</span>'
    conf = pick["confidence"]
    out = [
        f'<div class="pick">{esc(pick["selection"])}</div>',
        f'<div class="tiny">{pct(pick["probability"])} · {odds(pick["fair_odds"])} · '
        f'<span class="badge {conf}">{conf}</span></div>',
    ]
    bp = row.get("band_pick")
    if bp:
        out.append(
            f'<div class="bandline">Band pick: {esc(bp["selection"])} · '
            f'{pct(bp["probability"])} · {odds(bp["fair_odds"])}</div>'
        )
    return "".join(out)


def source_cell(row: dict) -> str:
    url = row.get("official_url") or ""
    if not url:
        return '<span class="blank">—</span>'
    scope = row.get("source_scope", "competition")
    label = "fixture page" if scope == "fixture" else "competition page"
    return (
        f'<a href="{esc(url)}" rel="noopener">{esc(domain(url))}</a>'
        f'<div class="tiny">{label}</div>'
    )


def verified_cell(row: dict) -> str:
    v = row.get("verification") or {}
    status = v.get("status", "captured")
    if status == "reverified":
        return '<span class="badge ok">re-verified 22 Oct</span>'
    day = CAPTURED_AT[8:10].lstrip("0") if len(CAPTURED_AT) >= 10 else CAPTURED_AT
    month = _MONTHS.get(CAPTURED_AT[5:7], "") if len(CAPTURED_AT) >= 10 else ""
    return f'<span class="badge warn">captured {day} {month}</span>'


def ordered_rows(rows: list[dict]) -> list[dict]:
    """Today, then upcoming ascending, then past most-recent-first."""
    upcoming = sorted(
        [m for m in rows if status_of(m) != "past"], key=lambda m: (m["date"], m.get("time") or "")
    )
    past = sorted(
        [m for m in rows if status_of(m) == "past"],
        key=lambda m: (m["date"], m.get("time") or ""),
        reverse=True,
    )
    return upcoming + past


def match_table(rows: list[dict], *, show_sport: bool = True) -> str:
    rows = ordered_rows(rows)
    head = ["Date", "Status", "Match", "Markets (model)", "Pick", "Source", "Evidence"]
    if show_sport:
        head.insert(2, "Sport")
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    body = []
    for m in rows:
        status = status_of(m)
        cells = [
            f'<td class="nowrap">{esc(m["date"])}</td>',
            f'<td><span class="badge {status}">{status}</span></td>',
        ]
        if show_sport:
            cells.append(
                f'<td><a href="sports/{esc(m["sport"])}.html">{esc(m["sport_name"])}</a>'
                f'<div class="tiny">{esc(m["competition"])}</div></td>'
            )
        cells += [
            f'<td><div class="teams">{esc(m["home"])} <span>v</span> {esc(m["away"])}</div>'
            f'<div class="tiny">{esc(m.get("venue") or "venue unconfirmed")}</div></td>',
            f"<td>{markets_cell(m)}</td>",
            f"<td>{pick_cell(m)}</td>",
            f"<td>{source_cell(m)}</td>",
            f"<td>{verified_cell(m)}</td>",
        ]
        body.append(
            f'<tr class="row-{status}" data-sport="{esc(m["sport"])}" '
            f'data-status="{status}" data-conf="{esc((m.get("pick") or {}).get("confidence", "none"))}">'
            + "".join(cells)
            + "</tr>"
        )
    return (
        f'<div class="table-wrap"><table class="data"><thead><tr>{th}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def filter_bar(sports: list[tuple[str, str]], *, status=True, conf=True) -> str:
    sport_opts = "".join(f'<option value="{esc(s)}">{esc(n)}</option>' for s, n in sports)
    extra = ""
    if status:
        extra += (
            '<select id="f-status"><option value="">All dates</option>'
            '<option value="upcoming">Upcoming</option><option value="today">Today</option>'
            '<option value="past">Past</option></select>'
        )
    if conf:
        extra += (
            '<select id="f-conf"><option value="">All confidence</option>'
            '<option value="high">High</option><option value="medium">Medium</option>'
            '<option value="low">Low</option><option value="none">Unlined</option></select>'
        )
    return f'''<div class="filters">
  <input id="f-text" type="search" placeholder="Search team, competition, venue…" aria-label="Search">
  <select id="f-sport"><option value="">All sports</option>{sport_opts}</select>
  {extra}
  <span id="f-count" class="tiny"></span>
</div>
<script>
document.addEventListener('DOMContentLoaded', function () {{
  var rows = Array.prototype.slice.call(document.querySelectorAll('table.data tbody tr'));
  var t = document.getElementById('f-text'), s = document.getElementById('f-sport');
  var st = document.getElementById('f-status'), c = document.getElementById('f-conf');
  var out = document.getElementById('f-count');
  function apply() {{
    var q = (t.value || '').toLowerCase(), n = 0;
    rows.forEach(function (r) {{
      var ok = (!q || r.textContent.toLowerCase().indexOf(q) !== -1)
        && (!s.value || r.dataset.sport === s.value)
        && (!st || !st.value || r.dataset.status === st.value)
        && (!c || !c.value || r.dataset.conf === c.value);
      r.style.display = ok ? '' : 'none';
      if (ok) n++;
    }});
    out.textContent = n + ' of ' + rows.length + ' rows';
  }}
  [t, s, st, c].forEach(function (el) {{ if (el) el.addEventListener('input', apply); }});
  apply();
}});
</script>'''


# --------------------------------------------------------------------------- shell
NAV = [
    ("index.html", "Dashboard"),
    ("matches.html", "All matches"),
    ("sports/index.html", "Sports"),
    ("picks.html", "Picks"),
    ("verification.html", "Verification"),
    ("flagged.html", "Flagged"),
    ("methodology.html", "Methodology"),
    ("sources.html", "Sources"),
    ("archive.html", "Archive"),
    ("integration.html", "Cross-layer review"),
]


def page(title: str, active: str, body: str, prefix: str = "") -> str:
    links = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{prefix}{esc(href)}"{current}>{esc(label)}</a>')
    nav = "".join(links)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG2</title>
<meta name="description" content="Dated OLBG reverse-engineering research: officially sourced fixtures, independently originated lines, confidence-graded picks and open review items.">
<link rel="stylesheet" href="{prefix}assets/style.css"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f172a'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%2314b8a6'/%3E%3C/svg%3E">
</head>
<body>
<header class="topbar">
  <div class="wrap bar">
    <a class="brand" href="{prefix}index.html"><span class="dot"></span>OLBG2 <span class="brand-sub">research desk</span></a>
    <nav class="nav" aria-label="Main navigation">{nav}</nav>
  </div>
</header>
<div class="stripe"><div class="wrap"><strong>Snapshot {AS_OF_CLOCK}</strong> · {SNAPSHOT["rows"]} stored rows · {SNAPSHOT["originated"]} originated lines · {SNAPSHOT["band"]} price-band picks · every row carries its official source link · <a href="{prefix}flagged.html">{SNAPSHOT["flags"]} open review items</a></div></div>
<main class="wrap">
{body}
</main>
<footer class="footer"><div class="wrap">
  <p><strong>Dated, partial research snapshot — not a live feed and not betting advice.</strong> Model probabilities are estimates, not guarantees. Rows dated before {TODAY} are labelled <em>past</em> and are not presented as upcoming. Unconfirmed values are blank (<code>—</code>) and listed on <a href="{prefix}flagged.html">Flagged for Review</a>. 18+.</p>
  <p class="tiny">Built by <code>scripts/build_site.py</code> from checked-in data. Earlier layers are preserved at <a href="{prefix}verified/index.html">/verified/</a>, <a href="{prefix}live/index.html">/live/</a>, <a href="{prefix}survey/index.html">/survey/</a>, <a href="{prefix}site/index.html">/site/</a> and indexed in the <a href="{prefix}archive.html">archive</a>.</p>
</div></footer>
</body>
</html>
"""


# --------------------------------------------------------------------------- pages
def build_index(matches, preds=None, flagged=None) -> str:
    rows, predictions, flags, sports, band = dataset()
    counts = Counter(m["sport"] for m in rows)
    originated = sum(1 for m in rows if m["line_status"] == "originated")
    band_picks = sum(1 for m in rows if m.get("band_pick"))
    high = sum(1 for m in rows if (m.get("pick") or {}).get("confidence") == "high")
    upcoming = [m for m in rows if status_of(m) != "past"]
    today = [m for m in rows if status_of(m) == "today"]
    past = sum(1 for m in rows if status_of(m) == "past")
    reverified = sum(1 for m in rows if (m.get("verification") or {}).get("status") == "reverified")
    fixture_scope = sum(1 for m in rows if m.get("source_scope") == "fixture")
    total = len(rows)
    competitions = len({m["competition"] for m in rows})
    sports_with_rows = len(counts)
    blank = total - originated
    band_count = len(band["selections"])
    pred_count = len(predictions)
    high_pred = sum(1 for p in predictions if p.get("match_type") != "band")
    flag_count = len(flags)
    conf = Counter((m.get("pick") or {}).get("confidence", "none") for m in rows)
    past_dated = sum(1 for m in rows if m["date"] < TODAY)
    max_price = max((p["fair_odds"] for p in predictions), default=0)

    cards = []
    for s in sports["eligible_sports"]:
        n = counts.get(s["slug"], 0)
        lined = sum(1 for m in rows if m["sport"] == s["slug"] and m["line_status"] == "originated")
        hp = sum(
            1
            for m in rows
            if m["sport"] == s["slug"] and (m.get("pick") or {}).get("confidence") == "high"
        )
        note = s["status_summary"]
        cards.append(
            f'<a class="card sport" href="sports/{esc(s["slug"])}.html">'
            f'<div class="cardhead"><h3>{esc(s["name"])}</h3><span class="pill">{n} rows</span></div>'
            f'<p>{esc(note)}</p>'
            f'<div class="metrics"><span><b>{lined}</b> lined</span><span><b>{hp}</b> high</span>'
            f'<span><b>{n - lined}</b> blank</span></div></a>'
        )

    next_rows = sorted(
        [m for m in rows if status_of(m) != "past"], key=lambda m: (m["date"], m["time"] or "")
    )[:12]

    body = f"""
<section class="hero">
  <p class="eyebrow">OLBG reverse-engineering · primary-source verification · independent line origination</p>
  <h1>Every eligible OLBG sport, one verified table.</h1>
  <p class="lede">A <strong>dated, partial research snapshot</strong> of {total} fixtures across {sports_with_rows} of the 17 eligible sports,
  excluding soccer/football, horse racing, American football, boxing, UFC/MMA, hurling, cycling and specials.
  Fixture IDs, teams, dates and start times are linked to the governing body or league that publishes them;
  source links <strong>do not mean every fixture or input was independently re-checked</strong> in this audit.
  Model prices and confidence labels are our own estimates.</p>
  <div class="cta"><a class="button primary" href="matches.html">Browse all {total} rows</a>
  <a class="button" href="picks.html">{band_count} price-band picks</a>
  <a class="button" href="flagged.html">Open review items</a></div>
</section>

<div class="kpis">
  <div class="kpi"><div class="v">{total}</div><div class="k">stored rows</div><div class="s">{sports_with_rows} sports · {competitions} competitions</div></div>
  <div class="kpi"><div class="v">{originated}</div><div class="k">originated lines</div><div class="s">moneyline, handicap, total</div></div>
  <div class="kpi"><div class="v">{band_count}</div><div class="k">price-band picks</div><div class="s">≥70% and −250 to +10000</div></div>
  <div class="kpi"><div class="v">{pred_count}</div><div class="k">written predictions</div><div class="s">all {band_count} in the −250…+10000 band, 30+ words</div></div>
  <div class="kpi"><div class="v">6</div><div class="k">source families re-read 22 Oct</div><div class="s">NHL · URC · Top 14 · Pro D2 · EuroLeague · EHF</div></div>
  <div class="kpi"><div class="v">{flag_count}</div><div class="k">open review items</div><div class="s">blank, stale or irregular</div></div>
</div>

<div class="notice"><strong>Read the date column.</strong> {past_dated} rows are dated before 2026-10-22 and are already past;
{len(today)} are dated today and {len(upcoming) - len(today)} are later. Past rows stay visible for
audit but are never presented as upcoming tips. <a href="verification.html">Verification ledger</a> · <a href="methodology.html">Methodology</a></div>

<h2>Sports covered</h2>
<p class="sub">All 17 eligible OLBG sports are shown. “0 rows” means the sport's official body published no fixture
inside this capture window (Aussie Rules is off-season; eSports showed no active tips), not that the sport was skipped
silently. <a href="sports/index.html">Open the category index</a>.</p>
<div class="grid sports">{"".join(cards)}</div>

<h2>Next fixtures in the snapshot</h2>
<p class="sub">Ordered by local fixture date and published start time. Every row links to the official page it was read from.</p>
{match_table(next_rows)}

<h2>Analysis</h2>
<p class="sub">These figures are computed from the published dataset itself, not from any external claim.</p>
<div class="two-col">
  <div class="panel"><h3>Coverage and evidence</h3><ul>
    <li><strong>{originated} of {total} rows ({originated / total * 100:.0f}%)</strong> carry originated prices — moneyline and handicap on every lined row, plus totals wherever the official feed publishes scoring data; {blank} rows are blank with a stated reason.</li>
    <li><strong>{fixture_scope} of {total} rows</strong> cite a URL that identifies the individual fixture; the remaining {total - fixture_scope} cite a competition or rankings page, disclosed as VF-11.</li>
    <li><strong>6 official source families</strong> were re-read line by line on 2026-10-22 and every compared figure matched except one corrected form sentence; the coverage limit, and which rows were not re-read, are published as VF-23. The snapshot itself was captured on 2026-10-22.</li>
    <li>The snapshot spans <strong>{competitions} competition labels</strong> in {sports_with_rows} sports; Aussie Rules and eSports returned no active fixtures and are shown empty rather than skipped.</li>
  </ul></div>
  <div class="panel"><h3>Prices and confidence</h3><ul>
    <li>Confidence split: <strong>{conf.get('high', 0)} high</strong>, {conf.get('medium', 0)} medium, {conf.get('low', 0)} low, {conf.get('none', 0)} unlined/no pick.</li>
    <li><strong>{band_count} band picks</strong> sit at fair odds 1.40-1.42 with model probabilities of 70.0-71.4%, the only window satisfying both the ≥70% rule and the −250 floor.</li>
    <li>Moneyline picks graded high (&ge;72%) whose fair price is shorter than the &minus;250 floor stay on the sport tables without a written prediction, rather than padding the picks page with ultra-short prices.</li>
    <li>The longest fair price anywhere in the {pred_count} predictions is <strong>{max_price:.2f}</strong>, inside the +10000 ceiling.</li>
  </ul></div>
</div>

<h2>What this project does — and does not do</h2>
<div class="two-col">
  <div class="panel"><h3>Does</h3><ul>
    <li>Records OLBG's sport taxonomy and excludes the eight categories in the brief.</li>
    <li>Reads fixture, date, venue and form data from governing bodies or leagues.</li>
    <li>Originates its own moneyline, handicap and total prices from those inputs.</li>
    <li>Writes unique, sourced predictions for every published high-confidence pick.</li>
    <li>Leaves unconfirmed values blank and publishes them for review.</li>
  </ul></div>
  <div class="panel"><h3>Does not</h3><ul>
    <li>Claim a live, exhaustive OLBG schedule — the capture is dated {AS_OF_CLOCK}.</li>
    <li>Copy bookmaker odds or tipster percentages into the model.</li>
    <li>Fill a missing venue, ranking or total with an inferred value.</li>
    <li>Guarantee any selection; confidence is an estimate, not certainty.</li>
    <li>Present past fixtures as upcoming.</li>
  </ul></div>
</div>
"""
    return page("Unified dashboard", "index.html", body)


def build_matches() -> str:
    rows, *_ = dataset()
    sports = sorted({(m["sport"], m["sport_name"]) for m in rows}, key=lambda x: x[1])
    counts = Counter(status_of(m) for m in rows)
    body = f"""
<h1>All matches</h1>
<p class="lede">The complete published dataset: <strong>{len(rows)} rows</strong> across
<strong>{len({m['sport'] for m in rows})} sports</strong>. Filter by sport, date status or confidence.
Every row carries the official page it was read from and a verification badge; unlined rows show an em dash
plus the reason no price was originated.</p>
<div class="kpis small">
  <div class="kpi"><div class="v">{counts['upcoming']}</div><div class="k">upcoming</div></div>
  <div class="kpi"><div class="v">{counts['today']}</div><div class="k">today</div></div>
  <div class="kpi"><div class="v">{counts['past']}</div><div class="k">past</div></div>
  <div class="kpi"><div class="v">{sum(1 for m in rows if m['line_status'] == 'originated')}</div><div class="k">lined</div></div>
  <div class="kpi"><div class="v">{sum(1 for m in rows if m['line_status'] != 'originated')}</div><div class="k">blank / flagged</div></div>
</div>
{filter_bar(sports)}
{match_table(rows)}
<p class="tiny">Confidence badge colours: <span class="badge high">high</span> model probability ≥72% (or a band pick ≥70%),
<span class="badge medium">medium</span> ≥60%, <span class="badge low">low</span> below 60%.
The price-band picks are a separate, stricter list: model probability ≥70% <em>and</em> fair odds 1.40-101.00.</p>
"""
    return page("All matches", "matches.html", body)


def build_sport_page(slug: str, meta: dict) -> str:
    rows, preds, flags, sports, band = dataset()
    mine = [m for m in rows if m["sport"] == slug]
    lined = [m for m in mine if m["line_status"] == "originated"]
    blank = [m for m in mine if m["line_status"] != "originated"]
    hp = [m for m in mine if (m.get("pick") or {}).get("confidence") == "high"]
    bp = [m for m in mine if m.get("band_pick")]
    status = Counter(status_of(m) for m in mine)
    if not mine:
        reason = meta.get("status_summary", "No fixture was published inside the capture window.")
        body = f"""
<h1>{esc(meta['name'])}</h1>
<div class="notice"><strong>No rows in this snapshot.</strong> {esc(reason)}</div>
<p>The sport is in scope and was surveyed. Publishing no fixture is the honest result when the official body
lists none in the window; inventing one would break the project's verification rule.</p>
<p><a class="button" href="../sports/index.html">All sports</a> <a class="button" href="../methodology.html">Methodology</a></p>
"""
        return page(f"{meta['name']} — no rows", "sports/index.html", body, prefix="../")
    body = f"""
<p class="crumb"><a href="../index.html">Dashboard</a> / <a href="../sports/index.html">Sports</a> / {esc(meta['name'])}</p>
<h1>{esc(meta['name'])}</h1>
<p class="lede">{esc(meta['status_summary'])}</p>
<div class="kpis small">
  <div class="kpi"><div class="v">{len(mine)}</div><div class="k">rows</div></div>
  <div class="kpi"><div class="v">{len(lined)}</div><div class="k">lined</div></div>
  <div class="kpi"><div class="v">{len(blank)}</div><div class="k">blank</div></div>
  <div class="kpi"><div class="v">{len(hp)}</div><div class="k">high confidence</div></div>
  <div class="kpi"><div class="v">{len(bp)}</div><div class="k">band picks</div></div>
  <div class="kpi"><div class="v">{status['upcoming'] + status['today']}</div><div class="k">not yet played</div></div>
</div>
<div class="notice"><strong>Markets investigated:</strong> {esc(', '.join(meta.get('markets_investigated', [])))}.
Governing body: {esc(meta.get('governing_body', '—'))}.
<a href="{esc(meta.get('official_url', '#'))}" rel="noopener">Official hub</a></div>
{match_table(mine, show_sport=False)}
"""
    return page(f"{meta['name']} fixtures", "sports/index.html", body, prefix="../")


def build_sports_index() -> str:
    rows, preds, flags, sports, band = dataset()
    counts = Counter(m["sport"] for m in rows)
    cards = []
    for s in sports["eligible_sports"]:
        n = counts.get(s["slug"], 0)
        lined = sum(1 for m in rows if m["sport"] == s["slug"] and m["line_status"] == "originated")
        cards.append(
            f'<a class="card sport" href="{esc(s["slug"])}.html"><div class="cardhead">'
            f'<h3>{esc(s["name"])}</h3><span class="pill">{n} rows</span></div>'
            f'<p>{esc(s["status_summary"])}</p>'
            f'<div class="metrics"><span><b>{lined}</b> lined</span><span><b>{n - lined}</b> blank</span></div></a>'
        )
    excluded = "".join(
        f'<li><strong>{esc(x["label"])}</strong> — {esc(x["reason"])}</li>'
        for x in sports["excluded_sports"]
    )
    body = f"""
<p class="crumb"><a href="../index.html">Dashboard</a> / Sports</p>
<h1>Sports</h1>
<p class="lede">17 eligible OLBG sports. 15 carry rows in this snapshot; Aussie Rules and eSports were surveyed
and had no active fixtures. The eight excluded categories are listed at the bottom with the reason.</p>
<div class="grid sports">{"".join(cards)}</div>
<h2>Excluded by the brief</h2>
<ul class="excluded">{excluded}</ul>
"""
    return page("Sports index", "sports/index.html", body, prefix="../")


def build_picks() -> str:
    rows, preds, flags, sports, band = dataset()
    by_id = {m["id"]: m for m in rows}
    band_preds = sorted([p for p in preds if p.get("match_type") == "band"], key=lambda p: p["time"])
    primary = sorted([p for p in preds if p.get("match_type") != "band"], key=lambda p: p["time"])

    def pred_card(p: dict) -> str:
        row = by_id.get(p["match_id"], {})
        facts = "".join(
            f'<li>{esc(f["claim"])} — <a href="{esc(f["source"])}" rel="noopener">{esc(domain(f["source"]))}</a></li>'
            for f in p.get("facts", [])
        )
        band_tag = (
            '<span class="badge band">in band −250…+10000</span>'
            if p.get("match_type") == "band"
            else '<span class="badge outband">shorter than −250</span>'
        )
        return f'''<article class="pred">
  <div class="predhead"><div><span class="badge {esc(p['sport'])}">{esc(p['sport_name'])}</span>
  <span class="tiny">{esc(p['competition'])} · {esc(p['time'])}</span></div>{band_tag}</div>
  <h3>{esc(p['headline'])}</h3>
  <p class="selection">{esc(p['selection'])} · <strong>{pct(p['probability'])}</strong> · {odds(p['fair_odds'])} decimal · {p['word_count']} words</p>
  <p>{esc(p['text'])}</p>
  <div class="sources"><strong>Verified facts</strong><ul>{facts}</ul></div>
  <div class="predfoot"><a href="{esc(row.get('official_url', p.get('official_url', '#')))}" rel="noopener">Official fixture page</a>
  <a href="sports/{esc(p['sport'])}.html">All {esc(p['sport_name'])} rows</a></div>
</article>'''

    body = f"""
<h1>Picks &amp; predictions</h1>
<p class="lede">Two clearly separated lists. <strong>{len(band_preds)} price-band picks</strong> satisfy both rules in the brief:
model probability ≥70% and fair odds between −250 (1.40) and +10000 (101.00). Because a 70%+ probability cannot be
priced above 1.43, the qualifying window is narrow; we enumerated handicap and total ladders to find selections inside it.
{f'A further <strong>{len(primary)} high-confidence picks</strong> are strong model selections but priced shorter than −250, so they are labelled as outside the requested band rather than passed off as compliant.' if primary else 'There are no additional high-confidence picks outside the requested price band in this snapshot.'}</p>
<div class="notice"><strong>How the numbers are produced.</strong> Probabilities come from the sport-specific models documented in
<a href="methodology.html">Methodology</a>; prices are fair decimals (1/probability), not bookmaker quotes. Every prediction is
≥30 words, unique, and carries at least two facts with the official source that published them.</div>

<h2>Price-band picks ({len(band_preds)})</h2>
<p class="sub">All are dated 2026-10-22 or later at the snapshot. Each quotes its own probability and price.</p>
<div class="preds">{"".join(pred_card(p) for p in band_preds)}</div>

<h2>High-confidence picks outside the price band ({len(primary)})</h2>
<p class="sub">{('These selections are priced shorter than −250 and are disclosed separately, not re-labelled.' if primary else 'No selections in this category at this snapshot.')}</p>
<div class="preds">{"".join(pred_card(p) for p in primary)}</div>
"""
    return page("Picks and predictions", "picks.html", body)


def build_verification() -> str:
    rows, preds, flags, sports, band = dataset()
    counts = Counter(m["sport"] for m in rows)
    reverified = [m for m in rows if (m.get("verification") or {}).get("status") == "reverified"]
    fixture_scope = sum(1 for m in rows if m.get("source_scope") == "fixture")
    comp_scope = len(rows) - fixture_scope
    unlined = [m for m in rows if m["line_status"] != "originated"]
    rows_html = "".join(
        f'<tr><td>{esc(m["id"])}</td><td>{esc(m["sport_name"])}</td>'
        f'<td>{esc(m["home"])} v {esc(m["away"])}</td><td>{esc(m["date"])}</td>'
        f'<td>{esc((m.get("verification") or {}).get("scope", ""))}</td>'
        f'<td><a href="{esc(m["official_url"])}" rel="noopener">{esc(domain(m["official_url"]))}</a></td></tr>'
        for m in reverified
    )
    per_sport = "".join(
        f'<tr><td><a href="sports/{esc(s["slug"])}.html">{esc(s["name"])}</a></td>'
        f'<td>{counts.get(s["slug"], 0)}</td>'
        f'<td>{sum(1 for m in rows if m["sport"] == s["slug"] and m.get("source_scope") == "fixture")}</td>'
        f'<td>{sum(1 for m in rows if m["sport"] == s["slug"] and m["line_status"] == "originated")}</td>'
        f'<td>{sum(1 for m in rows if m["sport"] == s["slug"] and m["line_status"] != "originated")}</td></tr>'
        for s in sports["eligible_sports"]
    )
    body = f"""
<h1>Verification ledger</h1>
<p class="lede">Line-by-line evidence status for every published row. A value is published only when an official
governing-body or league page returned it; anything else is blank and listed on <a href="flagged.html">Flagged for Review</a>.
No value on this site was inferred from memory or copied from a secondary outlet.</p>

<div class="kpis">
  <div class="kpi"><div class="v">{len(rows)}</div><div class="k">published rows</div></div>
  <div class="kpi"><div class="v">6</div><div class="k">source families re-read 2026-10-22</div><div class="s">NHL · URC · Top 14 · Pro D2 · EuroLeague · EHF</div></div>
  <div class="kpi"><div class="v">{fixture_scope}</div><div class="k">fixture-scoped source</div><div class="s">URL identifies the match</div></div>
  <div class="kpi"><div class="v">{comp_scope}</div><div class="k">competition-scoped source</div><div class="s">URL confirms the league, not the match</div></div>
  <div class="kpi"><div class="v">{len(unlined)}</div><div class="k">unlined rows</div><div class="s">price deliberately blank</div></div>
</div>

<div class="notice warn"><strong>The {comp_scope} competition-scoped rows are the main evidence caveat.</strong>
Their official URL is an official rankings, standings or schedule page, but it does not itself identify the individual
fixture. The fixture, date and opponent rest on the OLBG listing captured on 2026-10-22 and are marked accordingly.
This is disclosed as <a href="flagged.html#VF-11">VF-11</a>.</div>

<h2>Re-read line by line on 2026-10-22</h2>
<p class="sub">Every figure below was re-fetched from the governing body in this session and compared with the published row.
The rows that were <em>not</em> re-read are named in <a href="flagged.html#VF-23">VF-23</a> rather than implied to be checked.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Source family</th><th>What was compared</th><th>Result</th><th>Official page</th></tr></thead><tbody>
<tr><td>NHL team rates</td><td>MIN 6-2-2 (31/25), CGY 2-6-0 (17/37), CAR 8-2-1 (42/27), EDM 7-1-1 (41/27), BOS 7-2-1 (36/22), NSH 3-2-3 (23/22)</td><td>All match</td><td><a href="https://api.nhle.com/stats/rest/en/team/summary" rel="noopener">api.nhle.com</a></td></tr>
<tr><td>NHL fixtures</td><td>12 games, ids, venues and 23:00Z start times on 22 October</td><td>Match</td><td><a href="https://api-web.nhle.com/v1/score/2026-10-22" rel="noopener">api-web.nhle.com</a></td></tr>
<tr><td>URC table + Round 3</td><td>All 16 clubs' PTS/PF/PA and five Round 3 scorelines</td><td>All match</td><td><a href="https://stats.unitedrugby.com/match-centre/table/2026-27" rel="noopener">stats.unitedrugby.com</a></td></tr>
<tr><td>Top 14</td><td>Toulouse 24 pts, 5-0-1, 197/124, W-W-W-W-W; Perpignan 9th</td><td>Match (Perpignan row detail truncated in fetch)</td><td><a href="https://top14.lnr.fr/classement" rel="noopener">top14.lnr.fr</a></td></tr>
<tr><td>Pro D2</td><td>Provence 7-0-0 (222/158), Aurillac 16 pts (240/254), Béziers 2-0-5 (147/240), Nevers 0-0-7 (146/222)</td><td>Match; one form sentence corrected (VF-25)</td><td><a href="https://prod2.lnr.fr/classement" rel="noopener">prod2.lnr.fr</a></td></tr>
<tr><td>EuroLeague</td><td>Panathinaikos 5-1 (528/438, +90, 4-1 home); Baskonia 20th 1-5 (504/564, 0-2 away)</td><td>Both match exactly</td><td><a href="https://www.euroleaguebasketball.net/en/euroleague/standings/" rel="noopener">euroleaguebasketball.net</a></td></tr>
<tr><td>EHF Champions League</td><td>Group E: Barça 4-0-0 (137:104), Montpellier 1-0-3 (116:125); fixture 202711020101049</td><td>Match</td><td><a href="https://ehfcl.eurohandball.com/men/2026-27/standings/" rel="noopener">ehfcl.eurohandball.com</a></td></tr>
</tbody></table></div>
<p class="tiny">Full comparison table and the list of rows not re-read: <a href="https://github.com/buffedlizard55-lab/OLBG2/blob/main/research/verification-072755db.md">research/verification-072755db.md</a>.</p>

<h2>Evidence by sport</h2>
<div class="table-wrap"><table class="data"><thead><tr><th>Sport</th><th>Rows</th><th>Fixture-scoped URL</th>
<th>Lined</th><th>Blank</th></tr></thead><tbody>{per_sport}</tbody></table></div>

<h2>What “verified” means here</h2>
<table class="data plain"><thead><tr><th>Badge</th><th>Meaning</th></tr></thead><tbody>
<tr><td><span class="badge warn">captured 22 Oct</span></td><td>The value was read from the cited official page on 2026-10-22 and is preserved with that provenance. Six source families (NHL, URC, Top 14, Pro D2, EuroLeague, EHF) were additionally re-read line by line that day; see <a href="https://github.com/buffedlizard55-lab/OLBG2/blob/main/research/verification-072755db.md">the verification report</a> and VF-23 for what was and was not re-checked.</td></tr>
<tr><td><span class="badge none">blank</span></td><td>The official source did not publish the value. The cell stays empty and the reason is on the flagged page.</td></tr>
</tbody></table>
"""
    return page("Verification ledger", "verification.html", body)


def build_flagged(flagged=None, matches=None) -> str:
    rows, preds, vflags, sports, band = dataset()
    layers = [("Verified desk", "2026-10-22", vflags)]
    root = load("flagged.json")
    layers.append(("Root dashboard", "2026-10-21", root.get("items", []) + root.get("resolved", [])))
    live = json.loads((DATA / "live" / "flags.json").read_text()).get("flags", [])
    layers.append(("Live slate", "2026-10-21", live))
    desk = json.loads((DATA / "desk" / "flagged.json").read_text()).get("flagged", [])
    layers.append(("Evidence desk v2", "2026-10-21", desk))
    survey = json.loads((DATA / "survey" / "flags.json").read_text())
    layers.append(("All-sport survey", "2026-10-21", survey))

    sections = []
    total = 0
    for name, date, items in layers:
        total += len(items)
        body_rows = []
        for item in items:
            iid = item.get("id", "")
            sev = item.get("severity", "")
            title = item.get("item") or item.get("title") or item.get("category") or ""
            detail = item.get("detail", "")
            src = item.get("source_url") or item.get("source") or ""
            cat = item.get("category") or item.get("area") or ""
            anchor = re.sub(r"[^A-Za-z0-9_-]", "-", iid)
            link = (
                f'<a href="{esc(src)}" rel="noopener">{esc(domain(src))}</a>'
                if isinstance(src, str) and src.startswith("http")
                else '<span class="blank">no source link recorded</span>'
            )
            body_rows.append(
                f'<tr id="{esc(anchor)}"><td class="nowrap">{esc(iid)}</td>'
                f'<td><span class="badge {esc(sev)}">{esc(sev)}</span></td>'
                f'<td><strong>{esc(title)}</strong><div class="tiny">{esc(cat)}</div></td>'
                f'<td>{esc(detail)}</td><td>{link}</td></tr>'
            )
        sections.append(
            f'<h2>{esc(name)} <span class="pill">{len(items)} items · {esc(date)}</span></h2>'
            + '<div class="table-wrap"><table class="data"><thead><tr><th>ID</th><th>Severity</th>'
              '<th>Finding</th><th>Detail</th><th>Source</th></tr></thead><tbody>'
            + "".join(body_rows)
            + "</tbody></table></div>"
        )
    body = f"""
<h1>Flagged for Review</h1>
<p class="lede">Every irregularity, blank value, stale row and unresolved disagreement found across the repository,
with the source that raised it. Nothing here blocks publication: the rule is to show the gap rather than fill it.
<strong>{total} items</strong> across five layers. The 18 verified-desk items are current; the rest are preserved from
earlier sessions and may already be closed.</p>
<div class="notice warn"><strong>How to read this page.</strong> Severity <em>high</em> means a published value or fixture
depends on a source that does not fully support it. <em>medium</em> means a value is blank, stale or capped.
<em>low</em> is a documented limitation. Items with no source link are marked explicitly.</div>
{sections[0]}
{sections[1]}
{sections[2]}
{sections[3]}
{sections[4]}
"""
    return page("Flagged for Review", "flagged.html", body)


def build_methodology(matches=None) -> str:
    rows, preds, flags, sports, band = dataset()
    models = [
        ("Ice Hockey", "Bivariate Poisson goal grid, 8-game shrinkage to the league mean, +5% home attack, 52% of regulation ties to the home side. Markets: moneyline, ±1.5 puck line, 5.5/6.5 total."),
        ("Basketball (EuroLeague / EuroCup)", "Normal margin model from points for/against, 3-game shrinkage, +3.4 home court, σ=10.8; totals σ=13.5. Markets: moneyline, handicap, total."),
        ("Basketball (NBA)", "Logistic model from 2025-26 win records, +0.28 home logit, margin σ=12. Totals deliberately blank because nba.com standings omit points for/against. Confidence capped at medium."),
        ("Rugby Union", "Normal points model from league tables, 3-game shrinkage, +4.2 home advantage, σ=12.6; draw band included; totals σ=14.2. Markets: 1X2, draw-no-bet, handicap, total."),
        ("Handball", "Poisson goal grid from EHF group standings, +6% home attack, no draw split. Markets: 1X2, handicap, total."),
        ("Darts", "Binomial leg model from official PDC prize-money rankings; best-of-11 legs. Markets: match winner, leg handicap, total legs."),
        ("Tennis", "Best-of-three set model from ATP ranking points. Markets: match winner, set handicap, total sets."),
        ("Snooker", "Best-of-seven frame model from WST two-year ranking money. Markets: match winner, frame handicap, total frames."),
        ("Baseball", "Poisson run model from 162-game runs scored/allowed, 4% home factor. Markets: moneyline, run line, total."),
        ("Motor Racing", "Plackett-Luce-style weights from official FIA points (exponent 1.65) with an 8% residual field share; championship model uses a normal CDF over the points gap."),
    ]
    model_rows = "".join(f"<tr><td><strong>{esc(a)}</strong></td><td>{esc(b)}</td></tr>" for a, b in models)
    body = f"""
<h1>Methodology &amp; models</h1>
<p class="lede">How the {len([r for r in rows if r.get("line_status") == "originated"])} originated lines, the confidence labels and the {len(preds)} predictions are produced — and where the
limits are. This is a research model, not a bookmaker. Rows include source links to the official input page, but a link
does not by itself prove the page supported every field; the <a href="verification.html">verification ledger</a> records
what was actually checked.</p>

<h2>Pipeline</h2>
<ol class="steps">
  <li><strong>Discover</strong> the sport and event on OLBG. OLBG is used only for discovery and market vocabulary.</li>
  <li><strong>Verify</strong> the fixture on the governing body or league endpoint: ids, teams, local date, start time, venue.</li>
  <li><strong>Collect</strong> the model inputs from official standings: wins, losses, goals/points for and against, ranking money.</li>
  <li><strong>Originate</strong> moneyline, handicap and total prices from the sport-specific distribution below.</li>
  <li><strong>Grade</strong> the selection: high ≥72% (≥70% for a price-band pick), medium ≥60%, low below 60%.</li>
  <li><strong>Write</strong> a unique ≥30-word prediction for every published high-confidence or band pick, with sourced facts.</li>
  <li><strong>Disclose</strong> every blank, stale or unsupported value on <a href="flagged.html">Flagged for Review</a>.</li>
</ol>

<h2>Confidence and the price band</h2>
<div class="two-col">
<div class="panel"><h3>Confidence</h3>
<p><span class="badge high">high</span> model probability ≥72%. <span class="badge medium">medium</span> ≥60%.
<span class="badge low">low</span> below 60%. NBA picks are capped at medium because the prior season's records
do not reflect current rosters.</p></div>
<div class="panel"><h3>Price band (−250 to +10000)</h3>
<p>Decimal 1.40 to 101.00. A 70%+ probability is at most 1.43 decimal, so only a 70.0–71.4% selection can satisfy both
the confidence rule and the −250 floor. The builder enumerates moneyline, handicap ladders and total ladders, then takes
the highest-probability qualifying selection. The 20 original high picks are 1.02–1.39 and are disclosed as outside the band.</p></div>
</div>

<h2>Sport models</h2>
<div class="table-wrap"><table class="data"><thead><tr><th>Sport</th><th>Model and markets</th></tr></thead>
<tbody>{model_rows}</tbody></table></div>

<h2>Evidence rules</h2>
<ul>
  <li>A fixture is published only with an official URL. If the URL is a competition page rather than a fixture page, the row says so (63 rows).</li>
  <li>A value that the official page did not return is <code>null</code>, rendered as <code>—</code>, and explained on the flagged page. No value is inferred.</li>
  <li>No bookmaker price, tipster percentage or secondary outlet enters any equation.</li>
  <li>Rows dated before 2026-10-22 are labelled <em>past</em>. The snapshot does not pretend to be live.</li>
  <li><strong>Rows include source links</strong>; the audit trail records whether each was re-read on 2026-10-22.</li>
</ul>

<h2>Known limits</h2>
<ul>
  <li>Sample sizes are small early in the season (3–11 matches per club), so shrinkage is heavy and prices move with one result.</li>
  <li>No injury, suspension, lineup, weather or travel information is modelled.</li>
  <li>No home-advantage term is applied to neutral-site or tournament fixtures beyond the venue flag.</li>
  <li>Futures (F1 title, 2027 rugby league) rest on roster assumptions that are not verifiable in October 2026.</li>
</ul>
"""
    return page("Methodology", "methodology.html", body)


def build_sources(sources=None, matches=None) -> str:
    rows, preds, flags, sports, band = dataset()
    counter = Counter()
    for m in rows:
        for key in ("official_url", "data_url"):
            if m.get(key):
                counter[m[key]] += 1
    fact_sources = Counter()
    for p in preds:
        for fact in p.get("facts", []):
            fact_sources[fact["source"]] += 1
    domains = Counter(domain(u) for u in list(counter) + list(fact_sources))
    rows_html = "".join(
        f'<tr><td><a href="{esc(u)}" rel="noopener">{esc(u)}</a></td>'
        f'<td>{esc(domain(u))}</td><td>{n}</td></tr>'
        for u, n in sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    )
    fact_html = "".join(
        f'<tr><td><a href="{esc(u)}" rel="noopener">{esc(u)}</a></td><td>{esc(domain(u))}</td><td>{n}</td></tr>'
        for u, n in sorted(fact_sources.items(), key=lambda x: (-x[1], x[0]))[:60]
    )
    body = f"""
<h1>Sources</h1>
<p class="lede">The official register behind the dataset: {len(counter)} distinct fixture/data URLs and
{len(fact_sources)} prediction-fact URLs across {len(domains)} domains. OLBG is used for discovery only and is never the
source of a price or a result. A source link records where a value came from; it does not establish that the page was fetched during this audit, and it is not proof that the page supports every claim beside it.</p>
<div class="grid domains">
  {''.join(f'<div class="card"><div class="cardhead"><h3>{esc(d)}</h3><span class="pill">{n}</span></div></div>' for d, n in domains.most_common(12))}
</div>
<h2>Fixture and model-input sources</h2>
<div class="table-wrap"><table class="data"><thead><tr><th>URL</th><th>Domain</th><th>Rows</th></tr></thead>
<tbody>{rows_html}</tbody></table></div>
<h2>Prediction fact sources</h2>
<p class="sub">Every claim in a prediction links to the page that published it. The full claim-by-claim list is on each
prediction card at <a href="picks.html">Picks</a>.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>URL</th><th>Domain</th><th>Facts</th></tr></thead>
<tbody>{fact_html}</tbody></table></div>
"""
    return page("Sources", "sources.html", body)


def build_archive() -> str:
    verified = load_verified("matches.json")["matches"]
    root = load("matches.json")["matches"]
    live = json.loads((DATA / "live" / "lines.json").read_text())["rows"]
    desk = json.loads((DATA / "desk" / "fixtures.json").read_text())["fixtures"]
    survey_events = []
    for f in sorted((DATA / "survey" / "events").glob("*.json")):
        for e in json.loads(f.read_text()):
            survey_events.append((f.stem, e))

    root_rows = "".join(
        f'<tr><td>{esc(m["sport"])}</td><td>{esc(m["start_display"])}</td>'
        f'<td>{esc(m["home"]["name"])} v {esc(m["away"]["name"])}</td>'
        f'<td>{esc(m.get("line_status", ""))}</td>'
        f'<td><a href="{esc(m["fixture_source"]["url"])}" rel="noopener">{esc(domain(m["fixture_source"]["url"]))}</a></td></tr>'
        for m in root
    )
    live_rows = "".join(
        f'<tr><td>{esc(r["sport"])}</td><td>{esc(r["date"])}</td>'
        f'<td>{esc(r["home_name"])} v {esc(r["away_name"])}</td><td>{len(r.get("markets", {}))} markets</td>'
        f'<td><a href="{esc(r["source_url"])}" rel="noopener">{esc(domain(r["source_url"]))}</a></td></tr>'
        for r in live
    )
    desk_rows = "".join(
        f'<tr><td>{esc(f["sport"])}</td><td>{esc(f["date"])}</td>'
        f'<td>{esc(f["home_name"])} v {esc(f["away_name"])}</td><td>{esc(f.get("league", ""))}</td>'
        f'<td><a href="{esc(f["official_url"])}" rel="noopener">{esc(domain(f["official_url"]))}</a></td></tr>'
        for f in desk
    )
    survey_rows = "".join(
        f'<tr><td>{esc(s.replace("_", " ").title())}</td><td>{esc(e.get("listed_time") or "—")}</td>'
        f'<td>{esc(e.get("match", ""))}</td><td>{esc(e.get("market", ""))}</td>'
        f'<td><a href="{esc(e.get("official_fixture_source") or e.get("source_url") or "#")}" rel="noopener">{esc(domain(e.get("official_fixture_source") or e.get("source_url") or ""))}</a></td></tr>'
        for s, e in survey_events
    )
    body = f"""
<h1>Archive of earlier layers</h1>
<p class="lede">Five research layers exist in this repository. The unified dashboard is built from the
<strong>verified desk</strong> ({len(verified)} rows, 15 sports), which contains every fixture published by the other
structured layers plus additional sports. The earlier layers are preserved untouched below with their own source links,
so nothing is lost and no row is counted twice on the dashboard.</p>
<div class="notice"><strong>Do not add these row counts together.</strong> The same fixture appears in several layers.
Use the <a href="matches.html">unified table</a> for the published dataset; use this page for provenance.</div>

<h2>Root dashboard layer <span class="pill">{len(root)} rows · 2026-10-21</span></h2>
<p class="sub">Superseded by the verified desk for NHL, NBA, URC, cricket and handball. The unified category
pages replace its old sport pages; its full row-level data and source links are preserved in the table below.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Sport</th><th>Start</th><th>Match</th><th>Line status</th><th>Fixture source</th></tr></thead>
<tbody>{root_rows}</tbody></table></div>

<h2>Live slate layer <span class="pill">{len(live)} rows · 2026-10-21</span></h2>
<p class="sub">URC Round 5 and MLB World Series Games 1–3. Preserved at <a href="live/index.html">/live/</a>.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Sport</th><th>Date</th><th>Match</th><th>Markets</th><th>Source</th></tr></thead>
<tbody>{live_rows}</tbody></table></div>

<h2>Evidence desk v2 <span class="pill">{len(desk)} rows · 2026-10-21</span></h2>
<p class="sub">NHL and NBA. Preserved at <a href="site/index.html">/site/</a>.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Sport</th><th>Date</th><th>Match</th><th>League</th><th>Source</th></tr></thead>
<tbody>{desk_rows}</tbody></table></div>

<h2>All-sport survey inventory <span class="pill">{len(survey_events)} listings · 2026-10-20/21</span></h2>
<p class="sub">OLBG discovery inventory; listing times are relative (“Today 16:30”) and fixtures are not all
officially verified. Preserved at <a href="survey/index.html">/survey/</a>.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Sport</th><th>Listed</th><th>Match</th><th>Market</th><th>Official fixture source</th></tr></thead>
<tbody>{survey_rows}</tbody></table></div>
"""
    return page("Archive of earlier layers", "archive.html", body)


def build_css() -> str:
    return """:root{
  --bg:#f6f7f9;--surface:#fff;--alt:#f0f2f5;--border:#e3e6ea;--strong:#cfd5dc;
  --ink:#111827;--muted:#5b6572;--subtle:#7b8794;--accent:#0f766e;--accent-soft:#ccfbf1;
  --link:#0b5cab;--high:#166534;--high-bg:#dcfce7;--med:#854d0e;--med-bg:#fef3c7;
  --low:#334155;--low-bg:#e2e8f0;--danger:#991b1b;--danger-bg:#fee2e2;--warn:#92400e;--warn-bg:#fef3c7;
  --radius:12px;--shadow:0 1px 2px rgba(16,24,40,.06),0 1px 3px rgba(16,24,40,.1)}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
code{background:var(--alt);padding:.08em .32em;border-radius:4px;font-size:.88em}
.wrap{max-width:1280px;margin:0 auto;padding:0 1.1rem}
.topbar{background:#0f172a;color:#f8fafc;position:sticky;top:0;z-index:40}
.bar{display:flex;align-items:center;justify-content:space-between;gap:.8rem;flex-wrap:wrap;min-height:58px}
.brand{display:flex;align-items:center;gap:.5rem;color:#fff;font-weight:800;letter-spacing:-.01em}
.brand:hover{text-decoration:none;color:#5eead4}
.brand-sub{font-weight:500;color:#94a3b8;font-size:.82rem}
.dot{width:10px;height:10px;border-radius:3px;background:#14b8a6;display:inline-block}
.nav{display:flex;flex-wrap:wrap;gap:.15rem}
.nav a{color:#cbd5e1;font-size:.82rem;padding:.4rem .55rem;border-radius:7px}
.nav a:hover{background:#1e293b;color:#fff;text-decoration:none}
.nav a[aria-current="page"]{background:#134e4a;color:#5eead4;font-weight:600}
.stripe{background:#ecfdf5;border-bottom:1px solid #a7f3d0;color:#065f46;font-size:.78rem;padding:.45rem 0}
main{padding:1.6rem 0 3rem}
h1{font-size:2rem;line-height:1.15;letter-spacing:-.025em;margin:.2rem 0 .6rem}
h2{font-size:1.25rem;letter-spacing:-.015em;margin:2.1rem 0 .6rem}
h3{font-size:1rem;margin:0 0 .35rem}
p{margin:.4rem 0}
.eyebrow{text-transform:uppercase;letter-spacing:.09em;font-size:.72rem;font-weight:700;color:var(--accent);margin:0}
.lede{font-size:1.02rem;color:#374151;max-width:72rem}
.sub{color:var(--muted);font-size:.9rem;margin-top:-.2rem}
.crumb{font-size:.82rem;color:var(--muted);margin:0 0 .3rem}
.hero{background:linear-gradient(180deg,#ffffff,#f0fdfa);border:1px solid var(--border);border-radius:var(--radius);padding:1.6rem;box-shadow:var(--shadow)}
.cta{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem}
.button{display:inline-block;border:1px solid var(--strong);background:#fff;color:var(--ink);padding:.5rem .85rem;border-radius:8px;font-size:.86rem;font-weight:600}
.button:hover{text-decoration:none;border-color:var(--accent);color:var(--accent)}
.button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.button.primary:hover{background:#115e59;color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.7rem;margin:1.1rem 0}
.kpi{background:#fff;border:1px solid var(--border);border-radius:10px;padding:.85rem .95rem;box-shadow:var(--shadow)}
.kpi .v{font-size:1.65rem;font-weight:800;letter-spacing:-.03em;line-height:1.1}
.kpi .k{font-size:.78rem;font-weight:650;color:#374151}
.kpi .s{font-size:.72rem;color:var(--subtle)}
.kpis.small{grid-template-columns:repeat(auto-fit,minmax(110px,1fr))}
.kpis.small .kpi .v{font-size:1.3rem}
.grid{display:grid;gap:.8rem}
.grid.sports{grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}
.grid.domains{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
.card{display:block;background:#fff;border:1px solid var(--border);border-radius:10px;padding:.9rem;box-shadow:var(--shadow);color:inherit}
.card:hover{border-color:#99f6e4;text-decoration:none;transform:translateY(-1px)}
.cardhead{display:flex;justify-content:space-between;align-items:center;gap:.5rem}
.card p{font-size:.82rem;color:var(--muted);margin:.3rem 0 .5rem}
.metrics{display:flex;gap:.8rem;font-size:.75rem;color:var(--subtle);border-top:1px solid var(--border);padding-top:.45rem}
.metrics b{color:var(--ink)}
.pill{background:var(--alt);border:1px solid var(--border);border-radius:999px;padding:.1rem .5rem;font-size:.72rem;font-weight:700;color:#374151;white-space:nowrap}
.notice{background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #3b82f6;border-radius:8px;padding:.7rem .85rem;margin:.9rem 0;font-size:.86rem;color:#1e3a8a}
.notice.warn{background:var(--warn-bg);border-color:#fcd34d;border-left-color:#f59e0b;color:#78350f}
.two-col{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:.9rem}
.panel{background:#fff;border:1px solid var(--border);border-radius:10px;padding:1rem}
.panel ul{margin:.3rem 0 0 1rem;padding:0}.panel li{margin:.25rem 0;font-size:.88rem}
.filters{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;background:#fff;border:1px solid var(--border);border-radius:10px;padding:.65rem;margin:.9rem 0}
.filters input,.filters select{border:1px solid var(--strong);border-radius:7px;padding:.42rem .55rem;font-size:.84rem;background:#fff}
.filters input{min-width:250px;flex:1}
#f-count{color:var(--muted);margin-left:auto}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow);margin:.8rem 0}
table.data{border-collapse:collapse;width:100%;font-size:.8rem;min-width:900px}
table.data th{position:sticky;top:0;background:#f8fafc;text-align:left;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);padding:.55rem .6rem;border-bottom:1px solid var(--strong);white-space:nowrap}
table.data td{padding:.55rem .6rem;border-bottom:1px solid var(--border);vertical-align:top}
table.data tbody tr:last-child td{border-bottom:0}
table.data tbody tr:hover{background:#fafcff}
table.data.plain{min-width:500px}
table.data.plain td{font-size:.85rem}
.teams{font-weight:650}.teams span{color:var(--subtle);font-weight:400}
.pick{font-weight:600}
.tiny{font-size:.72rem;color:var(--subtle);line-height:1.4}
.bandline{margin-top:.25rem;font-size:.72rem;color:#0f766e;background:#f0fdfa;border:1px solid #99f6e4;border-radius:5px;padding:.15rem .35rem;display:inline-block}
.blank{color:#9ca3af}
.badge{display:inline-block;border-radius:999px;padding:.08rem .45rem;font-size:.68rem;font-weight:700;text-transform:capitalize;white-space:nowrap}
.badge.high,.badge.ok{background:var(--high-bg);color:var(--high)}
.badge.medium,.badge.warn{background:var(--med-bg);color:var(--med)}
.badge.low,.badge.none{background:var(--low-bg);color:var(--low)}
.badge.upcoming{background:#dbeafe;color:#1e40af}
.badge.today{background:#ede9fe;color:#5b21b6}
.badge.past{background:#e5e7eb;color:#4b5563}
.badge.band{background:#ccfbf1;color:#115e59}
.badge.outband{background:#fef3c7;color:#92400e}
.badge.high,.badge.medium,.badge.low{text-transform:capitalize}
.badge.resolved,.badge.low{background:#e5e7eb;color:#374151}
.badge.environment,.badge.irregularity{background:#fef3c7;color:#92400e}
.badge.critical{background:var(--danger-bg);color:var(--danger)}
.badge.very-high{background:var(--danger-bg);color:var(--danger)}
.preds{display:grid;gap:.85rem}
.pred{background:#fff;border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:10px;padding:1rem;box-shadow:var(--shadow)}
.predhead{display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap;margin-bottom:.35rem}
.pred h3{margin:.15rem 0 .3rem;font-size:1.05rem}
.selection{font-size:.85rem;color:var(--accent);font-weight:600;margin:0 0 .45rem}
.sources{background:#fafafa;border:1px solid var(--border);border-radius:7px;padding:.5rem .7rem;margin-top:.6rem;font-size:.78rem}
.sources ul{margin:.2rem 0 0 1rem;padding:0}.sources li{margin:.15rem 0}
.predfoot{display:flex;gap:1rem;font-size:.78rem;margin-top:.55rem;flex-wrap:wrap}
.excluded{margin:.4rem 0 0 1rem;padding:0;font-size:.88rem;color:#374151}
.excluded li{margin:.25rem 0}
.steps{margin:.4rem 0 0 1.1rem;padding:0;font-size:.9rem}
.steps li{margin:.3rem 0}
.footer{border-top:1px solid var(--border);background:#fff;padding:1.2rem 0 2rem;color:var(--muted);font-size:.82rem}
.footer p{margin:.3rem 0}
.nowrap{white-space:nowrap}
@media(max-width:640px){h1{font-size:1.55rem}.bar{min-height:auto;padding:.5rem 0}.nav a{font-size:.75rem;padding:.32rem .4rem}.filters input{min-width:0;width:100%}}
"""


def main() -> None:
    rows, preds, flags, sports, band = dataset()
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "style.css").write_text(build_css(), encoding="utf-8")

    (ROOT / "index.html").write_text(build_index(load("matches.json"), preds, flags), encoding="utf-8")
    (ROOT / "matches.html").write_text(build_matches(), encoding="utf-8")
    (ROOT / "verification.html").write_text(build_verification(), encoding="utf-8")
    (ROOT / "picks.html").write_text(build_picks(), encoding="utf-8")
    (ROOT / "flagged.html").write_text(build_flagged(), encoding="utf-8")
    (ROOT / "methodology.html").write_text(build_methodology(), encoding="utf-8")
    (ROOT / "sources.html").write_text(build_sources(), encoding="utf-8")
    (ROOT / "archive.html").write_text(build_archive(), encoding="utf-8")

    (ROOT / "sports").mkdir(exist_ok=True)
    (ROOT / "sports" / "index.html").write_text(build_sports_index(), encoding="utf-8")
    meta_by_slug = {s["slug"]: s for s in sports["eligible_sports"]}
    for slug, meta in meta_by_slug.items():
        (ROOT / "sports" / f"{slug}.html").write_text(build_sport_page(slug, meta), encoding="utf-8")

    # Cross-layer evidence page is generated by the audit module so the two stay in sync.
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from integration_audit import body as integration_body

    (ROOT / "integration.html").write_text(
        page("Evidence status & integration review", "integration.html", integration_body()),
        encoding="utf-8",
    )
    lines = [
        f"build_site: 10 root pages + {len(meta_by_slug)} sport pages",
        f"  {len(rows)} rows, {sum(1 for m in rows if m['line_status'] == 'originated')} originated, "
        f"{sum(1 for m in rows if m.get('band_pick'))} band picks",
        f"  {len(preds)} predictions ({sum(1 for p in preds if p.get('match_type') == 'band')} band)",
        f"  {len(flags)} verified review items",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
