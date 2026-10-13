#!/usr/bin/env python3
"""Same-universe benchmarks and pre-registered redesign tests.

Why same-universe: the stock list is today's survivors, which flatters every result. A benchmark built
from the SAME list and the SAME dates carries the same flattery, so strategy-vs-benchmark comparisons are
fair even though the absolute numbers are optimistic.

Pre-registered (fixed before any result was seen):

  Baseline  the live variant (prior_high / ema50 / 120d), risk-sized portfolio, as in grid.md.
  H1        a momentum portfolio built the way NSE builds Nifty200 Momentum 30: top 30 by the average of the
            cross-sectional z-scores of 6- and 12-month returns divided by daily volatility, rebalanced
            at the end of March and September, 25 bps per side on turnover. Equal weight (we lack market caps).
            This is the investable alternative the screen has to beat.
  H2        baseline, but same-day candidates are admitted in order of that momentum score instead of the old score.
  H3        baseline, but per-trade risk and the open-risk cap are halved when the Nifty is below its EMA200.

A hypothesis counts as an improvement only if (a) its Calmar ratio (CAGR / |max drawdown|) beats the baseline's in
BOTH the design period and the hold-out, AND (b) the hold-out daily-return difference versus the baseline has a
month-clustered 95% interval (Bonferroni-adjusted for the two tested hypotheses) that excludes zero. Rule (a) alone
passes by chance far too often; (b) is what makes a 'win' worth a forward test. Still a candidate, not a conclusion.
"""
import json
import os

import numpy as np
import pandas as pd

import analysis as an
import backtest as bt
import research as rs
import strategy

SPLIT = '2023-01-01'
TOP_N = 30
REBAL_MONTHS = (3, 9)
COST_BPS = 25.0
TRADING_DAYS = 252


# --------------------------------------------------------------------------- metrics
def perf(ret):
    """CAGR, max drawdown, Calmar and Sharpe-like ratio (rf = 0) from a daily simple-return series."""
    r = pd.Series(ret).dropna()
    if len(r) < 20:
        return None
    eq = (1 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    cagr = float(eq.iloc[-1] ** (1 / years) - 1) * 100
    dd = float((eq / eq.cummax() - 1).min()) * 100
    sd = float(r.std())
    return {'cagr_pct': round(cagr, 1), 'max_drawdown_pct': round(dd, 1),
            'calmar': round(cagr / abs(dd), 2) if dd < 0 else None,
            'sharpe': round(float(r.mean() / sd * np.sqrt(TRADING_DAYS)), 2) if sd > 0 else None,
            'days': int(len(r))}


def calendar_years(ret):
    r = pd.Series(ret).dropna()
    return {str(y): round(float((1 + g).prod() - 1) * 100, 1) for y, g in r.groupby(r.index.year)}


# --------------------------------------------------------------------------- momentum portfolio
def momentum_scores(closes):
    """Cross-sectional momentum score per date: mean of the z-scores of vol-adjusted 6m and 12m returns."""
    rets = closes.pct_change()
    vol = rets.rolling(TRADING_DAYS).std()
    def z(x):
        return x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1), axis=0)
    s6 = z((closes / closes.shift(126) - 1) / vol)
    s12 = z((closes / closes.shift(TRADING_DAYS) - 1) / vol)
    return (s6 + s12) / 2


def rebalance_dates(index, months=REBAL_MONTHS):
    """Last trading day of each rebalance month."""
    idx = pd.DatetimeIndex(index)
    df = pd.DataFrame({'d': idx, 'ym': idx.to_period('M')})
    last = df.groupby('ym')['d'].max()
    return [d for ym, d in last.items() if ym.month in months]


