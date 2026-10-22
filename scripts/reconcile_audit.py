#!/usr/bin/env python3
"""Cross-layer reconciliation audit for the OLBG2 repository.

Reads every published data layer (read-only), normalises each row into one common
record, and reports *mechanical* defects that no single layer can see:

  C1  overlap       the same fixture published by more than one layer
  C2  price         the same team priced differently by different layers
  C3  grade         the same fixture/selection graded at different confidence
  C4  non-fixture   published "matches" that are not head-to-head fixtures
                    (outrights, tournament fields, venue-vs-field, race cards)
  C5  stale         fixture date before the layer's own capture stamp / the audit date
  C6  citation      shared, missing or non-governing-body source URLs
  C7  prediction    word count, duplication, explicit selection, band compliance
  C8  one URL, incompatible pairings (fixture-scoped citations only)
  C9  the same fixture twice inside one layer
  C10 scope         excluded sports, and eligible-sport coverage

The audit never writes outside its own scope:
  data/reconcile/rows.json    normalised rows (one per published row)
  data/reconcile/report.json  summary + findings

Standard library only. Deterministic: no clock, no network, no randomness.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "reconcile")

AUDIT_DATE = "2026-10-22"  # fixed audit date; never read from the clock

EXCLUDED_SLUGS = {
    "soccer", "football", "boxing", "ufc", "mma", "american-football",
    "hurling", "horse-racing", "cycling", "specials",
}
ELIGIBLE_SLUGS = [
    "aussie-rules", "baseball", "basketball", "cricket", "darts", "esports",
    "gaelic-football", "golf", "greyhounds", "handball", "ice-hockey",
    "motor-racing", "rugby-league", "rugby-union", "snooker", "tennis", "volleyball",
]

OFFICIAL_HOSTS = {
    "www.nhl.com", "api-web.nhle.com", "api.nhle.com", "www.nba.com", "cdn.nba.com",
    "www.euroleaguebasketball.net", "api-live.euroleague.net", "www.atptour.com",
    "www.wtatennis.com", "www.pdc.tv", "stats.unitedrugby.com", "www.gbgb.org.uk",
    "stats.swehockey.se", "ehfcl.eurohandball.com", "www.formula1.com",
    "www.afl.com.au", "prod2.lnr.fr", "top14.lnr.fr", "www.wst.tv", "lolesports.com",
    "www.mlb.com", "www.nrl.com", "www.legavolley.it", "www.gaa.ie",
    "www.icc-cricket.com", "www.pgatour.com", "www.plusliga.pl",
    "www.europeantour.com", "www.superleague.co.uk", "www.olbg.com",
    "www.espncricinfo.com", "stats.rugbyleague.com", "www.rugby-league.com",
    "www.world.rugby", "www.rugbyworldcup.com", "www.eurohandball.com",
}

ALIASES = {
    "la clippers": "los angeles clippers",
    "la lakers": "los angeles lakers",
    "ny rangers": "new york rangers",
    "ny islanders": "new york islanders",
    "nj devils": "new jersey devils",
    "barca": "barcelona",
    "fc barcelona": "barcelona",
}


# --------------------------------------------------------------------------- #
# scalars, names, dates
# --------------------------------------------------------------------------- #
def _s(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("name", "default", "team", "label", "full_name"):
            if value.get(key):
                return _s(value.get(key))
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(_s(v) for v in value if _s(v))
    return str(value).strip()


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def norm_name(name) -> str:
    s = strip_accents(_s(name)).lower()
    if not s:
        return ""
    s = re.sub(r"\s*\([^)]*\)", " ", s)
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # strip common market suffixes that appear inside outcome labels
    s = re.sub(r"\s+(ml|moneyline|to win|win match)$", "", s)
    return ALIASES.get(s, s)


def sport_slug(sport) -> str:
    s = _s(sport).lower().replace("_", " ")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def as_date(value) -> str:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", _s(value))
    return m.group(0) if m else ""


def host_of(url) -> str:
    m = re.match(r"https?://([^/]+)", _s(url), re.I)
    return (m.group(1) if m else "").lower()


def fnum(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def dec_from_american(am):
    a = fnum(am)
    if a is None or a == 0:
        return None
    return round(1 + a / 100.0, 2) if a > 0 else round(1 + 100.0 / abs(a), 2)


# --------------------------------------------------------------------------- #
# club codes used by the /site/ desk layer
# --------------------------------------------------------------------------- #
def _read_json(rel):
    full = os.path.join(ROOT, rel)
    if not os.path.exists(full):
        return None
    with open(full, encoding="utf-8") as fh:
        return json.load(fh)


def load_abbreviations() -> dict:
    """Club code -> club name, from the repository's own captured team tables."""
    out = {}
    doc = _read_json("data/desk/nhl_teams.json")
    if isinstance(doc, dict):
        teams = doc.get("teams") or {}
        if isinstance(teams, dict):
            for code, meta in teams.items():
                if isinstance(meta, dict) and meta.get("name"):
                    out[str(code).upper()] = meta["name"]
    doc = _read_json("data/inputs/nhl_teams.json")
    if isinstance(doc, dict):
        for key in ("teams", "nhl_teams"):
            teams = doc.get(key)
            if isinstance(teams, dict):
                for code, meta in teams.items():
                    if isinstance(meta, dict):
                        name = meta.get("name") or meta.get("team_name") or meta.get("full_name")
                        if name:
                            out.setdefault(str(code).upper(), name)
            elif isinstance(teams, list):
                for meta in teams:
                    if isinstance(meta, dict):
                        code = meta.get("abbr") or meta.get("triCode") or meta.get("code")
                        name = meta.get("name") or meta.get("team_name") or meta.get("full_name")
                        if code and name:
                            out.setdefault(str(code).upper(), name)
    return out


