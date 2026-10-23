#!/usr/bin/env python3
"""Build the selection table: every price we originated, plus the market-implied picks for
OLBG rows that have no official numeric input.

Two bases are published side by side and never mixed silently:

  originated       our own fair price, computed by scripts/ledger_model.py from official
                   season records only (no bookmaker input)
  market-implied   1 / OLBG's quoted decimal for that selection. It is a published market
                   price, not our origination, and every such row says so.

Confidence rule (single rule for both bases): high >= 70%, medium 60-69.99%, low < 60%.
Band rule: the fair American price must satisfy -250 <= price <= +10000.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402
DATA = ROOT / "data" / "ledger"
ANCHOR = anchor()
import datetime as _dtmod
ANCHOR_DT = _dtmod.datetime.strptime(ANCHOR, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dtmod.timezone.utc)


def dec_to_american(dec: float) -> str:
    if not dec or dec <= 1:
        return ""
    if dec >= 2:
        return f"+{round((dec - 1) * 100):d}"
    return f"{round(-100 / (dec - 1)):d}"


def band(american: str) -> bool:
    try:
        a = int(american)
    except (TypeError, ValueError):
        return False
    return -250 <= a <= 10000


def grade(p: float) -> str:
    return "high" if p >= 0.70 else ("medium" if p >= 0.60 else "low")


def main() -> int:
    lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))
    matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))

    picks = []
    for f in lines["fixtures"]:
        if not f.get("markets"):
            continue
        for group, label in (("win", "Win match"), ("handicap", "Handicap"), ("total", "Match total")):
            for s in f["markets"].get(group, []):
                picks.append({
                    "id": f"{f['fixture_id']}-{group}-{s['selection'].replace(' ', '_')}",
                    "sport": f["sport"], "competition": f["competition"],
                    "event": f"{f['away']} at {f['home']}" if f["sport"] in ("Ice Hockey", "Baseball") else f"{f['away']} v {f['home']}",
                    "match_id": f["fixture_id"], "start_utc": f["start_utc"],
                    "market": s["market"], "market_group": label, "selection": s["selection"],
                    "prob": s["prob"], "decimal": s["decimal"], "american": s["american"],
                    "in_band": s["in_band"], "confidence": grade(s["prob"]),
                    "basis": "originated", "official_url": f["official_url"],
                    "source_url": f["source_url"], "olbg_url": "", "venue": f.get("venue", ""),
                })

    for ev in matches["events"]:
        if ev.get("our_markets"):
            continue  # already covered by an originated row above
        best = None
        for m in ev["markets"]:
            try:
                dec = float(m["olbg_decimal"])
            except (TypeError, ValueError):
                continue
            if dec <= 1:
                continue
            p = 1 / dec
            cand = {**m, "prob": p, "decimal": dec, "american": m["olbg_american"] or dec_to_american(dec)}
            if best is None or cand["prob"] > best["prob"]:
                best = cand
        if not best:
            continue
        picks.append({
            "id": f"olbg-{ev['event_id']}-{best['selection'].replace(' ', '_')}",
            "sport": ev["sport"], "competition": ev["competition"], "event": ev["event"],
            "match_id": ev["event_id"], "start_utc": ev["start_utc"],
            "market": best["market"] or "Quoted market", "market_group": best["market"] or "Quoted market",
            "selection": best["selection"], "prob": round(best["prob"], 4), "decimal": best["decimal"],
            "american": best["american"], "in_band": band(best["american"]),
            "confidence": grade(best["prob"]), "basis": "market-implied",
            "official_url": ev["verify"]["official_url"], "source_url": ev["olbg_url"],
            "olbg_url": ev["olbg_url"], "venue": ev["venue"],
            "verify_state": ev["verify"]["state"],
        })

    picks.sort(key=lambda p: (-p["prob"], p["sport"], p["event"]))
    by_sport, top5 = {}, {}
    for p in picks:
        by_sport.setdefault(p["sport"], []).append(p)
    for sport, rows in by_sport.items():
        # a "match winner" table first, then the strongest of the remaining markets
        winners = [r for r in rows if "win" in r["market_group"].lower()]
        winners.sort(key=lambda r: -r["prob"])
        chosen = winners[:5]
        if len(chosen) < 5:
            rest = sorted([r for r in rows if r not in chosen], key=lambda r: -r["prob"])
            chosen += rest[: 5 - len(chosen)]
        top5[sport] = [r["id"] for r in chosen]

    high = [p for p in picks if p["confidence"] == "high"]
    high_band = [p for p in high if p["in_band"]]
    out = {
        "meta": {
            "generated_at": ANCHOR,
            "selections": len(picks),
            "originated": len([p for p in picks if p["basis"] == "originated"]),
            "market_implied": len([p for p in picks if p["basis"] == "market-implied"]),
            "high": len(high), "high_in_band": len(high_band),
            "medium": len([p for p in picks if p["confidence"] == "medium"]),
            "low": len([p for p in picks if p["confidence"] == "low"]),
            "sports": sorted(by_sport),
            "top5_by_sport": top5,
            "rule": "high >= 70%; in band = fair American between -250 and +10000",
        },
        "picks": picks,
    }
    (DATA / "picks.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["meta"], indent=1)[:1400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
