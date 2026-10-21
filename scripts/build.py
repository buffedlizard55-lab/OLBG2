"""Validate the evidence snapshot, originate lines, and build the static dashboard."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from model import (
    choose_selection,
    confidence_label,
    implied,
    nba_market,
    nhl_market,
    shrunk_goal_rate,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "site"
OFFICIAL_HOSTS = {"www.nhl.com", "www.nba.com", "api.nhle.com", "api-web.nhle.com", "statsapi.mlb.com"}
REFERENCE_HOSTS = {"www.olbg.com"}
SNAPSHOT_LABEL = "2026-10-21 05:55 UTC"
MARKETS = {"Money line", "Puck line", "Spread", "Total", "Win match"}


# ------------------------------------------------------------------ helpers


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def host_of(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"URL must be absolute https: {url}")
    return parsed.netloc.lower()


def check_url(url: str, hosts: set[str], label: str) -> str:
    host = host_of(url)
    if host not in hosts:
        raise ValueError(f"{label}: host {host} is not approved ({url})")
    return url


def a(url: str | None, label: str, cls: str = "") -> str:
    if not url:
        return '<span class="muted">Not published</span>'
    klass = f' class="{cls}"' if cls else ""
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer"{klass}>{esc(label)}</a>'


def price(value: int | None) -> str:
    if value is None:
        return "—"
    return f"+{value}" if value > 0 else str(value)


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def badge(label: str, reason: str = "") -> str:
    title = f' title="{esc(reason)}"' if reason else ""
    return f'<span class="badge {esc(label)}"{title}>{esc(label)}</span>'


def num(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:+.{digits}f}" if isinstance(value, float) else str(value)


# ------------------------------------------------------------------ validation


def validate(data: dict) -> None:
    meta = data["meta"]
    params = meta["params"]
    for key in ("nhl_shrink_games", "nhl_home_goals", "nhl_logistic_scale", "nhl_total_sd",
                "nhl_league_total", "nba_home_points", "nba_logistic_scale", "high_edge",
                "medium_edge", "min_games_for_high", "min_prediction_words"):
        if key not in params:
            raise ValueError(f"meta.params missing {key}")
    if not meta.get("snapshot_utc"):
        raise ValueError("missing snapshot timestamp")

    sources = data["sources"]["sources"]
    by_url = {}
    for src in sources:
        check_url(src["url"], OFFICIAL_HOSTS | REFERENCE_HOSTS, "source")
        if src["kind"] == "official":
            check_url(src["url"], OFFICIAL_HOSTS, "official source")
        elif src["kind"] == "reference":
            check_url(src["url"], REFERENCE_HOSTS, "reference source")
        else:
            raise ValueError(f"unknown source kind {src['kind']}")
        if src["url"] in by_url:
            raise ValueError(f"duplicate source {src['url']}")
        by_url[src["url"]] = src

    coverage = {row["sport"]: row for row in data["coverage"]["coverage"]}
    if not coverage:
        raise ValueError("coverage registry is empty")
    for row in coverage.values():
        if row["status"] not in {"covered", "no-fixtures", "unverified", "excluded"}:
            raise ValueError(f"bad coverage status {row['status']}")
        if row["official_url"]:
            check_url(row["official_url"], OFFICIAL_HOSTS, "coverage official")
        if row["olbg_url"]:
            check_url(row["olbg_url"], REFERENCE_HOSTS, "coverage olbg")

    excluded = {s.lower() for s in meta["excluded_sports"]}
    fixtures = data["fixtures"]["fixtures"]
    if not fixtures:
        raise ValueError("no fixtures")
    seen = set()
    for fx in fixtures:
        if fx["id"] in seen:
            raise ValueError(f"duplicate fixture id {fx['id']}")
        seen.add(fx["id"])
        if fx["sport"].lower() in excluded:
            raise ValueError(f"excluded sport in fixtures: {fx['sport']}")
        if fx["sport_slug"] not in {row["slug"] for row in coverage.values()}:
            raise ValueError(f"fixture sport_slug not registered: {fx['sport_slug']}")
        if fx["date"] < meta["window_start"] or fx["date"] > meta["window_end"]:
            raise ValueError(f"fixture {fx['id']} outside the published window")
        check_url(fx["official_url"], OFFICIAL_HOSTS, f"fixture {fx['id']}")
        if fx["olbg_url"]:
            check_url(fx["olbg_url"], REFERENCE_HOSTS, f"fixture {fx['id']} olbg")
        if fx["engine"] not in {"nhl", "nba"}:
            raise ValueError(f"unknown engine {fx['engine']}")

    teams = data["nhl_teams"]["teams"]
    for abbr in {fx["inputs"]["home"] for fx in fixtures if fx["engine"] == "nhl"} | {
            fx["inputs"]["away"] for fx in fixtures if fx["engine"] == "nhl"}:
        if abbr not in teams:
            raise ValueError(f"missing NHL team input {abbr}")
        team = teams[abbr]
        if team["gp"] != team["w"] + team["l"] + team["otl"]:
            raise ValueError(f"NHL team {abbr}: W+L+OT does not equal GP")
        if team["gp"] <= 0 or team["gf"] < 0 or team["ga"] < 0:
            raise ValueError(f"NHL team {abbr}: impossible totals")

    picks = data["picks"]["picks"]
    narratives = {}
    for fid, pick in picks.items():
        if fid not in seen:
            raise ValueError(f"pick for unknown fixture {fid}")
        if pick["market"] not in MARKETS:  # pragma: no cover - defensive
            raise ValueError(f"unknown market {pick['market']}")
        words = len(pick["narrative"].split())
        if words < params["min_prediction_words"]:
            raise ValueError(f"prediction for {fid} is only {words} words")
        norm = re.sub(r"\W+", " ", pick["narrative"].lower()).strip()
        if norm in narratives:
            raise ValueError(f"prediction for {fid} duplicates {narratives[norm]}")
        narratives[norm] = fid
        if not pick["sources"]:
            raise ValueError(f"prediction for {fid} has no sources")
        for url in pick["sources"]:
            if url not in by_url:
                raise ValueError(f"prediction for {fid} cites an unregistered source: {url}")
        if not pick.get("facts"):
            raise ValueError(f"prediction for {fid} has no fact list")

    for flag in data["flagged"]["flagged"]:
        for url in flag["sources"]:
            if url not in by_url:
                raise ValueError(f"flag {flag['id']} cites an unregistered source: {url}")


# ------------------------------------------------------------------ computation


def build_rows(data: dict) -> list[dict]:
    meta = data["meta"]
    params = meta["params"]
    teams = data["nhl_teams"]["teams"]
    picks = data["picks"]["picks"]
    rows = []
    for fx in data["fixtures"]["fixtures"]:
        if fx["engine"] == "nhl":
            home = teams[fx["inputs"]["home"]]
            away = teams[fx["inputs"]["away"]]
            market = nhl_market(home, away, params)
            sample_ok = min(home["gp"], away["gp"]) >= params["min_games_for_high"]
            baseline = False
        else:
            home = {"abbr": fx["home"], "name": fx["home_name"], "gp": 0}
            away = {"abbr": fx["away"], "name": fx["away_name"], "gp": 0}
            market = nba_market(home, away, params)
            sample_ok = False
            baseline = True

        ml = market["money_line"]
        primary = choose_selection(market)["primary"]
        pick = picks.get(fx["id"])
        if pick:
            if pick["market"] != "Money line":
                raise ValueError(f"only money-line picks are wired for {fx['id']}")
            if pick["selection"] != ml["favoured"]:
                raise ValueError(
                    f"pick for {fx['id']} selects {pick['selection']} but the model favours {ml['favoured']}"
                )
        selection = pick["selection"] if pick else primary["selection"]
        odds = ml["home"] if selection == ml["home_team"] else ml["away"]
        probability = ml["p_home"] if selection == ml["home_team"] else ml["p_away"]
        edge = abs(ml["p_home"] - 0.5)
        evidence = bool(pick and fx["official_url"] in pick["sources"])
        label, reason = confidence_label(edge, evidence=evidence, sample_ok=sample_ok,
                                        baseline=baseline, params=params)
        if pick and not evidence:
            raise ValueError(f"prediction for {fx['id']} must cite its own official page")
        rows.append({
            "fixture": fx, "market": market, "pick": pick, "selection": selection,
            "odds": odds, "probability": probability, "edge": edge,
            "confidence": label, "confidence_reason": reason,
            "evidence": evidence, "leans": choose_selection(market)["leans"],
        })

    for row in rows:
        if row["confidence"] == "high" and not row["pick"]:
            raise ValueError(f"high confidence without a prediction: {row['fixture']['id']}")
    return rows


# ------------------------------------------------------------------ rendering


NAV = [
    ("index.html", "Overview", "home"),
    ("picks.html", "Pick sheet", "picks"),
    ("sports/index.html", "Sports", "sports"),
    ("methodology.html", "Method", "method"),
    ("sources.html", "Sources", "sources"),
    ("flagged.html", "Flagged", "flagged"),
]


def page(title: str, body: str, active: str, prefix: str = "", subtitle: str = "") -> str:
    items = "".join(
        f'<a class="nav-item{" active" if key == active else ""}" href="{prefix}{path}">'
        f'<span>{esc(text)}</span></a>'
        for path, text, key in NAV
    )
    sub = f'<span class="crumb">{esc(subtitle)}</span>' if subtitle else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>{esc(title)} · OLBG research desk</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<div class="shell">
<aside class="sidebar">
  <div class="brand"><span class="mark">O<span>.</span></span><div><strong>OLBG research</strong><small>Independent evidence desk</small></div></div>
  <div class="nav-label">Workspace</div>
  <nav aria-label="Main">{items}</nav>
  <div class="side-note"><span class="dot"></span><div><strong>Snapshot</strong><br><small>{esc(SNAPSHOT_LABEL)}</small></div></div>
  <div class="side-note quiet"><small>Not affiliated with OLBG, the NHL or the NBA. No betting advice.</small></div>
</aside>
<main class="main">
  <header class="topbar"><span>SPORTS INTELLIGENCE <span class="slash">/</span> {esc(title.upper())}</span><span class="top-right">{sub}<span class="live-dot"></span> RESEARCH MODE</span></header>
  {body}
  <footer>Independent research snapshot · fair odds only · no guaranteed outcomes · <a href="{prefix}methodology.html">method</a> · <a href="{prefix}flagged.html">flagged items</a></footer>
</main></div>
<script>
document.querySelectorAll('[data-filter]').forEach(function (btn) {{
  btn.addEventListener('click', function () {{
    var group = btn.getAttribute('data-group');
    document.querySelectorAll('[data-group="' + group + '"]').forEach(function (b) {{ b.classList.toggle('on', b === btn); }});
    var want = btn.getAttribute('data-filter');
    document.querySelectorAll('[data-conf]').forEach(function (row) {{
      row.hidden = want !== 'all' && row.getAttribute('data-conf') !== want;
    }});
  }});
}});
</script>
</body></html>"""


