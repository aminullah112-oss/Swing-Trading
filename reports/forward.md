# Forward validation (paper, simulated fills)

Signals recorded: 262 (249 evidence-eligible, 13 legacy excluded). Event log: verified (452 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 47, 'void': 18, 'rejected': 150, 'open': 18, 'closed': 9, 'pending': 7}.

Signals not taken, with reasons:

- entry session passed without a trigger: 47
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 42
- symbol already has an active signal: 150
- not yet triggered: 7

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 6 (avg -1.36R)
- Lost: exited at a loss (trend/time exit): 3 (avg -0.53R)
- Open, in profit (mark-to-market): 11 (avg +2.23R)
- Open, at a loss (mark-to-market): 7 (avg -0.42R)
- Never triggered (buy-stop not reached): 47
- Waiting for entry session: 7
- Not tradable (rejected, cancelled or void): 168

Closed eligible signals: 9 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.439 over 2 entry months; month-clustered 95% CI [0.034, 0.944]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.