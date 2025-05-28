import streamlit as st
from components.ui_components import display_main_app_ui

# Import from new files
from config import _log, VALID_USERNAME, VALID_PASSWORD
from utils.auth import check_login, logout
from utils.excel_export import to_excel
from utils.session_state_manager import initialize_session_state

# --- Main App UI and Logic ---

# Initialize session state variables
initialize_session_state()

# --- Login Form ---
if not st.session_state.logged_in:
    st.title("🔒 Prihlásenie") # Slovak Title
    st.text_input("Meno", key="username", on_change=check_login)
    st.text_input("Heslo", type="password", key="password", on_change=check_login)
    # Placeholder to ensure the form is rendered before potential rerun
    st.empty()

# --- Main Application (Protected by Login) ---
else:
    # Add logout button to the sidebar or top
    with st.sidebar:
        st.write(f"Prihlásený ako: {VALID_USERNAME}") # Slovak Status
        st.button("Odhlásiť", on_click=logout) # Slovak Button
    
    display_main_app_ui()
