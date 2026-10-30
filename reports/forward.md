# Forward validation (paper, simulated fills)

Signals recorded: 108 (95 evidence-eligible, 13 legacy excluded). Event log: verified (232 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 28, 'void': 12, 'rejected': 35, 'open': 7, 'closed': 5, 'pending': 8}.

Signals not taken, with reasons:

- entry session passed without a trigger: 28
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 21
- symbol already has an active signal: 35
- not yet triggered: 8

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 3 (avg -1.20R)
- Lost: exited at a loss (trend/time exit): 2 (avg -0.58R)
- Open, in profit (mark-to-market): 4 (avg +0.92R)
- Open, at a loss (mark-to-market): 3 (avg -0.24R)
- Never triggered (buy-stop not reached): 28
- Waiting for entry session: 8
- Not tradable (rejected, cancelled or void): 47

Closed eligible signals: 5 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: -0.151 over 1 entry months; month-clustered 95% CI [-0.151, -0.151]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.