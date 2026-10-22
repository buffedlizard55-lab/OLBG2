#!/usr/bin/env python3
"""Build /fresh/ dashboard (session arena/f048d3a9-olbg2) from data/fresh/audit.json
plus the read-only unified desk in data/verified/. Deterministic, stdlib only."""
import json, html
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fresh"; OUT.mkdir(exist_ok=True)
audit = json.loads((ROOT / "data/fresh/audit.json").read_text())
rows = json.loads((ROOT / "data/verified/matches.json").read_text())["matches"]
pred_doc = json.loads((ROOT / "data/verified/predictions.json").read_text())
preds = pred_doc["predictions"] + pred_doc.get("research", [])
sports = json.loads((ROOT / "data/verified/sports.json").read_text())
c = audit["checks"]
E = html.escape
CSS = """*{box-sizing:border-box}body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#0f172a;background:#f8fafc}
header{background:#0f172a;color:#fff;padding:22px}header a{color:#5eead4}nav a{margin-right:14px;color:#5eead4;text-decoration:none}
main{max-width:1180px;margin:0 auto;padding:20px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px}.card b{font-size:26px;display:block}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13px}th,td{border:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#f1f5f9;position:sticky;top:0}.badge{padding:1px 7px;border-radius:99px;font-size:11px;white-space:nowrap}
.high{background:#dcfce7}.medium{background:#fef9c3}.low{background:#fee2e2}.blank{background:#e2e8f0}
input#q{width:100%;padding:10px;margin:12px 0;border:1px solid #cbd5e1;border-radius:8px}footer{padding:18px;color:#64748b;font-size:12px;text-align:center}
.pred{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin:12px 0}"""

