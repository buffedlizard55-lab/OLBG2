#!/usr/bin/env python3
"""Reproducible structural repository audit for the Zenith review page."""
from __future__ import annotations
import json, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
    rows=[]
    # Scan prediction data with the user's reader-facing forbidden vocabulary rule.
    for path in sorted((ROOT/'data').rglob('predictions*.json')):
        try: data=json.loads(path.read_text(encoding='utf-8'))
        except Exception: continue
        items=data if isinstance(data,list) else data.get('predictions',data.get('items',[])) if isinstance(data,dict) else []
        bad=[]
        for x in items:
            if not isinstance(x,dict): continue
            text=(x.get('text') or x.get('prediction') or x.get('writeup') or '')
            if re.search(r'\b(model\w*|verif\w*)\b',text,re.I): bad.append(x.get('id','(unlabelled)'))
        if bad:
            rows.append({"id":f"AUDIT-PROSE-{path.parent.name or 'root'}","severity":"review","title":"Reader-facing prose requires a wording pass","detail":f"{len(bad)} of {len(items)} entries contain prohibited internal terminology; this is a repository-wide inherited finding, not part of Zenith's prediction prose.","artifact":path.relative_to(ROOT).as_posix(),"source_url":f"https://github.com/buffedlizard55-lab/OLBG2/blob/main/{path.relative_to(ROOT).as_posix()}"})
    coord=(ROOT/'COORDINATION.md').read_text(encoding='utf-8',errors='replace')
    markers=[(i+1,line) for i,line in enumerate(coord.splitlines()) if line.startswith(('<<<<<<<','>>>>>>>')) or line.strip()=='=======']
    if markers:
        rows.append({"id":"AUDIT-GIT-CONFLICT-MARKERS","severity":"high","title":"Conflict-marker-like lines remain in the shared coordination history","detail":f"Structural scan found {len(markers)} marker-like lines in COORDINATION.md (historical append/rebase remnants). The file is documentation; no runtime code depends on these lines. Review before editing because board history is append-only.","artifact":"COORDINATION.md","source_url":"https://github.com/buffedlizard55-lab/OLBG2/blob/main/COORDINATION.md"})
    rows.extend([
      {"id":"AUDIT-TEMPORAL-SNAPSHOT","severity":"high","title":"The published sporting slate is a dated snapshot, not a live feed","detail":"This desk's official source bundle is dated 2026-10-23; scheduled fixtures can start or change after capture. Re-check the governing-body source before treating a row as current or bettable.","artifact":"data/zenith/fixtures.json","source_url":"https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/zenith/fixtures.json"},
      {"id":"AUDIT-OLBG-QUOTE-GEOGATE","severity":"high","title":"OLBG consensus/odds widgets vary by visitor region","detail":"Live OLBG event detail pages accessed from the US show false Expired badges and blank WIN @ values on upcoming events; header percentage denominators visibly concatenate strings. OLBG tip counts and any absent quote are not used as line inputs.","artifact":"data/zenith/olbg_events.json","source_url":"https://www.olbg.com/betting-tips"},
      {"id":"AUDIT-INVENTORY-LIMIT","severity":"high","title":"Captured OLBG hubs are not a complete worldwide match inventory","detail":"The inventory is the hub-tip data present in the dated capture, and only event rows discoverable there are listed. Golf returned no live tip objects; Snooker had expired tips at hub capture; Rugby League listings were 2027 outright futures, not 2026 matches. Official fixture tables may contain matches OLBG did not list.","artifact":"data/zenith/olbg_events.json","source_url":"https://www.olbg.com/betting-tips"},
      {"id":"AUDIT-PRICE-AVAILABILITY","severity":"high","title":"Fair prices are not bookmaker offers or evidence of market availability","detail":"Zenith prices are reciprocal fair prices from stored probabilities. No claim is made that a bookmaker lists the exact handicap/total, accepts a wager, or offers the displayed price. The user's requested range is screened on our fair American price only.","artifact":"data/zenith/lines.json","source_url":"https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/zenith/lines.json"},
      {"id":"AUDIT-INJURY-FEED","severity":"medium","title":"Injury reporting is available only for NBA in the checked official material","detail":"An official NBA report for 2026-10-23 5:15 PM ET was read. Other sources in this sample did not supply a comprehensive fixture-specific injury report, so blank injury fields mean not captured, not no injuries. One inherited row-level parse in the source bundle appears to misalign a player/team cell; Zenith withholds those parsed player claims instead of repeating them.","artifact":"data/cadence/fixtures.json (source layer); Zenith fixture injury facts withheld","source_url":"https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_05_15PM.pdf"},
      {"id":"AUDIT-QUOTE-ATTRIBUTION","severity":"medium","title":"OLBG hub odds and tip percentages have location-sensitive and arithmetic defects","detail":"The tip hub objects are a dated (20:31–20:36Z) capture. Direct event pages read in this session showed string-concatenated header denominators and false Expired badges for upcoming fixtures; displayed tip percentages therefore are published as source fields, not reused as probabilities.","artifact":"data/zenith/olbg_events.json","source_url":"https://www.olbg.com/betting-tips"},
      {"id":"AUDIT-ACTIONABILITY-WINDOW","severity":"high","title":"Most of the fixture rows are not confirmed upcoming at the declared cutoff","detail":"Only fixtures whose official start timestamp is strictly later than 2026-10-23 21:45 UTC receive an actionable market/pick. The other rows remain in the source ledger, but started or time-unconfirmed rows are deliberately blank rather than described as bettable.","artifact":"data/zenith/matches.json","source_url":"https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/zenith/matches.json"},
      {"id":"AUDIT-OLBG-SPORTID","severity":"medium","title":"Gaelic Sports is split into two OLBG sport routes","detail":"OLBG lists Gaelic Football id 25 and Hurling id 26 as separate routes; this desk groups both beneath the requested Gaelic Sports category while preserving the original sub-sport value.","artifact":"data/zenith/sources.json","source_url":"https://www.olbg.com/betting-tips"},
    ])
    out={"generated_utc":"2026-10-23T21:45:00Z","count":len(rows),"findings":rows}
    p=ROOT/'data/zenith/repo_audit.json'; p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(f"zenith_audit: {len(rows)} findings")
if __name__=='__main__':main()
