#!/usr/bin/env python3
"""Daily Top-5 desk: static dashboard builder (session arena/b499dfe1-olbg2)."""
import json, os, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "daily"); SITE = os.path.join(ROOT, "daily")
os.makedirs(os.path.join(SITE, "sports"), exist_ok=True); os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
def load(n):
    with open(os.path.join(D, n)) as f: return json.load(f)
E = html.escape
CSS = """
:root{--bg:#0f1419;--card:#1a2230;--ink:#e8eef5;--mut:#9fb0c3;--acc:#4da3ff;--hi:#2ecc71;--med:#f1c40f;--low:#e67e22;--line:#2b3a4f}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--acc)}.wrap{max-width:1180px;margin:0 auto;padding:20px}
header.site{background:#131c29;border-bottom:1px solid var(--line)}nav a{margin-right:14px;text-decoration:none;font-weight:600}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:150px}
.kpi b{font-size:26px;display:block}.mut{color:var(--mut)}table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.05em}
.badge{display:inline-block;padding:1px 8px;border-radius:20px;font-size:12px;font-weight:700;color:#10151c}
.high{background:var(--hi)}.medium{background:var(--med)}.low{background:var(--low)}.blank{background:#566}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
small{color:var(--mut)}footer{border-top:1px solid var(--line);margin-top:30px;padding:16px 0;color:var(--mut);font-size:13px}
.pred p{line-height:1.55}.filter{margin:10px 0}.filter input,.filter select{padding:7px;background:#0d1420;color:var(--ink);border:1px solid var(--line);border-radius:6px}
"""
open(os.path.join(SITE, "assets", "daily.css"), "w").write(CSS)

