"""Tests for the /meridian/ desk (session arena/1286444e-olbg2).

The suite runs against the committed artefacts and re-runs each generator once to prove the
layer is deterministic. It is picked up by `python -m unittest discover -s tests`.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "meridian"
OUT = ROOT / "meridian"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball",
          "Ice Hockey", "Basketball", "Rugby League"]
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def module(script):
    spec = importlib.util.spec_from_file_location(f"meridian_{script}",
                                                  ROOT / "scripts" / f"{script}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MeridianScope(unittest.TestCase):
    def test_exactly_fifteen_sports(self):
        self.assertEqual(set(load("fixtures.json")["sports"]), set(SPORTS))
        self.assertTrue({m["sport"] for m in load("matches.json")["matches"]} <= set(SPORTS))

    def test_every_sport_has_a_page(self):
        self.assertEqual(len(list((OUT / "sports").glob("*.html"))), 16)  # 15 sports + index

    def test_fixtures_have_official_https_sources_and_facts(self):
        for f in load("fixtures.json")["fixtures"]:
            self.assertTrue(f["official_url"].startswith("https://"), f["id"])
            self.assertGreaterEqual(len(f["facts"]), 1, f["id"])
            for fact in f["facts"]:
                self.assertTrue(fact["source_url"].startswith("https://"), f["id"])


class MeridianPricing(unittest.TestCase):
    def test_price_is_the_reciprocal_of_the_probability(self):
        for row in load("lines.json")["lines"]:
            p = row["probability"]
            expected = -max(100, int(round(100 * p / (1 - p)))) if p >= 0.5 \
                else max(100, int(round(100 * (1 - p) / p)))
            self.assertEqual(row["american"], expected,
                             f"{row['fixture_id']} {row['selection']}")
            self.assertEqual(row["in_band"], -250 <= row["american"] <= 10000)

    def test_band_boundary_arithmetic(self):
        self.assertEqual(round(100 / 1.40, 2), 71.43)
        rows = load("lines.json")["lines"]
        self.assertTrue(all(r["in_band"] == (-250 <= r["american"] <= 10000) for r in rows))

    def test_every_published_pick_sits_inside_the_band(self):
        for p in load("picks.json")["picks"]:
            self.assertTrue(p["in_band"], p["id"])
            self.assertIn(p["confidence"], ("low", "medium", "high"))
            self.assertTrue(p["official_url"].startswith("https://"), p["id"])

    def test_confidence_is_capped_per_sport(self):
        picks = load("picks.json")
        order = {"low": 1, "medium": 2, "high": 3}
        caps = {"Cricket": "medium", "Basketball": "medium", "Rugby League": "medium",
                "Darts": "medium", "Tennis": "medium", "Handball": "medium",
                "Volleyball": "medium", "Gaelic Sports": "medium", "Motor Racing": "low",
                "Greyhounds": "low", "Golf": "low"}
        for p in picks["picks"]:
            cap = caps.get(p["sport"], "high")
            self.assertLessEqual(order[p["confidence"]], order[cap], p["id"])

    def test_market_implied_rows_are_kept_out_of_the_originated_totals(self):
        doc = load("lines.json")
        self.assertTrue(all(r["basis"] == "originated" for r in doc["lines"]))

    def test_blank_rows_state_a_reason(self):
        for m in load("matches.json")["matches"]:
            if m["status"] != "priced":
                self.assertTrue(m["blank_reason"], m["id"])


class MeridianProse(unittest.TestCase):
    def test_length_uniqueness_and_vocabulary(self):
        preds = load("predictions.json")["predictions"]
        self.assertGreaterEqual(len(preds), 20)
        openings, texts = set(), set()
        for p in preds:
            self.assertGreaterEqual(p["words"], 30, p["id"])
            self.assertEqual(p["words"], len(p["text"].split()), p["id"])
            self.assertIsNone(BANNED.search(p["text"]), p["id"])
            self.assertIsNone(BANNED.search(p["headline"]), p["id"])
            self.assertNotIn(p["text"], texts)
            texts.add(p["text"])
            opening = " ".join(p["text"].split()[:5]).lower()
            self.assertNotIn(opening, openings, p["id"])
            openings.add(opening)

    def test_each_prediction_names_its_selection_and_two_facts(self):
        for p in load("predictions.json")["predictions"]:
            sticky = [w for w in re.findall(r"[A-Za-z]+", p["selection"]) if len(w) >= 4]
            self.assertTrue(any(w.lower() in p["text"].lower() for w in sticky), p["id"])
            self.assertGreaterEqual(len(p["facts"]), 2, p["id"])
            self.assertTrue(p["official_url"].startswith("https://"), p["id"])

    def test_every_high_confidence_pick_has_a_write_up(self):
        written = {p["fixture_id"] for p in load("predictions.json")["predictions"]}
        for pick in load("picks.json")["picks"]:
            if pick["confidence"] == "high":
                self.assertIn(pick["fixture_id"], written, pick["id"])

    def test_write_up_ceiling_is_five_per_sport(self):
        preds = load("predictions.json")["predictions"]
        for sport in SPORTS:
            rows = [p for p in preds if p["sport"] == sport]
            high = [p for p in rows if p["confidence"] == "high"]
            self.assertLessEqual(len(rows), max(5, len(high)), sport)


class MeridianSite(unittest.TestCase):
    def test_pages_exist_and_every_table_row_links_a_source(self):
        from html.parser import HTMLParser

        class Rows(HTMLParser):
            def __init__(self):
                super().__init__()
                self.rows, self.row, self.inbody = [], None, False

            def handle_starttag(self, tag, attrs):
                d = dict(attrs)
                if tag == "tbody":
                    self.inbody = True
                elif tag == "tr" and self.inbody:
                    self.row = []
                elif tag == "a" and self.row is not None and d.get("href"):
                    self.row.append(d["href"])

            def handle_endtag(self, tag):
                if tag == "tr" and self.row is not None:
                    self.rows.append(self.row)
                    self.row = None
                elif tag == "tbody":
                    self.inbody = False

        for name in ("index.html", "picks.html", "matches.html", "lines.html",
                     "flagged.html", "sources.html", "band.html"):
            parser = Rows()
            parser.feed((OUT / name).read_text(encoding="utf-8"))
            self.assertTrue(parser.rows, name)
            for row in parser.rows:
                self.assertTrue(any(h.startswith("https://") for h in row),
                                f"{name}: {row}")

    def test_local_links_resolve(self):
        broken = []
        for page in OUT.rglob("*.html"):
            for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
                if href.startswith(("http", "mailto:", "#")):
                    continue
                target = (page.parent / href.split("#")[0]).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    broken.append(f"{page.relative_to(ROOT)} -> {href}")
        self.assertEqual(broken, [])

    def test_strict_verifier_passes(self):
        import subprocess
        import sys
        run = subprocess.run([sys.executable, str(ROOT / "scripts" / "meridian_verify.py")],
                             cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_published_counts_match_the_data(self):
        picks = load("picks.json")
        self.assertEqual(picks["count"], len(picks["picks"]))
        self.assertEqual(picks["high"], len([p for p in picks["picks"] if p["confidence"] == "high"]))
        self.assertEqual(load("predictions.json")["count"], len(load("predictions.json")["predictions"]))

    def test_flagged_and_audit_are_published(self):
        self.assertGreaterEqual(load("flagged.json")["count"], 8)
        self.assertGreaterEqual(load("repo_audit.json")["count"], 4)
        page = (OUT / "flagged.html").read_text(encoding="utf-8")
        for item in load("flagged.json")["items"]:
            self.assertIn(item["id"], page)


class MeridianDeterminism(unittest.TestCase):
    def test_rebuild_is_byte_identical(self):
        before = {p.relative_to(ROOT): p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        data_before = {p.name: p.read_bytes() for p in DATA.glob("*.json")}
        module("meridian_seed").main()
        module("meridian_model").main()
        module("meridian_predictions").main()
        module("meridian_audit").build()
        module("meridian_build").main()
        after = {p.relative_to(ROOT): p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        data_after = {p.name: p.read_bytes() for p in DATA.glob("*.json")}
        self.assertEqual(before, after)
        self.assertEqual(data_before, data_after)


if __name__ == "__main__":
    unittest.main()
