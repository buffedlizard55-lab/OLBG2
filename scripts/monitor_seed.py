"""Reproduce this session's selected field transcriptions, NOT simulated raw HTTP captures.
Source pages were read with the agent fetch_page tool on 2026-10-23 16:16–16:19 UTC.
Excerpts are deliberately labelled selected extracts; original response bytes unavailable.
"""
import hashlib
import json
from pathlib import Path
from monitor_core import SPORTS, log5, american

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/monitor'
AT = '2026-10-23T16:19:00Z'
SOURCES, EVENTS, DISCOVERY = [], [], []

def source(key, sport, url, status, excerpt, note='', kind='official'):
    SOURCES.append(dict(id=key, sport=sport, url=url, status=status, kind=kind,
                        captured_at=AT, method='agent fetch_page; selected field transcription',
                        excerpt=excerpt, note=note,
                        sha256=hashlib.sha256(excerpt.encode()).hexdigest()))
    return key

def event(key, sport, name, date, time, official, source_id, olbg=None, start=None, note='', status='scheduled'):
    row = dict(id=key, sport=sport, name=name, date=date, display_time=time, start_utc=start,
               official_url=official, source_id=source_id, captured_at=AT, status=status,
               fixture_status='confirmed', olbg_url=olbg, olbg_status='matched' if olbg else 'unverified',
               probability=None, confidence=None, fair_american=None, market_price=None,
               market_price_source=None, market_price_at=None, injuries=None, recent_history=None,
               prediction=None, calibrated=False, note=note)
    EVENTS.append(row)
    return row

# Each one of these OLBG hubs was actually read in this session. This is a partial capture,
# never an assertion that Load More Tips was exhausted or all event pages were inspected.
observations = {
 'golf': ('No tips found.', 'No event listing in the returned hub. This does not prove that no tournament or market exists.'),
 'volleyball': ('VOLLEY GOATS Mitteldeutschland vs Netzhoppers KW; Today 13:30; Win Match. SG Sokol-Post W vs TSV Hartberg W; Set Score.', 'Only selected hub fields captured; official schedule request failed.'),
 'rugby-union': ('Connacht v Zebre Parma; Today 14:45; To Win. Edinburgh v Lions; Today 14:45. Cardiff v Sharks; Today 14:45.', 'Official URC page also uses a local clock without a named zone. Do not convert to UTC.'),
 'cricket': ('Tasmania vs Victoria One Day Match; Today 19:30; Win Match. New Zealand vs India 2nd T20 Match; Tomorrow 03:00.', 'ICC endpoints returned a page-not-found body; no match facts promoted.'),
 'snooker': ('Jak Jones v Scott Donaldson; Today 14:05; Win Match. David Gilbert v Mark Williams; Today 14:05; Win Match.', 'WST lists 14:00 without a named zone in captured text; no UTC kick-off inferred.'),
 'darts': ('Jonny Clayton vs Niko Springer; Today 14:45; Win Match 2-way; 26/31 Win Tips; 84%.', 'Tip share is not a probability of winning. PDC event route is a soft 404.'),
 'baseball': ('TB Rays @ MIL Brewers; Today 20:00; Money Line; 25/31 Win Tips; 81%.', 'Matches the official participant pair. OLBG relative-date timezone is not certified.'),
 'gaelic-sports': ('St Finbarrs v Nemo Rangers; 25 Oct 12:00; Nemo Rangers +1.50. Ballyhale Shamrocks v Tullaroan; 25 Oct 09:45; Handicap.', 'Gaelic Football and Hurling belong to one requested Gaelic Sports category. County fixtures not confirmed by national GAA page.'),
 'greyhounds': ('5:12 Towcester; Today 12:12; Choices Jean; Daily Races; Expired.', 'Expired listings occur alongside other entries; never assume all hub rows are upcoming.'),
 'tennis': ('Arthur Fils vs Alex Michelsen; Today 12:30; Win Match. Ann Li vs Ashlyn Krueger; Today 23:00; Total Games; Over 22.50.', 'ATP Basel says no daily schedule; do not reuse older Basel fixtures as current.'),
 'motor-racing': ('USA Grand Prix; 25 Oct 16:00; Win Race; Max Verstappen; 13/38 Win Tips; 34%.', 'Official F1 schedule supports the race date. Complete entry list and performance inputs not captured.'),
 'handball': ('Pays dAix UC vs Toulouse; Today 14:00; Money Line. GRK Ohrid vs Spor Toto SK; Match Handicap; Spor Toto SK +11.50.', 'EHF routes returned page-not-found bodies; exact domestic fixtures not confirmed.'),
 'ice-hockey': ('MTL Canadiens @ CHI Blackhawks; Today 20:07; Money Line. K Espoo vs HIFK; Game Totals; Over 5.50.', 'NHL date-specific score and schedule endpoints returned 404 bodies to fetch_page.'),
 'basketball': ('CHI Bulls @ MIL Bucks; Today 16:10; Money Line. NY Knicks @ BOS Celtics; Pointspread; BOS Celtics -2.50.', 'NBA official times are ten minutes earlier than corresponding OLBG labels when read as ET. OLBG zone remains unknown.'),
 'rugby-league': ('State of Origin 2027; 27 May 2027 06:00; Win Tournament. Super League 2027; 02 Oct 2027 13:00; Grand Final Winner. NRL 2027; 03 Oct 2027 04:30.', 'World Cup fixtures were on NRL but were not observed in this OLBG hub capture. Do not assert OLBG coverage.'),
}
for slug, name, hubs, official in SPORTS:
    for path, num in hubs:
        text, note = observations[slug]
        if num == 25:
            text = 'St Finbarrs v Nemo Rangers; 25 Oct 12:00; Nemo Rangers +1.50.'
        elif num == 26:
            text = 'Ballyhale Shamrocks v Tullaroan; 25 Oct 09:45; Handicap; Tullaroan +3.50.'
        source('olbg-'+str(num), slug, f'https://www.olbg.com/betting-tips/{path}/{num}', 'read-partial', text, note, 'olbg')

