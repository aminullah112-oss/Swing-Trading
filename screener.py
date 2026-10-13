#!/usr/bin/env python3
"""
EDGE PROTOCOL v3.4
- yfinance bulk download (working)
- StockEdge CSV fixed (skip rows 1-5, use Symbol column B)
- Fixed 7 broken Yahoo Finance ticker symbols
"""

import hashlib, json, glob, os, sys, time, uuid, warnings
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import yfinance as yf

from risk import size_position, stop_distance
import strategy
import analysis

warnings.filterwarnings('ignore')

IST = ZoneInfo('Asia/Kolkata')

def _env_float(name, default):
    try:    return float(os.environ.get(name, default))
    except ValueError: return default

# Override via workflow env / repo variables. Defaults are deliberately conservative.
CAPITAL        = _env_float('EDGE_CAPITAL', 565000)    # actual available INR equity
RISK_PCT       = _env_float('EDGE_RISK_PCT', 0.5) / 100
MAX_POS_PCT    = _env_float('EDGE_MAX_POS_PCT', 25) / 100     # per-position value cap
MAX_OPEN_RISK  = _env_float('EDGE_MAX_OPEN_RISK_PCT', 1.5) / 100  # across all signals
MIN_DATA_RATIO = 0.8    # fail the scan if fewer than 80% of symbols have usable data

# Corrected Yahoo Finance ticker symbols for NSE
NSE_STOCKS = [
    'RELIANCE','TCS','HDFCBANK','INFY','HINDUNILVR',
    'ICICIBANK','SBIN','BHARTIARTL','KOTAKBANK','LT',
    'AXISBANK','WIPRO','MARUTI','BAJFINANCE','HCLTECH',
    'ASIANPAINT','ULTRACEMCO','TITAN','SUNPHARMA','NESTLEIND',
    'TECHM','TATAMOTORS','INDUSINDBK','POWERGRID','NTPC',
    'BAJAJFINSV','ONGC','JSWSTEEL','TATASTEEL','COALINDIA',
    'ADANIENT','ADANIPORTS','CIPLA','DRREDDY','DIVISLAB',
    'BRITANNIA','EICHERMOT','GRASIM','HEROMOTOCO','ITC',
    'M&M','BPCL','IOC','TATACONSUM','APOLLOHOSP',
    'BAJAJ-AUTO','UPL','SBILIFE','HDFCLIFE','HINDALCO',
    'DMART','SIEMENS','HAVELLS','PIDILITIND','DABUR',
    'MARICO','COLPAL','BERGEPAINT','GODREJCP','MUTHOOTFIN',
    'LUPIN','BIOCON','TORNTPHARM','ALKEM','AUROPHARMA',
    'GLENMARK','AMBUJACEM','ACC','SHREECEM','INDIGO',
    'TATAPOWER','TRENT','NAUKRI','IRCTC','CONCOR',
    'SAIL','NMDC','VEDL','GAIL','PETRONET',
    'IGL','BANKBARODA','PNB','CANBK','FEDERALBNK',
    'IDFCFIRSTB','RBLBANK','AUBANK','CHOLAFIN','LICHSGFIN',
    'MANAPPURAM','SUNDARMFIN','SHRIRAMFIN','PIIND','PERSISTENT',
    'COFORGE','MPHASIS','LTTS','KPITTECH','TATAELXSI',
    'CYIENT','DEEPAKNTR','NAVINFLUOR','TATACHEM','APOLLOTYRE',
    'BALKRISIND','CEATLTD','MRF','MOTHERSON','BHARATFORG',
    'BOSCHLTD','VOLTAS','KAJARIACER','SUPREMEIND','ASTRAL',
    'POLYCAB','KEI','PAGEIND','RADICO','LAURUSLABS',
    'GRANULES','AJANTPHARM','ERIS','METROPOLIS','MAXHEALTH',
    'FORTIS','NH','SYNGENE','BRIGADE','SOBHA',
    'PRESTIGE','GODREJPROP','PHOENIXLTD','OBEROIRLTY','THERMAX',
    'CUMMINSIND','EMAMILTD','BEL','HAL','IRFC',
    'RVNL','PFC','RECLTD','SJVN','NHPC',       # REC.NS → RECLTD.NS
    'SUZLON','TRIDENT','RAYMOND','COROMANDEL','CHAMBLFERT',
    'RALLIS','DHANUKA','ATUL','NOCIL','APLAPOLLO',
    'ZOMATO','AARTIIND','TVSMOTOR','PRAJIND',   # Fixed tickers
    'GUJARATGAS',
]
NSE_STOCKS = list(dict.fromkeys(NSE_STOCKS))
YF_TICKERS = [f"{s}.NS" for s in NSE_STOCKS]
BENCH = '^NSEI'


