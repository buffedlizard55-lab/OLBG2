#!/usr/bin/env python3
"""
scripts/beacon_verify.py — End-to-end structural, mathematical, and link verifier for /beacon/.
"""
from __future__ import annotations

import json
import math
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "beacon"
SITE_DIR = ROOT / "beacon"

BANNED_HREF_SUBSTRINGS = (
    "wst.tv/tournaments/northern-ireland-open-2026",
    "wst.tv/matches",
    "unitedrugby.com/standings",
    "liquipedia.net",
    "Basketball/19",
    "Australian_Rules/27",
    "Esports/28",
    "2025-category-one-schedule",
)


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.in_tbody = False
        self.in_tr = False
        self.cur_tr_ext_links: list[str] = []
        self.tbody_rows_total = 0
        self.tbody_rows_with_ext_link = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        amap = dict(attrs)
        if amap.get("id"):
            self.ids.add(amap["id"])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.cur_tr_ext_links = []
        elif tag in ("a", "link", "script"):
            target = amap.get("href") or amap.get("src")
            if target:
                self.links.append(target)
                if tag == "a" and self.in_tr and target.startswith(("https://", "http://")):
                    self.cur_tr_ext_links.append(target)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_tr:
            self.tbody_rows_total += 1
            if self.cur_tr_ext_links:
                self.tbody_rows_with_ext_link += 1
            self.in_tr = False
        elif tag == "tbody":
            self.in_tbody = False