source('taxonomy', 'all', 'https://www.olbg.com/sitemap-betting-tips.xml', 'read-partial',
       'Observed hub IDs: Tennis 3; Golf 5; Rugby_League 10; Rugby_Union 9; Cricket 7; Basketball 4; Baseball 12; Darts 15; Snooker 8; Ice_Hockey 13; Motor_Racing 14; Handball 20; Volleyball 21; Greyhounds 28; Gaelic_Football 25. Hurling 26 read separately.',
       'URL grammar is a discovery aid, not proof of schedule completeness.', 'olbg')
source('golf-official', 'golf', 'https://www.pgatour.com/schedule', 'read-partial',
       'Schedule; Season 2026. JAN 15 - 18 Sony Open in Hawaii. JAN 22 - 25 The American Express.', 'Only the first returned chunk read; no current event promoted.')
source('volleyball-official', 'volleyball', SPORTS[1][3], 'fetch-failed', 'Failed to fetch page', 'No fixture confirmed. This endpoint is only one competition, not all volleyball.')
source('cricket-official', 'cricket', 'https://www.icc-cricket.com/match-list', 'soft-404', '404; Oops: Page not found', 'Also tried /matches with the same result. No negative claim about actual fixtures.')
source('darts-official', 'darts', 'https://www.pdc.tv/tournament/european-championship-1', 'soft-404', '404; Sorry, it looks like the page you are looking for isn’t available right now.', 'Cookie text precedes the error; HTTP/tool success is not evidence success.')
source('darts-calendar', 'darts', 'https://www.pdc.tv/calendar/', 'read-no-fixtures', '2026/2027; Premier, World Series, Pro Tour; Clear; Jan ... Dec', 'Calendar controls, no match pairings in returned final chunk.')
source('greyhounds-official', 'greyhounds', 'https://www.gbgb.org.uk/racing/', 'read-no-fixtures', 'Latest Results; Search results; Track; Class; Distance; Date; Time; Winner', 'Race-card URL returned 404. Racing page yielded controls, not a full card with runners.')
source('tennis-official', 'tennis', 'https://www.atptour.com/en/scores/current/basel/328/daily-schedule', 'read-no-fixtures', 'There Is Currently No Daily Schedule. Please check back later for the daily tournament schedule.', 'Cannot substantiate the historical repository Basel quarter-finals as upcoming from this response.')
source('handball-official', 'handball', 'https://www.eurohandball.com/en/matches/', 'soft-404', 'We are sorry!Page not found', 'Also tried /en/competitions/ehf-champions-league/men/2026-27/matches/; same result.')
source('ice-hockey-official', 'ice-hockey', 'https://api.nhle.com/v1/score/2026-10-23', 'soft-404', '# 404 Not Found', 'Also tried /v1/schedule/2026-10-23; same body. Direct sandbox HTTPS failed at TLS.')

