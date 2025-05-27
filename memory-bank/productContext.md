# Product Context: Analyzátor Dabingových Scenárov

## Purpose
Automate analysis of Slovak dubbing scripts to:
- Track speaker participation across segments
- Identify scene transitions and markers
- Calculate timecode distributions
- Generate reports for dubbing directors
- **Estimate segment durations based on speaker count for planning**
- **Generate optimal recording schedules considering speaker availability and global studio slots**

## User Workflow
1. Upload .docx script file
2. System parses and structures the content
3. User reviews extracted data
4. User configures nominal segment durations based on speaker count
5. User inputs speaker availability and global recording times
6. User generates speaker-segment matrix
7. User views proposed recording schedule
8. User exports data to Excel

## Key Components
1. Document Parser (parser.py)
   - Extracts speakers, timecodes, dialogues
   - Identifies scene markers and segments
2. Data Processor
   - Creates speaker-segment matrices
   - Calculates statistics
   - **Calculates segment durations based on configurable nominal values**
3. **Scheduler (analyzer/scheduler.py)**
   - **Generates optimal recording plans**
   - **Considers speaker availability and global recording slots**
4. Streamlit UI
   - File upload interface
   - Data visualization
   - Export controls
   - **Input fields for nominal segment durations**
   - **Input fields for speaker availability and global recording times**
   - **Display of proposed recording schedule**

## Technical Dependencies
- docx2txt for document conversion
- pandas for data manipulation
- openpyxl for Excel export
- Streamlit for web interface
