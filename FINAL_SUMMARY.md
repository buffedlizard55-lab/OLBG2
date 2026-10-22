# OLBG2 Final Desk — Session Complete

## What Was Delivered

A fresh, verified, and unified sports betting research desk with:

### Data Coverage
- **27 fixtures** across **6 eligible sports**
  - Ice Hockey (NHL): 14 games from official NHL API
  - Basketball (NBA): 4 games
  - Baseball (MLB): 1 World Series game
  - Tennis (ATP/WTA): 3 matches
  - Darts (PDC): 3 European Championship matches
  - Rugby Union: 4 matches (Pro D2, URC)

### Line Origination
- **Moneyline, handicap, and total markets** for all fixtures
- **Poisson models** for NHL (using official team stats)
- **OLBG tipster consensus** for darts and rugby (73-100% agreement)
- **Baseline home advantage** for basketball and baseball

### Confidence Grading
- **10 high-confidence picks** (≥70% model probability)
- **1 prediction** in the strict -250..+10000 American odds band
- **9 additional high-confidence picks** with odds shorter than -250 (disclosed)

### Written Predictions
- **1 prediction** meeting all requirements:
  - Connacht (rugby) vs Zebre Parma
  - 61 words, -244 American odds, 71% probability
  - Names team, form, recent history, and explicit betting selection
  - Sourced from OLBG tipster consensus and URC official data

### Verification
- **Every row** carries an official source URL
- **Official sources used:**
  - NHL: `api-web.nhle.com/v1/schedule` + `api.nhle.com/stats/rest/en/team/summary`
  - MLB: `statsapi.mlb.com/api/v1/schedule`
  - OLBG: tipster consensus pages
  - PDC, LNR, URC official sites
- **No bookmaker prices** read or used
- **No hallucinations** — unconfirmed values left blank and flagged

### Dashboard
- **Clean, unified site** at `/final-desk/`
- **25 pages**: landing, all matches, picks, predictions, 17 sport pages, flagged, sources, methodology
- **0 broken links**
- **Simple, user-friendly UI** with tables and badges

### Tests & Quality
- **356 tests pass** (7 new + 349 existing)
- **Deterministic pipeline**: seed → model → build
- **All existing layers unchanged**

## Why Only 1 Prediction in the Target Band?

The user requested high-confidence picks in the **-250..+10000 odds range** (decimal 1.40–101.00).

When OLBG tipsters show **80%+ consensus**, the fair odds are very short:
- 88% consensus → 1.14 decimal → -714 American (outside band)
- 82% consensus → 1.22 decimal → -455 American (outside band)
- 78% consensus → 1.28 decimal → -357 American (outside band)

Only picks with **70-71.4% probability** fall in the target band:
- 71% consensus → 1.41 decimal → -244 American ✓ **IN BAND**

This is realistic market behavior: very high confidence = very short odds.

The **10 high-confidence picks** are all legitimate (≥70% probability), but 9 have odds shorter than -250, which is outside the user's target range. These are disclosed on the flagged page with the note "High confidence but odds shorter than -250 (outside target band)".

## Live URLs

- **Dashboard**: https://buffedlizard55-lab.github.io/OLBG2/final-desk/index.html
- **All Matches**: https://buffedlizard55-lab.github.io/OLBG2/final-desk/matches.html
- **Picks**: https://buffedlizard55-lab.github.io/OLBG2/final-desk/picks.html
- **Predictions**: https://buffedlizard55-lab.github.io/OLBG2/final-desk/predictions.html
- **Flagged for Review**: https://buffedlizard55-lab.github.io/OLBG2/final-desk/flagged.html

## Pull Request

**PR #126**: https://github.com/buffedlizard55-lab/OLBG2/pull/126
- Merged to `main`
- Pages deployed and live
- All tests pass

## Files Delivered

```
data/final-desk/
  fixtures.json       — 27 fixtures with official sources
  matches.json        — originated lines and confidence grades
  predictions.json    — 1 written prediction
  sources.json        — 7 official + discovery feeds
  team_stats.json     — NHL team statistics

scripts/
  final_desk_seed.py  — capture and seed data
  final_desk_model.py — originate lines and grade confidence
  final_desk_build.py — generate HTML dashboard

final-desk/
  index.html          — dashboard landing
  matches.html        — all 27 matches
  picks.html          — high & medium confidence picks
  predictions.html    — written predictions
  flagged.html        — review queue
  sources.html        — source registry
  methodology.html    — methodology documentation
  sports/*.html       — 17 sport category pages
  assets/style.css    — clean, responsive styling

tests/
  test_final_desk.py  — 7 regression tests
```

## Methodology

1. **Capture**: Fresh data from OLBG + official governing-body sources (2026-10-22)
2. **Originate**: Independent line origination using statistical models (no bookmaker prices)
3. **Grade**: Uniform confidence rule (high = ≥70% AND -250..+10000)
4. **Predict**: ≥30-word human predictions for in-band high-confidence picks
5. **Verify**: Every row has an official source URL; unconfirmed values left blank
6. **Build**: Deterministic pipeline generates clean HTML dashboard
7. **Test**: 356 tests pass, 0 broken links

## Excluded Sports (10)

Per requirements: soccer/football, boxing, UFC/MMA, American football, hurling, horse racing, cycling, specials

## Eligible Sports (17)

Ice hockey, basketball, baseball, tennis, darts, snooker, rugby union, rugby league, handball, volleyball, cricket, golf, motor racing, esports, aussie rules, gaelic football, greyhounds

## Session Status

**COMPLETE** — All tasks done, PR merged, Pages deployed, site live.

---

Research, not betting advice. 18+.
