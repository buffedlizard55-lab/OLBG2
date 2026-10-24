#!/usr/bin/env python3
"""Attach unique, source-audited writing to every published pick."""
from __future__ import annotations

import json
import re
from pathlib import Path

from today_official_data import NBA_INJURY, NBA_PRIOR, NBA_STATS, NHLE_TEAM

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
MLB_MIL = "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings&season=2026"
MLB_STAND = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)

COPY = {
    "nhl-2026020174": (
        "Vegas has the stronger two-way route through Columbus",
        "Vegas Golden Knights are the moneyline selection in Columbus. Their 8-4-0 record is supported by 45 goals in 12 official team-summary games, while Columbus is 3-5-0 with 19 goals and 29 allowed in eight. Mark Stone’s eight goals and Jack Eichel’s 13 assists give Vegas multiple finishing and creation routes; Kent Johnson’s four goals lead the listed Blue Jackets. The pick respects Columbus’s home ice, but Vegas’s stronger record and scoring depth make the away win the clearest position. Columbus’s 3.625 goals allowed per game further supports the call without assuming a particular final score."
    ),
    "nba-0022600105": (
        "Cleveland’s full-season baseline separates a pair of 0-1 teams",
        "Cleveland Cavaliers are the moneyline selection against Brooklyn. The completed 2025-26 standings provide the strongest sample: Cleveland finished 52-30, Brooklyn 20-62. Both clubs are 0-1 this season, so their opening results do not outweigh that prior. Donovan Mitchell’s 32 points and 10 rebounds and Julius Randle’s 33 points and eight boards establish the main offensive references rather than a claim about current form. The official injury report lists Tyler Bilodeau out for Brooklyn and Khalifa Diop, Nae’Qwan Tomlin and Ernest Udeh Jr. out for Cleveland. Those absences narrow the certainty, but the long-run record gap still drives the home selection."
    ),
    "nba-0022600110": (
        "Denver’s prior-season strength outweighs a noisy opening week",
        "Denver Nuggets are the moneyline selection at home to New Orleans. Denver’s 54-28 record last season is the principal anchor against the Pelicans’ 26-56; this year’s 0-1 and 0-2 starts are explicitly treated as tiny samples. Aaron Gordon’s 20-point opener and Dejounte Murray’s 19.5-point average identify the current contributors without overstating their significance. Denver’s 84 points in one game are not presented as an established scoring level. Cameron Johnson, Spencer Jones and Julian Strawther are officially out, Alpha Diallo is questionable, and New Orleans had not submitted its report, keeping the availability caveat substantial."
    ),
    "nba-0022600109": (
        "San Antonio’s 62-win prior carries the road call",
        "San Antonio Spurs are the away moneyline selection in Dallas. Last season’s 62-20 record gives San Antonio a much stronger long-run baseline than Dallas’s 26-56, even though the Spurs have opened 0-2 and the Mavericks 1-1. Victor Wembanyama’s 18.5 points and 13 rebounds per game contrast with Cooper Flagg’s 23 points, five rebounds and four assists; those figures describe two-game samples, not settled form. The selection therefore leans on the full-season record rather than the early table. Both teams were marked NOT YET SUBMITTED on the official injury report, so no availability advantage is claimed."
    ),
    "nhl-2026020176": (
        "McDavid and Draisaitl headline Edmonton’s home case",
        "Edmonton Oilers are the home moneyline selection against Toronto. The Oilers’ 8-1-1 record and 46 goals in ten team-summary games supply the decisive early-season case, while Toronto stands 6-4-2 with 43 goals in twelve. Connor McDavid’s 23 assists and Leon Draisaitl’s ten goals give Edmonton elite production at both ends of a scoring sequence; Auston Matthews’s eight goals and ten assists keep the opponent’s threat explicit. Edmonton’s 32 goals allowed show this is not a defensive lock, so the pick is about overall strength rather than expecting a shutout. Toronto’s twelve-game sample also gives the visitors enough substance to keep the price from being treated as certain."
    ),
    "nhl-2026020169": (
        "New Jersey’s scoring gap supports a home win, not a price adjustment",
        "New Jersey Devils are the home moneyline selection against Los Angeles. New Jersey has 33 goals and 31 allowed through ten team-summary games, compared with the Kings’ 20 and 29 through eight, while the records are 6-4-0 and 2-4-2. Jack Hughes’s eight assists and Arseny Gritsyuk’s five goals support the Devils’ attack; Artemi Panarin’s six goals make Los Angeles the dangerous underdog rather than a passive opponent. The official scoring gap and home ice justify New Jersey, but the price remains outside the requested floor and is not adjusted to fit it. Los Angeles’s 3.625 goals allowed per game is the relevant early-season defensive comparison."
    ),
    "nhl-2026020170": (
        "Boston’s two-way numbers just miss the High threshold",
        "Boston Bruins are the home moneyline selection, graded just below the High threshold. Boston’s 42 goals for and 22 against in eleven games are stronger two-way figures than San Jose’s 32 and 36 over the same number, and the Bruins’ 8-2-1 record leads the Sharks’ 6-4-1. David Pastrnak’s six goals and ten assists plus Jeremy Swayman’s six wins supply concrete support; Macklin Celebrini’s five goals and nine assists show why San Jose cannot be dismissed. The 3.818 goals per game attached to Boston is an early-season scoring rate, not a guarantee. San Jose’s 3.273 goals allowed per game offers a narrower matchup comparison than simply reading the standings."
    ),
    "nba-0022600106": (
        "Philadelphia’s start and prior record outweigh Milwaukee’s scoring average",
        "Philadelphia 76ers are the home moneyline selection against Milwaukee. The 45-37 prior-season record and a 2-0 start give Philadelphia a better combined baseline than Milwaukee’s 32-50 and 0-2, although the current sample remains only two games per club. Tyrese Maxey averages 30 points and Tyler Herro 29, so both primary scoring references are acknowledged. Philadelphia’s 110 points per game and plus-seven differential support the pick without treating them as settled form. Dominick Barlow, Tacko Fall, Ariel Hukporti and LeBron James are officially out for Philadelphia; that confirmed absence list tempers the selection rather than being ignored."
    ),
    "nba-0022600108": (
        "Chicago gets the home nod while Washington’s report remains pending",
        "Chicago Bulls are the home moneyline selection against Washington. Chicago’s 31-51 prior-season record was stronger than Washington’s 17-65, and both teams now stand 1-1, so the longer sample carries the decision. Jalen Smith’s 14.5 points and 10.5 rebounds and Anthony Davis’s 21.5 points and 10.5 rebounds are the listed current leaders, not evidence of a long-term trend. Washington’s 115 points per game and plus-one differential keep this from reading like a mismatch. Nic Claxton is officially out and Noa Essengue probable for Chicago; Washington had not submitted its report, leaving a material uncertainty."
    ),
    "nhl-2026020178": (
        "Detroit’s defensive comparison supports the road selection",
        "Detroit Red Wings are the away moneyline selection in Calgary. Detroit’s 27 goals for and 28 against across ten games compare favourably with Calgary’s 19 and 38 across nine, while the records are 4-3-3 and 3-6-0. Alex DeBrincat’s six goals and six assists provide the clearest individual attacking support; Morgan Frost’s three goals and Joel Farabee’s five assists are Calgary’s listed counters. Calgary’s 4.222 goals allowed per game is a small-sample figure, but the nine-game defensive gap still supports Detroit. Home ice and Detroit’s three overtime losses prevent a stronger grade, while Calgary’s nine-game sample still leaves room for regression."
    ),
    "mlb-849802": (
        "Milwaukee’s season-long run differential earns the Game 2 call",
        "Milwaukee Brewers are the home moneyline selection for World Series Game 2. Their 103-59 record, 832 runs scored and 618 allowed establish the stronger season-long run differential against Tampa Bay’s 98-64, 736 and 650. Milwaukee also went 55-26 at home and 8-2 over the last ten, while the Rays were 43-38 away and 5-5. Logan Henderson and Drew Rasmussen are the officially listed probable starters, but no handedness or unconfirmed availability is added. Tampa Bay’s quality keeps this below High confidence; the selection rests on Milwaukee’s season record and home split."
    ),
    "tennis-atp-almaty-2026-final": (
        "Medvedev’s season-long baseline carries the Almaty final",
        "Daniil Medvedev is the match-winner selection against Nikoloz Basilashvili. The official head-to-head page lists Medvedev at 45-18 this season and Basilashvili at 7-10, a much broader basis than one week’s results. Medvedev also owns 37 hard-court wins and a 10-1 Almaty record, while Basilashvili has reached his first tour final since Doha 2022 and climbed to live rank 97. The Georgian’s three-set semifinal win over Stefanos Tsitsipas shows why this is not a certainty, but Medvedev leads their head-to-head 1-0 and won their Vienna meeting 6-2 6-2. His season-long consistency and defending-champion record justify the pick."
    ),
    "tennis-wta-osaka-2026-final": (
        "Krueger gets only a marginal lean in a finely balanced Osaka final",
        "Ashlyn Krueger is a narrow match-winner selection against Katerina Siniakova. Krueger’s 8-1 completed-set record at Osaka includes wins over sixth seed Janice Tjen, fourth seed Talia Gibson and top seed Ann Li; Siniakova’s 7-1 completed-set record includes an opening match that ended by retirement, so it is not treated as eight completed sets. Siniakova beat Katie Boulter 6-1 6-4 to reach her first singles final since 2023, while Krueger is the 2023 Osaka champion and current rank 55. The near-even grading reflects Siniakova’s strong week, with Krueger’s slightly larger completed-set sample and demanding route providing only a marginal lean."
    ),
    "tennis-wta-ningbo-2026-final": (
        "Rybakina’s season record and title defence lead the Ningbo call",
        "Elena Rybakina is the match-winner selection in the Ningbo final. Her 49-14 season record, World No. 1 ranking and three titles give her the strongest baseline against Leylah Fernandez’s 24-25 and one title. Rybakina also leads their head-to-head 3-2 and is defending the Ningbo championship. Fernandez’s 11-2 run since the Asian Swing began and her second final of the season make her a live opponent, not a passive underdog. Both won their semifinals 6-3 7-5, but Rybakina has lost only one set this week and has spent less time on court. The pick rests on season-long superiority and the defending champion’s repeat-final experience."
    ),
    "vol-20261025-civitanova-padova": (
        "Civitanova’s cleaner opener supplies the volleyball card’s strongest edge",
        "Cucine Lube Civitanova are the match-winner selection against Pallavolo Padova. Civitanova opened with a 3-0 win at Verona, scoring 78 points and conceding 65, while Padova lost 0-3 at home to Piacenza with 56 points for and 75 against. That gives the home side the better opening result, set return and point differential, although one round cannot establish a reliable season hierarchy. Padova’s home defeat also came against a strong opening opponent, so the price keeps meaningful upset room rather than treating the sweep comparison as decisive. The pick is supported by every available first-round indicator, with home court providing only a modest additional edge."
    ),
    "vol-20261025-monza-verona": (
        "Monza’s resistance at Pordenone earns a cautious home lean",
        "Vero Volley Monza are the match-winner selection against Rana Verona in a cautious call between two opening-round losers. Monza took a set at Pordenone before falling 1-3, finishing with 91 points for and 94 against; Verona lost 0-3 at home to Civitanova with 65 and 78. Monza’s ability to extend their opener and nearly match Pordenone’s scoring is the main reason for the home lean. Verona’s 65 points came against a Civitanova side that swept every set, which limits how harshly that result should be read. With both teams 0-1 and only one official round available, the low grade is more appropriate than presenting Monza’s small statistical edge as settled form."
    ),
    "vol-20261025-trentino-cisterna": (
        "Home court barely separates two opening-round sweep winners",
        "Itas Trentino are the match-winner selection against Cisterna Volley, but the margin is deliberately small. Trentino won 3-0 at Modena with 75 points for and 61 against, while Cisterna won 3-0 at home to Milano with 79 and 56. Both teams are 1-0 and neither dropped a set, so the opening round offers no meaningful separation in wins or set record. Cisterna’s slightly stronger point differential is acknowledged rather than hidden; the selection comes only from the fixed home-court component after heavy shrinkage. With identical results and just one match per club, this remains low confidence and should not be read as a claim that Trentino have demonstrated superior form."
    ),
    "vol-20261025-perugia-pordenone": (
        "Perugia’s home edge narrowly outweighs Pordenone’s efficient opener",
        "Sir Susa Scai Perugia are the match-winner selection against Tinet Prata di Pordenone in the closest call on the volleyball card. Perugia won 3-2 at Cuneo with 114 points for and 95 against, while Pordenone won 3-1 at home to Monza with 94 and 91. Both are 1-0, and Pordenone’s fewer sets lost balance Perugia’s stronger point differential. Home court creates the narrow lean, not a claim of proven superiority after one round. Pordenone’s four-set win shows they can close a match efficiently, while Perugia’s five-set opener demonstrates resilience but also leaves greater uncertainty. The low grade reflects those competing indicators."
    ),
    "hb-20261025-saint-raphael-paris": (
        "Paris pair an unbeaten record with the stronger defensive return",
        "Paris Saint-Germain Handball are the away moneyline selection against Saint-Raphaël. Paris are 7-0-0 with 239 goals for and 190 against, while Saint-Raphaël are 2-5-0 with 207 and 225 through seven matches. That gives Paris both the unbeaten record and the stronger scoring differential, yet the three-way price still includes a meaningful draw and home-win path. Saint-Raphaël’s 207 goals show enough attacking production to resist a certainty claim, especially at home. The selection is based on Paris’s superior seven-game evidence and strong defensive comparison, with regular-time settlement explicitly retained rather than treating the match as a two-way contest."
    ),
    "hb-20261025-rhein-neckar-magdeburg": (
        "Magdeburg’s response and head-to-head record outweigh Löwen’s home edge",
        "SC Magdeburg are the away moneyline selection against Rhein-Neckar Löwen. Magdeburg’s 8-1-0 record and 301 goals for compare with Löwen’s 3-5-1 and 266, while the defensive figures are 266 against and 273. The champion has responded to its 30-34 defeat with four wins, although the latest 29-28 at Stuttgart was narrow. Löwen lost 36-37 at Kiel and took one point from the last three, but David Späth’s 118 saves and home court keep an upset plausible. Magdeburg’s ten wins and one draw across the last 11 head-to-heads strengthen the call without making it certain."
    ),
    "hb-20261025-fuchse-wetzlar": (
        "Füchse’s scoring ceiling meets a winless opponent, with recent caveats",
        "Füchse Berlin are the home moneyline selection against HSG Wetzlar. Berlin’s 5-3-0 record and 270 goals for meet Wetzlar’s 0-7-2 and 303 allowed, but the recent story is less comfortable: Füchse lost 36-37 to Lemgo and 33-34 at Flensburg on last-second goals. Wetzlar also lost 30-34 to Erlangen and still seeks its first win. Mathias Gidsel’s 70 goals in eight games give Berlin an elite scoring reference, while Niklas Theiß has 54 for the visitors. Ten consecutive head-to-head wins and a 29-6 overall series support Füchse, with the recent narrow defeats tempering the grade."
    ),
    "hb-20261025-montpellier-saran": (
        "Montpellier’s positive scoring differential leads a three-way home call",
        "Montpellier Handball are the home moneyline selection against Saran Loiret Handball. Montpellier’s 4-1-2 record includes two draws and comes with 234 goals for and 205 against; Saran are 3-4-0 with 202 and 216. That gives the hosts the better return across seven matches and a positive scoring differential, while Saran’s negative differential points the other way. The regular-time tie remains a genuine alternative and is priced separately, not folded into either team. With no official availability report read and only the current standings as comparable form evidence, Montpellier’s edge supports a medium grade rather than a stronger claim."
    ),
    "hb-20261025-bergischer-hamburg": (
        "Hamburg receives only a narrow lean despite Bergischer’s home struggles",
        "Handball Club Hamburg are the away moneyline selection against Bergischer HC in a near-even call. Hamburg’s 2-6-1 record and 274 goals for sit against Bergischer’s 1-7-0 and 223, although the hosts have conceded fewer goals, 256 compared with 285. Hamburg’s 35-30 win at Bietigheim was its second of the season, while Bergischer followed a 29-28 win at Balingen with a 26-33 defeat at Melsungen and still has no home point. Bergischer won both meetings last season and leads the overall series 8-6, so Hamburg receives only a narrow lean from current season evidence."
    ),
    "darts-ec-aspinall-littler": (
        "Littler’s ranking base edges a balanced opener comparison",
        "Luke Littler is the match-winner selection against Nathan Aspinall. Both won their openers 6-3, so the tournament leg records do not justify a runaway position. Littler’s 105.05 average against William O’Connor was the tournament’s best at that point, while Aspinall’s 6-3 win over Cristo Reyes keeps the opposition firmly live. The longer ranking evidence separates them more clearly: Littler has £3,106,000 in two-year world-ranking earnings against Aspinall’s £577,000, although Aspinall leads current European Tour earnings £87,000 to £75,000. The best-of-19 format and identical opening scorelines support a medium rather than high grade."
    ),
    "darts-ec-clayton-rock": (
        "Rock’s six-leg finish narrowly outweighs Clayton’s ranking edge",
        "Josh Rock is the match-winner selection against Jonny Clayton. Rock’s 6-1 defeat of Chris Dobey included six consecutive legs, compared with Clayton’s 6-3 win over Niko Springer, giving Rock the better opening-round leg differential. Their official ranking profiles are much closer: Clayton has £691,000 in world-ranking earnings and £86,000 on the European Tour, while Rock has £599,000 and £76,000. Clayton’s slightly stronger earnings base prevents a high grade, but Rock’s six-leg finishing run is the decisive current-tournament evidence. The selection is for the match, not an assumption that another 6-1 score is likely."
    ),
    "darts-ec-price-bunting": (
        "Price’s small ranking and leg-record edges meet Bunting’s finishing threat",
        "Gerwyn Price is the match-winner selection against Stephen Bunting in Sunday’s quarterfinal. Price beat Rob Cross 6-2 with a 99.26 average and Cameron Menzies 10-4, while Bunting edged Danny Noppert 6-5 before beating Kim Huybrechts 10-3 with four 100-plus checkouts. Their tournament leg records are 16-6 and 16-8, so both arrive with strong returns rather than a one-sided form gap. Price’s £779,500 world-ranking earnings and £70,000 European Tour total exceed Bunting’s £568,750 and £43,000, providing a modest additional edge. Bunting’s finishing display keeps this at medium confidence."
    ),
    "f1-2026-united-states": (
        "Antonelli’s season lead and close Practice 2 pace earn a restrained race call",
        "Kimi Antonelli is the race-winner selection for the United States Grand Prix. His 340 championship points and eight wins lead the field, and his Practice 2 lap was only 0.042 seconds behind Charles Leclerc’s 1:35.291. Max Verstappen brings consecutive victories in Bahrain and Singapore and was third in Practice 2, 0.189 seconds off Leclerc, so this remains a low-confidence race call rather than a season-title assumption. George Russell has three wins and 238 points, while Lewis Hamilton has 229 and one win. Qualifying had not produced an official grid when researched, so no starting-position advantage is claimed."
    ),
}


