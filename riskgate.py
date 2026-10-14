"""Pre-trade risk gate. Decides whether ONE order may be submitted, from the order and the account/market/broker state only.

Independence: this module imports nothing from the strategy, scanner, scoring or backtest code (tests enforce it by
scanning imports), so a bug or a change in signal generation cannot loosen a risk limit. Limits come from settings.py.

Fail closed: a missing field, an unknown state, a malformed number or any exception is a REJECTION. A uncertain input is
never read as 'probably fine'. Exits that reduce an existing position are never blocked by the entry checks, only
validated (cannot sell more than held).

This module only approves or rejects. It places no orders and contains no broker code.
"""
import json
import math
import os

import settings

REQUIRED_ORDER = ('symbol', 'side', 'qty', 'entry_price', 'stop_price', 'client_order_id')
REQUIRED_STATE = ('equity', 'cash', 'open_positions', 'submitted_ids', 'health_status', 'market', 'broker', 'quote', 'liquidity')


class Reject(Exception):
    pass


def _num(x, name, positive=True):
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise Reject(f'{name} is not a number: {x!r}')
    if not math.isfinite(v) or (positive and v <= 0):
        raise Reject(f'{name} must be a positive finite number: {x!r}')
    return v


def kill_switch_engaged(path=None):
    """Engaged unless the file exists, parses, and says engaged=false. Missing/unreadable = engaged (fail closed)."""
    try:
        with open(path or settings.KILL_SWITCH_FILE) as f:
            return bool(json.load(f).get('engaged', True))
    except (OSError, ValueError, AttributeError):
        return True


def position_risk(p):
    """Open risk of an existing position: shares * (entry - stop), floored at 0."""
    return max(0.0, float(p['qty']) * (float(p['entry_price']) - float(p['stop_price'])))


def _check_exit(order, state):
    held = sum(float(p['qty']) for p in state['open_positions'] if p['symbol'] == order['symbol'])
    q = _num(order['qty'], 'qty')
    if q > held:
        raise Reject(f"sell qty {q:g} exceeds the held position {held:g} (no shorting)")
    return {'kind': 'exit', 'held': held}


