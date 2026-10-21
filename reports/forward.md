# Forward validation (paper, simulated fills)

Signals recorded: 67 (54 evidence-eligible, 13 legacy excluded). Event log: verified (161 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 21, 'void': 9, 'rejected': 14, 'open': 4, 'closed': 2, 'pending': 4}.

Signals not taken, with reasons:

- entry session passed without a trigger: 21
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 12
- symbol already has an active signal: 14
- not yet triggered: 4

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 1 (avg -1.17R)
- Lost: exited at a loss (trend/time exit): 1 (avg -0.04R)
- Open, in profit (mark-to-market): 1 (avg +0.21R)
- Open, at a loss (mark-to-market): 3 (avg -0.42R)
- Never triggered (buy-stop not reached): 21
- Waiting for entry session: 4
- Not tradable (rejected, cancelled or void): 23

Closed eligible signals: 2 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: -0.377 over 1 entry months; month-clustered 95% CI [-0.377, -0.377]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 0. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.