#!/usr/bin/env python3
"""Build a 15-category inventory from the stored raw OLBG hub tip-object ledger.

Capture timestamp is preserved from the original HTTP manifest. The 21:45Z status label
is a later evaluation against the captured event start; it does not claim a later refetch.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'zenith'
SPORTS={"Golf":"golf","Volleyball":"volleyball","Rugby Union":"rugby-union","Cricket":"cricket","Snooker":"snooker","Darts":"darts","Baseball":"baseball","Gaelic Football":"gaelic-sports","Hurling":"gaelic-sports","Greyhounds":"greyhounds","Tennis":"tennis","Motor Racing":"motor-racing","Handball":"handball","Ice Hockey":"ice-hockey","Basketball":"basketball","Rugby League":"rugby-league"}
CUTOFF='2026-10-23T21:45:00Z'
def main():
 raw=json.loads((ROOT/'data/ledger/olbg.json').read_text()); grouped={}; excluded={}
 for row in raw.get('tips',[]):
  source_sport=row.get('sport','')
  if source_sport not in SPORTS:
   excluded[source_sport]=excluded.get(source_sport,0)+1; continue
  sport=SPORTS[source_sport]; eid=str(row.get('event_id') or '')
  if not eid: continue
  key=(sport,eid)
  start=row.get('start') or ''
  expired=str(row.get('olbg_expired') or '0')
  if expired=='1': state='expired_on_olbg_capture'
  elif start and start<=CUTOFF: state='started_or_completed_by_2145z'
  else: state='strictly_future_by_2145z'
  e=grouped.setdefault(key,{
   'sport':sport,'olbg_sub_sport':source_sport,'sport_slug':SPORTS[source_sport],
   'event_id':eid,'event':row.get('event',''),'competition':row.get('competition',''),
   'start_utc':start,'olbg_expired_flag':expired,'evaluated_state_at_utc_cutoff':state,
   'event_url':row.get('event_url',''),'page_url':row.get('page_url',''),
   'first_capture_utc':row.get('captured_at',''),'markets_on_hub':[]})
  market={
   'market':row.get('market',''),'selection':row.get('selection',''),
   'olbg_consensus_tips':int(row['olbg_win_tips']) if str(row.get('olbg_win_tips','')).isdigit() else None,
   'olbg_confidence_pct':row.get('olbg_confidence'),
   'quoted_decimal':row.get('olbg_decimal') or None,
   'quoted_american':row.get('olbg_american') or None,
   'quoted_fractional':row.get('olbg_fractional') or None,
   'comments':int(row['olbg_comments']) if str(row.get('olbg_comments','')).isdigit() else None,
   'quote_note':'OLBG-displayed quote at the source capture; not our line; regional suppression/expiry bugs observed.'}
  if market not in e['markets_on_hub']:e['markets_on_hub'].append(market)
 events=sorted(grouped.values(),key=lambda x:(x['sport'],x['start_utc'] or '9999',x['event_id']))
 by={}
 for sport in sorted(set(SPORTS.values())):
  es=[x for x in events if x['sport']==sport]
  by[sport]={'total_events':len(es),'strictly_future_by_cutoff':sum(x['evaluated_state_at_utc_cutoff']=='strictly_future_by_2145z' for x in es),'started_or_completed_by_cutoff':sum(x['evaluated_state_at_utc_cutoff']=='started_or_completed_by_2145z' for x in es),'expired_on_olbg_capture':sum(x['evaluated_state_at_utc_cutoff']=='expired_on_olbg_capture' for x in es)}
 data={'capture_timestamp_utc':raw.get('meta',{}).get('generated_at',''),'status_evaluated_at_utc':CUTOFF,'session':'arena/110cf432-olbg2','sport_count':15,'excluded_out_of_scope_tip_rows':excluded,'olbg_architecture':{'sport_hub_pattern':'/betting-tips/{sportSlug}/{sportId}','all_events_pattern':'/betting-tips/{sportSlug}/All_{sportSlug}/All_Events/{sportId}','event_detail_pattern':'/betting-tips/{sportSlug}/{competition}/{eventSlug}/{sportId}?event_id={eventId}','sports':[{'sport':s,'olbg_route_ids':([25,26] if s=='Gaelic Sports' else next((entry['olbg_sport_ids'] for entry in json.loads((OUT/'sources.json').read_text())['sports'] if entry['sport']==s),[]))} for s in sorted(set(SPORTS.values()))]},'live_event_page_probes':json.loads((OUT/'olbg_events.json').read_text()).get('live_event_page_probes',[]),'by_sport_summary':by,'total_unique_covered_hub_events':len(events),'strictly_future_by_cutoff':sum(x['evaluated_state_at_utc_cutoff']=='strictly_future_by_2145z' for x in events),'events':events}
 (OUT/'olbg_events.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
 print(f"zenith_olbg: {len(events)} event IDs, {sum(len(x['markets_on_hub']) for x in events)} tip-market selections, captured {data['capture_timestamp_utc']}; status cutoff {CUTOFF}")
if __name__=='__main__':main()
