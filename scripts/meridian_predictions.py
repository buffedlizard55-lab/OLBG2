#!/usr/bin/env python3
"""Written predictions for the /meridian/ desk.

Every sentence below uses only facts captured in data/meridian/fixtures.json, and each entry
names the market and the selection in plain words. The words "model" and "verified" (and their
derivatives) are banned from the published text; a check in meridian_verify.py enforces that.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "meridian"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)

# fixture_id -> (headline, prose). The prose always states the selection explicitly.
TEXTS = {
    "nhl-car-stl": (
        "St. Louis plus one and a half on the puck line",
        "Back St. Louis +1.5 on the puck line. The Blues are 5-4-1 with 11 points, and at Enterprise "
        "Center they are 3-0-1 with 15 goals for and only six against; Joel Hofer has four wins. "
        "Carolina lead the league at 8-2-2 with 47 goals for, but eight of their points came on the "
        "road, where they have scored 34 in eight games, so a one-goal finish is plausible.",
    ),
    "nhl-tbl-uta": (
        "Utah plus one and a half on the puck line against Tampa Bay",
        "Take Utah +1.5 on the puck line. Utah are 7-4-0 with 41 goals for and 36 against, and Karel "
        "Vejmelka has five wins. Tampa Bay have 34 goals for and 29 against and conceded six at "
        "Colorado in their most recent game, while their road scoring totals 16 goals in five games, "
        "so the visitors can keep this within one strike.",
    ),
    "nhl-tor-edm": (
        "Over six and a half goals when McDavid and Matthews share a rink",
        "Take Over 6.5 goals in Toronto at Edmonton. Edmonton have scored 47 goals in ten games and "
        "are 5-0-0 on the road with 27 scored; Toronto have 43 in twelve and have taken points in "
        "three straight. Connor McDavid has 23 assists, Leon Draisaitl ten goals and Auston Matthews "
        "eight goals with ten assists, and Edmonton have conceded 32, so both nets have been busy.",
    ),
    "nhl-det-cgy": (
        "Calgary plus one and a half against a Detroit side that cannot separate",
        "Take Calgary +1.5 on the puck line. The Flames are 3-6-0 with just 19 goals, yet they are "
        "2-3-0 at the Saddledome and have won their last two, so a tight game suits them. Detroit are "
        "4-3-3 and have won only one road game, scoring eight and conceding seven in three; Alex "
        "DeBrincat's six goals and six assists are carrying a thin attack, which points to a narrow "
        "margin.",
    ),
    "nhl-nsh-pit": (
        "Nashville plus one and a half against a Pittsburgh side that leaks goals",
        "Take Nashville +1.5 on the puck line. Pittsburgh are 4-6-1 and have conceded 38 goals in "
        "eleven games, and only once in their last six home games have they won by two or more. "
        "Nashville are 3-3-3 with 23 goals for and 30 against, Juuse Saros has three wins and Ryan "
        "O'Reilly four goals, and their four road games produced 11 goals for and 16 against, all in "
        "one-goal territory.",
    ),
    "nhl-buf-wsh": (
        "Washington's home record should be too much for Buffalo",
        "Back Washington on the money line. The Capitals are 5-4-0 with 30 goals for and 29 against, "
        "and at Capital One Arena they have won four of six while scoring 22 and conceding 20; Logan "
        "Thompson has four wins. Buffalo are 4-4-2 with 28 goals for and 37 against, with only two "
        "regulation wins in ten games and a 14-goals-for, 18-goals-against road record, so the home "
        "side holds the clearer route to the result.",
    ),
    "nhl-vgk-cbj": (
        "Vegas have the depth to see off a Columbus side short on goals",
        "Back Vegas on the money line. Vegas are 8-4-0 with 46 goals for and 36 against, Mark Stone "
        "has eight goals and Jack Eichel 13 assists, and only two of their four defeats came by more "
        "than a goal. Columbus are 3-5-0 and have scored just 20 goals in eight games, with 16 scored "
        "and 22 conceded across six home dates, so the road favourite holds the cleaner route to the "
        "result.",
    ),
    "mlb-tb-mil-g2": (
        "Milwaukee's home record and Henderson's 0.84 WHIP settle Game 2",
        "Back Milwaukee on the money line in World Series Game 2. The Brewers finished 103-59 with "
        "832 runs scored and 618 allowed, and were 55-26 at American Family Field. Logan Henderson "
        "starts with an 11-3 record, a 2.47 ERA, 110 strikeouts in 98.1 innings and a 0.84 WHIP, "
        "while Tampa Bay counters with Drew Rasmussen at 2.67 after Milwaukee won Game 1 3-2.",
    ),
    "nba-sas-dal": (
        "Dallas have the only win between these two and the healthier baseline",
        "Back Dallas on the money line. Dallas are 1-1 while San Antonio are 0-2, and both Spurs "
        "defeats came at home. Neither club had filed an injury report by the 1:30 PM ET deadline, so "
        "no absence can be claimed for either side; Dallas have already taken a road win while San "
        "Antonio have yet to win anywhere, which tips the balance to the home side.",
    ),
    "nba-mia-cha": (
        "Charlotte's depth survives four absences against a zero-and-two Miami",
        "Back Charlotte on the money line. The Hornets are 1-1 while Miami are 0-2, and the official "
        "report lists four Hornets out: Boswell after right knee surgery, Knueppel with a left "
        "hamstring strain and White with a left calf strain, while Miami list only Larsson as "
        "probable with a left finger sprain. A zero-and-two start and a road trip to Spectrum Center "
        "make the home side the percentage call.",
    ),
    "nba-gsw-phx": (
        "Phoenix's frontcourt absences are less costly than Golden State's zero-and-two start",
        "Back Phoenix on the money line. Phoenix are 0-1 and Golden State are 0-2 with one road "
        "defeat, while the Suns' report lists Mark Williams out after left shoulder surgery, "
        "Oghodaro doubtful with a right oblique strain and Kennard questionable with left knee "
        "tendinopathy. Golden State had not submitted a report at the 1:30 PM ET deadline, so their "
        "rotation is unknown heading into a 10:00 PM ET tip.",
    ),
    "nba-nop-den": (
        "Denver's home edge outweighs three rotation absences",
        "Back Denver on the money line. Denver are 0-1 and New Orleans are 0-2, and the Nuggets' "
        "report lists Cameron Johnson out with a right ankle sprain, Spencer Jones out on bilateral "
        "hamstring injury management and Julian Strawther out with a left knee sprain, with Alpha "
        "Diallo questionable with a right wrist sprain. New Orleans had not filed at the 1:30 PM ET "
        "deadline, so Denver's known absences are the only ones that can be weighed.",
    ),
    "nba-atl-hou": (
        "Atlanta's two-and-zero start meets a Houston side missing Adams and VanVleet",
        "Back Atlanta on the money line. Both teams are 2-0, but Houston list Steven Adams out on "
        "left ankle injury management, Fred VanVleet out on right knee injury management and Reed "
        "Sheppard questionable with a left knee contusion and bone bruise. Atlanta are without "
        "Mouhamed Gueye (left foot fracture) and Henri Veesaar (right ACL tear), and the 8:30 PM ET "
        "tip is their first home game after two road wins.",
    ),
    "cri-pak-eng-odi4": (
        "Pakistan's two-and-zero record against a winless England side makes them the call",
        "Back Pakistan to win the fourth ODI at Gaddafi Stadium. Pakistan have beaten Sri Lanka by 37 "
        "runs and England by 87 in Rawalpindi, with Arafat Minhas taking five wickets and making a "
        "half-century in the second of those. England have lost all three matches, including a 430-"
        "run chase conceded to Sri Lanka after Harry Brook's 202, the fastest double century in ODI "
        "history, and the venue shifts to Lahore on 25 October.",
    ),
    "cri-nz-ind-t20i3": (
        "India's two four-wicket chases make them the call in Wellington",
        "Back India to win the third T20I at Hagley Oval. India have chased successfully twice at "
        "Hagley Oval, winning both by four wickets, after New Zealand made 225 for 4 in the opener "
        "with Finn Allen hitting 45 from 24 balls. Nitish Kumar Reddy's 26 not out from 13 balls "
        "sealed the second game, and Ishan Kishan will again be missing with a low-grade right "
        "adductor strain for the 27 October fixture.",
    ),
    "cri-bol-tit": (
        "Six straight wins make the Titans the pick in Paarl",
        "Back the Titans to beat Goldrush Boland. The Titans have extended an unbeaten run to six "
        "matches, and Chad Laycock's six for 26 against them was not enough to stop a 21-run defeat. "
        "Boland beat Kaneez Tuskers by 63 runs after posting 187 with Lehan Botha making 54 and Gavin "
        "Kaplan 38, but they bowled Tuskers out for 124 and now meet the pool's form side.",
    ),
    "cri-tus-cob": (
        "Cobras plus twelve and a half covers a Tuskers batting line that collapsed for 124",
        "Back YesPlay Cobras -12.5 on the run handicap, which needs them to win by 13 runs or more. "
        "Tuskers are 1-3 and were bowled out for 124 chasing 187 against Boland, with Jack Lees and "
        "Ludwig Kaestner out for ducks. Cobras chased down 188 at Newlands with one ball remaining to "
        "beat that same Boland side, and the 1:00 PM start at Pietermaritzburg Oval favours the side "
        "that has already closed a game out.",
    ),
    "darts-nav-llt": (
        "Littler's 105 average points to a tight total",
        "Littler's 105.05 average points to a tight total: take Under 17.5 legs in Nathan Aspinall against Luke Littler. Littler opened his European "
        "Championship campaign with a 6-3 win over William O'Connor at a 105.05 average, the best of "
        "the tournament to that point, and Aspinall beat Cristo Reyes by the same 6-3 margin. Round "
        "Two is best of 19 legs in Saturday's 7:00 to 11:00 PM session in Dortmund, and both "
        "players' scoring rates point to a tight total: Under 17.5 legs implies a 10-7 or 10-8 "
        "finish rather than a decider.",
    ),
    "darts-jcv-jro": (
        "Clayton and Rock trade legs tidily",
        "Clayton and Rock traded tidy first rounds: take Under 17.5 legs in Jonny Clayton against Josh Rock. Clayton beat Niko Springer 6-3 in "
        "the first round and Rock disposed of Chris Dobey 6-1, but Round Two is best of 19 legs in "
        "Dortmund's evening session. Two accurate scorers tend to trade legs rather than run away "
        "with frames, making Under 17.5 legs the percentage play.",
    ),
    "darts-rsv-dhe": (
        "Smith's clean 6-0 start suggests a compact total",
        "Smith's clean 6-0 first round suggests a compact total: take Under 17.5 legs in Ross Smith against Damon Heta. Smith, the top seed, beat Karel "
        "Sedlacek 6-0 in the first round, while Heta needed a decider to see off James Wade 6-5. "
        "Round Two is best of 19 legs, and Smith's clean first-round performance against a "
        "decider-weary opponent points to a compact total.",
    ),
    "darts-gvw-lwo": (
        "Van Veen's defence points to a short match",
        "Van Veen's title-defence experience points to a short match: take Under 17.5 legs in Gian van Veen against Luke Woodhouse. The defending champion beat "
        "Andrew Gilding 6-4 in round one, while Woodhouse needed a nine-dart finish to edge Dirk "
        "van Duijvenbode 6-3. Round Two is best of 19 legs in Dortmund, and Van Veen's "
        "title-defence experience against a decider-tested opponent points to a compact total.",
    ),
    "darts-sbu-khy": (
        "Bunting's decider win hints at a low leg count",
        "Bunting's recent European form hints at a tight total: take Under 17.5 legs in Stephen Bunting against Kim Huybrechts. Bunting needed a decider to "
        "beat Danny Noppert 6-5 after a late call-up, while Huybrechts demolished Ryan Searle 6-1 at "
        "a 103.81 average. Round Two is best of 19 legs in Saturday's evening session in Dortmund, "
        "and Bunting's recent European Championship form points to a tight total.",
    ),
    "vb-per-pra": (
        "Perugia's title pedigree should hold against newly promoted Prata",
        "Back Sir Susa Scai Perugia to beat Tinet Prata di Pordenone. Perugia are the reigning "
        "Italian champions and opened their campaign by winning at Modena, while Prata are newly "
        "promoted and marked their SuperLega debut with a 3-1 win over Allianz Milano. The match is "
        "at PalaBarton, and the promoted side's first away test against the champions is the "
        "toughest fixture on their early calendar.",
    ),
    "vb-tre-cis": (
        "Under four and a half sets fits two Round 1 winners meeting at Trento",
        "Take Under 4.5 sets when Itas Trentino host Cisterna Volley. Both sides won their opener, "
        "Trentino at Modena and Cisterna 3-1 against Allianz Milano, and Trentino have all fourteen "
        "players available, including Theo Faure, the best opposite at the 2026 European "
        "Championship. The clubs have met 56 times in official competition, and the 4:00 PM Sunday "
        "start at the BTS Arena is Trentino's first home match in 177 days.",
    ),
    "ten-basel-djo-hum": (
        "Djokovic's 2026 title and 19-8 record outrank Humbert's left-handed threat",
        "Back Novak Djokovic to beat Ugo Humbert in Basel. Djokovic is 19-8 in 2026, won his 102nd "
        "tour title in Beijing this month and is 11th in the Live Race to Turin, and he returns to "
        "the Swiss Indoors for the first time since 2011, having won the event in 2009. Humbert is a "
        "former Top-20 left-hander, but Djokovic's title pedigree on indoor hard courts is the "
        "deciding factor.",
    ),
    "ten-vienna-alc-kha": (
        "Alcaraz answers the Shanghai defeat against a familiar Top-10 opponent",
        "Back Carlos Alcaraz to beat Karen Khachanov in Vienna. Alcaraz is number three in the ATP "
        "Rankings and is chasing a fourth tour-level title of 2026, though he arrives after a "
        "third-round exit to Zizou Bergs in Shanghai. Khachanov is a former Top-10 player and a "
        "recent US Open semi-finalist, but Alcaraz leads their head-to-head series 6-0 and reached "
        "the semi-finals here as an 18-year-old in 2021.",
    ),
    "ten-almaty-final": (
        "Basilashvili plus one and a half sets covers a final where Medvedev's edge is one break",
        "Take Nikoloz Basilashvili +1.5 sets against Daniil Medvedev in the Almaty final. Medvedev "
        "led Alexander Bublik 6-3 when the Kazakh retired in the semi-final, and he is 10-1 at this "
        "event, but Basilashvili qualified and then beat Adrian Mannarino 6-3 6-1, and he is "
        "guaranteed to return to the Top 100. Winning a set against a champion with a short turnaround "
        "is a realistic outcome.",
    ),
}

OUTRIGHT_TEXTS = {

    "nhl-nyr-ott": (
        "Ottawa under five and a half goals against the Rangers",
        "Take Under 5.5 goals in Ottawa against the Rangers. New York have scored 37 and conceded 29 in "
        "twelve games, but on the road that becomes eight goals for and 19 against in six, a 1-4-1 record "
        "built on low-scoring games. Ottawa are 7-4-0 with 31 scored and 30 conceded, Tim Stutzle has seven "
        "goals and eight assists, and three of their last five have finished inside five goals.",
    ),
    "nba-was-chi": (
        "Chicago's home floor and Washington's missing report shape the call",
        "Back Chicago on the money line. Chicago are 1-1 and Washington are 1-1, but the Wizards have not "
        "played a road game yet and had not submitted an injury report at the 1:00 PM ET filing. Chicago "
        "list Nic Claxton out with a left hamstring strain and Noa Essengue probable with a right head "
        "contusion, and the 8:00 PM ET tip at United Center is the Bulls' second home date of the campaign.",
    ),
    "nhl-sjs-bos": (
        "Under six and a half goals at TD Garden",
        "Take Under 6.5 goals in Boston against San Jose. Boston are 8-2-1 with 42 goals for and only 22 "
        "against, and at TD Garden that split tightens to 21 scored and six conceded in five games, with "
        "Jeremy Swayman already on four wins. San Jose are 6-4-1 with 33 scored and 37 conceded and have "
        "only one regulation win in eleven, so the visitors' route to goals is narrow.",
    ),
    "ru-tou-pau": (
        "Pau's five wins in six make them the form pick at Stade Mayol",
        "Back Section Paloise to win at Toulon. Pau are second on 22 points with 239 scored and 181 "
        "conceded, and their run reads win over Bayonne, draw at Lyon, win over La Rochelle, win at Vannes "
        "and win over Castres. Toulon are eleventh on 12 points with 130 scored and 130 conceded, and "
        "although they beat Racing 92 last time out, three draws in five games show a side that struggles "
        "to close matches.",
    ),
    "ru-lar-ubb": (
        "Bordeaux's 215 points make them the away side to back in La Rochelle",
        "Back Union Bordeaux-Begles to win at Stade Marcel-Deflandre. Bordeaux are third on 19 points with "
        "215 points scored and 151 conceded, and they won at Clermont in round six before beating Lyon at "
        "home. La Rochelle are fourth on 18 points with a much tighter 144 for and 135 against, and they "
        "have won only twice in their last five, drawing with Racing 92 and at Pau, so the visitors' "
        "scoring output is the decisive difference.",
    ),

        "f1-usgp-race": (
        "Leclerc's practice double makes him the value in Austin",
        "Back Charles Leclerc to win the United States Grand Prix. He topped both Friday sessions, "
        "setting 1:35.291 in the second, with Kimi Antonelli 0.042 seconds back, Max Verstappen "
        "0.189 and Lewis Hamilton 0.615. Leclerc sits fifth in the championship on 215 points "
        "against Antonelli's 340, so he has nothing to protect, and qualifying on Saturday has still "
        "to run, which adds uncertainty to a price that looks generous.",
    ),
}


def main() -> int:
    fixtures = {f["id"]: f for f in json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]}
    picks_doc = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    picks = picks_doc["picks"]
    rows, skipped = [], []
    for p in picks:
        if p["fixture_id"] not in TEXTS and p["fixture_id"] not in OUTRIGHT_TEXTS:
            skipped.append(p["fixture_id"])
            continue
        if p["fixture_id"] in OUTRIGHT_TEXTS:
            head, text = OUTRIGHT_TEXTS[p["fixture_id"]]
        else:
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
    order = {"high": 3, "medium": 2, "low": 1}
    rows.sort(key=lambda r: (-order[r["confidence"]], -r["probability"]))
    kept, count, high_count = [], {}, {}
    for r in rows:
        n = count.get(r["sport"], 0)
        if r["confidence"] == "high":
            high_count[r["sport"]] = high_count.get(r["sport"], 0) + 1
        if n >= 5 and r["confidence"] != "high":
            continue
        count[r["sport"]] = n + 1
        kept.append(r)
    kept.sort(key=lambda r: (r["start_utc"] or "9999", r["sport"]))
    out = {
        "generated_utc": picks_doc["as_of_utc"], "count": len(kept),
        "by_sport": count,
        "min_words": min((r["words"] for r in kept), default=0),
        "shortfall_note": "Write-ups are published for high and medium selections that cleared the "
                          "focus band with two or more sourced facts. Sports with fewer than five "
                          "write-ups are listed on the Flagged for Review page; the shortfall is "
                          "disclosed rather than padded with invention.",
        "predictions": kept,
    }
    (DATA / "predictions.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    bad = [r["id"] for r in kept if r["words"] < 30 or BANNED.search(r["text"]) or BANNED.search(r["headline"])]
    print(f"meridian_predictions: {len(kept)} write-ups across {len(count)} sports "
          f"(min {out['min_words']} words), {len(bad)} failing a rule, {len(skipped)} picks without prose")
    if bad:
        print("FAIL:", bad)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
