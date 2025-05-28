import streamlit as st
from datetime import datetime, timedelta

def initialize_session_state():
    """Initializes session state variables."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "nominal_durations" not in st.session_state:
        st.session_state.nominal_durations = {
            1: 60,
            2: 90,
            3: 120,
            4: 150,
            5: 200 # For 5+ speakers
        }
    
    if "speaker_availability_slots" not in st.session_state:
        st.session_state.speaker_availability_slots = {}
    
    if "recording_slots" not in st.session_state:
        st.session_state.recording_slots = []
        for i in range(6): # For today and next 5 days (total 6 days)
            current_date = (datetime.today() + timedelta(days=i)).strftime('%Y-%m-%d')
            st.session_state.recording_slots.append(f"{current_date} 09:00-17:00")

    if "show_apply_button" not in st.session_state:
        st.session_state.show_apply_button = False
