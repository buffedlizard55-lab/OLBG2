"""Automated checks for the /signal/ desk (session 6b10ecda).

These run inside the repository's existing CI step
``python -m unittest discover -s tests`` and never write to the tree.
"""
import json
import os
import re
import unittest
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "signal")
SITE = os.path.join(ROOT, "signal")
BANNED = re.compile(r"\bmodel(s|led|ling)?\b|\bverified\b", re.I)

SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts",
          "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing",
          "Handball", "Ice Hockey", "Basketball", "Rugby League"]


def load(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


class Links(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag in ("a", "link"):
            for key, value in attrs:
                if key == "href":
                    self.hrefs.append(value)


class SignalDeskTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")["matches"]
        cls.preds = load("predictions.json")["predictions"]
        cls.flags = load("flagged.json")["flags"]
        cls.sources = load("sources.json")["sources"]

    # ------------------------------------------------------------- sourcing
    def test_every_match_row_has_an_official_source(self):
        for m in self.matches:
            self.assertTrue(m["source_url"].startswith("http"),
                            "%s has no source link" % m["id"])

    def test_every_unpriced_fixture_is_flagged(self):
        for m in self.matches:
            if not m["pick"] and m["status"] != "result":
                self.assertTrue(m["flags"], "%s is blank without a flag" % m["id"])

    def test_every_flag_has_a_source_and_detail(self):
        self.assertGreaterEqual(len(self.flags), 20)
        for f in self.flags:
            self.assertTrue(f["source_url"].startswith("http"), f["id"])
            self.assertGreater(len(f["detail"]), 40, f["id"])

    def test_sources_cover_the_sports_with_prices(self):
        priced = {p["sport"] for p in self.preds}
        covered = {s["sport"] for s in self.sources}
        self.assertTrue(priced.issubset(covered), priced - covered)

    # -------------------------------------------------------------- pricing
    def test_two_way_markets_are_fair(self):
        for m in self.matches:
            sides = {}
            for mk in m["markets"]:
                sides.setdefault(mk["market"], []).append(mk["prob"])
            for name, probs in sides.items():
                if len(probs) == 2:
                    self.assertAlmostEqual(sum(probs), 1.0, delta=0.02,
                                           msg="%s / %s" % (m["id"], name))

    def test_probabilities_are_clamped(self):
        for m in self.matches:
            for mk in m["markets"]:
                self.assertGreaterEqual(mk["prob"], 0.0)
                self.assertLessEqual(mk["prob"], 0.9501)

    def test_in_band_flag_matches_the_price_rule(self):
        for p in self.preds:
            american = int(p["american"].replace("+", ""))
            self.assertEqual(p["in_band"], -250 <= american <= 10000,
                             "%s %s" % (p["id"], p["american"]))

    def test_confidence_tiers_follow_the_probability(self):
        for p in self.preds:
            expected = "high" if p["prob"] >= 0.70 else (
                "medium" if p["prob"] >= 0.60 else "low")
            self.assertEqual(p["confidence"], expected, p["id"])

    # ---------------------------------------------------------- write-ups
    def test_write_ups_are_long_unique_and_clean(self):
        seen = set()
        written = [p for p in self.preds if p["write_up"]]
        self.assertGreaterEqual(len(written), 30)
        for p in written:
            self.assertGreaterEqual(len(p["write_up"].split()), 30, p["id"])
            self.assertIsNone(BANNED.search(p["write_up"]), p["id"])
            opener = p["write_up"][:60].lower()
            self.assertNotIn(opener, seen, "repeated opening: %s" % p["id"])
            seen.add(opener)

    def test_top_five_per_sport_is_respected_where_data_exists(self):
        per_sport = {}
        for p in self.preds:
            per_sport.setdefault(p["sport"], []).append(p)
        for sport, rows in per_sport.items():
            top = sorted(rows, key=lambda r: -r["prob"])[:5]
            written = [r for r in top if r["write_up"]]
            self.assertTrue(written, "no preview written for %s" % sport)

    # -------------------------------------------------------------- pages
    def test_every_in_scope_sport_has_a_page(self):
        for sport in SPORTS:
            fn = re.sub(r"[^a-z0-9]+", "-", sport.lower()).strip("-") + ".html"
            self.assertTrue(os.path.exists(os.path.join(SITE, "sports", fn)), fn)

    def test_support_pages_exist(self):
        for fn in ("index.html", "picks.html", "predictions.html", "matches.html",
                   "flagged.html", "sources.html", "verification.html",
                   "methodology.html", os.path.join("assets", "signal.css")):
            self.assertTrue(os.path.exists(os.path.join(SITE, fn)), fn)

    def test_local_links_resolve(self):
        pages = [os.path.join(SITE, f) for f in os.listdir(SITE) if f.endswith(".html")]
        pages += [os.path.join(SITE, "sports", f)
                  for f in os.listdir(os.path.join(SITE, "sports"))]
        for pg in pages:
            with open(pg, "r", encoding="utf-8") as fh:
                parser = Links()
                parser.feed(fh.read())
            for href in parser.hrefs:
                if href.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = os.path.normpath(os.path.join(os.path.dirname(pg), href))
                self.assertTrue(os.path.exists(target),
                                "%s -> %s" % (os.path.basename(pg), href))

    def test_pages_do_not_use_the_two_forbidden_words(self):
        for folder, _, files in os.walk(SITE):
            for fn in files:
                if not fn.endswith(".html"):
                    continue
                with open(os.path.join(folder, fn), "r", encoding="utf-8") as fh:
                    visible = re.sub(r"<[^>]+>", " ", fh.read())
                self.assertIsNone(BANNED.search(visible), fn)


if __name__ == "__main__":
    unittest.main()
