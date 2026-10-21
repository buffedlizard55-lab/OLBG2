#!/usr/bin/env python3
"""Materialise the collected OLBG event inventory into data/events/<sport>.json.

Every row carries provenance:
  * source_url      - the OLBG page the row was read from (row-level provenance)
  * retrieved_via   - "live_fetch" (harness fetched the page during this session)
                      or "indexed_snapshot" (read from a dated search-index copy)
  * as_of           - the date the underlying page content is dated
Rows are never merged across retrievals of different ages.
"""
import json, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "survey" / "events"
OUT.mkdir(parents=True, exist_ok=True)

LIVE = "live_fetch"
SNAP = "indexed_snapshot"

# ---------------------------------------------------------------------------
# Sport registry. OLBG sport ids come from https://www.olbg.com/sitemap-betting-tips.xml
# (retrieved live 2026-10-21). include/exclude follows the project brief.
# ---------------------------------------------------------------------------
SPORTS = [
    # id, slug, name, include, note
    (1,  "Football",         "Football (soccer)",        False, "Excluded by brief: 'soccer', 'football'."),
    (2,  "Horse_Racing",     "Horse Racing",             False, "Excluded by brief: 'horse racing'."),
    (3,  "Tennis",           "Tennis",                   True,  ""),
    (4,  "Basketball",       "Basketball",               True,  ""),
    (5,  "Golf",             "Golf",                     True,  "Outright tournaments only; no head-to-head match market listed."),
    (7,  "Cricket",          "Cricket",                  True,  ""),
    (8,  "Snooker",          "Snooker",                  True,  ""),
    (9,  "Rugby_Union",      "Rugby Union",              True,  ""),
    (10, "Rugby_League",     "Rugby League",             True,  ""),
    (11, "American_Football","American Football",        False, "Excluded by brief: 'american football'."),
    (12, "Baseball",         "Baseball",                 True,  ""),
    (13, "Ice_Hockey",       "Ice Hockey",               True,  ""),
    (14, "Motor_Racing",     "Motor Racing",             True,  "Included: brief excludes 'cycling', not motorsport. See flag F-04."),
    (15, "Darts",            "Darts",                    True,  ""),
    (16, "Boxing",           "Boxing",                   False, "Excluded by brief: 'boxing'. OLBG has no separate UFC/MMA node. See F-05."),
    (17, "Cycling",          "Cycling",                  False, "Excluded by brief: 'cycling'."),
    (20, "Handball",         "Handball",                 True,  ""),
    (21, "Volleyball",       "Volleyball",               True,  ""),
    (22, "Aussie_Rules",     "Aussie Rules",             True,  "No /betting-tips node in OLBG sitemap; no upcoming events listed."),
    (23, "eSports",          "eSports",                  True,  "No /betting-tips node in OLBG sitemap; no upcoming events listed."),
    (25, "Gaelic_Football",  "Gaelic Football",          False, "Football code; excluded under brief's 'football'. Ambiguous - see flag F-03."),
    (28, "Greyhounds",       "Greyhounds",               False, "Racing family; excluded alongside 'horse racing'. Ambiguous - see flag F-03."),
]

T = "https://www.olbg.com/betting-tips"

def ev(match, comp, when, market, sel, tips, pct, eid, slug, sport_id, via, as_of, extra=None):
    d = dict(match=match, competition=comp, listed_time=when, market=market,
             top_selection=sel, tips_for=split(tips)[0], tips_total=split(tips)[1],
             tip_pct=pct, event_id=eid,
             source_url=f"{T}/{slug}/{sport_id}?event_id={eid}",
             retrieved_via=via, as_of=as_of)
    if extra:
        d.update(extra)
    return d

def split(t):
    if not t:
        return (None, None)
    a, b = t.split("/")
    return (int(a), int(b))

DATA = {}

