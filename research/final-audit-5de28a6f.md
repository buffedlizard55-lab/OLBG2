# Consolidated 17-sport audit — `arena/5de28a6f-olbg2`

Date: 2026-10-22 · snapshot clock 08:22 UTC · author session `5de28a6f`
Output: `/final/` (26 pages) · data: `data/final/{matches,summary,predictions,flagged}.json`

## 1. What this pass did

The repository carried five overlapping desks. Each was internally consistent but they
disagreed with each other: different confidence vocabularies, different denominators,
duplicate fixtures with different prices. This pass merged them into one table, applied a
single grading rule, re-read a sample of rows against the official pages, and published
the result with per-row provenance.

Nothing in the five source layers was edited. They remain byte-identical and are linked
from `final/archive.html`.

## 2. Layer inventory (read from the files, not from headings)

| Layer | Rows | Lined | Sports | Dated range |
|---|---:|---:|---:|---|
| hub | 189 | 159 | 15 | 22 Oct–2 Nov (futures to Jul 2027) |
| slate | 148 | 148 | 15 | 22–27 Oct |
| board | 207 | 167 | 13 | 22 Oct–2 Nov (futures to Jul 2027) |
| verified | 118 | 94 | 13 | 22 Oct–2 Nov (futures to Jul 2027) |
| forward | 93 | 77 | 3 | 23 Oct–2 Nov |

Total 755 rows. De-duplication produced **312 unique fixtures**; **208** of them appear
in two or more layers. One hub row (`grey-689570`) has no individual representative: it
collapses into a greyhound fixture that another hub row already defines. This is recorded
on the flagged page.

## 3. Result

| Metric | Value |
|---|---:|
| Fixtures | 312 |
| Originated (3 markets) | 279 |
| Deliberately unlined | 33 |
| High confidence | 15 |
| Medium | 129 |
| Low | 135 |
| Sports | 17 |
| Excluded-sport leaks | 0 |

Per sport: ice hockey 95, basketball 49, rugby union 31, tennis 28, darts 18, handball 12,
motor racing 11, volleyball 9, Aussie rules 9, snooker 8, rugby league 8, eSports 8,
baseball 7, golf 5, Gaelic football 5, greyhounds 5, cricket 4.

Layer used for the surviving row: hub 147, board 73, slate 53, verified 39. The largest
overlaps are ice hockey (82), basketball (39) and rugby union (31).

## 4. The rule, and why only 15 high picks

High = model probability **≥ 0.70** *and* fair decimal **1.40–101.00** (the brief's
−250…+10000 band). Because 1/0.70 = 1.4286, the overlap of "≥70%" with "no shorter than
−250" is only **70.0–71.4%**. Everything stronger than 71.4% is priced shorter than −250
and is graded **medium** with the explicit reason "outside the focus band"; everything
between 60% and 70% is medium; below 60% is low.

This is why the consolidated desk reports 15 highs where the hub claimed 25 and the board
claimed 42. Those layers used 65% thresholds or price-only bands.

## 5. Corrections applied (each has a source link on `/final/flagged.html`)

