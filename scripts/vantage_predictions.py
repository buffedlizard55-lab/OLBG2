#!/usr/bin/env python3
"""Individually authored, source-fact-linked previews; never synthesize empty quotas.

All published analytical selections, not just the featured one, require unique
30+ word prose, a clearly named selection and a source for every external fact.
Injuries are mentioned only where an official match-specific report supports them.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vantage"

# The text is editorially written one fixture at a time. Probabilities, lines,
# and quoted odds are data-driven cells beside the write-up, not invented facts.
TEXT = {
    "nhl-2026020170": (
        "Boston Bruins money line is the single high-confidence, in-band selection in this snapshot. Boston shut out Nashville 6-0 on Thursday; Michael DiPietro stopped 28 shots and David Pastrnak scored twice with two assists. San Jose also arrives with momentum after beating Ottawa 6-2 behind Yaroslav Askarov's 41 saves. Across eleven league games Boston has scored 42 and conceded 22, compared with San Jose's 32 for and 36 against. That defensive gap makes Boston the lean, but the captured FanDuel -178 is not a current OLBG quote.",
        "The NHL score feed, team summary and the two October 22 game reports supply the scores, player output and current form. This 70.4% estimate is sensitive to the chosen prior: 72.1% with eight prior games or 69.0% with twelve. A fixture-specific injury list was not available, so no absence is asserted.",
    ),
    "nhl-2026020169": (
        "New Jersey Devils money line gets a medium, price-sensitive lean against Los Angeles. The Devils show a 6-4-0 record in the NHL game listing, with Jack Hughes on eight assists and Arseny Gritsyuk on five goals. Los Angeles is 2-4-2 and has allowed 29 goals in eight games; Artemi Panarin has six for the Kings. The fair line here is shorter for New Jersey than for Los Angeles, but the league-served FanDuel -194 is shorter still, so this is analysis rather than a claim of value.",
        "League matchup listing and 2026-27 NHL team summary supply the team/player numbers. No confirmed game-specific injury fact is used.",
    ),
    "nhl-2026020174": (
        "Vegas Golden Knights money line is the calculated side at Columbus, graded medium rather than automatic chalk. Vegas comes in 8-4-0, with 45 goals scored across twelve games; Mark Stone has eight goals and Jack Eichel thirteen assists. Columbus is 3-5-0, and its 19 goals in eight outings trail its 29 conceded. That difference supports an away lean, though an eight-game Blue Jackets sample is small and the quoted league partner price can move before faceoff.",
        "The matchup and leader numbers are in the NHL 24 October game listing; goal totals come from the NHL team summary.",
    ),
    "nhl-2026020176": (
        "Edmonton Oilers money line edges the Toronto matchup on scoring evidence, but the recommendation is only medium. Edmonton's ten-game NHL record is 8-1-1 with 46 goals scored, while Toronto's twelve-game return is 43 scored and 38 conceded. Leon Draisaitl has ten goals and Connor McDavid twenty-three assists; Auston Matthews has eight goals for the Leafs. A lively total is plausible, yet neither a predicted goal count nor the league-served -182 quote guarantees this particular winner.",
        "The official score feed names the participants, records and leaders; NHL team summary provides the goals-for/against inputs.",
    ),
    "ehf-magdeburg-kriens": (
        "SC Magdeburg in the three-way, regular-time match winner market is the measured lean against HC Kriens-Luzern. The EHF lists Magdeburg at five wins from five, 176 goals for and 140 against; Kriens has two wins from five and 158 for against 161. That scoring gap is meaningful, but the home three-way estimate still leaves room for a draw. OLBG's most-tipped Tie is a count of opinions, not evidence that a draw occurs in three quarters of games.",
        "Both clubs' group figures are published on the EHF standings; the EHF calendar confirms this specific fixture. No player availability is assumed.",
    ),
    "mlb-849802": (
        "Milwaukee Brewers money line is the medium research selection for World Series Game 2, not an inferred available bet. Milwaukee's official regular-season totals are 103-59 and 832 runs scored against 618 allowed, compared with Tampa Bay's 98-64 and 736 against 650. The MLB schedule lists Logan Henderson opposite Drew Rasmussen as probable starters; their season ERAs are 2.47 and 2.67 respectively. Milwaukee won Game 1 by a run, but neither that result nor a regular-season run rate determines the next postseason game.",
        "The MLB schedule confirms matchup, probable pitchers and prior game; the league standings and pitcher endpoint supply the season statistics. OLBG shows no usable numeric quote.",
    ),
    "ehf-kielce-kolstad": (
        "Industria Kielce to win in regulation is the small medium edge in its EHF Champions League meeting with Kolstad Håndball. Kielce has 155 goals scored and 153 conceded over five group games; Kolstad's 143 for and 178 against leaves a wider defensive deficit. The fixture is on the EHF's October 28 slate. With only five results on either side, a draw still matters in this three-outcome market and the projected price cannot stand in for a bookmaker offer.",
        "The official EHF match page and group table identify the fixture and both teams' complete five-game scoring records.",
    ),
    "nhl-2026020172": (
        "Pittsburgh Penguins money line is a low-confidence lean, not a must-back favorite. Their NHL listing records 4-6-1 through eleven games, and the team summary shows 36 goals scored against 37 allowed. Nashville is 3-3-3 with 23 for and 28 against in nine; Ryan O'Reilly has four goals and Roman Josi eight assists. Pittsburgh's Evgeni Malkin has six goals, but these clubs' patchy records and the unconfirmed goalie assignments make a strong call difficult.",
        "Records and named leaders are in the NHL game listing; official team scoring rates come from the 2026-27 summary. No starting goalie is asserted.",
    ),
    "nhl-2026020175": (
        "Carolina Hurricanes money line is only a narrow away lean against St. Louis in our fair prices. Carolina's 8-2-2 record and 47 goals in twelve games are eye-catching, with Sebastian Aho on seven goals and Jackson Blake on ten assists. Yet the Blues have scored 35 in ten, Mason McTavish has six goals, and home ice matters in a close projection. The recorded partner -154 on Carolina is not an OLBG offer and could be gone by puck drop.",
        "NHL 24 October score feed supplies records, leaders and the partner quote; team goals were read from the NHL summary.",
    ),
    "nhl-2026020171": (
        "New York Rangers money line has a modest statistical edge in Ottawa, graded low. The Rangers' 7-4-1 is accompanied by 37 goals scored and 29 conceded in twelve games; Adam Fox is listed with fourteen assists. Ottawa is 7-4-0 over eleven and Tim Stützle has seven goals and eight assists. The Senators were beaten 6-2 by San Jose in their previous documented game, though one setback alone is not enough to upgrade an away pick.",
        "NHL game listing and summary provide this season's records and scoring; the Sharks–Senators game centre confirms the recent score.",
    ),
    "nhl-2026020177": (
        "Utah Mammoth money line is a tentative home lean over Tampa Bay rather than a strong selection. Utah is 7-4-0, with 41 goals for and 36 against over eleven games; Nick Schmaltz has seven goals and Mikhail Sergachev ten assists. Tampa Bay is 7-3-0, with 34 for and 29 against in ten and Brandon Hagel on seven goals. Those profiles are competitive enough that a small calculated edge should not be mistaken for certainty or for the league partner's posted -144.",
        "The NHL score feed lists both teams and leaders and contains the partner quote; team summary provides the two scoring splits.",
    ),
    "nhl-2026020179": (
        "Seattle Kraken money line is a low-grade home angle against Minnesota, despite the Wild being the shorter side in the NHL feed's partner quote. Seattle is 7-3-1 through eleven games with 42 goals scored and 37 allowed; Minnesota is 6-3-2 with 32 for and 27 against. Kirill Kaprizov's eleven goals give the visitors obvious danger, so the narrow fair-price tilt toward Seattle is a judgment with plenty of uncertainty, not a market consensus.",
        "NHL schedule records the fixture, partner quote and Kaprizov total; team summary supplies goals and games played.",
    ),
    "ehf-vardar-melsungen": (
        "HC Vardar 1961 for the regulation-time result is a fragile home lean against MT Melsungen. In the EHF's first five group games Vardar scored 154 and allowed 158, whereas Melsungen scored and conceded 138. The different scoring profiles narrow substantially after accounting for the small sample; a level score is also a distinct outcome. This is low confidence because an assumed home edge and those five games do not establish future player availability or a real offered price.",
        "EHF official group table and match page provide the five-game numbers, date and opposing clubs.",
    ),
    "top14-rochelle-bordeaux": (
        "Union Bordeaux-Bègles to win in regular time is an exceptionally close, low-confidence alternative at Stade Rochelais. The league table has Bordeaux at four wins from six with 215 points for and 151 against; La Rochelle also has four wins, scoring 144 and allowing 135. Louis Bielle-Biarrey is named in Bordeaux's starting side and Grégory Alldritt in La Rochelle's. Home ground and the possible draw stop that larger attack tally from being a sure away victory; the published selection is purely an estimate.",
        "Top 14 standings supplies the scoring; the official match sheet names both starting players, fixture and venue.",
    ),
    "ehf-gog-sporting": (
        "GOG in the three-way regular-time market is the thinnest home lean on this card. Its five EHF group matches produced 178 goals for and 172 against, while Sporting Clube de Portugal posted 191 for and 165 against and remains unbeaten with four wins and one draw. Sporting's stronger raw scoring should make a reader pause: GOG's side of this calculation relies on the stated home allowance, not on an injury report or any bookmaker quote. Low confidence is warranted.",
        "The EHF official table supports the scoring and record, and its dated match link identifies GOG against Sporting.",
    ),
}

# Extra independently consulted official pages for words not present in a fixture's
# original facts list. The destination source itself is included in the site card.
EXTRA_SOURCES = {
    "nhl-2026020172": ["https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154"],
    "nhl-2026020171": ["https://www.nhl.com/gamecenter/sjs-vs-ott/2026/10/22/2026020156"],
}


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main():
    picks = load("picks.json")["picks"]
    fixtures = {r["id"]: r for r in load("fixtures.json")["fixtures"]}
    assert set(TEXT) == {p["fixture_id"] for p in picks}, "never show a bare pick without a write-up"
    previews = []
    seen = set()
    for p in picks:
        text, note = TEXT[p["fixture_id"]]
        f = fixtures[p["fixture_id"]]
        n = len(text.split())
        assert n >= 30, (f["id"], n)
        assert not re.search(r"\b(model|verified)\b", text, re.I), f["id"]
        assert p["selection"].casefold() in text.casefold(), f["id"]
        assert text not in seen, f["id"]
        seen.add(text)
        links = list(dict.fromkeys([f["official_url"], *f["extra_official_urls"],
                                    *[fact["url"] for fact in f["facts"]],
                                    *EXTRA_SOURCES.get(f["id"], [])]))
        assert len(links) >= 2, (f["id"], links)
        assert all(urlsplit(url).scheme == "https" for url in links)
        previews.append(dict(id=f"preview-{f['id']}", pick_id=p["id"], fixture_id=f["id"],
                             sport=f["sport"], start_utc=f["start_utc"],
                             headline=f"{p['selection']} · {p['market']}", selection=p["selection"],
                             market=p["market"], confidence=p["confidence"],
                             word_count=n, text=text, evidence_note=note,
                             sources=links, sourced_facts=f["facts"],
                             injury_status=None,
                             injury_note="No official pregame injury/availability information captured for this specific selection; left blank."))
    assert len({" ".join(r["text"].lower().split()[:6]) for r in previews}) == len(previews)
    payload = dict(as_of_utc=load("picks.json")["as_of_utc"], count=len(previews),
                   high=sum(x["confidence"] == "high" for x in previews),
                   by_sport=dict(sorted(Counter(x["sport"] for x in previews).items())),
                   predictions=previews)
    (DATA / "predictions.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"vantage_predictions: {payload['count']} unique 30+ word write-ups, {payload['high']} high, 0 unlinked picks")


if __name__ == "__main__":
    main()
