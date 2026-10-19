# Forward validation (paper, simulated fills)

Signals recorded: 59 (46 evidence-eligible, 13 legacy excluded). Event log: verified (131 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 15, 'void': 9, 'rejected': 10, 'pending': 12}.

Signals not taken, with reasons:

- entry session passed without a trigger: 15
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 6
- symbol already has an active signal: 10
- not yet triggered: 12

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 0
- Lost: exited at a loss (trend/time exit): 0
- Open, in profit (mark-to-market): 0
- Open, at a loss (mark-to-market): 0
- Never triggered (buy-stop not reached): 15
- Waiting for entry session: 12
- Not tradable (rejected, cancelled or void): 19

Closed eligible signals: 0 of 100 needed; first eligible signal 2026-10-14; 182 days required.

No entered, eligible signals yet: no expectancy can be stated.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 0. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.