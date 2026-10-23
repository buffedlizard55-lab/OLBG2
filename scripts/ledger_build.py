#!/usr/bin/env python3
"""Build the /ledger/ dashboard from the committed JSON in data/ledger/.

Pages: overview, matches (the OLBG slate), fixtures (official schedule + our markets),
picks, previews, 15 sport pages, flagged, sources, verification, method, repo review.

The builder is offline and deterministic: run it twice and the bytes are identical.
"""
from __future__ import annotations

import datetime as _dt
import html
import json
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402
DATA = ROOT / "data" / "ledger"
ANCHOR = anchor()
import datetime as _dtmod
ANCHOR_DT = _dtmod.datetime.strptime(ANCHOR, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dtmod.timezone.utc)
OUT = ROOT / "ledger"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
SLUG = {s: s.lower().replace(" ", "-") for s in SPORTS}
NAV = [
    ("index.html", "Overview"), ("matches.html", "OLBG matches"), ("fixtures.html", "Fixtures & prices"),
    ("picks.html", "Picks"), ("predictions.html", "Previews"), ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"), ("verification.html", "Verification"), ("repo-review.html", "Repo review"),
    ("methodology.html", "Method"), ("../index.html", "OLBG2 home"),
]

E = html.escape


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def badge(text, kind="neutral"):
    return f'<span class="tag {kind}">{E(str(text))}</span>'


def conf_tag(c):
    return badge(c, {"high": "good", "medium": "warn", "low": "neutral"}.get(c, "neutral"))


def basis_tag(b):
    return badge("originated" if b == "originated" else "market-implied",
                 "good" if b == "originated" else "warn")


def state_tag(s):
    return badge({"official-fixture": "official fixture", "official-page": "official page",
                  "unmatched": "unmatched"}.get(s, s),
                 {"official-fixture": "good", "official-page": "warn", "unmatched": "bad"}.get(s, "neutral"))


def src_link(src):
    """A flag's source: an external URL, or a local file inside this layer."""
    if not src:
        return '<span class="blank">—</span>'
    if src.startswith("http"):
        return f'<a href="{E(src)}" rel="noopener" target="_blank">source</a>'
    local = src.lstrip("/")
    if local.startswith("ledger/"):
        local = local[len("ledger/"):]
    return f'<a href="{E(local)}">source</a>'


def link(url, label):
    if not url:
        return '<span class="blank">—</span>'
    return f'<a href="{E(url)}" rel="noopener" target="_blank">{E(label)}</a>'


def shell(active, title, body, prefix=""):
    nav = "".join(
        f'<a class="{"here" if href == active else ""}" href="{prefix}{href}">{E(label)}</a>' for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} | OLBG2 ledger</title>