def evaluate(order, state, kill_switch_path=None):
    """Return {'approved': bool, 'kind': 'entry'|'exit', 'reasons': [rejections], 'warnings': [...], 'limits': {...}}.
    Never raises."""
    reasons, warnings, limits = [], [], {}
    kind = 'entry'
    try:
        if not isinstance(order, dict) or not isinstance(state, dict):
            raise Reject('order and state must be dicts')
        miss = [k for k in REQUIRED_ORDER if k not in order or order[k] in (None, '')]
        miss += [f'state.{k}' for k in REQUIRED_STATE if k not in state or state[k] is None]
        if miss:
            raise Reject(f'missing required fields: {miss}')
        side = str(order['side']).lower()
        if side not in ('buy', 'sell'):
            raise Reject(f'unknown side {order["side"]!r}')
        if side == 'sell':
            kind = 'exit'
            _check_exit(order, state)
            return {'approved': True, 'kind': kind, 'reasons': [], 'warnings': ['exit: entry checks not applied'], 'limits': {}}
        if kill_switch_engaged(kill_switch_path):
            reasons.append('kill switch engaged (or kill_switch.json missing/unreadable)')

        equity = _num(state['equity'], 'equity')
        cash = _num(state['cash'], 'cash', positive=False)
        qty = _num(order['qty'], 'qty')
        entry = _num(order['entry_price'], 'entry_price')
        stop = _num(order['stop_price'], 'stop_price')
        atr = _num(order.get('atr', 0) or 0, 'atr', positive=False)

        # 1. system state
        hs = state['health_status']
        if hs not in ('OK', 'WARN'):
            reasons.append(f'health status {hs!r} does not permit new entries')
        if settings.LIVE_EXECUTION_ENABLED is not True and state.get('mode') == 'live':
            reasons.append('live mode requested but LIVE_EXECUTION_ENABLED is False')
        if state.get('state_reconciled') is not True:
            reasons.append('positions/orders not reconciled with the broker since the last restart')
        # 2. duplicates / replay
        if order['client_order_id'] in set(state['submitted_ids']):
            reasons.append(f"duplicate order: client_order_id {order['client_order_id']!r} already submitted")
        if any(p['symbol'] == order['symbol'] for p in state['open_positions']):
            reasons.append(f"{order['symbol']} already has an open position")
        # 3. market state: holidays, halts, circuit limits, stale prices
        m = state['market']
        if m.get('session_open') is not True:
            reasons.append('market not open / not a trading session (holiday or outside hours)')
        if order['symbol'] in set(m.get('halted', [])):
            reasons.append(f"{order['symbol']} is halted")
        q = state['quote']
        age = q.get('age_seconds')
        if age is None or not math.isfinite(float(age)) or float(age) > settings.MAX_QUOTE_AGE_S:
            reasons.append(f'quote is stale or has no timestamp (age {age}, limit {settings.MAX_QUOTE_AGE_S}s)')
        ltp = q.get('ltp')
        try:
            ltp = _num(ltp, 'ltp')
            if abs(ltp / entry - 1) > 0.03:
                reasons.append(f'last price {ltp:g} differs from the order entry {entry:g} by more than 3%')
            ub, lb = q.get('upper_circuit'), q.get('lower_circuit')
            if ub is None or lb is None:
                reasons.append('circuit limits unknown')
            elif ltp >= float(ub) * 0.995 or ltp <= float(lb) * 1.005:
                reasons.append('price is at/near its circuit limit: fills are not assured')
        except Reject as e:
            reasons.append(str(e))
        # 4. broker / API health
        b = state['broker']
        if b.get('connected') is not True:
            reasons.append('broker not connected')
        hb = b.get('heartbeat_age_seconds')
        if hb is None or float(hb) > settings.BROKER_HEARTBEAT_MAX_S:
            reasons.append(f'broker heartbeat missing or older than {settings.BROKER_HEARTBEAT_MAX_S}s')
        if int(b.get('consecutive_rejects', 99)) >= settings.MAX_CONSECUTIVE_REJECTS:
            reasons.append(f"{b.get('consecutive_rejects')} consecutive broker rejections: entries halted until a human clears it")
        if int(b.get('consecutive_timeouts', 99)) >= settings.MAX_CONSECUTIVE_REJECTS:
            reasons.append('repeated broker timeouts: entries halted')
        # 5. stop and risk arithmetic
        if stop >= entry:
            reasons.append(f'stop {stop:g} is not below entry {entry:g}')
        dist = entry - stop
        risk = qty * dist
        risk_cap = equity * settings.RISK_PCT
        limits['per_trade_risk'] = {'value': round(risk, 2), 'cap': round(risk_cap, 2)}
        if dist > 0 and risk > risk_cap * (1 + 1e-9):
            reasons.append(f'trade risk {risk:.0f} exceeds {settings.RISK_PCT:.2%} of equity ({risk_cap:.0f})')
        stressed = qty * (dist + settings.GAP_STRESS_ATR * atr)
        stress_cap = risk_cap * settings.STRESS_RISK_MULT
        limits['gap_stress_loss'] = {'value': round(stressed, 2), 'cap': round(stress_cap, 2)}
        if atr <= 0:
            reasons.append('ATR missing: the stop-gap stress loss cannot be computed')
        elif stressed > stress_cap * (1 + 1e-9):
            reasons.append(f'gap-stressed loss {stressed:.0f} exceeds {settings.STRESS_RISK_MULT:g}x the per-trade limit ({stress_cap:.0f})')
        value = qty * entry
        limits['position_value'] = {'value': round(value, 2), 'cap': round(equity * settings.MAX_POS_PCT, 2)}
        if value > equity * settings.MAX_POS_PCT * (1 + 1e-9):
            reasons.append(f'position value {value:.0f} exceeds {settings.MAX_POS_PCT:.0%} of equity')
        open_risk = sum(position_risk(p) for p in state['open_positions'])
        limits['aggregate_open_risk'] = {'value': round(open_risk + risk, 2), 'cap': round(equity * settings.MAX_OPEN_RISK, 2)}
        if open_risk + risk > equity * settings.MAX_OPEN_RISK * (1 + 1e-9):
            reasons.append(f'aggregate open risk {open_risk + risk:.0f} would exceed {settings.MAX_OPEN_RISK:.2%} of equity')
        # 6. cash
        need = value * (1 + settings.CASH_BUFFER)
        limits['cash'] = {'need': round(need, 2), 'available': round(cash, 2)}
        if need > cash:
            reasons.append(f'cash {cash:.0f} cannot fund {need:.0f} (order plus {settings.CASH_BUFFER:.0%} buffer)')
        # 7. liquidity
        lq = state['liquidity'].get(order['symbol'])
        if not lq or not lq.get('adv_shares') or not lq.get('adv_value'):
            reasons.append('no liquidity data for the symbol')
        else:
            if qty > settings.LIQUIDITY_PARTICIPATION_CAP * float(lq['adv_shares']):
                reasons.append(f"qty {qty:g} exceeds {settings.LIQUIDITY_PARTICIPATION_CAP:.0%} of average daily volume ({float(lq['adv_shares']):.0f})")
            if value > settings.ADV_ORDER_CAP * float(lq['adv_value']):
                reasons.append(f'order value {value:.0f} exceeds {settings.ADV_ORDER_CAP:.0%} of average daily traded value')
        # 8. concentration
        cl = order.get('cluster')
        if cl:
            same = sum(1 for p in state['open_positions'] if p.get('cluster') == cl)
            if same >= settings.MAX_PER_CLUSTER:
                reasons.append(f'{same} open positions already in cluster {cl!r} (limit {settings.MAX_PER_CLUSTER})')
        else:
            warnings.append('cluster/sector unknown: concentration is limited only by the aggregate risk cap')
    except Reject as e:
        reasons.append(str(e))
    except Exception as e:                      # any unexpected failure rejects
        reasons.append(f'risk gate error, rejected (fail closed): {type(e).__name__}: {e}')
    return {'approved': not reasons, 'kind': kind, 'reasons': reasons, 'warnings': warnings, 'limits': limits}
