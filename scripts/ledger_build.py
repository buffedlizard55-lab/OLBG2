#!/usr/bin/env python3
"""Build the /ledger/ static dashboard from data/ledger/*.json (session 21a0c524)."""
import json
from html import escape as e
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ledger"
L = json.loads((ROOT / "data/ledger/lines.json").read_text())
P = json.loads((ROOT / "data/ledger/predictions.json").read_text())["predictions"]
F = json.loads((ROOT / "data/ledger/flagged.json").read_text())["flags"]
SRC = {s["key"]: s for s in json.loads((ROOT / "data/ledger/sources.json").read_text())["sources"]}
IN = json.loads((ROOT / "data/ledger/inputs.json").read_text())
MATCH = {m["id"]: m for m in L["matches"]}
SEL = L["selections"]

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
SLUG = {s: s.lower().replace(" ", "-") for s in SPORTS}

CSS = """/* ledger desk */
*{box-sizing:border-box}body{margin:0;font:16px/1.55 -apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#17202a;background:#f6f8fa}
header{background:#0b2a4a;color:#fff;padding:14px 18px}header b{font-size:20px}header span{opacity:.85;font-size:13px;margin-left:8px}
nav{background:#123c66;padding:8px 18px;display:flex;flex-wrap:wrap;gap:6px}nav a{color:#dcebfb;text-decoration:none;padding:5px 10px;border-radius:6px;font-size:14px}nav:c{color:#fff}nav a:hover{background:#1d4f82;color:#fff}
main{max-width:1180px;margin:0 auto;padding:20px 16px 48px}h1{font-size:26px;margin:.2em 0 .4em}h2{font-size:20px;margin:1.4em 0 .5em;border-bottom:2px solid #0b2a4a;padding-bottom:4px}h3{margin:1.2em 0 .4em}
table{border-collapse:collapse;width:100%;background:#fff;font-size:14px;margin:.5em 0 1em}th,td{border:1px solid #d5dde5;padding:6px 8px;text-align:left;vertical-align:top}th{background:#0b2a4a;color:#fff}tr:nth-child(even) td{background:#f0f4f8}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:12px 0}.card{background:#fff;border:1px solid #d5dde5;border-radius:10px;padding:12px}.card b{font-size:22px;display:block}
.sportgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.sport{background:#fff;border:1px solid #d5dde5;border-radius:10px;padding:12px}.sport a{font-weight:700;font-size:17px}
.pill{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;font-weight:700}.A{background:#0a7a42;color:#fff}.B{background:#b45309;color:#fff}.C{background:#334155;color:#fff}
.High{background:#0a7a42;color:#fff}.Medium{background:#d97706;color:#fff}.Low{background:#64748b;color:#fff}
.preview{background:#fff;border:1px solid #d5dde5;border-left:5px solid #0b2a4a;border-radius:8px;padding:14px;margin:12px 0}.preview h3{margin-top:0}
.note{background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:12px;margin:12px 0}.ok{background:#ecfdf5;border-color:#a7f3d0}
small{color:#475569}footer{max-width:1180px;margin:0 auto;padding:0 16px 30px;color:#475569;font-size:13px}
a{color:#0b5cad}@media(max-width:720px){table{font-size:12px}th,td{padding:4px}}
"""

def source_links(keys):
    out = []
    for k in keys or []:
        if k in SRC:
            out.append(f'<a href="{e(SRC[k]["url"])}">{e(SRC[k]["name"])}</a>')
    return "<br>".join(out) if out else "—"

def page(title, body, depth=0):
    p = "../" * depth
    nav = "".join(f'<a href="{p}{h}">{t}</a>' for h, t in [
        ("index.html", "Dashboard"), ("picks.html", "Top picks"), ("previews.html", "Previews"),
        ("matches.html", "All matches"), ("lines.html", "All lines"), ("sports/index.html", "Sports"),
        ("flagged.html", "Flagged for Review"), ("sources.html", "Sources"), ("method.html", "Method"),
        ("olbg.html", "OLBG map"), ("verification.html", "Verification")])
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{e(title)} — Ledger desk</title><link rel='stylesheet' href='{p}assets/style.css'></head><body>"
            f"<header><b>Ledger desk</b><span>15-sport OLBG coverage · own originated prices · captured 23 Oct 2026</span></header><nav>{nav}</nav>"
            f"<main>{body}</main><footer>Fair prices originated for this desk from official data only — they are not bookmaker offers. "
            f"18+. Betting involves risk; never bet more than you can afford to lose.</footer></body></html>")