ABBREV = load_abbreviations()


def expand_side(side) -> str:
    s = _s(side)
    if 2 <= len(s) <= 4 and re.fullmatch(r"[A-Z]{2,4}", s) and s in ABBREV:
        return ABBREV[s]
    return s


# --------------------------------------------------------------------------- #
# classification: head-to-head fixture or not
# --------------------------------------------------------------------------- #
FIELD_PATTERNS = [
    (r"\boutright\b", "outright / futures market, not a fixture"),
    (r"strokeplay field", "tournament field, not a fixture"),
    (r"\bfield\b", "a 'field' is quoted as a competitor"),
    (r"race card|trap card", "race-meeting card, not a head-to-head fixture"),
    (r"licensed meeting", "race meeting, not a head-to-head fixture"),
    (r"\bdraw\b", "draw / bracket entry, not a fixture"),
    (r"\bchasing pack\b", "chasing pack, not a single opponent"),
    (r"\b(grid|contender field)\b", "grid / contender group, not a single opponent"),
    (r"^\d+[- ](player|driver|club|team|runner|bowler|trap)", "field size quoted as a competitor"),
]


def classify(home, away, competition) -> tuple[str, str]:
    h, a, c = _s(home), _s(away), _s(competition)
    low = " ".join([h, a, c]).lower()
    for pattern, reason in FIELD_PATTERNS:
        if re.search(pattern, low):
            return "non_fixture", reason
    for side, label in ((h, "home"), (a, "away")):
        if re.search(r"\s+v\s+", side, re.I):
            return "non_fixture", f"nested 'v' inside the {label} name"
    if re.search(r"\b(golf course|racecourse)\b", low):
        return "non_fixture", "venue framed as a competitor"
    if not h or not a:
        return "incomplete", "one side is blank"
    if norm_name(h) == norm_name(a):
        return "non_fixture", "identical sides"
    return "fixture", ""


# --------------------------------------------------------------------------- #
# market parsing (five different published shapes)
# --------------------------------------------------------------------------- #
PROB_KEYS = ("probability", "prob", "fair_prob", "p", "model_prob")
DEC_KEYS = ("fair_decimal", "decimal", "fair_dec", "dec", "fair_odds", "price", "odds")
AM_KEYS = ("fair_american", "american", "fair_am", "book_am_int")


def _outcome(o: dict) -> dict:
    if not isinstance(o, dict):
        return {"label": "", "prob": None, "dec": None, "am": None, "book_dec": None}
    prob = next((fnum(o[k]) for k in PROB_KEYS if fnum(o.get(k)) is not None), None)
    dec = next((fnum(o[k]) for k in DEC_KEYS if fnum(o.get(k)) is not None), None)
    am = next((o[k] for k in AM_KEYS if o.get(k) is not None), None)
    if dec is None and am is not None:
        dec = dec_from_american(am)
    return {"label": _s(o.get("label") or o.get("selection") or o.get("name") or o.get("team")),
            "prob": prob, "dec": dec, "am": am,
            "book_dec": fnum(o.get("book_dec"))}


