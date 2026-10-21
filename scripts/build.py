"""Validate the evidence snapshot and build the static research site.

Run:  python scripts/build.py
Out:  site/  (index, fixtures, sports/*, methodology, sources, flagged, assets)
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from poisson import evaluate  # noqa: E402

DATA = ROOT / "data/events.json"
OUT = ROOT / "site"

EXCLUDED = {
    "soccer", "football", "american football", "boxing", "ufc", "mma", "hurling",
    "horse racing", "cycling", "specials", "gaelic football",
}
APPROVED_HOSTS = {
    "www.nhl.com", "api-web.nhle.com", "api.nhle.com", "www.olbg.com",
    "www.nba.com", "cdn.nba.com", "stats.nba.com", "data.nba.com",
    "www.mlb.com", "statsapi.mlb.com", "www.icc-cricket.com", "www.atptour.com",
    "www.premrugby.com", "www.premiershiprugby.com", "www.rugby-league.com",
    "www.pdc.tv", "www.wst.tv", "www.eurohandball.com", "en.volleyballworld.com",
    "www.afl.com.au", "www.formula1.com", "www.pgatour.com", "www.gbgb.org.uk",
    "www.world.rugby", "www.ecb.co.uk", "www.iihf.com", "www.ice.hockey",
}
NAV = [
    ("index.html", "Overview", "home"),
    ("fixtures.html", "All fixtures", "fixtures"),
    ("sports/index.html", "Sports", "sports"),
    ("methodology.html", "Methodology", "method"),
    ("sources.html", "Sources", "sources"),
    ("flagged.html", "Flagged for review", "flagged"),
]
STATUS_LABEL = {
    "covered": ("Covered", "ok"),
    "verified_no_games": ("No games (verified)", "neutral"),
    "official_feed_incomplete": ("Official feed incomplete", "bad"),
    "date_not_exposed": ("Date not exposed", "warn"),
    "not_verified": ("Not verified", "warn"),
    "not_a_head_to_head_fixture": ("Not head-to-head", "neutral"),
    "no_official_authority": ("No official authority", "warn"),
}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def link(url: str, label: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in APPROVED_HOSTS:
        raise ValueError(f"Unapproved source URL: {url}")
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} &#8599;</a>'


def _next_day(date: str) -> str:
    from datetime import date as _date, timedelta
    return (_date.fromisoformat(date) + timedelta(days=1)).isoformat()


def stamp(start_utc: str) -> str:
    date, time = start_utc.split("T")
    return f"{date} · {time[:5]} UTC"


def badge(text: str, kind: str) -> str:
    return f'<span class="badge {kind}">{esc(text)}</span>'


def pills(recent: list[str]) -> str:
    out = []
    for item in recent:
        code, _, opp = item.partition(" ")
        kind = "w" if code in ("W", "OTW", "SOW") else "l"
        out.append(f'<span class="pill {kind}">{esc(code)} {esc(opp)}</span>')
    return '<div class="pills">' + "".join(out) + "</div>"


# --------------------------------------------------------------------------- validation

def validate(data: dict) -> None:
    snap = data.get("snapshot") or {}
    for key in ("as_of_utc", "window", "scope", "excluded_sports"):
        if not snap.get(key):
            raise ValueError(f"snapshot.{key} is required")

    model = data.get("model") or {}
    for key in ("name", "home_multiplier", "away_multiplier", "tie_split_home", "edge_high", "edge_medium"):
        if key not in model:
            raise ValueError(f"model.{key} is required")
    if not 0 < model["tie_split_home"] < 1:
        raise ValueError("tie_split_home must be in (0,1)")
    if model["edge_medium"] >= model["edge_high"]:
        raise ValueError("edge_medium must be below edge_high")

    events = data.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("events must be a non-empty list")

    seen = set()
    for row in events:
        rid = row.get("id")
        if not rid or rid in seen:
            raise ValueError(f"missing or duplicate event id: {rid}")
        seen.add(rid)
        if row["sport"].lower() in EXCLUDED:
            raise ValueError(f"{rid}: excluded sport {row['sport']}")
        for key in ("sport", "competition", "date", "start_utc"):
            if not row.get(key):
                raise ValueError(f"{rid}: missing {key}")
        utc_date = row["start_utc"][:10]
        if utc_date not in (row["date"], _next_day(row["date"])):
            raise ValueError(f"{rid}: start_utc does not fall on the fixture date or the following UTC day")
        for side in ("away", "home"):
            team = row.get(side) or {}
            for key in ("name", "abbrev", "coach", "gf_pg", "ga_pg", "pp_pct", "pk_pct", "l10"):
                if key not in team:
                    raise ValueError(f"{rid}: {side}.{key} missing")
            if not isinstance(team["gf_pg"], (int, float)) or not isinstance(team["ga_pg"], (int, float)):
                raise ValueError(f"{rid}: {side} goal rates must be numeric")
            if team["gf_pg"] <= 0 or team["ga_pg"] <= 0:
                raise ValueError(f"{rid}: {side} goal rates must be positive")
            if not team.get("recent"):
                raise ValueError(f"{rid}: {side}.recent is required")
        for key in ("official", "official_api", "olbg"):
            link(row["sources"][key], key)
        if not isinstance(row.get("olbg_listed"), bool):
            raise ValueError(f"{rid}: olbg_listed must be a boolean")

        # model / pick agreement
        mk = evaluate(row, model)
        pick = row.get("pick")
        if not pick:
            raise ValueError(f"{rid}: every fixture needs a selection")
        if pick["selection"] != mk["selection"]:
            raise ValueError(f"{rid}: pick {pick['selection']} != model {mk['selection']}")
        if pick["confidence"] != mk["confidence"]:
            raise ValueError(f"{rid}: confidence {pick['confidence']} != model {mk['confidence']}")
        if pick["confidence"] == "high":
            text = pick.get("narrative") or ""
            if len(text.split()) < 30:
                raise ValueError(f"{rid}: high confidence needs a 30+ word narrative")
            if pick["selection"] not in text:
                raise ValueError(f"{rid}: narrative must name the selection")
        if not (pick.get("basis") or "").strip():
            raise ValueError(f"{rid}: pick needs a factual basis")

    sports = {c["slug"] for c in data["coverage"]}
    if len(sports) != len(data["coverage"]):
        raise ValueError("duplicate coverage slug")
    for cov in data["coverage"]:
        if cov["sport"].lower() in EXCLUDED:
            raise ValueError(f"excluded sport on coverage board: {cov['sport']}")
        for key in ("sport", "slug", "olbg_url", "official_url", "rows", "status", "detail"):
            if cov.get(key) in (None, ""):
                raise ValueError(f"coverage {cov.get('sport')}: missing {key}")
        if cov["status"] not in STATUS_LABEL:
            raise ValueError(f"coverage {cov['sport']}: unknown status {cov['status']}")
        link(cov["olbg_url"], "OLBG")
        link(cov["official_url"], "Official")
        expected = sum(1 for r in events if r["sport"] == cov["sport"])
        if cov["rows"] != expected:
            raise ValueError(f"coverage {cov['sport']}: rows={cov['rows']} but {expected} events")

    for flag in data["flags"]:
        for key in ("item", "sport", "detail", "sources"):
            if not flag.get(key):
                raise ValueError(f"flag missing {key}")
        for url in flag["sources"]:
            link(url, "source")


# --------------------------------------------------------------------------- chrome

def page(title: str, description: str, body: str, active: str, prefix: str = "") -> str:
    items = "".join(
        f'<a class="nav-item{" active" if key == active else ""}" href="{prefix}{path}">'
        f'<span class="swatch"></span>{esc(text)}</a>'
        for path, text, key in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="description" content="{esc(description)}">
<title>{esc(title)} · OLBG research desk</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body><div class="shell">
<aside class="sidebar">
  <div class="brand"><span class="brand-icon">O<span>.</span></span>
    <div><strong>OLBG / research</strong><small>Official-source desk</small></div></div>
  <div class="nav-label">WORKSPACE</div>
  <nav aria-label="Main navigation">{items}</nav>
  <div class="side-note"><span class="dot"></span>Static snapshot<br><small>Not a live feed. Not betting advice.</small></div>
</aside>
<main class="main">
  <header class="topbar"><span>SPORTS INTELLIGENCE <span class="slash">/</span> {esc(title.upper())}</span>
  <span class="top-right">SNAPSHOT MODE <span class="live-dot"></span></span></header>
{body}
<footer>Independent research snapshot assembled {esc(SNAP['as_of_utc'])}. Not affiliated with OLBG, the NHL or any league.
Every published row links to an official competition source. Model prices are this desk's own estimates, not bookmaker prices,
and no outcome is guaranteed. Betting involves risk; if you gamble, keep it legal in your jurisdiction.</footer>
</main></div></body></html>"""