def fmt_am(am):
    return f"+{am}" if am and am > 0 else str(am)

def sel_rows(rows, with_fixture=True):
    tr = ""
    for s in rows:
        m = MATCH[s["fixture"]]
        ev = (m["away"] + " at " + m["home"]) if m.get("away") else m["home"]
        band = "in band" if s["in_band"] else "outside band"
        tier = s["tier"] or "—"
        pre = ""
        if with_fixture:
            pre = "<td>" + e(m["sport"]) + "<br><small>" + e(m["date"]) + "</small></td><td>" + e(ev) + "<br><small>" + e(m["competition"]) + "</small></td>"
        tr += ("<tr>" + pre
               + "<td>" + e(s["market"]) + "</td><td><b>" + e(s["selection"]) + "</b></td>"
               + "<td>{:.1f}%</td>".format(s["prob"] * 100)
               + "<td>" + fmt_am(s["american"]) + "<br><small>" + str(s["decimal"]) + "</small></td>"
               + "<td><span class='pill " + s["confidence"] + "'>" + s["confidence"] + "</span></td>"
               + "<td><span class='pill " + (s["tier"] or "C") + "'>Tier " + tier + "</span><br><small>" + band + "</small></td>"
               + "<td>" + source_links(m["source_keys"]) + "</td></tr>")
    head = ("<tr><th>Sport / date</th><th>Event</th>" if with_fixture else "<tr>") + "<th>Market</th><th>Selection</th><th>Chance</th><th>Our fair price (US / decimal)</th><th>Confidence</th><th>Band tier</th><th>Official source</th></tr>"
    return "<table>" + head + tr + "</table>"

def best_per_fixture(sels):
    best = {}
    for s in sels:
        if s["fixture"] not in best or s["prob"] > best[s["fixture"]]["prob"]:
            best[s["fixture"]] = s
    return sorted(best.values(), key=lambda x: -x["prob"])

by_sport_sel = defaultdict(list)
for s in SEL: by_sport_sel[MATCH[s["fixture"]]["sport"]].append(s)
by_sport_match = defaultdict(list)
for m in L["matches"]: by_sport_match[m["sport"]].append(m)

tierA = sorted([s for s in SEL if s["tier"] == "A"], key=lambda x: -x["prob"])
tierB = best_per_fixture([s for s in SEL if s["tier"] == "B"])[:12]
tierC = best_per_fixture([s for s in SEL if s["tier"] == "C" and s["in_band"]])[:15]
priced = [m for m in L["matches"] if m["priced"]]

# ----- index -----
cards = "".join([
    f"<div class='card'><b>{len(L['matches'])}</b>fixtures published<br><small>{len(priced)} priced · {len(L['matches'])-len(priced)} listed without a price (see Flagged)</small></div>",
    f"<div class='card'><b>{len(SEL)}</b>selections originated<br><small>match winner, handicap and totals markets</small></div>",
    f"<div class='card'><b>{len(tierA)}</b>Tier A picks<br><small>above 70% and priced −250 or bigger</small></div>",
    f"<div class='card'><b>{len(P)}</b>written previews<br><small>min {min(p['words'] for p in P)} words, each naming its selection</small></div>",
    f"<div class='card'><b>{len(F)}</b>flags for review<br><small>nothing hidden — every gap is listed</small></div>",
    f"<div class='card'><b>{len(SRC)}</b>official sources<br><small>every table row links to one</small></div>"])
sport_cards = ""
for sp in SPORTS:
    ms = by_sport_match.get(sp, [])
    npriced = sum(1 for m in ms if m["priced"])
    top = best_per_fixture(by_sport_sel.get(sp, []))[:1]
    top_txt = (f"<br><small>Top: {e(top[0]['selection'])} ({e(top[0]['market'])}) {top[0]['prob']*100:.1f}% at {fmt_am(top[0]['american'])}</small>" if top else "<br><small>No price originated — see flag on the sport page.</small>")
    sport_cards += f"<div class='sport'><a href='sports/{SLUG[sp]}.html'>{sp}</a><br>{len(ms)} fixtures · {npriced} priced{top_txt}</div>"

