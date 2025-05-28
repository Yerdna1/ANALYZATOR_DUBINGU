import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import json
import re
from datetime import datetime, timedelta

from converter import convert_and_chunk
from parser.core_parsing import parse_chunks_to_structured_data
from analyzer.data_processing import process_parsed_data, get_unique_speakers
from analyzer.calculations import calculate_segment_times_by_speaker_count, calculate_total_speaker_time
from analyzer.scheduler.core import calculate_optimal_schedule
from analyzer.scheduler.calendar import generate_calendar_view
from analyzer.scheduler.summary import summarize_speaker_schedule

from config import _log
from utils.excel_export import to_excel

def process_uploaded_file(uploaded_file):
    """Processes the uploaded DOCX file and returns processed data."""
    st.info(f"Spracováva sa súbor: {uploaded_file.name}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = Path(tmp_file.name)

    try:
        with st.spinner("Konvertujem a rozdeľujem dokument..."):
            chunks = convert_and_chunk(tmp_file_path)

        if chunks is None:
            st.error("Nepodarilo sa konvertovať alebo rozdeliť dokument. Skontrolujte logy pre detaily.")
            return None
        elif not chunks:
            st.warning("Dokument bol konvertovaný, ale neboli vygenerované žiadne textové časti (chunks).")
            return None
        else:
            st.success(f"Dokument úspešne rozdelený na {len(chunks)} častí.")

            with st.spinner("Spracovávam časti (chunks)..."):
                parsed_data_raw = parse_chunks_to_structured_data(chunks)

            parsed_data = []
            if parsed_data_raw:
                for row_dict in parsed_data_raw:
                    cleaned_row = {k: (v if v is not None else '') for k, v in row_dict.items()}
                    parsed_data.append(cleaned_row)

            if not parsed_data:
                st.warning("Spracovanie dokončené, ale neboli extrahované žiadne štruktúrované dáta.")
                return None
            else:
                st.success(f"Spracovanie dokončené. Extrahovaných {len(parsed_data)} riadkov.")

                with st.spinner("Analyzujem štruktúrované dáta..."):
                    df_processed = process_parsed_data(parsed_data, st.session_state.nominal_durations)

                if df_processed.empty:
                    st.warning("Analýza dát nepriniesla žiadne spracované riadky.")
                    return None
                else:
                    st.success("Dáta úspešne analyzované a obohatené.")
                    return df_processed
    except Exception as e:
        st.error(f"Počas spracovania nastala neočakávaná chyba: {e}")
        _log.exception("Nespracovaná chyba počas behu aplikácie:")
        return None
    finally:
        if 'tmp_file_path' in locals() and tmp_file_path.exists():
            tmp_file_path.unlink()
            _log.info(f"Dočasný súbor zmazaný: {tmp_file_path}")

def display_parsed_data_table(df_processed):
    """Displays the processed data in a table."""
    st.header("Spracované Dáta Scenára")
    try:
        df_display_raw = df_processed.copy()
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
        st.dataframe(df_display, use_container_width=True)
    except Exception as e:
        _log.error(f"Error creating/casting main DataFrame for display: {e}.")
        st.error("Chyba pri zobrazovaní spracovaných dát.")

def display_speaker_segment_matrix(df_processed, uploaded_file_name):
    """Generates and displays the speaker-segment matrix with download option."""
    st.header("Matica Rečník-Segment")
    df_parsed_str_segment = df_processed.copy()
    df_parsed_str_segment['Segment'] = df_parsed_str_segment['Segment'].astype(str)

    df_filtered = df_parsed_str_segment[
        (df_parsed_str_segment['Speaker'] != '') &
        (df_parsed_str_segment['Segment'].str.isdigit()) &
        (df_parsed_str_segment['Segment'].astype(int) > 0)
    ].copy()

    if not df_filtered.empty:
        df_filtered['Segment'] = df_filtered['Segment'].astype(int)
        try:
            speaker_matrix = pd.crosstab(
                index=df_filtered['Speaker'],
                columns=df_filtered['Segment']
            )
            transformed_matrix = speaker_matrix.copy()
            for segment_col in transformed_matrix.columns:
                transformed_matrix[segment_col] = transformed_matrix[segment_col].apply(
                    lambda count: str(segment_col) if count > 0 else ''
                )
            st.dataframe(transformed_matrix, use_container_width=True)

            excel_data = to_excel(transformed_matrix)
            st.download_button(
                label="📥 Stiahnuť Maticu Rečník-Segment (Excel)",
                data=excel_data,
                file_name=f"{Path(uploaded_file_name).stem}_matica_recnik_segment.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Chyba pri vytváraní matice rečníkov: {e}")
    else:
        st.warning("Neboli nájdené žiadne dáta rečníkov v platných segmentoch na vytvorenie matice.")

def display_segment_time_analysis(df_processed):
    """Displays segment time analysis by speaker count."""
    st.header("Analýza Času Segmentov Podľa Počtu Rečníkov")
    segment_times_by_speaker_count = calculate_segment_times_by_speaker_count(df_processed)
    if segment_times_by_speaker_count:
        for key, value in segment_times_by_speaker_count.items():
            st.write(f"- Celkový čas pre {key.replace('_', ' ')}: {value:.2f} sekúnd")
    else:
        st.info("Žiadne dáta pre analýzu času segmentov podľa počtu rečníkov.")

def display_total_speaker_time(df_processed):
    """Displays total time needed per speaker."""
    st.header("Celkový Čas Potrebný pre Každého Rečníka")
    total_speaker_times = calculate_total_speaker_time(df_processed)
    if total_speaker_times:
        for speaker, time in total_speaker_times.items():
            st.write(f"- {speaker}: {time:.2f} sekúnd")
    else:
        st.info("Žiadne dáta pre celkový čas rečníkov.")

def configure_nominal_durations():
    """Allows user to configure nominal segment durations."""
    st.header("Nominálne Trvanie Segmentov")
    st.markdown("Zadajte nominálne trvanie segmentov v sekundách podľa počtu rečníkov:")

    for i in range(1, 5):
        st.session_state.nominal_durations[i] = st.number_input(
            f"Segment s {i} rečníkom/rečníkmi (sekundy)",
            min_value=1,
            value=st.session_state.nominal_durations.get(i, 60),
            key=f"nominal_duration_{i}"
        )
    
    st.session_state.nominal_durations[5] = st.number_input(
        "Segment s 5+ rečníkmi (sekundy)",
        min_value=1,
        value=st.session_state.nominal_durations.get(5, 200),
        key="nominal_duration_5plus"
    )

def manage_speaker_availability(unique_speakers):
    """Manages speaker availability inputs."""
    st.header("Dostupnosť Rečníkov a Optimálny Plán Nahrávania")
    speaker_availability_inputs = {}

    if unique_speakers:
        st.markdown("Zadajte dostupné časové sloty pre každého rečníka:")
        
        for speaker in unique_speakers:
            if speaker not in st.session_state.speaker_availability_slots:
                today = datetime.today().strftime('%Y-%m-%d')
                tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
                day_after_tomorrow = (datetime.today() + timedelta(days=2)).strftime('%Y-%m-%d')
                st.session_state.speaker_availability_slots[speaker] = [
                    f"{today} 09:00-17:00",
                    f"{tomorrow} 09:00-17:00",
                    f"{day_after_tomorrow} 09:00-17:00"
                ]
        speakers_to_remove = [s for s in st.session_state.speaker_availability_slots if s not in unique_speakers]
        for s in speakers_to_remove:
            del st.session_state.speaker_availability_slots[s]

        num_cols = st.slider("Počet stĺpcov pre dostupnosť rečníkov", 1, 4, 2)
        cols = st.columns(num_cols)
        col_idx = 0

        for speaker in unique_speakers:
            with cols[col_idx]:
                st.subheader(f"Dostupnosť pre {speaker}")
                current_slots = st.session_state.speaker_availability_slots.get(speaker, [])
                
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

                new_slot_key = f"new_slot_{speaker}"
                if new_slot_key not in st.session_state:
                    st.session_state[new_slot_key] = f"{datetime.today().strftime('%Y-%m-%d')} 09:00-12:00"

                new_slot_value = st.text_input(
                    "Pridať nový slot (YYYY-MM-DD HH:MM-HH:MM)", 
                    value=st.session_state[new_slot_key], 
                    key=new_slot_key
                )
                
                if st.button("Pridať Slot", key=f"add_slot_{speaker}"):
                    if new_slot_value and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}-\d{2}:\d{2}", new_slot_value.strip()):
                        st.session_state.speaker_availability_slots[speaker].append(new_slot_value.strip())
                        st.rerun()
                    else:
                        st.error("Neplatný formát slotu. Použite YYYY-MM-DD HH:MM-HH:MM.")
                
                speaker_availability_inputs[speaker] = st.session_state.speaker_availability_slots[speaker]
            
            col_idx = (col_idx + 1) % num_cols
    else:
        st.info("Žiadni rečníci nájdení pre zadanie dostupnosti.")
    return speaker_availability_inputs

