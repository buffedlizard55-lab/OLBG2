#!/usr/bin/env python3
"""Generate the line-by-line human-review ledger from Vantage's frozen data."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/vantage"
OUTPUT = ROOT / "research/vantage-7a6b583e.md"


def load(n):
    return json.loads((DATA / n).read_text(encoding="utf-8"))


def escape(s):
    return str(s or "—").replace("|", "\\|").replace("\n", " ")


def L(url, label):
    # Percent-encode parentheses/quotes so nested API query strings remain clickable
    # in GitHub Markdown (the exact requested URL stays the same after decoding).
    return f"[{escape(label)}]({quote(url, safe='/:?&=#%-_')})" if url else "—"


def main():
    matches, fixtures, lines = load("matches.json"), load("fixtures.json"), load("lines.json")
    preds, picks, flags = load("predictions.json"), load("picks.json"), load("flagged.json")
    audit, sources, taxa = load("repo_audit.json"), load("sources.json"), load("olbg_taxonomy.json")
    original = json.loads((DATA / "captures/olbg_first_page.json").read_text())
    notes = [f'''# Vantage — 24 October 2026 official-source review and OLBG routing audit

**Session:** `arena/7a6b583e-olbg2` · **Fixed integration branch:** `arena/7a6b583e-olbg2` · **Internal cutoff:** {matches['as_of_utc']}.
**Reader entry point:** [Executive summary](../vantage/index.html) · [Picks & complete prose](../vantage/picks.html) · [All matches](../vantage/matches.html) · [Flagged for Review](../vantage/flagged.html).

## Executive result — strict about what was, and was not, established

| Measure | Count | Meaning |
|---|---:|---|
| OLBG discovery rows | {matches['listings']} | First visible page only: 96 copied from a merged source session + one directly checked Hurling match. No full pagination claim. |
| Official source-matched records | {matches['confirmed']} | Matched participants/event/date, **not** automatically a future bettable market. |
| OLBG-only, unconfirmed | {matches['unknown']} | Official fixture/date/venue/quote fields left null; an official *review target* is linked, never presented as confirmation. |
| Priced future fixtures | {matches['priced']} | Future by >90 minutes at cutoff, both-side numerical league input; 95 own fair outcome lines in four sports. |
| Published picks / fully written previews | {picks['count']} / {preds['count']} | Every row with a selection has a unique >=30-word text and at least two official URLs. |
| High / high with fair **and separate observed** in-band | {picks['high']} / {picks['focused']} | One NHL candidate. Its quoted partner price was in the NHL feed, not on OLBG; it may no longer be offered. |
| Flagged items | {flags['count']} | All unmatched and unpriced listings, 15 per-sport shortfalls and cross-source irregularities. |

**Important limitations.** This is a static research snapshot. It is **not** a live betting feed, an exhaustive OLBG schedule, proof a bet is still available, or a calibrated guarantee. External facts were read from first-hand official pages/APIs except the PDC session and the WTA Osaka draw, where official-site indexed excerpts were used because the direct pages returned a cookie wall/notification shell. Those two categories have no originated selections. Full raw HTTP response bodies were not archived; field-level structured extracts, URLs, dates and the original OLBG extract's hash are retained instead. The exact timestamp of *every* web read was not preserved; league facts were consulted during this 24 October session around the 17:10–18:00 UTC window. The 17:50 cutoff is the deterministic model gate, aligned with the end of the imported OLBG capture, not a claim that all remote pages were refreshed at precisely 17:50.

**Imported discovery provenance:** [source at pinned commit 6926afe](https://github.com/buffedlizard55-lab/OLBG2/blob/6926afe/data/today/olbg_listings.json) · SHA-256 `{original['source_sha256']}`. A separate [Hurling first-page extract](../data/vantage/captures/olbg_hurling_first_page.json) adds OLBG sport id 26 under Gaelic Sports. All other previous repository layers remain distinct and historical.

## 1. Reverse-engineered OLBG URLs and availability boundary

- Hubs use `/betting-tips/{{Sport_Slug}}/{{sport_id}}` ([example, NHL id 13](https://www.olbg.com/betting-tips/Ice_Hockey/13)). The numeric suffix is required; event pages use `/betting-tips/{{Sport}}/{{group}}/{{competition}}/{{event}}/{{id}}?event_id={{N}}`.
- A hub lists **one top-tipped outcome per event**, tip fraction, a rendered display time and event URL. The sport's `Load More Tips` means the captured first page cannot establish all matches or all markets. Inline bookmaker promotions interrupt rows. Tip share (e.g. 3/3 = 100%) is **not** a calibrated probability.
- The [Sharks–Bruins event](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/SJ_Sharks_@_BOS_Bruins/13?event_id=200007) exposed Money Line, Puck Line and Game Totals, but no usable OLBG bookmaker quote. The [Magdeburg–Kriens event](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/SC_Magdeburg_vs_HC_Kriens_Luzern/20?event_id=12136) exposed **only 3-way Money Line** on direct read. A handicap priced by us for that game is theoretical unless actually offered elsewhere.
- Gaelic Sports here groups [Gaelic Football id 25](https://www.olbg.com/betting-tips/Gaelic_Football/25) and [Hurling id 26](https://www.olbg.com/betting-tips/Hurling/26). Golf returned `No tips found`; Rugby League returned only 2027 outright futures; neither is made into a match bet by importing an unrelated official schedule.
- OLBG's publisher-time strings have no universal timezone. NBA [official 1pm ET injury report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_00PM.pdf) differs by one hour from two OLBG NBA rows. The OLBG South Africa–Australia **31 October** display is the last scheduled Test day; [Cricket South Africa](https://cricket.co.za/csa-announces-unmissable-2026-27-home-season-for-the-proteas-men/) starts the third Test on **27 October**. Its two official start clocks also differ, so time stays blank.

### Hub catalogue

| Sport | OLBG id(s) / hub | First page rows | Official matched | Official check target |
|---|---|---:|---:|---|
''']
    for h in taxa["hubs"]:
        hub = L(h["url"], str(h.get("sport_ids") or h["sport_id"]))
        if h.get("subhub_url"):
            hub += " / " + L(h["subhub_url"], "Hurling id 26")
        notes.append(f"| {escape(h['sport'])} | {hub} | {h['listings']} | {h['official_matches']} | {L(h['official_check_target'], 'official target')} |\n")
    notes += [f"""
