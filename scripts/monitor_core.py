"""Evidence-first monitor. No historical desk is an input to this pipeline."""
from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, parse_qs

SPORTS = [
    ('golf', 'Golf', [('Golf', 5)], 'https://www.pgatour.com/schedule'),
    ('volleyball', 'Volleyball', [('Volleyball', 21)], 'https://en.volleyballworld.com/volleyball/competitions/superlega/2026-2027/schedule/'),
    ('rugby-union', 'Rugby Union', [('Rugby_Union', 9)], 'https://www.unitedrugby.com/match-centre'),
    ('cricket', 'Cricket', [('Cricket', 7)], 'https://www.icc-cricket.com/match-list'),
    ('snooker', 'Snooker', [('Snooker', 8)], 'https://www.wst.tv/matches/'),
    ('darts', 'Darts', [('Darts', 15)], 'https://www.pdc.tv/calendar/'),
    ('baseball', 'Baseball', [('Baseball', 12)], 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}'),
    ('gaelic-sports', 'Gaelic Sports', [('Gaelic_Football', 25), ('Hurling', 26)], 'https://www.gaa.ie/fixtures-results'),
    ('greyhounds', 'Greyhounds', [('Greyhounds', 28)], 'https://www.gbgb.org.uk/racing/'),
    ('tennis', 'Tennis', [('Tennis', 3)], 'https://www.atptour.com/en/scores/current/basel/328/daily-schedule'),
    ('motor-racing', 'Motor Racing', [('Motor_Racing', 14)], 'https://www.formula1.com/en/racing/2026'),
    ('handball', 'Handball', [('Handball', 20)], 'https://www.eurohandball.com/en/matches/'),
    ('ice-hockey', 'Ice Hockey', [('Ice_Hockey', 13)], 'https://api-web.nhle.com/v1/score/{date}'),
    ('basketball', 'Basketball', [('Basketball', 4)], 'https://www.nba.com/games?date={date}'),
    ('rugby-league', 'Rugby League', [('Rugby_League', 10)], 'https://www.nrl.com/draw/'),
]
SPORT_MAP = {s[0]: s for s in SPORTS}
MAX_AGE_HOURS = 6

