#!/usr/bin/env python3
"""Build the Layer-4 "live slate" dashboard at /live/ (session arena/d4b9d560-olbg2).

Reads  : data/live/lines.json, data/live/coverage.json, data/live/flags.json
Writes : live/index.html, live/picks.html, live/flagged.html, live/methodology.html,
         live/sports/<sport>.html, live/assets/style.css

The page set is self-contained: it does not modify the root dashboard, /site/ or
/survey/, it only links to them. Every fixture row renders the official source URL it
was captured from; rows with no official source are not rendered at all, and the
sports that could not be captured are listed on the flagged page instead.
"""
from __future__ import annotations

import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_DATA = os.path.join(ROOT, "data", "live")
OUT = os.path.join(ROOT, "live")

NAV = [
    ("index.html", "Live slate"),
    ("picks.html", "Picks &amp; predictions"),
    ("methodology.html", "Methodology"),
    ("flagged.html", "Flagged for review"),
]
CROSS = [
    ("../index.html", "Root dashboard"),
    ("../survey/index.html", "Survey (130 events)"),
    ("../site/index.html", "Evidence desk v2"),
]

CSS = """
:root{--bg:#0f1115;--card:#171a21;--line:#262b36;--text:#e8ebf0;--dim:#98a2b3;--acc:#4c8dff;
--high:#2ecc71;--med:#f1c40f;--low:#e67e22}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{padding:26px 30px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:23px}h2{font-size:18px;margin:30px 0 10px}
p{color:var(--dim);margin:6px 0}
nav{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px}
nav a{color:var(--acc);text-decoration:none}nav a:hover{text-decoration:underline}
main{padding:24px 30px 60px;max-width:1240px}
.cards{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;min-width:150px}
.card b{display:block;font-size:26px}
table{width:100%;border-collapse:collapse;margin:10px 0 26px;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;background:#12151b}
tr:hover td{background:#141821}
a{color:var(--acc)}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:700}
.high{background:rgba(46,204,113,.16);color:var(--high)}
.medium{background:rgba(241,196,15,.16);color:var(--med)}
.low{background:rgba(230,126,34,.16);color:var(--low)}
.muted{color:var(--dim)}.small{font-size:12.5px}
.quote{background:var(--card);border-left:3px solid var(--acc);padding:12px 16px;border-radius:6px;margin:10px 0}
footer{border-top:1px solid var(--line);padding:18px 30px;color:var(--dim);font-size:13px}
code{background:#12151b;padding:1px 5px;border-radius:4px}
"""


def esc(v):
    return html.escape("" if v is None else str(v))


