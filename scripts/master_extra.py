"""Merge the first-hand captures made in this session into the consolidated desk.

`data/master/extra_source.json` holds only what was read directly from an official page, with the
URL and the capture time. This script converts that into the same shapes `master_build.py` and
`master_verify.py` already consume, and recomputes the summary so no count is hand-edited.

Run order: master_data.py -> master_extra.py -> master_build.py -> master_verify.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MASTER = ROOT.parent / "data" / "master"
NOW = datetime(2026, 10, 23, 22, 30, tzinfo=timezone.utc)


def american(prob: float) -> int:
    if prob <= 0 or prob >= 1:
        raise ValueError(prob)
    if prob >= 0.5:
        return -round(100 * prob / (1 - prob))
    return round(100 * (1 - prob) / prob)


def decimal_from_american(am: int) -> float:
    return round(1 + (am / 100 if am > 0 else 100 / -am), 3)


def prob_from_american(am: int) -> float:
    return (100 / (-am + 100)) if am < 0 else (100 / (am + 100))


def confidence(prob: float) -> str:
    if prob >= 0.70:
        return "high"
    if prob >= 0.60:
        return "medium"
    return "low"


def in_band(am: int) -> bool:
    return -250 <= am <= 10000


def load(name: str) -> dict:
    return json.loads((MASTER / name).read_text(encoding="utf-8"))


def dump(name: str, payload: dict) -> None:
    (MASTER / name).write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    src = json.loads((MASTER / "extra_source.json").read_text(encoding="utf-8"))
    matches = load("matches.json")
    picks = load("picks.json")
    flagged = load("flagged.json")

    known = {m["id"] for m in matches["matches"]}
    added_matches = added_picks = 0

    for spec in src["matches"]:
        if spec["id"] in known:
            continue
        start = spec["start_utc"]
        started = bool(start) and datetime.fromisoformat(start).replace(tzinfo=timezone.utc) < NOW
        markets = []
        for line in spec["markets_spec"]:
            if "american" in line:
                am = line["american"]
                dec = decimal_from_american(am)
                prob = round(prob_from_american(am), 6)
            else:
                prob = line["prob"]
                am = american(prob)
                dec = round(1 / prob, 3)
            markets.append(
                {
                    "market": line["market"],
                    "selection": line["selection"],
                    "prob": prob,
                    "decimal": dec,
                    "american": am,
                    "fair_decimal": dec,
                    "fair_american": am,
                    "in_band": in_band(am),
                    "confidence": confidence(prob),
                    "basis": line["basis"],
                    "book": line.get("book", ""),
                    "main": line["market"] == "Match winner",
                }
            )
        match = dict(spec)
        match.pop("markets_spec", None)
        match["markets"] = markets
        match["started"] = started
        match["listing_state"] = "official-fixture"
        matches["matches"].append(match)
        added_matches += 1
        if started:
            continue
        for m in markets:
            picks["picks"].append(
                {
                    "id": f'{spec["id"]}|{m["market"]}|{m["selection"]}',
                    "match_id": spec["id"],
                    "sport": spec["sport"],
                    "competition": spec["competition"],
                    "event": spec["event"],
                    "start_utc": start,
                    "venue": spec["venue"],
                    "market": m["market"],
                    "selection": m["selection"],
                    "prob": m["prob"],
                    "fair_american": m["fair_american"],
                    "fair_decimal": m["fair_decimal"],
                    "in_band": m["in_band"],
                    "confidence": m["confidence"],
                    "basis": m["basis"],
                    "official_url": spec["official_url"],
                    "source_url": spec["official_source_url"],
                    "olbg_url": "",
                    "facts": [f'{spec["event"]}: {spec["competition"]}'],
                }
            )
            added_picks += 1

    existing_flags = {f["id"] for f in flagged["items"]}
    for flag in src["flags"]:
        if flag["id"] not in existing_flags:
            flagged["items"].append(flag)
            existing_flags.add(flag["id"])

    ms, ps = matches["matches"], picks["picks"]
    counts = {
        "matches": len(ms),
        "with_official": sum(1 for m in ms if m["official_url"]),
        "with_olbg": sum(1 for m in ms if m.get("olbg_url")),
        "both": sum(1 for m in ms if m["official_url"] and m.get("olbg_url")),
        "priced": sum(1 for m in ms if m["markets"]),
        "started": sum(1 for m in ms if m["started"]),
        "upcoming": sum(1 for m in ms if not m["started"]),
        "picks": len(ps),
        "high": sum(1 for p in ps if p["confidence"] == "high"),
        "high_in_band": sum(1 for p in ps if p["confidence"] == "high" and p["in_band"]),
        "medium": sum(1 for p in ps if p["confidence"] == "medium"),
        "originated_picks": sum(1 for p in ps if p["basis"] == "originated"),
        "market_implied_picks": sum(1 for p in ps if p["basis"] == "market-implied"),
        "sports_with_rows": len({m["sport"] for m in ms}),
        "sports_with_picks": len({p["sport"] for p in ps}),
    }
    dump("matches.json", matches)
    dump("picks.json", picks)
    dump("flagged.json", flagged)
    dump("summary.json", counts)
    print(json.dumps({"added_matches": added_matches, "added_picks": added_picks, **counts}, indent=1))


if __name__ == "__main__":
    main()
