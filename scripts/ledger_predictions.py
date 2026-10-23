#!/usr/bin/env python3
"""Ledger desk: attach hand-written previews to selected originated prices + build flags.

Every factual claim in the prose (records, goals, points, leaders, venues, dates,
scores) comes from an official page read first-hand on 2026-10-23 and is traceable via
data/ledger/inputs.json + data/ledger/sources.json. No injury is asserted anywhere:
no official injury or availability list was readable today (flag LG-INJ1).
Internal terminology is kept out of the reader-facing preview text.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINES = json.loads((ROOT / "data/ledger/lines.json").read_text())
MATCH = {m["id"]: m for m in LINES["matches"]}

# (fixture, market, selection) -> preview text. Selection is named explicitly in each text.
PROSE = {
 ("NHL-2026020170", "Match winner (2-way)", "Boston Bruins"):
  "Take the Boston Bruins to beat San Jose at TD Garden. Boston have made an 8-2-1 start while scoring 42 goals and conceding only 22 in eleven games, the stingiest defensive figures involved in this fixture, and David Pastrnak leads the hosts with six goals and ten assists. Jeremy Swayman already has six wins behind that structure, whereas the Sharks, lively as Macklin Celebrini has been with five goals and nine assists, have leaked 36 goals in their eleven outings. On home ice that two-way gap makes Boston the clear match-winner selection.",
 ("NHL-2026020169", "Match winner (2-way)", "New Jersey Devils"):
  "Back the New Jersey Devils to beat the Los Angeles Kings at the Prudential Center. New Jersey sit at 6-4-0 with 33 goals scored against 31 conceded, and Jack Hughes has been pulling the strings with eight assists, while Los Angeles arrive at 2-4-2 having managed just 20 goals in eight games. Artemi Panarin's six goals give the Kings one obvious threat, but their scoring depth has been thin and Darcy Kuemper has only two wins so far. With home ice and the healthier spread of production, New Jersey are the match-winner pick.",
 ("NHL-2026020174", "Match winner (2-way)", "Vegas Golden Knights"):
  "Side with the Vegas Golden Knights to win on the road against Columbus at Nationwide Arena. Vegas have piled up 45 goals in twelve games on the way to an 8-4-0 record, Jack Eichel has thirteen assists and Mark Stone eight goals, and that firepower meets a Blue Jackets side bottoming out at 3-5-0 with only 19 goals scored in eight games. Kent Johnson's four goals lead a Columbus attack that has simply not kept pace, so even away from home Vegas earn the match-winner vote.",
 ("NHL-2026020176", "Match winner (2-way)", "Edmonton Oilers"):
  "Go with the Edmonton Oilers to beat Toronto at Rogers Place in the glamour tie of the night. Edmonton own the league's hottest start at 8-1-1, 46 goals scored in ten games, Connor McDavid has an eye-watering 23 assists already and Leon Draisaitl has struck ten times. Toronto bring real quality of their own through Auston Matthews, eight goals and ten assists, but the Maple Leafs have shipped 38 goals in twelve and that looseness is dangerous against this Edmonton top end. The Oilers are the match-winner selection.",
 ("NHL-2026020171", "Handicap +1.5", "Ottawa Senators"):
  "Take the Ottawa Senators with the +1.5 goal start at home to the New York Rangers. These two are hard to split on the raw numbers, Ottawa going 7-4-0 with 29 scored and 30 conceded while the Rangers are 7-4-1 with 37 and 29, and Linus Ullmark's seven wins show how often the Senators keep games tight late. Tim Stutzle, seven goals and eight assists, gives Ottawa enough punch to stay close even if Adam Fox, fourteen assists, runs the Rangers' breakouts. A one-goal margin either way is the likeliest script, which is exactly what the +1.5 handicap is for.",
 ("NHL-2026020177", "Handicap +1.5", "Utah Mammoth"):
  "Take the Utah Mammoth receiving +1.5 goals at home against Tampa Bay at the Delta Center. Tampa's 7-2-0 record and tight 23 goals conceded mark them out as favourites, yet Utah have been scoring freely themselves with 41 goals in eleven games and Nick Schmaltz has seven of them, matching Brandon Hagel's tally for the Lightning. Utah are 7-4-0 rather than a side being blown out weekly, and home ice in what shapes as a one-goal game makes the +1.5 start the sensible side of this handicap.",
 ("NHL-2026020179", "Handicap +1.5", "Minnesota Wild"):
  "Take the Minnesota Wild with +1.5 goals for the trip to Seattle. Minnesota have conceded only 27 goals in eleven games, Kirill Kaprizov has eleven goals, Quinn Hughes has eleven assists and Jesper Wallstedt has six wins, so this is a well-organised 6-3-2 team that rarely gets run out of a building. Seattle are a strong 7-3-1 at Climate Pledge Arena and Frederick Gaudreau's six goals lead their scoring, but the Kraken have also allowed 37, giving Minnesota routes to keep this within a goal and land the +1.5 handicap.",
 ("MLB-849805", "Match winner (2-way)", "Milwaukee Brewers"):
  "Back the Milwaukee Brewers to win Game 1 of the World Series against Tampa Bay at American Family Field tonight. Milwaukee produced the best regular-season record of the two finalists at 103-59, scored 832 runs while allowing only 618, went 55-26 at this ballpark and closed the season 8-2 in their last ten on a five-game winning streak. Tampa Bay were excellent too at 98-64 with 736 runs scored, but they were a modest 43-38 on the road, so the opening night edge sits with the Brewers as the match-winner selection.",
 ("MLB-849805", "Handicap +1.5", "Milwaukee Brewers"):
  "For the safer route into tonight's opener, take the Milwaukee Brewers on the +1.5 run line against Tampa Bay. Milwaukee's season profile is built for this bet: 103 wins, a plus-214 run differential from 832 scored against 618 allowed, and a 55-26 home record at American Family Field. Tampa Bay's own differential was a healthy plus-86, which is precisely why a tight opener would surprise nobody, and the +1.5 cushion covers the Brewers in both a home win and the one-run defeat scenario. That breadth of cover makes it this desk's strongest baseball angle.",
 ("EL-R8-04", "Match winner", "Panathinaikos AKTOR Athens"):
  "Take Panathinaikos to beat Olimpia Milan in Athens in Round 8. The hosts top the standings picture used here at 6-1, scoring 613 points and conceding a lean 517 through seven games, a plus-96 differential that is the best of the twenty clubs. Milan, by contrast, are 1-6 with 585 scored against 648 conceded, and trips to the Telekom Center Athens rarely fix a defence leaking at that rate. Everything in the seven-round body of work points one way, so Panathinaikos are the match-winner selection, albeit at a very short price.",
 ("EL-R8-06", "Match winner", "Real Madrid"):
  "Back Real Madrid to win away at Baskonia in Vitoria-Gasteiz. Madrid have been the competition's most explosive attack across the first seven rounds with 667 points scored, and even at 4-3 their plus-37 differential towers over a Baskonia side sitting 1-6 after conceding 649 points, one of the worst defensive totals in the standings. Baskonia's 583 points scored shows they can trade baskets for stretches, but sustaining that against Madrid's depth for forty minutes is a different task. Real Madrid are the match-winner pick on the road.",
 ("EL-R8-03", "Match winner", "Crvena Zvezda Meridianbet Belgrade"):
  "Side with Crvena Zvezda to beat Maccabi Tel Aviv at the Belgrade Arena. Zvezda have quietly built a 4-3 record on defence, conceding just 532 points in seven games, while Maccabi are 2-5 and have given up 653, one of the leakiest marks in the league. Maccabi's 608 scored means they will have their runs, yet on the road against this half-court defence those runs have tended to dry up. Crvena Zvezda get the match-winner vote at home.",
 ("EL-R8-01", "Match winner", "Dubai Basketball"):
  "Go with Dubai Basketball to beat Paris at the Coca-Cola Arena. Dubai are 5-2 with 597 points scored and 584 conceded, a steady two-way profile, whereas Paris have managed one win from six while scoring only 504 points. That scoring shortfall is the heart of this pick: Paris have repeatedly stalled in the half court, and Dubai at home have shown they can sit on a lead once ahead. Nothing in the first seven rounds suggests an away turnaround here, so Dubai are the match-winner selection.",
 ("EL-R8-08", "Match winner", "Hapoel IBI Tel Aviv"):
  "Take Hapoel Tel Aviv to beat Anadolu Efes in Botevgrad, the Bulgarian base listed for this Round 8 fixture. Hapoel have been one of the early-season pace-setters at 5-2, pouring in 630 points across seven games, and they meet an Efes side stuck at 3-4 with a negative differential after conceding 590. Efes remain a name to respect, but their 581 points scored is mid-pack production and Hapoel's tempo has stretched better defences than this. At a fair rather than prohibitive price, Hapoel are the match-winner selection.",
 ("RLWC-R2-1", "Match winner (2-way)", "Samoa"):
  "Back Samoa to beat Papua New Guinea in Port Moresby on Saturday. Samoa opened their World Cup by dismantling France 78-4 in Sydney, comfortably the most emphatic result of Round 1, while Papua New Guinea gave up eighteen points in beating Lebanon 42-18 at this same Santos National Football Stadium. Home surroundings will lift the Kumuls and one game's evidence should always be handled gently at a tournament this young, but the sheer scale of Samoa's first outing marks them out. Samoa are the match-winner selection.",
 ("RLWC-R2-2", "Match winner (2-way)", "England"):
  "Take England to beat France in Perth. England were beaten 30-12 by a powerful Tonga outfit in Round 1 yet still scored twelve points against elite opposition, while France endured a chastening 78-4 defeat by Samoa and conceded tries in clusters all afternoon. At HBF Park, where England have just played, that defensive fragility is the clearest signal this fixture offers. One match apiece is a thin evidence base, as this desk keeps stressing, but the gap between those two opening performances makes England the match-winner pick.",
 ("RLWC-R2-3", "Match winner (2-way)", "New Zealand"):
  "Go with New Zealand to beat the Cook Islands in Christchurch on Sunday. New Zealand pushed Australia all the way before going down 24-22 in the tournament opener, a level of resistance nobody else in Round 1 had to offer the favourites, whereas the Cook Islands were beaten 40-12 by Fiji in Newcastle. Playing at One NZ Stadium in front of a home crowd only strengthens the case. The Kiwis are taken as the match-winner selection, with the usual caution that every side here has one World Cup match in the legs.",
 ("RLWC-R2-4", "Match winner (2-way)", "Fiji"):
  "In the bravest call on this page, take Fiji to beat Australia in Brisbane. The numbers behind it are narrow and come with a health warning: Fiji scored forty and conceded twelve against the Cook Islands, while Australia were held to a 24-22 squeak by New Zealand, so on one game each the Fijian differential reads better. Australia's pedigree obviously dwarfs that single-match snapshot and most neutrals will disagree, which is why the price rather than certainty carries this. If you follow the published figures to their conclusion, Fiji are the match-winner selection.",
 ("SN-87883228", "Match winner", "Mark Selby"):
  "Back Mark Selby to beat Jimmy White when the International Championship resumes on 30 October. Selby sits fifth on the world ranking list with a little over a million pounds in ranking money and, just as tellingly, he tops the one-year list published alongside it, the surest sign of current winning habits on tour. White remains a beloved draw and a dangerous scorer in bursts, but he does not appear on the top-36 ranking table this desk could read. Over any sensible distance, Selby is the match-winner selection.",
 ("SN-9b7fcc94", "Match winner", "Shaun Murphy"):
  "Take Shaun Murphy to beat Mitchell Mann in the International Championship on 30 October. Murphy, seventh in the world with close to nine hundred thousand pounds in ranking money, also features in the top ten of the one-year list, which speaks to a season already gathering momentum. Mann is not listed in the top thirty-six of the ranking table available to this desk, and that gulf in tour earnings usually reflects a gulf in scoring power and safety play alike. Shaun Murphy is the clear match-winner selection.",
 ("SN-e6719e69", "Match winner", "Kyren Wilson"):
  "Side with Kyren Wilson to beat Sam Craigie in Saturday's Northern Ireland Open semi-final in Belfast. Wilson, ninth on the world ranking list with more than seven hundred thousand pounds banked, has already come through the week's draw to reach the last four, and the tour's own reports bannered his run to the semis alongside Craigie's. Craigie deserves real credit for getting this far, yet he sits outside the top-36 ranking table this desk could read, and Wilson's all-round scoring and safety game is the more reliable package. Kyren Wilson is the match-winner selection.",
 ("SN-41c153a5", "Match winner", "Zhou Yuelong"):
  "Go with Zhou Yuelong to beat Liam Davies when they meet on 30 October. Zhou has established himself just outside the elite bracket at seventeenth in the world with around three hundred and sixty thousand pounds in ranking money, a level of week-to-week consistency that Davies, absent from the top-36 table this desk could read, is still chasing. Davies did appear on the Home Nations bonus list published by the tour, so he is not without recent encouragement, but Zhou's heavier scoring should tell. Zhou Yuelong is the match-winner selection.",
 ("GO-GENESIS", "Outright winner (36 holes completed)", "Antoine ROZNER"):
  "If you want one name from the top of the Genesis Championship board, take Antoine Rozner to win the tournament from here. Rozner shares the halfway lead at ten under par after rounds of 67 and 65, the low round of Friday among the leading pair, and he holds a three-shot cushion over the four players bunched at seven under. Halfway leaders convert often enough to respect, and nobody in this field is currently closer. With 36 holes left this stays an outright speculation rather than a confident call, but Rozner is the selection.",
 ("MR-USGP", "Race winner — United States GP (R18)", "Kimi Antonelli (Mercedes)"):
  "For an interest in Sunday's United States Grand Prix, take Kimi Antonelli to win the race. Antonelli leads the championship by a commanding margin on 340 points to team-mate George Russell's 238, and the early-season record this desk could read in full shows him winning in China, Japan, Miami, Canada and Monaco. No practice or qualifying running had been published on the pages checked, so this is strictly a small-stakes outright based on season-long supremacy rather than anything seen this weekend. On that basis Antonelli is the race-winner selection.",
 ("HB-07", "Match winner (2-way)", "Kosovo"):
  "Take Kosovo's women to beat Estonia again when the pair meet for the second time in two days in World Championship qualifying. Kosovo won Friday's first meeting 39-22, a seventeen-goal margin recorded on the European federation's own feed, and a gap of that size over sixty minutes usually reflects depth in every position rather than one hot goalkeeper. Turnarounds inside twenty-four hours do happen in handball, and a single result is all the evidence available here, so keep stakes sensible. On that evidence, Kosovo are the match-winner selection.",
 ("HB-04", "Match winner (2-way)", "MRK Sloga Doboj"):
  "Back MRK Sloga Doboj to beat Kur in the European Cup return on Saturday. These sides played on Friday and Sloga won 38-26 per the federation feed, pulling clear by twelve goals, and the schedule now flips the listing order for the second meeting a day later. Fatigue and rotation can compress margins in these quickfire double-headers, which is why this stays a low-key play built on one official result, but a twelve-goal win is hard evidence of a matchup problem for Kur. Sloga Doboj are the match-winner selection.",
}

preds = []
for (fid, market, selection), text in PROSE.items():
    row = next(s for s in LINES["selections"] if s["fixture"] == fid and s["market"] == market and s["selection"] == selection)
    words = len(text.split())
    assert words >= 30, (fid, words)
    low = text.lower()
    assert "model" not in low and "verif" not in low, fid
    m = MATCH[fid]
    preds.append({"fixture": fid, "sport": m["sport"], "competition": m["competition"], "date": m["date"],
                  "event": (f'{m["away"]} at {m["home"]}' if m.get("away") else m["home"]),
                  "market": market, "selection": selection, "prob": row["prob"], "american": row["american"],
                  "decimal": row["decimal"], "confidence": row["confidence"], "tier": row["tier"],
                  "in_band": row["in_band"], "text": text, "words": words,
                  "source_keys": m["source_keys"]})
preds.sort(key=lambda x: (x["sport"], -x["prob"]))

FLAGS = [
 ("LG-01", "OLBG discovery", "OLBG sport hubs read first-hand on 2026-10-23 served 'No tips found' with no event rows in fetched HTML. OLBG is used here for taxonomy, URL schema and market names only; every fixture comes from the official league/federation source linked on its row.", ["olbg-tips", "olbg-darts", "olbg-nhl"]),
 ("LG-BAND", "Brief maths", "The brief's two rules overlap: high confidence above 70% with a fair price no shorter than -250 can only both hold between 70.00% and 71.43% (-250 is exactly 71.43%). The site labels that strict window Tier A, prices above 70% but shorter than -250 Tier B, and the strongest remaining in-band prices Tier C, rather than quietly widening either rule.", []),
 ("LG-NH1", "Ice Hockey", "Calgary Flames goals for/against were cut off in the NHL Stats chunk read (record and point percentage only). Detroit at Calgary is published unpriced instead of estimated.", ["nhl-summary"]),
 ("LG-NH2", "Ice Hockey", "The NHL score feed embeds third-party bookmaker odds (its 'odds partners'). Those prices were ignored completely; every NHL price here is originated from goals data.", ["nhl-score23"]),
 ("LG-BK1", "Basketball", "The NBA live scoreboard JSON returned HTTP 500 on 2026-10-23. No NBA fixtures are published; basketball coverage is EuroLeague Round 8 only.", ["nba-cdn"]),
 ("LG-EL1", "Basketball", "The EuroLeague feed returns two clock times per game without a legend in the text served, and some teams show 6 games played against others' 7. Dates/times are stored 'as served', per-game rates are used throughout, and the margin/total standard deviations (13/18) are stated assumptions on the method page.", ["el-sched", "el-stand"]),
 ("LG-ML1", "Baseball", "Probable pitchers were not present in the MLB feeds read, and run rates use a two-team baseline built from the finalists' own runs scored (stated on each row). Game-by-game pitching matchups would normally move these prices.", ["mlb-sched", "mlb-al", "mlb-nl"]),
 ("LG-ML2", "Baseball", "World Series Game 6 (30 Oct) appeared only as a truncated chunk and Game 7 was not read in full, so only Games 1-5 are published.", ["mlb-sched"]),
 ("LG-RL1", "Rugby League", "Every nation has played one or two World Cup matches. On those differentials alone Fiji grade above Australia and New Zealand's line is flattered by a narrow loss; both rows are published as the data reads, capped at Medium, with this warning attached. The round-2 'positions' as served (for example two different 3rds) appear pool-relative and are quoted verbatim, not interpreted as an overall table.", ["rlwc-r1", "rlwc-r2"]),
 ("LG-RU1", "Rugby Union", "The PREM Rugby fixtures page served no fixture rows in fetched HTML and the URC fixtures URL returned 404. Rugby Union therefore has zero fixtures today rather than borrowed data from another desk.", ["prem-r4", "urc"]),
 ("LG-SN1", "Snooker", "The readable ranking table stops at 36th place (£198,500). Opponents below that line are priced using £198,500 as a ceiling, so favourite prices are floors and are labelled bounded; Liu Hongyu v Louis Heathcote (neither in top 36) is left unpriced. Match formats were not on the pages read, so no frame handicaps or totals are offered.", ["wst-rank", "wst-home"]),
 ("LG-TE1", "Tennis", "Quarter-final results were readable on the ATP scoreboard, but semi-final pairings could not be confirmed from the readable draw chunks. Completed quarter-finals are listed for the record and no tennis price is originated.", ["atp-scores", "atp-draw"]),
 ("LG-CR1", "Cricket", "No official table, ranking or results feed was read for these sides, so all 13 cricket fixtures are published without prices. Start times render in the viewer's timezone ('your time') and are stored verbatim; one venue is spelled 'Hnry Stadium' on the source page and is quoted as served.", ["ca-matches"]),
 ("LG-GO1", "Golf", "Only players at -4 or better appear in the leaderboard chunk read. Outright shares are normalised over those 16 players and are therefore upper bounds; the full weekend field would dilute them.", ["dpwt-lb"]),
 ("LG-MR1", "Motor Racing", "No practice, qualifying or grid information had been published on the Formula 1 pages read. United States GP outright shares follow championship points for the top ten only and are Low confidence by construction.", ["f1-cal", "f1-stand"]),
 ("LG-HB1", "Handball", "Only two of the fourteen 24 October fixtures involve a pairing with an official result from 23 October; only those two are priced, from that single result, at Low confidence. Both pairs also show the unusual pattern of the same clubs meeting on consecutive days with the home/away listing flipped, quoted as served.", ["ehf"]),
 ("LG-GA1", "Gaelic Sports", "OLBG splits 'Gaelic Football' (sport 25) from 'Hurling' (26), while the users brief says 'Gaelic Sports'. The only fixture on the GAA page read is the Shinty-Hurling International final, Ireland v Scotland in Cork; it is published under Gaelic Sports with this scope note and no price (no form data read).", ["gaa", "olbg-sitemap"]),
 ("LG-GH1", "Greyhounds", "The GBGB open-races page served its filter interface but no meetings, races or runners in fetched HTML. Greyhounds has zero fixtures rather than invented cards.", ["gbgb"]),
 ("LG-VB1", "Volleyball", "The CEV homepage served news only (Champions League Volley 2027 early rounds under way) with no fixture list. Volleyball has zero fixtures today.", ["cev"]),
 ("LG-DA1", "Darts", "pdc.tv/calendar served cookie-consent markup only and the OLBG darts hub served 'No tips found'. Darts has zero fixtures; OLBG's darts market guide (Win Match, Handicap, Total Legs, Total 180s) is documented on the OLBG page for when an official draw is readable.", ["pdc", "olbg-darts"]),
 ("LG-INJ1", "All sports", "No official injury, team-news or availability feed was readable for any fixture today. Previews therefore assert no injuries at all; late team news could move any of these prices.", []),
 ("LG-TZ1", "All sports", "NHL and MLB start times are UTC in their official feeds and are labelled as such. EuroLeague, EHF, NRL, WST, GAA and Cricket Australia times are stored exactly 'as served' because those pages render in a viewer-local zone or do not state one; no silent conversion is applied.", []),
 ("LG-REPO1", "Repository", "COORDINATION.md on main still contains leftover merge-conflict separator lines (around lines 3216-3628, tagged 'origin/main' and commit 140baf3). That file is the shared append-only board, so this session logs the defect here for the integration owner instead of rewriting other sessions' records.", []),
]

(ROOT / "data/ledger/predictions.json").write_text(json.dumps(
    {"meta": {"desk": "ledger", "generated_for": "2026-10-23", "predictions": len(preds),
              "min_words": min(p["words"] for p in preds)}, "predictions": preds}, indent=1, ensure_ascii=False))
(ROOT / "data/ledger/flagged.json").write_text(json.dumps(
    {"meta": {"desk": "ledger", "flags": len(FLAGS)},
     "flags": [{"id": i, "area": a, "detail": d, "source_keys": k} for i, a, d, k in FLAGS]}, indent=1, ensure_ascii=False))
print(f"predictions={len(preds)} min_words={min(p['words'] for p in preds)} flags={len(FLAGS)}")
from collections import Counter
print(Counter(p["sport"] for p in preds))
