# Cross-Layer Integration & Verification Audit (`2026-10-21`)

## Summary of Published Layers on `buffedlizard55-lab.github.io/OLBG2`

1. **`/verified/` — Primary-Source Multi-Sport Origination Desk (`V1` + `V2`, session `4d77e99a`)**
   - **Coverage:** All **17 eligible OLBG sports** audited live on `2026-10-21`; all **8 excluded categories** (`soccer/football`, `horse-racing`, `american-football`, `boxing`, `ufc-mma`, `hurling`, `cycling`, `specials`) explicitly blocked.
   - **Scale:** **145 verified rows** (`102` originated lines across `9` sports: NHL `16`, NBA `11`, EuroLeague `10`, BKT EuroCup `4`, French Top 14 `7`, French Pro D2 `8`, URC `8`, EHF Champions League `12`, PDC European Championship `16`, ATP Singles `7`, WST Snooker `2`, MLB World Series Game 1 `1`, FIA Formula 1 `2`; plus `43` unconfirmed rows left strictly blank `—` and itemized on `/verified/flagged.html`).
   - **Predictions:** **17 unique, natural human-written `HIGH` confidence predictions** (`51–66` words each, zero boilerplate, citing verified official primary feeds).

2. **`/survey/` — All-Sports Inventory & Origination Layer (`V3`, remediated in `4d77e99a`)**
   - Added missing `Hurling` (`id 26`) and `UFC/MMA` (`id 27`) exclusions and included `Gaelic Football` (`id 25`), `Greyhounds` (`id 28`), and `Rugby League` (`id 10`, 3 live 2027 markets).
   - Replaced fabricated Top 14 figures and third-party Cricinfo/ESPN/Wikipedia citations with official LNR (`top14.lnr.fr`), URC (`stats.unitedrugby.com`), PDC (`pdc.tv`), WST (`wst.tv`), and MLB (`statsapi.mlb.com`) feeds (`0` non-official URLs remaining in `official_source_audit.py`).

3. **`/site/` — Evidence Desk v2 (`V3b`, updated in `4d77e99a`)**
   - Updated Buffalo Sabres live goal leader in `nhl-2026020152` from `Tage Thompson: 3 goals` to `Tage Thompson: 5 goals; Zach Benson: 6 assists` per `api-web.nhle.com/v1/score/2026-10-21` and rebuilt `/site/`.

4. **`/` — Root Dashboard (owned by `e3c5f898`)**
   - Preserved untouched per `COORDINATION.md` lock discipline; cross-linked seamlessly via `integration.html`.
