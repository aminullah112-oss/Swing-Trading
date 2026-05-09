#!/usr/bin/env python3
"""
EDGE PROTOCOL v3.1 — NSE Direct API
=====================================
Uses NSEPython (NSE India official data) instead of Yahoo Finance.
Yahoo Finance blocks GitHub Actions IPs. NSE API does not.

Data source: NSE India public API via nsepython library
"""

import json
import glob
import time
import warnings
import traceback
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import requests

warnings.filterwarnings('ignore')

# ── Capital config ──────────────────────────────────────────
CAPITAL       = 750000
RISK_PCT_HC   = 0.02
RISK_PCT_GO   = 0.01
MAX_POSITIONS = 5

# ── NSE 200 liquid stocks (symbols exactly as NSE uses them) ─
NSE_STOCKS = [
    'RELIANCE','TCS','HDFCBANK','INFY','HINDUNILVR',
    'ICICIBANK','SBIN','BHARTIARTL','KOTAKBANK','LT',
    'AXISBANK','WIPRO','MARUTI','BAJFINANCE','HCLTECH',
    'ASIANPAINT','ULTRACEMCO','TITAN','SUNPHARMA','NESTLEIND',
    'TECHM','TATAMOTORS','INDUSINDBK','POWERGRID','NTPC',
    'BAJAJFINSV','ONGC','JSWSTEEL','TATASTEEL','COALINDIA',
    'ADANIENT','ADANIPORTS','CIPLA','DRREDDY','DIVISLAB',
    'BRITANNIA','EICHERMOT','GRASIM','HEROMOTOCO','ITC',
    'MM','BPCL','IOC','TATACONSUM','APOLLOHOSP',
    'BAJAJ-AUTO','UPL','SBILIFE','HDFCLIFE','HINDALCO',
    'DMART','SIEMENS','HAVELLS','PIDILITIND','DABUR',
    'MARICO','COLPAL','BERGEPAINT','GODREJCP','MUTHOOTFIN',
    'LUPIN','BIOCON','TORNTPHARM','ALKEM','AUROPHARMA',
    'GLENMARK','AMBUJACEM','ACC','SHREECEM','INDIGO',
    'TATAPOWER','TRENT','NAUKRI','IRCTC','CONCOR',
    'SAIL','NMDC','VEDL','GAIL','PETRONET',
    'GUJARATGAS','IGL','ZOMATO','BANKBARODA','PNB',
    'CANBK','FEDERALBNK','IDFCFIRSTB','RBLBANK','AUBANK',
    'CHOLAFIN','LICHSGFIN','MANAPPURAM','MFIN','SUNDARMFIN',
    'SHRIRAMFIN','PIIND','PERSISTENT','COFORGE','MPHASIS',
    'LTTS','KPITTECH','TATAELXSI','CYIENT','DEEPAKNTR',
    'AARTI','NAVINFLUOR','TATACHEM','APOLLOTYRE','BALKRISIND',
    'CEATLTD','MRF','TVSMOTORS','MOTHERSON','BHARATFORG',
    'BOSCHLTD','VOLTAS','KAJARIACER','SUPREMEIND','ASTRAL',
    'POLYCAB','KEI','PAGEIND','RADICO','LAURUSLABS',
    'GRANULES','AJANTPHARM','ERIS','METROPOLIS','MAXHEALTH',
    'FORTIS','NH','SYNGENE','BRIGADE','SOBHA',
    'PRESTIGE','GODREJPROP','PHOENIXLTD','OBEROIRLTY','THERMAX',
    'CUMMINSIND','PRAJ','EMAMILTD','BEL','HAL',
    'IRFC','RVNL','PFC','REC','SJVN',
    'NHPC','SUZLON','TRIDENT','RAYMOND','COROMANDEL',
    'CHAMBLFERT','RALLIS','DHANUKA','ATUL','NOCIL',
    'APLAPOLLO','RATNAMANI','WELCORP','WELSPUNIND','KPRMILL',
]
NSE_STOCKS = list(dict.fromkeys(NSE_STOCKS))