# --- TENNIS (live fetch of /betting-tips/Tennis/3 on 2026-10-21) -----------
ten = [
 ("Leylah Fernandez vs Aliaksandra Sasnovich","Today 02:30","Win Match","Leylah Fernandez","6/7",86,902039,"Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Aliaksandra_Sasnovich"),
 ("Katie Boulter vs Viktorija Golubic","Today 01:30","Win Match","Katie Boulter","5/8",63,902065,"Tennis/All_Tennis/All_Events/Katie_Boulter_vs_Viktorija_Golubic"),
 ("James Duckworth vs Luciano Darderi","Today 02:30","Win Match","Luciano Darderi","4/5",80,902038,"Tennis/All_Tennis/All_Events/James_Duckworth_vs_Luciano_Darderi"),
 ("Adrian Mannarino vs Andrey Rublev","Today 05:30","Win Match","Andrey Rublev","4/5",80,902037,"Tennis/All_Tennis/All_Events/Adrian_Mannarino_vs_Andrey_Rublev"),
 ("Sorana Cirstea vs Sara Bejlek","Today 04:00","Win Match","Sara Bejlek","3/6",50,902074,"Tennis/All_Tennis/All_Events/Sorana_Cirstea_vs_Sara_Bejlek"),
 ("Zangar Nurlanuly vs Tomas Machac","Today 04:00","1st Set Winner","Zangar Nurlanuly","3/4",75,901935,"Tennis/All_Tennis/All_Events/Zangar_Nurlanuly_vs_Tomas_Machac"),
 ("Mattia Bellucci vs Tomas Martin Etcheverry","Today 02:30","Set Betting","Tomas Martin Etcheverry to win 2-1","2/3",67,901993,"Tennis/All_Tennis/All_Events/Mattia_Bellucci_vs_Tomas_Martin_Etcheverry"),
 ("Dino Prizmic vs Damir Dzumhur","Today 05:30","Win Match","Damir Dzumhur","2/2",100,901896,"Tennis/All_Tennis/All_Events/Dino_Prizmic_vs_Damir_Dzumhur"),
 ("Stan Wawrinka vs Martin Landaluce","Today 08:00","Win Match","Stan Wawrinka","2/2",100,901974,"Tennis/All_Tennis/All_Events/Stan_Wawrinka_vs_Martin_Landaluce"),
 ("David Goffin vs Remy Bertola","Today 12:00","Win Match","David Goffin","2/2",100,902028,"Tennis/All_Tennis/All_Events/David_Goffin_vs_Remy_Bertola"),
 ("Facundo Diaz Acosta vs Nikoloz Basilashvili","Today 04:00","Set Betting","Nikoloz Basilashvili to win 2-1","1/2",50,902040,"Tennis/All_Tennis/All_Events/Facundo_Diaz_Acosta_vs_Nikoloz_Basilashvili"),
 ("Martin Damm vs Francisco Cerundolo","Today 05:30","Set Betting","Francisco Cerundolo to win 2-1","1/1",100,902048,"Tennis/All_Tennis/All_Events/Martin_Damm_vs_Francisco_Cerundolo"),
 ("Mariano Navone vs Tallon Griekspoor","Today 07:00","Win Match","Tallon Griekspoor","1/1",100,902085,"Tennis/All_Tennis/All_Events/Mariano_Navone_vs_Tallon_Griekspoor"),
 ("Ekaterina Alexandrova vs Marta Kostyuk","Today 07:00","Win Match","Marta Kostyuk",None,None,902084,"Tennis/All_Tennis/All_Events/Ekaterina_Alexandrova_vs_Marta_Kostyuk"),
]
DATA["tennis"] = [ev(m,None,w,mk,s,t,p,e,sl,3,LIVE,"2026-10-21") for (m,w,mk,s,t,p,e,sl) in ten]

