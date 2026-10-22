#!/usr/bin/env python3
"""Build the GitHub Pages site into docs/ from data/*.json.

Pure stdlib. Deterministic: the same data always produces byte-identical HTML.
Every table row renders at least one source link, and rows whose values could
not be confirmed from an official source render a blank cell plus an
UNVERIFIED badge - never a guessed value.
"""
import json, html, pathlib, collections, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "survey"
# GitHub Pages on this repository is configured as build_type "legacy" with
# source {branch: main, path: "/"}, and the API call to repoint it at /docs
# returns 403 for this token (no pages:write scope). The site is therefore
# published at the repository root, which also keeps the URLs clean:
# https://buffedlizard55-lab.github.io/OLBG2/flagged.html rather than /docs/flagged.html
DOCS = ROOT / "survey"
ASSETS = DOCS / "assets"
SPORTS_DIR = DOCS / "sports"
DOCS.mkdir(parents=True, exist_ok=True)
for d in (ASSETS, SPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
(DOCS / ".nojekyll").write_text("")

# Pages of the site, kept explicit so the verifier never scans the whole repo.
TOP_PAGES = ["index.html", "sports.html", "lines.html", "picks.html", "predictions.html",
             "methodology.html", "verification.html", "flagged.html", "excluded.html"]


def site_files():
    out = [DOCS / t for t in TOP_PAGES]
    out += sorted(SPORTS_DIR.glob("*.html"))
    out += [ASSETS / "style.css", ASSETS / "app.js"]
    return [f for f in out if f.exists()]

RETRIEVED = "2026-10-21"
DIVERGENCE_CAP_DOC = 15.0   # must match scripts/analyse.py DIVERGENCE_CAP

sports = json.loads((DATA / "sports.json").read_text())
flags = json.loads((DATA / "flags.json").read_text())
picks = json.loads((DATA / "picks.json").read_text())
preds = json.loads((DATA / "predictions.json").read_text())
lines_doc = json.loads((DATA / "lines.json").read_text())
lines = lines_doc["lines"]
CONST = lines_doc["model_constants"]
VIN = lines_doc["verified_inputs"]

EVENTS = {}
for f in sorted((DATA / "events").glob("*.json")):
    EVENTS[f.stem] = json.loads(f.read_text())

BY_KEY = {}
for k, rows in EVENTS.items():
    for r in rows:
        BY_KEY[(k, r["match"])] = r
LINE_BY_KEY = {(r["sport"], r["match"]): r for r in lines}

included = [s for s in sports if s["included"]]
excluded = [s for s in sports if not s["included"]]
all_events = sum(len(v) for v in EVENTS.values())
live_rows = sum(1 for v in EVENTS.values() for r in v if r["retrieved_via"] == "live_fetch")
snap_rows = all_events - live_rows
conf = collections.Counter(r["confidence"] for r in lines)
f15 = next(f for f in flags if f["id"] == "F-15")
n_unverified = len(f15.get("items", []))


def e(s):
    return html.escape("" if s is None else str(s))


OFFICIAL_HOSTS = ("icc-cricket.com", "lnr.fr", "unitedrugby.com", "owgr.com", "pgatour.com",
                  "dpworldtour.com", "atptour.com", "wtatennis.com", "pdc.tv", "worldsnooker.com",
                  "wst.tv", "world.rugby", "nba.com", "euroleaguebasketball.net", "nhl.com",
                  "nhle.com", "mlb.com", "formula1.com", "fia.com", "eurohandball.com",
                  "plusliga.pl", "nrl.com", "superleague.co.uk", "gaa.ie", "gbgb.org.uk")


def tier_of(url):
    """Classify a source so the site never calls an OLBG page an official one."""
    if not url:
        return "none"
    u = url.lower()
    if "olbg.com" in u:
        return "olbg"
    if any(h in u for h in OFFICIAL_HOSTS):
        return "official"
    return "corroborating"


def src(url, label="source"):
    if not url:
        return '<span class="badge badge-unv">UNVERIFIED</span>'
    return (f'<a class="src t-{tier_of(url)}" href="{e(url)}" rel="noopener noreferrer" '
            f'target="_blank">{e(label)} &#8599;</a>')


def autosrc(url):
    """Source link with a label that states the tier, so a reader can tell a
    governing body from OLBG's own page from press corroboration."""
    t = tier_of(url)
    return src(url, {"official": "official", "olbg": "OLBG",
                     "corroborating": "corroborating", "none": "source"}[t])


def pct(x):
    return "&mdash;" if x is None else f"{x * 100:.1f}%"


def odds(x):
    return "&mdash;" if x is None else f"{x:.2f}"


def badge(level):
    cls = {"high": "b-high", "medium": "b-med", "low": "b-low",
           "unverified": "b-unv"}.get(level, "b-unv")
    return f'<span class="badge {cls}">{e(level)}</span>'


CSS = """
a.src.t-official{color:var(--hi)}a.src.t-olbg{color:var(--acc)}a.src.t-corroborating{color:var(--md)}
:root{--bg:#0f1420;--panel:#161d2e;--panel2:#1c2438;--line:#26304a;--fg:#e8ecf6;
--mut:#94a1bd;--acc:#5b9dff;--hi:#33d69f;--md:#ffc857;--lo:#8b97b3;--unv:#ff6b6b;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
header{background:linear-gradient(180deg,#131a2b,#0f1420);border-bottom:1px solid var(--line);
padding:22px 0;position:sticky;top:0;z-index:20;backdrop-filter:blur(6px)}
.wrap{max-width:1240px;margin:0 auto;padding:0 20px}
.brand{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.brand h1{margin:0;font-size:20px;letter-spacing:.2px}
.brand .tag{color:var(--mut);font-size:13px}
nav{margin-top:12px;display:flex;gap:6px;flex-wrap:wrap}
nav a{padding:6px 11px;border:1px solid var(--line);border-radius:999px;color:var(--mut);font-size:13px}
nav a:hover{color:var(--fg);border-color:var(--acc);text-decoration:none}
nav a.on{background:var(--acc);border-color:var(--acc);color:#08111f;font-weight:600}
main{padding:26px 0 60px}
h2{font-size:18px;margin:30px 0 10px}h3{font-size:15px;margin:20px 0 8px;color:var(--mut)}
p.lead{color:var(--mut);max-width:80ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:18px 0 6px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi .n{font-size:26px;font-weight:700;letter-spacing:-.5px}
.kpi .l{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.7px;margin-top:3px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
table{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--panel);
border:1px solid var(--line);border-radius:12px;overflow:hidden}
caption{caption-side:top;text-align:left;color:var(--mut);font-size:12.5px;padding:8px 10px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--panel2);color:var(--mut);font-size:11.5px;text-transform:uppercase;
letter-spacing:.6px;position:sticky;top:0;cursor:pointer;white-space:nowrap}
th:hover{color:var(--fg)}
tbody tr:hover{background:#1a2237}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;
letter-spacing:.3px;border:1px solid transparent;white-space:nowrap}
.b-high{background:rgba(51,214,159,.16);color:var(--hi);border-color:rgba(51,214,159,.4)}
.b-med{background:rgba(255,200,87,.14);color:var(--md);border-color:rgba(255,200,87,.4)}
.b-low{background:rgba(139,151,179,.16);color:var(--lo);border-color:rgba(139,151,179,.4)}
.b-unv,.badge-unv{background:rgba(255,107,107,.14);color:var(--unv);border-color:rgba(255,107,107,.45)}
.src{white-space:nowrap;font-size:12px}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.controls input,.controls select{background:var(--panel2);border:1px solid var(--line);
color:var(--fg);padding:7px 10px;border-radius:8px;font-size:13px}
.controls input{min-width:230px}
.note{border-left:3px solid var(--acc);background:var(--panel2);padding:10px 13px;
border-radius:0 8px 8px 0;color:var(--mut);font-size:13.5px;margin:12px 0}
.warn{border-left-color:var(--unv)}
.pred{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:14px 0}
.pred h4{margin:0 0 4px;font-size:16px}
.pred .meta{color:var(--mut);font-size:12.5px;margin-bottom:10px}
.pred .text{font-size:14.5px;line-height:1.65}
.sel{display:inline-block;background:rgba(91,157,255,.14);border:1px solid rgba(91,157,255,.4);
color:#cfe1ff;padding:5px 10px;border-radius:8px;font-size:13px;font-weight:600;margin:8px 0}
ul.facts{margin:10px 0 0;padding-left:18px;color:var(--mut);font-size:12.5px}
ul.facts li{margin:4px 0}
footer{border-top:1px solid var(--line);padding:20px 0 40px;color:var(--mut);font-size:12.5px}
code{background:var(--panel2);padding:1px 5px;border-radius:5px;font-size:12.5px}
.flag{border:1px solid var(--line);border-left:3px solid var(--md);border-radius:8px;
padding:12px 14px;margin:10px 0;background:var(--panel)}
.flag.sev-irregularity,.flag.sev-source-conflict,.flag.sev-model-divergence{border-left-color:var(--unv)}
.flag.sev-coverage-gap,.flag.sev-data-availability{border-left-color:var(--md)}
.flag.sev-scope-decision,.flag.sev-environment,.flag.sev-data-freshness,.flag.sev-model-limitation,.flag.sev-source-tier{border-left-color:var(--acc)}
.flag h4{margin:0 0 4px;font-size:14px}
.flag .id{color:var(--mut);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.flag p{margin:6px 0;font-size:13.5px;color:#cdd6ea}
.flag .act{color:var(--md);font-size:12.5px}
.scroll{overflow-x:auto;border-radius:12px}
.small{font-size:12px;color:var(--mut)}
"""

JS = """
// Client-side filter + column sort. Progressive enhancement: the tables are
// complete and readable with JavaScript disabled.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('input[data-filter]').forEach(function (inp) {
    inp.addEventListener('input', function () {
      var q = inp.value.trim().toLowerCase();
      var tbl = document.querySelector(inp.getAttribute('data-filter'));
      if (!tbl) return;
      tbl.querySelectorAll('tbody tr').forEach(function (tr) {
        tr.style.display = !q || tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
      });
    });
  });
  document.querySelectorAll('select[data-sportfilter]').forEach(function (sel) {
    sel.addEventListener('change', function () {
      var tbl = document.querySelector(sel.getAttribute('data-sportfilter'));
      if (!tbl) return;
      tbl.querySelectorAll('tbody tr').forEach(function (tr) {
        tr.style.display = sel.value === 'all' || tr.getAttribute('data-sport') === sel.value ? '' : 'none';
      });
    });
  });
  document.querySelectorAll('table[data-sortable] th').forEach(function (th, i) {
    th.addEventListener('click', function () {
      var tbl = th.closest('table'), tb = tbl.querySelector('tbody');
      var rows = Array.prototype.slice.call(tb.querySelectorAll('tr'));
      var dir = th.getAttribute('data-dir') === 'asc' ? 'desc' : 'asc';
      tbl.querySelectorAll('th').forEach(function (o) { o.removeAttribute('data-dir'); });
      th.setAttribute('data-dir', dir);
      rows.sort(function (a, b) {
        var x = (a.children[i] ? a.children[i].textContent : '').trim();
        var y = (b.children[i] ? b.children[i].textContent : '').trim();
        var nx = parseFloat(x.replace(/[^0-9.\\-]/g, '')), ny = parseFloat(y.replace(/[^0-9.\\-]/g, ''));
        var c = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : x.localeCompare(y);
        return dir === 'asc' ? c : -c;
      });
      rows.forEach(function (r) { tb.appendChild(r); });
    });
  });
});
"""

NAV = [("../index.html", "Main dashboard"), ("../verified/index.html", "Verified Desk"),
       ("index.html", "Survey dashboard"), ("sports.html", "Sports"), ("lines.html", "Our Lines"),
       ("picks.html", "Picks"), ("predictions.html", "Predictions"),
       ("methodology.html", "Methodology"), ("verification.html", "Verification"),
       ("flagged.html", "Flagged for Review"), ("excluded.html", "Excluded Sports")]


def page(title, cur, body, sub=None):
    nav = "".join(
        f'<a href="{("../" if sub else "") + href}" class="{"on" if href == cur else ""}">{e(label)}</a>'
        for href, label in NAV)
    pre = "../" if sub else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} &middot; OLBG2</title>