def kpi(label: str, value: str, note: str) -> str:
    return f'<div class="kpi"><span>{esc(label)}</span><strong>{esc(value)}</strong><small>{esc(note)}</small></div>'


def pick_table(rows: list[dict], prefix: str = "", show_narrative: bool = False) -> str:
    body = []
    for row in rows:
        fx, market, pick = row["fixture"], row["market"], row["pick"]
        links = a(fx["official_url"], "League") + (" · " + a(fx["olbg_url"], "OLBG") if fx["olbg_url"] else "")
        narrative = ""
        if show_narrative and pick:
            sources = " ".join(a(u, f"source {i + 1}") for i, u in enumerate(pick["sources"]))
            facts = "".join(f"<li>{esc(f)}</li>" for f in pick["facts"])
            narrative = (
                f'<div class="prediction"><p>{esc(pick["narrative"])}</p>'
                f'<div class="prediction-meta"><span><strong>Verified inputs</strong></span><ul>{facts}</ul>'
                f'<span class="src">{sources}</span></div></div>'
            )
        body.append(
            f'<tr data-conf="{esc(row["confidence"])}">'
            f'<td class="when mono">{esc(fx["date"][5:])}<br><span class="muted">{esc(fx["time"])}</span></td>'
            f'<td><span class="tag">{esc(fx["league"])}</span></td>'
            f'<td><strong>{esc(fx["away"])}</strong> at <strong>{esc(fx["home"])}</strong>'
            f'<br><span class="muted">{esc(fx["away_name"])} at {esc(fx["home_name"])}</span></td>'
            f'<td><strong>{esc(row["selection"])}</strong><br><span class="muted">{esc(row["pick"]["market"] if pick else "Money line")}</span></td>'
            f'<td class="mono">{price(row["odds"])}</td>'
            f'<td class="mono">{pct(row["probability"])}</td>'
            f'<td class="mono">{row["edge"] * 100:.1f} pts</td>'
            f'<td>{badge(row["confidence"], row["confidence_reason"])}</td>'
            f'<td class="src">{links}</td></tr>'
            + (f'<tr class="pred-row" data-conf="{esc(row["confidence"])}"><td colspan="9">{narrative}</td></tr>' if narrative else "")
        )
    return (
        '<div class="table-scroll"><table class="pick-table"><thead><tr>'
        '<th>When</th><th>League</th><th>Matchup</th><th>Selection</th><th>Price</th>'
        '<th>Model prob.</th><th>Edge</th><th>Confidence</th><th>Sources</th>'
        "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"
    )