# --- CRICKET (live fetch of /betting-tips/Cricket/7 on 2026-10-21) ----------
cri = [
 ("Afghanistan vs Bangladesh One Day Match","Today 07:30","Win Match","Afghanistan","7/7",100,188824,"Cricket/All_Cricket/All_Events/Afghanistan_vs_Bangladesh_One_Day_Match"),
 ("Northern Cape Heat vs Garden Route Badgers T20","Today 07:00","Win Match","Garden Route Badgers","5/8",63,188823,"Cricket/All_Cricket/All_Events/Northern_Cape_Heat_vs_Garden_Route_Badgers_T20"),
 ("North West Dragons vs Limpopo Impalas T20","Today 12:00","Win Match","North West Dragons","5/6",83,188810,"Cricket/All_Cricket/All_Events/North_West_Dragons_vs_Limpopo_Impalas_T20"),
 ("New Zealand vs India 1st T20 Match","Tomorrow 03:00","Win Match","India","5/7",71,188814,"Cricket/All_Cricket/All_Events/New_Zealand_vs_India_1st_T20_Match"),
 ("Eastern Storm vs Tuskers T20","Tomorrow 12:00","Win Match","Eastern Storm","4/4",100,188811,"Cricket/All_Cricket/All_Events/Eastern_Storm_vs_Tuskers_T20"),
 ("Namibia vs Ireland 1st ODI","Tomorrow 04:00","Win Match","Ireland","3/3",100,188828,"Cricket/All_Cricket/All_Events/Namibia_vs_Ireland_1st_ODI"),
 ("England vs Sri Lanka One Day Match","Tomorrow 04:00","Win Match","England","1/2",50,188829,"Cricket/All_Cricket/All_Events/England_vs_Sri_Lanka_One_Day_Match"),
 ("Australia W vs New Zealand W 3rd T20 Match","Tomorrow 04:15","Win Match","Australia W","1/2",50,188826,"Cricket/All_Cricket/All_Events/Australia_W_vs_New_Zealand_W_3rd_T20_Match"),
 ("Mpumalanga Rhinos vs South Africa Emerging T20","Tomorrow 07:00","Win Match","South Africa Emerging","1/2",50,188825,"Cricket/All_Cricket/All_Events/Mpumalanga_Rhinos_vs_South_Africa_Emerging_T20"),
]
cri_out = [
 ("World Cup 2027","21 Nov 2027 05:00","Outright Winner","India","6/12",50,182606,"Cricket/All_Cricket/All_Events/World_Cup_2027"),
 ("Big Bash Women 2026","05 Dec 03:10","Outright Winner","Sydney Sixers W","2/3",67,187184,"Cricket/All_Cricket/All_Events/Big_Bash_Women_2026"),
 ("T20 Big Bash 2026-27","12 Dec 03:15","Outright Winner","Adelaide Strikers","1/2",50,187503,"Cricket/All_Cricket/All_Events/T20_Big_Bash_2026-27"),
 ("SA20 2026-27","24 Jan 2027 11:30","Outright Winner","Pretoria Capitals","1/1",100,187504,"Cricket/All_Cricket/All_Events/SA20_2026-27"),
 ("T20 Blast 2027","18 Jul 2027 11:00","Outright Winner",None,None,None,188350,"Cricket/All_Cricket/All_Events/T20_Blast_2027"),
]
DATA["cricket"] = [ev(m,None,w,mk,s,t,p,e,sl,7,LIVE,"2026-10-21",{"outright":False}) for (m,w,mk,s,t,p,e,sl) in cri]
DATA["cricket"] += [ev(m,None,w,mk,s,t,p,e,sl,7,LIVE,"2026-10-21",{"outright":True}) for (m,w,mk,s,t,p,e,sl) in cri_out]

# --- SNOOKER (live fetch of /betting-tips/Snooker/8 on 2026-10-21) ----------
snk = [
 ("Cheung Ka Wai v Stuart Bingham","Today 05:00","Win Match","Cheung Ka Wai","8/11",73,9933,"Snooker/All_Snooker/All_Events/Cheung_Ka_Wai_v_Stuart_Bingham"),
 ("Pang Junxu v Liam Davies","Today 05:00","Win Match","Pang Junxu","6/9",67,9929,"Snooker/All_Snooker/All_Events/Pang_Junxu_v_Liam_Davies"),
 ("Elliot Slessor v Jamie Jones","Today 15:00","Win Match","Jamie Jones","4/4",100,9931,"Snooker/All_Snooker/All_Events/Elliot_Slessor_v_Jamie_Jones"),
 ("Luca Brecel v Martin O Donnell","Today 15:00","Win Match","Martin O Donnell","4/5",80,9932,"Snooker/All_Snooker/All_Events/Luca_Brecel_v_Martin_O_Donnell"),
 ("John Higgins v Jak Jones","Today 08:00","Win Match","John Higgins","3/6",50,9934,"Snooker/All_Snooker/All_Events/John_Higgins_v_Jak_Jones"),
 ("Sam Craigie v Xu Si","Today 09:00","Win Match","Sam Craigie","3/3",100,9930,"Snooker/All_Snooker/All_Events/Sam_Craigie_v_Xu_Si"),
]
DATA["snooker"] = [ev(m,None,w,mk,s,t,p,e,sl,8,LIVE,"2026-10-21") for (m,w,mk,s,t,p,e,sl) in snk]

