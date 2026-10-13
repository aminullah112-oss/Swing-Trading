"""Single source of truth for risk limits, capital, execution/cost assumptions and the live-trading switch.

Everything that other modules need to agree on lives here. Environment variables override the risk inputs
(they are deployment settings); the live-execution switch is deliberately NOT overridable from the
environment: enabling live trading needs a code change and a separate explicit approval.
"""
import os


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


# ---------------------------------------------------------------- risk (do not raise to improve backtests)
CAPITAL = _env_float('EDGE_CAPITAL', 565000)                 # tradable INR equity (must be confirmed by the operator)
RISK_PCT = _env_float('EDGE_RISK_PCT', 0.5) / 100            # max risk per trade, fraction of equity
MAX_POS_PCT = _env_float('EDGE_MAX_POS_PCT', 25) / 100       # max position value, fraction of equity
MAX_OPEN_RISK = _env_float('EDGE_MAX_OPEN_RISK_PCT', 1.5) / 100   # max aggregate open risk, fraction of equity
STRESS_RISK_MULT = 2.0        # stressed (gap) risk may not exceed this multiple of the per-trade risk limit
GAP_STRESS_ATR = 1.0          # stressed loss = distance to stop + this many ATRs of extra gap beyond the stop

# ---------------------------------------------------------------- data quality
MIN_DATA_RATIO = 0.8          # scan fails outright below this share of symbols with any usable data
OFFICIAL_COVERAGE_MIN = 0.95  # share of symbols that must have an OFFICIAL bar for the expected session to trade
CUTOFF_CONSISTENCY_MIN = 0.95 # share of symbols that must share the expected data cutoff
MAX_CRITICAL_ISSUE_SHARE = 0.02
JUMP_WARN = 0.30              # one-day move that suggests an unadjusted corporate action
JUMP_ERROR = 0.50

# ---------------------------------------------------------------- execution model (paper) and costs
# Legacy flat model: what control C0 was originally measured with. Kept so C0 stays reproducible.
LEGACY_COST_BPS_PER_SIDE = 15.0
LEGACY_SLIPPAGE_BPS_PER_SIDE = 10.0
# Indian equity delivery, itemised (rates are ASSUMPTIONS as of 2026-10; verify against your broker's contract note):
#   buy : STT 0.10% + exchange txn ~0.00297% + SEBI 0.0001% + stamp duty 0.015% + GST 18% on (txn + SEBI + brokerage)
#   sell: STT 0.10% + exchange txn ~0.00297% + SEBI 0.0001% + depository charge ~Rs 15.34 per scrip per day
# Brokerage is assumed zero (discount delivery). The depository charge is expressed in bps of a typical Rs 60,000 order.
COST_BUY_BPS = 11.9
COST_SELL_BPS = 12.9
SLIPPAGE_BPS_PER_SIDE = 10.0
LIQUIDITY_PARTICIPATION_CAP = 0.05    # at most 5% of the entry day's volume can be filled
ADV_ORDER_CAP = 0.02                  # order value at most 2% of 20-day average daily traded value

# ---------------------------------------------------------------- live trading: hard-disabled
LIVE_EXECUTION_ENABLED = False        # requires a code change plus the operator's separate written approval