def _market_bucket(name: str) -> str:
    n = (name or "").lower()
    if any(k in n for k in ("moneyline", "match winner", "winner", "win match", "1x2", "head to head")):
        return "moneyline"
    if any(k in n for k in ("handicap", "spread", "puck", "run line", "set handicap", "frame", "leg")):
        return "handicap"
    if any(k in n for k in ("total", "over/under", "o/u", "points")):
        return "total"
    return "other"


def extract_markets(row: dict) -> dict:
    """Return {'moneyline':[outcome...], 'handicap':[...], 'total':[...], 'names':[...],
    'book_prices': bool} from any of the published market shapes."""
    out = {"moneyline": [], "handicap": [], "total": [], "other": [], "names": [],
           "book_prices": False}
    markets = row.get("markets")

    if isinstance(markets, list):
        if markets and all(isinstance(m, dict) and "outcomes" not in m and "home" not in m
                           for m in markets):
            # flat list of individual selections: {market, selection, probability, price}
            grouped = defaultdict(list)
            for m in markets:
                grouped[_market_bucket(_s(m.get("market")))].append(m)
            for bucket, items in grouped.items():
                out[bucket] = [{"label": _s(i.get("selection")), "prob": fnum(i.get("probability")),
                                "dec": fnum(i.get("price")), "am": None,
                                "book_dec": fnum(i.get("book_dec"))} for i in items]
                out["names"].append(bucket)
                out["book_prices"] = out["book_prices"] or any(i.get("book_dec") for i in items)
        else:
            for m in markets:
                if not isinstance(m, dict):
                    continue
                name = _s(m.get("market") or m.get("name") or m.get("type"))
                bucket = _market_bucket(name)
                out["names"].append(name or bucket)
                if isinstance(m.get("outcomes"), list):
                    out[bucket].extend(_outcome(o) for o in m["outcomes"])
                elif isinstance(m.get("home"), dict) or isinstance(m.get("away"), dict):
                    for side in ("home", "away", "over", "under", "draw"):
                        if isinstance(m.get(side), dict):
                            oc = _outcome(m[side])
                            if not oc["label"]:
                                oc["label"] = _s(m.get("label")) + " " + side
                            out[bucket].append(oc)
    elif isinstance(markets, dict):
        for key, val in markets.items():
            bucket = _market_bucket(key)
            out["names"].append(key)
            if isinstance(val, dict) and isinstance(val.get("outcomes"), list):
                out[bucket].extend(_outcome(o) for o in val["outcomes"])
            elif isinstance(val, dict):
                for side in ("home", "away", "over", "under", "draw"):
                    if isinstance(val.get(side), dict):
                        oc = _outcome(val[side])
                        if not oc["label"]:
                            oc["label"] = side
                        out[bucket].append(oc)
            elif isinstance(val, list):
                out[bucket].extend(_outcome(o) for o in val)

    # per-market dicts used by /verified/, /board/, /forward/
    for key, bucket in (("winner_market", "moneyline"), ("handicap_market", "handicap"),
                        ("total_market", "total")):
        m = row.get(key)
        if not isinstance(m, dict):
            continue
        out["names"].append(key)
        pairs = [("home", "home_odds", "home_prob"), ("away", "away_odds", "away_prob")]
        if bucket == "handicap":
            pairs = [("fav", "fav_odds", "fav_prob"), ("dog", "dog_odds", "dog_prob")]
        if bucket == "total":
            pairs = [("over", "over_odds", "over_prob"), ("under", "under_odds", "under_prob")]
        got = []
        for side, dec_key, prob_key in pairs:
            dec = fnum(m.get(dec_key))
            prob = fnum(m.get(prob_key))
            if dec is not None or prob is not None:
                got.append({"label": side if bucket != "moneyline" else _s(m.get(side + "_name")) or side,
                            "prob": prob, "dec": dec, "am": None, "book_dec": None})
        if got:
            out[bucket].extend(got)
    return out


def _pair_to_home_away(markets: dict, home: str, away: str) -> dict:
    """Map moneyline outcomes onto home/away using the label, falling back to order."""
    hn, an = norm_name(home), norm_name(away)
    dec = {"home": None, "away": None}
    prob = {"home": None, "away": None}
    outs = markets.get("moneyline") or []
    if len(outs) == 2:
        for o in outs:
            label = norm_name(o["label"])
            side = None
            if label and (label == hn or hn.startswith(label) or label.startswith(hn)):
                side = "home"
            elif label and (label == an or an.startswith(label) or label.startswith(an)):
                side = "away"
            if side and dec[side] is None:
                dec[side], prob[side] = o["dec"], o["prob"]
        if dec["home"] is None and dec["away"] is None and outs[0]["label"] in ("", "home"):
            dec = {"home": outs[0]["dec"], "away": outs[1]["dec"]}
            prob = {"home": outs[0]["prob"], "away": outs[1]["prob"]}
    return {"dec": dec, "prob": prob, "count": len(outs)}