# --- GOLF (live fetch of /betting-tips/Golf/5 on 2026-10-21) ----------------
gol = [
 ("Genesis Championship","25 Oct 04:00","Win Tournament","Si Woo Kim","5/18",28,101905,"Golf/All_Golf/All_Events/Genesis_Championship"),
 ("Bermuda Championship","25 Oct 17:45","Win Tournament","Ben James","3/12",25,101904,"Golf/All_Golf/All_Events/Bermuda_Championship"),
 ("Players Series SA","25 Oct 02:45","Win Tournament","Josh Armstrong","2/2",100,101907,"Golf/All_Golf/All_Events/Players_Series_SA"),
 ("BMW Ladies Championship","25 Oct 04:00","Win Tournament","Sei Young Kim","2/8",25,101906,"Golf/All_Golf/All_Events/BMW_Ladies_Championship"),
 ("Stifel Charity Classic","25 Oct 17:45","Win Tournament","Steven Alker","2/7",29,101903,"Golf/All_Golf/All_Events/Stifel_Charity_Classic"),
 ("Senior Italian Open","24 Oct 11:45","Win Tournament","Mikael Lundberg","1/2",50,101911,"Golf/All_Golf/All_Events/Senior_Italian_Open"),
 ("Fortinet Players Cup","25 Oct 02:45","Win Tournament","Ryosuke Kinoshita","1/2",50,101908,"Golf/All_Golf/All_Events/Fortinet_Players_Cup"),
 ("Hong Kong Open","25 Oct 03:45","Win Tournament","Paul Casey","1/3",33,101910,"Golf/All_Golf/All_Events/Hong_Kong_Open"),
 ("Stella Artois Players Championship","25 Oct 10:45","Win Tournament","Daniel van Tonder","1/2",50,101912,"Golf/All_Golf/All_Events/Stella_Artois_Players_Championship"),
 ("Hero Womens Indian Open","25 Oct 08:00","Win Tournament","Avani Prashanth",None,None,101909,"Golf/All_Golf/All_Events/Hero_Womens_Indian_Open"),
]
DATA["golf"] = [ev(m,None,w,mk,s,t,p,e,sl,5,LIVE,"2026-10-21",{"outright":True}) for (m,w,mk,s,t,p,e,sl) in gol]

