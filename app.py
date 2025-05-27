import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import logging
from io import BytesIO
from datetime import datetime
import json # Import json module

# Import functions from our modules
from converter import convert_and_chunk
from parser.core_parsing import parse_chunks_to_structured_data
from parser.constants import COLUMN_HEADERS
from analyzer.data_processing import process_parsed_data, get_unique_speakers
from analyzer.calculations import calculate_segment_times_by_speaker_count, calculate_total_speaker_time
from analyzer.scheduler import calculate_optimal_schedule, generate_calendar_view

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide", page_title="Analyzátor Dabingových Scenárov") # Slovak Title

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_log = logging.getLogger(__name__)

# --- Hardcoded Credentials (INSECURE - for demo only) ---
VALID_USERNAME = "andrej"
VALID_PASSWORD = "andrej123"

# --- Login Check Function ---
def check_login():
    """Checks credentials and updates session state."""
    if st.session_state["username"] == VALID_USERNAME and st.session_state["password"] == VALID_PASSWORD:
        st.session_state.logged_in = True
        del st.session_state["username"] # Clear credentials after check
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

# --- Helper Function for Excel Export ---
def to_excel(df: pd.DataFrame) -> bytes:
    """Converts a Pandas DataFrame to an Excel file in memory, ensuring index is the first column named 'Rečník'."""
    output = BytesIO()
    df_reset = df.reset_index()
    if not df_reset.empty:
        original_first_col_name = df_reset.columns[0]
        df_reset = df_reset.rename(columns={original_first_col_name: 'Rečník'})
        _log.info(f"Excel Export: Renamed first column '{original_first_col_name}' to 'Rečník'.")
    else:
        _log.warning("Excel Export: DataFrame is empty, cannot rename index column.")
        if df.index.name:
             df_reset[df.index.name] = []
             df_reset = df_reset.rename(columns={df.index.name: 'Rečník'})

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_reset.to_excel(writer, index=False, sheet_name='Matica_Rečník_Segment')
    processed_data = output.getvalue()
    return processed_data

# --- Main App UI and Logic ---