mlb_url = 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-23'
source('mlb-schedule', 'baseball', mlb_url, 'read', 'totalGames: 1; gamePk: 849805; officialDate: 2026-10-23; gameDate: 2026-10-24T00:00:00Z; detailedState: Scheduled; startTimeTBD: false; away: Tampa Bay Rays (139); home: Milwaukee Brewers (158); venue: American Family Field; description: World Series Game 1.')
mlb_event = 'https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789'
source('mlb-markets', 'baseball', mlb_event, 'read-partial', 'Money Line: MIL Brewers / TB Rays. Run Line: TB Rays +1.50 / MIL Brewers -1.50. Game Totals: Under 6.50 / Over 6.50. WIN @ contains no numeric price in returned text.', 'Actual event markets read. No bookmaker quote captured. Tipster commentary is not an official statistics source.', 'olbg')
standings_url = 'https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason&fields=records,teamRecords,team,id,name,wins,losses,runsScored,runsAllowed'
source('mlb-records', 'baseball', standings_url, 'read', 'team id 139 Rays: runsAllowed 650; runsScored 736; wins 98; losses 64. team id 158 Brewers: runsAllowed 618; runsScored 832; wins 103; losses 59.', 'All three response chunks read. Only these labelled totals transcribed. Unlabelled splitRecords were not interpreted.')
r = event('mlb-849805', 'baseball', 'Tampa Bay Rays @ Milwaukee Brewers', '2026-10-23', '2026-10-24T00:00:00Z', mlb_url, 'mlb-schedule', mlb_event, '2026-10-24T00:00:00Z', 'Official league date is October 23; UTC start falls on October 24. Experimental moneyline only; pitching, recent game history, injuries and bookmaker odds unconfirmed.')
r['inputs'] = dict(home_wins=103, home_losses=59, away_wins=98, away_losses=64, source_id='mlb-records')
r['selection'] = 'Milwaukee Brewers to win'
r['other_selection'] = 'Tampa Bay Rays to win'
r['observed_markets'] = [{'name':'Run Line','line':'±1.50','source_id':'mlb-markets'}, {'name':'Game Totals','line':'6.50','source_id':'mlb-markets'}]
r['probability'] = log5(103, 59, 98, 64)
r['confidence'] = 'low'
r['fair_american'] = american(r['probability'])
r['prediction'] = 'Milwaukee to win is a cautious lean, not a high-confidence recommendation. The Brewers finished the regular season 103–59, scoring 832 runs and allowing 618; Tampa Bay went 98–64 with 736 scored and 650 allowed. Those season totals give Milwaukee a modest statistical advantage, but they do not establish tonight’s pitching matchup, recent postseason form or player availability.'
r['prediction_source_ids'] = ['mlb-records', 'mlb-schedule']

