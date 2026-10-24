#!/usr/bin/env python3
"""Written predictions for the /clarity/ desk.

Every sentence below uses only facts captured in data/clarity/fixtures.json, and each entry
names the market and the selection in plain words. The words "model" and "verified" (and their
derivatives) are banned from the published text; a check in clarity_verify.py enforces that.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clarity"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)

# fixture_id -> (headline, prose). The prose always states the selection explicitly.
TEXTS = {
    "nhl-car-stl": (
        "St. Louis +1.5 on the puck line holds the safest shape of the night",
        "Back St. Louis Blues +1.5 on the puck line. The Blues are 5-4-1 and have taken points in all "
        "four home games, scoring 15 and conceding nine at Enterprise Center, with Joel Hofer already on "
        "four wins. Carolina arrive as the league's best side at 8-2-2 with 47 goals, but six of their wins "
        "came on the road and their 34 goals in eight away games still leave room for a one-goal finish."),
    "nhl-tbl-uta": (
        "Tampa Bay +1.5 covers the travel and the back-half of a road trip",
        "Take Tampa Bay Lightning +1.5 on the puck line. The Lightning are 7-3-0 with 34 goals for and 29 "
        "against, and they have lost only once by more than one goal all season. Utah are 7-4-0 at home-ice "
        "strength, 18 goals scored and 14 conceded in four games in Salt Lake City, but Lightning goaltending "
        "and a 16-goal road total keep this inside one strike of the puck line."),
    "nhl-tor-edm": (
        "Over 6.5 goals is the play when McDavid and Matthews share a rink",
        "Take Over 6.5 goals in Toronto at Edmonton. Edmonton have scored 47 goals in ten games and are 5-0-0 "
        "on the road with 27 scored, while Toronto have 43 in twelve and have taken points in three straight. "
        "Connor McDavid has 23 assists, Leon Draisaitl ten goals and Auston Matthews eight goals with ten "
        "assists, and the Oilers have conceded 32, so both nets have been busy."),
    "nhl-det-cgy": (
        "Calgary +1.5 is the value against a Red Wings side that cannot separate",
        "Back Calgary Flames +1.5. Detroit are 4-3-3 and have won only one road game, scoring eight and "
        "conceding seven in three, while Alex DeBrincat's six goals and six assists are carrying a thin "
        "attack. Calgary are 3-6-0 with just 19 goals, but they are 2-3-0 at the Saddledome and their "
        "last two results were wins, so a one-goal game is the most likely shape."),
    "nhl-nsh-pit": (
        "Nashville +1.5 fits a Penguins team that leaks goals at home",
        "Back Nashville Predators +1.5 on the puck line. Pittsburgh are 4-6-1, have conceded 38 goals in "
        "eleven games and only once in their last six home games have they won by two or more. Nashville "
        "are 3-3-3 with 23 goals against 30, Juuse Saros has three wins and Ryan O'Reilly four goals, and "
        "their four road games have produced 11 goals for and 16 against, all one-goal territory."),
    "nhl-buf-wsh": (
        "Washington's home record should be too much for Buffalo",
        "Back Washington Capitals on the money line. Washington are 5-4-0 with 30 goals for and 29 against, "
        "and at Capital One Arena they have won four of six while scoring 22 and conceding 20. Buffalo are "
        "4-4-2 with 28 goals against 37, they have only two regulation wins in ten games, and their road "
        "record reads 1-0-2 with 14 scored and 18 conceded."),
    "mlb-tb-mil-g2": (
        "Milwaukee's home record and Henderson's 0.84 WHIP settle Game 2",
        "Back Milwaukee Brewers on the money line in World Series Game 2. The Brewers finished 103-59 with "
        "832 runs scored and 618 allowed, and were 55-26 at American Family Field. Logan Henderson starts "
        "with an 11-3 record, a 2.47 ERA, 110 strikeouts in 98.1 innings and a 0.84 WHIP, while Drew "
        "Rasmussen counters at 2.67 with 174 strikeouts in 172 innings after Milwaukee won Game 1 3-2."),
    "nhl-vgk-cbj": (
        "Vegas have the depth to see off a Columbus side short on goals",
        "Back Vegas Golden Knights on the money line. Vegas are 8-4-0 with 46 goals for and 36 against, Mark "
        "Stone has eight goals and Jack Eichel 13 assists, and only two of their four defeats came by more "
        "than a goal. Columbus are 3-5-0 and have scored just 20 goals in eight games, with 16 scored and 22 "
        "conceded across six home dates, so the road favourite holds the cleaner route to the result."),
    "golf-genesis-r4": (
        "Katsuragawa's 63 gives him the outright lead to defend on Sunday",
        "Back Yuto Katsuragawa to win the Genesis Championship outright. He leads at 13 under after rounds of "
        "69, 68 and a third-round 63, three shots clear of Casey Jarvis on 11 under and four ahead of Kim Si "
        "Woo, Antoine Rozner and Sanghun Shin. He is 27th in the Race to Dubai standings and the final round "
        "closes on the Jack Nicklaus Golf Club Korea layout where he made seven birdies on Saturday."),
    "grey-scurry-final": (
        "Shadow Storm can join the four-timer club in the Scurry Gold Cup",
        "Back Shadow Storm to win the Arena Racing Company Scurry Gold Cup final at Dunstall Park. Richard "
        "Rees' dog is the reigning GBGB Sprinter of the Year, holds the track record and clocked 15.66 in his "
        "semi-final, the fastest qualifying run over the 270 metres. He is chasing a second straight Scurry "
        "and would be only the fourth greyhound to win back-to-back renewals of a £12,500 Category One prize."),
    "f1-usgp-race": (
        "Leclerc's practice double makes him the value in Austin",
        "Back Charles Leclerc to win the United States Grand Prix. He topped both Friday sessions, setting "
        "1:35.291 in the second, with Kimi Antonelli 0.042 seconds back, Max Verstappen 0.189 and Lewis "
        "Hamilton 0.615. Leclerc sits fifth in the championship on 215 points against Antonelli's 340, so he "
        "has nothing to protect, and the 56-lap race at Circuit of The Americas rewards the car with the "
        "cleanest single-lap pace shown so far."),
    "grey-oaks-final": (
        "Fahrenheit Jess has the clock and the kennel behind her in the Oaks",
        "Back Fahrenheit Jess to win the Premier Greyhound Racing Oaks final at Dunstall Park. Graham "
        "Holland's Irish raider made all in her semi-final in 27.87, the fastest of the three qualifiers, "
        "and her trainer also saddles Ballydoyle Tina, so the kennel knows the track shape. Signet Nayla won "
        "her semi in 28.35 and Slingshot Poppy in 27.90, which leaves Holland's leading bitch with a clear "
        "early-pace edge over the 480 metres for the £20,000 prize."),
    "darts-lit-asp": (
        "Under 17.5 legs reflects Littler's 105 average and a short-format evening",
        "Take Under 17.5 legs in Luke Littler against Nathan Aspinall. Littler opened his European "
        "Championship with a 6-3 win over William O'Connor at a 105.05 average, the best of the tournament to "
        "that point, and Aspinall beat Cristo Reyes by the same 6-3 margin. Round Two is best of 19 legs in "
        "Saturday's 19:00 to 23:00 session in Dortmund, and the world number one's scoring rate points to a "
        "10-6 or 10-7 finish rather than a decider."),
    "vb-per-pra": (
        "Perugia's title pedigree should hold against newly promoted Prata",
        "Back Sir Susa Scai Perugia to beat Tinet Prata di Pordenone. Perugia are the reigning Italian "
        "champions and opened the campaign by beating Cuneo, while Prata are newly promoted and marked their "
        "SuperLega debut with a 3-1 win over Vero Volley Monza. The match is at PalaBarton on Sunday at "
        "18:00, and the promoted side's first away test against the champions is the toughest fixture on "
        "their early calendar."),
    "cri-pak-eng-odi4": (
        "Pakistan's 2-0 record against a winless England makes them the call in Lahore",
        "Back Pakistan to win the fourth ODI at Gaddafi Stadium. Pakistan have beaten Sri Lanka by 37 runs "
        "and England by 87 in Rawalpindi, with Arafat Minhas taking five wickets and making a half-century in "
        "the second of those. England have lost all three matches, including a 430 chase conceded to Sri "
        "Lanka after Harry Brook's 202, the fastest double century in ODI history, and the venue shifts to "
        "Lahore on 25 October."),
    "nba-sas-dal": (
        "Dallas have the only win between these two and the healthier baseline",
        "Back Dallas Mavericks on the money line. Dallas are 1-1 and San Antonio are 0-2, with both Spurs "
        "defeats coming at home, and neither franchise had submitted an injury report at the 1:00 PM ET "
        "filing, so no absence can be claimed for either side. The game tips at 20:00 ET at American Airlines "
        "Center, and Dallas have already taken a road win while San Antonio have yet to win anywhere."),
    "ten-basel-djo-hum": (
        "Djokovic's 2026 title and 19-8 record outrank Humbert's left-handed threat",
        "Back Novak Djokovic to beat Ugo Humbert in Basel. Djokovic is 19-8 in 2026, won his 102nd tour title "
        "in Beijing this month and is 11th in the Live Race to Turin, and he returns to the Swiss Indoors for "
        "the first time since 2011, having won the event in 2009. Humbert is a former Top-20 left-hander, but "
        "the draw also offers Djokovic a semi-final against top seed Ben Shelton."),
    "ten-vienna-alc-kha": (
        "Alcaraz answers the Shanghai defeat against a familiar top-10 opponent",
        "Back Carlos Alcaraz to beat Karen Khachanov in Vienna. Alcaraz is No. 3 in the ATP Rankings and is "
        "chasing a fourth tour-level title of 2026, though he arrives after a third-round exit to Zizou Bergs "
        "in Shanghai. Khachanov is a former Top-10 player and a recent US Open semi-finalist, but Alcaraz "
        "reached the semi-finals on his only previous Vienna appearance as an 18-year-old in 2021."),
    "vb-tre-cis": (
        "Under 4.5 sets fits two Round 1 winners meeting at the BTS Arena",
        "Take Under 4.5 sets when Itas Trentino host Cisterna Volley. Both sides won their opener, Trentino "
        "at Modena and Cisterna 3-1 against Allianz Milano, and Trentino now have all fourteen players "
        "available including Theo Faure, the best opposite at the 2026 European Championship. The clubs have "
        "met 56 times in official competition, and the 17:00 Sunday start at the BTS Arena is Trentino's "
        "first home match in 177 days."),
    "vb-gie-ber": (
        "Berlin's title pedigree points to a four-set finish in Hildesheim",
        "Take Under 4.5 sets in Helios GRIZZLYS Giesen against BERLIN RECYCLING Volleys. Berlin are the "
        "reigning Bundesliga champions and the record champions, while Giesen reached a first national final "
        "in club history at their own Ligacup in October in front of 2,040 spectators. The 19:30 Saturday "
        "start at the Sparkassen-Arena is Giesen's first home league match of the campaign against the "
        "division's benchmark side."),
    "nba-mia-cha": (
        "Charlotte's depth survives four absences against a 0-2 Miami",
        "Back Charlotte Hornets on the money line. Charlotte are 1-1 while Miami are 0-2, and the official "
        "report lists four Hornets out: Boswell after right knee surgery, Knueppel with a left hamstring "
        "strain, White with a left calf strain and Williams with a right hamstring strain. Miami list only "
        "Larsson as probable with a left finger sprain, but a 0-2 start and a road trip to Spectrum Center "
        "make the home side the percentage call."),
    "cri-nz-ind-t20i3": (
        "India's two four-wicket chases make them the call in Wellington",
        "Back India to win the third T20I at Hnry Stadium. India have chased successfully twice at Hagley "
        "Oval, winning both by four wickets, after New Zealand made 225/4 in the opener with Finn Allen "
        "hitting 45 from 24 balls. Nitish Kumar Reddy's 26 not out from 13 balls sealed the second game, and "
        "Ishan Kishan will again be missing with a low-grade right adductor strain for the 27 October "
        "fixture."),
    "cri-bol-tit": (
        "Six straight wins make the Titans the pick in Paarl",
        "Back Momentum Multiply Titans to beat Goldrush Boland. The Titans have extended an unbeaten run to "
        "six matches, and Chad Laycock's 6/26 against them was not enough to stop a 21-run defeat. Boland beat "
        "Kaneez Tuskers by 63 runs after posting 187 with Lehan Botha making 54 and Gavin Kaplan 38, but they "
        "bowled Tuskers out for 124 and now meet the pool's form side at Boland Park."),
    "nba-gsw-phx": (
        "Phoenix's frontcourt absences are less costly than Golden State's 0-2 start",
        "Back Phoenix Suns on the money line. Phoenix are 0-1 and Golden State are 0-2 with one road defeat, "
        "while the Suns' report lists Mark Williams out after left shoulder surgery, Oghodaro doubtful with a "
        "right oblique strain and Kennard questionable with left knee tendinopathy. Golden State had not "
        "submitted a report at the 1:00 PM ET filing, so the Warriors' rotation is unknown heading into a "
        "22:00 ET tip at Footprint Center."),
    "cri-tus-cob": (
        "Cobras +12.5 covers a Tuskers batting line that collapsed for 124",
        "Back YesPlay Cobras -12.5 on the run handicap, which needs them to win by 13 runs or more. Tuskers "
        "are 1-3 and were bowled out for 124 chasing 187 against Boland, losing Jack Lees and Ludwig Kaestner "
        "for ducks. Cobras chased down 188 at Newlands with one ball remaining to beat that same Boland side, "
        "and the 13:00 start at Pietermaritzburg Oval favours the side that has already closed a game out."),
    "nba-nop-den": (
        "Denver's Ball Arena edge outweighs three rotation absences",
        "Back Denver Nuggets on the money line. Denver are 0-1 and New Orleans are 0-2, and the Nuggets' "
        "report lists Cameron Johnson out with a right ankle sprain, Spencer Jones out on bilateral hamstring "
        "injury management and Julian Strawther out with a left knee sprain, with Alpha Diallo questionable "
        "because of a right wrist sprain. New Orleans had not filed at the 1:00 PM ET deadline, so Denver's "
        "known absences are the only ones that can be weighed."),
    "top14-lar-ubb": (
        "Bordeaux's 215 points make them the away side to back in La Rochelle",
        "Back Union Bordeaux-Begles to win at Stade Marcel-Deflandre. Bordeaux are third on 19 points with 215 "
        "points scored and 151 conceded, and they won at Clermont in round six before beating Lyon at home. La "
        "Rochelle are fourth on 18 points with a much tighter 144 for and 135 against, and they have won only "
        "twice in their last five, drawing with Racing 92 and at Pau, so the visitors' scoring output is the "
        "decisive difference."),
    "top14-tou-pau": (
        "Pau's five wins in six make them the form pick at Stade Mayol",
        "Back Section Paloise to win at Toulon. Pau are second on 22 points with 239 scored and 181 conceded, "
        "and their run reads win over Bayonne, draw at Lyon, win over La Rochelle, win at Vannes and win over "
        "Castres. Toulon are eleventh on 12 points with 130 scored and 130 conceded, and although they beat "
        "Racing 92 last time out, three draws in five games show a side that struggles to close matches."),
    "nba-hou-atl": (
        "Atlanta's 2-0 start meets a Houston side missing Adams and VanVleet",
        "Back Atlanta Hawks on the money line. Both teams are 2-0, but Houston list Steven Adams out on left "
        "ankle injury management, Fred VanVleet out on right knee injury management and Reed Sheppard "
        "questionable with a left knee contusion and bone bruise. Atlanta are without Mouhamed Gueye, who has "
        "a left foot fracture, and Henri Veesaar, who has a right ACL tear, and they play their first home "
        "game after two road wins."),
    "nhl-nyr-ott": (
        "Under 5.5 goals fits two teams whose road and home splits diverge",
        "Take Under 5.5 goals in Ottawa against the Rangers. New York have scored 37 and conceded 29 in twelve "
        "games, but on the road that becomes eight goals for and 19 against in six, a 1-4-1 record built on "
        "low-scoring games. Ottawa are 7-4-0 with 31 scored and 30 conceded, Tim Stutzle has seven goals and "
        "eight assists, and three of their last five have finished inside five goals."),
    "ten-almaty-final": (
        "Basilashvili +1.5 sets covers a final where Medvedev's edge is one break",
        "Back Nikoloz Basilashvili +1.5 on the set handicap, which pays if he wins a set or loses in three. "
        "Medvedev is the top seed with a Tour-leading 37 hard-court wins in 2026 and a 10-1 record at the "
        "Almaty Open, and he led Alexander Bublik 6-3 when the Kazakh retired in the semi-final. Basilashvili "
        "qualified, then beat Adrian Mannarino 6-3 6-1, is guaranteed a return to the Top 100 and is chasing "
        "a sixth tour title."),
    "nba-was-chi": (
        "Chicago's home floor and Washington's missing report shape the call",
        "Back Chicago Bulls on the money line. Chicago are 1-1 and Washington are 1-1, but the Wizards have "
        "not played a road game yet and had not submitted an injury report at the 1:00 PM ET filing. Chicago "
        "list Nic Claxton out with a left hamstring strain and Noa Essengue probable with a right head "
        "contusion, and the 20:00 ET tip at United Center is the Bulls' second home date of the campaign."),
    "nhl-sjs-bos": (
        "Under 6.5 goals is the shape at TD Garden",
        "Take Under 6.5 goals in Boston against San Jose. Boston are 8-2-1 with 42 goals for and only 22 "
        "against, and at TD Garden that split tightens to 21 scored and six conceded in five games, with "
        "Jeremy Swayman already on six wins. San Jose are 6-4-1 with 33 scored and 37 conceded and have only "
        "one regulation win in eleven, so the visitors' route to goals is narrow."),
    "golf-bermuda-r4": (
        "Smotherman's two-shot cushion is the shortest price left on the board",
        "Back Austin Smotherman to win the Butterfield Bermuda Championship outright. He leads at 16 under "
        "through ten holes of the third round after rounds of 65 and 66, with Chandler Blanchet one back at 15 "
        "under following a 62, and Chris Kirk, Ben Silverman and Seamus Power tied at 14 under. The published "
        "market has Smotherman at +240, the shortest of the leading group, ahead of Kirk at +650 and Power at "
        "+700."),
}


def main() -> int:
    fixtures = {f["id"]: f for f in json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]}
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    rows, skipped = [], []
    for p in picks["picks"]:
        if p["fixture_id"] not in TEXTS:
            skipped.append(p["fixture_id"])
            continue
        head, text = TEXTS[p["fixture_id"]]
        words = len(text.split())
        rows.append({
            "id": f"pred-{p['fixture_id']}", "pick_id": p["id"], "fixture_id": p["fixture_id"],
            "sport": p["sport"], "competition": p["competition"], "home": p["home"], "away": p["away"],
            "start_utc": p["start_utc"], "selection": p["selection"], "market": p["market"],
            "confidence": p["confidence"], "probability": p["probability"],
            "american_display": p["american_display"], "headline": head, "text": text, "words": words,
            "official_url": p["official_url"], "olbg_url": p["olbg_url"],
            "facts": [{"claim": f["claim"], "value": f["value"], "source_url": f["source_url"]}
                      for f in fixtures[p["fixture_id"]]["facts"]],
        })
    # Per-sport ceiling of five write-ups, strongest first (probability within confidence tier).
    order = {"high": 3, "medium": 2, "low": 1}
    rows.sort(key=lambda r: (-order[r["confidence"]], -r["probability"]))
    kept, count, high_count = [], {}, {}
    for r in rows:
        n = count.get(r["sport"], 0)
        # Every high-confidence pick gets prose. Medium picks are capped so no sport exceeds five
        # write-ups unless its own high picks already exceed that.
        if r["confidence"] == "high":
            high_count[r["sport"]] = high_count.get(r["sport"], 0) + 1
        if n >= 5 and r["confidence"] != "high":
            continue
        count[r["sport"]] = n + 1
        kept.append(r)
    kept.sort(key=lambda r: (r["start_utc"] or "9999", r["sport"]))
    out = {
        "generated_utc": picks["as_of_utc"], "count": len(kept),
        "by_sport": count,
        "min_words": min((r["words"] for r in kept), default=0),
        "shortfall_note": "Write-ups are published only where a high or medium selection cleared the "
                          "focus band with two or more sourced facts. Sports with no write-up are listed "
                          "on the Flagged for Review page.",
        "predictions": kept,
    }
    (DATA / "predictions.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    bad = [r["id"] for r in kept if r["words"] < 30 or BANNED.search(r["text"])]
    print(f"clarity_predictions: {len(kept)} write-ups across {len(count)} sports "
          f"(min {out['min_words']} words), {len(bad)} failing a rule, {len(skipped)} picks without prose")
    if bad:
        print("FAIL:", bad)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
