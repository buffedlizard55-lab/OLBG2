#!/usr/bin/env python3
"""Build the /relay/ GitHub Pages layer for session arena/103d996c-olbg2.

Reads data/relay/*.json and writes a self-contained desk under relay/:
landing dashboard, all fixtures, originated lines, picks, predictions,
model inputs, flagged-for-review, source register, methodology and per-sport
subpages. The stylesheet is imported from scripts/current_build.py so the
layer matches the house look. Stdlib only, deterministic output.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from current_build import CSS  # noqa: E402  (house stylesheet)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "relay")
OUT = os.path.join(ROOT, "relay")

SPORTS_IN_SCOPE = [
    ("Ice Hockey", "ice-hockey"), ("Basketball", "basketball"),
    ("Rugby Union", "rugby-union"), ("Handball", "handball"),
    ("Baseball", "baseball"), ("Snooker", "snooker"), ("Tennis", "tennis"),
    ("Darts", "darts"), ("Cricket", "cricket"), ("Motor Racing", "motor-racing"),
    ("Golf", "golf"), ("Rugby League", "rugby-league"),
    ("Aussie Rules", "aussie-rules"), ("Volleyball", "volleyball"),
    ("Gaelic Football", "gaelic-football"), ("Greyhounds", "greyhounds"),
    ("eSports", "esports"),
]

ZERO_ROW_REASONS = {
    "snooker": ("The BetVictor Northern Ireland Open Round 3 fixtures all fell on 22 "
                "October and were in play or finished at capture time; the Round 4 draw "
                "could not be read because the fetch proxy failed on the later chunks of "
                "wst.tv/matches. Flag RL-08."),
    "tennis": ("The ATP official scores page was read first-hand on 22 October (Round of "
               "16 results from Vienna, Brussels and Lyon) but the upcoming-schedule chunks "
               "could not be retrieved, so no future fixture could be published. Flag RL-09."),
    "darts": ("pdc.tv confirms the 2026 European Championship is live (tournament hub "
              "10870), but the hub's draw and results are JavaScript-rendered and were not "
              "extractable, so no fixture could be published. Flag RL-10."),
    "cricket": ("icc-cricket.com/en/matches returned HTTP 404 and the match-list route "
                "could not be reached through the fetch proxy. Flag RL-11."),
    "golf": ("The DP World Tour's current event (Genesis Championship, Korea) was already "
             "in play at capture time and no finished future field could be verified. "
             "Flag RL-12."),
    "rugby-league": ("No official fixture feed could be verified in this session; the "
                     "/current/ layer's reason (domestic seasons concluded, 2027 fixtures "
                     "unpublished) stands. Flag RL-12."),
    "aussie-rules": ("The 2026 AFL season is concluded and no official 2027 fixture could "
                     "be verified in this session. Flag RL-12."),
    "volleyball": ("No official club-competition fixture feed could be verified in this "
                   "session. Flag RL-12."),
    "gaelic-football": ("No official county or club fixture could be verified in this "
                        "session. Flag RL-12."),
    "greyhounds": ("No official fixture feed could be verified in this session. Flag RL-12."),
    "esports": ("No official league fixture feed could be verified in this session. "
                "Flag RL-12."),
}

FLAGS = [
    ("RL-01", "Fetch-proxy outage limited first-hand re-verification",
     "The agent web-fetch tool failed intermittently all session (proxy SignatureDoesNotMatch; "
     "endpoints that never returned: api.nhle.com, stats.nba.com, cdn.nba.com HTTP 500, "
     "icc-cricket.com match-list, later chunks of wst.tv and atptour.com pages). Endpoints read "
     "first-hand this session: api-web.nhle.com score feeds for 23 and 24 October, "
     "statsapi.mlb.com schedule, atptour.com scores (results only), pdc.tv tournaments, "
     "wst.tv/matches (completed matches only), icc-cricket.com (404). 9 of 38 rows are class A; "
     "29 rows are class B carry-overs from the /current/ session's verbatim captures."),
    ("RL-02", "NHL strength table is a 2026-10-21 snapshot",
     "GF/GA ratings come from the official team-summary capture read 2026-10-22 12:26 UTC, which "
     "excludes the twelve games played on the evening of 22 October. W-L-OTL records are as "
     "printed by the official feed at 20:56 UTC on 22 October. Disclosed, not adjusted."),
    ("RL-03", "EHF group tables predate the 22 October round",
     "The 24-club standings capture (12:55 UTC) predates the five group matches played on the "
     "evening of 22 October, which involve several clubs in the 28-29 October fixtures priced "
     "here (MT Melsungen, Kolstad, Sporting, GOG, Kristianstad, Magdeburg, Barca, Montpellier, "
     "Szeged). Lines therefore rest on five-round form. Disclosed, not adjusted."),
    ("RL-04", "Three NHL games carry gameDate 2026-10-25 inside the 24 October slate",
     "Games 2026020177-179 start after midnight UTC (western venues) and the feed labels their "
     "gameDate 2026-10-25 while counting them in the twelve-game 24 October slate. Published "
     "exactly as the feed returned, with both the date label and the UTC start time."),
    ("RL-05", "Five-picks-per-sport unmet for Basketball",
     "Only three EuroLeague fixtures fall after capture time in the window; the NBA could not be "
     "read (cdn.nba.com HTTP 500, stats.nba.com unreachable), so three in-band picks are "
     "published for basketball instead of five."),
    ("RL-06", "No in-band pick for Baseball",
     "The only fixtures are World Series Games 1 and 2, which the model rates close to level; "
     "no originated market reaches p >= 0.70 inside the -250..+10000 band on either side. Both "
     "games publish their strongest two-way opinion capped at low/medium instead."),
    ("RL-07", "No in-band pick for Motor Racing",
     "The F1 outright is a share-of-championship-points price; the leader's share is far below "
     "70%, so nothing can enter the band. Published and labelled low, no per-circuit model "
     "claimed."),
    ("RL-08", "Snooker publishes zero rows", ZERO_ROW_REASONS["snooker"]),
    ("RL-09", "Tennis publishes zero rows", ZERO_ROW_REASONS["tennis"]),
    ("RL-10", "Darts publishes zero rows", ZERO_ROW_REASONS["darts"]),
    ("RL-11", "Cricket publishes zero rows", ZERO_ROW_REASONS["cricket"]),
    ("RL-12", "Six further sports publish zero rows without fresh probing",
     "Golf, Rugby League, Aussie Rules, Volleyball, Gaelic Football, Greyhounds and eSports "
     "could not be probed successfully while the fetch proxy was failing; the /current/ layer's "
     "reasons stand for this window and each sport page repeats them."),
    ("RL-13", "F1 race day derived from the rendered event dates",
     "The official calendar renders the United States round as '23 - 25 OCT'; this layer lists "
     "the race on 2026-10-25 (final day) as an assumption. Flagged, not verified."),
    ("RL-14", "World Series starters not used in the model",
     "The official schedule feed names no probable pitcher. MLB.com's official probable-pitcher "
     "pages (mlb.com/rays/roster/probable-pitchers, mlb.com/brewers/roster/probable-pitchers) "
     "list Jacob Misiorowski for Milwaukee with Tampa Bay TBD at capture time; press reports "
     "expect Drew Rasmussen but that is not official and is not used. Games 1 and 2 price "
     "identically."),
    ("RL-15", "Model parameters are assumptions",
     "Home advantages, shrinkage priors, standard deviations and draw bands are this layer's "
     "assumptions (identical to the /current/ layer and METHODOLOGY.md). No official source "
     "publishes them."),
    ("RL-16", "EHF venues blank",
     "The 28-29 October EHF fixture capture did not retain per-fixture venues, so venue cells "
     "are blank rather than inferred."),
    ("RL-17", "EuroLeague tip times are as rendered",
     "Tip times are printed without a timezone on the official game centre and are published "
     "as rendered."),
]

SOURCES = [
    ("NHL official API — score/schedule 2026-10-23",
     "https://api-web.nhle.com/v1/score/2026-10-23",
     "data/relay/capture/nhl_score_2026-10-23.json",
     "A — read first-hand 2026-10-22 20:56 UTC", "Two fixtures, records, team leaders"),
    ("NHL official API — score/schedule 2026-10-24",
     "https://api-web.nhle.com/v1/score/2026-10-24",
     "data/relay/capture/nhl_score_2026-10-24.json",
     "A — read first-hand 2026-10-22 20:57 UTC", "Five of the twelve-game slate with records and leaders"),
    ("MLB official Stats API — World Series schedule",
     "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-24",
     "data/relay/capture/mlb_world_series_2026-10-22.json",
     "A — read first-hand 2026-10-22 20:56 UTC", "Games 1 and 2, venues, game ids"),
    ("ATP Tour official scores page",
     "https://www.atptour.com/en/scores/current",
     "research/relay-103d996c.md (transcript excerpt)",
     "A — read first-hand 2026-10-22 20:58 UTC",
     "Round-of-16 results, Vienna/Brussels/Lyon; upcoming schedule not retrievable (RL-09)"),
    ("PDC tournaments page", "https://www.pdc.tv/tournaments/",
     "research/relay-103d996c.md (transcript excerpt)",
     "A — read first-hand 2026-10-22 21:01 UTC",
     "2026 European Championship live; hub 10870; draw not extractable (RL-10)"),
    ("World Snooker Tour matches page", "https://www.wst.tv/matches/",
     "research/relay-103d996c.md (transcript excerpt)",
     "A — read first-hand 2026-10-22 21:16 UTC",
     "NI Open completed Round 1/2 results; upcoming chunk not retrievable (RL-08)"),
    ("ICC matches route", "https://www.icc-cricket.com/en/matches",
     "research/relay-103d996c.md", "A — read first-hand 2026-10-22 21:02 UTC",
     "HTTP 404 — cricket publishes zero rows (RL-11)"),
    ("NHL official API — team summary (carried over)",
     "https://api.nhle.com/stats/rest/en/team/summary",
     "data/current/capture/nhl_team_summary_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:26 UTC",
     "32-club GF/GA ratings; 2026-10-21 snapshot (RL-02)"),
    ("NHL official API — 24 October slate (carried over)",
     "https://api-web.nhle.com/v1/score/2026-10-24",
     "data/current/capture/nhl_score_2026-10-24.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:32 UTC",
     "The seven 24 October fixtures not in this session's fresh capture (RL-04)"),
    ("URC official match centre, Round 4 (carried over)",
     "https://stats.unitedrugby.com/match-centre/2026-27/4",
     "data/current/capture/urc_round4_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:21 UTC",
     "Eight Round 4 fixtures"),
    ("URC official table (carried over)",
     "https://stats.unitedrugby.com/match-centre/table/2026-27",
     "data/current/capture/urc_table_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:20 UTC",
     "16-club table with form strings and Round 3 results"),
    ("EuroLeague official game centre and standings (carried over)",
     "https://www.euroleaguebasketball.net/en/euroleague/game-center/",
     "data/current/capture/euroleague_round7_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:40 UTC",
     "Round 7 fixtures and the 20-club standings"),
    ("EHF Champions League official fixtures (carried over)",
     "https://ehfcl.eurohandball.com/",
     "data/current/capture/ehf_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:24 UTC",
     "28-29 October group-phase fixtures (RL-16)"),
    ("EHF Champions League official standings (carried over)",
     "https://ehfcl.eurohandball.com/men/2026-27/standings/",
     "data/current/capture/ehf_standings_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:55 UTC",
     "24-club group tables (RL-03)"),
    ("MLB official standings sample (carried over)",
     "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104",
     "data/current/capture/mlb_standings_sample_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 13:05 UTC",
     "30-club runs for/against and records"),
    ("Formula 1 official calendar and drivers' standings (carried over)",
     "https://www.formula1.com/en/racing/2026",
     "data/current/capture/f1_calendar_2026-10-22.json",
     "B — first-hand by the /current/ session, 2026-10-22 12:36 UTC",
     "United States round (RL-13) and 23-driver standings"),
    ("MLB.com official probable-pitcher pages (located via search, pages quoted)",
     "https://www.mlb.com/rays/roster/probable-pitchers",
     "research/relay-103d996c.md", "C — official page content quoted via search index 2026-10-22",
     "Misiorowski named for Milwaukee; Tampa Bay TBD (RL-14). Not used in the model."),
]


def tbl(headers, rows):
    """<table> with thead/tbody so structural tests can check cell counts."""
    head = "".join("<th>%s</th>" % h for h in headers)
    return ("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
            % (head, "".join(rows)))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def page(title, body, depth=0, current=""):
    up = "../" * depth
    root = up + "../"   # prefix that reaches the repository root from this page
    nav_items = [
        ("index.html", "Dashboard"), ("matches.html", "All Fixtures"),
        ("lines.html", "Originated Lines"), ("picks.html", "Picks &amp; Confidence"),
        ("predictions.html", "High-Confidence Predictions"),
        ("inputs.html", "Model Inputs"), ("flagged.html", "Flagged for Review"),
        ("sources.html", "Source Register"), ("methodology.html", "Methodology"),
        ("sports/index.html", "By Sport"),
    ]
    nav = "".join(
        '<a href="%s%s"%s>%s</a>' % (up, href, ' aria-current="page"' if href == current else "", label)
        for href, label in nav_items)
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<link rel="stylesheet" href="%sassets/style.css">
</head>
<body>
<header class="topbar"><div class="wrap bar">
<a class="brand" href="%sindex.html"><span>OLBG Relay Desk</span>
<small>fresh official capture &middot; window 23&ndash;29 October 2026 &middot; session arena/103d996c-olbg2</small></a>
<nav class="nav" aria-label="Primary navigation">%s</nav>
</div></header>
<div class="cross"><div class="wrap">
<strong>Cross-layer:</strong>
<a href="%sindex.html">Root dashboard</a> &middot;
<a href="%scurrent/index.html">Current capture desk</a> &middot;
<a href="%sverified/index.html">Verified desk</a> &middot;
<a href="%slive/index.html">Live slate</a> &middot;
<a href="%sflagged.html">Root review queue</a>
</div></div>
<main class="wrap">
%s
</main>
<footer class="foot"><div class="wrap">
<p>OLBG Relay Desk &middot; generated by <code>scripts/relay_build.py</code> from
<code>data/relay/*.json</code> &middot; every row links an official source &middot;
unverified values are blank, never inferred &middot;
<a href="%sflagged.html">Flagged for Review</a></p>
</div></footer>
</body>
</html>
""" % (title, up, up, nav, root, root, root, root, root, body, up)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as handle:
        return json.load(handle)


