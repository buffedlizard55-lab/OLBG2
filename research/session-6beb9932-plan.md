# Session arena/6beb9932-olbg2 — Fresh Implementation Plan

## Date: 2026-10-22

## Scope
Build a clean, unified, deduplicated desk following all requirements:
1. Fresh capture from OLBG + official sources
2. Line origination for every match
3. Confidence grading (low/medium/high)
4. High-confidence predictions (≥30 words, -250..+10000 band)
5. Clean unified site
6. Full verification with source links

## Eligible Sports (17)
Ice Hockey, Basketball, Baseball, Tennis, Darts, Snooker, Rugby Union, Rugby League,
Handball, Volleyball, Cricket, Golf, Motor Racing, eSports, Aussie Rules, Gaelic Football, Greyhounds

## Excluded Sports (10)
Soccer/Football, Boxing, UFC/MMA, American Football, Hurling, Horse Racing, Cycling, Specials

## Implementation Steps
1. Capture OLBG listings for all eligible sports
2. Capture official sources (NHL, NBA, MLB, ATP/WTA, etc.)
3. Build unified dataset with deduplication
4. Originate lines (moneyline, handicap, total)
5. Grade confidence (high = ≥70% AND -250..+10000)
6. Write predictions for high-confidence picks
7. Build clean site
8. Verify everything
9. Create PR and merge

## File Scope
- `data/unified/**` - new unified dataset
- `scripts/unified_*.py` - new builders
- `unified/**` - new site
- `tests/test_unified.py` - new tests
- `research/session-6beb9932.md` - audit report
- `COORDINATION.md` - append-only