def page(title, body, depth=0):
    pre = "../" * depth
    nav = " ".join(f'<a href="{pre}{h}">{t}</a>' for h, t in
                   [("index.html", "Dashboard"), ("matches.html", "All Matches &amp; Lines"), ("top5.html", "Top 5 per Sport"),
                    ("predictions.html", "Predictions"), ("sports/index.html", "By Sport"), ("methodology.html", "Methodology"),
                    ("sources.html", "Sources"), ("flagged.html", "Flagged for Review")])
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — OLBG2 Daily Top-5 Desk</title><link rel="stylesheet" href="{pre}assets/daily.css"></head><body>
<header class="site"><div class="wrap"><strong>OLBG2 · Daily Top-5 Desk</strong> <small>originated lines, capture 2026-10-22, window 23–30 Oct 2026</small><nav style="margin-top:8px">{nav}</nav>
<small>Cross-layer: <a href="{pre}../index.html">root dashboard</a> · <a href="{pre}../current/index.html">/current/</a> · <a href="{pre}../final/index.html">/final/</a> · <a href="{pre}../flagged.html">root Flagged for Review</a></small></div></header>
<main class="wrap"><h1>{E(title)}</h1>{body}
<footer>Prices are this project's own originated fair no-vig lines (decimal = 1/p), <strong>not</strong> bookmaker quotes and not betting advice. Confidence: high = model probability ≥70% with fair American odds inside −250…+10000 plus a sample gate. Unverified values are left blank and flagged. 18+ Gamble responsibly.</footer>
</main></body></html>"""

def am(o): return f"{o['fair_decimal']} ({o['fair_american']:+d})".replace("+","+") if o else ""
def fmt_am(o):
    if not o: return '<span class="badge blank">blank</span>'
    a = o["fair_american"]; return f"{o['fair_decimal']:.2f} ({'+' if a>0 else ''}{a})"
def badge(c): return f'<span class="badge {E(c)}">{E(c)}</span>'

FX = load("fixtures.json")["fixtures"]; LINES = {r["match_id"]: r for r in load("lines.json")["rows"]}
TOP5 = load("top5.json")["top5"]; PREDS = load("predictions.json")["predictions"]
SPORTS = load("sports.json")["sports"]; EXCL = load("sports.json")["excluded"]
SRCS = load("sources.json")["sources"]; FLAGS = load("flagged.json")["flags"]; UNL = load("unlined.json")["unlined"]
PRED_BY_ID = {p["match_id"]: p for p in PREDS}
PREDLINK = {k: f'<br><a href="predictions.html#{k}">prediction</a>' for k in PRED_BY_ID}
SNAME = {s["slug"]: s["name"] for s in SPORTS}
highs = [p for v in TOP5.values() for p in v if p["confidence"] == "high"]
all_high = [r for r in LINES.values() if r.get("primary_pick") and r["primary_pick"]["confidence"] == "high"]

# ---- index ----
cards = ""
for s in SPORTS:
    n = sum(1 for f in FX if f["sport"] == s["slug"]); t = len(TOP5.get(s["slug"], []))
    un = sum(1 for u in UNL if u["sport"] == s["slug"])
    cards += f'<div class="card"><h3><a href="sports/{s["slug"]}.html">{E(s["name"])}</a></h3><p>{n} originated fixture(s) · {t}/5 Top-5 picks · {un} unlined<br><small>OLBG sport id {E(str(s.get("olbg_sport_id") or "—"))} · <a href="{E(s["olbg_url"])}" rel="noopener">OLBG hub</a> · <a href="{E(s["official_url"])}" rel="noopener">official site</a></small></p></div>'
body = f"""<p>Reverse-engineered from OLBG's public taxonomy (sport hubs at <code>/betting-tips/{{Sport}}/{{sport_id}}</code>, event pages with <code>event_id</code>), then rebuilt independently: every price below is <strong>originated by our own models</strong> from official-source inputs captured 2026-10-22. OLBG prices are never used. Excluded per brief: soccer/football, boxing, UFC/MMA, American football, hurling, Horse Racing, cycling, specials.</p>
<div class="kpis">
<div class="kpi"><b>{len(FX)}</b>upcoming fixtures originated (23–30 Oct)</div>
<div class="kpi"><b>{sum(len(v) for v in TOP5.values())}</b>Top-5 picks across {sum(1 for v in TOP5.values() if v)} sports</div>
<div class="kpi"><b>{len(all_high)}</b>high-confidence in-band picks (≥70%, −250…+10000)</div>
<div class="kpi"><b>{len(PREDS)}</b>written predictions (≥30 words, unique)</div>
<div class="kpi"><b>{len(FLAGS)}</b>flags on the <a href="flagged.html">review page</a></div></div>
<h2>Covered sports (17)</h2><div class="grid">{cards}</div>
<h2>How to read this desk</h2><p><strong>All Matches &amp; Lines</strong> shows every originated market (match winner, handicap/spread, totals, plus darts leg markets and the F1 race-winner outright). <strong>Top 5 per Sport</strong> ranks each sport's five highest-probability primary picks. Where a sport has fewer than five verifiable fixtures the slots stay blank and the gap is flagged — quotas are never filled with invented matches.</p>"""
open(os.path.join(SITE, "index.html"), "w").write(page("Daily Top-5 Dashboard", body))

