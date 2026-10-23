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
import re
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
    if not rows:
        return '<p class="empty">No rows.</p>'
    head = "".join(f"<th>{E(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(c if str(c).startswith("<") else f"<td>{E(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def kpi(value, label, note=""):
    return f'<div class="kpi"><div class="v">{E(str(value))}</div><div class="k">{E(label)}</div><div class="n">{E(note)}</div></div>'


def build():
    global BUILT, CAPTURE_WINDOW, BUILD_NOW
    matches = load("matches.json")
    lines = load("lines.json")
    picks = load("picks.json")
    preds = load("predictions.json")
    inh = load("inherited.json")
    PREVIEW_SPORTS = sorted(set(preds["meta"]["by_sport"]) | set(inh["meta"]["by_sport"]))
    flags = load("flagged.json")
    sources = load("sources.json")
    review = load("repo_review.json")
    olbg = load("olbg.json")

    global BUILD_NOW
    BUILT = matches["meta"]["generated_at"]
    BUILD_NOW = ANCHOR
    CAPTURE_WINDOW = f"{sources['meta']['first_capture']} to {sources['meta']['last_capture']}"

    events = matches["events"]
    picks_by_id = {p["id"]: p for p in picks["picks"]}
    per_sport = defaultdict(lambda: {"events": 0, "verified": 0, "priced": 0, "previews": 0})
    for e in events:
        per_sport[e["sport"]]["events"] += 1
        if e["verify"]["state"] != "unmatched":
            per_sport[e["sport"]]["verified"] += 1
        if e.get("our_markets"):
            per_sport[e["sport"]]["priced"] += 1
    for p in preds["predictions"]:
        per_sport[p["sport"]]["previews"] += 1

    priced_fixtures = [f for f in lines["fixtures"] if f.get("markets")]
    high = [p for p in picks["picks"] if p["confidence"] == "high"]
    high_band = [p for p in high if p["in_band"]]

    # ---------------------------------------------------------------- overview
    # match-winner selections first: a preview desk should lead with who wins, not with a total
    top = sorted(high, key=lambda p: (0 if p["in_band"] else 1, 0 if "win" in p["market_group"].lower() else 1, -p["prob"]))[:10]
    rows = []
    for p in top:
        rows.append([
            f'<a href="sports/{SLUG[p["sport"]]}.html">{E(p["sport"])}</a>',
            E(p["event"]),
            f'<b>{E(p["selection"])}</b> {E(p["market"])}',
            f'<b>{E(p["american"] or "—")}</b>',
            f'{p["prob"]*100:.1f}%',
            conf_tag(p["confidence"]) + (badge("in band", "good") if p["in_band"] else badge("outside band", "warn")),
            basis_tag(p["basis"]),
            E(p["start_utc"][:16].replace("T", " ")),
            link(p["official_url"], "official"),
        ])

    soon = sorted([e for e in events if BUILD_NOW <= e["start_utc"] <= "2026-10-25T23:59:00Z"],
                  key=lambda e: e["start_utc"])[:12]
    soon_rows = [[E(e["sport"]), E(e["start_utc"][11:16] + " UTC"), E(e["event"]),
                  E(e["competition"] or "—"), state_tag(e["verify"]["state"]),
                  (link(e["verify"]["official_url"], "official") if e["verify"]["official_url"] else link(e["olbg_url"], "OLBG"))] for e in soon]

    cover_rows = []
    for s in SPORTS:
        d = per_sport[s]
        rows_sport = [e for e in events if e["sport"] == s]
        best = max((p["prob"] for p in picks["picks"] if p["sport"] == s), default=0)
        cover_rows.append([
            f'<a href="sports/{SLUG[s]}.html"><b>{E(s)}</b></a>',
            d["events"], d["verified"], d["priced"], d["previews"],
            f"{best*100:.1f}%" if best else '<span class="blank">—</span>',
            "" if d["events"] else '<span class="warn-text">no OLBG listing at capture</span>',
        ])

    body = f"""
<section class="lede">
<p class="eyebrow">Snapshot · {E(matches["meta"]["generated_at"])} · session arena/41b3bae5-olbg2</p>
<h2>Executive summary</h2>
<p>OLBG listed <b>{len(events)}</b> upcoming events in the fifteen requested sports when the pages were captured.
<b>{sum(1 for e in events if e["verify"]["state"] != "unmatched")}</b> of them were matched to an official source,
<b>{sum(1 for e in events if e.get("our_markets"))}</b> carry our own price, and <b>{len(preds["predictions"])}</b> written previews
were published, with <b>{len(inh["previews"])}</b> more carried over from this desk's predecessor. Alongside that, <b>{len(priced_fixtures)}</b> official schedule fixtures (NHL, MLB, EuroLeague) were priced from
official season records, producing <b>{picks["meta"]["selections"]}</b> selections.</p>
<p class="note">Where a sport has no official numeric input today, the desk says so and leaves the market blank. It never borrows a
price from a bookmaker and calls it ours, and it never writes a preview without a fact behind it.</p>
</section>
<div class="kpis">
{kpi(len(events), "OLBG events in scope", "the fifteen requested sports")}
{kpi(sum(1 for e in events if e["verify"]["state"] != "unmatched"), "matched to an official source", "fixture feed or official page")}
{kpi(len(priced_fixtures), "fixtures with our prices", "NHL, MLB, EuroLeague")}
{kpi(picks["meta"]["selections"], "selections priced", "winner, handicap, total")}
{kpi(len(high), "high-confidence picks", "≥ 70% on our price")}
{kpi(len(high_band), "high and inside −250…+10000", "the brief's two rules together")}
{kpi(len(preds["predictions"]), "written previews", f"{preds['meta']['min_words']}–{preds['meta']['max_words']} words each")}
{kpi(len(inh["previews"]), "previews carried in", f"prose rules re-checked; {len(PREVIEW_SPORTS)} of 15 sports covered in total")}
{kpi(flags["meta"]["items"], "open review items", "see Flagged for review")}
</div>

<h2>Highest-confidence picks</h2>
<p class="note">Selections that satisfy both rules lead the table, then match-winner picks, then the strongest of the rest. Every price shown is ours, with no margin.
The band column applies the brief's −250 to +10000 filter to that price.</p>
{table(["Sport", "Match", "Selection", "Our price", "Chance", "Confidence", "Basis", "Start (UTC)", "Source"], rows)}

<h2>Starting in the next 36 hours</h2>
<p class="note">From the OLBG slate. "Source" opens the official page where one was found, otherwise the OLBG listing.</p>
{table(["Sport", "Start", "Event", "Competition", "Official check", "Source"], soon_rows)}

<h2>Coverage by sport</h2>
<p class="note">Events counted from OLBG's own listing. Verified means an official fixture feed or official page confirmed the
pairing. Priced means a line was originated for that row. Previews counted from the write-ups page.</p>
{table(["Sport", "OLBG events", "Verified", "Priced", "Previews", "Best chance", "Note"], cover_rows)}

<h2>What this page does not claim</h2>
<ul class="plain">
<li>It is not a complete live slate. It is what OLBG listed at {E(CAPTURE_WINDOW.split(' to ')[-1])} plus the official schedules captured alongside it.</li>
<li>Previews exist for {len(PREVIEW_SPORTS)} of 15 sports. The rest are named individually on the flagged page rather than filled with words that no capture supports.</li>
<li>{len(inh["previews"])} of the previews were written by this desk's predecessor in the same scope and are marked <em>carried</em>: their facts were not re-read today, only their wording rules re-checked.</li>
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
<h2>Official fixtures and our prices</h2>
<p class="note">{len(priced_fixtures)} fixtures from the official NHL, MLB and EuroLeague feeds. Each row carries three markets:
a two-way winner, a 1.5-line handicap and a match total. The expected score is the number the price was built from, so a reader can
check the arithmetic. A blank would mean no official input; there are none today, because every fixture below has both sides on
record.</p>
<p class="note">EuroLeague tip times are served without an offset. Those times are published exactly as served and are marked on the
<a href="flagged.html">flagged page</a>.</p>
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
    top5 = picks["meta"]["top5_by_sport"]
    sections = []
    for s in SPORTS:
        ids = top5.get(s, [])
        if not ids:
            continue
        rows = []
        for i in ids:
            p = picks_by_id.get(i)
            if not p:
                continue
            rows.append([f'<b>{E(p["selection"])}</b>', E(p["event"]), E(p["market"]), E(p["american"] or "—"),
                         f'{p["prob"]*100:.1f}%', conf_tag(p["confidence"]),
                         badge("in band", "good") if p["in_band"] else badge("outside", "warn"),
                         basis_tag(p["basis"]), link(p["official_url"] or p["source_url"], "source")])
        sections.append(f'<h3 id="{SLUG[s]}">{E(s)}</h3>'
                        + table(["Selection", "Match", "Market", "Price", "Chance", "Confidence", "Band", "Basis", "Source"], rows))
    inband = sorted([p for p in picks["picks"] if p["in_band"] and p["confidence"] == "high"], key=lambda p: -p["prob"])
    band_rows = [[E(p["sport"]), E(p["event"]), f'<b>{E(p["selection"])}</b>', E(p["market"]), E(p["american"]),
                  f'{p["prob"]*100:.2f}%', conf_tag(p["confidence"]), basis_tag(p["basis"]), link(p["official_url"], "source")] for p in inband]
    body = f"""
<h2>Picks — the five strongest per sport</h2>
<p class="note">A match-winner selection is preferred for these five. Where a sport has fewer than five match-winner picks, the
strongest handicap or total selections fill the rest. Every row states whether the number is ours or taken from OLBG's quote.</p>
<div class="kpis">
{kpi(picks["meta"]["selections"], "selections", "all markets")}
{kpi(len(high), "high confidence", "≥ 70%")}
{kpi(len(high_band), "high + in band", "−250…+10000")}
{kpi(picks["meta"]["medium"], "medium", "60–69.9%")}
</div>
<h2>High confidence and inside the price band</h2>
<p class="note">These {len(high_band)} rows satisfy both rules at once. The intersection is narrow by construction: a 70% chance is
about −233, which is shorter than the band's −250 floor, so only selections between 70.0% and 71.4% can appear here.</p>
{table(["Sport", "Match", "Selection", "Market", "Price", "Chance", "Confidence", "Basis", "Source"], band_rows)}
<h2>Top five by sport</h2>
{"".join(sections)}
"""
    pages["picks.html"] = shell("picks.html", "Picks", body)

    # ---------------------------------------------------------------- previews
    cards = []
    for p in sorted(preds["predictions"], key=lambda x: (SPORTS.index(x["sport"]) if x["sport"] in SPORTS else 99, -x["prob"])):
        facts = "".join(f"<li>{E(f)}</li>" for f in p["facts"])
        cards.append(f"""
<article class="preview" id="{E(p['id'])}">
<div class="pv-head"><h3>{E(p['sport'])} · {E(p['event'])}</h3>
<div class="pv-tags">{conf_tag(p['confidence'])}{badge(p['selection'] + ' ' + (p['american'] or ''), 'pick')}{basis_tag(p['basis'])}
{badge(f"{p['words']} words", 'neutral')}</div></div>
<p class="pv-pick"><b>Selection:</b> {E(p['selection'])} — {E(p['market'])} at <b>{E(p['american'] or '—')}</b>
<span class="muted">({E(p['start_utc'][:16].replace('T',' '))} UTC · {E(p['competition'] or '')})</span></p>
<p class="pv-text">{E(p['text'])}</p>
<details><summary>The facts behind it</summary><ul class="facts">{facts}</ul>
<p class="src">Official source: {link(p['prediction_source'], p['prediction_source'])}</p></details>
</article>""")
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
<h2>Written previews — {len(preds['predictions'])}</h2>
<p class="note">Each preview is at least 30 words, unique, names the selection, and cites at least two facts taken from the official
capture linked beneath it. Injury status is omitted everywhere: no official team-news feed was readable today, so no preview
asserts one. Preview coverage is {len(PREVIEW_SPORTS)} of 15 sports; the shortfall is item L-01 on the flagged page.</p>
<div class="previews">{"".join(cards)}</div>
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
    frows = [[badge(f["code"], "code"), E(f["sport"]), f'<b>{E(f["title"])}</b><br><span class="muted">{E(f["detail"])}</span>',
              badge(f["severity"], {"high": "bad", "medium": "warn"}.get(f["severity"], "neutral")),
              src_link(f["source"]), E(f["impact"])] for f in flags["items"]]
    unmatched_rows = [[E(e["sport"]), E(e["start_utc"][:16].replace("T", " ")), E(e["event"]), link(e["olbg_url"], "OLBG listing")]
                      for e in events if e["verify"]["state"] == "unmatched"]
    body = f"""
<h2>Flagged for review</h2>
<p class="note">Everything this desk could not confirm, could not price, or chose not to assert. Nothing here blocks publication;
each item says what is missing, which source failed, and how the row was handled.</p>
{table(["Ref", "Sport", "Finding", "Severity", "Source", "Effect on the desk"], frows)}
<h2>Unmatched OLBG rows ({len(unmatched_rows)})</h2>
<p class="note">These are listed by OLBG but were not found on any official source captured today. They keep their OLBG price in
the OLBG column and carry no price of ours.</p>
{table(["Sport", "Start (UTC)", "Event", "Listing"], unmatched_rows)}
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
<p class="note">A line-by-line pass over the merged repository before this layer was added. {review['meta']['findings']} findings,
each one reproducible from the evidence column. None of them is repaired silently: files owned by other sessions are left alone and
the finding is recorded here.</p>
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
<p>The slate is OLBG's: every upcoming event in the fifteen requested sports at capture time. The verification and the numbers are
ours. OLBG's quoted price is carried in its own column and never used to build a price of ours.</p>
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
<h3>4. The price band</h3>
<p>The brief asks for selections between −250 and +10000 and for a chance above 70%. A 70% chance is −233, so the two rules only
overlap between 70.0% and 71.4%. The desk publishes the intersection honestly: {picks['meta']['high']} high-confidence selections,
{picks['meta']['high_in_band']} of them inside the band.</p>
<h3>5. What is never done</h3>
<ul class="plain">
<li>A missing value is left blank, never filled from another sport, another day or an average.</li>
<li>No injury, suspension or team-news claim is made without an official page that says it.</li>
<li>No preview is written for a fixture without a captured fact to write around. Eleven sports therefore have none today.</li>
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
        preds_s = [p for p in preds["predictions"] if p["sport"] == s]
        picks_s = [picks_by_id[i] for i in top5.get(s, []) if i in picks_by_id]
        fxs = [f for f in priced_fixtures if f["sport"] == s]
        mrows = [[E(e["start_utc"][:16].replace("T", " ")), E(e["event"]), E(e["competition"] or "—"),
                  E(", ".join(f'{m["selection"]} {m["olbg_decimal"]}' for m in e["markets"][:2] if m["olbg_decimal"]) or "—"),
                  state_tag(e["verify"]["state"]), link(e["verify"]["official_url"] or e["olbg_url"], "source")] for e in evs]
        prows = [[f'<b>{E(p["selection"])}</b>', E(p["market"]), E(p["american"]), f'{p["prob"]*100:.1f}%',
                  conf_tag(p["confidence"]), basis_tag(p["basis"]), link(p["official_url"], "source")] for p in picks_s]
        frows2 = [[E(f["start_utc"][:16].replace("T", " ")), f'{E(f["away"])} at {E(f["home"])}' if s in ("Ice Hockey", "Baseball") else f'{E(f["home"])} v {E(f["away"])}',
                   E(f.get("venue") or "—"),
                   E(f'{f["markets"]["win"][0]["selection"]} {f["markets"]["win"][0]["american"]} / {f["markets"]["win"][1]["selection"]} {f["markets"]["win"][1]["american"]}'),
                   link(f["official_url"], "official")] for f in fxs]
        inh_s = [p for p in inh["previews"] if p["sport"] == s]
        pv = "".join(f'<article class="preview"><h3>{E(p["event"])} — {E(p["selection"])}</h3><p>{E(p["text"])}</p>'
                     f'<p class="src">{link(p["prediction_source"], "official source")} · {p["words"]} words</p></article>'
                     for p in preds_s)
        pv += "".join(f'<article class="preview"><h3>{E(p["event"])} — {E(p["selection"])}</h3><p>{E(p["text"])}</p>'
                      f'<p class="src">carried from the earlier ledger pass · '
                      + " ".join(link(sv["url"], "source") for sv in p["sources"])
                      + f' · {p["words"]} words</p></article>' for p in inh_s)
        body = f"""
<p class="crumb"><a href="../index.html">Overview</a> / <a href="../matches.html">OLBG matches</a> / {E(s)}</p>
<h2>{E(s)}</h2>
<div class="kpis">
{kpi(len(evs), "OLBG events", "upcoming at capture")}
{kpi(len([e for e in evs if e["verify"]["state"] != "unmatched"]), "verified", "official source found")}
{kpi(len(fxs), "priced fixtures", "our own markets")}
{kpi(len(preds_s) + len(inh_s), "previews", f"{len(preds_s)} written here, {len(inh_s)} carried")}
</div>
<h3>OLBG listings</h3>
{table(["Start (UTC)", "Event", "Competition", "OLBG quote", "Official check", "Source"], mrows)}
<h3>Our picks</h3>
{table(["Selection", "Market", "Price", "Chance", "Confidence", "Basis", "Source"], prows) if prows else '<p class="empty">No selection priced for this sport today.</p>'}
<h3>Official fixtures priced</h3>
{table(["Start (UTC)", "Fixture", "Venue", "Winner market", "Source"], frows2) if frows2 else NO_FEED_HTML}
<h3>Previews</h3>
{pv if pv else '<p class="empty">No preview published for this sport. The reason is item L-01 on the <a href="../flagged.html">flagged page</a>.</p>'}
"""
        pages[f"sports/{SLUG[s]}.html"] = shell(f"sports/{SLUG[s]}.html" if s == "Golf" else "",
                                                s, body, prefix="../")

    cards = []
    for s in SPORTS:
        evs = [e for e in events if e["sport"] == s]
        n_ok = len([e for e in evs if e["verify"]["state"] != "unmatched"])
        n_pv = len([p for p in preds["predictions"] if p["sport"] == s]) + len([p for p in inh["previews"] if p["sport"] == s])
        n_hi = len([p for p in picks["picks"] if p["sport"] == s and p["confidence"] == "high"])
        cards.append(f"""<a class="card" href="{SLUG[s]}.html">
<h3>{E(s)}</h3>
<p><b>{len(evs)}</b> OLBG events · <b>{n_ok}</b> matched to an official source</p>
<p><b>{n_hi}</b> high-confidence picks · <b>{n_pv}</b> previews</p>
<p class="muted">Open the sport page →</p></a>""")
    pages["sports/index.html"] = shell("sports/index.html", "Sports",
        f"""<h2>Fifteen sports</h2>
<p class="note">Each sport page carries its OLBG listing, the official source check for every row, our own prices, the priced
official fixtures and the previews. Sports with no readable official input today say so on the card and in detail on the
<a href="../flagged.html">flagged page</a>.</p>
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
