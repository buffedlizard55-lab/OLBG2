# Line-by-line verification record — session arena/1352b77f-olbg2

Date: 2026-10-22 (fetches 07:25–08:10 UTC). Branch `arena/1352b77f-olbg2`, claim commit `d4318cf`.
Method: every cited figure was re-fetched with `fetch_page` from the governing body's own page and compared
field by field against the row published in `data/verified/matches.json` (or `data/forward/matches.json`).
No bookmaker page was read (repo-wide rule). Nothing below is copied from memory or a secondary outlet;
anything not re-read today is named explicitly as not re-read. Full flag text: `data/verified/flagged.json`
VF-34 (and VF-23 for the earlier pass).

## Result summary

| # | Source family (official URL) | Rows re-read | Result |
|---|---|---|---|
| 1 | NHL score feed — https://api-web.nhle.com/v1/score/2026-10-22 | 12/12 | all match |
| 2 | NHL team records (same feed + team summary) | 12 teams | all match |
| 3 | NBA week schedule — https://www.nba.com/schedule?date=2026-10-24 | 14/14 published + 60 captured | all match; slate captured (VF-14) |
| 4 | NBA 2025-26 standings — https://www.nba.com/standings?Season=2025-26 | 30/30 priors | all match |
| 5 | MLB Stats API schedule — https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-21&endDate=2026-11-02 | 4 desk + 7 forward | all match |
| 6 | PDC World Rankings — https://www.pdc.tv/rankings | 18/18 players | all match |
| 7 | WST Johnstone's Paint Rankings — https://www.wst.tv/rankings/abfba8fe-1423-5a2a-a96b-d77e8b413ca8 | 8/8 rows | all match |
| 8 | EHF CL standings + calendar — https://ehfcl.eurohandball.com/men/2026-27/standings/ | 5/5 rows | all match |
| 9 | URC table — https://stats.unitedrugby.com/match-centre/table/2026-27 | 16/16 club records | all match |
| 10 | URC Round 4 listing — https://stats.unitedrugby.com/match-centre/2026-27/4 | fixtures 292608–292610 | all match |
| 11 | LNR Top 14 table — https://top14.lnr.fr/classement | 14/14 clubs + 7 J7 links | all match |
| 12 | LNR Pro D2 table — https://prod2.lnr.fr/classement | 16/16 clubs + 8 J8 links | all match |
| 13 | FIA F1 drivers — https://www.formula1.com/en/results/2026/drivers | 3 named rows + field | all match |

Published values corrected in this session: **0**. New rows captured: **60** (NBA 24–31 Oct).

## Detail

### 1–2. NHL (12 rows, 22 Oct)

Compared id, matchup, venue, UTC start and each club's W-L-OTL for all twelve games
(2026020154–2026020165): BOS–NSH, TOR–NYR, OTT–SJS, NJD–ANA, PIT–FLA (23:00Z), NYI–LAK (23:30Z),
STL–VGK / DAL–WPG (23 Oct 00:00Z), CGY–MIN / EDM–CAR (01:00Z), SEA–UTA / VAN–DET (02:00Z).
Venues matched row by row; VAN's 2-8-1 home record (game 2026020165) was visible in the feed's
home-ice block. Note: the NHL feed embeds bookmaker `odds` arrays — those fields were not read
(repo-wide ban on bookmaker prices).

### 3–4. NBA (14 published rows + priors; 60 new rows)

The 14 published rows (CLE@PHI 19:00 ET + DEN@OKC 21:30 ET on 22 Oct; 12 games of 23 Oct) matched
the official week page exactly on tip-off, venue and game id. All 30 clubs' 2025-26 records and
home/road splits in `data/inputs/nba_teams.json` matched `nba.com/standings?Season=2025-26` exactly
(incl. BKN 20-62, PHX 45-37, MEM 25-57, SAC 22-60, UTA 22-60). The same schedule page server-renders
future weeks, so the 24–31 Oct slate (8+7+9+4+12+3+10+7 games, ids 0022600015–0022600153 incl. the
ten 30 Oct Emirates NBA Cup group games) was captured and originated in this session — this closes
VF-14 at matchup level for 22–31 Oct. 1–2 Nov games were not on the rendered page and are not invented.

### 5. MLB World Series (4 desk + 7 forward rows)

Stats API schedule hydrations for 21 Oct–2 Nov confirmed TB Rays @ MIL Brewers G1–G7:
G1 849805 (23 Oct), G2 849802 (24 Oct), G3 849804 (26 Oct, TB home), G4 849803 (27 Oct), G5 849799
(28 Oct, ifNecessary), G6 849801 (30 Oct, ifNecessary), G7 849800 (31 Oct, ifNecessary). Desk
“if necessary” blanks on G5–G7 are correct. Forward WS rows match the same feed.

### 6. PDC (18 rows)