# --------------------------------------------------------------------------- fragments

def market_cells(row: dict, mk: dict) -> str:
    ml, pl, t5 = mk["money_line"], mk["puck_line"], mk["totals"]["5.5"]
    a, h = row["away"]["abbrev"], row["home"]["abbrev"]
    return (
        f'<td class="mono">{esc(h)} {ml["home"]}%<br><span class="muted small">{ml["home_odds"]:.2f} · '
        f'{esc(a)} {ml["away"]}% {ml["away_odds"]:.2f}</span></td>'
        f'<td class="mono">{esc(h)} -1.5 {pl["home_minus_1_5"]}%<br><span class="muted small">{pl["home_minus_1_5_odds"]:.2f} · '
        f'{esc(a)} +1.5 {pl["away_plus_1_5"]}% {pl["away_plus_1_5_odds"]:.2f}</span></td>'
        f'<td class="mono">O 5.5 {t5["over"]}%<br><span class="muted small">{t5["over_odds"]:.2f} · '
        f'U 5.5 {t5["under"]}% {t5["under_odds"]:.2f}</span></td>'
    )


def fixture_table(events: list[dict], model: dict, *, show_status: bool = True) -> str:
    if not events:
        return '<div class="table-scroll"><table><tbody><tr><td class="empty">No fixture on this page has passed official-source verification.</td></tr></tbody></table></div>'
    head = (
        "<thead><tr><th>Matchup</th><th>Competition</th><th>Start</th>"
        '<th class="num">Money line</th><th class="num">Puck line</th><th class="num">Total 5.5</th>'
        "<th>Selection</th><th>Confidence</th><th>Sources</th></tr></thead>"
    )
    rows = []
    for row in events:
        mk = evaluate(row, model)
        src = (
            f'{link(row["sources"]["official"], "NHL")}'
            f'{link(row["sources"]["official_api"], "feed")}'
            f'{link(row["sources"]["olbg"], "OLBG")}'
        )
        rows.append(
            f'<tr><td><span class="match">{esc(row["away"]["name"])}</span> <span class="at">at</span> '
            f'<span class="match">{esc(row["home"]["name"])}</span></td>'
            f'<td>{esc(row["competition"])}<br><span class="muted small">{esc(row["date"])}</span></td>'
            f'<td class="nowrap mono">{esc(stamp(row["start_utc"]))}</td>'
            f'{market_cells(row, mk)}'
            f'<td><strong>{esc(mk["selection"])}</strong><br><span class="muted small">{mk["selection_prob"]}% · {mk["selection_odds"]:.2f}</span></td>'
            f'<td>{badge(mk["confidence"].capitalize(), mk["confidence"])}</td>'
            f'<td class="src">{src}</td></tr>'
        )
    return f'<div class="table-scroll"><table>{head}<tbody>{"".join(rows)}</tbody></table></div>'


