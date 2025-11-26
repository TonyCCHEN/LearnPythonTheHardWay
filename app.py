import streamlit as st
from PIL import Image
import io, base64, sqlite3, datetime
import os

# ---------- Config ----------
st.set_page_config(page_title="1BOX — Dimensional Stash", layout="wide", initial_sidebar_state="expanded")
DB_PATH = "1box_diablo.db"
GRID_ROWS = 6
GRID_COLS = 4

# ---------- Styles (Diablo-like theme) ----------
DIABLO_CSS = r"""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
<style>
/* page background & texture */
.stApp {
  background: radial-gradient(ellipse at bottom, rgba(8,12,16,0.85) 0%, rgba(6,10,14,1) 60%), url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="%230f1720" offset="0"/><stop stop-color="%23121a24" offset="1"/></linearGradient></defs><rect width="100%" height="100%" fill="url(%23g)"/><g opacity="0.06" fill="%23000"><circle cx="50" cy="50" r="80"/><circle cx="300" cy="300" r="120"/></g></svg>') no-repeat fixed center;
  color: #e7e7e7;
  font-family: "Roboto", Arial, sans-serif;
  -webkit-font-smoothing:antialiased;
}

/* Header / title */
.title {
  font-family: "Playfair Display", serif;
  font-weight: 900;
  font-size: 40px;
  color: #f6e9c9;
  letter-spacing: 1px;
  text-shadow: 0 2px 0 rgba(0,0,0,0.6), 0 6px 18px rgba(0,0,0,0.6);
}

/* gold framed stash container */
.stash-frame {
  border: 3px solid rgba(220,180,90,0.95);
  border-radius: 12px;
  padding: 14px;
  background: linear-gradient(180deg, rgba(255,255,255,0.015), rgba(0,0,0,0.08));
  box-shadow: 0 10px 30px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.03);
}

/* inventory grid */
.inv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
  gap: 12px;
  padding: 6px;
}

/* cell base */
.inv-cell {
  background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));
  border: 2px solid rgba(255,255,255,0.03);
  height: 96px;
  min-height: 96px;
  border-radius: 6px;
  display:flex;
  align-items:center;
  justify-content:center;
  position:relative;
  overflow:hidden;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

/* hover pop */
.inv-cell:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 14px 28px rgba(0,0,0,0.7), 0 0 18px rgba(255,230,150,0.03);
  z-index: 3;
}

/* image sizing */
.inv-cell img {
  max-width: 80%;
  max-height: 80%;
  object-fit: contain;
  border-radius: 4px;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,0.6));
}

/* badge for rare/epic/legend */
.item-badge {
  position:absolute;
  top:6px;
  left:6px;
  padding:4px 7px;
  font-size:11px;
  font-weight:700;
  border-radius:6px;
  color:#0f1012;
  text-transform:uppercase;
  letter-spacing:0.6px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.6), inset 0 -2px 0 rgba(255,255,255,0.06);
}

/* rarity colors */
.bad-common { background: rgba(200,200,200,0.95); color: #111; }
.bad-rare { background: linear-gradient(180deg,#6db8ff,#3b8bff); color: #02112a; }
.bad-epic { background: linear-gradient(180deg,#c77bff,#8a3bff); color: #140626; }
.bad-legend { background: linear-gradient(180deg,#ffd36a,#ff9b3b); color: #2b1a00; }

/* colored border for rarity */
.border-common { border-color: rgba(255,255,255,0.06); }
.border-rare { border-color: rgba(80,150,255,0.95); box-shadow: 0 6px 18px rgba(60,120,255,0.06); }
.border-epic { border-color: rgba(180,100,255,0.95); box-shadow: 0 6px 18px rgba(140,60,255,0.06); }
.border-legend { border-color: rgba(255,200,100,0.95); box-shadow: 0 6px 26px rgba(255,160,40,0.07); }

/* title small meta at bottom */
.cell-meta {
  position:absolute;
  bottom:6px;
  left:6px;
  right:6px;
  font-size:12px;
  color:#efe9df;
  background: linear-gradient(180deg, rgba(0,0,0,0.35), rgba(0,0,0,0.22));
  padding:4px 6px;
  border-radius:6px;
  display:flex;
  justify-content:space-between;
  align-items:center;
}

/* empty cell look */
.empty {
  color: rgba(255,255,255,0.12);
  font-weight:600;
  font-size:13px;
}

/* sparkle animation for legendary */
@keyframes sparkle {
  0% { transform: translateY(0) rotate(0) scale(1); opacity:1;}
  50% { transform: translateY(-6px) rotate(8deg) scale(1.03); opacity:0.95;}
  100% { transform: translateY(0) rotate(0) scale(1); opacity:1;}
}
.legend-spark {
  position:absolute;
  right:6px;
  top:6px;
  width:10px;
  height:10px;
  background: radial-gradient(circle at 30% 30%, #fff9d6 0%, #ffd36a 40%, #ff9b3b 100%);
  border-radius:50%;
  box-shadow: 0 0 10px rgba(255,180,80,0.9);
  animation: sparkle 2.6s ease-in-out infinite;
}

/* responsive adjustments */
@media (max-width: 700px) {
  .title { font-size: 28px; }
  .inv-cell { height: 84px; min-height: 84px; }
  .inv-grid { gap:10px; }
}
</style>
"""

