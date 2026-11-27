# Forward validation (paper, simulated fills)

Signals recorded: 407 (394 evidence-eligible, 13 legacy excluded). Event log: verified (660 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 57, 'void': 34, 'rejected': 252, 'open': 17, 'closed': 12, 'pending': 22}.

Signals not taken, with reasons:

- entry session passed without a trigger: 57
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 60
- symbol already has an active signal: 252
- not yet triggered: 22

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 7 (avg -1.33R)
- Lost: exited at a loss (trend/time exit): 5 (avg -0.49R)
- Open, in profit (mark-to-market): 14 (avg +2.19R)
- Open, at a loss (mark-to-market): 3 (avg -0.38R)
- Never triggered (buy-stop not reached): 57
- Waiting for entry session: 22
- Not tradable (rejected, cancelled or void): 286

Closed eligible signals: 12 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.612 over 2 entry months; month-clustered 95% CI [0.162, 1.25]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.