import pandas as pd
import logging
from datetime import datetime, timedelta

from .utils import parse_time_slot

_log = logging.getLogger(__name__)

def generate_calendar_view(
    unique_speakers: list[str], 
    speaker_availability: dict[str, list[str]],
    recording_days_times: list[str], # New parameter for global recording times
    time_granularity_minutes: int = 30,
    start_hour: int = 8,
    end_hour: int = 20,
    num_days_to_show: int = 7 # Show a week by default
) -> pd.DataFrame:
    """
    Generates a DataFrame representing a calendar view of speaker availability and recording slots.
    
    Args:
        unique_speakers: List of all unique speakers.
        speaker_availability: Dictionary of speaker names to lists of time slot strings (YYYY-MM-DD HH:MM-HH:MM).
        recording_days_times: List of global recording time slot strings (YYYY-MM-DD HH:MM-HH:MM).
        time_granularity_minutes: Interval for time slots in the calendar (e.g., 30 for 30-min slots).
        start_hour: The starting hour for the calendar view (e.g., 8 for 8:00).
        end_hour: The ending hour for the calendar view (e.g., 20 for 20:00).
        num_days_to_show: Number of days to display in the calendar.
        
    Returns:
        A Pandas DataFrame representing the calendar view.
    """
    _log.info("Generating calendar view...")
    
    all_time_labels = []
    all_time_intervals = []
    start_date = datetime.today().date() # Start from today

    for d_offset in range(num_days_to_show):
        current_date = start_date + timedelta(days=d_offset)
        current_time = datetime.combine(current_date, datetime.min.time().replace(hour=start_hour))
        end_time_limit = datetime.combine(current_date, datetime.min.time().replace(hour=end_hour))

        while current_time < end_time_limit:
            slot_end = current_time + timedelta(minutes=time_granularity_minutes)
            label = f"{current_date.strftime('%Y-%m-%d')} {current_time.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}"
            all_time_labels.append(label)
            all_time_intervals.append((current_time, slot_end))
            current_time = slot_end

    # Initialize calendar data with empty strings
    calendar_data = {speaker: [''] * len(all_time_labels) for speaker in unique_speakers}
    calendar_data['Recording Slots'] = [''] * len(all_time_labels) # Add column for global recording slots
    calendar_df = pd.DataFrame(calendar_data, index=all_time_labels)
    
    # Parse speaker availability
    parsed_speaker_availability = {}
    for speaker, slots in speaker_availability.items():
        parsed_slots = []
        for slot_str in slots:
            parsed_slot = parse_time_slot(slot_str)
            if parsed_slot:
                parsed_slots.append(parsed_slot)
        parsed_speaker_availability[speaker] = parsed_slots

    # Populate speaker availability
    for speaker, slots in parsed_speaker_availability.items():
        for start_dt, end_dt in slots:
            for i, (interval_start_dt, interval_end_dt) in enumerate(all_time_intervals):
                # Check for overlap
                if max(start_dt, interval_start_dt) < min(end_dt, interval_end_dt):
                    calendar_df.loc[all_time_labels[i], speaker] = "Dostupný" # Slovak for Available

    # Parse and populate global recording slots
    parsed_recording_slots = []
    for slot_str in recording_days_times:
        parsed_slot = parse_time_slot(slot_str)
        if parsed_slot:
            parsed_recording_slots.append(parsed_slot)

    for start_dt, end_dt in parsed_recording_slots:
        for i, (interval_start_dt, interval_end_dt) in enumerate(all_time_intervals):
            if max(start_dt, interval_start_dt) < min(end_dt, interval_end_dt):
                calendar_df.loc[all_time_labels[i], 'Recording Slots'] = "Nahrávanie" # Slovak for Recording

    _log.info("Calendar view generated.")
    return calendar_df