def fixture_detail(row: dict, model: dict) -> str:
    mk = evaluate(row, model)
    pick = row["pick"]
    ml, pl, t55, t65 = mk["money_line"], mk["puck_line"], mk["totals"]["5.5"], mk["totals"]["6.5"]
    narr = f'<p class="narr">{esc(pick["narrative"])}</p>' if pick.get("narrative") else ""
    flags = "".join(f'<div class="note"><b>Flagged:</b> {esc(f)}</div>' for f in row.get("flags", []))
    olbg_note = "" if row["olbg_listed"] else (
        '<div class="note"><b>OLBG:</b> no individual OLBG event page was listed for this fixture at capture time, '
        "so the OLBG link points at the league index.</div>"
    )
    form = ""
    for side in ("away", "home"):
        t = row[side]
        form += (
            f'<div class="team"><b>{esc(t["name"])}</b> <span class="muted small">{esc(t["abbrev"])} · coach {esc(t["coach"])}</span>'
            f'<div class="rowof">GF/GP {t["gf_pg"]:.2f} · GA/GP {t["ga_pg"]:.2f} · PP {t["pp_pct"]*100:.1f}% '
            f'(rank {t["pp_rank"]}) · PK {t["pk_pct"]*100:.1f}% (rank {t["pk_rank"]})</div>'
            f'<div class="rowof">Last ten {esc(t["l10"])} · current streak {esc(t["streak"])}</div>'
            f'{pills(t["recent"])}</div>'
        )
    return f"""<article class="fixture">
<div class="fixture-head"><div>
  <h3>{esc(row["away"]["name"])} at {esc(row["home"]["name"])}</h3>
  <div class="meta">{esc(row["competition"])} · {esc(stamp(row["start_utc"]))} · fixture id {esc(row["id"])}</div>
</div><div>{badge(mk["confidence"].capitalize() + " confidence", mk["confidence"])}</div></div>
<div class="pickblock">
  <div class="muted small">OUR SELECTION</div>
  <div class="pickline"><span class="sel">{esc(mk["selection"])}</span>
    <span class="muted small">money line · {mk["selection_prob"]}% · fair price {mk["selection_odds"]:.2f}</span></div>
  {narr}
  <p class="meta"><b>Basis:</b> {esc(pick["basis"])}</p>
</div>
<div class="markets">
  <div class="market"><div class="label">Money line (incl. OT/SO)</div>
    <div class="val">{esc(row["away"]["abbrev"])} {ml["away"]}% · {ml["away_odds"]:.2f}</div>
    <div class="val">{esc(row["home"]["abbrev"])} {ml["home"]}% · {ml["home_odds"]:.2f}</div>
    <div class="sub">60-min model, ties split {int(model["tie_split_home"]*100)}/{int((1-model["tie_split_home"])*100)}</div></div>
  <div class="market"><div class="label">Puck line 1.5</div>
    <div class="val">{esc(row["home"]["abbrev"])} -1.5 · {pl["home_minus_1_5"]}% · {pl["home_minus_1_5_odds"]:.2f}</div>
    <div class="val">{esc(row["away"]["abbrev"])} +1.5 · {pl["away_plus_1_5"]}% · {pl["away_plus_1_5_odds"]:.2f}</div>
    <div class="sub">P(margin &ge; 2) from the same matrix</div></div>
  <div class="market"><div class="label">Match total</div>
    <div class="val">O 5.5 · {t55["over"]}% · {t55["over_odds"]:.2f}</div>
    <div class="val">O 6.5 · {t65["over"]}% · {t65["over_odds"]:.2f}</div>
    <div class="sub">U 5.5 {t55["under"]}% · {t55["under_odds"]:.2f} · U 6.5 {t65["under"]}% · {t65["under_odds"]:.2f}</div></div>
</div>
<div class="markets" style="grid-template-columns:repeat(3,minmax(0,1fr))">
  <div class="market"><div class="label">Expected goals</div><div class="val">{esc(row["away"]["abbrev"])} {mk["lambda_away"]} · {esc(row["home"]["abbrev"])} {mk["lambda_home"]}</div><div class="sub">Model &lambda;, not a league stat</div></div>
  <div class="market"><div class="label">Expected total</div><div class="val">{mk["expected_total"]}</div><div class="sub">Most likely score {esc(mk["most_likely_score"])}</div></div>
  <div class="market"><div class="label">Regulation 3-way</div><div class="val">{mk["regulation_three_way"]["home"]} / {mk["regulation_three_way"]["tie"]} / {mk["regulation_three_way"]["away"]}%</div><div class="sub">Home / tie / away after 60 minutes</div></div>
</div>
<div class="form">{form}</div>
{olbg_note}{flags}
<div class="meta">Sources: {link(row["sources"]["official"], "official game page")} {link(row["sources"]["official_api"], "official game feed")} {link(row["sources"]["olbg"], "OLBG listing")}</div>
</article>"""


