#!/usr/bin/env python3
"""Generate Zenith's own fair-price ledger from official-input probabilities.

The source bundle stores the same-day official numeric inputs and line calculations in the
Cadence capture layer. This adapter recomputes fair American/decimal prices from the stored
probability (no OLBG odds are used), builds a per-fixture market ledger, and chooses a
single highest-probability available selection for each fixture. Captured bookmaker quotes
and OLBG tip consensus remain separate fields and never feed the probability.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "zenith"


def american(p: float) -> int:
    p = min(max(p, 0.0001), 0.9999)
    return int(round(-100*p/(1-p))) if p >= .5 else int(round(100*(1-p)/p))


def decimal(p: float) -> float:
    return round(1 / min(max(p, .0001), .9999), 3)


def confidence(p: float) -> str:
    if p >= .70:
        return "high"
    if p >= .60:
        return "medium"
    return "low"


def main() -> None:
    fixtures = json.loads((OUT / "fixtures.json").read_text())["fixtures"]
    base_lines = json.loads((ROOT / "data/cadence/lines.json").read_text())["lines"]
    base_picks = json.loads((ROOT / "data/cadence/picks.json").read_text())["picks"]
    by_fixture: dict[str, list[dict[str, Any]]] = {}
    for row in base_lines:
        by_fixture.setdefault(row["fixture_id"], []).append(row)
    pick_by_fixture: dict[str, list[dict[str, Any]]] = {}
    for row in base_picks:
        pick_by_fixture.setdefault(row["fixture_id"], []).append(row)

    lines, matches = [], []
    for f in fixtures:
        # Never present a pick/line as actionable if its official start is before the
        # cutoff or the official source did not confirm an exact start time.
        actionable = f.get("temporal_state") == "upcoming_at_capture"
        supported = by_fixture.get(f["id"], []) if actionable else []
        local = []
        for idx, row in enumerate(supported):
            p = round(float(row["probability"]), 6)
            # Our published odds are fair prices (zero margin); the separately named market
            # comparison fields retain any official feed quote and are not sportsbook offers.
            rec = {
                "id": f"{f['id']}-z{idx+1}", "fixture_id": f["id"], "sport": f["sport"],
                "competition": f["competition"], "market": row["market"], "selection": row["selection"],
                "line": row.get("line"), "probability": p,
                "our_fair_american": american(p), "our_fair_decimal": decimal(p),
                "confidence": row.get("confidence", confidence(p)), "in_user_odds_band": -250 <= american(p) <= 10000,
                "source_probability_id": row["id"],
                "basis": row.get("basis", ""),
                "official_fixture_url": f["official_fixture_url"],
                "official_stats_url": f["official_stats_url"],
                "olbg_event_url": f["olbg_event_url"],
                "olbg_quote_used": False,
                "bookmaker_availability": "not checked",
            }
            lines.append(rec); local.append(rec)
        candidates = pick_by_fixture.get(f["id"], [])
        selected = max(candidates, key=lambda p: (p["probability"], p["market"] == "Money line")) if candidates else None
        chosen_line = next((x for x in local if selected and x["selection"] == selected["selection"] and x["market"] == selected["market"] and x.get("line") == selected.get("line")), None)
        matches.append({**f,
            "our_selection": chosen_line["selection"] if chosen_line else "",
            "our_market": chosen_line["market"] if chosen_line else "",
            "our_probability": chosen_line["probability"] if chosen_line else None,
            "our_fair_american": chosen_line["our_fair_american"] if chosen_line else None,
            "confidence": chosen_line["confidence"] if chosen_line else "",
            "market_count": len(local),
            "markets_status": "originated from official numeric evidence" if local else ("blank: not a confirmed upcoming fixture at the 21:45 UTC cutoff" if not actionable else "blank: no official comparative numeric inputs in the captured evidence"),
        })

    (OUT / "lines.json").write_text(json.dumps({"as_of_utc": "2026-10-23T21:45:00Z", "count": len(lines), "lines": lines}, indent=2, ensure_ascii=False)+"\n")
    (OUT / "matches.json").write_text(json.dumps({"as_of_utc": "2026-10-23T21:45:00Z", "count": len(matches), "matches": matches}, indent=2, ensure_ascii=False)+"\n")
    picks=[]
    for old in base_picks:
        f=next((x for x in fixtures if x['id']==old['fixture_id']),None)
        if not f or f.get('temporal_state') != 'upcoming_at_capture': continue
        match=next(x for x in matches if x['id']==f['id'])
        rec={k:old.get(k) for k in ('id','fixture_id','sport','competition','home','away','start_utc','time_display','selection','market','line','probability','confidence','evidence_tier','evidence','basis','sport_rank')}
        rec.update({"fair_american":american(float(old['probability'])),"fair_decimal":decimal(float(old['probability'])),"in_user_odds_band":-250<=american(float(old['probability']))<=10000,"official_fixture_url":match['official_fixture_url'],"official_stats_url":match['official_stats_url'],"olbg_event_url":match['olbg_event_url'],"olbg_quote_used":False})
        picks.append(rec)
    (OUT / "picks.json").write_text(json.dumps({"as_of_utc":"2026-10-23T21:45:00Z","count":len(picks),"picks":picks},indent=2,ensure_ascii=False)+"\n")
    print(f"zenith_model: {len(matches)} fixtures; {len(lines)} fair-price selections; {len(picks)} official-evidence picks")

if __name__ == "__main__": main()
