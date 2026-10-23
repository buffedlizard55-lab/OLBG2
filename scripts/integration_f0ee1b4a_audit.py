#!/usr/bin/env python3
"""Audit the final 15-sport integration without refreshing or inventing data.

The row pass is an internal source-to-record and generated-data consistency check. External
spot checks performed with the page-reading tool are recorded separately with their own
URLs; this script does not claim that all 59 external sources were fetched again.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cadence"
OUT = ROOT / "data" / "integration-f0ee1b4a"
REPORT = ROOT / "research" / "integration-f0ee1b4a.md"
CHECK_UTC = "2026-10-23T21:30:02Z"
SESSION = "arena/f0ee1b4a-olbg2"
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
BANNED = re.compile(
    r"\b(model|models|modelled|modeled|modelling|modeling|verify|verified|verifies|verification)\b",
    re.I,
)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def american(probability: float) -> int:
    p = min(max(probability, 1e-4), 1 - 1e-4)
    if p >= 0.5:
        return int(round(-100.0 * p / (1 - p)))
    return int(round(100.0 * (1 - p) / p))


def main() -> None:
    fixtures_payload = load("fixtures.json")
    matches_payload = load("matches.json")
    lines_payload = load("lines.json")
    picks_payload = load("picks.json")
    predictions_payload = load("predictions.json")
    sources_payload = load("sources.json")
    fixtures = fixtures_payload["fixtures"]
    matches = {row["id"]: row for row in matches_payload["matches"]}
    sources = {row["key"]: row for row in sources_payload["sources"]}
    picks = {row["id"]: row for row in picks_payload["picks"]}
    errors: list[str] = []
    row_checks: list[dict] = []
    seen = set()

    common_fields = [
        "id", "sport", "competition", "home", "away", "venue", "start_utc", "time_display",
        "olbg_event_id", "official_source_url", "stats_source_url", "facts",
    ]
    event_urls = [row["url"] for row in sources.values() if "olbg.com" in row["url"]]

    for fixture in fixtures:
        fid = fixture["id"]
        row_errors: list[str] = []
        match = matches.get(fid)
        if match is None:
            row_errors.append("missing generated match row")
            match = {}
        for field in common_fields:
            if fixture.get(field) != match.get(field):
                row_errors.append(f"fixture/match drift: {field}")
        if fixture.get("sport") not in SPORTS:
            row_errors.append("out-of-scope sport")
        identity = (
            fixture.get("sport"), fixture.get("home"), fixture.get("away"),
            fixture.get("start_utc"), fixture.get("time_display"),
        )
        if identity in seen:
            row_errors.append("duplicate participant/start identity")
        seen.add(identity)
        official_url = fixture.get("official_source_url") or ""
        if not official_url.startswith("https://"):
            row_errors.append("official fixture URL is not HTTPS")
        for key in (fixture.get("source"), fixture.get("stats_source")):
            if key not in sources:
                row_errors.append(f"unregistered source key: {key}")
        if fixture.get("source") in sources:
            if official_url != sources[fixture["source"]]["url"]:
                row_errors.append("fixture URL differs from registered source URL")
        if fixture.get("stats_source") in sources:
            if fixture.get("stats_source_url") != sources[fixture["stats_source"]]["url"]:
                row_errors.append("stats URL differs from registered source URL")
        for fact in fixture.get("facts") or []:
            key = fact.get("source_key")
            if key not in sources:
                row_errors.append(f"fact has unregistered source: {key}")
            elif fact.get("source_url") != sources[key]["url"]:
                row_errors.append(f"fact URL differs from source register: {key}")
            if not str(fact.get("source_url", "")).startswith("https://"):
                row_errors.append("fact source is not HTTPS")
            if not str(fact.get("value", "")).strip():
                row_errors.append("empty fact value")
        if not fixture.get("facts"):
            row_errors.append("no sourced facts")
        if not fixture.get("start_utc") and not fixture.get("time_display"):
            row_errors.append("both UTC and publisher time are blank")
        if match.get("status") == "blank" and not str(match.get("note") or "").strip():
            row_errors.append("blank price row has no reason")
        event_id = fixture.get("olbg_event_id")
        if event_id is not None and not any(f"event_id={event_id}" in url for url in event_urls):
            row_errors.append(f"OLBG event id {event_id} has no registered event URL")
        if match.get("status") == "originated":
            primary = picks.get(f"{fid}-pick")
            if primary is None:
                row_errors.append("priced row has no primary selection")
            else:
                if match.get("favourite") != primary["selection"]:
                    row_errors.append("summary selection differs from primary pick")
                if match.get("favourite_probability") != round(primary["probability"], 4):
                    row_errors.append("summary probability differs from primary pick")
                if match.get("confidence") != primary["confidence"]:
                    row_errors.append("summary confidence differs from primary pick")
        blank_fields = [] if fixture.get("venue") else ["venue"]
        row_checks.append({
            "id": fid,
            "sport": fixture["sport"],
            "competition": fixture["competition"],
            "fixture": fixture["home"] + (f" v {fixture['away']}" if fixture.get("away") else ""),
            "official_source_url": official_url,
            "facts_checked": len(fixture.get("facts") or []),
            "price_status": match.get("status"),
            "start_representation": "UTC" if fixture.get("start_utc") else "publisher time string; no UTC inferred",
            "blank_fields": blank_fields,
            "review_notes": (["official participant order differs: Cork GAA lists Nemo Rangers first"] if fid == "gaa-cork-psfc" else []),
            "recorded_olbg_event_id": event_id,
            "active_olbg_listing_confirmed": False if event_id == 199984 else None,
            "internal_check": "fail" if row_errors else "pass",
            "issues": row_errors,
        })
        errors.extend(f"{fid}: {issue}" for issue in row_errors)

    fixture_ids = {row["id"] for row in fixtures}
    for line in lines_payload["lines"]:
        if line["fixture_id"] not in fixture_ids:
            errors.append(f"{line['id']}: line references unknown fixture")
        if american(round(line["probability"], 6)) != line["fair_american"]:
            errors.append(f"{line['id']}: American-price arithmetic drift")
        if line["in_band"] != (-250 <= line["fair_american"] <= 10000):
            errors.append(f"{line['id']}: band flag drift")
    for pick in picks_payload["picks"]:
        if pick["fixture_id"] not in fixture_ids:
            errors.append(f"{pick['id']}: pick references unknown fixture")
        if pick["in_band"] != (-250 <= pick["fair_american"] <= 10000):
            errors.append(f"{pick['id']}: band flag drift")
        if pick["confidence"] == "high" and pick["probability"] < 0.70:
            errors.append(f"{pick['id']}: high confidence below 70%")

    prediction_ids = set()
    for prediction in predictions_payload["predictions"]:
        pid = prediction["id"]
        prediction_ids.add(pid)
        if len(prediction["text"].split()) != prediction["word_count"] or prediction["word_count"] < 30:
            errors.append(f"{pid}: word-count/minimum-length drift")
        if BANNED.search(prediction["text"]) or BANNED.search(prediction["headline"]):
            errors.append(f"{pid}: prohibited reader-facing word")
        pick = picks.get(prediction["pick_id"])
        if pick is None:
            errors.append(f"{pid}: unknown pick")
            continue
        for field in ("fixture_id", "selection", "probability", "fair_american", "confidence"):
            if prediction[field] != pick[field]:
                errors.append(f"{pid}: {field} differs from pick")
        fixture_facts = {fact["value"] for fact in matches[prediction["fixture_id"]]["facts"]}
        for fact in prediction["facts"]:
            if fact["claim"] not in fixture_facts:
                errors.append(f"{pid}: prose fact absent from fixture record")
            if not fact["source_url"].startswith("https://"):
                errors.append(f"{pid}: fact without HTTPS source")

    blank_venues = [row for row in row_checks if "venue" in row["blank_fields"]]
    local_time_only = [row for row in row_checks if row["start_representation"] != "UTC"]
    recorded_olbg = [row for row in row_checks if row["recorded_olbg_event_id"] is not None]
    high_predictions = [p for p in predictions_payload["predictions"] if p["confidence"] == "high"]
    high_by_sport = Counter(p["sport"] for p in high_predictions)
    five_high_sports = sorted(sport for sport in SPORTS if high_by_sport[sport] >= 5)
    high_picks = [p for p in picks_payload["picks"] if p["confidence"] == "high" and p.get("sport_rank")]
    natural_band = [p for p in high_picks if p["in_band"] and not p.get("band_board")]
    alternate_band = [p for p in high_picks if p["in_band"] and p.get("band_board")]

    findings = [
        {
            "id": "FI-01", "severity": "high", "status": "corrected",
            "item": "Cork Gaelic football source-to-price inputs",
            "finding": "The previous calculation used +8 v +2. The cited scores are Nemo 1-15 to 0-16 and St Finbarr's 2-12 to 0-16, both two-point wins. The basis and generated row now use +2 v +2; the selection remains low confidence.",
            "source_url": "https://gaacork.ie/league/215999/",
            "review_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/scripts/cadence_model.py",
        },
        {
            "id": "FI-02", "severity": "high", "status": "corrected",
            "item": "Outright and three-way fixture summaries",
            "finding": "Six outright summaries used an event name or a blank opponent instead of the leading golfer, runner or driver; four also inverted the leading probability. Summaries now equal their primary selection. Three-way summaries use draw-inclusive probabilities.",
            "source_url": "https://www.pgatour.com/leaderboard",
            "review_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/tests/test_integration_f0ee1b4a.py",
        },
        {
            "id": "FI-03", "severity": "high", "status": "corrected",
            "item": "Unsupported Gaelic OLBG event id",
            "finding": "The Gaelic row's numeric olbg_event_id=14 had no corresponding event URL in the stored capture or source register. It was removed. A live read of that constructed URL returned 'No tips found.'",
            "source_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25?event_id=14",
            "review_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/fixtures.json",
        },
        {
            "id": "FI-04", "severity": "high", "status": "needs review",
            "item": "Current OLBG listing coverage is not established",
            "finding": f"Only {len(recorded_olbg)} of {len(row_checks)} rows retains a recorded OLBG event id with a matching registered URL, and its live re-read returned 'No tips found.' The integration therefore confirms zero currently readable active OLBG listings. The other rows are official-context fixtures, not claimed OLBG listings.",
            "source_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13?event_id=199984",
            "review_url": "https://buffedlizard55-lab.github.io/OLBG2/olbg/flagged.html",
        },
        {
            "id": "FI-05", "severity": "medium", "status": "needs review",
            "item": "Blank venue fields",
            "finding": f"{len(blank_venues)} fixture rows have no confirmed venue and remain blank across {len({r['sport'] for r in blank_venues})} sports. No venue has been inferred. Each affected row and its official source is enumerated below.",
            "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/fixtures.json",
            "review_url": "https://buffedlizard55-lab.github.io/OLBG2/cadence/matches.html",
        },
        {
            "id": "FI-06", "severity": "medium", "status": "needs review",
            "item": "Five high-confidence write-ups per sport",
            "finding": f"The target is met for {len(five_high_sports)} of 15 sports ({', '.join(five_high_sports)}). There are {len(high_predictions)} high-confidence and {len(predictions_payload['predictions']) - len(high_predictions)} medium-confidence write-ups in total; medium write-ups are not counted toward the high-confidence target.",
            "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/predictions.json",
            "review_url": "https://buffedlizard55-lab.github.io/OLBG2/cadence/predictions.html",
        },
        {
            "id": "FI-07", "severity": "low", "status": "needs review",
            "item": "NHL published comparison prices moved after the stored capture",
            "finding": "The live schedule still listed both NHL fixtures as FUT with the stored teams, starts and venues. Provider 8 showed Montréal -170 / Chicago +138 in the integration read, while the 20:05Z record stored -169 / +137. The desk's own probabilities were not changed; its historical comparison prose remains tied to the earlier capture.",
            "source_url": "https://api-web.nhle.com/v1/schedule/2026-10-23",
            "review_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/captures/nhle_schedule.json",
        },
        {
            "id": "FI-08", "severity": "medium", "status": "needs review",
            "item": "Historical desks are not consolidated into current counts",
            "finding": "Older overlapping desks retain their own stale taxonomy, prose and source-link findings. They are preserved for audit, not added to the current 93-row snapshot. The existing 16-findings repository audit remains linked from the current desk.",
            "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/cadence/repo_audit.json",
            "review_url": "https://buffedlizard55-lab.github.io/OLBG2/cadence/audit.html",
        },
        {
            "id": "FI-09", "severity": "medium", "status": "needs review",
            "item": "Cork official participant ordering differs between sources",
            "finding": "Cork GAA lists Nemo Rangers v St Finbarrs, while the stored Munster source string and generated row list St Finbarr's v Nemo Rangers. The final is at a neutral venue; no home/away designation is inferred and the underlying 48% low-confidence selection mapping is unchanged. The ordering discrepancy remains explicit for manual review.",
            "source_url": "https://gaacork.ie/league/215999/",
            "review_url": "https://munster.gaa.ie/fixtures/events-calendar/",
        },
    ]

    external_spot_checks = [
        {
            "checked_utc": CHECK_UTC,
            "url": "https://api-web.nhle.com/v1/schedule/2026-10-23",
            "result": "NHL JSON retrieved. Games 2026020166 and 2026020167 were FUT with the stored participants, UTC starts and venues. Provider 8 prices had moved as described in FI-07.",
        },
        {
            "checked_utc": CHECK_UTC,
            "url": "https://www.olbg.com/betting-tips/Ice_Hockey/13?event_id=199984",
            "result": "OLBG page retrieved; the event area displayed 'No tips found.' No active market or listing was inferred.",
        },
        {
            "checked_utc": CHECK_UTC,
            "url": "https://www.olbg.com/betting-tips/Gaelic_Football/25?event_id=14",
            "result": "OLBG page retrieved; it displayed 'No tips found.' and did not identify the Cork final.",
        },
        {
            "checked_utc": CHECK_UTC,
            "url": "https://gaacork.ie/league/215999/",
            "result": "Cork GAA page retrieved; it listed Nemo Rangers v St Finbarrs on 25 October at 16:00 and the two semi-final scorelines used in FI-01. Its participant order differs from the stored Munster source string, as disclosed in FI-09.",
        },
        {
            "checked_utc": CHECK_UTC,
            "url": "https://gaacork.ie/fixtures/",
            "result": "Cork GAA fixture page independently listed the same final, venue and referee David Murnane.",
        },
    ]

    summary = {
        "fixture_rows": len(row_checks),
        "row_internal_pass": sum(row["internal_check"] == "pass" for row in row_checks),
        "row_internal_fail": sum(row["internal_check"] == "fail" for row in row_checks),
        "fact_rows_checked": sum(row["facts_checked"] for row in row_checks),
        "registered_sources": len(sources),
        "priced_fixtures": matches_payload["originated"],
        "blank_price_fixtures": matches_payload["blank"],
        "originated_prices": lines_payload["count"],
        "graded_selections": picks_payload["count"],
        "written_predictions": predictions_payload["count"],
        "high_confidence_predictions": len(high_predictions),
        "medium_confidence_predictions": len(predictions_payload["predictions"]) - len(high_predictions),
        "five_high_writeup_sports": five_high_sports,
        "high_shortlisted_picks": len(high_picks),
        "natural_high_in_band": len(natural_band),
        "alternate_high_in_band": len(alternate_band),
        "blank_venues": len(blank_venues),
        "publisher_time_only": len(local_time_only),
        "recorded_olbg_event_ids": len(recorded_olbg),
        "active_olbg_listings_confirmed": 0,
        "errors": errors,
    }
    payload = {
        "schema": 1,
        "session": SESSION,
        "integration_check_utc": CHECK_UTC,
        "stored_snapshot_utc": matches_payload["generated_utc"],
        "method_boundary": "All rows checked internally against stored source registers and generated selections. External live reads were spot checks only, not a fresh re-read of every source.",
        "summary": summary,
        "findings": findings,
        "external_spot_checks": external_spot_checks,
        "row_checks": row_checks,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_markdown(payload), encoding="utf-8")
    print(
        f"integration audit: {summary['row_internal_pass']}/{summary['fixture_rows']} rows pass; "
        f"{summary['fact_rows_checked']} sourced facts; {len(errors)} errors; "
        f"{len(findings)} findings ({sum(f['status'] == 'needs review' for f in findings)} open)"
    )
    if errors:
        for error in errors:
            print("FAIL", error)
        raise SystemExit(1)


def render_markdown(payload: dict) -> str:
    s = payload["summary"]
    lines = [
        "# Final integration audit — 23 October 2026",
        "",
        f"- **Session:** `{payload['session']}`",
        f"- **Stored snapshot:** `{payload['stored_snapshot_utc']}`",
        f"- **Integration external spot checks:** `{payload['integration_check_utc']}`",
        "- **Primary site:** https://buffedlizard55-lab.github.io/OLBG2/cadence/",
        "",
        "> **Verification boundary.** Every one of the 93 fixture records was checked internally against the generated match, selection and source-register records. External pages were re-read only for the spot checks below. A 'pass' means internal consistency; it does not mean all 59 external sources were fetched again. Official links are provided for manual review.",
        "",
        "## Executive result",
        "",
        "| Check | Result |",
        "|---|---:|",
        f"| Fixture rows internally consistent | {s['row_internal_pass']} / {s['fixture_rows']} |",
        f"| Sourced fact entries checked | {s['fact_rows_checked']} |",
        f"| Registered official/OLBG sources | {s['registered_sources']} |",
        f"| Priced / blank-price fixtures | {s['priced_fixtures']} / {s['blank_price_fixtures']} |",
        f"| Originated prices / graded selections | {s['originated_prices']} / {s['graded_selections']} |",
        f"| High / medium write-ups | {s['high_confidence_predictions']} / {s['medium_confidence_predictions']} |",
        f"| Natural / alternate high selections in −250…+10000 | {s['natural_high_in_band']} / {s['alternate_high_in_band']} |",
        f"| Blank venues retained | {s['blank_venues']} |",
        f"| Publisher-local time strings retained without UTC inference | {s['publisher_time_only']} |",
        f"| Active OLBG listings confirmed by integration | {s['active_olbg_listings_confirmed']} |",
        f"| Internal errors after corrections | {len(s['errors'])} |",
        "",
        "The 93 rows are **not** represented as 93 currently listed OLBG events. The full OLBG schedule, every available market, current bookmaker prices and five qualifying high-confidence write-ups per sport remain incomplete and visible as review findings.",
        "",
        "## Findings and corrections",
        "",
        "| ID | Status | Item | Finding | Source | Manual review |",
        "|---|---|---|---|---|---|",
    ]
    for finding in payload["findings"]:
        text = finding["finding"].replace("|", "\\|")
        lines.append(
            f"| {finding['id']} | {finding['status']} | {finding['item']} | {text} | "
            f"[official/source]({finding['source_url']}) | [review]({finding['review_url']}) |"
        )
    lines += [
        "",
        "## External spot checks",
        "",
        "These are page-reading-tool observations, not a substitute for a raw-response archive or a full refresh.",
        "",
    ]
    for check in payload["external_spot_checks"]:
        lines.append(f"- **{check['checked_utc']} — [{check['url']}]({check['url']}):** {check['result']}")
    lines += [
        "",
        "## Line-by-line fixture checks",
        "",
        "Every row below was compared across `fixtures.json`, `matches.json`, its primary pick and the source register. 'Publisher time' means the official local/display string is retained and no UTC value was invented. Blank venue cells remain blank and are flagged here. 'OLBG listing unestablished' is not proof that an event is absent from OLBG; only the recorded NHL event URL was live-spot-checked in this integration.",
        "",
        "| # | Sport | Fixture | Facts | Price | Start representation | Blank / OLBG state | Internal check | Official source |",
        "|---:|---|---|---:|---|---|---|---|---|",
    ]
    for index, row in enumerate(payload["row_checks"], 1):
        blank = list(row["blank_fields"])
        if row["recorded_olbg_event_id"] is not None:
            blank.append("recorded OLBG id; active listing not confirmed")
        else:
            blank.append("OLBG listing unestablished")
        blank.extend(row.get("review_notes") or [])
        fixture = row["fixture"].replace("|", "\\|")
        lines.append(
            f"| {index} | {row['sport']} | {fixture} | {row['facts_checked']} | {row['price_status']} | "
            f"{row['start_representation']} | {', '.join(blank)} | {row['internal_check']} | "
            f"[official]({row['official_source_url']}) |"
        )
    lines += [
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 scripts/cadence_seed.py",
        "python3 scripts/cadence_model.py",
        "python3 scripts/cadence_predictions.py",
        "python3 scripts/cadence_build.py",
        "python3 scripts/cadence_verify.py",
        "python3 scripts/integration_f0ee1b4a_audit.py",
        "python3 -m unittest tests.test_integration_f0ee1b4a -v",
        "```",
        "",
        "No probability was copied from OLBG. The integration corrections changed the Cork basis and fixture-summary presentation; they did not create a high-confidence pick or add prediction prose.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