def stamp(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('A timezone is required')
    return d.astimezone(timezone.utc)

def fresh(captured_at, now):
    age = stamp(now) - stamp(captured_at)
    return timedelta(0) <= age <= timedelta(hours=MAX_AGE_HOURS)

def american(p):
    if not math.isfinite(p) or not 0 < p < 1:
        raise ValueError('Probability must lie strictly between zero and one')
    return -100*p/(1-p) if p > .5 else 100*(1-p)/p

def implied(price):
    if not math.isfinite(price) or -100 < price < 100:
        raise ValueError('American odds must be <= -100 or >= +100')
    return -price/(-price+100) if price < 0 else 100/(price+100)

def in_price_band(price):
    return price is not None and math.isfinite(price) and ( -250 <= price <= -100 or 100 <= price <= 10000 )

def log5(home_w, home_l, away_w, away_l):
    """Independent descriptive baseline; not an official value or calibrated forecast."""
    vals = [home_w, home_l, away_w, away_l]
    if any(type(x) is not int or x <= 0 for x in vals):
        raise ValueError('Positive, observed win/loss counts required')
    h, a = home_w/(home_w+home_l), away_w/(away_w+away_l)
    return (h-h*a)/(h+a-2*h*a)

def confidence(probability, calibrated=False):
    if probability is None:
        return None
    if not 0 < probability < 1 or not math.isfinite(probability):
        raise ValueError('Invalid probability')
    # A strong numeric output from an untested formula is not strong evidence.
    if not calibrated:
        return 'low'
    return 'high' if probability >= .70 else 'medium' if probability >= .60 else 'low'

def qualifies(row, now):
    """Observed bookmaker odds and fair odds are deliberately different fields."""
    p = row.get('probability')
    return bool(p is not None and 0 < p < 1 and p >= .70
                and row.get('confidence') == 'high' and row.get('calibrated') is True
                and row.get('fixture_status') == 'confirmed'
                and row.get('olbg_status') == 'matched'
                and row.get('status') == 'scheduled'
                and row.get('start_utc') and stamp(row['start_utc']) > stamp(now)
                and fresh(row['captured_at'], now)
                and row.get('market_price_source')
                and row.get('market_price_at') and fresh(row['market_price_at'], now)
                and in_price_band(row.get('market_price')))

def top_five(rows, now, today=False):
    """Up to five DISTINCT events per sport; never pad a quota or count markets as matches."""
    result = {s[0]: [] for s in SPORTS}
    ranked = sorted((r for r in rows if qualifies(r, now)), key=lambda r: (-r['probability'], r['start_utc'], r['id']))
    seen = set()
    for row in ranked:
        if today and stamp(row['start_utc']).date() != stamp(now).date():
            continue
        if row['id'] in seen or len(result[row['sport']]) == 5:
            continue
        result[row['sport']].append(row)
        seen.add(row['id'])
    return result

class OLBGLinks(HTMLParser):
    """Public event links only. No percentages interpreted as probabilities or odds."""
    def __init__(self, sport, base):
        super().__init__()
        self.sport, self.base, self.events, self._anchor = sport, base, {}, None
        self.allowed = {str(n) for _, n in SPORT_MAP[sport][2]}
        self.pages = set()
    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        a = dict(attrs); url = urljoin(self.base, a.get('href', ''))
        u = urlsplit(url)
        if u.scheme != 'https' or u.hostname not in ('www.olbg.com', 'olbg.com'):
            return
        if u.path.rstrip('/').split('/')[-1] not in self.allowed:
            return
        ids = parse_qs(u.query).get('event_id', [])
        if len(ids) == 1 and ids[0].isdigit():
            self._anchor = (ids[0], url, [])
        elif 'next' in a.get('rel', '').split():
            self.pages.add(url)
    def handle_data(self, text):
        if self._anchor:
            self._anchor[2].append(text)
    def handle_endtag(self, tag):
        if tag == 'a' and self._anchor:
            event_id, url, text = self._anchor
            self.events.setdefault(event_id, {'olbg_id': event_id, 'sport': self.sport, 'olbg_url': url, 'label': ' '.join(' '.join(text).split()), 'fixture_status': 'unverified', 'start_utc': None, 'probability': None, 'market_price': None})
            self._anchor = None

def parse_mlb(payload, source_id, captured_at):
    if not isinstance(payload.get('dates'), list) or 'totalGames' not in payload:
        raise ValueError('Unrecognized MLB schedule response')
    rows = []
    for date in payload['dates']:
        for g in date.get('games', []):
            if g['status'].get('abstractGameState') != 'Preview' or g['status'].get('startTimeTBD'):
                continue
            if not g.get('gameDate') or g['status'].get('detailedState') != 'Scheduled':
                continue
            if stamp(g['gameDate']) <= stamp(captured_at):
                continue
            teams = g['teams']
            rows.append({'id': f"mlb-{g['gamePk']}", 'sport': 'baseball',
                         'name': f"{teams['away']['team']['name']} @ {teams['home']['team']['name']}",
                         'date': g['officialDate'], 'display_time': g['gameDate'], 'start_utc': g['gameDate'],
                         'status': 'scheduled', 'fixture_status': 'confirmed', 'source_id': source_id,
                         'official_url': f"https://statsapi.mlb.com/api/v1.1/game/{g['gamePk']}/feed/live",
                         'captured_at': captured_at, 'olbg_url': None, 'olbg_status': 'unverified',
                         'probability': None, 'confidence': None, 'fair_american': None, 'market_price': None,
                         'injuries': None, 'prediction': None, 'calibrated': False,
                         'note': 'Official schedule only. OLBG event identity, odds, inputs and injuries need confirmation.'})
    return rows


def parse_nhl(payload, source_id, captured_at):
    """Parse the NHL web score schema conservatively. No odds/form inference.

    A malformed candidate fails the capture atomically, rather than making a
    partly parsed response appear to be a complete fixture list.
    """
    now = stamp(captured_at)
    if not isinstance(payload, dict) or not isinstance(payload.get('games'), list):
        raise ValueError('Unrecognized NHL score response')
    rows, seen = [], set()
    for game in payload['games']:
        if not isinstance(game, dict):
            raise ValueError('Invalid NHL game object')
        # PRE can indicate pregame; LIVE, CRIT, FINAL, OFF and unknown states
        # must never become upcoming selections.
        if game.get('gameState') not in ('FUT', 'PRE'):
            continue
        if game.get('gameScheduleState') != 'OK':
            continue
        key = game.get('id')
        if type(key) is not int or key <= 0 or key in seen:
            raise ValueError('Invalid or duplicate NHL game id')
        seen.add(key)
        start = game.get('startTimeUTC')
        if not isinstance(start, str) or not start.endswith('Z'):
            raise ValueError('Missing explicit NHL UTC start')
        if stamp(start) <= now:
            continue
        date = game.get('gameDate')
        if not isinstance(date, str):
            raise ValueError('Missing NHL official game date')
        # Validate the calendar date, but do not infer it from the UTC start.
        datetime.strptime(date, '%Y-%m-%d')
        names = []
        for side in ('awayTeam', 'homeTeam'):
            team = game.get(side)
            name = team.get('name') if isinstance(team, dict) else None
            name = name.get('default') if isinstance(name, dict) else None
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Missing NHL official team name')
            names.append(name.strip())
        rows.append(dict(
            id=f'nhl-{key}', sport='ice-hockey', name=f'{names[0]} @ {names[1]}',
            date=date, display_time=start, start_utc=start, status='scheduled',
            fixture_status='confirmed', source_id=source_id,
            official_url=f'https://www.nhl.com/gamecenter/{key}',
            captured_at=captured_at, olbg_url=None, olbg_status='unverified',
            probability=None, confidence=None, fair_american=None,
            market_price=None, injuries=None, prediction=None, calibrated=False,
            note='Official schedule only. OLBG identity, offered odds, form and injuries remain unconfirmed.'
        ))
    return rows
