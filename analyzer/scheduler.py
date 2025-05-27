import pandas as pd
import logging
from datetime import datetime, timedelta

_log = logging.getLogger(__name__)

def parse_time_slot(time_str: str) -> tuple[datetime, datetime] | None:
    """
    Parses a time slot string (e.g., "YYYY-MM-DD HH:MM-HH:MM") into start and end datetime objects.
    """
    try:
        date_part, time_range_part = time_str.split(' ', 1)
        start_time_str, end_time_str = time_range_part.split('-')
        
        start_dt = datetime.strptime(f"{date_part} {start_time_str.strip()}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_part} {end_time_str.strip()}", "%Y-%m-%d %H:%M")

        if end_dt < start_dt: # Handle overnight slots (e.g., 2023-01-01 23:00-01:00)
            end_dt += timedelta(days=1)
            _log.warning(f"Time slot {time_str} spans overnight. Adjusted end time.")

        return start_dt, end_dt
    except ValueError as e:
        _log.error(f"Invalid time slot format '{time_str}': {e}. Expected 'YYYY-MM-DD HH:MM-HH:MM'.")
        return None

def calculate_optimal_schedule(
    df_processed: pd.DataFrame, 
    speaker_availability: dict[str, list[str]]
) -> dict:
    """
    Calculates an optimal recording schedule based on processed data and speaker availability.
    
    Args:
        df_processed: DataFrame with processed segment data (including NumSpeakersInSegment, SegmentDuration).
        speaker_availability: Dictionary where keys are speaker names and values are lists of time slot strings.
                              e.g., {"ANDREJ": ["09:00-12:00", "14:00-17:00"]}
                                    
    Returns:
        A dictionary representing the proposed schedule.
    """
