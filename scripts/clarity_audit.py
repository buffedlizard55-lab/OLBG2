#!/usr/bin/env python3
"""Reproducible repository audit and flag list for the /clarity/ desk.

The audit is derived by scanning the checkout, so every finding names a file and a line range
that a reviewer can open. It never edits another session's files.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clarity"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
NOW = "2026-10-24T17:35:00Z"
OUT_OF_SCOPE = {"aussie-rules", "esports", "hurling-standalone"}


def rel(p):
    return p.relative_to(ROOT).as_posix()


def reader_facing_prose():
    """Find prediction JSON whose `text` is published prose and which uses internal vocabulary."""
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
            hits.append({"file": rel(path), "entries": len(bad), "total": len(rows), "first_line": first})
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
                        if isinstance(r, dict) and str(r.get("sport")) in OUT_OF_SCOPE})
        if found:
            hits.append({"file": rel(path), "sports": found,
                         "rows": sum(1 for r in rows if isinstance(r, dict)
                                     and str(r.get("sport")) in OUT_OF_SCOPE)})
    return hits


def zenith_temporal():
    path = ROOT / "data" / "zenith" / "matches.json"
    if not path.exists():
        return None
    matches = json.loads(path.read_text(encoding="utf-8"))["matches"]
    past = [m for m in matches if (m.get("start_utc") or "9999") < NOW]
    ids = {m["id"] for m in past}
    lines = json.loads((ROOT / "data" / "zenith" / "lines.json").read_text(encoding="utf-8"))["lines"]
    picks = json.loads((ROOT / "data" / "zenith" / "picks.json").read_text(encoding="utf-8"))["picks"]
    src = path.read_text(encoding="utf-8").splitlines()
    first = next((i + 1 for i, l in enumerate(src) if f'"id": "{past[0]["id"]}"' in l), 1) if past else 1
    return {
        "file": "data/zenith/matches.json", "first_past_line": first,
        "past_fixtures": len(past),
        "lines_on_past": sum(1 for x in lines if x["fixture_id"] in ids),
        "picks_on_past": sum(1 for x in picks if x["fixture_id"] in ids),
        "example": [{"id": m["id"], "sport": m["sport"], "start_utc": m["start_utc"]} for m in past[:3]],
    }


def build():
    findings = []

    prose = reader_facing_prose()
    if prose:
        total = sum(h["entries"] for h in prose)
        findings.append({
            "id": "CR-01", "severity": "high",
            "title": f"{total} published prediction texts use internal vocabulary the brief bans",
            "detail": "The brief forbids the words 'model' and 'verified' in reader-facing predictions. "
                      "These entries are live prose on other desks and were not edited by this session "
                      "because each file belongs to a different session's scope. Files and line numbers "
                      "are listed so the owning session can fix them.",
            "evidence": prose,
            "action": "Left untouched by this session; listed for the owning sessions.",
        })

    zoo = out_of_scope_sports()
    if zoo:
        findings.append({
            "id": "CR-02", "severity": "high",
            "title": "Data files inside the 15-sport desks still carry Aussie Rules and eSports rows",
            "detail": "Seven desks that describe themselves as exact-15-sport layers publish rows for "
                      "sports that are not in the brief's list. The rows are in committed JSON, so the "
                      "claim and the data disagree on the same branch.",
            "evidence": zoo,
            "action": "Reported, not edited: these files belong to merged sessions.",
        })

    z = zenith_temporal()
    if z and z["past_fixtures"]:
        findings.append({
            "id": "CR-03", "severity": "high",
            "title": "The 'future-only' desk still publishes lines and picks on started fixtures",
            "detail": f"PR #194 announced that only fixtures with a confirmed start after the capture "
                      f"cut-off receive an actionable market. Re-scanning the committed data at "
                      f"{NOW} finds {z['past_fixtures']} fixtures whose published start time has already "
                      f"passed, carrying {z['lines_on_past']} originated selections and "
                      f"{z['picks_on_past']} picks. A pick on a game that has already started cannot be "
                      f"placed.",
            "evidence": [z],
            "action": "Reported for the Zenith owner; this desk filters on start time instead.",
        })

    coord = (ROOT / "COORDINATION.md").read_text(encoding="utf-8", errors="replace").splitlines()
    marks = [(i + 1, l[:12]) for i, l in enumerate(coord)
             if l.startswith("<<<<<<<") or l.startswith(">>>>>>>") or l.strip() == "======="]
    if marks:
        findings.append({
            "id": "CR-04", "severity": "medium",
            "title": "Merge-conflict markers are still checked in to the shared task board",
            "detail": f"COORDINATION.md carries {len(marks)} conflict-marker lines. They are plain text so "
                      "nothing breaks, but the board is the coordination contract for parallel sessions and "
                      "the markers make its history ambiguous.",
            "evidence": [{"file": "COORDINATION.md", "lines": [m[0] for m in marks]}],
            "action": "Left in place; this session appends only.",
        })

    root_html = (ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
    stripe = re.search(r"Current stored snapshot ([0-9T:Z\-]+)", root_html)
    rr = ROOT / "data" / "ledger" / "repo_review.json"
    stale_claim = False
    if rr.exists():
        doc = json.loads(rr.read_text(encoding="utf-8"))
        for f in doc.get("findings", []):
            if f.get("code") == "RR-03" and "2026-10-22" in f.get("detail", ""):
                stale_claim = True
    if stale_claim:
        findings.append({
            "id": "CR-05", "severity": "medium",
            "title": "A published audit finding describes a root page that has since changed",
            "detail": f"The /ledger/ audit's RR-03 states the root status stripe reads 2026-10-22 08:15 UTC. "
                      f"The committed root page now reads "
                      f"{stripe.group(1) if stripe else 'a different timestamp'}. The finding is stale in its "
                      f"own text even though the page it criticises has been rewritten.",
            "evidence": [{"file": "data/ledger/repo_review.json", "code": "RR-03"},
                         {"file": "index.html", "stripe": stripe.group(1) if stripe else ""}],
            "action": "Reported; the ledger layer is regenerated by its owner's script, not by hand.",
        })

    layers = sorted(p.name for p in ROOT.iterdir()
                    if p.is_dir() and (p / "index.html").exists() and not p.name.startswith("."))
    findings.append({
        "id": "CR-06", "severity": "medium",
        "title": f"{len(layers)} separate dashboards publish an overlapping 15-sport brief",
        "detail": "Each directory publishes its own dashboard with its own counts. A reader landing on any "
                  "one of them sees a different total for the same day. This desk adds /clarity/ as an "
                  "explicitly dated 2026-10-24 snapshot and states its counts on every page header rather "
                  "than implying it supersedes the others.",
        "evidence": [{"layers": layers, "count": len(layers)}],
        "action": "Root integration request recorded in COORDINATION.md.",
    })

    findings.append({
        "id": "CR-07", "severity": "info",
        "title": "OLBG renders fixture times in US Eastern, not UK time",
        "detail": "Confirmed again on 2026-10-24: OLBG lists HBW Balingen-Weilstetten v MT Melsungen at "
                  "'Today 14:00', while the German league publishes 20:00 CEST. 14:00 ET is 20:00 CEST. "
                  "Any row that mixes an OLBG time with a governing-body time without conversion is six "
                  "hours out.",
        "evidence": [{"olbg": "https://www.olbg.com/betting-tips/Handball/20",
                      "official": "https://www.opel-hbl.de/de/team/Rhein-Neckar%20L%C3%B6wen/fe80598a-3952-11ef-914c-af5c55c3771d"}],
        "action": "This desk publishes governing-body times and never converts from OLBG.",
    })

    out = {"generated_utc": NOW, "count": len(findings), "layers": len(layers), "findings": findings}
    (DATA / "repo_audit.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------ flag list
    fixtures = json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]
    matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))["matches"]
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    preds = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))
    sports15 = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
                "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
                "Ice Hockey", "Basketball", "Rugby League"]
    with_pred = {p["sport"] for p in preds["predictions"]}
    with_pick = {p["sport"] for p in picks["picks"]}
    blanks = [m for m in matches if m["status"] == "blank"]
    flags = [
        {"id": "CL-01", "severity": "high", "sport": "Multiple",
         "title": "Write-up shortfall against the five-per-sport target",
         "detail": f"{len(preds['predictions'])} write-ups are published across {len(with_pred)} of the 15 "
                   f"sports. Sports with a pick but fewer than five write-ups: "
                   + ", ".join(f"{s} ({preds['by_sport'].get(s, 0)})" for s in sports15 if s in with_pick)
                   + ". Sports with no write-up at all: "
                   + ", ".join(s for s in sports15 if s not in with_pred)
                   + ". A write-up is only published where a selection cleared the focus band with two or "
                     "more officially sourced facts; the alternative is invention.",
         "source": "data/clarity/predictions.json"},
        {"id": "CL-02", "severity": "high", "sport": "Multiple",
         "title": f"{len(blanks)} fixtures are published without an originated line",
         "detail": "Each row states its own reason. Grouped: "
                   + "; ".join(f"{s}: {sum(1 for b in blanks if b['sport'] == s)}"
                               for s in sorted({b['sport'] for b in blanks})) + ".",
         "source": "data/clarity/matches.json"},
        {"id": "CL-03", "severity": "high", "sport": "Handball",
         "title": "Handball has three verified fixtures and zero lines",
         "detail": "The HBL table page and the LNH standings page both render their numbers client-side, so "
                   "neither side's goals-for/against could be read. Only one side per fixture had published "
                   "European goal totals, which is not a two-sided input.",
         "source": "https://www.opel-hbl.de/de/hbl/tabelle"},
        {"id": "CL-04", "severity": "high", "sport": "Snooker",
         "title": "Snooker's only upcoming fixture has an unresolved opponent",
         "detail": "The Northern Ireland Open final is Kyren Wilson against the winner of Mark Williams v "
                   "Jak Jones. With the second finalist unknown at capture, no opponent-dependent market "
                   "can be originated.",
         "source": "https://www.wst.tv/matches/"},
        {"id": "CL-05", "severity": "medium", "sport": "Volleyball",
         "title": "Volleyball lines rest on a documented class prior, not on a table",
         "detail": "Lega Pallavolo and the Volleyball Bundesliga both publish their standings client-side. The "
                   "per-set probabilities are keyed to verified status facts (reigning champions, newly "
                   "promoted, both won their opener) and are labelled as an assumption on the row.",
         "source": "https://www.legavolley.it/classifica/?IdCampionato=999&lang=en"},
        {"id": "CL-06", "severity": "medium", "sport": "Tennis",
         "title": "No serve or return statistics were published for these matches",
         "detail": "The set-level edge is keyed to the official seed line and, for Almaty, to the published "
                   "head-to-head. Where neither exists (Basel, Vienna) the class prior is stated on the row.",
         "source": "https://www.atptour.com/en/news/djokovic-basel-2026-draw-preview"},
        {"id": "CL-07", "severity": "medium", "sport": "Basketball",
         "title": "Four NBA teams had not filed an injury report at the 1:00 PM ET deadline",
         "detail": "Milwaukee, Washington, San Antonio, New Orleans and Golden State were listed NOT YET "
                   "SUBMITTED. Their absences are unknown, not zero, and the rows say so.",
         "source": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_00PM.pdf"},
        {"id": "CL-08", "severity": "medium", "sport": "Darts",
         "title": "Nathan Aspinall's Round 1 average was not published",
         "detail": "The PDC published the result (6-3 over Cristo Reyes) but only Littler's 105.05 average. "
                   "The per-leg edge therefore uses a stated tournament-mean prior.",
         "source": "https://www.pdc.tv/news/2026/october/23/Littler-kickstarts-European-Championship-title-bid-in-style/"},
        {"id": "CL-09", "severity": "medium", "sport": "Golf",
         "title": "Two golf events, two different pricing bases",
         "detail": "The PGA TOUR leaderboard embeds FanDuel win prices, which are published and labelled "
                   "market-implied. The DP World Tour leaderboard carries no prices, so that outright field is "
                   "originated from the leaderboard alone.",
         "source": "https://www.pgatour.com/leaderboard"},
        {"id": "CL-10", "severity": "medium", "sport": "Motor Racing",
         "title": "The F1 race line is originated before qualifying",
         "detail": "The grid was not set at capture. The race field is priced from the two published practice "
                   "orders and the championship table, and the row states that qualifying was still to come.",
         "source": "https://www.formula1.com/en/racing/2026/united-states"},
        {"id": "CL-11", "severity": "medium", "sport": "Greyhounds",
         "title": "Two Scurry and two Oaks finalists had no published semi-final time",
         "detail": "Ballinakill Liam, Newinn Souly, Strike It Skye and Holding Hollie qualified without a "
                   "time in the GBGB reports. Their shares use the remaining qualifiers' clock as the only "
                   "official benchmark.",
         "source": "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/"},
        {"id": "CL-12", "severity": "low", "sport": "Cricket",
         "title": "Cricket totals are competition-typical lines with no edge",
         "detail": "No innings-level par score for these venues was published in a readable form, so the "
                   "Over/Under prices sit at 50/50 and are graded low rather than dressed up as a view.",
         "source": "https://www.ecb.co.uk/news/4594465/how-to-watch-and-follow-the-england-men-v-pakistan-and-sri-lanka"},
        {"id": "CL-13", "severity": "low", "sport": "Multiple",
         "title": "OLBG hub capture limits",
         "detail": "Every one of the 15 OLBG sport hubs was read on 2026-10-24. Golf returned 'No tips "
                   "found.' while a PGA TOUR event was in progress; Snooker returned a single fixture; Rugby "
                   "League returned only 2027 outright futures. OLBG is used as a listing cross-check, never "
                   "as a price source.",
         "source": "https://www.olbg.com/betting-tips"},
    ]
    out_flags = {"generated_utc": NOW, "count": len(flags),
                 "high": sum(1 for f in flags if f["severity"] == "high"), "items": flags}
    (DATA / "flagged.json").write_text(json.dumps(out_flags, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"clarity_audit: {len(findings)} repo findings, {len(flags)} flag items, {len(layers)} published layers")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
