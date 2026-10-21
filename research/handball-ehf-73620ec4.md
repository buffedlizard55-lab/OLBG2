# Handball capture and verification — session `arena/73620ec4-olbg2`

**Captured:** 2026-10-21, 07:06–07:45 UTC
**Competition:** EHF Champions League Men 2026/27, Group Phase round 5
**Official sources**

| Ref | Source | URL | What it verified |
|---|---|---|---|
| S33 | EHF Champions League Men — matches page | <https://ehfcl.eurohandball.com/men/2026-27/matches/> | All 12 fixtures on 21–22 October: pairing, date, published throw-off time and timezone label, EHF match id, detail link |
| S34 | EHF Champions League Men — standings | <https://ehfcl.eurohandball.com/men/2026-27/standings/> | Groups A–F: games played, W-D-L, goals for, goals against, goal difference and points for all 24 clubs |
| S36 | EHF match detail, HC Zagreb v Paris Saint-Germain | <https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101032/HCZagreb-ParisSaintGermain/> | Confirms "Wed Oct 21, 2026 18:45 (CEST)", venue Arena Zagreb, Zagreb (CRO), Group Phase |
| S31 | OLBG handball hub (discovery only) | <https://www.olbg.com/betting-tips/Handball/20> | Event discovery and the timezone/name findings F24, F25 |

The EHF standings page was read twice (groups A–B, then C–F) in the same capture window and the numbers were
identical in both reads. No other source is used for any handball number on the site.

## Line-by-line fixture verification

Every row below was read from the EHF matches page (S33) and paired against that group's standings row (S34).
"Time" is the time exactly as EHF publishes it (CEST). UTC is a computed conversion, flagged as such in
`data/inputs/handball_ehf.json` → `meta.time_note`.

| # | EHF match id | Date | Time (CEST) | Home | Away | Group | Home record (W-D-L, GF:GA, Pts) | Away record (W-D-L, GF:GA, Pts) | Originated? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 202711020101059 | 2026-10-21 | 18:45 | Dinamo Bucuresti | SAH - Aarhus | E | 0-1-3, 97:122, 1 | 2-1-1, 127:126, 5 | yes |
| 2 | 202711020101012 | 2026-10-21 | 18:45 | RK Partizan AdmiralBet | FC Porto | A | 0-0-4, 115:151, 0 | 1-0-3, 125:140, 2 | yes |
| 3 | 202711020101001 | 2026-10-21 | 18:45 | One Veszprém HC | Füchse Berlin | A | 4-0-0, 146:111, 8 | 3-0-1, 149:133, 6 | yes |
| 4 | 202711020101032 | 2026-10-21 | 18:45 | HC Zagreb | Paris Saint-Germain | C | 1-0-3, 117:130, 2 | 3-1-0, 154:128, 7 | yes |
| 5 | 202711020101017 | 2026-10-21 | 20:45 | HBC Nantes | HC Vardar 1961 | B | 3-0-1, 115:110, 6 | 0-0-4, 121:131, 0 | yes |
| 6 | 202711020101029 | 2026-10-21 | 20:45 | Aalborg Håndbold | RK Celje Pivovarna Laško | C | 3-1-0, 136:115, 7 | 0-0-4, 120:154, 0 | yes |
| 7 | 202711020101070 | 2026-10-21 | 20:45 | HC Kriens-Luzern | Industria Kielce | F | 2-0-2, 128:129, 4 | 2-0-2, 123:123, 4 | yes |
| 8 | 202711020101043 | 2026-10-22 | 18:45 | OTP Bank - PICK Szeged | GOG | D | 1-1-2, 139:136, 3 | 3-0-1, 145:139, 6 | yes |
| 9 | 202711020101019 | 2026-10-22 | 18:45 | MT Melsungen | Orlen Wisla Plock | B | 2-0-2, 110:112, 4 | 3-0-1, 115:108, 6 | yes |
| 10 | 202711020101049 | 2026-10-22 | 20:45 | Barça | Montpellier Handball | E | 4-0-0, 137:104, 8 | 1-0-3, 116:125, 2 | yes |
| 11 | 202711020101041 | 2026-10-22 | 20:45 | Sporting Clube de Portugal | IFK Kristianstad | D | 3-1-0, 149:125, 7 | 0-0-4, 122:155, 0 | yes |
| 12 | 202711020101064 | 2026-10-22 | 20:45 | Kolstad Håndball | SC Magdeburg | F | 0-0-4, 111:143, 0 | 4-0-0, 141:108, 8 | yes |

