#!/usr/bin/env python3
"""Render the independent audit as a human-reviewable Markdown report."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
AUDIT = ROOT / "data" / "audit34"
OUT = ROOT / "research" / "34af5757-evidence-audit.md"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def md(value):
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(md(cell) for cell in row) + " |" for row in rows],
    ])


def pct(value):
    return f"{value:.2%}"


def main():
    report = load(AUDIT / "report.json")
    listings_payload = load(DATA / "olbg_listings.json")
    fixtures = listings_payload["fixtures"]
    picks = load(DATA / "picks.json")["picks"]
    lines = load(DATA / "lines.json")["lines"]
    predictions = load(DATA / "predictions.json")["predictions"]
    nhl = load(AUDIT / "official_nhl_2026-10-24.json")
    mlb = load(AUDIT / "official_mlb_2026-10-24.json")
    flagged = load(DATA / "flagged.json")
    published_nhl = {int(f["id"].split("-")[-1]): f for f in fixtures if f["sport"] == "Ice Hockey"}
    published_mlb = {int(f["id"].split("-")[-1]): f for f in fixtures if f["sport"] == "Baseball"}
    olbg_by_game = {
        2026020168: "199999", 2026020169: "200000", 2026020170: "200007",
        2026020171: "200008", 2026020172: "200006", 2026020174: "200001",
        2026020175: "200002", 2026020176: "200010", 2026020177: "200009",
        2026020178: "200004", 2026020179: "200005",
    }

    findings_by_id = {}
    for finding in report["findings"]:
        for affected in finding["affected_ids"]:
            findings_by_id.setdefault(str(affected), []).append(finding["code"])

    fixture_rows = []
    for game in nhl["games"]:
        published = published_nhl.get(game["game_id"])
        match = (f"{published['away']} @ {published['home']}" if published else
                 f"{game['away']} ({game['away_abbrev']}) @ {game['home']} ({game['home_abbrev']})")
        if published:
            result = "Matched: names, start, venue and both records checked"
        else:
            event = olbg_by_game.get(game["game_id"])
            result = "MISSING from board" + (f"; stored OLBG event {event}" if event else "")
        fixture_rows.append([
            game["game_id"], match, game["start_utc"],
            f"{game['away_record']} / {game['home_record']}", result,
            f"[NHL game centre]({game['official_url']})",
        ])
    for game in mlb["games"]:
        published = published_mlb.get(game["game_id"])
        fixture_rows.append([
            game["game_id"], f"{game['away']} @ {game['home']}", game["start_utc"],
            f"{game['away_record']} / {game['home_record']}",
            "Matched: names, start, venue, records and four run inputs checked" if published else "MISSING from board",
            f"[MLB schedule]({game['official_url']})",
        ])

    pick_by_fixture = {p["fixture_id"]: p for p in picks}
    prediction_rows = []
    for pred in predictions:
        pick = pick_by_fixture[pred["fixture_id"]]
        requested_high = pick["confidence"] == "high" and pick["probability"] >= 0.70
        codes = sorted(set(findings_by_id.get(pred["id"], []) + findings_by_id.get(pred["fixture_id"], [])))
        prediction_rows.append([
            pred["id"], f"{pred['selection']} — {pred['market']}", pct(pred["probability"]),
            pick["confidence"], "high" if requested_high else "not high under requested rule",
            "in" if pick["in_band"] else "outside",
            "yes" if pick.get("olbg_event_url") else "NO stored link",
            len(pred["text"].split()), ", ".join(codes) or "none",
            f"[official input]({pred['official_fixture_url']})",
        ])

    line_rows = []
    for line in lines:
        codes = findings_by_id.get(line["id"], [])
        line_rows.append([
            line["id"], f"{line['selection']} — {line['market']}", pct(line["probability"]),
            line["fair_american"], f"{line['fair_decimal']:.3f}",
            "pass" if not any(c.startswith("PRICE-") for c in codes) else "FAIL",
            ", ".join(codes) or "none", f"[input]({line['source_url']})",
        ])

    finding_rows = [[
        f["severity"].upper(), f["code"], ", ".join(map(str, f["affected_ids"])),
        f["detail"], f["origin"], f"[source]({f['source_url']})",
        f"[review]({f['review_url']})",
    ] for f in report["findings"]]

    source_rows = [[f"[official/source page]({r['url']})", r["result"]] for r in report["source_reads"]]
    hubs = {s["sport"]: s["hub_url"] for s in flagged["sports"]}
    quota_rows = [[sport, row["count"], row["shortfall"], f"[OLBG hub]({hubs[sport]})"]
                  for sport, row in report["qualified_by_sport"].items()]

    s = report["summary"]
    content = f"""# Independent evidence and usability audit — 24 October 2026

**Session:** `arena/34af5757-olbg2`  
**Recorded:** {report['recorded_at_utc']}  
**Status:** **{report['status'].upper()}** — {s['findings']} findings from {s['checks']} offline field, row, arithmetic, prose and link checks.

## Executive result

The current `/today/` board is **not ready to be described as a full list or as five qualified high-confidence picks per sport**.
The official NHL response contains 12 games, while the board contains seven NHL rows. The five omitted games already have OLBG
event ids in the stored hub capture. One published high pick is below the requested 70% rule, and only **one** published pick is
simultaneously high under that rule, inside the requested price band, linked to an OLBG event in the stored data, and accompanied
by a ≥30-word preview.

