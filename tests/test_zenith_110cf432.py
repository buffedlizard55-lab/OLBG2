import importlib.util
import json
import subprocess
import sys
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "zenith"
SITE = ROOT / "zenith"
SPEC = importlib.util.spec_from_file_location("zenith_build_test", ROOT / "scripts" / "zenith_build.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
BANNED = re.compile(r"\b(model\w*|verif\w*)\b", re.I)
SPORTS = {"Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball", "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey", "Basketball", "Rugby League"}


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.rows=[]; self.row_links=[]; self.row_header=False; self.inrow=False
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag in ("a", "link", "script", "img"):
            v=d.get("href") if tag in ("a", "link") else d.get("src")
            if v: self.links.append(v)
        if tag=="tr": self.inrow=True; self.row_links=[]; self.row_header=False
        if self.inrow and tag=="th": self.row_header=True
        if self.inrow and tag=="a" and d.get("href", "").startswith("https://"): self.row_links.append(d["href"])
    def handle_endtag(self, tag):
        if tag=="tr" and self.inrow:
            self.rows.append((self.row_header, self.row_links)); self.inrow=False


class ZenithDataTests(unittest.TestCase):
    def test_exact_fifteen_sport_scope_and_all_category_pages(self):
        self.assertEqual(set(load("fixtures")["sports"]), SPORTS)
        for sport in SPORTS:
            slug=next(s["slug"] for s in load("sources")["sports"] if s["sport"]==sport)
            self.assertTrue((SITE/"sports"/f"{slug}.html").is_file())
        self.assertEqual(load("fixtures")["count"], 93)

    def test_fixture_rows_have_unique_ids_official_sources_and_fact_provenance(self):
        matches=load("matches")["matches"]
        self.assertEqual(len({m["id"] for m in matches}),len(matches))
        for m in matches:
            self.assertIn(m["sport"],SPORTS)
            self.assertTrue(m["official_fixture_url"].startswith("https://"),m["id"])
            self.assertTrue(m["facts"],m["id"])
            for fact in m["facts"]:
                self.assertTrue(fact["source_url"].startswith("https://"),m["id"])
                self.assertTrue(fact["source_key"],m["id"])

    def test_fair_odds_and_band_are_recomputed_from_probabilities(self):
        for row in load("lines")["lines"]:
            p=row["probability"]
            expected=round(-100*p/(1-p)) if p>=.5 else round(100*(1-p)/p)
            self.assertEqual(row["our_fair_american"],expected,row["id"])
            self.assertEqual(row["in_user_odds_band"],-250<=expected<=10000,row["id"])
            self.assertFalse(row["olbg_quote_used"])
            self.assertTrue(row["official_fixture_url"].startswith("https://"))

    def test_predictions_unique_long_explicit_and_linked(self):
        rows=load("predictions")["predictions"]
        self.assertTrue(rows)
        openings=set()
        for row in rows:
            self.assertGreaterEqual(row["word_count"],30)
            self.assertEqual(row["word_count"],len(row["text"].split()))
            self.assertFalse(BANNED.search(row["text"]),row["id"])
            if row["selection"].casefold() not in row["text"].casefold():
                # Alternate handicap/total prose may phrase the same selection naturally;
                # require its team/outcome and numeric line to remain explicit.
                numbers=re.findall(r"\d+(?:\.\d+)?",row["selection"])
                self.assertTrue(any(n in row["text"] for n in numbers),row["id"])
                self.assertTrue(any(team and any(part.casefold() in row["text"].casefold() for part in team.split() if len(part)>3) for team in (row.get("home"),row.get("away"))),row["id"])
            opening=" ".join(row["text"].split()[:4]).casefold()
            self.assertNotIn(opening,openings)
            openings.add(opening)
            self.assertTrue(row["official_fixture_url"].startswith("https://"))
            self.assertTrue(row["facts"])
            for fact in row["facts"]: self.assertTrue(fact["source_url"].startswith("https://"))

    def test_olbg_inventory_is_scoped_and_preserves_quote_provenance(self):
        data=load("olbg_events")
        self.assertEqual(data["capture_timestamp_utc"],"2026-10-23T20:36:17Z")
        self.assertEqual(data["total_unique_covered_hub_events"],len(data["events"]))
        for event in data["events"]:
            self.assertTrue(event["event_url"].startswith("https://"))
            for market in event["markets_on_hub"]:
                self.assertIn("not our line",market["quote_note"])

    def test_rendered_rows_link_sources_all_pages_and_local_links_resolve(self):
        for page in SITE.rglob("*.html"):
            parser=PageLinks(); parser.feed(page.read_text(encoding="utf-8"))
            for is_header, links in parser.rows:
                if not is_header: self.assertTrue(links,f"{page.relative_to(ROOT)} has an unlinked table row")
            for href in parser.links:
                u=urlsplit(href)
                if u.scheme or u.netloc or not u.path: continue
                target=(page.parent/unquote(u.path)).resolve()
                if target.is_dir(): target/= "index.html"
                self.assertTrue(target.is_relative_to(ROOT.resolve()),href)
                self.assertTrue(target.is_file(),f"{page.relative_to(ROOT)}: {href}")

    def test_strict_cli_verifier_passes(self):
        run=subprocess.run([sys.executable,str(ROOT/"scripts"/"zenith_verify.py")],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_deterministic_rebuild_and_flagged_findings(self):
        before={p.relative_to(ROOT):p.read_bytes() for p in SITE.rglob("*") if p.is_file()}
        BUILDER.build()
        after={p.relative_to(ROOT):p.read_bytes() for p in SITE.rglob("*") if p.is_file()}
        self.assertEqual(before,after)
        self.assertGreaterEqual(load("flagged")["count"],10)
        self.assertGreaterEqual(load("repo_audit")["count"],10)


if __name__=="__main__": unittest.main()
