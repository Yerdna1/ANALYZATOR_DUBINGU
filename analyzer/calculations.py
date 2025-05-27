import pandas as pd
import logging

_log = logging.getLogger(__name__)

def calculate_segment_times_by_speaker_count(df: pd.DataFrame) -> dict[str, float]:
    """
    Calculates the total time in seconds for segments based on the number of unique speakers.
    Assumes 'NumSpeakersInSegment' and 'TimeInSeconds' columns are available in the DataFrame.
    """
    if df.empty or 'NumSpeakersInSegment' not in df.columns or 'TimeInSeconds' not in df.columns:
        _log.warning("DataFrame is empty or missing required columns for speaker count time calculation.")
        return {}

    # Group by segment to get unique segment durations and speaker counts
    # For now, using max TimeInSeconds as a proxy for segment duration.
    # This needs refinement if actual segment durations are not derived from timecodes.
    segment_summary = df.groupby('Segment').agg(
        NumSpeakers=('NumSpeakersInSegment', 'first'), # Assuming NumSpeakersInSegment is consistent per segment
        MaxTimeInSeconds=('TimeInSeconds', 'max') # Using max time as a proxy for segment end
    ).reset_index()

    # Calculate duration between segments for a more accurate segment duration
    # This is a simplified approach. A more robust solution would involve parsing start/end timecodes.
    segment_summary['SegmentDuration'] = segment_summary['MaxTimeInSeconds'].diff().fillna(segment_summary['MaxTimeInSeconds'])
    segment_summary.loc[segment_summary['SegmentDuration'] < 0, 'SegmentDuration'] = segment_summary['MaxTimeInSeconds'] # Handle cases where timecodes might reset

    # Filter for valid segments (e.g., segment > 0)
    segment_summary = segment_summary[segment_summary['NumSpeakers'] > 0]

    results = {}
    for i in range(1, 6): # For 1 to 5 speakers
        total_time = segment_summary[segment_summary['NumSpeakers'] == i]['SegmentDuration'].sum()
        results[f"segments_with_{i}_speakers_time_seconds"] = round(total_time, 2)
        _log.debug(f"Calculated total time for segments with {i} speakers: {total_time} seconds.")

    return results

def calculate_total_speaker_time(df: pd.DataFrame) -> dict[str, float]:
    """
    Calculates the total 'active' time for each speaker.
    Assumes 'Speaker' and 'TimeInSeconds' columns are available.
    This is a simplified calculation, summing up TimeInSeconds for each line a speaker has.
    A more accurate 'active' time would consider actual dialogue duration or segment duration.
    """
    if df.empty or 'Speaker' not in df.columns or 'TimeInSeconds' not in df.columns:
        _log.warning("DataFrame is empty or missing required columns for total speaker time calculation.")
        return {}

    # Filter out empty speakers
    df_active_speakers = df[df['Speaker'] != ''].copy()

    # Group by speaker and sum their 'TimeInSeconds'
    # This is a proxy. If 'TimeInSeconds' is a start time, this sums start times, not durations.
    # A more accurate approach would be to assign a duration to each line or segment.
    # For now, we'll use a simple count of lines or a nominal duration per line.
    # Let's refine this to count unique segments a speaker is in, and multiply by a nominal segment duration.
    # Or, if we can get actual segment durations, use that.

    # For now, let's sum the 'TimeInSeconds' for each line a speaker has, as a rough proxy.
    # This is not ideal for "total team needed" but is a direct interpretation of "time for every speaker".
    # A better approach for "total team needed" would be to sum the duration of segments they are in.

    # Let's try to sum the 'SegmentDuration' for each unique segment a speaker is in.
    # First, get unique speaker-segment pairs and their segment durations
    speaker_segment_durations = df_active_speakers.groupby(['Speaker', 'Segment'])['SegmentDuration'].first().reset_index()
    
    # Then, sum these durations per speaker
    total_speaker_time = speaker_segment_durations.groupby('Speaker')['SegmentDuration'].sum()

    results = {speaker: round(time, 2) for speaker, time in total_speaker_time.items()}
    _log.info("Calculated total active time for each speaker.")
    return results

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Example usage with dummy data (similar to data_processing output)
    test_df = pd.DataFrame([
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

    segment_times = calculate_segment_times_by_speaker_count(test_df)
    print("\nSegment Times by Speaker Count:", segment_times)

    speaker_times = calculate_total_speaker_time(test_df)
    print("\nTotal Speaker Times:", speaker_times)
