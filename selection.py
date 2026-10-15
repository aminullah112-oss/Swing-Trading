"""Stock-selection context for each signal: relative-strength rank, tier, sector, regime and size scaling.

Evidence status, stated plainly (do not read more into the labels than this):
  * relative strength is the one selection idea with supporting evidence (the momentum-30 replica beat C0 on hold-out), but
    ADMITTING signals in rank order was tested in reports/benchmarks.md and FAILED, so the rank is shown, not used to reorder.
  * the 'preferred' tier is the PREREG_v2 stack (V2-2). It is a hypothesis until that test passes; C0 trades every signal.
  * the sector cap and the volatility size scale only remove or shrink positions. The regime halving is OFF (tested, failed).
"""
import json
import os

import numpy as np
import pandas as pd

import settings

HERE = os.path.dirname(os.path.abspath(__file__))
STACK = {'min_rank': 0.70, 'min_from_52h_pct': -10.0, 'min_adv20_value_cr': 5.0, 'max_atr_pct': 4.0}      # = PREREG_v2 V2-2


def load_sectors(path=None):
    try:
        with open(path or os.path.join(HERE, 'universe', 'sectors.json')) as f:
            return json.load(f)['sectors']
    except (OSError, ValueError, KeyError):
        return {}


def sector_of(symbol, sectors):
    return sectors.get(symbol) or f'UNKNOWN:{symbol}'      # an unmapped symbol never shares a bucket, so it is never capped by mistake


def momentum(df):
    """Volatility-adjusted 6- and 12-month momentum on the last bar (same formula as backtest.indicator_series)."""
    c = df['Close'].astype(float)
    if len(c) < 253:
        return np.nan
    r = c.pct_change().rolling(252).std().iloc[-1]
    return float(0.5 * ((c.iloc[-1] / c.iloc[-127] - 1) + (c.iloc[-1] / c.iloc[-253] - 1)) / r) if r and r > 0 else np.nan


def rank_universe(frames):
    """{symbol: percentile 0-1} of momentum across the whole scanned universe on the latest bar (NaN if under 253 bars)."""
    m = pd.Series({s: momentum(df) for s, df in frames.items()})
    return m.rank(pct=True).to_dict()


def regime(nifty_close):
    if nifty_close is None or len(nifty_close) < 200:
        return 'unknown'
    c = nifty_close.astype(float)
    return 'bull' if c.iloc[-1] > c.ewm(span=200, adjust=False).mean().iloc[-1] else 'bear'


def tier(rec, rank, reg, blocked):
    """('avoid'|'preferred'|'standard', conditions). 'avoid' = a known event blocks the entry. Informational until PREREG_v2 reports."""
    cond = {
        'relative strength in the top 30%': rank is not None and rank == rank and rank >= STACK['min_rank'],
        'within 10% of the 52-week high': rec['from_52w_high'] >= STACK['min_from_52h_pct'],
        f"traded value at least INR {STACK['min_adv20_value_cr']:g} crore a day": rec['avg_value_cr'] >= STACK['min_adv20_value_cr'],
        f"ATR at most {STACK['max_atr_pct']:g}% of price": rec['atr_pct'] <= STACK['max_atr_pct'],
        'Nifty above its EMA200': reg == 'bull',
    }
    if blocked:
        return 'avoid', cond
    return ('preferred' if all(cond.values()) else 'standard'), cond


def size_multiplier(rec, reg):
    """(multiplier, notes). Only ever <= 1."""
    mult, notes = 1.0, []
    if settings.VOL_SCALE_ENABLED and rec['atr_pct'] > settings.VOL_SCALE_ATR_PCT:
        mult *= settings.VOL_SCALE_MULT
        notes.append(f"ATR {rec['atr_pct']:.1f}% above {settings.VOL_SCALE_ATR_PCT:g}%: size x{settings.VOL_SCALE_MULT}")
    if settings.REGIME_HALVING_ENABLED and reg == 'bear':
        mult *= 0.5
        notes.append('Nifty below EMA200: size x0.5')
    return mult, notes


def sector_counts(symbols, sectors):
    out = {}
    for s in symbols:
        g = sector_of(s, sectors)
        out[g] = out.get(g, 0) + 1
    return out


def sector_ok(symbol, active_symbols, sectors, cap=None):
    """(ok, sector, count_already_open)."""
    cap = cap or settings.MAX_PER_SECTOR
    g = sector_of(symbol, sectors)
    n = sector_counts(active_symbols, sectors).get(g, 0)
    return n < cap, g, n


def conviction(cond, blocked):
    """Checklist-based conviction, NOT a probability of profit. high = all five selection conditions hold (the PREREG_v2 stack),
    medium = three or four, low = two or fewer, avoid = a known event blocks the entry. No backtest has shown that any of these
    levels predicts returns; they only describe how many of the stack's conditions a signal meets."""
    met = sum(bool(v) for v in cond.values())
    level = 'avoid' if blocked else 'high' if met == len(cond) else 'medium' if met >= 3 else 'low'
    return {'level': level, 'met': met, 'of': len(cond)}
