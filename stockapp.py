import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import numpy as np

# --- 1. Global Parameters (Direct Translation of R Code) ---
ADX_PERIOD = 14
RSI_PERIOD = 14
EMA_FAST = 13
EMA_SLOW = 26
DATA_DAYS = 180
RR_TARGET = 2.5       # CRITICAL: Minimum R/R ratio required for Trend
MIN_VOLUME = 100000   # Liquidity filter
MIN_PRICE = 5         # Price filter
TSL_BUFFER_PERCENT = 0.02 # TSL must be at least 2% away from close

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

# --- 3. Ticker List Assembly (Simplified for Streamlit) ---
def get_ticker_lists():
    # Simplified S&P 500 list
    sp500_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JPM', 'JNJ', 'V', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'LLY', 'NOW', 'DHI']
    
    us_stocks_custom = [
        'AAPL', 'XLV', 'NFLX', 'ALAB', 'IJR', 'AMD', 'AMZN', 'RMBS', 'VPU', 'VIS', 'SHOP', 'SCHW', 'AVGO', 'ONDS', 
        'QCOM', 'META', 'NVDA', 'MRVL', 'SITM', 'ISRG', 'BRK-B', 'CRWD', 'TSLA', 'ASML', 'PLTR', 'GOOGL', 'HIMS', 
        'VRT', 'NRG', 'RTX', 'NVTS', 'CRUS', 'ENPH', 'PYPL', 'SOFI', 'MU', 'VST', 'AOSL', 'CRDO', 'TEM', 'ZS', 
        'LLY', 'TTEK', 'MORN', 'SPXC', 'GTLS', 'PPC', 'CPAY', 'CAG', 'TAP', 'DVA', 'AA'
    ]

    # Combined TW stocks list (Top 150)
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

def calculate_tsl(data, multiplier):
    """Calculates the Trailing Stop Loss using the highest high and ATR."""
    if data.empty or len(data) < ADX_PERIOD:
        return np.nan

    # pandas_ta uses 'ATR' column name for the latest value
    latest_atr = data['ATR'].iloc[-1]
    if pd.isna(latest_atr) or latest_atr <= 0:
        return np.nan

    # Look back for the highest high over the ATR period (14 days, since ADX_PERIOD is 14)
    lookback_highs = data['High'].iloc[-ADX_PERIOD:].max()
    
    if pd.isna(lookback_highs):
        return np.nan

    tsl = lookback_highs - (latest_atr * multiplier)
    return round(tsl, 2) if tsl > 0 else np.nan

def calculate_take_profit(entry_price, stop_loss, rr_ratio):
    """Calculates the take profit price based on entry, stop, and R/R."""
    if pd.isna(entry_price) or pd.isna(stop_loss) or stop_loss <= 0:
        return np.nan
    
    risk = entry_price - stop_loss
    if risk <= 0:
        return np.nan
    
    target = entry_price + (risk * rr_ratio)
    return round(target, 2)

def calculate_rr(entry_price, tsl_price, tp_price):
    """Calculates the final Risk/Reward ratio."""
    if pd.isna(entry_price) or pd.isna(tsl_price) or pd.isna(tp_price):
        return np.nan

    risk = entry_price - tsl_price
    reward = tp_price - entry_price
    
    if risk <= 0 or reward <= 0:
        return np.nan
    
    return round(reward / risk, 2)

