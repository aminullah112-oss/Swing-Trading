# EDGE PROTOCOL — NSE Swing Trading Screener

Automated technical analysis screener for NSE stocks using GitHub Actions + Python + GitHub Pages.

**Live Dashboard:** https://aminullah112-oss.github.io/Swing-Trading

---

## ✨ Features

- **Automated Daily Scans** — Runs every weekday at 9 AM IST via GitHub Actions
- **Technical Filters** — EMA trend, RSI momentum, Supertrend, volume surge detection
- **Zero Cost** — Runs on GitHub's free tier (no servers, no payments)
- **Live Website** — Real-time results hosted on GitHub Pages
- **Version Control** — Scan history preserved in git commits

---

## 🎯 EDGE PROTOCOL Filters

Each stock must pass ALL filters:

| Filter | Condition |
|--------|-----------|
| **EMA Trend** | EMA(20) > EMA(50) > EMA(200) |
| **RSI Momentum** | 50 < RSI(14) < 75 |
| **Trend Follow** | Price > Supertrend(10,3) |
| **Volume Surge** | Volume > 1.5x MA(20) |
| **Price Floor** | Price > ₹0.85 |

---

## 🏗️ Project Structure

```
Swing-Trading/
├── screener.py                    # Main screening logic
├── requirements.txt               # Python dependencies
├── index.html                     # Website homepage
├── style.css                      # Website styling
├── script.js                      # Frontend JS for results
├── results.json                   # Latest scan results (auto-generated)
├── .github/workflows/
│   └── screen.yml                 # GitHub Actions workflow
└── README.md                      # This file
```

---

## 🚀 Quick Start

### 1. Clone Your Repository

```bash
git clone https://github.com/aminullah112-oss/Swing-Trading.git
cd Swing-Trading
```

### 2. Test Locally (Optional)

```bash
pip install -r requirements.txt
python screener.py
```

This will create `results.json` with the latest scan.

### 3. Enable GitHub Pages

1. Go to repo **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / folder: **/ (root)**
4. Save

Your site will be live at: `https://aminullah112-oss.github.io/Swing-Trading`

### 4. Enable GitHub Actions

1. Go to **Actions** tab
2. Click **"I understand my workflows, go ahead and enable them"**
3. The workflow will run automatically every weekday at 9 AM IST

---

## ⚙️ Configuration

### Modify Stock List

Edit `screener.py`, line ~15:

```python
NSE_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    # Add more stocks...
]
```

Use `.NS` suffix for NSE tickers (e.g., `INFY.NS`, `SBIN.NS`).

### Change Scan Time

Edit `.github/workflows/screen.yml`, line ~8:

```yaml
- cron: '30 3 * * 1-5'  # Current: 9 AM IST (3:30 UTC), Mon-Fri
```

