# Forward validation (paper, simulated fills)

Signals recorded: 373 (360 evidence-eligible, 13 legacy excluded). Event log: verified (619 events). Every fill here is simulated; none is a broker fill.

By status: {'expired': 55, 'void': 32, 'rejected': 225, 'open': 17, 'closed': 12, 'pending': 19}.

Signals not taken, with reasons:

- entry session passed without a trigger: 55
- entry was simulated on an unfinished session bar; the official bar decides: 3
- aggregate open-risk budget 1.5% of capital would be exceeded: 58
- symbol already has an active signal: 225
- not yet triggered: 19

How the filtered stocks fared:

- Won: closed in profit: 0
- Lost: stop hit: 7 (avg -1.33R)
- Lost: exited at a loss (trend/time exit): 5 (avg -0.49R)
- Open, in profit (mark-to-market): 16 (avg +1.98R)
- Open, at a loss (mark-to-market): 1 (avg -0.04R)
- Never triggered (buy-stop not reached): 55
- Waiting for entry session: 19
- Not tradable (rejected, cancelled or void): 257

Closed eligible signals: 12 of 100 needed; first eligible signal 2026-10-14; 182 days required.

Average R including open trades: +0.687 over 2 entry months; month-clustered 95% CI [0.275, 1.271]. Rolling expectancy (last closed): needs 30+ closed.

Taken-signal equity drawdown 0.0% of capital (now +0.0%). Gap-through-stop exits: 2. Partial fills: 0.

Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.