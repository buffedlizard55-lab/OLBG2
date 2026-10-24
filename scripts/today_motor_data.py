"""Official Formula 1 inputs for the 2026 United States Grand Prix."""
from __future__ import annotations

F1_EVENT = "https://www.formula1.com/en/racing/2026/united-states"
F1_TIMETABLE = "https://www.formula1.com/en/latest/article/formula-1-msc-cruises-united-states-grand-prix-2026.2u6li2pzNhPzL3TSYaagrm"
F1_STANDINGS = "https://www.formula1.com/en/results/2026/drivers"
F1_RACES = "https://www.formula1.com/en/results/2026/races"
F1_FP2 = "https://www.formula1.com/en/results/2026/races/1297/united-states/practice/2"

# name, championship points, 2026 wins, Practice 2 gap in seconds.
# The current entry list is the 22 drivers who set an official FP2 time.
DRIVERS = [
    ("Charles Leclerc", 215, 1, 0.0),
    ("Kimi Antonelli", 340, 8, 0.042),
    ("Max Verstappen", 221, 2, 0.189),
    ("Lewis Hamilton", 229, 1, 0.615),
    ("George Russell", 238, 3, 0.744),
    ("Liam Lawson", 75, 0, 1.040),
    ("Lando Norris", 201, 2, 1.082),
    ("Oscar Piastri", 138, 0, 1.096),
    ("Isack Hadjar", 97, 0, 1.120),
    ("Oliver Bearman", 23, 0, 1.245),
    ("Gabriel Bortoleto", 10, 0, 1.541),
    ("Pierre Gasly", 41, 0, 1.549),
    ("Arvid Lindblad", 38, 0, 1.668),
    ("Esteban Ocon", 7, 0, 1.820),
    ("Franco Colapinto", 27, 0, 1.910),
    ("Fernando Alonso", 7, 0, 1.944),
    ("Lance Stroll", 0, 0, 1.978),
    ("Nico Hulkenberg", 13, 0, 2.139),
    ("Valtteri Bottas", 0, 0, 3.131),
    ("Carlos Sainz", 7, 0, 3.155),
    ("Sergio Perez", 0, 0, 3.745),
    ("Alexander Albon", 5, 0, 8.135),
]

MOTOR_FIXTURE = dict(
    id="f1-2026-united-states", sport="Motor Racing",
    competition="Formula 1 — United States Grand Prix", event_name="United States Grand Prix",
    home="Race", away="22-starter field", venue="Circuit of The Americas, Austin",
    start_utc="2026-10-25T20:00:00Z",
    start_source="Official timetable: 15:00 Austin; the article states Austin is five hours behind UTC; event structured data also gives 20:00Z",
    home_record="17 races", away_record="22 starters",
    market_decimal_home=None, market_decimal_away=None, market_source=None,
    olbg_event_id="913", olbg_listed_selection="Max Verstappen", olbg_market="Win Race",
    fact_home="Antonelli leads the championship with 340 points and has eight wins from 17 completed races",
    fact_away="22 current starters set Practice 2 times; Leclerc led in 1:35.291",
    source_url=F1_TIMETABLE, source_label="Formula 1 official timetable",
    stats_source_url=F1_STANDINGS,
    pricing_source_urls=[F1_TIMETABLE, F1_STANDINGS, F1_RACES, F1_FP2],
    motor=dict(drivers=[dict(name=name, points=points, wins=wins, fp2_gap=gap)
                        for name, points, wins, gap in DRIVERS]),
    extra_facts=[
        ("Official timetable: the Grand Prix is 15:00-17:00 Austin on Sunday 25 October over 56 laps or 120 minutes; Austin is five hours behind UTC", F1_TIMETABLE),
        ("Official standings: Antonelli 340 points, Russell 238, Hamilton 229, Verstappen 221, Leclerc 215 and Norris 201", F1_STANDINGS),
        ("Official race results: 17 completed 2026 races; Antonelli has eight wins, Russell three, Verstappen two, Norris two, Hamilton one and Leclerc one", F1_RACES),
        ("Official recent results: Verstappen won in Bahrain and Singapore, the two most recent completed Grands Prix", F1_RACES),
        ("Official Practice 2: Leclerc 1:35.291; Antonelli +0.042s, Verstappen +0.189s, Hamilton +0.615s and Russell +0.744s", F1_FP2),
        ("Official Practice 2 entry list contains 22 starters; Tsunoda has a standings row but no current Practice 2 time and is not included in this race field", F1_FP2),
    ],
    injuries=[], injury_report_status="no official availability report read",
)
