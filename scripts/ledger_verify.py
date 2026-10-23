#!/usr/bin/env python3
"""Self-audit for the /ledger/ desk. Exits non-zero on any problem."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L = json.loads((ROOT / "data/ledger/lines.json").read_text())
P = json.loads((ROOT / "data/ledger/predictions.json").read_text())["predictions"]
F = json.loads((ROOT / "data/ledger/flagged.json").read_text())["flags"]
SRC = {s["key"]: s for s in json.loads((ROOT / "data/ledger/sources.json").read_text())["sources"]}
MATCH = {m["id"]: m for m in L["matches"]}
SPORTS15 = {"Golf","Volleyball","Rugby Union","Cricket","Snooker","Darts","Baseball","Gaelic Sports",
            "Greyhounds","Tennis","Motor Racing","Handball","Ice Hockey","Basketball","Rugby League"}
errors, checks = [], 0
def ck(cond, msg):
    global checks; checks += 1
    if not cond: errors.append(msg)

for m in L["matches"]:
    ck(m["sport"] in SPORTS15, f"{m['id']} sport outside the 15: {m['sport']}")
    ck(bool(m["source_keys"]), f"{m['id']} has no source keys")
    for k in m["source_keys"]:
        ck(k in SRC, f"{m['id']} unknown source key {k}")
        ck(SRC[k]["url"].startswith("http"), f"{k} bad url")
    if not m["priced"]:
        ck(bool(m.get("blank_reason")), f"{m['id']} unpriced without a reason")
for s in L["selections"]:
    ck(s["fixture"] in MATCH, f"orphan selection {s}")
    ck(0 < s["prob"] < 1, f"bad prob {s}")
    expect_band = -250 <= s["american"] <= 10000
    ck(s["in_band"] == expect_band, f"band mismatch {s}")
    if s["tier"] == "A": ck(0.70 <= s["prob"] <= 0.7143 + 1e-9 and s["in_band"], f"Tier A outside window {s}")
    if s["prob"] >= 0.70 and s["in_band"]: ck(s["tier"] == "A", f"should be Tier A {s}")
    if s["confidence"] == "High": ck(s["prob"] >= 0.70, f"High below 70% {s}")
# winner pairs sum to ~1
from collections import defaultdict
g = defaultdict(list)
for s in L["selections"]:
    if "winner" in s["market"].lower() and "Outright" not in s["market"] and "Race winner" not in s["market"]:
        g[(s["fixture"], s["market"])].append(s["prob"])
for k, v in g.items():
    ck(abs(sum(v) - 1) < 0.002, f"winner probs {k} sum {sum(v)}")
texts = set()
for p in P:
    ck(p["words"] >= 30, f"preview short {p['fixture']}")
    low = p["text"].lower()
    ck("model" not in low and "verif" not in low, f"banned word in preview {p['fixture']}")
    ck(p["text"] not in texts, f"duplicate preview {p['fixture']}"); texts.add(p["text"])
    ck(p["selection"].split("(")[0].strip().lower().split()[-1] in low or p["selection"].lower() in low,
       f"selection not named in preview {p['fixture']}")
    row = [s for s in L["selections"] if s["fixture"] == p["fixture"] and s["selection"] == p["selection"] and s["market"] == p["market"]]
    ck(len(row) == 1 and row[0]["american"] == p["american"], f"preview price mismatch {p['fixture']}")
for f in F:
    for k in f["source_keys"]: ck(k in SRC, f"flag {f['id']} bad source {k}")
# built pages + internal links
built = list((ROOT / "ledger").rglob("*.html"))
ck(len(built) >= 25, f"only {len(built)} pages built")
for html in built:
    txt = html.read_text()
    ck("<table" in txt or "sportgrid" in txt or "preview" in txt, f"{html} has no table/grid/cards")
    for href in re.findall(r'href="([^"]+)"|href=\'([^\']+)\'', txt):
        h = href[0] or href[1]
        if h.startswith(("http", "#", "mailto:")): continue
        target = (html.parent / h.split("#")[0]).resolve()
        ck(target.exists(), f"{html.relative_to(ROOT)} broken link -> {h}")
print(f"ledger_verify: {checks} checks, {len(errors)} errors")
for e in errors[:40]: print(" -", e)
sys.exit(1 if errors else 0)
