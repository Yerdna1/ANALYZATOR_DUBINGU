import pandas as pd
import logging
from datetime import datetime, timedelta

_log = logging.getLogger(__name__)

def summarize_speaker_schedule(schedule_details: list[dict]) -> pd.DataFrame:
    """
    Summarizes the recording schedule by speaker, calculating total scheduled time,
    number of segments, overall time range, and idle time.

    Args:
        schedule_details: A list of dictionaries, each representing a scheduled segment.
                          Example: [{"segment_id": "1", "speakers": ["ANDREJ"], "duration": 60,
                                     "assigned_start_time": "YYYY-MM-DD HH:MM",
                                     "assigned_end_time": "YYYY-MM-DD HH:MM"}]

    Returns:
        A Pandas DataFrame summarizing the schedule per speaker.
    """
    speaker_summary = {}

    for item in schedule_details:
        segment_start_str = item.get("assigned_start_time")
        segment_end_str = item.get("assigned_end_time")

        if not segment_start_str or not segment_end_str:
            _log.warning(f"Skipping segment {item.get('segment_id')} due to missing assigned_start_time or assigned_end_time.")
            continue

        try:
            segment_start = datetime.strptime(segment_start_str, '%Y-%m-%d %H:%M')
            segment_end = datetime.strptime(segment_end_str, '%Y-%m-%d %H:%M')
        except ValueError as e:
            _log.error(f"Error parsing time for segment {item.get('segment_id')}: {e}")
            continue

        for speaker in item['speakers']:
            if speaker not in speaker_summary:
                speaker_summary[speaker] = {
                    "TotalScheduledDuration": 0.0,
                    "TotalSegments": 0,
                    "TimeRanges": [],
                    "ScheduledTimeRanges": [] # To store formatted time ranges
                }
            
            speaker_summary[speaker]["TotalScheduledDuration"] += item['duration']
            speaker_summary[speaker]["TotalSegments"] += 1
            speaker_summary[speaker]["TimeRanges"].append((segment_start, segment_end))
            speaker_summary[speaker]["ScheduledTimeRanges"].append(f"{segment_start.strftime('%Y-%m-%d %H:%M')}-{segment_end.strftime('%H:%M')}")

    summary_data = []
    for speaker, data in speaker_summary.items():
        overall_start = None
        overall_end = None
        
        # Sort time ranges to calculate idle time and overall range
        sorted_time_ranges = sorted(data["TimeRanges"], key=lambda x: x[0])
        
        if sorted_time_ranges:
            overall_start = sorted_time_ranges[0][0]
            overall_end = sorted_time_ranges[0][1]
            
            idle_time = timedelta(seconds=0)
            
            for i in range(1, len(sorted_time_ranges)):
                prev_end = sorted_time_ranges[i-1][1]
                current_start = sorted_time_ranges[i][0]
                
                if current_start > prev_end:
                    idle_time += (current_start - prev_end)
                
                overall_end = max(overall_end, sorted_time_ranges[i][1])
            
            overall_time_range_str = f"{overall_start.strftime('%Y-%m-%d %H:%M')}-{overall_end.strftime('%H:%M')}"
        else:
            overall_time_range_str = "N/A"
            idle_time = timedelta(seconds=0)

        summary_data.append({
            "SpeakerName": speaker,
            "TotalScheduledDuration": data["TotalScheduledDuration"],
            "TotalSegments": data["TotalSegments"],
            "OverallTimeRange": overall_time_range_str,
            "IdleTime": idle_time.total_seconds(),
            "ScheduledTimeRanges": ", ".join(data["ScheduledTimeRanges"])
        })

    df_summary = pd.DataFrame(summary_data)
    return df_summary
