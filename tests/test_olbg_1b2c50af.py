from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "olbg"
OUT = ROOT / "olbg"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def ascii_name(value):
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


NUMBER = re.compile(r"(?<![\w])(?:\d+(?:[.:–-]\d+)*|\.\d+)")


def normalized_number(token):
    token = token.replace("–", "-")
    if re.fullmatch(r"(?:\d+)?\.\d+", token):
        return str(float(token))
    return token


class CanonicalRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load("source.json")
        cls.matches = load("matches.json")["matches"]
        cls.events = {event["id"]: event for event in cls.matches}
        cls.predictions = load("predictions.json")["predictions"]
        cls.summary = load("summary.json")["counts"]

    def test_fresh_hub_audit_has_exact_scope_and_all_sports(self):
        checks = self.source["review"]["olbg_checks"]
        self.assertEqual(len(checks), 16)
        self.assertEqual({c["sport"] for c in checks}, {s["slug"] for s in self.source["sports"]})
        self.assertEqual(sum(c["sport"] == "gaelic-sports" for c in checks), 2)
        self.assertEqual(len(self.source["discovery"]), 16)
        for check in checks:
            self.assertIn("No tips found", check["observed_text"])
            self.assertTrue(check["url"].startswith("https://www.olbg.com/betting-tips/"))
        self.assertIn("not a claim", self.source["review"]["olbg_scope_note"])
        self.assertEqual(self.source["research_cutoff"], self.source["review"]["audit_cutoff"])

    def test_committed_raw_captures_match_manifest(self):
        manifest = self.source["capture_manifest"]
        self.assertEqual(len(manifest["captures"]), 3)
        for item in manifest["captures"]:
            blob = (DATA / "captures" / item["path"]).read_bytes()
            self.assertEqual(len(blob), item["bytes"])
            self.assertEqual(hashlib.sha256(blob).hexdigest(), item["sha256"])
            self.assertEqual(item["status"], 200)
            json.loads(blob)

    def test_every_nhl_team_input_matches_the_raw_official_capture(self):
        raw = json.loads((DATA / "captures" / "nhl_team_summary_2026-10-23.json").read_text())
        rows = raw["data"]
        teams = self.source["inputs"]["nhl"]["teams"]
        self.assertEqual(len(rows), 32)
        self.assertEqual(len(teams), 32)
        fields = {"gp": "gamesPlayed", "gf": "goalsFor", "ga": "goalsAgainst", "w": "wins", "l": "losses", "otl": "otLosses", "points": "points", "team_id": "teamId"}
        for row in rows:
            team = teams[ascii_name(row["teamFullName"])]
            for ours, theirs in fields.items():
                self.assertEqual(team[ours], row[theirs], row["teamFullName"])

    def test_all_five_official_sunday_nhl_games_are_reconciled(self):
        raw = json.loads((DATA / "captures" / "nhl_schedule_2026-10-25.json").read_text())
        day = next(d for d in raw["gameWeek"] if d["date"] == "2026-10-25")
        expected = {g["id"] for g in day["games"]}
        self.assertEqual(expected, {2026020180, 2026020181, 2026020182, 2026020183, 2026020184})
        by_id = {g["id"]: g for g in day["games"]}
        team_names = {r["teamId"]: ascii_name(r["teamFullName"]) for r in json.loads((DATA / "captures" / "nhl_team_summary_2026-10-23.json").read_text())["data"]}
        actual = {
            int(event["id"].rsplit("-", 1)[1])
            for event in self.matches
            if event["sport"] == "ice-hockey"
            and event["id"].rsplit("-", 1)[1].isdigit()
            and int(event["id"].rsplit("-", 1)[1]) in expected
        }
        self.assertEqual(actual, expected)
        for game_id in expected:
            game, event = by_id[game_id], self.events[f"nhl-{game_id}"]
            self.assertEqual(event["start_utc"], game["startTimeUTC"])
            self.assertEqual(event["date"], "2026-10-25")
            self.assertEqual(event["venue"], game["venue"]["default"])
            self.assertEqual(event["neutral_site"], game["neutralSite"])
            self.assertEqual(event["pricing"]["away"], team_names[game["awayTeam"]["id"]])
            self.assertEqual(event["pricing"]["home"], team_names[game["homeTeam"]["id"]])
            self.assertEqual(event["provenance"], "official_context")
            self.assertIsNone(event["olbg_url"])
            self.assertIn("FUT", event["official_status"])
            self.assertTrue(any(s["url"].endswith("/score/2026-10-25") for s in event["official_sources"]))
        self.assertTrue(self.events["nhl-2026020182"]["neutral_site"])
        self.assertEqual(self.events["nhl-2026020182"]["venue"], "Princess Auto Stadium")

    def test_high_predictions_have_fact_level_evidence_and_supported_numbers(self):
        self.assertEqual(len(self.predictions), 7)
        self.assertEqual(Counter(p["sport"] for p in self.predictions), {"ice-hockey": 5, "basketball": 2})
        normalized_texts = set()
        for pred in self.predictions:
            facts = pred["facts"]
            self.assertGreaterEqual(len(facts), 4)
            self.assertTrue(pred["reviewed_at"])
            self.assertTrue(pred["review_scope"])
            kinds = {f["kind"] for f in facts}
            self.assertGreaterEqual(kinds, {"team_form", "availability"})
            self.assertTrue(kinds & {"recent_form", "recent_history"})
            self.assertTrue(kinds & {"player", "goalie"})
            official_urls = {s["url"] for s in pred["official_sources"] if s["kind"] == "official"}
            for fact in facts:
                self.assertIn(fact["source_url"], official_urls)
                self.assertTrue(fact["source_url"].startswith("https://"))
            prose_numbers = {normalized_number(n) for n in NUMBER.findall(pred["text"])}
            fact_numbers = {normalized_number(n) for f in facts for n in NUMBER.findall(f["text"])}
            self.assertLessEqual(prose_numbers, fact_numbers, (pred["event_id"], prose_numbers - fact_numbers))
            normalized = re.sub(r"\W+", " ", pred["text"].lower()).strip()
            self.assertNotIn(normalized, normalized_texts)
            normalized_texts.add(normalized)

    def test_sixth_in_band_nhl_candidate_has_an_explicit_daily_cap(self):
        event = self.events["nhl-2026020170"]
        self.assertEqual(event["confidence"], "medium")
        self.assertIn("sixth in-band", event["cap_reason"])
        self.assertTrue(any(s["url"].endswith("/2026020170/landing") for s in event["official_sources"]))
        flags = load("flagged.json")["items"]
        cap = next(f for f in flags if f["id"] == "CAP-nhl-2026020170-winner")
        self.assertEqual(cap["detail"], event["cap_reason"])

    def test_clippers_road_column_reconciliation_is_preserved(self):
        clippers = self.source["inputs"]["nba"]["teams"]["LAC"]
        self.assertEqual((clippers["road_w"], clippers["road_l"]), (19, 22))
        self.assertEqual((clippers["home_w"], clippers["home_l"]), (23, 18))
        reconciliation = self.source["review"]["input_reconciliations"]
        self.assertEqual([r["id"] for r in reconciliation], ["NBA-ROAD-COLUMN-18"])
        self.assertIn("ROAD 19-22", reconciliation[0]["result"])

    def test_rendered_audit_covers_every_row_and_raw_capture(self):
        text = (OUT / "sources.html").read_text(encoding="utf-8")
        for event in self.matches:
            self.assertIn(f'matches.html#{event["id"]}', text)
        for check in self.source["review"]["olbg_checks"]:
            self.assertIn(check["url"], text)
        for capture in self.source["capture_manifest"]["captures"]:
            self.assertIn(capture["sha256"], text)
            self.assertIn(capture["path"], text)
        for pred in self.predictions:
            page = (OUT / "sports" / f'{pred["sport"]}.html').read_text(encoding="utf-8")
            self.assertIn("fact-level evidence links", page)
            for fact in pred["facts"]:
                self.assertIn(fact["source_url"].replace("&", "&amp;"), page)


if __name__ == "__main__":
    unittest.main()
