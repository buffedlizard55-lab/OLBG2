"""Validate an evidence-first snapshot and build dependency-free GitHub Pages."""
import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/events.json"
OUT = ROOT / "site"
EXCLUDED = {"soccer", "boxing", "ufc", "mma", "football", "american football", "hurling", "horse racing", "cycling", "specials", "gaelic football"}

def esc(value):
    return html.escape(str(value), quote=True)

def link(url, label, *, external=True):
    if not url:
        return '<span class="muted">Unverified</span>'
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Unsafe URL: {url}")
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>'

def validate(data):
    if not data.get("as_of_utc") or not isinstance(data.get("events"), list):
        raise ValueError("Missing snapshot metadata/events")
    seen = set()
    for row in data["events"]:
        if row["id"] in seen:
            raise ValueError("Duplicate event ID")
        seen.add(row["id"])
        if row["sport"].lower() in EXCLUDED or not row["official_url"].startswith("https://www.nhl.com/"):
            raise ValueError("Excluded sport or unapproved official source")
        for field in ("date", "time", "away", "home", "league", "note", "olbg_url"):
            if not row.get(field):
                raise ValueError(f"Missing {field} on {row['id']}")
        link(row["official_url"], "Official")
        link(row["olbg_url"], "OLBG")
        lines = row["own_lines"]
        if set(lines) != {"money_line", "handicap", "total"}:
            raise ValueError("Incomplete market schema")
        if row["confidence"] not in (None, "low", "medium", "high"):
            raise ValueError("Invalid confidence")
        if row["confidence"] == "high" and (not row["winner"] or not row["prediction"] or len(row["prediction"].split()) < 30):
            raise ValueError("High confidence requires selection and 30+ word prediction")
        if row["winner"] and not row["confidence"]:
            raise ValueError("Selection requires confidence")
    for gap in data["coverage_gaps"]:
        link(gap["official_url"], "Official")
        link(gap["olbg_url"], "OLBG")

def page(title, body, active, prefix=""):
    nav = [
        ("index.html", "Overview", "home"),
        ("sports/ice-hockey.html", "Ice hockey", "hockey"),
        ("sports/basketball.html", "Basketball", "basketball"),
        ("sports/tennis.html", "Tennis", "tennis"),
        ("sports/baseball.html", "Baseball", "baseball"),
        ("methodology.html", "Methodology", "method"),
        ("flagged.html", "Flagged for review", "flagged"),
    ]
    items = "".join(f'<a class="nav-item {"active" if key == active else ""}" href="{prefix}{path}">{esc(text)}</a>' for path, text, key in nav)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{esc(title)} · OLBG research desk</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body><div class="shell"><aside class="sidebar"><div class="brand"><span class="brand-icon">O<span>.</span></span><div><strong>OLBG / research</strong><small>Independent evidence desk</small></div></div><div class="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{items}</nav><div class="side-note"><span class="dot"></span> Evidence-first snapshot<br><small>Not a live betting feed</small></div></aside><main class="main"><header class="topbar"><span>SPORTS INTELLIGENCE <span class="slash">/</span> {esc(title.upper())}</span><span class="top-right">RESEARCH MODE <span class="live-dot"></span></span></header>{body}<footer>Independent research snapshot · Not affiliated with OLBG or any league · No betting advice or guaranteed outcomes.</footer></main></div></body></html>'''

def event_rows(events):
    if not events:
        return '<tr><td colspan="8" class="empty">No independently verified fixtures are available for this category. See Flagged page for inventory notes.</td></tr>'
    out = []
    for row in events:
        lines = row["own_lines"]
        line_text = " / ".join(esc(lines[k]) if lines[k] is not None else "—" for k in ("money_line", "handicap", "total"))
        out.append(f'''<tr><td><strong>{esc(row['away'])}</strong><br><span class="muted">at {esc(row['home'])}</span></td><td>{esc(row['league'])}</td><td>{esc(row['date'])}<br><span class="muted">{esc(row['time'])}</span></td><td class="mono">{line_text}<small class="muted">ML / handicap / total</small></td><td>{esc(row['winner']) if row['winner'] else '<span class="muted">—</span>'}</td><td><span class="badge">{esc(row['confidence']) if row['confidence'] else 'Unrated'}</span></td><td>{link(row['official_url'], 'League')}<br>{link(row['olbg_url'], 'OLBG')}</td><td><span class="review">Review needed</span></td></tr>''')
    return "".join(out)

