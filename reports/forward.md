# Forward validation (paper, simulated fills)

Signals recorded: 243 (230 evidence-eligible, 13 legacy excluded). Event log: verified (429 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 45, 'void': 18, 'rejected': 135, 'open': 18, 'closed': 8, 'pending': 6}.

Signals not taken, with reasons:

- entry session passed without a trigger: 45
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 41
- symbol already has an active signal: 135
- not yet triggered: 6

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 5 (avg -1.30R)
- Lost: exited at a loss (trend/time exit): 3 (avg -0.53R)
- Open, in profit (mark-to-market): 12 (avg +1.83R)
- Open, at a loss (mark-to-market): 6 (avg -0.48R)
- Never triggered (buy-stop not reached): 45
- Waiting for entry session: 6
- Not tradable (rejected, cancelled or void): 153

Closed eligible signals: 8 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.425 over 2 entry months; month-clustered 95% CI [0.153, 0.742]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.