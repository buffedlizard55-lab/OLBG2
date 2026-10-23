"""Build /focus/ static pages from data/focus/*.json. Deterministic."""
import html, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "focus"; OUT = ROOT / "focus"
INP = json.loads((DATA / "inputs.json").read_text()); LABELS = INP["labels"]; SPORTS = INP["sports"]
M = json.loads((DATA / "matches.json").read_text())["matches"]
PRED = json.loads((DATA / "predictions.json").read_text())["predictions"]
FLAGS = json.loads((DATA / "flagged.json").read_text())["flags"]
LINES = json.loads((DATA / "lines.json").read_text())["rows"]
def e(x): return html.escape(str(x))
def badge(c): return f'<span class="badge {e(c)}">{e(c)}</span>'
def src(url): return f'<a href="{e(url)}" rel="noopener">{e(url.split("/")[2])}</a>' if url else "—"
def amer(a): return f"+{a}" if a > 0 else str(a)
NAV = [("index.html","Summary"),("matches.html","All matches"),("top5.html","Top 5 per sport"),("predictions.html","Predictions"),("flagged.html","Flagged for Review"),("sources.html","Sources"),("methodology.html","Methodology"),("sports/index.html","Sports")]
def page(title, body, cur="", depth=0):
    pref = "../" * depth
    nav = "".join('<a href="%s%s"%s>%s</a>' % (pref, h, ' aria-current="page"' if h == cur else '', n) for h, n in NAV)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · OLBG2 Focus</title><link rel="stylesheet" href="{pref}../assets/style.css"></head><body>
<header class="topbar"><div class="wrap bar"><a class="brand" href="{pref}index.html"><span class="dot"></span>OLBG2 <span class="brand-sub">focus desk · 15 sports</span></a><nav class="nav">{nav}</nav></div></header>
<div class="stripe"><div class="wrap">Captured 2026-10-23 · Prices are our own fair prices (decimal = 1/p), not bookmaker odds · High = p ≥ 70% and fair American −250…+10000 · Blank = no official numeric input, never estimated</div></div>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap"><p class="sub">Research only, not betting advice. Every row links its official source. Unverified values are blank and listed on <a href="{pref}flagged.html">Flagged for Review</a>.</p></div></footer></body></html>"""
def prices_cell(m):
    if not m["prices"]: return '<span class="blank">— blank (see Flagged)</span>'
    parts=[]
    for p in m["prices"][:6]: parts.append(f"<div><b>{e(p['market'])}</b> {e(p['selection'])} · {round(p['p']*100,1)}% · {p['decimal']} ({amer(p['american'])}){' ★' if p.get('in_band') else ''}</div>")
    return "".join(parts)
def best_pick(m):
    if m["in_band"]:
        b=max(m["in_band"], key=lambda x:x["p"]); return f"{e(b['selection'])} ({e(b['market'])})", b
    ws=[p for p in m["prices"] if p["market"] in ("match winner","outright winner")]
    if ws:
        b=max(ws, key=lambda x:x["p"]); return f"{e(b['selection'])} ({e(b['market'])})", b
    return "—", None

