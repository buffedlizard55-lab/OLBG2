#!/usr/bin/env python3
"""Build data/final/flagged.json: every irregularity, correction and coverage limit."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "final"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    matches = read(DATA / "matches.json")["matches"]
    preds = read(DATA / "predictions.json")["predictions"]
    conf = Counter((m.get("pick") or {}).get("confidence", "none") for m in matches)
    unlined = [m for m in matches if m["line_status"] == "unlined"]
    multi = [m for m in matches if len(m["provenance"]["layers"]) > 1]
    scope = Counter(m["source_scope"] for m in matches)
    facts = [f for p in preds for f in p["facts"]]
    started = [m for m in matches if m["start_utc"] < "2026-10-22T08:22:00Z"]
    player_rows = [m for m in matches if m["source_scope"] == "player"]
    comp_rows = [m for m in matches if m["source_scope"] == "competition"]

    items = [
        {
            "id": "FR-01", "severity": "high", "category": "Confidence-rule divergence",
            "sport": "cross-sport",
            "item": "Five layers used at least three different definitions of a high-confidence pick",
            "detail": (f"The hub graded 25 picks high at >=65% probability inside the band; 22 of those 25 are below 70%. "
                       f"The verified desk used 72% (or a 70% band selection), the board labelled 42 picks high, and the slate "
                       f"marked rows high at a price-only band (one ATP pick at 64.97% was labelled high). This consolidation "
                       f"applies one rule - >=70% AND fair decimal 1.40-101.00 - and produces {conf['high']} high picks. "
                       f"Every other pick is medium or low with the reason on the row."),
            "source_name": "Hub grading function", "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/scripts/hub_model.py",
        },
        {
            "id": "FR-02", "severity": "high", "category": "Duplicate fixtures and conflicting prices",
            "sport": "cross-sport",
            "item": f"{sum(len(read(DATA.parent / n / 'matches.json')[k]) for n, k in (('hub','rows'),('slate','matches'),('board','matches'),('verified','matches'),('forward','matches')))} layer rows collapse to {len(matches)} fixtures; {len(multi)} fixtures appear in two or more layers",
            "detail": (f"{len(multi)} of the {len(matches)} fixtures were captured by more than one session. The same game can carry "
                       "different model probabilities because each layer ran its own model. Example: Minnesota Wild at Calgary "
                       "is 70.84% on the verified row but 67.38% on the hub row; Boston v Nashville is 63.69% on the board row "
                       "and 66.01% on the hub row. One row per fixture is kept, the layer used is recorded in provenance, and "
                       "the other layers are not blended into the number."),
            "source_name": "NHL GameCenter example", "source_url": "https://www.nhl.com/gamecenter/min-vs-cgy/2026/10/22/2026020162",
        },
        {
            "id": "FR-03", "severity": "medium", "category": "Fixture corrected",
            "sport": "Golf",
            "item": "Inherited golf row named a tournament that finished on 4 October",
            "detail": ("The hub and verified layers carried 'Bank of Utah Championship' on 2026-10-22. The official PGA Tour "
                       "tournament page for 22-25 October 2026 is the Butterfield Bermuda Championship at Port Royal Golf Club, "
                       "Southampton. The row was replaced with the official event and left unlined because strokes-gained inputs "
                       "are not server-rendered. The original stale value is preserved in the hub layer."),
            "source_name": "PGA Tour tournament page",
            "source_url": "https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview",
        },
        {
            "id": "FR-04", "severity": "medium", "category": "Rejected correction",
            "sport": "Darts",
            "item": "Earlier 'Bunting withdrew' finding was not applied",
            "detail": ("A previous session logged that Stephen Bunting withdrew from the European Championship and was replaced "
                       "by Ritchie Edhouse. No official page read in this pass confirms that, Edhouse did not qualify through the "
                       "European Tour Order of Merit, and multiple dated listings for 19-22 October still show Noppert v Bunting. "
                       "The pair is therefore left unchanged; the PDC article could not be read past its consent wall, so the draw "
                       "remains inherited rather than re-verified."),
            "source_name": "PDC schedule article (consent wall)",
            "source_url": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/",
        },
        {
            "id": "FR-05", "severity": "medium", "category": "Write-up corrected",
            "sport": "Tennis",
            "item": "Fils ranking in the inherited write-up did not match the official capture",
            "detail": ("The slate write-up quoted Arthur Fils at #22 with 2,050 points. The hub, slate and verified inputs all "
                       "carry the 2026-10-19 ATP list at #10 with 3,325 points, and Mannarino at #79 with 743. The published "
                       "write-up uses the captured #10 / 3,325 figures."),
            "source_name": "ATP rankings", "source_url": "https://www.atptour.com/en/rankings/singles",
        },
        {
            "id": "FR-06", "severity": "medium", "category": "Write-up corrected",
            "sport": "Ice Hockey",
            "item": "Boston write-up quoted a player total the official game page contradicts",
            "detail": ("The board/forward text said David Pastrnak had 4 goals and 8 assists. The NHL GameCenter page for "
                       "Nashville at Boston on 22 October lists Pastrnak with 6 points. The published write-up now uses the "
                       "verified 6 points and Swayman's 6-1-1 / 1.98 / .928 line."),
            "source_name": "NHL GameCenter",
            "source_url": "https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154",
        },
        {
            "id": "FR-07", "severity": "medium", "category": "Write-up corrected",
            "sport": "Ice Hockey",
            "item": "Josi assist total corrected from 8 to 6",
            "detail": ("The Washington write-up said Roman Josi had eight assists. The official game page read today lists six "
                       "assists, four goals for Ryan O'Reilly and three wins for Juuse Saros. The published text uses those figures."),
            "source_name": "NHL GameCenter",
            "source_url": "https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154",
        },
        {
            "id": "FR-08", "severity": "low", "category": "Source hygiene",
            "sport": "cross-sport",
            "item": "Synthetic 'book' prices dropped from the slate layer",
            "detail": ("The slate rows publish book_dec/book_am columns generated by applying a 4.5% overround to the layer's own "
                       "fair price. They are not observed bookmaker prices. They were removed from the consolidated dataset; no "
                       "bookmaker or tipster price is published anywhere on this desk."),
            "source_name": "Slate methodology", "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/slate/methodology.html",
        },
        {
            "id": "FR-09", "severity": "low", "category": "Blank unconfirmed market",
            "sport": "cross-sport",
            "item": f"{len(unlined)} fixtures are deliberately unlined",
            "detail": ("Unlined by sport: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(m['sport'] for m in unlined).items()))
                       + ". Each row states its reason (client-rendered rankings, no pre-match scoring table, futures without "
                       "rosters, or a sample too small to price). No value was estimated to fill a blank."),
            "source_name": "Flagged page", "source_url": "flagged.html",
        },
        {
            "id": "FR-10", "severity": "low", "category": "Source scope",
            "sport": "cross-sport",
            "item": f"{sum(1 for m in matches if m['source_scope'] != 'fixture')} of {len(matches)} rows do not link to an individual fixture page",
            "detail": (f"{sum(1 for m in matches if m['source_scope'] == 'fixture')} rows cite a URL that identifies the fixture; {scope.get('competition',0)} cite a "
                       f"competition, rankings or tournament page and {scope.get('player',0)} cite a player page. Two tennis rows "
                       "(atp-902103 and atp-902133) link to player profiles because the layer did not capture a tournament-specific "
                       "schedule URL; both are flagged rather than presented as fixture-level proof."),
            "source_name": "Example player page", "source_url": "https://www.atptour.com/en/players/valentin-vacherot/va25/overview",
        },
        {
            "id": "FR-11", "severity": "low", "category": "Inherited facts",
            "sport": "cross-sport",
            "item": f"{sum(1 for f in facts if not f['verified'])} of {len(facts)} facts in the write-ups were not re-read today",
            "detail": ("Each fact carries its source URL and an 'inherited' badge. Re-read today: NHL standings and skater leaders, "
                       "the Nashville-Boston game page, the SHL table, the PGA Tour tournament page. Not re-read: LNR, URC, ATP "
                       "rankings table, EHF, EuroLeague/EuroCup, NBA, MLB, Formula 1, SuperLega, PlusLiga, AFLW, NRL, LoL, GAA, GBGB."),
            "source_name": "NHL leaders feed",
            "source_url": "https://api-web.nhle.com/v1/skater-stats-leaders/20262027/2?categories=goals,assists,points&limit=10",
        },
        {
            "id": "FR-12", "severity": "low", "category": "Date and status",
            "sport": "cross-sport",
            "item": f"{len(started)} fixtures had already started before the 08:22 UTC snapshot",
            "detail": ("New Zealand v India (07:00 UTC), plus two tennis ties at 08:00 UTC, are shown with a 'started' label and "
                       "dimmed styling. They are retained for audit and are never counted as upcoming tips."),
            "source_name": "ICC match page", "source_url": "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india",
        },
        {
            "id": "FR-13", "severity": "low", "category": "Fixture scope",
            "sport": "Cricket",
            "item": "Two tri-series cricket rows cite non-fixture ICC pages",
            "detail": ("icc-tri-m4 links to an ICC news article and icc-tri-m5 to the ICC ODI team rankings page. Neither page "
                       "identifies the fixture by date and teams. The rows are retained with the exact source that was captured and "
                       "are marked competition-scope on the table."),
            "source_name": "ICC team rankings", "source_url": "https://www.icc-cricket.com/rankings/team-rankings/mens/odi",
        },
        {
            "id": "FR-14", "severity": "low", "category": "Upstream not edited",
            "sport": "cross-sport",
            "item": "The hub layer still publishes the stale golf row and 65%-high labels",
            "detail": ("This session's scope is the consolidated /final/ layer. The hub, verified, board, slate and forward layers "
                       "are left byte-identical to their owning sessions. The defects fixed here therefore still exist in those "
                       "archives; the consolidated table and its flagged page are the corrected view."),
            "source_name": "Hub layer", "source_url": "https://buffedlizard55-lab.github.io/OLBG2/hub/flagged.html",
        },
        {
            "id": "FR-15", "severity": "low", "category": "Excluded-sport leak check",
            "sport": "cross-sport",
            "item": "0 rows from the ten excluded categories survived",
            "detail": ("Soccer/football, boxing, UFC/MMA, American football, hurling, horse racing, cycling and specials are "
                       "filtered by slug and asserted in tests. Gaelic football is in scope because the brief lists 'football' and "
                       "'American football' separately and does not name Gaelic football; that interpretation is documented."),
            "source_name": "Consolidation script", "source_url": "https://github.com/buffedlizard55-lab/OLBG2/blob/main/scripts/final_consolidate.py",
        },
        {
            "id": "FR-17", "severity": "high", "category": "Non-official source",
            "sport": "eSports",
            "item": "8 eSports pairings came from Liquipedia, not an official league page",
            "detail": ("The slate layer captured the LoL Worlds 2026 Swiss Round 1 pairings from Liquipedia, a community wiki. "
                       "That is not an official source, so the eight rows are published as unlined and unverified, with the "
                       "official lolesports.com Worlds schedule as the outbound link. No market or pick is shown for them. "
                       "This is why eSports carries eight rows but zero originated picks."),
            "source_name": "LoL Esports official schedule", "source_url": "https://lolesports.com/en-US/leagues/worlds/schedule",
        },
        {
            "id": "FR-16", "severity": "low", "category": "Consent wall",
            "sport": "Darts",
            "item": "PDC article cannot be read past the consent wall",
            "detail": ("The official PDC schedule article returns cookie-consent text in every chunk read. The darts fixtures are "
                       "therefore inherited from the hub capture, with the PDC URL kept on every row."),
            "source_name": "PDC schedule article",
            "source_url": "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/",
        },
    ]

    payload = {
        "generated_at": "2026-10-22T08:50:00Z",
        "counts": {"items": len(items), "high": sum(1 for i in items if i["severity"] == "high"),
                   "medium": sum(1 for i in items if i["severity"] == "medium"),
                   "low": sum(1 for i in items if i["severity"] == "low")},
        "items": items,
    }
    (DATA / "flagged.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(items)} flags")


if __name__ == "__main__":
    main()
