"""Versioned, immutable stock universes.

A universe version never changes once frozen; a change means a NEW version. Every report records the
version and hash it was produced with, and results from different versions must not be compared as if
they were the same experiment.
"""
import hashlib
import json
import os

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'universe')
CURRENT = 'U159_v2'


def _path(version):
    return os.path.join(DIR, f'{version}.json')


def load(version=CURRENT):
    with open(_path(version)) as f:
        d = json.load(f)
    d['symbols'] = list(dict.fromkeys(d['symbols']))
    return d


def file_hash(version):
    with open(_path(version), 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def content_hash(symbols, aliases=None):
    blob = json.dumps({'symbols': sorted(symbols), 'aliases': {k: aliases[k] for k in sorted(aliases or {})}}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def manifest():
    with open(os.path.join(DIR, 'MANIFEST.json')) as f:
        return json.load(f)['hashes']


def verify_manifest():
    """Problems (empty list = every frozen version still matches its recorded hash)."""
    problems = []
    for v, h in manifest().items():
        if not os.path.exists(_path(v)):
            problems.append(f'{v}: file missing')
        elif file_hash(v) != h:
            problems.append(f'{v}: file changed after being frozen (create a new version instead)')
    if CURRENT not in manifest():
        problems.append(f'CURRENT version {CURRENT} is not in the manifest')
    return problems


def diff(a, b):
    sa, sb = set(load(a)['symbols']), set(load(b)['symbols'])
    return {'removed': sorted(sa - sb), 'added': sorted(sb - sa)}