## 2. Dated row-by-row event verification (OLBG discovery is never proof)

The **official fixture** column stays `—` when no specific sporting-body pairing was found. A link labelled **review target** is an authority to check manually, **not proof** for that row. Selection without 30+ written words is prohibited; the table links to the actual prediction card instead. Rows with no match price show blanks and the reason on `/vantage/matches.html` and in the {flags['count']}-item review queue.

| OLBG sport/event (separate listing URL) | Official fixture | League start (UTC, if explicit or zoned) | Status at cutoff | Written selection | Sporting-body source or NON-CONFIRMING review target |
|---|---|---|---|---|---|
"""]
    for r in matches["matches"]:
        label = f"{r['sport']}: {r['olbg_listing']} (id {r['olbg_event_id']})"
        event = L(r["olbg_event_url"], label)
        fixture = f"{r['official_home']}{' v ' + r['official_away'] if r['official_away'] else ''}" if r["official_confirmed"] else "—"
        start = r["official_start_utc"] or "—"
        selection = (L(f"../vantage/predictions.html#preview-{r['id']}", r["primary_selection"])
                     if r["primary_selection"] else "—")
        src = (L(r["fixture_source_url"], "official fixture") if r["official_confirmed"] else
               L(r["review_target_url"], "review target ONLY — not confirmed"))
        notes.append(f"| {event} | {escape(fixture)} | {escape(start)} | {escape(r['official_status'])} | {selection} | {src} |\n")
    notes += ["""
## 3. Source fact ledger — each published assertion has an authority URL

The table below enumerates the **frozen field-level input claims**, including the NHL 22 October recent-results facts and NBA injury-report facts. Values are not filled from an unrelated match or inferred from tip counts; when the official body did not supply a start, venue, injury status or both teams' numeric form, it was left blank and flagged. These links are manual review starting points; this structural build does not silently assert re-fetches after publication.

| Matched event id | Official field / fact as transcribed | Official source |
|---|---|---|
"""]
    for f in fixtures["fixtures"]:
        for fact in f["facts"]:
            notes.append(f"| {escape(f['id'])} | {escape(fact['claim'])} | {L(fact['url'], fact['url'])} |\n")
    notes += ["""
## 4. Origination, confidence and price-band arithmetic

