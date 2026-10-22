#!/usr/bin/env python3
"""Daily Top-5 desk: independent line origination + Top-5 selection + predictions.

Prices are OUR originated fair no-vig prices (decimal = 1/p, American derived
from that decimal) — never bookmaker or OLBG prices (OLBG publishes none here).
Confidence: high = model p >= 0.70 AND fair American inside [-250, +10000]
AND sample gate; medium = p >= 0.60; low otherwise. Alternate handicap/total
lines are searched so strong opinions can be expressed inside the focus band.
"""
import json, os, math, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "daily")

def load(n):
    with open(os.path.join(D, n)) as f: return json.load(f)

def norm_cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def pois(k, lam): return math.exp(-lam) * lam ** k / math.factorial(k)
def logistic(x): return 1 / (1 + math.exp(-x))

def fair(p):
    p = min(max(p, 0.01), 0.99)
    dec = round(1 / p, 2)
    am = round(-100 / (dec - 1)) if dec < 2 else round(100 * (dec - 1))
    return dec, am

def in_band(p, am): return p >= 0.70 and -250 <= am <= 10000

def out(name, p, side="", line=""):
    p = round(p, 4)  # price derives from the stored probability so rows always agree
    dec, am = fair(p)
    return {"name": name, "side": side, "line": line, "p": p,
            "fair_decimal": dec, "fair_american": am,
            "confidence": "high" if in_band(p, am) else ("medium" if p >= 0.60 else "low")}

def grid(lh, la, n):
    ph = [pois(i, lh) for i in range(n)]; pa = [pois(j, la) for j in range(n)]
    return ph, pa

def poisson_markets(fx, lh, la, draw_ok, hcap_line=1.5, unit="goals"):
    n = int(max(lh, la) + 6 * math.sqrt(max(lh, la)) + 12)
    ph, pa = grid(lh, la, n)
    pw = pd = pl = phc = 0.0; tot = {}
    for i in range(n):
        for j in range(n):
            q = ph[i] * pa[j]
            if i > j: pw += q
            elif i == j: pd += q
            else: pl += q
            if i - j >= hcap_line + 0.5 or (hcap_line == 1.5 and i - j >= 2): phc += q
            tot[i + j] = tot.get(i + j, 0) + q
    s = pw + pd + pl; pw, pd, pl, phc = pw / s, pd / s, pl / s, phc / s
    tot = {k: v / s for k, v in tot.items()}
    exp_tot = lh + la
    tline = math.floor(exp_tot) + 0.5
    pover = sum(v for k, v in tot.items() if k > tline)
    mk = []
    if draw_ok:
        mk.append({"market": "Match Result (1X2)", "line": "", "outcomes": [
            out(fx["home"], pw, "home"), out("Draw", pd, "draw"), out(fx["away"], pl, "away")]})
        p2h = pw / (pw + pl)
        mk.append({"market": "Match Winner (2-way, draw no bet)", "line": "", "outcomes": [
            out(fx["home"], p2h, "home"), out(fx["away"], 1 - p2h, "away")]})
    else:
        p2h = pw + pd / 2
        mk.append({"market": "Match Winner (incl. OT/SO or extra innings)", "line": "", "outcomes": [
            out(fx["home"], p2h, "home"), out(fx["away"], 1 - p2h, "away")]})
    # handicap: standard line +/-1.5 plus one alternate step each side for band search.
    # Convention: hl>0 -> home gives hl (home -hl, away +hl); hl<0 -> home receives.
    margin = {}
    for i in range(n):
        for j in range(n):
            margin[i - j] = margin.get(i - j, 0) + ph[i] * pa[j] / s
    outs = []
    for hl in [-2.5, -1.5, 1.5, 2.5]:
        pc = sum(v for k, v in margin.items() if k > hl)  # P(home covers -hl line)
        lab_h = f"{fx['home']} {'-' if hl > 0 else '+'}{abs(hl)}"
        lab_a = f"{fx['away']} {'+' if hl > 0 else '-'}{abs(hl)}"
        outs.append(out(lab_h, pc, "home", -hl)); outs.append(out(lab_a, 1 - pc, "away", hl))
    mk.append({"market": f"Handicap ({unit})", "line": hcap_line, "outcomes": outs})
    touts = []
    for tl in [tline - 1, tline, tline + 1, tline + 2]:
        po = sum(v for k, v in tot.items() if k > tl)
        touts.append(out(f"Over {tl}", po, "over", tl)); touts.append(out(f"Under {tl}", 1 - po, "under", tl))
    total_unit = "Runs" if "run" in unit else "Goals"
    mk.append({"market": f"Match Total {total_unit} (Over/Under)", "line": tline, "outcomes": touts})
    return mk, lh - la, exp_tot

