#!/usr/bin/env python3
"""Final Desk Build — generate clean HTML dashboard"""
import json, os

SPORTS = ["ice-hockey", "basketball", "baseball", "tennis", "darts", "snooker",
    "rugby-union", "rugby-league", "handball", "volleyball", "cricket",
    "golf", "motor-racing", "esports", "aussie-rules", "gaelic-football", "greyhounds"]

SPORT_LABELS = {s: s.replace("-", " ").title() for s in SPORTS}

CSS = """
:root { --bg: #f8f9fa; --fg: #212529; --accent: #0d6efd; --success: #198754; --warn: #ffc107; --danger: #dc3545; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--fg); line-height: 1.6; }
.container { max-width: 1200px; margin: 0 auto; padding: 1rem; }
header { background: #fff; border-bottom: 2px solid var(--accent); padding: 1rem 0; margin-bottom: 2rem; }
header h1 { font-size: 1.5rem; }
nav { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 0.5rem; }
nav a { color: var(--accent); text-decoration: none; font-size: 0.9rem; }
nav a:hover { text-decoration: underline; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.kpi { background: #fff; padding: 1rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
.kpi .value { font-size: 2rem; font-weight: bold; color: var(--accent); }
.kpi .label { font-size: 0.85rem; color: #666; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }
th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #eee; font-size: 0.9rem; }
th { background: #f1f3f5; font-weight: 600; }
tr:hover { background: #f8f9fa; }
.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.badge-high { background: var(--success); color: #fff; }
.badge-medium { background: var(--warn); color: #000; }
.badge-low { background: #6c757d; color: #fff; }
.sport-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.sport-card { background: #fff; padding: 1rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.sport-card h3 { margin-bottom: 0.5rem; }
.sport-card a { color: var(--accent); }
.prediction { background: #fff; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid var(--success); }
.prediction h4 { margin-bottom: 0.5rem; }
.flag { background: #fff3cd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid var(--warn); }
a { color: var(--accent); }
footer { margin-top: 2rem; padding: 1rem 0; border-top: 1px solid #ddd; text-align: center; font-size: 0.85rem; color: #666; }
"""

def page(title, body, depth=0):
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — OLBG2 Final Desk</title><link rel="stylesheet" href="{prefix}assets/style.css"></head>
<body><div class="container">
<header><h1>OLBG2 — Final Desk</h1>
<nav><a href="{prefix}index.html">Dashboard</a><a href="{prefix}matches.html">All Matches</a>
<a href="{prefix}picks.html">Picks</a><a href="{prefix}predictions.html">Predictions</a>
<a href="{prefix}sports/index.html">By Sport</a><a href="{prefix}flagged.html">Flagged</a>
<a href="{prefix}sources.html">Sources</a><a href="{prefix}methodology.html">Methodology</a></nav></header>
{body}
<footer>Research, not betting advice. 18+. Data captured 2026-10-22 from official sources.</footer>
</div></body></html>"""

def build():
    with open("data/final-desk/matches.json") as f:
        data = json.load(f)
    with open("data/final-desk/predictions.json") as f:
        predictions = json.load(f)
    with open("data/final-desk/sources.json") as f:
        sources = json.load(f)
    matches = data["matches"]
    os.makedirs("final-desk/sports", exist_ok=True)
    os.makedirs("final-desk/assets", exist_ok=True)
    with open("final-desk/assets/style.css", "w") as f:
        f.write(CSS)
    # Index
    by_sport = {}
    for m in matches:
        by_sport.setdefault(m["sport"], []).append(m)
    high = sum(1 for m in matches if m["confidence"] == "high")
    med = sum(1 for m in matches if m["confidence"] == "medium")
    low = sum(1 for m in matches if m["confidence"] == "low")
    kpis = f"""<div class="kpi-grid">