# Initialize session state for login status if not already present
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Initialize nominal durations in session state
if "nominal_durations" not in st.session_state:
    st.session_state.nominal_durations = {
        1: 60,
        2: 90,
        3: 120,
        4: 150,
        5: 200 # For 5+ speakers
    }

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

    st.title("🎬 Analyzátor Dabingových Scenárov") # Slovak Title

    st.markdown("""
    Nahrajte svoj dabingový scenár (ako súbor `.docx`) nižšie.
    Aplikácia vykoná nasledovné:
1.  Prekonvertuje a rozdelí dokument na časti (chunks).
2.  Analyzuje text na identifikáciu Rečníkov, Časových kódov, Dialógov, Označení scén a Označení segmentov.
3.  Zobrazí spracované dáta v tabuľke.
4.  Vygeneruje maticu zobrazujúcu, ktorý rečník sa objavuje v ktorom segmente.
5.  Umožní vám stiahnuť maticu Rečník-Segment ako súbor Excel.
""") # Slovak Instructions

    uploaded_file = st.file_uploader("Vyberte súbor DOCX", type="docx") # Slovak Label

    if uploaded_file is not None:
        st.info(f"Spracováva sa súbor: {uploaded_file.name}") # Slovak Status

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = Path(tmp_file.name)

        try:
            # --- Step 1: Convert and Chunk ---
            with st.spinner("Konvertujem a rozdeľujem dokument..."): # Slovak Spinner
                chunks = convert_and_chunk(tmp_file_path)

            if chunks is None:
                st.error("Nepodarilo sa konvertovať alebo rozdeliť dokument. Skontrolujte logy pre detaily.") # Slovak Error
            elif not chunks:
                st.warning("Dokument bol konvertovaný, ale neboli vygenerované žiadne textové časti (chunks).") # Slovak Warning
            else:
                st.success(f"Dokument úspešne rozdelený na {len(chunks)} častí.") # Slovak Success

                # --- Step 2: Parse Chunks ---
                with st.spinner("Spracovávam časti (chunks)..."): # Slovak Spinner
                    parsed_data_raw = parse_chunks_to_structured_data(chunks)

                # --- Clean parsed data: Replace None with '' ---
                parsed_data = []
                if parsed_data_raw:
                    for row_dict in parsed_data_raw:
                        cleaned_row = {k: (v if v is not None else '') for k, v in row_dict.items()}
                        parsed_data.append(cleaned_row)
                # --- End Cleaning ---

                if not parsed_data:
                    st.warning("Spracovanie dokončené, ale neboli extrahované žiadne štruktúrované dáta.") # Slovak Warning
                else:
                    st.success(f"Spracovanie dokončené. Extrahovaných {len(parsed_data)} riadkov.") # Slovak Success

                    # --- Step 2.5: Process Parsed Data with Analyzer ---
                    with st.spinner("Analyzujem štruktúrované dáta..."): # Slovak Spinner
                        df_processed = process_parsed_data(parsed_data, st.session_state.nominal_durations)

                    if df_processed.empty:
                        st.warning("Analýza dát nepriniesla žiadne spracované riadky.") # Slovak Warning
                    else:
                        st.success("Dáta úspešne analyzované a obohatené.") # Slovak Success

                        # --- Step 3: Display Parsed Data Table ---
                        st.header("Spracované Dáta Scenára") # Slovak Header
                        # Create DataFrame, explicitly setting dtype to str where possible
                        try:
                            df_display_raw = df_processed.copy()
                            # Rename columns for display
                            df_display = df_display_raw.rename(columns={
                                "Segment": "Segment",
                                "Speaker": "Rečník",
                                "Timecode": "Časový kód",
                                "Text": "Text",
                                "Scene Marker": "Označenie Scény",
                                "Segment Marker": "Označenie Segmentu",
                                "TimeInSeconds": "Čas v sekundách",
                                "NumSpeakersInSegment": "Počet rečníkov v segmente"
                            })
                            # Display using standard st.dataframe
                            st.dataframe(df_display, use_container_width=True)
                        except Exception as e:
                            _log.error(f"Error creating/casting main DataFrame for display: {e}.")
                            st.error("Chyba pri zobrazovaní spracovaných dát.")


                        # --- Step 4: Generate and Display Speaker-Segment Matrix ---
                        st.header("Matica Rečník-Segment") # Slovak Header
                        # Ensure 'Segment' column is treated as string for filtering if needed, then filter
                        df_parsed_str_segment = df_processed.copy()
                        df_parsed_str_segment['Segment'] = df_parsed_str_segment['Segment'].astype(str)

                        df_filtered = df_parsed_str_segment[
                            (df_parsed_str_segment['Speaker'] != '') &
                            (df_parsed_str_segment['Segment'].str.isdigit()) & # Check if string is digit
                            (df_parsed_str_segment['Segment'].astype(int) > 0) # Convert valid ones to int for comparison
                        ].copy()

                        if not df_filtered.empty:
                            # Convert Segment back to integer for crosstab
                            df_filtered['Segment'] = df_filtered['Segment'].astype(int)
                            try:
                                speaker_matrix = pd.crosstab(
                                    index=df_filtered['Speaker'],
                                    columns=df_filtered['Segment']
                                )
                                transformed_matrix = speaker_matrix.copy()
                                for segment_col in transformed_matrix.columns:
                                    # Ensure segment number is stored as string
                                    transformed_matrix[segment_col] = transformed_matrix[segment_col].apply(
                                        lambda count: str(segment_col) if count > 0 else ''
                                    )

                                # Display matrix - contains only strings now
                                st.dataframe(transformed_matrix, use_container_width=True)

                                # --- Step 5: Prepare Excel Download ---
                                excel_data = to_excel(transformed_matrix)
                                st.download_button(
                                    label="📥 Stiahnuť Maticu Rečník-Segment (Excel)", # Slovak Label
                                    data=excel_data,
                                    file_name=f"{Path(uploaded_file.name).stem}_matica_recnik_segment.xlsx", # Slovak Filename
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except Exception as e:
                                st.error(f"Chyba pri vytváraní matice rečníkov: {e}") # Slovak Error
                        else:
                            st.warning("Neboli nájdené žiadne dáta rečníkov v platných segmentoch na vytvorenie matice.") # Slovak Warning

                        # --- New Feature: Segment Time Analysis by Speaker Count ---
                        st.header("Analýza Času Segmentov Podľa Počtu Rečníkov") # Slovak Header
                        segment_times_by_speaker_count = calculate_segment_times_by_speaker_count(df_processed)
                        if segment_times_by_speaker_count:
                            for key, value in segment_times_by_speaker_count.items():
                                st.write(f"- Celkový čas pre {key.replace('_', ' ')}: {value:.2f} sekúnd")
                        else:
                            st.info("Žiadne dáta pre analýzu času segmentov podľa počtu rečníkov.")

                        # --- New Feature: Total Team Needed per Speaker ---
                        st.header("Celkový Čas Potrebný pre Každého Rečníka") # Slovak Header
                        total_speaker_times = calculate_total_speaker_time(df_processed)
                        if total_speaker_times:
                            for speaker, time in total_speaker_times.items():
                                st.write(f"- {speaker}: {time:.2f} sekúnd")
                        else:
                            st.info("Žiadne dáta pre celkový čas rečníkov.")

                        # Initialize nominal durations in session state
                        if "nominal_durations" not in st.session_state:
                            st.session_state.nominal_durations = {
                                1: 60,
                                2: 90,
                                3: 120,
                                4: 150,
                                5: 200 # For 5+ speakers
                            }
                        
                        # --- New Feature: Nominal Segment Durations ---
                        st.header("Nominálne Trvanie Segmentov") # Slovak Header
                        st.markdown("Zadajte nominálne trvanie segmentov v sekundách podľa počtu rečníkov:")

                        nominal_durations_inputs = {}
                        for i in range(1, 5): # For 1 to 4 speakers
                            nominal_durations_inputs[i] = st.number_input(
                                f"Segment s {i} rečníkom/rečníkmi (sekundy)",
                                min_value=1,
                                value=st.session_state.nominal_durations.get(i, 60),
                                key=f"nominal_duration_{i}"
                            )
                            st.session_state.nominal_durations[i] = nominal_durations_inputs[i]
                        
                        # For 5+ speakers
                        nominal_durations_inputs[5] = st.number_input(
                            "Segment s 5+ rečníkmi (sekundy)",
                            min_value=1,
                            value=st.session_state.nominal_durations.get(5, 200),
                            key="nominal_duration_5plus"
                        )
                        st.session_state.nominal_durations[5] = nominal_durations_inputs[5]

                        # --- New Feature: Speaker Availability and Optimal Plan ---
                        st.header("Dostupnosť Rečníkov a Optimálny Plán Nahrávania") # Slovak Header
                        
                        unique_speakers = get_unique_speakers(df_processed)
                        speaker_availability_inputs = {}

                        if unique_speakers:
                            st.markdown("Zadajte dostupné časové sloty pre každého rečníka:")
                            
                            # Initialize session state for speaker availability if not present
                            if "speaker_availability_slots" not in st.session_state:
                                st.session_state.speaker_availability_slots = {speaker: [f"{datetime.today().strftime('%Y-%m-%d')} 09:00-12:00", f"{datetime.today().strftime('%Y-%m-%d')} 13:00-17:00"] for speaker in unique_speakers}
                            
                            # Ensure all current unique speakers are in session state, add new ones with default slots
                            for speaker in unique_speakers:
                                if speaker not in st.session_state.speaker_availability_slots:
                                    st.session_state.speaker_availability_slots[speaker] = [f"{datetime.today().strftime('%Y-%m-%d')} 09:00-12:00", f"{datetime.today().strftime('%Y-%m-%d')} 13:00-17:00"]
                            # Remove speakers no longer in unique_speakers
                            speakers_to_remove = [s for s in st.session_state.speaker_availability_slots if s not in unique_speakers]
                            for s in speakers_to_remove:
                                del st.session_state.speaker_availability_slots[s]

                            speaker_availability_inputs = {} # This will hold the final, cleaned inputs for scheduler

                            # Allow user to select number of columns
                            num_cols = st.slider("Počet stĺpcov pre dostupnosť rečníkov", 1, 4, 2) # Slovak Label
                            cols = st.columns(num_cols)
                            col_idx = 0

                            for speaker in unique_speakers:
                                with cols[col_idx]:
                                    st.subheader(f"Dostupnosť pre {speaker}")
                                    current_slots = st.session_state.speaker_availability_slots.get(speaker, [])
                                    
                                    # Display current slots with delete buttons
                                    if current_slots:
                                        for i, slot in enumerate(current_slots):
                                            col1_inner, col2_inner = st.columns([0.7, 0.3])
                                            with col1_inner:
                                                st.write(f"- {slot}")
                                            with col2_inner:
                                                if st.button("Zmazať", key=f"delete_{speaker}_{i}"):
                                                    st.session_state.speaker_availability_slots[speaker].pop(i)
                                                    st.rerun()
                                    else:
                                        st.info("Žiadne časové sloty pridané.")

                                    # Input for new slot
                                    new_slot_key = f"new_slot_{speaker}"
                                    if new_slot_key not in st.session_state:
                                        st.session_state[new_slot_key] = f"{datetime.today().strftime('%Y-%m-%d')} 09:00-12:00"

                                    new_slot_value = st.text_input(
                                        "Pridať nový slot (YYYY-MM-DD HH:MM-HH:MM)", 
                                        value=st.session_state[new_slot_key], 
                                        key=new_slot_key
                                    )
                                    
                                    if st.button("Pridať Slot", key=f"add_slot_{speaker}"):
                                        # Regex for YYYY-MM-DD HH:MM-HH:MM
                                        if new_slot_value and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}-\d{2}:\d{2}", new_slot_value.strip()):
                                            st.session_state.speaker_availability_slots[speaker].append(new_slot_value.strip())
                                            st.session_state[new_slot_key] = f"{datetime.today().strftime('%Y-%m-%d')} 09:00-12:00" # Reset input
                                            st.rerun()
                                        else:
                                            st.error("Neplatný formát slotu. Použite YYYY-MM-DD HH:MM-HH:MM.")
                                    
                                    speaker_availability_inputs[speaker] = st.session_state.speaker_availability_slots[speaker]
                                
                                col_idx = (col_idx + 1) % num_cols # Move to next column
                        else:
                            st.info("Žiadni rečníci nájdení pre zadanie dostupnosti.")

                        # --- New Feature: Global Recording Days and Times ---
                        st.header("Globálne Časy Nahrávania") # Slovak Header
                        st.markdown("Zadajte dostupné globálne časové sloty pre nahrávanie (formát: YYYY-MM-DD HH:MM-HH:MM, jeden slot na riadok):")

                        if "recording_slots" not in st.session_state:
                            st.session_state.recording_slots = [f"{datetime.today().strftime('%Y-%m-%d')} 09:00-17:00"]
                        
                        recording_days_times = []
                        current_recording_slots = st.session_state.recording_slots

                        if current_recording_slots:
                            for i, slot in enumerate(current_recording_slots):
                                col1, col2 = st.columns([0.8, 0.2])
                                with col1:
                                    st.write(f"- {slot}")
                                with col2:
                                    if st.button("Zmazať", key=f"delete_rec_slot_{i}"):
                                        st.session_state.recording_slots.pop(i)
                                        st.rerun()
                        else:
                            st.info("Žiadne globálne časové sloty pre nahrávanie pridané.")

                        new_rec_slot_key = "new_recording_slot"
                        if new_rec_slot_key not in st.session_state:
                            st.session_state[new_rec_slot_key] = f"{datetime.today().strftime('%Y-%m-%d')} 09:00-17:00"

                        new_rec_slot_value = st.text_input(
                            "Pridať nový globálny slot (YYYY-MM-DD HH:MM-HH:MM)",
                            value=st.session_state[new_rec_slot_key],
                            key=new_rec_slot_key
                        )

                        if st.button("Pridať Globálny Slot", key="add_rec_slot"):
                            if new_rec_slot_value and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}-\d{2}:\d{2}", new_rec_slot_value.strip()):
                                st.session_state.recording_slots.append(new_rec_slot_value.strip())
                                st.session_state[new_rec_slot_key] = f"{datetime.today().strftime('%Y-%m-%d')} 09:00-17:00" # Reset input
                                st.rerun()
                            else:
                                st.error("Neplatný formát globálneho slotu. Použite YYYY-MM-DD HH:MM-HH:MM.")
                        
                        recording_days_times = st.session_state.recording_slots

                        # --- New Feature: Calendar View ---
                        st.header("Kalendár Dostupnosti Rečníkov a Nahrávania") # Slovak Header
                        num_days_to_show = st.slider("Počet dní na zobrazenie v kalendári", 1, 30, 7) # Slider for number of days
                        if unique_speakers or recording_days_times:
                            with st.spinner("Generujem kalendár..."): # Slovak Spinner
                                calendar_df = generate_calendar_view(
                                    unique_speakers, 
                                    speaker_availability_inputs, 
                                    recording_days_times,
                                    num_days_to_show=num_days_to_show
                                )
                            if not calendar_df.empty:
                                st.dataframe(calendar_df, use_container_width=True)
                            else:
                                st.info("Kalendár dostupnosti nebol vygenerovaný.")
                        else:
                            st.info("Žiadni rečníci alebo globálne časy nahrávania na zobrazenie v kalendári.")

                        # --- JSON Export/Import for Availability ---
                        st.header("Uložiť/Načítať Dostupnosť") # Slovak Header

                        # Export Button
                        export_data = {
                            "speaker_availability": st.session_state.speaker_availability_slots,
                            "recording_slots": st.session_state.recording_slots
                        }
                        json_export_str = json.dumps(export_data, indent=4)
                        st.download_button(
                            label="📥 Stiahnuť Dostupnosť (JSON)", # Slovak Label
                            data=json_export_str,
                            file_name="availability_config.json",
                            mime="application/json"
                        )

                        # Import Uploader
                        uploaded_json_file = st.file_uploader("Nahrať Dostupnosť (JSON)", type="json") # Slovak Label
                        if uploaded_json_file is not None:
                            try:
                                loaded_data = json.load(uploaded_json_file)
                                if "speaker_availability" in loaded_data and "recording_slots" in loaded_data:
                                    st.session_state.loaded_speaker_availability = loaded_data["speaker_availability"]
                                    st.session_state.loaded_recording_slots = loaded_data["recording_slots"]
                                    st.success("Dostupnosť úspešne načítaná z JSON súboru! Kliknite 'Použiť Načítané Dáta' pre aplikovanie.") # Slovak Success
                                    st.session_state.show_apply_button = True # Show the apply button
                                else:
                                    st.error("Neplatný formát JSON súboru. Očakáva sa 'speaker_availability' a 'recording_slots'.") # Slovak Error
                            except json.JSONDecodeError:
                                st.error("Chyba pri dekódovaní JSON súboru. Uistite sa, že je to platný JSON.") # Slovak Error
                            except Exception as e:
                                st.error(f"Nastala chyba pri načítaní JSON súboru: {e}") # Slovak Error
                        
                        if st.session_state.get("show_apply_button", False):
                            if st.button("Použiť Načítané Dáta"): # Slovak Button
                                st.session_state.speaker_availability_slots = st.session_state.loaded_speaker_availability
                                st.session_state.recording_slots = st.session_state.loaded_recording_slots
                                st.session_state.show_apply_button = False # Hide button after applying
                                st.rerun()

                        if st.button("Vypočítať Optimálny Plán Nahrávania"): # Slovak Button
                            if unique_speakers and speaker_availability_inputs:
                                with st.spinner("Vypočítavam optimálny plán..."): # Slovak Spinner
                                    optimal_schedule = calculate_optimal_schedule(df_processed, speaker_availability_inputs, recording_days_times)
                                
                                st.subheader("Navrhovaný Plán Nahrávania") # Slovak Subheader
                                if optimal_schedule and optimal_schedule.get("details"):
                                    for item in optimal_schedule["details"]:
                                        st.write(f"Segment {item['segment_id']} ({item['duration']:.2f}s) s rečníkmi {', '.join(item['speakers'])}: {item['status']}")
                                    if optimal_schedule.get("unassigned_segments"):
                                        st.warning(f"Nasledujúce segmenty neboli priradené: {', '.join(optimal_schedule['unassigned_segments'])}")
                                else:
                                    st.info("Optimálny plán nebol vygenerovaný alebo neobsahuje detaily.")
                            else:
                                st.warning("Nahrajte dokument a zadajte dostupnosť rečníkov pre výpočet plánu.")

        except Exception as e:
            st.error(f"Počas spracovania nastala neočakávaná chyba: {e}") # Slovak Error
            _log.exception("Nespracovaná chyba počas behu aplikácie:") # Log full traceback
        finally:
            # Clean up the temporary file
            if 'tmp_file_path' in locals() and tmp_file_path.exists():
                tmp_file_path.unlink()
                _log.info(f"Dočasný súbor zmazaný: {tmp_file_path}") # Slovak Log
    else: # Correctly indented else for 'if uploaded_file is not None:'
        st.info("Prosím, nahrajte súbor DOCX pre začatie.") # Slovak Info
