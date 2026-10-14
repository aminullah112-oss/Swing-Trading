"""Provenance for every generated report: which code, configuration, universe and data produced it.

Two hashes:
  evidence_hash  everything a backtest result depends on (strategy spec, risk fractions, cost/execution model,
                 universe version and content). Backtest-derived evidence is only valid for the same evidence_hash.
  config_hash    evidence_hash plus deployment inputs (capital).
A report whose evidence_hash differs from the current one is STALE and earns no readiness credit.
"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

import settings
import strategy
import universe

BACKTEST_MAX_AGE_DAYS = 45
SCAN_MAX_AGE_DAYS = 4


def _h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def commit_sha():
    sha = os.environ.get('GITHUB_SHA')
    if sha:
        return sha
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10,
                              cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip() or 'unknown'
    except Exception:
        return 'unknown'


def strategy_identity():
    d = strategy.describe()
    return {k: d[k] for k in ('min_score', 'trigger', 'exit_mode', 'max_hold')} | {'stop_atr_mult': strategy.STOP_ATR_MULT}


def universe_info(version=None):
    u = universe.load(version or universe.CURRENT)
    return {'version': u['version'], 'count': len(u['symbols']), 'hash': universe.content_hash(u['symbols'], u.get('aliases'))}


def evidence_config(version=None):
    return {
        'strategy': strategy_identity(),
        'risk': {'risk_pct': settings.RISK_PCT, 'max_pos_pct': settings.MAX_POS_PCT, 'max_open_risk': settings.MAX_OPEN_RISK},
        'costs': {'legacy_cost_bps': settings.LEGACY_COST_BPS_PER_SIDE, 'legacy_slip_bps': settings.LEGACY_SLIPPAGE_BPS_PER_SIDE,
                  'buy_bps': settings.COST_BUY_BPS, 'sell_bps': settings.COST_SELL_BPS, 'slip_bps': settings.SLIPPAGE_BPS_PER_SIDE,
                  'participation_cap': settings.LIQUIDITY_PARTICIPATION_CAP, 'adv_cap': settings.ADV_ORDER_CAP},
        'universe': universe_info(version),
    }


def evidence_hash(version=None):
    return _h(evidence_config(version))


def config_hash(version=None):
    return _h({'evidence': evidence_config(version), 'capital': settings.CAPITAL})


def c0_hash():
    return _h(strategy_identity())


def file_id(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except OSError:
        return None


def make(kind, data_cutoff=None, sources=None, universe_version=None, extra=None):
    """Provenance block to embed in a report. `sources` maps a label to a file path whose content id is recorded."""
    u = universe_info(universe_version)
    p = {
        'kind': kind,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'commit_sha': commit_sha(),
        'config_hash': config_hash(universe_version),
        'evidence_hash': evidence_hash(universe_version),
        'c0_hash': c0_hash(),
        'universe_version': u['version'], 'universe_hash': u['hash'], 'universe_count': u['count'],
        'data_cutoff': data_cutoff,
        'source_ids': {k: file_id(v) for k, v in (sources or {}).items()},
    }
    if extra:
        p.update(extra)
    return p


def problems(prov, kind='backtest', now=None):
    """Why this report cannot be treated as current evidence (empty list = current and consistent)."""
    if not prov:
        return ['report has no provenance block (produced before provenance existed): rerun it']
    out = []
    now = now or datetime.now(timezone.utc)
    if prov.get('evidence_hash') != evidence_hash():
        out.append(f"evidence_hash {prov.get('evidence_hash')} != current {evidence_hash()} (strategy, risk, costs or universe changed since this report)")
    if prov.get('universe_hash') != universe_info()['hash']:
        out.append(f"universe {prov.get('universe_version')} ({prov.get('universe_hash')}) != current {universe_info()['version']}")
    try:
        gen = datetime.fromisoformat(prov['generated_at'])
        age = (now - gen).days
        limit = BACKTEST_MAX_AGE_DAYS if kind == 'backtest' else SCAN_MAX_AGE_DAYS
        if age > limit:
            out.append(f'report is {age} days old (limit {limit} for {kind} evidence)')
    except Exception:
        out.append('report has an unreadable generated_at')
    return out
