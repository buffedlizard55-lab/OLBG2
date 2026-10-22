#!/usr/bin/env python3
"""Tests for final desk pipeline"""
import unittest
import json
import os

class TestFinalDesk(unittest.TestCase):
    def setUp(self):
        with open("data/final-desk/matches.json") as f:
            self.data = json.load(f)
        with open("data/final-desk/predictions.json") as f:
            self.predictions = json.load(f)
    
    def test_matches_exist(self):
        self.assertGreater(len(self.data["matches"]), 0)
    
    def test_all_matches_have_sources(self):
        for m in self.data["matches"]:
            self.assertIn("official_url", m)
            self.assertTrue(m["official_url"].startswith("https://"))
    
    def test_confidence_grading(self):
        for m in self.data["matches"]:
            self.assertIn(m["confidence"], ["high", "medium", "low"])
    
    def test_high_confidence_in_band(self):
        for p in self.predictions:
            amer = p["fair_odds"]["american"]
            amer_val = float(amer.replace("+", ""))
            self.assertGreaterEqual(amer_val, -250)
            self.assertLessEqual(amer_val, 10000)
    
    def test_predictions_word_count(self):
        for p in self.predictions:
            self.assertGreaterEqual(p["word_count"], 30)
    
    def test_sports_coverage(self):
        sports = set(m["sport"] for m in self.data["matches"])
        self.assertGreater(len(sports), 0)
    
    def test_site_built(self):
        self.assertTrue(os.path.exists("final-desk/index.html"))
        self.assertTrue(os.path.exists("final-desk/matches.html"))
        self.assertTrue(os.path.exists("final-desk/picks.html"))

if __name__ == "__main__":
    unittest.main()
