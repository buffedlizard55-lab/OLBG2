#!/usr/bin/env python3
"""Experimental independent-Poisson research lines; never bookmaker prices.

Factual rates are separate from modelling assumptions. No calibrated model has
been established, so confidence is capped at medium, even when p >= .70.
"""
from math import exp, factorial


def quote(p):
    if not 0 < p < 1:
        raise ValueError('Probability must be strictly between zero and one')
    d = round(1 / p, 4)
    american = round(100 * (1 / p - 1)) if p <= .5 else -round(100 * p / (1 - p))
    return {'probability': round(p, 6), 'fair_decimal': d,
            'fair_american': american, 'confidence': 'medium' if p >= .6 else 'low',
            'in_focus_band': 1.4 <= 1 / p <= 101,
            'confidence_limit': 'Uncalibrated experimental model; never high confidence.'}


def confidence(p, decimal, calibrated=False):
    """Strict price-window gate plus evidence-of-calibration safeguard."""
    if calibrated and p >= .70 and 1.4 <= decimal <= 101:
        return 'high'
    return 'medium' if p >= .6 else 'low'


def originate(home, away):
    """Inputs contain only gp/gf/ga. No market-price or tipster input is read.

    lambda_home = mean(home GF/GP, away GA/GP), vice versa away.
    No home edge assumed. Independent Poisson, conditional grid 0..40;
    a regulation tie is split equally for illustrative overtime winner prices.
    Handicap/total distributions are regulation-only, labelled explicitly.
    """
    for team in (home, away):
        if team['gp'] <= 0 or min(team['gf'], team['ga']) < 0:
            raise ValueError('Invalid scoring inputs')
    lh = (home['gf']/home['gp'] + away['ga']/away['gp'])/2
    la = (away['gf']/away['gp'] + home['ga']/home['gp'])/2
    def pmf(k, rate):
        return exp(-rate)*rate**k/factorial(k)
    grid = [(h, a, pmf(h, lh)*pmf(a, la)) for h in range(41) for a in range(41)]
    mass = sum(p for h, a, p in grid)
    def prob(predicate):
        return sum(p for h, a, p in grid if predicate(h, a))/mass
    draw = prob(lambda h,a: h==a)
    ph = prob(lambda h,a: h>a)+draw/2
    line = int(lh+la)+.5
    home_line = -1.5 if ph >= .5 else 1.5
    pc = prob(lambda h,a: h+home_line>a)
    po = prob(lambda h,a: h+a>line)
    return {'lambda_home': round(lh,6), 'lambda_away': round(la,6),
            'winner': {'home': quote(ph), 'away': quote(1-ph)},
            'regulation': {'home': quote(prob(lambda h,a:h>a)), 'draw': quote(draw),
                           'away': quote(prob(lambda h,a:h<a))},
            'handicap': {'period': 'regulation only', 'home_line': home_line,
                         'home': quote(pc), 'away': quote(1-pc)},
            'total': {'period': 'regulation only', 'line': line,
                      'over': quote(po), 'under': quote(1-po)},
            'winner_selection': 'home' if ph>=.5 else 'away',
            'assumptions': 'Independent Poisson; no home adjustment; ties split 50/50 for winner; no calibration, injuries or starters.'}