idx = (f"<h1>Executive summary — 23 October 2026</h1>"
       f"<p>Today's desk covers the fifteen requested OLBG sports using only fixtures read first-hand today on official league and federation pages. "
       f"Prices are our own fair prices, built from published goals, runs, points, rankings and results — never from OLBG tip percentages or bookmaker odds. "
       f"Where an official page would not give up readable data, the fixture is still listed, the price cell stays empty and the reason appears on the "
       f"<a href='flagged.html'>Flagged for Review</a> page.</p>"
       f"<div class='note ok'><b>The two headline rules, honestly reconciled.</b> A fair price of −250 is a 71.43% chance, so &lsquo;above 70%&rsquo; and "
       f"&lsquo;−250 or bigger&rsquo; can both be true only between 70.00% and 71.43%. Those rare cases are <b>Tier A</b> ({len(tierA)} today). "
       f"Selections above 70% at shorter prices are <b>Tier B</b>; the strongest remaining in-band chances are <b>Tier C</b>. Every row carries its tier and an in-band marker.</div>"
       f"<div class='cards'>{cards}</div>"
       f"<h2>Tier A — highest-confidence picks inside the −250 to +10000 band</h2>{sel_rows(tierA)}"
       f"<h2>Strongest in-band chances below 70% (Tier C)</h2>{sel_rows(tierC[:10])}"
       f"<h2>Above 70% but shorter than −250 (Tier B, best per fixture)</h2><p><small>Shown for completeness; these sit outside the requested price band.</small></p>{sel_rows(tierB[:8])}"
       f"<h2>The fifteen sports</h2><div class='sportgrid'>{sport_cards}</div>"
       f"<h2>Best of the previews</h2><p>Full set of {len(P)} written previews: <a href='previews.html'>previews page</a>.</p>")
(OUT / "assets").mkdir(parents=True, exist_ok=True)
(OUT / "assets/style.css").write_text(CSS)
(OUT / "index.html").write_text(page("Dashboard", idx))

# ----- picks -----
pk = (f"<h1>Top picks</h1><p>Confidence labels follow the originated chance (High from 70%, Medium from 60%), with caps where samples are tiny. "
      f"Band = our fair American price between −250 and +10000.</p>"
      f"<h2>Tier A — above 70% and in band</h2>{sel_rows(tierA) if tierA else '<p>None today.</p>'}"
      f"<h2>Tier B — above 70%, shorter than −250 (best per fixture)</h2>{sel_rows(tierB)}"
      f"<h2>Tier C — strongest in-band chances (best per fixture)</h2>{sel_rows(tierC)}")
for sp in SPORTS:
    top5 = best_per_fixture(by_sport_sel.get(sp, []))[:5]
    pk += f"<h2>{sp} — top {len(top5)} by chance (target: five)</h2>"
    pk += sel_rows(top5) if top5 else "<p><small>No priced selections in this sport today — see its sport page and the Flagged page for the official-source reason.</small></p>"
(OUT / "picks.html").write_text(page("Top picks", pk))

# ----- previews -----
pv = f"<h1>Written previews ({len(P)})</h1><p>Each preview names its selection in plain language and uses only facts published on the official pages linked under it. No official injury list was readable today, so no preview claims one (flag LG-INJ1).</p>"
for p in P:
    pv += (f"<article class='preview' id='{p['fixture']}'><h3>{e(p['selection'])} — {e(p['market'])}</h3>"
           f"<p><small>{e(p['sport'])} · {e(p['competition'])} · {e(p['date'])} · {e(p['event'])} · "
           f"<span class='pill {p['confidence']}'>{p['confidence']}</span> <span class='pill {p['tier']}'>Tier {p['tier']}</span> · "
           f"chance {p['prob']*100:.1f}% · our fair price {fmt_am(p['american'])} ({p['decimal']}) · {'in band' if p['in_band'] else 'outside band'} · {p['words']} words</small></p>"
           f"<p>{e(p['text'])}</p><p><small>Sources: {source_links(p['source_keys'])}</small></p></article>")
(OUT / "previews.html").write_text(page("Previews", pv))