def load_stockedge():
    """
    Load StockEdge CSV.
    File format: rows 1-5 are headers/metadata, row 6 is column headers,
    data starts row 7. Symbol is in column B (index 1).
    """
    se    = set()
    files = (glob.glob('stockedge*.csv') +
             glob.glob('StockEdge*.csv') +
             glob.glob('Swing*.csv'))

    if not files:
        print("No StockEdge CSV found. Upload stockedge.csv for HIGH CONVICTION labels.")
        return se

    try:
        # Skip first 5 rows, row 6 becomes header
        df = pd.read_csv(files[0], skiprows=5, header=0)
        print(f"StockEdge columns: {list(df.columns[:5])}")

        # Symbol column — try 'Symbol' first, fallback to column index 1
        if 'Symbol' in df.columns:
            col = 'Symbol'
        elif 'symbol' in df.columns:
            col = 'symbol'
        else:
            col = df.columns[1]  # Column B = index 1

        se = set(df[col].dropna().astype(str).str.strip().str.upper())
        print(f"StockEdge loaded: {len(se)} stocks")
        print(f"Sample: {list(se)[:5]}")

    except Exception as e:
        print(f"StockEdge error: {e}")

    return se


def fetch_bulk():
    print(f"Downloading {len(YF_TICKERS)} stocks in bulk...")
    for attempt in range(3):
        try:
            data = yf.download(
                tickers=YF_TICKERS + [BENCH],
                period='1y',
                interval='1d',
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=True,
                timeout=60,
            )
            if data is not None and not data.empty:
                print(f"Downloaded: {data.shape}")
                return data
            time.sleep(5)
        except Exception as e:
            print(f"Attempt {attempt+1}: {e}")
            time.sleep(5)
    return None


def extract_df(data, ticker):
    try:
        if ticker in data.columns.get_level_values(0):
            df = data[ticker].copy()
        else:
            df = data.xs(ticker, axis=1, level=0).copy()
        df = df[['Open','High','Low','Close','Volume']].dropna(subset=['Close'])
        df['Volume'] = df['Volume'].fillna(0)
        return df.sort_index() if len(df) >= 50 else None
    except:
        return None


def compute_atr(h, l, c, p=14):
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(p).mean()


def compute_supertrend(h, l, c, p=10, m=3):
    atr = compute_atr(h, l, c, p)
    hl2 = (h+l)/2
    up  = hl2 + m*atr
    dn  = hl2 - m*atr
    st  = [np.nan]*len(c)
    d   = [1]*len(c)
    for i in range(1, len(c)):
        fu = up.iloc[i] if up.iloc[i]<up.iloc[i-1] or c.iloc[i-1]>up.iloc[i-1] else up.iloc[i-1]
        fl = dn.iloc[i] if dn.iloc[i]>dn.iloc[i-1] or c.iloc[i-1]<dn.iloc[i-1] else dn.iloc[i-1]
        if   c.iloc[i]>fu: d[i]=1;  st[i]=fl
        elif c.iloc[i]<fl: d[i]=-1; st[i]=fu
        else: d[i]=d[i-1]; st[i]=fl if d[i]==1 else fu
    return pd.Series(st,index=c.index), pd.Series(d,index=c.index)


def compute_rsi(c, p=14):
    delta=c.diff()
    g=delta.where(delta>0,0.0).ewm(com=p-1,adjust=False).mean()
    l=(-delta.where(delta<0,0.0)).ewm(com=p-1,adjust=False).mean()
    return 100-(100/(1+g/l))