Use [crontab.guru](https://crontab.guru) to convert times.

### Adjust Filters

Edit `screener.py`, function `apply_filters()` (around line ~80):

```python
ema_ok = (ind['ema_20'] > ind['ema_50']) and (ind['ema_50'] > ind['ema_200'])
rsi_ok = (50 < ind['rsi'] < 75)  # Change 50-75 to your range
# ... etc
```

---

## 📊 Understanding the Results

**results.json** contains:

```json
{
  "timestamp": "2025-05-09T09:05:23.123456",
  "scan_date": "2025-05-09",
  "scan_time": "09:05:23",
  "count": 5,
  "filters": { ... },
  "stocks": [
    {
      "symbol": "RELIANCE",
      "price": 2850.50,
      "ema_20": 2820.45,
      "ema_50": 2790.10,
      "ema_200": 2750.80,
      "rsi": 62.30,
      "supertrend": 2840.00,
      "volume": 5000000,
      "avg_volume": 3200000
    },
    ...
  ]
}
```

---

## 🔄 Workflow Automation

The GitHub Actions workflow (`screen.yml`):

1. **Triggers:** Weekdays at 9 AM IST (or manual via Actions tab)
2. **Runs:** Python screener against 50+ NSE stocks
3. **Calculates:** EMA, RSI, Supertrend, volume indicators
4. **Filters:** Applies EDGE PROTOCOL rules
5. **Saves:** Results to `results.json`
6. **Commits:** Auto-commits if results changed
7. **Website:** Updates instantly on GitHub Pages

---

## 📱 Website Features

- **Live Table** — Real-time stock results sorted by symbol
- **Auto-Refresh** — Updates every 5 minutes
- **Filter Info** — Shows active filter rules
- **Responsive Design** — Works on mobile, tablet, desktop
- **Zero JavaScript Build** — Plain HTML/CSS/JS, no frameworks

---

## 🛠️ Local Testing

Run the screener locally anytime:

```bash
python screener.py
```

Output:
```
============================================================
EDGE PROTOCOL - NSE Stock Screener
Scan started: 2025-05-09 09:00:00
============================================================

[1/50] Screening RELIANCE.NS... ✅ MATCH
[2/50] Screening TCS.NS... ❌ Filtered out
[3/50] Screening HDFCBANK.NS... ✅ MATCH
...
============================================================
📊 EDGE PROTOCOL Scan Complete
Found 5 stocks matching criteria
============================================================
```

---

## 🔗 Accessing Results

- **Website:** `https://aminullah112-oss.github.io/Swing-Trading`
- **Raw JSON:** `https://raw.githubusercontent.com/aminullah112-oss/Swing-Trading/main/results.json`
- **GitHub Repo:** `https://github.com/aminullah112-oss/Swing-Trading`

---

## 📈 Indicators Explained

| Indicator | Purpose | Calculation |
|-----------|---------|-------------|
| **EMA(20/50/200)** | Trend direction | Exponential moving average |
| **RSI(14)** | Momentum / overbought-oversold | Relative Strength Index |
| **Supertrend(10,3)** | Dynamic support/resistance | ATR-based oscillator |
| **Volume MA(20)** | Liquidity confirmation | 20-period moving average |

---

## ⚠️ Disclaimers

- **Not Financial Advice** — This screener is for educational research only
- **No Guarantees** — Past performance ≠ future results
- **Risk Management** — Always use stop-losses and position sizing
- **Data Quality** — Relies on Yahoo Finance data accuracy

---

## 🐛 Troubleshooting

### Website shows "Loading..." or blank table?

1. Check if `results.json` exists in repo
2. Open browser DevTools → Console for errors
3. Manually run: GitHub Actions → screen workflow → "Run workflow"

### No stocks found in results?

- Market may not have matching candidates that day
- Check filters aren't too strict
- Verify yfinance data is available

### GitHub Actions failing?

1. Go to **Actions** tab → **Daily Stock Screen** → failed run
2. Click job to see detailed logs
3. Common issues:
   - Network timeout (yfinance slow)
   - Invalid ticker symbols
   - Python package installation errors

### How to manually trigger a scan?

1. Go to repo **Actions** tab
2. Click **Daily Stock Screen** workflow
3. Click **Run workflow** → **Run workflow**

---

## 📝 License

MIT License — feel free to fork, modify, and distribute.

---

## 📧 Support

For issues or questions:
1. Check GitHub Issues
2. Review GitHub Actions logs
3. Open a new Issue with details

---

## 🎓 Learning Resources

- **yfinance Docs:** https://github.com/ranaroussi/yfinance
- **GitHub Actions:** https://docs.github.com/en/actions
- **GitHub Pages:** https://docs.github.com/en/pages
- **Technical Analysis:** https://www.investopedia.com/

---

**Built with ❤️ for NSE swing traders**

Last updated: 2025-05-09

---

## ⚙️ Risk configuration

Position sizing lives in `risk.py` and is configured by environment variables (set as repository **Variables** in GitHub → Settings → Secrets and variables → Actions):

| Variable | Default | Meaning |
|---|---|---|
| `EDGE_CAPITAL` | 565000 | Available INR equity |
| `EDGE_RISK_PCT` | 0.5 | % of capital risked per trade |
| `EDGE_MAX_POS_PCT` | 25 | Max position value, % of capital |
| `EDGE_MAX_OPEN_RISK_PCT` | 1.5 | Signals beyond this cumulative risk are dimmed as over budget (listed in an arbitrary fixed order: nothing is ranked) |

Shares are rounded down to the strictest of the risk, position-cap and cash limits; there is no forced one-share minimum. `sizer.js` mirrors the same formula and reads its defaults from `results.json`. If the data download fails or under 80% of symbols have usable data, the scan exits non-zero and the previous `results.json` is kept. Tests: `tests/test_risk.py` (pytest).


---

## 🧪 Backtester

`backtest.py` replays the live scanner rules (same `stage/setup/score/filters` code) over up to 10 years of history. Run it from **Actions → Backtest → Run workflow** (Yahoo is needed, so run it on GitHub or your own machine, not offline). Reports land in `reports/`.

- Signal on the close of day *t*; entry on *t+1* (next open, or a buy-stop above the signal-day high in the `trigger` variant)
- Stops fill at the stop or at the open on a gap; stop wins if stop and target share a bar
- 15 bps statutory/brokerage + 10 bps slippage per side (edit `Config` to change)
- Results in R-multiples with 95% CI, split by score band, setup, market regime, exit reason and year, plus an in-sample / out-of-sample split and a mark-to-market portfolio simulation

**Limitations:** the universe is today's constituents (survivorship bias flatters results), the StockEdge flag has no history so tiers are by score, and daily bars hide intraday order. A failing backtest is meaningful; a passing one is only a reason to start paper trading.


### Pre-registered research (`research.py`)

Runs a fixed grid of 12 entry/exit variants (trial count fixed in advance) and a diagnosis of whether the 0-100 score, or any of its components, predicts R. Design period = entries before 2023-01-01, hold-out = 2023 onward. Confidence intervals are month-clustered bootstraps (trades entered in the same month share market moves) with a Bonferroni adjustment for 12 trials. A variant is "promising" only if the design period is positive, the hold-out adjusted CI lower bound is above zero, and a fresh-start hold-out portfolio has positive CAGR. Outputs: `reports/grid.md`, `reports/diagnosis.md`.

Caveats: survivorship bias; the TRENDING-vs-pullback pattern was seen on the full sample before the hold-out was set, so only forward paper-trading data can confirm it.


---

## 🧾 Live strategy (v4) and paper-trading ledger

The scanner now outputs one thing: **signals** for the `prior_high/ema50/h120` variant of the pre-registered grid (spec in `strategy.py`). The High Conviction / GO / Watch tiers and the score ranking are gone, because the score did not predict returns (`reports/diagnosis.md`).

- **Signal:** stage 2 + Supertrend up + the scanner's filters, with the old score kept only as a qualifier (>= 72) because every tested signal satisfied it
- **Entry:** buy-stop at the signal-day high, valid for the next session only
- **Exit:** next open after a daily close below EMA50, or after 120 trading days; hard stop = close - max(1.5 x ATR, 3%)
- **Sizing:** from the buy-stop price to the stop, 0.5% risk, 25% position cap, 1.5% open-risk budget

`paper.py` logs every signal into `ledger.json` and follows it with the same `simulate_trade` the backtest uses, so paper and backtest results share one definition of a trade. `tests/test_screener_backtest_parity.py` asserts the live scanner and the backtest agree on every sampled day.

The Backtest workflow also writes `reports/universe.md`: the equal-weight return of this exact stock list versus the Nifty, an upper bound on how much any result is just "today's survivors went up".

**Status: paper-trading candidate, not a validated edge.** Survivorship bias, a strong 2023-26 hold-out and wide confidence intervals are unresolved. Do not trade real money from it until the ledger has on the order of 100 closed trades that look like the backtest.


---

## ✅ Readiness scorecard and monitoring

**`readiness.py`** computes the go-live rating from evidence (`reports/readiness.md`, `readiness.json`). It has 11 gates worth 10 points. Points are earned only by verified evidence: a passing backtest of the live variant, beating buy-and-hold of the same universe per unit of drawdown, 100+ closed forward signals over 6+ months, a forward expectancy whose confidence lower bound is above zero and not clearly below the backtest, 30+ live fills with slippage within 2x the model, and healthy operations and risk limits. Things code cannot verify (a survivorship-free backtest, a market-stress period survived, correct capital) are flags in `attestations.json` that default to `false`; set them only when genuinely true. Log real fills in `live_fills.csv`.

The score maps to a live-risk policy: under 4.5 or any kill switch or unconfirmed capital means paper only; a fill-test tier of 0.10% risk opens once the forward gates pass; 0.25% and 0.50% need more evidence. The thresholds are fixed in the code, not tuned.

**`health.py`** runs daily: scan freshness and coverage, ledger freshness and integrity, signal drought, edge decay on the forward record, a drawdown kill switch (8% of capital on taken signals; warning at 5%) and risk-limit sanity. A FAIL turns the workflow red (GitHub emails you) and opens an issue. Kill-switch levels are set in advance so they cannot be argued away during a drawdown.


---

## 🖥️ Pages

- **Trade Desk** (`index.html`, the homepage): market backdrop (Nifty trend, breadth; informational, with the live variant's regime behaviour in `reports/regime.md`), then one card per tradeable signal with a 60-day chart (EMA20, EMA50, buy level, stop), the plan (buy-stop, stop, shares, risk, exit line), automated execution checks and a manual pre-trade checklist. Signals that fail a hard execution check (thin liquidity, stop wider than 15%) move to a separate table with the reason. It always shows the live-trading status bar from the readiness scorecard.
- **Paper Trading & Readiness** (`paper.html`): the forward ledger, its results, the readiness scorecard and health checks.
- **Position Sizer** (`sizer.html`).

`analysis.py` defines the execution checks and the market backdrop. They are hygiene, not alpha: they were not part of the backtested rules, `warn` is information, and only a `block` hides a signal from the tradeable list. Sizes on the desk use the live risk the readiness policy allows; while that is 0 they show the reference (paper) size and say so.
