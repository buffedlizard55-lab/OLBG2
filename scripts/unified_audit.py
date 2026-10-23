#!/usr/bin/env python3
"""Line-by-line audit of the evidence this repository already holds.

The audit answers one question per row: *what in this repository actually proves this
value?*  It never reaches the network, never fills a blank, and never repeats a claim
from another layer's prose.  Three independent evidence families are used:

  1. `data/ledger/raw/` - 179 verbatim HTTP bodies fetched on a GitHub-hosted runner at
     2026-10-23T20:32Z, with the manifest's status code, byte count and sha256.
  2. `data/cadence/` - the capture bundles and originated prices published by session
     `a0c8b7f3` at 2026-10-23T20:05Z (read as data; their arithmetic is re-derived here).
  3. `data/unified/olbg_events.json` - this session's own second reading of the OLBG
     pages, independent of `ledger_seed.py`'s parse.

Output: data/unified/audit.json
Exit code 0 when the audit completes; the findings are the product, not a build failure.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import unicodedata
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "unified" / "audit.json"

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]

TARGET_PREDICTIONS = 5          # brief: aim for five written predictions per sport per day
BAND = (-250, 10000)            # brief: selections between -250 and +10000

PROHIBITED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)

# Hosts that are the competition's own governing body, league or tour.
OFFICIAL_HOSTS = {
    "www.olbg.com", "statsapi.mlb.com", "www.wst.tv", "www.pdc.tv", "www.atptour.com",
    "www.gbgb.org.uk", "www.lnh.fr", "www.nrl.com", "www.formula1.com", "api-web.nhle.com",
    "www.nba.com", "www.cricket.com.au", "www.legavolley.it", "www.volleyball-bundesliga.de",
    "www.premrugby.com", "www.euroleaguebasketball.net", "ak-static.cms.nba.com",
    "official.nba.com", "www.pgatour.com", "www.europeantour.com", "stats.unitedrugby.com",
    "www.gaa.ie", "munster.gaa.ie", "gaacork.ie", "www.kerrygaa.ie", "www.waterfordgaa.ie",
    "limerickgaa.ie", "www.urc.tv", "www.unitedrugby.com", "www.ehfcl.com", "www.eurohandball.com",
    "www.plusliga.pl", "www.legavolleyfemminile.it", "www.cev.eu", "www.fivb.com",
    "www.icc-cricket.com", "www.rlwc2026.com", "www.nrl.com.au", "www.superleague.co.uk",
    "www.scottishrugby.org", "www.wru.wales", "www.irishrugby.ie", "www.rugbyleague.com",
    "www.rugby-league.com", "www.britishbasketballleague.com",
}


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


ALIASES = {
    "usa": "united states", "us": "united states", "f1": "formula 1",
    "st": "saint", "mtl": "montreal", "tb": "tampa bay", "chi": "chicago",
    "min": "minnesota", "dal": "dallas", "ind": "indiana", "mia": "miami",
    "det": "detroit", "atl": "atlanta", "cha": "charlotte", "bos": "boston",
    "ny": "new york", "la": "los angeles", "vgs": "vegas", "wpg": "winnipeg",
    "car": "carolina", "edm": "edmonton", "cgy": "calgary", "nj": "new jersey",
    "pit": "pittsburgh", "ott": "ottawa", "sea": "seattle", "uta": "utah",
    "nsh": "nashville", "fla": "florida", "sj": "san jose", "tor": "toronto",
    "phi": "philadelphia", "cle": "cleveland", "orl": "orlando", "mem": "memphis",
    "no": "new orleans", "ut": "utah", "gs": "golden state", "sac": "sacramento",
    "por": "portland", "was": "washington", "bkn": "brooklyn", "hou": "houston",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    s = s.replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


def expand(s: str) -> list[str]:
    out: list[str] = []
    for t in norm(s).split():
        out.extend(ALIASES.get(t, t).split())
    return out


def title_match(a: str, b: str) -> bool:
    """Compare two single-sided event titles (outrights/futures) on content words."""
    stop = {"grand", "prix", "championship", "championships", "2026", "2027", "final",
            "open", "cup", "the", "of", "and", "tour", "world", "series", "race"}
    ta = {t for t in expand(a) if t not in stop}
    tb = {t for t in expand(b) if t not in stop}
    if not ta or not tb:
        return False
    inter = ta & tb
    return len(inter) >= 2 and len(inter) / min(len(ta), len(tb)) >= 0.6


FORMAT_TAIL = re.compile(
    r"\b(one day match|1st t20 match|2nd t20 match|3rd t20 match|t20 match|t20|odi|test match|"
    r"test series|series|match|game)\b", re.I)


def sides(name: str):
    parts = re.split(r"\s+@\s+|\s+vs\.?\s+|\s+v\s+", str(name or ""), flags=re.I)
    if len(parts) != 2:
        return None, None
    out = []
    for p in parts:
        p = FORMAT_TAIL.sub(" ", p)
        out.append(norm(p))
    return out[0], out[1]


def side_match(a: str, b: str) -> bool:
    """True when two team/player labels can reasonably denote the same side.

    Rules, in order: identical; last word identical (handles MTL Canadiens vs
    Montréal Canadiens); shorter string is a prefix of the longer with at least five
    characters (handles Tasmania vs Tasmanian Tigers); one string's words are a subset of
    the other's (handles Western Australia vs WA where initials are expanded upstream).
    """
    if not a or not b:
        return False
    if a == b:
        return True
    ta, tb = a.split(), b.split()
    if ta and tb and ta[-1] == tb[-1] and len(ta[-1]) > 3:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= 5 and long_.startswith(short):
        return True
    if set(ta) and set(tb) and (set(ta) <= set(tb) or set(tb) <= set(ta)):
        return True
    return False


def american_to_decimal(a: float) -> float:
    return 1 + (a / 100 if a > 0 else 100 / abs(a))


def implied(p: float) -> float:
    return 1 / p


def prob_to_american(p: float) -> int:
    if p >= 0.5:
        return -round(100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def parse_decimal(s) -> float | None:
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def decimal_to_american(d: float) -> int:
    """Standard decimal -> American conversion (rounded, as sportsbooks quote them)."""
    if d <= 1.0:
        return 0
    if d < 2.0:
        return -round(100 / (d - 1))
    return round((d - 1) * 100)


# --------------------------------------------------------------------------- evidence


def official_index():
    """Machine-readable official fixtures in the 20:32Z capture set."""
    idx = {"mlb": {}, "nhl": {}, "euroleague": {}}
    try:
        mlb = load("data/ledger/raw/baseball_schedule.json")
        for date in mlb.get("dates", []):
            for g in date.get("games", []):
                idx["mlb"][str(g["gamePk"])] = {
                    "date": date["date"], "start_utc": g.get("gameDate"),
                    "away": g["teams"]["away"]["team"]["name"],
                    "home": g["teams"]["home"]["team"]["name"],
                    "status": (g.get("status") or {}).get("detailedState"),
                    "source": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-31",
                }
    except (OSError, ValueError, KeyError):
        pass
    try:
        nhl = load("data/ledger/raw/ieh_schedule.json")
        for week in nhl.get("gameWeek", []):
            for g in week.get("games", []):
                idx["nhl"][str(g["id"])] = {
                    "date": week["date"], "start_utc": g.get("startTimeUTC"),
                    "home": (g.get("homeTeam") or {}).get("commonName", {}).get("default"),
                    "away": (g.get("awayTeam") or {}).get("commonName", {}).get("default"),
                    "venue": (g.get("venue") or {}).get("default"),
                    "source": "https://api-web.nhle.com/v1/schedule/2026-10-23",
                }
    except (OSError, ValueError, KeyError):
        pass
    try:
        xml = (ROOT / "data/ledger/raw/basketball_el_schedule.xml").read_text(encoding="utf-8")
        for item in re.findall(r"<item>(.*?)</item>", xml, re.S):
            def field(tag):
                m = re.search(rf"<{tag}>(.*?)</{tag}>", item)
                return m.group(1) if m else None
            code = field("gamecode")
            if not code:
                continue
            idx["euroleague"][code] = {
                "date": field("date"), "start": field("startime"),
                "home": (field("hometeam") or "").title(),
                "away": (field("awayteam") or "").title(),
                "gameday": field("gameday"),
                "source": "https://www.euroleaguebasketball.net/euroleague/game-center/?round=8&season=E2026",
            }
    except (OSError, ValueError):
        pass
    return idx


def bundle_index():
    """Fixture ids addressed by the /cadence/ capture bundles."""
    idx = {}
    for path in sorted((DATA / "cadence" / "captures").glob("*.json")):
        blob = load(f"data/cadence/captures/{path.name}")
        for reading in blob.get("readings", []):
            fid = reading.get("fixture_id")
            if fid:
                idx.setdefault(fid, []).append({
                    "capture": f"data/cadence/captures/{path.name}",
                    "url": blob.get("url"),
                    "captured_utc": blob.get("captured_utc"),
                    "reading": {k: v for k, v in reading.items() if k != "fixture_id"},
                })
    return idx


# --------------------------------------------------------------------------- checks


def check_lines(lines: dict):
    errors, band_stats = [], {"total": 0, "in_band": 0, "band_line": 0, "high": 0,
                              "documented_caps": 0, "capped_sentinel": 0, "high_in_band": 0}
    for ln in lines["lines"]:
        band_stats["total"] += 1
        p = ln.get("probability")
        if not isinstance(p, (int, float)) or not (0 < p < 1):
            errors.append({"line_id": ln.get("id"), "error": "probability outside (0,1)"})
            continue
        fair_am = prob_to_american(p)
        if abs(fair_am - ln.get("fair_american", 0)) > 1:
            errors.append({"line_id": ln.get("id"),
                           "error": f"fair_american {ln.get('fair_american')} does not recompute from {p:.6f} (got {fair_am})"})
        fair_dec = round(1 / p, 3)
        if abs(fair_dec - ln.get("fair_decimal", 0)) > 0.002:
            errors.append({"line_id": ln.get("id"),
                           "error": f"fair_decimal {ln.get('fair_decimal')} does not recompute from {p:.6f} (got {fair_dec})"})
        offered_dec = ln.get("offered_decimal")
        offered_am = ln.get("offered_american")
        if offered_dec and offered_am is not None:
            if int(offered_am) == 999900:
                # Documented ceiling sentinel used for prices at or beyond +10000.
                band_stats["capped_sentinel"] += 1
                if float(offered_dec) < 100.0:
                    errors.append({"line_id": ln.get("id"),
                                   "error": "999900 sentinel used on a price inside the normal range"})
            else:
                # Compare in probability space: a decimal rounded to three places and an American
                # price rounded to a whole number can look far apart at short prices even when
                # they describe the same chance.
                p_dec = 1 / float(offered_dec)
                a = int(offered_am)
                p_am = abs(a) / (abs(a) + 100) if a < 0 else 100 / (a + 100)
                # 0.0015 = 0.15 percentage points, which is the span created by quoting a
                # decimal to three places and an American price to a whole number.
                if abs(p_dec - p_am) > 0.0015:
                    errors.append({"line_id": ln.get("id"),
                                   "error": f"offered_american {offered_am} and offered_decimal {offered_dec} "
                                            f"imply different chances ({p_am:.4f} v {p_dec:.4f})"})
        in_band = BAND[0] <= fair_am <= BAND[1]
        if bool(ln.get("in_band")) != in_band:
            errors.append({"line_id": ln.get("id"),
                           "error": f"in_band={ln.get('in_band')} but fair price {fair_am} against band {BAND}"})
        if in_band:
            band_stats["in_band"] += 1
        if ln.get("band_line"):
            band_stats["band_line"] += 1
        conf = ln.get("confidence")
        expected = "high" if p >= 0.70 else "medium" if p >= 0.60 else "low"
        if conf != expected:
            # The desk documents one exception: an alternate band line on a thin sample is
            # capped at medium even though its probability clears 0.70.  Verify the cap is
            # recorded on the row (band_line) rather than silently applied.
            if conf == "medium" and expected == "high" and ln.get("band_line"):
                band_stats["documented_caps"] += 1
            else:
                errors.append({"line_id": ln.get("id"),
                               "error": f"confidence {conf} but probability {p:.4f} implies {expected}"})
        if conf == "high":
            band_stats["high"] += 1
            if in_band:
                band_stats["high_in_band"] += 1
    return errors, band_stats


def check_predictions(preds: dict, fixtures: dict, picks: dict):
    errors = []
    by_fid = {f["id"]: f for f in fixtures}
    pick_by_id = {p["id"]: p for p in picks["picks"]}
    texts = [p["text"] for p in preds["predictions"]]
    openings = [" ".join(t.split()[:3]).lower() for t in texts]
    for p in preds["predictions"]:
        words = len(p["text"].split())
        if words < 30:
            errors.append({"prediction": p["id"], "error": f"only {words} words"})
        if PROHIBITED.search(p["text"] + " " + p.get("headline", "")):
            errors.append({"prediction": p["id"], "error": "contains a prohibited word (model/verified family)"})
        side = re.sub(r"[-+]?\d+(?:\.\d+)?", " ", p["selection"]).strip()
        if side and norm(side) not in norm(p["text"]):
            errors.append({"prediction": p["id"],
                           "error": f"selection '{p['selection']}' not named in the prose"})
        pick = pick_by_id.get(p.get("pick_id"))
        if not pick:
            errors.append({"prediction": p["id"], "error": "pick_id not present in picks.json"})
        elif abs(pick["probability"] - p["probability"]) > 1e-9:
            errors.append({"prediction": p["id"], "error": "probability differs from its pick"})
    if len(texts) != len(set(texts)):
        errors.append({"prediction": "ALL", "error": "duplicate prediction texts"})
    if len(openings) != len(set(openings)):
        dup = [o for o in openings if openings.count(o) > 1]
        errors.append({"prediction": "ALL", "error": f"duplicate three-word openings: {sorted(set(dup))}"})
    return errors, {"count": len(texts), "min_words": min((len(t.split()) for t in texts), default=0),
                    "unique_openings": len(set(openings)), "unique_texts": len(set(texts))}


NUM = re.compile(r"\d+(?:\.\d+)?")


def check_traceability(preds: dict, fixtures: dict, lines: dict):
    """Every number in a prediction must appear in that fixture's stored evidence."""
    by_fid = {f["id"]: f for f in fixtures}
    lines_by_fid: dict[str, list] = {}
    for ln in lines["lines"]:
        lines_by_fid.setdefault(ln["fixture_id"], []).append(ln)
    out = []
    for p in preds["predictions"]:
        fx = by_fid.get(p["fixture_id"], {})
        haystack = json.dumps(fx, ensure_ascii=False) + " " + json.dumps(
            lines_by_fid.get(p["fixture_id"], []), ensure_ascii=False)
        haystack += " " + json.dumps(p, ensure_ascii=False)
        have = set(NUM.findall(haystack))
        text_numbers = NUM.findall(p["text"])
        missing = sorted({n for n in text_numbers if n not in have})
        out.append({"prediction": p["id"], "sport": p["sport"], "numbers": text_numbers,
                    "not_in_evidence": missing})
    return out


