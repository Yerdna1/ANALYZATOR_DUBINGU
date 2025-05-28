import pandas as pd
import logging
from datetime import datetime, timedelta

from .utils import parse_time_slot

_log = logging.getLogger(__name__)

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
                    assigned_start_time = rec_start
                    assigned_end_time = rec_start + timedelta(seconds=float(segment['duration']))
                    schedule["details"].append({
                        "segment_id": segment['segment_id'],
                        "speakers": segment['speakers'],
                        "duration": segment['duration'],
                        "assigned_start_time": assigned_start_time.strftime('%Y-%m-%d %H:%M'),
                        "assigned_end_time": assigned_end_time.strftime('%Y-%m-%d %H:%M'),
                        "status": "Assigned"
                    })
                    assigned = True
                    _log.info(f"  Segment {segment['segment_id']} assigned to {assigned_start_time.strftime('%Y-%m-%d %H:%M')}")
                    
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