<link rel="stylesheet" href="{prefix}assets/ledger.css">
</head><body>
<header class="top"><div class="wrap">
<h1>OLBG2 <span>ledger</span></h1>
<p class="sub">Fifteen sports, one table. Every value traces to a captured official response.</p>
<nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">
<p>Snapshot built {E(BUILT)} from captures taken {E(CAPTURE_WINDOW)}. Prices are fair prices with no margin, published for
analysis, not as betting advice. 18+.</p>
<p>Rows whose official source could not be found are marked unmatched and listed on
<a href="{prefix}flagged.html">Flagged for review</a>. This desk does not fill a gap with an estimate.</p>
</div></footer></body></html>"""


def table(headers, rows, cls=""):
    """Render semantic table cells from escaped text or trusted markup fragments.

    Call sites escape dynamic text with ``E`` before passing it here; markup helpers such
    as ``link`` and ``badge`` return trusted fragments. The wrapper must always put each
    fragment inside a <td>. Previously, any string beginning with '<' was emitted as a
    direct child of <tr>, creating invalid tables and double-escaping already escaped text.
    """
    if not rows:
        return '<p class="empty">No rows.</p>'
    head = "".join(f'<th scope="col">{E(h)}</th>' for h in headers)

    def cell(value):
        content = "" if value is None else str(value)
        return f"<td>{content}</td>"

    body = "".join("<tr>" + "".join(cell(c) for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table class="{E(cls)}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def kpi(value, label, note=""):
    return f'<div class="kpi"><div class="v">{E(str(value))}</div><div class="k">{E(label)}</div><div class="n">{E(note)}</div></div>'


def build():
    global BUILT, CAPTURE_WINDOW, BUILD_NOW
    matches = load("matches.json")
    lines = load("lines.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    inh = load("inherited.json")
    flags = load("flagged.json")
    sources = load("sources.json")
    review = load("repo_review.json")
    olbg = load("olbg.json")

    global BUILD_NOW
    BUILT = matches["meta"]["generated_at"]
    BUILD_NOW = ANCHOR
    CAPTURE_WINDOW = f"{sources['meta']['first_capture']} to {sources['meta']['last_capture']}"

    events = matches["events"]
    per_sport = defaultdict(lambda: {"events": 0, "verified": 0, "priced": 0, "previews": 0})
    for e in events:
        per_sport[e["sport"]]["events"] += 1
        if e["verify"]["state"] != "unmatched":
            per_sport[e["sport"]]["verified"] += 1
        if e.get("our_markets"):
            per_sport[e["sport"]]["priced"] += 1
    priced_fixtures = [f for f in lines["fixtures"] if f.get("markets")]
    all_high = [p for p in picks["picks"] if p["confidence"] == "high"]
    originated_high = [p for p in all_high if p["basis"] == "originated"]
    market_reference_high = [p for p in all_high if p["basis"] == "market-implied"]
    all_high_band = [p for p in all_high if p["in_band"]]

    # The user-facing recommendation card is limited to OLBG-listed events that also
    # have an official fixture URL and our own originated prices. Other official
    # schedule fixtures and OLBG's one-sided price references remain separate context.
    olbg_fixture_urls = {
        e["verify"].get("official_url")
        for e in events
        if e["verify"].get("state") == "official-fixture"
        and e.get("our_markets")
        and e["verify"].get("official_url")
    }
    olbg_events_with_lines = [e for e in events if e.get("our_markets")]
    olbg_originated_picks = [
        p for p in picks["picks"]
        if p.get("basis") == "originated" and p.get("official_url") in olbg_fixture_urls
    ]
    olbg_picks_by_fixture = defaultdict(list)
    for p in olbg_originated_picks:
        olbg_picks_by_fixture[p["official_url"]].append(p)
    olbg_recommendations = [
        max(rows_for_fixture, key=lambda p: (p["prob"], "win" in p["market_group"].lower()))
        for _, rows_for_fixture in sorted(olbg_picks_by_fixture.items())
    ]
    olbg_high = [p for p in olbg_recommendations if p["confidence"] == "high"]
    olbg_high_band = [p for p in olbg_high if p["in_band"]]
    olbg_all_high_band = [p for p in olbg_originated_picks if p["confidence"] == "high" and p["in_band"]]
    market_implied = [p for p in picks["picks"] if p["basis"] == "market-implied"]

    olbg_listing_urls = {e.get("olbg_url") for e in events if e.get("olbg_url")}
    current_olbg_previews = [
        p for p in preds["predictions"]
        if p.get("olbg_url") in olbg_listing_urls
        or p.get("official_url") in olbg_fixture_urls
    ]
    current_olbg_preview_ids = {p["id"] for p in current_olbg_previews}
    context_previews = [p for p in preds["predictions"] if p["id"] not in current_olbg_preview_ids]
    olbg_preview_pick_keys = {
        (p.get("official_url"), p.get("selection", "").casefold(), p.get("market", "").casefold())
        for p in current_olbg_previews
    }
    olbg_high_with_preview = [
        p for p in olbg_high
        if (p.get("official_url"), p.get("selection", "").casefold(), p.get("market", "").casefold())
        in olbg_preview_pick_keys
    ]
    for p in current_olbg_previews:
        per_sport[p["sport"]]["previews"] += 1

    # ---------------------------------------------------------------- overview
    top = sorted(olbg_recommendations,
                 key=lambda p: ({"high": 0, "medium": 1, "low": 2}.get(p["confidence"], 3), -p["prob"], p["start_utc"]))[:10]
    rows = []
    for p in top:
        rows.append([
            f'<a href="sports/{SLUG[p["sport"]]}.html">{E(p["sport"])}</a>',
            E(p["event"]),
            f'<b>{E(p["selection"])}</b>',
            E(p["market"]),
            E(p["american"] or "—"),
            f'{p["prob"]*100:.1f}%',
            conf_tag(p["confidence"]),
            badge("in band", "good") if p["in_band"] else badge("outside band", "warn"),
            E(p["start_utc"][:16].replace("T", " ")),
            link(p["official_url"], "official"),
        ])

    window_start = _dt.datetime.strptime(BUILD_NOW, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
    window_end = (window_start + _dt.timedelta(hours=36)).strftime("%Y-%m-%dT%H:%M:%SZ")
    soon = sorted([e for e in events if BUILD_NOW <= e["start_utc"] <= window_end],
                  key=lambda e: e["start_utc"])[:12]
    soon_rows = [[E(e["sport"]), E(e["start_utc"][:16].replace("T", " ") + " UTC"), E(e["event"]),
                  E(e["competition"] or "—"), state_tag(e["verify"]["state"]),
                  link(e["verify"]["official_url"], "official"), link(e["olbg_url"], "OLBG listing")] for e in soon]

    cover_rows = []
    for s in SPORTS:
        d = per_sport[s]
        rows_sport = [e for e in events if e["sport"] == s]
        best = max((p["prob"] for p in olbg_recommendations if p["sport"] == s), default=0)
        evidence_url = next((e["verify"].get("official_url") for e in rows_sport if e["verify"].get("official_url")), "")
        cover_rows.append([
            f'<a href="sports/{SLUG[s]}.html"><b>{E(s)}</b></a>',
            d["events"], d["verified"], d["priced"], d["previews"],
            f"{best*100:.1f}%" if best else '<span class="blank">—</span>',
            "" if d["events"] else '<span class="warn-text">no OLBG listing at capture</span>',
            link(evidence_url, "official") if evidence_url else '<span class="blank">—</span>',
            link(f"sports/{SLUG[s]}.html", "rows & review"),
        ])

    body = f"""
<section class="lede">
<p class="eyebrow">Snapshot · {E(matches["meta"]["generated_at"])} · session arena/41b3bae5-olbg2</p>
<h2>Executive summary</h2>
<p>OLBG listed <b>{len(events)}</b> upcoming events across the fifteen requested sports. <b>{sum(1 for e in events if e["verify"]["state"] != "unmatched")}</b> were matched to an official page or fixture feed, but only <b>{len(olbg_events_with_lines)}</b> have our own originated lines. The recommendations below are limited to those source-matched OLBG events.</p>
<p>Separately, <b>{len(priced_fixtures)}</b> official NHL, MLB and EuroLeague schedule fixtures have <b>{picks["meta"]["originated"]}</b> originated market selections. Only <b>{len(olbg_fixture_urls)}</b> of those fixtures also appeared on the captured OLBG slate; the rest are context, not OLBG picks. Another <b>{len(market_implied)}</b> selections are derived from OLBG's one-sided quoted prices and are not our lines.</p>
<p>There are <b>{len(current_olbg_previews)}</b> current write-ups tied to OLBG-listed events: {sum(1 for p in current_olbg_previews if p["confidence"] == "low")} low-, {sum(1 for p in current_olbg_previews if p["confidence"] == "medium")} medium- and {sum(1 for p in current_olbg_previews if p["confidence"] == "high")} high-confidence. <b>{len(olbg_high_with_preview)}</b> of {len(olbg_high)} high-confidence OLBG recommendations have a matching written preview; {len(olbg_high) - len(olbg_high_with_preview)} remain without one. The <b>{len(inh["previews"])}</b> carried previews are from an earlier snapshot and were not re-read today.</p>
<p class="note">Values with no official support remain blank and are listed for review. No missing form, player or injury information is inferred, and no OLBG quote is labelled as our price.</p>
</section>
<div class="kpis">
{kpi(len(events), "OLBG events", "the fifteen requested sports")}
{kpi(sum(1 for e in events if e["verify"]["state"] != "unmatched"), "officially matched", "9 official-page, 3 fixture-feed")}
{kpi(len(olbg_events_with_lines), "OLBG matches with our lines", "only source-matched fixtures")}
{kpi(len(olbg_high), "high OLBG picks", "originated selections only")}
{kpi(len(olbg_high_band), "high + in-band OLBG picks", "−250…+10000")}
{kpi(len(current_olbg_previews), "current OLBG-linked previews", f"{sum(1 for p in current_olbg_previews if p['confidence'] == 'low')} low · {sum(1 for p in current_olbg_previews if p['confidence'] == 'medium')} medium · {sum(1 for p in current_olbg_previews if p['confidence'] == 'high')} high")}
{kpi(len(priced_fixtures), "official context fixtures", f"{len(priced_fixtures) - len(olbg_fixture_urls)} not on the OLBG list")}
{kpi(len(market_implied), "market-implied references", "not our originated prices")}
{kpi(flags["meta"]["items"], "open review items", "see Flagged for review")}
</div>

