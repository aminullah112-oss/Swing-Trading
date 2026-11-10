# Forward validation (paper, simulated fills)

Signals recorded: 168 (155 evidence-eligible, 13 legacy excluded). Event log: verified (334 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 39, 'void': 15, 'rejected': 77, 'open': 14, 'closed': 7, 'pending': 3}.

Signals not taken, with reasons:

- entry session passed without a trigger: 39
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 33
- symbol already has an active signal: 77
- not yet triggered: 3

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 5 (avg -1.30R)
- Lost: exited at a loss (trend/time exit): 2 (avg -0.58R)
- Open, in profit (mark-to-market): 12 (avg +2.03R)
- Open, at a loss (mark-to-market): 2 (avg -0.40R)
- Never triggered (buy-stop not reached): 39
- Waiting for entry session: 3
- Not tradable (rejected, cancelled or void): 92

Closed eligible signals: 7 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.756 over 2 entry months; month-clustered 95% CI [0.394, 1.028]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.