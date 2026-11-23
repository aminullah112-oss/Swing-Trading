# Forward validation (paper, simulated fills)

Signals recorded: 325 (312 evidence-eligible, 13 legacy excluded). Event log: verified (550 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 53, 'void': 25, 'rejected': 191, 'open': 22, 'closed': 12, 'pending': 9}.

Signals not taken, with reasons:

- entry session passed without a trigger: 53
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 56
- symbol already has an active signal: 191
- not yet triggered: 9

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 7 (avg -1.33R)
- Lost: exited at a loss (trend/time exit): 5 (avg -0.49R)
- Open, in profit (mark-to-market): 11 (avg +2.50R)
- Open, at a loss (mark-to-market): 11 (avg -0.38R)
- Never triggered (buy-stop not reached): 53
- Waiting for entry session: 9
- Not tradable (rejected, cancelled or void): 216

Closed eligible signals: 12 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.341 over 2 entry months; month-clustered 95% CI [-0.075, 1.103]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.