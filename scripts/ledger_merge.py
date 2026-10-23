#!/usr/bin/env python3
"""Match every OLBG-listed event to an official fixture and record the strength of the match.

  official-fixture  the participants were found in a structured official schedule feed
                    (NHL, MLB, EuroLeague) inside a 36-hour window, with a fixture page
  official-page     the two participants sit on opposite sides of the same "v"/"vs" marker
                    in an official competition page captured today (text kept as evidence)
  unmatched         nothing official found: the row keeps its OLBG listing only and is
                    published on the flagged page

No name is corrected or guessed. If the evidence is not there, the row stays unmatched.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger_common import anchor  # noqa: E402
DATA = ROOT / "data" / "ledger"
ANCHOR = anchor()
import datetime as _dtmod
ANCHOR_DT = _dtmod.datetime.strptime(ANCHOR, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dtmod.timezone.utc)
sys.path.insert(0, str(ROOT / "scripts"))

from ledger_official import strip_tags  # noqa: E402

SCOPE = {
    "Golf": "Golf", "Volleyball": "Volleyball", "Rugby Union": "Rugby Union", "Cricket": "Cricket",
    "Snooker": "Snooker", "Darts": "Darts", "Baseball": "Baseball",
    "Gaelic Football": "Gaelic Sports", "Hurling": "Gaelic Sports", "Greyhounds": "Greyhounds",
    "Tennis": "Tennis", "Motor Racing": "Motor Racing", "Handball": "Handball",
    "Ice Hockey": "Ice Hockey", "Basketball": "Basketball", "Rugby League": "Rugby League",
}
OUT_OF_SCOPE = {"Football", "Boxing", "Horse Racing", "American Football", "Cycling", "Esports"}
STOP = {
    "the", "fc", "bc", "sc", "ac", "cf", "club", "team", "women", "womens", "men", "mens", "u21",
    "u20", "u19", "u18", "vs", "and", "of", "de", "cd", "ca", "ec", "hc", "rc", "sk", "if", "bk",
    "basket", "basketball", "handball", "hockey", "volley", "volleyball", "rugby", "league",
    "union", "cup", "match", "city", "town", "county", "sports", "sport", "athletic", "athletics",
    "united", "utd", "rovers", "one", "day", "first", "second", "test", "t20", "odi",
}
SPLIT_RE = re.compile(r"\s+(?:@|vs\.?|v\.?)\s+", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def tokens(name: str) -> set[str]:
    return {t for t in norm(name).split() if len(t) >= 4 and t not in STOP and not t.isdigit()}


def event_sides(event: str):
    m = SPLIT_RE.search(event or "")
    if not m:
        return (event or "").strip(), ""
    return event[: m.start()].strip(), event[m.end():].strip()


def dt_of(s: str):
    for fmt, n in (("%Y-%m-%dT%H:%M:%S", 19), ("%Y-%m-%d", 10)):
        try:
            return _dt.datetime.strptime(s[:n], fmt).replace(tzinfo=_dt.timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def main() -> int:
    olbg = json.loads((DATA / "olbg.json").read_text(encoding="utf-8"))
    official = json.loads((DATA / "official.json").read_text(encoding="utf-8"))
    now = ANCHOR_DT

    events: dict[tuple, dict] = {}
    for tip in olbg["tips"]:
        raw = tip["sport"]
        if raw in OUT_OF_SCOPE or raw not in SCOPE:
            continue
        start = dt_of(tip["start"])
        if not start or start < now - _dt.timedelta(hours=2):
            continue
        if str(tip.get("olbg_expired")) == "1":
            continue
        key = (SCOPE[raw], norm(tip["event"]), (tip["start"] or "")[:16])
        ev = events.setdefault(key, {
            "sport": SCOPE[raw], "olbg_sport": raw, "event": tip["event"],
            "event_id": tip["event_id"], "competition": tip["competition"],
            "start_utc": tip["start"], "venue": tip["venue"], "olbg_url": tip["event_url"],
            "captured_at": tip["captured_at"], "markets": [],
        })
        if not ev["competition"] and tip["competition"]:
            ev["competition"] = tip["competition"]
        if not ev["venue"] and tip["venue"]:
            ev["venue"] = tip["venue"]
        ev["markets"].append({
            "market": tip["market"], "selection": tip["selection"],
            "olbg_decimal": tip["olbg_decimal"], "olbg_american": tip["olbg_american"],
            "olbg_confidence": tip["olbg_confidence"],
        })

    structured: dict[str, list] = {}
    for f in official["fixtures"]:
        structured.setdefault(f["sport"], []).append(f)

    text_by_sport: dict[str, list] = {}
    for src in official["text_sources"]:
        if not src.get("ok"):
            continue
        path = DATA / src.get("stored_as", "")
        if not path.exists():
            continue
        text_by_sport.setdefault(src["sport"], []).append(
            (src["key"], src["url"], src.get("captured_at", ""), norm(strip_tags(path.read_text(encoding="utf-8", errors="replace"))))
        )

    for ev in events.values():
        a, b = event_sides(ev["event"])
        ta, tb = tokens(a), tokens(b)
        ev["side_a"], ev["side_b"] = a, b
        ev["verify"] = {"state": "unmatched", "official_url": "", "source_url": "",
                        "captured_at": "", "detail": "no official counterpart found in today's captures"}
        if not (ta and tb):
            continue

        # 1) structured official schedule
        best = None
        for f in structured.get(ev["sport"], []):
            h, aw = tokens(f"{f['home']} {f.get('home_full','')}"), tokens(f"{f['away']} {f.get('away_full','')}")
            side_ok = (bool(ta & h) and bool(tb & aw)) or (bool(ta & aw) and bool(tb & h))
            if not side_ok:
                continue
            t1, t2 = dt_of(ev["start_utc"]), dt_of(f["start_utc"])
            if t1 and t2 and abs((t1 - t2).total_seconds()) > 36 * 3600:
                continue
            best = f
            break
        if best:
            ev["verify"] = {
                "state": "official-fixture",
                "official_url": best["official_url"], "source_url": best["source_url"],
                "captured_at": best["captured_at"],
                "detail": f"matched {best['away']} at {best['home']} ({best['competition']}) in the official schedule feed",
                "fixture_id": best["fixture_id"], "official_start_utc": best["start_utc"],
                "official_venue": best["venue"], "time_basis": best.get("time_basis", "UTC as published by the feed"),
            }
            continue

        # 2) official page: both names on opposite sides of the same versus marker
        hit = None
        for key, url, cap_at, text in text_by_sport.get(ev["sport"], []):
            for sep in re.finditer(r"\s(?:vs\.?|v)\s", text):
                prev = text[max(0, sep.start() - 45): sep.start()]
                nxt = text[sep.end(): sep.end() + 45]
                if (any(t in prev for t in ta) and any(t in nxt for t in tb)) or \
                   (any(t in prev for t in tb) and any(t in nxt for t in ta)):
                    hit = (key, url, cap_at, text[max(0, sep.start() - 90): sep.end() + 100])
                    break
            if hit:
                break
        if hit:
            key, url, cap_at, snippet = hit
            ev["verify"] = {
                "state": "official-page", "official_url": url, "source_url": url,
                "captured_at": cap_at,
                "detail": f"the two participants sit either side of a versus marker on the official {key} page",
                "evidence": re.sub(r"\s+", " ", snippet)[:240],
            }

    out = sorted(events.values(), key=lambda e: (e["start_utc"], e["sport"], e["event"]))
    states, bysport = {}, {}
    for e in out:
        st = e["verify"]["state"]
        states[st] = states.get(st, 0) + 1
        s = bysport.setdefault(e["sport"], {"events": 0, "official-fixture": 0, "official-page": 0, "unmatched": 0})
        s["events"] += 1
        s[st] += 1

    result = {
        "meta": {
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "note": "OLBG-listed upcoming events in the fifteen requested sports, each matched against an official source captured today.",
            "events": len(out), "states": states, "by_sport": bysport,
        },
        "events": out,
    }
    (DATA / "matches.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result["meta"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
