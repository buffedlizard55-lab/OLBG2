# Verified desk refresh — session `arena/4daa1e65-olbg2`

Capture/review date: **2026-10-22 UTC**. This note records evidence and limitations; it is not a claim that every OLBG event has been independently confirmed by a governing body.

## Baseline reproduction (before implementation edits)

Ran the workflow's complete regeneration sequence in `.github/workflows/pages.yml` order:

1. `verified_seed.py`, `verified_model.py`, `verified_build.py`
2. `live_model.py`, `live_build.py`
3. `build.py`
4. `survey_sync_inventory.py`, `survey_lines.py`, `survey_analyse.py`, `survey_build.py`, `survey_verify.py`
5. `build_site.py`, `integration_audit.py`
6. `python3 -m unittest discover -s tests -v`
7. the workflow's scoped `git diff --exit-code` stale-output check

Result: **60/60 tests passed**, survey verification passed, integration audit reported zero local-link errors, and the generated-file diff was empty. This proves deterministic structural reproduction only; it does not externally validate the stored facts.

Baseline `/verified/` snapshot: 155 rows (112 originated, 43 unlined), 20 High, 38 Medium, 54 Low, capture date 2026-10-21.

## Confirmed repository defects to remediate

- Stale 21 October NHL, NBA, EuroLeague/EuroCup, tennis, snooker, volleyball, cricket and greyhound rows remain presented as an active desk on 22 October.
- Basketball uses OLBG sport id/route `19`; the live hub and sitemap use **Basketball/4**. Golf uses `4`; the live hub and sitemap use **Golf/5**. Downstream event links must use the same corrected ids.
- Several sport summaries describe a different number or slate from the rows actually generated (for example NHL, Basketball, Rugby Union, Volleyball, Golf and Motor Racing).
- OLBG-discovered events and official-only supplementary fixtures are not differentiated. The NHL and parts of the Rugby Union, Handball and Baseball schedules are official supplements, not evidence that those events currently have OLBG tips.
- Multiple hubs still display **Load More Tips**. The rendered page chunks expose more cards than a first-chunk reading, but do not resolve the dynamic control. No exhaustive all-OLBG claim is supportable until that limitation is explicitly flagged.
- The model uses `HIGH_THRESHOLD = 0.72` and has no American-odds-band gate. The requested strict screen is probability **> 70%**, with fair American price between **-250 and +10000** (decimal 1.40 through 101.00).
- Some High narratives cite official-looking URLs for statements not established by the cited page, and some use OLBG itself as a “fact” source. High narratives must contain only manually reviewed official evidence.
- The published methodology and audit pages contain hard-coded 21 October counts, branch names and thresholds.

## OLBG reverse-engineering and visible-card inventory

Source taxonomy: <https://www.olbg.com/sitemap-betting-tips.xml> and each eligible sport hub. Correct eligible routes are Ice Hockey/13, Basketball/4, Rugby Union/9, Handball/20, Darts/15, Tennis/3, Snooker/8, Baseball/12, Motor Racing/14, Volleyball/21, Cricket/7, Golf/5, Rugby League/10, Gaelic Football/25, Greyhounds/28, Aussie Rules/22 and eSports/23.

The hub card links carry `event_id` values and the most-tipped selection/market. Those percentages are community tip shares, **not model probabilities and not independent fair prices**. Event cards are interspersed with editorial modules in later response chunks, so all rendered chunks must be inspected before counting the static inventory.

Visible cards captured on 22 October (static rendered inventory, not a claim about hidden Load More results):

| Hub | Visible current cards | Notes |
|---|---:|---|
| Ice Hockey | 4 | SHL Skellefteå–Djurgården (`199905`), Timrå–Färjestad (`199901`), Örebro–Brynäs (`199900`); Liiga JYP–HPK (`199912`). No current NHL card visible. Load More present. |
| Basketball | 13 | Seven NBA cards include three already live/completed 21 October ET games plus DEN–OKC `534843`, CLE–PHI `534845`, HOU–SAS `534841`, NYK–BOS `534842`; four EuroLeague, one KBL and one NBB cards. Load More present. |
| Rugby Union | 16 | 15 match cards plus Six Nations 2027 `609013`; Load More present. |
| Handball | 20 | Five current EHF CL cards plus domestic/international cards; Load More present. |
| Darts | 18 | 16 European Championship ties plus outrights `26023`, `32338`; Load More present. |
| Tennis | 20 | Twenty match cards across ATP/WTA; Load More present. |
| Snooker | 0 | “No tips found.” |
| Baseball | 1 | TB @ MIL `160789`; Load More present. |
| Motor Racing | 3 | USA GP `913`, Drivers Championship `828`, Championship Without Kimi Antonelli `912`. |
| Volleyball | 9 | Three PlusLiga, five Czech and one Polish women's card; Load More present. |
| Cricket | 12 | Seven match cards and five outrights; Load More present between match and outright groups. |
| Golf | 4 | Bermuda `101904`, Senior Italian Open `101911`, Stella Artois Players Championship `101912`, Stifel Charity Classic `101903`. |
| Rugby League | 3 | State of Origin `2695857`, Super League `2801554`, NRL `2801600`. The prior seed swaps the State of Origin/NRL ids. |
| Gaelic Football | 6 | Five club matches incl. Fr Caseys `3537` plus All-Ireland 2027 `3327`; Load More present. |
| Greyhounds | 0 | “No tips found.” |
| Aussie Rules | 0 | “No tips found.” |
| eSports | 0 | “No tips found.” |

Pagination probes `?page=2` and `?offset=15` returned the initial Basketball card set; `/Basketball/4/2` was a no-tips route, not page two. They are not valid pagination evidence.

