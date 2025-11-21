import datetime
import yfinance as yf
import pandas as pd

# --- CONFIGURATION ---
# Famous "Smart Money" funds we look for in the Top Holders list
SMART_MONEY_WATCHLIST = {
    "Vanguard Group": 0.85,        # High credibility for stability
    "Blackrock": 0.80,             # High credibility for flow
    "Berkshire Hathaway": 0.99,    # The Oracle (Highest)
    "State Street": 0.75,
    "Morgan Stanley": 0.70,
    "Goldman Sachs": 0.70,
    "Tiger Global": 0.90,          # Tech Specialist
    "Appaloosa": 0.95,             # Tepper
    "Duquesne": 0.95,              # Druckenmiller
    "Geode Capital": 0.65,
}

class Voter:
    """Base class for anyone 'voting' on the stock price."""
    def __init__(self, name, credibility_score):
        self.name = name
        self.credibility_score = credibility_score

class Analyst(Voter):
    """Sell-Side Analyst giving a specific Price Target."""
    def __init__(self, name, firm, credibility_score, price_target, rating_date):
        super().__init__(name, credibility_score)
        self.firm = firm
        self.price_target = price_target
        self.rating_date = rating_date

    def get_recency_weight(self):
        """Decay weight if the rating is old."""
        if not self.rating_date:
            return 0.5 # Penalize undated generic data
        
        days_old = (datetime.datetime.now() - self.rating_date).days
        if days_old < 30: return 1.0
        if days_old < 90: return 0.8
        return 0.5

class FundManager(Voter):
    """Buy-Side Manager 'voting' with capital allocation."""
    def __init__(self, name, fund_name, credibility_score, action, conviction_level):
        super().__init__(name, credibility_score)
        self.fund_name = fund_name
        self.action = action  # "BUY", "HOLD", "SELL" (Derived from holding size/presence)
        self.conviction_level = conviction_level 

class MarketDataProvider:
    """Fetches 'reachable' data using yfinance (Free)."""
    @staticmethod
    def get_real_data(ticker_symbol):
        print(f"\n📡 Connecting to Yahoo Finance for {ticker_symbol}...")
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Fetch Analyst Consensus & Targets
        try:
            info = stock.info
            current_price = info.get('currentPrice', 0.0)
            target_mean = info.get('targetMeanPrice', 0.0)
            target_high = info.get('targetHighPrice', 0.0)
            target_low = info.get('targetLowPrice', 0.0)
            num_analysts = info.get('numberOfAnalystOpinions', 0)
            print(f"   -> Price: ${current_price} | Consensus: ${target_mean} ({num_analysts} analysts)")
        except Exception as e:
            print(f"   ⚠️ Error fetching basic info: {e}")
            return None

        # 2. Fetch Institutional Holders (The 'Smart Money' Vote)
        holders_data = []
        try:
            # yfinance returns a DataFrame for institutional_holders
            inst_holders = stock.institutional_holders
            if inst_holders is not None and not inst_holders.empty:
                # Convert to list of dicts for easier processing
                # Columns usually: ['Holder', 'Shares', 'Date Reported', '% Out', 'Value']
                for index, row in inst_holders.iterrows():
                    holders_data.append({
                        "Holder": row.get('Holder', 'Unknown'),
                        "Pct_Held": row.get('% Out', 0),
                        "Shares": row.get('Shares', 0)
                    })
                print(f"   -> Found {len(holders_data)} major institutional holders.")
            else:
                print("   -> No institutional holder data available.")
        except Exception as e:
            print(f"   ⚠️ Error fetching holders: {e}")

        # 3. Fetch Recent Upgrades/Downgrades (Analyst Actions)
        recent_ratings = []
        try:
            upgrades = stock.upgrades_downgrades
            if upgrades is not None and not upgrades.empty:
                # Get last 5 ratings
                latest = upgrades.tail(5)
                for index, row in latest.iterrows():
                    recent_ratings.append({
                        "Firm": row.get('Firm', 'Unknown'),
                        "Action": row.get('Action', 'Unknown'),
                        "ToGrade": row.get('ToGrade', 'Unknown'),
                        "Date": index
                    })
                print(f"   -> Found recent analyst actions from: {', '.join([r['Firm'] for r in recent_ratings])}")
        except Exception as e:
            print(f"   ⚠️ Error fetching upgrades: {e}")

        return {
            "current_price": current_price,
            "targets": {"mean": target_mean, "high": target_high, "low": target_low},
            "holders": holders_data,
            "ratings": recent_ratings
        }

