#!/usr/bin/env python3
"""Seed the /compass/ desk data from the committed capture files.

Reads: scripts/compass_data_olbg.py (raw OLBG hub capture), scripts/compass_data_fixtures.py
(fixture records + fact source registry). Writes: data/compass/{olbg.json, fixtures.json,
sources.json, flagged.json, captures/olbg/hubs.json, captures/official/manifest.json}.
Deterministic: same inputs, byte-identical outputs.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "compass"

from compass_data_olbg import CAPTURE, LISTINGS  # noqa: E402
from compass_data_fixtures import FIXTURES, S  # noqa: E402

AS_OF = "2026-10-24T22:45:00Z"
SHOWN_DATE = "24 October 2026"
SESSION = "arena/9f424dec-olbg2"

# Which fixture facts are inherited from the 17:35Z official capture (facts_inherited)
INHERITED_KEYS = {
    "now_4a8390fe", "icc_pak_87", "icc_sl_chase", "icc_nz_india", "ecb_triseries",
    "opel_hbl", "lnh_starligue", "legavolley_tre", "legavolley_per", "prem_r4",
    "munster_gaa", "nrl_rlwc",
}
INHERITED_URLS = {
    "now_4a8390fe": "data/now/fixtures.json (official capture committed 2026-10-24T17:35Z by arena/4a8390fe-olbg2)",
    "icc_pak_87": S["icc_pak_87"],
    "icc_sl_chase": S["icc_sl_chase"],
    "icc_nz_india": S["icc_nz_india"],
    "ecb_triseries": S["ecb_triseries"],
    "opel_hbl": S["opel_hbl"],
    "lnh_starligue": S["lnh_starligue"],
    "legavolley_tre": S["legavolley_tre"],
    "legavolley_per": S["legavolley_per"],
    "prem_r4": S["prem_r4"],
    "munster_gaa": S["munster_gaa"],
    "nrl_rlwc": S["nrl_rlwc"],
    "olbg_capture": "https://www.olbg.com/betting-tips (hub capture, this session)",
    "now_4a8390fe": "data/now/fixtures.json",
}

SOURCES = [
    {"key": "olbg_capture", "name": "OLBG hub capture (this session)", "url": CAPTURE["hubs"]["Ice Hockey"],
     "captured_utc": AS_OF, "note": "All 15 sport hubs fetched 22:25-22:45Z via the fetch tool; displayed times are US Eastern (verified against the NHL schedule)."},
    {"key": "nhl_standings", "name": "NHL.com standings", "url": S["nhl_standings"], "captured_utc": "2026-10-24T22:40:00Z",
     "note": "2026-27 season standings at 22:25:30Z: records, GF/GA, home/road splits for 30 of 32 teams (Chicago, Vancouver not captured — flagged)."},
    {"key": "nhl_sched_24", "name": "NHL.com schedule Sat 24 Oct", "url": S["nhl_sched_24"], "captured_utc": "2026-10-24T22:42:00Z",
     "note": "Official 12-game slate with 7:00/9:00/10:00 PM EDT starts; two completed results (ANA 5-4 PHI; NJD 3-1 LAK). Bookmaker odds shown on the page were NOT used for our lines."},
    {"key": "nhl_sched_25", "name": "NHL.com schedule Sun 25 Oct", "url": S["nhl_sched_25"], "captured_utc": "2026-10-24T22:38:00Z",
     "note": "MTL vs WPG listed at a neutral site, 7:00 PM EDT (special-event-season game)."},
    {"key": "mlb_sched_ws", "name": "MLB StatsAPI World Series schedule", "url": S["mlb_sched_ws"], "captured_utc": "2026-10-24T22:33:00Z",
     "note": "2026 World Series: Game 2 (24 Oct, American Family Field) and Games 3-4 at Tropicana Field with probable pitchers."},
    {"key": "mlb_al", "name": "MLB StatsAPI AL standings 2026", "url": S["mlb_al"], "captured_utc": "2026-10-24T22:36:00Z",
     "note": "Regular-season records and splits: Tampa Bay 98-64 (home 55-26, road 43-38)."},
    {"key": "mlb_nl", "name": "MLB StatsAPI NL standings 2026", "url": S["mlb_nl"], "captured_utc": "2026-10-24T22:45:00Z",
     "note": "Regular-season records and splits: Milwaukee 103-59 (home 55-26, night 68-35, W5)."},
    {"key": "mlb_pitchers", "name": "MLB StatsAPI Game 2 starters", "url": S["mlb_pitchers"], "captured_utc": "2026-10-24T22:36:00Z",
     "note": "Rasmussen (TB) 2.67 ERA / 0.91 WHIP; Henderson (MIL) 2.47 ERA / 0.84 WHIP, 2026 season."},
    {"key": "mlb_pitchers_g3", "name": "MLB StatsAPI Game 3 starters", "url": S["mlb_pitchers_g3"], "captured_utc": "2026-10-24T22:50:00Z",
     "note": "Gasser (MIL) 3.87 ERA / 1.19 WHIP; Peralta (TB) 3.25 ERA / 1.01 WHIP with Tampa Bay in 2026."},
    {"key": "nba_standings", "name": "NBA.com standings 2026-27", "url": S["nba_standings"], "captured_utc": "2026-10-24T22:35:00Z",
     "note": "New-season standings (1-2 games played each). 2025-26 prior-season records are behind a JS selector and could not be captured — flagged; NBA confidence capped at medium."},
    {"key": "atp_almaty", "name": "ATP Almaty daily schedule (day 9, finals)", "url": S["atp_almaty"], "captured_utc": "2026-10-24T22:39:00Z",
     "note": "Medvedev (1) v Basilashvili (Q) final, not before 14:00 local."},
    {"key": "atp_current", "name": "ATP Tour live scores", "url": S["atp_current"], "captured_utc": "2026-10-24T22:39:00Z",
     "note": "Almaty SFs (Medvedev def. Bublik 6-3 ret.; Basilashvili def. Tsitsipas 6-4 6-7 6-3), Lyon SFs (Musetti def. Cobolli 4-6 6-2 7-5; Fritz def. Paul 6-3 7-5), Brussels SFs."},
    {"key": "wta_tournaments", "name": "WTA official tournament update feed", "url": S["wta_tournaments"], "captured_utc": "2026-10-24T22:41:00Z",
     "note": "Draw/schedule pages are client-side rendered; the feed confirms Osaka (Kinoshita Group Japan Open) and Tokyo (Toray Pan Pacific Open) as the current WTA Asia events. Individual WTA match pairings therefore unverified — flagged."},
    {"key": "top14_cal", "name": "LNR Top 14 calendar J7", "url": S["top14_cal"], "captured_utc": "2026-10-24T22:39:00Z",
     "note": "Saturday J7 results; La Rochelle v Bordeaux-Begles dimanche 25 octobre 21h05 local."},
    {"key": "top14_class", "name": "LNR Top 14 standings (after J6)", "url": S["top14_class"], "captured_utc": "2026-10-24T22:45:00Z",
     "note": "La Rochelle 4th 18 pts +9; Bordeaux-Begles 3rd 19 pts +64; Toulouse 1st 28 pts."},
    {"key": "galway_gaa", "name": "Galway GAA official fixture changes", "url": S["galway_gaa"], "captured_utc": "2026-10-24T22:45:00Z",
     "note": "SFC County Final Sunday 25 Oct 16:00: Maigh Cuilinn vs Salthill-Knocknacarra (Pearse Stadium). OLBG lists 'Moycullen' — data error flagged."},
    {"key": "pdc_ec", "name": "PDC official news: Finals Day recap", "url": S["pdc_ec"], "captured_utc": "2026-10-24T22:50:00Z",
     "note": "Round Two results (Price 10-4 Menzies; Bunting 10-3 Huybrechts; Ross Smith 10-7 Heta; Woodhouse 10-6 van Veen; Littler 10-5 Aspinall, avg 114.47); quarter-finals on Finals Day Sunday 25 Oct."},
    {"key": "pdc_ec_r1", "name": "PDC official news: round one", "url": S["pdc_ec_r1"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Littler 6-3 O'Connor (avg 105.05, six 180s); Aspinall 6-3 Reyes (inherited 17:35Z capture)."},
    {"key": "csa_pro20", "name": "Cricket South Africa upcoming fixtures (official)", "url": S["csa_pro20"], "captured_utc": "2026-10-24T22:48:00Z",
     "note": "Pro20 Cup 25 Oct: Boland v Titans (Boland Park), NWD v NC Heat (Senwes Park), Tuskers v WP (City Oval Pietermaritzburg), 13:00 SAST each."},
    {"key": "rugby_au_a", "name": "Rugby Australia: Australia A team confirmed", "url": S["rugby_au_a"], "captured_utc": "2026-10-24T23:00:00Z",
     "note": "Australia A v USA Eagles, Geodis Park Nashville, Sunday 25 Oct 9:00am AEDT (= 22:00Z 24 Oct); nine Wallabies in the 23."},
    {"key": "ecb_triseries", "name": "ECB: how to watch England v Pakistan/Sri Lanka tri-series", "url": S["ecb_triseries"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Pakistan v England 4th ODI, Gaddafi Stadium Lahore, 25 Oct 08:00 GMT (inherited)."},
    {"key": "icc_sl_chase", "name": "ICC: Sri Lanka's 430 chase", "url": S["icc_sl_chase"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "England 429/4 (Brook 202, fastest ODI double century); England winless in three (inherited)."},
    {"key": "icc_pak_87", "name": "ICC: Pakistan's 87-run win over England", "url": S["icc_pak_87"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Match 2 of the tri-series; Arafat Minhas five-forty (inherited)."},
    {"key": "icc_nz_india", "name": "ICC: India take 2-0 lead over New Zealand", "url": S["icc_nz_india"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Series position ahead of the 3rd T20I (inherited)."},
    {"key": "opel_hbl", "name": "opel-hbl.de Rhein-Neckar Lowen team page", "url": S["opel_hbl"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Bundesliga Matchday 10: SC Magdeburg v RNL 13:00 UTC (inherited)."},
    {"key": "lnh_starligue", "name": "LNH Daikin StarLigue", "url": S["lnh_starligue"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "PSG v Saint-Raphael, J8 (inherited)."},
    {"key": "legavolley_tre", "name": "Lega Pallavolo (SuperLega)", "url": S["legavolley_tre"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Round 2 fixtures (inherited)."},
    {"key": "legavolley_per", "name": "Lega Pallavolo (Perugia round)", "url": S["legavolley_per"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Perugia v Pordenone (inherited)."},
    {"key": "prem_r4", "name": "Premiership Rugby Round 4 fixtures", "url": S["prem_r4"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Harlequins v Saracens (inherited)."},
    {"key": "munster_gaa", "name": "Munster GAA Cork Premier SFC Final", "url": S["munster_gaa"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "St Finbarrs v Nemo Rangers final (inherited)."},
    {"key": "nrl_rlwc", "name": "NRL.com RLWC 2026 draw", "url": S["nrl_rlwc"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Round 2: Australia v Fiji 25 Oct (inherited; context only — not on the OLBG hub at capture)."},
    {"key": "pgatour", "name": "PGA TOUR leaderboard", "url": S["pgatour"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Bermuda Championship round 4 in play (context; no OLBG golf tips at capture)."},
    {"key": "europeantour", "name": "DP World Tour Genesis Championship", "url": S["europeantour"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Round 4 in play (context; no OLBG golf tips at capture)."},
    {"key": "f1_us", "name": "Formula 1 United States Grand Prix page", "url": S["f1_us"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Round 18, 25 Oct 20:00Z (context; no OLBG motor racing tips at capture)."},
    {"key": "wst_ni", "name": "World Snooker Tour matches", "url": S["wst_ni"], "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Northern Ireland Open final 25 Oct 13:00Z, Kyren Wilson (context; no OLBG snooker tips at capture)."},
    {"key": "gbgb", "name": "Greyhound Board of Great Britain", "url": S["gbgb"], "captured_utc": "2026-10-24T22:48:00Z",
     "note": "No public online racecard for the 11:04 Doncaster; OLBG runner list used (flagged)."},
    {"key": "now_4a8390fe", "name": "Inherited official capture (session arena/4a8390fe-olbg2, 17:35Z)",
     "url": "data/now/fixtures.json", "captured_utc": "2026-10-24T17:35:00Z",
     "note": "Same-day official capture committed earlier by the /now/ desk; facts inherited and re-corroborated where this session re-fetched the same source."},
]


def olbg_rows():
    rows = []
    for event_id, sport, event, disp, market, selection, tips, pct in LISTINGS:
        rows.append({
            "event_id": event_id, "sport": sport, "event": event, "displayed_time": disp,
            "market": market, "selection": selection, "tips": tips,
            "pct": (int(pct) if pct else None),
            "url": f"https://www.olbg.com/betting-tips/event/{event_id}",
            "hub": CAPTURE["hubs"][sport],
        })
    return rows


def fixture_rows():
    olbg = {r["event_id"]: r for r in olbg_rows()}
    # map fixture id -> olbg event id
    mapping = {
        "nhl-tor-edm": "200010", "nhl-sjs-bos": "200007", "nhl-car-stl": "200002",
        "nhl-vgk-clb": "200001", "nhl-nyr-ott": "200008", "nhl-buf-was": "200003",
        "nhl-nsh-pit": "200006", "nhl-tbl-uta": "200009", "nhl-det-cgy": "200004",
        "nhl-min-sea": "200005", "nhl-mtl-wpg": "200074",
        "mlb-g2": "160792",
        "cri-pak-eng-odi4": "188838", "cri-tor-van": "188845", "cri-nwd-nch": "188851",
        "cri-tus-wp": "188850", "cri-es-sae": "188848", "cri-bol-tit": "188849",
        "cri-indw-zimbw": "188847", "cri-nz-ind-t20i3": "188852", "cri-nam-irl-odi3": "188854",
        "cri-sa-aus": "188835", "cri-out-wc27": "182606", "cri-out-bblw26": "187184",
        "cri-out-bbl26": "187503", "cri-out-sa20": "187504", "cri-out-blast27": "188350",
        "rug-usa-ausa": "609583", "rug-har-sar": "609571", "rug-lar-ubb": "609554",
        "rug-out-six27": "609013",
        "gae-sal-mcg": "3532", "gae-stf-nem": "3530", "gae-kan-eoc": "3531",
        "gae-frc-kil": "3537", "gae-out-aic27": "3327",
        "gry-don-1104": "690043",
        "dar-rsm-lwk": "32408", "dar-prc-bun": "32407", "dar-out-ec26": "32338", "dar-out-pdc27": "26023",
        "ten-med-bas": "902251", "ten-mus-fri": "902253", "ten-ryb-fer": "902207",
        "ten-krueg-sin": "902171",
        "ten-eal-sto": "902175", "ten-uch-mer": "902173", "ten-fer-sak": "902172",
        "ten-waw-leh": "902232", "ten-mic-vdz": "902240", "ten-vac-nav": "902237",
        "ten-she-ruu": "902231", "ten-kym-rin": "902234", "ten-djo-hum": "902233",
        "ten-fri-tsi": "902239", "ten-run-hal": "902236", "ten-fok-ber": "902235",
        "ten-tab-jod": "902238", "ten-hur-fil": "902247",
        "han-rnl-mag": "12092", "han-psg-sra": "12084",
        "han-yis-ham": "12152", "han-ali-adl": "12106", "han-mag-kri": "12136",
        "han-gra-pug": "12102", "han-lit-bel": "12125", "han-lux-gbr": "12126",
        "han-amo-mal": "12144", "han-ber-ham": "12087", "han-fuc-par": "12128",
        "han-fuc-wet": "12089", "han-fol-kri": "12154", "han-ksk-kol": "12132",
        "han-ska-tth": "12075", "han-hif-ikc": "12148", "han-mon-sar": "12081",
        "han-lug-sko": "12149", "han-ali-onn": "12147", "han-gum-fln": "12095",
        "ice-serv-zsc": "200021", "ice-fra-wol": "200037", "ice-schw-ber": "200041",
        "ice-bern-lug": "200018", "ice-vie-grz": "200043", "ice-kre-muc": "200039",
        "ice-ise-nur": "200038", "ice-aug-str": "200036", "ice-bre-erc": "200040",
        "nba-mil-phi": "536111", "nba-bkn-cle": "536112", "nba-sa-dal": "536114",
        "nba-was-chi": "536113", "nba-hou-atl": "536115", "nba-no-den": "536116",
        "nba-gs-phx": "536118", "kbl-gas-thr": "536125", "kbl-any-won": "536126",
        "kbl-seo-suw": "536127",
        "vol-bru-pra": "37003", "vol-cis-tre": "36994", "vol-lud-rot": "37014",
        "vol-pad-civ": "36995", "vol-per-por": "36997", "vol-vak-gal": "37110",
        "vol-ham-mun": "37059", "vol-con-val": "37076", "vol-orp-kng": "37107",
        "vol-chl-res": "36965", "vol-mnz-ver": "36996", "vol-bes-goz": "37108",
        "vol-kuz-nil": "37109", "vol-ara-thy": "37111", "vol-ilb-afy": "37112",
        "vol-man-zer": "37113", "vol-tou-nic": "37054", "vol-fen-ecz": "37114",
        "vol-mon-cru": "37101", "vol-nor-ren": "37102",
        "rl-out-soo27": "2695857", "rl-out-sl27": "2801554", "rl-out-nrl27": "2801600",
    }
    rows = []
    for f in FIXTURES:
        eid = mapping.get(f["id"])
        o = olbg.get(eid) if eid else None
        inherited = any(k in INHERITED_KEYS for _, _, k in f["facts"])
        row = {
            "id": f["id"], "sport": f["sport"], "competition": f["competition"],
            "home": f["home"], "away": f["away"], "start_utc": f["start_utc"],
            "start_display": f["start_display"], "venue": f["venue"],
            "official_url": f["official_url"], "blank_reason": f["blank"],
            "facts_inherited": inherited,
            "facts_capture": "2026-10-24T17:35Z (data/now)" if inherited else "2026-10-24T22:30Z (this session)",
            "olbg_listed": o is not None,
            "olbg_listing": o,
            "inputs": f["inputs"],
            "facts": [
                {"claim": c, "value": v, "source_key": k,
                 "source_url": INHERITED_URLS.get(k, S.get(k, "")),
                 "captured_utc": "2026-10-24T17:35:00Z" if k in INHERITED_KEYS else "2026-10-24T22:45:00Z"}
                for c, v, k in f["facts"]
            ],
        }
        rows.append(row)
    return rows


FLAGS = [
    {"id": "cmp-01", "severity": "data-error", "sport": "Gaelic Sports",
     "fixture_id": "gae-sal-mcg",
     "text": "OLBG lists the Galway SFC final as 'Moycullen v Salthill-Knocknacarra'. The official Galway GAA schedule (published 23 Oct) has Maigh Cuilinn v Salthill-Knocknacarra at 16:00 on 25 Oct. The desk uses the official pairing.",
     "source": S["galway_gaa"]},
    {"id": "cmp-02", "severity": "time", "sport": "Rugby Union", "fixture_id": "rug-usa-ausa",
     "text": "OLBG displayed the USA v Australia A kickoff as 19:00 (Eastern view, = 23:00Z). Rugby Australia states 9:00am AEDT Sunday 25 Oct = 22:00Z. Official time used; OLBG is one hour off.",
     "source": S["rugby_au_a"]},
    {"id": "cmp-03", "severity": "time", "sport": "Ice Hockey",
     "fixture_id": "nhl-det-cgy,nhl-min-sea,nhl-tbl-uta",
     "text": "OLBG display times for the late NHL games (22:07/23:07 in the Eastern view) sit about 1h07m from the official 9:00/10:00 PM EDT starts, while the 7:00 PM EDT games show a +7-minute offset (19:07). Official NHL start times are used throughout.",
     "source": S["nhl_sched_24"]},
    {"id": "cmp-04", "severity": "data-quality", "sport": "Ice Hockey",
     "fixture_id": "nhl-car-stl,nhl-nyr-ott,nhl-det-cgy",
     "text": "OLBG tip distributions diverge sharply from the official standings for several NHL games (Carolina 10/11 away vs a 5-4-1 St Louis; New York Rangers 6/7 despite a 1-4-1 road record; Calgary 4/6 despite 3-6 with a -19 goal differential). Our lines follow the official statistics, not the tip share.",
     "source": S["nhl_standings"]},
    {"id": "cmp-05", "severity": "data-quality", "sport": "Handball",
     "fixture_id": "han-psg-sra,han-mag-kri,han-fuc-par,han-ksk-kol",
     "text": "On several top-tier handball fixtures (including a PSG home game and EHF Champions League qualifiers) the most-tipped OLBG selection is 'Tie' with 50-71% of tips. That pattern is unusual at this level, so no high-confidence pick is taken from it; lines are published with the community share noted.",
     "source": S["olbg_capture"]},
    {"id": "cmp-06", "severity": "data-quality", "sport": "Basketball", "fixture_id": "nba-sa-dal",
     "text": "OLBG's most-tipped selection in San Antonio v Dallas is the Spurs (7/10, 70%) even though San Antonio are 0-2 and 0-2 on the road this season. Our line follows the official standings (Dallas at home).",
     "source": S["nba_standings"]},
    {"id": "cmp-07", "severity": "unverified", "sport": "Tennis",
     "fixture_id": "ten-ryb-fer,ten-krueg-sin,ten-eal-sto,ten-uch-mer,ten-fer-sak,ten-waw-leh,ten-mic-vdz,ten-vac-nav,ten-she-ruu,ten-kym-rin,ten-djo-hum,ten-fri-tsi,ten-run-hal,ten-fok-ber,ten-tab-jod,ten-hur-fil",
     "text": "WTA draw/schedule pages and the 26-Oct ATP round are client-side rendered, so the hosting tournament for these pairings could not be named from the official sites. The WTA update feed confirms Osaka (Kinoshita Group Japan Open) and Tokyo (Toray Pan Pacific Open) as the live Asia events. Pairings and start times are OLBG-derived and flagged.",
     "source": S["wta_tournaments"]},
    {"id": "cmp-08", "severity": "data-quality", "sport": "Volleyball",
     "fixture_id": "vol-cis-tre,vol-per-por,vol-pad-civ",
     "text": "OLBG's most-tipped selections in the three Italian fixtures favour the lower-ranked side (Cisterna over Trentino, Pordenone over Perugia, Padova over Civitanova). Our lines treat the league favourites as the model picks; the community share is recorded for reference.",
     "source": S["legavolley_tre"]},
    {"id": "cmp-09", "severity": "unverified", "sport": "Greyhounds", "fixture_id": "gry-don-1104",
     "text": "GBGB does not publish a public online racecard for the 11:04 Doncaster. The runner list comes from the OLBG event page, which shows five named selections (a standard card carries six) — the list may be incomplete.",
     "source": S["gbgb"]},
    {"id": "cmp-10", "severity": "unverified", "sport": "Cricket",
     "fixture_id": "cri-tor-van,cri-indw-zimbw,cri-nam-irl-odi3,cri-sa-aus,cri-es-sae",
     "text": "No official fixture page was found/captured for the Toronto Kings v Vancouver Guardians T20, the India Women v Zimbabwe Women 2nd ODI, Namibia v Ireland 3rd ODI, or the 31 Oct South Africa v Australia fixture. CSA Pro20 fixtures are confirmed except Eastern Storm v SA Emerging (aggregators only). These rows carry OLBG-derived times and no official link.",
     "source": S["csa_pro20"]},
    {"id": "cmp-11", "severity": "coverage", "sport": "Golf",
     "fixture_id": "",
     "text": "The OLBG golf hub showed 'No tips found' at 22:35Z (PGA TOUR Bermuda Championship R4 and DP World Tour Genesis Championship R4 are in play on the official tours, but no OLBG golf tips were listed). The golf page therefore carries context only and no picks.",
     "source": S["pgatour"]},
    {"id": "cmp-12", "severity": "coverage", "sport": "Snooker",
     "fixture_id": "",
     "text": "The OLBG snooker hub showed 'No tips found' at 22:35Z; the Northern Ireland Open final (Kyren Wilson, 13:00Z per WST) listed earlier in the day had expired. Context only, no picks.",
     "source": S["wst_ni"]},
    {"id": "cmp-13", "severity": "coverage", "sport": "Motor Racing",
     "fixture_id": "",
     "text": "The OLBG motor racing hub showed 'No tips found' at 22:35Z; the F1 United States Grand Prix (Round 18, 25 Oct 20:00Z) listed earlier in the day had expired. Context only, no picks.",
     "source": S["f1_us"]},
    {"id": "cmp-14", "severity": "coverage", "sport": "Rugby League",
     "fixture_id": "rl-out-soo27,rl-out-sl27,rl-out-nrl27",
     "text": "The OLBG rugby league hub listed only 2027 ante-post outrights at capture, even though Rugby League World Cup 2026 is in progress (nrl.com: Australia v Fiji, 25 Oct). The RLWC context is shown on the sport page, but picks are only for the OLBG-listed outrights.",
     "source": S["nrl_rlwc"]},
    {"id": "cmp-15", "severity": "method", "sport": "Ice Hockey",
     "fixture_id": "nhl-tor-edm,nhl-sjs-bos,nhl-car-stl,nhl-vgk-clb,nhl-nyr-ott,nhl-buf-was,nhl-nsh-pit,nhl-tbl-uta,nhl-det-cgy,nhl-min-sea,nhl-mtl-wpg",
     "text": "The league-average scoring rate is computed from the 30 of 32 teams whose standings were captured (Chicago and Vancouver were not in the captured standings page). The impact on strength factors is under 1%.",
     "source": S["nhl_standings"]},
    {"id": "cmp-16", "severity": "method", "sport": "Basketball",
     "fixture_id": "nba-mil-phi,nba-bkn-cle,nba-sa-dal,nba-was-chi,nba-hou-atl,nba-no-den,nba-gs-phx",
     "text": "NBA confidence is capped at medium: only 1-2 games had been played in 2026-27 at capture and the 2025-26 prior-season records sit behind a JavaScript selector on the official standings page and could not be captured.",
     "source": S["nba_standings"]},
    {"id": "cmp-17", "severity": "time", "sport": "Rugby Union", "fixture_id": "rug-har-sar",
     "text": "OLBG displayed Harlequins v Saracens at 11:00 (Eastern view, = 15:00Z); the Premiership fixture listing (inherited official capture) has 11:00 UTC. Official time used.",
     "source": S["prem_r4"]},
    {"id": "cmp-18", "severity": "time", "sport": "Handball", "fixture_id": "han-rnl-mag",
     "text": "OLBG displayed SC Magdeburg v RNL at 10:00 (Eastern view, = 14:00Z); the official league page (inherited capture) has 13:00 UTC. Official time used.",
     "source": S["opel_hbl"]},
    {"id": "cmp-19", "severity": "method", "sport": "Tennis", "fixture_id": "ten-med-bas",
     "text": "OLBG displayed the Almaty final at 06:00 (Eastern view, = 10:00Z); the ATP daily schedule says 'not before 14:00' Almaty local (UTC+5) = 09:00Z. Official used.",
     "source": S["atp_almaty"]},
    {"id": "cmp-20", "severity": "market", "sport": "Baseball", "fixture_id": "mlb-g2",
     "text": "OLBG's most-tipped Game 2 selection is the Rays money line (13/22, 59%) although the Brewers are at home, lead the series 1-0 and have the stronger regular season. Our line favours Milwaukee.",
     "source": S["mlb_nl"]},
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "captures" / "olbg").mkdir(parents=True, exist_ok=True)
    (OUT / "captures" / "official").mkdir(parents=True, exist_ok=True)

    olbg = {"as_of_utc": AS_OF, "shown_date": SHOWN_DATE, "session": SESSION,
            "capture": CAPTURE, "count": len(LISTINGS), "listings": olbg_rows()}
    for path in (OUT / "captures" / "olbg" / "hubs.json", OUT / "olbg.json"):
        path.write_text(
            json.dumps(olbg, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    fixtures = {"as_of_utc": AS_OF, "shown_date": SHOWN_DATE, "session": SESSION,
                "count": len(FIXTURES), "fixtures": fixture_rows()}
    (OUT / "fixtures.json").write_text(
        json.dumps(fixtures, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    sources = {"as_of_utc": AS_OF, "count": len(SOURCES), "sources": SOURCES}
    (OUT / "sources.json").write_text(
        json.dumps(sources, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    flagged = {"as_of_utc": AS_OF, "count": len(FLAGS), "items": FLAGS}
    (OUT / "flagged.json").write_text(
        json.dumps(flagged, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    (OUT / "captures" / "official" / "manifest.json").write_text(
        json.dumps({"as_of_utc": AS_OF,
                    "note": "Official-page extracts are recorded as fact lines with source keys in fixtures.json; this manifest lists every official URL captured or inherited.",
                    "urls": sorted({s["url"] for s in SOURCES if s["key"] != "olbg_capture"})},
                   indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    print(f"compass_seed: {len(LISTINGS)} OLBG listings, {len(FIXTURES)} fixtures, "
          f"{len(SOURCES)} sources, {len(FLAGS)} flags")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