def write(rel, content):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def badge(level):
    cls = {"high": "pill hi", "medium": "pill md", "low": "pill lo"}.get(level, "pill lo")
    return '<span class="%s">%s</span>' % (cls, esc(level))


def ev_badge(ev):
    return '<span class="pill %s">%s</span>' % ("hi" if ev == "A" else "md",
                                                 "evidence " + esc(ev))


def matches_table(matches, with_lines=False, lines_by_id=None):
    headers = ["Sport", "Date (official)", "Time", "Fixture", "Competition",
               "Venue", "Evidence", "Official source"]
    if with_lines:
        headers += ["Primary originated pick", "p", "Fair price", "Confidence"]
    rows = []
    for m in matches:
        if m["kind"] == "event":
            fixture = esc(m["event"])
        else:
            fixture = "%s v %s" % (esc(m["home"]["name"]), esc(m["away"]["name"]))
            if m["sport"] == "ice-hockey":
                rec = ""
                if m["home"].get("record") or m["away"].get("record"):
                    rec = '<br><small>%s %s &middot; %s %s</small>' % (
                        esc(m["home"]["abbrev"]), esc(m["home"]["record"]),
                        esc(m["away"]["abbrev"]), esc(m["away"]["record"]))
                fixture += rec
        line = '<td colspan="4">&mdash;</td>'
        if with_lines:
            r = lines_by_id.get(m["id"])
            if r and r["originated"] and r["primary"]:
                p = r["primary"]
                line = ("<td>%s: <strong>%s</strong></td><td>%.4f</td><td>%.2f / %+d</td><td>%s</td>"
                        % (esc(p["market"]), esc(p["selection"]), p["p"],
                           p["fair_decimal"], p["fair_american"], badge(p["confidence"])))
            else:
                line = '<td colspan="4">blank &mdash; see flagged</td>'
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td>%s</td><td>%s</td>"
                    '<td><a href="%s" rel="nofollow">%s</a></td>%s</tr>'
                    % (esc(m["sport_name"]), esc(m["date"]), esc(m["time_note"]),
                       fixture, esc(m["competition"]), esc(m.get("venue") or "&mdash;"),
                       ev_badge(m["evidence"]), esc(m["official_url"]),
                       esc(m["source_name"]), line))
    return tbl(headers, rows)