def market_cell(market: dict) -> str:
    ml = market["money_line"]
    hc = market["handicap"]
    tot = market["total"]
    total = (f'O {tot["line"]:g} {price(tot["over"])} / U {tot["line"]:g} {price(tot["under"])}'
             if tot else '<span class="muted">No total originated</span>')
    return (
        f'<div class="mk"><span>ML</span><b>{esc(ml["away_team"].split()[-1])} {price(ml["away"])}</b>'
        f'<b>{esc(ml["home_team"].split()[-1])} {price(ml["home"])}</b></div>'
        f'<div class="mk"><span>{"Puck line" if market["engine"] == "nhl" else "Spread"}</span>'
        f'<b>{esc(ml["away_team"].split()[-1])} {hc["line_away"]:+g} {price(hc["away"])}</b>'
        f'<b>{esc(ml["home_team"].split()[-1])} {hc["line_home"]:+g} {price(hc["home"])}</b></div>'
        f'<div class="mk"><span>Total</span><b class="wide">{total}</b></div>'
    )


def fixture_table(rows: list[dict], prefix: str = "") -> str:
    body = []
    for row in rows:
        fx = row["fixture"]
        body.append(
            f'<tr><td class="when mono">{esc(fx["date"][5:])}<br><span class="muted">{esc(fx["time"])}</span></td>'
            f'<td><strong>{esc(fx["away"])} @ {esc(fx["home"])}</strong><br>'
            f'<span class="muted">{esc(fx["away_name"])} at {esc(fx["home_name"])}</span>'
            f'{"<br><span class=muted>" + esc(fx["venue"]) + "</span>" if fx.get("venue") else ""}</td>'
            f'<td>{market_cell(row["market"])}</td>'
            f'<td><strong>{esc(row["selection"])}</strong> {price(row["odds"])}<br>'
            f'{badge(row["confidence"], row["confidence_reason"])}</td>'
            f'<td class="src">{a(fx["official_url"], "League page")}'
            f'{"<br>" + a(fx["olbg_url"], "OLBG page") if fx["olbg_url"] else ""}</td></tr>'
        )
    return (
        '<div class="table-scroll"><table><thead><tr><th>When</th><th>Matchup</th>'
        '<th>Our lines</th><th>Pick</th><th>Sources</th></tr></thead><tbody>'
        + "".join(body) + "</tbody></table></div>"
    )


