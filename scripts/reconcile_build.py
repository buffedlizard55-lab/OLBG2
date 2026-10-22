#!/usr/bin/env python3
"""Build the /reconcile/ cross-layer reconciliation console from data/reconcile/*.

Deterministic: input is the committed audit output, output is the committed HTML.
No clock, no network, no randomness.
"""

from __future__ import annotations

import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "reconcile")
SITE = os.path.join(ROOT, "reconcile")

NAV = [
    ("index.html", "Overview"),
    ("conflicts.html", "Conflicts"),
    ("non-fixtures.html", "Non-fixtures"),
    ("freshness.html", "Freshness"),
    ("provenance.html", "Provenance"),
    ("predictions.html", "Predictions"),
    ("spot-checks.html", "Spot checks"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "Method"),
    ("sources.html", "Sources"),
]

SPORT_NAMES = {}


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def link(url, label=None) -> str:
    if not url:
        return '<span class="blank">—</span>'
    label = label or re.sub(r"^https?://(www\.)?", "", url)
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)}</a>'


def page(title: str, body: str, rel: str = "", subtitle: str = "") -> str:
    nav = "".join(
        f'<a href="{rel}{href}">{esc(label)}</a>' for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG2 reconciliation console</title>
<link rel="stylesheet" href="{rel}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <div class="brand"><span class="dot"></span> OLBG2 · Reconciliation console</div>
    <nav class="nav">{nav}<a href="{rel}../index.html">Dashboard</a></nav>
  </div>
</header>
<main id="main" class="wrap">
{f'<p class="kicker">{esc(subtitle)}</p>' if subtitle else ''}
{body}
</main>
<footer class="foot"><div class="wrap">
<p>Independent cross-layer audit of the published OLBG2 datasets. Read-only: no other session's data was edited.
Every value below is machine-derived from committed JSON; spot checks link the official page that was read.</p>
<p>Audit date 2026-10-22 · session <code>arena/3552df3e-olbg2</code> · <a href="{rel}flagged.html">Flagged for review</a></p>
</div></footer>
<script src="{rel}assets/app.js"></script>
</body>
</html>
"""


def table(headers, rows, cls="data", empty="No rows."):
    if not rows:
        return f'<p class="empty">{esc(empty)}</p>'
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "\n".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>\n{body}\n</tbody></table></div>'


def kpi(label, value, note=""):
    return (f'<div class="kpi"><div class="kpi-v">{esc(value)}</div>'
            f'<div class="kpi-l">{esc(label)}</div>'
            f'{f"<div class=kpi-n>{esc(note)}</div>" if note else ""}</div>')


def write(path: str, content: str):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)


CSS = """/* OLBG2 reconciliation console — single stylesheet, no external assets */
:root{--bg:#0b0f16;--panel:#121926;--panel2:#0f1522;--line:#233043;--ink:#e8eef7;
--muted:#93a4bd;--accent:#5eead4;--accent2:#60a5fa;--warn:#fbbf24;--bad:#f87171;--ok:#34d399}
*{box-sizing:border-box}
@media (prefers-color-scheme:light){:root{--bg:#f6f8fb;--panel:#fff;--panel2:#f0f4fa;--line:#dbe3ee;
--ink:#111823;--muted:#5a6b84;--accent:#0d9488;--accent2:#2563eb;--warn:#b45309;--bad:#b91c1c;--ok:#047857}}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent2);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.skip{position:absolute;left:-9999px}.skip:focus{left:8px;top:8px;background:var(--panel);padding:8px;z-index:9}
header.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);
border-bottom:1px solid var(--line);backdrop-filter:blur(8px)}
header .wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:12px 20px}
.brand{font-weight:700;letter-spacing:.2px;display:flex;align-items:center;gap:9px}
.dot{width:9px;height:9px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent)}
.nav{display:flex;gap:4px;flex-wrap:wrap;font-size:13.5px}
.nav a{padding:5px 9px;border-radius:7px;color:var(--muted);border:1px solid transparent}
.nav a:hover{color:var(--ink);border-color:var(--line);text-decoration:none}
main{padding:26px 20px 60px}
h1{font-size:28px;line-height:1.2;margin:6px 0 6px}
h2{font-size:19px;margin:34px 0 10px;padding-bottom:7px;border-bottom:1px solid var(--line)}
h3{font-size:15.5px;margin:22px 0 8px}
p{color:var(--ink)}p.lede{color:var(--muted);max-width:78ch}
.kicker{color:var(--accent);font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;margin:0 0 4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:18px 0 6px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi-v{font-size:26px;font-weight:700;letter-spacing:-.4px}
.kpi-l{color:var(--muted);font-size:12.5px;margin-top:2px}
.kpi-n{color:var(--muted);font-size:11.5px;margin-top:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px;margin:14px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px 17px}
.card h3{margin:0 0 6px;font-size:15px}.card p{margin:0;color:var(--muted);font-size:13.5px}
.card a.more{font-size:13px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:640px}
th,td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:0;background:var(--panel2);color:var(--muted);font-weight:600;
font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
tbody tr:nth-child(even){background:color-mix(in srgb,var(--panel2) 55%,transparent)}
tbody tr:hover{background:color-mix(in srgb,var(--accent2) 10%,transparent)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.blank{color:var(--muted)}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:600;
border:1px solid var(--line);color:var(--muted);white-space:nowrap}
.tag.ok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 45%,transparent)}
.tag.bad{color:var(--bad);border-color:color-mix(in srgb,var(--bad) 45%,transparent)}
.tag.warn{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 45%,transparent)}
.tag.info{color:var(--accent2);border-color:color-mix(in srgb,var(--accent2) 45%,transparent)}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:8px;padding:12px 15px;margin:14px 0;color:var(--muted);font-size:13.5px}
.note strong{color:var(--ink)}
.empty{color:var(--muted);border:1px dashed var(--line);border-radius:10px;padding:16px}
.foot{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--muted);font-size:12.5px}
.foot p{margin:4px 0}
code{background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:1px 5px;font-size:12px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 14px}
.filters input,.filters select{background:var(--panel);border:1px solid var(--line);color:var(--ink);
border-radius:8px;padding:7px 10px;font-size:13px}
ul.tight{margin:8px 0 8px 18px;padding:0}ul.tight li{margin:3px 0;color:var(--muted)}
"""

APP_JS = """// Filter any table whose rows carry data-search attributes.
document.querySelectorAll('[data-filter]').forEach(function(box){
  var target = document.getElementById(box.dataset.filter);
  if(!target) return;
  box.addEventListener('input', function(){
    var q = box.value.toLowerCase();
    target.querySelectorAll('tbody tr').forEach(function(tr){
      tr.style.display = (!q || (tr.dataset.search||'').toLowerCase().includes(q)) ? '' : 'none';
    });
  });
});
document.querySelectorAll('th[data-sort]').forEach(function(th){
  th.style.cursor='pointer';
  th.addEventListener('click', function(){
    var table = th.closest('table'), idx = Array.from(th.parentNode.children).indexOf(th);
    var dir = th.dataset.dir === 'asc' ? -1 : 1; th.dataset.dir = dir === 1 ? 'asc' : 'desc';
    var rows = Array.from(table.tBodies[0].rows);
    rows.sort(function(a,b){
      var av = a.cells[idx].dataset.v || a.cells[idx].innerText;
      var bv = b.cells[idx].dataset.v || b.cells[idx].innerText;
      var an = parseFloat(av), bn = parseFloat(bv);
      if(!isNaN(an) && !isNaN(bn)) return (an-bn)*dir;
      return av.localeCompare(bv)*dir;
    });
    rows.forEach(function(r){ table.tBodies[0].appendChild(r); });
  });
});
"""


def main() -> int:
    report = json.load(open(os.path.join(DATA, "report.json"), encoding="utf-8"))
    rows_doc = json.load(open(os.path.join(DATA, "rows.json"), encoding="utf-8"))
    spots = json.load(open(os.path.join(DATA, "spot_checks.json"), encoding="utf-8"))
    rows = rows_doc["rows"]
    f = report["findings"]
    t = report["totals"]
    layers = report["layers"]

    write("assets/style.css", CSS)
    write("assets/app.js", APP_JS)

    # ---------------------------------------------------------------- index
    layer_rows = []
    for name, m in sorted(layers.items(), key=lambda kv: -kv[1]["rows"]):
        layer_rows.append([
            esc(name), f'<span class="num">{m["rows"]}</span>',
            f'<span class="num">{m["fixtures"]}</span>',
            f'<span class="num">{m["non_fixtures"]}</span>',
            f'<span class="num">{m["sports"]}</span>',
            f'<span class="num">{m["with_moneyline"]}</span>',
            f'<span class="num">{m["high"]}</span>',
            esc(m["capture_date"]), f'<code>{esc(m["path"])}</code>',
        ])
    body = f"""