# --------------------------------------------------------------------------- pages

SNAP: dict = {}


def write(path: str, text: str) -> None:
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_index(data: dict) -> None:
    events, model, cov = data["events"], data["model"], data["coverage"]
    high = [e for e in events if e["pick"]["confidence"] == "high"]
    covered = [c for c in cov if c["rows"] > 0]
    asof = esc(SNAP["as_of_utc"])
    stats = f"""<div class="stats">
<div><span>Verified fixtures</span><strong>{len(events):02}</strong><small>Teams, date and start read from the official league feed</small></div>
<div><span>High-confidence picks</span><strong>{len(high):02}</strong><small>Each with a 30+ word sourced narrative</small></div>
<div><span>Markets priced</span><strong>3</strong><small>Money line, puck line, match total — per fixture</small></div>
<div><span>Sports with rows</span><strong>{len(covered):02}</strong><small>of {len(cov)} eligible OLBG categories</small></div>
</div>"""
    cov_rows = []
    for c in cov:
        label, kind = STATUS_LABEL[c["status"]]
        cov_rows.append(
            f'<tr><td><a href="sports/{esc(c["slug"])}.html"><strong>{esc(c["sport"])}</strong></a>'
            f'<br><span class="muted small">OLBG id {esc(c["olbg_id"])}</span></td>'
            f'<td class="num mono">{c["rows"]}</td><td>{badge(label, kind)}</td>'
            f'<td class="small">{esc(c["detail"])}</td>'
            f'<td class="src">{link(c["olbg_url"], "OLBG")}{link(c["official_url"], "Official")}</td></tr>'
        )
    body = f"""<section class="hero">
<div class="eyebrow">SNAPSHOT <span class="dash"></span> {asof}</div>
<h1>Fourteen verified fixtures.<br><em>Every number traceable.</em></h1>
<p>This desk reads the official competition feed first, publishes only what that feed supports, and then originates its own
money line, puck line and match total. Where an official source could not confirm a fixture, the row is absent and the gap is written down.</p>
</section>
<div class="notice"><b>Coverage is partial and that is deliberate.</b> One sport has fully verified rows ({len(events)} NHL games across {esc(SNAP["window"])}).
Fifteen other eligible OLBG categories are tracked on the coverage board with the exact reason each has no row.
<a href="flagged.html">Read the flagged items &rarr;</a></div>
{stats}
<div class="section-head"><div><div class="eyebrow">FIXTURE LEDGER</div><h2>Every verified fixture</h2>
<p>Prices are fair odds (1 / probability) from our own model. No bookmaker price is used as an input.</p></div>
<a class="text-link" href="fixtures.html">Open full detail &rarr;</a></div>
{fixture_table(events, model)}
<div class="section-head"><div><div class="eyebrow">COVERAGE BOARD</div><h2>Eligible sports, status by status</h2>
<p>OLBG taxonomy taken from its betting-tips sitemap. Soccer, boxing, UFC/MMA, football (incl. American and Gaelic), hurling,
horse racing, cycling and specials are excluded by the brief and never enter the pipeline.</p></div><span class="count">{len(cov)} categories</span></div>
<div class="table-scroll"><table><thead><tr><th>Sport</th><th class="num">Rows</th><th>Status</th><th>Why</th><th>Sources</th></tr></thead>
<tbody>{"".join(cov_rows)}</tbody></table></div>
<div class="section-head"><div><div class="eyebrow">METHOD</div><h2>How a line is originated</h2></div><a class="text-link" href="methodology.html">Full methodology &rarr;</a></div>
<div class="grid-3">
<div class="card"><h3>1. Official inputs</h3><p>Goals for and against per game, power play, penalty kill and the last ten results for both teams, read from the NHL game-centre payload at {asof}.</p></div>
<div class="card"><h3>2. Poisson score matrix</h3><p>Each attack is blended with the opposing defence and run through a 60-minute Poisson matrix. Ties are split 50/50 for the two-way money line.</p></div>
<div class="card"><h3>3. Fair price and confidence</h3><p>Prices are 1 / probability. Confidence is set by the distance of the selection from a coin flip, using the thresholds declared in the data file.</p></div>
</div>"""
    write("index.html", page("Overview", "Verified fixtures, originated lines and a transparent coverage board.", body, "home"))


