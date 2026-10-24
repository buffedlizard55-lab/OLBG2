#!/usr/bin/env python3
"""Generate a row-by-row review queue: absence of evidence stays visible."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vantage"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def generate():
    matches = read("matches.json")["matches"]
    picks = read("picks.json")["picks"]
    previews = read("predictions.json")["predictions"]
    index = {s: h for s, h in ((h["sport"], h) for h in read("olbg_taxonomy.json")["hubs"])}
    highs = Counter(p["sport"] for p in previews if p["confidence"] == "high")
    flags = []
    for sport in SPORTS:
        hub = index[sport]
        flags.append(dict(id=f"V-GAP-{sport.lower().replace(' ', '-')}", severity="high",
                          category="five-per-sport shortfall", sport=sport,
                          summary=f"{sport}: {highs[sport]} / 5 high-confidence 30+ word write-ups",
                          detail=(f"{hub['listings']} OLBG first-page event rows; {hub['official_matches']} authority-matched event records (including disclosed indexed-only reads). "
                                  "No additional high-confidence, quoted, verified-future match met the evidence gate. "
                                  "Do not manufacture missing predictions to reach five."),
                          missing_fields=["remaining high-confidence predictions"],
                          official_url=hub["official_check_target"], official_link_role="review target; not proof of unconfirmed events",
                          olbg_url=hub["url"]))
    for row in matches:
        if row["official_confirmed"] and row["primary_selection"]:
            continue
        missing = (["confirmed fixture", "official kickoff", "numeric inputs", "originated line", "prediction"]
                   if not row["official_confirmed"] else
                   ["safe future start or sufficient aligned numeric inputs", "originated line", "prediction"])
        flags.append(dict(id=f"V-ROW-{row['olbg_event_id']}", severity="medium",
                          category="unverified listing" if not row["official_confirmed"] else "unpriced official match",
                          sport=row["sport"], summary=row["olbg_listing"],
                          detail=(f"OLBG says {row['olbg_displayed_time']}. {row['official_status']}. "
                                  f"{row['official_note'] or ''} {row['line_reason'] or ''}").strip(),
                          missing_fields=missing,
                          official_url=row["fixture_source_url"] or row["review_target_url"],
                          official_link_role="fixture confirmed" if row["fixture_source_url"] else "review target only; not evidence for OLBG claim",
                          olbg_url=row["olbg_event_url"]))
    for code, sport, title, detail, official, olbg in [
        ("V-SCOPE", "All", "OLBG inventory incomplete", "The imported 96 rows are the first visible hub page only. Load More Tips and inline promotional cards mean the complete active slate and all markets were not captured.",
         "https://www.olbg.com/betting-tips/Volleyball/21", "https://www.olbg.com/betting-tips/Volleyball/21"),
        ("V-PRICE", "All", "No current OLBG bookmaker price", "OLBG pages surfaced no numeric offered odds. A fair price inside -250 to +10000 does not prove an actual bet is offered; NHL game data separately supplied league-served FanDuel snapshots, which may expire before reading.",
         "https://api-web.nhle.com/v1/score/2026-10-24", "https://www.olbg.com/betting-tips/Ice_Hockey/13"),
        ("V-NHL-SENSITIVITY", "Ice Hockey", "High grade is sensitive to prior/home edge", "Boston's 70.4% (fair -238) is an uncalibrated Poisson estimate from 11-game team goals. Repeating the calculation with eight prior games yields 72.1% (fair -258), outside the band; twelve prior games yields 69.0% (fair -223), below high. No injury/starting-goalie adjustment was applied.",
         "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2", "https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/SJ_Sharks_@_BOS_Bruins/13?event_id=200007"),
        ("V-UNCONFIRMED-INJURIES", "All", "No official injury claim attached to predictions", "The NHL league summary, EHF table, MLB stats and Top 14 table do not constitute game-specific injury reports. Blank injury cells mean unknown, not injury-free.",
         "https://api-web.nhle.com/v1/score/2026-10-24", "https://www.olbg.com/betting-tips"),
        ("V-NBA-TIMES", "Basketball", "Two OLBG NBA times disagree with official report", "OLBG listed NOP@DEN at 22:00 and GSW@PHX at 23:00. The NBA 1:00 pm ET injury report lists NOP@DEN at 21:00 and GSW@PHX at 22:00 ET. Only the official reported times are used, and no basketball price was originated from 1-2 games.",
         "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-24_01_00PM.pdf", "https://www.olbg.com/betting-tips/Basketball/4"),
        ("V-CRICKET-DATE", "Cricket", "OLBG uses last Test day as displayed start", "OLBG dates South Africa v Australia as 31 October, while Cricket South Africa and Cricket Australia schedule the third Test to begin 27 October. The start time also differs across the two official sources, so it remains blank.",
         "https://cricket.co.za/csa-announces-unmissable-2026-27-home-season-for-the-proteas-men/", "https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/South_Africa_vs_Australia/7?event_id=188835"),
        ("V-WTA-DRAW", "Tennis", "Osaka final participants unconfirmed at cut", "OLBG has Krueger v Siniakova as a final. WTA Osaka draw at the reading point still displayed semifinals, so this listing is not treated as a confirmed final or assigned a price.",
         "https://www.wtatennis.com/tournaments/405/osaka/2026/draws", "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Ashlyn_Krueger_vs_Katerina_Siniakova/3?event_id=902171"),
        ("V-HANDBALL-TIPS", "Handball", "75% Tie is tip share, not true draw chance", "OLBG Magdeburg–Kriens event page shows 3 of 4 tipsters backing Tie. EHF table shows Magdeburg 5-0 and Kriens 2-3. Neither figure alone estimates the other; our 1X2 remains an expressly uncalibrated fair estimate.",
         "https://ehfcl.eurohandball.com/men/2026-27/standings/", "https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/SC_Magdeburg_vs_HC_Kriens_Luzern/20?event_id=12136"),
        ("V-SWISS", "Ice Hockey", "Swiss National League listings not matched", "The Switzerland NLA rows on OLBG appear in the first page but no game-specific fixture, start and season scoring pair was confirmed from an official Swiss league source in this pass. They remain entirely blank on the official side.",
         "https://www.nationalleague.ch/", "https://www.olbg.com/betting-tips/Ice_Hockey/13"),
        ("V-GBGB", "Greyhounds", "Final and generic daily race cannot be equated", "GBGB confirms a Saturday Scurry Gold Cup final and Avarua Lake among its entrants, but not the 9:18 Dunstall Park OLBG daily race name, trap or price. The GBGB article is a review target, not confirmation of the individual OLBG race.",
         "https://www.gbgb.org.uk/shadow-storm-chases-scurry-gold-cup-history-at-dunstall-park/", "https://www.olbg.com/betting-tips/Greyhounds/28"),
        ("V-GOLF", "Golf", "Golf hub has zero tips while PGA event is in progress", "PGA Tour identifies the Butterfield Bermuda Championship on 22–25 October, but the OLBG Golf hub answered No tips found. No golf pick is created from a third-party market or inferred event.",
         "https://www.pgatour.com/leaderboard", "https://www.olbg.com/betting-tips/Golf/5"),
        ("V-RUGBY-LEAGUE", "Rugby League", "Only 2027 futures, no OLBG match", "The three captured OLBG entries are 2027 outright futures. The NRL's 2026 World Cup fixtures are official context, not evidence that OLBG offers match markets for those games.",
         "https://www.nrl.com/news/2026/10/20/world-cup-team-lists-mens-round-2/", "https://www.olbg.com/betting-tips/Rugby_League/10"),
        ("V-NZC-TIME", "Cricket", "NZC reader-local time varies across reads", "NZ Cricket's 27 October third T20I match page showed different reader-local clocks on separate reads without a timezone label. The fixture and venue are confirmed, but its start UTC is blank in this desk.",
         "https://scoring.nzc.nz/match/35de7c5e-f734-4003-89db-59d7081e9d29", "https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/New_Zealand_vs_India_3rd_T20_Match/7?event_id=188852"),
        ("V-NHL-CGY", "Ice Hockey", "Calgary goals input not independently recovered", "The Calgary entry straddled a truncated tool-output boundary. Its complete goals-for/goals-against pair was not independently checked for this pass, so Detroit–Calgary retains an official fixture but blank fair lines.",
         "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2", "https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/DET_Red_Wings_@_CGY_Flames/13?event_id=200004"),
        ("V-PDC-INDEX", "Darts", "PDC direct page is a cookie wall", "The PDC article URL exposed only a cookie-consent page on direct read. The official-site indexed excerpt supplied the two evening pairings, but no exact start could be independently recovered; no darts price or selection is published.",
         "https://www.pdc.tv/news/2026/october/24/2026-machineseeker-european-championship---day-three-latest", "https://www.olbg.com/betting-tips/Darts/15"),
        ("V-WTA-INDEX", "Tennis", "Osaka draw not exposed on direct read", "The official WTA draw page returned notifications instead of draw cells. An official-site search-indexed excerpt still showed semifinals; the OLBG Krueger–Siniakova final was not treated as confirmed, and no price was originated.",
         "https://www.wtatennis.com/tournaments/405/osaka/2026/draws", "https://www.olbg.com/betting-tips/Tennis/3"),
        ("V-ATP-TIME", "Tennis", "Not-before time is a lower bound, not a kickoff", "ATP's Almaty daily schedule says the Medvedev–Basilashvili final is not before 15:00 local, following another match and concert. The exact start is unconfirmed, so this desk leaves official start UTC blank and publishes no pre-match pick.",
         "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule", "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Daniil_Medvedev_vs_Nikoloz_Basilashvili/3?event_id=902251"),
    ]:
        flags.append(dict(id=code, severity="high" if code in ("V-PRICE", "V-CRICKET-DATE", "V-NBA-TIMES") else "medium",
                          category="cross-source irregularity", sport=sport, summary=title, detail=detail,
                          missing_fields=["source resolution or independently confirmed bookmaker availability"],
                          official_url=official, official_link_role="official check source" if "olbg.com" not in official else "OLBG discovery source, not official governing body",
                          olbg_url=olbg))
    payload = dict(as_of_utc=read("matches.json")["as_of_utc"], count=len(flags),
                   by_category=dict(Counter(r["category"] for r in flags)),
                   flags=flags)
    return payload


def main():
    payload = generate()
    (DATA / "flagged.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"vantage_flags: {payload['count']} flagged rows; {payload['by_category']}")


if __name__ == "__main__":
    main()