<h2>Best originated selection per source-confirmed OLBG match</h2>
<p class="note">One highest-probability originated selection is shown for each of the {len(olbg_recommendations)} OLBG-listed matches with an official fixture URL. These are our fair lines, not bookmaker prices; the rows link to the official game page. The complete market set is on <a href="fixtures.html">Fixtures &amp; prices</a>.</p>
{table(["Sport", "Match", "Selection", "Market", "Fair price", "Chance", "Confidence", "Band", "Start (UTC)", "Official source"], rows)}

<h2>OLBG listings starting within 36 hours (first 12)</h2>
<p class="note">The time window is calculated from the capture timestamp. The official-source cell is blank when no governing-body match was found; the original OLBG listing is linked separately for every row. Unmatched rows remain flagged.</p>
{table(["Sport", "Start (UTC)", "Event", "Competition", "Official check", "Official source", "OLBG listing"], soon_rows)}

<h2>Coverage by sport</h2>
<p class="note">Event totals come from the captured OLBG pages. “Officially matched” confirms a fixture feed or participant pairing on an official page; the latter does not by itself confirm start time or form. “Our lines” counts only matches with an originated price. Official schedules outside the OLBG list are not included.</p>
{table(["Sport", "OLBG events", "Officially matched", "Our lines", "OLBG previews", "Best chance", "Note", "Official source (where found)", "Rows & review"], cover_rows)}

<h2>What this page does not claim</h2>
<ul class="plain">
<li>This is a dated capture, not a complete live slate. It records what OLBG listed at {E(CAPTURE_WINDOW.split(' to ')[-1])} and the official schedules captured alongside it.</li>
<li>Only {len(olbg_events_with_lines)} OLBG-listed events have our own lines; {len(events) - len(olbg_events_with_lines)} are unpriced. Of those, {sum(1 for e in events if e["verify"]["state"] == "unmatched")} remain unmatched to an official source.</li>
<li>The 93 official schedule fixtures include {len(priced_fixtures) - len(olbg_fixture_urls)} matches absent from the captured OLBG slate. Their lines are supplementary context, not OLBG picks.</li>
<li>{len(olbg_high)} high-confidence originated selections are attached to OLBG-listed matches; {len(olbg_high_with_preview)} have a matching current preview. The prediction page explains the shortfall.</li>
<li>{len(inh["previews"])} carried previews are from a predecessor snapshot and their facts were not re-read today.</li>
<li>Injuries are absent by design: no official team-news feed was readable, so none is asserted.</li>
</ul>
<p><a class="button" href="flagged.html">Read the {flags["meta"]["items"]} review items</a>
<a class="button" href="methodology.html">How the prices are made</a></p>
"""
    pages = {"index.html": shell("index.html", "Overview", body)}

    # ---------------------------------------------------------------- matches
    groups = []
    for s in SPORTS:
        rows = []
        for e in [x for x in events if x["sport"] == s]:
            ours = ""
            if e.get("our_markets"):
                win = [m for m in e["our_markets"]["win"]]
                home_fav = max(win, key=lambda m: m["prob"])
                ours = f'{E(home_fav["selection"])} <span class="muted">{E(home_fav["american"])}</span>'
            olbg_prices = ", ".join(f'{m["selection"]} {m["olbg_decimal"]}' for m in e["markets"][:3] if m["olbg_decimal"])
            rows.append([
                E(e["start_utc"][:16].replace("T", " ")),
                f'<b>{E(e["event"])}</b>',
                E(e["competition"] or e.get("olbg_sport") or "—"),
                E(olbg_prices or "—"),
                ours or '<span class="blank">—</span>',
                state_tag(e["verify"]["state"]),
                link(e["verify"]["official_url"] or "", "official") if e["verify"]["official_url"] else '<span class="blank">—</span>',
                link(e["olbg_url"], "OLBG"),
            ])
        groups.append(f'<h3 id="{SLUG[s]}">{E(s)} <span class="count">{len(rows)}</span></h3>'
                      + table(["Start (UTC)", "Event", "Competition", "OLBG quote", "Our price", "Official check", "Official source", "Listing"], rows))
    body = f"""
