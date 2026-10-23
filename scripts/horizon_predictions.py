"""Horizon desk (session arena/9c5af337-olbg2) — editorial predictions.

Writes data/horizon/predictions.json containing up to 5 predictions per covered
sport (every priced fixture up to 5 per sport, ordered by highest confidence).

Hard rules enforced by scripts/horizon_verify.py:
  - Every prediction is >= 30 words.
  - Neither 'model' nor 'verified' (or any case variant) appears in any prediction.
  - Every prediction names the teams/competitors, player(s), current form, recent
    match history, match statistics, injury/availability status, and an explicit
    betting selection with originated odds.
  - Every opening phrase and sentence is unique across the entire corpus.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "horizon")

FORBIDDEN = re.compile(r"\b(model|verified)\b", re.IGNORECASE)

PROSE = {
    # --- Ice Hockey (top 5 by confidence) ----------------------------------
    "nhl-2026020170": (
        "Boston Bruins host the San Jose Sharks at TD Garden holding an 8-2-1 record (17 points, 7-2-1 in their last ten, W1) "
        "with 41 goals scored against 29 allowed (3.73 GF/G vs 2.64 GA/G) and a 5-1-0 home mark. San Jose arrive at 1-7-2 "
        "(4 points, L4, 0-4-1 on the road) with 20 goals for and 40 against (4.00 GA/G). Neither club lists an injury scratch "
        "on the NHL schedule feed for this matchup. Our fair moneyline prices Boston at -355 (78.0%), shorter than the -250 ceiling, "
        "so the selection is Boston Bruins to win and Boston Bruins -1.5 on the puck line at -113."
    ),
    "nhl-2026020172": (
        "Pittsburgh Penguins welcome the Nashville Predators to PPG Paints Arena sitting 6-3-1 through ten games (13 points, W1, "
        "3-1-1 at home) with 33 goals for and 29 against (3.30 GF/G, 2.90 GA/G). Nashville enter on a three-game slide at 2-6-1 "
        "(5 points, 1-3-0 on the road) while scoring 21 goals and conceding 33 across nine outings (2.33 GF/G, 3.67 GA/G). "
        "No player injury designations are attached to the official NHL game entry. With Pittsburgh's fair moneyline at -355 (78.0%), "
        "we pair the Pittsburgh Penguins match winner call with the in-band Pittsburgh Penguins -1.5 puck line at -113."
    ),
    "nhl-2026020176": (
        "Edmonton Oilers return to Rogers Place on a five-game winning streak at 8-1-1 (17 points, 8-1-1 over ten games, 4-0-1 at home) "
        "after piling up 41 goals and yielding 29 (4.10 GF/G vs 2.90 GA/G). Visiting Toronto Maple Leafs stand 4-4-2 (10 points, L1, "
        "1-2-1 on the road) with 31 goals scored and 33 conceded in ten games. The NHL game feed carries no injury exclusions for "
        "either roster at capture time. Because Edmonton's fair moneyline sits at -355 (78.0%), our selection is Edmonton Oilers to win "
        "alongside Edmonton Oilers -1.5 on the puck line at -113."
    ),
    "nhl-2026020173": (
        "Washington Capitals skate onto Capital One Arena ice at 7-2-1 (15 points, W2, 5-1-0 at home) having outscored opponents "
        "34-23 across ten games (3.40 GF/G and a league-low 2.30 GA/G among Saturday hosts). Buffalo Sabres travel south at 4-5-1 "
        "(9 points, L1, 2-3-0 away) with 29 goals scored and 32 allowed. No injury scratches are posted on the official NHL schedule "
        "endpoint for this contest. Washington's fair moneyline is -346 (77.6%), so we back the Washington Capitals as match winner "
        "and take the actionable Washington Capitals -1.5 puck line at -111."
    ),
    "nhl-2026020171": (
        "Ottawa Senators host the New York Rangers at Canadian Tire Centre with a 6-2-1 record (13 points, W1, 4-1-0 on home ice) "
        "and a 32-26 goal differential over nine appearances (3.56 GF/G vs 2.89 GA/G). New York arrive at 3-5-2 (8 points, L2, "
        "2-2-1 on the road) having scored 27 times while surrendering 33 goals in ten games. Neither side has a separate injury "
        "report attached on the NHL schedule feed. Ottawa's fair moneyline prices at -329 (76.7%), making our selection Ottawa "
        "Senators to win paired with the in-band Ottawa Senators -1.5 puck line at -107."
    ),

    # --- Basketball (top 5 by confidence) ----------------------------------
    "el-E2026_76": (
        "Panathinaikos AKTOR Athens host Armani Olimpia Milan in EuroLeague Round 8 at Telekom Center Athens sitting 6-1 through "
        "seven rounds with 613 points scored and 517 allowed (87.6 PF/G vs 73.9 PA/G, a +96 cumulative margin). Milan arrive at "
        "1-6 with 585 points for and 648 against (83.6 PF/G vs 92.6 PA/G, -63 net). EuroLeague's Round 8 game centre lists no "
        "pre-game injury exclusions at capture time. Panathinaikos price at -733 (88.0%) on the fair moneyline, so we pair the "
        "Panathinaikos match winner pick with Panathinaikos -19.5 on the point spread at -108."
    ),
    "nba-0022600095": (
        "Indiana Pacers open their home clash with the Dallas Mavericks at 1-0 after opening night while Dallas travel in at 0-1. "
        "The official 3:15 PM ET NBA Referee Injury Report rules Dallas big men Dereck Lively II (right foot surgery) and Santi "
        "Aldama (right knee surgery) plus wing Caleb Martin (right thumb sprain) Out, while Indiana list T.J. McConnell (right "
        "hamstring strain) and Johnny Furphy (right ACL repair) Out. With Dallas missing both interior rotation pieces, Indiana's "
        "fair moneyline reaches -317 (76.0%); we select Indiana Pacers to win and take Indiana Pacers -8.5 at -108."
    ),
    "nba-0022600102": (
        "Los Angeles Lakers and LA Clippers meet at 10:00 PM ET with both clubs holding 1-0 records from their season openers, "
        "but the 3:15 PM ET NBA injury bulletin tilts the rotation sharply: the Clippers list Bradley Beal (right knee injury "
        "management), Brandon Ingram (right heel surgery), Jordan Miller (left rotator cuff surgery), and Max Strus (right plantar "
        "fascia) all Out, while the Lakers have zero players on the injury report. That four-man wing absence pushes the Lakers' "
        "fair moneyline to -317 (76.0%), so we pick Los Angeles Lakers to win and back Los Angeles Lakers -8 at -108."
    ),
    "el-E2026_73": (
        "Real Madrid visit Kosner Baskonia Vitoria-Gasteiz at Buesa Arena for EuroLeague Round 8 carrying a 4-3 record across seven "
        "games with 667 points scored and 630 conceded (95.3 PF/G vs 90.0 PA/G, +37 net). Baskonia sit bottom of the table at 1-6 "
        "having scored 583 points and surrendered 649 (83.3 PF/G vs 92.7 PA/G, -66 net). No injury exclusions appear on the "
        "EuroLeague Round 8 game-centre sheet. Real Madrid's fair moneyline is -312 (75.7%), so we select Real Madrid as match "
        "winner and play the in-band Real Madrid -7.5 point spread at +108."
    ),
    "el-E2026_77": (
        "Hapoel IBI Tel Aviv host Anadolu Efes Istanbul at Arena Botevgrad in EuroLeague Round 8 holding a 5-2 record after seven "
        "games with 630 points scored and 601 allowed (90.0 PF/G vs 85.9 PA/G, +29 differential). Efes enter at 3-4 with 581 "
        "points for and 590 against (83.0 PF/G vs 84.3 PA/G, -9 net). EuroLeague's official Round 8 match listing records no "
        "injury absences at capture time. Hapoel's fair moneyline prices at -299 (74.9%), so we back Hapoel IBI Tel Aviv to win "
        "and take Hapoel IBI Tel Aviv -7 on the spread at -108."
    ),

    # --- Baseball (all 2 World Series fixtures) ----------------------------
    "mlb-849805": (
        "Milwaukee Brewers host the Tampa Bay Rays in World Series Game 1 at American Family Field riding a five-game winning "
        "streak, an 8-2 mark over their last ten, and a 103-59 regular season (832 runs scored, 618 allowed, 55-26 at home, "
        "68-35 in night games). Tampa Bay went 98-64 (736 scored, 650 allowed, 43-38 away, 5-5 in ten, L1). Jacob Misiorowski "
        "starts for Milwaukee after posting a 16-5 record, 1.80 ERA, 0.80 WHIP, and 252 strikeouts in 174.2 innings across 30 "
        "starts against Nick Martinez (31 starts, 15-6, 3.10 ERA, 1.09 WHIP, 109 K in 180.0 IP), with no injury scratches on "
        "either starter. Milwaukee's fair moneyline is -285 (74.0%), so we pick Milwaukee Brewers to win and play Milwaukee "
        "Brewers -1.5 on the run line at -122."
    ),
    "mlb-849802": (
        "World Series Game 2 keeps the Tampa Bay Rays (98-64, 736 runs for, 650 against, 43-38 road, L1) at American Family Field "
        "against the Milwaukee Brewers (103-59, 832 runs for, 618 against, 55-26 home, W5, 8-2 in ten). Tampa Bay hand the ball "
        "to right-hander Drew Rasmussen, who went 16-5 with a 2.67 ERA, 0.91 WHIP, 174 strikeouts, and 32 walks across 172.0 "
        "innings in 30 starts, while Milwaukee name Logan Henderson, whose 2026 regular-season MLB pitching split is blank on "
        "StatsAPI and flagged rather than estimated; neither club lists an injury replacement for the starters. We select "
        "Milwaukee Brewers to win at a fair moneyline of -134 (57.4%, medium confidence)."
    ),

    # --- Cricket (all 3 priced fixtures) -----------------------------------
    "cri-40394": (
        "India Women meet Zimbabwe Women in the 2nd ODI at Vadodara International Cricket Stadium two days after winning the "
        "series opener on 23 October by 9 wickets: Zimbabwe Women were bowled out for 197 in 49.5 overs before India Women "
        "chased 1-200 in just 27.1 overs at 7.38 runs per over. Cricket Australia's match hub lists no injury withdrawals for "
        "either squad ahead of Sunday's fixture. India Women price at -355 (78.0%) on the fair match-winner line, so our "
        "selection is India Women to win paired with the in-band India Women -45.5 first-innings runs handicap at -138."
    ),
    "cri-41095": (
        "New Zealand and India contest the 2nd T20I at Hagley Oval in Christchurch on 24 October after India took the opening "
        "T20I at the same venue on 22 October by 4 wickets, overhauling New Zealand's 4-225 (20.0 overs) with 6-230 in 19.4 "
        "overs for a combined 455 runs across 39.4 overs. Neither camp has an injury scratch posted on the Cricket Australia "
        "match centre. With both batting line-ups clearing 11.2 runs per over on the Hagley Oval surface, we pick India to win "
        "at -127 (56.0%, medium confidence) and also note Over 195.5 first-innings runs at -127."
    ),
    "cri-40981": (
        "Pakistan host England at Gaddafi Stadium in Lahore in the Pakistan ODI Tri-Series on 25 October after England's high-"
        "scoring 2-wicket defeat to Sri Lanka in Rawalpindi on 22 October, where England piled up 4-429 from 50.0 overs (8.58 "
        "runs per over) and Sri Lanka replied with 8-430 in 49.5 overs. Cricket Australia's fixture feed reports no injury "
        "absences for the Lahore leg, and Pakistan have not yet batted in the captured tri-series results. We select England "
        "to win at a fair moneyline of -108 (52.0%, low confidence) with Over 315.5 first-innings runs at -122."
    ),

    # --- Snooker (all 3 priced fixtures) -----------------------------------
    "snk-ni-sf1": (
        "Kyren Wilson faces Sam Craigie in the first BetVictor Northern Ireland Open semi-final at Waterfront Hall, Belfast on "
        "Saturday 24 October over the best of 11 frames. World number nine Wilson holds £716,800 on the Johnstone's Paint World "
        "Rankings and swept past Anthony McGill 6-1 in Friday's quarter-final after edging He Guoqiang 4-3 in Round 3, whereas "
        "Craigie (#44 on £132,000) beat Elliot Slessor 6-2 in the quarter-final and Matthew Selt 4-2 in Round 3, with no medical "
        "withdrawals reported by WST. We select Kyren Wilson to win at -237 (70.3%, high confidence, inside the -250 ceiling)."
    ),
    "snk-ic-murphy": (
        "Shaun Murphy meets Mitchell Mann in Round 2 of the International Championship in Nanjing over the best of 11 frames. "
        "Murphy sits seventh on the Johnstone's Paint World Rankings with £897,350 and has compiled a 65% match win rate across "
        "20 appearances in the 2026/27 season with a 21.0-second average shot time, 46 breaks of 50+, and 15 centuries. Mann "
        "enters with a 48% win rate across 17 matches, a 31.5-second average shot time, 23 half-centuries, and 4 centuries, and "
        "WST lists both players active without injury withdrawals. Our selection is Shaun Murphy to win at -219 (68.6%, medium "
        "confidence) and Shaun Murphy -1.5 frames at -136."
    ),
    "snk-ic-zhou": (
        "Zhou Yuelong and Liam Davies clash in Nanjing in the International Championship Round 2 over the best of 11 frames. "
        "Although Zhou is world number 17 on £359,100 with a 57% win rate over 23 season matches (26.4s shot time, 51 breaks "
        "of 50+, 14 centuries), WST's match centre records Davies at a 75% win rate across 28 matches in 2026/27 with a faster "
        "24.9-second average shot time, 57 breaks of 50+, and 11 centuries, and neither player has an injury withdrawal. "
        "Driven by Davies's superior 28-match season win rate and scoring volume, we pick Liam Davies to win at -152 (60.2%, "
        "medium confidence)."
    ),

    # --- Darts (top 5 by confidence) ---------------------------------------
    "drt-r2-1": (
        "Top seed Ross Smith (£158,000 on the 2026 European Tour Rankings) meets 17th seed Damon Heta in Saturday afternoon's "
        "Machineseeker European Championship Round Two at Westfalenhalle, Dortmund over the best of 11 legs. Smith defeated Karel "
        "Sedlacek 6-4 in Thursday's opening round, while Heta survived a deciding-leg 6-5 win over James Wade, and both players "
        "came through Day One with no medical withdrawals reported by the PDC. Ross Smith's fair moneyline sits at -257 (72.0%), "
        "just shorter than -250, so we select Ross Smith as match winner and take Ross Smith -1.5 legs at -163."
    ),
    "drt-r2-7": (
        "Third seed Krzysztof Ratajski (£89,500 on the 2026 European Tour Order of Merit) takes on 19th seed and four-time "
        "European Champion Michael van Gerwen in Saturday evening's Round Two session in Dortmund over the best of 11 legs. "
        "Ratajski's top-three European Tour qualification campaign puts him 16 seed places ahead of van Gerwen in the official "
        "PDC bracket, and neither player is listed with an injury withdrawal on the tournament hub. With Ratajski's fair "
        "moneyline at -257 (72.0%), we pick Krzysztof Ratajski to win and play the in-band Krzysztof Ratajski -1.5 leg handicap "
        "at -163."
    ),
    "drt-r2-5": (
        "Second seed Wessel Nijman (£124,000 on the 2026 European Tour Rankings) faces 15th seed Ryan Joyce in Saturday evening's "
        "best-of-11 Round Two tie at Dortmund's Westfalenhalle. Nijman qualified second across the 14-event European Tour season "
        "behind only Ross Smith, whereas Joyce enters from the middle of the 32-man seed list with no injury issues reported on "
        "the PDC schedule release. Nijman's fair moneyline prices at -253 (71.7%), four ticks shorter than -250, so our selection "
        "is Wessel Nijman to win paired with Wessel Nijman -1.5 legs at -161."
    ),
    "drt-r2-3": (
        "Thirteenth seed Gerwyn Price meets 29th seed Cameron Menzies in Saturday afternoon's Round Two session in Dortmund over "
        "the best of 11 legs. Price dispatched Rob Cross 6-2 in Thursday's opening round while Menzies upset fourth seed Niels "
        "Zonneveld 6-3 on Day One, and both players are confirmed fit on the PDC order of play. Seated 16 places higher on the "
        "European Tour table and fresh off a four-leg Round One victory margin, Gerwyn Price prices right on the high-confidence "
        "threshold at -233 (70.0%), giving us an in-band moneyline selection on Gerwyn Price to win."
    ),
    "drt-r2-6": (
        "Seventh seed Jonny Clayton and tenth seed Josh Rock lock horns in Saturday evening's Machineseeker European Championship "
        "Round Two at Westfalenhalle over the best of 11 legs. Separated by only three places on the 2026 European Tour seeding "
        "ladder and with no injury withdrawals affecting the Saturday evening card, this matchup projects as the tightest seeded "
        "clash of the night. Our fair line makes Jonny Clayton a -124 favourite (55.3%, medium confidence), and we pair Jonny "
        "Clayton to win with Over 9.5 total legs at -117."
    ),

    # --- Tennis (top 5 by confidence) --------------------------------------
    "ten-brussels-sf2": (
        "Top seed Arthur Fils and unseeded German veteran Jan-Lennard Struff meet in Saturday evening's second ATP 250 Brussels "
        "semifinal on Centre Court (not before 18:30 local). World number 10 Fils carries 3,325 points on the 19 October PIF ATP "
        "Singles Rankings and advanced past fifth seed Alex Michelsen 6-4, 7-6(12) in Friday's quarter-final, while world number "
        "58 Struff holds 929 ATP points after eliminating Zizou Bergs in straight sets, with neither semifinalist listing an "
        "injury withdrawal. That 3,325-to-929 points edge prices Arthur Fils at -238 (70.4%, high confidence), right inside our "
        "-250 ceiling, so the selection is Arthur Fils to win."
    ),
    "ten-brussels-sf1": (
        "Third seed Francisco Cerundolo faces Dutchman Tallon Griekspoor in Saturday's opening ATP 250 Brussels semifinal on "
        "Centre Court (not before 16:00 local). Cerundolo sits at world number 21 with 2,220 PIF ATP points after winning his "
        "quarter-final in straight sets, whereas Griekspoor stands at world number 60 on 885 ATP points, and the ATP Tour daily "
        "schedule reports no injury withdrawals for either player. Backed by a 2,220-to-885 ranking-points advantage, our "
        "selection is Francisco Cerundolo to win at -187 (65.1%, medium confidence) and Cerundolo -3.5 games at -113."
    ),
    "ten-almaty-sf1": (
        "Daniil Medvedev and Alexander Bublik contest the second semifinal of the ATP 250 Almaty Open on Center Court (not before "
        "18:00 local on Saturday 24 October). World number 5 Medvedev holds 3,660 PIF ATP points and defeated Terence Atmane "
        "6-4, 6-4 in Friday's quarter-final, while eighth-seeded home favourite Bublik sits at world number 19 with 2,275 points "
        "after outlasting Karen Khachanov 4-6, 7-6(5), 7-6(5) in two tiebreak sets, with no medical withdrawals on the ATP sheet. "
        "We select Daniil Medvedev to win at -138 (58.0%, medium confidence) alongside Over 22.5 games at -113."
    ),
    "ten-vienna-q1f": (
        "Adolfo Daniel Vallejo takes on Italian veteran Lorenzo Sonego in Saturday's Erste Bank Open Qualifying Round 1 on "
        "Glaubandich Court in Vienna. Second qualifying seed Vallejo is ranked world number 54 with 997 points on the 19 October "
        "PIF ATP Singles table, while unseeded Sonego enters at world number 89 with 658 ATP points, and the official Vienna "
        "order of play lists both players active with no medical withdrawals. Holding a 339-point cushion in the ATP standings, "
        "our selection is Adolfo Daniel Vallejo to win at -133 (57.0%, medium confidence)."
    ),
    "ten-vienna-q1d": (
        "Top qualifying seed Thiago Agustin Tirante faces French left-hander Adrian Mannarino in Saturday's Erste Bank Open "
        "Qualifying Round 1 on Centre Court in Vienna (not before 18:00 local). Tirante sits at world number 50 with 1,032 PIF "
        "ATP Singles points compared with world number 79 Mannarino on 743 points, and neither player carries an injury tag on "
        "the ATP Tour Vienna schedule. Supported by Tirante's 289-point ranking lead over best-of-three sets, we pick Thiago "
        "Agustin Tirante to win at -125 (55.6%, medium confidence)."
    ),

    # --- Golf (both verified tournaments) ----------------------------------
    "golf-genesis": (
        "Antoine Rozner and Casey Jarvis share the 36-hole lead at the DP World Tour's Genesis Championship in Korea on 10-under "
        "132 after Rozner carded rounds of 67 and 65 and Jarvis posted 65 and 67, three strokes clear of Martin Couvra (69-66), "
        "Filippo Celli (69-66), Ryan Fox (68-67), and Sanghun Shin (66-69) tied on 7-under 135, with Si Woo Kim and Daihan Lee "
        "at 6-under 136 and no withdrawals among the leaders. Rozner's second-round 65 gives him the momentum entering Saturday's "
        "09:06 tee times, so we select Antoine Rozner outright at +304 (24.8%, low confidence) and Rozner at -104 in the co-leader "
        "matchbet against Jarvis."
    ),
    "golf-bermuda": (
        "Kensei Hirata (65-64) and Chandler Blanchet (62-67) sit tied atop the PGA TOUR's Butterfield Bermuda Championship at "
        "Port Royal Golf Course on 13-under 129 after 36 holes, one shot ahead of Seamus Power (66-64), Corey Conners (63-67), "
        "Eric Cole (65-65), Ben Silverman (63-67), and Danny Walker (63-67) all finished on 12-under 130, with the projected cut "
        "at -5 and no injury withdrawals among the top nine. Hirata's bogey-free Friday 64 outpaced Blanchet's 67 by three strokes, "
        "so we select Kensei Hirata to win outright at +649 (13.4%, low confidence) and Hirata at -104 in the 36-hole co-leader "
        "matchbet over Blanchet."
    ),

    # --- Greyhounds (both GBGB Category One finals) ------------------------
    "grey-oaks": (
        "G D Holland's Fahrenheit Jess heads the six-runner Premier Greyhound Racing Oaks Final over 480m at Dunstall Park on "
        "Saturday 24 October (£20,000 to the winner) after making all in Semi-Final 2 on 17 October in a fastest-of-the-round "
        "27.87 seconds (-10 going) ahead of Holding Hollie. B Fairbairn's Slingshot Poppy won Semi-Final 3 in 27.90s (-10) from "
        "Ballydoyle Tina, while K R Hutton's Signet Nayla took Semi-Final 1 in 28.35s (-10) from Strike It Skye, and all six "
        "bitches are declared fit on the GBGB card. Holding a 0.03s edge over Slingshot Poppy and 0.48s over Signet Nayla, our "
        "selection is Fahrenheit Jess to win at +150 (40.0%, low confidence)."
    ),
    "grey-scurry": (
        "Richard Rees's Shadow Storm leads the Arena Racing Company Scurry Gold Cup Final over 270m at Dunstall Park on Saturday "
        "24 October (£12,500 winner's prize) after clocking 15.66 seconds (-5 going) to win Semi-Final 3 by 1¼ lengths from "
        "Newinn Souly on 17 October. M P Brown's Roanna Mamba won Semi-Final 2 in 15.73s (-5) ahead of Magical Jason, while "
        "kennelmate Avarua Lake took Semi-Final 1 in 15.86s (-5) from Ballinakill Liam, with all six finalists declared on the "
        "GBGB open-race sheet. With a 0.07s cushion over Roanna Mamba and 0.20s over Avarua Lake, we select Shadow Storm to win "
        "at +162 (38.1%, low confidence)."
    ),

    # --- Handball (all 3 priced Daikin StarLigue fixtures) -----------------
    "hb-nantes-chambery": (
        "HBC Nantes welcome Chambéry to H Arena in Daikin StarLigue Journée 08 on Saturday 24 October at 19:00 local sitting "
        "second in the table at 6-1-0 with 244 goals scored and 203 conceded across seven games (34.9 GF/G vs 29.0 GA/G, +41 "
        "goal difference). Chambéry arrive 12th at 2-3-2 with 224 goals for and 231 against (32.0 GF/G vs 33.0 GA/G, -7). LNH "
        "lists no injury scratches for the Saturday fixture. Nantes price at -337 (77.1%) on the three-way moneyline, so we pair "
        "Nantes to win with the in-band Nantes -6.5 goal handicap at -108."
    ),
    "hb-montpellier-saran": (
        "Montpellier Handball host Saran on Sunday 25 October at 17:00 local in Daikin StarLigue Journée 08 holding a 4-1-2 "
        "record through seven matches with 234 goals scored and 205 conceded (33.4 GF/G vs 29.3 GA/G, +29 differential). Saran "
        "enter 11th at 3-4-0 with 202 goals for and 216 against (28.9 GF/G vs 30.9 GA/G, -14), and no player injury exclusions "
        "are published on the LNH calendar page. Montpellier's fair three-way moneyline sits at -309 (75.5%), so our selection "
        "is Montpellier to win alongside Montpellier -6 on the two-way goal handicap at -108."
    ),
    "hb-sr-paris": (
        "Paris Saint-Germain Handball travel to Saint-Raphaël on Sunday 25 October at 16:00 local unbeaten at 7-0-0 atop the "
        "Daikin StarLigue standings with 239 goals scored and 190 allowed across seven outings (34.1 GF/G vs 27.1 GA/G, +49 "
        "goal difference). Saint-Raphaël sit 14th at 2-5-0 with 207 goals for and 225 against (29.6 GF/G vs 32.1 GA/G, -18), "
        "with no injury withdrawals listed on the LNH fixture feed. Even accounting for the 8% three-way draw allocation and "
        "road venue, Paris price at -234 (70.1%, high confidence), right inside the -250 ceiling, so we select Paris to win."
    ),

    # --- Motor Racing (both Formula 1 markets) -----------------------------
    "f1-wdc": (
        "After 17 rounds of the 2026 FIA Formula One World Championship, Kimi Antonelli leads the Drivers' Standings on 340 "
        "points, 102 clear of Mercedes teammate George Russell (238), with Lewis Hamilton on 229, Max Verstappen on 221, Charles "
        "Leclerc on 215, Lando Norris on 201, and Oscar Piastri on 138, and all contenders active in Austin with no injury "
        "stand-ins. Antonelli's 102-point cushion prices him at -900 (90.0%, high confidence) for the title, shorter than -250, "
        "so we pair Kimi Antonelli to win the Drivers' Championship with the in-band Runner-Up Championship Matchbet backing "
        "George Russell (238 pts, +0.326s in Austin FP1) over Lewis Hamilton (229 pts) at -127."
    ),
    "f1-usgp": (
        "Charles Leclerc topped Friday's Practice 1 at the 5.513-km, 56-lap Circuit of The Americas in Austin with a 1:36.052 "
        "benchmark, 0.084s ahead of Max Verstappen, 0.245s clear of Lando Norris, 0.326s ahead of George Russell (238 season "
        "points), and 0.481s up on championship leader Kimi Antonelli (340 points), with all 20 drivers taking part and no "
        "medical substitutions. Weighting FP1 pace at COTA with 17-round season points makes Leclerc the +234 race-winner "
        "favourite (30.0%, low confidence) and -113 in an FP1 top-two head-to-head matchbet over Verstappen."
    ),

    # --- Rugby League (top 5 by confidence) --------------------------------
    "rlwc-eng-fra": (
        "England meet France in Rugby League World Cup Round 2 at HBF Park, Perth on 24 October looking to rebound from their "
        "12-30 Round 1 defeat to Tonga (-18 differential), while France sit sixth on the ladder after suffering a 4-78 Round 1 "
        "thrashing against Samoa (-74 differential). NRL.com's official match centre lists both nations without injury-forced "
        "team-list withdrawals at capture time. That 56-point gap in Round 1 scoring margin puts England's fair moneyline at "
        "-670 (87.0%), so we pick England as match winner and take the in-band England -21 points handicap at -108."
    ),
    "rlwc-r3-leb-fra": (
        "Lebanon and France square off in RLWC Round 3 at CommBank Stadium, Sydney on 1 November. Lebanon opened with an 18-42 "
        "loss to Papua New Guinea (-24 margin) before falling 0-36 to Tonga in Round 2, whereas France were overwhelmed 4-78 by "
        "Samoa in Round 1 (-74 margin) at the same Sydney venue, and NRL's draw hub carries no injury exclusions for this fixture. "
        "Because Lebanon's fair moneyline prices at -563 (84.9%) off the Round 1 margin baseline, our selection is Lebanon to "
        "win paired with the actionable Lebanon -19 points handicap at -108."
    ),
    "rlwc-r3-ton-sam": (
        "Tonga and Samoa collide in a heavyweight Pacific RLWC Round 3 showdown at CommBank Stadium, Sydney on 1 November. "
        "Tonga beat England 30-12 (+18) in Round 1 and shut out Lebanon 36-0 in Round 2, while Samoa sit second on points "
        "differential after dismantling France 78-4 (+74) in Round 1 at CommBank Stadium, with no injury withdrawals posted on "
        "the NRL draw feed. Samoa's explosive +74 opening margin prices them at -388 (79.5%) on the fair moneyline, so we back "
        "Samoa to win and play Samoa -15 on the handicap at +108."
    ),
    "rlwc-png-samoa": (
        "Papua New Guinea host Samoa at Santos National Football Stadium in Port Moresby in RLWC Round 2 on 24 October after "
        "beating Lebanon 42-18 (+24 margin, 3rd on the ladder) in Round 1, while second-placed Samoa arrive off a 78-4 (+74 "
        "margin) demolition of France in Sydney. Neither team has an injury scratch recorded on the NRL draw page at capture "
        "time. Samoa's 50-point superior Round 1 margin puts their fair moneyline at -326 (76.5%), so we select Samoa as match "
        "winner and take Samoa -13 on the points handicap at +108."
    ),
    "rlwc-r3-aus-cook": (
        "Australia face the Cook Islands in RLWC Round 3 at Queensland Country Bank Stadium in Townsville on 31 October. The "
        "Kangaroos edged New Zealand 24-22 (+2 margin, 2nd on the ladder) in their tournament opener, whereas the fourth-placed "
        "Cook Islands lost 12-40 (-28 margin) to Fiji in Round 1, and NRL's match hub lists no injury withdrawals. With "
        "Australia's fair moneyline sitting at -314 (75.9%), shorter than the -250 ceiling, we select Australia to win and "
        "back the in-band Australia -12.5 points handicap at -108."
    ),

    # --- Rugby Union (top 5 by confidence across PREM + URC) ---------------
    "ru-quins-saracens": (
        "Harlequins host London rivals Saracens at Twickenham Stoop on Sunday 25 October in Gallagher PREM Round 4 sitting 10th "
        "and last at 0-0-3 with a -68 points difference and 2 league points after three rounds. Saracens arrive third at 2-0-1 "
        "with a +21 points difference and 11 league points, and Premiership Rugby's fixture feed lists no injury withdrawals at "
        "capture time. That nine-point and 89-point-differential gulf puts Saracens at -1567 (94.0%) on the fair moneyline, so "
        "we pick Saracens to win and play the in-band Saracens -35 points handicap at -108."
    ),
    "ru-bulls-ulster": (
        "Vodacom Bulls welcome Ulster to Loftus Versfeld on Saturday 24 October in United Rugby Championship Round 4 sitting "
        "second in the 16-club table at 2-0-1 with 126 points scored, 54 conceded (+72 differential), and 11 league points "
        "through three rounds. Ulster enter seventh at 0-2-1 with 88 points for, 93 against (-5 differential), and 8 league "
        "points, with no injury withdrawals listed on the URC match centre. Backed by a +77 points-difference edge at altitude "
        "in Pretoria, the Bulls price at -1194 (92.3%) on the moneyline, so we select Vodacom Bulls to win and take Vodacom "
        "Bulls -23.5 on the handicap at -108."
    ),
    "ru-benetton-glasgow": (
        "Benetton Rugby host table-topping Glasgow Warriors at Stadio Monigo in Treviso on Saturday 24 October in URC Round 4. "
        "Glasgow lead the URC standings at 2-1-0 with 95 points scored, 72 conceded (+23 differential), and 13 league points, "
        "whereas 10th-placed Benetton stand 0-1-2 with 64 points for, 68 against (-4 differential), and 5 league points, and no "
        "injury scratches appear on the URC Round 4 feed. Glasgow's eight-point table lead prices them at -967 (90.6%) on the "
        "fair moneyline, so we pick Glasgow Warriors to win and back Glasgow Warriors -21.5 at -108."
    ),
    "ru-stormers-scarlets": (
        "DHL Stormers host Scarlets at DHL Stadium in Cape Town on Saturday 24 October in URC Round 4 holding third place on the "
        "official URC table at 2-0-1 with 81 points scored, 54 conceded (+27 differential), and 11 league points after three "
        "rounds. Eighth-placed Scarlets travel south at 1-0-2 with 68 points for, 85 against (-17 differential), and 7 league "
        "points, with no injury exclusions listed on the URC match centre. With the Stormers' fair moneyline at -823 (89.2%), "
        "our selection is DHL Stormers to win paired with the in-band DHL Stormers -20 points handicap at -108."
    ),
    "ru-bristol-exeter": (
        "Bristol Bears welcome West Country rivals Exeter Chiefs to Ashton Gate on Saturday 24 October in Gallagher PREM Round 4 "
        "holding sixth place at 2-0-1 with a +2 points difference and 10 league points after three rounds. Exeter sit eighth at "
        "1-0-2 with a -21 points difference and 8 league points, and no injury withdrawals are posted on the Premiership Rugby "
        "match listing. Bristol's home advantage and 23-point superior differential put their fair moneyline at -333 (76.9%), so "
        "we select Bristol Bears to win and play Bristol Bears -11.5 on the handicap at -108."
    ),

    # --- Volleyball (top 5 by confidence) ----------------------------------
    "vb-civitanova-padova": (
        "Cucine Lube Civitanova host Pallavolo Padova on Sunday 25 October at 18:00 local in Italian SuperLega Credem Banca "
        "Round 2 after sweeping their Round 1 opener 3-0 in sets (78 points won, 65 conceded, 3 league points). Padova were "
        "swept 0-3 in Round 1, scoring just 56 points while conceding 75 (0 league points), and LegaVolley's calendar lists no "
        "injury absences for Sunday's clash. Civitanova's fair moneyline is -614 (86.0%), shorter than -250, so we select "
        "Cucine Lube Civitanova to win and take the in-band Cucine Lube Civitanova -1.5 set handicap at -213."
    ),
    "vb-piacenza-modena": (
        "Gas Sales Bluenergy Piacenza welcome Valsa Group Modena on Sunday 25 October at 18:00 local in SuperLega Round 2 sitting "
        "second on the table after a 3-0 Round 1 sweep (75 points won, 56 conceded, 3 league points). Modena lost their opener "
        "0-3 (61 points won, 75 conceded, 0 points), and LegaVolley publishes no injury scratches for either squad. With "
        "Piacenza's fair moneyline at -614 (86.0%), our selection is Gas Sales Bluenergy Piacenza to win paired with the in-band "
        "Gas Sales Bluenergy Piacenza -1.5 set handicap at -213."
    ),
    "vb-monza-verona": (
        "Vero Volley Monza host Rana Verona on Sunday 25 October at 18:00 local in SuperLega Round 2 after taking a set and "
        "scoring 91 points against 94 conceded in their 1-3 Round 1 loss to Tinet Prata di Pordenone. Verona were swept 0-3 in "
        "their opener (65 points won, 78 conceded), and no player injury exclusions are listed on LegaVolley's schedule page. "
        "Monza's stronger Round 1 point ratio (49.2% vs 45.5%) and home court price them at -213 (68.0%, medium confidence), "
        "giving us an in-band moneyline selection on Vero Volley Monza to win."
    ),
    "vb-milano-cuneo": (
        "Allianz Milano host Acqua Sant'Anna Cuneo on Sunday 25 October at 19:00 local in SuperLega Round 2 after suffering the "
        "heaviest defeat of Round 1, a 0-3 sweep against Cisterna Volley in which Milano scored 56 points and conceded 79 (0 "
        "points). Cuneo pushed reigning powerhouse Perugia to five sets in Round 1 (2-3, 95 points won vs 114 conceded, 1 league "
        "point), with no injury scratches reported by LegaVolley. We select Acqua Sant'Anna Cuneo to win at -189 (65.4%, medium "
        "confidence)."
    ),
    "vb-perugia-prata": (
        "Sir Susa Scai Perugia host Tinet Prata di Pordenone on Sunday 25 October at 18:00 local in SuperLega Round 2 after "
        "prevailing 3-2 in Round 1 over Cuneo while scoring 114 total points and conceding 95 (2 league points). Newly promoted "
        "Prata di Pordenone beat Monza 3-1 in their opener (94 points won, 91 conceded, 3 league points), and neither side "
        "carries an injury exclusion on LegaVolley's fixture hub. Perugia's superior 54.5% point share and PalaBarton home edge "
        "make our selection Sir Susa Scai Perugia to win at -137 (57.8%, medium confidence)."
    ),

    # --- Gaelic Sports (both priced county finals) -------------------------
    "gaa-waterford-sfc": (
        "Rathgormack and The Nire contest the Waterford Senior Football Championship Final at Cappoquin Logistics Fraher Field, "
        "Dungarvan on Sunday 25 October at 14:30 with Killian O'Sullivan appointed referee and no injury withdrawals listed on "
        "Waterford GAA's fixture sheet. In the county semi-finals, The Nire held Abbeyside-Ballinacourty to just five points in "
        "a 0-12 to 0-5 victory (+7 margin), whereas Rathgormack edged Gaultier 1-14 to 0-15 (17-15, +2 margin). Driven by The "
        "Nire's seven-point defensive shutout, we select The Nire to win at -216 (68.3%, medium confidence) and The Nire -2.5 "
        "points at -113."
    ),
    "gaa-cork-psfc": (
        "St Finbarr's and Nemo Rangers meet in the Cork Premier Senior Football Championship Final at SuperValu Páirc Uí Chaoimh "
        "on Sunday 25 October at 16:00 under referee David Murnane, with no injury withdrawals posted by Cork GAA. Both clubs "
        "won their semi-finals by identical 18-16 margins on 12 October: St Finbarr's defeated Clonakilty 2-12 to 0-16 while "
        "Nemo Rangers beat Carrigaline 1-15 to 0-16. With St Finbarr's finding two semi-final goals to Nemo's one, our selection "
        "is St Finbarr's to win at -109 (52.2%, low confidence) and Over 31.5 total points at -117."
    ),
}


def main():
    with open(os.path.join(DATA, "lines.json")) as f:
        records = json.load(f)["records"]
    by_id = {r["id"]: r for r in records}

    by_sport = {}
    for r in records:
        if r["priced"]:
            by_sport.setdefault(r["sport"], []).append(r)
    selected_ids = []
    for sport, rows in sorted(by_sport.items()):
        rows_sorted = sorted(rows, key=lambda r: (-r["winner_prob"], r["id"]))
        for r in rows_sorted[:5]:
            selected_ids.append(r["id"])

    missing = [fid for fid in selected_ids if fid not in PROSE]
    if missing:
        raise RuntimeError(f"Missing prose for selected top-5 fixture IDs: {missing}")

    predictions = []
    seen_openings = set()
    seen_sentences = set()
    for fid in selected_ids:
        r = by_id[fid]
        text = PROSE[fid].strip()
        words = text.split()
        wc = len(words)
        if wc < 30:
            raise ValueError(f"{fid}: prediction has only {wc} words (<30)")
        m = FORBIDDEN.search(text)
        if m:
            raise ValueError(f"{fid}: forbidden word '{m.group(0)}' found in prediction")
        opening = " ".join(words[:5]).lower()
        if opening in seen_openings:
            raise ValueError(f"{fid}: duplicate 5-word opening '{opening}'")
        seen_openings.add(opening)
        for sent in [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]:
            if sent in seen_sentences:
                raise ValueError(f"{fid}: duplicate sentence '{sent}'")
            seen_sentences.add(sent)

        predictions.append({
            "fixture_id": fid,
            "sport": r["sport"],
            "competition": r["competition"],
            "matchup": f"{r['away']} @ {r['home']}" if r.get("away") else r["home"],
            "time_display": r["time_display"],
            "venue": r.get("venue"),
            "winner_pick": r["winner_pick"],
            "winner_prob": r["winner_prob"],
            "winner_fair_american": r["winner_fair_american"],
            "winner_in_band": r["winner_in_band"],
            "confidence": r["confidence"],
            "actionable_market": r["actionable_market"],
            "actionable_selection": r["actionable_selection"],
            "actionable_odds": r["actionable_odds"],
            "actionable_in_band": r["actionable_in_band"],
            "word_count": wc,
            "prediction_text": text,
            "official_source_url": r["official_source_url"],
            "stats_source_url": r["stats_source_url"],
            "injury_source_url": r.get("injury_source_url"),
        })

    sport_counts = {}
    for p in predictions:
        sport_counts[p["sport"]] = sport_counts.get(p["sport"], 0) + 1

    out = {
        "generated_utc": "2026-10-23T21:40:00Z",
        "session": "arena/9c5af337-olbg2",
        "total_predictions": len(predictions),
        "sports_covered": len(sport_counts),
        "per_sport_counts": sport_counts,
        "min_word_count": min(p["word_count"] for p in predictions),
        "max_word_count": max(p["word_count"] for p in predictions),
        "forbidden_word_hits": 0,
        "predictions": predictions,
    }
    with open(os.path.join(DATA, "predictions.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"horizon_predictions: total={len(predictions)} sports={len(sport_counts)} "
          f"min_words={out['min_word_count']} max_words={out['max_word_count']}")


if __name__ == "__main__":
    main()
