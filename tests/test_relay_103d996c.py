"""Regression tests for the /relay/ layer (session arena/103d996c-olbg2).

Three jobs, mirroring tests/test_current.py:
  1. prove the published pages are byte-identical to a fresh rebuild,
  2. prove every local link, anchor and official source link is well formed
     and that subpage chrome resolves inside the layer,
  3. re-verify the captured official numbers and the originated arithmetic
     independently of scripts/relay_model.py.
"""

import json
import math
import os
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "relay")
CAPTURE = os.path.join(DATA, "capture")
CURCAP = os.path.join(ROOT, "data", "current", "capture")
OUT = os.path.join(ROOT, "relay")

ELIGIBLE = ["aussie-rules", "baseball", "basketball", "cricket", "darts", "esports",
            "gaelic-football", "golf", "greyhounds", "handball", "ice-hockey",
            "motor-racing", "rugby-league", "rugby-union", "snooker", "tennis",
            "volleyball"]

sys.path.insert(0, os.path.join(ROOT, "scripts"))


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def data(name):
    return load(os.path.join(DATA, name))


def capture(name):
    return load(os.path.join(CAPTURE, name))


def curcap(name):
    return load(os.path.join(CURCAP, name))


class Collector(HTMLParser):
    """Collect hrefs, ids and the per-row cell counts of every table."""

    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()
        self.tables = []          # list of (header_count, [body_row_counts])
        self._stack = []
        self._heads = []
        self._body = []
        self._cells = 0
        self._in_body = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link") and a.get("href"):
            self.hrefs.append(a["href"])
        if tag in ("script", "img") and a.get("src"):
            self.hrefs.append(a["src"])
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "table":
            self._heads, self._body = [], []
        elif tag == "thead":
            self._stack.append("thead")
        elif tag == "tbody":
            self._stack.append("tbody")
            self._in_body = True
        elif tag == "tr":
            self._cells = 0
        elif tag in ("th", "td"):
            self._cells += int(a.get("colspan", 1))
            if self._stack and self._stack[-1] == "thead":
                self._heads.append(self._cells)

    def handle_endtag(self, tag):
        if tag == "tr":
            if self._in_body and (not self._stack or self._stack[-1] != "thead"):
                self._body.append(self._cells)
        elif tag in ("thead", "tbody"):
            if self._stack:
                self._stack.pop()
            if tag == "tbody":
                self._in_body = False
        elif tag == "table":
            if self._heads:
                self.tables.append((max(self._heads), self._body))