## Official confirmations and source captures

### NHL

- <https://api-web.nhle.com/v1/score/2026-10-22> — all five response chunks reviewed; 12 games on the official 22 October schedule.
- MIN @ CGY is game **2026020162**, 2026-10-23T01:00:00Z at Scotiabank Saddledome. Official records: Minnesota 6-2-2, Calgary 2-6-0. The feed's leaders include Kirill Kaprizov 11 goals, Quinn Hughes 11 assists, Jesper Wallstedt six wins and Dustin Wolf one win.
- <https://api-web.nhle.com/v1/club-schedule/MIN/week/2026-10-19> — Minnesota lost 4-3 in overtime at Edmonton on 20 October; upcoming Calgary fixture confirmed.
- <https://api-web.nhle.com/v1/club-schedule/CGY/week/2026-10-12> — Calgary beat Carolina 3-2 on 18 October after earlier losses including 6-2 at Vegas.

### SHL and Liiga

- <https://stats.swehockey.se/ScheduleAndResults/Overview/20961> — official Swedish Ice Hockey Federation page confirms all three OLBG SHL pairings for 22 October at 19:00 local, venues, current table and recent scores. Färjestad lead at 8W-2T-0L, 40:11, 27 points; Timrå are 2W-3T-5L, 20:23, 12 points. Skellefteå are third (32:25) and Djurgården 12th (23:33); Örebro and Brynäs each have 14 points.
- <https://www.liiga.fi/en/schedule?kausi=2026-2027&sarja=runkosarja&joukkue=hpk> and <https://www.jypliiga.fi/> — JYP–HPK confirmed for 22 October at 18:30 local (15:30 UTC on the official league display).

### Rugby Union

- <https://prod2.lnr.fr/classement> — Aurillac ninth, 3W-0D-4L, 240:254, two straight wins; Nevers 16th, 0W-0D-7L, 146:222.
- <https://prod2.lnr.fr/feuille-de-match/2026-2027/j8/12066-aurillac-nevers> — Aurillac–Nevers, 23 October, 19:30 local, Stade Jean Alric.
- <https://stats.unitedrugby.com/match-centre/table/2026-27> — Connacht 1W-0D-2L; Zebre 0W-0D-3L, 52:116; recent results include Glasgow 36-19 Connacht and Zebre 12-29 Edinburgh.
- <https://stats.unitedrugby.com/match-centre/202601/united-rugby-championship/connacht-rugby-vs-zebre-parma-2026-10-23/292609> — Connacht–Zebre at Dexcom Stadium on 23 October.

### NBA

- <https://www.nba.com/games?date=2026-10-22> and `?date=2026-10-23` — two and 12 official daily games respectively; the 21 October ET cards were already live when reviewed and must not be published as upcoming picks.
- <https://www.nba.com/game/den-vs-okc-0022600007> — DEN @ OKC, 22 October 21:30 ET, Paycom Center; OKC 1-0, DEN 0-0 on the linked official calendar. Recent official matchup scores are also displayed.
- <https://www.nba.com/game/cle-vs-phi-0022600006> — CLE @ PHI, 22 October 19:00 ET, Xfinity Mobile Arena; Philadelphia opened with a 106-100 win over New York, Tyrese Maxey 28 points.
- <https://www.nba.com/game/nyk-vs-bos-0022600008> — NYK @ BOS, 23 October 19:00 ET, TD Garden; official standings show both 0-1.
- <https://www.nba.com/game/hou-vs-sas-0022600009> — HOU @ SAS official id confirmed; linked official calendar shows San Antonio 0-1 entering the game.
- <https://www.nba.com/standings> — current 2026-27 records used only where shown; prior-season modelling remains Medium-capped.

### MLB and Formula 1

- <https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-23&endDate=2026-10-27&hydrate=team,venue> — TB @ MIL World Series Game 1 `gamePk=849805` on 23 October; Games 2 and 3 on 24 and 26 October. Only Game 1 is visible on the current OLBG card; later games are official supplements.
- <https://www.formula1.com/en/racing/2026/united-states> — United States GP race on 25 October at 16:00 track time, Circuit of the Americas.
- <https://www.formula1.com/en/results/2026/drivers> — official driver standings source; any values not re-read in the current capture must remain explicitly tied to their stored capture rather than described as newly checked.

## Strict High screen on the stored pre-refresh model

American -250 = decimal 1.40; +10000 = decimal 101.00. Applying `p > 0.70` and fair decimal >= 1.40 to the stored model leaves four candidates, all previously Medium:

- `nhl-2026020162`: Minnesota Wild, p=0.7082, fair 1.41.
- `prod2-12066`: Stade Aurillacois, p=0.7053, fair 1.42.
- `urc-292609`: Connacht Rugby, p=0.7025, fair 1.42.
- `ehfcl-202711020101001`: One Veszprém HC, p=0.7103, fair 1.41 — **21 October fixture, therefore stale and excluded from the refreshed active desk**.

The first three have current official fixture/form evidence above. They are candidates for refreshed High narratives, not evidence that the old snapshot was already compliant.

## Coverage and publication rule for the refresh

- Remove stale rows from the active dataset rather than silently presenting them as upcoming.
- Distinguish `OLBG-discovered`, `official supplementary`, and `official confirmation pending` states in the data/UI.
- Keep unconfirmed fields blank and unconfirmed events unlined. An official review URL is not, by itself, proof of fixture verification.
- Do not sum overlapping rows across `/`, `/site/`, `/survey/`, `/live/` and `/verified/`.
- Publish the visible static inventory plus clearly labelled official supplements, and flag every unresolved Load More hub. Do not claim exhaustive dynamic OLBG coverage.