# --- BASKETBALL (live fetch of /betting-tips/Basketball/4 on 2026-10-21) ----
bkb = [
 ("MIL Bucks @ WAS Wizards","NBA","Today 19:10","Money Line","WAS Wizards","9/11",82,534889,"Basketball/NBA/NBA/MIL_Bucks_@_WAS_Wizards"),
 ("Hapoel Tel Aviv vs Virtus Bologna","Euroleague","Today 12:00","Money Line","Hapoel Tel Aviv","5/8",63,535919,"Basketball/European/Euroleague/Hapoel_Tel_Aviv_vs_Virtus_Bologna"),
 ("Seoul Thunders vs KCC Egis","Korea KBL","Today 06:00","Money Line","Seoul Thunders","3/5",60,535966,"Basketball/Other/Korea_KBL/Seoul_Thunders_vs_KCC_Egis"),
 ("ATL Hawks @ ORL Magic","NBA","Today 19:10","Money Line","ATL Hawks","3/5",60,534888,"Basketball/NBA/NBA/ATL_Hawks_@_ORL_Magic"),
 ("CHI Bulls @ TOR Raptors","NBA","Today 19:40","Money Line","TOR Raptors","3/4",75,535673,"Basketball/NBA/NBA/CHI_Bulls_@_TOR_Raptors"),
 ("PAOK vs Ratiopharm Ulm","Euro Cup","Today 13:00","Money Line","PAOK","2/2",100,535952,"Basketball/European/Euro_Cup/PAOK_vs_Ratiopharm_Ulm"),
 ("Bosna Sarajevo vs Bahcesehir Koleji","Euro Cup","Today 13:30","Money Line","Bahcesehir Koleji","2/3",67,535950,"Basketball/European/Euro_Cup/Bosna_Sarajevo_vs_Bahcesehir_Koleji"),
 ("Hapoel Jerusalem vs Rigas Zelli","Euro Cup","Today 14:00","Money Line","Hapoel Jerusalem","2/3",67,535956,"Basketball/European/Euro_Cup/Hapoel_Jerusalem_vs_Rigas_Zelli"),
 ("IND Pacers @ NO Pelicans","NBA","Today 20:10","Money Line","NO Pelicans","2/4",50,534892,"Basketball/NBA/NBA/IND_Pacers_@_NO_Pelicans"),
 ("PHX Suns @ POR Trail Blazers","NBA","Today 22:10","Money Line","PHX Suns","2/3",67,534893,"Basketball/NBA/NBA/PHX_Suns_@_POR_Trail_Blazers"),
 ("Panathinaikos vs Baskonia","Euroleague","Tomorrow 14:15","Money Line","Panathinaikos","2/3",67,535923,"Basketball/European/Euroleague/Panathinaikos_vs_Baskonia"),
 ("DEN Nuggets @ OKC Thunder","NBA","Tomorrow 21:40","Money Line","OKC Thunder","2/2",100,534843,"Basketball/NBA/NBA/DEN_Nuggets_@_OKC_Thunder"),
 ("U BT Cluj Napoca vs London Lions","Euro Cup","Today 12:00","Money Line","London Lions","1/2",50,535949,"Basketball/European/Euro_Cup/U_BT_Cluj_Napoca_vs_London_Lions"),
 ("AEK vs Antwerp Giants","Basketball Champions League","Today 12:00","Money Line","Antwerp Giants","1/2",50,535969,"Basketball/European/Basketball_Champions_League/AEK_vs_Antwerp_Giants"),
]
DATA["basketball"] = [ev(m,c,w,mk,s,t,p,e,sl,4,LIVE,"2026-10-21") for (m,c,w,mk,s,t,p,e,sl) in bkb]

# --- Rows below come from DATED search-index snapshots, not a live fetch.
# --- They are kept separate and flagged; as_of records the snapshot date.

# Darts - snapshot of /betting-tips/Darts/15, pageAge 2026-10-20
dart = [
 ("Luke Humphries vs Ryan Searle","22 Oct 20:45","Win Match 2-way","Luke Humphries","2/3",67),
 ("Jonny Clayton vs Niko Springer","23 Oct 19:45","Win Match 2-way","Jonny Clayton","2/3",67),
 ("Luke Woodhouse vs Dirk van Duijvenbode","22 Oct 18:15","Win Match 2-way","Luke Woodhouse","1/1",100),
 ("Niels Zonneveld vs Cameron Menzies","22 Oct 19:15","Win Match 2-way","Niels Zonneveld","1/1",100),
 ("Gerwyn Price vs Rob Cross","22 Oct 19:45","Win Match 2-way","Gerwyn Price","1/2",50),
 ("James Wade vs Damon Heta","22 Oct 20:15","Win Match 2-way","James Wade","1/1",100),
 ("Gian van Veen vs Andrew Gilding","22 Oct 21:15","Win Match 2-way","Gian van Veen","1/1",100),
 ("Ross Smith vs Karel Sedlacek","22 Oct 21:45","Win Match 2-way","Ross Smith","1/2",50),
 ("Ryan Joyce vs Jermaine Wattimena","23 Oct 18:15","Win Match 2-way","Jermaine Wattimena","1/2",50),
 ("Krzysztof Ratajski vs Dave Chisnall","23 Oct 18:45","Win Match 2-way","Krzysztof Ratajski","1/2",50),
 ("Nathan Aspinall vs Cristo Reyes","23 Oct 19:15","Win Match 2-way","Nathan Aspinall","1/1",100),
 ("Luke Littler vs William OConnor","23 Oct 20:15","Win Match 2-way","William OConnor","1/2",50),
 ("Wessel Nijman vs Martin Schindler","23 Oct 20:45","Win Match 2-way","Wessel Nijman","1/2",50),
 ("Josh Rock vs Chris Dobey","23 Oct 21:45","Win Match 2-way","Chris Dobey","1/1",100),
 ("PDC World Championship 2027","03 Jan 2027 17:00","Win Tournament","Luke Littler","23/36",64),
 ("European Championship","25 Oct 18:00","Win Tournament","Luke Humphries","2/5",40),
]
DATA["darts"] = [dict(match=m, competition="European Championship" if m not in ("PDC World Championship 2027",) else "PDC World Darts Championship",
                      listed_time=w, market=mk, top_selection=s, tips_for=split(t)[0], tips_total=split(t)[1],
                      tip_pct=p, event_id=None,
                      source_url="https://www.olbg.com/betting-tips/Darts/15",
                      retrieved_via=SNAP, as_of="2026-10-20",
                      outright=(mk=="Win Tournament"),
                      stale_flag=True) for (m,w,mk,s,t,p) in dart]