def build_fixtures(data: dict) -> None:
    events, model = data["events"], data["model"]
    high = [e for e in events if e["pick"]["confidence"] == "high"]
    body = f"""<section class="hero">
<div class="eyebrow">FULL DETAIL <span class="dash"></span> {esc(SNAP["as_of_utc"])}</div>
<h1>Line by line,<br><em>source by source.</em></h1>
<p>Each card carries the official inputs used, the resulting prices on three markets, the selection, the confidence and the
links needed to re-check the whole thing by hand.</p>
</section>
{fixture_table(events, model)}
<div class="section-head"><div><div class="eyebrow">FIXTURE DETAIL</div><h2>Inputs, markets and selections</h2>
<p>Results lists run most recent first, exactly as the league feed returns them.</p></div><span class="count">{len(events)} fixtures</span></div>
{"".join(fixture_detail(e, model) for e in events)}
<div class="section-head"><div><div class="eyebrow">HIGH CONFIDENCE</div><h2>Published narratives</h2>
<p>Only the {len(high)} high-confidence selections carry a written prediction. Every claim in them is a field in the official payload.</p></div></div>
<div class="grid-2">{"".join(f'<div class="card"><h3>{esc(e["away"]["abbrev"])} at {esc(e["home"]["abbrev"])} {badge("high", "high")}</h3><p>{esc(e["pick"]["narrative"])}</p><div class="meta">{link(e["sources"]["official"], "official game page")}</div></div>' for e in high)}</div>"""
    write("fixtures.html", page("All fixtures", "Every verified fixture with official inputs, originated lines and narratives.", body, "fixtures"))


def build_sports(data: dict) -> None:
    cov = data["coverage"]
    cards = []
    for c in cov:
        label, kind = STATUS_LABEL[c["status"]]
        cards.append(
            f'<a class="card" href="../sports/{esc(c["slug"])}.html" style="text-decoration:none;color:inherit">'
            f'<h3>{esc(c["sport"])} {badge(label, kind)}</h3>'
            f'<p>{esc(c["detail"][:150])}{"…" if len(c["detail"])>150 else ""}</p>'
            f'<div class="meta">{c["rows"]} row(s) · OLBG id {esc(c["olbg_id"])} · {esc(c["official_name"])}</div></a>'
        )
    body = f"""<section class="hero">
<div class="eyebrow">CATEGORIES <span class="dash"></span> {len(cov)} ELIGIBLE</div>
<h1>Every eligible sport,<br><em>including the empty ones.</em></h1>
<p>The brief excludes soccer, boxing, UFC/MMA, football, American football, hurling, horse racing, cycling and specials.
What remains is listed here. An empty category is a finding, not an omission.</p>
</section>
<div class="grid-2">{"".join(cards)}</div>"""
    write("sports/index.html", page("Sports", "Every eligible OLBG sport category with its verification status.", body, "sports", "../"))


