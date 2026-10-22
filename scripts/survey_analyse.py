#!/usr/bin/env python3
"""Turn originated survey lines into picks, confidence labels, human predictions
and flags — strictly citing official governing-body sources only.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "survey"
DIVERGENCE_CAP = 15.0

lines_doc = json.loads((DATA / "lines.json").read_text())
lines = lines_doc["lines"]
FORM = lines_doc["verified_inputs"]["form"]

_inventory = {}
for f in sorted((DATA / "events").glob("*.json")):
    for e in json.loads(f.read_text()):
        _inventory[(f.stem, e["match"])] = e

for rec in lines:
    row = _inventory.get((rec["sport"], rec["match"]))
    if row:
        rec["olbg_source"] = row["source_url"]
        rec["olbg_listed_time"] = row["listed_time"]
        rec["olbg_market"] = row["market"]
        rec["olbg_top_selection"] = row.get("top_selection")
        rec["olbg_tips"] = (f"{row['tips_for']}/{row['tips_total']}"
                            if row.get("tips_for") is not None else None)
        rec["olbg_tip_pct"] = row.get("tip_pct")
        rec["as_of"] = row["as_of"]
        rec["retrieved_via"] = row["retrieved_via"]
    else:
        rec["olbg_source"] = None
        rec["join_warning"] = "No matching inventory row found"

OFFICIAL_CROSS_REF = {
    "Toulouse v Perpignan": {
        "home": 83.06, "away": 15.32, "draw": 1.61,
        "source": "https://top14.lnr.fr/club/toulouse",
        "as_of": "2026-10-21",
        "kickoff_local": "2026-10-24 16:35 (French local)",
        "venue": "Stade Ernest-Wallon, Toulouse",
        "fixture_source": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan",
    },
    "La Rochelle v Bordeaux": {
        "home": 46.24, "away": 53.18, "draw": 0.58,
        "source": "https://top14.lnr.fr/club/la-rochelle",
        "as_of": "2026-10-21",
        "kickoff_local": "2026-10-25 21:05 (French local)",
        "venue": "Stade Marcel-Deflandre, La Rochelle",
        "corroborated_by": "https://top14.lnr.fr/club/bordeaux-begles",
    },
}


def fair_american(prob):
    """Fair no-vig American price of a probability (the published convention)."""
    if prob >= 0.5:
        return round(-100.0 / (1.0 / prob - 1.0))
    return round((1.0 / prob - 1.0) * 100.0)


def in_focus_band(prob):
    """The brief's -250..+10000 window on the fair no-vig price."""
    return -250 <= fair_american(prob) <= 10000


def confidence(rec):
    p, tier = rec.get("pick_probability"), rec.get("tier")
    if p is None or tier in (None, "none"):
        return "unverified", []
    notes = []
    rec["official_cross_ref"] = OFFICIAL_CROSS_REF.get(rec["match"])
    xref = rec["official_cross_ref"]
    capped = False
    if xref:
        ours = p * 100.0
        side = rec.get("pick")
        official = xref["home"] if side == rec.get("side_a") else xref["away"]
        div = abs(ours - official)
        rec["official_divergence_pp"] = round(div, 2)
        notes.append(f"LNR publishes {official}% for {side}; our line is {ours:.2f}% "
                     f"(divergence {div:.2f} pp).")
        if div > DIVERGENCE_CAP:
            capped = True
            notes.append(f"Divergence exceeds the {DIVERGENCE_CAP} pp cap, so confidence is "
                         f"capped at LOW and the disagreement is flagged for review.")

    if capped:
        return "low", notes
    # Uniform window rule (all layers): high requires p >= 0.72, or p >= 0.70
    # with the fair no-vig price inside [-250, +10000]. Never high below 0.70.
    if tier in ("tier1", "tier2") and rec.get("form_verified") and (
        p >= 0.72 or (p >= 0.70 and in_focus_band(p))
    ):
        return "high", notes
    if tier in ("tier1", "tier2") and p >= 0.60:
        return "medium", notes
    return "low", notes


for rec in lines:
    c, notes = confidence(rec)
    rec["confidence"] = c
    rec["confidence_notes"] = notes