# Rugby Union - snapshot of /betting-tips/Rugby_Union/9, pageAge 2026-10-20
ru = [
 ("Montauban v Oyonnax","Tomorrow 20:00","To Win","Oyonnax","4/6",67),
 ("Agen v Nissa","23 Oct 18:30","To Win","Nissa","3/4",75),
 ("Soyaux Angouleme v Dax","23 Oct 18:30","To Win","Dax","3/3",100),
 ("Connacht v Zebre Parma","23 Oct 19:45","To Win","Connacht","3/5",60),
 ("Narbonne v Brive","23 Oct 18:00","To Win","Narbonne","2/2",100),
 ("Aurillac v Nevers","23 Oct 18:30","To Win","Nevers","2/4",50),
 ("Bulls v Ulster","24 Oct 12:45","Handicap","Ulster +18.50","2/2",100),
 ("Valence Romans v Colomiers","23 Oct 18:30","To Win","Colomiers","1/1",100),
 ("Grenoble v Biarritz","23 Oct 20:00","Handicap","Biarritz +11.50","1/1",100),
 ("Provence v Beziers","23 Oct 20:00","Handicap","Beziers +28.50","1/1",100),
 ("Stormers v Scarlets","24 Oct 15:00","To Win","Stormers","1/2",50),
 ("Bayonne v Lyon","24 Oct 15:35","Handicap","Lyon +10.50","1/1",100),
 ("Toulouse v Perpignan","24 Oct 15:35","Handicap","Perpignan +23.50","1/1",100),
 ("Leinster v Munster","24 Oct 18:00","To Win","Leinster","1/1",100),
 ("La Rochelle v Bordeaux","25 Oct 20:05","To Win","La Rochelle","1/1",100),
 ("Six Nations 2027","14 Mar 2027 20:00","Win Tournament","Ireland","3/9",33),
]
DATA["rugby_union"] = [dict(match=m, competition=None, listed_time=w, market=mk, top_selection=s,
                             tips_for=split(t)[0], tips_total=split(t)[1], tip_pct=p, event_id=None,
                             source_url="https://www.olbg.com/betting-tips/Rugby_Union/9",
                             retrieved_via=SNAP, as_of="2026-10-20", outright=(mk=="Win Tournament"),
                             stale_flag=True) for (m,w,mk,s,t,p) in ru]

# Ice Hockey - snapshot of /betting-tips/Ice_Hockey/13, pageAge 2026-10-18
ih = [
 ("Adler Mannheim vs Schwenninger Wild Wings","Germany Eishockey Liga","Today 15:30","Money Line","Adler Mannheim","6/8",75),
 ("CLB Blue Jackets @ MIN Wild","NHL","Today 23:07","Money Line","MIN Wild","4/6",67),
 ("ERC Ingolstadt vs Augsburger Panther","Germany Eishockey Liga","Today 15:30","Money Line","Augsburger Panther","3/4",75),
 ("Kolner Haie vs Fischtown Pinguins Bremerhaven","Germany Eishockey Liga","Today 15:30","Money Line","Fischtown Pinguins Bremerhaven","2/3",67),
 ("HCB Sudtirol Alperia vs EHC Black Wings Linz","Austria EHL","Today 17:00","Money Line","HCB Sudtirol Alperia","2/2",100),
 ("CAR Hurricanes @ CGY Flames","NHL","Tomorrow 01:07","Money Line","CAR Hurricanes","2/3",67),
 ("Milano HC vs Fehervar AV19","Austria EHL","Today 16:00","Money Line","Fehervar AV19","1/1",100),
 ("HC TWK Innsbruck vs HK Olimpija Ljubljana","Austria EHL","Today 16:30","Game Totals","Over 5.50","1/1",100),
 ("Nurnberg Ice Tigers vs EHC Munchen","Germany Eishockey Liga","Today 18:00","Money Line","Nurnberg Ice Tigers","1/2",50),
]
DATA["ice_hockey"] = [dict(match=m, competition=c, listed_time=w, market=mk, top_selection=s,
                           tips_for=split(t)[0], tips_total=split(t)[1], tip_pct=p, event_id=None,
                           source_url="https://www.olbg.com/betting-tips/Ice_Hockey/13",
                           retrieved_via=SNAP, as_of="2026-10-18", outright=False, stale_flag=True)
                      for (m,c,w,mk,s,t,p) in ih]