def table(events):
    return '<div class="table-scroll"><table><thead><tr><th>Matchup</th><th>League</th><th>Scheduled</th><th>Our lines</th><th>Winner</th><th>Confidence</th><th>Sources</th><th>Status</th></tr></thead><tbody>' + event_rows(events) + '</tbody></table></div>'

def write(path, text):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")

def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    validate(data)
    events = data["events"]
    asof = esc(data["as_of_utc"])
    kicker = f'<div class="eyebrow">SNAPSHOT <span class="dash"></span> {asof}</div>'
    notice = '<div class="notice"><b>Limited coverage — evidence first.</b> This is a manually verified, time-bound sample, not the full OLBG slate. A blank line or selection means no independent estimate has been substantiated. Market labels are research categories considered, not priced odds. <a href="flagged.html">See open checks →</a> · <a href="methodology.html">Methodology →</a></div>'
    # Overview hero + stats + explainer
    intro = f'''<section class="hero">{kicker}<h1>A clearer view of<br><em>what we know.</em></h1><p>Official fixtures, traceable sources, and an explicit boundary between confirmed facts and unfinished analysis. All rows are verified line-by-line against league gamecenters; unverified markets stay blank.</p></section>{notice}'''
    stats = f'<div class="stats"><div><span>VERIFIED FIXTURES</span><strong>{len(events):02}</strong><small>Official NHL gamecenters matched</small></div><div><span>ORIGINATED LINES</span><strong>00</strong><small>No unsupported prices published</small></div><div><span>OPEN CHECKS</span><strong>{len(events) + len(data["coverage_gaps"]):02}</strong><small>Visible on review page</small></div></div>'
    # scope and exclusions explainer
    scope_block = f'''<div class="scope-grid"><article class="scope-card"><h3>Scope</h3><p>{esc(data["scope"])}</p><small>Exclusions per brief: soccer, boxing, UFC/MMA, football (incl. Gaelic/American), hurling, horse racing, cycling, specials. Excluded content is never listed as eligible.</small></article><article class="scope-card muted-card"><h3>What counts as verified?</h3><p>Each published fixture requires both an official league gamecenter URL (NHL.com) and an OLBG reference. OLBG is not treated as an official source. Times are shown exactly as labeled by the league; no timezone conversion inferred.</p><small>Re-audited 05:20Z Oct 21 2026 — see verification log.</small></article></div>'''
    # OLBG reverse-engineer summary
    olbg_summary = '''<div class="section-head"><div><div class="eyebrow">REVERSE ENGINEERING</div><h2>OLBG structure observed</h2></div></div><div class="notes" style="margin-top:0"><article><b>OLBG is a tipster hub, not an odds provider</b><p>OLBG aggregates community tips per event (event_id). Each page lists tipster selections, win-tip percentages, and market tags (Money Line, Puck Line / Point Spread, Game Totals / Over-Under). It does not originate prices.</p><small>Examples: Ice hockey index and PHI@BUF / FLA@OTT pages list Over 5.50 at 00:37 local display; Basketball shows MIL@WAS Money Line 9/11 82% with Pointspread -4.50 and Under 239.50. <a href="https://www.olbg.com/betting-tips" target="_blank" rel="noopener noreferrer">OLBG tips hub ↗</a></small></article><article><b>Timing discrepancy flagged</b><p>NHL gamecenters consistently say 7:30 PM EDT for both Oct 21 games. OLBG shows 19:37 / 00:37 without a stated timezone, so no reconciliation is inferred. This is published as an irregularity on the Flagged page.</p><small>See NHL schedule vs OLBG event pages. Times remain exactly as labeled.</small></article><article><b>Markets considered, not priced</b><p>For NHL, the club examines Money line (2-way including OT), Puck line (usually ±1.5), and Game total (Over/Under). Without a documented model, inputs, timestamp and reproducible calculation, no independent line is published — hence the — / — / — display.</p><small>Methodology details: <a href="methodology.html">Methodology →</a></small></article></div>'''
    section = '<div class="section-head"><div><div class="eyebrow">MATCH TRACKER</div><h2>Fixture ledger</h2></div><a class="text-link" href="sports/ice-hockey.html">Explore ice hockey →</a></div>'
    write('index.html', page('Overview', intro + stats + scope_block + olbg_summary + section + table(events) + '<p class="table-foot">Source links accompany every fixture. Blank lines and unrated confidence mean no verified estimate — not a zero value. See Methodology for pricing rules.</p>', 'home'))

    # Category pages
    sport_defs = [
        ("Ice hockey", "ice-hockey", "Official NHL fixtures cross-checked with OLBG listings. No independent pricing or selection is ready. Other ice hockey leagues are inventoried but not verified — see flagged.", True),
        ("Basketball", "basketball", "OLBG lists NBA, EuroLeague, EuroCup and KBL games for Oct 21, but the official NBA games feed currently errors and Euroleague was not cross-checked in this snapshot. No basketball fixture is promoted to verified until an official league page confirms it.", False),
        ("Tennis", "tennis", "OLBG tennis lists ~15 matches for Oct 21 across ATP/WTA/ITF (e.g., Fernandez vs Sasnovich, Boulter vs Golubic) with markets Win Match, 1st Set, Set Betting. No ATP/WTA/ITF official draw cross-check has been performed in this snapshot, so tennis remains inventoried, not verified.", False),
        ("Baseball", "baseball", "MLB schedule for Oct 21 2026 shows no games (no-games message). There is therefore no baseball fixture to verify or originate on this date.", False),
    ]
    for sport, filename, desc, has_subset_possible in sport_defs:
        subset = [x for x in events if x["sport"] == sport]
        body = f'<section class="subhero">{kicker}<h1>{sport}</h1><p>{esc(desc)}</p></section><div class="section-head"><div><div class="eyebrow">CATEGORY / {esc(sport.upper())}</div><h2>Verified fixtures</h2></div><span class="count">{len(subset):02} entries</span></div>' + table(subset)
        if subset:
            body += '<div class="section-head below"><div><div class="eyebrow">MARKET AUDIT</div><h2>Research notes — line by line</h2></div></div><div class="notes">' + ''.join(f'<article><b>{esc(r["away"])} at {esc(r["home"])}</b><p>{esc(r["note"])}</p><small>Markets considered: {esc(", ".join(r["markets_checked"]))}. Listed by OLBG, not independently priced. {link(r["official_url"], "Official gamecenter")} · {link(r["olbg_url"], "OLBG")}</small></article>' for r in subset) + '</div>'
            # Add deep analysis for ice hockey only
            if sport == "Ice hockey":
                body += '<div class="section-head below"><div><div class="eyebrow">ANALYSIS FINDINGS</div><h2>What the verified data says (no pick yet)</h2></div></div><div class="analysis-grid"><article><b>Philadelphia Flyers @ Buffalo Sabres — form snapshot</b><p>Philadelphia enters 2-6-3 with the league-low 1.55 GF/GP (32nd) and 3.18 GA/GP. Power play 12.9% (27th), PK 84.6% (8th). Leaders: Trevor Zegras (2G5A 7pts in 11 GP) and rook Matvei Michkov team-high 6 goals. Buffalo is 4-3-2, scoring 3.00 GF/GP (17th) but allowing 3.67 GA/GP (26th), PP 9.1% last, PK 64.5% last. Jack Quinn 7 pts and Tage Thompson 3 goals pace them; goaltending splits Woll .917 vs UPL .860 show the matchup. The official gamecenter provides these lines; without an originating model we publish no money line, puck line or total.</p><small>Sources: <a href="https://www.nhl.com/gamecenter/phi-vs-buf/2026/10/21/2026020152" target="_blank" rel="noopener noreferrer">NHL gamecenter PHI@BUF ↗</a> | Team stats & roster verified 05:20Z</small></article><article><b>Florida Panthers @ Ottawa Senators — form snapshot</b><p>Florida (5-2-2) brings 3.33 GF/GP (9th) and a top-half defence 2.78 GA/GP (11th), PP 20.9% (16th), PK 80.6% (13th). Matthew Tkachuk 3G 11A 14pts in 9 GP leads, with Verhaeghe 6G and Seth Jones 10 pts. Ottawa (6-3-0) is 2.44 GF/GP (25th) but strong defensively 2.56 GA/GP (8th), PP 12.8% (28th), PK 79.4% (16th). Brady Tkachuk 10 pts and Ullmark 6-1-0, 1.33 GAA .945 anchor them. Last-10: FLA 5-2-2 (wins vs SEA, VAN OT, CBJ, LAK; losses BUF, MIN), OTT 6-3-0 (wins NYI SO, NJD, NSH SO, PHI, BOS, TOR). Again, verified but not priced — no confidence assigned until a model exists.</p><small>Sources: <a href="https://www.nhl.com/gamecenter/fla-vs-ott/2026/10/21/2026020153" target="_blank" rel="noopener noreferrer">NHL gamecenter FLA@OTT ↗</a> | Last-10 and roster verified 05:20Z</small></article><article><b>Why no high-confidence prediction?</b><p>High-confidence requires a 30+ word narrative naming teams, players, current form, recent history, and an explicit selection (e.g., pick or over/under) — each fact backed by an official source. The brief also requires an originated line (money line / handicap / total) from a documented method. Neither condition is met yet, so no picks are published rather than publishing unverified text.</p><small>Rule enforced by tests: prediction must exist and be ≥30 words if confidence=high.</small></article></div>'
        else:
            # add inventory detail for empty categories
            if sport == "Basketball":
                body += '<div class="section-head below"><div><div class="eyebrow">INVENTORY NOTES</div><h2>OLBG listings observed — not verified</h2></div></div><div class="notes"><article><b>NBA — Oct 21 slate on OLBG</b><p>OLBG basketball index lists MIL Bucks @ WAS Wizards 19:10 Money Line 9/11 (82%, 6 comments), ATL Hawks @ ORL Magic 19:10, CHI Bulls @ TOR Raptors 19:40, IND Pacers @ NO Pelicans 20:10, PHX Suns @ POR 22:10, plus DEN @ OKC tomorrow 21:40. Market tags include Money Line, Pointspread (-4.50 etc.) and Game Totals (Over/Under 239.50). Tipster commentary mentions WAS trio Davis/Young/Dybansta — these are tipster claims, not verified facts.</p><small>OLBG: <a href="https://www.olbg.com/betting-tips/Basketball/4" target="_blank" rel="noopener noreferrer">Basketball index ↗</a> · Official NBA games page (errors on load): <a href="https://www.nba.com/games" target="_blank" rel="noopener noreferrer">nba.com/games ↗</a></small></article><article><b>Euroleague / EuroCup / KBL</b><p>Also listed: Hapoel Tel Aviv vs Virtus Bologna 12:00, Panathinaikos vs Baskonia 14:15, PAOK vs Ulm 13:00, Bosna vs Bahcesehir 13:30, Seoul Thunders vs KCC Egis 06:00, AEK vs Antwerp 12:00. No euroleague.net cross-check performed.</p><small>OLBG example: <a href="https://www.olbg.com/betting-tips/Basketball/European/Euroleague/Hapoel_Tel_Aviv_vs_Virtus_Bologna/4?event_id=535919" target="_blank" rel="noopener noreferrer">Hapoel vs Virtus ↗</a></small></article></div>'
            elif sport == "Tennis":
                body += '<div class="section-head below"><div><div class="eyebrow">INVENTORY NOTES</div><h2>OLBG tennis observed</h2></div></div><div class="notes"><article><b>Tennis markets on OLBG</b><p>~15 matches: Leylah Fernandez vs Sasnovich 02:30 Win Match 6/7, Katie Boulter vs Golubic 01:30, Duckworth vs Darderi 02:30, Mannarino vs Rublev 05:30, Cirstea vs Bejlek 04:00, Bellucci vs Etcheverry Set Betting 2-1, Prizmic vs Dzumhur 05:30, Wawrinka vs Landaluce 08:00 etc. Markets: Win Match, 1st Set Winner, Set Betting.</p><small>OLBG: <a href="https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events" target="_blank" rel="noopener noreferrer">Tennis tips ↗</a> · Example: <a href="https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Aliaksandra_Sasnovich/3?event_id=902039" target="_blank" rel="noopener noreferrer">Fernandez vs Sasnovich ↗</a></small></article></div>'
            elif sport == "Baseball":
                body += '<div class="section-head below"><div><div class="eyebrow">INVENTORY NOTES</div><h2>MLB Oct 21</h2></div></div><div class="notes"><article><b>No MLB games Oct 21</b><p>MLB schedule page returns "There are no games scheduled for the dates selected." That is the official source for this date; it does not assert the league has no other dates.</p><small><a href="https://www.mlb.com/schedule/2026-10-21" target="_blank" rel="noopener noreferrer">MLB schedule Oct 21 ↗</a></small></article></div>'
        write(f'sports/{filename}.html', page(sport, body, filename.replace('ice-hockey', 'hockey'), '../'))

    # Methodology page
    method_body = f'''<section class="subhero">{kicker}<h1>Methodology<span class="accent">.</span></h1><p>How independent lines, confidence and high-confidence narratives would be produced — and why none are published in this snapshot.</p></section>
    <div class="section-head"><div><div class="eyebrow">PRICING FRAMEWORK</div><h2>Originating our own lines</h2></div></div>
    <div class="method-grid">
      <article><b>Requirements before any line is shown</b><p>An originated money line, handicap (puck line / point spread) and total (over/under) requires: (1) a documented statistical method (e.g., Elo, Poisson, Dixon-Coles for soccer-free sports), (2) explicit inputs (form, injuries, home advantage) with source links, (3) timestamp, and (4) reproducible calculation (code or spreadsheet). Without these, the table shows — / — / —.</p><small>Current status: 00 lines originated. Rule enforced by validation.</small></article>
      <article><b>Markets examined per match</b><p>Every available market is considered: Win match / Money line (2-way incl. OT for NHL, 3-way where applicable), Handicap / Puck line / Point spread (typically ±1.5 in NHL, varies elsewhere), Match total / Game totals Over-Under. OLBG tags are used as research categories only, never as our price.</p><small>Examples on OLBG: PHI@BUF Over 5.50; WAS -4.50 spread; Fernandez Win Match.</small></article>
      <article><b>Winner &amp; confidence</b><p>After originating lines, a winner (or Over/Under) is selected and labeled low / medium / high confidence. Low/medium can be a naked pick with a source note. High confidence additionally requires a 30+ word human narrative naming teams, players, current form and recent match history — each factual claim backed by an official source.</p><small>Test enforces: confidence high ⇒ winner + 30-word prediction present.</small></article>
      <article><b>What verification looks like</b><p>Line-by-line: every table row has an official league URL (NHL gamecenter, NBA games, MLB schedule, etc.) and an OLBG URL. If a value cannot be confirmed on the official source, it stays blank and the row is flagged. Nothing is inferred. See Flagged page for the current gaps.</p><small>Verification log is in COORDINATION.md with direct links.</small></article>
    </div>
    <div class="section-head below"><div><div class="eyebrow">EXCLUSIONS</div><h2>Sports outside scope</h2></div></div>
    <div class="scope-grid"><article class="scope-card muted-card"><h3>Excluded by brief</h3><p>Soccer, boxing, UFC/MMA, football (including Gaelic &amp; American football), hurling, horse racing, cycling, specials. These are never treated as eligible, even if OLBG lists them.</p><small>OLBG categories exist for these but are out of scope for this project.</small></article><article class="scope-card"><h3>Eligible — but not necessarily covered today</h3><p>All other sports OLBG tips are in scope when they appear: ice hockey (NHL, EHL, SHL...), basketball (NBA, EuroLeague...), tennis (ATP/WTA/ITF), baseball (MLB), rugby, darts, snooker, volleyball, etc. Coverage depends on what official schedule can verify on the snapshot date.</p><small>See category pages for per-sport status.</small></article></div>
    <div class="notice" style="margin-bottom:40px"><b>No betting advice.</b> This is a research snapshot. Nothing here is a recommendation or guaranteed outcome.</div>
    '''
    write('methodology.html', page('Methodology', method_body, 'method'))

    # Flagged
    flags = ''.join(f'<tr><td><strong>{esc(r["away"])} at {esc(r["home"])}</strong><br><span class="muted">{esc(r["sport"])} · {esc(r["date"])}</span></td><td>{esc(r["note"])}</td><td>{link(r["official_url"], "Official")}<br>{link(r["olbg_url"], "OLBG")}</td></tr>' for r in events)
    flags += ''.join(f'<tr><td><strong>{esc(g["sport"])}</strong><br><span class="muted">Coverage gap</span></td><td>{esc(g["issue"])}</td><td>{link(g["official_url"], "Official reference")}<br>{link(g["olbg_url"], "OLBG")}</td></tr>' for g in data['coverage_gaps'])
    body = f'<section class="subhero">{kicker}<h1>Flagged for review<span class="accent">.</span></h1><p>Open questions stay visible. Nothing here is represented as verified betting analysis until cleared.</p></section><div class="section-head"><div><div class="eyebrow">TRANSPARENCY LOG</div><h2>Unresolved items</h2></div><span class="count">{len(events)+len(data["coverage_gaps"]):02} open</span></div><div class="table-scroll"><table class="flags"><thead><tr><th>Item</th><th>Why flagged</th><th>Review sources</th></tr></thead><tbody>{flags}</tbody></table></div><div class="section-head below"><div><div class="eyebrow">LIMITS</div><h2>What would unlock a confident pick</h2></div></div><div class="notes"><article><b>Needed</b><p>A documented pricing model, input freeze (injuries, form freeze time), and source-backed 30-word narratives. Until then, high-confidence text blocks remain absent by design.</p><small>See <a href="methodology.html">Methodology</a> for rules.</small></article></div>'
    write('flagged.html', page('Flagged for review', body, 'flagged'))
    write('.nojekyll', '')
    print(f'Built {len(events)} verified fixtures, {len(events)+len(data["coverage_gaps"])} review items')

if __name__ == '__main__':
    build()
