import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import numpy as np
import time 

# --- 1. Global Parameters ---
ADX_PERIOD = 14
RSI_PERIOD = 14
EMA_FAST = 13
EMA_SLOW = 26
DATA_DAYS = 180
RR_TARGET = 2.5      
MIN_VOLUME = 100000  
MIN_PRICE = 5        
TSL_BUFFER_PERCENT = 0.02 
BATCH_SIZE = 25      

# --- 2. Dynamic ATR Multiplier Configuration ---
ATR_MULTIPLIER_CONFIG = {
    "TSLA": 3.5, "CRWD": 3.5, "META": 3.5, "AMZN": 3.0, "NVDA": 3.5, "AMD": 3.5, "AVGO": 3.5, "MSFT": 3.0,
    "ALAB": 3.5, "PLTR": 3.5, "ZM": 3.5, "SNOW": 3.5, "DASH": 3.5, "UBER": 3.5, "ABNB": 3.5, "ROKU": 3.5,
    "SQ": 3.5, "SHOP": 3.5, "SNAP": 3.5, "PINS": 3.5, "NET": 3.5, "DOCU": 3.5, "FSLY": 3.5, "OKTA": 3.5,
    "ZS": 3.5, "CRSP": 3.5,
    "00631L.TW": 3.5, "2454.TW": 3.5, "6781.TW": 3.5, "2379.TW": 3.5, "2449.TW": 3.5, "3711.TW": 3.5, "6669.TW": 3.5, "3661.TW": 3.5,
    "1303.TW": 3.0, "1326.TW": 3.0, "2330.TW": 3.0, "2317.TW": 3.0, "2382.TW": 3.0, "2308.TW": 3.0, "2891.TW": 3.0, "2881.TW": 3.0,
    "DEFAULT": 3.0
}

# --- 3. Ticker List Assembly ---
def get_ticker_lists():
    sp500_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JPM', 'JNJ', 'V', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'LLY', 'NOW', 'DHI']
    
    us_stocks_custom = [
        'AAPL', 'XLV', 'NFLX', 'ALAB', 'IJR', 'AMD', 'AMZN', 'RMBS', 'VPU', 'VIS', 'SHOP', 'SCHW', 'AVGO', 'ONDS', 
        'QCOM', 'META', 'NVDA', 'MRVL', 'SITM', 'ISRG', 'BRK-B', 'CRWD', 'TSLA', 'ASML', 'PLTR', 'GOOGL', 'HIMS', 
        'VRT', 'NRG', 'RTX', 'NVTS', 'CRUS', 'ENPH', 'PYPL', 'SOFI', 'MU', 'VST', 'AOSL', 'CRDO', 'TEM', 'ZS', 
        'LLY', 'TTEK', 'MORN', 'SPXC', 'GTLS', 'PPC', 'CPAY', 'CAG', 'TAP', 'DVA', 'AA', 'BTC-USD'
    ]

    tw_stocks_raw = [
        '2330', '2317', '2454', '2308', '2382', '2891', '3711', '2881', '2882', '2886', '2303', '2357', '2884', 
        '2892', '3231', '2885', '2379', '6669', '2345', '2890', '2887', '5871', '2327', '2883', '3034', '1216', 
        '1303', '2412', '3045', '3008', '2383', '4938', '3661', '2002', '1301', '2207', '5880', '2912', '2603', 
        '4904', '2395', '1326', '2301', '3017', '2609', '2615', '1101', '5876', '6505', '9910', '2360', '3665', 
        '2449', '3037', '2344', '3653', '2408', '2385', '2376', '1590', '2801', '1319', '2313', '1476', '3036', 
        '3533', '1513', '1605', '2409', '3481', '2353', '2356', '2324', '1102', '1229', '2834', '1402', '2880', 
        '2812', '2377', '2855', '9904', '2618', '2474', '2347', '8046', '6239', '1722', '2371', '2633', '1477', 
        '4958', '2404', '6415', '6770', '3702', '1504', '8464', '3706', '3044', '6176', '1210', '2027', '2354', 
        '6285', '3023', '2105', '8454', '2402', '6269', '1802', '2374', '2606', '2201', '1795', '2610', '5879', 
        '2542', '2206', '4763', '5434', '1723', '9921', '6139', '6531', '3443', '2368', '2458', '6446', '6191', 
        '2049', '1519', '1717', '3592', '8016', '3708', '4915', '2492', '9938', '2337', '2340', '5347', '2059', 
        '3406', '6719', '1589', '2417', '1312'
    ]
    tw_tickers = [f"{t}.TW" for t in set(tw_stocks_raw)]

    tw_etf = ["00631L.TW"]

    return {
        "S&P 500 (Sample)": sp500_tickers,
        "Custom US Stocks": us_stocks_custom,
        "TW Stocks (Top 150)": tw_tickers,
        "TW ETF (00631L.TW)": tw_etf
    }