# Handball - snapshot of /betting-tips/Handball/20, pageAge 2026-10-18
hb = [
 ("GOG vs KIF Kolding","Today 15:00","Money Line","GOG","7/12",58),
 ("SG Flensburg Handewitt vs Fuchse Berlin","Today 14:00","Money Line","Tie","6/12",50),
 ("SC Magdeburg vs TVB Stuttgart","Today 17:00","Money Line","SC Magdeburg","6/8",75),
 ("Podravka Vegeta W vs Nykobing FH W","Today 13:00","Money Line","Tie","5/9",56),
 ("Ribe Esbjerg HH vs Skanderborg Handbold","Today 13:30","Money Line","Tie","5/10",50),
 ("CSM Bucuresti W vs Sola W","Today 15:00","Money Line","CSM Bucuresti (W)","5/7",71),
 ("TBV Lemgo Lippe vs Frisch Auf Goppingen","Today 15:30","Money Line","TBV Lemgo Lippe","5/13",38),
 ("Bergsoy vs OIF Arendal","Today 15:30","Money Line","Tie","4/5",80),
 ("Flint Tonsberg W vs Utleira W","Today 15:00","Money Line","Tie","3/3",100),
 ("Chambery Savoie vs Pays dAix UC","Today 16:00","Money Line","Tie","3/5",60),
 ("Aalborg Handbold vs Mors Thy Handbold","Today 19:00","Money Line","Tie","3/5",60),
 ("Bjerringbro Silkeborg vs TMS Ringsted","Today 17:00","Money Line","Bjerringbro-Silkeborg","2/3",67),
 ("BM Cangas vs FC Barcelona","Today 17:15","Money Line","BM Cangas","2/2",100),
 ("Fredericia HK vs Skive FH","Today 18:00","Money Line","Fredericia HK","2/4",50),
]
DATA["handball"] = [dict(match=m, competition=None, listed_time=w, market=mk, top_selection=s,
                         tips_for=split(t)[0], tips_total=split(t)[1], tip_pct=p, event_id=None,
                         source_url="https://www.olbg.com/betting-tips/Handball/20",
                         retrieved_via=SNAP, as_of="2026-10-18", outright=False, stale_flag=True)
                    for (m,w,mk,s,t,p) in hb]

# Volleyball - snapshot of /betting-tips/Volleyball/21, pageAge 2026-10-20
vb = [
 ("SAVO Volley vs Loimu","Today 16:30","Win Match","SAVO Volley","13/17",76),
 ("Prostejov W vs VK Lvice Praha W","Today 17:00","Win Match","Prostejov W","11/15",73),
 ("Vampula W vs Arctic Volley W","Today 16:30","Win Match","Vampula W","9/10",90),
 ("St Nazaire vs Toulouse","Today 19:00","Win Match","Toulouse","9/10",90),
 ("Praia Clube W vs Pinheiros W","Tomorrow 01:00","Win Match","Praia Clube W","7/9",78),
 ("TSV Hartberg W vs VBV Trofaiach-WSV Eisenerz W","Today 16:35","Win Match","VBV Trofaiach/WSV Eisenerz W","6/9",67),
 ("TV Rottenburg vs SWD Duren","Today 17:30","Win Match","SWD Duren","6/9",67),
 ("Narbonne vs Royan","Today 18:00","Win Match","Royan","6/9",67),
 ("VCO Berlin vs FT Freiburg","Today 18:00","Win Match","FT Freiburg","6/11",55),
 ("Fluminense W vs Sancor Volei W","Today 22:30","Win Match","Fluminense W","6/8",75),
 ("AZS Olsztyn vs Norwid Czestochowa","Today 16:30","Win Match","AZS Olsztyn","5/8",63),
 ("AS Cannes vs Sete","Today 18:00","Win Match","AS Cannes","5/9",56),
]
DATA["volleyball"] = [dict(match=m, competition=None, listed_time=w, market=mk, top_selection=s,
                           tips_for=split(t)[0], tips_total=split(t)[1], tip_pct=p, event_id=None,
                           source_url="https://www.olbg.com/betting-tips/Volleyball/21",
                           retrieved_via=SNAP, as_of="2026-10-20", outright=False, stale_flag=True)
                      for (m,w,mk,s,t,p) in vb]

