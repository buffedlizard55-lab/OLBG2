#!/usr/bin/env python3
"""Acceptance tests for the /summit/ desk (session arena/84013d5f-olbg2).

These tests run against the committed artefacts and the desk verifier; they are a drift
guard for the desk, not a re-run of the network collection.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "summit"
SITE = ROOT / "summit"
SPORTS = [
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
    "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
    "Basketball", "Rugby League",
]
BANNED = re.compile(r"\b(model|models|modelled|modeled|modelling|modeling|verify|verified|verifies|verification)\b", re.I)


def load(name):
    with open(DATA / name) as f:
        return json.load(f)


def american(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return int(round(-100.0 * p / (1 - p))) if p >= 0.5 else int(round(100.0 * (1 - p) / p))


def load_verifier():
    spec = importlib.util.spec_from_file_location("summit_verify", ROOT / "scripts" / "summit_verify.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SummitData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = load("matches.json")
        cls.lines = load("lines.json")
        cls.picks = load("picks.json")
        cls.preds = load("predictions.json")
        cls.sources = load("sources.json")
        cls.flags = load("flagged.json")
        cls.audit = load("repo_audit.json")

    def test_all_fifteen_sports_have_fixtures(self):
        have = {m["sport"] for m in self.matches["fixtures"]}
        self.assertEqual(have, set(SPORTS))

    def test_no_out_of_scope_sport(self):
        banned = {"Aussie Rules", "Esports", "eSports", "Football", "Soccer", "American Football",
                  "Horse Racing", "Boxing", "MMA", "UFC"}
        for row in self.matches["fixtures"]:
            self.assertNotIn(row["sport"], banned)
        for p in self.picks["picks"]:
            self.assertNotIn(p["sport"], banned)
        for pr in self.preds["predictions"]:
            self.assertNotIn(pr["sport"], banned)

    def test_originated_fixtures_have_official_sources(self):
        for m in self.matches["fixtures"]:
            if m["status"] == "originated":
                self.assertTrue(m["official_source_url"].startswith("https://"), m["id"])
                self.assertTrue(m["facts"], m["id"])
                for f in m["facts"]:
                    self.assertTrue(f.get("source_url", "").startswith("https://"), (m["id"], f))

    def test_fact_keys_registered(self):
        keys = {s["key"] for s in self.sources["sources"]}
        for m in self.matches["fixtures"]:
            for f in m["facts"]:
                self.assertIn(f.get("source_key"), keys, (m["id"], f.get("source_key")))

    def test_blank_rows_state_reason(self):
        blanks = [m for m in self.matches["fixtures"] if m["status"] == "blank"]
        self.assertTrue(blanks)
        for m in blanks:
            self.assertTrue((m.get("note") or "").strip(), m["id"])

    def test_price_arithmetic(self):
        for r in self.lines["lines"]:
            p = round(r["probability"], 6)
            self.assertEqual(american(p), r["fair_american"], r["id"])
            self.assertAlmostEqual(1 / p, r["fair_decimal"], delta=max(0.002, 0.0005 * r["fair_decimal"]))
            self.assertGreaterEqual(r["offered_decimal"], r["fair_decimal"], r["id"])

    def test_band_and_labels(self):
        for r in list(self.lines["lines"]) + list(self.picks["picks"]):
            expect = -250 <= r["fair_american"] <= 10000
            self.assertEqual(expect, r["in_band"], r["id"])
            if r["confidence"] == "high":
                self.assertGreaterEqual(r["probability"], 0.70, r["id"])
            if r["confidence"] == "low":
                self.assertLess(r["probability"], 0.60, r["id"])

    def test_predictions(self):
        fixes = {m["id"]: m for m in self.matches["fixtures"]}
        by_pick = {p["id"]: p for p in self.picks["picks"]}
        openings, bodies = set(), set()
        for pr in self.preds["predictions"]:
            self.assertGreaterEqual(pr["word_count"], 30, pr["id"])
            self.assertEqual(len(pr["text"].split()), pr["word_count"], pr["id"])
            self.assertIsNone(BANNED.search(pr["text"]), pr["id"])
            self.assertIsNone(BANNED.search(pr["headline"]), pr["id"])
            fixture = fixes[pr["fixture_id"]]
            values = {f.get("value") or f.get("text") for f in fixture["facts"]}
            for f in pr["facts"]:
                self.assertIn(f["claim"], values, pr["id"])
                self.assertTrue(f["source_url"].startswith("https://"), pr["id"])
            op = " ".join(pr["text"].split()[:3]).lower()
            self.assertNotIn(op, openings, pr["id"])
            openings.add(op)
            self.assertNotIn(pr["text"], bodies, pr["id"])
            bodies.add(pr["text"])
            pick = by_pick[pr["pick_id"]]
            self.assertEqual(pick["selection"], pr["selection"], pr["id"])
            self.assertEqual(pick["probability"], pr["probability"], pr["id"])
            self.assertEqual(pick["fair_american"], pr["fair_american"], pr["id"])


class SummitVerifier(unittest.TestCase):
    def test_verifier_exits_zero(self):
        res = subprocess.run([sys.executable, str(ROOT / "scripts" / "summit_verify.py")],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_no_broken_local_links(self):
        mod = load_verifier()
        errs = mod.local_link_errors()
        self.assertEqual(errs, [], "\n".join(errs))


if __name__ == "__main__":
    unittest.main()