def verify_all() -> dict:
    errors: list[str] = []

    sports = json.loads((DATA_DIR / "sports.json").read_text())
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
    picks = json.loads((DATA_DIR / "predictions.json").read_text())["predictions"]
    flags = json.loads((DATA_DIR / "flagged.json").read_text())["flagged"]
    summary = json.loads((DATA_DIR / "summary.json").read_text())

    eligible_ids = {s["olbg_id"] for s in sports["eligible"]}
    excluded_ids = {s["olbg_id"] for s in sports["excluded"]}
    if len(eligible_ids) != 17:
        errors.append(f"Expected 17 eligible sports, got {len(eligible_ids)}")

    seen_sports = {m["sport"] for m in matches}
    if len(seen_sports) != 17:
        errors.append(f"Matches cover {len(seen_sports)}/17 sports")

    # Verify match invariants
    high_max = 5.0 / 7.0
    for m in matches:
        if m["olbg_id"] in excluded_ids or m["olbg_id"] not in eligible_ids:
            errors.append(f"Invalid OLBG ID on {m['id']}: {m['olbg_id']}")
        for u in (m["official_url"], m["olbg_url"]):
            if not u.startswith("https://"):
                errors.append(f"Missing https URL on {m['id']}: {u}")
            for bad in BANNED_HREF_SUBSTRINGS:
                if bad in u:
                    errors.append(f"Banned URL substring '{bad}' on {m['id']}: {u}")
        if m["match_state"] == "unverified_blank":
            if m["markets"] is not None or m["winner_pick"]["selection"] != "—":
                errors.append(f"Unverified row {m['id']} must keep blank markets/selection")
        else:
            mk = m["markets"]
            if mk.get("handicap"):
                lh = abs(mk["handicap"]["line_home"])
                if lh < 1.5 or abs((lh - math.floor(lh)) - 0.5) > 1e-9:
                    errors.append(f"Invalid handicap line {lh} on {m['id']}")
            if mk.get("total"):
                tl = abs(mk["total"]["line"])
                if abs((tl - math.floor(tl)) - 0.5) > 1e-9:
                    errors.append(f"Invalid total line {tl} on {m['id']}")
            wp = m["winner_pick"]
            if wp["confidence"] == "high":
                if m["match_state"] != "upcoming":
                    errors.append(f"Non-upcoming match {m['id']} graded high")
                if not (0.7000 <= wp["prob_exact"] <= high_max):
                    errors.append(f"Winner high pick {m['id']} outside [0.7000, 5/7]: {wp['prob_exact']}")

    # Verify high-confidence picks invariants
    seen_prose: set[str] = set()
    for p in picks:
        if p["confidence"] != "high":
            errors.append(f"Non-high pick in predictions.json: {p['pick_id']}")
        if not (0.7000 <= p["model_prob_exact"] <= high_max):
            errors.append(f"Pick {p['pick_id']} prob {p['model_prob_exact']} outside [0.7000, 5/7]")
        if not (1.40 <= p["fair_decimal_exact"] <= 101.00):
            errors.append(f"Pick {p['pick_id']} decimal {p['fair_decimal_exact']} outside [1.40, 101.00]")
        if not (-250 <= p["fair_american"] <= 10000):
            errors.append(f"Pick {p['pick_id']} american {p['fair_american']} outside [-250, +10000]")
        words = p["prediction"].split()
        if len(words) < 30:
            errors.append(f"Pick {p['pick_id']} under 30 words ({len(words)})")
        if p["prediction"] in seen_prose:
            errors.append(f"Duplicate prose on {p['pick_id']}")
        seen_prose.add(p["prediction"])
        if len(p.get("verified_players") or []) < 2:
            errors.append(f"Pick {p['pick_id']} has fewer than 2 verified players")
        if "Luke Humphries" in p["selection"]:
            errors.append(f"Withdrawn player Luke Humphries selected in {p['pick_id']}")

    # Verify HTML pages, 100% row source links, and 0 broken internal links/fragments
    html_files = sorted(SITE_DIR.rglob("*.html"))
    if len(html_files) != 26:
        errors.append(f"Expected 26 HTML files in beacon/, got {len(html_files)}")

    parsed: dict[Path, PageInspector] = {}
    for hf in html_files:
        ins = PageInspector()
        ins.feed(hf.read_text())
        parsed[hf] = ins
        if ins.tbody_rows_total == 0:
            errors.append(f"Page {hf.relative_to(ROOT)} has 0 tbody rows")
        if ins.tbody_rows_with_ext_link != ins.tbody_rows_total:
            errors.append(
                f"Page {hf.relative_to(ROOT)} missing external source link on "
                f"{ins.tbody_rows_total - ins.tbody_rows_with_ext_link}/{ins.tbody_rows_total} rows"
            )

    internal_checked = 0
    total_tbody_rows = 0
    for hf, ins in parsed.items():
        total_tbody_rows += ins.tbody_rows_total
        for raw in ins.links:
            if raw.startswith(("https://", "http://")):
                for bad in BANNED_HREF_SUBSTRINGS:
                    if bad in raw:
                        errors.append(f"Banned href '{bad}' in {hf.relative_to(ROOT)}: {raw}")
                continue
            if raw.startswith(("mailto:", "javascript:")):
                continue
            u = urlparse(raw)
            target_path = (hf.parent / u.path).resolve() if u.path else hf.resolve()
            internal_checked += 1
            if not target_path.exists():
                errors.append(f"Broken relative link in {hf.relative_to(ROOT)}: {raw} -> {target_path}")
                continue
            if u.fragment and target_path in parsed:
                if u.fragment not in parsed[target_path].ids:
                    errors.append(f"Missing fragment #{u.fragment} in {target_path.relative_to(ROOT)} (from {hf.relative_to(ROOT)})")

    if summary["total_rows"] != len(matches) or summary["high_confidence_picks"] != len(picks) or summary["flagged_total"] != len(flags):
        errors.append("summary.json count mismatch against matches/predictions/flagged")

    return {
        "ok": len(errors) == 0,
        "pages": len(html_files),
        "tbody_rows": total_tbody_rows,
        "internal_links_checked": internal_checked,
        "matches": len(matches),
        "high_picks": len(picks),
        "flagged": len(flags),
        "errors": errors,
    }


def main() -> None:
    res = verify_all()
    if not res["ok"]:
        for e in res["errors"]:
            print("ERROR:", e)
        raise SystemExit(1)
    print(
        f"beacon_verify: OK — {res['pages']} HTML pages, {res['tbody_rows']}/{res['tbody_rows']} source-linked table rows, "
        f"{res['internal_links_checked']} internal links verified (0 broken), "
        f"{res['matches']} matches, {res['high_picks']} strict [-250,-233] high picks, {res['flagged']} flagged items."
    )


if __name__ == "__main__":
    main()
