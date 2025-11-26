import streamlit as st
from PIL import Image
import io
import sqlite3
import datetime
import base64
import pandas as pd

# -----------------------
# Config
# -----------------------
st.set_page_config(page_title="1BOX — Dimensional Stash", layout="wide", initial_sidebar_state="expanded")

DB_PATH = "1box.db"
GRID_ROWS = 6
GRID_COLS = 4  # 4 columns works well on mobile; user can change

# -----------------------
# Styles (Diablo-like dark theme)
# -----------------------
st.markdown(
    """
    <style>
    /* page background */
    .stApp {
      background: linear-gradient(180deg, #0f2230 0%, #122c3a 100%);
      color: #e6e6e6;
      font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }

    /* container boxes */
    .box {
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border: 2px solid rgba(255,255,255,0.03);
      border-radius: 10px;
      padding: 10px;
      box-shadow: 0 6px 18px rgba(0,0,0,0.6);
    }

    /* inventory grid */
    .inv-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
      gap: 12px;
    }

    .inv-cell {
      background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));
      border: 2px solid rgba(255,255,255,0.04);
      height: 96px;
      min-height: 96px;
      border-radius: 6px;
      display:flex;
      align-items:center;
      justify-content:center;
      position:relative;
      overflow:hidden;
    }

    .inv-cell img {
      max-width: 82%;
      max-height: 82%;
      object-fit:contain;
      border-radius: 4px;
    }

    .cell-meta {
      position:absolute;
      bottom:4px;
      left:4px;
      right:4px;
      font-size:11px;
      color:#d8d8d8;
      text-align:left;
      background: rgba(0,0,0,0.35);
      padding:4px 6px;
      border-radius:4px;
    }

    .cell-empty {
      opacity:0.18;
      font-size:13px;
      color:#bfc9d3;
    }

    /* action buttons */
    .btn {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.06);
      color:#eaeaea;
      padding:8px 12px;
      border-radius:8px;
      margin-right:8px;
    }

    /* small notes */
    .muted {
      color:#b7c0c7;
      font-size:13px;
    }

    /* make grid responsive for narrow screens (phones) */
    @media (max-width: 600px) {
      .inv-cell { height: 84px; min-height: 84px; }
      .inv-grid { gap:10px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Database helpers
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            remark TEXT,
            location TEXT,
            image BLOB,
            grid_row INTEGER,
            grid_col INTEGER,
            created_at TEXT
        )
        """
    )
    conn.commit()
    return conn

conn = init_db()

def save_item(title, remark, location, image_bytes, row=None, col=None):
    now = datetime.datetime.now().isoformat()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO items (title, remark, location, image, grid_row, grid_col, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, remark, location, image_bytes, row, col, now),
    )
    conn.commit()
    return cur.lastrowid