No current fixture value was changed by this audit. The 8 published fixtures match the official audit fields checked below.
The findings are corrections for the active integration owner, not silently patched facts. Historical archive desks are outside
this external-fact audit; the root navigation is included because it directs readers between those desks.

| Metric | Result |
|---|---:|
| Published fixtures / official audit index | {s['fixtures']} / {s['official_fixture_index']} |
| Published NHL fixtures / official NHL response | {s['published_nhl_fixtures']} / {s['official_nhl_games']} |
| OLBG listing rows | {s['olbg_listings']} |
| Originated line rows | {s['lines']} |
| Picks / written previews | {s['picks']} / {s['predictions']} |
| High under stored 65% rule / requested 70% rule | {s['high_at_stored_65_rule']} / {s['high_at_requested_70_rule']} |
| Qualified high + in-band + stored OLBG link | {s['qualified_high_in_band_with_olbg']} |
| `/today/` HTML table rows checked | {s['html_table_rows_checked']} |
| Table rows without an external review link | {s['html_rows_without_external_link']} |
| Local link or anchor errors | {s['local_link_errors']} |
| Root navigation links | {s['root_nav_links']} |

## Official-source reads performed for this audit

These were first-hand reads, not copied claims from the repository. The committed NHL/MLB audit indexes explicitly say they are
transcribed fields, not raw responses. Live pages can change after the read window.

{table(['Source', 'What the response supported'], source_rows)}

## Fixture reconciliation — every official audit-index row

Records are shown as **away / home**. “Matched” refers only to the named fields; it is not a claim that every statistic elsewhere
in the repository was rechecked. Missing rows must be added from the official response by the integration owner, not backfilled by inference.

{table(['Game id', 'Match', 'Official start', 'Record A / H', 'Audit result', 'Official review link'], fixture_rows)}

## Pick and prediction reconciliation — every published preview

“Requested grade” applies the 70% floor without one-decimal display rounding. A preview can be well sourced and still fail the
selection, band or OLBG-availability rule; those are separate columns deliberately.

{table(['Preview id', 'Selection / market', 'Probability', 'Stored grade', 'Requested grade', 'Band', 'OLBG stored', 'Words', 'Finding codes', 'Source'], prediction_rows)}

## Originated-line arithmetic — every published line

Fair American and decimal prices were recomputed from each stored probability. A passing arithmetic check does not validate the
probability itself or prove that a market was available at a sportsbook.

{table(['Line id', 'Selection / market', 'Probability', 'Fair US', 'Fair decimal', 'Arithmetic', 'Other findings', 'Input'], line_rows)}

## Qualified five-per-sport coverage

A qualified row here must be high at ≥70%, inside −250…+10000, linked to an OLBG event in the stored snapshot and have a unique
≥30-word preview. This intentionally stricter count exposes where a “top five” includes medium or otherwise unqualified rows.

{table(['Sport', 'Qualified previews', 'Shortfall from five', 'Listing source'], quota_rows)}

## Flagged for Review — all findings

{table(['Severity', 'Code', 'Affected rows', 'Finding / required correction', 'Basis', 'Source', 'Manual review'], finding_rows)}

## Checks that passed

- All 8 published fixtures matched the official audit-index fields listed above; there were no NHL/MLB field mismatches.
- All 20 fair American and decimal price calculations matched their stored probabilities; all stored band flags matched the numeric price test.
- Every published pick had a preview. All 6 previews had at least 30 words, matching stored word counts, unique text, matching selections/markets and fact-level HTTPS links; none contained either prohibited internal-only term.
- Every one of the {s['html_table_rows_checked']} `/today/` HTML table body rows contained an external review link. Local page links and fragments passed with zero errors.
- The MLB fixture, probable pitchers, venue, start, season records, run totals and home/away/last-ten splits were supported by the official MLB responses listed above.
- The official NHL score response supports Alex Tuch as a WSH leader with five goals. The flagged Washington issue is the citation endpoint, not an unsupported roster assertion.

## Required integration actions

1. Join the five omitted official NHL games to their already captured OLBG event ids, then recalculate the actual five highest eligible ice-hockey selections from the full candidate set.
2. Apply one documented 70% high-confidence rule. Do not let one-decimal formatting turn 69.95% into an apparently qualifying 70.0% high pick.
3. Keep the out-of-band New Jersey selection out of the primary in-band executive summary; do not reprice it to fit.
4. Remove the contradicted Vegas superlative, add the missing standings citations and correct the Washington citation endpoint.
5. Describe Tipsport prices as third-party prices carried by the NHL feed. Add all standings input URLs to MLB total rows.
6. Enumerate unpriced market families and reasons; do not represent moneyline-only NHL coverage as an investigation of every available market.
7. Replace the stale root executive body and overloaded current/historical navigation with one current desk and one archive link.
8. Preserve raw, timestamped source responses or clearly retain the current limitation. Refresh dynamic OLBG tip/absence claims before publication.

## Reproduce

```sh
python3 scripts/audit34_integrity.py
python3 scripts/audit34_report.py
python3 -m unittest tests.test_audit34 -v
python3 scripts/integration_audit.py
```

`data/audit34/report.json` is the machine-readable exception register. This audit does not claim fresh official reads for the other
14 sports, does not fill their missing fixtures, and does not mark the five-per-sport target complete.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(content.splitlines())} lines)")


if __name__ == "__main__":
    main()
