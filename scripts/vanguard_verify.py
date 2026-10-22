"""Structural verifier for /vanguard/: band arithmetic, sources, prose, links."""
import json, re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "vanguard"
M = json.loads((D / "matches.json").read_text())
L = json.loads((D / "lines.json").read_text())
P = json.loads((D / "predictions.json").read_text())
F = json.loads((D / "flagged.json").read_text())
errors = []

for m in M["matches"]:
    if not m["source_url"].startswith("https://"):
        errors.append(f'{m["id"]}: missing https source')
for x in L["rows"]:
    p = x["p"]
    if abs(x["decimal"] - round(1 / p, 2)) > 0.011:
        errors.append(f'{x["fixture"]} {x["selection"]}: decimal {x["decimal"]} != 1/{p}')
    if x.get("in_band") and not (0.7000 <= p <= 5 / 7 + 1e-12 and -250 <= x["american"] <= 10000):
        errors.append(f'{x["fixture"]} {x["selection"]}: in-band breach')
    if x["market"] != "match winner" and abs(p - 0.5) < 0.02:
        pass
for pr in P["predictions"]:
    if pr["words"] < 30:
        errors.append(f'{pr["id"]}: only {pr["words"]} words')
    if len(pr["text"].split()) < 30:
        errors.append(f'{pr["id"]}: short text')
    if not any(n.lower() in pr["text"].lower() for n in [pr["selection"].split()[0]]):
        errors.append(f'{pr["id"]}: selection not named')
    if pr["american"] < -250 or pr["american"] > 10000:
        errors.append(f'{pr["id"]}: price outside band')
openers = [p["text"].split(".")[0][:40] for p in P["predictions"]]
if len(openers) != len(set(openers)):
    errors.append("duplicate prediction openings")

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.t = []
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if v and ((tag in ("a", "link") and k == "href") or (tag == "img" and k == "src")):
                self.t.append(v)

pages = sorted((ROOT / "vanguard").rglob("*.html"))
for page in pages:
    lk = Links(); lk.feed(page.read_text())
    for href in lk.t:
        u = urlsplit(href)
        if u.scheme or u.netloc or not u.path:
            continue
        t = (page.parent / unquote(u.path)).resolve()
        if t.is_dir(): t /= "index.html"
        if not t.is_file():
            errors.append(f'{page.relative_to(ROOT)}: broken link {href}')

print(f"pages={len(pages)} fixtures={len(M['matches'])} prices={len(L['rows'])} predictions={len(P['predictions'])} flags={F['count']}")
for e in errors[:25]:
    print("FAIL", e)
print("ALL CHECKS PASS" if not errors else f"{len(errors)} FAILURES")
raise SystemExit(bool(errors))