def build_sport_pages(data: dict) -> None:
    model = data["model"]
    for c in data["coverage"]:
        rows = [e for e in data["events"] if e["sport"] == c["sport"]]
        label, kind = STATUS_LABEL[c["status"]]
        if rows:
            table = fixture_table(rows, model)
            detail = "".join(fixture_detail(e, model) for e in rows)
            markets = sorted({m for e in rows for m in ("Money line", "Puck line", "Match total")})
            extra = f"""<div class="section-head"><div><div class="eyebrow">MARKETS INVESTIGATED</div><h2>What was priced</h2></div></div>
<div class="grid-3">{"".join(f'<div class="card"><h3>{esc(m)}</h3><p>Priced for all {len(rows)} fixtures from the same 60-minute score matrix.</p></div>' for m in markets)}</div>
<div class="section-head"><div><div class="eyebrow">FIXTURE DETAIL</div><h2>Inputs and selections</h2></div></div>{detail}"""
        else:
            table = ""
            extra = f"""<div class="card" style="margin-bottom:14px"><h3>Why there is no row {badge(label, kind)}</h3>
<p>{esc(c["detail"])}</p>
<div class="meta">{link(c["official_url"], c["official_name"] + " fixtures")} {link(c["olbg_url"], "OLBG category")}</div></div>"""
            table = ("<div class=\"section-head\"><div><div class=\"eyebrow\">FIXTURES</div><h2>Verified fixtures</h2></div>"
                     f'<span class="count">0 rows</span></div>{table}')
        body = f"""<section class="hero">
<div class="eyebrow">CATEGORY <span class="dash"></span> {esc(c["sport"].upper())}</div>
<h1>{esc(c["sport"])}<span style="color:var(--accent)">.</span></h1>
<p>{esc(c["official_name"])}. {esc(c["detail"])}</p>
</section>
<div class="pickline" style="margin-bottom:18px">{badge(label, kind)}<span class="count">{c["rows"]} row(s) published</span>
{link(c["olbg_url"], "OLBG category")}{link(c["official_url"], "Official source")}</div>
{extra}"""
        write(f'sports/{c["slug"]}.html', page(c["sport"], c["detail"][:150], body, "sports", "../"))


