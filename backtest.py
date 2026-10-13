#!/usr/bin/env python3
"""
EDGE PROTOCOL backtester (skeleton).

Replays the live scanner's rules (screener.stage/setup/score/filters) over daily history:

  * Signal is computed from data up to the close of day t only (all indicators are causal;
    tests/test_backtest.py checks the vectorised series against screener.indicators()).
  * Entry is on day t+1 (open, or a buy-stop above the signal-day high with --trigger prior_high).
  * Stops fill at the stop, or at the open if the bar gaps through it. If a stop and a target
    are both inside one bar the stop wins.
  * Costs: statutory/brokerage bps per side plus slippage bps per side.
  * Results are in R-multiples per trade, then a portfolio simulation (risk-based sizing from
    risk.py, position cap, open-risk budget, mark-to-market equity) gives drawdown and CAGR.

KNOWN LIMITATIONS (printed in every report):
  * Survivorship bias: the universe is today's constituents, so historical results are optimistic.
  * The StockEdge flag cannot be backtested (no point-in-time history), so tiers are by score.
  * Daily bars only; no intraday path, so stop-vs-target ordering inside a bar is assumed.
  * Yahoo adjusted prices, no delisting data, no circuit-limit / liquidity modelling.
"""
import argparse, json, math, os, sys
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

import screener as sc
from risk import size_position, stop_distance

WARMUP = 250   # bars before the first signal, mirrors the ~1y the live scan sees


@dataclass
class Config:
    min_score: int = 72
    trigger: str = 'none'          # 'none' (next open) | 'prior_high' (buy-stop above signal high)
    target_r: float = 0.0          # 0 = no fixed target
    exit_mode: str = 'ema20'       # 'none' | 'ema20' | 'ema50' (close below, exit next open) | 'chandelier'
    trail_k: float = 3.0           # chandelier: highest high since entry - k*ATR, ratchets up only
    max_hold: int = 40             # trading days
    slippage_bps: float = 10.0     # per side
    cost_bps: float = 15.0         # brokerage + STT + GST + stamp, per side (delivery)
    capital: float = 565000.0
    risk_pct: float = 0.005
    max_pos_pct: float = 0.25
    max_open_risk: float = 0.015
    split_date: str = '2023-01-01' # entries before = design period, on/after = hold-out


# --------------------------------------------------------------------------------------
# Indicators: vectorised twin of screener.indicators() (verified equal in tests)
# --------------------------------------------------------------------------------------
def indicator_series(df):
    c = df['Close'].astype(float); h = df['High'].astype(float)
    l = df['Low'].astype(float);   v = df['Volume'].astype(float)
    e20 = c.ewm(span=20, adjust=False).mean()
    e50 = c.ewm(span=50, adjust=False).mean()
    e200 = c.ewm(span=200, adjust=False).mean()
    rsi = sc.compute_rsi(c)
    st, sd = sc.compute_supertrend(h, l, c)
    atr = sc.compute_atr(h, l, c)
    v10 = v.shift(1).rolling(10).mean()     # live: mean of the 10 bars before the current one
    v5 = v.shift(1).rolling(5).mean()
    h52 = h.rolling(252, min_periods=1).max()
    out = pd.DataFrame({
        'price': c, 'ema_20': e20, 'ema_50': e50, 'ema_200': e200,
        'ema20_slope': (e20 / e20.shift(5) - 1) * 100,
        'ema50_slope': (e50 / e50.shift(5) - 1) * 100,
        'ema200_slope': (e200 / e200.shift(10) - 1) * 100,
        'rsi': rsi, 'rsi_5ago': rsi.shift(5),
        'st_dir': sd.where(st.notna(), 0).astype(int),
        'vol_ratio': (v / v10).where(v10 > 0, 1.0),
        'vol_5d': (v / v5).where(v5 > 0, 1.0),
        'ema20_dist': (c - e20) / e20 * 100,
        'from_52h': (c - h52) / h52 * 100,
        'atr': atr, 'atr_pct': atr / c * 100,
        'high': h, 'low': l,
    })
    return out


def base_signals(df):
    """Per-day scanner output independent of any threshold: score, stage, setup, passed (filters ok)."""
    ind = indicator_series(df)
    rows = []
    for i in range(len(ind)):
        if i < WARMUP:
            rows.append((0, 0, '', False)); continue
        d = ind.iloc[i].to_dict()
        if any(pd.isna(d[k]) for k in ('ema_200', 'ema200_slope', 'rsi', 'atr', 'rsi_5ago', 'ema20_slope')):
            rows.append((0, 0, '', False)); continue
        stg = sc.stage(d)
        ok, _ = sc.filters(d, stg)
        if not ok:
            rows.append((0, stg, '', False)); continue
        stp, _ = sc.setup(d)
        s, _ = sc.score(d, stg, stp)
        rows.append((s, stg, stp, True))
    sig = pd.DataFrame(rows, index=ind.index, columns=['score', 'stage', 'setup', 'passed'])
    return ind, sig


