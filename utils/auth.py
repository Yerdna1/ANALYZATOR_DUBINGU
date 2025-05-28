import streamlit as st

from config import VALID_USERNAME, VALID_PASSWORD

# --- Login Check Function ---
def check_login():
    """Checks credentials and updates session state."""
    if st.session_state.get("username") == VALID_USERNAME and st.session_state.get("password") == VALID_PASSWORD:
        st.session_state.logged_in = True
        # Clear credentials after check, but only if they exist
        if "username" in st.session_state:
            del st.session_state["username"]
        if "password" in st.session_state:
            del st.session_state["password"]
        st.success("Prihlásený úspešne!") # Slovak Success
        st.rerun() # Rerun to show the main app
    else:
        st.error("Nesprávne meno alebo heslo.") # Slovak Error

# --- Logout Function ---
def logout():
    """Logs the user out."""
    st.session_state.logged_in = False
    st.info("Boli ste odhlásený.") # Slovak Info
    st.rerun()