<h2>The OLBG slate — {len(events)} upcoming events</h2>
<p class="note">This is the fixture list the brief is built on: every upcoming event OLBG listed in the fifteen requested sports at
capture time, with OLBG's own quoted price kept separate from ours. The OLBG quote is a single-sided bookmaker price, not our line.</p>
<p class="note">Verification states: <b>official fixture</b> = found in an official schedule feed (NHL, MLB, EuroLeague) inside a
36-hour window; <b>official page</b> = both participants sit either side of a versus marker on an official competition page;
<b>unmatched</b> = nothing official found, so the row is a listing only.</p>
{"".join(groups)}
"""
    pages["matches.html"] = shell("matches.html", "OLBG matches", body)

    # ---------------------------------------------------------------- fixtures
    frows = []
    for f in priced_fixtures:
        win = f["markets"]["win"]
        handicap = f["markets"].get("handicap", [])
        total = f["markets"].get("total", [])
        total_pick = max(total, key=lambda m: m["prob"]) if total else None
        exp = f["markets"].get("_expected", {})
        frows.append([
            E(f["sport"]),
            E(f["start_utc"][:16].replace("T", " ")),
            f'<b>{E(f["away"])}</b> at <b>{E(f["home"])}</b>' if f["sport"] in ("Ice Hockey", "Baseball") else f'<b>{E(f["home"])}</b> v <b>{E(f["away"])}</b>',
            E(f.get("venue") or "—"),
            f'{E(win[0]["selection"])} <span class="muted">{E(win[0]["american"])}</span><br>{E(win[1]["selection"])} <span class="muted">{E(win[1]["american"])}</span>',
            f'{E(handicap[0]["selection"])} <span class="muted">{E(handicap[0]["american"])}</span><br>{E(handicap[1]["selection"])} <span class="muted">{E(handicap[1]["american"])}</span>',
            f'{E(total_pick["selection"])} <span class="muted">{E(total_pick["american"])}</span>' if total_pick else "—",
            f'{exp.get("home","—")} – {exp.get("away","—")}',
            link(f["official_url"], "official"),
        ])
    body = f"""
<h2>Supplementary official fixtures and our prices</h2>
<p class="note">These {len(priced_fixtures)} NHL, MLB and EuroLeague fixtures come from official schedule feeds. Only {len(olbg_fixture_urls)} also appear on the captured OLBG list; the remaining {len(priced_fixtures) - len(olbg_fixture_urls)} are supplementary context and are not counted as OLBG matches or OLBG picks. Each row carries winner, handicap and total markets. The expected score is the number the price was built from, so a reader can check the arithmetic.</p>
<p class="note">EuroLeague tip times are served without an offset and are published as served, not converted to UTC. This is flagged on the <a href="flagged.html">review page</a>.</p>
{table(["Sport", "Start (UTC)", "Fixture", "Venue", "Winner market", "Handicap", "Total", "Expected score", "Source"], frows)}
<h2>Market notes</h2>
<ul class="plain">
<li><b>Winner</b> is a two-way market: the draw is not priced in hockey or basketball, where a regulation tie is split 50/50, and not in baseball, where extra innings decide it.</li>
<li><b>Handicap</b> is a fixed 1.5 line for the side we make favourite, and +1.5 for the other.</li>
<li><b>Total</b> is the half-point line nearest the expected score: 5.5 and 6.5 in hockey, 7.5 and 8.5 in baseball, 159.5 and 163.5 in the EuroLeague.</li>
</ul>
"""
    pages["fixtures.html"] = shell("fixtures.html", "Fixtures & prices", body)

    # ---------------------------------------------------------------- picks
    recommendations = sorted(olbg_recommendations, key=lambda p: (SPORTS.index(p["sport"]), p["start_utc"]))
    recommendation_rows = [[
        f'<a href="sports/{SLUG[p["sport"]]}.html">{E(p["sport"])}</a>',
        E(p["event"]), f'<b>{E(p["selection"])}</b>', E(p["market"]), E(p["american"] or "—"),
        f'{p["prob"]*100:.1f}%', conf_tag(p["confidence"]),
        badge("in band", "good") if p["in_band"] else badge("outside", "warn"),
        link(p["official_url"], "official"),
    ] for p in recommendations]
    all_market_rows = [[
        f'<a href="sports/{SLUG[p["sport"]]}.html">{E(p["sport"])}</a>', E(p["event"]),
        f'<b>{E(p["selection"])}</b>', E(p["market"]), E(p["american"] or "—"),
        f'{p["prob"]*100:.1f}%', conf_tag(p["confidence"]),
        badge("in band", "good") if p["in_band"] else badge("outside band", "warn"),
        link(p["official_url"], "official"),
    ] for p in sorted(olbg_originated_picks, key=lambda p: (SPORTS.index(p["sport"]), p["start_utc"], p["market"], -p["prob"]))]
    band_rows = [[
        f'<a href="sports/{SLUG[p["sport"]]}.html">{E(p["sport"])}</a>', E(p["event"]),
        f'<b>{E(p["selection"])}</b>', E(p["market"]), E(p["american"]),
        f'{p["prob"]*100:.2f}%', conf_tag(p["confidence"]), link(p["official_url"], "official"),
    ] for p in sorted(olbg_all_high_band, key=lambda p: -p["prob"])]
    unpriced_sports = [s for s in SPORTS if s not in {e["sport"] for e in olbg_events_with_lines}]
    unpriced_sport_list = ", ".join(E(s) for s in unpriced_sports)
    body = f"""
<h2>Originated recommendations for OLBG-listed matches</h2>
<p class="note">Only OLBG events that also have a captured official fixture URL and an originated price appear as recommendations.
There are {len(recommendations)} such matches: {len(olbg_high)} high-confidence picks, {len(olbg_high_band)} both high and inside
−250…+10000. One best-probability selection is shown per match; all other originated markets for those matches follow below.
A market-implied price from OLBG is not our line and is not counted here.</p>
<div class="kpis">
{kpi(len(recommendations), "OLBG matches with picks", "one recommendation per fixture")}
{kpi(len(olbg_high), "high confidence", "originated selections only")}
{kpi(len(olbg_high_band), "high + in band", "−250…+10000")}
{kpi(len(olbg_originated_picks), "originated market selections", "across the matched OLBG fixtures")}
</div>
{table(["Sport", "Match", "Selection", "Market", "Fair price", "Chance", "Confidence", "Band", "Official source"], recommendation_rows)}

<h2>High-confidence OLBG picks inside the requested price band</h2>
<p class="note">Only originated selections for the official-source-matched OLBG fixtures are included. The matching official page is linked in each row.</p>
{table(["Sport", "Match", "Selection", "Market", "Fair price", "Chance", "Confidence", "Official source"], band_rows)}

<h2>All originated markets on these OLBG-listed matches</h2>
<p class="note">Winner, handicap and total selections for the {len(olbg_events_with_lines)} source-matched fixtures. The inputs and probabilities are the desk's; each row links to its official game page.</p>
{table(["Sport", "Match", "Selection", "Market", "Fair price", "Chance", "Confidence", "Band", "Official source"], all_market_rows)}