<meta name="description" content="{e(title)} - OLBG2 sports betting research dashboard.">
<link rel="stylesheet" href="{pre}assets/style.css">
<script src="{pre}assets/app.js" defer></script></head>
<body><header><div class="wrap"><div class="brand">
<h1>OLBG2</h1><span class="tag">Reverse-engineered OLBG match intelligence &middot; retrieved {e(RETRIEVED)}</span>
</div><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">
Built from <code>data/*.json</code> by <code>scripts/build_site.py</code>. Every published value carries a source
link; values that could not be confirmed against an official source are left blank and flagged
<a href="{pre}flagged.html">for review</a>. Nothing on this site is betting advice. 18+.
</div></footer></body></html>
"""


def kpis(items):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="n">{n}</div><div class="l">{e(l)}</div></div>'
        for n, l in items) + "</div>"


# ---------------------------------------------------------------- dashboard
b = ["""<h2>Dashboard</h2>
<p class="lead">A reverse-engineering of <a href="https://www.olbg.com/" target="_blank" rel="noopener">OLBG.com</a>
covering every sport OLBG lists <em>except</em> the ten the brief excludes. We inventory the fixtures,
record every market OLBG offers on them, originate our own lines from official governing-body ratings,
pick a winner with a confidence label, and write a prediction for each high-confidence pick.
Where a value cannot be confirmed from an official source it is left blank and flagged &mdash; never inferred.</p>"""]
b.append(kpis([
    (f"{len(included)}", "sports in scope"),
    (f"{len(excluded)}", "sports excluded"),
    (f"{all_events}", "events inventoried"),
    (f"{len(lines)}", "lines originated"),
    (f"{conf['high']}", "high-confidence picks"),
    (f"{n_unverified}", "rows flagged unverified"),
    (f"{len(flags)}", "flags raised"),
]))
b.append(f"""<div class="note">Retrieval split: <strong>{live_rows}</strong> rows were read from a live fetch of
OLBG on {e(RETRIEVED)}; <strong>{snap_rows}</strong> come from dated search-index snapshots
(2026-10-18 to 2026-10-20). The two populations are never merged &mdash; each row carries
<code>retrieved_via</code> and <code>as_of</code>. See <a href="flagged.html">F-16</a>.</div>""")

b.append('<h2>Confidence breakdown</h2><div class="scroll"><table data-sortable><thead><tr>'
         '<th>Confidence</th><th class="num">Picks</th><th>Rule that produced it</th></tr></thead><tbody>')
RULES = {"high": "Model probability &ge; 0.72 on verified Tier&nbsp;1/2 inputs with verified form, "
                 "or &ge; 0.70 with the fair no-vig price inside the &minus;250&hellip;+10000 focus band "
                 "(the uniform rule shared by every layer).",
         "medium": "Model probability &ge; 0.60 on verified Tier&nbsp;1/2 inputs, or &ge; 0.70 on Tier&nbsp;3 base rates.",
         "low": "Any other published line, and any line whose divergence from an official published "
                "probability exceeds 15 percentage points.",
         "unverified": "No line could be originated from a verifiable official source."}
for lvl in ("high", "medium", "low"):
    b.append(f"<tr><td>{badge(lvl)}</td><td class='num'>{conf.get(lvl, 0)}</td><td class='small'>{RULES[lvl]}</td></tr>")
b.append("</tbody></table></div>")

b.append('<h2>Coverage by sport</h2><div class="scroll"><table data-sortable data-require-source><thead><tr>'
         '<th>Sport</th><th class="num">Events</th><th class="num">Lines originated</th>'
         '<th class="num">High</th><th class="num">Med</th><th class="num">Low</th>'
         '<th>Retrieval</th><th>OLBG listing</th></tr></thead><tbody>')
for s in included:
    key = s["slug"].lower()
    rows = EVENTS.get(key, [])
    ls = [r for r in lines if r["sport"] == key]
    c = collections.Counter(r["confidence"] for r in ls)
    via = collections.Counter(r["retrieved_via"] for r in rows)
    via_txt = ", ".join(f"{v.replace('_', ' ')}: {n}" for v, n in sorted(via.items())) or "no events"
    b.append(f"""<tr><td><a href="sports/{e(key)}.html">{e(s['name'])}</a></td>
<td class="num">{len(rows)}</td><td class="num">{len(ls)}</td>
<td class="num">{c.get('high', 0)}</td><td class="num">{c.get('medium', 0)}</td>
<td class="num">{c.get('low', 0)}</td><td class="small">{e(via_txt)}</td>
<td>{src(s['listing_url'], 'OLBG')}</td></tr>""")
b.append("</tbody></table></div>")

b.append("""<h2>Latest flags</h2><div class="grid">""")
for f in flags[:6]:
    b.append(f"""<div class="flag sev-{e(f['severity'])}"><div class="id">{e(f['id'])} &middot;
{e(f['severity'])}</div><h4>{e(f['title'])}</h4>
<p class="small"><a href="flagged.html#{e(f['id'])}">Read the detail &rarr;</a></p></div>""")
b.append(f'</div><p class="small"><a href="flagged.html">All {len(flags)} flags</a>, including '
         f'{n_unverified} itemised rows with no originated line.</p>')
open(DOCS / "index.html", "w").write(page("Dashboard", "index.html", "\n".join(b)))

# ---------------------------------------------------------------- all sports
b = ['<h2>Sports in scope</h2><p class="lead">OLBG exposes 22 sports. Fifteen are in scope after the brief\'s '
     'exclusions; seven are excluded. Sport identifiers and the full taxonomy come from '
     '<a href="https://www.olbg.com/sitemap-betting-tips.xml" target="_blank" rel="noopener">OLBG\'s own sitemap</a>.</p>',
     '<div class="scroll"><table data-sortable data-require-source><thead><tr><th>Sport</th><th class="num">OLBG id</th>'
     '<th class="num">Events</th><th>Status</th><th>Note</th><th>Listing</th></tr></thead><tbody>']
for s in sports:
    key = s["slug"].lower()
    n = len(EVENTS.get(key, []))
    link = (f'<a href="sports/{e(key)}.html">{e(s["name"])}</a>' if s["included"] else e(s["name"]))
    st = '<span class="badge b-high">in scope</span>' if s["included"] else '<span class="badge badge-unv">excluded</span>'
    b.append(f'<tr><td>{link}</td><td class="num">{e(s["olbg_sport_id"])}</td><td class="num">{n}</td>'
             f'<td>{st}</td><td class="small">{e(s["note"]) or "&mdash;"}</td>'
             f'<td>{src(s["listing_url"] or "https://www.olbg.com/sitemap-betting-tips.xml", "OLBG")}</td></tr>')
b.append('</tbody></table></div><p class="small">Exclusion reasoning is on the '
         '<a href="excluded.html">Excluded Sports</a> page.</p>')
open(DOCS / "sports.html", "w").write(page("Sports", "sports.html", "\n".join(b)))

# ---------------------------------------------------------------- per sport
MARKET_TAXONOMY = {
    "snooker": [("Win Match", "Which player wins the match.", "Individual matches"),
                ("Handicap Betting", "The match result once a frame handicap is applied.", "Individual matches"),
                ("Frame Betting", "The final frame score of a match.", "Individual matches"),
                ("Win Tournament", "Which player wins the whole tournament.", "Antepost")],
    "basketball": [("Money Line", "The winner of the game; a straight win bet.", "Individual games"),
                   ("Pointspread", "The winner after a points handicap is applied.", "Individual games"),
                   ("Game Totals", "Over/under on the combined points scored.", "Individual games")],
    "baseball": [("Money Line", "The winner of the game.", "Individual games"),
                 ("Run Line", "The winner after a run handicap, usually 1.5.", "Individual games"),
                 ("Game Totals", "Over/under on the combined runs scored.", "Individual games"),
                 ("Outright", "Winner of a league or tournament.", "Antepost")],
    "ice_hockey": [("Money Line", "The winner; two-way in the NHL because overtime and shootout count.", "Individual games"),
                   ("Puck Line", "The winner after a goal handicap, usually 1.5.", "Individual games"),
                   ("Game Totals", "Over/under on combined goals; 5.5 is the common NHL line.", "Individual games")],
    "motor_racing": [("Fastest Qualifier", "Pole position.", "Race weekend"),
                     ("Win Race", "Race or sprint winner.", "Race weekend"),
                     ("Podium Finish", "A driver to finish in the top three.", "Race weekend"),
                     ("Top 6 Finish", "A driver to finish in the top six.", "Race weekend"),
                     ("Points Finish", "A driver to finish in a points-scoring position.", "Race weekend"),
                     ("Fastest Lap", "The driver who sets the quickest lap.", "Race weekend"),
                     ("Win Tournament", "Antepost championship markets, including 'Without' versions.", "Antepost")],
    "cricket": [("Win Match", "Which side wins the match.", "Individual matches"),
                ("Outright Winner", "Which side wins the tournament.", "Antepost")],
    "tennis": [("Win Match", "Which player wins the match.", "Individual matches"),
               ("1st Set Winner", "Which player takes the opening set.", "Individual matches"),
               ("Set Betting", "The exact final set score, e.g. 2-1.", "Individual matches")],
    "rugby_union": [("To Win", "Which club wins the match.", "Individual matches"),
                    ("Handicap", "The result after a points handicap is applied.", "Individual matches"),
                    ("Win Tournament", "Which nation or club wins the competition.", "Antepost")],
    "rugby_league": [("To Win", "Which club wins the match.", "Individual matches"),
                     ("Handicap (2-way)", "The result after a points handicap is applied.", "Individual matches")],
    "darts": [("Win Match 2-way", "Which player wins the match; no draw option.", "Individual matches"),
              ("Win Tournament", "Which player wins the event.", "Antepost")],
    "handball": [("Money Line", "Home / away / tie.", "Individual matches")],
    "volleyball": [("Win Match", "Which club wins the match.", "Individual matches")],
    "golf": [("Win Tournament", "Which player wins the tournament.", "Antepost")],
}
TAX_SOURCE = {
    "snooker": "https://www.olbg.com/betting-tips/Snooker/8",
    "basketball": "https://www.olbg.com/betting-tips/Basketball/4",
    "baseball": "https://www.olbg.com/betting-tips/Baseball/12",
    "ice_hockey": "https://www.olbg.com/betting-tips/Ice_Hockey/13",
    "motor_racing": "https://www.olbg.com/betting-tips/Motor_Racing/14",
}

for s in included:
    key = s["slug"].lower()
    rows = EVENTS.get(key, [])
    b = [f'<h2>{e(s["name"])}</h2>',
         f'<p class="lead">OLBG sport id <code>{e(s["olbg_sport_id"])}</code>. '
         f'{len(rows)} event{"s" if len(rows) != 1 else ""} inventoried. '
         f'Listing source: {src(s["listing_url"], "OLBG")}</p>']
    if s["note"]:
        b.append(f'<div class="note">{e(s["note"])}</div>')
    if not rows:
        empty = next((f for f in flags if f["id"] in ("F-17", "F-18") and s["slug"] in f["detail"]), None)
        b.append('<div class="note warn"><strong>No upcoming events.</strong> OLBG lists no fixtures for this '
                 'sport at retrieval time. '
                 + (f'See <a href="../flagged.html#{e(empty["id"])}">{e(empty["id"])}</a>.' if empty else "")
                 + '</div>')
    else:
        tax = MARKET_TAXONOMY.get(key)
        if tax:
            ts = TAX_SOURCE.get(key, s["listing_url"])
            b.append('<h3>Markets OLBG offers on this sport</h3><div class="scroll"><table><thead><tr>'
                     '<th>Market</th><th>What it settles</th><th>Applies to</th></tr></thead><tbody>')
            for m, w, a in tax:
                b.append(f'<tr><td><strong>{e(m)}</strong></td><td>{e(w)}</td><td>{e(a)}</td></tr>')
            b.append(f'</tbody></table></div><p class="small">Taxonomy source: {src(ts, "OLBG")}</p>')

        b.append(f'<h3>Events ({len(rows)})</h3><div class="controls">'
                 f'<input type="search" placeholder="Filter {e(s["name"])} events..." data-filter="#t-{e(key)}">'
                 f'</div><div class="scroll"><table id="t-{e(key)}" data-sortable data-require-source><thead><tr>'
                 '<th>Match / event</th><th>Competition</th><th>Listed time (OLBG, US Eastern)</th>'
                 '<th>Market</th><th>OLBG top selection</th><th class="num">Tips</th><th class="num">%</th>'
                 '<th>Our pick</th><th>Confidence</th><th>Our line</th><th>Sources</th>'
                 '</tr></thead><tbody>')
        for r in rows:
            lr = LINE_BY_KEY.get((key, r["match"]))
            if lr:
                wm = next((m for m in lr["markets"] if m["name"].startswith("Win Match")), lr["markets"][0])
                line_txt = (f'p={pct(lr.get("pick_probability"))} @ {odds(wm.get("our_fair_odds_a") or wm.get("our_fair_odds_b"))}'
                            if wm.get("our_probability") is not None else "&mdash;")
                pick, cf = lr.get("pick"), lr["confidence"]
                official = lr.get("rating_source") or (wm.get("basis_source")) or r.get("official_fixture_source")
                extra = f'<br>{autosrc(official)}' if official else ""
                conf_cell = badge(cf)
            else:
                line_txt = '<span class="badge badge-unv">UNVERIFIED</span>'
                pick, cf = "&mdash;", "unverified"
                official = r.get("official_fixture_source")
                extra = f'<br>{autosrc(official)}' if official else ""
                conf_cell = badge("unverified")
            tips = r["tips_for"] if r["tips_for"] is not None else "&mdash;"
            total = r["tips_total"] if r["tips_total"] is not None else ""
            tipstr = f"{tips}/{total}" if total else str(tips)
            b.append(f"""<tr data-sport="{e(key)}"><td><strong>{e(r['match'])}</strong></td>
<td>{e(r.get('competition')) or '&mdash;'}</td><td class="small">{e(r['listed_time'])}
<div class="small">as of {e(r['as_of'])}</div></td>
<td>{e(r['market'])}</td><td>{e(r.get('top_selection')) or '&mdash;'}</td>
<td class="num">{tipstr}</td><td class="num">{'' if r.get('tip_pct') is None else str(r['tip_pct']) + '%'}</td>
<td>{e(pick) if pick not in ('&mdash;',) else '&mdash;'}</td><td>{conf_cell}</td><td>{line_txt}</td>
<td>{src(r['source_url'], 'OLBG')}{extra}</td></tr>""")
        b.append('</tbody></table></div>')
        b.append('<p class="small">Times are reproduced exactly as OLBG displays them, which is US Eastern '
                 '(<a href="../flagged.html#F-06">F-06</a>). "Tips" is OLBG\'s community tip count for the top '
                 'selection and is <em>not</em> an input to our lines. Rows marked '
                 '<span class="badge badge-unv">UNVERIFIED</span> have no originated line; the reason and the '
                 'official source needed are listed under <a href="../flagged.html#F-15">F-15</a>.</p>')
    SPORTS_DIR.joinpath(f"{key}.html").write_text(
        page(s["name"], "sports.html", "\n".join(b), sub=True))

# ---------------------------------------------------------------- lines
b = ['<h2>Our originated lines</h2>',
     f'<p class="lead">{len(lines)} lines originated from verified inputs. Each is computed by a disclosed formula '
     'from a governing-body rating or a published competition base rate. Bookmaker prices were <strong>not</strong> '
     'used, because OLBG renders them client-side and they were not retrievable '
     '(<a href="flagged.html#F-02">F-02</a>). Full method on the '
     '<a href="methodology.html">Methodology</a> page.</p>',
     '<div class="controls"><input type="search" placeholder="Filter lines..." data-filter="#t-lines"></div>',
     '<div class="scroll"><table id="t-lines" data-sortable data-require-source><thead><tr>'
     '<th>Match</th><th>Sport</th><th>Tier</th><th>Verified input</th><th class="num">Our p</th>'
     '<th class="num">Our fair odds</th><th>Handicap</th><th>Total</th><th>Official cross-ref</th>'
     '<th>Sources</th></tr></thead><tbody>']
for r in sorted(lines, key=lambda x: (-x["pick_probability"], x["match"])):
    wm = next((m for m in r["markets"] if m["name"].startswith("Win Match")), r["markets"][0])
    hc = next((m for m in r["markets"] if m["name"].lower().startswith("handicap")), None)
    tt = next((m for m in r["markets"] if m["name"].lower().startswith("match total")), None)
    p_side = wm.get("our_probability") if wm.get("our_probability") is not None else r.get("pick_probability")
    fo = wm.get("our_fair_odds_a") or wm.get("our_fair_odds_b")
    if r.get("pick") == r.get("side_b"):
        fo = wm.get("our_fair_odds_b")
    xr = r.get("official_cross_ref")
    xr_txt = (f'{xr["home"]} / {xr["draw"]} / {xr["away"]}<div class="small">&Delta; '
              f'{r.get("official_divergence_pp", "?")} pp</div>') if xr else "&mdash;"
    xr_src = f'<br>{src(xr["source"], "LNR")}' if xr else ""
    inp = (f'{e(r.get("rating_label") or "ICC rating")}: {e(r.get("side_a"))} {e(r.get("rating_a"))} v '
           f'{e(r.get("side_b"))} {e(r.get("rating_b"))}' if r.get("rating_a") is not None
           else "OLBG published competition base rates")
    inp_src = r.get("rating_source") or wm.get("basis_source")
    hc_txt = e(hc.get("our_line")) if hc and hc.get("our_line") else (
        '<span class="badge badge-unv">UNVERIFIED</span>' if hc else "&mdash;")
    tt_txt = e(tt.get("our_line")) if tt and tt.get("our_line") is not None else (
        '<span class="badge badge-unv">UNVERIFIED</span>' if tt else "&mdash;")
    b.append(f"""<tr><td><strong>{e(r['match'])}</strong><div class="small">{e(r.get('competition'))}</div></td>
<td>{e(r['sport'])}</td><td><code>{e(r['tier'])}</code></td><td class="small">{inp}</td>
<td class="num">{pct(p_side)}</td><td class="num">{odds(fo)}</td><td>{hc_txt}</td><td>{tt_txt}</td>
<td class="num small">{xr_txt}</td>
<td>{src(r.get('olbg_source'), 'OLBG')}{f'<br>{autosrc(inp_src)}' if inp_src else ''}{xr_src}</td></tr>""")
b.append('</tbody></table></div>')
b.append('<div class="note warn">Where a handicap or total cell reads '
         '<span class="badge badge-unv">UNVERIFIED</span>, no official input was available to originate it. '
         'The cell is deliberately blank rather than estimated. Cricket totals and handicaps are all in this '
         'state &mdash; see <a href="flagged.html#F-15">F-15</a>.</div>')
open(DOCS / "lines.html", "w").write(page("Our Lines", "lines.html", "\n".join(b)))

# ---------------------------------------------------------------- picks
b = ['<h2>Picks and confidence</h2>',
     '<p class="lead">One winner pick per originated line, with a low / medium / high confidence label from the '
     'rule published on the <a href="methodology.html">Methodology</a> page. Events without an originated line '
     'get no pick at all &mdash; a pick is never made without a verifiable basis.</p>',
     '<div class="controls"><input type="search" placeholder="Filter picks..." data-filter="#t-picks">'
     '<select data-sportfilter="#t-picks"><option value="all">All sports</option>'
     + "".join(f'<option value="{e(k)}">{e(k.replace("_", " "))}</option>'
               for k in sorted({r["sport"] for r in picks})) + '</select></div>',
     '<div class="scroll"><table id="t-picks" data-sortable data-require-source><thead><tr><th>Match</th><th>Sport</th>'
     '<th>Pick</th><th class="num">Our probability</th><th>Confidence</th><th>Why</th>'
     '<th>Form verified</th><th>Sources</th></tr></thead><tbody>']
for r in sorted(picks, key=lambda x: ({"high": 0, "medium": 1, "low": 2}.get(x["confidence"], 3),
                                      -(x["pick_probability"] or 0))):
    lr = LINE_BY_KEY[(r["sport"], r["match"])]
    notes = "<br>".join(e(n) for n in r.get("confidence_notes", [])) or "&mdash;"
    official = lr.get("rating_source")
    b.append(f"""<tr data-sport="{e(r['sport'])}"><td><strong>{e(r['match'])}</strong>
<div class="small">{e(r.get('competition'))}</div></td><td>{e(r['sport'])}</td>
<td><strong>{e(r['pick'])}</strong></td><td class="num">{pct(r['pick_probability'])}</td>
<td>{badge(r['confidence'])}</td><td class="small">{notes}</td>
<td>{'yes' if r['form_verified'] else 'no'}</td>
<td>{src(lr.get('olbg_source'), 'OLBG')}{f'<br>{autosrc(official)}' if official else ''}</td></tr>""")
b.append('</tbody></table></div>')
open(DOCS / "picks.html", "w").write(page("Picks", "picks.html", "\n".join(b)))

# ---------------------------------------------------------------- predictions
def pred_card(p):
    band_tag = ('<span class="badge b-high">in band &minus;250&hellip;+10000</span>'
                if p.get("price_band") == "in-band"
                else '<span class="badge badge-unv">outside the &minus;250&hellip;+10000 focus band</span>')
    out = [f"""<div class="pred"><h4>{e(p['match'])} {band_tag}</h4>
<div class="meta">{e(p['competition'])} &middot; {e(p['kickoff'])} &middot; {e(p['venue'])}</div>
<div class="sel">{e(p['selection'])}</div>
<div class="meta">Our probability <strong>{pct(p['our_probability'])}</strong> &middot; our fair price
<strong>{odds(p['our_fair_odds'])}</strong> &middot; fair American {p.get('fair_american', '&mdash;')}
&middot; confidence {badge(p['confidence'])}
&middot; {e(p['word_count'])} words</div>
<div class="text">{e(p['text'])}</div>
<ul class="facts">"""]
    for fact, url in p["facts_used"]:
        out.append(f'<li>{e(fact)} &mdash; {src(url, "verify")}</li>')
    out.append("</ul>")
    if p.get("official_cross_ref"):
        out.append(f'<div class="note small">Official cross-reference: {e(p["official_cross_ref"])}</div>')
    out.append(f'<p class="small">OLBG fixture: {src(p.get("olbg_source"), "OLBG")} &middot; '
               f'Venue source: {src(p.get("venue_source"), "verify")}</p></div>')
    return "".join(out)

in_band = [p for p in preds if p.get("price_band") == "in-band"]
outside = [p for p in preds if p.get("price_band") != "in-band"]
b = ['<h2>Predictions for high-confidence picks</h2>',
     f'<p class="lead">{len(preds)} high-confidence picks carry a written prediction. Every factual claim in each '
     'one is listed underneath it with the source it was verified against. No player, score, injury or date appears '
     'in a prediction unless it was verified during collection. The brief asks high-confidence generation to focus '
     'on fair prices between &minus;250 and +10000, so the two groups below are shown separately.</p>']
b.append(f'<h3>In the &minus;250&hellip;+10000 focus band ({len(in_band)})</h3>')
if in_band:
    for p in in_band:
        b.append(pred_card(p))
else:
    b.append('<div class="note">No selection on this slate qualifies inside the focus band: every high-confidence '
             'pick here is priced shorter than &minus;250 on its win-match market. They are shown below and '
             'labelled honestly rather than passed off as in-band.</div>')
b.append(f'<h3>Outside the focus band &mdash; chalk favourites ({len(outside)})</h3>')
for p in outside:
    b.append(pred_card(p))
b.append('<div class="note warn">Medium and low confidence picks deliberately carry no written prediction. '
         'For those we do not hold enough verified player-level detail to write one without inventing it, which '
         'the verification rule forbids.</div>')
open(DOCS / "predictions.html", "w").write(page("Predictions", "predictions.html", "\n".join(b)))

# ---------------------------------------------------------------- methodology
b = ['<h2>Methodology</h2>',
     '<p class="lead">How a line is originated, how a pick is made, and exactly which parts are verified facts '
     'versus disclosed modelling assumptions.</p>',
     '<div class="card"><h3>1. Inventory</h3><p>OLBG\'s sport taxonomy is taken from '
     + src("https://www.olbg.com/sitemap-betting-tips.xml", "its sitemap") +
     ', which lists 22 sports with numeric ids. Each in-scope sport\'s <code>/betting-tips/&lt;Sport&gt;/&lt;id&gt;</code> '
     'page is read and every fixture recorded with its event id, competition, displayed time, market, OLBG\'s top '
     'community selection and tip counts. Each row records <code>retrieved_via</code> and <code>as_of</code> so a '
     'live-fetched row is never mixed with a dated snapshot row.</p></div>',
     '<div class="card"><h3>2. Evidence tiers</h3><div class="scroll"><table><thead><tr><th>Tier</th>'
     '<th>Input</th><th>Used for</th></tr></thead><tbody>'
     '<tr><td><code>tier1</code></td><td>Governing-body rating for <strong>both</strong> competitors '
     '(ICC team ratings, OWGR average points, PDC Order of Merit, WST rankings, ATP/WTA rankings).</td>'
     '<td>Cricket internationals in this run.</td></tr>'
     '<tr><td><code>tier2</code></td><td>Official league table position and points difference for both clubs.</td>'
     '<td>Top 14 fixtures in this run.</td></tr>'
     '<tr><td><code>tier3</code></td><td>Published competition-level base rates with a stated sample size.</td>'
     '<td>URC fixtures in this run.</td></tr>'
     '<tr><td><code>none</code></td><td>Nothing verifiable.</td><td>No line is published; the row is flagged.</td></tr>'
     '</tbody></table></div></div>',
     '<div class="card"><h3>3. Probability</h3><p>A logistic function of the rating gap: '
     '<code>p = 1 / (1 + exp(-&Delta; / S))</code>. Fair no-vig decimal price is <code>1 / p</code>. '
     'Half-point lines use <code>floor(x) + 0.5</code>, the convention that avoids a push.</p>',
     '<h3>Model constants &mdash; disclosed assumptions, not sourced facts</h3>'
     '<div class="scroll"><table><thead><tr><th>Constant</th><th class="num">Value</th><th>Status</th>'
     '</tr></thead><tbody>']
for k, v in CONST.items():
    if k == "notes":
        continue
    b.append(f'<tr><td><code>{e(k)}</code></td><td class="num">{e(v)}</td>'
             f'<td class="small">Assumption. Sensitivity is published per line.</td></tr>')
b.append('</tbody></table></div><ul class="facts">')
for n in CONST.get("notes", []):
    b.append(f'<li>{e(n)}</li>')
b.append('</ul></div>')
b.append('<div class="card"><h3>4. Confidence rule</h3><div class="scroll"><table><thead><tr>'
         '<th>Label</th><th>Condition</th></tr></thead><tbody>')
for lvl in ("high", "medium", "low", "unverified"):
    b.append(f'<tr><td>{badge(lvl)}</td><td class="small">{RULES[lvl]}</td></tr>')
b.append('</tbody></table></div><div class="note warn"><strong>Official-divergence guard.</strong> Where a '
         'governing body publishes its own probability for the same fixture, we compute the gap. If it exceeds '
         f'{DIVERGENCE_CAP_DOC} percentage points, confidence is capped at LOW and the disagreement is flagged. '
         'We never silently override an official figure with our own.</div></div>')
b.append('<div class="card"><h3>5. Predictions</h3><p>A prediction is written only for a high-confidence pick, '
         'must be at least 30 words, must name the selection unambiguously, and may only use facts recorded in '
         '<code>data/lines.json</code> or <code>data/analyse</code> verified-form blocks. Each fact is published '
         'under the prediction with its source link. The word count is asserted at build time.</p></div>')
b.append('<div class="card"><h3>6. What we do not do</h3><ul class="facts">'
         '<li>We do not de-vig bookmaker prices, because OLBG renders them client-side and they were not '
         'retrievable (<a href="flagged.html#F-02">F-02</a>).</li>'
         '<li>We do not use OLBG community tip percentages as a probability input. That would echo the crowd '
         'rather than originate a line. Tip counts are shown as separate, clearly labelled community data.</li>'
         '<li>We do not fill a blank cell with an estimate. An unverifiable value stays blank and is flagged.</li>'
         '<li>We do not name a player, injury, score or date in a prediction unless it was verified.</li>'
         '</ul></div>')
open(DOCS / "methodology.html", "w").write(page("Methodology", "methodology.html", "\n".join(b)))

# ---------------------------------------------------------------- verification
b = ['<h2>Verification</h2>',
     f'<p class="lead">Every row on every table carries a source link. This page reports what was checked, what '
     f'passed, and what remains unverified. Run of {e(RETRIEVED)}.</p>',
     kpis([(f"{all_events}", "rows inventoried"),
           (f"{live_rows}", "live-fetched"),
           (f"{snap_rows}", "snapshot, flagged"),
           (f"{len(lines)}", "lines with a verified input"),
           (f"{n_unverified}", "rows with no verified basis"),
           (f"{len(flags)}", "flags raised")])]
b.append('<div class="card"><h3>Official sources consulted</h3><div class="scroll"><table data-require-source><thead><tr>'
         '<th>Source</th><th>Body</th><th>What it was used for</th><th>As of</th><th>Status</th>'
         '</tr></thead><tbody>')
OFFICIAL = [
    ("https://top14.lnr.fr/classement", "Ligue Nationale de Rugby",
     "Official Top 14 standings after Journée 6 for Round 7 origination", "2026-10-21", "used"),
    ("https://top14.lnr.fr/club/toulouse", "Ligue Nationale de Rugby",
     "Official club win probabilities (83.06 / 15.32 / 1.61) & Sale Sharks 60-14 result", "2026-10-21", "used"),
    ("https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan", "Ligue Nationale de Rugby",
     "Fixture confirmation: Journée 7, 24 Oct 2026 16:35, Stade Ernest-Wallon", "2026-10-21", "used"),
    ("https://stats.unitedrugby.com/match-centre/table/2026-27", "United Rugby Championship",
     "Official URC Round 3 standings & Round 4 fixtures", "2026-10-21", "used"),
    ("https://www.pdc.tv/rankings", "Professional Darts Corporation",
     "Official PDC Werner Ranking Ladder prize sums for all 32 European Championship R1 players", "2026-10-21", "used"),
    ("https://www.wst.tv/rankings/", "World Snooker Tour",
     "Official WST two-year prize rankings (Top 36) & Northern Ireland Open R2 match centre", "2026-10-21", "used"),
    ("https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026", "Major League Baseball",
     "Official 2026 regular-season W-L & run totals for World Series Game 1 (TB @ MIL)", "2026-10-21", "used"),
    ("https://www.atptour.com/en/rankings/singles", "ATP Tour",
     "Official PIF ATP Top-100 singles rankings (originated on /verified/)", "2026-10-21", "used"),
    ("https://www.euroleaguebasketball.net/en/euroleague/standings/", "Euroleague Basketball",
     "Official EuroLeague R7 & BKT EuroCup R4 standings (originated on /verified/)", "2026-10-21", "used"),
    ("https://ehfcl.eurohandball.com/men/2026-27/standings/", "European Handball Federation",
     "Official EHF Champions League Men Group Phase standings (originated on /verified/)", "2026-10-21", "used"),
    ("https://www.formula1.com/en/results/2026/drivers", "FIA Formula One",
     "Official 2026 FIA Drivers' Championship points after Round 17 (originated on /verified/)", "2026-10-21", "used"),
    ("https://www.icc-cricket.com/rankings/team-rankings", "International Cricket Council",
     "Client-side JS shell only; cricket rows left blank after purging third-party mirrors", "2026-10-21", "not usable"),
    ("https://www.wtatennis.com/rankings/singles", "WTA Tour",
     "Client-side JS shell; WTA rows left blank", "2026-10-21", "not usable"),
]
for url, body, use, asof, status in OFFICIAL:
    ok = status.startswith("used")
    b.append(f'<tr><td>{autosrc(url)}<div class="small">{e(url.replace("https://www.", "").replace("https://", "")[:52])}</div></td>'
             f'<td>{e(body)}</td><td class="small">{e(use)}</td><td class="small">{e(asof)}</td>'
             f'<td>{badge("high") if ok else badge("unverified")} <span class="small">{e(status)}</span></td></tr>')
b.append('</tbody></table></div></div>')
b.append('<div class="card"><h3>Checks performed</h3><ul class="facts">'
         '<li><strong>Row-level provenance</strong> &mdash; every one of the '
         f'{all_events} inventory rows carries an OLBG event or listing URL.</li>'
         '<li><strong>Blank-not-guess</strong> &mdash; no cell contains an estimated value. Unverifiable cells '
         'render as <span class="badge badge-unv">UNVERIFIED</span> and are itemised under '
         '<a href="flagged.html#F-15">F-15</a>.</li>'
         '<li><strong>Timezone cross-check</strong> &mdash; OLBG\'s displayed 07:30 for Afghanistan v Bangladesh '
         'was reconciled against the official 11:30 GMT start, establishing that OLBG displays US Eastern. '
         'See <a href="flagged.html#F-06">F-06</a>.</li>'
         '<li><strong>Cross-source reconciliation</strong> &mdash; ICC, ATP, PDC and WST values were compared '
         'across the official page and independent mirrors; every disagreement is logged '
         '(<a href="flagged.html#F-09">F-09</a>, <a href="flagged.html#F-10">F-10</a>, '
         '<a href="flagged.html#F-11">F-11</a>, <a href="flagged.html#F-12">F-12</a>).</li>'
         '<li><strong>Model versus official</strong> &mdash; our lines were compared with LNR\'s own published '
         'probabilities; the disagreement on La Rochelle v Bordeaux capped that pick at LOW '
         '(<a href="flagged.html#F-14">F-14</a>).</li>'
         '<li><strong>Prediction word count</strong> &mdash; asserted at build time to be at least 30 words.</li>'
         '<li><strong>Build and link integrity</strong> &mdash; <code>scripts/verify.py</code> checks every '
         'internal link resolves to a generated file and that no table row is missing a source cell.</li>'
         '</ul></div>')
open(DOCS / "verification.html", "w").write(page("Verification", "verification.html", "\n".join(b)))

# ---------------------------------------------------------------- flagged
b = ['<h2>Flagged for Review</h2>',
     f'<p class="lead">{len(flags)} flags. A flag never blocks publication; it marks something a human should '
     'look at &mdash; a source conflict, a scope decision, a coverage gap, or a value we could not verify. '
     f'{n_unverified} individual event rows carry no originated line and are itemised under F-15.</p>',
     kpis([(f"{len(flags)}", "flags"),
           (sum(1 for f in flags if f['severity'] == 'source-conflict'), "source conflicts"),
           (sum(1 for f in flags if f['severity'] == 'irregularity'), "irregularities"),
           (sum(1 for f in flags if f['severity'] == 'scope-decision'), "scope decisions"),
           (sum(1 for f in flags if f['severity'] == 'coverage-gap'), "coverage gaps"),
           (n_unverified, "unverified rows")])]
for f in flags:
    b.append(f'<div class="flag sev-{e(f["severity"])}" id="{e(f["id"])}">'
             f'<div class="id">{e(f["id"])} &middot; {e(f["severity"])} &middot; {e(f["area"])}</div>'
             f'<h4>{e(f["title"])}</h4><p>{e(f["detail"])}</p>')
    if f.get("consequence"):
        b.append(f'<p><strong>Consequence:</strong> {e(f["consequence"])}</p>')
    if f.get("action"):
        b.append(f'<p class="act"><strong>Action:</strong> {e(f["action"])}</p>')
    if f.get("items"):
        b.append(f'<div class="controls"><input type="search" placeholder="Filter the {len(f["items"])} '
                 f'unverified rows..." data-filter="#t-f15"></div>')
        b.append('<div class="scroll"><table id="t-f15" data-sortable data-require-source><thead><tr><th>Sport</th><th>Event</th>'
                 '<th>Market</th><th>Listed time</th><th>As of</th><th>Retrieval</th>'
                 '<th>Why no line was originated</th><th>Provenance</th></tr></thead><tbody>')
        for it in f["items"]:
            b.append(f"""<tr data-sport="{e(it['sport'])}"><td>{e(it['sport'].replace('_', ' '))}</td>
<td><strong>{e(it['match'])}</strong></td><td>{e(it['market'])}</td>
<td class="small">{e(it['listed_time'])}</td><td class="small">{e(it['as_of'])}</td>
<td class="small">{e(it['retrieved_via'].replace('_', ' '))}</td>
<td class="small">{e(it['reason'])}</td><td>{src(it['source_url'], 'OLBG')}</td></tr>""")
        b.append('</tbody></table></div>')
    b.append('</div>')
open(DOCS / "flagged.html", "w").write(page("Flagged for Review", "flagged.html", "\n".join(b)))

# ---------------------------------------------------------------- excluded
b = ['<h2>Excluded sports</h2>',
     '<p class="lead">The brief excludes soccer, boxing, UFC, MMA, football, American football, hurling, horse '
     'racing, cycling and specials. Mapped against OLBG\'s own 22-sport taxonomy, seven OLBG sports fall out of '
     'scope. Two of those exclusions are judgement calls and are flagged.</p>',
     '<div class="scroll"><table data-sortable data-require-source><thead><tr><th>OLBG sport</th><th class="num">id</th>'
     '<th>Brief term that excludes it</th><th>Reasoning</th><th>Reference</th></tr></thead><tbody>']
MAP = {"Football": "soccer / football", "Horse_Racing": "horse racing",
       "American_Football": "american football", "Boxing": "boxing (and UFC / MMA)",
       "Cycling": "cycling", "Gaelic_Football": "football (judgement call)",
       "Greyhounds": "horse racing family (judgement call)"}
for s in excluded:
    b.append(f'<tr><td><strong>{e(s["name"])}</strong></td><td class="num">{e(s["olbg_sport_id"])}</td>'
             f'<td>{e(MAP.get(s["slug"], "&mdash;"))}</td><td class="small">{e(s["note"])}</td>'
             f'<td>{src("https://www.olbg.com/sitemap-betting-tips.xml", "OLBG sitemap")}</td></tr>')
b.append('</tbody></table></div>')
b.append('<div class="card"><h3>Brief terms with no OLBG counterpart</h3><p class="small">OLBG has no separate '
         'sport node for <strong>UFC</strong>, <strong>MMA</strong>, <strong>Hurling</strong> or '
         '<strong>Specials</strong>, so those four exclusions are vacuous against OLBG\'s taxonomy. Combat sports '
         'sit under <code>Boxing</code> (id 16), which is excluded anyway. See '
         '<a href="flagged.html#F-05">F-05</a>.</p></div>')
b.append('<div class="note warn"><strong>Two decisions need your confirmation.</strong> '
         '<a href="flagged.html#F-03">F-03</a> &mdash; Greyhounds (id 28) and Gaelic Football (id 25) are not '
         'named in the brief. Greyhounds was excluded as a racing-family sport alongside horse racing, and Gaelic '
         'Football as a football code alongside soccer; neither fits the match-winner / handicap / total model the '
         'brief asks for. Both are a one-line change in <code>scripts/load_inventory.py</code> if you disagree.</div>')
open(DOCS / "excluded.html", "w").write(page("Excluded Sports", "excluded.html", "\n".join(b)))

(ASSETS / "style.css").write_text(CSS)
(ASSETS / "app.js").write_text(JS)
built = site_files()
print(f"built {len(built)} site files into survey/")
for p in built:
    print(f"  {p.relative_to(DOCS)!s:34s} {p.stat().st_size:7d} B")
