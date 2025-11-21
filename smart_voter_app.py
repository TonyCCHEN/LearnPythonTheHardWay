import streamlit as st
import datetime
import yfinance as yf
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Smart Price Voter", page_icon="🗳️", layout="wide")

# --- CONFIGURATION ---
SMART_MONEY_WATCHLIST = {
    "Vanguard Group": 0.85,
    "Blackrock": 0.80,
    "Berkshire Hathaway": 0.99,
    "State Street": 0.75,
    "Morgan Stanley": 0.70,
    "Goldman Sachs": 0.70,
    "Tiger Global": 0.90,
    "Appaloosa": 0.95,
    "Duquesne": 0.95,
    "Geode Capital": 0.65,
}

# --- CLASSES ---
class Voter:
    def __init__(self, name, credibility_score):
        self.name = name
        self.credibility_score = credibility_score

class Analyst(Voter):
    def __init__(self, name, firm, credibility_score, price_target, rating_date):
        super().__init__(name, credibility_score)
        self.firm = firm
        self.price_target = price_target
        self.rating_date = rating_date

    def get_recency_weight(self):
        if not self.rating_date:
            return 0.5
        days_old = (datetime.datetime.now() - self.rating_date).days
        if days_old < 30: return 1.0
        if days_old < 90: return 0.8
        return 0.5

class FundManager(Voter):
    def __init__(self, name, fund_name, credibility_score, action, conviction_level):
        super().__init__(name, credibility_score)
        self.fund_name = fund_name
        self.action = action 
        self.conviction_level = conviction_level 

class MarketDataProvider:
    @staticmethod
    def get_real_data(ticker_symbol):
        stock = yf.Ticker(ticker_symbol)
        try:
            info = stock.info
            current_price = info.get('currentPrice', 0.0)
            target_mean = info.get('targetMeanPrice', 0.0)
            target_high = info.get('targetHighPrice', 0.0)
            target_low = info.get('targetLowPrice', 0.0)
            num_analysts = info.get('numberOfAnalystOpinions', 0)
        except Exception:
            return None

        holders_data = []
        try:
            inst_holders = stock.institutional_holders
            if inst_holders is not None and not inst_holders.empty:
                for index, row in inst_holders.iterrows():
                    holders_data.append({
                        "Holder": row.get('Holder', 'Unknown'),
                        "Pct_Held": row.get('% Out', 0),
                        "Shares": row.get('Shares', 0)
                    })
        except Exception:
            pass

        recent_ratings = []
        try:
            upgrades = stock.upgrades_downgrades
            if upgrades is not None and not upgrades.empty:
                latest = upgrades.tail(5)
                for index, row in latest.iterrows():
                    recent_ratings.append({
                        "Firm": row.get('Firm', 'Unknown'),
                        "Action": row.get('Action', 'Unknown'),
                        "ToGrade": row.get('ToGrade', 'Unknown'),
                        "Date": index
                    })
        except Exception:
            pass

        return {
            "current_price": current_price,
            "targets": {"mean": target_mean, "high": target_high, "low": target_low, "count": num_analysts},
            "holders": holders_data,
            "ratings": recent_ratings
        }