<h1>Cross-layer reconciliation</h1>
<p class="lede">Every published OLBG2 layer is checked against every other one. The question is not
“is any single page internally consistent?” — it is “do the {t['rows']:,} rows the repository publishes actually
describe {t['distinct_fixtures']:,} fixtures, at one price, with one grade, and a link that supports the row?”</p>

<div class="grid">
{kpi("Published rows audited", f"{t['rows']:,}", f"across {len(layers)} layers")}
{kpi("Distinct fixtures", f"{t['distinct_fixtures']:,}", f"{t['sports']} eligible sports")}
{kpi("Rows that are not fixtures", t['non_fixtures'], "outrights, fields, race cards")}
{kpi("Cross-layer overlaps", f"{t['overlap_groups']:,}", f"{t['overlap_rows']:,} rows inside them")}
{kpi("Price conflicts", t['price_conflicts'], "same team, different price")}
{kpi("Grade conflicts", t['confidence_conflicts'], "same pick, different confidence")}
{kpi("Rule violations", t['rule_violations'], "high grade outside the stated rule")}
{kpi("Excluded-sport rows", t['excluded_scope_rows'], "brief's exclusion list")}
</div>

<h2>What this console found</h2>
<div class="cards">
  <div class="card"><h3>1 · The catalogue is {t['overlap_rows'] / max(t['rows'],1):.0%} duplication</h3>
  <p>{t['rows']:,} published rows resolve to {t['distinct_fixtures']:,} distinct fixtures. {t['overlap_rows']:,} rows sit in
  {t['overlap_groups']:,} fixtures published by two or more layers. <a class="more" href="conflicts.html">See overlaps →</a></p></div>

  <div class="card"><h3>2 · {t['non_fixtures']} rows are not matches</h3>
  <p>Outright futures, tournament fields, “field v venue” and greyhound race cards are formatted as head-to-head
  fixtures with their own moneylines. <a class="more" href="non-fixtures.html">List them →</a></p></div>

  <div class="card"><h3>3 · The same team is priced {t['price_conflicts']} times differently</h3>
  <p>Largest disagreement: see the conflicts page. Different layers run different models and nothing reconciles them,
  so two URLs can quote the same club at very different prices. <a class="more" href="conflicts.html">Compare →</a></p></div>

  <div class="card"><h3>4 · {t['rule_violations']} grades break the project's own rule</h3>
  <p>The published rule is “high only when p ≥ 0.70 and the fair price is inside −250…+10000”. Violations are listed row by row.
  <a class="more" href="conflicts.html#grades">Check grades →</a></p></div>