# ---- matches ----
rows = ""
for fx in sorted(FX, key=lambda f: (f["date"], f["sport"], f["id"])):
    r = LINES.get(fx["id"], {}); wp = r.get("winner_pick") or {}; pp = r.get("primary_pick") or {}
    mk_txt = "<br>".join(
        f"<small><b>{E(m['market'])}</b>" + (f" — main line {E(str(m['line']))}" if m.get("line") != "" and m.get("line") is not None else "") +
        (": " + "; ".join(f"{E(o['name'])} {o['p']*100:.1f}% {fmt_am(o)}" for o in m["outcomes"][:6]) +
         (f" … +{len(m['outcomes'])-6} alternate lines in data" if len(m["outcomes"]) > 6 else "") if m["outcomes"] else f": <span class='badge blank'>blank</span> {E(m.get('blank_reason',''))}") + "</small>"
        for m in r.get("markets", []))
    fix = f"{E(fx['home'])} v {E(fx['away'])}" if fx["away"] else E(fx["home"])
    rows += f"""<tr data-sport="{fx['sport']}"><td>{fx['date']}<br><small>{E(SNAME.get(fx['sport'],fx['sport']))}</small></td>
<td><b>{fix}</b><br><small>{E(fx['competition'])}{(' · ' + E(fx['venue'])) if fx.get('venue') else ''}</small><br>{mk_txt}</td>
<td>{E(wp.get('name',''))}<br><small>{(str(round(wp['p']*100,1))+'%') if wp else ''} {fmt_am(wp) if wp else ''}</small></td>
<td>{E(pp.get('name',''))}<br><small>{E(pp.get('market',''))}</small></td><td>{badge(pp.get('confidence','low')) if pp else ''}<br><small>{(str(round(pp['p']*100,1))+'%') if pp else ''} {fmt_am(pp) if pp else ''}</small></td>
<td><a href="{E(fx['official_url'])}" rel="noopener">official source</a>{PREDLINK.get(fx['id'],'')}</td></tr>"""
for u in UNL:
    rows += f"""<tr data-sport="{u['sport']}"><td>{u['date']}<br><small>{E(SNAME.get(u['sport'],u['sport']))}</small></td>
<td><b>{E(u['home'])} v {E(u['away'])}</b><br><small>{E(u['competition'])}</small><br><small>{E(u['blank_reason'])}</small></td>
<td colspan="3"><span class="badge blank">blank — unverified, see Flagged</span></td><td><a href="{E(u['official_url'])}" rel="noopener">official source</a></td></tr>"""
opts = "".join(f'<option value="{s["slug"]}">{E(s["name"])}</option>' for s in SPORTS)
body = f"""<p>Every upcoming fixture in the window with all originated markets. Alternate handicap/total lines beyond the first six outcomes are in <code>data/daily/lines.json</code>.</p>
<div class="filter"><label>Sport <select id="sf" onchange="f()"><option value="">All sports</option>{opts}</select></label> <input id="q" placeholder="Search team…" oninput="f()"></div>
<table id="mt"><thead><tr><th>Date / Sport</th><th>Fixture &amp; originated markets</th><th>Match-winner pick</th><th>Primary pick</th><th>Confidence</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table>
<script>function f(){{var s=document.getElementById('sf').value,q=document.getElementById('q').value.toLowerCase();document.querySelectorAll('#mt tbody tr').forEach(function(r){{r.style.display=(!s||r.dataset.sport===s)&&(!q||r.textContent.toLowerCase().includes(q))?'':'none'}})}}</script>"""
open(os.path.join(SITE, "matches.html"), "w").write(page("All Matches & Lines", body))

# ---- top5 ----
sec = ""
for s in SPORTS:
    cand = TOP5.get(s["slug"], [])
    trs = "".join(f"""<tr><td>{p['sport_rank']}</td><td>{p['date']}</td><td><b>{E(p['fixture'])}</b><br><small>{E(p['competition'])}</small></td>
<td><b>{E(p['selection'])}</b><br><small>{E(p['market'])}</small></td><td>{p['p']*100:.1f}%</td><td>{fmt_am(p)}</td><td>{badge(p['confidence'])}</td>
<td><a href="{E(p['official_url'])}" rel="noopener">official</a> · <a href="predictions.html#{p['match_id']}">write-up</a></td></tr>""" for p in cand)
    for i in range(len(cand) + 1, 6):
        trs += f'<tr><td>{i}</td><td colspan="7"><span class="badge blank">blank</span> <small>No further verifiable fixture in window — see <a href="flagged.html">Flagged for Review</a>.</small></td></tr>'
    sec += f'<h2>{E(s["name"])}</h2><table><thead><tr><th>#</th><th>Date</th><th>Fixture</th><th>Selection</th><th>Model %</th><th>Our fair price</th><th>Conf.</th><th>Links</th></tr></thead><tbody>{trs}</tbody></table>'
open(os.path.join(SITE, "top5.html"), "w").write(page("Top 5 Picks per Sport", "<p>Ranked by the model probability of each match's primary pick (in-band alternate where one exists, otherwise the match-winner pick). High = ≥70% <em>and</em> fair price inside −250…+10000 with the sample gate passed.</p>" + sec))

# ---- predictions ----
cards2 = "".join(f"""<article class="card pred" id="{p['match_id']}"><h3>{E(p['fixture'])}</h3>
<p><small>{E(SNAME.get(p['sport'],p['sport']))} · {E(p['competition'])} · {p['date']}</small><br>
<b>Selection: {E(p['selection'])}</b> ({E(p['market'])}) — {p['p']*100:.1f}%, our fair price {fmt_am(p)} {badge(p['confidence'])}</p>
<p>{E(p['text'])}</p><p><small>{p['word_count']} words · facts checked against the row's official capture · <a href="{E(p['official_url'])}" rel="noopener">official source</a></small></p></article>"""
for p in sorted(PREDS, key=lambda x: (-x["p"], x["date"])))
open(os.path.join(SITE, "predictions.html"), "w").write(page("Written Predictions", f"<p>{len(PREDS)} unique write-ups (every Top-5 pick and every high-confidence pick). Each names the selection in its first sentence and uses only official-source facts stored on the fixture row — records, scoring rates, form lines, rankings and named player leaders where the official feed provides them. No injury, lineup or travel claims are made.</p>" + cards2))

