"""Generate data/canon/sources.json: the official-source allowlist registry for /canon/."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "canon"

OFFICIAL_HOSTS = {
    "nba.com": "NBA (official league site)",
    "www.nba.com": "NBA (official league site)",
    "euroleaguebasketball.net": "EuroLeague (official competition site)",
    "www.euroleaguebasketball.net": "EuroLeague (official competition site)",
    "api-web.nhle.com": "NHL (official live data API)",
    "api.nhle.com": "NHL (official stats API)",
    "stats.swehockey.se": "Swedish Ice Hockey Association (official stats)",
    "liiga.fi": "Finnish Hockey League (official site)",
    "www.liiga.fi": "Finnish Hockey League (official site)",
    "statsapi.mlb.com": "MLB Advanced Media (official stats API)",
    "www.mlb.com": "MLB (official league site)",
    "atptour.com": "ATP Tour (official tour site)",
    "www.atptour.com": "ATP Tour (official tour site)",
    "wtatennis.com": "WTA Tour (official tour site)",
    "www.wtatennis.com": "WTA Tour (official tour site)",
    "wtafiles.wtatennis.com": "WTA Tour (official draw files)",
    "pdc.tv": "Professional Darts Corporation (official tour site)",
    "www.pdc.tv": "Professional Darts Corporation (official tour site)",
    "wst.tv": "World Snooker Tour (official tour site)",
    "www.wst.tv": "World Snooker Tour (official tour site)",
    "formula1.com": "Formula 1 (official championship site)",
    "www.formula1.com": "Formula 1 (official championship site)",
    "ehfcl.eurohandball.com": "EHF Champions League Men (official competition site)",
    "daikin-hbl.de": "Handball-Bundesliga (official league site)",
    "www.daikin-hbl.de": "Handball-Bundesliga (official league site)",
    "plusliga.pl": "Polish PlusLiga (official league site)",
    "legavolley.it": "Lega Pallavolo Serie A (official league site)",
    "www.legavolley.it": "Lega Pallavolo Serie A (official league site)",
    "unitedrugby.com": "United Rugby Championship (official competition site)",
    "www.unitedrugby.com": "United Rugby Championship (official competition site)",
    "top14.lnr.fr": "Ligue Nationale de Rugby - Top 14 (official league site)",
    "prod2.lnr.fr": "Ligue Nationale de Rugby - Pro D2 (official league site)",
    "nrl.com": "National Rugby League / RLWC2026 (official competition site)",
    "www.nrl.com": "National Rugby League / RLWC2026 (official competition site)",
    "afl.com.au": "Australian Football League (official league site, AFLW section)",
    "www.afl.com.au": "Australian Football League (official league site, AFLW section)",
    "munster.gaa.ie": "GAA Munster Council (official provincial council site)",
    "gaa.ie": "Gaelic Athletic Association (official national governing body)",
    "www.gaa.ie": "Gaelic Athletic Association (official national governing body)",
    "wearetyrone.com": "Tyrone GAA affiliated coverage of the official county final replay fixture",
    "gbgb.org.uk": "Greyhound Board of Great Britain (official governing body)",
    "www.gbgb.org.uk": "Greyhound Board of Great Britain (official governing body)",
    "olbg.com": "OLBG.com (site under study - fixture existence cross-check only)",
    "www.olbg.com": "OLBG.com (site under study - fixture existence cross-check only)",
    "pgatour.com": "PGA Tour (official tour site)",
    "www.pgatour.com": "PGA Tour (official tour site)",
    "lolesports.com": "Riot Games LoL Esports (official esports league site)",
    "cricketworld.com": "Cricket World (aggregated official fixture listing, cross-checked against cricbuzz.com)",
    "www.bjsports.live": "Match preview citing official ODI Tri-Nation Series schedule",
}


def main():
    matches = json.loads((DATA_DIR / "matches.json").read_text())["matches"]
    urls = sorted({m["source_url"] for m in matches})
    rows = []
    for url in urls:
        host = urlsplit(url).netloc
        rows.append({
            "url": url,
            "host": host,
            "publisher": OFFICIAL_HOSTS.get(host, "UNCLASSIFIED - needs manual review"),
        })
    unclassified = [r for r in rows if r["publisher"].startswith("UNCLASSIFIED")]
    out = {
        "generated_utc": "2026-10-22T12:24:00Z",
        "session": "arena/3de6d2ed-olbg2",
        "count": len(rows),
        "unclassified_count": len(unclassified),
        "sources": rows,
    }
    (DATA_DIR / "sources.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"canon_sources.py OK: {len(rows)} distinct source URLs, {len(unclassified)} unclassified")
    if unclassified:
        for r in unclassified:
            print("  UNCLASSIFIED:", r["url"])


if __name__ == "__main__":
    main()
