#!/usr/bin/env python3
"""
EDGE PROTOCOL - NSE Stock Screener
Automated swing trading scanner with EMA, RSI, Volume, Supertrend filters
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta
import traceback

# NSE stock list — customize as needed
NSE_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
    'ICICIBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'LANDT.NS', 'MARUTI.NS',
    'BAJAJ-AUTO.NS', 'ASIANPAINT.NS', 'DMART.NS', 'WIPRO.NS', 'TECHM.NS',
    'SUNPHARMA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'COALINDIA.NS', 'NTPC.NS',
    'POWERGRID.NS', 'GAIL.NS', 'IOC.NS', 'BPCL.NS', 'JSWSTEEL.NS',
    'BAJAJFINSV.NS', 'BHEL.NS', 'BOSCHIND.NS', 'BRITANNIA.NS', 'CADILAHC.NS',
    'CIPLA.NS', 'COLPAL.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HDFC.NS',
    'HEROMOTOCO.NS', 'HONAUT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LT.NS',
    'LTTS.NS', 'M&M.NS', 'MAXHEALTH.NS', 'MRF.NS', 'NESTLEIND.NS',
    'NMDC.NS', 'ONGC.NS', 'PAGEIND.NS', 'PEL.NS', 'PIIND.NS',
    'SBICARD.NS', 'SBILIFE.NS', 'SIEMENS.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS',
    'TATASTEEL.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'UNITDSPR.NS', 'UPL.NS',
    'VGUARD.NS', 'VOLTAS.NS', 'WHIRLPOOL.NS', 'YESBANK.NS', 'ZEEL.NS'
]

def calculate_indicators(hist):
    """
    Calculate technical indicators from OHLCV data.
    Returns dict with EMA, RSI, Supertrend, volume metrics.
    """
    close = hist['Close']
    high = hist['High']
    low = hist['Low']
    volume = hist['Volume']
    
    # EMA Calculation
    ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema_200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
    
    # RSI(14) Calculation
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]
    
    # Supertrend(10, 3) — Simplified ATR-based calculation
    hl_avg = (high + low) / 2.0
    hl_std = (high - low).rolling(window=10).std()
    supertrend = hl_avg.iloc[-1] + (3 * hl_std.iloc[-1])
    
    # Volume metrics
    avg_vol_20 = volume.tail(20).mean()
    curr_vol = volume.iloc[-1]
    
    # Current price
    curr_price = close.iloc[-1]
    
    return {
        'ema_20': ema_20,
        'ema_50': ema_50,
        'ema_200': ema_200,
        'rsi': rsi_val,
        'supertrend': supertrend,
        'price': curr_price,
        'volume': curr_vol,
        'avg_volume_20': avg_vol_20,
        'high': high.iloc[-1],
        'low': low.iloc[-1]
    }

def apply_filters(ind):
    """
    Apply EDGE PROTOCOL filters.
    
    Filters:
    - EMA(20) > EMA(50) > EMA(200) : Trend confirmation
    - RSI(14) between 50-75 : Momentum filter
    - Price > Supertrend(10,3) : Trend follow
    - Volume > 1.5x EMA(20 vol) : Volume surge
    - Price > 0.85 : Penny stock exclusion
    """
    ema_ok = (ind['ema_20'] > ind['ema_50']) and (ind['ema_50'] > ind['ema_200'])
    rsi_ok = (50 < ind['rsi'] < 75)
    trend_ok = ind['price'] > ind['supertrend']
    volume_ok = ind['volume'] > (ind['avg_volume_20'] * 1.5)
    price_ok = ind['price'] > 0.85
    
    return all([ema_ok, rsi_ok, trend_ok, volume_ok, price_ok])

def screen_stocks():
    """
    Main screening function.
    Iterates through all NSE stocks, calculates indicators, applies filters.
    Returns list of matching stocks.
    """
    results = []
    processed = 0
    errors = 0
    
    for ticker in NSE_STOCKS:
        try:
            processed += 1
            print(f"[{processed}/{len(NSE_STOCKS)}] Screening {ticker}...", end=' ', flush=True)
            
            # Fetch historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period='60d')
            
            # Skip if insufficient data
            if len(hist) < 20:
                print("⚠ Insufficient data")
                continue
            
            # Calculate indicators
            ind = calculate_indicators(hist)
            
            # Apply filters
            if apply_filters(ind):
                result = {
                    'symbol': ticker.replace('.NS', ''),
                    'price': round(ind['price'], 2),
                    'ema_20': round(ind['ema_20'], 2),
                    'ema_50': round(ind['ema_50'], 2),
                    'ema_200': round(ind['ema_200'], 2),
                    'rsi': round(ind['rsi'], 2),
                    'supertrend': round(ind['supertrend'], 2),
                    'high': round(ind['high'], 2),
                    'low': round(ind['low'], 2),
                    'volume': int(ind['volume']),
                    'avg_volume': int(ind['avg_volume_20'])
                }
                results.append(result)
                print("✅ MATCH")
            else:
                print("❌ Filtered out")
        
        except Exception as e:
            errors += 1
            print(f"❌ Error: {str(e)}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Processed: {processed} | Matched: {len(results)} | Errors: {errors}")
    print(f"{'='*60}\n")
    
    return results

def save_results(results):
    """
    Save screening results to results.json.
    Includes timestamp, count, and detailed stock data.
    """
    output = {
        'timestamp': datetime.now().isoformat(),
        'scan_date': datetime.now().strftime('%Y-%m-%d'),
        'scan_time': datetime.now().strftime('%H:%M:%S'),
        'count': len(results),
        'filters': {
            'ema_trend': 'EMA(20) > EMA(50) > EMA(200)',
            'rsi_range': '50 < RSI(14) < 75',
            'supertrend': 'Price > Supertrend(10,3)',
            'volume': 'Volume > 1.5x MA(20)',
            'price_floor': 'Price > 0.85'
        },
        'stocks': results
    }
    
    with open('results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Results saved to results.json ({len(results)} stocks)")
    return output

def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("EDGE PROTOCOL - NSE Stock Screener")
    print(f"Scan started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    try:
        results = screen_stocks()
        output = save_results(results)
        
        print("\n" + "="*60)
        print("📊 EDGE PROTOCOL Scan Complete")
        print(f"Found {output['count']} stocks matching criteria")
        print("="*60 + "\n")
        
        return output
    
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print(traceback.format_exc())
        return None

if __name__ == '__main__':
    main()