def fact(claim, url):
    return dict(claim=claim, source_url=url)


def facts_for(fixture):
    if fixture["sport"] == "Baseball":
        return [
            fact("MLB schedule: World Series Game 2, Tampa Bay at Milwaukee, 2026-10-25T00:00:00Z; probable pitchers Drew Rasmussen and Logan Henderson", fixture["source_url"]),
            fact("Milwaukee: 103-59, 832 runs scored, 618 allowed, 55-26 at home, 8-2 over the last ten", MLB_MIL),
            fact("Tampa Bay: 98-64, 736 runs scored, 650 allowed, 43-38 away, 5-5 over the last ten", MLB_STAND),
        ]
    if fixture["sport"] == "Motor Racing":
        return [fact(claim, url) for claim, url in fixture.get("extra_facts", [])]
    if fixture["sport"] == "Tennis":
        # Schedule, player records and current-tournament evidence have distinct
        # official URLs. Keep them separate rather than attributing every claim
        # to the order-of-play page.
        facts = [fact(f"Official order of play: {fixture.get('start_display') or fixture['start_utc']}", fixture["source_url"])]
        home_source = fixture["stats_source_url"]
        away_source = fixture["stats_source_url"]
        if fixture["id"] == "tennis-wta-ningbo-2026-final":
            from today_extra_data import WTA_RYBAKINA, WTA_FERNANDEZ
            home_source, away_source = WTA_RYBAKINA, WTA_FERNANDEZ
        facts.extend([fact(f"{fixture['home']}: {fixture['fact_home']}", home_source),
                      fact(f"{fixture['away']}: {fixture['fact_away']}", away_source)])
        facts.extend(fact(claim, url) for claim, url in fixture.get("extra_facts", []))
        return facts
    facts = [fact(f"{fixture['home']}: {fixture['fact_home']}", fixture.get("stats_source_url", fixture["source_url"])),
             fact(f"{fixture['away']}: {fixture['fact_away']}", fixture.get("stats_source_url", fixture["source_url"]))]
    facts.extend(fact(claim, url) for claim, url in fixture.get("extra_facts", []))
    if fixture["sport"] == "Darts":
        facts.append(fact(
            f"Tournament leg records: {fixture['home']} {fixture['home_record']}; "
            f"{fixture['away']} {fixture['away_record']}", fixture["record_source_url"]))
    if fixture["sport"] in ("Volleyball", "Handball"):
        facts.append(fact(
            f"Official standings records: {fixture['home']} {fixture['home_record']}; "
            f"{fixture['away']} {fixture['away_record']}", fixture["stats_source_url"]))
    if fixture["sport"] == "Ice Hockey":
        for side in ("home", "away"):
            row = fixture["nhl"][side]
            facts.append(fact(
                f"{fixture[side]} team summary: {row['gp']} games, {row['goals_for']} goals for, "
                f"{row['goals_against']} against; {row['goals_for'] / row['gp']:.3f} GF/game and "
                f"{row['goals_against'] / row['gp']:.3f} GA/game", NHLE_TEAM))
    elif fixture["sport"] == "Basketball":
        facts.append(fact(
            f"Completed 2025-26 records: {fixture['home']} {fixture['prior_home_record']}; "
            f"{fixture['away']} {fixture['prior_away_record']}", NBA_PRIOR))
        for side in ("home", "away"):
            row = fixture["nba"][side]
            facts.append(fact(
                f"{fixture[side]} current traditional statistics: {row['gp']} games, "
                f"{row['points_per_game']} points per game, {row['point_differential']} average point differential",
                NBA_STATS))
        for item in fixture.get("injuries", []):
            facts.append(fact(
                f"{item['team']}: {item['player']} — {item['status']} ({item['reason']})",
                NBA_INJURY))
    return facts


