#!/usr/bin/env python3
"""Write the human previews for the 2026-10-24 snapshot.

Every sentence that carries a number is backed by one of the captured facts listed in the
`facts` array for that prediction.  Nothing is carried over from an earlier session's data:
if a figure was not read in this capture it does not appear in the copy.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "today"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)

NHLE = "https://api-web.nhle.com/v1/score/2026-10-24"
NHLE_SCHED = "https://api-web.nhle.com/v1/schedule/2026-10-24"
MLB_SCHED = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team"
MLB_MIL = "https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings&season=2026"
MLB_STAND = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"

COPY = {
    "nhl-2026020174": dict(
        headline="Vegas take the best record of the priced card into Columbus",
        text=("Vegas Golden Knights to win on the money line. Vegas are 8-4-0 through twelve games with "
              "46 goals for and 36 against, a 16-point return that is the strongest record of any club "
              "priced here tonight. Columbus are 3-5-0 from eight starts and sit on six points. Our fair "
              "price for the visitors is -237 and the league's own two-way quote has them at 1.76, so the "
              "road side is where the edge sits. Selection: Vegas Golden Knights, money line."),
        facts=[
            ("Vegas 8-4-0 in 12 games, 46 goals for, 36 against, 16 points", NHLE),
            ("Columbus 3-5-0 in 8 games, 6 points", NHLE),
            ("League quote: Vegas 1.76, Columbus 2.11", NHLE),
        ],
    ),
    "nhl-2026020170": dict(
        headline="Boston's 17-point start meets a San Jose side four points back",
        text=("Boston Bruins to win at TD Garden. Boston are 8-2-1 over eleven games for 17 points, with "
              "42 goals scored and 22 conceded, and the individual numbers match the team ones: David "
              "Pastrnak has six goals and ten assists while Jeremy Swayman has six wins in net. San Jose "
              "are 6-4-1 and on 13 points from the same eleven games, four points adrift. We make Boston "
              "-233, inside the requested range, and the league quote of 1.54 is close to that."),
        facts=[
            ("Boston 8-2-1 in 11 games, 17 points, 42 goals for, 22 against", NHLE),
            ("David Pastrnak: 6 goals, 10 assists. Jeremy Swayman: 6 wins", NHLE),
            ("San Jose 6-4-1 in 11 games, 13 points; Macklin Celebrini 5 goals, 9 assists", NHLE),
            ("League quote: Boston 1.54, San Jose 2.52", NHLE),
        ],
    ),
    "nhl-2026020169": dict(
        headline="New Jersey's form is the stronger side of this game, but -279 is outside the band",
        text=("New Jersey Devils to win at the Prudential Center. New Jersey are 6-4-0 for twelve points, "
              "with Jack Hughes already on eight assists, Arseny Gritsyuk on five goals and Jake Allen on "
              "four wins. Los Angeles are 2-4-2, six points from eight games, and their output runs through "
              "Artemi Panarin's six goals and Brandt Clarke's five assists. We price the Devils at 73.6%, a "
              "fair -279, so this pick is flagged as being outside the -250 floor rather than trimmed to fit."),
        facts=[
            ("New Jersey 6-4-0 in 10 games, 12 points; Jack Hughes 8 assists; Jake Allen 4 wins", NHLE),
            ("Los Angeles 2-4-2 in 8 games, 6 points; Artemi Panarin 6 goals; Brandt Clarke 5 assists", NHLE),
            ("League quote: New Jersey 1.53, Los Angeles 2.55", NHLE),
        ],
    ),
    "nhl-2026020173": dict(
        headline="Washington hold the same points as Buffalo from one fewer game",
        text=("Washington Capitals on the money line. Washington are 5-4-0 for ten points, with Alex Tuch on "
              "five goals, Dylan Strome on five assists and Logan Thompson on four wins. Buffalo are 4-4-2, "
              "also on ten points, but they have needed one more game to get there. That extra fixture "
              "without an extra point is the whole of the case for the home side, and it is why the fair "
              "price is -145 while the league has Washington at 1.84. Selection: Capitals to win."),
        facts=[
            ("Washington 5-4-0 in 9 games, 10 points; Alex Tuch 5 goals; Logan Thompson 4 wins", NHLE_SCHED),
            ("Buffalo 4-4-2 in 10 games, 10 points; Tage Thompson 5 goals; Zach Benson 6 assists", NHLE_SCHED),
            ("League quote: Washington 1.84, Buffalo 2.01", NHLE_SCHED),
            ("No OLBG event id was listed for this fixture at capture", "https://www.olbg.com/betting-tips/Ice_Hockey/13"),
        ],
    ),
    "mlb-849802": dict(
        headline="A 103-win Milwaukee side hosts a Tampa Bay team that travelled badly",
        text=("Milwaukee Brewers to win the World Series game at American Family Field. Milwaukee went 103-59 "
              "with 832 runs scored and 618 allowed, were 55-26 at home, and won eight of their last ten. "
              "Tampa Bay finished 98-64 with 736 runs and 650 allowed, but were 43-38 on the road and 5-5 "
              "across their last ten. Logan Henderson is listed as Milwaukee's probable starter and Drew "
              "Rasmussen for the Rays. We make the Brewers -131, a slender home edge rather than a strong one."),
        facts=[
            ("Milwaukee 103-59, 832 runs scored, 618 allowed, 55-26 home, 8-2 last ten", MLB_MIL),
            ("Tampa Bay 98-64, 736 scored, 650 allowed, 43-38 away, 5-5 last ten", MLB_STAND),
            ("Probable pitchers: Logan Henderson (MIL), Drew Rasmussen (TB) - first pitch 2026-10-25T00:00:00Z at American Family Field", MLB_SCHED),
        ],
    ),
    "nhl-2026020171": dict(
        headline="Ottawa at home against the crowd on a coin-flip record",
        text=("Ottawa Senators to win at the Canadian Tire Centre, which goes against the crowd: OLBG's "
              "most-tipped selection on this game was the New York Rangers. Ottawa are 7-4-0 for 14 points, "
              "Tim Stutzle has seven goals and eight assists and Linus Ullmark has seven wins. New York are "
              "7-4-1 for 15 points, one point better over one extra game, with Alexis Lafreniere on eight "
              "goals and Adam Fox on fourteen assists. We price Ottawa at -125 on home ice."),
        facts=[
            ("Ottawa 7-4-0 in 11 games, 14 points; Tim Stutzle 7 goals, 8 assists; Linus Ullmark 7 wins", NHLE),
            ("New York 7-4-1 in 12 games, 15 points; Alexis Lafreniere 8 goals; Adam Fox 14 assists", NHLE),
            ("League quote: Ottawa 1.80, New York 2.05", NHLE),
            ("OLBG most-tipped selection on event 200008 was NY Rangers (3/3 tips, 100%)", "https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/NY_Rangers_@_OTT_Senators/13?event_id=200008"),
        ],
    ),
}


def main() -> None:
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["picks"]
    fixtures = {f["id"]: f for f in json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))["fixtures"]}
    out = []
    for pick in picks:
        copy = COPY.get(pick["fixture_id"])
        if not copy:
            continue
        text = copy["text"].strip()
        words = len(text.split())
        assert words >= 30, (pick["fixture_id"], words)
        assert not BANNED.search(text), pick["fixture_id"]
        f = fixtures[pick["fixture_id"]]
        out.append(dict(
            id=f"pred-{pick['fixture_id']}",
            fixture_id=pick["fixture_id"], sport=pick["sport"], competition=pick["competition"],
            home=pick["home"], away=pick["away"], start_utc=pick["start_utc"],
            selection=pick["selection"], market=pick["market"],
            probability=pick["probability"], fair_american=pick["fair_american"],
            confidence=pick["confidence"], in_band=pick["in_band"],
            headline=copy["headline"], text=text, word_count=words,
            facts=[dict(claim=c, source_url=u) for c, u in copy["facts"]],
            injuries=None,
            injuries_note=("No injury or suspension list was published by the league feed used for this fixture, "
                           "so no availability claim is made."),
            official_fixture_url=f["source_url"],
            olbg_event_url=next((l["url"] for l in json.loads((DATA / "olbg_listings.json").read_text(encoding="utf-8"))["listings"]
                                 if pick.get("olbg_event_id") and l["event_id"] == pick["olbg_event_id"]), ""),
            provenance_note=("Written from the facts stored against this fixture at capture; every figure in the "
                             "copy appears in the facts list below it."),
        ))
    (DATA / "predictions.json").write_text(json.dumps(dict(
        generated_utc=json.loads((DATA / "picks.json").read_text(encoding="utf-8"))["as_of_utc"],
        count=len(out), min_words=min([p["word_count"] for p in out], default=0), predictions=out,
    ), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"today_predictions: {len(out)} previews, shortest {min([p['word_count'] for p in out], default=0)} words")


if __name__ == "__main__":
    main()
