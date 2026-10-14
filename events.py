"""Append-only, hash-chained event log (events.jsonl).

Each line commits to the previous line's hash, so deleting, editing or reordering any earlier event breaks
verification from that point on. This is tamper-EVIDENT, not tamper-proof: someone with write access to the
repository could rewrite the whole file consistently. The CI check (verify against the previous commit's
file, which must be a byte-prefix of the new one) closes that gap for anything pushed through the pipeline.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

GENESIS = '0' * 64


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str)


def _digest(body):
    return hashlib.sha256(_canon(body).encode()).hexdigest()


def read(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def append(path, etype, ref, data=None, ts=None):
    """Append one event and return it. ref = id of the thing the event is about (signal id, scan id, ...)."""
    prev = read(path)
    body = {'seq': len(prev) + 1, 'ts': ts or datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'type': etype, 'ref': ref, 'data': data or {}, 'prev': prev[-1]['hash'] if prev else GENESIS}
    ev = dict(body, hash=_digest(body))
    with open(path, 'a') as f:
        f.write(_canon(ev) + '\n')
    return ev


def verify(path):
    """(ok, n_events, problem). Checks sequence numbers, back-links and every hash."""
    prev, n = GENESIS, 0
    try:
        evs = read(path)
    except ValueError as e:
        return False, 0, f'unparseable line: {e}'
    for i, ev in enumerate(evs, 1):
        body = {k: v for k, v in ev.items() if k != 'hash'}
        if ev.get('seq') != i:
            return False, n, f'event {i}: sequence number {ev.get("seq")}'
        if ev.get('prev') != prev:
            return False, n, f'event {i}: broken chain link'
        if _digest(body) != ev.get('hash'):
            return False, n, f'event {i}: content does not match its hash'
        prev, n = ev['hash'], i
    return True, n, None


def extends(old_bytes, new_bytes):
    """Append-only check for CI: the previous file content must be an exact prefix of the new one."""
    return new_bytes.startswith(old_bytes)