# --- 4. Helper Functions ---
# (Helper functions for calculate_tsl, calculate_take_profit, calculate_rr, calculate_position_sizing)

def calculate_tsl(data, multiplier):
    if data.empty or len(data) < ADX_PERIOD:
        return np.nan
    latest_atr = data['ATR'].iloc[-1]
    if pd.isna(latest_atr) or latest_atr <= 0:
        return np.nan
    lookback_highs = data['High'].iloc[-ADX_PERIOD:].max()
    if pd.isna(lookback_highs):
        return np.nan
    tsl = lookback_highs - (latest_atr * multiplier)
    return round(tsl, 2) if tsl > 0 else np.nan

def calculate_take_profit(entry_price, stop_loss, rr_ratio):
    if pd.isna(entry_price) or pd.isna(stop_loss) or stop_loss <= 0:
        return np.nan
    risk = entry_price - stop_loss
    if risk <= 0:
        return np.nan
    target = entry_price + (risk * rr_ratio)
    return round(target, 2)

def calculate_rr(entry_price, tsl_price, tp_price):
    if pd.isna(entry_price) or pd.isna(tsl_price) or pd.isna(tp_price):
        return np.nan
    risk = entry_price - tsl_price
    reward = tp_price - entry_price
    if risk <= 0 or reward <= 0:
        return np.nan
    return round(reward / risk, 2)

