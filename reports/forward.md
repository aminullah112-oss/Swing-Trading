# Forward validation (paper, simulated fills)

Signals recorded: 26 (13 evidence-eligible, 13 legacy excluded). Event log: verified (48 events). Every fill here is simulated; none is a broker fill.

By status: {'rejected': 11, 'open': 1, 'expired': 1}.

Signals not taken, with reasons:

- symbol already has an active signal: 11
- aggregate open-risk budget 1.5% of capital would be exceeded: 1
- entry session passed without a trigger: 1

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 0
- Lost: exited at a loss (trend/time exit): 0
- Open, in profit (mark-to-market): 0
- Open, at a loss (mark-to-market): 1 (avg -0.12R)
- Never triggered (buy-stop not reached): 1
- Waiting for entry session: 0
- Not tradable (rejected, cancelled or void): 11

Closed eligible signals: 0 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: -0.117 over 1 entry months; month-clustered 95% CI None. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.17%). Gap-through-stop exits: 0. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.