- Method and all numeric constants are published in [the methodology page](../vantage/methodology.html) and tested against every row by `scripts/vantage_verify.py`. The result is an **independent fair estimate**, with no bookmaker vig. NLP/tipster percentages are not model inputs. All market prices, total cutoffs and handicap margins are our own assumptions and deliberately labelled as such.
- For Boston–San Jose, the [NHL team summary](https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2) shows Boston 11 GP/42 GF/22 GA and San Jose 11 GP/32 GF/36 GA. Our fixed 10-game shrinkage and 1.035 home factor produce 70.434% (fair −238). The [NHL score feed](https://api-web.nhle.com/v1/score/2026-10-24) separately labelled FanDuel (provider 7) at −178 on Boston. The [OLBG event](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/SJ_Sharks_@_BOS_Bruins/13?event_id=200007) shows a moneyline selection but **no numeric OLBG price**. All three contexts are distinct.
- **Sensitivity check, not a confidence guarantee:** keeping the same two teams and changing just the shrinkage denominator from 10 to 8 gives 72.084% (fair −258, outside requested band); changing it to 12 gives 69.043% (fair −223, below high). No goalie/lineup/injury adjustment or out-of-sample calibration was fitted. The high label is fragile and published with its warning.
- An event beginning within 90 minutes of the frozen cutoff is withheld from the picks board. Independent lines are originated for 15 later, officially started-scheduled matches (95 prices); WST `Live Now`, NBA 1–2-game records, NZC reader-local clock, Hurling no official throw-in, and other unsupported markets remain blank. The page's browser-time badge archives highlighted picks when their official UTC start arrives. Static HTML cannot prove a market is open or a quote persists.
- At p≥70% a no-vig fair moneyline is at most about −233; a fair −250 corresponds to 71.43%. This narrow probability overlap is the reason we publish **one** high band candidate, not five invented per sport. See [all reviewed gaps](../vantage/flagged.html).

### All 15 fully written candidate selections (not just the featured one)

| Event | Explicit selection & market | Confidence | Our fair price | Separate observed quote | Official match source |
|---|---|---|---:|---:|---|
"""]
    for p in picks["picks"]:
        notes.append(f"| {escape(p['fixture_id'])} | {L('../vantage/predictions.html#preview-'+p['fixture_id'], p['selection']+' · '+p['market'])} | {p['confidence']} | {p['fair_american']:+} | {p['observed_american'] if p['observed_american'] is not None else '—'} | {L(p['official_url'], 'official match')} |\n")
    notes += ["""
## 5. Existing repository: line-ranged irregularities (not silently edited)

All below refer to existing files at source `main` commit `6926afe` when this session claimed a disjoint directory. Active parallel integration sessions own root HTML, README and CI; edits to those files are **requested in COORDINATION.md** rather than made across scopes here.

| Code | Severity / status | File and lines | Finding | Manual source |
|---|---|---|---|---|
"""]
    for x in audit["findings"]:
        notes.append(f"| {x['code']} | {x['severity']} / {x['status']} | `{escape(x['path'])}` | {escape(x['finding'])} | {L(x['source_url'], 'manual source')} |\n")
    notes += [f"""
## 6. Repeatable checks, publication and handoff

```sh
python3 scripts/vantage_seed.py
python3 scripts/vantage_model.py
python3 scripts/vantage_predictions.py
python3 scripts/vantage_flags.py
python3 scripts/vantage_build.py
python3 scripts/vantage_report.py
python3 scripts/vantage_verify.py
python3 -m unittest discover -s tests -p 'test_vantage_7a6b583e.py' -v
python3 scripts/integration_audit.py
```

All {picks['count']} published selections have one unique ≥30-word analysis, their cited league-page URLs, explicit fair odds and separate observed quotes where any were supplied. **{flags['count']}** non-blocking review items remain open; especially note PDC/WTA indexed-excerpt limitations, date/time conflicts, and missing observed OLBG prices. No claim of five supported daily high predictions in each of the 15 sports is made. A successful CI build proves structural consistency, not a future win.

**Coordination:** only `vantage/**`, `data/vantage/**`, `scripts/vantage_*.py`, `tests/test_vantage_7a6b583e.py`, this file and append-only `COORDINATION.md` are touched. Root navigation belongs to active 24 October sessions. A direct Pages URL works after merge; request a root link from the root owner. PR/merge and Pages deployment evidence are recorded in `COORDINATION.md` when complete.
"""]
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text("".join(notes), encoding="utf-8")
    print(f"vantage_report: {matches['listings']} first-page rows, {sum(len(x['facts']) for x in fixtures['fixtures'])} official fact records, {len(audit['findings'])} repo findings -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
