"""The only path from an approved order to an exchange, and it is closed.

submit() refuses unless ALL of these hold: settings.LIVE_EXECUTION_ENABLED is True (it is hard-coded False and changing
it needs a code change plus the operator's explicit written approval), the risk gate approves, and the client order id has
not been used. Today no broker adapter exists in this repository: there is no network or broker code here, and a test
asserts it. In paper mode the order is recorded as SIMULATED in the hash-chained event log and nothing is sent anywhere.
"""
import events as evlog
import riskgate
import settings


class LiveTradingDisabled(Exception):
    pass


def submit(order, state, mode='paper', events_path='events.jsonl', ts=None, kill_switch_path=None):
    """Returns {'status': 'simulated'|'blocked', 'decision': risk decision, 'reason': ...}. Never contacts a broker."""
    state = dict(state or {}, mode=mode)
    decision = riskgate.evaluate(order, state, kill_switch_path)
    ref = str((order or {}).get('client_order_id', 'unknown'))
    if mode == 'live':
        if settings.LIVE_EXECUTION_ENABLED is not True:
            evlog.append(events_path, 'order_blocked', ref, {'reason': 'live execution disabled', 'reasons': decision['reasons']}, ts)
            return {'status': 'blocked', 'decision': decision, 'reason': 'live execution is disabled (LIVE_EXECUTION_ENABLED is False)'}
        raise LiveTradingDisabled('No broker adapter is implemented; live submission is not available.')
    if not decision['approved']:
        evlog.append(events_path, 'order_blocked', ref, {'reasons': decision['reasons']}, ts)
        return {'status': 'blocked', 'decision': decision, 'reason': '; '.join(decision['reasons'])}
    evlog.append(events_path, 'order_simulated', ref, {'symbol': order['symbol'], 'side': order['side'], 'qty': order['qty'],
                                                       'entry_price': order['entry_price'], 'simulated': True}, ts)
    return {'status': 'simulated', 'decision': decision, 'reason': 'paper order recorded; nothing was sent to any broker'}