`pdc.tv/rankings` World Rankings ladder read through rank 76: every player cited on the desk matched
on rank and prize money (1 Littler £3,113,500; 2 Humphries £1,062,500; 3 van Veen £1,035,750;
4 Price £782,000; 5 Clayton £706,000; 6 Wade £681,250; 7 Noppert £608,500; 8 Rock £606,500;
10 van Gerwen £587,500; 11 Aspinall £579,500; 12 Nijman £569,500; 13 Smith £567,250;
14 Bunting £566,250; 15 Searle £562,250; 16 Wattimena £538,750; 17 Dobey £534,750; 18 Woodhouse
£506,000; 19 Ratajski £440,000; 20 van Duijvenbode £430,500; 21 Heta £410,750; 22 Cross £398,500;
23 Joyce £386,500; 24 Schindler £386,250; 25 Doets £375,250; 26 Menzies £375,000; 27 Gilding
£355,750; 29 Zonneveld £281,750; 30 Chisnall £281,750; 32 O'Connor £274,500; 36 Springer £239,750;
44 Sedlacek £177,250; 71 Reyes £95,000). Rank field of every row correct.

### 7. WST (8 rows)

The official Johnstone's Paint World Rankings page renders the full top 36 server-side. Every named
rank/prize pair on the desk matches (Wilson 9th £716,800; Williams 8th £747,400; Slessor 23rd
£329,200; Gilbert 34th £221,200; Pang 29th £272,750; Jak Jones 24th £319,300). The five players
described as “outside the official top 36” (Selt, Craigie, McGill, Baranowski, Walden, Cheung Ka Wai,
O'Donnell, Wells, Brown, Donaldson — cited across the blank-value rows) are indeed absent from the
36-row list, so VF-03's blanks stand: ranks/prizes below 36 load only in a client-side widget and
were not captured.

### 8. EHF (5 rows)

Today's five fixtures appear on the official calendar exactly as published (MT Melsungen v Orlen
Wisla Plock and OTP Bank–PICK Szeged v GOG at 18:45; Sporting v IFK Kristianstad, Barça v
Montpellier and Kolstad v SC Magdeburg at 20:45; match ids 202711020101019/43/41/49/64). Group
tables matched every summary: Group B Wisla Plock 3-0-1 115:108, Melsungen 2-0-2 110:112; Group D
Sporting 3-1-0 149:125, GOG 3-0-1 145:139, Szeged 1-1-2 139:136, Kristianstad 0-0-4 122:155;
Group E Barça 4-0-0 137:104, Montpellier 1-0-3 116:125.

### 9–10. URC (16 rows)

All 16 club summaries match the official table after Round 3 (Edinburgh 3-0-0 80/54 … Zebre
0-0-3 52/116). Round 4 fixtures 292608 Cardiff v Sharks (Cardiff Arms Park), 292609 Connacht v Zebre
(Dexcom Stadium), 292610 Edinburgh v Lions (Hive Stadium) confirmed at 18:45 UTC (14:45 local;
the earlier ET-render correction of VF-29 re-confirmed — the fetch renderer is US/Eastern).
Round 5 (30–31 Oct) fixture pages were not re-fetched this session.

### 11–12. LNR Top 14 (7 rows) & Pro D2 (8 rows)

Every club summary (W-D-L, PF/PA) on the two classements matched, 30 clubs in total, and every J7
(11861–11867) / J8 (12063–12070) “prochain match” link matches the fixture id on the row.
Béziers' row remains correct after VF-25 (2-0-5 147/240; two wins in the last five).

### 13. F1 (3 rows)

`formula1.com/en/results/2026/drivers`: Antonelli 1st 340 (Mercedes), Russell 238, Hamilton 229,
Verstappen 221 — exactly the figures on the three rows (drivers' title, constructors' title race
naming the same points, Belgium race-winner market naming the same top four).

## NOT re-read this session (carry their capture-date provenance + per-row source links)

- EuroLeague Round 7 (9 rows) and forward EuroCup Round 5 (16 rows) — the api-live games endpoints
  dump the whole season in 20–34 chunks and the standings endpoint returns empty bodies; team names
  and arena names were spot-confirmed from the season dump but the row-level figures were not compared
  again today (see VF-34 and the 072755db pass for Panathinaikos/Baskonia).
- URC Round 5 fixtures (8 rows).
- Golf (2), Gaelic football (5), Rugby League (3), Cricket (1), Volleyball (3).
- Forward NHL slate for 26 Oct–2 Nov (58 rows) — the 23–25 Oct games share the capture feed verified
  in the forward layer's own research doc; the per-date feeds (one ~6-chunk fetch per date) were not
  re-fetched today.
- WST ranks below 36 (VF-03), GBGB greyhound cards (VF-22 — `https://www.gbgb.org.uk/racecards/`
  returned the official 404 page at 08:05 UTC; earlier fetch failures logged in VF-22).

## Irregularities noted

1. NBA static endpoints stay broken (`cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json`
   HTTP 500; `/games` list client-errors) while the week page is fully server-rendered — use the
   week page as the NBA fixture source (VF-14).
2. Fetch-renderer timezone is US/Eastern: URC/PDC/JS-localised pages render in ET (VF-10/VF-29
   convention). NBA pages publish explicit “ET” labels; desk keeps them labelled.
3. `pdc.tv` and `wst.tv` serve cookie-consent walls before the data; both remain readable in later
   chunks without consent interaction.
4. The GBGB site itself now 404s `/racecards/` — the official racecards path may have moved;
   VF-22 stays open with this retry recorded.
