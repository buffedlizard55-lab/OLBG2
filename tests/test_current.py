"""Regression tests for the /current/ capture-and-origination layer.

These tests own three jobs:
  1. prove the published pages are byte-identical to a fresh rebuild,
  2. prove every local link, anchor and official source link is well formed,
  3. re-verify the captured official numbers and the originated arithmetic
     independently of scripts/current_model.py.
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
DATA = os.path.join(ROOT, "data", "current")
CAPTURE = os.path.join(DATA, "capture")
OUT = os.path.join(ROOT, "current")

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
            if self._stack and self._stack[-1] == "thead":
                pass
            elif self._in_body:
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
    """Re-check the official numbers we transcribed, independently."""

    def test_ehf_24_clubs_internally_consistent(self):
        clubs = capture("ehf_standings_2026-10-22.json")["clubs"]
        self.assertEqual(len(clubs), 24)
        self.assertEqual(len({c["club"] for c in clubs}), 24)
        for c in clubs:
            self.assertEqual(c["goals_for"] - c["goals_against"], c["diff"], c["club"])
            self.assertEqual(c["w"] + c["d"] + c["l"], c["gp"], c["club"])
        self.assertEqual(sum(c["goals_for"] for c in clubs),
                         sum(c["goals_against"] for c in clubs))

    def test_mlb_30_clubs_internally_consistent(self):
        doc = capture("mlb_standings_sample_2026-10-22.json")
        teams = doc["teams"]
        self.assertEqual(len(teams), 30)
        self.assertEqual(len({t["team_id"] for t in teams}), 30)
        for t in teams:
            self.assertEqual(t["wins"] + t["losses"], t["gp"], t["team"])
            self.assertEqual(t["runs_scored"] - t["runs_allowed"], t["run_differential"])
        self.assertEqual(doc["league_avg_runs_per_game"],
                         round(sum(t["runs_scored"] for t in teams) /
                               sum(t["gp"] for t in teams), 4))
        self.assertEqual(doc["total_runs_scored"], doc["total_runs_allowed"])

    def test_nhl_32_clubs(self):
        teams = capture("nhl_team_summary_2026-10-22.json")["teams"]
        self.assertEqual(len(teams), 32)
        self.assertEqual(len({t["teamId"] for t in teams}), 32)
        for t in teams:
            self.assertEqual(t["w"] + t["l"] + t["otl"], t["gp"], t["team"])
            self.assertAlmostEqual(t["gfpg"], t["gf"] / t["gp"], places=4)

    def test_urc_16_clubs(self):
        table = capture("urc_table_2026-10-22.json")["table"]
        self.assertEqual(len(table), 16)
        self.assertEqual(len({t["team"] for t in table}), 16)
        for t in table:
            self.assertEqual(t["w"] + t["d"] + t["l"], t["pl"], t["team"])
            self.assertEqual(t["pf"] - t["pa"], t["diff"], t["team"])
            self.assertEqual(len(t["form"]), t["pl"], t["team"])

    def test_euroleague_20_clubs(self):
        st = capture("euroleague_round7_2026-10-22.json")["standings"]
        self.assertEqual(len(st), 20)
        self.assertEqual(sorted(c["pos"] for c in st), list(range(1, 21)))
        self.assertEqual(sorted(c["code"] for c in st),
                         sorted({c["code"] for c in st}))
        for c in st:
            self.assertEqual(c["pts_for"] - c["pts_against"], c["diff"], c["code"])
            self.assertEqual(c["w"] + c["l"], c["gp"], c["code"])

    def test_snooker_results_are_best_of_seven(self):
        results = capture("wst_ni_open_2026-10-22.json")["completed_results_first_hand"]
        self.assertEqual(len(results), 21)
        for r in results:
            self.assertEqual(max(r["s1"], r["s2"]), 4, r)
            self.assertNotEqual(r["s1"], r["s2"], r)

    def test_f1_standings_and_winners(self):
        doc = capture("f1_calendar_2026-10-22.json")
        drivers = doc["drivers_standings"]
        self.assertEqual(len(drivers), 23)
        self.assertEqual(sorted(d["pos"] for d in drivers), list(range(1, 24)))
        self.assertEqual(drivers, sorted(drivers, key=lambda d: -d["pts"]))
        self.assertEqual(len(doc["race_winners_first_hand"]), 7)

    def test_every_capture_declares_an_official_source(self):
        for name in sorted(os.listdir(CAPTURE)):
            if not name.endswith(".json"):
                continue
            doc = capture(name)
            urls = [v for k, v in doc.items()
                    if k.startswith("source_url") and isinstance(v, str) and v]
            self.assertTrue(urls, name)
            for url in urls:
                self.assertTrue(url.startswith("https://"), (name, url))


class TestModelOutputs(unittest.TestCase):
    def setUp(self):
        self.matches = data("matches.json")
        self.lines = data("lines.json")
        self.band = data("band.json")
        self.preds = data("predictions.json")
        self.rows = {r["match_id"]: r for r in self.lines["rows"]}

    def test_sport_scope_is_exactly_the_17_eligible(self):
        self.assertEqual(self.matches["sport_order"], ELIGIBLE)
        self.assertEqual(sorted(self.matches["sports"]), sorted(ELIGIBLE))
        for m in self.matches["matches"]:
            self.assertIn(m["sport"], ELIGIBLE)

    def test_zero_row_sports_all_carry_a_documented_reason(self):
        zero = [s for s, i in self.matches["sports"].items() if i["fixture_rows"] == 0]
        self.assertEqual(len(zero), 10)
        for slug in zero:
            info = self.matches["sports"][slug]
            self.assertTrue(info["zero_row_reason"], slug)
            self.assertRegex(info["zero_row_flag"], r"^CU-\d\d$")
            self.assertGreaterEqual(len(info["zero_row_reason"].split()), 20, slug)

    def test_every_fixture_row_has_an_official_source_and_a_capture_file(self):
        for m in self.matches["matches"]:
            self.assertTrue(m["official_url"].startswith("https://"), m["id"])
            self.assertTrue(os.path.isfile(os.path.join(ROOT, m["capture_file"])), m["id"])
            self.assertTrue(m["source_name"], m["id"])
            self.assertTrue(m["home"]["name"], m["id"])

    def test_originated_counts_add_up(self):
        c = self.lines["counts"]
        self.assertEqual(c["originated_rows"] + c["blank_rows"], c["fixture_rows"])
        self.assertEqual(len(self.lines["rows"]), c["fixture_rows"])
        self.assertEqual(c["prices_originated"],
                         sum(len(mk["outcomes"]) for r in self.lines["rows"]
                             for mk in r["markets"]))
        self.assertEqual(c["high_confidence"] + c["medium_confidence"] + c["low_confidence"],
                         c["originated_rows"])

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
                if mk["market"] == "race winner (outright)":
                    continue
                sides = [o for o in mk["outcomes"] if o["side"] in ("home", "away", "draw")]
                if mk["market"] == "match winner":
                    # each published probability is rounded to four decimals, so a
                    # three-way market can sum to 0.9999 or 1.0001 by rounding alone
                    self.assertAlmostEqual(sum(o["p"] for o in sides), 1.0, places=3)
                else:
                    home = [o for o in sides if o["side"] == "home"]
                    away = [o for o in sides if o["side"] == "away"]
                    self.assertEqual(len(home), len(away))
                    for h, a in zip(sorted(home, key=lambda x: x["line"]),
                                    sorted(away, key=lambda x: x["line"])):
                        self.assertEqual(h["line"], a["line"])
                        self.assertAlmostEqual(h["p"] + a["p"], 1.0, places=9)

    def test_handicap_lines_are_half_points_and_never_push(self):
        for r in self.lines["rows"]:
            for mk in r["markets"]:
                if mk["market"] != "handicap":
                    continue
                for o in mk["outcomes"]:
                    self.assertAlmostEqual(abs(o["line"]) % 1.0, 0.5, places=9,
                                           msg="%s %s" % (r["match_id"], o["selection"]))

    def test_total_lines_are_half_points(self):
        for r in self.lines["rows"]:
            for mk in r["markets"]:
                if mk["market"] != "match total":
                    continue
                for o in mk["outcomes"]:
                    self.assertAlmostEqual(abs(o["line"]) % 1.0, 0.5, places=9)

    def test_high_confidence_gate_holds_both_ways(self):
        for r in self.lines["rows"]:
            if not r["originated"]:
                self.assertIsNone(r["primary"])
                continue
            p = r["primary"]["p"]
            dec = 1.0 / p
            american = 100.0 * (dec - 1.0) if dec >= 2.0 else -100.0 / (dec - 1.0)
            in_band = p >= 0.70 and -250.0 <= american <= 10000.0
            if r["primary"]["confidence"] == "high":
                self.assertTrue(in_band, r["match_id"])
                self.assertTrue(r["band_pick"], r["match_id"])
            else:
                self.assertFalse(in_band or r["band_pick"], r["match_id"])
            if p >= 0.70 and not in_band:
                self.assertEqual(r["primary"]["confidence"], "medium", r["match_id"])

    def test_band_picks_are_unique_per_fixture_and_satisfy_the_gate(self):
        ids = [b["match_id"] for b in self.band["selections"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), self.lines["counts"]["band_picks"])
        for b in self.band["selections"]:
            self.assertGreaterEqual(b["p"], 0.70)
            dec = 1.0 / b["p"]
            self.assertGreaterEqual(round(dec, 2), 1.40)
            american = 100.0 * (dec - 1.0) if dec >= 2.0 else -100.0 / (dec - 1.0)
            self.assertLessEqual(american, 10000.0)
            self.assertEqual(b["confidence"], "high")

    def test_blank_rows_publish_a_reason_and_a_source(self):
        blanks = data("blanks.json")["rows"]
        self.assertEqual(len(blanks), self.lines["counts"]["blank_rows"])
        for b in blanks:
            self.assertGreaterEqual(len(b["reason"].split()), 20)
            self.assertTrue(b["official_url"].startswith("https://"))

    def test_independent_recomputation_of_two_fixtures(self):
        """Recompute from the raw captures through a separate code path."""
        teams = capture("nhl_team_summary_2026-10-22.json")["teams"]
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

        table = capture("urc_table_2026-10-22.json")["table"]
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
        row = self.rows["urc-r4-292614"]
        self.assertAlmostEqual(row["primary"]["p"], p_home / total, places=3)
        self.assertAlmostEqual(row["expected_margin"], mu, places=2)


class TestPredictions(unittest.TestCase):
    def setUp(self):
        self.preds = data("predictions.json")["predictions"]
        self.band = {b["match_id"]: b for b in data("band.json")["selections"]}

    def test_one_prediction_per_high_confidence_pick(self):
        self.assertEqual({p["match_id"] for p in self.preds}, set(self.band))
        self.assertEqual({p["id"] for p in self.preds},
                         {"pred-" + m for m in self.band})

    def test_predictions_are_at_least_30_words_and_unique(self):
        texts = [p["text"] for p in self.preds]
        self.assertEqual(len(texts), len(set(texts)))
        for p in self.preds:
            words = p["text"].split()
            self.assertGreaterEqual(len(words), 30, p["id"])
            self.assertEqual(p["word_count"], len(words))
            self.assertEqual(p["confidence"], "high")

    def test_prediction_numbers_match_the_model(self):
        for p in self.preds:
            b = self.band[p["match_id"]]
            self.assertEqual(p["selection"], b["selection"], p["id"])
            self.assertEqual(p["probability"], b["p"], p["id"])
            self.assertEqual(p["fair_decimal"], b["fair_decimal"], p["id"])
            self.assertEqual(p["fair_american"], b["fair_american"], p["id"])
            self.assertEqual(p["market"], b["market"], p["id"])

    def test_prediction_names_its_own_fixture(self):
        matches = {m["id"]: m for m in data("matches.json")["matches"]}
        for p in self.preds:
            m = matches[p["match_id"]]
            names = [m["home"]["name"]] + ([m["away"]["name"]] if m["away"] else [])
            text = p["text"].lower()
            hit = any(n.lower().split()[0] in text for n in names) or \
                any(n.lower().split()[-1] in text for n in names)
            self.assertTrue(hit, "%s names no side of %s" % (p["id"], names))

    def test_every_prediction_fact_carries_an_official_link(self):
        for p in self.preds:
            self.assertGreaterEqual(len(p["facts_used"]), 2, p["id"])
            for f in p["facts_used"]:
                self.assertTrue(f["source_url"].startswith("https://"), (p["id"], f))
                self.assertTrue(f["fact"], p["id"])

    def test_predictions_state_their_price(self):
        for p in self.preds:
            self.assertIn(str(abs(p["fair_american"])), p["text"], p["id"])


class TestSiteStructure(unittest.TestCase):
    def test_all_expected_pages_exist(self):
        expect = ["index.html", "matches.html", "lines.html", "picks.html",
                  "predictions.html", "inputs.html", "flagged.html", "sources.html",
                  "methodology.html", "sports/index.html", "assets/style.css"]
        expect += ["sports/%s.html" % slug for slug in ELIGIBLE]
        for rel in expect:
            self.assertTrue(os.path.isfile(os.path.join(OUT, rel)), rel)

    @staticmethod
    def snapshot():
        snap = {}
        for path in pages() + [os.path.join(OUT, "assets", "style.css")]:
            with open(path, "rb") as handle:
                snap[path] = handle.read()
        return snap

    def test_rebuild_is_byte_identical(self):
        before = self.snapshot()
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "current_build.py")],
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

    def test_official_source_links_are_https(self):
        bad = []
        for path in pages():
            _, text = collect(path)
            for href in re.findall(r'href="(https?://[^"]+)"', text):
                if not href.startswith("https://"):
                    bad.append((os.path.relpath(path, ROOT), href))
        self.assertEqual(bad, [])

    def test_tables_have_consistent_header_and_cell_counts(self):
        bad = []
        for path in pages():
            parser, _ = collect(path)
            for head, body in parser.tables:
                for cells in body:
                    if cells != head:
                        bad.append("%s: header %d cells vs row %d"
                                   % (os.path.relpath(path, ROOT), head, cells))
        self.assertEqual(bad[:20], [])

    def test_every_fixture_appears_on_the_matches_page_with_a_source(self):
        _, text = collect(os.path.join(OUT, "matches.html"))
        for m in data("matches.json")["matches"]:
            self.assertIn(m["official_url"], text, m["id"])

    def test_zero_row_sport_pages_explain_themselves(self):
        sports = data("matches.json")["sports"]
        for slug in ELIGIBLE:
            path = os.path.join(OUT, "sports", slug + ".html")
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            if sports[slug]["fixture_rows"] == 0:
                self.assertIn(sports[slug]["zero_row_flag"], text, slug)
                self.assertIn("0 rows", text, slug)
            else:
                self.assertIn("Official fixture page", text, slug)

    def test_flagged_page_lists_every_flag_and_blank(self):
        with open(os.path.join(OUT, "flagged.html"), encoding="utf-8") as handle:
            text = handle.read()
        for flag in data("matches.json")["excluded"]:
            self.assertIn(flag["reason_flag"], text, flag["reason_flag"])
        for slug, info in data("matches.json")["sports"].items():
            if info["zero_row_flag"]:
                self.assertIn(info["zero_row_flag"], text, slug)
        for b in data("blanks.json")["rows"]:
            self.assertIn(b["match_id"].split("-")[0], text)

    def test_no_page_advertises_a_bookmaker_price(self):
        for path in pages():
            with open(path, encoding="utf-8") as handle:
                text = handle.read().lower()
            for term in ("bet365", "pinnacle", "william hill", "ladbrokes", "oddschecker"):
                self.assertNotIn(term, text, (path, term))


class TestPipelineReproducibility(unittest.TestCase):
    def test_seed_and_model_are_deterministic(self):
        snaps = {}
        for name in ("matches.json", "lines.json", "band.json", "blanks.json"):
            with open(os.path.join(DATA, name), "rb") as handle:
                snaps[name] = handle.read()
        for script in ("current_seed.py", "current_model.py"):
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", script)],
                           check=True, cwd=ROOT, capture_output=True)
        for name, before in snaps.items():
            with open(os.path.join(DATA, name), "rb") as handle:
                self.assertEqual(before, handle.read(), "%s is not reproducible" % name)

    def test_predictions_file_is_the_only_hand_authored_input(self):
        doc = data("predictions.json")
        self.assertIn("hand-authored", doc["generated_by"])
        self.assertEqual(len(doc["predictions"]), doc["counts"]["predictions"])


if __name__ == "__main__":
    unittest.main()
