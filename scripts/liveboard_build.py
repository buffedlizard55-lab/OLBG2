#!/usr/bin/env python3
"""liveboard_build.py — renders the /liveboard/ dashboard from the JSON data files.

Deterministic: running it twice on the same inputs produces byte-identical HTML.
Every internal link it emits is written to a manifest that the test suite checks.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "liveboard"
OUT = ROOT / "liveboard"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]

NAV = [("index.html", "Dashboard"), ("picks.html", "Top picks"), ("matches.html", "All matches"),
       ("lines.html", "Originated lines"), ("predictions.html", "Predictions"),
       ("coverage.html", "Coverage"), ("flagged.html", "Flagged for review"),
       ("sources.html", "Sources"), ("methodology.html", "Method")]


def e(x) -> str:
    return html.escape(str(x), quote=True)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def page(title: str, body: str, active: str, depth: int = 0) -> str:
    prefix = "../" * depth
    links = "".join(
        f'<a class="{"on" if f == active else ""}" href="{prefix}{f}">{e(t)}</a>' for f, t in NAV
    )
    sport_links = "".join(
        f'<a href="{prefix}sports/{slug(s)}.html">{e(s)}</a>' for s in SPORTS
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · OLBG live board</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="brand"><a href="{prefix}index.html">OLBG <span>live board</span></a>
      <p class="stamp">Captured 23 Oct 2026 · 15 sports · every row carries its source</p></div>
    <nav class="main">{links}</nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
  <p>Research aid, not betting advice. Prices here are originated by this project, not quotes from a bookmaker.
  OLBG supplies the fixture list and its published tip shares; governing bodies supply every other number.
  Where an official number was not obtained, the value is blank and the row appears on
  <a href="{prefix}flagged.html">Flagged for review</a>.</p>
  <details><summary>Sports</summary><div class="sports">{sport_links}</div></details>
  <p class="small muted" style="margin-top:1.2rem">Part of the wider research desk:
  <a href="{prefix}../index.html">root dashboard</a> ·
  <a href="{prefix}../integration.html">cross-layer review</a> ·
  <a href="{prefix}../archive.html">earlier layers</a>.</p>
</footer>
</body>
</html>
"""


def table(headers, rows, cls="") -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def conf_badge(c: str) -> str:
    return f'<span class="badge b-{c}">{e(c)}</span>'