def signals_for(df, cfg):
    ind, sig = base_signals(df)
    sig['signal'] = sig['passed'] & (sig['score'] >= cfg.min_score)
    return ind, sig


def prepare(frames):
    """Compute indicators/signals once per symbol so many configs can be replayed cheaply."""
    out = {}
    for sym, df in frames.items():
        if len(df) < WARMUP + 20:
            continue
        ind, sig = base_signals(df)
        out[sym] = {
            'dates': df.index, 'ind': ind, 'sig': sig,
            'a': {'open': df['Open'].astype(float).values, 'high': df['High'].astype(float).values,
                  'low': df['Low'].astype(float).values, 'close': df['Close'].astype(float).values,
                  'ema20': ind['ema_20'].values, 'ema50': ind['ema_50'].values, 'atr': ind['atr'].values},
        }
    return out


# --------------------------------------------------------------------------------------
# Single-trade simulation
# --------------------------------------------------------------------------------------
def simulate_trade(a, s, cfg, setup='', score=0):
    """a: dict of numpy arrays open/high/low/close/ema20/atr. s: signal-day index.
    Returns trade dict or None if the entry never triggers."""
    O, H, L, C, E20 = a['open'], a['high'], a['low'], a['close'], a['ema20']
    n = len(C); e = s + 1
    if e >= n:
        return None
    sd = stop_distance(C[s], a['atr'][s])
    stop = C[s] - sd
    slip = cfg.slippage_bps / 1e4
    if cfg.trigger == 'prior_high':
        if H[e] < H[s]:
            return None                       # buy-stop never triggered; signal expires
        raw_fill = max(O[e], H[s])
    else:
        raw_fill = O[e]
    fill = raw_fill * (1 + slip)
    if fill <= stop:
        # gapped open below the planned stop: still taken at the open, as a loss
        return _finish(a, s, e, e, fill, stop, O[e], 'gap_stop', cfg, setup, score, sd)
    target = fill + cfg.target_r * sd if cfg.target_r > 0 else None
    cur_stop, hh = stop, H[e]
    ref = a['ema50'] if cfg.exit_mode == 'ema50' else E20

    for d in range(e, n):
        why = 'trail' if cur_stop > stop else 'stop'
        if d > e and O[d] <= cur_stop:
            return _finish(a, s, e, d, fill, stop, O[d], 'gap_' + why, cfg, setup, score, sd)
        if L[d] <= cur_stop:
            return _finish(a, s, e, d, fill, stop, min(cur_stop, O[d]) if d > e else cur_stop, why, cfg, setup, score, sd)
        if target is not None and d > e and O[d] >= target:
            return _finish(a, s, e, d, fill, stop, O[d], 'target_gap', cfg, setup, score, sd)
        if target is not None and H[d] >= target:
            return _finish(a, s, e, d, fill, stop, target, 'target', cfg, setup, score, sd)
        if d - e + 1 >= cfg.max_hold:
            return _finish(a, s, e, d, fill, stop, C[d], 'time', cfg, setup, score, sd)
        if cfg.exit_mode in ('ema20', 'ema50') and C[d] < ref[d]:
            if d + 1 < n:
                return _finish(a, s, e, d + 1, fill, stop, O[d + 1], cfg.exit_mode, cfg, setup, score, sd)
            # exit signal on the final bar: the real exit is tomorrow's open, which we don't have yet
            return _finish(a, s, e, d, fill, stop, C[d], cfg.exit_mode + '_pending', cfg, setup, score, sd)
        if cfg.exit_mode == 'chandelier':      # trail set at today's close, active from tomorrow
            hh = max(hh, H[d])
            cur_stop = max(cur_stop, hh - cfg.trail_k * a['atr'][d])
    return _finish(a, s, e, n - 1, fill, stop, C[n - 1], 'end_of_data', cfg, setup, score, sd)


