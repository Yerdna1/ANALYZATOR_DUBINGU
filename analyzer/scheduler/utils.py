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
