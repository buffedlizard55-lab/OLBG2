#!/usr/bin/env python3
"""Originate prices for the 2026-10-24 snapshot and grade the picks.

Method (documented in today/methodology.html):
  * strength  = points percentage from the official record (NHL: (2W+OTL)/2GP)
                or winning percentage (MLB).
  * home edge = 4.5 percentage points (NHL), 4.0 (MLB).
  * spread    = 0.85 x (strength_home - strength_away) + home edge.
  * probability is clamped to [0.12, 0.88] before a fair price is derived.
A fair American price is the reciprocal of that probability.  The market column is the
de-vigged two-way price from the league feed and is shown only for comparison.
No market price is ever copied into our own number.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
OUT = DATA

HOME_EDGE = {"NHL": 0.045, "MLB": 0.040}
CONF_HIGH = 0.65
CONF_MEDIUM = 0.55
BAND_LOW = -250
BAND_HIGH = 10000


def points_pct(record: str, sport: str) -> float:
    parts = [int(x) for x in record.split("-")]
    if sport == "NHL":
        w, l, otl = parts
        gp = w + l + otl
        return (2 * w + otl) / (2 * gp)
    w, l = parts
    return w / (w + l)


def american(p: float) -> int:
    if p >= 0.5:
        return -round(100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def decimal_to_american(d: float) -> int:
    if d >= 2.0:
        return round((d - 1) * 100)
    return -round(100 / (d - 1))


def main() -> None:
    payload = json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))
    fixtures = payload["fixtures"]
    league = {"Ice Hockey": "NHL", "Baseball": "MLB"}
    lines, picks = [], []

    for f in fixtures:
        lg = league[f["sport"]]
        ph = points_pct(f["home_record"], lg)
        pa = points_pct(f["away_record"], lg)
        spread = HOME_EDGE[lg] + 0.85 * (ph - pa)
        p_home = min(0.88, max(0.12, 0.5 + spread))
        p_away = 1 - p_home

        market_home = None
        if f.get("market_decimal_home"):
            i_h = 1 / f["market_decimal_home"]
            i_a = 1 / f["market_decimal_away"]
            market_home = round(i_h / (i_h + i_a), 4)

        for side, p, record in (("home", p_home, f["home_record"]), ("away", p_away, f["away_record"])):
            team = f[side]
            lines.append(dict(
                id=f"{f['id']}-ml-{side}", fixture_id=f["id"], sport=f["sport"], competition=f["competition"],
                market="Money line", selection=team, line=None,
                probability=round(p, 4), fair_american=american(p), fair_decimal=round(1 / p, 3),
                strength=round(ph if side == "home" else pa, 4), record=record,
                market_implied_home=market_home,
                source_url=f["source_url"], source_label=f["source_label"],
            ))

        # MLB total: expected runs from both clubs' season runs scored / allowed per game.
        if f["sport"] == "Baseball":
            lines.extend(mlb_total_lines(f, p_home, p_away))

        best_side = "home" if p_home >= p_away else "away"
        p = max(p_home, p_away)
        line = dict(
            fixture_id=f["id"], sport=f["sport"], competition=f["competition"],
            home=f["home"], away=f["away"], start_utc=f["start_utc"],
            selection=f[best_side], market="Money line", probability=round(p, 4),
            fair_american=american(p), fair_decimal=round(1 / p, 3),
            confidence="high" if p >= CONF_HIGH else ("medium" if p >= CONF_MEDIUM else "low"),
            in_band=BAND_LOW <= american(p) <= BAND_HIGH,
            market_implied=(market_home if best_side == "home" else (None if market_home is None else round(1 - market_home, 4))),
            olbg_event_id=f.get("olbg_event_id"), olbg_listed_selection=f.get("olbg_listed_selection"),
            source_url=f["source_url"], source_label=f["source_label"], start_source=f["start_source"],
        )
        picks.append(line)

    picks.sort(key=lambda r: (-r["probability"], r["sport"], r["fixture_id"]))
    payload_out = dict(
        as_of_utc=payload["capture_end_utc"],
        method="strength from official record + fixed home edge; fair price = 1/probability; market column is de-vigged league-feed price",
        thresholds=dict(high=CONF_HIGH, medium=CONF_MEDIUM, band=[BAND_LOW, BAND_HIGH]),
        count=len(lines), lines=lines,
    )
    (OUT / "lines.json").write_text(json.dumps(payload_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    top_by_sport, counts = {}, {}
    for p in picks:
        counts[p["sport"]] = counts.get(p["sport"], 0) + 1
        if counts[p["sport"]] <= 5:
            top_by_sport.setdefault(p["sport"], []).append(p)
    published = [p for sport in top_by_sport for p in top_by_sport[sport]]
    published.sort(key=lambda r: (-r["probability"], r["sport"]))
    (OUT / "picks.json").write_text(json.dumps(dict(
        as_of_utc=payload["capture_end_utc"], count=len(published), per_sport_limit=5,
        picks=published,
    ), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"today_model: {len(lines)} fair prices, {len(published)} published picks "
          f"({sum(1 for p in published if p['confidence']=='high')} high, "
          f"{sum(1 for p in published if p['in_band'])} inside the band)")


def mlb_total_lines(f, p_home, p_away):
    """Expected combined runs, then a totals market at 7.5 and 8.5 runs."""
    r = f["runs"]
    g = r["games"]
    exp_total = ((r["home_scored"] + r["away_allowed"]) / g + (r["away_scored"] + r["home_allowed"]) / g) / 2
    out = []
    import math
    for total in (7.5, 8.5):
        # Poisson tail on the expected combined total, split across both clubs.
        lam = exp_total
        p_under = sum(math.exp(-lam) * lam ** k / math.factorial(k) for k in range(int(total) + 1))
        for side, prob in (("Over", 1 - p_under), ("Under", p_under)):
            out.append(dict(
                id=f"{f['id']}-total-{str(total).replace('.', '')}-{side.lower()}",
                fixture_id=f["id"], sport=f["sport"], competition=f["competition"],
                market="Game total", selection=f"{side} {total}", line=total,
                probability=round(prob, 4), fair_american=american(prob), fair_decimal=round(1 / prob, 3),
                strength=None, record=None, market_implied_home=None,
                source_url=MLB_SCHED_SRC, source_label="MLB Stats API schedule + season standings",
                expected_total=round(exp_total, 3),
            ))
    return out


MLB_SCHED_SRC = ("https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24"
                 "&hydrate=probablePitcher,team")

if __name__ == "__main__":
    main()
