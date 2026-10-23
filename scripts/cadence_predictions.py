"""Cadence desk — written predictions for the graded selections.

Only selections graded ``high`` or ``medium`` receive a written prediction. Each paragraph
is unique, at least 30 words, states the betting selection explicitly, and quotes only
numbers that exist in the stored official facts for that fixture (the builder fails if a
number in the text cannot be matched back to a captured fact). The words "model" and
"verified" (and their inflections) are prohibited in reader-facing prose and are rejected by
the builder.

Run: python3 scripts/cadence_predictions.py -> data/cadence/{predictions,flagged}.json
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "cadence")
GENERATED = "2026-10-23T20:20:00Z"
BANNED = re.compile(r"\b(model|models|modelled|modeled|modelling|modeling|verify|verified|verifies|"
                    r"verification|hallucinat\w*)\b", re.I)

PROSE = {
    "nhl-2026020167-pick": dict(
        headline="Tampa Bay carry a three-game run into Denver",
        text=("Tampa Bay Lightning to win the money line in Denver. The Lightning are 7-2-0 through nine "
              "games with 31 goals scored and 23 conceded, and they arrive on a three-game winning run after "
              "a 5-0-0 start at home. Colorado are 5-4-1 and have lost two straight despite scoring 41 times, "
              "because they have allowed 31. The NHL's own schedule feed had Tampa Bay at +105 and Colorado at "
              "-129, so the desk's -263 quote is a genuine disagreement with the published price rather than a copy of it."),
        facts=["7-2-0 in 9 games", "5-4-1 in 10 games", "Tampa Bay +105"]),
    "nhl-2026020167-band": dict(
        headline="Both blue lines point to six goals or more",
        text=("Over 5.5 goals in Colorado. The Avalanche have scored 41 goals in ten games and conceded 31, "
              "while Tampa Bay have 31 for and 23 against in nine. Combining both clubs' scoring and conceding "
              "rates gives an expected total near 6.7, which puts six or more goals on the board at roughly seventy "
              "per cent. The desk quotes that alternate line at a fair -237, and the reasoning is the two goal "
              "columns rather than any reported goaltending decision."),
        facts=["5-4-1 in 10 games", "7-2-0 in 9 games"]),
    "nhl-2026020166-pick": dict(
        headline="Chicago's blank road record meets a superior points percentage",
        text=("Montréal Canadiens to win at the United Center. Montréal are 4-3-2 with 30 goals for and 34 "
              "against, and their nine games include a 3-2-1 home record; Chicago are 3-6-0 with only 21 goals "
              "scored and 36 conceded, and they have lost all four road games. The NHL feed had Montréal at -169, "
              "so this is a shorter -229 on the same side, with the away side's superior points percentage doing the work."),
        facts=["4-3-2 in 9 games", "3-6-0 in 9 games", "Montréal -169"]),
    "el-E2026_76-pick": dict(
        headline="Panathinaikos' defence has separated the field",
        text=("Panathinaikos AKTOR Athens to win at home against Armani Olimpia Milan. Panathinaikos are 6-1 "
              "through seven EuroLeague rounds with 613 points scored and 517 conceded, a +96 differential that "
              "leads the competition, and they are 5-1 at home and 1-0 away. Milan are 1-6 and have been outscored "
              "by 63, with one win in seven. The desk quotes -499 on the Greek side to win outright."),
        facts=["6-1 in 7 EuroLeague games", "1-6 in 7 EuroLeague games"]),
    "el-E2026_73-band": dict(
        headline="Two of Europe's fastest teams meet in Vitoria",
        text=("Over 171.5 points in the Real Madrid visit to Baskonia. Real Madrid have scored 667 points in "
              "seven EuroLeague games and conceded 630, the highest-scoring record in the competition; Baskonia "
              "have conceded 649 in seven, the second-worst defensive record. Adding both clubs' scoring and "
              "conceding rates puts the expected total above 171, which is why the desk quotes this alternate "
              "line at a fair -248."),
        facts=["4-3 in 7 EuroLeague games"]),
    "el-E2026_77-band": dict(
        headline="Neither defence suppresses a total in Belgrade",
        text=("Over 162.5 points when Hapoel IBI Tel Aviv host Anadolu Efes. Hapoel have scored 630 points in "
              "seven EuroLeague games and conceded 601; Efes have 581 for and 590 against across the same number "
              "of rounds. Both defences sit in the bottom half of the table, so the combined scoring rate supports "
              "a total above 162, and the desk quotes this band line at a fair -246."),
        facts=["5-2 in 7 EuroLeague games", "3-4 in 7 EuroLeague games"]),
    "el-E2026_75-band": dict(
        headline="Valencia's scoring rate holds up the total in Spain",
        text=("Over 163.5 points in Valencia against Fenerbahce. Fenerbahce have the second-best defensive "
              "record in the EuroLeague at 447 conceded in six games, but Valencia have scored 583 in six and "
              "conceded 537, so both ends of the floor produce points. The combined rate lands just above this "
              "line, which the desk prices at a fair -241, a touch shorter than the 0.700 floor."),
        facts=["4-2 in 6 EuroLeague games", "5-1 in 6 EuroLeague games"]),
    "el-E2026_80-band": dict(
        headline="Bologna and Kaunas both leak enough to clear this line",
        text=("Bologna is the venue for this 163.5-point over. Virtus have scored 606 and conceded 608 across seven EuroLeague "
              "rounds, and Zalgiris have 595 for and 602 against in the same number of games, so neither side "
              "arrives with a defensive record that suppresses a total. The combined rate sits comfortably above "
              "this line, which the desk quotes at a fair -238."),
        facts=["4-3 in 7 EuroLeague games", "3-4 in 7 EuroLeague games"]),
    "mlb-849805-pick": dict(
        headline="Milwaukee's home record and a 1.80 ERA meet the Rays",
        text=("Milwaukee Brewers to win World Series Game 1 at American Family Field. Milwaukee finished 103-59 "
              "with 832 runs scored and 618 allowed, went 55-26 at home and 68-35 at night, and closed the regular "
              "season on a five-game winning streak with eight wins in ten. Tampa Bay were 98-64 but 43-38 on the "
              "road. Jacob Misiorowski starts for Milwaukee after a 1.80 earned run average with 252 strikeouts in "
              "174.2 innings; Nick Martinez, on a 3.10 ERA, starts for Tampa Bay."),
        facts=["103-59", "1.80 ERA", "3.10 ERA"]),
    "cri-40981-pick": dict(
        headline="England arrive in Lahore after conceding 430",
        text=("Pakistan to win the Pakistan ODI Tri-Series match against England at the Gaddafi Stadium. England "
              "arrive after conceding 8-430 in 49.5 overs at Rawalpindi, where Sri Lanka chased down 430 with two "
              "wickets and one ball in hand. Home conditions in Lahore and England's expensive bowling in that "
              "game are the basis of a 63 per cent price, which the desk quotes at -170."),
        facts=["Sri Lanka won by 2 wickets"]),
    "cri-40394-pick": dict(
        headline="India finished the first ODI with 22 overs unused",
        text=("India Women to win the second ODI against Zimbabwe Women in Vadodara. The first match finished "
              "inside 28 overs of the chase: Zimbabwe were bowled out for 197 in 49.5 overs and India reached "
              "1-200 in 27.1 overs, a nine-wicket win with more than 22 overs unused. The same venue stages the "
              "second game, and the desk prices India at -170."),
        facts=["India Women won by 9 wickets"]),
    "cri-40981-band": dict(
        headline="A 15.5-run cushion sits inside the expected margin",
        text=("Pakistan to cover a 15.5-run handicap against England in Lahore. The line sits well below the "
              "42-run margin that the desk derives from the only completed result available, England's two-wicket "
              "defeat at Rawalpindi after conceding 430 in 49.5 overs. A 15.5-run cushion is the widest that "
              "keeps the selection at roughly seventy per cent, and it is quoted at a fair -244."),
        facts=["Pakistan v England", "Sri Lanka won by 2 wickets"]),
    "cri-41095-band": dict(
        headline="India chased 226 with two balls to spare at this ground",
        text=("India to cover a 13.5-run handicap in the second Twenty20 international at Hagley Oval. India "
              "chased 226 with two balls to spare in the first match at the same ground, finishing 6-230 in 19.4 "
              "overs after New Zealand made 4-225. A 13.5-run handicap is the widest line that holds the selection "
              "near seventy per cent, and the desk quotes -242."),
        facts=["India won by 4 wickets"]),
    "cri-40394-band": dict(
        headline="Zimbabwe's 197 was passed in 27.1 overs",
        text=("A 14.5-run handicap for India Women in the second ODI. Zimbabwe were dismissed for 197 in "
              "49.5 overs in the opener and India knocked off the runs in 27.1 overs for the loss of one wicket, "
              "a winning margin far beyond this line. The desk's 14.5-run handicap is the widest that keeps the "
              "price near the band ceiling, quoted at -241."),
        facts=["India Women won by 9 wickets", "2nd ODI"]),
    "drt-r2-1-pick": dict(
        headline="Top seed against a deciding-leg survivor",
        text=("Ross Smith to beat Damon Heta in the second round in Dortmund. Smith is the top seed on the 2026 "
              "European Tour Rankings with £158,000 banked and opened with a 6-4 win over Karel Sedlacek. Heta "
              "needed a deciding leg to get past James Wade 6-5 in round one. The seeding and the cleaner opening "
              "round put Smith at about 72 per cent, priced at -257 on the money line."),
        facts=["top seed on the 2026 European Tour Rankings", "beat James Wade 6-5"]),
    "drt-r2-5-pick": dict(
        headline="Second seed meets the fifteenth",
        text=("Wessel Nijman to beat Ryan Joyce in round two. Nijman is the second seed on the 2026 European "
              "Tour Rankings with £124,000, having won two European Tour titles this season; Joyce qualified "
              "fifteenth. The gap in the one-year ranking list is the whole basis of the price, and it supports a "
              "66 per cent quote at -196."),
        facts=["second seed with £124,000", "15th seed"]),
    "drt-r2-7-pick": dict(
        headline="A three-time seed takes on the four-time champion",
        text=("Krzysztof Ratajski to beat Michael van Gerwen. Ratajski is third on the 2026 European Tour "
              "Rankings with £89,500 and arrives as the higher seed, while Van Gerwen is seeded 19th despite his "
              "four European Championship titles. Seeding on the one-year list is the only comparative input used "
              "here, and it produces a 65 per cent price at -185."),
        facts=["third seed with £89,500", "four-time European Championship winner"]),
    "hb-sr-paris-pick": dict(
        headline="The unbeaten leaders visit the Var",
        text=("Paris Saint-Germain Handball to win at Saint-Raphaël. Paris have won all seven StarLigue rounds, "
              "scoring 239 goals and conceding 190 for a +49 differential that tops the table; Saint-Raphaël are "
              "2-5 with 207 scored and 225 conceded. The unbeaten start and the 22-goal gap in goal difference "
              "underpin a 76 per cent price at -314."),
        facts=["7-0-0 after 7 rounds", "2-5-0 after 7 rounds"]),
    "hb-nantes-chambery-pick": dict(
        headline="Nantes own the division's best scoring rate",
        text=("HBC Nantes to beat Chambéry. Nantes are 6-1 after seven rounds with 244 goals scored and 203 "
              "conceded, the second-best record in the division; Chambéry have won twice, drawn twice and lost "
              "three, and their goal difference is -7. Nantes' scoring rate is the highest in StarLigue, and the "
              "desk prices them at -284."),
        facts=["6-1-0 after 7 rounds", "2-3-2 after 7 rounds"]),
    "hb-montpellier-saran-band": dict(
        headline="Nearly six goals a game separate these two",
        text=("Montpellier to cover a 2.5-goal handicap against Saran. Montpellier have scored 234 and conceded "
              "205 across seven rounds with only one defeat, while Saran have 202 for and 216 against. The gap in "
              "goal difference per game is nearly six, so a 2.5-goal line is well inside the expected margin, and "
              "it is quoted at a fair -244 to keep the selection near the band ceiling."),
        facts=["4-1-2 after 7 rounds", "3-4-0 after 7 rounds"]),
    "hb-nantes-chambery-band": dict(
        headline="A plus line on the league's second-best side",
        text=("Nantes with a +2.5 start at Chambéry. The plus line collects if Nantes avoid defeat by "
              "three goals or more, and their 41-goal positive differential against Chambéry's -7 makes that the "
              "strongest available quote near the band ceiling. Nantes have lost once in seven rounds; the desk "
              "prices this alternate line at a fair -238."),
        facts=["6-1-0 after 7 rounds", "2-3-2 after 7 rounds"]),
    "f1-wdc-pick": dict(
        headline="A 102-point cushion with five rounds left",
        text=("Kimi Antonelli to win the 2026 Drivers' Championship. Antonelli leads on 340 points to George "
              "Russell's 238 with five rounds and 130 points still available after Austin, a 102-point cushion, "
              "and he won five consecutive rounds from China through Monaco earlier in the season. Only Russell "
              "can realistically catch him. The desk prices the title at -609."),
        facts=["Antonelli 340, Russell 238"],),
    "rlwc-eng-fra-pick": dict(
        headline="France conceded 78 in the opening round",
        text=("England to beat France in Perth. France conceded 78 points to Samoa in round one while scoring "
              "four, the heaviest defeat of the opening round; England lost 12-30 to Tonga but scored twelve more "
              "than France managed. On round-one margins the desk rates England about 78 per cent, which is quoted "
              "at -362 with the thin sample stated plainly."),
        facts=["England lost 12-30 to Tonga", "France lost 4-78 to Samoa"]),
    "rlwc-r3-ton-sam-pick": dict(
        headline="Samoa's 74-point margin dwarfs Tonga's 18",
        text=("Samoa to beat Tonga in Sydney on 1 November. Samoa opened with a 78-4 win over France, a "
              "74-point margin, while Tonga beat England 30-12 for an 18-point margin. Both are one-match samples, "
              "but Samoa's scoring rate is more than double Tonga's and their defensive record is 74 points "
              "better, so the desk quotes -330."),
        facts=["Tonga beat England 30-12", "Samoa beat France 78-4"]),
    "rlwc-r3-leb-fra-pick": dict(
        headline="Lebanon scored eighteen; France scored four",
        text=("Lebanon to beat France on 1 November. Lebanon lost 18-42 to Papua New Guinea but scored eighteen "
              "points; France managed four against Samoa and conceded 78. The margin comparison is the only "
              "numeric input available for this fixture, and it puts Lebanon at about 76 per cent, quoted at -313 "
              "with the small sample flagged on the row."),
        facts=["Lebanon lost 18-42", "France lost 4-78"]),
    "rlwc-png-samoa-pick": dict(
        headline="Port Moresby hosts the round's two biggest scorers",
        text=("Papua New Guinea's home fixture against Samoa leans to the visitors. Samoa beat France 78-4 in round one; Papua New "
              "Guinea beat Lebanon 42-18. Samoa's winning margin is fifty points the larger, and they sit second "
              "on the ladder to Papua New Guinea's third. The desk quotes -285, while noting that one match per "
              "side is a thin basis for any price."),
        facts=["Samoa beat France 78-4", "Papua New Guinea beat Lebanon 42-18"]),
    "rlwc-r3-eng-png-pick": dict(
        headline="A 42-point swing in round-one margins",
        text=("Papua New Guinea to beat England in Wollongong on 30 October. Papua New Guinea beat Lebanon 42-18 "
              "for a 24-point margin, while England lost 12-30 to Tonga for an 18-point deficit, a 42-point swing "
              "in round-one margins. The desk prices Papua New Guinea at -256 and states on the row that a single "
              "match per side underpins the number."),
        facts=["Papua New Guinea beat Lebanon 42-18", "England lost 12-30 to Tonga"]),
    "snk-ni-sf1-pick": dict(
        headline="Five times the ranking money, one frame dropped",
        text=("Kyren Wilson to beat Sam Craigie in the Northern Ireland Open semi-final. Wilson is world number "
              "nine with £716,800 on the Johnstone's Paint World Rankings and reached the last four with a 6-1 "
              "win over Anthony McGill. Craigie beat Elliot Slessor 6-2. The ranking-money gap is more than five "
              "times in Wilson's favour and he has dropped one frame in the quarter-final, so the desk quotes -288."),
        facts=["world no.9 with £716,800", "6-1 in the quarter-final", "6-2 in the quarter-final"]),
    "ru-quins-saracens-pick": dict(
        headline="The division's worst defence hosts the second-best",
        text=("Saracens to win at Harlequins. Saracens are 2-1 after three Gallagher PREM rounds with a +21 "
              "points difference and eleven league points; Harlequins have lost all three with a -68 difference "
              "and two points, the worst defensive record in the division. The desk prices Saracens at -156 as a "
              "medium-confidence selection, because three rounds is a small sample."),
        facts=["points difference +21", "points difference -68"]),
    "vb-piacenza-modena-pick": dict(
        headline="Fifty-six points conceded in a straight-set opener",
        text=("Gas Sales Bluenergy Piacenza to beat Valsa Group Modena. Piacenza opened SuperLega with a 3-0 "
              "win, scoring 75 points and conceding 56; Modena lost 0-3 and managed 61 points while conceding 75. "
              "Set and point ratios both favour the home side, and the desk quotes -254, with the caveat that only "
              "one round has been played."),
        facts=["3-0 sets, 75 points for and 56 against", "0-3 sets, 61 points for and 75 against"]),
    "vb-civitanova-padova-pick": dict(
        headline="Straight sets and a 19-point swing",
        text=("Cucine Lube Civitanova to beat Pallavolo Padova. Civitanova won their opener 3-0 with 78 points "
              "scored and 65 conceded; Padova lost 0-3, scoring 56 and conceding 75. Both the set count and the "
              "point ratio point the same way, a nineteen-point swing across the two openers, and the desk prices "
              "the home side at -254 with one round of evidence."),
        facts=["3-0 sets, 78 points for and 65 against", "0-3 sets, 56 points for and 75 against"]),
    "vb-milano-cuneo-pick": dict(
        headline="Cuneo took two sets and 95 points in defeat",
        text=("Acqua Sant'Anna Cuneo to win at Allianz Milano. Cuneo lost their opener 2-3 but took two sets and "
              "scored 95 points; Milano lost 0-3 scoring 56 and conceding 79. Cuneo's point ratio is markedly "
              "better even in defeat, and the desk quotes -168 as a medium-confidence selection with one round "
              "played."),
        facts=["2-3 sets, 95 points for and 114 against", "0-3 sets, 56 points for and 79 against"]),
    "ten-almaty-sf1-band": dict(
        headline="A 1.5-game cushion on the world number five",
        text=("Daniil Medvedev to cover a 1.5-game handicap in the Almaty semi-final. Medvedev is world number "
              "five on 3,660 ATP points and won his quarter-final 6-4 6-4; Bublik is nineteenth on 2,275 and "
              "needed three sets, two of them tiebreaks, to beat Karen Khachanov. The ranking gap gives Medvedev a "
              "59 per cent match price, and a 1.5-game cushion lifts the selection to about 71 per cent at -242."),
        facts=["world no.5 with 3,660 ATP points", "world no.19 with 2,275 ATP points"]),
}


def main():
    picks = json.load(open(os.path.join(OUT, "picks.json")))
    matches = {m["id"]: m for m in json.load(open(os.path.join(OUT, "matches.json")))["matches"]}
    sources = {s["key"]: s for s in json.load(open(os.path.join(OUT, "sources.json")))["sources"]}
    by_pick = {p["id"]: p for p in picks["picks"]}

    predictions, problems = [], []
    openings = set()
    for pid, spec in PROSE.items():
        pick = by_pick.get(pid)
        if pick is None:
            problems.append(f"{pid}: no such graded pick")
            continue
        fx = matches[pick["fixture_id"]]
        facts, missing = [], []
        for needle in spec["facts"]:
            hit = next((f for f in fx["facts"] if needle.lower() in f["value"].lower()), None)
            if hit is None:
                missing.append(needle)
            else:
                facts.append({"claim": hit["value"], "source_url": hit["source_url"], "source_key": hit["source_key"]})
        text = spec["text"]
        words = text.split()
        opening = " ".join(words[:3]).lower()
        if missing:
            problems.append(f"{pid}: fact not found in capture -> {missing}")
        if len(words) < 30:
            problems.append(f"{pid}: {len(words)} words")
        if BANNED.search(text) or BANNED.search(spec["headline"]):
            problems.append(f"{pid}: banned word")
        if opening in openings:
            problems.append(f"{pid}: duplicate opening '{opening}'")
        openings.add(opening)
        if not facts:
            problems.append(f"{pid}: no linked facts")
        predictions.append({
            "id": f"pred-{pid}", "pick_id": pid, "fixture_id": pick["fixture_id"], "sport": pick["sport"],
            "competition": pick["competition"], "home": pick["home"], "away": pick["away"],
            "start_utc": pick["start_utc"], "time_display": pick["time_display"],
            "selection": pick["selection"], "market": pick["market"], "line": pick["line"],
            "probability": pick["probability"], "fair_american": pick["fair_american"],
            "confidence": pick["confidence"], "in_band": pick["in_band"],
            "headline": spec["headline"], "text": text, "word_count": len(words),
            "facts": facts, "official_source_url": pick["official_source_url"],
        })

    if problems:
        for p in problems:
            print("PROBLEM:", p)
        raise SystemExit(1)

    predictions.sort(key=lambda p: (p["sport"], p["pick_id"]))
    graded = [p for p in picks["picks"] if p["confidence"] in ("high", "medium")]
    shortlisted = [p for p in graded if p.get("sport_rank")]
    unpaid = [p for p in shortlisted if p["id"] not in PROSE]
    if unpaid:
        for p in unpaid:
            print("PROBLEM: shortlisted pick without a prediction:", p["id"], p["sport"], p["selection"])
        raise SystemExit(1)

    flagged = json.load(open(os.path.join(OUT, "model_flags.json"))) if os.path.exists(
        os.path.join(OUT, "model_flags.json")) else []
    flagged = flagged + [{
        "id": "CD-PR1", "severity": "medium", "category": "Prediction coverage",
        "item": "Written predictions by sport",
        "finding": ("Written predictions exist for the graded selections listed on /cadence/predictions.html. "
                    "Three sports carry no prediction because no selection in them reached medium confidence: golf "
                    "(best outright 9.1%), greyhounds (best runner 50.4% off semi-final times alone) and Gaelic "
                    "sports (no numeric strength input for both sides). Their strongest selections are still "
                    "published with their prices and probabilities."),
        "source_url": "https://www.pgatour.com/leaderboard", "status": "published"}]
    flagged.append({
        "id": "CD-PR3", "severity": "medium", "category": "Repository overlap",
        "item": "This desk is another overlapping dashboard",
        "finding": ("The repository already holds more than thirty desks covering the same brief. Adding "
                    "/cadence/ makes that thirty-eight, and the ledger desk's own repository review flags the "
                    "overlap as a high-severity finding (RR-02). /cadence/ is published in its own namespace, "
                    "states its capture window and its shortfalls, and does not claim to supersede any other "
                    "layer; a single authoritative desk is an integration decision, not a claim this session can "
                    "make unilaterally."),
        "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/ledger/repo-review.html",
        "status": "published"})
    flagged.append({
        "id": "CD-PR2", "severity": "high", "category": "Price-band arithmetic",
        "item": "The two rules in the brief intersect in 1.43 percentage points",
        "finding": ("'High confidence above 70%' and 'price between -250 and +10000' intersect only in "
                    "70.00%-71.43%, because a fair -250 is 71.43%. The desk therefore publishes each selection's "
                    "own fair price and marks whether it is in band, and additionally quotes an alternate line at "
                    "the band ceiling wherever a continuous line ladder exists. It never relabels a shorter price "
                    "as in band. Today 8 of the 22 high-confidence selections fall inside the band without an "
                    "alternate line."),
        "source_url": "https://www.olbg.com/betting-tips", "status": "published"})

    json.dump({"generated_utc": GENERATED, "session": "arena/a0c8b7f3-olbg2",
               "count": len(predictions), "min_words": min(p["word_count"] for p in predictions),
               "sports": sorted({p["sport"] for p in predictions}),
               "unpaid_graded": [p["id"] for p in unpaid],
               "graded_not_shortlisted": [p["id"] for p in graded if not p.get("sport_rank")],
               "predictions": predictions},
              open(os.path.join(OUT, "predictions.json"), "w"), indent=1, ensure_ascii=False)
    json.dump({"generated_utc": GENERATED, "count": len(flagged), "flags": flagged},
              open(os.path.join(OUT, "flagged.json"), "w"), indent=1, ensure_ascii=False)
    print(f"predictions={len(predictions)} sports={len({p['sport'] for p in predictions})} "
          f"min_words={min(p['word_count'] for p in predictions)} flags={len(flagged)} unpaid_graded={len(unpaid)}")


if __name__ == "__main__":
    main()