Checks applied to every row:

1. **Pairing** — both club names appear on the EHF matches page under the stated date and in the same group as
   the standings rows used for the model. Twelve fixtures = six groups × two matches, which matches the
   standings page's five completed rounds structure.
2. **Date** — each fixture's date group on S33 agrees with the date in the row.
3. **Time** — published time copied verbatim; the timezone label "CEST" is EHF's own.
4. **Strength input** — the five standings columns used (`gp`, `w`/`d`/`l`, `gf`, `ga`, `pts`) were read for that
   club from S34 and stored in `data/inputs/handball_ehf.json`.
5. **Venue** — only row 4 has a venue (Arena Zagreb), because only that match detail page was opened (S36). The
   other eleven are blank and listed as F26.

## What was originated

For each fixture the model produces seven prices: three-way match winner, a two-way handicap and a two-way match
total. Parameters are in `scripts/model.py` → `PARAMS` (`handball_shrink_k`, `handball_home_goals`,
`handball_overround`) and are recorded on every row. The score grid is renormalised after truncation; the first
build truncated at 45 goals and lost about 10% of the joint mass, which was caught by a probability check and
fixed before publication.

| Grade | Count | Fixtures |
|---|---|---|
| high | 5 | Zagreb v PSG, Aalborg v Celje, Barça v Montpellier, Sporting v Kristianstad, Kolstad v Magdeburg |
| medium | 4 | Dinamo v Aarhus, Partizan v Porto, Veszprém v Berlin, Nantes v Vardar |
| low | 3 | Kriens v Kielce, Szeged v GOG, Melsungen v Plock |

Five written predictions (one per high pick) are in `data/predictions.json`, each with a per-fact source list.

## Irregularities found (published on the Flagged for Review page)

| ID | Finding | Evidence |
|---|---|---|
| F24 | OLBG renders start times in the viewer's timezone, not the venue's | OLBG: "Today 12:45" for Zagreb v PSG; EHF: 18:45 CEST = 16:45 UTC = 12:45 US Eastern |
| F25 | OLBG club names differ from EHF registered names | RK Zagreb/HC Zagreb, KS Kielce/Industria Kielce, PSG Handball/Paris Saint-Germain, Skanderborg Handbold/SAH - Aarhus, Veszprem/One Veszprém HC |
| F26 | Eleven of twelve venues blank | EHF fixtures list has no venue field; only S36 was opened |

F12 (previously "OLBG displayed times do not map to one timezone") is closed with F24 as the explanation. F21
("Handball — events exist, none published") is closed by this capture.

## OLBG event ids seen for these fixtures (for manual review, not linked on the site)

| OLBG event id | OLBG label | EHF fixture |
|---|---|---|
| 12053 | RK Zagreb vs PSG Handball | HC Zagreb v Paris Saint-Germain |
| 12055 | Veszprem vs Fuchse Berlin | One Veszprém HC v Füchse Berlin |
| 12050 | Nantes vs HC Vardar | HBC Nantes v HC Vardar 1961 |
| 12044 | Aalborg Handbold vs RK Celje | Aalborg Håndbold v RK Celje Pivovarna Laško |
| 12052 | RK Partizan vs FC Porto | RK Partizan AdmiralBet v FC Porto |
| 12047 | HC Kriens Luzern vs KS Kielce | HC Kriens-Luzern v Industria Kielce |
| 12048 | Kolstad vs SC Magdeburg | Kolstad Håndball v SC Magdeburg |
| 12054 | Sporting CP vs IFK Kristianstad | Sporting Clube de Portugal v IFK Kristianstad |
| 12045 | Dinamo Bucuresti vs Skanderborg Handbold | Dinamo Bucuresti v SAH - Aarhus (naming differs, not linked) |

OLBG listed no counterpart on the first page segment for Szeged v GOG, Melsungen v Plock or Barça v Montpellier.

## Reproduce

```sh
python3 scripts/model.py        # data/inputs/handball_ehf.json -> data/matches.json
python3 scripts/build_site.py   # regenerates sports/handball.html and the shared pages
python3 -m unittest discover -s tests -v
```