def main() -> None:
    olbg = json.loads((DATA / "olbg.json").read_text())
    lines = json.loads((DATA / "lines.json").read_text())
    preds = json.loads((DATA / "predictions.json").read_text())
    flags = json.loads((DATA / "flagged.json").read_text())
    sources = json.loads((DATA / "sources.json").read_text())

    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "sports").mkdir(exist_ok=True)

    rows = lines["rows"]
    events = [(h["sport"], ev) for h in olbg["hubs"] for ev in h.get("events", [])]
    high = [r for r in rows if r["high_and_in_band"] and r["is_match"]]
    high_out = [r for r in rows if r["high_and_in_band"] and not r["is_match"]]
    written = preds["predictions"]

    # ---------------------------------------------------------------- per-sport top five
    by_sport = {}
    for r in rows:
        by_sport.setdefault(r["sport"], []).append(r)
    top5 = {s: sorted(v, key=lambda x: (-x["probability"], x["event"]))[:5] for s, v in by_sport.items()}

    # ---------------------------------------------------------------------- dashboard
    kpi = [
        ("Sports captured", len([h for h in olbg["hubs"] if h.get("events")]), f"of {len(SPORTS)} in scope"),
        ("Fixture rows from OLBG", len(events), "first-page capture"),
        ("Markets priced", len(rows), "winner, handicap and total"),
        ("High confidence, in band", len(high), "p ≥ 70% and −250 or longer"),
        ("Fair lines published", len(lines["originated_lines"]), "our own number, no price"),
        ("Written predictions", len(written), "each ≥ 30 words"),
        ("Flagged for review", len(flags["flags"]), "named, sourced reasons"),
    ]
    kpi_html = "".join(f'<div class="kpi"><b>{v}</b><span>{e(a)}</span><em>{e(b)}</em></div>' for a, v, b in kpi)

    exec_rows = []
    for r in sorted(high, key=lambda x: (-x["probability"], x["sport"])):
        exec_rows.append([
            e(r["sport"]),
            f'<a href="{e(r["olbg_url"])}" target="_blank" rel="noopener">{e(r["event"])}</a>',
            e(r["selection"]),
            f'{r["probability"]*100:.1f}%',
            e(r["offered_american"]),
            conf_badge(r["confidence"]),
            e("official inputs" if r["source_class"] == "official-model" else "OLBG tip share"),
        ])
    exec_html = table(["Sport", "Fixture", "Selection", "Chance", "Our price", "Confidence", "Basis"], exec_rows) \
        if exec_rows else "<p class='muted'>No selection cleared both gates today.</p>"

    cov_rows = []
    for s in SPORTS:
        c = lines["coverage"].get(s, {})
        cov_rows.append([
            f'<a href="sports/{slug(s)}.html">{e(s)}</a>',
            c.get("events_captured", 0), c.get("markets_priced", 0),
            c.get("rows_official_model", 0), c.get("high_confidence_in_band", 0),
            f'<a href="flagged.html#{slug(s)}">see flags</a>',
        ])
    cov_html = table(["Sport", "Fixtures captured", "Markets priced", "From official inputs", "High &amp; in band", "Review"], cov_rows)

    body = f"""
<section class="hero">
  <h1>The board, as it actually stands</h1>
  <p class="lede">Every upcoming fixture this session could read off OLBG's fifteen sport hubs on 23 October 2026,
  each one priced from a number that can be traced to an official source or to OLBG's own published tip share —
  and nothing at all where neither exists.</p>
  <div class="kpis">{kpi_html}</div>
</section>

<section>
  <h2>Executive summary — today's highest confidence selections</h2>
  <p class="muted">A row qualifies only if our chance of the selection winning is at or above 70%
  <em>and</em> our offered price is −250 or longer. Because a fair 70% shot is already around −233,
  that pair of conditions describes a narrow window, which is why the list is short and specific.</p>
  {exec_html}
  <p class="muted">{len(high_out)} further outright selections cleared the same two gates but are not single matches;
  they are shown on <a href="picks.html">Top picks</a> under their own heading.</p>
</section>

<section>
  <h2>Coverage by sport</h2>
  <p class="muted">Fifteen sports were in scope. Golf published no events at all at capture time; Rugby League published
  outright markets only. The other thirteen have fixture rows. Only some of those rows could be priced from an official
  number — the rest carry an explicitly labelled tip-share price rather than a silent guess.</p>
  {cov_html}
</section>

<section class="two">
  <div>
    <h2>What is solid</h2>
    <ul class="ticks">
      <li>Every fixture row links the OLBG page it was read from.</li>
      <li>Every official number links the governing body endpoint that returned it.</li>
      <li>Every price is reproducible: <code>scripts/liveboard_model.py</code> rebuilds the file byte for byte.</li>
      <li>Every prediction states a selection in plain words, with its facts linked underneath.</li>
    </ul>
  </div>
  <div>
    <h2>What is not</h2>
    <ul class="crosses">
      <li>Five written predictions per sport was not reached. Seven were written, in three sports.</li>
      <li>No official injury list was obtained, so no prediction claims one.</li>
      <li>OLBG shows no odds to a logged-out visitor, so its tip share is the only market signal available.</li>
      <li>OLBG's “Load More” pagination was not followed; these lists are first-page slices.</li>
    </ul>
  </div>
</section>
"""
    (OUT / "index.html").write_text(page("Dashboard", body, "index.html"))

    # -------------------------------------------------------------------------- picks
    blocks = []
    for s in SPORTS:
        rs = top5.get(s)
        if not rs:
            blocks.append(f"<h3>{e(s)}</h3><p class='muted'>No fixture row captured for this sport.</p>")
            continue
        trs = []
        for r in rs:
            trs.append([
                f'<a href="{e(r["olbg_url"])}" target="_blank" rel="noopener">{e(r["event"])}</a>',
                e(r["time_displayed"]),
                e(r["market"]),
                e(r["selection"]),
                f'{r["probability"]*100:.1f}%',
                e(r["offered_american"]),
                "yes" if r["in_band"] else "no",
                conf_badge(r["confidence"]),
            ])
        blocks.append(f"<h3>{e(s)}</h3>" + table(["Fixture", "OLBG time", "Market", "Selection", "Chance", "Our price", "In band", "Confidence"], trs))

    out_rows = []
    for r in sorted(high_out, key=lambda x: -x["probability"]):
        out_rows.append([e(r["sport"]), e(r["event"]), e(r["selection"]), f'{r["probability"]*100:.1f}%',
                         e(r["offered_american"]), conf_badge(r["confidence"])])

    body = f"""
<section>
  <h1>Top picks, sport by sport</h1>
  <p class="lede">The five highest-probability selections we could originate for each sport, whatever their confidence label.
  A sport with fewer than five rows shows what exists rather than padding the table.</p>
</section>
<section>
  <h2>Cleared both gates — single matches</h2>
  {table(["Sport","Fixture","Selection","Chance","Our price","Confidence"],
         [[e(r['sport']), f'<a href="{e(r["olbg_url"])}" target="_blank" rel="noopener">{e(r["event"])}</a>',
           e(r['selection']), f'{r["probability"]*100:.1f}%', e(r['offered_american']), conf_badge(r['confidence'])]
          for r in high]) if high else "<p class='muted'>None.</p>"}
</section>
<section>
  <h2>Cleared both gates — outrights</h2>
  {table(["Sport","Market","Selection","Chance","Our price","Confidence"],
         out_rows) if out_rows else "<p class='muted'>None.</p>"}
</section>
<section>
  <h2>Five per sport</h2>
  <p class="muted">Ranked by our probability. “In band” means our price sits between −250 and +10000;
  a very strong favourite can be high confidence and still fall outside the band, which is exactly what the brief's
  window is designed to exclude.</p>
  {''.join(blocks)}
</section>
"""
    (OUT / "picks.html").write_text(page("Top picks", body, "picks.html"))

    # ------------------------------------------------------------------------ matches
    m_rows = []
    for s, ev in events:
        m_rows.append([
            f'<a href="sports/{slug(s)}.html">{e(s)}</a>',
            e(ev.get("c", "")),
            f'<a href="{e(ev["u"])}" target="_blank" rel="noopener">{e(ev["n"])}</a>',
            e(ev["t"]),
            e(ev.get("m", "")),
            e(ev.get("s", "")),
            f'{ev.get("w","")}/{ev.get("tw","")}',
            f'{ev.get("p","")}%',
            e(ev["id"]),
        ])
    body = f"""
<section>
  <h1>Every fixture captured from OLBG</h1>
  <p class="lede">{len(events)} rows, read from the fifteen sport hubs on 23 October 2026. The time column is OLBG's own
  string copied verbatim: it is not UTC, and for North American competitions OLBG prints US Eastern while European
  competitions are printed in UK local time. No conversion has been applied.</p>
  <p class="muted">The tip counter is OLBG's “tips for this selection / all tips on that market”. It is the site's own
  sentiment measure, not a price.</p>
</section>
<section>
  {table(["Sport","Competition","Fixture","OLBG time","Market OLBG shows","Most-tipped selection","Tips","Share","Event id"], m_rows)}
</section>
"""
    (OUT / "matches.html").write_text(page("All matches", body, "matches.html"))

    # -------------------------------------------------------------------------- lines
    l_rows = []
    for r in sorted(rows, key=lambda x: (SPORTS.index(x["sport"]), -x["probability"])):
        l_rows.append([
            e(r["sport"]),
            f'<a href="{e(r["olbg_url"])}" target="_blank" rel="noopener">{e(r["event"])}</a>',
            e(r["market"]),
            e(r["selection"]),
            f'{r["probability"]*100:.2f}%',
            e(r["fair_american"]),
            e(r["offered_american"]),
            "yes" if r["in_band"] else "no",
            conf_badge(r["confidence"]),
            f'<a href="{e(r["source_url"])}" target="_blank" rel="noopener">source</a>',
            e(r["basis"]),
        ])
    fl_rows = [[e(x["sport"]),
                f'<a href="{e(x["olbg_url"])}" target="_blank" rel="noopener">{e(x["event"])}</a>',
                e(x["market"]), e(x["line"]), e(x["basis"]),
                f'<a href="{e(x["source_url"])}" target="_blank" rel="noopener">source</a>']
               for x in lines["originated_lines"]]
    body = f"""
<section>
  <h1>Originated lines</h1>
  <p class="lede">Two provenance classes, never mixed silently. <b>Official inputs</b> means the probability was
  estimated from a number returned by a governing body. <b>OLBG tip share</b> means it was estimated from the tip split
  OLBG publishes, smoothed with a Laplace prior so a single tip can never read as certainty.</p>
  <p class="muted">Fair price is 1 ÷ probability. Our offered price applies the sport's margin, documented on the
  <a href="methodology.html">method</a> page. A price is “in band” when it sits between −250 and +10000.</p>
</section>
<section>
  <h2>Fair handicap and total lines</h2>
  <p class="muted">Where the inputs allowed it, we published our own line rather than a price on a line someone else set.</p>
  {table(["Sport","Fixture","Market","Our line","Basis","Source"], fl_rows) if fl_rows else "<p class='muted'>None.</p>"}
</section>
<section>
  <h2>All {len(rows)} priced selections</h2>
  {table(["Sport","Fixture","Market","Selection","Chance","Fair price","Our price","In band","Confidence","Source","Basis"], l_rows)}
</section>
"""
    (OUT / "lines.html").write_text(page("Originated lines", body, "lines.html"))

    # -------------------------------------------------------------------- predictions
    p_blocks = []
    for p_ in written:
        facts = "".join(f'<li>{e(f["claim"])} — <a href="{e(f["source_url"])}" target="_blank" rel="noopener">source</a></li>'
                        for f in p_.get("facts", []))
        p_blocks.append(f"""
<article class="pred">
  <h2>{e(p_['selection'])} <span class="small">{e(p_['sport'])} · {e(p_['event'])}</span></h2>
  <p class="meta">{conf_badge(p_['confidence'])} <span class="muted">{e(p_['market'])} · {e(p_['band'])} ·
  {len(p_['text'].split())} words</span></p>
  <p class="copy">{e(p_['text'])}</p>
  <h3>Facts behind it</h3>
  <ul class="facts">{facts}</ul>
  <p class="muted small">Injury and availability: no official list was obtained for this fixture, so none is asserted.</p>
</article>""")
    body = f"""
<section>
  <h1>Written predictions</h1>
  <p class="lede">{len(written)} selections, each written around that fixture's own numbers, each at least thirty words,
  each stating the side plainly. Every claim underneath is a link to the official page it came from.</p>
  <p class="muted">The brief asked for five per sport. That target was not reached today; the shortfall and the reason for
  each sport are on <a href="flagged.html">Flagged for review</a>.</p>
</section>
<section>
  <h2>Selections that cleared both gates but carry no write-up</h2>
  <p class="muted">A prediction is only written when the fixture has official facts behind it. These selections qualified
  on the numbers but had no official current-form input, so nothing was invented to fill the gap.</p>
  {table(["Sport","Fixture","Selection","Our price","Why no prediction"],
         [[e(r['sport']), f'<a href="{e(r["olbg_url"])}" target="_blank" rel="noopener">{e(r["event"])}</a>',
           e(r['selection']), e(r['offered_american']),
           e("No official form input was obtained for this competition; the price rests on OLBG's tip split alone.")]
          for r in high if not any(p_['event_id'] == r['event_id'] and p_['selection'].startswith(r['selection'].split()[0]) for p_ in written)])
   if any(not any(p_['event_id'] == r['event_id'] and p_['selection'].startswith(r['selection'].split()[0]) for p_ in written) for r in high)
   else "<p class='muted'>Every qualifying selection has a write-up.</p>"}
</section>
{''.join(p_blocks)}
"""
    (OUT / "predictions.html").write_text(page("Predictions", body, "predictions.html"))

    # ----------------------------------------------------------------------- coverage
    rows_cov = []
    for s in SPORTS:
        c = lines["coverage"].get(s, {})
        pf = [x for x in flags["flags"] if x.get("sport") == s]
        rows_cov.append([
            f'<a href="sports/{slug(s)}.html">{e(s)}</a>',
            c.get("events_captured", 0), c.get("markets_priced", 0),
            c.get("rows_official_model", 0), c.get("rows_community_implied", 0),
            c.get("high_confidence_in_band", 0),
            len([p for p in written if p["sport"] == s]),
            len(pf),
        ])
    body = f"""
<section>
  <h1>Coverage</h1>
  <p class="lede">The honest scoreboard. Every sport in scope, what was captured, what was priced, and how many
  predictions made it through.</p>
</section>
<section>
  {table(["Sport","Fixtures","Priced markets","Official inputs","Tip-share rows","High &amp; in band","Predictions","Flags"], rows_cov)}
</section>
<section>
  <h2>Why the predictions column is thin</h2>
  <ul>
    <li><b>No official strength or form input reached.</b> Darts (PDC order of merit behind a consent wall),
    Tennis (ATP ranking table did not render in the chunks read), Handball (domestic tables not read; EHF's own
    calendar does not list OLBG's fixtures), Volleyball (the Polish site redirected to the women's competition),
    Greyhounds (no official form feed), Gaelic Sports (club fixtures absent from the GAA's national fixture page).</li>
    <li><b>Official input existed but was too thin to write to the brief's standard.</b> Ice Hockey and Basketball:
    the NHL feed gave prices, not club records, and the NBA static endpoint failed; without a record or a recent
    result there is no form sentence that would be honest.</li>
    <li><b>No fixture at all.</b> Golf published nothing; Rugby League published outrights only.</li>
  </ul>
</section>
"""
    (OUT / "coverage.html").write_text(page("Coverage", body, "coverage.html"))

    # ------------------------------------------------------------------------ flagged
    f_blocks = []
    for f in flags["flags"]:
        links = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">source {i+1}</a>'
                         for i, u in enumerate(f.get("sources", [])))
        f_blocks.append(f"""
<article class="flag" id="{e(f['id'].lower())}">
  <h2>{e(f['id'])} — {e(f['title'])}</h2>
  <p class="meta"><span class="badge b-high">{e(f['severity'])}</span> <span class="muted">{e(f.get('sport','Cross-sport'))}</span></p>
  <p>{e(f['detail'])}</p>
  <p class="small">What we did instead: {e(f['action'])}</p>
  <p class="small">{links}</p>
</article>""")
    body = f"""
<section>
  <h1>Flagged for review</h1>
  <p class="lede">Nothing here is hidden elsewhere on the site. Each item names what could not be established,
  what was published instead, and the page we tried.</p>
</section>
{''.join(f_blocks)}
"""
    (OUT / "flagged.html").write_text(page("Flagged for review", body, "flagged.html"))

    # ------------------------------------------------------------------------ sources
    s_rows = [[f'<a href="{e(b["source_url"])}" target="_blank" rel="noopener">{e(b["source_name"])}</a>',
               e(b["sport"]), e(b["subject"]),
               e(", ".join(sorted(b.get("fields", {}).keys())) if b.get("fields") else
                 ("standings" if b.get("teams") else "fixtures and results" if b.get("fixtures") else
                  "standings" if b.get("drivers") else "rankings" if b.get("world") else "see block"))]
              for b in json.loads((DATA / "inputs.json").read_text())["blocks"]]
    blocked = [[e(x["name"]), e(x["url"]), e(x["result"])] for x in sources["blocked"]]
    body = f"""
<section>
  <h1>Sources</h1>
  <p class="lede">The OLBG pages are the object of the reverse-engineering. The governing-body pages are where the
  numbers came from. Both registers are complete: if a number is on this site, its page is below.</p>
</section>
<section>
  <h2>Official inputs read first-hand</h2>
  {table(["Body / endpoint","Sport","What was read","Fields"], s_rows)}
</section>
<section>
  <h2>OLBG pages read first-hand</h2>
  {table(["Hub","Sport id","Events captured on first page"],
         [[f'<a href="{e(h["hub_url"])}" target="_blank" rel="noopener">{e(h["hub_url"])}</a>',
           str(h["id"]), str(len(h.get("events", []))) + ("" if h.get("events") else " — " + h.get("hub_status","no events"))]
          for h in olbg["hubs"]])}
</section>
<section>
  <h2>Attempted and blocked</h2>
  <p class="muted">These were tried in this session and returned nothing usable. A blocked page is recorded, never worked around.</p>
  {table(["Source","URL","Result"], blocked)}
</section>
"""
    (OUT / "sources.html").write_text(page("Sources", body, "sources.html"))

    # ------------------------------------------------------------------------ method
    body = f"""
<section>
  <h1>Method</h1>
  <p class="lede">Short enough to check line by line. The script that produces every number is
  <code>scripts/liveboard_model.py</code>; the script that produces this site is <code>scripts/liveboard_build.py</code>.
  Both read only the two JSON files in <code>data/liveboard/</code>.</p>
</section>
<section>
  <h2>1. Fixtures come from OLBG</h2>
  <p>Each sport hub is <code>/betting-tips/{{Sport}}/{{id}}</code>. The hub lists the event, the market OLBG is showing
  for it, the most-tipped selection and the tip split. Those five fields are copied verbatim, including OLBG's own
  time string. No timezone conversion is applied because OLBG's display is not a UTC source.</p>
  <h2>2. Probability comes from one of two places</h2>
  <p><b>Official inputs.</b> Baseball uses Bill James' log5 on the two clubs' regular-season winning percentages with a
  home term; run lines and totals come from a normal approximation on season runs scored and allowed. The two NHL games
  use the mean implied probability of the moneylines the NHL's own feed publishes, because that endpoint carries prices
  but not club records. EuroLeague uses point differential per game. Snooker uses the log of World Snooker Tour ranking
  money. Formula 1 uses championship points share, discounted for single-race variance.</p>
  <p><b>OLBG tip share.</b> Everywhere else the probability is the Laplace-smoothed tip split,
  <code>(tips + 1) / (total + 2)</code>. The smoothing is what stops a 1-of-1 tip becoming a 100% chance. These rows are
  labelled on every table; they are our own transformation of OLBG's sentiment, not a bookmaker price.</p>
  <h2>3. Prices</h2>
  <p>Fair decimal is 1 ÷ probability. Our offered price divides that by (1 − margin), with the margin listed per sport
  in the script. American odds are derived from the decimal in the usual way.</p>
  <h2>4. Labels</h2>
  <ul>
    <li><b>high</b> — probability at or above 70%, and at least six tips behind it when the price is tip-share based.</li>
    <li><b>medium</b> — probability at or above 60%.</li>
    <li><b>low</b> — everything else.</li>
    <li><b>in band</b> — our offered American price sits between −250 and +10000, as the brief specifies.</li>
  </ul>
  <h2>5. What the band really does</h2>
  <p>A fair 70% shot is about −233, and a fair 75% shot is about −300 once a five per cent margin is applied. So
  “70% or better” and “−250 or longer” overlap in a window of roughly 70–75%. That is not a bug: it is the consequence of
  asking for both a high strike rate and a price that is not prohibitively short. Strong favourites such as Gloucester at
  89% are correctly excluded from the band while still appearing in the per-sport top five.</p>
  <h2>6. Rules that were not bent</h2>
  <p>No value is inferred, filled forward or copied from a secondary site. A fixture without an official input and
  without a tip sample is left unlined. A claim without an official page is not written into a prediction.</p>
</section>
"""
    (OUT / "methodology.html").write_text(page("Method", body, "methodology.html"))

    # ------------------------------------------------------------------- sport pages
    for s in SPORTS:
        hub = next((h for h in olbg["hubs"] if h["sport"] == s), None)
        srows = []
        for ev in (hub or {}).get("events", []):
            pr = [r for r in rows if r["event_id"] == ev["id"]]
            price = "<br>".join(f'{e(r["selection"])} · {r["probability"]*100:.1f}% · {e(r["offered_american"])} · {e(r["confidence"])}'
                                for r in pr) or "<span class='muted'>not priced</span>"
            srows.append([f'<a href="{e(ev["u"])}" target="_blank" rel="noopener">{e(ev["n"])}</a>',
                          e(ev["t"]), e(ev.get("m", "")), f'{ev.get("w","")}/{ev.get("tw","")}', price])
        preds_here = [p_ for p_ in written if p_["sport"] == s]
        pred_html = "".join(f'<article class="pred"><h3>{e(p_["selection"])}</h3><p class="meta">{conf_badge(p_["confidence"])} <span class="muted">{e(p_["event"])}</span></p><p class="copy">{e(p_["text"])}</p></article>'
                            for p_ in preds_here) or "<p class='muted'>No prediction was written for this sport today; the reason is on <a href='../flagged.html'>Flagged for review</a>.</p>"
        sport_flags = [f for f in flags["flags"] if f.get("sport") == s]
        flag_html = "".join(f'<li><b>{e(f["id"])}</b> {e(f["title"])}</li>' for f in sport_flags) or "<li class='muted'>None.</li>"
        body = f"""
<section>
  <h1>{e(s)}</h1>
  <p class="lede">{len((hub or {}).get('events', []))} fixture rows captured from
  <a href="{e((hub or {}).get('hub_url','#'))}" target="_blank" rel="noopener">the OLBG hub</a> on 23 October 2026.</p>
</section>
<section>
  <h2>Fixtures and our prices</h2>
  {table(["Fixture","OLBG time","Market OLBG shows","Tips","Our price"], srows) if srows else "<p class='muted'>OLBG published no events for this sport at capture time.</p>"}
</section>
<section>
  <h2>Predictions</h2>
  {pred_html}
</section>
<section>
  <h2>Flags for this sport</h2>
  <ul>{flag_html}</ul>
</section>
"""
        (OUT / "sports" / f"{slug(s)}.html").write_text(page(s, body, "", depth=1))

    # ------------------------------------------------------------------------- css
    (OUT / "assets" / "style.css").write_text(CSS)

    # --------------------------------------------------------------------- manifest
    manifest = {}
    for p_ in OUT.rglob("*.html"):
        txt = p_.read_text()
        hrefs = re.findall(r'href="([^"#][^"]*)"', txt)
        for h in hrefs:
            if h.startswith(("http://", "https://", "mailto:")):
                continue
            target = (p_.parent / h.split("#")[0]).resolve()
            manifest.setdefault(str(p_.relative_to(ROOT)), []).append(str(target.relative_to(ROOT)))
    (DATA / "link-manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(f"built {len(list(OUT.rglob('*.html')))} pages")


CSS = """/* OLBG live board — small, dependency-free stylesheet */
:root{
  --bg:#f6f7f9; --card:#fff; --ink:#12161c; --muted:#5d6773; --line:#e2e6ec;
  --accent:#0d5c63; --accent-soft:#e3f1f2; --high:#0f7b46; --med:#8a5a00; --low:#6b7280;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
header.top{background:#0b2b30;color:#eaf3f4;border-bottom:3px solid var(--accent)}
header.top .wrap{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;padding:14px 18px}
.brand a{color:#fff;text-decoration:none;font-weight:700;font-size:18px;letter-spacing:.2px}
.brand a span{font-weight:400;color:#9fc6cb}
.stamp{margin:2px 0 0;font-size:12px;color:#9fc6cb}
nav.main{display:flex;flex-wrap:wrap;gap:4px}
nav.main a{color:#d7e6e8;text-decoration:none;padding:6px 10px;border-radius:6px;font-size:13.5px}
nav.main a:hover{background:#14444b}
nav.main a.on{background:var(--accent-soft);color:#0b2b30;font-weight:600}
main{background:var(--bg);padding-bottom:40px}
h1{font-size:26px;margin:26px 0 6px;letter-spacing:-.2px}
h2{font-size:18px;margin:26px 0 8px}
h3{font-size:15.5px;margin:18px 0 6px}
.lede{color:var(--muted);max-width:80ch;margin:0 0 14px}
.muted{color:var(--muted)}
.small{font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:24px;line-height:1.1}
.kpi span{display:block;font-size:12.5px;color:var(--muted);margin-top:2px}
.kpi em{display:block;font-size:11.5px;color:#8b95a1;font-style:normal;margin-top:6px}
.scroll{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0 18px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f0f3f6;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:#54606d;white-space:nowrap}
tbody tr:hover{background:#fafcfd}
table a{color:var(--accent);text-decoration:none}
table a:hover{text-decoration:underline}
.badge{display:inline-block;font-size:11px;padding:2px 7px;border-radius:999px;font-weight:600;color:#fff}
.b-high{background:var(--high)} .b-medium{background:var(--med)} .b-low{background:var(--low)}
.pred,.flag{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.pred h2{margin-top:0}
.pred .small{font-weight:400;color:var(--muted);font-size:13px}
.pred .copy{font-size:14.5px;max-width:88ch}
.facts{font-size:13px;color:#3c4652}
.copy{white-space:normal}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.two ul{margin:6px 0;padding-left:18px}
.ticks li{margin:4px 0}
.crosses li{margin:4px 0}
footer{color:var(--muted);font-size:12.5px;margin-top:30px;padding:18px;border-top:1px solid var(--line)}
footer .sports{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
footer .sports a{color:var(--accent);text-decoration:none}
code{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:12.5px}
@media (max-width:760px){.two{grid-template-columns:1fr}h1{font-size:22px}}
"""

if __name__ == "__main__":
    main()
