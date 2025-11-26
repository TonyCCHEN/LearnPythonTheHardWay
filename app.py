# --- DIABLO UI SKIN -------------------------------------------------------
st.markdown("""
<style>

/* --- GLOBAL PAGE --- */
body, .stApp {
    background-color: #0f0f0f;
    color: #e5d5a3;
    font-family: 'Cinzel', serif;
}

/* --- TITLE --- */
h1, h2, h3, h4 {
    color: #e9d8a6 !important;
    text-shadow: 0 0 8px rgba(255,200,100,0.35);
    font-family: 'Cinzel', serif;
}

/* LEFT SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f0f, #1a1a1a);
    border-right: 2px solid rgba(255,200,100,0.15);
}

/* --- STASH FRAME --- */
.stash-frame {
    border: 3px solid rgba(220,180,90,0.95);
    border-radius: 12px;
    padding: 14px;
    background: #111;
    box-shadow: 0 0 24px rgba(255,200,120,0.15);
}

/* --- INVENTORY GRID --- */
.inv-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
    gap: 8px;
}

/* --- INVENTORY CELL --- */
.inv-cell {
    background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0));
    border: 1px solid rgba(255,220,140,0.25);
    border-radius: 6px;
    height: 92px;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: 0.12s ease-in-out;
}

.inv-cell:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 18px rgba(255,200,120,0.25);
}

/* --- ITEM IMAGE --- */
.inv-cell img {
    max-width: 80%;
    max-height: 80%;
    object-fit: contain;
}

/* --- BADGES (RARITY COLORS) --- */
.bad-common { color: #cccccc; }
.bad-rare   { color: #6ba8ff; }
.bad-epic   { color: #d36bff; }
.bad-legend { color: #ffdd66; text-shadow: 0 0 8px rgba(255,220,120,0.6); }

/* --- ITEM NAME BELOW --- */
.item-meta {
    text-align: center;
    font-size: 12px;
    margin-top: 6px;
    color: #e5d5a3;
}

</style>
""", unsafe_allow_html=True)
# -------------------------------------------------------------------------