def calculate_optimal_schedule(
    df_processed: pd.DataFrame, 
    speaker_availability: dict[str, list[str]],
    recording_days_times: list[str] # New parameter for global recording times
) -> dict:
    """
    Calculates an optimal recording schedule based on processed data, speaker availability,
    and global recording slots.
    
    Args:
        df_processed: DataFrame with processed segment data (including NumSpeakersInSegment, SegmentDuration).
        speaker_availability: Dictionary where keys are speaker names and values are lists of time slot strings.
                              e.g., {"ANDREJ": ["YYYY-MM-DD HH:MM-HH:MM", "YYYY-MM-DD HH:MM-HH:MM"]}
        recording_days_times: List of global recording time slot strings (YYYY-MM-DD HH:MM-HH:MM).
                                    
    Returns:
        A dictionary representing the proposed schedule.
    """
    _log.info("Starting optimal schedule calculation...")

    # 1. Parse all availability and recording slots into datetime objects
    parsed_speaker_availability = {}
    for speaker, slots in speaker_availability.items():
        parsed_slots = []
        for slot_str in slots:
            parsed_slot = parse_time_slot(slot_str)
            if parsed_slot:
                parsed_slots.append(parsed_slot)
        parsed_speaker_availability[speaker] = parsed_slots
    _log.debug(f"Parsed speaker availability: {parsed_speaker_availability}")

    parsed_recording_slots = []
    for slot_str in recording_days_times:
        parsed_slot = parse_time_slot(slot_str)
        if parsed_slot:
            parsed_recording_slots.append(parsed_slot)
    _log.debug(f"Parsed global recording slots: {parsed_recording_slots}")

    # 2. Group segments and prepare for scheduling
    segments_to_schedule = []
    # Get unique segments and their total duration and speakers
    segment_groups = df_processed[df_processed['Speaker'] != ''].groupby('Segment')
    for segment_id, group in segment_groups:
        speakers_in_segment = group['Speaker'].unique().tolist()
        num_speakers = len(speakers_in_segment)
        # Sum SegmentDuration for all lines within the same segment to get total segment duration
        segment_total_duration = group['SegmentDuration'].sum() 
        
        if num_speakers > 0 and segment_total_duration > 0:
            segments_to_schedule.append({
                'segment_id': segment_id,
                'speakers': speakers_in_segment,
                'num_speakers': num_speakers,
                'duration': segment_total_duration # Use summed duration
            })
    
    # Sort segments for scheduling (e.g., multi-speaker first, then by duration descending)
    segments_to_schedule.sort(key=lambda x: (x['num_speakers'], x['duration']), reverse=True)
    _log.info(f"Segments to schedule (sorted by num_speakers, then duration): {segments_to_schedule}")

    # 3. Implement Basic Greedy Scheduling Logic
    schedule = {
        "status": "Generated Schedule",
        "details": [],
        "unassigned_segments": []
    }
    
    # Create a mutable copy of recording slots to track used time
    available_recording_slots = sorted(parsed_recording_slots, key=lambda x: x[0]) # Sort by start time
    
    for segment in segments_to_schedule:
        _log.debug(f"Attempting to schedule segment {segment['segment_id']} (Speakers: {segment['speakers']}, Duration: {segment['duration']:.2f}s)")
        
        assigned = False
        for rec_slot_idx, (rec_start, rec_end) in enumerate(available_recording_slots):
            # Check if segment duration fits within the current recording slot
            if (rec_end - rec_start).total_seconds() >= segment['duration']:
                # Check if all speakers are available within this recording slot
                all_speakers_available = True
                for speaker in segment['speakers']:
                    speaker_has_slot = False
                    if speaker in parsed_speaker_availability:
                        for sp_start, sp_end in parsed_speaker_availability[speaker]:
                            # Check for overlap between speaker's slot and current recording slot
                            if max(rec_start, sp_start) < min(rec_end, sp_end):
                                speaker_has_slot = True
                                break
                    if not speaker_has_slot:
                        all_speakers_available = False
                        _log.debug(f"  Speaker {speaker} not available in recording slot {rec_start.strftime('%H:%M')}-{rec_end.strftime('%H:%M')}")
                        break
                
                if all_speakers_available:
                    # Assign segment to this slot (simplified: just take the start of the recording slot)
                    assigned_time = rec_start
                    schedule["details"].append({
                        "segment_id": segment['segment_id'],
                        "speakers": segment['speakers'],
                        "duration": segment['duration'],
                        "assigned_time": assigned_time.strftime('%Y-%m-%d %H:%M'),
                        "status": "Assigned"
                    })
                    assigned = True
                    _log.info(f"  Segment {segment['segment_id']} assigned to {assigned_time.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Update the available recording slot (simple greedy: consume from start)
                    # In a real scheduler, this would split the slot or manage a timeline.
                    # For now, we'll just reduce the current slot or remove it if fully consumed.
                    new_rec_start = rec_start + timedelta(seconds=float(segment['duration']))
                    if new_rec_start < rec_end:
                        available_recording_slots[rec_slot_idx] = (new_rec_start, rec_end)
                    else:
                        available_recording_slots.pop(rec_slot_idx) # Slot fully consumed
                    
                    # Re-sort to keep track of available slots
                    available_recording_slots.sort(key=lambda x: x[0])
                    break # Move to next segment
        
        if not assigned:
            schedule["unassigned_segments"].append(segment['segment_id'])
            _log.warning(f"  Segment {segment['segment_id']} could not be assigned.")

    _log.info("Optimal schedule calculation completed.")
    return schedule

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

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Dummy processed DataFrame
    test_df_processed = pd.DataFrame([
        {"Segment": "1", "Speaker": "ANDREJ", "Timecode": "00:00:10", "Text": "Hello", "TimeInSeconds": 10.0, "NumSpeakersInSegment": 2, "SegmentDuration": 5.0},
        {"Segment": "1", "Speaker": "EVA", "Timecode": "00:00:12", "Text": "Hi", "TimeInSeconds": 12.0, "NumSpeakersInSegment": 2, "SegmentDuration": 5.0},
        {"Segment": "2", "Speaker": "PETER", "Timecode": "00:00:20", "Text": "Good morning", "TimeInSeconds": 20.0, "NumSpeakersInSegment": 1, "SegmentDuration": 3.0},
        {"Segment": "3", "Speaker": "ANDREJ", "Timecode": "00:00:30", "Text": "How are you?", "TimeInSeconds": 30.0, "NumSpeakersInSegment": 3, "SegmentDuration": 7.0},
        {"Segment": "3", "Speaker": "EVA", "Timecode": "00:00:32", "Text": "I'm fine", "TimeInSeconds": 32.0, "NumSpeakersInSegment": 3, "SegmentDuration": 7.0},
        {"Segment": "3", "Speaker": "PETER", "Timecode": "00:00:35", "Text": "Me too", "TimeInSeconds": 35.0, "NumSpeakersInSegment": 3, "SegmentDuration": 7.0},
        {"Segment": "4", "Speaker": "NINA", "Timecode": "00:00:40", "Text": "What's up?", "TimeInSeconds": 40.0, "NumSpeakersInSegment": 1, "SegmentDuration": 4.0},
        {"Segment": "5", "Speaker": "JAN", "Timecode": "00:00:50", "Text": "Nothing much", "TimeInSeconds": 50.0, "NumSpeakersInSegment": 5, "SegmentDuration": 10.0},
        {"Segment": "5", "Speaker": "MARTIN", "Timecode": "00:00:52", "Text": "Just chilling", "TimeInSeconds": 52.0, "NumSpeakersInSegment": 5, "SegmentDuration": 10.0},
        {"Segment": "5", "Speaker": "JOZO", "Timecode": "00:00:55", "Text": "Working hard", "TimeInSeconds": 55.0, "NumSpeakersInSegment": 5, "SegmentDuration": 10.0},
        {"Segment": "5", "Speaker": "PETER", "Timecode": "00:00:58", "Text": "Almost done", "TimeInSeconds": 58.0, "NumSpeakersInSegment": 5, "SegmentDuration": 10.0},
        {"Segment": "5", "Speaker": "JAN4", "Timecode": "00:01:00", "Text": "Let's go home", "TimeInSeconds": 60.0, "NumSpeakersInSegment": 5, "SegmentDuration": 10.0},
        {"Segment": "6", "Speaker": "", "Timecode": "00:01:10", "Text": "Scene change", "TimeInSeconds": 70.0, "NumSpeakersInSegment": 0, "SegmentDuration": 0.0}, # No speaker
    ])

    # Dummy speaker availability
    speaker_avail = {
        "ANDREJ": ["09:00-12:00", "14:00-17:00"],
        "EVA": ["10:00-13:00"],
        "PETER": ["09:00-11:00", "15:00-18:00"],
        "NINA": ["13:00-16:00"],
        "JAN": ["09:00-17:00"],
        "MARTIN": ["09:00-17:00"],
        "JOZO": ["09:00-17:00"],
        "JAN4": ["09:00-17:00"],
    }

    schedule = calculate_optimal_schedule(test_df_processed, speaker_avail)
    print("\nOptimal Schedule (Placeholder):", schedule)
