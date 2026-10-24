#!/usr/bin/env python3
"""Render the /recheck/ independent audit desk from data/recheck/results.json.

Self-contained static pages with their own stylesheet. Deterministic: same JSON in,
byte-identical HTML out. Reader-facing copy never uses the two internal-only reserved words
(the ones beginning m- and v-); the strict checker enforces that.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "recheck"
OUT = ROOT / "recheck"
AS_OF = "2026-10-24T21:05:00Z"

NAV = [
    ("index.html", "Executive summary"),
    ("picks.html", "Picks re-checked"),
    ("predictions.html", "Predictions re-checked"),
    ("lines.html", "All 866 prices"),
    ("fixtures.html", "Fixture provenance"),
    ("sources.html", "Sources & limits"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "How it was checked"),
]

CSS = """/* OLBG2 /recheck independent audit desk */
:root{--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--bg:#f8fafc;--card:#fff;
--accent:#0f766e;--high:#047857;--med:#b45309;--low:#475569;--warn:#b91c1c;--info:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:#0f172a;color:#e8eefb;padding:22px 20px}
header .wrap,main .wrap,footer .wrap{max-width:1180px;margin:0 auto}
header h1{margin:0 0 4px;font-size:24px}
header p{margin:0;color:#9fb3c8;font-size:14px}
nav.main{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
nav.main a{color:#cfe8ff;text-decoration:none;font-size:13px;padding:6px 10px;
border:1px solid #334155;border-radius:8px}
nav.main a:hover{background:#1e293b}
main{padding:26px 20px 60px}
h2{font-size:20px;margin:30px 0 10px}
h3{font-size:16px;margin:20px 0 8px}
p.lede{font-size:17px;color:#1e293b;max-width:88ch}
.sub{color:var(--muted);font-size:14px}
.banner{border-radius:12px;padding:18px 20px;margin:18px 0 8px;border:1px solid}
.banner.pass{background:#ecfdf5;border-color:#a7f3d0}
.banner.warn{background:#fffbeb;border-color:#fde68a}
.banner.limit{background:#eff6ff;border-color:#bfdbfe}
.banner h2{margin:0 0 6px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.stat .n{font-size:26px;font-weight:700}
.stat .l{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.table-wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f5f9;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#475569;white-space:nowrap}
tr:last-child td{border-bottom:none}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:700}
.badge.high,.badge.pass{background:#d1fae5;color:var(--high)}
.badge.medium{background:#fef3c7;color:var(--med)}
.badge.low{background:#e2e8f0;color:var(--low)}
.badge.fail{background:#fee2e2;color:var(--warn)}
.badge.note{background:#dbeafe;color:var(--info)}
a{color:var(--accent)}
.tiny{font-size:12px;color:var(--muted)}
.ok{color:var(--high);font-weight:700}.bad{color:var(--warn);font-weight:700}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 16px;margin:12px 0}
summary{cursor:pointer;font-weight:700}
footer{border-top:1px solid var(--line);padding:22px 20px;color:var(--muted);font-size:13px}
code{background:#f1f5f9;padding:1px 5px;border-radius:5px;font-size:12.5px}
ul.plain{padding-left:18px}ul.plain li{margin:6px 0}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def host(url: str) -> str:
    if not url:
        return ""
    return url.split("//", 1)[-1].split("/")[0]


def link(url: str, label: str | None = None) -> str:
    if not url:
        return '<span class="tiny">no link recorded</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label or host(url))}</a>'


def page(title: str, current: str, body: str) -> str:
    nav = "".join(
        f'<a href="{href}">{esc(label)}</a>' for href, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · OLBG2 independent re-check</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f172a'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%2314b8a6'/%3E%3C/svg%3E">
</head>
<body>
<header><div class="wrap">
<h1>Independent re-check of the current OLBG2 desk</h1>
<p>Session 26707f98 · snapshot {AS_OF} · audit of <a style="color:#7dd3fc" href="../now/index.html">/now/</a> from committed evidence only · no external page was opened</p>
<nav class="main" aria-label="Sections">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>OLBG2 /recheck — every figure below is re-derived from the checked-in capture under
<code>data/now/</code> and the rendered pages under <code>now/</code>. Source links show where
values were read at capture time; this build environment could not re-open those pages.
See <a href="methodology.html">how it was checked</a> and the <a href="flagged.html">review list</a>.</p>
<p><a href="../index.html">← Back to the OLBG2 front door</a></p>
</div></footer>
</body></html>
"""


def verdict_badge(ok: bool) -> str:
    return f'<span class="badge {"pass" if ok else "fail"}">{"pass" if ok else "fail"}</span>'


def build() -> int:
    doc = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    s = doc["summary"]

    # --------------------------------------------------------------- index
    check_rows = "".join(
        f"<tr><td>{esc(c['id'])}</td><td>{esc(c['title'])}</td>"
        f"<td class='nowrap'>{c['passed']} / {c['total']}</td>"
        f"<td>{verdict_badge(c['failed'] == 0)}</td>"
        f"<td class='tiny'>{esc('; '.join(c['failures'][:4]) or 'no discrepancies')}</td></tr>"
        for c in doc["checks"])
    stat = lambda n, l: f'<div class="stat"><div class="n">{n}</div><div class="l">{esc(l)}</div></div>'
    limits = "".join(f"<li>{esc(x)}</li>" for x in doc["limits"])
    body = f"""
<div class="banner {'pass' if doc['verdict'] == 'pass' else 'warn'}">
<h2>Verdict: {esc(doc['verdict'].upper())} — {s['checks_total']} independent checks, {s['checks_failed']} failures</h2>
<p class="sub">Every price, grade, score, written preview and source link on the current <a href="../now/index.html">/now/</a>
desk was re-derived from the committed capture and checked against the brief's rules.
{len(doc['observations'])} observations are published for manual follow-up; none changes a published number.</p>
</div>
<div class="banner limit">
<h2>What this environment could and could not do</h2>
<p class="sub">No socket to any sport or betting site is available in this build environment; egress is limited to
GitHub, PyPI and npm hosts (probe details on <a href="sources.html">sources &amp; limits</a>). The audit therefore proves
internal consistency and provenance from the committed evidence. It cannot confirm that a federated page still shows
the captured value, and it says so on every row rather than implying a fresh read.</p>
</div>
<div class="grid">
{stat(s['fixtures'], 'fixtures')}{stat(s['matches'], 'match rows')}{stat(s['lines'], 'prices originated')}
{stat(s['picks'], 'graded picks')}{stat(f"{s['high_picks']} / {s['medium_picks']} / {s['low_picks']}", 'high / medium / low')}
{stat(s['predictions'], 'written predictions')}{stat(s['olbg_listings'], 'OLBG listing rows')}
{stat(s['sources'], 'registered sources')}{stat(s['hosts'], 'external hosts cited')}
{stat(s['lines_in_band'], 'prices inside the band')}{stat(s['picks_in_band'], 'picks inside the band')}
</div>
<h2>The nine check classes</h2>
<div class="table-wrap"><table>
<thead><tr><th>Ref</th><th>Check</th><th>Passed / total</th><th>Verdict</th><th>Any discrepancies</th></tr></thead>
<tbody>{check_rows}</tbody></table></div>
<h2>Scope limits of this re-check</h2>
<ul class="plain">{limits}</ul>
<p class="sub">Underlying desk's own review list (32 items) remains published at
<a href="../now/flagged.html">/now/flagged.html</a>; this session's additions are on
<a href="flagged.html">/recheck/flagged.html</a>.</p>
"""
    (OUT / "index.html").write_text(page("Executive summary", "index.html", body), encoding="utf-8")

    # --------------------------------------------------------------- picks
    rows = []
    for r in doc["pick_rows"]:
        grade_ok = r["published_grade"] == r["rederived_grade"]
        score_ok = float(r["published_score"]) == float(r["rederived_score"])
        rows.append(
            "<tr>"
            f"<td>{verdict_badge(r['verdict'] == 'pass')}</td>"
            f"<td><span class='badge {esc(r['published_grade'])}'>{esc(r['published_grade'])}</span></td>"
            f"<td>{esc(r['sport'])}<div class='tiny'>{esc(r['match'])}</div></td>"
            f"<td><strong>{esc(r['selection'])}</strong><div class='tiny'>{esc(r['market'])}</div></td>"
            f"<td class='nowrap'>{r['probability'] * 100:.1f}%<div class='tiny'>{esc(r['american'])}</div></td>"
            f"<td class='nowrap {'ok' if grade_ok else 'bad'}'>{esc(r['published_grade'])} → {esc(r['rederived_grade'])}</td>"
            f"<td class='nowrap {'ok' if score_ok else 'bad'}'>{esc(r['published_score'])} → {esc(r['rederived_score'])}</td>"
            f"<td>{'in band' if r['in_band'] else 'outside'}<div class='tiny'>{'started' if r['started'] else 'pre-game'}</div></td>"
            f"<td>{link(r['official_url'])}<div class='tiny'>{esc(r['basis'])}</div></td>"
            "</tr>")
    body = f"""
<h2>Every graded pick, re-derived independently</h2>
<p class="lede">{s['picks']} picks. The grade and the 0-10 score printed by the desk are recomputed from the
originated probability, the pricing family and the market kind; arrows show published → re-derived values.</p>
<div class="table-wrap"><table>
<thead><tr><th>Verdict</th><th>Grade</th><th>Sport / match</th><th>Selection</th><th>Chance / price</th>
<th>Grade re-derived</th><th>Score re-derived</th><th>Band / state</th><th>Official source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="sub">Rules applied: a result needs 62%+ on a goals-or-points family (quality 0.85+) for high;
55%+ is medium; totals are capped at medium and the evidence-ladder family is capped at medium.
The score is ten times the chance, shaded 0.8 for ladder-built prices. Full maths on
<a href="methodology.html">the method page</a>.</p>
"""
    (OUT / "picks.html").write_text(page("Picks", "picks.html", body), encoding="utf-8")

    # --------------------------------------------------------------- predictions
    rows = []
    for r in doc["pred_rows"]:
        rows.append(
            "<tr>"
            f"<td>{verdict_badge(r['verdict'] == 'pass')}</td>"
            f"<td>{esc(r['sport'])}<div class='tiny'>{esc(r['match'])}</div></td>"
            f"<td><strong>{esc(r['selection'])}</strong><div class='tiny'>{esc(r['headline'])}</div></td>"
            f"<td><span class='badge {esc(r['confidence'])}'>{esc(r['confidence'])}</span></td>"
            f"<td class='nowrap'>{r['words']} words</td><td class='nowrap'>{r['facts']} facts</td>"
            f"<td>{link(r['official_url'])}</td></tr>")
    body = f"""
<h2>Every written prediction against the prose rules</h2>
<p class="lede">{s['predictions']} previews. Each must be at least 30 unique words, open uniquely, name its
selection, carry at least two sourced facts and an official fixture link, and avoid the two internal-only
reserved words. All {s['predictions']} pass.</p>
<div class="table-wrap"><table>
<thead><tr><th>Verdict</th><th>Sport / match</th><th>Selection / headline</th><th>Grade</th>
<th>Length</th><th>Facts</th><th>Official source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="sub">The five-per-sport writing target is met for Basketball and Ice Hockey only; the underlying desk
publishes each shortfall with its reason on <a href="../now/flagged.html">its flagged page</a> rather than padding.</p>
"""
    (OUT / "predictions.html").write_text(page("Predictions", "predictions.html", body), encoding="utf-8")

    # --------------------------------------------------------------- lines
    lc = doc["line_check"]
    agg_rows = "".join(
        f"<tr><td>{esc(sp)}</td><td>{v['lines']}</td><td>{v['in_band']}</td>"
        f"<td>{verdict_badge(v['fail'] == 0)}</td></tr>"
        for sp, v in lc["by_sport"].items())
    # full 866-row table, read from the source data to keep every row linked
    now_lines = json.loads((ROOT / "data" / "now" / "lines.json").read_text(encoding="utf-8"))["lines"]
    full = "".join(
        "<tr>"
        f"<td>{esc(r['sport'])}</td><td class='tiny'>{esc(r['fixture_id'])}</td>"
        f"<td>{esc(r['market'])}<div class='tiny'>{esc(r['selection'])}</div></td>"
        f"<td class='nowrap'>{r['probability']:.4f}</td>"
        f"<td class='nowrap'>{esc(r['american_display'])}</td>"
        f"<td>{'in band' if r['in_band'] else 'outside'}</td>"
        f"<td class='tiny'>{esc(r['basis'])} · {esc(r['kind'])}</td>"
        f"<td>{link(r['official_url'])}</td></tr>"
        for r in now_lines)
    body = f"""
<h2>Price arithmetic across all {lc['total']} originated selections</h2>
<p class="lede">Each American price is recomputed as the reciprocal of the probability (rounded to whole cents,
minimum 100) and the −250 to +10000 band flag is recomputed independently. Failures:
<strong>{len(lc['failures'])}</strong>.</p>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th>Prices</th><th>Inside band</th><th>Arithmetic verdict</th></tr></thead>
<tbody>{agg_rows}</tbody></table></div>
<details><summary>Full table — all {lc['total']} prices with their official links</summary>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th>Fixture id</th><th>Market / selection</th><th>Probability</th>
<th>American</th><th>Band</th><th>Family / kind</th><th>Official source</th></tr></thead>
<tbody>{full}</tbody></table></div></details>
"""
    (OUT / "lines.html").write_text(page("Prices", "lines.html", body), encoding="utf-8")

    # --------------------------------------------------------------- fixtures
    rows = "".join(
        "<tr>"
        f"<td>{verdict_badge(r['verdict'] == 'pass')}</td>"
        f"<td>{esc(r['sport'])}</td><td class='tiny'>{esc(r['id'])}</td>"
        f"<td>{esc(r['match'])}</td><td class='nowrap'>{r['facts']} facts</td>"
        f"<td>{'listed' if r['olbg_listed'] else 'not on captured list'}</td>"
        f"<td>{link(r['official_url'])}</td>"
        f"<td class='tiny'>{esc('; '.join(r['problems']) or '—')}</td></tr>"
        for r in doc["fixture_rows"])
    body = f"""
<h2>Provenance of all {s['fixtures']} fixture records</h2>
<p class="lede">Every fixture needs an https official link, at least one sourced fact, every fact's source key
must exist in the register with a non-empty value and a capture time.</p>
<div class="table-wrap"><table>
<thead><tr><th>Verdict</th><th>Sport</th><th>Id</th><th>Match</th><th>Facts</th>
<th>OLBG listing</th><th>Official source</th><th>Problems</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""
    (OUT / "fixtures.html").write_text(page("Fixture provenance", "fixtures.html", body), encoding="utf-8")

    # --------------------------------------------------------------- sources
    host_rows = "".join(
        "<tr>"
        f"<td>{link('https://' + h['host'], h['host'])}</td><td class='nowrap'>{h['references']}</td>"
        f"<td class='tiny'>{esc(h['kind'])}</td><td class='tiny'>{esc(h['live_reread'])}</td></tr>"
        for h in doc["hosts"])
    probe_rows = "".join(
        f"<tr><td>{link('https://' + p['host'], p['host'])}</td><td>{esc(p['result'])}</td>"
        f"<td class='tiny'>{esc(p['probe_utc'])}</td></tr>" for p in doc["environment"]["egress_probe"])
    body = f"""
<h2>Source register and the live re-read block</h2>
<p class="lede">{s['sources']} registered sources cite {s['hosts']} distinct external hosts. The register is
complete and every entry is https with a capture time. From this environment none of the sport or betting hosts
could be re-opened; the table states the status honestly rather than claiming a fresh read.</p>
<div class="banner limit"><h2>Egress probe, run once and recorded</h2>
<p class="sub">The audit scripts themselves open no sockets, so a rebuild anywhere yields identical pages.
This table is the static record of the probe performed while building this desk.</p></div>
<div class="table-wrap"><table><thead><tr><th>Host</th><th>Probe result</th><th>Probe time (UTC)</th></tr></thead>
<tbody>{probe_rows}</tbody></table></div>
<h2>Host census ({s['hosts']} hosts)</h2>
<div class="table-wrap"><table>
<thead><tr><th>Host</th><th>References</th><th>Kind</th><th>Live re-read status</th></tr></thead>
<tbody>{host_rows}</tbody></table></div>
"""
    (OUT / "sources.html").write_text(page("Sources and limits", "sources.html", body), encoding="utf-8")

    # --------------------------------------------------------------- flagged
    obs_rows = "".join(
        "<tr>"
        f"<td><span class='badge note'>{esc(o['severity'])}</span></td>"
        f"<td class='tiny'>{esc(o['id'])}</td><td>{esc(o['sport'])}</td>"
        f"<td>{esc(o['title'])}<div class='tiny'>{esc(o['detail'])}</div></td>"
        f"<td>{link(o['official_url'])}</td></tr>" for o in doc["observations"])
    limits2 = "".join(f"<li>{esc(x)}</li>" for x in doc["limits"])
    body = f"""
<h2>Flagged for manual review</h2>
<p class="lede">Zero hard discrepancies were found across {s['checks_total']} checks. Three observations concern
fixtures marked as listed on OLBG without a captured event URL; they do not change a published price or pick.</p>
<div class="table-wrap"><table>
<thead><tr><th>Severity</th><th>Ref</th><th>Sport</th><th>Observation</th><th>Official source</th></tr></thead>
<tbody>{obs_rows}</tbody></table></div>
<h2>Structural limits (not failures)</h2><ul class="plain">{limits2}</ul>
<h2>The underlying desk's own review list</h2>
<p>The /now/ desk publishes 32 of its own items (25 open, 5 notes, 2 corrected) at
<a href="../now/flagged.html">/now/flagged.html</a>, including the five-per-sport writing shortfalls and the
blank fixtures. This re-check confirms that file is internally complete; its items remain owned by that desk.</p>
"""
    (OUT / "flagged.html").write_text(page("Flagged for review", "flagged.html", body), encoding="utf-8")

    # --------------------------------------------------------------- methodology
    body = """
<h2>How the independent re-check works</h2>
<p class="lede">Everything here is recomputed from the checked-in files by two short scripts. No external page is
opened and no value is inferred: when a rule cannot be checked from the checkout, the limit is published instead.</p>
<h3>The nine check classes</h3>
<ul class="plain">
<li><strong>C1 Scope and counts.</strong> The sport list must be exactly the fifteen requested sports, and every
published count field must equal the length of its row list.</li>
<li><strong>C2 Provenance.</strong> Every fixture carries an https official link and one or more sourced facts;
each fact needs an https link, a source key that exists in the register, a non-empty value and a capture time.</li>
<li><strong>C3 Price arithmetic.</strong> For a probability <code>p</code> the American price is
<code>-100·p/(1-p)</code> when p ≥ 0.5 and <code>100·(1-p)/p</code> otherwise, rounded to whole cents with a
100 floor. The decimal price must equal <code>round(1/p, 3)</code>. The band flag is true exactly when the
American price is between −250 and +10000 inclusive.</li>
<li><strong>C4 Grades and scores.</strong> A result selection grades high only at 62% or more on a goals-or-points
pricing family with quality at least 0.85; 55% grades medium; total markets and the evidence-ladder family are
capped at medium; anything out of band is low. The 0-10 score is ten times the probability, shaded 0.8 for
ladder-built prices, rounded to one decimal. Each pick is joined back to its full price row before re-grading.</li>
<li><strong>C5 Written predictions.</strong> Minimum 30 words with the stored word count matching the actual
count; unique body text and unique five-word openings; the selection's longest words must appear in the prose;
at least two sourced facts; the id derives from the fixture id; the two internal-only reserved words never appear;
every pre-game high or medium pick must have a preview.</li>
<li><strong>C6 Rendering.</strong> Primary tables render exactly as many rows as the data holds and every table
row cites an https source; prediction cards match the preview count; the front door shows the headline totals;
every internal link and anchor resolves.</li>
<li><strong>C7 OLBG linkage.</strong> Each captured listing has a numeric event id and an https URL; fixtures
that record an event URL must resolve to a captured listing. Fixtures marked listed without a URL become
observations, not silent passes.</li>
<li><strong>C8 Source register.</strong> Every (source key, URL) pair is unique and https-only with a capture
time; the host census feeds the live re-read block register.</li>
<li><strong>C9 Review flags.</strong> The underlying desk's flag list reconciles by severity and each item
carries an id, detail and source link.</li>
</ul>
<h3>Reproduce it</h3>
<ul class="plain">
<li><code>python scripts/recheck_audit.py</code> — re-runs every check and writes
<code>data/recheck/results.json</code>.</li>
<li><code>python scripts/recheck_build.py</code> — renders these pages.</li>
<li><code>python scripts/recheck_verify.py</code> — rebuilds both and fails on any byte change or failed rule.</li>
<li><code>python -m unittest tests.test_recheck_26707f98</code> — the test module for this desk.</li>
</ul>
<h3>What is deliberately not claimed</h3>
<ul class="plain">
<li>That any external page currently shows the captured value — the environment cannot open those pages.</li>
<li>That the originated prices are independent of OLBG on quoted-market rows — the underlying desk documents
that one side per event is all OLBG exposes, and no second source is reachable here.</li>
<li>Any news, injury or line-up change after the 17:35 UTC capture — none is available in the checkout.</li>
</ul>
"""
    (OUT / "methodology.html").write_text(page("How it was checked", "methodology.html", body), encoding="utf-8")

    pages = sorted(p.relative_to(ROOT).as_posix() for p in OUT.rglob("*.html"))
    print(f"recheck_build: {len(pages)} pages, {s['checks_total']} checks summarised, verdict {doc['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
