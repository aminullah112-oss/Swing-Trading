"""Once-only hold-out. Opening the hold-out for a hypothesis is an event in a hash-chained log; a second opening for the
same (hypothesis, pre-registration hash) is refused, so the hold-out cannot be re-looked-at while parameters are adjusted.
The log is append-only (check_events.py-style CI check applies) and failed results stay recorded."""
import os

import events as evlog

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiments', 'holdout_log.jsonl')


class HoldoutAlreadyOpened(Exception):
    pass


def opened(path=None):
    return {(e['data']['hypothesis'], e['data']['prereg_hash']): e for e in evlog.read(path or LOG) if e['type'] == 'holdout_opened'}


def open_once(hypothesis, prereg_hash, data_cutoff, path=None, ts=None):
    """Record the opening, or raise. Call this BEFORE computing any hold-out statistic."""
    path = path or LOG
    ok, _, problem = evlog.verify(path)
    if not ok:
        raise HoldoutAlreadyOpened(f'hold-out log failed verification ({problem}); refusing to open the hold-out')
    if (hypothesis, prereg_hash) in opened(path):
        raise HoldoutAlreadyOpened(f'hold-out for {hypothesis} under pre-registration {prereg_hash[:12]} was already opened; it cannot be reused')
    return evlog.append(path, 'holdout_opened', hypothesis, {'hypothesis': hypothesis, 'prereg_hash': prereg_hash, 'data_cutoff': data_cutoff}, ts)


def record_result(hypothesis, prereg_hash, passed, summary, path=None, ts=None):
    return evlog.append(path or LOG, 'holdout_result', hypothesis,
                        {'hypothesis': hypothesis, 'prereg_hash': prereg_hash, 'passed': bool(passed), 'summary': summary}, ts)
