import streamlit as st
import sqlite3
from PIL import Image
import io
import base64
import datetime

st.set_page_config(page_title="1BOX Memory Stash", layout="wide")

# ------------------------------
# Database Setup
# ------------------------------
def init_db():
    conn = sqlite3.connect("1box.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            remark TEXT,
            image BLOB,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

conn = init_db()

def save_item(title, remark, image_bytes):
    conn.execute("INSERT INTO items (title, remark, image, created_at) VALUES (?, ?, ?, ?)",
                 (title, remark, image_bytes, datetime.datetime.now().isoformat()))
    conn.commit()

def load_items():
    cursor = conn.execute("SELECT id, title, remark, image, created_at FROM items ORDER BY id DESC")
    return cursor.fetchall()

# ------------------------------
# UI Title
# ------------------------------
st.markdown("""
# 🧊 DIMENSIONAL STASH — 1BOX Memory Keeper  
Capture anything with a photo + story so you never forget where things are.
""")

# ------------------------------
# Sidebar Input Form
# ------------------------------
st.sidebar.header("📥 Capture New Item")

title = st.sidebar.text_input("Item Name")
remark = st.sidebar.text_area("Short Story / Remark (Where you keep it?)")
uploaded_img = st.sidebar.file_uploader("Upload Photo", type=["png", "jpg", "jpeg"])
camera_img = st.sidebar.camera_input("Or take a photo")

save_btn = st.sidebar.button("💾 Save to 1BOX")

# Get image bytes
image_bytes = None
if uploaded_img:
    image_bytes = uploaded_img.read()
elif camera_img:
    image_bytes = camera_img.read()

# Save logic
if save_btn:
    if not title:
        st.sidebar.error("❗ Please enter a title.")
    elif not image_bytes:
        st.sidebar.error("❗ Please upload or take a photo.")
    else:
        save_item(title, remark, image_bytes)
        st.sidebar.success("✅ Saved into 1BOX!")

# ------------------------------
# Main Inventory Grid
# ------------------------------
st.subheader("📦 Global Stash (Your Items)")

items = load_items()

if len(items) == 0:
    st.info("Start by adding your first item from the sidebar!")
else:
    cols = st.columns(4)
    for idx, item in enumerate(items):
        id_, title, remark, image_data, timestamp = item
        img = Image.open(io.BytesIO(image_data))

        with cols[idx % 4]:
            st.image(img, use_column_width=True)
            st.markdown(f"**{title}**")
            st.caption(remark)
            st.caption(f"📅 {timestamp[:10]}")

# ------------------------------
# Search Function
# ------------------------------
st.markdown("---")
st.subheader("🔍 Search Your Stash")

query = st.text_input("Search by name or remark...")

if query:
    results = [i for i in items if query.lower() in i[1].lower() or query.lower() in i[2].lower()]
    st.write(f"Found {len(results)} items:")

    for item in results:
        id_, title, remark, image_data, timestamp = item
        img = Image.open(io.BytesIO(image_data))
        st.image(img, width=150)
        st.write(f"**{title}** — {remark}")