def _pick_of(row: dict) -> dict | None:
    p = row.get("pick") or row.get("winner_pick") or row.get("recommended_pick")
    if isinstance(p, str):
        p = {"selection": p}
    if not isinstance(p, dict):
        return None
    sel = _s(p.get("selection") or p.get("label") or p.get("team") or p.get("market"))
    prob = next((fnum(p[k]) for k in ("probability", "prob") if fnum(p.get(k)) is not None), None)
    if prob is None:
        prob = fnum(row.get("winner_prob"))
    dec = next((fnum(p[k]) for k in ("fair_decimal", "fair_odds", "fair_dec") if fnum(p.get(k)) is not None), None)
    am = p.get("fair_american") or p.get("fair_am")
    if dec is None and am is not None:
        dec = dec_from_american(am)
    conf = p.get("confidence") or row.get("confidence") or row.get("confidence_tier")
    return {"selection": sel, "probability": prob, "decimal": dec, "american": am,
            "confidence": (conf or "").lower() or None}


# --------------------------------------------------------------------------- #
# layer loading
# --------------------------------------------------------------------------- #
LAYER_FILES = [
    ("root", "data/matches.json"),
    ("verified", "data/verified/matches.json"),
    ("board", "data/board/matches.json"),
    ("forward", "data/forward/matches.json"),
    ("hub", "data/hub/matches.json"),
    ("slate", "data/slate/matches.json"),
    ("portal", "data/portal/matches.json"),
    ("final", "data/final/matches.json"),
    ("desk", "data/desk/fixtures.json"),
    ("live", "data/live/lines.json"),
    ("survey", "data/survey/lines.json"),
]


def rows_of(doc) -> list:
    if isinstance(doc, list):
        return doc
    if not isinstance(doc, dict):
        return []
    for key in ("matches", "rows", "fixtures", "selections", "lines", "events"):
        v = doc.get(key)
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    for v in doc.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def stamp_of(doc) -> str:
    if not isinstance(doc, dict):
        return ""
    for key in ("generated_at", "captured_at", "generated_utc", "as_of", "written_utc"):
        d = as_date(doc.get(key))
        if d:
            return d
    meta = doc.get("meta")
    if isinstance(meta, dict):
        for key in ("generated_at", "captured_at", "as_of"):
            d = as_date(meta.get(key))
            if d:
                return d
    return ""


def normalise_row(layer: str, row: dict, stamp: str) -> dict:
    home = expand_side(_s(row.get("home") or row.get("home_name") or row.get("side_a")))
    away = expand_side(_s(row.get("away") or row.get("away_name") or row.get("away_team") or row.get("side_b")))
    comp = _s(row.get("competition") or row.get("league") or row.get("event"))
    if not comp and row.get("match"):
        comp = _s(row.get("match"))
    d = (as_date(row.get("date")) or as_date(row.get("start_utc")) or as_date(row.get("time"))
         or as_date(row.get("time_utc")) or as_date(row.get("start_display")))
    url = _s(row.get("official_url") or row.get("source_url") or row.get("source"))

    markets = extract_markets(row)
    ml = _pair_to_home_away(markets, home, away)
    cls, reason = classify(home, away, comp)

    return {
        "layer": layer,
        "id": _s(row.get("id") or row.get("match_id") or row.get("fixture_id")),
        "sport": sport_slug(row.get("sport")),
        "sport_raw": _s(row.get("sport")),
        "competition": comp,
        "date": d,
        "time": _s(row.get("start_utc") or row.get("time_utc") or row.get("time")),
        "home": home,
        "away": away,
        "home_norm": norm_name(home),
        "away_norm": norm_name(away),
        "venue": _s(row.get("venue")),
        "official_url": url,
        "host": host_of(url),
        "line_status": _s(row.get("line_status") or row.get("status")),
        "ml_dec": [ml["dec"]["home"], ml["dec"]["away"]],
        "ml_prob": [ml["prob"]["home"], ml["prob"]["away"]],
        "ml_outcomes": ml["count"],
        "handicap": markets["handicap"][:4],
        "total": markets["total"][:4],
        "market_names": markets["names"],
        "other_markets": [o["label"] for o in markets["other"] if o.get("label")][:6],
        "publishes_book_price": markets["book_prices"],
        "pick": _pick_of(row),
        "class": cls,
        "class_reason": reason,
        "capture_date": stamp,
        "scope": _s(row.get("source_scope")),
    }