def momentum_portfolio(closes, top_n=TOP_N, months=REBAL_MONTHS, cost_bps=COST_BPS):
    """Daily net returns of the equal-weight top-N momentum portfolio, plus the holdings at each rebalance."""
    closes = closes.sort_index()
    scores = momentum_scores(closes)
    rets = closes.pct_change()
    rebal = [d for d in rebalance_dates(closes.index, months) if scores.loc[d].notna().sum() >= top_n]
    if not rebal:
        return pd.Series(dtype=float), {}
    out = pd.Series(0.0, index=closes.index[closes.index > rebal[0]])
    holdings, prev = {}, {}
    for i, d in enumerate(rebal):
        picks = scores.loc[d].dropna().nlargest(top_n).index.tolist()
        w_new = {s: 1.0 / len(picks) for s in picks}
        turnover = sum(abs(w_new.get(s, 0.0) - prev.get(s, 0.0)) for s in set(w_new) | set(prev))
        holdings[str(d.date())] = picks
        end = rebal[i + 1] if i + 1 < len(rebal) else closes.index[-1]
        seg = rets.loc[(rets.index > d) & (rets.index <= end), picks]
        daily = seg.mean(axis=1).fillna(0.0)                      # equal weight, rebalanced daily within the picks
        if len(daily):
            daily.iloc[0] -= turnover * cost_bps / 1e4
        out.loc[daily.index] = daily
        prev = w_new
    return out, holdings


# --------------------------------------------------------------------------- strategy portfolios
def _equity_returns(eq):
    return eq.pct_change().dropna() if len(eq) else pd.Series(dtype=float)


def strategy_portfolios(frames, trades, cfg, bench):
    """Portfolio equity for the baseline and for H2/H3, run separately over the design period and the hold-out."""
    split = pd.Timestamp(SPLIT)
    regime = an.regime_series(bench) if bench is not None else None

    def scale(d):                                                   # H3: half risk when the Nifty is below its EMA200
        if regime is None:
            return 1.0
        k = regime.index.searchsorted(pd.Timestamp(d), side='right') - 1
        return 1.0 if k < 0 or regime.iat[k] in ('uptrend', 'pullback_in_uptrend') else 0.5

    variants = {'baseline': {}, 'H2': {'order_col': 'mom'}, 'H3': {'risk_scale': scale}}
    out = {}
    for name, kw in variants.items():
        out[name] = {}
        for label, sel in (('full', trades), ('design', trades[trades['entry_date'] < split]),
                           ('holdout', trades[trades['entry_date'] >= split])):
            if sel.empty:
                continue
            _, eq = bt.portfolio(frames, sel, cfg, **kw)
            out[name][label] = _equity_returns(eq)
    return out


def _slice(ret, lo=None, hi=None):
    r = ret
    if lo is not None:
        r = r[r.index >= pd.Timestamp(lo)]
    if hi is not None:
        r = r[r.index < pd.Timestamp(hi)]
    return r


# --------------------------------------------------------------------------- report
def compute_series(frames, bench, prepared=None, cfg=None):
    """All daily return series used in the report (also reused by official_index.py)."""
    cfg = cfg or strategy.backtest_config()
    prepared = prepared if prepared is not None else bt.prepare(frames)
    trades = bt.generate_trades(frames, cfg, bench, prepared)
    closes = pd.DataFrame({s: df['Close'].astype(float) for s, df in frames.items()}).sort_index()
    ew = closes.pct_change().mean(axis=1)
    nifty = bench.astype(float).pct_change() if bench is not None else None
    mom, hold = momentum_portfolio(closes)
    strat = strategy_portfolios(frames, trades, cfg, bench)
    return {'trades': trades, 'ew': ew, 'nifty': nifty, 'mom': mom, 'holdings': hold, 'strat': strat}