def indicators(df):
    c=df['Close'].astype(float)
    h=df['High'].astype(float)
    l=df['Low'].astype(float)
    v=df['Volume'].astype(float)
    e20=c.ewm(span=20,adjust=False).mean()
    e50=c.ewm(span=50,adjust=False).mean()
    e200=c.ewm(span=200,adjust=False).mean()
    def sl(s,n): v=s.iloc[-n]; return (s.iloc[-1]-v)/v*100 if v else 0
    rsi=compute_rsi(c)
    st,sd=compute_supertrend(h,l,c)
    n=len(v)
    v10=v.iloc[max(0,n-11):n-1].mean() if n>11 else v.mean()
    v5 =v.iloc[max(0,n-6):n-1].mean()  if n>6  else v.mean()
    cv =v.iloc[-1]
    p=c.iloc[-1]; e20v=e20.iloc[-1]; e50v=e50.iloc[-1]; e200v=e200.iloc[-1]
    h52=h.tail(252).max(); l52=l.tail(252).min()
    atr=compute_atr(h,l,c).iloc[-1]
    return {
        'price':p,'ema_20':e20v,'ema_50':e50v,'ema_200':e200v,
        'ema20_slope':sl(e20,6),'ema50_slope':sl(e50,6),
        'ema200_slope':sl(e200,min(11,len(e200)-1)),
        'rsi':rsi.iloc[-1],'rsi_5ago':rsi.iloc[-6] if len(rsi)>6 else rsi.iloc[-1],
        'st_dir':int(sd.iloc[-1]) if not pd.isna(sd.iloc[-1]) else 0,
        'vol_ratio':cv/v10 if v10>0 else 1,'vol_5d':cv/v5 if v5>0 else 1,
        'ema20_dist':(p-e20v)/e20v*100 if e20v else 0,
        'from_52h':(p-h52)/h52*100 if h52 else 0,
        'atr':atr,'atr_pct':atr/p*100 if p else 0,
        'high':h.iloc[-1],'low':l.iloc[-1],
    }


def stage(ind):
    if (ind['price']>ind['ema_200'] and ind['ema200_slope']>0 and
        ind['ema_50']>ind['ema_200'] and ind['ema_20']>ind['ema_50']):
        return 3 if ind['rsi']>75 or ind['from_52h']>-2 else 2
    return 4 if ind['price']<ind['ema_200'] and ind['ema200_slope']<0 else 1


def setup(ind):
    d=ind['ema20_dist']; r=ind['rsi']
    if -2<=d<=4 and ind['rsi_5ago']>r and r<63: return 'PULLBACK_EMA20','Pullback to EMA20'
    d50=(ind['price']-ind['ema_50'])/ind['ema_50']*100
    if -2<=d50<=4 and r<58: return 'PULLBACK_EMA50','Pullback to EMA50'
    if 4<d<=9 and max(ind['vol_ratio'],ind['vol_5d'])>=1.3 and r>52: return 'BREAKOUT_CONT','Breakout continuation'
    if ind['atr_pct']<1.8 and -3<=d<=6: return 'COMPRESSION','Volatility compression'
    return 'TRENDING','Stage 2 momentum'


def score(ind, stg, stp):
    s,r=[],[]
    if stg==2: s.append(25); r.append("Stage 2 (+25)")
    pts={'PULLBACK_EMA20':20,'PULLBACK_EMA50':14,'COMPRESSION':12,'BREAKOUT_CONT':10,'TRENDING':6}
    p=pts.get(stp,0); s.append(p); r.append(f"{stp} (+{p})")
    rsi=ind['rsi']
    if   45<=rsi<=62: s.append(20); r.append(f"RSI {rsi:.0f} (+20)")
    elif 62<rsi<=70:  s.append(13); r.append(f"RSI {rsi:.0f} (+13)")
    elif 38<=rsi<45:  s.append(8);  r.append(f"RSI {rsi:.0f} (+8)")
    elif 70<rsi<=76:  s.append(4);  r.append(f"RSI {rsi:.0f} (+4)")
    vr=max(ind['vol_ratio'],ind['vol_5d'])
    if   vr>=1.8: s.append(20); r.append(f"Vol {vr:.1f}x (+20)")
    elif vr>=1.2: s.append(13); r.append(f"Vol {vr:.1f}x (+13)")
    elif vr>=0.7: s.append(7);  r.append(f"Vol {vr:.1f}x (+7)")
    else:         s.append(3);  r.append(f"Vol {vr:.1f}x (+3)")
    sl=sum([ind['ema20_slope']>0,ind['ema50_slope']>0,ind['ema200_slope']>0])
    if sl==3: s.append(15); r.append("All EMAs rising (+15)")
    elif sl==2: s.append(10); r.append("2 EMAs rising (+10)")
    else: s.append(3); r.append("1 EMA rising (+3)")
    if -18<=ind['from_52h']<=-3: s.append(3); r.append("Near 52W high (+3)")
    if ind['st_dir']==1: s.append(3); r.append("Supertrend bullish (+3)")
    return min(sum(s),100), r