# ----- matches -----
def match_rows(ms):
    tr = ""
    for m in ms:
        ss = [s for s in SEL if s["fixture"] == m["id"]]
        best = max(ss, key=lambda x: x["prob"]) if ss else None
        ev = f'{m["away"]} at {m["home"]}' if m.get("away") else m["home"]
        best_txt = (f"<b>{e(best['selection'])}</b> ({e(best['market'])}) {best['prob']*100:.1f}% at {fmt_am(best['american'])}" if best
                    else e(m.get("blank_reason", "—")))
        tr += (f"<tr><td>{e(m['sport'])}</td><td>{e(m['date'])}<br><small>{e(m['start'])}</small></td><td>{e(ev)}<br><small>{e(m['competition'])}</small></td>"
               f"<td>{e(m['venue'] or '—')}</td><td>{e(m['status'])}</td><td>{'Yes' if m['priced'] else 'No'}</td><td>{best_txt}</td>"
               f"<td>{e(m.get('context', ''))}<br><small>{e(m.get('inputs', ''))}</small></td><td>{source_links(m['source_keys'])}</td></tr>")
    return ("<table><tr><th>Sport</th><th>Date / start</th><th>Event</th><th>Venue</th><th>Status</th><th>Priced</th>"
            "<th>Strongest selection (or why blank)</th><th>Published facts behind it</th><th>Official source</th></tr>" + tr + "</table>")

mh = f"<h1>All matches ({len(L['matches'])})</h1><p>Every fixture read on an official page today, including completed, in-play and participant-to-be-confirmed rows that are deliberately left unpriced.</p>" + match_rows(L["matches"])
(OUT / "matches.html").write_text(page("All matches", mh))

# ----- lines -----
ln = f"<h1>All originated lines ({len(SEL)})</h1><p>Every market priced for every priced fixture: match winner, handicap and totals, plus outrights for golf and Formula 1. Market menu follows the guides read on OLBG (Money Line, Puck Line/Handicap, Totals, outright winner).</p>"
for m in L["matches"]:
    ss = [s for s in SEL if s["fixture"] == m["id"]]
    if not ss: continue
    ev = f'{m["away"]} at {m["home"]}' if m.get("away") else m["home"]
    ln += f"<h3>{e(m['sport'])} — {e(ev)} <small>({e(m['date'])}, {e(m['competition'])})</small></h3>" + sel_rows(sorted(ss, key=lambda x: (x["market"], -x["prob"])), with_fixture=False)
(OUT / "lines.html").write_text(page("All lines", ln))

# ----- sport pages -----
(OUT / "sports").mkdir(exist_ok=True)
sindex = "<h1>Sports</h1><div class='sportgrid'>" + "".join(
    f"<div class='sport'><a href='{SLUG[s]}.html'>{s}</a><br>{len(by_sport_match.get(s, []))} fixtures</div>" for s in SPORTS) + "</div>"
(OUT / "sports/index.html").write_text(page("Sports", sindex, depth=1))
for sp in SPORTS:
    ms = by_sport_match.get(sp, [])
    top5 = best_per_fixture(by_sport_sel.get(sp, []))[:5]
    pvs = [p for p in P if p["sport"] == sp]
    flag_rows = [f for f in F if sp.split()[0].lower() in f["area"].lower() or f["area"] == sp]
    body = f"<h1>{sp}</h1><p>{len(ms)} fixtures published, {sum(1 for m in ms if m['priced'])} priced, {len(pvs)} written previews.</p>"
    if ms:
        body += "<h2>Fixtures</h2>" + match_rows(ms)
    else:
        att = "".join("<tr><td>" + e(s["name"]) + "</td><td>" + e(s["used_for"]) + "</td><td><a href='" + e(s["url"]) + "'>" + e(s["url"]) + "</a></td></tr>" for s in SRC.values() if s["sport"] == sp)
        body += "<h2>Fixtures</h2><p><small>No fixtures could be read on an official page today. Attempts made first-hand:</small></p><table><tr><th>Official page attempted</th><th>Outcome</th><th>Link</th></tr>" + att + "</table>" 
    body += f"<h2>Top {len(top5)} picks (best selection per fixture)</h2>" + (sel_rows(top5, with_fixture=False) if top5 else "<p><small>None.</small></p>")
    if pvs:
        body += "<h2>Previews</h2>"
        for p in pvs:
            body += f"<article class='preview'><h3>{e(p['selection'])} — {e(p['market'])}</h3><p>{e(p['text'])}</p><p><small>Chance {p['prob']*100:.1f}% · {fmt_am(p['american'])} · Tier {p['tier']} · Sources: {source_links(p['source_keys'])}</small></p></article>"
    if flag_rows:
        body += "<h2>Flags for this sport</h2>" + "".join(f"<p><b>{f['id']}</b> — {e(f['detail'])}<br><small>{source_links(f['source_keys'])}</small></p>" for f in flag_rows)
    (OUT / f"sports/{SLUG[sp]}.html").write_text(page(sp, body, depth=1))

