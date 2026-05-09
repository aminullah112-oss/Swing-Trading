# EDGE PROTOCOL Setup Guide

Complete these steps to get your automated screener running.

---

## ✅ Step 1: Push Code to GitHub

You now have all files ready. Copy them to your repo:

```bash
cd path/to/Swing-Trading

# Copy the files you downloaded from Claude
# (All files: screener.py, requirements.txt, index.html, etc.)

git add .
git commit -m "Initial EDGE PROTOCOL setup"
git push origin main
```

**Files to push:**
- `screener.py` — Main screener logic
- `requirements.txt` — Python dependencies
- `index.html`, `style.css`, `script.js` — Website
- `results.json` — Sample results (will auto-update)
- `.github/workflows/screen.yml` — GitHub Actions automation
- `README.md` — Documentation

---

## ✅ Step 2: Enable GitHub Pages

1. Go to: **GitHub.com** → Your **Swing-Trading** repo
2. Click **Settings** tab (top right)
3. Left sidebar → **Pages**
4. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/ (root)**
5. Click **Save**

**Wait 1-2 minutes.** Your site will be live at:
```
https://aminullah112-oss.github.io/Swing-Trading
```

---

## ✅ Step 3: Enable GitHub Actions

1. Go to: **GitHub.com** → Your **Swing-Trading** repo
2. Click **Actions** tab
3. You'll see a yellow banner saying:
   > "Enable workflows by pushing a commit to this repository"
4. Click **"I understand my workflows, go ahead and enable them"**
5. Click the **Daily Stock Screen** workflow on the left

**Automation is now active!**
- Runs every weekday at **9:00 AM IST** (Mon-Fri)
- Scans 50+ NSE stocks
- Auto-updates results.json
- Website refreshes every 5 minutes

---

## ✅ Step 4: Manual Test Run (Optional)

Test the workflow immediately without waiting for 9 AM:

1. Go to **Actions** → **Daily Stock Screen**
2. Click **"Run workflow"** button (top right)
3. Click **"Run workflow"** again to confirm
4. Wait 2-5 minutes
5. Refresh your website to see live results

**Check the workflow log:**
- Click the running job
- Watch Python execute the screener
- See which stocks passed filters

---

## 🎯 What Happens Now

### Every Weekday at 9 AM IST:

1. **GitHub Actions triggers** the workflow
2. **Python runs** `screener.py`:
   - Fetches 60 days of historical data for 50+ NSE stocks
   - Calculates EMA(20,50,200), RSI(14), Supertrend(10,3)
   - Applies all 5 filters
   - Returns matching stocks
3. **Results save** to `results.json`
4. **Git commits** automatically if results changed
5. **Website updates** — new results visible instantly
6. **History preserved** — each day's scan is in git history

### Manual Runs Anytime:

Go to **Actions** → **Daily Stock Screen** → **Run workflow**

---

## 🌐 Your Live Website

Visit: **https://aminullah112-oss.github.io/Swing-Trading**

Features:
- ✅ Live stock table with all indicators
- ✅ Auto-refresh every 5 minutes
- ✅ Filter rules displayed
- ✅ Scan timestamp
- ✅ Mobile responsive
- ✅ Zero maintenance

---

## ⚙️ Customization

### Change Scan Time

Edit `.github/workflows/screen.yml` line 8:

```yaml
- cron: '30 3 * * 1-5'  # Current: 9 AM IST (3:30 UTC), Mon-Fri
```

Use [crontab.guru](https://crontab.guru) to convert your timezone.

Examples:
- `0 4 * * 1-5` = 9:30 AM IST
- `30 2 * * 1-5` = 8 AM IST
- `0 9 * * 1-5` = 2:30 PM IST

### Change Stock List

Edit `screener.py` around line 15:

```python
NSE_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    # Add your stocks here
]
```

Add/remove NSE tickers as needed.

### Adjust Filters

Edit `screener.py`, function `apply_filters()` (line ~80):

```python
rsi_ok = (50 < ind['rsi'] < 75)  # Change 50-75 to your range
```

Modify any threshold to tighten/loosen screening.

---

## 🔧 Troubleshooting

### Website blank or showing "Loading..."?

**Cause:** Results.json not found or page not deployed yet

**Fix:**
1. Wait 1-2 minutes after enabling Pages
2. Check GitHub.com → Settings → Pages says "Your site is live"
3. Hard refresh browser (Ctrl+Shift+R)
4. Check browser console for errors (F12)

### Actions workflow failing?

**Cause:** Usually network timeout or yfinance rate limit

**Fix:**
1. Go to **Actions** tab → failed run
2. Click job to see error details
3. Click **"Run workflow"** again to retry
4. If persistent, yfinance may be temporarily down — try again in 5 min

### No stocks found in results?

**Cause:** Market conditions don't match filters

**Fix:**
1. Normal behavior — some days have no matches
2. Check filters aren't too strict
3. Run manually during market hours (9:15 AM - 3:30 PM IST)
4. Loosen RSI range or other thresholds if needed

### How to disable/pause automation?

Go to **Actions** → **Daily Stock Screen** → click **...** → **Disable workflow**

---

## 📊 Understanding Results

Each stock in the table shows:
- **Symbol** — NSE ticker name
- **Price** — Current price in INR
- **EMA 20/50/200** — Trend confirmation
- **RSI(14)** — Momentum (50-75 range ✅)
- **Supertrend** — Dynamic support level
- **Volume** — Today's volume in millions/thousands

---

## 🎓 Next Steps

1. **Share your dashboard** — Send the website URL to friends/traders
2. **Integrate with trading** — Use results for swing entries
3. **Track history** — Check GitHub commits to see past scans
4. **Refine filters** — Test different indicator combinations
5. **Add more stocks** — Expand NSE_STOCKS list
6. **Collect data** — results.json contains full history

---

## 🚀 You're Done!

Your automated NSE screener is now:
- ✅ Running daily at 9 AM IST
- ✅ Displaying results on your website
- ✅ Preserved in git history
- ✅ Zero cost, zero maintenance
- ✅ GitHub Pages hosted (always free)

**Check back tomorrow morning to see your first automated scan!**

Questions? See README.md for full documentation.

---

**Built for swing traders. Powered by GitHub. ❤️**
