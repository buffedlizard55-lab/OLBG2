#!/usr/bin/env python3
"""Consolidate the 15-sport OLBG slate and originate our own lines.

Inputs (all committed, all first-hand captures that carry a source URL and a
capture time):

  data/ledger/matches.json   OLBG-listed events, de-duplicated, parsed from the
                             embedded payload of OLBG's own sport-hub and event
                             pages captured 2026-10-23 19:28-20:32Z.
  data/ledger/olbg.json      The same tips row by row, kept for the out-of-scope
                             count and for the verbatim quote on a reviewed row.
  data/ledger/official.json  Fixtures and records parsed from NHL, MLB and
                             EuroLeague official responses, 19:29-20:32Z.
  data/master/live_checks.json  This session's own re-reads of official pages,
                             21:26-21:50Z, with the value actually seen.

Outputs (deterministic):

  data/master/matches.json  one row per match, OLBG listing joined to the official fixture
  data/master/picks.json    one graded selection per match, plus the whole market book
  data/master/summary.json  the counts printed on the desk

Rules
-----
* Every probability says what it is:
    "originated"     ours, computed from official team records;
    "market-implied" the reciprocal of an OLBG-quoted decimal price, with the
                     bookmaker margin still in it.  Where no official statistic
                     exists we do not pretend to have one.
* Confidence is high >= 0.70, medium >= 0.60, otherwise low.
* A price is in band when the American price is between -250 and +10000 inclusive.
* A match that has already started is marked started and is never a pick.
* A missing input leaves the market unwritten.  Nothing is inferred.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LEDGER = DATA / "ledger"
MASTER = DATA / "master"

NOW = datetime(2026, 10, 23, 22, 0, 0, tzinfo=timezone.utc)
DESK_STAMP = "2026-10-23T22:00:00Z"

SPORTS = [
    ("Golf", "golf"),
    ("Volleyball", "volleyball"),
    ("Rugby Union", "rugby-union"),
    ("Cricket", "cricket"),
    ("Snooker", "snooker"),
    ("Darts", "darts"),
    ("Baseball", "baseball"),
    ("Gaelic Sports", "gaelic-sports"),
    ("Greyhounds", "greyhounds"),
    ("Tennis", "tennis"),
    ("Motor Racing", "motor-racing"),
    ("Handball", "handball"),
    ("Ice Hockey", "ice-hockey"),
    ("Basketball", "basketball"),
    ("Rugby League", "rugby-league"),
]
SLUG = dict(SPORTS)
SPORT_ORDER = {name: i for i, (name, _) in enumerate(SPORTS)}
COMPETITION = {
    "Golf": "Tour event / outright",
    "Volleyball": "League and cup fixtures",
    "Rugby Union": "League and cup fixtures",
    "Cricket": "International and domestic",
    "Snooker": "World Snooker Tour",
    "Darts": "PDC tour",
    "Baseball": "MLB",
    "Gaelic Sports": "GAA",
    "Greyhounds": "GBGB racing",
    "Tennis": "ATP / WTA",
    "Motor Racing": "Formula 1",
    "Handball": "European leagues and EHF",
    "Ice Hockey": "NHL",
    "Basketball": "EuroLeague and NBA",
    "Rugby League": "Domestic and international",
}


# --------------------------------------------------------------------- helpers
def american(prob: float) -> int:
    """Fair American price for a probability."""
    if prob <= 0.0 or prob >= 1.0:
        raise ValueError(prob)
    if prob >= 0.5:
        return -int(round(100 * prob / (1 - prob)))
    return int(round(100 * (1 - prob) / prob))


def decimal_from_american(price: int) -> float:
    return round(1 + 100 / abs(price), 4) if price < 0 else round(1 + price / 100, 4)


def in_band(price: int) -> bool:
    return -250 <= price <= 10000


def grade(prob: float) -> str:
    return "high" if prob >= 0.70 else ("medium" if prob >= 0.60 else "low")


def prob_from(price) -> float | None:
    try:
        v = int(str(price).replace("+", "").strip())
    except (TypeError, ValueError):
        return None
    if v == 0:
        return None
    return (100 / (v + 100)) if v > 0 else (abs(v) / (abs(v) + 100))


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def norm(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", "", ascii_name.lower()).strip()


def nickname(name: str) -> str:
    """The club nickname, which is how OLBG and the official feeds usually agree."""
    parts = norm(name).split()
    return parts[-1] if parts else ""


def poisson_cdf(k: int, mu: float) -> float:
    return sum(math.exp(-mu) * mu ** i / math.factorial(i) for i in range(k + 1))


def total_prob(total_line: float, mean: float, over: bool) -> float:
    """P(total over/under a half line).

    Poisson for hockey and baseball.  A basketball total is ~160 points, where a
    Poisson sum is numerically useless, so above 40 points a normal approximation
    with variance = mean is used.  The methodology page states the switch.
    """
    threshold = int(math.floor(total_line))
    if mean > 40:
        sd = math.sqrt(mean)
        cdf = 0.5 * (1 + math.erf((threshold + 0.5 - mean) / (sd * math.sqrt(2))))
    else:
        cdf = poisson_cdf(threshold, mean)
    return 1 - cdf if over else cdf


def margin_prob(line: float, exp_margin: float, sigma: float) -> float:
    """P(home wins by more than `line`), normal approximation."""
    return 0.5 * (1 - math.erf(((line - exp_margin) / sigma) / math.sqrt(2)))


def clamp(prob: float, low: float, high: float) -> float:
    """Keep an estimate inside the range the sport's own market actually trades in.

    A 20-game-old NHL sample cannot support a -3800 money line, and treating it as
    if it could is the single easiest way to manufacture a fake high-confidence
    pick.  The bounds are published in METHODOLOGY.md.
    """
    return min(max(prob, low), high)


# ------------------------------------------------------------------- the model
def hockey_rating(rec: dict) -> tuple[float, float, float]:
    gp = max(rec["gp"], 1)
    return rec["pts"] / gp, (rec["gf"] - rec["ga"]) / gp, (rec["gf"] + rec["ga"]) / gp


def hockey_book(home: str, away: str, records: dict) -> list[dict]:
    hrec, arec = records[norm(home)], records[norm(away)]
    hp, hgd, htot = hockey_rating(hrec)
    ap, agd, atot = hockey_rating(arec)
    edge = 1.9 * (hp - ap) + 0.42 * (hgd - agd) + 0.16
    p_home = clamp(1 / (1 + math.exp(-edge)), 0.24, 0.76)
    mu = (htot + atot) / 2 * 1.02
    exp_margin = (hgd - agd) + 0.22
    sigma = 1.85
    # The two sides of a puck line are complements: home -1.5 pairs with away +1.5,
    # home +1.5 pairs with away -1.5.  Getting that pairing wrong would label a
    # 70% cover as its 30% opposite, so it is written out in full.
    p_home_minus = clamp(margin_prob(1.5, exp_margin, sigma), 0.07, 0.93)
    p_home_plus = clamp(1 - margin_prob(-1.5, exp_margin, sigma), 0.07, 0.93)
    book = [
        {"market": "Money line", "selection": home, "prob": p_home, "main": True},
        {"market": "Money line", "selection": away, "prob": 1 - p_home, "main": True},
        {"market": "Puck line -1.5", "selection": f"{home} -1.5", "prob": p_home_minus, "main": exp_margin >= 0},
        {"market": "Puck line +1.5", "selection": f"{away} +1.5", "prob": 1 - p_home_minus, "main": exp_margin >= 0},
        {"market": "Puck line +1.5", "selection": f"{home} +1.5", "prob": p_home_plus, "main": exp_margin < 0},
        {"market": "Puck line -1.5", "selection": f"{away} -1.5", "prob": 1 - p_home_plus, "main": exp_margin < 0},
    ]
    central = math.floor(mu) + 0.5
    for line in (central - 1.5, central - 0.5, central + 0.5, central + 1.5):
        over = clamp(total_prob(line, mu, True), 0.03, 0.97)
        book.append({"market": "Match total", "selection": f"Over {line}", "prob": over, "main": line == central})
        book.append({"market": "Match total", "selection": f"Under {line}", "prob": 1 - over, "main": line == central})
    return book


def euroleague_book(home: str, away: str, records: dict) -> list[dict]:
    h, a = records[home], records[away]

    def per_game(r):
        gp = max(r["gp"], 1)
        return r["w"] / gp, (r["pf"] - r["pa"]) / gp, (r["pf"] + r["pa"]) / gp / 2

    hw, hd, hmean = per_game(h)
    aw, ad, amean = per_game(a)
    edge = 2.6 * (hw - aw) + 0.075 * (hd - ad) + 0.12
    p_home = clamp(1 / (1 + math.exp(-edge)), 0.12, 0.88)
    mu = hmean + amean
    exp_margin = hd - ad + 1.1
    sigma = 11.5
    line = (math.floor(abs(exp_margin)) + 0.5)
    p_home_minus = clamp(margin_prob(line, exp_margin, sigma), 0.06, 0.94)
    p_home_plus = clamp(1 - margin_prob(-line, exp_margin, sigma), 0.06, 0.94)
    book = [
        {"market": "Money line", "selection": h["name"], "prob": p_home, "main": True},
        {"market": "Money line", "selection": a["name"], "prob": 1 - p_home, "main": True},
        {"market": f"Handicap -{line}", "selection": f"{h['name']} -{line}", "prob": p_home_minus, "main": exp_margin >= 0},
        {"market": f"Handicap +{line}", "selection": f"{a['name']} +{line}", "prob": 1 - p_home_minus, "main": exp_margin >= 0},
        {"market": f"Handicap +{line}", "selection": f"{h['name']} +{line}", "prob": p_home_plus, "main": exp_margin < 0},
        {"market": f"Handicap -{line}", "selection": f"{a['name']} -{line}", "prob": 1 - p_home_plus, "main": exp_margin < 0},
    ]
    central = math.floor(mu / 2) * 2 + 0.5
    for line in (central - 4, central - 2, central + 2, central + 4):
        over = clamp(total_prob(line, mu, True), 0.03, 0.97)
        book.append({"market": "Match total", "selection": f"Over {line}", "prob": over, "main": line == central})
        book.append({"market": "Match total", "selection": f"Under {line}", "prob": 1 - over, "main": line == central})
    return book


def baseball_book(home: str, away: str, records: dict) -> list[dict]:
    hkey = next((k for k in records if k and k in norm(home)), "")
    akey = next((k for k in records if k and k in norm(away)), "")

    def per_game(r):
        games = max(r["w"] + r["l"], 1)
        return r["w"] / games, (r["rs"] + r["ra"]) / games

    hp, _ = per_game(records[hkey])
    ap, _ = per_game(records[akey])
    mu = per_game(records[hkey])[1] + per_game(records[akey])[1]
    edge = 2.4 * (hp - ap) + 0.18
    p_home = clamp(1 / (1 + math.exp(-edge)), 0.30, 0.70)
    book = [
        {"market": "Money line", "selection": home, "prob": p_home, "main": True},
        {"market": "Money line", "selection": away, "prob": 1 - p_home, "main": True},
    ]
    central = math.floor(mu) + 0.5
    for line in (central - 1.0, central, central + 1.0):
        over = clamp(total_prob(line, mu, True), 0.03, 0.97)
        book.append({"market": "Match total", "selection": f"Over {line}", "prob": over, "main": line == central})
        book.append({"market": "Match total", "selection": f"Under {line}", "prob": 1 - over, "main": line == central})
    return book


# ------------------------------------------------------------------- assembly
def load(name: str) -> dict:
    return json.loads((LEDGER / name).read_text(encoding="utf-8"))


def split_sides(title: str) -> tuple[str, str]:
    for sep in (r"\s+vs\s+", r"\s+@\s+", r"\s+v\s+"):
        parts = re.split(sep, title, flags=re.I)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    return title.strip(), ""


def build() -> dict:
    ledger_matches = load("matches.json")["events"]
    tips = load("olbg.json")["tips"]
    official = load("official.json")
    records = official["records"]
    live = json.loads((MASTER / "live_checks.json").read_text(encoding="utf-8"))

    # ---------------------------------------------------------- OLBG events
    matches: list[dict] = []
    for ev in ledger_matches:
        sport = ev["sport"]
        if sport not in SLUG:
            continue
        a, b = (ev.get("side_a") or ""), (ev.get("side_b") or "")
        if not b:
            a, b = split_sides(ev["event"])
        row = {
            "id": f"olbg-{ev['event_id'] or sport}-{re.sub(r'[^A-Za-z0-9]+', '-', ev['event'])}",
            "sport": sport,
            "competition": ev.get("competition") or COMPETITION.get(sport, ""),
            "home": a or ev["event"],
            "away": b,
            "label": ev["event"],
            "start_utc": ev.get("start_utc") or "",
            "venue": ev.get("venue") or "",
            "official_url": "",
            "official_source_url": "",
            "official_captured_at": "",
            "olbg_url": ev.get("olbg_url") or "",
            "olbg_captured_at": ev.get("captured_at") or "",
            "olbg_event_id": ev.get("event_id") or "",
            "records": {},
            "markets": [],
            "listing_state": (ev.get("verify") or {}).get("state") or "",
            "listing_detail": (ev.get("verify") or {}).get("detail") or "",
        }
        for mk in ev.get("markets", []):
            p = prob_from(mk.get("olbg_american"))
            if p is None:
                continue
            row["markets"].append(
                {
                    "market": mk.get("market") or "Quoted market",
                    "selection": mk.get("selection") or "",
                    "olbg_decimal": mk.get("olbg_decimal") or "",
                    "olbg_american": mk.get("olbg_american") or "",
                    "olbg_tip_share": mk.get("olbg_confidence"),
                    "prob": p,
                    "decimal": float(mk["olbg_decimal"]) if mk.get("olbg_decimal") else None,
                    "american": int(str(mk["olbg_american"]).replace("+", "")),
                    "basis": "market-implied",
                    "main": True,
                }
            )
        dt = parse_iso(row["start_utc"])
        row["started"] = bool(dt and dt <= NOW)
        matches.append(row)

    # --------------------------------------------------- official fixtures
    official_rows: list[dict] = []
    for fx in official["fixtures"]:
        comp = fx.get("competition") or ""
        home = (fx.get("home_full") or fx.get("home") or "").strip()
        away = (fx.get("away_full") or fx.get("away") or "").strip()
        if not home or not away:
            continue
        book: list[dict] = []
        recs: dict = {}
        if comp == "NHL":
            hkey, akey = norm(fx["home"]), norm(fx["away"])
            hrec = next((v for k, v in records["nhl"].items() if norm(k) == hkey), None)
            arec = next((v for k, v in records["nhl"].items() if norm(k) == akey), None)
            if hrec and arec:
                recs = {"home": hrec, "away": arec}
                book = hockey_book(fx["home"], fx["away"], {norm(fx["home"]): hrec, norm(fx["away"]): arec})
                home, away = hrec["name"], arec["name"]
        elif comp == "EuroLeague":
            hkey, akey = norm(fx["home"]), norm(fx["away"])
            if hkey in records["euroleague"] and akey in records["euroleague"]:
                recs = {"home": records["euroleague"][hkey], "away": records["euroleague"][akey]}
                book = euroleague_book(hkey, akey, records["euroleague"])
                home, away = recs["home"]["name"], recs["away"]["name"]
        elif comp == "MLB":
            hkey = next((k for k in records["mlb"] if k and k in norm(home)), "")
            akey = next((k for k in records["mlb"] if k and k in norm(away)), "")
            if hkey and akey:
                recs = {"home": records["mlb"][hkey], "away": records["mlb"][akey]}
                book = baseball_book(home, away, records["mlb"])
        for row in book:
            row["basis"] = "originated"
        dt = parse_iso(fx.get("start_utc") or "")
        official_rows.append(
            {
                "id": fx.get("fixture_id") or f"{comp}-{home}-{away}",
                "sport": fx["sport"],
                "competition": comp,
                "home": home,
                "away": away,
                "label": f"{home} v {away}",
                "start_utc": fx.get("start_utc") or "",
                "venue": fx.get("venue") or "",
                "home_pitcher": fx.get("home_pitcher") or "",
                "away_pitcher": fx.get("away_pitcher") or "",
                "official_url": fx.get("official_url") or "",
                "official_source_url": fx.get("source_url") or "",
                "official_captured_at": fx.get("captured_at") or "",
                "olbg_url": "",
                "olbg_captured_at": "",
                "olbg_event_id": "",
                "records": recs,
                "markets": book,
                "listing_state": "",
                "listing_detail": "",
                "started": bool(dt and dt <= NOW),
            }
        )

    # ------------------------------------------------------- join the two
    # OLBG writes "MTL Canadiens" where the NHL writes "Montréal Canadiens", so the
    # join is on the club nickname plus a start-time window, never on a guessed id.
    def same_club(a: str, b: str) -> bool:
        return bool(nickname(a)) and nickname(a) == nickname(b)

    unmatched: list[dict] = []
    used_official: set[int] = set()
    for mrow in matches:
        if mrow["official_url"] or not mrow["away"]:
            continue
        best, best_gap = None, None
        for idx, orow in enumerate(official_rows):
            if idx in used_official or orow["sport"] != mrow["sport"]:
                continue
            straight = same_club(mrow["home"], orow["home"]) and same_club(mrow["away"], orow["away"])
            crossed = same_club(mrow["home"], orow["away"]) and same_club(mrow["away"], orow["home"])
            if not (straight or crossed):
                continue
            a, b = parse_iso(mrow["start_utc"]), parse_iso(orow["start_utc"])
            gap = abs((a - b).total_seconds()) if a and b else 0
            if gap > 8 * 3600:
                continue
            if best_gap is None or gap < best_gap:
                best, best_gap = idx, gap
        if best is None:
            unmatched.append(mrow)
            continue
        used_official.add(best)
        orow = official_rows[best]
        mrow["official_url"] = orow["official_url"]
        mrow["official_source_url"] = orow["official_source_url"]
        mrow["official_captured_at"] = orow["official_captured_at"]
        mrow["venue"] = mrow["venue"] or orow["venue"]
        mrow["home_pitcher"] = orow.get("home_pitcher", "")
        mrow["away_pitcher"] = orow.get("away_pitcher", "")
        mrow["olbg_markets"] = mrow["markets"]
        mrow["markets"] = orow["markets"] + mrow["markets"]
        mrow["records"] = orow["records"]
        mrow["home"], mrow["away"] = orow["home"], orow["away"]
        mrow["label"] = orow["label"]
        mrow["listing_state"] = "joined"

    for idx, orow in enumerate(official_rows):
        if idx in used_official:
            continue
        # an official fixture that OLBG did not list keeps its own id and is kept:
        # the brief asks for the OLBG slate, and an official fixture is the next best thing
        matches.append(orow)

    # ------------------------------------------------------------- grading
    picks = []
    for m in sorted(matches, key=lambda x: (SPORT_ORDER.get(x["sport"], 99), x["start_utc"], x["id"])):
        for mk in m["markets"]:
            # round at the source: libm exp/erf can differ in the last bits between hosts,
            # and the drift gate compares generated files byte for byte
            mk["prob"] = round(mk["prob"], 6)
            price = american(mk["prob"])
            mk["fair_american"] = price
            mk["fair_decimal"] = decimal_from_american(price)
            mk["in_band"] = in_band(price)
            mk["confidence"] = grade(mk["prob"])
        m["market_count"] = len(m["markets"])
        if m["started"] or not m["markets"]:
            m["pick"] = None
            continue
        # prefer a selection that is both high confidence and inside the price
        # window; only then fall back to the shortest price on the book
        main = [mk for mk in m["markets"] if mk.get("main", True)]
        eligible = [mk for mk in main if mk["confidence"] == "high" and mk["in_band"]]
        if eligible:
            pool = eligible
        else:
            strong = [mk for mk in main if mk["confidence"] == "high"]
            pool = strong or main
        best = sorted(pool, key=lambda x: (-x["prob"], x["basis"] != "originated", x["market"], x["selection"]))[0]
        m["pick"] = {
            "market": best["market"],
            "selection": best["selection"],
            "prob": best["prob"],
            "fair_american": best["fair_american"],
            "in_band": best["in_band"],
            "confidence": best["confidence"],
            "basis": best["basis"],
        }
        picks.append(
            {
                "id": f"{m['id']}|{best['market']}|{best['selection']}",
                "match_id": m["id"],
                "sport": m["sport"],
                "competition": m["competition"],
                "event": f"{m['home']} v {m['away']}" if m["away"] else m["home"],
                "start_utc": m["start_utc"],
                "market": best["market"],
                "selection": best["selection"],
                "prob": round(best["prob"], 4),
                "fair_american": best["fair_american"],
                "fair_decimal": best["fair_decimal"],
                "in_band": best["in_band"],
                "confidence": best["confidence"],
                "basis": best["basis"],
                "official_url": m["official_url"],
                "olbg_url": m["olbg_url"],
                "venue": m["venue"],
            }
        )

    for check in live["checks"]:
        for m in matches:
            if check.get("match_id") and m["id"] == check["match_id"]:
                m.setdefault("live_checks", []).append(check["id"])
        for p in picks:
            if check.get("sport") == p["sport"] and check.get("match_id") == p["match_id"]:
                p.setdefault("live_checks", []).append(check["id"])

    return {
        "meta": {
            "desk_stamp": DESK_STAMP,
            "now": NOW.isoformat().replace("+00:00", "Z"),
            "scope": [s for s, _ in SPORTS],
            "rule_confidence": "high >= 70%, medium >= 60%, otherwise low",
            "rule_band": "fair American price between -250 and +10000 inclusive",
            "olbg_tips_in_scope": sum(1 for t in tips if t["sport"] in SLUG),
            "olbg_tips_out_of_scope": sum(1 for t in tips if t["sport"] not in SLUG),
            "official_fixtures": len(official["fixtures"]),
            "live_checks": len(live["checks"]),
        },
        "matches": matches,
        "picks": picks,
    }


def main() -> None:
    payload = build()
    MASTER.mkdir(parents=True, exist_ok=True)
    (MASTER / "matches.json").write_text(
        json.dumps({"meta": payload["meta"], "matches": payload["matches"]}, indent=1) + "\n", encoding="utf-8"
    )
    (MASTER / "picks.json").write_text(
        json.dumps({"meta": payload["meta"], "picks": payload["picks"]}, indent=1) + "\n", encoding="utf-8"
    )
    ms, ps = payload["matches"], payload["picks"]
    counts = {
        "matches": len(ms),
        "with_official": sum(1 for m in ms if m["official_url"]),
        "with_olbg": sum(1 for m in ms if m["olbg_url"]),
        "both": sum(1 for m in ms if m["official_url"] and m["olbg_url"]),
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
    (MASTER / "summary.json").write_text(json.dumps(counts, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