def margin_markets(fx, exp_h, exp_a, sigma, draw_ok=False):
    m = exp_h - exp_a; tot = exp_h + exp_a
    ph = norm_cdf(m / sigma)
    mk = [{"market": "Match Winner (2-way)" if not draw_ok else "Match Winner (2-way, draw no bet)", "line": "",
           "outcomes": [out(fx["home"], ph, "home"), out(fx["away"], 1 - ph, "away")]}]
    base = -round(m) - 0.5 if m >= 0 else -round(m) + 0.5
    outs = []
    for hl in sorted(set([base + k for k in (-14, -11, -8, -6, -4, -3, -2, -1, 0, 1, 2, 3, 4, 6, 8, 11, 14)])):
        pc = norm_cdf((m + hl) / sigma)  # home receiving hl points (hl can be negative = giving)
        lab_h = f"{fx['home']} {'+' if hl > 0 else '-'}{abs(hl)}"
        lab_a = f"{fx['away']} {'-' if hl > 0 else '+'}{abs(hl)}"
        outs.append(out(lab_h, pc, "home", hl)); outs.append(out(lab_a, 1 - pc, "away", -hl))
    mk.append({"market": "Handicap / Point Spread", "line": base, "outcomes": outs})
    tline = math.floor(tot) + 0.5
    touts = []
    for tl in [tline - 12, tline - 9, tline - 6, tline - 3, tline, tline + 3, tline + 6, tline + 9, tline + 12]:
        po = 1 - norm_cdf((tl - tot) / (sigma * 1.35))
        touts.append(out(f"Over {tl}", po, "over", tl)); touts.append(out(f"Under {tl}", 1 - po, "under", tl))
    mk.append({"market": "Match Total Points (Over/Under)", "line": tline, "outcomes": touts})
    return mk, m, tot

def shrink_rates(h, a, kf="gf", ka="ga", prior_gp=8):
    gp_h, gp_a = h["gp"], a["gp"]
    return gp_h, gp_a

def poisson_inputs(teams, kf, ka):
    avg = sum(t[kf] for t in teams) / sum(t["gp"] for t in teams)
    return avg

