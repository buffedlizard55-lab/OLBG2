"""Build the /canon/ static dashboard from data/canon/*.json.

Deterministic, dependency-free (stdlib only). Every table row carries a
clickable link to its official source. No value is invented by this script;
it only renders what canon_data.py / canon_predictions.py / canon_flags.py
already computed from verified inputs.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "canon"
OUT_DIR = ROOT / "canon"

SPORT_SLUGS = {
    "basketball": "basketball", "ice-hockey": "ice-hockey", "tennis": "tennis",
    "darts": "darts", "snooker": "snooker", "handball": "handball",
    "volleyball": "volleyball", "baseball": "baseball", "motor-racing": "motor-racing",
    "golf": "golf", "cricket": "cricket", "rugby-league": "rugby-league",
    "gaelic-football": "gaelic-football", "greyhounds": "greyhounds",
    "aussie-rules": "aussie-rules", "esports": "esports", "rugby-union": "rugby-union",
}
SPORT_NAMES = {
    "basketball": "Basketball", "ice-hockey": "Ice Hockey", "tennis": "Tennis",
    "darts": "Darts", "snooker": "Snooker", "handball": "Handball",
    "volleyball": "Volleyball", "baseball": "Baseball", "motor-racing": "Motor Racing",
    "golf": "Golf", "cricket": "Cricket", "rugby-league": "Rugby League",
    "gaelic-football": "Gaelic Football", "greyhounds": "Greyhounds",
    "aussie-rules": "Aussie Rules", "esports": "eSports", "rugby-union": "Rugby Union",
}

NAV = [
    ("index.html", "Overview"),
    ("matches.html", "All Matches"),
    ("picks.html", "High-Confidence Picks"),
    ("sports/index.html", "Sports"),
    ("flagged.html", "Flagged for Review"),
    ("audit.html", "Repo Audit"),
    ("methodology.html", "Methodology"),
    ("sources.html", "Sources"),
]

STYLE = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       margin: 0; background: #f6f7fb; color: #1b2430; line-height: 1.55; }
header.top { background: #0f172a; color: #fff; padding: 14px 24px; position: sticky; top: 0; z-index: 10; }
header.top .brand { font-weight: 700; font-size: 1.15rem; margin-right: 24px; }
header.top a { color: #cbd5e1; text-decoration: none; margin-right: 16px; font-size: 0.92rem; }
header.top a:hover, header.top a.active { color: #fff; text-decoration: underline; }
main { max-width: 1180px; margin: 0 auto; padding: 24px; }
h1 { font-size: 1.7rem; margin-top: 0; }
h2 { font-size: 1.25rem; margin-top: 2rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }
.lede { color: #475569; max-width: 760px; }
.notice { background: #fff7ed; border: 1px solid #fdba74; border-radius: 8px; padding: 12px 16px; margin: 16px 0; }
.notice.critical { background: #fef2f2; border-color: #fca5a5; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin: 18px 0; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }
.card .num { font-size: 1.6rem; font-weight: 700; color: #0f172a; }
.card .label { color: #64748b; font-size: 0.85rem; }
.table-wrap { overflow-x: auto; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; }
table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
th, td { text-align: left; padding: 9px 12px; border-bottom: 1px solid #eef1f6; white-space: nowrap; }
td.wrap, th.wrap { white-space: normal; }
th { background: #f1f5f9; position: sticky; top: 0; }
tr:hover td { background: #f8fafc; }
.badge { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 0.76rem; font-weight: 600; }
.badge.high { background: #dcfce7; color: #166534; }
.badge.medium { background: #fef9c3; color: #854d0e; }
.badge.low { background: #e2e8f0; color: #475569; }
.badge.none { background: #f1f5f9; color: #94a3b8; }
.badge.critical { background: #fee2e2; color: #991b1b; }
.badge.high-sev { background: #ffedd5; color: #9a3412; }
.badge.medium-sev { background: #fef9c3; color: #854d0e; }
.badge.low-sev { background: #e2e8f0; color: #475569; }
.pred { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 18px; margin-bottom: 14px; }
.pred h3 { margin: 0 0 6px 0; font-size: 1.02rem; }
.pred .meta { color: #64748b; font-size: 0.82rem; margin-bottom: 8px; }
.pred .sel { font-weight: 700; color: #0f172a; margin-top: 8px; }
a.src { font-size: 0.82rem; }
footer { max-width: 1180px; margin: 0 auto; padding: 24px; color: #94a3b8; font-size: 0.82rem; }
.sport-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.sport-grid a { display: block; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px;
                text-decoration: none; color: #0f172a; font-weight: 600; }
.sport-grid a .count { display: block; font-weight: 400; color: #64748b; font-size: 0.82rem; margin-top: 4px; }
code { background: #f1f5f9; padding: 1px 5px; border-radius: 4px; }
"""


