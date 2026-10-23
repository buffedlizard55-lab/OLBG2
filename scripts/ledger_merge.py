#!/usr/bin/env python3
"""Match every OLBG-listed event to an official fixture, and record how it was matched.

Three outcomes, in decreasing strength:

  official-fixture  the participants were found in a structured official schedule feed
                    (NHL, MLB, EuroLeague) with a kick-off time and a fixture page
  official-page     both participants were found in the text of an official competition
                    page captured today (the page is linked on the row)
  unmatched         nothing official could be found: the row keeps its OLBG listing only
                    and is published on the flagged page

The matching is deliberately conservative: a token has to appear for *each* side of the
fixture, and a structured match must also fall inside a date window.  No name is
"corrected" or guessed; if a token is missing the row simply stays unmatched.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ledger"

SCOPE = {
    "Golf": "Golf", "Volleyball": "Volleyball", "Rugby Union": "Rugby Union", "Cricket": "Cricket",
    "Snooker": "Snooker", "Darts": "Darts", "Baseball": "Baseball",
    "Gaelic Football": "Gaelic Sports", "Hurling": "Gaelic Sports", "Greyhounds": "Greyhounds",
    "Tennis": "Tennis", "Motor Racing": "Motor Racing", "Handball": "Handball",
    "Ice Hockey": "Ice Hockey", "Basketball": "Basketball", "Rugby League": "Rugby League",
}
OUT_OF_SCOPE = {"Football", "Boxing", "Horse Racing", "American Football", "Cycling", "Esports", "Rugby Sevens"}

STOP = {
    "the", "fc", "bc", "sc", "ac", "cf", "club", "team", "women", "womens", "men", "mens", "u21", "u20",
    "u19", "u18", "vs", "v", "and", "of", "de", "cd", "ca", "ec", "hc", "rc", "sk", "if", "bk", "basket",
    "basketball", "handball", "hockey", "volley", "volleyball", "rugby", "league", "union", "cup", "match",
    "city", "town", "county", "sports", "sport", "athletic", "athletics", "united", "utd", "rovers",
}

RE_SPLIT_EVENT = re.compile(r"\s+(?:@|vs\.?|v\.?)\s+", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def tokens(name: str) -> set[str]:
    return {t for t in norm(name).split() if len(t) >= 4 and t not in STOP and not t.isdigit()}


def event_sides(event: str) -> tuple[str, str, str]:
    """Return (side_a, side_b, separator) without assuming which is home."""
    text = event.strip()
    m = RE_SPLIT_EVENT.search(text)
    if not m:
        return text, "", ""
    return text[: m.start()].strip(), text[m.end():].strip(), m.group(0).strip()


def dt_of(s: str):
    try:
        return _dt.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=_dt.timezone.utc)
    except (ValueError, TypeError):
        try:
            return _dt.datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=_dt.timezone.utc)
        except (ValueError, TypeError):
            return None


def load_text(key: str) -> str:
    from ledger_official import strip_tags  # local module, same directory
    cap_path = DATA / "raw" / f"{key}.html"
    if not cap_path.exists():
        return ""
    return strip_tags(cap_path.read_text(encoding="utf-8", errors="replace"))


def main() -> int:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    olbg = json.loads((DATA / "olbg.json").read_text(encoding="utf-8"))
    official = json.loads((DATA / "official.json").read_text(encoding="utf-8"))
    NOW = _dt.datetime.now(_dt.timezone.utc)

    # ---- collapse OLBG tips into events
    events: dict[tuple, dict] = {}
    for tip in olbg["tips"]:
        raw_sport = tip["sport"]
        if raw_sport in OUT_OF_SCOPE or raw_sport not in SCOPE:
            continue
        start = dt_of(tip["start"])
        if not start or start < NOW - _dt.timedelta(hours=2):
            continue  # already under way or finished: not an upcoming match
        if str(tip.get("olbg_expired")) == "1":
            continue
        key = (SCOPE[raw_sport], tip["event_id"] or tip["event"])
        ev = events.setdefault(key, {
            "sport": SCOPE[raw_sport],
            "olbg_sport": raw_sport,
            "event": tip["event"],
            "event_id": tip["event_id"],
            "competition": tip["competition"],
            "start_utc": tip["start"],
            "venue": tip["venue"],
            "olbg_url": tip["event_url"],
            "captured_at": tip["captured_at"],
            "markets": [],
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

    # ---- official structured fixtures by sport
    structured = {}
    for f in official["fixtures"]:
        structured.setdefault(f["sport"], []).append(f)

    # ---- official text pages by sport
    text_by_sport: dict[str, list[tuple[str, str, str]]] = {}
    for src in official["text_sources"]:
        if not src.get("ok"):
            continue
        text_by_sport.setdefault(src["sport"], []).append((src["key"], src["url"], norm(load_text(src["key"]))))

    out = []
    for ev in events.values():
        a, b, sep = event_sides(ev["event"])
        ta, tb = tokens(a), tokens(b)
        ev["side_a"], ev["side_b"] = a, b
        ev["verify"] = {"state": "unmatched", "official_url": "", "source_url": "", "captured_at": "",
                        "detail": "no official counterpart found in today's captures"}
        if ta and tb:
            # 1) structured feed match
            best = None
            for f in structured.get(ev["sport"], []):
                names = [f"{f['home']} {f.get('home_full','')}", f"{f['away']} {f.get('away_full','')}",
                         f"{f.get('home_abbrev','')}", f.get("away_abbrev", "")]
                hay = [tokens(n) for n in names[:2]]
                ok_a = bool(ta & (hay[0] | hay[1])) and bool(tb & (hay[0] | hay[1]))
                # one side must hit each team's own token set
                side_ok = (bool(ta & hay[0]) and bool(tb & hay[1])) or (bool(ta & hay[1]) and bool(tb & hay[0]))
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
                    "official_url": best["official_url"],
                    "source_url": best["source_url"],
                    "captured_at": best["captured_at"],
                    "detail": f"matched {best['away']} at {best['home']} ({best['competition']}) in the official schedule feed",
                    "fixture_id": best["fixture_id"],
                    "official_start_utc": best["start_utc"],
                    "official_venue": best["venue"],
                    "time_basis": best.get("time_basis", "UTC as published by the feed"),
                }
            else:
                # 2) text match against the sport's official pages
                for key, url, text in text_by_sport.get(ev["sport"], []):
                    ta_hit = any(t in text for t in ta)
                    tb_hit = any(t in text for t in tb)
                    if ta_hit and tb_hit:
                        ev["verify"] = {
                            "state": "official-page",
                            "official_url": url,
                            "source_url": url,
                            "captured_at": next((s["captured_at"] for s in official["text_sources"] if s["key"] == key), ""),
                            "detail": f"both participants appear in the text of the official {key} page",
                        }
                        break
        out.append(ev)

    out.sort(key=lambda e: (e["start_utc"], e["sport"], e["event"]))
    states = {}
    for e in out:
        states[e["verify"]["state"]] = states.get(e["verify"]["state"], 0) + 1
    bysport = {}
    for e in out:
        bysport.setdefault(e["sport"], {"events": 0, "official-fixture": 0, "official-page": 0, "unmatched": 0})
        bysport[e["sport"]]["events"] += 1
        bysport[e["sport"]][e["verify"]["state"]] += 1

    result = {
        "meta": {
            "generated_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "note": "OLBG-listed upcoming events in the fifteen requested sports, each matched against an official source captured today.",
            "events": len(out),
            "states": states,
            "by_sport": bysport,
        },
        "events": out,
    }
    (DATA / "matches.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result["meta"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