def build_methodology(data: dict) -> None:
    m = data["model"]
    body = f"""<section class="hero">
<div class="eyebrow">METHOD <span class="dash"></span> {esc(m["name"])}</div>
<h1>Our own numbers,<br><em>and their limits.</em></h1>
<p>No bookmaker price is copied, scraped or used as an input. Every published price is recomputed from the official inputs stored with the fixture.</p>
</section>
<div class="prose">
<h2>1. What counts as a verified fixture</h2>
<p>A row is published only when the competition's own feed returns the two teams, the fixture date and the start time.
For this snapshot that means the NHL game-centre payload at <code>api-web.nhle.com</code>, plus the NHL game page for each fixture.
OLBG is recorded as the coverage reference the brief asked for, but OLBG is never treated as an official match source.</p>

<h2>2. The model</h2>
<div class="formula">lambda_home = ((home.GF/GP + away.GA/GP) / 2) &times; {m["home_multiplier"]}
lambda_away = ((away.GF/GP + home.GA/GP) / 2) &times; {m["away_multiplier"]}
P(i, j)   = Poisson(i; lambda_home) &times; Poisson(j; lambda_away),  i,j = 0..{m["max_goals"]}</div>
<p>Goals for and against per game come from the official payload. The blend is a standard attack-versus-defence estimate:
each side's scoring rate is averaged with the opponent's concession rate.</p>

<h2>3. Markets</h2>
<ul>
<li><b>Money line (two-way, overtime and shootout included):</b> P(home win) + {m["tie_split_home"]} &times; P(tie). The site's own model assumes the extra period is a coin flip; that assumption is stated, not hidden.</li>
<li><b>Puck line 1.5:</b> P(margin &ge; 2) for the favourite, and its complement for the underdog.</li>
<li><b>Match total:</b> over and under at 5.5 and 6.5 goals, read from the same 60-minute matrix.</li>
<li><b>Regulation three-way:</b> shown for transparency; it is not the market the selection is taken from.</li>
</ul>

<h2>4. Prices and confidence</h2>
<p>Prices are fair decimal odds, <code>1 / probability</code>, rounded to two decimals. No margin is added, so these are not
sportsbook prices and should not be read as ones.</p>
<p>Confidence is a property of this model, not a claim about the real world. The selected side is always the side the model prices shorter.
The label then comes from how far that side sits from a coin flip:</p>
<div class="table-scroll"><table><thead><tr><th>Label</th><th>Condition</th><th>Meaning</th></tr></thead><tbody>
<tr><td>{badge("high", "high")}</td><td>edge &ge; {m["edge_high"]*100:.0f} points</td><td>The model separates the sides by at least {m["edge_high"]*200:.0f} points of probability.</td></tr>
<tr><td>{badge("medium", "medium")}</td><td>{m["edge_medium"]*100:.0f}–{m["edge_high"]*100:.0f} points</td><td>A moderate model edge.</td></tr>
<tr><td>{badge("low", "low")}</td><td>under {m["edge_medium"]*100:.0f} points</td><td>Close to a coin flip; published for completeness only.</td></tr>
</tbody></table></div>

<h2>5. Narratives</h2>
<p>Only high-confidence selections carry a written prediction, and each is at least 30 words. Every factual statement in a
narrative maps to a field in the official payload: goals for and against per game, points percentage, power-play and penalty-kill
rank, the last-ten record, the listed results, the head coach or the schedule. Nothing is added from memory.</p>

<h2>6. Model parameters are assumptions</h2>
<p>The home multiplier ({m["home_multiplier"]}), away multiplier ({m["away_multiplier"]}), tie split ({m["tie_split_home"]}) and the confidence
edges are choices made by this desk. They are <b>not</b> league statistics and are not presented as verified facts. They live in
<code>data/events.json</code> under <code>model</code>, so anyone can change them and re-run <code>scripts/build.py</code> to reproduce every price.</p>

<h2>7. What the model does not do</h2>
<ul>
<li>It does not adjust for rest, back-to-backs, travel or schedule density.</li>
<li>It does not know who starts in goal, who is injured, scratched or suspended.</li>
<li>It does not use shots, expected goals, special-teams match-up or score effects.</li>
<li>It does not shrink small samples. Early-season rates are carried in exactly as published, which is why some prices look extreme.</li>
<li>It does not compare against market prices, so it cannot claim value against a bookmaker.</li>
</ul>

<h2>8. Reproduction</h2>
<div class="formula">python -m unittest discover -s tests -v
python scripts/build.py
python -m http.server 8000 -d site</div>
<p>The build refuses to run if a row lacks an approved source host, if a selection disagrees with the model, if a high-confidence
narrative is under 30 words or fails to name its selection, or if the coverage board's row counts disagree with the fixture list.</p>
</div>"""
    write("methodology.html", page("Methodology", "How lines are originated, priced and rated, and what the model cannot do.", body, "method"))


def build_sources(data: dict) -> None:
    rows = []
    for e in data["events"]:
        rows.append(
            f'<tr><td><strong>{esc(e["away"]["abbrev"])} at {esc(e["home"]["abbrev"])}</strong><br>'
            f'<span class="muted small">{esc(e["date"])}</span></td>'
            f'<td class="src">{link(e["sources"]["official"], "NHL game page")}</td>'
            f'<td class="src">{link(e["sources"]["official_api"], "Official feed (JSON)")}</td>'
            f'<td class="src">{link(e["sources"]["olbg"], "OLBG")}{badge("listed", "ok") if e["olbg_listed"] else badge("index only", "neutral")}</td></tr>'
        )
    cov_rows = "".join(
        f'<tr><td><strong>{esc(c["sport"])}</strong></td><td class="src">{link(c["official_url"], c["official_name"])}</td>'
        f'<td class="src">{link(c["olbg_url"], "OLBG category")}</td><td>{esc(c["status"])}</td></tr>'
        for c in data["coverage"]
    )
    tax = "".join(f'<li><b>{esc(s)}</b> — OLBG sport id {esc(i)}</li>' for s, i in [
        ("Football / soccer", 1), ("Horse racing", 2), ("Tennis", 3), ("Basketball", 4), ("Golf", 5),
        ("Cricket", 7), ("Snooker", 8), ("Rugby union", 9), ("Rugby league", 10), ("American football", 11),
        ("Baseball", 12), ("Ice hockey", 13), ("Motor racing", 14), ("Darts", 15), ("Boxing", 16),
        ("Cycling", 17), ("Handball", 20), ("Volleyball", 21), ("Aussie rules", 22), ("eSports", 23),
        ("Gaelic football", 25), ("Greyhounds", 28),
    ])
    body = f"""<section class="hero">
<div class="eyebrow">SOURCE REGISTER <span class="dash"></span> {esc(SNAP["as_of_utc"])}</div>
<h1>Every link,<br><em>in one place.</em></h1>
<p>This is the manual-review list. Each fixture shows the official game page, the machine-readable official feed it was read from,
and the OLBG reference. Category sources follow.</p>
</section>
<div class="section-head"><div><div class="eyebrow">FIXTURES</div><h2>Row-level sources</h2></div><span class="count">{len(data["events"])} rows</span></div>
<div class="table-scroll"><table><thead><tr><th>Fixture</th><th>Official game page</th><th>Official feed</th><th>OLBG reference</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<div class="section-head"><div><div class="eyebrow">CATEGORIES</div><h2>Governing-body sources</h2></div><span class="count">{len(data["coverage"])} categories</span></div>
<div class="table-scroll"><table><thead><tr><th>Sport</th><th>Official source</th><th>OLBG</th><th>Status</th></tr></thead>
<tbody>{cov_rows}</tbody></table></div>
<div class="prose"><h2>OLBG taxonomy observed</h2>
<p>Sport ids below were read from OLBG's betting-tips sitemap and category URLs. Categories struck out by the brief are still listed,
because the exclusion has to be explicit rather than implied.</p><ul>{tax}</ul>
<p>OLBG is used as the coverage reference. It is not treated as an official match source, and its tipster selections are not our picks.</p></div>"""
    write("sources.html", page("Sources", "Row-level and category-level source links for manual review.", body, "sources"))