def calculate_position_sizing(entry_price, tsl_price, capital=1000000, risk_percent=0.01):
    """Calculates the number of shares based on 1% risk of $1,000,000 capital."""
    if pd.isna(entry_price) or pd.isna(tsl_price) or tsl_price <= 0:
        return 0
    risk_amount = capital * risk_percent
    risk_per_share = entry_price - tsl_price
    if risk_per_share <= 0:
        return 0
    return int(risk_amount // risk_per_share)

# --- 5. Main Scanner Logic ---

@st.cache_data(ttl=timedelta(hours=4))
def run_advanced_scan(all_tickers_list):
    """Fetches data, calculates indicators, and runs the signal logic for all tickers."""
    trend_signals = []
    mean_reversion_signals = []
    failed_tickers = []
    
    end_date = datetime.now()
    # Need sufficient data for ADX (14) and EMA(26), plus padding
    start_date = end_date - timedelta(days=DATA_DAYS)
    
    # Placeholder for Streamlit feedback
    status_text = st.empty()
    
    for i, ticker in enumerate(all_tickers_list):
        status_text.text(f"Scanning {ticker} ({i+1}/{len(all_tickers_list)})...")

        multiplier = ATR_MULTIPLIER_CONFIG.get(ticker, ATR_MULTIPLIER_CONFIG["DEFAULT"])

        try:
            # 1. Fetch Data
            data = yf.download(ticker, start=start_date, end=end_date, progress=False, show_errors=False)

            if data.empty or len(data) < (EMA_SLOW * 2): # Need enough data for 26-period EMA
                failed_tickers.append(ticker)
                continue
            
            # 2. Calculate Indicators (pandas_ta)
            # ADX(14) also calculates +DI and -DI
            data.ta.adx(length=ADX_PERIOD, append=True) 
            data.ta.atr(length=ADX_PERIOD, append=True) # ATR(14) for TSL
            data.ta.ema(length=EMA_FAST, append=True) # EMA(13)
            data.ta.ema(length=EMA_SLOW, append=True) # EMA(26)
            data.ta.rsi(length=RSI_PERIOD, append=True) # RSI(14)

            # Drop rows with NaN values (start of indicators)
            data.dropna(inplace=True)

            if len(data) < 2:
                failed_tickers.append(ticker)
                continue

            # 3. Extract Latest Values
            latest_row = data.iloc[-1]
            yesterday_row = data.iloc[-2]

            # Get latest values using pandas_ta default column names
            adx = latest_row[f'ADX_{ADX_PERIOD}']
            di_plus = latest_row[f'DMP_{ADX_PERIOD}']
            di_minus = latest_row[f'DMN_{ADX_PERIOD}']
            rsi = latest_row[f'RSI_{RSI_PERIOD}']
            ema_f = latest_row[f'EMA_{EMA_FAST}']
            ema_s = latest_row[f'EMA_{EMA_SLOW}']
            latest_close = latest_row['Close']
            
            # Use yesterday's EMA values for crossover check
            ema_f_yest = yesterday_row[f'EMA_{EMA_FAST}']
            ema_s_yest = yesterday_row[f'EMA_{EMA_SLOW}']

            # Get Volume (mean of last 20 days for robustness, or just last day)
            avg_volume = data['Volume'].iloc[-20:].mean()
            
            # --- 4. Apply Initial Filters ---
            if pd.isna(adx) or pd.isna(rsi) or pd.isna(latest_close) or pd.isna(avg_volume):
                continue
            if avg_volume < MIN_VOLUME:
                continue
            if latest_close < MIN_PRICE:
                continue

            # 5. Calculate TSL, Target, R/R
            tsl_price = calculate_tsl(data, multiplier)
            if pd.isna(tsl_price) or tsl_price <= 0:
                continue
                
            stop_distance = latest_close - tsl_price
            if stop_distance / latest_close < TSL_BUFFER_PERCENT:
                continue
            
            # --- TREND SIGNAL LOGIC (ADX > 25, RSI < 70, R/R >= 2.5) ---
            if adx > 25:
                # Trend is strong and bullish if EMA and DI are aligned
                is_trend_bullish = (ema_f > ema_s) and (di_plus > di_minus) and \
                                   (ema_f_yest < ema_s_yest and ema_f > ema_s) # Added EMA Crossover condition
                
                is_valid_entry = is_trend_bullish and (rsi < 70)
                
                if is_valid_entry:
                    target_price = calculate_take_profit(latest_close, tsl_price, RR_TARGET)
                    rr_ratio = calculate_rr(latest_close, tsl_price, target_price)
                    
                    if not pd.isna(rr_ratio) and rr_ratio >= RR_TARGET:
                        trend_signals.append({
                            'Ticker': ticker,
                            'Close': f"{latest_close:.2f}",
                            'R_R': rr_ratio,
                            'TSL': tsl_price,
                            'Target': target_price,
                            'ADX': f"{adx:.2f}",
                            'RSI': f"{rsi:.2f}",
                            'DI+': f"{di_plus:.2f}",
                            'DI-': f"{di_minus:.2f}",
                            'Max Shares (1% Risk)': calculate_position_sizing(latest_close, tsl_price)
                        })

            # --- MEAN REVERSION SIGNAL LOGIC (ADX < 20, RSI < 30, R/R > 1.0) ---
            elif adx < 20 and rsi < 30:
                # Target is the 26-day EMA
                target_price = round(ema_s, 2)
                rr_ratio = calculate_rr(latest_close, tsl_price, target_price)

                if not pd.isna(rr_ratio) and rr_ratio > 1.0:
                    mean_reversion_signals.append({
                        'Ticker': ticker,
                        'Close': f"{latest_close:.2f}",
                        'R_R': rr_ratio,
                        'TSL': tsl_price,
                        'Target (EMA_26)': target_price,
                        'ADX': f"{adx:.2f}",
                        'RSI': f"{rsi:.2f}",
                        'Max Shares (1% Risk)': calculate_position_sizing(latest_close, tsl_price)
                    })

        except Exception as e:
            # Catch data errors or yfinance connection issues
            failed_tickers.append(ticker)
            # st.error(f"Error processing {ticker}: {e}") # Debugging

    status_text.empty()
    return pd.DataFrame(trend_signals), pd.DataFrame(mean_reversion_signals), failed_tickers

# --- 6. Streamlit UI ---

def main():
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
        st.caption("Data is cached for 4 hours. Click 'Run Scan' to fetch new data.")
        
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
            st.markdown(
                """
                **Strategy:** Buy entry on confirmed trend strength (**ADX > 25**), momentum alignment (**DI+ > DI-**, **EMA-F > EMA-S**), 
                and **RSI < 70** (not overbought). Requires high **Risk/Reward** (R/R $\\ge$ 2.5).
                """
            )
        else:
            st.info("No Trend Following signals found meeting all high-expectancy criteria.")

        st.markdown("---")

        # Mean Reversion Signals
        st.subheader(f"📉 Mean Reversion Signals (Oversold/Consolidation) - {len(mean_rev_df)}")
        if not mean_rev_df.empty:
            st.dataframe(mean_rev_df.sort_values(by='RSI', ascending=True), use_container_width=True, hide_index=True)
            st.markdown(
                """
                **Strategy:** Buy entry on oversold condition (**RSI < 30**) in a low-trend environment (**ADX < 20**). 
                Target is the **EMA(26)** (the mean). Requires **R/R > 1.0**.
                """
            )
        else:
            st.info("No Mean Reversion signals found.")

        st.markdown("---")
        
        # Failed Tickers
        st.subheader(f"⚠️ Failed Tickers - {len(failed_tickers)}")
        if failed_tickers:
            st.warning("Could not retrieve data or failed initial checks.")
            st.dataframe(pd.DataFrame({'Ticker': failed_tickers}), use_container_width=False, hide_index=True)
        else:
            st.success("All selected tickers were successfully processed.")

    elif run_button:
         st.error("Please select at least one list of tickers to scan in the sidebar.")
    else:
        st.info("Select lists in the sidebar and click 'Run Advanced Scan' to begin the analysis.")

if __name__ == '__main__':
    main()
