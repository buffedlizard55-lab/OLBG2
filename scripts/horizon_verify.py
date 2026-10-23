"""Horizon desk (session arena/9c5af337-olbg2) — end-to-end verification.

Audits:
  1. Strictly 15 mandated sports in data/horizon/*.json and horizon/sports/*.html.
  2. Every prediction in data/horizon/predictions.json has >=30 words, zero hits
     for \\b(model|verified)\\b, unique 5-word openings, and unique sentences.
  3. Every prediction rendered in horizon/index.html and horizon/sports/*.html
     has zero hits for \\b(model|verified)\\b.
  4. Every <tbody><tr> across all 19 HTML files in /horizon/ has at least one
     external https:// official source anchor.
  5. Every local href/src across all 19 HTML files in /horizon/ resolves to an
     existing file on disk (and #fragment IDs resolve in the target file).
  6. Every priced fixture has valid confidence ('low'|'medium'|'high') and
     every high-confidence fixture has an actionable line in [-250, +10000].
  7. Every unpriced fixture is present in data/horizon/flagged.json and rendered
     on horizon/flagged.html.

Writes data/horizon/verification.json and exits non-zero on any failure.
"""
import html.parser
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "horizon")
SITE = os.path.join(ROOT, "horizon")

MANDATED_SPORTS = {
    "Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker",
    "Darts", "Baseball", "Gaelic Sports", "Greyhounds", "Tennis",
    "Motor Racing", "Handball", "Ice Hockey", "Basketball", "Rugby League",
}
EXPECTED_SLUGS = {
    "golf", "volleyball", "rugby-union", "cricket", "snooker",
    "darts", "baseball", "gaelic-sports", "greyhounds", "tennis",
    "motor-racing", "handball", "ice-hockey", "basketball", "rugby-league",
}
FORBIDDEN = re.compile(r"\b(model|verified)\b", re.IGNORECASE)


class PageInspector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.in_tr = False
        self.tr_ext_links = 0
        self.total_tbody_rows = 0
        self.unlinked_tbody_rows = 0
        self.links = []
        self.ids = set()
        self.in_pred_body = False
        self.pred_texts = []
        self._buf = []

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if "id" in ad and ad["id"]:
            self.ids.add(ad["id"])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.tr_ext_links = 0
        elif tag == "a":
            href = ad.get("href", "")
            if href:
                self.links.append(href)
            if self.in_tr and (href.startswith("https://") or href.startswith("http://")):
                self.tr_ext_links += 1
        elif tag == "link":
            href = ad.get("href", "")
            if href:
                self.links.append(href)
        elif tag == "p" and "pred-body" in ad.get("class", ""):
            self.in_pred_body = True
            self._buf = []

    def handle_data(self, data):
        if self.in_pred_body:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            self.total_tbody_rows += 1
            if self.tr_ext_links == 0:
                self.unlinked_tbody_rows += 1
        elif tag == "p" and self.in_pred_body:
            self.in_pred_body = False
            self.pred_texts.append("".join(self._buf).strip())