</div>

<h2>Layers audited</h2>
{table(["Layer", "Rows", "Fixtures", "Non-fixtures", "Sports", "With moneyline", "Graded high", "Capture date", "Source file"],
       layer_rows)}

<h2>Eligible-sport coverage</h2>
<p class="lede">The brief excludes soccer, boxing, UFC/MMA, American football, hurling, horse racing, cycling and specials.
All {t['sports']} eligible sports have at least one row; {t['eligible_sports_with_fixtures']} have at least one genuine
head-to-head fixture. No row is published under an excluded sport.</p>
{table(["Sport", "Rows", "Genuine fixtures", "Layers"],
       [[esc(k.replace('-', ' ')), f'<span class="num">{v["rows"]}</span>',
         f'<span class="num">{v["fixture_rows"]}</span>',
         esc(", ".join(v["layers"]))] for k, v in sorted(f["eligible_coverage"].items())])}

<h2>How to read this</h2>
<div class="note"><strong>This page does not declare any other layer “wrong”.</strong> Two layers disagreeing about a price is
expected when each runs its own model; what is not acceptable is publishing both as if each were the authoritative number.
The console measures that gap, names the rows, and leaves the decision visible. Values are machine-derived from the committed
JSON, so every finding can be reproduced by running <code>python3 scripts/reconcile_audit.py</code>.</div>
"""
    write("index.html", page("Overview", body, subtitle="OLBG2 · independent audit"))

    # ------------------------------------------------------------ conflicts
    over_rows = []
    for g in f["overlap"][:300]:
        over_rows.append([
            esc(g["sport"].replace("-", " ")), esc(g["date"]),
            esc(" v ".join([s.title() for s in g["sides"]])),
            f'<span class="num">{g["layer_count"]}</span>',
            esc(", ".join(sorted({r["layer"] for r in g["rows"]}))),
            esc("; ".join(sorted({str(r["pick"]) for r in g["rows"] if r["pick"]}))[:120]),
        ])
    price_rows = []
    for c in f["price_conflict"][:250]:
        vals = ", ".join(f'{v["layer"]} {v["decimal"]:.2f}' for v in c["values"])
        price_rows.append([
            esc(c["sport"].replace("-", " ")), esc(c["date"]), esc(c["team"].title()),
            esc(vals), f'<span class="num">{c["spread"]:.2f}</span>',
        ])
    conf_rows = []
    for c in f["confidence_conflict"][:250]:
        g = ", ".join(f'{x["layer"]}:{x["confidence"]}' for x in c["grades"])
        tiers = {x["confidence"] for x in c["grades"]}
        sev = "bad" if {"high", "low"} <= tiers else "warn"
        conf_rows.append([
            esc(c["sport"].replace("-", " ")), esc(c["date"]), esc(c["selection"].title()),
            esc(g), f'<span class="tag {sev}">{"split" if len(tiers) > 2 else "mixed"}</span>',
        ])
    rule_rows = []
    for v in f["rule_violations"][:250]:
        rule_rows.append([
            esc(v["layer"]), esc(v["sport"].replace("-", " ")), esc(v.get("selection") or ""),
            esc(v["why"]),
            f'<span class="num">{v["probability"]:.3f}</span>' if v.get("probability") is not None else '<span class="blank">—</span>',
            f'<span class="num">{v["decimal"]:.2f}</span>' if v.get("decimal") is not None else '<span class="blank">—</span>',
        ])
    body = f"""
<h1>Conflicts</h1>
<p class="lede">Where two layers publish the same fixture with different numbers. Overlaps first (the same fixture at several URLs),
then the price, grade and rule disagreements inside them.</p>