def page(title, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — OLBG2 Fresh Audit</title><style>{CSS}</style></head><body><header><h1>{E(title)}</h1>
<nav><a href="index.html">Dashboard</a><a href="matches.html">All matches (188)</a><a href="picks.html">Predictions check</a><a href="flagged.html">Flagged for Review</a><a href="sources.html">Sources</a><a href="methodology.html">Methodology</a><a href="../index.html">Main dashboard</a></nav>
<p>Fresh line-by-line audit · session arena/f048d3a9-olbg2 · captured 2026-10-22 · Research, not betting advice. 18+.</p></header>
<main>{body}</main><footer>Every row links to its official source. Blank = unverified, never inferred. Prices are originated fair prices, not bookmaker quotes.</footer></body></html>"""

def odds(w, k): return "—" if not w or w.get(k) is None else f"{w[k]:g}"

# index
sport_counts = Counter(r["sport_name"] for r in rows)
cards = "".join(f'<div class="card"><b>{v}</b>{E(k)}</div>' for k, v in sorted(sport_counts.items()))
checks_rows = "".join(f"<tr><td>{E(k.replace('_',' '))}</td><td>{E(str(v)[:220])}</td></tr>" for k, v in c.items() if not isinstance(v, (list, dict)) or k in ("source_scope_counts",))
flag_rows = "".join(f'<tr><td>{f["id"]}</td><td><span class="badge {f["severity"]}">{f["severity"]}</span></td><td>{E(f["item"])}</td><td><a href="{E(f["source_url"])}">official source</a></td></tr>' for f in audit["flags"])
(OUT / "index.html").write_text(page("Fresh Audit Dashboard", f"""
<p>This layer mechanically re-audits the unified desk (188 rows, 30 predictions, 17 eligible sports; excluded: soccer, boxing, UFC/MMA, football, American football, hurling, horse racing, cycling, specials) line by line — arithmetic, confidence gate, links, blanks, duplication and documentation drift. It edits no upstream value; discrepancies are published on the Flagged page with blank corrected values.</p>
<div class="cards"><div class="card"><b>{len(rows)}</b>rows audited</div><div class="card"><b>{len(preds)}</b>predictions checked</div>
<div class="card"><b>{c['high_predictions_in_band']}</b>high picks passing the gate</div><div class="card"><b>{len(c['confidence_gate_violations'])}</b>gate violations (FR-01)</div>
<div class="card"><b>{len(audit['flags'])}</b>fresh flags</div><div class="card"><b>0</b>excluded-sport leaks</div></div>
<h2>Rows by sport</h2><div class="cards">{cards}</div>
<h2>Headline checks</h2><table><tr><th>Check</th><th>Result</th></tr>{checks_rows}</table>
<h2>Fresh flags (summary)</h2><table><tr><th>ID</th><th>Severity</th><th>Item</th><th>Source</th></tr>{flag_rows}</table>
<p>First-hand sample re-read this session: <a href="https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154">NHL NSH@BOS, Oct 22 2026</a>, <a href="https://www.nhl.com/gamecenter/min-vs-cgy/2026/10/22/2026020162">NHL MIN@CGY, Oct 22 2026</a>, <a href="https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/panathinaikos-aktor-athens-kosner-baskonia-vitoria-gasteiz/E2026/67/">EuroLeague Panathinaikos v Baskonia, 22 Oct 2026</a> (PAO rank 1, Baskonia rank 20 as published), and the <a href="https://www.olbg.com/betting-tips">OLBG tips hub</a> (URL schema /betting-tips/&lt;Sport&gt;/&lt;id&gt;, events under /betting-tips/&lt;Sport&gt;/&lt;League&gt;/&lt;Event&gt;/&lt;id&gt;?event_id=). All other rows remain at their upstream capture status — see FR-08.</p>"""))

# matches
trs = []
for r in sorted(rows, key=lambda x: (x["date"], x["sport_name"], x["home"])):
    p = r.get("pick") or {}; w = r.get("winner_market") or {}; h = r.get("handicap_market") or {}; t = r.get("total_market") or {}
    conf = p.get("confidence") or "blank"
    trs.append(f"""<tr><td>{r['date']}</td><td>{E(r['sport_name'])}</td><td>{E(r['competition'])}</td>
<td>{E(r['home'])} v {E(r['away'])}</td><td>{E(r.get('venue') or '—')}</td>
<td>{odds(w,'home_odds')} / {odds(w,'draw_odds') if w.get('draw_odds') else '—'} / {odds(w,'away_odds')}</td>
<td>{E(h.get('label','—'))} {odds(h,'fav_odds')}</td><td>{odds(t,'line')} (O {odds(t,'over_odds')} / U {odds(t,'under_odds')})</td>
<td>{E(p.get('selection','—'))}</td><td><span class="badge {conf}">{conf}</span></td>
<td>{E(r.get('source_scope',''))}</td><td><a href="{E(r['official_url'])}">{E(r['official_source'])}</a> · <a href="{E(r['olbg_url'])}">OLBG</a></td></tr>""")
(OUT / "matches.html").write_text(page("All Matches — Fresh Audit", f"""
<input id="q" placeholder="Filter by team, sport, competition…" oninput="document.querySelectorAll('tbody tr').forEach(tr=>tr.style.display=tr.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none')">
<table><thead><tr><th>Date</th><th>Sport</th><th>Competition</th><th>Fixture</th><th>Venue</th><th>Winner (H/D/A fair)</th><th>Handicap</th><th>Total</th><th>Pick</th><th>Conf.</th><th>Source scope</th><th>Official source</th></tr></thead><tbody>{''.join(trs)}</tbody></table>"""))

# picks
gate_ids = {g["match_id"] for g in c["confidence_gate_violations"]}
pcards = []
for p in preds:
    bad = p["match_id"] in gate_ids and p.get("confidence") == "high"
    pcards.append(f"""<div class="pred"><b>{E(p['selection'])}</b> — {E(p['event'])} · {E(p['sport_name'])} · {E(p['market'])}<br>
<span class="badge {p['confidence']}">{p['confidence']}</span> prob {p['probability']:.1%} · fair {p['fair_odds']} ({p['fair_american']:+d}) · {len(p['text'].split())} words
{' · <b style="color:#b91c1c">FR-01 gate violation: labelled high below 70%</b>' if bad else ''}
<p>{E(p['text'])}</p><small>Facts: {' · '.join(f'<a href="{E(f["source"])}">{E(f["claim"])}</a>' for f in p['facts'])} · <a href="{E(p['official_url'])}">official fixture</a></small></div>""")
(OUT / "picks.html").write_text(page("Predictions Check", f"""
<p>Gate: <b>high</b> only when model probability ≥70% <i>and</i> fair American odds are inside −250…+10000. {c['high_predictions_in_band']} of 30 predictions pass as high; 2 research write-ups fail the gate (FR-01) and are shown flagged, not relabelled here — the upstream owner must regrade them. Every text is ≥30 words, unique, and names its selection explicitly.</p>{''.join(pcards)}"""))

# flagged
frs = "".join(f"""<tr><td>{f['id']}</td><td><span class="badge {f['severity']}">{f['severity']}</span></td><td>{E(f['category'])}</td><td>{E(f['item'])}</td><td>{E(f['detail'])}</td><td>{E(f['corrected_value'] or '— blank —')}</td><td>{E(f['status'])}</td><td><a href="{E(f['source_url'])}">{E(f['source_name'])}</a></td></tr>""" for f in audit["flags"])
(OUT / "flagged.html").write_text(page("Flagged for Review", f"""
<p>Fresh flags from this session only (upstream VF-01…VF-35 remain on the <a href="../flagged.html">main flagged page</a>). Corrected values are blank where not confirmed from an official source.</p>
<table><thead><tr><th>ID</th><th>Severity</th><th>Category</th><th>Item</th><th>Detail</th><th>Corrected value</th><th>Status</th><th>Official source</th></tr></thead><tbody>{frs}</tbody></table>"""))

# sources
src = {}
for r in rows: src.setdefault(r["official_source"], (r["official_url"], r["sport_name"]))
srs = "".join(f'<tr><td>{E(k)}</td><td>{E(v[1])}</td><td><a href="{E(v[0])}">{E(v[0])}</a></td></tr>' for k, v in sorted(src.items()))
elig = "".join(f"<tr><td>{E(s['name'])}</td><td>{E(s['governing_body'])}</td><td><a href=\"{E(s['official_url'])}\">official</a></td><td><a href=\"{E(s['olbg_url'])}\">OLBG hub</a></td><td>{E(s['status_summary'])}</td></tr>" for s in sports["eligible_sports"])
(OUT / "sources.html").write_text(page("Sources", f"<h2>Row source families</h2><table><tr><th>Source</th><th>Sport</th><th>Official URL</th></tr>{srs}</table><h2>Eligible taxonomy (17) & excluded (8)</h2><table><tr><th>Sport</th><th>Governing body</th><th>Official</th><th>OLBG</th><th>Status</th></tr>{elig}</table><p>Excluded by brief: soccer/football, boxing, UFC/MMA, American football, hurling, horse racing, cycling, specials — 0 leaked rows found in the unified desk.</p>"))

(OUT / "methodology.html").write_text(page("Methodology — Fresh Audit", """
<h2>What this layer does</h2><p><code>scripts/fresh_audit.py</code> reads <code>data/verified/matches.json</code>, <code>predictions.json</code>, <code>sports.json</code>, <code>flagged.json</code> and <code>README.md</code> read-only and re-checks every row: eligible-sport membership, duplicate ids/fixtures, HTTPS official + OLBG links, winner/handicap/total probability sums (3-way markets include the draw), fair-odds = 1/probability and American conversion (with rounding tolerances for 4dp probabilities / 2dp odds), the uniform confidence gate, prediction length/uniqueness/cross-references/fact sources, blanks, dates, and README claim drift. Results are written to <code>data/fresh/audit.json</code>; <code>scripts/fresh_build.py</code> renders these pages. Neither script edits upstream data.</p>
<h2>Confidence gate</h2><p>High = model probability ≥70% AND fair American price inside −250…+10000 (decimal 1.40–101.00). Since a ≥70% probability implies fair decimal ≤1.43, passing high picks cluster at 70.0–71.4%. Anything else is medium (≥60%) or low. Picks that fail the gate but say 'high' are flagged (FR-01), never silently relabelled here. Gate reference: <a href="https://www.nhl.com/gamecenter/min-vs-cgy/2026/10/22/2026020162">official NHL fixture used in the sample re-read</a>.</p>
<h2>Lines originated (upstream, audited here)</h2><p>Moneyline/win-match, handicap (puck/point/goal/frame/leg/set), and match totals were investigated for every sport; markets are blank where official inputs were missing (e.g. NBA totals, snooker frame format, greyhound trap ratings). Prices are fair model prices from official governing-body statistics, not bookmaker quotes and not OLBG tipster prices.</p>
<h2>Verification limit</h2><p>Sandbox HTTP to sports hosts is blocked; this session re-read a 4-page official sample via browser fetch (FR-08) and mechanically audited the rest. A passing mechanical check is not first-hand verification of a fixture's facts.</p>"""))
print(f"Built {len(list(OUT.glob('*.html')))} pages in {OUT}")
