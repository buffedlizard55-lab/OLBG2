"""Ledger desk tests (session 21a0c524)."""
import json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L = json.loads((ROOT / "data/ledger/lines.json").read_text())
P = json.loads((ROOT / "data/ledger/predictions.json").read_text())["predictions"]
SRC = {s["key"]: s for s in json.loads((ROOT / "data/ledger/sources.json").read_text())["sources"]}
MATCH = {m["id"]: m for m in L["matches"]}
SPORTS15 = {"Golf","Volleyball","Rugby Union","Cricket","Snooker","Darts","Baseball","Gaelic Sports",
            "Greyhounds","Tennis","Motor Racing","Handball","Ice Hockey","Basketball","Rugby League"}

class Ledger(unittest.TestCase):
    def test_only_15_sports(self):
        self.assertTrue(all(m["sport"] in SPORTS15 for m in L["matches"]))

    def test_every_match_has_official_source(self):
        for m in L["matches"]:
            self.assertTrue(m["source_keys"], m["id"])
            for k in m["source_keys"]:
                self.assertIn(k, SRC)
                self.assertTrue(SRC[k]["url"].startswith("https://"))

    def test_unpriced_has_reason(self):
        for m in L["matches"]:
            if not m["priced"]:
                self.assertTrue(m.get("blank_reason"), m["id"])

    def test_tier_a_window(self):
        for s in L["selections"]:
            if s["tier"] == "A":
                self.assertGreaterEqual(s["prob"], 0.70)
                self.assertLessEqual(s["prob"], 0.7143)
                self.assertGreaterEqual(s["american"], -250)
                self.assertLessEqual(s["american"], 10000)
            if s["prob"] >= 0.70 and s["in_band"]:
                self.assertEqual(s["tier"], "A")

    def test_confidence_thresholds(self):
        for s in L["selections"]:
            if s["confidence"] == "High":
                self.assertGreaterEqual(s["prob"], 0.70)

    def test_winner_pairs_sum_to_one(self):
        from collections import defaultdict
        g = defaultdict(float)
        for s in L["selections"]:
            if "winner" in s["market"].lower() and "Outright" not in s["market"] and "Race winner" not in s["market"]:
                g[(s["fixture"], s["market"])] += s["prob"]
        for k, v in g.items():
            self.assertAlmostEqual(v, 1.0, delta=0.002, msg=str(k))

    def test_previews(self):
        self.assertGreaterEqual(len(P), 20)
        seen = set()
        for p in P:
            self.assertGreaterEqual(p["words"], 30, p["fixture"])
            low = p["text"].lower()
            self.assertNotIn("model", low)
            self.assertNotIn("verif", low)
            self.assertNotIn(p["text"], seen); seen.add(p["text"])
            rows = [s for s in L["selections"] if s["fixture"] == p["fixture"]
                    and s["selection"] == p["selection"] and s["market"] == p["market"]]
            self.assertEqual(len(rows), 1, p["fixture"])
            self.assertEqual(rows[0]["american"], p["american"])

    def test_site_pages_exist(self):
        for rel in ["ledger/index.html", "ledger/picks.html", "ledger/previews.html", "ledger/matches.html",
                    "ledger/lines.html", "ledger/flagged.html", "ledger/sources.html", "ledger/method.html",
                    "ledger/olbg.html", "ledger/verification.html", "ledger/sports/index.html"]:
            self.assertTrue((ROOT / rel).exists(), rel)
        for sp in SPORTS15:
            self.assertTrue((ROOT / f"ledger/sports/{sp.lower().replace(' ', '-')}.html").exists(), sp)

    def test_no_other_desks_touched_markers(self):
        # ledger pages must not claim another desk's identity
        txt = (ROOT / "ledger/index.html").read_text()
        self.assertIn("Ledger desk", txt)

if __name__ == "__main__":
    unittest.main()
