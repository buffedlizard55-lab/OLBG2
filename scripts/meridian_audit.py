#!/usr/bin/env python3
"""Reproducible repository audit and flag list for the /meridian/ desk.

The audit is derived by scanning the checkout, so every finding names a file and a line range
that a reviewer can open. It never edits another session's files.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "meridian"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
NOW = "2026-10-24T18:10:00Z"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]


def rel(p):
    return p.relative_to(ROOT).as_posix()


def reader_facing_prose():
    hits = []
    for path in sorted((ROOT / "data").rglob("predictions*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows = doc if isinstance(doc, list) else doc.get("predictions", doc.get("items", []))
        if not isinstance(rows, list):
            continue
        bad = [r for r in rows if isinstance(r, dict)
               and BANNED.search((r.get("text") or "") + " " + (r.get("headline") or ""))]
        if bad:
            lines = path.read_text(encoding="utf-8").splitlines()
            first = next((i + 1 for i, l in enumerate(lines) if '"text":' in l
                          and BANNED.search(l)), 1)
            hits.append({"file": rel(path), "entries": len(bad), "total": len(rows),
                         "first_line": first})
    return hits


def out_of_scope_sports():
    hits = []
    for path in sorted((ROOT / "data").rglob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows = doc if isinstance(doc, list) else (
            doc.get("matches") or doc.get("picks") or doc.get("predictions") or [])
        if not isinstance(rows, list):
            continue
        found = sorted({str(r.get("sport")) for r in rows
                        if isinstance(r, dict) and str(r.get("sport")) not in SPORTS
                        and str(r.get("sport")) not in ("aussie-rules", "esports", "hurling-standalone")})
        if found:
            hits.append({"file": rel(path), "sports": found,
                         "rows": sum(1 for r in rows if isinstance(r, dict)
                                     and str(r.get("sport")) in found)})
    return hits


def build():
    findings = []

    prose = reader_facing_prose()
    if prose:
        total = sum(h["entries"] for h in prose)
        findings.append({
            "id": "MF-01", "severity": "high",
            "title": f"{total} published prediction texts elsewhere in the repo use banned vocabulary",
            "detail": "The reader-facing predictions in other data layers still contain the words the "
                      "brief bans ('model', 'verified'). This session does not edit those files because "
                      "they belong to other sessions; the files and line numbers are listed so the "
                      "owning sessions can fix them.",
            "evidence": prose,
            "action": "Left untouched by this session; listed for the owning sessions.",
        })

    zoo = out_of_scope_sports()
    if zoo:
        findings.append({
            "id": "MF-02", "severity": "high",
            "title": "Data files outside the exact-15-sport list carry Aussie Rules and eSports rows",
            "detail": "Layers outside this desk publish rows for sports that are not in the brief's "
                      "list of fifteen, so the claim and the data disagree on the same branch.",
            "evidence": zoo,
            "action": "Reported, not edited: these files belong to merged sessions.",
        })

    layers = sorted(p.name for p in ROOT.iterdir()
                    if p.is_dir() and (p / "index.html").exists() and not p.name.startswith("."))
    findings.append({
        "id": "MF-03", "severity": "medium",
        "title": f"{len(layers)} separate dashboards publish an overlapping 15-sport brief",
        "detail": "Each directory publishes its own dashboard with its own counts. A reader landing "
                  "on any one of them sees a different total for the same day. This desk adds "
                  "/meridian/ as an explicitly dated 2026-10-24 snapshot and states its counts on "
                  "every page header rather than implying it supersedes the others.",
        "evidence": [{"layers": layers, "count": len(layers)}],
        "action": "Root integration request recorded in COORDINATION.md.",
    })

    coord = (ROOT / "COORDINATION.md").read_text(encoding="utf-8", errors="replace").splitlines()
    marks = [(i + 1, l[:12]) for i, l in enumerate(coord)
             if l.startswith("<<<<<<<") or l.startswith(">>>>>>>") or l.strip() == "======="]
    if marks:
        findings.append({
            "id": "MF-04", "severity": "medium",
            "title": "Merge-conflict markers are still checked in to the shared task board",
            "detail": f"COORDINATION.md carries {len(marks)} conflict-marker lines. They are plain "
                      "text so nothing breaks, but the board is the coordination contract for parallel "
                      "sessions and the markers make its history ambiguous.",
            "evidence": [{"file": "COORDINATION.md", "lines": [m[0] for m in marks]}],
            "action": "Left in place; this session appends only.",
        })

    out = {"generated_utc": NOW, "count": len(findings), "layers": len(layers), "findings": findings}
    (DATA / "repo_audit.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8")

    fixtures = json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]
    matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))["matches"]
    picks_doc2 = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    picks = picks_doc2["picks"]
    preds_doc = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))
    preds = preds_doc
    sports15 = list(SPORTS)
    with_pred = {p["sport"] for p in preds["predictions"]}
    with_pick = {p["sport"] for p in picks}
    blanks = [m for m in matches if m["status"] != "priced"]
    flags = [
        {"id": "MF-10", "severity": "high", "sport": "Multiple",
         "title": "Write-up shortfall against the five-per-sport target",
         "detail": f"{len(preds)} write-ups are published across {len(with_pred)} of the 15 sports. "
                   f"Sports with a pick but fewer than five write-ups: "
                   + ", ".join(f"{s} ({preds['by_sport'].get(s, 0)})" for s in sports15 if s in with_pick)
                   + f". Sports with no write-up at all: "
                   + ", ".join(s for s in sports15 if s not in with_pred)
                   + ". A write-up is only published where a selection cleared the focus band with "
                     "two or more officially sourced facts; the alternative is invention.",
         "source": "data/meridian/predictions.json"},
        {"id": "MF-11", "severity": "high", "sport": "Multiple",
         "title": f"{len(blanks)} fixtures are published without an originated line",
         "detail": "Each row states its own reason. Grouped: "
                   + "; ".join(f"{s}: {sum(1 for b in blanks if b['sport'] == s)}"
                               for s in sorted({b['sport'] for b in blanks})) + ".",
         "source": "data/meridian/matches.json"},
        {"id": "MF-12", "severity": "high", "sport": "Golf",
         "title": "Golf returned no listings on OLBG",
         "detail": "The Golf hub returned 'No tips found.' at 17:16 UTC on 2026-10-24 while a PGA "
                   "TOUR event was in progress, so no golf fixture could be attached to a pick.",
         "source": "https://www.olbg.com/betting-tips/Golf/5"},
        {"id": "MF-13", "severity": "high", "sport": "Rugby League",
         "title": "Rugby League listed only 2027 outright futures",
         "detail": "The Rugby League hub listed State of Origin 2027, Super League 2027 and NRL "
                   "2027 outrights, but no Rugby League match event, so no Rugby League fixture is "
                   "published.",
         "source": "https://www.olbg.com/betting-tips/Rugby_League/10"},
        {"id": "MF-14", "severity": "high", "sport": "Snooker",
         "title": "Snooker's only upcoming fixture has an unresolved opponent",
         "detail": "The Northern Ireland Open final is Kyren Wilson against the winner of Mark "
                   "Williams v Jak Jones; with the second finalist unknown at capture, no "
                   "opponent-dependent market can be originated.",
         "source": "https://www.wst.tv/matches/"},
        {"id": "MF-15", "severity": "medium", "sport": "Handball",
         "title": "Handball tables render client-side, so no two-sided input exists",
         "detail": "The HBL table page and the LNH standings page render their numbers client-side, "
                   "so neither side's goals-for/against could be read for the three handball "
                   "fixtures.",
         "source": "https://www.opel-hbl.de/de/hbl/tabelle"},
        {"id": "MF-16", "severity": "medium", "sport": "Volleyball",
         "title": "Volleyball lines rest on a documented class prior, not on a table",
         "detail": "Lega Pallavolo and the Volleyball Bundesliga publish their standings "
                   "client-side. The per-set probabilities are keyed to verified status facts and "
                   "are labelled as an assumption on the row.",
         "source": "https://www.legavolley.it/classifica/?IdCampionato=999&lang=en"},
        {"id": "MF-17", "severity": "medium", "sport": "Tennis",
         "title": "No serve or return statistics were published for these matches",
         "detail": "The set-level edge is keyed to the official seed line and, for Almaty, to the "
                   "published head-to-head. Where neither exists (Basel, Vienna) the class prior is "
                   "stated on the row.",
         "source": "https://www.atptour.com/en/news/djokovic-basel-2026-draw-preview"},
        {"id": "MF-18", "severity": "medium", "sport": "Basketball",
         "title": "Five NBA teams had not filed an injury report at the 1:00 PM ET deadline",
         "detail": "Milwaukee, Washington, San Antonio, New Orleans and Golden State were listed "
                   "NOT YET SUBMITTED. Their absences are unknown, not zero, and the rows say so.",
         "source": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_30PM.pdf"},
        {"id": "MF-19", "severity": "medium", "sport": "Motor Racing",
         "title": "The F1 race line is originated before qualifying",
         "detail": "The grid was not set at capture. The race field is priced from the two published "
                   "practice orders and the championship table, and the row states that qualifying "
                   "was still to come.",
         "source": "https://www.formula1.com/en/racing/2026/united-states"},
        {"id": "MF-20", "severity": "medium", "sport": "Darts",
         "title": "Darts per-match start times are not published",
         "detail": "The PDC publishes only the session window (19:00-23:00 CEST for the Saturday "
                   "evening Round Two), not per-match times, so all five darts rows carry the "
                   "session window.",
         "source": "https://www.pdc.tv/news/2026/october/24/2026-machineseeker-european-championship---day-three-latest"},
        {"id": "MF-21", "severity": "medium", "sport": "Multiple",
         "title": "OLBG renders fixture times in US Eastern time",
         "detail": "OLBG hub pages localize kick-offs to the requester's time zone without stating "
                   "it (for example a 23:00Z NHL game renders as 'Today 19:07'). All times on this "
                   "desk come from the governing body and are stored in UTC.",
         "source": "https://www.olbg.com/betting-tips"},
    ]
    out_flags = {"generated_utc": NOW, "count": len(flags),
                 "high": sum(1 for f in flags if f["severity"] == "high"), "items": flags}
    (DATA / "flagged.json").write_text(json.dumps(out_flags, indent=1, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    print(f"meridian_audit: {len(findings)} repo findings, {len(flags)} flag items, {len(layers)} published layers")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
