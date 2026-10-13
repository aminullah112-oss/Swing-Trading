"""Performance metrics beyond CAGR/drawdown: Sortino, profit factor, expectancy, turnover, exposure, cash, costs.
Pure functions over a daily return series and the `taken` list from backtest.portfolio(..., detail=True)."""
import numpy as np
import pandas as pd

TD = 252


def perf(ret):
    r = pd.Series(ret).dropna()
    if len(r) < 20:
        return None
    eq = (1 + r).cumprod()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    cagr = float(eq.iloc[-1] ** (1 / years) - 1) * 100
    dd = float((eq / eq.cummax() - 1).min()) * 100
    sd = float(r.std())
    down = r[r < 0]
    dsd = float(np.sqrt((down ** 2).sum() / len(r))) if len(r) else 0.0       # downside deviation vs 0, over all days
    return {'cagr_pct': round(cagr, 2), 'max_drawdown_pct': round(dd, 2),
            'calmar': round(cagr / abs(dd), 3) if dd < 0 else None,
            'sharpe': round(float(r.mean() / sd * np.sqrt(TD)), 3) if sd > 0 else None,
            'sortino': round(float(r.mean() / dsd * np.sqrt(TD)), 3) if dsd > 0 else None,
            'vol_pct': round(sd * np.sqrt(TD) * 100, 2), 'days': int(len(r)), 'years': round(years, 2)}


def trade_stats(r):
    """Per-trade statistics in R: expectancy, profit factor, win rate, payoff."""
    r = pd.Series(r, dtype=float).dropna()
    if r.empty:
        return {'trades': 0}
    w, l = r[r > 0], r[r <= 0]
    return {'trades': int(len(r)), 'win_rate': round(float((r > 0).mean()), 3), 'expectancy_r': round(float(r.mean()), 3),
            'profit_factor': round(float(w.sum() / -l.sum()), 3) if l.sum() < 0 else None,
            'avg_win_r': round(float(w.mean()), 3) if len(w) else None, 'avg_loss_r': round(float(l.mean()), 3) if len(l) else None}


def taken_stats(taken, equity):
    """Costs, turnover and gross-vs-net from the accepted trades of a portfolio run."""
    if not taken or equity is None or len(equity) == 0:
        return {'accepted': 0}
    t = pd.DataFrame(taken)
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    notional = float((t['shares'] * t['entry']).sum())
    gross, net = float(t['gross'].sum()), float(t['pnl'].sum())
    return {'accepted': int(len(t)), 'gross_pnl': round(gross, 0), 'net_pnl': round(net, 0),
            'costs_inr': round(float(t['cost'].sum()), 0), 'slippage_inr': round(float(t['slippage'].sum()), 0),
            'cost_drag_pct_of_gross': round((gross - net) / abs(gross) * 100, 1) if gross else None,
            'turnover_x_per_year': round(notional * 2 / float(equity.mean()) / years, 2)}      # buys + sells over mean equity


def full(ret, r_trades=None, taken=None, equity=None, port_stats=None):
    out = {'portfolio': perf(ret)}
    if r_trades is not None:
        out['trades'] = trade_stats(r_trades)
    if taken is not None:
        out['costs'] = taken_stats(taken, equity)
    if port_stats:
        out['exposure'] = {k: port_stats.get(k) for k in ('avg_exposure_pct', 'max_exposure_pct', 'time_in_cash_pct', 'avg_positions',
                                                          'liquidity_limited_orders', 'rejected_by_limits')}
    return out


def exposure_matched(bench_ret, avg_exposure_pct, cash_yield_annual=0.0):
    """Benchmark held at the strategy's average invested fraction, the rest in cash at cash_yield_annual (default 0%, stated)."""
    f = avg_exposure_pct / 100.0
    r = pd.Series(bench_ret).dropna()
    return f * r + (1 - f) * ((1 + cash_yield_annual) ** (1 / TD) - 1)


def vol_matched(bench_ret, target_vol_pct):
    """Benchmark scaled (levered or de-levered, cash at 0%) to the strategy's annualised volatility."""
    r = pd.Series(bench_ret).dropna()
    sd = float(r.std() * np.sqrt(TD) * 100)
    return r * (target_vol_pct / sd) if sd > 0 else r


def yearly_returns(ret):
    r = pd.Series(ret).dropna()
    return {int(y): float((1 + g).prod() - 1) for y, g in r.groupby(r.index.year)}