# ----- flagged -----
fr = "".join(f"<tr><td><b>{f['id']}</b></td><td>{e(f['area'])}</td><td>{e(f['detail'])}</td><td>{source_links(f['source_keys'])}</td></tr>" for f in F)
(OUT / "flagged.html").write_text(page("Flagged for Review",
    f"<h1>Flagged for Review ({len(F)})</h1><p>Everything that could not be confirmed from an official page today, plus methodological caveats and one repository defect. "
    f"Flagged items never block publication; they are published empty or labelled, never estimated silently.</p>"
    f"<table><tr><th>ID</th><th>Area</th><th>What is wrong / missing</th><th>Source links for manual review</th></tr>{fr}</table>"))

# ----- sources -----
sr = "".join(f"<tr><td>{e(s['name'])}</td><td>{e(s['sport'])}</td><td>{e(s['used_for'])}</td><td><a href='{e(s['url'])}'>{e(s['url'])}</a></td></tr>" for s in SRC.values())
(OUT / "sources.html").write_text(page("Sources",
    f"<h1>Sources ({len(SRC)})</h1><p>All read first-hand on 23 October 2026. Failed attempts are listed alongside successes and marked (attempt).</p>"
    f"<table><tr><th>Source</th><th>Area</th><th>Used for</th><th>Link</th></tr>{sr}</table>"))

# ----- method -----
bl = L["meta"]["league_baselines"]
method = f"""<h1>Method — how our own lines are originated</h1>
<div class='note'><b>Plain-English version.</b> We read the official fixture list, then the official scoring records behind it. A team's expected score blends what it scores with what tonight's opponent concedes, measured against the league average. Those expectations become chances for the match winner, the handicap and the total, and each chance converts to a fair price. If the scoring record cannot be read, we do not price the game.</div>
<h2>Scoring expectations</h2>
<table><tr><th>League</th><th>Baseline read today</th><th>Expected score</th><th>Markets from it</th></tr>
<tr><td>NHL</td><td>{bl['nhl_gpg']} goals per team per game (31 complete teams, NHL Stats API)</td><td>(team GF rate × opponent GA rate ÷ baseline), home side ×1.06</td><td>Money line 2-way (drawn regulation split evenly as an overtime proxy), puck line ±1.5, totals 5.5 and 6.5 — independent Poisson grid</td></tr>
<tr><td>MLB World Series</td><td>{bl['mlb_runs_two_team']} runs per team per game (finalists' own runs scored)</td><td>Same structure, home ×1.03</td><td>Money line, run line ±1.5, totals 7.5 and 8.5 — Poisson grid. Probable pitchers were not in the feeds read (LG-ML1)</td></tr>
<tr><td>EuroLeague</td><td>{bl['euroleague_ppg']} points per team per game</td><td>(PF rate × opponent PA rate ÷ baseline), home ×1.02</td><td>Match winner, handicap set at the expected margin, total set at the expected total — Normal curves with stated SDs (margin 13, total 18)</td></tr>
<tr><td>RLWC</td><td>{bl['rlwc_mean_pts']} points per team per game over 6 tournament games</td><td>Same structure after adding two phantom average games to every nation (one and two-game samples)</td><td>Winner, ±12.5 handicap, total 44.5 — Normal curves, wide stated SDs (16 and 19), confidence capped at Medium</td></tr>
<tr><td>Snooker</td><td>World ranking money (official WST list)</td><td>Log-strength on ranking money; players below 36th use the 36th-place £198,500 as a ceiling</td><td>Match winner only (formats were not published on the pages read), bounded prices labelled, capped at Medium</td></tr>
<tr><td>Golf / F1 outrights</td><td>36-hole leaderboard; championship points</td><td>Share weights on strokes deficit / points share</td><td>Outright winner only, always Low confidence, upper-bound caveat on the golf page</td></tr>
<tr><td>Handball</td><td>One official same-pairing result from 23 Oct</td><td>That result regressed halfway toward 28–28</td><td>Winner, ±4.5, total 54.5 — stated SDs 6.5 / 8.5, always Low confidence</td></tr></table>
<h2>Confidence and the price band</h2>
<p>High = chance of 70% or more; Medium = 60% or more; Low = below 60%, before the caps noted above. The requested band runs from −250 to +10000 in American odds. Because −250 equals 71.43%, a pick can be both &lsquo;above 70%&rsquo; and in band only between 70.00% and 71.43%: Tier A. Higher chances at shorter prices are Tier B; other in-band picks are Tier C.</p>
<h2>What we never do</h2>
<p>No OLBG tip percentage, bookmaker price or search-result snippet enters a price. A value an official page did not publish in readable form is left blank and flagged, never interpolated. In-play and completed matches are listed for the record and never priced.</p>"""
(OUT / "method.html").write_text(page("Method", method))

