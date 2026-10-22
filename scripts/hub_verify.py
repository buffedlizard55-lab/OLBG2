#!/usr/bin/env python3
"""Comprehensive structural, mathematical, content, and link audit for /hub/ (arena/42c8f6be-olbg2)."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
HUB_DATA = ROOT / "data" / "hub"
HUB_DIR = ROOT / "hub"

FORBIDDEN_SLUGS = {
    "soccer", "football", "boxing", "ufc", "mma",
    "american-football", "hurling", "horse-racing", "cycling", "specials",
}


class HubHTMLInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.assets: list[str] = []
        self.in_tbody = False
        self.in_tr = False
        self.current_tr_https_links: list[str] = []
        self.tbody_row_https_counts: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        if ad.get("id"):
            self.ids.add(ad["id"])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.current_tr_https_links = []
        elif tag == "a" and ad.get("href"):
            href = ad["href"]
            self.links.append(href)
            if self.in_tr and href.startswith("https://"):
                self.current_tr_https_links.append(href)
        elif tag in ("link", "script", "img") and (ad.get("href") or ad.get("src")):
            ref = ad.get("href") or ad.get("src")
            if ref:
                self.assets.append(ref)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_tr:
            self.tbody_row_https_counts.append(len(self.current_tr_https_links))
            self.in_tr = False
        elif tag == "tbody":
            self.in_tbody = False


def verify_all() -> dict:
    json_names = ["sports.json", "inputs.json", "flagged.json", "sources.json", "repo_audit.json", "matches.json", "predictions.json"]
    loaded = {}
    for nm in json_names:
        p = HUB_DATA / nm
        assert p.is_file() and p.stat().st_size > 20, f"Missing or empty JSON file: {p}"
        loaded[nm] = json.loads(p.read_text(encoding="utf-8"))

    sports = loaded["sports.json"]
    matches = loaded["matches.json"]["rows"]
    preds = loaded["predictions.json"]["predictions"]

    assert len(sports["eligible"]) == 17
    assert len(sports["excluded"]) == 10
    by_slug = {s["slug"]: s for s in sports["eligible"]}
    assert by_slug["basketball"]["olbg_sport_id"] == 4
    assert by_slug["golf"]["olbg_sport_id"] == 5

    # Check zero excluded sports anywhere in matches or predictions
    for r in matches:
        assert r["sport"] in by_slug, f"Unknown sport {r['sport']}"
        assert r["sport"] not in FORBIDDEN_SLUGS, f"Forbidden sport leaked: {r['sport']}"
        assert r["official_url"].startswith("https://"), f"Missing HTTPS official_url on {r['id']}"
        assert r["olbg_url"].startswith("https://www.olbg.com/"), f"Invalid OLBG URL on {r['id']}"

    orig = [r for r in matches if r["status"] == "originated"]
    unl = [r for r in matches if r["status"] == "unlined"]
    assert len(orig) == 159
    assert len(unl) == 30

    # Fair odds & probability invariants
    for r in orig:
        for mname, mobj in r["markets"].items():
            if mobj is None:
                continue
            probs = [o["prob"] for o in mobj["outcomes"]]
            assert abs(sum(probs) - 1.0) <= 0.005, f"Overround error on {r['id']}.{mname}: sum={sum(probs)}"
            for o in mobj["outcomes"]:
                dec = o["fair_decimal"]
                am = o["fair_american"]
                if dec >= 2.0:
                    exp_am = int(round((dec - 1.0) * 100.0))
                else:
                    exp_am = -int(round(100.0 / (dec - 1.0)))
                assert am == exp_am, f"Decimal/American mismatch on {r['id']}: dec={dec} am={am} exp={exp_am}"
        if r["sport"] == "basketball" and r["id"].startswith("nba-"):
            assert r["markets"]["total"] is None, f"NBA total should be None on {r['id']}"
        if r["sport"] == "volleyball":
            assert r["pick"]["confidence"] == "low", f"SuperLega GP=1 row {r['id']} must be low confidence"
        if r["pick"]["fair_decimal"] < 1.40:
            assert r["pick"]["confidence"] != "high", f"Short chalk {r['id']} must not be high confidence"

    for r in unl:
        assert r["markets"] == {"winner": None, "handicap": None, "total": None}
        assert r["pick"] is None

    high_ids = [r["id"] for r in orig if r["pick"]["confidence"] == "high"]
    pred_ids = [p["match_id"] for p in preds]
    assert high_ids == pred_ids, f"High-confidence mismatch: {high_ids} vs {pred_ids}"
    assert len(preds) == 25
    assert len({p["sport"] for p in preds}) >= 8

    for p in preds:
        dec, am = p["fair_decimal"], p["fair_american"]
        assert 1.40 <= dec <= 101.00, f"Out-of-band decimal {dec} on {p['match_id']}"
        assert (-250 <= am <= -100) or (100 <= am <= 10000), f"Out-of-band American {am} on {p['match_id']}"
        assert len(p["text"].split()) >= 30, f"Short prediction on {p['match_id']}"
        assert len(p["facts"]) >= 2

    # Inspect all 22 HTML files under hub/
    html_files = sorted(list(HUB_DIR.glob("*.html")) + list((HUB_DIR / "sports").glob("*.html")))
    assert len(html_files) == 22, f"Expected 22 HTML files under hub/, found {len(html_files)}"

    parsed_map: dict[Path, HubHTMLInspector] = {}
    for hf in html_files:
        ins = HubHTMLInspector()
        ins.feed(hf.read_text(encoding="utf-8"))
        parsed_map[hf.resolve()] = ins
        assert len(ins.tbody_row_https_counts) >= 1, f"Page {hf} has zero table rows"
        for idx, cnt in enumerate(ins.tbody_row_https_counts):
            assert cnt >= 1, f"Table row #{idx} in {hf} is missing an https:// official source link"

    checked_internal = 0
    total_rows_checked = 0
    for hf, ins in parsed_map.items():
        total_rows_checked += len(ins.tbody_row_https_counts)
        for ref in ins.assets + ins.links:
            if ref.startswith(("https://", "http://", "mailto:")):
                continue
            parsed = urlparse(ref)
            target = (hf.parent / parsed.path).resolve() if parsed.path else hf
            assert target.is_file(), f"Broken relative target '{ref}' in {hf} -> {target}"
            if parsed.fragment:
                if target in parsed_map:
                    target_ids = parsed_map[target].ids
                else:
                    ext_ins = HubHTMLInspector()
                    ext_ins.feed(target.read_text(encoding="utf-8"))
                    target_ids = ext_ins.ids
                assert parsed.fragment in target_ids, f"Broken fragment '#{parsed.fragment}' in {hf} -> {target}"
            checked_internal += 1

    summary = {
        "html_pages": len(html_files),
        "table_rows_verified_with_https_source": total_rows_checked,
        "internal_links_and_fragments_verified": checked_internal,
        "originated_rows": len(orig),
        "unlined_rows": len(unl),
        "high_confidence_predictions": len(preds),
    }
    print(f"hub_verify.py OK: {summary}")
    return summary


if __name__ == "__main__":
    verify_all()