def manage_global_recording_times():
    """Manages global recording time slots."""
    st.header("Globálne Časy Nahrávania")
    st.markdown("Zadajte dostupné globálne časové sloty pre nahrávanie (formát: YYYY-MM-DD HH:MM-HH:MM, jeden slot na riadok):")

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
            st.rerun()
        else:
            st.error("Neplatný formát globálneho slotu. Použite YYYY-MM-DD HH:MM-HH:MM.")
    
    return st.session_state.recording_slots

def display_calendar_view(unique_speakers, speaker_availability_inputs, recording_days_times):
    """Displays the calendar view of speaker and recording availability."""
    st.header("Kalendár Dostupnosti Rečníkov a Nahrávania")
    num_days_to_show = st.slider("Počet dní na zobrazenie v kalendári", 1, 30, 7)
    if unique_speakers or recording_days_times:
        with st.spinner("Generujem kalendár..."):
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

def manage_availability_json_import_export():
    """Handles JSON import/export for availability data."""
    st.header("Uložiť/Načítať Dostupnosť")

    export_data = {
        "speaker_availability": st.session_state.speaker_availability_slots,
        "recording_slots": st.session_state.recording_slots
    }
    json_export_str = json.dumps(export_data, indent=4)
    st.download_button(
        label="📥 Stiahnuť Dostupnosť (JSON)",
        data=json_export_str,
        file_name="availability_config.json",
        mime="application/json"
    )

    uploaded_json_file = st.file_uploader("Nahrať Dostupnosť (JSON)", type="json")
    if uploaded_json_file is not None:
        try:
            loaded_data = json.load(uploaded_json_file)
            if "speaker_availability" in loaded_data and "recording_slots" in loaded_data:
                st.session_state.loaded_speaker_availability = loaded_data["speaker_availability"]
                st.session_state.loaded_recording_slots = loaded_data["recording_slots"]
                st.success("Dostupnosť úspešne načítaná z JSON súboru! Kliknite 'Použiť Načítané Dáta' pre aplikovanie.")
                st.session_state.show_apply_button = True
            else:
                st.error("Neplatný formát JSON súboru. Očakáva sa 'speaker_availability' a 'recording_slots'.")
        except json.JSONDecodeError:
            st.error("Chyba pri dekódovaní JSON súboru. Uistite sa, že je to platný JSON.")
        except Exception as e:
            st.error(f"Nastala chyba pri načítaní JSON súboru: {e}")
    
    if st.session_state.get("show_apply_button", False):
        if st.button("Použiť Načítané Dáta"):
            st.session_state.speaker_availability_slots = st.session_state.loaded_speaker_availability
            st.session_state.recording_slots = st.session_state.loaded_recording_slots
            st.session_state.show_apply_button = False
            st.rerun()

