"""Pre-trade analysis for each signal: tradeability checks and market context.

IMPORTANT: these checks are execution and risk hygiene, not alpha. They were not part of the
backtested rules, so they must not be read as improving expectancy. A 'block' hides a signal from the
'tradeable now' view only for practical reasons (can't be traded cleanly); 'warn' is information for
your own judgement. The signal itself (strategy.py) is unchanged.
"""
import numpy as np

THIN_CR = 2.0           # avg daily traded value below this (Rs crore) -> block
LOW_CR = 5.0            # below this -> warn
STOP_WARN = 10.0        # stop distance % of entry
STOP_BLOCK = 15.0
GAP_WARN = 4.0          # buy-stop more than this % above the close
RANGE_WARN = 0.35       # close in the lower third of the signal day's range
EXTENDED_WARN = 8.0     # % above EMA20
VOLUME_WARN = 0.5       # volume ratio below this


def _chk(cid, status, text):
    return {'id': cid, 'status': status, 'text': text}


def build_checks(rec):
    """rec needs: avg_value_cr, stop_pct, trigger_gap_pct, close_in_range, ema_dist_pct, vol_ratio."""
    out = []
    v = rec['avg_value_cr']
    if v < THIN_CR:
        out.append(_chk('liquidity', 'block', f'Thin: ₹{v:.1f} cr average daily traded value (below ₹{THIN_CR:g} cr)'))
    elif v < LOW_CR:
        out.append(_chk('liquidity', 'warn', f'Modest liquidity: ₹{v:.1f} cr/day; use limit orders'))
    else:
        out.append(_chk('liquidity', 'ok', f'Liquid: ₹{v:.0f} cr/day average traded value'))

    s = rec['stop_pct']
    if s > STOP_BLOCK:
        out.append(_chk('stop_width', 'block', f'Stop is {s:.1f}% below entry: too wide to size sensibly, high gap risk'))
    elif s > STOP_WARN:
        out.append(_chk('stop_width', 'warn', f'Wide stop ({s:.1f}%): small position and real gap risk'))
    else:
        out.append(_chk('stop_width', 'ok', f'Stop {s:.1f}% below entry'))

    g = rec['trigger_gap_pct']
    if g > GAP_WARN:
        out.append(_chk('trigger_gap', 'warn', f'Buy-stop is {g:.1f}% above the close: the signal day closed well off its high'))
    else:
        out.append(_chk('trigger_gap', 'ok', f'Buy-stop {g:.1f}% above the close'))

    if rec['close_in_range'] < RANGE_WARN:
        out.append(_chk('close_strength', 'warn', f"Weak close: bottom {rec['close_in_range'] * 100:.0f}% of the day's range"))
    else:
        out.append(_chk('close_strength', 'ok', f"Close in the top {100 - rec['close_in_range'] * 100:.0f}% of the day's range"))

    e = rec['ema_dist_pct']
    out.append(_chk('extension', 'warn', f'Extended: {e:.1f}% above EMA20') if e > EXTENDED_WARN
               else _chk('extension', 'ok', f'{e:.1f}% from EMA20'))

    vr = rec['vol_ratio']
    out.append(_chk('volume', 'warn', f'Light volume ({vr:.1f}x average)') if vr < VOLUME_WARN
               else _chk('volume', 'ok', f'Volume {vr:.1f}x average'))
    return out


def execution_ok(checks):
    return not any(c['status'] == 'block' for c in checks)


def market_context(nifty_close_series, n_stage2, n_processed, n_signals):
    """Informational market backdrop. The backtest found regime made little difference to the rules,
    so none of this gates a signal."""
    ctx = {'breadth_stage2_pct': round(100 * n_stage2 / max(n_processed, 1), 1), 'signals': n_signals}
    c = None if nifty_close_series is None else nifty_close_series.dropna().astype(float)
    if c is None or len(c) < 60:
        ctx['nifty'] = None
        return ctx
    e50, e200 = c.ewm(span=50, adjust=False).mean().iloc[-1], c.ewm(span=200, adjust=False).mean().iloc[-1]
    last = float(c.iloc[-1])
    if last > e50 > e200:
        trend = 'Uptrend: above EMA50 and EMA200'
    elif last > e200:
        trend = 'Above EMA200 but below EMA50: pullback within an uptrend'
    elif last > e50:
        trend = 'Below EMA200, above EMA50: bounce in a weak market'
    else:
        trend = 'Downtrend: below EMA50 and EMA200'
    ctx['nifty'] = {'close': round(last, 1), 'ema50': round(float(e50), 1), 'ema200': round(float(e200), 1),
                    'vs_ema200_pct': round((last / float(e200) - 1) * 100, 1),
                    'change_20d_pct': round((last / float(c.iloc[-21]) - 1) * 100, 1) if len(c) > 21 else None,
                    'drawdown_pct': round((last / float(c.tail(252).max()) - 1) * 100, 1), 'trend': trend}
    return ctx


def sparkline(df, n=60):
    """Last n closes with EMA20/EMA50, for a small chart on the desk."""
    c = df['Close'].astype(float)
    e20, e50 = c.ewm(span=20, adjust=False).mean(), c.ewm(span=50, adjust=False).mean()
    t = lambda s: [round(float(x), 2) for x in s.tail(n)]
    return {'close': t(c), 'ema20': t(e20), 'ema50': t(e50), 'from': str(c.tail(n).index[0].date())}


def day_features(df, ind):
    """Features for the checks, from the signal day's bar and recent volume."""
    close, high, low = float(ind['price']), float(ind['high']), float(ind['low'])
    rng = high - low
    return {
        'avg_value_cr': round(float((df['Close'].astype(float) * df['Volume'].astype(float)).tail(20).mean()) / 1e7, 2),
        'close_in_range': round((close - low) / rng, 3) if rng > 0 else 0.5,
    }
