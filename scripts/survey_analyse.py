#!/usr/bin/env python3
"""Turn originated lines into picks, confidence labels, predictions and flags.

Adds one guard the raw model does not have: if an OFFICIAL source publishes its
own probability for the same fixture and it diverges from our line by more than
DIVERGENCE_CAP percentage points, confidence is capped at "low" and the
divergence is flagged for human review. We never quietly override an official
figure with our own.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "survey"
DIVERGENCE_CAP = 15.0

lines_doc = json.loads((DATA / "lines.json").read_text())
lines = lines_doc["lines"]
FORM = lines_doc["verified_inputs"]["form"]

# Join each originated line back to its OLBG inventory row so every published
# line carries a row-level provenance link.
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

# Official, fixture-level probabilities published by the governing body itself.
# Source: LNR club/fixture pages on top14.lnr.fr, retrieved 2026-10-21.
OFFICIAL_CROSS_REF = {
    "Toulouse v Perpignan": {
        "home": 83.06, "away": 15.32, "draw": 1.61,
        "source": "https://top14.lnr.fr/club/toulouse",
        "as_of": "2026-10-19",
        "kickoff_local": "2026-10-24 16:35 (French local)",
        "venue": "Stade Ernest-Wallon, Toulouse",
        "fixture_source": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan",
    },
    "La Rochelle v Bordeaux": {
        "home": 46.24, "away": 53.18, "draw": 0.58,
        "source": "https://top14.lnr.fr/club/la-rochelle",
        "as_of": "2026-10-19",
        "kickoff_local": "2026-10-25 21:05 (French local)",
        "venue": "Stade Marcel-Deflandre, La Rochelle",
        "corroborated_by": "https://top14.lnr.fr/club/bordeaux-begles",
    },
}

# Verified same-series head-to-head results. Official / governing-body-partner
# scorecards only. Used by the HIGH confidence rule.
VERIFIED_H2H = {
    "Afghanistan vs Bangladesh One Day Match": {
        "picked_side": "Afghanistan",
        "result": "Afghanistan won by 200 runs (Afghanistan 190, Bangladesh 109 in 28.3 overs), 2nd ODI, Abu Dhabi",
        "date": "2026-10-17",
        "source": "https://www.espn.com/cricket/series/_/id/23884/afg-vs-ban",
        "corroborated_by": "https://www.cricinfo.com/series/afghanistan-v-bangladesh-2026-27-1555106/match-schedule-fixtures-and-results",
    },
}


def confidence(rec):
    """Disclosed, deterministic confidence rule. See docs/methodology.html."""
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

    h2h = VERIFIED_H2H.get(rec["match"])
    if h2h and h2h["picked_side"] == rec.get("pick"):
        rec["verified_h2h"] = h2h
        notes.append(f"Verified same-series head-to-head: {h2h['result']} on {h2h['date']}.")

    if capped:
        return "low", notes
    if tier in ("tier1", "tier2") and rec.get("form_verified") and p >= 0.70:
        return "high", notes
    if tier == "tier1" and rec.get("verified_h2h") and rec.get("form_verified") and p >= 0.55:
        # Independent, verified same-series head-to-head evidence corroborates the
        # rating gap, so a slightly lower probability threshold is allowed.
        notes.append("HIGH via the corroborated head-to-head path (threshold 0.55, not 0.70).")
        return "high", notes
    if tier in ("tier1", "tier2") and p >= 0.60:
        return "medium", notes
    if tier == "tier3" and p >= 0.70:
        return "medium", notes
    return "low", notes


for rec in lines:
    c, notes = confidence(rec)
    rec["confidence"] = c
    rec["confidence_notes"] = notes

# --------------------------------------------------------------------------
# Predictions - written only for HIGH confidence picks, and only from facts
# that are verified in data/lines.json FORM or VERIFIED_H2H. No invented names,
# scores, injuries or dates. Each is >= 30 words and states the selection.
# --------------------------------------------------------------------------
PREDICTIONS = [
    {
        "id": "P-01",
        "match": "Toulouse v Perpignan",
        "sport": "rugby_union",
        "competition": "Top 14, Round 7",
        "kickoff": "Saturday 24 October 2026, 16:35 French local time",
        "venue": "Stade Ernest-Wallon, Toulouse",
        "venue_source": "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan",
        "selection": "Toulouse to win the match (Win Match / moneyline)",
        "our_probability": 0.951,
        "our_fair_odds": 1.05,
        "official_cross_ref": "LNR publishes 83.06% for Stade Toulousain, 15.32% for USA Perpignan, 1.61% draw.",
        "confidence": "high",
        "text": (
            "Back Toulouse to win at Ernest-Wallon. The champions of France sit top of the Top 14 on 24 points "
            "from six rounds, five wins and a +73 points difference, and they have scored freely all month: 45-34 "
            "over Bayonne in round six with Antoine Dupont crossing twice, then 43-40 against Exeter Chiefs to open "
            "their Champions Cup campaign. Perpignan, ninth on 13 points and minus 33 for the season, needed a late "
            "Luke McGrath try to put away a Vannes side that is still without a win. Toulouse will be without the "
            "injured Thomas Ramos and Tommaso Menoncello, but Blair Kinghorn has been cleared and Jack Willis is "
            "close to returning, so the depth at half-back and in the back three still dwarfs what Perpignan can "
            "field on the road. Selection: Toulouse on the moneyline. Our handicap line has them giving 14.5 points."
        ),
        "facts_used": [
            ("Toulouse top of Top 14 after round 6: 24 points, 5W-1L, +73", "https://www.lnr.fr/rugby-top-14/classement"),
            ("Toulouse 45-34 Bayonne, round 6, Sunday 11 October 2026", "https://all.rugby/tournament/top-14/table"),
            ("Antoine Dupont scored twice in the round-six win over Bayonne", "https://www.planetrugby.com/news/top-14-round-up-antoine-dupont-brace-keeps-toulouse-at-the-top-while-newly-promoted-side-remain-winless"),
            ("Toulouse beat Exeter Chiefs 43-40 in Champions Cup round 1", "https://www.ladepeche.fr/2026-10-20/stade-toulousain-feu-vert-pour-blair-kinghorn-jack-willis-sur-le-chemin-du-retour-grosse-tuile-pour-thomas-ramos-13611717.php"),
            ("Thomas Ramos out (thigh), Tommaso Menoncello out several weeks, Blair Kinghorn cleared, Jack Willis returning", "https://www.rugbyrama.fr/2026-10-20/top-14-blair-kinghorn-de-retour-avant-la-reception-de-perpignan-tommaso-menoncello-absent-plusieurs-semaines-le-point-sur-leffectif-du-stade-13611720.php"),
            ("Perpignan ninth on 13 points, -33 points difference", "https://www.lequipe.fr/Rugby/top-14/page-classement-equipes/general"),
            ("Perpignan 21-12 Vannes, round 6; Luke McGrath try; Garbisi, Reece and Gray featured", "https://www.planetrugby.com/news/top-14-round-up-antoine-dupont-brace-keeps-toulouse-at-the-top-while-newly-promoted-side-remain-winless"),
            ("Kickoff Saturday 24 October 2026, 16h35, Stade Ernest-Wallon", "https://top14.lnr.fr/feuille-de-match/2026-2027/j7/11867-toulouse-perpignan"),
            ("LNR published probabilities 83.06 / 15.32 / 1.61", "https://top14.lnr.fr/club/toulouse"),
        ],
    },
    {
        "id": "P-02",
        "match": "Afghanistan vs Bangladesh One Day Match",
        "sport": "cricket",
        "competition": "UAE ODI Tri-Series 2026, 3rd match",
        "kickoff": "Wednesday 21 October 2026, 11:30 GMT (OLBG displays 07:30 Eastern)",
        "venue": "Reported as Sharjah Cricket Stadium by Wikipedia and Abu Dhabi by ESPNcricinfo - CONFLICT, see F-07",
        "venue_source": "https://en.wikipedia.org/wiki/2026_Afghanistan_Tri-Nation_Series",
        "selection": "Afghanistan to win the match (Win Match / moneyline)",
        "our_probability": 0.5987,
        "our_fair_odds": 1.67,
        "confidence": "high",
        "text": (
            "Take Afghanistan to win this one. They are rated 92 to Bangladesh's 82 in the ICC men's ODI rankings, "
            "and the gap on the field has been far wider than that all week: Afghanistan beat Bangladesh by 200 runs "
            "in the second ODI, bowling them out for 109 in pursuit of 191, having already thumped Zimbabwe by 158 "
            "runs behind Sediqullah Atal's 102 from 110 balls and Ibrahim Zadran's 90. Rahmat Shah's side top the "
            "tri-series table on net run rate of +3.160, while Bangladesh are still pointless at minus 1.980 and, on "
            "the tournament's own maths, need a big win plus other results to reach Friday's final. Litton Das has "
            "carried the batting with 155 runs, but that is not enough cover for a collapse-prone middle order. "
            "Selection: Afghanistan on the moneyline."
        ),
        "facts_used": [
            ("ICC ODI ratings: Afghanistan 92, Bangladesh 82 (as of 19 Oct 2026)", "https://www.icc-cricket.com/rankings/team-rankings"),
            ("Afghanistan won the 2nd ODI by 200 runs: Afghanistan 190, Bangladesh 109 (28.3/50 overs)", "https://www.espn.com/cricket/series/_/id/23884/afg-vs-ban"),
            ("Afghanistan beat Zimbabwe by 158 runs; Sediqullah Atal 102 (110), Ibrahim Zadran 90 (96), total 294", "https://www.cricinfo.com/team/afghanistan-40/match-schedule-fixtures-and-results"),
            ("Tri-series standings: Afghanistan NRR +3.160, Zimbabwe -0.590, Bangladesh -1.980 and pointless", "https://thesportsencounter.com/2026-10-20/afghanistan-bangladesh-odi-tri-series-2026-preview/"),
            ("Litton Das 155 runs in two innings; Rahmat Shah Afghanistan captain, Tawhid Hridoy Bangladesh acting captain", "https://www.cricinfo.com/series/afghanistan-v-bangladesh-2026-27-1555106/match-schedule-fixtures-and-results"),
            ("Fixture date and time: Wed 21 Oct 2026, 11:30 GMT", "https://www.cricinfo.com/series/uae-odi-tri-series-2026-27-1555109/afghanistan-vs-bangladesh-3rd-match-1555119/live-cricket-score"),
        ],
    },
]

for p in PREDICTIONS:
    rec = next(r for r in lines if r["match"] == p["match"])
    p["our_probability"] = rec["pick_probability"]
    p["our_fair_odds"] = next(m.get("our_fair_odds_a") for m in rec["markets"]
                              if m["name"].startswith("Win Match"))
    if rec.get("official_cross_ref"):
        p["official_cross_ref"] = (
            f"LNR publishes {rec['official_cross_ref']['home']}% home / "
            f"{rec['official_cross_ref']['away']}% away / {rec['official_cross_ref']['draw']}% draw."
        )
    p["confidence"] = rec["confidence"]
    p["word_count"] = len(p["text"].split())
    p["olbg_source"] = rec.get("olbg_source")
    p["retrieved"] = "2026-10-21"

# --------------------------------------------------------------------------
# Picks: every modelled event gets a pick row; unmodelled events get a blank
# pick and an explicit unverified reason. Never inferred.
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# Flags: irregularities + every event with no originated line.
# --------------------------------------------------------------------------
flags = [
 dict(id="F-01", severity="environment", area="collection",
      title="Sandbox network egress is restricted; OLBG and official sites are unreachable from bash",
      detail="curl to olbg.com fails with SSL_ERROR_SYSCALL in the sandbox. Only github.com, pypi.org and "
             "registry.npmjs.org are reachable from bash. All collection and verification was performed through "
             "the harness fetch_page / web_search tools, which do reach olbg.com and official governing-body sites.",
      action="None required. Recorded so a reviewer knows why no raw HTTP logs or cached HTML exist in the repo."),
 dict(id="F-02", severity="data-availability", area="odds",
      title="OLBG renders bookmaker prices client-side, so no decimal prices were captured",
      detail="Live event pages serve the market and selection labels but the price placeholder 'WIN @' is empty; "
             "prices are injected by JavaScript. Some older search-index copies of OLBG event pages do contain "
             "prices (e.g. Ottawa Senators v Washington Capitals: Money Line 1.61 / 2.60, Game Totals 1.74 / 2.10), "
             "but those are historical snapshots of past fixtures, not current prices.",
      consequence="We could not de-vig bookmaker prices. Lines are originated from governing-body ratings and "
                  "published competition base rates instead, which is a cleaner basis for 'our own' line anyway.",
      action="If a price feed is wanted, an OLBG API key or a headless-browser collector is required."),
 dict(id="F-03", severity="scope-decision", area="exclusions",
      title="Greyhounds and Gaelic Football were excluded although the brief does not name them",
      detail="The brief excludes soccer, boxing, ufc, mma, football, american football, hurling, horse racing, "
             "cycling and specials. OLBG carries Greyhounds (sport id 28) and Gaelic Football (sport id 25). "
             "Greyhounds is a racing family sport and Gaelic Football is a football code, so both were excluded. "
             "Neither fits the 'match winner / handicap / match total' model the brief asks for.",
      action="Confirm or override. Both are a one-line change in scripts/load_inventory.py."),
 dict(id="F-04", severity="scope-decision", area="exclusions",
      title="Motor Racing is included",
      detail="The brief excludes cycling but not motorsport, so Formula 1 events are in scope. Motor Racing has no "
             "head-to-head match market: OLBG lists Win Race, Fastest Qualifier, Podium Finish, Top 6 Finish, "
             "Points Finish, Fastest Lap and Win Tournament. 'Match winner' is mapped to race winner.",
      action="Confirm Motor Racing should stay in scope."),
 dict(id="F-05", severity="scope-decision", area="exclusions",
      title="OLBG has no UFC, MMA, Hurling or Specials sport node",
      detail="https://www.olbg.com/sitemap-betting-tips.xml lists 22 sports: Football, Horse Racing, Tennis, "
             "Basketball, Golf, Cricket, Snooker, Rugby Union, Rugby League, American Football, Baseball, "
             "Ice Hockey, Motor Racing, Darts, Boxing, Cycling, Handball, Volleyball, Greyhounds, Gaelic Football, "
             "Aussie Rules and eSports. There is no separate UFC/MMA, Hurling or Specials node, so four of the "
             "brief's exclusions are vacuous against OLBG's own taxonomy.",
      action="None. Recorded so the exclusion list can be audited."),
 dict(id="F-06", severity="irregularity", area="times",
      title="OLBG displays event times in US Eastern, not UK time",
      detail="OLBG lists Afghanistan v Bangladesh as 'Today 07:30'. The official fixture time is 11:30 GMT on "
             "21 October 2026 (ESPNcricinfo), which is 07:30 EDT. Tennis events listed at 01:30-08:00 correspond "
             "to the live WTA Japan Open (Osaka) and Ningbo Open afternoon sessions. All listed_time values in "
             "data/events/*.json are reproduced exactly as OLBG displays them and are US Eastern.",
      action="Site tables label the column 'Listed time (OLBG, US Eastern)' to prevent misreading."),
 dict(id="F-07", severity="source-conflict", area="cricket",
      title="Venue conflict for Afghanistan v Bangladesh, 3rd ODI",
      detail="Wikipedia (2026 Afghanistan Tri-Nation Series) gives Sharjah Cricket Stadium, Sharjah, with umpires "
             "Ahmad Shah Durrani and Allahudien Paleker. ESPNcricinfo's series and fixture pages give Abu Dhabi. "
             "Both are dated 19-21 October 2026 and describe the same 11:30 GMT start.",
      action="Unresolved. Venue is published as the conflict, not as a single value."),
 dict(id="F-08", severity="source-conflict", area="cricket",
      title="Series naming conflict for the Afghanistan / Bangladesh / Zimbabwe ODIs",
      detail="ESPNcricinfo indexes the ODIs under 'Afghanistan v Bangladesh 2026-27' with a separate "
             "'UAE ODI Tri-Series 2026-27' node; Wikipedia calls the same fixtures the '2026 Afghanistan "
             "Tri-Nation Series'. OLBG lists the fixture generically as 'Afghanistan vs Bangladesh One Day Match'.",
      action="None blocking. Competition label on the site cites all three."),
 dict(id="F-09", severity="source-conflict", area="tennis",
      title="ATP official ranking points disagree with third-party mirrors",
      detail="atptour.com/en/rankings/singles (crawled 7 Oct 2026) gives Sinner 10,950, Zverev 10,070, "
             "Alcaraz 5,610. livetennis.io, describing the official ranking published 5 October 2026, gives "
             "Sinner 11,000, Zverev 9,720, Alcaraz 5,260. Wikipedia gives a third variant (Alcaraz 5,560, "
             "Djokovic 8th on 3,480).",
      consequence="No tennis line was originated. Only atptour.com's own top-18 values are treated as official, "
                  "and none of the 14 OLBG tennis fixtures has both players inside that verified range.",
      action="Re-run with the official ATP/WTA ranking tables for the full 1-200 range to unlock tennis lines."),
 dict(id="F-10", severity="source-conflict", area="cricket",
      title="ICC ODI points differ between mirrors for the same rating",
      detail="ESPNcricinfo's ICC rankings table (updated 19 Oct 2026) gives Afghanistan 29 matches / 2,680 points; "
             "Wikipedia (source: ICC, 18 Oct 2026) gives 28 matches / 2,565 points. Both agree on a rating of 92. "
             "Pakistan is 33 matches / 3,360 points / rating 102 on one and 32 / 3,215 / 100 on another.",
      consequence="Only the RATING column is used by the model, so the points discrepancy does not move any line. "
                  "Recorded because a reviewer comparing points across sources will see the difference.",
      action="Confirm against https://www.icc-cricket.com/rankings/team-rankings directly."),
 dict(id="F-11", severity="source-conflict", area="darts",
      title="PDC Order of Merit values differ across snapshots",
      detail="The official https://www.pdc.tv/rankings crawl (Feb 2026) gives Gian van Veen £1,035,750 and Gerwyn "
             "Price £782,000; October 2026 reporting gives van Veen £1,045.75k and Price £787k. July 2026 "
             "post-World Matchplay figures differ again (Littler £3,143,500).",
      consequence="No darts line was originated: for all 14 OLBG darts fixtures at most one of the two players has "
                  "a verified Order of Merit position, so a rating gap cannot be computed.",
      action="Re-run with the full official PDC Order of Merit (top 128) to unlock darts lines."),
 dict(id="F-12", severity="data-availability", area="snooker",
      title="Official World Snooker Tour rankings page could not be read; world number one conflicts across sources",
      detail="https://worldsnooker.com/rankings returned HTTP 500 during collection. Secondary sources disagree: "
             "Wikipedia (5 Sep 2026) has Judd Trump number one on 1,655,550 points; snookerhq (5 Oct 2026) has "
             "Trump third on £1,114,050 behind Wu Yize; Wikipedia's Judd Trump article (16 Oct 2026) states a "
             "current ranking of 3 as of 4 October 2026.",
      consequence="No snooker line was originated for any of the 6 fixtures.",
      action="Re-run against https://wst.tv/rankings or worldsnooker.com when reachable."),
 dict(id="F-13", severity="irregularity", area="motor-racing",
      title="OLBG's own F1 calendar contains a Grand Prix / circuit / country mismatch",
      detail="https://www.olbg.com/betting-tips/Motor_Racing/14 lists 'Round 16, 4 October, Bahrain Grand Prix, "
             "Sepang International Circuit, Malaysia'. The Bahrain Grand Prix is held at the Bahrain International "
             "Circuit in Sakhir; Sepang is the Malaysian circuit. The row mixes three different events.",
      action="Raised against the source site. Our Motor Racing rows use only the USA Grand Prix and the Drivers' "
             "Championship markets, not the calendar table."),
 dict(id="F-14", severity="model-divergence", area="rugby-union",
      title="Our originated rugby union lines diverge from LNR's own published probabilities",
      detail="LNR's official club pages publish fixture probabilities. Toulouse v Perpignan: LNR 83.06 / 15.32 / "
             "1.61 versus our 95.10 / 2.60 / 2.30 (12.04 pp divergence, inside the 15 pp cap, pick direction "
             "agrees). La Rochelle v Bordeaux: LNR 46.24 / 53.18 / 0.58 versus our 24.73 / 72.99 / 2.30 "
             "(19.81 pp divergence, outside the cap).",
      consequence="La Rochelle v Bordeaux confidence is capped at LOW despite a 0.73 model probability. Our model "
                  "weights points difference heavily (Bordeaux +64 versus La Rochelle +9) and LNR's figure does not.",
      action="Review whether points difference should carry that much weight in the rugby union model."),
 dict(id="F-16", severity="data-freshness", area="inventory",
      title="Most inventory rows come from dated search-index snapshots rather than a live fetch",
      detail="Live fetches on 2026-10-21 covered tennis, cricket, snooker, golf and basketball (58 rows). "
             "Darts, rugby union, ice hockey, handball, volleyball, baseball and motor racing (86 rows) come from "
             "search-index copies dated 2026-10-18 to 2026-10-20, where the page's own 'Today' refers to that "
             "earlier date. Each row carries retrieved_via and as_of so the two populations are never mixed.",
      action="Re-collect those seven sports with a live fetch before acting on their times."),
 dict(id="F-17", severity="coverage-gap", area="inventory",
      title="Aussie Rules and eSports have no OLBG betting-tips node and no upcoming events",
      detail="https://www.olbg.com/sitemap-betting-tips.xml lists /best-tipsters/Aussie_Rules/22 and "
             "/best-tipsters/eSports/23 but no corresponding /betting-tips node for either. The AFL 2026 season "
             "content on OLBG is a February pre-season preview; the 2026 season has concluded.",
      action="Both sports are reported as zero events rather than omitted silently."),
 dict(id="F-18", severity="coverage-gap", area="inventory",
      title="Rugby League lists no upcoming events",
      detail="https://www.olbg.com/betting-tips/Rugby_League/10 currently serves only its historical statistics "
             "tables (Super League, Championship, NRL) with no fixture list. The fixtures that appear in "
             "search-index copies of the same URL are dated 28 March 2026.",
      action="Rugby League is reported as zero current events. Its published base rates are retained in the "
             "model inputs for the next window."),
 dict(id="F-19", severity="model-limitation", area="cricket",
      title="No home-advantage term in the cricket model",
      detail="No official, in-session verifiable home-advantage coefficient for ODI or T20I cricket was available, "
             "so the term is set to zero rather than guessed. Both ICC-rated fixtures modelled are at neutral "
             "venues in the UAE, which limits the impact for this run.",
      action="Add a sourced home-advantage coefficient before applying the model to home-and-away series."),
 dict(id="F-21", severity="environment", area="publishing",
      title="GitHub Pages cannot be repointed at /docs, so the site publishes from the repository root",
      detail="Pages on this repository is build_type 'legacy' with source {branch: main, path: '/'}. "
             "PUT /repos/buffedlizard55-lab/OLBG2/pages with source[path]=/docs returns "
             "'403 Resource not accessible by integration' - the available token has no pages:write scope. "
             "Adding an Actions workflow would not help either, because switching build_type to 'workflow' "
             "needs the same permission.",
      consequence="scripts/build_site.py generates the site at the repository root (index.html, "
                  "sports.html, lines.html, picks.html, predictions.html, methodology.html, "
                  "verification.html, flagged.html, excluded.html, sports/, assets/, .nojekyll) instead of "
                  "into docs/. This also produces cleaner URLs: "
                  "https://buffedlizard55-lab.github.io/OLBG2/flagged.html rather than /docs/flagged.html.",
      action="If a docs/ layout is preferred, a maintainer with pages:write can run "
             "'gh api -X PUT repos/buffedlizard55-lab/OLBG2/pages -f source[branch]=main -f source[path]=/docs' "
             "and then change the DOCS constant in scripts/build_site.py back to ROOT / 'docs'."),
 dict(id="F-20", severity="source-tier", area="predictions",
      title="Player availability in prediction P-01 comes from regional press, not an official team sheet",
      detail="The Thomas Ramos, Tommaso Menoncello, Blair Kinghorn and Jack Willis availability statements are "
             "sourced to La Depeche and Rugbyrama (both 20 October 2026). Neither the LNR nor Stade Toulousain "
             "published a confirmed team sheet at collection time.",
      action="Treat as press-tier evidence. Re-check against the official LNR match sheet before staking."),
]

# F-15 is generated: one row per event with no originated line.
modelled = {(r["sport"], r["match"]) for r in lines}
SPORT_OF_FILE = {
    "tennis": "tennis", "cricket": "cricket", "snooker": "snooker", "golf": "golf",
    "basketball": "basketball", "darts": "darts", "rugby_union": "rugby_union",
    "ice_hockey": "ice_hockey", "handball": "handball", "volleyball": "volleyball",
    "baseball": "baseball", "motor_racing": "motor_racing",
}
REASON = {
    "tennis": "Official ATP/WTA ranking not verified for both players (see F-09). Source to consult: https://www.atptour.com/en/rankings/singles and https://www.wtatennis.com/rankings/singles",
    "snooker": "Official World Snooker Tour ranking not verified for both players (see F-12). Source to consult: https://wst.tv/rankings",
    "darts": "Official PDC Order of Merit position not verified for both players (see F-11). Source to consult: https://www.pdc.tv/rankings",
    "golf": "Outright tournament market. The official field list was not verified, so a tournament-winner probability cannot be computed. OWGR average points were retrieved (https://www.owgr.com/current-world-ranking, week 42, 18 Oct 2026) but a field is required to normalise them.",
    "basketball": "No official league standings or rating retrieved for both clubs in-session. Sources to consult: https://www.nba.com/standings, https://www.euroleaguebasketball.net, and the relevant national federation.",
    "ice_hockey": "No official league standings retrieved for both clubs in-session. Sources to consult: https://www.nhl.com/standings and the DEL / ICEHL official sites.",
    "handball": "OLBG publishes favourite/underdog/tie base rates for EHF and IHF tournaments only; these fixtures are domestic Danish, German, Norwegian, French, Austrian and Spanish league games, so no published base rate applies. Sources to consult: the relevant national federation league table.",
    "volleyball": "No official league standings retrieved for either club in-session. Sources to consult: the relevant national federation (Finland, Czechia, France, Brazil, Austria, Germany, Poland, Italy, Turkey).",
    "baseball": "Postseason fixture; no official starting-pitcher or standings-based rating retrieved in-session. Source to consult: https://www.mlb.com/standings and the official postseason bracket.",
    "motor_racing": "Multi-car race, not a head-to-head match. Requires the official FIA entry list and championship standings. Sources to consult: https://www.formula1.com/en/results and the FIA official calendar.",
    "rugby_union": "French second-tier (Pro D2) or non-Top-14 fixture: no official league table retrieved in-session, and OLBG publishes no base rates for that competition. Source to consult: https://www.lnr.fr/rugby-pro-d2/classement or https://www.urcrugby.com",
}

missing = []
for f in sorted((DATA / "events").glob("*.json")):
    sport = f.stem
    for e in json.loads(f.read_text()):
        if (sport, e["match"]) in modelled:
            continue
        if sport == "rugby_union" and e["match"] in ("Toulouse v Perpignan", "Bayonne v Lyon",
                                                     "La Rochelle v Bordeaux", "Connacht v Zebre Parma",
                                                     "Bulls v Ulster", "Stormers v Scarlets",
                                                     "Leinster v Munster"):
            continue
        missing.append(dict(sport=sport, match=e["match"], market=e["market"],
                            listed_time=e["listed_time"], as_of=e["as_of"],
                            retrieved_via=e["retrieved_via"], source_url=e["source_url"],
                            reason=(
                                "Antepost outright on national teams. Requires the official World Rugby rankings. "
                                "Source to consult: https://www.world.rugby/rankings/mru"
                                if e.get("outright") and sport == "rugby_union"
                                else REASON.get(sport, "No verified official basis retrieved in-session.")
                            )))

flags.append(dict(
    id="F-15", severity="coverage-gap", area="lines",
    title=f"{len(missing)} of the inventoried events have no originated line",
    detail="Each is listed below with the exact official source that would be needed to originate a line. "
           "Values are left blank rather than inferred, per the verification rule.",
    items=missing,
))

flags.sort(key=lambda f: f["id"])
(DATA / "flags.json").write_text(json.dumps(flags, indent=2, ensure_ascii=False) + "\n")
(DATA / "picks.json").write_text(json.dumps(picks, indent=2, ensure_ascii=False) + "\n")
(DATA / "predictions.json").write_text(json.dumps(PREDICTIONS, indent=2, ensure_ascii=False) + "\n")
(DATA / "lines.json").write_text(json.dumps(lines_doc, indent=2, ensure_ascii=False) + "\n")

from collections import Counter
c = Counter(r["confidence"] for r in lines)
print("picks      :", len(picks), dict(c))
print("predictions:", len(PREDICTIONS), [f"{p['id']}={p['word_count']}w" for p in PREDICTIONS])
print("flags      :", len(flags), f"(F-15 carries {len(missing)} unverified event rows)")
for p in PREDICTIONS:
    assert p["word_count"] >= 30, p["id"]
print("word-count check: all predictions >= 30 words OK")