def build():
    seeded = load("matches.json")
    lines_doc = load("lines.json")
    band = load("band.json")
    preds = load("predictions.json")
    inputs = load("model_inputs.json")
    matches = seeded["matches"]
    lines_by_id = {r["match_id"]: r for r in lines_doc["rows"]}
    counts = lines_doc["counts"]

    # ---------------- index ----------------
    per_sport = {}
    for m in matches:
        per_sport.setdefault(m["sport_name"], []).append(m)
    sport_rows = []
    for name, slug in SPORTS_IN_SCOPE:
        rows = per_sport.get(name, [])
        picks = [s for s in band["selections"] if s["sport_name"] == name]
        if rows:
            status = ('%d fixtures, %d in-band high-confidence picks &mdash; <a href="sports/%s.html">sport page</a>'
                      % (len(rows), len(picks), slug))
        else:
            status = ('zero rows this window &mdash; <a href="sports/%s.html">reason on sport page</a>' % slug)
        sport_rows.append("<tr><td><strong>%s</strong></td><td>%s</td></tr>" % (esc(name), status))
    body = """
<p class="eyebrow">Session arena/103d996c-olbg2 &middot; captured 2026-10-22 20:55&ndash;21:20 UTC</p>
<h1>Relay multi-sport fixture desk</h1>
<p class="lede">Upcoming fixtures for the eligible OLBG sports for the window
<strong>23&ndash;29 October 2026</strong>, with originated lines on every fixture that has an
official strength input. Nine rows were read first-hand from official endpoints in this
session (evidence&nbsp;A); 29 rows carry over verbatim from the completed
<a href="../current/index.html">/current/</a> capture of the same day (evidence&nbsp;B) because
this session's fetch proxy failed on those endpoints &mdash; every row says which.</p>
<div class="cards">
<div class="card"><b>%d</b><span>fixtures</span></div>
<div class="card"><b>%d</b><span>originated prices</span></div>
<div class="card"><b>%d</b><span>in-band high-confidence picks</span></div>
<div class="card"><b>%d</b><span>written predictions</span></div>
<div class="card"><b>%d</b><span>sports with rows / 17 in scope</span></div>
<div class="card"><b>%d</b><span>disclosure flags</span></div>
</div>
<h2>Sports coverage</h2>
%s
<h2>How to read this desk</h2>
<p>High confidence means model probability &ge; 0.70 <em>and</em> a fair no-vig American price
inside &minus;250&hellip;+10000, searched across every originated market and both sides.
Nothing here reads a bookmaker price. Values that could not be confirmed are blank and flagged
on the <a href="flagged.html">Flagged for Review</a> page. Five-picks-per-sport is met for
Rugby Union (6), Handball (6) and Ice Hockey (5); the shortfalls and the ten zero-row sports
are disclosed, never papered over.</p>
""" % (counts["fixture_rows"], counts["prices_originated"], counts["band_picks"],
       preds["counts"]["predictions"], counts["sports_with_rows"], len(FLAGS),
       tbl(["Sport", "Status this window"], sport_rows))
    write("index.html", page("Relay Desk — OLBG fixtures and originated lines", body, 0, "index.html"))

    # ---------------- matches ----------------
    body = ("<h1>All fixtures — window 23&ndash;29 October 2026</h1>"
            "<p>Every fixture with its official source link and evidence class. "
            "Records shown beside NHL fixtures are as printed by the official feed at capture "
            "time (flag RL-02).</p>" + matches_table(matches, True, lines_by_id))
    write("matches.html", page("All Fixtures — Relay Desk", body, 0, "matches.html"))

    # ---------------- lines ----------------
    rows = []
    for m in matches:
        r = lines_by_id.get(m["id"])
        if not r or not r["originated"]:
            continue
        fixture = m.get("event") or "%s v %s" % (m["home"]["name"], m["away"]["name"])
        for mk in r["markets"]:
            shown = mk["outcomes"][:14]
            cell = "; ".join("%s %.4f (%.2f/%+d)" % (
                o.get("selection", o.get("name", "")), o["p"], o["fair_decimal"],
                o["fair_american"]) for o in shown)
            if len(mk["outcomes"]) > 14:
                cell += "; … (+%d more)" % (len(mk["outcomes"]) - 14)
            rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                        % (esc(fixture), esc(m["date"]), esc(mk["market"]), cell))
    body = ("<h1>Originated lines — %d prices across %d markets</h1>"
            "<p>Every price is a fair no-vig number derived from the model probability printed "
            "beside it. No bookmaker price was read. Long handicap/total grids are truncated in "
            "this view; the full grid lives in <code>data/relay/lines.json</code>.</p>"
            "%s"
            % (counts["prices_originated"], counts["markets_originated"],
               tbl(["Fixture", "Date", "Market", "Outcomes (p, decimal/american)"], rows)))
    write("lines.html", page("Originated Lines — Relay Desk", body, 0, "lines.html"))

    # ---------------- picks ----------------
    rows = []
    for s in band["selections"]:
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><strong>%s</strong></td>"
                    "<td>%.4f</td><td>%.2f / %+d</td><td>%s</td><td>%s</td>"
                    '<td><a href="%s" rel="nofollow">source</a></td></tr>'
                    % (esc(s["sport_name"]), esc(s["date"]), esc(s["fixture"]),
                       esc(s.get("competition", "")), esc(s["selection"]), s["p"],
                       s["fair_decimal"], s["fair_american"], badge("high"),
                       ev_badge(s["evidence"]), esc(s["official_url"])))
    capped = []
    for m in matches:
        r = lines_by_id.get(m["id"])
        if r and r["originated"] and r["primary"] and r["primary"]["confidence"] != "high":
            capped.append("<tr><td>%s</td><td>%s</td><td>%s: <strong>%s</strong></td><td>%.4f</td>"
                          "<td>%.2f / %+d</td><td>%s</td><td>%s</td></tr>"
                          % (esc(m["sport_name"]), esc(m["date"]), esc(r["primary"]["market"]),
                             esc(r["primary"]["selection"]), r["primary"]["p"],
                             r["primary"]["fair_decimal"], r["primary"]["fair_american"],
                             badge(r["primary"]["confidence"]), esc(r["primary"]["note"])))
    body = ("<h1>Picks &amp; confidence</h1>"
            "<p>%d selections cleared the uniform high-confidence gate "
            "(p&nbsp;&ge;&nbsp;0.70 <em>and</em> fair American inside &minus;250&hellip;+10000). "
            "Fixtures with no in-band selection publish their strongest two-way opinion capped "
            "at medium/low beneath.</p>"
            "<h2>In-band high-confidence picks</h2>%s"
            "<h2>Capped strongest opinions (no in-band selection)</h2>%s"
            % (len(band["selections"]),
               tbl(["Sport", "Date", "Fixture", "Competition", "Selection", "p",
                    "Fair price", "Confidence", "Evidence", "Official source"], rows),
               tbl(["Sport", "Date", "Selection", "p", "Fair price", "Confidence",
                    "Why capped"], capped)))
    write("picks.html", page("Picks & Confidence — Relay Desk", body, 0, "picks.html"))

    # ---------------- predictions ----------------
    blocks = []
    for p in preds["predictions"]:
        blocks.append(
            '<article class="pred"><h3>%s <span class="pill hi">high</span></h3>'
            '<p class="meta">%s &middot; %s &middot; %s &middot; selection: <strong>%s</strong> '
            '&middot; p %.4f &middot; fair %.2f / %+d</p><p>%s</p>'
            '<p class="meta"><a href="%s" rel="nofollow">official fixture source</a></p></article>'
            % (esc(p["fixture"]), esc(p["sport_name"]), esc(p["date"]),
               esc(p["competition"]), esc(p["selection"]), p["probability"],
               p["fair_decimal"], p["fair_american"], esc(p["text"]),
               esc(next(m["official_url"] for m in matches if m["id"] == p["match_id"]))))
    body = ("<h1>High-confidence predictions</h1>"
            "<p>%d hand-written previews, one per in-band selection. Each names the club or "
            "player, current form and a recent result from an official table, and states the "
            "exact betting selection with its fair price. Every number quoted is from an "
            "official capture; nothing is invented.</p>%s"
            % (len(preds["predictions"]), "".join(blocks)))
    write("predictions.html", page("High-Confidence Predictions — Relay Desk", body, 0,
                                   "predictions.html"))

    # ---------------- inputs ----------------
    rows = []
    for key, cfg in inputs["inputs"].items():
        rows.append("<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td>"
                    '<td><a href="%s" rel="nofollow">%s</a></td></tr>'
                    % (esc(key), esc(cfg.get("model", "")), esc(cfg.get("snapshot_note")
                       or cfg.get("note") or ""), esc(cfg.get("source_url", "")),
                       esc(cfg.get("source_name", ""))))
    body = ("<h1>Model inputs</h1><p>One strength table per sport, each built only from the "
            "official capture it links to. Shrinkage priors, home advantages and standard "
            "deviations are model assumptions (flag RL-15).</p>"
            "%s" % tbl(["Sport key", "Model", "Notes", "Official source"], rows))
    write("inputs.html", page("Model Inputs — Relay Desk", body, 0, "inputs.html"))

    # ---------------- flagged ----------------
    rows = "".join(
        '<tr id="%s"><td><strong>%s</strong></td><td>%s</td><td>%s</td></tr>'
        % (fid, fid, esc(title), esc(detail)) for fid, title, detail in FLAGS)
    body = ("<h1>Flagged for Review</h1><p>%d disclosure flags. None blocks publication; each "
            "states exactly what is verified, what is a snapshot, and what is an assumption. "
            "Unverified values are blank in the tables above, never inferred.</p>"
            "%s"
            % (len(FLAGS), tbl(["Flag", "Title", "Detail"], rows)))
    write("flagged.html", page("Flagged for Review — Relay Desk", body, 0, "flagged.html"))

    # ---------------- sources ----------------
    rows = "".join(
        "<tr><td>%s</td><td><a href=\"%s\" rel=\"nofollow\">%s</a></td><td><code>%s</code></td>"
        "<td>%s</td><td>%s</td></tr>"
        % (esc(n), esc(u), esc(u), esc(c), esc(cls), esc(what)) for n, u, c, cls, what in SOURCES)
    body = ("<h1>Source register</h1><p>Every capture this desk publishes from. Class A rows "
            "were read first-hand in this session; class B rows carry over verbatim from the "
            "/current/ session's captures of the same day; class C is official-page content "
            "quoted via the search index (used for disclosure only, never for prices).</p>"
            "%s" % tbl(["Source", "Official URL", "Stored capture", "Evidence",
                        "What it provides"], rows))
    write("sources.html", page("Source Register — Relay Desk", body, 0, "sources.html"))

    # ---------------- methodology ----------------
    body = """
<h1>Methodology</h1>
<p><strong>Capture.</strong> Official governing-body endpoints only, read through the agent
web-fetch tool; each response is stored under <code>data/relay/capture/</code> (class A) or
carried over verbatim from <code>data/current/capture/</code> (class B). No bookmaker,
aggregator or press price is read. When the proxy failed, the row says so rather than
substituting a source.</p>
<p><strong>Origination.</strong> Attack/defence ratings with games-played shrinkage feed either
an independent-Poisson score grid (ice hockey, handball, baseball) or a normal margin/total
model (basketball, rugby union); F1 uses a share-of-championship-points outright. From each
distribution the desk originates a match-winner market, a handicap grid and a match-total grid,
and prices every side at fair no-vig decimal and American from the rounded model probability.</p>
<p><strong>Confidence gate.</strong> A selection is high confidence only when
p&nbsp;&ge;&nbsp;0.7000 <em>and</em> its fair American price lies inside &minus;250&hellip;+10000.
The search covers every originated market and both sides; the published pick prefers the
moneyline, then a favourite-side handicap, then totals, then an underdog-receiving handicap.
p&nbsp;&ge;&nbsp;0.70 shorter than &minus;250 is capped at medium; 0.60&ndash;0.70 is medium;
below is low.</p>
<p><strong>Predictions.</strong> Hand-authored against <code>data/relay/band.json</code>,
minimum 30 words, quoting only captured official numbers (standings, form strings, records,
team leaders), with the exact selection and fair price stated. Tests enforce length,
uniqueness and the fact links.</p>
<p><strong>Verification.</strong> <code>tests/test_relay_103d996c.py</code> recomputes
selected fixtures from the stored captures through an independent code path, checks every
rendered link and anchor, asserts every fixture row carries an official URL, and re-runs the
band gate over every published price.</p>
"""
    write("methodology.html", page("Methodology — Relay Desk", body, 0, "methodology.html"))

    # ---------------- sports ----------------
    idx = []
    for name, slug in SPORTS_IN_SCOPE:
        rows = per_sport.get(name, [])
        picks = [s for s in band["selections"] if s["sport_name"] == name]
        if rows:
            picks_html = ""
            if picks:
                prows = "".join(
                    "<tr><td>%s</td><td>%s</td><td><strong>%s</strong></td><td>%.4f</td>"
                    "<td>%.2f / %+d</td><td>%s</td></tr>"
                    % (esc(s["date"]), esc(s["fixture"]), esc(s["selection"]), s["p"],
                       s["fair_decimal"], s["fair_american"],
                       '<a href="%s" rel="nofollow">source</a>' % esc(s["official_url"]))
                    for s in picks)
                picks_html = ("<h2>In-band high-confidence picks</h2>"
                              + tbl(["Date", "Fixture", "Selection", "p", "Fair price",
                                     "Official source"], prows))
            quota = ("<p>Five-picks-per-sport target: <strong>%s</strong> (%d in-band picks).</p>"
                     % ("met" if len(picks) >= 5 else "not met — disclosed, see flagged RL-05/06/07",
                        len(picks)))
            body = ("<h1>%s</h1>%s%s<h2>Fixtures</h2>%s"
                    % (esc(name), quota, picks_html, matches_table(rows, True, lines_by_id)))
        else:
            body = ("<h1>%s</h1><p><strong>Zero rows this window.</strong> %s</p>"
                    "<p>See <a href=\"../flagged.html\">Flagged for Review</a>.</p>"
                    % (esc(name), esc(ZERO_ROW_REASONS[slug])))
        write("sports/%s.html" % slug,
              page("%s — Relay Desk" % esc(name), body, 1, "sports/index.html"))
        idx.append("<li><a href=\"%s.html\">%s</a> — %s</li>"
                   % (slug, esc(name), ("%d fixtures, %d picks" % (len(rows), len(picks)))
                      if rows else "zero rows, reason on page"))
    body = ("<h1>By sport</h1><p>Seventeen sports in scope after the OLBG exclusions "
            "(soccer, boxing, UFC/MMA, football, American football, hurling, horse racing, "
            "cycling, specials).</p><ul>%s</ul>" % "".join(idx))
    write("sports/index.html", page("By Sport — Relay Desk", body, 1, "sports/index.html"))

    write("assets/style.css", CSS.strip() + "\n")
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print("relay_build OK: %d files under relay/" % n)


if __name__ == "__main__":
    build()
