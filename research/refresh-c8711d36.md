# Refresh and gap-closure attempt — session c8711d36 (2026-10-21)

Every value below was re-read from the official source named. Nothing was inferred;
where a table could not be read, the existing flag stays open and says so.

| Check | Official source | Result |
|---|---|---|
| San Jose Sharks GP/W/L/OTL/GF/GA | NHL standings API https://api-web.nhle.com/v1/standings/now (standings date 2026-10-20) | **Verified:** 10 GP, 5-4-1, 11 pts, **27 GF / 35 GA**, home 2-2-0, away 3-2-1, L10 5-4-1. Matches `data/desk/nhl_teams.json` exactly, closing the desk layer's cross-scope request. Root dashboard uses the stats-API convention (26/34); the one-goal difference each way equals San Jose's one shootout win — the convention already flagged as F19. No change to either dataset. |
| ICC men's ODI rankings | https://www.icc-cricket.com/rankings/team-rankings/mens/odi | Page loads, fixtures AFG v BAN (ODI) and NZ v IND (T20I) confirmed as upcoming, but ranking table rows render empty. **F11 stays open** for the root dashboard; survey-layer cricket lines (ESPNcricinfo ICC ratings) unaffected. |
| ATP singles rankings | https://www.atptour.com/en/rankings/singles | Page loads, week 2026.10.19 offered, table client-rendered and not extracted. **F04 stays open.** |
| Scope: Greyhounds / Gaelic Football | Brief exclusion list + https://www.olbg.com/sitemap-betting-tips.xml (ids 25, 28) | Neither sport is named in the brief's exclusions, so both remain **in scope** on the root dashboard per `scripts/config.py`. The survey layer's contrary judgement stays flagged (survey F-03); recorded on the root flagged page as **F23**. No fixtures published for either — Gaelic club fixtures remain unverified (F07). |

Structured record: `data/refresh/refresh.json`.
