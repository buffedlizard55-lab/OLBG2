# Collection log (raw provenance)

Every fetch used to build the dataset is recorded here with the URL, UTC capture time and
what was taken from it. Nothing enters `data/` without a line here.

| # | UTC time | URL | What was taken | Status |
|---|----------|-----|----------------|--------|
| 1 | 2026-10-21 ~05:12 | https://www.olbg.com/betting-tips | Global event list; sport IDs in hrefs | ok |
| 2 | 2026-10-21 ~05:12 | https://www.olbg.com/sitemap-betting-tips.xml | Sport taxonomy + sport IDs | ok |
| 3 | 2026-10-21 ~05:12 | https://www.olbg.com/betting-tips/Basketball/NBA/NBA/4 | NBA event list + markets | ok |
| 4 | 2026-10-21 ~05:13 | https://www.olbg.com/betting-tips/Tennis/3 | Tennis event list + markets | ok |
| 5 | 2026-10-21 ~05:13 | https://www.olbg.com/betting-tips/Cricket/7 | Cricket event list + markets | ok |
| 6 | 2026-10-21 ~05:14 | https://api-web.nhle.com/v1/schedule/2026-10-21 | NHL official schedule, 2026-10-21: 2 games | ok |
| 7 | 2026-10-21 ~05:14 | https://api-web.nhle.com/v1/standings/2026-10-20 | NHL official standings as of 2026-10-20 | ok |
| 8 | 2026-10-21 ~05:14 | https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-21 | MLB official schedule: 0 games (rest day) | ok |
| 9 | 2026-10-21 ~05:15 | https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json | NBA scoreboard JSON — fetch failed (HTTP 500) | failed |
