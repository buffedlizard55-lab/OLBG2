#!/usr/bin/env python3
"""Executive desk — structural verification of the data and the built site."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "executive"
SITE = ROOT / "executive"
SPORTS = 15
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
PAGES = ["index.html", "matches.html", "lines.html", "picks.html", "predictions.html",
         "sources.html", "methodology.html", "flagged.html"]


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def main() -> int:
    findings: list[dict] = []
    sources = {s["key"]: s for s in load("sources")["sources"]}
    fixtures = load("fixtures")["fixtures"]
    lines = load("lines")["lines"]
    picks = load("picks")["picks"]
    preds = load("predictions")["predictions"]
    flags = load("flagged")["items"]

    sports = {m["sport"] for m in fixtures}
    if len(sports) < SPORTS - 1:
        findings.append({"severity": "warn", "title": "Sport coverage",
                         "detail": f"Only {len(sports)} sports carry priced fixtures; Rugby League has no live 24 Oct match and is documented on its category page."})

    for m in fixtures:
        urls = [sources[k].get("url", "") for k in m["source_keys"] if k in sources]
        if not any(str(u).startswith("https://") for u in urls):
            findings.append({"severity": "error", "title": "Fixture without source",
                             "detail": f"{m['id']} has no official source URL."})
        if ("unverified" in m["home_strength_basis"].lower()
                and "unverified" in m["away_strength_basis"].lower()):
            if not m.get("note"):
                findings.append({"severity": "warn", "title": "Unverified input not flagged",
                                 "detail": f"{m['id']} uses a default strength input without a note."})

    # fair-price consistency
    for r in lines:
        implied = 1.0 / r["fair_decimal"]
        if abs(implied - r["fair_probability"]) > 0.02:
            findings.append({"severity": "error", "title": "Fair price inconsistency",
                             "detail": f"{r['fixture_id']}: decimal {r['fair_decimal']} implies {implied:.4f} but probability is {r['fair_probability']:.4f}."})

    # preview quality
    texts = {}
    for p in preds:
        t = p["text"].strip()
        texts.setdefault(t.lower(), []).append(p["id"])
        if BANNED.search(t):
            findings.append({"severity": "error", "title": "Prohibited word in preview",
                             "detail": f"{p['id']} preview contains a prohibited word."})
        if p["confidence"] == "high" and len(t.split()) < 30:
            findings.append({"severity": "error", "title": "Short high-conviction preview",
                             "detail": f"{p['id']} high-conviction preview is under 30 words."})
    for t, ids in texts.items():
        if len(ids) > 1:
            findings.append({"severity": "error", "title": "Duplicate preview",
                             "detail": f"Preview text shared by {ids}."})

    # band bookkeeping
    for p in picks:
        if not p["in_band"] and -250 <= p["fair_odds"] <= 10000:
            findings.append({"severity": "error", "title": "Band flag mismatch",
                             "detail": f"{p['fixture_id']} price {p['fair_odds']} is in band but flagged out."})
        if p["in_band"] and not (-250 <= p["fair_odds"] <= 10000):
            findings.append({"severity": "error", "title": "Band flag mismatch",
                             "detail": f"{p['fixture_id']} price {p['fair_odds']} is outside the band but flagged in."})

    # built site
    for page in PAGES:
        path = SITE / page
        if not path.exists():
            findings.append({"severity": "error", "title": "Missing page", "detail": f"{page} was not built."})
    for slug in ["ice-hockey", "basketball", "motor-racing", "tennis", "golf", "cricket", "darts",
                 "snooker", "volleyball", "rugby-union", "handball", "gaelic-sports", "greyhounds",
                 "baseball", "rugby-league"]:
        if not (SITE / "sports" / f"{slug}.html").exists():
            findings.append({"severity": "error", "title": "Missing sport page", "detail": f"sports/{slug}.html not built."})

    html_text = "\n".join(p.read_text(encoding="utf-8") for p in SITE.rglob("*.html"))
    if "<h2>Executive summary</h2>" not in html_text:
        findings.append({"severity": "warn", "title": "Executive summary", "detail": "No explicit executive-summary section found in the built site."})
    matches_html = (SITE / "matches.html").read_text(encoding="utf-8") if (SITE / "matches.html").exists() else ""
    if matches_html.count('target="_blank"') < len(fixtures):
        findings.append({"severity": "warn", "title": "Source link coverage",
                         "detail": "Some fixture rows may not show an official source link."})

    errors = [f for f in findings if f["severity"] == "error"]
    warns = [f for f in findings if f["severity"] == "warn"]
    (DATA / "verify_findings.json").write_text(
        json.dumps({"as_of_utc": "2026-10-24T22:45:00Z", "count": len(findings),
                    "errors": len(errors), "warnings": len(warns), "findings": findings},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"executive_verify: {len(errors)} errors, {len(warns)} warnings")
    for f in findings:
        print(f"  [{f['severity']}] {f['title']}: {f['detail']}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
