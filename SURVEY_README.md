# OLBG2 — All-Sports Survey & Primary-Source Origination Overview

Reverse-engineering of [OLBG.com](https://www.olbg.com/) covering all **17 eligible sports** while explicitly excluding **soccer, football, horse racing, american football, boxing, ufc, mma, hurling, cycling, and specials**.

- **Verified Multi-Sport Origination Desk (`/verified/`):** <https://buffedlizard55-lab.github.io/OLBG2/verified/> (`145` verified rows, `102` originated multi-market lines across `9` sports, `17` bespoke human `HIGH`-confidence write-ups, `43` unconfirmed rows left blank & flagged)
- **All-Sports Survey Layer (`/survey/`):** <https://buffedlizard55-lab.github.io/OLBG2/survey/> (`145` inventoried events across all `17` eligible sports, `26` originated lines, `5` human `HIGH`-confidence predictions, `0` third-party sources)
- **Root Dashboard (`/`):** <https://buffedlizard55-lab.github.io/OLBG2/>

## Remediated Survey Headline Metrics (2026-10-21)

| Metric | Value |
| --- | --- |
| Taxonomy entries (`data/survey/sports.json`) | 25 (`17` eligible in scope · `8` excluded incl. `Hurling/26` & `UFC_MMA/27`) |
| Inventoried events across 17 eligible sports | 145 (`100%` paired with `official_fixture_source`) |
| Originated lines (`data/survey/lines.json`) | 26 (Top 14 R7, URC R4, PDC European Championship R1, WST NI Open R2, MLB WS G1) |
| High-confidence human predictions (`>= 30` words) | 5 (`P-01` to `P-05`, `54–70` words each, `0` third-party domains) |
| Unlined events left blank (`F-15`) | 119 |
| `official_source_audit.py` non-official URLs remaining | **0** (`events_needing_official_fixture_source: []`, `facts_needing_official_source_review: []`) |

## Reproduce Deterministically

```bash
python3 scripts/verified_seed.py
python3 scripts/verified_model.py
python3 scripts/verified_build.py
python3 scripts/survey_sync_inventory.py
python3 scripts/survey_lines.py
python3 scripts/survey_analyse.py
python3 scripts/survey_build.py
python3 scripts/survey_verify.py
python3 scripts/build_site.py
python3 scripts/integration_audit.py
python3 -m unittest discover -s tests -v
```
