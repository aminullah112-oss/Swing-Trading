#!/usr/bin/env python3
"""
EDGE PROTOCOL v3.2 — Stooq Data Source
========================================
Uses Stooq.com for NSE historical data.
Stooq serves NSE data freely without IP blocking or authentication.
Format: {SYMBOL}.NS (e.g. RELIANCE.NS)
"""

import json, glob, time, warnings, traceback
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests

warnings.filterwarnings('ignore')

CAPITAL       = 750000
RISK_PCT_HC   = 0.02
RISK_PCT_GO   = 0.01
MAX_POSITIONS = 5

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
    'CHOLAFIN','LICHSGFIN','MANAPPURAM','SUNDARMFIN','SHRIRAMFIN',
    'PIIND','PERSISTENT','COFORGE','MPHASIS','LTTS',
    'KPITTECH','TATAELXSI','CYIENT','DEEPAKNTR','AARTI',
    'NAVINFLUOR','TATACHEM','APOLLOTYRE','BALKRISIND','CEATLTD',
    'MRF','TVSMOTORS','MOTHERSON','BHARATFORG','BOSCHLTD',
    'VOLTAS','KAJARIACER','SUPREMEIND','ASTRAL','POLYCAB',
    'KEI','PAGEIND','RADICO','LAURUSLABS','GRANULES',
    'AJANTPHARM','ERIS','METROPOLIS','MAXHEALTH','FORTIS',
    'NH','SYNGENE','BRIGADE','SOBHA','PRESTIGE',
    'GODREJPROP','PHOENIXLTD','OBEROIRLTY','THERMAX','CUMMINSIND',
    'PRAJ','EMAMILTD','BEL','HAL','IRFC',
    'RVNL','PFC','REC','SJVN','NHPC',
    'SUZLON','TRIDENT','RAYMOND','COROMANDEL','CHAMBLFERT',
    'RALLIS','DHANUKA','ATUL','NOCIL','APLAPOLLO',
]
NSE_STOCKS = list(dict.fromkeys(NSE_STOCKS))


def fetch_stooq(symbol, days=400):
    """
    Fetch OHLCV data from Stooq.com.
    NSE symbols: RELIANCE.NS, TCS.NS etc.
    Returns sorted DataFrame or None.
    """
    end   = datetime.now()
    start = end - timedelta(days=days)
    url   = (
        f'https://stooq.com/q/d/l/'
        f'?s={symbol.lower()}.ns'
        f'&d1={start.strftime("%Y%m%d")}'
        f'&d2={end.strftime("%Y%m%d")}'
        f'&i=d'
    )
    try:
        resp = requests.get(url, timeout=15,
                            headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code != 200:
            return None
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text))
        if df.empty or 'No data' in resp.text or len(df) < 5:
            return None
        df.columns = [c.strip() for c in df.columns]
        # Stooq columns: Date,Open,High,Low,Close,Volume
        df['Date']   = pd.to_datetime(df['Date'])
        df['Open']   = pd.to_numeric(df['Open'],   errors='coerce')
        df['High']   = pd.to_numeric(df['High'],   errors='coerce')
        df['Low']    = pd.to_numeric(df['Low'],    errors='coerce')
        df['Close']  = pd.to_numeric(df['Close'],  errors='coerce')
        df['Volume'] = pd.to_numeric(df.get('Volume', pd.Series([0]*len(df))),
                                     errors='coerce').fillna(0)
        df = df.dropna(subset=['Open','High','Low','Close'])
        df = df.sort_values('Date').reset_index(drop=True)
        return df if len(df) >= 50 else None
    except Exception:
        return None