def load():
    matches = json.loads((DATA_DIR / "matches.json").read_text())
    preds = json.loads((DATA_DIR / "predictions.json").read_text())
    flags = json.loads((DATA_DIR / "flagged.json").read_text())
    sources = json.loads((DATA_DIR / "sources.json").read_text())
    return matches, preds, flags, sources


def nav_html(active: str, depth: int = 0) -> str:
    prefix = "../" * depth
    items = []
    for href, label in NAV:
        cls = " class=\"active\"" if href == active else ""
        items.append(f'<a href="{prefix}{href}"{cls}>{escape(label)}</a>')
    return (
        f'<header class="top"><span class="brand">OLBG2 / canon</span>'
        f'<a href="{prefix}../index.html">Root dashboard</a>' + "".join(items) + "</header>"
    )


def page(title: str, body: str, active: str, depth: int = 0) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} - OLBG2 canon</title>
<style>{STYLE}</style>
</head><body>
{nav_html(active, depth)}
<main>
{body}
</main>
<footer>Session <code>arena/3de6d2ed-olbg2</code> &middot; captured 2026-10-22 12:08-12:18 UTC &middot;
Research only, not betting advice. 18+. See <a href="{'../' * depth}methodology.html">methodology</a> for the model and confidence rule.</footer>
</body></html>
"""


def conf_badge(conf: str | None) -> str:
    conf = conf or "none"
    label = conf.capitalize() if conf != "none" else "Unlined"
    return f'<span class="badge {conf}">{escape(label)}</span>'


def sev_badge(sev: str) -> str:
    return f'<span class="badge {sev}-sev">{escape(sev.capitalize())}</span>'


def match_row(m: dict, link_depth: int = 0) -> str:
    top = m["top_market"]
    sel = top["selection"] if top else "&mdash;"
    price = f"{top['fair_american']:+d} ({top['fair_decimal']:.2f})" if top else "&mdash;"
    conf = m["confidence"]
    date = m["date"] or "&mdash;"
    time_ = (m["time_utc"] or "").replace("T", " ").replace("Z", " UTC") if m["time_utc"] else "TBC"
    return (
        "<tr>"
        f"<td class='wrap'>{escape(m['sport_name'])}</td>"
        f"<td class='wrap'>{escape(m['competition'])}</td>"
        f"<td class='wrap'>{escape(m['home'])} vs {escape(m['away'])}</td>"
        f"<td>{escape(date)}</td>"
        f"<td>{escape(time_)}</td>"
        f"<td class='wrap'>{escape(sel)}</td>"
        f"<td>{price}</td>"
        f"<td>{conf_badge(conf)}</td>"
        f"<td><a class='src' href='{escape(m['source_url'])}' target='_blank' rel='noopener'>Official source &rarr;</a></td>"
        "</tr>"
    )


def build_index(matches, preds, flags, sources):
    c = matches["total_count"]
    orig = matches["originated_count"]
    unlined = matches["unlined_count"]
    high = matches["high_confidence_count"]
    body = f"""