def calculate_position_sizing(entry_price, tsl_price, capital=1000000, risk_percent=0.01):
    if pd.isna(entry_price) or pd.isna(tsl_price) or tsl_price <= 0:
        return 0
    risk_amount = capital * risk_percent
    risk_per_share = entry_price - tsl_price
    if risk_per_share <= 0:
        return 0
    return int(risk_amount // risk_per_share)

# --- Core Processing Logic (Shared) ---
def process_ticker_data(data, ticker):
    """Processes cleaned data through indicators and signal logic."""
    multiplier = ATR_MULTIPLIER_CONFIG.get(ticker, ATR_MULTIPLIER_CONFIG["DEFAULT"])
    
    # Calculate Indicators
    data.ta.adx(length=ADX_PERIOD, append=True) 
    data.ta.atr(length=ADX_PERIOD, append=True) 
    data.ta.ema(length=EMA_FAST, append=True) 
    data.ta.ema(length=EMA_SLOW, append=True) 
    data.ta.rsi(length=RSI_PERIOD, append=True) 

    data.dropna(inplace=True)

    if len(data) < 2:
        return None, None # Not enough data

    # Extract Latest Values
    latest_row = data.iloc[-1]
    yesterday_row = data.iloc[-2]

    adx = latest_row[f'ADX_{ADX_PERIOD}']
    di_plus = latest_row[f'DMP_{ADX_PERIOD}']
    di_minus = latest_row[f'DMN_{ADX_PERIOD}']
    rsi = latest_row[f'RSI_{RSI_PERIOD}']
    ema_f = latest_row[f'EMA_{EMA_FAST}']
    ema_s = latest_row[f'EMA_{EMA_SLOW}']
    latest_close = latest_row['Close']
    
    ema_f_yest = yesterday_row[f'EMA_{EMA_FAST}']
    ema_s_yest = yesterday_row[f'EMA_{EMA_SLOW}']

    avg_volume = data['Volume'].iloc[-20:].mean()
    
    # --- Apply Initial Filters ---
    if pd.isna(adx) or pd.isna(rsi) or pd.isna(latest_close) or pd.isna(avg_volume):
        return None, None
    if avg_volume < MIN_VOLUME or latest_close < MIN_PRICE:
        return None, None

    # Calculate TSL and R/R components
    tsl_price = calculate_tsl(data, multiplier)
    if pd.isna(tsl_price) or tsl_price <= 0:
        return None, None
        
    stop_distance = latest_close - tsl_price
    if stop_distance / latest_close < TSL_BUFFER_PERCENT:
        return None, None
    
    signal_data = {
        'Ticker': ticker, 'Close': f"{latest_close:.2f}", 
        'ADX': f"{adx:.2f}", 'RSI': f"{rsi:.2f}", 'TSL': tsl_price
    }
    
    # --- TREND SIGNAL LOGIC ---
    if adx > 25:
        is_trend_bullish = (ema_f > ema_s) and (di_plus > di_minus) and \
                           (ema_f_yest < ema_s_yest and ema_f > ema_s) 
        
        if is_trend_bullish and (rsi < 70):
            target_price = calculate_take_profit(latest_close, tsl_price, RR_TARGET)
            rr_ratio = calculate_rr(latest_close, tsl_price, target_price)
            
            if not pd.isna(rr_ratio) and rr_ratio >= RR_TARGET:
                return {**signal_data, 'R_R': rr_ratio, 'Target': target_price, 
                        'DI+': f"{di_plus:.2f}", 'DI-': f"{di_minus:.2f}",
                        'Max Shares (1% Risk)': calculate_position_sizing(latest_close, tsl_price)}, None

    # --- MEAN REVERSION SIGNAL LOGIC ---
    elif adx < 20 and rsi < 30:
        target_price = round(ema_s, 2)
        rr_ratio = calculate_rr(latest_close, tsl_price, target_price)

        if not pd.isna(rr_ratio) and rr_ratio > 1.0:
            return None, {**signal_data, 'R_R': rr_ratio, 'Target (EMA_26)': target_price,
                          'Max Shares (1% Risk)': calculate_position_sizing(latest_close, tsl_price)}
            
    return None, None

# --- US/Batch Scanning Function ---
def scan_us_tickers(us_list, start_date, end_date, status_text):
    trend_signals = []
    mean_rev_signals = []
    failed_tickers = []
    total_us = len(us_list)
    
    us_batches = [us_list[i:i + BATCH_SIZE] for i in range(0, total_us, BATCH_SIZE)]
    current_count = 0

    for batch_index, batch in enumerate(us_batches):
        batch_tickers_str = " ".join(batch)
        current_count += len(batch)

        status_text.text(f"Scanning US/Batch {batch_index+1}/{len(us_batches)}: ({current_count}/{total_us})...")
        
        try:
            batch_data = yf.download(batch_tickers_str, start=start_date, end=end_date, progress=False, show_errors=False)
            time.sleep(1) # Delay between batches
        except Exception:
            failed_tickers.extend(batch)
            continue
            
        for ticker in batch:
            try:
                if isinstance(batch_data.columns, pd.MultiIndex):
                    if ticker in batch_data.columns.get_level_values(1):
                        data = batch_data.loc[:, (slice(None), ticker)]
                        data.columns = data.columns.droplevel(1) 
                    else:
                        failed_tickers.append(ticker)
                        continue
                elif ticker == batch[0] and len(batch) == 1: 
                    data = batch_data
                else:
                    failed_tickers.append(ticker)
                    continue

                # --- PATCH 1: Cleanup Data ---
                data = data.apply(pd.to_numeric, errors='coerce')
                data.dropna(subset=['Close'], inplace=True)
                
                if data.empty or len(data) < 40:
                    failed_tickers.append(ticker)
                    continue

                trend_sig, mr_sig = process_ticker_data(data, ticker)
                if trend_sig: trend_signals.append(trend_sig)
                if mr_sig: mean_rev_signals.append(mr_sig)

            except Exception:
                failed_tickers.append(ticker)
                
    return trend_signals, mean_rev_signals, failed_tickers

# --- TW/Single Scanning Function ---
def scan_tw_tickers(tw_list, start_date, end_date, status_text):
    trend_signals = []
    mean_rev_signals = []
    failed_tickers = []
    
    for i, ticker in enumerate(tw_list):
        status_text.text(f"Scanning TW/Single {i+1}/{len(tw_list)}: ({ticker})...")
        
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False, show_errors=False)
            
            # --- PATCH 1: Cleanup Data ---
            data = data.apply(pd.to_numeric, errors='coerce')
            data.dropna(subset=['Close'], inplace=True)

            if data.empty or len(data) < 40:
                failed_tickers.append(ticker)
                continue
            
            trend_sig, mr_sig = process_ticker_data(data, ticker)
            if trend_sig: trend_signals.append(trend_sig)
            if mr_sig: mean_rev_signals.append(mr_sig)

            time.sleep(1.5) # Slow down international requests significantly

        except Exception:
            failed_tickers.append(ticker)
            time.sleep(1.5)

    return trend_signals, mean_rev_signals, failed_tickers