class SmartPriceEngine:
    def __init__(self, ticker):
        self.ticker = ticker
        self.current_price = 0.0
        self.analysts = []
        self.funds = []

    def load_real_data(self):
        data = MarketDataProvider.get_real_data(self.ticker)
        if not data:
            print("❌ Failed to load data.")
            return

        self.current_price = data["current_price"]
        targets = data["targets"]
        
        # --- 1. BUILD ANALYST VOTERS ---
        # We create "Composite Analysts" based on the High/Low/Mean data
        if targets["mean"] > 0:
            self.analysts.append(Analyst("Street Consensus", "Avg", 0.5, targets["mean"], datetime.datetime.now()))
        
        if targets["high"] > 0:
             # The "Bull" Analyst
            self.analysts.append(Analyst("Street High", "Optimistic", 0.7, targets["high"], datetime.datetime.now()))
            
        if targets["low"] > 0:
            # The "Bear" Analyst
            self.analysts.append(Analyst("Street Low", "Pessimistic", 0.7, targets["low"], datetime.datetime.now()))

        # Add specific recent ratings if available
        for r in data["ratings"]:
            # Estimate target based on grade (since yfinance doesn't give the exact target in this DF)
            # Buy = +15%, Hold = 0%, Sell = -15% relative to current price
            est_target = self.current_price
            credibility = 0.6
            
            grade = r["ToGrade"].lower()
            if "buy" in grade or "outperform" in grade or "overweight" in grade:
                est_target = self.current_price * 1.15
                credibility = 0.8
            elif "sell" in grade or "underperform" in grade:
                est_target = self.current_price * 0.85
                credibility = 0.8
            
            self.analysts.append(Analyst(f"Recent: {r['Firm']}", r['Firm'], credibility, est_target, r['Date']))

        # --- 2. BUILD FUND MANAGER VOTERS ---
        # We match the real holders against our "Smart Money Watchlist"
        for holder in data["holders"]:
            holder_name = holder["Holder"]
            
            # Check if this holder is in our watchlist (partial match)
            matched_smart_investor = None
            for smart_name, score in SMART_MONEY_WATCHLIST.items():
                if smart_name.lower() in holder_name.lower():
                    matched_smart_investor = (smart_name, score)
                    break
            
            if matched_smart_investor:
                name, score = matched_smart_investor
                # If they are in the top 10, it's a high conviction hold
                # We treat presence in Top 10 as a "BUY/HOLD" vote
                self.funds.append(FundManager(holder_name, name, score, "BUY", 0.8))
            else:
                # Generic Top Holder (lower credibility but still huge money)
                self.funds.append(FundManager(holder_name, "Institutional", 0.4, "BUY", 0.5))

    def calculate_smart_consensus(self):
        if self.current_price == 0:
            print("⚠️ No price data found. Exiting.")
            return

        print(f"\n\n--- 📊 CALCULATING SMART CONSENSUS FOR ${self.ticker} ---")
        print(f"Market Price: ${self.current_price:.2f}")

        # --- ANALYST CALCULATION ---
        total_weight = 0
        weighted_sum = 0
        
        print("\n[1] Sell-Side Analyst Votes:")
        for a in self.analysts:
            w = a.credibility_score * a.get_recency_weight()
            total_weight += w
            weighted_sum += (a.price_target * w)
            print(f"  • {a.name:<25} | Target: ${a.price_target:.2f} | Weight: {w:.2f}")
        
        if total_weight == 0: base_price = self.current_price
        else: base_price = weighted_sum / total_weight
        
        print(f">> Weighted Analyst Target: ${base_price:.2f}")

        # --- FUND MANAGER CALCULATION ---
        print("\n[2] Smart Money (Institutional) Votes:")
        if not self.funds:
            print("  (No major smart funds found in Top 10 holders)")
            sentiment_mod = 1.0
        else:
            bullish_power = 0
            total_power = 0
            
            for f in self.funds:
                # Presence in top holders is generally bullish
                power = f.credibility_score * f.conviction_level
                bullish_power += power
                total_power += f.credibility_score
                print(f"  • {f.name:<25} | {f.fund_name} | Impact: {power:.2f}")

            # Normalize score (0.0 to 1.0)
            # If lots of SMART money is present, score goes up.
            raw_sentiment = bullish_power / len(self.funds) # Average conviction
            
            # If raw sentiment is high (>0.6), we boost price. If low, we dampen.
            # Range: 0.90x (Dampener) to 1.10x (Booster)
            sentiment_mod = 0.90 + (raw_sentiment * 0.20) 

        final_price = base_price * sentiment_mod
        print(f"\n>> Institutional Modifier: {sentiment_mod:.3f}x")
        
        print(f"\n================================================")
        print(f"🎯 SMART FORECAST: ${final_price:.2f}")
        print(f"   vs Market Price: ${self.current_price:.2f}")
        print(f"================================================")

if __name__ == "__main__":
    # You can change the ticker here to test different stocks
    ticker_input = input("Enter Stock Ticker (e.g., TSM, NVDA, GOOGL): ").upper()
    if not ticker_input: ticker_input = "TSM"
    
    engine = SmartPriceEngine(ticker_input)
    engine.load_real_data()
    engine.calculate_smart_consensus()