def main():
    OUT.mkdir(exist_ok=True); (OUT/"sports").mkdir(exist_ok=True)
    highs=[m for m in M if m["in_band"]]; priced=[m for m in M if m["prices"]]
    # index
    kpis=f"""<div class="kpis">
    <div class="kpi"><div class="v">{len(M)}</div><div class="k">fixtures / events</div><div class="s">across 15 sports</div></div>
    <div class="kpi"><div class="v">{len(priced)}</div><div class="k">with originated lines</div><div class="s">{len(M)-len(priced)} blank, flagged</div></div>
    <div class="kpi"><div class="v">{len(LINES)}</div><div class="k">originated prices</div><div class="s">winner · handicap · total where inputs allow</div></div>
    <div class="kpi"><div class="v">{sum(len(m['in_band']) for m in M)}</div><div class="k">in-band high selections</div><div class="s">p ≥70%, −250…+10000</div></div>
    <div class="kpi"><div class="v">{len(PRED)}</div><div class="k">written predictions</div><div class="s">≥30 words, high picks only</div></div>
    <div class="kpi"><div class="v">{len(FLAGS)}</div><div class="k">review items</div><div class="s">published, non-blocking</div></div></div>"""
    cards="".join(f'<a class="card" href="sports/{s}.html"><h3>{e(LABELS[s])}</h3><p>{len([m for m in M if m["sport"]==s])} fixture(s) · {len([m for m in M if m["sport"]==s and m["in_band"]])} with high selection(s) · {len([p for p in PRED if p["sport"]==s])} prediction(s)</p></a>' for s in SPORTS)
    exec_rows=""
    for p in sorted(PRED, key=lambda x:-x["p"]):
        exec_rows+=f'<tr><td>{e(LABELS[p["sport"]])}</td><td>{e(p["home"])} v {e(p["away"])}</td><td><b>{e(p["selection"])}</b></td><td>{round(p["p"]*100,1)}% · {p["decimal"]} ({amer(p["american"])})</td><td>{badge("high")}</td><td>{src(p["source_url"])}</td></tr>'
    body=f"""<p class="eyebrow">Executive summary · 2026-10-23</p><h1>15-sport focus desk</h1>
<p class="lede">OLBG lists far more than these fifteen sports; this desk covers only Golf, Volleyball, Rugby Union, Cricket, Snooker, Darts, Baseball, Gaelic Sports, Greyhounds, Tennis, Motor Racing, Handball, Ice Hockey, Basketball and Rugby League. Fixtures were checked against governing-body sources, lines were originated here from official strength inputs, and every pick is graded low, medium or high. High means at least a 70% assessed chance with a fair price between −250 and +10000.</p>
{kpis}
<h2>Highest-confidence picks (today &amp; upcoming)</h2><div class="tablewrap"><table><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th>Fair price</th><th>Confidence</th><th>Official source</th></tr></thead><tbody>{exec_rows or '<tr><td colspan="6">No high pick cleared the gate.</td></tr>'}</tbody></table></div>
<p class="sub">Only {len(PRED)} written predictions cleared the strict gate, in {len(set(p['sport'] for p in PRED))} sports. The five-per-sport aim is <a href="flagged.html">flagged per sport</a> where it was not met — no filler prices were created.</p>
<h2>By sport</h2><div class="grid sports">{cards}</div>
<h2>How to read this desk</h2><p>★ marks an in-band high selection. Prices are fair prices from our own calculations (see <a href="methodology.html">Methodology</a>), never copied bookmaker odds. Where an official numeric input could not be captured, the price cell is blank and the reason is on the Flagged page.</p>"""
    (OUT/"index.html").write_text(page("Executive summary", body, "index.html"))
    # matches
    rows=""
    for m in sorted(M, key=lambda x:(x["start_utc"] or "9999", LABELS[x["sport"]])):
        pick,b = best_pick(m)
        rows+=f'<tr><td class="nowrap">{e(m["start_utc"][:10] if m["start_utc"] else "—")}</td><td><a href="sports/{m["sport"]}.html">{e(LABELS[m["sport"]])}</a><div class="tiny">{e(m["competition"])}</div></td><td><div class="teams">{e(m["home"])} <span>v</span> {e(m["away"])}</div><div class="tiny">{e(m["facts"])}</div></td><td>{prices_cell(m)}</td><td><div class="pick">{pick}</div>{badge(m["confidence"])}</td><td>{src(m["source_url"])}<div class="tiny">official</div></td></tr>'
    (OUT/"matches.html").write_text(page("All matches", f'<h1>All matches</h1><p class="sub">{len(M)} rows · every row carries an official source link</p><div class="tablewrap"><table><thead><tr><th>Date (UTC)</th><th>Sport</th><th>Match &amp; form notes</th><th>Originated lines</th><th>Pick &amp; confidence</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>', "matches.html"))
    # top5
    trows=""
    for s in SPORTS:
        ms=[m for m in M if m["sport"]==s and m["prices"]]
        ms=sorted(ms, key=lambda m:-(max([x["p"] for x in m["in_band"]] or [x["p"] for x in m["prices"] if x["market"]=="match winner"] or [0])))[:5]
        if not ms: trows+=f'<tr><td>{e(LABELS[s])}</td><td colspan="4">No priced fixture captured — see Flagged for Review</td></tr>'; continue
        for m in ms:
            pick,b=best_pick(m)
            trows+=f'<tr><td>{e(LABELS[s])}</td><td>{e(m["home"])} v {e(m["away"])}</td><td><b>{pick}</b></td><td>{round(b["p"]*100,1) if b else "—"}% · {b["decimal"] if b else "—"}</td><td>{badge(m["confidence"])}</td></tr>'
    (OUT/"top5.html").write_text(page("Top 5 per sport", f'<h1>Top five per sport</h1><p class="sub">Highest-confidence selection per fixture, five fixtures per sport where five priced fixtures exist. Shortfalls are flagged, not padded.</p><div class="tablewrap"><table><thead><tr><th>Sport</th><th>Match</th><th>Selection</th><th>Fair price</th><th>Confidence</th></tr></thead><tbody>{trows}</tbody></table></div>', "top5.html"))
    # predictions
    prows="".join(f'<div class="panel"><h3>{e(LABELS[p["sport"]])} — {e(p["home"])} v {e(p["away"])}</h3><p><b>{e(p["selection"])}</b> · {round(p["p"]*100,1)}% · {p["decimal"]} ({amer(p["american"])}) {badge("high")}</p><p>{e(p["text"])}</p><p class="tiny">{p["words"]} words · Source: {src(p["source_url"])}</p></div>' for p in PRED)
    (OUT/"predictions.html").write_text(page("Predictions", f'<h1>High-confidence predictions</h1><p class="sub">{len(PRED)} unique write-ups, each at least 30 words, each naming the selection plainly.</p>{prows or "<p>None cleared the gate.</p>"}', "predictions.html"))
    # flagged
    frows="".join(f'<tr><td>{e(f["id"])}</td><td>{e(LABELS.get(f["sport"], f["sport"]))}</td><td>{e(f["kind"])}</td><td>{e(f["text"])}</td><td>{src(f["source"])}</td></tr>' for f in FLAGS)
    (OUT/"flagged.html").write_text(page("Flagged for Review", f'<h1>Flagged for Review</h1><p class="sub">{len(FLAGS)} items · none blocks publication · each links the source that raised it</p><div class="tablewrap"><table><thead><tr><th>ID</th><th>Sport</th><th>Kind</th><th>Detail</th><th>Source</th></tr></thead><tbody>{frows}</tbody></table></div>', "flagged.html"))
    # sources
    srows="".join(f'<tr><td>{e(LABELS[m["sport"]])}</td><td>{e(m["home"])} v {e(m["away"])}</td><td>{src(m["source_url"])}<div class="tiny">{e(m["source_url"])}</div></td><td>{e(m["basis"])}</td></tr>' for m in M)
    (OUT/"sources.html").write_text(page("Sources", f'<h1>Official sources</h1><p class="sub">One official link per row. A competition-page link proves the competition, not every fixture detail — those rows are flagged.</p><div class="tablewrap"><table><thead><tr><th>Sport</th><th>Row</th><th>Official link</th><th>Input basis</th></tr></thead><tbody>{srows}</tbody></table></div>', "sources.html"))
    # methodology
    (OUT/"methodology.html").write_text(page("Methodology", """<h1>Methodology</h1>
<h2>Discovery &amp; confirmation</h2><p>OLBG's sport hubs (e.g. <a href="https://www.olbg.com/betting-tips/Ice_Hockey/13">olbg.com/betting-tips/Ice_Hockey/13</a>, re-read 2026-10-23) define the sport taxonomy and market labels (Money Line, Puck Line, Game Totals). OLBG publishes tipster selections, not prices, so no price here comes from OLBG. Each fixture is then checked on the governing body named in its source link.</p>
<h2>Line origination</h2><p>Poisson attack/defence for ice hockey, baseball and handball (rates shrunk toward the league average, home edge split ±half); normal margin/total for rugby union and basketball net-proxy winner-only; logistic strength-difference for volleyball and rugby league. Fair decimal = 1/p rounded to two places; American is derived from that rounded decimal. Handicap and total lines are half-point lines nearest the expected margin/total. Markets investigated per fixture: match winner, handicap and match total (outright only for Motor Racing).</p>
<h2>Confidence</h2><p><b>High:</b> p ≥ 0.7000 and fair American between −250 and +10000 inclusive (decimal 1.40–101.00). <b>Medium:</b> best winner price ≥ 60% without an in-band high. <b>Low:</b> otherwise. <b>Blank:</b> no official numeric input captured — price left empty and flagged.</p>
<h2>Limits</h2><p>Strength inputs for non-NHL/MLB rows come from the 2026-10-22 official capture referenced in each row's basis; NHL fixtures/records and the MLB World Series schedule were re-read on 2026-10-23. Injuries are included only where a governing-body page stated them; none were stated for these rows, so none are claimed. Five predictions per sport was the aim; the strict band (only 70.0–71.4% qualifies on a straight price) means most sports fall short — every shortfall is flagged.</p>""", "methodology.html"))
    # sport pages
    idx=""
    for s in SPORTS:
        ms=[m for m in M if m["sport"]==s]
        rows="".join(f'<tr><td>{e(m["start_utc"][:10] if m["start_utc"] else "—")}</td><td>{e(m["home"])} v {e(m["away"])}<div class="tiny">{e(m["competition"])} · {e(m["facts"])}</div></td><td>{prices_cell(m)}</td><td>{badge(m["confidence"])}</td><td>{src(m["source_url"])}</td></tr>' for m in ms) or '<tr><td colspan="5">No fixture captured in this snapshot.</td></tr>'
        preds="".join(f'<div class="panel"><h3>{e(p["home"])} v {e(p["away"])} — {e(p["selection"])}</h3><p>{e(p["text"])}</p></div>' for p in PRED if p["sport"]==s)
        (OUT/"sports"/f"{s}.html").write_text(page(LABELS[s], f'<p class="crumb"><a href="index.html">Sports</a> / {e(LABELS[s])}</p><h1>{e(LABELS[s])}</h1><div class="tablewrap"><table><thead><tr><th>Date</th><th>Match</th><th>Lines</th><th>Confidence</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>{preds}', "sports/index.html", depth=1))
        idx+=f'<a class="card" href="{s}.html"><h3>{e(LABELS[s])}</h3><p>{len(ms)} fixture(s)</p></a>'
    (OUT/"sports"/"index.html").write_text(page("Sports", f'<h1>Sports</h1><div class="grid sports">{idx}</div>', "sports/index.html", depth=1))
    print(f"focus_build: {2+6+len(SPORTS)+1} pages")

if __name__ == "__main__": main()