<h2>Shortfall against the five-per-sport target</h2>
<p>Only Baseball and Ice Hockey currently have an OLBG-listed match with an official fixture match and our own line. The following remaining listed sports have no originated OLBG selection in this capture: <b>{unpriced_sport_list}</b>. Their values remain blank on the relevant sport page and unmatched listings remain on <a href="flagged.html">Flagged for Review</a>; no prices are inferred to fill the target.</p>
<p><b>{len(events) - len(olbg_events_with_lines)}</b> other OLBG listings have no originated line: {sum(1 for e in events if e["verify"]["state"] == "unmatched")} are unmatched to an official source and {sum(1 for e in events if e["verify"]["state"] == "official-page")} have a page-level pairing only. The {len(market_implied)} market-implied references remain visible on <a href="matches.html">OLBG matches</a>, separated from our fair prices.</p>
<p>The supplementary schedule page contains {len(priced_fixtures) - len(olbg_fixture_urls)} official fixtures not found on the captured OLBG list. Those lines are context only; see <a href="fixtures.html">Fixtures &amp; prices</a>.</p>
"""
    pages["picks.html"] = shell("picks.html", "Picks", body)

    # ---------------------------------------------------------------- previews
    def render_current_previews(preview_rows):
        rendered = []
        for p in sorted(preview_rows, key=lambda x: (SPORTS.index(x["sport"]) if x["sport"] in SPORTS else 99, -x["prob"])):
            facts = "".join(f"<li>{E(f)}</li>" for f in p["facts"])
            source_line = f'Official source: {link(p["prediction_source"], "fact source")}'
            if p.get("official_url") and p["official_url"] != p["prediction_source"]:
                source_line += f' · Fixture page: {link(p["official_url"], "official game page")}'
            rendered.append(f"""
<article class="preview" id="{E(p['id'])}">
<div class="pv-head"><h3>{E(p['sport'])} · {E(p['event'])}</h3>
<div class="pv-tags">{conf_tag(p['confidence'])}{badge(p['selection'] + ' ' + (p['american'] or ''), 'pick')}{basis_tag(p['basis'])}
{badge(f"{p['words']} words", 'neutral')}</div></div>
<p class="pv-pick"><b>Selection:</b> {E(p['selection'])} — {E(p['market'])} at <b>{E(p['american'] or '—')}</b>
<span class="muted">({E(p['start_utc'][:16].replace('T',' '))} UTC · {E(p['competition'] or '')})</span></p>
<p class="pv-text">{E(p['text'])}</p>
<details><summary>The facts behind it</summary><ul class="facts">{facts}</ul>
<p class="src">{source_line}</p></details>
</article>""")
        return "".join(rendered)

    olbg_cards = render_current_previews(current_olbg_previews)
    context_cards = render_current_previews(context_previews)
    inh_cards = []
    for p in sorted(inh["previews"], key=lambda x: (SPORTS.index(x["sport"]) if x["sport"] in SPORTS else 99, -x["prob"])):
        srcs = "".join(f'<li>{link(sv["url"], sv["name"] or sv["url"])} <span class="muted">{E(sv["used_for"])}</span></li>'
                       for sv in p["sources"])
        inh_cards.append(f"""
<article class="preview">
<div class="pv-head"><h3>{E(p['sport'])} · {E(p['event'])}</h3>
<div class="pv-tags">{conf_tag(p['confidence'].lower())}{badge(p['selection'] + ' ' + str(p['american'] or ''), 'pick')}{badge('carried', 'neutral')}
{badge(f"{p['words']} words", 'neutral')}</div></div>
<p class="pv-pick"><b>Selection:</b> {E(p['selection'])} — {E(p['market'])} at <b>{E(str(p['american'] or '—'))}</b>
<span class="muted">({E(p['date'])} · {E(p['competition'] or '')} · earlier fixture id {E(p['carried_fixture_id'])})</span></p>
<p class="pv-text">{E(p['text'])}</p>
<details><summary>Sources it was written from</summary><ul class="facts">{srcs}</ul></details>
</article>""")
    body = f"""
<h2>Previews tied to OLBG-listed events — {len(current_olbg_previews)}</h2>
<p class="note">These are the current write-ups joined to OLBG events in the captured slate: {sum(1 for p in current_olbg_previews if p["basis"] == "originated")} use originated lines and {sum(1 for p in current_olbg_previews if p["basis"] == "market-implied")} use OLBG's one-sided quote as a reference. They include {sum(1 for p in current_olbg_previews if p["confidence"] == "low")} low-, {sum(1 for p in current_olbg_previews if p["confidence"] == "medium")} medium- and {sum(1 for p in current_olbg_previews if p["confidence"] == "high")} high-confidence previews; {len(olbg_high_with_preview)} of {len(olbg_high)} high-confidence OLBG recommendations have matching write-ups. No player or injury claims are added without support in a captured official source.</p>
<div class="previews">{olbg_cards if olbg_cards else '<p class="empty">No preview is joined to an OLBG-listed match in this capture.</p>'}</div>
<h2>Other official-schedule previews — {len(context_previews)}</h2>
<p class="note">These fact-linked previews are not joined to an OLBG listing in this snapshot. They are supplementary official-schedule research, not OLBG picks. The capture's official schedule and price rows remain on <a href="fixtures.html">Fixtures &amp; prices</a>.</p>
<div class="previews">{context_cards if context_cards else '<p class="empty">No supplementary preview.</p>'}</div>
<h2>Carried previews — {len(inh['previews'])}</h2>
<p class="note">These were written against this desk's predecessor in the same <code>/ledger/</code> scope (session
<code>{E(inh['meta']['source_layer'])}</code>) and are carried here rather than dropped. Their fixture ids belong to the earlier
desk, so they are not joined to a row of this desk's price table and the facts behind them were not re-read today. What was
re-checked here is the prose rule: length, uniqueness, no forbidden wording, and a live https source. They add coverage in
{E(", ".join(sorted(set(inh['meta']['by_sport']) - set(preds['meta']['by_sport']))))}.</p>
<div class="previews">{"".join(inh_cards)}</div>
"""
    pages["predictions.html"] = shell("predictions.html", "Previews", body)

    # ---------------------------------------------------------------- flagged
    olbg_event_by_official_url = {
        e["verify"].get("official_url"): e
        for e in olbg_events_with_lines
        if e["verify"].get("official_url")
    }
    high_preview_gap_rows = []
    for p in olbg_high:
        if p not in olbg_high_with_preview:
            event = olbg_event_by_official_url.get(p.get("official_url"), {})
            high_preview_gap_rows.append([
                E(p["sport"]), E(p["event"]), f'<b>{E(p["selection"])}</b>', E(p["market"]),
                f'{p["prob"]*100:.1f}%', E(p["american"] or "—"),
                link(p.get("official_url"), "official"), link(event.get("olbg_url"), "OLBG listing"),
            ])
    if high_preview_gap_rows:
        high_preview_gap_section = f"""