# ---- sport pages ----
idx = ""
for s in SPORTS:
    fxs = [f for f in FX if f["sport"] == s["slug"]]; uns = [u for u in UNL if u["sport"] == s["slug"]]
    trs = ""
    for fx in sorted(fxs, key=lambda f: f["date"]):
        r = LINES.get(fx["id"], {}); pp = r.get("primary_pick") or {}; wp = r.get("winner_pick") or {}
        fix = f"{E(fx['home'])} v {E(fx['away'])}" if fx["away"] else E(fx["home"])
        trs += f"<tr><td>{fx['date']}</td><td><b>{fix}</b><br><small>{E(fx['competition'])}</small></td><td>{E(wp.get('name',''))}</td><td>{E(pp.get('name',''))}<br><small>{E(pp.get('market',''))}</small></td><td>{badge(pp.get('confidence','low')) if pp else ''} {(str(round(pp['p']*100,1))+'%') if pp else ''} {fmt_am(pp) if pp else ''}</td><td><a href=\"{E(fx['official_url'])}\" rel=\"noopener\">official</a></td></tr>"
    for u in uns:
        trs += f"<tr><td>{u['date']}</td><td><b>{E(u['home'])} v {E(u['away'])}</b><br><small>{E(u['competition'])}</small></td><td colspan=\"3\"><span class=\"badge blank\">blank</span> <small>{E(u['blank_reason'])}</small></td><td><a href=\"{E(u['official_url'])}\" rel=\"noopener\">official</a></td></tr>"
    if not trs: trs = '<tr><td colspan="6">No fixture rows in this window — see Flagged for Review for the verified reason.</td></tr>'
    mkt = "".join(f"<li>{E(m)}</li>" for m in s.get("markets_investigated", []))
    b = f"""<p><a href="index.html">By sport</a> › {E(s['name'])}</p><p>{len(fxs)} originated fixture(s), {len(TOP5.get(s['slug'],[]))}/5 Top-5 picks, {len(uns)} unlined. Markets investigated:</p><ul>{mkt}</ul>
<table><thead><tr><th>Date</th><th>Fixture</th><th>Winner pick</th><th>Primary pick</th><th>Confidence / price</th><th>Source</th></tr></thead><tbody>{trs}</tbody></table>"""
    open(os.path.join(SITE, "sports", s["slug"] + ".html"), "w").write(page(s["name"], b, depth=1))
    idx += f'<div class="card"><h3><a href="{s["slug"]}.html">{E(s["name"])}</a></h3><p>{len(fxs)} originated · {len(TOP5.get(s["slug"],[]))}/5 Top-5 · {len(uns)} unlined</p></div>'
open(os.path.join(SITE, "sports", "index.html"), "w").write(page("By Sport", f'<div class="grid">{idx}</div>', depth=1))

