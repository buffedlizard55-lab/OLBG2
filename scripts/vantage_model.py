#!/usr/bin/env python3
"""Originates dated multi-market *fair estimates*, keeping offered quotes separate.

No OLBG tip count, comment, or bookmaker quote is a pricing input.  Match-winner,
handicap, and total calculations are performed only when both sides have first-hand
numeric official records, a league-confirmed future UTC start, and an OLBG event id.
Unconfirmed values stay None, with one per-row review flag.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vantage"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]
AS_OF = "2026-10-24T17:45:00Z"
# Own assumptions, NOT official match statistics. See /vantage/methodology.html.
NHL_PRIOR_GOALS = 3.1
NHL_SHRINK_GAMES = 10
NHL_HOME_FACTOR = 1.035
MLB_HOME_FACTOR = 1.03
RUGBY_PRIOR_POINTS = 25.0
HANDBALL_PRIOR_GOALS = 30.0
NORMAL_SHRINK_GAMES = 8
RUGBY_HOME_EDGE = 1.5
HANDBALL_HOME_EDGE = 1.0
RUGBY_MARGIN_SD = 16.0
HANDBALL_MARGIN_SD = 9.0
RUGBY_TOTAL_SD = 19.0
HANDBALL_TOTAL_SD = 11.0


def read(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def write(name: str, payload: dict) -> None:
    (DATA / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def american(p: float) -> int:
    if not 0 < p < 1:
        raise ValueError(f"invalid probability {p}")
    return -round(100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)


def pmf(lam: float, n: int = 35) -> list[float]:
    """Poisson distribution; tiny truncated tail explicitly tested before use."""
    vals = [math.exp(-lam)]
    for k in range(1, n + 1):
        vals.append(vals[-1] * lam / k)
    assert sum(vals) > 0.999999, (lam, sum(vals))
    return vals


def nhl_prices(stats: dict) -> tuple[dict, dict[str, float]]:
    h, a = stats["home"], stats["away"]
    wh, wa = h["gp"] / (h["gp"] + NHL_SHRINK_GAMES), a["gp"] / (a["gp"] + NHL_SHRINK_GAMES)
    ah = 1 + wh * (h["gf"] / h["gp"] / NHL_PRIOR_GOALS - 1)
    dh = 1 + wh * (h["ga"] / h["gp"] / NHL_PRIOR_GOALS - 1)
    aa = 1 + wa * (a["gf"] / a["gp"] / NHL_PRIOR_GOALS - 1)
    da = 1 + wa * (a["ga"] / a["gp"] / NHL_PRIOR_GOALS - 1)
    lh = NHL_PRIOR_GOALS * ah * da * NHL_HOME_FACTOR
    la = NHL_PRIOR_GOALS * aa * dh / NHL_HOME_FACTOR
    ph, pa = pmf(lh), pmf(la)
    h_ml = h_minus = tie = 0.0
    for i, v in enumerate(ph):
        for j, z in enumerate(pa):
            product = v * z
            if i > j:
                h_ml += product
            if i == j:
                tie += product
            if i - j >= 2:
                h_minus += product
    h_ml += 0.5 * tie  # own convention for OT/shootout, not a factual result
    # A whole-goal line can push; choose an independent half-goal total.
    threshold = math.floor(lh + la) + 0.5
    under = sum(v * z for i, v in enumerate(ph) for j, z in enumerate(pa) if i + j < threshold)
    prices = dict(moneyline_home=h_ml, moneyline_away=1 - h_ml,
                  handicap_home_minus_1_5=h_minus, handicap_away_plus_1_5=1 - h_minus,
                  under=under, over=1 - under)
    return dict(lambda_home=round(lh, 4), lambda_away=round(la, 4), total_line=threshold,
                handicap_line=1.5, source=stats["input_url"],
                convention="two-way winner incl. OT/SO by tie split; totals and puck line are simplified regulation-goal estimates"), prices


def mlb_prices(stats: dict) -> tuple[dict, dict[str, float]]:
    h, a = stats["home"], stats["away"]
    # Regular-season team run rates only; pitcher ERA is narrated, not fitted.
    lh = (h["rs"] / h["gp"] + a["ra"] / a["gp"]) / 2 * MLB_HOME_FACTOR
    la = (a["rs"] / a["gp"] + h["ra"] / h["gp"]) / 2 / MLB_HOME_FACTOR
    ph, pa = pmf(lh), pmf(la)
    h_ml = h_runline = tie = 0.0
    for i, v in enumerate(ph):
        for j, z in enumerate(pa):
            q = v * z
            if i > j:
                h_ml += q
            if i == j:
                tie += q
            if i - j >= 2:
                h_runline += q
    h_ml += .5 * tie  # crude extra-inning assumption, independent of MLB result
    threshold = math.floor(lh + la) + .5
    under = sum(v * z for i, v in enumerate(ph) for j, z in enumerate(pa) if i + j < threshold)
    prices = dict(moneyline_home=h_ml, moneyline_away=1 - h_ml,
                  handicap_home_minus_1_5=h_runline, handicap_away_plus_1_5=1 - h_runline,
                  under=under, over=1 - under)
    return dict(lambda_home=round(lh, 4), lambda_away=round(la, 4), total_line=threshold,
                handicap_line=1.5, source=stats["input_url"],
                convention="season run-rate Poisson with a 50/50 tie split; no pitcher or extra-inning fit"), prices


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def normal_prices(stats: dict, *, kind: str) -> tuple[dict, dict[str, float]]:
    h, a = stats["home"], stats["away"]
    if kind == "rugby":
        prior, edge, margin_sd, total_sd, hc = RUGBY_PRIOR_POINTS, RUGBY_HOME_EDGE, RUGBY_MARGIN_SD, RUGBY_TOTAL_SD, 3.5
    else:
        prior, edge, margin_sd, total_sd, hc = HANDBALL_PRIOR_GOALS, HANDBALL_HOME_EDGE, HANDBALL_MARGIN_SD, HANDBALL_TOTAL_SD, 2.5
    # Shrink each team's two-sided scoring input independently to the stated prior.
    def projected(team, other):
        raw = (team["pf"] / team["gp"] + other["pa"] / other["gp"]) / 2
        weight = min(team["gp"], other["gp"]) / (min(team["gp"], other["gp"]) + NORMAL_SHRINK_GAMES)
        return prior + weight * (raw - prior)
    mu_h = projected(h, a) + edge
    mu_a = projected(a, h)
    margin, total = mu_h - mu_a, mu_h + mu_a
    # Three-way regulation winner: signed margin >+0.5 (home), <-0.5 (away),
    # otherwise draw. This is a transparent approximation, not a calibrated fit.
    home_win = 1 - norm_cdf((0.5 - margin) / margin_sd)
    away_win = norm_cdf((-0.5 - margin) / margin_sd)
    draw = 1 - home_win - away_win
    home_cover = 1 - norm_cdf((hc - margin) / margin_sd)
    # Half-point total nearest our projection (own hypothetical market).
    threshold = math.floor(total) + .5
    under = norm_cdf((threshold - total) / total_sd)
    prices = dict(home_1x2=home_win, draw_1x2=draw, away_1x2=away_win,
                  handicap_home_minus=home_cover, handicap_away_plus=1 - home_cover,
                  under=under, over=1 - under)
    return dict(mean_home=round(mu_h, 4), mean_away=round(mu_a, 4), total_line=threshold,
                handicap_line=hc, margin_sd=margin_sd, total_sd=total_sd,
                source=stats["input_url"], convention="regular-time 1X2 (not two-way incl. overtime); Gaussian difference and total"), prices


def market_rows(fixture: dict) -> tuple[dict, list[dict]]:
    stats = fixture["stats"]
    if stats["kind"] == "nhl":
        detail, ps = nhl_prices(stats)
        kind = ("Money line (incl. OT/SO)", "Puck line ±1.5", "Game total")
        spec = [(kind[0], fixture["home"], None, "moneyline_home", "home"),
                (kind[0], fixture["away"], None, "moneyline_away", "away"),
                (kind[1], f"{fixture['home']} -1.5", -1.5, "handicap_home_minus_1_5", None),
                (kind[1], f"{fixture['away']} +1.5", +1.5, "handicap_away_plus_1_5", None),
                (kind[2], f"Under {detail['total_line']}", detail["total_line"], "under", None),
                (kind[2], f"Over {detail['total_line']}", detail["total_line"], "over", None)]
    elif stats["kind"] == "mlb":
        detail, ps = mlb_prices(stats)
        kind = ("Money line (incl. extras)", "Run line ±1.5", "Game total")
        spec = [(kind[0], fixture["home"], None, "moneyline_home", None),
                (kind[0], fixture["away"], None, "moneyline_away", None),
                (kind[1], f"{fixture['home']} -1.5", -1.5, "handicap_home_minus_1_5", None),
                (kind[1], f"{fixture['away']} +1.5", +1.5, "handicap_away_plus_1_5", None),
                (kind[2], f"Under {detail['total_line']}", detail["total_line"], "under", None),
                (kind[2], f"Over {detail['total_line']}", detail["total_line"], "over", None)]
    else:
        detail, ps = normal_prices(stats, kind=stats["kind"])
        kind = ("1X2 (regular time)", "Handicap (regular time)", "Total (regular time)")
        hc = detail["handicap_line"]
        spec = [(kind[0], fixture["home"], None, "home_1x2", None),
                (kind[0], "Draw", None, "draw_1x2", None),
                (kind[0], fixture["away"], None, "away_1x2", None),
                (kind[1], f"{fixture['home']} -{hc:g}", -hc, "handicap_home_minus", None),
                (kind[1], f"{fixture['away']} +{hc:g}", hc, "handicap_away_plus", None),
                (kind[2], f"Under {detail['total_line']}", detail["total_line"], "under", None),
                (kind[2], f"Over {detail['total_line']}", detail["total_line"], "over", None)]
    out = []
    for market, selection, number, key, quote_side in spec:
        p = ps[key]
        assert 0 < p < 1, (fixture["id"], key, p)
        quote = fixture.get("offered_quote") if quote_side else None
        observed = quote.get(f"{quote_side}_american") if quote else None
        out.append(dict(id=f"{fixture['id']}-{key}", fixture_id=fixture["id"], sport=fixture["sport"],
                        start_utc=fixture["start_utc"], market=market, selection=selection, line=number,
                        probability=round(p, 6), fair_american=american(p),
                        fair_decimal=round(1 / p, 4), fair_in_band=-250 <= american(p) <= 10000,
                        observed_american=observed, observed_source_url=quote["source_url"] if quote else None,
                        observed_in_band=(-250 <= observed <= 10000) if observed is not None else None,
                        olbg_offered_price=None, official_source_url=fixture["official_url"],
                        stats_source_url=stats["input_url"],
                        availability="OLBG event recorded; current market availability and odds unconfirmed"))
    if stats["kind"] in ("nhl", "mlb"):
        assert abs(ps["moneyline_home"] + ps["moneyline_away"] - 1) < 1e-9
    else:
        assert abs(ps["home_1x2"] + ps["draw_1x2"] + ps["away_1x2"] - 1) < 1e-9
    return detail, out


def generate() -> tuple[dict, dict, dict]:
    first = read("discovery.json")
    fixture_records = read("fixtures.json")["fixtures"]
    as_of = datetime.fromisoformat(AS_OF.replace("Z", "+00:00"))
    fixture_by_id = {f["olbg_event_id"]: f for f in fixture_records}
    assert len(fixture_by_id) == len(fixture_records)
    all_rows = []
    priced = []
    lines = []
    for listing in first["listings"]:
        f = fixture_by_id.get(listing["event_id"])
        official_started = f is not None and f["start_utc"] is not None and \
            datetime.fromisoformat(f["start_utc"].replace("Z", "+00:00")) <= as_of
        soon = bool(f and f["start_utc"] and not official_started and
                    datetime.fromisoformat(f["start_utc"].replace("Z", "+00:00")) <= as_of + timedelta(minutes=90))
        # Fail closed: time uncertainty, score started, imminently starting (may be
        # started before the Pages deployment), or explicit official conflict = no price.
        conflict = f is not None and f["id"] in {"cricket-sa-aus-3rd-test", "volley-perugia-prata"}
        future = bool(f and f["start_utc"] and not official_started and not soon and not conflict)
        state = ("unverified listing" if not f else "official page labels this live; withheld" if f["id"] == "wst-williams-jones" else
                 "started before capture" if official_started else "timing / name conflict" if conflict else
                 "starts within 90 minutes; withheld" if soon else "start time unconfirmed" if not f["start_utc"] else "confirmed future at capture")
        row = dict(id=f["id"] if f else f"olbg-{listing['event_id']}", sport=listing["sport"],
                   competition=f["competition"] if f else None, official_home=f["home"] if f else None,
                   official_away=f["away"] if f else None, official_date=f["date"] if f else None,
                   official_start_utc=f["start_utc"] if f else None,
                   official_published_start=f["published_start"] if f else None,
                   official_venue=f["venue"] if f else None, official_confirmed=bool(f),
                   fixture_source_url=f["official_url"] if f else None,
                   review_target_url=("https://www.wtatennis.com/tournaments/405/osaka/2026/draws"
                                      if listing["event_id"] == "902171" else
                                      read("olbg_taxonomy.json")["hubs"][SPORTS.index(listing["sport"])]["official_check_target"]),
                   official_status=state, official_note=f["status_note"] if f else "No same-event official confirmation in this research window",
                   olbg_event_id=listing["event_id"], olbg_event_url=listing["url"],
                   olbg_listing=listing["event"], olbg_displayed_time=listing["displayed_time"],
                   olbg_top_selection=listing["selection"], olbg_top_market=listing["market"],
                   olbg_tip_fraction=listing["tips"],
                   primary_selection=None, primary_confidence=None, primary_probability=None,
                   primary_fair_american=None, primary_observed_american=None,
                   primary_market=None, prediction_id=None,
                   line_reason="Official matching fixture, start and both sides' numeric strength inputs required",
                   future_at_capture=future, sports_scope="exact fifteen")
        if f and f["stats"] and future:
            detail, market = market_rows(f)
            priced.append(dict(fixture_id=f["id"], sport=f["sport"], official_url=f["official_url"],
                               olbg_event_url=listing["url"], start_utc=f["start_utc"],
                               home=f["home"], away=f["away"], statistics=f["stats"],
                               estimate=detail))
            lines.extend(market)
            winner_key = "moneyline_home" if f["stats"]["kind"] in ("nhl", "mlb") else "home_1x2"
            opp_key = "moneyline_away" if f["stats"]["kind"] in ("nhl", "mlb") else "away_1x2"
            win_rows = [x for x in market if x["id"].endswith(winner_key) or x["id"].endswith(opp_key)]
            lead = max(win_rows, key=lambda x: x["probability"])
            conf = "high" if lead["probability"] >= .70 else "medium" if lead["probability"] >= .58 else "low"
            # Real limits: five 2026/27 EHF games or three URC rounds are too few for a
            # high-confidence recommendation; an MLB season record cannot calibrate a WS price.
            if f["stats"]["kind"] != "nhl":
                conf = "medium" if conf == "high" and f["stats"]["kind"] == "mlb" else "low" if conf == "high" else conf
            if f["stats"]["kind"] == "rugby":
                conf = "low"  # <=6 matches and draw assumptions
            row.update(primary_selection=lead["selection"], primary_market=lead["market"],
                       primary_probability=lead["probability"], primary_confidence=conf,
                       primary_fair_american=lead["fair_american"],
                       primary_observed_american=lead["observed_american"],
                       primary_line_id=lead["id"], line_reason=None)
        elif f and not future:
            row["line_reason"] = "Started, within 90 minutes of capture, time unconfirmed, or conflicting official details"
        elif f and not f["stats"]:
            row["line_reason"] = "Both sides' matched, dated numeric performance inputs unavailable"
        all_rows.append(row)
    confirmed = sum(r["official_confirmed"] for r in all_rows)
    match_payload = dict(as_of_utc=AS_OF, listings=len(all_rows), first_page_only=True,
                         confirmed=confirmed, unknown=len(all_rows) - confirmed,
                         priced=len(priced), matches=all_rows)
    line_payload = dict(as_of_utc=AS_OF, count=len(lines), fixtures=len(priced),
                        basis="our own fair estimates; not quoted OLBG odds", assumptions=dict(
                            NHL_PRIOR_GOALS=NHL_PRIOR_GOALS, NHL_SHRINK_GAMES=NHL_SHRINK_GAMES,
                            NHL_HOME_FACTOR=NHL_HOME_FACTOR, MLB_HOME_FACTOR=MLB_HOME_FACTOR,
                            RUGBY_PRIOR_POINTS=RUGBY_PRIOR_POINTS, HANDBALL_PRIOR_GOALS=HANDBALL_PRIOR_GOALS,
                            NORMAL_SHRINK_GAMES=NORMAL_SHRINK_GAMES,
                            RUGBY_HOME_EDGE=RUGBY_HOME_EDGE, HANDBALL_HOME_EDGE=HANDBALL_HOME_EDGE,
                            RUGBY_MARGIN_SD=RUGBY_MARGIN_SD, HANDBALL_MARGIN_SD=HANDBALL_MARGIN_SD,
                            RUGBY_TOTAL_SD=RUGBY_TOTAL_SD, HANDBALL_TOTAL_SD=HANDBALL_TOTAL_SD),
                        detail=priced, lines=lines)
    picks = []
    for r in all_rows:
        if not r["primary_selection"]:
            continue
        line = next(x for x in lines if x["id"] == r["primary_line_id"])
        picks.append(dict(id=f"pick-{r['id']}", fixture_id=r["id"], sport=r["sport"],
                          competition=r["competition"], official_home=r["official_home"],
                          official_away=r["official_away"], start_utc=r["official_start_utc"],
                          selection=r["primary_selection"], market=r["primary_market"],
                          confidence=r["primary_confidence"], probability=r["primary_probability"],
                          fair_american=r["primary_fair_american"], fair_in_band=line["fair_in_band"],
                          observed_american=line["observed_american"], observed_in_band=line["observed_in_band"],
                          olbg_offered_price=None, olbg_event_url=r["olbg_event_url"],
                          olbg_top_selection=r["olbg_top_selection"],
                          official_url=r["fixture_source_url"], stats_source_url=line["stats_source_url"],
                          notes="Independent estimate, not a bookmaker quote. Confirm the actual OLBG market and bookmaker price before any use."))
    picks.sort(key=lambda r: (-r["probability"], r["start_utc"], r["id"]))
    return match_payload, line_payload, dict(as_of_utc=AS_OF, count=len(picks),
                                             high=sum(p["confidence"] == "high" for p in picks),
                                             medium=sum(p["confidence"] == "medium" for p in picks),
                                             low=sum(p["confidence"] == "low" for p in picks),
                                             focused=sum(p["confidence"] == "high" and p["fair_in_band"] and p["observed_in_band"] is True for p in picks),
                                             picks=picks)


def main():
    matches, lines, picks = generate()
    for name, payload in (("matches.json", matches), ("lines.json", lines), ("picks.json", picks)):
        write(name, payload)
    print(f"vantage_model: {matches['listings']} OLBG listings, {matches['confirmed']} official matched, "
          f"{lines['fixtures']} dated priced fixtures, {lines['count']} fair selections, {picks['focused']} in-band high with separate observed quote")


if __name__ == "__main__":
    main()
