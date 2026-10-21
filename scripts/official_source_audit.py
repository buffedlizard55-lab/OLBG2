#!/usr/bin/env python3
"""Read-only provenance audit. Domain ownership is NOT factual verification.

JSON output is designed for review, not as a gate: unverified inventory rows must
remain visible while upstream fixture sources and narrative facts are investigated.
"""
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'survey'
# Deliberately narrow allowlist: a familiar sports news site is not a governing body.
OFFICIAL_HOSTS = {
    'icc-cricket.com', 'nba.com', 'nhl.com', 'nhlstats.nhl.com',
    'mlb.com', 'atptour.com', 'wtatennis.com', 'itftennis.com',
    'worldsnooker.com', 'wst.tv', 'pdc.tv', 'lnr.fr', 'top14.lnr.fr',
    'unitedrugby.com', 'thepwr.com', 'gaa.ie', 'fiba.basketball',
}


def host(url):
    try:
        parsed = urlparse(url or '')
        return (parsed.hostname or '').lower() if parsed.scheme == 'https' else ''
    except ValueError:
        return ''


def classify(url):
    domain = host(url)
    if not domain:
        return 'missing_or_invalid'
    if domain == 'olbg.com' or domain.endswith('.olbg.com'):
        return 'olbg_provenance_only'
    if domain in OFFICIAL_HOSTS or any(domain.endswith('.' + d) for d in OFFICIAL_HOSTS):
        return 'official_domain_candidate'
    return 'not_allowlisted'


def audit(data=DATA):
    events = []
    for path in sorted((data / 'events').glob('*.json')):
        for item in json.loads(path.read_text()):
            # OLBG establishes what OLBG listed, not that the fixture is real.
            official = item.get('official_fixture_source')
            events.append({'sport': path.stem, 'match': item['match'],
                           'listing_source_class': classify(item.get('source_url')),
                           'official_fixture_source': official,
                           'fixture_source_class': classify(official)})
    facts = []
    for prediction in json.loads((data / 'predictions.json').read_text()):
        for label, url in prediction.get('facts_used', []):
            facts.append({'prediction': prediction['id'], 'fact': label,
                          'url': url, 'class': classify(url)})
    return {'note': 'A domain candidate is not independently verified page content. '
                    'Blank official fixture sources are unverified; OLBG is listing provenance only.',
            'inventory_count': len(events),
            'fixture_source_classes': dict(sorted(Counter(e['fixture_source_class'] for e in events).items())),
            'facts_count': len(facts),
            'fact_source_classes': dict(sorted(Counter(f['class'] for f in facts).items())),
            'events_needing_official_fixture_source': [e for e in events if e['fixture_source_class'] != 'official_domain_candidate'],
            'facts_needing_official_source_review': [f for f in facts if f['class'] != 'official_domain_candidate']}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
