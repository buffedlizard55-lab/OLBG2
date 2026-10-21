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
    nav = [("index.html", "Overview", "home"), ("sports/ice-hockey.html", "Ice hockey", "hockey"), ("sports/basketball.html", "Basketball", "basketball"), ("flagged.html", "Flagged for review", "flagged")]
    items = "".join(f'<a class="nav-item {"active" if key == active else ""}" href="{prefix}{path}">{esc(text)}</a>' for path, text, key in nav)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{esc(title)} · OLBG research desk</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body><div class="shell"><aside class="sidebar"><div class="brand"><span class="brand-icon">O<span>.</span></span><div><strong>OLBG / research</strong><small>Independent evidence desk</small></div></div><div class="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{items}</nav><div class="side-note"><span class="dot"></span> Evidence-first snapshot<br><small>Not a live betting feed</small></div></aside><main class="main"><header class="topbar"><span>SPORTS INTELLIGENCE <span class="slash">/</span> {esc(title.upper())}</span><span class="top-right">RESEARCH MODE <span class="live-dot"></span></span></header>{body}<footer>Independent research snapshot · Not affiliated with OLBG or any league · No betting advice or guaranteed outcomes.</footer></main></div></body></html>'''


def event_rows(events):
    if not events:
        return '<tr><td colspan="8" class="empty">No independently verified fixtures are available for this category.</td></tr>'
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
    notice = '<div class="notice"><b>Limited coverage.</b> This is a manually verified, time-bound sample, not the full OLBG slate. A blank line or selection means no independent estimate has been substantiated. <a href="flagged.html">See open checks →</a></div>'
    intro = f'''<section class="hero">{kicker}<h1>A clearer view of<br><em>what we know.</em></h1><p>Official fixtures, traceable sources, and an explicit boundary between confirmed facts and unfinished analysis.</p></section>{notice}'''
    stats = f'<div class="stats"><div><span>VERIFIED FIXTURES</span><strong>{len(events):02}</strong><small>Official league schedule matched</small></div><div><span>ORIGINATED LINES</span><strong>00</strong><small>No unsupported prices published</small></div><div><span>OPEN CHECKS</span><strong>{len(events) + len(data["coverage_gaps"]):02}</strong><small>Visible on review page</small></div></div>'
    section = '<div class="section-head"><div><div class="eyebrow">MATCH TRACKER</div><h2>Fixture ledger</h2></div><a class="text-link" href="sports/ice-hockey.html">Explore ice hockey →</a></div>'
    write('index.html', page('Overview', intro + stats + section + table(events) + '<p class="table-foot">Source links accompany every fixture. Times are shown exactly as labeled by the league; no conversion inferred.</p>', 'home'))
    for sport, filename in (("Ice hockey", "ice-hockey"), ("Basketball", "basketball")):
        subset = [x for x in events if x["sport"] == sport]
        body = f'<section class="subhero">{kicker}<h1>{sport}</h1><p>{"Official NHL fixtures cross-checked with OLBG listings. No independent pricing or selection is ready." if subset else "No matchup has passed independent official-source verification for this category."}</p></section><div class="section-head"><div><div class="eyebrow">CATEGORY / {esc(sport.upper())}</div><h2>Verified fixtures</h2></div><span class="count">{len(subset):02} entries</span></div>' + table(subset)
        if subset:
            body += '<div class="section-head below"><div><div class="eyebrow">MARKET AUDIT</div><h2>Research notes</h2></div></div><div class="notes">' + ''.join(f'<article><b>{esc(r["away"])} at {esc(r["home"])}</b><p>{esc(r["note"])}</p><small>Markets considered: {esc(", ".join(r["markets_checked"]))}. Listed by OLBG, not independently priced. {link(r["official_url"], "Official schedule")}</small></article>' for r in subset) + '</div>'
        write(f'sports/{filename}.html', page(sport, body, filename.replace('ice-hockey', 'hockey'), '../'))
    flags = ''.join(f'<tr><td><strong>{esc(r["away"])} at {esc(r["home"])}</strong><br><span class="muted">{esc(r["sport"])} · {esc(r["date"])}</span></td><td>{esc(r["note"])}</td><td>{link(r["official_url"], "Official")}<br>{link(r["olbg_url"], "OLBG")}</td></tr>' for r in events)
    flags += ''.join(f'<tr><td><strong>{esc(g["sport"])}</strong><br><span class="muted">Coverage gap</span></td><td>{esc(g["issue"])}</td><td>{link(g["official_url"], "Official reference")}<br>{link(g["olbg_url"], "OLBG")}</td></tr>' for g in data['coverage_gaps'])
    body = f'<section class="subhero">{kicker}<h1>Flagged for review<span class="accent">.</span></h1><p>Open questions stay visible. Nothing here is represented as verified betting analysis.</p></section><div class="section-head"><div><div class="eyebrow">TRANSPARENCY LOG</div><h2>Unresolved items</h2></div><span class="count">{len(events)+len(data["coverage_gaps"]):02} open</span></div><div class="table-scroll"><table class="flags"><thead><tr><th>Item</th><th>Why flagged</th><th>Review sources</th></tr></thead><tbody>{flags}</tbody></table></div>'
    write('flagged.html', page('Flagged for review', body, 'flagged'))
    write('.nojekyll', '')
    print(f'Built {len(events)} verified fixtures, {len(events)+len(data["coverage_gaps"])} review items')


if __name__ == '__main__':
    build()