def injury_fields(fixture):
    if fixture["sport"] != "Basketball":
        return None, "No official injury or availability report was read; injury status remains blank."
    status = fixture.get("injury_report_status", "submitted")
    if status != "submitted":
        note = f"NBA 1:30 PM ET report: {status}; no availability claim is made for an unsubmitted team."
    elif fixture.get("injuries"):
        note = "NBA 1:30 PM ET injury report read; captured designations are listed in the official facts below."
    else:
        note = "NBA 1:30 PM ET injury report read; no additional availability claim is made."
    return fixture.get("injuries", []), note


def build():
    board = json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))
    fixtures = {f["id"]: f for f in board["fixtures"]}
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["picks"]
    predictions = []
    for pick in picks:
        fixture = fixtures[pick["fixture_id"]]
        if fixture["id"] not in COPY:
            raise SystemExit(f"Missing unique analysis for published pick {fixture['id']}")
        headline, text = COPY[fixture["id"]]
        if BANNED.search(text):
            raise SystemExit(f"Prohibited wording in analysis {fixture['id']}")
        if pick["selection"] not in text:
            raise SystemExit(f"Selection is not explicit in analysis {fixture['id']}")
        injuries, injuries_note = injury_fields(fixture)
        predictions.append(dict(
            id=f"preview-{fixture['id']}", fixture_id=fixture["id"], sport=pick["sport"],
            competition=pick["competition"], event_name=pick.get("event_name"),
            home=pick["home"], away=pick["away"],
            start_utc=pick["start_utc"], start_display=pick.get("start_display"),
            headline=headline, selection=pick["selection"],
            market=pick["market"], line=pick.get("line"), probability=pick["probability"],
            fair_american=pick["fair_american"], confidence=pick["confidence"],
            in_band=pick["in_band"], text=text, word_count=len(text.split()),
            official_fixture_url=fixture["source_url"], olbg_event_url=pick.get("olbg_event_url"),
            facts=facts_for(fixture), injuries=injuries, injuries_note=injuries_note,
        ))
    (DATA / "predictions.json").write_text(json.dumps(dict(
        generated_utc=board["capture_end_utc"], count=len(predictions),
        min_words=min((p["word_count"] for p in predictions), default=0),
        unique_texts=len({p["text"].casefold() for p in predictions}), predictions=predictions,
    ), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"today_predictions: {len(predictions)} unique analyses, "
          f"shortest {min((p['word_count'] for p in predictions), default=0)} words")


if __name__ == "__main__":
    build()
