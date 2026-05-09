#!/usr/bin/env python3
"""
EDGE PROTOCOL v2.0 — NSE Swing Trading Decision System
=======================================================
- Scans 325 NSE stocks (Nifty 500 universe)
- Scores each stock 0-100 on setup quality
- Cross-validates with StockEdge CSV
- Outputs GO / WATCH / NO-GO with entry, stop, position size
- Capital: Rs 5L - 10L range
"""

import yfinance as yf
import pandas as pd
import json
import os
import glob
from datetime import datetime
import traceback

# CAPITAL CONFIG
CAPITAL_MIN = 500000
CAPITAL_MAX = 1000000
CAPITAL = (CAPITAL_MIN + CAPITAL_MAX) / 2   # Rs 7.5L working capital

RISK_PCT_HIGH_CONVICTION = 0.02   # 2% risk per HIGH CONVICTION trade
RISK_PCT_STANDARD        = 0.01   # 1% risk per STANDARD trade
MAX_POSITIONS            = 5

NSE_STOCKS = [
    'RELIANCE.NS','TCS.NS','HDFCBANK.NS','INFY.NS','HINDUNILVR.NS',
    'ICICIBANK.NS','SBIN.NS','BHARTIARTL.NS','KOTAKBANK.NS','LT.NS',
    'AXISBANK.NS','WIPRO.NS','MARUTI.NS','BAJFINANCE.NS','HCLTECH.NS',
    'ASIANPAINT.NS','ULTRACEMCO.NS','TITAN.NS','SUNPHARMA.NS','NESTLEIND.NS',
    'TECHM.NS','TATAMOTORS.NS','INDUSINDBK.NS','POWERGRID.NS','NTPC.NS',
    'BAJAJFINSV.NS','ONGC.NS','JSWSTEEL.NS','TATASTEEL.NS','COALINDIA.NS',
    'ADANIENT.NS','ADANIPORTS.NS','CIPLA.NS','DRREDDY.NS','DIVISLAB.NS',
    'BRITANNIA.NS','EICHERMOT.NS','GRASIM.NS','HEROMOTOCO.NS','ITC.NS',
    'M&M.NS','BPCL.NS','IOC.NS','TATACONSUM.NS','APOLLOHOSP.NS',
    'BAJAJ-AUTO.NS','UPL.NS','SBILIFE.NS','HDFCLIFE.NS','HINDALCO.NS',
    'DMART.NS','SIEMENS.NS','HAVELLS.NS','PIDILITIND.NS','DABUR.NS',
    'MARICO.NS','COLPAL.NS','BERGEPAINT.NS','GODREJCP.NS','MUTHOOTFIN.NS',
    'LUPIN.NS','BIOCON.NS','TORNTPHARM.NS','ALKEM.NS','AUROPHARMA.NS',
    'GLENMARK.NS','IPCALAB.NS','ABBOTINDIA.NS','AMBUJACEM.NS','ACC.NS',
    'SHREECEM.NS','RAMCOCEM.NS','JKCEMENT.NS','INDIGO.NS','TATAPOWER.NS',
    'TRENT.NS','NAUKRI.NS','IRCTC.NS','CONCOR.NS','SAIL.NS',
    'NMDC.NS','VEDL.NS','HINDZINC.NS','GAIL.NS','PETRONET.NS',
    'GUJARATGAS.NS','IGL.NS','MGL.NS','ZOMATO.NS','NYKAA.NS',
    'BANKBARODA.NS','PNB.NS','CANBK.NS','UNIONBANK.NS','FEDERALBNK.NS',
    'IDFCFIRSTB.NS','RBLBANK.NS','BANDHANBNK.NS','AUBANK.NS','CHOLAFIN.NS',
    'LICHSGFIN.NS','PNBHOUSING.NS','CANFINHOME.NS','MANAPPURAM.NS','M&MFIN.NS',
    'SUNDARMFIN.NS','SHRIRAMFIN.NS','PIIND.NS','PERSISTENT.NS','COFORGE.NS',
    'MPHASIS.NS','LTTS.NS','KPITTECH.NS','TATAELXSI.NS','CYIENT.NS',
    'DEEPAKNTR.NS','AARTI.NS','NAVINFLUOR.NS','TATACHEM.NS','GNFC.NS',
    'APOLLOTYRE.NS','BALKRISIND.NS','CEATLTD.NS','MRF.NS','TVSMOTORS.NS',
    'MOTHERSON.NS','BHARATFORG.NS','BOSCHLTD.NS','TIINDIA.NS','SCHAEFFLER.NS',
    'VOLTAS.NS','BLUESTARCO.NS','KAJARIACER.NS','SUPREMEIND.NS','ASTRAL.NS',
    'POLYCAB.NS','KEI.NS','PAGEIND.NS','MCDOWELL-N.NS','RADICO.NS',
    'LAURUSLABS.NS','GRANULES.NS','AJANTPHARM.NS','NATCOPHARM.NS','ERIS.NS',
    'METROPOLIS.NS','MAXHEALTH.NS','FORTIS.NS','NH.NS','SYNGENE.NS',
    'BRIGADE.NS','SOBHA.NS','PRESTIGE.NS','GODREJPROP.NS','PHOENIXLTD.NS',
    'OBEROIRLTY.NS','TORNTPOWER.NS','THERMAX.NS','CUMMINSIND.NS','PRAJ.NS',
    'JYOTHYLAB.NS','EMAMILTD.NS','BATAINDIA.NS','TATACOMM.NS','BEL.NS',
    'HAL.NS','COCHINSHIP.NS','MAZAGON.NS','BHEL.NS','IRFC.NS',
    'RVNL.NS','RAILTEL.NS','PFC.NS','REC.NS','SJVN.NS','NHPC.NS',
    'INOXWIND.NS','SUZLON.NS','TRIDENT.NS','RAYMOND.NS','VARDHMAN.NS',
    'COROMANDEL.NS','CHAMBLFERT.NS','RALLIS.NS','DHANUKA.NS','ATUL.NS',
    'NOCIL.NS','ROSSARI.NS','VINATIORGA.NS','KANSAINER.NS','AKZOINDIA.NS',
    'APLAPOLLO.NS','RATNAMANI.NS','WELCORP.NS','GMRINFRA.NS','IRB.NS',
    'WELSPUNIND.NS','ARVIND.NS','KPRMILL.NS','LATENTVIEW.NS','INTELLECT.NS',
]

