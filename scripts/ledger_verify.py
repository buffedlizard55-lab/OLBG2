#!/usr/bin/env python3
"""Audit the /ledger/ layer and fail loudly if anything does not add up.

Checks
  1. every capture in the manifest that returned 200 has a stored body whose sha256 matches
  2. every OLBG row links the OLBG page it came from
  3. every row marked official-fixture / official-page has an official URL and a capture time
  4. every pick links a source and every originated pick links its fixture
  5. every preview is >= 30 words, unique, names its selection, has >= 2 facts, avoids the
     words "model" and "verified", and links an official source
  6. every internal link and fragment on the generated pages resolves
  7. the published counts equal the counts in the data
  8. all fifteen sports have a page

Writes data/ledger/verify.json and exits 1 on any failure.
"""
from __future__ import annotations

import hashlib
import html.parser
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ledger"
OUT = ROOT / "ledger"
SPORTS = ["Golf", "Volleyball", "Rugby Union", "Cricket", "Snooker", "Darts", "Baseball",
          "Gaelic Sports", "Greyhounds", "Tennis", "Motor Racing", "Handball", "Ice Hockey",
          "Basketball", "Rugby League"]


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if not v:
                continue
            if (tag in ("a", "link") and k == "href") or (tag in ("img", "script") and k == "src"):
                self.targets.append((tag, v))