PREDICTIONS = [
    {
        "id": "P-01",
        "match": "Toulouse v Perpignan",
        "sport": "rugby_union",
        "competition": "Top 14, Journée 7",
        "kickoff": "Saturday 24 October 2026, 16:35 French local time",
        "venue": "Stade Ernest-Wallon, Toulouse",
        "venue_source": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan",
        "selection": "Toulouse to win the match (Win Match / 1X2 moneyline)",
        "confidence": "high",
        "text": (
            "Back Stade Toulousain on the match-winner line at Stade Ernest-Wallon on Saturday afternoon. "
            "Official Ligue Nationale de Rugby standings place Toulouse top of the Top 14 on 24 points from "
            "six matches (five wins, one loss, 197 points scored, 124 conceded, +73) riding a five-match league "
            "winning streak plus a 60-14 Champions Cup victory over Sale Sharks. Ninth-placed Perpignan sit on "
            "13 points (3W-0D-3L, -33 points difference) heading into Toulouse."
        ),
        "facts_used": [
            ("Stade Toulousain 1st in Top 14 after J6: 24 pts, 5W-0D-1L, 197 PF, 124 PA (+73)", "https://top14.lnr.fr/classement"),
            ("Toulouse on 5 straight Top 14 wins plus 60-14 Champions Cup win vs Sale Sharks", "https://top14.lnr.fr/club/toulouse"),
            ("USA Perpignan 9th in Top 14 after J6: 13 pts, 3W-0D-3L, 166 PF, 199 PA (-33)", "https://top14.lnr.fr/classement"),
            ("Journée 7 fixture confirmed for Saturday 24 October 2026 at 16:35, Stade Ernest-Wallon", "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan"),
        ],
    },
    {
        "id": "P-02",
        "match": "Bulls v Ulster",
        "sport": "rugby_union",
        "competition": "United Rugby Championship, Round 4",
        "kickoff": "Saturday 24 October 2026, 07:45 local",
        "venue": "Loftus Versfeld, Pretoria",
        "venue_source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/vodacom-bulls-vs-ulster-rugby-2026-10-24/292611",
        "selection": "Bulls to win the match (Win Match / 1X2 moneyline)",
        "confidence": "high",
        "text": (
            "Take Vodacom Bulls to win the Round 4 match-winner market against Ulster at Loftus Versfeld. "
            "The official URC table shows Pretoria's Bulls third on 11 points (2W-0D-1L) leading the entire "
            "championship in attack with 126 points scored against just 54 conceded (+72), fresh off a 57-15 "
            "rout of the Lions on 10 October. Ulster arrive winless at 0W-2D-1L (88 for, 93 against) after "
            "drawing 26-26 with Munster."
        ),
        "facts_used": [
            ("Vodacom Bulls 3rd in URC after Round 3: 11 pts, 2W-0D-1L, 126 PF, 54 PA (+72)", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
            ("Bulls defeated Lions 57-15 on 10 October 2026", "https://stats.unitedrugby.com/match-centre/2026-27/4"),
            ("Ulster 11th in URC at 0W-2D-1L (8 pts, 88 PF, 93 PA) after 26-26 draw vs Munster", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
        ],
    },
    {
        "id": "P-03",
        "match": "Stormers v Scarlets",
        "sport": "rugby_union",
        "competition": "United Rugby Championship, Round 4",
        "kickoff": "Saturday 24 October 2026, 10:00 local",
        "venue": "DHL Stadium, Cape Town",
        "venue_source": "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/dhl-stormers-vs-scarlets-2026-10-24/292612",
        "selection": "Stormers to win the match (Win Match / 1X2 moneyline)",
        "confidence": "high",
        "text": (
            "Back DHL Stormers to beat Scarlets at DHL Stadium in Saturday's URC Round 4 contest. "
            "Cape Town's Stormers hold fourth spot on 11 points (2W-0D-1L) with the league's joint-best "
            "defensive record of 54 points conceded across three rounds (81 scored, +27) after beating "
            "the Sharks 39-22 on 10 October. Scarlets sit twelfth at 1W-0D-2L with 68 scored and 85 conceded (-17)."
        ),
        "facts_used": [
            ("DHL Stormers 4th in URC after Round 3: 11 pts, 2W-0D-1L, 81 PF, 54 PA (+27)", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
            ("Stormers beat Sharks 39-22 on 10 October 2026", "https://stats.unitedrugby.com/match-centre/2026-27/4"),
            ("Scarlets 12th in URC at 1W-0D-2L (7 pts, 68 PF, 85 PA)", "https://stats.unitedrugby.com/match-centre/table/2026-27"),
        ],
    },
    {
        "id": "P-04",
        "match": "Luke Littler vs William O'Connor",
        "sport": "darts",
        "competition": "2026 PDC European Championship, Round 1",
        "kickoff": "Friday 23 October 2026, 15:15",
        "venue": "Westfalenhalle, Dortmund",
        "venue_source": "https://www.pdc.tv/rankings",
        "selection": "Luke Littler to win the match (Win Match 2-way)",
        "confidence": "high",
        "text": (
            "Luke Littler is a strong selection on the 2-way match-winner market against William O'Connor "
            "in Friday's European Championship first round in Dortmund. On the official PDC Werner Ranking "
            "Ladder, World No. 1 Littler sits on £3,113,500 across the two-year cycle — more than eleven "
            "times World No. 32 O'Connor's £274,500 haul — creating clear separation across a race to six legs."
        ),
        "facts_used": [
            ("Luke Littler ranked PDC World No. 1 with £3,113,500 two-year prize money", "https://www.pdc.tv/rankings"),
            ("William O'Connor ranked PDC World No. 32 with £274,500 two-year prize money", "https://www.pdc.tv/rankings"),
        ],
    },
    {
        "id": "P-05",
        "match": "Nathan Aspinall vs Cristo Reyes",
        "sport": "darts",
        "competition": "2026 PDC European Championship, Round 1",
        "kickoff": "Friday 23 October 2026, 14:15",
        "venue": "Westfalenhalle, Dortmund",
        "venue_source": "https://www.pdc.tv/rankings",
        "selection": "Nathan Aspinall to win the match (Win Match 2-way)",
        "confidence": "high",
        "text": (
            "Side with Nathan Aspinall on the 2-way match-winner line against qualifier Cristo Reyes in "
            "Friday's Dortmund opener. Official PDC standings place Aspinall eleventh in the world on "
            "£579,500 over two seasons, sixty places and nearly half a million pounds ahead of No. 71 "
            "Reyes on £95,000, giving Aspinall decisive leg-winning depth over best-of-eleven legs."
        ),
        "facts_used": [
            ("Nathan Aspinall ranked PDC World No. 11 with £579,500 two-year prize money", "https://www.pdc.tv/rankings"),
            ("Cristo Reyes ranked PDC World No. 71 with £95,000 two-year prize money", "https://www.pdc.tv/rankings"),
        ],
    },
]

for p in PREDICTIONS:
    rec = next(r for r in lines if r["match"] == p["match"])
    p["our_probability"] = rec["pick_probability"]
    wm = next(m for m in rec["markets"] if m["name"].startswith("Win Match"))
    p["our_fair_odds"] = wm["our_fair_odds_a"] if rec["pick"] == rec["side_a"] else wm["our_fair_odds_b"]
    if rec.get("official_cross_ref"):
        p["official_cross_ref"] = (
            f"LNR publishes {rec['official_cross_ref']['home']}% home / "
            f"{rec['official_cross_ref']['away']}% away / {rec['official_cross_ref']['draw']}% draw."
        )
    p["confidence"] = rec["confidence"]
    p["word_count"] = len(p["text"].split())
    p["olbg_source"] = rec.get("olbg_source")
    p["retrieved"] = "2026-10-21"
    am = fair_american(p["our_probability"])
    p["fair_american"] = am
    p["price_band"] = "in-band" if -250 <= am <= 10000 else "outside-band"

picks = []
for rec in lines:
    picks.append(dict(
        sport=rec["sport"], match=rec["match"], competition=rec.get("competition"),
        tier=rec["tier"], pick=rec.get("pick"), pick_probability=rec.get("pick_probability"),
        confidence=rec["confidence"], confidence_notes=rec.get("confidence_notes", []),
        official_divergence_pp=rec.get("official_divergence_pp"),
        form_verified=bool(rec.get("form_verified")),
        retrieved="2026-10-21",
    ))

flags = [
    dict(id="F-01", severity="environment", area="collection",
         title="Sandbox bash egress is restricted; all primary feeds fetched via fetch_page",
         detail="Direct curl to sports domains is blocked in bash; every OLBG hub and governing-body table was read live on 2026-10-21 via fetch_page.",
         action="Documented for reproducibility."),
    dict(id="F-02", severity="data-availability", area="odds",
         title="OLBG injects bookmaker decimal odds client-side",
         detail="SSR HTML on OLBG event pages serves market labels and tip counts with empty price slots ('WIN @').",
         consequence="All lines are originated independently from official governing-body data rather than de-vigged bookmaker odds.",
         action="None required."),
    dict(id="F-03", severity="scope-decision", area="exclusions",
         title="Gaelic Football (id 25) and Greyhounds (id 28) included in eligible 17-sport inventory; unlined without public ratings",
         detail="Both sports are active on OLBG and not among the 10 excluded brief terms. Their 11 live markets are inventoried with official GAA/GBGB links and left unlined because no public quantitative rating table exists.",
         action="Aligned across Root (/), Survey (/survey/), and Verified (/verified/)."),
    dict(id="F-05", severity="scope-decision", area="exclusions",
         title="Hurling (id 26) and UFC/MMA (id 27) active on OLBG and explicitly blocked",
         detail="Live inspection of OLBG confirmed active hubs at /betting-tips/Hurling/26 and /betting-tips/UFC_MMA/27; both are explicitly excluded per project scope.",
         action="Enforced in data/survey/sports.json and data/verified/sports.json."),
    dict(id="F-07", severity="data-availability", area="cricket",
         title="Cricket left unoriginated after removing unverified third-party mirrors",
         detail="Earlier survey runs relied on ESPNcricinfo, ESPN, Wikipedia, and TheSportsEncounter and contained an internal 200-run vs 81-run scorecard contradiction. Because official icc-cricket.com renders team ratings and scorecards client-side, all cricket rows are left blank rather than sourced from third-party sites.",
         action="Consult official ICC data feeds when server-rendered."),
    dict(id="F-14", severity="model-divergence", area="rugby-union",
         title="La Rochelle v Bordeaux capped at LOW against official LNR club win probability",
         detail="LNR club pages publish 46.24% La Rochelle / 53.18% Bordeaux / 0.58% draw versus our points-difference logistic output; divergence exceeds 15 pp so confidence is capped at LOW.",
         action="Retained as automatic divergence safeguard."),
]

modelled = {(r["sport"], r["match"]) for r in lines}
REASON = {
    "tennis": "One or both players sit outside SSR ATP Top-100 singles rankings or on client-rendered WTA rankings (https://www.atptour.com/en/rankings/singles).",
    "cricket": "Official icc-cricket.com renders team ratings and match scorecards client-side; third-party mirrors refused.",
    "snooker": "One or both players rank outside WST's server-rendered Top 36 (https://www.wst.tv/rankings/).",
    "golf": "Tournament field strokes-gained distribution not available on static PGA/DP World Tour schedule pages.",
    "basketball": "Full NHL/NBA/EuroLeague/EuroCup multi-market originations published on /verified/sports/basketball.html.",
    "ice_hockey": "Full 16-game NHL multi-market originations published on /verified/sports/ice-hockey.html.",
    "handball": "Full 12-game EHF Champions League multi-market originations published on /verified/sports/handball.html.",
    "volleyball": "Polish PlusLiga clubs sit at M=1 match played and plusliga.pl/table.html cross-redirects to tauronliga.pl.",
    "motor_racing": "Full FIA Formula 1 Round 18 & Championship originations published on /verified/sports/motor-racing.html.",
    "rugby_union": "Pro D2 / URC / Six Nations row; full 23-match Top 14 + Pro D2 + URC card originated on /verified/sports/rugby-union.html.",
    "rugby_league": "2027 off-season antepost futures with no current-season matches played (https://www.nrl.com/draw/).",
    "gaelic_football": "County championship markets lack public official GAA club Elo/points tables (https://www.gaa.ie/football).",
    "greyhounds": "Trap sectional times and form require licensed GBGB data feeds (https://www.gbgb.org.uk).",
}

missing = []
for f in sorted((DATA / "events").glob("*.json")):
    sport = f.stem
    for e in json.loads(f.read_text()):
        if (sport, e["match"]) in modelled:
            continue
        missing.append(dict(
            sport=sport, match=e["match"], market=e["market"],
            listed_time=e["listed_time"], as_of=e["as_of"],
            retrieved_via=e["retrieved_via"], source_url=e["source_url"],
            official_fixture_source=e.get("official_fixture_source"),
            reason=REASON.get(sport, "No verified official basis retrieved in-session."),
        ))

flags.append(dict(
    id="F-15", severity="coverage-gap", area="lines",
    title=f"{len(missing)} inventoried events left blank pending server-rendered official ratings",
    detail="Every unlined row is itemized below with its OLBG listing link, official governing-body link, and exact reason.",
    items=missing,
))

flags.sort(key=lambda f: f["id"])
(DATA / "flags.json").write_text(json.dumps(flags, indent=2, ensure_ascii=False) + "\n")
(DATA / "picks.json").write_text(json.dumps(picks, indent=2, ensure_ascii=False) + "\n")
(DATA / "predictions.json").write_text(json.dumps(PREDICTIONS, indent=2, ensure_ascii=False) + "\n")
(DATA / "lines.json").write_text(json.dumps(lines_doc, indent=2, ensure_ascii=False) + "\n")
print("survey_analyse: picks=", len(picks), "predictions=", len(PREDICTIONS), "unlined=", len(missing))