def run(frames, bench, prepared=None, cfg=None, series_bundle=None):
    s = series_bundle or compute_series(frames, bench, prepared, cfg)
    trades, ew, nifty, mom, hold, strat = s['trades'], s['ew'], s['nifty'], s['mom'], s['holdings'], s['strat']
    series = {'Live strategy (baseline)': None, 'H1 momentum-30 replica': mom, 'Equal-weight universe': ew, 'Nifty 50': nifty}
    periods = {'design': (None, SPLIT), 'holdout': (SPLIT, None)}
    table = {}
    for label, (lo, hi) in periods.items():
        table[label] = {'Live strategy (baseline)': perf(strat['baseline'].get(label, pd.Series(dtype=float)))}
        for name, r in series.items():
            if r is not None:
                table[label][name] = perf(_slice(r, lo, hi))
    # first rebalance leaves the design period short; report the date the momentum replica starts
    hyp = {}
    for name in ('baseline', 'H2', 'H3'):
        hyp[name] = {p: perf(strat[name].get(p, pd.Series(dtype=float))) for p in ('design', 'holdout')}
    def diff_ci(r1, r2, alpha):
        d = (r1 - r2).dropna()
        if len(d) < 60:
            return None
        ci = rs.cluster_ci_mean(d.values, d.index.to_period('M').astype(str).values, alpha=alpha)
        return [float(ci[0]) * 100, float(ci[1]) * 100] if ci else None          # in percent per day

    diffs = {}
    verdict = {}
    for name in ('H2', 'H3'):
        calmar_ok = True
        diffs[name] = {}
        for p in ('design', 'holdout'):
            a, b = hyp[name][p], hyp['baseline'][p]
            calmar_ok &= bool(a and b and a['calmar'] is not None and b['calmar'] is not None and a['calmar'] > b['calmar'])
            diffs[name][p] = diff_ci(strat[name].get(p, pd.Series(dtype=float)), strat['baseline'].get(p, pd.Series(dtype=float)),
                                     alpha=0.05 / 2)
        ci_ok = bool(diffs[name]['holdout'] and diffs[name]['holdout'][0] > 0)
        verdict[name] = bool(calmar_ok and ci_ok)
        verdict[name + '_calmar_both'] = bool(calmar_ok)
        verdict[name + '_holdout_ci_excludes_zero'] = ci_ok
    hb = table['holdout']
    base_c = hb['Live strategy (baseline)']['calmar'] if hb.get('Live strategy (baseline)') else None
    mom_c = hb['H1 momentum-30 replica']['calmar'] if hb.get('H1 momentum-30 replica') else None
    verdict['baseline_beats_momentum_holdout'] = bool(base_c is not None and mom_c is not None and base_c >= mom_c)
    years = {'Live strategy (baseline)': calendar_years(strat['baseline'].get('full', pd.Series(dtype=float))),
             'H1 momentum-30 replica': calendar_years(mom), 'Equal-weight universe': calendar_years(ew)}
    if nifty is not None:
        years['Nifty 50'] = calendar_years(nifty)
    diffs['baseline_minus_momentum_holdout'] = diff_ci(strat['baseline'].get('holdout', pd.Series(dtype=float)), _slice(mom, SPLIT), alpha=0.05)
    rep = {'split': SPLIT, 'periods': table, 'hypotheses': hyp, 'verdict': verdict, 'diff_ci': diffs, 'calendar_years': years,
           'momentum_first_rebalance': str(mom.index[0].date()) if len(mom) else None, 'trades': int(len(trades)),
           'momentum_holdings_last': (list(hold.items())[-1] if hold else None)}
    return rep