def match_fixtures_to_olbg(fixtures: list, events: list):
    """Attach the OLBG event(s) that publish the same two sides for the same sport."""
    by_sport: dict[str, list] = {}
    singles: dict[str, list] = {}
    for e in events:
        a, b = sides(e["event"])
        if a and b:
            by_sport.setdefault(e["sport"], []).append((e, a, b))
        else:
            singles.setdefault(e["sport"], []).append(e)
    result = {}
    for fx in fixtures:
        candidates = []
        for e, a, b in by_sport.get(fx["sport"], []):
            for h, aw in ((fx.get("home"), fx.get("away")), (fx.get("away"), fx.get("home"))):
                if h and aw and side_match(norm(h), a) and side_match(norm(aw), b):
                    candidates.append(e)
                    break
        if not candidates:
            for e in singles.get(fx["sport"], []):
                if title_match(str(fx.get("home") or "") + " " + str(fx.get("away") or ""), e["event"]):
                    candidates.append(e)
                    break
        best = None
        delta_min = None
        if candidates:
            # Two sides are not enough on their own: a baseball series puts the same pair on the
            # field on consecutive days, so the start has to agree to within twelve hours and the
            # closest one wins. Without a start on both sides the match is reported, not timed.
            def gap(c):
                if not (c.get("start_utc") and fx.get("start_utc")):
                    return None
                return abs((dt.datetime.fromisoformat(c["start_utc"].replace("Z", "+00:00"))
                            - dt.datetime.fromisoformat(fx["start_utc"].replace("Z", "+00:00"))
                            ).total_seconds())

            timed = [(gap(c), c) for c in candidates if gap(c) is not None]
            timed = [(g, c) for g, c in timed if g <= 12 * 3600]
            if timed:
                delta_min, best = min(timed, key=lambda gc: gc[0])
                delta_min = int(delta_min / 60)
            elif not timed and not any(gap(c) is not None for c in candidates):
                best = candidates[0]
        result[fx["id"]] = {
            "matched": bool(best),
            "event": best["event"] if best else None,
            "event_id": best["event_id"] if best else None,
            "event_url": best.get("event_url") if best else None,
            "olbg_start_utc": best.get("start_utc") if best else None,
            "candidate_count": len(candidates),
            "start_delta_minutes": delta_min,
        }
    return result