class SmartPriceEngine:
    def __init__(self, ticker):
        self.ticker = ticker
        self.current_price = 0.0
        self.analysts = []
        self.funds = []
        self.raw_data = None

    def load_data(self):
        self.raw_data = MarketDataProvider.get_real_data(self.ticker)
        if not self.raw_data or self.raw_data['current_price'] == 0:
            return False
        
        self.current_price = self.raw_data["current_price"]
        targets = self.raw_data["targets"]
        
        # Build Composite Analysts
        if targets["mean"] > 0:
            self.analysts.append(Analyst("Street Consensus", "Avg", 0.5, targets["mean"], datetime.datetime.now()))
        if targets["high"] > 0:
            self.analysts.append(Analyst("Street High", "Optimistic", 0.7, targets["high"], datetime.datetime.now()))
        if targets["low"] > 0:
            self.analysts.append(Analyst("Street Low", "Pessimistic", 0.7, targets["low"], datetime.datetime.now()))

        # Build Specific Analysts
        for r in self.raw_data["ratings"]:
            est_target = self.current_price
            credibility = 0.6
            grade = str(r["ToGrade"]).lower()
            if "buy" in grade or "outperform" in grade or "overweight" in grade:
                est_target = self.current_price * 1.15
                credibility = 0.8
            elif "sell" in grade or "underperform" in grade:
                est_target = self.current_price * 0.85
                credibility = 0.8
            
            # Convert Pandas Timestamp to python datetime if needed
            rating_date = r['Date'].to_pydatetime() if isinstance(r['Date'], pd.Timestamp) else r['Date']
            self.analysts.append(Analyst(r['Firm'], "Recent Rating", credibility, est_target, rating_date))

        # Build Fund Managers
        for holder in self.raw_data["holders"]:
            holder_name = holder["Holder"]
            matched = None
            for smart_name, score in SMART_MONEY_WATCHLIST.items():
                if smart_name.lower() in holder_name.lower():
                    matched = (smart_name, score)
                    break
            
            if matched:
                name, score = matched
                self.funds.append(FundManager(holder_name, name, score, "BUY", 0.8))
            else:
                self.funds.append(FundManager(holder_name, "Institutional", 0.4, "BUY", 0.5))
        return True

    def calculate(self):
        # Analyst Weighted Avg
        total_weight = 0
        weighted_sum = 0
        analyst_details = []
        
        for a in self.analysts:
            w = a.credibility_score * a.get_recency_weight()
            total_weight += w
            weighted_sum += (a.price_target * w)
            analyst_details.append({
                "Source": f"{a.name} ({a.firm})",
                "Target": f"${a.price_target:.2f}",
                "Weight": f"{w:.2f}"
            })
        
        base_price = weighted_sum / total_weight if total_weight > 0 else self.current_price

        # Fund Manager Sentiment
        bullish_power = 0
        fund_details = []
        if not self.funds:
            sentiment_mod = 1.0
        else:
            for f in self.funds:
                power = f.credibility_score * f.conviction_level
                bullish_power += power
                fund_details.append({
                    "Fund": f"{f.name}",
                    "Type": f"{f.fund_name}",
                    "Impact": f"{power:.2f}"
                })
            
            raw_sentiment = bullish_power / len(self.funds)
            sentiment_mod = 0.90 + (raw_sentiment * 0.20)

        final_price = base_price * sentiment_mod
        
        return {
            "base_price": base_price,
            "final_price": final_price,
            "sentiment_mod": sentiment_mod,
            "analyst_details": analyst_details,
            "fund_details": fund_details,
            "raw_targets": self.raw_data["targets"]
        }

# --- UI LAYOUT ---
st.title("🗳️ Smart Price Voter")
st.markdown("""
This tool calculates a **Consensus Price Target** by weighting Analyst forecasts based on credibility 
and adjusting for **Smart Money** (Institutional) conviction.
""")

ticker = st.text_input("Enter Stock Ticker", value="TSM", max_chars=5).upper()

if st.button("Analyze Smart Forecast", type="primary"):
    engine = SmartPriceEngine(ticker)
    
    with st.spinner(f"Fetching data for {ticker}..."):
        success = engine.load_data()
    
    if not success:
        st.error(f"Could not fetch data for {ticker}. Please check the symbol.")
    else:
        result = engine.calculate()
        
        # Top Level Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${engine.current_price:.2f}")
        col2.metric("Smart Forecast", f"${result['final_price']:.2f}", 
                    delta=f"{(result['final_price'] - engine.current_price):.2f}")
        
        mod_delta = (result['sentiment_mod'] - 1.0) * 100
        col3.metric("Smart Money Modifier", f"{result['sentiment_mod']:.3f}x", 
                    delta=f"{mod_delta:.1f}%", delta_color="off")

        # Data Breakdown
        st.divider()
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("1. Analyst Votes (Sell-Side)")
            st.caption("Weighted by recency and historical accuracy.")
            if result['analyst_details']:
                st.dataframe(pd.DataFrame(result['analyst_details']), hide_index=True, use_container_width=True)
            else:
                st.info("No analyst targets found.")
            
            st.markdown(f"**Weighted Analyst Base:** ${result['base_price']:.2f}")

        with c2:
            st.subheader("2. Fund Manager Votes (Buy-Side)")
            st.caption("Top 10 Holders screened for 'Smart Money' funds.")
            if result['fund_details']:
                st.dataframe(pd.DataFrame(result['fund_details']), hide_index=True, use_container_width=True)
            else:
                st.warning("No major institutional holders found in Top 10.")

        # Explanation
        st.divider()
        st.subheader("📝 The Verdict")
        upside = ((result['final_price'] / engine.current_price) - 1) * 100
        
        if upside > 15:
            verdict = "STRONG BUY"
            color = "green"
        elif upside > 5:
            verdict = "ACCUMULATE"
            color = "blue"
        elif upside > -5:
            verdict = "HOLD"
            color = "orange"
        else:
            verdict = "TRIM / AVOID"
            color = "red"
            
        st.markdown(f"""
        Based on **{len(result['analyst_details'])} analyst inputs** and **{len(result['fund_details'])} institutional votes**, 
        the Smart Voter model suggests a target of **${result['final_price']:.2f}**.
        
        This represents a **{upside:.1f}%** potential move from current levels.
        
        **Rating:** :{color}[{verdict}]
        """)