def fixture_key(r: dict) -> tuple:
    return (r["sport"], r["date"], tuple(sorted([r["home_norm"], r["away_norm"]])))


# --------------------------------------------------------------------------- #
# predictions
# --------------------------------------------------------------------------- #
PRED_FILES = [
    ("final", "data/final/predictions.json"),
    ("verified", "data/verified/predictions.json"),
    ("portal", "data/portal/predictions.json"),
    ("hub", "data/hub/predictions.json"),
    ("board", "data/board/predictions.json"),
    ("forward", "data/forward/predictions.json"),
    ("slate", "data/slate/predictions.json"),
    ("live", "data/live/predictions.json"),
    ("survey", "data/survey/predictions.json"),
]
MARKET_WORDS = ["over", "under", "handicap", "spread", "to win", "win", "moneyline",
                "beat", "cover", "outright", "total", "points"]


def load_predictions() -> list:
    preds = []
    for layer, path in PRED_FILES:
        doc = _read_json(path)
        for p in rows_of(doc):
            text = _s(p.get("text") or p.get("prediction") or p.get("analysis"))
            sel = _s(p.get("selection") or p.get("team_focus"))
            dec = next((fnum(p[k]) for k in ("fair_decimal", "fair_dec", "fair_odds")
                        if fnum(p.get(k)) is not None), None)
            am = p.get("fair_american") or p.get("fair_am")
            if dec is None and am is not None:
                dec = dec_from_american(am)
            preds.append({
                "layer": layer,
                "match_id": _s(p.get("match_id") or p.get("fixture_id") or p.get("id")),
                "sport": sport_slug(p.get("sport")),
                "selection": sel,
                "market": _s(p.get("market")),
                "confidence": _s(p.get("confidence") or p.get("confidence_tier")).lower(),
                "probability": next((fnum(p[k]) for k in ("probability", "prob")
                                     if fnum(p.get(k)) is not None), None),
                "decimal": dec,
                "text": text,
                "words": len(re.findall(r"[A-Za-z0-9'\-]+", text)),
                "official_url": _s(p.get("official_url") or p.get("source_url")),
            })
    return preds


