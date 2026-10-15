# Forward validation (paper, simulated fills)

Signals recorded: 26 (13 evidence-eligible, 13 legacy excluded). Event log: verified (60 events). Every fill here is simulated; none is a broker fill.

By status: {'pending': 11, 'void': 1, 'rejected': 1}.

Signals not taken, with reasons:

- not yet triggered: 11
- entry was simulated on an unfinished session bar; the official bar decides: 1
- symbol already has an active signal: 1

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 0
- Lost: exited at a loss (trend/time exit): 0
- Open, in profit (mark-to-market): 0
- Open, at a loss (mark-to-market): 0
- Never triggered (buy-stop not reached): 0
- Waiting for entry session: 11
- Not tradable (rejected, cancelled or void): 2

Closed eligible signals: 0 of 100 needed; first eligible signal 2026-10-14; 182 days required.

No entered, eligible signals yet: no expectancy can be stated.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 0. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.