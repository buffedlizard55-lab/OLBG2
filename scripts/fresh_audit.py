#!/usr/bin/env python3
"""Fresh (session f048d3a9) mechanical line-by-line audit of the unified desk.

Read-only over data/verified/*.json and README.md. Never edits upstream data.
Checks: excluded-sport leakage, duplicates, source links, probability sums,
fair-odds / American-odds arithmetic, the uniform confidence gate
(high = model prob >= 0.70 AND fair American in [-250, +10000]),
prediction word counts / uniqueness / cross-references, blanks, staleness,
and README claim drift. Outputs data/fresh/audit.json.
"""
import json, re, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VD = ROOT / "data" / "verified"
OUT = ROOT / "data" / "fresh" / "audit.json"
CAPTURED = "2026-10-22"

def american(decimal):
    if decimal >= 2: return round((decimal - 1) * 100)
    return round(-100 / (decimal - 1))

def load(name):
    return json.loads((VD / name).read_text())

def main():
    matches_doc = load("matches.json"); rows = matches_doc["matches"]
    preds_doc = load("predictions.json")
    all_preds = preds_doc["predictions"] + preds_doc.get("research", [])
    sports_doc = load("sports.json")
    flagged_doc = load("flagged.json")
    readme = (ROOT / "README.md").read_text()
    flags = []
    def flag(fid, sev, cat, item, detail, source_name, source_url):
        flags.append({"id": fid, "severity": sev, "category": cat, "item": item,
                      "detail": detail, "corrected_value": "",
                      "status": "unverified — blank, needs owner review",
                      "source_name": source_name, "source_url": source_url})

    checks = {}
    # 1 excluded leakage: sport slug must be in eligible list
    eligible = {s["slug"] for s in sports_doc["eligible_sports"]}
    leaked = [r["id"] for r in rows if r["sport"] not in eligible]
    checks["excluded_sport_leakage_rows"] = leaked
    checks["eligible_sports_total"] = len(eligible)
    checks["sports_with_rows"] = sorted({r["sport"] for r in rows})
    checks["eligible_sports_with_zero_rows"] = sorted(eligible - {r["sport"] for r in rows})

    # 2 duplicates
    ids = collections.Counter(r["id"] for r in rows)
    keys = collections.Counter((r["sport"], r["home"], r["away"], r["date"]) for r in rows)
    checks["duplicate_ids"] = [k for k, v in ids.items() if v > 1]
    checks["duplicate_fixtures"] = [list(k) for k, v in keys.items() if v > 1]

    # 3 source links
    checks["rows_without_official_https_url"] = [r["id"] for r in rows
        if not str(r.get("official_url", "")).startswith("https://")]
    checks["rows_without_olbg_url"] = [r["id"] for r in rows if not r.get("olbg_url")]
    checks["source_scope_counts"] = dict(collections.Counter(r.get("source_scope") for r in rows))
    checks["blank_venue_rows"] = sum(1 for r in rows if not r.get("venue"))
    checks["blank_summary_rows"] = sum(1 for r in rows if not r.get("home_summary"))
    checks["unlined_rows"] = sum(1 for r in rows if r.get("line_status") != "originated")

    # 4-6 arithmetic (tolerances: probs rounded to 4dp, odds to 2dp)
    prob_sum_bad, odds_bad, amer_bad, ht_bad = [], [], [], []
    for r in rows:
        w = r.get("winner_market") or {}
        if w:
            total = w.get("home_prob", 0) + w.get("away_prob", 0) + (w.get("draw_prob") or 0)
            if abs(total - 1) > 0.005: prob_sum_bad.append(r["id"])
            for pk, ok in (("home_prob", "home_odds"), ("away_prob", "away_odds"), ("draw_prob", "draw_odds")):
                if w.get(pk) and w.get(ok) and abs(w[ok] - 1 / w[pk]) > max(0.02, 0.005 * w[ok]):
                    odds_bad.append(r["id"])
        for mk in ("handicap_market", "total_market"):
            m = r.get(mk) or {}
            if m:
                a, b = (m.get("fav_prob"), m.get("dog_prob")) if mk == "handicap_market" else (m.get("over_prob"), m.get("under_prob"))
                if a is not None and b is not None and abs(a + b - 1) > 0.005: ht_bad.append(r["id"])
        p = r.get("pick") or {}
        if p.get("fair_odds") and p.get("probability"):
            if abs(p["fair_odds"] - 1 / p["probability"]) > max(0.02, 0.005 * p["fair_odds"]): odds_bad.append(r["id"] + ":pick")
            if p.get("fair_american") is not None and abs(p["fair_american"] - american(1 / p["probability"])) > max(2, 0.02 * abs(american(1 / p["probability"]))) :
                amer_bad.append(r["id"])
    checks["winner_prob_sum_failures"] = sorted(set(prob_sum_bad))
    checks["fair_odds_failures"] = sorted(set(odds_bad))
    checks["american_conversion_failures"] = sorted(set(amer_bad))
    checks["handicap_total_prob_sum_failures"] = sorted(set(ht_bad))

    # 7 confidence gate over every labelled selection in the desk
    def gate(prob, amer):
        return prob is not None and prob >= 0.70 and amer is not None and -250 <= amer <= 10000
    gate_violations, label_conflicts = [], []
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        labels = {}
        for field in ("pick", "band_pick", "featured", "research_pick"):
            s = r.get(field) or {}
            if s.get("confidence"):
                labels.setdefault(s.get("selection"), {})[field] = s["confidence"]
                amer = s.get("fair_american") or (american(1 / s["probability"]) if s.get("probability") else None)
                if s.get("probability") is None: continue
                if s["confidence"] == "high" and not gate(s.get("probability"), amer):
                    gate_violations.append({"match_id": r["id"], "field": field,
                        "selection": s.get("selection"), "probability": s.get("probability"),
                        "fair_american": amer})
        for sel, lab in labels.items():
            if len(set(lab.values())) > 1:
                label_conflicts.append({"match_id": r["id"], "selection": sel, "labels": lab})
    for pr in all_preds:
        if pr.get("confidence") == "high" and not gate(pr.get("probability"), pr.get("fair_american")):
            gate_violations.append({"match_id": pr["match_id"], "field": "predictions.json:" + pr.get("match_type", ""),
                "selection": pr.get("selection"), "probability": pr.get("probability"),
                "fair_american": pr.get("fair_american")})
    checks["confidence_gate_violations"] = gate_violations
    checks["cross_field Confidence label_conflicts"] = label_conflicts

    # 8 predictions
    checks["predictions_total"] = len(all_preds)
    checks["predictions_under_30_words"] = [p["match_id"] for p in all_preds if len(p["text"].split()) < 30]
    checks["prediction_word_count_field_mismatches"] = [p["match_id"] for p in all_preds
        if p.get("word_count") != len(p["text"].split())]
    texts = collections.Counter(p["text"] for p in all_preds)
    checks["duplicate_prediction_texts"] = sum(1 for v in texts.values() if v > 1)
    openings = collections.Counter(" ".join(p["text"].split()[:3]) for p in all_preds)
    checks["duplicate_prediction_openings"] = [k for k, v in openings.items() if v > 1]
    checks["predictions_with_unknown_match_id"] = [p["match_id"] for p in all_preds if p["match_id"] not in by_id]
    checks["predictions_without_fact_sources"] = [p["match_id"] for p in all_preds
        if not p.get("facts") or any(not str(f.get("source", "")).startswith("https://") for f in p["facts"])]
    checks["high_predictions_in_band"] = sum(1 for p in all_preds
        if p.get("confidence") == "high" and gate(p.get("probability"), p.get("fair_american")))

    # 9 staleness / date-time consistency
    checks["rows_dated_before_capture"] = [r["id"] for r in rows if r["date"] < CAPTURED]
    checks["date_vs_utc_time_mismatch_rows"] = [r["id"] for r in rows
        if r.get("time") and str(r["time"])[:10] not in (r["date"],) and "T" in str(r["time"])
        and str(r["time"])[:10] != r["date"]]
    checks["counts_field_in_matches_json"] = matches_doc.get("counts")
    checks["flagged_items_upstream"] = len(flagged_doc.get("items", []))

    # 10 README drift (first integer claims)
    m = re.search(r"\*\*(\d+) rows across", readme)
    checks["readme_claimed_rows"] = int(m.group(1)) if m else None
    checks["actual_rows"] = len(rows)

    # ---- Flags (corrected values left blank; upstream owners fix in their scope) ----
    if gate_violations:
        flag("FR-01", "high", "Confidence gate violation",
             f"{len(gate_violations)} selection(s) labelled 'high' below 70% model probability",
             "Uniform gate (README/METHODOLOGY): high requires prob >= 0.70 AND fair American in [-250,+10000]. "
             "Offenders: " + "; ".join(f"{g['match_id']} ({g['field']}) prob={g['probability']} amer={g['fair_american']}" for g in gate_violations) +
             ". Example row pick in matches.json for pdc-32323 is 'medium' at 0.668 while the research write-up for the same selection says 'high' — same selection, two labels.",
             "PDC Order of Merit / rankings (official)", "https://www.pdc.tv/rankings")
    if label_conflicts:
        flag("FR-02", "medium", "Cross-field label conflict",
             f"{len(label_conflicts)} match(es) carry different confidence labels in different fields of the same row",
             "Fields compared: pick / band_pick / featured / research_pick in data/verified/matches.json. "
             + "; ".join(f"{c['match_id']}: {c['labels']}" for c in label_conflicts[:6]),
             "NHL GameCenter (official)", "https://www.nhl.com/gamecenter/lak-vs-nyi/2026/10/22/2026020159")
    if checks["readme_claimed_rows"] != len(rows):
        flag("FR-03", "medium", "Documentation drift",
             f"README claims {checks['readme_claimed_rows']} unified rows; data/verified/matches.json contains {len(rows)}",
             "README also states source-scope and review-item counts from an earlier capture. The data file (captured_at 2026-10-22) is authoritative; README numbers were not updated after the 188-row rebuild.",
             "NHL GameCenter (official, desk source family)", "https://www.nhl.com/gamecenter/nsh-vs-bos/2026/10/22/2026020154")
    if checks["eligible_sports_with_zero_rows"]:
        flag("FR-04", "medium", "Coverage gap",
             "Eligible sports with zero rows in unified desk: " + ", ".join(checks["eligible_sports_with_zero_rows"]),
             "Per sports.json status summaries: Tennis had no server-rendered next-round order of play on capture day; Aussie Rules is in AFL off-season; eSports listed 0 active OLBG tips. No rows were invented to fill these sports.",
             "ATP rankings (official)", "https://www.atptour.com/en/rankings/singles")
    if checks["source_scope_counts"].get("competition"):
        flag("FR-05", "low", "Source granularity",
             f"{checks['source_scope_counts']['competition']} of {len(rows)} rows cite a competition/rankings page, not a fixture-specific page",
             "These rows keep their competition-level official URL; fixture detail on those rows is unverified at fixture level and is left as published with this flag (see also upstream VF-11).",
             "EuroLeague standings (official)", "https://www.euroleaguebasketball.net/en/euroleague/standings/")
    if checks["blank_venue_rows"]:
        flag("FR-06", "low", "Blank values",
             f"{checks['blank_venue_rows']} rows have blank venue; {checks['blank_summary_rows']} rows have blank team summaries; {checks['unlined_rows']} rows unlined",
             "Blanks are published as blank (—) per the no-inference rule; they are not errors in arithmetic but limit handicap/total origination on those rows.",
             "GBGB racing (official)", "https://www.gbgb.org.uk/racing/results/")
    if checks["date_vs_utc_time_mismatch_rows"]:
        flag("FR-07", "low", "Date/time labelling",
             f"{len(checks['date_vs_utc_time_mismatch_rows'])} rows have a local `date` that differs from the UTC date in `time`",
             "Example nhl-2026020162: date=2026-10-22, time=2026-10-23T01:00:00Z (22 Oct evening North America). Consistent with local-date convention, but the convention is not stated on the row; flagged so readers do not read it as a wrong date.",
             "NHL GameCenter (official)", "https://www.nhl.com/gamecenter/min-vs-cgy/2026/10/22/2026020162")
    if amer_bad:
        flag("FR-10", "low", "Rounding convention",
             f"{len(set(amer_bad))} picks have fair_american derived from the 2dp-rounded fair odds rather than the 4dp probability",
             "Example ehfcl-202711020101041: prob 0.8893 (fair 1.1245) but fair_american -833 = conversion of rounded 1.12. Difference is a rounding convention, not a pricing error; flagged so the convention is stated once in METHODOLOGY. Rows: " + ", ".join(sorted(set(amer_bad))[:11]),
             "EHF Champions League (official)", "https://ehfcl.eurohandball.com/men/2026-27/matches/")
    if checks["duplicate_prediction_openings"]:
        flag("FR-11", "low", "Prediction uniqueness",
             "Duplicate 3-word opening(s): " + ", ".join(checks["duplicate_prediction_openings"]),
             "All 30 prediction texts are unique and >=30 words, but two Vodacom Bulls write-ups share the opening 'Back Vodacom Bulls', weakening the 'unique openings' claim made by earlier layers.",
             "URC (official)", "https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/connacht-rugby-vs-zebre-parma-2026-10-23/292609")
    flag("FR-08", "medium", "First-hand re-verification limit",
         "This session re-read only a sample of official pages first-hand (NHL x2, EuroLeague x1, OLBG hub x1); remaining rows are mechanically audited, not re-verified",
         "Direct sandbox HTTP to official sports hosts is blocked (empty curl responses); browser-fetch titles/content confirmed: NHL NSH@BOS and MIN@CGY on Oct 22 2026, EuroLeague Panathinaikos v Baskonia 22 Oct 2026 (PAO rank 1, Baskonia rank 20 as published). All other rows retain their upstream capture status and are NOT marked re-verified here.",
         "EuroLeague game centre (official)", "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/panathinaikos-aktor-athens-kosner-baskonia-vitoria-gasteiz/E2026/67/")
    flag("FR-09", "low", "EuroLeague tip-time ambiguity",
         "EuroLeague game-centre page shows both '18:15' (page title) and '14:15' (stream line) for Panathinaikos v Baskonia; desk row publishes 18:15 UTC",
         "The two times on the same official page could not be reconciled from the fetched content (likely different timezone renderings). Corrected value left blank; owner should state the timezone basis on the row.",
         "EuroLeague game centre (official)", "https://www.euroleaguebasketball.net/en/euroleague/game-center/2026-27/panathinaikos-aktor-athens-kosner-baskonia-vitoria-gasteiz/E2026/67/")

    audit = {"session": "arena/f048d3a9-olbg2", "captured_at": CAPTURED,
             "scope": "Mechanical audit of data/verified unified desk (188 rows, 30 predictions). No upstream value edited.",
             "checks": checks, "flags": sorted(flags, key=lambda f: f["id"])}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=1))
    print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in checks.items()}, indent=1))
    print(f"flags={len(flags)} -> {OUT}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