def build_flagged(data: dict) -> None:
    flags = "".join(
        f'<tr><td><strong>{esc(f["item"])}</strong><br><span class="muted small">{esc(f["sport"])}</span></td>'
        f'<td class="small">{esc(f["detail"])}</td>'
        f'<td class="src">{"".join(link(u, "source") for u in f["sources"])}</td></tr>'
        for f in data["flags"]
    )
    gaps = "".join(
        f'<tr><td><strong>{esc(c["sport"])}</strong></td><td>{badge(STATUS_LABEL[c["status"]][0], STATUS_LABEL[c["status"]][1])}</td>'
        f'<td class="small">{esc(c["detail"])}</td>'
        f'<td class="src">{link(c["official_url"], "Official")}{link(c["olbg_url"], "OLBG")}</td></tr>'
        for c in data["coverage"] if c["rows"] == 0
    )
    body = f"""<section class="hero">
<div class="eyebrow">TRANSPARENCY <span class="dash"></span> {esc(SNAP["as_of_utc"])}</div>
<h1>Flagged for review<span style="color:var(--flag)">.</span></h1>
<p>Open questions stay visible. None of these items blocks the rest of the dataset; each one is a place where an official source
did not give us what the brief assumes is available.</p>
</section>
<div class="notice"><b>Nothing on this page is a verified betting claim.</b> It is the audit trail: what disagreed, what was missing,
and which links you need to check it yourself.</div>
<div class="section-head"><div><div class="eyebrow">IRREGULARITIES</div><h2>Open items</h2></div><span class="count">{len(data["flags"])} items</span></div>
<div class="table-scroll"><table><thead><tr><th>Item</th><th>What was found</th><th>Review sources</th></tr></thead><tbody>{flags}</tbody></table></div>
<div class="section-head"><div><div class="eyebrow">COVERAGE GAPS</div><h2>Eligible categories with no row</h2>
<p>Each gap states the blocker and links the source that would be used next.</p></div><span class="count">{sum(1 for c in data["coverage"] if c["rows"]==0)} categories</span></div>
<div class="table-scroll"><table><thead><tr><th>Sport</th><th>Status</th><th>Why there is no row</th><th>Sources</th></tr></thead><tbody>{gaps}</tbody></table></div>"""
    write("flagged.html", page("Flagged for review", "Irregularities, verification gaps and the sources to check them.", body, "flagged"))


def build() -> None:
    global SNAP
    data = json.loads(DATA.read_text(encoding="utf-8"))
    validate(data)
    SNAP = data["snapshot"]
    build_index(data)
    build_fixtures(data)
    build_sports(data)
    build_sport_pages(data)
    build_methodology(data)
    build_sources(data)
    build_flagged(data)
    write(".nojekyll", "")
    high = sum(1 for e in data["events"] if e["pick"]["confidence"] == "high")
    print(f"built {len(data['events'])} fixtures ({high} high confidence), "
          f"{len(data['coverage'])} category pages, {len(data['flags'])} flags")


if __name__ == "__main__":
    build()
