import streamlit as st
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
# In a real deployed app, you would store these in st.secrets
# For this example, we keep it simple.
ACCESS_PASSWORD = "mysecretpassword"
DATA_FILE = "diary_log.json"
PAGE_TITLE = "The Inner Circle 🔒"
PAGE_ICON = "🤫"

# --- SETUP ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)

# --- FUNCTIONS ---

def load_messages():
    """Loads chat/diary entries from a local JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_message(author, text):
    """Saves a new message to the local JSON file."""
    messages = load_messages()
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "author": author,
        "text": text
    }
    messages.append(new_entry)
    with open(DATA_FILE, "w") as f:
        json.dump(messages, f, indent=4)

def check_password():
    """Returns True if the user has entered the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password_input"] == ACCESS_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # Clean up
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input
        st.text_input(
            "Enter the secret password:", 
            type="password", 
            on_change=password_entered, 
            key="password_input"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input again + error
        st.text_input(
            "Enter the secret password:", 
            type="password", 
            on_change=password_entered, 
            key="password_input"
        )
        st.error("😕 Access denied. Wrong password.")
        return False
    else:
        # Password correct
        return True

# --- MAIN APP LOGIC ---

if check_password():
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.caption("A shared space for close friends.")
    
    # Optional: Allow users to pick a nickname for this session
    if "author_name" not in st.session_state:
        st.session_state.author_name = "Anonymous"

    with st.sidebar:
        st.header("Settings")
        st.session_state.author_name = st.text_input("Your Nickname", value=st.session_state.author_name)
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    # --- DISPLAY CHAT HISTORY ---
    # Load messages fresh on every rerun so we see updates from others
    messages = load_messages()

    # Display loop
    for msg in messages:
        # Using Streamlit's chat_message UI component
        # We assume 'Anonymous' or specific names for avatars
        avatar = "👤"
        if msg['author'] == st.session_state.author_name:
            # Differentiate user's own messages visually if desired, 
            # though standard chat apps put user on right.
            # st.chat_message("user") puts it on the right with default styling.
            with st.chat_message("user"):
                st.write(msg['text'])
                st.caption(f"{msg['timestamp']}")
        else:
            with st.chat_message("assistant", avatar=avatar): # "assistant" style is just left-aligned
                st.write(f"**{msg['author']}**: {msg['text']}")
                st.caption(f"{msg['timestamp']}")

    # --- INPUT NEW MESSAGE ---
    # st.chat_input is fixed to the bottom of the screen
    if prompt := st.chat_input("Write something..."):
        save_message(st.session_state.author_name, prompt)
        st.rerun() # Rerun immediately to show the new message