def collect(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    parser = Collector()
    parser.feed(text)
    return parser, text


def pages():
    out = []
    for base, _, files in os.walk(OUT):
        for name in sorted(files):
            if name.endswith(".html"):
                out.append(os.path.join(base, name))
    return sorted(out)


class TestCapturedArithmetic(unittest.TestCase):
    def test_relay_captures_declare_official_sources(self):
        for name in sorted(os.listdir(CAPTURE)):
            doc = capture(name)
            self.assertTrue(doc["source_url"].startswith("https://"), name)
            self.assertIn("fetched_utc", doc, name)

    def test_nhl_32_clubs(self):
        teams = curcap("nhl_team_summary_2026-10-22.json")["teams"]
        self.assertEqual(len(teams), 32)
        for t in teams:
            self.assertEqual(t["w"] + t["l"] + t["otl"], t["gp"], t["abbrev"])

    def test_urc_16_clubs(self):
        table = curcap("urc_table_2026-10-22.json")["table"]
        self.assertEqual(len(table), 16)
        for t in table:
            self.assertEqual(t["w"] + t["d"] + t["l"], t["pl"], t["team"])
            self.assertEqual(t["pf"] - t["pa"], t["diff"], t["team"])

    def test_euroleague_20_clubs(self):
        standings = curcap("euroleague_round7_2026-10-22.json")["standings"]
        self.assertEqual(len(standings), 20)
        for c in standings:
            self.assertEqual(c["w"] + c["l"], c["gp"], c["code"])
            self.assertEqual(c["pts_for"] - c["pts_against"], c["diff"], c["code"])

    def test_ehf_24_clubs_internally_consistent(self):
        clubs = curcap("ehf_standings_2026-10-22.json")["clubs"]
        self.assertEqual(len(clubs), 24)
        gf = sum(c["goals_for"] for c in clubs)
        ga = sum(c["goals_against"] for c in clubs)
        self.assertEqual(gf, ga)
        for c in clubs:
            self.assertEqual(c["w"] + c["d"] + c["l"], c["gp"], c["club"])
            self.assertEqual(c["goals_for"] - c["goals_against"], c["diff"], c["club"])

    def test_mlb_world_series_captures_agree(self):
        fresh = capture("mlb_world_series_2026-10-22.json")
        carried = curcap("mlb_world_series_2026-10-22.json")
        self.assertEqual([g["gamePk"] for g in fresh["games"]],
                         [g["game_pk"] for g in carried["games"]])

    def test_relay_nhl_capture_records_parse(self):
        for name in ("nhl_score_2026-10-23.json", "nhl_score_2026-10-24.json"):
            doc = capture(name)
            for g in doc["games"]:
                for side in ("home", "away"):
                    w, l, otl = (int(x) for x in g[side]["record"].split("-"))
                    self.assertGreaterEqual(w + l + otl, 1, g["id"])


class TestModelOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seeded = data("matches.json")
        cls.lines = data("lines.json")
        cls.band = data("band.json")
        cls.rows = {r["match_id"]: r for r in cls.lines["rows"]}

    def test_sport_scope_is_exactly_the_17_eligible(self):
        slugs = set()
        for m in self.seeded["matches"]:
            slugs.add(m["sport"])
        self.assertTrue(slugs <= set(ELIGIBLE))
        page_slugs = {f[:-5] for f in os.listdir(os.path.join(OUT, "sports"))
                      if f.endswith(".html") and f != "index.html"}
        self.assertEqual(page_slugs, set(ELIGIBLE))

    def test_every_fixture_row_has_source_capture_and_evidence(self):
        for m in self.seeded["matches"]:
            self.assertTrue(m["official_url"].startswith("https://"), m["id"])
            cap = os.path.join(ROOT, m["capture_file"])
            self.assertTrue(os.path.isfile(cap), m["id"])
            self.assertIn(m["evidence"], ("A", "B"), m["id"])

    def test_counts_add_up(self):
        c = self.lines["counts"]
        self.assertEqual(c["fixture_rows"], len(self.seeded["matches"]))
        self.assertEqual(c["originated_rows"], sum(1 for r in self.lines["rows"] if r["originated"]))
        self.assertEqual(c["prices_originated"],
                         sum(len(mk["outcomes"]) for r in self.lines["rows"] for mk in r["markets"]))
        self.assertEqual(c["band_picks"], len(self.band["selections"]))

    def test_prices_are_consistent_with_probabilities(self):
        for r in self.lines["rows"]:
            for mk in r["markets"]:
                for o in mk["outcomes"]:
                    self.assertGreater(o["p"], 0.0)
                    self.assertLessEqual(o["p"], 1.0)
                    self.assertEqual(o["fair_decimal"], round(1.0 / o["p"], 2), o)
                    dec = 1.0 / o["p"]
                    expect = 100.0 * (dec - 1.0) if dec >= 2.0 else -100.0 / (dec - 1.0)
                    self.assertEqual(o["fair_american"], int(round(expect)))

    def test_market_probabilities_sum_to_one(self):
        for r in self.lines["rows"]:
            for mk in r["markets"]:
                if mk["market"] == "match winner":
                    total = sum(o["p"] for o in mk["outcomes"])
                    self.assertAlmostEqual(total, 1.0, places=3)
                    sides = {o["side"] for o in mk["outcomes"]}
                    self.assertIn("home", sides)
                    self.assertIn("away", sides)

    def test_handicap_and_total_lines_are_half_points(self):
        for r in self.lines["rows"]:
            for mk in r["markets"]:
                if mk["market"] in ("handicap", "match total"):
                    for o in mk["outcomes"]:
                        line = o["line"]
                        self.assertAlmostEqual(line * 2, round(line * 2), places=6)
                        self.assertNotAlmostEqual(line, round(line), places=6)

    def test_band_gate_holds_both_ways(self):
        def in_band(p):
            return 0.7000 <= p <= 250.0 / 350.0 and (1.0 / p) <= 10100.0
        for r in self.lines["rows"]:
            for mk in r["markets"]:
                for o in mk["outcomes"]:
                    self.assertEqual(o["in_band"], in_band(o["p"]),
                                     "%s %s %s" % (r["match_id"], mk["market"],
                                                   o.get("selection", o.get("name"))))
                    if o["confidence"] == "high":
                        self.assertTrue(o["in_band"])

    def test_band_picks_unique_per_fixture_and_in_band(self):
        seen = set()
        for s in self.band["selections"]:
            self.assertNotIn(s["match_id"], seen)
            seen.add(s["match_id"])
            self.assertEqual(s["confidence"], "high")
            self.assertGreaterEqual(s["p"], 0.7000)
            self.assertLessEqual(s["p"], 250.0 / 350.0 + 1e-9)

    def test_independent_recomputation_of_two_fixtures(self):
        """Recompute from the raw captures through a separate code path."""
        teams = curcap("nhl_team_summary_2026-10-22.json")["teams"]
        league = sum(t["gf"] for t in teams) / sum(t["gp"] for t in teams)
        by = {t["abbrev"]: t for t in teams}

        def rating(t):
            w = t["gp"] / (t["gp"] + 8.0)
            return (1 + w * ((t["gf"] / t["gp"]) / league - 1),
                    1 + w * ((t["ga"] / t["gp"]) / league - 1))

        ah, dh = rating(by["BOS"])
        aa, da = rating(by["SJS"])
        lh, la = league * ah * da * 1.05, league * aa * dh / 1.05
        grid = {}
        for i in range(13):
            for j in range(13):
                w = (math.exp(-lh) * lh ** i / math.factorial(i)) * \
                    (math.exp(-la) * la ** j / math.factorial(j))
                grid[i + j] = grid.get(i + j, 0.0) + w
        over = sum(w for t, w in grid.items() if t > 4.5) / sum(grid.values())
        row = self.rows["nhl-2026020170"]
        self.assertAlmostEqual(row["band_pick"]["p"], over, places=3)
        self.assertAlmostEqual(row["expected_total"], lh + la, places=2)

        table = curcap("urc_table_2026-10-22.json")["table"]
        ul = sum(t["pf"] for t in table) / sum(t["pl"] for t in table)
        tb = {t["team"]: t for t in table}

        def urat(t):
            w = t["pl"] / (t["pl"] + 6.0)
            return (1 + w * ((t["pf"] / t["pl"]) / ul - 1),
                    1 + w * ((t["pa"] / t["pl"]) / ul - 1))

        h, a = tb["Leinster Rugby"], tb["Munster Rugby"]
        ah2, dh2 = urat(h)
        aa2, da2 = urat(a)
        mu = (ul * ah2 * da2 + 3.0) - (ul * aa2 * dh2 - 3.0)

        def phi(z):
            return 0.5 * (1 + math.erf(z / math.sqrt(2)))

        p_home = 1 - phi((1.0 - mu) / 13.0)
        p_draw = phi((1.0 - mu) / 13.0) - phi((-1.0 - mu) / 13.0)
        p_away = phi((-1.0 - mu) / 13.0)
        total = p_home + p_draw + p_away
        row = self.rows["urc-292614"]
        self.assertAlmostEqual(row["primary"]["p"], p_home / total, places=3)
        self.assertAlmostEqual(row["expected_margin"], mu, places=2)


class TestPredictions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preds = data("predictions.json")["predictions"]
        cls.band = data("band.json")["selections"]
        cls.rows = {r["match_id"]: r for r in data("lines.json")["rows"]}
        cls.matches = {m["id"]: m for m in data("matches.json")["matches"]}

    def test_one_prediction_per_high_confidence_pick(self):
        self.assertEqual({p["match_id"] for p in self.preds},
                         {s["match_id"] for s in self.band})

    def test_predictions_are_at_least_30_words_and_unique(self):
        texts = []
        for p in self.preds:
            n = len(p["text"].split())
            self.assertGreaterEqual(n, 30, "%s has %d words" % (p["match_id"], n))
            texts.append(p["text"])
        self.assertEqual(len(set(texts)), len(texts))

    def test_prediction_numbers_match_the_model(self):
        for p in self.preds:
            row = self.rows[p["match_id"]]
            self.assertEqual(row["band_pick"]["selection"], p["selection"])
            self.assertAlmostEqual(p["probability"], row["band_pick"]["p"], places=4)
            self.assertEqual(p["fair_american"], row["band_pick"]["fair_american"])

    def test_prediction_names_its_own_fixture_and_selection(self):
        for p in self.preds:
            m = self.matches[p["match_id"]]
            if m["kind"] == "event":
                self.assertIn(m["event"].split("(")[0].strip(), p["fixture"])
            else:
                home, away = m["home"]["name"], m["away"]["name"]
                self.assertTrue(home in p["text"] or home.split()[0] in p["text"]
                                or away in p["text"] or away.split()[0] in p["text"],
                                p["match_id"])
            sel = p["selection"]
            key = sel.split()[0] if sel[0].isalpha() else sel
            self.assertTrue(key in p["text"] or sel in p["text"]
                            or any(tok in p["text"] for tok in sel.split()),
                            "%s selection %r not stated" % (p["match_id"], sel))

    def test_predictions_state_their_price(self):
        for p in self.preds:
            self.assertTrue(("%+d" % p["fair_american"]) in p["text"], p["match_id"])


class TestSiteStructure(unittest.TestCase):
    def snapshot(self):
        out = {}
        for base, _, files in os.walk(OUT):
            for name in files:
                path = os.path.join(base, name)
                with open(path, encoding="utf-8") as handle:
                    out[path] = handle.read()
        return out

    def test_all_expected_pages_exist(self):
        for rel in ("index.html", "matches.html", "lines.html", "picks.html",
                    "predictions.html", "inputs.html", "flagged.html",
                    "sources.html", "methodology.html", "sports/index.html",
                    "assets/style.css"):
            self.assertTrue(os.path.isfile(os.path.join(OUT, rel)), rel)
        for slug in ELIGIBLE:
            self.assertTrue(os.path.isfile(os.path.join(OUT, "sports", slug + ".html")), slug)

    def test_rebuild_is_byte_identical(self):
        before = self.snapshot()
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "relay_build.py")],
                       check=True, cwd=ROOT, capture_output=True)
        after = self.snapshot()
        self.assertEqual(sorted(before), sorted(after))
        for path in sorted(before):
            self.assertEqual(before[path], after[path],
                             "stale generated file: %s" % os.path.relpath(path, ROOT))

    def test_local_links_and_anchors_resolve(self):
        errors = []
        for path in pages():
            parser, _ = collect(path)
            base = os.path.dirname(path)
            for href in parser.hrefs:
                if href.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target, _, frag = href.partition("#")
                if target:
                    resolved = os.path.normpath(os.path.join(base, target))
                    if os.path.isdir(resolved):
                        resolved = os.path.join(resolved, "index.html")
                    if not os.path.isfile(resolved):
                        errors.append("%s -> %s" % (os.path.relpath(path, ROOT), href))
                        continue
                else:
                    resolved = path
                if frag:
                    with open(resolved, encoding="utf-8") as handle:
                        if 'id="%s"' % frag not in handle.read():
                            errors.append("%s -> %s (missing anchor)"
                                          % (os.path.relpath(path, ROOT), href))
        self.assertEqual(errors, [])

    def test_subpage_chrome_resolves_inside_the_layer(self):
        """Exact rendered hrefs (lesson from the /current/ str.replace defect)."""
        for slug in ELIGIBLE:
            parser, text = collect(os.path.join(OUT, "sports", slug + ".html"))
            self.assertIn('href="../index.html"', text, slug)      # brand -> relay dashboard
            self.assertIn('href="../flagged.html"', text, slug)    # nav + footer
            self.assertIn('href="../sports/index.html"', text, slug)
            self.assertIn('href="../assets/style.css"', text, slug)
            self.assertIn('href="../../index.html"', text, slug)   # root dashboard
            self.assertIn('href="../../current/index.html"', text, slug)
            self.assertNotIn('href="../../../', text, slug)
            for href in parser.hrefs:
                if href.startswith(("http://", "https://")) or href.startswith("../../"):
                    continue
                resolved = os.path.normpath(os.path.join(OUT, "sports", href))
                self.assertTrue(resolved.startswith(OUT + os.sep),
                                "%s escapes the layer via %s" % (slug, href))

    def test_official_source_links_are_https(self):
        for path in pages():
            _, text = collect(path)
            for m in re.findall(r'href="(http://[^"]+)"', text):
                self.fail("insecure link %s in %s" % (m, path))

    def test_tables_have_consistent_header_and_cell_counts(self):
        errors = []
        for path in pages():
            parser, _ = collect(path)
            for header, body in parser.tables:
                for cells in body:
                    if cells != header:
                        errors.append("%s: header %d vs row %d"
                                      % (os.path.relpath(path, ROOT), header, cells))
        self.assertEqual(errors, [])

    def test_every_fixture_appears_on_the_matches_page_with_a_source(self):
        _, text = collect(os.path.join(OUT, "matches.html"))
        for m in data("matches.json")["matches"]:
            self.assertIn(m["official_url"], text, m["id"])

    def test_zero_row_sport_pages_explain_themselves(self):
        zero = [s for s in ELIGIBLE
                if not any(m["sport"] == s for m in data("matches.json")["matches"])]
        self.assertTrue(zero)
        for slug in zero:
            _, text = collect(os.path.join(OUT, "sports", slug + ".html"))
            self.assertIn("Zero rows this window", text, slug)
            self.assertRegex(text, r"RL-\d\d", slug)

    def test_flagged_page_lists_every_flag(self):
        _, text = collect(os.path.join(OUT, "flagged.html"))
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import relay_build
        for fid, _, _ in relay_build.FLAGS:
            self.assertIn(fid, text)

    def test_landing_numbers_match_the_data(self):
        """Headline counts must be derived from the data (lesson from PR #120)."""
        _, text = collect(os.path.join(OUT, "index.html"))
        lines = data("lines.json")
        preds = data("predictions.json")
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import relay_build
        for token in ("<b>%d</b>" % lines["counts"]["fixture_rows"],
                      "<b>%d</b>" % lines["counts"]["prices_originated"],
                      "<b>%d</b>" % lines["counts"]["band_picks"],
                      "<b>%d</b>" % preds["counts"]["predictions"],
                      "<b>%d</b>" % len(relay_build.FLAGS)):
            self.assertIn(token, text)

    def test_no_bookmaker_domain_is_linked(self):
        banned = ("bet365", "paddypower", "williamhill", "skybet", "betfair",
                  "draftkings", "fanduel", "unibet", "tipsport")
        for path in pages():
            _, text = collect(path)
            low = text.lower()
            for b in banned:
                self.assertNotIn(b, low, "%s advertises %s" % (path, b))


if __name__ == "__main__":
    unittest.main()