def display_optimal_schedule(df_processed, unique_speakers, speaker_availability_inputs, recording_days_times):
    """Calculates and displays the optimal recording schedule."""
    if st.button("Vypočítať Optimálny Plán Nahrávania"):
        if unique_speakers and speaker_availability_inputs:
            with st.spinner("Vypočítavam optimálny plán..."):
                optimal_schedule = calculate_optimal_schedule(df_processed, speaker_availability_inputs, recording_days_times)
            
            st.subheader("Navrhovaný Plán Nahrávania")
            if optimal_schedule and optimal_schedule.get("details"):
                for item in optimal_schedule["details"]:
                    st.write(f"Segment {item['segment_id']} ({item['duration']:.2f}s) s rečníkmi {', '.join(item['speakers'])}: {item['assigned_start_time']}-{item['assigned_end_time'].split(' ')[1]} ({item['status']})")
                if optimal_schedule.get("unassigned_segments"):
                    st.warning(f"Nasledujúce segmenty neboli priradené: {', '.join(optimal_schedule['unassigned_segments'])}")
            else:
                st.info("Optimálny plán nebol vygenerovaný alebo neobsahuje detaily.")

            if optimal_schedule and optimal_schedule.get("details"):
                st.subheader("Súhrn Plánu Nahrávania Podľa Rečníka")
                speaker_summary_df = summarize_speaker_schedule(optimal_schedule["details"])
                if not speaker_summary_df.empty:
                    speaker_summary_df['TotalScheduledDuration (min)'] = (speaker_summary_df['TotalScheduledDuration'] / 60).round(2)
                speaker_summary_df['IdleTime (min)'] = (speaker_summary_df['IdleTime'] / 60).round(2)
                st.dataframe(speaker_summary_df[['SpeakerName', 'TotalScheduledDuration (min)', 'TotalSegments', 'OverallTimeRange', 'IdleTime (min)', 'ScheduledTimeRanges']], use_container_width=True)
            else:
                st.info("Žiadny súhrn plánu nahrávania pre rečníkov.")
        else:
            st.warning("Nahrajte dokument a zadajte dostupnosť rečníkov pre výpočet plánu.")

def display_main_app_ui():
    """Displays the main application UI and handles file processing."""
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
        df_processed = process_uploaded_file(uploaded_file)

        if df_processed is not None:
            display_parsed_data_table(df_processed)
            display_speaker_segment_matrix(df_processed, uploaded_file.name)
            display_segment_time_analysis(df_processed)
            display_total_speaker_time(df_processed)
            configure_nominal_durations()
            
            unique_speakers = get_unique_speakers(df_processed)
            speaker_availability_inputs = manage_speaker_availability(unique_speakers)
            recording_days_times = manage_global_recording_times()
            
            display_calendar_view(unique_speakers, speaker_availability_inputs, recording_days_times)
            manage_availability_json_import_export()
            display_optimal_schedule(df_processed, unique_speakers, speaker_availability_inputs, recording_days_times)
    else:
        st.info("Prosím, nahrajte súbor DOCX pre začatie.")