def _finish(a, s, e, d_exit, fill, stop, exit_raw, reason, cfg, setup, score, plan_risk):
    slip = cfg.slippage_bps / 1e4
    exit_px = exit_raw * (1 - slip)
    cost = cfg.cost_bps / 1e4 * (fill + exit_px)
    pnl = exit_px - fill - cost
    # R is measured against the stop distance a trader sees on the signal day (what sizing uses)
    return {
        'signal_idx': s, 'entry_idx': e, 'exit_idx': d_exit,
        'entry': round(fill, 4), 'stop': round(stop, 4), 'exit': round(exit_px, 4),
        'plan_risk': plan_risk, 'pnl_per_share': pnl, 'r': pnl / plan_risk,
        'reason': reason, 'hold': d_exit - e + 1, 'setup': setup, 'score': int(score),
    }


FEATURES = ['rsi', 'volr', 'nrising', 'near52', 'from_52h', 'ema20_dist', 'atr_pct']


def _features(row):
    return {'rsi': row['rsi'], 'volr': max(row['vol_ratio'], row['vol_5d']),
            'nrising': int((row['ema20_slope'] > 0) + (row['ema50_slope'] > 0) + (row['ema200_slope'] > 0)),
            'near52': int(-18 <= row['from_52h'] <= -3), 'from_52h': row['from_52h'],
            'ema20_dist': row['ema20_dist'], 'atr_pct': row['atr_pct']}


def generate_trades(frames, cfg, bench=None, prepared=None):
    """One sequential position per symbol (a symbol can't re-enter until its trade has exited)."""
    prepared = prepared if prepared is not None else prepare(frames)
    trades = []
    bench_up = None
    if bench is not None and len(bench) > 200:
        bench_up = (bench > bench.ewm(span=200, adjust=False).mean())
    for sym, p in prepared.items():
        ind, sig, a, dates = p['ind'], p['sig'], p['a'], p['dates']
        flag = (sig['passed'] & (sig['score'] >= cfg.min_score)).values
        i = WARMUP
        while i < len(dates) - 1:
            if flag[i]:
                t = simulate_trade(a, i, cfg, sig['setup'].iat[i], sig['score'].iat[i])
                if t:
                    t['symbol'] = sym
                    t['signal_date'] = dates[t['signal_idx']]
                    t['entry_date'] = dates[t['entry_idx']]
                    t['exit_date'] = dates[t['exit_idx']]
                    t.update(_features(ind.iloc[i]))
                    if bench_up is not None:
                        k = bench_up.index.searchsorted(t['signal_date'], side='right') - 1
                        t['regime'] = ('bull' if bench_up.iat[k] else 'bear') if k >= 0 else 'unknown'
                    else:
                        t['regime'] = 'unknown'
                    trades.append(t)
                    i = t['exit_idx'] + 1
                    continue
            i += 1
    cols = ['symbol', 'signal_date', 'entry_date', 'exit_date', 'entry', 'stop', 'exit', 'plan_risk', 'r', 'pnl_per_share',
            'reason', 'hold', 'setup', 'score', 'regime'] + FEATURES
    df = pd.DataFrame(trades)
    return df[cols] if len(df) else pd.DataFrame(columns=cols)


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------
def r_stats(r):
    r = pd.Series(r, dtype=float)
    n = len(r)
    if n == 0:
        return {'trades': 0}
    wins, losses = r[r > 0], r[r <= 0]
    se = r.std(ddof=1) / math.sqrt(n) if n > 1 else float('nan')
    return {
        'trades': n,
        'win_rate': round(len(wins) / n, 3),
        'avg_r': round(r.mean(), 3),
        'avg_r_ci95': [round(r.mean() - 1.96 * se, 3), round(r.mean() + 1.96 * se, 3)] if n > 1 else None,
        'avg_win_r': round(wins.mean(), 3) if len(wins) else 0.0,
        'avg_loss_r': round(losses.mean(), 3) if len(losses) else 0.0,
        'profit_factor': round(wins.sum() / -losses.sum(), 2) if losses.sum() < 0 else None,
        'worst_r': round(r.min(), 2),
    }


def bucket_stats(trades):
    out = {}
    if trades.empty:
        return out
    bands = pd.cut(trades['score'], [0, 71, 79, 89, 101], labels=['<72', '72-79', '80-89', '90+'], right=True)
    out['by_score'] = {str(k): r_stats(g['r']) for k, g in trades.groupby(bands, observed=True)}
    out['by_setup'] = {k: r_stats(g['r']) for k, g in trades.groupby('setup')}
    out['by_regime'] = {k: r_stats(g['r']) for k, g in trades.groupby('regime')}
    out['by_exit'] = {k: r_stats(g['r']) for k, g in trades.groupby('reason')}
    out['by_year'] = {str(k): r_stats(g['r']) for k, g in trades.groupby(trades['entry_date'].dt.year)}
    return out


def split_in_out_of_sample(trades, split_date):
    cut = pd.Timestamp(split_date)
    return trades[trades['entry_date'] < cut], trades[trades['entry_date'] >= cut]


