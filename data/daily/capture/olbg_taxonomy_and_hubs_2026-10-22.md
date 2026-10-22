# Capture — OLBG.com sport taxonomy and per-sport event hubs

Fetched first-hand by the agent `fetch_page` tool on **2026-10-22, 20:56–21:10 UTC**.
Every block below is verbatim from the rendered page named above it. Rows the
site renders are listed in the order the site renders them.

## 1. Sport taxonomy (numeric id = last path segment of the hub URL)

URL: <https://www.olbg.com/betting-tips> (global tips page; sport menu) and the
hub URLs in §2–§8. The id/slug pairs are confirmed by the hub URLs that returned
a rendered page in this session; the pairs for the excluded sports are recorded
in `research/olbg-reverse-engineering.md` from the site's own tips sitemap.

| Sport | URL slug | id | Status in this project |
|---|---|---|---|
| Football (soccer) | Football | 1 | **excluded** |
| Horse Racing | Horse_Racing | 2 | **excluded** |
| Tennis | Tennis | 3 | included — 8 fixtures captured |
| Basketball | Basketball | 4 | included — covered by `/current/` |
| Golf | Golf | 5 | included — no in-scope fixture verified |
| Cricket | Cricket | 7 | included — 8 fixtures captured |
| Snooker | Snooker | 8 | included — covered by `/current/` |
| Rugby Union | Rugby_Union | 9 | included — covered by `/current/` |
| Rugby League | Rugby_League | 10 | included — **no fixture listed** |
| American Football | American_Football | 11 | **excluded** |
| Baseball | Baseball | 12 | included — covered by `/current/` |
| Ice Hockey | Ice_Hockey | 13 | included — covered by `/current/` |
| Motor Racing | Motor_Racing | 14 | included — covered by `/current/` |
| Darts | Darts | 15 | included — **no verifiable official fixture data** |
| Boxing (also files UFC/MMA) | Boxing | 16 | **excluded** |
| Cycling | Cycling | 17 | **excluded** |
| Handball | Handball | 20 | included — covered by `/current/` |
| Volleyball | Volleyball | 21 | included — no fixture listed |
| Aussie Rules | Aussie_Rules | 22 | included — **no fixture listed** |
| eSports | eSports | 23 | included — **"No tips found."** |
| Gaelic Football | Gaelic_Football | 25 | included — 2 in-window fixtures |
| Hurling | Hurling | 26 | **excluded** |
| Greyhounds | Greyhounds | 28 | included — no fixture listed |

"Specials" is not a sport on OLBG; it is a bet-type page (`/specials`), so it is
excluded by construction.

## 2. Tennis hub

URL: <https://www.olbg.com/betting-tips/Tennis/3>

```text
Ann Li vs Lilli Tagger            Today  22:30     Win Match        6/7   86%
Talia Gibson vs Ashlyn Krueger    Tomorrow  00:00  Win Match        3/4   75%
Leylah Fernandez vs Ekaterina Alexandrova  Tomorrow 02:30  Win Match  3/4  75%
Stefanos Tsitsipas vs James Duckworth      Tomorrow 04:00  Win Match  3/4  75%
Sara Bejlek vs Marie Bouzkova     Tomorrow 01:00  Set Betting      2/2  100%
Iva Jovic vs Diana Shnaider       Tomorrow 04:00  Win Match        2/3   67%
Daniil Medvedev vs Terence Atmane Tomorrow 05:30  Win Match        2/2  100%
Mary Stoiana vs Katerina Siniakova Tomorrow 01:30 Win Match        1/1  100%
Nikoloz Basilashvili vs Adrian Mannarino Tomorrow 02:30 Win Match 1/1 100%
Katie Boulter vs Antonia Ruzic    Tomorrow 03:00  Games Won        1/1  100%
Elena Rybakina vs Katarzyna Kawa  Tomorrow 07:00  Set Betting      1/1  100%
Corentin Moutet vs Tommy Paul     Tomorrow 08:00  Win Match        1/1  100%
Daniel Altmaier vs Taylor Fritz   Tomorrow 09:30  Total Games      1/1  100%
Tallon Griekspoor vs Jiri Lehecka Tomorrow 10:00  Win Match        1/1  100%
```

Event page markets (verbatim headings) — URL:
<https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Daniil_Medvedev_vs_Terence_Atmane/3?event_id=902145>

```text
Win Match: Daniil Medvedev 2/2 100% | Terence Atmane 0/2 0%
Set Betting: Medvedev 2-0 | Medvedev 2-1 | Atmane 2-1 | Atmane 2-0
1st Set Winner: Medvedev | Atmane
Games Won: Daniil Medvedev -3.50 | Terence Atmane +3.50
Total Games: Under 22.50 | Over 22.50
```

No odds are printed anywhere on the hub or event page — only tip counts and
percentages. OLBG therefore cannot be used as a price source.

## 3. Darts hub

