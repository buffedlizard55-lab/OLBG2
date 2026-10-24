"""Official PDC and corroborating trusted inputs for the 2026 European Championship.

Ranking earnings and tournament leg records are data inputs only. Prices are
originated separately in today_model.py; no bookmaker price is used.
"""
from __future__ import annotations

PDC_HUB = "https://www.pdc.tv/tournament-hub/10870"
PDC_EVENT = "https://www.pdc.tv/tournaments/machineseeker-european-championship"
PDC_RANKINGS = "https://www.pdc.tv/rankings"
PDC_DRAW = "https://www.pdc.tv/news/2026/october/18/2026-Machineseeker-European-Championship-field---draw-confirmed/"
PDC_DAY1 = "https://www.pdc.tv/news/2026/october/22/nine-dart-star-woodhouse-sets-up-van-veen-clash-dortmund/"
PDC_FRIDAY = "https://www.pdc.tv/news/2026/october/23/Littler-kickstarts-European-Championship-title-bid-in-style/"
PDC_DAY3 = "https://www.pdc.tv/news/2026/october/24/2026-machineseeker-european-championship---day-three-latest"
PDC_PREVIEW = "https://www.pdc.tv/news/2026/october/21/2026-machineseeker-european-championship-preview/"
ESPN_RESULTS = "https://www.espn.com/darts/story/_/id/49948004/pdc-european-championship-darts-2026-schedule-results-how-watch-prize-money-dates-more-dortmund"
INDEPENDENT_QF = "https://www.independent.co.uk/sport/stephen-bunting-borussia-dortmund-gerwyn-price-bundesliga-eintracht-frankfurt-b3072710.html"


def player(world_money, et_money, legs_won, legs_lost):
    return dict(world_money=world_money, et_money=et_money,
                legs_won=legs_won, legs_lost=legs_lost)


def darts_fixture(identifier, round_name, home, away, start, start_display,
                  home_record, away_record, event_id, listed_selection,
                  home_stats, away_stats, fact_home, fact_away,
                  source_url, pricing_sources, extra_facts, record_source=PDC_FRIDAY):
    return dict(
        id=identifier, sport="Darts",
        competition=f"PDC European Championship — {round_name}",
        home=home, away=away, venue="Westfalenhallen, Dortmund",
        start_utc=start, start_display=start_display,
        start_source="OLBG listed match time; PDC official session schedule and order",
        home_record=home_record, away_record=away_record,
        market_decimal_home=None, market_decimal_away=None, market_source=None,
        olbg_event_id=event_id, olbg_listed_selection=listed_selection,
        olbg_market="Win Match 2-way", fact_home=fact_home, fact_away=fact_away,
        source_url=source_url, source_label="PDC official tournament schedule/report",
        stats_source_url=PDC_RANKINGS, pricing_source_urls=pricing_sources,
        record_source_url=record_source,
        darts=dict(best_of=19, home=home_stats, away=away_stats),
        extra_facts=extra_facts, injuries=[],
        injury_report_status="no official player availability report read",
    )


SATURDAY_SOURCES = [PDC_DAY3, PDC_FRIDAY, PDC_EVENT, PDC_RANKINGS, PDC_HUB]
SATURDAY_FACTS = [
    ("PDC Day Three schedule: Saturday evening Round 2, best of 19 legs; Nathan Aspinall v Luke Littler and Jonny Clayton v Josh Rock", PDC_DAY3),
    ("PDC Friday results: Aspinall 6-3 Reyes, Littler 6-3 O'Connor, Clayton 6-3 Springer and Rock 6-1 Dobey", PDC_FRIDAY),
    ("PDC rankings: two-year world-ranking earnings and current European Tour earnings are separate official fields", PDC_RANKINGS),
]

DARTS_FIXTURES = [
    darts_fixture(
        "darts-ec-aspinall-littler", "Round 2", "Nathan Aspinall", "Luke Littler",
        "2026-10-24T19:15:00Z", "OLBG listed 19:15 UTC; PDC evening session 17:00–21:00 UTC",
        "6-3", "6-3", "32397", "Luke Littler",
        player(577000, 87000, 6, 3), player(3106000, 75000, 6, 3),
        "Beat Cristo Reyes 6-3 in Round 1; £577,000 world-ranking earnings and £87,000 European Tour earnings",
        "Beat William O'Connor 6-3 with a 105.05 average; £3,106,000 world-ranking earnings and £75,000 European Tour earnings",
        PDC_DAY3, SATURDAY_SOURCES, SATURDAY_FACTS + [
            ("PDC Friday report: Littler's 105.05 average was the best of the tournament at that point", PDC_FRIDAY),
        ]),
    darts_fixture(
        "darts-ec-clayton-rock", "Round 2", "Jonny Clayton", "Josh Rock",
        "2026-10-24T20:15:00Z", "OLBG listed 20:15 UTC; PDC evening session 17:00–21:00 UTC",
        "6-3", "6-1", "32400", "Jonny Clayton",
        player(691000, 86000, 6, 3), player(599000, 76000, 6, 1),
        "Beat Niko Springer 6-3 in Round 1; £691,000 world-ranking earnings and £86,000 European Tour earnings",
        "Won six consecutive legs to beat Chris Dobey 6-1; £599,000 world-ranking earnings and £76,000 European Tour earnings",
        PDC_DAY3, SATURDAY_SOURCES, SATURDAY_FACTS + [
            ("PDC Friday report: Rock reeled off six legs straight against Dobey; Clayton scored impressively against Springer", PDC_FRIDAY),
        ]),
    darts_fixture(
        "darts-ec-price-bunting", "Quarter-final", "Gerwyn Price", "Stephen Bunting",
        "2026-10-25T12:00:00Z", "OLBG listed 12:00 UTC; PDC quarterfinal session begins 12:00 UTC",
        "16-6", "16-8", "32407", "Gerwyn Price",
        player(779500, 70000, 16, 6), player(568750, 43000, 16, 8),
        "Beat Rob Cross 6-2 with a 99.26 average and Cameron Menzies 10-4; £779,500 world-ranking and £70,000 European Tour earnings",
        "Beat Danny Noppert 6-5 and Kim Huybrechts 10-3 with four 100-plus checkouts; £568,750 world-ranking and £43,000 European Tour earnings",
        PDC_PREVIEW,
        [PDC_PREVIEW, PDC_DRAW, PDC_DAY1, PDC_EVENT, PDC_RANKINGS, PDC_HUB, ESPN_RESULTS, INDEPENDENT_QF],
        [
            ("PDC Sunday schedule: afternoon quarterfinals begin 13:00 CET/12:00 GMT after the clocks go back; best of 19 legs", PDC_PREVIEW),
            ("PDC opening report: Price beat Cross 6-2 with a 99.26 average; Bunting beat Noppert 6-5 with a 160 checkout in the decider", PDC_DAY1),
            ("ESPN current results: Price beat Menzies 10-4 and Bunting beat Huybrechts 10-3 in Saturday Round 2", ESPN_RESULTS),
            ("Independent report: those results established Price v Bunting as Sunday's quarterfinal; Bunting fired four 100-plus checkouts", INDEPENDENT_QF),
            ("PDC rankings: Price £779,500 world-ranking and £70,000 European Tour earnings; Bunting £568,750 and £43,000", PDC_RANKINGS),
        ], record_source=ESPN_RESULTS),
]