def compute_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_supertrend(high, low, close, period=10, mult=3):
    atr   = compute_atr(high, low, close, period)
    hl2   = (high + low) / 2
    upper = hl2 + mult * atr
    lower = hl2 - mult * atr
    st    = [np.nan] * len(close)
    dir_  = [1] * len(close)
    for i in range(1, len(close)):
        fu = (upper.iloc[i] if upper.iloc[i] < upper.iloc[i-1]
              or close.iloc[i-1] > upper.iloc[i-1]
              else upper.iloc[i-1])
        fl = (lower.iloc[i] if lower.iloc[i] > lower.iloc[i-1]
              or close.iloc[i-1] < lower.iloc[i-1]
              else lower.iloc[i-1])
        if   close.iloc[i] > fu: dir_[i] = 1;  st[i] = fl
        elif close.iloc[i] < fl: dir_[i] = -1; st[i] = fu
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

    def slope(s, n): return (s.iloc[-1] - s.iloc[-n]) / s.iloc[-n] * 100

    rsi       = compute_rsi(close, 14)
    st, st_d  = compute_supertrend(high, low, close, 10, 3)

    price     = close.iloc[-1]
    ema20v    = ema20.iloc[-1]
    ema50v    = ema50.iloc[-1]
    ema200v   = ema200.iloc[-1]
    atr_val   = compute_atr(high, low, close, 14).iloc[-1]

    # Volume: use 10-day avg of completed sessions
    vol10     = volume.iloc[-11:-1].mean() if len(volume) > 11 else volume.mean()
    vol5      = volume.iloc[-6:-1].mean()  if len(volume) > 6  else volume.mean()
    curr_vol  = volume.iloc[-1]

    high52    = high.tail(252).max()
    low52     = low.tail(252).min()

    return {
        'price':        price,
        'ema_20':       ema20v,
        'ema_50':       ema50v,
        'ema_200':      ema200v,
        'ema20_slope':  slope(ema20, 6),
        'ema50_slope':  slope(ema50, 6),
        'ema200_slope': slope(ema200, 11),
        'rsi':          rsi.iloc[-1],
        'rsi_5ago':     rsi.iloc[-6] if len(rsi) > 6 else rsi.iloc[-1],
        'st_dir':       int(st_d.iloc[-1]),
        'vol_ratio':    curr_vol / vol10 if vol10 > 0 else 1,
        'vol_5d_ratio': curr_vol / vol5  if vol5  > 0 else 1,
        'ema20_dist':   (price - ema20v) / ema20v * 100,
        'from_52w_high':(price - high52) / high52 * 100,
        'atr_val':      atr_val,
        'atr_pct':      atr_val / price * 100,
        'high':         high.iloc[-1],
        'low':          low.iloc[-1],
    }


def get_stage(ind):
    if (ind['price'] > ind['ema_200'] and
        ind['ema200_slope'] > 0 and
        ind['ema_50'] > ind['ema_200'] and
        ind['ema_20'] > ind['ema_50']):
        if ind['rsi'] > 75 or ind['from_52w_high'] > -2:
            return 3
        return 2
    if ind['price'] < ind['ema_200'] and ind['ema200_slope'] < 0:
        return 4
    return 1


def get_setup(ind):
    d20 = ind['ema20_dist']
    rsi = ind['rsi']
    if -2 <= d20 <= 4 and ind['rsi_5ago'] > rsi and rsi < 63:
        return 'PULLBACK_EMA20', 'Pullback to EMA20 — re-entry'
    d50 = (ind['price'] - ind['ema_50']) / ind['ema_50'] * 100
    if -2 <= d50 <= 4 and rsi < 58:
        return 'PULLBACK_EMA50', 'Pullback to EMA50'
    if 4 < d20 <= 9 and ind['vol_ratio'] >= 1.3 and rsi > 52:
        return 'BREAKOUT_CONT', 'Breakout continuation'
    if ind['atr_pct'] < 1.8 and -3 <= d20 <= 6:
        return 'COMPRESSION', 'Volatility compression'
    return 'TRENDING', 'Stage 2 momentum'