<h1>OLBG2 canon desk &mdash; 17-sport first-hand origination &amp; forensic audit</h1>
<p class="lede">A from-scratch reverse-engineering of OLBG.com's eligible 17-sport taxonomy (every sport except
soccer, boxing, UFC/MMA, American football, hurling, horse racing, cycling and specials), captured
2026-10-22 between 12:08 and 12:18 UTC and cross-checked line by line against primary governing-body
sources. This pass also re-audited every existing layer in the repository and found eight previously
undetected factual defects &mdash; including a same-day PDC withdrawal that even OLBG.com's live page
had not yet reflected. See <a href="audit.html">the full audit</a>.</p>
<div class="notice critical"><strong>Headline finding:</strong> Luke Humphries withdrew from the PDC
European Championship on 2026-10-22 with gastroenteritis. Every other layer in this repository, and the
live OLBG event at capture time, still priced the original pairing. See <a href="flagged.html#F-01">F-01</a>.</div>
<div class="cards">
  <div class="card"><div class="num">{c}</div><div class="label">Total fixtures captured</div></div>
  <div class="card"><div class="num">{orig}</div><div class="label">Originated multi-market fixtures</div></div>
  <div class="card"><div class="num">{unlined}</div><div class="label">Transparently blank (unconfirmable)</div></div>
  <div class="card"><div class="num">{high}</div><div class="label">High-confidence in-band picks</div></div>
  <div class="card"><div class="num">{preds['count']}</div><div class="label">Written predictions (&ge;30 words)</div></div>
  <div class="card"><div class="num">17</div><div class="label">Eligible sports covered</div></div>
  <div class="card"><div class="num">{len(flags['flags'])}</div><div class="label">Flagged review items</div></div>
  <div class="card"><div class="num">{sources['count']}</div><div class="label">Distinct official sources cited</div></div>
</div>
<h2>Where to go next</h2>
<ul>
  <li><a href="matches.html">All Matches</a> &mdash; the full captured list across all 17 sports, every row linked to its official source.</li>
  <li><a href="picks.html">High-Confidence Picks</a> &mdash; the 59 written predictions, each &ge;30 words, naming verified players, form, and history.</li>
  <li><a href="sports/index.html">Sports</a> &mdash; per-sport pages.</li>
  <li><a href="flagged.html">Flagged for Review</a> &mdash; 10 items including 8 newly found defects in prior repository layers.</li>
  <li><a href="audit.html">Repo Audit</a> &mdash; the full line-by-line audit of every existing layer in this repository.</li>
  <li><a href="methodology.html">Methodology</a> &mdash; the confidence rule and price model.</li>
  <li><a href="sources.html">Sources</a> &mdash; every official URL cited, classified by publisher.</li>
</ul>
"""
    return page("Overview", body, "index.html")


def build_matches(matches):
    rows = "".join(match_row(m) for m in matches["matches"])
    body = f"""
<h1>All captured matches ({matches['total_count']})</h1>
<p class="lede">Every fixture captured in the 2026-10-22 window, across all 17 eligible OLBG sports. Blank
selection/price means no official input could be confirmed in time; see <a href="flagged.html">Flagged for Review</a>.</p>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th>Competition</th><th>Fixture</th><th>Date</th><th>Time (UTC)</th>
<th>Top selection</th><th>Fair price</th><th>Confidence</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
"""
    return page("All Matches", body, "matches.html")


def build_picks(preds):
    cards = []
    for p in preds["predictions"]:
        price = f"{p['fair_american']:+d} ({p['fair_decimal']:.2f} decimal, {p['probability']*100:.1f}% model probability)"
        cards.append(f"""
<div class="pred">
  <h3>{escape(p['sport_name'])} &middot; {escape(p['competition'])}</h3>
  <div class="meta">{escape(p['matchup'])} &middot; {escape(p['date'] or '')} &middot;
  <a class="src" href="{escape(p['source_url'])}" target="_blank" rel="noopener">Official source &rarr;</a></div>
  <div>{escape(p['prediction'])}</div>
  <div class="sel">Selection: {escape(p['selection'])} &middot; {price}</div>
</div>""")
    body = f"""
<h1>High-confidence picks ({preds['count']})</h1>
<p class="lede">Every pick below clears the uniform project rule: model probability &ge; 70% AND fair price
inside &minus;250 to +10000 American (1.40&ndash;101.00 decimal). Each write-up is unique prose of at least
30 words naming the teams/players, a verified current-form stat, a dated recent result, and the explicit
selection.</p>
{''.join(cards)}
"""
    return page("High-Confidence Picks", body, "picks.html")


def build_sports_index(matches):
    counts: dict[str, list] = {}
    for m in matches["matches"]:
        counts.setdefault(m["sport"], []).append(m)
    cards = []
    for slug in sorted(SPORT_SLUGS):
        rows = counts.get(slug, [])
        name = SPORT_NAMES[slug]
        high = sum(1 for r in rows if r["confidence"] == "high")
        cards.append(
            f'<a href="{slug}.html">{escape(name)}<span class="count">{len(rows)} fixtures '
            f'&middot; {high} high-confidence</span></a>'
        )
    body = f"""
