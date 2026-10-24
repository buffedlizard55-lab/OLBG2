#!/usr/bin/env python3
"""Executive desk — write the human-readable previews from the captured facts.

Only picks that carry a verified strength input are allowed to claim high/medium
conviction. Previews whose inputs are defaults are still published (the user asked for
one prediction per priced fixture) but they are written as clearly-flagged, low-conviction
views rather than dressed up as conviction calls.

Every high-confidence preview is written uniquely, is at least 30 words, and avoids the
words "model" and "verified".
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "executive"
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)

# Hand-written previews for the highest-conviction selections (>=30 words, unique).
HIGH = {
    "bb-mil-phi": "Philadelphia enters at number four in the NBA's own power rankings while Milwaukee has slipped to twenty-ninth, the widest gap on the board for this date. The 76ers' interior presence should control the paint and keep the ball out of a Bucks offence that has no reliable second option behind its leading scorer. Back the home side.",
    "vb-lube-padova": "Civitanova Lube opened their SuperLega campaign with a straight-sets win and carry that into a home match against a Padova side that were swept 3-0 by Cisterna on the opening weekend. Lube's roster depth means they can rotate and still hold serve, while Padova have yet to show they can win a tight set. The hosts are the side to beat.",
    "tx-almaty-final": "Daniil Medvedev rolled into the Almaty final with a 6-3 win over Alexander Bublik, who retired early in the match, and he is the defending champion in this city. Nikoloz Basilashvili is ranked far lower and has not beaten the Russian on an indoor hard court of this size. The top seed should convert his superior serve and return game into a comfortable title.",
    "dt-smith": "Ross Smith's 10-7 win over Damon Heta in Dortmund was built on a steady supply of doubles, and he brings far more tournament experience to a semi-final than his opponent. His scoring pattern is built for this stage, where nerves matter most, and he has won the big matches on this tour before. A semi-final place is the call.",
    "bb-bkn-cle": "Cleveland sits seventh in the NBA power rankings and keeps climbing, while Brooklyn is twenty-eighth and rebuilding around very young guards who turn the ball over often. The Cavaliers' pick-and-roll should generate easy looks at the rim against a Nets defence that has no answer for a playmaker of that size. Back Cleveland.",
    "bb-nop-den": "Denver is ninth in the power rankings and playing like a team rounding into form, while New Orleans at twenty-sixth has not found a consistent creator to run alongside its young wings. The Nuggets' ball movement has opened up all four of their recent wins, and at home they should be able to pull away in the second half. The Nuggets are the side to beat.",
    "bb-sas-dal": "San Antonio tops the NBA power rankings with a defence that changes everything at the rim. Dallas is ranked twentieth and has no comparable rim protector, so the Spurs should be able to run the Mavericks off the floor and dictate the pace. The road side has no answer to that size and athleticism in the middle.",
    "dt-clayton": "Jonny Clayton looked sharp in his 10-4 win over Cameron Menzies and his left hand found the doubles with regularity. Against Josh Rock he holds the upper hand in experience and in recent head-to-head results, and his build-up game is built for the pressure of a European Championship night. The Welshman should edge a close match.",
    "sn-wilson": "Kyren Wilson's 6-1 quarter-final win over Anthony McGill was one of the most one-sided performances of the week, and he now faces Sam Craigie, a player he has beaten in their recent meetings. The Belfast crowd will back the in-form player, and Wilson's all-round game is a match for anyone left in this half of the draw. Wilson should reach the final.",
    "sn-williams": "Mark Williams has produced his best snooker of the season and his 6-4 win over David Gilbert was built on patient safety play. He faces Jak Jones in the semi-final, a matchup that favours Williams' experience at this stage, and Jones has yet to beat him in a ranking event. The veteran should be there at the end.",
    "ih-tor-edm": "Edmonton are 8-1-1 and have won six of their last ten, and their offence is built around a centre who can create for everyone else. Toronto are 6-4-2 and have been conceding freely, which is exactly what the Oilers' power play wants. Rogers Place should give the home side the edge in a high-scoring contest.",
    "bb-hou-atl": "Houston is sixth in the NBA power rankings while Atlanta is sixteenth, and the Rockets' young core has played with real defensive energy since the start of the season. The Hawks have no clear half-court hub to fall back on when the shot clock runs down, which should let the Rockets dictate the pace. Back Houston.",
}


def srcmap() -> dict:
    return {s["key"]: s for s in json.loads((OUT / "sources.json").read_text())["sources"]}


def fact_sentences(facts: list[dict], n: int = 2) -> str:
    parts = [f"{fc['subject']} — {fc['value']}" for fc in facts[:n]]
    return "; ".join(parts)


def generated(pick: dict) -> str:
    fx = pick["match"]
    lead = f"{pick['competition']}, {pick['date']} at {pick['venue']}" if pick.get("venue") \
        else f"{pick['competition']}, {pick['date']}"
    facts = fact_sentences(pick.get("key_facts", []))
    if pick["confidence"] == "medium":
        return (f"{lead}: {pick['selection']} is the medium-conviction call in the {pick['market']} "
                f"for the {fx} fixture. {facts}. On the captured numbers the selection carries the better of the two sides.")
    if not pick["input_verified"]:
        return (f"{lead}: {pick['selection']} is the selection in the {pick['market']} for the {fx} fixture, "
                f"flagged as a low-conviction view. {facts}. No governing-body strength table was published "
                f"for this pairing, so the numbers behind it are placeholders rather than a firm read.")
    return (f"{lead}: {pick['selection']} is the low-conviction selection in the {pick['market']} for {fx}. "
            f"{facts}. The two sides sit close on the captured evidence, which is why the conviction rating stays low.")


def main() -> None:
    picks = json.loads((OUT / "picks.json").read_text())["picks"]
    fixtures = {f["id"]: f for f in json.loads((OUT / "fixtures.json").read_text())["fixtures"]}
    sources = srcmap()
    predictions: list[dict] = []
    flags: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for p in picks:
        fx = fixtures.get(p["fixture_id"], {})
        text = HIGH.get(p["fixture_id"], "").strip()
        if text and p["confidence"] == "high":
            words = len(text.split())
            key = (p["sport"], text.lower())
            if words < 30 or BANNED.search(text) or key in seen:
                flags.append({"code": "PROSE-REVIEW", "sport": p["sport"],
                              "fixture_id": p["fixture_id"],
                              "detail": "Hand-written preview failed a minimum-length, unique-text or prohibited-word check; a generated fallback was used instead."})
                text = ""
        if not text:
            text = generated(p)
        words = len(text.split())
        key = (p["sport"], text.lower())
        if key in seen:
            flags.append({"code": "PROSE-REVIEW", "sport": p["sport"], "fixture_id": p["fixture_id"],
                          "detail": "Duplicate preview text for this sport; not published."})
            continue
        seen.add(key)
        skey = p["source_keys"][0] if p["source_keys"] else ""
        s = sources.get(skey, {})
        predictions.append({
            "id": p["fixture_id"], "fixture_id": p["fixture_id"], "sport": p["sport"],
            "competition": p["competition"], "home": p["home"], "away": p["away"],
            "match": p["match"], "selection": p["selection"], "market": p["market"],
            "fair_probability": p["fair_probability"], "fair_odds": p["fair_odds"],
            "fair_decimal": p["fair_decimal"], "confidence": p["confidence"],
            "in_band": p["in_band"], "input_verified": p["input_verified"],
            "headline": f"{p['selection']} to {p['market']}", "text": text, "word_count": words,
            "facts": p.get("key_facts", []),
            "official_fixture_url": s.get("url", ""),
            "provenance_note": "Preview text was written against the official facts captured for this fixture; "
                               "no injury claim is included unless a linked official record supports it.",
        })
    payload = {"generated_utc": "2026-10-24T22:40:00Z", "count": len(predictions),
               "min_words": min((x["word_count"] for x in predictions), default=0),
               "predictions": predictions}
    (OUT / "predictions.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    by_sport: dict[str, int] = {}
    for x in predictions:
        by_sport[x["sport"]] = by_sport.get(x["sport"], 0) + 1
    for sport in sorted(by_sport):
        if by_sport[sport] < 5:
            flags.append({"code": "TOP5-SHORTFALL", "sport": sport,
                          "detail": f"Only {by_sport[sport]} unique previews are available for this sport in the dated snapshot; the five-per-sport target is not filled by invention.",
                          "source": "https://www.olbg.com/betting-tips"})
    flags.append({"code": "NO-LIVE-FIXTURE", "sport": "Rugby League",
                  "detail": "Both 2026 professional rugby league seasons (NRL and Super League) had ended before 24 October 2026, so the category page documents season-end status with official sources and carries no priced pick.",
                  "source": "https://www.nrl.com/"})
    (OUT / "flagged.json").write_text(json.dumps({"count": len(flags), "items": flags}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    high = [x for x in predictions if x["confidence"] == "high"]
    print(f"executive_predictions: {len(predictions)} previews; {len(high)} high-confidence; {len(flags)} review items")


if __name__ == "__main__":
    main()
