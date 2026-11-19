# Forward validation (paper, simulated fills)

Signals recorded: 277 (264 evidence-eligible, 13 legacy excluded). Event log: verified (480 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 49, 'void': 22, 'rejected': 159, 'open': 15, 'closed': 11, 'pending': 8}.

Signals not taken, with reasons:

- entry session passed without a trigger: 49
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 45
- symbol already has an active signal: 159
- not yet triggered: 8

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 6 (avg -1.36R)
- Lost: exited at a loss (trend/time exit): 5 (avg -0.49R)
- Open, in profit (mark-to-market): 11 (avg +2.23R)
- Open, at a loss (mark-to-market): 4 (avg -0.49R)
- Never triggered (buy-stop not reached): 49
- Waiting for entry session: 8
- Not tradable (rejected, cancelled or void): 181

Closed eligible signals: 11 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.462 over 2 entry months; month-clustered 95% CI [0.048, 0.944]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.