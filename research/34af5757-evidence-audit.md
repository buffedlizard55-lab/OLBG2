# Independent evidence and usability audit — 24 October 2026

**Session:** `arena/34af5757-olbg2`  
**Recorded:** 2026-10-24T17:51:06Z  
**Status:** **NEEDS REVIEW** — 18 findings from 1512 offline field, row, arithmetic, prose and link checks.

## Executive result

The current `/today/` board is **not ready to be described as a full list or as five qualified high-confidence picks per sport**.
The official NHL response contains 12 games, while the board contains seven NHL rows. The five omitted games already have OLBG
event ids in the stored hub capture. One published high pick is below the requested 70% rule, and only **one** published pick is
simultaneously high under that rule, inside the requested price band, linked to an OLBG event in the stored data, and accompanied
by a ≥30-word preview.

No current fixture value was changed by this audit. The 8 published fixtures match the official audit fields checked below.
The findings are corrections for the active integration owner, not silently patched facts. Historical archive desks are outside
this external-fact audit; the root navigation is included because it directs readers between those desks.

| Metric | Result |
|---|---:|
| Published fixtures / official audit index | 8 / 13 |
| Published NHL fixtures / official NHL response | 7 / 12 |
| OLBG listing rows | 96 |
| Originated line rows | 20 |
| Picks / written previews | 6 / 6 |
| High under stored 65% rule / requested 70% rule | 3 / 2 |
| Qualified high + in-band + stored OLBG link | 1 |
| `/today/` HTML table rows checked | 315 |
| Table rows without an external review link | 0 |
| Local link or anchor errors | 0 |
| Root navigation links | 37 |

## Official-source reads performed for this audit

These were first-hand reads, not copied claims from the repository. The committed NHL/MLB audit indexes explicitly say they are
transcribed fields, not raw responses. Live pages can change after the read window.

