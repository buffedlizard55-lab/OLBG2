> Preserved verbatim from branch `arena/1bb45081-olbg2` (PR #54, session arena/1bb45081) by the
> integration session arena/1352b77f-olbg2 when PR #54 was closed as superseded. The uniform
> odds-window gate this audit proposed is adopted in the published models (see VF-35); the
> narrative-archiving numbers below describe that branch's older five-layer dataset, not the
> current tree.

# Odds-window compliance audit and cross-layer remediation

- Session: `arena/1bb45081-olbg2`
- Date: 2026-10-22
- Scope: all five published layers (`/`, `/site/`, `/survey/`, `/live/`, `/verified/`)
- Status: remediated, all 66 unittests green, all layers byte-stable under the CI rebuild sequence

## 1. Finding

The project brief restricts high-confidence picks to selections whose odds sit
between **-250 and +10000 American** and whose model win probability is
**greater than 70%**. An audit of the committed layers on 2026-10-22 found that
every layer was still labelling heavy chalk as "high":

- 20 of 24 `/verified/` high picks were priced shorter than -250 (down to -5000).
- 7 of 9 root-dashboard narratives sat outside the window (or below 70%).
- All 4 `/live/` URC picks (76.2%–85.9%) were chalk between -323 and -625.
- All 5 `/survey/` picks (76.8%–95.1%) were chalk between -333 and -2000.
- 3 of 4 `/site/` desk "high" rows were below the 70% probability floor.

The old layer rules used disparate thresholds (verified >=72% fair probability;
desk >=13 pts model edge plus evidence; live >=62% probability; survey >=72%
with tier/form gates; NHL root >=65% with a games-played gate). None tested the
odds window.

## 2. The uniform rule

A selection is labelled **high** only when **both** hold:

1. model probability `p >= 0.70`; and
2. its fair, no-vig American price
   `A(p) = round(-100 / (1/p - 1))` (for `p > 0.5`) lies in `[-250, +10000]`.

Boundary arithmetic: -250 American = decimal 1.40 = 71.43% implied probability,
so the effective high band is **70.0% <= p <= 71.43%**. The +10000 leg
(decimal 101.00) never binds for a >70% favourite.

The gate is evaluated on **fair no-vig prices** (`1/p`) uniformly across
layers, so the rule is a deterministic function of the published model
probability. Market rows still display each layer's documented model
overround separately (e.g. Paris SG handball: fair 1.42 / -238 vs published
1.37 / -270); this distinction is disclosed on the root picks page and in
flag F28.

Each layer keeps its own existing evidence/sample gates; the window is an
additional conjunction, never a relaxation. Selections that fail are capped at
medium (or low), and every displaced narrative is moved verbatim — with its
facts and source links — into a per-layer archive file. Nothing is deleted.

## 3. Per-layer results

### Verified desk (`/verified/`, 155 rows, 112 originated)

- 4 active highs, all inside the band:

| ID | Sport | Probability | Fair decimal | American |
|---|---|---|---|---|
| `nhl-2026020162` | Ice hockey (NHL, MIN @ CGY) | 70.82% | 1.41 | -244 |
| `prod2-12066` | Rugby union (Pro D2, Aurillac v Nevers) | 70.53% | 1.42 | -238 |
| `urc-292609` | Rugby union (URC, Connacht v Zebre) | 70.25% | 1.42 | -238 |
| `ehfcl-202711020101001` | Handball (Veszprém v Füchse Berlin) | 71.03% | 1.41 | -244 |

- 20 narratives archived in `data/verified/archived_predictions.json`
  (American range -5000…-256), each with `archive_reason`, `regraded_to`,
  fair decimal and American fields.
- New flags: **VF-11** (high, the 20 chalk regrades + rule + four compliant
  picks), **VF-12** (medium, Veszprém v Berlin had already completed 39-35 on
  21 Oct; retained as snapshot reasoning with an on-card note), **VF-13**
  (low, two venues newly verified from official pages: Stade Jean Alric,
  Aurillac; One Veszprem Arena).

### Root dashboard (`/`, 47 fixtures, 45 originated)

- Active highs: `nhl-2026020159` NY Islanders (71.18%, fair 1.40 / **-250**,
  inclusive boundary) and `ehfcl-202711020101032` Paris SG handball
  (70.19%, fair 1.42 / -238).
- 7 archives in `data/predictions_archived.json`: handball chalk Aalborg
  (-556), Sporting (-588), Barça (-370), Magdeburg (-526); NHL sub-70% picks
  Buffalo (65.4%, -189), Boston (65.3%, -189), Minnesota (68.9%, -222).
- Flags **F27** (high) and **F28** (medium, fair-vs-published price
  disclosure). Stale flag meta counts corrected (24 open / 4 resolved).

### Live slate (`/live/`, 11 fixtures)

- 0 active highs; 8 medium / 3 low.
- 4 URC archives in `data/live/archived_predictions.json`: Glasgow -417
  (80.9%), Scarlets -323 (76.2%), Leinster -625 (85.9%), Munster -556
  (84.5%). The picks page renders an explicit empty-state card rather than
  inventing a high.
- Flag **L12** added to `data/live/flags.json` (12 flags total).

### Survey (`/survey/`, 26 modelled rows)

- 0 active highs; 5 archives in
  `data/survey/archived_predictions.json`: Toulouse -2000 (95.1%),
  Bulls -714 (87.7%), Stormers -526 (83.8%), Luke Littler -526 (83.7%),
  Nathan Aspinall -333 (76.8%).
- `survey_analyse.py` now emits a confidence note on every window-capped row
  and flag **F-16**; the `survey_verify.py` high==prediction set invariant
  still holds (both sets empty).

### Evidence desk v2 (`/site/`, 25 fixtures)

- 1 active high: `nhl-2026020162` Minnesota @ Calgary (70.1%, fair 1.43 /
  -233), which retains its narrative.
- 4 archives in `data/desk/archived_picks.json`: Buffalo (65.0%, -185),
  Boston (68.6%, -217), Dallas (64.7%, -182) regraded medium; the
  Florida/Pittsburgh narrative (54.5%, low) archived because written
  predictions now accompany window-compliant highs only.
- Flag **flag-odds-window** (10 desk flags total); desk source-register
  discipline preserved (only registered hosts cited).

## 4. Code and test changes

- Window helpers (`fair_decimal`, `american_from_decimal`,
  `window_high_eligible`) added to `scripts/verified_model.py`,
  `scripts/model.py`, `scripts/live_model.py`, `scripts/survey_analyse.py`,
  and `scripts/engine.py`, each with identical boundary math.
- Builders render archive sections and empty states: `verified_build.py`,
  `build_site.py`, `live_build.py`, `survey_build.py`, `build.py`.
- `scripts/integration_audit.py` discloses every archived narrative fact and
  records the cross-layer remediation row.
- Tests grew from 60 to 66: window-math and archive-coverage tests in
  `test_verified_pipeline.py`, `test_live.py`, `test_build.py`;
  `test_integration.py` counts facts across active + archived survey files.

## 5. Verification trail (official primary sources read this session)

- NHL standings/schedule: `api-web.nhle.com/v1/standings/now` (2026-10-21),
  `api-web.nhle.com/v1/schedule/2026-10-22` — MIN @ CGY game 2026020162.
- LNR Pro D2: `prod2.lnr.fr/classement` and
  `prod2.lnr.fr/feuille-de-match/2026-2027/j8/12066-aurillac-nevers`
  (23 Oct 19:30, Stade Jean Alric).
- URC: `stats.unitedrugby.com/match-centre/table/2026-27` and match centre
  292609 (Connacht v Zebre, Dexcom Stadium, 23 Oct 14:45).
- EHF: `ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101001/...`
  (final 39:35, One Veszprem Arena, 5,090 spectators) and the 2026-27
  standings (Veszprém 5-0, +39).

## 6. Reproducibility

Running the `.github/workflows/pages.yml` sequence end to end
(verified seed/model/build, live model/build, desk build, survey
sync/lines/analyse/build/verify, root build_site, integration audit, full
unittest) produces no uncommitted diff on any generated path. Probabilities
and fair prices in all data files are unchanged; only confidence labels and
narrative placements changed.