nba_data = [
 ('chi-vs-mil-0022600099','Bulls','Bucks','4:00 PM ET','20:00',536041,'CHI_Bulls_@_MIL_Bucks'),
 ('nyk-vs-bos-0022600008','Knicks','Celtics','7:00 PM ET','23:00',534842,'NY_Knicks_@_BOS_Celtics'),
 ('tor-vs-was-0022600097','Raptors','Wizards','7:00 PM ET','23:00',536034,'TOR_Raptors_@_WAS_Wizards'),
 ('atl-vs-cha-0022600094','Hawks','Hornets','7:00 PM ET','23:00',536035,'ATL_Hawks_@_CHA_Hornets'),
 ('min-vs-orl-0022600096','Timberwolves','Magic','7:00 PM ET','23:00',536036,'MIN_Timberwolves_@_ORL_Magic'),
 ('dal-vs-ind-0022600095','Mavericks','Pacers','7:00 PM ET','23:00',536037,'DAL_Mavericks_@_IND_Pacers'),
 ('det-vs-mia-0022600098','Pistons','Heat','8:00 PM ET','00:00',536038,'DET_Pistons_@_MIA_Heat'),
 ('hou-vs-sas-0022600009','Rockets','Spurs','9:30 PM ET','01:30',534841,'HOU_Rockets_@_SA_Spurs'),
 ('nop-vs-uta-0022600100','Pelicans','Jazz','9:30 PM ET','01:30',536040,'NO_Pelicans_@_UTA_Jazz'),
 ('mem-vs-gsw-0022600101','Grizzlies','Warriors','10:00 PM ET','02:00',536039,'MEM_Grizzlies_@_GS_Warriors'),
 ('lac-vs-lal-0022600102','Clippers','Lakers','10:00 PM ET','02:00',536042,'LA_Clippers_@_LA_Lakers'),
 ('por-vs-sac-0022600103','Trail Blazers','Kings','10:00 PM ET','02:00',536043,'POR_Trail_Blazers_@_SAC_Kings'),
]
source('nba-schedule', 'basketball', 'https://www.nba.com/games?date=2026-10-23', 'read',
       'October 23, 2026; 12 games. ' + '; '.join(f'{a} @ {h}: {t}; {key}' for key,a,h,t,_,_,_ in nba_data),
       'Both chunks read. UTC normalization uses the explicitly labelled ET and America/New_York calendar rules; it is a conversion, not a separately published UTC value.')
for key, a, h, time, utc, oid, path in nba_data:
    day = '23' if int(utc[:2]) >= 20 else '24'
    event('nba-'+key.split('-')[-1], 'basketball', f'{a} @ {h}', '2026-10-23', time,
          'https://www.nba.com/game/'+key, 'nba-schedule',
          f'https://www.olbg.com/betting-tips/Basketball/NBA/NBA/{path}/4?event_id={oid}',
          f'2026-10-{day}T{utc}:00Z', 'Fixture/time confirmed from NBA list; UTC is normalized from ET. No independently supported forecasting inputs or injury report captured; lines blank.')

urc_url = 'https://stats.unitedrugby.com/match-centre/2026-27/4'
source('urc-schedule', 'rugby-union', urc_url, 'read-partial', 'All times shown are Local. ROUND 4; Friday 23 October 2026. Cardiff Rugby v Hollywoodbets Sharks 14:45, Cardiff Arms Park (292608). Connacht v Zebre Parma 14:45, Dexcom Stadium (292609). Edinburgh v 10bet Lions 14:45, Hive Stadium (292610).', 'Local zone unspecified in response. UTC deliberately blank; current pre-match state cannot be certified.')
for key, name, path, oid in [('292608','Cardiff Rugby v Hollywoodbets Sharks','Cardiff_v_Sharks',609575), ('292609','Connacht v Zebre Parma','Connacht_v_Zebre_Parma',609577), ('292610','Edinburgh v 10bet Lions','Edinburgh_v_Lions',609579)]:
    event('urc-'+key,'rugby-union',name,'2026-10-23','14:45 (Local; zone unconfirmed)',urc_url,'urc-schedule',f'https://www.olbg.com/betting-tips/Rugby_Union/All_Rugby_Union/All_Events/{path}/9?event_id={oid}',note='Date and pairing supported. Start UTC and pre-match eligibility unverified.',status='time-unverified')

source('wst-schedule','snooker','https://www.wst.tv/matches/','read-partial','BetVictor Northern Ireland Open 2026. Scheduled; Quarter Finals; Fri 23 Oct; 14:00. Match 60 Jak Jones v Scott Donaldson. Match 59 David Gilbert v Mark Williams. Completed earlier quarter-finals: Anthony McGill 1–6 Kyren Wilson; Sam Craigie 6–2 Elliot Slessor.','Chunks 0 and 2 read; no timezone named. Completed rows not promoted as picks.')
for key, name, uid, oid in [('60','Jak Jones v Scott Donaldson','3d9c9656-9688-4709-adc6-ad60dcb9fbf4',9951),('59','David Gilbert v Mark Williams','19048b0d-aaf4-4691-ad10-15b1b707f622',9950)]:
    event('wst-'+key,'snooker',name,'2026-10-23','14:00 (zone unconfirmed)','https://www.wst.tv/match-centre/'+uid,'wst-schedule',f'https://www.olbg.com/betting-tips/Snooker/All_Snooker/All_Events/{name.replace(" ","_")}/8?event_id={oid}',note='Official date/pairing; UTC time and pre-match eligibility unverified.',status='time-unverified')

