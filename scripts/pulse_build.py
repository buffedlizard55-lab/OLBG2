#!/usr/bin/env python3
"""pulse_build.py - renders the static /pulse/ dashboard from data/pulse/*.json.
Deterministic: output depends only on the JSON inputs. No external assets."""
import json, os, html, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data/pulse")
SITE = os.path.join(ROOT, "pulse")

matches = json.load(open(os.path.join(D, "matches.json")))
flagged = json.load(open(os.path.join(D, "flagged.json")))
preds = json.load(open(os.path.join(D, "predictions.json")))
inputs = json.load(open(os.path.join(D, "inputs.json")))

E = lambda s: html.escape(str(s), quote=True)

def fa(v):
    if v is None: return "—"
    return f"+{v}" if v > 0 else str(v)

def prob(p):
    return "—" if p is None else f"{p*100:.1f}%"

SPORT_ORDER = ["ice-hockey","basketball","baseball","darts","handball","snooker","tennis","rugby-union","cricket","motor-racing"]
SPORT_NAMES = {"ice-hockey":"Ice Hockey","basketball":"Basketball","baseball":"Baseball","darts":"Darts",
 "handball":"Handball","snooker":"Snooker","tennis":"Tennis","rugby-union":"Rugby Union","cricket":"Cricket",
 "motor-racing":"Motor Racing","esports":"Esports","golf":"Golf","greyhounds":"Greyhounds",
 "gaelic-football":"Gaelic Football","volleyball":"Volleyball","rugby-league":"Rugby League","aussie-rules":"Aussie Rules"}
SPORT_EMOJI = {"ice-hockey":"🏒","basketball":"🏀","baseball":"⚾","darts":"🎯","handball":"🤾","snooker":"🎱",
 "tennis":"🎾","rugby-union":"🏉","cricket":"🏏","motor-racing":"🏎️","esports":"🎮","golf":"⛳",
 "greyhounds":"🐕","gaelic-football":"🏐","volleyball":"🏐","rugby-league":"🏉","aussie-rules":"🏉"}

NAV = [("index.html","Home"),("matches.html","All Matches"),("picks.html","High-Confidence Picks"),
 ("sports/index.html","By Sport"),("flagged.html","Flagged for Review"),("sources.html","Sources"),
 ("methodology.html","Methodology")]

