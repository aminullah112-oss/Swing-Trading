#!/usr/bin/env python3
"""
EDGE PROTOCOL v3.0 — Professional NSE Swing Trading System
============================================================
Philosophy: Find stocks in Stage 2 uptrend, pulling back to support,
with institutional volume confirmation. Works any day of the week.

30-year swing trading principles:
- Stage analysis (Weinstein methodology)
- Pullback to EMA, not breakout chasing
- Volume confirms institutional interest
- RSI reset from overbought = re-entry opportunity
- Trend must be intact on multiple timeframes
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
import glob
from datetime import datetime, timedelta
import traceback
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# CAPITAL CONFIG
# ─────────────────────────────────────────────
CAPITAL          = 750000   # Rs 7.5L midpoint
RISK_PCT_HC      = 0.02     # 2% risk — High Conviction
RISK_PCT_GO      = 0.01     # 1% risk — GO
MAX_POSITIONS    = 5

# ─────────────────────────────────────────────
# NSE UNIVERSE — Nifty 500 liquid stocks
# ─────────────────────────────────────────────
NSE_STOCKS = [
    # Nifty 50
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
    # Nifty Next 50
    'DMART.NS','SIEMENS.NS','HAVELLS.NS','PIDILITIND.NS','DABUR.NS',
    'MARICO.NS','COLPAL.NS','BERGEPAINT.NS','GODREJCP.NS','MUTHOOTFIN.NS',
    'LUPIN.NS','BIOCON.NS','TORNTPHARM.NS','ALKEM.NS','AUROPHARMA.NS',
    'GLENMARK.NS','IPCALAB.NS','ABBOTINDIA.NS','AMBUJACEM.NS','ACC.NS',
    'SHREECEM.NS','RAMCOCEM.NS','JKCEMENT.NS','INDIGO.NS','TATAPOWER.NS',
    'TRENT.NS','NAUKRI.NS','IRCTC.NS','CONCOR.NS','SAIL.NS',
    'NMDC.NS','VEDL.NS','HINDZINC.NS','GAIL.NS','PETRONET.NS',
    'GUJARATGAS.NS','IGL.NS','MGL.NS','ZOMATO.NS','NYKAA.NS',
    # Midcap
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


# ─────────────────────────────────────────────
# STOCKEDGE LOADER
# ─────────────────────────────────────────────
def load_stockedge():
    stockedge_symbols = set()
    csv_files = (glob.glob('stockedge*.csv') +
                 glob.glob('StockEdge*.csv') +
                 glob.glob('STOCKEDGE*.csv'))
    if not csv_files:
        print("INFO: No stockedge.csv found. Upload to repo for HIGH CONVICTION labels.")
        return stockedge_symbols
    try:
        df = pd.read_csv(csv_files[0])
        possible = ['Symbol','symbol','SYMBOL','Ticker','NSE Code','Stock','Name']
        col = next((c for c in possible if c in df.columns), df.columns[0])
        stockedge_symbols = set(
            df[col].dropna().astype(str).str.strip().str.upper().tolist()
        )
        print(f"StockEdge loaded: {len(stockedge_symbols)} stocks")
    except Exception as e:
        print(f"StockEdge error: {e}")
    return stockedge_symbols


# ─────────────────────────────────────────────
# CORE INDICATORS
# ─────────────────────────────────────────────
def compute_atr(high, low, close, period=14):
    """True Range based ATR."""
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_supertrend(high, low, close, period=10, multiplier=3):
    """
    Proper Supertrend(10,3) — switches direction based on price.
    Returns supertrend line and direction (1=bullish, -1=bearish).
    """
    atr    = compute_atr(high, low, close, period)
    hl2    = (high + low) / 2
    upper  = hl2 + multiplier * atr
    lower  = hl2 - multiplier * atr

    supertrend = pd.Series(index=close.index, dtype=float)
    direction  = pd.Series(index=close.index, dtype=int)

    for i in range(1, len(close)):
        # Final upper band
        if upper.iloc[i] < upper.iloc[i-1] or close.iloc[i-1] > upper.iloc[i-1]:
            final_upper = upper.iloc[i]
        else:
            final_upper = upper.iloc[i-1]

        # Final lower band
        if lower.iloc[i] > lower.iloc[i-1] or close.iloc[i-1] < lower.iloc[i-1]:
            final_lower = lower.iloc[i]
        else:
            final_lower = lower.iloc[i-1]

        # Direction
        if close.iloc[i] > final_upper:
            direction.iloc[i] = 1
            supertrend.iloc[i] = final_lower
        elif close.iloc[i] < final_lower:
            direction.iloc[i] = -1
            supertrend.iloc[i] = final_upper
        else:
            direction.iloc[i] = direction.iloc[i-1]
            supertrend.iloc[i] = (final_lower
                                  if direction.iloc[i] == 1
                                  else final_upper)

    return supertrend, direction


def compute_rsi(close, period=14):
    delta = close.diff()
    gain  = delta.where(delta > 0, 0.0).ewm(com=period-1, adjust=False).mean()
    loss  = (-delta.where(delta < 0, 0.0)).ewm(com=period-1, adjust=False).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def compute_indicators(hist):
    close  = hist['Close'].astype(float)
    high   = hist['High'].astype(float)
    low    = hist['Low'].astype(float)
    volume = hist['Volume'].astype(float)

    # EMAs
    ema_20  = close.ewm(span=20,  adjust=False).mean()
    ema_50  = close.ewm(span=50,  adjust=False).mean()
    ema_200 = close.ewm(span=200, adjust=False).mean()

    # EMA slopes — 5-day rate of change
    ema20_slope  = (ema_20.iloc[-1]  - ema_20.iloc[-6])  / ema_20.iloc[-6]  * 100
    ema50_slope  = (ema_50.iloc[-1]  - ema_50.iloc[-6])  / ema_50.iloc[-6]  * 100
    ema200_slope = (ema_200.iloc[-1] - ema_200.iloc[-11]) / ema_200.iloc[-11] * 100

    # RSI(14) — EMA-smoothed (Wilder method)
    rsi = compute_rsi(close, 14)

    # RSI 5-day ago (to detect pullback/reset)
    rsi_5d_ago = rsi.iloc[-6] if len(rsi) > 6 else rsi.iloc[-1]

    # Supertrend(10,3) — proper implementation
    st_line, st_dir = compute_supertrend(high, low, close, 10, 3)

    # Volume — use 10-day avg (more responsive than 20-day)
    # This works correctly on any day including Saturday
    vol_10d_avg = volume.iloc[-11:-1].mean()   # last 10 completed sessions
    curr_vol    = volume.iloc[-1]
    vol_ratio   = curr_vol / vol_10d_avg if vol_10d_avg > 0 else 0

    # 5-day avg volume (weekly rhythm)
    vol_5d_avg  = volume.iloc[-6:-1].mean()
    vol_5d_ratio = curr_vol / vol_5d_avg if vol_5d_avg > 0 else 0

    # Price metrics
    price        = close.iloc[-1]
    ema20_val    = ema_20.iloc[-1]
    ema50_val    = ema_50.iloc[-1]
    ema200_val   = ema_200.iloc[-1]

    # Distance from EMA20 (%)
    ema20_dist   = (price - ema20_val) / ema20_val * 100

    # 52-week high/low
    high_52w     = high.tail(252).max()
    low_52w      = low.tail(252).min()
    from_52w_high = (price - high_52w) / high_52w * 100   # negative = below high
    from_52w_low  = (price - low_52w)  / low_52w  * 100   # positive = above low

    # ATR for volatility
    atr_val = compute_atr(high, low, close, 14).iloc[-1]
    atr_pct = atr_val / price * 100

    # Highest volume day in last 20 sessions (institutional activity marker)
    vol_20d_max = volume.tail(20).max()
    is_high_vol_day = curr_vol >= (vol_20d_max * 0.8)  # within 80% of 20d max

    # Consecutive green days
    last_5_closes = close.tail(6)
    consec_green  = sum(1 for i in range(1, len(last_5_closes))
                        if last_5_closes.iloc[i] > last_5_closes.iloc[i-1])

    return {
        'price':          price,
        'ema_20':         ema20_val,
        'ema_50':         ema50_val,
        'ema_200':        ema200_val,
        'ema20_slope':    ema20_slope,
        'ema50_slope':    ema50_slope,
        'ema200_slope':   ema200_slope,
        'rsi':            rsi.iloc[-1],
        'rsi_5d_ago':     rsi_5d_ago,
        'supertrend':     st_line.iloc[-1],
        'st_direction':   st_dir.iloc[-1],
        'volume':         curr_vol,
        'vol_10d_avg':    vol_10d_avg,
        'vol_ratio':      vol_ratio,
        'vol_5d_ratio':   vol_5d_ratio,
        'is_high_vol_day':is_high_vol_day,
        'ema20_dist':     ema20_dist,
        'high_52w':       high_52w,
        'low_52w':        low_52w,
        'from_52w_high':  from_52w_high,
        'from_52w_low':   from_52w_low,
        'atr_val':        atr_val,
        'atr_pct':        atr_pct,
        'consec_green':   consec_green,
        'high':           high.iloc[-1],
        'low':            low.iloc[-1],
    }


# ─────────────────────────────────────────────
# STAGE ANALYSIS (Weinstein)
# ─────────────────────────────────────────────
def get_stage(ind):
    """
    Stage 1: Basing — price flat, EMA200 flat
    Stage 2: Uptrend — price > EMA200, EMA200 rising  ← We want this
    Stage 3: Topping — price extended, momentum fading
    Stage 4: Downtrend — price < EMA200
    """
    price       = ind['price']
    ema200      = ind['ema_200']
    ema50       = ind['ema_50']
    ema20       = ind['ema_20']
    ema200_slope = ind['ema200_slope']
    ema50_slope  = ind['ema50_slope']
    ema20_slope  = ind['ema20_slope']

    if (price > ema200 and
        ema200_slope > 0 and
        ema50 > ema200 and
        ema20 > ema50):
        if ind['rsi'] > 70 or ind['from_52w_high'] > -5:
            return 3   # Topping / Extended
        return 2       # Stage 2 uptrend ✅

    if price < ema200 and ema200_slope < 0:
        return 4       # Downtrend

    if abs(ema200_slope) < 0.1:
        return 1       # Basing

    return 0           # Unclear


# ─────────────────────────────────────────────
# SETUP TYPE DETECTION
# ─────────────────────────────────────────────
def get_setup_type(ind):
    """
    Identify the specific swing setup:
    - Pullback to EMA20 (best setup — institutional re-entry)
    - Pullback to EMA50 (deeper pullback, still valid)
    - Breakout continuation (price just broke above resistance)
    - Range compression (low volatility coiling before move)
    """
    dist20 = ind['ema20_dist']
    rsi    = ind['rsi']
    rsi5   = ind['rsi_5d_ago']

    # Pullback to EMA20 — price within 3% of EMA20 after being higher
    if -1 <= dist20 <= 3 and rsi5 > rsi and rsi < 60:
        return 'PULLBACK_EMA20', 'Price pulled back to EMA20 — ideal re-entry'

    # Pullback to EMA50
    dist50 = (ind['price'] - ind['ema_50']) / ind['ema_50'] * 100
    if -1 <= dist50 <= 3 and rsi < 55:
        return 'PULLBACK_EMA50', 'Deeper pullback to EMA50 — valid entry with wider stop'

    # Breakout continuation — just broke out, vol surge confirms
    if dist20 > 3 and dist20 <= 8 and ind['vol_ratio'] >= 1.5 and rsi > 55:
        return 'BREAKOUT_CONT', 'Breakout with volume — momentum entry'

    # Tight consolidation (ATR compressed)
    if ind['atr_pct'] < 1.5 and -2 <= dist20 <= 5:
        return 'COMPRESSION', 'Low volatility compression — coiling for move'

    return 'TRENDING', 'In uptrend — standard momentum play'


# ─────────────────────────────────────────────
# SCORING ENGINE (0-100)
# ─────────────────────────────────────────────
def score_stock(ind, stage, setup_type):
    score   = 0
    reasons = []

    # ── 1. Stage Quality (25 pts) ──
    if stage == 2:
        score += 25
        reasons.append("Stage 2 uptrend confirmed (+25)")
    else:
        reasons.append(f"Stage {stage} — not ideal (+0)")

    # ── 2. Setup Type (20 pts) ──
    setup_scores = {
        'PULLBACK_EMA20': 20,
        'PULLBACK_EMA50': 14,
        'COMPRESSION':    12,
        'BREAKOUT_CONT':  10,
        'TRENDING':        6,
    }
    s = setup_scores.get(setup_type, 0)
    score += s
    reasons.append(f"{setup_type} (+{s})")

    # ── 3. RSI Quality (20 pts) ──
    rsi = ind['rsi']
    if 45 <= rsi <= 60:
        score += 20
        reasons.append(f"RSI reset {rsi:.0f} — fresh momentum (+20)")
    elif 60 < rsi <= 68:
        score += 14
        reasons.append(f"RSI strong {rsi:.0f} (+14)")
    elif 40 <= rsi < 45:
        score += 8
        reasons.append(f"RSI oversold bounce {rsi:.0f} (+8)")
    elif 68 < rsi <= 75:
        score += 5
        reasons.append(f"RSI extended {rsi:.0f} (+5)")
    else:
        reasons.append(f"RSI poor {rsi:.0f} (+0)")

    # ── 4. Volume Confirmation (20 pts) ──
    # Use BOTH 10-day and 5-day ratio — works any day of week
    vr  = ind['vol_ratio']
    vr5 = ind['vol_5d_ratio']
    best_vr = max(vr, vr5)

    if best_vr >= 2.0 or ind['is_high_vol_day']:
        score += 20
        reasons.append(f"Strong vol confirmation {best_vr:.1f}x (+20)")
    elif best_vr >= 1.3:
        score += 13
        reasons.append(f"Above avg volume {best_vr:.1f}x (+13)")
    elif best_vr >= 1.0:
        score += 7
        reasons.append(f"Average volume {best_vr:.1f}x (+7)")
    else:
        score += 3
        reasons.append(f"Below avg volume (+3)")

    # ── 5. Trend Alignment (15 pts) ──
    slopes_positive = sum([
        ind['ema20_slope']  > 0,
        ind['ema50_slope']  > 0,
        ind['ema200_slope'] > 0,
    ])
    if slopes_positive == 3:
        score += 15
        reasons.append("All EMAs rising (+15)")
    elif slopes_positive == 2:
        score += 10
        reasons.append("2 EMAs rising (+10)")
    else:
        score += 4
        reasons.append("1 EMA rising (+4)")

    # ── Bonus Points ──
    # Near 52W high (momentum) but not extended
    if -15 <= ind['from_52w_high'] <= -3:
        score += 3
        reasons.append("Near 52W high — strong stock (+3)")

    # Supertrend bullish
    if ind['st_direction'] == 1:
        score += 3
        reasons.append("Supertrend bullish (+3)")

    return min(score, 100), reasons


# ─────────────────────────────────────────────
# BASE FILTERS — Broad, not restrictive
# ─────────────────────────────────────────────
def passes_base_filters(ind, stage):
    """
    Minimum qualifying criteria.
    Deliberately loose — scoring engine does the heavy lifting.
    """
    # Must be in uptrend (Stage 2) or transitioning
    if stage not in [2]:
        return False, "Not in Stage 2 uptrend"

    # Supertrend must be bullish
    if ind['st_direction'] != 1:
        return False, "Supertrend bearish"

    # RSI must show momentum (not overbought, not crashed)
    if not (35 < ind['rsi'] < 78):
        return False, f"RSI out of range ({ind['rsi']:.0f})"

    # Price must be above both EMA20 and EMA50 (or within 2% below EMA20)
    if ind['price'] < ind['ema_50'] * 0.97:
        return False, "Price too far below EMA50"

    # Minimum price filter
    if ind['price'] < 20:
        return False, "Price below Rs20 (illiquid)"

    # Must have 200 days data (EMA200 valid)
    if ind['ema_200'] <= 0:
        return False, "Insufficient history"

    return True, "Passed"


# ─────────────────────────────────────────────
# DECISION + POSITION SIZING
# ─────────────────────────────────────────────
def get_decision(score, in_stockedge):
    if score >= 75 and in_stockedge:  return 'HIGH_CONVICTION'
    if score >= 75:                    return 'GO'
    if score >= 58 and in_stockedge:  return 'WATCH_CLOSELY'
    if score >= 58:                    return 'WATCH'
    return 'NO_GO'


def calculate_position(price, atr, decision):
    """
    Stop loss = 1.5x ATR below entry (volatility-adjusted, professional method)
    Better than fixed % — adapts to each stock's actual volatility.
    """
    stop_dist = 1.5 * atr
    stop_loss = round(price - stop_dist, 2)

    if decision == 'HIGH_CONVICTION':
        risk_amt = CAPITAL * RISK_PCT_HC
    elif decision == 'GO':
        risk_amt = CAPITAL * RISK_PCT_GO
    else:
        return None

    shares  = max(1, int(risk_amt / stop_dist))
    target1 = round(price + (2.0 * stop_dist), 2)   # 2:1 RR
    target2 = round(price + (3.0 * stop_dist), 2)   # 3:1 RR (trail)

    return {
        'shares':      shares,
        'invested':    round(shares * price, 2),
        'stop_loss':   stop_loss,
        'stop_dist':   round(stop_dist, 2),
        'risk_amount': round(shares * stop_dist, 2),
        'target_1':    target1,
        'target_2':    target2,
        'rr_ratio':    '2:1 / 3:1',
    }


# ─────────────────────────────────────────────
# MAIN SCANNER
# ─────────────────────────────────────────────
def screen_stocks(stockedge_symbols):
    results   = []
    processed = 0
    skipped   = 0
    filtered  = {
        'stage':      0,
        'supertrend': 0,
        'rsi':        0,
        'price':      0,
        'data':       0,
    }
    total = len(NSE_STOCKS)

    print(f"Scanning {total} NSE stocks...\n")
    print(f"{'Symbol':<15} {'Stage':<8} {'Setup':<20} {'Score':<8} {'RSI':<8} {'Decision'}")
    print("-" * 80)

    for ticker in NSE_STOCKS:
        try:
            processed += 1
            symbol = ticker.replace('.NS', '')

            stock = yf.Ticker(ticker)
            hist  = stock.history(period='1y')   # Extra history for EMA200

            if len(hist) < 210:
                filtered['data'] += 1
                skipped += 1
                continue

            ind   = compute_indicators(hist)
            stage = get_stage(ind)

            ok, reason = passes_base_filters(ind, stage)
            if not ok:
                key = ('stage' if 'Stage' in reason else
                       'supertrend' if 'Supertrend' in reason else
                       'rsi' if 'RSI' in reason else
                       'price' if 'Price' in reason or 'Rs' in reason else 'data')
                filtered[key] = filtered.get(key, 0) + 1
                continue

            setup_type, setup_desc = get_setup_type(ind)
            score, reasons         = score_stock(ind, stage, setup_type)
            in_stockedge           = symbol in stockedge_symbols
            decision               = get_decision(score, in_stockedge)

            if decision == 'NO_GO':
                continue

            position = calculate_position(ind['price'], ind['atr_val'], decision)

            results.append({
                'symbol':        symbol,
                'decision':      decision,
                'score':         score,
                'stage':         stage,
                'setup_type':    setup_type,
                'setup_desc':    setup_desc,
                'in_stockedge':  in_stockedge,
                'price':         round(ind['price'], 2),
                'ema_20':        round(ind['ema_20'], 2),
                'ema_50':        round(ind['ema_50'], 2),
                'ema_200':       round(ind['ema_200'], 2),
                'rsi':           round(ind['rsi'], 2),
                'vol_ratio':     round(ind['vol_ratio'], 2),
                'vol_5d_ratio':  round(ind['vol_5d_ratio'], 2),
                'ema_dist_pct':  round(ind['ema20_dist'], 2),
                'from_52w_high': round(ind['from_52w_high'], 2),
                'atr_pct':       round(ind['atr_pct'], 2),
                'st_direction':  int(ind['st_direction']) if not pd.isna(ind['st_direction']) else 0,
                'reasons':       reasons,
                'position':      position,
                'timestamp':     datetime.now().isoformat(),
            })

            tag = {'HIGH_CONVICTION':'🟢 HC','GO':'🟩 GO',
                   'WATCH_CLOSELY':'🟡 WC','WATCH':'🟨 W'}.get(decision, '?')
            print(f"{symbol:<15} S{stage:<7} {setup_type:<20} {score:<8} {ind['rsi']:<8.1f} {tag}")

        except Exception as e:
            skipped += 1

    # Sort by score
    priority = {'HIGH_CONVICTION':0,'GO':1,'WATCH_CLOSELY':2,'WATCH':3}
    results.sort(key=lambda x: (priority.get(x['decision'],9), -x['score']))

    print("\n" + "="*80)
    print(f"SCAN COMPLETE: {processed} processed | {len(results)} setups found | {skipped} skipped")
    print(f"Filtered out → Stage:{filtered.get('stage',0)} | "
          f"Supertrend:{filtered.get('supertrend',0)} | "
          f"RSI:{filtered.get('rsi',0)} | "
          f"Price:{filtered.get('price',0)} | "
          f"Data:{filtered.get('data',0)}")

    hc = sum(1 for r in results if r['decision']=='HIGH_CONVICTION')
    go = sum(1 for r in results if r['decision']=='GO')
    wc = sum(1 for r in results if r['decision']=='WATCH_CLOSELY')
    w  = sum(1 for r in results if r['decision']=='WATCH')
    print(f"Results → HC:{hc} | GO:{go} | WATCH_CLOSELY:{wc} | WATCH:{w}")
    print("="*80 + "\n")

    return results


# ─────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────
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
        'methodology': {
            'framework':    'Stage Analysis (Weinstein) + EMA Pullback',
            'universe':     f'{len(NSE_STOCKS)} NSE stocks',
            'supertrend':   'Proper ATR-based Supertrend(10,3)',
            'volume':       '10-day + 5-day avg (works any day)',
            'stop_method':  '1.5x ATR volatility-adjusted stop',
            'rr_ratio':     '2:1 minimum / 3:1 trail',
        },
        'stocks': results,
    }

    with open('results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(results)} results to results.json")
    return output


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def main():
    print("\n" + "="*80)
    print("EDGE PROTOCOL v3.0 — Professional NSE Swing Trading System")
    print(f"Capital: Rs{CAPITAL/100000:.1f}L | Framework: Stage Analysis + EMA Pullback")
    print(f"Scan date: {datetime.now().strftime('%A, %Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    stockedge_symbols = load_stockedge()
    results           = screen_stocks(stockedge_symbols)
    save_results(results)

    actionable = sum(1 for r in results if r['decision'] in ['HIGH_CONVICTION','GO'])
    print(f"Done. {actionable} actionable setups ready.")

if __name__ == '__main__':
    main()