source('f1-schedule','motor-racing','https://www.formula1.com/en/racing/2026/united-states','read-partial','FORMULA 1 MSC CRUISES UNITED STATES GRAND PRIX 2026. 25Oct Race16:00. My time / Track time controls. Circuit Length 5.513km; Number of Laps 56; Race Distance 308.432km.','Display timezone not pinned; time not converted. Full entry field, recent results and qualifying not captured.')
event('f1-us-2026','motor-racing','United States Grand Prix','2026-10-25','16:00 (display zone unconfirmed)','https://www.formula1.com/en/racing/2026/united-states','f1-schedule','https://www.olbg.com/betting-tips/Motor_Racing/All_Motor_Racing/All_Events/USA_Grand_Prix/14?event_id=913',note='Race date confirmed; no race-winner distribution without full field and relevant inputs.',status='time-unverified')

source('nrl-schedule','rugby-league','https://www.nrl.com/draw/?competition=131&round=2&season=2026','read-partial','2026 Rugby League World Cup; Round 2. Friday 23rd October Tonga 36–0 Lebanon Full Time. Saturday 24th October: Papua New Guinea vs Samoa (12:25am), England vs France (2:35am). Sunday 25th October: New Zealand vs Cook Islands (1:05am), Australia vs Fiji (5:05am).','Displayed clocks have no timezone; these World Cup fixtures not observed in OLBG hub capture. Completed Tonga game excluded.')
for i,(name,day,time,path) in enumerate([('Papua New Guinea vs Samoa','24','12:25am','papua-new-guinea-v-samoa'),('England vs France','24','2:35am','england-v-france'),('New Zealand vs Cook Islands','25','1:05am','new-zealand-v-cook-islands'),('Australia vs Fiji','25','5:05am','australia-v-fiji')]):
    event('rlwc-'+path,'rugby-league',name,'2026-10-'+day,time+' (zone unconfirmed)','https://www.nrl.com/draw/rugby-league-world-cup/2026/round-2/'+path+'/','nrl-schedule',note='Official-only inventory; OLBG coverage not confirmed. No winner or line inferred.',status='time-unverified')

source('gaa-schedule','gaelic-sports','https://www.gaa.ie/fixtures-results','read','2026; Saturday 24 October; Shinty-Hurling International; Ireland v Scotland; Final; 18:00; Venue: SuperValu Páirc Uí Chaoimh, Cork; Referee: Eamonn Furlong.','Does not substantiate OLBG county football or hurling pairings. Shinty-Hurling recorded as official-only, not an OLBG match.')
event('gaa-9abfb6e4','gaelic-sports','Ireland v Scotland — Shinty-Hurling International','2026-10-24','18:00 (zone unconfirmed)','https://www.gaa.ie/hurling/shinty-hurling-international/ireland-scotland/9abfb6e4-6223-44b7-8d25-57510681e49e','gaa-schedule',note='Official-only: OLBG membership, UTC and inputs unconfirmed.',status='time-unverified')

# Discovery examples retain only source-reported text, not official fixture values.
for sport, label, source_id in [
 ('volleyball','VOLLEY GOATS Mitteldeutschland vs Netzhoppers KW','olbg-21'),
 ('cricket','Tasmania vs Victoria One Day Match','olbg-7'),
 ('cricket','New Zealand vs India 2nd T20 Match','olbg-7'),
 ('darts','Jonny Clayton vs Niko Springer','olbg-15'),
 ('gaelic-sports','St Finbarrs v Nemo Rangers','olbg-25'),
 ('gaelic-sports','Ballyhale Shamrocks v Tullaroan','olbg-26'),
 ('greyhounds','5:12 Towcester (Expired in capture)','olbg-28'),
 ('tennis','Arthur Fils vs Alex Michelsen','olbg-3'),
 ('tennis','Ann Li vs Ashlyn Krueger','olbg-3'),
 ('handball','Pays dAix UC vs Toulouse','olbg-20'),
 ('ice-hockey','MTL Canadiens @ CHI Blackhawks','olbg-13'),
 ('rugby-league','State of Origin 2027 (outright, not a match)','olbg-10'),
]:
    DISCOVERY.append(dict(sport=sport,label=label,source_id=source_id,official_name=None,date=None,start_utc=None,market_price=None,confidence=None,status='unverified'))

