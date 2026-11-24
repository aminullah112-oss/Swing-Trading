# Forward validation (paper, simulated fills)

Signals recorded: 325 (312 evidence-eligible, 13 legacy excluded). Event log: verified (566 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 53, 'void': 32, 'rejected': 184, 'open': 15, 'closed': 12, 'pending': 16}.

Signals not taken, with reasons:

- entry session passed without a trigger: 53
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 56
- symbol already has an active signal: 184
- not yet triggered: 16

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 7 (avg -1.33R)
- Lost: exited at a loss (trend/time exit): 5 (avg -0.49R)
- Open, in profit (mark-to-market): 10 (avg +2.73R)
- Open, at a loss (mark-to-market): 5 (avg -0.28R)
- Never triggered (buy-stop not reached): 53
- Waiting for entry session: 16
- Not tradable (rejected, cancelled or void): 216

Closed eligible signals: 12 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.527 over 2 entry months; month-clustered 95% CI [0.065, 1.103]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.