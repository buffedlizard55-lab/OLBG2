"""Assemble the /daily-picks/ Flagged for Review register.

Two kinds of entry:
  * coverage gaps  - a sport, market or value this pass did not verify, with the reason;
  * irregularities - a conflict between this session's fresh official read and a value
                     already published in the repository, computed rather than claimed.

Run daily_picks_data.py and daily_picks_predictions.py first.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "daily-picks"
GENERATED = "2026-10-22T21:50:00Z"

COVERED = ["ice-hockey", "rugby-union", "aussie-rules", "rugby-league", "basketball",
           "baseball", "cricket"]

UNCOVERED = {
    "tennis": "No official ATP or WTA fixture page was readable this pass that listed a "
              "start time and a player record together; the WTA scores page reported zero live "
              "tournaments. Fixtures from the 22 October capture remain on /final/ and /current/, "
              "but no line was originated here.",
    "darts": "pdc.tv returned a cookie-consent wall instead of the schedule, so the 23 October "
             "European Championship pairings could not be re-read. /final/ carries nine dart "
             "fixtures from the earlier capture; none is priced here.",
    "snooker": "wst.tv served the Northern Ireland Open results but the later rounds ran to four "
               "multi-thousand-word chunks with no scheduled-time field; not read to completion.",
    "handball": "No official EHF page was fetched this pass.",
    "volleyball": "PlusLiga and SuperLega fixture pages were not fetched this pass.",
    "golf": "Tournament outright markets need a field list; none was fetched this pass.",
    "motor-racing": "Formula 1 driver head-to-heads were not fetched this pass; /final/ carries "
                    "nine United States Grand Prix rows from the earlier capture.",
    "gaelic-football": "County-board fixtures were not fetched this pass.",
    "greyhounds": "GBGB race cards were not fetched this pass.",
    "esports": "The LoL Worlds pairing list was not fetched this pass; /final/ notes the "
               "official schedule did not confirm the pairings it carried.",
}

INHERITED = [
    ("AFLW ladder positions, points and percentages",
     "https://www.afl.com.au/aflw",
     "Carried from the 22 October capture already committed in data/final. Not re-fetched by this "
     "session; afl.com.au/aflw/ladder returned a JavaScript shell with no rows."),
    ("ICC ODI team ratings 103 (Pakistan) and 94 (England)",
     "https://www.icc-cricket.com/rankings/mens/team-rankings/odi",
     "Carried from the 22 October capture. Not re-fetched by this session."),
    ("IRL world rankings and Round 1 scorelines",
     "https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/",
     "The Round 2 draw, venues and pool positions were re-read on nrl.com this session; the IRL "
     "rating numbers and Round 1 scorelines were carried forward and were not re-read."),
]

GENERAL = [
    ("Odds-band arithmetic", "The brief asks for high-confidence picks priced between -250 and "
     "+10000. A selection with a 70% chance prices at -233; anything at or above 70% therefore "
     "sits between -233 and -10000, and the overlap with a -250 floor is only 70.0%-71.4%. This "
     "desk publishes the true model price and marks band membership, rather than moving a line to "
     "manufacture compliant prices."),
    ("Confidence is a model label", "High, medium and low describe how far the model's probability "
     "sits from 50%. They are not strike rates, guarantees, or a claim that a price is a value bet."),
    ("Predictions are team-level", "No injury, lineup, suspension or player-scoring claim is made. "
     "Player-level facts were not read on an official page for these fixtures this pass."),
    ("Prices are not bookmaker prices", "Every price here is a fair, no-margin price computed as "
     "1 / probability from the model. No bookmaker quote was read or compared."),
    ("Two sports cannot reach five fixtures", "Baseball published two fixtures (World Series games 1 "
     "and 2) and cricket one inside the 23-25 October window, so five distinct matches do not exist "
     "for those sports here."),
    ("Repeated fixtures in the five-pick lists", "Basketball has three fixtures in the window and "
     "rugby union's best five selections include two markets on Cardiff v Sharks. Where a sport has "
     "fewer than five fixtures, the list uses additional markets on the same fixture and says so."),
]


def nhl_conflicts() -> list[dict]:
    """Compare this session's NHL standings read with the /final/ rows for the same fixture."""
    final = json.loads((ROOT / "data" / "final" / "matches.json").read_text())
    rows = final["matches"] if isinstance(final, dict) else final
    standing = {}
    text = (ROOT / "scripts" / "daily_picks_data.py").read_text()
    block = re.search(r"NHL = \{(.*?)\n\}", text, re.S).group(1)
    for name, gp, w, l, ot, gf, ga, streak in re.findall(
            r'"([^"]+)":\s*\((\d+), (\d+), (\d+), (\d+), (\d+), (\d+), "([^"]+)"\)', block):
        standing[name] = dict(gp=int(gp), w=int(w), l=int(l), ot=int(ot),
                              gf=int(gf), ga=int(ga), streak=streak)
    out = []
    seen = set()
    for r in rows:
        if r["sport"] != "ice-hockey":
            continue
        if not (r.get("date") or "").startswith(("2026-10-23", "2026-10-24", "2026-10-25")):
            continue
        for side, summary in (("home", r.get("home_summary")), ("away", r.get("away_summary"))):
            team = r[side]
            if team not in standing or not summary:
                continue
            m = re.match(r"(\d+)-(\d+)-(\d+) \((\d+) GF / (\d+) GA\)", summary)
            if not m:
                continue
            old = dict(w=int(m.group(1)), l=int(m.group(2)), ot=int(m.group(3)),
                       gf=int(m.group(4)), ga=int(m.group(5)))
            new = standing[team]
            diffs = [k for k in old if old[k] != new[k]]
            if diffs and (team, r.get("date")) not in seen:
                seen.add((team, r.get("date")))
                out.append({
                    "id": f"IR-NHL-{len(out) + 1:02d}",
                    "team": team,
                    "fixture": f"{r['home']} vs {r['away']}",
                    "date": r["date"],
                    "published": summary,
                    "verified": (f"{new['w']}-{new['l']}-{new['ot']} "
                                 f"({new['gf']} GF / {new['ga']} GA, {new['gp']} GP)"),
                    "fields": diffs,
                    "source": "https://www.nhl.com/standings/2026-10-22/wildcard",
                })
    return out