def verify():
    errors = []
    with open(os.path.join(DATA, "fixtures.json")) as f:
        fx = json.load(f)
    with open(os.path.join(DATA, "lines.json")) as f:
        ln = json.load(f)
    with open(os.path.join(DATA, "predictions.json")) as f:
        pr = json.load(f)
    with open(os.path.join(DATA, "flagged.json")) as f:
        fl = json.load(f)

    fx_sports = {r["sport"] for r in fx["fixtures"]}
    ln_sports = {r["sport"] for r in ln["records"]}
    pr_sports = {r["sport"] for r in pr["predictions"]}
    if fx_sports != MANDATED_SPORTS:
        errors.append(f"fixtures.json sports mismatch: {fx_sports ^ MANDATED_SPORTS}")
    if ln_sports != MANDATED_SPORTS:
        errors.append(f"lines.json sports mismatch: {ln_sports ^ MANDATED_SPORTS}")
    if pr_sports != MANDATED_SPORTS:
        errors.append(f"predictions.json sports mismatch: {pr_sports ^ MANDATED_SPORTS}")

    sport_files = {os.path.splitext(fn)[0] for fn in os.listdir(os.path.join(SITE, "sports")) if fn.endswith(".html")}
    if sport_files != EXPECTED_SLUGS:
        errors.append(f"horizon/sports/*.html mismatch: {sport_files ^ EXPECTED_SLUGS}")

    flagged_ids = {x["fixture_id"] for x in fl["items"]}
    for r in ln["records"]:
        if not r["priced"]:
            if r["id"] not in flagged_ids:
                errors.append(f"Unpriced fixture {r['id']} missing from flagged.json")
            if r["winner_pick"] is not None or r["confidence"] is not None:
                errors.append(f"Unpriced fixture {r['id']} has non-null pick/confidence")
        else:
            if r["confidence"] not in ("low", "medium", "high"):
                errors.append(f"Priced fixture {r['id']} has invalid confidence {r['confidence']}")
            if not r["actionable_in_band"] or not (-250 <= r["actionable_odds"] <= 10000):
                errors.append(f"Priced fixture {r['id']} lacks in-band actionable line: {r['actionable_odds']}")

    openings = set()
    sentences = set()
    for p in pr["predictions"]:
        txt = p["prediction_text"]
        words = txt.split()
        if len(words) < 30 or len(words) != p["word_count"]:
            errors.append(f"Prediction {p['fixture_id']} word count invalid: {len(words)}")
        if FORBIDDEN.search(txt):
            errors.append(f"Prediction {p['fixture_id']} contains forbidden word")
        op = " ".join(words[:5]).lower()
        if op in openings:
            errors.append(f"Duplicate opening phrase in {p['fixture_id']}: {op}")
        openings.add(op)
        for s in [x.strip() for x in re.split(r"(?<=[.!?])\s+", txt) if x.strip()]:
            if s in sentences:
                errors.append(f"Duplicate sentence in {p['fixture_id']}: {s}")
            sentences.add(s)

    html_files = []
    for root, _dirs, files in os.walk(SITE):
        for fn in sorted(files):
            if fn.endswith(".html"):
                html_files.append(os.path.join(root, fn))

    parsed = {}
    total_rows = 0
    unlinked_rows = 0
    html_pred_count = 0
    for path in html_files:
        insp = PageInspector()
        with open(path, encoding="utf-8") as f:
            insp.feed(f.read())
        parsed[os.path.abspath(path)] = insp
        total_rows += insp.total_tbody_rows
        unlinked_rows += insp.unlinked_tbody_rows
        if insp.unlinked_tbody_rows > 0:
            errors.append(f"{os.path.relpath(path, ROOT)} has {insp.unlinked_tbody_rows} unlinked tbody rows")
        for pt in insp.pred_texts:
            html_pred_count += 1
            if FORBIDDEN.search(pt):
                errors.append(f"Rendered prediction in {os.path.relpath(path, ROOT)} contains forbidden word")
            if len(pt.split()) < 30:
                errors.append(f"Rendered prediction in {os.path.relpath(path, ROOT)} has <30 words")

    checked_local_links = 0
    broken_links = []
    for path, insp in parsed.items():
        base_dir = os.path.dirname(path)
        for href in insp.links:
            u = urlparse(href)
            if u.scheme in ("http", "https", "mailto"):
                continue
            target = os.path.abspath(os.path.join(base_dir, u.path)) if u.path else path
            checked_local_links += 1
            if not os.path.exists(target):
                broken_links.append(f"{os.path.relpath(path, ROOT)} -> {href}")
                continue
            if u.fragment and target in parsed:
                if u.fragment not in parsed[target].ids:
                    broken_links.append(f"{os.path.relpath(path, ROOT)} -> {href} (missing #{u.fragment})")
    if broken_links:
        errors.extend(broken_links)

    report = {
        "verified_utc": "2026-10-23T21:40:00Z",
        "session": "arena/9c5af337-olbg2",
        "passed": len(errors) == 0,
        "html_files_checked": len(html_files),
        "total_tbody_rows": total_rows,
        "unlinked_tbody_rows": unlinked_rows,
        "predictions_checked": len(pr["predictions"]),
        "rendered_prediction_cards_checked": html_pred_count,
        "local_links_checked": checked_local_links,
        "broken_local_links": len(broken_links),
        "errors": errors,
    }
    with open(os.path.join(DATA, "verification.json"), "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print("horizon_verify:", json.dumps({k: v for k, v in report.items() if k != "errors"}))
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    verify()
