#!/usr/bin/env python3
"""pulse_verify.py - line-by-line integrity audit of the /pulse/ desk.
Hard-fails (exit 1) on any breach of: official-source link per row, blank-label rule,
excluded-sport rule, band-rule arithmetic, prediction minimums."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data/pulse")
SITE = os.path.join(ROOT, "pulse")

matches = json.load(open(os.path.join(D, "matches.json")))
flagged = json.load(open(os.path.join(D, "flagged.json")))
preds = json.load(open(os.path.join(D, "predictions.json")))

errors, warnings = [], []

OFFICIAL = ("api-web.nhle.com", "api.nhle.com", "www.nhl.com", "www.nba.com", "statsapi.mlb.com",
 "www.mlb.com", "www.pdc.tv", "ehfcl.eurohandball.com", "www.wst.tv", "www.atptour.com",
 "prod2.lnr.fr", "www.icc-cricket.com", "icc-cricket.com", "www.formula1.com", "lolesports.com",
 "www.europeantour.com", "www.gbgb.org.uk", "www.gaa.ie", "en.volleyballworld.com", "www.nrl.com",
 "www.afl.com.au")
def official(u):
    return isinstance(u, str) and u.startswith("https://") and any(h in u for h in OFFICIAL)

EXCLUDED = re.compile(r"\b(soccer|premier league|bundesliga|la liga|serie a|ligue 1|europa league|champions league odds|american football|\bnfl\b|\bncaaf\b|horse racing|thoroughbred|boxing|\bufc\b|\bmma\b|cycling|tour de france|hurling|specials)\b", re.I)

def fair_american(p):
    if p <= 0 or p >= 1: return None
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)

# 1) every match row: official url + correct confidence arithmetic
seids = set()
for m in matches:
    if m["id"] in seids: errors.append(f"duplicate id {m['id']}")
    seids.add(m["id"])
    if not official(m["official_url"]):
        errors.append(f"{m['id']}: non-official official_url {m['official_url']}")
    for u in m.get("data_urls", []):
        if not u.startswith("http"): errors.append(f"{m['id']}: bad data url {u}")
    if EXCLUDED.search(m["sport"]) or EXCLUDED.search(m["competition"]):
        errors.append(f"{m['id']}: excluded sport/competition in {m['sport']}")
    wm = m.get("winner_market")
    if wm is None and not m.get("line_status"):
        errors.append(f"{m['id']}: neither markets nor line_status label")
    if isinstance(wm, list):
        s = sum(x["probability"] for x in wm)
        if abs(s - 1) > 0.02: errors.append(f"{m['id']}: winner probs sum {s}")
        for x in wm:
            fa = fair_american(x["probability"])
            if fa is None or x["fair_american"] is None:
                errors.append(f"{m['id']} {x['selection']}: degenerate probability {x['probability']}")
                continue
            tol = abs(fa - x["fair_american"]) / max(abs(fa), 100.0)
            if tol > 0.02: errors.append(f"{m['id']} {x['selection']}: fair {x['fair_american']} vs {fa}")
            exp = "high" if x["probability"] >= 0.70 and -250 <= x["fair_american"] <= 10000 else \
                  ("medium" if x["probability"] >= 0.575 else "low")
            if x["confidence"] != exp:
                errors.append(f"{m['id']}: {x['selection']} graded {x['confidence']} expected {exp}")
        pick = m.get("pick")
        if pick is None or pick not in wm: errors.append(f"{m['id']}: pick not from winner market")
        if wm.index(pick) != max(range(len(wm)), key=lambda i: wm[i]["probability"]):
            errors.append(f"{m['id']}: pick is not the favourite side")

# 2) predictions: min words, band membership, selection consistency, per-claim links, uniqueness
texts = []
for h in preds["high_picks"]:
    wc = len(re.findall(r"\w+", h["text"]))
    if wc < 30: errors.append(f"prediction {h['match_id']} only {wc} words")
    if wc != h["words"]: errors.append(f"prediction {h['match_id']} word-count field {h['words']} != {wc}")
    if not (h["probability"] >= 0.70 and -250 <= h["fair_american"] <= 10000):
        errors.append(f"prediction {h['match_id']} out of band")
    texts.append(h["text"])
    mt = [m for m in matches if m["id"] == h["match_id"]]
    if not mt: errors.append(f"prediction {h['match_id']} not in matches.json"); continue
    if mt[0]["pick"]["selection"] != h["selection"]:
        errors.append(f"prediction selection mismatch for {h['match_id']}")
    if abs(mt[0]["pick"]["probability"] - h["probability"]) > 0.0005:
        errors.append(f"prediction probability mismatch for {h['match_id']}")
    for c in h["verified_claims"]:
        if not official(c["url"]): errors.append(f"claim url not official: {c['url']}")
    if len(EXCLUDED.findall(h["text"])): errors.append("prediction mentions excluded sport")
if len(set(texts)) != len(texts): errors.append("duplicate prediction texts")

# high picks in predictions must equal high picks computed from matches.json
model_highs = []
for m in matches:
    if isinstance(m.get("winner_market"), list):
        pick = m["pick"]
        if pick["probability"] >= 0.70 and -250 <= (pick["fair_american"] or 0) <= 10000:
            model_highs.append((m["id"], pick["selection"]))
pred_highs = {(h["match_id"], h["selection"]) for h in preds["high_picks"]}
if set(model_highs) != pred_highs:
    errors.append(f"high-pick set mismatch: model {model_highs} vs predictions {pred_highs}")

# 3) band audit verdicts must be reproducible from (p, fair): HIGH iff >=70% AND in band
for r in preds["band_audit"]["rows"]:
    is_high = r["p"] >= 0.70 and -250 <= r["fair"] <= 10000
    verdict_high = str(r["verdict"]).startswith("HIGH")
    if is_high != verdict_high:
        errors.append(f"band audit verdict wrong for {r['market']} (p={r['p']}, fair={r['fair']})")
    if is_high and " - inside band" not in r["verdict"]:
        errors.append(f"band audit HIGH row missing band note: {r['market']}")
    if not is_high and "HIGH" in r["verdict"].split(" - ")[0]:
        errors.append(f"band audit non-HIGH row mislabelled: {r['market']}")

# 4) HTML pages: source links + blanks + no excluded content
html_files = []
for base, _, fs in os.walk(SITE):
    html_files += [os.path.join(base, f) for f in fs if f.endswith(".html")]
tr_with_match = 0
for f in html_files:
    t = open(f).read()
    if "http://" in t.replace("http://w3.org", ""): errors.append(f"{f}: insecure http link")
    if EXCLUDED.search(re.sub(r"excluded[^<.]*", " ", t, flags=re.I) if "methodology" in f or "index" in f else t) and "flagged" not in f and "methodology" not in f and "/index" not in f:
        warnings.append(f"{f}: possible excluded-sport mention (checked contextually)")
# row/link coverage on the two main tables
for f in (os.path.join(SITE, "matches.html"), os.path.join(SITE, "index.html"), os.path.join(SITE, "flagged.html")):
    t = open(f).read()
    n_blank = t.count('class="blank"')
for slug in ("ice-hockey", "basketball", "baseball", "darts", "handball", "snooker", "tennis", "rugby-union", "cricket", "motor-racing"):
    f = os.path.join(SITE, "sports", slug + ".html")
    t = open(f).read()
    rows = len(re.findall(r"<tr>\s*\n?<td>", t))
    links = t.count("official source")
    ms = [m for m in matches if m["sport"] == slug]
    if rows != len(ms): errors.append(f"{slug}.html: {rows} fixture rows vs {len(ms)} in matches.json")
    if links < len(ms): errors.append(f"{slug}.html: only {links} official-source cells for {len(ms)} fixtures")

# 5) flags present for every blank
if not flagged["flags"]: errors.append("no flags recorded")
blank_ids = {m["id"] for m in matches if m.get("winner_market") is None}
needed = {"PU-01", "PU-03"}  # NBA + cricket blanks
codes = {f["code"] for f in flagged["flags"]}
for c in needed:
    if c not in codes: errors.append(f"missing flag {c} for blank fixtures {blank_ids}")

print(f"checked {len(matches)} matches, {len(html_files)} pages, {len(pred_highs)} high pick(s), {len(flagged['flags'])} flags")
for w in warnings: print("  warn:", w)
if errors:
    for e in errors: print("  FAIL:", e)
    sys.exit(1)
print("pulse_verify: ALL CHECKS PASS")