def main() -> None:
    picks = json.loads((OUT / "picks.json").read_text())
    matches = json.loads((OUT / "matches.json").read_text())
    preds = json.loads((OUT / "predictions.json").read_text())

    per_sport = {}
    for p in picks["picks"]:
        per_sport.setdefault(p["sport"], []).append(p)

    coverage = []
    for sport in COVERED:
        rows = [m for m in matches["matches"] if m["sport"] == sport]
        got = per_sport.get(sport, [])
        coverage.append({
            "sport": sport,
            "fixtures": len(rows),
            "picks": len(got),
            "high": sum(1 for x in got if x["confidence"] == "high"),
            "high_in_band": sum(1 for x in got if x["confidence"] == "high" and x["in_band"]),
            "target_met": len(got) >= 5,
            "note": ("five picks published" if len(got) >= 5 else
                     f"only {len(rows)} verified fixture(s) in the window, so {len(got)} picks "
                     f"published across the markets available"),
        })

    conflicts = nhl_conflicts()
    flags = {
        "generated_utc": GENERATED,
        "session": "arena/6b4da610-olbg2",
        "counts": {
            "coverage_gaps": len(UNCOVERED),
            "inherited_inputs": len(INHERITED),
            "discrepancies": len(conflicts),
            "general": len(GENERAL),
            "total": len(UNCOVERED) + len(INHERITED) + len(conflicts) + len(GENERAL),
        },
        "coverage": coverage,
        "sports_not_covered": [{"sport": k, "reason": v} for k, v in UNCOVERED.items()],
        "inherited_inputs": [{"item": i, "source": u, "detail": d} for i, u, d in INHERITED],
        "discrepancies": conflicts,
        "general": [{"item": i, "detail": d} for i, d in GENERAL],
        "predictions_published": preds["count"],
    }
    (OUT / "flagged.json").write_text(json.dumps(flags, indent=1))
    print("flags:", flags["counts"], "coverage:", [(c["sport"], c["fixtures"], c["picks"]) for c in coverage])


if __name__ == "__main__":
    main()
