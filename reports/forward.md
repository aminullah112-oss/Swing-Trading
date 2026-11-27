# Forward validation (paper, simulated fills)

Signals recorded: 407 (394 evidence-eligible, 13 legacy excluded). Event log: verified (664 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 57, 'void': 36, 'rejected': 250, 'open': 15, 'closed': 12, 'pending': 24}.

Signals not taken, with reasons:

- entry session passed without a trigger: 57
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 60
- symbol already has an active signal: 250
- not yet triggered: 24

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 7 (avg -1.33R)
- Lost: exited at a loss (trend/time exit): 5 (avg -0.49R)
- Open, in profit (mark-to-market): 15 (avg +2.11R)
- Open, at a loss (mark-to-market): 0
- Never triggered (buy-stop not reached): 57
- Waiting for entry session: 24
- Not tradable (rejected, cancelled or void): 286

Closed eligible signals: 12 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.738 over 2 entry months; month-clustered 95% CI [0.312, 1.271]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.