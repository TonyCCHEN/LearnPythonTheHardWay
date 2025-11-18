import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------
# This function handles all the data fetching and calculation.
# st.cache_data tells Streamlit to "remember" the result for a
# set time (ttl=900 seconds = 15 mins) instead of re-running
# this expensive download every time the page is refreshed.
# -----------------------------------------------------------------
@st.cache_data(ttl=900)
def get_signal_data():
    tickers = ["006208.TW", "00713.TW"]
    
    # We only need the last ~2 years of data for a 252-day window
    # This is MUCH faster than downloading from 2010
    data = yf.download(tickers, period="2y")['Close']
    data.columns = ["006208", "00713"]
    
    # --- Start Calculation ---
    df = data.dropna()
    df['Ratio'] = df['006208'] / df['00713']
    
    window = 252
    df['MA'] = df['Ratio'].rolling(window=window).mean()
    df['STD'] = df['Ratio'].rolling(window=window).std()
    df['Zscore'] = (df['Ratio'] - df['MA']) / df['STD']
    
    df['Signal'] = 'Neutral'
    df.loc[df['Zscore'] > 1.5, 'Signal'] = 'Buy 00713 / Short 006208'
    df.loc[df['Zscore'] < -1.5, 'Signal'] = 'Buy 006208 / Short 00713'
    # --- End Calculation ---
    
    # Return just the most recent row of data
    return df.iloc[-1], df.index[-1].strftime("%Y-%m-%d")

# -----------------------------------------------------------------
# The Web App Interface
# -----------------------------------------------------------------

st.set_page_config(page_title="Pairs Trading Signal", layout="wide")
st.title("📈 006208 / 00713 Pairs Trading Signal")

# Add a button to manually refresh the data
if st.button("Refresh Data"):
    # Clear the cache so st.cache_data reruns
    st.cache_data.clear()

# Get the latest data
try:
    latest, last_date = get_signal_data()
    
    st.markdown(f"**Last Data Point:** {last_date}")

    # Display the current signal
    signal = latest['Signal']
    st.subheader("Current Signal: ")
    if "Buy 006208" in signal:
        st.success(f"**{signal}** (Ratio is very low)")
    elif "Buy 00713" in signal:
        st.warning(f"**{signal}** (Ratio is very high)")
    else:
        st.info(f"**{signal}**")

    # --- Display Key Metrics ---
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    # Use st.metric for a nice "dashboard" look
    col1.metric(
        label="Current Z-score",
        value=f"{latest['Zscore']:.2f}",
        help="How many standard deviations the ratio is from its 1-year mean."
    )
    
    col2.metric(
        label="Current Ratio",
        value=f"{latest['Ratio']:.4f}",
        help="006208 Price / 00713 Price"
    )
    
    col3.metric(
        label="1-Year Mean (MA)",
        value=f"{latest['MA']:.4f}",
        help="The 252-day moving average of the ratio."
    )

except Exception as e:
    st.error(f"An error occurred while fetching data: {e}")
    st.error("The yfinance API might be temporarily down or the tickers may have changed.")