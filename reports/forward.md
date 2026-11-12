# Forward validation (paper, simulated fills)

Signals recorded: 192 (179 evidence-eligible, 13 legacy excluded). Event log: verified (363 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 41, 'void': 16, 'rejected': 93, 'open': 14, 'closed': 7, 'pending': 8}.

Signals not taken, with reasons:

- entry session passed without a trigger: 41
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 34
- symbol already has an active signal: 93
- not yet triggered: 8

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 5 (avg -1.30R)
- Lost: exited at a loss (trend/time exit): 2 (avg -0.58R)
- Open, in profit (mark-to-market): 11 (avg +2.34R)
- Open, at a loss (mark-to-market): 3 (avg -0.37R)
- Never triggered (buy-stop not reached): 41
- Waiting for entry session: 8
- Not tradable (rejected, cancelled or void): 109

Closed eligible signals: 7 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.807 over 2 entry months; month-clustered 95% CI [0.484, 1.049]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.