def main():
    F = load("fixtures.json"); fixtures = F["fixtures"]
    # league environments from the seeded inputs themselves
    nhl = {f["inputs"]["home"]["abbrev"]: f["inputs"]["home"] for f in fixtures if f["sport"] == "ice-hockey"}
    for f in fixtures:
        if f["sport"] == "ice-hockey": nhl[f["inputs"]["away"]["abbrev"]] = f["inputs"]["away"]
    nhl_avg = sum(t["gf"] for t in nhl.values()) / sum(t["gp"] for t in nhl.values()) if nhl else 3.0
    el = {}
    for f in fixtures:
        if f["family"] == "margin" and "EuroLeague" in f["competition"]:
            el[f["home"]] = f["inputs"]["home"]; el[f["away"]] = f["inputs"]["away"]
    # full EuroLeague env from verified inputs file directly (standings of 20)
    with open(os.path.join(ROOT, "data", "verified", "inputs.json")) as fh: V = json.load(fh)
    el_avg = sum(t["pf"] for t in V["euroleague_teams"].values()) / sum(t["gp"] for t in V["euroleague_teams"].values())
    env = {}
    for key, tk in [("Top 14", "top14_teams"), ("Pro D2", "prod2_teams")]:
        ts = V[tk].values(); env[key] = sum(t["pf"] for t in ts) / sum(t["gp"] for t in ts)
    urc_ts = V["urc_teams"].values(); urc_avg = sum(t["pf"] for t in urc_ts) / sum(t["gp"] for t in urc_ts)
    ehf_ts = V["ehf_teams"].values(); ehf_avg = sum(t["gf"] for t in ehf_ts) / sum(t["gp"] for t in ehf_ts)

    lines, all_picks = [], []
    for fx in fixtures:
        fam = fx["family"]; inp = fx["inputs"]; note = ""; gate = True; cap = ""
        try:
            if fam == "poisson":  # NHL
                h, a = inp["home"], inp["away"]
                def att(t): 
                    w = t["gp"] / (t["gp"] + 8); return 1 + w * ((t["gf"]/t["gp"])/nhl_avg - 1)
                def dfc(t):
                    w = t["gp"] / (t["gp"] + 8); return 1 + w * ((t["ga"]/t["gp"])/nhl_avg - 1)
                lh = nhl_avg * att(h) * dfc(a) * 1.05; la = nhl_avg * att(a) * dfc(h) / 1.05
                mk, em, et = poisson_markets(fx, lh, la, draw_ok=False, unit="goals (puck line)")
                if min(h["gp"], a["gp"]) < 7: gate = False; cap = "Sample gate: fewer than 7 games for one side — confidence capped below high."
            elif fam == "poisson_handball":
                h, a = inp["home"], inp["away"]
                def att2(t):
                    w = t["gp"] / (t["gp"] + 3); return 1 + w * ((t["gf"]/t["gp"])/ehf_avg - 1)
                def dfc2(t):
                    w = t["gp"] / (t["gp"] + 3); return 1 + w * ((t["ga"]/t["gp"])/ehf_avg - 1)
                lh = ehf_avg * att2(h) * dfc2(a) + 0.4; la = ehf_avg * att2(a) * dfc2(h) - 0.4
                mk, em, et = poisson_markets(fx, lh, la, draw_ok=True, unit="goals")
                if min(h["gp"], a["gp"]) < 4: gate = False; cap = "Sample gate: fewer than 4 group games — capped below high."
            elif fam == "poisson_baseball":
                h, a = inp["home"], inp["away"]; avg = inp.get("league_runs_pg") or 4.4
                gh, ga_ = h["wins"] + h["losses"], a["wins"] + a["losses"]
                lh = avg * (h["runs_scored"]/gh/avg) * (a["runs_allowed"]/ga_/avg) * 1.02
                la = avg * (a["runs_scored"]/ga_/avg) * (h["runs_allowed"]/gh/avg) / 1.02
                mk, em, et = poisson_markets(fx, lh, la, draw_ok=False, unit="runs (run line)")
                gate = False; cap = "No verified probable-pitcher input captured — confidence capped at medium."
            elif fam == "nba_prior":
                h, a = inp["home"], inp["away"]
                def rating(t):
                    sh = 0.75 * (t["w"]/(t["w"]+t["l"])) + 0.125; return math.log(sh/(1-sh))
                m = 11.0 * (rating(h) + 0.20 - rating(a))
                # totals not originated: no official PF/PA input
                ph = norm_cdf(m / 12.0)
                base = -round(m) - 0.5 if m >= 0 else -round(m) + 0.5
                outs = []
                for hl in sorted(set([base + k for k in (-14,-11,-8,-6,-4,-2,0,2,4,6,8,11,14)])):
                    pc = norm_cdf((m + hl) / 12.0)
                    outs.append(out(f"{fx['home']} {'+' if hl>0 else '-'}{abs(hl)}", pc, "home", hl))
                    outs.append(out(f"{fx['away']} {'-' if hl>0 else '+'}{abs(hl)}", 1-pc, "away", -hl))
                mk = [{"market": "Moneyline (2-way)", "line": "", "outcomes": [out(fx["home"], ph, "home"), out(fx["away"], 1-ph, "away")]},
                      {"market": "Point Spread", "line": base, "outcomes": outs},
                      {"market": "Game Total (Over/Under)", "line": "", "outcomes": [],
                       "blank_reason": "Not originated: no verified official points-for/against input captured for 2026-27 (0 games played at capture)."}]
                em, et = m, None
                gate = False; cap = "Prior-season (2025-26) records only; 2026-27 had 0 games at capture — confidence capped at medium."
            elif fam == "margin":
                h, a = inp["home"], inp["away"]
                if "EuroLeague" in fx["competition"]:
                    avg, sig, prior, home_adj = el_avg, 11.0, 3, 3.0
                elif "Top 14" in fx["competition"]:
                    avg, sig, prior, home_adj = env["Top 14"], 14.0, 6, 3.0
                elif "Pro D2" in fx["competition"]:
                    avg, sig, prior, home_adj = env["Pro D2"], 14.0, 6, 3.0
                else:
                    avg, sig, prior, home_adj = urc_avg, 14.0, 6, 3.0
                def att3(t):
                    w = t["gp"] / (t["gp"] + prior); return 1 + w * ((t["pf"]/t["gp"])/avg - 1)
                def dfc3(t):
                    w = t["gp"] / (t["gp"] + prior); return 1 + w * ((t["pa"]/t["gp"])/avg - 1)
                eh = avg * att3(h) * dfc3(a) + home_adj/2; ea = avg * att3(a) * dfc3(h) - home_adj/2
                mk, em, et = margin_markets(fx, eh, ea, sig, draw_ok=(fx["sport"] == "rugby-union"))
                if fx["sport"] == "rugby-union" and min(h["gp"], a["gp"]) < 3:
                    gate = False; cap = "Sample gate: fewer than 3 league rounds — capped below high."
            elif fam == "darts":
                h, a = inp["home"], inp["away"]
                pl_ = logistic(0.45 * (math.log(h["prize_gbp"]) - math.log(a["prize_gbp"])))  # per-leg, damped log-prize
                # first to 6 (best of 11)
                pm = sum(math.comb(5+k, k) * pl_**6 * (1-pl_)**k for k in range(0, 6))
                ph15 = sum(math.comb(5+k, k) * pl_**6 * (1-pl_)**k for k in range(0, 5))  # win by 2+ legs
                pl10 = sum(math.comb(5+k, k)*(pl_**6*(1-pl_)**k + (1-pl_)**6*pl_**k) for k in range(4, 6))  # 10+ legs
                mk = [{"market": "Match Winner (best of 11 legs)", "line": "", "outcomes": [out(fx["home"], pm, "home"), out(fx["away"], 1-pm, "away")]},
                      {"market": "Leg Handicap -1.5/+1.5", "line": -1.5, "outcomes": [out(f"{fx['home']} -1.5 legs", ph15, "home", -1.5), out(f"{fx['away']} +1.5 legs", 1-ph15, "away", 1.5)]},
                      {"market": "Total Legs Over/Under 9.5", "line": 9.5, "outcomes": [out("Over 9.5 legs", pl10, "over", 9.5), out("Under 9.5 legs", 1-pl10, "under", 9.5)]}]
                em, et = None, None
            elif fam == "outright":  # F1
                dr = inp["drivers"]
                tot_pts = sum(max(d["pts"], 1) for d in dr)
                ow = []
                wins = {}
                for w in inp.get("winners", []):
                    nm = w.get("winner") or w.get("driver") or ""
                    if nm: wins[nm] = wins.get(nm, 0) + 1
                for d in dr:
                    share = max(d["pts"], 1) / tot_pts
                    p = 0.65 * share + 0.35 * (wins.get(d["driver"], 0) / max(len(inp.get("winners", [])), 1))
                    ow.append((d, p))
                ssum = sum(p for _, p in ow); ow = [(d, p/ssum) for d, p in ow]
                mk = [{"market": "Race Winner", "line": "", "outcomes": [out(d["driver"], p, "", "") for d, p in ow]}]
                em, et = None, None
                gate = False; cap = "Outright market from season points share + recorded race wins only; no qualifying/car input — capped at medium."
            else:
                continue
        except Exception as e:
            lines.append({"match_id": fx["id"], "originated": False, "blank_reason": f"Model input incomplete: {e}"})
            continue
        # pick winner + best in-band selection
        best = None; winner = None
        for mkt in mk:
            for o in mkt["outcomes"]:
                o["market"] = mkt["market"]
                if "Winner" in mkt["market"] or "Moneyline" in mkt["market"]:
                    if winner is None or o["p"] > winner["p"]: winner = o
                if in_band(o["p"], o["fair_american"]) and gate:
                    if best is None or o["p"] < best["p"]: best = o
        if best is not None and winner is not None and best is not winner:
            pass  # in-band alternate expresses the opinion inside -250..+10000
        if best is None:
            # No in-band selection: the primary pick IS the match winner pick
            # (honest headline call), never an extreme alternate line at ~1.01.
            best = winner
            if best and not gate and best["confidence"] == "high": best["confidence"] = "medium"
        row = {"match_id": fx["id"], "sport": fx["sport"], "originated": True,
               "expected_margin": round(em, 2) if em is not None else None,
               "expected_total": round(et, 2) if et is not None else None,
               "winner_pick": winner, "primary_pick": best, "confidence_cap_note": cap, "markets": mk}
        lines.append(row)
        if best:
            all_picks.append({"match_id": fx["id"], "sport": fx["sport"], "date": fx["date"],
                              "fixture": f"{fx['home']} v {fx['away']}" if fx["away"] else fx["home"],
                              "competition": fx["competition"], "selection": best["name"],
                              "market": best["market"], "p": best["p"], "fair_decimal": best["fair_decimal"],
                              "fair_american": best["fair_american"], "confidence": best["confidence"],
                              "official_url": fx["official_url"]})
    json.dump({"generated_by": "scripts/daily_model.py", "gate": {"high": "p>=0.70 AND fair American in [-250,10000] AND sample gate"},
               "rows": lines}, open(os.path.join(D, "lines.json"), "w"), indent=1)

    # ----- Top 5 per sport -----
    sports = [s["slug"] for s in load("sports.json")["sports"]]
    top5 = {}
    for sp in sports:
        cand = sorted([p for p in all_picks if p["sport"] == sp], key=lambda p: (-p["p"], p["date"], p["match_id"]))[:5]
        for i, p in enumerate(cand, 1): p["sport_rank"] = i
        top5[sp] = cand
    json.dump({"generated_by": "scripts/daily_model.py", "rule": "Top 5 by model probability of each match's strongest in-band-or-best selection, per sport, upcoming window only.",
               "top5": top5}, open(os.path.join(D, "top5.json"), "w"), indent=1)

    # ----- Predictions: union of Top-5 and all high-confidence picks -----
    fx_by_id = {f["id"]: f for f in fixtures}
    line_by_id = {r["match_id"]: r for r in lines if r.get("originated")}
    need = {}
    for sp, cand in top5.items():
        for p in cand: need[p["match_id"]] = p
    for p in all_picks:
        if p["confidence"] == "high": need[p["match_id"]] = p
    preds = [write_prediction(fx_by_id[mid], line_by_id[mid], p) for mid, p in sorted(need.items()) if mid in line_by_id]
    json.dump({"generated_by": "scripts/daily_model.py",
               "rule": "Written prediction for every Top-5-per-sport pick and every high-confidence (p>=70%, -250..+10000) pick. Facts only from the seeded official inputs on the row.",
               "count": len(preds), "predictions": preds}, open(os.path.join(D, "predictions.json"), "w"), indent=1)

    # ----- Flags -----
    unlined = load("unlined.json")
    flags = []
    n = 0
    for sp in sports:
        rows_sp = [f for f in fixtures if f["sport"] == sp]
        un_sp = [u for u in unlined["unlined"] if u["sport"] == sp]
        if not rows_sp and not un_sp:
            n += 1; flags.append({"id": f"DA-{n:02d}", "sport": sp, "kind": "zero-row sport",
                "item": f"No fixture row for {sp} in 2026-10-23..2026-10-30 window",
                "detail": unlined["zero_row_reasons"].get(sp, "No official fixture captured in window."),
                "official_url": next((s["official_url"] for s in load("sports.json")["sports"] if s["slug"] == sp), "")})
        elif len(top5.get(sp, [])) < 5:
            n += 1; flags.append({"id": f"DA-{n:02d}", "sport": sp, "kind": "fewer than 5 originated picks",
                "item": f"{sp}: only {len(top5.get(sp, []))} originated upcoming match(es) — Top-5 target not met, slots left blank",
                "detail": "The remaining Top-5 slots are deliberately blank: no further fixture with verified origination inputs exists in the window. Nothing was invented to fill the quota.",
                "official_url": next((s["official_url"] for s in load("sports.json")["sports"] if s["slug"] == sp), "")})
    for u in unlined["unlined"]:
        n += 1; flags.append({"id": f"DA-{n:02d}", "sport": u["sport"], "kind": "unlined fixture (blank price)",
            "item": f"{u['home']} v {u['away']} ({u['date']})", "detail": u["blank_reason"], "official_url": u["official_url"]})
    for r in lines:
        if not r.get("originated"):
            n += 1; flags.append({"id": f"DA-{n:02d}", "sport": fx_by_id.get(r["match_id"], {}).get("sport", ""), "kind": "model blank",
                "item": r["match_id"], "detail": r.get("blank_reason", ""), "official_url": fx_by_id.get(r["match_id"], {}).get("official_url", "")})
    json.dump({"flags": flags}, open(os.path.join(D, "flagged.json"), "w"), indent=1)
    print(f"lines={len(lines)} picks={len(all_picks)} high={sum(1 for p in all_picks if p['confidence']=='high')} preds={len(preds)} flags={len(flags)}")

