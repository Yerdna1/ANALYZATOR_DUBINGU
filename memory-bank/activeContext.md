# Active Context: Analyzátor Dabingových Scenárov

## Current Focus
1. **Implementing configurable nominal segment durations.**
2. **Refining and debugging the optimal scheduling logic.**
3. Ensuring robust handling of Streamlit session state for new inputs.

## Recent Changes
- Added input fields for nominal segment durations (1, 2, 3, 4, 5+ speakers) in `app.py`.
- Modified `analyzer/data_processing.py` to calculate `SegmentDuration` based on these nominal durations, replacing timecode-based calculation.
- Updated `analyzer/scheduler.py` to include a basic greedy scheduling algorithm that considers speaker availability and global recording slots.
- Fixed `KeyError` in `app.py` by moving `nominal_durations` initialization to the global scope.
- Fixed `TypeError` in `analyzer/scheduler.py` by casting `segment['duration']` to `float` for `timedelta` calculation.

## Next Steps
1. **Verify the application runs without errors** and the new nominal duration inputs function correctly.
2. **Test the optimal scheduling logic** with various inputs to ensure it produces reasonable results.
3. Continue to refine the scheduling algorithm if needed based on testing.

## Open Questions
- How should the optimal scheduling algorithm prioritize segments if multiple options exist? (Currently, it prioritizes multi-speaker segments then by duration descending).
- Are there specific constraints or preferences for scheduling that need to be incorporated (e.g., minimizing studio time, specific speaker preferences)?
