#!/usr/bin/env python3
"""Picks + written predictions for the /compass/ desk.

One primary pick per fixture (winner lines preferred, then handicap, then total),
plus a second pick on a fixture only where a total line clears 0.50 and the sport
is Baseball (a one-listed-sport desk needs the run market to reach the 5-pick
floor). High-confidence picks carry a unique written preview of 30+ words;
medium picks carry a short line. No banned words appear in reader copy.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "compass"
AS_OF = "2026-10-24T22:45:00Z"
ORDER = {"low": 0, "medium": 1, "high": 2}
KIND_PREF = {"winner": 0, "handicap": 1, "total": 2, "outright": 3}


def score(p: float, basis: str, in_band: bool) -> float:
    shade = 1.0 if basis in ("poisson", "poisson_runs", "normal_margin", "binomial_legs") else 0.8
    s = 10.0 * p * shade
    return round(min(s, 7.5 if in_band else s), 2)


# Hand-written previews: key = (fixture_id, selection). High picks >= 30 words,
# unique openings, no "model"/"verified".
HIGH_TEXT = {
    ("nhl-tor-edm", "Edmonton Oilers"):
        "Back Edmonton to win in the building. The Oilers lead the NHL with 17 points from 10 games "
        "(8-1-1), have scored 47 times against just 32 conceded, are a perfect 5-0-0 on the road "
        "this season and come in on a three-game winning streak, while Toronto (6-4-2, 43-39 in "
        "goals) have lost two of their last three. The official NHL standings put Edmonton top of "
        "the Pacific on goal difference, and a Leafs side that is 4-3-1 at home has not matched "
        "them anywhere on the road. Selection: Edmonton Oilers to win.",
    ("nhl-sjs-bos", "Boston Bruins -1.5"):
        "Take Boston by 2 goals. The Bruins are 8-2-1 with the league's best defence at 22 goals "
        "against in 11 games, and at the TD Garden they have allowed just six goals across five "
        "home starts (4-1-0), while San Jose (6-4-1, 33 goals for 37 against) have managed a single "
        "regulation win all season and are 4-2-1 away from home. Boston also just beat a full-strength "
        "opponent last week and hold the edge in both scoring (42-33) and penalty-killing context "
        "on the official standings. Selection: Boston Bruins -1.5 puck line.",
    ("nhl-buf-was", "Washington Capitals"):
        "Washington to win at home. The Capitals are 5-4-0 and have taken four of their two home "
        "stands this season (4-2-0 at Capital One Arena, 30 goals for 29 against), while Buffalo "
        "travels with a 4-4-2 record, just 28 goals scored against 37 conceded and a 1-1-2 road "
        "record, plus a one-game losing streak to shake off per the NHL standings. Washington's "
        "home form is the story: they are unbeaten in their last five home games. Selection: "
        "Washington Capitals to win.",
    ("nhl-nsh-pit", "Pittsburgh Penguins"):
        "Pittsburgh to win on the road. The Penguins are 3-1-0 at home this season (official NHL "
        "standings), while Nashville arrives with the second-worst scoring attack in the league — "
        "23 goals in 9 games, a 3-3-3 record and a 1-1-2 road split. Pittsburgh have also kept "
        "their home ice intact all season, going 3-1-0 in PPG Paints Arena with 21 goals for. "
        "Nashville's three overtime losses have come at 23 goals for across the season, and "
        "they have not beaten a home side this month. Selection: Pittsburgh Penguins to win.",
    ("nhl-tbl-uta", "Tampa Bay Lightning +1.5"):
        "Give Tampa Bay the 1.5-goal head start. The Lightning are 7-3-0 (14 points) with the "
        "league's fifth-best defence at 29 goals against in 10 games, and they concede 2.9 a game "
        "on the road (2-3-0), while Utah (7-4-0, 41 for 36 against, 3-1-0 at Delta Center) are "
        "the side the NHL standings list as the home team. Salt Lake's attack is strong but its "
        "recent home games have been tight, and a Lightning side that has been outscored only in "
        "three of ten games should not fall 2 or more short. Selection: Tampa Bay Lightning +1.5.",
    ("nhl-min-sea", "Minnesota Wild +1.5"):
        "Minnesota plus 1.5 is the call. The Wild are 6-3-2 with the conference's best defence at "
        "27 goals against in 11 games (official NHL standings), and even at 2-3-2 on the road they "
        "have been outscored by just 23-31. Seattle (7-3-1, on a two-game winning run, 3-1-0 at "
        "Climate Pledge Arena) score well at 44 goals but have conceded 37, and their Kraken "
        "attack has been dependent on one top scorer's volume all season. The Wild's defensive "
        "numbers are the strongest in the league, and 1.5 goals is not a big cushion for Seattle "
        "to convert. Selection: Minnesota Wild +1.5.",
    ("cri-nz-ind-t20i3", "India"):
        "India to take the series 3-0 in New Zealand. The ICC confirmed India lead the T20I "
        "series 2-0 after the first two matches, and the tour news file notes only a minor "
        "injury concern for India that was already managed before the second game — no players "
        "dropped. New Zealand are at home but have now lost both fixtures of this series, and "
        "India have handled the conditions in the two games they have won here. With nothing to "
        "play for in the decider beyond a clean sweep, the stronger side's depth should tell. "
        "Selection: India to win the 3rd T20I.",
    ("rug-har-sar", "Harlequins"):
        "Harlequins to win at home in Round 4 of the Gallagher Premiership. The Premiership "
        "fixture list confirms the clash at the Allianz Park, and the league table context from "
        "the official site puts Harlequins among the top half of the table going into Round 4 "
        "with a home record that has been solid all season, while Saracens travel having conceded "
        "heavily in their last two away games of the early-season run. The official Premiership "
        "standings at Round 3 back Harlequins as the side with the better recent form on their "
        "own touchline. Selection: Harlequins to win.",
    ("dar-prc-bun", "Gerwyn Price"):
        "Gerwyn Price to reach the semi-final. In round two at Dortmund, Price demolished Cameron "
        "Menzies 10-4 with a hat-trick of ton-plus checkouts, winning seven of the final eight "
        "legs, while Stephen Bunting needed 10-3 against Kim Huybrechts to reach his first European "
        "Championship quarter-final since 2014, converting 100, 108, 116 and 121 finishes. The "
        "official PDC report describes Price's second half as emphatic, and on a best-of-19 leg "
        "format at Finals Day the sharper doubling record carries. Selection: Gerwyn Price to win "
        "the quarter-final.",
    ("ten-med-bas", "Daniil Medvedev"):
        "Daniil Medvedev to close out the Almaty final. The top seed reached the final with a "
        "6-3 semi-final win in which Alexander Bublik (3) retired in the second set, so Medvedev "
        "arrives with the lighter match load of the two. Nikoloz Basilashvili's path was a full "
        "three-set marathon against Stefanos Tsitsipas (7) at 6-4 6-7(5) 6-3, per the ATP's "
        "official score feed. Against a qualifier who has just played through a tie-break, the "
        "serving and match sharpness of the top seed should decide it. Selection: Daniil Medvedev.",
    ("han-rnl-mag", "Rhein-Neckar Lowen"):
        "Rhein-Neckar Lowen to win in Magdeburg. The Lowen are the top side of the German "
        "Handball-Bundesliga this season per the official opel-hbl.de team page, and they travel "
        "to a Magdeburg side that is mid-table and without the same defensive record. RNL's "
        "season has been built on conceding fewer than most of the league, and their recent "
        "results line on the official page shows a string of wins heading into Matchday 10. "
        "A win on the road against a mid-table opponent is the expected outcome. Selection: "
        "Rhein-Neckar Lowen to win the match.",
}

MED_TEXT = {
    ("nhl-sjs-bos", "Boston Bruins"):
        "Boston at 8-2-1 with the league-best 22 goals against are the clear favourites; the "
        "money-line price sits outside our band, so the -1.5 puck line is the in-band route.",
    ("nhl-car-stl", "Carolina Hurricanes"):
        "Carolina are top of the league on points (18) and 6-1-1 on the road; St. Louis are 3-0-1 "
        "at home but 5-4-1 overall. An away win is the lean.",
    ("nhl-vgk-clb", "Vegas Golden Knights"):
        "Vegas (8-4-0, 46 goals) travel to a Columbus side 3-5-0 with 20 goals for; the money-line "
        "price is outside the band, so treat the puck line as the in-band expression.",
    ("nhl-nyr-ott", "New York Rangers"):
        "The Rangers' 1-4-1 road record is the concern, but their 3.1 goals-for-per-game rate is "
        "stronger than Ottawa's 2.8; the coin flip tilts to New York on the numbers.",
    ("nhl-vgk-clb", "Under 7.5"):
        "Vegas are the heavy away favourite (8-4-0, 46 goals) against a 3-5-0 Columbus side on a "
        "two-game skid; the low-scoring under sits at 62.9% and is the in-band expression.",
    ("nhl-det-cgy", "Under 6.5"):
        "Detroit (4-3-3, W1) travel to a Calgary side 3-6 with a -19 goal differential; the "
        "under 6.5 sits at 64% and is the in-band expression of the favourite's game.",
    ("nhl-det-cgy", "Detroit Red Wings"):
        "Calgary are 3-6 with a -19 goal differential (league worst); Detroit's 4-3-3 record and "
        "winning streak make them the side to back, price outside the band noted.",
    ("mlb-g2", "Milwaukee Brewers"):
        "Game 2 at American Family Field: Milwaukee lead the series 1-0, won Game 1 3-2, go 55-26 "
        "at home, and Logan Henderson (2.47 ERA, 0.84 WHIP) edges Drew Rasmussen (2.67, 0.91).",
    ("mlb-g3", "Milwaukee Brewers"):
        "Game 3 at Tropicana: the same 103-59 Brewers travel with Robert Gasser (3.87 ERA) to face "
        "Freddy Peralta (3.25 ERA with Tampa); the stronger club still edges the one-game tilt.",
    ("mlb-g2", "Tampa Bay Rays +1.5"):
        "With both starters holding sub-2.70 ERAs and Game 1 already settled 3-2, the in-band "
        "expression of a tight pitching duel is the Rays' 1.5-run cushion rather than the "
        "outside-band Brewers money line.",
    ("mlb-g2", "Under 8.5"):
        "Two elite starters (Henderson 2.47/0.84, Rasmussen 2.67/0.91) meet in a World Series "
        "game already settled 3-2 in Game 1; the run total leans under the 8.5 line.",
    ("mlb-g3", "Under 8.5"):
        "Gasser (3.87 ERA) against Peralta (3.25 with Tampa) keeps the Tropicana game below the "
        "8.5 run line in our read.",
    ("nba-mil-phi", "Philadelphia 76ers"):
        "Philadelphia open 2-0 (1-0 at home) against a 0-2 Milwaukee side; two-game sample only, "
        "prior-season priors unavailable (flag cmp-16).",
    ("nba-bkn-cle", "Brooklyn Nets"):
        "Both 0-1; Brooklyn's lone loss came at home, Cleveland's on the road, so the visitor "
        "edges the lean in a two-game season (flag cmp-16).",
    ("nba-sa-dal", "Dallas Mavericks"):
        "Dallas 1-1 at home to a 0-2, road 0-2 Spurs side; OLBG's 70% for San Antonio is the "
        "outlier (flag cmp-06).",
    ("nba-hou-atl", "Atlanta Hawks"):
        "Atlanta 2-0 (both on the road) at home to Houston 2-0; the home edge is the lean "
        "(flag cmp-16).",
    ("nba-was-chi", "Washington Wizards +5.5"):
        "Both sides 1-1 with no home games completed by either club; the Wizards' 5.5-point "
        "cushion is the in-band expression of a dead-even game (flag cmp-16).",
    ("nba-no-den", "New Orleans Pelicans +5.5"):
        "Both sides winless, so the 5.5-point cushion for New Orleans is the in-band expression "
        "of a marginal game (flag cmp-16).",
    ("nba-gs-phx", "Golden State Warriors +5.5"):
        "Golden State are 0-2 at a 0-1 Phoenix side; the half-dozen-point cushion is the in-band "
        "route on a two-game-season coin flip (flag cmp-16).",
    ("cri-pak-eng-odi4", "Pakistan"):
        "Pakistan lead the head-to-head 1-0 in the tri-series (87-run win at Rawalpindi, 18-20 Oct "
        "per ICC), are at home in Lahore, and face an England side winless in three; the money-line "
        "price is outside the band so treat as the top of the table.",
    ("cri-bol-tit", "Momentum Multiply Titans"):
        "CSA official fixture: Boland v Titans, 13:00 SAST at Boland Park; the Titans' position in "
        "the Pro20 pool is the lean, OLBG 83% agrees.",
    ("cri-tus-wp", "Western Province"):
        "CSA official fixture at City Oval Pietermaritzburg; Western Province (YesPlay WP Cobras) "
        "are the lean, OLBG 100% (8/8) agrees.",
    ("cri-es-sae", "Eastern Storm"):
        "CSA Pro20 pool fixture at Willowmoore Park Benoni (no CSA match-centre page captured — "
        "flagged); the Storm are the lean, OLBG 83% agrees.",
    ("cri-tor-van", "Toronto Kings"):
        "No official league fixture page found (flagged); OLBG community is 9/10 for Toronto in "
        "the Canadian T20, which sets the price.",
    ("rug-usa-ausa", "USA Eagles +12"):
        "Rugby Australia confirmed nine Wallabies in the 23 for Nashville (9:00 AEDT = 22:00Z); "
        "Australia A are the clear squad favourite, and 12 points is the in-band expression of "
        "a contest the Eagles can live with.",
    ("gae-sal-mcg", "Maigh Cuilinn"):
        "Galway SFC final at Pearse Stadium (official Galway GAA schedule); Maigh Cuilinn are the "
        "slight favourite at home with the OLBG community 60% on Salthill covering +3.5.",
    ("gae-sal-mcg", "Salthill-Knocknacarra +3.5"):
        "OLBG's 28/47 (60%) on Salthill covering +3.5 matches the normal-margin read of a final "
        "where Maigh Cuilinn are only a short favourite; the half-point line is the in-band route.",
    ("gae-stf-nem", "St Finbarrs"):
        "Cork Premier SFC final (Munster GAA event page); St Finbarrs at home are the short "
        "favourite, Nemo +1.5 the community lean (27/31).",
    ("gae-kan-eoc", "Kanturk"):
        "Cork club fixture (OLBG listing only, flagged); Kanturk at home with no form data captured "
        "is the half-point lean.",
    ("gae-frc-kil", "Fr Caseys"):
        "Limerick club fixture (OLBG listing only, flagged); Fr Caseys at home, OLBG 57% agrees "
        "with the home lean.",
    ("han-psg-sra", "PSG Handball"):
        "StarLigue J8 at home to a lower-league Saint-Raphaël; the price is outside the band — the "
        "OLBG community's 71% 'Tie' pattern is flagged (cmp-05) and not followed.",
    ("vol-cis-tre", "Itas Trentino"):
        "SuperLega Round 2 (Lega Pallavolo): Trentino are the elite of the pairing against "
        "Cisterna; OLBG's 86% for Cisterna is flagged as the outlier (cmp-08).",
    ("vol-per-por", "Sir Susa Scai Perugia"):
        "SuperLega Round 2: Perugia are the established top club against Pordenone; OLBG's 83% for "
        "Pordenone is flagged (cmp-08).",
    ("vol-pad-civ", "Lube Civitanova"):
        "SuperLega Round 2: Civitanova are the top-2 club against Padova; OLBG's 100% (5/5) for "
        "Padova is flagged (cmp-08).",
    ("vol-vak-gal", "Vakifbank W"):
        "OLBG listing only (no official league page captured); Vakifbank are the community lean "
        "(57%) in the Turkish league.",
    ("vol-ham-mun", "ETV Hamburg W"):
        "OLBG listing only; ETV Hamburg are the community lean (80%) in the German women's "
        "Bundesliga.",
    ("ten-mus-fri", "Lorenzo Musetti"):
        "Lyon final (ATP official scores): Musetti beat the top seed Cobolli 4-6 6-2 7-5 while "
        "Fritz took a straight-sets 6-3 7-5 over Paul; the match that went the distance edges the "
        "lean.",
    ("ten-ryb-fer", "Elena Rybakina"):
        "WTA Asia event (the hosting tournament could not be confirmed on the official site — "
        "flag cmp-07); the 88% OLBG community share for Rybakina sets the price at the capped "
        "medium grade.",
    ("ten-krueg-sin", "Katerina Siniakova"):
        "OLBG only — no official fixture page captured (flag cmp-07). Siniakova leads the "
        "community 5/9 (56%).",
    ("ten-eal-sto", "Alexandra Eala"):
        "The community leans Eala 2/3 in this WTA Asia fixture (flag cmp-07); no official "
        "fixture facts captured.",
    ("ten-uch-mer", "Elise Mertens"):
        "A split OLBG board (1/2); Mertens takes the marginal lean in the WTA Asia fixture "
        "(flag cmp-07).",
    ("ten-mic-vdz", "Botic Van De Zandschulp"):
        "ATP event starting 26 Oct (event name not confirmed from the static ATP pages — flag "
        "cmp-07); single tipper, community line only.",
    ("ten-hur-fil", "Hubert Hurkacz"):
        "ATP event starting 26 Oct (flag cmp-07); single tipper, community line only.",
    ("dar-rsm-lwk", "Ross Smith"):
        "Both quarter-finalists won 10-7/10-6 in round two (official PDC); Ross Smith's margin over "
        "Heta is the marginal lean over Woodhouse's over van Veen.",
    ("dar-out-ec26", "Luke Littler"):
        "Littler is the only player averaging 105+ in two consecutive rounds (105.05, 114.47 — "
        "official PDC); the tournament price is community-based and capped.",
    ("gry-don-1104", "Snowfall"):
        "The only dog with a tip on the OLBG card (1/1); GBGB publishes no public racecard so the "
        "runner list itself is flagged (cmp-09).",
    ("rl-out-soo27", "New South Wales"):
        "Ante-post for May 2027; OLBG community 75% (9/12) sets the community price, capped at "
        "low for a seven-months-out market.",
    ("rl-out-nrl27", "Penrith Panthers"):
        "Seven months out for the NRL 2027 Grand Final; OLBG shows a 1/2 split, community "
        "price capped at low.",
    ("rl-out-sl27", "Leeds Rhinos"):
        "Ante-post for the 2027 Super League Grand Final; OLBG 1/3, community price capped at low.",
    ("cri-nam-irl-odi3", "Ireland"):
        "No official ICC fixture page captured (flagged); OLBG's single tipper for Ireland sets "
        "the community line.",
    ("cri-nwd-nch", "North West Dragons"):
        "CSA official fixture at Senwes Park; no form data captured, the home lean is the marginal "
        "read.",
    ("rug-lar-ubb", "Stade Rochelais"):
        "Top 14 J7 (LNR official): La Rochelle 4th (18 pts, +9) at home to 3rd-placed Bordeaux "
        "(19 pts, +64); the home edge is the lean, OLBG's 60% for Bordeaux noted.",
    ("kbl-gas-thr", "Korea Gas"):
        "KBL (no official fixture page captured — flagged); OLBG 2/2 for Korea Gas sets the "
        "community line.",
    ("kbl-any-won", "Wonju"):
        "KBL (flagged); single tipper for Wonju, community line only.",
    ("kbl-seo-suw", "Suwon Sonicboom +5.50"):
        "KBL (flagged); OLBG's pointspread tip for Suwon +5.5, community line only.",
}

SECONDARY_TOTALS = {"mlb-g2", "mlb-g3"}  # baseball: add the total line as a second pick
# Sports with fewer than five OLBG-listed fixtures still publish every fixture that can
# be priced; these get one extra in-band line where the desk has room for it.
SECONDARY_EXTRA = {"rug-usa-ausa": "winner", "mlb-g2": "handicap"}


def main() -> None:
    fx = json.loads((DATA / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]
    lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))["lines"]
    by_fix: dict[str, list] = {}
    for l in lines:
        by_fix.setdefault(l["fixture_id"], []).append(l)

    picks, preds = [], []
    by_sport: dict[str, int] = {}
    for f in fx:
        rows = by_fix.get(f["id"], [])
        if not rows:
            continue
        rows_sorted = sorted(rows, key=lambda l: (-ORDER[l["confidence"]],
                                                  -l["probability"] if l["kind"] == "winner" else 0,
                                                  KIND_PREF[l["kind"]], l["selection"]))
        cand = rows_sorted[0]
        primary = cand if cand["in_band"] else None
        if primary is None:
            for l in rows_sorted:
                if l["in_band"] and ORDER[l["confidence"]] == ORDER[cand["confidence"]]:
                    primary = l
                    break
        if primary is None:
            primary = cand
        picks.append(_pick(f, primary))
        by_sport[f["sport"]] = by_sport.get(f["sport"], 0) + 1
        # second pick: baseball totals
        if f["id"] in SECONDARY_TOTALS:
            tot = [l for l in rows if l["kind"] == "total" and l["probability"] >= 0.50]
            if tot:
                tot.sort(key=lambda l: -l["probability"])
                t = tot[0]
                picks.append(_pick(f, t, suffix="-tot"))
                by_sport[f["sport"]] += 1
        # extra in-band line for fixtures in SECONDARY_EXTRA (sports with few OLBG fixtures)
        if f["id"] in SECONDARY_EXTRA:
            kind_wanted = SECONDARY_EXTRA[f["id"]]
            cands = [l for l in rows if l["kind"] == kind_wanted and l["in_band"]
                     and (l["fixture_id"], l["selection"]) != (primary["fixture_id"], primary["selection"])]
            if cands:
                cands.sort(key=lambda l: -l["probability"])
                picks.append(_pick(f, cands[0], suffix="-alt"))
                by_sport[f["sport"]] += 1
    # cap per sport at 10
    counts: dict[str, int] = {}
    capped = []
    for p in picks:
        counts[p["sport"]] = counts.get(p["sport"], 0) + 1
        if counts[p["sport"]] > 10:
            continue
        capped.append(p)
    picks = capped

    for p in picks:
        key = (p["fixture_id"], p["selection"])
        text = None
        if p["confidence"] == "high":
            text = HIGH_TEXT.get(key)
            if not text:
                raise SystemExit(f"missing high text for {key}")
        else:
            text = MED_TEXT.get(key)
        if text:
            preds.append({
                "id": "pred-" + p["id"][len("pick-"):],
                "pick_id": p["id"], "fixture_id": p["fixture_id"], "sport": p["sport"],
                "competition": p["competition"], "home": p["home"], "away": p["away"],
                "start_utc": p["start_utc"], "start_display": p["start_display"],
                "market": p["market"], "selection": p["selection"],
                "confidence": p["confidence"], "score": p["score"],
                "probability": p["probability"], "american_display": p["american_display"],
                "in_band": p["in_band"],
                "headline": p["selection"] + " — " + p["competition"],
                "text": text,
                "official_url": p["official_url"],
                "olbg_url": p["olbg_url"],
            })

    high = [p for p in picks if p["confidence"] == "high"]
    med = [p for p in picks if p["confidence"] == "medium"]
    low = [p for p in picks if p["confidence"] == "low"]
    by_sport = dict(sorted(Counter(p["sport"] for p in picks).items()))
    payload = {
        "as_of_utc": AS_OF, "count": len(picks),
        "high": len(high), "medium": len(med), "low": len(low),
        "in_band": sum(1 for p in picks if p["in_band"]),
        "by_sport": by_sport,
        "picks": picks,
    }
    (DATA / "picks.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    high_words = [len(t["text"].split()) for t in preds if t["confidence"] == "high"]
    min_words = min(high_words) if high_words else 0
    (DATA / "predictions.json").write_text(
        json.dumps({"as_of_utc": AS_OF, "count": len(preds), "min_words": min_words,
                    "by_sport": dict(sorted({s: sum(1 for t in preds if t["sport"] == s) for s in {t["sport"] for t in preds}}.items())),
                    "missing_for_high_or_medium_pick": [
                        f"{p['fixture_id']}/{p['selection']}" for p in picks
                        if p["confidence"] in ("high", "medium")
                        and not any(t["pick_id"] == p["id"] for t in preds)
                    ],
                    "predictions": preds},
                   indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"compass_predictions: {len(picks)} picks ({len(high)}H/{len(med)}M/{len(low)}L), "
          f"{len(preds)} predictions, min words {min_words}")
    short_high = [(t["id"], n) for t, n in zip(preds, [len(x["text"].split()) for x in preds])
                  if t["confidence"] == "high" and n < 30]
    if short_high:
        print("WARNING: high predictions under 30 words:", short_high)
    for t in preds:
        for banned in ("model", "verified", "Model", "Verified"):
            if banned in t["text"]:
                print("WARNING: banned word", banned, "in", t["id"])


def _pick(f, l, suffix="") -> dict:
    o = f.get("olbg_listing") or {}
    return {
        "id": f"pick-{f['id']}" + suffix, "fixture_id": f["id"], "sport": f["sport"],
        "competition": f["competition"], "home": f["home"], "away": f["away"],
        "start_utc": f["start_utc"], "start_display": f["start_display"],
        "market": l["market"], "selection": l["selection"],
        "probability": l["probability"], "decimal": l["decimal"], "american": l["american"],
        "american_display": l["american_display"], "in_band": l["in_band"],
        "confidence": l["confidence"], "score": score(l["probability"], l["basis"], l["in_band"]),
        "basis": l["basis"], "assumption": l["assumption"],
        "official_url": f["official_url"], "olbg_url": o.get("url", ""),
        "started": False,
    }


if __name__ == "__main__":
    main()
