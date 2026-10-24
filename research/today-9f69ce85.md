# OLBG.com — live re-read, 24 October 2026 (session `arena/9f69ce85-olbg2`)

All fifteen hubs were fetched between **17:15 and 17:50 UTC** on 2026-10-24. Everything below is
what the pages actually returned in that window; nothing is carried over from an earlier session.

## 1. Routing that still works

| Shape | Example | Note |
|---|---|---|
| Sport hub | `https://www.olbg.com/betting-tips/Ice_Hockey/13` | returns the tips table for that sport |
| Sport hub without the numeric id | `https://www.olbg.com/betting-tips/Ice_Hockey` | **404** — the id is mandatory |
| Event page | `https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/LA_Kings_@_NJ_Devils/13?event_id=200000` | `{Sport}/{Group}/{Competition}/{Event}/{id}?event_id=N` |
| Grouped sports | `https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/...` | tennis, darts, snooker, cricket, Gaelic, greyhounds use `All_*` groups |
| Nested groups | `https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/...` | handball, volleyball, rugby union, basketball (Europe) all nest under a group |

Sport ids confirmed live today: Golf 5, Volleyball 21, Rugby Union 9, Cricket 7, Snooker 8, Darts 15,
Baseball 12, Gaelic Football 25, Greyhounds 28, Tennis 3, Motor Racing 14, Handball 20, Ice Hockey 13,
Basketball 4, Rugby League 10. These match the taxonomy recorded in `research/olbg-reverse-engineering.md`.

## 2. What a hub page gives you

One row per listed event: the event name, a competition label where the sport is grouped, a displayed
start, **the single most-tipped selection**, its market label, a tip count written as `x/y Win Tips`, a
percentage, comment and expert badges, an `event_id`, and the event URL.

It does **not** give you odds. No price is rendered on any hub page in any of the fifteen sports today,
so OLBG cannot be used as an odds source here. Every price on this site is originated from official
league inputs instead.

## 3. Irregularities seen today (all published, none silently patched)

1. **Displayed times are not UTC and are not consistent across sports.** NHL rows show US Eastern clock
   time plus about seven minutes — `Today 19:07` is a 23:00Z start. Greyhound rows are UK race times.
   The strings are stored verbatim in `data/today/olbg_listings.json` and are never used as kick-offs.
2. **The golf hub returned "No tips found."** No golf event exists to attach a pick to. Its in-page sport
   menu also labels itself "All Sports" rather than "Golf" — a cosmetic bug, not a data one.
3. **Rugby League listed only 2027 outrights.** State of Origin, Super League and NRL futures were present;
   no match event of any kind. That is a coverage fact, not a capture failure.
4. **Promo cards are interleaved inside the tips list.** On the Ice Hockey hub an inline row of "Best
   Ice Hockey Betting Sites UK" cards sits *between* two tips, so a naive scraper that stops at the first
   block loses roughly half the slate. The capture here continues past the promo block.
5. **Expired rows are still rendered.** Two greyhound races carried an "Expired" badge while showing a
   67% most-tipped selection. Started events were excluded from any pick.
6. **Hubs are paginated.** Every hub ends with a "Load More Tips" control, so the 96 rows captured here are
   the first page of each sport, not a complete inventory.

## 4. What that means for the picks

A pick needs three things: an OLBG listing (so it can be placed), an official fixture confirmation (teams
plus start), and official facts to write about. Today:

* **Ice Hockey** — 16 listings and 12 NHL games in the league feed; 7 fixtures confirmed end-to-end, 6 of
  them still upcoming at the cut-off, so 5 picks were published.
* **Baseball** — 1 listing (the World Series game) and 1 confirmed fixture; 1 pick.
* **Basketball** — 10 listings, including 9 NBA games, but no official per-game data could be read:

  | Endpoint | Result |
  |---|---|
  | `https://www.nba.com/games?date=2026-10-24` | calendar rendered (8 games on the date), game payload replaced by "Sorry, something went wrong" |
  | `https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json` | HTTP 500, twice |
  | `https://stats.nba.com/stats/scoreboardv3?GameDate=2026-10-24&LeagueID=00` | request failed |

* **The other eleven sports** — listings exist, official confirmation does not. Reasons and the exact URLs
  are on `today/flagged.html`.

## 5. Files this session owns

`data/today/**`, `scripts/today_*.py`, `today/**`, `tests/test_today_9f69ce85.py`, and the append-only
sections of `README.md` and `COORDINATION.md`. No earlier desk, `site/**` or `/zenith/` file was touched.
