# Forward validation (paper, simulated fills)

Signals recorded: 77 (64 evidence-eligible, 13 legacy excluded). Event log: verified (175 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 24, 'void': 9, 'rejected': 20, 'open': 3, 'closed': 3, 'pending': 5}.

Signals not taken, with reasons:

- entry session passed without a trigger: 24
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 12
- symbol already has an active signal: 20
- not yet triggered: 5

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 2 (avg -1.20R)
- Lost: exited at a loss (trend/time exit): 1 (avg -0.04R)
- Open, in profit (mark-to-market): 1 (avg +0.21R)
- Open, at a loss (mark-to-market): 2 (avg -0.45R)
- Never triggered (buy-stop not reached): 24
- Waiting for entry session: 5
- Not tradable (rejected, cancelled or void): 29

Closed eligible signals: 3 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: -0.522 over 1 entry months; month-clustered 95% CI [-0.522, -0.522]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 1. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.