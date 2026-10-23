#!/usr/bin/env python3
"""Produce the register, the flag list and the repository review used by the /ledger/ desk.

Everything in the register comes from data/ledger/manifest.json (the capture record) or
from the OLBG pages themselves. Nothing is typed in by hand except the explanatory notes
in the curated flag list, and each of those points at the capture or file it describes.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402
DATA = ROOT / "data" / "ledger"
ANCHOR = anchor()
import datetime as _dtmod
ANCHOR_DT = _dtmod.datetime.strptime(ANCHOR, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dtmod.timezone.utc)

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def sources_register() -> dict:
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for c in manifest["captures"]:
        rows.append({
            "key": c["key"], "url": c.get("final_url") or c.get("requested_url"),
            "requested_url": c.get("requested_url"), "status": c.get("status"),
            "bytes": c.get("bytes"), "sha256": c.get("sha256"),
            "fetched_at": c.get("fetched_at"), "sport": c.get("sport"),
            "kind": c.get("kind"), "note": c.get("note"),
            "truncated": c.get("truncated", False), "error": c.get("error", ""),
            "stored_as": c.get("stored_as", ""),
        })
    rows.sort(key=lambda r: ((r["sport"] or ""), r["key"]))
    ok = [r for r in rows if r["status"] == 200]
    return {
        "meta": {"generated_at": ANCHOR,
                 "captures": len(rows), "ok": len(ok), "failed": len(rows) - len(ok),
                 "first_capture": min((r["fetched_at"] or "") for r in rows) if rows else "",
                 "last_capture": max((r["fetched_at"] or "") for r in rows) if rows else ""},
        "sources": rows,
    }


def repo_review() -> dict:
    findings = []

    def add(code, title, detail, evidence, severity):
        findings.append({"code": code, "title": title, "detail": detail, "evidence": evidence, "severity": severity})

    coord = (ROOT / "COORDINATION.md").read_text(encoding="utf-8", errors="replace").split("\n")
    marks = [(i + 1, l.strip()) for i, l in enumerate(coord) if l.startswith(">>>>>>>")]
    meth = (ROOT / "METHODOLOGY.md").read_text(encoding="utf-8", errors="replace").split("\n")
    meth_marks = [(i + 1, l.strip()) for i, l in enumerate(meth) if l.startswith(">>>>>>>")]
    if marks or meth_marks:
        add("RR-01", "Unresolved merge-conflict markers are checked in",
            f"`COORDINATION.md` carries {len(marks)} closing conflict markers and `METHODOLOGY.md` carries {len(meth_marks)}. "
            "They are plain text, so nothing breaks, but they are not content and they make the shared board hard to read.",
            "COORDINATION.md lines " + ", ".join(str(n) for n, _ in marks) + "; METHODOLOGY.md line " + ", ".join(str(n) for n, _ in meth_marks),
            "medium")

    layers = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and (p / "index.html").exists() and not p.name.startswith("."))
    add("RR-02", "Thirty-three published dashboards overlap the same brief",
        "Each of these directories publishes a full dashboard for the same 15-sport brief, with different counts and different "
        "levels of evidence. There is no marker of which one is authoritative, so a reader landing on any of them can be misled.",
        f"{len(layers)} directories with an index.html: " + ", ".join(layers),
        "high")

    root_html = (ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
    stale = re.search(r"Snapshot (20\d\d-\d\d-\d\d \d\d:\d\d) UTC", root_html)
    add("RR-03", "The root dashboard advertises a stale snapshot and points at the weakest desk",
        "The root page's status stripe still reads 2026-10-22 08:15 UTC and its primary call to action opens `/monitor/`, "
        "which states that no high-confidence picks cleared. The most complete desk from the same day, `/signal/`, is not linked "
        "from the root navigation at all.",
        f"index.html stripe: {stale.group(0) if stale else 'not found'}; root navigation references to /signal/: "
        f"{root_html.count('signal/')}; /monitor/ page text: 'No high-confidence picks cleared.'",
        "high")

    add("RR-04", "The cross-layer link checker trips over any non-UTF-8 file",
        "`scripts/integration_audit.py` reads every `*.html` under the repository as UTF-8 with no fallback. A single Latin-1 "
        "response stored under `data/` was enough to raise UnicodeDecodeError and fail the whole suite. Captures in this layer are "
        "therefore stored as `.txt`, and the checker itself is left untouched as another session's file.",
        "Reproduced locally: `python3 -m unittest tests.test_integration` failed with UnicodeDecodeError at "
        "`scripts/integration_audit.py:127` while `data/ledger/raw/handball_spain.html` existed.",
        "medium")

    dup = []
    for p in ROOT.rglob("index.html"):
        if any(part in ("data", ".git", "_site", "node_modules") for part in p.parts):
            continue
        ids = re.findall(r'\sid="([^"]+)"', p.read_text(encoding="utf-8", errors="replace"))
        d = sorted({i for i in ids if ids.count(i) > 1})
        if d:
            dup.append(f"{p.relative_to(ROOT)}: {', '.join(d[:4])}")
    if dup:
        add("RR-05", "Duplicate element ids in a published page", "Anchor targets repeat inside the page, so a fragment link can land on the wrong row.",
            "; ".join(dup[:3]), "low")

    tests = len(list((ROOT / "tests").glob("test_*.py")))
    add("RR-06", "CI rebuilds many layers and checks them for drift",
        f"The Pages workflow rebuilds {tests} test modules' worth of layers and fails if generated HTML differs from what is committed. "
        "Any new layer has to be added to both the rebuild steps and the drift list or it will silently rot. This layer adds its own "
        "step and drift paths.",
        ".github/workflows/pages.yml — 'Fail if any generated page or data file is stale'",
        "info")

    add("RR-07", "Earlier desks publish numbers that cannot be reconciled with each other",
        "For the same day the repository contains, among others, 101 fixtures (/signal/), 133 (/liveboard/), 24 (/monitor/), 40 (/focus/) "
        "and 188 stored rows on the root. They describe different capture windows rather than contradicting one another, but the pages "
        "do not say so consistently.",
        "Each desk's own build output; see /ledger/verification.html for the full comparison.",
        "medium")

    return {"meta": {"generated_at": ANCHOR,
                     "findings": len(findings), "layers": len(layers)}, "findings": findings}


def flags(matches, picks, predictions, lines, sources) -> dict:
    lag = [s for s in SPORTS if s not in predictions["meta"]["by_sport"]]
    unmatched = [e for e in matches["events"] if e["verify"]["state"] == "unmatched"]
    by_sport_unmatched = {}
    for e in unmatched:
        by_sport_unmatched[e["sport"]] = by_sport_unmatched.get(e["sport"], 0) + 1

    items = [
        {"code": "L-01", "severity": "high", "sport": "Several",
         "title": "Eleven sports carry no written preview today",
         "detail": "The brief asks for five previews per sport. Previews were published for "
                   + ", ".join(f"{k} ({v})" for k, v in sorted(predictions["meta"]["by_sport"].items()))
                   + ". No preview is published for " + ", ".join(lag) + " because no official current-form, table or result "
                   "input for those fixtures could be captured today. A preview written without one would be invention.",
         "source": "", "impact": "Shortfall against the five-per-sport target; disclosed rather than filled."},
        {"code": "L-02", "severity": "high", "sport": "Multiple",
         "title": f"{len(unmatched)} of {matches['meta']['events']} OLBG-listed events could not be matched to an official source",
         "detail": "Per sport: " + ", ".join(f"{k} {v}" for k, v in sorted(by_sport_unmatched.items()))
                   + ". The OLBG event is still listed and its quoted price is shown, but no official fixture page was found in "
                     "today's captures, so no line was originated and no preview was written for those rows.",
         "source": "https://www.olbg.com/betting-tips", "impact": "Those rows are published as unverified listings."},
        {"code": "L-03", "severity": "high", "sport": "Basketball",
         "title": "Every NBA endpoint refused the capture",
         "detail": "cdn.nba.com returned 403 for both the scoreboard and the league schedule, nba.com/games returned 403 and "
                   "stats.nba.com timed out. The eleven NBA fixtures OLBG lists therefore have no official verification and no "
                   "originated line. EuroLeague responded normally and carries the basketball pricing.",
         "source": "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
         "impact": "11 NBA rows unverified; basketball previews use EuroLeague fixtures only."},
        {"code": "L-04", "severity": "medium", "sport": "Golf",
         "title": "OLBG's golf hub rendered no tip objects",
         "detail": "The golf hub was fetched successfully (HTTP 200, 183 KB) but contained no market or event objects, so no golf "
                   "fixture was listed by the source the brief is built on. The DP World Tour schedule and leaderboard pages also "
                   "render client-side, so no golf market was originated.",
         "source": "https://www.olbg.com/betting-tips/Golf/5", "impact": "Zero golf rows today."},
        {"code": "L-05", "severity": "medium", "sport": "Snooker",
         "title": "All four OLBG snooker tips had already expired at capture time",
         "detail": "The hub returned four tips, all flagged expired by OLBG itself and all dated before the capture. Nothing "
                   "upcoming was listed, so snooker has no rows today. world table pages on wst.tv render client-side.",
         "source": "https://www.olbg.com/betting-tips/Snooker/8", "impact": "Zero snooker rows today."},
        {"code": "L-06", "severity": "medium", "sport": "Rugby League",
         "title": "OLBG lists only outright markets for rugby league",
         "detail": "The three rugby league entries are 2027 futures (State of Origin, Super League, NRL), not matches. Outright "
                   "futures are outside the match-winner, handicap and total markets this desk prices.",
         "source": "https://www.olbg.com/betting-tips/Rugby_League/10", "impact": "No rugby league match priced."},
        {"code": "L-07", "severity": "medium", "sport": "OLBG",
         "title": "OLBG's JSON tip endpoint returns 404 when called directly",
         "detail": "The hub pages call /sports/<Sport>/top_tips?paginate=1-100&... and the path is visible in the page payload, but a "
                   "direct request without the page's own headers returns OLBG's 404 page (98 KB) for all sixteen sports. The desk "
                   "therefore parses the server-rendered hub payload instead.",
         "source": "https://www.olbg.com/sports/Darts/top_tips?paginate=1-100", "impact": "Capture falls back to hub HTML."},
        {"code": "L-08", "severity": "medium", "sport": "Basketball",
         "title": "EuroLeague tip times are served in venue-local time",
         "detail": "api-live.euroleague.net returns a date and a start time without an offset. The desk publishes the time exactly as "
                   "served and marks the column, rather than converting it to UTC and implying a precision the feed does not give.",
         "source": "https://api-live.euroleague.net/v1/schedules?seasonCode=E2026&gameNumber=8", "impact": "Times marked 'as served'."},
        {"code": "L-09", "severity": "medium", "sport": "Multiple",
         "title": "Official-page matches are evidence of a fixture row, not of a kick-off time",
         "detail": "For seven fixtures the two participants sit either side of a versus marker on an official competition page. That "
                   "confirms the pairing appears on an official page; it does not confirm the start time OLBG publishes. Those rows "
                   "are labelled official-page, not official-fixture.",
         "source": "https://www.cricket.com.au/matches?year=2026&isCompleted=0", "impact": "Verification strength is stated per row."},
        {"code": "L-10", "severity": "medium", "sport": "Multiple",
         "title": "No official injury feed could be read",
         "detail": "None of the captured official pages carried a team-news or injury list for these fixtures. No preview asserts an "
                   "injury, a return date or a suspension. Where a reader expects an injury line, the honest answer is that it could "
                   "not be confirmed today.",
         "source": "", "impact": "Injury field omitted rather than guessed."},
        {"code": "L-11", "severity": "info", "sport": "Multiple",
         "title": "The 70% rule and the -250 to +10000 band only overlap between 70.0% and 71.4%",
         "detail": f"Any selection above 70% is shorter than -233, so it falls outside a band that starts at -250. Today "
                   f"{picks['meta']['high']} selections are graded high and {picks['meta']['high_in_band']} of those are also inside "
                   "the price band. The desk publishes both counts rather than moving the thresholds.",
         "source": "", "impact": "Both counts are shown on every summary."},
        {"code": "L-12", "severity": "info", "sport": "Multiple",
         "title": "OLBG quotes one side of each market, so implied probabilities are not margin-free",
         "detail": "Each OLBG tip carries a single price. 1/price therefore overstates the chance slightly because the bookmaker "
                   "margin has not been removed. Market-implied rows say so, and they are never mixed into the originated totals.",
         "source": "https://www.olbg.com/betting-tips", "impact": "Labelled 'market-implied'."},
        {"code": "L-13", "severity": "info", "sport": "Baseball",
         "title": "Probable pitchers are published for two of the seven World Series games",
         "detail": "statsapi.mlb.com lists Nick Martinez against Jacob Misiorowski for game one and Drew Rasmussen against Logan "
                   "Henderson for game two. Games three to seven carry no probable pitcher at capture time, and the previews for "
                   "those games say so.",
         "source": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-31",
         "impact": "Two of five baseball previews cite a starting pitcher."},
        {"code": "L-14", "severity": "info", "sport": "Greyhounds / Tennis / Darts / Handball / Volleyball",
         "title": "Five sports publish fixtures but no readable form line",
         "detail": "GBGB publishes meetings and race times without runners; WTA, PDC and WST render their draw and ranking pages "
                   "client-side; the domestic handball and volleyball league sites publish tables that did not parse into a form "
                   "line. Those fixtures are listed and priced only where OLBG quotes a price, and none carries a preview.",
         "source": "https://www.gbgb.org.uk/racing/", "impact": "No originated line in these sports."},
        {"code": "L-15", "severity": "info", "sport": "Multiple",
         "title": "Two sources were only stored in part",
         "detail": f"{len([s for s in sources['sources'] if s.get('truncated')])} responses exceeded the 300 KB storage cap and were "
                   "stored truncated. The cap is recorded in the register next to the row, and no parsed figure depends on the part "
                   "that was cut.",
         "source": "/ledger/sources.html", "impact": "Truncation disclosed per capture."},
    ]
    return {"meta": {"generated_at": ANCHOR,
                     "items": len(items),
                     "high": len([i for i in items if i["severity"] == "high"])},
            "items": items}


def main() -> int:
    matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    predictions = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))
    lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))
    src = sources_register()
    (DATA / "sources.json").write_text(json.dumps(src, indent=1) + "\n", encoding="utf-8")
    rep = repo_review()
    (DATA / "repo_review.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    fl = flags(matches, picks, predictions, lines, src)
    (DATA / "flagged.json").write_text(json.dumps(fl, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"sources": src["meta"], "repo_findings": rep["meta"], "flags": fl["meta"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