| Source | What the response supported |
| --- | --- |
| [official/source page](https://api-web.nhle.com/v1/score/2026-10-24) | The response reported 12 games on 24 October. Games 2026020168 through 2026020179 were read, including start times, venues, records and teamLeaders. The response also identifies odds providerId 3 as Tipsport in oddsPartners. |
| [official/source page](https://api-web.nhle.com/v1/standings/2026-10-24) | The standings response directly showed Boston with 17 points, a .772727 point percentage, 42 goals for and 22 against; Vegas had 16 points, a .666667 point percentage, 46 goals for and 36 against. |
| [official/source page](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) | Game 849802 was World Series Game 2, Tampa Bay at Milwaukee, scheduled for 2026-10-25T00:00:00Z at American Family Field. Drew Rasmussen and Logan Henderson were listed as probable pitchers. |
| [official/source page](https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings&season=2026) | Milwaukee's official record was 103-59 with 832 runs scored, 618 allowed, a 55-26 home split and an 8-2 last-ten split. |
| [official/source page](https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026) | Tampa Bay's official record was 98-64 with 736 runs scored, 650 allowed, a 43-38 away split and a 5-5 last-ten split. |
| [official/source page](https://www.olbg.com/betting-tips/Ice_Hockey/13) | A fresh read displayed BUF Sabres @ WAS Capitals as event 200003. It also displayed changed tip totals/selections for other events, demonstrating that hub content changes after a snapshot. |

## Fixture reconciliation — every official audit-index row

Records are shown as **away / home**. “Matched” refers only to the named fields; it is not a claim that every statistic elsewhere
in the repository was rechecked. Missing rows must be added from the official response by the integration owner, not backfilled by inference.

| Game id | Match | Official start | Record A / H | Audit result | Official review link |
| --- | --- | --- | --- | --- | --- |
| 2026020168 | Anaheim Ducks @ Philadelphia Flyers | 2026-10-24T17:00:00Z | 4-6-0 / 3-6-3 | Matched: names, start, venue and both records checked | [NHL game centre](https://www.nhl.com/gamecenter/ana-vs-phi/2026/10/24/2026020168) |
| 2026020169 | Los Angeles Kings @ New Jersey Devils | 2026-10-24T19:30:00Z | 2-4-2 / 6-4-0 | Matched: names, start, venue and both records checked | [NHL game centre](https://www.nhl.com/gamecenter/lak-vs-njd/2026/10/24/2026020169) |
| 2026020170 | San Jose Sharks @ Boston Bruins | 2026-10-24T23:00:00Z | 6-4-1 / 8-2-1 | Matched: names, start, venue and both records checked | [NHL game centre](https://www.nhl.com/gamecenter/sjs-vs-bos/2026/10/24/2026020170) |
| 2026020171 | New York Rangers @ Ottawa Senators | 2026-10-24T23:00:00Z | 7-4-1 / 7-4-0 | Matched: names, start, venue and both records checked | [NHL game centre](https://www.nhl.com/gamecenter/nyr-vs-ott/2026/10/24/2026020171) |
| 2026020172 | Nashville Predators @ Pittsburgh Penguins | 2026-10-24T23:00:00Z | 3-3-3 / 4-6-1 | Matched: names, start, venue and both records checked | [NHL game centre](https://www.nhl.com/gamecenter/nsh-vs-pit/2026/10/24/2026020172) |
| 2026020173 | Buffalo Sabres @ Washington Capitals | 2026-10-24T23:00:00Z | 4-4-2 / 5-4-0 | Matched: names, start, venue and both records checked | [NHL game centre](https://www.nhl.com/gamecenter/buf-vs-wsh/2026/10/24/2026020173) |
| 2026020174 | Vegas Golden Knights @ Columbus Blue Jackets | 2026-10-24T23:00:00Z | 8-4-0 / 3-5-0 | Matched: names, start, venue and both records checked | [NHL game centre](https://www.nhl.com/gamecenter/vgk-vs-cbj/2026/10/24/2026020174) |
| 2026020175 | Hurricanes (CAR) @ Blues (STL) | 2026-10-24T23:00:00Z | 8-2-2 / 5-4-1 | MISSING from board; stored OLBG event 200002 | [NHL game centre](https://www.nhl.com/gamecenter/car-vs-stl/2026/10/24/2026020175) |
| 2026020176 | Maple Leafs (TOR) @ Oilers (EDM) | 2026-10-24T23:00:00Z | 6-4-2 / 8-1-1 | MISSING from board; stored OLBG event 200010 | [NHL game centre](https://www.nhl.com/gamecenter/tor-vs-edm/2026/10/24/2026020176) |
| 2026020177 | Lightning (TBL) @ Mammoth (UTA) | 2026-10-25T01:00:00Z | 7-3-0 / 7-4-0 | MISSING from board; stored OLBG event 200009 | [NHL game centre](https://www.nhl.com/gamecenter/tbl-vs-uta/2026/10/24/2026020177) |
| 2026020178 | Red Wings (DET) @ Flames (CGY) | 2026-10-25T02:00:00Z | 4-3-3 / 3-6-0 | MISSING from board; stored OLBG event 200004 | [NHL game centre](https://www.nhl.com/gamecenter/det-vs-cgy/2026/10/24/2026020178) |
| 2026020179 | Wild (MIN) @ Kraken (SEA) | 2026-10-25T02:00:00Z | 6-3-2 / 7-3-1 | MISSING from board; stored OLBG event 200005 | [NHL game centre](https://www.nhl.com/gamecenter/min-vs-sea/2026/10/24/2026020179) |
| 849802 | Tampa Bay Rays @ Milwaukee Brewers | 2026-10-25T00:00:00Z | 98-64 / 103-59 | Matched: names, start, venue, records and four run inputs checked | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |

## Pick and prediction reconciliation — every published preview

“Requested grade” applies the 70% floor without one-decimal display rounding. A preview can be well sourced and still fail the
selection, band or OLBG-availability rule; those are separate columns deliberately.

| Preview id | Selection / market | Probability | Stored grade | Requested grade | Band | OLBG stored | Words | Finding codes | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pred-nhl-2026020169 | New Jersey Devils — Money line | 73.62% | high | high | outside | yes | 82 | EXECUTIVE-OUT-OF-BAND, OLBG-SNAPSHOT-DYNAMIC, PROSE-FACT-INDEX-GAP, THIRD-PARTY-PRICE-LABEL | [official input](https://api-web.nhle.com/v1/score/2026-10-24) |
| pred-nhl-2026020174 | Vegas Golden Knights — Money line | 70.29% | high | high | in | yes | 80 | PROSE-SUPERLATIVE-CONTRADICTED, QUALIFIED-FIVE-PER-SPORT-SHORTFALL, STANDINGS-CITATION-MISSING, THIRD-PARTY-PRICE-LABEL | [official input](https://api-web.nhle.com/v1/score/2026-10-24) |
| pred-nhl-2026020170 | Boston Bruins — Money line | 69.95% | high | not high under requested rule | in | yes | 81 | HIGH-THRESHOLD-NOT-70, STANDINGS-CITATION-MISSING, THIRD-PARTY-PRICE-LABEL | [official input](https://api-web.nhle.com/v1/score/2026-10-24) |
| pred-nhl-2026020173 | Washington Capitals — Money line | 59.22% | medium | not high under requested rule | in | NO stored link | 83 | OLBG-SNAPSHOT-DYNAMIC, PICK-WITHOUT-OLBG-LISTING, PROSE-FACT-INDEX-GAP, THIRD-PARTY-PRICE-LABEL, WASHINGTON-SOURCE-ENDPOINT | [official input](https://api-web.nhle.com/v1/schedule/2026-10-24) |
| pred-mlb-849802 | Milwaukee Brewers — Money line | 56.62% | medium | not high under requested rule | in | yes | 83 | none | [official input](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |
| pred-nhl-2026020171 | Ottawa Senators — Money line | 55.47% | medium | not high under requested rule | in | yes | 79 | OLBG-SNAPSHOT-DYNAMIC, THIRD-PARTY-PRICE-LABEL | [official input](https://api-web.nhle.com/v1/score/2026-10-24) |

## Originated-line arithmetic — every published line

Fair American and decimal prices were recomputed from each stored probability. A passing arithmetic check does not validate the
probability itself or prove that a market was available at a sportsbook.

| Line id | Selection / market | Probability | Fair US | Fair decimal | Arithmetic | Other findings | Input |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nhl-2026020168-ml-home | Philadelphia Flyers — Money line | 52.37% | -110 | 1.909 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020168-ml-away | Anaheim Ducks — Money line | 47.63% | 110 | 2.100 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020169-ml-home | New Jersey Devils — Money line | 73.62% | -279 | 1.358 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020169-ml-away | Los Angeles Kings — Money line | 26.38% | 279 | 3.791 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020170-ml-home | Boston Bruins — Money line | 69.95% | -233 | 1.429 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020170-ml-away | San Jose Sharks — Money line | 30.05% | 233 | 3.328 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020171-ml-home | Ottawa Senators — Money line | 55.47% | -125 | 1.803 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020171-ml-away | New York Rangers — Money line | 44.53% | 125 | 2.245 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020172-ml-home | Pittsburgh Penguins — Money line | 46.77% | 114 | 2.138 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020172-ml-away | Nashville Predators — Money line | 53.23% | -114 | 1.879 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020173-ml-home | Washington Capitals — Money line | 59.22% | -145 | 1.689 | pass | none | [input](https://api-web.nhle.com/v1/schedule/2026-10-24) |
| nhl-2026020173-ml-away | Buffalo Sabres — Money line | 40.78% | 145 | 2.452 | pass | none | [input](https://api-web.nhle.com/v1/schedule/2026-10-24) |
| nhl-2026020174-ml-home | Columbus Blue Jackets — Money line | 29.71% | 237 | 3.366 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| nhl-2026020174-ml-away | Vegas Golden Knights — Money line | 70.29% | -237 | 1.423 | pass | none | [input](https://api-web.nhle.com/v1/score/2026-10-24) |
| mlb-849802-ml-home | Milwaukee Brewers — Money line | 56.62% | -131 | 1.766 | pass | none | [input](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |
| mlb-849802-ml-away | Tampa Bay Rays — Money line | 43.38% | 131 | 2.305 | pass | none | [input](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |
| mlb-849802-total-75-over | Over 7.5 — Game total | 64.64% | -183 | 1.547 | pass | MLB-TOTAL-INPUT-LINK-GAP | [input](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |
| mlb-849802-total-75-under | Under 7.5 — Game total | 35.36% | 183 | 2.828 | pass | MLB-TOTAL-INPUT-LINK-GAP | [input](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |
| mlb-849802-total-85-over | Over 8.5 — Game total | 51.14% | -105 | 1.955 | pass | MLB-TOTAL-INPUT-LINK-GAP | [input](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |
| mlb-849802-total-85-under | Under 8.5 — Game total | 48.86% | 105 | 2.047 | pass | MLB-TOTAL-INPUT-LINK-GAP | [input](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-24&hydrate=probablePitcher,team) |

## Qualified five-per-sport coverage

A qualified row here must be high at ≥70%, inside −250…+10000, linked to an OLBG event in the stored snapshot and have a unique
≥30-word preview. This intentionally stricter count exposes where a “top five” includes medium or otherwise unqualified rows.

| Sport | Qualified previews | Shortfall from five | Listing source |
| --- | --- | --- | --- |
| Golf | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Golf/5) |
| Volleyball | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Volleyball/21) |
| Rugby Union | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Rugby_Union/9) |
| Cricket | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Cricket/7) |
| Snooker | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Snooker/8) |
| Darts | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Darts/15) |
| Baseball | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Baseball/12) |
| Gaelic Sports | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Gaelic_Football/25) |
| Greyhounds | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Greyhounds/28) |
| Tennis | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Tennis/3) |
| Motor Racing | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Motor_Racing/14) |
| Handball | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Handball/20) |
| Ice Hockey | 1 | 4 | [OLBG hub](https://www.olbg.com/betting-tips/Ice_Hockey/13) |
| Basketball | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Basketball/4) |
| Rugby League | 0 | 5 | [OLBG hub](https://www.olbg.com/betting-tips/Rugby_League/10) |

## Flagged for Review — all findings

| Severity | Code | Affected rows | Finding / required correction | Basis | Source | Manual review |
| --- | --- | --- | --- | --- | --- | --- |
| HIGH | EXECUTIVE-OUT-OF-BAND | nhl-2026020169 | The three-card executive summary leads with a selection explicitly outside the requested −250…+10000 focus band. Keep out-of-band analysis in a separate review section rather than the primary executive card. | automated | [source](https://github.com/buffedlizard55-lab/OLBG2) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/scripts/today_build.py) |
| HIGH | HIGH-THRESHOLD-NOT-70 | nhl-2026020170 | The configured high threshold is 65.00%, not the requested 70.00%. Boston Bruins is 69.95%. Boston displays as 70.0% only after one-decimal rounding; its stored probability is 69.95%. | automated | [source](https://github.com/buffedlizard55-lab/OLBG2) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/scripts/today_model.py) |
| HIGH | NHL-OFFICIAL-COVERAGE-GAP | 2026020175, 2026020176, 2026020177, 2026020178, 2026020179 | The official response reported 12 NHL games but the board has only 7 NHL fixtures. Missing game ids: 2026020175, 2026020176, 2026020177, 2026020178, 2026020179. Five corresponding OLBG event ids already exist in the stored hub capture; these are coverage omissions, not blank values to infer away. | automated | [source](https://api-web.nhle.com/v1/score/2026-10-24) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/olbg_listings.json) |
| HIGH | NHL-OLBG-JOIN-GAP | 200002, 200009, 200010, 200005, 200004 | Stored NHL OLBG listings without a joined official fixture: 200002 (CAR Hurricanes @ STL Blues), 200009 (TB Lightning @ UTA Mammoth), 200010 (TOR Maple Leafs @ EDM Oilers), 200005 (MIN Wild @ SEA Kraken), 200004 (DET Red Wings @ CGY Flames). The official audit index contains all five corresponding games. | automated | [source](https://www.olbg.com/betting-tips/Ice_Hockey/13) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/olbg_listings.json) |
| HIGH | PICK-WITHOUT-OLBG-LISTING | nhl-2026020173 | An actionable pick is published without an OLBG event URL in the stored snapshot. | automated | [source](https://www.olbg.com/betting-tips/Ice_Hockey/13) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/picks.json) |
| HIGH | PROSE-SUPERLATIVE-CONTRADICTED | pred-nhl-2026020174, nhl-2026020174 | The Vegas preview calls its 16-point return the strongest record of any club priced on the card, and the headline calls Vegas the best record on the priced card. Boston is also priced on that card and the official standings show 17 points and a higher point percentage (.772727 versus .666667). Remove the superlative; the underlying Vegas and Boston numbers themselves are supported. | first-hand source read | [source](https://api-web.nhle.com/v1/standings/2026-10-24) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/predictions.json) |
| HIGH | ROOT-STALE-EXECUTIVE-BODY | index.html | The root notice points to the 24 October board, but the main executive body still labels 23 October matches as today's and its primary button opens the older cadence dashboard. That is the navigation ambiguity the consolidation must remove. | automated | [source](https://github.com/buffedlizard55-lab/OLBG2) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/index.html) |
| MEDIUM | MARKET-INVESTIGATION-INCOMPLETE | data/today/lines.json | Published NHL markets are ['Money line']; the complete board has ['Game total', 'Money line']. No handicap market is originated anywhere, and no NHL total is originated despite game-total listings in the OLBG capture. Unavailable or unpriced markets should be enumerated with a reason rather than omitted silently. | automated | [source](https://www.olbg.com/betting-tips/Ice_Hockey/13) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/lines.json) |
| MEDIUM | MLB-TOTAL-INPUT-LINK-GAP | mlb-849802-total-75-over, mlb-849802-total-75-under, mlb-849802-total-85-over, mlb-849802-total-85-under | All four MLB total rows say schedule + season standings but link only the schedule. The run inputs come from two standings responses, so each total row needs those input links as well. | automated | [source](https://statsapi.mlb.com/api/v1/teams/158?hydrate=standings&season=2026) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/lines.json) |
| MEDIUM | OLBG-SNAPSHOT-DYNAMIC | NO-OLBG-LISTING, nhl-2026020173, pred-nhl-2026020169, pred-nhl-2026020171 | At the audit read, OLBG displayed Buffalo at Washington as event 200003, although the stored snapshot says no listing was found. New Jersey and Ottawa tip data also differed from the stored snapshot. This does not prove the historical capture was wrong; it shows that the absence flag and tip claims are time-sensitive and need a raw capture or a fresh snapshot before publication. | first-hand source read | [source](https://www.olbg.com/betting-tips/Ice_Hockey/13) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/flagged.json) |
| LOW | PROSE-FACT-INDEX-GAP | pred-nhl-2026020169, pred-nhl-2026020173 | The New Jersey text includes Arseny Gritsyuk's five goals and the Washington text includes Dylan Strome's five assists, but those player figures are absent from each prediction's own facts array. The official score response supports both figures; add the missing fact entries so the displayed evidence index matches the prose. | first-hand source read | [source](https://api-web.nhle.com/v1/score/2026-10-24) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/predictions.json) |
| MEDIUM | QUALIFIED-FIVE-PER-SPORT-SHORTFALL | Baseball | Baseball has 0 written high-confidence picks that also meet the 70% rule, band rule and stored OLBG-link rule; the target is five. Existing top-five counts include medium or otherwise unqualified rows. | automated | [source](https://www.olbg.com/betting-tips) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/picks.json) |
| MEDIUM | QUALIFIED-FIVE-PER-SPORT-SHORTFALL | nhl-2026020174 | Ice Hockey has 1 written high-confidence picks that also meet the 70% rule, band rule and stored OLBG-link rule; the target is five. Existing top-five counts include medium or otherwise unqualified rows. | automated | [source](https://www.olbg.com/betting-tips) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/picks.json) |
| MEDIUM | RAW-SNAPSHOT-NOT-COMMITTED | data/today/sources.json | The /today/ source register describes first-hand reads but no raw official or OLBG response body is committed. Later readers can recheck the live URL but cannot independently reconstruct the historical response or changing prices/tip totals from the derived JSON alone. | automated | [source](https://api-web.nhle.com/v1/score/2026-10-24) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/sources.json) |
| MEDIUM | ROOT-NAVIGATION-OVERLOAD | index.html | The root navigation contains 37 links mixing current and historical desks. The current landing page should expose the executive summary, picks, matches, predictions, 15 sport pages and review queue first; historical material belongs in one archive link. | automated | [source](https://github.com/buffedlizard55-lab/OLBG2) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/index.html) |
| MEDIUM | STANDINGS-CITATION-MISSING | pred-nhl-2026020174, pred-nhl-2026020170 | Goal-for/goal-against facts cite the score endpoint; those direct standings fields belong to the official standings endpoint. The audit re-read confirmed Boston 42/22 and Vegas 46/36 at the standings URL. | automated | [source](https://api-web.nhle.com/v1/standings/2026-10-24) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/predictions.json) |
| MEDIUM | THIRD-PARTY-PRICE-LABEL | pred-nhl-2026020169, pred-nhl-2026020170, pred-nhl-2026020171, pred-nhl-2026020173, pred-nhl-2026020174 | The previews describe a league's own quote. The official NHL response labels providerId 3 as Tipsport; it is a third-party price carried by the league feed, not a price originated by the league. Keep the own-line and market-comparison concepts distinct. | first-hand source read | [source](https://api-web.nhle.com/v1/score/2026-10-24) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/olbg_listings.json) |
| MEDIUM | WASHINGTON-SOURCE-ENDPOINT | pred-nhl-2026020173, nhl-2026020173 | Washington's record and player-leader facts link to the schedule endpoint, while the source register assigns records and team leaders to the score endpoint. A first-hand score-endpoint read supports the values, including Alex Tuch as a WSH leader with five goals, so the appropriate correction is the citation endpoint rather than inventing a roster change. | first-hand source read | [source](https://api-web.nhle.com/v1/score/2026-10-24) | [review](https://github.com/buffedlizard55-lab/OLBG2/blob/main/data/today/sources.json) |

## Checks that passed

- All 8 published fixtures matched the official audit-index fields listed above; there were no NHL/MLB field mismatches.
- All 20 fair American and decimal price calculations matched their stored probabilities; all stored band flags matched the numeric price test.
- Every published pick had a preview. All 6 previews had at least 30 words, matching stored word counts, unique text, matching selections/markets and fact-level HTTPS links; none contained either prohibited internal-only term.
- Every one of the 315 `/today/` HTML table body rows contained an external review link. Local page links and fragments passed with zero errors.
- The MLB fixture, probable pitchers, venue, start, season records, run totals and home/away/last-ten splits were supported by the official MLB responses listed above.
- The official NHL score response supports Alex Tuch as a WSH leader with five goals. The flagged Washington issue is the citation endpoint, not an unsupported roster assertion.

## Required integration actions

1. Join the five omitted official NHL games to their already captured OLBG event ids, then recalculate the actual five highest eligible ice-hockey selections from the full candidate set.
2. Apply one documented 70% high-confidence rule. Do not let one-decimal formatting turn 69.95% into an apparently qualifying 70.0% high pick.
3. Keep the out-of-band New Jersey selection out of the primary in-band executive summary; do not reprice it to fit.
4. Remove the contradicted Vegas superlative, add the missing standings citations and correct the Washington citation endpoint.
5. Describe Tipsport prices as third-party prices carried by the NHL feed. Add all standings input URLs to MLB total rows.
6. Enumerate unpriced market families and reasons; do not represent moneyline-only NHL coverage as an investigation of every available market.
7. Replace the stale root executive body and overloaded current/historical navigation with one current desk and one archive link.
8. Preserve raw, timestamped source responses or clearly retain the current limitation. Refresh dynamic OLBG tip/absence claims before publication.

## Reproduce

```sh
python3 scripts/audit34_integrity.py
python3 scripts/audit34_report.py
python3 -m unittest tests.test_audit34 -v
python3 scripts/integration_audit.py
```

`data/audit34/report.json` is the machine-readable exception register. This audit does not claim fresh official reads for the other
14 sports, does not fill their missing fixtures, and does not mark the five-per-sport target complete.
