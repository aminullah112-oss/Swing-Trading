"""Position sizing for EDGE PROTOCOL. Pure Python, no third-party imports.

sizer.js mirrors calcPosition() below; keep the two in step (tests/test_risk.py
pins the expected numbers for both).
"""
import math

MIN_STOP_PCT = 0.03   # stop distance never tighter than 3% of price
ATR_MULT     = 1.5


def stop_distance(price, atr, atr_mult=ATR_MULT, min_pct=MIN_STOP_PCT):
    return max(atr_mult * atr, price * min_pct)


def size_position(capital, risk_pct, price, stop_dist, max_pos_pct=0.25, cash=None):
    """Return the share count allowed by the strictest of the risk, exposure and cash limits.

    risk_pct and max_pos_pct are fractions (0.005 = 0.5%). Returns shares=0 when
    even one share breaks a limit; there is no forced minimum.
    """
    if min(capital, risk_pct, price, stop_dist) <= 0:
        return _result(0, price, stop_dist, 'invalid input')

    by_risk = math.floor(capital * risk_pct / stop_dist)
    limits  = {'risk': by_risk,
               'position cap': math.floor(capital * max_pos_pct / price)}
    if cash is not None:
        limits['cash'] = math.floor(cash / price)

    binding = min(limits, key=limits.get)
    shares  = max(0, limits[binding])
    note = None
    if shares == 0:
        note = f'0 shares: {binding} limit cannot fund one share'
    elif binding != 'risk':
        note = f'capped by {binding}'
    return _result(shares, price, stop_dist, note)


def _result(shares, price, stop_dist, note):
    return {
        'shares':      shares,
        'invested':    round(shares * price, 2),
        'stop_loss':   round(price - stop_dist, 2),
        'risk_amount': round(shares * stop_dist, 2),
        'target_1':    round(price + 2 * stop_dist, 2),
        'target_2':    round(price + 3 * stop_dist, 2),
        'rr_ratio':    '2:1 / 3:1',
        'note':        note,
    }
