# OLBG.com — reverse engineering notes

Captured 2026-10-21 (UTC) from the live site with the agent fetch tool. OLBG is a
UK-facing betting-tips community site. The data we need (event list, market type,
tip counts) is rendered server-side into the tips list on every sport hub page, so it
can be read without an API key.

## 1. Sport taxonomy and numeric sport IDs

The numeric ID is the last path segment of every sport hub URL and is also embedded in
every event URL. Extracted from `https://www.olbg.com/sitemap-betting-tips.xml`.

| Sport | Slug | ID | Included in this project |
|-------|------|----|--------------------------|
| Horse Racing | `Horse_Racing` | 2 | excluded |
| Football (soccer) | `Football` | 1 | excluded |
| Tennis | `Tennis` | 3 | included |
| Golf | `Golf` | 5 | included |
| American Football (NFL) | `American_Football` | 11 | excluded |
| Rugby League | `Rugby_League` | 10 | included |
| Rugby Union | `Rugby_Union` | 9 | included |
| Cricket | `Cricket` | 7 | included |
| Basketball | `Basketball` | 4 | included |
| Baseball | `Baseball` | 12 | included |
| Darts | `Darts` | 15 | included |
| Snooker | `Snooker` | 8 | included |
| Boxing | `Boxing` | 16 | excluded |
| Ice Hockey | `Ice_Hockey` | 13 | included |
| Motor Racing | `Motor_Racing` | 14 | included |
| Handball | `Handball` | 20 | included |
| Volleyball | `Volleyball` | 21 | included |
| Greyhounds | `Greyhounds` | 28 | included |
| Cycling | `Cycling` | 17 | excluded |
| Gaelic Football | `Gaelic_Football` | 25 | included |
| eSports | `eSports` | 23 | included |
| Aussie Rules | `Aussie_Rules` | 22 | included |
| Hurling | `Hurling` | 26 | excluded |

Excluded set implemented in `scripts/config.py` = soccer (Football/1), boxing (16),
UFC/MMA (no separate OLBG sport ID; OLBG files MMA under Boxing/16 — verified on the
sport hub), American Football (11), Hurling (26), Horse Racing (2), Cycling (17).
"Specials" are not a sport on OLBG; they are bet-type pages (`/specials`,
`/betting-tips/.../?market=special`) and are therefore excluded by construction.

## 2. URL schema

Sport hub (paged): `/betting-tips/{Sport}/{id}`
Competition:       `/betting-tips/{Sport}/{Group}/{Competition}/{id}`
Event page:        `/betting-tips/{Sport}/{Group}/{Competition}/{Event_Name}/{id}?event_id={event_id}`

`{Event_Name}` is the display name with spaces replaced by `_`; `@` marks an away team
in US sports (`MIL_Bucks_@_WAS_Wizards`). `{event_id}` is OLBG's internal event key and
is stable across sessions.

## 3. Fields available on a hub page (per event)

`event name`, `competition label` (US sports only), `start date/time as displayed`,
`most-tipped selection`, `market type label`, `tip count / total tips`, `percent`,
`expert badges`, `comment count`, `event_id`, `event URL`.

Markets seen on the captured pages: Win Match / To Win / Money Line / Win Match 2-way,
Handicap (2-way), Puck Line, Game Totals, Total Legs, Set Betting, 1st Set Winner,
Outright Winner.

## 4. Irregularities found (flagged, not "fixed")

1. **Displayed start times do not reconcile to one timezone.** NBA events show
   US-Eastern clock times with a +10 minute offset from the official NBA tip time
   (e.g. OLBG `19:10` vs NBA `7:00 PM ET`); NHL events show UK clock times with a
   ~+7 minute offset (OLBG `Tomorrow 00:37` vs NHL `23:30Z` = `00:30` UK). Conclusion:
   OLBG's displayed time is not a reliable UTC source. The dataset stores OLBG's string
   verbatim and takes the authoritative kick-off from the official league feed.
2. **Season drift on cached pages.** The global `/betting-tips` page returned a cached
   list containing football fixtures that do not exist in October 2026 (e.g. a
   "Champions League" card with Real Madrid v RB Leipzig). Sport hub pages were
   internally consistent. Only hub pages were used for event discovery.
3. **Event names are not canonical.** Cricket appends the format to the team pair
   (`Afghanistan vs Bangladesh One Day Match`); Gaelic football abbreviates
   (`Eire Og Cor`). Canonical names come from the official source.
4. **No odds are published on the hub page**; only tip percentages. Therefore OLBG
   cannot be used as an odds source here, and lines in this repo are originated
   independently (see `METHODOLOGY.md`).