FLAGS = [
 ('M01','Coverage is partial','All 15 categories were researched, but neither paginated OLBG inventory nor every market was exhausted. A few selected discoveries are stored, not an exhaustive event list.','https://www.olbg.com/betting-tips'),
 ('M02','No supported high-confidence recommendations','Observed bookmaker prices, calibrated forecast performance and complete match-specific inputs are missing. No high-confidence prediction is published and the 75-per-day target is unmet.','https://www.olbg.com/betting-tips'),
 ('M03','Actual odds versus fair lines','OLBG vote shares are not win probabilities. No numeric bookmaker price appeared in the captured MLB event text. Fair lines must not substitute for the requested offered-price range.','https://www.olbg.com/betting-tips/Baseball/12'),
 ('M04','Old desks are not fresh evidence','587 HTML pages existed at baseline. Many overlapping layers and hard-coded October 22 date filters remain archived. Their fixture, line and prediction counts are not added to this monitor.','https://github.com/buffedlizard55-lab/OLBG2/blob/2999cc0cbe319451b6cd2a3737952e30a4da6208/scripts/build_site.py'),
 ('M05','Coordination-board artifacts','Literal merge-separator/end-marker lines remain at baseline COORDINATION.md lines 3216, 3307, 3437, 3549, 3609 and 3628. Prior session history is preserved rather than silently deleted.','https://github.com/buffedlizard55-lab/OLBG2/blob/2999cc0cbe319451b6cd2a3737952e30a4da6208/COORDINATION.md'),
 ('M06','UTC and today are not interchangeable','MLB Game 1 has officialDate October 23 but begins October 24 00:00 UTC. Unknown-zone URC/WST/F1/NRL times are left unconverted and cannot qualify for a timed pick.','https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-23'),
 ('M07','Gaelic Sports scope corrected','This monitor includes both OLBG Gaelic Football and Hurling within Gaelic Sports. Historical desks excluded hurling and added esports/Aussie Rules; those decisions do not match the present explicit 15-category request.','https://www.olbg.com/betting-tips/Hurling/26'),
 ('M08','Automation is not complete collection','Scheduled checks can capture public pages, detect evidence failures, extract OLBG links and parse MLB schedules. Other official adapters, exhaustive pagination, odds feeds, injuries and automatic original prose remain incomplete. Failed refreshes retain the capture age, never relabel old evidence as new.','https://github.com/buffedlizard55-lab/OLBG2/actions'),
 ('M09','Pricing assumptions disclosed','Only the MLB two-way moneyline baseline is originated from sourced regular-season win/loss totals. It is uncalibrated, omits postseason form, pitchers and home advantage, and is low confidence. Handicap and total prices remain blank.','https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason'),
 ('M10','Stored extracts are not raw captures','Agent fetch_page responses were transcribed into selected field extracts with source URLs and hashes. Hashes establish local integrity only, not source authenticity. Runtime HTTP captures use a separate ledger.','https://github.com/buffedlizard55-lab/OLBG2/tree/arena/8226c94a-olbg2/data/monitor'),
]

def main():
    OUT.mkdir(exist_ok=True)
    payload = dict(schema_version=1,captured_at=AT,capture_window='2026-10-23 16:16–16:19 UTC',sources=SOURCES,events=EVENTS,discovery=DISCOVERY,
                   flags=[dict(id=k,title=t,detail=d,url=u,status='needs review') for k,t,d,u in FLAGS])
    (OUT/'seed.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(f'monitor seed: {len(EVENTS)} official fixture rows, {len(SOURCES)} source entries; partial capture')

if __name__=='__main__': main()
