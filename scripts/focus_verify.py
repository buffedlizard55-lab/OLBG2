"""Verify /focus/: prices recompute, predictions >=30w & banned words absent,
every match row has https official source, internal links resolve, KPIs match data."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"data"/"focus"; OUT = ROOT/"focus"
ok = True
def chk(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: ok = False

M = json.loads((DATA/"matches.json").read_text())["matches"]
PRED = json.loads((DATA/"predictions.json").read_text())["predictions"]
FLAGS = json.loads((DATA/"flagged.json").read_text())["flags"]
for m in M:
    chk(m["source_url"].startswith("https://"), f"{m['id']} official https source")
    for p in m["prices"]:
        dec = max(round(1/p["p"]+1e-12,2),1.01)
        chk(abs(dec-p["decimal"])<0.011, f"{m['id']} {p['selection']} price recomputes")
        if p.get("in_band"): chk(0.70 <= p["p"] <= 5/7+1e-9 and -250 <= p["american"] <= 10000, f"{m['id']} in-band gate")
for p in PRED:
    chk(p["words"]>=30 and len(p["text"].split())>=30, f"{p['fixture']} prediction >=30 words")
    chk("model" not in p["text"].lower() and "verified" not in p["text"].lower(), f"{p['fixture']} banned words absent")
    chk(p["confidence"]=="high" and 0.70 <= p["p"] <= 5/7+1e-9, f"{p['fixture']} high gate")
chk(len(set(p["text"] for p in PRED))==len(PRED), "predictions unique")
sports = json.loads((DATA/"inputs.json").read_text())["sports"]
chk(len(sports)==15, "exactly 15 sports in scope")
for s in sports: chk((OUT/"sports"/f"{s}.html").exists(), f"sport page {s}")
# internal links
link_re = re.compile(r'href="([^"#]+)(?:#[^"]*)?"')
for f in OUT.rglob("*.html"):
    for h in link_re.findall(f.read_text()):
        if h.startswith(("http://","https://","mailto:","data:")): continue
        chk((f.parent/h).resolve().exists() or (f.parent/h/"index.html").exists() if False else (f.parent/h).exists(), f"{f.relative_to(OUT)} -> {h}")
idx = (OUT/"index.html").read_text()
chk(f'<div class="v">{len(M)}</div>' in idx, "index KPI fixtures matches data")
chk("Flagged for Review" in idx, "index links flagged")
print("ALL CHECKS PASS" if ok else "FAILURES PRESENT")
sys.exit(0 if ok else 1)