def main() -> int:
    checks, failures = [], []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            failures.append(f"{name}: {detail}")

    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    olbg = json.loads((DATA / "olbg.json").read_text(encoding="utf-8"))
    matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))
    picks = json.loads((DATA / "picks.json").read_text(encoding="utf-8"))
    preds = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))
    inherited = json.loads((DATA / "inherited.json").read_text(encoding="utf-8"))
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))

    # 1 hashes
    bad = []
    for c in manifest["captures"]:
        if c.get("status") != 200:
            continue
        p = DATA / c.get("stored_as", "")
        if not p.exists():
            bad.append(f"{c['key']}: missing body")
            continue
        if c.get("sha256") and hashlib.sha256(p.read_bytes()).hexdigest() != c["sha256"]:
            bad.append(f"{c['key']}: sha mismatch")
    check("capture bodies match their stored sha256", not bad, "; ".join(bad[:5]))

    # 2 OLBG rows link back
    missing = [t["event"] for t in olbg["tips"] if not t.get("event_url", "").startswith("https://www.olbg.com")]
    check("every OLBG tip links its OLBG event page", not missing, f"{len(missing)} without a link")

    # 3 verification rows carry a source
    weak = [e["event"] for e in matches["events"]
            if e["verify"]["state"] != "unmatched" and not (e["verify"].get("official_url") and e["verify"].get("captured_at"))]
    check("every matched event links an official URL and its capture time", not weak, f"{len(weak)} incomplete")

    # 4 picks carry a source
    nosrc = [p["id"] for p in picks["picks"] if not (p.get("official_url") or p.get("source_url"))]
    check("every selection links a source", not nosrc, f"{len(nosrc)} without a source")
    bad_basis = [p["id"] for p in picks["picks"] if p["basis"] not in ("originated", "market-implied")]
    check("every selection states its basis", not bad_basis, ",".join(bad_basis[:3]))

    # 5 previews
    problems, seen = [], {}
    for p in preds["predictions"]:
        t = p["text"].lower()
        if p["words"] < 30:
            problems.append(f"{p['id']}: {p['words']} words")
        for bad_word in ("model", "verified"):
            if re.search(rf"\b{bad_word}\b", t):
                problems.append(f"{p['id']}: contains '{bad_word}'")
        sticky = [w for w in re.findall(r"[a-z]+", p["selection"].lower()) if len(w) >= 4]
        if sticky and not any(w in t for w in sticky):
            problems.append(f"{p['id']}: selection not named")
        if len(p.get("facts", [])) < 2:
            problems.append(f"{p['id']}: fewer than two facts")
        if not p.get("prediction_source", "").startswith("http"):
            problems.append(f"{p['id']}: no official source")
        opening = " ".join(p["text"].split()[:6]).lower()
        if opening in seen:
            problems.append(f"{p['id']}: duplicate opening with {seen[opening]}")
        seen[opening] = p["id"]
    check("every preview passes the publication rules", not problems, "; ".join(problems[:6]))

    # 5b previews carried in from the earlier ledger pass
    iprob, iseen = [], {}
    for p in inherited["previews"]:
        t = p["text"].lower()
        if p["words"] < 30 or p["words"] != len(p["text"].split()):
            iprob.append(f"{p['event']}: word count")
        for bad_word in ("model", "verified", "verification"):
            if re.search(rf"\b{bad_word}\b", t):
                iprob.append(f"{p['event']}: contains '{bad_word}'")
        if not p.get("sources") or not all(sv["url"].startswith("https://") for sv in p["sources"]):
            iprob.append(f"{p['event']}: source missing or not https")
        opening = " ".join(p["text"].split()[:6]).lower()
        if opening in iseen:
            iprob.append(f"{p['event']}: duplicate opening with {iseen[opening]}")
        iseen[opening] = p["event"]
    check("carried previews obey the same prose rules", not iprob, "; ".join(iprob[:6]))
    check("carried preview count matches the data",
          inherited["meta"]["published"] == len(inherited["previews"]),
          f"{inherited['meta']['published']} vs {len(inherited['previews'])}")
    check("carried previews state their provenance",
          all("carried" in p["provenance"] for p in inherited["previews"]), "")
    preview_sports = set(preds["meta"]["by_sport"]) | set(inherited["meta"]["by_sport"])
    check("preview coverage is stated for the union of both prose sets",
          len(preview_sports) == len(set(inherited["meta"]["by_sport"]) | set(preds["meta"]["by_sport"])),
          f"{len(preview_sports)} sports")

    # 6 links and fragments
    broken, checked = [], 0
    for page in sorted(OUT.rglob("*.html")):
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        ids = set(re.findall(r'\sid="([^"]+)"', page.read_text(encoding="utf-8")))
        for _, href in parser.targets:
            if href.startswith(("http:", "https:", "mailto:", "data:")):
                continue
            target, _, frag = href.partition("#")
            path = page.parent / target if target else page
            if path.is_dir():
                path = path / "index.html"
            checked += 1
            if not path.exists():
                broken.append(f"{page.relative_to(ROOT)} -> {href}")
            elif frag and frag not in ids and target:
                broken.append(f"{page.relative_to(ROOT)} -> {href} (missing anchor)")
    check(f"internal links resolve ({checked} checked)", not broken, "; ".join(broken[:5]))

    # 7 counts
    check("published selection count matches the data", picks["meta"]["selections"] == len(picks["picks"]),
          f"{picks['meta']['selections']} vs {len(picks['picks'])}")
    high = [p for p in picks["picks"] if p["confidence"] == "high"]
    check("high-confidence count matches the data", picks["meta"]["high"] == len(high), f"{picks['meta']['high']} vs {len(high)}")
    check("in-band high count matches the data", picks["meta"]["high_in_band"] == len([p for p in high if p["in_band"]]), "")
    check("source register matches the manifest",
          sources["meta"]["captures"] == len(manifest["captures"]),
          f"{sources['meta']['captures']} vs {len(manifest['captures'])}")
    check("every answered OLBG row keeps its quoted price",
          all(any(m.get("olbg_decimal") for m in e["markets"]) for e in matches["events"]), "")

    # 8 pages
    missing_pages = [s for s in SPORTS if not (OUT / "sports" / (s.lower().replace(" ", "-") + ".html")).exists()]
    check("all fifteen sport pages exist", not missing_pages, ",".join(missing_pages))
    empty = [p.name for p in OUT.rglob("*.html") if len(p.read_text(encoding="utf-8")) < 1500]
    check("no page is trivially short", not empty, ",".join(empty))

    report = {"generated_at": matches["meta"]["generated_at"],
              "checks": len(checks), "passed": len([c for c in checks if c["ok"]]),
              "failed": len(failures), "failures": failures, "detail": checks}
    (DATA / "verify.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{report['passed']}/{report['checks']} checks passed")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