<div class="kpi"><div class="value">{len(matches)}</div><div class="label">Total Matches</div></div>
<div class="kpi"><div class="value">{len(by_sport)}</div><div class="label">Sports Covered</div></div>
<div class="kpi"><div class="value">{high}</div><div class="label">High Confidence</div></div>
<div class="kpi"><div class="value">{med}</div><div class="label">Medium Confidence</div></div>
<div class="kpi"><div class="value">{len(predictions)}</div><div class="label">Predictions</div></div></div>"""
    sport_cards = '<div class="sport-grid">'
    for s in SPORTS:
        count = len(by_sport.get(s, []))
        sport_cards += f'<div class="sport-card"><h3>{SPORT_LABELS[s]}</h3><p>{count} matches</p><a href="sports/{s}.html">View →</a></div>'
    sport_cards += '</div>'
    with open("final-desk/index.html", "w") as f:
        f.write(page("Dashboard", f"<h2>Dashboard</h2>{kpis}<h2>Sports</h2>{sport_cards}"))
    # All matches
    rows = ""
    for m in matches:
        ml = m.get("markets", {}).get("moneyline", {})
        home_odd = ml.get("home", {}).get("decimal", "—")
        away_odd = ml.get("away", {}).get("decimal", "—")
        src = m.get("official_url", "")
        rows += f"""<tr><td>{m['sport']}</td><td>{m['competition']}</td><td>{m['away_team']} @ {m['home_team']}</td>
<td>{m['date'][:16]}</td><td>{home_odd}</td><td>{away_odd}</td><td>{m.get('pick','—')}</td>
<td><span class="badge badge-{m['confidence']}">{m['confidence']}</span></td>
<td><a href="{src}" target="_blank">Source</a></td></tr>"""
    with open("final-desk/matches.html", "w") as f:
        f.write(page("All Matches", f"""<h2>All Matches ({len(matches)})</h2>
<table><tr><th>Sport</th><th>Competition</th><th>Match</th><th>Date</th><th>Home</th><th>Away</th><th>Pick</th><th>Confidence</th><th>Source</th></tr>{rows}</table>"""))
    # Picks
    pick_rows = ""
    for m in matches:
        if m["confidence"] in ("high", "medium"):
            odds = m.get("fair_odds", {})
            pick_rows += f"""<tr><td>{m['sport']}</td><td>{m['away_team']} @ {m['home_team']}</td>
<td>{m.get('pick','—')}</td><td>{odds.get('decimal','—')}</td><td>{odds.get('american','—')}</td>
<td><span class="badge badge-{m['confidence']}">{m['confidence']}</span></td></tr>"""
    with open("final-desk/picks.html", "w") as f:
        f.write(page("Picks", f"""<h2>High & Medium Confidence Picks</h2>
<table><tr><th>Sport</th><th>Match</th><th>Pick</th><th>Fair Decimal</th><th>Fair American</th><th>Confidence</th></tr>{pick_rows}</table>"""))
    # Predictions
    pred_html = ""
    for p in predictions:
        pred_html += f'<div class="prediction"><h4>{p["pick"]} — {p["market"]}</h4><p>{p["text"]}</p><small>{p["word_count"]} words</small></div>'
    with open("final-desk/predictions.html", "w") as f:
        f.write(page("Predictions", f"<h2>High-Confidence Predictions ({len(predictions)})</h2>{pred_html or '<p>No high-confidence predictions in the current window.</p>'}"))
    # Sport pages
    sport_index = '<h2>Sports</h2><div class="sport-grid">'
    for s in SPORTS:
        sport_index += f'<div class="sport-card"><h3>{SPORT_LABELS[s]}</h3><p>{len(by_sport.get(s, []))} matches</p><a href="{s}.html">View →</a></div>'
    sport_index += '</div>'
    with open("final-desk/sports/index.html", "w") as f:
        f.write(page("Sports", sport_index, depth=1))
    for s in SPORTS:
        sport_matches = by_sport.get(s, [])
        rows = ""
        for m in sport_matches:
            ml = m.get("markets", {}).get("moneyline", {})
            rows += f"""<tr><td>{m['competition']}</td><td>{m['away_team']} @ {m['home_team']}</td>
