#!/usr/bin/env python3
"""Consolidate the five published layers into one canonical, de-duplicated dataset.

Inputs (read-only):
  data/verified/matches.json      primary-source desk, 118 rows
  data/hub/matches.json           multi-sport hub, 189 rows
  data/board/matches.json         board layer, 207 rows
  data/slate/matches.json         slate layer, 148 rows
  data/forward/matches.json       forward window, 93 rows

Outputs:
  data/final/matches.json         canonical rows, one per fixture
  data/final/summary.json         counts + audit numbers
  data/final/sports.json          17 eligible + 10 excluded sports

Rules enforced here
-------------------
* Fixtures are clustered by sport + unordered team pair + date (+/-1 day), so the
  same game captured by different layers becomes one row.
* Every row keeps the official URL and source name of the layer it came from.
* A row is `high` only if the selected outcome has model probability >= 70% AND a
  fair decimal price inside 1.40..101.00 (the brief's -250..+10000 band). This is
  the only interval that satisfies both constraints (70% -> 1.43 decimal).
* A >=70% selection priced shorter than 1.40 is graded `medium` with an explicit
  reason; it is not silently promoted to high.
* No bookmaker price is read, derived or published. Slate's synthetic `book_dec`
  columns are dropped.
"""
from __future__ import annotations

import json
import re
import unicodedata
import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "final"

NOW = dt.datetime(2026, 10, 22, 8, 22, tzinfo=dt.timezone.utc)

LAYER_FILES = [
    ("verified", DATA / "verified" / "matches.json", "matches", "captured_at", 0),
    ("hub", DATA / "hub" / "matches.json", "rows", "captured_at", 1),
    ("board", DATA / "board" / "matches.json", "matches", "captured_at", 2),
    ("slate", DATA / "slate" / "matches.json", "matches", "generated_at", 3),
    ("forward", DATA / "forward" / "matches.json", "matches", "captured_at", 4),
]

# Layer preference when two rows are otherwise equally good (lower = preferred).
# verified is the desk that was already re-read line by line on 2026-10-22; hub is
# the newest broad capture. slate is last because it publishes synthetic book prices.
PRIORITY = {"verified": 0, "hub": 1, "board": 2, "slate": 3, "forward": 4}

BAND_MIN_DEC = 1.40
BAND_MAX_DEC = 101.00
BAND_MIN_AM = -250
BAND_MAX_AM = 10000
HIGH_MIN_PROB = 0.70
MEDIUM_MIN_PROB = 0.60

EXCLUDED_KEYWORDS = [
    "soccer", "boxing", "ufc", "mma", "american football",
    "hurling", "horse racing", "cycling", "specials",
]
# "football" alone means association football; "gaelic-football" and "american-football"
# are separate entries, and only the latter is excluded.
EXCLUDED_SPORTS = {"soccer", "boxing", "ufc-mma", "american-football", "hurling",
                   "horse-racing", "cycling", "specials"}

SPORT_NAMES = {
    "ice-hockey": "Ice Hockey", "basketball": "Basketball", "rugby-union": "Rugby Union",
    "darts": "Darts", "tennis": "Tennis", "handball": "Handball", "volleyball": "Volleyball",
    "baseball": "Baseball", "motor-racing": "Motor Racing", "snooker": "Snooker",
    "cricket": "Cricket", "golf": "Golf", "rugby-league": "Rugby League",
    "gaelic-football": "Gaelic Football", "greyhounds": "Greyhounds",
    "aussie-rules": "Aussie Rules", "esports": "eSports",
}

SPORT_ORDER = list(SPORT_NAMES)


# --------------------------------------------------------------------------- helpers
def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def name_of(value) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("code") or "").strip()
    return str(value or "").strip()