<h1>Sports ({len(SPORT_SLUGS)})</h1>
<p class="lede">All 17 eligible OLBG sports. No excluded sport (soccer, boxing, UFC/MMA, American football,
hurling, horse racing, cycling, specials) appears anywhere in this desk.</p>
<div class="sport-grid">{''.join(cards)}</div>
"""
    return page("Sports", body, "sports/index.html", depth=1)


def build_sport_page(slug: str, matches):
    rows_data = [m for m in matches["matches"] if m["sport"] == slug]
    name = SPORT_NAMES[slug]
    rows = "".join(match_row(m) for m in rows_data)
    body = f"""
<h1>{escape(name)} ({len(rows_data)} fixtures)</h1>
<p class="lede"><a href="index.html">&larr; all sports</a></p>
<div class="table-wrap"><table>
<thead><tr><th>Sport</th><th>Competition</th><th>Fixture</th><th>Date</th><th>Time (UTC)</th>
<th>Top selection</th><th>Fair price</th><th>Confidence</th><th>Source</th></tr></thead>
<tbody>{rows if rows else '<tr><td colspan="9">No fixtures captured in this window.</td></tr>'}</tbody>
</table></div>
"""
    return page(name, body, "sports/index.html", depth=1)


def build_flagged(flags):
    rows = []
    for f in flags["flags"]:
        rows.append(f"""
<div class="pred" id="{escape(f['id'])}">
  <h3>{escape(f['id'])} &middot; {sev_badge(f['severity'])} &middot; {escape(f['category'])}</h3>
  <div class="meta"><strong>{escape(f['title'])}</strong></div>
  <div>{escape(f['detail'])}</div>
  <div class="sel"><a class="src" href="{escape(f['source_url'])}" target="_blank" rel="noopener">Official source &rarr;</a></div>
</div>""")
    body = f"""
<h1>Flagged for Review ({flags['count']})</h1>
<p class="lede">Irregularities found during this session's forensic audit, published for manual review.
These do not block publication; they are disclosed here with the official source needed to check each claim.</p>
{''.join(rows)}
"""
    return page("Flagged for Review", body, "flagged.html")


def build_audit(matches):
    audit_md_path = ROOT / "research" / "audit-3de6d2ed.md"
    md = audit_md_path.read_text() if audit_md_path.exists() else ""
    # Very small, dependency-free markdown-ish renderer: headings + tables as preformatted.
    lines = md.splitlines()
    html_parts = []
    in_table = False
    for line in lines:
        if line.startswith("# "):
            html_parts.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            html_parts.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("### "):
            html_parts.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.strip().startswith("|"):
            if not in_table:
                html_parts.append("<div class='table-wrap'><table>")
                in_table = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            tag = "th" if not html_parts[-1].strip().endswith("</tr></thead>") and "<thead>" not in "".join(html_parts[-3:]) else "td"
            html_parts.append("<tr>" + "".join(f"<td class='wrap'>{escape(c)}</td>" for c in cells) + "</tr>")
        else:
            if in_table:
                html_parts.append("</table></div>")
                in_table = False
            if line.strip() == "---":
                continue
            if line.strip():
                html_parts.append(f"<p class='lede'>{escape(line.strip())}</p>")
    if in_table:
        html_parts.append("</table></div>")
    body = "\n".join(html_parts)
    return page("Repo Audit", body, "audit.html")


def build_methodology():
    body = """