def filters(ind, stg):
    if stg!=2:         return False,f"Stage {stg}"
    if ind['st_dir']!=1: return False,"Supertrend bearish"
    if not(33<ind['rsi']<80): return False,f"RSI {ind['rsi']:.0f}"
    if ind['price']<ind['ema_50']*0.95: return False,"Below EMA50"
    if ind['price']<20: return False,"Price<20"
    return True,"OK"


def evaluate(df, in_se=False):
    """Run the live strategy on one symbol's history. Returns (record, None) for a signal or
    (None, reason_key) otherwise. This is the same rule backtest.base_signals() replays
    (tests/test_screener_backtest_parity.py asserts they agree)."""
    ind = indicators(df)
    stg = stage(ind)
    ok, reason = filters(ind, stg)
    if not ok:
        k = ('stage' if 'Stage' in reason else 'st' if 'Super' in reason
             else 'rsi' if 'RSI' in reason else 'price')
        return None, k
    stp, sdsc = setup(ind)
    sc_, rsns = score(ind, stg, stp)
    if sc_ < strategy.MIN_SCORE:
        return None, 'score'
    price = float(ind['price'])
    sd = stop_distance(price, ind['atr'])
    trigger, stop = round(float(ind['high']), 2), round(price - sd, 2)
    feat = analysis.day_features(df, ind)
    feat.update({
        'stop_pct': round((trigger - stop) / trigger * 100, 2) if trigger > 0 else 99.0,
        'trigger_gap_pct': round((trigger - price) / price * 100, 2),
        'ema_dist_pct': float(ind['ema20_dist']),
        'vol_ratio': float(max(ind['vol_ratio'], ind['vol_5d'])),
    })
    checks = analysis.build_checks(feat)
    return {
        'avg_value_cr': feat['avg_value_cr'], 'close_in_range': feat['close_in_range'],
        'stop_pct': feat['stop_pct'], 'trigger_gap_pct': feat['trigger_gap_pct'],
        'checks': checks, 'execution_ok': analysis.execution_ok(checks), 'spark': analysis.sparkline(df),
        'symbol': None, 'decision': 'SIGNAL', 'score': sc_, 'stage': stg,
        'setup_type': stp, 'setup_desc': sdsc, 'in_stockedge': in_se,
        'signal_date': str(df.index[-1].date()),
        'price': round(price, 2), 'trigger': round(float(ind['high']), 2),
        'stop_loss': round(price - sd, 2), 'plan_risk': round(sd, 4),
        'ema_20': round(ind['ema_20'], 2), 'ema_50': round(ind['ema_50'], 2), 'ema_200': round(ind['ema_200'], 2),
        'rsi': round(ind['rsi'], 2),
        'vol_ratio': round(max(ind['vol_ratio'], ind['vol_5d']), 2),
        'vol_5d_ratio': round(ind['vol_5d'], 2),
        'ema_dist_pct': round(ind['ema20_dist'], 2), 'from_52w_high': round(ind['from_52h'], 2),
        'atr_pct': round(ind['atr_pct'], 2), 'st_direction': ind['st_dir'],
        'atr': round(ind['atr'], 2), 'reasons': rsns, 'position': None,
    }, None


def position(rec, open_risk=0.0):
    """Size from the buy-stop price to the stop (the risk actually taken if the stop-buy fills)."""
    trigger, stop = rec['trigger'], rec['stop_loss']
    if trigger <= stop:
        return None
    p = size_position(CAPITAL, RISK_PCT, trigger, trigger - stop, MAX_POS_PCT)
    return {
        'shares': p['shares'], 'invested': p['invested'], 'stop_loss': stop, 'risk_amount': p['risk_amount'],
        'risk_pct_of_capital': round(p['risk_amount'] / CAPITAL * 100, 3), 'note': p['note'],
        'within_risk_budget': bool(p['shares'] > 0 and open_risk + p['risk_amount'] <= CAPITAL * MAX_OPEN_RISK),
    }


def arbitrary_order(scan_date, symbol):
    """No ranking exists (the score does not predict R), so use a deterministic pseudo-random order."""
    return hashlib.sha1(f'{scan_date}|{symbol}'.encode()).hexdigest()


