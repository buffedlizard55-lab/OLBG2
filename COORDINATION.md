# Coordination

Session identifier: `bfeb6335` (Arena's fixed working branch: `arena/bfeb6335-olbg2`). The hosting environment requires all work to stay on this branch; do not create a `session-*` branch. This repository was empty apart from README at claim time (2026-10-21 UTC). No other claims existed. The first claim was committed (`a2823d4`) and pushed before implementation. A pull --rebase against the session branch preceded each successful push. The first attempted pull failed because the remote branch did not yet exist; the second attempt after the audit commit stopped on unstaged files, which were committed before retrying. No merge conflicts or competing session edits occurred.

| Task | Status | Owner | File scope | Notes |
| --- | --- | --- | --- | --- |
| Source audit and evidence-first data pipeline | done | bfeb6335 | `scripts/**`, `data/**`, `tests/**`, `.gitignore` | Partial snapshot only, validated locally. Unsupported sport coverage is a separate review item below. |
| Dashboard, category pages, review page, documentation and integration | done | bfeb6335 | `site/**`, `.github/**`, `README.md`, `COORDINATION.md` | Static Pages site built locally; final remote deployment tracked below. |
| Full eligible-sports schedule and original line coverage | needs review | unclaimed | future data and verification files; request shared output edits via board | Published on Flagged for Review page. Neither exhaustive inventory nor original prices could be responsibly verified in this session. |

## Requests and handoffs

- None. Other sessions: please claim non-overlapping scopes here before editing; the shared table and navigation are integration-owned.

## Source and verification log — 2026-10-21 UTC

- [NHL schedule Oct 21](https://www.nhl.com/schedule/2026-10-21) lists two games for Oct 21: Flyers @ Sabres and Panthers @ Senators at 7:30 PM EDT. Opened both league gamecenters individually: [PHI at BUF](https://www.nhl.com/gamecenter/phi-vs-buf/2026/10/21/2026020152) and [FLA at OTT](https://www.nhl.com/gamecenter/fla-vs-ott/2026/10/21/2026020153). Both name the teams and give Oct 21, 2026, 7:30 PM EDT. Each published row links to its own official source.
- Checked OLBG's [ice hockey index](https://www.olbg.com/betting-tips/Ice_Hockey/13), [PHI @ BUF](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/PHI_Flyers_@_BUF_Sabres/13?event_id=199897) and [FLA @ OTT](https://www.olbg.com/betting-tips/Ice_Hockey/NHL/NHL/FLA_Panthers_@_OTT_Senators/13?event_id=199896) index entries. OLBG displayed 19:37 for both whereas NHL displayed 7:30 PM EDT. OLBG did not label its time zone in the retrieved text; no conversion or reconciliation inferred. OLBG tips are not our picks.
- [OLBG NBA matchup page](https://www.olbg.com/betting-tips/Basketball/NBA/NBA/MIL_Bucks_@_WAS_Wizards/4?event_id=534889) contains a Bucks/Wizards listing and market headings. The accessible [official NBA games page](https://www.nba.com/games) showed 11 games on Oct 21 but failed to expose the individual matchup list ("Sorry, something went wrong"). Consequently no NBA fixture row is claimed as verified. See Flagged for Review.
- [MLB schedule Oct 21](https://www.mlb.com/schedule/2026-10-21) displayed no games for that date; this does not establish season-wide absence of baseball matches.
- Reviewed the two NHL source-to-row mappings manually; ran `python -m unittest discover -s tests -v` (6 passing tests) and `python scripts/build.py`. The tests reject excluded sports, malformed links, invalid high-confidence text, missing fields, and broken local links. External links were opened at research time, not monitored continuously.

## Irregularities and limits

- **Needs review:** Two OLBG vs NHL start-time discrepancies (19:37 vs 19:30 EDT). Verified league time is shown; OLBG time not interpreted.
- **Needs review:** Full multi-sport OLBG schedule, official cross-checks, original money-line/handicap/total estimates, independent confidence ratings and 30-word sourced narratives were **not** completed. No invented prices or predictions were inserted. Category pages only reflect audited sports. Market headings are categories considered, not verified original lines.
- The snapshot is dated; league feeds may change. GitHub Pages deployment is a static build, not a real-time update mechanism.

## Integration and publication

- Local integration tests and generated-link validation passed. PR link, merge result and deployment confirmation pending.