<h3>High-confidence OLBG picks without a matching preview — {len(high_preview_gap_rows)}</h3>
<p class="note">These selections meet the numeric confidence and price-band rules, but this capture contains no matching written preview for the exact selection. The official game page and OLBG listing are linked for manual review. Player and injury facts were not added without an official source.</p>
{table(["Sport", "Match", "Selection", "Market", "Chance", "Fair price", "Official source", "OLBG listing"], high_preview_gap_rows)}
"""
    else:
        high_preview_gap_section = f"""
<h3>High-confidence OLBG preview coverage</h3>
<p class="note">All {len(olbg_high)} high-confidence originated OLBG recommendations in this capture have a matching source-linked written preview. The fact source and official game page are shown with each preview; no unsupported player or injury claims were added.</p>
"""
    frows = [[badge(f["code"], "code"), E(f["sport"]), f'<b>{E(f["title"])}</b><br><span class="muted">{E(f["detail"])}</span>',
              badge(f["severity"], {"high": "bad", "medium": "warn"}.get(f["severity"], "neutral")),
              src_link(f["source"]), E(f["impact"])] for f in flags["items"]]
    unmatched_rows = [[E(e["sport"]), E(e["start_utc"][:16].replace("T", " ")), E(e["event"]),
                       link(e["verify"]["official_url"], "official"), link(e["olbg_url"], "OLBG listing")]
                      for e in events if e["verify"]["state"] == "unmatched"]
    body = f"""
<h2>Flagged for review</h2>
<p class="note">Everything this desk could not confirm, could not price, or chose not to assert. Missing values remain blank; OLBG-only listings are not given an official source by inference.</p>
{high_preview_gap_section}
<h3>Other open findings — {len(frows)}</h3>
{table(["Ref", "Sport", "Finding", "Severity", "Source", "Effect on the desk"], frows)}
<h2>Unmatched OLBG rows ({len(unmatched_rows)})</h2>
<p class="note">These are listed by OLBG but were not found on any official source captured today. The official-source cells remain blank; the OLBG listing is linked for follow-up. They carry no price of ours.</p>
{table(["Sport", "Start (UTC)", "Event", "Official source", "OLBG listing"], unmatched_rows)}
"""
    pages["flagged.html"] = shell("flagged.html", "Flagged for review", body)

    # ---------------------------------------------------------------- sources
    srows = []
    for s in sources["sources"]:
        err = s.get("error") or ""
        st = badge(str(s["status"]), "good" if s["status"] == 200 else "bad")
        srows.append([st, E(s["sport"] or "OLBG"), f'<code>{E(s["key"])}</code>', link(s["url"], s["url"][:78] + ("…" if len(s["url"]) > 78 else "")),
                      E(s["fetched_at"] or ""), E(f"{s['bytes']:,}" if s.get("bytes") else "—"),
                      E("yes" if s.get("truncated") else ""), E(err[:60])])
    body = f"""
<h2>Source register — {sources['meta']['captures']} captures</h2>
<p class="note">Every public page this desk read, with its HTTP status, byte count, storage key and the UTC time of the request.
{ sources['meta']['ok']} returned 200 and {sources['meta']['failed']} did not; a failure is recorded too, because a blocked source is
evidence about what could not be checked. Bodies are stored verbatim under <code>data/ledger/raw/</code> and hashed in
<code>data/ledger/manifest.json</code>.</p>
<p class="note">Captures were taken by a GitHub Actions job (<code>.github/workflows/ledger-capture.yml</code>), because the authoring
sandbox has no route to the public internet. The job commits the responses back to the branch that requested them.</p>
{table(["Status", "Sport", "Key", "URL", "Fetched (UTC)", "Bytes", "Truncated", "Error"], srows)}
"""
    pages["sources.html"] = shell("sources.html", "Sources", body)

    # ---------------------------------------------------------------- verification
    by_state = defaultdict(int)
    for e in events:
        by_state[e["verify"]["state"]] += 1
    ver_rows = [[E(e["sport"]), E(e["event"]), state_tag(e["verify"]["state"]), E(e["verify"]["detail"]),
                 E(e["verify"].get("evidence", "")[:160]), link(e["verify"]["official_url"] or "", "open")]
                for e in events if e["verify"]["state"] != "unmatched"]
    body = f"""
