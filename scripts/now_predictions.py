#!/usr/bin/env python3
"""Write one unique human preview for every published pick on the /now/ desk.

Rules enforced by ``now_verify.py`` and the unit tests:

* at least 30 words, no two previews open with the same five words;
* the selection is named in the text, in plain betting language;
* two or more sourced facts from the fixture's official record are attached to each
  preview and rendered underneath it;
* the words ``model`` and ``verified`` never appear in reader-facing copy.

Low-confidence picks get a preview too, so a reader never has to follow a bare line.
Output: data/now/predictions.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOW = ROOT / "data" / "now"
AS_OF_UTC = "2026-10-24T22:32:00Z"

# fixture_id -> (headline, text)
TEXTS = {
    "vb-per-pra": (
        "Perugia's title pedigree makes the champions the call against promoted Prata",
        "Back Sir Susa Scai Perugia to win at PalaBarton. Perugia are the reigning Italian "
        "champions, while Prata di Pordenone are newly promoted and opened with a 3-1 win over "
        "Vero Volley Monza. Prata's debut result was impressive, but it came against a side that "
        "finished outside the top four, and the step up to facing the champions in Perugia on a "
        "Sunday evening is a different test entirely.",
    ),
    "vb-gie-ber": (
        "Berlin's record haul of Bundesliga titles outweighs Giesen's Ligacup run",
        "Berlin RECYCLING Volleys are the pick to win in Hildesheim. The visitors are the "
        "reigning Bundesliga champions and the competition's record title holders. Giesen hosted "
        "the season-opening Ligacup and reached a first national final in club history in front "
        "of 2,040 spectators, so they arrive in form, but a first home league fixture against "
        "the benchmark side in Germany is the toughest opening assignment available.",
    ),
    "vb-tre-cis": (
        "Trentino and Cisterna both won in round one, so under 4.5 sets is the value",
        "Take under 4.5 sets when Itas Trentino host Cisterna Volley at the BTS Arena. Both "
        "clubs won their opening fixture of the SuperLega season, Trentino away at Modena and "
        "Cisterna 3-1 at home to Allianz Milano. It is the 57th official meeting between the two "
        "clubs, and with Trentino fielding a full fourteen-man roster including Theo Faure, the "
        "best opposite at the 2026 European Championship, a four-set finish is the likeliest "
        "shape of the match.",
    ),
    "urc-osp-dra": (
        "Dragons' unbeaten start in the URC makes them the call at the Ospreys",
        "Back Dragons RFC on the draw-removed match market at 19:00 UK time. The visitors have "
        "one win and one draw from three rounds, 88 points scored against 83 conceded, and nine "
        "league points. The Ospreys have conceded 107 points in three matches, more than any side "
        "in the bottom half, and their form reads loss, loss, win. Dragons have named Rio Dyer "
        "and Jared Rosser in a back three built to counter-attack on the new S4C-televised slot.",
    ),
    "top14-tou-pau": (
        "Pau's five-try form makes them the side to back at Toulon",
        "Section Paloise to win at Toulon. Pau sit second in the Top 14 with 22 league points "
        "from six matches and have scored 239 points, the best attacking return of any side in "
        "the division. Toulon have managed 130 points in the same number of games and have drawn "
        "three of their last five. Pau arrive on the back of wins over Bayonne, La Rochelle, "
        "Vannes and Castres, and their 7-1-1 record makes the draw-removed price look short.",
    ),
    "top14-lar-ubb": (
        "Bordeaux-Begles carry the heavier attack into La Rochelle",
        "Union Bordeaux-Begles are the pick to win on the draw-removed market at Stade Marcel "
        "Deflandre. Bordeaux have scored 215 points in six Top 14 rounds and conceded 151, while "
        "La Rochelle have managed 144 for and 135 against. Bordeaux's sequence reads draw with "
        "Toulouse, win over Paris, draw at Perpignan, win over Lyon and win at Clermont. The one "
        "gap between the clubs is attacking output, and that is what decides tight French "
        "fixtures.",
    ),
    "prem-har-sar": (
        "Harlequins shipping 68 points in three games points to under 56.5",
        "Under 56.5 points is the call at the Twickenham Stoop. Harlequins are bottom of the "
        "Premiership with three defeats from three and a points difference of minus 68, and they "
        "have scored only two league points. Saracens are third on 11 points with a points "
        "difference of plus 21 after a win-loss-win sequence. Round four has already produced "
        "Gloucester 23-5 Bath and Newcastle 17-3 Sale, both comfortably inside this line, and "
        "Quins' problem is scoring rather than conceding.",
    ),
    "cri-pak-eng-odi4": (
        "Pakistan's 2-0 series lead makes them the side to beat England in Lahore",
        "Pakistan to win the fourth ODI at the Gaddafi Stadium. Pakistan have won two of three "
        "matches in this series, including an 87-run defeat of England at Rawalpindi in which "
        "Arafat Minhas took five wickets and made a half-century. England have lost all three, "
        "despite Harry Brook's 202 from 139 balls in the third match, the fastest ODI double "
        "century. A batting line-up that has produced one winless week now meets the side with "
        "the series already in hand.",
    ),
    "darts-lit-asp": (
        "Littler's 105 average and Aspinall's 6-3 opener point to under 17.5 legs",
        "Under 17.5 legs is the selection for the second-round match at the European "
        "Championship. Luke Littler opened with a 6-3 win over William O'Connor at a 105.05 "
        "three-dart average, the best of the tournament at that stage. Nathan Aspinall also won "
        "6-3, against Cristo Reyes. Round two is best of 19 legs and this is the second match of "
        "the Saturday evening session, so a quick, clean finish inside 17 legs is the likeliest "
        "outcome for two players who each dropped only three legs in round one.",
    ),
    "mlb-tb-mil-g2": (
        "Rasmussen's 2.67 ERA gives the Rays the edge with a 1.5-run start",
        "Take Tampa Bay Rays +1.5 at American Family Field. Drew Rasmussen starts for the Rays "
        "after a regular season of 16-5 with a 2.67 ERA across 172 innings, 174 strikeouts and a "
        "0.91 WHIP. Milwaukee lead the World Series after a 3-2 win in game one, and their "
        "starter Logan Henderson was 11-3 with a 2.47 ERA in 18 starts. The Brewers were 103-59 "
        "and 55-26 at home, so a 1.5-run cushion on a genuine ace is the sensible way in.",
    ),
    "gaa-kilkenny-shc-final": (
        "Ballyhale and Tullaroan are level on quality, so the three-point start is the bet",
        "Tullaroan +3.5 is the call in the Kilkenny senior hurling final at UPMC Nowlan Park. "
        "These are the two most decorated clubs in the county, Ballyhale with 21 titles and "
        "Tullaroan with 20, and it is the first time the top two on the roll of honour have met "
        "in the final. Ballyhale beat Thomastown 1-18 to 1-16, a two-point margin, and Tullaroan "
        "are back in a decider for the first time since 1994.",
    ),
    "gaa-galway-sfc-final": (
        "Maigh Cuilinn's 30-point semi-final win warrants a big handicap at Pearse Stadium",
        "Maigh Cuilinn -24.5 is the selection in the Galway senior football final. Their "
        "semi-final was a 4-26 to 0-8 win over Annaghdown, a 30-point margin, while "
        "Salthill-Knocknacarra edged Corofin 0-15 to 2-7 by two points on the same afternoon. "
        "The final was moved to Pearse Stadium at 16:00 after weekend weather warnings forced "
        "the CCC to re-arrange fixtures, and the gulf in semi-final scoring is the clearest "
        "number on the card.",
    ),
    "ten-almaty-final": (
        "Medvedev's 37 hard-court wins and 10-1 week support a games handicap",
        "Daniil Medvedev -3.5 games is the pick for the Almaty Open final. The top seed has won "
        "a Tour-leading 37 hard-court matches in 2026, is 10-1 at this event and has taken three "
        "titles this year, all on hard courts. Nikoloz Basilashvili came through qualifying and "
        "beat Adrian Mannarino 6-3 6-1 in the quarter-finals. Medvedev leads their head-to-head "
        "1-0 after a win in Vienna in 2022, and Medvedev was 6-3 up on Alexander Bublik when the "
        "Kazakh retired in the semi-final.",
    ),
    "ten-basel-djo-hum": (
        "Djokovic's 19-8 season makes him the pick on his Basel return",
        "Novak Djokovic to win his first-round match at the Swiss Indoors. Djokovic is 19-8 in "
        "2026 and eleventh in the PIF ATP Live Race To Turin, and he is playing in Basel for the "
        "first time since 2011, having won the title in 2009. Ugo Humbert is a left-handed "
        "former Top-20 player who has not been drawn against Djokovic before. The draw also puts "
        "top seed Ben Shelton in Djokovic's half, which underlines the standing of the section.",
    ),
    "ten-vienna-alc-kha": (
        "Alcaraz's ranking gap over Khachanov makes him the call in Vienna",
        "Carlos Alcaraz to win his opening match at the Erste Bank Open. Alcaraz is ranked No. 3 "
        "and is chasing a fourth tour-level title of 2026, and he reached the semi-finals in "
        "Vienna as an 18-year-old on his only previous appearance in 2021. Karen Khachanov is a "
        "former Top-10 player and a recent US Open semi-finalist, so this is no formality. "
        "Alcaraz's last completed event ended in a third-round exit to Zizou Bergs in Shanghai, "
        "which is why the price is not shorter.",
    ),
    "hb-hbl-bal-mel": (
        "Melsungen's European pedigree points to a clear win at promoted Balingen",
        "MT Melsungen -5.5 goals is the pick in Balingen. Melsungen won the 2025/26 EHF European "
        "League, their first major title, and have three wins from five Champions League group "
        "games with 138 goals scored and 138 conceded. They beat Orlen Wisla Plock 28-26 in "
        "Kassel on 22 October. Balingen-Weilstetten were promoted this season as 2. Bundesliga "
        "champions and are playing a first home match at this level, so a five-goal start against "
        "a European trophy holder looks short.",
    ),
    "hb-hbl-rnl-scm": (
        "Magdeburg's 5-0 European start is too much for a Löwen side in flux",
        "SC Magdeburg -5.5 goals is the selection at the SAP Arena. Magdeburg are the reigning "
        "German champions after a 31-2-1 season, have won all five Champions League group games "
        "with 176 goals scored and 140 conceded, and beat TVB Stuttgart 29-28 in their last "
        "league outing. Rhein-Neckar Löwen parted company with head coach Maik Machulla on 15 "
        "October and have since lost at home to Eisenach and drawn with Wetzlar. A five-goal "
        "handicap reflects that contrast.",
    ),
    "hb-lnh-sr-paris": (
        "Prandi's 153 goals and PSG's European form make the Parisians the pick",
        "Paris Saint-Germain -5.5 goals is the call at Saint-Raphaël. PSG have already "
        "qualified for the EHF Champions League main round after winning in Celje, and Elohim "
        "Prandi leads the Médiaguide scoring list with 153 goals. Saint-Raphaël's Drevy Paschal "
        "has 174 and both men were nominated in the 2026 LNH awards, so there is individual "
        "quality on both sides. The difference is squad depth: Paris are unbeaten in Europe and "
        "have the deeper bench for a Sunday evening in the Var.",
    ),
    "nhl-sjs-bos": (
        "Boston's 8-2-1 start and Swayman's six wins make them the call at the TD Garden",
        "Boston Bruins to win on the money line. Boston are 8-2-1 with 42 goals scored and 22 "
        "conceded, and they are 5-0-0 at home having allowed six goals in five games at the TD "
        "Garden. Jeremy Swayman has six wins, and David Pastrnak has six goals and ten assists. "
        "San Jose are 6-4-1 but have one regulation win in eleven games, and a .091 regulation "
        "win percentage is the weakest record in the league for holding a lead.",
    ),
    "nhl-car-stl": (
        "St. Louis are unbeaten in four home games and get a 1.5-goal start from Carolina",
        "St. Louis Blues +1.5 is the play at the Enterprise Center. The Blues are 3-0-1 at home "
        "with 15 goals scored and nine conceded, and 5-4-1 overall. Carolina lead the league on "
        "18 points at 8-2-2 and are 6-1-1 on the road with 34 goals in eight away games, so they "
        "deserve to be favourites. The cushion matters because Sebastian Aho has seven goals and "
        "Jackson Blake ten assists, while Mason McTavish has six for St. Louis in a tight "
        "Central Division matchup.",
    ),
    "nhl-tbl-uta": (
        "Tampa Bay's 2-3 road record and a 6-3 defeat in Colorado make plus 1.5 the pick",
        "Tampa Bay Lightning +1.5 is the selection in Salt Lake City. The Lightning lost 6-3 at "
        "Colorado on 23 October after conceding three first-period goals, and they are 2-3-0 on "
        "the road with 16 goals scored and 20 conceded. Utah are 7-4-0 with 41 goals for and 36 "
        "against at the Delta Center. Nikita Kucherov has nine assists and Brandon Hagel seven "
        "goals, so Tampa Bay still carry enough offence to stay within one goal of a Utah side "
        "that has conceded 36.",
    ),
    "nhl-nsh-pit": (
        "Nashville's low-scoring games give them value with a 1.5-goal head start",
        "Nashville Predators +1.5 is the call at PPG Paints Arena. Nashville have scored only 23 "
        "goals in nine games and conceded 30, and four of those games have been on the road where "
        "they have 11 goals for and 16 against. Pittsburgh are 4-6-1 and have lost six of eleven, "
        "though they are 3-1-0 at home with 14 goals in four games. Evgeni Malkin has six goals "
        "and Erik Karlsson ten assists, but nothing in Pittsburgh's record suggests a blowout "
        "against a tight-checking opponent.",
    ),
    "nhl-buf-wsh": (
        "Buffalo's two regulation wins in ten games make Washington the money-line pick",
        "Washington Capitals to win on the money line. Washington are 5-4-0 and 4-2-0 at home "
        "with 22 goals scored and 20 conceded at Capital One Arena, and Alex Tuch has five goals. "
        "Buffalo are 4-4-2 with only two regulation wins in ten and one win in three road games, "
        "and they have conceded 37 goals, the most of any side playing tonight. Logan Thompson "
        "has four wins in the Washington net and the home side's goal difference is the better "
        "of the two.",
    ),
    "nhl-tor-edm": (
        "Edmonton's five road wins and Draisaitl's ten goals make them the pick at home",
        "Edmonton Oilers to win on the money line. Edmonton are 8-1-1 with 47 goals scored and "
        "32 conceded, and they have won all five road games while riding a three-game winning "
        "streak. Leon Draisaitl has ten goals and Connor McDavid 23 assists. Toronto are 6-4-2 "
        "and have lost two of four away from home, although Auston Matthews has eight goals and "
        "ten assists. Rogers Place has been the difference between these two records so far.",
    ),
    "nhl-nyr-ott": (
        "Rangers' 1-4-1 road record turns this into an Ottawa pick",
        "Under 6.5 goals is the call at the Canadian Tire Centre. Ottawa are 7-4-0 with 31 goals "
        "for and 30 against, and the Rangers are 1-4-1 away from Madison Square Garden with only "
        "eight goals scored in six road games, against 29 at home. Artemi Panarin has eight goals "
        "and Adam Fox 14 assists, but New York's road scoring is the thinnest in the league for a "
        "side with a winning record, and Ottawa have kept four of their last six under this "
        "number.",
    ),
    "nhl-vgk-cbj": (
        "Columbus have scored 20 goals in eight games, so a 1.5-goal start holds up",
        "Columbus Blue Jackets +1.5 is the play at Nationwide Arena. Vegas are 8-4-0 with 46 "
        "goals scored, the second-best attack on tonight's card, and Mark Stone has eight goals "
        "with Jack Eichel on 13 assists. Columbus are 3-5-0 and have scored only 20 goals in "
        "eight games, 16 of them at home in six. Kent Johnson has four. The Blue Jackets have "
        "lost four games by two or more, which is exactly the risk in taking the extra goal.",
    ),
    "nhl-det-cgy": (
        "Calgary's 19 goals in nine games make plus 1.5 the sensible way in against Detroit",
        "Calgary Flames +1.5 is the selection at the Scotiabank Saddledome. Calgary have scored "
        "19 goals in nine games and conceded 38, the worst defensive record on the slate, and "
        "they are 2-3-0 at home with 11 goals in five games there. Detroit are 4-3-3 with a plus "
        "one goal difference and are unbeaten in three road games at 1-0-2 and have Alex "
        "DeBrincat on six goals and six assists. Low-scoring home games and a Detroit side that "
        "has not won away in regulation both point to a one-goal margin.",
    ),
    "nba-was-chi": (
        "Two 1-1 records and a short Chicago bench make the Wizards plus 7.5 the pick",
        "Washington Wizards +7.5 is the call at the United Center. Both clubs are 1-1, and "
        "Chicago have listed Claxton out with a left hamstring strain while Essengue is probable "
        "with a right head contusion. Washington have not submitted an injury report, so no "
        "absence can be stated for them, and they are 1-1 at home so far. With both teams on the "
        "same record two games into the season, a 7.5-point start is the safer side of a "
        "coin-flip game.",
    ),
    "nba-gsw-phx": (
        "Phoenix's short injury list against a winless Warriors side gives value at plus 7.5",
        "Phoenix Suns +7.5 is the selection at home. Phoenix are 0-1 and list Williams out after "
        "left shoulder surgery with Ighodaro doubtful and Kennard questionable, but they are "
        "facing a Golden State side on 0-2 that has not submitted an injury report. The Warriors "
        "are 0-1 on the road. Two games into the season, with no result separating these teams "
        "beyond one loss each, a 7.5-point cushion on the home floor is the more defensible "
        "position.",
    ),
    "nba-mia-cha": (
        "Charlotte's four unavailable players make the Heat the pick with 7.5 points",
        "Miami Heat +7.5 is the call at Spectrum Center. Charlotte are 1-1 but list four players "
        "out: Boswell after right knee surgery, Knueppel with a left hamstring strain, White with "
        "a left calf strain and Williams with a right hamstring strain. Miami are 0-2 yet have "
        "nobody listed out, with Larsson probable after a left finger sprain. A 7.5-point start "
        "for a team facing a rotation this thin is the clearest number on the NBA card.",
    ),
    "nba-bkn-cle": (
        "Cleveland's three absences and a home opener make Brooklyn plus 5.5 the pick",
        "Brooklyn Nets +5.5 is the play at Rocket Arena. Brooklyn are 0-1 and list only Bilodeau "
        "out with a right shoulder sprain. Cleveland are also 0-1 and are without Diop for left "
        "knee injury management, Tomlin with a low back stress reaction and Udeh on G League "
        "two-way status, and they lost their only road game before this home opener. With both "
        "sides on one defeat and Cleveland short three bodies, the five-and-a-half point start is "
        "generous.",
    ),
    "nba-nop-den": (
        "Denver's three absences and an 0-2 Pelicans start keep this close at plus 5.5",
        "New Orleans Pelicans +5.5 is the selection in Denver. The Nuggets are 0-1 and list "
        "Johnson out with a right ankle sprain, Jones out for bilateral hamstring management and "
        "Strawther out with a left knee sprain, with Diallo questionable. New Orleans are 0-2 but "
        "have not submitted an injury report, so nothing can be stated about their availability. "
        "Denver have not played at home yet this season and a five-and-a-half point cushion on a "
        "thin rotation is the value side.",
    ),
    "nba-sas-dal": (
        "Dallas at home against a winless Spurs side is the straightforward pick",
        "Dallas Mavericks to win at the American Airlines Center. Dallas are 1-1 after two road "
        "games and have not played at home yet this season. San Antonio are 0-2 and both defeats "
        "came at home, so they arrive on the second night of a difficult start. Neither club had "
        "submitted an injury report at the 1:00 PM ET filing, so no absence can be listed for "
        "either roster. With the Spurs yet to win and Dallas yet to play at home, the home side "
        "is the pick.",
    ),
    "nba-mil-phi": (
        "Philadelphia's 2-0 start outweighs a four-man absence list against Milwaukee",
        "Philadelphia 76ers to win at Xfinity Mobile Arena. The 76ers are 2-0 and 1-0 at home, "
        "while Milwaukee are 0-2. Philadelphia list James out with low back and sciatica issues, "
        "Barlow out with a low back stress reaction, Fall out with a left quadriceps strain and "
        "Hukporti out after an Achilles tear, so the rotation is short. Milwaukee had not "
        "submitted a report at the 1:00 PM ET filing, so their availability is unknown, but an "
        "0-2 start keeps them second best here.",
    ),
    "nba-hou-atl": (
        "Atlanta's home floor edges a meeting of two unbeaten 2-0 teams",
        "Atlanta Hawks to win at home against Houston. Both clubs are 2-0, and Atlanta's wins "
        "have both come on the road, so this is their first home game of the season. Houston are "
        "without Adams for left ankle injury management, VanVleet for right knee injury "
        "management and have Sheppard questionable with a left knee contusion. Atlanta list "
        "Gueye out with a left foot fracture and Veesaar out after an ACL tear. Two unbeaten "
        "teams with similar absence lists make home court the tie-breaker.",
    ),
    "rlwc-aus-fiji": (
        "Australia's round-one win over New Zealand makes them the pick against Fiji",
        "Australia to win on the draw-removed market at 19:05 AEST. Australia beat New Zealand "
        "24-22 in the tournament opener, with James Tedesco captaining from fullback and Sam "
        "Walker and Tom Dearden forming a new halves pairing after Reece Walsh, Mitchell Moses "
        "and Liam Martin were ruled out. Fiji beat Cook Islands 40-12 with Waqa Blake making 188 "
        "run metres, Caleb Navale 202 and Sunia Turuva 169, and Apisai Koroisau leads an "
        "unchanged side. Beating New Zealand by two is a stronger form line than beating Cook "
        "Islands by 28.",
    ),
    "cri-nz-ind-t20i3": (
        "India's two chase wins make them a narrow call in Wellington",
        "India to win the third T20I at Hnry Stadium is a low-confidence selection rather than a "
        "strong stance. The tourists have taken both completed matches by four wickets: they "
        "chased a New Zealand total of 225/4 in the opener and needed 26 not out from 13 balls "
        "by Nitish Kumar Reddy in the second. India lead 2-0, but Ishan Kishan missed that "
        "second match with a low-grade right adductor strain, and Finn Allen's 45 off 24 in the "
        "opening game shows the hosts still carry serious power at the top of the order.",
    ),
    "cri-tus-cob": (
        "Laycock's record spell gives Tuskers a route back against Cobras",
        "Kaneez Tuskers to win at Pietermaritzburg Oval is a low-confidence play on a bowler in "
        "exceptional form. Chad Laycock took 6/26 against the Titans, the record bowling "
        "performance in the captured official report, even though the Tuskers were then bowled "
        "out for 124 in a 63-run defeat to Boland. YesPlay Cobras edged Boland by six wickets "
        "with one ball remaining at Newlands, so they arrive with a recent win of their own. "
        "The case for the "
        "Tuskers rests on their strike bowler disrupting a similarly tight contest at home.",
    ),
    "cri-bol-tit": (
        "An unbeaten six-match run keeps the Titans narrowly ahead at Boland Park",
        "Momentum Multiply Titans to win at Boland Park is a low-confidence selection because "
        "their six-match unbeaten run meets a home side coming off an emphatic 63-run victory. "
        "Boland posted 187 in 20 overs against the Tuskers, with Lehan Botha making 54 and "
        "Gavin Kaplan 38, before bowling the visitors out for 124. The Titans extended their "
        "own sequence by beating those same Tuskers, and that sustained run across six matches "
        "is the main reason to prefer them by the smallest of margins in this domestic T20.",
    ),
}


def main() -> int:
    picks = json.loads((NOW / "picks.json").read_text(encoding="utf-8"))
    preds, missing, missing_high_medium = [], [], []
    for pick in picks["picks"]:
        entry = TEXTS.get(pick["fixture_id"])
        if not entry:
            missing.append(pick["fixture_id"])
            if pick["confidence"] in {"high", "medium"}:
                missing_high_medium.append(pick["fixture_id"])
            continue
        headline, text = entry
        preds.append({
            "id": "pred-" + pick["fixture_id"],
            "pick_id": pick["id"],
            "fixture_id": pick["fixture_id"],
            "sport": pick["sport"],
            "competition": pick["competition"],
            "home": pick["home"],
            "away": pick["away"],
            "start_utc": pick["start_utc"],
            "start_display": pick["start_display"],
            "market": pick["market"],
            "selection": pick["selection"],
            "confidence": pick["confidence"], "score": pick.get("score"),
            "probability": pick["probability"],
            "american_display": pick["american_display"],
            "headline": headline,
            "text": text,
            "words": len(text.split()),
            "official_url": pick["official_url"],
            "olbg_url": pick["olbg_url"],
            "facts": pick["facts"],
        })
    by_sport = {}
    for p in preds:
        by_sport[p["sport"]] = by_sport.get(p["sport"], 0) + 1
    payload = {
        "as_of_utc": AS_OF_UTC,
        "count": len(preds),
        "min_words": min((p["words"] for p in preds), default=0),
        "by_sport": dict(sorted(by_sport.items())),
        "missing_for_published_pick": missing,
        "missing_for_high_or_medium_pick": missing_high_medium,
        "predictions": preds,
    }
    (NOW / "predictions.json").write_text(json.dumps(payload, indent=1) + "\n",
                                          encoding="utf-8")
    print(f"now_predictions: {len(preds)} previews across {len(by_sport)} sports, "
          f"shortest {payload['min_words']} words, {len(missing)} picks without prose")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
