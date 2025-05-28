import streamlit as st
import logging

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide", page_title="Analyzátor Dabingových Scenárov") # Slovak Title

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_log = logging.getLogger(__name__)

# --- Hardcoded Credentials (INSECURE - for demo only) ---
VALID_USERNAME = "andrej"
VALID_PASSWORD = "andrej123"
