#!/usr/bin/env python3
"""Daily Top-5 desk structural verifier. Fails (exit 1) on any violation."""
import json, os, re, sys, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "daily"); SITE = os.path.join(ROOT, "daily")
def load(n):
    with open(os.path.join(D, n)) as f: return json.load(f)
errs = []
FX = load("fixtures.json")["fixtures"]; LINES = load("lines.json")["rows"]
TOP5 = load("top5.json")["top5"]; PREDS = load("predictions.json")["predictions"]
SPORTS = load("sports.json")["sports"]; FLAGS = load("flagged.json")["flags"]
fx_ids = {f["id"] for f in FX}
EXCLUDED = {"soccer", "football", "boxing", "ufc", "mma", "american-football", "hurling", "horse-racing", "cycling", "specials"}
for f in FX:
    if f["sport"] in EXCLUDED: errs.append(f"excluded sport leaked: {f['id']}")
    if not f["official_url"].startswith("https://"): errs.append(f"no official https URL: {f['id']}")
    if not ("2026-10-23" <= f["date"] <= "2026-10-30"): errs.append(f"outside window: {f['id']} {f['date']}")
L = {r["match_id"]: r for r in LINES}
for mid, r in L.items():
    if mid not in fx_ids: errs.append(f"line for unknown fixture {mid}")
    if not r.get("originated"): continue
    for m in r["markets"]:
        for o in m["outcomes"]:
            dec = round(1 / min(max(o["p"], 0.01), 0.99), 2)
            if abs(dec - o["fair_decimal"]) > 0.011: errs.append(f"price mismatch {mid} {o['name']}")
            if o["confidence"] == "high" and not (o["p"] >= 0.70 and -250 <= o["fair_american"] <= 10000):
                errs.append(f"high outside band {mid} {o['name']} p={o['p']} am={o['fair_american']}")
for sp, cand in TOP5.items():
    if len(cand) > 5: errs.append(f"{sp} has >5 top picks")
    ps = [p["p"] for p in cand]
    if ps != sorted(ps, reverse=True): errs.append(f"{sp} top5 not ranked desc")
    for p in cand:
        if p["match_id"] not in fx_ids: errs.append(f"top5 unknown {p['match_id']}")
# predictions: every top5 + every high covered; >=30 words; unique; low pairwise similarity
need = {p["match_id"] for v in TOP5.values() for p in v} | {r["match_id"] for r in LINES if r.get("primary_pick") and r["primary_pick"]["confidence"] == "high"}
have = {p["match_id"] for p in PREDS}
if need - have: errs.append(f"missing predictions: {sorted(need-have)}")
texts = [p["text"] for p in PREDS]
if len(set(texts)) != len(texts): errs.append("duplicate prediction texts")
for p in PREDS:
    if p["word_count"] < 30 or len(p["text"].split()) < 30: errs.append(f"short prediction {p['match_id']}")
    if p["selection"].split(" in ")[0] not in p["text"].split(".")[0] and p["selection"] not in p["text"]:
        errs.append(f"selection not obvious in text {p['match_id']}")
    if not p["official_url"].startswith("https://"): errs.append(f"prediction lacks official URL {p['match_id']}")
toks = [set(re.findall(r"[a-z0-9%]+", t.lower())) for t in texts]
for i in range(len(toks)):
    for j in range(i + 1, len(toks)):
        jac = len(toks[i] & toks[j]) / max(len(toks[i] | toks[j]), 1)
        if jac > 0.88: errs.append(f"near-duplicate predictions {PREDS[i]['match_id']} vs {PREDS[j]['match_id']} j={jac:.2f}")
# every sport has a page; every page internally linked exists
pages = []
for dp, _, fns in os.walk(SITE):
    for fn in fns:
        if fn.endswith(".html"): pages.append(os.path.join(dp, fn))
for s in SPORTS:
    if not os.path.exists(os.path.join(SITE, "sports", s["slug"] + ".html")): errs.append(f"missing sport page {s['slug']}")
for pg in pages:
    html = open(pg).read()
    for href in re.findall(r'href="([^"#]+?\.html)(#[^"]*)?"', html):
        h = href[0]
        if h.startswith("http"): continue
        target = os.path.normpath(os.path.join(os.path.dirname(pg), h))
        if not os.path.exists(target): errs.append(f"broken link {pg} -> {h}")
    if 'class="badge high"' in html and "predictions.html" in pg: pass
# flagged covers every zero-row / short sport
short = {sp for sp in TOP5 if len(TOP5[sp]) < 5}
flagged_sports = {f["sport"] for f in FLAGS}
for sp in short:
    if sp not in flagged_sports: errs.append(f"sport {sp} short of 5 but not flagged")
for f in FLAGS:
    if not f["official_url"].startswith("https://"): errs.append(f"flag lacks official URL {f['id']}")
print(f"fixtures={len(FX)} lines={len(LINES)} top5_total={sum(len(v) for v in TOP5.values())} preds={len(PREDS)} flags={len(FLAGS)} pages={len(pages)}")
if errs:
    print("FAIL"); [print(" -", e) for e in errs[:40]]; sys.exit(1)
print("daily_verify OK")