NSE_STOCKS = list(dict.fromkeys(NSE_STOCKS))


def load_stockedge():
    stockedge_symbols = set()
    csv_files = glob.glob('stockedge*.csv') + glob.glob('StockEdge*.csv') + glob.glob('STOCKEDGE*.csv')
    if not csv_files:
        print("WARNING: No StockEdge CSV found. Upload stockedge.csv to repo root.")
        print("Proceeding without StockEdge cross-validation.\n")
        return stockedge_symbols
    csv_file = csv_files[0]
    print(f"Loading StockEdge: {csv_file}")
    try:
        df = pd.read_csv(csv_file)
        possible_cols = ['Symbol','symbol','SYMBOL','Ticker','ticker','Stock','stock','NSE Code','NSE_Code','Name','name']
        symbol_col = None
        for col in possible_cols:
            if col in df.columns:
                symbol_col = col
                break
        if symbol_col is None:
            symbol_col = df.columns[0]
        symbols = df[symbol_col].dropna().astype(str).str.strip().str.upper().tolist()
        stockedge_symbols = set(symbols)
        print(f"StockEdge loaded: {len(stockedge_symbols)} stocks\n")
    except Exception as e:
        print(f"StockEdge load error: {e}\n")
    return stockedge_symbols


def calculate_indicators(hist):
    close  = hist['Close']
    high   = hist['High']
    low    = hist['Low']
    volume = hist['Volume']

    ema_20  = close.ewm(span=20,  adjust=False).mean()
    ema_50  = close.ewm(span=50,  adjust=False).mean()
    ema_200 = close.ewm(span=200, adjust=False).mean()

    ema_20_slope  = ema_20.iloc[-1]  - ema_20.iloc[-5]
    ema_50_slope  = ema_50.iloc[-1]  - ema_50.iloc[-5]
    ema_200_slope = ema_200.iloc[-1] - ema_200.iloc[-10]

    delta = close.diff()
    gain  = delta.where(delta > 0, 0).rolling(14).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs    = gain / loss
    rsi   = (100 - (100 / (1 + rs))).iloc[-1]

    hl_avg     = (high + low) / 2.0
    atr        = (high - low).rolling(10).mean()
    supertrend = (hl_avg + 3 * atr).iloc[-1]

    avg_vol_20 = volume.tail(20).mean()
    curr_vol   = volume.iloc[-1]
    vol_ratio  = curr_vol / avg_vol_20 if avg_vol_20 > 0 else 0

    curr_price    = close.iloc[-1]
    ema20_val     = ema_20.iloc[-1]
    ema20_dist    = ((curr_price - ema20_val) / ema20_val) * 100

    return {
        'price':         curr_price,
        'ema_20':        ema20_val,
        'ema_50':        ema_50.iloc[-1],
        'ema_200':       ema_200.iloc[-1],
        'ema_20_slope':  ema_20_slope,
        'ema_50_slope':  ema_50_slope,
        'ema_200_slope': ema_200_slope,
        'rsi':           rsi,
        'supertrend':    supertrend,
        'volume':        curr_vol,
        'avg_volume_20': avg_vol_20,
        'vol_ratio':     vol_ratio,
        'ema20_dist_pct':ema20_dist,
        'high':          high.iloc[-1],
        'low':           low.iloc[-1],
    }