def page(title, body, prefix=""):
    nav = " ".join('<a href="%s%s">%s</a>' % (prefix, h, l) for h, l in NAV)
    cross_prefix = "../" if prefix else ""
    cross = " ".join('<a href="%s%s">%s</a>' % (cross_prefix, h, l) for h, l in CROSS)
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><link rel="stylesheet" href="%sassets/style.css"></head>
<body><header><h1>%s</h1>
<p class="muted">OLBG2 &middot; Layer 4 live slate &middot; session <code>arena/d4b9d560-olbg2</code> &middot;
captured 2026-10-21 &middot; every row carries its official source link</p>
<nav>%s<span class="muted">|</span>%s</nav></header>
<main>%s</main>
<footer>Prices are originated by this project's own model, not copied from any bookmaker.
Unverified values are left blank and listed on the flagged page. Nothing is inferred to fill a gap.</footer>
</body></html>
""" % (esc(title), prefix, esc(title), nav, cross, body)


def slug(sport):
    return re.sub(r"[^a-z0-9]+", "-", sport.lower()).strip("-")


def money(market, row):
    out = []
    for sel, priced in market["options"].items():
        label = sel
        if market["type"] == "3-way" and sel == "draw":
            label = "Draw"
        elif sel in ("over", "under"):
            label = "%s %.1f" % (sel.capitalize(), market["line"])
        elif market["type"] in ("handicap", "run line") and sel in market.get("line", {}):
            label = "%s %+.1f" % (sel, market["line"][sel])
        out.append("%s <b>%s</b> (%.1f%%)" % (esc(label), esc(priced["american"]), priced["probability"] * 100))
    return "<br>".join(out)


def fixture_table(rows, show_sport=False):
    head = "<tr><th>Date</th>%s<th>Match</th><th>Venue</th><th>Match winner</th><th>Handicap</th><th>Total</th><th>Pick</th><th>Source</th></tr>" % (
        "<th>Sport</th>" if show_sport else ""
    )
    body = []
    for r in rows:
        pick = r["pick"]
        cells = [
            "<td>%s<br><span class='muted small'>%s</span></td>" % (esc(r["date"]), esc(r["time"])),
        ]
        if show_sport:
            cells.append("<td>%s</td>" % esc(r["sport"]))
        cells += [
            "<td><b>%s</b> @ <b>%s</b>%s</td>"
            % (esc(r["away_name"]), esc(r["home_name"]), "<br><span class='muted small'>%s</span>" % esc(r["detail"]) if r.get("detail") else ""),
            "<td>%s</td>" % esc(r["venue"]),
            "<td>%s</td>" % money(r["markets"]["match_winner"], r),
            "<td>%s</td>" % money(r["markets"]["handicap"], r),
            "<td>%s</td>" % money(r["markets"]["total"], r),
            "<td><span class='pill %s'>%s</span><br>%s<br><span class='muted small'>%.1f%% &middot; %s</span></td>"
            % (pick["confidence"], esc(pick["confidence"]), esc(pick["label"]), pick["probability"] * 100, esc(pick["american"])),
            "<td class='small'><a href='%s'>official source</a></td>" % esc(r["source_url"]),
        ]
        body.append("<tr>%s</tr>" % "".join(cells))
    return "<table>%s%s</table>" % (head, "".join(body))


def inputs_table(rows):
    body = []
    for r in rows:
        i = r["inputs"]
        flat = []
        for side in ("home", "away"):
            flat.append("%s: %s" % (side, ", ".join("%s=%s" % (k, v) for k, v in i[side].items())))
        body.append(
            "<tr><td>%s</td><td class='small'>%s</td><td class='small muted'>%s</td><td class='small'><a href='%s'>official source</a></td></tr>"
            % (esc(r["id"]), esc(" | ".join(flat)), esc(", ".join("%s=%s" % (k, v) for k, v in r["model"].items() if k != "name")), esc(i["source_url"]))
        )
    return (
        "<table><tr><th>Fixture</th><th>Inputs (official)</th><th>Model parameters</th><th>Source</th></tr>%s</table>"
        % "".join(body)
    )


def build():
    lines = json.load(open(os.path.join(LIVE_DATA, "lines.json")))
    coverage = json.load(open(os.path.join(LIVE_DATA, "coverage.json")))
    flags = json.load(open(os.path.join(LIVE_DATA, "flags.json")))
    rows = lines["rows"]

    os.makedirs(os.path.join(OUT, "sports"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    with open(os.path.join(OUT, "assets", "style.css"), "w") as fh:
        fh.write(CSS.strip() + "\n")

    sports = {}
    for r in rows:
        sports.setdefault(r["sport"], []).append(r)

    by_conf = {c: [r for r in rows if r["pick"]["confidence"] == c] for c in ("high", "medium", "low")}
    captured = [s for s in coverage["sports"] if s["status"] == "verified fixtures"]

    # ---- index
    cards = "".join(
        '<div class="card"><span class="muted small">%s</span><b>%s</b></div>' % (esc(k), esc(v))
        for k, v in [
            ("Fixtures captured", len(rows)),
            ("Market lines originated", sum(len(r["markets"]) for r in rows)),
            ("Sports with official sources", len(captured)),
            ("High-confidence picks", len(by_conf["high"])),
            ("Medium", len(by_conf["medium"])),
            ("Low", len(by_conf["low"])),
            ("Open flags", len(flags["flags"])),
        ]
    )
    sport_links = " &middot; ".join(
        '<a href="sports/%s.html">%s (%d)</a>' % (slug(s), esc(s), len(v)) for s, v in sorted(sports.items())
    )
    cover_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td class='small'>%s</td><td class='small'>%s</td></tr>"
        % (
            esc(s["sport"]),
            esc(s["status"]),
            esc(s["fixtures"]),
            esc(s["note"]),
            "<a href='%s'>source tried</a>" % esc(s["source_url"]) if s.get("source_url") else "<span class='muted'>none fetched</span>",
        )
        for s in coverage["sports"]
    )
    index = page(
        "Live slate - 2026-10-21",
        "<p>Fixtures captured on 2026-10-21 from official governing-body and league sources, with lines originated "
        "by this project's own model. Sports whose official source could not be reached are listed at the bottom and "
        "on the flagged page rather than filled in.</p>"
        '<div class="cards">%s</div>'
        "<h2>Sports covered</h2><p>%s</p>"
        "<h2>Every captured fixture</h2>%s"
        "<h2>Model inputs and parameters, per fixture</h2>%s"
        "<h2>Sport-by-sport capture status</h2>"
        "<table><tr><th>Sport</th><th>Status</th><th>Fixtures</th><th>Note</th><th>Source</th></tr>%s</table>"
        % (cards, sport_links, fixture_table(rows, True), inputs_table(rows), cover_rows),
    )

    # ---- per sport
    for sport, srows in sports.items():
        body = (
            "<p>%d fixtures, official source per row. Prices originated by this project's model.</p>"
            % len(srows)
            + fixture_table(srows)
            + "<h2>Inputs and model parameters</h2>"
            + inputs_table(srows)
        )
        with open(os.path.join(OUT, "sports", slug(sport) + ".html"), "w") as fh:
            fh.write(page("%s - live slate" % sport, body, prefix="../"))

    # ---- picks
    def fair_american(prob):
        return round(-100.0 / (1.0 / prob - 1.0)) if prob >= 0.5 else round((1.0 / prob - 1.0) * 100.0)

    pred_blocks_in, pred_blocks_out = [], []
    for r in by_conf["high"]:
        p = r["prediction"]
        am = fair_american(r["pick"]["probability"])
        in_band = -250 <= am <= 10000
        tag = ("<span class='pill high'>high</span> <span class='muted small'>in the -250...+10000 focus band</span>"
               if in_band else
               "<span class='pill high'>high</span> <span class='muted small'>outside the -250...+10000 focus band (chalk favourite)</span>")
        block = (
            "<div class='quote'><b>%s</b> &middot; %s @ %s &middot; %s "
            "<span class='muted small'>%.1f%% &middot; %s</span><p>%s</p>"
            "<p class='small muted'>Selection: %s. Words: %d. Facts from: <a href='%s'>official source</a>.</p></div>"
            % (
                esc(r["date"]), esc(r["away_name"]), esc(r["home_name"]), tag,
                r["pick"]["probability"] * 100, esc(r["pick"]["american"]),
                esc(p["text"]), esc(p["selection"]), p["words"], esc(r["source_url"]),
            )
        )
        (pred_blocks_in if in_band else pred_blocks_out).append(block)
    pick_rows = "".join(
        "<tr><td>%s</td><td>%s @ %s</td><td>%s</td><td><span class='pill %s'>%s</span></td><td>%.1f%%</td><td>%s</td><td class='small'><a href='%s'>official source</a></td></tr>"
        % (
            esc(r["date"]), esc(r["away_name"]), esc(r["home_name"]), esc(r["pick"]["label"]),
            r["pick"]["confidence"], r["pick"]["confidence"], r["pick"]["probability"] * 100,
            esc(r["pick"]["american"]), esc(r["source_url"]),
        )
        for r in rows
    )
    picks = page(
        "Picks and predictions",
        "<p>One match-winner pick per fixture with a confidence label "
        "(high = model probability &ge; 72%%, or &ge; 70%% with the fair no-vig price inside "
        "-250...+10000; medium 55-72%%; low &lt; 55%%). Written predictions accompany every "
        "high-confidence pick.</p><h2>All picks</h2>"
        "<table><tr><th>Date</th><th>Match</th><th>Pick</th><th>Confidence</th><th>Model probability</th><th>Price</th><th>Source</th></tr>%s</table>"
        "<h2>High-confidence predictions inside the -250...+10000 focus band (%d)</h2>%s"
        "<h2>High-confidence predictions outside the focus band (%d)</h2>"
        "<p class='small muted'>The brief asks for high-confidence generation to focus on fair prices between "
        "-250 and +10000. These are chalk favourites priced shorter than -250; their write-ups are retained for "
        "completeness and clearly labelled rather than passed off as in-band.</p>%s"
        % (pick_rows, len(pred_blocks_in), "".join(pred_blocks_in) or
           "<p class='small muted'>No in-band high-confidence picks on this slate.</p>",
           len(pred_blocks_out), "".join(pred_blocks_out)),
    )

    # ---- flagged
    flag_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td><b>%s</b><p class='small muted'>%s</p><p class='small muted'>Action: %s</p></td><td class='small'>%s</td></tr>"
        % (
            esc(f["id"]), esc(f["severity"]), esc(f["title"]), esc(f["detail"]), esc(f["action"]),
            "<br>".join("<a href='%s'>%s</a>" % (esc(u), esc(u[:78] + ("..." if len(u) > 78 else ""))) for u in f["sources"]),
        )
        for f in flags["flags"]
    )
    flagged = page(
        "Flagged for review",
        "<p>Irregularities found in this repository, values that could not be confirmed from an official source, and "
        "the limits of the model. Nothing here blocks the build; each item is listed with the source links needed to "
        "review it.</p><table><tr><th>Flag</th><th>Type</th><th>Finding</th><th>Sources</th></tr>%s</table>" % flag_rows,
    )

    # ---- methodology
    method = page(
        "Methodology",
        "<h2>What was captured, and from where</h2>"
        "<table><tr><th>Source</th><th>What it returned</th></tr>"
        "<tr><td class='small'><a href='https://stats.unitedrugby.com/match-centre/2026-27/5'>URC official match centre, Round 5</a></td>"
        "<td>8 fixtures with match ids, venues, local kick-off times, broadcasters, plus the Round 3 results panel</td></tr>"
        "<tr><td class='small'><a href='https://stats.unitedrugby.com/match-centre/table/2026-27'>URC official league table</a></td>"
        "<td>16 clubs: played, won, drawn, lost, bonus points, points for/against, difference, tries, form</td></tr>"
        "<tr><td class='small'><a href='https://statsapi.mlb.com/api/v1/schedule?sportId=1&amp;startDate=2026-10-22&amp;endDate=2026-10-26&amp;hydrate=team'>MLB official Stats API schedule</a></td>"
        "<td>3 World Series games with game ids, venues, UTC and local dates</td></tr>"
        "<tr><td class='small'><a href='https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&amp;season=2026&amp;standingsTypes=regularSeason'>MLB official Stats API standings</a></td>"
        "<td>Rays 98-64, 736 runs scored, 650 allowed; Brewers 103-59, 832 scored, 618 allowed</td></tr>"
        "<tr><td class='small'><a href='https://api-web.nhle.com/v1/score/2026-10-22'>NHL official score feed</a></td>"
        "<td>Cross-check of fixture ids 2026020154-2026020157, matchups, venues, start times and team records</td></tr>"
        "<tr><td class='small'><a href='https://api.nhle.com/stats/rest/en/team/summary?isAggregate=false&amp;isGame=false&amp;start=0&amp;limit=32&amp;sort=points&amp;factCayenneExp=gamesPlayed%3E=1&amp;cayenneExp=gameTypeId=2%20and%20seasonId%3C=20262027%20and%20seasonId%3E=20262027'>NHL official team summary</a></td>"
        "<td>30 of 32 clubs re-read; compared line by line with the published inputs (flag L01)</td></tr>"
        "<tr><td class='small'><a href='https://www.nba.com/games?date=2026-10-22'>NBA official games page</a></td>"
        "<td>Month calendar only; fixture list failed to render (flag L02)</td></tr>"
        "<tr><td class='small'><a href='https://www.atptour.com/en/scores/current'>ATP official scores</a></td>"
        "<td>In-play and finished matches; no upcoming fixture list (flag L03)</td></tr></table>"
        "<h2>How lines are originated</h2>"
        "<p><b>Rugby union.</b> Expected points are built from the official table: a club's points for per game and its "
        "opponent's points against per game, each scaled by the table's average scoring rate. The home side is then "
        "shifted by half the home advantage measured in the official Round 3 results (+4.81 points to the home side, -4.81 to the away side, from a mean home margin of +9.63 over 8 matches), so the expected total is not inflated. "
        "Match-winner prices use a normal model on the margin with the sample spread of those results (18.96 points); "
        "the draw price is the season draw rate read from the table (3 drawn matches in 24 played, 12.5%). Handicap and "
        "total prices use the same margin spread and a total spread of 12.93 points.</p>"
        "<p><b>Baseball.</b> Independent Poisson model on runs. Each side's run rate comes from the official standings "
        "(runs scored and allowed over 162 games) and is rescaled by the two finalists' own average run environment, so "
        "no league constant that was not captured is assumed. Tied scorelines are split 50/50 as extra innings. No home "
        "advantage is applied because no official home/away split was captured (flag L07).</p>"
        "<p><b>Pricing.</b> Fair prices are divided by 1.04, a disclosed 4% overround, then converted to American odds. "
        "<b>Confidence.</b> high = probability &ge; 0.72, or &ge; 0.70 with the fair no-vig price inside "
        "[-250, +10000]; medium 0.55-0.72, low &lt; 0.55 on the model probability of the match-winner "
        "selection.</p>"
        "<h2>Rules this layer follows</h2>"
        "<p>A value is published only when an official source returned it in this session's capture. Anything "
        "unreachable stays blank and appears on the flagged page. No value is inferred from memory, and no secondary "
        "outlet is used as a factual source.</p>",
    )

    pages = {
        "index.html": index,
        "picks.html": picks,
        "flagged.html": flagged,
        "methodology.html": method,
    }
    for name, content in pages.items():
        with open(os.path.join(OUT, name), "w") as fh:
            fh.write(content)

    # ---- link check: local hrefs must resolve, every fixture row must have a source
    broken = []
    for dirpath, _dirs, files in os.walk(OUT):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            text = open(path).read()
            for href in re.findall(r'href="([^"#]+)"', text):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                if not os.path.exists(os.path.normpath(os.path.join(dirpath, href))):
                    broken.append("%s -> %s" % (os.path.relpath(path, ROOT), href))
    missing_source = [r["id"] for r in rows if not r.get("source_url")]
    print("live_build: %d pages, %d fixtures, %d flags" % (len(pages) + len(sports), len(rows), len(flags["flags"])))
    if broken:
        raise SystemExit("broken local links: %s" % ", ".join(broken))
    if missing_source:
        raise SystemExit("fixtures without an official source URL: %s" % ", ".join(missing_source))
    print("live_build: 0 broken local links, every fixture row carries an official source URL")


if __name__ == "__main__":
    build()