# --------------------------------------------------------------------------------------
# Portfolio simulation (mark-to-market)
# --------------------------------------------------------------------------------------
def portfolio(frames, trades, cfg):
    if trades.empty:
        return {'accepted': 0}, pd.Series(dtype=float)
    dates = sorted(set().union(*[set(df.index) for df in frames.values()]))
    dates = [d for d in dates if trades['entry_date'].min() <= d <= trades['exit_date'].max()]
    closes = {s: df['Close'].astype(float) for s, df in frames.items()}
    by_entry = {d: g.sort_values('score', ascending=False) for d, g in trades.groupby('entry_date')}
    by_exit = {}
    realized = cfg.capital
    open_pos = []   # dicts: symbol, shares, entry, stop, exit_date, pnl_per_share
    equity, accepted, rejected = {}, 0, 0
    for d in dates:
        eq_now = realized + sum(p['shares'] * (_px(closes[p['symbol']], d, p['entry']) - p['entry']) for p in open_pos)
        for _, t in by_entry.get(d, pd.DataFrame()).iterrows():
            if any(p['symbol'] == t['symbol'] for p in open_pos):
                rejected += 1; continue
            risk_open = sum(p['shares'] * p['plan_risk'] for p in open_pos)
            sz = size_position(eq_now, cfg.risk_pct, t['entry'], t['plan_risk'], cfg.max_pos_pct)
            if sz['shares'] < 1 or risk_open + sz['risk_amount'] > eq_now * cfg.max_open_risk:
                rejected += 1; continue
            open_pos.append({'symbol': t['symbol'], 'shares': sz['shares'], 'entry': t['entry'], 'plan_risk': t['plan_risk'],
                             'exit_date': t['exit_date'], 'pnl_per_share': t['pnl_per_share']})
            accepted += 1
        still = []
        for p in open_pos:
            if p['exit_date'] <= d:
                realized += p['shares'] * p['pnl_per_share']
            else:
                still.append(p)
        open_pos = still
        equity[d] = realized + sum(p['shares'] * (_px(closes[p['symbol']], d, p['entry']) - p['entry']) for p in open_pos)
    eq = pd.Series(equity)
    return _equity_stats(eq, cfg.capital, accepted, rejected), eq


def _px(series, d, default):
    k = series.index.searchsorted(d, side='right') - 1
    return float(series.iat[k]) if k >= 0 else default


def _equity_stats(eq, start, accepted, rejected):
    if eq.empty:
        return {'accepted': accepted, 'rejected': rejected}
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    dd = eq / eq.cummax() - 1
    under = (dd < 0).astype(int)
    longest = cur = 0
    for u in under:
        cur = cur + 1 if u else 0
        longest = max(longest, cur)
    return {
        'accepted': accepted, 'rejected_by_limits': rejected,
        'final_equity': round(float(eq.iloc[-1]), 0),
        'total_return_pct': round((eq.iloc[-1] / start - 1) * 100, 1),
        'cagr_pct': round(((eq.iloc[-1] / start) ** (1 / years) - 1) * 100, 1) if eq.iloc[-1] > 0 else -100.0,
        'max_drawdown_pct': round(float(dd.min()) * 100, 1),
        'longest_drawdown_days': int(longest),
        'years': round(years, 2),
    }


def benchmark_stats(bench, start, end):
    if bench is None or bench.empty:
        return None
    b = bench[(bench.index >= start) & (bench.index <= end)]
    if len(b) < 2:
        return None
    years = max((b.index[-1] - b.index[0]).days / 365.25, 1e-9)
    dd = b / b.cummax() - 1
    return {'cagr_pct': round(((b.iloc[-1] / b.iloc[0]) ** (1 / years) - 1) * 100, 1),
            'max_drawdown_pct': round(float(dd.min()) * 100, 1)}


# --------------------------------------------------------------------------------------
# Orchestration, data, report
# --------------------------------------------------------------------------------------
def run(frames, cfg, bench=None, prepared=None):
    trades = generate_trades(frames, cfg, bench, prepared)
    ins, oos = split_in_out_of_sample(trades, cfg.split_date)
    pstats, eq = portfolio(frames, trades, cfg)
    report = {
        'config': asdict(cfg),
        'universe': {'symbols': len(frames), 'survivorship_bias': True},
        'all_trades': r_stats(trades['r']) if len(trades) else {'trades': 0},
        'in_sample': r_stats(ins['r']) if len(ins) else {'trades': 0},
        'out_of_sample': r_stats(oos['r']) if len(oos) else {'trades': 0},
        'oos_starts': cfg.split_date,
        'portfolio': pstats,
        'benchmark': benchmark_stats(bench, eq.index[0], eq.index[-1]) if len(eq) else None,
        'buckets': bucket_stats(trades),
    }
    return report, trades, eq