<td>{m['date'][:16]}</td><td>{ml.get('home',{}).get('decimal','—')}</td><td>{ml.get('away',{}).get('decimal','—')}</td>
<td>{m.get('pick','—')}</td><td><span class="badge badge-{m['confidence']}">{m['confidence']}</span></td>
<td><a href="{m.get('official_url','')}" target="_blank">Source</a></td></tr>"""
        body = f"<h2>{SPORT_LABELS[s]} ({len(sport_matches)} matches)</h2>"
        if sport_matches:
            body += f'<table><tr><th>Competition</th><th>Match</th><th>Date</th><th>Home</th><th>Away</th><th>Pick</th><th>Confidence</th><th>Source</th></tr>{rows}</table>'
        else:
            body += '<p>No fixtures captured for this sport in the current window.</p>'
        with open(f"final-desk/sports/{s}.html", "w") as f:
            f.write(page(SPORT_LABELS[s], body, depth=1))
    # Flagged
    flags = [
        {"id": "FD-01", "text": "NBA team stats not available from official source; basketball lines use baseline home advantage only", "source": "https://www.nba.com/stats"},
        {"id": "FD-02", "text": "Tennis draws not fully captured from ATP/WTA; rankings page is client-rendered", "source": "https://www.atptour.com/en/rankings/singles"},
        {"id": "FD-03", "text": "10 sports have zero fixtures in this capture window: darts, snooker, rugby-union, rugby-league, handball, volleyball, cricket, golf, motor-racing, esports, aussie-rules, gaelic-football, greyhounds", "source": "https://www.olbg.com/betting-tips"}
    ]
    flag_html = ""
    for fl in flags:
        flag_html += f'<div class="flag"><strong>{fl["id"]}</strong>: {fl["text"]} <a href="{fl["source"]}" target="_blank">[Source]</a></div>'
    with open("final-desk/flagged.html", "w") as f:
        f.write(page("Flagged for Review", f"<h2>Flagged for Review ({len(flags)})</h2>{flag_html}"))
    # Sources
    src_rows = ""
    for k, v in sources.items():
        src_rows += f'<tr><td>{k}</td><td>{v["type"]}</td><td>{v["sport"]}</td><td><a href="{v["url"]}" target="_blank">{v["url"][:60]}...</a></td></tr>'
    with open("final-desk/sources.html", "w") as f:
        f.write(page("Sources", f"""<h2>Sources ({len(sources)})</h2>
<table><tr><th>ID</th><th>Type</th><th>Sport</th><th>URL</th></tr>{src_rows}</table>"""))
    # Methodology
    with open("final-desk/methodology.html", "w") as f:
        f.write(page("Methodology", """<h2>Methodology</h2>
<h3>Line Origination</h3><p>Lines are originated from official governing-body statistics using Poisson models (NHL) or baseline home-advantage models (NBA, MLB). No bookmaker prices are read or used.</p>
<h3>Confidence Grading</h3><p><strong>High:</strong> model probability ≥ 70% AND fair American odds between -250 and +10000 (decimal 1.40–101.00).</p>
<p><strong>Medium:</strong> model probability ≥ 55%.</p><p><strong>Low:</strong> all other picks.</p>
<h3>Predictions</h3><p>Written predictions are generated for high-confidence picks only. Each prediction is ≥30 words, names the team/player, includes current form and recent history, and states the explicit betting selection.</p>
<h3>Sources</h3><p>Every row carries an official source URL. Values that cannot be confirmed from an official source are left blank and flagged.</p>"""))
    # Count pages
    pages = sum(1 for root, dirs, files in os.walk("final-desk") for f in files if f.endswith(".html"))
    print(f"✓ Built {pages} pages, {len(matches)} matches, {len(predictions)} predictions")
    # Check links
    broken = 0
    for root, dirs, files in os.walk("final-desk"):
        for fn in files:
            if fn.endswith(".html"):
                with open(os.path.join(root, fn)) as f:
                    content = f.read()
                import re
                for href in re.findall(r'href="([^"#]*?)"', content):
                    if href.startswith("http") or href.startswith("#"): continue
                    target = os.path.normpath(os.path.join(root, href))
                    if not os.path.exists(target):
                        broken += 1
    print(f"✓ {broken} broken local links")

if __name__ == "__main__":
    build()