st.markdown(DIABLO_CSS, unsafe_allow_html=True)

# ---------- DB helpers ----------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            remark TEXT,
            location TEXT,
            rarity TEXT,
            image BLOB,
            grid_row INTEGER, grid_col INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

conn = init_db()

def save_item(title, remark, location, rarity, img_bytes, row=None, col=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO items (title, remark, location, rarity, image, grid_row, grid_col, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, remark, location, rarity, img_bytes, row, col, datetime.datetime.now().isoformat()))
    conn.commit()
    return cur.lastrowid

def load_all_items():
    cur = conn.cursor()
    cur.execute("SELECT id, title, remark, location, rarity, image, grid_row, grid_col, created_at FROM items ORDER BY id")
    return cur.fetchall()

def delete_item(item_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()

def update_item_cell(item_id, row, col):
    cur = conn.cursor()
    cur.execute("UPDATE items SET grid_row=?, grid_col=? WHERE id=?", (row, col, item_id))
    conn.commit()

# ---------- Utilities ----------
def read_bytes(uploaded):
    return uploaded.read() if uploaded else None

def pil_from_bytes(b):
    return Image.open(io.BytesIO(b)).convert("RGBA")

def img_to_b64(b):
    return base64.b64encode(b).decode()

# ---------- Sidebar: capture ----------
st.sidebar.markdown("### 🧾 Capture New Item")
with st.sidebar.form("capture", clear_on_submit=False):
    title = st.text_input("Item Name", max_chars=60)
    remark = st.text_area("Short story / where kept", max_chars=250, height=80)
    location = st.text_input("Physical location (optional)")
    rarity = st.selectbox("Rarity", ["Common", "Rare", "Epic", "Legendary"])
    uploaded = st.file_uploader("Upload photo (png/jpg)", type=["png","jpg","jpeg"])
    cam = st.camera_input("Or take a photo")
    auto_place = st.checkbox("Auto-place to next free slot", value=True)
    submit = st.form_submit_button("💾 Save to 1BOX (Diablo Skin)")

if submit:
    img_bytes = None
    if uploaded:
        img_bytes = read_bytes(uploaded)
    elif cam:
        img_bytes = read_bytes(cam)

    if not title:
        st.sidebar.error("Please add a title.")
    elif img_bytes is None:
        st.sidebar.error("Please provide a photo.")
    else:
        # determine placement
        items = load_all_items()
        occ = {(it[6], it[7]) for it in items if it[6] is not None}
        assigned = (None, None)
        if auto_place:
            found = False
            for r in range(1, GRID_ROWS+1):
                for c in range(1, GRID_COLS+1):
                    if (r,c) not in occ:
                        assigned = (r,c)
                        found = True
                        break
                if found: break
        save_item(title, remark, location, rarity, img_bytes, assigned[0], assigned[1])
        st.sidebar.success(f"Saved! {'Placed at ('+str(assigned[0])+','+str(assigned[1])+')' if assigned[0] else 'Not placed (grid full)'}")

# ---------- Header ----------
col1, col2 = st.columns([4,1])
with col1:
    st.markdown('<div class="title">❄️ DIMENSIONAL STASH — 1BOX Memory Keeper</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#c9d3d9;margin-top:6px">Capture objects with photo + story. Diablo-themed skin enabled.</div>', unsafe_allow_html=True)
with col2:
    st.write("")

st.markdown("---")

# ---------- Build grid ----------
items = load_all_items()
grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
floating = []
for it in items:
    iid, t, rm, loc, rarity, img, row, col, created = it
    if row is not None and col is not None and 1 <= row <= GRID_ROWS and 1 <= col <= GRID_COLS:
        grid[row-1][col-1] = it
    else:
        floating.append(it)

# ---------- Stash frame and grid HTML ----------
st.markdown("### 🧰 Global Stash")
st.markdown('<div class="stash-frame">', unsafe_allow_html=True)

grid_html = '<div class="inv-grid">'
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        cell = grid[r][c]
        if cell is None:
            grid_html += f'''
            <div class="inv-cell border-common">
              <div class="empty">Empty</div>
            </div>
            '''
        else:
            iid, t, rm, loc, rarity, img, row, col, created = cell
            b64 = base64.b64encode(img).decode()
            # map rarity to classes
            rcls = {'Common':'border-common','Rare':'border-rare','Epic':'border-epic','Legendary':'border-legend'}.get(rarity, 'border-common')
            badge_cls = {'Common':'bad-common','Rare':'bad-rare','Epic':'bad-epic','Legendary':'bad-legend'}.get(rarity, 'bad-common')
            # small safe title
            safe_t = t.replace("<","").replace(">","")
            spark_html = '<div class="legend-spark"></div>' if rarity=='Legendary' else ''
            grid_html += f'''
            <div class="inv-cell {rcls}">
              <img src="data:image/png;base64,{b64}" />
              <div class="item-badge {badge_cls}">{rarity}</div>
              {spark_html}
              <div class="cell-meta"><div style="font-weight:700;">{safe_t}</div><div style="font-size:11px;color:#efe9df;opacity:0.9">{loc or ''}</div></div>
            </div>
            '''
grid_html += '</div>'
st.components.v1.html(grid_html, height=GRID_ROWS*110 + 40, scrolling=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Items list (details, move, delete) ----------
st.markdown("---")
st.markdown("### 📚 Items — Details & Actions")
for it in reversed(items):
    iid, t, rm, loc, rarity, img, row, col, created = it
    cols = st.columns([1, 3, 1])
    with cols[0]:
        st.image(Image.open(io.BytesIO(img)), width=92)
    with cols[1]:
        st.markdown(f"**{t}**  ")
        st.markdown(f"*{rm}*  ")
        st.markdown(f"**Location:** {loc or '—'}  ")
        st.markdown(f"**Rarity:** {rarity}  ")
        st.markdown(f"**Slot:** {f'({row},{col})' if row else 'Not placed'}  ")
        st.markdown(f"**Added:** {created[:19].replace('T',' ')}")
    with cols[2]:
        if st.button(f"Delete {iid}", key=f"del_{iid}"):
            delete_item(iid)
            st.experimental_rerun()
        with st.expander("Move / Place slot"):
            newr = st.number_input("Row", min_value=1, max_value=GRID_ROWS, value=row if row else 1, key=f"nr_{iid}")
            newc = st.number_input("Col", min_value=1, max_value=GRID_COLS, value=col if col else 1, key=f"nc_{iid}")
            if st.button("Place here", key=f"place_{iid}"):
                # occupancy check
                occupied = False
                for other in items:
                    if other[0] != iid and other[6]==newr and other[7]==newc:
                        occupied = True
                        break
                if occupied:
                    st.warning("Slot occupied.")
                else:
                    update_item_cell(iid, newr, newc)
                    st.experimental_rerun()

# floating unplaced
if floating:
    st.markdown("---")
    st.markdown("### 🧭 Unplaced items")
    for it in floating:
        iid, t, rm, loc, rarity, img, row, col, created = it
        fcols = st.columns([1,3,1])
        with fcols[0]:
            st.image(Image.open(io.BytesIO(img)), width=90)
        with fcols[1]:
            st.markdown(f"**{t}** — {rm}")
        with fcols[2]:
            if st.button(f"Auto-place {iid}", key=f"autop_{iid}"):
                curr = load_all_items()
                occ = {(x[6], x[7]) for x in curr if x[6] is not None}
                placed = False
                for rr in range(1, GRID_ROWS+1):
                    for cc in range(1, GRID_COLS+1):
                        if (rr,cc) not in occ:
                            update_item_cell(iid, rr, cc)
                            placed = True
                            break
                    if placed: break
                st.experimental_rerun()

st.markdown('<div style="margin-top:18px;color:#c8d2d8;font-size:13px">Tip: Legendary items get a sparkle. Use rarity to mark sentimental or important items.</div>', unsafe_allow_html=True)