# --------------------------------------------------------------------------- #
# audit
# --------------------------------------------------------------------------- #
def main() -> int:
    layers, rows, layer_meta = {}, [], {}
    for layer, path in LAYER_FILES:
        doc = _read_json(path)
        if doc is None:
            layer_meta[layer] = {"path": path, "present": False}
            continue
        stamp = stamp_of(doc)
        rs = [normalise_row(layer, r, stamp) for r in rows_of(doc)]
        layers[layer] = rs
        rows.extend(rs)
        layer_meta[layer] = {"path": path, "present": True, "rows": len(rs), "capture_date": stamp}

    findings = defaultdict(list)
    by_key = defaultdict(list)
    for r in rows:
        if r["class"] == "fixture" and r["date"]:
            by_key[fixture_key(r)].append(r)
    overlap_groups = {k: v for k, v in by_key.items() if len({r["layer"] for r in v}) > 1}

    # C1 overlap -----------------------------------------------------------
    for k, v in sorted(overlap_groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        findings["overlap"].append({
            "sport": k[0], "date": k[1], "sides": list(k[2]),
            "layer_count": len({r["layer"] for r in v}),
            "rows": [{"layer": r["layer"], "id": r["id"], "home": r["home"], "away": r["away"],
                      "pick": (r["pick"] or {}).get("selection"),
                      "pick_dec": (r["pick"] or {}).get("decimal"),
                      "ml_dec": r["ml_dec"]} for r in v],
        })
    # distribution of how many layers a fixture appears in
    findings["overlap_depth"] = dict(sorted(Counter(
        len({r["layer"] for r in v}) for v in overlap_groups.values()).items()))

    # C2 price conflicts ---------------------------------------------------
    price_conflicts = []
    for k, v in overlap_groups.items():
        per_team = defaultdict(list)
        for r in v:
            for idx, team in enumerate((r["home_norm"], r["away_norm"])):
                d = r["ml_dec"][idx] if r["ml_dec"] else None
                if d:
                    per_team[team].append((r["layer"], r["id"], d))
        for team, items in per_team.items():
            vals = {round(i[2], 3) for i in items}
            if len(vals) > 1:
                price_conflicts.append({
                    "sport": k[0], "date": k[1], "team": team,
                    "values": [{"layer": i[0], "id": i[1], "decimal": i[2]} for i in items],
                    "spread": round(max(vals) - min(vals), 3),
                })
    findings["price_conflict"] = sorted(price_conflicts, key=lambda x: -x["spread"])

    # C3 confidence conflicts ----------------------------------------------
    conf_conflicts = []
    for k, v in overlap_groups.items():
        grades = defaultdict(set)
        for r in v:
            p = r["pick"] or {}
            if p.get("selection") and p.get("confidence"):
                grades[norm_name(p["selection"])].add((p["confidence"], r["layer"]))
        for sel, g in grades.items():
            if len({t[0] for t in g}) > 1:
                conf_conflicts.append({
                    "sport": k[0], "date": k[1], "selection": sel,
                    "grades": sorted([{"confidence": t[0], "layer": t[1]} for t in g],
                                     key=lambda x: x["layer"]),
                })
    findings["confidence_conflict"] = conf_conflicts

    # C4 non-fixture rows --------------------------------------------------
    for r in rows:
        if r["class"] != "fixture":
            findings["non_fixture"].append({
                "layer": r["layer"], "id": r["id"], "sport": r["sport"], "date": r["date"],
                "competition": r["competition"], "home": r["home"], "away": r["away"],
                "reason": r["class_reason"], "status": r["line_status"],
                "official_url": r["official_url"],
            })

    # C5 stale / undated ---------------------------------------------------
    for r in rows:
        if not r["date"]:
            findings["undated"].append({"layer": r["layer"], "id": r["id"], "sport": r["sport"],
                                        "home": r["home"], "away": r["away"],
                                        "why": "no fixture date published on the row"})
        elif r["capture_date"] and r["date"] < r["capture_date"]:
            findings["stale"].append({"layer": r["layer"], "id": r["id"], "sport": r["sport"],
                                      "date": r["date"], "capture_date": r["capture_date"],
                                      "home": r["home"], "away": r["away"],
                                      "why": "fixture dated before the layer's own capture stamp"})
        elif r["date"] < AUDIT_DATE:
            findings["stale"].append({"layer": r["layer"], "id": r["id"], "sport": r["sport"],
                                      "date": r["date"], "capture_date": r["capture_date"],
                                      "home": r["home"], "away": r["away"],
                                      "why": "fixture dated before the audit date, still published as scheduled"})

    # C6 citations ---------------------------------------------------------
    url_rows = defaultdict(list)
    for r in rows:
        if r["official_url"]:
            url_rows[r["official_url"]].append(r)
    findings["citation"] = {
        "rows_with_url": sum(1 for r in rows if r["official_url"]),
        "rows_without_url": sum(1 for r in rows if not r["official_url"]),
        "distinct_urls": len(url_rows),
        "fixture_scope_rows": sum(1 for r in rows if r.get("scope") == "fixture"),
        "competition_scope_rows": sum(1 for r in rows if r.get("scope") == "competition"),
        "shared_urls": [
            {"url": u, "rows": len(v), "layers": sorted({r["layer"] for r in v}),
             "sports": sorted({r["sport"] for r in v})}
            for u, v in sorted(url_rows.items(), key=lambda kv: -len(kv[1])) if len(v) > 1
        ][:40],
        "non_official_hosts": [
            {"host": h, "rows": c} for h, c in Counter(
                r["host"] or "(no host)" for r in rows
                if r["official_url"] and r["host"] not in OFFICIAL_HOSTS).most_common()],
        "hosts": [{"host": h, "rows": c} for h, c in
                  Counter(r["host"] for r in rows if r["host"]).most_common()],
    }

    # C7 predictions -------------------------------------------------------
    preds = load_predictions()
    texts = Counter(p["text"].strip() for p in preds if p["text"].strip())
    openings = Counter(" ".join(re.findall(r"[A-Za-z0-9'\-]+", p["text"])[:3]).lower()
                       for p in preds if p["text"].strip())
    pred_rows = []
    for p in preds:
        low = p["text"].lower()
        first = norm_name(p["selection"]).split()[0] if norm_name(p["selection"]) else ""
        pred_rows.append({
            **p,
            "under_30_words": p["words"] < 30,
            "names_selection": bool(first) and first in low,
            "explicit_market": any(w in low for w in MARKET_WORDS),
            "high_outside_band": (p["confidence"] == "high" and p["decimal"] is not None
                                  and not (1.40 <= p["decimal"] <= 101.0)),
            "high_below_70": (p["confidence"] == "high" and p["probability"] is not None
                              and p["probability"] < 0.70),
            "duplicate_text": texts[p["text"].strip()] > 1 if p["text"].strip() else False,
        })
    findings["predictions"] = {
        "count": len(preds),
        "by_layer": dict(Counter(p["layer"] for p in preds)),
        "min_words": min((p["words"] for p in preds), default=0),
        "max_words": max((p["words"] for p in preds), default=0),
        "median_words": sorted(p["words"] for p in preds)[len(preds) // 2] if preds else 0,
        "under_30": sum(1 for p in preds if p["words"] < 30),
        "duplicate_texts": sum(1 for t, c in texts.items() if c > 1),
        "duplicate_openings": sum(1 for t, c in openings.items() if c > 1 and t),
        "distinct_openings": len(openings),
        "high_outside_band": sum(1 for r in pred_rows if r["high_outside_band"]),
        "high_below_70": sum(1 for r in pred_rows if r["high_below_70"]),
        "not_naming_selection": sum(1 for r in pred_rows if not r["names_selection"]),
        "without_explicit_market": sum(1 for r in pred_rows if not r["explicit_market"]),
        "rows": pred_rows,
        "repeated_openings": [{"opening": t, "count": c} for t, c in openings.most_common(12) if c > 1],
    }

    # C8 one fixture-scoped URL describing incompatible pairings ------------
    by_url = defaultdict(list)
    for r in rows:
        if r["date"] and r["official_url"] and r["class"] == "fixture":
            looks_fixture_scoped = (r.get("scope") == "fixture"
                                    or re.search(r"/(gamecenter|match|game|event|fixture)s?/", r["official_url"])
                                    or re.search(r"\d{6,}", r["official_url"]))
            if looks_fixture_scoped:
                by_url[(r["sport"], r["date"], r["official_url"])].append(r)
    competing = []
    for k, v in by_url.items():
        pairs = {tuple(sorted([r["home_norm"], r["away_norm"]])) for r in v}
        if len(pairs) > 1:
            competing.append({
                "sport": k[0], "date": k[1], "official_url": k[2],
                "layers": sorted({r["layer"] for r in v}),
                "pairs": [list(p) for p in sorted(pairs)],
                "rows": [{"layer": r["layer"], "id": r["id"], "home": r["home"], "away": r["away"],
                          "competition": r["competition"]} for r in v],
            })
    findings["competing_pairs"] = sorted(competing, key=lambda x: (x["sport"], x["date"]))

    # C9 same fixture twice in one layer -----------------------------------
    within = []
    for layer, rs in layers.items():
        seen = defaultdict(list)
        for r in rs:
            if r["class"] == "fixture" and r["date"]:
                seen[fixture_key(r)].append(r)
        for k, v in seen.items():
            if len(v) > 1:
                within.append({"layer": layer, "sport": k[0], "date": k[1], "pairs": list(k[2]),
                               "ids": [r["id"] for r in v]})
    findings["within_layer_duplicates"] = within

    # C10 scope + coverage -------------------------------------------------
    breaches = [{"layer": r["layer"], "id": r["id"], "sport": r["sport"],
                 "sport_raw": r["sport_raw"], "competition": r["competition"],
                 "matched": r["sport"]} for r in rows if r["sport"] in EXCLUDED_SLUGS]
    findings["excluded_scope"] = breaches
    findings["eligible_coverage"] = {
        slug: {"layers": sorted({r["layer"] for r in rows if r["sport"] == slug}),
               "rows": sum(1 for r in rows if r["sport"] == slug),
               "fixture_rows": sum(1 for r in rows if r["sport"] == slug and r["class"] == "fixture")}
        for slug in ELIGIBLE_SLUGS
    }
    findings["unknown_sports"] = sorted({r["sport_raw"] for r in rows
                                         if r["sport"] not in ELIGIBLE_SLUGS
                                         and r["sport"] not in EXCLUDED_SLUGS})
    findings["sport_label_variants"] = {
        slug: sorted({r["sport_raw"] for r in rows if r["sport"] == slug})
        for slug in ELIGIBLE_SLUGS
    }

    # confidence-rule compliance per layer --------------------------------
    rule_violations = []
    for r in rows:
        p = r["pick"]
        if not p or p.get("confidence") != "high":
            continue
        if p.get("probability") is not None and p["probability"] < 0.70:
            rule_violations.append({"layer": r["layer"], "id": r["id"], "sport": r["sport"],
                                    "why": "graded high below 70% model probability",
                                    "selection": p.get("selection"),
                                    "probability": p["probability"], "decimal": p.get("decimal")})
        if p.get("decimal") is not None and not (1.40 <= p["decimal"] <= 101.0):
            rule_violations.append({"layer": r["layer"], "id": r["id"], "sport": r["sport"],
                                    "why": "graded high outside the -250..+10000 band",
                                    "selection": p.get("selection"),
                                    "probability": p.get("probability"), "decimal": p["decimal"]})
    findings["rule_violations"] = rule_violations

    per_layer = {}
    for layer, rs in layers.items():
        per_layer[layer] = {
            "rows": len(rs),
            "fixtures": sum(1 for r in rs if r["class"] == "fixture"),
            "non_fixtures": sum(1 for r in rs if r["class"] != "fixture"),
            "sports": len({r["sport"] for r in rs if r["sport"]}),
            "with_moneyline": sum(1 for r in rs if r["ml_dec"] and all(x is not None for x in r["ml_dec"])),
            "with_pick": sum(1 for r in rs if r["pick"]),
            "high": sum(1 for r in rs if (r["pick"] or {}).get("confidence") == "high"),
            "medium": sum(1 for r in rs if (r["pick"] or {}).get("confidence") == "medium"),
            "low": sum(1 for r in rs if (r["pick"] or {}).get("confidence") == "low"),
            "book_price_rows": sum(1 for r in rs if r["publishes_book_price"]),
            "capture_date": layer_meta[layer].get("capture_date", ""),
            "path": layer_meta[layer]["path"],
        }

    report = {
        "audit_date": AUDIT_DATE,
        "layers": per_layer,
        "layer_meta": layer_meta,
        "totals": {
            "rows": len(rows),
            "fixtures": sum(1 for r in rows if r["class"] == "fixture"),
            "non_fixtures": sum(1 for r in rows if r["class"] != "fixture"),
            "sports": len({r["sport"] for r in rows if r["sport"]}),
            "distinct_fixtures": len(by_key),
            "overlap_groups": len(overlap_groups),
            "overlap_rows": sum(len(v) for v in overlap_groups.values()),
            "price_conflicts": len(price_conflicts),
            "confidence_conflicts": len(conf_conflicts),
            "stale_rows": len(findings["stale"]),
            "undated_rows": len(findings["undated"]),
            "excluded_scope_rows": len(breaches),
            "competing_pair_groups": len(findings["competing_pairs"]),
            "within_layer_duplicates": len(within),
            "eligible_sports_with_rows": sum(1 for v in findings["eligible_coverage"].values() if v["rows"]),
            "eligible_sports_with_fixtures": sum(1 for v in findings["eligible_coverage"].values() if v["fixture_rows"]),
            "rule_violations": len(rule_violations),
            "rows_without_official_url": findings["citation"]["rows_without_url"],
        },
        "findings": findings,
    }

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(OUT, "rows.json"), "w", encoding="utf-8") as fh:
        json.dump({"audit_date": AUDIT_DATE, "count": len(rows), "rows": rows},
                  fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    t = report["totals"]
    print(f"rows={t['rows']} fixtures={t['fixtures']} non_fixtures={t['non_fixtures']} "
          f"sports={t['sports']} distinct_fixtures={t['distinct_fixtures']}")
    print(f"overlap_groups={t['overlap_groups']} overlap_rows={t['overlap_rows']} "
          f"price_conflicts={t['price_conflicts']} confidence_conflicts={t['confidence_conflicts']}")
    print(f"stale={t['stale_rows']} undated={t['undated_rows']} excluded={t['excluded_scope_rows']} "
          f"competing_pairs={t['competing_pair_groups']} within_dups={t['within_layer_duplicates']} "
          f"rule_violations={t['rule_violations']}")
    print(f"predictions={findings['predictions']['count']} under30={findings['predictions']['under_30']} "
          f"dup_texts={findings['predictions']['duplicate_texts']} dup_openings={findings['predictions']['duplicate_openings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
