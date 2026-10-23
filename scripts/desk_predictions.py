#!/usr/bin/env python3
"""Write the human predictions for high-confidence selections and the flag register.

Every paragraph is written for one named selection, is at least 30 words, opens
differently from the others, and uses only figures that appear in
data/olbgdesk/inputs.json and were read first-hand from the NHL feed. No injury
sentence is written for any fixture because no official injury report was
captured; that omission is published as a flag rather than padded with guesses.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NHL_SRC = "https://api.nhle.com/stats/rest/en/team/summary?isAggregate=false&isGame=false&sort=teamFullName&dir=ASC&factCayenneExp=gamesPlayed%3E=1&cayenneExp=gameTypeId=2%20and%20seasonId%3C=20262027%20and%20seasonId%3E=20262027"
SCORE = {"2026-10-23": "https://api-web.nhle.com/v1/score/2026-10-23",
         "2026-10-24": "https://api-web.nhle.com/v1/score/2026-10-24"}

PREDICTIONS = [
 {
  "sid": "nhl-2026020166", "market": "Puck Line +1.5", "selection": "Montreal Canadiens",
  "match": "Montreal Canadiens at Chicago Blackhawks", "start_utc": "2026-10-24T00:00:00Z",
  "text": "Montreal carry a 4-3-2 record into the United Center and have scored 28 goals in nine games, 3.11 per night, while conceding 3.78. Cole Caufield has six goals for the Canadiens, Nick Suzuki seven assists and Jacob Fowler three wins. Chicago are 3-6-0, have scored 21 and conceded 36 in nine, a rate of 4.00 against per game, so a one-goal margin either way is the likeliest outcome. Montreal +1.5 is the selection.",
  "facts": ["Montreal 4-3-2, 28 GF in 9 GP = 3.11 per game, 3.78 conceded",
            "Caufield 6 goals, Suzuki 7 assists, Fowler 3 wins",
            "Chicago 3-6-0, 21 GF, 36 GA in 9 GP = 4.00 conceded per game", "Line +1.5"],
  "sources": [NHL_SRC, SCORE["2026-10-23"]],
 },
 {
  "sid": "nhl-2026020168", "market": "Puck Line +1.5", "selection": "Anaheim Ducks",
  "match": "Anaheim Ducks at Philadelphia Flyers", "start_utc": "2026-10-24T17:00:00Z",
  "text": "Anaheim's ten games have produced 27 goals for and 33 against, a 6.00-goal combined profile, and they meet a Philadelphia side scoring 1.67 per game. The Flyers are 3-6-3 with 20 goals for and 36 against in twelve outings, so winning by two clear goals has been rare for them. Beckett Sennecke has five goals for the Ducks, Leo Carlsson nine assists and Lukas Dostal three wins, while Matvei Michkov's six goals carry Philadelphia's attack.",
  "facts": ["Anaheim 4-6-0, 27 GF, 33 GA in 10 GP = 6.00 combined per game",
            "Philadelphia 3-6-3, 20 GF, 36 GA in 12 GP = 1.67 per game",
            "Sennecke 5 goals, Carlsson 9 assists, Dostal 3 wins", "Michkov 6 goals"],
  "sources": [NHL_SRC, SCORE["2026-10-24"]],
 },
 {
  "sid": "nhl-2026020170", "market": "Money Line", "selection": "Boston Bruins",
  "match": "San Jose Sharks at Boston Bruins", "start_utc": "2026-10-24T23:00:00Z",
  "text": "Boston's 8-2-1 start rests on 42 goals scored and only 22 conceded in eleven games, a plus-20 differential. San Jose are 6-4-1 but have conceded four more than they have scored, 36 against 32 across eleven. The Bruins' 2.00 goals against per game is the lowest of the twelve clubs on this board, and TD Garden is the venue. Boston on the money line is the selection.",
  "facts": ["Boston 8-2-1, 42 GF, 22 GA, 11 GP, +20",
            "San Jose 6-4-1, 32 GF, 36 GA, 11 GP",
            "Boston 2.00 GA/GP lowest of the 12 clubs in this board's fixtures"],
  "sources": [NHL_SRC, SCORE["2026-10-24"]],
 },
 {
  "sid": "nhl-2026020171", "market": "Puck Line +1.5", "selection": "New York Rangers",
  "match": "New York Rangers at Ottawa Senators", "start_utc": "2026-10-24T23:00:00Z",
  "text": "Alexis Lafreniere's Rangers are 7-4-1 with 37 goals for and 29 against in twelve games, a 3.08 scoring rate, and that output makes a single-goal finish the likeliest way this ends in Ottawa. The Senators are 7-4-0 but have been outscored 30-29 across eleven. Lafreniere has seven goals, Adam Fox ten assists, and Ottawa concede 2.73 per game. New York +1.5 is the play.",
  "facts": ["NY Rangers 7-4-1, 37 GF, 29 GA in 12 GP = 3.08 per game, 2.42 conceded",
            "Ottawa 7-4-0, 29 GF, 30 GA in 11 GP = 2.64 scored, 2.73 conceded",
            "Lafreniere 7 goals, Fox 10 assists", "Line +1.5"],
  "sources": [NHL_SRC, SCORE["2026-10-24"]],
 },
 {
  "sid": "nhl-2026020168", "market": "Match Total 6.5", "selection": "Under 6.5",
  "match": "Anaheim Ducks at Philadelphia Flyers", "start_utc": "2026-10-24T17:00:00Z",
  "text": "Philadelphia's scoring is the anchor for this under: 20 goals in twelve games, 1.67 per match, the lowest rate of any club on this board. Anaheim have scored 27 and conceded 33 in ten, so their games have averaged 6.00 goals combined. Put the two profiles together and the Flyers' low-event matches pull the expected total down. Under 6.5 goals at Xfinity Mobile Arena is the selection.",
  "facts": ["Philadelphia 20 GF in 12 GP = 1.67 per game",
            "Anaheim 27 GF, 33 GA in 10 GP = 6.00 combined per game",
            "Philadelphia have conceded 36 in 12", "Line 6.5 goals"],
  "sources": [NHL_SRC, SCORE["2026-10-24"]],
 },
 {
  "sid": "nhl-2026020171", "market": "Match Total 6.5", "selection": "Under 6.5",
  "match": "New York Rangers at Ottawa Senators", "start_utc": "2026-10-24T23:00:00Z",
  "text": "These two clubs have played 23 games between them and their goals for and against add up to 125, an average of 5.43 per fixture. New York have scored 37 and conceded 29 in twelve, Ottawa 29 and 30 in eleven. Neither side scores more than 3.08 per game, and both concede fewer than 2.73. On those rates the 6.5 line leaves little room, so under 6.5 is the play.",
  "facts": ["125 goals in 23 combined games = 5.43 per game",
            "NY Rangers 37 GF / 29 GA in 12 = 3.08 scored, 2.42 conceded",
            "Ottawa 29 GF / 30 GA in 11 = 2.64 scored, 2.73 conceded", "Line 6.5 goals"],
  "sources": [NHL_SRC, SCORE["2026-10-24"]],
 },
]

FLAGS = [
 ("F-01", "Golf", "OLBG's Golf hub returned \"No tips found.\" at capture time, so no Golf event existed to list. No official golf fixture was captured either. Golf therefore publishes zero rows on this desk.", "https://www.olbg.com/betting-tips/Golf/5"),
 ("F-02", "Rugby League", "OLBG lists only 2027 outright markets (State of Origin, Super League Grand Final, NRL Grand Final) for this sport. No match fixture was listed, so no match row or match price exists.", "https://www.olbg.com/betting-tips/Rugby_League/10"),
 ("F-03", "Rugby Union", "The URC table page returns its standings client-side and rendered no numeric columns in this environment, so points-for and points-against inputs are absent. All URC rows are published unlined rather than filled with estimates.", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
 ("F-04", "Baseball", "Only the American League East block of the MLB standings rendered before the capture window closed. Milwaukee's season totals were not captured, so World Series Game 1 is published unlined.", "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason"),
 ("F-05", "Ice Hockey", "The NHL club-statistics capture began mid-record for Nashville and did not include Winnipeg. Both clubs' goal totals are absent, so any fixture needing them is excluded rather than estimated.", NHL_SRC),
 ("F-06", "12 sports", "Twelve sports have OLBG events but no official numeric input was captured for them in this window. Their prices are consensus-derived only and are labelled that way on every row; no narrative is written for them.", "https://www.olbg.com/betting-tips"),
 ("F-07", "All sports", "OLBG renders no price on the hub and no price on the event page (checked on event_id 32335, where the win price field is blank). No OLBG price is recorded anywhere in this dataset, and every price here is originated independently.", "https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Jonny_Clayton_vs_Niko_Springer/15?event_id=32335"),
 ("F-08", "Darts, Baseball", "Two high-confidence selections (Jonny Clayton, Milwaukee Brewers) have no official numeric fact base captured. Their selection and confidence are published, but the narrative is withheld rather than written from unverified material.", "https://www.olbg.com/betting-tips/Darts/15"),
 ("F-09", "All sports", "OLBG sport hubs are paginated behind \"Load More Tips\" and \"Show Expired Events\". Only the first rendered page of each hub was captured, so the 125-row inventory is what OLBG displayed above the fold, not a guarantee of the complete slate.", "https://www.olbg.com/betting-tips"),
 ("F-10", "All sports", "OLBG's displayed start times do not reconcile to UTC. The NHL row shows \"Today 20:07\" for a game the NHL feed puts at 2026-10-24T00:00:00Z (20:00 ET). Displayed strings are stored verbatim and never used as the authoritative kick-off.", SCORE["2026-10-23"]),
 ("F-11", "All sports", "No official injury or team-news report was captured for any fixture. Injury sentences are therefore omitted from every prediction rather than inferred.", NHL_SRC),
 ("F-12", "All sports", "The target of five written predictions per sport is not met. Six predictions exist, all Ice Hockey, because that is the only sport for which official numeric inputs were captured. This is a coverage gap, not a completed target.", NHL_SRC),
 ("F-13", "Tennis", "The ATP order-of-play route tried returned HTTP 404, so no ATP fixture or ranking input was captured. All nine Tennis rows remain OLBG-listed only.", "https://www.atptour.com/en/scores/current/vienna/336/order-of-play"),
 ("F-14", "Basketball", "The NBA scoreboard endpoint returned HTTP 500 and no EuroLeague numeric page was captured. All fourteen Basketball rows remain OLBG-listed only.", "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"),
 ("F-15", "Darts", "The PDC tournament route returned a cookie-consent shell with no match data. The twelve Darts fixtures are OLBG-listed only and were not confirmed against the governing body.", "https://www.pdc.tv/tournaments/machineseeker-european-championship"),
 ("F-16", "Snooker", "The WST matches page rendered completed Round 1 results only; the two quarter-finals OLBG lists were not visible in the captured window. They remain unconfirmed against WST.", "https://www.wst.tv/matches/"),
 ("F-17", "Repo", "COORDINATION.md still contains three unresolved merge-conflict blocks (six marker lines at 3216/3307, 3437/3549 and 3609/3628). This desk leaves them untouched because they belong to other sessions' records, and flags them for the integration owner.", "https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md"),
]


def main():
    out = []
    for p in PREDICTIONS:
        words = len(re.findall(r"[A-Za-z0-9'\-]+", p["text"]))
        assert words >= 30, (p["sid"], words)
        assert "model" not in p["text"].lower(), p["sid"]
        assert "verified" not in p["text"].lower(), p["sid"]
        out.append({**p, "words": words})
    openings = [p["text"].split()[0] for p in out]
    assert len(set(openings)) == len(openings), openings
    json.dump({"generated_utc": "2026-10-23T16:40:00Z", "predictions": out},
              open(os.path.join(ROOT, "data/olbgdesk/predictions.json"), "w"), indent=1)
    json.dump({"generated_utc": "2026-10-23T16:40:00Z",
               "flags": [{"id": i, "sport": s, "finding": f, "source": u} for i, s, f, u in FLAGS]},
              open(os.path.join(ROOT, "data/olbgdesk/flagged.json"), "w"), indent=1)
    print(f"{len(out)} predictions, words {min(p['words'] for p in out)}-{max(p['words'] for p in out)}, {len(FLAGS)} flags")


if __name__ == "__main__":
    main()