def score_stock(ind, stage, setup):
    score, reasons = 0, []

    # Stage (25)
    if stage == 2:
        score += 25; reasons.append("Stage 2 uptrend (+25)")

    # Setup (20)
    pts = {'PULLBACK_EMA20':20,'PULLBACK_EMA50':14,
           'COMPRESSION':12,'BREAKOUT_CONT':10,'TRENDING':6}
    s = pts.get(setup, 0)
    score += s; reasons.append(f"{setup} (+{s})")

    # RSI (20)
    rsi = ind['rsi']
    if   45 <= rsi <= 62: score += 20; reasons.append(f"RSI {rsi:.0f} ideal (+20)")
    elif 62 <  rsi <= 70: score += 13; reasons.append(f"RSI {rsi:.0f} strong (+13)")
    elif 38 <= rsi <  45: score += 8;  reasons.append(f"RSI {rsi:.0f} bounce (+8)")
    elif 70 <  rsi <= 76: score += 4;  reasons.append(f"RSI {rsi:.0f} extended (+4)")
    else:                              reasons.append(f"RSI {rsi:.0f} poor (+0)")

    # Volume (20) — use best of 10d and 5d ratio
    vr = max(ind['vol_ratio'], ind['vol_5d_ratio'])
    if   vr >= 1.8: score += 20; reasons.append(f"Vol {vr:.1f}x surge (+20)")
    elif vr >= 1.2: score += 13; reasons.append(f"Vol {vr:.1f}x above avg (+13)")
    elif vr >= 0.7: score += 7;  reasons.append(f"Vol {vr:.1f}x avg (+7)")
    else:           score += 3;  reasons.append(f"Vol {vr:.1f}x low (+3)")

    # EMA slopes (15)
    s3 = sum([ind['ema20_slope']>0, ind['ema50_slope']>0, ind['ema200_slope']>0])
    if   s3 == 3: score += 15; reasons.append("All EMAs rising (+15)")
    elif s3 == 2: score += 10; reasons.append("2 EMAs rising (+10)")
    else:         score += 3;  reasons.append("1 EMA rising (+3)")

    # Bonus
    if -18 <= ind['from_52w_high'] <= -3:
        score += 3; reasons.append("Near 52W high (+3)")
    if ind['st_dir'] == 1:
        score += 3; reasons.append("Supertrend bullish (+3)")

    return min(score, 100), reasons


def passes_filters(ind, stage):
    if stage != 2:
        return False, f"Stage {stage}"
    if ind['st_dir'] != 1:
        return False, "Supertrend bearish"
    if not (33 < ind['rsi'] < 80):
        return False, f"RSI {ind['rsi']:.0f}"
    if ind['price'] < ind['ema_50'] * 0.95:
        return False, "Below EMA50"
    if ind['price'] < 20:
        return False, "Price<20"
    return True, "OK"


def get_decision(score, in_se):
    if score >= 72 and in_se: return 'HIGH_CONVICTION'
    if score >= 72:           return 'GO'
    if score >= 55 and in_se: return 'WATCH_CLOSELY'
    if score >= 55:           return 'WATCH'
    return 'NO_GO'


def calc_position(price, atr, decision):
    sd  = max(1.5 * atr, price * 0.03)  # min 3% stop
    stp = round(price - sd, 2)
    if decision == 'HIGH_CONVICTION': risk = CAPITAL * RISK_PCT_HC
    elif decision == 'GO':            risk = CAPITAL * RISK_PCT_GO
    else:                             return None
    shares = max(1, int(risk / sd))
    return {
        'shares':      shares,
        'invested':    round(shares * price, 2),
        'stop_loss':   stp,
        'risk_amount': round(shares * sd, 2),
        'target_1':    round(price + 2.0 * sd, 2),
        'target_2':    round(price + 3.0 * sd, 2),
        'rr_ratio':    '2:1 / 3:1',
    }