def load_history(years, cache):
    if cache and os.path.exists(cache):
        raw = pd.read_pickle(cache)
    else:
        import yfinance as yf
        raw = yf.download(tickers=sc.YF_TICKERS + sc.ALIAS_TICKERS + ['^NSEI'], period=f'{years}y', interval='1d',
                          group_by='ticker', auto_adjust=True, progress=False, threads=True, timeout=120)
        if raw is None or raw.empty:
            sys.exit('FATAL: history download failed')
        if cache:
            raw.to_pickle(cache)
    frames = {}
    frame_last = raw.index.max()
    for sym in sc.NSE_STOCKS:
        df, used, _ = sc.resolve_symbol(raw, sym, frame_last)
        if df is not None:
            frames[used] = df
    bench = None
    try:
        bench = raw['^NSEI']['Close'].dropna().astype(float)
    except Exception:
        pass
    if len(frames) < 0.8 * len(sc.NSE_STOCKS):
        sys.exit(f'FATAL: only {len(frames)}/{len(sc.NSE_STOCKS)} symbols had history')
    return frames, bench


def to_markdown(rep, title):
    def row(name, s):
        if not s or not s.get('trades'):
            return f'| {name} | 0 | | | | |'
        ci = s.get('avg_r_ci95')            # None when a bucket has a single trade
        ci_txt = f" ({ci[0]:+.2f}..{ci[1]:+.2f})" if ci else ' (n/a: 1 trade)'
        return (f"| {name} | {s['trades']} | {s['win_rate']:.0%} | {s['avg_r']:+.2f}"
                f"{ci_txt} | {s['profit_factor']} | {s['worst_r']} |")
    L = [f'# {title}', '',
         f"Config: `{json.dumps(rep['config'])}`", '',
         '| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |', '|---|---|---|---|---|---|',
         row('ALL', rep['all_trades']), row('Design period', rep['in_sample']),
         row(f"Hold-out (from {rep['oos_starts']})", rep['out_of_sample'])]
    for key, label in [('by_score', 'Score'), ('by_setup', 'Setup'), ('by_regime', 'Regime'),
                       ('by_exit', 'Exit'), ('by_year', 'Year')]:
        for k, v in rep['buckets'].get(key, {}).items():
            L.append(row(f'{label}: {k}', v))
    L += ['', f"Portfolio: `{json.dumps(rep['portfolio'])}`", f"Benchmark (Nifty buy&hold): `{json.dumps(rep['benchmark'])}`", '',
          '**Limitations:** survivorship bias (today\'s universe), StockEdge flag not testable, daily bars only '
          '(stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; '
          'an edge that fails here is unlikely to exist, one that passes is not yet proven.']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=10)
    ap.add_argument('--cache', default='history_cache.pkl')
    ap.add_argument('--out', default='reports')
    ap.add_argument('--name', default='baseline')
    ap.add_argument('--min-score', type=int, default=72)
    ap.add_argument('--trigger', choices=['none', 'prior_high'], default='none')
    ap.add_argument('--target-r', type=float, default=0.0)
    ap.add_argument('--exit-mode', choices=['none', 'ema20', 'ema50', 'chandelier'], default='ema20')
    ap.add_argument('--trail-k', type=float, default=3.0)
    ap.add_argument('--max-hold', type=int, default=40)
    ap.add_argument('--capital', type=float, default=565000)
    ap.add_argument('--risk-pct', type=float, default=0.5, help='percent')
    a = ap.parse_args()
    cfg = Config(min_score=a.min_score, trigger=a.trigger, target_r=a.target_r, exit_mode=a.exit_mode, trail_k=a.trail_k,
                 max_hold=a.max_hold, capital=a.capital, risk_pct=a.risk_pct / 100)
    frames, bench = load_history(a.years, a.cache)
    rep, trades, eq = run(frames, cfg, bench)
    os.makedirs(a.out, exist_ok=True)
    with open(f'{a.out}/backtest_{a.name}.json', 'w') as f:
        json.dump(rep, f, indent=2, default=str)
    trades.to_csv(f'{a.out}/trades_{a.name}.csv', index=False)
    md = to_markdown(rep, f'Backtest: {a.name}')
    with open(f'{a.out}/backtest_{a.name}.md', 'w') as f:
        f.write(md)
    print(md)


if __name__ == '__main__':
    main()
