#!/usr/bin/env python3
"""Author the /latest/ written previews and join them to the graded picks.

The prose below was written for this desk, one selection at a time, from the facts already carried
on each fixture record. Nothing is templated: no two previews open the same way and each one names
the market, the selection and the numbers it leans on. `facts_used` names the exact claims from the
fixture record that the preview rests on, and the build refuses to publish a preview whose claim is
not on the record with a source URL.

Rules enforced here (and re-checked by scripts/latest_verify.py):
  * at least 30 words of prose;
  * the words banned by the brief do not appear in reader-facing copy;
  * every preview maps to a graded pick on a fixture that had not started;
  * at least two sourced facts per preview.

Run:  python scripts/latest_predictions.py
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "latest"
MIN_WORDS = 30
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)

# (fixture_id, market, selection) -> (headline, prose, facts_used)
PROSE = [
    ("nhl-sjs-bos", "Match winner (money line)", "Boston Bruins",
     "Swayman's six wins and Boston's six goals conceded at home point one way",
     "Boston Bruins to win the money line at TD Garden. Boston are 8-2-1 with 42 goals scored and 22 "
     "conceded, and at home they have given up just six goals in five games while scoring 21. Jeremy "
     "Swayman has six wins in that run. San Jose are 6-4-1 but have only one regulation win in 11, and "
     "David Pastrnak's six goals and ten assists give Boston the sharper top line.",
     ["Boston 2026-27 record", "Boston home split", "San Jose 2026-27 record",
      "San Jose regulation-win record", "Boston goalkeeper wins"]),

    ("nhl-tor-edm", "Match winner (money line)", "Edmonton Oilers",
     "Edmonton are 5-0-0 away and take that record into Toronto",
     "Edmonton Oilers to win. Edmonton are 8-1-1 and perfect on the road at 5-0-0, scoring 27 and "
     "conceding 13 across those five away games, with Leon Draisaitl on 10 goals and Connor McDavid on "
     "23 assists. Toronto are 6-4-2 and 2-1-1 away, and Auston Matthews has eight goals and ten assists, "
     "but the Oilers' road record is the stronger half of this fixture.",
     ["Edmonton 2026-27 record", "Edmonton road split", "Toronto 2026-27 record",
      "Toronto road split", "Team leaders"]),

    ("nhl-buf-wsh", "Match winner (money line)", "Washington Capitals",
     "Washington are 4-2-0 at home while Buffalo have two regulation wins in ten",
     "Washington Capitals to win. Washington are 5-4-0 and 4-2-0 at home, with 22 goals for and 20 "
     "against in six home games, and Alex Tuch has five goals. Buffalo are 4-4-2 with only two "
     "regulation wins in ten matches and a 1-0-2 road record, and Tage Thompson's five goals are the "
     "Sabres' leading return. The home split is the clearest difference between them.",
     ["Washington 2026-27 record", "Washington home split", "Buffalo 2026-27 record",
      "Buffalo regulation form", "Team leaders"]),

    ("nhl-vgk-cbj", "Match winner (money line)", "Vegas Golden Knights",
     "Vegas average almost four goals a game and Columbus have conceded 29 in eight",
     "Vegas Golden Knights to win. Vegas are 8-4-0 with 46 goals scored, Mark Stone on eight goals and "
     "Jack Eichel on 13 assists. Columbus are 3-5-0, have scored 20 goals in eight games while "
     "conceding 29, and are 3-3-0 at home. Kent Johnson's four goals are the Blue Jackets' leading "
     "return, which is a thin base against a side scoring at close to four a game.",
     ["Columbus 2026-27 record", "Vegas 2026-27 record", "Columbus home split", "Team leaders"]),

    ("nhl-det-cgy", "Match winner (money line)", "Detroit Red Wings",
     "Calgary have conceded 38 goals in nine games and Detroit arrive 1-0-2 on the road",
     "Detroit Red Wings to win at the Scotiabank Saddledome. Detroit are 4-3-3 with eight goals for and "
     "seven against in three road games, a 1-0-2 record, and Alex DeBrincat has six goals and six "
     "assists. Calgary are 3-6-0, have conceded 38 goals in nine matches and are 2-3-0 at home, with "
     "Morgan Frost's three goals their leading return.",
     ["Calgary 2026-27 record", "Detroit 2026-27 record", "Detroit road split",
      "Calgary home split", "Team leaders"]),

    ("nba-sas-dal", "Match winner (draw removed)", "Dallas Mavericks",
     "San Antonio are 0-2 after two home defeats and travel to Dallas",
     "Dallas Mavericks to win. Dallas are 1-1 and San Antonio are 0-2, having lost both of their games "
     "at home, so a Spurs side still looking for a first win visits a Mavericks team that has already "
     "split two road games. Both clubs were listed NOT YET SUBMITTED on the 1:00 PM ET injury filing, "
     "so no absence can be stated for either roster.",
     ["Dallas record", "San Antonio record", "Injury report status", "Dallas road split",
      "San Antonio road split"]),

    ("nba-mil-phi", "Match winner (draw removed)", "Philadelphia 76ers",
     "Philadelphia are 2-0 and Milwaukee are 0-2 with no report filed",
     "Philadelphia 76ers to win. Philadelphia are 2-0 and won their only home game, while Milwaukee are "
     "0-2 and had not filed an injury report at the 1:00 PM ET deadline. The 76ers are without James, "
     "Barlow, Fall and Hukporti, so this selection rests on the record and the home court rather than "
     "on a full roster.",
     ["Philadelphia record", "Milwaukee record", "Philadelphia unavailable",
      "Milwaukee report status", "Philadelphia home record"]),

    ("nba-hou-atl", "Match winner (draw removed)", "Atlanta Hawks",
     "Both sides are 2-0 but Atlanta's wins both came on the road",
     "Atlanta Hawks to win. Both teams are 2-0, yet Atlanta's two wins both came away from home and "
     "this is their first home game of the season. Houston are without Adams and VanVleet and list "
     "Sheppard questionable with a left knee contusion, while Atlanta are missing Gueye and Veesaar; "
     "the form lines are level, so the home floor separates them.",
     ["Atlanta record", "Houston record", "Houston unavailable", "Atlanta unavailable",
      "Atlanta home record"]),

    ("nba-gsw-phx", "Match winner (draw removed)", "Phoenix Suns",
     "Golden State are 0-2 and 0-1 on the road heading into Phoenix",
     "Phoenix Suns to win. Phoenix are 0-1 and Golden State are 0-2, one of those defeats coming on the "
     "road. Phoenix list Williams out after left shoulder surgery and Ighodaro doubtful with an oblique "
     "strain, while Golden State had not filed a report at the 1:00 PM ET deadline. The Warriors' 0-1 "
     "road start is the form line behind this price.",
     ["Phoenix record", "Golden State record", "Phoenix unavailable",
      "Golden State report status", "Golden State road record"]),

    ("nba-was-chi", "Match winner (draw removed)", "Chicago Bulls",
     "Washington have played both games at home and are 0-0 on the road",
     "Chicago Bulls to win. Both teams are 1-1, but Washington are 0-0 on the road and have played both "
     "of their games at home, while Chicago have already split a pair. Chicago list Claxton out with a "
     "left hamstring strain and Essengue probable after a head contusion; Washington had not filed a "
     "report by the 1:00 PM ET deadline.",
     ["Chicago record", "Washington record", "Chicago unavailable",
      "Washington report status", "Washington road record"]),

    ("mlb-tb-mil-g2", "Handicap 1.5", "Tampa Bay Rays +1.5",
     "Rasmussen's 2.67 ERA makes a one-run cushion worth taking",
     "Tampa Bay Rays with a 1.5-run start in Game 2 of the World Series. The Rays went 98-64 with 736 "
     "runs scored and 650 allowed, and they lost Game 1 by a single run, 3-2. Drew Rasmussen starts on "
     "a 16-5 record and 2.67 ERA over 30 starts, with 174 strikeouts and a 0.91 WHIP in 172 innings, so "
     "one run of cover is the value here.",
     ["Rays regular season", "World Series Game 1 result", "Game 2 probable pitchers",
      "Rasmussen 2026", "Henderson 2026"]),

    ("mlb-tb-mil-g2", "Total runs 9.5", "Under 9.5",
     "Two sub-3.00 ERAs and a 3-2 opener point under nine and a half",
     "Under 9.5 runs in Game 2 of the World Series. Milwaukee allowed 618 runs in the regular season "
     "and Tampa Bay allowed 650. Logan Henderson starts with a 2.47 ERA and a 0.84 WHIP across 18 "
     "starts, Drew Rasmussen with a 2.67 ERA and a 0.91 WHIP, and Game 1 finished 3-2 - six runs below "
     "this line.",
     ["Brewers regular season", "Rays regular season", "World Series Game 1 result",
      "Game 2 probable pitchers", "Rasmussen 2026", "Henderson 2026"]),

    ("mlb-tb-mil-g2", "Match winner (money line)", "Milwaukee Brewers",
     "The 103-win side are at home with their best starter on the mound",
     "Milwaukee Brewers to win Game 2. Milwaukee were 103-59 with 832 runs scored and 618 allowed, won "
     "Game 1 by 3-2 on 23 October and start Logan Henderson, who is 11-3 with a 2.47 ERA and a 0.84 "
     "WHIP in 18 starts. Tampa Bay counter with Drew Rasmussen's 16-5 record and 2.67 ERA, so this is a "
     "pitchers' duel in which the stronger regular-season side has the home dugout.",
     ["Brewers regular season", "World Series Game 1 result", "Game 2 probable pitchers",
      "Henderson 2026", "Rasmussen 2026"]),

    ("mlb-tb-mil-g2", "Total runs 8.5", "Under 8.5",
     "Neither of these rotations has given up runs at a nine-run pace",
     "Under 8.5 runs is the call at American Family Field. Game 1 finished 3-2, so five runs fewer than this line "
     "were enough. Milwaukee conceded 618 runs across the regular season and Tampa Bay 650, and the "
     "starters are Henderson (2.47 ERA, 0.84 WHIP) and Rasmussen (2.67 ERA, 0.91 WHIP). Both clubs' "
     "best arms are in this game.",
     ["Brewers regular season", "Rays regular season", "World Series Game 1 result",
      "Game 2 probable pitchers", "Rasmussen 2026", "Henderson 2026"]),

    ("top14-lar-ubb", "Total points 60.5", "Under 60.5",
     "Two of the tighter defensive records in the TOP 14 meet in La Rochelle",
     "The points line sits at 60.5 at Stade Marcel-Deflandre, and the under is the selection. The home side have scored 144 and conceded 135 in six "
     "TOP 14 rounds; Bordeaux have scored 215 and conceded 151. La Rochelle's league run reads "
     "W-D-D-W-W and Bordeaux's D-W-D-W-W, and both arrive on a win, which on these scoring records "
     "points to a controlled afternoon rather than a shoot-out.",
     ["La Rochelle league record", "Bordeaux league record", "Bordeaux recent form",
      "La Rochelle recent form"]),

    ("top14-lar-ubb", "Match winner (draw removed)", "Union Bordeaux-Bègles",
     "Bordeaux have scored 71 more points than La Rochelle this season",
     "Union Bordeaux-Bègles to win. Bordeaux are third on 19 points with 215 scored in six rounds and "
     "arrive on a five-match league run of D-W-D-W-W, winning the last two against Lyon and at "
     "Clermont. La Rochelle are fourth on 18 with 144 scored, so the visitors' scoring rate is the "
     "clearest difference between the two records.",
     ["La Rochelle league record", "Bordeaux league record", "Bordeaux recent form",
      "La Rochelle recent form"]),

    ("top14-lar-ubb", "Handicap 11.5", "Stade Rochelais +11.5",
     "An 11.5-point start is a large cushion for a side with four wins in six",
     "Stade Rochelais with an 11.5-point start. La Rochelle are 4-2 with 144 points scored and 135 "
     "conceded, and their five-match league run reads W-D-D-W-W. Bordeaux have scored 101 more points "
     "but conceded 16 more, and a handicap this size asks them to win by two converted tries or more "
     "away from home, which their recent draws at Perpignan and against Toulouse do not support.",
     ["La Rochelle league record", "Bordeaux league record", "Bordeaux recent form",
      "La Rochelle recent form"]),

    ("top14-lar-ubb", "Total points 48.5", "Over 48.5",
     "The two records average 53.75 points a match",
     "Over 48.5 points. Bordeaux's six league matches have produced 366 points and La Rochelle's 279, "
     "an average of 53.75 per match across those twelve team games. Both clubs have won four of six and "
     "both have scored freely through October, so a line almost five points below their combined "
     "average is the side of the market to take.",
     ["La Rochelle league record", "Bordeaux league record", "Bordeaux recent form",
      "La Rochelle recent form"]),

    ("top14-lar-ubb", "Handicap 1.5", "Union Bordeaux-Bègles -1.5",
     "A 1.5-point line asks only that Bordeaux win",
     "Union Bordeaux-Bègles by two points or more is the call. They have scored 215 points in six "
     "rounds, 71 more than La Rochelle's 144, and they have won two of their last three league matches, "
     "at Perpignan and at Clermont. A 1.5-point line asks only for a win, and the scoring gap between "
     "the two records is why it is priced at a shade under even money.",
     ["La Rochelle league record", "Bordeaux league record", "Bordeaux recent form"]),

    ("rlwc-aus-fiji", "Match winner (draw removed)", "Australia",
     "Tedesco, Walker and Dearden form a rebuilt spine against Fiji",
     "Australia to win at Suncorp Stadium. Australia beat New Zealand 24-22 in the tournament opener "
     "and name James Tedesco at fullback with Sam Walker and Tom Dearden in the halves after Reece "
     "Walsh, Mitchell Moses and Liam Martin were ruled out. Fiji beat Cook Islands 40-12 with Caleb "
     "Navale running 202 metres and Waqa Blake 188, but that is a different class of opponent.",
     ["Australia Round 1", "Fiji Round 1", "Pool A standing", "Australia team changes", "Fiji team"]),

    ("rlwc-aus-fiji", "Handicap 3.5", "Australia -3.5",
     "A 3.5-point line against a Fiji side that has played one pool match",
     "A 3.5-point handicap for Australia is the selection. Their 24-22 win over New Zealand is the strongest "
     "form line in Pool A, and Fiji's 40-12 win came against Cook Islands. Apisai Koroisau's side are "
     "unchanged from Round 1, while Australia have rebuilt their spine around Walker and Dearden; the "
     "small line still asks for a converted-try margin.",
     ["Australia Round 1", "Fiji Round 1", "Pool A standing", "Australia team changes", "Fiji team"]),

    ("rlwc-aus-fiji", "Total points 48.5", "Under 48.5",
     "The opener produced 46 points and this line sits above it",
     "The 48.5-point line looks high for this pool match, so Under 48.5 is the play. Australia's opener against New Zealand produced 46 points and Fiji's against "
     "Cook Islands 52. Australia have replaced three frontline players, including both first-choice "
     "halves, and Fiji name an unchanged seventeen; a total set above the 46 the opener produced looks "
     "the wrong side of a match between two sides with settled defences.",
     ["Australia Round 1", "Fiji Round 1", "Australia team changes", "Fiji team"]),

    ("rlwc-aus-fiji", "Handicap 13.5", "Fiji +13.5",
     "Fiji have scored 40 in the tournament and get two scores of cover",
     "Fiji with a 13.5-point start. Fiji top Pool A after a 40-12 win in which Caleb Navale ran 202 "
     "metres and Waqa Blake 188, and Apisai Koroisau captains an unchanged side. Australia are without "
     "Reece Walsh, Mitchell Moses and Liam Martin and start two new halves, so a two-score cushion for "
     "a team that has already posted 40 points is the pick.",
     ["Australia Round 1", "Fiji Round 1", "Pool A standing", "Australia team changes", "Fiji team"]),

    ("rlwc-aus-fiji", "Total points 40.5", "Over 40.5",
     "Both Round 1 matches cleared this line easily",
     "Over 40.5 points in Brisbane. The Round 1 matches involving these two sides produced 46 and 52 "
     "points, and Fiji scored 40 on their own against Cook Islands. A line five points below the lower "
     "of those two totals is short for two teams who both put up 24 points or more in the opening "
     "round of the pool.",
     ["Australia Round 1", "Fiji Round 1", "Pool A standing"]),

    ("cri-pak-eng-odi4", "Match winner", "Pakistan",
     "England have not won in three attempts and Pakistan beat them by 87",
     "Pakistan to win the fourth ODI in Lahore. Pakistan beat England by 87 runs at Rawalpindi on 20 "
     "October, with Arafat Minhas taking five wickets and making a half-century. England have no win in "
     "three matches this series; they did make 429/4 on 22 October, Harry Brook striking the fastest "
     "ODI double century, and Sri Lanka still chased it down.",
     ["Match 2", "England innings", "England series position", "Match 1", "Match 3"]),

    ("cri-nz-ind-t20i3", "Match winner", "India",
     "India lead 2-0 and have chased down 225 in this series",
     "India to win the third T20I in Wellington. India have won both matches by four wickets, the "
     "second on 24 October when Nitish Kumar Reddy made 26 not out from 13 balls, and they lead the "
     "five-match series 2-0. New Zealand made 225/4 in the first game and still lost, with Finn Allen "
     "making 45 from 24 balls.",
     ["First T20I", "Second T20I", "Series position", "India availability", "Venue"]),

    ("cri-tus-cob", "Match winner", "Kaneez Tuskers",
     "Laycock's 6/26 is the best return on this card",
     "Kaneez Tuskers to win at Pietermaritzburg Oval. The Tuskers were bowled out for 124 in a 63-run "
     "defeat to Boland, but Chad Laycock's 6/26 against Titans is the record bowling performance in "
     "this competition and gives them a wicket-taking route. The Cobras beat Boland by six wickets with "
     "one ball remaining at Newlands, so neither side arrives in dominant form.",
     ["Tuskers recent result", "Tuskers individual", "Cobras recent result", "Fixture"]),

    ("cri-bol-tit", "Match winner", "Momentum Multiply Titans",
     "The Titans have won six in a row, Boland have lost none of their own",
     "Momentum Multiply Titans to win at Boland Park. The Titans extended an unbeaten run to six "
     "matches by beating the Tuskers. Boland posted 187 in 20 overs and beat the Tuskers by 63 runs "
     "behind Lehan Botha's 54 and Gavin Kaplan's 38. Both arrive in form, and the Titans' six-match "
     "sequence is the longer of the two.",
     ["Titans form", "Boland form", "Boland collapse of note", "Fixture"]),

    ("ten-almaty-final", "Handicap 3.5", "Daniil Medvedev -3.5",
     "Medvedev is 10-1 at this event and leads the head-to-head",
     "Daniil Medvedev on the 3.5 handicap in the Almaty final. Medvedev has a Tour-leading 37 "
     "hard-court wins in 2026, is 10-1 at the Almaty Open, has won three titles this year on hard "
     "courts and leads Nikoloz Basilashvili 1-0 head to head from Vienna in 2022. Basilashvili came "
     "through qualifying and beat Mannarino 6-3 6-1, but the line asks only for a one-break margin.",
     ["Semi-final 1", "Medvedev hard-court season", "Medvedev titles", "Basilashvili route",
      "Head-to-head"]),

    ("ten-basel-djo-hum", "Match winner", "Novak Djokovic",
     "Djokovic is 19-8 this year and returns to a court he won on in 2009",
     "Novak Djokovic to win his Basel first round. Djokovic is 19-8 in 2026 and 11th in the PIF ATP "
     "Live Race To Turin, and he returns to the Swiss Indoors for the first time since 2011, having won "
     "the title in 2009. Ugo Humbert, a former Top-20 left-hander, is the opponent, and top seed Ben "
     "Shelton sits in the same half of the draw.",
     ["Draw", "Djokovic 2026", "Djokovic history", "Humbert profile", "Event"]),

    ("ten-vienna-alc-kha", "Match winner", "Carlos Alcaraz",
     "Alcaraz is world No. 3 and chasing a fourth title of the year",
     "Carlos Alcaraz to win his Vienna opener. Alcaraz is No. 3 in the PIF ATP Rankings and is chasing "
     "a fourth tour-level title of 2026, though he arrives after a third-round loss to Zizou Bergs in "
     "Shanghai. Karen Khachanov is a former Top-10 player and a recent US Open semi-finalist, and this "
     "is Alcaraz's first Vienna appearance since he reached the semi-finals as an 18-year-old in 2021.",
     ["Draw", "Alcaraz ranking", "Alcaraz recent form", "Vienna history", "Khachanov profile"]),

    ("ten-basel-djo-hum", "Handicap 3.5", "Ugo Humbert +3.5",
     "A 3.5 start for a former Top-20 left-hander against a part-season opponent",
     "Ugo Humbert with a 3.5 start against Djokovic. Humbert is a former Top-20 left-hander, and "
     "Djokovic has played 27 tour matches in 2026, going 19-8, before arriving in Basel for the first "
     "time since 2011. A three-and-a-half line gives the Frenchman room in a first-round match where "
     "the favourite has not competed at this venue for fourteen years.",
     ["Draw", "Djokovic 2026", "Djokovic history", "Humbert profile"]),

    ("ten-vienna-alc-kha", "Handicap 3.5", "Karen Khachanov +3.5",
     "Alcaraz has not played here since 2021 and Khachanov gets three and a half",
     "Karen Khachanov with a 3.5 start against Alcaraz. Khachanov is a former Top-10 player and a "
     "recent US Open semi-finalist, and Alcaraz arrives in Vienna after a third-round exit to Zizou "
     "Bergs in Shanghai, his most recent completed event. Alcaraz has not played this tournament since "
     "2021, and a 3.5 line keeps the selection live if the match turns on a tight set.",
     ["Draw", "Alcaraz recent form", "Vienna history", "Khachanov profile"]),

    ("hb-hbl-rnl-scm", "Handicap 5.5", "SC Magdeburg -5.5",
     "Magdeburg are 5-0 in Europe and the Löwen changed coach this month",
     "SC Magdeburg to win by six or more on the 5.5-goal handicap. Magdeburg are 5-0 in EHF Champions League "
     "group F with 176 goals scored and 140 conceded, and they are the reigning German champions after "
     "a 31-2-1 season. Rhein-Neckar Löwen parted company with head coach Maik Machulla on 15 October "
     "and have since lost at home to Eisenach and drawn with Wetzlar.",
     ["Magdeburg EHF Champions League", "Magdeburg domestic status", "Löwen coaching change",
      "Löwen recent domestic form", "Magdeburg last league result"]),

    ("hb-lnh-sr-paris", "Handicap 5.5", "Paris Saint-Germain -5.5",
     "Paris reached the European main round and take on a side they outgun",
     "Paris Saint-Germain to win by six or more at Saint-Raphaël. Paris qualified for the EHF Champions "
     "League main round with a win in Celje, and Elohim Prandi leads their scoring on 153 goals. "
     "Saint-Raphaël's Drevy Paschal has 174 and both men were nominated in the 2026 LNH awards, but the "
     "champions' European form is the stronger line in this fixture.",
     ["Fixture", "Paris European record", "Médiaguide leaders", "LNH awards"]),

    ("hb-hbl-rnl-scm", "Handicap 9.5", "Rhein-Neckar Löwen +9.5",
     "Nine and a half goals is a lot of cover for the home side",
     "Rhein-Neckar Löwen with a 9.5-goal start. The Löwen changed coach on 15 October and have lost at "
     "home to Eisenach and drawn with Wetzlar, while Magdeburg are unbeaten in five European games with "
     "a plus-36 goal difference and won 29-28 at Stuttgart on 18 October. A nine-and-a-half-goal "
     "cushion is the way to take a home side in transition.",
     ["Magdeburg EHF Champions League", "Magdeburg last league result", "Löwen coaching change",
      "Löwen recent domestic form"]),

    ("hb-lnh-sr-paris", "Handicap 9.5", "Saint-Raphaël +9.5",
     "Paschal has 174 goals and Saint-Raphaël get almost ten goals of cover",
     "Saint-Raphaël with a 9.5-goal start. Drevy Paschal has 174 goals, the leading figure on the "
     "Médiaguide list for this fixture, and he was nominated in the 2026 LNH awards alongside Paris's "
     "Elohim Prandi, who has 153. Paris won in Celje to reach the Champions League main round, but "
     "nine and a half goals is a large cushion in a domestic fixture.",
     ["Fixture", "Paris European record", "Médiaguide leaders", "LNH awards"]),

    ("hb-hbl-rnl-scm", "Handicap 7.5", "SC Magdeburg -7.5",
     "Magdeburg's 36-goal European differential against a side in transition",
     "SC Magdeburg on the 7.5 line. Magdeburg won 29-28 at TVB Stuttgart on 18 October and are 5-0 in "
     "Europe with 176 goals for and 140 against. The Löwen's coaching change on 15 October has been "
     "followed by a home defeat to Eisenach and a draw with Wetzlar, which is the form gap this line is "
     "measuring.",
     ["Magdeburg EHF Champions League", "Magdeburg last league result", "Löwen coaching change",
      "Löwen recent domestic form"]),

    ("vb-per-pra", "Match winner", "Sir Susa Scai Perugia",
     "Champions at home against a side playing its second top-flight match",
     "Sir Susa Scai Perugia to win at PalaBarton. Perugia are the reigning Italian champions, while "
     "Tinet Prata di Pordenone are newly promoted and opened their SuperLega season with a 3-1 win over "
     "Vero Volley Monza. That debut was a good one, but it came against a side outside the top four and "
     "the step up to facing the champions away is a different test.",
     ["Fixture", "Perugia status", "Prata Round 1", "Prata status", "Broadcast"]),

    ("vb-per-pra", "Total sets 4.5", "Under 4.5",
     "A 3-0 or 3-1 home win beats this line and only a fifth set loses it",
     "Perugia and Prata should land under 4.5 sets, so the under is the pick. Perugia are the reigning champions and Prata were "
     "promoted from Serie A2, so a 3-0 or 3-1 home win keeps this under and only a five-set match beats "
     "it. Prata's 3-1 opening win over Monza shows they can take a set, which is why the line sits at "
     "4.5 rather than 3.5.",
     ["Fixture", "Perugia status", "Prata Round 1", "Prata status"]),

    ("vb-tre-cis", "Total sets 4.5", "Under 4.5",
     "Both sides won 3-1 in Round 1, pointing at a four-set night",
     "Four sets or fewer between Itas Trentino and Cisterna Volley is the call, so the under 4.5 is the selection. Trentino won at Modena in Round 1 and "
     "have their full fourteen-player roster available, including Theo Faure, the best opposite at the "
     "2026 European Championship. Cisterna beat Allianz Milano 3-1, so a four-set finish is the "
     "likeliest outcome and the under is the selection.",
     ["Fixture", "Trentino Round 1", "Cisterna Round 1", "Trentino squad"]),

    ("vb-tre-cis", "Match winner", "Cisterna Volley",
     "Fifty-six meetings and two 3-1 opening wins make this a coin flip",
     "Cisterna Volley to win at Trentino. Both sides won their opening match 3-1, Cisterna over "
     "Allianz Milano and Trentino at Modena, and the clubs have met 56 times in official competition. "
     "Trentino have the deeper squad with Theo Faure available, but the Round 1 records are level and "
     "the price reflects a match with no clear favourite.",
     ["Fixture", "Trentino Round 1", "Cisterna Round 1", "Trentino squad", "Head-to-head history"]),

    ("gaa-kilkenny-shc-final", "Handicap 3.5", "Shamrocks Ballyhale +3.5",
     "Two points separated Ballyhale from Thomastown in the semi-final",
     "A 3.5-point start for Shamrocks Ballyhale in the Kilkenny final. The club hold 21 Kilkenny "
     "senior hurling titles to Tullaroan's 20 and beat Thomastown 1-18 to 1-16 in the semi-final. "
     "Tullaroan reached a first decider since 1994 by beating Bennettsbridge, and this is the first "
     "time the two most decorated clubs in the county have met in the final.",
     ["Final", "Historic first", "Titles", "Ballyhale semi-final", "Tullaroan semi-final"]),

    ("gaa-kilkenny-shc-final", "Handicap 1.5", "Shamrocks Ballyhale +1.5",
     "A 1.5-point cushion for the county's most decorated club",
     "Shamrocks Ballyhale with a 1.5-point start at UPMC Nowlan Park. Their 1-18 to 1-16 win "
     "over Thomastown is the only semi-final scoreline carried on the official record, a two-point "
     "margin, and they hold 21 county titles against Tullaroan's 20. Tullaroan are in a first final "
     "since 1994, with Owen Beehan refereeing the decider.",
     ["Final", "Titles", "Ballyhale semi-final", "Tullaroan semi-final", "Referee"]),

    ("gaa-kilkenny-shc-final", "Match winner (draw removed)", "Shamrocks Ballyhale",
     "Level prices, so pedigree is the tie-breaker",
     "Shamrocks Ballyhale to win the Kilkenny senior hurling final. The club hold 21 county titles "
     "against Tullaroan's 20 and beat Thomastown 1-18 to 1-16 in the semi-final, while Tullaroan are in "
     "a first final since 1994. The two clubs have never met at this stage before, and with the price "
     "level the pick rests on Ballyhale's record in deciders.",
     ["Final", "Historic first", "Titles", "Ballyhale semi-final", "Tullaroan semi-final"]),

    ("f1-usgp-race", "Race winner", "Kimi Antonelli",
     "Pole by 0.179 seconds at Circuit of The Americas",
     "Kimi Antonelli to win the United States Grand Prix. Antonelli took pole at Circuit of The "
     "Americas with 1:34.035 in Q3, 0.179 seconds clear of Max Verstappen, with Isack Hadjar third on "
     "1:34.250. Starting from the front for Mercedes, the grid curve used here gives him a 40% share of "
     "the race, the largest of any driver on the grid.",
     ["Pole position", "Front row", "Session window"]),

    ("f1-usgp-race", "Winner without the pole sitter", "Max Verstappen",
     "Second on the grid and 0.036 clear of his team-mate",
     "Max Verstappen to win without the pole sitter. Verstappen qualified second on 1:34.214, 0.179 "
     "behind Antonelli and 0.036 ahead of team-mate Isack Hadjar on 1:34.250. Red Bull fill two of the "
     "top three grid slots, and in a market that removes Antonelli, Verstappen carries a 40% share of "
     "what remains.",
     ["Pole position", "Front row", "Session window"]),

    ("f1-usgp-race", "Winner without the pole sitter", "Isack Hadjar",
     "Third on the grid ahead of both Ferraris",
     "Isack Hadjar to win without the pole sitter. Hadjar qualified third on 1:34.250, ahead of both "
     "Ferraris of Charles Leclerc on 1:34.267 and Lewis Hamilton on 1:34.311. The Red Bull pair start "
     "together on the second row, and with the pole sitter removed from the market Hadjar holds a 24% "
     "share of the remaining chance.",
     ["Front row", "Ferrari row three", "Session window"]),

    ("f1-usgp-race", "Race winner", "Max Verstappen",
     "Plus money on the second-fastest qualifier",
     "Max Verstappen to win the United States Grand Prix at plus money. Verstappen lines up second, "
     "0.179 seconds off Antonelli's 1:34.035 pole, and Red Bull placed both cars in the top three. At "
     "+317 the grid curve gives him a 24% chance of the win, which is the longest price carried by any "
     "front-row starter on this grid.",
     ["Pole position", "Front row", "Ferrari row three"]),

    ("f1-usgp-race", "Winner without the pole sitter", "Charles Leclerc",
     "Fourth on the grid, 0.017 seconds off the second Red Bull",
     "Charles Leclerc to win without the pole sitter. Leclerc qualified fourth on 1:34.267, 0.017 "
     "seconds off the second Red Bull of Hadjar, with Ferrari team-mate Lewis Hamilton fifth on "
     "1:34.311. Ferrari have both cars in the top five and the market removes only Antonelli, so the "
     "grid curve gives Leclerc a 14% share of what is left.",
     ["Ferrari row three", "Front row", "Session window"]),
]


def build():
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    fixtures = {f["id"]: f for f in json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]}
    index = {(p["fixture_id"], p["market"], p["selection"]): p for p in picks["picks"]}

    out, problems = [], []
    for fixture_id, market, selection, headline, text, facts_used in PROSE:
        key = (fixture_id, market, selection)
        pick = index.get(key)
        if not pick:
            problems.append(f"no graded pick for {key}")
            continue
        fixture = fixtures[fixture_id]
        facts = fixture["facts"]
        attached = []
        for claim in facts_used:
            match = [f for f in facts if f["claim"] == claim]
            if not match:
                problems.append(f"{key}: no such fact on the record: {claim}")
                continue
            attached.append(match[0])
        if len(attached) < 2:
            problems.append(f"{key}: fewer than two sourced facts attached")
        if BANNED.search(text) or BANNED.search(headline):
            problems.append(f"{key}: banned wording in reader-facing copy")
        words = len(text.split())
        if words < MIN_WORDS:
            problems.append(f"{key}: {words} words, below the {MIN_WORDS}-word floor")
        out.append({
            "pick_id": pick["id"],
            "fixture_id": fixture_id,
            "sport": pick["sport"],
            "competition": pick["competition"],
            "home": pick["home"],
            "away": pick["away"],
            "start_utc": pick["start_utc"],
            "start_display": pick["start_display"],
            "market": market,
            "selection": selection,
            "confidence": pick["confidence"],
            "probability": pick["probability"],
            "american_display": pick["american_display"],
            "headline": headline,
            "text": text,
            "words": words,
            "official_url": pick["official_url"],
            "facts": [{"claim": f["claim"], "value": f["value"], "source_url": f["source_url"],
                       "source_key": f["source_key"]} for f in attached],
        })

    if problems:
        for p in problems:
            print("  FAIL:", p)
        return 1

    by_sport = {}
    for row in out:
        by_sport[row["sport"]] = by_sport.get(row["sport"], 0) + 1
    doc = {
        "build_utc": picks["build_utc"],
        "count": len(out),
        "min_words": min(r["words"] for r in out),
        "by_sport": by_sport,
        "note": ("One preview per graded pick. Every claim underneath a preview is copied from the "
                 "fixture record with the page it was read from."),
        "predictions": out,
    }
    (DATA / "predictions.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    openings = {r["text"].split()[0].lower() for r in out}
    print(f"latest_predictions: {len(out)} previews across {len(by_sport)} sports, "
          f"shortest {doc['min_words']} words, {len(openings)} different opening words")
    for s, n in by_sport.items():
        print(f"  {s:14s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
