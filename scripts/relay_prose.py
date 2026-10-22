#!/usr/bin/env python3
"""Hand-authored predictions for the /relay/ layer (session arena/103d996c-olbg2).

Each text is written by the agent against data/relay/band.json and quotes only
numbers that an official capture returned (official standings tables, the NHL
team summary, the URC table with form strings and Round 3 scores, EHF group
tables, EuroLeague standings with home/away splits, official team-leader
values from the NHL score feed). Word counts and uniqueness are checked by
tests/test_relay_103d996c.py.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "relay")

TEXTS = {
 "el-E2026-68": (
  "Both sides reach Zalgirio Arena on identical 2-4 EuroLeague records, yet the "
  "defensive numbers separate them: LDLC ASVEL Villeurbanne have conceded 572 "
  "points in six rounds, the second-worst tally in the official standings, while "
  "Zalgiris Kaunas have given up 517. With ASVEL 1-2 on the road, we back Zalgiris "
  "on the -1.5 handicap to win outright at a fair -237."),
 "el-E2026-69": (
  "Paris Basketball sit 18th after a 1-5 start, their only win coming at the "
  "Adidas Arena, whereas Valencia Basket are fifth at 4-2 and still unbeaten away "
  "from home at 2-0 with 583 points scored. Even allowing Paris home court, our "
  "rating makes this near level, so Valencia plus 4.5 points at fair -238 is the "
  "selection we are taking."),
 "el-E2026-70": (
  "A genuine heavyweight clash: Olympiacos Piraeus (5-1, third) host Fenerbahce "
  "Tarfin Istanbul (5-1, second), but the visitors are 0-1 away while Olympiacos "
  "are 1-0 at the Sunel Arena and outscoring opponents 564-524. Our model calls "
  "the hosts slight underdogs, which makes Olympiacos +1.5 at fair -244 the value "
  "play in this one."),
 "urc-292608": (
  "Cardiff Rugby host the Hollywoodbets Sharks at Cardiff Arms Park with both "
  "clubs on WWL form through three United Rugby Championship rounds. The Sharks "
  "were beaten 39-22 at the Stormers last time out and have conceded 83 points "
  "already; Cardiff's defence has allowed 71. We take Cardiff plus 2.5 on the "
  "handicap at a fair -248."),
 "urc-292609": (
  "Bottom-of-the-table Zebre Parma travel to the Dexcom Stadium still searching "
  "for a first win, 0-3 with LLL form and 116 points conceded in three rounds, "
  "including a 29-12 home loss to Edinburgh. Connacht Rugby, despite a LWL start, "
  "are the far stronger side on points for and against, so Connacht -2.5 at fair "
  "-244 is our handicap selection."),
 "urc-292610": (
  "Edinburgh sit top of the URC on a perfect 3-0, 14 points and WWW form after a "
  "29-12 win at Zebre, conceding just 54 points. The 10bet Lions arrive off a "
  "brutal 57-15 defeat at the Bulls with 102 points against. At the Hive Stadium "
  "we back Edinburgh to cover -4.5 at a fair price of -244."),
 "nhl-2026020170": (
  "Boston Bruins (7-2-1, 36 goals for) welcome the San Jose Sharks to TD Garden, "
  "where Jeremy Swayman already has six wins and David Pastrnak 12 points. San "
  "Jose lean on Macklin Celebrini's 5 goals and 9 assists but have managed only "
  "26 goals in ten games. Our Poisson model projects about six goals, so Over 4.5 "
  "at fair -250 is the play."),
 "nhl-2026020172": (
  "Nashville's 3-2-3 start is built on defence: just 22 goals against in eight "
  "games with Juuse Saros on three wins, while Roman Josi has eight assists. The "
  "Penguins (3-6-1) counter with Evgeni Malkin's five goals and Erik Karlsson's "
  "ten assists. With the model's total near 6.3, we take Under 7.5 at PPG Paints "
  "Arena at fair -239."),
 "nhl-2026020176": (
  "Connor McDavid has 20 assists in nine games and Leon Draisaitl eight goals as "
  "the 7-1-1 Edmonton Oilers host Toronto at Rogers Place. The Maple Leafs "
  "(5-4-2) answer with Auston Matthews' 8 goals and 10 assists. High quality does "
  "not mean high scoring: our projected total is 7.16, "
  "so Under 8.5 at fair -243 is the selection."),
 "urc-292612": (
  "The DHL Stormers, fourth on 11 points, smashed the Sharks 39-22 at this venue "
  "in Round 3 and have conceded only 54 points all season. Scarlets (12th, LLW "
  "before last week's 27-26 win over Benetton) have shipped 85. A 10:00 local "
  "kickoff in Cape Town suits the Stormers, and we back them to cover -3.5 at "
  "fair -247."),
 "urc-292614": (
  "The big Irish interpro at the Aviva Stadium: Leinster, unbeaten at home and "
  "fresh from a 29-5 dismantling of Cardiff, have the tighter defence (58 points "
  "against in three rounds). Munster drew 26-26 at Ulster and sit ninth on form "
  "LWD with 74 conceded. Our ratings make Leinster clear home favourites, and we "
  "back them on the moneyline at fair -240."),
 "urc-292615": (
  "Ospreys and Dragons RFC meet at St Helen's having played out a 38-31 Ospreys "
  "win at Rodney Parade in Round 3. Dragons (8th, DWL) have scored 88 but leak "
  "points, while the Ospreys' 81 points for keeps them in this despite a 1-0-2 "
  "record. We take Ospreys plus 4.5 on the handicap at a fair -237."),
 "nhl-2026020177": (
  "Tampa Bay (7-2-0) roll into the Delta Center on the second night of a "
  "back-to-back after Friday's game in Denver, with Andrei Vasilevskiy on five "
  "wins and Brandon Hagel and Nikita Kucherov driving a 31-goal offence. Utah "
  "(7-3-0) score freely but our model rates this close to pick'em, so Lightning "
  "+1.5 at fair -235 is the value we publish."),
 "nhl-2026020178": (
  "The Calgary Flames' struggles are defensive: 37 goals against in eight games, "
  "a 2-6-0 record and Dustin Wolf still on one win, with Morgan Frost leading the "
  "offence on three goals. The Detroit Red Wings counter through Alex DeBrincat's "
  "6 goals and 5 assists. Our projected total of 5.9 clears four and a half "
  "comfortably, so Over 4.5 at the Saddledome at fair -236 is the selection."),
 "ehfcl-202711020101004": (
  "Unbeaten One Veszprem HC top Group A with 185 goals for and 146 against over "
  "five matches, while FC Porto (1-1-3) have played in games averaging 66.2 "
  "goals. Both clubs' match totals sit well below the 71.5 line, so in Porto's "
  "home arena we take Under 71.5 goals at a fair -248."),
 "ehfcl-202711020101022": (
  "HC Vardar 1961 have dropped four of five in Group B but stay within touching "
  "distance at 154-158 on goals, and they host MT Melsungen, whose 2-0-2 record "
  "comes with a modest 110 goals for in four matches. Home court matters in "
  "Skopje, and we back Vardar plus 3.5 at fair -240."),
 "ehfcl-202711020101036": (
  "Group C's winless RK Celje Pivovarna Lasko (0-0-5) have still put 150 goals on "
  "the board, and their matches have averaged 67.6. HC Zagreb (2-0-3) average "
  "60.8 in games that have featured 146 goals for and 158 against. Our projected "
  "total is 64.2, so Under 68.5 at fair -246 is the handicapped total we like."),
 "ehfcl-202711020101065": (
  "SC Magdeburg are four wins from four in Group F, outscoring opponents 141-108, "
  "the best defensive record in the group tables we captured. Swiss side HC "
  "Kriens-Luzern arrive at 2-0-3 with 161 conceded. Magdeburg are clear "
  "favourites in our rating and we take them at -1.5 on the handicap, fair -245."),
 "ehfcl-202711020101067": (
  "Industria Kielce (3-0-2) host a Kolstad Handball side that is 0-0-4 with just "
  "111 goals scored in Group F. Kielce's own games have averaged 61.6 goals and "
  "Kolstad's 63.5, both below our 62.3 projection's neighbours. We take Under "
  "66.5 goals at fair -242 in this mismatch."),
 "ehfcl-202711020101040": (
  "Sporting Clube de Portugal lead Group D unbeaten in regulation (3-1-0) with "
  "only 125 goals against, the group's best. GOG sit second at 3-0-1 but concede "
  "more than they would like (139). Travelling to Denmark is never easy, so we "
  "take Sporting plus 2.5 on the handicap at a fair -236."),
}


def main():
    band = json.load(open(os.path.join(DATA, "band.json"), encoding="utf-8"))
    picks = []
    for s in band["selections"]:
        text = TEXTS[s["match_id"]].strip()
        assert len(text.split()) >= 30, (s["match_id"], len(text.split()))
        picks.append({
            "id": "pred-" + s["match_id"],
            "match_id": s["match_id"],
            "fixture": s["fixture"],
            "sport": s["sport"],
            "sport_name": s["sport_name"],
            "date": s["date"],
            "competition": s.get("competition", ""),
            "time_note": s.get("time_note", ""),
            "market": s["market"],
            "selection": s["selection"],
            "probability": s["p"],
            "fair_decimal": s["fair_decimal"],
            "fair_american": s["fair_american"],
            "confidence": "high",
            "text": text,
        })
    texts = [p["text"] for p in picks]
    assert len(set(texts)) == len(texts), "duplicate prediction text"
    doc = {
        "layer": "relay",
        "generated_by": "hand-authored against data/relay/band.json; word counts, "
                        "uniqueness and fact links validated by tests/test_relay_103d996c.py",
        "rule": "Every high-confidence selection carries a unique written prediction of at "
                "least 30 words naming the club or player, current form from an official "
                "standings table, a recent result, and the exact betting selection with its "
                "fair price.",
        "predictions": picks,
        "counts": {"predictions": len(picks),
                   "by_sport": {}},
    }
    for p in picks:
        doc["counts"]["by_sport"][p["sport_name"]] = \
            doc["counts"]["by_sport"].get(p["sport_name"], 0) + 1
    out = os.path.join(DATA, "predictions.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    print("relay predictions OK:", json.dumps(doc["counts"]))


if __name__ == "__main__":
    main()
