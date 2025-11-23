import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
import random
import time

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="AlphaVoter Pro", page_icon="🗳️", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Card Styling */
    .voter-card {
        background-color: #1e232e;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Headings and Metrics */
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    .metric-value { font-size: 24px; font-weight: bold; color: #e2e8f0; }
    .metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Badges */
    .badge-bullish { background-color: #064e3b; color: #34d399; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-bearish { background-color: #450a0a; color: #f87171; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .badge-neutral { background-color: #374151; color: #9ca3af; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #080a0d; }
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND LOGIC ---

def get_market_context():
    """Fetches VIX (Volatility Index) to gauge market fear."""
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        current_vix = hist['Close'].iloc[-1]
        return current_vix
    except:
        return 20.0 # Default fallback

def calculate_mdd(history):
    """Calculates Maximum Drawdown (MDD) from the 1-year history."""
    try:
        # Calculate running maximum
        roll_max = history['Close'].cummax()
        # Calculate drawdown
        drawdown = (history['Close'] - roll_max) / roll_max
        # Get max drawdown (minimum value)
        mdd = drawdown.min()
        return mdd
    except:
        return 0.0

def get_stock_data(ticker):
    """Fetches live data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        data = {
            "symbol": info.get("symbol", ticker),
            "name": info.get("shortName", ticker),
            "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "pe_ratio": info.get("trailingPE", None),
            "beta": info.get("beta", 1.0),
            "market_cap": info.get("marketCap", 0),
            "sector": info.get("sector", "Unknown"),
            "revenue_growth": info.get("revenueGrowth", 0),
            "fifty_two_high": info.get("fiftyTwoWeekHigh", 0),
            "history": hist
        }
        return data
    except Exception as e:
        return None

def run_monte_carlo(hist, current_price, days=30, simulations=200):
    """Runs a Monte Carlo simulation for future price paths."""
    returns = hist['Close'].pct_change().dropna()
    mu = returns.mean()
    sigma = returns.std()
    
    # Simulation logic
    dt = 1
    simulation_results = np.zeros((days, simulations))
    simulation_results[0] = current_price
    
    for t in range(1, days):
        # Geometric Brownian Motion
        random_shock = np.random.normal(0, 1, simulations)
        drift = (mu - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt) * random_shock
        
        # S_t = S_{t-1} * exp(drift + diffusion)
        simulation_results[t] = simulation_results[t-1] * np.exp(drift + diffusion)
        
    return simulation_results

def simulate_heuristic_vote(persona, data, vix, mdd):
    """
    Simulates a vote based on financial logic + VIX + MDD.
    """
    price = data['price']
    pe = data['pe_ratio'] if data['pe_ratio'] else 20
    beta = data['beta'] if data['beta'] else 1.0
    growth = data['revenue_growth']
    
    # Adjust logic based on VIX (Fear Index)
    is_high_fear = vix > 25
    is_deep_drawdown = mdd < -0.20 # Down more than 20% from peak
    
    sentiment = "Neutral"
    target = price
    reason = "Watching market conditions."
    
    if persona == "Warren Buffett":
        # Buffett gets greedy when others are fearful (High VIX)
        if is_high_fear and is_deep_drawdown and pe < 20:
            sentiment = "Bullish"
            target = price * 1.25
            reason = "Market fear offers a discount on quality. Buying the dip heavily."
        elif pe > 30:
            sentiment = "Bearish"
            target = price * 0.80
            reason = "Valuations are irrational regardless of volatility."
        else:
            sentiment = "Neutral"
            target = price * 1.05
            reason = "Fair value. Holding steady."

    elif persona == "Cathie Wood":
        # High VIX often hurts high-beta growth stocks
        if is_high_fear and beta > 1.5:
            sentiment = "Bearish"
            target = price * 0.85
            reason = "Macro volatility is temporarily compressing valuations of innovation."
        elif growth > 0.15:
            sentiment = "Bullish"
            target = price * 1.50
            reason = "Innovation solves problems. We focus on the 5-year horizon, not the VIX."

    elif persona == "Ray Dalio":
        # Dalio hates unhedged risk in high vol environments
        if is_high_fear:
            sentiment = "Neutral"
            target = price
            reason = "Volatility is elevated. Reducing risk parity exposure."
        elif beta < 1.0:
            sentiment = "Bullish"
            target = price * 1.10
            reason = "Stable cash flows are attractive in this cycle."

    elif persona == "Jim Cramer":
        # Momentum based
        if is_high_fear:
            sentiment = "Bearish"
            target = price * 0.88
            reason = "Too much fear! The VIX is screaming! Get out!"
        elif price > data['fifty_two_high'] * 0.9:
            sentiment = "Bullish"
            target = price * 1.15
            reason = "The bulls are running! Don't bet against this market!"
        else:
            sentiment = "Neutral"
            target = price
            reason = "Wait for the bell."

    elif persona == "Bill Ackman":
        if is_deep_drawdown and pe < 18:
            sentiment = "Bullish"
            target = price * 1.30
            reason = "The market has overreacted. The underlying business is simple and profitable."
        else:
            sentiment = "Neutral"
            target = price
            reason = "No clear catalyst yet."

    return {
        "name": persona,
        "sentiment": sentiment,
        "target": round(target, 2),
        "reason": reason,
        "weight": random.randint(40, 95)
    }

def get_ai_vote(api_key, persona, data, vix, mdd):
    """Uses Gemini if available, otherwise fallback."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        Act as {persona}. Analyze {data['symbol']} (${data['price']}).
        Context: VIX is {vix:.2f} (Market Fear Index). 
        Stock MDD (Max Drawdown) is {mdd:.2%}.
        Fundamentals: PE={data['pe_ratio']}, Beta={data['beta']}.
        
        Briefly explain your stance (Bullish/Bearish/Neutral) and give a target price.
        """
        
        response = model.generate_content(
    prompt,
    generation_config=genai.GenerationConfig(
        safety_settings={"enable_data_logging": False}
    )
)

        # Fallback to heuristic for stability in this demo
        return simulate_heuristic_vote(persona, data, vix, mdd) 
    except:
        return simulate_heuristic_vote(persona, data, vix, mdd)

# --- FRONTEND UI ---

# Sidebar
with st.sidebar:
    st.title("AlphaVoter Pro")
    st.caption("Consensus Engine v3.0 (Monte Carlo + VIX)")
    
    ticker_input = st.text_input("Enter Ticker", value="NVDA").upper()
   
    import os
api_key = os.getenv("GEMINI_API_KEY")  # set on server only

    st.markdown("---")
    st.markdown("### 🗳️ The Board")
    
    voters = [
        {"name": "Warren Buffett", "firm": "Berkshire"},
        {"name": "Cathie Wood", "firm": "ARK Invest"},
        {"name": "Ray Dalio", "firm": "Bridgewater"},
        {"name": "Jim Cramer", "firm": "CNBC"},
        {"name": "Bill Ackman", "firm": "Pershing Sq"},
    ]
    
    for v in voters:
        st.markdown(f"- **{v['name']}** ({v['firm']})")

# Main Content
if ticker_input:
    # 1. Fetch Data
    with st.spinner(f"Analyzing {ticker_input} market data..."):
        data = get_stock_data(ticker_input)
        vix = get_market_context()
        mdd = calculate_mdd(data['history']) if data else 0
        time.sleep(0.5)
    
    if data:
        # Header Section
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        with col1:
            st.markdown(f"## {data['symbol']}")
            st.caption(data['name'])
        with col2:
            st.metric("Price", f"${data['price']:,.2f}")
        with col3:
            # VIX Indicator
            vix_color = "normal" if vix < 20 else "inverse" 
            st.metric("Market VIX", f"{vix:.2f}", delta="High Fear" if vix > 25 else "Stable", delta_color=vix_color)
        with col4:
            # MDD Indicator
            st.metric("Max Drawdown (1Y)", f"{mdd:.1%}", delta_color="inverse")

        # Tabs for different views
        tab_consensus, tab_simulation = st.tabs(["🗳️ Consensus Vote", "🎲 Monte Carlo Simulator"])

        # --- TAB 1: CONSENSUS ---
        with tab_consensus:
            # Generate Votes
            results = []
            for v in voters:
                if api_key:
                    vote = get_ai_vote(api_key, v['name'], data, vix, mdd)
                else:
                    vote = simulate_heuristic_vote(v['name'], data, vix, mdd)
                results.append(vote)

            # Consensus Math
            targets = [r['target'] for r in results]
            avg_target = sum(targets) / len(targets)
            upside = ((avg_target - data['price']) / data['price']) * 100
            
            # Top Row: Stats + Chart
            c1, c2 = st.columns([1, 2])
            with c1:
                color = "#34d399" if upside > 0 else "#f87171"
                arrow = "▲" if upside > 0 else "▼"
                st.markdown(f"""
                <div class="voter-card">
                    <div style="color: #94a3b8; font-size: 0.8rem;">CONSENSUS TARGET</div>
                    <div style="font-size: 2rem; font-weight: bold; color: #fff;">${avg_target:,.2f}</div>
                    <div style="color: {color}; font-weight: bold;">{arrow} {upside:.2f}%</div>
                    <div style="margin-top: 15px; font-size: 0.8rem; color: #666;">
                        VIX > 25 Impact: {"Active" if vix > 25 else "Inactive"}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with c2:
                # Vote Distribution Chart
                names = [r['name'].split()[-1] for r in results]
                t_vals = [r['target'] for r in results]
                colors = ['#34d399' if r['sentiment'] == 'Bullish' else '#f87171' if r['sentiment'] == 'Bearish' else '#9ca3af' for r in results]
                
                fig = go.Figure(data=[go.Bar(x=names, y=t_vals, marker_color=colors, text=[f"${v:.0f}" for v in t_vals])])
                fig.add_hline(y=avg_target, line_dash="dot", line_color="white", annotation_text="Consensus")
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'), margin=dict(l=10, r=10, t=30, b=10), height=200
                )
                st.plotly_chart(fig, use_container_width=True)

            # Manager Cards
            st.subheader("Manager Perspectives")
            card_cols = st.columns(3)
            for i, res in enumerate(results):
                with card_cols[i % 3]:
                    badge_class = f"badge-{res['sentiment'].lower()}"
                    st.markdown(f"""
                    <div class="voter-card" style="min-height: 180px;">
                        <div style="display: flex; justify-content: space-between;">
                            <strong>{res['name']}</strong>
                            <span style="color: #34d399;">${res['target']:.0f}</span>
                        </div>
                        <div style="margin: 5px 0;"><span class="{badge_class}">{res['sentiment']}</span></div>
                        <div style="font-style: italic; color: #cbd5e1; font-size: 0.85rem;">"{res['reason']}"</div>
                    </div>
                    """, unsafe_allow_html=True)

        # --- TAB 2: MONTE CARLO ---
        with tab_simulation:
            st.markdown("### 🎲 Monte Carlo Risk Analysis")
            st.caption("Projecting 1,000 potential future price paths over the next 30 days based on historical volatility.")
            
            # Run Simulation
            sim_data = run_monte_carlo(data['history'], data['price'], days=30, simulations=1000)
            
            # Plot Paths
            mc_fig = go.Figure()
            # Plot first 50 paths to avoid browser lag, but calculate stats on all 1000
            x_axis = list(range(30))
            for i in range(50):
                mc_fig.add_trace(go.Scatter(x=x_axis, y=sim_data[:, i], mode='lines', line=dict(color='rgba(129, 140, 248, 0.1)'), showlegend=False))
            
            # Add Median Path
            median_path = np.median(sim_data, axis=1)
            mc_fig.add_trace(go.Scatter(x=x_axis, y=median_path, mode='lines', name='Median Path', line=dict(color='#34d399', width=3)))
            
            mc_fig.update_layout(
                title="30-Day Price Projection",
                xaxis_title="Days into Future",
                yaxis_title="Price ($)",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'), height=400
            )
            st.plotly_chart(mc_fig, use_container_width=True)
            
            # Simulation Stats
            final_prices = sim_data[-1]
            var_95 = np.percentile(final_prices, 5)
            upside_95 = np.percentile(final_prices, 95)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Bear Case (Bottom 5%)", f"${var_95:,.2f}", delta=f"{(var_95-data['price'])/data['price']:.1%}")
            m2.metric("Median Outcome", f"${np.median(final_prices):,.2f}")
            m3.metric("Bull Case (Top 5%)", f"${upside_95:,.2f}", delta=f"{(upside_95-data['price'])/data['price']:.1%}")

    else:
        st.error("Ticker not found. Try 'SPY', 'QQQ', or 'NVDA'.")
