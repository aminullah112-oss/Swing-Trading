#!/usr/bin/env python3
"""CI guard for events.jsonl: the chain must verify and, when a base ref is given, the base version must be an exact
byte-prefix of the working copy (append-only). Usage: python check_events.py [base_ref]"""
import subprocess, sys
import events as ev

PATH = 'events.jsonl'


def main(base=None):
    ok, n, problem = ev.verify(PATH)
    if not ok:
        print(f'FAIL: {PATH} chain broken after {n} events: {problem}')
        return 1
    if base:
        r = subprocess.run(['git', 'show', f'{base}:{PATH}'], capture_output=True)
        if r.returncode == 0 and not ev.extends(r.stdout, open(PATH, 'rb').read()):
            print(f'FAIL: {PATH} is not an append-only extension of {base}')
            return 1
    print(f'OK: {n} events, chain verified' + (f', append-only vs {base}' if base else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