# --- 5. Main Scanner Logic (Orchestrator) ---
@st.cache_data(ttl=timedelta(hours=4))
def run_advanced_scan(all_tickers_list):
    status_text = st.empty()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DATA_DAYS)

    # 1. Split Tickers (Syntax is correct here)
    us_tickers = [t for t in all_tickers_list if not t.endswith('.TW')]
    tw_tickers = [t for t in all_tickers_list if t.endswith('.TW')]
    
    # 2. Run US Scan (Batch)
    us_trend, us_mr, us_failed = scan_us_tickers(us_tickers, start_date, end_date, status_text)
    
    # 3. Run TW Scan (Slow/Single)
    tw_trend, tw_mr, tw_failed = scan_tw_tickers(tw_tickers, start_date, end_date, status_text)

    # 4. Combine Results
    trend_df = pd.DataFrame(us_trend + tw_trend)
    mean_rev_df = pd.DataFrame(us_mr + tw_mr)
    failed_list = us_failed + tw_failed

    status_text.empty()
    return trend_df, mean_rev_df, failed_list

# --- 6. Streamlit UI ---
def main():
    st.set_page_config(layout="wide", page_title="Advanced Stock Screener")
    st.title("🛡️ Systematic Daily Stock Screener (ADX + R/R Filter)")
    st.markdown("---")
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Scanner Settings")
        st.markdown(f"**Trend Filter (Buy):** ADX > 25, RSI < 70, R/R $\\ge$ **{RR_TARGET}**")
        st.markdown(f"**MR Filter (Buy):** ADX < 20, RSI < 30, R/R $>$ 1.0")

        ticker_groups = get_ticker_lists()
        
        selected_keys = st.multiselect(
            "Select Ticker Lists to Scan:",
            options=list(ticker_groups.keys()),
            default=["Custom US Stocks", "TW Stocks (Top 150)"]
        )

        all_tickers = sorted(list(set([t for key in selected_keys for t in ticker_groups[key]])))

        st.info(f"Scanning **{len(all_tickers)}** unique tickers.")
        st.caption("US stocks are processed in batches (faster); TW stocks are processed one-by-one (stable).")
        
        run_button = st.button("▶️ Run Advanced Scan")
        
    st.header(f"Results for Scan on: {datetime.now().strftime('%Y-%m-%d')}")
    st.caption("---")
    
    # --- Execute Scan and Display Results ---
    if run_button and all_tickers:
        with st.spinner('Fetching data and running systematic analysis...'):
            trend_df, mean_rev_df, failed_tickers = run_advanced_scan(all_tickers)
        
        # Trend Signals
        st.subheader(f"📈 Trend Following Signals (R/R $\\ge$ {RR_TARGET}:1) - {len(trend_df)}")
        if not trend_df.empty:
            st.dataframe(trend_df.sort_values(by='ADX', ascending=False), use_container_width=True, hide_index=True)
            st.markdown("**(Risk/Reward)** R/R $\\ge$ 2.5. Trend is strong (**ADX > 25**) and momentum is not overbought (**RSI < 70**).")
        else:
            st.info("No Trend Following signals found meeting all high-expectancy criteria.")

        st.markdown("---")

        # Mean Reversion Signals
        st.subheader(f"📉 Mean Reversion Signals (Oversold/Consolidation) - {len(mean_rev_df)}")
        if not mean_rev_df.empty:
            st.dataframe(mean_rev_df.sort_values(by='RSI', ascending=True), use_container_width=True, hide_index=True)
            st.markdown("**(Oversold)** RSI < 30 in a consolidation (**ADX < 20**). Target is the **EMA(26)**.")
        else:
            st.info("No Mean Reversion signals found.")

        st.markdown("---")
        
        # Failed Tickers
        st.subheader(f"⚠️ Failed Tickers - {len(failed_tickers)}")
        if failed_tickers:
            st.warning("Could not retrieve data or failed initial checks. This is often due to delisted tickers or aggressive filtering.")
            st.dataframe(pd.DataFrame({'Ticker': failed_tickers}), use_container_width=False, hide_index=True)
        else:
            st.success("All selected tickers were successfully processed.")

    elif run_button:
         st.error("Please select at least one list of tickers to scan in the sidebar.")
    else:
        st.info("Select lists in the sidebar and click 'Run Advanced Scan' to begin the analysis.")

if __name__ == '__main__':
    main()
