import streamlit as st
import time
import random
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="WorldView",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS to match the Dark Blue/Slate Aesthetic
# Streamlit allows us to inject CSS to override default styles
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    
    /* Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* News Card Styling */
    .news-card {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .news-card:hover {
        border-color: #475569;
        background-color: rgba(30, 41, 59, 0.9);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        color: #0f172a;
        margin-right: 8px;
    }
    .badge-conflict { background-color: #f87171; }
    .badge-env { background-color: #34d399; }
    .badge-culture { background-color: #a78bfa; }
    .badge-tech { background-color: #60a5fa; }
    
    /* Text Styles */
    .timestamp { color: #94a3b8; font-size: 0.8rem; }
    .source-tag { color: #64748b; font-size: 0.85rem; font-weight: 600; }
    .region-tag { color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
    
    /* Button Styling */
    div.stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #3b82f6;
        border-color: #3b82f6;
    }
    
    /* Divider */
    hr { margin: 2em 0; border-color: #334155; }
</style>
""", unsafe_allow_html=True)

# 3. Data Simulation (This is where you would normally fetch RSS feeds)
# In a real app, you would replace this function with `requests.get()` calls.
def fetch_news_data():
    """Simulates fetching fresh data from an API."""
    
    # Static data to start with (Real headlines from Nov 23, 2025)
    base_articles = [
        {
            "headline": "Israeli Airstrikes Renewed in Gaza Amidst Fragile Ceasefire",
            "summary": "Israel launched a series of airstrikes across the Gaza Strip on Saturday, November 22, resulting in the deaths of at least 24 people and injuring dozens more. The strikes mark a significant test for the ceasefire that began in October.",
            "source": "Combined Reports (NYT, ABC)",
            "region": "Middle East",
            "category": "Conflict",
            "cat_class": "badge-conflict",
            "time": "2 hrs ago"
        },
        {
            "headline": "US-Backed Ukraine Peace Plan Faces International Scrutiny",
            "summary": "A 28-point peace plan to end the Russia-Ukraine war, reportedly crafted by the incoming Trump administration, has drawn sharp criticism. Western leaders at the G20 summit indicated the plan might require 'additional work.'",
            "source": "The Guardian / DW News",
            "region": "Europe",
            "category": "Geopolitics",
            "cat_class": "badge-tech",
            "time": "4 hrs ago"
        },
        {
            "headline": "COP30 Climate Summit Concludes with Tentative Deal",
            "summary": "The 30th UN Climate Change Conference (COP30) in Belém, Brazil, concluded with an agreement to triple adaptation finance for developing countries by 2035, though it failed to explicitly mention a fossil fuel phase-out.",
            "source": "DW News / Straits Times",
            "region": "Americas/Global",
            "category": "Environment",
            "cat_class": "badge-env",
            "time": "6 hrs ago"
        },
        {
            "headline": "'A Foggy Tale' Sweeps Golden Horse Awards in Taiwan",
            "summary": "The film 'A Foggy Tale' won Best Narrative Feature at the 62nd Golden Horse Awards in Taipei. The event occurred against a backdrop of local news involving a rare security incident on the Taipei Metro.",
            "source": "PTS (公視) / NHK",
            "region": "Asia",
            "category": "Culture",
            "cat_class": "badge-culture",
            "time": "8 hrs ago"
        }
    ]
    
    # Simulate a random "Breaking News" update if we refresh
    if "last_fetch" in st.session_state:
        if random.random() > 0.5:
            base_articles.insert(0, {
                "headline": "BREAKING: G20 Leaders Issue Joint Statement on AI Safety",
                "summary": "In a surprise late-night announcement, G20 leaders have agreed to a new binding framework for Artificial Intelligence safety protocols. Markets in Asia have reacted positively.",
                "source": "Breaking Wire",
                "region": "Global",
                "category": "Technology",
                "cat_class": "badge-tech",
                "time": "Just now"
            })
    
    return base_articles

# 4. Session State Management
if 'news_data' not in st.session_state:
    st.session_state.news_data = fetch_news_data()
if 'last_fetch' not in st.session_state:
    st.session_state.last_fetch = datetime.now().strftime("%H:%M")

# 5. Sidebar - Sources
with st.sidebar:
    st.title("WorldView")
    st.caption("Daily Regional Recap")
    st.markdown("---")
    
    st.subheader("Active Sources")
    
    sources = {
        "Americas": ["NY Times (USA)", "ABC News (USA)", "TIME (USA)"],
        "Asia": ["Straits Times (SG)", "NHK (Japan)", "PTS (Taiwan)"],
        "Europe": ["The Guardian (UK)", "DW News (DE)"]
    }
    
    for region, outlets in sources.items():
        st.markdown(f"**{region}**")
        for outlet in outlets:
            st.markdown(f"🟢 <span style='color:#cbd5e1; font-size:0.9em'>{outlet}</span>", unsafe_allow_html=True)
        st.write("") # Spacer

    st.markdown("---")
    st.info("ℹ️ **AI Aggregation:** Summaries are generated using cross-verified data points from the listed sources.")

# 6. Main Content Area
col1, col2 = st.columns([3, 1])

with col1:
    st.title("Global Daily Briefing")
    # Calculate total sources dynamically so it matches the list (now 8 with TIME)
    total_sources = sum(len(v) for v in sources.values())
    st.markdown(f"Synthesized from **{total_sources} verified sources** across 3 continents.")

with col2:
    # The Update Button Logic
    st.write("") # Alignment spacer
    st.write("") 
    if st.button("🔄 Update Briefing"):
        with st.spinner('Fetching latest headlines...'):
            time.sleep(1.5) # Simulate network delay
            st.session_state.news_data = fetch_news_data()
            st.session_state.last_fetch = datetime.now().strftime("%H:%M")
            st.rerun()
    st.markdown(f"<div style='text-align: right; color: #64748b; font-size: 0.8em;'>Last updated: {st.session_state.last_fetch}</div>", unsafe_allow_html=True)

st.markdown("---")

# 7. Rendering the Articles
st.subheader("Top Headlines")

for article in st.session_state.news_data:
    # Using HTML/Markdown for the card design to get the specific look
    st.markdown(f"""
    <div class="news-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div>
                <span class="badge {article['cat_class']}">{article['category'].upper()}</span>
                <span class="timestamp">🕒 {article['time']}</span>
            </div>
            <span class="region-tag">{article['region']}</span>
        </div>
        <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.3em;">{article['headline']}</h3>
        <p style="color: #cbd5e1; line-height: 1.6;">{article['summary']}</p>
        <div style="border-top: 1px solid #334155; margin-top: 15px; padding-top: 10px; display: flex; justify-content: space-between;">
            <span class="source-tag">Sources: {article['source']}</span>
            <a href="#" style="color: #60a5fa; text-decoration: none; font-size: 0.9em;">Read Analysis →</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: #475569; margin-top: 40px; text-transform: uppercase; letter-spacing: 2px; font-size: 0.8em;">
    End of Briefing
</div>
""", unsafe_allow_html=True)
