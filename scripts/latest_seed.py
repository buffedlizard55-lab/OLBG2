#!/usr/bin/env python3
"""Seed the /latest/ desk from evidence that is already committed, with provenance kept intact.

Nothing here invents a fact. Every fixture, every fact and every price is read from the desk that
captured it (`data/now/`), stamped with that capture's time, and republished with the same source
URL. The only new material this session adds is a hand-written live re-check log
(`data/latest/rechecks.json`) and one first-hand capture of the Formula 1 qualifying classification
(`data/latest/f1.json`), both of which were read during this session and are stored with their URL
and read time.

Run:  python scripts/latest_seed.py
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "now"
OUT = ROOT / "data" / "latest"

# The moment this desk describes. Everything downstream is stamped with it so a reader can tell
# which fixtures were still to start when the desk was cut.
BUILD_UTC = "2026-10-24T22:45:00Z"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]


def read(name, base=SRC):
    return json.loads((base / name).read_text(encoding="utf-8"))


def write(name, doc):
    (OUT / name).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fx_src = read("fixtures.json")
    matches = read("matches.json")["matches"]
    lines_src = read("lines.json")
    sources_src = read("sources.json")
    olbg_src = read("olbg.json")
    rechecks = read("rechecks.json", OUT) if (OUT / "rechecks.json").exists() else {"rechecks": []}
    f1 = read("f1.json", OUT)

    status = {m["id"]: m for m in matches}

    fixtures = []
    for f in fx_src["fixtures"]:
        m = status.get(f["id"], {})
        row = dict(f)
        row["status"] = m.get("status", "priced")
        row["blank_reason"] = m.get("blank_reason", "")
        row["inherited"] = {
            "from": "data/now/fixtures.json",
            "captured_utc": f.get("facts_capture", "").split(" ")[-1] or "2026-10-24T17:35:00Z",
        }
        fixtures.append(row)

    # The Formula 1 race is the one fixture this session re-captured first hand, because the
    # qualifying classification it needed did not exist at the 17:35Z capture.
    f1_fixture = {
        "id": f1["fixture_id"],
        "sport": "Motor Racing",
        "competition": f1["competition"],
        "home": f1["favourite"],
        "away": "Field",
        "start_utc": f1["start_utc"],
        "start_display": f1["start_display"],
        "venue": f1["venue"],
        "official_url": f1["source_url"],
        "olbg_url": f1["olbg_url"],
        "inputs": {"grid": f1["grid"]},
        "status": "priced",
        "blank_reason": "",
        "facts_inherited": False,
        "facts_capture": f1["captured_utc"],
        "inherited": {"from": "data/latest/f1.json", "captured_utc": f1["captured_utc"]},
        "olbg_listed": True,
        "facts": f1["facts"],
    }
    # Replace the inherited, unpriced Motor Racing row with the first-hand capture.
    fixtures = [f for f in fixtures if f["id"] != f1_fixture["id"]] + [f1_fixture]
    order = {s: i for i, s in enumerate(SPORTS)}
    fixtures.sort(key=lambda r: (order[r["sport"]], r["start_utc"], r["id"]))

    lines = list(lines_src["lines"])
    lines = [dict(r, origin="inherited from data/now/lines.json (captured 17:35Z)") for r in lines]

    write("fixtures.json", {
        "build_utc": BUILD_UTC,
        "sports": SPORTS,
        "count": len(fixtures),
        "inheritance_note": (
            "Every fixture except the Formula 1 race was captured by the /now/ desk at 17:35Z on "
            "2026-10-24 and is republished here unchanged with its own capture time and source URL. "
            "The Formula 1 row was read first hand during this session after qualifying."),
        "fixtures": fixtures,
    })
    write("lines.json", {
        "build_utc": BUILD_UTC,
        "count": len(lines),
        "note": "Originated by the /now/ desk from official rates; no bookmaker price was read.",
        "lines": lines,
    })
    # The qualifying classification was read first hand in this session, so it is added to the register
    # with its own read time rather than being attributed to the earlier capture.
    sources = [dict(s) for s in sources_src["sources"]]
    sources = [s for s in sources if s["url"] != f1["source_url"]]
    sources.append({
        "url": f1["source_url"],
        "source_key": "f1_usgp_quali",
        "captured_utc": f1["captured_utc"],
        "claims": len(f1["facts"]),
        "sports": ["Motor Racing"],
        "fixtures": 1,
        "official": True,
        "kind": "official governing body / championship results",
    })
    sources.sort(key=lambda r: r["url"])
    write("sources.json", {"build_utc": BUILD_UTC, "count": len(sources),
                           "official_count": sum(1 for s in sources if s.get("official")),
                           "sources": sources})
    write("olbg.json", {
        "capture_utc": olbg_src.get("capture_utc"),
        "rechecked_utc": olbg_src.get("rechecked_utc"),
        "hubs": olbg_src.get("hubs", []),
        "rechecks": rechecks.get("rechecks", []),
    })
    print(f"latest_seed: {len(fixtures)} fixtures, {len(lines)} originated prices, "
          f"{len(sources_src['sources'])} sources, {len(rechecks.get('rechecks', []))} live re-checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