def coverage_chips(data: dict) -> str:
    chips = []
    for row in data["coverage"]["coverage"]:
        inner = f'<span>{esc(row["sport"])}</span><b>{esc(str(row["fixtures"]))}</b>'
        if row["status"] == "covered":
            chips.append(f'<a class="chip {esc(row["status"])}" href="sports/{esc(row["slug"])}.html">{inner}</a>')
        else:
            chips.append(f'<span class="chip {esc(row["status"])}" title="{esc(row["note"])}">{inner}</span>')
    return '<div class="chips">' + "".join(chips) + "</div>"


# ------------------------------------------------------------------ pages


def build() -> dict:
    data = {
        "meta": load("meta.json"),
        "sources": load("sources.json"),
        "nhl_teams": load("team_inputs/nhl.json"),
        "fixtures": load("fixtures.json"),
        "picks": load("picks.json"),
        "flagged": load("flagged.json"),
        "coverage": load("coverage.json"),
    }
    validate(data)
    rows = build_rows(data)
    meta = data["meta"]
    params = meta["params"]
    coverage = data["coverage"]["coverage"]
    covered = [c for c in coverage if c["status"] == "covered"]
    unverified = [c for c in coverage if c["status"] == "unverified"]
    high = [r for r in rows if r["confidence"] == "high"]
    medium = [r for r in rows if r["confidence"] == "medium"]
    low = [r for r in rows if r["confidence"] == "low"]
    markets_priced = sum(2 + (1 if r["market"]["total"] else 0) for r in rows)
    flags = data["flagged"]["flagged"]

    OUT.mkdir(exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)
    (OUT / "data").mkdir(exist_ok=True)

    # ---------------- overview
    hero = (
        '<section class="hero"><div class="eyebrow">SNAPSHOT <span class="dash"></span> '
        f'{esc(meta["snapshot_utc"])}</div><h1>The slate,<br><em>priced and sourced.</em></h1>'
        '<p>Every fixture below was matched to an official league page. Every price is originated here, '
        'from published team rates, with no bookmaker input. Where the evidence runs out, the cell is blank and '
        'the item is on the flagged page.</p></section>'
    )
    notice = (
        '<div class="notice"><b>Scope.</b> NHL Oct 21-22 and NBA Oct 21 are covered. '
        f'{len(unverified)} eligible sports could not be verified in this session and carry no rows. '
        'NBA prices are baseline only. <a href="flagged.html">See what is open →</a></div>'
    )
    kpis = (
        '<div class="kpis">'
        + kpi("Fixtures verified", str(len(rows)), "each with its own official page")
        + kpi("Sports covered", str(len(covered)), "NHL and NBA")
        + kpi("Markets priced", str(markets_priced), "money line, handicap, total")
        + kpi("High confidence", str(len(high)), "model edge + evidence pack")
        + kpi("Flagged items", str(len(flags)), "open questions, published")
        + "</div>"
    )
    section = (
        '<div class="section-head"><div><div class="eyebrow">PICK SHEET</div><h2>Every match, one selection</h2></div>'
        '<a class="text-link" href="picks.html">Full pick sheet →</a></div>'
    )
    legends = (
        '<div class="legend"><span class="muted">Confidence is computed, not chosen:</span>'
        f' high ≥ {params["high_edge"] * 100:.0f} points of win-probability edge <em>and</em> an official evidence pack; '
        f'medium ≥ {params["medium_edge"] * 100:.0f} pts; everything else is low.</div>'
    )
    cov = (
        '<div class="section-head"><div><div class="eyebrow">COVERAGE</div><h2>Which sports are priced</h2></div>'
        '<a class="text-link" href="sports/index.html">Coverage detail →</a></div>' + coverage_chips(data)
    )
    build_note = (
        '<div class="cards2"><article class="card"><h3>How the numbers are made</h3>'
        '<p>NHL ratings are goals for and against per game, shrunk toward the league mean by 12 games, plus a '
        '0.25-goal home edge, converted with a logistic curve. NBA ratings are league-average because the season '
        'is one game old. Prices are no-vig fair odds.</p>'
        '<a class="text-link" href="methodology.html">Read the method →</a></article>'
        '<article class="card"><h3>What is deliberately blank</h3>'
        '<p>No total is published for the NBA. No venue is filled in unless the fetched page named it. No pick is '
        'labelled high without a cited gamecenter pack. Blank means unverified here.</p>'
        '<a class="text-link" href="flagged.html">Open items →</a></article></div>'
    )
    (OUT / "index.html").write_text(
        page("Overview", hero + notice + kpis + section + legends + pick_table(rows) + cov + build_note, "home", subtitle="2026-10-21/22"),
        encoding="utf-8",
    )

    # ---------------- pick sheet
    filters = (
        '<div class="filters"><span class="muted">Filter</span>'
        '<button class="pill on" data-group="conf" data-filter="all">All</button>'
        '<button class="pill" data-group="conf" data-filter="high">High</button>'
        '<button class="pill" data-group="conf" data-filter="medium">Medium</button>'
        '<button class="pill" data-group="conf" data-filter="low">Low</button></div>'
    )
    high_cards = "".join(
        f'<article class="prediction-card"><div class="eyebrow">HIGH CONFIDENCE <span class="dash"></span> '
        f'{esc(r["fixture"]["league"])}</div>'
        f'<h3>{esc(r["selection"])} <span class="price mono">{price(r["odds"])}</span></h3>'
        f'<p class="matchup-line">{esc(r["fixture"]["away_name"])} at {esc(r["fixture"]["home_name"])} · '
        f'{esc(r["fixture"]["date"])} {esc(r["fixture"]["time"])}</p>'
        f'<p>{esc(r["pick"]["narrative"])}</p>'
        f'<div class="facts"><ul>' + "".join(f"<li>{esc(f)}</li>" for f in r["pick"]["facts"]) + "</ul></div>"
        f'<div class="src">' + " ".join(a(u, f"source {i + 1}") for i, u in enumerate(r["pick"]["sources"]))
        + f' · {a(r["fixture"]["official_url"], "official game page")}</div></article>'
        for r in high
    )
    picks_body = (
        f'<section class="subhero"><div class="eyebrow">PICK SHEET <span class="dash"></span> {esc(meta["snapshot_utc"])}</div>'
        '<h1>One selection per match<span class="accent">.</span></h1>'
        '<p>Model probability, fair price, edge and confidence for every verified fixture. Predictions appear in full '
        f'for the {len(high)} high-confidence picks; medium and low picks carry the model line only.</p></section>'
        '<div class="kpis small">' + kpi("High", str(len(high)), "with written prediction") + kpi("Medium", str(len(medium)), "model edge only")
        + kpi("Low", str(len(low)), "no edge") + "</div>"
        + '<div class="section-head"><div><div class="eyebrow">PREDICTIONS</div><h2>High confidence</h2></div></div>'
        + '<div class="prediction-grid">' + high_cards + "</div>"
        + '<div class="section-head below"><div><div class="eyebrow">ALL SELECTIONS</div><h2>Pick sheet</h2></div></div>'
        + filters + pick_table(rows, show_narrative=True)
    )
    (OUT / "picks.html").write_text(page("Pick sheet", picks_body, "picks", subtitle=f"{len(rows)} fixtures"), encoding="utf-8")

    # ---------------- sports index
    status_label = {"covered": "Covered", "no-fixtures": "No fixtures", "unverified": "Unverified", "excluded": "Excluded"}
    cards = []
    for row in coverage:
        cards.append(
            f'<article class="sport-card {esc(row["status"])}"><div class="sport-head"><h3>{esc(row["sport"])}</h3>'
            f'<span class="chip {esc(row["status"])}">{esc(status_label[row["status"]])}</span></div>'
            f'<p>{esc(row["note"])}</p><div class="sport-meta"><span class="mono">{row["fixtures"]} fixtures</span>'
            f'{a(row["official_url"], "Official")} {a(row["olbg_url"], "OLBG")}'
            f'{" " + a("../sports/" + row["slug"] + ".html", "Open →") if row["status"] == "covered" else ""}</div></article>'
        )
    sports_body = (
        '<section class="subhero"><div class="eyebrow">COVERAGE MAP</div><h1>Every sport, and its status<span class="accent">.</span></h1>'
        '<p>Eligible sports are listed with their verification state. A sport without an official check carries no '
        'fixture, no price and no pick. Excluded sports are recorded so the boundary is explicit.</p></section>'
        + '<div class="sport-grid">' + "".join(cards) + "</div>"
    )
    (OUT / "sports/index.html").write_text(page("Sports", sports_body, "sports", prefix="../"), encoding="utf-8")

    # ---------------- sport pages
    for sport in covered:
        slug = sport["slug"]
        subset = [r for r in rows if r["fixture"]["sport_slug"] == slug]
        groups = ""
        for day in sorted({r["fixture"]["date"] for r in subset}):
            day_rows = [r for r in subset if r["fixture"]["date"] == day]
            groups += f'<h3 class="day">{esc(day)}</h3>' + fixture_table(day_rows)
        ratings = ""
        if slug == "ice-hockey":
            trs = []
            for abbr, t in sorted(data["nhl_teams"]["teams"].items(),
                                  key=lambda kv: -shrunk_goal_rate(kv[1]["gf"], kv[1]["ga"], kv[1]["gp"], params["nhl_shrink_games"])):
                rating = shrunk_goal_rate(t["gf"], t["ga"], t["gp"], params["nhl_shrink_games"])
                trs.append(
                    f'<tr><td><strong>{esc(abbr)}</strong> <span class="muted">{esc(t["name"])}</span></td>'
                    f'<td class="mono">{t["gp"]}</td><td class="mono">{t["w"]}-{t["l"]}-{t["otl"]}</td>'
                    f'<td class="mono">{t["gf"] / t["gp"]:.2f}</td><td class="mono">{t["ga"] / t["gp"]:.2f}</td>'
                    f'<td class="mono">{t["pct"]:.3f}</td><td class="mono">{rating:+.3f}</td>'
                    f'<td class="mono">{esc(t["l10"])}</td><td class="mono">{esc(t["streak"])}</td></tr>'
                )
            ratings = (
                '<div class="section-head below"><div><div class="eyebrow">INPUTS</div><h2>NHL ratings</h2></div>'
                f'<span class="count">{len(trs)} clubs</span></div>'
                '<p class="table-foot">Official standings inputs and the shrunk rating used by the engine '
                f'(rating = goal difference per game × GP ÷ (GP + {params["nhl_shrink_games"]})). '
                + a("https://www.nhl.com/standings", "NHL standings") + "</p>"
                '<div class="table-scroll"><table><thead><tr><th>Club</th><th>GP</th><th>W-L-OT</th><th>GF/GP</th>'
                '<th>GA/GP</th><th>P%</th><th>Rating</th><th>L10</th><th>Streak</th></tr></thead><tbody>'
                + "".join(trs) + "</tbody></table></div>"
            )
        narratives = "".join(
            f'<article class="card"><div class="eyebrow">PREDICTION</div><h3>{esc(r["selection"])} '
            f'<span class="price mono">{price(r["odds"])}</span></h3><p>{esc(r["pick"]["narrative"])}</p>'
            f'<div class="src">' + " ".join(a(u, f"source {i + 1}") for i, u in enumerate(r["pick"]["sources"])) + "</div></article>"
            for r in subset if r["pick"]
        )
        note = (
            'Every NHL game in the window is listed, each linked to its gamecenter. Lines are fair odds with no margin.'
            if slug == "ice-hockey" else
            'Every NBA game on Oct 21 is listed. Lines are baseline: the season is one game old, so no club has a usable sample.'
        )
        body = (
            f'<section class="subhero"><div class="eyebrow">CATEGORY <span class="dash"></span> {esc(sport["sport"].upper())}</div>'
            f'<h1>{esc(sport["sport"])}<span class="accent">.</span></h1><p>{esc(note)}</p>'
            f'<div class="sport-meta">{a(sport["official_url"], "Official schedule")} {a(sport["olbg_url"], "OLBG index")}</div></section>'
            + (f'<div class="section-head"><div><div class="eyebrow">SLATE</div><h2>{len(subset)} fixtures</h2></div>'
               f'<span class="count">{len(subset)} priced</span></div>' + groups)
            + (ratings if ratings else "")
            + ('<div class="section-head below"><div><div class="eyebrow">PREDICTIONS</div><h2>Written picks</h2></div></div>'
               f'<div class="cards2">{narratives}</div>' if narratives else "")
        )
        (OUT / "sports" / f"{slug}.html").write_text(page(sport["sport"], body, "sports", prefix="../", subtitle=f"{len(subset)} fixtures"), encoding="utf-8")

    # ---------------- methodology
    p = params
    param_rows = "".join(
        f'<tr><td class="mono">{esc(k)}</td><td class="mono">{esc(v)}</td></tr>' for k, v in p.items()
    )
    method_body = f'''<section class="subhero"><div class="eyebrow">METHOD <span class="dash"></span> v{esc(meta["model_version"])}</div>
<h1>Originated, not copied<span class="accent">.</span></h1>
<p>No bookmaker price is read or reproduced. Every price on this site is derived from official league inputs with the
parameters below, so any line can be recomputed by hand.</p></section>
<div class="prose">
<h2>NHL</h2>
<ol>
<li><b>Rating.</b> For each club, goal difference per game is multiplied by GP ÷ (GP + {p["nhl_shrink_games"]}). The shrink pulls small samples toward the league mean, which is zero by construction.</li>
<li><b>Expected margin.</b> Home rating + {p["nhl_home_goals"]} goals − away rating.</li>
<li><b>Win probability.</b> P(home) = 1 ÷ (1 + e<sup>−margin ÷ {p["nhl_logistic_scale"]}</sup>), which includes overtime and shootouts.</li>
<li><b>Price.</b> No-vig fair American odds from that probability, rounded to the nearest 5. A 55% chance is about −120.</li>
<li><b>Puck line.</b> P(cover −1.5) = 1 − logistic(1.5 − margin, {p["nhl_logistic_scale"]}).</li>
<li><b>Total.</b> Each side's goals for per game is blended with the opponent's goals against per game, shrunk toward {p["nhl_league_total"]} goals over the same {p["nhl_shrink_games"]}-game weight. The line is the nearest half-goal; over/under uses a normal curve with σ = {p["nhl_total_sd"]}.</li>
</ol>
<h2>NBA</h2>
<p>The 2026-27 season is one game old at the snapshot, so every club carries a league-average rating and only home
court separates the sides ({p["nba_home_points"]} points, logistic scale {p["nba_logistic_scale"]}). That produces a
-2.5 home spread and a money line near −125. No total is originated because no verified
league scoring baseline is loaded. These are opening-style lines, not informed prices, and every NBA pick is low confidence.</p>
<h2>Confidence</h2>
<ul>
<li><b>High</b> requires at least {p["high_edge"] * 100:.0f} points of model edge, a games-played sample of at least
{p["min_games_for_high"]} per side, and an evidence pack: the fixture's own official game page must be cited in the prediction.</li>
<li><b>Medium</b> requires at least {p["medium_edge"] * 100:.0f} points of edge. A larger edge without an evidence pack is capped at medium.</li>
<li><b>Low</b> covers everything else, including every baseline NBA line.</li>
</ul>
<h2>Evidence rules</h2>
<ul>
<li>A fixture is published only with an official league URL on an approved host. OLBG is a reference, never a fixture source.</li>
<li>A high-confidence prediction is at least {p["min_prediction_words"]} words, unique, and names the team, a player, current form, recent results and the exact selection.</li>
<li>Every factual claim in a prediction has a source link on the same row, and the fact list is printed next to it.</li>
<li>Unconfirmed values stay blank. Blank is a finding, not an invitation to infer.</li>
</ul>
<h2>Known limits</h2>
<ul>{''.join(f'<li>{esc(x)}</li>' for x in meta["limits"])}</ul>
<h2>Parameters</h2>
<div class="table-scroll"><table><thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>{param_rows}</tbody></table></div>
<p class="table-foot"><a href="data/lines.json">lines.json</a> contains the full computed output for auditing.</p>
</div>'''
    (OUT / "methodology.html").write_text(page("Method", method_body, "method", subtitle=f"v{meta['model_version']}"), encoding="utf-8")

    # ---------------- sources
    kind_label = {"official": "Official", "reference": "Reference"}
    src_rows = "".join(
        f'<tr><td><strong>{esc(s["label"])}</strong><br><span class="muted">{esc(s["used_for"])}</span></td>'
        f'<td><span class="chip {"covered" if s["kind"] == "official" else "unverified"}">{esc(kind_label[s["kind"]])}</span></td>'
        f'<td class="mono src">{esc(s["checked_utc"])}</td><td class="src">{a(s["url"], host_of(s["url"]))}</td></tr>'
        for s in data["sources"]["sources"]
    )
    sources_body = (
        '<section class="subhero"><div class="eyebrow">SOURCE REGISTRY</div><h1>Every link, and what it proved<span class="accent">.</span></h1>'
        '<p>Only these URLs are accepted by the build. A prediction or flag that cites an unregistered link fails validation.</p></section>'
        '<div class="table-scroll"><table><thead><tr><th>Source</th><th>Type</th><th>Checked (UTC)</th><th>URL</th></tr></thead><tbody>'
        + src_rows + "</tbody></table></div>"
        '<p class="table-foot">Official sources are league properties on league domains. OLBG is recorded as a reference only: '
        'its tip percentages are its community data, not our picks, and its times are not treated as authoritative.</p>'
    )
    (OUT / "sources.html").write_text(page("Sources", sources_body, "sources", subtitle=f"{len(data['sources']['sources'])} links"), encoding="utf-8")

    # ---------------- flagged
    flag_rows = "".join(
        f'<tr><td><strong>{esc(f["item"])}</strong><br><span class="tag">{esc(f["category"])}</span></td>'
        f'<td>{esc(f["detail"])}</td><td class="src">' + "<br>".join(a(u, f"source {i + 1}") for i, u in enumerate(f["sources"]))
        + f'</td><td><span class="chip unverified">{esc(f["state"])}</span></td></tr>'
        for f in flags
    )
    gap_rows = "".join(
        f'<tr><td><strong>{esc(c["sport"])}</strong></td><td><span class="chip {esc(c["status"])}">{esc(c["status"])}</span></td>'
        f'<td>{esc(c["note"])}</td><td class="src">{a(c["olbg_url"], "OLBG index")}'
        f'{"<br>" + a(c["official_url"], "Official reference") if c["official_url"] else ""}</td></tr>'
        for c in coverage if c["status"] in {"unverified", "no-fixtures"}
    )
    flagged_body = (
        '<section class="subhero"><div class="eyebrow">TRANSPARENCY LOG</div><h1>Flagged for review<span class="accent">.</span></h1>'
        '<p>Open questions, conflicting sources, blanks and coverage gaps. None of these block publication; all of them are '
        'listed here with the link that raised them so they can be checked.</p></section>'
        f'<div class="section-head"><div><div class="eyebrow">OPEN ITEMS</div><h2>{len(flags)} flagged</h2></div></div>'
        '<div class="table-scroll"><table><thead><tr><th>Item</th><th>Why it is flagged</th><th>Sources</th><th>State</th></tr></thead><tbody>'
        + flag_rows + "</tbody></table></div>"
        f'<div class="section-head below"><div><div class="eyebrow">COVERAGE</div><h2>Sports without published rows</h2></div></div>'
        '<div class="table-scroll"><table><thead><tr><th>Sport</th><th>Status</th><th>Note</th><th>Reference</th></tr></thead><tbody>'
        + gap_rows + "</tbody></table></div>"
    )
    (OUT / "flagged.html").write_text(page("Flagged for review", flagged_body, "flagged", subtitle=f"{len(flags)} items"), encoding="utf-8")

    # ---------------- machine-readable output
    payload = {
        "snapshot_utc": meta["snapshot_utc"],
        "model_version": meta["model_version"],
        "params": params,
        "fixtures": [
            {
                "id": r["fixture"]["id"], "sport": r["fixture"]["sport"], "league": r["fixture"]["league"],
                "date": r["fixture"]["date"], "time": r["fixture"]["time"],
                "away": r["fixture"]["away_name"], "home": r["fixture"]["home_name"],
                "venue": r["fixture"].get("venue"),
                "official_url": r["fixture"]["official_url"], "olbg_url": r["fixture"]["olbg_url"],
                "lines": r["market"], "selection": r["selection"], "price": r["odds"],
                "model_probability": r["probability"], "edge": round(r["edge"], 4),
                "confidence": r["confidence"], "confidence_reason": r["confidence_reason"],
                "leans": r["leans"], "prediction": r["pick"]["narrative"] if r["pick"] else None,
            }
            for r in rows
        ],
        "flagged": flags,
    }
    (OUT / "data" / "lines.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    return {"rows": rows, "high": high, "medium": medium, "low": low}


if __name__ == "__main__":
    result = build()
    print(
        f"Built {len(result['rows'])} fixtures "
        f"({len(result['high'])} high, {len(result['medium'])} medium, {len(result['low'])} low)"
    )