OPENERS = [
 "Back {sel} — that is the call here.",
 "The selection is {sel}.",
 "{sel} gets the vote in this one.",
 "Side with {sel} at {venue}.",
 "Take {sel} to land the money.",
 "Our originated line points firmly to {sel}.",
]
FORM_T = [
 "{home} come in at {hform}, while {away} are {aform}.",
 "Form first: {home} ({hform}) against {away} ({aform}).",
 "On the numbers that count, {home} show {hform} and {away} show {aform}.",
 "Recent history matters: {home} bring {hform}; {away} bring {aform}.",
]
RATE_T = [
 "Per game that is {hrate} scored and {hcon} conceded for the hosts, against {arate} scored and {acon} conceded for the visitors.",
 "The scoring split reads {hrate} for / {hcon} against per game for {home}, and {arate} / {acon} for {away}.",
 "Dig one layer down and {home} average {hrate} for and {hcon} against, with {away} at {arate} and {acon}.",
]
CLOSE_T = [
 "Our model makes it a {pct}% shot (fair {dec}, {am}), which clears the 70% high-confidence bar inside the -250 to +10000 focus band.",
 "Priced from scratch, we make this {pct}% — fair odds {dec} ({am}) — comfortably in the target odds window.",
 "The originated probability is {pct}% at a fair {dec} ({am}); treat the price as our own line, not a bookmaker quote.",
 "At {pct}% (fair {dec} / {am}) this is one of the strongest ratings on the whole {sport} slate this week.",
]