def main():
    print("\n" + "=" * 70)
    print(f"EDGE PROTOCOL — {strategy.NAME}")
    print(f"Capital: Rs{CAPITAL:,.0f} | Risk/trade {RISK_PCT:.2%} | Pos cap {MAX_POS_PCT:.0%} | "
          f"Open-risk cap {MAX_OPEN_RISK:.2%} | Universe: {len(NSE_STOCKS)}")
    print(f"Scan: {datetime.now(IST).strftime('%A %Y-%m-%d %H:%M:%S')} IST")
    print("=" * 70 + "\n")

    se = load_stockedge()
    bulk = fetch_bulk()

    if bulk is None or bulk.empty:
        # Leave results.json untouched so the dashboard keeps the last good scan,
        # and exit non-zero so the workflow run shows as failed.
        print("FATAL: Data download failed. Keeping previous results.json.")
        sys.exit(1)

    now_utc = datetime.now(timezone.utc)
    last_bars = []
    results = []; stats = {'data': 0, 'stage': 0, 'st': 0, 'rsi': 0, 'price': 0, 'score': 0}
    missing = []

    print(f"\n{'Symbol':<14}{'Setup':<20}{'Close':>10}{'Buy>':>10}{'Stop':>10}")
    print("-" * 70)
    for sym, tick in zip(NSE_STOCKS, YF_TICKERS):
        try:
            df = extract_df(bulk, tick)
            if df is None:
                stats['data'] += 1; missing.append(sym); continue
            last_bars.append(df.index[-1])
            rec, why = evaluate(df, sym in se)
            if rec is None:
                stats[why] += 1; continue
            rec['symbol'] = sym
            rec['timestamp'] = now_utc.isoformat()
            results.append(rec)
            print(f"{sym:<14}{rec['setup_type']:<20}{rec['price']:>10.2f}{rec['trigger']:>10.2f}{rec['stop_loss']:>10.2f}")
        except Exception as e:
            print(f"{sym}: {str(e)[:50]}")

    processed = len(NSE_STOCKS) - stats['data']
    if processed < MIN_DATA_RATIO * len(NSE_STOCKS) or not last_bars:
        print(f"FATAL: only {processed}/{len(NSE_STOCKS)} symbols had usable data. Keeping previous results.json.")
        sys.exit(1)

    data_cutoff = max(last_bars).strftime('%Y-%m-%d')
    if missing:
        print(f"No usable data for {len(missing)} symbols: {', '.join(missing)}")
    try:
        nifty = extract_df(bulk, BENCH)
        nifty_close = nifty['Close'] if nifty is not None else None
    except Exception:
        nifty_close = None
    results.sort(key=lambda r: arbitrary_order(data_cutoff, r['symbol']))
    open_risk = 0.0
    for r in results:
        r['position'] = position(r, open_risk)
        if r['position'] and r['position']['within_risk_budget']:
            open_risk += r['position']['risk_amount']

    print("\n" + "=" * 70)
    print(f"DONE | Signals: {len(results)} | Filtered -> Stage:{stats['stage']} ST:{stats['st']} RSI:{stats['rsi']} "
          f"Price:{stats['price']} Score<{strategy.MIN_SCORE}:{stats['score']} Data:{stats['data']}")
    print("=" * 70)

    now_ist = now_utc.astimezone(IST)
    expected = analysis.expected_last_session(now_ist)
    behind = analysis.sessions_behind(max(last_bars).date(), expected)
    out = {
        'scan_id':           uuid.uuid4().hex[:12],
        'timestamp':         now_utc.isoformat(),           # UTC, machine-readable
        'scan_date':         now_ist.strftime('%Y-%m-%d'),  # IST, display
        'scan_time':         now_ist.strftime('%H:%M:%S') + ' IST',
        'data_cutoff':       data_cutoff,
        'expected_session':  str(expected),
        'sessions_behind':   behind,
        'missing_symbols':   missing,
        'symbols_processed': processed,
        'total_scanned':     len(NSE_STOCKS),
        'total_passed':      len(results),
        'capital':           CAPITAL,
        'strategy':          strategy.describe(),
        'risk_config': {
            'capital': CAPITAL, 'risk_pct': RISK_PCT * 100,
            'max_pos_pct': MAX_POS_PCT * 100, 'max_open_risk_pct': MAX_OPEN_RISK * 100,
        },
        'summary':           {'signals': len(results), 'tradeable': sum(1 for r in results if r['execution_ok'])},
        'market':            analysis.market_context(nifty_close, processed - stats['stage'], processed, len(results)),
        'stocks':            results,
    }
    # write-then-rename so a crash never leaves a half-written results.json
    with open('results.json.tmp', 'w') as f:
        json.dump(out, f, indent=2)
    os.replace('results.json.tmp', 'results.json')
    print(f"Saved {len(results)} signals. Data cutoff {data_cutoff}.")


if __name__ == '__main__':
    main()