<h2>Verification</h2>
<p class="note">What "checked" means here, stated per row rather than asserted for the page as a whole.</p>
<div class="kpis">
{kpi(by_state.get("official-fixture", 0), "official fixture", "found in a schedule feed")}
{kpi(by_state.get("official-page", 0), "official page", "pairing appears on an official page")}
{kpi(by_state.get("unmatched", 0), "unmatched", "listing only, no official source")}
{kpi(len(priced_fixtures), "fixtures priced", "from official season records")}
</div>
<h2>How the check was performed</h2>
<ol class="plain">
<li>Every OLBG sport hub was fetched and parsed for its embedded tip objects: event name, start time, market, quoted price and
OLBG's own confidence figure. That gives the slate, and it is the only thing OLBG is used for.</li>
<li>Official schedule feeds were fetched for the sports that publish one (NHL, MLB, EuroLeague) and parsed into fixtures with
fixture ids, venues and UTC start times.</li>
<li>Each OLBG event was compared with those feeds by participant name and a 36-hour time window. A hit is an
<b>official fixture</b> and links its game page.</li>
<li>For sports without a feed, the text of each official competition page was normalised and searched for the two participants on
opposite sides of the same versus marker. A hit is an <b>official page</b> and the surrounding text is stored on the row as
evidence.</li>
<li>Everything else is <b>unmatched</b>. It keeps its OLBG listing and appears on the flagged page.</li>
</ol>
<h2>Rows with an official source ({len(ver_rows)})</h2>
{table(["Sport", "Event", "State", "What was found", "Evidence", "Source"], ver_rows)}
"""
    pages["verification.html"] = shell("verification.html", "Verification", body)

    # ---------------------------------------------------------------- repo review
    rrows = [[badge(f["code"], "code"), f'<b>{E(f["title"])}</b><br><span class="muted">{E(f["detail"])}</span>',
              badge(f["severity"], {"high": "bad", "medium": "warn"}.get(f["severity"], "neutral")), E(f["evidence"])]
             for f in review["findings"]]
    body = f"""
<h2>Repository review</h2>
<p class="note">A repository-level review refreshed for this publication integration. {review['meta']['findings']} observations remain, each
with supporting evidence. Root navigation now separates the current ledger from dated archives; findings owned by other sessions
are left unchanged and kept visible for coordination.</p>
{table(["Ref", "Finding", "Severity", "Evidence"], rrows)}
<h2>What was run</h2>
<ul class="plain">
<li><code>python3 -m unittest discover -s tests</code> — full suite, including the integration link audit.</li>
<li><code>python3 scripts/integration_audit.py</code> — local link and fragment check across every published layer.</li>
<li><code>python3 scripts/ledger_verify.py</code> — this layer's own audit: capture hashes, row provenance, word counts, forbidden words.</li>
</ul>
<p>Findings that concern the shared board or another session's files are listed on
<a href="flagged.html">Flagged for review</a> as well, so they are visible without reading this page.</p>
"""
    pages["repo-review.html"] = shell("repo-review.html", "Repository review", body)

    # ---------------------------------------------------------------- method
    body = f"""
<h2>Method</h2>
<h3>1. What the desk collects</h3>
<p>The event list is OLBG's: every upcoming event captured in the fifteen requested sports. This snapshot contains {len(events)} events; {sum(1 for e in events if e["verify"]["state"] != "unmatched")} were matched to an official page or fixture feed, but only {len(olbg_events_with_lines)} also have an originated line. The 93 official schedule fixtures are a separate comparison layer, and {len(priced_fixtures) - len(olbg_fixture_urls)} were not found in the captured OLBG list. OLBG's one-sided quoted prices stay in their own column and are not our lines.</p>
<h3>2. How a price is originated</h3>
<p>Only official season records are inputs: wins, losses, goals or points for and against, games played. From them:</p>
<pre>rating      = 1500 + 400 × (points_pct − 0.5) + 30 × (score_difference_per_game)
home edge   = +45 rating points
p(home)     = 1 / (1 + 10^(−((rating_home + 45) − rating_away) / 400))
expected    = attack_home × defence_away ÷ league_average   (and the mirror for the away side)
total       = Poisson over the two expected scores (normal approximation above 30 combined points)
handicap    = the same distribution, ±1.5 for the side we make favourite</pre>
<p>The fair decimal is 1/p. No margin is added and no bookmaker price is an input. The expected score behind every fixture is
printed on <a href="fixtures.html">Fixtures &amp; prices</a> so the arithmetic can be checked.</p>
<h3>3. Confidence</h3>
<p>high = 70% or better, medium = 60–69.9%, low = below 60%. The same thresholds apply to a market-implied price, which is
labelled separately because it is not our number.</p>
<h3>4. The price band and the OLBG-only view</h3>
<p>The brief asks for selections between −250 and +10000 and for a chance above 70%. A 70% chance is about −233, so the two rules overlap only between 70.0% and 71.4%. Across the full combined dataset there are {len(all_high)} high-confidence selections ({len(originated_high)} originated and {len(market_reference_high)} market-implied references), with {len(all_high_band)} inside the band. The OLBG-only executive view is narrower: {len(olbg_high)} high recommendations, {len(olbg_high_band)} high and in-band, from {len(olbg_events_with_lines)} source-matched OLBG fixtures.</p>
<h3>5. What is never done</h3>
<ul class="plain">
<li>A missing value is left blank, never filled from another sport, another day or an average.</li>
<li>No injury, suspension or team-news claim is made without an official page that says it.</li>
<li>Only {len(current_olbg_previews)} current previews are joined to OLBG-listed events; the other {len(context_previews)} are separate official-schedule context, and {len(inh["previews"])} carried previews were not re-read today.</li>
<li>The words "model" and "verified" do not appear in a published preview; the method is described here instead.</li>
</ul>
<h3>6. Reproducing this</h3>
<pre>python3 scripts/ledger_capture.py      # on a runner with internet access
python3 scripts/ledger_seed.py         # OLBG payload -> data/ledger/olbg.json
python3 scripts/ledger_official.py     # official payloads -> data/ledger/official.json
python3 scripts/ledger_merge.py        # match OLBG events to official sources
python3 scripts/ledger_model.py        # originate prices
python3 scripts/ledger_picks.py        # grade and rank selections
python3 scripts/ledger_predictions.py  # validate the written previews
python3 scripts/ledger_report.py       # sources, flags, repository review
python3 scripts/ledger_build.py        # this site
python3 scripts/ledger_verify.py       # audit the result</pre>
"""
    pages["methodology.html"] = shell("methodology.html", "Method", body)

    # ---------------------------------------------------------------- sport pages
    NO_FEED_HTML = '<p class="empty">No official schedule feed carried this sport in the captures for today.</p>'
    for s in SPORTS:
        evs = [e for e in events if e["sport"] == s]
        preds_s = [p for p in current_olbg_previews if p["sport"] == s]
        context_preds_s = [p for p in context_previews if p["sport"] == s]
        picks_s = [p for p in olbg_recommendations if p["sport"] == s]
        fxs = [f for f in priced_fixtures if f["sport"] == s]
        mrows = [[E(e["start_utc"][:16].replace("T", " ")), E(e["event"]), E(e["competition"] or "—"),
                  E(", ".join(f'{m["selection"]} {m["olbg_decimal"]}' for m in e["markets"][:2] if m["olbg_decimal"]) or "—"),
                  state_tag(e["verify"]["state"]), link(e["verify"]["official_url"], "official"),
                  link(e["olbg_url"], "OLBG listing")] for e in evs]
        prows = [[f'<b>{E(p["selection"])}</b>', E(p["market"]), E(p["american"]), f'{p["prob"]*100:.1f}%',
                  conf_tag(p["confidence"]), basis_tag(p["basis"]), link(p["official_url"], "source")] for p in picks_s]
        frows2 = [[E(f["start_utc"][:16].replace("T", " ")), f'{E(f["away"])} at {E(f["home"])}' if s in ("Ice Hockey", "Baseball") else f'{E(f["home"])} v {E(f["away"])}',
                   E(f.get("venue") or "—"),
                   E(f'{f["markets"]["win"][0]["selection"]} {f["markets"]["win"][0]["american"]} / {f["markets"]["win"][1]["selection"]} {f["markets"]["win"][1]["american"]}'),
                   link(f["official_url"], "official")] for f in fxs]
        inh_s = [p for p in inh["previews"] if p["sport"] == s]
        pv = render_current_previews(preds_s)
        context_pv = render_current_previews(context_preds_s)
        carried_pv = "".join(f'<article class="preview"><h3>{E(p["event"])} — {E(p["selection"])}</h3><p>{E(p["text"])}</p>'
                              f'<p class="src">carried from the earlier ledger pass · '
                              + " ".join(link(sv["url"], "source") for sv in p["sources"])
                              + f' · {p["words"]} words · not re-read today</p></article>' for p in inh_s)
        body = f"""
