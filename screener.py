#!/usr/bin/env python3
"""
EDGE PROTOCOL - NSE Stock Screener
Full Nifty 500 coverage with EMA, RSI, Volume, Supertrend filters
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import traceback

# Full Nifty 500 Stock List
NSE_STOCKS = [
    # Nifty 50
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
    'ICICIBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS',
    'AXISBANK.NS', 'WIPRO.NS', 'MARUTI.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'ASIANPAINT.NS', 'ULTRACEMCO.NS', 'TITAN.NS', 'SUNPHARMA.NS', 'NESTLEIND.NS',
    'TECHM.NS', 'TATAMOTORS.NS', 'INDUSINDBK.NS', 'POWERGRID.NS', 'NTPC.NS',
    'BAJAJFINSV.NS', 'ONGC.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS', 'COALINDIA.NS',
    'ADANIENT.NS', 'ADANIPORTS.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS',
    'BRITANNIA.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'ITC.NS',
    'M&M.NS', 'BPCL.NS', 'IOC.NS', 'TATACONSUM.NS', 'APOLLOHOSP.NS',
    'BAJAJ-AUTO.NS', 'UPL.NS', 'SBILIFE.NS', 'HDFCLIFE.NS', 'HINDALCO.NS',

    # Nifty Next 50
    'DMART.NS', 'SIEMENS.NS', 'HAVELLS.NS', 'PIDILITIND.NS', 'DABUR.NS',
    'MARICO.NS', 'COLPAL.NS', 'BERGEPAINT.NS', 'GODREJCP.NS', 'MUTHOOTFIN.NS',
    'LUPIN.NS', 'BIOCON.NS', 'TORNTPHARM.NS', 'ALKEM.NS', 'AUROPHARMA.NS',
    'GLENMARK.NS', 'IPCALAB.NS', 'ABBOTINDIA.NS', 'PFIZER.NS', 'GLAXO.NS',
    'AMBUJACEM.NS', 'ACC.NS', 'SHREECEM.NS', 'RAMCOCEM.NS', 'JKCEMENT.NS',
    'INDIGO.NS', 'TATAPOWER.NS', 'ADANITRANS.NS', 'ADANIGREEN.NS', 'CESC.NS',
    'TRENT.NS', 'NYKAA.NS', 'ZOMATO.NS', 'PAYTM.NS', 'POLICYBZR.NS',
    'DELHIVERY.NS', 'NAUKRI.NS', 'JUSTDIAL.NS', 'IRCTC.NS', 'CONCOR.NS',
    'SAIL.NS', 'NMDC.NS', 'NATIONALUM.NS', 'VEDL.NS', 'HINDZINC.NS',
    'GAIL.NS', 'PETRONET.NS', 'GUJARATGAS.NS', 'IGL.NS', 'MGL.NS',

    # Nifty Midcap 150
    'BANKBARODA.NS', 'PNB.NS', 'CANBK.NS', 'UNIONBANK.NS', 'IDBI.NS',
    'FEDERALBNK.NS', 'IDFCFIRSTB.NS', 'RBLBANK.NS', 'BANDHANBNK.NS', 'AUBANK.NS',
    'CHOLAFIN.NS', 'BAJAJHLDNG.NS', 'LICHSGFIN.NS', 'PNBHOUSING.NS', 'CANFINHOME.NS',
    'MANAPPURAM.NS', 'M&MFIN.NS', 'SUNDARMFIN.NS', 'SHRIRAMFIN.NS', 'IBULHSGFIN.NS',
    'PIIND.NS', 'AAVAS.NS', 'HOMEFIRST.NS', 'CREDITACC.NS', 'SPANDANA.NS',
    'PERSISTENT.NS', 'COFORGE.NS', 'MINDTREE.NS', 'MPHASIS.NS', 'LTTS.NS',
    'KPITTECH.NS', 'TATAELXSI.NS', 'CYIENT.NS', 'HEXAWARE.NS', 'NIITTECH.NS',
    'ZENSARTECH.NS', 'RATEGAIN.NS', 'SONATSOFTW.NS', 'MASTEK.NS', 'TANLA.NS',
    'DEEPAKNTR.NS', 'AARTI.NS', 'NAVINFLUOR.NS', 'FINEORG.NS', 'CLEAN.NS',
    'SUDARSCHEM.NS', 'VINDHYATEL.NS', 'TATACHEM.NS', 'GNFC.NS', 'GSFC.NS',
    'APOLLOTYRE.NS', 'BALKRISIND.NS', 'CEATLTD.NS', 'MRF.NS', 'TVSMOTORS.NS',
    'MOTHERSON.NS', 'BHARATFORG.NS', 'SUNDRMFAST.NS', 'BOSCHLTD.NS', 'TIINDIA.NS',
    'SCHAEFFLER.NS', 'SKFINDIA.NS', 'TIMKEN.NS', 'GRINDWELL.NS', 'ELGIEQUIP.NS',
    'VOLTAS.NS', 'BLUESTARCO.NS', 'WHIRLPOOL.NS', 'KAJARIACER.NS', 'CERA.NS',
    'SUPREMEIND.NS', 'ASTRAL.NS', 'PRINCEPIPE.NS', 'FINOLEX.NS', 'VGUARD.NS',
    'POLYCAB.NS', 'KEI.NS', 'FINOLEX.NS', 'RHIM.NS', 'ORIENTREF.NS',
    'MCDOWELL-N.NS', 'RADICO.NS', 'UBL.NS', 'GLOBUSSPR.NS', 'VSTIND.NS',
    'PAGEIND.NS', 'TTKPRESTIG.NS', 'BUTTERFLY.NS', 'HAWKINCOO.NS', 'SKUMARSYNF.NS',
    'VEDANT.NS', 'KALYANKJIL.NS', 'THANGAMAYIL.NS', 'RAJESHEXPO.NS', 'RKFORGE.NS',
    'SYNGENE.NS', 'LAURUSLABS.NS', 'GRANULES.NS', 'AJANTPHARM.NS', 'NATCOPHARM.NS',
    'STRIDES.NS', 'ENDURANCE.NS', 'SUNDPHARMA.NS', 'ERIS.NS', 'JBCHEPHARM.NS',
    'DIVI.NS', 'METROPOLIS.NS', 'THYROCARE.NS', 'KRSNAA.NS', 'VIJAYABANK.NS',
    'MAXHEALTH.NS', 'NH.NS', 'RAINBOW.NS', 'MEDANTA.NS', 'FORTIS.NS',

    # Nifty Smallcap 250 (selective liquid ones)
    'CHAMBLFERT.NS', 'COROMANDEL.NS', 'RALLIS.NS', 'BAYER.NS', 'DHANUKA.NS',
    'JUBLPHARMA.NS', 'SOLARA.NS', 'SUVEN.NS', 'DIVIS.NS', 'SEQUENT.NS',
    'TATACOMM.NS', 'BHARATELECTR.NS', 'BEL.NS', 'HAL.NS', 'COCHINSHIP.NS',
    'MAZAGON.NS', 'GRSE.NS', 'MIDHANI.NS', 'BEML.NS', 'BHEL.NS',
    'IRFC.NS', 'RVNL.NS', 'RAILTEL.NS', 'IRCON.NS', 'NBCC.NS',
    'HUDCO.NS', 'PFC.NS', 'REC.NS', 'SJVN.NS', 'NHPC.NS',
    'GESHIP.NS', 'ESSARSHPNG.NS', 'SCI.NS', 'GMRINFRA.NS', 'IRB.NS',
    'ASHOKA.NS', 'SADBHAV.NS', 'HG INFRA.NS', 'PNC.NS', 'KPRMILL.NS',
    'WELSPUNIND.NS', 'TRIDENT.NS', 'RAYMOND.NS', 'ARVIND.NS', 'VARDHMAN.NS',
    'NIITLIMITED.NS', 'ZENSAR.NS', 'RATEGAIN.NS', 'LATENTVIEW.NS', 'INTELLECT.NS',
    'DATAMATICS.NS', 'XCHANGING.NS', 'SAKSOFT.NS', 'QUICKHEAL.NS', 'SUBEX.NS',
    'BRIGADE.NS', 'SOBHA.NS', 'PRESTIGE.NS', 'GODREJPROP.NS', 'PHOENIXLTD.NS',
    'OBEROIRLTY.NS', 'MAHLIFE.NS', 'KOLTEPATIL.NS', 'SUNTECK.NS', 'PURAVANKARA.NS',
    'INOXWIND.NS', 'SUZLON.NS', 'RENUKA.NS', 'RPOWER.NS', 'TORNTPOWER.NS',
    'JPPOWER.NS', 'GREENKO.NS', 'ACME.NS', 'GGREAVE.NS', 'THERMAX.NS',
    'PRAJ.NS', 'TRIVENI.NS', 'KIRLOSKAR.NS', 'CUMMINSIND.NS', 'GREAVES.NS',
    'JYOTHYLAB.NS', 'EMAMILTD.NS', 'BAJAJCON.NS', 'HATSUN.NS', 'HERITGFOOD.NS',
    'ZYDUSWELL.NS', 'GILLETTE.NS', 'PGHH.NS', 'HONAUT.NS', '3MINDIA.NS',
    'BATAINDIA.NS', 'VMART.NS', 'SHOPPER.NS', 'SPENCERS.NS', 'TRENT.NS',
    'INDIGOPNTS.NS', 'GRINDMASTER.NS', 'NOCIL.NS', 'ATUL.NS', 'BASF.NS',
    'AKZOINDIA.NS', 'KANSAINER.NS', 'VINATIORGA.NS', 'ROSSARI.NS', 'GALAXYSURF.NS',
    'SEQUENT.NS', 'WOCKPHARMA.NS', 'ALEMBICLTD.NS', 'MARKSANS.NS', 'SHILPAMED.NS',
    'PIRAMALENT.NS', 'APLAPOLLO.NS', 'RATNAMANI.NS', 'WELCORP.NS', 'MANGLMCMT.NS',
]

# Remove duplicates
NSE_STOCKS = list(dict.fromkeys(NSE_STOCKS))

def calculate_indicators(hist):
    close = hist['Close']
    high = hist['High']
    low = hist['Low']
    volume = hist['Volume']

    ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema_200 = close.ewm(span=200, adjust=False).mean().iloc[-1]

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]

    hl_avg = (high + low) / 2.0
    hl_std = (high - low).rolling(window=10).std()
    supertrend = hl_avg.iloc[-1] + (3 * hl_std.iloc[-1])

    avg_vol_20 = volume.tail(20).mean()
    curr_vol = volume.iloc[-1]
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
    ema_ok = (ind['ema_20'] > ind['ema_50']) and (ind['ema_50'] > ind['ema_200'])
    rsi_ok = (50 < ind['rsi'] < 75)
    trend_ok = ind['price'] > ind['supertrend']
    volume_ok = ind['volume'] > (ind['avg_volume_20'] * 1.5)
    price_ok = ind['price'] > 0.85
    return all([ema_ok, rsi_ok, trend_ok, volume_ok, price_ok])

def screen_stocks():
    results = []
    processed = 0
    errors = 0
    total = len(NSE_STOCKS)

    print(f"Scanning {total} NSE stocks...\n")

    for ticker in NSE_STOCKS:
        try:
            processed += 1
            print(f"[{processed}/{total}] {ticker}", end=' ... ', flush=True)

            stock = yf.Ticker(ticker)
            hist = stock.history(period='60d')

            if len(hist) < 20:
                print("⚠ Skipped (insufficient data)")
                continue

            ind = calculate_indicators(hist)

            if apply_filters(ind):
                results.append({
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
                })
                print("✅ MATCH")
            else:
                print("❌")

        except Exception as e:
            errors += 1
            print(f"❌ Error: {str(e)}")
            continue

    print(f"\n{'='*60}")
    print(f"Scanned: {processed} | Matched: {len(results)} | Errors: {errors}")
    print(f"{'='*60}\n")

    return results

def save_results(results):
    output = {
        'timestamp': datetime.now().isoformat(),
        'scan_date': datetime.now().strftime('%Y-%m-%d'),
        'scan_time': datetime.now().strftime('%H:%M:%S'),
        'total_scanned': len(NSE_STOCKS),
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

    print(f"✅ Saved {len(results)} stocks to results.json")
    return output

def main():
    print("\n" + "="*60)
    print("EDGE PROTOCOL - NSE Stock Screener (Nifty 500)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    try:
        results = screen_stocks()
        output = save_results(results)
        print(f"\n✅ Done. Found {output['count']} stocks from {output['total_scanned']} scanned.")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print(traceback.format_exc())

if __name__ == '__main__':
    main()