URL: <https://www.olbg.com/betting-tips/Darts/15>

```text
Ryan Joyce vs Jermaine Wattimena      Tomorrow 13:15  Win Match 2-way  9/11  82%
Jonny Clayton vs Niko Springer        Tomorrow 14:45  Win Match 2-way  8/11  73%
Josh Rock vs Chris Dobey              Tomorrow 16:45  Win Match 2-way  7/9   78%
Krzysztof Ratajski vs Dave Chisnall   Tomorrow 13:45  Win Match 2-way  5/9   56%
Nathan Aspinall vs Cristo Reyes       Tomorrow 14:15  Win Match 2-way  5/8   63%
Wessel Nijman vs Martin Schindler     Tomorrow 15:45  Win Match 2-way  5/9   56%
Luke Littler vs William OConnor       Tomorrow 15:15  Win Match 2-way  3/6   50%
Kevin Doets vs Michael van Gerwen     Tomorrow 16:15  Win Match 2-way  3/5   60%
European Championship  25 Oct 14:00   Win Tournament  3/16  19%
PDC World Championship 2027  03 Jan 2027  Win Tournament  23/37  62%
```

## 4. Cricket hub

URL: <https://www.olbg.com/betting-tips/Cricket/7>

```text
Afghanistan vs Zimbabwe One Day Match   Tomorrow 07:30  Win Match      6/7  86%
Dolphins vs Garden Route Badgers T20    Tomorrow 12:00  Win Match      2/4  50%
New Zealand vs India 2nd T20 Match      24 Oct  03:00   Win Match      1/1 100%
India W vs Zimbabwe W 1st ODI           Tomorrow 04:30  Man Of The Match 1/2 50%
World Cup 2027                          21 Nov 2027     Outright Winner 6/12 50%
```

## 5. Gaelic Football hub

URL: <https://www.olbg.com/betting-tips/Gaelic_Football/25>

```text
St Finbarrs v Nemo Rangers        25 Oct 16:00  Nemo Rangers +1.50      10/12  83%
Moycullen v Salthill-Knocknacarra 24 Oct 19:00  SalthillKnocknacarra +3.50 9/18 50%
Kanturk v Eire Og Cor             01 Nov 14:00  Kanturk                  4/5  80%
Rathgormack v The Nire            01 Nov 15:30  Rathgormack -2.50        2/2 100%
Fr Caseys v Kildimo Pallaskenry   01 Nov 15:30  Fr Caseys -3.50          2/2 100%
```

## 6. Rugby League hub — no match listed

URL: <https://www.olbg.com/betting-tips/Rugby_League/10>

```text
State of Origin 2027   27 May 2027 06:00  Win Tournament       9/12  75%
Super League 2027      02 Oct 2027 13:00  Grand Final Winner   1/3   33%
NRL 2027               03 Oct 2027 04:30  Grand Final Winner   1/2   50%
```

No 2026 fixture appears on the hub: the 2027 season outrights are the only
rugby-league events listed.

## 7. eSports hub — empty

URL: <https://www.olbg.com/betting-tips/eSports/23>

```text
**All Sports**SPORTS MENU
No tips found.
```

## 8. Global tips page (cross-check of the tennis/gaelic rows)

URL: <https://www.olbg.com/betting-tips>

```text
St Finbarrs v Nemo Rangers   25 Oct  12:00   Nemo Rangers +1.50   10/12  83%
Ryan Joyce vs Jermaine Wattimena  Tomorrow 13:15  Ryan Joyce  1 expert  9/11 82%
NE Patriots @ CHI Bears       Today 20:15    Money Line   17/29  59%
TB Rays @ MIL Brewers         Tomorrow 20:00 Money Line   16/20  80%
CLE Cavaliers @ PHI 76ers     Today 19:10    Money Line   11/17  65%
DEN Nuggets @ OKC Thunder     Today 21:40    Money Line   11/16  69%
```

## 9. Irregularities observed at capture time (recorded, not normalised)

1. The global page prints **"St Finbarrs v Nemo Rangers 25 Oct 12:00"** while the
   Gaelic hub prints **"25 Oct 16:00"** for the same event. Both strings are
   stored; neither is converted. Flag `DL-07`.
2. The global page shows **NFL, NBA, MLB and Premier League** rows. American
   football and soccer are excluded by the brief, so those rows are recorded here
   only as evidence that the page mixes in excluded sports.
3. The tennis and darts hubs print a day label ("Today"/"Tomorrow") with **no
   date and no timezone**; the ATP pages print a date ("Fri, 23 October 2026")
   and a local start time with no zone either. The date collision between OLBG's
   "Tomorrow" and the ATP day heading is disclosed as `DL-01`.
4. OLBG lists **sixteen** tennis events; only the eight men's ATP quarter-finals
   could be matched to an official ATP order of play. The eight WTA events are
   published as unverified rows rather than lined (`DL-03`).
