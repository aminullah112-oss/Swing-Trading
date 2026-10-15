# Forward validation (paper, simulated fills)

Signals recorded: 38 (25 evidence-eligible, 13 legacy excluded). Event log: verified (83 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 8, 'open': 3, 'void': 1, 'rejected': 4, 'pending': 9}.

Signals not taken, with reasons:

- entry session passed without a trigger: 8
- aggregate open-risk budget 1.5% of capital would be exceeded: 1
- symbol already has an active signal: 4
- not yet triggered: 9

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 0
- Lost: exited at a loss (trend/time exit): 0
- Open, in profit (mark-to-market): 1 (avg +0.05R)
- Open, at a loss (mark-to-market): 2 (avg -0.38R)
- Never triggered (buy-stop not reached): 8
- Waiting for entry session: 9
- Not tradable (rejected, cancelled or void): 5

Closed eligible signals: 0 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: -0.238 over 1 entry months; month-clustered 95% CI [-0.238, -0.238]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.28% of capital (now -0.28%). Gap-through-stop exits: 0. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.