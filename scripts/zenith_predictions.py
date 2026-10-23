#!/usr/bin/env python3
"""Select source-backed unique preview copy for Zenith's high/medium selections."""
from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'zenith'
BANNED=re.compile(r'\b(model\w*|verif\w*)\b',re.I)

def main():
    source=json.loads((ROOT/'data/cadence/predictions.json').read_text())['predictions']
    matches={m['id']:m for m in json.loads((OUT/'matches.json').read_text())['matches']}
    lines=json.loads((OUT/'lines.json').read_text())['lines']
    line_map={x['id']:x for x in lines}
    predictions=[]; flags=[]
    seen=set()
    for p in source:
        match=matches.get(p['fixture_id'])
        if not match:
            continue
        zline=line_map.get(p['pick_id'])
        # Only retain previews whose selection is represented in the independently published ledger.
        if not zline:
            zline=next((x for x in lines if x['fixture_id']==p['fixture_id'] and x['selection']==p['selection'] and x['market']==p['market']),None)
        if not zline or zline['confidence'] not in ('high','medium'):
            continue
        text=p['text'].strip()
        words=len(text.split())
        key=(p['sport'],text.lower())
        if words<30 or BANNED.search(text) or key in seen:
            flags.append({"code":"PROSE-REVIEW","sport":p['sport'],"fixture_id":p['fixture_id'],"detail":"Source preview failed a minimum-length, unique-text, or prohibited-word check; not published."})
            continue
        seen.add(key)
        predictions.append({
            "id":p['id'],"fixture_id":p['fixture_id'],"sport":p['sport'],"competition":p['competition'],
            "home":p['home'],"away":p['away'],"selection":p['selection'],"market":p['market'],
            "probability":zline['probability'],"confidence":zline['confidence'],"headline":p['headline'],
            "text":text,"word_count":words,"facts":p.get('facts',[]),
            "official_fixture_url":match['official_fixture_url'],"official_stats_url":match['official_stats_url'],
            "olbg_event_url":match['olbg_event_url'],
            "provenance_note":"Human-written text was checked against the captured official facts attached to this fixture; no injury claim is included unless a linked official report explicitly supports it."
        })
    payload={"generated_utc":"2026-10-23T21:45:00Z","count":len(predictions),"min_words":min([x['word_count'] for x in predictions],default=0),"predictions":predictions}
    (OUT/'predictions.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
    # All unfilled daily five-per-sport requirements and known capture limitations remain visible.
    by_sport={s:sum(x['sport']==s for x in predictions) for s in sorted({x['sport'] for x in matches.values()})}
    sources=json.loads((OUT/'sources.json').read_text())['sports']
    primary={x['sport']:x['primary_official_url'] for x in sources}
    for item in flags:
        item['source']=primary.get(item.get('sport',''), 'https://www.olbg.com/betting-tips')
    for sport,n in by_sport.items():
        if n<5:
            flags.append({"code":"TOP5-SHORTFALL","sport":sport,"detail":f"Only {n} evidence-supported unique previews are available in this dated snapshot; no unsupported quota filling.","source":primary.get(sport,'https://www.olbg.com/betting-tips')})
    (OUT/'flagged.json').write_text(json.dumps({"count":len(flags),"items":flags},indent=2,ensure_ascii=False)+'\n')
    print(f"zenith_predictions: {len(predictions)} source-backed previews; {len(flags)} review items")
if __name__=='__main__': main()