def passes_base_filters(ind):
    return all([
        ind['ema_20'] > ind['ema_50'] > ind['ema_200'],
        50 < ind['rsi'] < 75,
        ind['price'] > ind['supertrend'],
        ind['vol_ratio'] > 1.5,
        ind['price'] > 0.85,
    ])


def calculate_score(ind):
    score   = 0
    reasons = []

    # A. EMA Proximity (30 pts)
    dist = ind['ema20_dist_pct']
    if 0 <= dist <= 2:
        score += 30; reasons.append("Tight to EMA20 (+30)")
    elif 2 < dist <= 5:
        score += 20; reasons.append("Near EMA20 (+20)")
    elif 5 < dist <= 8:
        score += 10; reasons.append("Slightly extended (+10)")
    else:
        reasons.append("Too extended from EMA20 (+0)")

    # B. RSI Quality (20 pts)
    rsi = ind['rsi']
    if 55 <= rsi <= 65:
        score += 20; reasons.append(f"RSI ideal {rsi:.1f} (+20)")
    elif 65 < rsi <= 72:
        score += 10; reasons.append(f"RSI strong {rsi:.1f} (+10)")
    elif 50 <= rsi < 55:
        score += 5;  reasons.append(f"RSI weak {rsi:.1f} (+5)")
    else:
        reasons.append(f"RSI poor {rsi:.1f} (+0)")

    # C. Volume Surge (25 pts)
    vr = ind['vol_ratio']
    if vr >= 2.5:
        score += 25; reasons.append(f"Volume {vr:.1f}x surge (+25)")
    elif vr >= 2.0:
        score += 20; reasons.append(f"Volume {vr:.1f}x strong (+20)")
    elif vr >= 1.5:
        score += 12; reasons.append(f"Volume {vr:.1f}x above avg (+12)")
    else:
        reasons.append("Volume low (+0)")

    # D. Trend Slope (25 pts)
    slopes = sum([
        ind['ema_20_slope']  > 0,
        ind['ema_50_slope']  > 0,
        ind['ema_200_slope'] > 0,
    ])
    if slopes == 3:
        score += 25; reasons.append("All EMAs rising (+25)")
    elif slopes == 2:
        score += 15; reasons.append("2 EMAs rising (+15)")
    elif slopes == 1:
        score += 5;  reasons.append("1 EMA rising (+5)")
    else:
        reasons.append("No EMA rising (+0)")

    return score, reasons


def get_decision(score, in_stockedge):
    if score >= 75 and in_stockedge:
        return 'HIGH_CONVICTION'
    elif score >= 75:
        return 'GO'
    elif score >= 50 and in_stockedge:
        return 'WATCH_CLOSELY'
    elif score >= 50:
        return 'WATCH'
    else:
        return 'NO_GO'


def calculate_position(price, decision):
    stop_loss = round(price * 0.97, 2)
    stop_dist = price - stop_loss
    if stop_dist <= 0:
        return None
    if decision == 'HIGH_CONVICTION':
        risk_amt = CAPITAL * RISK_PCT_HIGH_CONVICTION
    elif decision == 'GO':
        risk_amt = CAPITAL * RISK_PCT_STANDARD
    else:
        return None
    shares   = max(1, int(risk_amt / stop_dist))
    return {
        'shares':      shares,
        'invested':    round(shares * price, 2),
        'stop_loss':   stop_loss,
        'risk_amount': round(shares * stop_dist, 2),
        'target_1':    round(price * 1.06, 2),
        'target_2':    round(price * 1.10, 2),
        'rr_ratio':    '2:1',
    }


