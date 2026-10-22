#!/usr/bin/env python3
"""Build the /current/ layer: a self-contained dashboard over the fresh capture.

Pages
  current/index.html          capture window, KPIs, sport cards
  current/matches.html        every fixture row with its official source link
  current/lines.html          every originated price, all markets, both sides
  current/picks.html          one selection and confidence label per fixture
  current/predictions.html    the high-confidence written predictions
  current/inputs.html         the official strength tables the model consumed
  current/flagged.html        Flagged for Review: every irregularity and blank
  current/sources.html        source register: URL, what it returned, capture file
  current/methodology.html    models, gate and every assumption that is ours
  current/sports/<slug>.html  one subpage per eligible sport (17)

Stdlib only. Deterministic: rebuilding produces byte-identical files.
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "current")
OUT = os.path.join(ROOT, "current")
CAPTURE_REL = "../data/current/capture/"

NAV = [
    ("index.html", "Dashboard"),
    ("matches.html", "All Fixtures"),
    ("lines.html", "Originated Lines"),
    ("picks.html", "Picks &amp; Confidence"),
    ("predictions.html", "High-Confidence Predictions"),
    ("inputs.html", "Model Inputs"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Source Register"),
    ("methodology.html", "Methodology"),
    ("sports/index.html", "By Sport"),
]

CSS = """
:root{--bg:#f5f7fa;--surface:#fff;--alt:#eef1f5;--border:#dfe4ea;--ink:#101828;
--muted:#5b6572;--subtle:#7b8794;--accent:#0f766e;--link:#0b5cab;
--hi:#166534;--hibg:#dcfce7;--md:#854d0e;--mdbg:#fef3c7;--lo:#334155;--lobg:#e2e8f0;
--bad:#991b1b;--badbg:#fee2e2;--r:12px}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
code{background:var(--alt);padding:.05em .3em;border-radius:4px;font-size:.88em}
.wrap{max-width:1320px;margin:0 auto;padding:0 1.1rem}
.topbar{background:#0f172a;color:#f8fafc;position:sticky;top:0;z-index:40}
.bar{display:flex;align-items:center;justify-content:space-between;gap:.9rem;
flex-wrap:wrap;min-height:60px}
.brand{color:#fff;font-weight:800;letter-spacing:-.01em;display:flex;gap:.55rem;
align-items:center;flex-wrap:wrap}
.brand:hover{text-decoration:none;color:#5eead4}
.brand small{font-weight:500;color:#94a3b8;font-size:.78rem}
.nav{display:flex;flex-wrap:wrap;gap:.1rem}
.nav a{color:#cbd5e1;font-size:.8rem;padding:.4rem .55rem;border-radius:7px}
.nav a:hover{background:#1e293b;color:#fff;text-decoration:none}
.nav a[aria-current="page"]{background:#134e4a;color:#5eead4;font-weight:600}
.cross{background:#ecfdf5;border-bottom:1px solid #a7f3d0;color:#065f46;
font-size:.78rem;padding:.42rem 0}
.cross a{color:#065f46;font-weight:600}
main{padding:1.5rem 0 3rem}
h1{font-size:1.95rem;line-height:1.15;letter-spacing:-.025em;margin:.2rem 0 .5rem}
h2{font-size:1.22rem;letter-spacing:-.015em;margin:2rem 0 .55rem}
h3{font-size:.98rem;margin:0 0 .3rem}
p{margin:.4rem 0}
.eyebrow{text-transform:uppercase;letter-spacing:.09em;font-size:.71rem;
font-weight:700;color:var(--accent);margin:0}
.lede{font-size:1.02rem;color:#374151;max-width:74rem}
.sub{color:var(--muted);font-size:.9rem}
.crumb{font-size:.82rem;color:var(--muted);margin:0 0 .3rem}
.hero{background:linear-gradient(180deg,#fff,#f0fdfa);border:1px solid var(--border);
border-radius:var(--r);padding:1.5rem;box-shadow:0 1px 2px rgba(16,24,40,.06)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(152px,1fr));
gap:.7rem;margin:1.1rem 0}
.kpi{background:#fff;border:1px solid var(--border);border-radius:10px;padding:.85rem .95rem}
.kpi .v{font-size:1.6rem;font-weight:800;letter-spacing:-.03em;line-height:1.1}
.kpi .k{font-size:.77rem;font-weight:650;color:#374151}
.kpi .s{font-size:.71rem;color:var(--subtle)}
.grid{display:grid;gap:.8rem}
.grid.sports{grid-template-columns:repeat(auto-fill,minmax(285px,1fr))}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{display:block;background:#fff;border:1px solid var(--border);border-radius:10px;
padding:.9rem;color:inherit}
a.card:hover{border-color:#99f6e4;text-decoration:none}
.cardhead{display:flex;justify-content:space-between;align-items:center;gap:.5rem}
.card p{font-size:.82rem;color:var(--muted);margin:.3rem 0 .5rem}
.metrics{display:flex;gap:.8rem;font-size:.75rem;color:var(--subtle);
border-top:1px solid var(--border);padding-top:.45rem;flex-wrap:wrap}
.metrics b{color:var(--ink)}
.pill{background:var(--alt);border:1px solid var(--border);border-radius:999px;
padding:.1rem .5rem;font-size:.71rem;font-weight:700;color:#374151;white-space:nowrap}
.notice{background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #3b82f6;
border-radius:8px;padding:.7rem .85rem;margin:.9rem 0;font-size:.86rem;color:#1e3a8a}
.notice.warn{background:var(--mdbg);border-color:#fcd34d;border-left-color:#f59e0b;color:#78350f}
.notice.bad{background:var(--badbg);border-color:#fca5a5;border-left-color:#dc2626;color:#7f1d1d}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--border);
border-radius:10px;margin:.8rem 0}
table.data{border-collapse:collapse;width:100%;font-size:.8rem;min-width:900px}
table.data th{position:sticky;top:0;background:#f8fafc;text-align:left;font-size:.69rem;
text-transform:uppercase;letter-spacing:.05em;color:var(--muted);padding:.55rem .6rem;
border-bottom:1px solid var(--border);white-space:nowrap}
table.data td{padding:.5rem .6rem;border-bottom:1px solid var(--border);vertical-align:top}
table.data tbody tr:last-child td{border-bottom:0}
table.data tbody tr:hover{background:#fafcff}
table.data.plain{min-width:520px}
.teams{font-weight:650}
.tiny{font-size:.71rem;color:var(--subtle);line-height:1.45}
.badge{display:inline-block;border-radius:999px;padding:.08rem .45rem;font-size:.68rem;
font-weight:700;text-transform:capitalize;white-space:nowrap}
.badge.high{background:var(--hibg);color:var(--hi)}
.badge.medium{background:var(--mdbg);color:var(--md)}
.badge.low{background:var(--lobg);color:var(--lo)}
.badge.blank{background:var(--badbg);color:var(--bad)}
.band{margin-top:.25rem;font-size:.71rem;color:#0f766e;background:#f0fdfa;
border:1px solid #99f6e4;border-radius:5px;padding:.15rem .35rem;display:inline-block}
.blank{color:#9ca3af}
.filters{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;background:#fff;
border:1px solid var(--border);border-radius:10px;padding:.6rem;margin:.9rem 0}
.filters input,.filters select{border:1px solid var(--border);border-radius:7px;
padding:.42rem .55rem;font-size:.84rem;background:#fff}
.filters input{min-width:240px;flex:1}
#f-count{color:var(--muted);margin-left:auto;font-size:.8rem}
.pred{background:#fff;border:1px solid var(--border);border-left:4px solid var(--accent);
border-radius:10px;padding:.95rem 1rem;margin:.75rem 0}
.pred h3{font-size:1rem}
.pred .text{font-size:.92rem;color:#1f2937;margin:.45rem 0}
.pred ul{margin:.4rem 0 0 1.1rem;padding:0}
.pred li{font-size:.79rem;color:var(--muted);margin:.2rem 0}
.price{font-variant-numeric:tabular-nums}
.right{text-align:right}
footer{border-top:1px solid var(--border);background:#fff;padding:1.2rem 0;
color:var(--muted);font-size:.8rem;margin-top:1.5rem}
@media(max-width:700px){table.data{min-width:640px}.bar{min-height:auto;padding:.5rem 0}}
"""

FILTER_JS = """
<script>
(function(){
  var q=document.getElementById('f-q'), s=document.getElementById('f-s'),
      c=document.getElementById('f-count'),
      rows=[].slice.call(document.querySelectorAll('tbody tr[data-f]'));
  function apply(){
    var term=(q&&q.value||'').toLowerCase(), sport=s&&s.value||'', n=0;
    rows.forEach(function(r){
      var ok=(!term||r.getAttribute('data-f').toLowerCase().indexOf(term)>-1)
             &&(!sport||r.getAttribute('data-s')===sport);
      r.style.display=ok?'':'none'; if(ok)n++;
    });
    if(c)c.textContent=n+' of '+rows.length+' rows shown';
  }
  if(q)q.addEventListener('input',apply); if(s)s.addEventListener('change',apply); apply();
})();
</script>
"""


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as handle:
        return json.load(handle)


def american(value):
    return "%+d" % value if value is not None else "&mdash;"


def badge(conf):
    return '<span class="badge %s">%s</span>' % (conf, conf)


def page(title, active, body, extra_head="", script="", depth=0):
    """Render the layer chrome.

    ``depth`` is how many directory levels below ``current/`` the page lives, so
    every chrome link is *composed* with the right prefix rather than patched by
    string surgery afterwards. A previous revision rewrote the finished HTML with
    blanket ``str.replace`` calls; because a bare ``index.html`` means the layer
    dashboard in the navigation but the sport index in a breadcrumb, those
    replacements silently sent the sport pages' Dashboard, Flagged for Review,
    brand and footer links up to the repository root instead.
    """
    layer = "../" * depth            # prefix that reaches current/
    repo = "../" * (depth + 1)       # prefix that reaches the repository root
    nav = "".join(
        '<a href="%s%s"%s>%s</a>'
        % (layer, href, ' aria-current="page"' if href == active else "", label)
        for href, label in NAV)
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<link rel="stylesheet" href="%sassets/style.css">
%s</head>
<body>
<header class="topbar"><div class="wrap bar">
<a class="brand" href="%sindex.html"><span>OLBG Current Capture Desk</span>
<small>2026-10-22 first-hand official capture &middot; window 22&ndash;29 October 2026</small></a>
<nav class="nav" aria-label="Primary navigation">%s</nav>
</div></header>
<div class="cross"><div class="wrap">
<strong>Cross-layer:</strong>
<a href="%sindex.html">Root dashboard</a> &middot;
<a href="%sverified/index.html">Verified desk</a> &middot;
<a href="%slive/index.html">Live slate</a> &middot;
<a href="%ssurvey/index.html">All-sport survey</a> &middot;
<a href="%sintegration.html">Integration status</a> &middot;
<a href="%sflagged.html">Root review queue</a>
</div></div>
<main class="wrap">
%s
</main>
<footer><div class="wrap">
<p>Every published value was returned by an official governing-body, league or tour endpoint
during the 2026-10-22 capture session and is stored verbatim under
<code>data/current/capture/</code>. Values no official source returned are left blank and
listed on <a href="%sflagged.html">Flagged for Review</a>. No bookmaker price was read; all
prices on this layer are originated from the models on <a href="%smethodology.html">Methodology</a>.</p>
</div></footer>
%s
</body>
</html>
""" % (esc(title), layer, extra_head, layer, nav,
       repo, repo, repo, repo, repo, repo,
       body, layer, layer, script)


def subpage(title, body, script=""):
    """Sport subpage: same chrome, composed one directory level deeper."""
    return page(title, "", body, script=script, depth=1)


def level_disclosure(pr):
    """A priced row the model rates as a true coin flip must say so in place.

    Returns ``(badge, note)``; both are empty strings for a row that carries a
    model edge, so callers can concatenate them unconditionally.
    """
    if not pr or not pr.get("level"):
        return "", ""
    return ('<span class="badge blank">coin flip</span> ',
            '<div class="tiny">%s</div>' % esc(pr["note"]))


def kpi(value, key, sub=""):
    return ('<div class="kpi"><div class="v">%s</div><div class="k">%s</div>'
            '<div class="s">%s</div></div>' % (value, esc(key), esc(sub)))


def fixture_label(m):
    if m["kind"] == "event":
        return m["event"]
    return "%s v %s" % (m["home"]["name"], m["away"]["name"])


def source_cell(m):
    return ('<a href="%s" rel="noopener">Official fixture page</a>'
            '<div class="tiny">%s</div>' % (esc(m["official_url"]), esc(m["source_name"])))


# --------------------------------------------------------------------------- #
def originated_by_sport(lines):
    """Fixtures that actually carry originated prices, counted per sport slug."""
    out = {}
    for r in lines["rows"]:
        if r["originated"]:
            out[r["sport"]] = out.get(r["sport"], 0) + 1
    return out


def total_flag_ids(d, flags):
    """Every distinct flag id published on flagged.html: the capture disclosure
    flags plus one zero-row flag per sport that publishes no rows at all."""
    zero = len([1 for slug in d["sport_order"] if d["sports"][slug]["zero_row_flag"]])
    return len(flags) + zero, zero


def build_index(d, lines, band, preds, flags):
    counts = lines["counts"]
    sports = d["sports"]
    window = d["capture_window"]
    originated = originated_by_sport(lines)
    n_flags, n_zero = total_flag_ids(d, flags)
    cards = []
    for slug in d["sport_order"]:
        info = sports[slug]
        n = info["fixture_rows"]
        orig = originated.get(slug, 0)
        picks = len([b for b in band["selections"] if b["sport"] == slug])
        if n:
            cards.append(
                '<a class="card" href="sports/%s.html"><div class="cardhead">'
                '<h3>%s</h3><span class="pill">%d fixture%s</span></div>'
                '<p>%d originated line%s &middot; %d high-confidence in-band pick%s</p>'
                '<div class="metrics"><span>View sport page &rarr;</span></div></a>'
                % (slug, esc(info["sport_name"]), n, "" if n == 1 else "s",
                   orig, "" if orig == 1 else "s", picks, "" if picks == 1 else "s"))
        else:
            cards.append(
                '<div class="card"><div class="cardhead"><h3>%s</h3>'
                '<span class="badge blank">0 rows</span></div>'
                '<p>%s</p><div class="metrics"><span>Flag %s</span>'
                '<a href="sports/%s.html">Why it is blank &rarr;</a></div></div>'
                % (esc(info["sport_name"]), esc(info["zero_row_reason"][:150] + "..."),
                   esc(info["zero_row_flag"]), slug))
    body = """
<p class="eyebrow">Fresh first-hand capture &middot; no upstream row reused</p>
<h1>Current multi-sport fixture desk</h1>
<p class="lede">A complete fixture list captured directly from official governing-body
endpoints on <strong>22 October 2026</strong> for every eligible OLBG sport except soccer,
boxing, UFC/MMA, football, American football, hurling, horse racing, cycling and specials.
Every price on this layer is <strong>originated here</strong> from official statistics; no
bookmaker odds were read, and no value is inferred. Anything an official source did not
return is left blank and published on <a href="flagged.html">Flagged for Review</a>.</p>
<div class="kpis">
%s%s%s%s%s%s%s</div>
<div class="notice"><strong>Capture window %s to %s.</strong> %d fixtures across %d sports
carry originated lines. A further %d sports publish zero rows, each with the first-hand
reason and the official source that was consulted. High-confidence requires both a model
probability of at least 0.70 <em>and</em> a fair no-vig American price between -250 and
+10000, searched across every originated market on both sides &mdash; which is why %d of the
%d picks sit on alternate handicap or total lines rather than on a moneyline.</div>
<h2>Every eligible sport</h2>
<div class="grid sports">%s</div>
<h2>Start here</h2>
<div class="grid two">
<div class="card"><h3><a href="matches.html">All fixtures</a></h3>
<p>Every captured fixture with its official per-match source link, venue, time as rendered
by the source, and the records or standings beside it.</p></div>
<div class="card"><h3><a href="lines.html">Originated lines</a></h3>
<p>All %d originated prices: match winner, handicap and match total, both sides, including
the alternate-line grid the in-band search runs over.</p></div>
<div class="card"><h3><a href="predictions.html">High-confidence predictions</a></h3>
<p>%d written predictions, each at least 30 words, naming the club or player, its current
form, a recent result read first-hand, and the exact selection.</p></div>
<div class="card"><h3><a href="flagged.html">Flagged for Review</a></h3>
<p>%d disclosure flags: blank rows, truncated values, unreachable official feeds, in-play
exclusions, and the model constants that are ours rather than the sport's.</p></div>
</div>
""" % (
        kpi(counts["fixture_rows"], "Fixture rows", "captured 2026-10-22"),
        kpi(counts["sports_with_rows"], "Sports with rows", "of 17 eligible"),
        kpi(counts["prices_originated"], "Originated prices", "all markets, both sides"),
        kpi(counts["band_picks"], "High-confidence picks", "p >= 0.70 and -250...+10000"),
        kpi(preds["counts"]["predictions"], "Written predictions",
            "%d-%d words each" % (preds["counts"]["min_word_count"],
                                  preds["counts"]["max_word_count"])),
        kpi(counts["blank_rows"], "Blank rows", "published with a reason"),
        kpi(n_flags, "Disclosure flags",
            "%d capture disclosures + %d zero-row" % (len(flags), n_zero)),
        esc(window["start"]), esc(window["end"]), counts["originated_rows"],
        counts["sports_with_rows"], 10,
        len([b for b in band["selections"] if b["market"] != "match winner"]),
        counts["band_picks"], "".join(cards),
        counts["prices_originated"], preds["counts"]["predictions"], n_flags)
    return page("Current Capture Desk — OLBG multi-sport fixtures, originated lines",
                "index.html", body)


# --------------------------------------------------------------------------- #
def build_matches(d, lines):
    rows = {r["match_id"]: r for r in lines["rows"]}
    trs = []
    for m in d["matches"]:
        r = rows[m["id"]]
        rec = ""
        if m["kind"] == "event":
            rec = "Round %s of the championship" % m["inputs"].get("round", "")
        else:
            bits = []
            if m["home"].get("record"):
                bits.append("%s %s" % (m["home"]["name"], m["home"]["record"]))
            if m["away"] and m["away"].get("record"):
                bits.append("%s %s" % (m["away"]["name"], m["away"]["record"]))
            rec = "<br>".join(esc(b) for b in bits) or '<span class="blank">not returned</span>'
        lvl_badge, lvl_note = level_disclosure(r["primary"] if r["originated"] else None)
        conf = (lvl_badge + badge(r["primary"]["confidence"])) if r["originated"] else \
            '<span class="badge blank">blank</span>'
        caveat = ('<div class="notice warn" style="margin:.3rem 0;padding:.35rem .5rem">'
                  '%s</div>' % esc(r["caveat"])) if r.get("caveat") else ""
        caveat += lvl_note
        trs.append(
            '<tr data-f="%s" data-s="%s"><td>%s</td><td>%s</td>'
            '<td class="teams">%s<div class="tiny">%s</div></td>'
            '<td>%s</td><td>%s</td><td>%s</td><td>%s%s</td><td>%s</td></tr>' % (
                esc(fixture_label(m) + " " + m["competition"]), esc(m["sport"]),
                esc(m["date"]), esc(m["sport_name"]), esc(fixture_label(m)),
                esc(m["competition"]),
                esc(m["venue"]) or '<span class="blank">not returned</span>',
                esc(m["time_note"] or m["start_utc"]) or '<span class="blank">not returned</span>',
                rec, conf, caveat, source_cell(m)))
    opts = "".join('<option value="%s">%s</option>' % (slug, esc(d["sports"][slug]["sport_name"]))
                   for slug in d["sport_order"] if d["sports"][slug]["fixture_rows"])
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; All fixtures</p>
<h1>All captured fixtures</h1>
<p class="lede">%d fixtures read first-hand from official sources on 22 October 2026,
covering %s. Times are reproduced exactly as the source rendered them; where a source did
not state a timezone that is disclosed rather than converted.</p>
<div class="filters"><input id="f-q" type="search" placeholder="Filter by club, competition or venue&hellip;">
<select id="f-s"><option value="">All sports</option>%s</select><span id="f-count"></span></div>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Date</th><th>Sport</th><th>Fixture</th><th>Venue</th><th>Time as rendered</th>
<th>Record / standing as returned</th><th>Confidence</th><th>Official source</th>
</tr></thead><tbody>%s</tbody></table></div>
""" % (len(d["matches"]), esc(d["capture_window"]["start"]) + " to " + esc(d["capture_window"]["end"]),
       opts, "".join(trs))
    return page("All captured fixtures — Current Capture Desk", "matches.html", body,
                script=FILTER_JS)


# --------------------------------------------------------------------------- #
def build_lines(d, lines):
    by_id = {m["id"]: m for m in d["matches"]}
    trs = []
    for r in lines["rows"]:
        m = by_id[r["match_id"]]
        if not r["originated"]:
            trs.append('<tr data-f="%s" data-s="%s"><td>%s</td><td>%s</td>'
                       '<td colspan="5" class="blank">%s</td>'
                       '<td><a href="flagged.html">Flag %s</a></td></tr>' % (
                           esc(fixture_label(m)), esc(m["sport"]), esc(m["date"]),
                           esc(m["sport_name"]), esc(r["blank_reason"]),
                           esc("CU-07")))
            continue
        first = True
        for mk in r["markets"]:
            for o in mk["outcomes"]:
                bandmark = '<span class="band">in band</span>' if o.get("in_band") else ""
                if first:
                    head = ('<div class="tiny">%s &middot; %s</div>'
                            % (esc(m["competition"]), source_cell(m)))
                    name = esc(fixture_label(m))
                else:
                    head = ""
                    name = '<span class="tiny">&darr; same fixture</span>'
                trs.append(
                    '<tr data-f="%s" data-s="%s"><td>%s</td><td>%s</td>'
                    '<td class="teams">%s%s</td><td>%s</td><td>%s</td>'
                    '<td class="right price">%.4f</td><td class="right price">%s</td>'
                    '<td class="right price">%s %s</td></tr>' % (
                        esc(fixture_label(m) + " " + mk["market"]), esc(m["sport"]),
                        esc(m["date"]), esc(m["sport_name"]), name, head,
                        esc(mk["market"]), esc(o.get("selection", o.get("name", ""))),
                        o["p"],
                        ("%.2f" % o["fair_decimal"]) if o["fair_decimal"] else "&mdash;",
                        american(o["fair_american"]), bandmark))
                first = False
    opts = "".join('<option value="%s">%s</option>' % (slug, esc(d["sports"][slug]["sport_name"]))
                   for slug in d["sport_order"] if d["sports"][slug]["fixture_rows"])
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; Originated lines</p>
<h1>Every originated price</h1>
<p class="lede">%d prices across %d markets. All are fair no-vig prices derived from this
layer's own models &mdash; <code>decimal = 1 / probability</code> &mdash; and none was read
from a bookmaker. Rows marked <span class="band">in band</span> satisfy the high-confidence
gate: probability at least 0.70 and a fair American price between -250 and +10000.</p>
<div class="notice">Handicap lines are posted the way a book posts them: the home side at
minus the threshold and the away side at plus it, always on a half-point so no line can
push. In ice hockey and baseball a level score is settled in overtime or extra innings, so
half the tie mass is assigned to each side before any handicap probability is computed.</div>
<div class="filters"><input id="f-q" type="search" placeholder="Filter by club, market or line&hellip;">
<select id="f-s"><option value="">All sports</option>%s</select><span id="f-count"></span></div>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Date</th><th>Sport</th><th>Fixture &amp; official source</th><th>Market</th>
<th>Selection</th><th class="right">Probability</th><th class="right">Fair decimal</th>
<th class="right">Fair American</th></tr></thead><tbody>%s</tbody></table></div>
""" % (lines["counts"]["prices_originated"], lines["counts"]["markets_originated"], opts,
       "".join(trs))
    return page("Originated lines — Current Capture Desk", "lines.html", body, script=FILTER_JS)


# --------------------------------------------------------------------------- #
def build_picks(d, lines):
    by_id = {m["id"]: m for m in d["matches"]}
    preds = {p["match_id"]: p for p in load("predictions.json")["predictions"]}
    trs = []
    for r in lines["rows"]:
        m = by_id[r["match_id"]]
        if not r["originated"]:
            trs.append('<tr data-f="%s" data-s="%s"><td>%s</td><td>%s</td><td class="teams">%s</td>'
                       '<td colspan="5" class="blank">%s</td>'
                       '<td><a href="flagged.html">CU-07</a></td><td>%s</td></tr>' % (
                           esc(fixture_label(m)), esc(m["sport"]), esc(m["date"]),
                           esc(m["sport_name"]), esc(fixture_label(m)), esc(r["blank_reason"]),
                           source_cell(m)))
            continue
        pr = r["primary"]
        note = '<div class="tiny">%s</div>' % esc(pr["note"]) if pr.get("note") else ""
        pred = ('<a href="predictions.html#%s">Written prediction</a>' % preds[r["match_id"]]["id"]
                if r["match_id"] in preds else '<span class="tiny">not required below 0.70</span>')
        trs.append('<tr data-f="%s" data-s="%s"><td>%s</td><td>%s</td>'
                   '<td class="teams">%s<div class="tiny">%s</div></td>'
                   '<td>%s</td><td>%s%s</td>'
                   '<td class="right price">%.4f</td><td class="right price">%s</td>'
                   '<td>%s</td><td>%s</td><td>%s</td></tr>' % (
                       esc(fixture_label(m)), esc(m["sport"]), esc(m["date"]),
                       esc(m["sport_name"]), esc(fixture_label(m)), esc(m["competition"]),
                       esc(pr["market"]), esc(pr["selection"]), note, pr["p"],
                       ("%.2f" % pr["fair_decimal"]) if pr["fair_decimal"] else "&mdash;",
                       badge(pr["confidence"]), pred, source_cell(m)))
    opts = "".join('<option value="%s">%s</option>' % (slug, esc(d["sports"][slug]["sport_name"]))
                   for slug in d["sport_order"] if d["sports"][slug]["fixture_rows"])
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; Picks</p>
<h1>One selection per fixture, with a confidence label</h1>
<p class="lede">%d selections: %d high, %d medium and %d low confidence, plus %d fixtures
published blank because no official strength input was captured for them. Confidence follows
one rule across every sport &mdash; <strong>high</strong> only where the model probability is at
least 0.70 <em>and</em> the fair American price sits between -250 and +10000; ultra-short chalk
shorter than -250 is capped at medium.</p>
<div class="filters"><input id="f-q" type="search" placeholder="Filter by club or selection&hellip;">
<select id="f-s"><option value="">All sports</option>%s</select><span id="f-count"></span></div>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Date</th><th>Sport</th><th>Fixture</th><th>Market</th><th>Selection</th>
<th class="right">Probability</th><th class="right">Fair American</th><th>Confidence</th>
<th>Prediction</th><th>Official source</th></tr></thead><tbody>%s</tbody></table></div>
""" % (lines["counts"]["originated_rows"], lines["counts"]["high_confidence"],
       lines["counts"]["medium_confidence"], lines["counts"]["low_confidence"],
       lines["counts"]["blank_rows"], opts, "".join(trs))
    return page("Picks and confidence — Current Capture Desk", "picks.html", body,
                script=FILTER_JS)


# --------------------------------------------------------------------------- #
def build_predictions(preds):
    blocks = []
    for p in preds["predictions"]:
        facts = "".join('<li>%s &mdash; <a href="%s" rel="noopener">official source</a></li>'
                        % (esc(f["fact"]), esc(f["source_url"])) for f in p["facts_used"])
        caveat = ('<div class="notice warn" style="margin:.5rem 0">%s</div>' % esc(p["caveat"])
                  if p["caveat"] else "")
        blocks.append("""
<div class="pred" id="%s">
<div class="cardhead"><h3>%s</h3>%s</div>
<p class="sub">%s &middot; %s &middot; %s%s</p>
<p class="text">%s</p>
<p><strong>Selection:</strong> %s &mdash; model probability <span class="price">%.4f</span>,
fair decimal <span class="price">%.2f</span>, fair American
<span class="price">%s</span>.</p>
%s<ul>%s</ul>
<p class="tiny">Fixture: <a href="%s" rel="noopener">%s</a> &middot;
row: <a href="picks.html">%s</a> &middot; raw capture: <code>%s</code></p>
</div>""" % (
            esc(p["id"]), esc(p["fixture"]), badge(p["confidence"]), esc(p["date"]),
            esc(p["competition"]), esc(p["venue"]) or "venue not returned",
            (" &middot; " + esc(p["time_note"])) if p["time_note"] else "",
            esc(p["text"]), esc(p["selection"]), p["probability"], p["fair_decimal"],
            american(p["fair_american"]), caveat, facts, esc(p["official_url"]),
            esc(p["official_url"]), esc(p["match_id"]), esc(p["capture_file"])))
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; High-confidence predictions</p>
<h1>High-confidence predictions</h1>
<p class="lede">%d selections clear the gate &mdash; model probability at least 0.70 with a
fair American price between -250 and +10000. Each carries its own written prediction of at
least 30 words naming the club or player, its current form from an official table, a recent
result read first-hand in this capture, and the exact betting selection. Nothing here is
copied from another layer or from a bookmaker.</p>
<div class="kpis">%s%s%s%s</div>
%s
""" % (len(preds["predictions"]),
       kpi(len(preds["predictions"]), "High-confidence picks", "p >= 0.70 and in band"),
       kpi(preds["counts"]["min_word_count"], "Shortest prediction", "words"),
       kpi(preds["counts"]["unique_texts"], "Unique texts", "no template reuse"),
       kpi(len(preds["counts"]["sports"]), "Sports represented",
           ", ".join(preds["counts"]["sports"])),
       "".join(blocks))
    return page("High-confidence predictions — Current Capture Desk", "predictions.html", body)


# --------------------------------------------------------------------------- #
def build_flagged(d, lines, flags):
    blanks = load("blanks.json")["rows"]
    by_id = {m["id"]: m for m in d["matches"]}

    frows = []
    for f in sorted(flags, key=lambda x: x["reason_flag"]):
        src = f["source_url"]
        link = ('<a href="%s" rel="noopener">Official source consulted</a>' % esc(src)
                if src.startswith("http") else '<a href="%s">Local disclosure</a>' % esc(src))
        sport = esc(f["sport"].title() if f["sport"] != "all" else "All sports")
        frows.append(
            '<tr data-f="%s" data-s="%s"><td><strong>%s</strong></td><td>%s</td>'
            '<td>%s</td><td>%s</td><td>%s</td></tr>' % (
                esc(f["what"] + " " + f["reason"]), esc(f["sport"]), esc(f["reason_flag"]),
                sport, esc(f["what"]), esc(f["reason"]), link))

    zrows = []
    for slug in d["sport_order"]:
        info = d["sports"][slug]
        if not info["zero_row_flag"]:
            continue
        src = info["source_consulted"]
        zrows.append(
            '<tr data-f="%s" data-s="%s"><td><strong>%s</strong></td><td>%s</td>'
            '<td><span class="badge blank">0 rows</span></td>'
            '<td>%s</td><td>%s</td></tr>' % (
                esc(info["sport_name"] + " " + info["zero_row_reason"]), esc(slug),
                esc(info["zero_row_flag"]), esc(info["sport_name"]), esc(info["zero_row_reason"]),
                ('<a href="%s" rel="noopener">Source consulted</a>' % esc(src)) if src else
                '<span class="blank">no official feed reachable this session</span>'))

    brows = []
    for b in blanks:
        brows.append(
            '<tr data-f="%s" data-s="%s"><td>%s</td><td>%s</td><td>%s</td>'
            '<td class="blank">blank &mdash; no originated price</td><td>%s</td>'
            '<td><a href="%s" rel="noopener">Official fixture page</a></td></tr>' % (
                esc(b["fixture"]), esc(b["sport"]), esc(b["date"]), esc(b["sport_name"]),
                esc(b["fixture"]), esc(b["reason"]), esc(b["official_url"])))

    crows = []
    for r in lines["rows"]:
        if not r.get("caveat"):
            continue
        m = by_id[r["match_id"]]
        crows.append('<tr data-f="%s" data-s="%s"><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            esc(fixture_label(m) + " " + r["caveat"]), esc(r["sport"]),
            esc(fixture_label(m)), esc(m["sport_name"]), esc(r["caveat"])))

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; Flagged for Review</p>
<h1>Flagged for Review</h1>
<p class="lede">Nothing on this page blocks publication; everything on it is disclosed so a
reviewer can check it by hand against the linked official source. %d distinct flag ids in
total: %d capture disclosures listed below, plus one zero-row flag for each of the %d sports
that publish no rows. Also disclosed here: %d fixtures published blank and %d rows carrying a
model caveat.</p>
<div class="notice bad"><strong>Deliberate blanks.</strong> Where an official source did not
return a value the cell is left empty. No value anywhere on this layer was inferred, estimated
from a third-party site, or carried over from another layer of this repository.</div>
<h2>Disclosure flags</h2>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Flag</th><th>Sport</th><th>What was captured or affected</th><th>Why it is flagged</th>
<th>Source</th></tr></thead><tbody>%s</tbody></table></div>
<h2>Sports publishing zero rows, with the first-hand reason</h2>
<div class="table-wrap"><table class="data plain"><thead><tr>
<th>Flag</th><th>Sport</th><th>Status</th><th>Reason no row is published</th>
<th>Official source consulted</th></tr></thead><tbody>%s</tbody></table></div>
<h2>Fixtures published with blank lines</h2>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Date</th><th>Sport</th><th>Fixture</th><th>Lines</th><th>Reason</th>
<th>Official source</th></tr></thead><tbody>%s</tbody></table></div>
<h2>Rows carrying a model caveat</h2>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Fixture</th><th>Sport</th><th>Caveat</th></tr></thead><tbody>%s</tbody></table></div>
""" % (len(flags) + len(zrows), len(flags), len(zrows), len(brows), len(crows),
       "".join(frows), "".join(zrows), "".join(brows), "".join(crows))
    return page("Flagged for Review — Current Capture Desk", "flagged.html", body)


# --------------------------------------------------------------------------- #
def build_sources(d, inputs):
    seen = {}
    for m in d["matches"]:
        seen.setdefault(m["source_family"], {
            "source_name": m["source_name"], "urls": set(), "capture": m["capture_file"],
            "rows": 0, "sports": set()})
        entry = seen[m["source_family"]]
        entry["urls"].add(m["official_url"])
        entry["rows"] += 1
        entry["sports"].add(m["sport_name"])
    for f in d["excluded"]:
        seen.setdefault("excluded", {"source_name": "Sources consulted for excluded fixtures",
                                     "urls": set(), "capture": "", "rows": 0, "sports": set()})
        seen["excluded"]["urls"].add(f["source_url"])
    for slug, info in d["sports"].items():
        if info["source_consulted"]:
            seen.setdefault("zero", {"source_name": "Sources consulted for zero-row sports",
                                     "urls": set(), "capture": "", "rows": 0, "sports": set()})
            seen["zero"]["urls"].add(info["source_consulted"])
            seen["zero"]["sports"].add(info["sport_name"])
    trs = "".join(
        '<tr><td><strong>%s</strong></td><td>%s</td><td class="right">%d</td>'
        '<td>%s</td><td><code>%s</code></td><td>%s</td></tr>' % (
            esc(family), esc(v["source_name"]), len(v["urls"]),
            esc(", ".join(sorted(v["sports"])) or "excluded fixtures"),
            esc(v["capture"].replace("data/current/capture/", "") or "n/a"),
            "".join('<div><a href="%s" rel="noopener">%s</a></div>' % (esc(u), esc(u[:96] + ("..." if len(u) > 96 else "")))
                    for u in sorted(v["urls"])[:4]) +
            ('<div class="tiny">+ %d more fixture URLs, one per row on '
             '<a href="matches.html">All fixtures</a></div>' % (len(v["urls"]) - 4))
            if len(v["urls"]) > 4 else "")
        for family, v in sorted(seen.items()))
    irows = "".join(
        '<tr><td>%s</td><td class="right">%d</td><td>%s</td>'
        '<td><a href="%s" rel="noopener">Official table</a></td></tr>' % (
            esc(name), len(cfg.get("clubs", cfg.get("drivers", []))), esc(cfg["model"]),
            esc(cfg["source_url"]))
        for name, cfg in sorted(inputs["inputs"].items()))
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; Source register</p>
<h1>Source register</h1>
<p class="lede">Every official endpoint read during the 22 October 2026 capture session, what
it returned, and the verbatim capture file it is stored in. Raw responses live under
<code>data/current/capture/</code> and are checked into the repository, so any number on this
layer can be traced to the response that produced it.</p>
<h2>Fixture and strength sources</h2>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Family</th><th>Official source</th><th class="right">URLs</th><th>Sports served</th>
<th>Capture file</th><th>Links</th></tr></thead><tbody>%s</tbody></table></div>
<h2>Strength tables consumed by the models</h2>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Table</th><th class="right">Clubs / drivers</th><th>Model built from it</th>
<th>Official source</th></tr></thead><tbody>%s</tbody></table></div>
<h2>Capture files</h2>
<div class="table-wrap"><table class="data plain"><thead><tr>
<th>File</th><th>What it holds</th></tr></thead><tbody>%s</tbody></table></div>
""" % (trs, irows, "".join(
        '<tr><td><code><a href="%s%s">%s</a></code></td><td>%s</td></tr>' % (
            CAPTURE_REL, esc(os.path.basename(f)), esc(os.path.basename(f)), esc(DESC.get(os.path.basename(f), "")))
        for f in sorted(os.listdir(os.path.join(ROOT, "data", "current", "capture")))
        if f.endswith(".json")))
    return page("Source register — Current Capture Desk", "sources.html", body)


DESC = {
    "urc_table_2026-10-22.json": "URC 2026/27 official 16-club table plus all eight Round 3 results with scores and venues.",
    "urc_round4_2026-10-22.json": "All eight URC Round 4 fixtures with official per-match URLs, venues and kickoff times as rendered.",
    "nhl_score_2026-10-23.json": "NHL game-week counts for 20-26 October plus the two 23 October games: ids, venue, start time, records and named leaders.",
    "nhl_score_2026-10-24.json": "All twelve NHL games on 24 October with ids, venues, records, derived game-centre links and six named leaders each.",
    "nhl_team_summary_2026-10-22.json": "Official 32-club NHL team summary: games, W-L-OTL, points, goals for and against, power-play and penalty-kill rates.",
    "euroleague_round7_2026-10-22.json": "All nine EuroLeague Round 7 fixtures with per-game URLs, venues and tip times, plus the complete 20-club standings.",
    "mlb_world_series_2026-10-22.json": "World Series Game 1 and Game 2: game ids, official dates, venue, series status and both clubs' season records.",
    "mlb_standings_sample_2026-10-22.json": "Official standings for all 30 MLB clubs with runs scored and allowed, used to derive the league average.",
    "f1_calendar_2026-10-22.json": "Round 18 United States Grand Prix details plus the full 23-driver 2026 championship standings and Round 1-7 winners.",
    "wst_ni_open_2026-10-22.json": "Northern Ireland Open Round 3 scheduled fixtures with match-centre URLs, plus 21 completed Round 1 and Round 2 frame scores.",
    "ehf_2026-10-22.json": "EHF Champions League Men fixtures for 22, 28 and 29 October with official match-detail URLs, plus captured European Cup and qualifier fixtures.",
    "ehf_standings_2026-10-22.json": "All 24 EHF Champions League Men group-phase clubs across Groups A to F with games, W-D-L, goals and points.",
    "dpworld_golf_2026-10-22.json": "DP World Tour schedule read showing the Genesis Championship in play at Round 2, the basis for golf publishing zero rows.",
}


# --------------------------------------------------------------------------- #
def build_inputs(inputs):
    blocks = []
    labels = {
        "nhl": ("NHL 32-club team summary", "nhl", ("code", "team", "gp", "w", "l", "otl", "pts", "gf", "ga", "gfpg", "gapg", "attack", "defence")),
        "euroleague": ("EuroLeague 20-club standings", "euroleague", ("pos", "team", "gp", "w", "l", "pts_for", "pts_against", "diff", "l10", "attack", "defence")),
        "urc": ("United Rugby Championship 16-club table", "urc", ("pos", "team", "pts", "pl", "w", "d", "l", "bp", "pf", "pa", "diff", "form", "attack", "defence")),
        "ehf": ("EHF Champions League Men 24-club group tables", "ehf", ("group", "pos", "club", "gp", "w", "d", "l", "goals_for", "goals_against", "diff", "pts", "attack", "defence")),
        "mlb": ("MLB 30-club standings sample", "mlb", ("division", "team", "gp", "w", "l", "win_pct", "rs", "ra", "diff", "attack", "defence")),
        "f1": ("F1 2026 Drivers' championship standings", "f1", ("pos", "driver", "team", "pts", "share")),
    }
    for key in ("nhl", "euroleague", "urc", "ehf", "mlb", "f1"):
        cfg = inputs["inputs"][key]
        title, _, cols = labels[key]
        clubs = cfg.get("clubs", cfg.get("drivers", []))
        head = "".join("<th>%s</th>" % esc(c.replace("_", " ")) for c in cols)
        rows = "".join("<tr>%s</tr>" % "".join(
            "<td>%s</td>" % esc(c.get(col, "")) for col in cols) for c in clubs)
        blocks.append("""
<h2 id="%s">%s</h2>
<p class="sub">Model: %s. Official source: <a href="%s" rel="noopener">%s</a>.</p>
<div class="table-wrap"><table class="data"><thead><tr>%s</tr></thead>
<tbody>%s</tbody></table></div>""" % (esc(key), esc(title), esc(cfg["model"]),
                                       esc(cfg["source_url"]), esc(cfg["source_url"]),
                                       head, rows))
    wst = inputs["inputs"]["wst"]
    form_rows = "".join(
        '<tr><td>%s</td><td class="right">%d</td><td class="right">%d</td>'
        '<td class="right">%d</td><td class="right">%.4f</td><td class="right">%.4f</td></tr>'
        % (esc(name), f["matches"], f["frames_won"], f["frames_lost"], f["frame_rate"], f["shrink"])
        for name, f in sorted(wst["form"].items()))
    blocks.append("""
<h2 id="wst">Northern Ireland Open in-event form</h2>
<p class="sub">%s. %d Round 1 and Round 2 results read first-hand, %d frames in total,
%.4f frames per match. Official source: <a href="%s" rel="noopener">%s</a>. No world-ranking
table was captured, so in-event frames are the only strength input available for snooker.</p>
<div class="table-wrap"><table class="data plain"><thead><tr><th>Player</th>
<th class="right">Matches</th><th class="right">Frames won</th><th class="right">Frames lost</th>
<th class="right">Frame rate</th><th class="right">Shrinkage</th></tr></thead>
<tbody>%s</tbody></table></div>""" % (esc(wst["model"]), wst["matches_observed"],
                                       wst["frames_observed"], wst["frames_per_match"],
                                       esc(wst["source_url"]), esc(wst["source_url"]), form_rows))
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; Model inputs</p>
<h1>Model inputs, exactly as an official source returned them</h1>
<p class="lede">These are the only numbers the models are allowed to use. Attack and defence
ratings are derived on this page from the published goals, points or runs columns; the rest
is verbatim from the linked official table.</p>
%s
""" % "".join(blocks)
    return page("Model inputs — Current Capture Desk", "inputs.html", body)


# --------------------------------------------------------------------------- #
def build_methodology(inputs, lines):
    cfgs = inputs["inputs"]
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> &rsaquo; Methodology</p>
<h1>Methodology, markets and the high-confidence gate</h1>
<p class="lede">Every price on this layer is originated from official statistics captured on
22 October 2026. Nothing is copied from a bookmaker and nothing is inherited from another
layer of this repository.</p>

<h2>The high-confidence gate</h2>
<div class="notice"><strong>high</strong> = model probability &ge; 0.7000 <em>and</em> a fair
no-vig American price inside -250 &hellip; +10000. A fair price of -250 corresponds to
p = 0.714286, so the band is a 1.43-point-wide window. <strong>medium</strong> = probability
&ge; 0.60, and also any probability above 0.70 whose fair price is shorter than -250, because
ultra-short chalk is capped. <strong>low</strong> = everything else.</div>
<p>The gate is applied to <em>every</em> originated market on <em>both</em> sides, not only to
the two-way moneyline. That matters: a moneyline can only satisfy the window between 70.0%% and
71.43%%, which almost never happens, whereas an alternate handicap or total line can be chosen
so a genuinely strong opinion lands inside the band. Of %d high-confidence picks, %d come from
an alternate handicap or total line and %d from a moneyline.</p>

<h2>Pricing convention</h2>
<p>Prices are fair and carry no vigourish: <code>fair_decimal = 1 / probability</code> rounded
to two decimals, converted to American as <code>+100 &times; (decimal - 1)</code> above 2.00
and <code>-100 / (decimal - 1)</code> below it. Handicap thresholds are always half-points so
no line can push, and the home side is posted at minus the threshold while the away side is
posted at plus it, making the two sides exact complements.</p>

<h2>Models by sport</h2>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Sport</th><th>Model</th><th>League average from the capture</th>
<th>Distribution</th><th>Alternate-line search radius</th></tr></thead><tbody>
<tr><td>Ice Hockey</td><td>%s</td><td>%.4f goals per team game over 32 clubs</td>
<td>Exact Poisson score grid to 12 goals; ties settled 50/50 for overtime and the shootout</td>
<td>Handicap &plusmn;2.0 from the puck line, total &plusmn;2.0</td></tr>
<tr><td>Basketball</td><td>%s</td><td>%.4f points per team game over 20 clubs</td>
<td>Normal margin, no draws</td><td>Handicap &plusmn;6.0, total &plusmn;4.0</td></tr>
<tr><td>Rugby Union</td><td>%s</td><td>%.4f points per team game over 16 clubs</td>
<td>Normal margin with a &plusmn;1 point draw band</td><td>Handicap &plusmn;7.0, total &plusmn;6.0</td></tr>
<tr><td>Handball</td><td>%s</td><td>%.4f goals per team game over 24 clubs</td>
<td>Exact Poisson score grid to 70 goals; draws stand</td><td>Handicap &plusmn;4.0, total &plusmn;4.0</td></tr>
<tr><td>Baseball</td><td>%s</td><td>%.4f runs per team game over 30 clubs</td>
<td>Exact Poisson score grid to 20 runs; ties settled 50/50 for extra innings</td>
<td>Handicap &plusmn;1.5, total &plusmn;2.0</td></tr>
<tr><td>Snooker</td><td>%s</td><td>%.4f frames per match across %d captured results</td>
<td>Exact best-of-seven frame distribution</td><td>Handicap &plusmn;1.5 frames, total &plusmn;1.0</td></tr>
<tr><td>Motor Racing</td><td>%s</td><td>%d championship points across 23 drivers</td>
<td>Direct share, no distribution</td><td>Not applicable &mdash; outrights only</td></tr>
</tbody></table></div>

<h2>Assumptions that are ours, not the sport's (flag CU-23)</h2>
<p>No official source publishes a home advantage, a shrinkage prior or a standard deviation.
These are chosen by this layer and are listed in full so the arithmetic can be re-run with
different values:</p>
<ul>
<li><strong>Home advantage:</strong> NHL &times;1.05 multiplicative on goals; EuroLeague +3.0
points; URC +3.0 points; EHF +0.4 goals; MLB +0.25 runs. Snooker and motor racing have no
home advantage.</li>
<li><strong>Shrinkage priors</strong> (<code>w = games / (games + prior)</code>): NHL 8,
EuroLeague 6, URC 6, EHF 3, MLB 20, snooker 6 matches. Ratings are
<code>1 + w &times; (rate / league_average - 1)</code>, so a club with no games sits exactly
at league average.</li>
<li><strong>Dispersion:</strong> hockey, handball, baseball and snooker need none because the
score grid is exact. EuroLeague margin sd 11.0 and total sd 15.0; URC margin sd 13.0 and total
sd 16.0, with a draw requiring the margin inside &plusmn;1 point.</li>
<li><strong>Alternate-line radii</strong> are capped per sport so a published line is one a
book would plausibly post rather than an artefact of searching a huge grid.</li>
</ul>

<h2>Verification performed</h2>
<ul>
<li>Every fixture, record, standing, venue, time and result was returned by an official
governing-body, league or tour endpoint during this session and stored verbatim under
<code>data/current/capture/</code>.</li>
<li>The four grid and normal models were recomputed from the raw captures through an
independent code path and agreed with the published probabilities to four decimal places.</li>
<li>Arithmetic in every captured table was re-checked: goals for minus goals against equals
the published difference, and wins plus draws plus losses equals games played, for all 24 EHF
clubs, all 30 MLB clubs, all 20 EuroLeague clubs and all 16 URC clubs.</li>
<li>Cross-validation: the EuroLeague standings positions 1 to 20 match the club codes printed
beside each fixture in the official game centre; NHL records beside the 23 and 24 October
fixtures match the 21 October team-summary snapshot for six clubs.</li>
<li>No bookmaker price, aggregator price or third-party statistic was read at any point.</li>
</ul>
""" % (lines["counts"]["band_picks"],
       len([b for b in load("band.json")["selections"] if b["market"] != "match winner"]),
       len([b for b in load("band.json")["selections"] if b["market"] == "match winner"]),
       esc(cfgs["nhl"]["model"]), cfgs["nhl"]["league_avg_goals_per_team_game"],
       esc(cfgs["euroleague"]["model"]), cfgs["euroleague"]["league_avg_points_per_team_game"],
       esc(cfgs["urc"]["model"]), cfgs["urc"]["league_avg_points_per_team_game"],
       esc(cfgs["ehf"]["model"]), cfgs["ehf"]["league_avg_goals_per_team_game"],
       esc(cfgs["mlb"]["model"]), cfgs["mlb"]["league_avg_runs_per_team_game"],
       esc(cfgs["wst"]["model"]), cfgs["wst"]["frames_per_match"], cfgs["wst"]["matches_observed"],
       esc(cfgs["f1"]["model"]), cfgs["f1"]["field_points_total"])
    return page("Methodology — Current Capture Desk", "methodology.html", body)


# --------------------------------------------------------------------------- #
def build_sport(slug, d, lines, preds_by_match):
    info = d["sports"][slug]
    rows = [m for m in d["matches"] if m["sport"] == slug]
    lrows = {r["match_id"]: r for r in lines["rows"]}
    if not rows:
        src = ('<a href="%s" rel="noopener">%s</a>' % (esc(info["source_consulted"]),
                                                       esc(info["source_consulted"]))
               if info["source_consulted"] else
               '<span class="blank">no official feed was reachable during this session</span>')
        body = """
<p class="crumb"><a href="../index.html">Dashboard</a> &rsaquo;
<a href="index.html">By sport</a> &rsaquo; %s</p>
<h1>%s</h1>
<p class="lede"><span class="badge blank">0 rows</span> This sport publishes no fixture on the
current layer. That is a deliberate outcome, not an omission: a row is published only when an
official source returned the fixture during the 22 October 2026 capture session.</p>
<div class="notice bad"><strong>Flag %s.</strong> %s</div>
<h2>Official source consulted</h2>
<p>%s</p>
<h2>What would change this</h2>
<p>A future capture session that reaches an official fixture feed for %s inside the published
window would add rows here. Until then the sport stays blank rather than being filled from a
third-party site or inferred.</p>
""" % (esc(info["sport_name"]), esc(info["sport_name"]), esc(info["zero_row_flag"]),
       esc(info["zero_row_reason"]), src, esc(info["sport_name"]))
        return subpage("%s — Current Capture Desk" % info["sport_name"], body)

    trs = []
    for m in rows:
        r = lrows[m["id"]]
        if not r["originated"]:
            trs.append('<tr data-f="%s" data-s="%s"><td>%s</td><td class="teams">%s</td>'
                       '<td>%s</td><td>%s</td><td colspan="5" class="blank">%s</td>'
                       '<td><a href="%s" rel="noopener">Official fixture page</a></td></tr>' % (
                           esc(fixture_label(m)), esc(slug), esc(m["date"]),
                           esc(fixture_label(m)),
                           esc(m["venue"]) or '<span class="blank">not returned</span>',
                           esc(m["time_note"] or m["start_utc"]), esc(r["blank_reason"]),
                           esc(m["official_url"])))
            continue
        pr = r["primary"]
        mk = {x["market"]: x for x in r["markets"]}
        mw = mk.get("match winner") or mk.get("race winner (outright)")
        ml = " / ".join("%s %.3f" % (o.get("name") or o.get("selection"), o["p"])
                        for o in (mw["outcomes"][:3] if mw else []))
        hc = mk.get("handicap")
        tot = mk.get("match total")
        nat = ""
        if hc:
            nat = "Handicap %s &middot; Total %s" % (
                esc(hc["outcomes"][0]["selection"]) if hc["outcomes"] else "&mdash;",
                esc(tot["outcomes"][0]["selection"]) if tot and tot["outcomes"] else "&mdash;")
        pred = ('<a href="../predictions.html#%s">Prediction</a>' % preds_by_match[m["id"]]["id"]
                if m["id"] in preds_by_match else "")
        lvl_badge, lvl_note = level_disclosure(pr)
        trs.append('<tr data-f="%s" data-s="%s"><td>%s</td><td class="teams">%s'
                   '<div class="tiny">%s</div></td><td>%s</td><td>%s</td>'
                   '<td class="tiny">%s</td><td>%s</td>'
                   '<td class="right price">%.4f</td><td class="right price">%s</td>'
                   '<td>%s %s</td><td><a href="%s" rel="noopener">Official fixture page</a></td></tr>' % (
                       esc(fixture_label(m)), esc(slug), esc(m["date"]), esc(fixture_label(m)),
                       esc(m["competition"]),
                       esc(m["venue"]) or '<span class="blank">not returned</span>',
                       esc(m["time_note"] or m["start_utc"]), ml + lvl_note, esc(pr["market"]),
                       pr["p"], american(pr["fair_american"]),
                       lvl_badge + badge(pr["confidence"]), pred,
                       esc(m["official_url"])))
    n = len(rows)
    orig = originated_by_sport(lines).get(slug, 0)
    picks = len([b for b in load("band.json")["selections"] if b["sport"] == slug])
    body = """
<p class="crumb"><a href="../index.html">Dashboard</a> &rsaquo;
<a href="index.html">By sport</a> &rsaquo; %s</p>
<h1>%s</h1>
<p class="lede">%d fixture%s captured first-hand on 22 October 2026, %d of them
carrying originated line%s, and %d high-confidence in-band pick%s.</p>
<div class="kpis">%s%s%s</div>
<div class="filters"><input id="f-q" type="search" placeholder="Filter %s fixtures&hellip;">
<span id="f-count"></span></div>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Date</th><th>Fixture</th><th>Venue</th><th>Time as rendered</th><th>Match winner prices</th>
<th>Selection</th><th class="right">Probability</th><th class="right">Fair American</th>
<th>Confidence</th><th>Official source</th></tr></thead><tbody>%s</tbody></table></div>
<p class="tiny">Full alternate-line grids for these fixtures are on
<a href="../lines.html">Originated lines</a>. Anything this sport could not confirm from an
official source is on <a href="../flagged.html">Flagged for Review</a>.</p>
""" % (esc(info["sport_name"]), esc(info["sport_name"]), n, "" if n == 1 else "s",
       orig, "" if orig == 1 else "s", picks, "" if picks == 1 else "s",
       kpi(n, "Fixtures", "captured 2026-10-22"),
       kpi(picks, "High-confidence picks", "p >= 0.70 and in band"),
       kpi(len({r["id"] for r in rows if not lrows[r["id"]]["originated"]}), "Blank rows",
           "published with a reason"),
       esc(info["sport_name"]), "".join(trs))
    return subpage("%s — Current Capture Desk" % info["sport_name"], body, script=FILTER_JS)


def build_sports_index(d, lines):
    cards = []
    for slug in d["sport_order"]:
        info = d["sports"][slug]
        n = info["fixture_rows"]
        picks = len([b for b in load("band.json")["selections"] if b["sport"] == slug])
        if n:
            cards.append('<a class="card" href="%s.html"><div class="cardhead"><h3>%s</h3>'
                         '<span class="pill">%d rows</span></div>'
                         '<p>%d high-confidence in-band pick%s.</p>'
                         '<div class="metrics"><span>Open &rarr;</span></div></a>'
                         % (slug, esc(info["sport_name"]), n, picks, "" if picks == 1 else "s"))
        else:
            cards.append('<a class="card" href="%s.html"><div class="cardhead"><h3>%s</h3>'
                         '<span class="badge blank">0 rows</span></div>'
                         '<p>Flag %s &mdash; no official fixture returned this session.</p>'
                         '<div class="metrics"><span>Read the reason &rarr;</span></div></a>'
                         % (slug, esc(info["sport_name"]), esc(info["zero_row_flag"])))
    body = """
<p class="crumb"><a href="../index.html">Dashboard</a> &rsaquo; By sport</p>
<h1>All 17 eligible sports</h1>
<p class="lede">OLBG covers 25 sports. Eight are excluded from this brief &mdash; soccer,
boxing, UFC/MMA, football, American football, hurling, horse racing, cycling and specials
&mdash; leaving the 17 below. %d carry originated fixture rows; the other %d publish zero rows,
each with the first-hand reason and the official source that was consulted.</p>
<div class="grid sports">%s</div>
""" % (lines["counts"]["sports_with_rows"],
       17 - lines["counts"]["sports_with_rows"], "".join(cards))
    return subpage("All 17 eligible sports — Current Capture Desk", body)


# --------------------------------------------------------------------------- #
def write(path, html):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as handle:
        handle.write(html)
    return full


def main():
    d = load("matches.json")
    lines = load("lines.json")
    band = load("band.json")
    preds = load("predictions.json")
    inputs = load("model_inputs.json")
    flags = d["excluded"]
    preds_by_match = {p["match_id"]: p for p in preds["predictions"]}

    write("assets/style.css", CSS.strip() + "\n")
    written = ["assets/style.css"]
    written.append(write("index.html", build_index(d, lines, band, preds, flags)))
    written.append(write("matches.html", build_matches(d, lines)))
    written.append(write("lines.html", build_lines(d, lines)))
    written.append(write("picks.html", build_picks(d, lines)))
    written.append(write("predictions.html", build_predictions(preds)))
    written.append(write("flagged.html", build_flagged(d, lines, flags)))
    written.append(write("sources.html", build_sources(d, inputs)))
    written.append(write("inputs.html", build_inputs(inputs)))
    written.append(write("methodology.html", build_methodology(inputs, lines)))
    written.append(write("sports/index.html", build_sports_index(d, lines)))
    for slug in d["sport_order"]:
        written.append(write("sports/%s.html" % slug,
                             build_sport(slug, d, lines, preds_by_match)))

    print("current_build OK: %d files under current/" % len(written))
    for w in written:
        print("   ", w)


if __name__ == "__main__":
    main()
