#!/usr/bin/env python3
"""
Strict line-by-line structural, link, provenance, and mathematical verifier for `/portal/`.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "portal"
PORTAL = ROOT / "portal"

ALLOWED_OFFICIAL_HOSTS = {
    "www.olbg.com",
    "www.atptour.com",
    "wtafiles.wtatennis.com",
    "www.wtatennis.com",
    "www.nba.com",
    "www.euroleaguebasketball.net",
    "www.pgatour.com",
    "www.europeantour.com",
    "www.icc-cricket.com",
    "cricket.co.za",
    "www.wst.tv",
    "stats.unitedrugby.com",
    "top14.lnr.fr",
    "prod2.lnr.fr",
    "www.rlwc2026.com",
    "www.nrl.com",
    "statsapi.mlb.com",
    "www.mlb.com",
    "api-web.nhle.com",
    "api.nhle.com",
    "stats.swehockey.se",
    "liiga.fi",
    "www.formula1.com",
    "www.pdc.tv",
    "ehfcl.eurohandball.com",
    "www.daikin-hbl.de",
    "www.legavolley.it",
    "www.plusliga.pl",
    "www.tauronliga.pl",
    "www.afl.com.au",
    "lolesports.com",
    "www.riotgames.com",
    "munster.gaa.ie",
    "www.gaa.ie",
    "www.gbgb.org.uk",
}

EXCLUDED_SPORT_SLUGS = {
    "soccer",
    "football",
    "american-football",
    "boxing",
    "ufc",
    "mma",
    "ufc-mma",
    "hurling",
    "horse-racing",
    "cycling",
    "specials",
    "politics",
    "entertainment",
}

FORBIDDEN_TEXT_PATTERNS = [
    re.compile(r"\b(?:ufc|mma|boxing|hurling|horse racing|cycling)\b", re.IGNORECASE),
    re.compile(r"\b(?:nfl|ncaa football|premier league|champions league soccer|la liga|serie a football)\b", re.IGNORECASE),
    re.compile(r"liquipedia\.net", re.IGNORECASE),
]


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.in_tbody = False
        self.in_tr = False
        self.tr_https_links: list[str] = []
        self.tbody_row_https_counts: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        if ad.get("id"):
            self.ids.add(ad["id"])
        for attr in ("href", "src"):
            val = ad.get(attr)
            if val:
                self.links.append(val)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.tr_https_links = []
        elif tag == "a" and self.in_tr:
            href = ad.get("href") or ""
            if href.startswith("https://"):
                self.tr_https_links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_tr:
            self.tbody_row_https_counts.append(len(self.tr_https_links))
            self.in_tr = False
        elif tag == "tbody":
            self.in_tbody = False


def verify_all() -> dict:
    sports = json.loads((DATA / "sports.json").read_text())
    matches_doc = json.loads((DATA / "matches.json").read_text())
    preds_doc = json.loads((DATA / "predictions.json").read_text())
    flagged_doc = json.loads((DATA / "flagged.json").read_text())

    eligible_slugs = {s["slug"] for s in sports["eligible_sports"]}
    assert len(eligible_slugs) == 17, f"Expected 17 eligible sports, got {len(eligible_slugs)}"
    assert not (eligible_slugs & EXCLUDED_SPORT_SLUGS), "Excluded sport slug in eligible list"

    matches = matches_doc["matches"]
    preds = preds_doc["predictions"]
    lined = [m for m in matches if m["status"] == "originated"]
    lined_sports = {m["sport"] for m in lined}
    assert lined_sports == eligible_slugs, f"Missing originated sport(s): {eligible_slugs - lined_sports}"

    # Verify every match row has official host URL, zero excluded terms, zero .25/.75 quarter-lines
    for m in matches:
        assert m["sport"] in eligible_slugs, f"Invalid sport {m['sport']}"
        for url_field in ("source_url", "olbg_url"):
            u = m[url_field]
            parsed = urlparse(u)
            assert parsed.scheme == "https" and parsed.netloc in ALLOWED_OFFICIAL_HOSTS, (
                f"Disallowed or non-HTTPS host in {m['id']} {url_field}: {u}"
            )
        blob = f"{m['competition']} {m['home']} {m['away']}"
        for pat in FORBIDDEN_TEXT_PATTERNS:
            assert not pat.search(blob), f"Forbidden excluded-sport/wiki pattern in {m['id']}: {blob}"
        if m["status"] == "originated":
            w = m["markets"]["winner"]
            if w["type"] == "1X2":
                s = w["home"]["prob"] + w["draw"]["prob"] + w["away"]["prob"]
            else:
                s = w["home"]["prob"] + w["away"]["prob"]
            assert abs(s - 1.0) <= 0.0005, f"Probability sum drift on {m['id']}: {s}"
            for mk_key in ("handicap", "total", "alt_in_band"):
                mk = m["markets"].get(mk_key)
                if mk and mk.get("line") is not None:
                    frac = abs(mk["line"]) % 1.0
                    assert abs(frac - 0.5) < 1e-6, f"Non-.5 line on {m['id']} {mk_key}: {mk['line']}"
            assert m["confidence"] in ("high", "medium", "low")
            assert m["in_band_selection"]["quote"]["in_band"], f"In-band selection out of band on {m['id']}"
        else:
            assert m["markets"]["winner"] is None and m["winner_pick"] is None and m["confidence"] is None

    # Verify predictions
    match_by_id = {m["id"]: m for m in matches}
    pred_sports = {p["sport"] for p in preds}
    assert pred_sports == eligible_slugs, f"Featured picks missing sport(s): {eligible_slugs - pred_sports}"
    openings = set()
    for p in preds:
        assert p["confidence"] == "high"
        assert 1.40 <= p["fair_decimal"] <= 101.00, f"Decimal out of band: {p['id']} {p['fair_decimal']}"
        assert -250 <= p["fair_american"] <= 10000, f"American out of band: {p['id']} {p['fair_american']}"
        words = p["prediction"].split()
        assert len(words) >= 30 and len(words) == p["word_count"], f"Word count error on {p['id']}"
        w3 = " ".join(words[:3])
        assert w3 not in openings, f"Duplicate 3-word opening: {w3}"
        openings.add(w3)
        for req in ("team_focus", "named_player", "current_form", "recent_history", "selection"):
            assert p.get(req) and len(str(p[req]).strip()) >= 3, f"Missing {req} on {p['id']}"
        assert p["fair_american_str"] in p["prediction"], f"American price missing from prose on {p['id']}"
        assert f"{p['fair_decimal']:.2f}" in p["prediction"], f"Decimal price missing from prose on {p['id']}"
        m = match_by_id[p["match_id"]]
        assert m["confidence"] == "high"
        parsed = urlparse(p["source_url"])
        assert parsed.scheme == "https" and parsed.netloc in ALLOWED_OFFICIAL_HOSTS

    # Verify all 26 HTML pages, every tbody tr official link, and every internal link + fragment
    html_files = sorted(PORTAL.rglob("*.html"))
    assert len(html_files) == 26, f"Expected 26 HTML pages in /portal/, found {len(html_files)}"

    parsed_pages: dict[Path, PageInspector] = {}
    total_tbody_rows = 0
    for hf in html_files:
        insp = PageInspector()
        insp.feed(hf.read_text())
        parsed_pages[hf.resolve()] = insp
        for idx, cnt in enumerate(insp.tbody_row_https_counts):
            assert cnt >= 1, f"{hf.relative_to(ROOT)} tbody row #{idx + 1} has zero HTTPS official links"
            total_tbody_rows += 1

    internal_checked = 0
    for hf, insp in parsed_pages.items():
        for link in insp.links:
            if link.startswith(("https://", "mailto:")):
                if link.startswith("https://"):
                    host = urlparse(link).netloc
                    assert host in ALLOWED_OFFICIAL_HOSTS, f"Disallowed external host {host} in {hf.name}: {link}"
                continue
            assert not link.startswith("http://"), f"Insecure HTTP link in {hf.name}: {link}"
            if link.startswith("#"):
                frag = link[1:]
                assert frag in insp.ids, f"Missing anchor #{frag} in {hf.relative_to(ROOT)}"
                internal_checked += 1
                continue
            path_part, _, frag = link.partition("#")
            target = (hf.parent / path_part).resolve()
            assert target.exists(), f"Broken relative link in {hf.relative_to(ROOT)}: {link} -> {target}"
            if frag and target in parsed_pages:
                assert frag in parsed_pages[target].ids, f"Missing fragment #{frag} in {target.relative_to(ROOT)}"
            internal_checked += 1

    return {
        "html_pages": len(html_files),
        "tbody_rows_with_https_official_link": total_tbody_rows,
        "internal_links_and_fragments_verified": internal_checked,
        "eligible_sports_lined": len(lined_sports),
        "originated_matches": len(lined),
        "unlined_blank_rows": len(matches) - len(lined),
        "featured_in_band_predictions": len(preds),
        "flagged_items": len(flagged_doc["items"]),
    }


def main() -> None:
    res = verify_all()
    print("portal_verify.py OK:", json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