def page(title, body, active="", subdir=""):
    prefix = subdir
    nav = "".join(f'<a class="{ "on" if active==href else ""}" href="{prefix}{href}">{E(label)}</a>' for href, label in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Pulse Desk · OLBG2</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<header><div class="wrap">
<div class="brand"><span class="logo">◍</span> Pulse <span class="dim">· verified match desk</span></div>
<nav>{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap">Built 2026-10-22 by session <code>arena/5fba1c42-olbg2</code> from first-hand official-source captures. Every row links to an official governing-body page. Values that could not be confirmed are blank and appear on the <a href="{prefix}flagged.html">Flagged for Review</a> page. · <a href="../index.html">Repo dashboard</a></footer>
</body></html>"""

def badge(c):
    return f'<span class="bdg {c}">{c.upper()}</span>'

def mrow(m):
    if m.get("pick"):
        p = m["pick"]
        pick_html = f'{E(p["selection"])}<div class="sub">model {prob(p["probability"])} · fair {fa(p["fair_american"])} ({p["fair_decimal"]}) {badge(p["confidence"])}</div>'
    else:
        pick_html = f'<span class="blank">{E(m.get("line_status","unverified — left blank"))}</span>'
    sport_slug = m["sport"]
    return f"""<tr>
<td class="no">{E(m["date"])}<div class="sub">{E(m["start_utc"])}</div></td>
<td><a href="sports/{sport_slug}.html">{SPORT_EMOJI.get(sport_slug,"")} {E(SPORT_NAMES.get(sport_slug,sport_slug))}</a><div class="sub">{E(m["competition"])[:70]}</div></td>
<td><b>{E(m["home"])}</b> v {E(m["away"])}<div class="sub">{E(m["venue"])[:60]}</div></td>
<td>{pick_html}</td>
<td class="src"><a href="{E(m["official_url"])}" target="_blank" rel="noopener">official source ↗</a></td>
</tr>"""

def market_cell(mm):
    if not mm: return '<span class="blank">—</span>'
    if isinstance(mm, str): return f'<span class="note">{E(mm)}</span>'
    out = []
    for x in mm:
        out.append(f'<div class="mrow2"><span class="sel">{E(x["selection"])}</span> <span class="odds">{prob(x["probability"])} · {fa(x["fair_american"])}</span> {badge(x["confidence"])}</div>')
    return "".join(out)

# ------------------------------------------------------------------ home
by_sport = {}
for m in matches: by_sport.setdefault(m["sport"], []).append(m)
n_orig = sum(1 for m in matches if m.get("pick"))
high = [h for h in preds["high_picks"]]
cards = []
for slug in SPORT_ORDER:
    ms = by_sport.get(slug, [])
    n_lined = sum(1 for m in ms if m.get("pick"))
    cards.append(f'<a class="card" href="sports/{slug}.html"><span class="big">{SPORT_EMOJI[slug]}</span><b>{SPORT_NAMES[slug]}</b><span class="num">{len(ms)}</span><span class="sub">fixtures · {n_lined} originated</span></a>')
unres = inputs["unresolved_sports"]
other_cards = "".join(f'<a class="card muted" href="flagged.html"><span class="big">{SPORT_EMOJI.get(u["sport"],"•")}</span><b>{SPORT_NAMES.get(u["sport"],u["sport"])}</b><span class="num">0</span><span class="sub">no verified fixture — flagged</span></a>' for u in unres)
other_cards += f'<a class="card muted" href="flagged.html"><span class="big">{SPORT_EMOJI["esports"]}</span><b>Esports</b><span class="num">0</span><span class="sub">Worlds Swiss from 23 Oct — pairings flagged</span></a>'
body = f"""
<h1>Today's verified match desk — 22 October 2026</h1>
<p class="lede">A fresh, first-hand sweep of every eligible OLBG sport. <b>{len(matches)} fixtures are published; {n_orig} carry independently originated lines</b> (win match, handicap and match total). One selection qualifies for the strict high-confidence band (model ≥70% <i>and</i> fair price between −250 and +10000). Excluded sports (football, American football, horse racing, boxing, UFC/MMA, cycling, hurling, specials) are never collected.</p>
<div class="kpis">
<div class="kpi"><span>{len(matches)}</span>verified fixtures</div>
<div class="kpi"><span>{n_orig}</span>originated markets sets</div>
<div class="kpi"><span>{len(high)}</span>in-band HIGH pick</div>
<div class="kpi"><span>{len(flagged["flags"])}</span>flagged items</div>
</div>
<h2>Featured high-confidence pick</h2>
{ "".join(f'''<div class="pickcard"><div class="ph"><b>{E(h["match"])}</b> <a href="picks.html" class="pill">write-up ↗</a></div>
<p>{E(h["text"])}</p><div class="meta">Selection: <b>{E(h["selection"])}</b> · model {prob(h["probability"])} · fair {fa(h["fair_american"])} · {badge("high")}</div></div>''' for h in high) }
<h2>Sports covered</h2>
<div class="grid">{"".join(cards)}</div>
<h2>Sports checked, no verified fixture at capture</h2>
<div class="grid">{other_cards}</div>
<h2>Band audit (why most ≥70% picks are only MEDIUM)</h2>
<table><thead><tr><th>Market</th><th>Model p</th><th>Fair US</th><th>Band verdict</th></tr></thead><tbody>
{"".join(f'<tr><td>{E(r["market"])}</td><td>{r["p"]*100:.1f}%</td><td>{fa(r["fair"])}</td><td class="{"ok" if r["verdict"].startswith("HIGH") else "warn"}">{E(r["verdict"])}</td></tr>' for r in preds["band_audit"]["rows"])}
</tbody></table>
<p class="note">{E(preds["band_audit"]["market_price_angle"])}</p>
<p class="note">Full write-up and per-claim source links on the <a href="picks.html">High-Confidence Picks</a> page. Method and constants: <a href="methodology.html">Methodology</a>.</p>
"""
open(os.path.join(SITE, "index.html"), "w").write(page("Home", body, "index.html"))

# ------------------------------------------------------------------ all matches
rows = "".join(mrow(m) for m in matches)
body = f"""<h1>All matches ({len(matches)})</h1>
<p class="note">Every row links to the official governing-body page it was verified against (last column). Blanks are deliberate and flagged — nothing is inferred.</p>
<table><thead><tr><th>Date / start</th><th>Sport / competition</th><th>Match</th><th>Winner pick (model)</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table>"""
open(os.path.join(SITE, "matches.html"), "w").write(page("All matches", body, "matches.html"))

# ------------------------------------------------------------------ picks
hcards = []
for h in high:
    claims = "".join(f'<li>{E(c["claim"])} — <a href="{E(c["url"])}" target="_blank" rel="noopener">verify ↗</a></li>' for c in h["verified_claims"])
    hcards.append(f"""<div class="pickcard">
<div class="ph"><b>{E(h["match"])}</b></div>
<p class="picktext">{E(h["text"])}</p>
<div class="meta">Selection: <b>{E(h["selection"])}</b> · model probability {prob(h["probability"])} · fair odds {fa(h["fair_american"])} (decimal {h["fair_decimal"]}) · {badge("high")} · {h["words"]} words</div>
<h4>Verified claims used in this write-up</h4><ul class="claims">{claims}</ul></div>""")
body = f"""<h1>High-confidence picks inside the −250…+10000 band</h1>
<p class="lede">{E(preds["rule"])}</p>
{"".join(hcards)}
<h2>The full ≥70% audit</h2>
<table><thead><tr><th>Market</th><th>Model p</th><th>Fair US</th><th>Verdict</th></tr></thead><tbody>
{"".join(f'<tr><td>{E(r["market"])}</td><td>{r["p"]*100:.1f}%</td><td>{fa(r["fair"])}</td><td>{E(r["verdict"])}</td></tr>' for r in preds["band_audit"]["rows"])}
</tbody></table>
<p class="note">{E(preds["band_audit"]["market_price_angle"])}</p>"""
open(os.path.join(SITE, "picks.html"), "w").write(page("High-confidence picks", body, "picks.html"))

# ------------------------------------------------------------------ flagged
def link_list(f):
    return " ".join('<a href="' + E(u) + '" target="_blank" rel="noopener">link ↗</a>' for u in f["links"])
frows = "".join(f'<tr><td><code>{E(f["code"])}</code></td><td><b>{E(f["item"])}</b></td><td>{E(f["detail"])}</td><td class="src">{link_list(f)}</td></tr>' for f in flagged["flags"])
blanks = [m for m in matches if not m.get("pick")]
brows = "".join(f'<tr><td>{E(SPORT_NAMES.get(m["sport"],m["sport"]))}</td><td><b>{E(m["home"])}</b> v {E(m["away"])}</td><td>{E(m.get("line_status",""))}</td><td class="src"><a href="{E(m["official_url"])}" target="_blank" rel="noopener">official source ↗</a></td></tr>' for m in blanks)
ures = "".join(f'<tr><td>{E(SPORT_NAMES.get(u["sport"],u["sport"]))}</td><td>{E(u["status"])}</td><td class="src"><a href="{E(u["url"])}" target="_blank" rel="noopener">official hub ↗</a></td></tr>' for u in unres)
body = f"""<h1>Flagged for Review</h1>
<p class="lede">Everything on this page is published for manual review — none of it blocks the main desk. Items fall in three groups: rules-based flags, blank values we refuse to invent, and sports with no first-hand fixture capture.</p>
<h2>Flags ({len(flagged["flags"])})</h2>
<table><thead><tr><th>Code</th><th>Item</th><th>Detail</th><th>Source links</th></tr></thead><tbody>{frows}</tbody></table>
<h2>Fixtures published with blank lines ({len(blanks)})</h2>
<table><thead><tr><th>Sport</th><th>Fixture</th><th>Why blank</th><th>Source</th></tr></thead><tbody>{brows}</tbody></table>
<h2>Sports with no verified fixture at capture</h2>
<table><thead><tr><th>Sport</th><th>Status (checked 2026-10-22)</th><th>Official hub</th></tr></thead><tbody>{ures}<tr><td>Esports</td><td>{E(inputs["esports_status"]["status"])}</td><td class="src"><a href="{E(inputs["esports_status"]["official_url"])}" target="_blank" rel="noopener">lolesports.com ↗</a></td></tr></tbody></table>"""
open(os.path.join(SITE, "flagged.html"), "w").write(page("Flagged for Review", body, "flagged.html"))

# ------------------------------------------------------------------ sources
FAMILIES = [
 ("NHL (ice hockey)", "Official score API, stats REST, GameCenter pages", "https://api-web.nhle.com/v1/score/2026-10-22"),
 ("NHL team stats", "Goals for/against per team, 2026-27 regular season", "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2"),
 ("NBA", "League official game pages & games calendar", "https://www.nba.com/games?date=2026-10-22"),
 ("NBA game 1", "Cavaliers at 76ers game page", "https://www.nba.com/game/cle-vs-phi-0022600006"),
 ("NBA game 2", "Nuggets at Thunder game page", "https://www.nba.com/game/den-vs-okc-0022600007"),
 ("MLB", "Official Stats API schedule (World Series)", "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-21&endDate=2026-10-28&hydrate=team,venue"),
 ("MLB standings AL", "Rays 98-64 verified", "https://statsapi.mlb.com/api/v1/standings?leagueId=103&season=2026&standingsTypes=regularSeason"),
 ("MLB standings NL", "Brewers 103-59 verified", "https://statsapi.mlb.com/api/v1/standings?leagueId=104&season=2026&standingsTypes=regularSeason&fields=records,teamRecords,team,name,wins,losses,runsScored,runsAllowed,divisionRank"),
 ("PDC (darts)", "European Championship schedule confirmed", "https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/"),
 ("PDC preview", "Draw bracket with 1-32 seeds", "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview"),
 ("EHF (handball)", "Champions League matches page", "https://ehfcl.eurohandball.com/men/2026-27/matches/"),
 ("EHF standings", "Group tables A-F (W-D-L, goals)", "https://ehfcl.eurohandball.com/men/2026-27/standings/"),
 ("WST (snooker)", "Northern Ireland Open match list & live centre", "https://www.wst.tv/matches/b4533c9e-8d2c-4ecc-8dfd-c6b284705578"),
 ("WST tournaments", "Tournament card (Belfast, 18-25 Oct)", "https://www.wst.tv/tournaments/"),
 ("ATP (tennis)", "Almaty daily schedule", "https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule"),
 ("ATP current", "Live scores hub (Almaty/Brussels/Lyon R16)", "https://www.atptour.com/en/scores/current"),
 ("LNR Pro D2 (rugby union)", "Journée 8 fixtures with official positions", "https://prod2.lnr.fr/calendrier-et-resultats"),
 ("ICC (cricket)", "NZ v India 1st T20I match page", "https://www.icc-cricket.com/matches/271646/new-zealand-vs-india"),
 ("ICC series news", "Five-match series schedule", "https://icc-cricket.com/news/iyer-backs-india-s-adaptability-ahead-of-new-zealand-t20is"),
 ("FIA F1", "2026 calendar with official round results", "https://www.formula1.com/en/racing/2026"),
 ("LoL Esports (Riot)", "Worlds 2026 primer (stage dates)", "https://lolesports.com/en-US/news/worlds-2026-primer"),
 ("DP World Tour (golf)", "Genesis Championship leaderboard", "https://www.europeantour.com/dpworld-tour/genesis-championship-2026/leaderboard"),
 ("GBGB (greyhounds)", "Results hub (JS-blocked at capture)", "https://www.gbgb.org.uk/racing/results/"),
 ("GAA (gaelic football)", "Fixtures & results hub", "https://www.gaa.ie/fixtures-results"),
 ("Volleyball World", "Competitions hub (no list rendered)", "https://en.volleyballworld.com/"),
 ("NRL (rugby league)", "Draw hub (no first-hand capture)", "https://www.nrl.com/draw/"),
 ("AFL (aussie rules)", "Fixture hub (no first-hand capture)", "https://www.afl.com.au/fixture"),
 ("OLBG (target site)", "Today’s tips page — universe cross-check & market shapes", "https://www.olbg.com/betting-tips/"),
]
srows = "".join(f'<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td class="src"><a href="{E(u)}" target="_blank" rel="noopener">{E(u[:70])}{"…" if len(u)>70 else ""}</a></td></tr>' for a,b,u in FAMILIES)
body = f"""<h1>Official sources ({len(FAMILIES)})</h1>
<p class="note">Every published value traces to one of these official governing-body / league pages (or, for the OLBG row, the target site itself for market-shape reference only — OLBG is never treated as an authority for facts).</p>
<table><thead><tr><th>Source family</th><th>What it verified</th><th>URL</th></tr></thead><tbody>{srows}</tbody></table>"""
open(os.path.join(SITE, "sources.html"), "w").write(page("Official sources", body, "sources.html"))

# ------------------------------------------------------------------ methodology
body = """<h1>Methodology</h1>
<h2>Pipeline</h2>
<ol>
<li><b>First-hand capture</b> — fixtures and team inputs are read only from official governing-body pages/feeds on 2026-10-22 and frozen in <code>data/pulse/inputs.json</code> with the URL of each row.</li>
<li><b>Origination</b> — <code>scripts/pulse_model.py</code> turns those inputs into probabilities. No bookmaker price is read, copied or implied. The NHL's league-published odds-partner prices are shown on a row as <i>market context</i> only and are never an input.</li>
<li><b>Grading</b> — a selection is <span class="bdg high">HIGH</span> only with model probability ≥70% <i>and</i> fair American odds between −250 and +10000 (decimal 1.40–101.00). 57.5–70% (or ≥70% but heavier than −250) is <span class="bdg medium">MEDIUM</span>; below is <span class="bdg low">LOW</span>. Nothing is nudged across a boundary.</li>
<li><b>Verification</b> — <code>scripts/pulse_verify.py</code> re-reads every generated page: every table row must carry an official HTTPS source link; blanks must be labelled; predictions must be ≥30 words with per-claim links.</li>
</ol>
<h2>Models (all deterministic, stdlib-only)</h2>
<table><thead><tr><th>Sport</th><th>Win model</th><th>Handicap / total</th></tr></thead><tbody>
<tr><td>Ice hockey (NHL)</td><td>Independent Poisson goals: λ_home = GF_h × GA_away / league_avg × 1.045 home edge; ties split 55% to the home side for OT/SO.</td><td>Puck line ±1.5 from the regulation margin grid; total 5.5 from the summed Poisson.</td></tr>
<tr><td>Baseball (MLB)</td><td>Log5 on the blend of actual win% and Pythagorean expectation (RS²/(RS²+RA²)), ×1.13 documented home-boost factor.</td><td>Not originated this session (no verified probable-pitcher data) — PU-19.</td></tr>
<tr><td>Darts (PDC)</td><td>Leg rating = seed^(−1.15) on the official 1–32 European Tour seeds; race to 6 legs via the binomial race formula.</td><td>−1.5/+1.5 legs and over/under 9.5 total legs from the full 6-0…6-5 distribution.</td></tr>
<tr><td>Handball (EHF)</td><td>Poisson goals from official group GF/GA (×1.03 home edge); winner market quoted draw-no-bet (tie removed and renormalised).</td><td>Goal handicap at floor(|Δλ|)+0.5; match total at floor(λ_h+λ_a)+0.5.</td></tr>
<tr><td>Snooker (WST)</td><td>Frame share this tournament with a +2/±4 shrinkage prior, Bradley–Terry frame probability, race to 4 frames.</td><td>−1.5/+1.5 frames and over/under 6.5 frames from the 4-0…4-3 distribution.</td></tr>
<tr><td>Tennis (ATP)</td><td>Set rating = seed^(−0.55); unseeded = placeholder 33 (PU-14); match = race to 2 sets.</td><td>−1.5/+1.5 sets and over/under 2.5 sets.</td></tr>
<tr><td>Rugby union (Pro D2)</td><td>Home margin ~ N(3.5 + 1.35×(away_pos − home_pos), 13), positions straight from the official LNR J8 list.</td><td>Handicap at floor(|μ|)+0.5 via the same normal; totals not originated (no verified points data) — PU-20.</td></tr>
<tr><td>Motor racing (F1)</td><td>Season score = wins + 0.5×P2 + 0.25×P3 over official R1–R16 results, normalised over the full 28-point pool.</td><td>Outright only.</td></tr>
</tbody></table>
<h2>Sensitivity (disclosed, computed on the featured pick)</h2>
<table><thead><tr><th>Constant</th><th>Value</th><th>Ottawa moneyline p</th><th>Grade consequence</th></tr></thead><tbody>
<tr><td>NHL home edge</td><td>1.02 / <b>1.045</b> / 1.07</td><td>68.6% / <b>70.4%</b> / 72.2%</td><td>MEDIUM / <b>HIGH</b> / MEDIUM (heavier than −250)</td></tr>
<tr><td>NHL OT home share</td><td>0.50 / <b>0.55</b> / 0.60</td><td>69.6% / <b>70.4%</b> / 71.2%</td><td>MEDIUM / <b>HIGH</b> / HIGH</td></tr>
</tbody></table>
<p class="note">The featured pick lives inside the narrow 70.00–71.43% sliver the brief's band creates for favourites; the desk publishes the constants and their sensitivity rather than hiding it.</p>
<h2>What we deliberately do not do</h2>
<ul>
<li>No value is inferred or back-filled — blanks stay blank and are flagged.</li>
<li>No fixture from an excluded sport is collected or originated.</li>
<li>No tip percentage from OLBG (a community measure) is used as a probability, and no bookmaker price is treated as truth; market prices appear only as labelled context.</li>
<li>Write-ups are required to contain ≥30 words, a named team and player, current form, recent verified results and an explicit selection.</li>
</ul>"""
open(os.path.join(SITE, "methodology.html"), "w").write(page("Methodology", body, "methodology.html"))

# ------------------------------------------------------------------ per-sport pages
os.makedirs(os.path.join(SITE, "sports"), exist_ok=True)
for slug in SPORT_ORDER:
    ms = by_sport.get(slug, [])
    rows = []
    for m in ms:
        wm = market_cell(m.get("winner_market"))
        cm = market_cell(m.get("handicap_market"))
        tm = market_cell(m.get("total_market"))
        extra = ""
        if m.get("expected"): extra = f'<div class="note">expected: {E(json.dumps(m["expected"]))}</div>'
        if m.get("leaders"): extra += f'<div class="note">official leaders — home: {E(m["leaders"]["home"])}; away: {E(m["leaders"]["away"])}</div>'
        if m.get("market_context"): extra += f'<div class="note">league-published partner prices (context): home {E(m["market_context"]["home"])} · away {E(m["market_context"]["away"])}</div>'
        if m.get("seed_model"): extra += f'<div class="note">{E(m["seed_model"])}</div>'
        rows.append(f"""<tr>
<td><b>{E(m["home"])}</b> v {E(m["away"])}<div class="sub">{E(m["date"])} · {E(m["start_utc"])}<br>{E(m.get("home_form",""))}<br>{E(m.get("away_form",""))}</div>{extra}</td>
<td>{wm}</td><td>{cm}</td><td>{tm}</td>
<td class="src"><a href="{E(m["official_url"])}" target="_blank" rel="noopener">official source ↗</a></td>
</tr>""")
    wst_extra = ""
    if slug == "snooker":
        live = inputs["wst"]["live_at_capture"]
        wst_extra = ("<h2>In play at capture (no pre-match lines — PU-04)</h2><ul>" +
            "".join(f'<li>{E(x["match"])} — {E(x["status"])}</li>' for x in live) + "</ul>" +
            f'<p class="note">{E(inputs["wst"]["giant_killing_note"])}</p>')
    atp_extra = ""
    if slug == "tennis":
        atp_extra = ("<h2>Also verified today</h2><ul>" +
            "".join(f'<li>{E(x["match"])} — {E(x["note"])}</li>' for x in inputs["atp"]["completed_today"]) +
            "".join(f'<li>{E(x["match"])} — {E(x["note"])}</li>' for x in inputs["atp"]["in_progress_at_capture"]) + "</ul>" +
            f'<p class="note">{E(inputs["atp"]["other_live_tournaments"])}</p>')
    icc_extra = ""
    if slug == "cricket":
        icc_extra = (f'<p class="note">{E(inputs["icc"]["in_play_at_capture"])} Full verified series schedule: {E("; ".join(inputs["icc"]["series_schedule_verified"]))} — <a href="{E(inputs["icc"]["series_news_url"])}" target="_blank" rel="noopener">ICC news ↗</a></p>')
    body = f"""<h1>{SPORT_EMOJI[slug]} {SPORT_NAMES[slug]}</h1>
<table><thead><tr><th>Fixture & verified form</th><th>Win match</th><th>Handicap</th><th>Match total</th><th>Source</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
{wst_extra}{atp_extra}{icc_extra}"""
    open(os.path.join(SITE, f"sports/{slug}.html"), "w").write(page(SPORT_NAMES[slug], body, "sports/index.html", "../"))

# sports index
scards = []
for slug in SPORT_ORDER:
    ms = by_sport.get(slug, [])
    n_lined = sum(1 for m in ms if m.get("pick"))
    comp = ms[0]["competition"] if ms else ""
    scards.append(f'<a class="card" href="{slug}.html"><span class="big">{SPORT_EMOJI[slug]}</span><b>{SPORT_NAMES[slug]}</b><span class="num">{len(ms)}</span><span class="sub">{E(comp)[:70]}</span><span class="sub">{n_lined} with originated lines</span></a>')
body = f"""<h1>Browse by sport</h1>
<p class="note">17 eligible sports tracked (OLBG's in-scope catalogue minus the excluded list). Ten have verified fixtures on this desk today; the remainder are audited on the <a href="../flagged.html">Flagged for Review</a> page.</p>
<div class="grid">{"".join(scards)}</div>"""
open(os.path.join(SITE, "sports/index.html"), "w").write(page("Sports", body, "sports/index.html", "../"))

print("built:", len(matches), "matches,", len(SPORT_ORDER)+7, "pages")
