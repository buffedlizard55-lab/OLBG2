#!/usr/bin/env python3
"""Read-only, deterministic cross-layer provenance audit.

This script does NOT fetch sources or mark rows verified. The dated primary-source
observations are documented in research/independent-audit-65ff36f0.md. It inspects
only committed snapshots; it never mutates the upstream sports/data layers.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ("verified", "hub", "slate", "board", "forward")
RIOT = "https://lolesports.com/en-US/"
PDC_SCHEDULE = "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/"
PDC_PREVIEW = "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview"
PGA_UTAH = "https://www.pgatour.com/tournaments/2026/bank-of-utah-championship/R2026554/overview"
PGA_BERMUDA = "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview"
# A host classification is not evidence that the URL supports the claims in a row.
OFFICIAL_HOSTS = frozenset({
    "www.pdc.tv", "stats.unitedrugby.com", "www.nba.com", "www.nhl.com",
    "www.euroleaguebasketball.net", "api-live.euroleague.net",
    "prod2.lnr.fr", "top14.lnr.fr", "www.wst.tv", "ehfcl.eurohandball.com",
    "www.gaa.ie", "www.mlb.com", "statsapi.mlb.com", "www.formula1.com",
    "www.plusliga.pl", "www.nrl.com", "www.icc-cricket.com", "www.pgatour.com",
    "www.europeantour.com", "www.superleague.co.uk", "stats.swehockey.se",
    "www.atptour.com", "www.legavolley.it", "www.gbgb.org.uk", "www.wtatennis.com",
    "www.afl.com.au", "lolesports.com", "www.lolesports.com",
})


def read(layer: str, kind: str) -> list[dict]:
    data = json.loads((ROOT / "data" / layer / f"{kind}.json").read_text())
    return data.get("matches", data.get("rows", [])) if kind == "matches" else data["predictions"]


def audit() -> dict:
    rows = {layer: read(layer, "matches") for layer in LAYERS}
    picks = {layer: read(layer, "predictions") for layer in LAYERS}
    findings: list[dict] = []
    for layer, items in rows.items():
        for row in items:
            url = row.get("official_url", "")
            host = urlsplit(url).hostname
            if urlsplit(url).scheme != "https" or host not in OFFICIAL_HOSTS:
                if row["sport"] == "esports" and layer == "slate" and host == "liquipedia.net":
                    finding = {
                        "id": "A65-ES-" + row["id"].rsplit("-", 1)[-1], "sport": "eSports",
                        "layer": layer, "row_id": row["id"],
                        "published": row["home"] + " vs " + row["away"],
                        "status": "Fixture pairing on official schedule; published citation unverified",
                        "issue": "The published 'official_url' and player-input links point to Liquipedia, a community wiki, not Riot Games. The Riot schedule displays this pairing (some team names/order differ); model form inputs and price have NOT been reverified.",
                        "official_value": row["home"] + " vs " + row["away"] if row["id"] not in {"lol-w26-r1-6", "lol-w26-r1-7", "lol-w26-r1-8"} else "",
                        "official_url": RIOT, "published_url": url,
                        "action": "Replace fixture citation with Riot match/schedule URL; separately verify all model inputs before calling the line verified.",
                    }
                else:
                    finding = {
                        "id": f"A65-SRC-{layer}-{row['id']}", "sport": row.get("sport_name", row["sport"]),
                        "layer": layer, "row_id": row["id"], "published": row.get("home", "") + " vs " + row.get("away", ""),
                        "status": "Source unverified", "issue": "Missing HTTPS link to a classified official publisher.",
                        "official_value": "", "official_url": "", "published_url": url,
                        "action": "Do not publish as verified until a primary source is obtained.",
                    }
                findings.append(finding)

    # Two dated claims are independently compared with the linked governing bodies.
    for layer in LAYERS:
        for row in rows[layer]:
            if row["id"] == "golf-utah-2026" and row.get("date") == "2026-10-22":
                findings.append({
                    "id": f"A65-GOLF-{layer}", "sport": "Golf", "layer": layer, "row_id": row["id"],
                    "published": "Bank of Utah Championship — 22 Oct 2026",
                    "status": "Contradicted by PGA Tour calendar", "issue": "Official PGA Tour event page dates the Bank of Utah Championship 1–4 Oct 2026, not 22 Oct. The 22–25 Oct tournament is the Butterfield Bermuda Championship; the Utah entry is a stale event, not a live fixture.",
                    "official_value": "Bank of Utah Championship: 1–4 Oct 2026; Butterfield Bermuda Championship: 22–25 Oct 2026",
                    "official_url": PGA_UTAH, "secondary_official_url": PGA_BERMUDA,
                    "published_url": row["official_url"], "action": "Suppress the stale row in originating layer; do not infer a field or market for the replacement.",
                })
            if row["id"] == "pdc-32330":
                findings.append({
                    "id": f"A65-DARTS-{layer}", "sport": "Darts", "layer": layer, "row_id": row["id"],
                    "published": row["home"] + " vs " + row["away"],
                    "status": "Conflicting publisher snapshots; replacement unverified" if row["away"] == "Ritchie Edhouse" else "PDC schedule supports pairing as of 21 Oct",
                    "issue": "The official PDC 19 Oct schedule and 21 Oct preview list Danny Noppert v Stephen Bunting. The slate asserts Bunting withdrew and Ritchie Edhouse replaced him, citing that 21 Oct preview, which does not support this replacement. A later PDC change is possible but has not been evidenced here.",
                    "official_value": "Danny Noppert vs Stephen Bunting (19–21 Oct PDC publications)" if row["away"] != "Ritchie Edhouse" else "",
                    "official_url": PDC_SCHEDULE, "secondary_official_url": PDC_PREVIEW,
                    "published_url": row["official_url"], "action": "Do not use slate's Edhouse selection, line or prediction until a newer PDC match source confirms replacement; revisit before play.",
                })

    bad_picks = []
    for layer, items in picks.items():
        for pick in items:
            text = pick.get("text", pick.get("analysis", ""))
            if len(text.split()) < 30:
                bad_picks.append({"layer": layer, "match_id": pick.get("match_id"), "issue": "under 30 words"})
            url = pick.get("official_url", "")
            if urlsplit(url).hostname not in OFFICIAL_HOSTS:
                bad_picks.append({"layer": layer, "match_id": pick.get("match_id"), "issue": "non-primary main citation"})
    # A conflict is a reported finding, not a license to silently rewrite other layers.
    by_id = {}
    for layer, items in rows.items():
        for row in items:
            by_id.setdefault(row["id"], {})[layer] = row
    participant_conflicts = [
        {"row_id": key, "layers": {name: r.get("away", "") for name, r in group.items()}}
        for key, group in by_id.items()
        if len({r.get("away") for r in group.values()}) > 1
    ]
    return {
        "as_of": "2026-10-22 UTC", "method": "Static repository scan + separately documented dated primary-source spot checks; not a live or exhaustive verification of every claim.",
        "layers": {layer: {"rows": len(rows[layer]), "predictions": len(picks[layer])} for layer in LAYERS},
        "scanned_rows": sum(map(len, rows.values())), "scanned_predictions": sum(map(len, picks.values())),
        "findings": sorted(findings, key=lambda f: (f["sport"], f["id"])),
        "prediction_issues": bad_picks, "participant_conflicts": participant_conflicts,
    }


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def link(url: str, label: str) -> str:
    if not url or urlsplit(url).scheme != "https":
        return '<span class="blank">— unverified</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>'


def shell(title: str, body: str, current: str) -> str:
    nav = ' '.join(f'<a href="{page}" {"aria-current=page" if page == current else ""}>{name}</a>' for page, name in (("index.html", "Overview"), ("flagged.html", "Flagged for Review"), ("../index.html", "Main dashboard")))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · OLBG2</title><link rel="stylesheet" href="assets/style.css"></head><body><a class="skip" href="#main">Skip to content</a><header><div class="wrap"><p class="eyebrow">OLBG2 / independent evidence check</p><nav aria-label="Audit navigation">{nav}</nav></div></header><main class="wrap" id="main">{body}</main><footer class="wrap">Static snapshot · 22 Oct 2026 UTC · <a href="../COORDINATION.md">Coordination &amp; scope</a> · No bookmaker odds.</footer></body></html>'''


def build(report: dict) -> None:
    output = ROOT / "audit65"
    output.mkdir(exist_ok=True)
    (ROOT / "data" / "audit65").mkdir(exist_ok=True)
    (ROOT / "data" / "audit65" / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    cases = report["findings"]
    cards = ''.join(f'<article class="card"><b>{esc(label)}</b><strong>{esc(value)}</strong></article>' for label, value in (("Published rows scanned", report["scanned_rows"]), ("Prediction records scanned", report["scanned_predictions"]), ("Evidence discrepancies", len(cases)), ("Official-source spot checks", "PDC · PGA Tour · Riot")))
    layer_rows = ''.join(f'<li><strong>{esc(layer)}</strong>: {n["rows"]} stored fixture rows / {n["predictions"]} featured predictions · <a href="../{esc(layer)}/index.html">Browse published layer</a></li>' for layer, n in report["layers"].items())
    overview = f'''<section class="hero"><p class="eyebrow">22 October 2026 · evidence first</p><h1>Publication integrity review</h1><p>Independent read-only audit of five published layers. The main dashboard and sport pages already exist; this page calls out conflicting or weakly sourced entries instead of adding another set of picks.</p><a class="button" href="flagged.html">Review {len(cases)} flagged rows →</a></section><div class="cards">{cards}</div><section><h2>What this checked</h2><p>Every committed fixture row was scanned for an HTTPS publisher link and source ownership; every featured prediction was scanned for a 30-word minimum and a classified publisher link. Specific PDC, PGA Tour and Riot Games claims were then compared with their official publications. <strong>An official-looking hostname is not proof that every claim on that row is correct.</strong></p><p>Stored layer counts are repository measurements, not externally sourced sporting facts. Layers overlap and are not a unique match count.</p><ul class="layer-list">{layer_rows}</ul></section><section class="notice"><h2>Limits and disposition</h2><p>This is a dated integrity check, not an exhaustive scrape of all sports, live prices, or proof of every model input. {len(report['prediction_issues'])} predictions failed the structural word-count/publisher-host check; that does <em>not</em> certify their factual prose. Unverified or conflicting values stay blank on the review page. Upstream tables remain untouched under the shared task board; corrections are requested there.</p></section>'''
    (output / "index.html").write_text(shell("Publication integrity review", overview, "index.html"))
    sections = []
    for sport in ("Darts", "Golf", "eSports"):
        items = [f for f in cases if f["sport"] == sport]
        lines = []
        for f in items:
            refs = link(f["official_url"], "Official source") + (" · " + link(f["secondary_official_url"], "Second official source") if f.get("secondary_official_url") else "")
            supported = esc(f["official_value"]) if f["official_value"] else '<span class="blank">— unverified</span>'
            lines.append(f'<tr id="{esc(f["id"])}"><th scope="row"><code>{esc(f["row_id"])}</code><small>{esc(f["layer"])}</small></th><td>{esc(f["published"])}</td><td><span class="badge">{esc(f["status"])}</span><p>{esc(f["issue"])}</p></td><td>{supported}</td><td>{refs}</td></tr>')
        sections.append(f'<section id="{esc(sport.lower())}"><h2>{esc(sport)} <span class="count">{len(items)}</span></h2><div class="table-wrap"><table><thead><tr><th>Row / layer</th><th>Published value</th><th>Finding</th><th>Officially supported value</th><th>Official review links</th></tr></thead><tbody>{"".join(lines)}</tbody></table></div></section>')
    review = f'''<section class="hero"><p class="eyebrow">Evidence &amp; exceptions</p><h1>Flagged for Review</h1><p>These rows are not independently cleared. A blank means the disputed value could not be confirmed from the cited official publication. Each row links to its governing body or tournament operator for manual review.</p><div class="chips"><a href="#darts">Darts</a><a href="#golf">Golf</a><a href="#esports">eSports</a></div></section>{''.join(sections)}<section class="notice"><h2>Action before republishing</h2><p>Recheck the contested PDC replacement on a post-21 October official draw or match-centre page; remove or date the stale Utah row; replace all eight Liquipedia citations with Riot Games match/schedule pages and separately reverify model inputs. Requests to upstream file owners are logged in <a href="../COORDINATION.md">COORDINATION.md</a>.</p><p>See the <a href="../research/independent-audit-65ff36f0.md">evidence log</a> for source excerpts, capture limits and exact file locations.</p></section>'''
    (output / "flagged.html").write_text(shell("Flagged for Review", review, "flagged.html"))


if __name__ == "__main__":
    result = audit()
    build(result)
    print(f"Scanned {result['scanned_rows']} rows / {result['scanned_predictions']} predictions; {len(result['findings'])} flagged rows, {len(result['prediction_issues'])} structural prediction issues")