def load_stockedge():
    se    = set()
    files = glob.glob('stockedge*.csv') + glob.glob('StockEdge*.csv')
    if not files:
        print("No stockedge.csv found. Upload for HIGH CONVICTION labels.")
        return se
    try:
        df  = pd.read_csv(files[0])
        col = next((c for c in ['Symbol','symbol','SYMBOL','Ticker','NSE Code']
                    if c in df.columns), df.columns[0])
        se  = set(df[col].dropna().astype(str).str.strip().str.upper())
        print(f"StockEdge loaded: {len(se)} stocks")
    except Exception as e:
        print(f"StockEdge error: {e}")
    return se


def main():
    print("\n" + "="*70)
    print("EDGE PROTOCOL v3.2 — Stooq Data Source")
    print(f"Capital: Rs{CAPITAL/100000:.1f}L | Universe: {len(NSE_STOCKS)} stocks")
    print(f"Scan: {datetime.now().strftime('%A %Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    se_symbols = load_stockedge()
    results    = []
    stats      = {'data':0,'stage':0,'supertrend':0,'rsi':0,'price':0,'nogo':0}

    print(f"{'Symbol':<14} {'Stage':<7} {'Setup':<20} {'Sc':<5} {'RSI':<6} Decision")
    print("-"*70)

    for i, symbol in enumerate(NSE_STOCKS):
        try:
            if i > 0 and i % 30 == 0:
                time.sleep(1)

            df = fetch_stooq(symbol, days=420)

            if df is None or len(df) < 60:
                stats['data'] += 1
                print(f"{symbol:<14} No data")
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

            setup, sdesc = get_setup(ind)
            score, rsns  = score_stock(ind, stage, setup)
            in_se        = symbol in se_symbols
            decision     = get_decision(score, in_se)

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
                'setup_desc':    sdesc,
                'in_stockedge':  in_se,
                'price':         round(ind['price'],        2),
                'ema_20':        round(ind['ema_20'],       2),
                'ema_50':        round(ind['ema_50'],       2),
                'ema_200':       round(ind['ema_200'],      2),
                'rsi':           round(ind['rsi'],          2),
                'vol_ratio':     round(max(ind['vol_ratio'], ind['vol_5d_ratio']), 2),
                'vol_5d_ratio':  round(ind['vol_5d_ratio'], 2),
                'ema_dist_pct':  round(ind['ema20_dist'],   2),
                'from_52w_high': round(ind['from_52w_high'],2),
                'atr_pct':       round(ind['atr_pct'],      2),
                'st_direction':  ind['st_dir'],
                'reasons':       rsns,
                'position':      pos,
                'timestamp':     datetime.now().isoformat(),
            })

            tag = {'HIGH_CONVICTION':'🟢HC','GO':'🟩GO',
                   'WATCH_CLOSELY':'🟡WC','WATCH':'🟨W'}.get(decision,'?')
            se  = '[SE]' if in_se else ''
            print(f"{symbol:<14} S{stage:<6} {setup:<20} {score:<5} "
                  f"{ind['rsi']:<6.1f} {tag} {se}")

        except Exception as e:
            print(f"{symbol}: {str(e)[:60]}")

    pri = {'HIGH_CONVICTION':0,'GO':1,'WATCH_CLOSELY':2,'WATCH':3}
    results.sort(key=lambda x: (pri.get(x['decision'],9), -x['score']))

    hc = sum(1 for r in results if r['decision']=='HIGH_CONVICTION')
    go = sum(1 for r in results if r['decision']=='GO')
    wc = sum(1 for r in results if r['decision']=='WATCH_CLOSELY')
    w  = sum(1 for r in results if r['decision']=='WATCH')

    print("\n" + "="*70)
    print(f"COMPLETE | {len(results)} setups | HC:{hc} GO:{go} WC:{wc} W:{w}")
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
        'summary':      {'high_conviction':hc,'go':go,'watch_closely':wc,'watch':w},
        'stocks':       results,
    }

    with open('results.json','w') as f:
        json.dump(output, f, indent=2)
    print(f"Saved {len(results)} results to results.json")


if __name__ == '__main__':
    main()