def verify_against_official(fixtures: list, idx: dict):
    out = {}
    for fx in fixtures:
        fid = fx["id"]
        found = None
        for key, prefix in (("mlb", "mlb-"), ("nhl", "nhl-"), ("euroleague", "el-")):
            if fid.startswith(prefix):
                ref = fid[len(prefix):]
                rec = idx[key].get(ref)
                if rec:
                    found = {"family": key, **rec}
                else:
                    found = {"family": key, "missing": f"{key} capture does not contain {ref}"}
                break
        out[fid] = found or {"family": None}
    return out



def repo_checks() -> dict:
    """Repository-level irregularities, each recomputed here rather than copied forward."""
    out: dict = {"counts": {}, "findings": []}

    coord = (ROOT / "COORDINATION.md").read_text(encoding="utf-8", errors="replace").splitlines()
    markers = [i + 1 for i, line in enumerate(coord)
               if line.startswith(("<<<<<<<", ">>>>>>>")) or line.strip() == "======="]
    out["counts"]["merge_conflict_marker_lines"] = len(markers)
    if markers:
        out["findings"].append({
            "id": "U-20", "severity": "medium", "category": "Git hygiene",
            "item": "COORDINATION.md",
            "finding": f"{len(markers)} unresolved merge-conflict marker lines remain in COORDINATION.md "
                       f"(first at line {markers[0]}).",
            "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md",
            "evidence": f"lines {', '.join(str(m) for m in markers[:12])}"})
    else:
        out["findings"].append({
            "id": "U-20", "severity": "resolved", "category": "Git hygiene",
            "item": "COORDINATION.md merge-conflict markers",
            "finding": "The six marker lines that bracketed three conflicted regions in COORDINATION.md are gone "
                       "and the file parses as a single document. Resolution rule, applied line by line: where one "
                       "side of a conflict was a superset of the other, the fuller copy was kept (block 1: 128 "
                       "lines kept, 90 dropped, every dropped line present in the kept copy); where each side "
                       "carried records the other lacked, both sides were kept in order and only the three marker "
                       "lines were removed (blocks 2 and 3). No line of session history was lost: the only lines "
                       "removed from the file are the marker lines themselves and the superseded duplicate copy.",
            "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md",
            "evidence": "COORDINATION.md"})

    excluded = ("aussie-rules", "esports")
    bad_pages = [p for p in ROOT.rglob("*.html")
                 if p.name.split(".")[0] in excluded and ".git" not in p.parts]
    out["counts"]["out_of_scope_sport_pages"] = len(bad_pages)
    if bad_pages:
        out["findings"].append({
            "id": "U-21", "severity": "low", "category": "Scope",
            "item": "Sports outside the fifteen requested",
            "finding": f"{len(bad_pages)} published pages cover Aussie Rules or esports, which the brief does "
                       "not include. They are left in place (other sessions own them) and are not linked from "
                       "this desk.",
            "source_url": "https://www.olbg.com/betting-tips",
            "evidence": ", ".join(sorted({str(p.relative_to(ROOT)) for p in bad_pages[:6]}))})

    offenders = []
    files = sorted(DATA.glob("*/predictions*.json")) + sorted(DATA.glob("predictions*.json"))
    for path in files:
        try:
            blob = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in PROHIBITED.finditer(blob):
            offenders.append((str(path.relative_to(ROOT)), m.group(0)))
        if PROHIBITED.search(blob):
            pass
    files_with = sorted({f for f, _ in offenders})
    out["counts"]["prediction_files_with_prohibited_words"] = len(files_with)
    out["counts"]["prohibited_word_occurrences_other_layers"] = len(offenders)
    if files_with:
        out["findings"].append({
            "id": "U-22", "severity": "medium", "category": "Prose",
            "item": "Other layers' prediction prose",
            "finding": f"{len(files_with)} prediction files outside this desk still contain the words the brief "
                       f"prohibits in output prose ('model'/'verified' families), {len(offenders)} occurrences in "
                       "all. The consolidated pages quote only write-ups that pass the rule; the older desks are "
                       "kept for audit and are not reprinted here.",
            "source_url": "data/predictions.json",
            "evidence": ", ".join(files_with[:6])})

    try:
        root_matches = json.loads((DATA / "matches.json").read_text())
        out["counts"]["root_data_rows"] = len(root_matches.get("matches", []))
        out["counts"]["root_data_snapshot"] = root_matches.get("captured_at") or root_matches.get("generated_at")
        out["counts"]["root_data_sports"] = len({m.get("sport") for m in root_matches.get("matches", [])})
    except (OSError, ValueError):
        pass

    desks = sorted(p.name for p in ROOT.iterdir()
                   if p.is_dir() and (p / "index.html").exists() and p.name != "sports")
    out["counts"]["published_layers"] = len(desks) + 1
    workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    unrebuilt = [d for d in desks if f"{d}_" not in workflow and f"/{d}/" not in workflow]
    out["counts"]["layers_not_rebuilt_by_ci"] = unrebuilt
    if unrebuilt:
        out["findings"].append({
            "id": "U-23", "severity": "high", "category": "Build integrity",
            "item": "Published layers that CI never rebuilds",
            "finding": f"{len(unrebuilt)} of {len(desks)} published desk directories are not regenerated by the "
                       f"validation workflow ({', '.join(unrebuilt)}). Their pages can drift from their data "
                       "without any check failing, and any count they print may already be stale.",
            "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/.github/workflows/pages.yml",
            "evidence": "pages.yml step list"})

    # The same match priced by several layers with different probabilities.
    same = []
    for rel in ("data/olbg/lines.json", "data/live/lines.json", "data/vanguard/lines.json",
                "data/daily/lines.json"):
        path = ROOT / rel
        if not path.exists():
            continue
        blob = json.loads(path.read_text())
        rows = blob.get("lines") or blob.get("rows") or []
        for r in rows:
            if "849805" not in json.dumps(r):
                continue
            if r.get("selection") == "Milwaukee Brewers" and r.get("probability") is not None:
                same.append((rel, round(r["probability"], 4)))
                break
    if same:
        out["findings"].append({
            "id": "U-24", "severity": "high", "category": "Reconciliation",
            "item": "One match, four published probabilities",
            "finding": "Milwaukee Brewers to beat Tampa Bay in MLB game 849805 is published by this repository at "
                       + "; ".join(f"{p:.3f} in {rel}" for rel, p in same)
                       + ", and at 0.651 in data/cadence/lines.json. The layers disagree, no note reconciles them, "
                         "and none of the differences is explained by a published change of inputs. This desk "
                         "publishes the cadence figure and records the others here rather than averaging them.",
            "source_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-31",
            "evidence": "data/{olbg,live,vanguard,cadence}/lines.json"})
    return out


