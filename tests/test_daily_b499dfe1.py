import json, os, re, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "daily"); SITE = os.path.join(ROOT, "daily")
def load(n):
    with open(os.path.join(D, n)) as f: return json.load(f)
class TestDailyDesk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = load("fixtures.json")["fixtures"]; cls.lines = load("lines.json")["rows"]
        cls.top5 = load("top5.json")["top5"]; cls.preds = load("predictions.json")["predictions"]
        cls.sports = load("sports.json")["sports"]; cls.flags = load("flagged.json")["flags"]
    def test_no_excluded_sports(self):
        bad = {"soccer","football","boxing","ufc","mma","american-football","hurling","horse-racing","cycling","specials"}
        self.assertFalse(bad & {f["sport"] for f in self.fx})
    def test_window_and_sources(self):
        for f in self.fx:
            self.assertTrue("2026-10-23" <= f["date"] <= "2026-10-30", f["id"])
            self.assertTrue(f["official_url"].startswith("https://"), f["id"])
    def test_17_sports_have_pages(self):
        self.assertEqual(len(self.sports), 17)
        for s in self.sports:
            self.assertTrue(os.path.exists(os.path.join(SITE, "sports", s["slug"] + ".html")), s["slug"])
    def test_prices_are_fair_no_vig(self):
        for r in self.lines:
            for m in r.get("markets", []):
                for o in m["outcomes"]:
                    self.assertAlmostEqual(round(1/min(max(o["p"],0.01),0.99),2), o["fair_decimal"], delta=0.011)
    def test_winner_market_probs_sum(self):
        for r in self.lines:
            for m in r.get("markets", []):
                if ("Winner" in m["market"] or "Moneyline" in m["market"]) and len(m["outcomes"]) == 2:
                    self.assertAlmostEqual(sum(o["p"] for o in m["outcomes"]), 1.0, delta=0.02)
    def test_high_confidence_gate(self):
        for r in self.lines:
            pp = r.get("primary_pick") or {}
            if pp.get("confidence") == "high":
                self.assertGreaterEqual(pp["p"], 0.70); self.assertGreaterEqual(pp["fair_american"], -250)
                self.assertLessEqual(pp["fair_american"], 10000)
    def test_top5_shape_and_ranking(self):
        for sp, cand in self.top5.items():
            self.assertLessEqual(len(cand), 5)
            self.assertEqual([p["p"] for p in cand], sorted([p["p"] for p in cand], reverse=True))
    def test_short_sports_flagged(self):
        fl = {f["sport"] for f in self.flags}
        for sp, cand in self.top5.items():
            if len(cand) < 5: self.assertIn(sp, fl)
    def test_predictions_cover_top5_and_highs(self):
        need = {p["match_id"] for v in self.top5.values() for p in v}
        need |= {r["match_id"] for r in self.lines if r.get("primary_pick") and r["primary_pick"]["confidence"] == "high"}
        self.assertFalse(need - {p["match_id"] for p in self.preds})
    def test_predictions_unique_min_words_selection_first(self):
        texts = [p["text"] for p in self.preds]
        self.assertEqual(len(set(texts)), len(texts))
        for p in self.preds:
            self.assertGreaterEqual(len(p["text"].split()), 30)
            first = p["text"].split(".")[0]
            self.assertTrue(p["selection"].split(" in ")[0] in first or p["selection"] in p["text"])
    def test_predictions_not_near_duplicate(self):
        toks = [set(re.findall(r"[a-z0-9%]+", p["text"].lower())) for p in self.preds]
        for i in range(len(toks)):
            for j in range(i+1, len(toks)):
                self.assertLessEqual(len(toks[i]&toks[j])/max(len(toks[i]|toks[j]),1), 0.88)
    def test_rendered_pages_no_broken_local_links(self):
        for dp, _, fns in os.walk(SITE):
            for fn in fns:
                if not fn.endswith(".html"): continue
                pg = os.path.join(dp, fn)
                for h in re.findall(r'href="([^"#]+?\.html)', open(pg).read()):
                    if h.startswith("http"): continue
                    self.assertTrue(os.path.exists(os.path.normpath(os.path.join(dp, h))), f"{pg}->{h}")
    def test_rendered_top5_rows_match_data(self):
        html = open(os.path.join(SITE, "top5.html")).read()
        for v in self.top5.values():
            for p in v: self.assertIn(p["selection"], html)
    def test_nba_totals_blank_not_invented(self):
        for r in self.lines:
            fx = next(f for f in self.fx if f["id"] == r["match_id"])
            if fx["family"] == "nba_prior":
                tot = [m for m in r["markets"] if "Game Total" in m["market"]]
                self.assertTrue(tot and not tot[0]["outcomes"] and tot[0].get("blank_reason"))
if __name__ == "__main__": unittest.main()