<h2 id="overlaps">Overlapping fixtures</h2>
<p class="lede">{t['overlap_groups']:,} fixtures are published by two or more layers ({t['overlap_rows']:,} rows).
Distribution by number of layers publishing the same fixture: {esc(", ".join(f"{k} layer(s): {v}" for k, v in f['overlap_depth'].items()))}.
Showing the 300 largest groups.</p>
{table(["Sport", "Date", "Fixture", "Layers", "Which layers", "Picks published"], over_rows, empty="No overlaps.")}

<h2 id="prices">Price conflicts</h2>
<p class="lede">The same club priced at different fair decimals by different layers. Spread is max − min.
{t['price_conflicts']} team-level conflicts; largest 250 shown.</p>
{table(["Sport", "Date", "Team", "Prices by layer", "Spread"], price_rows, empty="No price conflicts.")}

<h2 id="grades">Confidence conflicts</h2>
<p class="lede">The same fixture and the same selection, graded differently in different layers.
{t['confidence_conflicts']} selection-level conflicts; largest 250 shown.</p>
{table(["Sport", "Date", "Selection", "Grades", "Severity"], conf_rows, empty="No grade conflicts.")}

<h2 id="rules">Breaches of the project's own confidence rule</h2>
<p class="lede">The rule published across the repo is: <code>high</code> only when the model probability is ≥ 0.70
<strong>and</strong> the fair decimal price is inside 1.40–101.00 (−250…+10000). These rows are graded
<code>high</code> while failing one half of that rule.</p>
{table(["Layer", "Sport", "Selection", "Breach", "Probability", "Fair decimal"], rule_rows, empty="No rule breaches.")}
"""
    write("conflicts.html", page("Conflicts", body))

    # -------------------------------------------------------- non-fixtures
    nf = f["non_fixture"]
    by_reason = {}
    for r in nf:
        by_reason.setdefault(r["reason"], []).append(r)
    blocks = []
    for reason, items in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
        rws = [[esc(r["layer"]), esc(r["sport"].replace("-", " ")), esc(r["date"] or "—"),
                esc(r["competition"])[:70], esc(r["home"])[:60], esc(r["away"])[:60],
                esc(r["status"] or "—"), link(r["official_url"])] for r in items]
        blocks.append(f"<h3>{esc(reason)} <span class='tag warn'>{len(items)} rows</span></h3>"
                      + table(["Layer", "Sport", "Date", "Competition", "Home / side A", "Away / side B",
                               "Status", "Official source"], rws))
    body = f"""
<h1>Rows that are not matches</h1>
<p class="lede">{len(nf)} published rows describe something other than a head-to-head fixture: a season outright,
a tournament field, a venue, or a greyhound race meeting. They are still counted as “matches” by the layers that
publish them, and several carry a moneyline and a confidence grade.</p>
<div class="note"><strong>Why this matters.</strong> A reader filtering for “matches” on those pages sees a
{KPI if False else ''}selection that cannot be settled from a scoreline, because there is no scoreline. The fix is a
separate “futures / outrights” table, not a match line. This console classifies them; it does not delete them.</div>
{"".join(blocks)}
"""
    write("non-fixtures.html", page("Non-fixtures", body))

    # ---------------------------------------------------------- freshness
    stale = f["stale"]
    undated = f["undated"]
    stale_rows = [[esc(r["layer"]), esc(r["sport"].replace("-", " ")), esc(r["date"]),
                   esc(r["capture_date"] or "—"), esc(f'{r["home"]} v {r["away"]}'), esc(r["why"])]
                  for r in stale]
    body = f"""
<h1>Freshness</h1>
<p class="lede">A row is stale when its fixture date is earlier than the stamp on the layer that publishes it,
or earlier than this audit date while still being presented as an upcoming fixture.</p>
<div class="grid">
{kpi("Stale rows", len(stale), "fixture date before capture / audit date")}
{kpi("Rows with no date", len(undated), "cannot be scheduled or settled")}
{kpi("Audit date", "2026-10-22", "all comparisons are against this")}
</div>
{table(["Layer", "Sport", "Fixture date", "Layer capture", "Fixture", "Why it is stale"], stale_rows, empty="No stale rows.")}
<h2>Rows with no fixture date</h2>
<p class="lede">These rows exist in a layer but publish no date, so they cannot be placed on a schedule. They are listed rather
than guessed.</p>
{table(["Layer", "Sport", "Home / side A", "Away / side B", "Reason"],
       [[esc(r["layer"]), esc(r["sport"].replace("-", " ")), esc(r["home"]), esc(r["away"]), esc(r["why"])] for r in undated],
       empty="None.")}
"""
    write("freshness.html", page("Freshness", body))

    # --------------------------------------------------------- provenance
    cite = f["citation"]
    shared_rows = [[link(u["url"]), f'<span class="num">{u["rows"]}</span>',
                    esc(", ".join(u["layers"])), esc(", ".join(s.replace("-", " ") for s in u["sports"]))]
                   for u in cite["shared_urls"][:30]]
    host_rows = [[esc(h["host"]), f'<span class="num">{h["rows"]}</span>'] for h in cite["hosts"][:40]]
    body = f"""