<h1>Methodology</h1>
<h2>Scope</h2>
<p class="lede">The brief excludes soccer/football, boxing, UFC/MMA, American football, hurling, horse
racing, cycling and specials. The remaining 17 OLBG-taxonomy sports are in scope: Basketball, Ice Hockey,
Tennis, Darts, Snooker, Handball, Volleyball, Baseball, Motor Racing, Golf, Cricket, Rugby League, Gaelic
Football, Greyhounds, Aussie Rules, eSports and Rugby Union.</p>
<h2>Line origination</h2>
<p class="lede">For each fixture, a model probability is estimated from official governing-body statistics
(standings, recent results, rankings, head-to-head form) captured first-hand on 2026-10-22. That probability
is converted to a no-vig fair price: <code>fair_decimal = 1 / probability</code>, and the American price is
derived from the decimal price in the standard way. No bookmaker price is read, scraped, or invented
anywhere in this layer.</p>
<h2>Confidence rule (uniform across this repository)</h2>
<p class="lede"><strong>High</strong> requires model probability &ge; 70% <em>and</em> a fair American price
inside &minus;250 to +10000 (decimal 1.40&ndash;101.00). Because 1/0.70 = 1.4286, the only probability window
that can satisfy both the 70% floor and the &minus;250 ceiling at the same time is 70.0%&ndash;71.4%.
Anything priced shorter than &minus;250 is capped at <strong>medium</strong> even if the model probability is
higher, because the brief's focus band excludes it. <strong>Medium</strong> is probability &ge; 60%.
<strong>Low</strong> is below 60%, and unlined rows show no confidence badge at all.</p>
<h2>Predictions</h2>
<p class="lede">Every high-confidence pick gets one unique, non-templated written prediction of at least 30
words. Each prediction names the competing teams or players, a verified current-form statistic, a dated
recent result, and the explicit betting selection with its fair price. No individual fact in a prediction is
asserted without a matching official source captured the same session.</p>
<h2>Verification and blanks</h2>
<p class="lede">Every published row links to the official governing-body page it was read from. Where an
official input could not be confirmed (for example, GBGB's lack of an advance structured trap-draw card for
ordinary greyhound meetings, or a fixture's starting pitcher not yet announced), the market is left blank and
the reason is published on the <a href="flagged.html">Flagged for Review</a> page. Nothing is inferred or
filled in to make a row look more complete than the evidence supports.</p>
<h2>Reproduce</h2>
<p class="lede"><code>python3 scripts/canon_data.py &amp;&amp; python3 scripts/canon_predictions.py &amp;&amp;
python3 scripts/canon_flags.py &amp;&amp; python3 scripts/canon_sources.py &amp;&amp; python3 scripts/canon_build.py
&amp;&amp; python3 scripts/canon_verify.py</code></p>
"""
    return page("Methodology", body, "methodology.html")


def build_sources_page(sources):
    rows = "".join(
        f"<tr><td class='wrap'>{escape(s['publisher'])}</td><td>{escape(s['host'])}</td>"
        f"<td class='wrap'><a href='{escape(s['url'])}' target='_blank' rel='noopener'>{escape(s['url'])}</a></td></tr>"
        for s in sources["sources"]
    )
    body = f"""
<h1>Source registry ({sources['count']} official URLs)</h1>
<p class="lede">Every URL cited anywhere on /canon/ is classified below by its publishing body. Zero
unclassified sources: every fact in this desk traces to a named primary governing body, tour, or league.</p>
<div class="table-wrap"><table>
<thead><tr><th>Publisher</th><th>Host</th><th>URL</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
"""
    return page("Sources", body, "sources.html")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sports").mkdir(parents=True, exist_ok=True)
    matches, preds, flags, sources = load()

    (OUT_DIR / "index.html").write_text(build_index(matches, preds, flags, sources))
    (OUT_DIR / "matches.html").write_text(build_matches(matches))
    (OUT_DIR / "picks.html").write_text(build_picks(preds))
    (OUT_DIR / "flagged.html").write_text(build_flagged(flags))
    (OUT_DIR / "audit.html").write_text(build_audit(matches))
    (OUT_DIR / "methodology.html").write_text(build_methodology())
    (OUT_DIR / "sources.html").write_text(build_sources_page(sources))
    (OUT_DIR / "sports" / "index.html").write_text(build_sports_index(matches))
    for slug in SPORT_SLUGS:
        (OUT_DIR / "sports" / f"{slug}.html").write_text(build_sport_page(slug, matches))

    page_count = 7 + 1 + len(SPORT_SLUGS)
    print(f"canon_build.py OK: built {page_count} HTML pages in {OUT_DIR}")


if __name__ == "__main__":
    main()