# ---- methodology / sources / flagged ----
meth = """<h2>Verification chain</h2><ol><li><b>Discovery:</b> OLBG sport hubs (<code>/betting-tips/{Sport}/{sport_id}</code>, re-fetched 2026-10-22) define the 17-sport eligible taxonomy after exclusions.</li><li><b>Confirmation:</b> fixtures come only from official league/governing-body captures stored in this repo (NHL score API, NBA.com, EuroLeague, LNR, URC, EHF, PDC, MLB Stats API, formula1.com), with fresh 2026-10-22 confirmation fetches recorded in <code>research/daily-b499dfe1.md</code>.</li><li><b>Origination:</b> our own models (below). No bookmaker/OLBG price is read.</li><li><b>Publication:</b> every row links its official source; unverifiable values stay blank and flagged.</li></ol>
<h2>Models</h2><ul>
<li><b>NHL / MLB / EHF — Poisson attack-defence:</b> shrunk scoring &amp; concession rates vs league average (NHL prior 8 GP, home +5%; EHF prior 3, home +0.4 goals; MLB 162-game rates, home +2%), full score grid → winner (ties split for OT/SO; EHF also 1X2), ±1.5 handicap/run/puck line (+ one alternate step), totals around expected total.</li>
<li><b>EuroLeague / Top 14 / Pro D2 / URC — margin-normal:</b> expected scores from shrunk PF/PA attack-defence, σ 11 (EuroLeague) / 14 (rugby), home +3 pts → winner, spread, totals, with alternate lines stepped to search the −250…+10000 band at 1-point increments (wider steps beyond ±6).</li>
<li><b>NBA — prior-season logit:</b> 2025-26 records shrunk 25% to .500, rating diff ×11 + 0.20 home logit → moneyline &amp; spread. Totals <b>not originated</b> (no verified PF/PA). Confidence capped at medium (0 current-season games at capture).</li>
<li><b>Darts — Bradley-Terry on PDC Werner Rankings Ladder prize money:</b> damped log-prize per-leg probability → first-to-6 match, ±1.5 legs, O/U 9.5 legs (negative-binomial race).</li>
<li><b>F1 outright — points-share blend:</b> 65% championship-points share + 35% recorded race-wins share, normalised across 23 drivers. Capped at medium.</li></ul>
<h2>Confidence &amp; the focus band</h2><p>High requires model p ≥ 70% <strong>and</strong> fair American price (from rounded no-vig decimal 1/p) inside −250…+10000 <strong>and</strong> the sample gate (NHL ≥7 GP both, EHF ≥4, rugby ≥3 rounds; NBA/MLB/F1 capped for stated reasons). Medium ≥60%, low below. Alternate handicap/total lines are used to express 70%+ opinions inside the band; the in-band selection closest to the 70% floor is chosen. If no in-band selection exists, the primary pick is the plain match winner — never an extreme alternate at ~1.01.</p>
<h2>Top 5 &amp; predictions</h2><p>Per sport, matches are ranked by primary-pick probability; the top five (or fewer, blank-flagged) form the daily five. A written prediction (≥30 words, unique) accompanies every Top-5 pick and every high-confidence pick, built only from seeded official facts: records, per-game scoring/concession, form lines, rankings/prize money, and official player leaders (NHL feed). No injuries, lineups, transfers or travel are asserted.</p>
<h2>Limitations</h2><ul><li>Early-season samples (NHL 7–12 GP, URC 3 rounds) are noisy; shrinkage guards but does not fix roster change.</li><li>NBA priors are a season old. MLB has no probable-pitcher input. F1 has no qualifying input.</li><li>Coverage is the captured official competitions only — not every event worldwide. Gaps are enumerated on the Flagged page.</li><li>Fair prices carry no margin; they are not value claims against any market.</li></ul>"""
open(os.path.join(SITE, "methodology.html"), "w").write(page("Methodology", meth))
srows = "".join(f'<tr><td>{E(x["id"])}</td><td>{E(x["name"])}</td><td><a href="{E(x["url"])}" rel="noopener">{E(x["url"])}</a></td><td>{E(x["captured"])}</td><td><small>{E(x.get("note",""))}</small></td></tr>' for x in SRCS)
open(os.path.join(SITE, "sources.html"), "w").write(page("Official Sources", f"<table><thead><tr><th>ID</th><th>Source</th><th>URL</th><th>Captured</th><th>Note</th></tr></thead><tbody>{srows}</tbody></table>"))
frows = "".join(f'<tr><td>{E(f["id"])}</td><td>{E(SNAME.get(f["sport"],f["sport"]))}</td><td>{E(f["kind"])}</td><td>{E(f["item"])}<br><small>{E(f["detail"])}</small></td><td><a href="{E(f["official_url"])}" rel="noopener">official source</a></td></tr>' for f in FLAGS)
open(os.path.join(SITE, "flagged.html"), "w").write(page("Flagged for Review", f"<p>{len(FLAGS)} items need human review. Nothing here blocks publication; unverified values are blank everywhere else on this desk.</p><table><thead><tr><th>ID</th><th>Sport</th><th>Kind</th><th>Item &amp; detail</th><th>Source</th></tr></thead><tbody>{frows}</tbody></table>"))
print("pages built")