def _rec(t):
    if "wins" in t: return f"{t['wins']}-{t['losses']}"
    if "w" in t and "l" in t:
        s = f"{t['w']}-{t['l']}"
        if t.get("d"): s = f"{t['w']}-{t['d']}-{t['l']}"
        if t.get("otl"): s = f"{t['w']}-{t['l']}-{t['otl']}"
        return s
    return t.get("record", "")

def write_prediction(fx, row, pick):
    h = hashlib.sha256(fx["id"].encode()).hexdigest()
    rnd = lambda k: int(h[k:k+2], 16)
    inp = fx["inputs"]; ht, at = inp.get("home", {}), inp.get("away", {})
    venue = fx.get("venue") or "the scheduled venue"
    sel = pick["selection"]
    disp = sel if not sel.startswith(("Over ", "Under ")) else f"{sel} in {fx['home']} v {fx['away']}"
    parts = [OPENERS[rnd(0) % len(OPENERS)].format(sel=disp, venue=venue)]
    fam = fx["family"]
    if fam == "outright":
        dr = {d["driver"]: d for d in inp["drivers"]}
        d = dr.get(sel, {})
        parts.append(f"{sel} ({d.get('team','')}) leads the cast here on {d.get('pts','')} championship points (P{d.get('pos','')}) after 17 rounds, with the standings taken straight from formula1.com on 22 October.")
        prev = inp.get("previous_round", {})
        parts.append(f"The championship resumes at Round 18 in the United States (weekend rendered 23-25 Oct) after Round 17 in {prev.get('country','Singapore')} (09-11 Oct), so recent form is measured in season points and recorded race wins rather than a head-to-head.")
    elif fam == "darts":
        parts.append(f"The official PDC Werner Rankings Ladder puts {fx['home']} at No.{ht.get('rank')} with £{ht.get('prize_gbp',0):,} in ranking prize money, against {fx['away']} at No.{at.get('rank')} with £{at.get('prize_gbp',0):,} — a gulf of £{abs(ht.get('prize_gbp',0)-at.get('prize_gbp',0)):,} on the two-year ladder.")
        parts.append("It is a first-to-six-legs Round 1 tie at the European Championship, so the ranking gap is converted leg-by-leg in our model rather than treated as a coin flip over a short race.")
    elif fam == "nba_prior":
        parts.append(FORM_T[rnd(2) % len(FORM_T)].format(
            home=fx["home"], away=fx["away"],
            hform=f"a {ht.get('w')}-{ht.get('l')} record in 2025-26 (home {ht.get('home_w')}-{ht.get('home_l')})",
            aform=f"{at.get('w')}-{at.get('l')} last season (road {at.get('road_w')}-{at.get('road_l')})"))
        parts.append("Honesty clause: nobody had played a 2026-27 game when these official standings were captured, so this is a prior-season rating with home court added — which is exactly why confidence is capped at medium.")
    else:
        kf = "pf" if "pf" in ht else ("gf" if "gf" in ht else "runs_scored")
        ka = "pa" if "pa" in ht else ("ga" if "ga" in ht else "runs_allowed")
        gp_h = ht.get("gp") or (ht.get("wins", 0) + ht.get("losses", 0))
        gp_a = at.get("gp") or (at.get("wins", 0) + at.get("losses", 0))
        hf = _rec(ht); af = _rec(at)
        form_h = ht.get("form") if isinstance(ht.get("form"), str) else ""
        form_a = at.get("form") if isinstance(at.get("form"), str) else ""
        extra_h = f", form line {form_h}" if form_h else ""
        extra_a = f", form line {form_a}" if form_a else ""
        parts.append(FORM_T[rnd(2) % len(FORM_T)].format(
            home=fx["home"], away=fx["away"],
            hform=f"{hf} through {gp_h} games{extra_h}", aform=f"{af} through {gp_a}{extra_a}"))
        if gp_h and gp_a and ht.get(kf) is not None:
            parts.append(RATE_T[rnd(4) % len(RATE_T)].format(
                home=fx["home"], away=fx["away"],
                hrate=f"{ht[kf]/gp_h:.2f}", hcon=f"{ht[ka]/gp_h:.2f}",
                arate=f"{at[kf]/gp_a:.2f}", acon=f"{at[ka]/gp_a:.2f}"))
        leaders = inp.get("leaders", {})
        for code, team_name in [(fx.get("home_code"), fx["home"]), (fx.get("away_code"), fx["away"])]:
            ld = leaders.get(code, {})
            if ld.get("goals"):
                g = ld["goals"]; a_ = ld.get("assists", {})
                parts.append(f"Player watch for {team_name}: {g['player']} leads them with {g['value']} goals"
                             + (f", {a_['player']} tops the assists chart on {a_['value']}" if a_ else "")
                             + " per the official NHL score feed.")
                break
    if fx.get("competition"):
        parts.append(f"It is {fx['competition']} business on {fx['date']}" + (f" at {venue}" if fx.get("venue") else "") + ".")
    if row.get("confidence_cap_note") and pick["confidence"] != "high" and fam != "nba_prior":
        parts.append("Confidence note: " + row["confidence_cap_note"])
    if pick["confidence"] == "high":
        parts.append(CLOSE_T[rnd(6) % len(CLOSE_T)].format(
            pct=f"{pick['p']*100:.1f}", dec=pick["fair_decimal"], am=pick["fair_american"], sport=fx["sport"]))
    else:
        why = ("the model probability clears 70% but the fair price sits outside the -250 to +10000 focus band (or a confidence cap applies), so it is not labelled high" if pick["p"] >= 0.70 else "below the 70% high-confidence threshold, so it is rated on Top-5 merit only")
        parts.append(f"Our originated price makes it {pick['p']*100:.1f}% (fair {pick['fair_decimal']} / {pick['fair_american']}), graded {pick['confidence']} confidence because {why}; the price is our own line rather than a bookmaker quote.")
    text = " ".join(p.strip() for p in parts if p.strip())
    return {"match_id": fx["id"], "sport": fx["sport"], "date": fx["date"],
            "fixture": f"{fx['home']} v {fx['away']}" if fx["away"] else fx["home"],
            "competition": fx["competition"], "selection": sel, "market": pick["market"],
            "p": pick["p"], "fair_decimal": pick["fair_decimal"], "fair_american": pick["fair_american"],
            "confidence": pick["confidence"], "official_url": fx["official_url"],
            "word_count": len(text.split()), "text": text}

if __name__ == "__main__":
    main()
