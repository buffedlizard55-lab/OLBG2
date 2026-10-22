#!/usr/bin/env python3
"""Synchronize data/survey/sports.json and data/survey/events/*.json with
primary official governing-body fixture links and live 2026-10-21 OLBG hubs.

Remediates:
  - Adds Hurling (id 26, excluded) and UFC/MMA (id 27, excluded)
  - Aligns all 17 eligible OLBG sports (including Gaelic Football id 25,
    Greyhounds id 28, Basketball id 19, Golf id 4, Rugby League id 10)
  - Populates empty rugby_league.json with the 3 live 2026-10-21 OLBG markets
  - Populates gaelic_football.json (5 live county finals) and greyhounds.json
    (6 live UK race markets)
  - Upgrades darts.json, baseball.json, motor_racing.json, and snooker.json
    from stale snapshots to verified 2026-10-21 live records
  - Attaches per-row official_fixture_source on every verified fixture row
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURVEY = ROOT / "data" / "survey"
EVENTS = SURVEY / "events"
VERIFIED = ROOT / "data" / "verified"

SPORTS_TAXONOMY = [
    {"olbg_sport_id": 1, "slug": "Football", "name": "Football (soccer)", "included": False, "note": "Excluded by brief: 'soccer', 'football'.", "listing_url": None, "registry_source": "https://www.olbg.com/betting-tips/Football/1"},
    {"olbg_sport_id": 2, "slug": "Horse_Racing", "name": "Horse Racing", "included": False, "note": "Excluded by brief: 'horse racing'.", "listing_url": None, "registry_source": "https://www.olbg.com/betting-tips/Horse_Racing/2"},
    {"olbg_sport_id": 3, "slug": "Tennis", "name": "Tennis", "included": True, "note": "ATP Top-100 matches originated; WTA/Challenger unconfirmed ranks left blank.", "listing_url": "https://www.olbg.com/betting-tips/Tennis/3", "registry_source": "https://www.atptour.com/en/rankings/singles"},
    {"olbg_sport_id": 4, "slug": "Golf", "name": "Golf", "included": True, "note": "Outright tour events verified; lines left blank pending full field strokes-gained data.", "listing_url": "https://www.olbg.com/betting-tips/Golf/4", "registry_source": "https://www.pgatour.com/schedule"},
    {"olbg_sport_id": 6, "slug": "Boxing", "name": "Boxing", "included": False, "note": "Excluded by brief: 'boxing'.", "listing_url": None, "registry_source": "https://www.olbg.com/betting-tips/Boxing/6"},
    {"olbg_sport_id": 7, "slug": "Cricket", "name": "Cricket", "included": True, "note": "ICC fixtures verified; lines blank because icc-cricket.com renders ratings/scorecards client-side.", "listing_url": "https://www.olbg.com/betting-tips/Cricket/7", "registry_source": "https://www.icc-cricket.com/tournaments/mens-cricket-world-cup-league-2"},
    {"olbg_sport_id": 8, "slug": "Snooker", "name": "Snooker", "included": True, "note": "Northern Ireland Open R2 verified via WST; Top-36 matches originated.", "listing_url": "https://www.olbg.com/betting-tips/Snooker/8", "registry_source": "https://www.wst.tv/matches/"},
    {"olbg_sport_id": 9, "slug": "Rugby_Union", "name": "Rugby Union", "included": True, "note": "Top 14 Round 7, Pro D2 Round 8, and URC Round 4 verified from LNR & URC tables.", "listing_url": "https://www.olbg.com/betting-tips/Rugby_Union/9", "registry_source": "https://top14.lnr.fr/classement"},
    {"olbg_sport_id": 10, "slug": "Rugby_League", "name": "Rugby League", "included": True, "note": "3 active 2027 Grand Final / Premiership futures verified on OLBG off-season hub.", "listing_url": "https://www.olbg.com/betting-tips/Rugby_League/10", "registry_source": "https://www.nrl.com/draw/"},
    {"olbg_sport_id": 11, "slug": "American_Football", "name": "American Football", "included": False, "note": "Excluded by brief: 'american football'.", "listing_url": None, "registry_source": "https://www.olbg.com/betting-tips/American_Football/11"},
    {"olbg_sport_id": 12, "slug": "Baseball", "name": "Baseball", "included": True, "note": "2026 MLB World Series Game 1 (TB @ MIL, gamePk=849805) verified via MLB StatsAPI.", "listing_url": "https://www.olbg.com/betting-tips/Baseball/12", "registry_source": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-21&endDate=2026-10-26"},
    {"olbg_sport_id": 13, "slug": "Ice_Hockey", "name": "Ice Hockey", "included": True, "note": "NHL 2026-27 slate verified directly via api-web.nhle.com & api.nhle.com.", "listing_url": "https://www.olbg.com/betting-tips/Ice_Hockey/13", "registry_source": "https://api-web.nhle.com/v1/score/2026-10-21"},
    {"olbg_sport_id": 14, "slug": "Motor_Racing", "name": "Motor Racing", "included": True, "note": "2026 FIA Formula 1 Round 18 (Austin) & Drivers' Championship verified via formula1.com.", "listing_url": "https://www.olbg.com/betting-tips/Motor_Racing/14", "registry_source": "https://www.formula1.com/en/results/2026/drivers"},
    {"olbg_sport_id": 15, "slug": "Darts", "name": "Darts", "included": True, "note": "All 16 PDC European Championship Round 1 ties originated from pdc.tv/rankings.", "listing_url": "https://www.olbg.com/betting-tips/Darts/15", "registry_source": "https://www.pdc.tv/rankings"},
    {"olbg_sport_id": 17, "slug": "Cycling", "name": "Cycling", "included": False, "note": "Excluded by brief: 'cycling' (no active OLBG hub on 2026-10-21).", "listing_url": None, "registry_source": "https://www.olbg.com/sitemap-betting-tips.xml"},
    {"olbg_sport_id": 18, "slug": "Specials", "name": "Specials / Entertainment & Politics", "included": False, "note": "Excluded by brief: 'specials' (no active OLBG hub on 2026-10-21).", "listing_url": None, "registry_source": "https://www.olbg.com/sitemap-betting-tips.xml"},
    {"olbg_sport_id": 19, "slug": "Basketball", "name": "Basketball", "included": True, "note": "NBA opening week, EuroLeague R7, and BKT EuroCup R4 verified from official league feeds.", "listing_url": "https://www.olbg.com/betting-tips/Basketball/19", "registry_source": "https://www.euroleaguebasketball.net/en/euroleague/standings/"},
    {"olbg_sport_id": 20, "slug": "Handball", "name": "Handball", "included": True, "note": "EHF Champions League Men Round 5 fixtures verified via ehfcl.eurohandball.com.", "listing_url": "https://www.olbg.com/betting-tips/Handball/20", "registry_source": "https://ehfcl.eurohandball.com/men/2026-27/matches/"},
    {"olbg_sport_id": 21, "slug": "Volleyball", "name": "Volleyball", "included": True, "note": "Polish PlusLiga Round 2 verified on plusliga.pl; left blank at M=1.", "listing_url": "https://www.olbg.com/betting-tips/Volleyball/21", "registry_source": "https://www.plusliga.pl/games.html"},
    {"olbg_sport_id": 22, "slug": "Aussie_Rules", "name": "Aussie Rules", "included": True, "note": "Zero active markets on OLBG during AFL off-season.", "listing_url": "https://www.olbg.com/betting-tips/Aussie_Rules/22", "registry_source": "https://www.olbg.com/betting-tips/Aussie_Rules/22"},
    {"olbg_sport_id": 23, "slug": "eSports", "name": "eSports", "included": True, "note": "Zero active markets on OLBG hub on 2026-10-21.", "listing_url": "https://www.olbg.com/betting-tips/eSports/23", "registry_source": "https://www.olbg.com/betting-tips/eSports/23"},
    {"olbg_sport_id": 25, "slug": "Gaelic_Football", "name": "Gaelic Football", "included": True, "note": "5 county championship finals catalogued on OLBG; unlined due to absent official GAA tables.", "listing_url": "https://www.olbg.com/betting-tips/Gaelic_Football/25", "registry_source": "https://www.gaa.ie/football"},
    {"olbg_sport_id": 26, "slug": "Hurling", "name": "Hurling", "included": False, "note": "Excluded by brief: 'hurling' (active OLBG hub id 26 explicitly blocked).", "listing_url": None, "registry_source": "https://www.olbg.com/betting-tips/Hurling/26"},
    {"olbg_sport_id": 27, "slug": "UFC_MMA", "name": "UFC / MMA", "included": False, "note": "Excluded by brief: 'ufc', 'mma' (active OLBG hub id 27 explicitly blocked).", "listing_url": None, "registry_source": "https://www.olbg.com/betting-tips/UFC_MMA/27"},
    {"olbg_sport_id": 28, "slug": "Greyhounds", "name": "Greyhounds", "included": True, "note": "6 UK race markets catalogued on OLBG; unlined due to licensed GBGB trap data.", "listing_url": "https://www.olbg.com/betting-tips/Greyhounds/28", "registry_source": "https://www.gbgb.org.uk"},
]


def main() -> None:
    (SURVEY / "sports.json").write_text(json.dumps(SPORTS_TAXONOMY, indent=2, ensure_ascii=False) + "\n")
    vin = json.loads((VERIFIED / "inputs.json").read_text())

    # 1. Darts: all 16 live 2026-10-21 PDC European Championship R1 ties
    darts_rows = [
        {
            "match": f"{d['p1']} vs {d['p2']}",
            "competition": "PDC European Championship Round 1",
            "listed_time": d["time"],
            "market": "Win Match 2-way",
            "top_selection": d["p1"],
            "tips_for": None,
            "tips_total": None,
            "tip_pct": None,
            "event_id": int(d["id"].split("-")[1]),
            "source_url": d["olbg_url"],
            "official_fixture_source": "https://www.pdc.tv/rankings",
            "retrieved_via": "live_fetch",
            "as_of": "2026-10-21",
            "outright": False,
        }
        for d in vin["darts_fixtures"]
    ]
    (EVENTS / "darts.json").write_text(json.dumps(darts_rows, indent=2, ensure_ascii=False) + "\n")

    # 2. Rugby League: 3 live 2027 futures on OLBG Rugby_League/10
    rl_rows = [
        {
            "match": "Super League Grand Final 2027",
            "competition": "Super League 2027",
            "listed_time": "2027 Season Outright",
            "market": "Win Grand Final",
            "top_selection": None,
            "tips_for": None,
            "tips_total": None,
            "tip_pct": None,
            "event_id": 2695857,
            "source_url": "https://www.olbg.com/betting-tips/Rugby_League/10",
            "official_fixture_source": "https://www.superleague.co.uk/fixtures",
            "retrieved_via": "live_fetch",
            "as_of": "2026-10-21",
            "outright": True,
        },
        {
            "match": "NRL Telstra Premiership 2027",
            "competition": "NRL 2027",
            "listed_time": "2027 Season Outright",
            "market": "Win Premiership",
            "top_selection": None,
            "tips_for": None,
            "tips_total": None,
            "tip_pct": None,
            "event_id": 2801554,
            "source_url": "https://www.olbg.com/betting-tips/Rugby_League/10",
            "official_fixture_source": "https://www.nrl.com/draw/",
            "retrieved_via": "live_fetch",
            "as_of": "2026-10-21",
            "outright": True,
        },
        {
            "match": "NRL State of Origin Series 2027",
            "competition": "State of Origin 2027",
            "listed_time": "2027 Series Outright",
            "market": "Win Series",
            "top_selection": None,
            "tips_for": None,
            "tips_total": None,
            "tip_pct": None,
            "event_id": 2801600,
            "source_url": "https://www.olbg.com/betting-tips/Rugby_League/10",
            "official_fixture_source": "https://www.nrl.com/draw/",
            "retrieved_via": "live_fetch",
            "as_of": "2026-10-21",
            "outright": True,
        },
    ]
    (EVENTS / "rugby_league.json").write_text(json.dumps(rl_rows, indent=2, ensure_ascii=False) + "\n")

    # 3. Gaelic Football & Greyhounds from verified unlined live OLBG capture.
    # Only rows that carry a numeric OLBG event id are mirrored: rows sourced
    # from a governing body rather than the OLBG capture (e.g. the GBGB
    # Category One schedule rows gbgb-cat1-*) are published on the unified
    # desk but never presented here as OLBG discovery inventory.
    def _olbg_event_id(row):
        try:
            return int(row["id"].split("-")[1])
        except (IndexError, ValueError):
            return None

    gf_rows = []
    gh_rows = []
    for u in vin["unlined_rows"]:
        if _olbg_event_id(u) is None:
            continue
        if u["sport"] == "gaelic-football":
            gf_rows.append(
                {
                    "match": f"{u['home']} v {u['away']}" if u["away"] != "Field" else u["home"],
                    "competition": u["competition"],
                    "listed_time": u["time"],
                    "market": "Match Winner / Outright",
                    "top_selection": None,
                    "tips_for": None,
                    "tips_total": None,
                    "tip_pct": None,
                    "event_id": _olbg_event_id(u),
                    "source_url": u["olbg_url"],
                    "official_fixture_source": u["official_url"],
                    "retrieved_via": "live_fetch",
                    "as_of": "2026-10-21",
                    "outright": u["away"] == "Field",
                }
            )
        elif u["sport"] == "greyhounds":
            gh_rows.append(
                {
                    "match": u["home"],
                    "competition": u["competition"],
                    "listed_time": u["time"],
                    "market": "Win Race",
                    "top_selection": None,
                    "tips_for": None,
                    "tips_total": None,
                    "tip_pct": None,
                    "event_id": _olbg_event_id(u),
                    "source_url": u["olbg_url"],
                    "official_fixture_source": u["official_url"],
                    "retrieved_via": "live_fetch",
                    "as_of": "2026-10-21",
                    "outright": True,
                }
            )
    (EVENTS / "gaelic_football.json").write_text(json.dumps(gf_rows, indent=2, ensure_ascii=False) + "\n")
    (EVENTS / "greyhounds.json").write_text(json.dumps(gh_rows, indent=2, ensure_ascii=False) + "\n")

    # 4. Baseball live World Series Game 1
    (EVENTS / "baseball.json").write_text(
        json.dumps(
            [
                {
                    "match": "TB Rays @ MIL Brewers",
                    "competition": "2026 MLB World Series — Game 1",
                    "listed_time": "24 Oct 00:00 UTC",
                    "market": "Money Line",
                    "top_selection": "TB Rays",
                    "tips_for": 1,
                    "tips_total": 1,
                    "tip_pct": 100,
                    "event_id": 160789,
                    "source_url": "https://www.olbg.com/betting-tips/Baseball/12",
                    "official_fixture_source": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-21&endDate=2026-10-26",
                    "retrieved_via": "live_fetch",
                    "as_of": "2026-10-21",
                    "outright": False,
                }
            ],
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    # 5. Snooker: ensure all 6 existing rows + 2 originated WST Top-36 R2 matches carry official WST URLs
    snk = json.loads((EVENTS / "snooker.json").read_text())
    existing_snk = {r["match"] for r in snk}
    # Originated WST ties keep their fixture-level match-centre URL on every
    # run (idempotent); the remaining OLBG-listed rows point at the WST
    # matches index.
    originated_urls = {f"{s_row['p1']} v {s_row['p2']}": s_row["url"] for s_row in vin["snooker_originated"]}
    for r in snk:
        r["official_fixture_source"] = originated_urls.get(r["match"], "https://www.wst.tv/matches/")
    for s_row in vin["snooker_originated"]:
        mname = f"{s_row['p1']} v {s_row['p2']}"
        if mname not in existing_snk:
            snk.append(
                {
                    "match": mname,
                    "competition": "BetVictor Northern Ireland Open — Round 3" if s_row["id"].startswith("wst-2026-r3") else "BetVictor Northern Ireland Open — Round 2",
                    "listed_time": s_row["time"],
                    "market": "Win Match",
                    "top_selection": s_row["p1"],
                    "tips_for": None,
                    "tips_total": None,
                    "tip_pct": None,
                    "event_id": int(s_row["id"].split("-")[1]),
                    "source_url": s_row["olbg_url"],
                    "official_fixture_source": s_row["url"],
                    "retrieved_via": "live_fetch",
                    "as_of": "2026-10-21",
                }
            )
    (EVENTS / "snooker.json").write_text(json.dumps(snk, indent=2, ensure_ascii=False) + "\n")

    # 6. Attach official_fixture_source to all remaining event files where official governing-body feed exists
    default_official_by_sport = {
        "basketball": "https://www.nba.com/games?date=2026-10-21",
        "cricket": "https://www.icc-cricket.com/tournaments/mens-cricket-world-cup-league-2",
        "golf": "https://www.pgatour.com/schedule",
        "handball": "https://ehfcl.eurohandball.com/men/2026-27/matches/",
        "ice_hockey": "https://www.nhl.com/schedule",
        "motor_racing": "https://www.formula1.com/en/results/2026/drivers",
        "rugby_union": "https://top14.lnr.fr/calendrier-et-resultats",
        "tennis": "https://www.atptour.com/en/scores/current",
        "volleyball": "https://www.plusliga.pl/games.html",
    }
    for stem, default_url in default_official_by_sport.items():
        fpath = EVENTS / f"{stem}.json"
        rows = json.loads(fpath.read_text())
        for r in rows:
            m = r["match"]
            if stem == "rugby_union":
                if "Toulouse v Perpignan" == m:
                    r["official_fixture_source"] = "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan"
                elif any(k in m for k in ("Connacht", "Bulls", "Stormers", "Leinster", "Edinburgh", "Benetton", "Cardiff", "Ospreys")):
                    r["official_fixture_source"] = "https://stats.unitedrugby.com/match-centre/2026-27/4"
                elif r.get("outright"):
                    r["official_fixture_source"] = "https://www.world.rugby/rankings/mru"
                elif any(k in m for k in ("Toulouse", "Bayonne", "La Rochelle", "Pau", "Clermont", "Castres", "Toulon", "Stade Francais")):
                    r["official_fixture_source"] = "https://top14.lnr.fr/calendrier-et-resultats"
                else:
                    r["official_fixture_source"] = "https://prod2.lnr.fr/calendrier-et-resultats"
            elif stem == "basketball":
                if "@" in m:
                    r["official_fixture_source"] = "https://www.nba.com/games?date=2026-10-21"
                else:
                    r["official_fixture_source"] = "https://www.euroleaguebasketball.net/en/euroleague/game-center/"
            elif stem == "tennis":
                if any(w in m for w in ("Fernandez", "Ostapenko", "Tauson", "Shnaider", "Boulter", "Noskova", "Muchova", "Badosa", "Lys")):
                    r["official_fixture_source"] = "https://www.wtatennis.com/scores"
                else:
                    r["official_fixture_source"] = "https://www.atptour.com/en/scores/current"
            else:
                r.setdefault("official_fixture_source", default_url)
        fpath.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")

    print("survey_sync_inventory: synced 25 taxonomy entries (17 included / 8 excluded) and per-row official URLs")


if __name__ == "__main__":
    main()
