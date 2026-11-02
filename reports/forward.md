# Forward validation (paper, simulated fills)

Signals recorded: 129 (116 evidence-eligible, 13 legacy excluded). Event log: verified (264 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 30, 'void': 15, 'rejected': 49, 'open': 7, 'closed': 5, 'pending': 10}.

Signals not taken, with reasons:

- entry session passed without a trigger: 30
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 24
- symbol already has an active signal: 49
- not yet triggered: 10

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 3 (avg -1.20R)
- Lost: exited at a loss (trend/time exit): 2 (avg -0.58R)
- Open, in profit (mark-to-market): 5 (avg +1.30R)
- Open, at a loss (mark-to-market): 2 (avg -0.25R)
- Never triggered (buy-stop not reached): 30
- Waiting for entry session: 10
- Not tradable (rejected, cancelled or void): 64

Closed eligible signals: 5 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.103 over 1 entry months; month-clustered 95% CI [0.103, 0.103]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.