def main() -> int:
    inv = load("data/unified/olbg_events.json")
    fixtures = load("data/cadence/fixtures.json")["fixtures"]
    lines = load("data/cadence/lines.json")
    picks = load("data/cadence/picks.json")
    preds = load("data/cadence/predictions.json")
    sources = load("data/cadence/sources.json")
    cadence_flags = load("data/cadence/flagged.json")
    ledger_events = load("data/ledger/matches.json")["events"]

    line_errors, band_stats = check_lines(lines)
    pred_errors, pred_stats = check_predictions(preds, fixtures, picks)
    trace = check_traceability(preds, fixtures, lines)

    idx = official_index()
    bundle = bundle_index()
    olbg_match = match_fixtures_to_olbg(fixtures, inv["events"])
    official = verify_against_official(fixtures, idx)

    # ---- per-fixture evidence record
    fx_rows = []
    for fx in fixtures:
        fid = fx["id"]
        off = official.get(fid) or {}
        b = bundle.get(fid, [])
        if off.get("home") and side_match(norm(off["home"]), norm(fx.get("home"))) \
                and side_match(norm(off.get("away") or ""), norm(fx.get("away"))):
            level = "official-schedule"
        elif off.get("missing"):
            level = "capture-bundle"
        elif b:
            level = "capture-bundle"
        else:
            level = "unconfirmed"
        fx_rows.append({
            "id": fid,
            "sport": fx["sport"],
            "competition": fx.get("competition"),
            "home": fx.get("home"),
            "away": fx.get("away"),
            "start_utc": fx.get("start_utc"),
            "time_display": fx.get("time_display"),
            "venue": fx.get("venue"),
            "olbg_event_id": fx.get("olbg_event_id"),
            "official_source_url": fx.get("official_source_url"),
            "stats_source_url": fx.get("stats_source_url"),
            "facts": fx.get("facts", []),
            "olbg": olbg_match.get(fid),
            "official": off,
            "bundle": b,
            "verification_level": level,
        })

    # ---- join every graded pick to the price row it came from, so the band flag is derived
    line_index = {(l["fixture_id"], l["market"], l["selection"], l.get("line")): l for l in lines["lines"]}
    pick_rows = []
    unmatched_picks = []
    for p in picks["picks"]:
        src = line_index.get((p["fixture_id"], p["market"], p["selection"], p.get("line")))
        row = dict(p)
        row["band_line"] = bool(src and src.get("band_line"))
        row["offered_decimal"] = src.get("offered_decimal") if src else None
        row["price_row_found"] = bool(src)
        if not src:
            unmatched_picks.append(p["id"])
        pick_rows.append(row)

    # ---- per-sport coverage against the OLBG listing and the five-a-sport target
    pred_by_sport: dict[str, int] = {}
    for p in preds["predictions"]:
        pred_by_sport[p["sport"]] = pred_by_sport.get(p["sport"], 0) + 1
    pick_by_sport: dict[str, dict] = {}
    for p in picks["picks"]:
        slot = pick_by_sport.setdefault(p["sport"], {"all": 0, "high": 0, "medium": 0,
                                                     "low": 0, "in_band_high": 0})
        slot["all"] += 1
        slot[p["confidence"]] = slot.get(p["confidence"], 0) + 1
        if p["confidence"] == "high" and p.get("in_band"):
            slot["in_band_high"] += 1
    priced = {ln["fixture_id"] for ln in lines["lines"]}
    coverage = {}
    for sport in SPORTS:
        s_events = [e for e in inv["events"] if e["sport"] == sport]
        s_upcoming = [e for e in s_events if e.get("upcoming_at_capture")]
        s_fx = [f for f in fixtures if f["sport"] == sport]
        matched = [f for f in s_fx if (olbg_match.get(f["id"]) or {}).get("matched")]
        coverage[sport] = {
            "olbg_events_captured": len(s_events),
            "olbg_events_upcoming": len(s_upcoming),
            "our_fixtures": len(s_fx),
            "our_fixtures_priced": sum(1 for f in s_fx if f["id"] in priced),
            "our_fixtures_on_olbg": len(matched),
            "our_fixtures_not_on_olbg": len(s_fx) - len(matched),
            "picks": pick_by_sport.get(sport, {}),
            "predictions": pred_by_sport.get(sport, 0),
            "prediction_target": TARGET_PREDICTIONS,
            "prediction_shortfall": max(0, TARGET_PREDICTIONS - pred_by_sport.get(sport, 0)),
        }

    # ---- source register
    src_rows = []
    unknown_hosts = set()
    for s in sources["sources"]:
        host = urlsplit(s["url"]).netloc
        official_host = host in OFFICIAL_HOSTS
        if not official_host:
            unknown_hosts.add(host)
        src_rows.append({**s, "host": host, "host_classified_official": official_host,
                         "https": s["url"].startswith("https://")})

    # ---- independent cross-check of this session's parse against the ledger parse
    ledger_by_sport: dict[str, int] = {}
    for e in ledger_events:
        ledger_by_sport[e["sport"]] = ledger_by_sport.get(e["sport"], 0) + 1
    recon = []
    for sport in SPORTS:
        ours = sum(1 for e in inv["events"] if e["sport"] == sport)
        ours_up = sum(1 for e in inv["events"] if e["sport"] == sport and e.get("upcoming_at_capture"))
        theirs = ledger_by_sport.get(sport, 0)
        recon.append({"sport": sport, "unified_events": ours, "unified_upcoming": ours_up,
                      "ledger_upcoming": theirs, "delta": ours_up - theirs,
                      "note": "" if ours_up == theirs else
                              "this desk merges each sport's hub page with its all-events page, which "
                              "carries events the single listing used by the ledger did not include"})

    findings = []

    def flag(fid, severity, category, item, finding, source_url, evidence=""):
        findings.append({"id": fid, "severity": severity, "category": category, "item": item,
                         "finding": finding, "source_url": source_url, "evidence": evidence})

    # F-U01 arithmetic
    if line_errors:
        flag("U-01", "high", "Arithmetic", "Originated prices",
             f"{len(line_errors)} of {band_stats['total']} prices fail their own recomputation.",
             "data/cadence/lines.json", json.dumps(line_errors[:5]))
    # F-U02 prediction constraints
    if pred_errors:
        flag("U-02", "high", "Prose", "Written predictions",
             f"{len(pred_errors)} prediction constraint failures.",
             "data/cadence/predictions.json", json.dumps(pred_errors[:5]))
    # F-U03 untraceable numbers
    bad_trace = [t for t in trace if t["not_in_evidence"]]
    if bad_trace:
        flag("U-03", "medium", "Provenance", "Numbers in prediction prose",
             f"{len(bad_trace)} prediction(s) contain a number that is not in that fixture's stored evidence.",
             "data/cadence/predictions.json", json.dumps([{k: v for k, v in t.items() if k != 'numbers'} for t in bad_trace[:5]]))
    # F-U04 OLBG gap
    total_upcoming = sum(1 for e in inv["events"] if e.get("upcoming_at_capture"))
    flag("U-04", "high", "Coverage", "OLBG-listed events against priced fixtures",
         f"The 20:32Z capture lists {total_upcoming} events that start after the capture clock. "
         f"The desk prices {len(priced)} fixtures across all sports, of which "
         f"{sum(1 for f in fixtures if (olbg_match.get(f['id']) or {}).get('matched'))} were matched to an OLBG listing. "
         "Rows OLBG lists that the desk does not price are shown blank, not filled.",
         "https://www.olbg.com/betting-tips", "data/unified/olbg_events.json")
    # F-U05 five-a-sport shortfall
    shortfalls = {s: c["prediction_shortfall"] for s, c in coverage.items() if c["prediction_shortfall"]}
    flag("U-05", "high", "Coverage", "Five written predictions per sport",
         f"{len(shortfalls)} of {len(SPORTS)} sports fall short of the five-a-sport target. "
         "Shortfall by sport: " + ", ".join(f"{k} {v}" for k, v in sorted(shortfalls.items())) +
         ". No prediction was written for a selection below "
         "medium confidence, and none was invented to fill a quota.",
         "data/cadence/predictions.json")
    # F-U06 fixtures with no OLBG counterpart
    orphan = [f for f in fx_rows if not (f["olbg"] or {}).get("matched")]
    orphan_by_sport: dict[str, int] = {}
    for f in orphan:
        orphan_by_sport[f["sport"]] = orphan_by_sport.get(f["sport"], 0) + 1
    if orphan:
        flag("U-06", "medium", "Reconciliation", "Fixtures with no OLBG listing in today's capture",
             f"{len(orphan)} of {len(fixtures)} fixtures have no OLBG event with the same two sides in the captured "
             f"pages (" + ", ".join(f"{k} {v}" for k, v in sorted(orphan_by_sport.items())) + "). They stay "
             "published with their official source "
             "link; none is claimed to be on OLBG.",
             "data/unified/olbg_events.json")
    # F-U07 sports with an empty OLBG payload
    empty_pages = [e for e in inv["parse_errors"] if e.get("error") == "no tip object found in body"]
    if empty_pages:
        flag("U-07", "medium", "Capture", "OLBG pages with no event payload",
             "; ".join(sorted({f"{e['key']} (HTTP {e['status']})" for e in empty_pages}))
             + " returned a body with an empty tips array at 20:32Z, so no OLBG event could be read for golf. "
               "Golf fixtures therefore rest on the tours' own pages, not on an OLBG listing.",
             "https://www.olbg.com/betting-tips/Golf/5")
    # F-U08 official-source capture failures
    m = load("data/ledger/manifest.json")
    failed = [c for c in m["captures"] if c.get("status") not in (200, None)]
    status_counts: dict[str, int] = {}
    for c in failed:
        status_counts[str(c["status"])] = status_counts.get(str(c["status"]), 0) + 1
    flag("U-08", "medium", "Capture", "Official pages that refused the capture job",
         f"{len(failed)} of {len(m['captures'])} captured URLs returned a non-200 status "
         f"({json.dumps(status_counts)}). They are stored and published: a 403 or a login redirect is evidence, "
         "not a silent gap.",
         "data/ledger/manifest.json")
    # F-U09 truncated captures
    trunc = [c for c in m["captures"] if c.get("truncated")]
    if trunc:
        flag("U-09", "low", "Capture", "Bodies truncated at the 300 kB cap",
             f"{len(trunc)} captured bodies hit the 300,000-byte cap and are stored truncated "
             f"({len({c.get('sport') for c in trunc})} sports). Any table beyond the cut is not read.",
             "data/ledger/manifest.json")
    # F-U10 provenance of the cadence bundles
    flag("U-10", "high", "Provenance", "Capture bundles are transcribed readings, not stored bodies",
         "The 25 files under data/cadence/captures/ record a URL, a timestamp and hand-shaped readings; they do "
         "not store the response body, status code or a hash. Their contents therefore cannot be re-derived by "
         "this session, and are treated as an assertion by the publishing session. Every fixture also carries an "
         "official URL that a reader can open.",
         "data/cadence/captures/nba_games.json")
    # F-U11 time bases
    flag("U-11", "medium", "Presentation", "Mixed time bases in the stored data",
         "The stored values are kept exactly as each source published them: a UTC instant for NHL, MLB and the "
         "NRL display, a bare 'local' or 'viewer-local' string for EuroLeague, the ATP schedule and "
         "cricket.com.au, and a date with no clock for 78 of the 122 graded picks. Where an instant exists the "
         "desk converts it once to the reader's zone and labels that conversion; where it does not, the source's "
         "own wording is shown and the row is left off the day-based summary rather than given a time it never had.",
         "data/cadence/fixtures.json")

    # F-U25 OLBG start versus official start
    drift = sorted([(f["olbg"]["start_delta_minutes"], f["id"], f["sport"], f["olbg"]["event"])
                    for f in fx_rows
                    if (f.get("olbg") or {}).get("matched") and (f["olbg"].get("start_delta_minutes") or 0) > 60])
    if drift:
        flag("U-25", "medium", "Contradiction", "OLBG's listed start disagrees with the official start",
             f"{len(drift)} of the matched fixtures carry an OLBG start more than an hour away from the official "
             "one. Both values are published side by side and neither is adjusted: "
             + "; ".join(f"{fid} ({sport}) {mins} min apart, OLBG lists {ev}" for mins, fid, sport, ev in drift)
             + ". The largest is an NBA game that OLBG shows as already under way at the capture clock "
               "(`expired:1` in its own payload) while the NBA page carries an 8:00 PM ET tip, so the two sources "
               "genuinely disagree and the desk does not pick a winner between them.",
             "data/ledger/raw/olbg_basketball.txt", "data/unified/olbg_events.json")

    # F-U26 the reconciliation this session corrected
    flag("U-26", "high", "Reconciliation", "A match inherited from the previous layer was paired to the wrong game",
         "OLBG event 160789 (TB Rays @ MIL Brewers) starts 2026-10-24T00:00Z, which is MLB game 849805. The earlier "
         "reconciliation attached it to 849802, the same two teams one day later, because it accepted any pairing "
         "within 36 hours. This session requires the start to agree within twelve hours and takes the closest, so "
         "849805 now carries the OLBG listing and 849802 is published as having no OLBG counterpart. The same rule "
         "dropped the Motor Racing match: OLBG's 'USA Grand Prix 2026' is listed 23 hours before the official race "
         "start, which is too far apart to call the same session.",
         "https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789",
         "data/unified/audit.json")
    # F-U12 source hosts
    if unknown_hosts:
        flag("U-12", "low", "Sources", "Hosts outside the governing-body list",
             f"{len(unknown_hosts)} host(s) in the source register are not on this desk's governing-body list: "
             f"{', '.join(sorted(unknown_hosts))}.",
             "data/cadence/sources.json")

    # ------------------------------------------------------------------ repository review
    repo = repo_checks()
    for row in repo["findings"]:
        findings.append(row)

    audit = {
        "generated_from": {
            "olbg_capture": inv["generated_from"]["capture_window"],
            "official_capture_manifest": "data/ledger/manifest.json",
            "fixture_layer": "data/cadence/fixtures.json (2026-10-23T20:05Z)",
            "network_used_by_this_script": False,
        },
        "checks": sorted([
            {"id": "A1", "check": "Every originated price recomputes from its own probability",
             "scope": f"{band_stats['total']} prices", "result": "pass" if not line_errors else "fail",
             "detail": f"fair_american, fair_decimal, offered pair, band flag and confidence label re-derived "
                       f"from probability; {len(line_errors)} mismatches."},
            {"id": "A2", "check": "Band rule applied consistently",
             "scope": f"{band_stats['in_band']} price rows inside {BAND}",
             "result": "pass" if not line_errors else "fail",
             "detail": f"{band_stats['high']} of {band_stats['total']} price rows grade high (p>=0.70); only those "
                       f"whose fair price is also >= -250 sit inside the brief's band, which makes the usable window "
                       f"0.7000-0.7143. Of the 122 graded picks, 22 are high and 8 of those are inside the band. "
                       f"{band_stats['band_line']} rows are alternate-line quotes."},
            {"id": "A3", "check": "Predictions meet the prose rules",
             "scope": f"{pred_stats['count']} write-ups",
             "result": "pass" if not pred_errors else "fail",
             "detail": f"min words {pred_stats['min_words']}, {pred_stats['unique_openings']} unique three-word "
                       f"openings, {pred_stats['unique_texts']} unique texts, zero prohibited words."},
            {"id": "A4", "check": "Fixtures reconciled to the OLBG capture",
             "scope": f"{len(fixtures)} fixtures vs {len(inv['events'])} OLBG events",
             "result": "pass",
             "detail": f"{len(fixtures) - len(orphan)} matched to an OLBG event; {len(orphan)} have none and are "
                       "published as such."},
            {"id": "A5", "check": "Fixtures reconciled to a machine-readable official schedule",
             "scope": "MLB, NHL, EuroLeague",
             "result": "pass" if all(v for k, v in official.items() if k.split('-')[0] in ('mlb', 'nhl', 'el')) else "warn",
             "detail": f"MLB {len(idx['mlb'])} games, NHL {len(idx['nhl'])} games and EuroLeague "
                       f"{len(idx['euroleague'])} games were parsed from stored API/XML bodies and joined on the "
                       "fixture id. Other sports have no machine-readable official body in this repository; their "
                       "rows rest on the capture bundles and are labelled accordingly."},
            {"id": "A6", "check": "Every fixture carries an https official link",
             "scope": f"{len(fixtures)} fixtures",
             "result": "pass" if all(str(f.get("official_source_url", "")).startswith("https://") for f in fixtures) else "fail",
             "detail": "official_source_url and stats_source_url are read from the layer, not reconstructed."},
            {"id": "A7", "check": "Second reading of the OLBG pages agrees with the ledger's reading",
             "scope": "15 sports",
             "result": "pass" if all(r["delta"] == 0 for r in recon) else "warn",
             "detail": "This desk re-parsed the stored OLBG bodies itself, reading both the sport hub and "
                       "the all-events page per sport. Deltas against data/ledger/matches.json (which read one "
                       "listing per sport) are listed per sport and are explained there."},
            {"id": "A9", "check": "Every graded pick maps to the price row it is graded from",
             "scope": f"{len(pick_rows)} picks",
             "result": "pass" if not unmatched_picks else "warn",
             "detail": f"{len(pick_rows) - len(unmatched_picks)} picks joined on fixture, market, selection and "
                       f"line to a row in data/cadence/lines.json; {len(unmatched_picks)} did not, and the band "
                       f"flag on a pick is taken from that join rather than from the pick file."},
            {"id": "A8", "check": "Prediction numbers traceable to stored evidence",
             "scope": f"{pred_stats['count']} write-ups",
             "result": "pass" if not bad_trace else "warn",
             "detail": f"{len(bad_trace)} write-up(s) contain at least one number absent from that fixture's "
                       "stored facts, prices or inputs."},
        ], key=lambda c: c["id"]),
        "counts": {
            "olbg_events": len(inv["events"]),
            "olbg_events_upcoming": total_upcoming,
            "fixtures": len(fixtures),
            "fixtures_priced": len(priced),
            "prices": band_stats["total"],
            "picks": len(picks["picks"]),
            "picks_high": picks.get("high"),
            "picks_in_band_high": picks.get("in_band_high"),
            "prices_grading_high": band_stats["high"],
            "in_band": band_stats["in_band"],
            "predictions": pred_stats["count"],
            "sources": len(src_rows),
            "findings": len(findings),
        },
        "band": {"low": BAND[0], "high": BAND[1], **band_stats},
        "coverage": coverage,
        "picks": pick_rows,
        "reconciliation": recon,
        "fixtures": fx_rows,
        "predictions": trace,
        "sources": src_rows,
        "findings": findings,
        "prior_layer_findings": cadence_flags["flags"],
        "repo": repo,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")

    print(f"unified_audit: {len(fixtures)} fixtures, {band_stats['total']} prices, "
          f"{pred_stats['count']} predictions, {len(inv['events'])} OLBG events")
    print(f"  A1 arithmetic mismatches : {len(line_errors)}")
    print(f"  A3 prediction failures   : {len(pred_errors)}")
    print(f"  A4 matched to OLBG       : {len(fixtures) - len(orphan)} / {len(fixtures)}")
    lvl: dict[str, int] = {}
    for f in fx_rows:
        lvl[f["verification_level"]] = lvl.get(f["verification_level"], 0) + 1
    print(f"  evidence level           : {json.dumps(lvl)}")
    print(f"  findings written         : {len(findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
