# Forward validation (paper, simulated fills)

Signals recorded: 88 (75 evidence-eligible, 13 legacy excluded). Event log: verified (196 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 25, 'void': 9, 'rejected': 27, 'open': 5, 'closed': 5, 'pending': 4}.

Signals not taken, with reasons:

- entry session passed without a trigger: 25
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 16
- symbol already has an active signal: 27
- not yet triggered: 4

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 3 (avg -1.20R)
- Lost: exited at a loss (trend/time exit): 2 (avg -0.58R)
- Open, in profit (mark-to-market): 3 (avg +0.85R)
- Open, at a loss (mark-to-market): 2 (avg -0.18R)
- Never triggered (buy-stop not reached): 25
- Waiting for entry session: 4
- Not tradable (rejected, cancelled or void): 36

Closed eligible signals: 5 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: -0.258 over 1 entry months; month-clustered 95% CI [-0.258, -0.258]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.