# ----- OLBG map -----
ob = IN["olbg"]
rows = "".join(f"<tr><td>{e(n)}</td><td><a href='https://www.olbg.com/betting-tips/{e(sl)}/{i}'>/betting-tips/{e(sl)}/{i}</a></td><td>{i}</td><td><a href='sports/{SLUG[n.split(' (')[0]]}.html'>Ledger page</a></td></tr>"
               for (n, sl, i) in ob["sport_ids"])
(OUT / "olbg.html").write_text(page("OLBG map",
    f"<h1>OLBG, mapped</h1><p>How the source site is organised, read first-hand on 23 October 2026 from its betting-tips index, two sport hubs and its sitemap.</p>"
    f"<h2>URL scheme</h2><p>{e(ob['url_schema'])}</p><p>{e(ob['hub_note'])}</p>"
    f"<h2>Markets named in OLBG's own guides</h2><p>{e(ob['markets_read'])}</p>"
    f"<h2>The fifteen requested sports on OLBG</h2><table><tr><th>Sport (brief wording)</th><th>OLBG hub</th><th>OLBG sport ID</th><th>This desk</th></tr>{rows}</table>"
    f"<p><small>OLBG also lists sports outside this brief (for example Football 1, Horse Racing 2, American Football 11, Boxing 16, Cycling 17, Hurling 26), which this desk does not cover.</small></p>"))

# ----- verification -----
unpriced = [m for m in L["matches"] if not m["priced"]]
vf = (f"<h1>Verification</h1><p>Rebuild: <code>python3 scripts/ledger_model.py &amp;&amp; python3 scripts/ledger_predictions.py &amp;&amp; python3 scripts/ledger_build.py &amp;&amp; python3 scripts/ledger_verify.py</code>. "
      f"Inputs in <code>data/ledger/inputs.json</code> are hand transcriptions of the official pages in <code>data/ledger/sources.json</code>, each read on 2026-10-23.</p>"
      f"<table><tr><th>Check</th><th>Result</th></tr>"
      f"<tr><td>Fixtures published / priced / deliberately unpriced</td><td>{len(L['matches'])} / {len(priced)} / {len(unpriced)}</td></tr>"
      f"<tr><td>Selections originated</td><td>{len(SEL)} (Tier A {sum(1 for s in SEL if s['tier']=='A')}, Tier B {sum(1 for s in SEL if s['tier']=='B')}, Tier C {sum(1 for s in SEL if s['tier']=='C')})</td></tr>"
      f"<tr><td>Written previews / minimum length</td><td>{len(P)} / {min(p['words'] for p in P)} words</td></tr>"
      f"<tr><td>Sports with at least one fixture</td><td>{len([s for s in SPORTS if by_sport_match.get(s)])} of 15 (Rugby Union, Darts, Volleyball and Greyhounds returned no readable fixtures — flagged)</td></tr>"
      f"<tr><td>Every published row carries an official source link</td><td>Enforced by scripts/ledger_verify.py and tests/test_ledger_21a0c524.py</td></tr></table>"
      f"<h2>Unpriced fixtures and the exact reason ({len(unpriced)})</h2>" + match_rows(unpriced))
(OUT / "verification.html").write_text(page("Verification", vf))
print(f"built {len(list(OUT.rglob('*.html')))} pages")