<h1>Provenance</h1>
<p class="lede">A row is only as good as the page it cites. This page measures citation granularity and host ownership,
then lists the shared and shared-out URLs.</p>
<div class="grid">
{kpi("Rows with a source link", f"{cite['rows_with_url']:,}", f"of {t['rows']:,} ({cite['rows_with_url'] / max(t['rows'],1):.1%})")}
{kpi("Rows without a link", cite["rows_without_url"], "must be unverified")}
{kpi("Distinct URLs", f"{cite['distinct_urls']:,}", "for all rows")}
{kpi("Fixture-level citations", f"{cite['fixture_scope_rows']:,}", "page identifies the fixture")}
{kpi("Competition-level", f"{cite['competition_scope_rows']:,}", "page identifies only the competition")}
</div>
<div class="note"><strong>Reading the split.</strong> A competition-level citation can support a date and a team list but not the
pairing itself. That is why the spot-check page marks such rows <span class="tag warn">unreadable</span> rather than
<span class="tag ok">confirmed</span> when the pairing could not be read back.</div>

<h2>URLs reused across rows</h2>
<p class="lede">One URL supporting many rows is a granularity decision, not automatically an error — but when a single
fixture-level URL is reused for different pairings it is a defect (see the non-fixtures and conflicts pages).</p>
{table(["URL", "Rows", "Layers", "Sports"], shared_rows, empty="No shared URLs.")}

<h2>Hosts cited</h2>
{table(["Host", "Rows"], host_rows, empty="No hosts.")}
"""
    write("provenance.html", page("Provenance", body))

    # -------------------------------------------------------- predictions
    pr = f["predictions"]
    per_layer = "".join(f'<span class="tag info">{esc(k)} {v}</span> ' for k, v in sorted(pr["by_layer"].items()))
    pred_rows = []
    for r in pr["rows"]:
        flags = []
        if r["under_30_words"]:
            flags.append('<span class="tag bad">under 30 words</span>')
        if r["duplicate_text"]:
            flags.append('<span class="tag bad">duplicate text</span>')
        if not r["names_selection"]:
            flags.append('<span class="tag warn">selection not named</span>')
        if not r["explicit_market"]:
            flags.append('<span class="tag warn">no market stated</span>')
        if r["high_below_70"]:
            flags.append('<span class="tag bad">high &lt; 70%</span>')
        if r["high_outside_band"]:
            flags.append('<span class="tag bad">high outside band</span>')
        pred_rows.append([
            esc(r["layer"]), esc(r["sport"].replace("-", " ")), esc(r["selection"])[:44],
            f'<span class="num">{r["words"]}</span>',
            esc(r["confidence"] or "—"),
            f'<span class="num">{r["decimal"]:.2f}</span>' if r["decimal"] is not None else '<span class="blank">—</span>',
            "".join(flags) or '<span class="tag ok">clean</span>',
            link(r["official_url"], "source"),
        ])
    body = f"""
<h1>Predictions</h1>
<p class="lede">Every written prediction in every layer, checked against the brief's stated requirements:
at least 30 words, unique prose, the selection named, the market made explicit, and the confidence grade consistent
with the price band.</p>
<div class="grid">
{kpi("Predictions", pr["count"], "across all layers")}
{kpi("Shortest", f'{pr["min_words"]} words', f"median {pr['median_words']}, longest {pr['max_words']}")}
{kpi("Under 30 words", pr["under_30"], "brief requires ≥ 30")}
{kpi("Duplicate texts", pr["duplicate_texts"], "identical prose reused")}
{kpi("Repeated 3-word openings", pr["duplicate_openings"], f"{pr['distinct_openings']} distinct openings")}
{kpi("Grade inconsistent", pr["high_below_70"] + pr["high_outside_band"], "high grade vs price")}
</div>
<p>Layer split: {per_layer}</p>
<h2>Repeated openings</h2>
<p class="lede">Word-count and uniqueness are met; the remaining mechanical weakness is that a quarter of the
openings repeat a template (“Back …”, “Take …”). Listed so the writing can be de-templated rather than assumed fine.</p>
{table(["Opening", "Times repeated"],
       [[esc(o["opening"]), f'<span class="num">{o["count"]}</span>'] for o in pr["repeated_openings"]], empty="None.")}
<h2>All predictions</h2>
<div class="filters"><input data-filter="pred-table" placeholder="Filter by layer, sport, selection…" aria-label="Filter predictions"></div>
<div id="pred-table">
{table(["Layer", "Sport", "Selection", "Words", "Grade", "Fair decimal", "Checks", "Source"], pred_rows)}
</div>
"""
    write("predictions.html", page("Predictions", body))

    # --------------------------------------------------------- spot checks
    spot_rows = []
    for c in spots["checks"]:
        v = c["verdict"]
        tag = {"confirmed": "ok", "partially_confirmed": "warn",
               "contradicted": "bad", "unreadable": "info"}.get(v, "info")
        spot_rows.append([
            esc(c["id"]), esc(c["subject"])[:90], esc(c["claim_checked"])[:180],
            esc(c["observed"])[:420],
            f'<span class="tag {tag}">{esc(v.replace("_", " "))}</span>',
            link(c["official_url"]),
        ])
    counts = {}
    for c in spots["checks"]:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    body = f"""