def markdown(rep):
    def row(name, v):
        if not v:
            return f'| {name} | n/a | n/a | n/a | n/a |'
        return f"| {name} | {v['cagr_pct']}% | {v['max_drawdown_pct']}% | {v['calmar']} | {v['sharpe']} |"
    L = ['# Benchmarks and pre-registered redesign tests', '',
         'All series use the **same stock list and dates**, so survivorship flatters each equally. Absolute numbers are optimistic; '
         'comparisons are the point. Calmar = CAGR / |max drawdown|; Sharpe uses rf = 0. The strategy rows are a risk-sized portfolio '
         '(at most about three positions at 0.5% risk), so they are partly in cash: compare Calmar and Sharpe, not raw CAGR.', '']
    for label, title in (('design', f'Design period (before {rep["split"]})'), ('holdout', f'Hold-out (from {rep["split"]})')):
        L += [f'## {title}', '', '| Series | CAGR | Max DD | Calmar | Sharpe |', '|---|---|---|---|---|']
        for name, v in rep['periods'][label].items():
            L.append(row(name, v))
        L.append('')
    L += ['## Pre-registered hypotheses', '',
          'Improvement needs (a) a higher Calmar than the baseline in both periods and (b) a hold-out daily-return difference whose month-clustered '
          'interval (Bonferroni, 2 hypotheses) excludes zero.', '',
          '| Variant | Design CAGR / DD / Calmar | Hold-out CAGR / DD / Calmar | (a) Calmar up in both | Hold-out return diff vs baseline, %/day (CI) | (b) CI > 0 | Improves? |',
          '|---|---|---|---|---|---|---|']
    names = {'baseline': 'Baseline (live variant)', 'H2': 'H2: admit by momentum rank', 'H3': 'H3: half risk when Nifty < EMA200'}
    for k, nm in names.items():
        d, h = rep['hypotheses'][k]['design'], rep['hypotheses'][k]['holdout']
        f = lambda v: f"{v['cagr_pct']}% / {v['max_drawdown_pct']}% / {v['calmar']}" if v else 'n/a'
        if k == 'baseline':
            L.append(f'| {nm} | {f(d)} | {f(h)} | — | — | — | — |')
            continue
        ci = rep['diff_ci'][k]['holdout']
        cit = f'{ci[0]:+.4f}..{ci[1]:+.4f}' if ci else 'n/a'
        yn = lambda x: '✅' if x else '❌'
        L.append(f"| {nm} | {f(d)} | {f(h)} | {yn(rep['verdict'][k + '_calmar_both'])} | {cit} | {yn(rep['verdict'][k + '_holdout_ci_excludes_zero'])} | {yn(rep['verdict'][k])} |")
    v = rep['verdict']
    dm = rep['diff_ci'].get('baseline_minus_momentum_holdout')
    dmt = f" Daily-return difference (strategy minus replica): {dm[0]:+.4f}..{dm[1]:+.4f} %/day (month-clustered 95% CI)." if dm else ''
    L += ['', f"**Does the live strategy beat the momentum-30 replica in the hold-out (by Calmar)?** {'Yes' if v['baseline_beats_momentum_holdout'] else 'No'}.{dmt}", '',
          '## Calendar-year returns (%)', '']
    years = sorted({y for s in rep['calendar_years'].values() for y in s})
    L += ['| Series | ' + ' | '.join(years) + ' |', '|---|' + '---|' * len(years)]
    for name, s in rep['calendar_years'].items():
        L.append(f'| {name} | ' + ' | '.join(str(s.get(y, '')) for y in years) + ' |')
    L += ['', '_Three hypotheses were tested, so a single "improves both" is weak evidence. Neither H2 nor H3 changes the live scanner; '
          'a winner would be a candidate for the forward test. Momentum replica: equal weight, top 30, March/September rebalance, 25 bps per side. '
          f"First rebalance: {rep['momentum_first_rebalance']}._"]
    return '\n'.join(L)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=10)
    ap.add_argument('--cache', default='history_cache.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    frames, bench = bt.load_history(a.years, a.cache)
    rep = run(frames, bench)
    os.makedirs(a.out, exist_ok=True)
    with open(f'{a.out}/benchmarks.json', 'w') as f:
        json.dump(rep, f, indent=2, default=str)
    md = markdown(rep)
    with open(f'{a.out}/benchmarks.md', 'w') as f:
        f.write(md)
    print(md)


if __name__ == '__main__':
    main()
