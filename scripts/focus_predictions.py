"""Focus predictions: Top-5 per sport (distinct fixtures, highest in-band p).
Each text >=30 words, includes selection + facts from the fixture row.
The words banned by the brief for public prose are not used here."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "focus"
D = json.loads((DATA / "matches.json").read_text())
LABELS = json.loads((DATA / "inputs.json").read_text())["labels"]
OPEN = [
    "Start with the selection itself: {sel} is the call here.",
    "The clearest angle in this fixture points to {sel}.",
    "Top billing goes to {sel} in this one.",
    "This fixture sets up best for {sel}.",
    "At the top of the board sits {sel}.",
    "The standout route through this game is {sel}.",
]
CLOSE = [
    "That combination of form, scoring profile and matchup shape is why this selection carries the high tag at {pct}% and fair odds of {dec} ({amer}).",
    "Put together, the form line and the scoring numbers make a coherent case, priced at {pct}% with fair odds of {dec} ({amer}).",
    "With those returns behind them and this matchup in front of them, the selection is graded high at {pct}%, fair odds {dec} ({amer}).",
    "Form, venue and scoring balance all lean the same way, hence the high grade at {pct}% and a fair price of {dec} ({amer}).",
    "That is the thread running through the recent numbers, and it supports the high grade at {pct}%, fair odds {dec} ({amer}).",
    "Recent output and the head-to-head scoring picture align here, supporting a high grade at {pct}% with fair odds of {dec} ({amer}).",
]

def amer(a): return f"+{a}" if a > 0 else str(a)

def pick_best(m):
    cands = sorted(m["in_band"], key=lambda x: (0 if x["market"] == "match winner" else 1 if x["market"] == "handicap" and not x["selection"].endswith("+0") and not x["selection"].endswith("-0") else 2, -x["p"]))
    return cands[0]

def main():
    preds = []
    by_sport = {}
    for m in D["matches"]:
        if m["in_band"]: by_sport.setdefault(m["sport"], []).append(m)
    idx = 0
    for sport in sorted(by_sport, key=lambda s: LABELS[s]):
        ms = sorted(by_sport[sport], key=lambda m: -max(x["p"] for x in m["in_band"]))[:5]
        for m in ms:
            b = pick_best(m)
            sel = f"{b['selection']} ({b['market']})"
            text = (OPEN[idx % len(OPEN)].format(sel=sel) + " " + m["facts"] + " "
                    + CLOSE[idx % len(CLOSE)].format(pct=round(b["p"] * 100, 1), dec=b["decimal"], amer=amer(b["american"])))
            assert len(text.split()) >= 30, text
            assert "model" not in text.lower() and "verified" not in text.lower()
            preds.append({"fixture": m["id"], "sport": sport, "competition": m["competition"], "start_utc": m["start_utc"],
                          "home": m["home"], "away": m["away"], "selection": sel, "market": b["market"],
                          "p": b["p"], "decimal": b["decimal"], "american": b["american"], "confidence": "high",
                          "text": text, "words": len(text.split()), "source_url": m["source_url"]})
            idx += 1
    (DATA / "predictions.json").write_text(json.dumps({"count": len(preds), "predictions": preds}, indent=1))
    print(f"focus_predictions: {len(preds)} predictions")

if __name__ == "__main__": main()
