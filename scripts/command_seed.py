#!/usr/bin/env python3
"""Build the bounded source-transcription ledger without importing other desks."""
import json
from pathlib import Path
from command_model import originate
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/command'


def build():
    captured = json.loads((DATA/'inputs.json').read_text())
    rows = []
    for r in captured['fixtures']:
        row = dict(r)
        row['markets'] = None
        row['winner_pick'] = None
        row['confidence'] = None
        row['blank_reason'] = 'Scoring/ranking/form inputs not independently transcribed; no price or selection inferred.'
        if r['rates'] and r['status'] == 'scheduled on source':
            row['markets'] = originate(r['rates']['home'], r['rates']['away'])
            side = row['markets']['winner_selection']
            row['winner_pick'] = row[side]
            row['confidence'] = row['markets']['winner'][side]['confidence']
            row['blank_reason'] = None
        if 'live' in r['status'] or 'warming' in r['status']:
            row['blank_reason'] = 'Already live or warming up in the source response; no pre-match tip published.'
        if r['sport'] == 'greyhounds':
            row['blank_reason'] = 'Calendar event confirmed, but runner card/start time/form unavailable; all market fields blank.'
        rows.append(row)
    result = {'snapshot_date': captured['snapshot_date'], 'coverage': captured['coverage'],
              'counts': {'rows':len(rows), 'originated':sum(bool(r['markets']) for r in rows),
                         'high':sum(r['confidence']=='high' for r in rows)}, 'matches':rows}
    (DATA/'matches.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    (DATA/'predictions.json').write_text(json.dumps({'predictions':[], 'reason':'No high-confidence model meets both the strict odds/probability gate and independent calibration safeguard. Do not fabricate predictions to meet a quota.'},indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(build()['counts'])
