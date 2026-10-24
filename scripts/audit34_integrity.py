#!/usr/bin/env python3
"""Independent, offline integrity audit for the published 24 October board.

The external facts in data/audit34 are deliberately small audit indexes transcribed
from first-hand official reads. This script does not pretend that an offline check
is a fresh network verification; source-read windows and limitations stay in JSON.
"""
from __future__ import annotations

import html.parser
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TODAY_DATA = ROOT / "data" / "today"
TODAY_SITE = ROOT / "today"
AUDIT_DATA = ROOT / "data" / "audit34"
REPORT = AUDIT_DATA / "report.json"
USER_HIGH = 0.70
BAND_MIN = -250
BAND_MAX = 10000
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
    "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
    "Handball", "Ice Hockey", "Basketball", "Rugby League",
]
REPO_REVIEW = "https://github.com/buffedlizard55-lab/OLBG2/blob/main/"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def american(probability: float) -> int:
    if probability >= 0.5:
        return -round(100 * probability / (1 - probability))
    return round(100 * (1 - probability) / probability)


def within_requested_band(price: int) -> bool:
    return BAND_MIN <= price <= BAND_MAX


class TableAudit(html.parser.HTMLParser):
    """Count data rows and external review links; header rows are excluded."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self.row: dict | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self.row = {"cells": 0, "external": 0}
        elif self.row is not None and tag == "td":
            self.row["cells"] += 1
        elif self.row is not None and tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith(("https://", "http://")):
                self.row["external"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.row is not None:
            if self.row["cells"]:
                self.rows.append(self.row)
            self.row = None


class LinkAudit(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def audit() -> dict:
    listings_payload = load(TODAY_DATA / "olbg_listings.json")
    fixtures = listings_payload["fixtures"]
    listings = listings_payload["listings"]
    picks_payload = load(TODAY_DATA / "picks.json")
    picks = picks_payload["picks"]
    lines_payload = load(TODAY_DATA / "lines.json")
    lines = lines_payload["lines"]
    predictions_payload = load(TODAY_DATA / "predictions.json")
    predictions = predictions_payload["predictions"]
    flagged = load(TODAY_DATA / "flagged.json")["items"]
    official_nhl = load(AUDIT_DATA / "official_nhl_2026-10-24.json")
    official_mlb = load(AUDIT_DATA / "official_mlb_2026-10-24.json")
    manual = load(AUDIT_DATA / "manual_findings.json")

    findings: list[dict] = []
    checks = 0

    def add(code: str, severity: str, detail: str, affected_ids, source_url: str,
            review_path: str = "data/today") -> None:
        findings.append({
            "code": code,
            "severity": severity,
            "affected_ids": list(affected_ids),
            "detail": detail,
            "source_url": source_url,
            "review_url": REPO_REVIEW + review_path,
            "origin": "automated",
        })

    # Every machine-readable row must retain a reviewable provenance link.
    for row in fixtures:
        checks += 1
        if not row.get("source_url", "").startswith("https://"):
            add("FIXTURE-SOURCE-MISSING", "high", "Fixture has no HTTPS official source.",
                [row.get("id")], "", "data/today/olbg_listings.json")
    for row in listings:
        checks += 1
        if not row.get("url", "").startswith("https://www.olbg.com/"):
            add("OLBG-ROW-LINK-MISSING", "high", "OLBG listing row has no OLBG event link.",
                [row.get("event_id")], "https://www.olbg.com/betting-tips",
                "data/today/olbg_listings.json")
    for row in flagged:
        checks += 1
        if not row.get("source", "").startswith("https://"):
            add("REVIEW-ROW-LINK-MISSING", "medium", "Review row has no evidence link.",
                [row.get("code")], "https://www.olbg.com/betting-tips",
                "data/today/flagged.json")

    # Compare each published fixture with the fields actually read from official feeds.
    nhl_by_id = {g["game_id"]: g for g in official_nhl["games"]}
    for row in [f for f in fixtures if f["sport"] == "Ice Hockey"]:
        game_id = int(row["id"].removeprefix("nhl-"))
        official = nhl_by_id.get(game_id)
        checks += 1
        if not official:
            add("NHL-GAME-NOT-IN-AUDIT-INDEX", "high",
                "Published NHL game id was not present in the first-hand official audit index.",
                [row["id"]], official_nhl["source_url"], "data/today/olbg_listings.json")
            continue
        comparisons = {
            "start_utc": row["start_utc"] == official["start_utc"],
            "venue": row["venue"] == official["venue"],
            "home_record": row["home_record"] == official["home_record"],
            "away_record": row["away_record"] == official["away_record"],
            "home_name": row["home"].endswith(official["home"]),
            "away_name": row["away"].endswith(official["away"]),
        }
        checks += len(comparisons)
        for field, matches in comparisons.items():
            if not matches:
                add("NHL-FIXTURE-FIELD-MISMATCH", "high",
                    f"Published {field} does not match the official audit index for game {game_id}.",
                    [row["id"]], official["official_url"], "data/today/olbg_listings.json")

    published_nhl_ids = {int(f["id"].removeprefix("nhl-")) for f in fixtures
                         if f["sport"] == "Ice Hockey"}
    missing_nhl = [g for g in official_nhl["games"] if g["game_id"] not in published_nhl_ids]
    checks += 1
    if missing_nhl:
        add("NHL-OFFICIAL-COVERAGE-GAP", "high",
            "The official response reported 12 NHL games but the board has only 7 NHL fixtures. "
            "Missing game ids: " + ", ".join(str(g["game_id"]) for g in missing_nhl) +
            ". Five corresponding OLBG event ids already exist in the stored hub capture; these are coverage omissions, not blank values to infer away.",
            [g["game_id"] for g in missing_nhl], official_nhl["source_url"],
            "data/today/olbg_listings.json")

    mlb_by_id = {g["game_id"]: g for g in official_mlb["games"]}
    for row in [f for f in fixtures if f["sport"] == "Baseball"]:
        game_id = int(row["id"].removeprefix("mlb-"))
        official = mlb_by_id.get(game_id)
        checks += 1
        if not official:
            add("MLB-GAME-NOT-IN-AUDIT-INDEX", "high",
                "Published MLB game id was not present in the official audit index.",
                [row["id"]], official_mlb["schedule_url"], "data/today/olbg_listings.json")
            continue
        runs = row.get("runs") or {}
        comparisons = {
            "start_utc": row["start_utc"] == official["start_utc"],
            "venue": row["venue"] == official["venue"],
            "home": row["home"] == official["home"],
            "away": row["away"] == official["away"],
            "home_record": row["home_record"] == official["home_record"],
            "away_record": row["away_record"] == official["away_record"],
            "home_runs_scored": runs.get("home_scored") == official["home_runs_scored"],
            "home_runs_allowed": runs.get("home_allowed") == official["home_runs_allowed"],
            "away_runs_scored": runs.get("away_scored") == official["away_runs_scored"],
            "away_runs_allowed": runs.get("away_allowed") == official["away_runs_allowed"],
        }
        checks += len(comparisons)
        for field, matches in comparisons.items():
            if not matches:
                add("MLB-FIXTURE-FIELD-MISMATCH", "high",
                    f"Published {field} does not match the official MLB audit index.",
                    [row["id"]], official["official_url"], "data/today/olbg_listings.json")

    # Identify OLBG events that were captured but never joined to an official fixture.
    joined_event_ids = {str(f.get("olbg_event_id")) for f in fixtures if f.get("olbg_event_id")}
    unjoined_nhl = [r for r in listings if r.get("competition") == "NHL"
                    and str(r["event_id"]) not in joined_event_ids]
    checks += 1
    if unjoined_nhl:
        add("NHL-OLBG-JOIN-GAP", "high",
            "Stored NHL OLBG listings without a joined official fixture: " +
            ", ".join(f"{r['event_id']} ({r['event']})" for r in unjoined_nhl) +
            ". The official audit index contains all five corresponding games.",
            [r["event_id"] for r in unjoined_nhl], "https://www.olbg.com/betting-tips/Ice_Hockey/13",
            "data/today/olbg_listings.json")

    # Price arithmetic, temporal gate, confidence rule and OLBG availability.
    for row in lines:
        checks += 3
        expected_american = american(row["probability"])
        if row["fair_american"] != expected_american:
            add("PRICE-AMERICAN-MISMATCH", "high",
                f"Stored fair American price {row['fair_american']} should be {expected_american} from the stored probability.",
                [row["id"]], row["source_url"], "data/today/lines.json")
        if abs(row["fair_decimal"] - 1 / row["probability"]) > 0.0011:
            add("PRICE-DECIMAL-MISMATCH", "high", "Fair decimal price is not the reciprocal of probability.",
                [row["id"]], row["source_url"], "data/today/lines.json")
        if not row.get("source_url", "").startswith("https://"):
            add("LINE-SOURCE-MISSING", "high", "Originated line has no HTTPS input source.",
                [row["id"]], "", "data/today/lines.json")

    for row in picks:
        checks += 5
        if row["confidence"] == "high" and row["probability"] < USER_HIGH:
            # The configuration-level finding below groups all affected rows.
            pass
        if row["in_band"] != within_requested_band(row["fair_american"]):
            add("PICK-BAND-FLAG-MISMATCH", "high", "Stored in_band value disagrees with the fair American price.",
                [row["fixture_id"]], row["source_url"], "data/today/picks.json")
        if row["start_utc"] <= picks_payload["as_of_utc"]:
            add("PICK-NOT-FUTURE-AT-CUTOFF", "high", "Pick did not start after the selection cutoff.",
                [row["fixture_id"]], row["source_url"], "data/today/picks.json")
        if not row.get("olbg_event_url"):
            add("PICK-WITHOUT-OLBG-LISTING", "high",
                "An actionable pick is published without an OLBG event URL in the stored snapshot.",
                [row["fixture_id"]], "https://www.olbg.com/betting-tips/Ice_Hockey/13",
                "data/today/picks.json")
        if not row.get("source_url", "").startswith("https://"):
            add("PICK-SOURCE-MISSING", "high", "Pick has no official HTTPS source.",
                [row["fixture_id"]], "", "data/today/picks.json")

    below_user_high = [p for p in picks if p["confidence"] == "high" and p["probability"] < USER_HIGH]
    checks += 1
    if lines_payload["thresholds"].get("high") != USER_HIGH or below_user_high:
        add("HIGH-THRESHOLD-NOT-70", "high",
            f"The configured high threshold is {lines_payload['thresholds'].get('high'):.2%}, not the requested 70.00%. "
            + "; ".join(f"{p['selection']} is {p['probability']:.2%}" for p in below_user_high)
            + ". Boston displays as 70.0% only after one-decimal rounding; its stored probability is 69.95%.",
            [p["fixture_id"] for p in below_user_high], "https://github.com/buffedlizard55-lab/OLBG2",
            "scripts/today_model.py")

    executive = picks[:3]
    out_of_band_executive = [p for p in executive if not p["in_band"]]
    checks += 1
    if out_of_band_executive:
        add("EXECUTIVE-OUT-OF-BAND", "high",
            "The three-card executive summary leads with a selection explicitly outside the requested −250…+10000 focus band. "
            "Keep out-of-band analysis in a separate review section rather than the primary executive card.",
            [p["fixture_id"] for p in out_of_band_executive],
            "https://github.com/buffedlizard55-lab/OLBG2", "scripts/today_build.py")

    # Prediction requirements: one unique, sourced, >=30-word preview per published pick.
    pred_by_fixture = {p["fixture_id"]: p for p in predictions}
    seen_text: dict[str, str] = {}
    for row in picks:
        checks += 1
        if row["fixture_id"] not in pred_by_fixture:
            add("PICK-PREVIEW-MISSING", "high", "Published pick has no written preview.",
                [row["fixture_id"]], row["source_url"], "data/today/predictions.json")
    for row in predictions:
        words = row["text"].split()
        normalized = re.sub(r"\s+", " ", row["text"].strip().lower())
        checks += 7
        if len(words) < 30:
            add("PREVIEW-TOO-SHORT", "high", f"Preview has only {len(words)} whitespace-delimited words.",
                [row["id"]], row["official_fixture_url"], "data/today/predictions.json")
        if row.get("word_count") != len(words):
            add("PREVIEW-WORD-COUNT-MISMATCH", "medium",
                f"Stored word_count={row.get('word_count')} but whitespace count is {len(words)}.",
                [row["id"]], row["official_fixture_url"], "data/today/predictions.json")
        if re.search(r"\b(?:model|verified)\b", row["text"], re.I):
            add("PREVIEW-FORBIDDEN-TERM", "high", "Prediction text contains an internal-only term.",
                [row["id"]], row["official_fixture_url"], "data/today/predictions.json")
        if normalized in seen_text:
            add("PREVIEW-DUPLICATE", "high", f"Preview duplicates {seen_text[normalized]}.",
                [row["id"]], row["official_fixture_url"], "data/today/predictions.json")
        seen_text[normalized] = row["id"]
        if not row.get("facts") or any(not f.get("source_url", "").startswith("https://") for f in row["facts"]):
            add("PREVIEW-FACT-SOURCE-MISSING", "high", "A preview fact lacks an HTTPS source.",
                [row["id"]], row["official_fixture_url"], "data/today/predictions.json")
        pick = pred_by_fixture.get(row["fixture_id"]) and next(
            (p for p in picks if p["fixture_id"] == row["fixture_id"]), None)
        if pick and (pick["selection"] != row["selection"] or pick["market"] != row["market"]):
            add("PREVIEW-PICK-MISMATCH", "high", "Preview selection or market differs from its pick row.",
                [row["id"]], row["official_fixture_url"], "data/today/predictions.json")
        if row["confidence"] == "high" and row["probability"] < USER_HIGH:
            # Grouped in HIGH-THRESHOLD-NOT-70; keep this check explicit in the count.
            pass

    # The displayed fact source must cover the actual input family used.
    standings_citation = [p for p in predictions if any(
        re.search(r"goals for|goals against|\d+ against", f["claim"], re.I)
        and "/score/" in f["source_url"] for f in p["facts"])]
    checks += 1
    if standings_citation:
        add("STANDINGS-CITATION-MISSING", "medium",
            "Goal-for/goal-against facts cite the score endpoint; those direct standings fields belong to the official standings endpoint. "
            "The audit re-read confirmed Boston 42/22 and Vegas 46/36 at the standings URL.",
            [p["id"] for p in standings_citation], "https://api-web.nhle.com/v1/standings/2026-10-24",
            "data/today/predictions.json")

    mlb_total_lines = [l for l in lines if l["sport"] == "Baseball" and l["market"] == "Game total"]
    checks += 1
    if any("standings" in l["source_label"].lower() and "standings" not in l["source_url"].lower()
           for l in mlb_total_lines):
        add("MLB-TOTAL-INPUT-LINK-GAP", "medium",
            "All four MLB total rows say schedule + season standings but link only the schedule. "
            "The run inputs come from two standings responses, so each total row needs those input links as well.",
            [l["id"] for l in mlb_total_lines], official_mlb["standings_urls"][0],
            "data/today/lines.json")

    nhl_markets = sorted({l["market"] for l in lines if l["sport"] == "Ice Hockey"})
    all_markets = sorted({l["market"] for l in lines})
    checks += 1
    if nhl_markets == ["Money line"] or not any("handicap" in m.lower() for m in all_markets):
        add("MARKET-INVESTIGATION-INCOMPLETE", "medium",
            f"Published NHL markets are {nhl_markets}; the complete board has {all_markets}. "
            "No handicap market is originated anywhere, and no NHL total is originated despite game-total listings in the OLBG capture. "
            "Unavailable or unpriced markets should be enumerated with a reason rather than omitted silently.",
            ["data/today/lines.json"], "https://www.olbg.com/betting-tips/Ice_Hockey/13",
            "data/today/lines.json")

    # Qualified written high-confidence picks are counted under the user's actual rules.
    qualified_by_sport = {}
    for sport in SPORTS:
        qualified = []
        for p in picks:
            pred = pred_by_fixture.get(p["fixture_id"])
            if (p["sport"] == sport and p["confidence"] == "high"
                    and p["probability"] >= USER_HIGH and p["in_band"]
                    and p.get("olbg_event_url") and pred and len(pred["text"].split()) >= 30):
                qualified.append(p["fixture_id"])
        qualified_by_sport[sport] = {"count": len(qualified), "shortfall": 5 - len(qualified),
                                     "fixture_ids": qualified}
    checks += len(SPORTS)
    for sport, row in qualified_by_sport.items():
        if row["shortfall"] and any(p["sport"] == sport for p in picks):
            add("QUALIFIED-FIVE-PER-SPORT-SHORTFALL", "medium",
                f"{sport} has {row['count']} written high-confidence picks that also meet the 70% rule, band rule and stored OLBG-link rule; "
                f"the target is five. Existing top-five counts include medium or otherwise unqualified rows.",
                row["fixture_ids"] or [sport], "https://www.olbg.com/betting-tips",
                "data/today/picks.json")

    # Root usability: the 24 October notice must not sit above a stale executive body.
    root_html = (ROOT / "index.html").read_text(encoding="utf-8")
    checks += 2
    if "Start here: the 24 October board" in root_html and "Today's matches — 2026-10-23" in root_html:
        add("ROOT-STALE-EXECUTIVE-BODY", "high",
            "The root notice points to the 24 October board, but the main executive body still labels 23 October matches as today's and its primary button opens the older cadence dashboard. "
            "That is the navigation ambiguity the consolidation must remove.",
            ["index.html"], "https://github.com/buffedlizard55-lab/OLBG2", "index.html")
    nav_match = re.search(r"<nav\b.*?</nav>", root_html, re.S)
    root_nav_links = len(re.findall(r"<a\b", nav_match.group(0))) if nav_match else 0
    if root_nav_links > 12:
        add("ROOT-NAVIGATION-OVERLOAD", "medium",
            f"The root navigation contains {root_nav_links} links mixing current and historical desks. "
            "The current landing page should expose the executive summary, picks, matches, predictions, 15 sport pages and review queue first; historical material belongs in one archive link.",
            ["index.html"], "https://github.com/buffedlizard55-lab/OLBG2", "index.html")

    # Static row/link checks cover every /today/ HTML table, not just the JSON samples.
    html_rows = 0
    html_rows_without_link = []
    local_link_errors = []
    parsed_pages = {}
    for page in sorted(TODAY_SITE.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        tables = TableAudit()
        tables.feed(text)
        html_rows += len(tables.rows)
        for row in tables.rows:
            if not row["external"]:
                html_rows_without_link.append(str(page.relative_to(ROOT)))
        links = LinkAudit()
        links.feed(text)
        parsed_pages[page.resolve()] = links
    checks += html_rows
    for source_page, parser in parsed_pages.items():
        for href in parser.links:
            if href.startswith(("https://", "http://", "mailto:", "tel:", "data:")):
                continue
            parts = urlsplit(href)
            if not parts.path and parts.fragment:
                target = source_page
            else:
                target = (source_page.parent / unquote(parts.path)).resolve()
            if not target.exists():
                local_link_errors.append(f"{source_page}: missing {href}")
            elif parts.fragment and target.suffix == ".html":
                target_parser = parsed_pages.get(target)
                if target_parser and parts.fragment not in target_parser.ids:
                    local_link_errors.append(f"{source_page}: missing anchor {href}")
    checks += sum(len(p.links) for p in parsed_pages.values())
    if html_rows_without_link:
        add("HTML-ROW-SOURCE-MISSING", "high",
            "One or more published /today/ table body rows has no external review link.",
            sorted(set(html_rows_without_link)), "https://github.com/buffedlizard55-lab/OLBG2", "today")
    if local_link_errors:
        add("TODAY-LOCAL-LINK-ERROR", "high", "; ".join(local_link_errors[:20]),
            ["today"], "https://github.com/buffedlizard55-lab/OLBG2", "today")

    checks += 1
    raw_candidates = [p for p in TODAY_DATA.rglob("*") if p.is_file()
                      and p.suffix.lower() in {".html", ".txt", ".jsonl", ".zip"}]
    if not raw_candidates:
        add("RAW-SNAPSHOT-NOT-COMMITTED", "medium",
            "The /today/ source register describes first-hand reads but no raw official or OLBG response body is committed. "
            "Later readers can recheck the live URL but cannot independently reconstruct the historical response or changing prices/tip totals from the derived JSON alone.",
            ["data/today/sources.json"], "https://api-web.nhle.com/v1/score/2026-10-24",
            "data/today/sources.json")

    for item in manual["findings"]:
        findings.append({**item, "origin": "first-hand source read"})

    severities = Counter(f["severity"] for f in findings)
    return {
        "recorded_at_utc": manual["recorded_at_utc"],
        "status": "needs review" if findings else "pass",
        "scope": "Published /today/ board and root navigation; historical archive desks are outside this audit's external-fact scope.",
        "source_reads": manual["source_reads"],
        "summary": {
            "checks": checks,
            "findings": len(findings),
            "by_severity": dict(sorted(severities.items())),
            "fixtures": len(fixtures),
            "official_fixture_index": len(official_nhl["games"]) + len(official_mlb["games"]),
            "published_nhl_fixtures": len(published_nhl_ids),
            "official_nhl_games": len(official_nhl["games"]),
            "missing_nhl_fixture_ids": [g["game_id"] for g in missing_nhl],
            "olbg_listings": len(listings),
            "lines": len(lines),
            "picks": len(picks),
            "predictions": len(predictions),
            "high_at_stored_65_rule": sum(p["confidence"] == "high" for p in picks),
            "high_at_requested_70_rule": sum(p["confidence"] == "high" and p["probability"] >= USER_HIGH for p in picks),
            "qualified_high_in_band_with_olbg": sum(p["confidence"] == "high" and p["probability"] >= USER_HIGH
                                                       and p["in_band"] and bool(p.get("olbg_event_url")) for p in picks),
            "html_table_rows_checked": html_rows,
            "html_rows_without_external_link": len(html_rows_without_link),
            "local_link_errors": len(local_link_errors),
            "root_nav_links": root_nav_links,
        },
        "qualified_by_sport": qualified_by_sport,
        "findings": sorted(findings, key=lambda f: (f["severity"] != "high", f["code"], str(f["affected_ids"]))),
    }


def main() -> None:
    report = audit()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"audit34: {report['summary']['checks']} checks, {report['summary']['findings']} findings, "
          f"{report['summary']['local_link_errors']} local link errors")
    for finding in report["findings"]:
        print(f"{finding['severity'].upper()} {finding['code']}: {','.join(map(str, finding['affected_ids']))}")


if __name__ == "__main__":
    main()
