import pandas as pd
import re
import logging

_log = logging.getLogger(__name__)

def timecode_to_seconds(timecode_str: str) -> float:
    """Converts a timecode string (HH:MM:SS or MM:SS) to total seconds."""
    if not timecode_str:
        return 0.0
    
    # Handle potential ranges like "00:01-00:02" by taking the first timecode
    if '-' in timecode_str:
        timecode_str = timecode_str.split('-')[0].strip()

    # Remove "A " prefix if present
    timecode_str = timecode_str.replace('A ', '').strip()

    parts = timecode_str.split(':')
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        elif len(parts) == 2:
            h, m, s = 0, int(parts[0]), float(parts[1])
        else:
            _log.warning(f"Invalid timecode format: {timecode_str}. Returning 0.")
            return 0.0
        return h * 3600 + m * 60 + s
    except ValueError as e:
        _log.warning(f"Could not convert timecode '{timecode_str}' to seconds: {e}. Returning 0.")
        return 0.0

def process_parsed_data(parsed_data: list[dict], nominal_durations: dict[int, int]) -> pd.DataFrame:
    """
    Processes raw parsed data to add calculated fields:
    - 'TimeInSeconds': Converts timecode to total seconds (still useful for reference, but not for duration).
    - 'SegmentDuration': Duration of the segment based on nominal durations per speaker count.
    - 'NumSpeakersInSegment': Number of unique speakers in the segment.
    
    Args:
        parsed_data: List of dictionaries from the parser.
        nominal_durations: Dictionary mapping number of speakers to nominal duration in seconds.
    """
    if not parsed_data:
        return pd.DataFrame()

    df = pd.DataFrame(parsed_data)

    # Ensure 'Timecode', 'Segment', and 'Speaker' columns exist
    if 'Timecode' not in df.columns:
        df['Timecode'] = ''
    if 'Segment' not in df.columns:
        df['Segment'] = ''
    if 'Speaker' not in df.columns:
        df['Speaker'] = ''

    # Convert Timecode to seconds (kept for reference, not for duration calculation)
    df['TimeInSeconds'] = df['Timecode'].apply(timecode_to_seconds)

    # Calculate number of unique speakers per segment
    # Group by 'Segment' and count unique non-empty speakers
    segment_speaker_counts = df[df['Speaker'] != ''].groupby('Segment')['Speaker'].nunique()
    df['NumSpeakersInSegment'] = df['Segment'].map(segment_speaker_counts).fillna(0).astype(int)

    # Calculate SegmentDuration based on nominal durations
    # Apply nominal duration based on NumSpeakersInSegment
    def get_nominal_duration(row):
        num_speakers = row['NumSpeakersInSegment']
        if num_speakers >= 5: # Use the 5+ speakers value
            return nominal_durations.get(5, 200) # Default to 200 if not found
        elif num_speakers > 0:
            return nominal_durations.get(num_speakers, 60) # Default to 60 for 1-4 if not found
        return 0 # No speakers, no duration

    df['SegmentDuration'] = df.apply(get_nominal_duration, axis=1)
    
    _log.info("Processed parsed data with TimeInSeconds, NumSpeakersInSegment, and nominal SegmentDuration.")
    return df

def get_unique_speakers(df: pd.DataFrame) -> list[str]:
    """Extracts a sorted list of unique speakers from the DataFrame."""
    if 'Speaker' not in df.columns:
        return []
    unique_speakers = df['Speaker'].replace('', pd.NA).dropna().unique().tolist()
    return sorted(unique_speakers)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Example usage with dummy data
    test_data = [
        {"Segment": "1", "Speaker": "ANDREJ", "Timecode": "00:00:10", "Text": "Hello"},
        {"Segment": "1", "Speaker": "EVA", "Timecode": "00:00:12", "Text": "Hi"},
        {"Segment": "2", "Speaker": "PETER", "Timecode": "00:00:20", "Text": "Good morning"},
        {"Segment": "3", "Speaker": "ANDREJ", "Timecode": "00:00:30", "Text": "How are you?"},
        {"Segment": "3", "Speaker": "EVA", "Timecode": "00:00:32", "Text": "I'm fine"},
        {"Segment": "3", "Speaker": "PETER", "Timecode": "00:00:35", "Text": "Me too"},
        {"Segment": "4", "Speaker": "NINA", "Timecode": "00:00:40", "Text": "What's up?"},
        {"Segment": "5", "Speaker": "JAN", "Timecode": "00:00:50", "Text": "Nothing much"},
        {"Segment": "5", "Speaker": "MARTIN", "Timecode": "00:00:52", "Text": "Just chilling"},
        {"Segment": "5", "Speaker": "JOZO", "Timecode": "00:00:55", "Text": "Working hard"},
        {"Segment": "5", "Speaker": "PETER", "Timecode": "00:00:58", "Text": "Almost done"},
        {"Segment": "5", "Speaker": "JAN4", "Timecode": "00:01:00", "Text": "Let's go home"},
        {"Segment": "6", "Speaker": "", "Timecode": "00:01:10", "Text": "Scene change"}, # No speaker
    ]

    processed_df = process_parsed_data(test_data)
    print("\nProcessed DataFrame:")
    print(processed_df[['Segment', 'Speaker', 'Timecode', 'TimeInSeconds', 'NumSpeakersInSegment']].to_string())

    unique_speakers = get_unique_speakers(processed_df)
    print("\nUnique Speakers:", unique_speakers)