# ── Headers to mimic browser (NSE API requires this) ─────────
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/120.0.0.0 Safari/537.36'),
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.nseindia.com/',
    'Connection': 'keep-alive',
}

def get_nse_session():
    """Create a requests session with NSE cookies."""
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get('https://www.nseindia.com', timeout=10)
        time.sleep(1)
    except Exception:
        pass
    return session


def fetch_nse_history(session, symbol, days=365):
    """
    Fetch historical OHLCV data from NSE India API.
    Returns DataFrame with columns: Date, Open, High, Low, Close, Volume
    """
    end_date   = datetime.now()
    start_date = end_date - timedelta(days=days)

    series = 'EQ'
    url = (
        f'https://www.nseindia.com/api/historical/cm/equity'
        f'?symbol={symbol}&series=["{series}"]'
        f'&from={start_date.strftime("%d-%m-%Y")}'
        f'&to={end_date.strftime("%d-%m-%Y")}&csv=false'
    )

    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None

        data = resp.json()
        records = data.get('data', [])
        if not records:
            return None

        df = pd.DataFrame(records)
        df = df.rename(columns={
            'CH_TIMESTAMP':   'Date',
            'CH_OPENING_PRICE': 'Open',
            'CH_TRADE_HIGH_PRICE': 'High',
            'CH_TRADE_LOW_PRICE':  'Low',
            'CH_CLOSING_PRICE':    'Close',
            'CH_TOT_TRADED_QTY':   'Volume',
        })
        df = df[['Date','Open','High','Low','Close','Volume']].copy()
        df['Date']   = pd.to_datetime(df['Date'])
        df['Open']   = pd.to_numeric(df['Open'],   errors='coerce')
        df['High']   = pd.to_numeric(df['High'],   errors='coerce')
        df['Low']    = pd.to_numeric(df['Low'],    errors='coerce')
        df['Close']  = pd.to_numeric(df['Close'],  errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)
        df = df.dropna()
        return df

    except Exception as e:
        return None


# ── Technical Indicators ─────────────────────────────────────
def compute_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_supertrend(high, low, close, period=10, mult=3):
    atr  = compute_atr(high, low, close, period)
    hl2  = (high + low) / 2
    upper = hl2 + mult * atr
    lower = hl2 - mult * atr

    st  = [np.nan] * len(close)
    dir_ = [1]  * len(close)

    for i in range(1, len(close)):
        fu = upper.iloc[i] if upper.iloc[i] < upper.iloc[i-1] or close.iloc[i-1] > upper.iloc[i-1] else upper.iloc[i-1]
        fl = lower.iloc[i] if lower.iloc[i] > lower.iloc[i-1] or close.iloc[i-1] < lower.iloc[i-1] else lower.iloc[i-1]

        if close.iloc[i] > fu:
            dir_[i] = 1;  st[i] = fl
        elif close.iloc[i] < fl:
            dir_[i] = -1; st[i] = fu
        else:
            dir_[i] = dir_[i-1]
            st[i]   = fl if dir_[i] == 1 else fu

    return pd.Series(st, index=close.index), pd.Series(dir_, index=close.index)