def delete_item(item_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()

def load_all_items():
    cur = conn.cursor()
    cur.execute("SELECT id, title, remark, location, image, grid_row, grid_col, created_at FROM items ORDER BY id")
    return cur.fetchall()

def update_item_cell(item_id, row, col):
    cur = conn.cursor()
    cur.execute("UPDATE items SET grid_row = ?, grid_col = ? WHERE id = ?", (row, col, item_id))
    conn.commit()

# -----------------------
# Utilities
# -----------------------
def img_bytes_from_upload(uploaded_file):
    if uploaded_file is None:
        return None
    return uploaded_file.read()

def pil_from_bytes(b):
    return Image.open(io.BytesIO(b))

def bytes_to_base64(b):
    return base64.b64encode(b).decode()

# -----------------------
# Sidebar: Capture form
# -----------------------
st.sidebar.markdown("## ✨ Capture New Item")
with st.sidebar.form("capture_form", clear_on_submit=False):
    new_title = st.text_input("Item title", max_chars=50)
    new_remark = st.text_area("Short remark / story (where, when, why)", max_chars=250, height=80)
    new_location = st.text_input("Physical location (e.g., 'kitchen drawer', 'box A')", placeholder="Where did you place it?")
    uploaded_img = st.file_uploader("Upload photo (JPG/PNG)", type=["jpg", "jpeg", "png"])
    cam_img = st.camera_input("Or take a photo with camera")
    col1, col2 = st.columns([1,1])
    with col1:
        auto_place = st.checkbox("Auto-place to next free slot", value=True)
    with col2:
        select_slot = st.checkbox("Choose a specific slot", value=False)
    # if user chooses a specific slot we show selectors
    if select_slot:
        pick_row = st.number_input("Slot row (1-index)", min_value=1, max_value=GRID_ROWS, value=1)
        pick_col = st.number_input("Slot col (1-index)", min_value=1, max_value=GRID_COLS, value=1)
    else:
        pick_row = None
        pick_col = None

    submitted = st.form_submit_button("💾 Save to 1BOX")

# Save handling
if submitted:
    image_bytes = None
    if uploaded_img is not None:
        image_bytes = img_bytes_from_upload(uploaded_img)
    elif cam_img is not None:
        image_bytes = img_bytes_from_upload(cam_img)

    if not new_title:
        st.sidebar.error("Please provide an item title.")
    elif image_bytes is None:
        st.sidebar.error("Please upload or capture a photo.")
    else:
        # determine placement
        items = load_all_items()
        occupied = {(r, c): item for (item_id, t, rm, loc, im, r, c, ts) in items for (r, c, item) in [((r, c), item_id)] if r is not None}
        # simpler method: build set of occupied coordinates
        occ_coords = set()
        for (item_id, t, rm, loc, im, r, c, ts) in items:
            if r is not None and c is not None:
                occ_coords.add((r, c))

        assigned_row, assigned_col = None, None
        if select_slot and pick_row and pick_col:
            if (pick_row, pick_col) in occ_coords:
                st.sidebar.error("That slot is already occupied. Either auto-place or choose another slot.")
            else:
                assigned_row, assigned_col = int(pick_row), int(pick_col)
        elif auto_place:
            # find first empty in row-major order
            found = False
            for rr in range(1, GRID_ROWS + 1):
                for cc in range(1, GRID_COLS + 1):
                    if (rr, cc) not in occ_coords:
                        assigned_row, assigned_col = rr, cc
                        found = True
                        break
                if found:
                    break
            if not found:
                # grid full -> allow save but with no slot (will be in list)
                assigned_row, assigned_col = None, None
        else:
            assigned_row, assigned_col = None, None

        save_item(new_title, new_remark, new_location, image_bytes, assigned_row, assigned_col)
        st.sidebar.success("Saved to 1BOX!" + (f" Placed at ({assigned_row},{assigned_col})." if assigned_row else ""))

# -----------------------
# Top header
# -----------------------
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("## 🧊 1BOX — Dimensional Stash")
    st.markdown('<div class="muted">Capture objects with a photo + short story. Mobile-friendly, Diablo-style grid.</div>', unsafe_allow_html=True)
with col2:
    st.write("")  # keep some space

st.markdown("---")

# -----------------------
# Load items and build grid data structure
# -----------------------
items = load_all_items()  # each: id, title, remark, location, image, row, col, created_at

grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
free_slots = []
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        free_slots.append((r+1, c+1))
# place items into grid if they have coords
floating_items = []  # items without assigned slot
for item in items:
    item_id, title, remark, location, image, row, col, created_at = item
    if row is not None and col is not None:
        if 1 <= row <= GRID_ROWS and 1 <= col <= GRID_COLS:
            grid[row-1][col-1] = item
            if (row, col) in free_slots:
                free_slots.remove((row, col))
    else:
        floating_items.append(item)

# -----------------------
# Sidebar: actions & export
# -----------------------
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔧 Actions")
if st.sidebar.button("Export items as CSV (images base64)"):
    # prepare dataframe
    df_rows = []
    for item in items:
        item_id, title, remark, location, image, row, col, created_at = item
        b64 = base64.b64encode(image).decode() if image else ""
        df_rows.append({
            "id": item_id,
            "title": title,
            "remark": remark,
            "location": location,
            "grid_row": row,
            "grid_col": col,
            "created_at": created_at,
            "image_base64": b64
        })
    df = pd.DataFrame(df_rows)
    csv = df.to_csv(index=False).encode()
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="1box_export.csv">Download CSV</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

# -----------------------
# Inventory Grid UI
# -----------------------
st.markdown("### 🎛️ Global Stash — Inventory Grid")
st.markdown('<div class="box">', unsafe_allow_html=True)

# Build grid HTML
grid_html = '<div class="inv-grid">'
cell_index = 0
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        cell = grid[r][c]
        if cell is None:
            grid_html += f'''
            <div class="inv-cell">
                <div class="cell-empty">Empty</div>
            </div>
            '''
        else:
            item_id, title, remark, location, image, row_v, col_v, created_at = cell
            b64 = base64.b64encode(image).decode()
            safe_title = st._sanitize_html(title)
            # include a tiny caption overlay
            grid_html += f'''
            <div class="inv-cell">
                <img src="data:image/png;base64,{b64}" />
                <div class="cell-meta"><strong>{safe_title}</strong></div>
            </div>
            '''
grid_html += '</div>'

st.components.v1.html(grid_html, height=GRID_ROWS * 110 + 40, scrolling=True)

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# View item list with actions (tap to open / delete / move)
# -----------------------
st.markdown("---")
st.markdown("### 📚 Items List & Details")
for item in items[::-1]:  # newest first
    item_id, title, remark, location, image, row, col, created_at = item
    cols = st.columns([1, 3, 1])
    with cols[0]:
        st.image(Image.open(io.BytesIO(image)), width=100)
    with cols[1]:
        st.markdown(f"**{title}**  ")
        st.markdown(f"*{remark}*  ")
        st.markdown(f"**Location:** {location if location else '—'}  ")
        st.markdown(f"**Slot:** {f'({row},{col})' if row else 'Not placed'}  ")
        st.markdown(f"**Added:** {created_at[:19].replace('T',' ')}")
    with cols[2]:
        if st.button(f"View → {item_id}", key=f"view_{item_id}"):
            st.session_state[f"open_{item_id}"] = True
        if st.button(f"Delete ✖ {item_id}", key=f"del_{item_id}"):
            delete_item(item_id)
            st.experimental_rerun()
        # move controls
        with st.expander("Move / Place slot"):
            newr = st.number_input("Row (1-index)", min_value=1, max_value=GRID_ROWS, value=row if row else 1, key=f"move_r_{item_id}")
            newc = st.number_input("Col (1-index)", min_value=1, max_value=GRID_COLS, value=col if col else 1, key=f"move_c_{item_id}")
            if st.button("Place here", key=f"place_{item_id}"):
                # check occupancy by other items
                occupied = False
                for it in items:
                    if it[0] != item_id and it[5] == newr and it[6] == newc:
                        occupied = True
                        break
                if occupied:
                    st.warning("That slot is occupied. Choose another.")
                else:
                    update_item_cell(item_id, newr, newc)
                    st.experimental_rerun()

    # show details in collapse if requested
    if st.session_state.get(f"open_{item_id}", False):
        with st.expander(f"Details — {title}", expanded=True):
            st.image(Image.open(io.BytesIO(image)), width=240)
            st.write("**Remark:**", remark)
            st.write("**Location:**", location)
            st.write("**Slot:**", f"({row},{col})" if row else "Not placed")
            if st.button("Close", key=f"close_{item_id}"):
                st.session_state[f"open_{item_id}"] = False

# Floating unplaced items notice
if floating_items:
    st.markdown("---")
    st.markdown("### 🧭 Unplaced items (not assigned to any grid slot)")
    for item in floating_items:
        item_id, title, remark, location, image, row, col, created_at = item
        cols = st.columns([1, 3, 1])
        with cols[0]:
            st.image(Image.open(io.BytesIO(image)), width=90)
        with cols[1]:
            st.markdown(f"**{title}** — {remark}  ")
            st.markdown(f"Location: {location}")
        with cols[2]:
            if st.button(f"Place item {item_id}", key=f"placefloat_{item_id}"):
                # find first free
                curr_items = load_all_items()
                occ = {(it[5], it[6]) for it in curr_items if it[5] is not None}
                placed = False
                for rr in range(1, GRID_ROWS+1):
                    for cc in range(1, GRID_COLS+1):
                        if (rr, cc) not in occ:
                            update_item_cell(item_id, rr, cc)
                            placed = True
                            break
                    if placed:
                        break
                st.experimental_rerun()

st.markdown("---")
st.markdown('<div class="muted">Tip: On mobile, use the camera capture to quickly snap an item, write a short remark, and check "Auto-place".</div>', unsafe_allow_html=True)