<p class="crumb"><a href="../index.html">Overview</a> / <a href="../matches.html">OLBG matches</a> / {E(s)}</p>
<h2>{E(s)}</h2>
<div class="kpis">
{kpi(len(evs), "OLBG events", "upcoming at capture")}
{kpi(len([e for e in evs if e["verify"]["state"] != "unmatched"]), "officially matched", "fixture feed or page-level pairing")}
{kpi(len(picks_s), "OLBG matches with our picks", "one per fixture")}
{kpi(len([p for p in picks_s if p["confidence"] == "high"]), "high-confidence picks", "originated OLBG matches only")}
{kpi(len(preds_s), "OLBG-linked previews", "current capture")}
</div>
<h3>OLBG listings</h3>
{table(["Start (UTC)", "Event", "Competition", "OLBG quote", "Official check", "Official source", "OLBG listing"], mrows)}
<h3>Best originated selections for OLBG-listed matches</h3>
{table(["Selection", "Market", "Fair price", "Chance", "Confidence", "Basis", "Official source"], prows) if prows else '<p class="empty">No OLBG-listed match in this capture has an official fixture match and our own line. See <a href="../flagged.html">Flagged for Review</a>.</p>'}
<h3>Supplementary official fixtures (not all listed on OLBG)</h3>
{table(["Start (UTC)", "Fixture", "Venue", "Winner market", "Official source"], frows2) if frows2 else NO_FEED_HTML}
<h3>Previews for OLBG-listed events</h3>
{pv if pv else '<p class="empty">No current preview is joined to an OLBG-listed event in this capture.</p>'}
<h3>Other official-schedule previews (not joined to OLBG)</h3>
{context_pv if context_pv else '<p class="empty">No supplementary preview for this sport.</p>'}
<h3>Carried previews from an earlier snapshot (not re-read)</h3>
{carried_pv if carried_pv else '<p class="empty">No carried preview.</p>'}
"""
        pages[f"sports/{SLUG[s]}.html"] = shell(f"sports/{SLUG[s]}.html" if s == "Golf" else "",
                                                s, body, prefix="../")

    cards = []
    for s in SPORTS:
        evs = [e for e in events if e["sport"] == s]
        n_ok = len([e for e in evs if e["verify"]["state"] != "unmatched"])
        n_recs = len([p for p in olbg_recommendations if p["sport"] == s])
        n_pv = len([p for p in current_olbg_previews if p["sport"] == s])
        n_hi = len([p for p in olbg_recommendations if p["sport"] == s and p["confidence"] == "high"])
        n_context = len([p for p in context_previews if p["sport"] == s])
        n_carried = len([p for p in inh["previews"] if p["sport"] == s])
        cards.append(f"""<a class="card" href="{SLUG[s]}.html">
<h3>{E(s)}</h3>
<p><b>{len(evs)}</b> OLBG events · <b>{n_ok}</b> matched to an official page/feed</p>
<p><b>{n_recs}</b> originated OLBG picks · <b>{n_hi}</b> high · <b>{n_pv}</b> OLBG-linked previews</p>
<p class="muted">{n_context} supplementary previews · {n_carried} carried from earlier snapshot</p>
<p class="muted">Open the sport page →</p></a>""")
    pages["sports/index.html"] = shell("sports/index.html", "Sports",
        f"""<h2>Fifteen sports</h2>
<p class="note">Each page separates the OLBG event list from official-source matches, originated OLBG picks, supplementary official schedules, current OLBG-linked previews and carried previews. Blank or unmatched values are explained on <a href="../flagged.html">Flagged for Review</a>.</p>
<div class="cards">{"".join(cards)}</div>""", prefix="../")

    return pages


def main() -> int:
    pages = build()
    (OUT / "sports").mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    css_src = ROOT / "assets" / "ledger.css"
    (OUT / "assets" / "ledger.css").write_text(css_src.read_text(encoding="utf-8"), encoding="utf-8")
    for name, content in pages.items():
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"{len(pages)} pages written to {OUT.relative_to(ROOT)}/")
    return 0


CSS = """"""


if __name__ == "__main__":
    raise SystemExit(main())