def compute_rsi(close, period=14):
    delta = close.diff()
    gain  = delta.where(delta > 0, 0.0).ewm(com=period-1, adjust=False).mean()
    loss  = (-delta.where(delta < 0, 0.0)).ewm(com=period-1, adjust=False).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def compute_indicators(df):
    close  = df['Close']
    high   = df['High']
    low    = df['Low']
    volume = df['Volume']

    ema20  = close.ewm(span=20,  adjust=False).mean()
    ema50  = close.ewm(span=50,  adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    ema20_slope  = (ema20.iloc[-1]  - ema20.iloc[-6])  / ema20.iloc[-6]  * 100
    ema50_slope  = (ema50.iloc[-1]  - ema50.iloc[-6])  / ema50.iloc[-6]  * 100
    ema200_slope = (ema200.iloc[-1] - ema200.iloc[-11]) / ema200.iloc[-11] * 100

    rsi      = compute_rsi(close, 14)
    rsi_now  = rsi.iloc[-1]
    rsi_5ago = rsi.iloc[-6] if len(rsi) > 6 else rsi_now

    st_line, st_dir = compute_supertrend(high, low, close, 10, 3)

    vol_10d = volume.iloc[-11:-1].mean()
    vol_5d  = volume.iloc[-6:-1].mean()
    curr_vol = volume.iloc[-1]

    price    = close.iloc[-1]
    ema20v   = ema20.iloc[-1]
    ema50v   = ema50.iloc[-1]
    ema200v  = ema200.iloc[-1]

    ema20_dist = (price - ema20v) / ema20v * 100

    high_52w  = high.tail(252).max()
    low_52w   = low.tail(252).min()
    f52h      = (price - high_52w) / high_52w * 100
    f52l      = (price - low_52w)  / low_52w  * 100

    atr_val   = compute_atr(high, low, close, 14).iloc[-1]
    atr_pct   = atr_val / price * 100

    return {
        'price':        price,
        'ema_20':       ema20v,
        'ema_50':       ema50v,
        'ema_200':      ema200v,
        'ema20_slope':  ema20_slope,
        'ema50_slope':  ema50_slope,
        'ema200_slope': ema200_slope,
        'rsi':          rsi_now,
        'rsi_5ago':     rsi_5ago,
        'st_line':      st_line.iloc[-1],
        'st_dir':       int(st_dir.iloc[-1]),
        'vol_10d_avg':  vol_10d,
        'vol_5d_avg':   vol_5d,
        'vol_ratio':    curr_vol / vol_10d if vol_10d > 0 else 0,
        'vol_5d_ratio': curr_vol / vol_5d  if vol_5d  > 0 else 0,
        'ema20_dist':   ema20_dist,
        'from_52w_high':f52h,
        'from_52w_low': f52l,
        'atr_val':      atr_val,
        'atr_pct':      atr_pct,
        'high':         high.iloc[-1],
        'low':          low.iloc[-1],
    }


def get_stage(ind):
    p = ind['price']
    if (p > ind['ema_200'] and
        ind['ema200_slope'] > 0 and
        ind['ema_50'] > ind['ema_200'] and
        ind['ema_20'] > ind['ema_50']):
        if ind['rsi'] > 72 or ind['from_52w_high'] > -3:
            return 3
        return 2
    if p < ind['ema_200'] and ind['ema200_slope'] < 0:
        return 4
    return 1


def get_setup(ind):
    d20 = ind['ema20_dist']
    rsi = ind['rsi']
    r5  = ind['rsi_5ago']

    if -1 <= d20 <= 3 and r5 > rsi and rsi < 62:
        return 'PULLBACK_EMA20', 'Pullback to EMA20 — ideal re-entry'
    d50 = (ind['price'] - ind['ema_50']) / ind['ema_50'] * 100
    if -1 <= d50 <= 3 and rsi < 57:
        return 'PULLBACK_EMA50', 'Pullback to EMA50 — wider stop needed'
    if d20 > 3 and d20 <= 8 and ind['vol_ratio'] >= 1.4 and rsi > 55:
        return 'BREAKOUT_CONT', 'Breakout continuation with volume'
    if ind['atr_pct'] < 1.5 and -2 <= d20 <= 5:
        return 'COMPRESSION', 'Low volatility compression — coiling'
    return 'TRENDING', 'Stage 2 trending — momentum play'


def score_stock(ind, stage, setup):
    score   = 0
    reasons = []

    # Stage (25)
    if stage == 2:
        score += 25; reasons.append("Stage 2 uptrend (+25)")

    # Setup (20)
    pts = {'PULLBACK_EMA20':20,'PULLBACK_EMA50':14,'COMPRESSION':12,
           'BREAKOUT_CONT':10,'TRENDING':6}
    s = pts.get(setup, 0)
    score += s; reasons.append(f"{setup} (+{s})")

    # RSI (20)
    rsi = ind['rsi']
    if   45 <= rsi <= 60: score += 20; reasons.append(f"RSI fresh {rsi:.0f} (+20)")
    elif 60 <  rsi <= 68: score += 14; reasons.append(f"RSI strong {rsi:.0f} (+14)")
    elif 40 <= rsi < 45:  score += 8;  reasons.append(f"RSI bounce {rsi:.0f} (+8)")
    elif 68 <  rsi <= 75: score += 5;  reasons.append(f"RSI extended {rsi:.0f} (+5)")
    else:                              reasons.append(f"RSI poor {rsi:.0f} (+0)")

    # Volume (20)
    vr = max(ind['vol_ratio'], ind['vol_5d_ratio'])
    if   vr >= 2.0: score += 20; reasons.append(f"Vol {vr:.1f}x surge (+20)")
    elif vr >= 1.3: score += 13; reasons.append(f"Vol {vr:.1f}x above avg (+13)")
    elif vr >= 0.8: score += 7;  reasons.append(f"Vol {vr:.1f}x avg (+7)")
    else:           score += 3;  reasons.append(f"Vol low (+3)")

    # Trend slope (15)
    slopes = sum([ind['ema20_slope']>0, ind['ema50_slope']>0, ind['ema200_slope']>0])
    if   slopes == 3: score += 15; reasons.append("All EMAs rising (+15)")
    elif slopes == 2: score += 10; reasons.append("2 EMAs rising (+10)")
    else:             score += 4;  reasons.append("1 EMA rising (+4)")

    # Bonus
    if -15 <= ind['from_52w_high'] <= -3:
        score += 3; reasons.append("Near 52W high (+3)")
    if ind['st_dir'] == 1:
        score += 3; reasons.append("Supertrend bullish (+3)")

    return min(score, 100), reasons


def passes_filters(ind, stage):
    if stage != 2:
        return False, f"Stage {stage}"
    if ind['st_dir'] != 1:
        return False, "Supertrend bearish"
    if not (35 < ind['rsi'] < 78):
        return False, f"RSI {ind['rsi']:.0f}"
    if ind['price'] < ind['ema_50'] * 0.96:
        return False, "Below EMA50"
    if ind['price'] < 20:
        return False, "Price < Rs20"
    return True, "OK"


def get_decision(score, in_se):
    if score >= 75 and in_se: return 'HIGH_CONVICTION'
    if score >= 75:           return 'GO'
    if score >= 58 and in_se: return 'WATCH_CLOSELY'
    if score >= 58:           return 'WATCH'
    return 'NO_GO'


def calc_position(price, atr, decision):
    stop_dist = 1.5 * atr
    stop      = round(price - stop_dist, 2)
    if decision == 'HIGH_CONVICTION': risk = CAPITAL * RISK_PCT_HC
    elif decision == 'GO':            risk = CAPITAL * RISK_PCT_GO
    else:                             return None
    shares = max(1, int(risk / stop_dist))
    return {
        'shares':      shares,
        'invested':    round(shares * price, 2),
        'stop_loss':   stop,
        'risk_amount': round(shares * stop_dist, 2),
        'target_1':    round(price + 2.0 * stop_dist, 2),
        'target_2':    round(price + 3.0 * stop_dist, 2),
        'rr_ratio':    '2:1 / 3:1',
    }


def load_stockedge():
    se = set()
    files = glob.glob('stockedge*.csv') + glob.glob('StockEdge*.csv')
    if not files:
        print("No stockedge.csv — upload to repo for HIGH CONVICTION labels")
        return se
    try:
        df  = pd.read_csv(files[0])
        col = next((c for c in ['Symbol','symbol','SYMBOL','Ticker','NSE Code']
                    if c in df.columns), df.columns[0])
        se  = set(df[col].dropna().astype(str).str.strip().str.upper())
        print(f"StockEdge: {len(se)} stocks loaded")
    except Exception as e:
        print(f"StockEdge error: {e}")
    return se


def main():
    print("\n" + "="*70)
    print("EDGE PROTOCOL v3.1 — NSE Direct API")
    print(f"Capital: Rs{CAPITAL/100000:.1f}L | Stocks: {len(NSE_STOCKS)}")
    print(f"Scan: {datetime.now().strftime('%A %Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    se_symbols = load_stockedge()
    session    = get_nse_session()
    results    = []
    stats      = {'data':0,'stage':0,'supertrend':0,'rsi':0,'price':0,'nogo':0}

    print(f"{'Symbol':<14} {'Stage':<7} {'Setup':<20} {'Sc':<5} {'RSI':<6} Decision")
    print("-"*70)

    for i, symbol in enumerate(NSE_STOCKS):
        try:
            # Small delay to avoid rate limiting
            if i > 0 and i % 20 == 0:
                time.sleep(2)

            df = fetch_nse_history(session, symbol, days=400)

            if df is None or len(df) < 210:
                stats['data'] += 1
                continue

            ind   = compute_indicators(df)
            stage = get_stage(ind)

            ok, reason = passes_filters(ind, stage)
            if not ok:
                key = ('stage' if 'Stage' in reason else
                       'supertrend' if 'Super' in reason else
                       'rsi' if 'RSI' in reason else 'price')
                stats[key] += 1
                continue

            setup, setup_desc = get_setup(ind)
            score, reasons    = score_stock(ind, stage, setup)
            in_se             = symbol in se_symbols
            decision          = get_decision(score, in_se)

            if decision == 'NO_GO':
                stats['nogo'] += 1
                continue

            pos = calc_position(ind['price'], ind['atr_val'], decision)

            results.append({
                'symbol':        symbol,
                'decision':      decision,
                'score':         score,
                'stage':         stage,
                'setup_type':    setup,
                'setup_desc':    setup_desc,
                'in_stockedge':  in_se,
                'price':         round(ind['price'],        2),
                'ema_20':        round(ind['ema_20'],       2),
                'ema_50':        round(ind['ema_50'],       2),
                'ema_200':       round(ind['ema_200'],      2),
                'rsi':           round(ind['rsi'],          2),
                'vol_ratio':     round(ind['vol_ratio'],    2),
                'vol_5d_ratio':  round(ind['vol_5d_ratio'], 2),
                'ema_dist_pct':  round(ind['ema20_dist'],   2),
                'from_52w_high': round(ind['from_52w_high'],2),
                'atr_pct':       round(ind['atr_pct'],      2),
                'st_direction':  ind['st_dir'],
                'reasons':       reasons,
                'position':      pos,
                'timestamp':     datetime.now().isoformat(),
            })

            tag = {'HIGH_CONVICTION':'HC','GO':'GO',
                   'WATCH_CLOSELY':'WC','WATCH':'W'}.get(decision,'?')
            se  = '[SE]' if in_se else ''
            print(f"{symbol:<14} S{stage:<6} {setup:<20} {score:<5} "
                  f"{ind['rsi']:<6.1f} {tag} {se}")

        except Exception as e:
            print(f"{symbol}: Error — {str(e)[:50]}")
            continue

    # Sort by decision priority then score
    pri = {'HIGH_CONVICTION':0,'GO':1,'WATCH_CLOSELY':2,'WATCH':3}
    results.sort(key=lambda x: (pri.get(x['decision'],9), -x['score']))

    hc = sum(1 for r in results if r['decision']=='HIGH_CONVICTION')
    go = sum(1 for r in results if r['decision']=='GO')
    wc = sum(1 for r in results if r['decision']=='WATCH_CLOSELY')
    w  = sum(1 for r in results if r['decision']=='WATCH')

    print("\n" + "="*70)
    print(f"DONE | Passed: {len(results)} | HC:{hc} GO:{go} WC:{wc} W:{w}")
    print(f"Filtered → Stage:{stats['stage']} ST:{stats['supertrend']} "
          f"RSI:{stats['rsi']} Price:{stats['price']} "
          f"Data:{stats['data']} NoGo:{stats['nogo']}")
    print("="*70)

    output = {
        'timestamp':    datetime.now().isoformat(),
        'scan_date':    datetime.now().strftime('%Y-%m-%d'),
        'scan_time':    datetime.now().strftime('%H:%M:%S'),
        'capital':      CAPITAL,
        'total_scanned':len(NSE_STOCKS),
        'total_passed': len(results),
        'summary': {'high_conviction':hc,'go':go,'watch_closely':wc,'watch':w},
        'stocks':       results,
    }

    with open('results.json','w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(results)} results to results.json")

if __name__ == '__main__':
    main()