def screen_stocks(stockedge_symbols):
    results   = []
    processed = 0
    errors    = 0
    total     = len(NSE_STOCKS)

    print(f"Scanning {total} stocks...\n")

    for ticker in NSE_STOCKS:
        try:
            processed += 1
            symbol = ticker.replace('.NS', '')
            print(f"[{processed}/{total}] {symbol}", end=' ... ', flush=True)

            stock = yf.Ticker(ticker)
            hist  = stock.history(period='200d')

            if len(hist) < 50:
                print("Skipped (data)")
                continue

            ind = calculate_indicators(hist)

            if not passes_base_filters(ind):
                print("Filtered out")
                continue

            score, reasons = calculate_score(ind)
            in_stockedge   = symbol in stockedge_symbols
            decision       = get_decision(score, in_stockedge)
            position       = calculate_position(ind['price'], decision)

            results.append({
                'symbol':       symbol,
                'decision':     decision,
                'score':        score,
                'in_stockedge': in_stockedge,
                'price':        round(ind['price'], 2),
                'ema_20':       round(ind['ema_20'], 2),
                'ema_50':       round(ind['ema_50'], 2),
                'ema_200':      round(ind['ema_200'], 2),
                'rsi':          round(ind['rsi'], 2),
                'vol_ratio':    round(ind['vol_ratio'], 2),
                'ema_dist_pct': round(ind['ema20_dist_pct'], 2),
                'supertrend':   round(ind['supertrend'], 2),
                'reasons':      reasons,
                'position':     position,
                'timestamp':    datetime.now().isoformat(),
            })

            tag = {'HIGH_CONVICTION':'HC','GO':'GO','WATCH_CLOSELY':'WC','WATCH':'W','NO_GO':'NG'}.get(decision)
            se  = '[SE]' if in_stockedge else ''
            print(f"{tag} {se}| Score:{score}/100 RSI:{ind['rsi']:.1f}")

        except Exception as e:
            errors += 1
            print(f"Error: {e}")

    priority = {'HIGH_CONVICTION':0,'GO':1,'WATCH_CLOSELY':2,'WATCH':3,'NO_GO':4}
    results.sort(key=lambda x: (priority.get(x['decision'],9), -x['score']))

    hc = sum(1 for r in results if r['decision']=='HIGH_CONVICTION')
    go = sum(1 for r in results if r['decision']=='GO')
    wc = sum(1 for r in results if r['decision']=='WATCH_CLOSELY')
    w  = sum(1 for r in results if r['decision']=='WATCH')

    print(f"\n{'='*60}")
    print(f"Scanned:{processed} | Passed:{len(results)} | Errors:{errors}")
    print(f"HIGH CONVICTION:{hc} | GO:{go} | WATCH_CLOSELY:{wc} | WATCH:{w}")
    print(f"{'='*60}\n")
    return results


def save_results(results):
    hc = sum(1 for r in results if r['decision']=='HIGH_CONVICTION')
    go = sum(1 for r in results if r['decision']=='GO')
    wc = sum(1 for r in results if r['decision']=='WATCH_CLOSELY')
    w  = sum(1 for r in results if r['decision']=='WATCH')

    output = {
        'timestamp':    datetime.now().isoformat(),
        'scan_date':    datetime.now().strftime('%Y-%m-%d'),
        'scan_time':    datetime.now().strftime('%H:%M:%S'),
        'capital':      CAPITAL,
        'total_scanned':len(NSE_STOCKS),
        'total_passed': len(results),
        'summary': {
            'high_conviction': hc,
            'go':              go,
            'watch_closely':   wc,
            'watch':           w,
        },
        'stocks': results,
    }
    with open('results.json','w') as f:
        json.dump(output, f, indent=2)
    print(f"Saved {len(results)} results to results.json")
    return output


def main():
    print("\n" + "="*60)
    print("EDGE PROTOCOL v2.0 — NSE Swing Decision System")
    print(f"Capital: Rs{CAPITAL/100000:.1f}L | Max Positions: {MAX_POSITIONS}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    stockedge_symbols = load_stockedge()
    results = screen_stocks(stockedge_symbols)
    save_results(results)
    actionable = sum(1 for r in results if r['decision'] in ['HIGH_CONVICTION','GO'])
    print(f"Done. {actionable} actionable setups found.")

if __name__ == '__main__':
    main()
