# Verification record — session `arena/ba05b5b6-olbg2` (2026-10-24)

## Scope
Thirteen new high-confidence written predictions were added to `data/cadence/predictions.json`, one per high-confidence in-band selection that previously lacked a write-up. Every fact in every prediction carries a URL to an official governing-body or league page fetched in this session. No value was inferred or filled in. The words "model" and "verified" do not appear in any prediction text.

## Predictions added (13)

| # | Fixture | Selection | Market | Line | Probability | Fair American | Sport |
|---|---|---|---|---|---|---|---|
| 1 | Boston Celtics v New York Knicks (nba-0022600008) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 2 | San Antonio Spurs v Houston Rockets (nba-0022600009) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 3 | Charlotte Hornets v Atlanta Hawks (nba-0022600094) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 4 | Indiana Pacers v Dallas Mavericks (nba-0022600095) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 5 | Orlando Magic v Minnesota Timberwolves (nba-0022600096) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 6 | Washington Wizards v Toronto Raptors (nba-0022600097) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 7 | Miami Heat v Detroit Pistons (nba-0022600098) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 8 | Milwaukee Bucks v Chicago Bulls (nba-0022600099) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 9 | Utah Jazz v New Orleans Pelicans (nba-0022600100) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 10 | Golden State Warriors v Memphis Grizzlies (nba-0022600101) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 11 | Los Angeles Lakers v LA Clippers (nba-0022600102) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 12 | Sacramento Kings v Portland Trail Blazers (nba-0022600103) | Under 234.5 | Game total | 234.5 | 0.714 | -249 | Basketball |
| 13 | Leicester Tigers v Northampton Saints (ru-leicester-northampton) | Leicester Tigers -3.5 | Handicap | -3.5 | 0.701 | -235 | Rugby Union |

All 13 sit inside the −250…+10000 fair-price band and grade high confidence. Each text is 62–73 words, unique by opening, and names an explicit betting selection.

## Official sources fetched in this session

| Source | URL | What it confirmed |
|---|---|---|
| NBA.com standings | https://www.nba.com/standings | 2026-27 regular-season W-L records, home/road splits and streaks for every NBA team used (e.g. Boston 1-1, New York 0-2, Houston 2-0, San Antonio 0-2, Golden State 0-2, Sacramento 0-2, Portland 2-0) |
| NBA injury report (PDF) | https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-23_03_15PM.pdf | Player status and reason for every injury fact cited (e.g. Devin Carter out-illness, Coby White/Grant Williams/Kon Knueppel/Kylan Boswell out for Charlotte, Jimmy Butler/Moses Moody/Kristaps Porzingis out for Golden State, Bradley Beal/Brandon Ingram/Jordan Miller/Max Strus out for LA Clippers, Shaedon Sharpe/Branden Carlson out for Portland) |
| Premiership Rugby standings | https://www.premrugby.com/standings | Leicester Tigers 3-1, +31 points difference, 16 points, form W-W-W; Northampton Saints 2-2, +20 points difference, 11 points, form L-W-L |

## Method
- Fixture matchups, start times and competition were taken from the existing checked-in `data/cadence/matches.json` (itself sourced from official league feeds).
- Team records, form and injuries were re-read from the official pages above in this session.
- Probability (0.714 NBA / 0.701 Leicester) and fair American price (−249 / −235) come from the already-originated lines in `data/cadence/lines.json`; they were not re-derived.
- Each prediction fact cites the official URL it was read from. No claim is made without a source URL.

## Irregularities / open items (not silently fixed)
- Leicester Tigers stored match facts (2-0-1 after three rounds, +10, 11 points) reflect an earlier capture; the live Premiership Rugby page now reads 3-1 after four rounds, +31, 16 points, form W-W-W. The live verified standings were used for the prediction and cited; this is disclosed rather than hidden.
- Golf, Greyhounds and Gaelic Sports have no high-confidence pick supported by official facts; their five-per-sport shortfall is flagged on the review page, not padded.
- No bookmaker price was read or used; fair prices are the desk's own originated estimates.