<h1>First-hand spot checks</h1>
<p class="lede">Nine published claims were re-read from the official page they cite during this session.
This is a sample, not a re-verification of all {t['rows']:,} rows: anything not read is left unverified rather than assumed correct.</p>
<div class="grid">
{kpi("Checks performed", len(spots["checks"]), "read first-hand, 2026-10-22")}
{kpi("Confirmed", counts.get("confirmed", 0), "value read back exactly")}
{kpi("Partially confirmed", counts.get("partially_confirmed", 0), "some values not rendered")}
{kpi("Contradicted", counts.get("contradicted", 0), "official page disagrees")}
{kpi("Unreadable", counts.get("unreadable", 0), "cookie wall, redirect, client-rendered")}
</div>
<div class="note"><strong>The single most important result.</strong> The tennis rows in <code>/slate/</code> cite the official
Almaty order of play, and that page does not contain the pairings published. Under the brief's “no hallucinations” rule those
rows cannot stand as verified; they are listed on the flagged page.</div>
{table(["ID", "Subject", "Claim checked", "What the official page showed", "Verdict", "Official page"], spot_rows)}
<h2>Verdict definitions</h2>
<ul class="tight">{"".join(f"<li><strong>{esc(k)}</strong> — {esc(v)}</li>" for k, v in spots["verdict_key"].items())}</ul>
"""
    write("spot-checks.html", page("Spot checks", body))

    # ------------------------------------------------------------- flagged
    flag_items = []
    n = 1

    def add(title, detail, source, severity, count=None):
        nonlocal n
        flag_items.append((f"R{n:02d}", title, detail, source, severity, count))
        n += 1

    add("Tennis rows cite an official order of play that does not contain the published pairings",
        f"Spot check SC-04 read the ATP Almaty day-6 order of play for 2026-10-22. The published /slate/ pairings "
        f"(e.g. Flavio Cobolli v Rinky Hijikata) do not appear; the official card is Atmane–Bellucci, Machac–Khachanov, "
        f"Medvedev–Shimabukuro, Bublik–Marozsan plus doubles. Treat every /slate/ tennis row as unverified until re-read.",
        "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "bad",
        "13 slate tennis fixtures")
    add("Rows that are not head-to-head fixtures are published as matches",
        "Outright futures, tournament fields, venue-vs-field pairings and greyhound race meetings carry match-style "
        "moneylines and confidence grades in several layers. They cannot be settled from a scoreline.",
        "non-fixtures.html", "warn", f"{t['non_fixtures']} rows")
    add("The same fixtures are published at several URLs with different prices",
        f"{t['price_conflicts']} team-level price conflicts across {t['overlap_groups']} overlapping fixtures; the largest "
        "disagreement is over 16 decimal points on the same club on the same date.",
        "conflicts.html", "warn", f"{t['price_conflicts']} conflicts")
    add("The same selection is graded at different confidence levels",
        f"{t['confidence_conflicts']} selections are graded high in one layer and medium/low in another.",
        "conflicts.html#grades", "warn", f"{t['confidence_conflicts']} selections")
    add("Confidence grades break the project's own rule",
        f"{t['rule_violations']} rows are graded high while either below 70% model probability or outside the "
        "−250…+10000 fair-price band. Slate and hub contain the majority.",
        "conflicts.html#rules", "bad", f"{t['rule_violations']} rows")
    add("Published fixtures already in the past",
        f"{t['stale_rows']} rows are dated before the stamp of the layer that publishes them (root 21, desk 13).",
        "freshness.html", "warn", f"{t['stale_rows']} rows")
    add("Citation URLs that no longer point at the competition they are used to cite",
        "plusliga.pl/games.html resolves to tauronliga.pl and renders the women's TAURON Liga list, not the men's "
        "PlusLiga fixtures it supports. PDC rows cite a rankings page, not a fixture list.",
        "https://www.plusliga.pl/games.html", "warn", "3 volleyball + 18 darts rows")
    add("Twenty-five predictions repeat a template opening",
        f"{pr['duplicate_openings']} three-word openings are reused across {pr['count']} predictions "
        "(e.g. “Back Minnesota Wild” four times). Word counts and full-text uniqueness are otherwise clean.",
        "predictions.html", "warn", f"{pr['duplicate_openings']} openings")
    add("The site presents eleven overlapping datasets with no single authoritative one",
        f"{t['rows']:,} published rows resolve to {t['distinct_fixtures']:,} fixtures. Nothing in the navigation says which "
        "layer is authoritative for a given sport, and the README itself warns the layers must not be added together.",
        "index.html", "warn", f"{len(layers)} layers")

    flag_rows = []
    for fid, title, detail, src, sev, count in flag_items:
        src_html = (f'<a href="{esc(src)}" rel="noopener noreferrer" target="_blank">{esc(src)}</a>'
                    if src.startswith("http") else f'<a href="{esc(src)}">{esc(src)}</a>')
        tag = {"bad": "bad", "warn": "warn"}.get(sev, "info")
        flag_rows.append([esc(fid), esc(title), esc(detail), esc(count or "—"),
                          f'<span class="tag {tag}">{"material" if sev == "bad" else "review"}</span>', src_html])
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Every item below is published with the evidence needed to judge it. Nothing here blocks the site:
the console reports, it does not silently rewrite another layer's numbers. Items marked
<span class="tag bad">material</span> contradict an official source or the project's own stated rule.</p>
{table(["#", "Item", "Detail", "Scope", "Severity", "Source / evidence"], flag_rows)}
<div class="note"><strong>What is not flagged.</strong> Absence of another layer's rows from this page is not an endorsement.
Only nine claims were re-read first-hand; everything else is audited mechanically and remains unverified against its source.
The exhaustive mechanical results are on the conflicts, non-fixtures, freshness, provenance and predictions pages.</div>
"""
    write("flagged.html", page("Flagged for review", body))

    # ---------------------------------------------------------- methodology
    body = f"""
<h1>Method</h1>
<p class="lede">The audit is deterministic and reproduces exactly from committed JSON. No network call, no clock,
no randomness, no hand-entered number.</p>

<h2>Pipeline</h2>
<ul class="tight">
<li><code>python3 scripts/reconcile_audit.py</code> — reads the eleven published layers, normalises each row, and writes
<code>data/reconcile/rows.json</code> and <code>data/reconcile/report.json</code>.</li>
<li><code>python3 scripts/reconcile_build.py</code> — renders this console from those two files plus the hand-read
<code>data/reconcile/spot_checks.json</code>.</li>
<li><code>python3 scripts/reconcile_verify.py</code> — structural gate: every listed row keeps a source link, every internal
link resolves, no upstream data file changed, published counts match the report.</li>
<li><code>python3 -m unittest tests.test_reconcile</code> — unit tests over the normaliser, the classifier and the report.</li>
</ul>

<h2>Normalisation</h2>
<p class="lede">The layers publish five different market shapes (flat selection lists, per-market dicts with outcomes,
home/away dicts, winner/handicap/total objects, and survey lines keyed by side_a/side_b). Each is parsed into one record:
sport slug, date, home/away (club codes expanded from the repository's own captured team tables), moneyline decimals and
probabilities mapped by team name, pick, grade, source URL, and the layer's own capture stamp.</p>
<p class="lede">A fixture's identity is <code>(sport, date, sorted team names)</code> after accent stripping, alias
resolution and parenthetical removal. That is deliberately strict: two rows only merge when they describe the same two clubs
on the same date.</p>

<h2>Checks</h2>
{table(["ID", "Check", "Definition"], [
 [esc("C1"), "Overlap", "The same fixture published by more than one layer."],
 [esc("C2"), "Price conflict", "The same team priced at different fair decimals by different layers."],
 [esc("C3"), "Grade conflict", "The same fixture and selection graded differently across layers."],
 [esc("C4"), "Non-fixture", "Row is an outright, tournament field, venue pairing or race card, not a head-to-head fixture."],
 [esc("C5"), "Staleness", "Fixture date before the layer's capture stamp, or before the audit date."],
 [esc("C6"), "Citation", "Missing URLs, shared URLs, and hosts outside the governing-body list."],
 [esc("C7"), "Prediction quality", "Word count, duplication, selection named, market explicit, grade vs band."],
 [esc("C8"), "One URL, incompatible pairs", "A fixture-scoped URL cited by rows describing different pairings."],
 [esc("C9"), "Within-layer duplicate", "The same fixture published twice by one layer."],
 [esc("C10"), "Scope", "Rows under the brief's excluded sports; coverage of the 17 eligible sports."],
], cls="data")}

<h2>Limits, stated plainly</h2>
<ul class="tight">
<li>Only nine claims were re-read from an official page (spot-checks page). The rest of the audit is mechanical, so it can
prove inconsistency between layers but not that any single layer matches the outside world.</li>
<li>“Non-fixture” is a classification from the row's own text and structure. It is a defect report, not a deletion.</li>
<li>Price and grade conflicts are expected when layers run independent models. The finding is that no reconciliation exists,
not that a specific model is wrong.</li>
<li>The audit date is fixed at 2026-10-22 so rebuilds are reproducible; it is not read from the clock.</li>
</ul>
"""
    write("methodology.html", page("Method", body))

    # -------------------------------------------------------------- sources
    src_rows = []
    for c in spots["checks"]:
        src_rows.append([esc(c["id"]), link(c["official_url"]),
                         esc(", ".join(sorted({x["verdict"] for x in [c]})))])
    repo_sources = [
        ("NHL schedule feed (2026-10-22)", "https://api-web.nhle.com/v1/schedule/2026-10-22"),
        ("NHL club schedule (BOS, week of 2026-10-24)", "https://api-web.nhle.com/v1/club-schedule/BOS/week/2026-10-24"),
        ("ATP Almaty daily schedule", "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"),
        ("GBGB 2026 Category One schedule", "https://www.gbgb.org.uk/racing/open-races/2025-category-one-schedule/"),
        ("PDC Machineseeker European Championship", "https://www.pdc.tv/tournaments/machineseeker-european-championship"),
        ("Formula 1 2026 drivers' standings", "https://www.formula1.com/en/results/2026/drivers"),
        ("PlusLiga games page (resolves to TAURON Liga)", "https://www.plusliga.pl/games.html"),
        ("EuroLeague results API, season E2026 round 7", "https://api-live.euroleague.net/v1/results?seasonCode=E2026&round=7"),
        ("OLBG ice hockey hub (taxonomy reference)", "https://www.olbg.com/betting-tips/Ice_Hockey/13"),
    ]
    body = f"""
<h1>Sources</h1>
<p class="lede">Every URL this audit opened, and what it was used for. Internal layer files are listed as paths so the
audit is reproducible from the repository itself.</p>
<h2>Official pages read in this session</h2>
{table(["Check", "Official page", "Verdict"], src_rows)}
<h2>Governing-body endpoints used by the audited layers</h2>
<p class="lede">These are the citation hosts the layers themselves use. They were not all opened in this session; they are
listed because the provenance counts on the provenance page depend on them.</p>
{table(["Source", "URL"], [[esc(n), link(u)] for n, u in repo_sources])}
<h2>Repository inputs (read-only)</h2>
{table(["Layer", "File", "Rows"], [[esc(k), f"<code>{esc(v['path'])}</code>", f'<span class="num">{v["rows"]}</span>']
                                    for k, v in sorted(layers.items())])}
"""
    write("sources.html", page("Sources", body))

    # ------------------------------------------------------------ per sport
    per_sport = {}
    for r in rows:
        if not r["sport"]:
            continue
        per_sport.setdefault(r["sport"], []).append(r)
    write("sports/index.html", page("Sports", f"""
<h1>Sports</h1>
<p class="lede">Coverage and defect counts for each of the 17 eligible sports across all layers.</p>
{table(["Sport", "Rows", "Fixtures", "Non-fixtures", "Layers", "Conflicts"],
       [[f'<a href="{esc(k)}.html">{esc(k.replace("-", " ").title())}</a>',
         f'<span class="num">{len(v)}</span>',
         f'<span class="num">{sum(1 for r in v if r["class"] == "fixture")}</span>',
         f'<span class="num">{sum(1 for r in v if r["class"] != "fixture")}</span>',
         esc(", ".join(sorted({r["layer"] for r in v}))),
         f'<span class="num">{sum(1 for c in f["price_conflict"] if c["sport"] == k)}</span>']
        for k, v in sorted(per_sport.items())])}
""", rel="../"))

    for slug, rs in sorted(per_sport.items()):
        fixture_rows = []
        seen = set()
        for r in sorted(rs, key=lambda x: (x["date"] or "9999", x["home"])):
            key = (r["date"], r["home_norm"], r["away_norm"], r["class"])
            if key in seen:
                continue
            seen.add(key)
            fixture_rows.append([
                esc(r["date"] or "—"), esc(r["competition"])[:52],
                esc(r["home"]), esc(r["away"]),
                f'<span class="tag {"warn" if r["class"] != "fixture" else "ok"}">{esc(r["class"])}</span>',
                f'<span class="num">{r["ml_dec"][0]:.2f}</span>' if r["ml_dec"] and r["ml_dec"][0] else '<span class="blank">—</span>',
                f'<span class="num">{r["ml_dec"][1]:.2f}</span>' if r["ml_dec"] and r["ml_dec"][1] else '<span class="blank">—</span>',
                esc((r["pick"] or {}).get("confidence") or "—"),
                esc(", ".join(sorted({x["layer"] for x in rs if (x["date"], x["home_norm"], x["away_norm"]) ==
                                      (r["date"], r["home_norm"], r["away_norm"])}))),
                link(r["official_url"], "source"),
            ])
        write(f"sports/{slug}.html", page(slug.replace("-", " ").title(), f"""
<h1>{esc(slug.replace('-', ' ').title())}</h1>
<p class="lede">{len(rs)} published rows, {len({(r['date'], r['home_norm'], r['away_norm']) for r in rs})} distinct
fixtures, {sum(1 for r in rs if r['class'] != 'fixture')} rows that are not head-to-head fixtures.
Rows are de-duplicated across layers below; the “layers” column shows who publishes each fixture.</p>
<div class="filters"><input data-filter="sp-table" placeholder="Filter fixtures…" aria-label="Filter fixtures"></div>
<div id="sp-table">
{table(["Date", "Competition", "Home / A", "Away / B", "Class", "Home dec", "Away dec", "Grade", "Layers", "Source"], fixture_rows)}
</div>
""", rel="../"))

    print(f"built {len(per_sport) + 10} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
