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
