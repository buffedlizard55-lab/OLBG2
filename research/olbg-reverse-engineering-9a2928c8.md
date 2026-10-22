# OLBG Reverse Engineering — session arena/9a2928c8-olbg2 (2026-10-22)

This re-verification was done on 2026-10-22 UTC to confirm the OLBG sport taxonomy, URL schema, market labels and exclusions used by the live desk (119 rows).

## Method
- Fetched `https://www.olbg.com/betting-tips` via fetch_page (2026-10-22).
- Searched `OLBG.com betting tips sports taxonomy` via web_search (20+ sports).
- Cross-checked against prior verified inputs in `data/verified/sports.json` and `data/survey/sports.json`.

## Findings

### 1. Sport taxonomy
OLBG serves a global tip feed at `/betting-tips` listing today's events across 20+ sports. The page menu links to per-sport hubs of the form `/betting-tips/{Sport_Name}/{id}`. Verified examples in this session:
- `https://www.olbg.com/betting-tips/Baseball/12` — MLB Money Line market observed (TB Rays @ MIL Brewers on 23 Oct)
- `https://www.olbg.com/betting-tips/Basketball/19` — NBA / EuroLeague
- `https://www.olbg.com/betting-tips/Ice_Hockey/13` — NHL
- `https://www.olbg.com/betting-tips/Rugby_Union/9` — URC / Top14
- `https://www.olbg.com/betting-tips/Handball/20` — EHF CL
- `https://www.olbg.com/betting-tips/Darts/15` — PDC EC
- `https://www.olbg.com/betting-tips/Tennis/3`
- `https://www.olbg.com/betting-tips/Snooker/8`
- `https://www.olbg.com/betting-tips/Cricket/7`
- `https://www.olbg.com/betting-tips/Golf/4`
- `https://www.olbg.com/betting-tips/Motor_Racing/14`
- `https://www.olbg.com/betting-tips/Volleyball/21`
- `https://www.olbg.com/betting-tips/Rugby_League/10`
- `https://www.olbg.com/betting-tips/Gaelic_Football/25`
- `https://www.olbg.com/betting-tips/Greyhounds/28`
- `https://www.olbg.com/betting-tips/Aussie_Rules/22`
- `https://www.olbg.com/betting-tips/eSports/23`

Excluded per brief (8 categories) — verified to exist as OLBG hubs but filtered out:
- Soccer/Football `1` — `https://www.olbg.com/betting-tips/Football/1` (100+ leagues)
- Horse Racing `2` — `https://www.olbg.com/betting-tips/Horse_Racing/2`
- American Football `11` — `https://www.olbg.com/betting-tips/American_Football/11`
- Boxing `6`
- UFC/MMA `27` — `https://www.olbg.com/betting-tips/UFC_MMA/27`
- Hurling `26` — `https://www.olbg.com/betting-tips/Hurling/26`
- Cycling — no active hub (sporadic coverage noted in OLBG help)
- Specials — no active hub

The 17 eligible sports in `data/verified/sports.json` match exactly: Ice Hockey, Basketball, Rugby Union, Handball, Darts, Tennis, Snooker, Baseball, Motor Racing, Volleyball, Cricket, Golf, Rugby League, Gaelic Football, Greyhounds, Aussie Rules, eSports. This equals 25 total minus 8 excluded.

### 2. URL schema
- Sport hub: `/betting-tips/{Sport}/{id}` (id numeric, e.g., 13 for Ice Hockey)
- Event page: `/betting-tips/{Sport}/{League}/{Home}_v_{Away}/{id}?event_id={n}` or `/betting-tips/{Sport}/All_{Sport}/All_Events/{Match}/{id}?event_id={id}` — verified with baseball event 160789 and darts event 32324 on the live feed.

### 3. Market labels (OLBG vocabulary)
- Baseball: Money Line, Run Line (-1.5/+1.5), Game Totals (Over/Under) — confirmed in baseball explainer.
- Ice Hockey: win match / moneyline, puck line, total.
- Basketball: moneyline, handicap/spread, totals.
- Rugby Union: 1X2, handicap, total points.
- Darts: Win Match 2-way (best of 11 legs), handicap, total legs.
- OLBG renders tip counts (e.g., 13/16 Win Tips 81%) and comments, not bookmaker prices — prices are client-side `WIN @`.

### 4. Irregularities (for flagged page)
- Viewer-timezone rendering: fixture times shown without zone (confirmed prior F24).
- Abbreviated club names on OLBG vs official registered names (F25).
- Global `/betting-tips` cards are cached and may intermix sport feeds; per-sport hub is authoritative for inclusion decisions.
- No OLBG price scraped — model originates its own fair decimals.

### 5. Verification outcome
The live desk's eligible_sports list, excluded_sports list, olbg_url fields and markets_investigated arrays are consistent with the live OLBG taxonomy observed on 2026-10-22. No correction needed; this file serves as manual-review evidence.