| ID | Correction | Evidence |
|---|---|---|
| C-01 | Golf: "Bank of Utah Championship" (finished 4 Oct) replaced by the **Butterfield Bermuda Championship**, Port Royal GC, 22–25 Oct, left unlined | pgatour.com tournament page R2026528 |
| C-02 | Darts: slate duplicated `pdc-32330` as Noppert v **Edhouse**; the duplicate was dropped. **Bunting qualified 28th on £43,000; Edhouse did not qualify** | dartsnews / Sporting News / dartsking listings |
| C-03 | Tennis: Fils quoted at #22 / 2,050 points in the inherited text; the captured 2026-10-19 list has **#10 / 3,325** | atptour.com rankings page (captured) |
| C-04 | NHL: Pastrnak quoted at 4G/8A; the official game page shows **6 points** | nhl.com GameCenter NSH@BOS |
| C-05 | NHL: Josi quoted at 8 assists; official page shows **6 assists** | nhl.com GameCenter NSH@BOS |
| C-06 | All prices recomputed as **1/p**; this removed a field-misalignment that printed the Pro D2 draw at 1.37 instead of 37.31, and 60+ rounding drift rows | data/final/matches.json |
| C-07 | Synthetic slate "book_dec/book_am" columns (4.5% overround on the layer's own price) were **not** carried into the consolidated table | slate methodology |

## 6. Rejected / reversed findings

- **"Bunting withdrew" is false.** It was recorded in an earlier session and is now
  reversed: Bunting qualified (28th, £43,000), Edhouse missed out. Multiple independent
  dated listings publish Noppert v Bunting for Thursday 22 October, 19:00 Dortmund.
- **"Golf = Bank of Utah" was stale.** The event ended on 4 October; the October 22–25
  PGA Tour event is Bermuda.
- **"Noppert v Edhouse" (slate)** cannot stand and was dropped rather than merged.

## 7. Verification actually performed on 2026-10-22

| Source | Confirmed |
|---|---|
| `api-web.nhle.com/v1/standings/2026-10-22` (standingsDateTimeUtc 08:27:34Z) | CAR 8-2-1, 17 pts, 42/27; VGK 8-3-0, 16; EDM 7-1-1, 15, 41/27; BOS 7-2-1, 15, 36/22 |
| `api-web.nhle.com/v1/skater-stats-leaders/20262027/2` | Kaprizov 11 G; McDavid 20 A; Q. Hughes 11 A; Matthews 8 G / 18 P; MacKinnon 10 A; Lehkonen 8 G; Karlsson 10 A; Draisaitl 8 G; Schmaltz 7 G |
| `nhl.com/gamecenter/nsh-vs-bos/.../2026020154` | Swayman 6-1-1 / 1.98 / .928; Pastrnak 6 pts; NSH 3-2-3; Josi 6 A; O'Reilly 4 G; Saros 3 W |
| `api-web.nhle.com/v1/club-stats/COL/20262027/2` | MacKinnon 6 G / 10 A / 16 P; Lehkonen 8 G / 11 P; Makar 3 G / 8 A |
| `stats.swehockey.se/.../Standings/20961` | Skellefteå 3rd, 19 pts, 5-3-2, 32:25, home 3-1-1; Djurgården 12th, 12 pts, away 0-2-3 |
| `pgatour.com/.../R2026528/overview` | Port Royal GC, 22–25 Oct 2026 |
| Darts draw listings (dartsnews, dave.sport, live-darts, dartn.de) | Noppert (5) v Bunting (28), Thu 22 Oct, Westfalenhallen |

Not re-read: Top 14 / Pro D2 and URC tables, ATP rankings page (client-rendered),
EHF, EuroLeague, NBA, MLB, F1, volleyball, AFLW, NRL, GAA, GBGB, and the PDC article body
(consent wall). Those rows carry their layer's capture stamp and an amber "inherited"
badge. No value was promoted without a page fetch.

## 8. Open items on the flagged page (17)

FR-01 five confidence vocabularies · FR-02 duplicate fixtures with conflicting prices ·
FR-03 stale golf row · FR-04 rejected Bunting correction · FR-05 Fils ranking ·
FR-06 Pastrnak total · FR-07 Josi assists · FR-08 synthetic book prices ·
FR-09 33 unlined fixtures · FR-10 196 rows whose source is a competition/player page ·
FR-11 16 of 30 prose facts not re-read · FR-12 3 fixtures already started · FR-13 two
cricket rows cite non-fixture ICC pages · FR-14 upstream layers left uncorrected ·
FR-15 exclusion filter · FR-16 PDC consent wall · FR-17 eSports pairings from Liquipedia
(8 rows published unlined and unverified).

## 9. Known unresolved issues

1. **`nhl-2026020164` (Seattle v Utah)** — the slate model prices Utah +1.5 at 70.9%,
   but the verified and board models price Utah's moneyline at 50.8%. The fixture is
   graded low rather than promoted on the weaker model. Documented, not hidden.
2. **`prod2-12065` (Soyaux-Angoulême)** — 69.5%, just below the 70% floor. Medium by rule.
3. **`shl-2026-1024-bif-rbk` (Brynäs v Rögle)** — the surviving row carries Brynäs at
   58.1%; the earlier scan's 69.95% Rögle price is on a non-surviving row.
4. **Three fixtures had already started** at the 08:22 snapshot (NZ v India cricket, two
   tennis ties). They stay visible for audit and are never presented as tips.
5. **ATP fixtures 902103 / 902133** link to player profiles, not tournament pages; the
   competition label is generic ("ATP Tour Indoor Hard"). Flagged as player-scope.
6. **eSports**: only a community wiki was captured. Rows are unlined, unverified, and
   linked to the official lolesports schedule instead.

## 10. Reproduce

```
python3 scripts/final_consolidate.py   # 312 fixtures, 15 high
python3 scripts/final_predictions.py   # 15 sourced write-ups
python3 scripts/final_flags.py         # 17 review items
python3 scripts/final_build.py         # 26 pages under /final/
python3 -m unittest tests.test_final   # 24 structural checks
```

CI runs the same four scripts and fails if `final/` or `data/final/` drifts.