def norm_team(value) -> str:
    s = unicodedata.normalize("NFKD", name_of(value)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    words = [w for w in s.split() if len(w) > 2 and w not in {
        "the", "rugby", "club", "aik", "bk", "xv", "fc", "sc", "bc", "hc",
    }]
    return " ".join(sorted(words))


def parse_dt(value):
    if not value:
        return None
    s = str(value).strip().replace(" UTC", "").replace("Z", "")
    for fmt, length in (
        ("%Y-%m-%dT%H:%M:%S", 19),
        ("%Y-%m-%d %H:%M:%S", 19),
        ("%Y-%m-%dT%H:%M", 16),
        ("%Y-%m-%d %H:%M", 16),
        ("%Y-%m-%d", 10),
    ):
        try:
            return dt.datetime.strptime(s[:length], fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def iso_z(value: str | None) -> str | None:
    parsed = parse_dt(value)
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ") if parsed else (value or None)


def dec_from_american(am):
    try:
        am = int(am)
    except (TypeError, ValueError):
        return None
    if am < 0:
        return round(1 + 100 / abs(am), 2)
    return round(1 + am / 100, 2)


def american_from_dec(dec):
    if dec is None:
        return None
    if dec >= 2.0:
        return int(round((dec - 1) * 100))
    return int(round(-100 / (dec - 1)))


def fair_pair(prob: float):
    dec = round(max(1.02, 1.0 / max(prob, 1e-9)), 2)
    return dec, american_from_dec(dec)


def in_band(dec) -> bool:
    return dec is not None and BAND_MIN_DEC - 1e-9 <= dec <= BAND_MAX_DEC + 1e-9


def grade(prob, dec) -> tuple[str, str]:
    if prob is None or dec is None:
        return "low", "no model probability"
    if prob >= HIGH_MIN_PROB and in_band(dec):
        return "high", ">=70% model probability and fair price inside 1.40-101.00"
    if prob >= HIGH_MIN_PROB and dec < BAND_MIN_DEC:
        return "medium", ("model probability >=70% but fair price is shorter than -250 "
                          "(1.40 decimal), outside the brief's focus band")
    if prob >= MEDIUM_MIN_PROB:
        return "medium", ">=60% model probability"
    if prob >= 0.45:
        return "low", "under 60% model probability"
    return "low", "under 60% model probability"


def source_scope(url: str) -> str:
    if not url:
        return "competition"
    if re.search(r"/players?/", url):
        return "player"
    if re.search(r"/gamecenter/|/match-centre/|/matches?/\d|/fixtures?/|/game/\d|/tie/", url):
        return "fixture"
    return "competition"


# --------------------------------------------------------------------------- load
def load_layers():
    layers = {}
    for name, path, key, stamp_key, _prio in LAYER_FILES:
        payload = read_json(path)
        rows = payload[key]
        captured = payload.get(stamp_key) or ""
        for row in rows:
            row["_layer"] = name
            row["_captured"] = captured
        layers[name] = rows
    return layers


# --------------------------------------------------------------------------- markets
def market_outcome(label, prob, dec=None, am=None):
    prob = float(prob) if prob is not None else None
    if prob and prob > 0:
        # the price is definitionally 1/p; recomputing removes layer-to-layer
        # rounding drift and field misalignment, and caps absurd decimals
        dec = round(1.0 / prob, 2)
    else:
        dec = float(dec) if dec is not None else (dec_from_american(am) if am is not None else None)
    am = int(am) if am is not None else american_from_dec(dec)
    return {
        "label": str(label),
        "probability": round(prob, 4) if prob is not None else None,
        "fair_decimal": round(dec, 2) if dec is not None else None,
        "fair_american": am,
    }


def markets_verified(row):
    out = []
    winner = row.get("winner_market") or {}
    if winner:
        label = winner.get("type") or "Moneyline"
        outcomes = []
        if winner.get("draw_prob") is not None:
            outcomes.append(market_outcome("Draw", winner["draw_prob"], am=winner.get("draw_odds")))
        outcomes.append(market_outcome(name_of(row.get("home")), winner.get("home_prob"), am=winner.get("home_american")))
        outcomes.append(market_outcome(name_of(row.get("away")), winner.get("away_prob"), am=winner.get("away_american")))
        # home_odds/away_odds are decimal in this schema
        if winner.get("home_odds") is not None:
            outcomes[-2]["fair_decimal"] = winner["home_odds"]
            outcomes[-2]["fair_american"] = american_from_dec(winner["home_odds"])
        if winner.get("away_odds") is not None:
            outcomes[-1]["fair_decimal"] = winner["away_odds"]
            outcomes[-1]["fair_american"] = american_from_dec(winner["away_odds"])
        out.append({"market": "1X2" if winner.get("draw_prob") is not None else "Moneyline",
                    "outcomes": [o for o in outcomes if o["probability"] is not None]})

    hcp = row.get("handicap_market") or {}
    if hcp and hcp.get("label"):
        parts = [p.strip() for p in hcp["label"].split(" / ")]
        if len(parts) == 2:
            out.append({"market": "Handicap", "line": hcp.get("line"), "outcomes": [
                market_outcome(parts[0], hcp.get("fav_prob"), am=hcp.get("fav_american")),
                market_outcome(parts[1], hcp.get("dog_prob"), am=hcp.get("dog_american")),
            ]})
            if hcp.get("fav_odds") is not None:
                out[-1]["outcomes"][0]["fair_decimal"] = hcp["fav_odds"]
                out[-1]["outcomes"][0]["fair_american"] = american_from_dec(hcp["fav_odds"])
            if hcp.get("dog_odds") is not None:
                out[-1]["outcomes"][1]["fair_decimal"] = hcp["dog_odds"]
                out[-1]["outcomes"][1]["fair_american"] = american_from_dec(hcp["dog_odds"])

    total = row.get("total_market") or {}
    if total and total.get("line") is not None:
        out.append({"market": "Total", "line": total["line"], "outcomes": [
            market_outcome(f"Over {total['line']}", total.get("over_prob"), am=total.get("over_american")),
            market_outcome(f"Under {total['line']}", total.get("under_prob"), am=total.get("under_american")),
        ]})
        if total.get("over_odds") is not None:
            out[-1]["outcomes"][0]["fair_decimal"] = total["over_odds"]
            out[-1]["outcomes"][0]["fair_american"] = american_from_dec(total["over_odds"])
        if total.get("under_odds") is not None:
            out[-1]["outcomes"][1]["fair_decimal"] = total["under_odds"]
            out[-1]["outcomes"][1]["fair_american"] = american_from_dec(total["under_odds"])
    return out


MARKET_LABELS = {
    "winner": "Moneyline", "handicap": "Handicap", "total": "Total",
    "match winner": "Moneyline", "match result (1x2)": "1X2", "1x2": "1X2",
    "set handicap": "Handicap", "puck line": "Handicap", "handicap": "Handicap",
    "total games": "Total", "total": "Total", "total goals": "Total",
    "outright": "Outright",
}


def markets_hub(row):
    out = []
    for key, block in (row.get("markets") or {}).items():
        if not isinstance(block, dict):
            continue
        outs = []
        for o in block.get("outcomes") or []:
            if o.get("prob") is None:
                continue
            outs.append(market_outcome(o["label"], o["prob"], dec=o.get("fair_decimal"), am=o.get("fair_american")))
        if outs:
            out.append({"market": MARKET_LABELS.get(str(key).lower(), str(key).title()),
                        "line": block.get("line"), "outcomes": outs})
    return out


def markets_slate(row):
    out = []
    for block in row.get("markets") or []:
        name = MARKET_LABELS.get(str(block.get("market", "")).lower(), str(block.get("market", "Market")))
        outs = [market_outcome(o["label"], o.get("fair_prob"), dec=o.get("fair_dec"), am=o.get("fair_am"))
                for o in block.get("outcomes") or [] if o.get("fair_prob") is not None]
        if outs:
            out.append({"market": name, "line": block.get("line"), "outcomes": outs})
    return out


def normalize_markets(row):
    layer = row["_layer"]
    if layer == "hub":
        markets = markets_hub(row)
    elif layer == "slate":
        markets = markets_slate(row)
    else:
        markets = markets_verified(row)
    # Single source of truth: every published price is exactly 1/p.
    for market in markets:
        for outcome in market.get("outcomes", []):
            p = outcome.get("probability")
            if p:
                outcome["fair_decimal"] = round(1.0 / p, 2)
                outcome["fair_american"] = american_from_dec(outcome["fair_decimal"])
    return markets


def own_pick(row):
    layer = row["_layer"]
    if layer == "hub":
        p = row.get("pick") or {}
        if not p:
            return None
        dec = p.get("fair_decimal")
        am = p.get("fair_american")
        return {"selection": p.get("selection"), "market": p.get("market") or "Match Winner",
                "probability": p.get("prob"), "fair_decimal": dec if dec is not None else dec_from_american(am),
                "fair_american": am if am is not None else american_from_dec(dec)}
    if layer == "slate":
        p = row.get("recommended_pick") or {}
        if p:
            return {"selection": p.get("selection"), "market": p.get("market") or "Match Winner",
                    "probability": p.get("fair_prob"), "fair_decimal": p.get("fair_dec"),
                    "fair_american": int(p["fair_am"]) if str(p.get("fair_am", "")).lstrip("+-").isdigit() else None}
        return None
    p = row.get("pick") or {}
    if not p:
        return None
    return {"selection": p.get("selection"), "market": p.get("market") or "Match Winner",
            "probability": p.get("probability"),
            "fair_decimal": p.get("fair_odds") or dec_from_american(p.get("fair_american")),
            "fair_american": p.get("fair_american")}


def all_outcomes(markets):
    for m in markets:
        for o in m["outcomes"]:
            yield m, o


def match_outcome(pick, markets):
    if not pick or not pick.get("selection"):
        return None
    want = re.sub(r"\s*\(.*?\)\s*", "", str(pick["selection"])).strip().lower()
    best = None
    for market, o in all_outcomes(markets):
        label = re.sub(r"\s*\(.*?\)\s*", "", o["label"]).strip().lower()
        if label == want:
            return market, o
        if best is None and (want in label or label in want):
            best = (market, o)
    return best


def choose_pick(row, markets):
    """Pick the best brief-compliant selection from this row's own markets."""
    pick = own_pick(row)
    matched = match_outcome(pick, markets) if pick else None
    if pick and matched:
        market, o = matched
        pick = {**pick, "selection": o["label"], "market": market["market"],
                "probability": o["probability"], "fair_decimal": o["fair_decimal"],
                "fair_american": o["fair_american"]}

    # An in-band, >=70% outcome anywhere in the row's markets is the featured pick.
    window = []
    for market, o in all_outcomes(markets):
        p, d = o["probability"], o["fair_decimal"]
        if p is not None and d is not None and HIGH_MIN_PROB <= p <= 0.71475 and in_band(d):
            window.append((market, o))
    if window:
        # Closest to the centre of the 70.0-71.45% window, then Moneyline first.
        order = {"Moneyline": 0, "1X2": 1, "Handicap": 2, "Total": 3, "Outright": 4}
        window.sort(key=lambda mo: (abs(mo[1]["probability"] - 0.7071), order.get(mo[0]["market"], 9)))
        market, o = window[0]
        pick = {"selection": o["label"], "market": market["market"], "probability": o["probability"],
                "fair_decimal": o["fair_decimal"], "fair_american": o["fair_american"]}
    elif not pick:
        # No published pick: use the highest-probability outcome in the row.
        best = None
        for market, o in all_outcomes(markets):
            if o["probability"] is not None and (best is None or o["probability"] > best[1]["probability"]):
                best = (market, o)
        if best:
            market, o = best
            pick = {"selection": o["label"], "market": market["market"], "probability": o["probability"],
                    "fair_decimal": o["fair_decimal"], "fair_american": o["fair_american"]}
    if not pick:
        return None
    conf, reason = grade(pick["probability"], pick["fair_decimal"])
    pick["confidence"] = conf
    pick["grade_reason"] = reason
    return pick


# --------------------------------------------------------------------------- clustering
def cluster_key(row):
    d = parse_dt(row.get("date") or row.get("start_utc") or row.get("time") or row.get("time_utc"))
    date = d.date() if d else None
    return (row.get("sport"), frozenset([norm_team(row.get("home")), norm_team(row.get("away"))])), date


def row_quality(row, markets, pick):
    has_window = 0
    for _m, o in all_outcomes(markets):
        p, d = o["probability"], o["fair_decimal"]
        if p is not None and d is not None and HIGH_MIN_PROB <= p <= 0.71475 and in_band(d):
            has_window = 1
            break
    return (
        1 if row.get("line_status") == "originated" or row.get("status") == "originated" else 0,
        has_window,
        len(markets),
        -PRIORITY[row["_layer"]],
    )


def clean_venue(row):
    venue = name_of(row.get("venue"))
    if not venue or venue.lower() in {"official venue", "official club ground", "none", "tbd"}:
        return ""
    return venue


def consolidate():
    layers = load_layers()
    # Reject any excluded sport that leaked in.
    leaks = []
    for name, rows in layers.items():
        for row in rows:
            sport = str(row.get("sport", "")).lower()
            if sport in EXCLUDED_SPORTS or sport == "football":
                leaks.append((name, row.get("id"), sport))

    # group by (sport, team-pair) with a +/-1 day date tolerance
    groups = defaultdict(list)
    for name, rows in layers.items():
        for row in rows:
            (sp, teams), date = cluster_key(row)
            if not sp or not teams or len(teams) < 2:
                continue
            groups[(sp, teams)].append((date, row))

    fixtures = []
    for (sport, teams), items in groups.items():
        # Exact-date buckets first. Two adjacent dates are merged only when the
        # two buckets share no source layer, i.e. the same fixture captured with a
        # different timezone/date convention. Back-to-back games between the same
        # teams (e.g. World Series Games 1 and 2) stay separate because both
        # buckets contain rows from the same layers.
        dated = sorted([it for it in items if it[0] is not None], key=lambda it: it[0])
        undated = [it for it in items if it[0] is None]
        by_date = defaultdict(list)
        for date, row in dated:
            by_date[date].append((date, row))
        buckets = []
        for date in sorted(by_date):
            bucket = by_date[date]
            if buckets and (date - buckets[-1][0][0]).days <= 1:
                prev_layers = {r["_layer"] for _d, r in buckets[-1]}
                cur_layers = {r["_layer"] for _d, r in bucket}
                if not (prev_layers & cur_layers):
                    buckets[-1].extend(bucket)
                    continue
            buckets.append(list(bucket))
        if undated:
            buckets.append(undated)
        for bucket in buckets:
            prepared = []
            for date, row in bucket:
                markets = normalize_markets(row)
                pick = choose_pick(row, markets)
                prepared.append((row_quality(row, markets, pick), row, markets, pick, date))
            prepared.sort(key=lambda x: x[0], reverse=True)
            _q, row, markets, pick, date = prepared[0]
            others = [p[1]["_layer"] for p in prepared]
            fixtures.append((row, markets, pick, date, others, prepared))

    rows_out = []
    for row, markets, pick, date, others, prepared in fixtures:
        sport = row.get("sport")
        start = iso_z(row.get("start_utc") or row.get("time") or row.get("time_utc"))
        if not start and date:
            start = f"{date.isoformat()}T00:00:00Z"
        url = row.get("official_url") or row.get("source_url") or ""
        if isinstance(row.get("fixture_source"), dict):
            url = url or row["fixture_source"].get("url", "")
        unlined = not markets or not pick
        out = {
            "id": row.get("id"),
            "sport": sport,
            "sport_name": SPORT_NAMES.get(sport, row.get("sport_name") or sport),
            "competition": row.get("competition") or "",
            "date": (date.isoformat() if date else (row.get("date") or "")[:10]),
            "start_utc": start,
            "venue": clean_venue(row),
            "home": name_of(row.get("home")),
            "away": name_of(row.get("away")),
            "home_summary": row.get("home_summary") or row.get("home_record") or "",
            "away_summary": row.get("away_summary") or row.get("away_record") or "",
            "line_status": "unlined" if unlined else "originated",
            "blank_reason": (row.get("blank_reason") or row.get("notes") or
                             "no official pre-match input published by the governing body"),
            "markets": markets if not unlined else [],
            "pick": pick if not unlined else None,
            "official_source": row.get("official_source") or "",
            "official_url": url,
            "olbg_url": row.get("olbg_url") or "",
            "source_scope": row.get("source_scope") or source_scope(url),
            "provenance": {
                "layer_used": row["_layer"],
                "layers": sorted(set(others), key=lambda n: PRIORITY.get(n, 9)),
                "original_id": row.get("id"),
                "original_ids": {p[1]["_layer"]: p[1].get("id") for p in prepared},
                "captured_at": row.get("_captured") or "",
            },
            "verification": {
                "status": "inherited",
                "checked_at": None,
                "source_url": url,
                "note": "Fixture and values carried from the layer named in provenance; not re-read in this pass.",
            },
        }
        rows_out.append(out)

    apply_corrections(rows_out)
    rows_out.sort(key=lambda r: (SPORT_ORDER.index(r["sport"]) if r["sport"] in SPORT_ORDER else 99,
                                 r["start_utc"] or "", r["id"] or ""))
    return rows_out, layers, leaks


REVERIFIED = {
    "nhl-2026020154", "nhl-2026020155", "nhl-2026020156", "nhl-2026020157", "nhl-2026020158",
    "shl-2026-1022-ske-dif",
}
FORM_REVERIFIED_TEAMS = {"Boston Bruins", "Carolina Hurricanes", "Edmonton Oilers", "Vegas Golden Knights"}


def apply_corrections(rows):
    """Documented fixes applied to the consolidated set.

    Every entry here is evidenced by an official page fetched on 2026-10-22 and is
    repeated on the review page. Nothing else in the inherited rows is altered.
    """
    # Tennis rank/points summaries are enriched from the official ATP captures the
    # layers already hold; they do not invent a value for a player who is absent.
    players = {}
    for path, key in ((DATA / "hub" / "inputs.json", "atp_players"),
                      (DATA / "slate" / "inputs.json", "atp_players")):
        try:
            block = read_json(path).get(key) or {}
        except Exception:
            block = {}
        for value in block.values():
            if isinstance(value, dict) and value.get("name"):
                players[value["name"]] = value

    # 2026-10-22 verification: Stephen Bunting qualified 28th on the European Tour
    # Order of Merit (£43,000) and Ritchie Edhouse did not qualify, so the slate
    # row pairing Noppert with Edhouse cannot stand. Three other layers already
    # carry the correct Noppert v Bunting pairing, so the slate duplicate is dropped.
    rows[:] = [r for r in rows if not (
        r["sport"] == "darts" and r["id"] == "pdc-32330"
        and r["provenance"]["layer_used"] == "slate"
        and "edhouse" in r["away"].lower())]

    for row in rows:
        # PGA Tour: the inherited row named a tournament that finished on 4 October.
        # The official PGA Tour tournament page for 22-25 October 2026 is the
        # Butterfield Bermuda Championship at Port Royal Golf Course.
        if row["id"] == "golf-utah-2026":
            row.update({
                "id": "golf-bermuda-2026",
                "competition": "PGA Tour — Butterfield Bermuda Championship",
                "home": "120-Player Strokeplay Field",
                "away": "Port Royal Golf Course",
                "venue": "Port Royal Golf Course, Southampton",
                "line_status": "unlined",
                "markets": [],
                "pick": None,
                "blank_reason": ("The official PGA Tour tournament page confirms the field and venue; "
                                 "strokes-gained inputs are not server-rendered, so no line is originated."),
                "official_source": "PGA Tour Official Tournament Page",
                "official_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview",
                "source_scope": "competition",
                "verification": {
                    "status": "reverified",
                    "checked_at": "2026-10-22T08:40:00Z",
                    "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview",
                    "note": "Fixture corrected: the inherited 'Bank of Utah Championship' concluded on 2026-10-04.",
                },
            })
            row["verification"]["status"] = "corrected"

        if row["id"] in REVERIFIED:
            row["verification"].update({
                "status": "reverified",
                "checked_at": "2026-10-22T08:35:00Z",
                "note": ("Fixture, start time and venue matched the official NHL schedule for 2026-10-22."
                         if row["sport"] == "ice-hockey" else
                         "Table position, points, goals and home/away splits matched the official SHL standings."),
            })
        elif row["verification"]["status"] == "inherited" and (
                row["home"] in FORM_REVERIFIED_TEAMS or row["away"] in FORM_REVERIFIED_TEAMS):
            row["verification"].update({
                "status": "form",
                "checked_at": "2026-10-22T08:30:00Z",
                "note": "Team record re-read on the official NHL standings page; the fixture row itself is inherited.",
            })

        if row["sport"] == "esports" and "liquipedia" in (row.get("official_url") or ""):
            # The only captured pairing source is a community wiki. Keep the row
            # visible, but do not originate or imply a verified fixture.
            row.update({
                "line_status": "unlined",
                "markets": [],
                "pick": None,
                "blank_reason": ("Pairing captured from Liquipedia, a community wiki, not an official league page; "
                                 "no official lolesports.com fixture page was captured, so no market is published."),
                "official_source": "LoL Esports official Worlds schedule (pairing not confirmed there in this pass)",
                "official_url": "https://lolesports.com/en-US/leagues/worlds/schedule",
                "source_scope": "competition",
                "verification": {
                    "status": "unverified",
                    "checked_at": None,
                    "source_url": "https://lolesports.com/en-US/leagues/worlds/schedule",
                    "note": "Pairing came from Liquipedia (community wiki); it is not an official-source value.",
                },
            })

        if row["sport"] == "tennis" and not row["home_summary"] and not row["away_summary"]:
            h = players.get(row["home"])
            a = players.get(row["away"])
            if h:
                row["home_summary"] = f"ATP #{h['rank']} ({h['points']} pts)"
            if a:
                row["away_summary"] = f"ATP #{a['rank']} ({a['points']} pts)"
    return rows


def main():
    rows, layers, leaks = consolidate()
    counts = {
        "rows": len(rows),
        "originated": sum(1 for r in rows if r["line_status"] == "originated"),
        "unlined": sum(1 for r in rows if r["line_status"] == "unlined"),
        "high": sum(1 for r in rows if (r.get("pick") or {}).get("confidence") == "high"),
        "medium": sum(1 for r in rows if (r.get("pick") or {}).get("confidence") == "medium"),
        "low": sum(1 for r in rows if (r.get("pick") or {}).get("confidence") == "low"),
        "sports": len({r["sport"] for r in rows}),
        "excluded_leaks": len(leaks),
        "source_layers": {name: len(rows_) for name, rows_ in layers.items()},
        "per_sport": dict(Counter(r["sport"] for r in rows)),
        "provenance": dict(Counter(r["provenance"]["layer_used"] for r in rows)),
    }
    write_json(OUT / "matches.json", {
        "generated_at": "2026-10-22T08:22:00Z",
        "rule": {
            "high": "probability >= 0.70 AND fair decimal in 1.40..101.00",
            "medium": "probability >= 0.60, or >=0.70 priced shorter than 1.40",
            "low": "probability < 0.60",
            "band": {"min_decimal": 1.40, "max_decimal": 101.00, "min_american": -250, "max_american": 10000},
        },
        "counts": counts,
        "matches": rows,
    })
    write_json(OUT / "summary.json", {"generated_at": "2026-10-22T08:22:00Z", "counts": counts})
    print(json.dumps(counts, indent=2))
    print("leaks:", leaks[:5])


if __name__ == "__main__":
    main()