# Baseball - snapshot of /betting-tips/Baseball/12, pageAge 2026-10-20
DATA["baseball"] = [dict(match="TB Rays @ MIL Brewers", competition="MLB", listed_time="24 Oct 01:00",
                         market="Money Line", top_selection="TB Rays", tips_for=1, tips_total=1,
                         tip_pct=100, event_id=None,
                         source_url="https://www.olbg.com/betting-tips/Baseball/12",
                         retrieved_via=SNAP, as_of="2026-10-20", outright=False, stale_flag=True)]

# Motor Racing - snapshot of /betting-tips/Motor_Racing/14, pageAge 2026-10-18
DATA["motor_racing"] = [
 dict(match="USA Grand Prix", competition="Formula 1 World Championship (round 18)",
      listed_time="25 Oct 20:00", market="Win Race", top_selection="Max Verstappen",
      tips_for=5, tips_total=12, tip_pct=42, event_id=None,
      source_url="https://www.olbg.com/betting-tips/Motor_Racing/14",
      retrieved_via=SNAP, as_of="2026-10-18", outright=False, stale_flag=True),
 dict(match="USA Grand Prix", competition="Formula 1 World Championship (round 18)",
      listed_time="25 Oct 20:00", market="Fastest Lap", top_selection="Lando Norris",
      tips_for=4, tips_total=12, tip_pct=33, event_id=None,
      source_url="https://www.olbg.com/betting-tips/Motor_Racing/14",
      retrieved_via=SNAP, as_of="2026-10-18", outright=False, stale_flag=True),
 dict(match="Formula 1 Drivers Championship 2026", competition="Formula 1 World Championship",
      listed_time="06 Dec 13:00", market="Win Tournament", top_selection="Max Verstappen",
      tips_for=9, tips_total=33, tip_pct=27, event_id=None,
      source_url="https://www.olbg.com/betting-tips/Motor_Racing/14",
      retrieved_via=SNAP, as_of="2026-10-18", outright=True, stale_flag=True),
 dict(match="Formula 1 Drivers Championship 2026 Without Kimi Antonelli",
      competition="Formula 1 World Championship", listed_time="06 Dec 13:00",
      market="Win Tournament", top_selection="Max Verstappen", tips_for=4, tips_total=5,
      tip_pct=80, event_id=None,
      source_url="https://www.olbg.com/betting-tips/Motor_Racing/14",
      retrieved_via=SNAP, as_of="2026-10-18", outright=True, stale_flag=True),
]

# Rugby League - live sport page (2026-10-20 snapshot) listed NO upcoming events,
# only historical stat tables. Recorded as an empty inventory.
DATA["rugby_league"] = []
DATA["aussie_rules"] = []
DATA["esports"] = []

for sport, rows in DATA.items():
    p = OUT / f"{sport}.json"
    p.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    print(f"{sport:15s} {len(rows):3d} events -> {p.relative_to(ROOT)}")

# sport registry
reg = [dict(olbg_sport_id=i, slug=s, name=n, included=inc, note=note,
            listing_url=(f"{T}/{s}/{i}" if inc else None),
            registry_source="https://www.olbg.com/sitemap-betting-tips.xml")
       for (i, s, n, inc, note) in SPORTS]
(ROOT / "data" / "survey" / "sports.json").write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
print(f"\nsports.json: {len(reg)} sports, {sum(1 for r in reg if r['included'])} included, "
      f"{sum(1 for r in reg if not r['included'])} excluded")
